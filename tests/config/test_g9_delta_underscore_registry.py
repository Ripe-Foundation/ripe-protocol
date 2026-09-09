# Group 9 — account permissions.
# Never-skip #6: SwitchboardDelta.setUnderscoreRegistry, initiate + execute only.
# This is the production write for underscoreRegistry — no MissionControl injection.
#
# _isValidUnderscoreAddr is an initiate-time sentinel: empty (clear) is allowed;
# ledger getAddr(1) nonempty and isUserWallet(empty) == False; root
# isValidAddr(empty) == False; nonempty getAddr(10) requires
# isEarnVault(empty) == False; nonempty getAddr(3) requires
# isValidAddr(empty) == False. Missing / reverting selectors reject.

import boa
import pytest

from conf_utils import filter_logs
from constants import ZERO_ADDRESS


UNDERSCORE_LEDGER_ID = 1
UNDERSCORE_LEGOBOOK_ID = 3
UNDERSCORE_VAULT_REGISTRY_ID = 10
MISSION_CONTROL_REG_ID = 5


# Fully conforming: getAddr, isValidAddr, plus a real ledger / vault registry / legobook.
ROOT_REGISTRY_SOURCE = """
# @version 0.4.3

addrs: public(HashMap[uint256, address])
validAddrs: public(HashMap[address, bool])

@external
def setAddr(_regId: uint256, _addr: address):
    self.addrs[_regId] = _addr

@external
def setValid(_addr: address, _isValid: bool):
    self.validAddrs[_addr] = _isValid

@view
@external
def getAddr(_regId: uint256) -> address:
    return self.addrs[_regId]

@view
@external
def isValidAddr(_addr: address) -> bool:
    return self.validAddrs[_addr]
"""

UNDY_LEDGER_SOURCE = """
# @version 0.4.3

wallets: public(HashMap[address, bool])

@external
def setWallet(_addr: address, _isWallet: bool):
    self.wallets[_addr] = _isWallet

@view
@external
def isUserWallet(_addr: address) -> bool:
    return self.wallets[_addr]
"""

# A ledger that claims the zero address is a wallet — Delta must reject the registry.
LYING_LEDGER_SOURCE = """
# @version 0.4.3

@view
@external
def isUserWallet(_addr: address) -> bool:
    return True
"""

# Has a real ledger and isUserWallet(empty) == False, but no isValidAddr.
# The root sentinel now rejects it (missing selector reverts).
NO_IS_VALID_ADDR_REGISTRY_SOURCE = """
# @version 0.4.3

addrs: public(HashMap[uint256, address])

@external
def setAddr(_regId: uint256, _addr: address):
    self.addrs[_regId] = _addr

@view
@external
def getAddr(_regId: uint256) -> address:
    return self.addrs[_regId]
"""

# A vault registry pointer that exists but has no isEarnVault.
BROKEN_VAULT_REGISTRY_SOURCE = """
# @version 0.4.3

@view
@external
def notIsEarnVault(_vaultAddr: address) -> bool:
    return False
"""

HONEST_VAULT_REGISTRY_SOURCE = """
# @version 0.4.3

@view
@external
def isEarnVault(_vaultAddr: address) -> bool:
    return False
"""

ALWAYS_VAULT_REGISTRY_SOURCE = """
# @version 0.4.3

@view
@external
def isEarnVault(_vaultAddr: address) -> bool:
    return True
"""

REVERTING_VAULT_REGISTRY_SOURCE = """
# @version 0.4.3

@view
@external
def isEarnVault(_vaultAddr: address) -> bool:
    raise "broken vault registry"
"""

LEGOBOOK_SOURCE = """
# @version 0.4.3

validEmpty: public(bool)

@external
def setValidEmpty(_v: bool):
    self.validEmpty = _v

@view
@external
def isValidAddr(_addr: address) -> bool:
    return self.validEmpty
"""

REVERTING_IS_VALID_ADDR_SOURCE = """
# @version 0.4.3

@view
@external
def isValidAddr(_addr: address) -> bool:
    raise "isValidAddr revert"
"""

