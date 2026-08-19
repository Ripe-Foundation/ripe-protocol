import boa

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS


def test_calc_profit_returns_zero_when_ref_pool_unconfigured(endaoment, price_desk, curve_prices):
    assert price_desk.getAddr(2) == curve_prices.address
    assert curve_prices.getGreenStabilizerConfig().pool == boa.eval("empty(address)")
    assert endaoment.getGreenAmountToAddInStabilizer() == 0
    assert endaoment.getGreenAmountToRemoveInStabilizer() == 0
    assert endaoment.calcProfitForStabilizer() == 0


def test_disabled_slot_2_noops_all_four_endaoment_surfaces(
    endaoment, price_desk, governance, switchboard_delta
):
    with boa.env.anchor():
        assert endaoment.getGreenAmountToAddInStabilizer() == 0
        assert endaoment.getGreenAmountToRemoveInStabilizer() == 0
        assert endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address) is False
        assert endaoment.calcProfitForStabilizer() == 0

        assert price_desk.startAddressDisableInRegistry(2, sender=governance.address)
        boa.env.time_travel(blocks=price_desk.registryChangeTimeLock() + 1)
        assert price_desk.confirmAddressDisableInRegistry(2, sender=governance.address)
        assert price_desk.getAddr(2) == boa.eval("empty(address)")

        assert endaoment.getGreenAmountToAddInStabilizer() == 0
        assert endaoment.getGreenAmountToRemoveInStabilizer() == 0
        assert endaoment.calcProfitForStabilizer() == 0
        assert endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address) is False


def test_paused_curve_get_green_stabilizer_config_still_serves_configured_pool(
    governance,
    green_token,
    savings_green,
    switchboard_alpha,
):
    alt = boa.load(
        "contracts/mock/MockErc20.vy",
        governance,
        "ALT",
        "ALT",
        18,
        1_000_000_000,
        name="paused_curve_alt",
    )
    pool = boa.load("contracts/mock/MockCurveRefPool.vy")
    registry = boa.load(
        "contracts/mock/MockCurveRefPoolRegistry.vy",
        governance.address,
        green_token,
        savings_green,
        governance.address,
    )
    registry.setPool(pool, alt, green_token)
    registry.setValidRipeAddr(switchboard_alpha.address, True)
    curve = boa.load(
        "contracts/priceSources/CurvePrices.vy",
        registry,
        ZERO_ADDRESS,
        registry,
        green_token,
        savings_green,
        1,
        100,
        name="paused_curve_ref_views",
    )
    assert curve.setActionTimeLockAfterSetup(sender=governance.address)
    pool.setBalances(10_000 * EIGHTEEN_DECIMALS, 10_000 * EIGHTEEN_DECIMALS)
    aid = curve.setGreenRefPoolConfig(
        pool,
        10,
        60_00,
        0,
        10_00,
        100_000 * EIGHTEEN_DECIMALS,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=curve.actionTimeLock())
    assert curve.confirmGreenRefPoolConfig(aid, sender=governance.address)
    before = curve.getGreenStabilizerConfig()
    assert before.pool == pool.address
    assert before.greenBalance != 0

    curve.pause(True, sender=switchboard_alpha.address)
    assert curve.isPaused()
    after = curve.getGreenStabilizerConfig()
    assert after.pool == before.pool
    assert after.greenBalance == before.greenBalance
    assert after.greenRatio == before.greenRatio
    assert after.lpToken == before.lpToken
