from types import SimpleNamespace

import boa
import pytest

from config import BluePrint as source_blueprint
from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS


@pytest.fixture
def robinhood_curve_launch_route(
    ripe_hq_deploy,
    price_desk,
    chainlink,
    green_token,
    savings_green,
    deploy3r,
    governance,
    mock_price_source,
    switchboard_alpha,
):
    with boa.env.anchor():
        # Prevent a session-scoped generic test source from masking failure.
        mock_price_source.disablePriceFeed(green_token)

        usdg = boa.load(
            "contracts/mock/MockErc20.vy",
            deploy3r,
            "Robinhood USDG",
            "USDG",
            6,
            0,
            name="robinhood_curve_route_usdg",
        )
        feed = boa.load(
            "contracts/mock/MockChainlinkFeed.vy",
            EIGHTEEN_DECIMALS,
            name="robinhood_curve_route_usdg_feed",
        )
        assert chainlink.addNewPriceFeed(
            usdg,
            feed,
            86_400,
            False,
            False,
            sender=governance.address,
        )
        boa.env.time_travel(blocks=chainlink.actionTimeLock() + 1)
        feed.setMockData(
            100_000_000,
            1,
            1,
            boa.env.timestamp,
            boa.env.timestamp,
        )
        assert chainlink.confirmNewPriceFeed(usdg, sender=governance.address)

        curve_system = boa.load(
            "contracts/mock/MockRobinhoodCurveSystem.vy",
            usdg,
            green_token,
            EIGHTEEN_DECIMALS,
            name="robinhood_curve_route_system",
        )
        curve = boa.load(
            "contracts/priceSources/CurvePrices.vy",
            ripe_hq_deploy,
            ZERO_ADDRESS,
            curve_system,
            green_token,
            savings_green,
            10,
            1_000,
            name="robinhood_curve_route_prices",
        )
        assert curve.addNewPriceFeed(
            green_token, curve_system, sender=governance.address
        )
        boa.env.time_travel(blocks=curve.actionTimeLock() + 1)
        assert curve.confirmNewPriceFeed(
            green_token, sender=governance.address
        )
        assert curve.setActionTimeLockAfterSetup(sender=governance.address)

        if price_desk.getAddr(2) != curve.address:
            assert price_desk.startAddressUpdateToRegistry(
                2, curve, sender=governance.address
            )
            boa.env.time_travel(blocks=price_desk.registryChangeTimeLock() + 1)
            assert price_desk.confirmAddressUpdateToRegistry(
                2, sender=governance.address
            )

        priority_action = switchboard_alpha.setPriorityPriceSourceIds(
            [1, 2], sender=governance.address
        )
        boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock() + 1)
        assert switchboard_alpha.executePendingAction(
            priority_action, sender=governance.address
        )
        feed.setMockData(
            100_000_000,
            1,
            1,
            boa.env.timestamp,
            boa.env.timestamp,
        )

        yield SimpleNamespace(
            usdg=usdg,
            feed=feed,
            curve_system=curve_system,
            curve=curve,
            price_desk=price_desk,
            chainlink=chainlink,
            green=green_token,
            governance=governance,
        )


def test_green_route_uses_curve_and_chainlink_usdg_without_recursion(
    robinhood_curve_launch_route,
    mission_control,
):
    route = robinhood_curve_launch_route
    assert route.price_desk.getAddr(1) == route.chainlink.address
    assert route.price_desk.getAddr(2) == route.curve.address
    assert route.price_desk.getAddr(3) != ZERO_ADDRESS
    assert tuple(mission_control.getPriceConfig().priorityPriceSourceIds) == (1, 2)

    config = route.curve.curveConfig(route.green)
    assert config.pool == route.curve_system.address
    assert config.lpToken == route.curve_system.address
    assert config.numUnderlying == 2
    assert config.underlying[0] == route.usdg.address
    assert config.underlying[1] == route.green.address
    assert route.usdg.decimals() == 6
    assert route.green.decimals() == 18

    assert route.chainlink.hasPriceFeed(route.usdg)
    assert not route.curve.hasPriceFeed(route.usdg)
    assert route.curve.getPriceAndHasFeed(route.usdg) == (0, False)
    assert route.price_desk.getPrice(route.usdg, True) == EIGHTEEN_DECIMALS
    assert route.price_desk.getPrice(route.green, True) == EIGHTEEN_DECIMALS

    authority = {
        row.input_id: row.value
        for row in source_blueprint.ROBINHOOD_CURVE_LAUNCH_INPUTS
    }
    assert authority["feed.curve_assets"] == ("GREEN",)
    assert authority["feed.usdg_curve_feed"] is False
    assert authority["feed.route"] == (
        "GREEN",
        "Curve:GREEN/USDG",
        "PriceDesk",
        "Chainlink:USDG/USD",
    )


