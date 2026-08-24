import boa

from config.BluePrint import PARAMS
from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS


CURVE_AP = """
# @version 0.4.3

mr: public(address)
factory: public(address)

@deploy
def __init__(_mr: address, _factory: address):
    self.mr = _mr
    self.factory = _factory

@view
@external
def get_address(_id: uint256) -> address:
    if _id == 7:
        return self.mr
    return self.factory
"""

CURVE_MR = """
# @version 0.4.3

coins: public(address[8])
lp: public(address)
factory: public(address)
n: public(uint256)

@external
def setup(_coins: address[8], _lp: address, _factory: address, _n: uint256):
    self.coins = _coins
    self.lp = _lp
    self.factory = _factory
    self.n = _n

@external
def setN(_n: uint256):
    self.n = _n

@external
def setCoins(_coins: address[8]):
    self.coins = _coins

@view
@external
def is_registered(_pool: address) -> bool:
    return True

@view
@external
def get_lp_token(_pool: address) -> address:
    return self.lp

@view
@external
def get_underlying_coins(_pool: address) -> address[8]:
    return self.coins

@view
@external
def get_n_underlying_coins(_pool: address) -> uint256:
    return self.n

@view
@external
def get_registry_handlers_from_pool(_pool: address) -> address[10]:
    out: address[10] = empty(address[10])
    out[0] = self
    return out

@view
@external
def get_base_registry(_handler: address) -> address:
    return self.factory
"""

CURVE_POOL = """
# @version 0.4.3

@view
@external
def get_virtual_price() -> uint256:
    return 10 ** 18

@view
@external
def lp_price() -> uint256:
    return 10 ** 18

@view
@external
def price_oracle(_i: uint256 = 0) -> uint256:
    return 10 ** 18

@view
@external
def totalSupply() -> uint256:
    return 10 ** 18
"""

CURVE_POOL_WITH_SUPPLY = """
# @version 0.4.3

supply: public(uint256)

@external
def setSupply(_supply: uint256):
    self.supply = _supply

@view
@external
def get_virtual_price() -> uint256:
    return 10 ** 18

@view
@external
def lp_price() -> uint256:
    return 10 ** 18

@view
@external
def price_oracle(_i: uint256 = 0) -> uint256:
    return 10 ** 18

@view
@external
def totalSupply() -> uint256:
    return self.supply
"""


def _desk_params(fork):
    return (
        PARAMS[fork]["PRICE_DESK_MIN_REG_TIMELOCK"],
        PARAMS[fork]["PRICE_DESK_MAX_REG_TIMELOCK"],
    )


def _coins8(alpha_token, bravo_token, charlie_token, delta_token):
    extra = [boa.env.generate_address(f"coin{i}") for i in range(4)]
    return [
        alpha_token.address,
        bravo_token.address,
        charlie_token.address,
        delta_token.address,
        extra[0],
        extra[1],
        extra[2],
        extra[3],
    ], extra


def _load_curve(ripe_hq, green_token, savings_green, fork, ap):
    min_tl, max_tl = _desk_params(fork)
    return boa.load(
        "contracts/priceSources/CurvePrices.vy",
        ripe_hq,
        ZERO_ADDRESS,
        ap.address,
        green_token,
        savings_green,
        min_tl,
        max_tl,
        name="curve_n_coins",
    )


def _setup_system(alpha_token, bravo_token, charlie_token, delta_token, n, coins8=None, lp=None):
    extra = []
    if coins8 is None:
        coins8, extra = _coins8(alpha_token, bravo_token, charlie_token, delta_token)
    factory = boa.env.generate_address("curve_factory")
    mr = boa.loads(CURVE_MR)
    ap = boa.loads(CURVE_AP, mr.address, factory)
    pool = boa.loads(CURVE_POOL)
    if lp is None:
        lp = boa.loads(CURVE_POOL_WITH_SUPPLY)
        lp.setSupply(EIGHTEEN_DECIMALS)
    mr.setup(coins8, lp, factory, n)
    return mr, ap, pool, lp, extra


