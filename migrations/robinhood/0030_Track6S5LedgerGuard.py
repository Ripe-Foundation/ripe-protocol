MIGRATION_STAGE = {
    "migration_id": "0030",
    "semantic_id": "track6-s5-ledger-guard",
    "stage_kind": "assertion",
    "actions": (
        {
            "semantic_action_id": "assert-ledger-action-block-source",
            "kind": "assertion",
            "operation": "assert-typed-input",
            "component_id": "CM-008",
            "requires": (
                "input:Deployment.DP-04.ledger.actionBlockSourceBinding",
            ),
            "postconditions": ("ledger-source-is-approved-native-or-arbsys",),
        },
        {
            "semantic_action_id": "reject-base-ledger-state",
            "kind": "omission",
            "operation": "assert-state-import-absent",
            "component_id": "CM-008",
            "postconditions": ("no-base-ledger-state-import",),
        },
    ),
}


def migrate(migration):
    migration.apply_robinhood_stage(MIGRATION_STAGE)
