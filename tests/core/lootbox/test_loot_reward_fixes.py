import boa

from conf_utils import clear_transient_storage
from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS

MODE_PASSIVE = 0
MODE_REENTER_CLAIM = 1
MODE_REENTER_DISTRIBUTE = 2
MODE_FAIL = 3
MODE_STAB_CLAIM = 4

# Test-only distributor that doubles as the underscore registry: getAddr
# answers only UNDERSCORE_LOOT_DISTRIBUTOR_ID with itself so every other
# underscore lookup (wallet/vault/ledger probes) fails closed. Its
# addDepositRewards callback records what a real distributor sees
# mid-distribution and can reenter the protocol through real public routes
# or fail, driven by `mode`.
REWARD_FIX_DISTRIBUTOR_SOURCE = """
# @version 0.4.3

from ethereum.ercs import IERC20

interface LootboxDist:
    def distributeUnderscoreRewards() -> (uint256, uint256): nonpayable
    def lastUnderscoreSend() -> uint256: view

interface TellerClaim:
    def claimLoot(_user: address, _shouldStake: bool) -> uint256: nonpayable
    def claimManyFromStabilityPool(_vaultId: uint256, _claims: DynArray[StabPoolClaim, 15], _user: address, _shouldAutoDeposit: bool) -> uint256: nonpayable

interface LedgerView:
    def ripeAvailForRewards() -> uint256: view

struct StabPoolClaim:
    stabAsset: address
    claimAsset: address
    maxUsdValue: uint256

MODE_PASSIVE: constant(uint256) = 0
MODE_REENTER_CLAIM: constant(uint256) = 1
MODE_REENTER_DISTRIBUTE: constant(uint256) = 2
MODE_FAIL: constant(uint256) = 3
MODE_STAB_CLAIM: constant(uint256) = 4

# Lootbox.UNDERSCORE_LOOT_DISTRIBUTOR_ID
UNDERSCORE_LOOT_DISTRIBUTOR_ID: constant(uint256) = 6

lootbox: public(address)
teller: public(address)
ledger: public(address)
mode: public(uint256)
didReenter: public(bool)
observedAvail: public(uint256)
observedLastSend: public(uint256)
reenteredClaimAmount: public(uint256)
stabVaultId: public(uint256)
stabAsset: public(address)
stabClaimAsset: public(address)
claimedStabUsdValue: public(uint256)


@deploy
def __init__(_lootbox: address, _teller: address, _ledger: address):
    self.lootbox = _lootbox
    self.teller = _teller
    self.ledger = _ledger


@view
@external
def getAddr(_regId: uint256) -> address:
    # act as the loot distributor only; other underscore lookups fail closed
    if _regId == UNDERSCORE_LOOT_DISTRIBUTOR_ID:
        return self
    return empty(address)


@external
def setMode(_mode: uint256):
    self.mode = _mode
    self.didReenter = False


@external
def setStabClaim(_vaultId: uint256, _stabAsset: address, _claimAsset: address):
    self.stabVaultId = _vaultId
    self.stabAsset = _stabAsset
    self.stabClaimAsset = _claimAsset


@external
def addDepositRewards(_asset: address, _amount: uint256):
    self.observedAvail = staticcall LedgerView(self.ledger).ripeAvailForRewards()
    self.observedLastSend = staticcall LootboxDist(self.lootbox).lastUnderscoreSend()

    mode: uint256 = self.mode
    if mode == MODE_FAIL:
        raise "distributor rejected"

    if mode == MODE_REENTER_CLAIM and not self.didReenter:
        self.didReenter = True
        self.reenteredClaimAmount = extcall TellerClaim(self.teller).claimLoot(self, False)

    if mode == MODE_STAB_CLAIM and not self.didReenter:
        self.didReenter = True
        claims: DynArray[StabPoolClaim, 15] = [StabPoolClaim(
            stabAsset=self.stabAsset,
            claimAsset=self.stabClaimAsset,
            maxUsdValue=max_value(uint256),
        )]
        self.claimedStabUsdValue = extcall TellerClaim(self.teller).claimManyFromStabilityPool(self.stabVaultId, claims, self, False)

    if mode == MODE_REENTER_DISTRIBUTE:
        if not self.didReenter:
            self.didReenter = True
            extcall LootboxDist(self.lootbox).distributeUnderscoreRewards()
        return

    assert extcall IERC20(_asset).transferFrom(msg.sender, self, _amount, default_return_value=True) # dev: pull failed
"""


