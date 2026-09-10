"""Offline replay of actual fixed-pin bytes, explicitly using synthetic dispatch."""
import json
from pathlib import Path

import boa
import pytest

from .compiled import deploy
from .graph import make_graph,source,params,admit,weth_price_source
from .raw import Raw,Revert
from eth_abi import encode
from eth_utils import keccak
from .fork_inputs import FRESH_FIXTURE
from .fork_worker import reference_price,VECTORS

DATA=json.loads(FRESH_FIXTURE.read_text())


@pytest.mark.parametrize('case',DATA['cases'],ids=lambda c:f"{c['asset']}-{c['window']}")
def test_captured_fresh_inputs_through_source_and_actual_desk(case):
    """Bytes are captured; immutable-return dispatch/local graph are synthetic."""
    assert DATA['header_consistency']=='matched' and case['status'] in ('qualified','expected_rejected')
    boa.env.evm.patch.timestamp=DATA['pin']['timestamp']
    g=make_graph();raw=case['raw']
    asset=next(a for a in VECTORS['assets'] if a['label']==case['asset'])
    def decoded(key):return bytes.fromhex(raw[key][2:])
    Raw({'decimals()':decoded('assetDecimals')},address=asset['asset'])
    Raw({'decimals()':decoded('wethDecimals')},address=VECTORS['weth'])
    Raw({'decimals()':decoded('anchorDecimals'),'latestRoundData()':decoded('round')},address=VECTORS['anchor']['address'])
    Raw({'getPool(address,address,uint24)':decoded('canonicalPool')},address=VECTORS['factory'])
    Raw({**{key+'()':decoded(key) for key in ('factory','token0','token1','fee','liquidity','slot0')},
         'observations(uint256)':decoded('observation'),'observe(uint32[])':Revert(keccak(text='Error(string)')[:4]+encode(['string'],['OLD'])) if 'observe_revert' in raw else decoded('observe')},address=asset['pool'])
    weth_price_source(g,VECTORS['weth'],VECTORS['anchor']['address'])
    s=source(g,VECTORS['factory'])
    expected=reference_price(raw,asset,case['window'],DATA['pin']['timestamp'],deploy('v3','Reference'))
    assert expected==case['reference']
    if case['status']=='expected_rejected':
        assert expected==0
        with boa.reverts(case['expected_revert']):
            s.addNewPriceFeed(asset['asset'],*params(asset['pool'],window=case['window']),sender=g.gov)
        assert s.pendingUpdates(asset['asset']).actionId==0
        return
    assert expected==case['actual']
    assert admit(g,s,asset['asset'],params(asset['pool'],window=case['window']))==expected
    g.desk.syncTokenScale(asset['asset'],sender=g.local)
    assert g.desk.getPrice(asset['asset'],True)==expected
    assert g.desk.getUsdValue(asset['asset'],10**18,True)==expected
    assert g.desk.getAssetAmount(asset['asset'],expected,True)==10**18
