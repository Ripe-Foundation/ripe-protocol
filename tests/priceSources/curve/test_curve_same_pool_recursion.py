import boa

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS
from priceSources.curve.test_curve_rejects_more_than_four_underlyings import (
    _load_curve,
    _setup_system,
)
from priceSources.curve.test_robinhood_launch_route import (  # noqa: F401
    robinhood_curve_launch_route,
)


def _refresh_usdg_feed(route, answer=100_000_000):
    route.feed.setMockData(answer, 1, 1, boa.env.timestamp, boa.env.timestamp)


def test_curve_rejects_usdg_feed_on_same_green_pool(robinhood_curve_launch_route):
    route = robinhood_curve_launch_route
    assert route.curve.hasPriceFeed(route.green)
    assert not route.curve.hasPriceFeed(route.usdg)
    _refresh_usdg_feed(route)
    assert not route.curve.isValidNewFeed(route.usdg, route.curve_system)
    with boa.reverts("invalid pool"):
        route.curve.addNewPriceFeed(
            route.usdg, route.curve_system, sender=route.governance.address
        )


def test_curve_rejects_green_after_usdg_same_pool(
    robinhood_curve_launch_route,
    mock_price_source,
    switchboard_alpha,
    mission_control,
):
    route = robinhood_curve_launch_route
    assert route.curve.hasPriceFeed(route.green)
    assert route.curve.disablePriceFeed(route.green, sender=route.governance.address)
    boa.env.time_travel(blocks=route.curve.actionTimeLock() + 1)
    assert route.curve.confirmDisablePriceFeed(route.green, sender=route.governance.address)
    assert not route.curve.hasPriceFeed(route.green)

    mock_price_source.setPrice(route.green, EIGHTEEN_DECIMALS)
    mission_control.setPriorityPriceSourceIds([1, 6], sender=switchboard_alpha.address)
    _refresh_usdg_feed(route)
    assert route.curve.isValidNewFeed(route.usdg, route.curve_system)
    assert route.curve.addNewPriceFeed(
        route.usdg, route.curve_system, sender=route.governance.address
    )
    boa.env.time_travel(blocks=route.curve.actionTimeLock() + 1)
    _refresh_usdg_feed(route)
    assert route.curve.confirmNewPriceFeed(route.usdg, sender=route.governance.address)
    assert route.curve.hasPriceFeed(route.usdg)

    _refresh_usdg_feed(route)
    assert not route.curve.isValidNewFeed(route.green, route.curve_system)
    with boa.reverts("invalid pool"):
        route.curve.addNewPriceFeed(
            route.green, route.curve_system, sender=route.governance.address
        )


def test_curve_confirm_cancels_when_alt_admitted_during_timelock(
    robinhood_curve_launch_route,
    mock_price_source,
    switchboard_alpha,
    mission_control,
):
    route = robinhood_curve_launch_route
    assert route.curve.hasPriceFeed(route.green)
    assert route.curve.disablePriceFeed(route.green, sender=route.governance.address)
    boa.env.time_travel(blocks=route.curve.actionTimeLock() + 1)
    assert route.curve.confirmDisablePriceFeed(route.green, sender=route.governance.address)

    mock_price_source.setPrice(route.green, EIGHTEEN_DECIMALS)
    mission_control.setPriorityPriceSourceIds([1, 6], sender=switchboard_alpha.address)
    _refresh_usdg_feed(route)
    assert route.curve.addNewPriceFeed(
        route.usdg, route.curve_system, sender=route.governance.address
    )
    _refresh_usdg_feed(route)
    assert route.curve.addNewPriceFeed(
        route.green, route.curve_system, sender=route.governance.address
    )
    boa.env.time_travel(blocks=route.curve.actionTimeLock() + 1)
    _refresh_usdg_feed(route)
    assert route.curve.confirmNewPriceFeed(route.usdg, sender=route.governance.address)
    _refresh_usdg_feed(route)
    assert not route.curve.confirmNewPriceFeed(route.green, sender=route.governance.address)
    assert route.curve.hasPriceFeed(route.usdg)
    assert not route.curve.hasPriceFeed(route.green)


