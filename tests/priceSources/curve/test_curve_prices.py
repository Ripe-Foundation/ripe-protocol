import pytest
import boa

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS, CURVE_POOL_TYPE_STABLESWAP_NG, CURVE_POOL_TYPE_TWO_CRYPTO_NG, CURVE_POOL_TYPE_TWO_CRYPTO
from config.BluePrint import CORE_TOKENS, CURVE_PARAMS, ADDYS, WHALES
from conf_utils import filter_logs


##############
# Green Pool #
##############


@pytest.fixture(scope="module")
def deployed_green_pool(
    green_token,
    deploy3r,
    usdc_token,
    fork,
):
    factory = boa.from_etherscan(ADDYS[fork]["CURVE_STABLE_FACTORY"])

    implementation_idx = 0
    blueprint_address = factory.pool_implementations(implementation_idx)
    blueprint = boa.from_etherscan(blueprint_address, "green pool").deployer

    green_pool_deploy = factory.deploy_plain_pool(
        CURVE_PARAMS[fork]["GREEN_POOL_NAME"],
        CURVE_PARAMS[fork]["GREEN_POOL_SYMBOL"],
        [usdc_token, green_token],
        CURVE_PARAMS[fork]["GREEN_POOL_A"],
        CURVE_PARAMS[fork]["GREEN_POOL_FEE"],
        CURVE_PARAMS[fork]["GREEN_POOL_OFFPEG_MULTIPLIER"],
        CURVE_PARAMS[fork]["GREEN_POOL_MA_EXP_TIME"],
        implementation_idx,
        [0, 0],
        [b"", b""],
        [ZERO_ADDRESS, ZERO_ADDRESS],
        sender=deploy3r,
    )
    blueprint.at(green_pool_deploy) # register for later lookup_contract
    return green_pool_deploy


@pytest.fixture(scope="module")
def addSeedGreenLiq(
    green_token,
    deployed_green_pool,
    whale,
    fork,
    usdc_token,
    bob,
):
    def addSeedGreenLiq():
        green_pool = boa.env.lookup_contract(deployed_green_pool)

        # usdc
        usdc_amount = 100_000 * (10 ** usdc_token.decimals())
        usdc_token.transfer(bob, usdc_amount, sender=WHALES[fork]["usdc"])
        usdc_token.approve(green_pool, usdc_amount, sender=bob)

        # green
        green_amount = 100_000 * EIGHTEEN_DECIMALS
        green_token.transfer(bob, green_amount, sender=whale)
        green_token.approve(green_pool, green_amount, sender=bob)

        # add liquidity
        green_pool.add_liquidity([usdc_amount, green_amount], 0, bob, sender=bob)

    yield addSeedGreenLiq


@pytest.base
def test_add_curve_price_green_single_asset(
    green_token,
    deployed_green_pool,
    curve_prices,
    governance,
    usdc_token,
):
    assert curve_prices.isValidNewFeed(green_token, deployed_green_pool)

    # add new price feed
    assert curve_prices.addNewPriceFeed(green_token, deployed_green_pool, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock() + 1)
    assert curve_prices.confirmNewPriceFeed(green_token, sender=governance.address)

    log = filter_logs(curve_prices, "NewCurvePriceAdded")[0]

    # verify config
    config = curve_prices.curveConfig(green_token)
    assert config.pool == deployed_green_pool
    assert config.lpToken == deployed_green_pool
    assert config.numUnderlying == 2
    assert config.underlying[0] == usdc_token.address
    assert config.underlying[1] == green_token.address
    assert config.poolType == CURVE_POOL_TYPE_STABLESWAP_NG
    assert config.hasEcoToken == True

    # verify event
    assert log.asset == green_token.address
    assert log.pool == deployed_green_pool


@pytest.base
def test_get_price_green_single_asset(
    usdc_token, # load alt price
    deployed_green_pool,
    green_token,
    curve_prices,
    governance,
):
    # setup
    assert curve_prices.addNewPriceFeed(green_token, deployed_green_pool, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock() + 1)
    assert curve_prices.confirmNewPriceFeed(green_token, sender=governance.address)

    price = curve_prices.getPrice(green_token)
    assert price != 0


