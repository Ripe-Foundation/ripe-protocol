from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import subprocess

import pytest

import config.BluePrint as source_authority


ROOT = Path(__file__).resolve().parents[2]


def _qualification_map():
    return {
        item.path: item
        for item in source_authority.ROBINHOOD_STOCK_INPUT_QUALIFICATIONS
    }


def _m4_binding():
    binding = _qualification_map()[
        "Deployment.DP-11.stock.m4ComposedProof"
    ].candidate
    assert isinstance(binding, source_authority.RobinhoodStockM4Binding)
    return binding


def _head_blob(path: str) -> str:
    result = subprocess.run(
        ["/usr/bin/git", "rev-parse", f"HEAD:{path}"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def test_aapl_is_the_only_initial_stock_and_all_16_inputs_are_traced():
    assert source_authority.ROBINHOOD_INITIAL_STOCK_SYMBOLS == ("AAPL",)
    assert len(source_authority.ROBINHOOD_STOCK_LAUNCH_INPUT_PATHS) == 16
    assert len(set(source_authority.ROBINHOOD_STOCK_LAUNCH_INPUT_PATHS)) == 16
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
    assert resolved == {
        "Deployment.DP-11.stock.vaultArtifact",
        "Deployment.DP-11.stock.m2Movement",
        "Deployment.DP-11.stock.m3CreditContainment",
        "Deployment.DP-11.stock.m4ComposedProof",
    }
    records = _qualification_map()
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


def test_simple_artifact_binding_matches_frozen_artifacts_and_git_bytes():
    binding = dict(source_authority.ROBINHOOD_STOCK_ARTIFACT_BINDING)
    expectations = json.loads(
        (ROOT / "config/contract-artifact-expectations.json").read_text()
    )["contracts"]["SimpleErc20"]
    source = ROOT / binding["sourcePath"]

    assert binding["contract"] == "SimpleErc20"
    assert binding["sourceGitBlob"] == expectations["source_git_blob"]
    assert binding["sourceGitBlob"] == _head_blob(binding["sourcePath"])
    assert binding["sourceSha256"] == expectations["source_sha256"]
    assert binding["sourceSha256"] == hashlib.sha256(
        source.read_bytes()
    ).hexdigest()
    assert binding["creationSha256"] == expectations["artifacts"][
        "creation_sha256"
    ]
    assert binding["runtimeTemplateSha256"] == expectations["artifacts"][
        "runtime_template_sha256"
    ]
    assert binding["runtimeTemplateSize"] == expectations["artifacts"][
        "runtime_template_size"
    ]
    assert binding["abiCanonicalSha256"] == expectations["abi"][
        "canonical_sha256"
    ]
    assert binding["selectorsCanonicalSha256"] == expectations["selectors"][
        "canonical_sha256"
    ]
    assert binding["selectorCount"] == expectations["selectors"]["count"]


def test_m2_m3_repository_bindings_are_integrated_ancestors():
    records = _qualification_map()
    for path in (
        "Deployment.DP-11.stock.m2Movement",
        "Deployment.DP-11.stock.m3CreditContainment",
    ):
        candidate = dict(records[path].candidate)
        commit = candidate["integrationCommit"]
        ancestry = subprocess.run(
            ["/usr/bin/git", "merge-base", "--is-ancestor", commit, "HEAD"],
            cwd=ROOT,
            capture_output=True,
            check=False,
        )
        assert ancestry.returncode == 0
        assert candidate["gitBlob"] == _head_blob(candidate["source"])


def test_m4_binding_matches_exact_historical_tranche_and_current_bytes():
    binding = _m4_binding()
    assert binding.historical_tranche.changed_paths == (
        ("M", "tests/core/auctionHouse/test_ah_auctions.py"),
        (
            "A",
            "tests/core/auctionHouse/test_auctionhouse_stock_delivery.py",
        ),
        (
            "A",
            "tests/core/deleverage/test_deleverage_stock_delivery.py",
        ),
        (
            "M",
            "tests/core/deleverage/test_deleverage_swap_collateral.py",
        ),
    )
    source_authority.validate_robinhood_stock_m4_binding(ROOT, binding)


@pytest.mark.parametrize(
    "mutation",
    ("remove_path", "unrelated_substitution", "extra_path", "status_drift"),
)
def test_m4_historical_path_census_mutants_fail_closed(mutation):
    binding = _m4_binding()
    historical = binding.historical_tranche
    paths = historical.changed_paths
    if mutation == "remove_path":
        mutant_paths = paths[:-1]
    elif mutation == "unrelated_substitution":
        mutant_paths = (
            *paths[:-1],
            ("M", "tests/vaults/test_basic_vault_safety.py"),
        )
    elif mutation == "extra_path":
        mutant_paths = (*paths, ("A", "tests/vaults/test_basic_vault_safety.py"))
    else:
        mutant_paths = (("A", paths[0][1]), *paths[1:])
    mutant = replace(
        binding,
        historical_tranche=replace(historical, changed_paths=mutant_paths),
    )
    with pytest.raises(
        ValueError, match="RH_STOCK_M4_HISTORICAL_PATH_CENSUS"
    ):
        source_authority.validate_robinhood_stock_m4_binding(ROOT, mutant)


def test_m4_wrong_similar_commit_fails_closed():
    binding = _m4_binding()
    mutant = replace(
        binding,
        historical_tranche=replace(
            binding.historical_tranche,
            integration_commit="4f887207d344a1513d6c3a79d315c8315a10a9c8",
        ),
    )
    with pytest.raises(ValueError, match="RH_STOCK_M4_COMMIT"):
        source_authority.validate_robinhood_stock_m4_binding(ROOT, mutant)


def test_m4_exact_commit_missing_from_repository_fails_non_ancestor(tmp_path):
    with pytest.raises(ValueError, match="RH_STOCK_M4_NON_ANCESTOR"):
        source_authority.validate_robinhood_stock_m4_binding(
            tmp_path, _m4_binding()
        )


@pytest.mark.parametrize(
    ("mutation", "error"),
    (
        ("test_identity_omitted", "RH_STOCK_M4_TEST_IDENTITY_CENSUS"),
        ("test_blob_drift", "RH_STOCK_M4_TEST_BLOB"),
        ("test_sha256_drift", "RH_STOCK_M4_TEST_SHA256"),
        (
            "artifact_identity_omitted",
            "RH_STOCK_M4_ARTIFACT_IDENTITY_CENSUS",
        ),
        ("source_path_substitution", "RH_STOCK_M4_ARTIFACT_IDENTITY_CENSUS"),
        ("source_blob_drift", "RH_STOCK_M4_SOURCE_BLOB"),
        ("artifact_identity_drift", "RH_STOCK_M4_ARTIFACT_EXPECTATION"),
    ),
)
def test_m4_current_applicability_mutants_fail_closed(mutation, error):
    binding = _m4_binding()
    tests = binding.current_test_identities
    artifacts = binding.current_artifact_identities
    if mutation == "test_identity_omitted":
        mutant = replace(binding, current_test_identities=tests[:-1])
    elif mutation == "test_blob_drift":
        mutant = replace(
            binding,
            current_test_identities=(
                replace(tests[0], git_blob="0" * 40),
                *tests[1:],
            ),
        )
    elif mutation == "test_sha256_drift":
        mutant = replace(
            binding,
            current_test_identities=(
                replace(tests[0], sha256="0" * 64),
                *tests[1:],
            ),
        )
    elif mutation == "artifact_identity_omitted":
        mutant = replace(binding, current_artifact_identities=artifacts[:-1])
    elif mutation == "source_path_substitution":
        mutant = replace(
            binding,
            current_artifact_identities=(
                    *artifacts[:-1],
                    replace(
                        artifacts[-1],
                        source_path="contracts/vaults/RebaseErc20.vy",
                    ),
                ),
            )
    elif mutation == "source_blob_drift":
        mutant = replace(
            binding,
            current_artifact_identities=(
                replace(artifacts[0], source_git_blob="0" * 40),
                *artifacts[1:],
            ),
        )
    else:
        mutant = replace(
            binding,
            current_artifact_identities=(
                replace(artifacts[0], creation_sha256="0" * 64),
                *artifacts[1:],
            ),
        )
    with pytest.raises(ValueError, match=error):
        source_authority.validate_robinhood_stock_m4_binding(ROOT, mutant)


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
        "7395a0bff4abd75e11f832fbd0dee2f6569244dafa2ba52604d3f5989662acec"
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
