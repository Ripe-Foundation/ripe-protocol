"""Fail-closed Robinhood PriceDesk activation-plan admission policy."""

from __future__ import annotations

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


def _fail(message: str) -> None:
    raise PriceSourceAdmissionError(message)


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


def require_selected_bluechip_slot_3_plan(
    *,
    registered_sources: Sequence[str],
    priority_source_ids: Sequence[int],
    curve_routes: Sequence[tuple[str, str, Sequence[tuple[str, str]]]],
    candidate_address: str,
) -> None:
    """Gate Safe-calldata production for the exact selected admission plan."""
    load_manifest()
    if tuple(registered_sources) != tuple(item[1] for item in SELECTED_REGISTRY):
        _fail("registered-source growth or reordering is not admitted")
    if tuple(priority_source_ids) != SELECTED_PRIORITIES:
        _fail("priority source order is not admitted")
    canonical_routes = tuple(
        (asset, pool, tuple(underlyings))
        for asset, pool, underlyings in curve_routes
    )
    if canonical_routes != SUPPORTED_CURVE_ROUTES:
        _fail("Curve-over-snapshot or other unqualified graph is not admitted")
    encoded_candidate = str(candidate_address)
    if not re.fullmatch(r"0x[0-9a-fA-F]{40}", encoded_candidate):
        _fail("BlueChip slot-3 candidate address is malformed")
    candidate_value = int(encoded_candidate, 16)
    if candidate_value == 0:
        _fail("BlueChip slot-3 candidate address must be nonzero")