def test_curve_rejects_green_lp_with_sgreen_underlying(
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
    with boa.env.anchor():
        coins8 = [savings_green.address, alpha_token.address] + [ZERO_ADDRESS] * 6
        mr, ap, pool, lp, extra = _setup_system(
            alpha_token,
            bravo_token,
            charlie_token,
            delta_token,
            2,
            coins8=coins8,
            lp=green_token.address,
        )
        curve = _load_curve(ripe_hq, green_token, savings_green, fork, ap)
        mock_price_source.setPrice(savings_green, EIGHTEEN_DECIMALS)
        mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
        assert not curve.isValidNewFeed(green_token, pool)
        with boa.reverts("invalid pool"):
            curve.addNewPriceFeed(green_token, pool, sender=governance.address)


def test_sgreen_nested_alt_uses_green_curve_config(
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
    with boa.env.anchor():
        coins8 = [green_token.address, alpha_token.address] + [ZERO_ADDRESS] * 6
        mr, ap, pool, lp, extra = _setup_system(
            alpha_token,
            bravo_token,
            charlie_token,
            delta_token,
            2,
            coins8=coins8,
        )
        curve = _load_curve(ripe_hq, green_token, savings_green, fork, ap)
        mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)
        mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
        assert curve.addNewPriceFeed(green_token, pool, sender=governance.address)
        boa.env.time_travel(blocks=curve.actionTimeLock() + 1)
        mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)
        mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
        assert curve.confirmNewPriceFeed(green_token, sender=governance.address)
        assert curve.curveConfig(green_token).pool == pool.address

        mr.setCoins([savings_green.address, alpha_token.address] + [ZERO_ADDRESS] * 6)
        mock_price_source.setPrice(savings_green, EIGHTEEN_DECIMALS)
        mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
        assert not curve.isValidNewFeed(alpha_token, pool)
        with boa.reverts("invalid pool"):
            curve.addNewPriceFeed(alpha_token, pool, sender=governance.address)


def test_curve_rejects_green_sgreen_two_coin_single_asset(
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
    with boa.env.anchor():
        coins8 = [green_token.address, savings_green.address] + [ZERO_ADDRESS] * 6
        mr, ap, pool, lp, extra = _setup_system(
            alpha_token,
            bravo_token,
            charlie_token,
            delta_token,
            2,
            coins8=coins8,
        )
        curve = _load_curve(ripe_hq, green_token, savings_green, fork, ap)
        mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)
        mock_price_source.setPrice(savings_green, EIGHTEEN_DECIMALS)
        assert not curve.isValidNewFeed(green_token, pool)
        assert not curve.isValidNewFeed(savings_green, pool)
        with boa.reverts("invalid pool"):
            curve.addNewPriceFeed(green_token, pool, sender=governance.address)
        with boa.reverts("invalid pool"):
            curve.addNewPriceFeed(savings_green, pool, sender=governance.address)


def test_curve_self_recursive_green_lp_fail_closes_on_pricedesk(
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
        coins8 = [green_token.address, alpha_token.address] + [ZERO_ADDRESS] * 6
        mr, ap, pool, lp, extra = _setup_system(
            alpha_token,
            bravo_token,
            charlie_token,
            delta_token,
            2,
            coins8=coins8,
        )
        curve = _load_curve(ripe_hq, green_token, savings_green, fork, ap)
        assert price_desk.startAddNewAddressToRegistry(
            curve, "curve sgreen recursion", sender=governance.address
        )
        boa.env.time_travel(blocks=price_desk.registryChangeTimeLock() + 1)
        curve_id = price_desk.confirmNewAddressToRegistry(curve, sender=governance.address)
        mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)
        mock_price_source.setPrice(savings_green, EIGHTEEN_DECIMALS)
        mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
        mission_control.setPriorityPriceSourceIds(
            [6, curve_id], sender=switchboard_alpha.address
        )
        assert curve.addNewPriceFeed(green_token, pool, sender=governance.address)
        boa.env.time_travel(blocks=curve.actionTimeLock() + 1)
        mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)
        mock_price_source.setPrice(savings_green, EIGHTEEN_DECIMALS)
        mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
        assert curve.confirmNewPriceFeed(green_token, sender=governance.address)

        curve.eval(f"self.curveConfig[{green_token.address}].lpToken = {green_token.address}")
        curve.eval(
            f"self.curveConfig[{green_token.address}].underlying[0] = {savings_green.address}"
        )
        mock_price_source.setPrice(green_token, 0)
        mock_price_source.disablePriceFeed(green_token)
        coins = [savings_green.address, alpha_token.address, ZERO_ADDRESS, ZERO_ADDRESS]
        assert curve.getStableLpPrice(pool, coins) != 0
        assert curve.getPrice(green_token) == 0
        assert price_desk.getPrice(green_token) == 0


