"""Private-API contract for cold gas trials; dependency drift requires review."""
from importlib.metadata import version

import boa
import pytest

from registries.price_desk_gas_helpers import cold_trial


@pytest.mark.parametrize("raises", (False, True), ids=("normal", "exception"))
def test_cold_trial_restores_enclosing_anchor_journal(raises):
    assert (version("titanoboa"), version("py-evm")) == ("0.2.7", "0.12.1b1"), (
        "Requalify cold_trial private journal assumptions after dependency changes"
    )
    contract = boa.loads("""# @version 0.4.3
value: public(uint256)
@external
def setValue(new_value: uint256):
    self.value = new_value
""")
    state = boa.env.evm.vm.state
    address = bytes.fromhex(str(contract.address)[2:])
    db = state._account_db
    with boa.env.anchor():
        contract.setValue(1)
        db.mark_address_warm(address)
        db.mark_storage_warm(address, 0)
        previous = db._journal_accessed_state

        def trial():
            with cold_trial(contract):
                assert db._journal_accessed_state is not previous
                assert not state.is_address_warm(address)
                assert not state.is_storage_warm(address, 0)
                contract.setValue(2)
                assert contract.value() == 2
                if raises:
                    raise ValueError("trial failure")

        if raises:
            with pytest.raises(ValueError, match="trial failure"):
                trial()
        else:
            trial()
        assert db._journal_accessed_state is previous
        assert state.is_address_warm(address) and state.is_storage_warm(address, 0)
        assert contract.value() == 1
        # Both another nested checkpoint and the enclosing teardown remain valid.
        with boa.env.anchor():
            contract.setValue(3)
            assert contract.value() == 3
        assert contract.value() == 1
    assert contract.value() == 0
