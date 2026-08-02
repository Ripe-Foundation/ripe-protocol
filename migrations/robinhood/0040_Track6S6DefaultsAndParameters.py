MIGRATION_STAGE = {
    "migration_id": "0040",
    "semantic_id": "track6-s6-defaults-and-parameters",
    "stage_kind": "assertion",
    "actions": (
        {
            "semantic_action_id": "assert-defaults-constructor-authority",
            "kind": "assertion",
            "operation": "assert-constructor-provenance",
            "component_id": "CM-049",
            "requires": (
                "blueprint:defaults-constructor",
                "defaults:constructor",
            ),
            "postconditions": ("defaults-constructor-order-matches-blueprint",),
        },
        {
            "semantic_action_id": "assert-derived-ledger-is-evidence-only",
            "kind": "tooling-only",
            "operation": "assert-authority-boundary",
            "component_id": "CM-055",
            "postconditions": ("derived-json-is-not-plan-input",),
        },
    ),
}


def migrate(migration):
    migration.apply_robinhood_stage(MIGRATION_STAGE)
