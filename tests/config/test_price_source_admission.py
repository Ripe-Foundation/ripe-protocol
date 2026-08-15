from __future__ import annotations

import copy
from dataclasses import replace
import hashlib
import json
import re
from pathlib import Path

import boa
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
SGREEN = "0x0000000000000000000000000000000000000007"
ZERO_ADDRESS = "0x" + "0" * 40


def _live_topology() -> admission.LivePriceSourceTopology:
    return admission.LivePriceSourceTopology(
        next_registry_id=3,
        registry_addresses=(CHAINLINK, CURVE, ZERO_ADDRESS),
        priority_source_ids=(1, 2),
        curve_priced_assets=(GREEN,),
        curve_routes=(
            admission.LiveCurveRoute(
                feed_asset=GREEN,
                pool=GREEN_USDG_POOL,
                num_underlying=2,
                underlyings=(USDG, GREEN, ZERO_ADDRESS, ZERO_ADDRESS),
                underlying_price_source_ids=((USDG, (1,)),),
            ),
        ),
        curve_green_address=GREEN,
        savings_green_address=SGREEN,
        savings_green_has_feed=True,
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
        selected_savings_green_address=SGREEN,
        selected_usdg_address=USDG,
        selected_curve_pool_address=GREEN_USDG_POOL,
        selected_usdg_chainlink_feed=USDG_FEED,
    )


def test_selected_manifest_and_contract_allowances_are_exact():
    value = admission.load_manifest()
    source = (ROOT / "contracts" / "registries" / "PriceDesk.vy").read_text()
    contract_allowances = {
        "get_price_and_has_feed": int(
            re.search(
                r"PRICE_SOURCE_PRICE_GAS: constant\(uint256\) = ([\d_]+)", source
            )[1].replace("_", "")
        ),
        "has_price_feed": int(
            re.search(
                r"PRICE_SOURCE_HAS_FEED_GAS: constant\(uint256\) = ([\d_]+)", source
            )[1].replace("_", "")
        ),
        "add_price_snapshot": int(
            re.search(
                r"PRICE_SOURCE_SNAPSHOT_GAS: constant\(uint256\) = ([\d_]+)", source
            )[1].replace("_", "")
        ),
    }
    assert contract_allowances == value["source_allowances"]

    defaults = (ROOT / "contracts" / "config" / "DefaultsRobinhood.vy").read_text()
    stab_vault = (
        ROOT / "contracts" / "vaults" / "modules" / "StabVault.vy"
    ).read_text()
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
    assert value["qualification_controls"] == admission.QUALIFICATION_CONTROLS


def test_exact_governed_price_desk_runtime_passes_and_drift_fails():
    production_hq = "0xD4e82AE1De673bba3B53386A2D2C630AE6630940"
    seed_source = "# @version 0.4.3\n\n@deploy\ndef __init__():\n    pass\n"
    for label, seed_address in (
        ("green", GREEN),
        ("sgreen", SGREEN),
        ("ripe", USDG),
    ):
        boa.loads(
            seed_source,
            name=f"governed_price_desk_{label}_seed",
            override_address=seed_address,
        )
    boa.load(
        "contracts/registries/RipeHq.vy",
        GREEN,
        SGREEN,
        USDG,
        "0xe488a42D33b3Af5d3E5Cd5680938d8369716D1bf",
        3_600,
        50_400,
        3_600,
        50_400,
        override_address=production_hq,
        name="governed_price_desk_admission_hq",
    )
    governed = boa.load(
        "contracts/registries/PriceDesk.vy",
        production_hq,
        ZERO_ADDRESS,
        "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        3_600,
        50_400,
        name="governed_price_desk_admission_runtime",
    )
    runtime = bytes(boa.env.get_code(governed.address))
    admission.require_hardened_price_desk_runtime(runtime)
    assert len(runtime) == admission.GOVERNED_PRICE_DESK_RUNTIME_SIZE

    drifted = bytearray(runtime)
    drifted[-1] ^= 1
    with pytest.raises(
        admission.PriceSourceAdmissionError,
        match="governed hardened artifact",
    ):
        admission.require_hardened_price_desk_runtime(bytes(drifted))

    manifest = json.loads(
        (
            ROOT / "migration_history/robinhood-mainnet/v1/current-manifest.json"
        ).read_text()
    )
    old_source = manifest["contracts"]["PriceDesk"]["solc_json"]["sources"][
        "contracts/registries/PriceDesk.vy"
    ]["content"]
    old_price_desk = boa.loads(
        old_source,
        production_hq,
        ZERO_ADDRESS,
        "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        3_600,
        50_400,
        filename="contracts/registries/PriceDesk.vy",
        name="recorded_pre_hardening_price_desk_runtime",
    )
    with pytest.raises(
        admission.PriceSourceAdmissionError,
        match="governed hardened artifact",
    ):
        admission.require_hardened_price_desk_runtime(
            bytes(boa.env.get_code(old_price_desk.address))
        )