@pytest.mark.parametrize("failure", ("zero_pool", "zero_chainlink", "stale_chainlink"))
def test_configured_green_feed_safe_and_unsafe_modes_fail_without_fabrication(
    robinhood_curve_launch_route,
    failure,
):
    route = robinhood_curve_launch_route
    if failure == "zero_pool":
        route.curve_system.setOraclePrice(0)
    elif failure == "zero_chainlink":
        route.feed.setMockData(0)
    else:
        route.feed.setMockData(100_000_000, 1, 1, 1, 1)

    assert route.price_desk.getPrice(route.green, False) == 0
    with boa.reverts("has price config, no price"):
        route.price_desk.getPrice(route.green, True)


def test_reverting_pool_response_isolated_by_strictness(
    robinhood_curve_launch_route,
):
    route = robinhood_curve_launch_route
    route.curve_system.setShouldRevert(True)
    assert route.price_desk.getPrice(route.green, False) == 0
    with boa.reverts("has price config, no price"):
        route.price_desk.getPrice(route.green, True)


def test_missing_uninitialized_and_incompatible_pool_responses_fail_closed(
    robinhood_curve_launch_route,
    ripe_hq_deploy,
    savings_green,
    mock_rando_contract,
):
    route = robinhood_curve_launch_route
    uninitialized = boa.load(
        "contracts/priceSources/CurvePrices.vy",
        ripe_hq_deploy,
        ZERO_ADDRESS,
        route.curve_system,
        route.green,
        savings_green,
        10,
        1_000,
        name="robinhood_curve_uninitialized_prices",
    )
    assert uninitialized.getPriceAndHasFeed(route.green) == (0, False)

    route.curve_system.setRegistered(False)
    empty_config = uninitialized.getCurvePoolConfig(route.curve_system)
    assert empty_config.pool == ZERO_ADDRESS
    assert not uninitialized.isValidNewFeed(route.green, route.curve_system)

    route.curve_system.setRegistered(True)
    route.curve_system.setRegisteredPool(mock_rando_contract)
    with boa.reverts():
        uninitialized.isValidNewFeed(route.green, mock_rando_contract)
    assert uninitialized.getPriceAndHasFeed(route.green) == (0, False)


def test_pause_disable_repair_and_reenable_order_preserves_safe_green_failure(
    robinhood_curve_launch_route,
    switchboard_alpha,
):
    route = robinhood_curve_launch_route
    assert route.price_desk.getPrice(route.green, True) == EIGHTEEN_DECIMALS

    route.curve.pause(True, sender=switchboard_alpha.address)
    assert route.curve.isPaused()
    # Pause blocks configuration and snapshots, not ordinary view pricing.
    with boa.reverts("contract paused"):
        route.curve.addNewPriceFeed(
            route.usdg,
            route.curve_system,
            sender=route.governance.address,
        )
    assert not route.curve.addGreenRefPoolSnapshot(
        sender=switchboard_alpha.address
    )
    assert route.price_desk.getPrice(route.green, True) == EIGHTEEN_DECIMALS

    assert route.price_desk.startAddressDisableInRegistry(
        2, sender=route.governance.address
    )
    boa.env.time_travel(blocks=route.price_desk.registryChangeTimeLock() + 1)
    route.feed.setMockData(
        100_000_000, 1, 1, boa.env.timestamp, boa.env.timestamp
    )
    assert route.price_desk.confirmAddressDisableInRegistry(
        2, sender=route.governance.address
    )
    assert route.price_desk.getAddr(2) == ZERO_ADDRESS
    assert route.price_desk.getPrice(route.green, False) == 0
    assert route.price_desk.getPrice(route.green, True) == 0
    assert route.price_desk.getPrice(route.usdg, True) == EIGHTEEN_DECIMALS

    # Repair checks happen while Curve remains excluded from PriceDesk.
    assert route.curve.getPrice(
        route.green, 0, route.price_desk
    ) == EIGHTEEN_DECIMALS
    assert route.curve.greenRefPoolConfig().pool == ZERO_ADDRESS
    assert not route.curve.hasPriceFeed(route.usdg)
    route.curve.pause(False, sender=switchboard_alpha.address)
    assert not route.curve.isPaused()

    assert route.price_desk.startAddressUpdateToRegistry(
        2, route.curve, sender=route.governance.address
    )
    boa.env.time_travel(blocks=route.price_desk.registryChangeTimeLock() + 1)
    route.feed.setMockData(
        100_000_000, 1, 1, boa.env.timestamp, boa.env.timestamp
    )
    assert route.price_desk.confirmAddressUpdateToRegistry(
        2, sender=route.governance.address
    )
    assert route.price_desk.getAddr(2) == route.curve.address
    assert route.price_desk.getPrice(route.green, True) == EIGHTEEN_DECIMALS
