"""Operator depth agrees with actual canonical swaps across initialized ticks."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import boa
import pytest

from .compiled import at, deploy
from .graph import make_graph, quote_price_source, source
from .pools import organic_pool

spec = importlib.util.spec_from_file_location('twap_pool_depth', Path(__file__).resolve().parents[3]/'scripts/twap_pool_depth.py')
depth = importlib.util.module_from_spec(spec)
spec.loader.exec_module(depth)


class EvmPin:
    def __init__(self, contracts):
        self.contracts = {str(c.address).lower(): c for c in contracts}
        self.block, self.timestamp, self.chain_id = boa.env.evm.patch.block_number, boa.env.timestamp, 4663
        self.header = {'hash': '0x'+'ab'*32}
        self.verified = False

    def read(self, address, signature, outputs, inputs=(), args=()):
        value = getattr(self.contracts[str(address).lower()], signature.split('(')[0])(*args)
        return (value,) if len(outputs)==1 else tuple(value)

    def verify(self):
        self.verified = True


def ranged_pool():
    g=make_graph()
    factory,_,a,b,actor,ref=organic_pool(g)
    pool=at('v3','UniswapV3Pool',factory.createPool(a.address,b.address,500))
    pool.initialize(depth.Q96)
    pool.increaseObservationCardinalityNext(3601)
    for lower,upper,liquidity in [(-887270,887270,10**18),(-100,100,2*10**18),(-200,-50,3*10**18),(50,200,4*10**18)]:
        actor.add_range(pool.address,lower,upper,liquidity)
    boa.env.time_travel(seconds=3600)
    actor.add_range(pool.address,-100,100,1)
    return SimpleNamespace(g=g,factory=factory,pool=pool,a=a,b=b,actor=actor,ref=ref)


@pytest.mark.parametrize('asset0',[True,False])
@pytest.mark.parametrize('move',[-2,-1,1,2])
def test_operator_depth_matches_canonical_swap_across_multiple_ranges(asset0,move):
    l=ranged_pool();p=l.pool
    target=depth.spot_target(p.slot0()[0],asset0,move)
    ticks=depth.PoolTicks(EvmPin([p]),str(p.address),p.tickSpacing())
    measured=depth.walk_depth(p.slot0()[0],p.slot0()[1],p.liquidity(),target,p.fee(),ticks)
    before=[t.balanceOf(l.actor) for t in (l.a,l.b)]
    l.actor.move(p.address,measured['zero_for_one'],target)
    after=[t.balanceOf(l.actor) for t in (l.a,l.b)]
    paid=[x-y for x,y in zip(before,after)]
    assert measured['input_raw']==max(paid)
    assert measured['output_raw']==-min(paid)
    assert p.slot0()[0]==target and measured['crossings']
    # At least one of these ranges starts/ends on either side of initial spot.
    assert any(c['liquidityAfter']!=3*10**18+1 for c in measured['crossings'])


@pytest.mark.parametrize('tick',[-887272,-400000,-200,-1,0,1,200,400000,887272])
def test_operator_tick_boundary_matches_compiled_reference(tick):
    assert depth.sqrt_at_tick(tick)==deploy('v3','Reference').sqrt(tick)


@pytest.mark.parametrize('asset0',[True,False])
def test_operator_snapshot_reads_source_defaults_and_live_desk_quote(asset0):
    l=ranged_pool();asset=l.a if asset0 else l.b;quote=l.b if asset0 else l.a
    quote_price_source(l.g,quote,123*10**18)
    s=source(l.g,l.factory.address)
    s.setFeedDefaults(1800,900,2500,sender=l.g.gov)
    pin=EvmPin([l.pool,l.a,l.b,s,l.g.desk,l.g.hq])
    result=depth.snapshot(pin,str(l.pool.address),str(asset.address),str(s.address))
    assert pin.verified and result['fee_inclusive']
    assert result['window']==1800 and result['max_observation_age']==900 and result['ratio_bps']==2500
    assert result['proposal_min_liquidity']==(result['harmonic_liquidity']*2500+9999)//10000
    assert result['quote_price_usd18']==123*10**18
    assert len(result['directions'])==4
    for row in result['directions']:
        assert row['input_usd18']==row['input_raw']*123 # tick zero, both decimals18
    assert result['label']==f'market depth snapshot at block {pin.block}; not a TWAP manipulation cost'


def test_operator_pin_uses_one_block_and_rejects_reorg():
    from eth_abi import encode
    class FakeRpc:
        def __init__(self):self.calls=[];self.changed=False
        def call(self,method,args):
            self.calls.append((method,args))
            if method=='eth_chainId':return '0x1237'
            if method=='eth_blockNumber':return '0x7'
            if method=='eth_getBlockByNumber':return {'number':'0x7','hash':'0x'+('cd' if self.changed else 'ab')*32,'timestamp':'0x64'}
            assert method=='eth_call' and args[-1]=='0x7'
            return '0x'+encode(['uint256'],[42]).hex()
    rpc=FakeRpc();pin=depth.Pinned(rpc)
    assert pin.read('0x'+'01'*20,'value()',('uint256',))==(42,)
    pin.verify();rpc.changed=True
    with pytest.raises(ValueError,match='header changed'):pin.verify()
    assert sum(method=='eth_blockNumber' for method,_ in rpc.calls)==1
