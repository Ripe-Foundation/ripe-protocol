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
    "stored 0s; global 86400s; inherit MissionControl; effective 86400s"
)


@pytest.fixture(scope="session")
def ripe_hq():
    """Keep pure operator-output tests independent of protocol deployment."""


@pytest.mark.parametrize(
    ("generation", "stored", "global_stale_time", "expected"),
    (
        (
            prices.STALE_TIME_GENERATION_LEGACY,
            345_600,
            86_400,
            "stored 345600s; global 86400s; legacy cap; effective 86400s",
        ),
        (
            prices.STALE_TIME_GENERATION_LEGACY,
            345_600,
            0,
            "stored 345600s; global 0s; legacy fallback; effective 345600s",
        ),
        (
            prices.STALE_TIME_GENERATION_LEGACY,
            0,
            86_400,
            "stored 0s; global 86400s; legacy fallback; effective 86400s",
        ),
        (
            prices.STALE_TIME_GENERATION_LEGACY,
            0,
            0,
            "stored 0s; global 0s; legacy zero/zero; freshness unenforced",
        ),
        (
            prices.STALE_TIME_GENERATION_CURRENT,
            345_600,
            86_400,
            (
                "stored 345600s; global 86400s; exact local override; "
                "effective 345600s"
            ),
        ),
        (
            prices.STALE_TIME_GENERATION_CURRENT,
            345_600,
            0,
            (
                "stored 345600s; global 0s; exact local override; "
                "effective 345600s"
            ),
        ),
        (
            prices.STALE_TIME_GENERATION_CURRENT,
            0,
            86_400,
            INHERITED_POLICY,
        ),
        (
            prices.STALE_TIME_GENERATION_CURRENT,
            0,
            0,
            "stored 0s; global 0s; inherited global out of range; invalid/fail-closed",
        ),
        (
            prices.STALE_TIME_GENERATION_CURRENT,
            299,
            86_400,
            (
                "stored 299s; global 86400s; local override out of range; "
                "invalid/fail-closed"
            ),
        ),
        (
            prices.STALE_TIME_GENERATION_CURRENT,
            604_801,
            86_400,
            (
                "stored 604801s; global 86400s; local override out of range; "
                "invalid/fail-closed"
            ),
        ),
        (
            prices.STALE_TIME_GENERATION_CURRENT,
            0,
            604_801,
            (
                "stored 0s; global 604801s; inherited global out of range; "
                "invalid/fail-closed"
            ),
        ),
        (
            prices.STALE_TIME_GENERATION_UNKNOWN,
            345_600,
            86_400,
            (
                "stored 345600s; global 86400s; unknown generation; "
                "effective stale-time semantics not asserted"
            ),
        ),
        (
            prices.STALE_TIME_GENERATION_UNKNOWN,
            0,
            0,
            (
                "stored 0s; global 0s; unknown generation; "
                "effective stale-time semantics not asserted"
            ),
        ),
    ),
)
def test_price_feed_stale_time_formatter_uses_generation_truth_table(
    generation,
    stored,
    global_stale_time,
    expected,
):
    assert (
        prices._format_price_feed_stale_time(
            stored,
            global_stale_time,
            generation,
        )
        == expected
    )


def test_new_compatible_unrecognized_runtime_is_labeled_without_overclaiming():
    output = prices._format_price_feed_stale_time(
        345_600,
        86_400,
        prices.STALE_TIME_GENERATION_NEW_COMPATIBLE,
    )
    assert output.startswith(
        "new-compatible ABI, unrecognized codehash; expected new meaning: "
    )
    assert "exact local override; effective 345600s" in output


def test_conversion_route_formatter_scopes_effective_time_to_primary_leg():
    output = prices._format_route_stale_time(
        345_600,
        86_400,
        prices.STALE_TIME_GENERATION_CURRENT,
        needs_eth_to_usd=True,
    )

    assert output.startswith("primary-feed policy: ")
    assert "exact local override; effective 345600s" in output
    assert "final route also depends on the ETH anchor" in output
    assert "independently resolved policy" in output


@pytest.mark.parametrize("stored", (300, 604_800))
def test_current_formatter_accepts_exact_local_boundaries(stored):
    output = prices._format_price_feed_stale_time(
        stored,
        86_400,
        prices.STALE_TIME_GENERATION_CURRENT,
    )
    assert f"exact local override; effective {stored}s" in output


def test_manifest_bound_legacy_runtime_hash_inventory_is_exact():
    assert prices.KNOWN_LEGACY_STALE_TIME_RUNTIME_HASHES == {
        "0xb9a7cbdb193aeefb73fff5c17edd408dfe607cdbf1e2ea4aefe13da92682e99a",
        "0xd9fac1cfeddae2b19e47dbea1b59d0eccd2df32e96f420e801ee4fc4d974e482",
        "0x8b690e5d15f204e5656e084832d8805a5b921913c237cc0132074494dd87c648",
        "0x6ed75e536af6436a82fb3372b22795fb601ac11c3ea2c3f60ee7b78fb0cc7351",
    }
    assert prices.KNOWN_CURRENT_STALE_TIME_RUNTIME_HASHES == set()
    assert prices.EXPECTED_CURRENT_PRICE_DESK_RUNTIME_HASH is None


def test_stale_source_detection_does_not_depend_on_registry_description():
    legacy_hash = next(iter(prices.KNOWN_LEGACY_STALE_TIME_RUNTIME_HASHES))
    current_abi = SimpleNamespace(isValidStaleTimeUpdate=lambda *_args: True)

    assert prices._is_stale_time_feed_source(
        SimpleNamespace(),
        "Renamed Source",
        legacy_hash,
    )
    assert prices._is_stale_time_feed_source(
        current_abi,
        "Renamed Source",
        "0xunrecognized",
    )
    assert not prices._is_stale_time_feed_source(
        SimpleNamespace(),
        "Renamed Source",
        "0xunrecognized",
    )


