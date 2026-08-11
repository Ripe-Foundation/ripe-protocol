from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from config.robinhood_blueprint import (
    ROBINHOOD_BLUEPRINT,
    Blocker,
    Disposition,
    LifecyclePhase,
    RegistryDomain,
    RegistryIdAuthority,
    RelationPhase,
    RobinhoodBlueprintError,
    SourcePathKind,
    SourcePathState,
    SurfaceKind,
    SurfaceRecord,
    get_component,
    get_promotion,
    get_symbolic_input,
    validate_blueprint,
)
from scripts.utils.deployment_assertions import (
    blueprint_policy,
    blueprint_registry_map as registry_map,
)


ASSERTION_IDS = {
    "NEG-016",
    "NEG-017",
    "NEG-018",
    "NEG-019",
    "NEG-020",
    "NEG-021",
    "NEG-022",
    "NEG-023",
    "NEG-024",
    "NEG-025",
    "NEG-031",
    "NEG-033",
    "NEG-034",
    "NEG-035",
    "NEG-036",
    "NEG-037",
    "NEG-H03-GLOBAL-MINT-SEQUENCE", "NEG-H03-CURVE-HIGHER-POWERS", "NEG-H03-CURVE-USDG-RECURSION",
    "NEG-H03-LP-ORDINARY-ONLY",
    "NEG-H03-LP-ZERO-LTV",
    "NEG-H03-PSM-REDEEM-FIRST",
    "NEG-H03-PSM-MINT-LAST",
    "NEG-H03-STOCK-REWARD-DISABLED",
    "NEG-H03-TELLER-EXACT-RECEIPT",
    "NEG-H03-USDG-ROUTE",
}
ROOT = Path(__file__).resolve().parents[2]


def surface_map(blueprint=ROBINHOOD_BLUEPRINT):
    return {
        surface.surface_id: surface
        for component in blueprint.components
        for surface in component.surfaces
    }


def relation_map(blueprint=ROBINHOOD_BLUEPRINT):
    return {
        relation.relation_id: (component.component_id, relation)
        for component in blueprint.components
        for relation in component.relations
    }


def replace_component(component_id, **changes):
    return replace(
        ROBINHOOD_BLUEPRINT,
        components=tuple(
            replace(component, **changes)
            if component.component_id == component_id
            else component
            for component in ROBINHOOD_BLUEPRINT.components
        ),
    )


def replace_surface(surface_id, **changes):
    for component in ROBINHOOD_BLUEPRINT.components:
        if any(surface.surface_id == surface_id for surface in component.surfaces):
            return replace_component(
                component.component_id,
                surfaces=tuple(
                    replace(surface, **changes)
                    if surface.surface_id == surface_id
                    else surface
                    for surface in component.surfaces
                ),
            )
    raise AssertionError(surface_id)


def replace_registry(domain, registry_id, **changes):
    row = registry_map()[(domain, registry_id)]
    component = get_component(row.component_id)
    return replace_component(
        component.component_id,
        registry_expectations=tuple(
            replace(item, **changes)
            if item.domain is domain and item.registry_id == registry_id
            else item
            for item in component.registry_expectations
        ),
    )


def remove_relation(relation_id):
    source_component, _ = relation_map()[relation_id]
    component = get_component(source_component)
    return replace_component(
        source_component,
        relations=tuple(
            relation
            for relation in component.relations
            if relation.relation_id != relation_id
        ),
    )


def assert_code(code, candidate):
    with pytest.raises(RobinhoodBlueprintError) as error:
        validate_blueprint(candidate)
    assert error.value.code == code


def test_exact_26_assertion_ids_are_embedded_in_real_records():
    used = {
        assertion
        for component in ROBINHOOD_BLUEPRINT.components
        for assertion in component.negative_assertion_ids
    }
    assert used == ASSERTION_IDS


def test_omitted_component_has_no_surface():
    omitted = tuple(
        component
        for component in ROBINHOOD_BLUEPRINT.components
        if component.deployment is Disposition.OMITTED
    )
    assert len(omitted) == 14
    assert all(component.surfaces == () for component in omitted)

    injected = SurfaceRecord(
        surface_id="S-007-INJECTED",
        component_id="CM-007",
        kind=SurfaceKind.ARTIFACT,
        semantic_meaning="synthetic artifact on omitted component",
        disposition=Disposition.REQUIRED,
        lifecycle_phase=LifecyclePhase.DEPLOYED_INITIAL_VALUE,
        blocker_ids=(),
        assertion_ids=("NEG-016",),
    )
    assert_code(
        "H03_OMISSION_SURFACE",
        replace_component("CM-007", surfaces=(injected,)),
    )


