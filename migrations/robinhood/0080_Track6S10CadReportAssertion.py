MIGRATION_STAGE = {
    "migration_id": "0080",
    "semantic_id": "track6-s10-cad-report-assertion",
    "stage_kind": "tooling-only",
    "actions": (
        {
            "semantic_action_id": "assert-cad-report-interface",
            "kind": "tooling-only",
            "operation": "assert-offline-report-interface",
            "component_id": "CM-057",
            "postconditions": ("cad-report-remains-precollected-and-network-free",),
        },
        {
            "semantic_action_id": "bind-manifest-tooling",
            "kind": "tooling-only",
            "operation": "bind-selected-tooling-component",
            "component_id": "CM-056",
            "postconditions": ("history-remains-separate-and-uncreated",),
        },
    ),
}


def migrate(migration):
    migration.apply_robinhood_stage(MIGRATION_STAGE)
