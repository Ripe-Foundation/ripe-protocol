"""One isolated worker pins all twelve cases; default CI never requests RPC."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

BASE=Path(__file__).resolve().parent


@pytest.fixture(scope='module')
def ripe_hq():
    """No parent-session graph is needed by the subprocess launcher."""


@pytest.fixture(scope='module')
def fork_results(tmp_path_factory):
    env=os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE']='1'
    env['RIPE_TWAP_FORK_OUTPUT']=str(tmp_path_factory.mktemp('twap-fork')/'inputs.json')
    result=subprocess.run([sys.executable,str(BASE/'fork_worker.py')],cwd=BASE.parents[2],env=env,text=True,capture_output=True,timeout=600)
    assert result.returncode==0,result.stdout+result.stderr
    line=next(line for line in result.stdout.splitlines() if line.startswith('TWAP_FORK_RESULT '))
    data=json.loads(line.removeprefix('TWAP_FORK_RESULT '))
    assert len(data['cases'])==12
    return data


@pytest.mark.fork_qualification
@pytest.mark.parametrize('asset',['PONS','CASHCAT','AI','INDEX'])
@pytest.mark.parametrize('window',[1800,3600,14400])
def test_primary_pool_at_explicit_pin(fork_results,asset,window):
    case=next(c for c in fork_results['cases'] if c['asset']==asset and c['window']==window)
    print('TWAP_FORK '+json.dumps({k:v for k,v in case.items() if k!='raw'},sort_keys=True))
    if case['status']=='unverified':pytest.skip('unverified: '+case['reason'])
    assert case['behavior_passed'],case['reason']
