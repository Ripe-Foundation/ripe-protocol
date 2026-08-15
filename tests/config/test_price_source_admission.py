from __future__ import annotations

import copy
import json
import re
from pathlib import Path

import pytest

from config import price_source_admission as admission


ROOT = Path(__file__).resolve().parents[2]


def _manifest() -> dict:
    return json.loads(admission.DEFAULT_MANIFEST.read_text())


def test_selected_manifest_and_contract_allowances_are_exact():
    value = admission.load_manifest()
    source = (ROOT / "contracts" / "registries" / "PriceDesk.vy").read_text()
    contract_allowances = {
        "get_price_and_has_feed": int(
            re.search(r"PRICE_SOURCE_PRICE_GAS: constant\(uint256\) = ([\d_]+)", source)[1].replace("_", "")
        ),
        "has_price_feed": int(
            re.search(r"PRICE_SOURCE_HAS_FEED_GAS: constant\(uint256\) = ([\d_]+)", source)[1].replace("_", "")
        ),
        "add_price_snapshot": int(
            re.search(r"PRICE_SOURCE_SNAPSHOT_GAS: constant\(uint256\) = ([\d_]+)", source)[1].replace("_", "")
        ),
    }
    assert contract_allowances == value["source_allowances"]

    defaults = (ROOT / "contracts" / "config" / "DefaultsRobinhood.vy").read_text()
    stab_vault = (ROOT / "contracts" / "vaults" / "modules" / "StabVault.vy").read_text()
    envelope = value["qualification_envelope"]
    assert envelope["max_vaults_per_user"] == int(
        re.search(r"perUserMaxVaults = (\d+)", defaults)[1]
    )
    assert envelope["max_assets_per_vault"] == int(
        re.search(r"perUserMaxAssetsPerVault = (\d+)", defaults)[1]
    )
    assert envelope["max_user_valuation_positions"] == (
        envelope["max_vaults_per_user"] * envelope["max_assets_per_vault"]
    )
    assert envelope["max_active_claim_assets"] == int(
        re.search(
            r"MAX_ACTIVE_CLAIM_ASSETS: constant\(uint256\) = (\d+)",
            stab_vault,
        )[1]
    )
    assert envelope["max_claim_maintenance_batch"] == int(
        re.search(
            r"MAX_CLAIM_ASSET_MAINTENANCE: constant\(uint256\) = (\d+)",
            stab_vault,
        )[1]
    )


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        (
            lambda value: value["selected_registry"].append(
                {
                    "id": 4,
                    "semantic": "PythPrices",
                    "source_path": "contracts/priceSources/PythPrices.vy",
                }
            ),
            "registered-source list/order",
        ),
        (
            lambda value: value.update(priority_source_ids=[2, 1]),
            "priority source order",
        ),
        (
            lambda value: value["supported_curve_routes"][0]["underlyings"][1].update(
                resolution="BlueChipYieldPrices"
            ),
            "Curve feed or underlying graph",
        ),
        (
            lambda value: value["qualification_envelope"].update(
                max_user_valuation_positions=76
            ),
            "vault, asset, snapshot, Curve, or source-count envelope",
        ),
    ),
)
def test_manifest_rejects_unqualified_growth_and_topology(mutation, message):
    value = copy.deepcopy(_manifest())
    mutation(value)
    with pytest.raises(admission.PriceSourceAdmissionError, match=message):
        admission.validate_manifest(value)


def test_safe_action_preflight_rejects_curve_over_snapshot_source():
    route = (
        "GREEN",
        "GREEN/USDG",
        (("GREEN", "target_asset"), ("USDG", "BlueChipYieldPrices")),
    )
    with pytest.raises(
        admission.PriceSourceAdmissionError,
        match="Curve-over-snapshot",
    ):
        admission.require_selected_bluechip_slot_3_plan(
            registered_sources=(
                "ChainlinkPrices",
                "CurvePrices",
                "BlueChipYieldPrices",
            ),
            priority_source_ids=(1, 2),
            curve_routes=(route,),
            candidate_address="0x0000000000000000000000000000000000000001",
        )


def test_bluechip_migration_binds_live_slots_and_preflights_before_calldata():
    source = (
        ROOT
        / "migrations"
        / "robinhood-mainnet"
        / "0011_BlueChipYieldPricesCandidate.py"
    ).read_text()
    assert 'price_desk.getAddr(1) == migration.get_address("ChainlinkPrices")' in source
    assert 'price_desk.getAddr(2) == migration.get_address("CurvePrices")' in source
    assert source.index("require_selected_bluechip_slot_3_plan(") < source.index(
        "start, confirm = _add_calldata("
    )
