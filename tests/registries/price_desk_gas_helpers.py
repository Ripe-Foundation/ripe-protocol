"""Cold-state restoration and compiler call-gas observations for focused tests."""
from contextlib import contextmanager

import boa
from eth.vm.gas_meter import GasMeter

from conf_utils import clear_transient_storage


@contextmanager
def cold_trial(*contracts):
    """Restore storage AND transaction warmth, including enclosing Boa anchors.

    Pinned Titanoboa 0.2.7 / py-evm 0.12.1b1: _reset_access_counters replaces
    AccountDB._journal_accessed_state. The enclosing anchor owns checkpoints in
    the previous journal, which must be restored even when the trial raises.
    tests/test_price_desk_gas_helpers.py pins these private-API assumptions.
    """
    state = boa.env.evm.vm.state
    db = state._account_db
    previous_accesses = db._journal_accessed_state
    try:
        boa.env._reset_access_counters()
        clear_transient_storage()
        with boa.env.anchor():
            for contract in contracts:
                address = bytes.fromhex(str(contract.address)[2:])
                assert not state.is_address_warm(address)
                assert not state.is_storage_warm(address, 0)
            yield
    finally:
        db._journal_accessed_state = previous_accesses


def calls_to(computation, contract, selector=None):
    address = bytes.fromhex(str(contract.address)[2:])
    return [child for child in computation.children
            if child.msg.code_address == address
            and (selector is None or bytes(child.msg.data[:4]) == selector)] + [
        found for child in computation.children for found in calls_to(child, contract, selector)
    ]


class CallGasMeter(GasMeter):
    """Observe installed-compiler instructions without modifying contract code."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events = []

    def _set_code(self, code):
        self.code = code

    def consume_gas(self, amount, reason):
        self.events.append((self.code.program_counter - 1, self.gas_remaining, amount, reason))
        super().consume_gas(amount, reason)
