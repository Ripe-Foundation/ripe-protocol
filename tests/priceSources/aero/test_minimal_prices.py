from __future__ import annotations

import ast
import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path

import boa
import pytest

from constants import EIGHTEEN_DECIMALS, MAX_UINT256, ZERO_ADDRESS


ROOT = Path(__file__).resolve().parents[3]
MAX_UINT112 = 2**112 - 1
MAX_UINT32 = 2**32 - 1
ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"


MALFORMED_HQ_SOURCE = """# @version 0.4.3
responseMode: public(uint256)

@external
def setResponseMode(_mode: uint256):
    self.responseMode = _mode

@view
@external
@raw_return
def getAddr(_regId: uint256) -> Bytes[33]:
    mode: uint256 = self.responseMode
    if mode == 1:
        return slice(empty(bytes32), 0, 31)
    if mode == 2:
        return concat(empty(bytes32), b"x")
    if mode == 3:
        invalidAddressValue: uint256 = 2 ** 160
        invalidAddressWord: bytes32 = convert(invalidAddressValue, bytes32)
        return slice(invalidAddressWord, 0, 32)
    raise "forced revert"
"""


MISSION_CONTROL_SOURCE = """# @version 0.4.3
struct PriceConfig:
    staleTime: uint256
    priorityPriceSourceIds: DynArray[uint256, 10]

@view
@external
def getPriceConfig() -> PriceConfig:
    return PriceConfig(staleTime=0, priorityPriceSourceIds=[])

@view
@external
def underscoreRegistry() -> address:
    return empty(address)
"""


COMPOSITION_HQ_SOURCE = """# @version 0.4.3
hqGovernance: address
missionControl: address

@deploy
def __init__(_governance: address, _missionControl: address):
    self.hqGovernance = _governance
    self.missionControl = _missionControl

@view
@external
def governance() -> address:
    return self.hqGovernance

@view
@external
def minGovChangeTimeLock() -> uint256:
    return 1

@view
@external
def maxGovChangeTimeLock() -> uint256:
    return 100

@view
@external
def getAddr(_regId: uint256) -> address:
    if _regId == 5:
        return self.missionControl
    return empty(address)

@view
@external
def isValidAddr(_addr: address) -> bool:
    return False
"""


@dataclass
class AeroMonitorFixture:
    source: object
    pool: object
    ripe: object
    weth: object
    price_desk: object
    hq: object
    ripe_is_token0: bool


@pytest.fixture(scope="module")
def aero_factories():
    return {
        "token": boa.load_partial("contracts/mock/MockUniswapV2Token.vy"),
        "pool": boa.load_partial("contracts/mock/MockAeroRipePool.vy"),
        "price_desk": boa.load_partial(
            "contracts/mock/MockUniswapV2QuotePriceDesk.vy"
        ),
        "hq": boa.load_partial("contracts/mock/MockUniswapV2RipeHq.vy"),
        "source": boa.load_partial("contracts/priceSources/AeroRipePrices.vy"),
        "raw_source": boa.load_partial("contracts/mock/MockRawPriceSource.vy"),
        "protocol_price_desk": boa.load_partial(
            "contracts/registries/PriceDesk.vy"
        ),
        "malformed_hq": boa.loads_partial(
            MALFORMED_HQ_SOURCE, name="malformed_aero_monitor_hq"
        ),
        "mission_control": boa.loads_partial(
            MISSION_CONTROL_SOURCE, name="aero_monitor_mission_control"
        ),
        "composition_hq": boa.loads_partial(
            COMPOSITION_HQ_SOURCE, name="aero_monitor_composition_hq"
        ),
    }


