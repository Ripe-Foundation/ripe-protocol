import pytest
import boa

from constants import BLUE_CHIP_PROTOCOL_MORPHO, EIGHTEEN_DECIMALS
from config.BluePrint import YIELD_TOKENS, CORE_TOKENS
from conf_utils import filter_logs


@pytest.fixture(scope="module")
def usdc_token(fork, chainlink, governance):
    usdc = boa.from_etherscan(CORE_TOKENS[fork]["USDC"], name="usdc")
    assert chainlink.addNewPriceFeed(usdc, "0x7e860098F58bBFC8648a4311b374B1D669a2bc6B", sender=governance.address)
    boa.env.time_travel(blocks=chainlink.actionTimeLock() + 1)
    assert chainlink.confirmNewPriceFeed(usdc, sender=governance.address)
    return usdc


######################
# Morpho Integration #
######################


@pytest.base
def test_add_morpho_vault_token(
    blue_chip_prices,
    governance,
    usdc_token,
    fork,
    price_desk,
    _test,
):
    morpho_usdc = YIELD_TOKENS[fork]["MORPHO_MOONWELL_USDC"]
    assert blue_chip_prices.isValidNewFeed(morpho_usdc, BLUE_CHIP_PROTOCOL_MORPHO, 10, 10)

    # add new price feed
    assert blue_chip_prices.addNewPriceFeed(morpho_usdc, BLUE_CHIP_PROTOCOL_MORPHO, 10, 10, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    assert blue_chip_prices.confirmNewPriceFeed(morpho_usdc, sender=governance.address)

    log = filter_logs(blue_chip_prices, "NewPriceConfigAdded")[0]

    # verify config
    config = blue_chip_prices.priceConfigs(morpho_usdc)
    assert config.protocol == BLUE_CHIP_PROTOCOL_MORPHO
    assert config.underlyingAsset == usdc_token.address
    assert config.underlyingDecimals == 6
    assert config.vaultTokenDecimals == 18
    assert config.maxNumSnapshots == 10
    assert config.staleTime == 10
    assert config.nextIndex == 1 # snapshot taken during registration

    # verify event
    assert log.asset == morpho_usdc
    assert log.protocol == BLUE_CHIP_PROTOCOL_MORPHO
    assert log.underlyingAsset == usdc_token.address
    assert log.maxNumSnapshots == 10
    assert log.staleTime == 10

    usdc_price = price_desk.getPrice(usdc_token)
    assert usdc_price != 0

    # test price
    morpho_usdc_price = blue_chip_prices.getPrice(morpho_usdc)
    _test(morpho_usdc_price, int(1.03 * EIGHTEEN_DECIMALS))
