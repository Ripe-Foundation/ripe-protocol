#!/usr/bin/env python3
"""Synchronize the derived Robinhood parameter ledger from readable sources.

The only human-edited value authorities are config/BluePrint.py for deployment
inputs and contracts/config/DefaultsRobinhood.vy for Defaults-interface values.
This command never renders or overwrites Vyper source and never uses RPC.
"""

from __future__ import annotations

import argparse
import copy
from collections import Counter
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = "h04-robinhood-parameters-v4-derived-ledger"
LEGACY_SCHEMA_VERSION = "h04-robinhood-parameters-v3-profile1-pr66"
LAUNCH_INPUT_COMMIT = "74c4120fbfa1ade859dc32f61acdf567c139fe02"
MORPHO_AUTHORITY_COMMIT = "33ad0f3c08bf6dc88f6569c622886d264d6e2868"

ROOT = Path(__file__).resolve().parents[2]
LEDGER_PATH = ROOT / "config" / "robinhood-parameters.json"
BLUEPRINT_PATH = ROOT / "config" / "BluePrint.py"
DEFAULTS_PATH = ROOT / "contracts" / "config" / "DefaultsRobinhood.vy"

TOP_LEVEL_KEYS = {
    "schema_version",
    "baseline",
    "decision_registry",
    "binding_schedules",
    "parameters",
}
BASELINE_KEYS = {
    "commit",
    "tree",
    "branch",
    "phase_a_evidence_sha256",
    "controlling_r2_path",
    "controlling_r2_sha256",
}
RECORD_KEYS = {
    "id",
    "h03_ref",
    "destination",
    "description",
    "value",
    "unit",
    "status",
    "source",
    "owner",
    "reviewer_class",
    "approval",
    "launch_phase",
    "blockers",
    "zero_semantics",
    "base_comparison",
    "conversion",
    "consumers",
    "invalidation",
}
LEGACY_RECORD_KEYS = RECORD_KEYS | {"generated_repr"}

GEN_CONFIG_FIELDS = (
    "perUserMaxVaults",
    "perUserMaxAssetsPerVault",
    "priceStaleTime",
    "canDeposit",
    "canWithdraw",
    "canBorrow",
    "canRepay",
    "canClaimLoot",
    "canLiquidate",
    "canRedeemCollateral",
    "canRedeemInStabPool",
    "canBuyInAuction",
    "canClaimInStabPool",
)
AUCTION_FIELDS = ("hasParams", "startDiscount", "maxDiscount", "delay", "duration")
GEN_DEBT_FIELDS = (
    "perUserDebtLimit",
    "globalDebtLimit",
    "minDebtAmount",
    "numAllowedBorrowers",
    "maxBorrowPerInterval",
    "numBlocksPerInterval",
    "minDynamicRateBoost",
    "maxDynamicRateBoost",
    "increasePerDangerBlock",
    "maxBorrowRate",
    "maxLtvDeviation",
    "keeperFeeRatio",
    "minKeeperFee",
    "maxKeeperFee",
    "isDaowryEnabled",
    "ltvPaybackBuffer",
)
BOND_FIELDS = (
    "asset",
    "amountPerEpoch",
    "canBond",
    "minRipePerUnit",
    "maxRipePerUnit",
    "maxRipePerUnitLockBonus",
    "epochLength",
    "shouldAutoRestart",
    "restartDelayBlocks",
)
REWARD_FIELDS = (
    "arePointsEnabled",
    "ripePerBlock",
    "borrowersAlloc",
    "stakersAlloc",
    "votersAlloc",
    "genDepositorsAlloc",
    "autoStakeRatio",
    "autoStakeDurationRatio",
    "stabPoolRipePerDollarClaimed",
)
LOCK_FIELDS = (
    "minLockDuration",
    "maxLockDuration",
    "maxLockBoost",
    "canExit",
    "exitFee",
)
GOV_FIELDS = (
    "asset",
    *(f"config.lockTerms.{field}" for field in LOCK_FIELDS),
    "config.assetWeight",
    "config.shouldFreezeWhenBadDebt",
)
HR_FIELDS = (
    "contribTemplate",
    "maxCompensation",
    "minCliffLength",
    "maxStartDelay",
    "minVestingLength",
    "maxVestingLength",
)
DEBT_TERM_FIELDS = (
    "ltv",
    "redemptionThreshold",
    "liqThreshold",
    "liqFee",
    "borrowRate",
    "daowry",
)
ASSET_FIELDS = (
    "asset",
    "config.vaultIds",
    "config.stakersPointsAlloc",
    "config.voterPointsAlloc",
    "config.perUserDepositLimit",
    "config.globalDepositLimit",
    "config.minDepositBalance",
    *(f"config.debtTerms.{field}" for field in DEBT_TERM_FIELDS),
    "config.shouldBurnAsPayment",
    "config.shouldTransferToEndaoment",
    "config.shouldSwapInStabPools",
    "config.shouldAuctionInstantly",
    "config.canDeposit",
    "config.canWithdraw",
    "config.canRedeemCollateral",
    "config.canRedeemInStabPool",
    "config.canBuyInAuction",
    "config.canClaimInStabPool",
    "config.specialStabPoolId",
    *(f"config.customAuctionParams.{field}" for field in AUCTION_FIELDS),
    "config.whitelist",
    "config.isNft",
)
GOV_ROWS = ("RIPE", "RIPE_WETH_LP")
ACTIVE_GOV_ROWS = ("RIPE",)
ASSET_ROWS = (
    "GREEN",
    "RIPE",
    "SGREEN",
    "WETH",
    "GREEN_USDG_LP",
    "RIPE_WETH_LP",
)
ACTIVE_ASSET_ROWS = (
    "WETH",
    "RIPE",
    "SGREEN",
    "GREEN",
)
OMITTED_GOV_ROWS = ("RIPE_WETH_LP",)
OMITTED_ASSET_ROWS = ("GREEN_USDG_LP", "RIPE_WETH_LP")