@pytest.base
def test_add_curve_price_green_lp(
    deployed_green_pool,
    curve_prices,
    governance,
    usdc_token,
    green_token,
    addSeedGreenLiq,
    mock_price_source,
):
    addSeedGreenLiq() # need to add liquidity to pool
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS) # green needs a price

    assert curve_prices.isValidNewFeed(deployed_green_pool, deployed_green_pool)

    # add new price feed
    assert curve_prices.addNewPriceFeed(deployed_green_pool, deployed_green_pool, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock() + 1)
    assert curve_prices.confirmNewPriceFeed(deployed_green_pool, sender=governance.address)

    log = filter_logs(curve_prices, "NewCurvePriceAdded")[0]

    # verify config
    config = curve_prices.curveConfig(deployed_green_pool)
    assert config.pool == deployed_green_pool
    assert config.lpToken == deployed_green_pool
    assert config.numUnderlying == 2
    assert config.underlying[0] == usdc_token.address
    assert config.underlying[1] == green_token.address
    assert config.poolType == CURVE_POOL_TYPE_STABLESWAP_NG
    assert config.hasEcoToken == True

    # verify event
    assert log.asset == deployed_green_pool
    assert log.pool == deployed_green_pool


@pytest.base
def test_get_price_green_lp(
    usdc_token, # load alt price
    deployed_green_pool,
    curve_prices,
    governance,
    addSeedGreenLiq,
    mock_price_source,
    green_token,
):
    addSeedGreenLiq() # need to add liquidity to pool
    mock_price_source.setPrice(green_token, 1 * EIGHTEEN_DECIMALS) # green needs a price

    # setup
    assert curve_prices.addNewPriceFeed(deployed_green_pool, deployed_green_pool, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock() + 1)
    assert curve_prices.confirmNewPriceFeed(deployed_green_pool, sender=governance.address)

    price = curve_prices.getPrice(deployed_green_pool)
    assert price != 0


@pytest.base
def test_green_pool_imbalanced(
    usdc_token, # load alt price
    deployed_green_pool,
    curve_prices,
    governance,
    addSeedGreenLiq,
    green_token,
    _test,
    bob,
    whale,
):
    addSeedGreenLiq() # need to add liquidity to pool
    green_pool = boa.env.lookup_contract(deployed_green_pool)

    # setup green price
    assert curve_prices.addNewPriceFeed(green_token, green_pool, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock() + 1)
    assert curve_prices.confirmNewPriceFeed(green_token, sender=governance.address)

    # setup green lp price
    assert curve_prices.addNewPriceFeed(green_pool, green_pool, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock() + 1)
    assert curve_prices.confirmNewPriceFeed(green_pool, sender=governance.address)

    # initial prices
    orig_green_price = curve_prices.getPrice(green_token)
    _test(orig_green_price, 10 ** 18)
    orig_green_lp_price = curve_prices.getPrice(green_pool)
    _test(orig_green_lp_price, 10 ** 18)

    # swap amount
    swap_amount = 80_000 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, swap_amount, sender=whale)
    green_token.approve(green_pool, swap_amount, sender=bob)
    green_pool.exchange(1, 0, swap_amount, 0, bob, sender=bob)

    boa.env.time_travel(blocks=100)

    assert curve_prices.getPrice(green_token) < orig_green_price
    assert curve_prices.getPrice(green_pool) < orig_green_lp_price


#############
# Ripe Pool #
#############