def test_zero_is_not_placeholder():
    legitimate_zero_surfaces = {
        "S-014-COOLDOWN",
        "S-024-LP-ZERO-LTV",
        "S-044-COOLDOWN",
    }
    assert legitimate_zero_surfaces <= set(surface_map())
    assert all(
        "zero" in surface_map()[surface_id].semantic_meaning.lower()
        or "ltv=0" in surface_map()[surface_id].semantic_meaning.lower()
        for surface_id in legitimate_zero_surfaces
    )

    zero_address = "0x" + ("0" * 40)
    symbolic = ROBINHOOD_BLUEPRINT.symbolic_inputs[0]
    candidate = replace(
        ROBINHOOD_BLUEPRINT,
        symbolic_inputs=(
            replace(symbolic, semantic_class=zero_address),
            *ROBINHOOD_BLUEPRINT.symbolic_inputs[1:],
        ),
    )
    assert_code("H03_ADDRESS_LITERAL", candidate)


def test_psm_mint_disabled():
    surfaces = surface_map()
    assert surfaces["S-048-MINT"].disposition is Disposition.DISABLED
    assert surfaces["S-048-HQ-GREEN-CAP"].disposition is Disposition.BLOCKED
    assert surfaces["S-048-MINT"].lifecycle_phase is (
        LifecyclePhase.PRE_ACTIVATION_CONFIGURATION
    )
    assert_code(
        "H03_TRACK8_GATE",
        replace_surface("S-048-MINT", disposition=Disposition.REQUIRED),
    )


def test_psm_redeem_disabled():
    redeem = surface_map()["S-048-REDEEM"]
    assert redeem.disposition is Disposition.DISABLED
    assert redeem.assertion_ids == (
        "NEG-019",
        "NEG-H03-PSM-REDEEM-FIRST",
    )
    assert_code(
        "H03_TRACK8_GATE",
        replace_surface("S-048-REDEEM", disposition=Disposition.REQUIRED),
    )


def test_psm_no_auto_deposit_or_yield():
    surfaces = surface_map()
    auto_deposit = surfaces["S-048-AUTO-DEPOSIT"]
    assert auto_deposit.disposition is Disposition.DISABLED
    assert "source deploys with auto-deposit True" in (
        auto_deposit.semantic_meaning
    )
    assert "setting it to False" in auto_deposit.semantic_meaning
    for surface_id in (
        "S-048-YIELD",
        "S-048-APPROVAL",
    ):
        assert surfaces[surface_id].disposition is Disposition.DISABLED
    assert surfaces["S-048-UNDERSCORE"].disposition is Disposition.OMITTED
    assert_code(
        "H03_TRACK8_GATE",
        replace_surface("S-048-AUTO-DEPOSIT", disposition=Disposition.REQUIRED),
    )


def test_stock_asset_not_enabled_before_track8():
    surfaces = surface_map()
    stock_ids = {
        surface_id
        for surface_id, surface in surfaces.items()
        if "Stock" in surface.semantic_meaning
        or "AAPL" in surface.semantic_meaning
    }
    assert stock_ids
    assert not any(
        surfaces[surface_id].disposition is Disposition.REQUIRED
        for surface_id in stock_ids
    )
    track8_blockers = {f"B-T8-M{value}" for value in range(1, 6)}
    assert track8_blockers <= {
        blocker.blocker_id for blocker in ROBINHOOD_BLUEPRINT.blockers
    }
    assert_code(
        "H03_TRACK8_GATE",
        replace_surface(
            "S-034-AAPL-TRUSTED",
            disposition=Disposition.REQUIRED,
        ),
    )


def test_stock_credit_redeem_false():
    stock_redeem = surface_map()["S-043-STOCK-REDEEM"]
    assert stock_redeem.disposition is Disposition.DISABLED
    assert stock_redeem.lifecycle_phase is (
        LifecyclePhase.DEPLOYED_INITIAL_VALUE
    )
    assert_code(
        "H03_TRACK8_GATE",
        replace_surface(
            "S-043-STOCK-REDEEM",
            disposition=Disposition.REQUIRED,
        ),
    )


