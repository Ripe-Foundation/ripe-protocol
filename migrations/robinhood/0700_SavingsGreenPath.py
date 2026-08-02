MIGRATION_STAGE = {
    "migration_id": "0700",
    "semantic_id": "savings-green-path",
    "stage_kind": "configuration",
    "actions": (
        {
            "semantic_action_id": "assert-savings-green-deployed-inert",
            "kind": "assertion",
            "operation": "assert-deployed-disabled",
            "component_id": "CM-003",
            "requires": ("address:SGREEN_TOKEN",),
            "postconditions": ("savings-green-is-deployed", "savings-green-user-path-disabled"),
        },
        {
            "semantic_action_id": "assert-stability-path-inert",
            "kind": "assertion",
            "operation": "assert-feature-disabled",
            "component_id": "CM-022",
            "postconditions": ("stability-path-not-activated", "deployment-does-not-imply-activation"),
        },
        {
            "semantic_action_id": "reserve-savings-activation-decision",
            "kind": "blocked",
            "operation": "declare-future-owner-action",
            "requires": ("binding:savings-green-activation-authority",),
            "postconditions": ("no-activation-decision-in-launch-plan",),
        },
    ),
}


def migrate(migration):
    migration.apply_robinhood_stage(MIGRATION_STAGE)
