from __future__ import annotations

import pytest

from scripts.utils.robinhood_backends import DeterministicRobinhoodBackend
from scripts.utils.robinhood_backends import LOCAL_GOVERNANCE_REFERENCES
from scripts.utils.robinhood_executor import (
    RobinhoodExecutionError,
    RobinhoodStageExecutor,
)
from tests.deployment.robinhood_execution_support import (
    MigrationHandoff,
    TEMPORARY_GOVERNANCE,
    bound_mainnet_plan,
    build_bound_plan,
    committed_execution_root,
)


FAILURE_POINTS = (
    "0100:000000:deploy-green-token",
    "0200:000001:register-ledger",
    "0400:000002:configure-chainlink-usdg-feed",
    "0900:000004:assert-pre-handoff-postconditions",
)


@pytest.mark.parametrize("failure_action", FAILURE_POINTS)
@pytest.mark.parametrize("boundary", ("before", "after"))
def test_failure_boundary_resumes_without_repeating_mutation(
    committed_execution_root, bound_mainnet_plan, failure_action, boundary
):
    root = committed_execution_root
    plan = bound_mainnet_plan
    backend = DeterministicRobinhoodBackend(
        fail_before=failure_action if boundary == "before" else None,
        fail_after=failure_action if boundary == "after" else None,
    )
    executor = RobinhoodStageExecutor(plan, repository_root=root, backend=backend)
    migration = MigrationHandoff()
    failed_stage = None
    for stage in plan["stages"]:
        try:
            executor(migration, stage)
        except RobinhoodExecutionError:
            failed_stage = stage
            break
    assert failed_stage is not None
    assert backend.handed_off is False
    mutations_after_failure = backend.mutation_counts.get(failure_action, 0)

    retry_migration = MigrationHandoff()
    executor(retry_migration, failed_stage)
    for stage in plan["stages"][executor.stage_cursor:]:
        executor(MigrationHandoff(), stage)
    assert backend.handed_off is True
    assert backend.mutation_counts.get(failure_action, 0) == mutations_after_failure or boundary == "before"
    assert backend.mutation_counts.get(failure_action, 0) <= 1


def test_final_handoff_refuses_incomplete_required_assertion(
    committed_execution_root, bound_mainnet_plan
):
    root = committed_execution_root
    plan = bound_mainnet_plan
    backend = DeterministicRobinhoodBackend(
        fail_before="0900:000004:assert-pre-handoff-postconditions"
    )
    executor = RobinhoodStageExecutor(plan, repository_root=root, backend=backend)
    with pytest.raises(RobinhoodExecutionError):
        for stage in plan["stages"]:
            executor(MigrationHandoff(), stage)
    assert "0900:000005:handoff-governance-and-relinquish-deployer" not in backend.sequence
    assert backend.handed_off is False


def test_stale_modified_preview_and_wrong_profile_plans_fail_closed(
    committed_execution_root, bound_mainnet_plan
):
    root = committed_execution_root
    plan = bound_mainnet_plan
    backend = DeterministicRobinhoodBackend()
    candidates = []
    modified = dict(plan)
    modified["plan_hash"] = "0" * 64
    candidates.append(modified)
    wrong = dict(plan)
    wrong["profile"] = dict(plan["profile"], profile_id="robinhood-testnet")
    candidates.append(wrong)
    from scripts.utils.migration_runner import build_robinhood_plan

    candidates.append(
        build_robinhood_plan(
            "robinhood-mainnet", repository_root=root, preview=True
        )
    )
    for candidate in candidates:
        with pytest.raises(RobinhoodExecutionError, match="RHX_PLAN_REJECTED"):
            RobinhoodStageExecutor(
                candidate, repository_root=root, backend=backend
            )


def test_zero_temporary_governance_is_rejected_before_execution(
    committed_execution_root,
):
    from scripts.utils.migration_runner import MigrationPlanError

    with pytest.raises(
        MigrationPlanError,
        match="H05_TEMPORARY_LOCAL_GOVERNANCE_INVALID",
    ):
        build_bound_plan(
            committed_execution_root,
            overrides={
                "binding:temporary-local-governance": (
                    "address",
                    "0x" + "0" * 40,
                )
            },
        )


def test_final_governance_cannot_be_used_as_temporary_governance(
    committed_execution_root,
):
    from scripts.utils.migration_runner import MigrationPlanError

    baseline = build_bound_plan(committed_execution_root)
    final_governance = baseline["execution_envelope"]["values"][
        "input:Deployment.DP-18.roles.governance"
    ]["value"]
    with pytest.raises(
        MigrationPlanError,
        match="H05_TEMPORARY_LOCAL_GOVERNANCE_INVALID",
    ):
        build_bound_plan(
            committed_execution_root,
            overrides={
                "binding:temporary-local-governance": (
                    "address",
                    final_governance,
                )
            },
        )


