"""`verify_defaults.py` must check every value a contract copies from Defaults.

A generated defaults contract is consumed at construction by two contracts, and
`verify_defaults.py` originally rebuilt only one of them. So a generated file
could reproduce `MissionControl` exactly, pass verification, and still hand a
replacement `Ledger` the wrong `ripeAvailForRewards`, `ripeAvailForHr` and
`ripeAvailForBonds` -- the RIPE budgets for rewards, HR and bonds. Nothing
would have said so.

That instance is fixed. This module exists so the *class* does not recur: the
gap was invisible because the verifier's coverage was a hand-maintained list
with nothing tying it to the contracts it claims to cover. Add a fourth
`staticcall Defaults(...)` to `Ledger`, or a new consumer entirely, and the
verifier silently keeps reporting success over a field it never reads.

So the contracts are the authority here, not the script. Both checks parse the
Vyper sources for `staticcall Defaults(_defaults).<name>()` and require the
script to account for what they find.

Offline and cheap: reads three files, compiles nothing, forks nothing. The
verifier itself cannot be exercised here -- it forks a live network at a pinned
block and needs an RPC endpoint -- which is exactly why the part that *can* be
checked without one should be.
"""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"
VERIFY_DEFAULTS = ROOT / "scripts" / "verify_defaults.py"

DEFAULTS_READ_RE = re.compile(
    r"staticcall\s+Defaults\(\s*_defaults\s*\)\s*\.\s*(\w+)\s*\("
)


def _defaults_reads(path: Path) -> set[str]:
    return set(DEFAULTS_READ_RE.findall(path.read_text()))


def _consumers() -> dict[str, set[str]]:
    """{contract path: fields it copies from Defaults} for every consumer."""
    found = {}
    for path in sorted(CONTRACTS.rglob("*.vy")):
        reads = _defaults_reads(path)
        if reads:
            found[path.relative_to(ROOT).as_posix()] = reads
    return found


def test_ledger_fields_are_all_covered_by_the_verifier():
    ledger = _defaults_reads(CONTRACTS / "data" / "Ledger.vy")
    assert ledger, (
        "Ledger.vy no longer reads Defaults at construction; if that moved, "
        "this module and verify_defaults.py both need repointing"
    )

    source = VERIFY_DEFAULTS.read_text()
    match = re.search(r"LEDGER_GETTERS = \(([^)]*)\)", source, re.S)
    assert match, "verify_defaults.py has no LEDGER_GETTERS tuple"
    covered = set(re.findall(r'"(\w+)"', match.group(1)))

    assert ledger <= covered, (
        f"Ledger copies {sorted(ledger - covered)} from Defaults, which "
        "verify_defaults.py does not check. A generated defaults file could "
        "pass verification while a replacement Ledger comes up holding the "
        "wrong value."
    )


def test_no_third_consumer_of_defaults_goes_unverified():
    # The verifier rebuilds MissionControl and Ledger. A new consumer would be
    # unverified by construction, and the script has no way to notice.
    consumers = _consumers()
    expected = {"contracts/data/Ledger.vy", "contracts/data/MissionControl.vy"}

    assert set(consumers) == expected, (
        f"the set of contracts reading Defaults at construction changed to "
        f"{sorted(consumers)}. verify_defaults.py rebuilds only "
        f"{sorted(expected)}, so anything new here is unverified -- extend the "
        "script and this test together."
    )


def test_mission_control_fields_are_all_reachable_from_the_verifier():
    # Weaker than the Ledger check by necessity: MissionControl's getters are
    # not all named after the field they hold. Three renaming shapes are real
    # and none of them is a coverage gap:
    #
    #   priorityLiqAssetVaults  -> getPriorityLiqAssetVaults  (get- prefix)
    #   assetConfigs            -> assetConfig(asset)          (plural list on
    #   ripeGovVaultConfigs     -> ripeGovVaultConfig(asset)    Defaults, per-item
    #                                                           getter on MC)
    #
    # So this asserts the script reaches each copied field under one of those
    # spellings, rather than that it appears in a single exact tuple.
    fields = _defaults_reads(CONTRACTS / "data" / "MissionControl.vy")
    assert len(fields) > 5, f"only found {len(fields)} Defaults reads; regex drift?"

    source = VERIFY_DEFAULTS.read_text()

    def reached(field: str) -> bool:
        candidates = {field, field.removeprefix("priority")}
        if field.endswith("s"):
            candidates.add(field[:-1])
        return any(candidate in source for candidate in candidates)

    missing = sorted(field for field in fields if not reached(field))
    assert not missing, (
        f"MissionControl copies {missing} from Defaults and verify_defaults.py "
        "never mentions them"
    )
