# Track 6 S2: Checked Clock and Cadence Inventory

**Status:** Draft for owner review; do not launch until the owner approvals below are explicit

**Prepared:** 23 July 2026

**Planning baseline:** `758f45f5455fd7c05b25533d2d748769bcfc49c2`

## Fresh-agent instruction

Treat this document as the task contract. Implement only the checked clock-and-cadence inventory specified as Track 6 implementation slice S2. The result must make an unreviewed production `block.number`, indirect cadence dependency, timestamp-context change, or production import from test-only contracts fail deterministically.

This is tooling and test work only. Do not modify production contracts, defaults, parameter reports, migrations, manifests, ABI exports, dependency pins, CI workflows, or `docs/chains/rh-summary.md`. Do not change the semantic classification of an inventory ID merely to make the checker pass.

Use branch `rh-track-6-s2-clock-inventory`. Commit the validated deliverables to that branch with clear messages. Never push directly to or merge into `rh` or `master`; the owner reviews and integrates the work.

## Owner approvals required before kickoff

The fresh agent must verify explicit owner approval of this responsibility and integration posture:

- protocol/security owns the semantic classification and review of `BN-*`;
- risk/oracle owns the semantic classification and review of `CAD-*`;
- engineering/tooling maintains the checker implementation;
- S2 lands as a local script plus pytest coverage now; and
- a future CI integration must run the same commands, but this slice does not create a workflow or select a CI provider.

The repository currently has no committed `.github` workflow. Do not create one in S2.

If ownership or local-versus-CI posture is not approved, stop before implementation. Approval of this brief does not silently assign those responsibilities.

## Worktree bootstrap

The owner must first commit this approved brief to `rh`. The fresh agent is responsible for creating its own worktree:

1. Start from `/Users/wigglez/dev/ripe-protocol`.
2. Verify that:
   - the integration worktree is clean;
   - `rh` resolves to the owner-approved integration commit;
   - this brief exists in that commit;
   - `docs/chains/rh/block-number-inventory.md`, `docs/chains/rh/component-matrix.md`, `docs/chains/rh/shared-block-clock-specification.md`, and `docs/chains/rh/block-clock-validation-plan.md` exist in that commit; and
   - Track 6's reviewed specification cycle is closed.
3. Record the full starting commit and SHA-256 hashes of the four authoritative inputs.
4. Reproduce the integrated direct-occurrence baseline before creating the branch:
   - 100 exact production occurrences of `block.number`;
   - 95 matching production lines; and
   - 17 production files.
5. Confirm that branch `rh-track-6-s2-clock-inventory` and path `/Users/wigglez/dev/ripe-protocol-track-6-s2-clock-inventory` do not already exist. If either exists, stop and ask the owner; do not reuse, delete, reset, or overwrite it.
6. Create the isolated worktree:

   ```bash
   git -C /Users/wigglez/dev/ripe-protocol worktree add \
     -b rh-track-6-s2-clock-inventory \
     /Users/wigglez/dev/ripe-protocol-track-6-s2-clock-inventory \
     rh
   ```

7. Verify the new worktree's branch, commit, clean status, hashes, and baseline counts.
8. Run every subsequent command and make every edit inside `/Users/wigglez/dev/ripe-protocol-track-6-s2-clock-inventory`.

If the baseline differs, stop for inventory reconciliation. Do not update expected counts before explaining the source delta and obtaining the semantic owner's review.

## Exact file ownership

This slice may add only:

- `config/block-clock-inventory.json`;
- `scripts/check_block_clock_inventory.py`; and
- `tests/inventory/test_block_clock_inventory.py`.

If another file is required, stop and explain why. In particular, do not modify:

- anything under `contracts/`;
- the Track 3 or Track 6 source documents;
- parameter-generation or deployment tooling;
- dependency files;
- `.github` or other CI configuration; or
- the S1 harness files.

Use Python's standard library and dependencies already pinned by the repository. Do not add a parser dependency.

## Required reading

Read the current integrated versions of:

