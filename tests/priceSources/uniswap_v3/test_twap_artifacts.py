"""Offline provenance and the source's required ABI boundaries."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]


def test_upstream_lock_covers_every_vendored_byte():
    lock=json.loads((ROOT/'docs/priceSources/uniswap-v3-twap-upstream-lock.json').read_text())
    dependencies=lock['reference_dependencies']
    actual={str(p.relative_to(ROOT)) for p in (ROOT/'tests/priceSources/uniswap_v3/reference').rglob('*') if p.is_file() and 'vendor' in p.parts and not {'out','cache'} & set(p.parts)}
    assert {d['path'] for d in dependencies}==actual
    for d in dependencies:
        assert hashlib.sha256((ROOT/d['path']).read_bytes()).hexdigest()==d['sha256']
        assert any(pin in d['url'] for pin in (lock['v3_core_commit'],lock['v3_periphery_commit'],lock['v4_core_commit']))


def test_exported_source_overloads_events_and_internal_module_boundary():
    from scripts.export_abis import NON_STANDALONE_VYPER_SOURCES,_compile_abi
    source=ROOT/'contracts/priceSources/UniswapV3TwapPrices.vy'
    path=ROOT/'scripts/abis/UniswapV3TwapPrices.json'
    assert path.read_bytes()==_compile_abi(source,ROOT/'contracts')
    entries=json.loads(path.read_text())
    expected={('address',),('address','uint256'),('address','uint256','address')}
    for method in ('getPrice','getPriceAndHasFeed'):
        assert {tuple(i['type'] for i in e['inputs']) for e in entries if e.get('name')==method}==expected
    feed=[('asset','address',True),('pool','address',True)]
    pending=[('confirmationBlock','uint256',False),('actionId','uint256',False)]
    quote=[('quoteAsset','address',False),('twapWindow','uint32',False),('maxObservationAge','uint32',False),('minLiquidity','uint128',False)]
    base=[('baseLiquidity','uint128',False)]
    prev=[('prevPool','address',True)]
    events={'NewUniV3FeedPending':feed+quote+base+pending,'NewUniV3FeedAdded':feed+quote,'NewUniV3FeedCancelled':feed,
            'UniV3FeedUpdatePending':feed+prev+quote+base+pending,'UniV3FeedUpdated':feed+prev+quote,'UniV3FeedUpdateCancelled':feed+prev,
            'DisableUniV3FeedPending':feed+pending,'UniV3FeedDisabled':feed,'DisableUniV3FeedCancelled':feed,
            'FeedDefaultsSet':[('twapWindow','uint32',False),('maxObservationAge','uint32',False),('minLiquidityRatio','uint256',False)]}
    for name,fields in events.items():
        event=next(e for e in entries if e.get('name')==name)
        assert event=={'name':name,'type':'event','anonymous':False,
                       'inputs':[{'name':n,'type':t,'indexed':i} for n,t,i in fields]}
    proposal={('address','address'),('address','address','uint32'),('address','address','uint32','uint32')}
    for method in ('addNewPriceFeed','updatePriceFeed','isValidNewFeed','isValidUpdateFeed'):
        assert {tuple(i['type'] for i in e['inputs']) for e in entries if e.get('name')==method}==proposal
    assert {tuple(i['type'] for i in e['inputs']) for e in entries if e.get('name')=='setFeedDefaults'}=={('uint32','uint32','uint256')}
    assert {tuple(i['type'] for i in e['inputs']) for e in entries if e.get('name')=='getPoolLiquidity'}=={('address',),('address','uint32')}
    assert 'priceSources/modules/UniswapV3TwapMath.vy' in NON_STANDALONE_VYPER_SOURCES
    assert not (path.parent/'UniswapV3TwapMath.json').exists()


def test_engineering_targets_require_explicit_bounded_exceptions(monkeypatch):
    import pytest
    from .gas_tools import assert_source_budget,assert_deployed_size,SIZE_TARGET_EXCEPTIONS,TARGET_EXCEPTIONS
    with pytest.raises(AssertionError):assert_deployed_size(22501,exception='silent waiver')
    monkeypatch.setitem(SIZE_TARGET_EXCEPTIONS,'test_only',(23000,'Test-only deliberate exception'))
    assert_deployed_size(23000,exception='test_only')
    with pytest.raises(AssertionError):assert_deployed_size(23001,exception='test_only')
    with pytest.raises(AssertionError):assert_deployed_size(24577,exception='test_only')
    assert_source_budget(210000)
    assert_deployed_size(22500)
    with pytest.raises(AssertionError,match='engineering target'):assert_source_budget(210001)
    with pytest.raises(AssertionError,match='engineering target'):assert_deployed_size(22501)
    monkeypatch.setitem(TARGET_EXCEPTIONS,'test_only',(235000,'Test-only deliberate exception'))
    assert_source_budget(230000,exception='test_only')
    with pytest.raises(AssertionError):assert_source_budget(235001,exception='test_only')
    with pytest.raises(AssertionError):assert_source_budget(250000,exception='test_only')
    with pytest.raises(AssertionError):assert_source_budget(210001,exception='silent waiver')


def test_cold_recipe_rejects_incompatible_boa_version_or_journal(monkeypatch):
    import pytest
    from types import SimpleNamespace
    from . import gas_tools
    with pytest.raises(RuntimeError,match='review the recipe'):
        gas_tools.access_checkpoints(SimpleNamespace())
    monkeypatch.setattr(gas_tools,'version',lambda name:'future-version')
    with pytest.raises(RuntimeError,match='review the recipe'):
        gas_tools.access_checkpoints(SimpleNamespace())


def test_fresh_fixture_attests_current_contract_worker_and_laboratory():
    from .fork_inputs import FRESH_FIXTURE
    from .fork_provenance import assert_current_identity
    assert_current_identity(json.loads(FRESH_FIXTURE.read_text()))


def test_fixture_identity_rejects_changed_source_or_lab_and_ignores_pointer(monkeypatch):
    import copy
    import pytest
    from . import fork_inputs
    from .fork_provenance import source_identity,assert_current_identity,laboratory_hash
    good={**source_identity(),'laboratory':fork_inputs.LAB}
    assert_current_identity(good)
    for path in ('contracts/priceSources/UniswapV3TwapPrices.vy',
                 'contracts/priceSources/modules/UniswapV3TwapMath.vy',
                 'tests/priceSources/uniswap_v3/fork_worker.py'):
        bad=copy.deepcopy(good);bad['code_sha256'][path]='0'*64
        with pytest.raises(AssertionError,match='code_sha256'):assert_current_identity(bad)
    bad=copy.deepcopy(good);bad['laboratory_sha256']='0'*64
    with pytest.raises(AssertionError,match='laboratory_sha256'):assert_current_identity(bad)
    assert laboratory_hash({**fork_inputs.LAB,'twapWindow':1800})!=good['laboratory_sha256']
    monkeypatch.setattr(fork_inputs,'FRESH_FIXTURE',Path('a-different-filename.json'))
    assert source_identity()=={k:good[k] for k in ('code_sha256','laboratory_sha256')}


def test_reviewed_head_fork_archive_matches_recorded_git_sources():
    import subprocess
    path=ROOT/'docs/priceSources/evidence/uniswap-v3-twap/fresh-11d3bd30.json'
    data=json.loads(path.read_text())
    assert data['code_revision']=='11d3bd30d6a51d98c0d8eb5052a672c8c5a8aa51'
    for source,expected in data['code_sha256'].items():
        original=subprocess.check_output(['git','show',data['code_revision']+':'+source],cwd=ROOT)
        assert hashlib.sha256(original).hexdigest()==expected
    assert data['header_consistency']=='matched'
    assert {k:len(v) for k,v in data['buckets'].items()}=={'qualified':10,'expected_rejected':2,'unverified':0,'failed':0}


def test_archived_evidence_bytes_match_manifest():
    folder=ROOT/'docs/priceSources/evidence/uniswap-v3-twap'
    manifest=json.loads((folder/'sha256.json').read_text())
    assert {p.name for p in folder.iterdir() if p.is_file() and p.name not in ('README.md','sha256.json')}==set(manifest)
    for filename,digest in manifest.items():
        assert hashlib.sha256((folder/filename).read_bytes()).hexdigest()==digest


def test_pr_fork_attachment_roundtrips_exact_bytes_and_rejects_tampering():
    import pytest
    from scripts.twap_fork_evidence import pack,unpack
    raw=(ROOT/'docs/priceSources/evidence/uniswap-v3-twap/fresh-11d3bd30.json').read_bytes()
    report='PR introduction\n'+pack(raw)+'\nPR conclusions'
    assert unpack(report)==raw
    assert pack(raw)==pack(raw)
    with pytest.raises(ValueError,match='digest mismatch'):
        unpack(report.replace(hashlib.sha256(raw).hexdigest(),'0'*64))
    with pytest.raises(ValueError,match='missing fork evidence'):
        unpack('No attachment')
    incomplete=json.loads(raw);incomplete['cases'][0]['status']='unverified'
    with pytest.raises(ValueError,match='verified outcomes'):
        pack(json.dumps(incomplete).encode())
