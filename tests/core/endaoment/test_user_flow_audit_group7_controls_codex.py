import boa
import pytest

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS
from conf_utils import filter_logs
from tests.core.endaoment.g7_psm_helpers import after_psm_tx


ONE_GREEN = EIGHTEEN_DECIMALS
ONE_USDC = 10**6


BROKEN_UNDERSCORE_REGISTRY_SOURCE = """
# @version 0.4.3

# Passes Group 9's Delta empty-address sentinel, then reverts on a real
# isEarnVault walk. Typed PSM walks then revert mint and redeem.

@view
@external
def getAddr(_id: uint256) -> address:
    return self

@view
@external
def isUserWallet(_addr: address) -> bool:
    return False

@view
@external
def isValidAddr(_addr: address) -> bool:
    return False

@view
@external
def isEarnVault(_addr: address) -> bool:
    if _addr == empty(address):
        return False
    raise "broken vault registry"
"""


YIELD_REGISTRY_SOURCE = """
# @version 0.4.3

addresses: HashMap[uint256, address]
earn_vault: HashMap[address, bool]

@external
def setAddr(_id: uint256, _addr: address):
    self.addresses[_id] = _addr

@external
def setEarnVault(_addr: address, _is_earn_vault: bool):
    self.earn_vault[_addr] = _is_earn_vault

@view
@external
def getAddr(_id: uint256) -> address:
    return self.addresses[_id]

@view
@external
def isUserWallet(_addr: address) -> bool:
    return False

@view
@external
def isEarnVault(_addr: address) -> bool:
    return self.earn_vault[_addr]
"""


YIELD_LEGO_SOURCE = """
# @version 0.4.3

interface IERC20:
    def balanceOf(_owner: address) -> uint256: view
    def transfer(_to: address, _amount: uint256) -> bool: nonpayable
    def transferFrom(_from: address, _to: address, _amount: uint256) -> bool: nonpayable

interface MintableToken:
    def mint(_to: address, _amount: uint256): nonpayable
    def burn(_amount: uint256) -> bool: nonpayable

struct MiniAddys:
    ledger: address
    missionControl: address
    legoBook: address
    appraiser: address

USDC: immutable(address)
VAULT_TOKEN: immutable(address)
deposit_receipt_token: public(address)
withdraw_bps: public(uint256)
should_revert_deposit: public(bool)

@deploy
def __init__(_usdc: address, _vault_token: address):
    USDC = _usdc
    VAULT_TOKEN = _vault_token
    self.deposit_receipt_token = _vault_token
    self.withdraw_bps = 10_000

@external
def setWithdrawBps(_bps: uint256):
    assert _bps <= 10_000
    self.withdraw_bps = _bps

@external
def setShouldRevertDeposit(_should_revert: bool):
    self.should_revert_deposit = _should_revert

@external
def setDepositReceiptToken(_receipt_token: address):
    self.deposit_receipt_token = _receipt_token

@external
def depositForYield(
    _asset: address,
    _amount: uint256,
    _vault_addr: address,
    _extra_data: bytes32,
    _recipient: address,
    _mini_addys: MiniAddys = empty(MiniAddys),
) -> (uint256, address, uint256, uint256):
    assert not self.should_revert_deposit, "yield deposit failed"
    assert _asset == USDC
    assert _vault_addr == VAULT_TOKEN
    assert extcall IERC20(USDC).transferFrom(msg.sender, self, _amount, default_return_value=True)
    receipt_token: address = self.deposit_receipt_token
    extcall MintableToken(receipt_token).mint(_recipient, _amount)
    return _amount, receipt_token, _amount, _amount * 10 ** 12

@external
def withdrawFromYield(
    _vault_token: address,
    _amount: uint256,
    _extra_data: bytes32,
    _recipient: address,
    _mini_addys: MiniAddys = empty(MiniAddys),
) -> (uint256, address, uint256, uint256):
    assert _vault_token == VAULT_TOKEN
    assert extcall IERC20(VAULT_TOKEN).transferFrom(msg.sender, self, _amount, default_return_value=True)
    assert extcall MintableToken(VAULT_TOKEN).burn(_amount)
    underlying_amount: uint256 = _amount * self.withdraw_bps // 10_000
    assert extcall IERC20(USDC).transfer(_recipient, underlying_amount, default_return_value=True)
    return _amount, USDC, underlying_amount, underlying_amount * 10 ** 12

@view
@external
def getUnderlyingAmountSafe(_vault_token: address, _vault_token_balance: uint256) -> uint256:
    assert _vault_token == VAULT_TOKEN
    return _vault_token_balance

@view
@external
def getVaultTokenAmount(_asset: address, _asset_amount: uint256, _vault_token: address) -> uint256:
    assert _asset == USDC
    assert _vault_token == VAULT_TOKEN
    return _asset_amount
"""


