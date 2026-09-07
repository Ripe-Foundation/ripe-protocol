"""Opt-in, bounded-RPC worker. All EVM mutations are local to this process."""
import json
import os
from pathlib import Path
import re
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]

import boa
import boa.rpc
import requests
from eth_abi import decode,encode
from eth_utils import keccak
from boa.interpret import set_cache_dir
from conf_utils import advance_timelock_blocks
from priceSources.uniswap_v3.graph import make_graph,source,params,register,SOURCE
from priceSources.uniswap_v3.compiled import deploy,artifact
from priceSources.uniswap_v3.gas_tools import cold,calls

VECTORS=json.loads((ROOT/'docs/priceSources/uniswap-v3-twap-reference-vectors.json').read_text())
LAB={'minCurrentLiquidity':1,'minHarmonicLiquidity':1,'maxObservationAgeSeconds':3600,'quoteStaleTime':0,'localGraphGlobalQuoteAge':86400}


class InfrastructureError(Exception):
    pass


class HistoricalCallRevert(Exception):
    pass


def configuration(env):
    mode=env.get('RIPE_TWAP_PIN_MODE')
    block=env.get('RIPE_TWAP_BLOCK');block_hash=env.get('RIPE_TWAP_BLOCK_HASH')
    if mode=='fresh':
        if block is not None or block_hash is not None:
            raise ValueError('fresh mode rejects explicit block/hash inputs; unset them')
        rpc=env.get('RIPE_TWAP_RPC_URL')
    elif mode=='pinned':
        if not block or not block_hash or not re.fullmatch('0x[0-9a-fA-F]{64}',block_hash):
            raise ValueError('pinned mode requires both a block and a 32-byte block hash')
        block=int(block,0)
        if block<0:raise ValueError('negative pin')
        rpc=env.get('RIPE_TWAP_ARCHIVE_RPC_URL') or env.get('RIPE_TWAP_RPC_URL')
    else:
        raise ValueError('RIPE_TWAP_PIN_MODE must explicitly be fresh or pinned')
    if not rpc or not rpc.startswith(('https://','http://')):
        raise ValueError('explicit RPC endpoint required')
    return mode,rpc,block,block_hash


class Rpc:
    def __init__(self,url):
        self.url=url;self.session=requests.Session()
    def call(self,method,args):
        for attempt in range(3):
            try:
                response=self.session.post(self.url,json={'jsonrpc':'2.0','id':1,'method':method,'params':args},timeout=(5,15))
                if response.status_code in (429,500,502,503,504) and attempt<2:
                    time.sleep(attempt+1);continue
                if response.status_code!=200:
                    raise InfrastructureError(f'HTTP {response.status_code}')
                data=response.json()
                if 'error' in data:
                    error=data['error']
                    message=str(error.get('message','RPC error'))[:180]
                    if 'http' in message:message='provider RPC error'
                    if method=='eth_call' and (error.get('code')==3 or 'execution reverted' in message.lower()):
                        raise HistoricalCallRevert(message)
                    raise InfrastructureError(f'RPC {error.get("code")}: {message}')
                if 'result' not in data:raise InfrastructureError('missing RPC result')
                return data['result']
            except (requests.RequestException,ValueError) as exc:
                if attempt==2:raise InfrastructureError(type(exc).__name__) from None
                time.sleep(attempt+1)
        raise InfrastructureError('bounded RPC retries exhausted')
    def eth_call(self,address,signature,types,args,block):
        data=keccak(text=signature)[:4]+encode(types,args)
        return self.call('eth_call',[{'to':address,'data':'0x'+data.hex()},hex(block)])


def pin(rpc,mode,block,block_hash):
    if int(rpc.call('eth_chainId',[]),16)!=4663:
        raise ValueError('expected Robinhood chain 4663')
    if mode=='fresh':
        head=int(rpc.call('eth_blockNumber',[]),16)
        if head<32:raise ValueError('head below fresh offset')
        block=head-32
    header=rpc.call('eth_getBlockByNumber',[hex(block),False])
    if not header:raise InfrastructureError('pinned header unavailable')
    if int(header['number'],16)!=block or (block_hash and header['hash'].lower()!=block_hash.lower()):
        raise ValueError('pinned header/hash mismatch')
    return {'block':block,'hash':header['hash'],'timestamp':int(header['timestamp'],16)}


