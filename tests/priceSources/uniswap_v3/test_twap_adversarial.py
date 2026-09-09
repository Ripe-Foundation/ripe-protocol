"""Boundary failures through public source ABI and unchanged PriceDesk."""
import boa
import pytest
from conf_utils import advance_timelock_blocks

from .graph import params
from .raw import Raw,word,words
from .helpers import state


@pytest.mark.parametrize('fault',['zero_price','status0','status2','wide_status','revert','empty','short'])
def test_callback_status_and_abi_faults_roll_back_every_staged_write(lab,fault):
    l=lab
    l.s.addNewPriceFeed(l.asset,*params(l.pool),sender=l.g.gov)
    before=state(l.s,l.asset)
    payloads={'zero_price':words(0,1),'status0':words(10**18,0),'status2':words(10**18,2),
              'wide_status':words(10**18,2**255),'empty':b'','short':words(10**18,1)[:-1]}
    # Fault injection only: the normal/staging/gas suites use actual PriceDesk.
    responses={'getPrice(address,bool)':word(10**18),'tokenScale(address)':word(0)}
    if fault!='revert':responses['qualifyCallerPriceSource(address)']=payloads[fault]
    Raw(responses,address=l.g.desk.address)
    advance_timelock_blocks(2)
    reason='price source not executable' if fault in ('zero_price','status0','status2','wide_status') else None
    with boa.reverts(reason) if reason else boa.reverts():
        l.s.confirmNewPriceFeed(l.asset,sender=l.g.gov)
    assert l.s._computation.get_log_entries()==()
    assert state(l.s,l.asset)==before


def test_nonzero_callback_stale_time_is_rejected_by_actual_desk(lab):
    assert lab.g.desk.qualifyCallerPriceSource(lab.asset,300,sender=lab.s.address)==(0,2)
    assert lab.g.desk._computation.children==[]


@pytest.mark.parametrize('case',['intermediate_overflow_valid','final_overflow','weth_overflow','final_zero'])
def test_full_source_usd_composition_at_512_bit_boundaries(active,case,math):
    l=active
    answer=(2**256-1)//10**10
    tick=0
    if case=='final_overflow':tick=1
    elif case=='weth_overflow':answer=2**255-1
    elif case=='final_zero':tick=-400000;answer=1
    if case=='final_zero':assert math.quote(tick,10**18,True)>0
    l.pool.set_history(tick=tick)
    l.anchor.setMockData(answer)
    expected=answer*10**10 if case=='intermediate_overflow_valid' else 0
    assert l.s.getPriceAndHasFeed(l.asset)==(expected,True)
    assert l.g.desk.getPrice(l.asset)==expected
    if expected:
        assert 10**18*expected>=2**256
    else:
        with boa.reverts('has price config, no price'):l.g.desk.getPrice(l.asset,True)
