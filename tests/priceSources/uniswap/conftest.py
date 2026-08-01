from dataclasses import dataclass

import boa
import pytest
from eth_utils import to_checksum_address


FACTORY = to_checksum_address("0x8bceaa40b9acdfaedf85adf4ff01f5ad6517937f")
WETH = to_checksum_address("0x0Bd7D308f8E1639FAb988df18A8011f41EAcAD73")
ZERO = to_checksum_address("0x0000000000000000000000000000000000000000")
ONE = 10**18
Q112 = 2**112
UINT32_MODULUS = 2**32
UINT256_MODULUS = 2**256
WINDOW = 1800


@dataclass
class CandidateFixture:
    source: object
    pair: object
    factory: object
    ripe: object
    quote: object
    quote_desk: object
    governor: str
    reserve0: int
    reserve1: int
    ripe_is_token0: bool


def _install_at(path, address, *constructor_args):
    implementation = boa.load(path, *constructor_args)
    boa.env.set_code(address, boa.env.get_code(implementation.address))
    return boa.load_partial(path).at(address)


@pytest.fixture
def candidate_builder(ripe_hq_deploy, governance):
    def build(
        *,
        ripe_decimals=18,
        quote_decimals=18,
        ripe_is_token0=True,
        ripe_units=100,
        quote_units=10,
        quote_usd=2_000 * ONE,
        activate=True,
        max_period=2 * WINDOW,
        max_staleness=2 * WINDOW,
        min_ripe_reserve=1,
        min_quote_reserve=1,
        max_deviation_bps=2_000,
        max_quote_stale=3600,
        min_time_lock=1,
        max_time_lock=100,
        finish_setup=True,
    ):
        ripe = boa.load("contracts/mock/MockUniswapV2Token.vy", ripe_decimals)
        quote = _install_at("contracts/mock/MockUniswapV2Token.vy", WETH, quote_decimals)
        quote.setDecimals(quote_decimals)

        factory = _install_at("contracts/mock/MockUniswapV2Factory.vy", FACTORY)
        pair = boa.load("contracts/mock/MockUniswapV2Pair.vy")
        token0 = ripe.address if ripe_is_token0 else WETH
        token1 = WETH if ripe_is_token0 else ripe.address
        pair.configureIdentity(FACTORY, token0, token1)

        ripe_reserve = ripe_units * 10**ripe_decimals
        quote_reserve = quote_units * 10**quote_decimals
        reserve0 = ripe_reserve if ripe_is_token0 else quote_reserve
        reserve1 = quote_reserve if ripe_is_token0 else ripe_reserve
        token0_contract = ripe if ripe_is_token0 else quote
        token1_contract = quote if ripe_is_token0 else ripe
        token0_contract.setBalance(pair.address, reserve0)
        token1_contract.setBalance(pair.address, reserve1)
        pair.mint(governance.address)
        factory.setPair(ripe.address, WETH, pair.address)

        quote_desk = boa.load("contracts/mock/MockUniswapV2QuotePriceDesk.vy")
        quote_desk.setPrice(quote_usd)

        source = boa.load(
            "contracts/priceSources/RobinhoodUniswapV2RipePrices.vy",
            ripe_hq_deploy,
            ZERO,
            FACTORY,
            ripe.address,
            WETH,
            pair.address,
            min_time_lock,
            max_time_lock,
            ZERO,
            1,
        )
        assert source.actionTimeLock() == 0
        if finish_setup:
            assert source.setActionTimeLockAfterSetup(sender=governance.address)
            assert source.actionTimeLock() == min_time_lock
            source.updateOracleConfig(
                WINDOW,
                max_period,
                max_staleness,
                min_ripe_reserve,
                min_quote_reserve,
                max_deviation_bps,
                WINDOW,
                max_quote_stale,
                sender=governance.address,
            )
            boa.env.time_travel(blocks=min_time_lock)
            assert source.confirmPriceFeedUpdate(ripe.address, sender=governance.address)

        fixture = CandidateFixture(
            source=source,
            pair=pair,
            factory=factory,
            ripe=ripe,
            quote=quote,
            quote_desk=quote_desk,
            governor=governance.address,
            reserve0=reserve0,
            reserve1=reserve1,
            ripe_is_token0=ripe_is_token0,
        )
        if activate:
            assert finish_setup
            bootstrap_and_activate(fixture)
        return fixture

    return build


def bootstrap_and_activate(fixture):
    source = fixture.source
    assert source.update()
    assert source.average().updatedAt == 0
    boa.env.time_travel(seconds=WINDOW)
    assert source.update()
    assert source.average().averagingPeriodSeconds == WINDOW
    assert source.initiateActivation(sender=fixture.governor)
    boa.env.time_travel(blocks=source.actionTimeLock())
    assert source.confirmNewPriceFeed(fixture.ripe.address, sender=fixture.governor)


def sync_pair(fixture, reserve0, reserve1):
    token0 = fixture.ripe if fixture.ripe_is_token0 else fixture.quote
    token1 = fixture.quote if fixture.ripe_is_token0 else fixture.ripe
    token0.setBalance(fixture.pair.address, reserve0)
    token1.setBalance(fixture.pair.address, reserve1)
    fixture.pair.sync()


def diagnostic_state(fixture, stale_time=3600, registry=None):
    if registry is None:
        registry = fixture.quote_desk.address
    return fixture.source.getSafetyStateAtStaleTime(stale_time, registry)


def diagnostic_price(fixture, stale_time=3600, registry=None):
    state = diagnostic_state(fixture, stale_time, registry)
    return state[1] if state[0] == 0 else 0


def expected_quote_per_ripe(reserve_ripe, reserve_quote, ripe_decimals, quote_decimals):
    uq = reserve_quote * Q112 // reserve_ripe
    return uq * (10 ** (18 + ripe_decimals - quote_decimals)) // Q112


def normalize_uq(uq, ripe_decimals=18, quote_decimals=18):
    return uq * (10 ** (18 + ripe_decimals - quote_decimals)) // Q112
