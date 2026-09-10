"""Opt-in, bounded-RPC worker. All EVM mutations are local to this process."""
import hashlib
import subprocess
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
from priceSources.uniswap_v3.graph import make_graph,source,params,register,weth_price_source,SOURCE,CHAINLINK
from priceSources.uniswap_v3.compiled import deploy,artifact
from priceSources.uniswap_v3.gas_tools import cold,calls,dependency_trace,assert_source_hard_limit,assert_size_hard_limit,target_overruns
from priceSources.uniswap_v3.fork_results import atomic_save,initial_results,failure,sanitized,exception_reason,rpc_endpoints,downgrade,buckets

from priceSources.uniswap_v3.fork_inputs import VECTORS,LAB


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
    if not env.get('RIPE_TWAP_FORK_OUTPUT','').strip():
        raise ValueError('RIPE_TWAP_FORK_OUTPUT is required')
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
                    message=sanitized(error.get('message','RPC error'),(self.url,))
                    if method=='eth_call' and (error.get('code')==3 or 'execution reverted' in message.lower()):
                        raise HistoricalCallRevert(message)
                    raise InfrastructureError(f'RPC {error.get("code")}: {message}')
                if 'result' not in data:raise InfrastructureError('missing RPC result')
                return data['result']
            except (requests.RequestException,ValueError) as exc:
                if attempt==2:raise InfrastructureError(exception_reason(exc,(self.url,))) from None
                time.sleep(attempt+1)
        raise InfrastructureError('bounded RPC retries exhausted')
    def eth_call(self,address,signature,types,args,block):
        data=keccak(text=signature)[:4]+encode(types,args)
        return self.call('eth_call',[{'to':address,'data':'0x'+data.hex()},hex(block)])


def header_fields(header):
    try:
        number=int(header['number'],16)
        block_hash=header['hash']
        timestamp=int(header['timestamp'],16)
        if not re.fullmatch('0x[0-9a-fA-F]{64}',block_hash):raise ValueError('invalid hash')
        return number,block_hash,timestamp
    except (KeyError,TypeError,ValueError):
        raise InfrastructureError('missing or malformed block header field') from None


def pin(rpc,mode,block,block_hash):
    if int(rpc.call('eth_chainId',[]),16)!=4663:
        raise ValueError('expected Robinhood chain 4663')
    if mode=='fresh':
        head=int(rpc.call('eth_blockNumber',[]),16)
        if head<32:raise ValueError('head below fresh offset')
        block=head-32
    header=rpc.call('eth_getBlockByNumber',[hex(block),False])
    number,selected_hash,timestamp=header_fields(header)
    if number!=block or (block_hash and selected_hash.lower()!=block_hash.lower()):
        raise ValueError('pinned header/hash mismatch')
    return {'block':block,'hash':selected_hash,'timestamp':timestamp}


def collect(rpc,a,window,pin,raw=None,checkpoint=lambda:None,stage=lambda name:None):
    block=pin['block']
    raw={} if raw is None else raw
    def read(key,address,signature,types=(),args=()):
        stage('rpc:'+key)
        raw[key]=rpc.eth_call(address,signature,types,args,block)
        checkpoint()  # Persist even if decoding the just-received bytes fails.
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
        raw['observe_revert']=exception_reason(exc,(getattr(rpc,'url',''),))
        checkpoint()
    fee=decode(['uint24'],bytes.fromhex(raw['fee'][2:]))[0]
    read('canonicalPool',VECTORS['factory'],'getPool(address,address,uint24)',['address','address','uint24'],[a['asset'],VECTORS['weth'],fee])
    stage('rpc:poolRuntime')
    code=rpc.call('eth_getCode',[a['pool'],hex(block)])
    import hashlib
    raw['poolRuntimeSha256']=hashlib.sha256(bytes.fromhex(code[2:])).hexdigest()
    raw['poolRuntimeBytes']=len(bytes.fromhex(code[2:]))
    checkpoint()
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
    floor=(harmonic*LAB['minLiquidityRatio']+9999)//10000
    valid=(4295128739<=sqrt<1461446703485210103287273052203988822378723970342 and -887272<=tick<=887272 and 0<=index<card<=card_next<=65535 and unlocked and initialized and card>=window+1 and 0<LAB['maxObservationAge']<=window and (timestamp%2**32-ot)%2**32<=LAB['maxObservationAge'] and decoded('liquidity',['uint128'])[0]>=floor>0 and 1<=harmonic<=2**128-1 and -887272<=mean<=887272 and round_id>0 and answer>0 and answered>=round_id and 0<updated<=timestamp and timestamp-updated<=86400)
    assert decoded('factory',['address'])[0].lower()==VECTORS['factory'].lower()
    assert decoded('canonicalPool',['address'])[0].lower()==a['pool'].lower()
    tokens=[decoded(k,['address'])[0].lower() for k in ('token0','token1')]
    assert tokens==sorted([a['asset'].lower(),VECTORS['weth'].lower()],key=lambda x:int(x,16))
    if not valid:return 0
    quote=ref.quote(mean,10**d*10**18,a['asset'],VECTORS['weth'])
    usd=answer*10**(18-ad)
    result=quote*usd//10**36
    return result if usd<2**256 and result<2**256 else 0