ASSERTION_DESTINATION_PATHS = (
    "Deployment.DP-01.lootbox.minUnderscoreSendInterval",
    "Deployment.DP-02.lootbox.underscoreSendInterval",
    "Deployment.DP-03.deleverage.deleverageCooldown",
    "Deployment.DP-04.ledger.actionBlockSourceSemantic",
    "Deployment.DP-06.timelocks.minimumExpirationHeadroom",
    "Deployment.DP-09.psm.redemptionFirstOrder",
    "Deployment.DP-09.psm.greenMintLastOrder",
    "Deployment.DP-10.aapl.capFormula",
    "Deployment.DP-11.stock.enabledVaultCount",
    "Deployment.DP-12.launchGraph.assetCount",
    "Deployment.DP-13.stock.excludedFromStabilityPool",
    "Deployment.DP-14.lp.ltv",
)

CONSTRUCTOR_ABI_NAMES = (
    "_contribTemplate",
    "_trainingWheels",
    "_ripeToken",
    "_greenToken",
    "_sgreenToken",
    "_usdgToken",
    "_wethToken",
)
CONSTRUCTOR_BLUEPRINT_KEYS = (
    "CONTRIBUTOR_TEMPLATE",
    "TRAINING_WHEELS",
    "RIPE_TOKEN",
    "GREEN_TOKEN",
    "SGREEN_TOKEN",
    "USDG",
    "WETH",
)


class ManifestError(ValueError):
    """Stable fail-closed configuration diagnostic."""


def _expect_keys(value: Mapping[str, Any], keys: set[str], code: str) -> None:
    if set(value) != keys:
        extra = sorted(set(value) - keys)
        missing = sorted(keys - set(value))
        raise ManifestError(f"{code}:extra={extra}:missing={missing}")


def _reject_sensitive_or_placeholder_text(value: Any) -> None:
    if isinstance(value, str):
        lowered = value.lower()
        forbidden = (
            "todo",
            "tbd",
            "dummy",
            "placeholder",
            "/users/",
            "/home/",
            "localhost",
            "http://",
            "https://",
            "api_key",
            "private_key",
            "mnemonic",
        )
        if any(token in lowered for token in forbidden):
            raise ManifestError("H04_FORBIDDEN_TEXT")
    elif isinstance(value, Mapping):
        for nested in value.values():
            _reject_sensitive_or_placeholder_text(nested)
    elif isinstance(value, list):
        for nested in value:
            _reject_sensitive_or_placeholder_text(nested)


def canonical_default_paths() -> tuple[str, ...]:
    paths: list[str] = []
    paths.extend(f"Defaults.genConfig.{field}" for field in GEN_CONFIG_FIELDS)
    paths.extend(f"Defaults.genDebtConfig.{field}" for field in GEN_DEBT_FIELDS)
    paths.extend(
        f"Defaults.genDebtConfig.genAuctionParams.{field}"
        for field in AUCTION_FIELDS
    )
    paths.extend(
        (
            "Defaults.ripeAvailForRewards",
            "Defaults.ripeAvailForHr",
            "Defaults.ripeAvailForBonds",
        )
    )
    paths.extend(f"Defaults.ripeBondConfig.{field}" for field in BOND_FIELDS)
    paths.extend(f"Defaults.rewardsConfig.{field}" for field in REWARD_FIELDS)
    for row in GOV_ROWS:
        paths.extend(
            f"Defaults.ripeGovVaultConfigs[{row}].{field}" for field in GOV_FIELDS
        )
    paths.extend(f"Defaults.hrConfig.{field}" for field in HR_FIELDS)
    paths.extend(
        (
            "Defaults.underscoreRegistry",
            "Defaults.trainingWheels",
            "Defaults.shouldCheckLastTouch",
        )
    )
    for row in ASSET_ROWS:
        paths.extend(
            f"Defaults.assetConfigs[{row}].{field}" for field in ASSET_FIELDS
        )
    paths.extend(
        (
            "Defaults.priorityLiqAssetVaults[0].vaultId",
            "Defaults.priorityLiqAssetVaults[0].asset",
            "Defaults.priorityStabVaults[0].vaultId",
            "Defaults.priorityStabVaults[0].asset",
            "Defaults.priorityPriceSourceIds",
            "Defaults.liteSigners[0]",
        )
    )
    if len(paths) != 272 or len(set(paths)) != 272:
        raise ManifestError("H04_INTERNAL_DEFAULT_PATH_CENSUS")
    return tuple(paths)


def default_selectors() -> tuple[str, ...]:
    return (
        "genConfig",
        "genDebtConfig",
        "ripeAvailForRewards",
        "ripeAvailForHr",
        "ripeAvailForBonds",
        "ripeBondConfig",
        "rewardsConfig",
        "ripeGovVaultConfigs",
        "hrConfig",
        "underscoreRegistry",
        "trainingWheels",
        "shouldCheckLastTouch",
        "assetConfigs",
        "priorityLiqAssetVaults",
        "priorityStabVaults",
        "priorityPriceSourceIds",
        "liteSigners",
    )


