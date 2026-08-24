#!/usr/bin/env python3
"""
Output Price Source Configurations Script for Ripe Protocol

Fetches and displays all price source configurations from PriceDesk
on Base mainnet, formatted as markdown tables.

Includes:
- PriceDesk registry overview
- Per-source global config
- Per-source asset configurations (Chainlink, Pyth, BlueChipYield, UndyVault, Curve)

Usage:
    python scripts/params/prices.py
    python scripts/params/prices.py --strict-activation
    python scripts/params/prices.py --strict-activation \
        --chainlink-anchor ETH --proposed-anchor-feed 0x...
"""

import argparse
import os
import sys
import time

import boa
from eth_hash.auto import keccak

# Import shared utilities
from params_utils import (
    RIPE_HQ,
    RPC_DELAY,
    ZERO_ADDRESS,
    MISSION_CONTROL_ID,
    PRICE_DESK_ID,
    PROTOCOL_NAMES,
    format_address,
    format_percent,
    format_blocks_to_time,
    get_token_name,
    print_table,
    setup_boa_etherscan,
    boa_fork_context,
    print_report_header,
    print_report_footer,
    output_to_file,
    print_local_gov_params,
    print_address_registry_params,
    print_timelock_params,
)

# ============================================================================
# Global state
# ============================================================================


STALE_TIME_GENERATION_LEGACY = "legacy"
STALE_TIME_GENERATION_CURRENT = "current"
STALE_TIME_GENERATION_NEW_COMPATIBLE = "new-compatible"
STALE_TIME_GENERATION_UNKNOWN = "unknown"
MIN_LOCAL_STALE_TIME = 300
MAX_EFFECTIVE_STALE_TIME = 604_800
DEFAULT_EXPECTED_ACTIVATION_GLOBAL_STALE_TIME = 86_400

# Deployment-specific, exact runtime fingerprints collected from the
# repository's current Base manifest addresses. Vyper appends immutables to
# deployed runtime code, so a source-template hash is not a deployed identity.
# Add a current-generation hash only from a reviewed completion manifest.
KNOWN_LEGACY_STALE_TIME_RUNTIME_HASHES = {
    # ChainlinkPrices 0xD11B23b6391e294DF49961E64231bddDE5bB5E89
    "0xb9a7cbdb193aeefb73fff5c17edd408dfe607cdbf1e2ea4aefe13da92682e99a",
    # PythPrices 0x16371fAf6f603f8d8D6cef8C46253c80AdEe8b98
    "0xd9fac1cfeddae2b19e47dbea1b59d0eccd2df32e96f420e801ee4fc4d974e482",
    # RedStone 0x9f20F25f037046721A292B19A486932ef390EAf9
    "0x8b690e5d15f204e5656e084832d8805a5b921913c237cc0132074494dd87c648",
    # StorkPrices 0xceE8Ed804f72b6EcB6B2D679ca17B545bD654bF6
    "0x6ed75e536af6436a82fb3372b22795fb601ac11c3ea2c3f60ee7b78fb0cc7351",
}
KNOWN_CURRENT_STALE_TIME_RUNTIME_HASHES = set()
# PriceDesk also contains immutable constructor values, so its reviewed
# deployed runtime identity must be bound separately from the four sources.
# Populate only from the reviewed deployment completion record.
EXPECTED_CURRENT_PRICE_DESK_RUNTIME_HASH = None


class PriceState:
    """Holds loaded contracts and price source data."""

    def __init__(self):
        self.hq = None
        self.mc = None
        self.pd = None
        self.mission_control_stale_time = None
        self.price_sources = {}  # reg_id -> {addr, description, contract}

    def get_known_addresses(self) -> dict:
        """Return known addresses for name resolution."""
        known = {}
        if self.pd:
            known[str(self.pd.address).lower()] = "PriceDesk"
        for reg_id, source in self.price_sources.items():
            known[source["address"].lower()] = source["description"]
        return known


state = PriceState()


# ============================================================================
# Contract Loading
# ============================================================================


def initialize_prices():
    """Load PriceDesk and all price source contracts."""
    print("Loading price source configurations...", file=sys.stderr)

    # Load HQ and PriceDesk
    state.hq = boa.from_etherscan(RIPE_HQ, name="RipeHQ")
    time.sleep(RPC_DELAY)

    state.mc = None
    state.mission_control_stale_time = None
    try:
        mc_addr = state.hq.getAddr(MISSION_CONTROL_ID)
        if str(mc_addr) != ZERO_ADDRESS:
            state.mc = boa.from_etherscan(mc_addr, name="MissionControl")
            state.mission_control_stale_time = _read_mission_control_stale_time(
                state.mc
            )
            time.sleep(RPC_DELAY)
    except Exception:
        print(
            "  MissionControl stale-time policy unavailable; inherited feed "
            "values will be labeled without an effective value.",
            file=sys.stderr,
        )

    pd_addr = state.hq.getAddr(PRICE_DESK_ID)
    state.pd = boa.from_etherscan(pd_addr, name="PriceDesk")
    time.sleep(RPC_DELAY)

    # Load all price sources
    num_sources = state.pd.numAddrs()
    print(f"  Found {num_sources - 1} registered price sources...", file=sys.stderr)

    for i in range(1, num_sources):
        time.sleep(RPC_DELAY)
        addr_info = state.pd.addrInfo(i)
        addr = str(addr_info.addr)
        if addr == ZERO_ADDRESS:
            continue

        time.sleep(RPC_DELAY)
        source = boa.from_etherscan(addr, name=f"PriceSource_{i}")

        state.price_sources[i] = {
            "address": addr,
            "description": addr_info.description,
            "contract": source,
        }

    # Classify each loaded source once. Runtime reads and cross-source
    # discovery are report-scoped caches used by both active and pending output.
    for source_info in state.price_sources.values():
        generation, runtime_hash = _classify_stale_time_generation(
            source_info["contract"]
        )
        source_info["stale_time_generation"] = generation
        source_info["runtime_hash"] = runtime_hash

    for source_info in state.price_sources.values():
        source = source_info["contract"]
        if _is_redstone_source(source, source_info["description"]):
            source_info["cross_source_inventory"] = (
                _discover_eth_route_primary_feeds(source)
            )

    print("  All price sources loaded.\n", file=sys.stderr)


# ============================================================================
# Output Functions
# ============================================================================


def _read_mission_control_stale_time(mission_control):
    """Read the global price policy across old and current MissionControl ABIs."""
    if mission_control is None:
        return None

    try:
        if hasattr(mission_control, "getPriceStaleTime"):
            return int(mission_control.getPriceStaleTime())
    except Exception:
        pass

    try:
        config = mission_control.genConfig()
        if hasattr(config, "priceStaleTime"):
            return int(config.priceStaleTime)
        return int(config[2])
    except Exception:
        return None


def _runtime_code_hash(source):
    """Return the exact immutable-bound runtime hash, or None if unreadable."""
    try:
        code = boa.env.get_code(source.address)
        if isinstance(code, str):
            code = bytes.fromhex(code.removeprefix("0x"))
        else:
            code = bytes(code)
        if not code:
            return None
        return "0x" + keccak(code).hex()
    except Exception:
        return None


def _classify_stale_time_generation(
    source,
    known_legacy_hashes=None,
    known_current_hashes=None,
):
    """Classify exact known runtimes; never infer legacy from source names."""
    legacy_hashes = (
        KNOWN_LEGACY_STALE_TIME_RUNTIME_HASHES
        if known_legacy_hashes is None
        else known_legacy_hashes
    )
    current_hashes = (
        KNOWN_CURRENT_STALE_TIME_RUNTIME_HASHES
        if known_current_hashes is None
        else known_current_hashes
    )
    runtime_hash = _runtime_code_hash(source)
    if runtime_hash in legacy_hashes:
        return STALE_TIME_GENERATION_LEGACY, runtime_hash
    if runtime_hash in current_hashes:
        return STALE_TIME_GENERATION_CURRENT, runtime_hash
    if hasattr(source, "isValidStaleTimeUpdate"):
        return STALE_TIME_GENERATION_NEW_COMPATIBLE, runtime_hash
    return STALE_TIME_GENERATION_UNKNOWN, runtime_hash