def test_get_curve_pool_config_still_reports_eight_count_and_four_addresses(
    ripe_hq,
    governance,
    green_token,
    savings_green,
    alpha_token,
    bravo_token,
    charlie_token,
    delta_token,
    fork,
):
    mr, ap, pool, lp, extra = _setup_system(
        alpha_token, bravo_token, charlie_token, delta_token, 8
    )
    curve = _load_curve(ripe_hq, green_token, savings_green, fork, ap)
    cfg = curve.getCurvePoolConfig(pool)
    assert cfg.numUnderlying == 8
    stored = [str(a).lower() for a in cfg.underlying]
    assert stored == [
        str(alpha_token.address).lower(),
        str(bravo_token.address).lower(),
        str(charlie_token.address).lower(),
        str(delta_token.address).lower(),
    ]
    assert str(extra[0]).lower() not in stored


def test_propose_rejects_five_through_eight_underlyings(
    ripe_hq,
    governance,
    green_token,
    savings_green,
    mock_price_source,
    alpha_token,
    bravo_token,
    charlie_token,
    delta_token,
    fork,
):
    for n in range(5, 9):
        mr, ap, pool, lp, extra = _setup_system(
            alpha_token, bravo_token, charlie_token, delta_token, n
        )
        curve = _load_curve(ripe_hq, green_token, savings_green, fork, ap)
        for token in (alpha_token, bravo_token, charlie_token, delta_token):
            mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
        assert curve.getCurvePoolConfig(pool).numUnderlying == n
        assert not curve.isValidNewFeed(lp, pool)
        with boa.reverts("invalid pool"):
            curve.addNewPriceFeed(lp, pool, sender=governance.address)


def test_exactly_four_accepted(
    ripe_hq,
    governance,
    green_token,
    savings_green,
    mock_price_source,
    alpha_token,
    bravo_token,
    charlie_token,
    delta_token,
    fork,
):
    mr, ap, pool, lp, extra = _setup_system(
        alpha_token, bravo_token, charlie_token, delta_token, 4
    )
    curve = _load_curve(ripe_hq, green_token, savings_green, fork, ap)
    for token in (alpha_token, bravo_token, charlie_token, delta_token):
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
    assert curve.isValidNewFeed(lp, pool)
    assert curve.addNewPriceFeed(lp, pool, sender=governance.address)
    boa.env.time_travel(blocks=curve.actionTimeLock() + 1)
    for token in (alpha_token, bravo_token, charlie_token, delta_token):
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
    assert curve.confirmNewPriceFeed(lp, sender=governance.address)
    assert curve.hasPriceFeed(lp)
    assert curve.curveConfig(lp).numUnderlying == 4