def _deploy_reward_fix_distributor(lootbox, teller, ledger):
    return boa.loads(
        REWARD_FIX_DISTRIBUTOR_SOURCE,
        lootbox.address,
        teller.address,
        ledger.address,
        name="reward_fix_distributor",
        override_address=boa.env.generate_address(),
    )


def _setup_borrow_loot(user, ledger, lootbox, teller, credit_engine, createDebtTerms):
    # synthetic defense-in-depth: positive current debt with a raw vault count
    # of zero cannot arise from normal borrowing (borrowing requires deposited
    # collateral); it is seeded directly through the Ledger test route
    debt_terms = createDebtTerms()
    user_debt = (100 * EIGHTEEN_DECIMALS, 100 * EIGHTEEN_DECIMALS, debt_terms, 0, False)
    ledger.setUserDebt(user, user_debt, 0, (0, 0), sender=credit_engine.address)
    lootbox.updateBorrowPoints(user, sender=teller.address)
    boa.env.time_travel(blocks=20)
    lootbox.updateBorrowPoints(user, sender=teller.address)


#########################################
# Claim switch on every dedicated route #
#########################################


def test_claim_switch_gates_dedicated_deposit_claim(
    bob,
    governance,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
    switchboard_alpha,
):
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setRipeRewardsConfig()
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    boa.env.time_travel(blocks=20)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    claimable = lootbox.getClaimableDepositLootForAsset(bob, vault_id, alpha_token)
    assert claimable > 0

    # disable the protocol-wide switch through its governance route
    assert switchboard_alpha.setCanClaimLoot(False, sender=governance.address)

    points_before = ledger.userDepositPoints(bob, vault_id, alpha_token)
    avail_before = ledger.ripeAvailForRewards()
    balance_before = ripe_token.balanceOf(bob)
    supply_before = ripe_token.totalSupply()

    with boa.reverts(dev="loot claims disabled"):
        lootbox.claimDepositLootForAsset(bob, vault_id, alpha_token, sender=teller.address)

    # claim state is identical after the reverted call
    points_after = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert points_after.balancePoints == points_before.balancePoints
    assert points_after.lastUpdate == points_before.lastUpdate
    assert ledger.ripeAvailForRewards() == avail_before
    assert ripe_token.balanceOf(bob) == balance_before
    assert ripe_token.totalSupply() == supply_before
    assert lootbox.getClaimableDepositLootForAsset(bob, vault_id, alpha_token) == claimable

    # re-enabled claims still succeed with the original payout
    assert switchboard_alpha.setCanClaimLoot(True, sender=governance.address)
    total_ripe = lootbox.claimDepositLootForAsset(bob, vault_id, alpha_token, sender=teller.address)
    assert total_ripe == claimable
    assert ripe_token.balanceOf(bob) == balance_before + total_ripe
    assert ledger.userDepositPoints(bob, vault_id, alpha_token).balancePoints == 0


def test_claim_switch_gates_dedicated_borrow_claim(
    bob,
    governance,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
    ripe_token,
    switchboard_alpha,
):
    setGeneralConfig()
    setRipeRewardsConfig(True)
    _setup_borrow_loot(bob, ledger, lootbox, teller, credit_engine, createDebtTerms)

    claimable = lootbox.getClaimableBorrowLoot(bob)
    assert claimable > 0

    assert switchboard_alpha.setCanClaimLoot(False, sender=governance.address)

    points_before = ledger.userBorrowPoints(bob)
    global_before = ledger.globalBorrowPoints()
    avail_before = ledger.ripeAvailForRewards()
    balance_before = ripe_token.balanceOf(bob)
    supply_before = ripe_token.totalSupply()

    with boa.reverts(dev="loot claims disabled"):
        lootbox.claimBorrowLoot(bob, sender=teller.address)

    assert ledger.userBorrowPoints(bob) == points_before
    assert ledger.globalBorrowPoints() == global_before
    assert ledger.ripeAvailForRewards() == avail_before
    assert ripe_token.balanceOf(bob) == balance_before
    assert ripe_token.totalSupply() == supply_before
    assert lootbox.getClaimableBorrowLoot(bob) == claimable

    assert switchboard_alpha.setCanClaimLoot(True, sender=governance.address)
    total_ripe = lootbox.claimBorrowLoot(bob, sender=teller.address)
    assert total_ripe == claimable
    assert ripe_token.balanceOf(bob) == balance_before + total_ripe
    assert ledger.userBorrowPoints(bob).points == 0


