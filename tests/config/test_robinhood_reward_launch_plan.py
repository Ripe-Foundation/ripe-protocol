"""`config/robinhood-reward-launch-plan.json` is the preimage of an approved input.

`Deployment.DP-15.rewards.promotion` is not a value, it is a **commitment to a
document**: `config/BluePrint.py` records it as
`RobinhoodInput('f84bb555…d51234', 'approved')`, `config/robinhood-parameters.json`
carries the same digest under `unit: {"kind": "hash"}` on record `P-H04-399`, and
that record's `source.citation` names this JSON file by path. The bytes on disk
are the thing an owner approved on 2026-08-01; the digest is only a handle for
them.

This module exists because an earlier revision of the codebase-simplification
branch deleted the JSON as "a self-contained island -- no migration reads the
plan, and the packet it validates records `deployment_authorized=false`". Both
clauses were true and neither was relevant. Nothing *executes* an approval
packet; it is evidence, not code, and a packet recording that deployment is
**not** authorized is still the approved record of that decision. Deleting it
left an `approved` governance input whose preimage did not exist, a `unit: hash`
with nothing to hash, and a citation pointing at a missing path -- an approval
that could no longer be falsified by anything.

The deletion was invisible to the suite for two compounding reasons, both worth
keeping in mind during release qualification: the test that checked the digest
was deleted alongside the file, and it had already been deselected from the
default lane. This module is release-marked because it binds a committed
approval artifact rather than exercising contract behavior.

What survived the deletion was an assertion in
`tests/deployment/test_stock_aapl_launch_inclusion.py` that compares
`ROBINHOOD_DEPLOYMENT_INPUTS[...].value` to a hex literal copied from
`BluePrint.py`. That proves the constant was not edited. It cannot detect a
missing, truncated, or altered packet, because it never touches one. So no
expected digest is written literally below: the hash is computed from the file
and reconciled against both authorities that claim it, and any of the three
drifting apart fails here.

Not restored with it: `scripts/params/validate_robinhood_reward_launch_plan.py`,
a 424-line semantic validator whose only callers were the deleted tests. Its
per-leaf mutation sweep is subsumed by the digest for a frozen artifact -- every
mutation it could construct changes the bytes, and the bytes are pinned here.
Recoverable at `2b3a718^` if the packet ever becomes editable again.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from config.BluePrint import ROBINHOOD_DEPLOYMENT_INPUTS


pytestmark = pytest.mark.release


ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "config" / "robinhood-reward-launch-plan.json"
LEDGER = ROOT / "config" / "robinhood-parameters.json"

INPUT_PATH = "Deployment.DP-15.rewards.promotion"
LEDGER_RECORD_ID = "P-H04-399"


@pytest.fixture(scope="session")
def ripe_hq() -> None:
    """Override the repository autouse deployment fixture for source checks."""


def _ledger_record(record_id: str) -> dict:
    ledger = json.loads(LEDGER.read_bytes())
    return next(row for row in ledger["parameters"] if row["id"] == record_id)


def test_packet_digest_reconciles_with_both_authorities_that_claim_it():
    # Computed, never quoted. A literal here would reproduce the defect this
    # module exists to close: an expected value that agrees with BluePrint
    # because it was copied from BluePrint.
    digest = hashlib.sha256(PLAN.read_bytes()).hexdigest()

    approved_input = ROBINHOOD_DEPLOYMENT_INPUTS[INPUT_PATH]
    assert approved_input.disposition == "approved"
    assert approved_input.value == digest, (
        f"{INPUT_PATH} is approved at {approved_input.value}, but the packet on "
        f"disk hashes to {digest}. Either the packet changed after approval, or "
        "the input was repointed at content no owner approved."
    )

    record = _ledger_record(LEDGER_RECORD_ID)
    assert record["destination"]["path"] == INPUT_PATH
    assert record["unit"] == {"kind": "hash"}
    assert record["status"] == "approved"
    assert record["value"] == {"kind": "concrete", "raw": digest}, (
        f"{LEDGER_RECORD_ID} binds {record['value']}, which disagrees with the "
        f"packet digest {digest}."
    )


def test_the_cited_evidence_path_resolves():
    # The failure this catches directly: the citation named a file the tree no
    # longer contained, so the approval referenced evidence that was gone.
    citation = _ledger_record(LEDGER_RECORD_ID)["source"]["citation"]
    cited = [
        token.strip().rstrip(".,;")
        for token in citation.replace(" and ", " ").split()
        if token.strip().rstrip(".,;").endswith((".json", ".md"))
    ]
    assert cited, f"{LEDGER_RECORD_ID} cites no artifact path: {citation!r}"

    missing = sorted(path for path in cited if not (ROOT / path).is_file())
    assert not missing, (
        f"{LEDGER_RECORD_ID} cites {missing}, which are absent from the tree. "
        "An approval that cites missing evidence cannot be checked against "
        "anything."
    )
    assert PLAN.relative_to(ROOT).as_posix() in cited


def test_the_approved_packet_grants_no_lifecycle_authority():
    # What was actually approved, asserted rather than summarised. The original
    # deletion read `deployment_authorized=false` as evidence the packet was
    # inert; it is the opposite -- the packet is the approved record of a
    # product decision that deliberately withholds deployment authority, and
    # those two facts are what make it worth keeping.
    packet = json.loads(PLAN.read_bytes())["packet"]

    assert packet["owner_acceptance"] == "approved"
    assert packet["identity_effect"] == (
        "approved_product_decision_binding_no_lifecycle_authority"
    )
    assert packet["is_configuration_authority"] is False
    assert packet["deployment_authorized"] is False
    assert packet["activation_authorized"] is False
