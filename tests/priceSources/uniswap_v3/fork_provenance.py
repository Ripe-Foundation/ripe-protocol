"""Content identity of the fixed-WETH laboratory, independent of fixture naming."""
import hashlib
import json
import re
from pathlib import Path

from .fork_inputs import ROOT, LAB, VECTORS

CONTRACT_ROOTS=(
    'contracts/priceSources/UniswapV3TwapPrices.vy',
    'contracts/priceSources/ChainlinkPrices.vy',
    'contracts/registries/RipeHq.vy',
    'contracts/registries/PriceDesk.vy',
    'contracts/registries/Switchboard.vy',
    'contracts/data/MissionControl.vy',
)
HELPERS=('fork_worker.py','fork_provenance.py','fork_results.py','graph.py','gas_tools.py','compiled.py')


def laboratory_hash(lab=LAB,vectors=VECTORS):
    return hashlib.sha256(json.dumps({'LAB':lab,'VECTORS':vectors},sort_keys=True,separators=(',',':')).encode()).hexdigest()


def source_identity():
    paths=set(ROOT/path for path in CONTRACT_ROOTS)
    pending=list(paths)
    # Include the actual transitive Vyper dependencies, not unrelated contracts
    # whose future edits should not invalidate this laboratory's fixture.
    while pending:
        current=pending.pop()
        for module in re.findall(r'^import ((?:contracts|interfaces)\.[\w.]+)',current.read_text(),re.M):
            base=ROOT/module.replace('.','/')
            candidates=[base.with_suffix(suffix) for suffix in ('.vy','.vyi')]
            imported=next((p for p in candidates if p.is_file()),None)
            assert imported is not None, f'missing laboratory dependency: {module}'
            if imported not in paths:
                paths.add(imported);pending.append(imported)
    paths.update(Path(__file__).with_name(name) for name in HELPERS)
    paths.update(ROOT/path for path in ('requirements.txt','docs/priceSources/uniswap-v3-twap-upstream-lock.json',
                                      'tests/priceSources/uniswap_v3/reference/v3/artifacts.json'))
    return {'code_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)},
            'laboratory_sha256':laboratory_hash()}


def assert_current_identity(data):
    identity=source_identity()
    for key,value in identity.items():
        assert data.get(key)==value, f'fresh fixture {key} does not match the current laboratory; regenerate it'
    assert data['laboratory']==LAB
    assert all(case['laboratory']==LAB for case in data.get('cases',[]))