def test_claim_switch_blocks_zero_payout_attempts(
    sally,
    governance,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    alpha_token,
    ripe_token,
    switchboard_alpha,
):
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setRipeRewardsConfig()
    vault_id = vault_book.getRegId(simple_erc20_vault)

    # sally has no loot at all; a disabled attempt must still revert
    assert lootbox.getClaimableBorrowLoot(sally) == 0

    assert switchboard_alpha.setCanClaimLoot(False, sender=governance.address)

    user_points_before = ledger.userBorrowPoints(sally)
    global_points_before = ledger.globalBorrowPoints()
    deposit_points_before = ledger.userDepositPoints(sally, vault_id, alpha_token)
    rewards_before = ledger.ripeRewards()
    avail_before = ledger.ripeAvailForRewards()
    balance_before = ripe_token.balanceOf(sally)
    supply_before = ripe_token.totalSupply()

    with boa.reverts(dev="loot claims disabled"):
        lootbox.claimBorrowLoot(sally, sender=teller.address)
    with boa.reverts(dev="loot claims disabled"):
        lootbox.claimDepositLootForAsset(sally, vault_id, alpha_token, sender=teller.address)

    assert ledger.userBorrowPoints(sally) == user_points_before
    assert ledger.globalBorrowPoints() == global_points_before
    assert ledger.userDepositPoints(sally, vault_id, alpha_token) == deposit_points_before
    assert ledger.ripeRewards() == rewards_before
    assert ledger.ripeAvailForRewards() == avail_before
    assert ripe_token.balanceOf(sally) == balance_before
    assert ripe_token.totalSupply() == supply_before

    assert switchboard_alpha.setCanClaimLoot(True, sender=governance.address)
    assert lootbox.claimBorrowLoot(sally, sender=teller.address) == 0
    assert lootbox.claimDepositLootForAsset(sally, vault_id, alpha_token, sender=teller.address) == 0


