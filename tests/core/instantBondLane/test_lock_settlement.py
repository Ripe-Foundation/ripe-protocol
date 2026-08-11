import boa
import pytest

from conf_utils import filter_logs


MISMATCH_TELLER = """
# @version 0.4.3

import contracts.modules.Addys as addys

@external
def depositFromTrusted(
    _user: address,
    _vaultId: uint256,
    _asset: address,
    _amount: uint256,
    _lockDuration: uint256,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    return _amount - 1
"""


PARTIAL_PULL_TELLER = """
# @version 0.4.3

import contracts.modules.Addys as addys

interface IERC20:
    def transferFrom(_sender: address, _recipient: address, _amount: uint256) -> bool: nonpayable

@external
def depositFromTrusted(
    _user: address,
    _vaultId: uint256,
    _asset: address,
    _amount: uint256,
    _lockDuration: uint256,
    _a: addys.Addys = empty(addys.Addys),
) -> uint256:
    assert _amount > 1
    assert extcall IERC20(_asset).transferFrom(msg.sender, self, _amount - 1)
    return _amount
"""


NONEXACT_RECEIPT_TOKEN = """
# @version 0.4.3

decimals: public(immutable(uint8))
balanceOf: public(HashMap[address, uint256])
allowance: public(HashMap[address, HashMap[address, uint256]])
totalSupply: public(uint256)
owner: immutable(address)
receiptBps: immutable(uint256)

@deploy
def __init__(_owner: address, _decimals: uint8, _receiptBps: uint256):
    assert _receiptBps <= 20_000
    owner = _owner
    decimals = _decimals
    receiptBps = _receiptBps
    self.totalSupply = 10**30
    self.balanceOf[_owner] = self.totalSupply

@external
def transfer(_to: address, _value: uint256) -> bool:
    self.balanceOf[msg.sender] -= _value
    self.balanceOf[_to] += _value
    return True

@external
def approve(_spender: address, _value: uint256) -> bool:
    self.allowance[msg.sender][_spender] = _value
    return True

@external
def transferFrom(_from: address, _to: address, _value: uint256) -> bool:
    self.allowance[_from][msg.sender] -= _value
    self.balanceOf[_from] -= _value
    delivered: uint256 = _value * receiptBps // 10_000
    self.balanceOf[_to] += delivered
    if delivered > _value:
        self.totalSupply += delivered - _value
    else:
        self.totalSupply -= _value - delivered
    return True
"""


NO_RETURN_PAYMENT_TOKEN = """
# @version 0.4.3

decimals: public(immutable(uint8))
balanceOf: public(HashMap[address, uint256])
allowance: public(HashMap[address, HashMap[address, uint256]])
totalSupply: public(uint256)

@deploy
def __init__(_owner: address, _decimals: uint8):
    decimals = _decimals
    self.totalSupply = 10**30
    self.balanceOf[_owner] = self.totalSupply

@external
def transfer(_to: address, _value: uint256) -> bool:
    self.balanceOf[msg.sender] -= _value
    self.balanceOf[_to] += _value
    return True

@external
def approve(_spender: address, _value: uint256) -> bool:
    self.allowance[msg.sender][_spender] = _value
    return True

@external
def transferFrom(_from: address, _to: address, _value: uint256):
    self.allowance[_from][msg.sender] -= _value
    self.balanceOf[_from] -= _value
    self.balanceOf[_to] += _value
"""


FALSE_RETURN_PAYMENT_TOKEN = """
# @version 0.4.3

decimals: public(immutable(uint8))
balanceOf: public(HashMap[address, uint256])
allowance: public(HashMap[address, HashMap[address, uint256]])
totalSupply: public(uint256)

@deploy
def __init__(_owner: address, _decimals: uint8):
    decimals = _decimals
    self.totalSupply = 10**30
    self.balanceOf[_owner] = self.totalSupply

@external
def transfer(_to: address, _value: uint256) -> bool:
    self.balanceOf[msg.sender] -= _value
    self.balanceOf[_to] += _value
    return True

@external
def approve(_spender: address, _value: uint256) -> bool:
    self.allowance[msg.sender][_spender] = _value
    return True

@external
def transferFrom(_from: address, _to: address, _value: uint256) -> bool:
    return False
"""


