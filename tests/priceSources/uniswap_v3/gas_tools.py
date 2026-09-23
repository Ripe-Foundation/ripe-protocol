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


def mapping_slot(contract, path, key):
    """Vyper mapping layout: keccak(slot || key), with module-qualified path."""
    from eth_utils import keccak
    from .raw import words
    layout=contract.compiler_data.storage_layout['storage_layout']
    for name in path.split('.'):
        layout=layout[name]
    return int.from_bytes(keccak(words(layout['slot'],key)),'big')


def qualification_touch_set(g,source,pool,asset):
    """All standard pre-callback touches also used by the V3 price path.

    Pool metadata reads warm its address, not slot0/liquidity/observations.
    Staging warms all ten feed fields. Scale validation warms the priced
    asset's desk scale and Addys' HQ registry entry 7. Other governance,
    timelock, metadata, loop-check and factory slots are not price inputs.
    HQ entry 5 / MissionControl policy are first read inside the callback.
    """
    return {'addresses':{'source':str(source.address),'pool':str(pool.address),
                         'desk':str(g.desk.address),'RipeHq':str(g.hq.address)},
            'storage':[(str(source.address),slot,'feedConfig[asset].'+name)
                       for name,slot in mapping_struct_slots(source,'feedConfig',asset).items()]
                      +[(str(g.desk.address),mapping_slot(g.desk,'tokenScale',asset),'PriceDesk.tokenScale[asset]'),
                        (str(g.hq.address),mapping_struct_slots(g.hq,'registry.addrInfo',7,('addr',))['addr'],'RipeHq.addrInfo[7].addr')]}


def mapping_struct_slots(contract,path,key,fields=None):
    """Derive member offsets from the pinned compiler's resolved Vyper types."""
    module=contract.compiler_data.annotated_vyper_module._metadata['type']
    parts=path.split('.')
    for name in parts[:-1]:
        module=module.members[name].module_t
    struct=module.variables[parts[-1]].typ.value_type
    offset=mapping_slot(contract,path,key)
    slots={}
    for name,typ in struct.member_types.items():
        # These structs currently have scalar fields. Fail explicitly if their
        # shape changes: the executed-read intersection must be reviewed too.
        if fields is None or name in fields:
            assert typ.storage_size_in_words==1, 'review the TWAP touch-set struct shape'
            slots[name]=offset
        offset+=typ.storage_size_in_words
    assert offset-mapping_slot(contract,path,key)==struct.storage_size_in_words
    return slots



@contextmanager
def qualification_meter(source,touch_set=None,reads=None):
    """Observe the exact two GAS opcodes compiled from _qualifyPriceSource.

    Instrumentation runs outside the EVM and neither changes bytecode nor
    introduces EVM reads. Snapshots include only accesses preceding callback.
    """
    assert not boa.env.evm._fast_mode_enabled
    source_address=bytes.fromhex(str(source.address)[2:])
    pcs={pc for pc,node in source.compiler_data.source_map['pc_raw_ast_map'].items()
         if getattr(node,'node_source_code','')=='msg.gas'
         and source.compiler_data.bytecode_runtime[pc]==0x5a}
    assert len(pcs)==2, 'review the GAS instrumentation after compiler/source changes'
    opcodes=boa.env.evm.vm.state.computation_class.opcodes
    original=opcodes[0x5a]
    readings=[]
    def record(computation):
        pc=computation.code.program_counter-1
        original(computation=computation)
        if computation.msg.code_address==source_address and pc in pcs:
            snapshot={'gas':computation.get_gas_remaining(),'pc':pc,
                      'read_index':len(reads) if reads is not None else None,
                      'called_addresses':{c.msg.code_address for c in walk(computation)},
                      'price_calls':[c.get_gas_used() for c in walk(computation)
                                     if c is not computation and c.msg.code_address==source_address
                                     and bytes(c.msg.data[4:36])==bytes(computation.msg.data[4:36])
                                     and bytes(c.msg.data[:4])==source.getPriceAndHasFeed.prepare_calldata(boa.env.eoa,0,boa.env.eoa)[:4]]}
            if touch_set is not None:
                state=boa.env.evm.vm.state
                snapshot['warm_addresses']={label:state.is_address_warm(bytes.fromhex(address[2:]))
                                            for label,address in touch_set['addresses'].items()}
                snapshot['warm_slots']=[state.is_storage_warm(bytes.fromhex(address[2:]),slot)
                                        for address,slot,label in touch_set['storage']]
            readings.append(snapshot)
    opcodes[0x5a]=record
    try:
        yield readings
    finally:
        opcodes[0x5a]=original


def warm_qualification_ceiling(source):
    """Read the actual compiled source constant; do not mirror it in the harness."""
    for node in source.compiler_data.annotated_vyper_module.body:
        if getattr(getattr(node,'target',None),'id',None)=='MAX_WARM_QUALIFY_GAS':
            return node.value.value
    raise AssertionError('missing admission ceiling')


def qualification_gas(meter):
    """Keep the admission callback and its source child on distinct meters."""
    assert len(meter)==2 and meter[0]['price_calls']==[]
    assert len(meter[1]['price_calls'])==1
    return meter[0]['gas']-meter[1]['gas'],meter[1]['price_calls'][0]
