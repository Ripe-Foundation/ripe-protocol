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
    for name in ('UniV3FeedProposed','UniV3FeedConfirmed','UniV3FeedCancelled'):
        e=next(e for e in entries if e.get('name')==name)
        assert e['type']=='event'
        assert [i['name'] for i in e['inputs'] if i['indexed']]==['asset','actionId']
    assert 'priceSources/modules/UniswapV3TwapMath.vy' in NON_STANDALONE_VYPER_SOURCES
    assert not (path.parent/'UniswapV3TwapMath.json').exists()