def _stale_time_generation_label(generation, runtime_hash=None):
    if generation == STALE_TIME_GENERATION_LEGACY:
        label = "legacy semantics (recognized exact runtime)"
    elif generation == STALE_TIME_GENERATION_CURRENT:
        label = "current exact-override semantics (recognized exact runtime)"
    elif generation == STALE_TIME_GENERATION_NEW_COMPATIBLE:
        label = "new-compatible ABI, unrecognized codehash"
    else:
        label = "unknown generation; stale-time semantics not asserted"
    if runtime_hash is not None:
        return f"{label}; runtime `{runtime_hash}`"
    return f"{label}; runtime hash unavailable"


def _format_price_feed_stale_time(
    stored_stale_time,
    global_stale_time=None,
    generation=STALE_TIME_GENERATION_UNKNOWN,
):
    """Render stored/global policy under an explicitly classified generation."""
    stored = int(stored_stale_time)
    global_value = (
        None if global_stale_time is None else int(global_stale_time)
    )
    global_label = (
        "unavailable" if global_value is None else f"{global_value}s"
    )
    prefix = f"stored {stored}s; global {global_label}; "

    if generation == STALE_TIME_GENERATION_LEGACY:
        if global_value is None:
            return prefix + "legacy cap/fallback; effective value unavailable"
        if stored != 0 and global_value != 0:
            return (
                prefix
                + f"legacy cap; effective {min(stored, global_value)}s"
            )
        if stored != 0 or global_value != 0:
            return prefix + f"legacy fallback; effective {stored or global_value}s"
        return prefix + "legacy zero/zero; freshness unenforced"

    if generation == STALE_TIME_GENERATION_CURRENT:
        if stored != 0:
            if (
                stored < MIN_LOCAL_STALE_TIME
                or stored > MAX_EFFECTIVE_STALE_TIME
            ):
                return prefix + "local override out of range; invalid/fail-closed"
            return prefix + f"exact local override; effective {stored}s"
        if global_value is None:
            return prefix + "inherit MissionControl; effective value unavailable"
        if global_value == 0 or global_value > MAX_EFFECTIVE_STALE_TIME:
            return prefix + "inherited global out of range; invalid/fail-closed"
        return prefix + f"inherit MissionControl; effective {global_value}s"

    if generation == STALE_TIME_GENERATION_NEW_COMPATIBLE:
        current_meaning = _format_price_feed_stale_time(
            stored,
            global_value,
            STALE_TIME_GENERATION_CURRENT,
        )
        return (
            "new-compatible ABI, unrecognized codehash; expected new meaning: "
            + current_meaning
        )

    return (
        prefix
        + "unknown generation; effective stale-time semantics not asserted"
    )


def _format_route_stale_time(
    stored_stale_time,
    global_stale_time,
    generation,
    needs_eth_to_usd=False,
    needs_btc_to_usd=False,
):
    policy = _format_price_feed_stale_time(
        stored_stale_time,
        global_stale_time,
        generation,
    )
    anchors = []
    if needs_eth_to_usd:
        anchors.append("ETH")
    if needs_btc_to_usd:
        anchors.append("BTC")
    if not anchors:
        return policy
    return (
        f"primary-feed policy: {policy}; final route also depends on the "
        f"{' and '.join(anchors)} anchor's independently resolved policy"
    )


def _matching_cross_source_eth_route_primary_feeds(
    primary_feed,
    needs_eth_to_usd,
    discovered_eth_route_primary_feeds,
):
    """Return source labels only for an exact cross-source feed-address match."""
    if not needs_eth_to_usd:
        return ()
    feed = str(primary_feed).lower()
    if feed == ZERO_ADDRESS:
        return ()
    return tuple(discovered_eth_route_primary_feeds.get(feed, ()))


def _is_redstone_source(source, source_name):
    normalized_name = str(source_name).lower().replace(" ", "")
    return "redstone" in normalized_name or hasattr(source, "getRedStoneData")


def _is_chainlink_source(source, source_name):
    normalized_name = str(source_name).lower().replace(" ", "")
    return "chainlink" in normalized_name or hasattr(source, "getChainlinkData")


def _is_stale_time_feed_source(
    source=None,
    source_name="",
    runtime_hash=None,
):
    if runtime_hash in (
        KNOWN_LEGACY_STALE_TIME_RUNTIME_HASHES
        | KNOWN_CURRENT_STALE_TIME_RUNTIME_HASHES
    ):
        return True
    if source is not None and hasattr(source, "isValidStaleTimeUpdate"):
        return True
    normalized_name = str(source_name).lower().replace(" ", "")
    return any(
        source_type in normalized_name
        for source_type in ("chainlink", "pyth", "redstone", "stork")
    )


def _discover_eth_route_primary_feeds(excluded_source=None):
    """Inventory address-valued ETH-route primary feeds and unreadable surfaces."""
    discovered = {}
    incomplete_reads = set()
    excluded_address = str(getattr(excluded_source, "address", "")).lower()
    price_desk_eth = None
    try:
        if state.pd is not None:
            price_desk_eth = state.pd.ETH()
        else:
            incomplete_reads.add("PriceDesk.ETH (not loaded)")
    except Exception:
        incomplete_reads.add("PriceDesk.ETH")

    for reg_id, source_info in state.price_sources.items():
        source = source_info["contract"]
        source_address = str(getattr(source, "address", "")).lower()
        is_excluded_address = (
            excluded_address
            and source_address
            and source_address == excluded_address
        )
        if (
            source is excluded_source
            or is_excluded_address
            or not hasattr(source, "feedConfig")
        ):
            continue

        eth_assets = []
        if price_desk_eth is not None:
            eth_assets.append(price_desk_eth)
        try:
            if hasattr(source, "ETH"):
                eth_assets.append(source.ETH())
        except Exception:
            label = f"{source_info['description']} (registry {reg_id}).ETH"
            incomplete_reads.add(label)

        checked_assets = set()
        for eth_asset in eth_assets:
            normalized_asset = str(eth_asset).lower()
            if normalized_asset in checked_assets:
                continue
            checked_assets.add(normalized_asset)
            configs = []
            try:
                configs.append(("active", source.feedConfig(eth_asset)))
            except Exception:
                label = (
                    f"{source_info['description']} "
                    f"(registry {reg_id}).feedConfig"
                )
                incomplete_reads.add(label)

            if hasattr(source, "pendingUpdates"):
                try:
                    pending = source.pendingUpdates(eth_asset)
                    if getattr(pending, "actionId", 0) != 0:
                        if not hasattr(pending, "config"):
                            incomplete_reads.add(
                                f"{source_info['description']} "
                                f"(registry {reg_id}).pendingUpdates.config"
                            )
                        else:
                            configs.append(("pending", pending.config))
                except Exception:
                    incomplete_reads.add(
                        f"{source_info['description']} "
                        f"(registry {reg_id}).pendingUpdates"
                    )

            for config_state, config in configs:
                # Feed-id sources cannot match RedStone's address-valued feed.
                if not hasattr(config, "feed"):
                    continue
                feed = str(config.feed).lower()
                if feed == ZERO_ADDRESS:
                    continue
                label = f"{source_info['description']} (registry {reg_id})"
                if config_state == "pending":
                    label += ", pending"
                route_dependencies = []
                if getattr(config, "needsEthToUsd", False):
                    route_dependencies.append("ETH")
                if getattr(config, "needsBtcToUsd", False):
                    route_dependencies.append("BTC")
                if route_dependencies:
                    label += ", converts via " + "/".join(route_dependencies)
                discovered.setdefault(feed, set()).add(label)

    return (
        {
            feed: tuple(sorted(labels))
            for feed, labels in discovered.items()
        },
        tuple(sorted(incomplete_reads)),
    )


def _print_incomplete_cross_source_discovery(incomplete_reads):
    if not incomplete_reads:
        return
    reads = ", ".join(f"`{read}`" for read in incomplete_reads)
    print("\n#### ⚠️ RedStone Cross-Source Diagnostic Incomplete")
    print(
        f"- Could not read {reads}. This is nonfatal, but absence of a "
        "self-conversion warning is not conclusive; retry the report before "
        "confirmation or activation."
    )


def _unmatched_live_action_ids(source, matched_action_ids):
    """Find live timelock actions not attributable to enumerated assets."""
    incomplete_reads = set()
    try:
        next_action_id = int(source.actionId())
    except Exception:
        return (), ("actionId",)
    if next_action_id < 1:
        return (), ("actionId(invalid)",)

    live_action_ids = []
    for action_id in range(1, next_action_id):
        try:
            if source.hasPendingAction(action_id):
                live_action_ids.append(action_id)
        except Exception:
            incomplete_reads.add(f"hasPendingAction({action_id})")

    matched = {int(action_id) for action_id in matched_action_ids}
    live = set(live_action_ids)
    incomplete_reads.update(
        f"inactiveMappedAction({action_id})"
        for action_id in matched
        if action_id not in live
    )
    return (
        tuple(action_id for action_id in live_action_ids if action_id not in matched),
        tuple(sorted(incomplete_reads)),
    )