def _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, token, price=ONE_GREEN):
    mock_price_source.setPrice(token.address, price)
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)


def _enable_redeem(endaoment_psm, switchboard_charlie, mock_price_source, token, price=ONE_GREEN):
    mock_price_source.setPrice(token.address, price)
    endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)


def _execute_echo(switchboard_echo, action_id, governance):
    boa.env.time_travel(blocks=switchboard_echo.actionTimeLock())
    assert switchboard_echo.executePendingAction(action_id, sender=governance.address)


def _execute_delta(switchboard_delta, action_id, governance):
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    assert switchboard_delta.executePendingAction(action_id, sender=governance.address)


def _deploy_yield_stack(mission_control, switchboard_alpha, governance, charlie_token):
    registry = boa.loads(YIELD_REGISTRY_SOURCE, name="g7_yield_registry")
    vault_token = boa.load(
        "contracts/mock/MockErc20.vy",
        governance,
        "G7 Yield Receipt",
        "G7YR",
        6,
        0,
        name="g7_yield_receipt",
    )
    lego = boa.loads(
        YIELD_LEGO_SOURCE,
        charlie_token.address,
        vault_token.address,
        name="g7_yield_lego",
    )
    assert vault_token.setMinter(lego.address, True, sender=governance.address)
    registry.setAddr(1, registry.address)
    registry.setAddr(3, registry.address)
    registry.setAddr(10, registry.address)
    registry.setAddr(42, lego.address)
    mission_control.setUnderscoreRegistry(registry.address, sender=switchboard_alpha.address)
    return registry, vault_token, lego


def test_g7_specific_earn_vault_recipient_bypasses_fee_allowlist_and_global_mint_interval(
    endaoment_psm,
    charlie_token,
    green_token,
    switchboard_charlie,
    switchboard_alpha,
    governance,
    mission_control,
    mock_undy_v2,
    mock_price_source,
):
    payer = boa.env.generate_address()
    vault = boa.env.generate_address()
    amount = 125_000 * ONE_USDC

    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_undy_v2.setAllAddressesAreVaults(False)
    mock_undy_v2.setEarnVault(vault, True)
    _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
    endaoment_psm.setMintFee(10_000, sender=switchboard_charlie.address)
    endaoment_psm.setShouldEnforceMintAllowlist(True, sender=switchboard_charlie.address)

    charlie_token.mint(payer, 2 * amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 2 * amount, sender=payer)

    assert endaoment_psm.getMaxUsdcAmountForMint(payer, True) == 2 * amount
    first = endaoment_psm.mintGreen(amount, vault, False, sender=payer)
    after_psm_tx()
    second = endaoment_psm.mintGreen(amount, vault, False, sender=payer)

    assert first == second == amount * ONE_GREEN // ONE_USDC
    assert green_token.balanceOf(vault) == first + second
    assert charlie_token.balanceOf(payer) == 0
    assert endaoment_psm.globalMintInterval().start == 0
    assert endaoment_psm.globalMintInterval().amount == 0

    mock_undy_v2.setEarnVault(vault, False)
    mock_undy_v2.setAllAddressesAreVaults(True)