@pytest.fixture
def aero_monitor_builder(aero_factories):
    def build(
        *,
        ripe_is_token0=True,
        ripe_decimals=18,
        weth_decimals=18,
        ripe_reserve=100 * EIGHTEEN_DECIMALS,
        weth_reserve=10 * EIGHTEEN_DECIMALS,
        timestamp=1_700_000_000,
        weth_usd=2_000 * EIGHTEEN_DECIMALS,
        hq_override=None,
    ):
        ripe = aero_factories["token"].deploy(ripe_decimals)
        weth = aero_factories["token"].deploy(weth_decimals)
        token0 = ripe.address if ripe_is_token0 else weth.address
        token1 = weth.address if ripe_is_token0 else ripe.address
        pool = aero_factories["pool"].deploy(token0, token1)
        reserve0 = ripe_reserve if ripe_is_token0 else weth_reserve
        reserve1 = weth_reserve if ripe_is_token0 else ripe_reserve
        pool.configureState(reserve0, reserve1, timestamp)

        price_desk = aero_factories["price_desk"].deploy()
        price_desk.setPrice(weth_usd)
        hq = aero_factories["hq"].deploy(
            boa.env.generate_address("aero-monitor-governance"),
            price_desk.address,
        )
        source = aero_factories["source"].deploy(
            hq.address if hq_override is None else hq_override,
            pool.address,
            ripe.address,
            weth.address,
        )
        return AeroMonitorFixture(
            source=source,
            pool=pool,
            ripe=ripe,
            weth=weth,
            price_desk=price_desk,
            hq=hq,
            ripe_is_token0=ripe_is_token0,
        )

    return build


@pytest.mark.parametrize("ripe_is_token0", [True, False])
def test_monitor_identity_pool_state_and_prices(
    aero_monitor_builder,
    ripe_is_token0,
):
    fixture = aero_monitor_builder(ripe_is_token0=ripe_is_token0)

    assert fixture.source.isMonitoringOnly() is True
    assert fixture.source.RIPE_HQ() == fixture.hq.address
    assert fixture.source.RIPE_WETH_POOL() == fixture.pool.address
    assert fixture.source.RIPE_TOKEN() == fixture.ripe.address
    assert fixture.source.WETH_TOKEN() == fixture.weth.address
    assert fixture.source.RIPE_IS_TOKEN0() is ripe_is_token0
    assert fixture.source.getRipePoolState() == (
        100 * EIGHTEEN_DECIMALS,
        10 * EIGHTEEN_DECIMALS,
        1_700_000_000,
    )
    assert fixture.source.getRipeWethMonitoringPrice() == EIGHTEEN_DECIMALS // 10
    assert fixture.source.getRipeUsdMonitoringPrice() == 200 * EIGHTEEN_DECIMALS
    assert fixture.source.getAeroRipePrice(
        fixture.ripe.address
    ) == fixture.source.getRipeUsdMonitoringPrice()
    assert fixture.source.getAeroRipePrice(
        boa.env.generate_address("not-ripe")
    ) == 0


@pytest.mark.parametrize("zero_field", ["hq", "pool", "ripe", "weth"])
def test_constructor_rejects_zero_required_addresses(aero_factories, zero_field):
    ripe = aero_factories["token"].deploy(18)
    weth = aero_factories["token"].deploy(18)
    pool = aero_factories["pool"].deploy(ripe.address, weth.address)
    values = {
        "hq": boa.env.generate_address("hq"),
        "pool": pool.address,
        "ripe": ripe.address,
        "weth": weth.address,
    }
    values[zero_field] = ZERO_ADDRESS

    with boa.reverts("invalid monitoring config"):
        aero_factories["source"].deploy(
            values["hq"], values["pool"], values["ripe"], values["weth"]
        )


def test_constructor_rejects_identical_tokens(aero_factories):
    token = aero_factories["token"].deploy(18)
    pool = aero_factories["pool"].deploy(token.address, token.address)
    with boa.reverts("invalid monitoring tokens"):
        aero_factories["source"].deploy(
            boa.env.generate_address("hq"),
            pool.address,
            token.address,
            token.address,
        )


def test_constructor_rejects_wrong_pair(aero_factories):
    ripe = aero_factories["token"].deploy(18)
    weth = aero_factories["token"].deploy(18)
    other = aero_factories["token"].deploy(18)
    pool = aero_factories["pool"].deploy(ripe.address, other.address)
    with boa.reverts("not ripe weth pool"):
        aero_factories["source"].deploy(
            boa.env.generate_address("hq"),
            pool.address,
            ripe.address,
            weth.address,
        )