def _validate_value(value: Mapping[str, Any]) -> None:
    kind = value.get("kind")
    keys = {
        "concrete": {"kind", "raw"},
        "external_fact": {"kind", "raw"},
        "symbolic_binding": {"kind", "name"},
        "omitted": {"kind", "profile"},
        "typed_null": {"kind", "reason"},
        "derived": {"kind", "formula", "inputs"},
        "inherited": {"kind", "inherited_from"},
    }.get(str(kind))
    if keys is None:
        raise ManifestError("H04_VALUE_KIND")
    _expect_keys(value, keys, "H04_VALUE_KEYS")


def _validate_assertion_path_census(paths: Sequence[str]) -> None:
    counts = Counter(paths)
    missing = sorted(set(ASSERTION_DESTINATION_PATHS) - set(paths))
    extra = sorted(set(paths) - set(ASSERTION_DESTINATION_PATHS))
    duplicates = sorted(path for path, count in counts.items() if count != 1)
    if tuple(paths) != ASSERTION_DESTINATION_PATHS:
        raise ManifestError(
            "H04_ASSERTION_PATH_CENSUS:"
            f"missing={missing}:extra={extra}:duplicates={duplicates}"
        )


def _validate_shape(ledger: Mapping[str, Any], *, allow_legacy: bool) -> None:
    _expect_keys(ledger, TOP_LEVEL_KEYS, "H04_TOP_KEYS")
    schema = ledger.get("schema_version")
    allowed = {SCHEMA_VERSION}
    if allow_legacy:
        allowed.add(LEGACY_SCHEMA_VERSION)
    if schema not in allowed:
        raise ManifestError(f"H04_SCHEMA_VERSION:{schema}")
    baseline = ledger.get("baseline")
    if not isinstance(baseline, Mapping):
        raise ManifestError("H04_BASELINE_TYPE")
    _expect_keys(baseline, BASELINE_KEYS, "H04_BASELINE_KEYS")

    registry = ledger.get("decision_registry")
    if not isinstance(registry, list) or len(registry) != 22:
        raise ManifestError("H04_DECISION_REGISTRY_CENSUS")
    for entry in registry:
        if not isinstance(entry, Mapping):
            raise ManifestError("H04_DECISION_TYPE")
        _expect_keys(entry, {"id", "status", "operative"}, "H04_DECISION_KEYS")

    schedules = ledger.get("binding_schedules")
    schedule_keys = {
        "id",
        "records",
        "owner",
        "reviewer_class",
        "classification",
        "lifecycle_phase",
        "prerequisite",
        "closure_artifacts",
        "invalidation",
    }
    if not isinstance(schedules, list) or len(schedules) != 14:
        raise ManifestError("H04_BINDING_SCHEDULE_CENSUS")
    for entry in schedules:
        if not isinstance(entry, Mapping):
            raise ManifestError("H04_SCHEDULE_TYPE")
        _expect_keys(entry, schedule_keys, "H04_SCHEDULE_KEYS")

    parameters = ledger.get("parameters")
    valid_parameter_counts = {403, 436} if allow_legacy else {403}
    if not isinstance(parameters, list) or len(parameters) not in valid_parameter_counts:
        raise ManifestError("H04_PARAMETER_CENSUS")
    expected_record_keys = (
        LEGACY_RECORD_KEYS if schema == LEGACY_SCHEMA_VERSION else RECORD_KEYS
    )
    ids: list[str] = []
    destinations: list[str] = []
    for record in parameters:
        if not isinstance(record, Mapping):
            raise ManifestError("H04_RECORD_TYPE")
        _expect_keys(record, expected_record_keys, "H04_RECORD_KEYS")
        ids.append(str(record["id"]))
        destination = record["destination"]
        _expect_keys(destination, {"kind", "path"}, "H04_DESTINATION_KEYS")
        destinations.append(str(destination["path"]))
        _validate_value(record["value"])
        _reject_sensitive_or_placeholder_text(record["value"])
        unit = record["unit"]
        if set(unit) not in ({"kind"}, {"kind", "denominator"}):
            raise ManifestError("H04_UNIT_KEYS")
        _expect_keys(record["source"], {"citation", "commit"}, "H04_SOURCE_KEYS")
        _expect_keys(record["owner"], {"kind", "id"}, "H04_OWNER_KEYS")
        approval_keys = set(record["approval"])
        if approval_keys not in (
            {"status", "date", "provenance"},
            {"status", "date", "provenance", "schedule_id"},
            {"status", "schedule_id"},
        ):
            raise ManifestError("H04_APPROVAL_KEYS")
        _expect_keys(
            record["zero_semantics"],
            {"kind", "explanation"},
            "H04_ZERO_KEYS",
        )
        _expect_keys(
            record["base_comparison"],
            {"kind", "detail"},
            "H04_BASE_COMPARISON_KEYS",
        )
        conversion_keys = set(record["conversion"])
        if conversion_keys not in (
            {"kind"},
            {"kind", "formula"},
            {"kind", "base_blocks", "rh_blocks"},
        ):
            raise ManifestError("H04_CONVERSION_KEYS")
        for field in ("blockers", "consumers", "invalidation"):
            if not isinstance(record[field], list):
                raise ManifestError(f"H04_{field.upper()}_TYPE")
    try:
        numeric_ids = [int(record_id.removeprefix("P-H04-")) for record_id in ids]
    except ValueError as error:
        raise ManifestError("H04_PARAMETER_IDS") from error
    if (
        len(set(ids)) != len(parameters)
        or any(not record_id.startswith("P-H04-") for record_id in ids)
        or numeric_ids != sorted(numeric_ids)
    ):
        raise ManifestError("H04_PARAMETER_IDS")
    _validate_assertion_path_census(
        [
            str(record["destination"]["path"])
            for record in parameters
            if record["destination"]["kind"] == "assertion"
        ]
    )
    if len(set(destinations)) != len(parameters):
        raise ManifestError("H04_DUPLICATE_DESTINATION")


