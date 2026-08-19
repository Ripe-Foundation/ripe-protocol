"""Group 7 (PSM) — never-skip #6: registry, yield position, reserve drain.

The PSM's yield leg has no coverage anywhere in the existing suite (no shipped
mock implements `UndyLego.depositForYield`).  This file compiles a minimal
combined Underscore hub (registry + LegoBook + Lego + VaultRegistry) in-process
so the composition can be exercised.  It proves *interface composition only* —
it is not pinned Underscore behaviour.

The vault token is `charlie_token_vault` (`MockErc4626Vault` over the same 6dp
`charlie_token`).
"""

import boa
import pytest

from boa.contracts.base_evm_contract import BoaError
from boa.util.abi import abi_encode
from eth_utils import keccak

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS, MAX_UINT256
from conf_utils import filter_logs
from tests.core.endaoment.g7_psm_helpers import after_psm_tx


SIX_DECIMALS = 10**6
ONE_USDC = 10**6
ONE_GREEN = 10**18
HUNDRED_PERCENT = 100_00


MOCK_HUB_SRC = """
# @version 0.4.3

from ethereum.ercs import IERC20

interface Vault4626:
    def deposit(_amount: uint256, _receiver: address) -> uint256: nonpayable
    def redeem(_shares: uint256, _receiver: address, _owner: address) -> uint256: nonpayable
    def convertToAssetsSafe(_shares: uint256) -> uint256: view
    def convertToShares(_amount: uint256) -> uint256: view

struct MiniAddys:
    ledger: address
    missionControl: address
    legoBook: address
    appraiser: address

# registry knobs
missingRegId: public(uint256)
revertOnGetAddr: public(bool)
malformedGetAddr: public(bool)
legoAddrOverride: public(address)

# vault-registry knobs
allAddressesAreVaults: public(bool)
earnVaults: public(HashMap[address, bool])
revertOnIsEarnVault: public(bool)

# lego knobs
depositShortfallBps: public(uint256)      # keep this share of the deposit for itself
withdrawShortfallBps: public(uint256)     # deliver this much less than requested
overstateDepositReturn: public(bool)      # lie about assetAmount in the return tuple
overstateWithdrawBps: public(uint256)     # lie about underlyingAmount in the return tuple
viewInflateBps: public(uint256)           # getUnderlyingAmountSafe overstates by this
wrongVaultTokenInReturn: public(address)
revertOnDeposit: public(bool)
revertOnUnderlyingView: public(bool)
revertOnWithdraw: public(bool)

@deploy
def __init__():
    self.missingRegId = max_value(uint256)
    self.allAddressesAreVaults = False

@view
@external
def getAddr(_regId: uint256) -> address:
    assert not self.revertOnGetAddr
    if self.malformedGetAddr:
        return 0x0000000000000000000000000000000000000001
    if _regId == self.missingRegId:
        return empty(address)
    if self.legoAddrOverride != empty(address) and _regId != 3 and _regId != 10:
        return self.legoAddrOverride
    return self

@view
@external
def isUserWallet(_addr: address) -> bool:
    return False

@view
@external
def isValidAddr(_addr: address) -> bool:
    return True

@view
@external
def isEarnVault(_addr: address) -> bool:
    assert not self.revertOnIsEarnVault
    if self.allAddressesAreVaults:
        return True
    return self.earnVaults[_addr]

@external
def setEarnVault(_addr: address, _isVault: bool):
    self.earnVaults[_addr] = _isVault

@external
def setMissingRegId(_id: uint256):
    self.missingRegId = _id

@external
def setRevertOnGetAddr(_v: bool):
    self.revertOnGetAddr = _v

@external
def setRevertOnIsEarnVault(_v: bool):
    self.revertOnIsEarnVault = _v

@external
def setMalformedGetAddr(_v: bool):
    self.malformedGetAddr = _v

@external
def setLegoAddrOverride(_addr: address):
    self.legoAddrOverride = _addr

@external
def setDepositShortfallBps(_bps: uint256):
    self.depositShortfallBps = _bps

@external
def setWithdrawShortfallBps(_bps: uint256):
    self.withdrawShortfallBps = _bps

@external
def setOverstateDepositReturn(_v: bool):
    self.overstateDepositReturn = _v

@external
def setOverstateWithdrawBps(_bps: uint256):
    self.overstateWithdrawBps = _bps

@external
def setViewInflateBps(_bps: uint256):
    self.viewInflateBps = _bps

@external
def setWrongVaultTokenInReturn(_addr: address):
    self.wrongVaultTokenInReturn = _addr

@external
def setRevertOnDeposit(_v: bool):
    self.revertOnDeposit = _v

@external
def setRevertOnUnderlyingView(_v: bool):
    self.revertOnUnderlyingView = _v

@external
def setRevertOnWithdraw(_v: bool):
    self.revertOnWithdraw = _v

# ---- lego surface

@external
def depositForYield(
    _asset: address,
    _amount: uint256,
    _vaultAddr: address,
    _extraData: bytes32,
    _recipient: address,
    _miniAddys: MiniAddys = empty(MiniAddys),
) -> (uint256, address, uint256, uint256):
    assert not self.revertOnDeposit
    assert extcall IERC20(_asset).transferFrom(msg.sender, self, _amount, default_return_value=True)
    keep: uint256 = _amount * self.depositShortfallBps // 100_00
    deposited: uint256 = _amount - keep
    assert extcall IERC20(_asset).approve(_vaultAddr, deposited, default_return_value=True)
    shares: uint256 = extcall Vault4626(_vaultAddr).deposit(deposited, _recipient)
    reported: uint256 = _amount if self.overstateDepositReturn else deposited
    vt: address = _vaultAddr
    if self.wrongVaultTokenInReturn != empty(address):
        vt = self.wrongVaultTokenInReturn
    return reported, vt, shares, deposited

@external
def withdrawFromYield(
    _vaultToken: address,
    _amount: uint256,
    _extraData: bytes32,
    _recipient: address,
    _miniAddys: MiniAddys = empty(MiniAddys),
) -> (uint256, address, uint256, uint256):
    assert not self.revertOnWithdraw
    assert extcall IERC20(_vaultToken).transferFrom(msg.sender, self, _amount, default_return_value=True)
    burn: uint256 = _amount - _amount * self.withdrawShortfallBps // 100_00
    got: uint256 = extcall Vault4626(_vaultToken).redeem(burn, _recipient, self)
    reported: uint256 = got + got * self.overstateWithdrawBps // 100_00
    return burn, empty(address), reported, got

@view
@external
def getUnderlyingAmountSafe(_vaultToken: address, _vaultTokenBalance: uint256) -> uint256:
    assert not self.revertOnUnderlyingView
    base: uint256 = staticcall Vault4626(_vaultToken).convertToAssetsSafe(_vaultTokenBalance)
    return base + base * self.viewInflateBps // 100_00

@view
@external
def getVaultTokenAmount(_asset: address, _assetAmount: uint256, _vaultToken: address) -> uint256:
    return staticcall Vault4626(_vaultToken).convertToShares(_assetAmount)
"""