def test_g7_controlled_mock_earn_vault_beneficiary_can_recover_favorable_redeem_usdc(
    endaoment_psm,
    charlie_token,
    charlie_token_vault,
    green_token,
    switchboard_charlie,
    switchboard_alpha,
    governance,
    mission_control,
    mock_undy_v2,
    mock_price_source,
    whale,
):
    user = boa.env.generate_address()
    vault = charlie_token_vault.address
    seed = 10 * ONE_USDC
    green_amount = 1_000 * ONE_GREEN
    favorable = 1_052_631_578

    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    mock_undy_v2.setAllAddressesAreVaults(False)
    mock_undy_v2.setEarnVault(vault, True)
    _enable_redeem(
        endaoment_psm,
        switchboard_charlie,
        mock_price_source,
        charlie_token,
        95 * ONE_GREEN // 100,
    )
    endaoment_psm.setRedeemFee(10_000, sender=switchboard_charlie.address)
    charlie_token.mint(user, seed, sender=governance.address)
    charlie_token.approve(vault, seed, sender=user)
    shares = charlie_token_vault.deposit(seed, user, sender=user)
    green_token.transfer(user, green_amount, sender=whale)
    green_token.approve(endaoment_psm.address, green_amount, sender=user)
    charlie_token.mint(endaoment_psm.address, 1_100 * ONE_USDC, sender=governance.address)

    paid_to_vault = endaoment_psm.redeemGreen(green_amount, vault, False, sender=user)
    recovered = charlie_token_vault.redeem(shares, user, user, sender=user)

    assert paid_to_vault == favorable
    assert recovered == seed + favorable
    assert charlie_token.balanceOf(user) == seed + favorable

    mock_undy_v2.setEarnVault(vault, False)
    mock_undy_v2.setAllAddressesAreVaults(True)


def test_g7_echo_lite_can_only_queue_disable_governor_executes_or_cancels_it(
    endaoment_psm,
    mission_control,
    switchboard_charlie,
    switchboard_echo,
    governance,
    sally,
):
    endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    mission_control.setCanPerformLiteAction(sally, True, sender=switchboard_echo.address)

    disable_action = switchboard_echo.setPsmCanMint(False, sender=sally)
    assert endaoment_psm.canMint()
    with boa.reverts("no perms"):
        switchboard_echo.setPsmCanMint(True, sender=sally)
    with boa.reverts("no perms"):
        switchboard_echo.executePendingAction(disable_action, sender=sally)

    _execute_echo(switchboard_echo, disable_action, governance)
    assert not endaoment_psm.canMint()

    cancelled_enable = switchboard_echo.setPsmCanMint(True, sender=governance.address)
    assert not endaoment_psm.canMint()
    assert switchboard_echo.cancelPendingAction(cancelled_enable, sender=governance.address)
    assert not endaoment_psm.canMint()

    enable_action = switchboard_echo.setPsmCanMint(True, sender=governance.address)
    _execute_echo(switchboard_echo, enable_action, governance)
    assert endaoment_psm.canMint()


def test_g7_echo_can_timelock_a_nonzero_lego_with_empty_receipt_and_leave_yield_inert(
    endaoment_psm,
    charlie_token,
    switchboard_charlie,
    switchboard_echo,
    governance,
    mock_price_source,
):
    with boa.env.anchor():
        with boa.reverts("invalid lego id"):
            switchboard_echo.setPsmUsdcYieldPosition(0, ZERO_ADDRESS, sender=governance.address)

        action = switchboard_echo.setPsmUsdcYieldPosition(42, ZERO_ADDRESS, sender=governance.address)
        _execute_echo(switchboard_echo, action, governance)
        position = endaoment_psm.usdcYieldPosition()
        assert position.legoId == 42
        assert position.vaultToken == ZERO_ADDRESS

        user = boa.env.generate_address()
        _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
        charlie_token.mint(user, ONE_USDC, sender=governance.address)
        charlie_token.approve(endaoment_psm.address, ONE_USDC, sender=user)
        assert endaoment_psm.mintGreen(ONE_USDC, user, False, sender=user) == ONE_GREEN
        assert charlie_token.balanceOf(endaoment_psm.address) == ONE_USDC
        assert endaoment_psm.getUnderlyingYieldAmount() == 0