def test_curve_rejects_direct_sgreen_new_feed(
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
    with boa.env.anchor():
        coins8 = [savings_green.address, alpha_token.address] + [ZERO_ADDRESS] * 6
        mr, ap, pool, lp, extra = _setup_system(
            alpha_token,
            bravo_token,
            charlie_token,
            delta_token,
            2,
            coins8=coins8,
        )
        curve = _load_curve(ripe_hq, green_token, savings_green, fork, ap)
        mock_price_source.setPrice(savings_green, EIGHTEEN_DECIMALS)
        mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)

        cfg = curve.getCurvePoolConfig(pool)
        assert cfg.pool == pool.address
        assert cfg.numUnderlying == 2
        assert savings_green.address in cfg.underlying
        assert alpha_token.address in cfg.underlying
        assert cfg.lpToken == lp
        assert cfg.lpToken not in (green_token.address, savings_green.address)
        assert mock_price_source.getPrice(alpha_token) != 0
        # Same reconstructed pool is admissible for the non-sGREEN member.
        assert curve.isValidNewFeed(alpha_token, pool)

        assert not curve.isValidNewFeed(savings_green, pool)
        with boa.reverts("invalid pool"):
            curve.addNewPriceFeed(savings_green, pool, sender=governance.address)
        assert not curve.hasPendingPriceFeedUpdate(savings_green)
        assert curve.pendingUpdates(savings_green).actionId == 0
        assert curve.curveConfig(savings_green).pool == ZERO_ADDRESS
        assert curve.indexOfAsset(savings_green) == 0


def test_curve_rejects_legacy_direct_sgreen_update_but_allows_disable(
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
    with boa.env.anchor():
        coins8 = [savings_green.address, alpha_token.address] + [ZERO_ADDRESS] * 6
        mr, ap, pool, lp, extra = _setup_system(
            alpha_token,
            bravo_token,
            charlie_token,
            delta_token,
            2,
            coins8=coins8,
        )
        curve = _load_curve(ripe_hq, green_token, savings_green, fork, ap)
        mock_price_source.setPrice(savings_green, EIGHTEEN_DECIMALS)
        mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)

        legacy_pool = boa.env.generate_address("legacy_sgreen_pool")
        legacy_lp = boa.env.generate_address("legacy_sgreen_lp")
        assert legacy_pool != pool.address
        curve.eval(
            f"self.curveConfig[{savings_green.address}] = CurvePriceConfig("
            f"pool={legacy_pool}, "
            f"lpToken={legacy_lp}, "
            f"numUnderlying=2, "
            f"underlying=[{savings_green.address}, {alpha_token.address}, empty(address), empty(address)], "
            f"poolType=PoolType.STABLESWAP_NG, "
            f"hasEcoToken=True)"
        )
        curve.eval(f"priceData._addPricedAsset({savings_green.address})")

        assert curve.indexOfAsset(savings_green) != 0
        assert curve.curveConfig(savings_green).pool == legacy_pool
        replacement = curve.getCurvePoolConfig(pool)
        assert replacement.pool == pool.address
        assert replacement.pool != legacy_pool
        assert savings_green.address in replacement.underlying
        assert alpha_token.address in replacement.underlying
        assert replacement.lpToken not in (green_token.address, savings_green.address)
        assert mock_price_source.getPrice(alpha_token) != 0
        assert curve.isValidNewFeed(alpha_token, pool)

        assert not curve.isValidUpdateFeed(savings_green, pool)
        with boa.reverts("invalid feed"):
            curve.updatePriceFeed(savings_green, pool, sender=governance.address)
        assert not curve.hasPendingPriceFeedUpdate(savings_green)
        assert curve.curveConfig(savings_green).pool == legacy_pool

        assert curve.isValidDisablePriceFeed(savings_green)
        assert curve.disablePriceFeed(savings_green, sender=governance.address)
        boa.env.time_travel(blocks=curve.actionTimeLock() + 1)
        assert curve.confirmDisablePriceFeed(savings_green, sender=governance.address)
        assert curve.curveConfig(savings_green).pool == ZERO_ADDRESS
        assert curve.indexOfAsset(savings_green) == 0


def test_sgreen_price_derives_through_green_config(
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
    with boa.env.anchor():
        coins8 = [green_token.address, alpha_token.address] + [ZERO_ADDRESS] * 6
        mr, ap, pool, lp, extra = _setup_system(
            alpha_token,
            bravo_token,
            charlie_token,
            delta_token,
            2,
            coins8=coins8,
        )
        curve = _load_curve(ripe_hq, green_token, savings_green, fork, ap)
        mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)

        assert curve.isValidNewFeed(green_token, pool)
        assert curve.addNewPriceFeed(green_token, pool, sender=governance.address)
        boa.env.time_travel(blocks=curve.actionTimeLock() + 1)
        mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
        assert curve.confirmNewPriceFeed(green_token, sender=governance.address)

        green_price = curve.getPrice(green_token)
        sgreen_price = curve.getPrice(savings_green)
        assert green_price != 0
        assert sgreen_price != 0
        assert sgreen_price == green_price
        assert curve.hasPriceFeed(green_token)
        assert curve.hasPriceFeed(savings_green)
        assert curve.curveConfig(green_token).pool == pool.address
        assert curve.curveConfig(savings_green).pool == ZERO_ADDRESS