def test_charlie_dedicated_deposit_route_respects_claim_switch(
    bob,
    governance,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    performDeposit,
    simple_erc20_vault,
    vault_book,
    ledger,
    lootbox,
    teller,
    ripe_token,
    alpha_token,
    alpha_token_whale,
    switchboard_alpha,
    switchboard_charlie,
):
    # SwitchboardCharlie.claimDepositLootForAsset is the actual in-protocol
    # dedicated deposit route; dedicated claimBorrowLoot currently has no
    # in-protocol caller
    setGeneralConfig()
    setAssetConfig(alpha_token)
    setRipeRewardsConfig()
    performDeposit(bob, 100 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    boa.env.time_travel(blocks=20)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    lootbox.updateDepositPoints(bob, vault_id, simple_erc20_vault, alpha_token, sender=teller.address)

    claimable = lootbox.getClaimableDepositLootForAsset(bob, vault_id, alpha_token)
    assert claimable > 0

    assert switchboard_alpha.setCanClaimLoot(False, sender=governance.address)

    points_before = ledger.userDepositPoints(bob, vault_id, alpha_token)
    asset_points_before = ledger.assetDepositPoints(vault_id, alpha_token)
    global_points_before = ledger.globalDepositPoints()
    rewards_before = ledger.ripeRewards()
    avail_before = ledger.ripeAvailForRewards()
    balance_before = ripe_token.balanceOf(bob)
    supply_before = ripe_token.totalSupply()

    with boa.reverts(dev="loot claims disabled"):
        switchboard_charlie.claimDepositLootForAsset(bob, vault_id, alpha_token, sender=governance.address)

    points_after = ledger.userDepositPoints(bob, vault_id, alpha_token)
    assert points_after.balancePoints == points_before.balancePoints
    assert points_after.lastUpdate == points_before.lastUpdate
    assert ledger.assetDepositPoints(vault_id, alpha_token) == asset_points_before
    assert ledger.globalDepositPoints() == global_points_before
    assert ledger.ripeRewards() == rewards_before
    assert ledger.ripeAvailForRewards() == avail_before
    assert ripe_token.balanceOf(bob) == balance_before
    assert ripe_token.totalSupply() == supply_before
    assert lootbox.getClaimableDepositLootForAsset(bob, vault_id, alpha_token) == claimable

    # re-enabled: Charlie delivers the original entitlement exactly once
    assert switchboard_alpha.setCanClaimLoot(True, sender=governance.address)
    ripe_amount = switchboard_charlie.claimDepositLootForAsset(bob, vault_id, alpha_token, sender=governance.address)
    assert ripe_amount == claimable
    assert ripe_token.balanceOf(bob) == balance_before + ripe_amount
    assert ledger.userDepositPoints(bob, vault_id, alpha_token).balancePoints == 0
    assert switchboard_charlie.claimDepositLootForAsset(bob, vault_id, alpha_token, sender=governance.address) == 0


###########################################################
# Underscore rewards: persist before external interaction #
###########################################################


def test_underscore_distribution_reserves_before_external_interaction(
    setGeneralConfig,
    setRipeRewardsConfig,
    mission_control,
    switchboard_alpha,
    ledger,
    lootbox,
    teller,
    ripe_token,
):
    setGeneralConfig()
    setRipeRewardsConfig(True, 0, 100_00, 0, 0, 0)  # no per-block drip: only the undy reservation moves
    mock = _deploy_reward_fix_distributor(lootbox, teller, ledger)
    mission_control.setUnderscoreRegistry(mock.address, sender=switchboard_alpha.address)

    avail = 500 * EIGHTEEN_DECIMALS
    ledger.setRipeAvailForRewards(avail, sender=switchboard_alpha.address)
    boa.env.time_travel(blocks=lootbox.underscoreSendInterval() + 1)

    supply_before = ripe_token.totalSupply()
    current_block = boa.env.evm.patch.block_number

    deposit_rewards, yield_bonus = lootbox.distributeUnderscoreRewards(sender=switchboard_alpha.address)
    assert deposit_rewards == 100 * EIGHTEEN_DECIMALS
    assert yield_bonus == 100 * EIGHTEEN_DECIMALS
    total = deposit_rewards + yield_bonus

    # mid-callback, the distributor already saw the completed reservation
    assert mock.observedAvail() == avail - total
    assert mock.observedLastSend() == current_block

    # the successful distribution preserves timestamp, ledger, mint, and transfers
    assert lootbox.lastUnderscoreSend() == current_block
    assert ledger.ripeAvailForRewards() == avail - total
    assert ripe_token.balanceOf(mock.address) == total
    assert ripe_token.totalSupply() == supply_before + total


def test_reentering_claim_cannot_consume_reserved_capacity(
    setGeneralConfig,
    setRipeRewardsConfig,
    mission_control,
    switchboard_alpha,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
    ripe_token,
):
    setGeneralConfig()
    rate = EIGHTEEN_DECIMALS
    setRipeRewardsConfig(True, rate, 100_00, 0, 0, 0)
    mock = _deploy_reward_fix_distributor(lootbox, teller, ledger)
    mock.setMode(MODE_REENTER_CLAIM)
    mission_control.setUnderscoreRegistry(mock.address, sender=switchboard_alpha.address)

    # the distributor is itself a borrower so its callback can claim through Teller
    debt_terms = createDebtTerms()
    user_debt = (100 * EIGHTEEN_DECIMALS, 100 * EIGHTEEN_DECIMALS, debt_terms, 0, False)
    ledger.setUserDebt(mock.address, user_debt, 0, (0, 0), sender=credit_engine.address)
    lootbox.updateBorrowPoints(mock.address, sender=teller.address)

    elapsed = lootbox.underscoreSendInterval() + 1
    drip = elapsed * rate
    undy_total = lootbox.undyDepositRewardsAmount() + lootbox.undyYieldBonusAmount()
    # margin above (drip + undy) so a double-decrement is visible instead of clamping at zero
    avail = 2 * drip + undy_total + 1
    ledger.setRipeAvailForRewards(avail, sender=switchboard_alpha.address)
    bucket_before = ledger.ripeRewards().borrowers

    boa.env.time_travel(blocks=elapsed)
    clear_transient_storage()

    deposit_rewards, yield_bonus = lootbox.distributeUnderscoreRewards(sender=switchboard_alpha.address)
    assert deposit_rewards + yield_bonus == undy_total

    # the reentering claim received only what the buckets legitimately held
    claimed = mock.reenteredClaimAmount()
    assert claimed == bucket_before + drip

    # available capacity was consumed exactly once: the drip plus the undy reservation
    assert ledger.ripeAvailForRewards() == avail - drip - undy_total
    assert ledger.ripeRewards().borrowers == 0
    assert ripe_token.balanceOf(mock.address) == claimed + undy_total

    # the same reward cannot be delivered twice
    clear_transient_storage()
    balance_before = ripe_token.balanceOf(mock.address)
    assert teller.claimLoot(mock.address, False, sender=mock.address) == 0
    assert ripe_token.balanceOf(mock.address) == balance_before
    assert ledger.ripeRewards().borrowers == 0


def test_reentering_distribution_reverts_too_early(
    governance,
    setGeneralConfig,
    setRipeRewardsConfig,
    mission_control,
    switchboard,
    switchboard_alpha,
    ledger,
    lootbox,
    teller,
    ripe_token,
):
    setGeneralConfig()
    setRipeRewardsConfig(True, 0, 100_00, 0, 0, 0)
    mock = _deploy_reward_fix_distributor(lootbox, teller, ledger)

    # the reentering call must pass the switchboard perms gate to reach the interval check
    assert switchboard.startAddNewAddressToRegistry(mock.address, "reenter distributor", sender=governance.address)
    boa.env.time_travel(blocks=switchboard.registryChangeTimeLock())
    assert switchboard.confirmNewAddressToRegistry(mock.address, sender=governance.address) > 0

    mock.setMode(MODE_REENTER_DISTRIBUTE)
    mission_control.setUnderscoreRegistry(mock.address, sender=switchboard_alpha.address)
    ledger.setRipeAvailForRewards(1_000 * EIGHTEEN_DECIMALS, sender=switchboard_alpha.address)
    boa.env.time_travel(blocks=lootbox.underscoreSendInterval() + 1)

    last_send_before = lootbox.lastUnderscoreSend()
    avail_before = ledger.ripeAvailForRewards()
    supply_before = ripe_token.totalSupply()

    with boa.reverts(dev="too early"):
        lootbox.distributeUnderscoreRewards(sender=switchboard_alpha.address)

    assert lootbox.lastUnderscoreSend() == last_send_before
    assert ledger.ripeAvailForRewards() == avail_before
    assert ripe_token.totalSupply() == supply_before


def test_failed_distributor_call_restores_state(
    setGeneralConfig,
    setRipeRewardsConfig,
    mission_control,
    switchboard_alpha,
    ledger,
    lootbox,
    teller,
    ripe_token,
):
    setGeneralConfig()
    setRipeRewardsConfig(True, 0, 100_00, 0, 0, 0)
    mock = _deploy_reward_fix_distributor(lootbox, teller, ledger)
    mock.setMode(MODE_FAIL)
    mission_control.setUnderscoreRegistry(mock.address, sender=switchboard_alpha.address)

    avail = 500 * EIGHTEEN_DECIMALS
    ledger.setRipeAvailForRewards(avail, sender=switchboard_alpha.address)
    boa.env.time_travel(blocks=lootbox.underscoreSendInterval() + 1)

    last_send_before = lootbox.lastUnderscoreSend()
    rewards_before = ledger.ripeRewards()
    supply_before = ripe_token.totalSupply()
    balance_before = ripe_token.balanceOf(mock.address)

    with boa.reverts("distributor rejected"):
        lootbox.distributeUnderscoreRewards(sender=switchboard_alpha.address)

    # timestamp, ledger accounting, mint, and distribution all reverted together
    assert lootbox.lastUnderscoreSend() == last_send_before
    assert ledger.ripeAvailForRewards() == avail
    assert ledger.ripeRewards() == rewards_before
    assert ripe_token.totalSupply() == supply_before
    assert ripe_token.balanceOf(mock.address) == balance_before

    # once the distributor behaves, the same distribution succeeds
    mock.setMode(MODE_PASSIVE)
    current_block = boa.env.evm.patch.block_number
    deposit_rewards, yield_bonus = lootbox.distributeUnderscoreRewards(sender=switchboard_alpha.address)
    total = deposit_rewards + yield_bonus
    assert total == 200 * EIGHTEEN_DECIMALS
    assert lootbox.lastUnderscoreSend() == current_block
    assert ledger.ripeAvailForRewards() == avail - total
    assert ripe_token.balanceOf(mock.address) == balance_before + total


def test_underscore_callback_real_stability_claim_sees_reserved_budget(
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    mission_control,
    switchboard_alpha,
    ledger,
    lootbox,
    teller,
    ripe_token,
    ripe_gov_vault,
    stability_pool,
    vault_book,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    auction_house,
    savings_green,
    mock_price_source,
):
    # The distributor's callback performs a REAL Stability claim:
    # StabVault -> VaultBook.mintRipeForStabPoolClaims ->
    # Ledger.didGetRewardsFromStabClaims. Setup mirrors the module-scoped
    # setupStabPoolClaimsRewards fixture in tests/vaults/modules/
    # test_stab_vault_claims.py, copied inline because that fixture cannot be
    # injected across modules.
    setGeneralConfig()
    ripe_per_dollar = EIGHTEEN_DECIMALS  # 1 RIPE per claimed dollar
    setRipeRewardsConfig(True, 1, 10_00, 90_00, 0, 0, _stabPoolRipePerDollarClaimed=ripe_per_dollar)
    mission_control.setRipeGovVaultConfig(
        ripe_token,
        100_00,
        False,
        (0, 1_000, 100_00, False, 0),
        sender=switchboard_alpha.address,
    )
    core_id = mission_control.coreRipeGovVaultId()
    assert core_id != 0
    setAssetConfig(ripe_token, _vaultIds=[core_id])
    setAssetConfig(bravo_token)
    price = EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, price)
    mock_price_source.setPrice(bravo_token, price)
    mock_price_source.setPrice(ripe_token, price)

    mock = _deploy_reward_fix_distributor(lootbox, teller, ledger)
    stab_vault_id = vault_book.getRegId(stability_pool)
    mock.setStabClaim(stab_vault_id, alpha_token.address, bravo_token.address)
    mock.setMode(MODE_STAB_CLAIM)
    mission_control.setUnderscoreRegistry(mock.address, sender=switchboard_alpha.address)

    # Stability entitlement for the distributor itself: deposit then a
    # liquidation swap leaves it claimable bravo worth 10 USD
    deposit_amount = 10 * EIGHTEEN_DECIMALS
    alpha_token.transfer(stability_pool, deposit_amount, sender=alpha_token_whale)
    stability_pool.depositTokensInVault(mock.address, alpha_token, deposit_amount, sender=teller.address)
    bravo_token.transfer(stability_pool, deposit_amount, sender=bravo_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        alpha_token,
        deposit_amount,
        bravo_token,
        deposit_amount,
        ZERO_ADDRESS,
        alpha_token,
        savings_green,
        sender=auction_house.address,
    )

    # flush pending accrual, then budget exactly gross drip + undy + margin
    lootbox.updateRipeRewards(sender=teller.address)
    # the fixture's send interval is 43_200 blocks; travelling one block past
    # it (elapsed = 43_201) satisfies the send gate and defines the drip window
    interval = lootbox.underscoreSendInterval()
    elapsed = interval + 1
    gross_drip = elapsed * 1  # ripePerBlock = 1
    borrower_credit = gross_drip * 10_00 // 100_00
    staker_credit = gross_drip * 90_00 // 100_00
    # the floored credits (4_320 + 38_880) leave exactly one wei of gross terminal dust
    assert gross_drip - borrower_credit - staker_credit == 1
    undy_total = lootbox.undyDepositRewardsAmount() + lootbox.undyYieldBonusAmount()
    stability_margin = 7 * EIGHTEEN_DECIMALS
    stab_entitlement = deposit_amount * ripe_per_dollar // EIGHTEEN_DECIMALS
    assert stab_entitlement > stability_margin
    initial_budget = gross_drip + undy_total + stability_margin
    ledger.setRipeAvailForRewards(initial_budget, sender=switchboard_alpha.address)

    rewards_before = ledger.ripeRewards()
    supply_before = ripe_token.totalSupply()
    gov_before = ripe_gov_vault.getTotalAmountForUser(mock.address, ripe_token)
    bravo_before = bravo_token.balanceOf(mock.address)
    ripe_before = ripe_token.balanceOf(mock.address)

    boa.env.time_travel(blocks=elapsed)
    clear_transient_storage()
    current_block = boa.env.evm.patch.block_number

    deposit_rewards, yield_bonus = lootbox.distributeUnderscoreRewards(sender=switchboard_alpha.address)
    assert deposit_rewards + yield_bonus == undy_total

    # mid-callback the gross drip (including its one wei of terminal dust)
    # and the underscore amount were already charged: only the margin remains
    assert mock.observedAvail() == stability_margin
    assert mock.observedLastSend() == current_block

    # gross reservation persisted before the callback: buckets hold the
    # floored credits while the full gross (credits + one wei of dust) was charged
    stored = ledger.ripeRewards()
    assert stored.borrowers == rewards_before.borrowers + borrower_credit
    assert stored.stakers == rewards_before.stakers + staker_credit

    # the real Stability claim was capped at the margin despite a larger
    # entitlement, and its reward landed in the claimer's RipeGov position
    assert mock.claimedStabUsdValue() == deposit_amount
    gov_delta = ripe_gov_vault.getTotalAmountForUser(mock.address, ripe_token) - gov_before
    assert gov_delta == stability_margin

    # exact reconciliation: budget, supply, and balances
    assert ledger.ripeAvailForRewards() == 0
    assert ripe_token.totalSupply() == supply_before + undy_total + stability_margin
    assert ripe_token.balanceOf(mock.address) == ripe_before + undy_total
    assert bravo_token.balanceOf(mock.address) == bravo_before + deposit_amount
    assert lootbox.lastUnderscoreSend() == current_block


