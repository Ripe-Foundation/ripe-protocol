import pytest
from .fork_worker import configuration,pin


@pytest.mark.parametrize('env',[{}, {'RIPE_TWAP_PIN_MODE':'automatic'}, {'RIPE_TWAP_PIN_MODE':'pinned','RIPE_TWAP_BLOCK':'1'}, {'RIPE_TWAP_PIN_MODE':'pinned','RIPE_TWAP_BLOCK_HASH':'0x'+'ab'*32}, {'RIPE_TWAP_PIN_MODE':'fresh','RIPE_TWAP_BLOCK':'1'}, {'RIPE_TWAP_PIN_MODE':'fresh','RIPE_TWAP_BLOCK_HASH':'0x'+'ab'*32}])
def test_fork_modes_fail_closed_on_incomplete_or_mixed_pins(env):
    with pytest.raises(ValueError):configuration({'RIPE_TWAP_RPC_URL':'https://example.invalid',**env})


def test_fork_provider_selection_is_explicit():
    base={'RIPE_TWAP_RPC_URL':'https://fresh.invalid','RIPE_TWAP_ARCHIVE_RPC_URL':'https://archive.invalid'}
    assert configuration({**base,'RIPE_TWAP_PIN_MODE':'fresh'})[1]=='https://fresh.invalid'
    pinned={**base,'RIPE_TWAP_PIN_MODE':'pinned','RIPE_TWAP_BLOCK':'57037442','RIPE_TWAP_BLOCK_HASH':'0x'+'ab'*32}
    assert configuration(pinned)[1]=='https://archive.invalid'
    del pinned['RIPE_TWAP_ARCHIVE_RPC_URL']
    assert configuration(pinned)[1]=='https://fresh.invalid'


@pytest.mark.parametrize('error,expected',[({'code':-32000,'message':'metadata is not found'},'infrastructure'),({'code':3,'message':'execution reverted: OLD'},'revert')])
def test_rpc_state_failure_is_distinct_from_real_call_revert(error,expected):
    from types import SimpleNamespace
    from .fork_worker import Rpc,InfrastructureError,HistoricalCallRevert
    rpc=Rpc('https://example.invalid')
    rpc.session=SimpleNamespace(post=lambda *a,**kw:SimpleNamespace(status_code=200,json=lambda:{'error':error}))
    with pytest.raises(InfrastructureError if expected=='infrastructure' else HistoricalCallRevert):
        rpc.call('eth_call',[])


def test_partial_raw_calls_survive_provider_loss():
    from .fork_worker import collect,InfrastructureError,VECTORS
    class LostState:
        def eth_call(self,address,signature,*args):
            if signature=='latestRoundData()':raise InfrastructureError('state pruned')
            return '0x'+(18).to_bytes(32,'big').hex()
    raw={}
    with pytest.raises(InfrastructureError):collect(LostState(),VECTORS['assets'][0],1800,{'block':1},raw)
    assert set(raw)=={'assetDecimals','wethDecimals','anchorDecimals'}


def test_partial_rpc_inputs_are_saved_before_next_read_or_decode(tmp_path):
    import json
    from .fork_worker import collect,InfrastructureError,VECTORS
    from .fork_results import atomic_save
    path=tmp_path/'partial.json';raw={};stages=[]
    class LostState:
        def eth_call(self,address,signature,*args):
            if signature=='latestRoundData()':
                assert set(json.loads(path.read_text()))=={'assetDecimals','wethDecimals','anchorDecimals'}
                raise InfrastructureError('state pruned at round')
            return '0x'+(18).to_bytes(32,'big').hex()
    with pytest.raises(InfrastructureError,match='state pruned at round'):
        collect(LostState(),VECTORS['assets'][0],1800,{'block':1},raw,
                lambda:atomic_save(path,raw),stages.append)
    assert json.loads(path.read_text())==raw
    assert stages[-1]=='rpc:round'


def test_atomic_checkpoint_does_not_damage_previous_save(tmp_path,monkeypatch):
    import json
    from . import fork_results as results
    path=tmp_path/'inputs.json'
    results.atomic_save(path,{'raw':'retained'})
    def interrupted(*args):raise OSError('injected replacement failure')
    monkeypatch.setattr(results.os,'replace',interrupted)
    with pytest.raises(OSError):results.atomic_save(path,{'raw':'new'})
    assert json.loads(path.read_text())=={'raw':'retained'}
    assert list(tmp_path.iterdir())==[path]


def test_real_subprocess_timeout_retains_complete_and_partial_evidence(tmp_path):
    import json,os,sys
    from pathlib import Path
    from .fork_results import run_worker,initial_results
    worker=tmp_path/'slow_worker.py'
    worker.write_text('''import json,os,sys,time
sys.path.insert(0,os.environ['TWAP_TEST_HELPERS'])
from fork_results import atomic_save
path=os.environ['RIPE_TWAP_FORK_OUTPUT']
data=json.load(open(path))
data['pin']={'block':7,'hash':'0x'+'ab'*32,'timestamp':100}
data['cases'][0].update(status='passed',behavior_passed=True,header_consistency='matched',stage='asset_conversion',raw={'round':'0x1234'},actual=42,source_gas=12345)
data['cases'][1].update(stage='rpc:round',raw={'assetDecimals':'0x12'})
data['cases'][2].update(status='failed',stage='price',raw={'round':'0x56'},reason='price mismatch',actual=17,reference=18)
atomic_save(path,data)
time.sleep(60)
''')
    path=tmp_path/'inputs.json'
    env={**os.environ,'RIPE_TWAP_FORK_OUTPUT':str(path),'TWAP_TEST_HELPERS':str(Path(__file__).parent)}
    data=run_worker([sys.executable,str(worker)],cwd=tmp_path,env=env,timeout=2,
                    initial=initial_results('pinned',['TEST','WAITING'],{}))
    assert data['stage']=='timeout' and data['pin']['block']==7
    assert data['cases'][0]['status']=='passed' and data['cases'][0]['source_gas']==12345
    assert data['cases'][0]['raw']=={'round':'0x1234'}
    assert data['cases'][1]['raw']=={'assetDecimals':'0x12'}
    assert data['cases'][1]['status']=='unverified' and 'rpc:round' in data['cases'][1]['reason']
    assert data['cases'][2]['status']=='unverified' and data['cases'][2]['observed_status']=='failed'
    assert data['cases'][2]['actual']==17 and data['cases'][2]['reference']==18
    assert data['cases'][2]['observed_reason']=='price mismatch'
    assert data['cases'][3]['status']=='unverified' and 'pending' in data['cases'][3]['reason']
    assert json.loads(path.read_text())==data


