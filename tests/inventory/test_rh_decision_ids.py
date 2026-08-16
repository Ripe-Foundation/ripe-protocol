import pytest

from scripts import check_rh_decision_ids as decisions


def test_rh_decision_register_has_unique_ids():
    decisions.parse_register(
        decisions.REGISTER.read_text(), str(decisions.REGISTER)
    )


def test_duplicate_register_id_fails_closed():
    with pytest.raises(decisions.DecisionIdError, match="duplicate decision ID"):
        decisions.parse_register(
            "### RH-D038 — First\n### RH-D038 — Second\n",
            "mutant",
        )


def test_integration_collision_with_base_or_sibling_fails_closed():
    base = {"RH-D033": "Base decision"}
    with pytest.raises(decisions.DecisionIdError, match="base_conflicts"):
        decisions.require_unique_integration_claims(
            base,
            {"pr145": {"RH-D033": "Different decision"}},
        )
    with pytest.raises(decisions.DecisionIdError, match="duplicate_claims"):
        decisions.require_unique_integration_claims(
            base,
            {
                "pr145": {"RH-D038": "Deleverage"},
                "pr147": {"RH-D038": "Endaoment"},
            },
        )
