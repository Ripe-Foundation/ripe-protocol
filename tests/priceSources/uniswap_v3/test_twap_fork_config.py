import pytest
from .fork_worker import configuration


@pytest.mark.parametrize('env',[{}, {'RIPE_TWAP_PIN_MODE':'automatic'}, {'RIPE_TWAP_PIN_MODE':'pinned','RIPE_TWAP_BLOCK':'1'}, {'RIPE_TWAP_PIN_MODE':'pinned','RIPE_TWAP_BLOCK_HASH':'0x'+'ab'*32}, {'RIPE_TWAP_PIN_MODE':'fresh','RIPE_TWAP_BLOCK':'1'}, {'RIPE_TWAP_PIN_MODE':'fresh','RIPE_TWAP_BLOCK_HASH':'0x'+'ab'*32}])
def test_fork_modes_fail_closed_on_incomplete_or_mixed_pins(env):
    with pytest.raises(ValueError):configuration({'RIPE_TWAP_RPC_URL':'https://example.invalid','RIPE_TWAP_FORK_OUTPUT':'inputs.json',**env})


def test_fork_provider_selection_is_explicit():
    base={'RIPE_TWAP_RPC_URL':'https://fresh.invalid','RIPE_TWAP_ARCHIVE_RPC_URL':'https://archive.invalid','RIPE_TWAP_FORK_OUTPUT':'inputs.json'}
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
data['cases'][0].update(status='qualified',behavior_passed=True,header_consistency='matched',stage='asset_conversion',raw={'round':'0x1234'},actual=42,source_gas=12345)
data['cases'][1].update(stage='rpc:round',raw={'assetDecimals':'0x12'})
data['cases'][2].update(status='failed',stage='price',raw={'round':'0x56'},reason='price mismatch',actual=17,reference=18)
atomic_save(path,data)
time.sleep(60)
''')
    path=tmp_path/'inputs.json'
    env={**os.environ,'RIPE_TWAP_FORK_OUTPUT':str(path),'TWAP_TEST_HELPERS':str(Path(__file__).parent)}
    with pytest.raises(RuntimeError,match='did not complete: timeout'):
        run_worker([sys.executable,str(worker)],cwd=tmp_path,env=env,timeout=5,
                   initial=initial_results('pinned',['TEST','WAITING'],{}))
    data=json.loads(path.read_text())
    assert data['stage']=='timeout' and data['pin']['block']==7
    assert data['cases'][0]['status']=='qualified' and data['cases'][0]['source_gas']==12345
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


@pytest.mark.parametrize('fault',['price','usd_conversion','asset_conversion','exception','unavailable','gas_target','size_target','hard_gas','hard_size'])
def test_fork_measurements_survive_mismatch_or_descriptive_failure(tmp_path,monkeypatch,fault):
    import json
    from pathlib import Path
    import boa
    from . import fork_worker as worker
    from .fork_results import atomic_save,failure
    from .compiled import deploy
    from .raw import Raw,Revert
    from eth_abi import encode
    from eth_utils import keccak
    from .graph import make_graph,weth_price_source
    from .fork_inputs import FRESH_FIXTURE
    data=json.loads(FRESH_FIXTURE.read_text())
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
    weth_price_source(g,worker.VECTORS['weth'],worker.VECTORS['anchor']['address'])
    ref=deploy('v3','Reference')
    expected=worker.reference_price(raw,asset,case['window'],data['pin']['timestamp'],ref)
    assert expected>0
    if fault=='price':
        reference=worker.reference_price
        monkeypatch.setattr(worker,'reference_price',lambda *args:reference(*args)+1)
    elif fault in ('usd_conversion','asset_conversion'):
        name='getUsdValue' if fault=='usd_conversion' else 'getAssetAmount'
        original=getattr(g.desk,name)
        monkeypatch.setattr(g.desk,name,lambda *args:original(*args)+1)
    elif fault in ('gas_target','hard_gas'):
        # Inject measured costs at the reporting boundary; actual EVM price and
        # conversions still run. The gas suite separately enforces real caps.
        from types import SimpleNamespace
        original_calls=worker.calls
        def measured_calls(*args):
            return [SimpleNamespace(msg=c.msg,children=c.children,output=c.output,is_error=c.is_error,
                    get_gas_used=lambda:210001 if fault=='gas_target' else 250000) for c in original_calls(*args)]
        monkeypatch.setattr(worker,'calls',measured_calls)
    elif fault in ('size_target','hard_size'):
        monkeypatch.setattr(worker,'deployed_size',lambda s:22501 if fault=='size_target' else 24577)
    elif fault=='exception':
        def rejected(*args):raise RuntimeError('descriptive injected constructor failure')
        monkeypatch.setattr(worker,'source',rejected)
    else:
        case['raw']['observe_revert']='execution reverted: OLD'
        pool.responses['observe(uint32[])']=Revert(keccak(text='Error(string)')[:4]+encode(['string'],['OLD']));pool.install()
    path=tmp_path/'case.json'
    save=lambda:atomic_save(path,case)
    if fault=='unavailable':
        worker.qualify_case(g,ref,asset,case,save)
        assert case['status']=='expected_rejected' and case['behavior_passed']
        assert case['expected_revert']=='OLD'
    else:
        with pytest.raises((AssertionError,RuntimeError)) as caught:
            worker.qualify_case(g,ref,asset,case,save)
        failure(case,caught.value);save()
        assert case['status']=='failed' and not case['behavior_passed']
        if fault in ('hard_gas','hard_size'):
            assert case['stage']==('price' if fault=='hard_gas' else 'constructor')
            assert ('hard stipend' if fault=='hard_gas' else 'EIP-170') in case['reason']
            assert case['target_overrun']['source_gas' if fault=='hard_gas' else 'deployed_bytes']>0
        elif fault in ('gas_target','size_target'):
            assert case['stage']=='price' and 'engineering target exceeded' in case['reason']
            assert case['actual']==case['reference']==expected
            assert case['target_overrun']=={'source_gas':int(fault=='gas_target'),'deployed_bytes':int(fault=='size_target')}
        elif fault=='exception':
            assert case['stage']=='constructor' and 'descriptive injected constructor failure' in case['reason']
        else:
            assert case['stage']==fault
            assert case['actual']==expected and case['source_gas']>0 and case['desk_gas']>0
            assert case['source_calls'][0]['gas_forwarded']==250000
            dependencies=case['source_calls'][0]['dependencies']
            assert dependencies and all(d['gas_forwarded']>=d['gas_used'] for d in dependencies)
            assert all({'target','selector','gas_headroom','failed','return_bytes','children'}<=d.keys() for d in dependencies)
            if fault=='price':assert case['reference']==case['actual']+1
            if fault=='usd_conversion':assert case['usd_value']==case['reference']+1
            if fault=='asset_conversion':assert case['asset_amount']==case['token_scale']+1
    assert json.loads(path.read_text())==case


@pytest.mark.parametrize('output',[None,'','  '])
def test_output_path_is_required_configuration(output):
    env={'RIPE_TWAP_PIN_MODE':'fresh','RIPE_TWAP_RPC_URL':'https://example.invalid'}
    if output is not None:env['RIPE_TWAP_FORK_OUTPUT']=output
    with pytest.raises(ValueError,match='RIPE_TWAP_FORK_OUTPUT is required'):configuration(env)


def test_direct_worker_missing_output_reports_clean_config_error(tmp_path):
    import os,subprocess,sys
    from pathlib import Path
    env={key:value for key,value in os.environ.items() if not key.startswith('RIPE_TWAP_')}
    env.update(RIPE_TWAP_PIN_MODE='fresh',RIPE_TWAP_RPC_URL='https://example.invalid',PYTHONDONTWRITEBYTECODE='1')
    worker=Path(__file__).parent/'fork_worker.py'
    result=subprocess.run([sys.executable,str(worker)],cwd=tmp_path,env=env,text=True,capture_output=True,timeout=30)
    assert result.returncode==2
    assert result.stderr.strip()=='TWAP_FORK_CONFIG_ERROR RIPE_TWAP_FORK_OUTPUT is required'
    assert 'KeyError' not in result.stderr and 'Traceback' not in result.stderr


@pytest.mark.parametrize('configured',[False,True])
def test_requests_connection_errors_redact_host_and_relative_url(configured):
    from .fork_results import sanitized
    message="HTTPSConnectionPool(host='archive.example.invalid', port=443): Max retries exceeded with url: /v2/SECRETKEY123abc?api_key=QUERYSECRET (Caused by NewConnectionError('connection refused'))"
    urls=('https://archive.example.invalid/v2/SECRETKEY123abc?api_key=QUERYSECRET',) if configured else ()
    result=sanitized(message,urls)
    assert 'connection refused' in result
    for secret in ('archive.example.invalid','SECRETKEY123abc','QUERYSECRET','/v2/'):
        assert secret not in result


def test_configured_endpoint_fragments_are_redacted_from_saved_rpc_errors(tmp_path,monkeypatch):
    import json
    import requests
    from types import SimpleNamespace
    from .fork_worker import Rpc,InfrastructureError
    from .fork_results import atomic_save,failure,sanitized
    url='https://archive.example.invalid/v2/SECRETKEY123abc?api_key=QUERYSECRET'
    # Exercise real requests exception handling and finite retries without RPC.
    message="HTTPSConnectionPool(host='archive.example.invalid', port=443): Max retries exceeded with url: /v2/SECRETKEY123abc?api_key=QUERYSECRET (Caused by NewConnectionError('failed to resolve archive.example.invalid at /v2/SECRETKEY123abc'))"
    def disconnected(*args,**kwargs):raise requests.ConnectionError(message)
    rpc=Rpc(url);rpc.session=SimpleNamespace(post=disconnected)
    import sys
    monkeypatch.setattr(sys.modules[Rpc.__module__].time,'sleep',lambda delay:None)
    with pytest.raises(InfrastructureError) as caught:rpc.call('eth_call',[])
    case={'stage':'rpc:round','raw':{}}
    failure(case,caught.value,infrastructure=True,rpc_urls=(url,))
    path=tmp_path/'inputs.json';atomic_save(path,case)
    reported=json.dumps(case)
    assert 'failed to resolve' in case['reason']
    for value in (str(caught.value),path.read_text(),reported,
                  sanitized('unlabelled archive.example.invalid /v2/SECRETKEY123abc api_key=QUERYSECRET',(url,))):
        for secret in ('archive.example.invalid','SECRETKEY123abc','QUERYSECRET','/v2/'):
            assert secret not in value


def test_nonzero_exit_keeps_fatal_stderr_after_verbose_stdout(tmp_path):
    import os,sys
    from .fork_results import run_worker,initial_results
    path=tmp_path/'inputs.json'
    endpoint='https://archive.example.invalid/v2/SECRETKEY123abc'
    env={**os.environ,'RIPE_TWAP_FORK_OUTPUT':str(path),'RIPE_TWAP_ARCHIVE_RPC_URL':endpoint}
    worker=tmp_path/'fatal_worker.py'
    worker.write_text('''import sys