MISSING_IS_VALID_ADDR_SOURCE = """
# @version 0.4.3

@view
@external
def dummy() -> bool:
    return True
"""

ROOT_REVERTING_IS_VALID_ADDR_SOURCE = """
# @version 0.4.3

addrs: public(HashMap[uint256, address])

@external
def setAddr(_regId: uint256, _addr: address):
    self.addrs[_regId] = _addr

@view
@external
def getAddr(_regId: uint256) -> address:
    return self.addrs[_regId]

@view
@external
def isValidAddr(_addr: address) -> bool:
    raise "isValidAddr revert"
"""

GETADDR_REVERT_ROOT_SOURCE = """
# @version 0.4.3

addrs: public(HashMap[uint256, address])
revertId: public(uint256)

@external
def setAddr(_regId: uint256, _addr: address):
    self.addrs[_regId] = _addr

@external
def setRevertId(_regId: uint256):
    self.revertId = _regId

@view
@external
def getAddr(_regId: uint256) -> address:
    assert _regId != self.revertId, "getAddr revert"
    return self.addrs[_regId]

@view
@external
def isValidAddr(_addr: address) -> bool:
    return False
"""


@pytest.fixture
def undy_ledger():
    return boa.loads(UNDY_LEDGER_SOURCE, name="g9_undy_ledger")


@pytest.fixture
def conforming_registry(undy_ledger):
    root = boa.loads(ROOT_REGISTRY_SOURCE, name="g9_conforming_root")
    root.setAddr(UNDERSCORE_LEDGER_ID, undy_ledger.address)
    return root


@pytest.fixture
def unregistered_mc(ripe_hq, defaults):
    return boa.load("contracts/data/MissionControl.vy", ripe_hq, defaults, name="g9_delta_other_mc")


def _execute(switchboard_delta, governance, aid):
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    return switchboard_delta.executePendingAction(aid, sender=governance.address)


def _assert_initiate_rejected(
    switchboard_delta, governance, mission_control, registry_addr, revert=None
):
    aid_before = switchboard_delta.actionId()
    pending_before = switchboard_delta.pendingUnderscoreRegistry(aid_before)
    action_type_before = switchboard_delta.actionType(aid_before)
    mc_before = mission_control.underscoreRegistry()
    ctx = boa.reverts() if revert is None else boa.reverts(revert)
    with ctx:
        switchboard_delta.setUnderscoreRegistry(
            registry_addr, sender=governance.address
        )
    assert switchboard_delta.actionId() == aid_before
    assert switchboard_delta.pendingUnderscoreRegistry(aid_before) == pending_before
    assert switchboard_delta.actionType(aid_before) == action_type_before
    assert mission_control.underscoreRegistry() == mc_before


##########################
# Authorisation          #
##########################


def test_g9_delta_non_governor_initiate_rejects_with_no_pending_state(
    switchboard_delta, mission_control, conforming_registry, bob
):
    before = switchboard_delta.actionType(1)
    with boa.reverts("no perms"):
        switchboard_delta.setUnderscoreRegistry(conforming_registry.address, sender=bob)
    assert mission_control.underscoreRegistry() == ZERO_ADDRESS
    assert switchboard_delta.actionType(1) == before
    assert switchboard_delta.pendingUnderscoreRegistry(1) == ZERO_ADDRESS


##########################
# Validation at initiate #
##########################


def test_g9_delta_rejects_an_eoa(switchboard_delta, governance):
    eoa = boa.env.generate_address()
    with boa.reverts():
        switchboard_delta.setUnderscoreRegistry(eoa, sender=governance.address)


def test_g9_delta_rejects_a_registry_whose_ledger_pointer_is_empty(
    switchboard_delta, governance
):
    root = boa.loads(ROOT_REGISTRY_SOURCE, name="g9_empty_ledger_root")
    with boa.reverts("invalid underscore registry"):
        switchboard_delta.setUnderscoreRegistry(root.address, sender=governance.address)


