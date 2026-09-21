"""The diagnostic must exercise new HR without replacing Endaoment."""

from types import SimpleNamespace

import pytest

from scripts.utils.legacy_vault_gas import REPLACEMENT_ROLES, verify_department_graph

HR = "0x" + "15" * 20
ENDAOMENT = "0x" + "14" * 20
OLD_HR = "0x" + "01" * 20


@pytest.mark.parametrize(
    "fault", ["none", "old_hr", "wrong_inverse", "disabled", "clobbered_endaoment"]
)
def test_department_graph_rejects_wrong_hr_and_retained_identity(fault):
    assert REPLACEMENT_ROLES[15] == "HumanResources" and 14 not in REPLACEMENT_ROLES
    rows = {14: ENDAOMENT, 15: HR}
    if fault == "old_hr":
        rows[15] = OLD_HR
    if fault == "clobbered_endaoment":
        rows[14] = HR
    hq = SimpleNamespace(
        getAddr=lambda slot: rows[slot],
        getRegId=lambda target: 14 if fault == "wrong_inverse" else 15,
        isValidRegId=lambda slot: fault != "disabled",
    )
    if fault == "none":
        verify_department_graph(hq, {15: HR}, ENDAOMENT)
    else:
        with pytest.raises(RuntimeError, match="GAS_"):
            verify_department_graph(hq, {15: HR}, ENDAOMENT)
