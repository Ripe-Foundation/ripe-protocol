"""Canonical compiled V3 runtime, organic calibration and synthetic ring seeding."""
import hashlib
import boa
from .compiled import artifact, at, deploy

LAYOUT = artifact('v3', 'UniswapV3Pool')['storageLayout']
SLOTS = {x['label']: int(x['slot']) for x in LAYOUT['storage']}


def members(label):
    entry = next(x for x in LAYOUT['storage'] if x['label']==label)
    typ = LAYOUT['types'][entry['type']]
    if 'base' in typ:
        typ = LAYOUT['types'][typ['base']]
    assert int(typ['numberOfBytes'])==32
    return typ['members']


def pack(label, values):
    fields=members(label)
    assert len(fields)==len(values)
    result=0
    for field,value in zip(fields,values):
        assert int(field['slot'])==0
        width=int(LAYOUT['types'][field['type']]['numberOfBytes'])*8
        result |= (int(value) % 2**width) << (field['offset']*8)
    return result


def assert_runtime(pool):
    a=artifact('v3','UniswapV3Pool')['deployedBytecode']
    expected=bytes.fromhex(a['object'].removeprefix('0x'))
    actual=bytearray(boa.env.get_code(pool.address))
    assert len(actual)==len(expected)
    # The pool was deployed by its actual compiled factory. Only solc-listed
    # constructor immutable bindings may differ from the compiled template.
    for refs in a['immutableReferences'].values():
        for ref in refs:
            start,n=ref['start'],ref['length']
            actual[start:start+n]=expected[start:start+n]
    assert bytes(actual)==expected
    return hashlib.sha256(boa.env.get_code(pool.address)).hexdigest()


def organic_pool(g, tick=0, cardinality=8, writes=6, spacing=600):
    token0=boa.load('contracts/mock/MockErc20.vy',g.gov,'Test asset','TST',18,0)
    token1=boa.load('contracts/mock/MockErc20.vy',g.gov,'Test WETH','WETH',18,0)
    token0,token1=sorted([token0,token1],key=lambda t:int(t.address,16))
    factory=deploy('v3','UniswapV3Factory')
    pool=at('v3','UniswapV3Pool',factory.createPool(token0.address,token1.address,10000))
    ref=deploy('v3','Reference')
    pool.initialize(ref.sqrt(tick))
    pool.increaseObservationCardinalityNext(cardinality)
    actor=boa.load('tests/priceSources/uniswap_v3/PoolActor.vy')
    for token in (token0,token1):
        token.mint(actor,10**40,sender=g.gov)
    liquid=10**20
    actor.add(pool.address,liquid)
    for _ in range(writes):
        boa.env.time_travel(seconds=spacing)
        actor.add(pool.address,1)
        actor.remove(pool.address,1)
    assert pool.liquidity()==liquid
    assert_runtime(pool)
    return factory,pool,token0,token1,actor,ref


def seed_ring(pool, cardinality, *, index=None, initialized=None, spacing=4, tick=0, liquid=10**20, age=0, next_cardinality=None):
    """Synthetic constant tick/liquidity history. Actual canonical pool runtime."""
    initialized=cardinality if initialized is None else initialized
    index=(initialized-1) if index is None else index
    next_cardinality=cardinality if next_cardinality is None else next_cardinality
    assert 1<=initialized<=cardinality<=next_cardinality<=65535
    assert 0<=index<cardinality
    assert initialized==cardinality or index==initialized-1
    now=boa.env.timestamp
    oldest=now-age-(initialized-1)*spacing
    oldest_index=(index+1)%cardinality if initialized==cardinality else 0
    observations={}
    step=spacing*2**128//liquid
    for rank in range(initialized):
        i=(oldest_index+rank)%cardinality
        values=((oldest+rank*spacing)%2**32,tick*rank*spacing,step*rank,True)
        observations[i]=values
        boa.env.evm.set_storage(pool.address,SLOTS['observations']+i,pack('observations',values))
    for i in range(initialized,cardinality) if initialized<cardinality else ():
        boa.env.evm.set_storage(pool.address,SLOTS['observations']+i,1)
    sqrt_ratio = 2**96
    if tick:
        ref=deploy('v3','Reference')
        sqrt_ratio=ref.sqrt(tick)
    state=(sqrt_ratio,tick,index,cardinality,next_cardinality,0,True)
    boa.env.evm.set_storage(pool.address,SLOTS['slot0'],pack('slot0',state))
    boa.env.evm.set_storage(pool.address,SLOTS['liquidity'],liquid)
    assert tuple(pool.slot0())==state
    assert tuple(pool.observations(index))==observations[index]
    return dict(cardinality=cardinality,index=index,initialized=initialized,oldest=oldest,spacing=spacing,oldest_index=oldest_index,observations=observations)


def search_indices(ring,window):
    """Independent expected slot set; does not prove actual read order."""
    target=boa.env.timestamp-window
    newest=(ring['oldest']+(ring['initialized']-1)*ring['spacing'])
    if target>=newest:
        return []
    l=(ring['index']+1)%ring['cardinality'];r=l+ring['cardinality']-1
    indices=[]
    for _ in range(32):
        mid=(l+r)//2
        i=mid%ring['cardinality'];indices.append(i)
        obs=ring['observations'].get(i)
        if obs is None:
            l=mid+1;continue
        j=(i+1)%ring['cardinality'];indices.append(j)
        rank=(i-ring['oldest_index'])%ring['cardinality']
        t=ring['oldest']+rank*ring['spacing']
        if t<=target<=t+ring['spacing']:
            return indices
        if target<t:r=mid-1
        else:l=mid+1
    raise AssertionError('binary search did not terminate')