###############################################
# Gross-drip reservation (restored baseline)  #
###############################################


def test_gross_drip_reservation_charges_full_distribution(
    setGeneralConfig,
    setRipeRewardsConfig,
    switchboard_alpha,
    ledger,
    lootbox,
    teller,
):
    # restored baseline policy: the full gross distribution is reserved even
    # when the floored bucket credits sum to less
    setGeneralConfig()
    setRipeRewardsConfig(True, 19, 10_00, 90_00, 0, 0)

    # flush pending accrual so the next update spans exactly one block
    lootbox.updateRipeRewards(sender=teller.address)
    ledger.setRipeAvailForRewards(19, sender=switchboard_alpha.address)
    rewards_before = ledger.ripeRewards()

    boa.env.time_travel(blocks=1)
    updated = lootbox.updateRipeRewards(sender=teller.address)

    # gross 19 at 10_00/90_00: floored credits are 1 and 17
    assert updated.borrowers == rewards_before.borrowers + 1
    assert updated.stakers == rewards_before.stakers + 17
    assert updated.voters == rewards_before.voters
    assert updated.genDepositors == rewards_before.genDepositors

    # the reservation is the full gross distribution
    assert updated.newRipeRewards == 19
    stored = ledger.ripeRewards()
    assert stored.newRipeRewards == 19
    assert stored.borrowers == rewards_before.borrowers + 1
    assert stored.stakers == rewards_before.stakers + 17

    # the unassigned one wei was charged as gross terminal dust: the budget
    # is exhausted even though only 18 wei landed in buckets
    assert ledger.ripeAvailForRewards() == 0


