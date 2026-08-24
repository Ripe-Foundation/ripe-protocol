import ast
import re
from pathlib import Path

import pytest

from config import robinhood_launch as policy
from config.BluePrint import ROBINHOOD_AAPL_TOKEN_CANDIDATE, ROBINHOOD_ADDRESSES


EXPECTED_INHERIT_ASSETS = frozenset(
    (
        "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",  # native ETH
        "0x0bd7d308f8e1639fab988df18a8011f41eacad73",  # WETH
        "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",  # BTC sentinel
        "0x5fc5360d0400a0fd4f2af552add042d716f1d168",  # USDG
    )
)
EXPECTED_EQUITY_ASSETS = frozenset(
    (
        "0x4a0e65a3eccec6dbe60ae065f2e7bb85fae35eea",  # SPCX
        "0xd0601ce157db5bdc3162bbac2a2c8af5320d9eec",  # NVDA
        "0x322f0929c4625ed5bad873c95208d54e1c003b2d",  # TSLA
        "0xaf3d76f1834a1d425780943c99ea8a608f8a93f9",  # AAPL
        "0x2e0847e8910a9732eb3fb1bb4b70a580adad4fe3",  # GOOGL
        "0x1b0e319c6a659f002271b69db8a7df2f911c153e",  # GME
    )
)
EXPECTED_EQUITY_NAMES = ("SPCX", "NVDA", "TSLA", "AAPL", "GOOGL", "GME")


def test_stale_time_policy_values_and_bounds_are_exact():
    assert policy.STALE_WINDOW_MIN == 300
    assert policy.STALE_WINDOW_MAX == 604_800
    assert policy.STALE_WINDOW_GLOBAL == 86_400
    assert policy.STALE_WINDOW_INHERIT == 0
    assert policy.STALE_WINDOW_EQUITY == 345_600

    assert policy.STALE_WINDOW_INHERIT < policy.STALE_WINDOW_MIN
    assert (
        policy.STALE_WINDOW_MIN
        <= policy.STALE_WINDOW_GLOBAL
        <= policy.STALE_WINDOW_MAX
    )
    assert (
        policy.STALE_WINDOW_MIN
        <= policy.STALE_WINDOW_EQUITY
        <= policy.STALE_WINDOW_MAX
    )

    # Keep historical migration 0003 deterministic while forward migrations
    # consume the classifier rather than either legacy name.
    assert policy.STALE_WINDOW_DEFAULT == 86_400
    assert policy.STALE_WINDOW_USDG == 86_400


def test_every_post_pr206_target_override_is_zero_or_within_source_bounds():
    classified_assets = (
        policy.ROBINHOOD_STALE_TIME_INHERIT_ASSETS
        | policy.ROBINHOOD_STALE_TIME_EQUITY_ASSETS
    )
    for asset in classified_assets:
        override = policy.stale_time_override_for_asset(asset)
        assert override == policy.STALE_WINDOW_INHERIT or (
            policy.STALE_WINDOW_MIN
            <= override
            <= policy.STALE_WINDOW_MAX
        )