def _redstone_cross_source_collisions(
    source,
    num_assets,
    discovered_eth_route_primary_feeds,
):
    """Inspect active and pending RedStone routes without another inventory."""
    collisions = []
    local_hazards = set()
    incomplete_reads = set()
    matched_action_ids = set()

    eth_asset = None
    eth_configs = []
    try:
        eth_asset = source.ETH()
    except Exception:
        incomplete_reads.add("ETH")
    if eth_asset is not None:
        try:
            eth_configs.append(("active", source.feedConfig(eth_asset)))
        except Exception:
            incomplete_reads.add(f"feedConfig({eth_asset})")
        try:
            pending_eth = source.pendingUpdates(eth_asset)
            pending_eth_action_id = int(getattr(pending_eth, "actionId", 0))
            if pending_eth_action_id != 0:
                matched_action_ids.add(pending_eth_action_id)
                if not hasattr(pending_eth, "config"):
                    incomplete_reads.add(f"pendingUpdates({eth_asset}).config")
                else:
                    eth_configs.append(("pending", pending_eth.config))
        except Exception:
            incomplete_reads.add(f"pendingUpdates({eth_asset})")

    for index in range(1, int(num_assets)):
        try:
            asset = source.assets(index)
        except Exception:
            incomplete_reads.add(f"assets({index})")
            continue
        try:
            config = source.feedConfig(asset)
        except Exception:
            incomplete_reads.add(f"feedConfig({asset})")
            continue
        configs = (("active", config),)
        if hasattr(source, "pendingUpdates"):
            try:
                pending = source.pendingUpdates(asset)
            except Exception:
                incomplete_reads.add(f"pendingUpdates({asset})")
                pending = None
            pending_action_id = int(getattr(pending, "actionId", 0))
            if pending_action_id != 0:
                matched_action_ids.add(pending_action_id)
                if not hasattr(pending, "config"):
                    incomplete_reads.add(f"pendingUpdates({asset}).config")
                else:
                    configs += (("pending", pending.config),)

        for config_state, candidate in configs:
            if not hasattr(candidate, "feed"):
                continue
            matching_sources = _matching_cross_source_eth_route_primary_feeds(
                candidate.feed,
                getattr(candidate, "needsEthToUsd", False),
                discovered_eth_route_primary_feeds,
            )
            if matching_sources:
                collisions.append(
                    (
                        config_state,
                        str(asset),
                        str(candidate.feed),
                        tuple(matching_sources),
                    )
                )

            if not getattr(candidate, "needsEthToUsd", False):
                continue
            candidate_feed = str(candidate.feed).lower()
            if eth_asset is not None and str(asset).lower() == str(eth_asset).lower():
                local_hazards.add(
                    (config_state, str(asset), str(candidate.feed), "asset is ETH")
                )
            for eth_state, eth_config in eth_configs:
                if getattr(eth_config, "needsEthToUsd", False):
                    local_hazards.add(
                        (
                            config_state,
                            str(asset),
                            str(candidate.feed),
                            f"{eth_state} ETH config also needs ETH conversion",
                        )
                    )
                if (
                    candidate_feed != ZERO_ADDRESS
                    and candidate_feed == str(getattr(eth_config, "feed", "")).lower()
                ):
                    local_hazards.add(
                        (
                            config_state,
                            str(asset),
                            str(candidate.feed),
                            f"primary feed equals {eth_state} ETH feed",
                        )
                    )

    unmatched_actions, action_incomplete = _unmatched_live_action_ids(
        source,
        matched_action_ids,
    )
    incomplete_reads.update(action_incomplete)
    return (
        tuple(collisions),
        tuple(sorted(local_hazards)),
        unmatched_actions,
        tuple(sorted(incomplete_reads)),
    )


def _qualify_redstone_activation(
    source,
    num_assets,
    cross_source_inventory=None,
):
    """Fail closed on RedStone collisions or incomplete RPC discovery."""
    if cross_source_inventory is None:
        cross_source_inventory = _discover_eth_route_primary_feeds(source)
    discovered, discovery_incomplete = cross_source_inventory
    (
        collisions,
        local_hazards,
        unmatched_actions,
        config_incomplete,
    ) = _redstone_cross_source_collisions(
        source,
        num_assets,
        discovered,
    )
    incomplete = tuple(sorted(set(discovery_incomplete + config_incomplete)))
    if collisions or local_hazards or unmatched_actions or incomplete:
        details = []
        if collisions:
            details.append(
                "collisions="
                + ";".join(
                    f"{config_state}:{asset}:{feed}:{','.join(labels)}"
                    for config_state, asset, feed, labels in collisions
                )
            )
        if local_hazards:
            details.append(
                "local-hazards="
                + ";".join(
                    f"{config_state}:{asset}:{feed}:{reason}"
                    for config_state, asset, feed, reason in local_hazards
                )
            )
        if unmatched_actions:
            details.append(
                "unmatched-actions="
                + ",".join(str(action_id) for action_id in unmatched_actions)
            )
        if incomplete:
            details.append("incomplete=" + ",".join(incomplete))
        raise RuntimeError(
            "REDSTONE_ACTIVATION_QUALIFICATION_FAILED:" + "|".join(details)
        )
    return True


def _chainlink_anchor_rotation_dependents(
    source,
    anchor,
    proposed_feed,
    proposed_needs_eth_to_usd=False,
    proposed_needs_btc_to_usd=False,
):
    """Enumerate configured routes a proposed ETH/BTC anchor would invalidate."""
    anchor_name = str(anchor).upper()
    if anchor_name not in ("ETH", "BTC"):
        raise ValueError(f"CHAINLINK_ANCHOR_INVALID:{anchor}")
    proposed_feed_normalized = str(proposed_feed).lower()
    required_flag = (
        "needsEthToUsd" if anchor_name == "ETH" else "needsBtcToUsd"
    )
    affected = []
    incomplete_reads = set()
    matched_action_ids = set()
    try:
        num_assets = int(source.numAssets())
    except Exception:
        return (), ("numAssets",)

    for index in range(1, num_assets):
        try:
            asset = source.assets(index)
        except Exception:
            incomplete_reads.add(f"assets({index})")
            continue
        try:
            config = source.feedConfig(asset)
        except Exception:
            incomplete_reads.add(f"feedConfig({asset})")
            continue
        configs = (("active", config),)
        if hasattr(source, "pendingUpdates"):
            try:
                pending = source.pendingUpdates(asset)
            except Exception:
                incomplete_reads.add(f"pendingUpdates({asset})")
                pending = None
            pending_action_id = int(getattr(pending, "actionId", 0))
            if pending_action_id != 0:
                matched_action_ids.add(pending_action_id)
                if not hasattr(pending, "config"):
                    incomplete_reads.add(f"pendingUpdates({asset}).config")
                else:
                    configs += (("pending", pending.config),)

        for config_state, candidate in configs:
            if not getattr(candidate, required_flag, False):
                continue

            reason = None
            if proposed_feed_normalized == ZERO_ADDRESS:
                reason = "zero anchor feed"
            elif proposed_needs_eth_to_usd or proposed_needs_btc_to_usd:
                reason = "anchor is not a direct USD route"
            elif str(candidate.feed).lower() == proposed_feed_normalized:
                reason = "primary feed equals proposed anchor feed"
            if reason is not None:
                affected.append(
                    (
                        config_state,
                        str(asset),
                        str(candidate.feed),
                        reason,
                    )
                )

    unmatched_actions, action_incomplete = _unmatched_live_action_ids(
        source,
        matched_action_ids,
    )
    incomplete_reads.update(action_incomplete)
    incomplete_reads.update(
        f"unmatchedPendingAction({action_id})"
        for action_id in unmatched_actions
    )
    return tuple(affected), tuple(sorted(incomplete_reads))