@pytest.fixture(scope="module")
def deployed_ripe_pool(
    ripe_token,
    deploy3r,
    weth_token,
    fork,
):
    factory = boa.from_etherscan(ADDYS[fork]["CURVE_CRYPTO_FACTORY"])
    implementation_idx = 0
    blueprint_address = factory.pool_implementations(implementation_idx)
    blueprint = boa.from_etherscan(blueprint_address, "ripe pool").deployer

    ripe_pool_deploy = factory.deploy_pool(
        CURVE_PARAMS[fork]["RIPE_POOL_NAME"],
        CURVE_PARAMS[fork]["RIPE_POOL_SYMBOL"],
        [weth_token, ripe_token],
        implementation_idx,
        CURVE_PARAMS[fork]["RIPE_POOL_A"],
        CURVE_PARAMS[fork]["RIPE_POOL_GAMMA"],
        CURVE_PARAMS[fork]["RIPE_POOL_MID_FEE"],
        CURVE_PARAMS[fork]["RIPE_POOL_OUT_FEE"],
        CURVE_PARAMS[fork]["RIPE_POOL_FEE_GAMMA"],
        CURVE_PARAMS[fork]["RIPE_POOL_EXTRA_PROFIT"],
        CURVE_PARAMS[fork]["RIPE_POOL_ADJ_STEP"],
        CURVE_PARAMS[fork]["RIPE_POOL_MA_EXP_TIME"],
        CURVE_PARAMS[fork]["RIPE_POOL_INIT_PRICE"],
        sender=deploy3r,
    )
    blueprint.at(ripe_pool_deploy) # register for later lookup_contract
    return ripe_pool_deploy


@pytest.fixture(scope="module")
def addSeedRipeLiq(
    weth_token,
    ripe_token,
    deployed_ripe_pool,
    price_desk,
    whale,
    fork,
    bob,
):
    def addSeedRipeLiq():
        ripe_pool = boa.env.lookup_contract(deployed_ripe_pool)

        weth_amount = 1 * EIGHTEEN_DECIMALS
        weth_token.transfer(bob, weth_amount, sender=WHALES[fork]["weth"])
        weth_token.approve(ripe_pool, weth_amount, sender=bob)

        # ripe
        ripe_amount = price_desk.getPrice(weth_token) * weth_amount // CURVE_PARAMS[fork]["RIPE_POOL_INIT_PRICE"]
        ripe_token.transfer(bob, ripe_amount, sender=whale)
        ripe_token.approve(ripe_pool, ripe_amount, sender=bob)

        # add liquidity
        ripe_pool.add_liquidity([weth_amount, ripe_amount], 0, bob, sender=bob)

    yield addSeedRipeLiq


@pytest.base
def test_add_curve_price_ripe_single_asset(
    ripe_token,
    deployed_ripe_pool,
    curve_prices,
    governance,
    weth_token,
):
    assert curve_prices.isValidNewFeed(ripe_token, deployed_ripe_pool)

    # add new price feed
    assert curve_prices.addNewPriceFeed(ripe_token, deployed_ripe_pool, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock() + 1)
    assert curve_prices.confirmNewPriceFeed(ripe_token, sender=governance.address)

    log = filter_logs(curve_prices, "NewCurvePriceAdded")[0]

    # verify config
    config = curve_prices.curveConfig(ripe_token)
    assert config.pool == deployed_ripe_pool
    assert config.lpToken == deployed_ripe_pool
    assert config.numUnderlying == 2
    assert config.underlying[0] == weth_token.address
    assert config.underlying[1] == ripe_token.address
    assert config.poolType == CURVE_POOL_TYPE_TWO_CRYPTO_NG
    assert config.hasEcoToken == True

    # verify event
    assert log.asset == ripe_token.address
    assert log.pool == deployed_ripe_pool


@pytest.base
def test_get_price_ripe_single_asset(
    weth_token, # load alt price
    deployed_ripe_pool,
    ripe_token,
    curve_prices,
    governance,
):
    # setup
    assert curve_prices.addNewPriceFeed(ripe_token, deployed_ripe_pool, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock() + 1)
    assert curve_prices.confirmNewPriceFeed(ripe_token, sender=governance.address)

    price = curve_prices.getPrice(ripe_token)
    assert price != 0


