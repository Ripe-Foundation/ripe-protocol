import pytest
import boa

from constants import BLUE_CHIP_PROTOCOL_EULER
from config.BluePrint import YIELD_TOKENS, CORE_TOKENS
from conf_utils import filter_logs


@pytest.fixture(scope="module")
def usdc_token(fork, chainlink, governance):
    usdc = boa.from_etherscan(CORE_TOKENS[fork]["USDC"], name="usdc")
    if not chainlink.hasPriceFeed(usdc):
        # Use staleTime=0 for forked tests since historical Chainlink data may be stale
        assert chainlink.addNewPriceFeed(usdc, "0x7e860098F58bBFC8648a4311b374B1D669a2bc6B", 0, False, False, sender=governance.address)
        boa.env.time_travel(blocks=chainlink.actionTimeLock() + 1)
        assert chainlink.confirmNewPriceFeed(usdc, sender=governance.address)
    return usdc


@pytest.fixture(scope="module")
def weth_token(fork, chainlink):
    weth = boa.from_etherscan(CORE_TOKENS[fork]["WETH"], name="weth")
    assert chainlink.hasPriceFeed(weth)
    return weth


@pytest.fixture(scope="module")
def cbbtc_token(fork, chainlink, governance):
    cbbtc = boa.from_etherscan(CORE_TOKENS[fork]["CBBTC"], name="cbbtc")
    if not chainlink.hasPriceFeed(cbbtc):
        # Use staleTime=0 for forked tests since historical Chainlink data may be stale
        assert chainlink.addNewPriceFeed(cbbtc, "0x07DA0E54543a844a80ABE69c8A12F22B3aA59f9D", 0, False, False, sender=governance.address)
        boa.env.time_travel(blocks=chainlink.actionTimeLock() + 1)
        assert chainlink.confirmNewPriceFeed(cbbtc, sender=governance.address)
    return cbbtc


#####################
# Euler Integration #
#####################