@pytest.fixture(scope="module")
def undy_hub():
    return boa.loads(MOCK_HUB_SRC, name="g7_undy_hub")


@pytest.fixture
def wired(undy_hub, mission_control, switchboard_alpha, switchboard_charlie,
          endaoment_psm, charlie_token_vault, charlie_token, governance, mock_price_source):
    """Registry installed, lego id 1 -> hub, vault token -> charlie_token_vault."""
    mission_control.setUnderscoreRegistry(undy_hub.address, sender=switchboard_alpha.address)
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    # the 4626 mock rejects a tiny first deposit; seed it from an outsider first
    seeder = boa.env.generate_address()
    charlie_token.mint(seeder, 1_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(charlie_token_vault.address, MAX_UINT256, sender=seeder)
    charlie_token_vault.deposit(1_000 * SIX_DECIMALS, seeder, sender=seeder)
    endaoment_psm.setUsdcYieldPosition(1, charlie_token_vault.address, sender=switchboard_charlie.address)
    yield
    mission_control.setUnderscoreRegistry(ZERO_ADDRESS, sender=switchboard_alpha.address)


def _enable(psm, sb):
    if not psm.canMint():
        psm.setCanMint(True, sender=sb.address)
    if not psm.canRedeem():
        psm.setCanRedeem(True, sender=sb.address)


def _give_green(green_token, credit_engine, who, amount):
    green_token.mint(who, amount, sender=credit_engine.address)


# ---------------------------------------------------------------- launch state


def test_g7_launch_yield_position_is_empty_and_deposit_is_a_noop(
    endaoment_psm, charlie_token, green_token, switchboard_charlie, governance, mock_price_source
):
    psm = endaoment_psm
    assert psm.getUsdcYieldPositionVaultToken() == ZERO_ADDRESS
    assert psm.usdcYieldPosition() == (0, ZERO_ADDRESS)
    assert psm.getUnderlyingYieldAmount() == 0
    assert psm.shouldAutoDeposit() is True     # on, but with nothing to deposit into

    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    _enable(psm, switchboard_charlie)
    user = boa.env.generate_address()
    charlie_token.mint(user, 1_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(psm.address, MAX_UINT256, sender=user)
    psm.mintGreen(1_000 * SIX_DECIMALS, user, False, sender=user)

    # every paid USDC stayed idle
    assert charlie_token.balanceOf(psm.address) == 1_000 * SIX_DECIMALS
    assert psm.getAvailableUsdc() == 1_000 * SIX_DECIMALS
    assert psm.getUnderlyingYieldAmount() == 0


# ------------------------------------------------- 6a malformed registry


def test_g7_registry_that_reverts_bricks_every_psm_action(
    endaoment_psm, undy_hub, mission_control, switchboard_alpha, switchboard_charlie,
    charlie_token, green_token, governance, mock_price_source, credit_engine
):
    """A reverting registry walk reverts mint and redeem.

    Empty getAddr(10) is still regular: no vault-registry call is made.
    """
    psm = endaoment_psm
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    _enable(psm, switchboard_charlie)
    charlie_token.mint(psm.address, 10_000 * SIX_DECIMALS, sender=governance.address)

    user = boa.env.generate_address()
    charlie_token.mint(user, 5_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(psm.address, MAX_UINT256, sender=user)
    _give_green(green_token, credit_engine, user, 5_000 * EIGHTEEN_DECIMALS)
    green_token.approve(psm.address, MAX_UINT256, sender=user)

    mission_control.setUnderscoreRegistry(undy_hub.address, sender=switchboard_alpha.address)
    # adjacent positive control with a healthy registry
    assert psm.mintGreen(100 * SIX_DECIMALS, user, False, sender=user) > 0
    after_psm_tx()

    psm.setMintFee(500, sender=switchboard_charlie.address)
    undy_hub.setRevertOnGetAddr(True)
    with boa.reverts():
        psm.mintGreen(100 * SIX_DECIMALS, user, False, sender=user)
    after_psm_tx()
    with boa.reverts():
        psm.redeemGreen(100 * EIGHTEEN_DECIMALS, user, False, sender=user)
    after_psm_tx()
    undy_hub.setRevertOnGetAddr(False)

    undy_hub.setRevertOnIsEarnVault(True)
    with boa.reverts():
        psm.mintGreen(100 * SIX_DECIMALS, user, False, sender=user)
    after_psm_tx()
    with boa.reverts():
        psm.redeemGreen(100 * EIGHTEEN_DECIMALS, user, False, sender=user)
    after_psm_tx()
    undy_hub.setRevertOnIsEarnVault(False)
    psm.setMintFee(0, sender=switchboard_charlie.address)

    # absent id 10: vault registry is empty, so the walk stops before isEarnVault
    undy_hub.setMissingRegId(10)
    assert psm.mintGreen(100 * SIX_DECIMALS, user, False, sender=user) > 0
    after_psm_tx()
    undy_hub.setMissingRegId(MAX_UINT256)

    mission_control.setUnderscoreRegistry(ZERO_ADDRESS, sender=switchboard_alpha.address)


# ------------------------------------------------- yield composition


def test_g7_auto_deposit_moves_the_entire_idle_balance_not_just_this_payment(
    endaoment_psm, charlie_token, charlie_token_vault, green_token, switchboard_charlie,
    governance, mock_price_source, wired
):
    """Seed idle B, pay P: `_depositToYield` moves B + P while GREEN comes only from P."""
    psm = endaoment_psm
    _enable(psm, switchboard_charlie)

    B = 4_000 * SIX_DECIMALS
    charlie_token.mint(psm.address, B, sender=governance.address)
    assert psm.getUnderlyingYieldAmount() == 0

    P = 1_000 * SIX_DECIMALS
    user = boa.env.generate_address()
    charlie_token.mint(user, P, sender=governance.address)
    charlie_token.approve(psm.address, MAX_UINT256, sender=user)

    pre_supply = green_token.totalSupply()
    minted = psm.mintGreen(P, user, False, sender=user)

    assert minted == P * ONE_GREEN // ONE_USDC              # GREEN from P only
    assert green_token.totalSupply() - pre_supply == minted
    assert charlie_token.balanceOf(psm.address) == 0        # idle fully swept
    assert charlie_token_vault.balanceOf(psm.address) > 0
    assert psm.getUnderlyingYieldAmount() == B + P          # B + P now in yield
    assert psm.getAvailableUsdc() == B + P


def test_g7_redeem_pulls_from_yield_when_idle_is_short(
    endaoment_psm, charlie_token, charlie_token_vault, green_token, switchboard_charlie,
    governance, mock_price_source, credit_engine, wired
):
    psm = endaoment_psm
    _enable(psm, switchboard_charlie)

    charlie_token.mint(psm.address, 10_000 * SIX_DECIMALS, sender=governance.address)
    psm.depositToYield(sender=switchboard_charlie.address)
    after_psm_tx()
    assert charlie_token.balanceOf(psm.address) == 0
    assert psm.getUnderlyingYieldAmount() == 10_000 * SIX_DECIMALS

    user = boa.env.generate_address()
    _give_green(green_token, credit_engine, user, 3_000 * EIGHTEEN_DECIMALS)
    green_token.approve(psm.address, MAX_UINT256, sender=user)

    out = psm.redeemGreen(3_000 * EIGHTEEN_DECIMALS, user, False, sender=user)
    assert out == 3_000 * SIX_DECIMALS
    assert charlie_token.balanceOf(user) == out
    # the 102% over-pull leaves a surplus sitting idle
    surplus = charlie_token.balanceOf(psm.address)
    assert surplus > 0
    assert psm.getAvailableUsdc() == 10_000 * SIX_DECIMALS - out


def test_g7_over_pull_surplus_accumulates_across_redeems(
    endaoment_psm, charlie_token, charlie_token_vault, green_token, switchboard_charlie,
    governance, mock_price_source, credit_engine, wired
):
    """`_withdrawFromYield` asks for `amount * 102_00 // 10_000`; quantify the residue."""
    psm = endaoment_psm
    _enable(psm, switchboard_charlie)
    psm.setShouldAutoDeposit(False, sender=switchboard_charlie.address)

    charlie_token.mint(psm.address, 20_000 * SIX_DECIMALS, sender=governance.address)
    psm.depositToYield(sender=switchboard_charlie.address)
    after_psm_tx()

    user = boa.env.generate_address()
    _give_green(green_token, credit_engine, user, 20_000 * EIGHTEEN_DECIMALS)
    green_token.approve(psm.address, MAX_UINT256, sender=user)

    total_out = 0
    for _ in range(4):
        total_out += psm.redeemGreen(1_000 * EIGHTEEN_DECIMALS, user, False, sender=user)
        after_psm_tx()

    idle = charlie_token.balanceOf(psm.address)
    yielded = psm.getUnderlyingYieldAmount()
    assert total_out == 4_000 * SIX_DECIMALS
    assert idle + yielded == 20_000 * SIX_DECIMALS - total_out   # nothing lost
    # only the first redeem over-pulls; later ones are served from the surplus
    assert idle <= 1_000 * SIX_DECIMALS * 2 // 100 + 1

    psm.setShouldAutoDeposit(True, sender=switchboard_charlie.address)


def test_g7_yield_view_overstates_then_withdrawal_realises_less_late_revert(
    endaoment_psm, undy_hub, charlie_token, charlie_token_vault, green_token,
    switchboard_charlie, governance, mock_price_source, credit_engine, wired
):
    """The one path to a *late* `insufficient USDC`: view counted, realisation short."""
    psm = endaoment_psm
    _enable(psm, switchboard_charlie)
    psm.setShouldAutoDeposit(False, sender=switchboard_charlie.address)

    charlie_token.mint(psm.address, 10_000 * SIX_DECIMALS, sender=governance.address)
    psm.depositToYield(sender=switchboard_charlie.address)
    after_psm_tx()
    assert charlie_token.balanceOf(psm.address) == 0

    user = boa.env.generate_address()
    _give_green(green_token, credit_engine, user, 20_000 * EIGHTEEN_DECIMALS)
    green_token.approve(psm.address, MAX_UINT256, sender=user)

    # the capacity view now claims 50% more USDC than the vault can deliver
    undy_hub.setViewInflateBps(50_00)
    assert psm.getAvailableUsdc() == 15_000 * SIX_DECIMALS
    quote = psm.getMaxRedeemableGreenAmount(ZERO_ADDRESS, False)
    assert quote == 15_000 * SIX_DECIMALS * ONE_GREEN // ONE_USDC

    pre_supply = green_token.totalSupply()
    pre_green = green_token.balanceOf(user)
    with boa.reverts("insufficient USDC"):
        psm.redeemGreen(14_000 * EIGHTEEN_DECIMALS, user, False, sender=user)
    after_psm_tx()
    # full rollback: GREEN never left, nothing burned, vault position intact
    assert green_token.balanceOf(user) == pre_green
    assert green_token.totalSupply() == pre_supply
    assert charlie_token_vault.balanceOf(psm.address) > 0

    # adjacent positive control: a request inside the *real* inventory succeeds
    undy_hub.setViewInflateBps(0)
    assert psm.redeemGreen(9_000 * EIGHTEEN_DECIMALS, user, False, sender=user) == 9_000 * SIX_DECIMALS

    psm.setShouldAutoDeposit(True, sender=switchboard_charlie.address)


def test_g7_lego_partial_deposit_leaves_green_under_backed(
    endaoment_psm, undy_hub, charlie_token, charlie_token_vault, green_token,
    switchboard_charlie, governance, mock_price_source, wired
):
    """The PSM does not measure receipt; it trusts the Lego's return tuple.

    With a Lego that keeps 10% of the deposit, the mint still succeeds and GREEN
    is still minted 1:1, but redeemable inventory is 10% short. Integration /
    config-dependent: it needs a hostile or buggy Lego, not user input.
    """
    psm = endaoment_psm
    _enable(psm, switchboard_charlie)
    undy_hub.setDepositShortfallBps(10_00)

    user = boa.env.generate_address()
    charlie_token.mint(user, 1_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(psm.address, MAX_UINT256, sender=user)

    minted = psm.mintGreen(1_000 * SIX_DECIMALS, user, False, sender=user)
    log = filter_logs(psm, "EndaomentPSMYieldDeposit")[0]
    after_psm_tx()
    assert minted == 1_000 * EIGHTEEN_DECIMALS
    assert log.amount == 900 * SIX_DECIMALS
    assert psm.getAvailableUsdc() == 900 * SIX_DECIMALS

    undy_hub.setOverstateDepositReturn(True)
    charlie_token.mint(user, 1_000 * SIX_DECIMALS, sender=governance.address)
    psm.mintGreen(1_000 * SIX_DECIMALS, user, False, sender=user)
    log2 = filter_logs(psm, "EndaomentPSMYieldDeposit")[0]
    after_psm_tx()
    assert log2.amount == 1_000 * SIX_DECIMALS
    assert psm.getAvailableUsdc() == 1_800 * SIX_DECIMALS

    undy_hub.setDepositShortfallBps(0)
    undy_hub.setOverstateDepositReturn(False)


# ------------------------------------------------- 6b reserve drain


def test_g7_governor_sweep_between_quote_and_execute_shrinks_a_users_redeem(
    endaoment_psm, switchboard_echo, charlie_token, green_token, switchboard_charlie,
    governance, mock_price_source, credit_engine, mission_control, sally
):
    """`transferUsdcToEndaomentFundsInPsm` is an *immediate* governor-or-lite op.

    A user who observed non-zero capacity gets a silent partial fill, not a
    revert, because `_paymentAmount` is a ceiling.
    """
    psm = endaoment_psm
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    _enable(psm, switchboard_charlie)
    charlie_token.mint(psm.address, 10_000 * SIX_DECIMALS, sender=governance.address)

    user = boa.env.generate_address()
    _give_green(green_token, credit_engine, user, 10_000 * EIGHTEEN_DECIMALS)
    green_token.approve(psm.address, MAX_UINT256, sender=user)

    quoted = psm.getMaxRedeemableGreenAmount(user, False)
    assert quoted == 10_000 * EIGHTEEN_DECIMALS

    # launch lite-signers are empty; enable one to show both routes reach it
    mission_control.setCanPerformLiteAction(sally, True, sender=switchboard_echo.address)
    switchboard_echo.transferUsdcToEndaomentFundsInPsm(7_000 * SIX_DECIMALS, sender=sally)
    assert psm.getAvailableUsdc() == 3_000 * SIX_DECIMALS

    out = psm.redeemGreen(quoted, user, False, sender=user)
    after_psm_tx()
    assert out == 3_000 * SIX_DECIMALS                  # partial fill, no revert
    assert green_token.balanceOf(user) == 7_000 * EIGHTEEN_DECIMALS

    # once the reserve is gone the next call reverts before the GREEN pull
    with boa.reverts("zero amount"):
        psm.redeemGreen(MAX_UINT256, user, False, sender=user)


def test_g7_deposit_to_yield_is_composition_not_a_drain(
    endaoment_psm, switchboard_echo, charlie_token, green_token, switchboard_charlie,
    governance, mock_price_source, credit_engine, wired
):
    psm = endaoment_psm
    _enable(psm, switchboard_charlie)
    psm.setShouldAutoDeposit(False, sender=switchboard_charlie.address)
    charlie_token.mint(psm.address, 5_000 * SIX_DECIMALS, sender=governance.address)

    before = psm.getAvailableUsdc()
    switchboard_echo.depositToYieldInPsm(sender=governance.address)
    assert charlie_token.balanceOf(psm.address) == 0
    assert psm.getUnderlyingYieldAmount() == 5_000 * SIX_DECIMALS
    assert psm.getAvailableUsdc() == before          # idle+yield is conserved

    user = boa.env.generate_address()
    _give_green(green_token, credit_engine, user, 5_000 * EIGHTEEN_DECIMALS)
    green_token.approve(psm.address, MAX_UINT256, sender=user)
    assert psm.redeemGreen(5_000 * EIGHTEEN_DECIMALS, user, False, sender=user) == 5_000 * SIX_DECIMALS

    psm.setShouldAutoDeposit(True, sender=switchboard_charlie.address)


# ------------------------------------------------- 6c lifecycle


def test_g7_clearing_the_registry_strands_yield_inventory(
    endaoment_psm, undy_hub, mission_control, switchboard_alpha, switchboard_charlie,
    charlie_token, charlie_token_vault, green_token, governance, mock_price_source,
    credit_engine, wired
):
    """Registry cleared -> `_getLegoAddr` returns empty -> yield USDC is unreachable."""
    psm = endaoment_psm
    _enable(psm, switchboard_charlie)
    psm.setShouldAutoDeposit(False, sender=switchboard_charlie.address)

    charlie_token.mint(psm.address, 8_000 * SIX_DECIMALS, sender=governance.address)
    psm.depositToYield(sender=switchboard_charlie.address)
    after_psm_tx()
    assert psm.getAvailableUsdc() == 8_000 * SIX_DECIMALS
    vault_tokens = charlie_token_vault.balanceOf(psm.address)
    assert vault_tokens > 0

    mission_control.setUnderscoreRegistry(ZERO_ADDRESS, sender=switchboard_alpha.address)
    assert psm.getUnderlyingYieldAmount() == 0
    assert psm.getAvailableUsdc() == 0               # inventory collapsed to idle (0)
    assert charlie_token_vault.balanceOf(psm.address) == vault_tokens  # tokens still held

    user = boa.env.generate_address()
    _give_green(green_token, credit_engine, user, 5_000 * EIGHTEEN_DECIMALS)
    green_token.approve(psm.address, MAX_UINT256, sender=user)
    with boa.reverts("zero amount"):
        psm.redeemGreen(MAX_UINT256, user, False, sender=user)
    after_psm_tx()

    # rotation is barred while the old vault-token balance is non-zero
    with boa.reverts("vault token balance not zero"):
        psm.setUsdcYieldPosition(2, charlie_token_vault.address, sender=switchboard_charlie.address)

    # re-registering revives access with the accounting intact
    mission_control.setUnderscoreRegistry(undy_hub.address, sender=switchboard_alpha.address)
    assert psm.getAvailableUsdc() == 8_000 * SIX_DECIMALS
    assert psm.redeemGreen(5_000 * EIGHTEEN_DECIMALS, user, False, sender=user) == 5_000 * SIX_DECIMALS

    psm.setShouldAutoDeposit(True, sender=switchboard_charlie.address)


def test_g7_rotating_to_a_registry_where_the_lego_id_resolves_elsewhere(
    endaoment_psm, undy_hub, mission_control, switchboard_alpha, switchboard_charlie,
    charlie_token, charlie_token_vault, green_token, governance, mock_price_source,
    credit_engine, wired
):
    """Same lego id, different address: the PSM follows the registry, not the id."""
    psm = endaoment_psm
    _enable(psm, switchboard_charlie)
    psm.setShouldAutoDeposit(False, sender=switchboard_charlie.address)

    charlie_token.mint(psm.address, 6_000 * SIX_DECIMALS, sender=governance.address)
    psm.depositToYield(sender=switchboard_charlie.address)
    after_psm_tx()
    assert psm.getAvailableUsdc() == 6_000 * SIX_DECIMALS

    other = boa.loads(MOCK_HUB_SRC, name="g7_undy_hub_alt")
    undy_hub.setLegoAddrOverride(other.address)      # lego id 1 now points at `other`
    # `other` holds no approval history and no vault tokens, but the views still work
    assert psm.getUnderlyingYieldAmount() == 6_000 * SIX_DECIMALS

    user = boa.env.generate_address()
    _give_green(green_token, credit_engine, user, 6_000 * EIGHTEEN_DECIMALS)
    green_token.approve(psm.address, MAX_UINT256, sender=user)
    assert psm.redeemGreen(2_000 * EIGHTEEN_DECIMALS, user, False, sender=user) == 2_000 * SIX_DECIMALS

    undy_hub.setLegoAddrOverride(ZERO_ADDRESS)
    psm.setShouldAutoDeposit(True, sender=switchboard_charlie.address)


# ------------------------------------------------- 6d yield-position pairs


def test_g7_yield_position_all_four_pairs_at_the_psm(
    endaoment_psm, switchboard_charlie, charlie_token, charlie_token_vault, governance, wired
):
    psm = endaoment_psm
    # `wired` left us at (1, vault)
    assert psm.usdcYieldPosition() == (1, charlie_token_vault.address)

    # (nonzero, empty) -> yield off
    psm.setUsdcYieldPosition(1, ZERO_ADDRESS, sender=switchboard_charlie.address)
    assert psm.getUnderlyingYieldAmount() == 0
    charlie_token.mint(psm.address, 100 * SIX_DECIMALS, sender=governance.address)
    assert psm.depositToYield(sender=switchboard_charlie.address) == 0
    after_psm_tx()

    # (0, nonzero) -> also yield off
    psm.setUsdcYieldPosition(0, charlie_token_vault.address, sender=switchboard_charlie.address)
    assert psm.getUnderlyingYieldAmount() == 0
    assert psm.depositToYield(sender=switchboard_charlie.address) == 0
    after_psm_tx()

    # (0, empty) -> canonical off; reachable directly on the PSM
    psm.setUsdcYieldPosition(0, ZERO_ADDRESS, sender=switchboard_charlie.address)
    assert psm.usdcYieldPosition() == (0, ZERO_ADDRESS)

    # (nonzero, nonzero) -> on again
    psm.setUsdcYieldPosition(1, charlie_token_vault.address, sender=switchboard_charlie.address)
    assert psm.depositToYield(sender=switchboard_charlie.address) == 100 * SIX_DECIMALS


def test_g7_echo_can_reach_nonzero_empty_but_never_restores_canonical_off(
    endaoment_psm, switchboard_echo, switchboard_charlie, charlie_token_vault, governance, wired
):
    """`SwitchboardEcho.setPsmUsdcYieldPosition` rejects `legoId == 0`."""
    psm = endaoment_psm
    assert psm.usdcYieldPosition() == (1, charlie_token_vault.address)

    with boa.reverts():
        switchboard_echo.setPsmUsdcYieldPosition(0, ZERO_ADDRESS, sender=governance.address)
    with boa.reverts():
        switchboard_echo.setPsmUsdcYieldPosition(0, charlie_token_vault.address, sender=governance.address)

    # (nonzero, empty) IS reachable and functionally disables yield
    aid = switchboard_echo.setPsmUsdcYieldPosition(1, ZERO_ADDRESS, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_echo.actionTimeLock())
    assert switchboard_echo.executePendingAction(aid, sender=governance.address) is True
    assert psm.usdcYieldPosition() == (1, ZERO_ADDRESS)
    assert psm.getUnderlyingYieldAmount() == 0
    # ...but (0, empty) can only ever be restored by a non-Echo Switchboard write
    assert psm.usdcYieldPosition()[0] != 0


def test_g7_yield_rotation_needs_a_zero_old_vault_token_balance(
    endaoment_psm, switchboard_charlie, charlie_token, charlie_token_vault, governance, wired
):
    psm = endaoment_psm
    charlie_token.mint(psm.address, 1_000 * SIX_DECIMALS, sender=governance.address)
    psm.depositToYield(sender=switchboard_charlie.address)
    after_psm_tx()
    assert charlie_token_vault.balanceOf(psm.address) > 0

    with boa.reverts("vault token balance not zero"):
        psm.setUsdcYieldPosition(2, ZERO_ADDRESS, sender=switchboard_charlie.address)

    # drain to exactly zero, then rotation is allowed
    psm.withdrawFromYield(MAX_UINT256, False, False, sender=switchboard_charlie.address)
    assert charlie_token_vault.balanceOf(psm.address) == 0
    psm.setUsdcYieldPosition(2, ZERO_ADDRESS, sender=switchboard_charlie.address)
    assert psm.usdcYieldPosition() == (2, ZERO_ADDRESS)


def test_g7_overstated_withdrawal_return_reaches_the_usdc_transfer(
    endaoment_psm, undy_hub, charlie_token, charlie_token_vault, green_token,
    switchboard_charlie, governance, mock_price_source, credit_engine, wired
):
    """The PSM trusts the Lego's `underlyingAmount`; it never re-reads its own balance.

    `redeemGreen` sums `usdcBalance += self._withdrawFromYield(...)` and then
    asserts against that *reported* number.  A Lego that overstates its return
    walks straight past `insufficient USDC` and fails one line later in the USDC
    `transfer` — which is exactly the latest practical pre-burn blocker.
    Integration/config-dependent (needs a hostile or buggy Lego); the tx reverts
    in full, so it is a liveness failure, not an over-payout.
    """
    psm = endaoment_psm
    _enable(psm, switchboard_charlie)
    psm.setShouldAutoDeposit(False, sender=switchboard_charlie.address)

    charlie_token.mint(psm.address, 10_000 * SIX_DECIMALS, sender=governance.address)
    psm.depositToYield(sender=switchboard_charlie.address)
    after_psm_tx()
    assert charlie_token.balanceOf(psm.address) == 0

    user = boa.env.generate_address()
    _give_green(green_token, credit_engine, user, 20_000 * EIGHTEEN_DECIMALS)
    green_token.approve(psm.address, MAX_UINT256, sender=user)

    # the Lego delivers honestly but *reports* 30% more than it moved
    undy_hub.setWithdrawShortfallBps(30_00)
    undy_hub.setOverstateWithdrawBps(50_00)

    pre_supply = green_token.totalSupply()
    pre_green = green_token.balanceOf(user)
    pre_vault_tokens = charlie_token_vault.balanceOf(psm.address)
    with boa.reverts():
        psm.redeemGreen(9_000 * EIGHTEEN_DECIMALS, user, False, sender=user)
    after_psm_tx()
    # full rollback: no burn, no payout, position intact
    assert green_token.totalSupply() == pre_supply
    assert green_token.balanceOf(user) == pre_green
    assert charlie_token_vault.balanceOf(psm.address) == pre_vault_tokens
    assert charlie_token.balanceOf(user) == 0

    # an honest report of the same 30% shortfall stops one line earlier, at the
    # `insufficient USDC` assert, instead of blowing up inside the transfer
    undy_hub.setOverstateWithdrawBps(0)
    with boa.reverts("insufficient USDC"):
        psm.redeemGreen(9_000 * EIGHTEEN_DECIMALS, user, False, sender=user)
    after_psm_tx()
    assert green_token.totalSupply() == pre_supply

    # adjacent positive control: an honest, complete Lego serves the same request
    undy_hub.setWithdrawShortfallBps(0)
    out = psm.redeemGreen(5_000 * EIGHTEEN_DECIMALS, user, False, sender=user)
    assert out == 5_000 * SIX_DECIMALS

    psm.setShouldAutoDeposit(True, sender=switchboard_charlie.address)


def test_g7_a_failing_yield_venue_bricks_minting_entirely(
    endaoment_psm, undy_hub, charlie_token, green_token, switchboard_charlie,
    governance, mock_price_source, credit_engine, wired
):
    """A reverting `depositForYield` rolls back an otherwise-valid mint."""
    psm = endaoment_psm
    _enable(psm, switchboard_charlie)

    user = boa.env.generate_address()
    charlie_token.mint(user, 5_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(psm.address, MAX_UINT256, sender=user)

    assert psm.mintGreen(1_000 * SIX_DECIMALS, user, False, sender=user) > 0
    after_psm_tx()

    undy_hub.setRevertOnDeposit(True)
    pre_supply = green_token.totalSupply()
    pre_user = charlie_token.balanceOf(user)
    with boa.reverts():
        psm.mintGreen(1_000 * SIX_DECIMALS, user, False, sender=user)
    after_psm_tx()
    assert green_token.totalSupply() == pre_supply
    assert charlie_token.balanceOf(user) == pre_user

    undy_hub.setRevertOnDeposit(False)


def test_g7_a_reverting_underlying_view_bricks_redeeming_entirely(
    endaoment_psm, undy_hub, charlie_token, green_token, switchboard_charlie,
    governance, mock_price_source, credit_engine, wired
):
    """A reverting `getUnderlyingAmountSafe` bricks redeem and capacity views."""
    psm = endaoment_psm
    _enable(psm, switchboard_charlie)
    psm.setShouldAutoDeposit(False, sender=switchboard_charlie.address)

    charlie_token.mint(psm.address, 10_000 * SIX_DECIMALS, sender=governance.address)
    deposited = psm.depositToYield(sender=switchboard_charlie.address)
    after_psm_tx()
    assert deposited == 10_000 * SIX_DECIMALS
    assert psm.getAvailableUsdc() == 10_000 * SIX_DECIMALS
    charlie_token.mint(psm.address, 2_000 * SIX_DECIMALS, sender=governance.address)  # idle

    user = boa.env.generate_address()
    _give_green(green_token, credit_engine, user, 5_000 * EIGHTEEN_DECIMALS)
    green_token.approve(psm.address, MAX_UINT256, sender=user)
    assert psm.redeemGreen(500 * EIGHTEEN_DECIMALS, user, False, sender=user) > 0
    after_psm_tx()

    undy_hub.setRevertOnUnderlyingView(True)
    with pytest.raises(BoaError):
        assert psm.getAvailableUsdc() > 0
    with pytest.raises(BoaError):
        assert psm.getMaxRedeemableGreenAmount(user, False) > 0
    with boa.reverts():
        psm.redeemGreen(500 * EIGHTEEN_DECIMALS, user, False, sender=user)
    after_psm_tx()

    undy_hub.setRevertOnUnderlyingView(False)
    psm.setShouldAutoDeposit(True, sender=switchboard_charlie.address)


HIGH_ADDR_REG = """
# @version 0.4.3
@view
@external
def getAddr(_id: uint256) -> uint256:
    return 2 ** 160
"""

SHORT_ADDR_REG = """
# @version 0.4.3
@view
@external
@raw_return
def getAddr(_id: uint256) -> Bytes[16]:
    return slice(empty(bytes32), 0, 16)
"""

OVERSIZE_ADDR_REG = """
# @version 0.4.3
@view
@external
@raw_return
def getAddr(_id: uint256) -> Bytes[33]:
    return concat(empty(bytes32), b"x")
"""

NONCANONICAL_VAULT_REG = """
# @version 0.4.3
word: uint256
@deploy
def __init__(_word: uint256):
    self.word = _word
@view
@external
def getAddr(_id: uint256) -> address:
    return self
@view
@external
def isEarnVault(_addr: address) -> uint256:
    return self.word
"""

SHORT_VAULT_REG = """
# @version 0.4.3
@view
@external
def getAddr(_id: uint256) -> address:
    return self
@view
@external
@raw_return
def isEarnVault(_addr: address) -> Bytes[16]:
    return slice(empty(bytes32), 0, 16)
"""

OVERSIZE_VAULT_REG = """
# @version 0.4.3
@view
@external
def getAddr(_id: uint256) -> address:
    return self
@view
@external
@raw_return
def isEarnVault(_addr: address) -> Bytes[33]:
    return concat(empty(bytes32), b"x")
"""

CODELESS_ID10_REG = """
# @version 0.4.3
codeless: address
@deploy
def __init__(_codeless: address):
    self.codeless = _codeless
@view
@external
def getAddr(_id: uint256) -> address:
    if _id == 10:
        return self.codeless
    return self
@view
@external
def isEarnVault(_addr: address) -> bool:
    return True
"""

FIVE_ARG_LEGO = """
# @version 0.4.3
from ethereum.ercs import IERC20
interface Vault4626:
    def deposit(_amount: uint256, _receiver: address) -> uint256: nonpayable
@external
def depositForYield(_asset: address, _amount: uint256, _vaultAddr: address, _extraData: bytes32, _recipient: address) -> (uint256, address, uint256, uint256):
    assert extcall IERC20(_asset).transferFrom(msg.sender, self, _amount, default_return_value=True)
    assert extcall IERC20(_asset).approve(_vaultAddr, _amount, default_return_value=True)
    shares: uint256 = extcall Vault4626(_vaultAddr).deposit(_amount, _recipient)
    return _amount, _vaultAddr, shares, _amount
@view
@external
def getUnderlyingAmountSafe(_vaultToken: address, _vaultTokenBalance: uint256) -> uint256:
    return _vaultTokenBalance
"""

SHORT_LEGO = """
# @version 0.4.3
from ethereum.ercs import IERC20
take: bool
@deploy
def __init__(_take: bool):
    self.take = _take
@external
def depositForYield(_asset: address, _amount: uint256, _vaultAddr: address, _extraData: bytes32, _recipient: address) -> uint256:
    if self.take:
        assert extcall IERC20(_asset).transferFrom(msg.sender, self, _amount, default_return_value=True)
    return 1
"""

MALFORMED_LEGO = """
# @version 0.4.3
from ethereum.ercs import IERC20
take: bool
@deploy
def __init__(_take: bool):
    self.take = _take
@external
def depositForYield(_asset: address, _amount: uint256, _vaultAddr: address, _extraData: bytes32, _recipient: address) -> (uint256, uint256, uint256, uint256):
    if self.take:
        assert extcall IERC20(_asset).transferFrom(msg.sender, self, _amount, default_return_value=True)
    return 1, 2 ** 160, 1, 1
"""

OVERSIZE_LEGO = """
# @version 0.4.3
from ethereum.ercs import IERC20
take: bool
@deploy
def __init__(_take: bool):
    self.take = _take
@external
@raw_return
def depositForYield(_asset: address, _amount: uint256, _vaultAddr: address, _extraData: bytes32, _recipient: address) -> Bytes[129]:
    if self.take:
        assert extcall IERC20(_asset).transferFrom(msg.sender, self, _amount, default_return_value=True)
    return concat(empty(bytes32), empty(bytes32), empty(bytes32), empty(bytes32), b"x")
"""


def _method_id(sig):
    return keccak(text=sig)[:4]


def _returndata_len(to, data, *, modifying=False):
    ret = boa.env.execute_code(to_address=to, data=data, is_modifying=modifying)
    assert not ret.is_error, ret.error
    return len(ret.output)


def _getAddr_len(target, reg_id=10):
    return _returndata_len(
        target,
        _method_id("getAddr(uint256)") + abi_encode("uint256", reg_id),
        modifying=False,
    )


def _isEarnVault_len(target, addr):
    return _returndata_len(
        target,
        _method_id("isEarnVault(address)") + abi_encode("address", addr),
        modifying=False,
    )


def _depositForYield_len(target, asset, amount, vault, recipient):
    return _returndata_len(
        target,
        _method_id("depositForYield(address,uint256,address,bytes32,address)")
        + abi_encode(
            "(address,uint256,address,bytes32,address)",
            (asset, amount, vault, b"\x00" * 32, recipient),
        ),
        modifying=True,
    )


def _reverting_mint_on_registry(psm, mission_control, switchboard_alpha, switchboard_charlie, registry, user):
    mission_control.setUnderscoreRegistry(registry, sender=switchboard_alpha.address)
    psm.setMintFee(500, sender=switchboard_charlie.address)
    with boa.reverts():
        psm.mintGreen(100 * SIX_DECIMALS, user, False, sender=user)
    after_psm_tx()
    psm.setMintFee(0, sender=switchboard_charlie.address)
    mission_control.setUnderscoreRegistry(ZERO_ADDRESS, sender=switchboard_alpha.address)


def _regular_mint_on_registry(psm, mission_control, switchboard_alpha, switchboard_charlie, registry, user):
    mission_control.setUnderscoreRegistry(registry, sender=switchboard_alpha.address)
    psm.setMintFee(500, sender=switchboard_charlie.address)
    minted = psm.mintGreen(100 * SIX_DECIMALS, user, False, sender=user)
    after_psm_tx()
    assert minted == 95 * EIGHTEEN_DECIMALS
    psm.setMintFee(0, sender=switchboard_charlie.address)
    mission_control.setUnderscoreRegistry(ZERO_ADDRESS, sender=switchboard_alpha.address)


def _prep_regular_user(psm, switchboard_charlie, mock_price_source, charlie_token, governance):
    mock_price_source.setPrice(charlie_token.address, 1 * EIGHTEEN_DECIMALS)
    _enable(psm, switchboard_charlie)
    user = boa.env.generate_address()
    charlie_token.mint(user, 1_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(psm.address, MAX_UINT256, sender=user)
    return user


@pytest.mark.parametrize(
    "src,ctor_args,expected_len",
    [
        (HIGH_ADDR_REG, (), 32),
        (SHORT_ADDR_REG, (), 16),
    ],
    ids=["getAddr-high-word", "getAddr-short"],
)
def test_g7_malformed_getAddr_reverts_mint(
    endaoment_psm, mission_control, switchboard_alpha, switchboard_charlie,
    charlie_token, governance, mock_price_source, src, ctor_args, expected_len,
):
    psm = endaoment_psm
    user = _prep_regular_user(psm, switchboard_charlie, mock_price_source, charlie_token, governance)
    reg = boa.loads(src, *ctor_args, name="g7_getAddr_case")
    assert _getAddr_len(reg.address) == expected_len
    _reverting_mint_on_registry(
        psm, mission_control, switchboard_alpha, switchboard_charlie,
        reg.address, user,
    )


def test_g7_oversized_getAddr_decodes_prefix_and_is_regular(
    endaoment_psm, mission_control, switchboard_alpha, switchboard_charlie,
    charlie_token, governance, mock_price_source,
):
    """Typed ABI ignores extra bytes; 33-byte getAddr decodes as empty → regular."""
    psm = endaoment_psm
    user = _prep_regular_user(psm, switchboard_charlie, mock_price_source, charlie_token, governance)
    reg = boa.loads(OVERSIZE_ADDR_REG, name="g7_getAddr_oversized")
    assert _getAddr_len(reg.address) == 33
    _regular_mint_on_registry(
        psm, mission_control, switchboard_alpha, switchboard_charlie,
        reg.address, user,
    )


@pytest.mark.parametrize(
    "src,ctor_args,expected_len",
    [
        (NONCANONICAL_VAULT_REG, (2,), 32),
        (SHORT_VAULT_REG, (), 16),
    ],
    ids=["isEarnVault-noncanonical", "isEarnVault-short"],
)
def test_g7_malformed_isEarnVault_reverts_mint(
    endaoment_psm, mission_control, switchboard_alpha, switchboard_charlie,
    charlie_token, governance, mock_price_source, src, ctor_args, expected_len,
):
    psm = endaoment_psm
    user = _prep_regular_user(psm, switchboard_charlie, mock_price_source, charlie_token, governance)
    reg = boa.loads(src, *ctor_args, name="g7_isEarnVault_case")
    assert _isEarnVault_len(reg.address, user) == expected_len
    _reverting_mint_on_registry(
        psm, mission_control, switchboard_alpha, switchboard_charlie,
        reg.address, user,
    )


def test_g7_oversized_isEarnVault_decodes_prefix_and_is_regular(
    endaoment_psm, mission_control, switchboard_alpha, switchboard_charlie,
    charlie_token, governance, mock_price_source,
):
    """Typed ABI ignores extra bytes; 33-byte isEarnVault decodes as False → regular."""
    psm = endaoment_psm
    user = _prep_regular_user(psm, switchboard_charlie, mock_price_source, charlie_token, governance)
    reg = boa.loads(OVERSIZE_VAULT_REG, name="g7_isEarnVault_oversized")
    assert _isEarnVault_len(reg.address, user) == 33
    _regular_mint_on_registry(
        psm, mission_control, switchboard_alpha, switchboard_charlie,
        reg.address, user,
    )


def test_g7_codeless_id10_reverts_mint(
    endaoment_psm, mission_control, switchboard_alpha, switchboard_charlie,
    charlie_token, governance, mock_price_source,
):
    psm = endaoment_psm
    user = _prep_regular_user(psm, switchboard_charlie, mock_price_source, charlie_token, governance)
    empty_addr = boa.env.generate_address()
    reg = boa.loads(CODELESS_ID10_REG, empty_addr, name="g7_codeless_id10")
    assert _getAddr_len(reg.address) == 32
    assert _isEarnVault_len(empty_addr, user) == 0
    _reverting_mint_on_registry(
        psm, mission_control, switchboard_alpha, switchboard_charlie,
        reg.address, user,
    )


def test_g7_yield_configured_reverting_registry_reverts_user_paths(
    endaoment_psm, undy_hub, charlie_token, green_token, switchboard_charlie,
    governance, mock_price_source, credit_engine, wired,
):
    psm = endaoment_psm
    _enable(psm, switchboard_charlie)
    undy_hub.setRevertOnGetAddr(True)
    user = boa.env.generate_address()
    charlie_token.mint(user, 1_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(psm.address, MAX_UINT256, sender=user)
    pre_user = charlie_token.balanceOf(user)
    with boa.reverts():
        psm.mintGreen(1_000 * SIX_DECIMALS, user, False, sender=user)
    after_psm_tx()
    assert charlie_token.balanceOf(user) == pre_user
    _give_green(green_token, credit_engine, user, 1_000 * EIGHTEEN_DECIMALS)
    green_token.approve(psm.address, MAX_UINT256, sender=user)
    with boa.reverts():
        psm.redeemGreen(1_000 * EIGHTEEN_DECIMALS, user, False, sender=user)
    after_psm_tx()
    undy_hub.setRevertOnGetAddr(False)


def test_g7_honest_yield_deposit_returns_lego_asset_amount(
    endaoment_psm, undy_hub, charlie_token, charlie_token_vault, switchboard_charlie,
    governance, mock_price_source, wired,
):
    psm = endaoment_psm
    _enable(psm, switchboard_charlie)
    psm.setShouldAutoDeposit(False, sender=switchboard_charlie.address)
    charlie_token.mint(psm.address, 1_000 * SIX_DECIMALS, sender=governance.address)
    returned = psm.depositToYield(sender=switchboard_charlie.address)
    ev = filter_logs(psm, "EndaomentPSMYieldDeposit")[0]
    after_psm_tx()
    assert returned == 1_000 * SIX_DECIMALS
    assert ev.amount == 1_000 * SIX_DECIMALS
    assert charlie_token.balanceOf(psm.address) == 0
    assert charlie_token.allowance(psm.address, undy_hub.address) == 0
    assert charlie_token_vault.balanceOf(psm.address) > 0
    psm.setShouldAutoDeposit(True, sender=switchboard_charlie.address)


def test_g7_deposit_to_yield_return_is_lego_asset_amount(
    endaoment_psm, undy_hub, charlie_token, switchboard_charlie,
    governance, mock_price_source, wired,
):
    psm = endaoment_psm
    _enable(psm, switchboard_charlie)
    psm.setShouldAutoDeposit(False, sender=switchboard_charlie.address)
    undy_hub.setDepositShortfallBps(10_00)
    charlie_token.mint(psm.address, 1_000 * SIX_DECIMALS, sender=governance.address)
    returned = psm.depositToYield(sender=switchboard_charlie.address)
    ev = filter_logs(psm, "EndaomentPSMYieldDeposit")[0]
    assert returned == 900 * SIX_DECIMALS
    assert ev.amount == 900 * SIX_DECIMALS
    assert psm.getAvailableUsdc() == 900 * SIX_DECIMALS
    undy_hub.setDepositShortfallBps(0)
    psm.setShouldAutoDeposit(True, sender=switchboard_charlie.address)


def test_g7_five_arg_only_lego_still_deposits(
    endaoment_psm, undy_hub, charlie_token, charlie_token_vault, green_token,
    switchboard_charlie, governance, mock_price_source, wired,
):
    psm = endaoment_psm
    _enable(psm, switchboard_charlie)
    five = boa.loads(FIVE_ARG_LEGO, name="g7_five_arg_lego")
    undy_hub.setLegoAddrOverride(five.address)
    user = boa.env.generate_address()
    charlie_token.mint(user, 1_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(psm.address, MAX_UINT256, sender=user)
    assert psm.mintGreen(1_000 * SIX_DECIMALS, user, False, sender=user) == 1_000 * EIGHTEEN_DECIMALS
    assert charlie_token.balanceOf(psm.address) == 0
    assert charlie_token_vault.balanceOf(psm.address) > 0
    ev = filter_logs(psm, "EndaomentPSMYieldDeposit")[0]
    assert ev.amount == 1_000 * SIX_DECIMALS
    undy_hub.setLegoAddrOverride(ZERO_ADDRESS)


@pytest.mark.parametrize(
    "src,expected_len",
    [
        (SHORT_LEGO, 32),
        (MALFORMED_LEGO, 128),
    ],
    ids=["receipt-short", "receipt-malformed-address"],
)
def test_g7_malformed_yield_receipt_reverts_mint(
    endaoment_psm, undy_hub, charlie_token, green_token, switchboard_charlie,
    governance, mock_price_source, wired, src, expected_len,
):
    """Typed `depositForYield` decode reverts; a take inside the Lego rolls back."""
    psm = endaoment_psm
    _enable(psm, switchboard_charlie)
    user = boa.env.generate_address()
    charlie_token.mint(user, 10_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(psm.address, MAX_UINT256, sender=user)

    noop = boa.loads(src, False, name="g7_receipt_noop")
    assert _depositForYield_len(
        noop.address, charlie_token.address, 0, ZERO_ADDRESS, psm.address
    ) == expected_len

    taker = boa.loads(src, True, name="g7_receipt_take")
    undy_hub.setLegoAddrOverride(taker.address)
    pre_user = charlie_token.balanceOf(user)
    pre_psm = charlie_token.balanceOf(psm.address)
    pre_supply = green_token.totalSupply()
    with boa.reverts():
        psm.mintGreen(1_000 * SIX_DECIMALS, user, False, sender=user)
    after_psm_tx()
    assert charlie_token.balanceOf(user) == pre_user
    assert charlie_token.balanceOf(psm.address) == pre_psm
    assert green_token.totalSupply() == pre_supply
    assert charlie_token.allowance(psm.address, taker.address) == 0

    undy_hub.setLegoAddrOverride(noop.address)
    with boa.reverts():
        psm.mintGreen(1_000 * SIX_DECIMALS, user, False, sender=user)
    after_psm_tx()
    assert charlie_token.balanceOf(user) == pre_user
    assert green_token.totalSupply() == pre_supply
    assert charlie_token.allowance(psm.address, noop.address) == 0
    undy_hub.setLegoAddrOverride(ZERO_ADDRESS)


def test_g7_oversized_yield_receipt_decodes_prefix(
    endaoment_psm, undy_hub, charlie_token, green_token, switchboard_charlie,
    governance, mock_price_source, wired,
):
    """Typed ABI ignores the extra byte; the first four words are zeros."""
    psm = endaoment_psm
    _enable(psm, switchboard_charlie)
    user = boa.env.generate_address()
    charlie_token.mint(user, 10_000 * SIX_DECIMALS, sender=governance.address)
    charlie_token.approve(psm.address, MAX_UINT256, sender=user)

    noop = boa.loads(OVERSIZE_LEGO, False, name="g7_oversize_noop")
    assert _depositForYield_len(
        noop.address, charlie_token.address, 0, ZERO_ADDRESS, psm.address
    ) == 129

    taker = boa.loads(OVERSIZE_LEGO, True, name="g7_oversize_take")
    undy_hub.setLegoAddrOverride(taker.address)
    minted = psm.mintGreen(1_000 * SIX_DECIMALS, user, False, sender=user)
    ev = filter_logs(psm, "EndaomentPSMYieldDeposit")[0]
    after_psm_tx()
    assert minted == 1_000 * EIGHTEEN_DECIMALS
    assert ev.amount == 0
    assert charlie_token.balanceOf(psm.address) == 0
    assert charlie_token.balanceOf(taker.address) == 1_000 * SIX_DECIMALS

    undy_hub.setLegoAddrOverride(noop.address)
    minted = psm.mintGreen(1_000 * SIX_DECIMALS, user, False, sender=user)
    ev = filter_logs(psm, "EndaomentPSMYieldDeposit")[0]
    after_psm_tx()
    assert minted == 1_000 * EIGHTEEN_DECIMALS
    assert ev.amount == 0
    assert charlie_token.balanceOf(psm.address) == 1_000 * SIX_DECIMALS
    undy_hub.setLegoAddrOverride(ZERO_ADDRESS)


def test_g7_explicit_withdraw_from_yield_still_reverts_on_failing_venue(
    endaoment_psm, undy_hub, charlie_token, switchboard_charlie,
    governance, mock_price_source, wired,
):
    psm = endaoment_psm
    _enable(psm, switchboard_charlie)
    psm.setShouldAutoDeposit(False, sender=switchboard_charlie.address)
    charlie_token.mint(psm.address, 1_000 * SIX_DECIMALS, sender=governance.address)
    psm.depositToYield(sender=switchboard_charlie.address)
    after_psm_tx()
    undy_hub.setRevertOnWithdraw(True)
    with boa.reverts():
        psm.withdrawFromYield(1_000 * SIX_DECIMALS, False, False, sender=switchboard_charlie.address)
    undy_hub.setRevertOnWithdraw(False)
    psm.setShouldAutoDeposit(True, sender=switchboard_charlie.address)
