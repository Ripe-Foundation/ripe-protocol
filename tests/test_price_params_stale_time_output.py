import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


PARAMS_DIR = Path(__file__).resolve().parents[1] / "scripts" / "params"
ORIGINAL_SYS_PATH = tuple(sys.path)
try:
    if str(PARAMS_DIR) not in sys.path:
        sys.path.insert(0, str(PARAMS_DIR))
    SPEC = importlib.util.spec_from_file_location(
        "ripe_operator_prices",
        PARAMS_DIR / "prices.py",
    )
    prices = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(prices)
finally:
    sys.path[:] = ORIGINAL_SYS_PATH

ASSET = "0x" + "1" * 40
FEED = "0x" + "2" * 40
OTHER_FEED = "0x" + "3" * 40
ETH = "0x" + "e" * 40
CHAINLINK = "0x" + "c" * 40
REDSTONE = "0x" + "d" * 40
INHERITED_POLICY = (
    "inherit MissionControl (stored 0; effective 86400s)"
)


@pytest.fixture(scope="session")
def ripe_hq():
    """Keep pure operator-output tests independent of protocol deployment."""


@pytest.mark.parametrize(
    ("stored", "global_stale_time", "expected"),
    (
        (345_600, 86_400, "345600s"),
        (0, 86_400, INHERITED_POLICY),
        (
            0,
            None,
            "inherit MissionControl (stored 0; effective value unavailable)",
        ),
    ),
)
def test_price_feed_stale_time_formatter_distinguishes_storage_from_policy(
    stored,
    global_stale_time,
    expected,
):
    assert (
        prices._format_price_feed_stale_time(stored, global_stale_time)
        == expected
    )


def test_mission_control_stale_time_reader_supports_current_and_legacy_abis():
    current = SimpleNamespace(getPriceStaleTime=lambda: 86_400)
    legacy = SimpleNamespace(genConfig=lambda: (5, 10, 86_400))

    assert prices._read_mission_control_stale_time(current) == 86_400
    assert prices._read_mission_control_stale_time(legacy) == 86_400
    assert prices._read_mission_control_stale_time(None) is None