def check_header(rpc,selected):
    last=rpc.call('eth_getBlockByNumber',[hex(selected['block']),False])
    number,block_hash,timestamp=header_fields(last)
    return 'matched' if number==selected['block'] and block_hash.lower()==selected['hash'].lower() and timestamp==selected['timestamp'] else 'mismatch'


def deployed_size(contract):
    return len(boa.env.get_code(contract.address))


def qualify_case(g,ref,a,case,checkpoint):
    """Measure before asserting, so mismatches remain independently reviewable."""
    def stage(name):
        case['stage']=name
        checkpoint()
    selected=case['pin'];window=case['window']
    stage('reference')
    expected=reference_price(case['raw'],a,window,selected['timestamp'],ref)
    case['reference']=expected
    checkpoint()
    with boa.env.anchor():
        stage('constructor')
        s=source(g,VECTORS['factory'])
        case['deployed_bytes']=deployed_size(s)
        case['target_overrun']=target_overruns(size=case['deployed_bytes'])
        checkpoint()
        assert_size_hard_limit(case['deployed_bytes'])
        stage('proposal')
        if expected==0:
            reason='invalid feed'
            if 'observe_revert' in case['raw']:
                assert re.search(r'\bOLD\b',case['raw']['observe_revert']), 'unexpected observe revert'
                reason='OLD'
            case['expected_revert']=reason
            with boa.reverts(reason):
                s.addNewPriceFeed(a['asset'],*params(a['pool'],window=window),sender=g.gov)
            case.update(status='expected_rejected',behavior_passed=True,
                        reason='fixed-WETH laboratory admission rejected as expected: '+reason)
            checkpoint()
            return
        assert s.addNewPriceFeed(a['asset'],*params(a['pool'],window=window),sender=g.gov)
        stage('confirmation')
        advance_timelock_blocks(s.actionTimeLock())
        assert s.confirmNewPriceFeed(a['asset'],sender=g.gov)
        stage('registration')
        register(g.desk,s,g.gov)
        g.desk.syncTokenScale(a['asset'],sender=g.local)
        scale=g.desk.tokenScale(a['asset'])
        case['token_scale']=scale
        checkpoint()
        assert scale==10**decode(['uint8'],bytes.fromhex(case['raw']['assetDecimals'][2:]))[0], 'asset scale mismatch'
        assert boa.env.timestamp==selected['timestamp'], 'local timestamp drift'
        stage('price')
        cold(g.desk)
        case['actual']=g.desk.getPrice(a['asset'])
        comp=g.desk._computation
        children=calls(comp,s)
        case['desk_gas']=comp.get_gas_used()
        case['source_calls']=[{'gas_forwarded':c.msg.gas,'gas_used':c.get_gas_used(),
                               'failed':c.is_error,'output':'0x'+c.output.hex(),
                               'dependencies':dependency_trace(c)} for c in children]
        if len(children)==1:
            case['source_gas']=children[0].get_gas_used()
            case['target_overrun']=target_overruns(gas=case['source_gas'],size=case['deployed_bytes'])
        checkpoint()
        assert case['actual']==expected, 'price mismatch against compiled reference'
        assert len(children)==1 and children[0].msg.gas==250000, 'unexpected source call stipend/count'
        assert_source_hard_limit(case['source_gas'])
        assert not any(case['target_overrun'].values()), 'engineering target exceeded'
        stage('usd_conversion')
        case['usd_value']=g.desk.getUsdValue(a['asset'],scale,True)
        checkpoint()
        assert case['usd_value']==expected, 'USD conversion mismatch'
        stage('asset_conversion')
        case['asset_amount']=g.desk.getAssetAmount(a['asset'],expected,True)
        checkpoint()
        assert case['asset_amount']==scale, 'asset conversion mismatch'
        case.update(status='qualified',behavior_passed=True,
                    reason='local source and actual desk matched compiled reference at fixed pin')
        checkpoint()