def test_g7_delta_install_and_clear_registry_are_real_timelocked_production_writes(
    mission_control,
    switchboard_delta,
    governance,
    mock_undy_v2,
):
    assert mission_control.underscoreRegistry() == ZERO_ADDRESS
    install = switchboard_delta.setUnderscoreRegistry(mock_undy_v2.address, sender=governance.address)
    assert mission_control.underscoreRegistry() == ZERO_ADDRESS
    _execute_delta(switchboard_delta, install, governance)
    assert mission_control.underscoreRegistry() == mock_undy_v2.address

    clear = switchboard_delta.setUnderscoreRegistry(ZERO_ADDRESS, sender=governance.address)
    _execute_delta(switchboard_delta, clear, governance)
    assert mission_control.underscoreRegistry() == ZERO_ADDRESS


def test_g7_delta_accepts_registry_that_bricks_all_psm_user_actions_until_clear(
    endaoment_psm,
    charlie_token,
    green_token,
    switchboard_charlie,
    switchboard_delta,
    governance,
    mission_control,
    mock_price_source,
    whale,
):
    """Group 9 lets Delta install a registry that is honest at the empty-address
    sentinel and reverts on a real vault walk. Typed PSM walks then revert
    until the registry is cleared.
    """
    broken = boa.loads(BROKEN_UNDERSCORE_REGISTRY_SOURCE, name="g7_broken_underscore_registry")
    install = switchboard_delta.setUnderscoreRegistry(broken.address, sender=governance.address)
    _execute_delta(switchboard_delta, install, governance)
    assert mission_control.underscoreRegistry() == broken.address

    user = boa.env.generate_address()
    mint_payment = 10 * ONE_USDC
    green_amount = ONE_GREEN
    _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
    _enable_redeem(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
    charlie_token.mint(user, mint_payment, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, mint_payment, sender=user)
    green_token.transfer(user, green_amount, sender=whale)
    green_token.approve(endaoment_psm.address, green_amount, sender=user)
    charlie_token.mint(endaoment_psm.address, mint_payment, sender=governance.address)

    endaoment_psm.setMintFee(500, sender=switchboard_charlie.address)
    with boa.reverts():
        endaoment_psm.mintGreen(mint_payment, user, False, sender=user)
    after_psm_tx()
    with boa.reverts():
        endaoment_psm.redeemGreen(green_amount, user, False, sender=user)
    after_psm_tx()

    clear = switchboard_delta.setUnderscoreRegistry(ZERO_ADDRESS, sender=governance.address)
    _execute_delta(switchboard_delta, clear, governance)
    assert mission_control.underscoreRegistry() == ZERO_ADDRESS

    minted = endaoment_psm.mintGreen(mint_payment, user, False, sender=user)
    after_psm_tx()
    fee = mint_payment * 500 // 10_000
    assert minted == (mint_payment - fee) * ONE_GREEN // ONE_USDC
    assert endaoment_psm.redeemGreen(green_amount, user, False, sender=user) == ONE_USDC
    after_psm_tx()


def test_g7_immediate_governor_reserve_sweep_turns_visible_redeem_capacity_into_zero(
    endaoment_psm,
    charlie_token,
    green_token,
    switchboard_charlie,
    switchboard_echo,
    governance,
    mock_price_source,
    whale,
):
    user = boa.env.generate_address()
    inventory = 100 * ONE_USDC
    green_amount = 100 * ONE_GREEN
    _enable_redeem(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
    charlie_token.mint(endaoment_psm.address, inventory, sender=governance.address)
    green_token.transfer(user, green_amount, sender=whale)
    green_token.approve(endaoment_psm.address, green_amount, sender=user)
    assert endaoment_psm.getMaxRedeemableGreenAmount(user, False) == green_amount

    swept = switchboard_echo.transferUsdcToEndaomentFundsInPsm(inventory, sender=governance.address)
    assert swept == inventory
    assert endaoment_psm.getAvailableUsdc() == 0
    with boa.reverts("zero amount"):
        endaoment_psm.redeemGreen(green_amount, user, False, sender=user)


def test_g7_yield_position_custody_overpull_registry_clear_and_safe_rotation(
    endaoment_psm,
    charlie_token,
    green_token,
    switchboard_charlie,
    switchboard_alpha,
    governance,
    mission_control,
    mock_price_source,
):
    """Exercise the PSM's real yield calls against a minimal honest adapter."""
    with boa.env.anchor():
        registry, vault_token, lego = _deploy_yield_stack(
            mission_control, switchboard_alpha, governance, charlie_token
        )
        user = boa.env.generate_address()
        deposit = 200 * ONE_USDC
        redemption = 100 * ONE_USDC

        _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
        _enable_redeem(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
        endaoment_psm.setUsdcYieldPosition(42, vault_token.address, sender=switchboard_charlie.address)
        charlie_token.mint(user, deposit, sender=governance.address)
        charlie_token.approve(endaoment_psm.address, deposit, sender=user)

        assert endaoment_psm.mintGreen(deposit, user, False, sender=user) == 200 * ONE_GREEN
        after_psm_tx()
        assert charlie_token.balanceOf(endaoment_psm.address) == 0
        assert charlie_token.balanceOf(lego.address) == deposit
        assert vault_token.balanceOf(endaoment_psm.address) == deposit
        assert endaoment_psm.getUnderlyingYieldAmount() == deposit
        assert endaoment_psm.getAvailableUsdc() == deposit

        green_token.approve(endaoment_psm.address, redemption * ONE_GREEN // ONE_USDC, sender=user)
        assert endaoment_psm.redeemGreen(redemption * ONE_GREEN // ONE_USDC, user, False, sender=user) == redemption
        after_psm_tx()

        # The PSM deliberately requests 102% of the shortfall.  With a 1:1
        # adapter it realizes 102 USDC, pays 100, and keeps the 2-USDC buffer.
        assert vault_token.balanceOf(endaoment_psm.address) == 98 * ONE_USDC
        assert charlie_token.balanceOf(endaoment_psm.address) == 2 * ONE_USDC
        assert charlie_token.balanceOf(lego.address) == 98 * ONE_USDC
        assert endaoment_psm.getUnderlyingYieldAmount() == 98 * ONE_USDC
        assert endaoment_psm.getAvailableUsdc() == 100 * ONE_USDC

        # Clearing the root hides the receipt position from views but does not
        # move custody; reinstalling the same root makes it visible again.
        mission_control.setUnderscoreRegistry(ZERO_ADDRESS, sender=switchboard_alpha.address)
        assert endaoment_psm.getUnderlyingYieldAmount() == 0
        assert endaoment_psm.getAvailableUsdc() == 2 * ONE_USDC
        mission_control.setUnderscoreRegistry(registry.address, sender=switchboard_alpha.address)
        assert endaoment_psm.getAvailableUsdc() == 100 * ONE_USDC

        with boa.reverts("vault token balance not zero"):
            endaoment_psm.setUsdcYieldPosition(0, ZERO_ADDRESS, sender=switchboard_charlie.address)

        withdrawn, transferred = endaoment_psm.withdrawFromYield(
            2**256 - 1,
            False,
            False,
            sender=switchboard_charlie.address,
        )
        assert withdrawn == 98 * ONE_USDC
        assert transferred == 0
        assert vault_token.balanceOf(endaoment_psm.address) == 0
        endaoment_psm.setUsdcYieldPosition(0, ZERO_ADDRESS, sender=switchboard_charlie.address)


def test_g7_partial_yield_pairs_are_inert_until_both_lego_and_vault_token_are_set(
    endaoment_psm,
    charlie_token,
    switchboard_charlie,
    switchboard_alpha,
    governance,
    mission_control,
    mock_price_source,
):
    with boa.env.anchor():
        _, vault_token, _ = _deploy_yield_stack(
            mission_control, switchboard_alpha, governance, charlie_token
        )
        user = boa.env.generate_address()
        payment = 10 * ONE_USDC
        _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
        charlie_token.mint(user, 3 * payment, sender=governance.address)
        charlie_token.approve(endaoment_psm.address, 3 * payment, sender=user)

        endaoment_psm.setUsdcYieldPosition(42, ZERO_ADDRESS, sender=switchboard_charlie.address)
        assert endaoment_psm.mintGreen(payment, user, False, sender=user) == 10 * ONE_GREEN
        after_psm_tx()
        assert charlie_token.balanceOf(endaoment_psm.address) == payment
        assert endaoment_psm.getUnderlyingYieldAmount() == 0

        endaoment_psm.setUsdcYieldPosition(0, vault_token.address, sender=switchboard_charlie.address)
        assert endaoment_psm.mintGreen(payment, user, False, sender=user) == 10 * ONE_GREEN
        after_psm_tx()
        assert charlie_token.balanceOf(endaoment_psm.address) == 2 * payment
        assert endaoment_psm.getUnderlyingYieldAmount() == 0

        endaoment_psm.setUsdcYieldPosition(42, vault_token.address, sender=switchboard_charlie.address)
        assert endaoment_psm.mintGreen(payment, user, False, sender=user) == 10 * ONE_GREEN
        assert charlie_token.balanceOf(endaoment_psm.address) == 0
        assert vault_token.balanceOf(endaoment_psm.address) == 3 * payment
        assert endaoment_psm.getUnderlyingYieldAmount() == 3 * payment


def test_g7_wrong_yield_receipt_token_leaves_green_minted_but_the_configured_position_empty(
    endaoment_psm,
    charlie_token,
    green_token,
    switchboard_charlie,
    switchboard_alpha,
    governance,
    mission_control,
    mock_price_source,
):
    """A hostile/misconfigured Lego is an integration failure, not pinned Underscore proof."""
    with boa.env.anchor():
        _, expected_receipt, lego = _deploy_yield_stack(
            mission_control, switchboard_alpha, governance, charlie_token
        )
        wrong_receipt = boa.load(
            "contracts/mock/MockErc20.vy",
            governance,
            "G7 Wrong Receipt",
            "G7WR",
            6,
            0,
            name="g7_wrong_yield_receipt",
        )
        assert wrong_receipt.setMinter(lego.address, True, sender=governance.address)
        lego.setDepositReceiptToken(wrong_receipt.address)
        user = boa.env.generate_address()
        payment = 100 * ONE_USDC
        _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
        _enable_redeem(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
        endaoment_psm.setUsdcYieldPosition(42, expected_receipt.address, sender=switchboard_charlie.address)
        charlie_token.mint(user, payment, sender=governance.address)
        charlie_token.approve(endaoment_psm.address, payment, sender=user)

        assert endaoment_psm.mintGreen(payment, user, False, sender=user) == 100 * ONE_GREEN
        after_psm_tx()
        assert green_token.balanceOf(user) == 100 * ONE_GREEN
        assert charlie_token.balanceOf(endaoment_psm.address) == 0
        assert charlie_token.balanceOf(lego.address) == payment
        assert expected_receipt.balanceOf(endaoment_psm.address) == 0
        assert wrong_receipt.balanceOf(endaoment_psm.address) == payment
        assert endaoment_psm.getUnderlyingYieldAmount() == 0
        assert endaoment_psm.getAvailableUsdc() == 0

        green_token.approve(endaoment_psm.address, 100 * ONE_GREEN, sender=user)
        with boa.reverts("zero amount"):
            endaoment_psm.redeemGreen(100 * ONE_GREEN, user, False, sender=user)


def test_g7_yield_deposit_and_underrealized_withdraw_fail_atomically_after_user_input(
    endaoment_psm,
    charlie_token,
    green_token,
    switchboard_charlie,
    switchboard_alpha,
    governance,
    mission_control,
    mock_price_source,
):
    with boa.env.anchor():
        _, vault_token, lego = _deploy_yield_stack(
            mission_control, switchboard_alpha, governance, charlie_token
        )
        user = boa.env.generate_address()
        payment = 100 * ONE_USDC
        _enable_mint(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
        _enable_redeem(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
        endaoment_psm.setUsdcYieldPosition(42, vault_token.address, sender=switchboard_charlie.address)
        charlie_token.mint(user, payment, sender=governance.address)
        charlie_token.approve(endaoment_psm.address, payment, sender=user)

        lego.setShouldRevertDeposit(True)
        pre_user = charlie_token.balanceOf(user)
        pre_supply = green_token.totalSupply()
        with boa.reverts():
            endaoment_psm.mintGreen(payment, user, False, sender=user)
        after_psm_tx()
        assert charlie_token.balanceOf(user) == pre_user
        assert green_token.totalSupply() == pre_supply
        assert charlie_token.allowance(endaoment_psm.address, lego.address) == 0

        lego.setShouldRevertDeposit(False)
        assert endaoment_psm.mintGreen(payment, user, False, sender=user) == 100 * ONE_GREEN
        after_psm_tx()
        assert endaoment_psm.depositToYield(sender=switchboard_charlie.address) == 0
        after_psm_tx()
        green_token.approve(endaoment_psm.address, 100 * ONE_GREEN, sender=user)
        lego.setWithdrawBps(9_000)
        before_underrealized_withdraw = (
            charlie_token.balanceOf(user),
            charlie_token.balanceOf(endaoment_psm.address),
            charlie_token.balanceOf(lego.address),
            green_token.balanceOf(user),
            green_token.totalSupply(),
            green_token.allowance(user, endaoment_psm.address),
            vault_token.balanceOf(endaoment_psm.address),
            endaoment_psm.globalRedeemInterval(),
        )
        with boa.reverts("insufficient USDC"):
            endaoment_psm.redeemGreen(100 * ONE_GREEN, user, False, sender=user)
        after_psm_tx()
        assert (
            charlie_token.balanceOf(user),
            charlie_token.balanceOf(endaoment_psm.address),
            charlie_token.balanceOf(lego.address),
            green_token.balanceOf(user),
            green_token.totalSupply(),
            green_token.allowance(user, endaoment_psm.address),
            vault_token.balanceOf(endaoment_psm.address),
            endaoment_psm.globalRedeemInterval(),
        ) == before_underrealized_withdraw


@pytest.mark.parametrize(
    "price,expected_green_burn",
    [
        (95 * ONE_GREEN // 100, 950 * ONE_GREEN),
        (ONE_GREEN, 1_000 * ONE_GREEN),
        (105 * ONE_GREEN // 100, 1_000 * ONE_GREEN),
    ],
)
def test_g7_vault_normal_price_cap_and_favorable_payout_do_not_exceed_available_usdc(
    endaoment_psm,
    charlie_token,
    green_token,
    switchboard_charlie,
    switchboard_alpha,
    governance,
    mission_control,
    mock_undy_v2,
    mock_price_source,
    whale,
    price,
    expected_green_burn,
):
    """Math-only vault recipient proof; the random vault has no beneficiary claim."""
    with boa.env.anchor():
        user = boa.env.generate_address()
        vault = boa.env.generate_address()
        inventory = 1_000 * ONE_USDC
        mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
        mock_undy_v2.setAllAddressesAreVaults(False)
        mock_undy_v2.setEarnVault(vault, True)
        _enable_redeem(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token, price)
        charlie_token.mint(endaoment_psm.address, inventory, sender=governance.address)
        green_token.transfer(user, 1_000 * ONE_GREEN, sender=whale)
        green_token.approve(endaoment_psm.address, 1_000 * ONE_GREEN, sender=user)

        assert endaoment_psm.getMaxRedeemableGreenAmount(ZERO_ADDRESS, True) == expected_green_burn
        supply_before = green_token.totalSupply()
        paid = endaoment_psm.redeemGreen(1_000 * ONE_GREEN, vault, False, sender=user)

        assert supply_before - green_token.totalSupply() == expected_green_burn
        assert paid == inventory
        assert paid <= inventory
        assert charlie_token.balanceOf(endaoment_psm.address) == 0

        mock_undy_v2.setEarnVault(vault, False)
        mock_undy_v2.setAllAddressesAreVaults(True)


def test_g7_forced_one_wei_price_can_make_vault_redeem_late_revert_but_normal_price_succeeds(
    endaoment_psm,
    charlie_token,
    green_token,
    switchboard_charlie,
    switchboard_alpha,
    governance,
    mission_control,
    mock_undy_v2,
    mock_price_source,
    whale,
):
    with boa.env.anchor():
        user = boa.env.generate_address()
        vault = boa.env.generate_address()
        mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
        mock_undy_v2.setAllAddressesAreVaults(False)
        mock_undy_v2.setEarnVault(vault, True)
        endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
        charlie_token.mint(endaoment_psm.address, 1, sender=governance.address)
        green_token.transfer(user, 1, sender=whale)
        green_token.approve(endaoment_psm.address, 1, sender=user)

        mock_price_source.setPrice(charlie_token.address, 1)
        assert endaoment_psm.getMaxRedeemableGreenAmount(user, False) == 0
        regular_before = (
            charlie_token.balanceOf(endaoment_psm.address),
            charlie_token.balanceOf(user),
            green_token.balanceOf(user),
            green_token.totalSupply(),
            endaoment_psm.globalRedeemInterval(),
        )
        with boa.reverts("zero amount"):
            endaoment_psm.redeemGreen(1, user, False, sender=user)
        after_psm_tx()
        assert (
            charlie_token.balanceOf(endaoment_psm.address),
            charlie_token.balanceOf(user),
            green_token.balanceOf(user),
            green_token.totalSupply(),
            endaoment_psm.globalRedeemInterval(),
        ) == regular_before

        assert endaoment_psm.getMaxRedeemableGreenAmount(user, True) == 0
        before = (
            charlie_token.balanceOf(endaoment_psm.address),
            charlie_token.balanceOf(vault),
            green_token.balanceOf(user),
            green_token.totalSupply(),
            endaoment_psm.globalRedeemInterval(),
        )
        with boa.reverts("zero amount"):
            endaoment_psm.redeemGreen(1, vault, False, sender=user)
        after_psm_tx()
        assert (
            charlie_token.balanceOf(endaoment_psm.address),
            charlie_token.balanceOf(vault),
            green_token.balanceOf(user),
            green_token.totalSupply(),
            endaoment_psm.globalRedeemInterval(),
        ) == before

        mock_price_source.setPrice(charlie_token.address, ONE_GREEN)
        green_token.transfer(user, 10**12, sender=whale)
        green_token.approve(endaoment_psm.address, 10**12 + 1, sender=user)
        assert endaoment_psm.getMaxRedeemableGreenAmount(user, True) == 10**12
        assert endaoment_psm.redeemGreen(10**12, vault, False, sender=user) == 1

        mock_undy_v2.setEarnVault(vault, False)
        mock_undy_v2.setAllAddressesAreVaults(True)


def test_g7_dust_usd_capacity_is_zero_below_one_usdc_base_unit(
    endaoment_psm,
    charlie_token,
    green_token,
    switchboard_charlie,
    switchboard_alpha,
    governance,
    mission_control,
    mock_undy_v2,
    mock_price_source,
    whale,
):
    with boa.env.anchor():
        user = boa.env.generate_address()
        vault = boa.env.generate_address()
        mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
        mock_undy_v2.setAllAddressesAreVaults(False)
        mock_undy_v2.setEarnVault(vault, True)
        endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)
        charlie_token.mint(endaoment_psm.address, 1, sender=governance.address)
        green_token.transfer(user, 10**12, sender=whale)
        green_token.approve(endaoment_psm.address, 10**12, sender=user)

        mock_price_source.setPrice(charlie_token.address, ONE_GREEN - ONE_USDC)
        assert endaoment_psm.getMaxRedeemableGreenAmount(user, False) == 0
        assert endaoment_psm.getMaxRedeemableGreenAmount(user, True) == 0

        mock_price_source.setPrice(charlie_token.address, ONE_GREEN)
        assert endaoment_psm.getMaxRedeemableGreenAmount(user, False) == 10**12
        assert endaoment_psm.redeemGreen(10**12, user, False, sender=user) == 1
        after_psm_tx()

        charlie_token.mint(endaoment_psm.address, 1, sender=governance.address)
        mock_price_source.setPrice(charlie_token.address, 5 * 10**17)
        green_token.transfer(user, 10**12, sender=whale)
        green_token.approve(endaoment_psm.address, 10**12, sender=user)
        assert endaoment_psm.getMaxRedeemableGreenAmount(user, False) == 0
        assert endaoment_psm.getMaxRedeemableGreenAmount(user, True) == 0
        with boa.reverts("zero amount"):
            endaoment_psm.redeemGreen(10**12, user, False, sender=user)
        after_psm_tx()
        with boa.reverts("zero amount"):
            endaoment_psm.redeemGreen(10**12, vault, False, sender=user)
        after_psm_tx()

        mock_undy_v2.setEarnVault(vault, False)
        mock_undy_v2.setAllAddressesAreVaults(True)