@pytest.mark.parametrize(
    "ripe_decimals,weth_decimals,reason",
    [(6, 18, "invalid ripe decimals"), (18, 6, "invalid weth decimals")],
)
def test_constructor_rejects_noncanonical_decimals(
    aero_factories,
    ripe_decimals,
    weth_decimals,
    reason,
):
    ripe = aero_factories["token"].deploy(ripe_decimals)
    weth = aero_factories["token"].deploy(weth_decimals)
    pool = aero_factories["pool"].deploy(ripe.address, weth.address)
    with boa.reverts(reason):
        aero_factories["source"].deploy(
            boa.env.generate_address("hq"),
            pool.address,
            ripe.address,
            weth.address,
        )


@pytest.mark.parametrize("response_mode", [1, 2, 3])
def test_malformed_or_reverting_pool_fails_closed(
    aero_monitor_builder,
    response_mode,
):
    fixture = aero_monitor_builder()
    fixture.pool.setReserveResponseMode(response_mode)
    assert fixture.source.getRipePoolState() == (0, 0, 0)
    assert fixture.source.getRipeWethMonitoringPrice() == 0
    assert fixture.source.getRipeUsdMonitoringPrice() == 0
    assert fixture.source.getAeroRipePrice(fixture.ripe.address) == 0


@pytest.mark.parametrize(
    "reserve0,reserve1,timestamp",
    [
        (MAX_UINT112 + 1, 1, 1),
        (1, MAX_UINT112 + 1, 1),
        (1, 1, MAX_UINT32 + 1),
    ],
)
def test_defensive_aerodrome_bounds_fail_closed(
    aero_monitor_builder,
    reserve0,
    reserve1,
    timestamp,
):
    fixture = aero_monitor_builder()
    fixture.pool.configureState(reserve0, reserve1, timestamp)
    assert fixture.source.getRipePoolState() == (0, 0, 0)
    assert fixture.source.getRipeWethMonitoringPrice() == 0
    assert fixture.source.getRipeUsdMonitoringPrice() == 0


@pytest.mark.parametrize("ripe_reserve,weth_reserve", [(0, 1), (1, 0)])
def test_zero_reserve_zeroes_monitoring_prices(
    aero_monitor_builder,
    ripe_reserve,
    weth_reserve,
):
    fixture = aero_monitor_builder(
        ripe_reserve=ripe_reserve,
        weth_reserve=weth_reserve,
    )
    assert fixture.source.getRipeWethMonitoringPrice() == 0
    assert fixture.source.getRipeUsdMonitoringPrice() == 0
    assert fixture.source.getAeroRipePrice(fixture.ripe.address) == 0


@pytest.mark.parametrize("response_mode", [1, 2, 3, 4])
def test_unavailable_or_malformed_ripe_hq_fails_closed(
    aero_factories,
    aero_monitor_builder,
    response_mode,
):
    if response_mode == 4:
        hq = boa.env.generate_address("missing-hq")
    else:
        malformed = aero_factories["malformed_hq"].deploy()
        malformed.setResponseMode(response_mode)
        hq = malformed.address
    fixture = aero_monitor_builder(hq_override=hq)
    assert fixture.source.getRipeWethMonitoringPrice() == EIGHTEEN_DECIMALS // 10
    assert fixture.source.getRipeUsdMonitoringPrice() == 0


def test_missing_price_desk_or_weth_price_fails_closed(
    aero_factories,
    aero_monitor_builder,
):
    fixture = aero_monitor_builder(weth_usd=0)
    assert fixture.source.getRipeUsdMonitoringPrice() == 0

    missing_desk_hq = aero_factories["hq"].deploy(
        boa.env.generate_address("missing-desk-governance"),
        ZERO_ADDRESS,
    )
    fixture = aero_monitor_builder(hq_override=missing_desk_hq.address)
    assert fixture.source.getRipeUsdMonitoringPrice() == 0


@pytest.mark.parametrize("response_mode", [1, 2, 3])
def test_malformed_price_desk_response_fails_closed(
    aero_monitor_builder,
    response_mode,
):
    fixture = aero_monitor_builder()
    fixture.price_desk.setResponseMode(response_mode)
    assert fixture.source.getRipeWethMonitoringPrice() == EIGHTEEN_DECIMALS // 10
    assert fixture.source.getRipeUsdMonitoringPrice() == 0