def test_robinhood_manifest_records_pre_hardening_price_desk_source():
    deployed = json.loads(
        (
            ROOT / "migration_history/robinhood-mainnet/v1/current-manifest.json"
        ).read_text()
    )
    embedded = deployed["contracts"]["PriceDesk"]["solc_json"]["sources"][
        "contracts/registries/PriceDesk.vy"
    ]["content"].encode()
    current = (ROOT / "contracts/registries/PriceDesk.vy").read_bytes()
    assert hashlib.sha256(embedded).hexdigest() == (
        "7611139b85f93d042fcf7ddf964052909166b4bd98bdd4b7ee8c685c54641d2a"
    )
    assert hashlib.sha256(current).hexdigest() == (
        "7fd7e8eedd883a10ee7a225cb666896324d7b9b47de3a136175f62e00267561c"
    )
    assert embedded != current


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
            lambda value: replace(value, curve_green_address=USDG),
            "Curve GREEN binding",
        ),
        (
            lambda value: replace(
                value,
                registry_addresses=(CHAINLINK, USDG, ZERO_ADDRESS),
            ),
            "registered-source count, address, or slot order",
        ),
        (
            lambda value: replace(
                value,
                curve_routes=(replace(value.curve_routes[0], pool=USDG_FEED),),
            ),
            "GREEN Curve pool",
        ),
        (
            lambda value: replace(
                value,
                curve_routes=(
                    replace(
                        value.curve_routes[0],
                        num_underlying=3,
                        underlyings=(USDG, GREEN, USDG_FEED, ZERO_ADDRESS),
                    ),
                ),
            ),
            "Curve underlying count or list",
        ),
        (
            lambda value: replace(
                value,
                curve_routes=(
                    replace(
                        value.curve_routes[0],
                        underlying_price_source_ids=((USDG, (3,)),),
                    ),
                ),
            ),
            "underlying resolution is not Chainlink-only",
        ),
        (
            lambda value: replace(
                value,
                curve_priced_assets=(GREEN, USDG),
                curve_routes=(
                    *value.curve_routes,
                    admission.LiveCurveRoute(
                        feed_asset=USDG,
                        pool=GREEN_USDG_POOL,
                        num_underlying=1,
                        underlyings=(USDG, ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS),
                        underlying_price_source_ids=(),
                    ),
                ),
            ),
            "Curve priced-asset set",
        ),
        (
            lambda value: replace(value, savings_green_has_feed=False),
            "derived sGREEN Curve route",
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


def test_bluechip_migration_binds_runtime_and_emits_no_activation_calldata():
    source = (
        ROOT
        / "migrations"
        / "robinhood-mainnet"
        / "0011_BlueChipYieldPricesCandidate.py"
    ).read_text()
    assert "require_active_hardened_price_desk(migration, hq, price_desk)" in source
    assert "require_live_topology(migration, price_desk)" in source
    assert "migration.deploy(" not in source
    assert "migration.execute(" not in source
    assert "promote_candidate" not in source
    assert "_add_calldata" not in source
    assert "ACTIVATION_DEFERRED" in source

    observer = (ROOT / "scripts" / "utils" / "price_source_preflight.py").read_text()
    assert "curve.getPricedAssets()" in observer
    assert "for feed_asset in priced_assets" in observer
    assert "curve.curveConfig(feed_asset)" in observer
    assert "source.hasPriceFeed(underlying)" in observer
    assert "curve.hasPriceFeed(savings_green)" in observer