- `docs/chains/rh-summary.md`
- `docs/chains/rh/block-number-inventory.md`
- `docs/chains/rh/component-matrix.md`
- `docs/chains/rh/shared-block-clock-specification.md`
- `docs/chains/rh/block-clock-validation-plan.md`
- `docs/chains/rh/track-3-phase-0-inventory.md`
- `docs/chains/rh/track-6-shared-block-clock-specification.md`
- all 17 production contracts named in the clock inventory;
- `contracts/config/DefaultsBase.vy`
- `contracts/config/DefaultsLocal.vy`
- `config/BluePrint.py`
- `scripts/params/params_utils.py`
- `scripts/params/general.py`
- `scripts/params/regenerate_defaults.py`
- current generated parameter reports;
- `contracts/mock/`
- `contracts/testing/`
- representative repository Python scripts and tests; and
- ignore, packaging, and test configuration that affects path discovery.

The controlling Hightop Notes source is:

`/Users/wigglez/dev/hightop-notes/random/hood/hood-chain-executive-summary.md`

If the local checkout is unavailable, use the [GitHub copy](https://github.com/mickhagen/hightop-notes/blob/main/random/hood/hood-chain-executive-summary.md). If neither source is accessible, stop rather than silently skipping the selected architecture. Do not import the superseded federated design.

Use a fixed-string search such as `rg -F 'block.number'`. Do not present an unescaped regular-expression `.` match as a production count.

## Objective

Create one reviewed machine-readable ledger and one deterministic checker that:

- maps every direct production `block.number` occurrence to exactly one stable `BN-*` semantic record;
- preserves the Track 3 stable ID set `BN-001` through `BN-032`;
- records and checks `CAD-001` indirect cadence dependencies;
- records `TS-001` through `TS-011` as a separate timestamp-context domain;
- independently reconciles parser results with fixed-string occurrence, line, and file counts;
- distinguishes production, mock, live-probe/testing, ordinary tests, config, and tooling paths;
- detects direct, indirect, timestamp-context, classification, and import drift;
- makes suppression require semantic review rather than a new ID-shaped ignore;
- produces actionable path/function/line diagnostics; and
- can be invoked unchanged locally and by a future CI system.

## Phase A: Materialize schema version 1

Create `config/block-clock-inventory.json` with this top-level structure:

```json
{
  "schemaVersion": 1,
  "productionRoots": ["contracts"],
  "excludedProductionGlobs": [
    "contracts/mock/**",
    "contracts/testing/**"
  ],
  "directOccurrences": [
    {
      "id": "BN-001",
      "path": "contracts/tokens/modules/Erc20Token.vy",
      "function": "initiateHqChange",
      "normalizedExpression": "block.number",
      "ordinalInFunction": 1,
      "semanticReview": {
        "owner": "protocol",
        "status": "reviewed",
        "commit": "..."
      }
    }
  ],
  "indirectCadence": [],
  "timestampContext": [],
  "allowedNonProductionGlobs": [
    "tests/**",
    "contracts/mock/**",
    "contracts/testing/**"
  ]
}
```

Extend records only where the integrated inventory requires information such as component IDs, category, expression role, or source reference. Keep the schema deterministic and versioned; do not copy narrative prose that the checker cannot validate.

`contracts/mock/**` and `contracts/testing/**` intentionally appear in both lists. `excludedProductionGlobs` removes them from production occurrence, line, and file denominators; `allowedNonProductionGlobs` separately declares that these reviewed non-production paths may exist and must be discovered, classified, and reported. The checker and schema documentation must preserve this distinction so a future cleanup does not incorrectly “deduplicate” the entries or stop scanning them.

### Stable identity

The direct-occurrence key is:

```text
path + function + normalizedExpression + ordinalInFunction
```

- Line number is a diagnostic, never identity.
- Parse Vyper function boundaries.
- Normalize whitespace only; do not algebraically rewrite an expression.
- An ordinal is scoped to the function and normalized expression.
- Moving an occurrence within its function is reported as a move requiring review.
- Renaming a function, changing an expression, adding/removing an occurrence, or changing its ordinal is unmapped until reviewed.
- Multiple exact occurrences on one source line remain separately mapped.

Do not renumber stable IDs. Preserve the integrated many-occurrences-to-one-semantic-ID relationships where Track 3 intentionally grouped a semantic behavior.

### Semantic review

Every direct, indirect, and timestamp-context record must carry a non-placeholder review owner, status, and commit or equivalent immutable source reference.

Reject:

- empty values;
- `TODO`, `TBD`, `unknown`, `n/a`, or equivalent placeholders;
- an `ignore` status without a semantic owner and justification; or
- a self-approved classification invented only to satisfy this slice.

If a Track 3 record lacks enough reviewed information to populate the schema honestly, stop and request reconciliation.

## Phase B: Implement deterministic discovery

Implement `scripts/check_block_clock_inventory.py` so it:

1. resolves the repository root without depending on the caller's current directory;
2. walks declared roots deterministically;
3. applies path classifications explicitly;
4. parses Vyper function boundaries sufficiently for the current source;
5. locates and maps exact `block.number` occurrences;
6. performs an independent fixed-string count of occurrences, matching lines, and files;
7. scans indirect cadence patterns;
8. scans timestamp-context patterns separately;
9. validates the JSON schema and stable IDs; and
10. exits nonzero with deterministic diagnostics on drift.

Do not rely on network access, git state beyond optional diagnostics, generated caches, locale-dependent ordering, or nondeterministic object traversal.

### Required baseline

On the approved starting commit, require:

- 100 exact production `block.number` occurrences;
- 95 production lines containing the fixed string;
- 17 production files containing the fixed string;
- semantic IDs `BN-001` through `BN-032`;
- indirect cadence ID `CAD-001`; and
- timestamp-context IDs `TS-001` through `TS-011`.

Report non-production counts separately. Do not let `contracts/mock/**`, `contracts/testing/**`, or `tests/**` change the production denominator.

### Path classification

- `contracts/**` is production unless an approved exclusion matches.
- `contracts/mock/**` is non-production mock code.
- `contracts/testing/**` is non-production probe/test code that may be deployed for controlled evidence.
- `tests/**` is test code.
- Moving a file across classifications requires review.
- A production contract must never import from `contracts/mock/**` or `contracts/testing/**`.
- An unclassified Vyper path under the repository must be reported rather than silently treated as safe.

A new cadence dependency inside an excluded contract appears in the report and requires probe/mock review, but it does not change the production 100/95/17 baseline.

## Phase C: Check indirect cadence and timestamp context

The checker must cover the integrated `CAD-001` surface and look for newly introduced cadence patterns in production/config/migration/tooling paths, including:

- identifiers ending or containing `IN_BLOCKS`;
- identifiers containing `BLOCKS`;
- `ONE_DAY`;
- `staleBlocks`;
- `numBlocksPerInterval`;
- `ripePerBlock`;
- `increasePerDangerBlock`;
- comments that state block seconds, daily conversions, Base cadence, or Robinhood cadence;
- per-chain defaults and constructor values;
- generated parameter-report metadata or denominators; and
- aliases or arithmetic that convert wall time to block counts.

Use reviewed pattern definitions, not a single overbroad regex that makes the tool unusable. New candidates may require triage, but they may not disappear merely because they do not yet have an ID.

Keep `block.timestamp`, `*_IN_SECONDS`, and the `TS-*` context inventory separate from the direct/cadence denominator. Detect:

- a new timestamp use in a production contract;
- removal or movement of a reviewed timestamp context;
- mixed NUMBER/timestamp arithmetic;
- a seconds constant renamed into ambiguous block units; and
- a new dependency that crosses the two domains.

S2 guards the audited context. It does not convert timestamp logic or decide whether a new use is valid.

## Phase D: Diagnostics and command interface

Support:

```bash
PYTHONPATH=. python scripts/check_block_clock_inventory.py --check
```

The successful result must be concise and include schema version, direct occurrence/line/file totals, stable-ID totals, indirect/timestamp totals, and separate non-production counts.

Every failure must include, when applicable:

- source path;
- function;
- current line;
- normalized snippet;
- candidate stable ID;
- direct, indirect, timestamp, classification, or import domain;
- active expected and actual counts; and
- a remediation that calls for semantic review rather than suppression.

Use stable machine-searchable prefixes or error codes so tests and future CI can distinguish failure classes. Do not include secrets or full unrelated files.

The script must fail on:

- unmapped direct addition;
- missing direct occurrence;
- duplicate or ambiguous mapping;
- moved occurrence requiring review;
- stale occurrence, line, or file count;
- new or missing indirect pattern;
- new or missing timestamp context;
- duplicate, malformed, skipped, or placeholder schema record;
- an ignore without reviewed justification;
- unclassified contract path;
- production import from a mock/testing path; or
- parser results that disagree with independent fixed-string totals.

## Phase E: Mutation tests

Build `tests/inventory/test_block_clock_inventory.py` around temporary repository fixtures or another isolated standard-library technique. Tests must never mutate the real checkout.

Include mutations that:

- add a direct occurrence;
- remove a direct occurrence;
- place two exact occurrences on one line;
- move an occurrence within a function;
- rename its function;
- change the normalized expression;
- duplicate a schema mapping;
- introduce a new indirect cadence identifier;
- remove or change `CAD-001`;
- add a timestamp context;
- mix block and timestamp units;
- add a new production Vyper path;
- move a file into or out of `contracts/testing/**`;
- add a cadence use to a mock or testing contract and verify separate reporting;
- import a testing or mock contract from production;
- add a placeholder semantic review;
- add an unreviewed ignore; and
- create a parser/fixed-string disagreement.

Each mutation must fail for the intended reason and include useful diagnostics. Also prove:

- clean approved fixtures pass;
- discovery order does not change output;
- the command works outside the repository root;
- malformed JSON and unsupported schema versions fail;
- output and exit status are deterministic; and
- no network or git-branch assumption is required.

## Approval and safety boundaries

The agent may:

- read repository and public-source material;
- implement and test the three owned files;
- report a semantic inconsistency for owner resolution;
- recommend a narrowly scoped checker design; and
- commit validated work to the S2 branch.

The agent may not without fresh owner approval:

- change an inventory classification or ownership decision;
- alter or renumber a Track 3 stable ID;
- update a baseline merely because code drifted;
- add a dependency;
- modify production code or generated outputs;
- create or edit CI configuration;
- sign or broadcast a transaction;
- contact an external party; or
- mark a `rh-summary.md` checkbox complete.

## Stop conditions

Stop and report evidence if:

- the starting direct baseline is not 100 occurrences, 95 lines, and 17 files;
- the integrated narrative cannot be represented without changing semantic meaning;
- a production occurrence cannot map uniquely;
- the parser can suppress a fixed-string delta;
- a path can evade classification;
- a production import can reach mock/testing code;
- robust implementation requires a new dependency;
- Track 3 or Track 6 inputs materially changed after the recorded baseline;
- another branch concurrently changes an owned file; or
- achieving a green result would require a placeholder, ignore, or weakened mutation test.

## Validation

Run, in order:

```bash
PYTHONPATH=. python scripts/check_block_clock_inventory.py --check
PYTHONPATH=. pytest -q tests/inventory/test_block_clock_inventory.py
PYTHONPATH=. pytest -q
git diff --check
```

Also:

- [ ] Confirm the clean baseline is exactly 100 occurrences / 95 lines / 17 files.
- [ ] Confirm all 32 BN IDs, CAD-001, and all 11 TS IDs validate.
- [ ] Confirm excluded paths are separately counted and production imports are prohibited.
- [ ] Confirm every required mutation fails for the intended reason.
- [ ] Confirm the script runs from outside the repository root.
- [ ] Confirm only the three approved paths changed.
- [ ] Record commands, durations, starting commit, input hashes, and final commit.

If the full suite has a pre-existing failure, reproduce it on the untouched starting commit and clearly separate it from S2. Do not weaken or skip existing tests.

## Completion report

The final handoff must include:

- starting and final commit;
- exact changed files;
- owner approvals relied upon;
- schema and stable-key summary;
- reproduced production and non-production counts;
- mutation-test matrix;
- validation commands and results;
- any pre-existing failures;
- stop conditions encountered;
- future CI wiring left open; and
- which Track 6 S2 / Section 2 items are **eligible for owner review**.

Do not edit or tick `docs/chains/rh-summary.md`. The owner decides whether the checked-inventory requirement is complete after review and integration.