def settlement_snapshot(ctx):
    return (
        ctx.lane.configVersion(),
        ctx.lane.isInitialized(),
        ctx.lane.currentEpoch(),
        ctx.lane.epochRate(),
        ctx.lane.epochPaymentCap(),
        ctx.lane.epochMinPaymentAmount(),
        ctx.lane.epochMaxLockBonus(),
        ctx.lane.epochPricingVersion(),
        ctx.lane.epochAcceptedPayment(),
        ctx.lane.epochWeightedLateness(),
        ctx.lane.epochTimingEligible(),
        ctx.lane.rateOverride(),
        ctx.lane.overrideVersion(),
        ctx.lane.cumulativeMinted(),
        ctx.payment_token.balanceOf(ctx.bob),
        ctx.payment_token.balanceOf(ctx.endaoment_funds),
        ctx.payment_token.balanceOf(ctx.lane),
        ctx.ripe_token.totalSupply(),
        ctx.ripe_token.balanceOf(ctx.bob),
        ctx.ripe_token.balanceOf(ctx.lane),
        ctx.ripe_token.balanceOf(ctx.ripe_gov_vault),
        ctx.ripe_token.allowance(ctx.lane, ctx.teller),
        ctx.ripe_gov_vault.getTotalAmountForUser(ctx.bob, ctx.ripe_token),
    )


def replace_teller(ctx, replacement):
    registry_lock = ctx.ripe_hq.registryChangeTimeLock()
    assert ctx.ripe_hq.startAddressUpdateToRegistry(
        17,
        replacement,
        sender=ctx.governance.address,
    )
    if registry_lock:
        boa.env.time_travel(blocks=registry_lock)
    assert ctx.ripe_hq.confirmAddressUpdateToRegistry(
        17,
        sender=ctx.governance.address,
    )


@pytest.mark.parametrize(
    "requested_lock, expected_lock, expected_bonus_ratio",
    [
        (0, 0, 0),
        (99, 0, 0),
        (100, 100, 0),
        (550, 550, 2_500),
        (1_000, 1_000, 5_000),
        (5_000, 1_000, 5_000),
    ],
)
def test_lock_boundaries_and_linear_bonus(
    lane_env, requested_lock, expected_lock, expected_bonus_ratio
):
    lane_env.set_config(maxLockBonus=5_000)
    lane_env.setup_lock_terms(min_lock=100, max_lock=1_000)
    amount = 10 * lane_env.scale

    quote = lane_env.quote(amount, requested_lock)
    expected_base = amount * quote.rate // lane_env.scale
    expected_bonus = expected_base * expected_bonus_ratio // 10_000

    assert quote.available
    assert quote.actualLock == expected_lock
    assert quote.bonusRatio == expected_bonus_ratio
    assert quote.baseRipe == expected_base
    assert quote.bonusRipe == expected_bonus
    assert quote.totalRipe == expected_base + expected_bonus
    assert quote.totalRipe * lane_env.scale <= amount * 2 * 10**18


def test_zero_equal_and_invalid_live_lock_terms(lane_env):
    lane_env.set_config(maxLockBonus=5_000)
    amount = lane_env.scale

    lane_env.setup_lock_terms(min_lock=0, max_lock=0)
    quote = lane_env.quote(amount, 1_000)
    assert quote.actualLock == 0
    assert quote.bonusRatio == 0

    lane_env.setup_lock_terms(min_lock=500, max_lock=500)
    below = lane_env.quote(amount, 499)
    at = lane_env.quote(amount, 500)
    above = lane_env.quote(amount, 2_000)
    assert below.actualLock == 0
    assert below.bonusRatio == 0
    assert at.actualLock == 500
    assert at.bonusRatio == 5_000
    assert above.actualLock == 500
    assert above.bonusRatio == 5_000

    lane_env.setup_lock_terms(min_lock=1_000, max_lock=500)
    invalid = lane_env.quote(amount, 1_000)
    assert invalid.available
    assert invalid.actualLock == 0
    assert invalid.bonusRatio == 0
    assert invalid.bonusRipe == 0


def test_live_lock_terms_change_within_epoch_without_changing_epoch_bonus(lane_env):
    lane_env.set_config(maxLockBonus=6_000)
    amount = 5 * lane_env.scale

    lane_env.setup_lock_terms(min_lock=100, max_lock=1_000)
    first = lane_env.quote(amount, 550)
    assert first.bonusRatio == 3_000

    lane_env.setup_lock_terms(min_lock=200, max_lock=800)
    second = lane_env.quote(amount, 550)
    assert second.epoch == first.epoch
    assert second.pricingConfigVersion == first.pricingConfigVersion
    assert second.rate == first.rate
    assert second.bonusRatio == 3_500
    assert second.actualLock == 550
    assert second.totalRipe * lane_env.scale <= amount * 2 * 10**18


