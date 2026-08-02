MIGRATION_STAGE = {
    "migration_id": "0060",
    "semantic_id": "track6-s8-lifecycle-capacity",
    "stage_kind": "assertion",
    "actions": (
        {
            "semantic_action_id": "assert-lifecycle-capacity",
            "kind": "assertion",
            "operation": "assert-artifact-capacity",
            "component_id": "CM-059",
            "requires": ("binding:artifact-capacity-freeze",),
            "postconditions": ("selected-artifacts-fit-lifecycle-capacity",),
        },
        {
            "semantic_action_id": "assert-deployment-activation-separation",
            "kind": "assertion",
            "operation": "assert-lifecycle-separation",
            "component_id": "CM-059",
            "postconditions": ("deployment-does-not-imply-activation",),
        },
    ),
}


def migrate(migration):
    migration.apply_robinhood_stage(MIGRATION_STAGE)