def test_reverting_price_desk_response_fails_closed(aero_monitor_builder):
    fixture = aero_monitor_builder()
    fixture.price_desk.setShouldRevert(True)
    assert fixture.source.getRipeUsdMonitoringPrice() == 0


def test_unsafe_price_multiplication_fails_closed(aero_monitor_builder):
    fixture = aero_monitor_builder(
        ripe_reserve=1,
        weth_reserve=MAX_UINT112,
        weth_usd=MAX_UINT256,
    )
    assert (
        fixture.source.getRipeWethMonitoringPrice()
        == MAX_UINT112 * EIGHTEEN_DECIMALS
    )
    assert fixture.source.getRipeUsdMonitoringPrice() == 0
    assert fixture.source.getAeroRipePrice(fixture.ripe.address) == 0


@pytest.mark.parametrize("use_ripe", [True, False])
def test_complete_price_source_surface_is_inert(
    aero_monitor_builder,
    use_ripe,
):
    fixture = aero_monitor_builder()
    source = fixture.source
    asset = fixture.ripe.address if use_ripe else boa.env.generate_address("asset")

    assert source.getPrice(asset) == 0
    assert source.getPrice(asset, 123) == 0
    assert source.getPrice(asset, 123, fixture.price_desk.address) == 0
    assert source.getPriceAndHasFeed(asset) == (0, False)
    assert source.getPriceAndHasFeed(
        asset, 123, fixture.price_desk.address
    ) == (0, False)
    assert source.hasPriceFeed(asset) is False
    assert source.hasPendingPriceFeedUpdate(asset) is False
    assert source.getPricedAssets() == []

    for method in (
        source.addPriceSnapshot,
        source.confirmNewPriceFeed,
        source.cancelNewPendingPriceFeed,
        source.confirmPriceFeedUpdate,
        source.cancelPriceFeedUpdate,
        source.disablePriceFeed,
        source.confirmDisablePriceFeed,
        source.cancelDisablePriceFeed,
    ):
        assert method(asset) is False

    assert source.actionTimeLock() == 0
    assert source.hasPendingAction(1) is False
    assert source.getActionConfirmationBlock(1) == 0
    assert source.setActionTimeLock(1) is False
    assert source.setActionTimeLockAfterSetup() is False
    assert source.setActionTimeLockAfterSetup(1) is False
    assert source.isPaused() is False
    with boa.reverts("monitoring only"):
        source.pause(True)
    with boa.reverts("monitoring only"):
        source.recoverFunds(boa.env.generate_address("recipient"), asset)
    with boa.reverts("monitoring only"):
        source.recoverFundsMany(boa.env.generate_address("recipient"), [asset])


def _register_source(price_desk, source, governance, description):
    assert price_desk.startAddNewAddressToRegistry(
        source, description, sender=governance
    )
    return price_desk.confirmNewAddressToRegistry(source, sender=governance)


def test_price_desk_composition_treats_monitor_as_valid_no_feed(
    aero_factories,
    aero_monitor_builder,
):
    fixture = aero_monitor_builder()
    mission_control = aero_factories["mission_control"].deploy()
    hq_governance = boa.env.generate_address("hq-governance")
    local_governance = boa.env.generate_address("local-governance")
    hq = aero_factories["composition_hq"].deploy(
        hq_governance,
        mission_control.address,
    )
    price_desk = aero_factories["protocol_price_desk"].deploy(
        hq.address,
        local_governance,
        ETH,
        1,
        2,
    )
    assert _register_source(
        price_desk,
        fixture.source.address,
        local_governance,
        "inert Aero monitor",
    ) == 1

    ripe = fixture.ripe.address
    assert price_desk.hasPriceFeed(ripe) is False
    assert price_desk.getPrice(ripe, False) == 0
    assert price_desk.getPrice(ripe, True) == 0

    healthy = aero_factories["raw_source"].deploy()
    healthy.configure(77 * EIGHTEEN_DECIMALS, True)
    assert _register_source(
        price_desk,
        healthy.address,
        local_governance,
        "healthy RIPE source",
    ) == 2
    assert price_desk.hasPriceFeed(ripe) is True
    assert price_desk.getPrice(ripe, True) == 77 * EIGHTEEN_DECIMALS


