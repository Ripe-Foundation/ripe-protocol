import boa
from .graph import make_graph,source,admit,params
from .pools import organic_pool,seed_ring,pack,SLOTS


def test_compiler_layout_seed_matches_organic_history_and_repeated_timestamps():
    g=make_graph();f,p,a,w,actor,ref=organic_pool(g)
    original_state=tuple(p.slot0())
    original_obs=[tuple(p.observations(i)) for i in range(8)]
    for i,obs in enumerate(original_obs):
        assert boa.env.evm.get_storage(p.address,SLOTS['observations']+i)==pack('observations',obs)
    assert boa.env.evm.get_storage(p.address,SLOTS['slot0'])==pack('slot0',original_state)
    expected=p.observe([0,1,600,1800,3600])
    # Another liquidity-only action at this timestamp adds no new observation.
    actor.add(p.address,1);actor.remove(p.address,1)
    assert tuple(p.slot0())==original_state
    assert [tuple(p.observations(i)) for i in range(8)]==original_obs
    seed_ring(p,8,initialized=7,spacing=600)
    assert tuple(p.slot0())==original_state
    assert [tuple(p.observations(i)) for i in range(8)]==original_obs
    assert p.observe([0,1,600,1800,3600])==expected
    # The exact oldest boundary succeeds; one older second is genuine OLD.
    with boa.reverts('OLD'):p.observe([3601,0])
    anchor=boa.load('contracts/mock/MockChainlinkFeed.vy',10**18)
    s=source(g,f.address,w,anchor)
    admit(g,s,a.address,params(p,window=3600))
    assert g.desk.getPrice(a.address,True)==10**18
    actor.remove(p.address,10**20)
    assert p.liquidity()==0
    assert s.getPriceAndHasFeed(a.address)==(0,True)


def test_authentic_uint32_wrap_and_observation_only_writes():
    g=make_graph();boa.env.evm.patch.timestamp=2**32-3000
    f,p,a,w,actor,ref=organic_pool(g)
    assert boa.env.timestamp==2**32+600
    assert p.observations(0)[0]==2**32-3000
    assert p.observations(6)[0]==600
    assert p.observe([1800,0])[0]==[0,0]
    anchor=boa.load('contracts/mock/MockChainlinkFeed.vy',10**18)
    s=source(g,f.address,w,anchor)
    admit(g,s,a.address,params(p))
    assert g.desk.getPrice(a.address,True)==10**18


def test_authentic_crash_lag_extrapolation_and_halt_restart():
    g=make_graph();f,p,a,w,actor,ref=organic_pool(g)
    anchor=boa.load('contracts/mock/MockChainlinkFeed.vy',10**18)
    s=source(g,f.address,w,anchor)
    admit(g,s,a.address,params(p))
    actor.move(p.address,True,ref.sqrt(-6932))
    actual_tick=p.slot0()[1]
    assert actual_tick in (-6932,-6933)  # boundary tick semantics are canonical
    assert s.getPrice(a.address)==10**18  # entire trailing window predates crash
    boa.env.time_travel(seconds=900)
    expected=ref.quote(actual_tick//2,10**18,a.address,w.address)
    assert s.getPrice(a.address)==expected and 7*10**17<expected<8*10**17
    boa.env.time_travel(seconds=2100)
    # Fully extrapolated interval; no write in the last 3,000 seconds.
    assert s.getPrice(a.address)==ref.quote(actual_tick,10**18,a.address,w.address)
    boa.env.time_travel(seconds=601)
    assert s.getPriceAndHasFeed(a.address)==(0,True)
    # A liquidity action after the halt refreshes observation age, without
    # establishing a newly traded full window or a restart circuit breaker.
    actor.add(p.address,1);actor.remove(p.address,1)
    assert g.desk.getPrice(a.address,True)==ref.quote(actual_tick,10**18,a.address,w.address)
    anchor.setMockData(10**8,1,1,0,boa.env.timestamp-86401)
    assert s.getPriceAndHasFeed(a.address)==(0,True)
    anchor.setMockData(10**8)
    assert g.desk.getPrice(a.address,True)>0