def _qualify_chainlink_anchor_rotation(source, anchor, proposed_feed):
    """Fail closed when an anchor rotation breaks a dependent or is unreadable."""
    if str(proposed_feed).lower() == ZERO_ADDRESS:
        raise RuntimeError(
            "CHAINLINK_ANCHOR_ROTATION_QUALIFICATION_FAILED:zero-feed"
        )
    affected, incomplete = _chainlink_anchor_rotation_dependents(
        source,
        anchor,
        proposed_feed,
    )
    if affected or incomplete:
        details = []
        if affected:
            details.append(
                "affected="
                + ";".join(
                    f"{config_state}:{asset}:{feed}:{reason}"
                    for config_state, asset, feed, reason in affected
                )
            )
        if incomplete:
            details.append("incomplete=" + ",".join(incomplete))
        raise RuntimeError(
            "CHAINLINK_ANCHOR_ROTATION_QUALIFICATION_FAILED:"
            + "|".join(details)
        )
    return True


def _active_and_pending_feed_configs(
    source,
    asset,
    matched_action_ids,
    incomplete_reads,
):
    configs = []
    try:
        configs.append(("active", source.feedConfig(asset)))
    except Exception:
        incomplete_reads.add(f"feedConfig({asset})")

    if not hasattr(source, "pendingUpdates"):
        incomplete_reads.add("pendingUpdates(unavailable)")
        return tuple(configs)
    try:
        pending = source.pendingUpdates(asset)
    except Exception:
        incomplete_reads.add(f"pendingUpdates({asset})")
        return tuple(configs)
    pending_action_id = int(getattr(pending, "actionId", 0))
    if pending_action_id == 0:
        return tuple(configs)
    matched_action_ids.add(pending_action_id)
    if not hasattr(pending, "config"):
        incomplete_reads.add(f"pendingUpdates({asset}).config")
        return tuple(configs)
    configs.append(("pending", pending.config))
    return tuple(configs)


def _chainlink_conversion_route_hazards(source):
    """Mirror current Chainlink route invariants across active/pending state."""
    hazards = set()
    incomplete_reads = set()
    matched_action_ids = set()
    try:
        num_assets = int(source.numAssets())
    except Exception:
        return (), (), ("numAssets",)

    anchor_assets = {}
    for anchor_name in ("ETH", "BTC"):
        try:
            anchor_assets[anchor_name] = getattr(source, anchor_name)()
        except Exception:
            incomplete_reads.add(anchor_name)

    anchor_configs = {
        anchor_name: _active_and_pending_feed_configs(
            source,
            anchor_asset,
            matched_action_ids,
            incomplete_reads,
        )
        for anchor_name, anchor_asset in anchor_assets.items()
    }

    for index in range(1, num_assets):
        try:
            asset = source.assets(index)
        except Exception:
            incomplete_reads.add(f"assets({index})")
            continue
        configs = _active_and_pending_feed_configs(
            source,
            asset,
            matched_action_ids,
            incomplete_reads,
        )
        for config_state, candidate in configs:
            needs_eth = getattr(candidate, "needsEthToUsd", False)
            needs_btc = getattr(candidate, "needsBtcToUsd", False)
            if not needs_eth and not needs_btc:
                continue
            candidate_feed = str(getattr(candidate, "feed", ZERO_ADDRESS))
            if needs_eth and needs_btc:
                hazards.add(
                    (
                        config_state,
                        str(asset),
                        candidate_feed,
                        "both conversion flags are set",
                    )
                )
                continue

            anchor_name = "ETH" if needs_eth else "BTC"
            if anchor_name not in anchor_assets:
                continue
            anchor_asset = anchor_assets[anchor_name]
            if str(asset).lower() == str(anchor_asset).lower():
                hazards.add(
                    (
                        config_state,
                        str(asset),
                        candidate_feed,
                        f"asset is {anchor_name}",
                    )
                )
            for anchor_state, anchor_config in anchor_configs[anchor_name]:
                anchor_feed = str(
                    getattr(anchor_config, "feed", ZERO_ADDRESS)
                ).lower()
                if anchor_feed == ZERO_ADDRESS:
                    hazards.add(
                        (
                            config_state,
                            str(asset),
                            candidate_feed,
                            f"{anchor_state} {anchor_name} anchor feed is zero",
                        )
                    )
                if getattr(anchor_config, "needsEthToUsd", False) or getattr(
                    anchor_config,
                    "needsBtcToUsd",
                    False,
                ):
                    hazards.add(
                        (
                            config_state,
                            str(asset),
                            candidate_feed,
                            f"{anchor_state} {anchor_name} anchor also converts",
                        )
                    )
                if candidate_feed.lower() == anchor_feed:
                    hazards.add(
                        (
                            config_state,
                            str(asset),
                            candidate_feed,
                            f"primary feed equals {anchor_state} {anchor_name} feed",
                        )
                    )

    unmatched_actions, action_incomplete = _unmatched_live_action_ids(
        source,
        matched_action_ids,
    )
    incomplete_reads.update(action_incomplete)
    return (
        tuple(sorted(hazards)),
        unmatched_actions,
        tuple(sorted(incomplete_reads)),
    )


def _qualify_chainlink_conversion_routes(source):
    hazards, unmatched_actions, incomplete = (
        _chainlink_conversion_route_hazards(source)
    )
    if hazards or unmatched_actions or incomplete:
        details = []
        if hazards:
            details.append(
                "hazards="
                + ";".join(
                    f"{config_state}:{asset}:{feed}:{reason}"
                    for config_state, asset, feed, reason in hazards
                )
            )
        if unmatched_actions:
            details.append(
                "unmatched-actions="
                + ",".join(str(action_id) for action_id in unmatched_actions)
            )
        if incomplete:
            details.append("incomplete=" + ",".join(incomplete))
        raise RuntimeError(
            "CHAINLINK_ROUTE_QUALIFICATION_FAILED:" + "|".join(details)
        )
    return True


def _find_loaded_price_source(source_type):
    matches = [
        source_info
        for source_info in state.price_sources.values()
        if (
            _is_chainlink_source(
                source_info["contract"],
                source_info["description"],
            )
            if source_type.lower() == "chainlink"
            else source_type.lower()
            in str(source_info["description"]).lower().replace(" ", "")
        )
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"PRICE_SOURCE_DISCOVERY_FAILED:{source_type}:found={len(matches)}"
        )
    return matches[0]


def _qualify_price_desk_registry_stability():
    """Fail on enumerable pending changes to any existing PriceDesk reg ID."""
    pending_changes = []
    incomplete_reads = set()
    try:
        num_addrs = int(state.pd.numAddrs())
    except Exception:
        raise RuntimeError(
            "PRICE_DESK_REGISTRY_QUALIFICATION_FAILED:incomplete=numAddrs"
        ) from None

    for reg_id in range(1, num_addrs):
        try:
            pending_update = state.pd.pendingAddrUpdate(reg_id)
            if int(getattr(pending_update, "confirmBlock", 0)) != 0:
                pending_changes.append(
                    f"update:{reg_id}:{getattr(pending_update, 'newAddr', 'unknown')}"
                )
        except Exception:
            incomplete_reads.add(f"pendingAddrUpdate({reg_id})")
        try:
            pending_disable = state.pd.pendingAddrDisable(reg_id)
            if int(getattr(pending_disable, "confirmBlock", 0)) != 0:
                pending_changes.append(f"disable:{reg_id}")
        except Exception:
            incomplete_reads.add(f"pendingAddrDisable({reg_id})")

    if pending_changes or incomplete_reads:
        details = []
        if pending_changes:
            details.append("pending=" + ",".join(pending_changes))
        if incomplete_reads:
            details.append("incomplete=" + ",".join(sorted(incomplete_reads)))
        raise RuntimeError(
            "PRICE_DESK_REGISTRY_QUALIFICATION_FAILED:" + "|".join(details)
        )
    return True


def _source_stale_time_policy_issues(source):
    """Census active/pending local policy and all live source timelock actions."""
    invalid_policies = []
    incomplete_reads = set()
    matched_action_ids = set()
    try:
        num_assets = int(source.numAssets())
    except Exception:
        return (), (), ("numAssets",)

    for index in range(1, num_assets):
        try:
            asset = source.assets(index)
        except Exception:
            incomplete_reads.add(f"assets({index})")
            continue
        configs = _active_and_pending_feed_configs(
            source,
            asset,
            matched_action_ids,
            incomplete_reads,
        )
        for config_state, config in configs:
            if not hasattr(config, "staleTime"):
                incomplete_reads.add(f"{config_state}.staleTime({asset})")
                continue
            stale_time = int(config.staleTime)
            if stale_time != 0 and (
                stale_time < MIN_LOCAL_STALE_TIME
                or stale_time > MAX_EFFECTIVE_STALE_TIME
            ):
                invalid_policies.append(
                    (config_state, str(asset), stale_time)
                )

    unmatched_actions, action_incomplete = _unmatched_live_action_ids(
        source,
        matched_action_ids,
    )
    incomplete_reads.update(action_incomplete)
    return (
        tuple(invalid_policies),
        unmatched_actions,
        tuple(sorted(incomplete_reads)),
    )


