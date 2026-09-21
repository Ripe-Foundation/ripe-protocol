"""Constructor configuration must not call the active PriceDesk."""
import boa
import pytest

ZERO = "0x" + "00" * 20
E18 = 10 ** 18
EMPTY_REF = (ZERO, ZERO, 0, ZERO, 0, 0, 0, 0, 0, 0)


@pytest.fixture
def system():
    owner = boa.env.generate_address()
    green = boa.load("contracts/mock/MockErc20.vy", owner, "GREEN", "GREEN", 18, 1)
    alt = boa.load("contracts/mock/MockErc20.vy", owner, "ALT", "ALT", 6, 1)
    savings, ripe, eth, btc = [boa.env.generate_address() for _ in range(4)]
    hq = boa.load("contracts/mock/MockCurveRefPoolRegistry.vy", owner, green, savings, ripe)
    pool = boa.load("contracts/mock/MockCurveRefPool.vy")
    hq.setPool(pool, alt, green)
    pool.setBalances(10_000 * 10 ** 6, 10_000 * E18)
    # HQ slot 7 is zero: any dependency on PriceDesk must fail.
    return owner, green, alt, savings, eth, btc, hq, pool


def chainlink(s, feeds, default_feed=ZERO):
    owner, _, alt, _, eth, btc, hq, _ = s
    return boa.load("contracts/priceSources/ChainlinkPrices.vy", hq, ZERO,
                    1, 100, alt, eth, btc, default_feed, ZERO, 86400, feeds)


def curve(s, feeds, ref=EMPTY_REF):
    owner, green, _, savings, _, _, hq, _ = s
    return boa.load("contracts/priceSources/CurvePrices.vy", hq, ZERO, hq,
                    green, savings, 1, 100, feeds, ref)


def test_chainlink_bootstrap_conversion_anchor_order_and_decimals(system):
    _, green, _, _, eth, _, _, _ = system
    quote = boa.load("contracts/mock/MockChainlinkFeed.vy", 2 * E18)
    anchor = boa.load("contracts/mock/MockChainlinkFeed.vy", 2000 * E18)
    c = chainlink(system, [(green.address, quote.address, 86400, True, False),
                           (eth, anchor.address, 86400, False, False)])
    assert c.getPrice(green) == 4000 * E18
    assert c.feedConfig(green).decimals == 8
    assert c.pendingUpdates(green).actionId == 0
    assert len(c.getPricedAssets()) == 2


@pytest.mark.parametrize("invalid", ["duplicate", "zero", "stale", "both_conversions", "missing_anchor", "default_duplicate"])
def test_chainlink_constructor_rejects_invalid_config(system, invalid):
    _, green, alt, _, _, _, _, _ = system
    feed = boa.load("contracts/mock/MockChainlinkFeed.vy", E18)
    entry = (green.address, feed.address, 86400, False, False)
    entries = [entry]
    default = ZERO
    if invalid == "duplicate": entries *= 2
    if invalid == "zero": entries = [(ZERO, feed.address, 86400, False, False)]
    if invalid == "stale": entries = [(green.address, feed.address, 1, False, False)]
    if invalid == "both_conversions": entries = [(green.address, feed.address, 86400, True, True)]
    if invalid == "missing_anchor": entries = [(green.address, feed.address, 86400, True, False)]
    if invalid == "default_duplicate":
        default = feed.address
        entries = [(alt.address, feed.address, 86400, False, False)]
    reason = "duplicate initial feed" if invalid in ("duplicate", "default_duplicate") else "invalid asset" if invalid == "zero" else "invalid initial feed"
    with boa.reverts(reason):
        chainlink(system, entries, default)


def test_curve_constructor_loads_routes_and_reference_pool_without_desk(system):
    _, green, alt, _, _, _, _, pool = system
    ref = (pool.address, pool.address, 1, alt.address, 6, 10, 6000, 100, 1000, 100_000 * E18)
    c = curve(system, [(green.address, pool.address)], ref)
    assert c.curveConfig(green).pool == pool.address
    assert list(c.getPricedAssets()) == [green.address]
    assert tuple(c.greenRefPoolConfig()) == ref
    assert c.greenRefPoolData().lastSnapshot.update != 0


@pytest.mark.parametrize("invalid", ["duplicate", "unregistered", "wrong_asset", "reference_decimals"])
def test_curve_constructor_rejects_invalid_config(system, invalid):
    _, green, alt, _, _, _, _, pool = system
    feeds = [(green.address, pool.address)]
    refs = EMPTY_REF
    if invalid == "duplicate": feeds *= 2
    if invalid == "unregistered": feeds = [(green.address, boa.env.generate_address())]
    if invalid == "wrong_asset": feeds = [(boa.env.generate_address(), pool.address)]
    if invalid == "reference_decimals":
        refs = (pool.address, pool.address, 1, alt.address, 18, 10, 6000, 100, 1000, 100_000 * E18)
    with boa.reverts("invalid initial decimals" if invalid == "reference_decimals" else "invalid initial pool"):
        curve(system, feeds, refs)


@pytest.mark.parametrize("reverse", [False, True])
def test_curve_constructor_rejects_dependency_cycle_in_either_order(system, reverse):
    _, green, alt, _, _, _, _, pool = system
    feeds = [(green.address, pool.address), (alt.address, pool.address)]
    with boa.reverts("invalid initial pool"):
        curve(system, feeds[::-1] if reverse else feeds)


def test_curve_constructor_empty_reference_pool(system):
    c = curve(system, [])
    assert tuple(c.greenRefPoolConfig()) == EMPTY_REF
    assert c.greenRefPoolData().lastSnapshot.update == 0


def test_curve_constructor_zero_pool_skips_reference_initialization(system):
    ref = list(EMPTY_REF)
    ref[5] = 10
    c = curve(system, [], tuple(ref))
    assert tuple(c.greenRefPoolConfig()) == EMPTY_REF
    assert c.greenRefPoolData().lastSnapshot.update == 0
