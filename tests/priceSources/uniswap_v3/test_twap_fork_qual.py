"""One isolated worker pins all twelve cases; default CI never requests RPC."""
import json
import os
from pathlib import Path
import sys

import pytest
from .fork_results import run_worker,initial_results
from .fork_inputs import VECTORS,LAB

BASE=Path(__file__).resolve().parent


@pytest.fixture(scope='module')
def ripe_hq():
    """No parent-session graph is needed by the subprocess launcher."""


@pytest.fixture(scope='module')
def fork_results(tmp_path_factory):
    env=os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE']='1'
    env['RIPE_TWAP_FORK_OUTPUT']=str(tmp_path_factory.mktemp('twap-fork')/'inputs.json')
    data=run_worker([sys.executable,str(BASE/'fork_worker.py')],cwd=BASE.parents[2],env=env,
                    initial=initial_results(env.get('RIPE_TWAP_PIN_MODE'),[a['label'] for a in VECTORS['assets']],LAB))
    assert len(data['cases'])==3*len(VECTORS['assets'])
    return data


@pytest.mark.fork_qualification
@pytest.mark.parametrize('asset',[a['label'] for a in VECTORS['assets']])
@pytest.mark.parametrize('window',[1800,3600,14400])
def test_primary_pool_at_explicit_pin(fork_results,asset,window):
    case=next(c for c in fork_results['cases'] if c['asset']==asset and c['window']==window)
    print('TWAP_FORK '+json.dumps({k:v for k,v in case.items() if k!='raw'},sort_keys=True))
    if case['status']=='unverified':pytest.skip('unverified: '+case['reason'])
    assert case['behavior_passed'],case['reason']
