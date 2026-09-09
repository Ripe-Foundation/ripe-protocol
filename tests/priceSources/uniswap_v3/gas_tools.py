"""Pinned Titanoboa 0.2.7 transaction-level coldness recipe and trace helpers."""
from contextlib import contextmanager
import boa
from importlib.metadata import version


def access_checkpoints(state):
    message='TWAP cold reset requires Titanoboa 0.2.7 access-journal layout; review the recipe and rerun the SLOAD control before upgrading'
    if version('titanoboa')!='0.2.7':
        raise RuntimeError(message)
    try:
        journal=state._account_db._journal_accessed_state
        checkpoints=list(journal._journal._checkpoint_stack)
        assert callable(journal.record)
        return checkpoints
    except (AttributeError,TypeError,AssertionError) as exc:
        raise RuntimeError(message) from exc


def cold(target, sender=None):
    boa.env.reset_gas_metering_behavior()
    state=boa.env.evm.vm.state
    checkpoints=access_checkpoints(state)
    state.clear_transient_storage()
    # reset_gas_used replaces the access journal. Recreate outstanding Boa/
    # pytest checkpoint IDs with EMPTY access state, so later snapshot rollback
    # remains possible without restoring any warm accounts or slots here.
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


# Engineering target exceptions must be named, bounded and explained in source.
TARGET_EXCEPTIONS={}  # Future D2 exceptions must name a (bound, reason).

SIZE_TARGET_EXCEPTIONS={}  # Future D2 exceptions must name a (bound, reason).


SOURCE_TARGET=210000
SOURCE_HARD_LIMIT=250000
SIZE_TARGET=22500
SIZE_HARD_LIMIT=24576


def target_overruns(gas=None,size=None):
    """D2 disclosure for live fork measurements; zero means within target."""
    return {key:max(0,value-target) for key,value,target in
            (('source_gas',gas,SOURCE_TARGET),('deployed_bytes',size,SIZE_TARGET)) if value is not None}


def assert_source_hard_limit(gas):
    assert gas<SOURCE_HARD_LIMIT, f'source hard stipend exceeded: {gas}'


def assert_size_hard_limit(size):
    assert size<=SIZE_HARD_LIMIT, f'EIP-170 size exceeded: {size}'


def assert_source_budget(gas, exception=None):
    assert_source_hard_limit(gas)
    limit=SOURCE_TARGET
    if exception is not None:
        assert exception in TARGET_EXCEPTIONS, 'unknown gas target exception'
        limit,reason=TARGET_EXCEPTIONS[exception]
        assert reason.strip() and SOURCE_TARGET<limit<SOURCE_HARD_LIMIT
    assert gas<=limit, f'source engineering target exceeded: {gas} > {limit}; requires an explicit bounded exception'


def assert_deployed_size(size, exception=None):
    assert_size_hard_limit(size)
    limit=SIZE_TARGET
    if exception is not None:
        assert exception in SIZE_TARGET_EXCEPTIONS, 'unknown size target exception'
        limit,reason=SIZE_TARGET_EXCEPTIONS[exception]
        assert reason.strip() and SIZE_TARGET<limit<=SIZE_HARD_LIMIT
    assert size<=limit, f'deployed-size engineering target exceeded: {size} > {limit}'


def dependency_trace(computation):
    """Immediate source calls; gas used includes nested proxy/delegate calls."""
    def item(c):
        used=c.get_gas_used()
        return {'target':'0x'+c.msg.code_address.hex(),
                'selector':'0x'+bytes(c.msg.data[:4]).hex(),
                'gas_forwarded':c.msg.gas,'gas_used':used,
                'gas_headroom':c.msg.gas-used,'failed':c.is_error,
                'return_bytes':len(c.output),'children':[item(d) for d in c.children]}
    return [item(c) for c in computation.children]