def load_ledger(path: Path = LEDGER_PATH, *, allow_legacy: bool = False) -> Mapping[str, Any]:
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ManifestError(f"H04_JSON:{exc}") from exc
    if not isinstance(parsed, Mapping):
        raise ManifestError("H04_TOP_TYPE")
    _validate_shape(parsed, allow_legacy=allow_legacy)
    return parsed


def _blueprint_module() -> Any:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    module = importlib.import_module("config.BluePrint")
    if set(module.ROBINHOOD_DEPLOYMENT_INPUTS) != {
        record["destination"]["path"]
        for record in load_ledger(allow_legacy=True)["parameters"]
        if record["destination"]["kind"] == "deployment_input"
    }:
        raise ManifestError("H04_BLUEPRINT_DEPLOYMENT_INPUT_CENSUS")
    if tuple(key for _, key in module.ROBINHOOD_DEFAULTS_CONSTRUCTOR) != CONSTRUCTOR_BLUEPRINT_KEYS:
        raise ManifestError("H04_CONSTRUCTOR_BINDING_ORDER")
    try:
        importlib.import_module("config.robinhood_blueprint").validate_curve_launch_authority()
    except Exception as exc:
        raise ManifestError(f"H04_CURVE_AUTHORITY:{type(exc).__name__}:{exc}") from exc
    curve_values = {
        row.input_id: row.value for row in module.ROBINHOOD_CURVE_LAUNCH_INPUTS
    }
    curve_artifacts = {
        "artifact.curve_prices_source_sha256": ROOT
        / "contracts"
        / "priceSources"
        / "CurvePrices.vy",
        "artifact.curve_prices_abi_sha256": ROOT
        / "scripts"
        / "abis"
        / "CurvePrices.json",
    }
    for input_id, path in curve_artifacts.items():
        if hashlib.sha256(path.read_bytes()).hexdigest() != curve_values[input_id]:
            raise ManifestError(f"H04_CURVE_ARTIFACT_DRIFT:{input_id}")
    return module


def _field(value: Any, dotted: str) -> Any:
    for name in dotted.split("."):
        value = getattr(value, name)
    return value


def _ledger_leaf(value: Any, sentinel_bindings: Mapping[str, Any]) -> Mapping[str, Any]:
    if type(value).__name__ == "Address":
        text = str(value)
        lowered = text.lower()
        if lowered in sentinel_bindings:
            binding = sentinel_bindings[lowered]
            if type(binding).__name__ == "SymbolicBinding":
                return {"kind": "symbolic_binding", "name": binding.semantic_name}
            if not isinstance(binding, str) or not re.fullmatch(r"0x[0-9A-Fa-f]{40}", binding):
                raise ManifestError("H04_CONSTRUCTOR_ADDRESS_BINDING")
            return {"kind": "external_fact", "raw": binding}
        if lowered == "0x" + "0" * 40:
            return {"kind": "concrete", "raw": "empty(address)"}
        raise ManifestError(f"H04_DEFAULTS_NONCONSTRUCTOR_ADDRESS:{text}")
    if isinstance(value, list):
        normalized: list[Any] = []
        for item in value:
            leaf = _ledger_leaf(item, sentinel_bindings)
            if leaf["kind"] != "concrete":
                raise ManifestError("H04_NESTED_ADDRESS_LIST")
            normalized.append(leaf["raw"])
        return {"kind": "concrete", "raw": normalized}
    if type(value) not in (bool, int, str):
        raise ManifestError(f"H04_RUNTIME_VALUE_TYPE:{type(value).__name__}")
    return {"kind": "concrete", "raw": value}


def _add_fields(
    values: dict[str, Mapping[str, Any]],
    prefix: str,
    result: Any,
    fields: Sequence[str],
    sentinel_bindings: Mapping[str, Any],
) -> None:
    for field in fields:
        path = f"{prefix}.{field}"
        if path in values:
            raise ManifestError(f"H04_DUPLICATE_SOURCE_PATH:{path}")
        values[path] = _ledger_leaf(_field(result, field), sentinel_bindings)


