"""Operator depth agrees with actual canonical swaps across initialized ticks."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from fractions import Fraction

import boa
import pytest

from .compiled import at, deploy
from .graph import make_graph, quote_price_source, source

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


def ranged_pool(tick=0,decimals=(18,18),shape='ranges'):
    g=make_graph()
    tokens=sorted([boa.load('contracts/mock/MockErc20.vy',g.gov,'Depth token','DEP',d,0)
                   for d in decimals],key=lambda t:int(t.address,16))
    a,b=tokens
    factory=deploy('v3','UniswapV3Factory');ref=deploy('v3','Reference')
    actor=boa.load('tests/priceSources/uniswap_v3/PoolActor.vy')
    for token in tokens:token.mint(actor,10**40,sender=g.gov)
    pool=at('v3','UniswapV3Pool',factory.createPool(a.address,b.address,500))
    pool.initialize(depth.sqrt_at_tick(tick))
    pool.increaseObservationCardinalityNext(3601)
    if shape=='gap':
        ranges=[(tick-20,tick+20,10**18),(tick-400,tick-80,2*10**18),(tick+80,tick+400,3*10**18)]
    else:
        unit=1 if shape=='tiny' else 10**18
        ranges=[(-887270,887270,unit),(tick-100,tick+100,2*unit),
                (tick-200,tick-50,3*unit),(tick+50,tick+200,4*unit)]
    for lower,upper,liquidity in ranges:actor.add_range(pool.address,lower,upper,liquidity)
    boa.env.time_travel(seconds=3600)
    actor.add_range(pool.address,tick-10,tick+10,1)
    return SimpleNamespace(g=g,factory=factory,pool=pool,a=a,b=b,actor=actor,ref=ref)


@pytest.mark.parametrize('asset0',[True,False])
@pytest.mark.parametrize('move',[-2,-1,1,2])
@pytest.mark.parametrize('tick,shape',[(0,'ranges'),(-2600,'ranges'),(200000,'tiny'),(-200000,'gap')])
def test_operator_depth_matches_canonical_swap_across_multiple_ranges(asset0,move,tick,shape):
    l=ranged_pool(tick=tick,shape=shape);p=l.pool
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
    if shape=='gap':assert any(c['liquidityAfter']==0 for c in measured['crossings'])


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


@pytest.mark.parametrize('asset0',[True,False])
@pytest.mark.parametrize('tick,decimals',[(-200000,(6,18)),(200000,(18,6)),(-2600,(0,6))])
def test_operator_unequal_decimals_nonzero_spot_usd_matches_rational_quote(asset0,tick,decimals):
    l=ranged_pool(tick=tick,decimals=decimals)
    asset,quote=(l.a,l.b) if asset0 else (l.b,l.a)
    quote_price_source(l.g,quote,123*10**18)
    s=source(l.g,l.factory.address)
    pin=EvmPin([l.pool,l.a,l.b,s,l.g.desk,l.g.hq])
    result=depth.snapshot(pin,str(l.pool.address),str(asset.address),str(s.address))
    spot=Fraction(l.pool.slot0()[0]**2,2**192)
    for row in result['directions']:
        token=l.a if row['zero_for_one'] else l.b
        whole_input=Fraction(row['input_raw'],10**token.decimals())
        quote_per_whole=(spot if asset0 else 1/spot)*Fraction(10**asset.decimals(),10**quote.decimals())
        input_price=123*10**18*(quote_per_whole if token==asset else 1)
        exact=whole_input*input_price
        assert row['input_usd18']==exact.numerator//exact.denominator
    assert pin.verified


@pytest.mark.parametrize('field',['number','hash','timestamp'])
@pytest.mark.parametrize('value',[None,0,True,[],{},'','garbage','0x-1'])
def test_operator_malformed_header_is_normal_cli_failure(monkeypatch,capsys,field,value):
    class Rpc:
        def call(self,method,args):
            if method=='eth_chainId':return '0x1237'
            if method=='eth_blockNumber':return '0x7'
            return {'number':'0x7','hash':'0x'+'ab'*32,'timestamp':'0x64',field:value}
    monkeypatch.setattr(depth,'Rpc',lambda _:Rpc())
    monkeypatch.setattr(depth.sys,'argv',['twap_pool_depth.py','https://example.invalid','0x'+'01'*20,'0x'+'02'*20])
    assert depth.main()==1
    output=capsys.readouterr()
    assert output.out=='' and output.err.startswith('No verified depth snapshot:')
    assert 'Traceback' not in output.err


@pytest.mark.parametrize('value',[None,'',0,42,[],{},'0x','0x1','0xzz','0x'+'00'*8,'0x'+'ff'*32])
def test_operator_malformed_eth_call_result_is_normal_cli_failure(monkeypatch,capsys,value):
    # null, empty, odd-length, non-hex, short and non-canonical-padding payloads;
    # trailing bytes are tolerated by ABI decoding and are not a malformed case
    class Rpc:
        def call(self,method,args):
            if method=='eth_chainId':return '0x1237'
            if method=='eth_blockNumber':return '0x7'
            if method=='eth_getBlockByNumber':return {'number':'0x7','hash':'0x'+'ab'*32,'timestamp':'0x64'}
            assert method=='eth_call' and args[-1]=='0x7'
            return value
    monkeypatch.setattr(depth,'Rpc',lambda _:Rpc())
    monkeypatch.setattr(depth.sys,'argv',['twap_pool_depth.py','https://example.invalid','0x'+'01'*20,'0x'+'02'*20])
    assert depth.main()==1
    output=capsys.readouterr()
    assert output.out=='' and output.err.startswith('No verified depth snapshot: token0()')
    assert 'Traceback' not in output.err


def test_operator_decode_result_accepts_canonical_payloads_only():
    from eth_abi import encode
    word='0x'+encode(['uint256'],[42]).hex()
    assert depth.decode_result(word,('uint256',),'value()')==(42,)
    address='0x'+encode(['address'],['0x'+'01'*20]).hex()
    assert depth.decode_result(address,('address',),'token0()')[0].lower()=='0x'+'01'*20
    for bad in ('0x'+'ff'*32,word[:-2]):
        with pytest.raises(ValueError,match='does not decode'):
            depth.decode_result(bad,('address',),'token0()')


@pytest.mark.parametrize('fault',['missing_history','zero_quote'])
def test_operator_unavailable_inputs_produce_no_depth_estimate(monkeypatch,capsys,fault):
    l=ranged_pool();quote_price_source(l.g,l.b,0 if fault=='zero_quote' else 10**18)
    s=source(l.g,l.factory.address)
    pin=EvmPin([l.pool,l.a,l.b,s,l.g.desk,l.g.hq]);read=pin.read
    def checked_read(address,signature,*args):
        if fault=='missing_history' and signature=='observe(uint32[])':
            raise ValueError('RPC eth_call failed (code 3)')  # actual Rpc translates OLD into this error
        return read(address,signature,*args)
    monkeypatch.setattr(pin,'read',checked_read)
    monkeypatch.setattr(depth,'Pinned',lambda *args:pin)
    monkeypatch.setattr(depth.sys,'argv',['twap_pool_depth.py','https://example.invalid',str(l.pool.address),str(l.a.address),'--source',str(s.address)])
    assert depth.main()==1
    output=capsys.readouterr()
    assert output.out=='' and 'No verified depth snapshot:' in output.err
    assert not pin.verified


@pytest.mark.parametrize('tick,down,expected',[
    (-2571,False,(-2570,True)),(-2570,True,(-2570,True)),(-2570,False,(-2560,True)),
    (-2560,True,(-2560,True)),(-2561,True,(-2570,True)),(-2559,False,(-10,True)),
    (-11,False,(-10,True)),(-10,False,(0,True)),(-1,True,(-10,True)),(0,True,(0,True)),
    (-7681,False,(-5130,False)),(-5121,True,(-7680,False))])
def test_operator_tick_bitmap_negative_word_boundaries(tick,down,expected):
    class Pin:
        def read(self,address,signature,outputs,inputs,args):
            bits={-2:1<<255,-1:1|(1<<255),0:1}
            return (bits.get(args[0],0),)
    assert depth.PoolTicks(Pin(),'pool',10).next(tick,down)==expected


def test_operator_rpc_old_revert_is_a_sanitized_failure():
    rpc=depth.Rpc('https://example.invalid')
    rpc.session=SimpleNamespace(post=lambda *a,**kw:SimpleNamespace(raise_for_status=lambda:None,
        json=lambda:{'error':{'code':3,'message':'execution reverted: OLD'}}))
    with pytest.raises(ValueError,match='RPC eth_call failed'):
        rpc.call('eth_call',[])
