from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import pytest

import config.BluePrint as source_authority


ROOT = Path(__file__).resolve().parents[2]


def _qualification_map():
    return {
        item.path: item
        for item in source_authority.ROBINHOOD_STOCK_INPUT_QUALIFICATIONS
    }


def test_aapl_is_the_only_initial_stock_and_every_input_is_traced():
    """The census is 15 inputs, not the historical 16.

    `Deployment.DP-11.stock.vaultArtifact` was removed: it asserted SimpleErc20
    artifact identity and nothing else, so with the artifact-expectations
    pipeline retired there is no fact left for it to carry. Its deployment input
    still exists and remains blocked; only the qualification claim is gone.
    """
    assert source_authority.ROBINHOOD_INITIAL_STOCK_SYMBOLS == ("AAPL",)
    assert len(source_authority.ROBINHOOD_STOCK_LAUNCH_INPUT_PATHS) == 15
    assert len(set(source_authority.ROBINHOOD_STOCK_LAUNCH_INPUT_PATHS)) == 15
    assert (
        "Deployment.DP-11.stock.vaultArtifact"
        not in source_authority.ROBINHOOD_STOCK_LAUNCH_INPUT_PATHS
    )
    assert source_authority.ROBINHOOD_STOCK_LAUNCH_INPUT_PATHS == tuple(
        item.path
        for item in source_authority.ROBINHOOD_STOCK_INPUT_QUALIFICATIONS
    )
    assert all(
        path in source_authority.ROBINHOOD_DEPLOYMENT_INPUTS
        for path in source_authority.ROBINHOOD_STOCK_LAUNCH_INPUT_PATHS
    )
    source_authority.validate_robinhood_stock_launch_qualification()


def test_selected_external_candidates_are_values_not_launch_approvals():
    records = _qualification_map()
    assert records["Deployment.DP-10.aapl.identity"].candidate == (
        "0xaF3D76f1834A1d425780943C99Ea8A608f8a93f9"
    )
    assert records["Deployment.DP-10.aapl.feed"].candidate == (
        "0x6B22A786bAa607d76728168703a39Ea9C99f2cD0"
    )
    assert records["Deployment.DP-10.aapl.decimals"].candidate == 18
    assert all(
        "pending_current_verification" in records[path].resolution
        for path in (
            "Deployment.DP-10.aapl.identity",
            "Deployment.DP-10.aapl.feed",
            "Deployment.DP-10.aapl.decimals",
        )
    )
    assert all(
        isinstance(
            source_authority.ROBINHOOD_DEPLOYMENT_INPUTS[path].value,
            source_authority.SymbolicBinding,
        )
        and source_authority.ROBINHOOD_DEPLOYMENT_INPUTS[path].disposition
        == "blocked"
        for path in records
    )


def test_every_non_repository_fact_has_an_explicit_typed_blocker():
    resolved = set(
        source_authority.ROBINHOOD_STOCK_RESOLVED_REPOSITORY_FACT_PATHS
    )
    unresolved = set(source_authority.ROBINHOOD_STOCK_UNRESOLVED_INPUT_PATHS)
    assert resolved | unresolved == set(
        source_authority.ROBINHOOD_STOCK_LAUNCH_INPUT_PATHS
    )
    assert not resolved & unresolved
    # M2, M3, and M4 stay integrated repository facts -- their behavior is
    # proven by tests that still run, which is what status.yaml records for
    # B-T8-M2/M3/M4. What was removed is the hash evidence layer, not the
    # integration. Stock stays fail-closed on unresolved M5.
    assert resolved == {
        "Deployment.DP-11.stock.m2Movement",
        "Deployment.DP-11.stock.m3CreditContainment",
        "Deployment.DP-11.stock.m4ComposedProof",
    }
    records = _qualification_map()
    # An integrated semantic fact must carry no candidate payload. A hash with
    # nothing to recompute it is not proof, and a stale one reads as proof
    # while being false.
    assert all(records[path].candidate is None for path in resolved)
    assert all(records[path].blocker_ids for path in unresolved)
    assert all(not records[path].blocker_ids for path in resolved)

    ready, blockers = source_authority.robinhood_stock_launch_readiness()
    assert not ready
    assert len(blockers) == len(unresolved) + 1
    assert blockers[-1] == "activation:atomic_packet_unaccepted"
    assert all(
        any(path in blocker for blocker in blockers)
        for path in unresolved
    )
    assert all(
        all(path not in blocker for blocker in blockers)
        for path in resolved
    )


@pytest.mark.parametrize(
    "resolution",
    ("repository_fact_integrated", "semantic_fact_with_payload"),
)
def test_semantic_fact_cannot_carry_a_hash_payload(resolution):
    """M2/M3/M4 are proven by behavior; they must never regain an identity payload.

    Parametrized over the resolution string on purpose. An earlier revision of
    the guard keyed on a resolution value, and a review defeated it by renaming
    the resolution while attaching a payload. Resolution values are open
    vocabulary, so the guard keys on the exact path IDs instead; this test
    fails if that regresses.
    """
    mutant = tuple(
        replace(
            item,
            resolution=resolution,
            candidate=(("gitBlob", "0" * 40), ("sha256", "0" * 64)),
        )
        if item.path == "Deployment.DP-11.stock.m4ComposedProof"
        else item
        for item in source_authority.ROBINHOOD_STOCK_INPUT_QUALIFICATIONS
    )
    with pytest.raises(ValueError, match="RH_STOCK_SEMANTIC_FACT_PAYLOAD"):
        source_authority.validate_robinhood_stock_launch_qualification(mutant)