@pytest.base
def test_add_curve_price_ripe_lp(
    deployed_ripe_pool,
    curve_prices,
    governance,
    weth_token,
    ripe_token,
    addSeedRipeLiq,
):
    addSeedRipeLiq() # need to add liquidity to pool

    assert curve_prices.isValidNewFeed(deployed_ripe_pool, deployed_ripe_pool)

    # add new price feed
    assert curve_prices.addNewPriceFeed(deployed_ripe_pool, deployed_ripe_pool, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock() + 1)
    assert curve_prices.confirmNewPriceFeed(deployed_ripe_pool, sender=governance.address)

    log = filter_logs(curve_prices, "NewCurvePriceAdded")[0]

    # verify config
    config = curve_prices.curveConfig(deployed_ripe_pool)
    assert config.pool == deployed_ripe_pool
    assert config.lpToken == deployed_ripe_pool
    assert config.numUnderlying == 2
    assert config.underlying[0] == weth_token.address
    assert config.underlying[1] == ripe_token.address
    assert config.poolType == CURVE_POOL_TYPE_TWO_CRYPTO_NG
    assert config.hasEcoToken == True

    # verify event
    assert log.asset == deployed_ripe_pool
    assert log.pool == deployed_ripe_pool


@pytest.base
def test_get_price_ripe_lp(
    weth_token, # load alt price
    deployed_ripe_pool,
    curve_prices,
    governance,
    addSeedRipeLiq,
):
    addSeedRipeLiq() # need to add liquidity to pool

    # setup
    assert curve_prices.addNewPriceFeed(deployed_ripe_pool, deployed_ripe_pool, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock() + 1)
    assert curve_prices.confirmNewPriceFeed(deployed_ripe_pool, sender=governance.address)

    price = curve_prices.getPrice(deployed_ripe_pool)
    assert price != 0


@pytest.base
def test_ripe_pool_imbalanced(
    weth_token, # load alt price
    deployed_ripe_pool,
    curve_prices,
    governance,
    addSeedRipeLiq,
    ripe_token,
    bob,
    whale,
    price_desk,
):
    addSeedRipeLiq() # need to add liquidity to pool
    ripe_pool = boa.env.lookup_contract(deployed_ripe_pool)

    # setup ripe price
    assert curve_prices.addNewPriceFeed(ripe_token, ripe_pool, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock() + 1)
    assert curve_prices.confirmNewPriceFeed(ripe_token, sender=governance.address)

    # setup ripe lp price
    assert curve_prices.addNewPriceFeed(ripe_pool, ripe_pool, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock() + 1)
    assert curve_prices.confirmNewPriceFeed(ripe_pool, sender=governance.address)

    # initial prices
    orig_ripe_price = curve_prices.getPrice(ripe_token)
    orig_ripe_lp_price = curve_prices.getPrice(ripe_pool)

    # swap amount
    swap_amount = price_desk.getPrice(weth_token) * 8
    ripe_token.transfer(bob, swap_amount, sender=whale)
    ripe_token.approve(ripe_pool, swap_amount, sender=bob)
    ripe_pool.exchange(1, 0, swap_amount, 0, bob, sender=bob)

    boa.env.time_travel(blocks=100)

    assert curve_prices.getPrice(ripe_token) < orig_ripe_price
    assert curve_prices.getPrice(ripe_pool) < orig_ripe_lp_price


###############
# Other Pools #
###############


# stableswap ng pool
# usdc-scrvusd -> 0x5aB01ee6208596f2204B85bDFA39d34c2aDD98F6


@pytest.fixture(scope="module")
def base_usdc_scrvusd_pool():
    return boa.from_etherscan("0x5aB01ee6208596f2204B85bDFA39d34c2aDD98F6", name="base_usdc_scrvusd_pool")


@pytest.fixture(scope="module")
def scrvusd_token():
    return boa.from_etherscan("0x646A737B9B6024e49f5908762B3fF73e65B5160c", name="scrvusd")


@pytest.fixture(scope="module")
def usdc_token(fork, chainlink, governance):
    usdc = boa.from_etherscan(CORE_TOKENS[fork]["USDC"], name="usdc")

    assert chainlink.addNewPriceFeed(usdc, "0x7e860098F58bBFC8648a4311b374B1D669a2bc6B", sender=governance.address)
    boa.env.time_travel(blocks=chainlink.actionTimeLock() + 1)
    assert chainlink.confirmNewPriceFeed(usdc, sender=governance.address)

    return usdc