def test_post_pr206_policy_has_no_current_migration_consumer():
    migration_dir = (
        Path(__file__).resolve().parents[2]
        / "migrations"
        / "robinhood-mainnet"
    )
    target_names = {
        "stale_time_override_for_asset",
        "ROBINHOOD_STALE_TIME_INHERIT_ASSETS",
        "ROBINHOOD_STALE_TIME_EQUITY_ASSETS",
        "STALE_WINDOW_INHERIT",
        "STALE_WINDOW_EQUITY",
    }
    consumers = []

    def dotted_name(node):
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            prefix = dotted_name(node.value)
            if prefix is not None:
                return f"{prefix}.{node.attr}"
        return None

    for path in sorted(migration_dir.glob("*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        module_aliases = set()
        used_targets = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == "config.robinhood_launch":
                    for imported in node.names:
                        if imported.name == "*":
                            used_targets.update(target_names)
                        elif imported.name in target_names:
                            used_targets.add(imported.name)
                elif node.module == "config":
                    for imported in node.names:
                        if imported.name == "robinhood_launch":
                            module_aliases.add(
                                imported.asname or imported.name
                            )
            elif isinstance(node, ast.Import):
                for imported in node.names:
                    if imported.name == "config.robinhood_launch":
                        module_aliases.add(
                            imported.asname or "config.robinhood_launch"
                        )

        for node in ast.walk(tree):
            qualified = dotted_name(node)
            if qualified is None:
                continue
            for module_alias in module_aliases:
                prefix = f"{module_alias}."
                if qualified.startswith(prefix):
                    candidate = qualified.removeprefix(prefix)
                    if candidate in target_names:
                        used_targets.add(candidate)

        if used_targets:
            consumers.append((path.name, tuple(sorted(used_targets))))

    assert consumers == []


def test_stale_time_policy_asset_sets_are_exact_and_disjoint():
    assert policy.ROBINHOOD_STALE_TIME_INHERIT_ASSETS == EXPECTED_INHERIT_ASSETS
    assert policy.ROBINHOOD_STALE_TIME_EQUITY_ASSETS == EXPECTED_EQUITY_ASSETS
    assert EXPECTED_INHERIT_ASSETS.isdisjoint(EXPECTED_EQUITY_ASSETS)
    assert len(EXPECTED_INHERIT_ASSETS | EXPECTED_EQUITY_ASSETS) == 10


@pytest.mark.parametrize("asset", sorted(EXPECTED_INHERIT_ASSETS))
def test_core_routes_inherit_mission_control_policy(asset):
    assert policy.stale_time_override_for_asset(asset) == 0


@pytest.mark.parametrize("asset", sorted(EXPECTED_EQUITY_ASSETS))
def test_equity_routes_use_exact_four_day_override(asset):
    assert policy.stale_time_override_for_asset(asset) == 345_600


def test_classifier_compares_addresses_case_insensitively():
    assert (
        policy.stale_time_override_for_asset(
            ROBINHOOD_ADDRESSES["NATIVE_ETH_SENTINEL"]
        )
        == policy.STALE_WINDOW_INHERIT
    )
    assert (
        policy.stale_time_override_for_asset(ROBINHOOD_AAPL_TOKEN_CANDIDATE)
        == policy.STALE_WINDOW_EQUITY
    )


@pytest.mark.parametrize(
    "asset",
    (
        policy.ZERO_ADDRESS,
        policy.RIPE_WETH_POOL,
        "0x78f3556b67e17df817d51ef5a990cdaf09e8d3a9",  # ETH/USD feed, not ETH
    ),
)
def test_unknown_well_formed_addresses_are_rejected(asset):
    with pytest.raises(ValueError, match="^RH_ORACLE_STALE_POLICY_UNKNOWN_ASSET:"):
        policy.stale_time_override_for_asset(asset)


@pytest.mark.parametrize(
    "asset",
    (
        "AAPL",
        "0x1234",
        "0x" + "g" * 40,
        "0x" + "1" * 20 + "_" + "1" * 19,
        None,
    ),
)
def test_symbolic_or_malformed_assets_are_rejected(asset):
    with pytest.raises(ValueError, match="^RH_ORACLE_STALE_POLICY_INVALID_ADDRESS:"):
        policy.stale_time_override_for_asset(asset)


def test_policy_addresses_match_independent_source_authorities():
    source_core_assets = frozenset(
        ROBINHOOD_ADDRESSES[key].lower()
        for key in ("NATIVE_ETH_SENTINEL", "WETH", "BTC_SENTINEL", "USDG")
    )
    assert source_core_assets == EXPECTED_INHERIT_ASSETS

    defaults_source = (
        Path(__file__).resolve().parents[2]
        / "contracts"
        / "config"
        / "DefaultsRobinhoodLive.vy"
    ).read_text()
    live_addresses = {
        name: address.lower()
        for name, address in re.findall(
            r"^[ \t]*(WETH|USDG|SPCX|NVDA|TSLA|AAPL|GOOGL|GME)"
            r"[ \t]*:[ \t]*constant[ \t]*\([ \t]*address[ \t]*\)"
            r"[ \t]*=[ \t]*(0x[0-9A-Fa-f]{40})[ \t]*$",
            defaults_source,
            flags=re.MULTILINE,
        )
    }

    assert set(live_addresses) == {
        "WETH",
        "USDG",
        "SPCX",
        "NVDA",
        "TSLA",
        "AAPL",
        "GOOGL",
        "GME",
    }
    assert live_addresses["WETH"] in EXPECTED_INHERIT_ASSETS
    assert live_addresses["USDG"] in EXPECTED_INHERIT_ASSETS
    assert (
        frozenset(live_addresses[name] for name in EXPECTED_EQUITY_NAMES)
        == EXPECTED_EQUITY_ASSETS
    )
    assert live_addresses["AAPL"] == ROBINHOOD_AAPL_TOKEN_CANDIDATE.lower()
