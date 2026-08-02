MIGRATION_STAGE = {
    "migration_id": "0900",
    "semantic_id": "capabilities-roles-and-handoff",
    "stage_kind": "handoff",
    "actions": (
        {
            "semantic_action_id": "bind-governance-safe-guardian",
            "kind": "configuration",
            "operation": "bind-role-identities",
            "requires": ("input:Deployment.DP-18.roles.governance", "input:Deployment.DP-18.roles.safe", "input:Deployment.DP-18.roles.guardian"),
            "postconditions": ("governance-safe-guardian-identities-exact",),
        },
        {
            "semantic_action_id": "bind-training-wheels-operator-signers",
            "kind": "configuration",
            "operation": "bind-role-identities",
            "requires": ("address:TRAINING_WHEELS", "input:Deployment.DP-18.roles.liteSigners", "binding:operator-identity", "binding:release-signer-identity"),
            "postconditions": ("operator-and-signer-values-exact", "psm-lite-signer-posture-zero"),
        },
        {
            "semantic_action_id": "apply-approved-capabilities",
            "kind": "configuration",
            "operation": "apply-exact-capability-set",
            "requires": ("binding:approved-capability-set",),
            "postconditions": ("only-approved-capabilities-enabled", "psm-green-mint-withheld", "ccip-capabilities-absent"),
        },
        {
            "semantic_action_id": "finalize-action-and-registry-timelocks",
            "kind": "configuration",
            "operation": "finalize-timelocks",
            "requires": ("input-prefix:Deployment.DP-05.timelocks.",),
            "postconditions": ("all-final-timelocks-match-blueprint",),
        },
        {
            "semantic_action_id": "assert-pre-handoff-postconditions",
            "kind": "assertion",
            "operation": "assert-complete-launch-state",
            "requires": ("binding:release-proof",),
            "postconditions": (
                "all-selected-components-accounted-for",
                "all-selected-registrations-accounted-for",
                "all-omitted-and-deferred-components-absent",
                "curve-price-topology-one-two-three",
                "psm-disabled",
                "ccip-absent",
                "no-pending-required-actions",
            ),
        },
        {
            "semantic_action_id": "handoff-governance-and-relinquish-deployer",
            "kind": "handoff",
            "operation": "irreversible-final-authority-handoff",
            "requires": ("binding:final-handoff-authorization", "action:assert-pre-handoff-postconditions"),
            "abort_if": ("any-postcondition-failed", "identity-mismatch", "pending-action-exists"),
            "postconditions": ("governance-authority-final", "deployer-authority-zero", "handoff-is-final-action"),
        },
    ),
}


def migrate(migration):
    migration.apply_robinhood_stage(MIGRATION_STAGE)