class _Contract:
    def __init__(self, address):
        self.address = address


class _AeroCandidate:
    def __init__(self, hq, pool, ripe, weth):
        self.hq = hq.address
        self.pool = pool
        self.ripe = ripe
        self.weth = weth
        self.assertion_calls = []

    def isMonitoringOnly(self):
        self.assertion_calls.append("monitoring")
        return True

    def RIPE_HQ(self):
        self.assertion_calls.append("hq")
        return self.hq

    def RIPE_WETH_POOL(self):
        self.assertion_calls.append("pool")
        return self.pool

    def RIPE_TOKEN(self):
        self.assertion_calls.append("ripe")
        return self.ripe

    def WETH_TOKEN(self):
        self.assertion_calls.append("weth")
        return self.weth

    def getPriceAndHasFeed(self, asset):
        self.assertion_calls.append(("feed", asset))
        return 0, False


class _FakeMigration:
    def __init__(self):
        self.hq = _Contract("0x0000000000000000000000000000000000000001")
        self.addresses = {
            "RipePoolAero": "0x0000000000000000000000000000000000000002",
            "RipeToken": "0x0000000000000000000000000000000000000003",
            "WETH": "0x0000000000000000000000000000000000000004",
        }
        self.get_address_calls = []
        self.deployments = []
        self.candidate = None
        self._blueprint = type(
            "Blueprint",
            (),
            {"CORE_TOKENS": {"WETH": self.addresses["WETH"]}},
        )()

    def get_contract(self, name):
        assert name == "RipeHq"
        return self.hq

    def get_address(self, name):
        self.get_address_calls.append(name)
        return self.addresses[name]

    def blueprint(self):
        return self._blueprint

    def deploy(self, name, *args):
        self.deployments.append((name, args))
        self.candidate = _AeroCandidate(*args)
        return self.candidate


def _load_aero_migration():
    path = ROOT / "migrations/base-mainnet/2025082000_AeroPrices.py"
    spec = importlib.util.spec_from_file_location("aero_monitor_migration", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def test_migration_deploys_only_the_asserted_monitor():
    module, path = _load_aero_migration()
    migration = _FakeMigration()
    module.migrate(migration)

    assert len(migration.get_address_calls) == 2
    assert set(migration.get_address_calls) == {"RipePoolAero", "RipeToken"}
    assert migration.deployments == [
        (
            "AeroRipePrices",
            (
                migration.hq,
                migration.addresses["RipePoolAero"],
                migration.addresses["RipeToken"],
                migration.addresses["WETH"],
            ),
        )
    ]
    assert migration.candidate.assertion_calls == [
        "monitoring",
        "hq",
        "pool",
        "ripe",
        "weth",
        ("feed", migration.addresses["RipeToken"]),
    ]

    tree = ast.parse(path.read_text())
    calls = [
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    ]
    assert "execute" not in calls
    assert "setActionTimeLockAfterSetup" not in calls
    assert "relinquishGov" not in calls


def test_robinhood_still_omits_aero_monitor_and_pool():
    from config.BluePrint import ROBINHOOD_COMPONENT_SELECTIONS

    states = {
        row.semantic_name: (row.deployment_disposition, row.selection_state)
        for row in ROBINHOOD_COMPONENT_SELECTIONS
    }
    assert states["AeroRipePrices"] == ("omitted", "omitted")
    assert states["RipePoolAero"] == ("omitted", "omitted")


def test_committed_aero_abi_matches_monitor_surface():
    abi_path = ROOT / "scripts/abis/AeroRipePrices.json"
    entries = json.loads(abi_path.read_text())
    function_names = {
        entry["name"] for entry in entries if entry.get("type") == "function"
    }
    assert {
        "isMonitoringOnly",
        "getRipePoolState",
        "getRipeWethMonitoringPrice",
        "getRipeUsdMonitoringPrice",
        "getAeroRipePrice",
    } <= function_names
    assert {
        "priceConfigs",
        "snapShots",
        "pendingPriceConfigs",
        "getWeightedPrice",
        "getLatestSnapshot",
        "updatePriceConfig",
        "isValidPriceConfig",
        "governance",
        "relinquishGov",
    }.isdisjoint(function_names)