@pytest.base
def test_add_curve_price_stable_ng(
    usdc_token,
    base_usdc_scrvusd_pool,
    scrvusd_token,
    curve_prices,
    governance,
):
    assert curve_prices.isValidNewFeed(scrvusd_token, base_usdc_scrvusd_pool)

    # add new price feed
    assert curve_prices.addNewPriceFeed(scrvusd_token, base_usdc_scrvusd_pool, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock() + 1)
    assert curve_prices.confirmNewPriceFeed(scrvusd_token, sender=governance.address)

    log = filter_logs(curve_prices, "NewCurvePriceAdded")[0]

    # verify config
    config = curve_prices.curveConfig(scrvusd_token)
    assert config.pool == base_usdc_scrvusd_pool.address
    assert config.lpToken == base_usdc_scrvusd_pool.address
    assert config.numUnderlying == 2
    assert config.underlying[0] == usdc_token.address
    assert config.underlying[1] == scrvusd_token.address
    assert config.poolType == CURVE_POOL_TYPE_STABLESWAP_NG
    assert config.hasEcoToken == False

    # verify event
    assert log.asset == scrvusd_token.address
    assert log.pool == base_usdc_scrvusd_pool.address


@pytest.base
def test_get_price_stable_ng(
    usdc_token, # load alt price
    base_usdc_scrvusd_pool,
    scrvusd_token,
    curve_prices,
    governance,
):
    # setup
    assert curve_prices.addNewPriceFeed(scrvusd_token, base_usdc_scrvusd_pool, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock() + 1)
    assert curve_prices.confirmNewPriceFeed(scrvusd_token, sender=governance.address)

    price = curve_prices.getPrice(scrvusd_token)
    assert price != 0


# two crypto
# cbeth-weth -> 0x11C1fBd4b3De66bC0565779b35171a6CF3E71f59


@pytest.fixture(scope="module")
def base_cbeth_weth_pool():
    return boa.from_etherscan("0x11c1fbd4b3de66bc0565779b35171a6cf3e71f59", name="base_cbeth_weth_pool")


@pytest.fixture(scope="module")
def cbeth_token(fork):
    return boa.from_etherscan(CORE_TOKENS[fork]["CBETH"], name="cbeth")


@pytest.fixture(scope="module")
def weth_token(fork):
    return boa.from_etherscan(CORE_TOKENS[fork]["WETH"], name="weth")


@pytest.base
def test_add_curve_price_two_crypto(
    weth_token,
    cbeth_token,
    base_cbeth_weth_pool,
    curve_prices,
    governance,
):
    assert curve_prices.isValidNewFeed(cbeth_token, base_cbeth_weth_pool)

    # add new price feed
    assert curve_prices.addNewPriceFeed(cbeth_token, base_cbeth_weth_pool, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock() + 1)
    assert curve_prices.confirmNewPriceFeed(cbeth_token, sender=governance.address)

    log = filter_logs(curve_prices, "NewCurvePriceAdded")[0]

    # verify config
    config = curve_prices.curveConfig(cbeth_token)
    assert config.pool == base_cbeth_weth_pool.address
    assert config.lpToken == "0x98244d93D42b42aB3E3A4D12A5dc0B3e7f8F32f9"
    assert config.numUnderlying == 2
    assert config.underlying[0] == weth_token.address
    assert config.underlying[1] == cbeth_token.address
    assert config.poolType == CURVE_POOL_TYPE_TWO_CRYPTO
    assert config.hasEcoToken == False

    # verify event
    assert log.asset == cbeth_token.address
    assert log.pool == base_cbeth_weth_pool.address


@pytest.base
def test_get_price_two_crypto(
    weth_token, # load alt price
    base_cbeth_weth_pool,
    cbeth_token,
    curve_prices,
    governance,
    chainlink,
    _test,
):
    # setup
    assert curve_prices.addNewPriceFeed(cbeth_token, base_cbeth_weth_pool, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock() + 1)
    assert curve_prices.confirmNewPriceFeed(cbeth_token, sender=governance.address)

    price = curve_prices.getPrice(cbeth_token)
    assert price != 0

    cbeth_chainlink = chainlink.getChainlinkData("0xd7818272B9e248357d13057AAb0B417aF31E817d", 8, 0)
    _test(price, cbeth_chainlink, 1_00)


# two crypto ng
# frok-weth -> 0xa0D3911349e701A1F49C1Ba2dDA34b4ce9636569


