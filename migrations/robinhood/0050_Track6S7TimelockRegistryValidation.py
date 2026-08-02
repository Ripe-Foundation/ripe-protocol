MIGRATION_STAGE = {
    "migration_id": "0050",
    "semantic_id": "track6-s7-timelock-registry-validation",
    "stage_kind": "assertion",
    "actions": (
        {
            "semantic_action_id": "assert-timelock-input-set",
            "kind": "assertion",
            "operation": "assert-input-prefix",
            "component_id": "CM-055",
            "requires": ("input-prefix:Deployment.DP-05.timelocks.",),
            "postconditions": ("all-deployment-timelocks-have-blueprint-provenance",),
        },
        {
            "semantic_action_id": "assert-registry-topology-source",
            "kind": "assertion",
            "operation": "assert-topology-authority",
            "component_id": "CM-055",
            "requires": ("blueprint:registry-topology",),
            "postconditions": ("all-registry-ids-come-from-blueprint",),
        },
    ),
}


def migrate(migration):
    migration.apply_robinhood_stage(MIGRATION_STAGE)
