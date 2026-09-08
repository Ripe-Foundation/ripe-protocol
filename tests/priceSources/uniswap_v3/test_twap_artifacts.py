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
    common=[('asset','address',True),('actionId','uint256',True),('kind','uint256',False)]
    configuration=[('confirmationBlock','uint256',False),('expirationBlock','uint256',False),
        ('pool','address',False),('twapWindowSeconds','uint32',False),
        ('minCurrentLiquidity','uint128',False),('minHarmonicLiquidity','uint128',False),
        ('maxObservationAgeSeconds','uint32',False),('quoteStaleTime','uint256',False),
        ('assetIsToken0','bool',False),('assetDecimals','uint8',False),('fee','uint24',False)]
    for name in ('UniV3FeedProposed','UniV3FeedConfirmed','UniV3FeedCancelled'):
        event=next(e for e in entries if e.get('name')==name)
        fields=common+([] if name=='UniV3FeedCancelled' else configuration)
        assert event=={'name':name,'type':'event','anonymous':False,
                       'inputs':[{'name':n,'type':t,'indexed':i} for n,t,i in fields]}
    assert 'priceSources/modules/UniswapV3TwapMath.vy' in NON_STANDALONE_VYPER_SOURCES
    assert not (path.parent/'UniswapV3TwapMath.json').exists()


def test_engineering_targets_require_explicit_bounded_exceptions(monkeypatch):
    import pytest
    from .gas_tools import assert_source_budget,assert_deployed_size,SIZE_TARGET_EXCEPTIONS
    with pytest.raises(AssertionError):assert_deployed_size(22501,exception='silent waiver')
    monkeypatch.setitem(SIZE_TARGET_EXCEPTIONS,'test_only',(23000,'Test-only deliberate exception'))
    assert_deployed_size(23000,exception='test_only')
    with pytest.raises(AssertionError):assert_deployed_size(23001,exception='test_only')
    with pytest.raises(AssertionError):assert_deployed_size(24577,exception='test_only')
    assert_source_budget(210000)
    assert_deployed_size(22500)
    with pytest.raises(AssertionError,match='engineering target'):assert_source_budget(210001)
    with pytest.raises(AssertionError,match='engineering target'):assert_deployed_size(22501)
    assert_source_budget(230000,exception='synthetic_dependency_reserve')
    with pytest.raises(AssertionError):assert_source_budget(235001,exception='synthetic_dependency_reserve')
    with pytest.raises(AssertionError):assert_source_budget(250000,exception='synthetic_dependency_reserve')
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