print('verbose case output ' * 1000)
print('trace context ' * 1000, file=sys.stderr)
print("FatalDiagnosticMarker: HTTPSConnectionPool(host='archive.example.invalid'): Max retries exceeded with url: /v2/SECRETKEY123abc",file=sys.stderr)
raise SystemExit(7)
''')
    with pytest.raises(RuntimeError) as caught:
        run_worker([sys.executable,str(worker)],cwd=tmp_path,env=env,
                   initial=initial_results('pinned',['TEST'],{}))
    message=str(caught.value)
    assert 'FatalDiagnosticMarker' in message and 'exited 7' in message
    assert message.index('FatalDiagnosticMarker')<message.index('; stdout:')
    assert 'verbose case output' in message and len(message)<1000
    for secret in ('archive.example.invalid','SECRETKEY123abc','/v2/'):
        assert secret not in message
    assert path.is_file()


def test_empty_timeout_is_incomplete_and_completed_missing_state_stays_unverified(tmp_path,monkeypatch):
    import json,subprocess
    from .fork_results import initial_results,require_complete,run_worker
    path=tmp_path/'inputs.json'
    def timed_out(*args,**kwargs):raise subprocess.TimeoutExpired('test worker',600)
    monkeypatch.setattr(subprocess,'run',timed_out)
    with pytest.raises(RuntimeError,match='did not complete: timeout'):
        run_worker(['test-worker'],cwd=tmp_path,env={'RIPE_TWAP_FORK_OUTPUT':str(path)},
                   initial=initial_results('pinned',['TEST'],{}))
    data=json.loads(path.read_text())
    assert data['stage']=='timeout' and all(c['status']=='unverified' for c in data['cases'])
    data['stage']='complete'
    assert require_complete(data) is data


@pytest.mark.parametrize('missing',['number','hash','timestamp'])
@pytest.mark.parametrize('operation',['pin','check'])
def test_missing_header_fields_are_infrastructure_not_behavior_failure(missing,operation):
    from .fork_worker import pin,check_header,InfrastructureError
    header={'number':'0x7','hash':'0x'+'ab'*32,'timestamp':'0x64'}
    del header[missing]
    class Incomplete:
        def call(self,method,args):return '0x1237' if method=='eth_chainId' else header
    with pytest.raises(InfrastructureError,match='header field'):
        if operation=='pin':pin(Incomplete(),'pinned',7,None)
        else:check_header(Incomplete(),{'block':7,'hash':'0x'+'ab'*32,'timestamp':100})


def test_end_header_downgrade_preserves_first_observed_status_and_reason():
    from .fork_results import downgrade,buckets
    case={'asset':'TEST','window':3600,'status':'expected_rejected','behavior_passed':True,'reason':'invalid feed'}
    downgrade(case,'case header mismatch')
    downgrade(case,'end header missing')
    assert case['status']=='unverified' and not case['behavior_passed']
    assert case['observed_status']=='expected_rejected' and case['observed_reason']=='invalid feed'
    assert buckets({'cases':[case]})=={'qualified':[],'expected_rejected':[],'unverified':['TEST/3600'],'failed':[]}