def test_locked_settlement_exact_amount_lock_and_zero_residue(lane_env):
    lane_env.set_config(maxLockBonus=5_000)
    terms = lane_env.setup_lock_terms(min_lock=100, max_lock=1_000)
    amount = 20 * lane_env.scale
    quote = lane_env.quote(amount, 1_000)

    payment_before = lane_env.payment_token.balanceOf(lane_env.endaoment_funds)
    vault_before = lane_env.ripe_gov_vault.getTotalAmountForUser(
        lane_env.bob, lane_env.ripe_token
    )
    payout = lane_env.buy(
        amount,
        requested_lock=1_000,
        expected_epoch=quote.epoch,
        min_ripe_out=quote.totalRipe,
    )
    purchase = filter_logs(lane_env.lane, "InstantBondPurchased")[0]

    assert payout == quote.totalRipe
    assert purchase.actualLock == 1_000
    assert purchase.bonusRatio == 5_000
    assert purchase.ripeGovVaultId == lane_env.mission_control.coreRipeGovVaultId()
    assert lane_env.payment_token.balanceOf(lane_env.endaoment_funds) == payment_before + amount
    assert lane_env.ripe_gov_vault.getTotalAmountForUser(
        lane_env.bob, lane_env.ripe_token
    ) == vault_before + payout
    assert lane_env.ripe_gov_vault.userGovData(
        lane_env.bob, lane_env.ripe_token
    ).unlock == boa.env.evm.patch.block_number + 1_000
    assert lane_env.payment_token.balanceOf(lane_env.lane) == 0
    assert lane_env.ripe_token.balanceOf(lane_env.lane) == 0
    assert lane_env.ripe_token.allowance(lane_env.lane, lane_env.teller) == 0
    assert terms[1] == purchase.actualLock


def test_locked_settlement_follows_rotated_core_vault_pointer(
    lane_env,
    alternate_ripe_gov_vault,
    registerVault,
    setAssetConfig,
    switchboard_charlie,
):
    lane_env.set_config(maxLockBonus=5_000)
    lane_env.setup_lock_terms(min_lock=100, max_lock=1_000)
    source_id = lane_env.mission_control.coreRipeGovVaultId()
    core_id = registerVault(alternate_ripe_gov_vault, "Instant Bond Core RipeGov")
    setAssetConfig(lane_env.ripe_token, _vaultIds=[source_id, core_id])
    action_id = switchboard_charlie.setCoreRipeGovVaultId(
        core_id,
        sender=lane_env.governance.address,
    )
    boa.env.time_travel(blocks=switchboard_charlie.actionTimeLock())
    assert switchboard_charlie.executePendingAction(
        action_id,
        sender=lane_env.governance.address,
    )
    assert lane_env.mission_control.coreRipeGovVaultId() == core_id

    amount = 20 * lane_env.scale
    source_before = lane_env.ripe_gov_vault.getTotalAmountForUser(
        lane_env.bob, lane_env.ripe_token
    )
    target_before = alternate_ripe_gov_vault.getTotalAmountForUser(
        lane_env.bob, lane_env.ripe_token
    )
    payout = lane_env.buy(amount, requested_lock=1_000)
    purchase = filter_logs(lane_env.lane, "InstantBondPurchased")[0]

    assert purchase.ripeGovVaultId == core_id
    assert lane_env.ripe_gov_vault.getTotalAmountForUser(
        lane_env.bob, lane_env.ripe_token
    ) == source_before
    assert alternate_ripe_gov_vault.getTotalAmountForUser(
        lane_env.bob, lane_env.ripe_token
    ) == target_before + payout


def test_locked_settlement_after_user_position_migration_uses_new_core_vault(
    lane_env,
    alternate_ripe_gov_vault,
    registerVault,
    setAssetConfig,
    switchboard_echo,
):
    lane_env.set_config(maxLockBonus=5_000)
    lane_env.setup_lock_terms(min_lock=100, max_lock=1_000)
    source_id = lane_env.mission_control.coreRipeGovVaultId()
    first_payout = lane_env.buy(20 * lane_env.scale, requested_lock=500)

    core_id = registerVault(alternate_ripe_gov_vault, "Migrated Instant Bond Core")
    setAssetConfig(lane_env.ripe_token, _vaultIds=[source_id, core_id])
    lane_env.ripe_gov_vault.pause(True, sender=lane_env.switchboard.address)
    alternate_ripe_gov_vault.pause(True, sender=lane_env.switchboard.address)
    assert lane_env.teller.migrateRipeGovPosition(
        lane_env.bob,
        lane_env.ripe_token,
        source_id,
        core_id,
        sender=switchboard_echo.address,
    ) == first_payout
    assert lane_env.ripe_gov_vault.positionMigratedOut(
        lane_env.bob, lane_env.ripe_token
    )

    lane_env.mission_control.setCoreRipeGovVaultId(
        core_id,
        sender=lane_env.switchboard.address,
    )
    alternate_ripe_gov_vault.pause(False, sender=lane_env.switchboard.address)
    second_payout = lane_env.buy(10 * lane_env.scale, requested_lock=500)
    purchase = filter_logs(lane_env.lane, "InstantBondPurchased")[0]

    assert purchase.ripeGovVaultId == core_id
    assert lane_env.ripe_gov_vault.getTotalAmountForUser(
        lane_env.bob, lane_env.ripe_token
    ) == 0
    assert alternate_ripe_gov_vault.getTotalAmountForUser(
        lane_env.bob, lane_env.ripe_token
    ) == first_payout + second_payout


