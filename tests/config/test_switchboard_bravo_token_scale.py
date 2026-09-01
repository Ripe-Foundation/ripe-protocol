import boa
import pytest

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS


ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"

DECIMALS_TOKEN = """
# @version 0.4.3

_decimals: public(uint8)
should_revert: public(bool)

@deploy
def __init__(_decimals: uint8):
    self._decimals = _decimals

@external
def setShouldRevert(_v: bool):
    self.should_revert = _v

@view
@external
def decimals() -> uint8:
    if self.should_revert:
        raise "decimals revert"
    return self._decimals
"""

MOCK_HQ = """
# @version 0.4.3

governance: public(address)
switchboard: public(address)
priceDesk: public(address)

@deploy
def __init__(_gov: address, _switchboard: address, _priceDesk: address):
    self.governance = _gov
    self.switchboard = _switchboard
    self.priceDesk = _priceDesk

@view
@external
def getAddr(_regId: uint256) -> address:
    if _regId == 6:
        return self.switchboard
    if _regId == 7:
        return self.priceDesk
    return empty(address)

@view
@external
def minGovChangeTimeLock() -> uint256:
    return 1

@view
@external
def maxGovChangeTimeLock() -> uint256:
    return 100
"""


def _token(decimals=18):
    return boa.loads(DECIMALS_TOKEN, decimals)


def _add_fungible(switchboard_golf, governance, asset, mission_control=ZERO_ADDRESS):
    return switchboard_golf.addAsset(
        asset,
        [1],
        0,
        0,
        1000,
        10000,
        0,
        (0, 0, 0, 0, 0, 0),
        False,
        False,
        False,
        True,
        True,
        True,
        False,
        True,
        True,
        True,
        0,
        (False, 0, 0, 0, 0),
        ZERO_ADDRESS,
        False,
        mission_control,
        sender=governance.address,
    )


def _add_nft(switchboard_golf, governance, asset):
    return switchboard_golf.addAsset(
        asset,
        [1],
        0,
        0,
        1000,
        10000,
        0,
        (0, 0, 0, 0, 0, 0),
        False,
        False,
        False,
        True,
        True,
        True,
        False,
        True,
        True,
        True,
        0,
        (False, 0, 0, 0, 0),
        ZERO_ADDRESS,
        True,
        sender=governance.address,
    )


def _execute(switchboard_bravo, governance, action_id):
    boa.env.time_travel(blocks=switchboard_bravo.actionTimeLock())
    return switchboard_bravo.executePendingAction(action_id, sender=governance.address)


def _feed(mock_price_source, token):
    mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)


def test_fungible_add_new_stores_config_and_scale(
    switchboard_golf,
    mission_control,
    governance,
    price_desk,
    ripe_hq,
):
    token = _token(8)
    assert price_desk.tokenScale(token) == 0
    action_id = _add_fungible(switchboard_golf, governance, token)
    assert _execute(switchboard_golf, governance, action_id)
    assert mission_control.isSupportedAsset(token.address)
    assert price_desk.tokenScale(token) == 10**8


def test_fungible_add_new_does_not_need_a_feed(
    switchboard_golf,
    mission_control,
    governance,
    price_desk,
    ripe_hq,
):
    token = _token(18)
    action_id = _add_fungible(switchboard_golf, governance, token)
    assert _execute(switchboard_golf, governance, action_id)
    assert mission_control.isSupportedAsset(token.address)
    assert price_desk.tokenScale(token) == EIGHTEEN_DECIMALS


def test_preseeded_scale_skips_decimals_and_succeeds(
    switchboard_golf,
    mission_control,
    governance,
    price_desk,
    ripe_hq,
):
    token = _token(8)
    price_desk.syncTokenScale(token, sender=governance.address)
    token.setShouldRevert(True)
    action_id = _add_fungible(switchboard_golf, governance, token)
    assert _execute(switchboard_golf, governance, action_id)
    assert mission_control.isSupportedAsset(token.address)
    assert price_desk.tokenScale(token) == 10**8


def test_nft_admission_does_not_require_scale(
    switchboard_golf,
    mission_control,
    governance,
    price_desk,
    mock_rando_contract,
    ripe_hq,
):
    action_id = _add_nft(switchboard_golf, governance, mock_rando_contract)
    assert _execute(switchboard_golf, governance, action_id)
    assert mission_control.isSupportedAsset(mock_rando_contract.address)
    assert mission_control.assetConfig(mock_rando_contract.address).isNft
    assert price_desk.tokenScale(mock_rando_contract) == 0