@pytest.fixture(scope="module")
def base_frok_weth_pool():
    return boa.from_etherscan("0xa0D3911349e701A1F49C1Ba2dDA34b4ce9636569", name="base_frok_weth_pool")


@pytest.fixture(scope="module")
def frok_token():
    return boa.from_etherscan("0x42069BAbe14fB1802C5CB0F50BB9D2Ad6FEf55e2", name="frok")


@pytest.base
def test_add_curve_price_two_crypto_ng(
    weth_token,
    frok_token,
    base_frok_weth_pool,
    curve_prices,
    governance,
):
    assert curve_prices.isValidNewFeed(frok_token, base_frok_weth_pool)

    # add new price feed
    assert curve_prices.addNewPriceFeed(frok_token, base_frok_weth_pool, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock() + 1)
    assert curve_prices.confirmNewPriceFeed(frok_token, sender=governance.address)

    log = filter_logs(curve_prices, "NewCurvePriceAdded")[0]

    # verify config
    config = curve_prices.curveConfig(frok_token)
    assert config.pool == base_frok_weth_pool.address
    assert config.lpToken == base_frok_weth_pool.address
    assert config.numUnderlying == 2
    assert config.underlying[0] == frok_token.address
    assert config.underlying[1] == weth_token.address
    assert config.poolType == CURVE_POOL_TYPE_TWO_CRYPTO_NG
    assert config.hasEcoToken == False

    # verify event
    assert log.asset == frok_token.address
    assert log.pool == base_frok_weth_pool.address


@pytest.base
def test_get_price_two_crypto_ng(
    weth_token, # load alt price
    base_frok_weth_pool,
    frok_token,
    curve_prices,
    governance,
    _test,
):
    # setup
    assert curve_prices.addNewPriceFeed(frok_token, base_frok_weth_pool, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock() + 1)
    assert curve_prices.confirmNewPriceFeed(frok_token, sender=governance.address)

    price = curve_prices.getPrice(frok_token)
    assert price != 0

    # may need to update this every once in awhile
    _test(price, int(0.046 * EIGHTEEN_DECIMALS), 1_00)


#################
# General Tests #
#################


@pytest.base
def test_get_price_no_feed(curve_prices):
    """Test getting price for asset with no configured feed"""
    fake_token = boa.env.generate_address()
    
    price = curve_prices.getPrice(fake_token)
    assert price == 0
    
    price, has_feed = curve_prices.getPriceAndHasFeed(fake_token)
    assert price == 0
    assert has_feed == False
    
    assert not curve_prices.hasPriceFeed(fake_token)


@pytest.base 
def test_invalid_pool_edge_cases(curve_prices, governance, green_token, deployed_green_pool):
    """Test validation edge cases with real pool but different scenarios"""
    # Test with asset that's already configured
    assert curve_prices.addNewPriceFeed(green_token, deployed_green_pool, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock() + 1)
    assert curve_prices.confirmNewPriceFeed(green_token, sender=governance.address)
    
    # Now trying to add the same asset again should be invalid
    assert not curve_prices.isValidNewFeed(green_token, deployed_green_pool)


@pytest.base
def test_disable_feed_validation_logic(curve_prices, governance, green_token, deployed_green_pool):
    """Test disable feed validation logic"""
    # Test disabling non-existent feed should be invalid
    assert not curve_prices.isValidDisablePriceFeed(green_token)
    
    # Add a feed first
    assert curve_prices.addNewPriceFeed(green_token, deployed_green_pool, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock() + 1)
    assert curve_prices.confirmNewPriceFeed(green_token, sender=governance.address)
    
    # Now disabling should be valid
    assert curve_prices.isValidDisablePriceFeed(green_token)


@pytest.base
def test_update_price_feed_same_pool(
    green_token,
    deployed_green_pool, 
    curve_prices,
    governance
):
    """Test updating feed with same pool should fail"""
    # Add initial feed
    assert curve_prices.addNewPriceFeed(green_token, deployed_green_pool, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock() + 1)
    assert curve_prices.confirmNewPriceFeed(green_token, sender=governance.address)
    
    # Try to update with same pool - should be invalid
    assert not curve_prices.isValidUpdateFeed(green_token, deployed_green_pool)