@pytest.mark.parametrize(
    ("runtime_hash", "has_current_abi", "expected"),
    (
        ("0xlegacy", False, prices.STALE_TIME_GENERATION_LEGACY),
        ("0xcurrent", True, prices.STALE_TIME_GENERATION_CURRENT),
        (
            "0xunrecognized",
            True,
            prices.STALE_TIME_GENERATION_NEW_COMPATIBLE,
        ),
        ("0xunrecognized", False, prices.STALE_TIME_GENERATION_UNKNOWN),
        (None, False, prices.STALE_TIME_GENERATION_UNKNOWN),
    ),
)
def test_generation_classifier_prefers_exact_hash_then_abi_capability(
    monkeypatch,
    runtime_hash,
    has_current_abi,
    expected,
):
    source = SimpleNamespace(address=CHAINLINK)
    if has_current_abi:
        source.isValidStaleTimeUpdate = lambda *_args: True
    monkeypatch.setattr(prices, "_runtime_code_hash", lambda _source: runtime_hash)

    generation, observed_hash = prices._classify_stale_time_generation(
        source,
        known_legacy_hashes={"0xlegacy"},
        known_current_hashes={"0xcurrent"},
    )

    assert generation == expected
    assert observed_hash == runtime_hash


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

    assert prices._matching_cross_source_eth_route_primary_feeds(
        FEED.upper(),
        True,
        discovered,
    ) == ("Chainlink (registry 1)",)
    assert not prices._matching_cross_source_eth_route_primary_feeds(
        FEED,
        False,
        discovered,
    )
    assert not prices._matching_cross_source_eth_route_primary_feeds(
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

    discovered, incomplete_reads = prices._discover_eth_route_primary_feeds(
        redstone
    )

    assert discovered == {FEED.lower(): ("Chainlink (registry 1)",)}
    assert incomplete_reads == (
        "Unavailable source (registry 3).feedConfig",
    )


def test_direct_eth_usd_feed_discovery_includes_pending_anchor(monkeypatch):
    _isolate_operator_output(monkeypatch)
    redstone = SimpleNamespace(address=REDSTONE)
    active = SimpleNamespace(
        feed=OTHER_FEED,
        needsEthToUsd=False,
        needsBtcToUsd=False,
    )
    pending = SimpleNamespace(
        actionId=1,
        config=SimpleNamespace(
            feed=FEED,
            needsEthToUsd=False,
            needsBtcToUsd=False,
        ),
    )
    chainlink = SimpleNamespace(
        address=CHAINLINK,
        ETH=lambda: ETH,
        feedConfig=lambda _asset: active,
        pendingUpdates=lambda _asset: pending,
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

    discovered, incomplete = prices._discover_eth_route_primary_feeds(redstone)

    assert discovered[OTHER_FEED.lower()] == ("Chainlink (registry 1)",)
    assert discovered[FEED.lower()] == ("Chainlink (registry 1), pending",)
    assert incomplete == ()


def test_direct_eth_route_discovery_keeps_converting_primary_feed(monkeypatch):
    _isolate_operator_output(monkeypatch)
    redstone = SimpleNamespace(address=REDSTONE)
    converting_eth = SimpleNamespace(
        feed=FEED,
        needsEthToUsd=False,
        needsBtcToUsd=True,
    )
    chainlink = SimpleNamespace(
        address=CHAINLINK,
        ETH=lambda: ETH,
        feedConfig=lambda _asset: converting_eth,
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

    discovered, incomplete = prices._discover_eth_route_primary_feeds(redstone)

    assert discovered[FEED.lower()] == (
        "Chainlink (registry 1), converts via BTC",
    )
    assert incomplete == ()


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

    prices._print_price_source_assets(
        source,
        "Chainlink",
        2,
        prices.STALE_TIME_GENERATION_CURRENT,
    )

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

    prices._print_price_source_assets(
        source,
        "Feed ID source",
        2,
        prices.STALE_TIME_GENERATION_CURRENT,
    )

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

    prices._print_pending_price_changes(
        source,
        "Chainlink",
        2,
        prices.STALE_TIME_GENERATION_CURRENT,
    )

    output = capsys.readouterr().out
    assert f"Pending Stale Time: {INHERITED_POLICY}" in output


def test_pending_feed_update_uses_timelock_confirmation_block_api(
    monkeypatch,
    capsys,
):
    _isolate_operator_output(monkeypatch)
    pending = SimpleNamespace(
        actionId=7,
        config=SimpleNamespace(staleTime=0),
    )

    class PendingSource:
        def assets(self, _index):
            return ASSET

        def hasPendingPriceFeedUpdate(self, _asset):
            return True

        def pendingUpdates(self, _asset):
            return pending

        def getActionConfirmationBlock(self, action_id):
            assert action_id == 7
            return 123_456

        def actions(self, _action_id):
            pytest.fail("the nonexistent actions getter must not be used")

    prices._print_pending_price_changes(
        PendingSource(),
        "Chainlink",
        2,
        prices.STALE_TIME_GENERATION_CURRENT,
    )

    assert "Confirm Block: 123456" in capsys.readouterr().out


def test_pending_price_config_uses_timelock_confirmation_block_api(
    monkeypatch,
    capsys,
):
    _isolate_operator_output(monkeypatch)
    pending = SimpleNamespace(
        actionId=8,
        config=SimpleNamespace(
            underlyingAsset=OTHER_FEED,
            staleTime=300,
        ),
    )
    source = SimpleNamespace(
        assets=lambda _index: ASSET,
        hasPendingPriceFeedUpdate=lambda _asset: True,
        pendingPriceConfigs=lambda _asset: pending,
        getActionConfirmationBlock=lambda action_id: (
            654_321
            if action_id == 8
            else pytest.fail("unexpected action id")
        ),
        actions=lambda _action_id: pytest.fail(
            "the nonexistent actions getter must not be used"
        ),
    )

    prices._print_pending_price_changes(source, "BlueChipYield", 2)

    assert "Confirm Block: 654321" in capsys.readouterr().out


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


def test_cached_cross_source_inventory_is_reused_for_active_and_pending_output(
    monkeypatch,
    capsys,
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
        pendingUpdates=lambda _asset: SimpleNamespace(actionId=1, config=config),
        getRedStoneData=lambda: None,
    )
    inventory = ({}, ())
    monkeypatch.setattr(
        prices,
        "_discover_eth_route_primary_feeds",
        lambda _source: pytest.fail("cached discovery was not reused"),
    )

    prices._print_price_source_assets(
        redstone,
        "RedStone",
        2,
        prices.STALE_TIME_GENERATION_CURRENT,
        inventory,
    )
    prices._print_pending_price_changes(
        redstone,
        "RedStone",
        2,
        prices.STALE_TIME_GENERATION_CURRENT,
        inventory,
    )
    capsys.readouterr()


def _strict_redstone_source(
    active,
    *,
    pending=None,
    eth_config=None,
    pending_eth=None,
    asset=ASSET,
    extra_live_action_ids=(),
):
    direct_eth = eth_config
    if direct_eth is None:
        direct_eth = (
            active
            if str(asset).lower() == ETH.lower()
            else SimpleNamespace(
                feed="0x" + "9" * 40,
                needsEthToUsd=False,
                needsBtcToUsd=False,
            )
        )
    empty_pending = SimpleNamespace(actionId=0)

    def feed_config(requested_asset):
        if str(requested_asset).lower() == ETH.lower():
            return direct_eth
        return active

    def pending_updates(requested_asset):
        if str(requested_asset).lower() == ETH.lower():
            return pending_eth or empty_pending
        return pending or empty_pending

    live_ids = set(extra_live_action_ids)
    for candidate in (pending, pending_eth):
        action_id = int(getattr(candidate, "actionId", 0))
        if action_id != 0:
            live_ids.add(action_id)
    next_action_id = max(live_ids, default=0) + 1
    return SimpleNamespace(
        ETH=lambda: ETH,
        assets=lambda _index: asset,
        feedConfig=feed_config,
        pendingUpdates=pending_updates,
        actionId=lambda: next_action_id,
        hasPendingAction=lambda action_id: action_id in live_ids,
    )


def test_strict_redstone_activation_fails_on_exact_cross_source_collision():
    config = SimpleNamespace(
        feed=FEED,
        needsEthToUsd=True,
        needsBtcToUsd=False,
    )
    redstone = _strict_redstone_source(config)
    inventory = ({FEED.lower(): ("Chainlink (registry 1)",)}, ())

    with pytest.raises(
        RuntimeError,
        match="^REDSTONE_ACTIVATION_QUALIFICATION_FAILED:collisions=",
    ):
        prices._qualify_redstone_activation(redstone, 2, inventory)


def test_strict_redstone_activation_checks_pending_candidate_collision():
    active = SimpleNamespace(
        feed=OTHER_FEED,
        needsEthToUsd=True,
        needsBtcToUsd=False,
    )
    pending = SimpleNamespace(
        actionId=7,
        config=SimpleNamespace(
            feed=FEED,
            needsEthToUsd=True,
            needsBtcToUsd=False,
        ),
    )
    redstone = _strict_redstone_source(active, pending=pending)
    inventory = ({FEED.lower(): ("Chainlink (registry 1)",)}, ())

    with pytest.raises(RuntimeError, match="collisions=pending:"):
        prices._qualify_redstone_activation(redstone, 2, inventory)


def test_strict_redstone_activation_fails_closed_on_incomplete_discovery():
    redstone = SimpleNamespace()
    inventory = ({}, ("Chainlink (registry 1).feedConfig",))

    with pytest.raises(RuntimeError, match="incomplete=Chainlink"):
        prices._qualify_redstone_activation(redstone, 1, inventory)


def test_strict_redstone_activation_accepts_complete_collision_free_inventory():
    config = SimpleNamespace(
        feed=OTHER_FEED,
        needsEthToUsd=True,
        needsBtcToUsd=False,
    )
    redstone = _strict_redstone_source(config)
    inventory = ({FEED.lower(): ("Chainlink (registry 1)",)}, ())

    assert prices._qualify_redstone_activation(redstone, 2, inventory)


def test_strict_redstone_activation_fails_on_unmatched_pending_new_asset():
    config = SimpleNamespace(
        feed=OTHER_FEED,
        needsEthToUsd=False,
        needsBtcToUsd=False,
    )
    redstone = _strict_redstone_source(
        config,
        extra_live_action_ids=(2,),
    )

    with pytest.raises(RuntimeError, match="unmatched-actions=2"):
        prices._qualify_redstone_activation(redstone, 2, ({}, ()))


@pytest.mark.parametrize(
    ("asset", "active", "eth_config", "reason"),
    (
        (
            ETH,
            SimpleNamespace(
                feed=OTHER_FEED,
                needsEthToUsd=True,
                needsBtcToUsd=False,
            ),
            None,
            "asset is ETH",
        ),
        (
            ASSET,
            SimpleNamespace(
                feed=FEED,
                needsEthToUsd=True,
                needsBtcToUsd=False,
            ),
            SimpleNamespace(
                feed=FEED,
                needsEthToUsd=False,
                needsBtcToUsd=False,
            ),
            "primary feed equals active ETH feed",
        ),
        (
            ASSET,
            SimpleNamespace(
                feed=OTHER_FEED,
                needsEthToUsd=True,
                needsBtcToUsd=False,
            ),
            SimpleNamespace(
                feed=FEED,
                needsEthToUsd=True,
                needsBtcToUsd=False,
            ),
            "active ETH config also needs ETH conversion",
        ),
    ),
)
def test_strict_redstone_activation_mirrors_local_route_invariants(
    asset,
    active,
    eth_config,
    reason,
):
    redstone = _strict_redstone_source(
        active,
        asset=asset,
        eth_config=eth_config,
    )

    with pytest.raises(RuntimeError, match="local-hazards=") as exc_info:
        prices._qualify_redstone_activation(redstone, 2, ({}, ()))
    assert reason in str(exc_info.value)


def test_strict_redstone_activation_checks_pending_eth_anchor_state():
    active = SimpleNamespace(
        feed=OTHER_FEED,
        needsEthToUsd=True,
        needsBtcToUsd=False,
    )
    pending_eth = SimpleNamespace(
        actionId=3,
        config=SimpleNamespace(
            feed=FEED,
            needsEthToUsd=True,
            needsBtcToUsd=False,
        ),
    )
    redstone = _strict_redstone_source(active, pending_eth=pending_eth)

    with pytest.raises(RuntimeError, match="pending ETH config"):
        prices._qualify_redstone_activation(redstone, 2, ({}, ()))


def test_strict_price_desk_registry_rejects_pending_update_and_disable(monkeypatch):
    _isolate_operator_output(monkeypatch)
    prices.state.pd = SimpleNamespace(
        numAddrs=lambda: 3,
        pendingAddrUpdate=lambda reg_id: SimpleNamespace(
            newAddr=OTHER_FEED,
            confirmBlock=10 if reg_id == 1 else 0,
        ),
        pendingAddrDisable=lambda reg_id: SimpleNamespace(
            confirmBlock=10 if reg_id == 2 else 0,
        ),
    )

    with pytest.raises(RuntimeError, match="pending=update:1:") as exc_info:
        prices._qualify_price_desk_registry_stability()
    assert "disable:2" in str(exc_info.value)


def test_strict_price_desk_registry_accepts_stable_existing_ids(monkeypatch):
    _isolate_operator_output(monkeypatch)
    prices.state.pd = SimpleNamespace(
        numAddrs=lambda: 3,
        pendingAddrUpdate=lambda _reg_id: SimpleNamespace(confirmBlock=0),
        pendingAddrDisable=lambda _reg_id: SimpleNamespace(confirmBlock=0),
    )

    assert prices._qualify_price_desk_registry_stability()


def _stale_policy_source(active_stale, pending=None, live_ids=()):
    active = SimpleNamespace(staleTime=active_stale)
    empty_pending = SimpleNamespace(actionId=0)
    pending_action_ids = set(live_ids)
    pending_action_id = int(getattr(pending, "actionId", 0))
    if pending_action_id != 0:
        pending_action_ids.add(pending_action_id)
    return SimpleNamespace(
        numAssets=lambda: 2,
        assets=lambda _index: ASSET,
        feedConfig=lambda _asset: active,
        pendingUpdates=lambda _asset: pending or empty_pending,
        actionId=lambda: max(pending_action_ids, default=0) + 1,
        hasPendingAction=lambda action_id: action_id in pending_action_ids,
    )


@pytest.mark.parametrize("active_stale", (1, 299, 604_801))
def test_strict_source_policy_rejects_invalid_active_local_stale_time(active_stale):
    with pytest.raises(RuntimeError, match="invalid=active:"):
        prices._qualify_source_stale_time_policies(
            1,
            _stale_policy_source(active_stale),
        )


def test_strict_source_policy_rejects_invalid_pending_local_stale_time():
    pending = SimpleNamespace(
        actionId=1,
        config=SimpleNamespace(staleTime=604_801),
    )
    with pytest.raises(RuntimeError, match="invalid=pending:"):
        prices._qualify_source_stale_time_policies(
            1,
            _stale_policy_source(0, pending),
        )


@pytest.mark.parametrize("active_stale", (0, 300, 604_800))
def test_strict_source_policy_accepts_valid_local_stale_time(active_stale):
    assert prices._qualify_source_stale_time_policies(
        1,
        _stale_policy_source(active_stale),
    )


def test_strict_source_policy_rejects_unmatched_new_asset_action():
    with pytest.raises(RuntimeError, match="unmatched-actions=2"):
        prices._qualify_source_stale_time_policies(
            1,
            _stale_policy_source(0, live_ids=(2,)),
        )


def test_strict_source_policy_rejects_inactive_mapped_action():
    pending = SimpleNamespace(
        actionId=2,
        config=SimpleNamespace(staleTime=300),
    )
    source = _stale_policy_source(0, pending)
    source.hasPendingAction = lambda _action_id: False

    with pytest.raises(RuntimeError, match=r"inactiveMappedAction\(2\)"):
        prices._qualify_source_stale_time_policies(1, source)


def test_post_pointer_strict_gate_requires_zero_live_source_actions():
    source = _stale_policy_source(0, live_ids=(2,))

    with pytest.raises(RuntimeError, match="registry-1:live=2"):
        prices._qualify_source_has_no_pending_actions(1, source)


def test_post_pointer_strict_gate_accepts_source_without_live_actions():
    assert prices._qualify_source_has_no_pending_actions(
        1,
        _stale_policy_source(0),
    )


def test_strict_activation_requires_bound_price_desk_runtime(monkeypatch):
    _isolate_operator_output(monkeypatch)

    with pytest.raises(RuntimeError, match="expected-runtime=empty"):
        prices._qualify_exact_price_desk_runtime()


def test_strict_activation_rejects_wrong_price_desk_runtime(monkeypatch):
    _isolate_operator_output(monkeypatch)
    monkeypatch.setattr(
        prices,
        "EXPECTED_CURRENT_PRICE_DESK_RUNTIME_HASH",
        "0xexpected",
    )
    monkeypatch.setattr(prices.state, "pd", SimpleNamespace(address=CHAINLINK))
    monkeypatch.setattr(prices, "_runtime_code_hash", lambda _desk: "0xwrong")

    with pytest.raises(RuntimeError, match="observed=0xwrong:expected=0xexpected"):
        prices._qualify_exact_price_desk_runtime()


def test_strict_activation_accepts_exact_price_desk_runtime(monkeypatch):
    _isolate_operator_output(monkeypatch)
    monkeypatch.setattr(
        prices,
        "EXPECTED_CURRENT_PRICE_DESK_RUNTIME_HASH",
        "0xexpected",
    )
    monkeypatch.setattr(prices.state, "pd", SimpleNamespace(address=CHAINLINK))
    monkeypatch.setattr(
        prices,
        "_runtime_code_hash",
        lambda desk: "0xexpected" if desk is prices.state.pd else "0xwrong",
    )

    assert prices._qualify_exact_price_desk_runtime()


@pytest.mark.parametrize(
    "generation",
    (
        prices.STALE_TIME_GENERATION_NEW_COMPATIBLE,
        prices.STALE_TIME_GENERATION_UNKNOWN,
    ),
)
def test_strict_activation_rejects_non_exact_source_generation(
    monkeypatch,
    generation,
):
    _isolate_operator_output(monkeypatch)
    prices.state.price_sources = {
        1: {
            "description": "Chainlink",
            "contract": SimpleNamespace(),
            "stale_time_generation": generation,
            "runtime_hash": "0xunrecognized",
        }
    }

    with pytest.raises(
        RuntimeError,
        match="^PRICE_SOURCE_GENERATION_QUALIFICATION_FAILED:",
    ):
        prices._qualify_exact_stale_time_generations_and_global_policy()


def test_strict_activation_does_not_skip_renamed_known_stale_runtime(monkeypatch):
    _isolate_operator_output(monkeypatch)
    legacy_hash = next(iter(prices.KNOWN_LEGACY_STALE_TIME_RUNTIME_HASHES))
    prices.state.price_sources = {
        1: {
            "description": "Renamed Source",
            "contract": SimpleNamespace(),
            "stale_time_generation": prices.STALE_TIME_GENERATION_UNKNOWN,
            "runtime_hash": legacy_hash,
        }
    }

    with pytest.raises(RuntimeError, match="registry-1=unknown"):
        prices._qualify_exact_stale_time_generations_and_global_policy()


@pytest.mark.parametrize("global_stale_time", (None, 0, 604_801))
def test_strict_activation_rejects_global_policy_outside_launch_bounds(
    monkeypatch,
    global_stale_time,
):
    _isolate_operator_output(monkeypatch)
    prices.state.mission_control_stale_time = global_stale_time
    prices.state.price_sources = {}

    with pytest.raises(RuntimeError, match="global="):
        prices._qualify_exact_stale_time_generations_and_global_policy()


@pytest.mark.parametrize("global_stale_time", (86_400,))
def test_strict_activation_accepts_exact_generation_and_bounded_global_policy(
    monkeypatch,
    global_stale_time,
):
    _isolate_operator_output(monkeypatch)
    monkeypatch.setattr(
        prices,
        "KNOWN_CURRENT_STALE_TIME_RUNTIME_HASHES",
        {"0xrecognized"},
    )
    prices.state.mission_control_stale_time = global_stale_time
    prices.state.price_sources = {
        1: {
            "description": "Chainlink",
            "contract": SimpleNamespace(),
            "stale_time_generation": prices.STALE_TIME_GENERATION_CURRENT,
            "runtime_hash": "0xrecognized",
        }
    }

    assert prices._qualify_exact_stale_time_generations_and_global_policy()


@pytest.mark.parametrize("global_stale_time", (1, 299, 300, 604_800))
def test_strict_activation_rejects_valid_global_that_misses_expected_policy(
    monkeypatch,
    global_stale_time,
):
    _isolate_operator_output(monkeypatch)
    prices.state.mission_control_stale_time = global_stale_time
    prices.state.price_sources = {}

    with pytest.raises(RuntimeError, match="expected=86400"):
        prices._qualify_exact_stale_time_generations_and_global_policy()


@pytest.mark.parametrize("expected_global", (1, 299, 300, 604_800))
def test_strict_activation_allows_explicit_reviewed_global_policy(
    monkeypatch,
    expected_global,
):
    _isolate_operator_output(monkeypatch)
    monkeypatch.setattr(
        prices,
        "KNOWN_CURRENT_STALE_TIME_RUNTIME_HASHES",
        {"0xrecognized"},
    )
    prices.state.mission_control_stale_time = expected_global
    prices.state.price_sources = {
        1: {
            "description": "Chainlink",
            "contract": SimpleNamespace(),
            "stale_time_generation": prices.STALE_TIME_GENERATION_CURRENT,
            "runtime_hash": "0xrecognized",
        }
    }

    assert prices._qualify_exact_stale_time_generations_and_global_policy(
        expected_global
    )


def test_strict_activation_requires_bound_current_runtime_inventory(monkeypatch):
    _isolate_operator_output(monkeypatch)
    prices.state.price_sources = {}

    with pytest.raises(
        RuntimeError,
        match="expected-current-runtime-inventory=empty",
    ):
        prices._qualify_exact_stale_time_generations_and_global_policy()


def test_strict_activation_rejects_missing_and_duplicate_current_runtime(monkeypatch):
    _isolate_operator_output(monkeypatch)
    monkeypatch.setattr(
        prices,
        "KNOWN_CURRENT_STALE_TIME_RUNTIME_HASHES",
        {"0xchainlink", "0xpyth"},
    )
    prices.state.price_sources = {
        1: {
            "description": "Chainlink",
            "contract": SimpleNamespace(),
            "stale_time_generation": prices.STALE_TIME_GENERATION_CURRENT,
            "runtime_hash": "0xchainlink",
        },
        2: {
            "description": "Renamed Source",
            "contract": SimpleNamespace(),
            "stale_time_generation": prices.STALE_TIME_GENERATION_CURRENT,
            "runtime_hash": "0xchainlink",
        },
    }

    with pytest.raises(RuntimeError) as exc_info:
        prices._qualify_exact_stale_time_generations_and_global_policy()
    assert "missing-current=0xpyth" in str(exc_info.value)
    assert "duplicate-current=0xchainlink" in str(exc_info.value)


def test_strict_activation_accepts_complete_unique_current_runtime_inventory(
    monkeypatch,
):
    _isolate_operator_output(monkeypatch)
    monkeypatch.setattr(
        prices,
        "KNOWN_CURRENT_STALE_TIME_RUNTIME_HASHES",
        {"0xchainlink", "0xpyth"},
    )
    prices.state.price_sources = {
        1: {
            "description": "Chainlink",
            "contract": SimpleNamespace(),
            "stale_time_generation": prices.STALE_TIME_GENERATION_CURRENT,
            "runtime_hash": "0xchainlink",
        },
        2: {
            "description": "Pyth",
            "contract": SimpleNamespace(),
            "stale_time_generation": prices.STALE_TIME_GENERATION_CURRENT,
            "runtime_hash": "0xpyth",
        },
    }

    assert prices._qualify_exact_stale_time_generations_and_global_policy()


def test_strict_activation_rejects_recognized_legacy_generation(monkeypatch):
    _isolate_operator_output(monkeypatch)
    legacy_hash = next(iter(prices.KNOWN_LEGACY_STALE_TIME_RUNTIME_HASHES))
    prices.state.price_sources = {
        1: {
            "description": "Chainlink",
            "contract": SimpleNamespace(),
            "stale_time_generation": prices.STALE_TIME_GENERATION_LEGACY,
            "runtime_hash": legacy_hash,
        }
    }

    with pytest.raises(RuntimeError, match="registry-1=legacy"):
        prices._qualify_exact_stale_time_generations_and_global_policy()


def test_strict_activation_orchestrates_every_post_pointer_qualification(
    monkeypatch,
):
    _isolate_operator_output(monkeypatch)
    chainlink = SimpleNamespace(label="Chainlink")
    pyth = SimpleNamespace(label="Pyth")
    redstone = SimpleNamespace(label="RedStone", numAssets=lambda: 4)
    stork = SimpleNamespace(label="Stork")
    prices.state.price_sources = {
        1: {
            "description": "Chainlink",
            "contract": chainlink,
            "runtime_hash": "0xchainlink",
        },
        2: {
            "description": "Pyth",
            "contract": pyth,
            "runtime_hash": "0xpyth",
        },
        3: {
            "description": "RedStone",
            "contract": redstone,
            "runtime_hash": "0xredstone",
            "cross_source_inventory": ({}, ()),
        },
        4: {
            "description": "Stork",
            "contract": stork,
            "runtime_hash": "0xstork",
        },
    }
    calls = []

    monkeypatch.setattr(
        prices,
        "_is_stale_time_feed_source",
        lambda _source, _description, _runtime_hash=None: True,
    )
    monkeypatch.setattr(
        prices,
        "_is_chainlink_source",
        lambda _source, description: description == "Chainlink",
    )
    monkeypatch.setattr(
        prices,
        "_is_redstone_source",
        lambda _source, description: description == "RedStone",
    )
    monkeypatch.setattr(
        prices,
        "_qualify_price_desk_registry_stability",
        lambda: calls.append("price-desk-registry"),
    )
    monkeypatch.setattr(
        prices,
        "_qualify_exact_price_desk_runtime",
        lambda: calls.append("price-desk-runtime"),
    )
    monkeypatch.setattr(
        prices,
        "_qualify_exact_stale_time_generations_and_global_policy",
        lambda expected: calls.append(f"source-runtimes:{expected}"),
    )
    monkeypatch.setattr(
        prices,
        "_qualify_source_stale_time_policies",
        lambda reg_id, _source: calls.append(f"source-policy:{reg_id}"),
    )
    monkeypatch.setattr(
        prices,
        "_qualify_chainlink_conversion_routes",
        lambda source: calls.append(f"chainlink-graph:{source.label}"),
    )
    monkeypatch.setattr(
        prices,
        "_qualify_redstone_activation",
        lambda source, num_assets, inventory: calls.append(
            f"redstone-graph:{source.label}:{num_assets}:{inventory == ({}, ())}"
        ),
    )
    monkeypatch.setattr(
        prices,
        "_qualify_chainlink_anchor_rotation",
        lambda source, anchor, feed: calls.append(
            f"anchor:{source.label}:{anchor}:{feed}"
        ),
    )
    monkeypatch.setattr(
        prices,
        "_qualify_source_has_no_pending_actions",
        lambda reg_id, _source: calls.append(f"no-pending:{reg_id}"),
    )

    assert prices._run_strict_activation_qualifications(
        "ETH",
        FEED,
        90_000,
    )
    assert calls == [
        "price-desk-registry",
        "price-desk-runtime",
        "source-runtimes:90000",
        "source-policy:1",
        "source-policy:2",
        "source-policy:3",
        "source-policy:4",
        "chainlink-graph:Chainlink",
        "redstone-graph:RedStone:4:True",
        f"anchor:Chainlink:ETH:{FEED}",
        "no-pending:1",
        "no-pending:2",
        "no-pending:3",
        "no-pending:4",
    ]


def _chainlink_anchor_source():
    eth_dependent = ASSET
    other_eth_dependent = "0x" + "4" * 40
    btc_dependent = "0x" + "5" * 40
    configs = {
        ETH: SimpleNamespace(
            feed="0x" + "7" * 40,
            needsEthToUsd=False,
            needsBtcToUsd=False,
        ),
        "0x" + "b" * 40: SimpleNamespace(
            feed="0x" + "8" * 40,
            needsEthToUsd=False,
            needsBtcToUsd=False,
        ),
        eth_dependent: SimpleNamespace(
            feed=FEED,
            needsEthToUsd=True,
            needsBtcToUsd=False,
        ),
        other_eth_dependent: SimpleNamespace(
            feed=OTHER_FEED,
            needsEthToUsd=True,
            needsBtcToUsd=False,
        ),
        btc_dependent: SimpleNamespace(
            feed=FEED,
            needsEthToUsd=False,
            needsBtcToUsd=True,
        ),
    }
    assets = (None, eth_dependent, other_eth_dependent, btc_dependent)
    return SimpleNamespace(
        ETH=lambda: ETH,
        BTC=lambda: "0x" + "b" * 40,
        numAssets=lambda: len(assets),
        assets=lambda index: assets[index],
        feedConfig=lambda asset: configs[asset],
        pendingUpdates=lambda _asset: SimpleNamespace(actionId=0),
        actionId=lambda: 1,
        hasPendingAction=lambda _action_id: False,
    )


def test_chainlink_anchor_rotation_preflight_enumerates_only_impacted_dependents():
    source = _chainlink_anchor_source()

    eth_affected, eth_incomplete = (
        prices._chainlink_anchor_rotation_dependents(source, "ETH", FEED)
    )
    btc_affected, btc_incomplete = (
        prices._chainlink_anchor_rotation_dependents(source, "BTC", FEED)
    )

    assert eth_affected == (
        (
            "active",
            ASSET,
            FEED,
            "primary feed equals proposed anchor feed",
        ),
    )
    assert btc_affected == (
        (
            "active",
            "0x" + "5" * 40,
            FEED,
            "primary feed equals proposed anchor feed",
        ),
    )
    assert eth_incomplete == btc_incomplete == ()


def test_chainlink_anchor_rotation_preflight_checks_pending_candidate_routes():
    active = SimpleNamespace(
        feed=OTHER_FEED,
        needsEthToUsd=True,
        needsBtcToUsd=False,
    )
    pending = SimpleNamespace(
        actionId=9,
        config=SimpleNamespace(
            feed=FEED,
            needsEthToUsd=True,
            needsBtcToUsd=False,
        ),
    )
    source = SimpleNamespace(
        numAssets=lambda: 2,
        assets=lambda _index: ASSET,
        feedConfig=lambda _asset: active,
        pendingUpdates=lambda _asset: pending,
        actionId=lambda: 10,
        hasPendingAction=lambda action_id: action_id == 9,
    )

    affected, incomplete = prices._chainlink_anchor_rotation_dependents(
        source,
        "ETH",
        FEED,
    )

    assert affected == (
        (
            "pending",
            ASSET,
            FEED,
            "primary feed equals proposed anchor feed",
        ),
    )
    assert incomplete == ()


def test_chainlink_anchor_rotation_preflight_treats_zero_anchor_as_all_impacted():
    affected, incomplete = prices._chainlink_anchor_rotation_dependents(
        _chainlink_anchor_source(),
        "ETH",
        prices.ZERO_ADDRESS,
    )

    assert tuple(asset for _state, asset, _feed, _reason in affected) == (
        ASSET,
        "0x" + "4" * 40,
    )
    assert all(
        reason == "zero anchor feed"
        for _state, _asset, _feed, reason in affected
    )
    assert incomplete == ()


def test_chainlink_anchor_rotation_qualification_fails_on_impact_and_passes_safe():
    source = _chainlink_anchor_source()
    with pytest.raises(
        RuntimeError,
        match="^CHAINLINK_ANCHOR_ROTATION_QUALIFICATION_FAILED:affected=",
    ):
        prices._qualify_chainlink_anchor_rotation(source, "ETH", FEED)

    assert prices._qualify_chainlink_anchor_rotation(
        source,
        "ETH",
        "0x" + "6" * 40,
    )


def test_chainlink_anchor_rotation_rejects_zero_with_no_dependents():
    source = SimpleNamespace(
        numAssets=lambda: 1,
        actionId=lambda: 1,
        hasPendingAction=lambda _action_id: False,
    )

    with pytest.raises(RuntimeError, match="zero-feed"):
        prices._qualify_chainlink_anchor_rotation(
            source,
            "ETH",
            prices.ZERO_ADDRESS,
        )


def test_chainlink_anchor_rotation_fails_on_unmatched_pending_new_asset():
    source = _chainlink_anchor_source()
    source.actionId = lambda: 3
    source.hasPendingAction = lambda action_id: action_id == 2

    with pytest.raises(RuntimeError, match=r"unmatchedPendingAction\(2\)"):
        prices._qualify_chainlink_anchor_rotation(
            source,
            "ETH",
            "0x" + "6" * 40,
        )


def test_chainlink_anchor_rotation_qualification_fails_closed_on_rpc_gap():
    source = SimpleNamespace(
        numAssets=lambda: 2,
        assets=lambda _index: ASSET,
        feedConfig=lambda _asset: (_ for _ in ()).throw(RuntimeError("RPC")),
        actionId=lambda: 1,
        hasPendingAction=lambda _action_id: False,
    )
    with pytest.raises(RuntimeError, match="incomplete=feedConfig"):
        prices._qualify_chainlink_anchor_rotation(source, "ETH", OTHER_FEED)


def test_strict_chainlink_route_qualification_accepts_safe_graph():
    assert prices._qualify_chainlink_conversion_routes(
        _chainlink_anchor_source()
    )


@pytest.mark.parametrize(
    ("candidate", "reason"),
    (
        (
            SimpleNamespace(
                feed="0x" + "7" * 40,
                needsEthToUsd=True,
                needsBtcToUsd=False,
            ),
            "primary feed equals active ETH feed",
        ),
        (
            SimpleNamespace(
                feed=OTHER_FEED,
                needsEthToUsd=True,
                needsBtcToUsd=True,
            ),
            "both conversion flags are set",
        ),
    ),
)
def test_strict_chainlink_route_qualification_mirrors_route_invariants(
    candidate,
    reason,
):
    source = _chainlink_anchor_source()
    original_feed_config = source.feedConfig
    source.feedConfig = lambda asset: (
        candidate if str(asset).lower() == ASSET.lower() else original_feed_config(asset)
    )

    with pytest.raises(RuntimeError, match="hazards=") as exc_info:
        prices._qualify_chainlink_conversion_routes(source)
    assert reason in str(exc_info.value)


def test_strict_chainlink_route_qualification_rejects_converting_anchor():
    source = _chainlink_anchor_source()
    original_feed_config = source.feedConfig
    converting_anchor = SimpleNamespace(
        feed="0x" + "7" * 40,
        needsEthToUsd=True,
        needsBtcToUsd=False,
    )
    source.feedConfig = lambda asset: (
        converting_anchor
        if str(asset).lower() == ETH.lower()
        else original_feed_config(asset)
    )

    with pytest.raises(RuntimeError, match="active ETH anchor also converts"):
        prices._qualify_chainlink_conversion_routes(source)


def test_strict_chainlink_route_qualification_checks_pending_route():
    source = _chainlink_anchor_source()
    pending = SimpleNamespace(
        actionId=1,
        config=SimpleNamespace(
            feed="0x" + "7" * 40,
            needsEthToUsd=True,
            needsBtcToUsd=False,
        ),
    )
    source.pendingUpdates = lambda asset: (
        pending
        if str(asset).lower() == ASSET.lower()
        else SimpleNamespace(actionId=0)
    )
    source.actionId = lambda: 2
    source.hasPendingAction = lambda action_id: action_id == 1

    with pytest.raises(RuntimeError, match="hazards=pending:"):
        prices._qualify_chainlink_conversion_routes(source)


def test_strict_chainlink_route_qualification_rejects_unmatched_action():
    source = _chainlink_anchor_source()
    source.actionId = lambda: 3
    source.hasPendingAction = lambda action_id: action_id == 2

    with pytest.raises(RuntimeError, match="unmatched-actions=2"):
        prices._qualify_chainlink_conversion_routes(source)


def test_paused_source_output_warns_that_pricing_continues(monkeypatch, capsys):
    _isolate_operator_output(monkeypatch)
    monkeypatch.setattr(prices, "print_local_gov_params", lambda *_a, **_k: None)
    monkeypatch.setattr(prices, "print_timelock_params", lambda *_a, **_k: None)
    source = SimpleNamespace(
        isPaused=lambda: True,
        numAssets=lambda: 1,
    )
    source_info = {
        "address": CHAINLINK,
        "description": "Chainlink",
        "contract": source,
        "stale_time_generation": prices.STALE_TIME_GENERATION_LEGACY,
        "runtime_hash": "0xlegacy",
    }

    prices.print_price_source_config(1, source_info)

    output = capsys.readouterr().out
    assert "Source Administration Paused" in output
    assert "not a price circuit breaker" in output
    assert "Existing price reads continue" in output
    assert "must unpause" in output


def test_cli_requires_chainlink_anchor_preflight_arguments_together():
    with pytest.raises(SystemExit):
        prices._parse_args(["--chainlink-anchor", "ETH"])
    with pytest.raises(SystemExit):
        prices._parse_args(
            ["--proposed-anchor-feed", "0x" + "1" * 40]
        )
    with pytest.raises(SystemExit):
        prices._parse_args(
            [
                "--chainlink-anchor",
                "ETH",
                "--proposed-anchor-feed",
                prices.ZERO_ADDRESS,
            ]
        )


def test_cli_rejects_silently_ignored_expected_global_policy():
    with pytest.raises(SystemExit):
        prices._parse_args(["--expected-global-stale-time", "300"])

    args = prices._parse_args(
        [
            "--strict-activation",
            "--expected-global-stale-time",
            "300",
        ]
    )
    assert args.expected_global_stale_time == 300
    assert prices._parse_args([]).expected_global_stale_time == 86_400
