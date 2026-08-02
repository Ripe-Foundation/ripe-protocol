MIGRATION_STAGE = {
    "migration_id": "0070",
    "semantic_id": "track6-s9-disabled-integration-assertions",
    "stage_kind": "assertion",
    "actions": (
        {
            "semantic_action_id": "assert-omitted-components-absent",
            "kind": "omission",
            "operation": "assert-selection-state-absent",
            "selection_state": "omitted",
            "postconditions": ("every-omitted-component-is-absent",),
        },
        {
            "semantic_action_id": "assert-deferred-components-absent",
            "kind": "deferred",
            "operation": "assert-selection-state-absent",
            "selection_state": "deferred",
            "postconditions": ("every-deferred-component-is-absent",),
        },
        {
            "semantic_action_id": "assert-ccip-stage-absent",
            "kind": "deferred",
            "operation": "assert-migration-absent",
            "postconditions": ("migration-1000-is-not-executable-source",),
        },
        {
            "semantic_action_id": "assert-disabled-routes-absent",
            "kind": "omission",
            "operation": "assert-feature-family-absent",
            "feature_families": (
                "curve-lp-collateral",
                "curve-lp-valuation",
                "curve-psm-authority",
                "curve-dynamic-rates",
                "teller-green-reference-snapshots",
                "endaoment-stabilization",
                "ripe-weth-lp-admission",
                "uniswap-accounting",
            ),
            "postconditions": ("inactive-feature-families-have-no-actions",),
        },
    ),
}


def migrate(migration):
    migration.apply_robinhood_stage(MIGRATION_STAGE)