@pytest.base
def test_add_euler_vault_token_usdc(
    blue_chip_prices,
    governance,
    usdc_token,
    fork,
    price_desk,
    _test,
):
    euler_usdc = YIELD_TOKENS[fork]["EULER_USDC"]
    assert blue_chip_prices.isValidNewFeed(euler_usdc, BLUE_CHIP_PROTOCOL_EULER, 3600, 20, 20_00, 0)

    # add new price feed
    assert blue_chip_prices.addNewPriceFeed(euler_usdc, BLUE_CHIP_PROTOCOL_EULER, 3600, 20, 20_00, 0, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    assert blue_chip_prices.confirmNewPriceFeed(euler_usdc, sender=governance.address)

    log = filter_logs(blue_chip_prices, "NewPriceConfigAdded")[0]

    # verify config
    config = blue_chip_prices.priceConfigs(euler_usdc)
    assert config.protocol == BLUE_CHIP_PROTOCOL_EULER
    assert config.underlyingAsset == usdc_token.address
    assert config.underlyingDecimals == 6
    assert config.vaultTokenDecimals == 6
    assert config.minSnapshotDelay == 3600
    assert config.maxNumSnapshots == 20
    assert config.maxUpsideDeviation == 20_00
    assert config.staleTime == 0
    assert config.nextIndex == 1 # snapshot taken during registration

    # verify event
    assert log.asset == euler_usdc
    assert log.protocol == BLUE_CHIP_PROTOCOL_EULER
    assert log.underlyingAsset == usdc_token.address
    assert log.minSnapshotDelay == 3600
    assert log.maxNumSnapshots == 20
    assert log.maxUpsideDeviation == 20_00
    assert log.staleTime == 0

    usdc_price = price_desk.getPrice(usdc_token)
    assert usdc_price != 0

    # test price (vault share price is usually > underlying due to accrued yield)
    euler_usdc_price = blue_chip_prices.getPrice(euler_usdc)
    _test(euler_usdc_price, usdc_price, 5_00)


@pytest.base
def test_add_euler_vault_token_weth(
    blue_chip_prices,
    governance,
    weth_token,
    fork,
    price_desk,
    _test,
):
    euler_weth = YIELD_TOKENS[fork]["EULER_WETH"]
    assert blue_chip_prices.isValidNewFeed(euler_weth, BLUE_CHIP_PROTOCOL_EULER, 3600, 20, 20_00, 0)

    # add new price feed
    assert blue_chip_prices.addNewPriceFeed(euler_weth, BLUE_CHIP_PROTOCOL_EULER, 3600, 20, 20_00, 0, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    assert blue_chip_prices.confirmNewPriceFeed(euler_weth, sender=governance.address)

    log = filter_logs(blue_chip_prices, "NewPriceConfigAdded")[0]

    # verify config
    config = blue_chip_prices.priceConfigs(euler_weth)
    assert config.protocol == BLUE_CHIP_PROTOCOL_EULER
    assert config.underlyingAsset == weth_token.address
    assert config.underlyingDecimals == 18
    assert config.vaultTokenDecimals == 18
    assert config.minSnapshotDelay == 3600
    assert config.maxNumSnapshots == 20
    assert config.maxUpsideDeviation == 20_00
    assert config.staleTime == 0
    assert config.nextIndex == 1 # snapshot taken during registration

    # verify event
    assert log.asset == euler_weth
    assert log.protocol == BLUE_CHIP_PROTOCOL_EULER
    assert log.underlyingAsset == weth_token.address
    assert log.minSnapshotDelay == 3600
    assert log.maxNumSnapshots == 20
    assert log.maxUpsideDeviation == 20_00
    assert log.staleTime == 0

    # underlying price
    weth_price = price_desk.getPrice(weth_token)
    assert weth_price != 0

    # vault token price (vault share price is usually > underlying due to accrued yield)
    euler_weth_price = blue_chip_prices.getPrice(euler_weth)
    _test(euler_weth_price, weth_price, 5_00)


@pytest.base
def test_add_euler_vault_token_cbbtc(
    blue_chip_prices,
    governance,
    cbbtc_token,
    fork,
    price_desk,
    _test,
):
    euler_cbbtc = YIELD_TOKENS[fork]["EULER_CBBTC"]
    assert blue_chip_prices.isValidNewFeed(euler_cbbtc, BLUE_CHIP_PROTOCOL_EULER, 3600, 20, 20_00, 0)

    # add new price feed
    assert blue_chip_prices.addNewPriceFeed(euler_cbbtc, BLUE_CHIP_PROTOCOL_EULER, 3600, 20, 20_00, 0, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    assert blue_chip_prices.confirmNewPriceFeed(euler_cbbtc, sender=governance.address)

    log = filter_logs(blue_chip_prices, "NewPriceConfigAdded")[0]

    # verify config
    config = blue_chip_prices.priceConfigs(euler_cbbtc)
    assert config.protocol == BLUE_CHIP_PROTOCOL_EULER
    assert config.underlyingAsset == cbbtc_token.address
    assert config.underlyingDecimals == 8
    assert config.vaultTokenDecimals == 8
    assert config.minSnapshotDelay == 3600
    assert config.maxNumSnapshots == 20
    assert config.maxUpsideDeviation == 20_00
    assert config.staleTime == 0
    assert config.nextIndex == 1 # snapshot taken during registration

    # verify event
    assert log.asset == euler_cbbtc
    assert log.protocol == BLUE_CHIP_PROTOCOL_EULER
    assert log.underlyingAsset == cbbtc_token.address
    assert log.minSnapshotDelay == 3600
    assert log.maxNumSnapshots == 20
    assert log.maxUpsideDeviation == 20_00
    assert log.staleTime == 0

    # underlying price
    cbbtc_price = price_desk.getPrice(cbbtc_token)
    assert cbbtc_price != 0

    # vault token price (vault share price is usually > underlying due to accrued yield)
    euler_cbbtc_price = blue_chip_prices.getPrice(euler_cbbtc)
    _test(euler_cbbtc_price, cbbtc_price, 5_00)
