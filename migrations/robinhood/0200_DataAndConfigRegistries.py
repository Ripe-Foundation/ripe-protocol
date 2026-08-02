MIGRATION_STAGE = {
    "migration_id": "0200",
    "semantic_id": "data-and-config-registries",
    "stage_kind": "deployment",
    "actions": (
        {
            "semantic_action_id": "deploy-ledger",
            "kind": "deployment",
            "operation": "deploy",
            "component_id": "CM-008",
            "artifact": "Ledger",
            "constructor": (
                "address:RIPE_HQ",
                "address:DEFAULTS_ROBINHOOD",
                "input:Deployment.DP-04.ledger.actionBlockSourceBinding",
            ),
            "provides": ("address:LEDGER",),
            "postconditions": ("ledger-deployed-from-empty-state", "no-base-ledger-state-import"),
        },
        {
            "semantic_action_id": "register-ledger",
            "kind": "registration",
            "operation": "register-and-confirm",
            "component_id": "CM-008",
            "registry_ref": "registry:ripe_hq:CM-008",
            "requires": ("address:LEDGER",),
            "abort_if": ("returned-registry-id-mismatch",),
            "postconditions": ("returned-registry-id-matches-authority",),
        },
        {
            "semantic_action_id": "deploy-mission-control",
            "kind": "deployment",
            "operation": "deploy",
            "component_id": "CM-009",
            "artifact": "MissionControl",
            "constructor": ("address:RIPE_HQ", "address:DEFAULTS_ROBINHOOD"),
            "provides": ("address:MISSION_CONTROL",),
            "postconditions": ("mission-control-deployed",),
        },
        {
            "semantic_action_id": "register-mission-control",
            "kind": "registration",
            "operation": "register-and-confirm",
            "component_id": "CM-009",
            "registry_ref": "registry:ripe_hq:CM-009",
            "requires": ("address:MISSION_CONTROL",),
            "abort_if": ("returned-registry-id-mismatch",),
            "postconditions": ("returned-registry-id-matches-authority",),
        },
    ),
}


def migrate(migration):
    migration.apply_robinhood_stage(MIGRATION_STAGE)