def _qualify_source_stale_time_policies(reg_id, source):
    invalid_policies, unmatched_actions, incomplete = (
        _source_stale_time_policy_issues(source)
    )
    if invalid_policies or unmatched_actions or incomplete:
        details = []
        if invalid_policies:
            details.append(
                "invalid="
                + ";".join(
                    f"{config_state}:{asset}:{stale_time}"
                    for config_state, asset, stale_time in invalid_policies
                )
            )
        if unmatched_actions:
            details.append(
                "unmatched-actions="
                + ",".join(str(action_id) for action_id in unmatched_actions)
            )
        if incomplete:
            details.append("incomplete=" + ",".join(incomplete))
        raise RuntimeError(
            f"PRICE_SOURCE_STALE_POLICY_QUALIFICATION_FAILED:registry-{reg_id}:"
            + "|".join(details)
        )
    return True


def _qualify_source_has_no_pending_actions(reg_id, source):
    live_actions, incomplete = _unmatched_live_action_ids(source, ())
    if live_actions or incomplete:
        details = []
        if live_actions:
            details.append(
                "live=" + ",".join(str(action_id) for action_id in live_actions)
            )
        if incomplete:
            details.append("incomplete=" + ",".join(incomplete))
        raise RuntimeError(
            f"PRICE_SOURCE_PENDING_ACTION_QUALIFICATION_FAILED:registry-{reg_id}:"
            + "|".join(details)
        )
    return True


def _qualify_exact_price_desk_runtime():
    expected_hash = EXPECTED_CURRENT_PRICE_DESK_RUNTIME_HASH
    if not expected_hash:
        raise RuntimeError(
            "PRICE_DESK_RUNTIME_QUALIFICATION_FAILED:expected-runtime=empty"
        )

    observed_hash = (
        _runtime_code_hash(state.pd) if state.pd is not None else None
    )
    if observed_hash != expected_hash:
        raise RuntimeError(
            "PRICE_DESK_RUNTIME_QUALIFICATION_FAILED:"
            f"observed={observed_hash or 'unavailable'}:expected={expected_hash}"
        )
    return True


def _qualify_exact_stale_time_generations_and_global_policy(
    expected_global_stale_time=DEFAULT_EXPECTED_ACTIVATION_GLOBAL_STALE_TIME,
):
    failures = []
    expected_current_hashes = set(KNOWN_CURRENT_STALE_TIME_RUNTIME_HASHES)
    observed_current_hashes = []
    if not expected_current_hashes:
        failures.append("expected-current-runtime-inventory=empty")
    global_stale_time = state.mission_control_stale_time
    expected_global = int(expected_global_stale_time)
    if expected_global <= 0 or expected_global > MAX_EFFECTIVE_STALE_TIME:
        failures.append(f"expected-global={expected_global}")
    if (
        global_stale_time is None
        or int(global_stale_time) <= 0
        or int(global_stale_time) > MAX_EFFECTIVE_STALE_TIME
        or int(global_stale_time) != expected_global
    ):
        failures.append(
            f"global={global_stale_time}:expected={expected_global}"
        )

    for reg_id, source_info in sorted(state.price_sources.items()):
        if not _is_stale_time_feed_source(
            source_info.get("contract"),
            source_info["description"],
            source_info.get("runtime_hash"),
        ):
            continue
        generation = source_info.get(
            "stale_time_generation",
            STALE_TIME_GENERATION_UNKNOWN,
        )
        runtime_hash = source_info.get("runtime_hash")
        if generation == STALE_TIME_GENERATION_CURRENT and runtime_hash is not None:
            observed_current_hashes.append(runtime_hash)
        if (
            generation != STALE_TIME_GENERATION_CURRENT
            or runtime_hash not in expected_current_hashes
        ):
            failures.append(
                f"registry-{reg_id}={generation}:{runtime_hash or 'unavailable'}"
            )
    observed_current_set = set(observed_current_hashes)
    missing_hashes = sorted(expected_current_hashes - observed_current_set)
    extra_hashes = sorted(observed_current_set - expected_current_hashes)
    duplicate_hashes = sorted(
        runtime_hash
        for runtime_hash in observed_current_set
        if observed_current_hashes.count(runtime_hash) != 1
    )
    if missing_hashes:
        failures.append("missing-current=" + ",".join(missing_hashes))
    if extra_hashes:
        failures.append("extra-current=" + ",".join(extra_hashes))
    if duplicate_hashes:
        failures.append("duplicate-current=" + ",".join(duplicate_hashes))
    if failures:
        raise RuntimeError(
            "PRICE_SOURCE_GENERATION_QUALIFICATION_FAILED:"
            + "|".join(failures)
        )
    return True


def _run_strict_activation_qualifications(
    chainlink_anchor=None,
    proposed_anchor_feed=None,
    expected_global_stale_time=DEFAULT_EXPECTED_ACTIVATION_GLOBAL_STALE_TIME,
):
    _qualify_price_desk_registry_stability()
    _qualify_exact_price_desk_runtime()
    _qualify_exact_stale_time_generations_and_global_policy(
        expected_global_stale_time
    )
    for reg_id, source_info in sorted(state.price_sources.items()):
        if _is_stale_time_feed_source(
            source_info.get("contract"),
            source_info["description"],
            source_info.get("runtime_hash"),
        ):
            _qualify_source_stale_time_policies(
                reg_id,
                source_info["contract"],
            )
    chainlink_sources = [
        source_info
        for source_info in state.price_sources.values()
        if _is_chainlink_source(
            source_info["contract"],
            source_info["description"],
        )
    ]
    for source_info in chainlink_sources:
        _qualify_chainlink_conversion_routes(source_info["contract"])
    redstone_sources = [
        source_info
        for source_info in state.price_sources.values()
        if _is_redstone_source(
            source_info["contract"],
            source_info["description"],
        )
    ]
    for source_info in redstone_sources:
        source = source_info["contract"]
        _qualify_redstone_activation(
            source,
            source.numAssets(),
            source_info.get("cross_source_inventory"),
        )

    if chainlink_anchor is not None:
        chainlink_info = _find_loaded_price_source("chainlink")
        _qualify_chainlink_anchor_rotation(
            chainlink_info["contract"],
            chainlink_anchor,
            proposed_anchor_feed,
        )
    for reg_id, source_info in sorted(state.price_sources.items()):
        if _is_stale_time_feed_source(
            source_info.get("contract"),
            source_info["description"],
            source_info.get("runtime_hash"),
        ):
            _qualify_source_has_no_pending_actions(
                reg_id,
                source_info["contract"],
            )
    return True


def print_table_of_contents():
    """Print a clickable table of contents."""
    print("""
## Table of Contents

1. [PriceDesk Overview](#price-desk-overview)
2. [Price Source Configurations](#price-source-configs)
""")

    # Add links for each price source
    for reg_id, source in sorted(state.price_sources.items()):
        anchor = source["description"].lower().replace(" ", "-")
        print(f"   - [{source['description']}](#{anchor})")


def print_price_desk_overview():
    """Print PriceDesk registry overview."""
    print("\n<a id=\"price-desk-overview\"></a>")
    print("## PriceDesk Overview")
    print(f"\nAddress: `{state.pd.address}`\n")

    # Constants
    eth_addr = str(state.pd.ETH())
    rows = [
        ("ETH", format_address(eth_addr)),
    ]
    print_table("Constants", ["Parameter", "Value"], rows, level=3)

    # AddressRegistry Module params
    print_address_registry_params(state.pd, registry_name="price sources", level=3)

    # LocalGov Module params
    print_local_gov_params(state.pd, state.get_known_addresses, level=3)

    # Registered sources summary
    print("\n### Registered Price Sources")
    print("\n| Reg ID | Description | Address |")
    print("| --- | --- | --- |")
    for reg_id, source in sorted(state.price_sources.items()):
        print(f"| {reg_id} | {source['description']} | `{source['address']}` |")