def test_stock_stability_swap_false():
    surfaces = surface_map()
    for surface_id in (
        "S-022-STOCK-CUSTODY",
        "S-022-STOCK-SWAP",
    ):
        assert surfaces[surface_id].disposition is Disposition.DISABLED
    assert_code(
        "H03_TRACK8_GATE",
        replace_surface(
            "S-022-STOCK-SWAP",
            disposition=Disposition.REQUIRED,
        ),
    )


def test_unselected_oracles_are_unreachable_and_bluechip_source_is_selected():
    omitted_oracle_components = {
        "CM-019",
        "CM-020",
        "CM-039",
        "CM-040",
        "CM-041",
        "CM-050",
    }
    assert all(
        get_component(component_id).deployment is Disposition.OMITTED
        for component_id in omitted_oracle_components
    )
    bluechip = get_component("CM-018")
    assert bluechip.deployment is Disposition.REQUIRED
    assert bluechip.blocker_ids == ("B-P1-EXTERNAL-VERIFY",)
    topology = registry_map()
    policy = blueprint_policy()
    assert [
        topology[(RegistryDomain.PRICE_DESK, value)].semantic_name
        for value in range(2, 6)
    ] == ["Curve", "BlueChipYield", "Pyth", "Stork"]
    assert topology[(RegistryDomain.PRICE_DESK, 3)].disposition is (
        Disposition.REQUIRED
    )
    assert all(
        topology[(RegistryDomain.PRICE_DESK, value)].disposition
        is Disposition.OMITTED
        for value in (4, 5)
    )
    assert topology[(RegistryDomain.PRICE_DESK, 2)].disposition is Disposition.REQUIRED
    assert {
        key for key in policy.reserved_registries if key[0] == "price_desk"
    } == {("price_desk", value) for value in (4, 5)}
    assert ("price_desk", 3) in policy.required_registries


def test_ccip_capability_withheld_until_complete():
    surfaces = surface_map()
    promotion = get_promotion("P-CCIP-SEVEN-DAY")
    assert promotion.surface_ids == (
        "S-001-CCIP-CAP",
        "S-002-CCIP-CAP",
        "S-051-ARTIFACT",
        "S-052-ARTIFACT",
        "S-053-REGISTRATION",
        "S-058-TOOLCHAIN",
    )
    assert promotion.disposition is Disposition.DEFERRED
    for surface_id in ("S-001-CCIP-CAP", "S-002-CCIP-CAP"):
        assert surfaces[surface_id].disposition is Disposition.DISABLED
        assert surfaces[surface_id].lifecycle_phase is (
            LifecyclePhase.WITHIN_SEVEN_DAY_SEPARATELY_REVIEWED_CCIP_PROMOTION
        )
        assert "continuously" in surfaces[surface_id].semantic_meaning
    assert_code(
        "H03_PROMOTION_SET",
        replace(
            ROBINHOOD_BLUEPRINT,
                promotions=(
                    replace(
                        promotion,
                        surface_ids=promotion.surface_ids[:-1],
                    ),
                ),
        ),
    )


def test_registry_semantic_ids_cannot_shift():
    topology = registry_map()
    assert topology[(RegistryDomain.RIPE_HQ, 23)].semantic_name == (
        "RIPE CCIP BurnMint pool"
    )
    assert topology[(RegistryDomain.RIPE_HQ, 24)].semantic_name == (
        "GREEN CCIP BurnMint pool"
    )
    assert all(
        topology[(RegistryDomain.RIPE_HQ, value)].authority
        is RegistryIdAuthority.SOURCE_HARD_CODED
        for value in range(1, 23)
    )
    component = get_component("CM-001")
    row = component.registry_expectations[0]
    assert_code(
        "H03_REGISTRY_TOPOLOGY",
        replace_component(
            "CM-001",
            registry_expectations=(replace(row, registry_id=2),),
        ),
    )


@pytest.mark.parametrize(
    ("domain", "registry_id"),
    tuple(
        (item.domain, item.registry_id)
        for component in ROBINHOOD_BLUEPRINT.components
        for item in component.registry_expectations
    ),
)
def test_every_registry_mapping_fails_closed_on_semantic_reuse(
    domain, registry_id
):
    row = registry_map()[(domain, registry_id)]
    assert_code(
        "H03_REGISTRY_TOPOLOGY",
        replace_registry(
            domain,
            registry_id,
            semantic_name=f"{row.semantic_name} shifted",
        ),
    )