def _extract_defaults_values_in_active_env(
    boa_module: Any,
    defaults_path: Path,
    sentinels: Sequence[str],
    selected: Any,
    sentinel_bindings: Mapping[str, Any],
) -> dict[str, Mapping[str, Any]]:
    contract = boa_module.load(str(defaults_path), *sentinels)
    constructor = next(
        (entry for entry in contract.abi if entry.get("type") == "constructor"),
        None,
    )
    abi_names = tuple(item["name"] for item in constructor["inputs"]) if constructor else ()
    if abi_names != CONSTRUCTOR_ABI_NAMES:
        raise ManifestError(f"H04_CONSTRUCTOR_ABI:{abi_names}")

    values: dict[str, Mapping[str, Any]] = {}
    gen = contract.genConfig()
    _add_fields(values, "Defaults.genConfig", gen, GEN_CONFIG_FIELDS, sentinel_bindings)
    debt = contract.genDebtConfig()
    _add_fields(values, "Defaults.genDebtConfig", debt, GEN_DEBT_FIELDS, sentinel_bindings)
    _add_fields(
        values,
        "Defaults.genDebtConfig.genAuctionParams",
        debt.genAuctionParams,
        AUCTION_FIELDS,
        sentinel_bindings,
    )
    for selector in ("ripeAvailForRewards", "ripeAvailForHr", "ripeAvailForBonds"):
        values[f"Defaults.{selector}"] = _ledger_leaf(
            getattr(contract, selector)(), sentinel_bindings
        )
    _add_fields(
        values,
        "Defaults.ripeBondConfig",
        contract.ripeBondConfig(),
        BOND_FIELDS,
        sentinel_bindings,
    )
    _add_fields(
        values,
        "Defaults.rewardsConfig",
        contract.rewardsConfig(),
        REWARD_FIELDS,
        sentinel_bindings,
    )

    gov_row_by_key = {"RIPE_TOKEN": "RIPE"}
    sentinel_key = {
        sentinel.lower(): key
        for sentinel, (_, key) in zip(
            sentinels, selected.ROBINHOOD_DEFAULTS_CONSTRUCTOR, strict=True
        )
    }
    gov_results = contract.ripeGovVaultConfigs()
    if len(gov_results) != 1:
        raise ManifestError("H04_ACTIVE_GOV_ROW_CENSUS")
    for entry in gov_results:
        key = sentinel_key.get(str(entry.asset).lower())
        row = gov_row_by_key.get(str(key))
        if row is None:
            raise ManifestError("H04_GOV_ROW_IDENTITY")
        _add_fields(
            values,
            f"Defaults.ripeGovVaultConfigs[{row}]",
            entry,
            GOV_FIELDS,
            sentinel_bindings,
        )

    _add_fields(values, "Defaults.hrConfig", contract.hrConfig(), HR_FIELDS, sentinel_bindings)
    for selector in ("underscoreRegistry", "trainingWheels", "shouldCheckLastTouch"):
        values[f"Defaults.{selector}"] = _ledger_leaf(
            getattr(contract, selector)(), sentinel_bindings
        )

    asset_row_by_key = {
        "WETH": "WETH",
        "RIPE_TOKEN": "RIPE",
        "SGREEN_TOKEN": "SGREEN",
        "GREEN_TOKEN": "GREEN",
    }
    asset_results = contract.assetConfigs()
    if len(asset_results) != 4:
        raise ManifestError("H04_ACTIVE_ASSET_ROW_CENSUS")
    seen_rows: set[str] = set()
    for entry in asset_results:
        key = sentinel_key.get(str(entry.asset).lower())
        row = asset_row_by_key.get(str(key))
        if row is None or row in seen_rows:
            raise ManifestError("H04_ASSET_ROW_IDENTITY")
        seen_rows.add(row)
        _add_fields(
            values,
            f"Defaults.assetConfigs[{row}]",
            entry,
            ASSET_FIELDS,
            sentinel_bindings,
        )
    if seen_rows != set(ACTIVE_ASSET_ROWS):
        raise ManifestError("H04_ACTIVE_ASSET_ROWS")

    liquidations = contract.priorityLiqAssetVaults()
    if len(liquidations) != 1:
        raise ManifestError("H04_PRIORITY_LIQ_CENSUS")
    for index, entry in enumerate(liquidations):
        _add_fields(
            values,
            f"Defaults.priorityLiqAssetVaults[{index}]",
            entry,
            ("vaultId", "asset"),
            sentinel_bindings,
        )
    stability = contract.priorityStabVaults()
    if len(stability) != 1:
        raise ManifestError("H04_PRIORITY_STAB_CENSUS")
    _add_fields(
        values,
        "Defaults.priorityStabVaults[0]",
        stability[0],
        ("vaultId", "asset"),
        sentinel_bindings,
    )
    values["Defaults.priorityPriceSourceIds"] = _ledger_leaf(
        contract.priorityPriceSourceIds(), sentinel_bindings
    )
    values["Defaults.liteSigners[0]"] = _ledger_leaf(
        contract.liteSigners(), sentinel_bindings
    )

    for row in OMITTED_GOV_ROWS:
        for field in GOV_FIELDS:
            values[f"Defaults.ripeGovVaultConfigs[{row}].{field}"] = {
                "kind": "omitted",
                "profile": "Profile 2",
            }
    for row in OMITTED_ASSET_ROWS:
        for field in ASSET_FIELDS:
            values[f"Defaults.assetConfigs[{row}].{field}"] = {
                "kind": "omitted",
                "profile": "Profile 2",
            }
    if set(values) != set(canonical_default_paths()):
        missing = sorted(set(canonical_default_paths()) - set(values))
        extra = sorted(set(values) - set(canonical_default_paths()))
        raise ManifestError(f"H04_DEFAULT_SOURCE_COVERAGE:missing={missing}:extra={extra}")
    return values


