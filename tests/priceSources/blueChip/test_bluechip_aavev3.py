import pytest
import boa

from constants import BLUE_CHIP_PROTOCOL_AAVE_V3
from config.BluePrint import YIELD_TOKENS, CORE_TOKENS
from conf_utils import filter_logs


@pytest.fixture(scope="module")
def usdc_token(fork, chainlink, governance):
    usdc = boa.from_etherscan(CORE_TOKENS[fork]["USDC"], name="usdc")
    if not chainlink.hasPriceFeed(usdc):
        assert chainlink.addNewPriceFeed(usdc, "0x7e860098F58bBFC8648a4311b374B1D669a2bc6B", sender=governance.address)
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
        assert chainlink.addNewPriceFeed(cbbtc, "0x07DA0E54543a844a80ABE69c8A12F22B3aA59f9D", sender=governance.address)
        boa.env.time_travel(blocks=chainlink.actionTimeLock() + 1)
        assert chainlink.confirmNewPriceFeed(cbbtc, sender=governance.address)
    return cbbtc


#######################
# Aave v3 Integration #
#######################


@pytest.base
def test_add_aave_v3_vault_token_usdc(
    blue_chip_prices,
    governance,
    usdc_token,
    fork,
    price_desk,
):
    aave_v3_usdc = YIELD_TOKENS[fork]["AAVEV3_USDC"]
    assert blue_chip_prices.isValidNewFeed(aave_v3_usdc, BLUE_CHIP_PROTOCOL_AAVE_V3, 3600, 20, 20_00, 0)

    # add new price feed
    assert blue_chip_prices.addNewPriceFeed(aave_v3_usdc, BLUE_CHIP_PROTOCOL_AAVE_V3, 3600, 20, 20_00, 0, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    assert blue_chip_prices.confirmNewPriceFeed(aave_v3_usdc, sender=governance.address)

    log = filter_logs(blue_chip_prices, "NewPriceConfigAdded")[0]

    # verify config
    config = blue_chip_prices.priceConfigs(aave_v3_usdc)
    assert config.protocol == BLUE_CHIP_PROTOCOL_AAVE_V3
    assert config.underlyingAsset == usdc_token.address
    assert config.underlyingDecimals == 6
    assert config.vaultTokenDecimals == 6
    assert config.minSnapshotDelay == 3600
    assert config.maxNumSnapshots == 20
    assert config.maxUpsideDeviation == 20_00
    assert config.staleTime == 0
    assert config.nextIndex == 0 # no snapshot taken

    # verify event
    assert log.asset == aave_v3_usdc
    assert log.protocol == BLUE_CHIP_PROTOCOL_AAVE_V3
    assert log.underlyingAsset == usdc_token.address
    assert log.minSnapshotDelay == 3600
    assert log.maxNumSnapshots == 20
    assert log.maxUpsideDeviation == 20_00
    assert log.staleTime == 0

    usdc_price = price_desk.getPrice(usdc_token)
    assert usdc_price != 0

    # test price
    aave_v3_usdc_price = blue_chip_prices.getPrice(aave_v3_usdc)
    assert aave_v3_usdc_price == usdc_price


@pytest.base
def test_add_aave_v3_vault_token_weth(
    blue_chip_prices,
    governance,
    weth_token,
    fork,
    price_desk,
):
    aave_weth = YIELD_TOKENS[fork]["AAVEV3_WETH"]
    assert blue_chip_prices.isValidNewFeed(aave_weth, BLUE_CHIP_PROTOCOL_AAVE_V3, 3600, 20, 20_00, 0)

    # add new price feed
    assert blue_chip_prices.addNewPriceFeed(aave_weth, BLUE_CHIP_PROTOCOL_AAVE_V3, 3600, 20, 20_00, 0, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    assert blue_chip_prices.confirmNewPriceFeed(aave_weth, sender=governance.address)

    log = filter_logs(blue_chip_prices, "NewPriceConfigAdded")[0]

    # verify config
    config = blue_chip_prices.priceConfigs(aave_weth)
    assert config.protocol == BLUE_CHIP_PROTOCOL_AAVE_V3
    assert config.underlyingAsset == weth_token.address
    assert config.underlyingDecimals == 18
    assert config.vaultTokenDecimals == 18
    assert config.minSnapshotDelay == 3600
    assert config.maxNumSnapshots == 20
    assert config.maxUpsideDeviation == 20_00
    assert config.staleTime == 0
    assert config.nextIndex == 0 # no snapshot taken

    # verify event
    assert log.asset == aave_weth
    assert log.protocol == BLUE_CHIP_PROTOCOL_AAVE_V3
    assert log.underlyingAsset == weth_token.address
    assert log.minSnapshotDelay == 3600
    assert log.maxNumSnapshots == 20
    assert log.maxUpsideDeviation == 20_00
    assert log.staleTime == 0

    # underlying price
    weth_price = price_desk.getPrice(weth_token)
    assert weth_price != 0

    # vault token price
    aave_weth_price = blue_chip_prices.getPrice(aave_weth)
    assert aave_weth_price == weth_price


@pytest.base
def test_add_aave_v3_vault_token_cbbtc(
    blue_chip_prices,
    governance,
    cbbtc_token,
    fork,
    price_desk,
):
    aave_cbbtc = YIELD_TOKENS[fork]["AAVEV3_CBBTC"]
    assert blue_chip_prices.isValidNewFeed(aave_cbbtc, BLUE_CHIP_PROTOCOL_AAVE_V3, 3600, 20, 20_00, 0)

    # add new price feed
    assert blue_chip_prices.addNewPriceFeed(aave_cbbtc, BLUE_CHIP_PROTOCOL_AAVE_V3, 3600, 20, 20_00, 0, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    assert blue_chip_prices.confirmNewPriceFeed(aave_cbbtc, sender=governance.address)

    log = filter_logs(blue_chip_prices, "NewPriceConfigAdded")[0]

    # verify config
    config = blue_chip_prices.priceConfigs(aave_cbbtc)
    assert config.protocol == BLUE_CHIP_PROTOCOL_AAVE_V3
    assert config.underlyingAsset == cbbtc_token.address
    assert config.underlyingDecimals == 8
    assert config.vaultTokenDecimals == 8
    assert config.minSnapshotDelay == 3600
    assert config.maxNumSnapshots == 20
    assert config.maxUpsideDeviation == 20_00
    assert config.staleTime == 0
    assert config.nextIndex == 0 # no snapshot taken

    # verify event
    assert log.asset == aave_cbbtc
    assert log.protocol == BLUE_CHIP_PROTOCOL_AAVE_V3
    assert log.underlyingAsset == cbbtc_token.address
    assert log.minSnapshotDelay == 3600
    assert log.maxNumSnapshots == 20
    assert log.maxUpsideDeviation == 20_00
    assert log.staleTime == 0

    # underlying price
    cbbtc_price = price_desk.getPrice(cbbtc_token)
    assert cbbtc_price != 0

    # vault token price
    aave_cbbtc_price = blue_chip_prices.getPrice(aave_cbbtc)
    assert aave_cbbtc_price == cbbtc_price