def test_sgreen_required_chain_native_and_never_ccip():
    surfaces = surface_map()
    for surface_id in ("S-003-DEPOSIT", "S-003-WITHDRAW"):
        assert surfaces[surface_id].disposition is Disposition.REQUIRED
    assert surfaces["S-003-CCIP"].disposition is Disposition.OMITTED
    assert surfaces["S-003-REWARDS"].disposition is Disposition.BLOCKED
    assert_code(
        "H03_SURFACE_SET",
        replace_surface("S-003-CCIP", disposition=Disposition.REQUIRED),
    )


def test_hr_scaffold_has_no_contributors_or_rewards():
    assert get_component("CM-005").deployment is Disposition.OMITTED
    hr = get_component("CM-032")
    assert hr.deployment is Disposition.REQUIRED
    assert {surface.surface_id for surface in hr.surfaces} == {
        "S-032-HR-ACTIVATION"
    }
    assert hr.surfaces[0].disposition is Disposition.DISABLED


def test_bonds_stay_disabled_while_rewards_are_promotion_gated():
    surfaces = surface_map()
    for surface_id in (
        "S-028-REWARD-PATH",
        "S-029-BONDS",
        "S-029-RIPE-CAP",
    ):
        assert surfaces[surface_id].disposition is Disposition.DISABLED
    assert all(surfaces[surface_id].disposition is Disposition.BLOCKED for surface_id in ("S-003-REWARDS", "S-013-REWARD-ACTIONS", "S-033-REWARD-MINT"))
    assert surfaces["S-038-BOOSTER-CFG"].disposition is Disposition.REQUIRED
    assert_code(
        "H03_SURFACE_SET",
        replace_surface("S-029-BONDS", disposition=Disposition.REQUIRED),
    )


def test_slot_scaffolds_have_exact_disabled_capabilities():
    surfaces = surface_map()
    expected = {
        "S-014-INERT-ACTIONS",
        "S-028-REWARD-PATH",
        "S-029-BONDS",
        "S-029-RIPE-CAP",
        "S-032-HR-ACTIVATION",
    }
    assert all(
        surfaces[surface_id].disposition is Disposition.DISABLED
        for surface_id in expected
    )
    assert all(
        surfaces[surface_id].disposition is Disposition.BLOCKED
        for surface_id in (
            "S-013-REWARD-ACTIONS",
            "S-033-REWARD-MINT",
        )
    )
    assert surfaces["S-038-BOOSTER-CFG"].disposition is Disposition.REQUIRED
    assert surfaces["S-003-DEPOSIT"].disposition is Disposition.REQUIRED


def test_pricedesk_curve_selection_and_empty_slots_cannot_be_repurposed():
    topology = registry_map()
    reserved = tuple(
        topology[(RegistryDomain.PRICE_DESK, value)] for value in (4, 5)
    )
    assert all(item.disposition is Disposition.OMITTED for item in reserved)
    assert topology[(RegistryDomain.PRICE_DESK, 3)].semantic_name == (
        "BlueChipYield"
    )
    assert topology[(RegistryDomain.PRICE_DESK, 3)].disposition is (
        Disposition.REQUIRED
    )
    component = get_component("CM-017")
    row = component.registry_expectations[0]
    assert_code(
        "H03_REGISTRY_TOPOLOGY",
        replace_component(
            "CM-017",
            registry_expectations=(
                replace(
                    row,
                    semantic_name="Stock",
                    disposition=Disposition.REQUIRED,
                ),
            ),
        ),
    )