def test_sync_failure_rolls_back_mission_control(
    switchboard_golf,
    mission_control,
    governance,
    price_desk,
    mock_price_source,
    ripe_hq,
):
    token = _token(18)
    _feed(mock_price_source, token)
    token.setShouldRevert(True)
    action_id = _add_fungible(switchboard_golf, governance, token)
    pending_before = switchboard_golf.pendingAssetConfig(action_id)
    action_type_before = switchboard_golf.actionType(action_id)
    with boa.reverts("decimals revert"):
        _execute(switchboard_golf, governance, action_id)
    assert not mission_control.isSupportedAsset(token.address)
    assert price_desk.tokenScale(token) == 0
    assert switchboard_golf.hasPendingAction(action_id)
    assert switchboard_golf.actionType(action_id) == action_type_before
    assert switchboard_golf.pendingAssetConfig(action_id) == pending_before


def test_missing_target_price_desk_fails_atomically(
    switchboard_golf,
    mission_control,
    governance,
    switchboard,
    defaults,
    ripe_hq,
):
    token = _token(18)
    mock_hq = boa.loads(MOCK_HQ, governance.address, switchboard.address, ZERO_ADDRESS)
    replacement = boa.load(
        "contracts/data/MissionControl.vy",
        mock_hq,
        defaults,
        name="missing_desk_mission_control",
    )
    replacement.setCoreRipeGovVaultId(2, sender=switchboard_golf.address)
    replacement.setPreferredStabVaultId(1, sender=switchboard_golf.address)
    action_id = _add_fungible(
        switchboard_golf,
        governance,
        token,
        replacement.address,
    )
    pending_before = switchboard_golf.pendingAssetConfig(action_id)
    with boa.reverts("missing price desk"):
        _execute(switchboard_golf, governance, action_id)
    assert not replacement.isSupportedAsset(token.address)
    assert not mission_control.isSupportedAsset(token.address)
    assert switchboard_golf.hasPendingAction(action_id)
    assert switchboard_golf.pendingAssetConfig(action_id) == pending_before


def test_replacement_mission_control_updates_only_its_price_desk(
    switchboard_golf,
    mission_control,
    governance,
    switchboard,
    defaults,
    price_desk,
    ripe_hq,
    deploy3r,
):
    token = _token(8)
    other_desk = boa.load(
        "contracts/registries/PriceDesk.vy",
        ripe_hq,
        deploy3r,
        ETH,
        1,
        2,
        name="replacement_price_desk",
    )
    mock_hq = boa.loads(MOCK_HQ, governance.address, switchboard.address, other_desk.address)
    replacement = boa.load(
        "contracts/data/MissionControl.vy",
        mock_hq,
        defaults,
        name="replacement_mission_control",
    )
    replacement.setCoreRipeGovVaultId(2, sender=switchboard_golf.address)
    replacement.setPreferredStabVaultId(1, sender=switchboard_golf.address)

    default_scale_before = price_desk.tokenScale(token)
    action_id = _add_fungible(
        switchboard_golf,
        governance,
        token,
        replacement.address,
    )
    assert _execute(switchboard_golf, governance, action_id)
    assert replacement.isSupportedAsset(token.address)
    assert not mission_control.isSupportedAsset(token.address)
    assert other_desk.tokenScale(token) == 10**8
    assert price_desk.tokenScale(token) == default_scale_before


def test_non_add_new_actions_do_not_change_scale(
    switchboard_bravo,
    switchboard_golf,
    mission_control,
    governance,
    price_desk,
    ripe_hq,
):
    token = _token(8)
    add_id = _add_fungible(switchboard_golf, governance, token)
    assert _execute(switchboard_golf, governance, add_id)
    assert price_desk.tokenScale(token) == 10**8

    deposit_id = switchboard_bravo.setAssetDepositParams(
        token,
        [1],
        0,
        0,
        2000,
        20000,
        0,
        sender=governance.address,
    )
    debt_id = switchboard_golf.setAssetDebtTerms(
        token,
        70_00,
        75_00,
        80_00,
        8_00,
        12_00,
        3_00,
        sender=governance.address,
    )
    boa.env.time_travel(
        blocks=max(
            switchboard_bravo.actionTimeLock(),
            switchboard_golf.actionTimeLock(),
        )
    )
    assert switchboard_bravo.executePendingAction(deposit_id, sender=governance.address)
    assert switchboard_golf.executePendingAction(debt_id, sender=governance.address)
    assert price_desk.tokenScale(token) == 10**8
    assert mission_control.assetConfig(token.address).perUserDepositLimit == 2000