def collect(rpc,a,window,pin,raw=None):
    block=pin['block']
    raw={} if raw is None else raw
    def read(key,address,signature,types=(),args=()):
        raw[key]=rpc.eth_call(address,signature,types,args,block)
        return bytes.fromhex(raw[key][2:])
    read('assetDecimals',a['asset'],'decimals()')
    read('wethDecimals',VECTORS['weth'],'decimals()')
    read('anchorDecimals',VECTORS['anchor']['address'],'decimals()')
    read('round',VECTORS['anchor']['address'],'latestRoundData()')
    for key in ('factory','token0','token1','fee','liquidity'):
        read(key,a['pool'],key+'()')
    slot=decode(['uint160','int24','uint16','uint16','uint16','uint8','bool'],read('slot0',a['pool'],'slot0()'))
    read('observation',a['pool'],'observations(uint256)',['uint256'],[slot[2]])
    try:
        read('observe',a['pool'],'observe(uint32[])',['uint32[]'],[[window,0]])
    except HistoricalCallRevert as exc:
        raw['observe_revert']=str(exc)
    fee=decode(['uint24'],bytes.fromhex(raw['fee'][2:]))[0]
    read('canonicalPool',VECTORS['factory'],'getPool(address,address,uint24)',['address','address','uint24'],[a['asset'],VECTORS['weth'],fee])
    code=rpc.call('eth_getCode',[a['pool'],hex(block)])
    import hashlib
    raw['poolRuntimeSha256']=hashlib.sha256(bytes.fromhex(code[2:])).hexdigest()
    raw['poolRuntimeBytes']=len(bytes.fromhex(code[2:]))
    return raw


def reference_price(raw,a,window,timestamp,ref):
    if 'observe_revert' in raw:return 0
    def decoded(key,types):return decode(types,bytes.fromhex(raw[key][2:]))
    d=decoded('assetDecimals',['uint8'])[0];ad=decoded('anchorDecimals',['uint8'])[0]
    assert d<=18 and ad<=18 and decoded('wethDecimals',['uint8'])[0]==18
    round_id,answer,started,updated,answered=decoded('round',['uint80','int256','uint256','uint256','uint80'])
    sqrt,tick,index,card,card_next,protocol,unlocked=decoded('slot0',['uint160','int24','uint16','uint16','uint16','uint8','bool'])
    ot,oc,ol,initialized=decoded('observation',['uint32','int56','uint160','bool'])
    tc,sc=decoded('observe',['int56[]','uint160[]'])
    assert len(tc)==len(sc)==2
    delta=(tc[1]-tc[0]+2**55)%2**56-2**55
    spl=(sc[1]-sc[0])%2**160
    mean=delta//window
    harmonic=window*(2**160-1)//(spl*2**32) if spl else 0
    valid=(4295128739<=sqrt<1461446703485210103287273052203988822378723970342 and -887272<=tick<=887272 and 0<=index<card<=card_next<=65535 and unlocked and initialized and (timestamp%2**32-ot)%2**32<=3600 and decoded('liquidity',['uint128'])[0]>=1 and 1<=harmonic<=2**128-1 and -887272<=mean<=887272 and round_id>0 and answer>0 and answered>=round_id and 0<updated<=timestamp and timestamp-updated<=86400)
    assert decoded('factory',['address'])[0].lower()==VECTORS['factory'].lower()
    assert decoded('canonicalPool',['address'])[0].lower()==a['pool'].lower()
    tokens=[decoded(k,['address'])[0].lower() for k in ('token0','token1')]
    assert tokens==sorted([a['asset'].lower(),VECTORS['weth'].lower()],key=lambda x:int(x,16))
    if not valid:return 0
    quote=ref.quote(mean,10**d,a['asset'],VECTORS['weth'])
    usd=answer*10**(18-ad)
    result=quote*usd//10**18
    return result if usd<2**256 and result<2**256 else 0