def test_locked_settlement_rejects_core_vault_without_ripe_support(
    lane_env,
    alternate_ripe_gov_vault,
    registerVault,
):
    lane_env.set_config()
    lane_env.setup_lock_terms()
    unsupported_id = registerVault(
        alternate_ripe_gov_vault,
        "Unsupported Instant Bond Core",
    )
    lane_env.mission_control.setCoreRipeGovVaultId(
        unsupported_id,
        sender=lane_env.switchboard.address,
    )

    amount = lane_env.scale
    quote = lane_env.quote(amount, 500)
    before = settlement_snapshot(lane_env)
    with boa.reverts("vault does not support asset"):
        lane_env.buy(
            amount,
            requested_lock=500,
            expected_epoch=quote.epoch,
        )

    assert settlement_snapshot(lane_env) == before


def test_locked_settlement_rejects_non_ripe_gov_core_vault(
    lane_env,
    simple_erc20_vault,
    vault_book,
    setAssetConfig,
):
    lane_env.set_config()
    lane_env.setup_lock_terms()
    source_id = lane_env.mission_control.coreRipeGovVaultId()
    wrong_id = vault_book.getRegId(simple_erc20_vault)
    assert wrong_id != 0
    setAssetConfig(lane_env.ripe_token, _vaultIds=[source_id, wrong_id])
    lane_env.mission_control.setCoreRipeGovVaultId(
        wrong_id,
        sender=lane_env.switchboard.address,
    )

    amount = lane_env.scale
    quote = lane_env.quote(amount, 500)
    before = settlement_snapshot(lane_env)
    wrong_vault_balance_before = lane_env.ripe_token.balanceOf(simple_erc20_vault)
    with boa.reverts():
        lane_env.buy(
            amount,
            requested_lock=500,
            expected_epoch=quote.epoch,
        )

    assert settlement_snapshot(lane_env) == before
    assert lane_env.ripe_token.balanceOf(simple_erc20_vault) == wrong_vault_balance_before


def test_locked_settlement_zero_core_pointer_fails_before_payment(
    lane_env,
    setAssetConfig,
):
    lane_env.set_config()
    lane_env.setup_lock_terms()
    lane_env.mission_control.eval("self.coreRipeGovVaultId = 0")
    # This removes Teller's vault-id-zero fallback. Without the lane-local guard the
    # downstream reason changes to `invalid asset`, so this assertion kills removal
    # of the guard rather than accepting Lootbox's identical `invalid vault id` text.
    setAssetConfig(lane_env.ripe_token, _vaultIds=[])
    amount = lane_env.scale
    quote = lane_env.quote(amount, 500)
    before = settlement_snapshot(lane_env)

    assert quote.available
    assert quote.actualLock == 500
    with boa.reverts("invalid vault id"):
        lane_env.buy(
            amount,
            requested_lock=500,
            expected_epoch=quote.epoch,
        )

    assert settlement_snapshot(lane_env) == before


@pytest.mark.parametrize(
    "decimals, receipt_bps",
    [(6, 0), (6, 5_000), (6, 15_000), (18, 5_000)],
)
@pytest.mark.parametrize("requested_lock", [0, 500])
def test_nonexact_payment_receipt_reverts_every_effect(
    lane_factory,
    charlie_token_whale,
    decimals,
    receipt_bps,
    requested_lock,
):
    token = boa.loads(
        NONEXACT_RECEIPT_TOKEN,
        charlie_token_whale,
        decimals,
        receipt_bps,
    )
    ctx = lane_factory(payment_token=token)
    ctx.set_config()
    if requested_lock:
        ctx.setup_lock_terms()

    amount = 10 * ctx.scale
    quote = ctx.quote(amount, requested_lock)
    before = settlement_snapshot(ctx)
    with boa.reverts("payment receipt mismatch"):
        ctx.buy(
            amount,
            requested_lock=requested_lock,
            expected_epoch=quote.epoch,
        )

    assert settlement_snapshot(ctx) == before


