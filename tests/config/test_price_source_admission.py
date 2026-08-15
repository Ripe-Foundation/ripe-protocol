from __future__ import annotations

import copy
from dataclasses import replace
import json
import re
from pathlib import Path

import pytest

from config import price_source_admission as admission


ROOT = Path(__file__).resolve().parents[2]


def _manifest() -> dict:
    return json.loads(admission.DEFAULT_MANIFEST.read_text())


CHAINLINK = "0x0000000000000000000000000000000000000001"
CURVE = "0x0000000000000000000000000000000000000002"
GREEN = "0x0000000000000000000000000000000000000003"
USDG = "0x0000000000000000000000000000000000000004"
GREEN_USDG_POOL = "0x0000000000000000000000000000000000000005"
USDG_FEED = "0x0000000000000000000000000000000000000006"
ZERO_ADDRESS = "0x" + "0" * 40


def _live_topology() -> admission.LivePriceSourceTopology:
    return admission.LivePriceSourceTopology(
        next_registry_id=3,
        registry_addresses=(CHAINLINK, CURVE, ZERO_ADDRESS),
        priority_source_ids=(1, 2),
        curve_feed_asset=GREEN,
        curve_pool=GREEN_USDG_POOL,
        curve_num_underlying=2,
        curve_underlyings=(USDG, GREEN, ZERO_ADDRESS, ZERO_ADDRESS),
        underlying_price_source_ids=((USDG, (1,)),),
        chainlink_usdg_feed=USDG_FEED,
        max_vaults_per_user=5,
        max_assets_per_vault=15,
    )


def _validate_live(observed: admission.LivePriceSourceTopology) -> None:
    admission.require_selected_live_topology(
        observed=observed,
        selected_chainlink_address=CHAINLINK,
        selected_curve_address=CURVE,
        selected_green_address=GREEN,
        selected_usdg_address=USDG,
        selected_curve_pool_address=GREEN_USDG_POOL,
        selected_usdg_chainlink_feed=USDG_FEED,
    )


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


def test_live_topology_preflight_accepts_exact_observed_state():
    _validate_live(_live_topology())
    admission.require_selected_bluechip_slot_3_candidate(
        candidate_address="0x0000000000000000000000000000000000000007",
        observed_slot_3_address=ZERO_ADDRESS,
    )


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        (
            lambda value: replace(value, priority_source_ids=(2, 1)),
            "priority source order",
        ),
        (
            lambda value: replace(value, next_registry_id=4),
            "registered-source count, address, or slot order",
        ),
        (
            lambda value: replace(
                value,
                registry_addresses=(CHAINLINK, USDG, ZERO_ADDRESS),
            ),
            "registered-source count, address, or slot order",
        ),
        (
            lambda value: replace(value, curve_pool=USDG_FEED),
            "GREEN Curve pool",
        ),
        (
            lambda value: replace(
                value,
                curve_num_underlying=3,
                curve_underlyings=(USDG, GREEN, USDG_FEED, ZERO_ADDRESS),
            ),
            "Curve underlying count or list",
        ),
        (
            lambda value: replace(
                value,
                underlying_price_source_ids=((USDG, (3,)),),
            ),
            "underlying resolution is not Chainlink-only",
        ),
        (
            lambda value: replace(value, chainlink_usdg_feed=ZERO_ADDRESS),
            "USDG Chainlink feed is missing or unexpected",
        ),
        (
            lambda value: replace(value, max_assets_per_vault=16),
            "vault or asset envelope",
        ),
    ),
)
def test_live_topology_preflight_rejects_observed_drift(mutation, message):
    with pytest.raises(admission.PriceSourceAdmissionError, match=message):
        _validate_live(mutation(_live_topology()))


def test_bluechip_migration_binds_live_slots_and_preflights_before_calldata():
    source = (
        ROOT
        / "migrations"
        / "robinhood-mainnet"
        / "0011_BlueChipYieldPricesCandidate.py"
    ).read_text()
    assert "mission_control.getPriorityPriceSourceIds()" in source
    assert "curve.curveConfig(green)" in source
    assert "chainlink.feedConfig(usdg)" in source
    assert "source.hasPriceFeed(usdg)" in source
    assert "_require_live_topology(migration, price_desk, blue_chip)" in source
    assert "mission_control.genConfig()" in source
    preflights = [
        match.start()
        for match in re.finditer(
            r"_require_live_topology\(migration, price_desk(?:, blue_chip)?\)",
            source,
        )
    ]
    deploy = source.index("blue_chip = migration.deploy(")
    calldata = source.index("start, confirm = _add_calldata(")
    assert len(preflights) == 2
    assert preflights[0] < deploy < preflights[1] < calldata