def test_temporary_governance_must_equal_executor_sender(
    committed_execution_root, bound_mainnet_plan
):
    backend = DeterministicRobinhoodBackend(
        execution_sender="0x" + "3" * 40
    )
    with pytest.raises(
        RobinhoodExecutionError,
        match="RHX_TEMPORARY_GOVERNANCE_SENDER_MISMATCH",
    ):
        RobinhoodStageExecutor(
            bound_mainnet_plan,
            repository_root=committed_execution_root,
            backend=backend,
        )
    assert backend.sequence == []


@pytest.mark.parametrize(
    ("boundary", "reference"),
    (
        ("before", LOCAL_GOVERNANCE_REFERENCES[0]),
        ("after", LOCAL_GOVERNANCE_REFERENCES[5]),
        ("after", LOCAL_GOVERNANCE_REFERENCES[-1]),
    ),
)
def test_partial_relinquishment_history_resumes_only_remaining_contracts(
    tmp_path,
    committed_execution_root,
    bound_mainnet_plan,
    boundary,
    reference,
):
    history_root = tmp_path / f"history-{boundary}-{reference[8:]}"
    history_root.mkdir(mode=0o700)
    backend = DeterministicRobinhoodBackend(
        execution_sender=TEMPORARY_GOVERNANCE,
        fail_relinquishment_before=(
            reference if boundary == "before" else None
        ),
        fail_relinquishment_after=(
            reference if boundary == "after" else None
        ),
    )
    executor = RobinhoodStageExecutor(
        bound_mainnet_plan,
        repository_root=committed_execution_root,
        backend=backend,
        history_root=history_root,
    )
    with pytest.raises(
        RobinhoodExecutionError, match="RHX_RELINQUISHMENT_INCOMPLETE"
    ):
        for stage in bound_mainnet_plan["stages"]:
            executor(MigrationHandoff(), stage)
    assert executor.history is not None
    assert executor.history.current_index is None
    attempt = executor.history.attempts[-1]
    failed = attempt["step"]["actions"][-1]
    evidence = failed["execution_evidence"]
    assert evidence["failure_classification"] == (
        "relinquishment-incomplete"
    )
    assert evidence["outputs"] == []
    retained = set(evidence["retained_temporary_governance"])
    boundary_index = LOCAL_GOVERNANCE_REFERENCES.index(reference)
    expected_complete = set(
        LOCAL_GOVERNANCE_REFERENCES[
            : boundary_index
            if boundary == "before"
            else boundary_index + 1
        ]
    )
    receipts = evidence["authority_relinquishments"]
    assert {
        row["contract_reference"]
        for row in receipts
        if row["status"] == "complete"
    } == expected_complete
    failed_receipts = [row for row in receipts if row["status"] == "failed"]
    assert [row["contract_reference"] for row in failed_receipts] == (
        [reference] if boundary == "before" else []
    )
    expected_retained = set(
        LOCAL_GOVERNANCE_REFERENCES[
            boundary_index
            if boundary == "before"
            else boundary_index + 1 :
        ]
    )
    assert retained == expected_retained
    assert backend.handed_off is False
    final_governance = bound_mainnet_plan["execution_envelope"]["values"][
        "input:Deployment.DP-18.roles.governance"
    ]["value"].lower()
    assert backend.hq_governance == final_governance
    completed_before_resume = dict(
        backend.relinquishment_mutation_counts
    )

    resume_backend = DeterministicRobinhoodBackend(
        execution_sender=TEMPORARY_GOVERNANCE
    )
    resumed = RobinhoodStageExecutor(
        bound_mainnet_plan,
        repository_root=committed_execution_root,
        backend=resume_backend,
        history_root=history_root,
    )
    resumed(MigrationHandoff(), bound_mainnet_plan["stages"][-1])
    assert resumed.history is not None
    assert resumed.history.current_index is not None
    assert backend.handed_off is False
    assert resume_backend.handed_off is True
    assert resume_backend.hq_governance == final_governance
    assert set(resume_backend.local_governance.values()) == {
        "0x" + "0" * 40
    }
    assert all(
        count == 1
        for count in resume_backend.relinquishment_mutation_counts.values()
    )
    assert all(
        resume_backend.relinquishment_mutation_counts[item] == count
        for item, count in completed_before_resume.items()
    )