def test_exactly_divisible_distribution_fully_reserved(
    setGeneralConfig,
    setRipeRewardsConfig,
    switchboard_alpha,
    ledger,
    lootbox,
    teller,
):
    setGeneralConfig()
    setRipeRewardsConfig(True, 100, 10_00, 90_00, 0, 0)

    lootbox.updateRipeRewards(sender=teller.address)
    ledger.setRipeAvailForRewards(100, sender=switchboard_alpha.address)
    rewards_before = ledger.ripeRewards()

    boa.env.time_travel(blocks=1)
    updated = lootbox.updateRipeRewards(sender=teller.address)

    assert updated.borrowers == rewards_before.borrowers + 10
    assert updated.stakers == rewards_before.stakers + 90
    assert updated.newRipeRewards == 100
    assert ledger.ripeAvailForRewards() == 0


######################################################
# Zero-vault borrow claims still deliver their payout #
######################################################


def test_zero_vault_positive_borrow_claim_delivers(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
    ripe_token,
):
    setGeneralConfig()
    setRipeRewardsConfig(True)
    _setup_borrow_loot(bob, ledger, lootbox, teller, credit_engine, createDebtTerms)

    # borrow loot only: bob never deposited, so the raw vault count is zero
    assert ledger.numUserVaults(bob) == 0
    claimable = lootbox.getClaimableBorrowLoot(bob)
    assert claimable > 0

    balance_before = ripe_token.balanceOf(bob)
    total_ripe = lootbox.claimLootForUser(bob, bob, False, sender=teller.address)

    # the claim returns and delivers the same positive amount, exactly once
    assert total_ripe == claimable
    assert ripe_token.balanceOf(bob) == balance_before + total_ripe
    assert ledger.userBorrowPoints(bob).points == 0

    # a repeated claim cannot receive the same reward again
    assert lootbox.claimLootForUser(bob, bob, False, sender=teller.address) == 0
    assert ripe_token.balanceOf(bob) == balance_before + total_ripe