def run():
    mode,url,block,block_hash=configuration(os.environ)
    urls=rpc_endpoints(os.environ)
    path=os.environ['RIPE_TWAP_FORK_OUTPUT']
    output=initial_results(mode,[a['label'] for a in VECTORS['assets']],LAB)
    output['code_revision']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    from priceSources.uniswap_v3.fork_provenance import source_identity
    output.update(source_identity())
    output['laboratory']=LAB
    output['capture_worktree_dirty']=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    output['model']='fixed-WETH laboratory; local RipeHq/PriceDesk/ChainlinkPrices; pinned live pool and ETH/USD anchor'
    def save():atomic_save(path,output)
    def stage(name):
        output['stage']=name
        save()
    save()
    if cache:=os.environ.get('RIPE_BOA_CACHE_DIR'):set_cache_dir(cache)
    rpc=Rpc(url);selected=None
    infrastructure=(InfrastructureError,boa.rpc.RPCError,requests.RequestException)
    try:
        stage('compilation')
        # Compile before selecting a fresh pin, without any deployments.
        for contract in (SOURCE,CHAINLINK,'contracts/registries/RipeHq.vy','contracts/registries/PriceDesk.vy','contracts/registries/Switchboard.vy','contracts/data/MissionControl.vy'):
            boa.load_partial(str(ROOT/contract))
        artifact('v3','Reference')
        stage('pin')
        selected=pin(rpc,mode,block,block_hash)
        output['pin']=selected
        for case in output['cases']:case['pin']=selected
        save()
        stage('historical_state')
        code=rpc.call('eth_getCode',[VECTORS['factory'],hex(selected['block'])])
        if code=='0x':raise InfrastructureError('factory has no code at pin')
        stage('local_graph')
        boa.rpc.TIMEOUT=15
        with boa.fork(url,block_identifier=selected['block'],cache_dir=os.environ.get('RIPE_TWAP_FORK_CACHE') or None):
            assert boa.env.timestamp==selected['timestamp'], 'fork timestamp mismatch'
            g=make_graph();ref=deploy('v3','Reference')
            # WETH is priced through a real ChainlinkPrices source bound to the live ETH/USD anchor
            weth_price_source(g,VECTORS['weth'],VECTORS['anchor']['address'])
            assert boa.env.timestamp==selected['timestamp'], 'graph timestamp drift'
            number=boa.env.evm.patch.block_number
            stage('cases')
            for case in output['cases']:
                a=next(a for a in VECTORS['assets'] if a['label']==case['asset'])
                case['local_number_at_setup']=number
                case['clock_note']='Boa emulates NUMBER from child header; no claim about live EVM NUMBER'
                def case_stage(name):
                    case['stage']=name
                    save()
                try:
                    collect(rpc,a,case['window'],selected,case['raw'],save,case_stage)
                    qualify_case(g,ref,a,case,save)
                except infrastructure as exc:
                    failure(case,exc,infrastructure=True,rpc_urls=urls)
                except Exception as exc:
                    failure(case,exc,rpc_urls=urls)
                save()
                # Each completed measurement has its own post-read header check,
                # so a later process timeout need not discard verified cases.
                try:
                    case['header_consistency']=check_header(rpc,selected)
                except infrastructure as exc:
                    case['header_consistency']='unverified'
                    case['header_reason']=exception_reason(exc,urls)
                if case['header_consistency']!='matched':
                    downgrade(case,'case header consistency '+case['header_consistency'])
                save()
                print('TWAP_FORK_CASE '+json.dumps({k:v for k,v in case.items() if k!='raw'},sort_keys=True),flush=True)
    except infrastructure as exc:
        for case in output['cases']:
            if case['stage']=='pending':
                case['stage']=output['stage']
                failure(case,exc,infrastructure=True,rpc_urls=urls)
        save()
    stage('end_header')
    if selected:
        try:output['header_consistency']=check_header(rpc,selected)
        except infrastructure as exc:output['header_reason']=exception_reason(exc,urls)
    if output['header_consistency']!='matched':
        for case in output['cases']:
            downgrade(case,'end-header consistency '+output['header_consistency'])
    output['buckets']=buckets(output)
    stage('complete')
    print('TWAP_FORK_RESULT '+json.dumps(output,sort_keys=True),flush=True)
    return 0


if __name__=='__main__':
    try:raise SystemExit(run())
    except ValueError as exc:
        print('TWAP_FORK_CONFIG_ERROR '+sanitized(exc,rpc_endpoints(os.environ)),file=sys.stderr)
        raise SystemExit(2)