def test_unresolved_input_cannot_be_relabelled_an_integrated_fact():
    """Only M2/M3/M4 may claim integration; M5 and the rest stay fail-closed."""
    mutant = tuple(
        replace(item, resolution="repository_fact_integrated", blocker_ids=())
        if item.path == "Deployment.DP-11.stock.m5ActivationBinding"
        else item
        for item in source_authority.ROBINHOOD_STOCK_INPUT_QUALIFICATIONS
    )
    with pytest.raises(ValueError, match="RH_STOCK_REPOSITORY_FACT_SET"):
        source_authority.validate_robinhood_stock_launch_qualification(mutant)


def test_semantic_fact_cannot_be_silently_downgraded():
    """Dropping M4's integration claim must fail rather than pass silently."""
    mutant = tuple(
        replace(item, resolution="owner_choice_unresolved", blocker_ids=("B-T8-M5",))
        if item.path == "Deployment.DP-11.stock.m4ComposedProof"
        else item
        for item in source_authority.ROBINHOOD_STOCK_INPUT_QUALIFICATIONS
    )
    with pytest.raises(ValueError, match="RH_STOCK_REPOSITORY_FACT_SET"):
        source_authority.validate_robinhood_stock_launch_qualification(mutant)


def test_stock_census_cannot_shrink():
    """Removing a census path must fail rather than pass silently."""
    mutant = tuple(
        item
        for item in source_authority.ROBINHOOD_STOCK_INPUT_QUALIFICATIONS
        if item.path != "Deployment.DP-11.stock.m2Movement"
    )
    with pytest.raises(ValueError, match="RH_STOCK_INPUT_CENSUS"):
        source_authority.validate_robinhood_stock_launch_qualification(mutant)


def test_atomic_policy_keeps_defaults_routes_and_rewards_fail_closed():
    policy = dict(source_authority.ROBINHOOD_STOCK_ACTIVATION_POLICY)
    assert policy == {
        "vault": "SimpleErc20",
        "exclusiveVaultAssignment": True,
        "shouldSwapInStabPools": False,
        "shouldTransferToEndaoment": False,
        "shouldAuctionInstantly": True,
        "canRedeemCollateral": False,
        "unsupportedStockRoutes": "absent",
        "stockRewards": "disabled_recommendation_only",
        "defaultsPosture": "absent_until_atomic_packet_accepted",
    }
    assert source_authority.ROBINHOOD_ASSERTION_INVARIANTS[
        "stock_enabled_vaults"
    ] == ("SimpleErc20",)
    assert source_authority.ROBINHOOD_ASSERTION_INVARIANTS[
        "stock_excluded_from_stability_pool"
    ] is True

    defaults_source = (
        ROOT / "contracts/config/DefaultsRobinhood.vy"
    ).read_text()
    assert "AAPL" not in defaults_source
    ledger = json.loads(
        (ROOT / "config/robinhood-parameters.json").read_text()
    )
    records = {
        record["destination"]["path"]: record
        for record in ledger["parameters"]
    }
    assert "Defaults.assetConfigs[AAPL].asset" not in records
    exclusion = records[
        "Deployment.DP-13.stock.excludedFromStabilityPool"
    ]
    assert exclusion["value"] == {"kind": "concrete", "raw": True}

    assert source_authority.ROBINHOOD_DEPLOYMENT_INPUTS[
        "Deployment.DP-15.rewards.arePointsEnabled"
    ].disposition == "approved"
    promotion = source_authority.ROBINHOOD_DEPLOYMENT_INPUTS[
        "Deployment.DP-15.rewards.promotion"
    ]
    assert promotion.disposition == "approved"
    assert promotion.value == (
        "f84bb5558c3bcce6eb5018e723a42f7270eae63ed8f23789b47ee99663d51234"
    )


@pytest.mark.parametrize(
    "path", source_authority.ROBINHOOD_STOCK_LAUNCH_INPUT_PATHS
)
def test_omitting_any_atomic_input_fails_the_qualification(path):
    candidate = tuple(
        item
        for item in source_authority.ROBINHOOD_STOCK_INPUT_QUALIFICATIONS
        if item.path != path
    )
    with pytest.raises(ValueError, match="RH_STOCK_INPUT_CENSUS"):
        source_authority.validate_robinhood_stock_launch_qualification(
            candidate
        )


def test_resolution_and_policy_mutants_fail_closed(monkeypatch):
    records = source_authority.ROBINHOOD_STOCK_INPUT_QUALIFICATIONS
    unresolved = records[0]
    bad_unresolved = (
        replace(unresolved, blocker_ids=()),
        *records[1:],
    )
    with pytest.raises(ValueError, match="RH_STOCK_UNTYPED_BLOCKER"):
        source_authority.validate_robinhood_stock_launch_qualification(
            bad_unresolved
        )

    policy = tuple(
        (name, True if name == "shouldSwapInStabPools" else value)
        for name, value in source_authority.ROBINHOOD_STOCK_ACTIVATION_POLICY
    )
    monkeypatch.setattr(
        source_authority,
        "ROBINHOOD_STOCK_ACTIVATION_POLICY",
        policy,
    )
    with pytest.raises(ValueError, match="RH_STOCK_POLICY"):
        source_authority.validate_robinhood_stock_launch_qualification()