def extract_defaults_values(
    defaults_path: Path = DEFAULTS_PATH,
    blueprint: Any | None = None,
) -> dict[str, Mapping[str, Any]]:
    if not defaults_path.is_file():
        raise ManifestError("H04_DEFAULTS_MISSING")
    robinhood_names = [
        entry.name
        for entry in defaults_path.parent.iterdir()
        if entry.name.lower() == "defaultsrobinhood.vy"
    ]
    if robinhood_names != ["DefaultsRobinhood.vy"]:
        raise ManifestError("H04_DEFAULTS_FILENAME_COLLISION")
    source = defaults_path.read_text(encoding="utf-8")
    nonzero_literals = [
        item
        for item in re.findall(r"0x[0-9A-Fa-f]{40}", source)
        if item.lower() != "0x" + "0" * 40
    ]
    if nonzero_literals:
        raise ManifestError(f"H04_DEFAULTS_ADDRESS_LITERAL:{nonzero_literals[0]}")

    selected = blueprint or _blueprint_module()
    if len(selected.ROBINHOOD_DEFAULTS_CONSTRUCTOR) != 7:
        raise ManifestError("H04_CONSTRUCTOR_BINDING_CENSUS")
    sentinels = tuple(f"0x{index:040x}" for index in range(1, 8))
    if len(set(sentinels)) != 7:
        raise ManifestError("H04_SENTINEL_DISTINCTNESS")
    sentinel_bindings = {
        sentinel.lower(): selected.ROBINHOOD_ADDRESSES[key]
        for sentinel, (_, key) in zip(
            sentinels, selected.ROBINHOOD_DEFAULTS_CONSTRUCTOR, strict=True
        )
    }

    try:
        import vyper
        if vyper.__version__ != "0.4.3":
            raise ManifestError(f"H04_VYPER_VERSION:{vyper.__version__}")
        import boa
        import boa.interpret as boa_interpret
        from boa.environment import Env

        previous_env = boa.env
        previous_cache = boa_interpret._disk_cache
        with tempfile.TemporaryDirectory(prefix="rh-defaults-normalize-") as cache:
            os.chmod(cache, 0o700)
            environment_scope = None
            try:
                boa_interpret.set_cache_dir(Path(cache) / "boa")
                environment_scope = boa.set_env(Env())
                return _extract_defaults_values_in_active_env(
                    boa,
                    defaults_path,
                    sentinels,
                    selected,
                    sentinel_bindings,
                )
            finally:
                if environment_scope is not None:
                    environment_scope.__exit__(None, None, None)
                # Restore the exact caller cache object before TemporaryDirectory
                # removes the scoped cache tree.
                boa_interpret._disk_cache = previous_cache
    except ManifestError:
        raise
    except Exception as exc:
        raise ManifestError(f"H04_DEFAULTS_COMPILE:{type(exc).__name__}:{exc}") from exc


def extract_deployment_values(
    defaults_values: Mapping[str, Mapping[str, Any]],
    blueprint: Any | None = None,
) -> dict[str, Mapping[str, Any]]:
    selected = blueprint or _blueprint_module()
    values: dict[str, Mapping[str, Any]] = {}
    for path, record in selected.ROBINHOOD_DEPLOYMENT_INPUTS.items():
        value = record.value
        kind = type(value).__name__
        if kind == "SourceReference":
            if value.path not in defaults_values:
                raise ManifestError(f"H04_SOURCE_REFERENCE:{path}:{value.path}")
            normalized = copy.deepcopy(defaults_values[value.path])
        elif kind == "SymbolicBinding":
            normalized = {"kind": "symbolic_binding", "name": value.semantic_name}
        elif value == selected.ZERO_ADDRESS:
            normalized = {"kind": "concrete", "raw": "empty(address)"}
        elif isinstance(value, str) and re.fullmatch(r"0x[0-9A-Fa-f]{40}", value):
            normalized = {"kind": "external_fact", "raw": value}
        elif type(value) in (bool, int, str) or isinstance(value, list):
            normalized = {"kind": "concrete", "raw": copy.deepcopy(value)}
        else:
            raise ManifestError(f"H04_BLUEPRINT_VALUE_TYPE:{path}:{kind}")
        _reject_sensitive_or_placeholder_text(normalized)
        values[path] = normalized
    if len(values) != 119:
        raise ManifestError("H04_DEPLOYMENT_SOURCE_CENSUS")
    return values


