import pytest
import boa

from constants import BLUE_CHIP_PROTOCOL_MOONWELL, EIGHTEEN_DECIMALS
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


########################
# Moonwell Integration #
########################


@pytest.base
def test_add_moonwell_vault_token_usdc(
    blue_chip_prices,
    governance,
    usdc_token,
    fork,
    price_desk,
    _test,
    bob,
):
    moonwell_usdc = boa.from_etherscan(YIELD_TOKENS[fork]["MOONWELL_USDC"])
    assert blue_chip_prices.isValidNewFeed(moonwell_usdc, BLUE_CHIP_PROTOCOL_MOONWELL, 3600, 20, 20_00, 0)

    # add new price feed
    assert blue_chip_prices.addNewPriceFeed(moonwell_usdc, BLUE_CHIP_PROTOCOL_MOONWELL, 3600, 20, 20_00, 0, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    assert blue_chip_prices.confirmNewPriceFeed(moonwell_usdc, sender=governance.address)

    log = filter_logs(blue_chip_prices, "NewPriceConfigAdded")[0]

    # verify config
    config = blue_chip_prices.priceConfigs(moonwell_usdc)
    assert config.protocol == BLUE_CHIP_PROTOCOL_MOONWELL
    assert config.underlyingAsset == usdc_token.address
    assert config.underlyingDecimals == 6
    assert config.vaultTokenDecimals == 8
    assert config.minSnapshotDelay == 3600
    assert config.maxNumSnapshots == 20
    assert config.maxUpsideDeviation == 20_00
    assert config.staleTime == 0
    assert config.nextIndex == 1 # snapshot taken during registration

    # verify event
    assert log.asset == moonwell_usdc.address
    assert log.protocol == BLUE_CHIP_PROTOCOL_MOONWELL
    assert log.underlyingAsset == usdc_token.address
    assert log.minSnapshotDelay == 3600
    assert log.maxNumSnapshots == 20
    assert log.maxUpsideDeviation == 20_00
    assert log.staleTime == 0

    usdc_price = price_desk.getPrice(usdc_token)
    assert usdc_price != 0

    # deposit to test this
    amount = 1_000 * (10 ** 6)
    moonwell_usdc = boa.from_etherscan(YIELD_TOKENS[fork]["MOONWELL_USDC"])
    usdc_token.transfer(bob, amount, sender=moonwell_usdc.address)
    usdc_token.approve(moonwell_usdc, amount, sender=bob)
    assert moonwell_usdc.mint(amount, sender=bob) == 0

    # main test !
    bob_balance = moonwell_usdc.balanceOf(bob)
    moonwell_usdc_price = blue_chip_prices.getPrice(moonwell_usdc)
    _test(1_000 * EIGHTEEN_DECIMALS, moonwell_usdc_price * bob_balance // (10 ** moonwell_usdc.decimals()))


@pytest.base
def test_add_moonwell_vault_token_weth(
    blue_chip_prices,
    governance,
    weth_token,
    fork,
    price_desk,
    _test,
    bob,
):
    moonwell_weth = YIELD_TOKENS[fork]["MOONWELL_WETH"]
    assert blue_chip_prices.isValidNewFeed(moonwell_weth, BLUE_CHIP_PROTOCOL_MOONWELL, 3600, 20, 20_00, 0)

    # add new price feed
    assert blue_chip_prices.addNewPriceFeed(moonwell_weth, BLUE_CHIP_PROTOCOL_MOONWELL, 3600, 20, 20_00, 0, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    assert blue_chip_prices.confirmNewPriceFeed(moonwell_weth, sender=governance.address)

    log = filter_logs(blue_chip_prices, "NewPriceConfigAdded")[0]

    # verify config
    config = blue_chip_prices.priceConfigs(moonwell_weth)
    assert config.protocol == BLUE_CHIP_PROTOCOL_MOONWELL
    assert config.underlyingAsset == weth_token.address
    assert config.underlyingDecimals == 18
    assert config.vaultTokenDecimals == 8
    assert config.minSnapshotDelay == 3600
    assert config.maxNumSnapshots == 20
    assert config.maxUpsideDeviation == 20_00
    assert config.staleTime == 0
    assert config.nextIndex == 1 # snapshot taken during registration

    # verify event
    assert log.asset == moonwell_weth
    assert log.protocol == BLUE_CHIP_PROTOCOL_MOONWELL
    assert log.underlyingAsset == weth_token.address
    assert log.minSnapshotDelay == 3600
    assert log.maxNumSnapshots == 20
    assert log.maxUpsideDeviation == 20_00
    assert log.staleTime == 0

    # underlying price
    weth_price = price_desk.getPrice(weth_token)
    assert weth_price != 0

    # deposit to test this
    amount = 1 * EIGHTEEN_DECIMALS
    moonwell_weth = boa.from_etherscan(YIELD_TOKENS[fork]["MOONWELL_WETH"])
    weth_token.transfer(bob, amount, sender=moonwell_weth.address)
    weth_token.approve(moonwell_weth, amount, sender=bob)
    assert moonwell_weth.mint(amount, sender=bob) == 0

    # main test !
    bob_balance = moonwell_weth.balanceOf(bob)
    moonwell_weth_price = blue_chip_prices.getPrice(moonwell_weth)
    bob_value = moonwell_weth_price * bob_balance // (10 ** moonwell_weth.decimals())

    weth_value = weth_price * amount // EIGHTEEN_DECIMALS
    _test(weth_value, bob_value)


@pytest.base
def test_add_moonwell_vault_token_cbbtc(
    blue_chip_prices,
    governance,
    cbbtc_token,
    fork,
    price_desk,
    _test,
    bob,
):
    moonwell_cbbtc = YIELD_TOKENS[fork]["MOONWELL_CBBTC"]
    assert blue_chip_prices.isValidNewFeed(moonwell_cbbtc, BLUE_CHIP_PROTOCOL_MOONWELL, 3600, 20, 20_00, 0)

    # add new price feed
    assert blue_chip_prices.addNewPriceFeed(moonwell_cbbtc, BLUE_CHIP_PROTOCOL_MOONWELL, 3600, 20, 20_00, 0, sender=governance.address)
    boa.env.time_travel(blocks=blue_chip_prices.actionTimeLock() + 1)
    assert blue_chip_prices.confirmNewPriceFeed(moonwell_cbbtc, sender=governance.address)

    log = filter_logs(blue_chip_prices, "NewPriceConfigAdded")[0]

    # verify config
    config = blue_chip_prices.priceConfigs(moonwell_cbbtc)
    assert config.protocol == BLUE_CHIP_PROTOCOL_MOONWELL
    assert config.underlyingAsset == cbbtc_token.address
    assert config.underlyingDecimals == 8
    assert config.vaultTokenDecimals == 8
    assert config.minSnapshotDelay == 3600
    assert config.maxNumSnapshots == 20
    assert config.maxUpsideDeviation == 20_00
    assert config.staleTime == 0
    assert config.nextIndex == 1 # snapshot taken during registration

    # verify event
    assert log.asset == moonwell_cbbtc
    assert log.protocol == BLUE_CHIP_PROTOCOL_MOONWELL
    assert log.underlyingAsset == cbbtc_token.address
    assert log.minSnapshotDelay == 3600
    assert log.maxNumSnapshots == 20
    assert log.maxUpsideDeviation == 20_00
    assert log.staleTime == 0

    # underlying price
    cbbtc_price = price_desk.getPrice(cbbtc_token)
    assert cbbtc_price != 0

    # deposit to test this
    amount = 1 * (10 ** cbbtc_token.decimals())
    moonwell_cbbtc = boa.from_etherscan(YIELD_TOKENS[fork]["MOONWELL_CBBTC"])
    cbbtc_token.transfer(bob, amount, sender=moonwell_cbbtc.address)
    cbbtc_token.approve(moonwell_cbbtc, amount, sender=bob)
    assert moonwell_cbbtc.mint(amount, sender=bob) == 0

    # main test !
    bob_balance = moonwell_cbbtc.balanceOf(bob)
    moonwell_cbbtc_price = blue_chip_prices.getPrice(moonwell_cbbtc)
    bob_value = moonwell_cbbtc_price * bob_balance // (10 ** moonwell_cbbtc.decimals())

    cbbtc_value = cbbtc_price * amount // (10 ** cbbtc_token.decimals())
    _test(cbbtc_value, bob_value)