@pytest.base
def test_disable_non_existent_feed(curve_prices):
    """Test disabling feed that doesn't exist"""
    fake_token = boa.env.generate_address()
    
    assert not curve_prices.isValidDisablePriceFeed(fake_token)


@pytest.base
def test_time_lock_early_confirmation(
    green_token,
    deployed_green_pool,
    curve_prices, 
    governance
):
    """Test that actions cannot be confirmed before time lock expires"""
    # Add new feed
    assert curve_prices.addNewPriceFeed(green_token, deployed_green_pool, sender=governance.address)
    
    # Try to confirm immediately (should fail)
    with boa.reverts("time lock not reached"):
        curve_prices.confirmNewPriceFeed(green_token, sender=governance.address)


@pytest.base  
def test_confirm_non_pending_action(curve_prices, governance):
    """Test confirming actions that aren't pending"""
    fake_token = boa.env.generate_address()
    
    with boa.reverts("no pending new feed"):
        curve_prices.confirmNewPriceFeed(fake_token, sender=governance.address)
        
    with boa.reverts("no pending update feed"): 
        curve_prices.confirmPriceFeedUpdate(fake_token, sender=governance.address)
        
    with boa.reverts("no pending disable feed"):
        curve_prices.confirmDisablePriceFeed(fake_token, sender=governance.address)


@pytest.base
def test_cancel_non_pending_action(curve_prices, governance):
    """Test canceling actions that aren't pending"""
    fake_token = boa.env.generate_address()
    
    # These should fail because there's no pending action to cancel
    with boa.reverts("cannot cancel action"):
        curve_prices.cancelNewPendingPriceFeed(fake_token, sender=governance.address)


@pytest.base
def test_complete_feed_lifecycle(
    green_token,
    deployed_green_pool,
    curve_prices,
    governance
):
    """Test complete lifecycle: add -> disable"""
    # 1. Add new feed
    assert curve_prices.addNewPriceFeed(green_token, deployed_green_pool, sender=governance.address)
    assert curve_prices.hasPendingPriceFeedUpdate(green_token)
    
    boa.env.time_travel(blocks=curve_prices.actionTimeLock() + 1)
    assert curve_prices.confirmNewPriceFeed(green_token, sender=governance.address)
    assert curve_prices.hasPriceFeed(green_token)
    assert not curve_prices.hasPendingPriceFeedUpdate(green_token)
    
    # 2. Disable feed
    assert curve_prices.disablePriceFeed(green_token, sender=governance.address)
    assert curve_prices.hasPendingPriceFeedUpdate(green_token)
    
    boa.env.time_travel(blocks=curve_prices.actionTimeLock() + 1)
    assert curve_prices.confirmDisablePriceFeed(green_token, sender=governance.address)
    assert not curve_prices.hasPriceFeed(green_token)
    assert not curve_prices.hasPendingPriceFeedUpdate(green_token)


@pytest.base
def test_eco_token_detection(
    deployed_green_pool,
    deployed_ripe_pool,
    curve_prices,
    green_token,
    ripe_token,
    base_usdc_scrvusd_pool,
    scrvusd_token
):
    """Test that eco tokens are correctly detected in pools"""
    # Green pool should have eco token
    green_config = curve_prices.getCurvePoolConfig(green_token.address, deployed_green_pool)
    assert green_config.hasEcoToken == True
    
    # Ripe pool should have eco token  
    ripe_config = curve_prices.getCurvePoolConfig(ripe_token.address, deployed_ripe_pool)
    assert ripe_config.hasEcoToken == True
    
    # External pool should not have eco token
    external_config = curve_prices.getCurvePoolConfig(scrvusd_token.address, base_usdc_scrvusd_pool.address)
    assert external_config.hasEcoToken == False