def test_global_mint_reenable_is_final_launch_activation():
    surfaces = surface_map()
    disable = surfaces["S-004-GLOBAL-MINT-DISABLE"]
    enable = surfaces["S-004-GLOBAL-MINT-REENABLE"]
    psm_cap = surfaces["S-048-HQ-GREEN-CAP"]
    assert disable.disposition is Disposition.DISABLED
    assert disable.lifecycle_phase is LifecyclePhase.PRE_ACTIVATION_CONFIGURATION
    assert enable.disposition is Disposition.BLOCKED
    assert "final launch activation" in enable.semantic_meaning
    assert "full re-verification" in enable.semantic_meaning
    assert "final capability-tuple mutation" in psm_cap.semantic_meaning
    exact_pre_psm = {
        "S-010-HQ-BLACKLIST-CAP": (
            "canMintGreen=False",
            "canMintRipe=False",
            "canSetTokenBlacklist=True",
        ),
        "S-021-HQ-RIPE-CAP": (
            "canMintGreen=False",
            "canMintRipe=True",
            "canSetTokenBlacklist=False",
        ),
        "S-026-HQ-GREEN-CAP": (
            "canMintGreen=True",
            "canMintRipe=False",
            "canSetTokenBlacklist=False",
        ),
        "S-030-HQ-GREEN-CAP": (
            "canMintGreen=True",
            "canMintRipe=False",
            "canSetTokenBlacklist=False",
        ),
        "S-031-HQ-GREEN-CAP": (
            "canMintGreen=True",
            "canMintRipe=False",
            "canSetTokenBlacklist=False",
        ),
    }
    for surface_id, tuple_bits in exact_pre_psm.items():
        surface = surfaces[surface_id]
        assert surface.disposition is Disposition.BLOCKED
        assert surface.lifecycle_phase is (
            LifecyclePhase.PRE_ACTIVATION_CONFIGURATION
        )
        assert all(bit in surface.semantic_meaning for bit in tuple_bits)
        assert_code(
            "H03_TRACK8_GATE",
            replace_surface(
                surface_id,
                semantic_meaning=f"{surface.semantic_meaning} mutated",
            ),
        )
    assert_code(
        "H03_TRACK8_GATE",
        replace_surface(
            "S-004-GLOBAL-MINT-REENABLE",
            lifecycle_phase=LifecyclePhase.PRE_ACTIVATION_CONFIGURATION,
        ),
    )


def test_lp_assets_exclude_every_trusted_teller_route():
    lp_inputs = {
        get_symbolic_input("I-GREEN-USDG-LP").field_id,
        get_symbolic_input("I-RIPE-WETH-LP").field_id,
    }
    assert lp_inputs == {"I-GREEN-USDG-LP", "I-RIPE-WETH-LP"}
    ordinary = surface_map()["S-024-LP-ORDINARY-ONLY"]
    assert ordinary.disposition is Disposition.BLOCKED
    assert "deposit/depositMany" in ordinary.semantic_meaning
    assert "depositFromTrusted" in ordinary.semantic_meaning
    assert "Department/direct-vault bypass" in ordinary.semantic_meaning
    assert_code(
        "H03_TRACK8_GATE",
        replace_surface(
            "S-024-LP-ORDINARY-ONLY",
            semantic_meaning="LP may use depositFromTrusted",
        ),
    )


def test_lp_assets_are_deposit_only_with_zero_ltv():
    surfaces = surface_map()
    ltv = surfaces["S-024-LP-ZERO-LTV"]
    assert ltv.disposition is Disposition.BLOCKED
    assert "ltv=0" in ltv.semantic_meaning
    assert surfaces["S-024-LP-BORROW"].disposition is Disposition.OMITTED
    assert_code(
        "H03_TRACK8_GATE",
        replace_surface(
            "S-024-LP-ZERO-LTV",
            semantic_meaning="both approved LP assets use positive LTV",
        ),
    )


def test_usdg_is_psm_or_lp_only():
    surfaces = surface_map()
    assert surfaces["S-034-USDG-COLLATERAL"].disposition is (
        Disposition.OMITTED
    )
    assert surfaces["S-048-TELLER-ROUTE"].disposition is Disposition.OMITTED
    usdg = get_symbolic_input("I-USDG")
    assert usdg.consumers == ("CM-016", "CM-024", "CM-048")
    assert_code(
        "H03_TRACK8_GATE",
        replace_surface(
            "S-034-USDG-COLLATERAL",
            disposition=Disposition.REQUIRED,
        ),
    )


def test_psm_redeem_precedes_mint_capability():
    surfaces = surface_map()
    redeem = surfaces["S-048-REDEEM"]
    activation = surfaces["S-048-ACTIVATION"]
    assert "must be proved before mint" in redeem.semantic_meaning
    assert activation.assertion_ids == (
        "NEG-H03-PSM-REDEEM-FIRST",
        "NEG-H03-PSM-MINT-LAST",
    )
    assert_code(
        "H03_TRACK8_GATE",
        replace_surface(
            "S-048-ACTIVATION",
            semantic_meaning="mint precedes redemption",
        ),
    )


def test_psm_green_mint_capability_is_last():
    capability = surface_map()["S-048-HQ-GREEN-CAP"]
    assert capability.assertion_ids == (
        "NEG-018",
        "NEG-H03-PSM-MINT-LAST",
        "NEG-H03-GLOBAL-MINT-SEQUENCE",
    )
    assert "final capability-tuple mutation" in capability.semantic_meaning
    assert_code(
        "H03_TRACK8_GATE",
        replace_surface(
            "S-048-HQ-GREEN-CAP",
            assertion_ids=("NEG-018",),
        ),
    )


