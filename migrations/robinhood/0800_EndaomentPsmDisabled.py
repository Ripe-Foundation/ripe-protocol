MIGRATION_STAGE = {
    "migration_id": "0800",
    "semantic_id": "endaoment-psm-disabled",
    "stage_kind": "configuration",
    "actions": (
        {
            "semantic_action_id": "disable-psm-auto-deposit-before-launch",
            "kind": "configuration",
            "operation": "set-auto-deposit-disabled",
            "component_id": "CM-048",
            "requires": ("input:Deployment.DP-07.psm.preActivation.shouldAutoDeposit",),
            "postconditions": ("psm-auto-deposit-false",),
        },
        {
            "semantic_action_id": "assert-psm-disabled-posture",
            "kind": "assertion",
            "operation": "assert-disabled-scaffold",
            "component_id": "CM-048",
            "requires": ("defaults:lite-signers", "input:Deployment.DP-07.psm.yield.amount", "input:Deployment.DP-07.psm.yield.asset"),
            "postconditions": (
                "psm-can-mint-false",
                "psm-can-redeem-false",
                "psm-auto-deposit-false",
                "psm-reserve-funding-zero",
                "psm-yield-disabled",
                "psm-non-governance-lite-signers-zero",
            ),
        },
        {
            "semantic_action_id": "omit-psm-activation",
            "kind": "omission",
            "operation": "assert-action-family-absent",
            "component_id": "CM-048",
            "postconditions": ("no-minting-redemption-funding-yield-or-allowlist-activation", "curve-not-authority-for-psm"),
        },
        {
            "semantic_action_id": "reserve-psm-activation-sequence",
            "kind": "blocked",
            "operation": "declare-future-owner-action",
            "component_id": "CM-048",
            "requires": ("input:Deployment.DP-09.psm.executionBinding",),
            "postconditions": ("psm-activation-remains-separate",),
        },
    ),
}


def migrate(migration):
    migration.apply_robinhood_stage(MIGRATION_STAGE)