def test_g9_delta_rejects_a_ledger_that_calls_the_zero_address_a_wallet(
    switchboard_delta, governance
):
    root = boa.loads(ROOT_REGISTRY_SOURCE, name="g9_lying_root")
    root.setAddr(UNDERSCORE_LEDGER_ID, boa.loads(LYING_LEDGER_SOURCE, name="g9_lying_ledger").address)
    with boa.reverts("invalid underscore registry"):
        switchboard_delta.setUnderscoreRegistry(root.address, sender=governance.address)


##################################
# Full install / clear lifecycle #
##################################


def test_g9_delta_install_then_clear_full_lifecycle(
    switchboard_delta, governance, mission_control, conforming_registry
):
    # --- install ---
    aid = switchboard_delta.setUnderscoreRegistry(conforming_registry.address, sender=governance.address)
    assert aid > 0

    pending_logs = filter_logs(switchboard_delta, "PendingUnderscoreRegistryChange")
    assert len(pending_logs) == 1
    assert pending_logs[0].underscoreRegistry == conforming_registry.address
    assert pending_logs[0].actionId == aid

    # unchanged before confirmation
    assert mission_control.underscoreRegistry() == ZERO_ADDRESS
    assert switchboard_delta.pendingUnderscoreRegistry(aid) == conforming_registry.address
    assert switchboard_delta.executePendingAction(aid, sender=governance.address) is False
    assert mission_control.underscoreRegistry() == ZERO_ADDRESS

    assert _execute(switchboard_delta, governance, aid) is True
    assert mission_control.underscoreRegistry() == conforming_registry.address

    set_logs = filter_logs(switchboard_delta, "UnderscoreRegistrySet")
    assert len(set_logs) == 1
    assert set_logs[0].addr == conforming_registry.address

    # --- clear ---
    clear_aid = switchboard_delta.setUnderscoreRegistry(ZERO_ADDRESS, sender=governance.address)
    assert mission_control.underscoreRegistry() == conforming_registry.address
    assert _execute(switchboard_delta, governance, clear_aid) is True
    assert mission_control.underscoreRegistry() == ZERO_ADDRESS

    clear_logs = filter_logs(switchboard_delta, "UnderscoreRegistrySet")
    assert len(clear_logs) == 1
    assert clear_logs[0].addr == ZERO_ADDRESS


def test_g9_delta_cancel_leaves_the_registry_unchanged(
    switchboard_delta, governance, mission_control, conforming_registry
):
    aid = switchboard_delta.setUnderscoreRegistry(conforming_registry.address, sender=governance.address)
    assert switchboard_delta.cancelPendingAction(aid, sender=governance.address) is True
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    assert switchboard_delta.executePendingAction(aid, sender=governance.address) is False
    assert mission_control.underscoreRegistry() == ZERO_ADDRESS


def test_g9_delta_expiry_leaves_the_registry_unchanged(
    switchboard_delta, governance, mission_control, conforming_registry
):
    aid = switchboard_delta.setUnderscoreRegistry(conforming_registry.address, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_delta.expiration() + switchboard_delta.actionTimeLock() + 1)
    assert switchboard_delta.executePendingAction(aid, sender=governance.address) is False
    assert mission_control.underscoreRegistry() == ZERO_ADDRESS


##########################################
# pendingMissionControl snapshot         #
##########################################


def test_g9_delta_pending_mc_is_snapshotted_at_initiate(
    switchboard_delta,
    governance,
    ripe_hq,
    mission_control,
    unregistered_mc,
    conforming_registry,
):
    mc_a = mission_control
    mc_b = unregistered_mc
    aid = switchboard_delta.setUnderscoreRegistry(conforming_registry.address, sender=governance.address)
    assert switchboard_delta.pendingMissionControl(aid) == mc_a.address

    hq_lock = ripe_hq.registryChangeTimeLock()
    assert ripe_hq.startAddressUpdateToRegistry(MISSION_CONTROL_REG_ID, mc_b.address, sender=governance.address)
    boa.env.time_travel(blocks=hq_lock)
    assert ripe_hq.confirmAddressUpdateToRegistry(MISSION_CONTROL_REG_ID, sender=governance.address)

    assert _execute(switchboard_delta, governance, aid) is True
    assert mc_a.underscoreRegistry() == conforming_registry.address
    assert mc_b.underscoreRegistry() == ZERO_ADDRESS


