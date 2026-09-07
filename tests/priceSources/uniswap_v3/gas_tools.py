"""Pinned Titanoboa 0.2.7 transaction-level coldness recipe and trace helpers."""
from contextlib import contextmanager
import boa


def cold(target, sender=None):
    boa.env.reset_gas_metering_behavior()
    state=boa.env.evm.vm.state
    state.clear_transient_storage()
    # reset_gas_used replaces the access journal. Recreate outstanding Boa/
    # pytest checkpoint IDs with EMPTY access state, so later snapshot rollback
    # remains possible without restoring any warm accounts or slots here.
    checkpoints=list(state._account_db._journal_accessed_state._journal._checkpoint_stack)
    boa.env.reset_gas_used()
    for checkpoint in checkpoints:
        state._account_db._journal_accessed_state.record(checkpoint)
    for address in (sender or boa.env.eoa, getattr(target,'address',target)):
        state.mark_address_warm(bytes.fromhex(str(address)[2:]))
    # The VM's normal precompile rules stay in force. No dependencies are warmed.


def walk(computation):
    yield computation
    for child in computation.children:
        yield from walk(child)


def calls(computation, target):
    address=bytes.fromhex(str(getattr(target,'address',target))[2:])
    return [c for c in walk(computation) if c.msg.code_address==address]


@contextmanager
def storage_reads():
    state=boa.env.evm.vm.state
    original=state.get_storage
    reads=[]
    def record(address,slot,*args,**kwargs):
        reads.append((bytes(address),slot))
        return original(address,slot,*args,**kwargs)
    state.get_storage=record
    try:
        yield reads
    finally:
        state.get_storage=original