def test_profile1_predeployment_safety_envelope_is_atomic_and_fail_closed():
    manifest = json.loads(
        (ROOT / "config" / "robinhood-parameters.json").read_text()
    )
    records = {
        record["destination"]["path"]: record
        for record in manifest["parameters"]
    }
    surfaces = surface_map()
    topology = registry_map()

    assert records["Deployment.DP-18.roles.liteSigners"]["value"]["raw"] == []
    assert records["Defaults.underscoreRegistry"]["value"]["raw"] == (
        "empty(address)"
    )
    assert records["Deployment.DP-07.psm.constructor.canMint"]["value"]["raw"] is (
        False
    )
    assert records[
        "Deployment.DP-07.psm.constructor.canRedeem"
    ]["value"]["raw"] is False


    assert all(
        records[f"Deployment.DP-08.psm.{field}"]["status"] == "blocked"
        for field in (
            "mintFee",
            "redeemFee",
            "maxMintPerInterval",
            "maxRedeemPerInterval",
            "numBlocksPerInterval",
            "allowlists",
            "reserveFunding",
        )
    )
    assert all(
        records[f"Defaults.assetConfigs[{asset}].config.debtTerms.ltv"]["status"]
        == "omitted"
        for asset in ("GREEN_USDG_LP", "RIPE_WETH_LP")
    )
    assert "Defaults.assetConfigs[AAPL].asset" not in records
    assert {
        path.split("[", 1)[1].split("]", 1)[0]
        for path in records
        if path.startswith("Defaults.assetConfigs[")
        and path.endswith(".asset")
        and records[path]["status"] != "omitted"
    } == {"WETH", "RIPE", "SGREEN", "GREEN"}

    assert surfaces["S-048-MINT"].disposition is Disposition.DISABLED
    assert surfaces["S-048-REDEEM"].disposition is Disposition.DISABLED
    assert surfaces["S-048-ACTIVATION"].disposition is Disposition.BLOCKED
    assert surfaces["S-024-LP-BORROW"].disposition is Disposition.OMITTED
    assert surfaces["S-024-LP-ZERO-LTV"].disposition is Disposition.BLOCKED
    assert topology[(RegistryDomain.PRICE_DESK, 1)].semantic_name == "Chainlink"
    assert topology[(RegistryDomain.PRICE_DESK, 1)].disposition is (
        Disposition.REQUIRED
    )
    assert topology[(RegistryDomain.PRICE_DESK, 2)].semantic_name == "Curve"
    assert topology[(RegistryDomain.PRICE_DESK, 2)].disposition is (
        Disposition.REQUIRED
    )
    assert (ROOT / "contracts" / "config" / "DefaultsRobinhood.vy").is_file()


def test_curve_launch_graph_and_registry_selection_are_exact():
    curve = get_component("CM-017")
    assert curve.deployment is Disposition.REQUIRED
    assert len(curve.blocker_ids) == 9
    assert all(blocker.startswith("B-CURVE-") for blocker in curve.blocker_ids)
    assert {surface.surface_id for surface in curve.surfaces} == {
        "S-017-DEPLOYMENT",
        "S-017-GREEN-FEED",
        "S-017-USDG-FEED",
        "S-017-HIGHER-POWERS",
    }
    assert {relation.relation_id for relation in curve.relations} == {
        "R-291",
        "R-292",
        "R-293",
        "R-294",
        "R-295",
        "R-296",
    }
    price_desk_relations = {
        relation.relation_id: relation.target_component_id
        for relation in get_component("CM-015").relations
    }
    assert price_desk_relations["R-289"] == "CM-017"
    assert price_desk_relations["R-290"] == "CM-018"

    topology = registry_map()
    policy = blueprint_policy()
    assert topology[(RegistryDomain.PRICE_DESK, 2)].semantic_name == "Curve"
    assert topology[(RegistryDomain.PRICE_DESK, 2)].disposition is Disposition.REQUIRED
    assert ("price_desk", 2) in policy.required_registries