def test_g9_delta_passing_the_current_mc_at_initiate_reverts(
    switchboard_delta, governance, mission_control, conforming_registry
):
    with boa.reverts("use empty for current mission control"):
        switchboard_delta.setUnderscoreRegistry(
            conforming_registry.address, mission_control.address, sender=governance.address
        )


#####################################################
# Validation boundary — initiate-time sentinel      #
#####################################################


def test_g9_delta_probe_rejects_a_registry_with_no_is_valid_addr(
    switchboard_delta, governance, mission_control, undy_ledger
):
    """Missing root isValidAddr reverts at initiate."""
    root = boa.loads(NO_IS_VALID_ADDR_REGISTRY_SOURCE, name="g9_no_isvalidaddr_root")
    root.setAddr(UNDERSCORE_LEDGER_ID, undy_ledger.address)
    _assert_initiate_rejected(
        switchboard_delta, governance, mission_control, root.address
    )


def test_g9_delta_probe_rejects_a_registry_whose_vault_registry_is_broken(
    switchboard_delta, governance, mission_control, undy_ledger
):
    """Root isValidAddr(empty) is False so the reject is missing slot-10 isEarnVault."""
    root = boa.loads(ROOT_REGISTRY_SOURCE, name="g9_broken_vaultreg_root")
    root.setAddr(UNDERSCORE_LEDGER_ID, undy_ledger.address)
    root.setAddr(
        UNDERSCORE_VAULT_REGISTRY_ID,
        boa.loads(BROKEN_VAULT_REGISTRY_SOURCE, name="g9_broken_vault_registry").address,
    )
    _assert_initiate_rejected(
        switchboard_delta, governance, mission_control, root.address
    )


def test_g9_delta_probe_admits_a_registry_with_no_legobook_pointer(
    switchboard_delta, governance, teller_utils, undy_ledger, conforming_registry, alice, bob
):
    """Missing LegoBook pointer is the graceful case: _isUnderscoreAddr returns False."""
    aid = switchboard_delta.setUnderscoreRegistry(conforming_registry.address, sender=governance.address)
    assert _execute(switchboard_delta, governance, aid) is True
    assert conforming_registry.getAddr(UNDERSCORE_LEGOBOOK_ID) == ZERO_ADDRESS
    assert teller_utils.isUnderscoreAddr(alice) is False
    assert teller_utils.isUnderscoreOwnerOrLego(bob, alice) is False


def test_g9_delta_rejects_root_is_valid_addr_true(
    switchboard_delta, governance, mission_control, undy_ledger
):
    root = boa.loads(ROOT_REGISTRY_SOURCE, name="g9_root_true")
    root.setAddr(UNDERSCORE_LEDGER_ID, undy_ledger.address)
    root.setValid(ZERO_ADDRESS, True)
    _assert_initiate_rejected(
        switchboard_delta,
        governance,
        mission_control,
        root.address,
        "invalid underscore registry",
    )


def test_g9_delta_rejects_root_is_valid_addr_reverting(
    switchboard_delta, governance, mission_control, undy_ledger
):
    root = boa.loads(ROOT_REVERTING_IS_VALID_ADDR_SOURCE, name="g9_root_reverting")
    root.setAddr(UNDERSCORE_LEDGER_ID, undy_ledger.address)
    _assert_initiate_rejected(
        switchboard_delta,
        governance,
        mission_control,
        root.address,
        "isValidAddr revert",
    )


def test_g9_delta_accepts_empty_optional_slots(
    switchboard_delta, governance, mission_control, conforming_registry
):
    assert conforming_registry.getAddr(UNDERSCORE_VAULT_REGISTRY_ID) == ZERO_ADDRESS
    assert conforming_registry.getAddr(UNDERSCORE_LEGOBOOK_ID) == ZERO_ADDRESS
    aid = switchboard_delta.setUnderscoreRegistry(
        conforming_registry.address, sender=governance.address
    )
    assert _execute(switchboard_delta, governance, aid) is True
    assert mission_control.underscoreRegistry() == conforming_registry.address