@pytest.base
def test_price_desk_integration(
    green_token,
    deployed_green_pool,
    curve_prices,
    governance,
    price_desk
):
    """Test integration with price desk"""
    # Add feed
    assert curve_prices.addNewPriceFeed(green_token, deployed_green_pool, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock() + 1)
    assert curve_prices.confirmNewPriceFeed(green_token, sender=governance.address)
    
    # Test with explicit price desk parameter
    price_with_desk = curve_prices.getPrice(green_token, 0, price_desk.address)
    price_default = curve_prices.getPrice(green_token)
    
    # Should be the same since price desk should be the default
    assert price_with_desk == price_default


@pytest.base
def test_add_existing_asset_feed(
    green_token,
    deployed_green_pool,
    deployed_ripe_pool,
    curve_prices,
    governance
):
    """Test that adding feed for existing asset fails with isValidNewFeed"""
    # Add initial feed
    assert curve_prices.addNewPriceFeed(green_token, deployed_green_pool, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock() + 1)
    assert curve_prices.confirmNewPriceFeed(green_token, sender=governance.address)
    
    # Try to add again with different pool
    assert not curve_prices.isValidNewFeed(green_token, deployed_ripe_pool)


@pytest.base
def test_all_events_emitted(
    green_token,
    deployed_green_pool,
    curve_prices, 
    governance
):
    """Test that all expected events are emitted during feed lifecycle"""
    # Add new feed - should emit NewCurvePricePending
    curve_prices.addNewPriceFeed(green_token, deployed_green_pool, sender=governance.address)
    pending_logs = filter_logs(curve_prices, "NewCurvePricePending")
    assert len(pending_logs) == 1
    assert pending_logs[0].asset == green_token.address
    assert pending_logs[0].pool == deployed_green_pool
    
    # Confirm - should emit NewCurvePriceAdded
    boa.env.time_travel(blocks=curve_prices.actionTimeLock() + 1)
    curve_prices.confirmNewPriceFeed(green_token, sender=governance.address)
    added_logs = filter_logs(curve_prices, "NewCurvePriceAdded")
    assert len(added_logs) == 1
    
    # Disable feed - should emit disable events
    curve_prices.disablePriceFeed(green_token, sender=governance.address)
    disable_pending_logs = filter_logs(curve_prices, "DisableCurvePricePending")
    assert len(disable_pending_logs) == 1
    
    boa.env.time_travel(blocks=curve_prices.actionTimeLock() + 1)
    curve_prices.confirmDisablePriceFeed(green_token, sender=governance.address) 
    disabled_logs = filter_logs(curve_prices, "CurvePriceDisabled")
    assert len(disabled_logs) == 1


@pytest.base
def test_cancel_events(
    green_token,
    deployed_green_pool,
    curve_prices,
    governance
):
    """Test that cancel events are emitted"""
    # Add and cancel new feed
    curve_prices.addNewPriceFeed(green_token, deployed_green_pool, sender=governance.address)
    curve_prices.cancelNewPendingPriceFeed(green_token, sender=governance.address)
    cancel_logs = filter_logs(curve_prices, "NewCurvePriceCancelled")
    assert len(cancel_logs) == 1


@pytest.base
def test_access_control_non_governance(curve_prices, bob, green_token, deployed_green_pool):
    """Test that non-governance users cannot manage feeds"""
    with boa.reverts("no perms"):
        curve_prices.addNewPriceFeed(green_token, deployed_green_pool, sender=bob)
    
    with boa.reverts("no perms"):
        curve_prices.confirmNewPriceFeed(green_token, sender=bob)
        
    with boa.reverts("no perms"):
        curve_prices.cancelNewPendingPriceFeed(green_token, sender=bob)
        
    with boa.reverts("no perms"):
        curve_prices.updatePriceFeed(green_token, deployed_green_pool, sender=bob)
        
    with boa.reverts("no perms"):
        curve_prices.confirmPriceFeedUpdate(green_token, sender=bob)
        
    with boa.reverts("no perms"):
        curve_prices.cancelPriceFeedUpdate(green_token, sender=bob)
        
    with boa.reverts("no perms"):
        curve_prices.disablePriceFeed(green_token, sender=bob)
        
    with boa.reverts("no perms"):
        curve_prices.confirmDisablePriceFeed(green_token, sender=bob)
        
    with boa.reverts("no perms"):
        curve_prices.cancelDisablePriceFeed(green_token, sender=bob)