def test_psm_lite_pause_and_reserve_transfer_authority_is_explicitly_coupled():
    echo = (ROOT / "contracts" / "config" / "SwitchboardEcho.vy").read_text()
    charlie = (
        ROOT / "contracts" / "config" / "SwitchboardCharlie.vy"
    ).read_text()

    assert (
        "def transferUsdcToEndaomentFundsInPsm(_amount: uint256) -> uint256:\n"
        "    assert self._hasPermsForLiteAction(msg.sender, True)"
    ) in echo
    assert (
        "def pause(_contractAddr: address, _shouldPause: bool) -> bool:\n"
        "    assert self._hasPermsForLiteAction(msg.sender, _shouldPause)"
    ) in charlie
    assert (
        "return staticcall mc.canPerformLiteAction(_caller)"
    ) in echo
    assert (
        "return staticcall MissionControl("
        "self._getMissionControlAddr()).canPerformLiteAction(_caller)"
    ) in charlie


def test_psm_reserve_graph_has_no_lp_or_dex_liquidity_capital_edge():
    psm = get_component("CM-048")
    component_names = {
        component.component_id: component.name
        for component in ROBINHOOD_BLUEPRINT.components
    }
    targets = {
        relation.target_component_id: component_names[
            relation.target_component_id
        ]
        for relation in psm.relations
    }

    assert "CM-047" in targets
    assert targets["CM-047"] == "EndaomentFunds"
    assert all(
        "uniswap" not in name.lower()
        and "curve" not in name.lower()
        and "liquidity" not in name.lower()
        for name in targets.values()
    )
    assert all(
        "liquidity" not in relation.basis.lower()
        for relation in psm.relations
    )


def test_stock_activation_stays_parked_without_the_atomic_protected_tuple():
    manifest = json.loads(
        (ROOT / "config" / "robinhood-parameters.json").read_text()
    )
    records = {
        record["destination"]["path"]: record
        for record in manifest["parameters"]
    }
    surfaces = surface_map()

    assert "Defaults.assetConfigs[AAPL].asset" not in records
    assert all(
        record["status"] in {"blocked", "derived"}
        or (
            path == "Deployment.DP-11.stock.enabledVaultCount"
            and record["status"] == "approved"
            and record["value"]["raw"] == 1
            and record["launch_phase"] == "atomic Stock activation"
            and record["source"]["commit"]
            != "0f79b626c6ec4788ba43b3132ada9ebec6084f2a"
        )
        for path, record in records.items()
        if path.startswith("Deployment.DP-10.aapl.")
        or path.startswith("Deployment.DP-11.stock.")
    )
    assert surfaces["S-022-STOCK-SWAP"].disposition is Disposition.DISABLED
    assert surfaces["S-033-STOCK-REWARD"].disposition is Disposition.DISABLED
    assert surfaces["S-024-STOCK-USE"].disposition is Disposition.BLOCKED
    assert all(
        surface.disposition is not Disposition.REQUIRED
        for surface in surfaces.values()
        if "Stock" in surface.semantic_meaning
        or "AAPL" in surface.semantic_meaning
    )


def test_stock_rewards_start_disabled_and_are_not_selected_for_promotion():
    stock = surface_map()["S-033-STOCK-REWARD"]
    assert stock.disposition is Disposition.DISABLED
    assert stock.lifecycle_phase is LifecyclePhase.DEPLOYED_INITIAL_VALUE
    assert all(
        stock.surface_id not in promotion.surface_ids
        for promotion in ROBINHOOD_BLUEPRINT.promotions
    )
    assert_code(
        "H03_TRACK8_GATE",
        replace_surface(
            stock.surface_id,
            disposition=Disposition.OMITTED,
            lifecycle_phase=LifecyclePhase.OMITTED,
        ),
    )


def test_teller_exact_receipt_policy_covers_every_producer():
    exact = surface_map()["S-034-EXACT-RECEIPT"]
    assert exact.assertion_ids == ("NEG-H03-TELLER-EXACT-RECEIPT",)
    for required in (
        "R == Q",
        "vaultResult == Q",
        "typed balance reads",
        "one mutex policy",
        "atomic rollback",
    ):
        assert required in exact.semantic_meaning

    expected = {
        "R-141": "CM-022",
        "R-172": "CM-029",
        "R-188": "CM-030",
        "R-208": "CM-032",
        "R-220": "CM-033",
        "R-252": "CM-043",
        "R-266": "CM-044",
    }
    relations = relation_map()
    assert {
        relation_id: relations[relation_id][0]
        for relation_id in expected
    } == expected
    assert all(
        relations[relation_id][1].target_component_id == "CM-034"
        for relation_id in expected
    )
    assert len(relations["R-141"][1].source_proof_refs) >= 5
    for relation_id in expected:
        assert_code("H03_RELATION", remove_relation(relation_id))


