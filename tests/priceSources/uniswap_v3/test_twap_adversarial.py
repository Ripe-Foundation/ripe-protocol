"""Boundary failures through public source ABI and unchanged PriceDesk."""
import boa
import pytest
from conf_utils import advance_timelock_blocks

from .graph import source,params,admit
from .raw import Raw,word,words,selector
from .gas_tools import cold,calls
from .test_twap_lifecycle import state


@pytest.mark.parametrize('dependency',['asset','anchor','factory','pool_factory','token0','token1','fee'])
@pytest.mark.parametrize('fault',['revert','empty','short','extra','width','burn'])
def test_admission_scalar_abi_and_confirmation_rollback(lab,dependency,fault):
    l=lab
    l.s.addNewPriceFeed(l.asset,params(l.pool),sender=l.g.gov)
    before=state(l.s,l.asset)
    signature={'asset':'decimals()','anchor':'decimals()','factory':'getPool(address,address,uint24)',
               'pool_factory':'factory()','token0':'token0()','token1':'token1()','fee':'fee()'}[dependency]
    valid={'asset':word(18),'anchor':word(8),'factory':word(l.pool.address),'pool_factory':word(l.factory),
           'token0':word(l.asset),'token1':word(l.weth),'fee':word(10000)}[dependency]
    invalid={'empty':b'','short':valid[:-1],'extra':valid+b'\0','width':word(2**255),'burn':None}
    responses={} if fault=='revert' else {signature:invalid[fault]}
    target={'asset':l.asset,'anchor':l.anchor,'factory':l.factory}.get(dependency,l.pool)
    if target is l.pool:
        responses=dict(l.pool.responses)
        if fault=='revert':responses.pop(signature)
        else:responses[signature]=invalid[fault]
    Raw(responses,address=target.address)
    advance_timelock_blocks(2)
    with boa.reverts('feed metadata changed'):l.s.confirmNewPriceFeed(l.asset,sender=l.g.gov)
    assert l.s._computation.get_log_entries()==()
    assert state(l.s,l.asset)==before
    l.s.cancelNewPendingPriceFeed(l.asset,sender=l.g.gov)
    with boa.reverts('invalid feed'):l.s.addNewPriceFeed(l.asset,params(l.pool),sender=l.g.gov)
    assert l.s.getBoundAssetDecimals(l.asset)==(False,0)


@pytest.mark.parametrize('dependency',['weth','anchor'])
@pytest.mark.parametrize('fault',['revert','empty','short','extra','width','burn'])
def test_constructor_exact_decimal_abi(lab,dependency,fault):
    good=word(18 if dependency=='weth' else 8)
    data={'empty':b'','short':good[:-1],'extra':good+b'\0','width':word(2**255),'burn':None}
    Raw({} if fault=='revert' else {'decimals()':data[fault]},address=getattr(lab,dependency).address)
    with boa.reverts('invalid dependencies'):source(lab.g,lab.factory,lab.weth,lab.anchor)


@pytest.mark.parametrize('fault',['revert','empty','short','extra','zero_price','status0','status2','wide_status','burn'])
def test_callback_exact_abi_and_status_roll_back_every_staged_write(lab,fault):
    l=lab
    l.s.addNewPriceFeed(l.asset,params(l.pool),sender=l.g.gov)
    before=state(l.s,l.asset)
    payloads={'empty':b'','short':words(10**18,1)[:-1],'extra':words(10**18,1)+b'\0',
              'zero_price':words(0,1),'status0':words(10**18,0),'status2':words(10**18,2),
              'wide_status':words(10**18,2**255),'burn':None}
    # Fault injection only: the normal/staging/gas suites use actual PriceDesk.
    responses={'tokenScale(address)':word(0)}
    if fault!='revert':responses['qualifyCallerPriceSource(address)']=payloads[fault]
    Raw(responses,address=l.g.desk.address)
    advance_timelock_blocks(2)
    with boa.reverts('price source not executable'):l.s.confirmNewPriceFeed(l.asset,sender=l.g.gov)
    assert l.s._computation.get_log_entries()==()
    assert state(l.s,l.asset)==before


def test_nonzero_callback_stale_time_is_rejected_by_actual_desk(lab):
    assert lab.g.desk.qualifyCallerPriceSource(lab.asset,300,sender=lab.s.address)==(0,2)
    assert lab.g.desk._computation.children==[]


@pytest.mark.parametrize('case',['intermediate_overflow_valid','final_overflow','anchor_overflow','final_zero'])
def test_full_source_usd_normalization_and_512_bit_composition(active,case,math):
    l=active
    answer=(2**256-1)//10**10
    tick=0
    if case=='final_overflow':tick=1
    elif case=='anchor_overflow':answer=2**255-1
    elif case=='final_zero':tick=-400000;answer=1
    if case=='final_zero':assert math.quote(tick,10**18,True)>0
    l.pool.set_history(tick=tick)
    Raw({'decimals()':word(8),'latestRoundData()':words(1,answer,0,boa.env.timestamp,1)},address=l.anchor.address)
    expected=answer*10**10 if case=='intermediate_overflow_valid' else 0
    assert l.s.getPriceAndHasFeed(l.asset)==(expected,True)
    assert l.g.desk.getPrice(l.asset)==expected
    if expected:
        assert 10**18*expected>=2**256
    else:
        with boa.reverts('has price config, no price'):l.g.desk.getPrice(l.asset,True)


def costly_valid_dependencies(l):
    """Synthetic valid return bytes near individual caps; no stipend override."""
    Raw({'decimals()':(word(18),550)},address=l.asset.address)
    Raw({'decimals()':(word(8),550),
         'latestRoundData()':(words(1,10**8,0,boa.env.timestamp,1),1120)},address=l.anchor.address)
    for signature in ('slot0()','liquidity()','observations(uint256)'):
        l.pool.set(signature,(l.pool.responses[signature],550))
    l.pool.set('observe(uint32[])',(l.pool.responses['observe(uint32[])'],4550))


def test_direct_success_but_actual_desk_stipend_failure_rejects_confirmation(active):
    l=active
    l.s.updatePriceFeed(l.asset,params(l.pool,age=3601),sender=l.g.gov)
    before=state(l.s,l.asset)
    costly_valid_dependencies(l)
    cold(l.s)
    assert l.s.getPrice(l.asset)==10**18
    direct=l.s._computation.get_gas_used()
    cold(l.g.desk)
    assert l.g.desk.getPrice(l.asset)==0
    child=calls(l.g.desk._computation,l.s)[0]
    assert child.msg.gas==250000 and not child.is_error and child.output==words(0,1)
    advance_timelock_blocks(2)
    with boa.reverts('price source not executable'):l.s.confirmPriceFeedUpdate(l.asset,sender=l.g.gov)
    trace=l.s._computation
    assert trace.get_log_entries()==()
    qualification=[c for c in calls(trace,l.g.desk) if bytes(c.msg.data[:4])==selector('qualifyCallerPriceSource(address)')]
    assert len(qualification)==1
    callback=calls(qualification[0],l.s)[0]
    assert callback.msg.gas==250000 and callback.output==words(0,1) and not callback.is_error
    assert state(l.s,l.asset)==before
    print(f'TWAP_STIPEND_REJECTION direct_positive={direct} callback_failure={callback.get_gas_used()}')
