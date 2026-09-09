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
    from .graph import make_graph, source, weth_price_source
    from .raw import Pool
    g=make_graph()
    tokens=[boa.load('contracts/mock/MockChainlinkFeed.vy',10**18) for _ in range(2)]
    asset,weth=sorted(tokens,key=lambda t:int(t.address,16))
    for token in tokens:
        token.setDecimals(18)
    # $1 ETH anchor: a USD price equals the raw WETH quote per whole token.
    anchor=boa.load('contracts/mock/MockChainlinkFeed.vy',10**18)
    weth_price_source(g,weth,anchor)
    factory=boa.load('contracts/mock/MockUniV3Factory.vy')
    pool=Pool(asset,weth,factory)
    factory.setPool(asset,weth,10000,pool.address)
    s=source(g,factory)
    return SimpleNamespace(g=g,s=s,asset=asset,weth=weth,anchor=anchor,factory=factory,pool=pool)


@pytest.fixture(autouse=True)
def restore_python_fixture_state(request):
    # Boa snapshots revert EVM state, but not module-scoped Python objects.
    saved=[]
    for name in ('lab','gas_lab'):
        if name in request.fixturenames:
            lab=request.getfixturevalue(name)
            saved.append((lab,lab.g.desk,dict(lab.pool.responses) if name=='lab' else None))
    try:
        yield
    finally:
        for lab,desk,responses in saved:
            lab.g.desk=desk
            if responses is not None:
                lab.pool.responses=responses


@pytest.fixture
def active(lab):
    from .graph import admit,params
    assert admit(lab.g,lab.s,lab.asset,params(lab.pool))==10**18
    return lab