def print_price_source_config(reg_id: int, source_info: dict):
    """Print detailed configuration for a single price source."""
    source = source_info["contract"]
    source_name = source_info["description"]
    stale_time_generation = source_info.get(
        "stale_time_generation",
        STALE_TIME_GENERATION_UNKNOWN,
    )
    runtime_hash = source_info.get("runtime_hash")
    cross_source_inventory = source_info.get("cross_source_inventory")
    anchor = source_name.lower().replace(" ", "-")

    print(f"\n<a id=\"{anchor}\"></a>")
    print(f"### {source_name}")
    print(f"Address: `{source_info['address']}`")

    # Global config - these methods are optional depending on price source type
    rows = []
    if hasattr(source, 'isPaused'):
        rows.append(("isPaused", source.isPaused()))

    if _is_stale_time_feed_source(source, source_name, runtime_hash):
        rows.append(
            (
                "staleTimeSemantics",
                _stale_time_generation_label(
                    stale_time_generation,
                    runtime_hash,
                ),
            )
        )
        rows.append(
            (
                "MissionControl global stale time",
                (
                    "unavailable"
                    if state.mission_control_stale_time is None
                    else f"{state.mission_control_stale_time}s"
                ),
            )
        )

    if hasattr(source, 'maxConfidenceRatio'):
        rows.append(("maxConfidenceRatio", format_percent(source.maxConfidenceRatio())))

    num_assets = 0
    if hasattr(source, 'numAssets'):
        num_assets = source.numAssets()
        rows.append(("numAssets", num_assets - 1 if num_assets > 0 else 0))

    if rows:
        print_table("Global Config", ["Parameter", "Value"], rows, level=4)

    if hasattr(source, 'isPaused') and source.isPaused():
        print("\n#### ⚠️ Source Administration Paused")
        print(
            "- Pause freezes administrative mutation; it is not a price "
            "circuit breaker. Existing price reads continue, and governance "
            "must unpause the source before feed remediation."
        )

    # LocalGov Module params
    print_local_gov_params(source, state.get_known_addresses, level=4)

    # TimeLock Module params
    print_timelock_params(source, level=4)

    # Per-asset configurations
    if num_assets > 1:
        _print_price_source_assets(
            source,
            source_name,
            num_assets,
            stale_time_generation,
            cross_source_inventory,
        )

    # GREEN Reference Pool config (Curve Prices only)
    if hasattr(source, 'greenRefPoolConfig'):
        _print_green_ref_pool_config(source)

    # Pending price feed changes
    if num_assets > 1:
        _print_pending_price_changes(
            source,
            source_name,
            num_assets,
            stale_time_generation,
            cross_source_inventory,
        )


def _print_green_ref_pool_config(source):
    """Print GREEN Reference Pool configuration for Curve Prices."""
    try:
        config = source.greenRefPoolConfig()
        data = source.greenRefPoolData()
    except Exception:
        return  # No GREEN ref pool configured

    # Check if pool is configured (non-zero address)
    if str(config.pool) == ZERO_ADDRESS:
        return

    print("\n#### GREEN Reference Pool Configuration")

    # Get alt asset name
    alt_asset_name = get_token_name(str(config.altAsset))

    print(f"\n**Pool Config**")
    print(f"- Pool: `{config.pool}`")
    print(f"- LP Token: `{config.lpToken}`")
    print(f"- GREEN Index: {config.greenIndex}")
    print(f"- Alt Asset: {alt_asset_name} (`{config.altAsset}`)")
    print(f"- Alt Asset Decimals: {config.altAssetDecimals}")
    print(f"- Max Num Snapshots: {config.maxNumSnapshots}")
    print(f"- Danger Trigger: {format_percent(config.dangerTrigger)}")
    print(f"- Stale Blocks: {format_blocks_to_time(config.staleBlocks)}")
    print(f"- Stabilizer Adjust Weight: {config.stabilizerAdjustWeight}")
    print(f"- Stabilizer Max Pool Debt: {config.stabilizerMaxPoolDebt / (10**18):,.2f} GREEN")

    # Current status from data
    print(f"\n**Current Status**")
    print(f"- Num Blocks In Danger: {data.numBlocksInDanger}")
    print(f"- Next Index: {data.nextIndex}")

    # Last snapshot
    if data.lastSnapshot.update > 0:
        now = int(time.time())
        seconds_ago = now - data.lastSnapshot.update
        if seconds_ago < 60:
            time_ago = f"~{seconds_ago:.0f}s ago"
        elif seconds_ago < 3600:
            time_ago = f"~{seconds_ago/60:.1f}m ago"
        elif seconds_ago < 86400:
            time_ago = f"~{seconds_ago/3600:.1f}h ago"
        else:
            time_ago = f"~{seconds_ago/86400:.1f}d ago"

        print(f"- Last Snapshot:")
        print(f"  - GREEN Balance: {data.lastSnapshot.greenBalance / (10**18):,.2f} GREEN")
        print(f"  - Ratio: {data.lastSnapshot.ratio / (10**18):.6f}")
        print(f"  - In Danger: {data.lastSnapshot.inDanger}")
        print(f"  - Update: {data.lastSnapshot.update} ({time_ago})")


def _print_pending_price_changes(
    source,
    source_name: str,
    num_assets: int,
    stale_time_generation=STALE_TIME_GENERATION_UNKNOWN,
    cross_source_inventory=None,
):
    """Print pending price feed updates for a price source."""
    # Check if source has pending update checking method
    if not hasattr(source, 'hasPendingPriceFeedUpdate'):
        return

    pending_assets = []

    # Check each registered asset for pending updates
    for j in range(1, num_assets):
        time.sleep(RPC_DELAY)
        asset_addr = str(source.assets(j))
        if asset_addr == ZERO_ADDRESS:
            continue

        try:
            time.sleep(RPC_DELAY)
            has_pending = source.hasPendingPriceFeedUpdate(asset_addr)
            if has_pending:
                asset_name = get_token_name(asset_addr)
                pending_assets.append({
                    "asset": asset_name,
                    "asset_addr": asset_addr,
                })
        except Exception:
            continue

    if not pending_assets:
        return

    cross_source_eth_route_primary_feeds = {}
    incomplete_cross_source_reads = ()
    if cross_source_inventory is not None:
        (
            cross_source_eth_route_primary_feeds,
            incomplete_cross_source_reads,
        ) = cross_source_inventory
    elif _is_redstone_source(source, source_name):
        (
            cross_source_eth_route_primary_feeds,
            incomplete_cross_source_reads,
        ) = _discover_eth_route_primary_feeds(source)

    print(f"\n#### ⏳ Pending Price Feed Updates ({len(pending_assets)})")
    _print_incomplete_cross_source_discovery(incomplete_cross_source_reads)

    for item in pending_assets:
        asset_name = item["asset"]
        asset_addr = item["asset_addr"]

        print(f"\n**{asset_name}** (`{asset_addr}`)")

        # Get pending config details based on source type
        try:
            if hasattr(source, 'pendingUpdates'):
                # Chainlink, Pyth, Stork, Curve
                pending = source.pendingUpdates(asset_addr)
                if hasattr(pending, 'actionId') and pending.actionId > 0:
                    print(f"- Action ID: {pending.actionId}")

                    # Read confirmation timing from the shared TimeLock API.
                    if hasattr(source, 'getActionConfirmationBlock'):
                        confirm_block = source.getActionConfirmationBlock(
                            pending.actionId
                        )
                        if confirm_block > 0:
                            print(f"- Confirm Block: {confirm_block}")

                    # Show pending config details
                    if hasattr(pending, 'config'):
                        config = pending.config
                        if hasattr(config, 'feed') and str(config.feed) != ZERO_ADDRESS:
                            print(f"- Pending Feed: `{config.feed}`")
                            matching_sources = (
                                _matching_cross_source_eth_route_primary_feeds(
                                    config.feed,
                                    getattr(config, 'needsEthToUsd', False),
                                    cross_source_eth_route_primary_feeds,
                                )
                            )
                            if matching_sources:
                                sources = ", ".join(matching_sources)
                                print(
                                    "- ⚠️ Cross-source ETH conversion warning: "
                                    "`needsEthToUsd=True`, but pending feed "
                                    f"`{config.feed}` is also the primary feed "
                                    f"of an ETH route in {sources}. PriceDesk resolves the "
                                    "ETH conversion outside RedStone; investigate "
                                    "before confirmation or activation."
                                )
                        if hasattr(config, 'feedId') and config.feedId:
                            print(f"- Pending Feed ID: `0x{config.feedId.hex()}`")
                        if hasattr(config, 'staleTime'):
                            stale_time = _format_route_stale_time(
                                config.staleTime,
                                state.mission_control_stale_time,
                                stale_time_generation,
                                getattr(config, 'needsEthToUsd', False),
                                getattr(config, 'needsBtcToUsd', False),
                            )
                            print(f"- Pending Stale Time: {stale_time}")
                        if hasattr(config, 'pool') and str(config.pool) != ZERO_ADDRESS:
                            print(f"- Pending Pool: `{config.pool}`")

            elif hasattr(source, 'pendingPriceConfigs'):
                # BlueChipYield, UndyVault, AeroRipe
                pending = source.pendingPriceConfigs(asset_addr)
                if hasattr(pending, 'actionId') and pending.actionId > 0:
                    print(f"- Action ID: {pending.actionId}")

                    # Read confirmation timing from the shared TimeLock API.
                    if hasattr(source, 'getActionConfirmationBlock'):
                        confirm_block = source.getActionConfirmationBlock(
                            pending.actionId
                        )
                        if confirm_block > 0:
                            print(f"- Confirm Block: {confirm_block}")

                    # Show pending config details
                    if hasattr(pending, 'config'):
                        config = pending.config
                        if hasattr(config, 'underlyingAsset') and str(config.underlyingAsset) != ZERO_ADDRESS:
                            underlying_name = get_token_name(str(config.underlyingAsset))
                            print(f"- Pending Underlying: {underlying_name}")
                        if hasattr(config, 'minSnapshotDelay'):
                            print(f"- Pending Min Snapshot Delay: {format_blocks_to_time(config.minSnapshotDelay)}")
                        if hasattr(config, 'staleTime'):
                            print(f"- Pending Stale Time: {config.staleTime}s")

        except Exception as e:
            print(f"- Error retrieving pending config: {e}")


