"""Fail-closed Robinhood PriceDesk activation-plan admission policy."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "config" / "robinhood-price-source-admission.json"
DECISION = {
    "id": "RH-D042",
    "title": "PriceDesk source isolation uses bounded policy-only admission",
}
SOURCE_ALLOWANCES = {
    "get_price_and_has_feed": 250_000,
    "has_price_feed": 75_000,
    "add_price_snapshot": 150_000,
}
SELECTED_REGISTRY = (
    (1, "ChainlinkPrices", "contracts/priceSources/ChainlinkPrices.vy"),
    (2, "CurvePrices", "contracts/priceSources/CurvePrices.vy"),
    (3, "BlueChipYieldPrices", "contracts/priceSources/BlueChipYieldPrices.vy"),
)
SELECTED_PRIORITIES = (1, 2)
SUPPORTED_CURVE_ROUTES = (
    (
        "GREEN",
        "GREEN/USDG",
        (("GREEN", "target_asset"), ("USDG", "ChainlinkPrices")),
    ),
)
FORBIDDEN_CURVE_UNDERLYING_SOURCES = frozenset(
    {"BlueChipYieldPrices", "UndyVaultPrices", "snapshot_source"}
)
QUALIFICATION_ENVELOPE = {
    "selected_registered_sources": 3,
    "max_qualified_registered_sources": 10,
    "max_curve_underlyings": 4,
    "max_snapshot_observations": 25,
    "max_vaults_per_user": 5,
    "max_assets_per_vault": 15,
    "max_user_valuation_positions": 75,
    "max_active_claim_assets": 20,
    "max_claim_maintenance_batch": 15,
}


class PriceSourceAdmissionError(ValueError):
    """Raised when a PriceDesk activation plan leaves the qualified envelope."""


@dataclass(frozen=True)
class LivePriceSourceTopology:
    """Observed on-chain state used to authorize slot-3 calldata generation."""

    next_registry_id: int
    registry_addresses: tuple[str, str, str]
    priority_source_ids: tuple[int, ...]
    curve_feed_asset: str
    curve_pool: str
    curve_num_underlying: int
    curve_underlyings: tuple[str, str, str, str]
    underlying_price_source_ids: tuple[tuple[str, tuple[int, ...]], ...]
    chainlink_usdg_feed: str
    max_vaults_per_user: int
    max_assets_per_vault: int


def _fail(message: str) -> None:
    raise PriceSourceAdmissionError(message)


def _address(value: Any, label: str) -> str:
    encoded = str(value)
    if re.fullmatch(r"0x[0-9a-fA-F]{40}", encoded) is None:
        _fail(f"{label} address is malformed")
    return encoded.lower()


def _canonical_registry(value: Sequence[Mapping[str, Any]]) -> tuple:
    try:
        return tuple(
            (int(item["id"]), item["semantic"], item["source_path"])
            for item in value
        )
    except (KeyError, TypeError, ValueError) as error:
        raise PriceSourceAdmissionError("selected_registry is malformed") from error


def _canonical_curve_routes(value: Sequence[Mapping[str, Any]]) -> tuple:
    try:
        return tuple(
            (
                route["feed_asset"],
                route["pool"],
                tuple(
                    (item["asset"], item["resolution"])
                    for item in route["underlyings"]
                ),
            )
            for route in value
        )
    except (KeyError, TypeError) as error:
        raise PriceSourceAdmissionError("supported_curve_routes is malformed") from error


def validate_manifest(value: Mapping[str, Any]) -> None:
    expected_keys = {
        "schema_version",
        "decision",
        "enforcement",
        "source_allowances",
        "selected_registry",
        "priority_source_ids",
        "supported_curve_routes",
        "forbidden_curve_underlying_sources",
        "qualification_envelope",
    }
    if set(value) != expected_keys:
        _fail("manifest fields do not match the canonical schema")
    if value["schema_version"] != 1:
        _fail("unsupported manifest schema_version")
    if value["decision"] != DECISION:
        _fail("decision identifier/title drift")
    if value["enforcement"] != {
        "boundary": "policy_only_with_required_preflight",
        "on_chain_topology_guard": False,
        "governance_can_bypass_preflight": True,
    }:
        _fail("enforcement boundary drift")
    if value["source_allowances"] != SOURCE_ALLOWANCES:
        _fail("PriceDesk source allowance drift")
    if _canonical_registry(value["selected_registry"]) != SELECTED_REGISTRY:
        _fail("registered-source list/order leaves the selected topology")
    if tuple(value["priority_source_ids"]) != SELECTED_PRIORITIES:
        _fail("priority source order leaves the selected topology")
    routes = _canonical_curve_routes(value["supported_curve_routes"])
    if routes != SUPPORTED_CURVE_ROUTES:
        _fail("Curve feed or underlying graph leaves the selected topology")
    resolutions = {
        resolution
        for _asset, _pool, underlyings in routes
        for _underlying, resolution in underlyings
    }
    forbidden = frozenset(value["forbidden_curve_underlying_sources"])
    if forbidden != FORBIDDEN_CURVE_UNDERLYING_SOURCES:
        _fail("forbidden Curve-underlying source set drift")
    if resolutions & forbidden:
        _fail("Curve-over-snapshot-source graphs are not admitted")
    if value["qualification_envelope"] != QUALIFICATION_ENVELOPE:
        _fail("vault, asset, snapshot, Curve, or source-count envelope drift")


def load_manifest(path: Path = DEFAULT_MANIFEST) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise PriceSourceAdmissionError(f"cannot load admission manifest: {error}") from error
    if not isinstance(value, Mapping):
        _fail("admission manifest root must be an object")
    validate_manifest(value)
    return value


def require_selected_live_topology(
    *,
    observed: LivePriceSourceTopology,
    selected_chainlink_address: str,
    selected_curve_address: str,
    selected_green_address: str,
    selected_usdg_address: str,
    selected_curve_pool_address: str,
    selected_usdg_chainlink_feed: str,
) -> None:
    """Validate the selected topology from raw live contract readbacks."""
    load_manifest()
    zero = "0x" + "0" * 40
    expected_registry = (
        _address(selected_chainlink_address, "selected Chainlink"),
        _address(selected_curve_address, "selected Curve"),
        zero,
    )
    registry = tuple(
        _address(value, f"PriceDesk slot {index}")
        for index, value in enumerate(observed.registry_addresses, start=1)
    )
    if observed.next_registry_id != 3 or registry != expected_registry:
        _fail("live registered-source count, address, or slot order is not admitted")
    if tuple(observed.priority_source_ids) != SELECTED_PRIORITIES:
        _fail("priority source order is not admitted")

    green = _address(selected_green_address, "selected GREEN")
    usdg = _address(selected_usdg_address, "selected USDG")
    if _address(observed.curve_feed_asset, "live Curve feed asset") != green:
        _fail("live Curve feed asset is not the selected GREEN token")
    if _address(observed.curve_pool, "live GREEN Curve pool") != _address(
        selected_curve_pool_address,
        "selected GREEN Curve pool",
    ):
        _fail("live GREEN Curve pool is not admitted")
    underlying = tuple(
        _address(value, f"live Curve underlying {index}")
        for index, value in enumerate(observed.curve_underlyings)
    )
    if observed.curve_num_underlying != 2 or underlying != (usdg, green, zero, zero):
        _fail("live Curve underlying count or list is not admitted")

    resolutions = tuple(
        (
            _address(asset, "live Curve underlying resolution asset"),
            tuple(int(source_id) for source_id in source_ids),
        )
        for asset, source_ids in observed.underlying_price_source_ids
    )
    if resolutions != ((usdg, (1,)),):
        _fail("live Curve underlying resolution is not Chainlink-only")
    feed = _address(observed.chainlink_usdg_feed, "live USDG Chainlink feed")
    if feed == zero or feed != _address(
        selected_usdg_chainlink_feed,
        "selected USDG Chainlink feed",
    ):
        _fail("live USDG Chainlink feed is missing or unexpected")

    envelope = QUALIFICATION_ENVELOPE
    if (
        observed.max_vaults_per_user != envelope["max_vaults_per_user"]
        or observed.max_assets_per_vault != envelope["max_assets_per_vault"]
        or observed.max_vaults_per_user * observed.max_assets_per_vault
        != envelope["max_user_valuation_positions"]
    ):
        _fail("live vault or asset envelope is not admitted")


def require_selected_bluechip_slot_3_candidate(
    *,
    candidate_address: str,
    observed_slot_3_address: str,
) -> None:
    """Validate the finalized candidate and a still-empty live slot 3."""
    load_manifest()
    zero = "0x" + "0" * 40
    if _address(observed_slot_3_address, "PriceDesk slot 3") != zero:
        _fail("PriceDesk slot 3 became occupied before calldata generation")
    encoded_candidate = _address(candidate_address, "BlueChip slot-3 candidate")
    if encoded_candidate == zero:
        _fail("BlueChip slot-3 candidate address must be nonzero")