@pytest.mark.parametrize("decimals", [6, 18])
@pytest.mark.parametrize("requested_lock", [0, 500])
def test_no_return_payment_token_settles_exactly(
    lane_factory,
    charlie_token_whale,
    decimals,
    requested_lock,
):
    token = boa.loads(NO_RETURN_PAYMENT_TOKEN, charlie_token_whale, decimals)
    ctx = lane_factory(payment_token=token)
    ctx.set_config()
    if requested_lock:
        ctx.setup_lock_terms()

    amount = 10 * ctx.scale
    quote = ctx.quote(amount, requested_lock)
    payment_before = token.balanceOf(ctx.endaoment_funds)
    payout = ctx.buy(
        amount,
        requested_lock=requested_lock,
        expected_epoch=quote.epoch,
        min_ripe_out=quote.totalRipe,
    )

    assert payout == quote.totalRipe
    assert token.balanceOf(ctx.endaoment_funds) == payment_before + amount


@pytest.mark.parametrize("decimals", [6, 18])
@pytest.mark.parametrize("requested_lock", [0, 500])
def test_false_return_payment_token_reverts_every_effect(
    lane_factory,
    charlie_token_whale,
    decimals,
    requested_lock,
):
    token = boa.loads(FALSE_RETURN_PAYMENT_TOKEN, charlie_token_whale, decimals)
    ctx = lane_factory(payment_token=token)
    ctx.set_config()
    if requested_lock:
        ctx.setup_lock_terms()

    amount = 10 * ctx.scale
    quote = ctx.quote(amount, requested_lock)
    before = settlement_snapshot(ctx)
    with boa.reverts("payment failed"):
        ctx.buy(
            amount,
            requested_lock=requested_lock,
            expected_epoch=quote.epoch,
        )

    assert settlement_snapshot(ctx) == before


def test_intermediate_bonus_settlement_event_uses_the_bonus_bearing_lock(lane_env):
    lane_env.set_config(maxLockBonus=5_000)
    lane_env.setup_lock_terms(min_lock=100, max_lock=1_000)
    amount = 20 * lane_env.scale
    quote = lane_env.quote(amount, 550)

    payout = lane_env.buy(
        amount,
        requested_lock=550,
        expected_epoch=quote.epoch,
        min_ripe_out=quote.totalRipe,
    )
    logs = lane_env.lane.get_logs()
    purchase = next(
        log for log in logs if type(log).__name__ == "InstantBondPurchased"
    )
    deposit = next(
        log for log in logs if type(log).__name__ == "RipeGovVaultDeposit"
    )

    assert quote.actualLock == purchase.actualLock == deposit.lockDuration == 550
    assert quote.bonusRatio == purchase.bonusRatio == 2_500
    assert purchase.ripeGovVaultId == lane_env.mission_control.coreRipeGovVaultId()
    assert deposit.amount == payout == quote.totalRipe


def test_existing_position_uses_weighted_unlock_while_quote_discloses_increment(lane_env):
    lane_env.set_config(maxLockBonus=5_000)
    terms = lane_env.setup_lock_terms(min_lock=100, max_lock=1_000)

    prior_amount = 100 * 10**18
    lane_env.ripe_token.transfer(
        lane_env.ripe_gov_vault,
        prior_amount,
        sender=lane_env.ripe_whale,
    )
    lane_env.ripe_gov_vault.depositTokensWithLockDuration(
        lane_env.bob,
        lane_env.ripe_token,
        prior_amount,
        100,
        sender=lane_env.switchboard.address,
    )
    prior_data = lane_env.ripe_gov_vault.userGovData(
        lane_env.bob, lane_env.ripe_token
    )
    prior_shares = prior_data.lastShares
    prior_unlock = prior_data.unlock

    quote = lane_env.quote(10 * lane_env.scale, 1_000)
    lane_env.buy(
        10 * lane_env.scale,
        requested_lock=1_000,
        expected_epoch=quote.epoch,
        min_ripe_out=quote.totalRipe,
    )
    final_data = lane_env.ripe_gov_vault.userGovData(
        lane_env.bob, lane_env.ripe_token
    )
    new_shares = final_data.lastShares - prior_shares
    expected_unlock = lane_env.ripe_gov_vault.getWeightedLockOnTokenDeposit(
        new_shares,
        quote.actualLock,
        terms,
        prior_shares,
        prior_unlock,
    )

    actual_unlock = final_data.unlock
    assert new_shares > 0
    assert quote.actualLock == 1_000
    assert actual_unlock == expected_unlock
    assert prior_unlock < actual_unlock < boa.env.evm.patch.block_number + 1_000


