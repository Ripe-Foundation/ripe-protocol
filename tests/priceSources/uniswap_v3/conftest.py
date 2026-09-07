import boa
import pytest


@pytest.fixture(scope='session')
def ripe_hq():
    """This subtree builds its own minimal graph, with no session bootstrap."""


@pytest.fixture(autouse=True)
def twap_isolation():
    with boa.env.anchor():
        yield


@pytest.fixture
def math():
    return boa.load('tests/priceSources/uniswap_v3/MathHarness.vy')


@pytest.fixture(scope='module')
def lab():
    from types import SimpleNamespace
    from .graph import make_graph, source
    from .raw import Pool
    g=make_graph()
    tokens=[boa.load('contracts/mock/MockChainlinkFeed.vy',10**18) for _ in range(2)]
    asset,weth=sorted(tokens,key=lambda t:int(t.address,16))
    for token in tokens:
        token.setDecimals(18)
    anchor=boa.load('contracts/mock/MockChainlinkFeed.vy',10**18)
    factory=boa.load('contracts/mock/MockUniV3Factory.vy')
    pool=Pool(asset,weth,factory)
    factory.setPool(asset,weth,10000,pool.address)
    s=source(g,factory,weth,anchor)
    return SimpleNamespace(g=g,s=s,asset=asset,weth=weth,anchor=anchor,factory=factory,pool=pool)


@pytest.fixture(autouse=True)
def restore_raw_fixture(request):
    # Python fixture dictionaries are not reverted by Boa's EVM snapshot.
    if 'lab' in request.fixturenames:
        lab=request.getfixturevalue('lab')
        original=dict(lab.pool.responses)
        yield
        lab.pool.responses=original
    else:
        yield


@pytest.fixture
def active(lab):
    from .graph import admit,params
    assert admit(lab.g,lab.s,lab.asset,params(lab.pool))==10**18
    return lab
