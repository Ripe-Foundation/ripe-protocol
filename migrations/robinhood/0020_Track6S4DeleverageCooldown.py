MIGRATION_STAGE = {
    "migration_id": "0020",
    "semantic_id": "track6-s4-deleverage-cooldown",
    "stage_kind": "assertion",
    "actions": (
        {
            "semantic_action_id": "assert-zero-deleverage-cooldown",
            "kind": "assertion",
            "operation": "assert-source-invariant",
            "component_id": "CM-044",
            "requires": ("blueprint:assertion:deleverage_launch_cooldown",),
            "postconditions": ("deleverage-cooldown-remains-zero",),
        },
        {
            "semantic_action_id": "omit-cooldown-activation",
            "kind": "omission",
            "operation": "assert-action-absent",
            "component_id": "CM-044",
            "postconditions": ("no-cooldown-activation-transaction",),
        },
    ),
}


def migrate(migration):
    migration.apply_robinhood_stage(MIGRATION_STAGE)
