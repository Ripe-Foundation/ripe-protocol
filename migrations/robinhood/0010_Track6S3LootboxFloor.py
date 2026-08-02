MIGRATION_STAGE = {
    "migration_id": "0010",
    "semantic_id": "track6-s3-lootbox-floor",
    "stage_kind": "assertion",
    "actions": (
        {
            "semantic_action_id": "assert-lootbox-floor-clock",
            "kind": "assertion",
            "operation": "assert-source-invariant",
            "component_id": "CM-033",
            "requires": (
                "blueprint:assertion:deleverage_launch_cooldown",
                "blueprint:chain:evm_block_number_seconds",
            ),
            "postconditions": ("lootbox-floor-is-clock-safe",),
        },
    ),
}


def migrate(migration):
    migration.apply_robinhood_stage(MIGRATION_STAGE)