def test_teller_default_stake_zero_vault_borrow_claim(
    bob,
    setGeneralConfig,
    setAssetConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
    ripe_token,
    ripe_gov_vault,
    mission_control,
    switchboard_alpha,
    mock_price_source,
):
    # Teller-level route with the default _shouldStake=True: the delivered
    # borrow loot lands in the core RipeGov vault, not the wallet.
    # This exercises a synthetic defense-in-depth state (positive current debt
    # with a raw vault count of zero, seeded through the Ledger test route),
    # not an ordinary borrower lifecycle -- normal borrowing requires
    # deposited collateral, which registers a vault.
    setGeneralConfig()
    setRipeRewardsConfig(True)
    mission_control.setRipeGovVaultConfig(
        ripe_token,
        100_00,
        False,
        (0, 1_000, 100_00, False, 0),
        sender=switchboard_alpha.address,
    )
    core_id = mission_control.coreRipeGovVaultId()
    assert core_id != 0
    setAssetConfig(ripe_token, _vaultIds=[core_id])
    mock_price_source.setPrice(ripe_token, EIGHTEEN_DECIMALS)

    _setup_borrow_loot(bob, ledger, lootbox, teller, credit_engine, createDebtTerms)
    assert ledger.numUserVaults(bob) == 0
    claimable = lootbox.getClaimableBorrowLoot(bob)
    assert claimable > 0

    wallet_before = ripe_token.balanceOf(bob)
    gov_before = ripe_gov_vault.getTotalAmountForUser(bob, ripe_token)

    clear_transient_storage()
    total_ripe = teller.claimLoot(bob, sender=bob)
    assert total_ripe == claimable

    # staked delivery: wallet unchanged, RipeGov position receives the amount
    assert ripe_token.balanceOf(bob) == wallet_before
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == gov_before + total_ripe
    assert ledger.userBorrowPoints(bob).points == 0

    # a second claim cannot deliver the same reward again
    clear_transient_storage()
    assert teller.claimLoot(bob, sender=bob) == 0
    assert ripe_gov_vault.getTotalAmountForUser(bob, ripe_token) == gov_before + total_ripe