def _isolate_operator_output(monkeypatch):
    monkeypatch.setattr(prices.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(prices, "get_token_name", lambda _asset: "ASSET")
    monkeypatch.setattr(prices, "format_address", lambda address: address)
    monkeypatch.setattr(prices.state, "pd", None)
    monkeypatch.setattr(prices.state, "price_sources", {})
    monkeypatch.setattr(
        prices.state,
        "mission_control_stale_time",
        86_400,
    )


def _set_cross_source_inventory(monkeypatch, redstone, feed=FEED):
    chainlink_config = SimpleNamespace(
        feed=feed,
        needsEthToUsd=False,
        needsBtcToUsd=False,
    )
    chainlink = SimpleNamespace(
        address=CHAINLINK,
        ETH=lambda: ETH,
        feedConfig=lambda _asset: chainlink_config,
    )
    monkeypatch.setattr(prices.state, "pd", SimpleNamespace(ETH=lambda: ETH))
    monkeypatch.setattr(
        prices.state,
        "price_sources",
        {
            1: {
                "address": CHAINLINK,
                "description": "Chainlink",
                "contract": chainlink,
            },
            2: {
                "address": REDSTONE,
                "description": "RedStone",
                "contract": redstone,
            },
        },
    )


def test_cross_source_match_requires_eth_conversion_and_exact_feed_address():
    discovered = {FEED.lower(): ("Chainlink (registry 1)",)}

    assert prices._matching_cross_source_eth_usd_feeds(
        FEED.upper(),
        True,
        discovered,
    ) == ("Chainlink (registry 1)",)
    assert not prices._matching_cross_source_eth_usd_feeds(
        FEED,
        False,
        discovered,
    )
    assert not prices._matching_cross_source_eth_usd_feeds(
        OTHER_FEED,
        True,
        discovered,
    )


def test_direct_eth_usd_feed_discovery_is_best_effort(monkeypatch):
    _isolate_operator_output(monkeypatch)
    redstone = SimpleNamespace(address=REDSTONE)
    _set_cross_source_inventory(monkeypatch, redstone)

    class FailingSource:
        address = "0x" + "f" * 40

        def feedConfig(self, _asset):
            raise RuntimeError("RPC")

    failing_source = FailingSource()
    prices.state.price_sources[3] = {
        "address": failing_source.address,
        "description": "Unavailable source",
        "contract": failing_source,
    }

    discovered, incomplete_reads = prices._discover_direct_eth_usd_feeds(
        redstone
    )

    assert discovered == {FEED.lower(): ("Chainlink (registry 1)",)}
    assert incomplete_reads == (
        "Unavailable source (registry 3).feedConfig",
    )


@pytest.mark.parametrize("report_kind", ("active", "pending"))
def test_redstone_rpc_failure_reports_nonfatal_incomplete_diagnostic(
    monkeypatch,
    capsys,
    report_kind,
):
    _isolate_operator_output(monkeypatch)
    config = SimpleNamespace(
        feed=OTHER_FEED,
        needsEthToUsd=True,
        needsBtcToUsd=False,
        staleTime=0,
    )
    redstone = SimpleNamespace(
        address=REDSTONE,
        assets=lambda _index: ASSET,
        feedConfig=lambda _asset: config,
        hasPendingPriceFeedUpdate=lambda _asset: True,
        pendingUpdates=lambda _asset: SimpleNamespace(
            actionId=1,
            config=config,
        ),
        getRedStoneData=lambda: None,
    )
    _set_cross_source_inventory(monkeypatch, redstone)
    chainlink = prices.state.price_sources[1]["contract"]

    def unavailable_feed_config(_asset):
        raise RuntimeError("RPC")

    chainlink.feedConfig = unavailable_feed_config
    if report_kind == "active":
        prices._print_price_source_assets(redstone, "RedStone", 2)
    else:
        prices._print_pending_price_changes(redstone, "RedStone", 2)

    output = capsys.readouterr().out
    assert "RedStone Cross-Source Diagnostic Incomplete" in output
    assert "Chainlink (registry 1).feedConfig" in output
    assert "This is nonfatal" in output
    assert "absence of a self-conversion warning is not conclusive" in output
    assert "Cross-Source ETH Conversion Warnings" not in output


def test_chainlink_style_table_renders_zero_as_effective_inheritance(
    monkeypatch,
    capsys,
):
    _isolate_operator_output(monkeypatch)
    config = SimpleNamespace(
        feed=FEED,
        needsEthToUsd=False,
        needsBtcToUsd=False,
        staleTime=0,
    )
    source = SimpleNamespace(
        assets=lambda _index: ASSET,
        feedConfig=lambda _asset: config,
    )

    prices._print_price_source_assets(source, "Chainlink", 2)

    output = capsys.readouterr().out
    assert INHERITED_POLICY in output
    assert "| ASSET |" in output


def test_redstone_active_config_warns_on_cross_source_self_conversion(
    monkeypatch,
    capsys,
):
    _isolate_operator_output(monkeypatch)
    config = SimpleNamespace(
        feed=FEED,
        needsEthToUsd=True,
        needsBtcToUsd=False,
        staleTime=0,
    )
    redstone = SimpleNamespace(
        address=REDSTONE,
        assets=lambda _index: ASSET,
        feedConfig=lambda _asset: config,
        getRedStoneData=lambda: None,
    )
    _set_cross_source_inventory(monkeypatch, redstone)

    prices._print_price_source_assets(redstone, "RedStone", 2)

    output = capsys.readouterr().out
    assert "RedStone Cross-Source ETH Conversion Warnings" in output
    assert "Chainlink (registry 1)" in output
    assert "self-conversion hazard" in output


def test_redstone_unknown_feed_does_not_warn(monkeypatch, capsys):
    _isolate_operator_output(monkeypatch)
    config = SimpleNamespace(
        feed=OTHER_FEED,
        needsEthToUsd=True,
        needsBtcToUsd=False,
        staleTime=0,
    )
    redstone = SimpleNamespace(
        address=REDSTONE,
        assets=lambda _index: ASSET,
        feedConfig=lambda _asset: config,
        getRedStoneData=lambda: None,
    )
    _set_cross_source_inventory(monkeypatch, redstone)

    prices._print_price_source_assets(redstone, "RedStone", 2)

    assert "Cross-Source ETH Conversion Warnings" not in capsys.readouterr().out


@pytest.mark.parametrize("is_pyth", (False, True))
def test_feed_id_output_renders_zero_as_effective_inheritance(
    monkeypatch,
    capsys,
    is_pyth,
):
    _isolate_operator_output(monkeypatch)
    config = SimpleNamespace(feedId=b"\x01" * 32, staleTime=0)

    class FeedIdSource:
        def assets(self, _index):
            return ASSET

        def feedConfig(self, _asset):
            return config

    source = FeedIdSource()
    if is_pyth:
        source.maxConfidenceRatio = lambda: 100

    prices._print_price_source_assets(source, "Feed ID source", 2)

    output = capsys.readouterr().out
    assert INHERITED_POLICY in output
    expected_header = "Pyth Feed Configs" if is_pyth else "Stork Feed Configs"
    assert expected_header in output


def test_pending_feed_update_renders_zero_as_effective_inheritance(
    monkeypatch,
    capsys,
):
    _isolate_operator_output(monkeypatch)
    pending = SimpleNamespace(
        actionId=1,
        config=SimpleNamespace(staleTime=0),
    )
    source = SimpleNamespace(
        assets=lambda _index: ASSET,
        hasPendingPriceFeedUpdate=lambda _asset: True,
        pendingUpdates=lambda _asset: pending,
    )

    prices._print_pending_price_changes(source, "Chainlink", 2)

    output = capsys.readouterr().out
    assert f"Pending Stale Time: {INHERITED_POLICY}" in output


def test_pending_redstone_config_warns_before_confirmation(
    monkeypatch,
    capsys,
):
    _isolate_operator_output(monkeypatch)
    pending = SimpleNamespace(
        actionId=1,
        config=SimpleNamespace(
            feed=FEED,
            needsEthToUsd=True,
            staleTime=0,
        ),
    )
    redstone = SimpleNamespace(
        address=REDSTONE,
        assets=lambda _index: ASSET,
        hasPendingPriceFeedUpdate=lambda _asset: True,
        pendingUpdates=lambda _asset: pending,
        getRedStoneData=lambda: None,
    )
    _set_cross_source_inventory(monkeypatch, redstone)

    prices._print_pending_price_changes(redstone, "RedStone", 2)

    output = capsys.readouterr().out
    assert "Cross-source ETH conversion warning" in output
    assert "before confirmation or activation" in output
    assert "Chainlink (registry 1)" in output