def test_empty_ecosystem_lp_confirmation_is_atomic_and_retryable(
    ripe_hq,
    governance,
    green_token,
    ripe_token,
    savings_green,
    mock_price_source,
    price_desk,
    mission_control,
    switchboard_alpha,
    alpha_token,
    bravo_token,
    charlie_token,
    delta_token,
    fork,
):
    coins = [
        ripe_token.address,
        alpha_token.address,
        ZERO_ADDRESS,
        ZERO_ADDRESS,
        ZERO_ADDRESS,
        ZERO_ADDRESS,
        ZERO_ADDRESS,
        ZERO_ADDRESS,
    ]
    factory = boa.env.generate_address("empty eco curve factory")
    mr = boa.loads(CURVE_MR)
    ap = boa.loads(CURVE_AP, mr.address, factory)
    # Model Curve's two-contract topology: the pool prices the LP, while the
    # distinct LP token owns totalSupply().
    pool = boa.loads(CURVE_POOL)
    lp = boa.loads(CURVE_POOL_WITH_SUPPLY)
    mr.setup(coins, lp, factory, 2)
    curve = _load_curve(ripe_hq, green_token, savings_green, fork, ap)
    assert price_desk.address != ZERO_ADDRESS
    mission_control.setPriorityPriceSourceIds(
        [6],
        sender=switchboard_alpha.address,
    )

    # Empty ecosystem LPs remain proposal-compatible for launch sequencing.
    assert curve.addNewPriceFeed(lp, pool, sender=governance.address)
    pending_action = curve.pendingUpdates(lp).actionId
    boa.env.time_travel(blocks=curve.actionTimeLock() + 1)

    with boa.reverts("empty pool"):
        curve.confirmNewPriceFeed(lp, sender=governance.address)
    assert curve.pendingUpdates(lp).actionId == pending_action
    assert curve.curveConfig(lp).pool == ZERO_ADDRESS

    # A seeded LP with an unavailable underlying still fails atomically under
    # the exact source stipend instead of consuming or cancelling the action.
    lp.setSupply(EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    with boa.reverts("price source not executable"):
        curve.confirmNewPriceFeed(lp, sender=governance.address)
    assert curve.pendingUpdates(lp).actionId == pending_action
    assert not curve.hasPriceFeed(lp)

    mock_price_source.setPrice(ripe_token, EIGHTEEN_DECIMALS)
    assert price_desk.getPrice(ripe_token) == EIGHTEEN_DECIMALS
    assert curve.indexOfAsset(lp) == 0
    assert curve.canConfirmAction(pending_action)
    assert curve.confirmNewPriceFeed(lp, sender=governance.address)
    assert curve.pendingUpdates(lp).actionId == 0
    assert curve.hasPriceFeed(lp)


def test_empty_ecosystem_lp_update_confirmation_is_atomic_and_retryable(
    ripe_hq,
    governance,
    green_token,
    ripe_token,
    savings_green,
    mock_price_source,
    price_desk,
    mission_control,
    switchboard_alpha,
    alpha_token,
    fork,
):
    coins = [
        ripe_token.address,
        alpha_token.address,
        ZERO_ADDRESS,
        ZERO_ADDRESS,
        ZERO_ADDRESS,
        ZERO_ADDRESS,
        ZERO_ADDRESS,
        ZERO_ADDRESS,
    ]
    factory = boa.env.generate_address("update eco curve factory")
    mr = boa.loads(CURVE_MR)
    ap = boa.loads(CURVE_AP, mr.address, factory)
    old_pool = boa.loads(CURVE_POOL)
    new_pool = boa.loads(CURVE_POOL)
    lp = boa.loads(CURVE_POOL_WITH_SUPPLY)
    lp.setSupply(EIGHTEEN_DECIMALS)
    mr.setup(coins, lp, factory, 2)
    curve = _load_curve(ripe_hq, green_token, savings_green, fork, ap)
    assert price_desk.address != ZERO_ADDRESS
    mission_control.setPriorityPriceSourceIds(
        [6],
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(ripe_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)

    assert curve.addNewPriceFeed(lp, old_pool, sender=governance.address)
    boa.env.time_travel(blocks=curve.actionTimeLock() + 1)
    assert curve.confirmNewPriceFeed(lp, sender=governance.address)
    previous = curve.curveConfig(lp)

    # The proposal remains valid while the LP is empty, but confirmation reads
    # supply from the distinct LP token and preserves the old active route.
    lp.setSupply(0)
    assert curve.updatePriceFeed(lp, new_pool, sender=governance.address)
    pending_action = curve.pendingUpdates(lp).actionId
    boa.env.time_travel(blocks=curve.actionTimeLock() + 1)
    with boa.reverts("empty pool"):
        curve.confirmPriceFeedUpdate(lp, sender=governance.address)
    assert curve.pendingUpdates(lp).actionId == pending_action
    assert curve.curveConfig(lp) == previous

    # A seeded LP with an unavailable underlying also reverts atomically.
    lp.setSupply(EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(alpha_token, 0)
    mock_price_source.disablePriceFeed(alpha_token)
    with boa.reverts("price source not executable"):
        curve.confirmPriceFeedUpdate(lp, sender=governance.address)
    assert curve.pendingUpdates(lp).actionId == pending_action
    assert curve.curveConfig(lp) == previous

    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    assert curve.confirmPriceFeedUpdate(lp, sender=governance.address)
    assert curve.pendingUpdates(lp).actionId == 0
    assert curve.curveConfig(lp).pool == new_pool.address


def test_new_and_update_confirm_store_pending_four_coin_config_after_registry_drift(
    ripe_hq,
    governance,
    green_token,
    savings_green,
    mock_price_source,
    alpha_token,
    bravo_token,
    charlie_token,
    delta_token,
    fork,
):
    mr, ap, pool, lp, extra = _setup_system(
        alpha_token, bravo_token, charlie_token, delta_token, 4
    )
    curve = _load_curve(ripe_hq, green_token, savings_green, fork, ap)
    for token in (alpha_token, bravo_token, charlie_token, delta_token):
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)

    assert curve.addNewPriceFeed(lp, pool, sender=governance.address)
    pending = curve.pendingUpdates(lp).config
    assert pending.numUnderlying == 4
    drifted_coins = [
        extra[0],
        extra[1],
        extra[2],
        extra[3],
        alpha_token.address,
        bravo_token.address,
        charlie_token.address,
        delta_token.address,
    ]
    boa.env.time_travel(blocks=curve.actionTimeLock() + 1)
    mr.setN(8)
    mr.setCoins(drifted_coins)
    for token in (alpha_token, bravo_token, charlie_token, delta_token):
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
    assert curve.confirmNewPriceFeed(lp, sender=governance.address)
    stored = curve.curveConfig(lp)
    assert stored.pool == pool.address
    assert stored.lpToken == lp.address
    assert stored.numUnderlying == 4
    assert [str(a).lower() for a in stored.underlying] == [
        str(alpha_token.address).lower(),
        str(bravo_token.address).lower(),
        str(charlie_token.address).lower(),
        str(delta_token.address).lower(),
    ]
    assert curve.hasPriceFeed(lp)
    assert curve.getPrice(lp) != 0

    other_pool = boa.loads(CURVE_POOL)
    assert other_pool.address != pool.address
    mr.setN(4)
    mr.setCoins(
        [
            alpha_token.address,
            bravo_token.address,
            charlie_token.address,
            delta_token.address,
            extra[0],
            extra[1],
            extra[2],
            extra[3],
        ]
    )
    for token in (alpha_token, bravo_token, charlie_token, delta_token):
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
    assert curve.updatePriceFeed(lp, other_pool, sender=governance.address)
    boa.env.time_travel(blocks=curve.actionTimeLock() + 1)
    mr.setN(5)
    mr.setCoins(drifted_coins)
    for token in (alpha_token, bravo_token, charlie_token, delta_token):
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
    assert curve.confirmPriceFeedUpdate(lp, sender=governance.address)
    updated = curve.curveConfig(lp)
    assert updated.pool == other_pool.address
    assert updated.numUnderlying == 4
    assert [str(a).lower() for a in updated.underlying] == [
        str(alpha_token.address).lower(),
        str(bravo_token.address).lower(),
        str(charlie_token.address).lower(),
        str(delta_token.address).lower(),
    ]
    assert curve.getPrice(lp) != 0


def test_stored_num_underlying_over_four_prices_zero(
    ripe_hq,
    governance,
    green_token,
    savings_green,
    mock_price_source,
    alpha_token,
    bravo_token,
    charlie_token,
    delta_token,
    fork,
):
    mr, ap, pool, lp, extra = _setup_system(
        alpha_token, bravo_token, charlie_token, delta_token, 4
    )
    curve = _load_curve(ripe_hq, green_token, savings_green, fork, ap)
    for token in (alpha_token, bravo_token, charlie_token, delta_token):
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
    assert curve.addNewPriceFeed(lp, pool, sender=governance.address)
    boa.env.time_travel(blocks=curve.actionTimeLock() + 1)
    for token in (alpha_token, bravo_token, charlie_token, delta_token):
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
    assert curve.confirmNewPriceFeed(lp, sender=governance.address)
    assert curve.getPrice(lp) != 0

    curve.eval(f"self.curveConfig[{lp.address}].numUnderlying = 5")
    assert curve.curveConfig(lp).numUnderlying == 5
    assert curve.getPrice(lp) == 0
    assert curve.getPriceAndHasFeed(lp) == (0, True)
    assert curve.hasPriceFeed(lp) is True


def test_update_rejects_five_through_eight_and_accepts_exactly_four(
    ripe_hq,
    governance,
    green_token,
    savings_green,
    mock_price_source,
    alpha_token,
    bravo_token,
    charlie_token,
    delta_token,
    fork,
):
    mr, ap, pool, lp, extra = _setup_system(
        alpha_token, bravo_token, charlie_token, delta_token, 4
    )
    curve = _load_curve(ripe_hq, green_token, savings_green, fork, ap)
    for token in (alpha_token, bravo_token, charlie_token, delta_token):
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
    assert curve.addNewPriceFeed(lp, pool, sender=governance.address)
    boa.env.time_travel(blocks=curve.actionTimeLock() + 1)
    for token in (alpha_token, bravo_token, charlie_token, delta_token):
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
    assert curve.confirmNewPriceFeed(lp, sender=governance.address)

    for n in range(5, 9):
        other_pool = boa.loads(CURVE_POOL)
        mr.setN(n)
        for token in (alpha_token, bravo_token, charlie_token, delta_token):
            mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
        assert not curve.isValidUpdateFeed(lp, other_pool)
        with boa.reverts("invalid feed"):
            curve.updatePriceFeed(lp, other_pool, sender=governance.address)

    four_pool = boa.loads(CURVE_POOL)
    mr.setN(4)
    for token in (alpha_token, bravo_token, charlie_token, delta_token):
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
    assert curve.isValidUpdateFeed(lp, four_pool)
    assert curve.updatePriceFeed(lp, four_pool, sender=governance.address)
    boa.env.time_travel(blocks=curve.actionTimeLock() + 1)
    for token in (alpha_token, bravo_token, charlie_token, delta_token):
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
    assert curve.confirmPriceFeedUpdate(lp, sender=governance.address)
    assert curve.curveConfig(lp).pool == four_pool.address
    assert curve.curveConfig(lp).numUnderlying == 4
    assert curve.getPrice(lp) != 0


def test_update_same_pool_nested_alt_rejected(
    ripe_hq,
    governance,
    green_token,
    savings_green,
    mock_price_source,
    alpha_token,
    bravo_token,
    charlie_token,
    delta_token,
    fork,
):
    mr, ap, pool_a, lp, extra = _setup_system(
        alpha_token, bravo_token, charlie_token, delta_token, 2
    )
    curve = _load_curve(ripe_hq, green_token, savings_green, fork, ap)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)

    assert curve.addNewPriceFeed(alpha_token, pool_a, sender=governance.address)
    boa.env.time_travel(blocks=curve.actionTimeLock() + 1)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    assert curve.confirmNewPriceFeed(alpha_token, sender=governance.address)

    # Admit BRAVO through an acyclic route first. The strict dependency-graph
    # check now rejects the former test setup (BRAVO -> ALPHA while the active
    # ALPHA route already depends on BRAVO) at proposal time.
    pool_b = boa.loads(CURVE_POOL)
    mr.setCoins(
        [bravo_token.address, charlie_token.address] + [ZERO_ADDRESS] * 6
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, EIGHTEEN_DECIMALS)
    assert curve.addNewPriceFeed(bravo_token, pool_b, sender=governance.address)
    boa.env.time_travel(blocks=curve.actionTimeLock() + 1)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, EIGHTEEN_DECIMALS)
    assert curve.confirmNewPriceFeed(bravo_token, sender=governance.address)

    # Reconstruct pool A as ALPHA/BRAVO. Updating BRAVO to it would make the
    # active ALPHA -> BRAVO edge recursive and must be rejected.
    mr.setCoins(
        [alpha_token.address, bravo_token.address] + [ZERO_ADDRESS] * 6
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    assert not curve.isValidUpdateFeed(bravo_token, pool_a)
    with boa.reverts("invalid feed"):
        curve.updatePriceFeed(bravo_token, pool_a, sender=governance.address)


def test_curve_fallback_after_earlier_source_returns_zero(
    ripe_hq,
    governance,
    green_token,
    savings_green,
    mock_price_source,
    price_desk,
    switchboard_alpha,
    mission_control,
    alpha_token,
    bravo_token,
    charlie_token,
    delta_token,
    fork,
):
    with boa.env.anchor():
        mr, ap, pool, lp, extra = _setup_system(
            alpha_token, bravo_token, charlie_token, delta_token, 4
        )
        curve = _load_curve(ripe_hq, green_token, savings_green, fork, ap)
        assert price_desk.startAddNewAddressToRegistry(
            curve, "curve fallback", sender=governance.address
        )
        boa.env.time_travel(blocks=price_desk.registryChangeTimeLock() + 1)
        curve_id = price_desk.confirmNewAddressToRegistry(curve, sender=governance.address)
        for token in (alpha_token, bravo_token, charlie_token, delta_token):
            mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
        mock_price_source.setPrice(lp, 7 * EIGHTEEN_DECIMALS)
        mission_control.setPriorityPriceSourceIds(
            [6, curve_id], sender=switchboard_alpha.address
        )
        assert curve.addNewPriceFeed(lp, pool, sender=governance.address)
        boa.env.time_travel(blocks=curve.actionTimeLock() + 1)
        for token in (alpha_token, bravo_token, charlie_token, delta_token):
            mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
        assert curve.confirmNewPriceFeed(lp, sender=governance.address)
        assert price_desk.getPrice(lp) == 7 * EIGHTEEN_DECIMALS
        mock_price_source.setPrice(lp, 0)
        mock_price_source.disablePriceFeed(lp)
        curve_price = curve.getPrice(lp)
        assert curve_price != 0
        assert price_desk.getPrice(lp) == curve_price
