import pytest
import boa

from constants import BLUE_CHIP_PROTOCOL_MOONWELL, EIGHTEEN_DECIMALS, ZERO_ADDRESS
from config.BluePrint import YIELD_TOKENS, CORE_TOKENS, PARAMS
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


@pytest.fixture
def local_moonwell_token(alpha_token):
    return boa.load(
        "contracts/mock/MockMoonwellToken.vy",
        alpha_token,
        EIGHTEEN_DECIMALS,
        100 * 10**8,
        8,
        name="local_moonwell_token",
    )


@pytest.fixture
def local_moonwell_prices(
    ripe_hq_deploy,
    governance,
    mock_yield_registry,
    local_moonwell_token,
):
    moonwell_registry = boa.load(
        "contracts/mock/MockYieldRegistry.vy",
        [local_moonwell_token],
        name="local_moonwell_registry",
    )
    prices = boa.load(
        "contracts/priceSources/BlueChipYieldPrices.vy",
        ripe_hq_deploy,
        ZERO_ADDRESS,
        PARAMS["local"]["PRICE_DESK_MIN_REG_TIMELOCK"],
        PARAMS["local"]["PRICE_DESK_MAX_REG_TIMELOCK"],
        [mock_yield_registry, mock_yield_registry],
        [mock_yield_registry, mock_yield_registry],
        mock_yield_registry,
        mock_yield_registry,
        moonwell_registry,
        mock_yield_registry,
        mock_yield_registry,
        name="local_moonwell_prices",
    )
    assert prices.setActionTimeLockAfterSetup(sender=governance.address)
    return prices


def test_moonwell_successful_zero_live_pps_fails_closed_and_preserves_min_policy(
    local_moonwell_prices,
    local_moonwell_token,
    governance,
    mock_price_source,
    alpha_token,
    teller,
):
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    assert local_moonwell_prices.addNewPriceFeed(
        local_moonwell_token,
        BLUE_CHIP_PROTOCOL_MOONWELL,
        0,
        5,
        0,
        0,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=local_moonwell_prices.actionTimeLock() + 1)
    assert local_moonwell_prices.confirmNewPriceFeed(
        local_moonwell_token,
        sender=governance.address,
    )
    assert local_moonwell_prices.getWeightedPrice(local_moonwell_token) == 10**8
    assert local_moonwell_prices.getPrice(local_moonwell_token) == 10**8

    local_moonwell_token.setExchangeRate(EIGHTEEN_DECIMALS // 2)
    assert local_moonwell_prices.getPrice(local_moonwell_token) == 5 * 10**7
    local_moonwell_token.setExchangeRate(2 * EIGHTEEN_DECIMALS)
    assert local_moonwell_prices.getPrice(local_moonwell_token) == 10**8

    # Exercise the Moonwell duration-weighted path, not only its structural
    # min clamp. The manipulated 2x observation accrues 30 of 40 seconds, so
    # the raw TWAP is 1.75x after the live rate returns to 1x. The Moonwell
    # live-PPS clamp keeps the reported price at 1x.
    boa.env.time_travel(seconds=10)
    assert local_moonwell_prices.addPriceSnapshot(
        local_moonwell_token,
        sender=teller.address,
    )
    local_moonwell_token.setExchangeRate(EIGHTEEN_DECIMALS)
    boa.env.time_travel(seconds=30)
    expected_weighted = (10**8 * 10 + 2 * 10**8 * 30) // 40
    assert expected_weighted == 175_000_000
    assert local_moonwell_prices.getWeightedPrice(local_moonwell_token) == (
        expected_weighted
    )
    assert local_moonwell_prices.getPrice(local_moonwell_token) == 10**8

    local_moonwell_token.setExchangeRate(0)
    assert local_moonwell_token.exchangeRateStored() == 0
    assert local_moonwell_prices.getWeightedPrice(local_moonwell_token) == (
        expected_weighted
    )
    assert local_moonwell_prices.getPrice(local_moonwell_token) == 0


def test_moonwell_typed_live_pps_revert_is_not_suppressed(
    local_moonwell_prices,
    local_moonwell_token,
    governance,
    mock_price_source,
    alpha_token,
):
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    assert local_moonwell_prices.addNewPriceFeed(
        local_moonwell_token,
        BLUE_CHIP_PROTOCOL_MOONWELL,
        0,
        5,
        0,
        0,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=local_moonwell_prices.actionTimeLock() + 1)
    assert local_moonwell_prices.confirmNewPriceFeed(
        local_moonwell_token,
        sender=governance.address,
    )
    assert local_moonwell_prices.getWeightedPrice(local_moonwell_token) > 0
    local_moonwell_token.setShouldRevert(True)
    with boa.reverts():
        local_moonwell_prices.getPrice(local_moonwell_token)