def test_zero_vault_zero_payout_claim_safe_without_core_pointer(
    sally,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    mission_control,
    ripe_token,
):
    setGeneralConfig()
    setRipeRewardsConfig(True)

    assert ledger.numUserVaults(sally) == 0
    supply_before = ripe_token.totalSupply()

    # the zero-payout, zero-vault path must not read the core vault pointer
    mission_control.eval("self.coreRipeGovVaultId = 0")
    assert lootbox.claimLootForUser(sally, sally, False, sender=teller.address) == 0
    assert ripe_token.totalSupply() == supply_before


def test_zero_vault_positive_claim_unset_pointer_rolls_back_atomically(
    bob,
    setGeneralConfig,
    setRipeRewardsConfig,
    ledger,
    lootbox,
    teller,
    credit_engine,
    createDebtTerms,
    ripe_token,
    mission_control,
):
    setGeneralConfig()
    setRipeRewardsConfig(True)
    _setup_borrow_loot(bob, ledger, lootbox, teller, credit_engine, createDebtTerms)

    assert ledger.numUserVaults(bob) == 0
    claimable = lootbox.getClaimableBorrowLoot(bob)
    assert claimable > 0

    user_points_before = ledger.userBorrowPoints(bob)
    global_points_before = ledger.globalBorrowPoints()
    rewards_before = ledger.ripeRewards()
    avail_before = ledger.ripeAvailForRewards()
    supply_before = ripe_token.totalSupply()
    balance_before = ripe_token.balanceOf(bob)

    # the repaired zero-vault delivery path resolves the pointer only at mint
    # time, so an unset pointer must revert the entire claim atomically
    core_id = mission_control.coreRipeGovVaultId()
    assert core_id != 0
    mission_control.eval("self.coreRipeGovVaultId = 0")
    with boa.reverts(dev="invalid vault id"):
        lootbox.claimLootForUser(bob, bob, False, sender=teller.address)

    # borrow points, reward buckets, available rewards, supply, and balance
    # are all unchanged after the reverted delivery
    assert ledger.userBorrowPoints(bob) == user_points_before
    assert ledger.globalBorrowPoints() == global_points_before
    assert ledger.ripeRewards() == rewards_before
    assert ledger.ripeAvailForRewards() == avail_before
    assert ripe_token.totalSupply() == supply_before
    assert ripe_token.balanceOf(bob) == balance_before
    assert lootbox.getClaimableBorrowLoot(bob) == claimable

    # restoring the pointer lets the same claim deliver exactly once
    mission_control.eval(f"self.coreRipeGovVaultId = {core_id}")
    total_ripe = lootbox.claimLootForUser(bob, bob, False, sender=teller.address)
    assert total_ripe == claimable
    assert ripe_token.balanceOf(bob) == balance_before + total_ripe
    assert ledger.userBorrowPoints(bob).points == 0
    assert lootbox.claimLootForUser(bob, bob, False, sender=teller.address) == 0