def derive_assertion_values(
    defaults_values: Mapping[str, Mapping[str, Any]],
    blueprint: Any | None = None,
) -> dict[str, Mapping[str, Any]]:
    selected = blueprint or _blueprint_module()
    invariants = selected.ROBINHOOD_ASSERTION_INVARIANTS
    expected_invariant_keys = {
        "deleverage_launch_cooldown",
        "timelock_base_headroom_blocks",
        "base_blocks_per_robinhood_block",
        "psm_activation_sequence",
        "aapl_cap_formula",
        "aapl_cap_inputs",
        "stock_enabled_vaults",
        "stock_excluded_from_stability_pool",
        "profile_2_lp_ltv",
    }
    if set(invariants) != expected_invariant_keys:
        raise ManifestError("H04_ASSERTION_INVARIANT_CENSUS")

    underscore = defaults_values["Defaults.underscoreRegistry"]
    if underscore != {"kind": "concrete", "raw": "empty(address)"}:
        raise ManifestError("H04_ASSERTION_UNDERSCORE_SEMANTIC")

    arb_sys = selected.ROBINHOOD_ADDRESSES["ARB_SYS"]
    if not isinstance(arb_sys, str) or not re.fullmatch(r"0x[0-9A-Fa-f]{40}", arb_sys):
        raise ManifestError("H04_ASSERTION_ARB_SYS")

    ratio = invariants["base_blocks_per_robinhood_block"]
    base_headroom = invariants["timelock_base_headroom_blocks"]
    if type(ratio) is not int or ratio <= 0 or type(base_headroom) is not int:
        raise ManifestError("H04_ASSERTION_TIMELOCK_FORMULA")

    sequence = tuple(invariants["psm_activation_sequence"])
    if len(sequence) != len(set(sequence)) or {
        "redemption",
        "green_mint",
    } - set(sequence):
        raise ManifestError("H04_ASSERTION_PSM_SEQUENCE")

    active_asset_rows = {
        row
        for row in ASSET_ROWS
        if defaults_values[f"Defaults.assetConfigs[{row}].asset"]["kind"]
        != "omitted"
    }
    if active_asset_rows != set(ACTIVE_ASSET_ROWS):
        raise ManifestError("H04_ASSERTION_ACTIVE_ASSETS")

    values: dict[str, Mapping[str, Any]] = {
        "Deployment.DP-01.lootbox.minUnderscoreSendInterval": {
            "kind": "concrete",
            "raw": selected.ROBINHOOD_CHAIN["blocks_per_minute"] * 60 * 24,
        },
        "Deployment.DP-02.lootbox.underscoreSendInterval": {
            "kind": "concrete",
            "raw": 0,
        },
        "Deployment.DP-03.deleverage.deleverageCooldown": {
            "kind": "concrete",
            "raw": invariants["deleverage_launch_cooldown"],
        },
        "Deployment.DP-04.ledger.actionBlockSourceSemantic": {
            "kind": "concrete",
            "raw": hex(int(arb_sys, 16)),
        },
        "Deployment.DP-06.timelocks.minimumExpirationHeadroom": {
            "kind": "concrete",
            "raw": (base_headroom + ratio - 1) // ratio,
        },
        "Deployment.DP-09.psm.redemptionFirstOrder": {
            "kind": "concrete",
            "raw": sequence.index("redemption") + 1,
        },
        "Deployment.DP-09.psm.greenMintLastOrder": {
            "kind": "concrete",
            "raw": sequence.index("green_mint") + 1,
        },
        "Deployment.DP-10.aapl.capFormula": {
            "kind": "derived",
            "formula": invariants["aapl_cap_formula"],
            "inputs": list(invariants["aapl_cap_inputs"]),
        },
        "Deployment.DP-11.stock.enabledVaultCount": {
            "kind": "concrete",
            "raw": len(tuple(invariants["stock_enabled_vaults"])),
        },
        "Deployment.DP-12.launchGraph.assetCount": {
            "kind": "concrete",
            "raw": len(active_asset_rows),
        },
        "Deployment.DP-13.stock.excludedFromStabilityPool": {
            "kind": "concrete",
            "raw": invariants["stock_excluded_from_stability_pool"],
        },
        "Deployment.DP-14.lp.ltv": {
            "kind": "concrete",
            "raw": invariants["profile_2_lp_ltv"],
        },
    }
    _validate_assertion_path_census(tuple(values))
    for value in values.values():
        _validate_value(value)
    return values


def _validate_census(ledger: Mapping[str, Any]) -> None:
    records = ledger["parameters"]
    by_kind = Counter(record["destination"]["kind"] for record in records)
    if by_kind != Counter(defaults_field=272, deployment_input=119, assertion=12):
        raise ManifestError(f"H04_PARTITION:{dict(by_kind)}")
    defaults = [record for record in records if record["destination"]["kind"] == "defaults_field"]
    statuses = Counter(record["status"] for record in defaults)
    if statuses != Counter(approved=192, external_fact=3, blocked=7, omitted=70):
        raise ManifestError(f"H04_DEFAULT_STATUS_PARTITION:{dict(statuses)}")
    active_leaves = [
        record
        for record in defaults
        if record["destination"]["path"].startswith("Defaults.assetConfigs[")
        and record["status"] != "omitted"
    ]
    active_rows = {
        record["destination"]["path"].split("[", 1)[1].split("]", 1)[0]
        for record in active_leaves
    }
    if len(active_leaves) != 124 or active_rows != set(ACTIVE_ASSET_ROWS):
        raise ManifestError("H04_ACTIVE_ASSET_PARTITION")


def derive_ledger(
    tracked: Mapping[str, Any],
    *,
    defaults_path: Path = DEFAULTS_PATH,
    blueprint: Any | None = None,
) -> dict[str, Any]:
    _validate_shape(tracked, allow_legacy=True)
    expected = copy.deepcopy(tracked)
    expected["schema_version"] = SCHEMA_VERSION

    # The selected seven-argument authority removes one 31-field Steakhouse
    # asset row and one two-field priority-liquidation row. Preserve every
    # surviving record's stable ID and review metadata; gaps are intentional
    # tombstones for the removed historical destinations.
    selected = blueprint or _blueprint_module()
    retained_paths = (
        set(canonical_default_paths())
        | set(selected.ROBINHOOD_DEPLOYMENT_INPUTS)
        | {
            record["destination"]["path"]
            for record in tracked["parameters"]
            if record["destination"]["kind"] == "assertion"
        }
    )
    retained_records = []
    for record in expected["parameters"]:
        if record["destination"]["path"] not in retained_paths:
            continue
        retained_records.append(record)
    expected["parameters"] = retained_records
    retained_ids = {record["id"] for record in retained_records}
    for schedule in expected["binding_schedules"]:
        schedule["records"] = [
            record_id
            for record_id in schedule["records"]
            if record_id in retained_ids
        ]

    for record in expected["parameters"]:
        record.pop("generated_repr", None)

    deployment_paths = {
        record["destination"]["path"]
        for record in tracked["parameters"]
        if record["destination"]["kind"] == "deployment_input"
    }
    if set(selected.ROBINHOOD_DEPLOYMENT_INPUTS) != deployment_paths:
        raise ManifestError("H04_BLUEPRINT_DEPLOYMENT_INPUT_CENSUS")
    defaults_values = extract_defaults_values(defaults_path, blueprint=selected)
    deployment_values = extract_deployment_values(defaults_values, blueprint=selected)
    assertion_values = derive_assertion_values(defaults_values, blueprint=selected)
    for record in expected["parameters"]:
        destination = record["destination"]
        path = destination["path"]
        if destination["kind"] == "defaults_field":
            record["value"] = copy.deepcopy(defaults_values[path])
        elif destination["kind"] == "deployment_input":
            source_input = selected.ROBINHOOD_DEPLOYMENT_INPUTS[path]
            if record["status"] != source_input.disposition:
                raise ManifestError(
                    f"H04_DISPOSITION_DRIFT:{path}:ledger={record['status']}:blueprint={source_input.disposition}"
                )
            record["value"] = copy.deepcopy(deployment_values[path])
        elif destination["kind"] == "assertion":
            record["value"] = copy.deepcopy(assertion_values[path])
            if path == "Deployment.DP-13.stock.excludedFromStabilityPool":
                record["zero_semantics"] = {
                    "kind": "not_zero",
                    "explanation": (
                        "Approved explicit Stock exclusion; false, absence, "
                        "and omission are distinct."
                    ),
                }
    _validate_shape(expected, allow_legacy=False)
    _validate_census(expected)
    return expected


