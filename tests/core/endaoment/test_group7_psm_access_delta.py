"""Group 7 PSM proofs — never-skip #5: allowlist, pause, enablement, Echo
lite-vs-governor gates, Delta registry install + clear.

Enablement in user-flow fixtures: setCanMint/setCanRedeem with
sender=switchboard_charlie.address (address impersonation; suite shortcut).
Echo initiate/execute here is the production enablement proof (governor +
timelock), not a substitute for EOA mint/redeem (those are covered in the
conservation files). Lite signer enabled in fixture via
mission_control.setCanPerformLiteAction(sally, True, sender=switchboard_echo)
— launch liteSigners are empty, so lite access is governance-enableable
(stated per brief).
"""

import boa
import pytest

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS, MAX_UINT256

from tests.core.endaoment import g7_psm_helpers as g7


SIX = 10**6
E18 = 10**18
ONE_DAY_BLOCKS = 43_200


@pytest.fixture(autouse=True)
def _reset(endaoment_psm, switchboard_charlie, mission_control, switchboard_alpha, mock_undy_v2):
    g7.reset_psm_regular(
        endaoment_psm, switchboard_charlie, mission_control, switchboard_alpha, mock_undy_v2
    )
    yield


def _enable(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token, price=E18):
    mock_price_source.setPrice(charlie_token.address, price)
    if not endaoment_psm.canMint():
        endaoment_psm.setCanMint(True, sender=switchboard_charlie.address)
    if not endaoment_psm.canRedeem():
        endaoment_psm.setCanRedeem(True, sender=switchboard_charlie.address)


#############
# Allowlist #
#############


def test_g7_allowlist_sender_gated(
    endaoment_psm, charlie_token, green_token,
    switchboard_charlie, governance, mock_price_source,
):
    """Enforce on: unlisted sender + EOA recipient reverts; listed sender
    succeeds. Allowlist keys msg.sender, not recipient."""
    user = boa.env.generate_address()
    listed = boa.env.generate_address()
    _enable(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
    endaoment_psm.setShouldEnforceMintAllowlist(True, sender=switchboard_charlie.address)

    usdc_amount = 100 * SIX
    for who in (user, listed):
        charlie_token.mint(who, usdc_amount, sender=governance.address)
        charlie_token.approve(endaoment_psm.address, usdc_amount, sender=who)

    with boa.reverts("not on mint allowlist"):
        endaoment_psm.mintGreen(usdc_amount, user, False, sender=user)
    g7.after_psm_tx()

    endaoment_psm.updateMintAllowlist(listed, True, sender=switchboard_charlie.address)
    endaoment_psm.mintGreen(usdc_amount, listed, False, sender=listed)
    assert green_token.balanceOf(listed) == 100 * E18


def test_g7_allowlist_unlisted_sender_vault_recipient_succeeds(
    endaoment_psm, charlie_token, green_token,
    switchboard_charlie, mission_control, switchboard_alpha, mock_undy_v2,
    governance, mock_price_source,
):
    """Enforce on: unlisted sender + VAULT recipient succeeds (vault skip)."""
    vault = boa.env.generate_address()
    user = boa.env.generate_address()
    mock_undy_v2.setAllAddressesAreVaults(False)
    mock_undy_v2.setEarnVault(vault, True)
    mission_control.setUnderscoreRegistry(mock_undy_v2.address, sender=switchboard_alpha.address)
    _enable(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
    endaoment_psm.setShouldEnforceMintAllowlist(True, sender=switchboard_charlie.address)

    usdc_amount = 100 * SIX
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)
    endaoment_psm.mintGreen(usdc_amount, vault, False, sender=user)
    assert green_token.balanceOf(vault) == 100 * E18


def test_g7_pause_blocks_mint_and_redeem(
    endaoment_psm, charlie_token, green_token,
    switchboard_charlie, governance, mock_price_source, whale,
):
    """Pause blocks both entries (and the setters, already covered by existing
    config tests)."""
    user = boa.env.generate_address()
    _enable(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
    usdc_amount = 100 * SIX
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)
    charlie_token.mint(endaoment_psm.address, usdc_amount, sender=governance.address)

    endaoment_psm.pause(True, sender=switchboard_charlie.address)
    with boa.reverts("contract paused"):
        endaoment_psm.mintGreen(usdc_amount, user, False, sender=user)
    g7.after_psm_tx()
    green_token.transfer(user, 100 * E18, sender=whale)
    green_token.approve(endaoment_psm.address, 100 * E18, sender=user)
    with boa.reverts("contract paused"):
        endaoment_psm.redeemGreen(100 * E18, user, False, sender=user)


def test_g7_flags_off_block_mint_redeem(
    endaoment_psm, charlie_token, green_token,
    switchboard_charlie, governance, mock_price_source, whale,
):
    """canMint=False / canRedeem=False block (launch posture, not a finding)."""
    user = boa.env.generate_address()
    mock_price_source.setPrice(charlie_token.address, E18)
    assert not endaoment_psm.canMint() and not endaoment_psm.canRedeem()

    usdc_amount = 100 * SIX
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)
    with boa.reverts("minting disabled"):
        endaoment_psm.mintGreen(usdc_amount, user, False, sender=user)
    g7.after_psm_tx()

    green_token.transfer(user, 100 * E18, sender=whale)
    green_token.approve(endaoment_psm.address, 100 * E18, sender=user)
    with boa.reverts("redemption disabled"):
        endaoment_psm.redeemGreen(100 * E18, user, False, sender=user)