def _print_price_source_assets(
    source,
    source_name: str,
    num_assets: int,
    stale_time_generation=STALE_TIME_GENERATION_UNKNOWN,
    cross_source_inventory=None,
):
    """Print per-asset config for a price source."""
    asset_rows = []  # For Chainlink (table format)
    curve_configs = []
    yield_configs = []  # BlueChipYield / UndyVault with underlyingAsset
    pyth_configs = []
    stork_configs = []
    aero_configs = []  # AeroRipePrices (priceConfigs without underlyingAsset)
    redstone_warnings = []
    cross_source_eth_route_primary_feeds = {}
    incomplete_cross_source_reads = ()
    if cross_source_inventory is not None:
        (
            cross_source_eth_route_primary_feeds,
            incomplete_cross_source_reads,
        ) = cross_source_inventory
    elif _is_redstone_source(source, source_name):
        (
            cross_source_eth_route_primary_feeds,
            incomplete_cross_source_reads,
        ) = _discover_eth_route_primary_feeds(source)

    for j in range(1, num_assets):
        time.sleep(RPC_DELAY)
        asset_addr = str(source.assets(j))
        if asset_addr == ZERO_ADDRESS:
            continue

        asset_name = get_token_name(asset_addr)

        # Different price source types have different config methods
        if hasattr(source, 'feedConfig'):
            config = source.feedConfig(asset_addr)
            if hasattr(config, 'feed'):
                # Chainlink: feed, decimals, needsEthToUsd, needsBtcToUsd, staleTime
                feed_addr = format_address(str(config.feed)) if str(config.feed) != ZERO_ADDRESS else "N/A"
                needs_eth = getattr(config, 'needsEthToUsd', False)
                needs_btc = getattr(config, 'needsBtcToUsd', False)
                stale = getattr(config, 'staleTime', 0)
                matching_sources = _matching_cross_source_eth_route_primary_feeds(
                    config.feed,
                    needs_eth,
                    cross_source_eth_route_primary_feeds,
                )
                if matching_sources:
                    redstone_warnings.append(
                        (asset_name, str(config.feed), matching_sources)
                    )
                asset_rows.append([
                    asset_name,
                    feed_addr,
                    f"ETH:{needs_eth}, BTC:{needs_btc}",
                    _format_route_stale_time(
                        stale,
                        state.mission_control_stale_time,
                        stale_time_generation,
                        needs_eth,
                        needs_btc,
                    )
                ])
            elif hasattr(config, 'feedId'):
                # Pyth or Stork: feedId, staleTime
                # Distinguish by source having maxConfidenceRatio (Pyth) or not (Stork)
                if hasattr(source, 'maxConfidenceRatio'):
                    pyth_configs.append({
                        "asset": asset_name,
                        "asset_addr": asset_addr,
                        "config": config,
                    })
                else:
                    stork_configs.append({
                        "asset": asset_name,
                        "asset_addr": asset_addr,
                        "config": config,
                    })
        elif hasattr(source, 'priceConfigs'):
            config = source.priceConfigs(asset_addr)
            # BlueChipYield/UndyVault have underlyingAsset, AeroRipePrices does not
            if hasattr(config, 'underlyingAsset') and str(config.underlyingAsset) != ZERO_ADDRESS:
                yield_configs.append({
                    "asset": asset_name,
                    "asset_addr": asset_addr,
                    "config": config,
                })
            elif hasattr(config, 'minSnapshotDelay') and config.minSnapshotDelay > 0:
                # AeroRipePrices style - has minSnapshotDelay but no underlyingAsset
                aero_configs.append({
                    "asset": asset_name,
                    "asset_addr": asset_addr,
                    "config": config,
                })
        elif hasattr(source, 'curveConfig'):
            # Curve style - collect for separate display
            config = source.curveConfig(asset_addr)
            if config and str(config.pool) != ZERO_ADDRESS:
                curve_configs.append({
                    "asset": asset_name,
                    "asset_addr": asset_addr,
                    "config": config,
                })
        else:
            # Fallback - just show asset is registered
            asset_rows.append([asset_name, "Configured", "-", "-"])

    if asset_rows:
        headers = ["Asset", "Feed/Underlying", "Config", "StaleTime"]
        print(f"\n#### Registered Assets ({len(asset_rows)})")
        print(f"| {' | '.join(headers)} |")
        print(f"| {' | '.join(['---' for _ in headers])} |")
        for row in asset_rows:
            print(f"| {' | '.join(str(cell) for cell in row)} |")

    _print_incomplete_cross_source_discovery(incomplete_cross_source_reads)

    if redstone_warnings:
        print("\n#### ⚠️ RedStone Cross-Source ETH Conversion Warnings")
        for asset_name, feed, matching_sources in redstone_warnings:
            sources = ", ".join(matching_sources)
            print(
                f"- **{asset_name}**: `needsEthToUsd=True`, but primary feed "
                f"`{feed}` is also the primary feed of an ETH route in {sources}. "
                "PriceDesk resolves the ETH conversion outside RedStone; "
                "investigate this self-conversion hazard before activation."
            )

    # Curve configs - display separately in cleaner format
    if curve_configs:
        pool_type_names = {
            1: "STABLESWAP_NG",
            2: "TWO_CRYPTO_NG",
            4: "TRICRYPTO_NG",
            8: "TWO_CRYPTO",
            16: "METAPOOL",
            32: "CRYPTO",
        }

        print(f"\n#### Curve Pool Configs ({len(curve_configs)})")
        for item in curve_configs:
            config = item["config"]
            asset_name = item["asset"]
            pool_type = pool_type_names.get(config.poolType, f"Type:{config.poolType}")

            # Get underlying tokens
            underlying_names = []
            for k in range(config.numUnderlying):
                u_addr = str(config.underlying[k])
                if u_addr != ZERO_ADDRESS:
                    underlying_names.append(get_token_name(u_addr))

            print(f"\n**{asset_name}**")
            print(f"- Pool: `{config.pool}`")
            print(f"- Type: {pool_type}")
            print(f"- Underlying ({config.numUnderlying}): {', '.join(underlying_names)}")
            print(f"- LP Token: `{config.lpToken}`")
            print(f"- Has Eco Token: {config.hasEcoToken}")

    # Yield configs (BlueChipYield / UndyVault) - display in list format
    if yield_configs:
        print(f"\n#### Yield Token Configs ({len(yield_configs)})")
        for item in yield_configs:
            config = item["config"]
            asset_name = item["asset"]

            # Get protocol name
            protocol_id = getattr(config, 'protocol', 0)
            protocol_name = PROTOCOL_NAMES.get(protocol_id, f"ID:{protocol_id}")

            # Get underlying token name
            underlying = get_token_name(str(config.underlyingAsset))

            # Get last snapshot info
            last_snapshot = getattr(config, 'lastSnapshot', None)

            print(f"\n**{asset_name}**")
            print(f"- Protocol: {protocol_name}")
            print(f"- Underlying: {underlying} (`{config.underlyingAsset}`)")
            print(f"- Underlying Decimals: {config.underlyingDecimals}")
            print(f"- Vault Token Decimals: {config.vaultTokenDecimals}")
            print(f"- Min Snapshot Delay: {format_blocks_to_time(config.minSnapshotDelay)}")
            print(f"- Max Snapshots: {config.maxNumSnapshots}")
            print(f"- Max Upside Deviation: {config.maxUpsideDeviation / 100:.2f}%")
            print(f"- Stale Time: {config.staleTime}s")
            print(f"- Next Index: {config.nextIndex}")
            if last_snapshot and last_snapshot.lastUpdate > 0:
                # lastUpdate is a Unix timestamp - calculate time ago
                now = int(time.time())
                seconds_ago = now - last_snapshot.lastUpdate
                if seconds_ago < 60:
                    time_ago = f"~{seconds_ago:.0f}s ago"
                elif seconds_ago < 3600:
                    time_ago = f"~{seconds_ago/60:.1f}m ago"
                elif seconds_ago < 86400:
                    time_ago = f"~{seconds_ago/3600:.1f}h ago"
                else:
                    time_ago = f"~{seconds_ago/86400:.1f}d ago"
                print(f"- Last Snapshot: supply={last_snapshot.totalSupply}, pps={last_snapshot.pricePerShare}, block={last_snapshot.lastUpdate} ({time_ago})")

    # Pyth configs - display in list format
    if pyth_configs:
        print(f"\n#### Pyth Feed Configs ({len(pyth_configs)})")
        for item in pyth_configs:
            config = item["config"]
            asset_name = item["asset"]
            asset_addr = item["asset_addr"]

            feed_id = config.feedId.hex() if config.feedId else "N/A"
            stale = getattr(config, 'staleTime', 0)

            print(f"\n**{asset_name}**")
            print(f"- Asset Address: `{asset_addr}`")
            print(f"- Feed ID: `0x{feed_id}`")
            print(
                "- Stale Time: "
                + _format_price_feed_stale_time(
                    stale,
                    state.mission_control_stale_time,
                    stale_time_generation,
                )
            )

    # Stork configs - display in list format
    if stork_configs:
        print(f"\n#### Stork Feed Configs ({len(stork_configs)})")
        for item in stork_configs:
            config = item["config"]
            asset_name = item["asset"]
            asset_addr = item["asset_addr"]

            feed_id = config.feedId.hex() if config.feedId else "N/A"
            stale = getattr(config, 'staleTime', 0)

            print(f"\n**{asset_name}**")
            print(f"- Asset Address: `{asset_addr}`")
            print(f"- Feed ID: `0x{feed_id}`")
            print(
                "- Stale Time: "
                + _format_price_feed_stale_time(
                    stale,
                    state.mission_control_stale_time,
                    stale_time_generation,
                )
            )

    # AeroRipe configs - display in list format
    if aero_configs:
        print(f"\n#### RIPE Price Configs ({len(aero_configs)})")
        for item in aero_configs:
            config = item["config"]
            asset_name = item["asset"]
            asset_addr = item["asset_addr"]

            # Get last snapshot info
            last_snapshot = getattr(config, 'lastSnapshot', None)

            print(f"\n**{asset_name}**")
            print(f"- Asset Address: `{asset_addr}`")
            print(f"- Min Snapshot Delay: {format_blocks_to_time(config.minSnapshotDelay)}")
            print(f"- Max Snapshots: {config.maxNumSnapshots}")
            print(f"- Max Upside Deviation: {config.maxUpsideDeviation / 100:.2f}%")
            print(f"- Stale Time: {config.staleTime}s")
            print(f"- Next Index: {config.nextIndex}")
            if last_snapshot and last_snapshot.lastUpdate > 0:
                # lastUpdate is a Unix timestamp - calculate time ago
                now = int(time.time())
                seconds_ago = now - last_snapshot.lastUpdate
                if seconds_ago < 60:
                    time_ago = f"~{seconds_ago:.0f}s ago"
                elif seconds_ago < 3600:
                    time_ago = f"~{seconds_ago/60:.1f}m ago"
                elif seconds_ago < 86400:
                    time_ago = f"~{seconds_ago/3600:.1f}h ago"
                else:
                    time_ago = f"~{seconds_ago/86400:.1f}d ago"
                print(f"- Last Snapshot: price={last_snapshot.price}, block={last_snapshot.lastUpdate} ({time_ago})")