def test_g9_delta_rejects_vault_registry_is_earn_vault_true(
    switchboard_delta, governance, mission_control, undy_ledger
):
    root = boa.loads(ROOT_REGISTRY_SOURCE, name="g9_vault_true_root")
    root.setAddr(UNDERSCORE_LEDGER_ID, undy_ledger.address)
    root.setAddr(
        UNDERSCORE_VAULT_REGISTRY_ID,
        boa.loads(ALWAYS_VAULT_REGISTRY_SOURCE, name="g9_always_vault").address,
    )
    _assert_initiate_rejected(
        switchboard_delta,
        governance,
        mission_control,
        root.address,
        "invalid underscore registry",
    )


def test_g9_delta_rejects_vault_registry_is_earn_vault_reverting(
    switchboard_delta, governance, mission_control, undy_ledger
):
    root = boa.loads(ROOT_REGISTRY_SOURCE, name="g9_vault_revert_root")
    root.setAddr(UNDERSCORE_LEDGER_ID, undy_ledger.address)
    root.setAddr(
        UNDERSCORE_VAULT_REGISTRY_ID,
        boa.loads(REVERTING_VAULT_REGISTRY_SOURCE, name="g9_reverting_vault").address,
    )
    _assert_initiate_rejected(
        switchboard_delta,
        governance,
        mission_control,
        root.address,
        "broken vault registry",
    )


def test_g9_delta_accepts_vault_registry_is_earn_vault_false(
    switchboard_delta, governance, mission_control, undy_ledger
):
    root = boa.loads(ROOT_REGISTRY_SOURCE, name="g9_vault_false_root")
    root.setAddr(UNDERSCORE_LEDGER_ID, undy_ledger.address)
    root.setAddr(
        UNDERSCORE_VAULT_REGISTRY_ID,
        boa.loads(HONEST_VAULT_REGISTRY_SOURCE, name="g9_honest_vault").address,
    )
    aid = switchboard_delta.setUnderscoreRegistry(root.address, sender=governance.address)
    assert _execute(switchboard_delta, governance, aid) is True
    assert mission_control.underscoreRegistry() == root.address


def test_g9_delta_rejects_legobook_is_valid_addr_true(
    switchboard_delta, governance, mission_control, undy_ledger
):
    root = boa.loads(ROOT_REGISTRY_SOURCE, name="g9_lego_true_root")
    lego = boa.loads(LEGOBOOK_SOURCE, name="g9_lego_true")
    lego.setValidEmpty(True)
    root.setAddr(UNDERSCORE_LEDGER_ID, undy_ledger.address)
    root.setAddr(UNDERSCORE_LEGOBOOK_ID, lego.address)
    _assert_initiate_rejected(
        switchboard_delta,
        governance,
        mission_control,
        root.address,
        "invalid underscore registry",
    )


def test_g9_delta_rejects_legobook_is_valid_addr_missing(
    switchboard_delta, governance, mission_control, undy_ledger
):
    root = boa.loads(ROOT_REGISTRY_SOURCE, name="g9_lego_missing_root")
    root.setAddr(UNDERSCORE_LEDGER_ID, undy_ledger.address)
    root.setAddr(
        UNDERSCORE_LEGOBOOK_ID,
        boa.loads(MISSING_IS_VALID_ADDR_SOURCE, name="g9_lego_missing").address,
    )
    _assert_initiate_rejected(
        switchboard_delta, governance, mission_control, root.address
    )