def test_runtime_sources_and_explicit_no_edge_partition_are_exact():
    no_edge = {
        "CM-005",
        "CM-007",
        "CM-018",
        "CM-019",
        "CM-020",
        "CM-025",
        "CM-035",
        "CM-036",
        "CM-037",
        "CM-039",
        "CM-040",
        "CM-041",
        "CM-042",
        "CM-049",
        "CM-050",
        "CM-051",
        "CM-052",
        "CM-053",
        "CM-054",
        "CM-055",
        "CM-056",
        "CM-057",
        "CM-058",
        "CM-059",
        "CM-060",
    }
    runtime = {
        component.component_id
        for component in ROBINHOOD_BLUEPRINT.components
        if any(
            relation.phase is RelationPhase.RUNTIME_SECURITY
            for relation in component.relations
        )
    }
    assert len(no_edge) == 25
    assert len(runtime) == 35
    assert runtime.isdisjoint(no_edge)
    assert runtime | no_edge == {
        f"CM-{value:03d}" for value in range(1, 61)
    }


@pytest.mark.parametrize(
    ("code", "candidate"),
    (
        (
            "H03_COMPONENT_SET",
            replace(
                ROBINHOOD_BLUEPRINT,
                components=ROBINHOOD_BLUEPRINT.components[:-1],
            ),
        ),
        (
            "H03_IMMUTABLE",
            replace(
                ROBINHOOD_BLUEPRINT,
                components=list(ROBINHOOD_BLUEPRINT.components),
            ),
        ),
        (
            "H03_SYMBOLIC_FIELD",
            replace(
                ROBINHOOD_BLUEPRINT,
                symbolic_inputs=(
                    replace(
                        ROBINHOOD_BLUEPRINT.symbolic_inputs[0],
                        consumers=(),
                    ),
                    *ROBINHOOD_BLUEPRINT.symbolic_inputs[1:],
                ),
            ),
        ),
        (
            "H03_BLOCKER",
            replace(
                ROBINHOOD_BLUEPRINT,
                blockers=(
                    replace(
                        ROBINHOOD_BLUEPRINT.blockers[0],
                        primary_owner_id="OWN-UNKNOWN",
                    ),
                    *ROBINHOOD_BLUEPRINT.blockers[1:],
                ),
            ),
        ),
        (
            "H03_DISPOSITION",
            replace_component(
                "CM-001",
                deployment=Disposition.DEFERRED,
            ),
        ),
    ),
)
def test_core_mutation_matrix_diagnostic_families(code, candidate):
    assert_code(code, candidate)


def test_source_authority_mutation_matrix():
    component = get_component("CM-001")
    source = component.source_paths[0]
    for changed in (
        replace(source, path=None),
        replace(source, path="contracts/**/*.vy"),
        replace(source, path_kind=SourcePathKind.NONE),
        replace(source, path_state=SourcePathState.REVIEWED_PLANNED),
        replace(source, evidence_id="E-UNKNOWN"),
    ):
        assert_code(
            "H03_SOURCE_AUTHORITY",
            replace_component("CM-001", source_paths=(changed,)),
        )


def test_blocker_mutation_matrix():
    first = ROBINHOOD_BLUEPRINT.blockers[0]
    for changed in (
        replace(first, primary_owner_id="OWN-UNKNOWN"),
        replace(first, deadline_gate=""),
        Blocker(
            blocker_id="B-H02-AUDIT",
            primary_owner_id=first.primary_owner_id,
            co_owner_ids=first.co_owner_ids,
            summary=first.summary,
            deadline_gate=first.deadline_gate,
        ),
    ):
        candidate = replace(
            ROBINHOOD_BLUEPRINT,
            blockers=(changed, *ROBINHOOD_BLUEPRINT.blockers[1:]),
        )
        assert_code("H03_BLOCKER", candidate)


def test_relation_mutation_matrix():
    assert_code("H03_RELATION", remove_relation("R-288"))
    source_component, relation = relation_map()["R-001"]
    component = get_component(source_component)
    changed = replace(relation, target_component_id="CM-999")
    candidate = replace_component(
        source_component,
        relations=tuple(
            changed if item.relation_id == "R-001" else item
            for item in component.relations
        ),
    )
    assert_code("H03_RELATION", candidate)
