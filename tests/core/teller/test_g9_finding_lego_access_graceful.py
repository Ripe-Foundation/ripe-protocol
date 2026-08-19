# Group 9 — account permissions.
#
# SwitchboardDelta._isValidUnderscoreAddr is an initiate-time sentinel.
# A registry whose vault-registry slot lacks isEarnVault is rejected at
# initiate. An empty vault-registry slot is still skipped, and
# setUndyLegoAccess then returns False.

import boa
import pytest

from constants import ZERO_ADDRESS


UNDERSCORE_LEDGER_ID = 1
UNDERSCORE_VAULT_REGISTRY_ID = 10

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

# A vault registry that exists and answers other calls but has no isEarnVault.
PARTIAL_VAULT_REGISTRY_SOURCE = """
# @version 0.4.3

@view
@external
def isBasicEarnVault(_vaultAddr: address) -> bool:
    return True
"""


@pytest.fixture
def conforming_registry(switchboard_delta, governance, mission_control):
    """Ledger + root isValidAddr(empty) == False; vault slot empty from the start."""
    root = boa.loads(ROOT_REGISTRY_SOURCE, name="g9_graceful_root")
    ledger_mock = boa.loads(UNDY_LEDGER_SOURCE, name="g9_graceful_ledger")
    root.setAddr(UNDERSCORE_LEDGER_ID, ledger_mock.address)

    aid = switchboard_delta.setUnderscoreRegistry(root.address, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_delta.actionTimeLock())
    assert switchboard_delta.executePendingAction(aid, sender=governance.address) is True
    assert mission_control.underscoreRegistry() == root.address
    assert root.getAddr(UNDERSCORE_VAULT_REGISTRY_ID) == ZERO_ADDRESS

    return {"root": root, "ledger": ledger_mock}


def test_g9_adjacent_positive_control_graceful_when_vault_registry_slot_is_empty(
    conforming_registry, teller, teller_utils, mission_control, bob, sally
):
    """Conforming registry, vault slot empty from the start → fail-closed False."""
    assert teller_utils.isUnderscoreWalletOrVault(bob) is False
    assert teller.setUndyLegoAccess(sally, sender=bob) is False
    assert tuple(mission_control.userConfig(bob)) == (False, False, False)


def test_g9_delta_rejects_registry_whose_vault_registry_lacks_is_earn_vault(
    switchboard_delta, governance, mission_control
):
    """Missing isEarnVault on a nonempty slot 10 rejects at initiate."""
    root = boa.loads(ROOT_REGISTRY_SOURCE, name="g9_reject_partial_root")
    ledger_mock = boa.loads(UNDY_LEDGER_SOURCE, name="g9_reject_partial_ledger")
    root.setAddr(UNDERSCORE_LEDGER_ID, ledger_mock.address)
    root.setAddr(
        UNDERSCORE_VAULT_REGISTRY_ID,
        boa.loads(PARTIAL_VAULT_REGISTRY_SOURCE, name="g9_partial_vault_registry").address,
    )

    aid_before = switchboard_delta.actionId()
    mc_before = mission_control.underscoreRegistry()
    with boa.reverts():
        switchboard_delta.setUnderscoreRegistry(root.address, sender=governance.address)
    assert switchboard_delta.actionId() == aid_before
    assert switchboard_delta.pendingUnderscoreRegistry(aid_before) == ZERO_ADDRESS
    assert mission_control.underscoreRegistry() == mc_before