def test_repeated_max_lock_purchases_measure_rounding_bonus_and_share_blocks(lane_env):
    lane_env.set_config(maxLockBonus=5_000)
    terms = lane_env.setup_lock_terms(min_lock=100, max_lock=1_000)

    prior_amount = 10_000 * 10**18
    lane_env.ripe_token.transfer(
        lane_env.ripe_gov_vault,
        prior_amount,
        sender=lane_env.ripe_whale,
    )
    lane_env.ripe_gov_vault.depositTokensWithLockDuration(
        lane_env.bob,
        lane_env.ripe_token,
        prior_amount,
        100,
        sender=lane_env.switchboard.address,
    )
    lane_env.ripe_token.transfer(
        lane_env.ripe_gov_vault,
        1,
        sender=lane_env.ripe_whale,
    )
    vault_balance_before = lane_env.ripe_token.balanceOf(lane_env.ripe_gov_vault)
    user_amount_before = lane_env.ripe_gov_vault.getTotalAmountForUser(
        lane_env.bob, lane_env.ripe_token
    )

    total_base = 0
    total_bonus = 0
    total_payout = 0
    incremental_share_blocks = []
    rounding_remainders = []
    observed_unlocks = []
    purchase_amount = 10 * lane_env.scale + 1

    for _ in range(5):
        before = lane_env.ripe_gov_vault.userGovData(
            lane_env.bob, lane_env.ripe_token
        )
        quote = lane_env.quote(purchase_amount, 1_000)
        expected_new_shares = lane_env.ripe_gov_vault.amountToShares(
            lane_env.ripe_token,
            quote.totalRipe,
            False,
        )
        expected_unlock = lane_env.ripe_gov_vault.getWeightedLockOnTokenDeposit(
            expected_new_shares,
            quote.actualLock,
            terms,
            before.lastShares,
            before.unlock,
        )

        lane_env.buy(
            purchase_amount,
            requested_lock=1_000,
            expected_epoch=quote.epoch,
            min_ripe_out=quote.totalRipe,
        )
        after = lane_env.ripe_gov_vault.userGovData(
            lane_env.bob, lane_env.ripe_token
        )
        actual_new_shares = after.lastShares - before.lastShares
        normalized_new_shares = max(actual_new_shares // 10**18, 1)
        rounding_remainder = actual_new_shares % 10**18

        assert quote.actualLock == 1_000
        assert quote.bonusRatio == 5_000
        assert quote.bonusRipe == quote.baseRipe * 5_000 // 10_000
        assert actual_new_shares == expected_new_shares
        assert after.unlock == expected_unlock
        assert 0 <= rounding_remainder < 10**18

        total_base += quote.baseRipe
        total_bonus += quote.bonusRipe
        total_payout += quote.totalRipe
        incremental_share_blocks.append(normalized_new_shares * quote.actualLock)
        rounding_remainders.append(rounding_remainder)
        observed_unlocks.append(after.unlock)

    final_amount = lane_env.ripe_gov_vault.getTotalAmountForUser(
        lane_env.bob, lane_env.ripe_token
    )
    assert total_payout == total_base + total_bonus
    assert total_base * 5_000 // 10_000 - 5 < total_bonus
    assert total_bonus <= total_base * 5_000 // 10_000
    assert lane_env.ripe_token.balanceOf(
        lane_env.ripe_gov_vault
    ) == vault_balance_before + total_payout
    assert final_amount > user_amount_before
    assert all(commitment > 0 for commitment in incremental_share_blocks)
    assert any(remainder != 0 for remainder in rounding_remainders)
    assert observed_unlocks == sorted(observed_unlocks)
    assert observed_unlocks[-1] < boa.env.evm.patch.block_number + 1_000


def test_accepted_expired_position_max_bonus_dilution_is_pinned(lane_env):
    lane_env.set_config(maxLockBonus=5_000)
    lane_env.setup_lock_terms(min_lock=100, max_lock=1_000)
    prior_amount = 100_000 * 10**18
    lane_env.ripe_token.transfer(
        lane_env.ripe_gov_vault,
        prior_amount,
        sender=lane_env.ripe_whale,
    )
    lane_env.ripe_gov_vault.depositTokensWithLockDuration(
        lane_env.bob,
        lane_env.ripe_token,
        prior_amount,
        100,
        sender=lane_env.switchboard.address,
    )
    boa.env.time_travel(blocks=101)

    amount = 10 * lane_env.scale
    quote = lane_env.quote(amount, 1_000)
    payout = lane_env.buy(
        amount,
        requested_lock=1_000,
        expected_epoch=quote.epoch,
        min_ripe_out=quote.totalRipe,
    )
    final_unlock = lane_env.ripe_gov_vault.userGovData(
        lane_env.bob,
        lane_env.ripe_token,
    ).unlock
    effective_duration = final_unlock - boa.env.evm.patch.block_number

    assert quote.bonusRatio == 5_000
    assert quote.bonusRipe == quote.baseRipe // 2
    assert payout == quote.totalRipe
    # Owner-accepted inherited RipeGov behavior: a dominant expired position can
    # dilute a 1,000-block bonus-bearing deposit to the one-block floor (0.1%).
    assert effective_duration == 1
    assert effective_duration * 1_000 == quote.actualLock


def test_exit_disclosure_and_bad_debt_freeze(lane_env):
    lane_env.set_config()
    amount = lane_env.scale
    lane_env.setup_lock_terms(
        min_lock=100,
        max_lock=1_000,
        can_exit=True,
        exit_fee=750,
        freeze_on_bad_debt=True,
    )

    healthy = lane_env.quote(amount, 500)
    assert healthy.canExitEarly
    assert healthy.exitFee == 750
    assert not healthy.isExitFrozen

    lane_env.ledger.setBadDebt(1, sender=lane_env.switchboard.address)
    frozen = lane_env.quote(amount, 500)
    assert frozen.canExitEarly
    assert frozen.exitFee == 750
    assert frozen.isExitFrozen

    lane_env.setup_lock_terms(
        min_lock=100,
        max_lock=1_000,
        can_exit=False,
        exit_fee=0,
        freeze_on_bad_debt=False,
    )
    no_exit = lane_env.quote(amount, 500)
    assert not no_exit.canExitEarly
    assert no_exit.exitFee == 0
    assert not no_exit.isExitFrozen

    unlocked = lane_env.quote(amount, 0)
    assert not unlocked.canExitEarly
    assert unlocked.exitFee == 0
    assert not unlocked.isExitFrozen


def test_deposit_gates_and_ripe_gov_pause_only_block_locked_path(lane_env):
    lane_env.set_config()
    amount = lane_env.scale

    lane_env.setup_lock_terms(can_deposit=False)
    locked = lane_env.quote(amount, 500)
    assert locked.available
    before_minted = lane_env.lane.cumulativeMinted()
    with boa.reverts("protocol deposits disabled"):
        lane_env.buy(
            amount,
            requested_lock=500,
            expected_epoch=locked.epoch,
        )
    assert lane_env.lane.cumulativeMinted() == before_minted
    lane_env.buy(amount, requested_lock=0, expected_epoch=locked.epoch)

    lane_env.setup_lock_terms(can_deposit=True)
    lane_env.ripe_gov_vault.pause(True, sender=lane_env.switchboard.address)
    assert lane_env.ripe_gov_vault.isPaused()
    locked = lane_env.quote(amount, 500)
    assert locked.available
    paused_snapshot = settlement_snapshot(lane_env)
    # Teller's outer deposit equality check exposes this stable reason rather than
    # the nested paused-vault diagnostic.
    with boa.reverts("deposit failed"):
        lane_env.buy(
            amount,
            requested_lock=500,
            expected_epoch=locked.epoch,
        )
    assert settlement_snapshot(lane_env) == paused_snapshot
    lane_env.buy(amount, requested_lock=0, expected_epoch=locked.epoch)

    lane_env.ripe_gov_vault.pause(False, sender=lane_env.switchboard.address)
    lane_env.setup_lock_terms(asset_can_deposit=False)
    locked = lane_env.quote(amount, 500)
    assert locked.available
    with boa.reverts("asset deposits disabled"):
        lane_env.buy(
            amount,
            requested_lock=500,
            expected_epoch=locked.epoch,
        )


def test_payment_mint_approval_and_teller_failures_are_fully_atomic(lane_env):
    lane_env.set_config()
    lane_env.setup_lock_terms()
    amount = lane_env.scale

    with boa.env.anchor():
        lane_env.payment_token.approve(lane_env.lane, 0, sender=lane_env.bob)
        before = settlement_snapshot(lane_env)
        quote = lane_env.quote(amount)
        with boa.reverts():
            lane_env.buy(amount, expected_epoch=quote.epoch)
        assert settlement_snapshot(lane_env) == before

    with boa.env.anchor():
        lane_env.ripe_token.pause(True, sender=lane_env.governance.address)
        before = settlement_snapshot(lane_env)
        quote = lane_env.quote(amount)
        with boa.reverts():
            lane_env.buy(amount, expected_epoch=quote.epoch)
        assert settlement_snapshot(lane_env) == before

    with boa.env.anchor():
        lane_env.switchboard_registry.setBlacklist(
            lane_env.ripe_token,
            lane_env.teller,
            True,
            sender=lane_env.switchboard.address,
        )
        before = settlement_snapshot(lane_env)
        quote = lane_env.quote(amount, 500)
        with boa.reverts():
            lane_env.buy(
                amount,
                requested_lock=500,
                expected_epoch=quote.epoch,
            )
        assert settlement_snapshot(lane_env) == before

    with boa.env.anchor():
        lane_env.setup_lock_terms(can_deposit=False)
        before = settlement_snapshot(lane_env)
        quote = lane_env.quote(amount, 500)
        with boa.reverts("protocol deposits disabled"):
            lane_env.buy(
                amount,
                requested_lock=500,
                expected_epoch=quote.epoch,
            )
        assert settlement_snapshot(lane_env) == before


def test_failed_rollover_settlement_restores_override_and_timing_state(lane_env):
    lane_env.set_config(maxLockBonus=0)
    lane_env.buy(50 * lane_env.scale)
    target_rate = 777_777_777_777_777_777
    lane_env.set_rate_override(target_rate)
    boa.env.time_travel(blocks=lane_env.epoch_length)

    projected = lane_env.quote(lane_env.scale)
    assert projected.rate == target_rate
    before = settlement_snapshot(lane_env)

    lane_env.ripe_token.pause(True, sender=lane_env.governance.address)
    with boa.reverts():
        lane_env.buy(
            lane_env.scale,
            expected_epoch=projected.epoch,
            min_ripe_out=projected.totalRipe,
        )
    assert settlement_snapshot(lane_env) == before
    assert lane_env.lane.rateOverride() == target_rate
    assert lane_env.lane.overrideVersion() == 1

    lane_env.ripe_token.pause(False, sender=lane_env.governance.address)
    lane_env.buy(
        lane_env.scale,
        expected_epoch=projected.epoch,
        min_ripe_out=projected.totalRipe,
    )
    assert lane_env.lane.epochRate() == target_rate
    assert lane_env.lane.epochAcceptedPayment() == lane_env.scale
    assert lane_env.lane.epochWeightedLateness() == 0
    assert lane_env.lane.rateOverride() == 0
    assert lane_env.lane.overrideVersion() == 2


def test_ripe_pause_and_blacklist_asymmetry(lane_env):
    lane_env.set_config()
    lane_env.setup_lock_terms()
    amount = lane_env.scale

    lane_env.ripe_token.pause(True, sender=lane_env.governance.address)
    unlocked = lane_env.quote(amount, 0)
    assert unlocked.available
    with boa.reverts():
        lane_env.buy(amount, expected_epoch=unlocked.epoch)
    locked = lane_env.quote(amount, 500)
    assert locked.available
    with boa.reverts():
        lane_env.buy(amount, requested_lock=500, expected_epoch=locked.epoch)
    assert lane_env.lane.cumulativeMinted() == 0

    lane_env.ripe_token.pause(False, sender=lane_env.governance.address)
    lane_env.switchboard_registry.setBlacklist(
        lane_env.ripe_token,
        lane_env.bob,
        True,
        sender=lane_env.switchboard.address,
    )
    unlocked = lane_env.quote(amount, 0)
    assert unlocked.available
    with boa.reverts():
        lane_env.buy(amount, expected_epoch=unlocked.epoch)

    locked = lane_env.quote(amount, 500)
    payout = lane_env.buy(
        amount,
        requested_lock=500,
        expected_epoch=locked.epoch,
    )
    assert payout == locked.totalRipe
    assert lane_env.ripe_gov_vault.getTotalAmountForUser(
        lane_env.bob, lane_env.ripe_token
    ) == payout


def test_teller_deposit_mismatch_reverts_every_effect(lane_env):
    lane_env.set_config()
    lane_env.setup_lock_terms()
    mismatch_teller = boa.loads(MISMATCH_TELLER)
    replace_teller(lane_env, mismatch_teller)

    amount = lane_env.scale
    quote = lane_env.quote(amount, 500)
    before = settlement_snapshot(lane_env)
    with boa.reverts("deposit mismatch"):
        lane_env.buy(
            amount,
            requested_lock=500,
            expected_epoch=quote.epoch,
        )

    assert settlement_snapshot(lane_env) == before


def test_teller_allowance_reset_clears_partial_pull_safety_net(lane_env):
    lane_env.set_config()
    lane_env.setup_lock_terms()
    partial_teller = boa.loads(PARTIAL_PULL_TELLER)
    replace_teller(lane_env, partial_teller)

    amount = lane_env.scale
    quote = lane_env.quote(amount, 500)
    payout = lane_env.buy(
        amount,
        requested_lock=500,
        expected_epoch=quote.epoch,
        min_ripe_out=quote.totalRipe,
    )

    assert lane_env.ripe_token.balanceOf(partial_teller) == payout - 1
    assert lane_env.ripe_token.balanceOf(lane_env.lane) == 1
    assert lane_env.ripe_token.allowance(lane_env.lane, partial_teller) == 0