def test_exception_diagnostics_keep_description_and_redact_sensitive_context():
    from .fork_results import failure,exception_reason
    from types import SimpleNamespace
    case={'stage':'confirmation','raw':{'round':'0x01'}}
    failure(case,RuntimeError('oracle rejected; https://user:pass@provider.invalid/v3/secret?key=abc /'+'Users/example/private/key token=secret Bearer secret'))
    assert case['status']=='failed' and case['stage']=='confirmation'
    assert case['raw']=={'round':'0x01'}
    assert 'RuntimeError: oracle rejected' in case['reason']
    for secret in ('user:pass','provider.invalid','secret','/'+'Users/'):assert secret not in case['reason']
    error=RuntimeError('unhelpful full trace')
    error.stack_trace=SimpleNamespace(dev_reason='price source not executable')
    assert exception_reason(error)=='RuntimeError: price source not executable'


@pytest.mark.parametrize('fault',['price','usd_conversion','asset_conversion','exception','unavailable'])
def test_fork_measurements_survive_mismatch_or_descriptive_failure(tmp_path,monkeypatch,fault):
    import json
    from pathlib import Path
    import boa
    from . import fork_worker as worker
    from .fork_results import atomic_save,failure
    from .compiled import deploy
    from .raw import Raw
    from .graph import make_graph
    data=json.loads((Path(__file__).parent/'fixtures/fresh-57185814.json').read_text())
    captured=data['cases'][0]
    case={'asset':captured['asset'],'window':captured['window'],'pin':data['pin'],
          'raw':dict(captured['raw']),'status':'unverified'}
    asset=next(a for a in worker.VECTORS['assets'] if a['label']==case['asset'])
    boa.env.evm.patch.timestamp=data['pin']['timestamp']
    g=make_graph();raw=case['raw']
    def decoded(key):return bytes.fromhex(raw[key][2:])
    Raw({'decimals()':decoded('assetDecimals')},address=asset['asset'])
    Raw({'decimals()':decoded('wethDecimals')},address=worker.VECTORS['weth'])
    Raw({'decimals()':decoded('anchorDecimals'),'latestRoundData()':decoded('round')},address=worker.VECTORS['anchor']['address'])
    Raw({'getPool(address,address,uint24)':decoded('canonicalPool')},address=worker.VECTORS['factory'])
    pool=Raw({**{key+'()':decoded(key) for key in ('factory','token0','token1','fee','liquidity','slot0')},
         'observations(uint256)':decoded('observation'),'observe(uint32[])':decoded('observe')},address=asset['pool'])
    ref=deploy('v3','Reference')
    if fault=='price':
        reference=worker.reference_price
        monkeypatch.setattr(worker,'reference_price',lambda *args:reference(*args)+1)
    elif fault in ('usd_conversion','asset_conversion'):
        name='getUsdValue' if fault=='usd_conversion' else 'getAssetAmount'
        original=getattr(g.desk,name)
        monkeypatch.setattr(g.desk,name,lambda *args:original(*args)+1)
    elif fault=='exception':
        def rejected(*args):raise RuntimeError('descriptive injected constructor failure')
        monkeypatch.setattr(worker,'source',rejected)
    else:
        case['raw']['observe_revert']='execution reverted: OLD'
        del pool.responses['observe(uint32[])'];pool.install()
    path=tmp_path/'case.json'
    save=lambda:atomic_save(path,case)
    if fault=='unavailable':
        worker.qualify_case(g,ref,asset,case,save)
        assert case['status']=='unavailable' and case['behavior_passed']
    else:
        with pytest.raises((AssertionError,RuntimeError)) as caught:
            worker.qualify_case(g,ref,asset,case,save)
        failure(case,caught.value);save()
        assert case['status']=='failed' and not case['behavior_passed']
        if fault=='exception':
            assert case['stage']=='constructor' and 'descriptive injected constructor failure' in case['reason']
        else:
            assert case['stage']==fault
            assert case['actual']==captured['actual'] and case['source_gas']>0 and case['desk_gas']>0
            assert case['source_calls'][0]['gas_forwarded']==250000
            dependencies=case['source_calls'][0]['dependencies']
            assert dependencies and all(d['gas_forwarded']>=d['gas_used'] for d in dependencies)
            assert all({'target','selector','gas_headroom','failed','return_bytes','children'}<=d.keys() for d in dependencies)
            if fault=='price':assert case['reference']==case['actual']+1
            if fault=='usd_conversion':assert case['usd_value']==case['reference']+1
            if fault=='asset_conversion':assert case['asset_amount']==case['token_scale']+1
    assert json.loads(path.read_text())==case