def test_g7_direct_green_mint_from_unauthorized_reverts(
    green_token,
):
    """Direct GreenToken.mint from a non-canMintGreen address reverts."""
    rando = boa.env.generate_address()
    with boa.reverts("cannot mint"):
        green_token.mint(rando, E18, sender=rando)


############################
# Echo lite vs governor    #
############################


def test_g7_echo_lite_disable_initiate_only_governor_executes(
    switchboard_echo, endaoment_psm, mission_control, governance, sally,
    switchboard_charlie, mock_price_source, charlie_token,
):
    """Lite (sally with canPerformLiteAction): initiates False -> pending only,
    PSM flag unchanged; lite initiate True -> reverts; lite executePendingAction
    on its own disable -> reverts (governor-only); governor executes after the
    timelock -> flag flips. Disable is NOT an immediate emergency switch."""
    _enable(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
    assert endaoment_psm.canMint()

    mission_control.setCanPerformLiteAction(sally, True, sender=switchboard_echo.address)

    # lite initiates True -> reverts
    with boa.reverts("no perms"):
        switchboard_echo.setPsmCanMint(True, sender=sally)

    # lite initiates False -> queued, flag UNCHANGED (not immediate)
    aid = switchboard_echo.setPsmCanMint(False, sender=sally)
    assert endaoment_psm.canMint()  # still on

    # lite cannot execute its own disable
    boa.env.time_travel(blocks=switchboard_echo.actionTimeLock())
    with boa.reverts("no perms"):
        switchboard_echo.executePendingAction(aid, sender=sally)
    assert endaoment_psm.canMint()  # still on

    # governor executes after the timelock -> flag flips
    result = switchboard_echo.executePendingAction(aid, sender=governance.address)
    assert result
    assert not endaoment_psm.canMint()

    # governor initiate True + execute is the enable path
    aid2 = switchboard_echo.setPsmCanMint(True, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_echo.actionTimeLock())
    assert switchboard_echo.executePendingAction(aid2, sender=governance.address)
    assert endaoment_psm.canMint()


def test_g7_echo_cancel_leaves_flag_unchanged(
    switchboard_echo, endaoment_psm, mission_control, governance, sally,
    switchboard_charlie, mock_price_source, charlie_token,
):
    """Governor cancel of a pending lite disable leaves the flag unchanged."""
    _enable(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
    assert endaoment_psm.canRedeem()

    mission_control.setCanPerformLiteAction(sally, True, sender=switchboard_echo.address)
    aid = switchboard_echo.setPsmCanRedeem(False, sender=sally)
    assert endaoment_psm.canRedeem()

    switchboard_echo.cancelPendingAction(aid, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_echo.actionTimeLock() + 1)
    assert endaoment_psm.canRedeem()  # unchanged


def test_g7_echo_governor_enable_flow_end_to_end(
    switchboard_echo, endaoment_psm, charlie_token, green_token,
    governance, mock_price_source, switchboard_charlie,
):
    """Production enablement proof: governor initiate(True) + timelock +
    execute flips canMint; an ordinary EOA then mints."""
    mock_price_source.setPrice(charlie_token.address, E18)
    assert not endaoment_psm.canMint()

    aid = switchboard_echo.setPsmCanMint(True, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_echo.actionTimeLock())
    assert switchboard_echo.executePendingAction(aid, sender=governance.address)
    assert endaoment_psm.canMint()

    user = boa.env.generate_address()
    usdc_amount = 100 * SIX
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)
    endaoment_psm.mintGreen(usdc_amount, user, False, sender=user)
    assert green_token.balanceOf(user) == 100 * E18


############################
# Delta install + clear    #
############################


def test_g7_delta_install_and_clear_registry(
    switchboard_delta, mission_control, endaoment_psm, mock_undy_v2,
    governance, switchboard_charlie, mock_price_source, charlie_token, green_token,
):
    """One Delta initiate+execute install of the mock registry, and one
    initiate+execute clear to empty. Vault privileges track the registry
    after each. (MockUndyV2 passes Delta's Ledger probe: getAddr(1) returns
    the mock itself and isUserWallet(empty) is False.)"""
    _enable(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
    vault = boa.env.generate_address()
    mock_undy_v2.setAllAddressesAreVaults(False)
    mock_undy_v2.setEarnVault(vault, True)

    # install via Delta (governor + timelock)
    aid = switchboard_delta.setUnderscoreRegistry(mock_undy_v2.address, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    assert switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert mission_control.underscoreRegistry() == mock_undy_v2.address

    # vault recipient now skips the fee
    endaoment_psm.setMintFee(500, sender=switchboard_charlie.address)
    usdc_amount = 100 * SIX
    charlie_token.mint(vault, 2 * usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, 2 * usdc_amount, sender=vault)
    endaoment_psm.mintGreen(usdc_amount, vault, False, sender=vault)
    ev1 = g7.last_mint_event(endaoment_psm)
    g7.after_psm_tx()
    assert ev1.usdcFee == 0  # skip on

    # clear via Delta (empty is a legal clear)
    aid2 = switchboard_delta.setUnderscoreRegistry(ZERO_ADDRESS, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    assert switchboard_delta.executePendingAction(aid2, sender=governance.address)
    assert mission_control.underscoreRegistry() == ZERO_ADDRESS

    endaoment_psm.mintGreen(usdc_amount, vault, False, sender=vault)
    ev2 = g7.last_mint_event(endaoment_psm)
    assert ev2.usdcFee == usdc_amount * 500 // 10_000  # skip off


def test_g7_delta_probe_accepts_registry_psm_cannot_consume(
    switchboard_delta, mission_control, endaoment_psm, mock_undy_v2,
    governance, switchboard_charlie, mock_price_source, charlie_token, green_token,
):
    """Group 9's Delta sentinel accepts MockUndyV2. A registry whose vault
    id (10) resolves but whose isEarnVault is False for every address still
    gives no vault privileges — typed False is regular treatment."""
    # mock_undy_v2 already: getAddr(id) -> self, isUserWallet(empty) -> False
    # set ALL vault checks False so isEarnVault always False
    mock_undy_v2.setAllAddressesAreVaults(False)
    aid = switchboard_delta.setUnderscoreRegistry(mock_undy_v2.address, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    assert switchboard_delta.executePendingAction(aid, sender=governance.address)
    assert mission_control.underscoreRegistry() == mock_undy_v2.address

    _enable(endaoment_psm, switchboard_charlie, mock_price_source, charlie_token)
    endaoment_psm.setMintFee(500, sender=switchboard_charlie.address)
    user = boa.env.generate_address()
    usdc_amount = 100 * SIX
    charlie_token.mint(user, usdc_amount, sender=governance.address)
    charlie_token.approve(endaoment_psm.address, usdc_amount, sender=user)
    endaoment_psm.mintGreen(usdc_amount, user, False, sender=user)
    ev = g7.last_mint_event(endaoment_psm)
    assert ev.usdcFee == usdc_amount * 500 // 10_000
    assert green_token.balanceOf(user) == 95 * E18
