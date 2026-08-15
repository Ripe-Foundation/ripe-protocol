import pytest

from scripts import check_rh_decision_ids as decisions


def test_rh_decision_register_and_status_have_exact_unique_pairs():
    register = decisions.parse_register(
        decisions.REGISTER.read_text(), str(decisions.REGISTER)
    )
    status = decisions.parse_status(decisions.STATUS)
    decisions.require_exact_parity(register, status)
    assert register["RH-D038"] == (
        "SC-07/SC-09 Deleverage remediation is reopened and bounded"
    )


def test_rh_decision_count_excludes_only_fully_retired_ids():
    status = decisions.parse_status(decisions.STATUS)
    assert decisions.require_count_consistency(decisions.STATUS, status) == (
        len(status) - len(decisions.FULLY_RETIRED_DECISION_IDS)
    )


def test_stale_rh_decision_count_fails_closed(tmp_path):
    status_path = tmp_path / "status.yaml"
    status_path.write_text(
        "counts:\n"
        "  rh_d_decisions: 33\n"
        "decisions:\n"
        '  - { id: RH-D026, title: "Retired" }\n'
        '  - { id: RH-D038, title: "Active" }\n'
    )
    status = decisions.parse_status(status_path)
    with pytest.raises(decisions.DecisionIdError, match="expected 1"):
        decisions.require_count_consistency(status_path, status)


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