def canonical_json(ledger: Mapping[str, Any]) -> bytes:
    return (json.dumps(ledger, indent=2, sort_keys=True) + "\n").encode("utf-8")


def ledger_sha256(ledger: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(ledger)).hexdigest()


def _first_difference(actual: Any, expected: Any, path: str = "$") -> str | None:
    if type(actual) is not type(expected):
        return f"{path}:type:{type(actual).__name__}!={type(expected).__name__}"
    if isinstance(actual, Mapping):
        if set(actual) != set(expected):
            return f"{path}:keys:{sorted(actual)}!={sorted(expected)}"
        for key in expected:
            difference = _first_difference(actual[key], expected[key], f"{path}.{key}")
            if difference:
                return difference
        return None
    if isinstance(actual, list):
        if len(actual) != len(expected):
            return f"{path}:length:{len(actual)}!={len(expected)}"
        for index, (left, right) in enumerate(zip(actual, expected, strict=True)):
            difference = _first_difference(left, right, f"{path}[{index}]")
            if difference:
                return difference
        return None
    if actual != expected:
        return f"{path}:{actual!r}!={expected!r}"
    return None


def deployment_readiness(blueprint: Any | None = None) -> tuple[bool, tuple[str, ...]]:
    selected = blueprint or _blueprint_module()
    blockers: set[str] = set()
    curve_address_names = {
        "CURVE_ADDRESS_PROVIDER",
        "CURVE_META_REGISTRY",
        "CURVE_TRICRYPTO_NG_FACTORY",
        "CURVE_STABLESWAP_NG_FACTORY",
        "CURVE_TWOCRYPTO_NG_FACTORY",
        "GREEN_USDG_CURVE_POOL",
    }
    for name, value in selected.ROBINHOOD_ADDRESSES.items():
        status = selected.ROBINHOOD_ADDRESS_STATUS[name]
        # Curve rows below retain richer authority and resolution-state types.
        if name in curve_address_names:
            continue
        if type(value).__name__ == "SymbolicBinding" or status.endswith("unresolved"):
            blockers.add(f"address:{name}:unresolved")
        if status.endswith("unverified"):
            blockers.add(f"address:{name}:unverified")
    for path, record in selected.ROBINHOOD_DEPLOYMENT_INPUTS.items():
        if type(record.value).__name__ == "SymbolicBinding":
            blockers.add(f"input:{path}:unresolved")
    for row in selected.ROBINHOOD_CURVE_LAUNCH_INPUTS:
        if row.resolution_state in selected.ROBINHOOD_CURVE_BLOCKING_STATES:
            blockers.add(
                "curve:"
                f"{row.authority_class}:{row.input_id}:{row.resolution_state}"
            )
    return (not blockers, tuple(sorted(blockers)))


def atomic_write_ledger(path: Path, data: bytes) -> None:
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=".robinhood-parameters.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def sync_ledger(path: Path = LEDGER_PATH) -> str:
    tracked = load_ledger(path, allow_legacy=True)
    expected = derive_ledger(tracked)
    data = canonical_json(expected)
    atomic_write_ledger(path, data)
    return hashlib.sha256(data).hexdigest()


def check_ledger(
    path: Path = LEDGER_PATH,
    *,
    defaults_path: Path = DEFAULTS_PATH,
    blueprint: Any | None = None,
) -> str:
    tracked = load_ledger(path)
    expected = derive_ledger(
        tracked,
        defaults_path=defaults_path,
        blueprint=blueprint,
    )
    actual_data = path.read_bytes()
    expected_data = canonical_json(expected)
    if actual_data != expected_data:
        difference = _first_difference(tracked, expected) or "$:noncanonical-bytes"
        raise ManifestError(f"H04_LEDGER_DRIFT:{difference}")
    return hashlib.sha256(expected_data).hexdigest()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Synchronize the derived Robinhood parameter ledger"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="compile sources and compare the derived ledger without repository writes",
    )
    args = parser.parse_args(argv)
    try:
        if args.check:
            identity = check_ledger()
            ready, blockers = deployment_readiness()
            print(
                f"H04_OK sha256={identity} configuration_consistent=true "
                f"deployment_ready={str(ready).lower()} blockers={len(blockers)}"
            )
        else:
            identity = sync_ledger()
            print(f"H04_SYNCED sha256={identity}")
        return 0
    except ManifestError as exc:
        print(f"H04_ERROR: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
