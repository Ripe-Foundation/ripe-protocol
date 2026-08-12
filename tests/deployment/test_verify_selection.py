"""Selecting which contracts to verify.

Verification is a separate, manual step from deployment on purpose -- submitting
is its own failure surface. But a manifest holds every contract ever deployed to
a chain, so verifying "the thing I just shipped" meant re-submitting all 50.

`verify` reads the current manifest for what it submits, and uses the numbered
step manifests only to attribute each live address to the migration that
deployed it, so a run can be scoped to one migration or an explicit list.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from scripts import verify


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def ripe_hq() -> None:
    """Keep this suite independent of protocol deployment."""


def _current(chain="base-mainnet", environment="v1"):
    path = ROOT / f"migration_history/{chain}/{environment}/current-manifest.json"
    return json.loads(path.read_text())["contracts"]


def _rows_for(chain="base-mainnet", environment="v1"):
    return verify._rows(
        _current(chain, environment), verify._migration_owners(chain, environment)
    )


# --- attribution -----------------------------------------------------------


@pytest.mark.parametrize("chain", ("base-mainnet", "robinhood-mainnet"))
def test_every_live_contract_is_attributed_to_a_migration(chain):
    rows = _rows_for(chain)
    assert rows
    unattributed = [row["name"] for row in rows if row["migration"] is None]
    assert not unattributed, unattributed


def test_attribution_follows_the_address_not_the_name():
    """A redeployed contract belongs to the step holding its *live* address."""
    history = ROOT / "migration_history/base-mainnet/v1"
    owners = verify._migration_owners("base-mainnet", "v1")

    # Find a contract that appears in more than one step manifest.
    seen = {}
    for path in sorted(history.glob("[0-9]*-manifest.json")):
        stamp = path.name.split("-", 1)[0]
        for name, record in json.loads(path.read_text())["contracts"].items():
            seen.setdefault(name, []).append((stamp, record.get("address")))
    redeployed = {n: v for n, v in seen.items() if len({a for _, a in v}) > 1}
    assert redeployed, "expected at least one redeployed contract"

    name = sorted(redeployed)[0]
    live = _current()[name]["address"]
    owning = owners[(name, live)]
    superseded = {s for s, a in redeployed[name] if a != live}
    assert owning not in superseded or len(superseded) == 0


# --- selection parsing -----------------------------------------------------


def test_all_skips_contracts_that_cannot_be_submitted():
    rows = _rows_for()
    chosen = verify._parse_selection("all", rows)

    assert chosen
    assert all(rows[i]["verifiable"] for i in chosen)
    assert len(chosen) == sum(1 for r in rows if r["verifiable"])


@pytest.mark.parametrize("text", ("", "none", "q", "quit"))
def test_empty_selections_choose_nothing(text):
    assert verify._parse_selection(text, _rows_for()) == []


def test_indexes_and_ranges():
    rows = _rows_for()
    assert verify._parse_selection("1", rows) == [0]
    assert verify._parse_selection("1,3", rows) == [0, 2]
    assert verify._parse_selection("2-5", rows) == [1, 2, 3, 4]
    # reversed ranges and duplicates are tolerated, not silently wrong
    assert verify._parse_selection("5-2", rows) == [1, 2, 3, 4]
    assert verify._parse_selection("1,1,2", rows) == [0, 1]


def test_migration_selector_matches_the_step():
    rows = _rows_for()
    stamp = next(r["migration"] for r in rows if r["migration"])
    chosen = verify._parse_selection(f"m:{stamp}", rows)

    assert chosen
    assert {rows[i]["migration"] for i in chosen} == {stamp}
    assert verify._parse_selection(f"migration:{stamp}", rows) == chosen


@pytest.mark.parametrize(
    ("text", "message"),
    (
        ("0", "Out of range"),
        ("9999", "Out of range"),
        ("nope", "Not a number"),
        ("1-x", "Not a range"),
        ("m:00000000", "No contracts"),
    ),
)
def test_bad_selections_fail_closed(text, message):
    with pytest.raises(Exception) as captured:
        verify._parse_selection(text, _rows_for())
    assert message in str(captured.value)


# --- the CLI submits only what was selected --------------------------------


@pytest.fixture
def submissions(monkeypatch):
    seen = []

    def fake(api_key, contract_name, manifest_data, chain):
        seen.append(contract_name)
        return True

    monkeypatch.setattr(verify, "verify_from_manifest", fake)
    monkeypatch.setattr(verify.time, "sleep", lambda *_: None)
    monkeypatch.setenv("ETHERSCAN_API_KEY", "probe")
    return seen


def _invoke(*args, stdin=None):
    return CliRunner().invoke(
        verify.cli,
        ["--chain", "base-mainnet", "--environment", "v1", *args],
        input=stdin,
    )


def test_migration_flag_submits_only_that_migrations_contracts(submissions):
    rows = _rows_for()
    stamp = next(
        r["migration"] for r in rows if r["migration"] and r["verifiable"]
    )
    expected = [r["name"] for r in rows if r["migration"] == stamp]

    result = _invoke("--migration", stamp)

    assert result.exit_code == 0, result.output
    assert submissions == expected
    assert len(submissions) < len(rows)


def test_contracts_flag_submits_exactly_those(submissions):
    result = _invoke("--contracts", "GreenToken,RipeToken")

    assert result.exit_code == 0, result.output
    assert submissions == ["GreenToken", "RipeToken"]


def test_all_flag_submits_every_verifiable_contract(submissions):
    rows = _rows_for()

    result = _invoke("--all")

    assert result.exit_code == 0, result.output
    assert submissions == [r["name"] for r in rows if r["verifiable"]]


def test_checklist_default_submits_nothing(submissions):
    result = _invoke(stdin="\n")

    assert result.exit_code == 0, result.output
    assert submissions == []
    assert "Nothing selected" in result.output


def test_checklist_selection_requires_confirmation(submissions):
    # "1" selects one contract, then the confirm prompt is declined.
    result = _invoke(stdin="1\nn\n")

    assert submissions == []
    assert "Submitting 1 of" in result.output


def test_checklist_selection_submits_after_confirmation(submissions):
    result = _invoke(stdin="1\ny\n")

    assert result.exit_code == 0, result.output
    assert submissions == [_rows_for()[0]["name"]]


def test_failed_submission_exits_nonzero(monkeypatch):
    monkeypatch.setattr(verify, "verify_from_manifest", lambda **_: False)
    monkeypatch.setattr(verify.time, "sleep", lambda *_: None)
    monkeypatch.setenv("ETHERSCAN_API_KEY", "probe")

    result = _invoke("--contracts", "GreenToken")

    assert result.exit_code != 0
    assert "Verification failed for: GreenToken" in result.output