def print_all_price_sources():
    """Print all price source configurations."""
    print("\n<a id=\"price-source-configs\"></a>")
    print("## Price Source Configurations")

    for reg_id in sorted(state.price_sources.keys()):
        source_info = state.price_sources[reg_id]
        print_price_source_config(reg_id, source_info)
        print("\n---")


# ============================================================================
# Main Entry Point
# ============================================================================


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Report Base price-source configuration and policy.",
    )
    parser.add_argument(
        "--strict-activation",
        action="store_true",
        help=(
            "require recognized current-generation source runtimes and fail "
            "closed on enumerable registry changes, invalid policy, unsafe "
            "routes, or incomplete discovery; pending-new registry entries "
            "still require separate event evidence"
        ),
    )
    parser.add_argument(
        "--chainlink-anchor",
        choices=("ETH", "BTC"),
        help="anchor kind for a strict proposed-feed rotation preflight",
    )
    parser.add_argument(
        "--proposed-anchor-feed",
        help="proposed Chainlink ETH/USD or BTC/USD feed address",
    )
    parser.add_argument(
        "--expected-global-stale-time",
        type=int,
        default=None,
        help=(
            "exact deployment-policy global required by strict checks "
            "(default: 86400 seconds)"
        ),
    )
    args = parser.parse_args(argv)
    if (args.chainlink_anchor is None) != (args.proposed_anchor_feed is None):
        parser.error(
            "--chainlink-anchor and --proposed-anchor-feed must be supplied together"
        )
    if args.chainlink_anchor is not None:
        feed = str(args.proposed_anchor_feed)
        if (
            len(feed) != 42
            or not feed.lower().startswith("0x")
            or any(char not in "0123456789abcdefABCDEF" for char in feed[2:])
            or feed.lower() == ZERO_ADDRESS
        ):
            parser.error("--proposed-anchor-feed must be a 20-byte hex address")
    if (
        args.expected_global_stale_time is not None
        and not args.strict_activation
        and args.chainlink_anchor is None
    ):
        parser.error(
            "--expected-global-stale-time requires --strict-activation or "
            "a complete Chainlink anchor preflight"
        )
    if args.expected_global_stale_time is None:
        args.expected_global_stale_time = (
            DEFAULT_EXPECTED_ACTIVATION_GLOBAL_STALE_TIME
        )
    return args


def main(argv=None):
    """Main entry point."""
    args = _parse_args(argv)
    # Output file path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, "prices_output.md")

    print("Connecting to Base mainnet via Alchemy...", file=sys.stderr)

    # Set etherscan API
    setup_boa_etherscan()

    # Fork at latest block
    with boa_fork_context() as block_number:
        print(f"Connected. Block: {block_number}\n", file=sys.stderr)

        # Load all price source configurations
        initialize_prices()

        if args.strict_activation or args.chainlink_anchor is not None:
            _run_strict_activation_qualifications(
                args.chainlink_anchor,
                args.proposed_anchor_feed,
                args.expected_global_stale_time,
            )
            print(
                "Strict enumerable price-source checks passed; pending-new "
                "registry entries require separate event evidence.",
                file=sys.stderr,
            )

        print(f"Writing output to {output_file}...", file=sys.stderr)

        # Write report to file
        with output_to_file(output_file):
            # Header
            print_report_header("Ripe Protocol - Price Source Configurations", block_number)

            print("\nDetailed configuration for all price sources registered in PriceDesk.\n")

            # Table of Contents
            print_table_of_contents()

            # PriceDesk overview
            print_price_desk_overview()

            # All price source configs
            print_all_price_sources()

            # Footer
            print_report_footer(block_number)

        print(f"Done! Output saved to {output_file}", file=sys.stderr)


if __name__ == "__main__":
    main()