def run():
    mode,url,block,block_hash=configuration(os.environ)
    if cache:=os.environ.get('RIPE_BOA_CACHE_DIR'):set_cache_dir(cache)
    # Prepare local compilation before choosing a fresh header; no deployment.
    for path in (SOURCE,'contracts/registries/RipeHq.vy','contracts/registries/PriceDesk.vy','contracts/registries/Switchboard.vy','contracts/data/MissionControl.vy'):
        boa.load_partial(str(ROOT/path))
    artifact('v3','Reference')
    rpc=Rpc(url);selected=None;results=[]
    cases=[(a,w) for a in VECTORS['assets'] for w in (1800,3600,14400)]
    try:
        selected=pin(rpc,mode,block,block_hash)
        # Explicit historical-state preflight before any expensive graph setup.
        code=rpc.call('eth_getCode',[VECTORS['factory'],hex(selected['block'])])
        if code=='0x':raise InfrastructureError('factory has no code at pin')
        boa.rpc.TIMEOUT=15
        with boa.fork(url,block_identifier=selected['block'],cache_dir=os.environ.get('RIPE_TWAP_FORK_CACHE') or None):
            assert boa.env.timestamp==selected['timestamp']
            g=make_graph()
            ref=deploy('v3','Reference')
            assert boa.env.timestamp==selected['timestamp']
            number=boa.env.evm.patch.block_number
            for a,window in cases:
                case={'asset':a['label'],'window':window,'pin':selected,'laboratory':LAB,'raw':{},'status':'unverified'}
                try:
                    collect(rpc,a,window,selected,case['raw'])
                    expected=reference_price(case['raw'],a,window,selected['timestamp'],ref)
                    case['reference']=expected
                    with boa.env.anchor():
                        s=source(g,VECTORS['factory'],VECTORS['weth'],VECTORS['anchor']['address'])
                        if expected==0:
                            with boa.reverts('invalid feed'):s.addNewPriceFeed(a['asset'],params(a['pool'],window=window),sender=g.gov)
                            case.update(actual=0,status='failed',behavior_passed=True,reason='route unavailable under laboratory guards; admission rejected as expected')
                        else:
                            assert s.addNewPriceFeed(a['asset'],params(a['pool'],window=window),sender=g.gov)
                            advance_timelock_blocks(s.actionTimeLock())
                            assert s.confirmNewPriceFeed(a['asset'],sender=g.gov)
                            register(g.desk,s,g.gov)
                            g.desk.syncTokenScale(a['asset'],sender=g.local)
                            assert g.desk.tokenScale(a['asset'])==10**18
                            assert boa.env.timestamp==selected['timestamp']
                            cold(g.desk)
                            actual=g.desk.getPrice(a['asset'],True)
                            comp=g.desk._computation
                            assert actual==expected
                            assert g.desk.getUsdValue(a['asset'],10**18,True)==expected
                            assert g.desk.getAssetAmount(a['asset'],expected,True)==10**18
                            case.update(actual=actual,status='passed',behavior_passed=True,source_gas=calls(comp,s)[0].get_gas_used(),desk_gas=comp.get_gas_used(),deployed_bytes=len(boa.env.get_code(s.address)),reason='local source and actual desk matched compiled reference at fixed pin')
                except (InfrastructureError,boa.rpc.RPCError,requests.RequestException) as exc:
                    case['reason']=str(exc)[:180] if isinstance(exc,InfrastructureError) else type(exc).__name__
                except Exception as exc:
                    case.update(status='failed',behavior_passed=False,reason=type(exc).__name__)
                case['local_number_at_setup']=number
                case['clock_note']='Boa emulates NUMBER from child header; no claim about live EVM NUMBER'
                results.append(case)
                print('TWAP_FORK_CASE '+json.dumps({k:v for k,v in case.items() if k!='raw'},sort_keys=True),flush=True)
    except (InfrastructureError,boa.rpc.RPCError,requests.RequestException) as exc:
        reason=str(exc)[:180] if isinstance(exc,InfrastructureError) else type(exc).__name__
        results=[{'asset':a['label'],'window':w,'pin':selected,'laboratory':LAB,'status':'unverified','reason':reason,'raw':{}} for a,w in cases]
    consistency='unverified'
    if selected:
        try:
            last=rpc.call('eth_getBlockByNumber',[hex(selected['block']),False])
            consistency='matched' if last and last['hash']==selected['hash'] and int(last['timestamp'],16)==selected['timestamp'] else 'mismatch'
        except InfrastructureError:pass
    if consistency!='matched':
        for case in results:
            case.update(status='unverified',reason='end-header consistency '+consistency+'; '+case.get('reason',''))
    output={'mode':mode,'pin':selected,'header_consistency':consistency,'cases':results}
    if path:=os.environ.get('RIPE_TWAP_FORK_OUTPUT'):
        Path(path).write_text(json.dumps(output,indent=2)+'\n')
    print('TWAP_FORK_RESULT '+json.dumps(output,sort_keys=True),flush=True)
    return 0


if __name__=='__main__':
    try:raise SystemExit(run())
    except ValueError as exc:
        print('TWAP_FORK_CONFIG_ERROR '+str(exc),file=sys.stderr)
        raise SystemExit(2)
