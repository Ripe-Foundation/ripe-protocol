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
    """Record submissions instead of making them.

    The CLI is driven through `cli.callback` rather than click.testing's
    CliRunner, so this suite does not import Click's testing surface. Other
    suites here shell out with subprocess for the same reason, which cannot
    intercept the submission call.
    """
    seen = []
    monkeypatch.setattr(
        verify,
        "verify_from_manifest",
        lambda api_key, contract_name, manifest_data, chain: seen.append(
            contract_name
        )
        or True,
    )
    monkeypatch.setattr(verify.time, "sleep", lambda *_: None)
    monkeypatch.setenv("ETHERSCAN_API_KEY", "probe")
    return seen


def _invoke(monkeypatch=None, *, answer=None, confirm=None, **kwargs):
    if answer is not None:
        monkeypatch.setattr(verify.click, "prompt", lambda *a, **k: answer)
    if confirm is not None:
        def _confirm(*a, **k):
            if not confirm:
                raise verify.click.exceptions.Abort()
            return True

        monkeypatch.setattr(verify.click, "confirm", _confirm)
    return verify.cli.callback(
        "v1", "base-mainnet", "current", **kwargs
    )


def test_migration_flag_submits_only_that_migrations_contracts(submissions):
    rows = _rows_for()
    stamp = next(
        r["migration"] for r in rows if r["migration"] and r["verifiable"]
    )
    expected = [r["name"] for r in rows if r["migration"] == stamp]

    _invoke(migration=stamp)

    assert submissions == expected
    assert len(submissions) < len(rows)


def test_contracts_flag_submits_exactly_those(submissions):
    _invoke(contracts="GreenToken,RipeToken")

    assert submissions == ["GreenToken", "RipeToken"]


def test_all_flag_submits_every_verifiable_contract(submissions):
    rows = _rows_for()

    _invoke(verify_all=True)

    assert submissions == [r["name"] for r in rows if r["verifiable"]]


def test_checklist_default_submits_nothing(submissions, monkeypatch):
    _invoke(monkeypatch, answer="none")

    assert submissions == []


def test_checklist_selection_requires_confirmation(submissions, monkeypatch):
    with pytest.raises(verify.click.exceptions.Abort):
        _invoke(monkeypatch, answer="1", confirm=False)

    assert submissions == []


def test_checklist_selection_submits_after_confirmation(submissions, monkeypatch):
    _invoke(monkeypatch, answer="1", confirm=True)

    assert submissions == [_rows_for()[0]["name"]]


def test_failed_submission_exits_nonzero(monkeypatch):
    monkeypatch.setattr(verify, "verify_from_manifest", lambda **_: False)
    monkeypatch.setattr(verify.time, "sleep", lambda *_: None)
    monkeypatch.setenv("ETHERSCAN_API_KEY", "probe")

    with pytest.raises(verify.click.ClickException) as captured:
        _invoke(contracts="GreenToken")

    assert "Verification failed for: GreenToken" in str(captured.value)


def test_step_manifest_redirects_to_the_migration_selector(monkeypatch):
    """A numbered manifest is a record, not a payload.

    Owner decision: `solc_json` lives in `current-manifest.json` alone. So
    pointing --manifest at a step manifest can never verify anything, and
    should say why once rather than listing every contract as unverifiable.
    The redirect names the flag that does what the caller wanted.
    """
    monkeypatch.setenv("ETHERSCAN_API_KEY", "probe")
    monkeypatch.setattr(
        verify, "verify_from_manifest", lambda **_: pytest.fail("submitted")
    )

    with pytest.raises(verify.click.ClickException) as captured:
        verify.cli.callback("v1", "base-mainnet", "2026072800")

    message = str(captured.value)
    assert "is a step manifest" in message
    assert "--migration 2026072800" in message


def test_the_redirect_names_a_selector_that_works(submissions):
    # Whatever the redirect suggests has to actually be selectable.
    _invoke(migration="2026072800")

    assert submissions == ["AuctionHouse", "Deleverage"]