def test_g9_delta_rejects_legobook_is_valid_addr_reverting(
    switchboard_delta, governance, mission_control, undy_ledger
):
    root = boa.loads(ROOT_REGISTRY_SOURCE, name="g9_lego_revert_root")
    root.setAddr(UNDERSCORE_LEDGER_ID, undy_ledger.address)
    root.setAddr(
        UNDERSCORE_LEGOBOOK_ID,
        boa.loads(REVERTING_IS_VALID_ADDR_SOURCE, name="g9_lego_reverting").address,
    )
    _assert_initiate_rejected(
        switchboard_delta,
        governance,
        mission_control,
        root.address,
        "isValidAddr revert",
    )


def test_g9_delta_accepts_legobook_is_valid_addr_false(
    switchboard_delta, governance, mission_control, undy_ledger
):
    root = boa.loads(ROOT_REGISTRY_SOURCE, name="g9_lego_false_root")
    lego = boa.loads(LEGOBOOK_SOURCE, name="g9_lego_false")
    root.setAddr(UNDERSCORE_LEDGER_ID, undy_ledger.address)
    root.setAddr(UNDERSCORE_LEGOBOOK_ID, lego.address)
    aid = switchboard_delta.setUnderscoreRegistry(root.address, sender=governance.address)
    assert _execute(switchboard_delta, governance, aid) is True
    assert mission_control.underscoreRegistry() == root.address


def test_g9_delta_rejects_get_addr_vault_registry_reverts(
    switchboard_delta, governance, mission_control, undy_ledger
):
    root = boa.loads(GETADDR_REVERT_ROOT_SOURCE, name="g9_getaddr10_root")
    root.setAddr(UNDERSCORE_LEDGER_ID, undy_ledger.address)
    root.setRevertId(UNDERSCORE_VAULT_REGISTRY_ID)
    _assert_initiate_rejected(
        switchboard_delta,
        governance,
        mission_control,
        root.address,
        "getAddr revert",
    )


def test_g9_delta_rejects_get_addr_legobook_reverts(
    switchboard_delta, governance, mission_control, undy_ledger
):
    root = boa.loads(GETADDR_REVERT_ROOT_SOURCE, name="g9_getaddr3_root")
    root.setAddr(UNDERSCORE_LEDGER_ID, undy_ledger.address)
    root.setRevertId(UNDERSCORE_LEGOBOOK_ID)
    _assert_initiate_rejected(
        switchboard_delta,
        governance,
        mission_control,
        root.address,
        "getAddr revert",
    )


def test_g9_delta_accepts_both_optional_slots_nonempty_and_honest(
    switchboard_delta, governance, mission_control, undy_ledger
):
    root = boa.loads(ROOT_REGISTRY_SOURCE, name="g9_both_slots_root")
    root.setAddr(UNDERSCORE_LEDGER_ID, undy_ledger.address)
    root.setAddr(
        UNDERSCORE_VAULT_REGISTRY_ID,
        boa.loads(HONEST_VAULT_REGISTRY_SOURCE, name="g9_both_honest_vault").address,
    )
    root.setAddr(
        UNDERSCORE_LEGOBOOK_ID,
        boa.loads(LEGOBOOK_SOURCE, name="g9_both_honest_lego").address,
    )
    aid = switchboard_delta.setUnderscoreRegistry(root.address, sender=governance.address)
    assert _execute(switchboard_delta, governance, aid) is True
    assert mission_control.underscoreRegistry() == root.address


def test_g9_mock_undy_empty_guards_and_residual_nonzero_vault_check_revert(
    switchboard_delta, governance, mission_control, teller_utils, mock_undy_v2, bob
):
    assert mock_undy_v2.isValidAddr(ZERO_ADDRESS) is False
    assert mock_undy_v2.isEarnVault(ZERO_ADDRESS) is False
    mock_undy_v2.setVaultCheckRevertAddress(bob)
    with boa.reverts("mock underscore vault check"):
        mock_undy_v2.isEarnVault(bob)

    aid = switchboard_delta.setUnderscoreRegistry(
        mock_undy_v2.address, sender=governance.address
    )
    assert _execute(switchboard_delta, governance, aid) is True
    assert mission_control.underscoreRegistry() == mock_undy_v2.address
    with boa.reverts("mock underscore vault check"):
        teller_utils.isUnderscoreVault(bob)
