# Shared Stock Token Vault-Change Specification

Status: **Owner-directed minimum-change initial-launch proposal complete for
review; Stock Tokens are mandatory launch scope; no production code, vault/ID,
implementation, migration, deployment, live configuration, or transaction is
authorized**

Date: 2026-07-24 (America/Denver)

This document is the Track 8 working specification required by
`track-8-stock-token-vault-change.md`. It records the evidence reconciliation,
formal state and invariant model, architecture comparison, mandatory early
owner checkpoint, exact deposit-accounting design, and backing/debt-health
design, plus the settlement/liquidation/total-loss and corrected share-vault
designs, the Phase H current-control, governance, clock, and operational
evidence analysis, the Phase I compatibility and migration inventory, the
Phase J validation contract, and the Phase K reviewable implementation units
and atomic Release 0/1/2 gates. Section 23 is the later owner-directed,
launch-critical refinement: it reduces that comprehensive design to the
smallest demonstrably sufficient containment proposal. It does not authorize a
production vault or ID, implementation, migration, deployment, live
configuration, or any transaction.

The owner-confirmed direction now makes Stock Tokens a mandatory initial-launch
requirement. The old checkpoint fallback remains part of the historical record,
but it is no longer the planning default. The operative safe stop is:

> **Keep every Stock Token value path disabled until the complete minimum
> containment group in Section 23 is approved, implemented, audited, and
> activated atomically. If that group cannot be kept reasonably small or
> cannot prove the launch invariants, return the evidence to the owner before
> opening the larger permanent architecture.**

## 1. Scope, branch, and starting state

- Integration repository: `/Users/wigglez/dev/ripe-protocol`
- Track worktree:
  `/Users/wigglez/dev/ripe-protocol-track-8-stock-token-vault-change`
- Branch: `rh-track-8-stock-token-vault-change`
- Starting branch: `rh`
- Starting commit:
  `be6a759e15e763b633feefdce91cf8f3ee31a10e`
  (`docs: add Robinhood vault change track brief`)
- Starting integration worktree: clean
- Track worktree at bootstrap: clean
- Current Track 5 decision:
  `conditional — shared vault change specification required`
- Production code, interfaces, tests, mocks, defaults, migrations, manifests,
  ABIs, dependencies, CI, generated artifacts, and `rh-summary.md`: unchanged by
  Track 8
- Track branch push: owner-authorized backup only; no merge
- Merge, deployment, live configuration, and transaction actions: not
  performed

Parallel Track 6 S1, Track 6 S2, and Track 7 implementation outputs were not
integrated at the starting commit. After this worktree was created, integration
`rh` advanced to `ce3805d6079ee87d727486ea82b75cbddc12e46d`; that commit records
owner approval of the narrow S1/S2 kickoff choices, but does not integrate
their implementation outputs. Future implementation interfaces therefore
remain `pending`; no floating worktree or unmerged commit is treated as
authority.

### 1.1 Bootstrap command record

The following results were captured in the original session before creating
the Track worktree and transcribed from that session log into this document
during the first checkpoint-review revision:

```text
git -C /Users/wigglez/dev/ripe-protocol status --short --branch
=> ## rh...origin/rh

git -C /Users/wigglez/dev/ripe-protocol rev-parse rh
=> be6a759e15e763b633feefdce91cf8f3ee31a10e

git -C /Users/wigglez/dev/ripe-protocol show \
  rh:docs/chains/rh/track-8-stock-token-vault-change.md
=> present

git -C /Users/wigglez/dev/ripe-protocol show-ref --verify \
  refs/heads/rh-track-8-stock-token-vault-change
=> exit 1; branch absent

test -e /Users/wigglez/dev/ripe-protocol-track-8-stock-token-vault-change
=> exit 1; path absent
```

The contract-prescribed creation command and immediate verification were:

```text
git -C /Users/wigglez/dev/ripe-protocol worktree add \
  -b rh-track-8-stock-token-vault-change \
  /Users/wigglez/dev/ripe-protocol-track-8-stock-token-vault-change rh
=> worktree created at be6a759

git -C /Users/wigglez/dev/ripe-protocol-track-8-stock-token-vault-change \
  status --short --branch
=> ## rh-track-8-stock-token-vault-change
```

### 1.2 Documentation-only validation record

Before staging, each untracked deliverable was checked independently:

```text
git diff --no-index --check /dev/null \
  docs/chains/rh/stock-token-vault-change-specification.md
=> no whitespace diagnostics; exit 1 only because the new file differs from
   /dev/null

git diff --no-index --check /dev/null \
  docs/chains/rh/stock-token-vault-change-validation-plan.md
=> no whitespace diagnostics; exit 1 only because the new file differs from
   /dev/null

git status --short
=> ?? docs/chains/rh/stock-token-vault-change-specification.md
   ?? docs/chains/rh/stock-token-vault-change-validation-plan.md
```

The local checkpoint-draft commit itself evidences the staged file scope.
Immediately before that commit, `git diff --cached --check` returned no output;
that command result is a session-log record, not data encoded in the Git commit
object. No non-document file was included.

## 2. Evidence ledger

### 2.1 Primary evidence hashes

| Evidence | Commit provenance | SHA-256 at starting commit |
| --- | --- | --- |
| `docs/chains/rh/stock-token-vault-comparison.md` | `758f45f5455fd7c05b25533d2d748769bcfc49c2` | `2a1f01acc843f95fb94329f2451d18dd77db3142a5c9a1977b610ca2805c23da` |
| `docs/chains/rh/stock-token-vault-decision.md` | `758f45f5455fd7c05b25533d2d748769bcfc49c2` | `8dd7eee20dca17fcc367c3debf48ae0e2ce9598748c55ec2e7152beb89918629` |
| `docs/chains/rh/stock-token-vault-fix-recommendations.md` | `221122658f10b4241011e5e4e0d4faaa65ae7de1` | `c1ef4d58bce5b54f330d27228f5b583fe291661adb220cbcc5c0699b78d6b877` |
| `contracts/mock/MockStockTokenControls.vy` | `d8f11e9e3330e2c490ae5b14d5ef2bc186208dfc` | `5d1527262aad66642a6e0f6dfdaad03458abdc4085a0445ebff0af8969614ef7` |
| `tests/vaults/test_stock_token_vault_comparison.py` | `05940a5273cb7ff625ad0dc9bfb5ddc52c22844d` | `1f3723db14349f30a8b4990c8c993ef1a6add65c5b798871c86192aa7cd08c6c` |
| `docs/chains/rh/component-matrix.md` | `758f45f5455fd7c05b25533d2d748769bcfc49c2` | `9f4f33785d577461d17f89f0831e8e88b339e160509a4589e16bc5967364f2ec` |
| `docs/chains/rh/stock-token-transferability-evidence.md` | `72fbc300752e6f14db97ca16da7bbf75945eb3f8` | `01d7441e7338924316fcb14d159689625f83f0db35384a1c3d0ec56c27b22ba6` |
| `docs/chains/rh/block-number-inventory.md` | `4408aa2184cfa80e8f0fed5482397856a9aedfb7` | `3f111accff58e51b91986f134df6d15ed7401d692ef0cca28b2cafb1c89ad2d4` |
| `docs/chains/rh/shared-block-clock-specification.md` | `c3040041a1254a774e0a305060330d6ab9cc04ca` | `98a8afb992cedb749543d986544504c42c7e9b0d57ec2eb72154ea5dad95fb8d` |
| `docs/chains/rh/block-clock-validation-plan.md` | `fc3382c043e026a45eb411142ba6f4918d195aae` | `e3f5d73fa9588aba28ac8823b74c5d523d1e0e6451d29d47f352a87fe03371f2` |
| `migration_history/base-mainnet/v1/current-manifest.json` | `cbf7ea8264abbf81ea2becd616c8d79843a44b0f` | `06ac6dcf3d5c3d2366bd33118023fd6603fc4d759a7a5103901b29ae67007b00` |

### 2.2 Comparison-suite result

Commands were run unmodified from the Track worktree:

```text
PYTHONPATH=. pytest --collect-only -q \
  tests/vaults/test_stock_token_vault_comparison.py
=> 90 tests collected in 0.16s

PYTHONPATH=. pytest -q \
  tests/vaults/test_stock_token_vault_comparison.py
=> 90 passed in 51.98s
```

The actual integrated count is therefore 90, not an inherited point-in-time
count.

After incorporating checkpoint-review feedback, the same unchanged suite was
run again from the same pinned worktree:

```text
PYTHONPATH=. pytest -q \
  tests/vaults/test_stock_token_vault_comparison.py
=> 90 passed in 53.85s
```

### 2.3 Claim labels

- **Tested:** directly asserted by the 90-case integrated Track 5 suite.
- **Source-traced:** follows from current source and caller/callee ordering.
- **Live-verified:** read from the committed Base manifest plus read-only Base
  RPC at a pinned block.
- **Derived:** a consequence of tested/source/live facts, but not itself an
  executed test.
- **Pending:** requires owner policy, unintegrated S1/S2/Track 7 work, audit, or
  future implementation evidence.

## 3. Evidence and source delta report

### 3.1 Track 5 evidence to starting commit

The source delta from the integrated test-evidence commit
`05940a5273cb7ff625ad0dc9bfb5ddc52c22844d` to the Track 8 starting commit adds
Track 2 probe contracts/tests/scripts, Track 3/6/7/8 documents, and two probe or
migration-tool helpers. It also refines the Track 5 evidence documents.

No production vault, common Vault interface, Teller, CreditEngine,
AuctionHouse, Deleverage, Lootbox, Ledger, MissionControl, VaultBook,
Switchboard, or deployed-default source changed in that range. In particular,
all of the following behavioral inputs are unchanged:

- `BasicVault`, `SharesVault`, `SimpleErc20`, `RebaseErc20`, `StabVault`,
  `VaultData`, `StabilityPool`, and `RipeGov`;
- `Vault.vyi` and `ConfigStructs.vyi`;
- `Teller`, `TellerUtils`, `CreditEngine`, `AuctionHouse`,
  `AuctionHouseNFT`, `Deleverage`, `Lootbox`, and `CreditRedeem`;
- `Ledger`, `MissionControl`, `VaultBook`, and `RipeHq`;
- Switchboards Alpha, Bravo, Charlie, and Delta; and
- `DefaultsBase`.

Disposition: **no invalidating production-source delta**. The Track 5 suite was
nevertheless rerun rather than assumed.

### 3.2 Current behavior reconciliation

| Claim | Classification | Current result |
| --- | --- | --- |
| Simple total issuer burn leaves nominal user balances and borrowing amount | Tested | Reproduced by the suite; custody can be zero while nominal collateral remains positive. |
| Simple internal auction after total burn can charge GREEN and move a nominal buyer claim | Tested | Reproduced; the token never leaves the vault because the settlement mode only changes nominal ownership. |
| Rebase partial loss reprices live claims pro rata | Tested and source-traced | Current share conversion follows live `balanceOf(vault)`. |
| Rebase total loss with nonzero shares blocks withdrawal/internal transfer | Tested and source-traced | `_calcWithdrawalSharesAndAmount` asserts live balance is nonzero. Safety may hold by revert, but debt-resolution liveness is absent. |
| Rebase fresh deposit after zero custody with old shares is unsafe | Tested and source-traced | For an ordinary fully received deposit `R` after `C=0`, current code observes `totalAssetBalance=R`, sets `depositAmount=R`, and derives `prevTotalBalance=R-R=0`. `_amountToShares` then divides by the `+1` virtual balance and mints approximately `R × (old S + 10^8)` shares, heavily diluting the old shares without an approved recapitalization policy. |
| Later short-received deposit is reported/credited as requested in both paths | Tested and source-traced | Teller transfers the requested amount, then the vault infers receipt from total balance rather than measuring the call delta. |
| External auction transfer failure is atomic | Tested and source-traced | Vault transfer reverts before `_buyFungibleAuction` sends GREEN or calls debt repayment. |
| Paused internal settlement can still charge GREEN | Tested | Internal balance transfer does not exercise token transferability. |
| Total loss has no automatic exactly-once user-debt-to-bad-debt transition | Source-traced | Ledger exposes a Switchboard `setBadDebt` overwrite, but no current loss path atomically removes the same liability from user debt and increments protocol bad debt. |
| Phase E discovery: repayment can be blocked by an unavailable configured collateral price | Source-traced | `_repayDebt` calls `_getUserBorrowTerms(..., True, ...)` at `CreditEngine.vy:558`; each nonzero-amount, nonzero-LTV position reaches `PriceDesk.getUsdValue(..., True)` at line 741. `PriceDesk.vy:174-176` raises when a configured feed yields no price, so a stale/unavailable configured feed can revert repayment today. Phase E's non-raising repayment refresh is an intentional behavior fix and a required Phase I impact item. |
| Dedicated per-asset collateral-use safety flag exists | Source-traced | False. `AssetConfig` already has `canDeposit`, deposit limits, and per-asset `DebtTerms.ltv`; only the general `canBorrow` switch is global. Phase E rejects adding another stored flag and instead defines one fail-closed eligibility predicate from those existing controls plus automatic backing state. |

The evidence does not prove that every ordinary ERC-20 can spontaneously lose
vault custody. It proves what happens if custody falls independently of Ripe
accounting and that current deposit accounting can itself create an accounted
deficit after a short receipt. The repayment finding is independent additional
hardening evidence: even without a custody loss, oracle unavailability can
currently obstruct the risk-reducing action that invariant I-09 requires to
remain open.

### 3.3 Post-bootstrap integration delta

During Track 8 work, integration `rh` advanced from the mandated starting commit
`be6a759` to `ce3805d`. The later commit changes only:

- `docs/chains/rh-summary.md`; and
- `docs/chains/rh/shared-block-clock-specification.md`.

It records owner-approved checklist reconciliation and S1/S2 kickoff decisions.
It does not change any vault/protocol source, Track 5 comparison test or mock,
Base manifest, or Track 8 production assumption. The deployable Stock Token
vault path remains unchecked. The Track 8 worktree intentionally remains pinned
to `be6a759`; it was not rebased or moved after the checkpoint contract was
started.

### 3.4 Phase E source recheck

Immediately before Phase E, the isolated Track 8 branch was clean at
`b0fc9268b1f2543f3e8624e7695a41a613623b0a` with no upstream. Integration
`rh` was clean at `c2ded229fefe2ad614693c999bd89faeaec1535e`. A direct diff
between those commits showed no changes in the Phase E source set:

- `interfaces/ConfigStructs.vyi` and `interfaces/Vault.vyi`;
- `MissionControl`, `CreditEngine`, `TellerUtils`, and Ledger;
- Switchboards Alpha, Bravo, and Charlie;
- Simple/Rebase wrappers plus BasicVault, SharesVault, and VaultData; and
- AuctionHouse and Deleverage.

Phase E therefore uses the same source behavior reconciled in Phases A–D. No
integration commit was imported into the isolated worktree.

The integration increment leading to `c2ded229` did change the S1
test/config/script harness outside that source set, including
`tests/conftest.py`, clock-profile and inventory tests,
`config/block-clock-inventory.json`, and
`scripts/check_block_clock_inventory.py`. The Track 5 comparison test itself
was unchanged, and Track 8's reported 90-test evidence remains pinned to
`be6a759`. Any later rerun at an integrated tip must record this harness delta
and must not attribute a result difference to Track 8 without isolating it.

Captured at Phase E entry:

```text
git status --short --branch
=> ## rh-track-8-stock-token-vault-change

git -C /Users/wigglez/dev/ripe-protocol status --short --branch
=> ## rh...origin/rh

git diff --name-only b0fc9268 c2ded229 -- <Phase E source set above>
=> no output
```

### 3.5 Post-recheck integration state

During Phase E, integration `rh` remained at `c2ded229` but acquired external
documentation-only working-tree changes in
`shared-block-clock-specification.md` and an untracked Track 6 document. Those
files are outside Track 8's owned deliverables and Phase E source set. They
were neither read as controlling evidence, edited, staged, nor imported here.

After the Phase E review-remediation commit, integration `rh` advanced
externally to `f0bfd0fd5ac2be1d27321463b77248c7cd91d829`, committing only those
same two documentation paths. A direct `c2ded229..f0bfd0f` comparison over the
Phase E source set in Section 3.4 returned no paths. The Track 8 worktree was
not rebased, merged, or otherwise moved to that integration commit.

### 3.6 Phase F source and branch recheck

Immediately before Phase F, the isolated Track 8 worktree was clean at
`0d389625b7f11f92b322d79e4156ff25188f812c`. The branch tracked
`origin/rh-track-8-stock-token-vault-change` at zero ahead and zero behind
because the owner had authorized a backup push only. Integration `rh` was clean
at `f0bfd0fd5ac2be1d27321463b77248c7cd91d829`.

A direct comparison from the Track 8 entry commit to that integration commit
returned no path in the Phase F source set:

- `AuctionHouse`, `CreditEngine`, `CreditRedeem`, `Deleverage`, `Teller`, and
  `TellerUtils`;
- Ledger, MissionControl, and Switchboards Bravo, Charlie, and Delta;
- `ConfigStructs` and the common Vault interface; and
- Simple/Rebase wrappers plus BasicVault, SharesVault, and VaultData.

Phase F therefore specifies the same pinned source behavior already reconciled
in Sections 3.2–3.5. No integration commit was imported, no production source
was changed, and the backup push did not merge the track branch.

Captured at Phase F entry:

```text
git status --short --branch
=> ## rh-track-8-stock-token-vault-change...origin/rh-track-8-stock-token-vault-change

git rev-parse HEAD
=> 0d389625b7f11f92b322d79e4156ff25188f812c

git -C /Users/wigglez/dev/ripe-protocol status --short --branch
=> ## rh...origin/rh

git -C /Users/wigglez/dev/ripe-protocol rev-parse HEAD
=> f0bfd0fd5ac2be1d27321463b77248c7cd91d829

git diff --name-only 0d389625 f0bfd0f -- <Phase F source set above>
=> no output
```

### 3.7 Phase G source and branch recheck

At Phase G entry, the isolated worktree was clean and synchronized with its
owner-authorized backup branch at
`0d8423ef5d7f389fadc6f5797d6ad5fb18b5e5a0`. Integration `rh` and `origin/rh`
were clean and synchronized at
`f0bfd0fd5ac2be1d27321463b77248c7cd91d829`.

A direct `be6a759..f0bfd0f` comparison returned no changed path in the Phase G
source/evidence set:

- `SharesVault`, `VaultData`, `RebaseErc20`, and `RipeGov`;
- Lootbox, Ledger, and the common Vault interface;
- `test_shares_vault.py`, `test_loot_deposit_points.py`, and the Track 5
  comparison suite.

Phase G therefore specifies the same pinned share math, raw-share reward
weight, custody-valued global reward input, deregistration/recovery behavior,
and current unsafe donation/restoration behavior already evidenced at the
starting commit. No integration commit was imported and no floating track was
used.

Captured at Phase G entry:

```text
git status --short --branch
=> ## rh-track-8-stock-token-vault-change...origin/rh-track-8-stock-token-vault-change

git rev-parse HEAD
=> 0d8423ef5d7f389fadc6f5797d6ad5fb18b5e5a0

git -C /Users/wigglez/dev/ripe-protocol status --short --branch
=> ## rh...origin/rh

git -C /Users/wigglez/dev/ripe-protocol rev-parse HEAD
git -C /Users/wigglez/dev/ripe-protocol rev-parse origin/rh
=> f0bfd0fd5ac2be1d27321463b77248c7cd91d829
   f0bfd0fd5ac2be1d27321463b77248c7cd91d829

git -C /Users/wigglez/dev/ripe-protocol diff --name-status \
  be6a759..f0bfd0f -- <Phase G source/evidence set above>
=> no output
```

Phase G also required reconciliation edits in previously approved Sections
6–9 and 12–16, plus the corresponding earlier validation-plan sections. The
Phase G handoff did not enumerate that reach-back clearly enough. For an
explicit audit trail, those edits were:

| Earlier surface | Phase G reconciliation |
| --- | --- |
| Formal model, invariants, and state table (Sections 6–8) | Added allocated/quarantine state `A^s/U^s/A/U`, split the former zero predicate into `Z_custody/Z_live/Z_recorded`, propagated I-13, and updated the sixteen state rows to distinguish live custody, allocated backing, and quarantine. |
| Architecture comparison (Section 9) | Expanded Outcome 3 from I-01–I-12 to I-01–I-13 and recorded the now-specified partial-loss, post-zero, donation/restoration, reward, issuer-settlement, and total-loss policies while leaving implementation mechanisms unresolved. |
| Decision register and component boundary (Sections 12–13) | Recorded the owner-confirmed Phase G policies and returned the unresolved storage/interface mechanism to Phase I. |
| Deposit accounting (Section 14) | Composed the Phase D receipt rule with Section 17's pre-deposit allocated denominator `A_0`; the call-local caller-request symbol is now `A_req` so it cannot collide with global allocated backing `A`. |
| Backing/debt health (Section 15) | Renamed the user-position amount to `M(v,a,u)` and made the current-versus-corrected SharesVault total semantics explicit. |
| Settlement/total loss (Section 16) | Scoped retained non-issuer internal settlement to Section 17 allocated live claims with quarantine excluded, and recorded Section 17's no-automatic-allocation rule for later recovery without selecting a Phase I mechanism. |
| Validation plan before Phase G | Propagated the same symbols, state diagnostics, formula composition, test prerequisites, and section renumbering into the already specified Phase D–F validation surfaces. |

Both deliverables' status/introduction and closing hold/checklist language were
also advanced from the Phase F checkpoint to the owner-authorized Phase G
completion state; those are phase-progression markers, not technical
reconciliation changes.

These were consistency reconciliations needed to compose Phase G with the
approved A–F contracts; they did not reverse an owner-approved policy, select
an implementation mechanism, or begin Phase H.

During the final Phase G documentation audit, the integration worktree
acquired an external untracked
`docs/chains/rh/track-7-h1-dependency-security-preflight.md` while remaining at
the same `f0bfd0f` commit. That file is outside Track 8's owned deliverables and
source/evidence set. It was not read as controlling evidence, edited, staged,
or imported.

At this review-remediation pass, integration remained at `f0bfd0f` but also
showed external modifications to
`docs/chains/rh/robinhood-deployment-support-specification.md` and
`docs/chains/rh/robinhood-deployment-validation-plan.md`. Those files and the
untracked Track 7 file remain outside Track 8 scope; none was edited, staged,
or imported here.

During this final cosmetic closure pass, local integration `rh` advanced
externally from `f0bfd0f` to
`382eb7da82bc4ed54be945311a8ccd30fae87dec`, temporarily one commit ahead
of `origin/rh`; the remote subsequently synchronized to the same commit before
this pass completed. That commit contains only the same three out-of-scope
documentation paths identified above. No Track 8 source/evidence path changed,
no integration commit was imported, and Phase H was not begun.

### 3.8 Phase H source and branch recheck

At Phase H entry, the isolated Track 8 worktree was clean and synchronized
with its owner-authorized backup branch at
`6c8984102968197b7634d5b3786b0adfd101901f`. Integration `rh` and
`origin/rh` were clean and synchronized at
`382eb7da82bc4ed54be945311a8ccd30fae87dec`.

The integration increment `f0bfd0f..382eb7d` contains only:

- `docs/chains/rh/robinhood-deployment-support-specification.md`;
- `docs/chains/rh/robinhood-deployment-validation-plan.md`; and
- `docs/chains/rh/track-7-h1-dependency-security-preflight.md`.

The first two documents confirm that a Robinhood defaults contract and Stock
Token asset configuration remain proposed, not deployed or selected. The
third is Track 7's dependency-security preflight; its `H-01` label is not this
Track 8 Phase H and creates no Track 8 authorization.

A direct `be6a759..382eb7d` comparison returned no changed path in the Phase H
source set:

- MissionControl, Ledger, Teller, TellerUtils, CreditEngine, AuctionHouse, and
  Deleverage;
- Switchboards Alpha, Bravo, Charlie, and Delta plus LocalGov, TimeLock,
  DeptBasics, and Addys;
- VaultBook, AddressRegistry, VaultData, BasicVault, SharesVault,
  SimpleErc20, RebaseErc20, and the common interfaces;
- `DefaultsBase`; and
- the Track 5 comparison test and Base current manifest.

Phase H therefore maps the same pinned controls, events, getters, registry
guards, pause blast radii, and observable accounting state used by Phases A–G.
No integration commit was imported. The integrated deployment-support
documents are used only to confirm the absence of a completed Robinhood
defaults/configuration artifact; they do not select its future values.

Captured at Phase H entry:

```text
git status --short --branch
=> ## rh-track-8-stock-token-vault-change...origin/rh-track-8-stock-token-vault-change

git rev-parse HEAD
git rev-parse origin/rh-track-8-stock-token-vault-change
=> 6c8984102968197b7634d5b3786b0adfd101901f
   6c8984102968197b7634d5b3786b0adfd101901f

git -C /Users/wigglez/dev/ripe-protocol status --short --branch
=> ## rh...origin/rh

git -C /Users/wigglez/dev/ripe-protocol rev-parse HEAD
git -C /Users/wigglez/dev/ripe-protocol rev-parse origin/rh
=> 382eb7da82bc4ed54be945311a8ccd30fae87dec
   382eb7da82bc4ed54be945311a8ccd30fae87dec

git -C /Users/wigglez/dev/ripe-protocol diff --name-status \
  be6a759..382eb7d -- <Phase H source set above>
=> no output
```

Phase H also required reconciliation edits in previously approved Sections
11–13 and 15–17 and the corresponding earlier validation-plan surfaces. Phase
H handoff commit `1e414983946633c5f58e15c9bfb464aa84d067b5` did not enumerate
that reach-back clearly enough. For an explicit audit trail, those edits were:

| Earlier surface | Phase H reconciliation |
| --- | --- |
| Status, introduction, hold, and checklist progression | Advanced both deliverables from the Phase G checkpoint to owner-authorized Phase H, moved the hold from Phases H–K to Phases I–K, renumbered the closing sections, and marked Phases A–H as specified without closing `rh-summary.md` or any later gate. |
| Track 5 recommendation disposition (Section 11.1) | Linked the already-accepted monitoring and incident-response recommendations to Section 18's concrete read-only evidence/control requirements. Also corrected the stale “Freeze post-zero deposits” row from “returned for owner approval” to the owner-confirmed Phase G specification status already recorded in Section 12.1; this was a delayed status correction, not a new Phase H approval. |
| Owner authorization and decision register (Sections 12.1–12.3) | Recorded the exact Phase H authorization and boundary, updated the prior Phase F caller row with the completed alternatives analysis, registered the Phase H resolution/checkpoint gate, separate caller, and withdrawal-posture decisions as returned, and replaced the provisional emergency-control deferral with the evidence-complete-but-unselected status. |
| Component boundary (Section 13) | Added the control/default component IDs, Ledger borrower/auction enumeration responsibility, and the explicit finding that Phase H maps current interfaces without selecting a replacement. |
| Phase E operator evidence (Section 15.7) | Replaced the prospective “Phase H may add detail” marker with the completed Section 18 cross-reference while preserving the already-approved automatic fail-closed backing rule. |
| Phase F controls and acceptance (Sections 16.11–16.12) | Reconciled the provisional Department-pause treatment with the Phase H proof that broad Teller/CreditEngine/Ledger pauses are not a repayment-safe normal gate, returned the existing-control/dedicated-gate/caller alternatives without selection, and made future acceptance depend on the later owner-selected gate and its tests. |
| Phase G observation boundary (Section 17.5) | Removed the earlier preference for a permissionless checkpoint entry and retained only the approved liveness requirement; Phase H deliberately leaves the checkpoint caller unproposed and unselected. The post-zero freeze and quarantine semantics did not change. |
| Validation plan before Phase H | Added the proposed Phase H paths, reconciled the Phase F gate test and acceptance language with the returned alternatives, added the Phase H test contract, renumbered the former Sections 10–15 to 11–16, and advanced the closing hold from Phase H to Phase I. No test or implementation file was created. |

These were consistency and provenance reconciliations required to compose
Phase H with the approved A–G contracts. They did not reverse an
owner-approved policy, select a gate or caller, introduce a storage/interface
proposal, authorize implementation or migration, or begin Phase I.

At final Phase H handoff, integration `rh` and `origin/rh` remained at
`382eb7da82bc4ed54be945311a8ccd30fae87dec`, but the integration worktree had
gained an untracked
`docs/chains/rh/track-6-s4-deleverage-cooldown.md`. That path is not part of an
integration commit, was not imported, modified, or treated as Track 8
evidence, and creates no Phase H source delta. Its presence is disclosed here
rather than silently restating the entry-time clean-worktree observation as a
handoff-time fact.

During this reach-back audit remediation, local integration `rh` advanced
externally from `382eb7da82bc4ed54be945311a8ccd30fae87dec` to
`127b4bf287bf63c5ed662d82fbf3db8bf66d06a3` while `origin/rh` remained at
`382eb7da82bc4ed54be945311a8ccd30fae87dec`. The new commit only adds the
previously disclosed
`docs/chains/rh/track-6-s4-deleverage-cooldown.md`; no Phase H
source/evidence path changed. That commit was not imported or treated as Track
8 evidence.

### 3.9 Phase I source and branch recheck

At Phase I entry, the isolated Track 8 worktree was clean and synchronized
with its owner-authorized backup branch at
`342ea34b372a415f5f2ddf43c6cc1e4ed2a7d762`. Local integration `rh` was
clean at `127b4bf287bf63c5ed662d82fbf3db8bf66d06a3`, one documentation-only
commit ahead of `origin/rh` at
`382eb7da82bc4ed54be945311a8ccd30fae87dec`. The Track 8 merge base remained
`be6a759e15e763b633feefdce91cf8f3ee31a10e`; no integration commit was
imported.

The sole local-only integration increment,
`382eb7d..127b4bf`, adds
`docs/chains/rh/track-6-s4-deleverage-cooldown.md`. It changes no contract,
interface, ABI, migration, manifest, default, parameter generator, or Track 8
deliverable. The Phase I source and artifact inventory is therefore performed
against the same pinned contract tree and Base manifest used by Phases A–H.

Captured at Phase I entry:

```text
git status --short --branch
=> ## rh-track-8-stock-token-vault-change...origin/rh-track-8-stock-token-vault-change

git rev-parse HEAD
git rev-parse origin/rh-track-8-stock-token-vault-change
=> 342ea34b372a415f5f2ddf43c6cc1e4ed2a7d762
   342ea34b372a415f5f2ddf43c6cc1e4ed2a7d762

git -C /Users/wigglez/dev/ripe-protocol status --short --branch
=> ## rh...origin/rh [ahead 1]

git -C /Users/wigglez/dev/ripe-protocol rev-parse HEAD
git -C /Users/wigglez/dev/ripe-protocol rev-parse origin/rh
=> 127b4bf287bf63c5ed662d82fbf3db8bf66d06a3
   382eb7da82bc4ed54be945311a8ccd30fae87dec

git merge-base HEAD origin/rh
=> be6a759e15e763b633feefdce91cf8f3ee31a10e
```

During final Phase I validation, integrated `rh` and `origin/rh` advanced
externally from the entry state to
`3e6e6f230169fc445d0b29454457480c62efd89a`, merge commit
`merge: integrate Track 6 S3 Lootbox floor`. The Track 8 worktree was not
rebased and imported no integration commit; its merge base with `origin/rh`
remained `be6a759e15e763b633feefdce91cf8f3ee31a10e`.

The `127b4bf..3e6e6f2` delta changes `contracts/core/Lootbox.vy`, its
generated ABI, S1/S2 inventory/tooling and tests, shared test configuration,
and the new S3 implementation record. It changes no other Phase I production
source and no Track 8 deliverable. Phase I therefore re-read the integrated
Lootbox source, ABI, and implementation record through `origin/rh`, reconciled
them in Sections 17 and 19, and kept the remaining pinned Track 8 source
baseline unchanged. No S3 deployment, registry change, or live-state action is
treated as complete. The Track 5 comparison file is unchanged; its 90-case
evidence remains pinned to `be6a759`. Any later rerun at integrated `rh` must
account for S3's `tests/conf_core.py` Lootbox constructor change before
attributing a difference to Track 8.

Captured after the integration advance:

```text
git -C /Users/wigglez/dev/ripe-protocol rev-parse HEAD
git -C /Users/wigglez/dev/ripe-protocol rev-parse origin/rh
=> 3e6e6f230169fc445d0b29454457480c62efd89a
   3e6e6f230169fc445d0b29454457480c62efd89a

git merge-base HEAD origin/rh
=> be6a759e15e763b633feefdce91cf8f3ee31a10e

git diff --name-status 127b4bf..origin/rh -- \
  config contracts interfaces scripts \
  migration_history/base-mainnet/v1/current-manifest.json
=> M config/block-clock-inventory.json
   M contracts/core/Lootbox.vy
   M scripts/abis/Lootbox.json
   M scripts/check_block_clock_inventory.py
```

The manifest addresses used in Phase I are repository-declared deployment
records, not a substitute for a same-block live registry/code-hash read.
Section 5 independently pinned only `VaultBook`, `SimpleErc20`, and
`RebaseErc20` live identities. Every future core migration must repeat live
`RipeHq`/`VaultBook` resolution and runtime-code verification before treating
a manifest address as active.

### 3.10 Phase I reconciliation audit trail

Phase I required reach-back edits so the earlier phase records compose with
the later owner direction without rewriting their historical checkpoints:

| Earlier surface | Phase I reconciliation |
| --- | --- |
| Status, introduction, hold, and checklist | Advanced the deliverables from the Phase H checkpoint to Phase I owner review, moved the hold to Phases J–K, and left `rh-summary.md` unchanged. |
| Owner record and decision register (Sections 12.1–12.3) | Recorded the exact five-direction Phase I authorization, distinguished the resolved control/caller assumptions from the still-unapproved selectors/storage, and registered the returned implementation, migration, and live-version choices. |
| Phase C component map (Section 13) | Kept the original boundary as historical context and made Section 19.4 the exhaustive source/interface/storage/artifact impact inventory. |
| Phase F caller, controls, and acceptance (Sections 16.10–16.12) | Applied the later conditional permissionless-caller and existing-`canLiquidate` directions without approving the proposed selectors or Ledger migration. |
| Phase G observation, compatibility, and rewards (Sections 17.5–17.11) | Applied the later existing-Switchboard checkpoint-caller direction and returned the exact two-bucket/interface alternatives. After S3 integrated during Phase I, reconciled its Lootbox floor/constructor/getter/ABI change and recorded that it does not supply the separate loss-checkpoint reward interval/index. |
| Phase H handoff (Sections 18.12–18.13) | Preserved the Phase H alternatives as the historical handoff, then recorded which assumptions the later Phase I instruction resolved and which new machinery remains unapproved. |
| Validation plan | Added the Section 11 compatibility/artifact/migration contract, reconciled earlier acceptance gates with the later direction, renumbered the former Sections 11–16 to 12–17, and moved the stop boundary to Phase J. No test or implementation file was created. |

These are composition and provenance edits, not retroactive Phase I authority.
They do not select a new storage layout, interface, ABI, settlement mechanism,
production vault, migration, or Phase J work. The companion validation-plan
introduction links back to this audit trail.

### 3.11 Phase J source and branch recheck

At Phase J entry, the isolated Track 8 worktree was clean and synchronized
with its owner-authorized backup branch at
`8caf9555e6b30df9bc66f5cb6135153931285264`. Integration `rh` and
`origin/rh` were clean and synchronized at
`3e6e6f230169fc445d0b29454457480c62efd89a`. The Track 8 merge base remained
`be6a759e15e763b633feefdce91cf8f3ee31a10e`; no integration commit was
imported.

Phase I had already reconciled the integrated Track 6 S3 Lootbox source and
the S1/S2 harness/inventory delta at that same integration tip. Phase J
re-read the integrated validation interfaces through `rh`:

- `tests/utils/clock_profiles.py`,
  `tests/clock/test_clock_profiles.py`, and the narrow
  `tests/conftest.py` fixture registration;
- `config/block-clock-inventory.json`,
  `scripts/check_block_clock_inventory.py`, and
  `tests/inventory/test_block_clock_inventory.py`;
- `docs/chains/rh/shared-block-clock-specification.md` and
  `docs/chains/rh/block-clock-validation-plan.md`;
- the integrated S3 Lootbox source, ABI, constructor/floor record, and still
  open Base source/live rollout boundary; and
- Track 7's integrated dependency-security preflight and deployment-support
  plans, which do not reserve or approve a Track 8 migration ID, manifest,
  production vault, or live action.

The integrated S1/S2 command interfaces are:

```text
pytest -q tests/clock/test_clock_profiles.py
python scripts/check_block_clock_inventory.py
pytest -q tests/inventory/test_block_clock_inventory.py
pytest -q
```

They are future implementation/release gates for Track 8. Phase J does not
copy the integrated harness into this pinned worktree, modify it, or claim
that a future Track 8 implementation already passes it.

Captured at Phase J entry:

```text
git status --short --branch
=> ## rh-track-8-stock-token-vault-change...origin/rh-track-8-stock-token-vault-change

git rev-parse HEAD
git rev-parse origin/rh-track-8-stock-token-vault-change
=> 8caf9555e6b30df9bc66f5cb6135153931285264
   8caf9555e6b30df9bc66f5cb6135153931285264

git -C /Users/wigglez/dev/ripe-protocol status --short --branch
=> ## rh...origin/rh

git -C /Users/wigglez/dev/ripe-protocol rev-parse rh
git -C /Users/wigglez/dev/ripe-protocol rev-parse origin/rh
=> 3e6e6f230169fc445d0b29454457480c62efd89a
   3e6e6f230169fc445d0b29454457480c62efd89a

git merge-base HEAD origin/rh
=> be6a759e15e763b633feefdce91cf8f3ee31a10e
```

No existing test was rerun for Phase J because this phase changes
documentation only and the pinned Track 5 suite/source tree is unchanged.
The existing 90-case result remains evidence at `be6a759`; a future
implementation run must use the integrated harness and account for S3's
constructor fixture.

During final Phase J validation, the integration worktree gained an external
untracked `docs/chains/rh/track-6-s5-ledger-guard.md` while `rh` and
`origin/rh` remained synchronized at `3e6e6f2`. That path is outside Track
8's two deliverables and was not read, edited, staged, imported, or treated as
authority. Its presence does not change the commit-pinned Phase J source
recheck; it is disclosed so the clean-at-entry observation is not restated as
a clean-at-handoff fact.

During the Phase J review-remediation pass, local integration `rh` advanced
externally from `3e6e6f2` to
`27765d29094256fa9619dd44a0bfd145863de8b7`, one commit ahead of
`origin/rh`. That commit only adds the previously disclosed
`docs/chains/rh/track-6-s5-ledger-guard.md`; it changes no Track 8
source/evidence path or deliverable. The commit was not imported or treated as
Phase J authority, and the Track 8 merge base remains the pinned
`be6a759e15e763b633feefdce91cf8f3ee31a10e`.

### 3.12 Phase J reconciliation audit trail

Phase J necessarily advances earlier status and gate language while preserving
the historical Phase I stop:

| Earlier surface | Phase J reconciliation |
| --- | --- |
| Status, introduction, hold, and checklist | Advances the deliverables from Phase I owner review to a complete Phase J validation specification, moves the hold to Phase K, and leaves `rh-summary.md` unchanged. |
| Track 5 disposition, owner record, and decision register (Sections 11.1, 12.1–12.3, and 19.9) | Records the exact Phase J authorization and distinguishes preferred validation targets from production selections. Section 11.1's Base-hardening row and the decision registers now state that Base-first-or-atomic is a validation/release requirement without authorizing a migration. |
| Phase I alternatives (Section 19) | Keeps all-external conditional on complete integration and historical-use evidence, treats the isolated generic variant and `A^s/U^s` as test targets rather than selected files/layout/selectors, and keeps the two-selector transition inseparable from—but not authorization for—the full Ledger migration. |
| Validation-plan status and branch gates | Activates only the all-external preferred branch for evidence planning, keeps the per-asset-mode branch as an unselected comparison, preserves S3 independently if Track 8 would delay it, and makes empty/gated state an inactive rehearsal rather than launch evidence. |
| Validation record model | Adds deterministic profile inheritance so every named future assertion has a file, components, prerequisite, actors/token behavior, expected transition, invariant/control obligation, clock, diagnostics, tier, and reviewers without duplicating hundreds of case names. |
| Exact-token, S1/S2/S3, migration, and launch gates | Reconciles the integrated harness commands, adds complete historical settlement-use evidence, requires Base convergence before RH enablement, and preserves Track 7 ownership of IDs/manifests/tooling. |

These are Phase J validation specifications only. They do not select a
production vault or ID, approve a new storage declaration or selector,
authorize the Ledger or vault migration, authorize implementation or live
actions, or begin Phase K.

### 3.13 Phase K source, branch, and cross-track recheck

At Phase K entry, the isolated Track 8 worktree was clean and synchronized
with its owner-authorized backup branch at
`b18b4261f798b4d6daae3634b0ad747656944db9`. Local integration `rh` was at
`27765d29094256fa9619dd44a0bfd145863de8b7`, one commit ahead of
`origin/rh` at `3e6e6f230169fc445d0b29454457480c62efd89a`. The Track 8 merge
base remained `be6a759e15e763b633feefdce91cf8f3ee31a10e`; no integration
commit was imported.

The sole committed local-only integration increment,
`3e6e6f2..27765d2`, adds
`docs/chains/rh/track-6-s5-ledger-guard.md` and no other path. Its SHA-256 is
`37332bb560ba5591da10b08f1e2e8aca28d4d21142c6a61ef8ac210566b564e1`,
recomputed directly from `rh` rather than from the mutable integration
worktree. Phase K read that committed 1,283-line owner-approved planning brief
completely because it owns a potentially overlapping Ledger/Teller security
and migration boundary. The brief authorizes only its own Stage A decision
record. It does not authorize S5 production code, a Ledger replacement, a
migration, or any Track 8 change.

The S5 cross-track constraints that bind a later Track 8 implementation are:

- S5's state-safe default is to preserve live Ledger bytecode and state unless
  an exhaustive, independently audited migration is separately approved;
- S5 reserves `migrations/robinhood/0030_Track6S5LedgerGuard.py` to Track 7
  for S5 only, so Track 8 may not reuse that identifier or file;
- S5 may analyze Track 8 borrow, withdraw, and liquidation paths, but may not
  implement Track 8 accounting fixes;
- any S4/S5/Track 8 overlap in Teller, Ledger, MissionControl,
  SwitchboardDelta, interfaces, ABIs, fixtures, or tests requires an explicit
  integrated order and one semantic owner per hunk; and
- no protection or accounting mechanism may be split across a deployment
  state that silently disables the old protection before the replacement is
  active.

Accordingly, Section 21 treats the candidate Track 8
CreditEngine-to-Ledger transition as one review unit, but treats any Ledger
runtime/state migration as a separate highest-risk gate. If S5 selects a
Ledger-preserving architecture, Track 8 may not silently override it. If a
future owner instead considers one combined forward Ledger artifact and
migration, both tracks' semantics, complete state inventories, independent
audits, and Track 7 execution plan must be approved together. Combining one
migration opportunity does not combine or weaken the two audit scopes.

The integration worktree was no longer clean when the Phase K recheck was
recorded: it had an external modification to `docs/chains/rh-summary.md` and
an untracked `docs/chains/rh/minimal-contract-change-reassessment.md`. Track
8 did not read either working-tree change as authority, did not edit or stage
either path, and does not report them as committed integration state. The
committed `be6a759..27765d2` production/artifact delta remains only the
already-reconciled S3 `contracts/core/Lootbox.vy` and
`scripts/abis/Lootbox.json` changes. No other Phase K production input
changed.

Captured at Phase K entry:

```text
git status --short --branch
=> ## rh-track-8-stock-token-vault-change...origin/rh-track-8-stock-token-vault-change

git rev-parse HEAD
git rev-parse @{upstream}
=> b18b4261f798b4d6daae3634b0ad747656944db9
   b18b4261f798b4d6daae3634b0ad747656944db9

git -C /Users/wigglez/dev/ripe-protocol status --short --branch
=> ## rh...origin/rh [ahead 1]
   M docs/chains/rh-summary.md
   ?? docs/chains/rh/minimal-contract-change-reassessment.md

git -C /Users/wigglez/dev/ripe-protocol rev-parse rh
git -C /Users/wigglez/dev/ripe-protocol rev-parse origin/rh
=> 27765d29094256fa9619dd44a0bfd145863de8b7
   3e6e6f230169fc445d0b29454457480c62efd89a

git merge-base HEAD rh
=> be6a759e15e763b633feefdce91cf8f3ee31a10e
```

No existing test was rerun for Phase K because this phase changes only the
two specification documents. Phase J already defines the future executable
evidence contract; Phase K groups those targets without claiming they exist
or pass.

### 3.14 Phase K reconciliation audit trail

Phase K changes earlier status and gate language only where necessary to
compose the final handoff:

| Earlier surface | Phase K reconciliation |
| --- | --- |
| Status and introduction | Advances both deliverables from the Phase J hold to Phases A–K specification-complete, while retaining every production/migration/live non-approval. |
| Source/integration record (Sections 3.13 and 3.15) | Records the exact Phase K entry/handoff commits, dirty external integration paths, committed S5 brief provenance, and the separate Ledger-migration/cross-track boundary. No integration source was imported. |
| Owner record and decision register (Sections 12.1–12.3) | Quotes the exact Phase K authorization, marks only release planning as authorized, and replaces the stale “Phase K deferred” audit row with the completed split and still-unapproved production gates. |
| Phase J hold (former Section 21) | Replaced the hold with the thirteen review units, exact future/blocked files, assurance matrices, Release 0/1/2 groups, audit boundaries, stop conditions, consolidated decision register, and K-CP0–K-CP11 checkpoints. No candidate mechanism became selected. |
| Checklist handoff (Section 22) | Makes the completed A–K documents eligible for final specification review while leaving every `rh-summary.md` checkbox and production gate untouched. |
| Validation-plan status and closing gate | Maps J-P00–J-P20/T0–T6 to K-00–K-12 and Release 0/1/2, adds no new test assertion, and replaces the pre-Phase-K hold with the final owner/reviewer gate. |

No Phase D–J behavior, storage/interface recommendation, validation case, or
historical checkpoint was reversed. These edits do not approve an evidence
scan, test, production file, audit engagement, migration, deployment,
configuration, signer, transaction, or launch.

### 3.15 Phase K handoff integration state

During the Phase K drafting/validation pass, local `rh` and `origin/rh`
remained at `27765d2` and `3e6e6f2`, respectively, but other workstreams
expanded the integration worktree's uncommitted documentation changes. At
handoff, the tracked working-tree paths were:

- `docs/chains/rh-summary.md`;
- `docs/chains/rh/block-clock-validation-plan.md`;
- `docs/chains/rh/block-number-inventory.md`;
- `docs/chains/rh/component-matrix.md`;
- `docs/chains/rh/robinhood-deployment-support-specification.md`;
- `docs/chains/rh/robinhood-deployment-validation-plan.md`;
- `docs/chains/rh/shared-block-clock-specification.md`;
- `docs/chains/rh/track-6-s4-deleverage-cooldown.md`; and
- `docs/chains/rh/track-6-s5-ledger-guard.md`.

The untracked
`docs/chains/rh/minimal-contract-change-reassessment.md` also remained. Those
working-tree versions are not commit-pinned authority. In particular, the
uncommitted S5 edit is not the 1,283-line committed brief hashed in Section
3.13 and was not used to change Track 8's release choices. No contract,
interface, ABI, migration, manifest, default, dependency, test, or other
production artifact was modified in the integration worktree at this
handoff.

Track 8 did not clean, stage, edit, import, or commit any integration-worktree
path. K-CP2 and K-CP4 require a fresh integrated recheck; if any current
working-tree proposal later becomes committed authority, its changed
cross-track constraints must be reconciled then rather than anticipated here.

### 3.16 Minimum-change launch refinement and audit trail

At entry to the owner-directed minimum-change refinement, the isolated Track 8
worktree was clean and synchronized with its backup branch at
`1f719c824b5f10a236286d0a51c9b2a141aa2287`. Local `rh` remained at
`27765d29094256fa9619dd44a0bfd145863de8b7`; `origin/rh` remained at
`3e6e6f230169fc445d0b29454457480c62efd89a`; and the Track 8 merge base
remained `be6a759e15e763b633feefdce91cf8f3ee31a10e`.

The integration worktree still contained the external documentation-only
changes listed in Section 3.15 plus the untracked reassessment. None was read
as committed authority, edited, staged, imported, or committed by Track 8.
The minimum proposal instead re-traced the pinned Teller, BasicVault,
SimpleErc20, SharesVault, StabVault, CreditEngine, AuctionHouse,
MissionControl, Switchboard, and Lootbox source and used the already committed
Base snapshot in Section 5.

The refinement intentionally reaches back to earlier status/gate language:

| Earlier surface | Minimum-change reconciliation |
| --- | --- |
| Status and introduction | Makes Stock Tokens mandatory initial-launch scope and replaces product deferral with an atomic-containment enablement gate. |
| Section 12.1 | Records the later controlling owner direction and safe-stop test without enlarging the documentation-only authorization into implementation. |
| Phase J/K stop language and final checklist | Retains historical checkpoint outcomes but labels Section 23 as controlling; a partial containment group remains disabled, while Stock support itself is no longer deferred. |
| Phase K release model | Reduces initial launch to M0–M5 and moves corrected share, automatic bad debt, Ledger migration, reward-loss accounting, and recapitalization to backlog. |
| Validation-plan status and closing gate | Adds Section 20's minimum property/test/slice contract and supersedes the old product-default sentence. |

No production contract, interface, test, mock, storage layout, ABI, default,
migration, manifest, dependency, CI path, generated artifact, or
`rh-summary.md` was changed. The new proposed filename and test names are
future review targets only.

## 4. Current consumer and ordering trace

### 4.1 Deposit

1. `Teller._deposit` resolves the vault and calls
   `TellerUtils.validateOnDeposit`.
2. Validation reads `getVaultDataOnDeposit` before transfer and applies user and
   global limits to the requested/available amount.
3. Teller executes `transfer` or `transferFrom` to the vault.
4. Teller calls the selected vault's deposit function with the pre-transfer
   amount.
5. The vault returns an amount; Teller then registers vault participation,
   updates Lootbox points, optionally performs housekeeping, records a price
   snapshot, emits `TellerDeposit`, and returns that vault-returned amount.

`BasicVault` sets
`depositAmount = min(passedAmount, IERC20(asset).balanceOf(vault))` and credits
that amount. The clamp is against aggregate post-transfer custody, not the
current call's delta, so prior custody can make a short-received call appear
fully received.
`SharesVault` observes the entire post-transfer balance and computes
`prevTotalBalance = totalAssetBalance - depositAmount`, where
`depositAmount = min(requested, totalAssetBalance)`. A prior donation can affect
the conversion base, and a later short receipt remains indistinguishable from
the requested amount. The same Teller entry point is also used for trusted
Stability Pool and RipeGov flows. Section 14 selects Teller as the shared
measurement boundary and dispositions every identified deposit consumer.

### 4.2 Credit and debt health

`CreditEngine._getUserBorrowTerms` enumerates Ledger user vaults, then each
vault's user assets. It skips an entry when the returned asset is zero **or the
returned amount is zero**. It fetches debt terms, skips zero-LTV assets, values
the amount, and constructs weighted terms using max-debt weight.

Consequences:

- Simple returns nominal amounts even during an aggregate custody deficit, so
  missing custody can support borrowing.
- Merely changing the Simple amount view to zero is not sufficient. The zero
  entry is skipped, which can remove its liquidation threshold and borrow-rate
  weight. Existing debt may then appear healthy, have zero liquidation
  threshold, or become non-progressing unless a separate deficit signal is
  propagated.
- `canBorrow` is global. LTV is an economic parameter, not an immediate,
  custody-independent, per-asset safety switch.
- Debt is account-level; current storage does not attribute an exact slice of
  user debt to a particular collateral asset.

Repayment remains separately callable and must remain available while a
deficit or resolution freeze exists.

### 4.3 Auction settlement

`AuctionHouse._buyFungibleAuction` calculates a maximum collateral value and
calls `_transferCollateral` before taking payment:

- internal mode calls `Vault.transferBalanceWithinVault`, adds the buyer's vault
  participation, and updates buyer rewards; or
- external mode calls `Vault.withdrawTokensFromVault` to deliver the token to
  the recipient.

Only after a nonzero amount and USD value return does AuctionHouse transfer
GREEN to CreditEngine and call `repayDuringAuctionPurchase`. Therefore an
external token-transfer revert rolls back settlement. The unsafe case is the
internal mode: Simple can return a positive nominal amount without proving
custody is live or externally deliverable.

Active auction state is stored in Ledger and is removed when a position reports
depletion. No reservation ledger prevents two nominal claims from referring to
the same remaining aggregate custody after a loss.

### 4.4 Deleverage

The applicable path is external delivery through
`AuctionHouse.withdrawTokensFromVault`. It calculates credited USD value from
the amount the vault reports delivered. This is atomic if the token transfer
reverts. At total live-custody loss, however, the path returns or reverts
without creating repayment value. That preserves payment safety but is a debt
resolution dead end; it is not an exactly-once bad-debt transition.

### 4.5 Rewards and monitoring units

- `Lootbox.updateDepositPoints` reads raw share weight through
  `getUserLootBoxShare`; `SharesVault` returns raw shares divided by
  `DECIMAL_OFFSET`.
- Global asset value reads `getTotalAmountForVault`; `SharesVault` returns live
  custody, while Simple returns nominal total accounting.

Raw shares, token-denominated live claim, and global live value are distinct
units. Any permanent share path must keep those units explicit rather than
silently using one as another.

### 4.6 Registry, deregistration, and recovery

- `VaultBook.startAddressUpdateToRegistry` and
  `startAddressDisableInRegistry` reject a vault whose
  `doesVaultHaveAnyFunds()` returns true.
- `VaultData.deregisterVaultAsset` refuses while its persisted aggregate
  balance is nonzero.
- Vault recovery requires the asset to be unregistered and persisted total
  accounting to be zero.

Therefore a vault that reports accounted funds cannot be casually replaced in
the registry. The guard is not itself a live token-custody scan; Section 5.2
records the concrete vault ID 4 case where donation dust exists while the
accounted-funds result is false. Loss can also leave persisted nominal/share
state that blocks deregistration and recovery even when live custody is zero.

### 4.7 Standing Stock Token configuration constraints

These constraints carry forward unchanged into every architecture outcome and
future implementation/validation phase:

- Stock Token deposits, borrowing, and auction purchases remain disabled until
  the selected shared behavior, exact-token tests, live transferability gate,
  migration, and owner approvals close.
- `AssetConfig.canRedeemCollateral` remains `false`; the resulting
  `MissionControl.getRedeemCollateralConfig()` view must also report the asset
  disabled so CreditRedeem cannot extract Stock Tokens.
- `shouldSwapInStabPools` remains `false` unless governance separately and
  explicitly accepts Stability Pool custody of issuer-controlled collateral.
- Stock Tokens do not route through Base treasury, Endaoment partner liquidity,
  Curve, Aerodrome, Underscore, yield, or any unsupported integration.
- Issuer-controlled treatment remains generic and per-asset; no token-name,
  issuer-name, Robinhood-only, or `chain.id` behavior branch is permitted.

These are standing constraints, not open architecture conveniences. A future
proposal that changes one must return to the owner rather than silently
expanding scope.

### 4.8 AuctionHouseNFT disposition

`AuctionHouseNFT` (`CM-027`) is a temporary Department stub with no fungible or
NFT settlement functions and no calls to the common Vault interface. It does
not consume deposit, amount, internal-transfer, or withdrawal behavior traced
for fungible Stock Tokens. It is therefore **reused unchanged / inapplicable**
to the Track 8 fungible path unless a future NFT implementation introduces a
common Vault consumer; that would require a fresh disposition.

## 5. Live Base exposure

### 5.1 Verification boundary

Committed manifest addresses:

- `VaultBook`: `0xB758e30C14825519b895Fd9928d5d8748A71a944`
- `SimpleErc20`: `0xf75b566eF80Fde0dEfcC045A4d57b540eb43ddfD`
- `RebaseErc20`: `0xce2E96C9F6806731914A7b4c3E4aC1F296d98597`

Read-only Base RPC was pinned to:

- block: `49,036,674`
- block hash:
  `0x030f624ed01a4d2f6eca29774fca774570c2ff0eae80c9ecbaff0cf3381c86e0`
- timestamp: `2026-07-24T03:11:35Z`
- `VaultBook.getAddr(3)`: the manifested `SimpleErc20`
- `VaultBook.getRegId(SimpleErc20)`: `3`
- `VaultBook.getRegId(RebaseErc20)`: `4`
- Simple runtime code hash:
  `0x1d0ec56e109e264dad4435b772deec0026167d96acdb036c51e8b88909b34eb7`
- Rebase runtime code hash:
  `0x21f30af51f5b541329d1e82429851c237a379c07750389810676cccc3f79bef4`
- `SimpleErc20.getNumVaultAssets()`: `27`
- `SimpleErc20.doesVaultHaveAnyFunds()`: `true`
- `RebaseErc20.getNumVaultAssets()`: `6`
- `RebaseErc20.doesVaultHaveAnyFunds()`: `false` (accounted-share semantics;
  see Section 5.2)

The control-surface assessment also used verified Base Blockscout source/ABI
metadata retrieved on 2026-07-23 America/Denver. Explorer metadata is dated
public evidence, not a historical proof of every role holder or every possible
future implementation.

### 5.2 Registered assets and custody

`C` is live token `balanceOf(SimpleErc20)` and `N` is
`SimpleErc20.totalBalances(asset)`, both in raw token units at the pinned block.

| # | Asset | `C / N` | Dated control-surface assessment |
| ---: | --- | ---: | --- |
| 1 | USDC `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` | `0 / 0` | Verified `FiatTokenProxy`; upgrade, pause, blacklist, mint, and burn surfaces. Current burn semantics are not proof of arbitrary vault burn, but upgrade/freeze/short-receipt risk is present. |
| 2 | cbBTC `0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf` | `1,356,929 / 1,356,929` | Verified `FiatTokenProxy`; same controlled/upgradeable surface. Funded. |
| 3 | WETH `0x4200000000000000000000000000000000000006` | `1,149,627,914,921,567,448 / 1,149,627,914,921,567,447` | Verified fixed `WETH9`; no issuer burn, rebase, fee, or upgrade control found. One raw-unit donation/surplus, not a deficit. |
| 4 | cbDOGE `0xcbD06E5A2B0C65597161de254AA074E489dEb510` | `14,500,000,000 / 14,500,000,000` | Verified `FiatTokenProxy`; controlled/upgradeable. Funded. |
| 5 | uSOL `0x9B8Df6E244526ab5F6e6400d331DB28C8fdDdb55` | `823,425,136,048,272,240 / 823,425,136,048,272,240` | Verified beacon proxy with upgrade, blacklist, mint, and burn surfaces. Funded. |
| 6 | Morpho Spark USDC `0x7BfA7C4f149E7415b73bdeDfe609237e29CBF34A` | `0 / 0` | Verified non-proxy MetaMorpho vault. Owner fee/skim controls and underlying loss can reduce share value; no direct holder-share confiscation was established. |
| 7 | AERO `0x940181a94A35A4569E4529A3CDfB74e38FD98631` | `91,859,213,070,865,428,334 / 91,859,213,070,865,428,334` | Verified fixed token with minter surface; no holder-balance burn, rebase, fee, or upgrade control found. Funded. |
| 8 | Moonwell AERO `0x73902f619CEB9B31FD8EFecf435CbDf89E369Ba6` | `0 / 0` | Verified delegator/implementation architecture with admin implementation change and seize surface. Share value can change; upgrade risk exists. |
| 9 | cbXRP `0xcb585250f852C6c6bf90434AB21A00f02833a4af` | `0 / 0` | Verified `FiatTokenProxy`; controlled/upgradeable. |
| 10 | WELL `0xA88594D404727625A9437C3f886C7643872296AE` | `11,986,269,878,969,919,127,060 / 11,986,269,878,969,919,127,060` | Verified transparent proxy with upgrade, pause, mint, and burn surfaces. Funded. |
| 11 | VIRTUAL `0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b` | `1,054,012,762,792,834,343,376 / 1,054,012,762,792,834,343,376` | Verified Optimism mintable bridge token with privileged mint/burn surface. Funded. |
| 12 | VVV `0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf` | `0 / 0` | Verified fixed token with owner/mint surface; no holder-balance burn, rebase, fee, or upgrade control found. |
| 13 | DEGEN `0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed` | `0 / 0` | Verified fixed token with pause and self/allowance burn surfaces; no arbitrary holder-balance reduction established. |
| 14 | Moonwell cbETH `0x3bf93770f2d4a794c3d9EBEfBAeBAE2a8f09A5E5` | `0 / 0` | Verified delegator/implementation architecture; upgrade and seize surfaces; share-value loss remains possible. |
| 15 | cbETH `0x2Ae3F1Ec7F1F5012CFEab0185bfc7aa3cf0DEc22` | `800,000,000,000,000,000 / 800,000,000,000,000,000` | Verified upgradeable bridge-token proxy with privileged mint/burn surface. Funded. |
| 16 | Moonwell USDC `0xEdc817A28E8B93B03976FBd4a3dDBc9f7D176c22` | `0 / 0` | Verified delegator/implementation architecture; upgrade and seize surfaces. |
| 17 | Morpho Moonwell USDC `0xc1256Ae5FF1cf2719D4937adb3bbCCab2E00A2Ca` | `0 / 0` | Verified non-proxy MetaMorpho vault; share value can fall through underlying loss; owner fee/skim surfaces do not by themselves prove holder-share confiscation. |
| 18 | Morpho Seamless USDC `0x616a4E1db48e22028f6bbf20444Cd3b8e3273738` | `0 / 0` | Same class as other MetaMorpho shares. |
| 19 | Fluid USDC `0xf42f5795D9ac7e9D757dB633D693cD548Cfd9169` | `0 / 0` | Verified `fToken`; share value can change. No direct holder-unit confiscation, rebase, transfer fee, or proxy was established from the dated ABI. |
| 20 | Euler USDC `0x0A1a3b5f2041F33522C4efc754a7D096f880eE16` | `0 / 0` | Verified beacon-proxy EVault; upgrade and share-value loss risk. |
| 21 | Moonwell cbBTC `0xF877ACaFA28c19b96727966690b2f44d35aD5976` | `0 / 0` | Verified delegator/implementation architecture; upgrade and seize surfaces. |
| 22 | Morpho Moonwell WETH `0xa0E430870c4604CcfC7B38Ca7845B1FF653D0ff1` | `0 / 0` | Verified non-proxy MetaMorpho vault; share-value loss risk. |
| 23 | Morpho Seamless WETH `0x27D8c7273fd3fcC6956a0B370cE5Fd4A7fc65c18` | `0 / 0` | Verified non-proxy MetaMorpho vault; share-value loss risk. |
| 24 | Euler WETH `0x859160DB5841E5cfB8D3f144C6b3381A85A4b410` | `0 / 0` | Verified beacon-proxy EVault; upgrade and share-value loss risk. |
| 25 | Morpho Moonwell cbBTC `0x543257eF2161176D7C8cD90BA65C2d4CaEF5a796` | `0 / 0` | Verified non-proxy MetaMorpho vault; share-value loss risk. |
| 26 | sUSDe `0x211Cc4DD073734dA055fbF44a2b4667d5E5fE5d2` | `830,694,343,423,510,974 / 830,694,343,423,510,974` | Verified `StakedUSDeOFT` exposes blacklist and `redistributeBlackListedFunds`. This is an explicit mechanism capable of moving a blacklisted holder's funds independently of Ripe accounting. Funded. |
| 27 | wrapped superOETH `0x7FcD174E80f264448ebeE8c88a7C4476AAF58Ea6` | `0 / 0` | Verified upgradeable proxy; underlying/share-value loss and upgrade risk. |

At the pinned block, all funded assets were solvent in nominal accounting; WETH
had a one-unit surplus. This snapshot does not prove future safety.

For completeness, vault ID 4 (`RebaseErc20`) had the following six registered
assets at the same block. Here `C` is live token custody and `S` is
`RebaseErc20.totalBalances(asset)`, which stores aggregate raw shares.
Names/symbols were read from the listed tokens at the pinned block.

| # | Asset | `C / S` in raw units | Current implication |
| ---: | --- | ---: | --- |
| 1 | Compound AERO (`cAEROv3`) `0x784efeB622244d2348d4F2522f8860B96fbEcE89` | `0 / 0` | Registered; no custody or accounted shares. |
| 2 | Aave Base cbBTC (`aBascbBTC`) `0xBdb9300b7CDE636d9cD4AFF00f6F009fFBBc8EE6` | `1 / 0` | One smallest-unit unaccounted donation/dust; no user shares. |
| 3 | Aave Base USDC (`aBasUSDC`) `0x4e65fE4DbA92790696d040ac24Aa414708F5c0AB` | `1 / 0` | One smallest-unit unaccounted donation/dust; no user shares. |
| 4 | Aave Base WETH (`aBasWETH`) `0xD4a0e0b9149BCee3C920d2E00b5dE09138fd8bb7` | `1 / 0` | One smallest-unit unaccounted donation/dust; no user shares. |
| 5 | Compound USDC (`cUSDCv3`) `0xb125E6687d4313864e53df431d5425969c15Eb2F` | `0 / 0` | Registered; no custody or accounted shares. |
| 6 | Compound WETH (`cWETHv3`) `0x46e6b214b524310239732D51387075E0e70970bf` | `0 / 0` | Registered; no custody or accounted shares. |

`RebaseErc20.doesVaultHaveAnyFunds() == false` is therefore an
**accounted-share result**, not proof of literal zero ERC-20 custody:
`VaultData.doesVaultHaveAnyFunds()` iterates registered assets and checks
`totalBalances`, while three assets contain one raw token unit with zero
shares. No live user-funded share exposure is evidenced at this block, but a
future migration/recovery plan must reconcile registered assets and incidental
custody separately.

The three `C = 1, S = 0` rows are live instances of Section 8 state 2,
**pre-existing donation**: custody exists without a user claim, and a later
deposit must not treat that custody as the call's receipt.

Operationally, the false funds result means VaultBook's live-funds precondition
would not block an otherwise authorized
`startAddressUpdateToRegistry(4, ...)` or
`startAddressDisableInRegistry(4)` while those three raw units remain in vault
4. The normal governance/registry timing still applies, and neither operation
automatically moves the tokens. A migration or disable plan therefore cannot
use this boolean alone as proof of empty custody.

### 5.3 Base urgency conclusion

**Recommendation, not approval:** Release 1 is an urgent live Base hardening
requirement, even if Robinhood ultimately uses the permanent share path.

Reasoning:

1. Base currently routes vault ID 3 to the unsafe nominal Simple path.
2. Nine registered assets had positive custody at the pinned block.
3. Funded `sUSDe` exposes an explicit blacklist-funds redistribution surface.
4. Funded cbBTC, cbDOGE, uSOL, WELL, VIRTUAL, and cbETH have issuer, bridge,
   proxy, beacon, pause, blacklist, burn, or upgrade controls.
5. The current deposit path can create a deficit through short receipt even
   without issuer confiscation.

The current no-deficit snapshot reduces immediate incident evidence; it does
not remove the reachable invariant failure. Any Base change still requires the
owner to approve the live-version and custody-bearing migration posture.

### 5.4 Reproducibility appendix

#### Endpoints and retrieval times

- Pinned JSON-RPC endpoint:
  `https://mainnet.base.org`
- Verified-source metadata endpoint template:
  `https://base.blockscout.com/api/v2/smart-contracts/{address}`
- Initial RPC/source retrieval:
  2026-07-23 America/Denver
- Review repeat for registry and funded-status reads:
  `2026-07-24T03:46:40Z`
- Complete raw registry/custody/accounting response capture:
  `2026-07-24T04:07:01Z`

No secret, authenticated endpoint, write method, signing operation, or broadcast
was used.

The successful historical `eth_call` reads establish that
`https://mainnet.base.org` served state for the pinned block at capture time.
Reproduction later still requires an endpoint that retains historical state;
public endpoint archive availability and rate limits are not guaranteed.

#### RPC method transcript

The address table above is the decoded result of indices `1..27`; `C / N` is
the decoded pair from the last two calls for each address.

```text
cast block 49036674 --json --rpc-url https://mainnet.base.org

cast call 0xB758e30C14825519b895Fd9928d5d8748A71a944 \
  'getAddr(uint256)(address)' 3 \
  --block 49036674 --rpc-url https://mainnet.base.org

cast call 0xB758e30C14825519b895Fd9928d5d8748A71a944 \
  'getRegId(address)(uint256)' \
  0xf75b566eF80Fde0dEfcC045A4d57b540eb43ddfD \
  --block 49036674 --rpc-url https://mainnet.base.org

cast call 0xB758e30C14825519b895Fd9928d5d8748A71a944 \
  'getRegId(address)(uint256)' \
  0xce2E96C9F6806731914A7b4c3E4aC1F296d98597 \
  --block 49036674 --rpc-url https://mainnet.base.org

cast call 0xf75b566eF80Fde0dEfcC045A4d57b540eb43ddfD \
  'getNumVaultAssets()(uint256)' \
  --block 49036674 --rpc-url https://mainnet.base.org

cast call 0xf75b566eF80Fde0dEfcC045A4d57b540eb43ddfD \
  'vaultAssets(uint256)(address)' <index> \
  --block 49036674 --rpc-url https://mainnet.base.org

cast call <asset> 'balanceOf(address)(uint256)' \
  0xf75b566eF80Fde0dEfcC045A4d57b540eb43ddfD \
  --block 49036674 --rpc-url https://mainnet.base.org

cast call 0xf75b566eF80Fde0dEfcC045A4d57b540eb43ddfD \
  'totalBalances(address)(uint256)' <asset> \
  --block 49036674 --rpc-url https://mainnet.base.org

cast call <vault> 'doesVaultHaveAnyFunds()(bool)' \
  --block 49036674 --rpc-url https://mainnet.base.org

cast codehash <vault> \
  --block 49036674 --rpc-url https://mainnet.base.org
```

The review repeat returned:

```text
RebaseErc20.getNumVaultAssets()      => 6
RebaseErc20.doesVaultHaveAnyFunds() => false
SimpleErc20.doesVaultHaveAnyFunds() => true
```

#### Raw historical-read snapshot

The JSON below is committed inside this owned specification rather than as a
third Track 8 deliverable. Requests are recorded as command shapes above; the
per-asset request calldata is not duplicated here. Each response leaf under
`result`/`asset`/`custody`/`accounting` is the verbatim hex string from the
JSON-RPC `eth_call` result, with only transport envelopes and request IDs
omitted. `accounting` means nominal `totalBalances` for Simple and raw-share
`totalBalances` for Rebase. Every request used block tag `0x2ec3d82`.

```json
{
  "schema": "ripe.track8.base-vault-state.v1",
  "capturedAt": "2026-07-24T04:07:01Z",
  "rpc": "https://mainnet.base.org",
  "block": {
    "number": 49036674,
    "tag": "0x2ec3d82",
    "hash": "0x030f624ed01a4d2f6eca29774fca774570c2ff0eae80c9ecbaff0cf3381c86e0"
  },
  "vaultBook": {
    "getAddr3": {
      "calldata": "0xd81f84b70000000000000000000000000000000000000000000000000000000000000003",
      "result": "0x000000000000000000000000f75b566ef80fde0defcc045a4d57b540eb43ddfd"
    },
    "getRegIdSimple": {
      "calldata": "0xc4d9ba63000000000000000000000000f75b566ef80fde0defcc045a4d57b540eb43ddfd",
      "result": "0x0000000000000000000000000000000000000000000000000000000000000003"
    },
    "getRegIdRebase": {
      "calldata": "0xc4d9ba63000000000000000000000000ce2e96c9f6806731914a7b4c3e4ac1f296d98597",
      "result": "0x0000000000000000000000000000000000000000000000000000000000000004"
    }
  },
  "simple": {
    "address": "0xf75b566eF80Fde0dEfcC045A4d57b540eb43ddfD",
    "getNumVaultAssets": {
      "calldata": "0x28788f26",
      "result": "0x000000000000000000000000000000000000000000000000000000000000001b"
    },
    "doesVaultHaveAnyFunds": {
      "calldata": "0xa82e46fc",
      "result": "0x0000000000000000000000000000000000000000000000000000000000000001"
    },
    "assets": [
      {
        "index": 1,
        "asset": "0x000000000000000000000000833589fcd6edb6e08f4c7c32d4f71b54bda02913",
        "custody": "0x0000000000000000000000000000000000000000000000000000000000000000",
        "accounting": "0x0000000000000000000000000000000000000000000000000000000000000000"
      },
      {
        "index": 2,
        "asset": "0x000000000000000000000000cbb7c0000ab88b473b1f5afd9ef808440eed33bf",
        "custody": "0x000000000000000000000000000000000000000000000000000000000014b481",
        "accounting": "0x000000000000000000000000000000000000000000000000000000000014b481"
      },
      {
        "index": 3,
        "asset": "0x0000000000000000000000004200000000000000000000000000000000000006",
        "custody": "0x0000000000000000000000000000000000000000000000000ff44c7f64c5e4d8",
        "accounting": "0x0000000000000000000000000000000000000000000000000ff44c7f64c5e4d7"
      },
      {
        "index": 4,
        "asset": "0x000000000000000000000000cbd06e5a2b0c65597161de254aa074e489deb510",
        "custody": "0x0000000000000000000000000000000000000000000000000000000360447100",
        "accounting": "0x0000000000000000000000000000000000000000000000000000000360447100"
      },
      {
        "index": 5,
        "asset": "0x0000000000000000000000009b8df6e244526ab5f6e6400d331db28c8fdddb55",
        "custody": "0x0000000000000000000000000000000000000000000000000b6d64cc6d48f370",
        "accounting": "0x0000000000000000000000000000000000000000000000000b6d64cc6d48f370"
      },
      {
        "index": 6,
        "asset": "0x0000000000000000000000007bfa7c4f149e7415b73bdedfe609237e29cbf34a",
        "custody": "0x0000000000000000000000000000000000000000000000000000000000000000",
        "accounting": "0x0000000000000000000000000000000000000000000000000000000000000000"
      },
      {
        "index": 7,
        "asset": "0x000000000000000000000000940181a94a35a4569e4529a3cdfb74e38fd98631",
        "custody": "0x000000000000000000000000000000000000000000000004facd7b98d3da6f6e",
        "accounting": "0x000000000000000000000000000000000000000000000004facd7b98d3da6f6e"
      },
      {
        "index": 8,
        "asset": "0x00000000000000000000000073902f619ceb9b31fd8efecf435cbdf89e369ba6",
        "custody": "0x0000000000000000000000000000000000000000000000000000000000000000",
        "accounting": "0x0000000000000000000000000000000000000000000000000000000000000000"
      },
      {
        "index": 9,
        "asset": "0x000000000000000000000000cb585250f852c6c6bf90434ab21a00f02833a4af",
        "custody": "0x0000000000000000000000000000000000000000000000000000000000000000",
        "accounting": "0x0000000000000000000000000000000000000000000000000000000000000000"
      },
      {
        "index": 10,
        "asset": "0x000000000000000000000000a88594d404727625a9437c3f886c7643872296ae",
        "custody": "0x000000000000000000000000000000000000000000000289c6e8f4f18e68be14",
        "accounting": "0x000000000000000000000000000000000000000000000289c6e8f4f18e68be14"
      },
      {
        "index": 11,
        "asset": "0x0000000000000000000000000b3e328455c4059eeb9e3f84b5543f74e24e7e1b",
        "custody": "0x000000000000000000000000000000000000000000000039235d8f5c72f3a1d0",
        "accounting": "0x000000000000000000000000000000000000000000000039235d8f5c72f3a1d0"
      },
      {
        "index": 12,
        "asset": "0x000000000000000000000000acfe6019ed1a7dc6f7b508c02d1b04ec88cc21bf",
        "custody": "0x0000000000000000000000000000000000000000000000000000000000000000",
        "accounting": "0x0000000000000000000000000000000000000000000000000000000000000000"
      },
      {
        "index": 13,
        "asset": "0x0000000000000000000000004ed4e862860bed51a9570b96d89af5e1b0efefed",
        "custody": "0x0000000000000000000000000000000000000000000000000000000000000000",
        "accounting": "0x0000000000000000000000000000000000000000000000000000000000000000"
      },
      {
        "index": 14,
        "asset": "0x0000000000000000000000003bf93770f2d4a794c3d9ebefbaebae2a8f09a5e5",
        "custody": "0x0000000000000000000000000000000000000000000000000000000000000000",
        "accounting": "0x0000000000000000000000000000000000000000000000000000000000000000"
      },
      {
        "index": 15,
        "asset": "0x0000000000000000000000002ae3f1ec7f1f5012cfeab0185bfc7aa3cf0dec22",
        "custody": "0x0000000000000000000000000000000000000000000000000b1a2bc2ec500000",
        "accounting": "0x0000000000000000000000000000000000000000000000000b1a2bc2ec500000"
      },
      {
        "index": 16,
        "asset": "0x000000000000000000000000edc817a28e8b93b03976fbd4a3ddbc9f7d176c22",
        "custody": "0x0000000000000000000000000000000000000000000000000000000000000000",
        "accounting": "0x0000000000000000000000000000000000000000000000000000000000000000"
      },
      {
        "index": 17,
        "asset": "0x000000000000000000000000c1256ae5ff1cf2719d4937adb3bbccab2e00a2ca",
        "custody": "0x0000000000000000000000000000000000000000000000000000000000000000",
        "accounting": "0x0000000000000000000000000000000000000000000000000000000000000000"
      },
      {
        "index": 18,
        "asset": "0x000000000000000000000000616a4e1db48e22028f6bbf20444cd3b8e3273738",
        "custody": "0x0000000000000000000000000000000000000000000000000000000000000000",
        "accounting": "0x0000000000000000000000000000000000000000000000000000000000000000"
      },
      {
        "index": 19,
        "asset": "0x000000000000000000000000f42f5795d9ac7e9d757db633d693cd548cfd9169",
        "custody": "0x0000000000000000000000000000000000000000000000000000000000000000",
        "accounting": "0x0000000000000000000000000000000000000000000000000000000000000000"
      },
      {
        "index": 20,
        "asset": "0x0000000000000000000000000a1a3b5f2041f33522c4efc754a7d096f880ee16",
        "custody": "0x0000000000000000000000000000000000000000000000000000000000000000",
        "accounting": "0x0000000000000000000000000000000000000000000000000000000000000000"
      },
      {
        "index": 21,
        "asset": "0x000000000000000000000000f877acafa28c19b96727966690b2f44d35ad5976",
        "custody": "0x0000000000000000000000000000000000000000000000000000000000000000",
        "accounting": "0x0000000000000000000000000000000000000000000000000000000000000000"
      },
      {
        "index": 22,
        "asset": "0x000000000000000000000000a0e430870c4604ccfc7b38ca7845b1ff653d0ff1",
        "custody": "0x0000000000000000000000000000000000000000000000000000000000000000",
        "accounting": "0x0000000000000000000000000000000000000000000000000000000000000000"
      },
      {
        "index": 23,
        "asset": "0x00000000000000000000000027d8c7273fd3fcc6956a0b370ce5fd4a7fc65c18",
        "custody": "0x0000000000000000000000000000000000000000000000000000000000000000",
        "accounting": "0x0000000000000000000000000000000000000000000000000000000000000000"
      },
      {
        "index": 24,
        "asset": "0x000000000000000000000000859160db5841e5cfb8d3f144c6b3381a85a4b410",
        "custody": "0x0000000000000000000000000000000000000000000000000000000000000000",
        "accounting": "0x0000000000000000000000000000000000000000000000000000000000000000"
      },
      {
        "index": 25,
        "asset": "0x000000000000000000000000543257ef2161176d7c8cd90ba65c2d4caef5a796",
        "custody": "0x0000000000000000000000000000000000000000000000000000000000000000",
        "accounting": "0x0000000000000000000000000000000000000000000000000000000000000000"
      },
      {
        "index": 26,
        "asset": "0x000000000000000000000000211cc4dd073734da055fbf44a2b4667d5e5fe5d2",
        "custody": "0x0000000000000000000000000000000000000000000000000b87381aa8af49be",
        "accounting": "0x0000000000000000000000000000000000000000000000000b87381aa8af49be"
      },
      {
        "index": 27,
        "asset": "0x0000000000000000000000007fcd174e80f264448ebee8c88a7c4476aaf58ea6",
        "custody": "0x0000000000000000000000000000000000000000000000000000000000000000",
        "accounting": "0x0000000000000000000000000000000000000000000000000000000000000000"
      }
    ]
  },
  "rebase": {
    "address": "0xce2E96C9F6806731914A7b4c3E4aC1F296d98597",
    "getNumVaultAssets": {
      "calldata": "0x28788f26",
      "result": "0x0000000000000000000000000000000000000000000000000000000000000006"
    },
    "doesVaultHaveAnyFunds": {
      "calldata": "0xa82e46fc",
      "result": "0x0000000000000000000000000000000000000000000000000000000000000000"
    },
    "assets": [
      {
        "index": 1,
        "asset": "0x000000000000000000000000784efeb622244d2348d4f2522f8860b96fbece89",
        "custody": "0x0000000000000000000000000000000000000000000000000000000000000000",
        "accounting": "0x0000000000000000000000000000000000000000000000000000000000000000"
      },
      {
        "index": 2,
        "asset": "0x000000000000000000000000bdb9300b7cde636d9cd4aff00f6f009ffbbc8ee6",
        "custody": "0x0000000000000000000000000000000000000000000000000000000000000001",
        "accounting": "0x0000000000000000000000000000000000000000000000000000000000000000"
      },
      {
        "index": 3,
        "asset": "0x0000000000000000000000004e65fe4dba92790696d040ac24aa414708f5c0ab",
        "custody": "0x0000000000000000000000000000000000000000000000000000000000000001",
        "accounting": "0x0000000000000000000000000000000000000000000000000000000000000000"
      },
      {
        "index": 4,
        "asset": "0x000000000000000000000000d4a0e0b9149bcee3c920d2e00b5de09138fd8bb7",
        "custody": "0x0000000000000000000000000000000000000000000000000000000000000001",
        "accounting": "0x0000000000000000000000000000000000000000000000000000000000000000"
      },
      {
        "index": 5,
        "asset": "0x000000000000000000000000b125e6687d4313864e53df431d5425969c15eb2f",
        "custody": "0x0000000000000000000000000000000000000000000000000000000000000000",
        "accounting": "0x0000000000000000000000000000000000000000000000000000000000000000"
      },
      {
        "index": 6,
        "asset": "0x00000000000000000000000046e6b214b524310239732d51387075e0e70970bf",
        "custody": "0x0000000000000000000000000000000000000000000000000000000000000000",
        "accounting": "0x0000000000000000000000000000000000000000000000000000000000000000"
      }
    ]
  }
}
```

For control classification, each full asset address was fetched through the
Blockscout endpoint above. The recorded fields were verified contract name,
proxy type, implementation address/name when present, verification status, and
ABI function names matching upgrade, implementation, admin, owner, pause,
blacklist, burn, mint, seize, skim, fee, or redistribution behavior. The most
consequential direct-custody evidence is reproducible at:

```text
https://base.blockscout.com/api/v2/smart-contracts/0x211Cc4DD073734dA055fbF44a2b4667d5E5fE5d2
```

That verified ABI includes `blackList`, `updateBlackList`, and
`redistributeBlackListedFunds`. Classification still does not claim that every
listed method is exercisable by every role or that latest explorer metadata is
historical proof at the pinned block; unknown authority/role state remains
unknown.

## 6. Formal state model

For each vault `v`, asset `a`, user `u`, and state/time `t`:

| Symbol | Definition |
| --- | --- |
| `C_t` | Actual live ERC-20 custody: `IERC20(a).balanceOf(v)` at `t`. |
| `A^s_t` | Persisted token-denominated assets allocated to the share supply under the corrected share path. Current `SharesVault` has no such state. |
| `U^s_t` | Persisted token-denominated quarantined custody at the last successful checkpoint. It has no automatic beneficiary and is kept distinct so a later observed loss cannot silently use a donation to shield shareholder backing. |
| `A_t` | Effective allocated backing, `min(A^s_t, max(C_t - U^s_t, 0))`. Every successful state-changing share operation checkpoints both allocation buckets; conversion, credit, settlement, and rewards use `A`, never raw `C`. |
| `U_t` | Effective unallocated/quarantined custody, `C_t - A_t`. An unsolicited donation, positive delta, or restoration does not increase `A^s`; therefore it cannot create a live user claim without a separately approved allocation transaction. |
| `q` | Requested transfer amount for the current call. |
| `C^-`, `C^+` | Custody immediately before and after the call's token-transfer boundary. |
| `R` | Actual per-call receipt. When `C^+ >= C^-`, `R = C^+ - C^-`; a negative or unclassifiable delta must not create credit. |
| `N_u`, `N` | Raw nominal user balance and aggregate nominal balance, with `N = ΣN_u`, for a nominal vault. |
| `s_u`, `S` | Raw user shares and aggregate raw share supply, with `S = Σs_u`, for a share vault. |
| `L_u(A,S)` | User's token-denominated live claim under the Phase G conversion and rounding rules in Section 17. It is based on allocated backing `A`, not raw custody `C`, so quarantined `U` is not assigned to shareholders. |
| `K` | Aggregate allocable live claims, `K = ΣL_u`, including defined rounding bounds. |
| `B_u` | Token amount exposed by this asset to CreditEngine for borrowing and debt health. |
| `D_u` | Amount currently and safely deliverable to or for `u`, after backing, allocation, settlement-policy, pause, and blocklist checks. |
| `δ` | Nominal deficit: `max(N - C, 0)`. `deficit := δ > 0`. |
| `Z_custody` | Absolute custody-zero state, `S > 0 ∧ C = 0`. |
| `Z_live` | Immediately observable allocated-backing total-loss state, `S > 0 ∧ A = 0`; it includes `Z_custody` and the case where only quarantined `U` remains. |
| `Z_recorded` | Persistent post-zero state, `S > 0 ∧ A^s = 0`; after a loss checkpoint it remains true when later custody appears as `U`. |
| `P/BL/I` | Observable pause, relevant sender/recipient/operator blocklist, and implementation/beacon identity or change state. Unknown is not equivalent to safe. |
| `E_u` | User debt for an account that includes this asset. Current storage is account-level; no exact asset-attributed debt split exists. |
| `X` | Active auction claims/targets for `(v,a)` and their settlement state. |
| `BD` | Protocol bad debt recorded in Ledger. |

For a nominal path, token-denominated persisted accounting is `N`. For the
corrected share path, persisted accounting includes raw shares `S` plus the
allocated/quarantine checkpoints `A^s` and `U^s`; `L_u`, `K`, `C`, `A`, and
`U` must be reported separately. Current `SharesVault` persists only `S` and
derives every claim directly from `C`, so it cannot enforce the approved
no-automatic-allocation policy unchanged.

## 7. Formal invariants

The identifiers below are shared with the validation-plan draft.

### I-01 — exact receipt and donation isolation

For each deposit call:

```text
credited_token_amount = R
0 <= R <= q unless an explicit excess-receipt policy is owner-approved
prior custody not received by this call cannot be credited to this depositor
```

Any unexpected negative delta, callback ambiguity, or implementation change
must revert or otherwise commit zero credit.

### I-02 — aggregate borrowing conservation

```text
Σ B_u(v,a) <= C(v,a)
for the corrected share path: Σ B_u(v,a) <= A(v,a) <= C(v,a)
```

No user or combination of users may borrow against the same custody twice.

### I-03 — claim and settlement conservation

```text
Σ live claims allocated or settled from (v,a) <= A(v,a) <= C(v,a)
```

Quarantined `U` is excluded. Rounding dust must have an explicit bound and
disposition.

### I-04 — pay only for delivered collateral

For every auction, redemption, deleverage, or other collateral settlement:

```text
GREEN paid or debt reduced
    <= price(value of collateral actually and safely delivered)
```

An internal ledger move is not "safely delivered" for an issuer-controlled
asset unless the owner explicitly rejects the external-only policy and the
design separately proves live backing and later deliverability.

### I-05 — failed-delivery atomicity

Failed or false-returning token delivery, pause, blocklist, deficit guard, or
behavior switch cannot commit any of:

- GREEN payment;
- debt reduction;
- buyer claim;
- internal user-balance transfer;
- auction progress/removal; or
- reward/participation state derived from settlement.

### I-06 — deficit visibility

Fail-closed zero borrowing value must not erase the fact that existing debt is
unsafe. The derived deficit result must remain visible to previews, borrow
validation, account health, liquidation/resolution eligibility, and
getter-based monitoring even when `B_u = 0`. Existing configuration events
must identify the applied control state; no new stored deficit event is
required.

### I-07 — no new debt under an unsafe asset

If existing `canDeposit` is disabled, `DebtTerms.ltv == 0`, `δ > 0`,
`Z_custody`, `Z_live`, `Z_recorded`, or the backing check is unknown/failing:

```text
new borrowing capacity contributed by (v,a) = 0
```

Unrelated solvent collateral retains its correct capacity.

### I-08 — liability conservation and exactly once

At an approved bad-debt transition of amount `x`:

```text
user debt after = user debt before - x
protocol bad debt after = protocol bad debt before + x
```

The transition must be marked so it cannot repeat. The same `x` cannot remain
both as user debt and Ledger bad debt, and it cannot disappear from both.
Interest and repayments before the transition must use one pinned debt state.

### I-09 — repayment liveness

Repayment remains available before a bad-debt transition even when deposits,
borrowing, internal settlement, new auctions, or withdrawals are frozen.

### I-10 — post-zero non-interference

When `Z_live` or `Z_recorded` holds, a new depositor cannot recapitalize old
claims, erase them, or capture later restoration by accident. New deposits
remain frozen unless an explicit owner-approved recapitalization/allocation
procedure proves otherwise.

### I-11 — issuer-controlled external settlement

Under the recommended policy, issuer-controlled collateral is always settled
externally. Buyer-selected internal settlement is unavailable.

### I-12 — custody control is price-independent

Custody backing and the derived per-asset collateral-use check do not depend on
a valid, nonzero oracle price. Missing price may independently block valuation;
it must not hide or clear a custody deficit.

### I-13 — unallocated custody is not a claim

For the corrected share path:

```text
U = C - A
deposit share price, live claims, borrowing value, settlement, and rewards
    use A and exclude U
an unsolicited positive custody delta cannot increase A
after a successful checkpoint, an external negative delta reduces A before
    reducing the separately checkpointed U
```

Only an explicit, separately owner-approved allocation or recapitalization
transaction may move value from `U` into `A`. Merely observing restored
custody, receiving a new user deposit, or changing an oracle price is
insufficient.

## 8. Required state behavior

| State | Safety behavior | Liveness result | Allocation/policy | Operator evidence |
| --- | --- | --- | --- | --- |
| 1. Solvent ordinary operation | Credit exactly `R`; `ΣB`, `K`, and settlement remain bounded by `A <= C`. | Deposits, borrow, repay, withdrawal, and approved settlement can progress. | Phase G formulas round deposit shares down and withdrawal shares up; the last-share sweep is bounded by `A`. | `C`, `A`, `U`, raw shares, live claims, and normal events. |
| 2. Pre-existing donation | The donation is neither the next depositor's `R` nor allocated backing. | Deposit may proceed if call-local receipt is measured and `A > 0` or `S = 0`. | Donation remains `U`; no automatic shareholder, depositor, or protocol allocation. | Expose `C`, `A`, and `U` separately. |
| 3. Donation between deposits | Later depositor cannot capture the donation through receipt inference or share pricing. | Ordinary existing positions continue against unchanged `A`; separately approved recovery may progress later. | Donation remains `U` and does not change claims/rewards. | Record first `C > A` observation and resulting `U`. |
| 4. Short receipt / fee on transfer | Credit `R`, not `Q`; zero receipt commits no credit. | General call succeeds only if `R` satisfies minimums; exact callers or invalid deltas revert atomically. | Transfer fee remains external; `R > Q` reverts rather than being allocated. | `A_req`, `Q`, `R`, credited, returned, and event amounts must reconcile. |
| 5. Partial issuer reduction | Nominal path sets deficit and disables new borrowing/internal settlement; after a successful bucket checkpoint, the corrected share path reduces `A` before `U` and reprices shares pro rata. | Repay and safely allocable external delivery remain possible. | Checkpointed `U` is not silently consumed to shield shares; any later positive delta is new `U`, not automatic restoration. | Expose `C`, `A^s`, `U^s`, `A`, `U`, `N` or `S`, claims, `δ`, flags, and affected auctions. |
| 6. Aggregate nominal deficit | `B=0` for affected asset while the derived deficit keeps existing debt unsafe/visible. | Repay remains open; loss settlement freezes absent policy. | No silent `min(userNominal,C)` or pro rata. | Reconstruct `C<T` and credit/health outputs from same-block getters independently of price. |
| 7. Total custody loss with claims | No paid auction or collateral settlement for missing tokens; a successful state-changing checkpoint records `A^s = U^s = 0`. | Repay remains open; position becomes resolution-eligible under Phase F. | Exactly-once debt transition is specified; it does not erase shares or allocate later property. | `Z_custody`, `C=0`, `A=0`, raw shares positive, debt, and transition state observable. |
| 8. Zero custody, nonzero shares | Withdrawal/internal value transfer cannot invent value; `Z_custody` and `Z_live` freeze immediately and `Z_recorded` persists after checkpoint. | Repayment and Phase F resolution remain open; new deposits and value-bearing share transfers are closed. | Old shares remain registered and explicit with zero live claim/reward weight; no automatic erasure. | All zero-state predicates, raw shares, zero claim, and checkpoint event. |
| 9. Donation/restoration after zero | Custody becomes `U`; `A` and old claims remain zero after `Z_recorded`. | No allocation/recovery progresses without a separate owner, counsel/risk, and implementation approval. | The owner selected no automatic allocation and did not approve recapitalization. | Source/amount if knowable, `C`, `A=0`, `U`, unchanged claims, and no allocation event. |
| 10. Attempted new deposit after zero | Revert atomically before credit/share mint when any applicable zero predicate holds. | Deposit intentionally unavailable; transfer rollback leaves custody/accounting unchanged. | No fresh depositor can recapitalize old shares or dilute/erase them. | Clear post-zero freeze reason and unchanged `C`, `A^s`, `U^s`, `A`, `U`, `S`, and user state. |
| 11. Paused transfer | External delivery/deposit reverts; no downstream payment or accounting commits. | Retryable after unpause; repayment remains independent. | Internal settlement disabled for issuer-controlled assets. | Observable pause where supported; otherwise failure diagnostics. |
| 12. Sender/recipient/operator blocklist | Relevant transfer reverts atomically. | Retry with an eligible endpoint only where policy permits. | No bypass via internal claim for issuer-controlled assets. | Report which role failed when observable. |
| 13. Active auction before issuer action | Recheck backing/deliverability at purchase; do not rely on creation-time amount. | Auction may pause/fail without charging buyer. | Remaining custody cannot be allocated twice. | Auction state, custody-change point, and zero committed progress. |
| 14. Liquidation after issuer action | Do not manufacture a zero-backed auction; preserve deficit in health/resolution state. | Repay or approved resolution can progress. | Owner chooses total-loss transition. | Distinguish liquidation eligibility from auction eligibility. |
| 15. Implementation/beacon change | Re-evaluate receipt and delivery behavior; unsafe/unknown state fails closed. | Resume only after approved verification/re-enable. | Re-enable authority must be stronger than emergency disable. | Implementation/beacon/code identity and change evidence. |
| 16. Recovery/migration with users/debt | Disable old deposits; reconcile users, `C`, `A^s`, `U^s`, `A`, `U`, debt, auctions, and raw accounting before movement/retirement. | Abort/rollback must preserve one authoritative state. | Recovery can move only separately approved `U`, never allocated backing; migration remains owner-gated. | Before/after manifest, registry, balances, allocation, debt, auction, and reconciliation record. |

The table intentionally separates safety from liveness. A revert can prevent
theft while still leaving debt permanently unresolved.

## 9. Architecture comparison

### 9.1 Summary

| Outcome | Full invariant coverage | Robinhood Stock Token technical eligibility | Recommendation |
| --- | --- | --- | --- |
| 1. Do not list Stock Tokens | Vacuous for Stock Tokens; existing Base defects remain | No | Safe default if no direction is approved |
| 2. Minimum shared containment | I-01, I-02, I-05–I-07, I-09, I-12; partial I-03/I-04 | No for issuer-controlled collateral under the complete invariant set; containment freezes unresolved loss cases | Ship as urgent Base hardening if owner approves the full atomic release and migration |
| 3. Corrected shared share path | Can cover I-01–I-12 after policy, implementation, migration, audit, and exact-token validation | Yes, but only after every gate is complete | Permanent direction |
| 4. Another generic design | Not needed at this checkpoint | No current basis | Do not open unless later interface proof shows the shared corrected design cannot meet an invariant |

### 9.2 Outcome 1 — do not list

- **Invariant coverage:** prevents Stock Token custody exposure by absence.
- **Unresolved choices:** Base hardening remains; Robinhood product scope
  excludes Stock Token collateral.
- **Affected surfaces:** configuration and deployment inventory only; no Stock
  Token deposits, borrowing, auctions, or vault migration.
- **Base behavior:** unchanged and still exposed to shared nominal-vault defects.
- **Custody risk:** no new Robinhood Stock Token custody; current Base risk
  remains.
- **Scope/audit/testing:** lowest Robinhood contract scope; Base follow-up still
  requires review.
- **Rollback:** operationally simple before listing.
- **Operational burden:** enforce unsupported status and prevent accidental
  configuration.
- **Eligibility:** no.

### 9.3 Outcome 2 — minimum shared containment

One atomic deployable safety group:

- exact call-local received amount;
- fail-closed Simple borrowing value during aggregate deficit;
- explicit derived deficit propagation through debt health;
- no zero-threshold false health or non-liquidatable disappearance;
- internal-transfer deficit guard;
- derived per-asset collateral eligibility from existing `canDeposit`, LTV,
  and automatic backing state;
- repayment preserved; and
- no zero-backed auction manufactured.

Changing only the amount view is unsafe because CreditEngine skips zero amounts
before weighted terms are constructed.

- **Invariant coverage:** stops new phantom-backed debt and unsafe nominal
  internal settlement; preserves delivery atomicity and repayment.
- **Unresolved choices:** partial-loss allocation, total-loss bad-debt
  transition, post-zero restoration, and permanent issuer settlement remain
  unresolved/frozen.
- **Affected components:** at least `CM-024`, `CM-026`, `CM-030`, `CM-034`,
  `CM-045`, `CM-009`, `CM-011`–`CM-013`, `CM-021`, `CM-033`, `CM-044`, and
  common config/interfaces; exact changes are Phase I.
- **Base behavior/migration:** canonical shared source changes; funded vault ID
  3 means an owner-approved Base migration/version policy is mandatory.
- **Custody risk:** contains overcredit/new borrowing; does not allocate an
  existing loss or complete debt resolution.
- **Scope/audit:** cross-contract atomic safety review across deposit, credit,
  settlement, and governance.
- **Rollback:** deployment rollback is not a substitute for custody rollback;
  any moved positions need reconciled reverse migration.
- **Testing:** all affected Simple/Base regressions plus mixed collateral and
  existing debt.
- **Operations:** monitor deficits, disable quickly, keep repay open, do not
  auto-re-enable.
- **Eligibility:** not sufficient for full issuer-controlled collateral
  listing under I-08 and I-10.

### 9.4 Outcome 3 — corrected shared share-based permanent path

Required properties:

- pro-rata live claims after partial loss;
- exact call-local receipt;
- live claims, never raw shares, used for credit and settlement;
- explicit total-loss debt resolution;
- post-zero deposit freeze;
- no automatic donation/restoration allocation and no recapitalization without
  a separate approval;
- external-only issuer-controlled settlement;
- bounded rounding/dust;
- explicit reward and monitoring units; and
- migration from any custody-bearing prior vault version.

- **Invariant coverage:** capable of full I-01–I-13 coverage.
- **Specified choices:** partial loss is pro rata against allocated backing;
  post-zero deposits freeze; unsolicited positive deltas remain unallocated;
  user reward weight and global value use live economic claims; issuer-
  controlled settlement is external-only; total-loss liability progress is
  atomic and exactly once.
- **Unresolved choices:** the storage/interface boundary that distinguishes
  allocated backing from raw custody, any future recapitalization/recovery
  transaction, Phase F implementation mechanisms/caller, migration, and
  production vault selection.
- **Affected components:** `CM-025` plus the containment consumers above,
  common interfaces/config, VaultBook, defaults/migrations/manifests, and
  post-deployment verification.
- **Base behavior/migration:** one canonical source. Owner must choose parity,
  bounded temporary drift with convergence, or a justified live-version
  exception; no policy is selected here.
- **Custody risk:** live pro-rata claims remove nominal phantom collateral, but
  transfer controls and total loss still require explicit resolution.
- **Scope/audit:** larger math, storage/interface, settlement, bad-debt, reward,
  and migration boundary.
- **Rollback:** live share migration is stateful and not trivially reversible.
- **Testing:** highest burden, including property math, exact AAPL fork,
  dual-clock profiles, Base regression, and migration.
- **Operations:** explicit raw-share/live-claim/deficit/version evidence and
  stronger re-enable process.
- **Eligibility:** technically eligible only after owner selection and all
  implementation, audit, exact-token, migration, and production-behavior gates.

This is an architecture recommendation, not a selection of the current
`RebaseErc20` deployment or any other production vault.

### 9.5 Outcome 4 — another generic shared design

Not admitted at this checkpoint. The required invariants appear achievable
through generic changes to the shared vault/config/credit/settlement
architecture plus a corrected share path. Phase E established that existing
state and getters are sufficient for deficit-aware collateral use; later
settlement and exactly-once bad-debt work may still require interface changes,
but no issuer-branded or Robinhood-only vault is justified.

Reopen this outcome only if Phase D–I analysis, security review, or a proof
shows the shared corrected design cannot express an invariant.

## 10. Rejected shortcuts

| Shortcut | Disposition |
| --- | --- |
| Change only the Simple amount view to zero | Rejected: zero is skipped by CreditEngine and can erase weighted debt terms without resolving existing debt. |
| `min(userNominal, liveTotal)` | Rejected: multiple users can each claim the same aggregate custody. |
| Silent nominal pro rata or balance rewrite | Rejected absent owner-approved loss allocation/property-rights policy. |
| LTV set to zero as custody switch | Rejected: not an immediate backing control and does not make settlement honest. |
| Oracle price removal/zero as kill switch | Rejected: price and custody are independent; zero price can block health/liquidation. |
| Monitoring and operator response only | Rejected: onchain borrow and settlement must fail closed. |
| Disable deposits only | Rejected: existing borrowing, debt health, internal settlement, auctions, and loss resolution remain unsafe. |
| Treat internal balance movement as delivery | Rejected for issuer-controlled assets; token pause/blocklist/custody is not exercised. |
| Manufacture a zero-backed auction for progress | Rejected: violates payment/delivery conservation. |
| Treat later donation/restoration as automatic recovery | Rejected: ownership/allocation is ambiguous. |
| Permit fresh deposit at zero custody with old shares | Rejected absent explicit recapitalization; it can transfer value between old and new users. |
| Use current SharesVault unchanged | Rejected: short-receipt measurement, total-loss liveness, post-zero allocation, and migration are unresolved. |
| Use current SimpleErc20 unchanged | Rejected for Stock Token collateral: nominal phantom backing and first-withdrawer/internal-settlement failures persist. |
| Replace vault ID 3 directly in VaultBook | Rejected: live-funds checks and persisted user/asset state prevent casual replacement. |
| Disable repayment during freeze | Rejected: violates repayment liveness and worsens loss. |
| Robinhood-only/issuer-branded vault or `chain.id` branch | Rejected: violates the canonical shared-source constraint. |
| New insurer, Stability Pool custody route, or recovery token | Out of scope and rejected for Track 8. |

## 11. Recommendation

Recommend that the owner select checkpoint option **4: containment followed by
the corrected share path**, with these boundaries:

1. Treat the full Release 1 containment group as urgent Base hardening, not as a
   sufficient Robinhood Stock Token listing release.
2. Keep Robinhood Stock Token deposits, borrowing, and auctions disabled until
   the permanent path satisfies all invariants and gates.
3. Use a corrected generic share-based architecture as the permanent direction,
   without selecting a production vault at this checkpoint.
4. Require external-only settlement for issuer-controlled collateral.
5. Freeze post-zero deposits by default.
6. Do not begin implementation until the later owner gates and implementation
   authorization are satisfied.

This recommendation is not production-vault selection, implementation
authorization, Base migration approval, or acceptance of a loss-allocation
policy.

### 11.1 Track 5 recommendation disposition

| Track 5 recommendation | Track 8 disposition at checkpoint |
| --- | --- |
| Continuous live/accounted solvency monitoring | **Accepted as an operational and future getter/event requirement** and specified as a read-only Phase H repository evidence contract, but not as an onchain fix. Hosted monitoring is outside this repository track. |
| Rehearsed global-borrow, per-asset-deposit, and per-asset-auction response | **Accepted as Release 0 preparation and mapped in Phase H** with exact authority/event/getter/clock requirements. Any production flag change requires fresh owner approval. |
| Keep Stock Tokens disabled until behavior is approved | **Accepted**. This is the current safe state. |
| Fail-closed Simple borrowing amount under deficit | **Specified in Phase E** using existing vault/token getters and explicit debt-term propagation; no new external getter or stored flag is introduced. |
| Deficit-aware existing-debt health | **Accepted into the atomic containment group**; no amount-view-only patch is acceptable. |
| Reject Simple internal transfer while underbacked | **Accepted into the atomic containment group**; exact guard/result behavior is deferred. |
| Add generic per-asset collateral-use flag | **Functional requirement accepted; new stored flag rejected by the owner.** Phase E derives effective eligibility from existing `canDeposit`, `DebtTerms.ltv`, and automatic backing state without changing `AssetConfig`, storage, or the deployed interface. |
| Exact per-call deposit delta in the same release | **Specified in Phase D at the shared Teller boundary**; implementation remains unauthorized. |
| External-only issuer-controlled settlement | **Owner-approved for Phase F specification.** Section 16 proves that the policy cannot be enforced per asset by any current field; the exact implementation mechanism is returned without selecting new storage/interface. |
| Keep generic backing checks even with external-only settlement | **Accepted as invariants I-02, I-06, and I-07**. |
| Define deficit and total-loss debt progress | **Owner-approved for Phase F specification.** Section 16 defines the atomic exactly-once transition and identifies the minimum shared interfaces required; those interfaces and implementation remain unapproved. |
| Corrected share-based permanent behavior | **Accepted as the recommended permanent architecture**, not selected as a production vault. |
| Freeze post-zero deposits | **Owner-approved for Phase G specification**; implementation and its checkpoint gate/caller remain unapproved. |
| Do not auto-allocate later donations/restoration | **Accepted as a prohibition**; positive allocation remains an owner/counsel/risk decision. |
| Base canonical shared-version hardening and migration | **Base-first or atomic convergence is owner-directed as a Phase J validation/release requirement.** No migration, cutover, transaction, or live-version exception is approved. |
| Fifteen acceptance-test outcomes | **Carried into the validation-plan scaffold** with invariant IDs and named future tests. |
| Release 0/1/2 sequencing | **Accepted as release framing**; no implementation or deployment gate is opened. |
| `min(user nominal, live)`, silent rewrite, oracle kill switch, monitoring-only, and LTV-only shortcuts | **Rejected**, as detailed in Section 10. |

Every Track 5 fix recommendation is therefore accepted, rejected, deferred, or
returned for an explicit owner decision. None is treated as implementation
authorization.

## 12. Mandatory owner checkpoint

### 12.1 Direction decision

The checkpoint presented these options:

1. no Stock Token listing;
2. containment release only;
3. corrected share-based permanent path;
4. containment followed by corrected share path; or
5. another explicitly approved generic design.

The owner-confirmed 2026-07-23 message approves **option 4: containment
followed by the corrected share path**, and authorizes **Phase D specification
work only**. This is checkpoint option 4—the staged combination of Section 9
outcomes 2 and 3—not Section 9.5's separately numbered “another generic shared
design.”

Recorded approval provenance is the following message presented in this Track
8 work session immediately before Phase D began:

> I approve option 4 as the Track 8 architecture direction and authorize Phase
> D specification work only. This does not select a production vault, approve
> implementation, authorize a Base migration, or approve any loss-allocation
> policy. Later phases remain subject to their documented owner checkpoints.

That recorded authorization explicitly did not:

- select a production vault;
- approve implementation;
- authorize a Base migration; or
- approve a loss-allocation policy.

The following controlling Phase E message was then presented on 2026-07-23
after the deeper review of existing protocol parameters:

> I reject adding a new stored per-asset collateral-use parameter by default.
> Authorize Phase E specification work to use existing deposit controls and
> DebtTerms.ltv, fix their consumption semantics, and return to me before
> proposing any new storage or interface. This does not authorize
> implementation or Phase F.

The implementation agent did not rely on self-attestation. On 2026-07-23, the
owner directly closed the governance-confirmation item with:

> I confirm I gave the option-4 and Phase E instructions as quoted in §12.1.

This confirmation authenticates both quoted instructions for the Track 8
record. It does not expand either instruction's scope.

Phase E therefore may specify only a composition of existing controls and
automatic backing state. It may not propose new storage or a new external
interface without first returning to the owner.

On 2026-07-24, the immediately preceding Phase F decision restatement was:

1. issuer-controlled collateral is always external-settlement-only, with no
   buyer-selected internal ledger settlement; and
2. Phase F specifies an atomic, exactly-once total-loss transition from user
   debt to Ledger bad debt; if source proves minimal new storage/interface is
   necessary, return before selection.

That restatement also excluded implementation, migration, loss allocation,
production-vault selection, and Phase G. The owner then replied:

> yes i agree iwth your phase F decisions. but once documented, let's pause on
> work for the night

This owner-confirmed message authorizes Phase F specification work for those
two directions and requires a stop after documentation. It does not select a
production vault, approve implementation, approve a Base migration, approve a
partial-loss/recovery allocation, approve new storage or interfaces, or
authorize Phase G. Because the source trace below proves that current
accounting and configuration cannot fully express the directions, Section 16
identifies the exact minimal shared-interface choices and returns them for a
later owner decision rather than silently selecting them.

After the requested overnight pause, the three Phase G recommendations were
presented again in numbered order:

1. freeze new deposits after zero;
2. do not automatically allocate later donations/restoration, and require a
   separately approved recapitalization or recovery with counsel/risk input;
3. use explicit live-claim-based economic reward units coordinated with Track
   6 S3, never raw shares alone.

The owner replied on 2026-07-24:

> 1. freeze is okay
> 2. okay
> 3. okay
>
> You can start Phase G now

The numbered assent owner-confirms those three policy directions and
authorizes Phase G **specification work only**. It does not approve a
production vault, implementation, a storage field or interface, a
recapitalization/recovery transaction, a Base migration, or Phase H. Section
17 therefore defines the required behavior and explicitly returns the
newly-proven storage/interface compatibility boundary for Phase I review.

After Phase G and its review remediations were committed and backed up, the
owner authorized the next phase with the following 2026-07-24 instruction:

> I authorize Phase H specification work only. Prefer existing controls and
> preserve repayment liveness. Return to me with evidence and alternatives
> before proposing or selecting any new storage, interface, dedicated pause,
> or caller policy. Do not implement contract changes, begin Phase I, select a
> production vault, or authorize migration.

Phase H may therefore inventory current controls, specify evidence and
runbook requirements, reject controls that break repayment, and compare
alternatives. It may not select a total-loss or checkpoint caller, introduce
or select a dedicated pause, propose a new storage/interface mechanism, begin
the Phase I compatibility table, or authorize implementation or migration.

After Phase H was signed off, Phase I continuation was recommended with five
explicit directions:

1. use existing global `canLiquidate` as the total-loss-resolution gate
   baseline and accept its global liquidation coupling for design analysis;
2. analyze a narrow share-loss checkpoint gate without treating new storage
   or an interface as approved;
3. permit a total-loss transition caller only if the final entry point is
   deterministic and gives the caller no discretion over eligibility, amount,
   recipient, or timing-sensitive value;
4. use a restricted existing onchain operational actor for the share-loss
   checkpoint; and
5. preserve withdrawals when actual delivery is safe, disabling the affected
   asset only when delivery is unsafe.

The owner replied:

> okay let's do it

That assent authorizes **Phase I specification work only** under those five
directions. It does not approve the two-selector bad-debt interface, any
allocated/quarantine storage representation, a checkpoint selector, a
production vault, an all-external behavior change for every asset, a new
per-asset settlement field, a Base/Robinhood migration, implementation, or
Phase J. Phase I may prove that an interface or storage mechanism is necessary
and return exact alternatives; it may not silently select one.

After Phase I returned those exact alternatives, the owner authorized Phase J
on 2026-07-24:

> I authorize Phase J specification work only. Use all-external fungible
> settlement as the preferred path subject to complete integration and
> historical-usage evidence; use an isolated generic corrected-share variant
> and the A^s/U^s model as validation targets; and model the two-selector
> bad-debt transition without authorizing a Ledger migration. Preserve S3
> independently if Track 8 would delay it, require Base-first or atomic
> convergence, and treat any empty gated deployment as inactive staging
> rather than launch. Do not select a production vault or ID, authorize
> implementation or migration, or begin Phase K.

This instruction selects validation targets and a release-validation posture,
not production mechanisms. In particular:

- all-external remains conditional on a complete current-integration inventory
  and historical calldata/product-consumer evidence;
- the generic corrected-share variant and `A^s/U^s` are models to test, not
  approved source paths, storage declarations, selectors, ABIs, or a vault;
- the two-selector transition is an atomicity test target, not approval of its
  interfaces or the inseparable full Ledger migration;
- Track 8 must not delay S3 merely to combine Lootbox cutovers; the loss
  mechanism and any second cutover remain unapproved;
- Base-first or atomic convergence is a required future enablement/release
  condition, not authorization for a Base migration; and
- an empty gated deployment proves only artifact/configuration staging. It is
  not a launch, listing, production-vault selection, or permission to enable
  deposits, borrowing, auctions, or rewards.

After Phase J and its independent review closed without findings, the owner
authorized Phase K on 2026-07-24:

> I authorize Phase K specification work only. Define the reviewable
> implementation units, dependencies, audit boundaries, stop conditions, and
> atomic Release 0/1/2 groups using the Phase J validation targets and
> evidence gates. Preserve all-external settlement as conditional on complete
> integration and historical-usage evidence; keep the isolated generic
> corrected-share variant, A^s/U^s model, and two-selector bad-debt transition
> as unapproved implementation candidates; keep the full Ledger migration as
> a separate high-risk gate; preserve S3 independently if Track 8 would delay
> it; require Base-first or atomic convergence before Robinhood enablement;
> and treat empty gated staging as inactive, not launch.
> This authorization does not approve production code, tests, interfaces,
> storage, ABIs, defaults, migrations, manifests, a Ledger migration, a
> production vault or VaultBook ID, Base or Robinhood deployment, live
> configuration, or any transaction. Do not modify rh-summary.md. Return the
> final implementation/release split, unresolved decisions, owner
> checkpoints, and checklist handoff for my review before any implementation
> begins.

This authorization permits Section 21 to name exact future review surfaces
and to group them into activation-safe releases. It does not select any
candidate mechanism or authorize creation of the named future files. The
separate approval gates in Section 21.10 must be satisfied before evidence
acquisition, test implementation, production implementation, migration,
deployment, configuration, or enablement.

After Phase K, the owner clarified the controlling launch objective on
2026-07-24:

> Track 8 is not paused or deferred. Stock Tokens are a mandatory
> initial-launch requirement for Ripe on Robinhood, and identifying the
> smallest safe set of production changes is now a critical-path workstream.
> Continue working actively. The purpose of the current documentation-only
> boundary is to prevent unreviewed production edits in this planning branch,
> not to postpone Stock Token support.

The same instruction requires a concise minimum-change launch proposal,
explicit necessity decisions for the larger architecture, an exact production
surface, accepted risks, tests, and implementation slices. It also replaces
the old default stop:

> The safe stop condition is not “defer Stock Tokens by default.” The safe
> stop condition is: if no reasonably small shared patch can prevent phantom
> borrowing and false settlement, return that evidence to the owner before
> opening the larger architecture.

Section 23 is the response to that direction. The comprehensive Phase A–K
record remains evidence, but its corrected-share, automatic bad-debt, Ledger,
reward-loss, and recapitalization branches are no longer presumptive
initial-launch scope. The current production contracts remain unsafe for Stock
enablement until the proposed atomic group is implemented and accepted; that
technical disable is a launch gate, not a product deferral.

### 12.2 Checkpoint decisions and their actual gates

The product/architecture direction required for Phase D, the existing-controls
direction required for Phase E, the two policy directions required for Phase
F, and the three policy directions required for Phase G are owner-confirmed as
satisfied for specification work. Phase H specification work and Phase I
compatibility analysis are also owner-authorized. The five directions above
resolve the Phase H analysis boundary for Phase I without approving a storage,
interface, production vault, or migration. Phase J and Phase K are
owner-authorized under their validation-only and release-planning-only
directions above. Base-first or atomic convergence is a future
validation/release requirement, but no Base action is authorized. The
remaining implementation, migration, vault-selection, evidence-acquisition,
and live-release decisions are returned by Section 21. The Phase F–I source
traces create narrower implementation-mechanism/compatibility decisions; none
is implied by a validation-target or implementation-unit definition.

| Decision | Options | Evidence and recommendation | Owner | Affected components | Prerequisite / milestone | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Product outcome | Five checkpoint options above | Staged containment then corrected share path | Product + protocol owner | Whole track | Before Phase D | **Owner-confirmed: option 4, specification work only** |
| Per-asset collateral use | Add a stored flag / compose existing controls | Reuse `canDeposit`, `DebtTerms.ltv`, and automatic backing state; do not add storage or a deployed selector | Protocol owner + security | `CM-009`, `CM-011`–`013`, `CM-030`, existing config/getters | Before Phase E | **Owner-confirmed: existing-controls Phase E specification only; implementation not approved; Phase F was authorized separately on 2026-07-24** |
| Issuer-controlled settlement | Always external / permit bounded internal | Current internal mode can charge for undeliverable nominal claims; external-only selected | Protocol owner + risk/security | `CM-026`, `CM-030`, `CM-043`, `CM-044`, Vault interface | Before Phase F | **Owner-confirmed: external-only Phase F specification; enforcement mechanism and implementation not approved** |
| Total-loss transition | Approved user-debt→Ledger-bad-debt design / another existing-accounting design / no listing | Current system has no atomic exactly-once path; atomic transition selected for specification | Protocol owner + accounting/security | `CM-026`, `CM-030`, Ledger, interfaces | Before Phase F | **Owner-confirmed: atomic exactly-once Phase F specification; identified interfaces and implementation not approved** |
| Post-zero state | Freeze / explicit recapitalization | Freeze selected; old shares persist with zero claim and no fresh deposits | Protocol owner + risk | `CM-025`, deposit callers, controls | Before Phase G | **Owner-confirmed: freeze for Phase G specification; implementation not approved** |
| Later donation/restoration | Old holders / donor return / protocol / explicit recapitalization allocation / no automatic allocation | No automatic allocation selected; any later allocation/recovery requires a separate owner plus counsel/risk decision | Protocol owner + counsel/risk | Share math, recovery, migration | Before Phase G | **Owner-confirmed: no automatic allocation; no recapitalization/recovery transaction approved** |
| Reward attribution | Raw shares / live claims / hybrid explicit units | Live-claim-based economic units selected; raw shares remain accounting evidence only and S3 coordination is mandatory | Protocol owner + economics | `CM-033`, `CM-025` | Before Phase G/H | **Owner-confirmed: live-claim units for Phase G specification; Lootbox/interface implementation not approved** |
| Base live-version posture | Base-first / atomic convergence / no release | Funded ID 3 and live controlled assets make this material; Phase J requires Base-first-or-atomic convergence before RH enablement. Inactive staging is not launch and does not satisfy this gate. | Protocol owner + security/operations | Base vault consumers, VaultBook, manifests | Before implementation/release | **Owner-directed Phase J validation/release posture; no migration, cutover, or live action approved** |
| Release 1 Base priority | Base-first containment / atomic Base-RH convergence / no release | Section 21.6 requires the full economically atomic containment group and Base-first or atomic convergence before RH enablement | Protocol owner + security/operations | Containment atomic group and every affected stateful consumer | K-CP2–K-CP7 | **Phase K topology specified; no mechanism, implementation, migration, or live action approved** |

New Phase F implementation-mechanism/caller decisions, returned because no
current field or selector safely expresses the approved policies and the
transition caller's timing authority requires separate security review:

| Decision | Options | Recommendation | Required before | Status |
| --- | --- | --- | --- | --- |
| External-settlement enforcement | Disable buyer-selected internal settlement for all fungible auctions / add a generic per-asset settlement mode if bounded internal settlement must survive for other assets | Phase J uses all-external as the preferred validation path only after complete integration and historical-use evidence; any discovered dependency returns the production choice | Any Phase F implementation design | **Phase J preferred validation branch; no behavior, field, getter, setter, default, migration, or ABI approved** |
| Atomic bad-debt mechanism | Approve the two-selector CreditEngine→Ledger transition in Section 16.10 / approve another reviewed atomic shared-contract design / do not list | Phase J models the no-new-storage, compare-and-set two-selector design and the full Ledger migration it would require | Any Phase F implementation design | **Phase J validation target; interfaces, event, implementation, and Ledger migration not approved** |
| Total-loss transition caller | Permissionless deterministic / restricted approved keeper or Department / governed per-transition action | Permissionless is acceptable only for the zero-discretion `resolveUserTotalLoss(user)` shape in Section 19; any caller-supplied amount, asset list, recipient, or timing-sensitive value voids that direction and returns to owner/security | Any Phase F implementation design | **Owner-directed condition for Phase I; interface and implementation not approved** |

New Phase G compatibility decisions, returned because current source derives
claims directly from all custody and existing reward/recovery surfaces cannot
express the approved policies:

| Decision | Options | Recommendation | Required before | Status |
| --- | --- | --- | --- | --- |
| Allocated-backing mechanism | Append explicit allocated/quarantine checkpoint state to a generic share path / deploy a generic vault-level policy variant / another audited mechanism proving `A^s/U^s/A/U` / do not list | Phase J uses an isolated generic corrected-share variant and `A^s/U^s` as validation targets while preserving the Section 17 semantics and existing Rebase/RipeGov positive-delta behavior | Any Phase G implementation design | **Phase J validation target; no storage slot, selector, wrapper, ABI, migration import, or production vault approved** |
| Quarantine loss ordering | Preserve checkpointed `U` and reduce `A` first / use `U` as shareholder loss insurance / pro-rata reduction | Preserve `U` and reduce `A` first; otherwise the donation is automatically allocated for shareholder benefit contrary to the selected policy. Counsel/risk must confirm this property treatment before implementation | Phase I/accounting/counsel-risk review | **Reference behavior specified; implementation approval pending counsel/risk confirmation** |
| Positive-delta compatibility | Quarantine unsolicited positive deltas in the corrected path / explicitly allocate positive rebases in a separately reviewed generic mode | Do not silently apply quarantine semantics to existing yield/rebase users; separate the generic behaviors explicitly and test both | Phase I source/storage/interface impact review | **Returned; no mode/configuration field approved** |
| Reward integration surface | Reuse live-amount getters with explicit semantics / add an explicit economic-weight getter / global loss interval/index compatible with integrated S3 / do not list | Preserve raw shares for accounting, use live claims for economic weight, exclude `U` from global value, preserve S3's send-floor surfaces, and separately solve the untouched-user loss boundary because integrated S3 does not | Phase I owner/economics/security review | **Returned; no Vault/Lootbox/Ledger ABI or storage change approved** |

New Phase H control decisions are returned because current source has useful
fast controls but no dedicated total-loss/checkpoint gate and because broad
contract pauses violate the owner-required repayment-liveness boundary:

| Decision | Alternatives returned | Evidence and recommendation | Owner | Affected components | Prerequisite / needed-before milestone | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Total-loss resolution gate | Reuse existing global `canLiquidate` consumption / dedicated narrow gate / no listing | `canLiquidate` is immediate, fast-disable/governance-enable, observable, and repayment-independent; its global ordinary-liquidation coupling is explicit. Broad Teller/CreditEngine/Ledger pauses remain rejected. | Protocol owner + security | MissionControl, SwitchboardAlpha/Charlie, AuctionHouse, CreditEngine, Ledger | Exact resolver interface/security review before implementation | **Owner-directed for Phase I: use existing `canLiquidate` baseline; no dedicated gate or implementation approved** |
| Share-loss checkpoint gate | Existing asset containment as preconditions / dedicated narrow gate / no listing | Require `canDeposit=false` and `canBuyInAuction=false` before checkpoint; these contain exposure but do not themselves authorize state mutation. Do not add a dedicated stored gate by default. | Protocol owner + security/risk | MissionControl, SwitchboardCharlie, selected share-vault boundary, Teller, Lootbox | Corrected-share storage/interface review before implementation | **Owner-directed for Phase I: analyze narrow no-new-gate path; selector/storage remain unapproved** |
| Total-loss transition caller | Permissionless deterministic / restricted existing actor / governance per transition / no listing | Permissionless only for a zero-discretion `resolveUserTotalLoss(user)` that derives every value and eligibility input onchain; any caller-supplied subset/amount/recipient returns the decision. | Protocol owner + security/operations | CreditEngine, Ledger, AuctionHouse, resolution gate and evidence event | Caller-discretion/race proof before implementation | **Owner-directed condition for Phase I; resolver selector and implementation not approved** |
| Share-loss checkpoint caller | Restricted existing Switchboard actor / another approved actor / governance per checkpoint / no listing | Use existing `addys._isSwitchboardAddr` authority; no role mapping. The call must derive bucket changes and require containment, so the actor cannot choose allocation. | Protocol owner + security/risk/operations | Selected share-vault boundary, containment flags, evidence surface | Checkpoint storage/interface and counsel/risk review before implementation | **Owner-directed for Phase I: existing Switchboard actor; checkpoint selector/storage not approved** |
| Incident withdrawal posture | Preserve safe withdrawals asset-by-asset / disable affected asset when unsafe / broader freeze | Preserve repayment always and withdrawals when measured delivery is safe. Use existing per-asset disable only when delivery is unsafe; no standing broader freeze. | Protocol owner + security/operations | MissionControl, SwitchboardAlpha/Charlie, Teller/TellerUtils, selected vault and all co-resident assets | Exact delivery failure and blast-radius evidence before incident action | **Owner-directed operating posture; no production flag action approved** |

### 12.3 Decisions explicitly deferred but registered

These must not be treated as approved by the checkpoint recommendation:

| Decision area | Options/recommendation | Needed before | Status |
| --- | --- | --- | --- |
| Deposit measurement boundary | Teller measures the call-local custody delta and passes only verified receipt to the vault; see Section 14 | Phase D completion | **Specified; implementation not approved** |
| Requested/received/excess semantics | Validated transfer attempt `Q`; received/credited `R`; zero, negative, or excess delta reverts; see Section 14 | Phase D completion | **Specified; implementation not approved** |
| Nominal partial loss | Freeze unresolved or owner-approved allocation; never silent pro rata | Phase E/F | Deferred |
| Rounding | Retain `10^8` virtual shares and one virtual asset; deposit down, withdrawal share burn up, claim down, last-share sweep; see Section 17 | Phase G | **Specified; implementation not approved** |
| Emergency disable/re-enable | Sections 18–19 use existing `canLiquidate`, asset containment, Switchboard authority, and safe-withdraw posture; no dedicated stored gate/pause | Interface/security review before implementation | **Phase I direction specified; no selector, storage, implementation, or live action approved** |
| Vault selection | No production vault selected; Section 19 recommends but does not select a new generic corrected-share boundary | K-CP8 before Release 2 implementation | Deferred |
| Migration atomicity/rollback | Section 19.6 specifies live users/funds/debt/auctions/rewards, partial failure, retirement, and rollback reality | Before implementation/release | **Specified; exact IDs/manifests/tooling pending Track 7 and no migration approved** |
| Exact-token evidence | Pinned AAPL fork plus behavior-switch/loss tests | Future implementation validation | **Phase J plan complete; no test, live probe, signing, or broadcast authorized** |
| S1/S2 identical artifacts | Base/RH profiles and checked inventory | Future implementation validation | **Phase J reconciled the integrated command interfaces through `rh`; harness not imported or run against a Track 8 implementation** |
| Audit/release | Section 21 defines reviewable units, required reviewers, stop conditions, Release 0 evidence readiness, the atomic Release 1 containment group, and the atomic Release 2 corrected-path group | Before any implementation/release authorization | **Phase K split specified; no test, production implementation, audit engagement, migration, deployment, or live action approved** |

## 13. Affected component map at checkpoint

This is a Phase C impact boundary, not the finalized Phase I change table.

| Stable ID / surface | Why affected |
| --- | --- |
| `CM-021` VaultBook | Funded-vault replacement, disablement, migration, and retirement checks |
| `CM-024` Basic/Simple vault path | Nominal accounting, deficit, internal transfer, receipt |
| `CM-025` Rebase/Shares path | Raw shares, allocated backing/quarantine, live claim, post-zero, restoration, rounding |
| `CM-026` AuctionHouse | Settlement policy, delivery/payment ordering, active auctions |
| `CM-027` AuctionHouseNFT | Current temporary stub has no common Vault consumer; reused unchanged/inapplicable unless later implemented |
| `CM-030` CreditEngine | Borrow amount, deficit propagation, health, resolution, and intentional raising-to-non-raising repayment price refresh |
| `CM-043` CreditRedeem | Transfer/withdraw settlement consumer and unsupported Stock Token posture |
| `CM-033` Lootbox | Live-claim reward weight, allocated global value, interval boundary, and raw-share evidence |
| `CM-034` Teller | Transfer/credit/event/limit/housekeeping ordering |
| `CM-044` Deleverage | Delivered amount and zero-custody progress |
| `CM-045` TellerUtils | Deposit limit inputs and pre-transfer vault views |
| `CM-007`–`CM-013`, `CM-049` | Defaults, MissionControl, Switchboards, per-asset controls, Robinhood configuration, lite/governance authority, fast-disable/stronger-enable asymmetry, and Phase H evidence getters/events |
| Ledger | User debt, aggregate debt/yield, auction removal, affected-user/auction enumeration, and exactly-once protocol bad debt; Phase F identifies but does not approve one new transition selector |
| Existing `ConfigStructs`, MissionControl, and `Vault` interfaces | Phase E reuses current controls/getters; Phase F proves no current settlement-mode field exists; Phase G proves current Vault getters cannot expose `A^s/U^s/A/U`; Phase H maps existing controls and explicitly selects no replacement interface |
| StabilityPool, StabVault | Shared Teller deposit semantics remain; Stock Token swap/custody route stays disabled |
| RipeGov | Shared SharesVault/Teller semantics, separate lock-adjusted governance reward units, and the protocol-wide withdrawal-freeze consequence of nonzero bad debt |
| BondRoom | Existing global bad-debt clearing consumer; clearing cannot restore resolved user debt |
| HumanResources, CreditEngine/CreditRedeem reward paths | Trusted RIPE/sGREEN deposits must consume and verify Teller's returned receipt |
| Base/RH migration and manifests | Same canonical source, live-version policy, custody migration, verification |

Track 7 owns exact Robinhood migration IDs/namespaces/tooling. Track 8 will not
reserve or invent them.

## 14. Phase D — exact deposit accounting

### 14.1 Authorization and design boundary

The recorded option-4 instruction authorizes Phase D specification work only,
covering the staged combination of containment and the corrected share path.
This section therefore selects one shared deposit-accounting design, but does
not authorize its implementation or select a production vault.

The selected boundary is **Teller-side, call-local custody-delta
measurement**. Teller owns the transfer source and mode, resolves the target
vault, applies deposit limits, and is already the common entry point for every
production deposit path found in the pinned source. Every participating vault
must consume Teller's measured receipt; no vault may infer a call's receipt
from its aggregate balance.

The alternative, vault-side measurement, was rejected for the current
architecture:

- measuring only after Teller has transferred cannot recover the vault's
  call-local pre-transfer balance;
- moving `transferFrom` into every vault would change approvals, trusted
  deposits, Teller-held deposits, and the common call boundary; and
- a prepare/finalize pre-balance hook would introduce persistent or transient
  state that callbacks, stale prepares, and partial integrations could misuse.

Passing a Teller-captured pre-balance to each vault would still make Teller the
measurement boundary while unnecessarily widening interfaces. The selected
design therefore keeps measurement and enforcement in Teller and passes only
the verified received amount through the existing vault deposit parameter.
It is generic: no asset-name, issuer, vault-ID, or chain-ID branch is permitted.

### 14.2 Amount vocabulary

For one `_deposit` execution:

| Symbol | Name | Definition |
| --- | --- | --- |
| `A_req` | caller request | Raw `_amount` supplied to the Teller entry point. It may be `max_value(uint256)` or exceed the depositor balance/limit. |
| `Q` | transfer attempt | Final nonzero amount returned by `TellerUtils.validateOnDeposit` after source-balance and applicable user/global limit caps. |
| `C0` | custody before | Target vault's token `balanceOf` read immediately before the transfer. |
| `C1` | custody after | Target vault's token `balanceOf` read immediately after the transfer returns successfully. |
| `R` | received | Checked delta `C1 - C0`, valid only when `C1 >= C0` and `0 < R <= Q`. |
| `V` | credited/returned | Amount the vault reports after adding user accounting. It must equal `R`. |
| `C2` | custody after credit | Target vault's token balance after the vault accounting call. It must equal `C1`. |
| `C3` | custody before success events | Target vault's token balance after all post-credit external work and immediately before success events. It must equal `C1`. |

`A_req` is user/operator intent, `Q` is the requested transfer after protocol
validation, and `R` is the only amount delivered to and credited by the vault.
The terms `requested`, `received`, and `credited` must not be used
interchangeably in code, tests, events, or operational evidence.

### 14.3 Required transaction ordering

Every path into Teller `_deposit` must perform this sequence atomically:

1. Its top-level deposit-bearing Teller route enters a **deposit-specific
   mutex** before vault resolution, validation, token calls, or other external
   work. `_deposit` may execute only while that route owns the mutex.
2. Resolve the vault and vault ID and obtain the user's starting Ledger data.
3. Run the existing `validateOnDeposit` policy to derive `Q`.
4. Read `C0 = token.balanceOf(vaultAddr)` immediately before transfer.
5. Execute the existing transfer mode for `Q`:
   `transferFrom(depositor, vaultAddr, Q)` for ordinary/trusted-source funds or
   `transfer(vaultAddr, Q)` when Teller already holds the funds.
6. Require the token call to return true when it returns a value; a false
   result or revert fails the whole transaction.
7. Read `C1 = token.balanceOf(vaultAddr)` immediately after transfer.
8. Require `C1 >= C0`, compute `R = C1 - C0`, and require `0 < R <= Q`.
9. Call the resolved vault deposit function with `R`, never `A_req` or `Q`.
10. Require the vault's returned credited amount `V` to equal `R`.
11. Read `C2` after the vault call and require `C2 == C1`.
12. For a non-trusted deposit, apply the post-credit minimum-balance check in
    Section 14.6.
13. Only after those checks may Teller register vault participation, update
    Lootbox deposit points, perform requested housekeeping, add the PriceDesk
    snapshot, and emit successful-deposit events.
14. After `_deposit`'s post-credit external work and before its events, read
    `C3` and require `C3 == C1`.
15. Hold the deposit mutex through the final event and return `R`; a revert
    rolls back both the mutex write and every earlier state/external effect.

The current global `@nonreentrant` guard cannot simply be added to
`depositFromTrusted`. Existing nonreentrant Teller claim flows can legitimately
call Stability Pool/StabVault code that calls back into
`depositFromTrusted`. The unrelated outer claim does not own the deposit mutex,
so a separate deposit mutex permits that first callback to enter `_deposit`,
while rejecting any nested deposit after a deposit-bearing route has begun.
`deposit` and `depositFromTrusted` hold it through their returns;
`depositMany` holds it once across every item and final batch housekeeping;
`rebalance` holds it across deposit, withdrawal, final health check, and return;
and the Teller-held sGREEN and `depositIntoGovVault` routes hold it across their
respective `_deposit` calls and returns.

The mutex is deliberately global across Teller deposits, not keyed by asset or
vault. A token hook therefore cannot synchronously open an otherwise-legitimate
deposit for a different asset or vault. This is an accepted liveness
restriction: a keyed lock would preserve a nested path capable of interleaving
shared Ledger, Lootbox, housekeeping, price-snapshot, and event effects with
the outer deposit. The cross-asset deposit can be submitted separately after
the outer transaction. Any future requirement for synchronous composability
must reopen this design under security review rather than weakening the mutex
implicitly.

The `C2 == C1` check makes vault crediting a bookkeeping-only step for the
measured asset. It catches vault code, hooks, or callbacks that move the asset
again before credit finalization. The `C3 == C1` check extends that protection
across the Ledger, Lootbox, PriceDesk, and any housekeeping calls performed
inside `_deposit`, so its successful events cannot describe a balance changed
during that critical section. Batch-final housekeeping and rebalance
withdrawal occur after the per-deposit event but remain transaction-atomic and
inside the deposit mutex; the latter may intentionally change custody. No
callback may open a nested Teller deposit while the mutex is held.

`C3 == C1` relies on an explicit liveness assumption: Ledger participation,
Lootbox point updates, per-deposit housekeeping, and PriceDesk snapshot work do
not legitimately move the target vault's custody of the measured asset. That
assumption holds in the pinned caller trace, but implementation must repeat the
call-graph inventory against its integrated source and prove both sides:
ordinary housekeeping-enabled deposits still succeed, and an actual custody
mutation reverts before success events. If a future post-credit module must
legitimately move the measured custody, this ordering must be redesigned rather
than deleting or bypassing `C3`.

### 14.4 Token behavior and failure semantics

| Observed behavior | Required result |
| --- | --- |
| Ordinary receipt, `R == Q` | Credit and return `R`; continue with post-credit effects. |
| Short receipt or fee on transfer, `0 < R < Q` | General deposit succeeds with only `R` credited. Exact-receipt callers in Section 14.7 revert atomically. |
| Zero receipt, `R == 0` | Revert; no accounting, participation, points, housekeeping, snapshot, or event persists. |
| Negative delta, `C1 < C0` | Revert before subtraction; no loss is assigned to the depositor. |
| Excess delta, `R > Q` | Revert; do not cap or silently allocate the surplus. |
| Transfer returns false or reverts | Revert atomically. |
| Non-standard no-return ERC-20 | The existing default-true call convention may be retained, but the custody delta remains authoritative. |
| Prior donation | It is already included in `C0`, cancels from `C1 - C0`, and is never credited to the new depositor. |
| Donation between separate deposits | Each call has its own `C0`; neither depositor receives the inter-call donation. |
| Callback/nested deposit | Deposit mutex rejects the nested deposit; outer transaction either continues without it or reverts according to callback behavior. |
| Transfer-time upgrade or token logic change | The post-call balance is authoritative; invalid zero, negative, or excess observations revert. No cached token-behavior assumption is allowed. |
| Vault-side mutation during credit | `C2 != C1` reverts the whole deposit. |
| Mutation during post-credit external work | `C3 != C1` reverts the whole deposit before success events. |

A net-delta measurement cannot prove causation. If token transfer logic both
delivers tokens and changes unrelated vault custody in the same call, a net
delta within `(0, Q]` can be observationally indistinguishable from a short
receipt. Likewise, a simultaneous positive and negative mutation can net to an
apparently valid `R`. Such token behavior is unsupported unless the later
asset-behavior gate proves that transfer cannot mutate unrelated vault
custody. Phase D does not approve any asset under that gate.

Positive rebasing or unsolicited transfer during the measurement window that
pushes `R > Q` is intentionally fail-closed. There is no cap-to-`Q` path:
capping would leave an unassigned balance change inside the supposedly atomic
receipt window and make the evidence ambiguous.

### 14.5 Vault-specific credit contract

The existing external vault deposit signatures can remain unchanged. Their
`_amount` parameter changes semantically from a caller assertion to
**Teller-verified `R`**, and each returns `R`. This avoids a function-ABI break,
but the semantic change and new Teller event still require interface/ABI
inventory in Phase I before implementation.

**BasicVault / Simple path**

- Remove the aggregate `min(_amount, totalAssetBalance)` inference.
- Require `_amount > 0`; credit exactly `_amount == R`.
- The vault may assert its current custody is at least `R`, but must not use
  total custody to enlarge or redefine the receipt.
- Phase E specifies nominal deficit credit/health controls. Loss allocation,
  settlement, and final withdrawal behavior remain Phase F/G subjects.

**SharesVault / Rebase path**

- Require `_amount == R > 0` and current custody `C1 >= R`.
- Derive pre-deposit custody as `C0 = C1 - R`.
- Mint from `R` using the permanent Section 17 allocated-backing denominator,
  rounding shares down:
  `floor(R * (S + 10^8) / (A_0 + 1))`.
- Require the minted share amount to be positive. A positive receipt that
  rounds to zero must revert rather than become an uncredited donation.
- Phase D fixes the measurement input and rounding direction; Section 17 now
  supplies the allocated-backing denominator, bounded-dust proof, total-loss
  behavior, and post-zero non-allocation.

**StabVault / Stability Pool path**

- Use verified `R` instead of `min(_amount, aggregate custody)`.
- Preserve the current GREEN/sGREEN value conversion, claimable-value inputs,
  virtual offset, and share-mint direction.
- Compute the new-user value from `R` and the pre-deposit value represented by
  custody excluding `R`; mint shares rounding down and require positive shares.
- Ordinary GREEN and sGREEN regression cases must continue to produce
  `R == Q`; a general Teller deposit still follows measured semantics if token
  behavior later changes. Phase D must not silently alter Stability Pool
  economics, redemption, or claim accounting.

**RipeGov**

- The RipeGov wrapper receives verified `R`, delegates it to SharesVault, and
  must return `R`.
- `RipeGovVaultDeposit.amount` is `R`; `shares` is the positive share result
  minted from `R`. Lock-duration and governance-point rules are unchanged.
- `depositTokensWithLockDuration` must be restricted to Teller, matching
  `depositTokensInVault`, so production deposit accounting cannot bypass the
  shared measurement boundary. No production direct caller was found in the
  pinned tree; direct test helpers must be routed through Teller or an explicit
  isolated vault-unit harness during implementation.

### 14.6 Limits, minimums, prices, and housekeeping

Current `TellerUtils.validateOnDeposit` remains the pre-transfer policy source.
It may reduce `A_req` to `Q` using available source balance and the applicable
per-user/global limits. Because the measurement requires `R <= Q`, a short
receipt cannot exceed either upper limit.

The existing pre-transfer minimum check uses `Q` and is insufficient when
`R < Q` or share rounding reduces the user's live amount. For non-trusted
deposits, Teller must re-read the user's final live amount after vault credit
and require it to satisfy `minDepositBalance`. Trusted Ripe-department flows
remain exempt from user/global/minimum policy, as they are today, but are never
exempt from receipt measurement or their Section 14.7 exactness rule.

Registration, reward points, health housekeeping, and pricing must consume
post-credit state:

- do not add a vault to the user's Ledger participation before nonzero credit
  succeeds;
- update Lootbox only after the vault records shares/nominal balance from `R`;
- retain each entry point's current housekeeping policy, but run it only after
  measured credit;
- add the PriceDesk snapshot only after successful measured credit;
- `depositMany` measures every item independently and remains batch-atomic,
  with its existing single final housekeeping call and one mutex spanning the
  whole batch; and
- `rebalance` records `R` as `depositAmount`, then performs withdrawal and its
  final health check atomically while retaining the mutex.

Neither Lootbox, housekeeping, nor PriceDesk receives `A_req` or `Q` as a credited
amount. They read the final vault/account state produced from `R`.

### 14.7 Deposit-consumer disposition

The pinned caller trace supporting this matrix is:

| Source | Deposit use |
| --- | --- |
| `contracts/core/Teller.vy:229-320` | Public single/batch/trusted entry points and shared `_deposit` ordering |
| `contracts/core/Teller.vy:400-446` | Rebalance consumes `_deposit` return and emits `TellerRebalance` |
| `contracts/core/Teller.vy:626-642` | Teller-held sGREEN deposit |
| `contracts/core/Teller.vy:761-772` | RipeGov deposit with lock |
| `contracts/vaults/modules/BasicVault.vy:23-39` | Current nominal aggregate-balance clamp |
| `contracts/vaults/modules/SharesVault.vy:25-46` | Current share receipt and mint inputs |
| `contracts/vaults/modules/StabVault.vy:109-141` | Current Stability Pool receipt/value/share inputs |
| `contracts/vaults/RipeGov.vy:131-179` | Teller wrapper, broader locked-deposit authorization, points, and event |
| `contracts/vaults/modules/StabVault.vy:756,994` | RIPE reward stake and collateral-claim auto-deposit |
| `contracts/core/BondRoom.vy:223` | RIPE bond payout/stake |
| `contracts/core/Lootbox.vy:1157` | RIPE reward stake |
| `contracts/core/HumanResources.vy:426` | RIPE compensation stake |
| `contracts/core/CreditEngine.vy:1207` | sGREEN recipient deposit |
| `contracts/core/CreditRedeem.vy:293` | sGREEN recipient deposit |
| `contracts/core/Deleverage.vy:456` | Replacement-collateral deposit |

Repository-wide production-source search found no other direct vault deposit
caller. Implementation must repeat that inventory against the then-current
integrated commit.

Every production call found in the pinned source is assigned one of two
receipt policies:

- **measured**: accept `0 < R <= Q` and expose the difference; or
- **exact**: capture Teller's return and require `R == A_req`, which proves
  `R == Q == A_req`; revert the entire upstream operation on a source-balance cap
  or short receipt.

| Consumer / route | Policy | Required disposition |
| --- | --- | --- |
| Teller `deposit` | Measured | Return and emit `R`; caller-requested `A_req` and transfer attempt `Q` remain observable in the new event. |
| Teller `depositMany` | Measured per item | Each item gets an independent delta and event; any failed item reverts the batch. Existing function return shape need not change. |
| Teller `rebalance` | Measured | Use returned `R` in `TellerRebalance.depositAmount`; withdrawal and final health check remain atomic. |
| Teller `depositIntoGovVault` | Measured | Pass `R` to RipeGov; lock and points derive from credited shares. |
| Teller GREEN→sGREEN→Stability Pool | Exact | Capture `_deposit` result and require it equals the ERC-4626 `sGreenAmount`; return that exact amount. |
| Stability Pool/StabVault ordinary GREEN or sGREEN deposit | Measured | Preserve current economics using `R`; regression must prove current GREEN/sGREEN behavior yields `R == Q`. |
| StabVault collateral-claim auto-deposit | Measured | Credit only `R`. The claim event continues to describe collateral removed/routed; the Teller measurement event is the credited-amount record. |
| StabVault RIPE claim reward | Exact | Capture return and require equality with minted `ripeAvailable` before clearing approval. |
| BondRoom RIPE payout/stake | Exact | Capture return and require equality with `totalRipePayout`; payout accounting cannot exceed stake credit. |
| Lootbox RIPE reward stake | Exact | Capture return and require equality with `amountToStake`; reward accounting cannot exceed stake credit. |
| HumanResources RIPE stake | Exact | Capture return and require equality with `_amount`; compensation accounting cannot exceed stake credit. |
| CreditEngine sGREEN deposit for recipient | Exact | Capture return and require equality with minted/routed `sGreenAmount`. |
| CreditRedeem sGREEN deposit for recipient | Exact | Capture return and require equality with minted/routed `sGreenAmount`. |
| Deleverage collateral swap | Exact | Capture return and require equality with calculated `depositAmount` before housekeeping/event; `CollateralSwapped.depositAmount` is the verified amount. |
| Direct BasicVault, SharesVault, StabVault, or RipeGov production call | Prohibited | Teller is the only production deposit-accounting boundary. Vault-only unit harnesses may exercise internal math without representing an authorized production path. |

An exact caller compares Teller's return to the amount it supplied, so it need
not recover Teller's internal `Q`. The check occurs in the same transaction;
a mismatch rolls back minting, withdrawal, claim accounting, approvals, and
any intermediate bookkeeping. The StabVault collateral-claim auto-deposit is
the sole identified trusted path allowed to accept a short receipt because it
routes an already-determined user claim through a potentially
behavior-changing asset; it must not describe `Q` as the vault credit.

### 14.8 Event and ABI contract

Existing successful-deposit events retain their signatures for compatibility:

- `TellerDeposit.amount = R`;
- `SimpleErc20VaultDeposit.amount = R`;
- `RebaseErc20VaultDeposit.amount = R`;
- `StabilityPoolDeposit.amount = R`;
- `RipeGovVaultDeposit.amount = R`;
- share fields report shares actually minted from `R`;
- `TellerRebalance.depositAmount = R`; and
- `CollateralSwapped.depositAmount = R` after its exact-receipt assertion.

Teller must add one additive evidence event; its exact field contract is:

```text
TellerDepositMeasured(
    user,
    depositor,
    asset,
    inputAmount=A_req,
    transferAmount=Q,
    receivedAmount=R,
    creditedAmount=V,
    vaultAddr,
    vaultId
)
```

`user`, `depositor`, and `asset` should retain the existing indexed identity
pattern. Emit this event only after every custody, credit, minimum, and
post-credit check succeeds, immediately before the existing `TellerDeposit`.
The explicit `creditedAmount` is intentionally redundant with `receivedAmount`;
their equality is machine-checkable evidence of I-01 rather than an inference
from two contracts.

No existing function selector or return type must change for Phase D.
Interfaces that already return the credited amount retain that type. Callers
that currently ignore `depositFromTrusted` must consume it according to
Section 14.7. The additive event and any authorization tightening are future
ABI/source changes subject to Phase I inventory and separate implementation
approval.

### 14.9 Phase D acceptance and remaining gates

Phase D is specification-complete when the companion validation plan maps
tests to all rules above. The design establishes:

```text
0 < credited = returned = emitted existing amount = R <= Q <= A_req
```

`A_req` may be the `max_value(uint256)` sentinel, but `validateOnDeposit` still
derives `Q <= A_req`. It also establishes:

```text
C1 = C0 + R
C2 = C1
C3 = C1
prior donation is included in C0, not R
```

For the nominal path, `N' = N + R` and `C1 = C0 + R`, so a successful
deposit preserves the pre-call aggregate difference `C - N`; it cannot create
a new accounted deficit. For the corrected share path, Section 17 supplies
pre-deposit effective allocated backing `A_0`, so
`S' = S + floor(R * (S + 10^8) / (A_0 + 1))`. Therefore `Q - R` cannot mint
shares, and pre-existing quarantine `U` affects neither the call-local receipt
nor the conversion denominator.

The recorded option 4 direction and this deposit design did not by themselves
resolve backing or existing-debt deficit behavior. Section 15 now specifies
those Phase E concerns under the recorded existing-controls constraint.
Settlement policy, total-loss transition, post-zero allocation, reward units,
production-vault selection, and migration remain unresolved.

## 15. Phase E — backing, collateral-use, and debt health

### 15.1 Authorization and no-new-state boundary

The recorded Phase E instruction rejects a new stored per-asset collateral-use
parameter by default and authorizes specification work to reuse existing
deposit controls and `DebtTerms.ltv`. This phase therefore specifies no change
to:

- `AssetConfig` or `DebtTerms` layout;
- MissionControl storage;
- canonical `interfaces/*.vyi`;
- any externally callable selector, return type, event, ABI, default,
  migration, or manifest; or
- the existing `SwitchboardBravo._isLtvWithinMaxDeviation` rule that prevents a
  direct nonzero-to-zero LTV change.

A future implementation may need a contract-local declaration for an already
deployed MissionControl getter. That is a compile-time adapter, not a new
deployed selector or protocol interface, and must still be itemized in the
Phase I impact table. If implementation review finds that a new stored field or
external selector is actually necessary, work stops and returns to the owner
before proposing it.

Phase E changes the **consumption semantics** of existing state. It does not
authorize implementation or Phase F.

### 15.2 Existing controls and the selected predicate

The existing controls have distinct jobs:

| Input | Existing source and evidence | Phase E meaning |
| --- | --- | --- |
| `AssetConfig.canDeposit` | `MissionControl.assetConfig(asset)` and `getTellerDepositConfig`; `CanDepositAssetSet` | Existing fast asset safety switch. `false` blocks deposits today and, under Phase E, also contributes zero new borrowing capacity. |
| `DebtTerms.ltv` | `getDebtTerms(asset)`; `PendingAssetDebtTermsChange` and `AssetDebtTermsSet` | Per-asset economic/prelaunch eligibility and capacity coefficient. `0` means the asset is not borrowable. It is not an incident-time custody sensor. |
| Per-user/global deposit limits and minimum | Existing Teller deposit config | Exposure bounds while deposits are enabled. They do not measure backing and do not change the value of an existing position. |
| General `GenConfig.canDeposit` | Existing general deposit config | Protocol-wide deposit admission only. It is not composed into per-asset collateral eligibility because a general maintenance pause must not zero every account's collateral capacity. |
| General `GenConfig.canBorrow` | Existing borrow config | Protocol-wide borrow gate and incident bridge. It remains defense in depth, not the asset-specific answer. |
| Automatic backing state | Existing token and Vault getters defined below | Call-time proof that the specific `(vault, asset)` accounting is safely backed. No operator transaction or oracle is required to make a deficit fail closed. |

Pinned source anchors are `interfaces/ConfigStructs.vyi:88-117`;
`MissionControl.vy:599-613,643-667`; `SwitchboardCharlie.vy:428-433,
1140-1185`; `SwitchboardBravo.vy:501-527,555-565`;
`CreditEngine.vy:373-425,542-579,687-807,920-979,1246-1285`;
`PriceDesk.vy:86-100,142-176`; `BasicVault.vy:116-148`;
`SharesVault.vy:123-165`; and
`StabVault.vy:219-222`. The relevant existing event definitions are
`SwitchboardCharlie.vy:311-314` and `SwitchboardBravo.vy:117-126,158-165`.

For user position amount `M(v,a,u)` in vault `v` and asset `a`, the selected
effective new-borrow predicate is:

```text
capacityEligible(v,a,u) =
    AssetConfig[a].canDeposit
    and DebtTerms[a].ltv > 0
    and backingSafe(v,a,u)
    and M(v,a,u) > 0
```

There is deliberately no third boolean. The functional “collateral-use flag”
required by the task contract is the derived result of this predicate.

This choice creates one intentional coupling: disabling an asset's deposits
also disables that asset's support for **new** borrowing. That is an accepted,
conservative liveness restriction and makes `canDeposit` an asset safety freeze,
not merely a throughput toggle. Operators must not use the per-asset switch for
casual maintenance. The general deposit switch remains available when deposits
must pause without changing per-asset credit treatment.

`DebtTerms.ltv` remains the normal launch/economic control. It is not the
emergency switch because changes are governed and pending, the current
nonzero-to-zero transition is rejected, and an LTV value says nothing about
whether custody still exists. No Phase E change weakens those protections.

### 15.3 Automatic backing model

For every actual user position traversed by CreditEngine:

```text
C(v,a) = IERC20(a).balanceOf(v)
T(v,a) = Vault(v).getTotalAmountForVault(a)
M(v,a,u) = amount returned with a by
           Vault(v).getUserAssetAndAmountAtIndex(u, index)

aggregateDeficit(v,a) = C(v,a) < T(v,a)
zeroClaimPosition(v,a,u) = a != empty(address) and M(v,a,u) == 0

backingSafe(v,a,u) =
    not aggregateDeficit(v,a)
    and not zeroClaimPosition(v,a,u)
```

The asset-zero result remains the explicit non-collateral signal. StabilityPool
continues to return `(empty(address), 0)` to CreditEngine and is not pulled into
this design.

The same existing getters have vault-specific meaning:

- BasicVault/Simple returns persisted nominal user and total balances. Thus
  `T=N`, and any `C<T` is an aggregate nominal deficit. Every user's capacity
  for that `(vault, asset)` becomes zero; remaining custody is not silently
  assigned by user order.
- Current SharesVault/Rebase returns each user's live, round-down claim and
  returns live token custody as its vault total, so current partial loss is
  pro-rata and `C=T`. Under Section 17, the corrected user amount is the claim
  against `A`, and the aggregate economic total is `T=A<=C`; quarantine `U`
  is excluded. At total loss, the getter still returns the asset for a
  nonzero-share position but its amount is zero, so `zeroClaimPosition`
  catches the state that CreditEngine currently skips. Phase I must make the
  selected getter semantics explicit.
- A surplus `C>T` on a nominal vault is not a deficit and is not assigned to
  any depositor by this check. Phase D's receipt rule prevents a donation from
  becoming the next call's credit.

Both `C` and `T` reads are mandatory. A failed or malformed backing read is not
converted into optimistic capacity: a state-changing borrow reverts, and a
preview must return no capacity or fail rather than report a positive amount.
No price is consulted before this classification.

The nominal path expressly rejects:

```text
min(userNominal, C)
```

That formula lets multiple users each point at the same remaining custody. A
one-unit aggregate deficit therefore disables the entire affected nominal
`(vault, asset)` contribution until accounting is restored or an owner-approved
loss allocation replaces it.

### 15.4 CreditEngine evaluation and ordering

`CreditEngine._getUserBorrowTerms` is the shared calculation boundary for
maximum-borrow preview, state-changing borrow validation, account health,
liquidation/redemption eligibility, debt-term refresh during repayment, and
the excluding-asset calculation used by withdrawal preview. Phase E requires
the following order for each enumerated position:

1. Read `(asset, M)` from the Vault, where `M` is the call-local value of
   `M(v,a,u)`. Continue only when `asset` is empty. Do **not** continue merely
   because `M == 0`.
2. Read the existing asset configuration and `DebtTerms`.
3. If `ltv == 0`, treat the ordinary asset as intentionally non-collateral.
   A position with no configured debt terms contributes neither capacity nor
   resolution terms.
4. Read `C` and `T`, then derive `aggregateDeficit`,
   `zeroClaimPosition`, and `backingSafe` without an oracle.
5. Derive `capacityEligible` from Section 15.2.
6. Only an amount that is backing-safe may be sent to PriceDesk.
   State-changing borrowing uses the existing raising price mode. Previews and
   health use the non-raising mode and fail closed to zero value.
7. For an eligible position, compute:

   ```text
   liveCollateralValue = price(M)
   configuredMaxDebt = liveCollateralValue * DebtTerms.ltv / 100%
   capacityContribution = configuredMaxDebt
   resolutionWeight = max(configuredMaxDebt, 1)
   ```

8. For a backing-safe position whose `canDeposit` is false, compute its live
   value in non-raising mode for existing-debt resolution, but set:

   ```text
   capacityContribution = 0
   resolutionWeight = max(
       liveCollateralValue * DebtTerms.ltv / 100%,
       1
   )
   ```

   This prevents new borrowing immediately without pretending safely
   deliverable existing collateral vanished from liquidation math.
9. For an aggregate deficit, zero-claim position, or failed non-raising price,
   do not add collateral value or capacity. Preserve the configured
   liquidation, redemption, fee, rate, and daowry terms with the existing
   fallback weight of one. The zero contribution must not be skipped.
10. Add collateral value and `totalMaxDebt` only when the position is not the
    explicitly skipped `(vaultId, asset)` pair. Terms are still accumulated
    consistently for the call's documented purpose.

The future implementation should express these rules once in the shared
borrow-terms calculation, not as caller-specific patches. The `UserBorrowTerms`
shape need not change. `totalMaxDebt` is the sum of capacity contributions;
`collateralVal` is the sum of safely valued, deliverable live collateral used
for resolution; and the existing `DebtTerms` result is the weighted resolution
term set. A one-unit fallback weight is evidentiary/defensive—it prevents the
only unsafe asset's terms from collapsing to zero without materially
overwriting the weights of solvent positions.

Repayment is a special liveness context. Its debt-term refresh must use
non-raising prices, and known disabled/deficit/zero-claim positions must not
invoke PriceDesk as a prerequisite to repayment. A missing or stale price
therefore cannot stop the user from reducing debt. The repayment amount and
Ledger debt remain independent of collateral valuation.

This is an intentional current-behavior delta, not merely a refactor.
`CreditEngine._repayDebt` currently passes `True` at line 558, and the shared
loop passes that raising mode to PriceDesk at line 741. The Phase I impact
table must call out the change to non-raising repayment refresh, its
conservative zero-value/weight behavior, all repay event fields affected by the
recomputed collateral/health result, and the regression proof that debt still
decreases when a configured feed is unavailable.

The backing model also adds at least two CreditEngine-initiated staticcalls per
enumerated position: token `balanceOf(vault)` and
`Vault.getTotalAmountForVault(asset)`. A share vault's total getter may itself
perform another token balance read. Phase I and security review must inventory
these hot-path calls, benchmark worst-case configured user vault/asset counts
for borrow, preview, health, liquidation, repay, and withdrawal preview, and
consider safe per-traversal reuse of an identical `(vault, asset)` observation.
Gas optimization may not weaken same-call backing consistency or introduce
stored/stale backing state.

### 15.5 Required consumer behavior

| Surface | Required Phase E behavior |
| --- | --- |
| `getMaxBorrowAmount` | Uses the shared predicate. Disabled, deficit, zero-claim, or unpriced positions add zero; unrelated eligible solvent collateral retains its exact value/capacity. |
| State-changing borrow | Uses the same backing and control inputs as the preview. Positive debt cannot be created from a contribution that preview treats as zero. A safe asset with a required invalid price reverts rather than borrowing optimistically. |
| `hasGoodDebtHealth` | Compares debt with `totalMaxDebt` from eligible solvent contributions. A deficit entry is processed, not skipped. The account is healthy only if other eligible collateral actually covers the debt. |
| `canLiquidateUser` / redemption eligibility | Uses only safely valued, deliverable collateral and preserved nonzero resolution terms. If the only configured collateral is missing, collateral value is zero while its threshold remains nonzero, so existing debt does not become falsely non-liquidatable. Phase F still owns whether and how settlement may progress. |
| Repayment | Remains open. It reduces the existing account-level Ledger debt and refreshes terms conservatively without requiring a price for a known unsafe asset. It does not mutate LTV, allocate loss, or create bad debt. |
| `getMaxWithdrawableForAsset` | Uses the same backing/config calculation for the target and remaining assets. It returns zero for a deficit/zero-claim position, and for a disabled collateral asset while the user has debt. With no user debt, ordinary solvent withdrawal remains subject to Teller/Vault controls; Phase E does not authorize deficit allocation or withdrawal. |
| Existing auctions, internal settlement, deleverage, and bad debt | No new permission or transition is granted. Phase F remains the mandatory design gate. Phase E's health result may expose an unsafe account but cannot pay for, transfer, or write off missing collateral. |

`DebtTerms.ltv == 0` remains the prelaunch/non-collateral state. Phase E does
not repurpose the other debt terms as a custody switch and does not zero them
during an incident. Existing account-level debt remains in Ledger, continues
under the protocol's interest rules, and can be repaid. Because the incident
action is `canDeposit=false`, the configured nonzero liquidation and rate terms
remain available for resolution instead of disappearing with an amount-zero
skip.

### 15.6 Mixed collateral and price independence

For a user with positions `p`:

```text
totalMaxDebt =
    sum(capacityContribution(p))

resolutionCollateralValue =
    sum(safelyValuedDeliverableCollateral(p))
```

An unsafe position contributes zero to both sums. A solvent, enabled, priced
position contributes exactly its existing live value and
`value * ltv / 100%`; it is not haircut merely because another position is
unsafe. Therefore:

- one missing unit in a nominal vault can never support new GREEN debt;
- other solvent collateral remains valued exactly once;
- existing debt is not healthy merely because the unsafe position's amount is
  zero; and
- the account may remain legitimately healthy when unrelated eligible
  collateral alone covers its debt.

Backing classification precedes price lookup. A missing, zero, or stale price
cannot clear `aggregateDeficit` or `zeroClaimPosition`. It independently makes
the affected capacity zero (or makes a state-changing borrow revert). A known
unsafe position does not need any price to contribute zero or to preserve its
configured resolution terms.

### 15.7 Fast disable, stronger re-enable, and operator evidence

Existing permissions already implement the required asymmetry:

- `SwitchboardCharlie.setCanDepositAsset(asset, false)` passes lite-action
  permission to `_hasPermsForLiteAction`, so an authorized lite actor or
  governance can disable quickly.
- `setCanDepositAsset(asset, true)` does not receive lite permission, so
  re-enable requires governance.
- `SwitchboardBravo.setAssetDebtTerms` remains governed and pending. It is not
  the incident response path.

Under the future Phase E implementation, this fast disable is not a neutral
deposit pause. For an existing borrower, it immediately removes the affected
asset's `totalMaxDebt` contribution. Depending on the user's other collateral
and debt, `getMaxBorrowAmount` may become zero, `hasGoodDebtHealth` may become
false, and indebted withdrawal capacity may tighten. Because backing-safe
custody remains in `collateralVal` with its configured resolution terms, the
disable alone does **not** manufacture liquidation eligibility for an
otherwise solvent position; liquidation still uses live deliverable value and
its threshold. A lite actor must assess affected borrowers and be prepared to
hold the broader borrow/auction controls before using this asset-level safety
freeze.

The recommended incident sequence is:

1. set general `canBorrow=false` if the blast radius or asset identity is still
   uncertain;
2. set affected `canDeposit=false`, which immediately blocks deposits and,
   after the Phase E implementation, removes that asset's new-borrow support;
3. set `canBuyInAuction=false` for the affected asset as a separate existing
   containment action, without treating that as Phase F settlement approval;
4. reconcile every registered vault's `C`, `T`, user claims, debt, and active
   auctions; and
5. re-enable only through governance after `C>=T` for nominal paths, no
   debt-bearing zero-claim share state remains, prices and code identity are
   current, and the applicable settlement/migration plan is approved.

Even if governance re-enables `canDeposit` prematurely, the automatic backing
check still prevents an actual deficit from contributing capacity. Phase H
Section 18 adds operational detail and explicitly preserves this onchain
fail-closed property.

No new event is required to prove configuration changes:

- `CanDepositAssetSet` identifies the asset, new value, and caller;
- `PendingAssetDebtTermsChange` records proposed terms and confirmation block;
  and
- `AssetDebtTermsSet` records applied terms.

Monitoring must collect one same-block evidence bundle containing:

- `MissionControl.assetConfig(asset).canDeposit`;
- `MissionControl.getDebtTerms(asset)`;
- `IERC20(asset).balanceOf(vault)`;
- `Vault.getTotalAmountForVault(asset)`;
- the user's indexed asset/amount where user-level diagnosis is required; and
- `getMaxBorrowAmount`, `hasGoodDebtHealth`, and `canLiquidateUser`.

The getter bundle is the evidence for derived backing state; there is no
stored “deficit cleared” bit that can become stale or be flipped without
restoring custody.

### 15.8 Conservation and no-double-counting proof

For each nominal `(vault, asset)`:

```text
if C >= T:
    sum(user nominal balances) = T <= C
else:
    capacityContribution(user) = 0 for every user
```

For each share `(vault, asset)`, user amounts are round-down live claims against
the same `C`, so:

```text
sum(user live claims) <= C
```

The virtual offset and per-user rounding may leave dust; they cannot allocate
more than live custody. If a user's nonzero shares round to zero, that position
is processed as a zero-claim unsafe entry rather than disappearing.

Different vaults have different custody addresses and are checked separately.
The same asset in two vaults therefore cannot cause one vault's custody to back
the other's accounting. Within a nominal deficit, no user-order formula
allocates the same remaining `C` more than once.

Preview and state-changing borrow both consume the same
`_getUserBorrowTerms` rules and same onchain inputs. At an unchanged block/state
with a valid price, they derive the same per-position capacity and aggregate
maximum debt. With an invalid price they differ only in failure presentation:
preview reports no optimistic capacity, while state-changing borrow reverts.

### 15.9 Phase E acceptance and remaining boundary

Phase E is specification-complete only with the companion Section 7 validation
matrix. A future implementation must prove:

1. a one-unit nominal aggregate deficit produces zero capacity for every user
   of that `(vault, asset)`;
2. unrelated solvent collateral retains exact value and capacity;
3. an amount-zero unsafe position retains resolution terms and cannot make
   existing debt falsely healthy or non-liquidatable;
4. preview and state-changing validation share the same calculation;
5. repayment remains live without a valid price for a known unsafe position;
6. fast disable and governance-only re-enable retain their existing authority
   boundary;
7. no new storage field, canonical interface, selector, ABI, default, or
   migration is introduced;
8. the change is generic—no asset name, issuer, vault ID, or chain branch; and
9. worst-case hot-path call count and gas remain within reviewed bounds without
   caching stale backing state.

Phase E does not select a production vault, approve implementation, change a
live flag, allocate a loss, authorize liquidation settlement, or create a
bad-debt transition.

## 16. Phase F — settlement, liquidation, and bad-debt progress

### 16.1 Authorization and design boundary

The owner-confirmed Phase F direction is:

1. issuer-controlled collateral is external-settlement-only; and
2. total loss uses an atomic, exactly-once transition from user debt to
   Ledger bad debt.

The approval is for specification work only and requires a stop after this
section and its validation contract are documented. It does not approve:

- a production vault or listed asset;
- production code, interface, ABI, storage, default, migration, or test
  changes;
- a Base transaction or migration;
- Stability Pool, Endaoment, Curve, Aerodrome, Underscore, or yield routing for
  Stock Tokens;
- a nominal partial-loss allocation, restoration/donation allocation, insurer,
  or recovery token;
- either implementation mechanism returned in Section 12.2; or
- Phase G at the time of that instruction. Phase G was authorized separately
  only by the later owner message recorded in Section 12.1.

The standing `canRedeemCollateral = false` and
`shouldSwapInStabPools = false` requirements remain mandatory. Phase F defines
how a future shared implementation must behave; it does not enable either
route.

### 16.2 Pinned current-path findings

The Phase F source trace at the pinned tree establishes:

| Path | Current ordering and authority | Required Phase F delta |
| --- | --- | --- |
| Auction purchase, external mode | `AuctionHouse._buyFungibleAuction` calls `withdrawTokensFromVault` and returns on zero before transferring GREEN and calling `repayDuringAuctionPurchase` (`AuctionHouse.vy:1130-1148`) | Preserve delivery-before-payment ordering; measure what the recipient actually receives and re-check current backing |
| Auction purchase, internal mode | The buyer controls `_shouldTransferBalance`; `transferBalanceWithinVault` moves only vault accounting, after which GREEN and debt commit (`AuctionHouse.vy:1014-1085`, `1217-1228`) | Unavailable for issuer-controlled collateral; no paid nominal-only move |
| Stability Pool liquidation | `_swapAssetsWithStabPool` forces external mode, returns on zero, then swaps and reduces the repayment target (`AuctionHouse.vy:735-778`) | Stock Token route remains disabled; if another asset uses it, credit remains bounded by actual delivery |
| Deleverage | It withdraws externally through AuctionHouse, derives USD value from the returned amount, and calls `repayFromDept` only for the resulting value (`Deleverage.vy:857-907`, `1044-1078`) | Preserve and strengthen delivery measurement; never repay more than recipient receipt |
| Credit redemption | A caller-selected internal/external mode exists; Stock Tokens are blocked by `canRedeemCollateral`, but the common path burns GREEN after the vault result (`CreditRedeem.vy:197-260`; `CreditEngine.vy:1153-1175`) | Standing Stock Token disable remains; any future external-required asset must reject internal mode and require positive measured delivery before burn/debt change |
| Auction creation | `_canStartAuction` checks a nominal/user balance and liquidation state, not live custody (`AuctionHouse.vy:876-888`) | Require a positive safely allocable live amount at creation and restart |
| Active auction | Ledger stores timing/identity, but no custody reservation or snapshot (`Ledger.vy:575-754`) | Re-evaluate live allocable custody on every purchase; an auction never reserves custody |
| User debt | Only CreditEngine can call `Ledger.setUserDebt`; clearing liquidation removes all fungible auctions (`Ledger.vy:318-353`) | Keep CreditEngine as debt-policy owner |
| Protocol bad debt | `Ledger.setBadDebt` is a Switchboard-only global overwrite; Switchboard Delta reaches it through a pending governed action (`Ledger.vy:829-841`; `SwitchboardDelta.vy:936-947`, `1298-1301`) | Do not use this manual overwrite to simulate an atomic per-user transition |

The source contains no automatic current path that both removes a specific
liability from `userDebt` and increments `badDebt`. It also contains no
per-user bad-debt marker. Those are current-behavior facts, not proposed
changes.

### 16.3 Settlement vocabulary

For one `(vault, asset, user, recipient)` settlement attempt:

| Symbol | Meaning |
| --- | --- |
| `C` | Live token custody at the vault immediately before delivery. |
| `K_u` | User's live economic claim under the selected vault math. |
| `L_u` | Amount safely allocable to the user now, after aggregate backing, allocation, and route policy. |
| `Q` | Maximum token amount requested from the vault for this settlement. |
| `W` | Amount the vault deducts from the user's claim and reports as withdrawn. |
| `R` | Positive call-local increase in the external recipient's token balance. |
| `E` | Chargeable delivery amount: `min(Q, W, R)`, subject to the mismatch rules below. |
| `V(E)` | GREEN-denominated value of `E` under the approved price calculation. |
| `P` | GREEN actually committed for this settlement. |

For total-loss debt resolution:

| Symbol | Meaning |
| --- | --- |
| `D_s` | User debt stored in Ledger at the transition's compare-and-set point. |
| `Y` | Interest accrued from `D_s.lastTimestamp` to the transition timestamp but not yet stored or added to `unrealizedYield`. |
| `D_f` | Final current user liability, `D_s.amount + Y`, after all earlier actual repayments are reflected. |
| `X` | Residual liability moved atomically from user debt to bad debt; for the selected full total-loss transition, `X = D_f`. |
| `BD_0`, `BD_1` | Ledger bad debt immediately before and after the transition. |

`W` is not proof of delivery. A fee-on-transfer or otherwise nonstandard token
can debit the vault by `W` while increasing the recipient by less. Payment and
debt reduction use `E`, never `W` alone.

### 16.4 Generic settlement contract

Issuer-controlled collateral has one allowed settlement result: externally
delivered tokens. A buyer cannot opt into an internal vault-balance transfer.
This applies to auction purchases and to any other common path that later
permits settlement of that asset. The current Stock Token redemption and
Stability Pool flags remain false, so the rule does not imply enabling those
paths.

An external settlement must execute in this order:

1. validate the asset route, buyer/recipient, auction state, backing state, and
   maximum current `L_u`;
2. snapshot recipient balance and relevant vault/user accounting;
3. request `Q <= L_u` from the vault;
4. execute the token transfer;
5. measure `W` and recipient delta `R`;
6. reject a negative recipient delta, `W = 0`, `R = 0`, `W > L_u`,
   `R > W`, or any unexplained accounting increase;
7. set `E = min(Q, W, R)` and price only `E`;
8. commit GREEN transfer/burn/swap and reduce user debt by no more than the
   corresponding paid value;
9. update auction state, vault participation, rewards, and housekeeping from
   the committed `E`; and
10. emit the complete requested/debited/received/paid result.

`R < W` is an explicit short-delivery result, not a reason to overcharge the
buyer. Only `R` can support payment. The difference `W - R` is a collateral
transfer loss and must remain visible in the ending custody/claim evidence; it
cannot be silently reassigned to another user. An implementation may instead
reject all `R != W` tokens as unsupported, but it may not charge on `W` when
the recipient received less. `R > W` is rejected because recipient reflection,
rebase, or unrelated inflow is not collateral delivered from the liquidated
claim.

If the transfer reverts, returns false, produces an invalid delta, or fails
because of pause/blocklist/operator controls, the complete EVM transaction
reverts. GREEN ownership, user debt, vault accounting, auction data, rewards,
and housekeeping remain unchanged. The auction stays retryable after the token
restriction is removed; a temporary transfer restriction is not total loss.

For a batch, each row re-checks the policy and current `L_u`. A disallowed
internal issuer-controlled row contributes zero and cannot consume GREEN or
custody. Any later row sees custody and debt after prior committed rows in the
same transaction, so two buyers or two rows cannot allocate the same units.

### 16.5 Internal settlement for other assets

The task contract permits, but does not require, retaining internal settlement
for other assets. If retained, all of the following are mandatory:

- the asset's approved settlement mode permits it;
- the vault exposes a live claim, not raw nominal accounting;
- `L_u > 0`;
- the aggregate post-transfer claims remain no greater than live custody;
- a nominal vault is fully backed (`C >= N`) before and after the move;
- a share vault moves only the shares corresponding to the current live claim;
- the returned amount is no greater than `L_u`; and
- payment, debt, participation, points, and events commit only after the
  accounting move succeeds.

Under a nominal deficit, current Simple-vault internal and external settlement
remain frozen. `min(userNominal, C)` is still rejected because it assigns
shared loss by caller order. Under the corrected share path, the Section 17
live pro-rata claim against allocated backing can be safely allocable;
quarantined custody is excluded.

This bounded-other-asset rule is not an exception for Stock Tokens.
Issuer-controlled collateral remains external-only even while fully backed
and even if an internal share transfer would be mathematically conserved. That
is necessary because an internal move does not exercise issuer pause,
blocklist, confiscation, or recipient eligibility.

### 16.6 No existing settlement-mode parameter

The source was re-searched specifically to avoid adding a parameter
unnecessarily. `AssetConfig` contains deposit limits, `DebtTerms`, liquidation
routes, auction/redemption permissions, whitelist, and NFT state, but no field
that means issuer-controlled or external-only settlement
(`ConfigStructs.vyi:88-109`). `MissionControl.getAuctionBuyConfig` returns only
general/asset buy permissions, recipient allowlisting, and deposit-for-user
permission (`MissionControl.vy:713-722`).

Existing fields cannot safely stand in for settlement mode:

| Existing field | Why it is not the policy |
| --- | --- |
| `canBuyInAuction` | Enables or disables the entire purchase; it does not choose external versus internal delivery. |
| `canRedeemCollateral` | Controls a different route. Base USDC and other non-issuer assets also use `false`, so it is not an issuer classifier. |
| `shouldSwapInStabPools` | Selects a Stability Pool liquidation route, which Stock Tokens must keep disabled. |
| `shouldAuctionInstantly` | Selects auction creation, not settlement delivery. |
| `shouldTransferToEndaoment` / `shouldBurnAsPayment` | Select deleverage destinations/payment assets and do not describe buyer delivery. |
| `DebtTerms.ltv` or `canDeposit` | Govern credit capacity/admission; overloading either would reintroduce the Phase E semantic coupling this track carefully bounded. |
| whitelist, vault ID, token address/name, or chain ID | Either controls a different permission or violates the generic-design rule. |

There are therefore only two honest implementation shapes:

1. **All fungible auctions external.** Remove or reject buyer-selected internal
   settlement for every fungible asset. This needs no new stored mode and is
   the preferred simplification if product compatibility permits the broader
   behavior change.
2. **Generic per-asset mode.** If internal settlement must remain for some
   assets, add a narrowly named `requiresExternalSettlement`/settlement-mode
   field, carry it through the auction/redemption config getters, govern
   disable/re-enable semantics, default issuer-controlled assets to external,
   and migrate existing assets explicitly.

Option 2 is the exact new-storage/interface proposal that would be required;
it is **not selected or approved**. Option 1 is also not silently selected
because the owner's policy approval covered issuer-controlled collateral, not
a behavior change for every existing asset. The owner must choose after the
Phase I compatibility inventory.

### 16.7 Auction, liquidation, redemption, and deleverage behavior

Auction creation and restart require all current checks plus
`L_u > 0`. A nominal deficit with unresolved allocation, `C = 0`, a zero live
share claim, or an external-required asset that cannot currently deliver
cannot create a paid auction. Liquidation eligibility remains distinct:
existing debt can be unsafe and resolution-eligible even when auction
eligibility is false.

An auction is not a custody reservation. On every purchase:

- re-read the vault address, asset policy, current custody, user claim, and
  `L_u`;
- cap `Q` to the lower of remaining GREEN capacity and current `L_u`;
- settle only `E`;
- if live custody fell after creation, reduce the purchase to current `E`;
- if `L_u = 0` because custody is gone, make no payment/debt change and mark or
  remove the stale auction before total-loss finalization; and
- if positive custody exists but transfer is temporarily blocked, revert and
  retain the auction for retry rather than declaring total loss.

Auction purchase serialization plus the fresh `L_u` read proves that the first
purchase changes the second purchase's bound. No static auction snapshot can
allocate the same custody twice.

Credit redemption remains disabled for Stock Tokens. If governance ever asks
to enable redemption for another external-required asset, its common
`_shouldTransferBalance` input must reject/skip internal mode and its GREEN burn
and debt change must use positive measured `E`, not the vault's raw return.
That future enablement is outside this approval.

Deleverage remains external-only. Each asset leg must use measured `E` and
return an actual paid value. `totalRepaidAmount` is the sum of those paid
values, capped by current user debt. A zero/failed delivery contributes zero;
it cannot be converted into repayment by a target amount, nominal balance, or
price alone. The Stock Token standing constraints prohibit routing through
Endaoment, a Stability Pool, Curve, Aerodrome, Underscore, or a yield adapter.

### 16.8 Total-loss resolution eligibility

Total-loss resolution is a terminal liability transition, not another auction
or a loss-allocation shortcut. A user is eligible only when one same-
transaction scan proves all of the following:

1. current `D_f > 0`;
2. the account is in liquidation under preserved nonzero resolution terms;
3. at least one debt-supporting position is zero- or deficit-backed;
4. every safely deliverable positive claim in every participating vault has
   already been exhausted through an approved route;
5. no positive live custody remains whose ownership is unresolved by the
   nominal partial-loss policy;
6. no positive custody is merely paused, blocklisted, stale-priced, or
   otherwise temporarily undeliverable;
7. no active auction can still deliver positive collateral;
8. every zero-backed auction is canceled in the transition or was already
   removed; and
9. the debt snapshot used for transition still matches Ledger at commit.

Mixed collateral cannot jump this gate. Solvent collateral must be delivered
and applied first. A nominal partial deficit with `C > 0` remains frozen until
the owner approves an allocation; Phase F does not use total-loss resolution
to award that custody to a particular borrower, buyer, or the protocol.

Missing/stale price alone never proves total loss. Conversely, `C = 0` and no
other positive claim are token-unit facts and must not be hidden by a missing
price. Repayment remains available until the transition transaction commits.
A repayment mined first changes `D_s`/`D_f`, causing a stale transition
compare-and-set to fail or recompute. A transition mined first leaves user debt
zero, so a later `repayForUser` rejects at the existing no-debt validation
without changing liability.

### 16.9 Atomic exactly-once accounting

At the commit point, let current user liability be
`D_f = D_s.amount + Y`. The selected transition moves the full residual:

```text
X = D_f
userDebt_before = D_f
userDebt_after  = 0
BD_1            = BD_0 + X
```

The same call must also:

- remove `D_s.amount` from aggregate `totalDebt`;
- set principal to zero, `inLiquidation` to false, and remove the borrower;
- remove all of the user's fungible auctions;
- leave every vault balance/share/custody value unchanged;
- leave GREEN supply and ownership unchanged;
- leave pre-existing `unrealizedYield` unchanged; and
- add the newly accrued `Y` to `unrealizedYield` exactly once, matching current
  `setUserDebt` accrual semantics, without flushing or minting it during the
  transition.

`Y` is included in both the final user liability moved to `badDebt` and the
global pending-yield accumulator for different accounting purposes: `badDebt`
records the unpaid liability, while `unrealizedYield` preserves the protocol's
current accrued-interest booking. A later ordinary borrow can flush and mint
that pending yield under current behavior. Accounting/security review must
accept that consequence with the proposed interface; silently dropping `Y`
from either `X` or the current yield-booking path is not approved.

No new liquidation fee is created merely because no collateral can be
delivered. Fees already persisted in `D_s.amount` are part of the existing
liability; any alternative fee write-off policy requires a separate accounting
decision.

Exactly-once does not require a new per-user storage marker. The terminal
`userDebt.amount = 0`, an expected-debt/expected-timestamp compare-and-set, and
the atomic `badDebt += X` operation are the marker:

- a duplicate call sees zero user debt and cannot add `X` again;
- a concurrent repayment changes the expected debt snapshot and prevents a
  stale addition;
- an auction purchase that commits first changes debt/custody and invalidates
  eligibility;
- a transition that commits first removes auctions, so a later purchase cannot
  pay; and
- any revert rolls back debt, bad debt, auction removal, borrower removal, and
  events together.

Later recovery, donation, or issuer restoration does not reverse this
transition automatically. Section 17 records the owner's no-automatic-
allocation decision; any future recovery or recapitalization still requires a
separate owner plus counsel/risk decision.

### 16.10 Exact shared-contract interface needed

Current accounting cannot safely express Section 16.9:

- only CreditEngine may call `Ledger.setUserDebt`;
- only a Switchboard may call `Ledger.setBadDebt`;
- `setBadDebt` overwrites the global value rather than incrementing it;
- the two calls cannot currently be authorized and validated as one
  per-user compare-and-set; and
- using `repayFromDept` without delivered value would mislabel a write-off as a
  repayment and still would not increment bad debt.

The minimum coherent shared-contract proposal uses existing storage and two
new selectors:

1. `CreditEngine.resolveUserTotalLoss(user) -> transitionedAmount`
   performs the complete Section 16.8 scan, accrues `Y`, pins the Ledger debt
   snapshot, and invokes the Ledger transition. The later Phase I direction
   permits permissionless calling only for this zero-discretion shape.
2. `Ledger.moveUserDebtToBadDebt(user, expectedStoredAmount,
   expectedLastTimestamp, finalDebtAmount, accruedInterest)` is CreditEngine-
   only. It asserts the expected stored snapshot, `finalDebtAmount =
   expectedStoredAmount + accruedInterest`, positive debt, and the required
   liquidation state; then performs every state change in Section 16.9 and
   returns `X`.

The caller-policy options are:

1. permissionless/keeper-callable behind exact predicates and existing
   Department pauses;
2. restricted to an approved keeper, Department, or Switchboard role; or
3. a governed action for each transition.

Permissionless progress avoids a governance queue for a deterministic unsafe
account, but it also lets an unrelated keeper choose transaction ordering
against a borrower's intended repayment. Compare-and-set makes either mined
order accounting-safe. The later Phase I direction accepts that caller policy
only if security review proves the caller cannot choose eligibility, amount,
recipient, collateral allocation, bad-debt destination, partial position set,
or any timing-sensitive value input. Public-mempool and same-block repayment
races remain mandatory tests. If implementation requires any such
caller-supplied discretion, the caller decision returns to the owner; it
cannot inherit permissionless authority from this specification.

This proposal adds no new storage slot, no asset parameter, no insurer, and no
recovery asset. It does add one CreditEngine ABI selector, one Ledger ABI
selector/interface declaration, and corresponding events. The conceptual
Ledger event must include at least:

```text
user
expectedStoredAmount
accruedInterest
transitionedAmount
badDebtBefore
badDebtAfter
caller
```

CreditEngine must emit the eligibility/consumer result or the Ledger event must
also carry the resolution caller and canceled-auction count. Existing
`RepayDebt` must not be reused because no GREEN was repaid.

The current governed `setBadDebt(amount)` may remain only as an explicitly
audited global reconciliation tool. It must not be used for individual
transitions, and implementation review must ensure an overwrite cannot
accidentally erase bad debt accumulated by atomic transitions.

The two selectors and event/ABI changes are an exact proposal, not an
approval. The conditional permissionless policy is owner-directed for Phase I,
but the selector and Ledger migration remain returned for owner,
accounting/security, and operations review before implementation. If the
zero-discretion condition cannot be met or the interface is rejected, the
fallback remains: do not list.

### 16.11 Controls, liveness, and evidence

The existing fast `canDeposit = false` action remains the incident containment
switch described in Phase E. `canBuyInAuction = false` prevents new purchases
but does not itself cancel custody claims or move debt. The general
`canLiquidate` control governs liquidation entry. Department pauses on Teller,
AuctionHouse, CreditEngine, vaults, and Ledger retain their existing authority
and can stop the relevant call path; resumption uses the same existing
governance/department controls.

The proposed total-loss entry would necessarily fail while CreditEngine or
Ledger is paused, but Phase H proves that this current-source stop is not an
acceptable normal resolution gate: pausing Teller, CreditEngine, or Ledger
also blocks standard repayment or its debt commit. Ordinary repayment stays
available only when Teller, CreditEngine, Ledger, and the existing repay
control are active, even if asset deposit, borrow, liquidation, or auction
buying is disabled.

Phase H Section 18 closes the evidence/control inventory and rejects broad
Department pause as the normal gate. The later Phase I direction selects
existing `canLiquidate` as the resolution-gate baseline for design and permits
permissionless calling only under the zero-discretion condition in Section
16.10. No dedicated gate, selector, Ledger interface, or implementation is
approved. Phase F may not inherit “Department pause is enough.”

Operational evidence must distinguish:

- unsafe debt health;
- auction eligibility;
- live custody and safely allocable claim;
- external transfer blocked versus custody absent;
- active, stale, paused, and removed auction;
- user debt before/after;
- newly accrued interest included in `X`;
- aggregate total debt before/after;
- bad debt before/after; and
- transition caller, transaction, block/time, and source/runtime hashes.

The global effects of increasing `badDebt` are intentional but must be
reviewed: BondRoom bond proceeds can clear it, and RipeGov configurations with
`shouldFreezeWhenBadDebt` prevent withdrawal while it is nonzero
(`BondRoom.vy:202-214`; `RipeGov.vy:283-286`). A per-user transition therefore
has protocol-wide governance-token liveness consequences even though it
touches no RipeGov balance directly.

### 16.12 Phase F acceptance and stop boundary

Phase F is specification-complete only with companion validation-plan
Section 8. A future implementation must prove:

1. an issuer-controlled auction cannot use buyer-selected internal settlement;
2. external delivery precedes and bounds every GREEN/debt commit;
3. short or fee-charged delivery cannot overcharge;
4. two rows/buyers cannot allocate the same custody;
5. custody loss after auction creation is re-evaluated at purchase;
6. total loss cannot create or preserve a paid zero-backed auction;
7. pause/blocklist failure is atomic and retryable, not bad debt;
8. deleverage repayment is no greater than actual delivered value;
9. mixed solvent collateral is exhausted before resolution;
10. user debt decreases by exactly `X` while bad debt increases by exactly
    `X`, once;
11. newly accrued `Y` is included in `X`, added to `unrealizedYield` exactly
    once under current accrual semantics, and not minted during transition;
12. repayment/auction/transition race orders conserve liability and custody;
13. the Phase I-directed existing `canLiquidate` gate stops and resumes
    resolution without blocking standard repayment, the conditional
    permissionless caller has no value-relevant discretion, and the exact
    authority/event/getter/clock tests pass; and
14. no new storage, interface, ABI, default, migration, or production behavior
    is treated as approved by this document.

Phase F itself did not select any returned mechanism or caller/control
sub-decision. The later Phase I direction resolves only the existing-gate and
conditional caller assumptions described above; it does not approve the
interfaces or implementation.
At the Phase F handoff, work stopped for the owner-requested pause and Phase G
was unauthorized. The later owner message in Section 12.1 separately
authorized Phase G specification only; implementation/interface/storage work
remains unauthorized.

## 17. Phase G — corrected share-vault behavior

### 17.1 Authorization, selected policies, and current-source gap

The owner-confirmed Phase G directions are:

1. freeze new deposits after zero;
2. do not automatically allocate a later donation or issuer restoration, and
   do not create a recapitalization/recovery path without a separate owner plus
   counsel/risk decision; and
3. use explicit live-claim-based economic reward units coordinated with Track
   6 S3, never raw shares alone.

The authorization is specification-only. It does not select a production
vault, approve implementation, storage, interfaces, recovery, recapitalization,
migration, or Phase H.

Pinned current source cannot express all three policies:

- `SharesVault._depositTokensInVault` derives pre-deposit assets from the
  aggregate token balance and converts with all custody in the denominator
  (`SharesVault.vy:35-46`).
- Every user amount and the aggregate vault amount are derived directly from
  live `balanceOf` (`SharesVault.vy:151-165`), so every positive external
  delta—including donation or restoration—is automatically shareholder value.
- The current conversion is `(C + 1)/(S + 10^8)` with caller-selected
  round direction (`SharesVault.vy:202-268`); at `C = 0`, withdrawal is blocked
  but a new receipt can mint against the virtual one-asset denominator
  (`SharesVault.vy:180-196`).
- `getUserLootBoxShare` exposes raw shares divided by `10^8`, while Lootbox
  separately prices aggregate vault custody (`SharesVault.vy:116-118`;
  `Lootbox.vy:790-833`). Raw user weight therefore survives total loss and raw
  custody value includes donations.
- User deregistration checks raw user balance; asset deregistration and
  `doesVaultHaveAnyFunds` check aggregate persisted accounting only; recovery
  transfers the entire live balance only after deregistration
  (`VaultData.vy:126-151`, `175-222`, `294-303`).

A formula-only edit cannot distinguish shareholder backing from unallocated
custody. The corrected path therefore requires the semantic distinction
between allocated backing `A` and quarantined custody `U`, plus durable
checkpoints for both buckets, as defined in Section 6. The exact storage,
wrapper, selector, and deployment boundary is returned to Phase I; this
section approves none of them.

### 17.2 Allocated backing and mutation rules

For every corrected share-vault `(vault, asset)` pair:

```text
C   = current ERC-20 balanceOf(vault)
A^s = last persisted amount allocated to the share supply
U^s = last persisted amount quarantined
A   = min(A^s, max(C - U^s, 0))
U   = C - A
```

`A` is the only asset denominator for share conversion, credit, settlement,
withdrawal entitlement, and rewards. `U` is custody, but it is not a user
claim, borrowing asset, settlement asset, reward asset, or depositor receipt.
Persisting `U^s` is semantically necessary: after a donation has been
successfully observed, a later observed issuer reduction must reduce allocated
shareholder backing before consuming the separately quarantined amount. Using
only `min(A^s,C)` would silently make the donation a shareholder loss buffer,
which is an automatic allocation the owner rejected.

Every state-changing share operation must first checkpoint a negative custody
delta and any newly observed positive delta:

```text
A^s := A
U^s := U
```

It must never checkpoint `A^s` upward merely because `C` increased. Required
transitions are:

| Transition | Required allocated-backing result |
| --- | --- |
| New asset with no approved migration balance | `A^s = 0`, `U^s = C`; any existing custody is quarantined |
| Exact deposit receipt `R` | After synchronizing pre-transfer state and checking the freeze, `A^s_after = A_before + R`, `U^s_after = U_before`; only call-local `R` is allocated |
| Share withdrawal with measured vault debit `W` | Require `W <= A_before`; persist `A^s_after = A_before - W`, `U^s_after = U_before`. An unclassifiable concurrent delta reverts |
| Internal share transfer | `A^s/U^s` unchanged; only shares move, and the token-denominated amount is bounded by `A` |
| Observed external negative delta | Effective `A` falls before checkpointed quarantine; persist the recomputed `A/U`, and all shares reprice pro rata if `A` fell |
| Observed external positive delta | `A^s` unchanged; persist the entire delta in `U^s` |
| Separately approved allocation | Not available in this specification; a future transaction would have to decrement `U^s` and increment `A^s` by the same exact amount atomically |
| Migration initialization | Owner-approved reconciliation sets both buckets from proven entitlement/custody, never `A^s := C` by default |

For a deposit, let `C_0` be custody before the token transfer and `R` the
Phase D verified receipt. The vault observes `C_1 = C_0 + R`, derives
`A_0 = min(A^s,max(C_0-U^s,0))` and `U_0 = C_0-A_0`, checks the
post-zero rules, mints from `R` and `A_0`, then persists
`A^s := A_0 + R` and `U^s := U_0`. Thus pre-existing quarantine neither
changes the deposit price nor becomes the depositor's receipt.

This is accounting state, not a new collateral-use parameter. It does not
reopen the Phase E owner decision rejecting a new stored per-asset
collateral-use flag.

Valid corrected-share state also requires:

```text
S = 0  =>  A^s = 0
A^s + U^s = custody at the last successful checkpoint
```

If `S = 0` with positive `A^s`, deposit, deregistration, recovery, and
migration activation fail closed until reconciliation; the next depositor may
not inherit that malformed allocation. Positive custody with `S = A^s = 0`
is quarantine.

### 17.3 Conversion, rounding, minimums, and dust

Retain the current virtual constants:

```text
V_A = 1 asset base unit
V_S = DECIMAL_OFFSET = 10^8 raw share units
```

For a deposit receipt `R`, pre-deposit allocated backing `A_0`, and aggregate
shares `S_0`:

```text
mintedShares = floor(R * (S_0 + V_S) / (A_0 + V_A))
```

Deposits always round down. The call must require:

```text
R > 0
R satisfies the existing post-receipt minimum-deposit rule
mintedShares > 0
not Z_live
not Z_recorded
```

When `A_0 = 0` and `S_0 = 0`, the initial mint is exactly
`R * 10^8`. If `S_0 > 0` and `A_0 = 0`, the formula is not evaluated; the
post-zero freeze reverts.

For non-final conversion of shares `s`:

```text
claimDown(s) = floor(s * (A + V_A) / (S + V_S))
L_u =
    A                    if s_u = S and S > 0
    claimDown(s_u)       otherwise
```

The sole holder's live-claim view equals the final-sweep amount, so previews
and execution do not disagree. All other credit, view, reward, maximum
withdrawal, and settlement claims round down. A requested token withdrawal
`x` below the user's full claim burns:

```text
burnShares = ceil(x * (S + V_S) / (A + V_A))
```

The burn rounds up, is capped by the user's shares, and cannot transfer more
than `x`. A transfer of an internal token-denominated claim, where permitted
for a non-issuer-controlled asset, uses the same round-up share conversion.

If the final real-share burn consumes `s = S`, it transfers the remaining
allocated backing `A`, not `U`, and leaves `A^s = 0` and `S = 0`. This
last-share sweep makes virtual shares a pricing defense rather than a property
owner. It also gives rounding residue a deterministic disposition: the final
shareholder receives the remaining allocated dust; quarantined custody remains
quarantined.

The exact bounds are:

- each deposit loses less than one raw share to floor rounding;
- each non-final user conversion loses less than one asset base unit relative
  to the exact rational claim;
- each partial withdrawal burns less than one additional raw share relative
  to the exact rational requirement;
- for any partition of non-final user shares,
  `Σ floor(s_i * (A + 1)/(S + 10^8)) <= A`; and
- across any complete sequential withdrawal order, total transferred allocated
  assets are at most the starting `A`, with the final sweep transferring the
  remaining allocated residue exactly once.

The aggregate claim bound follows because `Σs_i <= S`, so the sum of floors is
no greater than `floor(S*(A+1)/(S+10^8))`; the unfloored expression is strictly
less than `A+1`, hence the integer result is at most `A`. Withdrawal
conservation then follows by induction from each successful
`A_next = A_before - allocatedDebit` plus the one final sweep. Order can change
which final holder receives sub-base-unit floor residue, but cannot change the
aggregate bound; that order effect is itself bounded by the stated rounding
dust and must be tested in both directions.

No token-decimal branch is needed. All formulas use integer base units.
Existing configured minimum deposit rules plus `R > 0` and
`mintedShares > 0` apply identically to 6- and 18-decimal assets. Tests must
cover one base unit, configured minimum minus/at/above, maximum safe operands,
and overflow/revert behavior.

### 17.4 Partial loss, total loss, and the persistent post-zero freeze

After both buckets have been checkpointed, an external reduction lowers
allocated backing first: every relevant view uses
`A = min(A^s,max(C-U^s,0))` immediately, preserving checkpointed quarantine
until `A` reaches zero. The next successful state-changing share, credit,
settlement, or Phase F resolution operation checkpoints `A^s := A` and
`U^s := U`. Raw shares do not change, so every holder absorbs the allocated
loss pro rata subject only to the bounded virtual/floor effects in Section
17.3. This ordering prevents a donation from silently becoming loss insurance
for shareholders.

Three zero predicates are reported:

```text
Z_custody  := S > 0 and C = 0
Z_live     := S > 0 and A = 0
Z_recorded := S > 0 and A^s = 0
```

`Z_custody` is the task contract's literal zero-custody state. `Z_live` is the
stronger economic freeze and also applies when the only custody left is
quarantined. It blocks any value-creating call that observes zero allocated
backing. `Z_custody` is diagnostic-only rather than an independent admission
gate: because `C = 0` implies `A = 0`, it always implies `Z_live`; every
post-zero freeze is enforced through `Z_live` or `Z_recorded`. A reverting
call cannot also persist a checkpoint because EVM
atomicity rolls the write back. Therefore a separate successful
loss-checkpoint call, or a successful Phase F total-loss transition that
checkpoints before moving debt, establishes `Z_recorded`. `Z_recorded` makes
the freeze persistent: if custody later appears, `A^s` remains zero and the
new custody is `U`.

While `Z_live` or `Z_recorded` holds:

- every deposit preview reports the freeze and every final deposit check
  reverts atomically;
- no shares are minted, credited, or reassigned;
- withdrawals and internal value transfers cannot create a positive amount;
- old shares remain unchanged and registered;
- old live claim, credit amount, settlement amount, and reward weight are zero;
- repayment and the Phase F exactly-once debt transition remain available
  under their independent controls; and
- neither repayment nor bad-debt transition erases the old property record.

The owner did not approve recapitalization. No user, issuer, keeper,
Switchboard, or migration may clear `Z_recorded`, increase `A^s`, or burn old
shares merely because new custody exists.

### 17.5 Observation boundary and issuer action ordering

An ERC-20 vault that can read only current `balanceOf` cannot prove an
unobserved historical minimum. If an issuer reduces custody and fully restores
it between all protocol observations, the final onchain state is
indistinguishable from no reduction. No share formula, oracle, event emitted by
the vault, or hosted monitor can reconstruct that transient history
trustlessly.

The exact onchain guarantee is therefore:

- every protocol state transition and every safety-critical preview uses the
  current `min(A^s,max(C-U^s,0))`;
- any successful dependent state commit first checkpoints an observed loss;
- a safety call that reverts on observed loss leaves no dependent state but
  also cannot persist the checkpoint, so a separate successful checkpoint path
  is required for durable post-zero memory;
- any positive delta after that checkpoint is quarantined as `U`; and
- a liveness-safe checkpoint path is required so an observed loss need not
  wait for a borrower action. Phase H returned the caller alternatives; the
  later Phase I direction uses an existing Switchboard actor and containment
  preconditions for the candidate analyzed in Section 19.5.

The caller policy is resolved for Phase I analysis, but the selector, storage,
and implementation remain unapproved. Tests must
include reduce→checkpoint→restore and reduce→restore-without-observation. The
second test must document the fundamental indistinguishability; it may not
claim the vault detected an event it never observed. For issuer-controlled
listing, operations must still use the Phase E fast disable and exact-token
incident evidence; this limitation is not a rationale for monitoring-only
safety.

### 17.6 Donations, restoration, and recapitalization

The selected allocation rule is uniform:

- a donation before the first deposit is `U`;
- a donation between deposits is `U`;
- a positive rebase or other unsolicited positive custody delta is `U` in
  this corrected behavior;
- restoration after an observed partial loss is `U` above the reduced `A^s`;
- restoration after `Z_recorded` is entirely `U`; and
- a later depositor allocates only its verified `R`, never pre-existing `U`.

No automatic rule awards `U` to old shareholders, the donor, a new depositor,
the protocol, or a recovery recipient. This is deliberate non-allocation, not
a protocol property claim.

A future recapitalization or recovery proposal must return to the owner and
must include counsel/risk disposition of beneficial ownership, eligible
source/recipient, exact amount, old-share and debt treatment, effect on
`A^s/S`, reward interval boundary, events, authority/timing, pause behavior,
front-running analysis, and migration/rollback. Until that approval, `U` stays
quarantined.

This behavior must not be silently imposed on existing assets whose intended
economics allocate positive rebases or yield. The live Base Rebase vault's six
registered assets are receipt/yield-bearing tokens, and current
`SharesVault` allocates their positive custody changes. This created the Phase
I requirement for a generic compatibility boundary without a Stock-specific
contract, token-name test, `chain.id` branch, or silently changed existing
semantics. Section 19 recommends the isolated generic-variant boundary and
returns its exact storage/interface design; no mode, parameter, or production
vault is approved.

### 17.7 Withdrawal, settlement, and aggregate conservation

Every withdrawal and settlement amount is bounded by the user's round-down
claim against `A`, and aggregate allocated delivery is bounded by `A <= C`.
`U` is never a fallback source for a user's claim.

For external settlement, Phase F's call-local delivery rule still controls:

```text
E = min(requested Q, vault debit W, recipient receipt R)
```

GREEN payment and debt reduction are bounded by `E`; share burn and allocated
backing reduction must reconcile to the same successful call. A revert,
false-return, blocklist, pause, or invalid debit/receipt rolls back shares,
`A^s`, `U^s`, payment, debt, auction progress, and reward state. Two auctions or
withdrawals re-read current `A`, `C`, `S`, and user shares, so both orders
cannot allocate the same backing.

An issuer-controlled asset remains external-settlement-only. Internal share
transfer for another asset may move only the rounded-up shares corresponding
to a currently allocable claim and does not reserve custody for a later
external withdrawal.

### 17.8 User/asset deregistration, VaultBook, and recovery

Corrected guards must distinguish accounting from custody:

- user/asset deregistration is allowed only after the user's raw shares are
  zero and reward state is checkpointed;
- a vault asset cannot deregister while `S != 0`, `A^s != 0`, `U^s != 0`,
  `C != 0`, or `U != 0`;
- `doesVaultHaveAnyFunds` must report true for raw shares, allocated backing,
  or live custody, including donation dust; and
- VaultBook replacement/disable checks cannot treat raw-share accounting alone
  as proof that custody is empty.

At total loss, old `S > 0` blocks deregistration even though `C = A = 0`.
When `S = A^s = 0` but donation dust exists, `U^s = C = U > 0` still blocks
deregistration and replacement. The live Base vault-ID-4 rows with one raw unit
of custody and zero shares are the pinned regression instance: corrected
semantics classify each unit as `U` and must not report the vault empty.

Current `recoverFunds` is not an approved quarantine mechanism: it requires
deregistration and transfers the entire live balance. A future recovery must
be separately approved, amount-bounded to proven `U`, incapable of touching
`A`, and compatible with registered live positions. Until then, neither
allocated backing nor quarantine is recoverable through a new Phase G path.

### 17.9 Rewards and economic units

For an ordinary corrected share-vault asset:

```text
rawShares_u       = s_u                         # accounting only
liveClaim_u       = L_u                         # token base units
rewardWeight_u    = floor(liveClaim_u / p_a)    # explicit normalized live claim
globalAssetValue  = floor(USD(A) / 10^18)       # existing whole-USD scale
```

`p_a` is the explicitly reported normalization factor. If the existing
Lootbox convention is retained, it is `10^decimals` below 8 decimals and
`10^(decimals // 2)` at 8 or more decimals
(`Lootbox.vy:838-844`). Tests must show the resulting floor for both 6- and
18-decimal assets; reports may not label normalized reward weight as tokens,
shares, or USD.

Raw shares may remain a pro-rata accounting numerator, but they cannot alone
be the economic reward balance. `U` contributes neither user reward weight nor
global asset value. At total loss, future user weight and global value become
zero; points earned before the loss remain historical and are not silently
clawed back.

The current lazy Lootbox snapshots create a second implementation requirement:
a global loss changes every user's live claim without iterating users. A
correct implementation must close the prior reward interval at the loss
checkpoint and ensure subsequent blocks use the new live-claim economics,
without letting untouched users accrue stale raw-share weight.

Integrated Track 6 S3 at `3e6e6f2` owns a different interval boundary: it
replaces Lootbox's Base-specific `ONE_DAY` constant with immutable
`MIN_UNDERSCORE_SEND_INTERVAL`, adds the constructor floor argument and
`minUnderscoreSendInterval()` getter, and preserves the strict Underscore
distribution condition. It does **not** add a per-vault loss checkpoint,
global share-price epoch/index, or untouched-user reward rebase. Section 19
therefore preserves the S3 source/ABI contract and returns the separate
Vault/Lootbox/Ledger loss-interval mechanism to the owner rather than claiming
S3 solved it.

RipeGov is a separate governance-point consumer: its
`getUserLootBoxShare` returns lock-adjusted governance points
(`RipeGov.vy:412-422`), and Lootbox already treats vault ID 2 specially. Phase
G does not redefine those governance units. A common-interface change must
preserve that distinction rather than silently interpreting RipeGov points as
token claims.

### 17.10 Events, views, reports, and manifests

Every future surface must name its unit:

| Surface | Required meaning |
| --- | --- |
| Raw user/total shares | `s_u` / `S`, integer share units; never token or USD value |
| Allocated checkpoint | `A^s`, token base units assigned to shares |
| Quarantine checkpoint | `U^s`, token base units last observed as unallocated |
| Effective allocated backing | `A = min(A^s,max(C-U^s,0))`, token base units used now |
| Live custody | `C`, raw ERC-20 `balanceOf` |
| Quarantine | `U = C - A`, token base units with no automatic beneficiary |
| User live claim | `L_u(A,S)`, token base units, round down |
| Reward weight | normalized live-claim units with `p_a` reported |
| Global reward value | whole-USD-scaled value of `A`, excluding `U` |
| Zero state | `Z_custody`, `Z_live`, and `Z_recorded`, with checkpoint block/caller where stored/emitted |

Existing Deposit, Withdrawal, and Transfer events may retain their current
amount/share fields only if `amount` means allocated call-local token amount
and `shares` means raw shares. A loss checkpoint, observed quarantine, and any
future allocation/recovery need distinct evidence carrying asset, previous/new
`A^s/U^s`, `C`, `A`, `U`, caller, and reason. Exact event names and ABI are
returned in Section 19.5 rather than selected.

The existing `amountToShares`/`sharesToAmount` signatures can remain only if
their denominators change from raw `C` to `A`; the existing
`getTotalAmountForUser` is the natural live-claim surface. The current
`getTotalAmountForVault` name is ambiguous because it returns custody for
SharesVault and nominal accounting for Simple. Section 19 preserves canonical
Vault selectors and returns specialized additive corrected-variant getters;
no selector is approved.

Repository reports must print `C`, `A^s`, `U^s`, `A`, `U`, `S`, per-user
shares and claims, reward normalization, debt, and auctions separately. Static
manifests record vault accounting version/capabilities and runtime identity;
they must not pretend to snapshot dynamic balances or omit the getter
semantics needed for post-deployment reconciliation.

### 17.11 Storage and ABI compatibility boundary

Current persisted `totalBalances` and `userBalances` are raw shares in
SharesVault. They remain raw shares; changing their unit would corrupt every
consumer. Enforcing no automatic positive-delta allocation requires some
durable equivalent of `A^s`; current storage and getters cannot derive it from
`C` and `S`. Preserving quarantine through a later observed loss also requires
durable equivalent state for `U^s`; allocated backing alone is insufficient.

That created the Phase I choice:

1. append allocated/quarantine checkpoint state to a compatible generic share
   implementation and migrate/reconcile every live asset;
2. deploy a generic vault-level behavior variant that shares canonical modules
   but isolates positive-delta policy;
3. approve another audited generic mechanism that proves the same
   `A^s/U^s/A/U` invariants; or
4. do not list.

Because SharesVault is consumed by both RebaseErc20 and RipeGov and existing
positive-rebase assets may rely on automatic yield allocation, a blanket
semantic/storage change is not assumed compatible. Section 19 maps storage
order, module export/runtime artifacts, selectors, events, every reader,
upgrade versus redeployment, Base live state, migration initialization,
rollback limits, and audit boundaries; it recommends the isolated generic
boundary and returns the exact storage/interface and migration-import choices
without selecting an implementation mechanism or production vault.

No Robinhood-only or issuer-branded vault, new collateral-use flag,
positive-delta mode, storage slot, getter, event, ABI, default, migration, or
manifest change is approved by this Phase G specification.

### 17.12 Phase G acceptance and stop boundary

Phase G is specification-complete only with companion validation-plan Section
9. A future implementation must prove:

1. after a successful bucket checkpoint, an observed negative delta reduces
   allocated backing first and reprices every share pro rata against `A`
   without using `U` as automatic shareholder insurance;
2. deposits mint from call-local `R` and pre-deposit `A`, excluding `U`;
3. deposits round down, withdrawal share burns round up, claims round down, and
   all stated dust bounds hold;
4. one-base-unit plus 6- and 18-decimal minimum/ordinary lifecycles work;
5. `Z_custody` is reported, `Z_live` blocks the observing value-creating call,
   and `Z_recorded` keeps the freeze after later custody appears;
6. old shares survive zero with zero claim/reward weight and cannot be erased
   by debt resolution;
7. donations/restoration remain `U` before first deposit, between deposits,
   and after a checkpointed partial/total loss;
8. reduce→restore without an intervening observation is documented as
   indistinguishable, not falsely claimed detected;
9. aggregate withdrawals/settlements never exceed starting `A` and never
   consume `U`;
10. deregistration, VaultBook, and recovery guards account for raw shares and
    live custody independently;
11. user reward weight derives from live claim, global value derives from `A`,
    and both exclude `U`;
12. reward interval behavior preserves the integrated S3 send-floor
    constructor/getter/strict-boundary contract and separately prevents stale
    post-loss raw-share economics;
13. RipeGov and existing positive-rebase/yield semantics are not silently
    changed; and
14. no new storage/interface/ABI/migration or production vault is treated as
    approved by this document.

## 18. Phase H — controls, governance, and operational evidence

### 18.1 Authorization and specification boundary

The owner-authorized Phase H instruction is quoted in Section 12.1. This phase
maps current controls and defines repayment-safe incident evidence. In
accordance with that instruction, it does **not**:

- propose or select a new storage field, deployed getter/setter, interface,
  event, ABI, dedicated pause, or caller policy;
- select either returned Phase F interface, any Phase G allocated-backing
  mechanism, or a production vault;
- create a Robinhood default, migration, manifest, runbook script, monitor, or
  test;
- authorize a live disable, pause, re-enable, migration, or transaction; or
- begin the Phase I source/storage/interface impact table.

Pinned source anchors are:

- `interfaces/ConfigStructs.vyi:5-18,88-117`;
- `MissionControl.vy:175-208,261-340,439-482,534-558,599-755`;
- `SwitchboardAlpha.vy:123-161,431-438,568-677`;
- `SwitchboardBravo.vy:58-173,223-325,349-565,597-704,743-798`;
- `SwitchboardCharlie.vy:181-183,311-368,428-495,755-830,899-935,
  1008-1052,1140-1210`;
- `SwitchboardDelta.vy:230-233,302-304,939-947,1298-1301`;
- `LocalGov.vy:119-160`, `TimeLock.vy:7-25,45-138`, and
  `DeptBasics.vy:13-22,63-68`;
- `VaultBook.vy:62-147,171-174` and
  `AddressRegistry.vy:7-100,109-198,226-370,404-467,478-547`;
- `VaultData.vy:11-34,103-222,230-274,294-303`;
- `BasicVault.vy:95-148` and `SharesVault.vy:103-165`;
- `Ledger.vy:131-183,319-351,406-469,582-754,815-841`;
- `Teller.vy:229-390,484-496,552-615`;
- `TellerUtils.vy:105-142,198-229`;
- `CreditEngine.vy:206-305,454-478,542-600,1217-1285`;
- `AuctionHouse.vy:231-279,1088-1162,1199-1228`; and
- `DefaultsBase.vy:42-57`.

Line references are to the source-pinned Track 8 tree. The integrated
deployment-support documents at `382eb7d` are used only for the negative fact
that no `DefaultsRobinhood` or final Stock Token configuration exists.

### 18.2 Roles, timing classes, and common failure semantics

The current controls use four authority/timing classes:

| Class | Current authority and behavior |
| --- | --- |
| Fast flag | Switchboard Alpha general flags and Switchboard Charlie asset flags write MissionControl immediately. Governance may set either value; a MissionControl lite signer may disable but may not enable. |
| Fast broad pause | Switchboard Charlie may call `pause(target,true)` immediately as governance or a lite signer. Only governance may call `pause(target,false)`. Both `PauseExecuted` and the target's `DepartmentPauseModified` or `VaultPauseModified` are emitted. |
| Config action | Switchboards Bravo, Charlie, and Delta initiate a governance-only `TimeLock` action. Confirmation is governance-only, valid at `confirmBlock <= NUMBER < expiration`, and otherwise returns false or expires/cancels according to the action executor. |
| Registry action | VaultBook/AddressRegistry start and confirm governance-only registry changes. Confirmation requires `NUMBER >= confirmBlock`; the registry path has no action-expiration window. |

`LocalGov.canGovern(addr)` and `getGovernors()` expose the local and Ripe HQ
governance set. MissionControl exposes lite actors through
`canPerformLiteAction`, `liteSigners(index)`, and `numLiteSigners`. These
getters must be part of any authority snapshot; a role name in a runbook is
not evidence that the executing address currently has the role.

Common absence behavior is fail-closed but not uniform in shape:

- an unset registry ID returns the empty address from `getAddr`;
- consumers that explicitly test the returned address may return zero/false
  without changing state, as AuctionHouse does for a missing vault;
- consumers that immediately staticcall/extcall the required empty or
  incompatible address revert or fail ABI decoding;
- an unsupported asset causes false config membership or an explicit
  `invalid asset` assertion before a fast asset flag can be changed; and
- no path interprets an absent MissionControl, VaultBook, Ledger, vault, or
  asset integration as permission to borrow, deposit, settle, write off debt,
  or migrate.

The operational interface must record the exact failure or empty-address
result. It may not normalize all absence cases to `false`, because a revert,
graceful zero, and a configured `false` flag are different evidence.

### 18.3 Current control map: storage, caller, timing, event, and getter

| ID / control | Contract and storage owner / current consumer | Caller, timing, and disable/re-enable asymmetry | Exact current event(s) and getter(s) |
| --- | --- | --- | --- |
| T8H-01 global borrowing | `MissionControl.genConfig.canBorrow`; consumed by `getBorrowConfig` and CreditEngine borrow validation | `SwitchboardAlpha.setCanBorrow`; immediate. Governance enables/disables; a current lite signer disables only. | `CanBorrowSet(canBorrow,caller)`; `MissionControl.genConfig()` and `getBorrowConfig(user,caller).canBorrow` |
| T8H-02 per-asset collateral use | No dedicated field. Phase E derives capacity from `assetConfig(asset).canDeposit`, `DebtTerms.ltv`, automatic backing safety, and nonzero live position amount. MissionControl owns the two stored inputs; vault/token reads supply backing. | Charlie changes `canDeposit` immediately with fast-disable/governance-enable asymmetry. Bravo changes debt terms through governance plus `TimeLock`; current validation refuses nonzero LTV directly to zero. Automatic backing has no operator/caller. | `CanDepositAssetSet`; `PendingAssetDebtTermsChange`; `AssetDebtTermsSet`; `assetConfig(asset)`, `getDebtTerms(asset)`, vault getters, and ERC-20 `balanceOf(vault)`. There is deliberately no single “collateral-use” event/getter. |
| T8H-03 per-asset deposits | `MissionControl.genConfig.canDeposit` plus `assetConfig(asset).canDeposit`; TellerUtils requires both and vault support. | Alpha general and Charlie asset fast flags. Both are immediate; lite actor may disable, governance may re-enable. | `CanDepositSet`; `CanDepositAssetSet`; `genConfig()`, `assetConfig(asset)`, and `getTellerDepositConfig(vaultId,asset,user)` |
| T8H-04 per-asset auction purchases | `MissionControl.genConfig.canBuyInAuction` plus `assetConfig(asset).canBuyInAuction`; AuctionHouse rechecks both for every purchase. | Alpha general and Charlie asset fast flags. Both are immediate; lite actor may disable, governance may re-enable. Active auctions remain recorded but purchase returns zero while disabled. | `CanBuyInAuctionSet`; `CanBuyInAuctionAssetSet`; `genConfig()`, `assetConfig(asset)`, and `getAuctionBuyConfig(asset,recipient)` |
| T8H-05 internal versus external settlement | No current config/storage owner. Teller exposes buyer input `_shouldTransferBalance`; AuctionHouse branches to `transferBalanceWithinVault` when true and external withdrawal when false. Phase F selects external-only behavior for issuer-controlled collateral but returns enforcement mechanism selection. | Current buyer chooses per call; no governance/timelock/asymmetry. The external route is only an entrypoint default, not an enforced policy. | No mode-change event/getter exists. The chosen route can be inferred only from call input plus settlement effects/events such as `FungAuctionPurchased`; `getAuctionBuyConfig` contains no mode. |
| T8H-06 withdrawals | `MissionControl.genConfig.canWithdraw` plus `assetConfig(asset).canWithdraw`; Teller/TellerUtils require both, authorization, limits, and debt-safe maximum. | Alpha general and Charlie asset fast flags; immediate lite disable/governance re-enable. A vault or Teller broad pause independently blocks execution. | `CanWithdrawSet`; `CanWithdrawAssetSet`; `genConfig()`, `assetConfig(asset)`, `getTellerWithdrawConfig(asset,user,caller)`, vault `isPaused()`, Teller `isPaused()` |
| T8H-07 repayment | `MissionControl.genConfig.canRepay`; CreditEngine `_validateOnRepay` consumes `getRepayConfig`. Teller, CreditEngine, and Ledger must also remain callable/unpaused. | Alpha fast flag; immediate lite disable/governance re-enable. Broad pause of Teller, CreditEngine, or Ledger can block repayment despite `canRepay=true`. | `CanRepaySet`; `genConfig()`, `getRepayConfig(user).canRepay`, and `isPaused()` on Teller/CreditEngine/Ledger; successful state evidence includes `RepayDebt` and Ledger debt getters. |
| T8H-08 liquidation initiation | `MissionControl.genConfig.canLiquidate`; AuctionHouse requires it before ordinary liquidation. | Alpha fast flag; immediate lite disable/governance re-enable. Individual auction start/pause actions in Charlie are instead governance and timelocked. | `CanLiquidateSet`; `genConfig()` and `getGenLiqConfig().canLiquidate`; individual pending/executed auction events and Ledger auction getters |
| T8H-09 bad-debt transition | Current `Ledger.badDebt` is a global amount. `SwitchboardDelta.setBadDebt` performs a governance-timelocked absolute overwrite. There is no current per-user, compare-and-set, exactly-once transition or dedicated control. Phase F returns a two-selector candidate without approval. | Current global overwrite is governance plus `TimeLock`; Ledger must be unpaused at execution. It has no fast dedicated disable/re-enable. A broad Ledger pause blocks this write and other Ledger mutations, including repayment dependencies. | `PendingBadDebtSet`; `BadDebtSet`; `Ledger.badDebt()`, Delta `pendingActions(actionId)`, and `getActionConfirmationBlock(actionId)`. No current event/getter identifies per-user loss resolution. |
| T8H-10 vault/asset registration | Vault addresses live in VaultBook `AddressRegistry`. Protocol asset config/list lives in MissionControl. VaultData registers an asset lazily on first deposit and stores the vault-local iterable. MissionControl deregistration removes iterable membership but does not erase the `assetConfig` mapping. | New vault address: governance start/confirm under registry delay. New protocol asset: Bravo governance plus `TimeLock`. Protocol/vault-asset deregistration: Charlie governance plus `TimeLock`. Vault-local initial registration is a deposit side effect, not a governance control. | `NewAddressPending/Confirmed/Cancelled`; `NewAssetPending`, `AssetAdded`; `PendingDeregisterAssetAction`, `AssetDeregistered`; `PendingDeregisterVaultAssetAction`, `VaultAssetDeregistered`; `getAddrInfo`, `pendingNewAddr`, MissionControl `isSupportedAsset/assets/indexOfAsset/getNumAssets/assetConfig`, VaultData `isSupportedVaultAsset/vaultAssets/indexOfAsset/getNumVaultAssets` |
| T8H-11 vault replacement/migration | VaultBook `AddressRegistry.addrInfo` owns the authoritative vault address. Update/disable starts only if current `doesVaultHaveAnyFunds()` reports false; neither operation moves token or user state. | Governance start/confirm under registry delay; no lite path. Disable has no fast re-enable: restoring/replacing an address is another governed registry action. Current funds guard uses vault-reported accounting and is not a complete live-custody scan. | `AddressUpdatePending/Confirmed/Cancelled`; `AddressDisablePending/Confirmed/Cancelled`; `addrInfo`, `getAddr`, `pendingAddrUpdate`, `pendingAddrDisable`, `registryChangeTimeLock`, and vault `doesVaultHaveAnyFunds()` |
| T8H-12 emergency disable/re-enable | Composition of T8H-01/T8H-03/T8H-04/T8H-06/T8H-07/T8H-08 flags and Charlie broad pause. There is no single emergency state. | Fast flags and broad pause are immediate. Lite actors may only move toward disabled/paused; governance is required to re-enable/unpause. Timelocked LTV/registry actions are not incident switches. | All flag events/getters above; `PauseExecuted(contractAddr,shouldPause)` plus target `DepartmentPauseModified` or `VaultPauseModified`; target `isPaused()` |

Events prove that a transaction emitted a claimed transition; current getters
prove the post-state at a pinned block. Neither alone is sufficient. Every
control assertion must pair the event transaction/block/log index with the
post-state getter and the current authority snapshot.

### 18.4 Base and Robinhood defaults

“Default” is separated from live state:

- **Base source default:** the value returned by committed `DefaultsBase` or
  the default argument in the current entrypoint.
- **Base live state:** a separately pinned onchain read; this section does not
  imply that source defaults equal the current live configuration.
- **Robinhood repository state:** no `DefaultsRobinhood` exists and no final
  Stock Token asset config is approved.
- **Track-required Robinhood posture:** an explicit fail-closed value required
  before any later deployment proposal; it is not a deployed fact.

| ID | Base source/default | Robinhood repository state and required posture |
| --- | --- | --- |
| T8H-01 | `DefaultsBase.genConfig.canBorrow=true` | No default contract. Required prelaunch posture is global borrow disabled until all launch gates pass. |
| T8H-02 | Per-asset. `addAsset` defaults `canDeposit=true` but empty `DebtTerms` has `ltv=0`; existing Base entries must be read individually. | No asset config. Stock Token `canDeposit=false` and `ltv=0`/unconfigured until explicit later approval; no new collateral-use field. |
| T8H-03 | General deposit true; `addAsset` asset deposit argument defaults true. | No asset config. Stock Token deposit must be explicitly false/omitted before activation. |
| T8H-04 | General auction buy true; `addAsset` asset auction-buy argument defaults true. | No asset config. Stock Token auction purchase must be explicitly false/omitted before the external-only mechanism is approved and implemented. |
| T8H-05 | Teller's public auction call defaults `_shouldTransferBalance=false`, but a buyer may pass true; there is no enforced mode. | No configured auction route. The owner-approved issuer policy is external-only, but its enforcement mechanism remains unselected. |
| T8H-06 | General withdrawal true; `addAsset` asset withdrawal argument defaults true. | No asset config. Before custody exists it is absent/false by omission. Any future incident plan should leave an already-live safe withdrawal path open unless delivery itself is unsafe; no launch value is selected here. |
| T8H-07 | `DefaultsBase.genConfig.canRepay=true`. | No default contract. Any future RH deployment proposal must explicitly keep repayment enabled and keep Teller/CreditEngine/Ledger unpaused during containment. |
| T8H-08 | `DefaultsBase.genConfig.canLiquidate=true`. | No default contract and no value selected. No Stock liquidation path exists while Stock registration/LTV/auction support is omitted; a future global value must account for every non-Stock asset on the chain. |
| T8H-09 | No DefaultsBase transition setting; Ledger storage begins at zero and the only current setter is a governed global overwrite. | No transition/default/interface. No debt write-off may be inferred from custody loss. |
| T8H-10 | Base defaults contain asset entries and Base has live registries, but each actual value is registry/config state, not a universal constant. | No Robinhood vault/asset registration is approved. Omission is the safe default. |
| T8H-11 | No migration default; Base has live VaultBook state and funded-vault guards. | No Robinhood vault address, replacement, or migration is approved. |
| T8H-12 | General Base flags are true in `DefaultsBase`; pause initial values are constructor inputs and must be read from each live target. | No composed emergency default exists. Prelaunch Stock controls remain disabled/omitted; repayment liveness is an explicit future deployment assertion. |

`SwitchboardBravo.addAsset` is especially unsafe as an implicit Robinhood
template: when arguments are omitted it defaults
`shouldSwapInStabPools=true`, `shouldAuctionInstantly=true`,
`canDeposit=true`, `canWithdraw=true`, `canRedeemCollateral=true`,
`canRedeemInStabPool=true`, `canBuyInAuction=true`, and
`canClaimInStabPool=true`. A future Stock Token action must supply and verify
every relevant boolean explicitly. The standing constraints remain:

- `canRedeemCollateral=false`;
- `shouldSwapInStabPools=false`;
- no Endaoment, Curve, Aerodrome, Underscore, Stability Pool, or yield route;
- no deposit, borrowing capacity, or auction purchase before its gates; and
- no chain/token-name branch or Stock-specific vault contract.

This finding does not authorize a default file or asset action. It is a
required fail-closed validation assertion.

### 18.5 `NUMBER` behavior and missing-integration matrix

| IDs | Repeated or jumping EVM `NUMBER` | Absent/invalid integration behavior |
| --- | --- | --- |
| T8H-01, T8H-03, T8H-04, T8H-06, T8H-07, T8H-08, T8H-12 fast flags/pause | The state change is immediate and has no elapsed-block precondition. Repeated numbers do not delay the transaction; a jump grants no additional authority. Logs at the same block require transaction hash and log index for order. | Missing MissionControl/Switchboard/target or unsupported asset makes the write fail/revert; consumers see false/empty config or fail their required call. No optimistic enable. |
| T8H-02 debt terms | Bravo stores `confirmBlock` and expiration. Repeated numbers prevent confirmation; a jump may enter or skip the valid window. Nonzero-to-zero LTV remains invalid regardless of clock. Automatic backing reads are immediate. | Missing MC/vault/token read fails or yields no eligible position; absence never creates capacity. |
| T8H-05 settlement | Route choice itself has no timelock. Auction start/end still use `NUMBER`; repeated numbers hold progress and jumps may reach/end the auction. Per-purchase custody and flags must be re-read. | Missing auction/vault returns zero or reverts before payment depending on the exact boundary; Phase F still requires no payment/debt commit without delivery. |
| T8H-09 current bad debt | Delta uses action confirmation plus expiration. Repeated numbers stall; a large jump can expire the action. | Missing/paused Ledger prevents execution. No partial global overwrite is accepted. |
| T8H-10 Bravo/Charlie asset actions | Config `TimeLock` semantics: repeated stalls; jump can enter or skip the confirmation window. Vault-local registration occurs only in a successful deposit transaction. | Missing/unsupported targets fail validation or execution. A failed registration action cannot make the asset supported. |
| T8H-10/T8H-11 registry actions | `confirmBlock=NUMBER+registryChangeTimeLock`. Repeated numbers stall; a jump makes confirmation eligible and there is no registry expiration. Confirmation still requires governance and revalidates address constraints. | Empty/invalid address or current funds guard blocks start/confirm. An address update/disable never migrates custody or accounting. |

No operator may translate block delays to seconds for Robinhood, assume
strictly increasing block numbers, or treat a jump as approval. The
repository-side record must include `chainId`, block number, block hash,
transaction hash, and log index. S1/S2 identical-artifact and checked-clock
evidence remains a Phase J prerequisite.

### 18.6 Repayment-safe incident sequence

The following is a future runbook contract, not authorization to transact:

1. Pin the chain, block number/hash, registry addresses, implementation/runtime
   identity, vault ID/address, asset, current governance/lite actors, all
   relevant flags, and target pause state.
2. Capture the full accounting/economic tuple in Section 18.10 before any
   control action when doing so does not prolong an active exploit.
3. For a known affected asset, use the existing fast asset controls to set
   `canDeposit=false` and `canBuyInAuction=false`. Under Phase E, the deposit
   disable also removes that asset from new-borrow capacity.
4. If the affected asset or blast radius is not yet known, use existing
   general `canBorrow=false` and, if auction exposure is also uncertain,
   `canBuyInAuction=false` as conservative bridges. Do not use a timelocked LTV
   edit as an incident switch.
5. Keep `canRepay=true` and keep Teller, CreditEngine, and Ledger unpaused.
   Confirm an indebted user's standard repayment path succeeds under the
   containment state. A broad pause of any of those three is not a
   repayment-safe normal response.
6. Leave withdrawals enabled when external delivery is safe. If the asset
   cannot deliver safely, use the per-asset withdrawal disable and record that
   exit liveness was intentionally sacrificed; do not casually use the global
   withdrawal flag or whole-vault pause.
7. Snapshot affected borrowers, raw positions, debt, liquidation state, and
   auctions. Do not resolve debt, checkpoint a share loss, move quarantine,
   replace the vault, or deregister the asset under this Phase H authority.
8. Require governance, a fresh pinned evidence record, and the later approved
   control/caller mechanism before re-enable. A monitor or lite signer may
   never re-enable automatically.

This sequence describes the required post-implementation operating model.
Pinned current source does **not** yet consume asset `canDeposit=false` as zero
borrow capacity; until the Phase E behavior is implemented, only the general
`canBorrow=false` flag is the existing borrowing bridge. Pinned current source
also has the raising-price repayment defect in Section 3.2. Therefore
`canRepay=true` and unpaused targets are necessary but not sufficient current
evidence: the runbook must execute or simulate the exact standard repayment
path against the deployed version and may not claim I-09 from flags alone.

The normal containment invariant is:

```text
new deposit = disabled
new affected-asset borrow capacity = 0
new affected-asset auction purchase = disabled
standard repayment = enabled and executable
withdrawal = enabled iff actual delivery remains safe
resolution/checkpoint/migration = no action without later approval
```

If an active exploit forces a broader pause that blocks repayment, the record
must label that as an exceptional owner/security decision and state the exact
repayment outage. It may not be presented as satisfying I-09.

### 18.7 Total-loss resolution gate alternatives

Current source has no dedicated total-loss resolution pause. Phase H returns
these alternatives without selecting an implementation:

| Alternative | Existing/new surface | Repayment and liveness | Blast radius / evidence | Phase H disposition |
| --- | --- | --- | --- | --- |
| Reuse `genConfig.canLiquidate` as a required gate for both ordinary liquidation and total-loss resolution | Existing MissionControl storage, Alpha setter, event, and getter; later implementation would change only consumption semantics | Standard repayment does not consume this flag. Lite actor can stop immediately; only governance can resume. | Disabling also stops every ordinary liquidation, including solvent-asset liquidation. The transition must read the same pinned control at commit. | Strongest existing-control candidate; **not selected**. Owner/security must accept the global coupling before Phase I treats it as a design. |
| Use broad Department pauses | Existing Charlie pause and target `isPaused` | Teller or CreditEngine pause blocks standard repayment; Ledger pause blocks debt writes and other repayment dependencies. Unpause is governance-only. | Very broad and target-dependent; event/getter exist. | **Rejected as the normal resolution gate** because it violates the repayment-liveness instruction. Retained only as an explicit catastrophic whole-contract fallback. |
| Add a dedicated narrow resolution pause later | Would require a new or repurposed storage owner, setter/getter, event, authority/default, ABI and migration analysis | Could preserve repayment and ordinary liquidation if designed narrowly | Precise blast radius, but creates exactly the new surface the owner required Phase H to return before proposing | Alternative recorded only; **no dedicated pause is proposed or selected**. |
| Do not implement automated total-loss resolution | No new surface | Repayment remains available, but unresolved debt can remain stuck after total loss | No caller/griefing exposure; fails Phase F resolution liveness | Safe fallback is no Stock Token listing, not silent manual accounting. |

Reusing `canLiquidate` is technically compatible with the owner's
existing-control preference, but Phase H does not promote it to an approved
design. The owner must decide whether its global liquidation coupling is
acceptable before any Phase I/interface work assumes it.

### 18.8 Total-loss transition caller alternatives

There is no current transition selector, so current source cannot answer who
calls it. Phase H intentionally does not propose or select a caller policy:

| Alternative | Benefit | Risk / required proof |
| --- | --- | --- |
| Permissionless deterministic call | Maximum liveness; no keeper registry or governance wait | Final predicates must leave the caller no discretion over user eligibility, amount, recipient, accounting bucket, or timing-sensitive value. Repayment/transition race is accounting-safe under compare-and-set but timing/griefing acceptability remains a separate security/product question. |
| Restricted existing Department or approved operational actor | Bounds who may choose transaction timing and supports staffed incident coordination without inventing a new role | Creates availability/trust dependence and must identify an existing onchain authority getter. It cannot silently mean “any Ripe department,” and a paused required caller must not strand resolution or repayment. |
| Governance per transition | Strong explicit authorization for each terminal action | Config `TimeLock` makes liveness depend on repeated/jumping `NUMBER`; repayment races and action expiration must be handled. Too slow for an automatic safety path unless the owner accepts that operational model. |
| No callable transition / no listing | Avoids a new caller policy | Leaves Phase F unsatisfied; the safe product result is no listing. |

The later caller decision must be coordinated with the selected gate, event
evidence, repayment-first behavior, duplicate/auction removal semantics, and
the exact `NUMBER` profile. No caller is implied by the phrase “keeper” in
earlier tests or prose.

### 18.9 Share-loss checkpoint control alternatives

An observed share loss must be durably checkpointed to make `Z_recorded` and
quarantine semantics survive later restoration. Existing source has no
standalone checkpoint selector or checkpoint-specific pause.

Existing asset containment is a prerequisite, not checkpoint authorization:
`canDeposit=false` and `canBuyInAuction=false` stop new exposure but neither
permits a caller to change `A^s/U^s`. The alternatives are:

| Alternative | Repayment/property effect | Blast radius / Phase H status |
| --- | --- | --- |
| Require asset containment, then make checkpoint execution consume an existing global gate such as `canLiquidate` | Does not inherently block repayment. Checkpoint timing is property-sensitive because the first durable observation decides whether later restoration is `U`. | Reuses current evidence but couples checkpointing to all liquidation; **not selected**. |
| Pause the affected vault, then allow a later approved checkpoint actor | Vault pause blocks deposits, withdrawals, and internal transfers for every asset in that vault; standard repayment reads can remain available, but exit liveness is reduced. | Existing control but overbroad. It is a containment fallback, not an approved checkpoint gate. |
| Later propose a dedicated checkpoint gate and caller | Could isolate one vault/asset and make event/state requirements explicit | Requires new interface/storage/ABI/default/migration analysis. Recorded only as an alternative; **not proposed or selected**. |
| No durable checkpoint / no listing | Avoids new control and caller surfaces | Cannot guarantee persistent post-zero freeze after restoration; safe result is no listing. |

The total-loss transition and share-loss checkpoint may eventually share one
atomic call or use separate calls. Phase H does not decide that interface.
Whichever path is later proposed must ensure a caller cannot reclassify
donations/restoration, allocate `U`, erase old shares, or choose a loss amount.

### 18.10 Operational evidence model and current getters

Every observation is pinned to one block and one accounting semantics:

```text
Observation O = (
  chainId, blockNumber, blockHash, observedAt,
  registry identities and code/runtime hashes,
  vaultId, vaultAddr, asset,
  C, N, S, A^s, U^s, A, U,
  per-user raw balance/shares and live claim,
  flags and pauses,
  borrowers, debt, liquidation state, auctions,
  lastCleanObservation, firstUnsafeObservation, observationWindow
)
```

The current read map is:

| Required datum | Current read/evidence | Required interpretation |
| --- | --- | --- |
| Live custody `C` | ERC-20 `balanceOf(vaultAddr)` | Raw token base units at the pinned block. Never infer ownership from custody alone. |
| Nominal accounted amount `N` | Simple/Basic `VaultData.totalBalances(asset)` and `userBalances(user,asset)` | Nominal token units. Compare aggregate `N` with `C`; `C<N` is a deficit. |
| Raw shares `S`, `s_u` | Rebase/Shares `VaultData.totalBalances(asset)` and `userBalances(user,asset)` | Raw share units, not tokens, USD, or reward value. |
| Current live claim | `getTotalAmountForUser(user,asset)` and indexed `getUserAssetAndAmountAtIndex` | Current wrapper semantics. For existing SharesVault this derives from all custody and does not expose Phase G quarantine. |
| Current vault total | `getTotalAmountForVault(asset)` | Must be labeled by vault type: nominal accounting for Basic, live custody for Shares. The shared name is not a shared unit. |
| `A^s`, `U^s`, `A`, `U` | No current onchain getters/state implement the Phase G model | Report `null/not implemented`, not a guessed split. Future implementation evidence must use only the owner-approved Phase I surface. |
| Deficit | Basic current: `max(N-C,0)`. Corrected share path: Section 17 model after implementation. | A monitor may detect arithmetic divergence but may not rewrite accounting or infer donation entitlement. |
| General/asset flags | MissionControl `genConfig`, `assetConfig`, `isSupportedAsset`, and operation-specific config getters | Record raw flags plus supported membership and the composed decision; deregistration can leave stale mapping values, so do not collapse unsupported/absent/revert into disabled. |
| Pauses/actors | Target `isPaused`; Alpha/Charlie events; LocalGov and MissionControl actor getters | Record target, caller, event transaction/log index, and post-state. |
| Affected borrowers/debt | Ledger `getNumBorrowers()` plus `borrowers(1..count)`, `userDebt(user)`, and `getNumUserVaults(user)` plus `userVaults(user,1..count)` | Provides onchain iterables for current debtors and their registered vaults. The public `num*` storage uses a one-based next-index convention; the normalized getters return counts. Recompute affected positions from the pinned vault/asset reads. |
| Active auctions | Ledger public `numFungLiqUsers` and `numFungibleAuctions(user)` are one-based next indices: enumerate `fungLiqUsers(1..value-1)` and `fungibleAuctions(user,1..value-1)`, then reconcile `getFungibleAuction` | Record active/paused status, amount left, block bounds, vault/asset, and user debt state. Zero means no iterable. |
| Debt-free depositors | Per-known-user VaultData iterables plus indexed historical deposit/withdraw/transfer events | Current vault storage has no global user enumeration. An event index/operator address set is required; “no affected users” cannot be proven from Ledger borrowers alone. |
| First observed divergence | Consecutive pinned snapshots and token/protocol event history | The exact statement is “first unsafe observation at block X, last clean observation at block Y.” External issuer balance changes may emit token events but no Ripe accounting event; without a prior sample the causal block is unknown. |

`doesVaultHaveAnyFunds()` is a guard diagnostic, not the custody/accounting
snapshot. Current SharesVault semantics can return false for positive custody
with zero shares, as the live Base vault-ID-4 evidence proves. The runbook must
read custody, raw accounting, registration, and the boolean independently.

### 18.11 Repository-side validation/runbook interface

No file is created in this specification-only track. A later implementation
should provide a read-only repository command in the existing `scripts/probes`
family, with a shape equivalent to:

```text
python scripts/probes/stock_token_vault_snapshot.py \
  --chain-id <id> \
  --rpc-url-env <environment-variable-name> \
  --block <number-or-hash> \
  --vault-id <id> \
  --asset <full-address> \
  --known-users <optional-input-file> \
  --output <json-path>
```

This is a repository CLI/output contract, **not** a proposed deployed
interface, dependency, or approved file path. It must:

1. require a pinned block and resolve/record its hash;
2. take RPC secrets only through an environment-variable name and never write
   the endpoint credential;
3. resolve registry addresses and record implementation/runtime identities;
4. emit raw response hex plus decoded values and explicit unit labels;
5. distinguish `unavailable`, `not implemented`, `empty address`, `revert`,
   `unsupported`, and numeric zero;
6. enumerate every onchain borrower and active auction, and state the source
   and completeness limit of any depositor list;
7. accept a prior snapshot and emit `lastClean`, `firstUnsafe`, and an
   observation window without claiming an unobserved causal block;
8. calculate only specified arithmetic such as `C-N`; it may not invent
   `A^s/U^s`, allocate `U`, or infer a beneficiary;
9. perform no transaction simulation that is presented as a live state
   change, no signing, and no broadcast; and
10. exit nonzero on inconsistent block identity, incomplete mandatory reads,
    unit ambiguity, or an unsupported accounting version.

The JSON record must contain at least:

```text
schemaVersion
capturedAt
chainId
blockNumber
blockHash
addressesAndCodeHashes
vaultId
vaultAddress
assetAddress
accountingKind
custody
nominalAccounted
rawTotalShares
allocatedCheckpoint
quarantineCheckpoint
effectiveAllocated
effectiveQuarantine
aggregateDeficit
flags
pauses
authorities
users
debts
auctions
events
lastCleanObservation
firstUnsafeObservation
observationWindow
readFailures
sourceCommit
```

Dynamic values do not belong in a static deployment manifest. A manifest may
declare accounting capability/version and getter semantics; each incident
snapshot owns its pinned dynamic evidence.

Hosted polling, paging, alert delivery, and staffing remain outside Track 8.
Any hosted system consuming this record is read-only. It may alert, compare,
and open a human review, but it may not write balances, mark `U` as anyone's
property, resolve debt, checkpoint loss, migrate, or re-enable a control.

### 18.12 Phase H recommendation and owner-returned decisions

Phase H's recommendation, within the owner's existing-control preference, is:

1. adopt the T8H-01–T8H-12 map and Section 18.6 repayment-safe sequence as the
   control/runbook baseline;
2. use the existing fast general/asset flags for containment and require
   governance-only re-enable with pinned post-state evidence;
3. reject broad Teller/CreditEngine/Ledger pause as the normal loss-resolution
   gate because it blocks repayment;
4. treat reuse of `canLiquidate` as the strongest no-new-state candidate for a
   resolution gate, while returning its global-liquidation coupling for owner
   and security judgment rather than selecting it;
5. make no checkpoint gate or caller recommendation until the owner reviews
   the timing/property alternatives in Sections 18.8–18.9; and
6. keep the operative fallback `do not list`.

At the Phase H handoff, the following decisions were required from the owner
before Phase I or any implementation design:

| Decision | Alternatives requiring owner direction | Current recommendation/status | Required owner/reviewers | Affected surface |
| --- | --- | --- | --- | --- |
| Resolution gate | Accept the global coupling of existing `canLiquidate` / authorize later analysis of a dedicated narrow gate / no listing | Existing `canLiquidate` is the preferred existing-control candidate, **not selected** | Protocol owner + security | MissionControl/Alpha, AuctionHouse, CreditEngine, Ledger |
| Share-loss checkpoint gate | Reuse an existing global gate / tolerate whole-vault pause / authorize later dedicated-gate analysis / no listing | No clean current control; **no gate selected or dedicated pause proposed** | Protocol owner + security/risk | MissionControl/Charlie, share vault, Teller, Lootbox |
| Total-loss caller | Permissionless deterministic / restricted existing actor / governance per transition / no listing | Evidence and tradeoffs returned; **no caller policy proposed or selected** | Protocol owner + security/operations | CreditEngine, Ledger, AuctionHouse, resolution gate |
| Share-loss checkpoint caller | Permissionless deterministic / restricted existing actor / governance per checkpoint / combine atomically with later approved total-loss transition / no listing | Timing affects restoration/quarantine classification; **no caller policy proposed or selected** | Protocol owner + security/risk/operations | Share vault, checkpoint gate, evidence surface |
| Incident withdrawal posture | Preserve safe withdrawals asset-by-asset / freeze affected asset withdrawal when delivery is unsafe / broader freeze | Preserve repayment always and preserve withdrawals when safe; any exit freeze must be explicit and evidenced | Protocol owner + security/operations | MissionControl/Alpha/Charlie, Teller, vault/co-resident assets |

The later owner instruction recorded in Section 12.1 authorized Phase I and
resolved these rows only to the extent stated in Section 19.2: existing
`canLiquidate` baseline, no dedicated checkpoint gate by default, conditional
permissionless total-loss calling, existing Switchboard checkpoint authority,
and safe-withdraw preservation. It did not approve a storage layout,
interface, event, ABI, production vault, implementation, Base migration,
Robinhood registration, or live transaction.

### 18.13 Phase H acceptance and stop boundary

The companion validation plan Section 10 makes this phase testable. Phase H
has completed its authorized specification work because it:

1. maps all twelve required control areas to owner, caller, timing,
   asymmetry, event, getter, defaults, clock behavior, and absence behavior;
2. proves which existing fast controls are repayment-safe and which broad
   pauses are not;
3. identifies the omitted-argument enable defaults that a Robinhood asset
   action must never inherit;
4. defines the required custody/accounting/share/claim/deficit/control/user/
   debt/auction evidence and its enumeration limits;
5. defines first-observed divergence without claiming impossible historical
   knowledge;
6. defines a read-only repository runbook/output contract with no automatic
   accounting or re-enable authority;
7. returned resolution/checkpoint gate and caller alternatives without
   selecting any new state/interface/dedicated pause/caller policy at that
   checkpoint; and
8. preserved the `do not list` fallback and stopped before Phase I until the
   later authorization recorded in Section 12.1.

## 19. Phase I — interfaces, storage, artifacts, and migration

### 19.1 Authorization and compatibility baseline

The owner-authorized Phase I directions are recorded in Section 12.1. This
phase inventories exact consequences and returns choices; it does not create
or approve production code, a storage layout, an interface, an ABI, a
deployment, a migration, or a production vault.

The pinned repository establishes four compatibility facts that constrain
every option:

1. Repository deployment tooling and source model Ripe core Departments and
   vaults as direct deployments. Repository search found no protocol proxy,
   beacon, delegatecall, or in-place implementation-upgrade mechanism for
   Teller, CreditEngine, Ledger, MissionControl, AuctionHouse, or the vaults.
   Section 5 independently pins the two live vault runtimes, but not every core
   address; a future migration must confirm the same direct-runtime fact live
   before relying on it.
2. Vyper modules are compiled into each consuming wrapper. A change to
   `BasicVault`, `SharesVault`, or `VaultData` changes the creation/runtime
   artifacts of every wrapper that composes that module; it is not a separately
   deployable library patch.
3. `Migration.deploy` deploys a fresh contract and writes its address, ABI,
   compiler input, constructor args, and source to the repository manifest
   (`scripts/utils/migration.py:78-88`, `218-235`;
   `scripts/utils/migration_helpers.py:164-184`). It does not itself prove that
   `RipeHq` or `VaultBook` was updated onchain. Registry activation is a
   separate governed/timelocked action.
4. A fresh state-owning deployment starts with fresh storage. Replacing
   Teller or AuctionHouse principally requires address activation, exact pause
   posture, and dependency regression; replacing CreditEngine, Lootbox, or
   Deleverage also requires exact local-config/history reconciliation.
   Replacing Ledger, MissionControl, RipeGov, or a funded vault requires
   explicit state migration. A manifest overwrite is not state migration.

The current manifest declares the following Base addresses. Only the
VaultBook/Simple/Rebase identities and vault runtime hashes were independently
pinned live in Section 5; the remaining rows must be resolved and code-hashed
again at a future migration block.

| Manifest key | Repository-declared Base address |
| --- | --- |
| `Ledger` | `0x365256e322a47Aa2015F6724783F326e9B24fA47` |
| `MissionControl` | `0x559E53F42b68b4995732Dba4aF300796761DBC19` |
| `SwitchboardAlpha` | `0x4bf9025D76FeDd6331661C5de482b0a607D912B9` |
| `SwitchboardBravo` | `0xF3775e9A7880a74644e90A9B22556F8Cee4e0b5B` |
| `SwitchboardCharlie` | `0xA5801c426590F44Bc7d33551Caf7354488C8516C` |
| `VaultBook` | `0xB758e30C14825519b895Fd9928d5d8748A71a944` |
| `SimpleErc20` | `0xf75b566eF80Fde0dEfcC045A4d57b540eb43ddfD` |
| `RebaseErc20` | `0xce2E96C9F6806731914A7b4c3E4aC1F296d98597` |
| `AuctionHouse` | `0x8a02aC4754b72aFBDa4f403ec5DA7C2950164084` |
| `CreditEngine` | `0xEdd0563D06CC52fb5F264A2366A31d9776f6dcC7` |
| `Lootbox` | `0x1f90ef42Da9B41502d2311300E13FAcf70c64be7` |
| `Teller` | `0xae87deB25Bc5030991Aa5E27Cbab38f37a112C13` |
| `Deleverage` | `0x62591b3058c1428FA4b5eD2160387725be285a64` |

The Base vault evidence remains:

- vault ID 3 is the funded nominal `SimpleErc20`, with 9 of 27 assets
  custody-positive at block `49,036,674`;
- vault ID 4 is `RebaseErc20`, with no raw shares but three one-unit custody
  donations that its current funds getter does not report; and
- neither vault runtime is approved unchanged for Stock Token listing.

The integrated S3 record independently pins a later, separate Lootbox
source/live boundary: `origin/rh` now contains S3 source commit `f40dc25` via
merge `3e6e6f2`, while Base ID 16 at block `49,059,353` still resolved the old
21,637-byte runtime with SHA-256
`db139674e84185d013b77211eb769631a9d3c0b5cc45ff90a00e0086095843da`.
S3's new shared creation artifact SHA-256 is
`9246a6d9dbee596750dc3a50d27d4418f318a62b7b4826a13f76aee37621e6ce`;
its deployment, registry/capability transition, Base state-window policy, and
live convergence remain open. Its dated latest-state read before block
`49,059,477` reported rewards enabled, interval `43,200`, deposit reward
`25e18`, yield bonus `150e18`, and `lastUnderscoreSend=49,037,562`; execution
must resnapshot rather than treating those values as current. Track 8 does not
convert that source approval into a deployment approval.

### 19.2 Phase I application of the owner directions

Phase I applies the five directions without expanding them:

- **Resolution gate:** the proposed total-loss resolver consumes existing
  `MissionControl.getGenLiqConfig().canLiquidate`. No dedicated resolution
  gate, MissionControl field, Switchboard setter, default, or migration is
  proposed. Disabling this global flag stops ordinary liquidation and
  total-loss resolution together; the owner accepted that coupling for this
  design analysis. Repayment does not consume the flag.
- **Resolution caller:** the candidate
  `CreditEngine.resolveUserTotalLoss(user)` may be permissionless only if
  `user` is its sole value-relevant caller input and the contract derives the
  full Section 16.8 scan, current debt, amount, auction cleanup, and bad-debt
  destination itself. If gas constraints introduce caller-supplied asset
  lists, amounts, recipients, or partial-selection discretion, permissionless
  authorization no longer applies and the caller decision returns to the
  owner/security reviewer.
- **Checkpoint control:** no dedicated stored checkpoint pause is justified.
  The narrow candidate requires the affected asset's existing
  `canDeposit=false` and `canBuyInAuction=false` containment state before a
  checkpoint can commit. Those flags are safety preconditions, not proof of
  entitlement and not authorization by themselves.
- **Checkpoint caller:** the candidate checkpoint entry is restricted through
  the vault's existing `addys._isSwitchboardAddr(msg.sender)` authority. It
  adds no role mapping or caller parameter. It remains callable while the
  vault is paused so a broad pause cannot prevent durable loss observation.
- **Withdrawals:** no new withdrawal mode is introduced. Existing global and
  per-asset withdrawal controls remain authoritative; corrected vault math
  permits delivery up to the user's live allocated claim. A failed/unsafe
  delivery reverts, and operations may disable only the affected asset through
  the existing flag while preserving repayment.

These are control/caller specifications. The new resolver/checkpoint selectors
and checkpoint storage they would control remain owner-returned compatibility
choices below.

### 19.3 Architecture-impact alternatives

#### Settlement enforcement

Two implementation shapes remain honest:

| Option | Compatibility impact | Phase I assessment |
| --- | --- | --- |
| Make all fungible auction settlement external | Keep the existing Teller/AuctionHouse selectors and `_shouldTransferBalance` argument for ABI compatibility, but reject `true` before collateral movement; no config storage, tuple, setter, getter, default, or migration | **Recommended** because it enforces issuer-controlled external delivery without adding the per-asset parameter the owner prefers to avoid. Requires product confirmation that no existing asset depends on internal auction settlement. |
| Add a generic per-asset external-settlement mode | Append/change `AssetConfig`, MissionControl storage/getters, Bravo/Charlie setter logic, defaults/params, ABIs, and every full-struct reader/writer; migrate all live asset configurations exactly | Technically expressible but high-risk. A direct MissionControl redeployment would require complete configuration migration, and tuple-layout changes create broad ABI/source coupling. **Not recommended by default and not approved.** |

Ignoring `_shouldTransferBalance=true` and silently performing an external
transfer is rejected: a caller could have selected an internal recipient
assumption. The ABI-preserving all-external option must explicitly reject the
unsupported mode.

#### Corrected share boundary

| Option | Compatibility impact | Phase I assessment |
| --- | --- | --- |
| Blanket-modify `SharesVault`/`VaultData` | Changes `RebaseErc20` and `RipeGov` runtimes and risks converting intended positive yield/rebase into quarantine; new state would not appear in already-deployed vaults | Rejected as the default boundary. It silently changes current yield/governance behavior and still cannot migrate live storage in place. |
| New generic vault-level corrected-share variant | Reuse common Addys/Vault conventions and existing Vault selectors; isolate `A^s/U^s`, checkpoint, evidence, and no-positive-delta semantics in a separately deployed generic wrapper/module | **Recommended architecture boundary**, but no file name, storage layout, interface, registry ID, or production vault is selected. This avoids changing existing `RebaseErc20` and `RipeGov` semantics. |
| Add a generic positive-delta mode to the current share wrapper | Requires mode storage/configuration, governance semantics, defaults, getters/events, and migration of current Rebase/RipeGov state | More coupling than a separate generic behavior boundary and conflicts with the preference for existing controls. Not recommended without new evidence. |
| Do not list | No new compatibility surface | Operative fallback if the returned storage/interface/migration choices are rejected. |

The recommended boundary is generic, not Stock-branded: no token name,
issuer, vault ID, or `chain.id` branch. It does not select that variant for
production.

#### Bad-debt transition

Section 16's two-selector design adds no Ledger storage and is the smallest
atomic accounting expression. Phase I nevertheless exposes a major deployment
cost: Ledger is a direct, state-heavy deployment. A new
`moveUserDebtToBadDebt` runtime cannot be activated by swapping an address
without migrating all Ledger state, including user vault indexes, debt,
borrowers, intervals, reward points, auctions, HR/bond state, bad debt, and
pool debt.

The alternatives are:

1. approve the two-selector design plus a separately audited full Ledger
   state migration;
2. redesign the accounting boundary only if another design can perform the
   same user-debt decrement, aggregate-debt decrement, auction cleanup,
   borrower removal, yield booking, and `badDebt += X` atomically without
   giving a second contract unsynchronized write authority; or
3. do not list.

Reusing `setBadDebt` plus a separate CreditEngine debt write remains rejected:
it is a global overwrite, has different authority/timing, and is not atomic.
The two-selector mechanism remains recommended on accounting correctness, but
its Ledger migration and interface are **not approved**.

#### Rewards

Existing Vault selectors can give the corrected variant live user claims and
allocated aggregate value without changing canonical function signatures:
that variant can define `getUserLootBoxShare` as its normalized live-claim
input and `getTotalAmountForVault` as allocated backing `A`. Existing
Rebase/RipeGov wrappers keep their current semantics.

That does not solve lazy interval accrual after a global loss. Untouched users'
persisted `lastBalance` values can otherwise accrue stale weight after the
checkpoint. Integrated Track 6 S3 was reconciled during final Phase I
validation: it governs the minimum Underscore send interval and strict send
boundary, not loss-driven user weighting. The exact Lootbox/Ledger loss epoch,
index, or checkpoint callback therefore remains an **owner-returned Track 8
decision**. Phase I does not invent it.

S3 also creates an integration collision that must not be hidden. Its merged
source changes the Lootbox constructor, immutable runtime data, getter, and
ABI, while its Base forward deployment and distribution-window continuity
policy remain unexecuted/open. Any Track 8 Lootbox change must build on that
integrated source. Deploying S3 first can require a second later Lootbox
cutover; combining a Track 8 loss mechanism with the first S3 deployment would
be a substantive source change that reopens S3 review. The owner must choose
the sequencing after the Track 8 reward interface is selected.

### 19.4 Source, storage, ABI, artifact, and live-impact table

“Fresh deployment” below means creation/runtime bytecode and code hash change,
followed by a governed registry update where applicable. It never means an
in-place upgrade. Every Track 8 delta below is specification-only source
intent: Track 8 changed no production source or live bytecode. Integrated S3
separately changed Lootbox production source and ABI but, per its approved
record, not live Base bytecode. A row that says “reused” means the recommended
Track 8 branch requires no source/runtime change for that surface; a live
address is treated as verified only where Section 5 or the dated integrated
S3 evidence pinned it, otherwise it remains repository-manifest-declared
pending same-block registry/code-hash verification.

| Surface | Proposed or returned delta | Storage/order, function/event/struct compatibility, callers/readers | Artifact/live/migration/rollback consequence | Security/audit boundary |
| --- | --- | --- | --- | --- |
| `BasicVault` (`CM-024` module) | Consume Teller-verified `R`; remove any reliance on aggregate custody as proof of call receipt. Current `min(R,C)` is redundant once Teller proves `0<R<=Q`, and must return exactly `R`. | No storage. Internal signature may remain. Consumed by `SimpleErc20`; Phase E separately reads nominal totals/custody. | Any source edit recompiles `SimpleErc20`; however Release 1 can leave the live wrapper unchanged if tests prove current code returns exact Teller `R`. No vault-state migration solely for this semantic proof. Rollback is the prior Teller/core registry set, not a module swap. | Prove `V==R`, donation isolation, nominal deficit fail-closed behavior, and no direct vault depositor. |
| `SharesVault` (`CM-025` module) | Existing positive-rebase behavior remains for current consumers. Teller `R` is the input; corrected quarantine behavior belongs in the returned generic variant. | Existing `userBalances/totalBalances` remain raw shares. Blanket new `A^s/U^s` storage is not selected. Consumed by `RebaseErc20` and `RipeGov`. | Avoids changing both live wrapper artifacts. Any common-module edit would change both runtimes and require separate migration/compatibility review. | Regression for current yield/rebase and RipeGov; prevent accidental quarantine semantics. |
| `VaultData` | Corrected variant needs funds/deregistration/recovery guards covering raw shares, `A^s`, `U^s`, and custody. Current shared module remains unchanged unless a later design proves universal compatibility. | Current storage order/units unchanged. A variant may reuse enumeration but must override/extend guards rather than reinterpret `totalBalances`. | Blanket edit changes Simple, Rebase, RipeGov, StabilityPool, and other composing artifacts. Recommended variant isolates the new runtime. | Dust, zero-share custody, deregistration, recovery, and VaultBook guard audit. |
| `SimpleErc20` (`CM-024`) | No permanent Stock Token selection. It may remain the Release 1 Base nominal vault only with Teller receipt enforcement plus CreditEngine/AuctionHouse containment. | Existing selectors/events/storage unchanged. Teller, CreditEngine, AuctionHouse, Deleverage, Lootbox, and VaultBook read it. | Section 5 runtime is live and funded. Replacing ID 3 is prohibited until exact migration; core containment can be deployed without moving this storage. Rollback after core activation is unsafe if new deposits/debt used new semantics. | All-user nominal deficit, internal settlement rejection, funded Base regression. |
| `RebaseErc20` (`CM-025`) | Preserve current positive-delta/yield semantics; not selected for Stock Tokens unchanged. | Existing raw-share storage and ABI unchanged. Three live one-unit donations remain migration evidence. | No automatic ID-4 replacement: current funds getter misses custody dust. Any replacement must prove raw custody zero independently. | Positive-rebase regression and literal-custody funds checks. |
| Returned generic corrected-share wrapper/module | Express Section 17 `A^s/U^s/A/U`, persistent freeze, checkpoint, exact rounding, and evidence without Stock-specific branches. | Requires at least per-asset allocated and quarantine checkpoints in fresh storage. Existing Vault selectors remain; specialized additive views/checkpoint/init surfaces are returned in Section 19.5. Readers: Teller, CreditEngine, AuctionHouse, Lootbox, VaultBook, operators/migration tools. | New creation/runtime artifact and new VaultBook registration. Fresh storage requires explicit seeding for any migrated position. No production name/ID or live address exists. Once users/custody are moved, rollback requires reverse migration and cannot be assumed. | New high-risk accounting boundary; full math/property, reentrancy, storage-seeding, recovery, and independent audit. |
| `RipeGov` | Restrict `depositTokensWithLockDuration` to Teller so Phase D cannot be bypassed; otherwise preserve governance-share/reward semantics. | Authorization behavior changes; selector/return/event shapes and persisted governance/share state stay unchanged. Teller is the only production caller found. | Runtime changes and fresh deployment would strand extensive state unless fully migrated. Prefer a minimal separately reviewed replacement only if this authorization hardening is included in an approved release. After any new lock/deposit, rollback requires reverse state/custody migration, not an address flip. | Prove every production lock deposit enters Teller and governance points/locks are unchanged. |
| `StabVault` module / `StabilityPool` wrapper | Ordinary and collateral-claim auto-deposits consume measured `R`; RIPE reward stake requires exact `R==Q`. Current Stability Pool economic/share formulas otherwise remain unchanged. | Source change to the composed module recompiles the wrapper. Existing Vault selectors/events and `VaultData` raw-share units remain. Persistent state includes all vault user/asset shares/enumeration/pause plus claimable balances/assets and literal custody. | Fresh StabilityPool runtime cannot replace the live wrapper without full custody, user/share, enumeration, claimable-balance, claimable-asset, and pause-state migration. This is a shared-protocol migration caused by Phase D caller exactness, even though Stock Tokens never route through the Stability Pool. After a new share/claim write, rollback is the inverse state/custody migration. | Legitimate Teller callback/reentrancy, measured versus exact paths, complete state/custody roots, claim conservation, reward-claim atomicity, and existing Stability Pool regression. |
| `BondRoom` | Capture Teller's returned RIPE stake and require equality with the bond payout before accounting completes. | Existing selector/event shapes remain. Preserve `bondBooster`, Department pause, immutable constructor posture, and Ledger-owned bond/bad-debt epoch state. | Fresh runtime requires exact local config/pause reproduction and atomic compatibility with the Ledger state; it must not reset a customized booster or detach a payout from its stake credit. After a new payout/bad-debt write, rollback requires Ledger plus stake reconciliation. | Payout/stake atomicity, booster parity, bad-debt-clearing conservation, and callback behavior. |
| `HumanResources` | Capture Teller's returned RIPE stake and require equality with compensation amount. | Existing selector/event shapes remain. Preserve exported LocalGov/TimeLock state, all pending contributor actions, Department pause, immutable constructor posture, and Ledger-owned contributor/reward state. | Fresh runtime requires complete local governance/timelock/pending-action migration plus Ledger reconciliation; omission can lose a pending contributor action or change its confirmation window. After a contributor/stake write, rollback requires reverse local/Ledger reconciliation. | Compensation/stake atomicity, governance authority, pending-action clocks, contributor enumeration/state, and repayment-independent liveness. |
| `CreditRedeem` (`CM-043`) | Capture and require exact Teller sGREEN deposit return. Stock `canRedeemCollateral=false` and unsupported routes remain mandatory. | No new storage or public selector/event shape. Preserve Department pause and immutable constructor posture. | Fresh runtime/ABI only if included in the Phase D atomic caller update; reproduce pause/constructor state before RipeHq activation. Before a new-path transaction an address revert is possible; afterward external mint/deposit/redemption effects must reconcile. No redemption path is permission to list Stock collateral. | Mint/deposit/redemption atomicity, disabled Stock route, receiver restrictions, and shared existing-asset regression. |
| `Teller` (`CM-034`) | Measure `C0/C1`, enforce `R`, recheck `C2/C3`, hold a global deposit-specific mutex, emit `TellerDepositMeasured`, and return `R`. | Use a transaction-local `transient(bool)` mutex candidate, not persistent storage, so no stale lock survives. Existing deposit selectors/returns/events remain; one additive event. Every Section 14.7 producer/caller is affected. Persistent state is the composed Department pause; the RipeHq address and mint permissions are immutable constructor state. | Fresh Teller creation/runtime and ABI. Reproduce the reviewed pause/constructor posture and activate through RipeHq only after all exact-receipt callers are compatible. Existing Teller rollback is unsafe after downstream code assumes the new event/return exactness. | Callback/reentrancy, token delta, housekeeping liveness, consumer exactness, gas, constructor/pause parity, and all entry-point inventory. |
| `TellerUtils` (`CM-045`) | Keep pre-transfer limits/validation. Final minimum is rechecked by Teller from credited live state. | No storage, struct, selector, event, or ABI change required. Teller remains sole caller. | Reused runtime if integrated source confirms no helper change. No migration. | Preview/final-limit equivalence and no optimistic minimum. |
| `CreditEngine` (`CM-030`) | Phase E backing/capacity-resolution split; non-raising repayment refresh; total-loss eligibility entry; call Ledger atomic transition. | No new persistent state proposed. Existing `undyVaulDiscount`, `buybackRatio`, and Department pause retain their exact units/values; public views keep signatures. Candidate additive `resolveUserTotalLoss(user)` and event; internal MissionControl/Vault/Ledger interfaces change. All borrow/health/withdraw/liquidation/repay consumers read changed semantics. | Fresh runtime/ABI and RipeHq address activation. Read and reproduce both live configuration values plus pause/constructor posture before cutover; defaults are not evidence of live values. Existing debt remains in Ledger. Address rollback is technically possible only before behavior-dependent transactions; after resolution writes it is not a semantic rollback. | Hot-path staticcall/gas, price-independent deficits, repayment liveness, deterministic caller, CAS race, config parity, and full consumer audit. |
| `Ledger` (`CM-008`) | Candidate CreditEngine-only `moveUserDebtToBadDebt` performs Section 16.9 atomically and additively emits loss-transition evidence. | **No new storage slot or unit change**, but one selector/event changes runtime/ABI. It writes existing user debt, total debt, borrowers, auctions, unrealized yield, and bad debt. Every existing Ledger mapping/aggregate plus Department pause and immutable constructor posture retains its exact unit/value. CreditEngine is sole transition caller; Switchboard `setBadDebt` remains an audited reconciliation tool. | Fresh direct deployment would start empty; full state migration is mandatory before RipeHq activation. Partial Ledger migration is forbidden. Rollback after either new Ledger writes or address activation is a full reverse-state migration, not an address flip. | Highest-risk shared accounting/audit boundary: every Ledger mapping/aggregate, pause/constructor parity, yield double-booking rationale, auction removal, exact snapshot, and total equality. |
| `AuctionHouse` (`CM-026`) | Re-read allocable custody; settle on measured `E`; prevent zero-backed auctions; enforce external-only issuer policy through one returned mechanism. | No persistent storage addition required. Existing buy selectors can remain. All-external option rejects `_shouldTransferBalance=true`; per-asset option would add config coupling. Current working caches are transient; persistent composed state is the Department pause/immutable constructor posture. Events retain existing fields plus additive delivery evidence if needed. | Fresh runtime/ABI; reproduce pause/constructor posture before RipeHq activation. Active auctions live in Ledger and must be reconciled before cutover. Rolling back can reopen internal settlement or stale auction semantics and is unsafe after new purchases. | Two-buyer ordering, payment/delivery atomicity, active auction cutover, discount/clock regression, pause parity, external-mode compatibility. |
| `AuctionHouseNFT` (`CM-027`) | No delta. The current stub has no settlement entry or common Vault consumer and is inapplicable to fungible Stock Tokens. | No storage, selector, event, caller, or reader change. A future implementation must re-enter the consumer inventory rather than inherit this disposition. | Artifact reused unchanged; no live migration consequence from Track 8. | Tripwire that a future NFT settlement path cannot silently consume changed vault semantics. |
| `Deleverage` (`CM-044`) | Price/repay only measured external receipt `E`; capture and assert exact Teller replacement-deposit return. Stock Token forbidden routes remain disabled. | No new storage or public selector required. Existing `minDeleverageBps`, `deleverageBuffer`, `deleverageCooldown`, `underscoreSafeSpreadBps`, per-user `lastDeleverageBlock`, and Department pause retain exact units/semantics; working caches are transient. Existing events must report measured amounts. Readers/callers: Teller, AuctionHouse, CreditEngine, PriceDesk. | Fresh runtime and RipeHq activation. Preserve integrated Track 6 source plus every live config value and cooldown history, or use an owner/security-approved conservative disable-and-wait cutover that cannot shorten any user's remaining cooldown. A reset-to-zero map is unsafe; rollback after a new swap/cooldown write requires downstream debt/custody plus last-block reconciliation. | Recipient-delta measurement, exact replacement deposit, cooldown state/cutover composition, zero delivery, routing prohibitions. |
| `Lootbox` (`CM-033`) | Build on integrated S3; consume live-claim user weight and allocated aggregate value for the corrected variant; close the separate reward interval at loss checkpoint. | Preserve S3's immutable `MIN_UNDERSCORE_SEND_INTERVAL`, five-argument constructor order, `minUnderscoreSendInterval()` ABI, strict send boundary, and existing Vault selector shapes. Current local state—Underscore enablement, send interval, last send, deposit/yield reward amounts, and pause—must be explicitly reconciled. Config/permission values are preserved; `lastUnderscoreSend` follows S3's still-open final-distribution/partial-window/continuity decision rather than silently resetting. No Track 8 epoch/index/callback storage or selector is selected. | Integrated source/ABI are S3-new while live Base is still the dated old runtime. Any Track 8 artifact must compile from the integrated S3 baseline and either sequence after S3's governed cutover or reopen S3 review as a combined artifact. Apply the owner-selected S3 window policy and reconcile Ledger-owned user/global points. Rollback after distribution or point accrual is not lossless. | Economic-unit labeling, untouched-user accrual, global conservation, S3 floor/constructor/getter and approved per-chain immutable values, pending S3 distribution window, Track 8 loss-interval choice, RipeGov exception. |
| `MissionControl` (`CM-009`) | Reuse current `canDeposit`, `DebtTerms.ltv`, `canLiquidate`, `canBuyInAuction`, and `canWithdraw`. No collateral-use or checkpoint field. Per-asset settlement mode remains the nonpreferred alternative. | Recommended path: no storage/tuple/selector/event change. Per-asset mode would require a new full-struct field and every getter/caller/writer to consume the same version. | Recommended path reuses live runtime/config. Per-asset mode requires fresh MissionControl plus complete general/asset/user/reward/debt configuration, enumeration, pause, and constructor-state migration plus new ABI/defaults. Rollback risks tuple/version mismatch. | Exact full-config round trip, no default drift, pause/constructor parity, and live-config hash/reconciliation. |
| `ConfigStructs` | Preserve `AssetConfig` and every current struct layout on the recommended path. | No source/ABI tuple change. The nonpreferred per-asset settlement mode would change the struct and every full-struct encoder/decoder, Switchboard action, default, and migration fixture. | Reused by every importing compilation. Any later struct edit changes all consuming creation/runtime artifacts even though the interface source owns no runtime state. | Repository-wide compiler inventory, tuple encoding, mixed-version rejection, and generated ABI/schema review. |
| `SwitchboardAlpha` (`CM-011`) | Existing `setCanLiquidate`, general borrow/repay/withdraw flags retained; no dedicated resolver setter. | No storage/interface/event change. `CanLiquidateSet` remains evidence; lite disable/governance enable behavior retained. | Reused runtime under recommended path. No migration. | Global coupling, disable/re-enable authority, repayment independence. |
| `SwitchboardBravo` (`CM-012`) | Debt terms remain unchanged. It changes only if an owner later selects a governed per-asset settlement field. | Recommended path: no change. Alternative would need pending-action storage, validation, event, MissionControl tuple handling. | Reuse under recommended path; alternative fresh runtime/config migration. | Pending-action clocks, full-struct preservation, zero-LTV guard regression. |
| `SwitchboardCharlie` (`CM-013`) | Existing fast per-asset deposit/withdraw/auction flags are checkpoint containment prerequisites; no new role mapping or dedicated gate. | No storage/interface/event change. Existing Switchboard membership authorizes the candidate vault checkpoint; existing events prove prerequisite flags. | Reused runtime. No migration. | Lite-action authority, asset identity, safe-withdraw posture, missing MissionControl failure. |
| Canonical `Vault.vyi` | Preserve existing selectors/returns for deposits, withdrawals, transfers, live user amount, reward input, total amount, enumeration, and funds check. | Do **not** force every Vault implementation to add corrected-share methods. A specialized additive interface is the narrower returned option. Existing consumers keep compiling against canonical Vault. | Canonical ABI unchanged on recommended boundary; new variant has a superset runtime/ABI. | Cross-vault semantic labels, consumer dispatch, no hardcoded vault ID/type confusion. |
| Other internal interfaces (contract-local `Teller`, `CreditEngine`, `Ledger`, `AuctionHouse`, and `MissionControl` declarations plus any specialized corrected-vault interface) | Add only the approved CreditEngine→Ledger selector declarations; update local MissionControl/Vault declarations only where existing selectors are consumed. The nonpreferred settlement-mode alternative expands Auction/Teller config tuples. | Additive local declarations do not create storage but must match deployed selectors. Canonical `interfaces/Vault.vyi` stays unchanged; a corrected-variant interface would be a separate superset. All callers named above require compile-time and runtime checks. | Every contract containing a changed local declaration must be recompiled; generated ABI changes only for externally exposed selectors/events. No interface file changes in Track 8. | Selector collision, return tuple encoding, caller authorization, mixed runtime/interface version skew. |
| `VaultBook` + AddressRegistry (`CM-021`) | Reuse governed add/update/disable. Corrected vault should receive a new Track 7-owned ID; do not replace funded ID 3/4 casually. | No storage/interface change proposed. Current funds check is insufficient for ID-4 dust; migration uses explicit custody/share checks in addition. | Reuse runtime. New address registration is timelocked and manifest-tracked. Address rollback does not move custody/state and is unsafe after users are seeded at a new ID. | `NUMBER` timelock, funds-check semantics, concurrent registry actions, new/old validity. |
| Defaults/parameter generation (`CM-007`, `CM-049`) | Recommended path adds no parameter. Keep Stock `canDeposit`, `canRedeemCollateral`, Stability Pool, and auction/borrow defaults disabled until release gates. | No `AssetConfig` tuple/default change under recommended path. Robinhood defaults remain pending Track 7; Track 8 invents no file/ID/value. | Rebuild only if a later owner selects a new parameter. Base/RH value manifests must be explicit and schema-identical. | Omitted-argument enable traps, chain profile parity, unsupported integration assertions. |
| ABIs and events | Preserve existing selectors/events where specified; the future baseline includes integrated S3's five-argument Lootbox constructor and floor getter. Add only Teller measurement, CreditEngine/Ledger transition, and corrected-variant checkpoint/state evidence after approval. | Additive events/selectors still change ABI consumers. Candidate fields/units are defined in Sections 14, 16, 17, and 19.5; no Track 8 artifact may regress the integrated S3 ABI. | `scripts/export_abis.py` would regenerate production ABIs only after implementation; no ABI file changes in Track 8. S3's separately integrated `Lootbox.json` is source evidence, not a Track 8 edit. Pin creation/runtime hashes in manifests. | Indexed-field continuity, units, exact event ordering, S3 ABI continuity, offchain decoder/version compatibility. |
| Base/RH migrations and manifests | Track 8 supplies sequencing, state roots, stop/rollback conditions; Track 7 owns IDs/namespaces/files/tooling. | No migration source or manifest change now. Every artifact records compiler input, constructor args, ABI, creation/runtime hashes, chain, registry ID/address, accounting capability/version. | Base containment and permanent-vault migration are separate gates. RH must deploy only the same approved shared source artifact. `pending Track 7` remains until reservations integrate. | Dry run, fork, dual-chain identical-artifact proof, signer/role/timelock review, partial-failure recovery. |
| Post-deployment verification | Reconcile code identity, registry identity, flags, custody, nominal/shares, `A^s/U^s/A/U`, users, debt, auctions, points, and events. | Read-only; no dynamic balance belongs in static manifest. Consumers must declare getter units/version. | Required before any enable. Failure leaves asset disabled and old address retained for audit/exit; it does not trigger automated rewrite or rollback. | Independent reviewer, same-block snapshots, roots/totals, exact-token fork, Base regression, incident rehearsal. |

### 19.5 Returned storage and interface contracts

This subsection is deliberately exact enough for owner/security comparison
without treating either proposal as approved.

#### Corrected share state

The minimum persistent economic state is:

```text
allocatedCheckpoint[asset]   # A^s, token base units
quarantineCheckpoint[asset]  # U^s, token base units
```

Existing `VaultData.userBalances` and `totalBalances` remain raw user/aggregate
shares. No separate post-zero boolean is needed: `S>0 && A^s==0` is the
persistent recorded freeze. No per-asset collateral-use flag, positive-delta
mode, recovery recipient, or ownership field is included.

For a fresh generic variant, source-declaration order must preserve the chosen
module composition and place the two mappings after the reused share/enumeration
state in the compiled storage layout. Because there is no in-place proxy,
“append” is a review discipline for compiler/storage proofs and migration
tools, not permission to write those slots into `RebaseErc20` live storage.

The minimum specialized interface candidate is:

```text
checkpointShareAsset(asset)
    -> (allocatedCheckpoint, quarantineCheckpoint)

getShareAssetState(asset)
    -> (rawShares, liveCustody, allocatedCheckpoint,
        quarantineCheckpoint, effectiveAllocated, effectiveQuarantine)

getUserShareState(user, asset)
    -> (rawShares, liveClaim, rewardWeight)
```

`checkpointShareAsset` has no caller-supplied amounts or allocation. It
requires existing asset containment and Switchboard authority, recomputes from
current custody, applies Section 17 loss-first ordering, records `A^s/U^s`,
and emits previous/new buckets, custody, caller, and zero predicates. Views are
unit-labeled and revert/fail closed on malformed token reads.

The exact names, tuple shape, event name, interface file, and storage
declarations are **returned, not selected**. Canonical `Vault.vyi` remains
unchanged under the recommended boundary.

#### Total-loss transition

The minimum candidate remains:

```text
CreditEngine.resolveUserTotalLoss(user) -> transitionedAmount

Ledger.moveUserDebtToBadDebt(
    user,
    expectedStoredAmount,
    expectedLastTimestamp,
    finalDebtAmount,
    accruedInterest,
) -> transitionedAmount
```

The external CreditEngine call consumes existing `canLiquidate`, takes no
amount/asset/recipient list, derives all eligibility, and is permissionless
only under that exact no-discretion property. The Ledger call is
CreditEngine-only and writes existing fields atomically. Neither selector adds
storage, but the Ledger runtime change still requires the full migration
described above.

#### Migration-only import

A fresh corrected vault cannot inherit user shares or enumerations. Migration
therefore needs either:

1. a one-time, paused-state batch import surface plus an irreversible
   `finalizeMigration`, with a sealed migration authority/state; or
2. another audited deployment/constructor mechanism that seeds the same user,
   asset, raw-share, `A^s`, and `U^s` state before registration.

Ordinary deposit replay is not equivalent: order and rounding can change
shares, the old vault owns custody, and pre-existing `U` must not be allocated.
No import selector, migration-authority slot, constructor scheme, or finalizer
is selected. This is a mandatory returned interface/storage decision if any
live positions are migrated. Empty, unreachable Robinhood staging can avoid
user-state import, but it is not launch evidence and does not solve Base ID-3
custody migration.

### 19.6 Vault migration sequence and stop conditions

Track 7 owns exact migration identifiers, namespaces, filenames, manifests,
and deployment tooling. Every Track 8 reference remains **pending Track 7**;
no Track 8 ID is reserved or invented here. The integrated S3 record names
`0010_Track6S3LootboxFloor.py` only as an S3-owned predeployment artifact
assertion; Track 8 may neither reuse it nor treat the absent future file as an
executed migration.

The required per-chain sequence is:

1. **Pin authority and identity.** Record chain ID, block/`NUMBER`, timestamp,
   `RipeHq`/`VaultBook` addresses, resolved old vault/core addresses, runtime
   hashes, governance/Switchboard/lite actors, all relevant pending actions,
   and every affected Department's pause, constructor/immutable posture, local
   config, and cooldown/timing state.
2. **Disable deposits to the old vault and contain new exposure.** Set every
   affected asset's `canDeposit=false`, keep the replacement inactive, and
   verify no Teller/config/registry route can credit the old address. Disable
   general borrow if blast radius is uncertain and set
   `canBuyInAuction=false`. Keep `canRepay=true`. Preserve withdrawals only
   where exact delivery is safe.
3. **Enumerate candidates.** Build the user/asset set from all historical
   deposit/withdraw/transfer events, Ledger user-vault participation,
   borrowers, and active auctions. Vault storage has per-user/per-asset
   enumeration but no global depositor list, so event-derived enumeration must
   be reconciled rather than assumed complete.
4. **Pin the old-state reconciliation.** For each asset record custody,
   nominal totals or raw total shares, every user balance/share/live claim,
   prices separately, reward checkpoints, debt, and auctions. Require sums and
   indexes to reconcile. A failed token read is a stop, not zero.
5. **Reconcile debt and auctions before movement.** Nominal `C<T`, positive
   custody with unresolved ownership, debt/claim mismatch, or an unenumerated
   auction blocks migration. Phase I does not allocate a nominal partial loss.
   Total-loss debt uses the separately approved transition only; it is not
   manufactured as a migration shortcut.
6. **Close active economic intervals.** Settle or pause/cancel every affected
   auction without payment for undelivered collateral. Close Lootbox intervals
   under the separately owner-approved Track 8 loss-interval mechanism while
   preserving integrated S3's send-floor and strict-distribution behavior.
   Until that mechanism exists, a reward-bearing migration remains blocked.
   Repayment stays open.
7. **Deploy inactive artifacts.** Deploy reviewed core/vault contracts with
   exact constructor state, leave the corrected vault paused/unregistered or
   otherwise unreachable for deposits, record creation/runtime hashes, and
   verify source. Deployment alone does not activate a registry entry.
8. **Seed and move per asset.** Use the separately approved migration surface
   to move exact custody and recreate exact user raw-share/claim entitlement,
   `A^s/U^s`, enumeration, and Ledger participation. A nominal source can be
   converted only from an owner-approved, fully backed entitlement snapshot.
   Checkpoint reward state before and after each user/asset move.
9. **Handle partial transaction failure.** Each transaction must be
   internally atomic and idempotently recorded, but a multi-user migration
   cannot be called globally atomic across mined transactions. During the
   batch window neither old nor new position may support new borrow/auction
   capacity twice. A failed batch leaves both vaults contained and resumes
   from proven state; it never enables the partially migrated asset.
10. **Reconcile before registry/config activation.** Prove old plus new custody
    equals the expected start minus measured external delivery; prove no user
    duplication/omission, exact aggregate shares/claims/buckets, Ledger
    participation, debt, auction, and reward roots, literal custody for every
    registered asset, and exact affected-core local config/pause/timing roots.
11. **Activate through Track 7-owned actions.** Register the new generic vault
    under a new reserved VaultBook ID unless the owner later approves a
    fully-empty replacement. Update asset-to-vault configuration only after
    timelock/role/`NUMBER` validation. New permissions begin disabled.
12. **Retire the old address.** Require every old user raw balance/share zero,
    accounted aggregate zero, literal custody zero, no active auction, no
    Ledger participation, and no reward residue. Deregister assets/users only
    after those checks. ID-4's current boolean alone is insufficient.
13. **Post-migration reconcile and soak.** Repeat all roots, totals, code
    hashes, flags, getter units, exact-token behavior, debt health, repayment,
    auctions, and reward evidence. Keep Stock deposits/borrowing/auction
    purchases disabled until the later release/audit gates.

Bulk `recoverFunds` is not a migration tool for registered/funded assets.
VaultBook address replacement does not move custody or storage. An old-address
disable does not clean user Ledger participation. All three shortcuts are
rejected.

Rollback reality is phase-dependent:

- before registry/config activation and before custody/state seeding, discard
  the inactive deployment;
- after some migration batches, resume forward or execute an independently
  specified reverse migration while both sides stay disabled;
- after new borrowing, settlement, reward accrual, or a bad-debt transition,
  an address flip cannot restore prior economics; recovery requires a new
  reconciled state transition and owner approval; and
- an issuer transfer freeze/blocklist can prevent both forward and reverse
  custody movement. Operations must treat that as a stop, not as permission to
  rewrite claims.

### 19.7 Base and Robinhood version posture

The recommended live-version posture is:

1. use one canonical reviewed source, compiler input, constructor schema, and
   creation artifact for shared core changes, with every chain-specific
   constructor argument explicit;
2. harden Base before or atomically with Robinhood **enablement**, not after
   RH lists an asset against safer semantics. A pre-convergence artifact may
   exist only as unreachable, empty, time-bounded staging with an explicit
   abort owner and cannot be reported as deployment completion or launch;
3. allow only a documented, time-bounded divergence during governed registry
   cutover, with the unsafe side contained and an expiry/abort condition; and
4. do not accept permanent Base/RH logic divergence merely to avoid migrating
   live Base state. Deployed runtime hashes may differ only where the reviewed
   shared source embeds approved immutable constructor values, as S3 does for
   RipeHq and `MIN_UNDERSCORE_SEND_INTERVAL`; manifests must reproduce and
   explain that difference byte-for-byte.

S3's owner-approved bounded temporary source/live drift is scoped to that
Lootbox-floor rollout and still lacks its recorded rollout owner, deadline,
maximum state, and distribution-window decision. It does not authorize a
Track 8 migration, permanent Base/RH version skew, or an additional Track 8
Lootbox delta.

Release 1 Base containment can avoid moving funded `SimpleErc20` ID 3 if its
nominal state remains fully reconciled, but it is not a three-contract
“core-only” swap. Teller receipt semantics must compose with every Section
14.7 consumer: measured RipeGov and StabilityPool paths; exact
StabilityPool, BondRoom, Lootbox, HumanResources, CreditEngine, CreditRedeem,
and Deleverage paths; plus AuctionHouse settlement and CreditEngine
backing/repayment changes. Several of those artifacts own live state, so the
cutover needs the row-specific migration or state-preserving procedure in
Section 19.4. Mixed old/new versions may exist only while every affected value
path is contained; repayment must remain live. This is not a permanent Stock
Token vault approval. It avoids the ID-3 custody move but still requires exact
registry/config sequencing, full regression, state reconciliation, and owner
approval.

Release 2 corrected-share adoption is a separate custody-bearing migration.
Base ID 3 cannot be replaced casually, and ID 4's three dust units must be
handled even though its current funds getter is false. Robinhood must use only
a Track 7-reserved ID and manifest after the production vault and exact-token
gates are approved.

Base-first or atomic convergence before RH enablement is owner-directed for
Phase J validation. The exact migration/cutover, any inactive staging, and
every live action remain unapproved.

### 19.8 Post-deployment evidence contract

Before any enablement, one pinned evidence bundle per chain must include:

```text
chainId
blockNumber
blockHash
timestamp
sourceCommit
migrationCommit
manifestPathAndHash
registryIdsAndResolvedAddresses
creationAndRuntimeCodeHashes
constructorArgs
storageOrStateMigrationRoot
coreLocalConfigPauseAndCooldownRoots
oldAndNewUserAssetRoots
custodyNominalShareAllocatedQuarantineTotals
debtBorrowerAuctionRewardRoots
controlValuesAndPendingActions
exactTokenProxyBeaconImplementationHashes
testAndAuditArtifactHashes
```

Required assertions:

- Base and Robinhood shared components match the approved source/compiler/
  constructor-schema/creation commitment; each deployed runtime matches its
  approved chain-specific constructor arguments, with any immutable-derived
  hash difference reproduced byte-for-byte and any other difference treated
  as version skew;
- every enabled asset resolves to the intended vault and getter semantics;
- every replaced Department reproduces its reviewed immutable, pause, local
  configuration, pending-action, and cooldown/timing state;
- `sum(user claims) <= A <= C`, `U=C-A`, and no `U` contributes to debt,
  settlement, or rewards;
- no old and new position are simultaneously credit-eligible;
- repayment works under every containment state;
- issuer-controlled settlement cannot choose internal mode;
- duplicate total-loss transition cannot add bad debt twice;
- old addresses cannot receive deposits and hold no unreported custody before
  retirement; and
- unsupported Stock Token routes remain disabled.

The evidence is read-only. A failed assertion keeps the asset disabled and
requires owner/security review; it cannot auto-repair balances or re-enable a
flag.

### 19.9 Owner-returned decisions after Phase I

Phase I returned the following decisions. Phase J now binds validation targets
and prerequisites without converting them into production approvals:

| Decision | Alternatives | Recommendation and evidence | Required owner/reviewers | Needed before | Status |
| --- | --- | --- | --- | --- | --- |
| Fungible settlement enforcement | Reject internal mode for all fungible auctions / add per-asset settlement mode / do not list | Prefer all-external: preserves tuple/storage/default schemas and avoids MissionControl migration. Phase J requires complete current integration plus historical calldata/product-consumer evidence; source defaults alone are insufficient. | Product + protocol + security | Phase F implementation design | **Preferred Phase J validation branch; no behavior/config change approved** |
| Corrected share implementation boundary | New generic vault-level variant / blanket shared-module change / generic mode / do not list | Use the isolated generic variant as the Phase J target to preserve Rebase/RipeGov positive-delta semantics | Protocol + security + economics | Storage/interface design and vault selection | **Phase J validation target; no file/layout/interface/vault approved** |
| Corrected share storage/interface | Two bucket mappings plus specialized checkpoint/views and one-time migration import / another audited equivalent / do not list | Test the minimum `A^s/U^s` model while keeping canonical Vault unchanged. Migration-import authority/finalization is a separate high-risk decision and is unnecessary for empty inactive staging. | Protocol + security + counsel/risk | Any Phase G implementation or live migration | **Phase J validation target; new storage/selectors/import not approved** |
| Atomic bad-debt interface and Ledger migration | Two-selector design plus full Ledger state migration / another atomic boundary / do not list | Model the two-selector atomic transition for correctness; keep the direct, full-state Ledger migration as an inseparable but separately unapproved gate | Protocol + accounting + security + operations | Phase F implementation design | **Phase J validation target; selector/event/implementation/Ledger migration not approved** |
| Reward loss-interval integration and S3 sequencing | Add a reviewed loss epoch/index or checkpoint callback on top of integrated S3 / defer Stock rewards or listing / do not list; deploy S3 first versus reopen S3 review for a combined artifact; preserve S3's separate final-distribution/partial-window/continuity choice | Preserve S3 independently if Track 8 would delay it. A combined cutover is eligible only if Track 8 is ready without reopening/delaying required S3 safety; otherwise Stock deposits/rewards remain disabled and a second explicit migration is required. | Economics + Track 6 owner + protocol/security + operations | Lootbox/Ledger interface and S3/Base rollout selection | **Sequencing constraint owner-directed for Phase J; loss mechanism and both migrations/window policies remain unapproved** |
| Base live-version and migration posture | Base first / atomic convergence / no release | Require Base first or atomic convergence before RH enablement. Any inactive pre-enable staging remains unreachable, time-bounded, and explicitly not launch; avoiding the ID-3 move does not avoid stateful shared-caller/core cutovers. | Protocol + security + operations | Implementation/release authorization | **Owner-directed Phase J validation/release posture; no live action or migration approved** |
| Production vault and VaultBook ID | New generic corrected vault / another approved generic vault / none | No selection until storage/interface, reward loss-interval/S3 sequencing, exact-token, audit, and migration gates close; Track 7 owns any ID | Product + protocol + risk/security | Robinhood asset registration | **Deferred; do not list remains operative** |

The earlier Phase I control directions are not reopened: existing
`canLiquidate` is the baseline resolution gate, total-loss calling is
permissionless only under a deterministic no-discretion selector, the
checkpoint caller is an existing Switchboard actor, containment flags are
checkpoint preconditions, and safe withdrawals remain available. What remains
unapproved is the new machinery those policies would invoke.

### 19.10 Phase I acceptance and stop boundary

Phase I is specification-complete with companion validation-plan Section 11
because it:

1. covers every component required by the task contract and every additional
   actual caller/reader;
2. states storage order, function/event/struct compatibility, callers,
   artifacts, Base live impact, source/live status, migration prerequisite,
   rollback limitation, and audit boundary for every proposed delta;
3. proves why stateful direct-deployment Department, Ledger, MissionControl,
   and vault changes require exact state cutover/migration rather than
   ordinary upgrades;
4. distinguishes Base Release 1 shared containment/caller cutover from
   Release 2 custody-bearing corrected-vault migration;
5. specifies old-vault disablement, user/asset enumeration, live funds,
   debt/auction/reward handling, raw state cleanup, custody/state movement,
   partial failure, retirement, permissions, and post-state reconciliation;
6. records all exact migration IDs/namespaces/manifests/tooling as
   `pending Track 7`;
7. reconciles integrated S3 without claiming it supplies Track 8 loss
   weighting or is live, and returns rather than selects the settlement, share
   storage/interface, Ledger migration, reward/S3 sequencing, live-version,
   and production-vault choices; and
8. stops before Phase J and leaves the operative posture `do not list`.

## 20. Phase J — complete validation specification

### 20.1 Authorization and decision-bound branches

The exact Phase J authorization and its non-approvals are recorded in Section
12.1. The companion validation plan now treats:

- all-external fungible settlement as the preferred branch, but makes complete
  current-integration and historical-use evidence a prerequisite rather than
  inferring compatibility from Teller's default argument;
- an isolated generic corrected-share variant and the `A^s/U^s` model as
  validation targets without selecting a file, layout, selector, ABI,
  migration import, vault, or ID;
- the two-selector bad-debt transition as the atomic accounting target without
  approving either selector, its event, implementation, or the full Ledger
  migration;
- integrated S3 as an independent safety release if Track 8 would delay it,
  while keeping Stock rewards and any loss-interval/index/callback unapproved;
- Base-first or atomic convergence as a future RH-enablement gate without
  authorizing a Base migration; and
- any empty gated deployment as inactive staging only. It cannot satisfy a
  listing, launch, vault-selection, reward, migration, or production-behavior
  gate.

The per-asset settlement-mode, blanket shared-module, generic positive-delta
mode, alternative atomic transition, migration-import, reward mechanism, and
`do not list` branches remain explicitly testable alternatives or fallbacks.
They are not silently deleted by choosing preferred validation targets.

### 20.2 Coverage contract

Companion validation-plan Sections 1–16 provide:

1. the unchanged 90-case current-behavior baseline;
2. proposed paths and reusable fixture boundaries;
3. an I-01–I-13 invariant map;
4. the complete sixteen-state matrix;
5. architecture and standing-configuration matrices;
6. Phase D–I behavior, control, compatibility, artifact, and migration tests;
7. the pinned AAPL exact-token fork plan;
8. integrated S1/S2 repeated/ordinary/jump clock and checked-inventory
   commands, with S3 preserved separately;
9. migration, diagnostics, evidence, and execution tiers; and
10. review and launch gates.

Validation-plan Sections 17–18 record the Phase J authorization and normalize
every named future assertion as the union of its case row plus one explicit
profile. The profile supplies the proposed file, stable components,
prerequisite, actors and token behavior, expected transition class,
invariant/control obligation, clock profile, diagnostics, runtime tier, and
reviewers. A future test is not accepted if any field is absent, inherited
from more than one conflicting profile, or silently relaxed by a fixture.

### 20.3 Phase J acceptance and stop boundary

Phase J is specification-complete when the two documents validate as a pair
and the companion plan proves:

- every I-01–I-13 invariant and all sixteen formal states map to named future
  assertions;
- all ten task-contract test layers and every required scenario have a named
  coverage location;
- all-external cannot pass without exhaustive integration/codebase inventory,
  decoded historical call evidence, declared coverage gaps, and product plus
  protocol/security disposition;
- zero asset staker/voter allocations are not misreported as Stock-specific
  reward disablement; deposits stay disabled until reward/loss behavior is
  approved;
- the Ledger transition cannot pass without the full-state migration matrix,
  even though Phase J does not authorize that migration;
- exact-token, Base regression, S1/S2 clock, S2 inventory, S3 compatibility,
  artifact parity, and migration failures all fail closed;
- Base is hardened first or converges atomically before RH enablement; and
- inactive empty staging is never accepted as launch evidence.

Phase J does not run nonexistent future tests, change current tests, select a
mechanism, or authorize implementation or migration. The operative posture
remains `do not list Stock Tokens under the current vault designs`.

## 21. Phase K — implementation and release split

### 21.1 Authorization and non-selection boundary

The exact Phase K authorization is recorded in Section 12.1. This phase
defines future review and release boundaries only. Every path below is an
**expected future file** or an explicitly blocked file choice; naming it does
not authorize creating or changing it.

The following distinctions are normative:

- **reviewable unit** means one coherent semantic and audit surface. It may be
  reviewed in its own PR after later authorization;
- **deployable unit** means an artifact that can be activated without another
  Track 8 unit. Most units below are deliberately not deployable alone;
- **atomic release group** means no affected economic/value path may be live
  under only part of the group. A state migration may use multiple
  resumable transactions only while both old and new paths remain contained
  and exactly one entitlement ledger is credit-eligible;
- **inactive staging** means an empty, unreachable, disabled artifact with no
  users, custody, debt, auctions, reward state, or live registry/config route.
  It is neither convergence nor launch and may be abandoned before any
  economic write; and
- **rollback** after a new economic write means a separately reconciled state
  transition. It never means merely pointing a registry back at an old
  address.

All-external fungible settlement remains evidence-conditional. The isolated
generic corrected-share variant, `A^s/U^s` state model, and two-selector
bad-debt transition remain unapproved candidates. A full Ledger migration is
not folded into the two-selector code review: it is a separate, highest-risk
owner/security/accounting/operations gate constrained by Track 6 S5 and Track
7.

### 21.2 Reviewable implementation units

The paths in the following table are exact where the current design and
repository establish them. A path marked **decision-bound** is deliberately
not invented: opening that unit requires the named owner to approve the exact
path first. Generated ABI files are changed only when the corresponding
approved runtime ABI changes; otherwise regeneration must prove byte equality.

| Unit | Review scope and expected future files | Stable components | Dependencies and owner decisions | Independently deployable? |
| --- | --- | --- | --- | --- |
| **K-00 — evidence and operations readiness** | Proposed `docs/chains/rh/stock-token-vault-implementation-record.md`, `docs/chains/rh/stock-token-vault-operations-runbook.md`, `docs/chains/rh/stock-token-settlement-usage-evidence.json`, `tests/probes/test_fungible_settlement_usage.py`, and `tests/probes/test_stock_token_vault_evidence.py` | `CM-021`, `CM-024`–`026`, `CM-030`, `CM-034`, every historical Teller/AuctionHouse generation | Separate read-only RPC/indexer authorization; complete integration and historical range inventory; product + protocol + security disposition; no production mechanism decision is implied | **No.** Release 0 evidence only; no production code, deployment, registry/config action, or Stock enablement |
| **K-01 — Teller deposit delta, mutex, event, and return** | `contracts/core/Teller.vy`, `scripts/abis/Teller.json`, proposed `tests/vaults/test_vault_receipt_accounting.py`, and `tests/core/teller/test_teller_deposit_receipts.py` | `CM-034`, `CM-045`, `CM-024`, `CM-025` | Phase D semantics; exact transient-storage/EVM proof; S5/S4 Teller overlap reconciled at the implementation baseline | **No.** Must activate with K-02/K-03/K-04/K-05/K-06 and their state/config cutovers |
| **K-02 — exact-receipt downstream consumers** | `contracts/vaults/RipeGov.vy`, `contracts/vaults/StabilityPool.vy`, `contracts/vaults/modules/StabVault.vy`, `contracts/core/BondRoom.vy`, `contracts/core/HumanResources.vy`, `contracts/core/CreditEngine.vy`, `contracts/core/CreditRedeem.vy`, `contracts/core/Deleverage.vy`, and `contracts/core/Lootbox.vy`; `scripts/abis/{RipeGov,StabilityPool,BondRoom,HumanResources,CreditEngine,CreditRedeem,Deleverage,Lootbox}.json`; proposed/affected tests resolved by validation profiles J-P02/J-P07 | `CM-022`, `CM-023`, `CM-029`, `CM-030`, `CM-032`, `CM-033`, `CM-043`, `CM-044` | K-01 exact `R`; integrated S3/S4 source; live local/pause/constructor/cooldown state inventory for every replaced stateful consumer | **No.** Every caller that assumes exact versus measured receipt must be compatible before K-01 is reachable |
| **K-03 — existing collateral controls and governance** | Expected production diff is **none** in `interfaces/ConfigStructs.vyi`, `contracts/data/MissionControl.vy`, `contracts/config/SwitchboardAlpha.vy`, `contracts/config/SwitchboardBravo.vy`, and `contracts/config/SwitchboardCharlie.vy`; proposed `tests/config/test_asset_collateral_controls.py` and `tests/config/test_stock_token_incident_controls.py` prove the negative file/schema contract | `CM-009`, `CM-011`–`013`, `CM-030` | Owner-confirmed no-new-collateral-flag direction; existing `canDeposit`, `DebtTerms.ltv`, automatic backing, `canLiquidate`, and asset containment semantics | **No artifact to deploy.** It is a mandatory negative-evidence and configuration prerequisite for Releases 1/2 |
| **K-04 — deficit detection, debt health, and repay liveness** | `contracts/core/CreditEngine.vy`, `scripts/abis/CreditEngine.json` only if changed/additive surfaces require it, proposed `tests/core/creditEngine/test_deficit_aware_credit.py` and `tests/core/creditEngine/test_stock_token_repay_liveness.py` | `CM-030`, `CM-009`, `CM-024`, `CM-025`, `CM-034`, `CM-045`, `CM-008` reader | K-03 controls; Phase E capacity/resolution split; current-price failure regression; K-06 existing-debt progress before activation | **No.** Fail-closed value/health cannot go live without settlement and debt-progress units |
| **K-05 — live-backed delivery and fungible settlement** | `contracts/core/AuctionHouse.vy`, `contracts/core/Deleverage.vy`, `scripts/abis/AuctionHouse.json`, `scripts/abis/Deleverage.json`, proposed `tests/core/auctionHouse/test_loss_aware_auctions.py` and `tests/core/deleverage/test_loss_aware_deleverage.py` | `CM-026`, `CM-044`, `CM-030`, `CM-034`, vault implementations and Ledger auctions | K-00 complete usage evidence; product/protocol/security approval of all-external or another mechanism; Phase F `E=min(Q,W,R)`; active-auction inventory | **No.** All-external is not even implementation-eligible until K-00 closes; delivery, payment, debt, and points must activate with Release 1 |
| **K-06 — total-loss resolver and atomic accounting candidate** | Candidate `contracts/core/CreditEngine.vy`, `contracts/data/Ledger.vy`, `scripts/abis/CreditEngine.json`, `scripts/abis/Ledger.json`, proposed `tests/core/auctionHouse/test_stock_token_resolution_controls.py` and `tests/data/test_ledger_bad_debt_transition.py` | `CM-030`, `CM-008`, `CM-026`, `CM-009` | Owner/accounting/security selection of the two selectors or another atomic design; accrued-interest booking; deterministic-caller proof; existing `canLiquidate` gate; S5 architecture decision | **No.** Candidate selectors are unapproved and, if selected, cannot activate without K-07 |
| **K-07 — full Ledger state migration and cutover** | No legal Track 8 migration filename exists yet. The unit is blocked until Track 7/owner assigns one. Known exact review files are proposed `tests/data/test_ledger_state_migration.py` and the K-00 implementation record. `migrations/robinhood/0030_Track6S5LedgerGuard.py` is S5-owned and prohibited for Track 8 reuse. | `CM-008` plus every Ledger reader/writer and Track 7 migration tooling | K-06 mechanism approval; complete Ledger state/key enumerability; S5 Checkpoint 0; Track 7 namespace; independent accounting/security audit; rehearsed forward/reverse plan | **No. Highest-risk separate gate.** No fresh Ledger may become active on an incomplete or best-effort state copy |
| **K-08 — isolated corrected-share candidate** | Candidate-only path set: `contracts/vaults/AllocatedErc20.vy`, `contracts/vaults/modules/AllocatedSharesVault.vy`, `interfaces/AllocatedSharesVault.vyi`, `scripts/abis/AllocatedErc20.json`, proposed `tests/vaults/modules/test_vault_loss_properties.py` and `tests/vaults/test_corrected_share_compatibility.py` | New generic counterpart to `CM-025`, plus `CM-021`, `CM-023`, `CM-024`, `CM-033` controls | Owner must approve even these candidate names; `A^s/U^s` storage/selectors/events; counsel/risk loss ordering; positive-delta isolation; migration-import design if live state moves | **No.** The file set is a review target, not a selected vault; it activates only in Release 2 |
| **K-09 — reward units, getters, events, and monitoring** | Decision-bound production set: either a reviewed `contracts/core/Lootbox.vy`/`scripts/abis/Lootbox.json` loss-boundary mechanism composed with K-08, or another exact owner-approved set. A Ledger-based loss index would additionally enter K-07 and is not presumed. Proposed tests are `tests/core/lootbox/test_vault_loss_rewards.py` and the K-08 compatibility tests; K-00 owns the operator record/runbook | `CM-033`, `CM-025` candidate, `CM-008`, `CM-013` configuration | Economics/security selection of loss epoch/index/callback; S3 sequencing and final-window policy; `U` exclusion; untouched-user proof; exact unit labels | **No.** S3 proceeds independently if this unit would delay it; Stock deposits/rewards remain disabled until K-09 is approved and atomic with Release 2 |
| **K-10 — Base/RH defaults and configuration contract** | Preferred path expects no Track 8 schema/runtime diff in `interfaces/Defaults.vyi`, `interfaces/ConfigStructs.vyi`, `contracts/data/MissionControl.vy`, `contracts/config/SwitchboardAlpha.vy`, `contracts/config/SwitchboardBravo.vy`, `contracts/config/SwitchboardCharlie.vy`, or `contracts/config/SwitchboardDelta.vy`. Review exact Base/local/Robinhood value sources `contracts/config/DefaultsBase.vy`, `contracts/config/DefaultsLocal.vy`, and future S6-owned `contracts/config/DefaultsRobinhood.vy`; generated ABIs only for an approved change. Proposed config tests are those in K-03 plus `tests/config/test_core_cutover_state.py` | `CM-007`, `CM-009`, `CM-011`–`014`, `CM-049` | S6 owns Robinhood defaults; Track 7 owns asset actions; standing Stock disables; no omitted-argument enable defaults; Base-first/atomic posture | **No.** Values/actions are part of the applicable atomic release and require separate live-configuration authorization |
| **K-11 — vault/core migration, registry, manifests, and verification** | Track 7-owned proposed RH paths `migrations/robinhood/0500_VaultsAndAssets.py` and `migrations/robinhood/0600_CoreDepartments.py`, future `migration_history/robinhood-{testnet,mainnet}/v1/`, proposed `tests/registries/test_vault_book_migration.py` and `tests/probes/test_stock_token_artifact_parity.py`. The exact Base migration filename/ID and any additional RH step remain decision-bound; current `migration_history/base-mainnet/v1/current-manifest.json` is evidence, never edited retroactively | `CM-004`, `CM-008`, `CM-009`, `CM-021`, `CM-024`–`026`, `CM-030`, `CM-033`, `CM-034`, Track 7 | K-01–K-10 applicable artifacts approved; production vault/ID; exact Track 7 namespace; live users/funds/debt/auctions/rewards; Base-first/atomic plan; signer/timelock authorization later | **No.** Migration and activation are release-level operations; no partial state or registry-only “migration” is deployable |
| **K-12 — exact-token, lifecycle, adversarial, dual-clock, and full regression** | Every proposed test path and fixture in companion Sections 3–14, especially `tests/probes/test_aapl_vault_behavior_fork.py`, integrated `tests/clock/test_clock_profiles.py`, `tests/inventory/test_block_clock_inventory.py`, and `scripts/check_block_clock_inventory.py` | `CM-059`, Track 2 AAPL, all affected Track 8 IDs | Approved implementation candidate; integrated S1/S2; exact-token permission/evidence; Track 7 rehearsal; every unit-level gate | **No.** Tests/evidence can reject a release but cannot authorize or constitute deployment |

K-02 is an umbrella compatibility gate, not permission for one broad
nine-contract PR. After later authorization it is divided into these small
subreviews:

- **K-02a — vault consumers:** `contracts/vaults/RipeGov.vy`,
  `contracts/vaults/StabilityPool.vy`,
  `contracts/vaults/modules/StabVault.vy`,
  `scripts/abis/RipeGov.json`, and `scripts/abis/StabilityPool.json`; targeted
  regressions include `tests/vaults/test_ripe_gov_vault.py`,
  `tests/vaults/modules/test_stab_vault.py`,
  `tests/vaults/modules/test_stab_vault_claims.py`, and
  `tests/vaults/modules/test_stab_vault_redemptions.py`.
- **K-02b — core stake/reward consumers:** `contracts/core/BondRoom.vy`,
  `contracts/core/HumanResources.vy`, `contracts/core/CreditEngine.vy`,
  `contracts/core/CreditRedeem.vy`, `contracts/core/Lootbox.vy`, and their
  exact same-name `scripts/abis/*.json` files; targeted regressions include
  the existing BondRoom, HumanResources, credit-redemption, and Lootbox claim/
  reward suites plus J-P02's exact-receipt cases.
- **K-02c — deleverage consumer:** `contracts/core/Deleverage.vy`,
  `scripts/abis/Deleverage.json`, the existing
  `tests/core/deleverage/**` suite, and proposed
  `tests/core/deleverage/test_loss_aware_deleverage.py`.

Each subreview may be its own PR and reviewer record. None is independently
deployable, and K-02 remains failed until all production callers are accounted
for and the combined artifacts pass Release 1 review.

`AllocatedErc20.vy`, `AllocatedSharesVault.vy`, and
`AllocatedSharesVault.vyi` are exact **candidate review paths**, introduced
only so a future implementation authorization can name or reject a concrete
file set. They do not select a production class, storage layout, interface,
VaultBook ID, or artifact. If the owner does not approve those names and that
boundary, K-08 remains unopened and the files must not be created.

Files shared by multiple units have one owner per hunk. In particular:

- K-02 owns exact-receipt call-site changes inside CreditEngine, Deleverage,
  and Lootbox;
- K-04 owns CreditEngine backing, health, capacity, and repayment semantics;
- K-06 owns only a later approved CreditEngine resolver and Ledger transition;
- K-05 owns Deleverage delivery/settlement semantics; and
- K-09 owns only a later approved Lootbox loss-boundary mechanism built on
  integrated S3.

Those reviews may be separate commits, but the final combined artifacts and
storage/config snapshots must be reviewed again before an atomic release.

### 21.3 Unit assurance, consumers, and stop boundaries

“S1/S2” below means use the integrated clock fixtures for every applicable
case, run the checked inventory command and tests, explain every inventory
delta, and pass the full integrated suite serially. A unit with no direct
`NUMBER` dependency still runs the release-level S1/S2 gate so that a shared
artifact or fixture cannot bypass it.

| Unit | Storage / ABI / artifact effect | Targeted Phase J evidence and required S1/S2/Base regression | Audit boundary and downstream consumers | Migration/rollback boundary and unit stop conditions |
| --- | --- | --- | --- | --- |
| K-00 | Documentation, sanitized evidence, and read-only tests/probes only; no runtime artifact | J-P05/J-P06/J-P15, T0/T3; pinned Base snapshots and complete historical ranges; S1/S2 versions recorded | Operations + product + protocol/security; feeds K-05, K-10, K-11, K-12 | Stop on provider/range/runtime/calldata/integration gap, unapproved RPC acquisition, private data, or disagreement. Never infer “unused” from a default |
| K-01 | Fresh Teller runtime; existing selectors/returns preserved; additive measured-deposit event; transient mutex; ABI changes only for event | J-P01, T1/T5/T6; ordinary/no-return/short/fee/negative/excess/reentrant and housekeeping-enabled Base regressions | Teller/vault security; all deposit producers and consumers | Reproduce pause/constructor state. Stop on unfaithful transient tests, C3 liveness failure, callback regression, or any caller bypass. No rollback after a downstream exact-`R` write without full reconciliation |
| K-02 | Fresh runtimes for changed consumers; no intended public selector/event change; ABI equality expected except independently approved deltas | J-P02/J-P07 plus each existing component suite, T1/T2/T5/T6; integrated S3/S4 and Base stateful-consumer regressions | Each component owner + protocol/security; users of RipeGov, StabilityPool, bonds, HR, redeem, deleverage, rewards, and CreditEngine distributions | Every stateful replacement needs exact local/pause/constructor/cooldown/pending-action state. Stop on ignored return, mixed Teller/caller reachability, callback break, or incomplete state inventory |
| K-03 | Required negative proof: no new storage, tuple, selector, event, default field, runtime, or ABI | J-P03/J-P13, T1/T2/T5/T6; current Base full-config round trip and lite-disable/governance-enable behavior | Config/governance/security; CreditEngine, AuctionHouse, operators, every asset config reader | Stop on any schema drift, hidden flag, LTV-as-incident-switch use, omitted-argument enable, or repayment-affecting pause |
| K-04 | Fresh CreditEngine runtime; no new persistent storage; public ABI expected unchanged unless K-06 later adds a selector/event | J-P04/J-P08, T1/T2/T5/T6; mixed collateral, one-unit deficit, missing price, repay, withdrawal, gas/staticcalls, Base existing-debt regression | Credit/risk + protocol/security; borrow, health, withdrawal, liquidation, repay, previews | Reproduce local config/pause/constructor state. Stop on false health, price-dependent custody control, repay failure, preview/state divergence, unacceptable gas, or K-06 absence at total loss |
| K-05 | Fresh AuctionHouse and affected Deleverage runtimes; no new persistent state; ABI-compatible buy inputs retained, with explicit rejection of unsupported internal mode; additive delivery evidence only if approved | J-P06/J-P07, T2/T3/T5/T6; two-buyer order, short/zero delivery, active auctions, Base fungible products, historical coverage | Auction/security + product; buyers, liquidated users, Teller, vaults, Ledger, Lootbox, Deleverage | Reconcile active auctions and local/pause/constructor/cooldown state. Stop until K-00 closes; stop on any internal-mode dependency without disposition, payment for `E=0`, or mixed old/new buyer path |
| K-06 | Candidate additive CreditEngine/Ledger selectors/events; no intended new Ledger storage, but both runtime/ABI artifacts change | J-P08/J-P09, T2/T5/T6; exact debt/yield/borrower/auction/bad-debt conservation, duplicate/race/repay and Base existing-debt regressions | Accounting + Ledger/security; borrowers, repayment, liquidation, bad-debt and auction consumers | Cannot activate without K-07 for the candidate design. Stop on unresolved yield booking, caller discretion, partial eligibility scan, non-CAS write, S5 conflict, or any liability mismatch |
| K-07 | Fresh Ledger state-owning runtime plus complete state transfer; migration artifact/manifest names remain owner/Track 7 blocked | J-P16, T3/T6 plus every Ledger domain suite and S5 state inventory; S1/S2 and Base full-state rehearsal mandatory | Separate external accounting/security audit + operations/Track 7; every protocol Department that reads/writes Ledger | Full forward/reverse roots only. Stop on one non-enumerable/unreconciled key, incomplete pause/constructor/locked/lastTouch state, reused S5 ID, stale snapshot, unapproved migration, or inability to keep repayment live |
| K-08 | New generic wrapper/module runtime and specialized ABI; fresh `A^s/U^s` storage; canonical `Vault.vyi`, current SharesVault/Rebase/RipeGov artifacts remain unchanged | J-P10/J-P12/J-P14, T1/T2/T3/T5/T6; 6/18 decimals, ordering/property tests, loss/donation/restoration/freeze, existing positive-rebase and RipeGov Base controls | Independent vault/math security + economics/counsel-risk; Teller, CreditEngine, AuctionHouse, Lootbox, VaultBook, operators | Fresh empty staging needs no import but is inactive. Any live state requires approved seeding/finalizer and K-11. Stop on unapproved paths/layout/selectors, allocation ambiguity, positive-delta regression, dust leak, or non-reversible post-zero bypass |
| K-09 | Decision-bound Lootbox and possibly corrected-vault runtime/ABI/storage; no Ledger involvement unless separately escalated through K-07 | J-P11/J-P12, T2/T3/T5/T6; untouched/touched users, interval boundaries, global value, `U` exclusion, S3 constructor/floor/getter/window regressions | Economics + Track 6 + protocol/security; deposit/yield points, RIPE distribution, Underscore path, RipeGov exception | S3 must remain independently releasable. Stop on raw-share reward, stale untouched-user accrual, unresolved S3 window, unapproved epoch/index/callback, or combined artifact that delays/reopens S3 without approval |
| K-10 | Preferred negative schema/runtime proof plus exact per-chain values/actions; any actual default/interface/ABI change reopens owner review | J-P03/J-P13/J-P18, T2/T3/T5/T6; Base live config snapshot, RH disabled-profile generation, omitted-address/standing-disable regressions | Governance/config/security/operations + S6/Track 7; every core/vault consumer | Config is activated only with its release group. Stop on unapproved value, source fork, chain-id behavior branch, missing getter/event, inherited enable default, or any action that impairs repayment |
| K-11 | New deployment/migration scripts and generated manifests only after exact approval; existing histories never rewritten | J-P17/J-P18, T3/T5/T6; clean dry plan, partial failure, roots, code/constructor/ABI parity, Base/RH and exact registry resolution | Independent migration/security/operations + Track 7; every replaced artifact, registry, user, and asset | Before seeding, abandon inactive artifacts. After seeding, forward or explicit reverse migration only. Stop on invented ID, manifest-only migration, duplicate credit eligibility, custody/read mismatch, signer/timelock gap, or failed post-state assertion |
| K-12 | Tests/fixtures/evidence only; no production or live artifact | J-P00/J-P19/J-P20 and every other profile, T0–T6; exact AAPL fork, every clock, full lifecycle/adversarial, full Base regression and clean Track 7 rehearsal | Independent release reviewer + Track 2/6/7, protocol/security/accounting/economics/counsel as mapped | Stop on skip/xfail/relaxed assertion, unapproved exact-token behavior switch, harness drift, nondeterminism, test/live identity mismatch, or any failed mandatory tier |

### 21.4 Dependency order and cross-track collision policy

Review-unit order is:

```text
K-00 evidence
    -> settlement/mechanism owner decisions
    -> K-01/K-02/K-03/K-04/K-05/K-06 review
    -> K-07 if the two-selector Ledger candidate is selected
    -> Release 1 integrated audit/rehearsal/Base activation
    -> Base soak and evidence
    -> K-08/K-09/K-10/K-11/K-12 Release 2 work
```

K-03 negative-schema proof can run in parallel with K-00. K-08 math and
compatibility review may be prepared after its exact candidate files,
storage, interfaces, and counsel/risk ordering are approved, but it cannot
activate before Release 1 containment is live and accepted. K-09 may not hold
S3 open: if Track 8 is not implementation- and audit-ready at the S3 gate, S3
continues independently and K-09 plans a later explicit cutover.

A future implementation branch must start from the exact integrated,
owner-approved H-01/S4/S5/Track 7 baseline. If S4 or S5 edits Teller,
CreditEngine, Ledger, MissionControl, SwitchboardDelta, an ABI, a fixture, or
a test used here, the affected Track 8 unit is re-traced before code begins.
No agent may resolve a collision by silently copying one branch over another,
coalescing two security policies into one event or flag, or reusing a
migration identifier.

### 21.5 Release 0 — operations and evidence readiness

Release 0 is **not a software or chain release**. Its allowed future output,
after separate authorization, is K-00 plus the read-only/evidence portions of
K-10/K-12:

1. freeze source, integration, runtime, proxy/beacon, registry, config, and
   historical block-range inputs;
2. build the complete current and historical fungible-settlement usage record;
3. refresh Base custody/accounting/control evidence at one pinned block;
4. prepare the incident and migration runbooks, named reviewers, audit scopes,
   stop conditions, and immutable evidence schema;
5. reproduce T0 and the integrated S1/S2 interfaces without changing
   production code; and
6. return every mechanism and evidence gap to the owner.

Release 0 must not:

- create or change production contracts, interfaces, storage, ABIs, defaults,
  migrations, manifests, or live configuration;
- enable a Stock Token path;
- acquire live RPC/indexer evidence without the separate acquisition
  authorization;
- deploy even an empty artifact and call that Release 0; or
- convert an evidence recommendation into the all-external, Ledger, vault,
  reward, or migration decision.

An empty gated deployment is a possible later pre-activation state inside an
approved Release 1 or 2 execution plan. It is not Release 0 completion and is
never launch.

### 21.6 Release 1 — atomic shared containment

Release 1 is the minimum shared Base hardening group. It is eligible only
after the owner separately approves the complete mechanism, source, audit,
migration, and Base execution bundle.

Its atomic economic group is:

```text
K-01 Teller exact receipt
+ K-02 all exact-receipt consumers
+ K-03 existing-control/no-new-schema contract
+ K-04 deficit-aware capacity, health, and repay liveness
+ K-05 measured external delivery and approved settlement enforcement
+ K-06 exactly-once existing-debt progress
+ K-07 full Ledger migration, if K-06 uses the two-selector candidate
+ K-10 disabled/config posture
+ K-11 core/state/registry cutover
+ K-12 integrated validation
```

The group is logically atomic even if preparation and state migration require
multiple transactions: all affected deposits, payouts, claims, borrowing,
auction purchases, and other value paths remain contained until every new
artifact and state root is compatible. Repayment remains live. One reviewed
activation boundary then makes the full compatible set reachable.

The following partial states are forbidden:

- Teller returns fail-closed zero/short receipt while an old consumer assumes
  the requested amount;
- CreditEngine reports a deficit/zero value while old liquidation cannot
  deliver or resolve the corresponding debt;
- internal settlement can still charge GREEN for missing collateral;
- AuctionHouse measures delivery but debt/points/payment use a larger amount;
- a total-loss resolver can call an old Ledger, or a new Ledger is active
  before all state reconciles;
- an old and new core address are both reachable for the same economic path;
  or
- Robinhood enables a safer path while Base still runs the unsafe shared
  semantics.

All-external is part of Release 1 only if K-00 proves complete integration and
historical compatibility and product/protocol/security explicitly approve the
behavior change. Otherwise Release 1 stops for another approved generic
mechanism or remains `do not list`; it may not infer approval from the current
default argument.

The candidate two-selector transition is part of Release 1 only if its
interfaces, event, accounting, caller proof, and K-07 migration are
separately approved. The Ledger migration remains a distinct high-risk
checkpoint and audit even if it is scheduled in the same activation group.
If that gate does not close and no equally atomic alternative is approved,
Release 1 does not activate.

Release 1 does not approve SimpleErc20 as the Stock Token vault and does not
enable Stock Tokens. Base ID 3 may remain in place only after a current
fully-reconciled snapshot and with the Section 19.7 constraints. Any nominal
deficit at the cutover is a stop requiring an owner allocation/containment
decision; it is not silently socialized or migrated.

### 21.7 Release 2 — corrected issuer-controlled collateral completion

Release 2 is separate from Release 1 and cannot begin economic activation
until Release 1 is live, reconciled, and accepted on Base or is included in
one explicitly approved atomic convergence plan.

Its atomic economic group is:

```text
approved K-08 generic corrected-share artifact
+ approved K-09 reward/loss-boundary semantics
+ K-10 final disabled configuration and standing constraints
+ K-11 custody/state/registry/manifest migration
+ K-12 exact-token, lifecycle, adversarial, dual-clock, Base/RH evidence
```

Before Release 2 implementation or activation, the owner and named reviewers
must approve:

- the exact generic source paths, storage order, selectors, events, ABI, and
  positive-delta boundary;
- `A^s/U^s` or an audited equivalent plus counsel/risk confirmation of
  loss-before-quarantine ordering;
- any migration import authority/finalizer and its permanent removal;
- the Track 8 loss interval/index/callback and S3 sequencing/window policy;
- the production vault and Track 7-owned VaultBook ID;
- complete state/custody/reward/debt/auction migration and rollback reality;
- exact AAPL fork and approved live-evidence gates; and
- one audited Base-first or atomic convergence plan.

Base shared safety semantics must be live first or converge atomically before
any Robinhood deposit, borrow, auction, reward, or other Stock value path is
enabled. This does not automatically require migrating Base ID 3 or ID 4 into
the new generic vault: any Base custody-bearing vault adoption is its own
owner-approved migration. It does require every affected shared core/runtime
and behavior to meet the approved Release 1/2 safety contract before
Robinhood enablement. Permanent chain-specific logic is prohibited.

An empty corrected vault may be deployed, code-hash verified, and left
unregistered/disabled only under a later approved execution plan. That state
has no users, custody, debt, auctions, or Stock reward state, has a named
expiry/abort owner, and is recorded as **inactive staging**. It does not
satisfy vault selection, migration, Base convergence, exact-token lifecycle,
listing, launch, or enablement.

### 21.8 Final audit boundaries

Independent review is layered; one broad “audit passed” statement is
insufficient:

| Boundary | Minimum independent reviewers | Must include |
| --- | --- | --- |
| Teller receipt and consumer composition | Protocol + token/reentrancy security + each stateful consumer owner | Delta math, callback/mutex liveness, event/return compatibility, exact-versus-measured consumers, state reproduction |
| Credit and settlement containment | Credit/risk + auction/security + product | Backing/capacity/resolution split, price-independent custody control, repayment, measured delivery/payment/debt/points, complete historical settlement evidence |
| Total-loss accounting | Accounting + CreditEngine/Ledger security | Eligibility, caller discretion, CAS race, interest/yield booking, borrower/auction removal, exactly-once liability conservation |
| Ledger migration | Separate external accounting/security audit + operations/Track 7 | Every storage domain/key, enumeration proof, roots/totals, S5 guard/lock state, activation/rollback, no partial Ledger |
| Corrected share math/storage | Independent vault/math security + economics + counsel/risk | `A^s/U^s/A/U`, rounding/dust, loss/donation/restoration ordering, freeze, import/finalizer, positive-delta isolation |
| Rewards/S3 | Economics + Track 6 owner + protocol/security | Live-claim weights, untouched-user boundary, global conservation, S3 floor/constructor/getter/window, second-cutover reality |
| Configuration and migration | Governance/config security + operations/Track 7 | Existing-control schema, exact values/roles/timelocks, artifacts/manifests, state/custody roots, partial failure, Base/RH convergence |
| Exact-token and release | Track 2 + independent release reviewer + all failed-row owners | AAPL identity/behavior, S1/S2, Base full regression, testnet/rehearsal, smoke/soak, no skipped mandatory evidence |

A combined implementation may receive a combined audit report, but the report
must render each boundary and reviewer conclusion separately. S5 and Track 8
Ledger findings must remain distinguishable even if one forward Ledger
artifact is considered.

### 21.9 Stop conditions

Stop and return to the owner before implementation or release if:

- any named future source, interface, storage, ABI, default, migration,
  manifest, vault, ID, role, value, or transaction lacks explicit approval;
- K-00 cannot prove gap-free integration and historical settlement usage;
- product evidence shows a current internal-settlement dependency without an
  approved disposition;
- the candidate corrected-share paths/layout/selectors or reward mechanism
  remain unselected;
- counsel/risk has not accepted the loss/quarantine property treatment;
- the two-selector transition, interest booking, caller proof, or full Ledger
  migration is unapproved;
- S5 selects an incompatible Ledger posture or has not supplied the required
  state/threat evidence for a shared Ledger change;
- any Ledger state key/domain is not exhaustively enumerable and reconciled;
- Track 8 would delay required S3 safety instead of sequencing independently;
- any partial Release 1 state can make debt falsely healthy,
  non-liquidatable, or chargeable against undeliverable collateral;
- repayment fails in any containment, migration, pause, price, or loss state;
- an old and new entitlement can both contribute borrow, settlement, or reward
  value;
- a Base regression, S1/S2 inventory/profile, exact-token, artifact, migration,
  audit, or post-state assertion fails or requires a skip/xfail/relaxation;
- a migration ID/path is invented, reused, or conflicts with Track 7/S5;
- an issuer freeze/blocklist prevents forward or reverse custody movement;
- Base cannot harden first or converge atomically before Robinhood enablement;
- inactive staging gains custody/state/reachability or is described as launch;
- a proposed rollback is only an address flip after an economic write;
- the integration baseline or overlapping source changes after approval
  without a fresh trace; or
- a live RPC, signer, governance, registry, deployment, migration,
  configuration, or transaction action becomes necessary without its own
  authorization.

The Phase K default on every stop was containment and no partial release.
Section 23 now controls the product posture: keep Stock value paths disabled,
return evidence to the owner if the minimum group fails, and do not silently
expand into the permanent architecture or defer the mandatory launch feature.

### 21.10 Owner checkpoints before implementation and release

None of the following checkpoints is passed by Phase K:

| Checkpoint | Exact owner decision/evidence required | What passing it authorizes | Current status |
| --- | --- | --- | --- |
| **K-CP0 — final specification acceptance** | Owner and independent reviewer accept Phases A–K, decision register, unit split, and checklist handoff | Closes specification planning only | **Pending owner/reviewer acceptance; no implementation** |
| **K-CP1 — Release 0 evidence acquisition/build** | Exact read-only RPC/indexer sources/ranges, sanitized artifact paths, proposed probe/test/doc files, and reviewers | Only the named Release 0 evidence/probe/document work | **Not authorized** |
| **K-CP2 — Release 1 mechanism selection** | Complete K-00 record; approve all-external or another enforcement; approve two-selector or another atomic debt design; approve interest/caller semantics; resolve S5 posture | Selects architecture for an exact implementation proposal, not code or migration | **Pending; all-external and two-selector remain candidates** |
| **K-CP3 — Ledger migration gate** | Exact Ledger artifact delta, every-key state proof, S5 compatibility, Track 7 filename/plan, external accounting/security audit plan, forward/reverse rehearsal | Only the specifically approved Ledger implementation/migration preparation | **Separate high-risk gate; not approved** |
| **K-CP4 — Release 1 implementation authorization** | Exact branch/baseline, allowed files per K-01–K-07/K-10–K-12, test paths, reviewers, and atomic activation contract | Production/test/interface/ABI edits only in that exact file set | **Not authorized** |
| **K-CP5 — Release 1 merge readiness** | Independent code/audit approvals, all tiers green, exact artifacts, accepted migration plan, and clean integrated commit graph | Only owner-approved merge/integration of the reviewed branch | **Merge not authorized** |
| **K-CP6 — Base migration/deployment execution** | Exact pre-state roots, Track 7 migration, signer/role/timelock plan, abort/recovery boundary, and enumerated Base transactions/digests | Only the expressly listed Base transactions | **No live action authorized** |
| **K-CP7 — Release 1 acceptance** | Pinned Base post-state, repayment/deficit/settlement/debt evidence, smoke/soak, incidents and unresolved risks | Marks containment accepted; does not select/list a Stock vault | **Pending future live evidence** |
| **K-CP8 — Release 2 mechanism and vault selection** | Exact K-08 files/storage/interface/events, counsel/risk allocation approval, K-09 reward/S3 choice, production vault, Track 7 ID, migration/import/finalizer | Selects the Release 2 design for an exact implementation proposal | **Not approved; no production vault/ID** |
| **K-CP9 — Release 2 implementation/audit authorization** | Exact files, tests, audit scopes, integrated baseline, Base/RH topology, and disabled staging rules | Only the approved Release 2 code/test/audit work | **Not authorized** |
| **K-CP10 — migration/testnet/rehearsal** | Approved Track 7 plans, artifacts, state roots, exact-token permission, roles/signers, testnet and clean rehearsal evidence | Only each expressly named non-production action | **Not authorized** |
| **K-CP11 — Robinhood deployment and enablement** | Accepted Base-first or atomic convergence, production vault/ID, final manifests/config, audits, exact AAPL lifecycle, smoke/soak, product/risk/security/operations approval, exact transactions | Only the separately listed deployment/config/enable transactions | **Not authorized; Stock value paths remain disabled pending the Section 23 minimum group** |

Approval of one row does not imply the next. A phrase such as “proceed,” a
merged implementation branch, an audit report, or an empty deployment is not
transaction or launch authorization.

### 21.11 Final decision register

This table is the historical Phase K consolidated handoff. Recommendations
remain recommendations; Section 23 supersedes its initial-launch scope and
mechanism priorities without deleting the permanent-design record.

| Decision area | Options and evidence | Recommendation | Owner | Affected components | Prerequisite | Needed before | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Product outcome | Do not list / containment / corrected path / staged option 4; Track 5/Phases A–C | Staged containment then corrected path | Product + protocol | Whole track | Phase C evidence | Specification direction | **Option 4 owner-confirmed for specification only** |
| Custody invariant | Nominal / shares / live allocated claims; I-01–I-13 | `C`, accounted claims, allocable/deliverable amount, and borrow value remain distinct; fail closed | Protocol + risk/security | Vaults, Teller, CreditEngine, AuctionHouse | Formal model | Any implementation | **Specified; implementation unapproved** |
| Deposit measurement | Teller delta / vault inference / token adapter | Teller measures `R`; zero/negative/excess revert, short credit exact | Protocol + security | `CM-034`, vaults, K-02 consumers | Phase D | K-CP4 | **Specified; K-01/K-02 unapproved** |
| Per-asset collateral use | New flag / existing controls / no listing | Existing `canDeposit` + `ltv` + backing; no new flag | Protocol + security/governance | `CM-009`, `CM-011`–`013`, `CM-030` | Phase E | K-CP4 | **Owner-directed; negative schema proof pending** |
| Nominal deficit policy | Silent nominal / pro rata / zero capacity-value + containment / no listing | Fail closed; no internal charge; owner decision for any live partial-deficit allocation | Protocol + risk/accounting | `CM-024`, `CM-030`, `CM-026` | Current live snapshot | Release 1 cutover/incident | **Safety behavior specified; allocation unresolved** |
| Partial loss | Corrected-share pro rata / another allocation / no listing; nominal path differs | Pro rata live claims only in approved corrected share model; no silent nominal allocation | Protocol + economics/counsel-risk | `CM-024`, `CM-025` candidate | K-08/audit | Release 2 | **Share behavior specified; nominal allocation deferred** |
| Total loss | Zero-backed auction / freeze only / atomic debt transition / no listing | Atomic exactly-once transition after deterministic eligibility | Protocol + accounting/security | `CM-030`, `CM-008`, `CM-026` | K-00, S5 | K-CP2/K-CP3 | **Direction specified; mechanism/migration unapproved** |
| Post-zero state | Reopen / recapitalize / persistent freeze | Freeze old shares with zero claim; separate recapitalization only | Protocol + risk | K-08 vault, controls | Phase G | Release 2 | **Owner-confirmed behavior; storage/interface unapproved** |
| Donation allocation | First depositor / old holders / protocol / quarantine / explicit recovery | No automatic allocation; preserve `U` and require counsel/risk for disposition | Protocol + counsel/risk | K-08/K-09/K-11 | Property treatment | Release 2 | **No-automatic-allocation owner-confirmed; final disposition open** |
| Settlement policy | All external / per-asset mode / no listing | All-external preferred only after complete integration/history evidence | Product + protocol/security | `CM-026`, `CM-034`, vaults | K-00 | K-CP2 | **Conditional candidate; not selected for implementation** |
| Rounding | Current virtual offset / another audited scheme | `10^8` virtual shares, one virtual asset; deposit/claim down, burn up, last-share sweep | Protocol + math/security | K-08 | Property tests | Release 2 | **Specified; candidate implementation unapproved** |
| Rewards/monitoring | Raw shares / live claims / explicit hybrid | Live allocated claim weight, `U` excluded; select loss boundary with S3 independently releasable | Economics + Track 6 + security | `CM-033`, K-08, Ledger | K-09 design/S3 window | K-CP8 | **Units directed; mechanism and migration unapproved** |
| Emergency controls | Existing globals/assets / dedicated pause / broad Department pause | Existing controls, preserve repayment and safe withdrawals; no new dedicated pause by default | Protocol + security/operations | `CM-009`, `CM-011`–`014`, cores/vaults | Phase H evidence | Implementation/runbook | **Specified; no live action** |
| Vault selection | Simple / current Rebase / candidate generic / another generic / none | No current vault unchanged; candidate generic only after K-08/K-09/audit | Product + protocol/risk/security | `CM-021`, `CM-024`, `CM-025` | K-CP8 | Release 2/registration | **No production vault or ID selected** |
| Base live version | Base first / atomic convergence / no release | Base first or atomic before RH enablement; staging is inactive | Protocol + security/operations | Every changed shared component | Approved migration/release | K-CP6/K-CP11 | **Owner-directed posture; no migration** |
| Migration | Fresh deploy / complete state migration / no release | Track 7-owned exact plan; Ledger separate; vault custody/state/rewards exact | Protocol + accounting/security/operations + Track 7 | K-07/K-11 and all stateful artifacts | Exact files/IDs/roots | Live execution | **Unapproved; Base filename and production vault/ID open** |
| Exact-token evidence | Mock only / pinned fork / authorized live evidence | Pinned AAPL full lifecycle plus implementation-switch and failure cases; live action separate | Track 2 + product/risk/security | AAPL proxy/beacon/implementation, all selected components | Approved candidate, permission | K-CP10/K-CP11 | **Plan complete; test/live evidence absent** |
| Audit/release | Independent units / atomic groups / partial activation | Review units separately, re-review combined artifacts, Release 1/2 economically atomic | Owner + all boundary reviewers | K-00–K-12 | Phase K acceptance | K-CP4 onward | **Split specified; no implementation/audit/release authorized** |
| Mandatory initial-launch minimum | Permanent option-4 group / external-only nominal containment / evidence return | Section 23's Teller + fresh external-only nominal vault + CreditEngine + AuctionHouse group; defer corrected shares, automatic bad debt, Ledger migration, reward-loss, and recapitalization | Product + protocol + risk/security/accounting/operations | M0–M5 | Owner acceptance of Section 23 | File-exact implementation authorization | **Owner-directed proposal complete; mechanism, vault/ID, implementation, and live action unapproved** |

### 21.12 Phase K acceptance and final stop boundary

Phase K is specification-complete with companion validation-plan Section 19
because it:

1. separates all ten task-contract implementation surfaces into thirteen
   reviewable units with exact or explicitly blocked expected files;
2. names component IDs, dependencies, owner decisions, deployability,
   storage/ABI/artifact effects, targeted Phase J profiles, S1/S2 and Base
   gates, audit boundaries, migration/rollback boundaries, consumers, and
   stop conditions for every unit;
3. distinguishes individually reviewable PRs from economically atomic
   activation;
4. makes fail-closed receipt/deficit semantics, debt health, live-backed
   settlement, and existing-debt progress inseparable in Release 1;
5. keeps all-external conditional on complete integration/history evidence;
6. keeps the corrected-share, `A^s/U^s`, reward-boundary, and two-selector
   designs unapproved while still giving them concrete review boundaries;
7. keeps the full Ledger migration as a separate highest-risk S5/Track 7 and
   independent-audit gate;
8. preserves S3 independently, Base-first or atomic convergence, and inactive
   staging as non-launch;
9. defines Release 0 as evidence/runbook readiness with no production code,
   Release 1 as atomic shared containment, and Release 2 as corrected
   issuer-controlled collateral completion; and
10. returns every remaining decision and K-CP0–K-CP11 checkpoint before any
    implementation or live action.

Phase K originally stopped here for final owner and independent specification
review. The later owner direction authorized the Section 23 documentation
refinement only. No future production/test/interface/migration file named in
Section 21 or 23 may be created or changed without a new file-exact
implementation authorization.

## 22. Final checklist handoff

Track 8 did not edit, stage, or close any `rh-summary.md` checkbox. The
external working-tree modification disclosed in Section 3.13 is not a Track 8
change and is not part of this branch.

Eligible for final owner and independent specification review:

- Phase 0, **resolve the deployable Stock Token vault path** (line 85 at the
  `be6a759` reconciliation baseline) — option 4 and its release architecture
  are specified, but no production vault, implementation, or migration is
  approved. This item remains open until the owner decides whether the
  specification itself satisfies its planning portion and separately tracks
  production selection.
- Section 4, **finish the Simple versus Rebase comparison** (line 186 at the
  baseline) — Track 5 evidence is hash-verified, source-reconciled, and rerun.
- Section 4, **write a separate vault-change specification if current behavior
  is unacceptable** (line 190 at the baseline) — Phases A–K and the companion
  validation plan are now complete and eligible for final owner/independent
  review. Track 8 still does not close the checkbox itself.

Not eligible for closure:

- chosen-vault behavior testing (line 189);
- production vault or VaultBook ID selection;
- vault/feed/config/risk-parameter implementation or live values;
- issuer-failure implementation evidence;
- Release 0 evidence acquisition, Release 1 or 2 implementation/audit/
  migration/deployment evidence;
- the Section 4 exit condition; or
- any technical launch gate requiring production code, an approved Ledger or
  vault migration, exact-token lifecycle evidence, Base convergence, or live
  owner authorization.

The handoff to any future implementation owner is:

1. obtain K-CP0 final specification acceptance;
2. request K-CP1 before creating Release 0 evidence/probe/test files;
3. close the unresolved decisions in Section 21.11 at their exact
   checkpoints;
4. request a file-exact implementation authorization before changing any
   production, test, interface, storage, ABI, default, migration, or manifest;
5. preserve the K-00–K-12 review boundaries and Release 1/2 atomic activation
   groups;
6. keep S3 independently releasable and reconcile S4/S5/Track 7 at the
   implementation baseline;
7. keep Base hardened first or converging atomically before any Robinhood
   Stock value path; and
8. stop before every merge, audit engagement, RPC acquisition, deployment,
   migration, configuration, signer, transaction, and enablement action until
   its named owner checkpoint passes.

The later minimum-change launch refinement in Section 23 supersedes the old
product-default wording above. The current deployments remain technically
ineligible until the atomic containment group passes, but Stock Token support
itself is mandatory initial-launch scope.

## 23. Owner-directed minimum-change initial-launch proposal

### 23.1 Decision boundary and recommendation

This section is the controlling Track 8 launch handoff. It uses Phases A–K as
evidence but deliberately does **not** continue the ideal permanent
architecture.

**Recommendation:** implement one atomic containment group consisting of:

1. Teller call-local receipt measurement;
2. a fresh generic external-only nominal ERC-20 vault that composes the
   existing BasicVault accounting and fails closed on an aggregate deficit;
3. CreditEngine call-time backing checks using existing getters, existing
   `canDeposit`, and existing `DebtTerms.ltv`;
4. AuctionHouse recipient-delta verification for external fungible delivery;
   and
5. existing configuration controls, with Stock rewards and unsupported routes
   disabled.

For specification purposes the proposed generic vault source is named
`contracts/vaults/ExternalErc20.vy`. The name and path are review targets, not
an implemented or owner-selected production artifact. It is not
issuer-branded, Robinhood-specific, share-based, or chain-gated.

This is a reasonably small shared patch. It prevents the two launch-critical
failures—phantom borrowing and false settlement—without new persistent
storage, a new canonical interface, a per-asset mode, a corrected-share
ledger, automatic loss allocation, a bad-debt transition, or a Ledger
migration. Therefore the safe-stop condition that would force a return to the
larger architecture is **not reached** by the pinned source evidence.

Load-bearing pinned evidence:

| Current source | Why the minimum patch lands there |
| --- | --- |
| `Teller.vy:272-320`; `TellerUtils.vy:104-161` | Teller owns the transfer and passes a pre-transfer amount to the vault; the validator owns existing admission/limit controls. |
| `BasicVault.vy:24-91,97-148`; `SimpleErc20.vy:54-150` | Basic credits from aggregate custody, withdraws against nominal accounting, and supports nominal-only internal moves; the wrapper is the narrow place to add deficit and external-only capability. |
| `CreditEngine.vy:542-579,687-807,920-979,1230-1285` | One shared borrow-terms loop feeds borrow, health, liquidation, repayment refresh, and withdrawal capacity; it currently skips `amount==0`. |
| `AuctionHouse.vy:1014-1162,1184-1228`; `Deleverage.vy:338-473,814-907,1044-1078` | Buyer input selects internal versus external mode; GREEN and debt commit after only a positive vault-reported amount. Deleverage and collateral swap likewise value the amount returned through AuctionHouse's withdrawal wrapper. None of these paths independently proves the recipient delta. |
| `MissionControl.vy:599-667,713-723`; `SwitchboardCharlie.vy:1140-1185` | Existing deposit, withdrawal, auction, repay, limit, and fast-disable controls already exist; no collateral-use or settlement-mode field is required. |
| Section 5 Base snapshot | ID 3 is live and funded but had no observed deficit at the pinned block; a fresh Stock vault avoids migrating its 27 registered/9 funded rows. |

The older option-4 permanent path remains a post-launch design backlog. It is
not a prerequisite for initial Stock Token activation under this proposal.

### 23.2 Minimum atomic safety contract

Let:

```text
Q  = validated deposit transfer attempt
C0 = vault custody before deposit transfer
C1 = vault custody after deposit transfer
R  = C1 - C0, the measured receipt
N  = aggregate nominal accounting for (vault, asset)
M  = a user's nominal accounting for (vault, asset)
W  = vault-reported external withdrawal/debit
V0 = vault custody before external withdrawal
V1 = vault custody after external withdrawal
O  = V0 - V1, the measured vault outflow
B0 = recipient balance before external settlement
B1 = recipient balance after external settlement
E  = B1 - B0, the measured delivered amount
```

The complete launch group must provide all seven properties at once:

| ID | Required property | Minimum enforcement |
| --- | --- | --- |
| ML-01 | Deposits credit only tokens actually received | Teller requires `C1 >= C0` and `0 < R == Q`, passes only `R`, requires the vault return `R`, and verifies custody is unchanged by the bookkeeping call. A short receipt reverts atomically. |
| ML-02 | Missing custody cannot support new borrowing | CreditEngine derives `C` and `T` at call time. `C<T`, `T=0` for an enumerated position, a nonzero-share zero claim, `canDeposit=false`, or `ltv=0` contributes zero new-borrow capacity. A failed backing read fails the capacity-bearing call closed rather than returning positive capacity. |
| ML-03 | Deficit cannot make existing debt falsely healthy or non-liquidatable | Unsafe positions remain in the terms calculation with zero collateral/capacity and the existing nonzero configured resolution terms, using the current fallback weight of one. |
| ML-04 | No GREEN charge or debt reduction without delivery | The launch vault requires `O == W == E`; AuctionHouse independently requires `E == W`. Exact-zero delivery preserves the current zero-return/outer-assert semantics and never pays; negative, short, excess, or sender-side-extra loss reverts before GREEN transfer and debt reduction. Auction and Deleverage paths can return positive only for positive delivery. |
| ML-05 | Nominal internal movement cannot masquerade as delivery | The launch vault's existing `transferBalanceWithinVault` selector always reverts. Stock Tokens therefore have no internal settlement route even when the buyer requests it. |
| ML-06 | Repayment remains available | Repayment refresh uses non-raising valuation; known unsafe positions require no price, reduce debt by payment, and never require loss allocation or a bad-debt transition. |
| ML-07 | Unsafe activity fails closed after issuer loss | The launch vault rejects deposits, withdrawals, and internal transfers whenever live custody is below nominal accounting; CreditEngine zeros capacity/value, while AuctionHouse and its Deleverage wrapper cannot settle the missing claim. |

These are one atomic product gate. A deployment with only some rows is not
launch-ready.

### 23.3 Exact minimum production surface

#### A. `contracts/core/Teller.vy`

Affected internal function and entry routes:

- `_deposit`;
- `deposit`;
- `depositMany`;
- `depositFromTrusted`;
- `rebalance`;
- the Teller-held sGREEN route; and
- `depositIntoGovVault`.

Required delta:

1. add and acquire one **transient**, global deposit mutex before vault
   resolution, validation, token calls, or other external work; this is not
   persistent storage and does not alter upgrade/migration layout;
2. derive `Q` with the existing `TellerUtils.validateOnDeposit`;
3. read `C0`, transfer `Q`, read `C1`, and require
   `C1 >= C0` and `0 < R=C1-C0 == Q`;
4. pass `R` through the existing vault deposit parameter;
5. require the vault return `R`; and
6. require the target vault's custody still equals `C1` immediately after the
   vault bookkeeping call; then
7. complete existing Ledger participation, Lootbox, optional housekeeping,
   PriceDesk snapshot, event, and return ordering under the mutex, without
   adding the comprehensive design's post-housekeeping custody assertion, and
   release the mutex immediately before return.

No function selector, return type, canonical interface, persistent storage
slot, default, or existing event signature changes. Existing
`TellerDeposit.amount` and return values become the measured `R`.
`TellerDepositMeasured`, the `C3` post-housekeeping assertion, and production
caller rewrites from the comprehensive Phase D design are useful evidence
hardening but are not required for the seven launch properties. Existing
RIPE/GREEN/sGREEN exact-token regressions must nevertheless prove that every
trusted caller continues to receive `R == Q`.

The dedicated mutex is necessary even though public deposit entry points
already use the contract's global nonreentrancy lock:
`depositFromTrusted` is intentionally callable during legitimate Stability
Pool/Teller flows. The mutex permits that first deposit callback while
rejecting a further nested deposit until the first deposit has completed all
of its accounting and housekeeping. A revert rolls back the transient write
with the rest of the transaction.

#### B. proposed `contracts/vaults/ExternalErc20.vy`

Composition:

- existing `VaultData`;
- existing `BasicVault`;
- existing canonical `Vault` interface; and
- the same constructor/Department/VaultBook integration pattern as
  `SimpleErc20`.

Affected functions:

- `depositTokensInVault`;
- `withdrawTokensFromVault`;
- `transferBalanceWithinVault`; and
- the existing read methods inherited/exported through `VaultData` and
  BasicVault.

Required behavior:

```text
deposit:
    C1 = balanceOf(vault)
    R  = Teller-supplied amount
    require C1 >= R
    C0 = C1 - R
    require C0 >= N
    credit exactly R through BasicVault

withdraw:
    V0 = balanceOf(vault)
    require V0 >= N
    B0 = balanceOf(recipient)
    W  = BasicVault external withdrawal result
    V1 = balanceOf(vault)
    B1 = balanceOf(recipient)
    require V0 >= V1 and V0 - V1 == W
    require B1 >= B0 and B1 - B0 == W
    require V1 >= updated N

internal transfer:
    revert unconditionally
```

Consequences:

- a pre-existing donation remains uncredited;
- any aggregate nominal deficit freezes all deposits and withdrawals for that
  `(vault, asset)` rather than allocating residual custody by transaction
  order;
- full restoration to `C>=N` restores backing mechanically, but operational
  re-enable still requires governance review;
- no internal auction or redemption path can move only nominal accounting;
- sender-side fees or burns cannot consume a donation or create a new deficit;
  and
- ordinary fully backed nominal behavior remains unchanged.

The new vault has the same external Vault method shapes. It adds no persistent
field beyond the existing fresh `VaultData` layout and requires no migration
import, share math, checkpoint, allocation bucket, or recovery selector.
Its new artifact ABI contains `ExternalErc20VaultDeposit` and
`ExternalErc20VaultWithdrawal` with the same amount/is-depleted units as the
current Simple events. It emits no successful internal-transfer event because
that selector always reverts.

Using a fresh generic wrapper instead of replacing live Base vault ID 3 is
intentional. It keeps the launch property local to a clean vault and avoids a
state migration of Base's 27 registered assets and 9 custody-positive assets.
A future decision may choose a different generic filename or harden
`SimpleErc20` in place, but it must preserve these semantics and account for
the resulting Base migration blast radius.

#### C. `contracts/core/CreditEngine.vy`

Affected functions:

- `_getUserBorrowTerms` (the one shared calculation);
- `_repayDebt` (raising mode changes to non-raising); and, through the shared
  calculation, `getMaxBorrowAmount`, `borrowForUser`, `hasGoodDebtHealth`,
  `canLiquidateUser`, `canRedeemUserCollateral`,
  `getUserCollateralValueAndDebtAmount`, `getCollateralValue`,
  `getLatestUserDebtAndTerms`, `updateDebtForUser`, and
  `getMaxWithdrawableForAsset`.

Required call-time predicate:

```text
C = IERC20(asset).balanceOf(vault)
T = Vault(vault).getTotalAmountForVault(asset)

backingSafe =
    asset != empty(address)
    and M > 0
    and T > 0
    and C >= T

capacityEligible =
    backingSafe
    and AssetConfig[asset].canDeposit
    and DebtTerms[asset].ltv > 0
```

For the launch nominal vault, `T=N`. An aggregate deficit therefore makes
every user's contribution zero without assigning the residual `C`.

The current `amount == 0 -> continue` rule must be removed. A configured
unsafe position remains in weighted resolution terms using the existing
fallback weight `1`, so:

- it contributes zero `collateralVal` and zero `totalMaxDebt`;
- its nonzero liquidation threshold remains visible;
- existing debt is unhealthy unless other safe collateral covers it; and
- zero collateral cannot make `canLiquidateUser` false merely by erasing the
  threshold.

A backing-safe position with `canDeposit=false` keeps live collateral value
for liquidation resolution but contributes zero new capacity. This preserves
the Phase E capacity/resolution distinction and prevents a fast admission
freeze from fabricating a custody loss.

CreditEngine adds a contract-local declaration for the already deployed
`MissionControl.assetConfig(address)` getter, or an equivalently narrow
existing getter that exposes `canDeposit`. That is not a new selector or
canonical interface.

#### D. `contracts/core/AuctionHouse.vy`

Affected functions:

- `_transferCollateral`;
- `withdrawTokensFromVault` (the existing Deleverage-only wrapper);
- `_buyFungibleAuction`; and
- through that internal path, `buyFungibleAuction` and
  `buyManyFungibleAuctions`.

For an external withdrawal:

```text
acquire transient global delivery mutex
B0 = IERC20(asset).balanceOf(recipient)
W  = Vault.withdrawTokensFromVault(...)
B1 = IERC20(asset).balanceOf(recipient)
require B1 >= B0
E = B1 - B0
require E == W
release delivery mutex
price and charge only positive E, never the requested or merely reported amount
```

All existing ordering remains: collateral delivery completes before
AuctionHouse transfers GREEN to CreditEngine or calls debt repayment. Any
failed equality assertion reverts the vault debit, transfer, GREEN movement,
debt change, auction mutation, Ledger participation, points, and events.

The same exact-delivery boundary must wrap the existing Deleverage-only
`withdrawTokensFromVault` entry:

```text
acquire transient global delivery mutex
B0 = IERC20(asset).balanceOf(recipient)
W  = Vault.withdrawTokensFromVault(...)
B1 = IERC20(asset).balanceOf(recipient)
require B1 >= B0
E = B1 - B0
require E == W
release delivery mutex
return E
```

The wrapper may return exact zero so a Deleverage loop can preserve its current
skip/continue behavior. Auction and Deleverage outer entry points retain their
existing success/revert rules when every row returns zero; the measurement
patch adds no new zero assertion. Neither path may return a positive amount
unless that amount reached the recipient. This single AuctionHouse boundary
covers unchanged Deleverage debt repayment, governance collateral-swap
valuation, and the withdrawal half of replacement collateral; Teller's
exact-receipt rule covers the replacement deposit. No `Deleverage.vy` source
or interface change is required.

The mutex is global across assets and vaults only while one external delivery
delta is open. It is released before price, payment, debt, event, or the next
batch/Deleverage leg, so ordinary sequential composition remains available.
A token or recipient callback that attempts a nested settlement fails closed
instead of contaminating `E` with another transfer. No legitimate nested
AuctionHouse delivery was found in the pinned caller inventory; implementation
review must prove that assumption and the sequential-batch liveness companion.

For a legacy internal settlement, AuctionHouse must first require:

```text
IERC20(asset).balanceOf(vault)
    >= Vault(vault).getTotalAmountForVault(asset)
```

This generic guard prevents the existing Base nominal vault from charging for
an internally moved claim during an aggregate deficit. Internal settlement
otherwise remains available for other fully backed existing vaults under
their current semantics. The launch vault itself rejects every internal call,
including while solvent. This keeps the Stock policy generic and exact without
an AuctionHouse per-asset mode.

#### E. interfaces, storage, ABIs, Ledger, and configuration

| Surface | Minimum-launch result |
| --- | --- |
| Canonical `interfaces/*.vyi` | No change. The existing Vault and core selector shapes suffice. |
| Persistent storage | No change in Teller, CreditEngine, AuctionHouse, MissionControl, or Ledger. The fresh vault uses the existing `VaultData` layout. Teller's deposit mutex and AuctionHouse's delivery mutex are transient. |
| ABI | No existing selector or event changes. Existing generated ABI files should be byte-for-byte unchanged. The fresh vault requires one new ABI/artifact with the existing canonical Vault selector shapes and vault-specific deposit/withdrawal events; any other ABI delta is a stop. |
| Ledger | No source, interface, artifact, storage, migration, or bad-debt write change. Existing user debt remains user debt after an issuer loss. |
| MissionControl/Switchboards | No new field. Use existing `canDeposit`, `canWithdraw`, `canBuyInAuction`, `canRedeemCollateral`, `DebtTerms.ltv`, deposit limits, and general borrow/repay controls. |
| Stock defaults | `canRedeemCollateral=false`; `shouldSwapInStabPools=false`; no ordinary configured Endaoment, Curve, Aerodrome, Underscore, yield, treasury, or unsupported route. The privileged volatile Deleverage override is a separate operational prohibition described in Section 23.11. Start contained and enable only in the final atomic activation. |
| Rewards | Initial Robinhood launch must keep protocol points/reward accrual disabled, or set every reward allocation capable of paying Stock depositors/borrowers to zero. Per-asset staker/voter zeroes alone are insufficient because the generic depositor and borrower buckets are global. |

If product requires Stock-linked deposit or borrower rewards at initial launch,
the minimum proposal is no longer sufficient: the Track 8 reward-loss boundary
returns to the owner before implementation.

### 23.4 Settlement mechanism comparison

| Mechanism | Safety | Production impact | Evidence conclusion |
| --- | --- | --- | --- |
| Force external delivery for every fungible auction | Satisfies ML-05 and, with recipient-delta measurement, ML-04 | Small AuctionHouse code delta and no storage, but changes every Base/RH fungible asset. Source/tests prove internal mode is a supported path; the required decoded historical production-call record has not been acquired. | Not the minimum evidence-supported launch choice today. It remains eligible if complete history proves no dependency and product/security approve the global behavior change. |
| Generic per-asset settlement mode | Satisfies ML-05 when correctly configured | Adds AssetConfig or parallel storage, getter/setter/event/defaults, governance rules, migration, ABI/interface consumption, and fail-safe default questions. | Rejected for initial launch. Existing controls do not encode settlement mode, but new stored configuration is unnecessary when the selected vault can enforce its own capability. |
| Generic external-only nominal vault plus measured external delivery | Satisfies ML-04/05 without changing other vaults | One fresh stateless policy wrapper over existing modules; no new canonical interface or persistent config; one AuctionHouse delivery boundary with transient call isolation. Requires the Stock asset to be registered only to this vault. | **Recommended.** It has the smallest affected economic surface and avoids making incomplete historical usage evidence a blocker for unrelated assets. |

Silently changing `_shouldTransferBalance=true` into an external transfer is
forbidden. For the proposed launch vault the call must revert. The transaction
input therefore remains truthful and machine-auditable.

The pinned production consumer inventory for
`transferBalanceWithinVault` is exactly AuctionHouse and CreditEngine's
CreditRedeem wrapper; the vault itself authorizes only those two core callers.
The launch wrapper rejects both internal uses. Stock
`canRedeemCollateral=false` independently keeps the CreditRedeem route
unreachable, while AuctionHouse uses the measured external path.

### 23.5 Larger-feature necessity decisions

| Comprehensive feature | Required for safe initial Stock launch? | Minimum-launch disposition |
| --- | --- | --- |
| Corrected share vault / `A^s/U^s` model | **No** | Use the fresh external-only nominal vault. Aggregate deficit freezes the whole asset; no pro-rata loss allocation is claimed. Keep the corrected share design in post-launch research. |
| Automatic partial-loss allocation | **No** | Reject deposits/withdrawals/settlement while `C<N`. Governance and counsel/risk decide any later allocation. |
| Automatic total-loss or bad-debt transition | **No** | Existing user debt persists, may remain in liquidation, and can be repaid. No automatic write-off is needed to prevent new borrowing or false payment. |
| Two-selector CreditEngine→Ledger transition | **No** | Post-launch candidate only. Do not add selectors or events for initial launch. |
| Full Ledger migration | **No** | Explicitly excluded. The minimum group never changes Ledger layout or artifact. |
| Reward-loss accounting / loss interval | **No**, if Stock-linked rewards are disabled | Keep Robinhood reward accrual incapable of paying Stock depositors/borrowers at activation. Otherwise return to owner. Preserve S3 independently. |
| New stored per-asset collateral-use flag | **No** | Existing `canDeposit`, `DebtTerms.ltv`, and call-time `C/T` backing provide the required admission/capacity behavior. |
| New stored per-asset settlement flag | **No** | The generic launch vault rejects internal transfer by capability. |
| Post-zero recapitalization | **No** | A deficit stays frozen. Full restoration can be reviewed under existing controls; any allocation/recapitalization is post-launch governance work. |
| Automatic donation/restoration allocation | **No** | Donations do not enter Teller's `R`. No launch code assigns a deficit or surplus among users. |
| Additive measurement/checkpoint events | **No** | Existing deposit/withdrawal/auction/config events plus raw balance reads are sufficient for launch safety. Additional diagnostics are backlog. |

### 23.6 Base compatibility and migration consequences

The pinned Base evidence at block `49,036,674` shows:

- live Simple vault ID 3 had 27 registered assets and 9 custody-positive
  assets;
- every funded row was nominally solvent;
- WETH had one raw-unit surplus;
- several funded assets have issuer, bridge, proxy, pause, blacklist, burn, or
  upgrade control; and
- live Rebase vault ID 4 had no accounted shares and three one-unit donation
  rows.

The minimum launch topology is:

1. deploy the shared Teller, CreditEngine, and AuctionHouse containment
   artifacts to Base first, or converge Base and Robinhood atomically;
2. do **not** migrate Base ID 3 or ID 4 merely to launch Stock Tokens;
3. optionally deploy the fresh external-only vault on Base as inactive,
   empty, unreachable staging for code-hash parity; this is not adoption or
   launch;
4. give the Robinhood instance a Track 7-owned, owner-approved registry ID
   only after implementation/audit evidence; and
5. enable the Stock asset only after the full group and exact-token/config
   gates pass.

The core Base cutover is still stateful deployment/re-wiring and needs its own
approved migration transactions. It does not require copying vault balances or
Ledger state, but it must reproduce the exact live RipeHq constructor/address
posture and Department pause/mint permissions for Teller, CreditEngine, and
AuctionHouse, plus CreditEngine's live `undyVaulDiscount` and `buybackRatio`;
constructor defaults are not evidence of parity. Existing Base ID 3 remains a
legacy nominal vault; the shared CreditEngine and AuctionHouse changes harden
its borrow/settlement consumers, while its current users and registry are not
silently moved.

No claim is made that an empty Base vault proves migration safety. Base
regression must cover all 27 registered ID-3 assets, the 9 funded rows, current
auctions/debt, existing internal-settlement behavior on non-launch vaults,
Teller trusted-deposit callbacks, and the integrated S1/S2/S3 surfaces.

### 23.7 Intentionally accepted risks and exposure bound

| Accepted risk | Deliberate minimum behavior | Operational consequence |
| --- | --- | --- |
| Issuer loss freezes the affected Stock asset | `C<N` blocks deposits, withdrawals, internal movement, capacity, valuation, and paid settlement | Users may temporarily be unable to withdraw or liquidate that Stock Token. |
| Existing debt may outlive collateral | No automatic Ledger transition or write-off | The user debt remains, interest follows existing rules, the protocol may carry stranded/economically bad debt, and accounting resolution may require a later upgrade/governance process. |
| Partial nominal loss is not allocated | All claims freeze instead of assigning residual custody by call order | Solvent residual custody may remain stranded until counsel/risk and governance approve an allocation. |
| Auction progress can stop | An auction may exist but cannot produce positive exact delivery | No GREEN is charged and debt is not reduced; operators disable new buys and retain evidence. |
| Full restoration can make `C>=N` again | Source backing becomes safe, but existing `canDeposit/canWithdraw/canBuyInAuction` controls remain the operational gate | Governance must review issuer status, balances, users, debt, and auctions before re-enable. |
| No Stock reward-loss correction | Stock-linked deposit/borrow rewards are disabled at initial activation | Launch forgoes those rewards; enabling them is a separate post-launch product/economics/security decision. |
| Aggregate freeze is conservative | One-unit deficit freezes every user of the affected `(vault,asset)` | Liveness is sacrificed to prevent double allocation and phantom credit. |
| Fee-on-transfer or other short-receipt assets are unsupported | Teller requires measured `R==Q`; the transaction reverts if less arrives | This sacrifices compatibility rather than adding post-credit minimum/caller-reconciliation machinery. The current funded Base and exact AAPL gates must prove ordinary exact receipt. |
| Privileged volatile-route misuse remains possible | Existing flags exclude Stock from ordinary Deleverage, but a permitted Switchboard or registered Ripe caller can explicitly invoke the volatile-asset override | Launch permissions/runbooks must prohibit Stock input. Exact recipient measurement still prevents false debt reduction, but it cannot preserve the no-Endaoment product policy against an authorized privileged call. |
| Nested external settlement is rejected | The AuctionHouse delivery mutex is global during each balance-delta window | A transfer hook cannot initiate a legitimate cross-asset nested settlement; sequential batch and Deleverage legs remain supported after the mutex is released. |

At the pinned Base block the observed nominal deficit and directly evidenced
deficit-attributable debt were both zero. Robinhood pre-activation exposure is
also zero because the fresh vault must be empty and disabled.

After activation, the maximum configured Stock deposit exposure is bounded by
the existing global deposit limit:

```text
custody/claim exposure <= globalDepositLimit(asset)
new-debt capacity <= globalDepositLimit(asset) * DebtTerms.ltv / 100%
```

Actual incident exposure is the smaller live sum of user debt and the
pre-incident capacity attributable to the Stock position, accounting for mixed
collateral. The exact launch limit and LTV are risk/default values outside
this behavior specification and require owner/risk approval. They must be
finite, non-placeholder values in the final Robinhood manifest.

Incident sequence:

1. set general `canBorrow=false` if identity or blast radius is uncertain;
2. set the affected asset's `canDeposit=false`,
   `canWithdraw=false`, and `canBuyInAuction=false`;
3. preserve `canRepay=true`;
4. pin code identities and read `C`, `N`, users, debt, auctions, prices, and
   config at one block;
5. do not restart settlement, rewards, or withdrawals from a price-only or
   issuer-only assurance; and
6. return any allocation, write-off, restoration, or upgrade plan to the
   owner with accounting and counsel/risk review.

### 23.8 Minimum launch test plan

All tests are future implementation work. Nothing in this planning branch
creates or runs them.

| Layer | Required proof |
| --- | --- |
| Current-behavior baseline | Reproduce the existing 90-case Track 5 result on pinned `be6a759`; add candidate successor cases that explicitly invert only the unsafe receipt/deficit/settlement/repay expectations and pass only against the complete candidate group. |
| Teller receipt | Ordinary receipt; atomic rejection of short, zero, negative, or excess receipt; donation; `max_value`; batch; rebalance; trusted callback; cross-asset nested callback rejection; `V!=R`; and custody mutation during vault credit. |
| External-only nominal vault | First deposit, multi-user deposit, donation, one-unit deficit, partial/total loss, deposit/withdraw freeze, full restoration under disabled config, exact vault outflow and recipient inflow, sender-side fee/burn, transfer false/revert/short/excess, post-withdraw backing, and unconditional internal-transfer rejection for AuctionHouse and CreditEngine callers. |
| CreditEngine | One-unit nominal deficit zeros every user's capacity/value; amount-zero position keeps liquidation terms; mixed safe collateral stays exact; `canDeposit=false` capacity/resolution split; preview/state parity; read failure; price independence; repay with missing/stale price; max-withdraw composition; worst-case gas/staticcalls. |
| AuctionHouse and unchanged Deleverage consumers | Single/batch external delivery, current exact-zero return/outer-assert behavior, short/excess recipient delta, nested cross-asset callback rejection, sequential-leg liveness, token pause/blocklist, loss after auction creation, two buyers, no GREEN/debt/event/points mutation on failed delivery, legacy internal settlement blocked while `C<T`, and unchanged fully backed internal behavior on a separate legacy vault. The Deleverage wrapper must return only exact recipient delivery, preserve exact-zero leg behavior, bound deleverage debt reduction, and bind both legs of `swapCollateral` together with Teller. |
| Configuration and restricted routes | Stock redemption and ordinary Stability Pool/Endaoment/Curve/Aerodrome/Underscore/yield routes disabled; no new field; rewards cannot accrue to Stock depositors/borrowers; finite deposit/LTV limits; disable/re-enable authority and event evidence. Explicitly prove that no user-accessible or automated path supplies Stock to Deleverage's privileged volatile-asset override. |
| Exact AAPL | Pinned proxy/beacon/implementation/code hashes, transfer-in/out, pause/blocklist/upgrade-behavior switch, receipt/delivery equality, issuer loss before borrow/health/auction/repay, and restoration still held by config. |
| Base regression | All 27 ID-3 registrations, 9 funded rows, WETH surplus, trusted deposit consumers, existing debt/auctions, non-launch internal settlement, exact RipeHq/Department constructor-pause-mint posture, CreditEngine `undyVaulDiscount`/`buybackRatio`, S1/S2 clock profiles, integrated S3, artifacts, and complete serial suite. |
| Release/migration | Source/compiler/creation/runtime hashes, storage-layout negative proof, ABI negative proof, Base-first or atomic core cutover, fresh RH vault/ID, disabled staging, atomic activation, smoke/soak, and rollback/forward-recovery boundaries. |

Launch acceptance requires:

```text
credited == R == Q
vaultOutflow == recipientDelivery == O == W == E
C < N => deposit == withdraw == internalTransfer == capacity == value == 0
debt > 0 and no safe collateral and not already in liquidation
    and configured liqThreshold > 0 => canLiquidateUser == true
repayment decreases debt without an unsafe-asset price
failed containment action => all relevant state unchanged
```

No xfail, skipped exact-token row, unresolved ABI/storage diff, or partial
activation may be relabeled as launch-ready.

### 23.9 Reviewable implementation slices and atomic activation

PRs may be reviewed separately in this dependency order:

| Slice | Exact proposed files | Exit evidence | Individually activatable? |
| --- | --- | --- | --- |
| M0 — evidence freeze | Documentation/evidence files approved in a later file-exact authorization; no production source | Integrated caller/runtime inventory, Base refresh, exact AAPL identities, config/reward posture, historical internal-settlement evidence for legacy-impact assessment | No |
| M1 — receipt boundary | `contracts/core/Teller.vy`; `tests/core/teller/test_teller_deposit.py`; `tests/core/teller/test_teller_rebalance.py`; candidate cases in `tests/vaults/test_stock_token_vault_comparison.py` | ML-01, mutex/callback liveness, unchanged signatures/storage, trusted-consumer regression | No |
| M2 — launch vault | proposed `contracts/vaults/ExternalErc20.vy`; proposed `scripts/abis/ExternalErc20.json`; proposed `tests/vaults/test_external_erc20.py` | ML-05/07, exact external receipt, deficit freeze, canonical Vault ABI/layout proof | No |
| M3 — credit containment | `contracts/core/CreditEngine.vy`; `tests/core/creditEngine/test_credit_borrow.py`; `tests/core/creditEngine/test_credit_repay.py`; proposed `tests/core/creditEngine/test_stock_backing.py` | ML-02/03/06 across every shared consumer | No |
| M4 — settlement containment | `contracts/core/AuctionHouse.vy`; `tests/core/auctionHouse/test_ah_auctions.py`; proposed `tests/core/auctionHouse/test_stock_delivery.py`; `tests/core/deleverage/test_deleverage_swap_collateral.py`; proposed `tests/core/deleverage/test_stock_delivery.py` | ML-04/05, mutex/callback isolation, sequential batch/Deleverage liveness, two-buyer/state-root atomicity, legacy-vault internal-mode regression, exact-zero Deleverage behavior, debt reduction bounded by delivery, and exact collateral-swap withdrawal/deposit | No |
| M5 — integration/config/release | Proposed `tests/config/test_stock_token_minimum.py`; proposed `tests/config/test_core_cutover_state.py`; `tests/probes/test_stock_token_transfer_probe.py`; Track 6/7-owned defaults, migration, manifest, artifact verification, smoke/runbook files only after their exact paths are approved | Full suite, Base-first/atomic convergence, exact constructor/Department/CreditEngine-local state, disabled rewards/routes, exact AAPL lifecycle, audits, final state/config hashes | **Only as the complete group** |

The final Stock Token activation is one economic release:

```text
M1 + M2 + M3 + M4 + approved M5
```

M1–M4 may be deployed disabled for ordered migration only if no Stock value
path is reachable and old/new state cannot both contribute value. No partial
group, empty vault, passed unit test, deployed bytecode, or completed audit is
launch-ready by itself.

Deployment order:

1. freeze the implementation baseline and re-run M0;
2. build/review/audit M1–M4 as one composed artifact set;
3. deploy and activate the shared Base core set first, or execute an approved
   atomic Base/RH convergence;
4. deploy/register the fresh Robinhood launch vault under a Track 7-owned ID
   while all Stock controls and rewards remain disabled;
5. apply approved finite limits, LTV, oracle, route disables, and role values;
6. run full Base, Robinhood, and exact-AAPL post-state evidence;
7. enable the complete Stock path in one reviewed transaction sequence whose
   intermediate states remain contained; and
8. smoke/soak before declaring initial-launch readiness.

### 23.10 Post-launch backlog

Only the following permanent-design work remains after the minimum launch:

1. corrected generic share accounting with explicit allocated/unallocated
   backing and audited partial-loss math;
2. counsel/risk-approved loss, donation, restoration, and recapitalization
   treatment;
3. an atomic exactly-once debt-to-bad-debt transition if governance wants
   automatic resolution;
4. the separate full Ledger design/migration only if that transition still
   requires it;
5. Stock-aware reward-loss intervals and live-claim attribution, coordinated
   without delaying S3;
6. richer measurement/loss/checkpoint events and monitoring;
7. optional per-asset settlement configuration only if a demonstrated product
   need cannot be expressed by vault capability; and
8. migration from the launch nominal freeze model to the permanent path.

None of these may be pulled back into initial-launch scope merely because the
comprehensive Phase A–K analysis already specified it.

### 23.11 Owner decisions required before implementation

The minimum proposal returns these decisions:

1. approve or reject the generic external-only nominal vault as the initial
   Stock path;
2. accept or reject the freeze/stranded-debt/later-governance risk model;
3. approve Stock-linked rewards being disabled at initial launch;
4. approve the Base posture: shared core hardening first or atomically, with
   no automatic migration of live Base ID 3/4;
5. approve the four-contract production surface and the no-new-storage/
   no-new-canonical-interface boundary; and
6. accept the permissions/runbook prohibition on passing Stock to
   `deleverageWithVolAssets`, or require an onchain prohibition and reopen the
   exact Deleverage/config surface; and
7. only after those decisions, provide a file-exact implementation/test
   authorization. Track 7 separately owns the production VaultBook ID,
   migration names, manifests, and transaction plan.

This section does not pass any of those gates. It does establish that a small
shared patch exists and that Stock Tokens need not be postponed for the
corrected-share, bad-debt, Ledger, reward-loss, or recapitalization designs.

One narrow operational boundary remains explicit rather than hidden:
`shouldTransferToEndaoment=false` excludes Stock from ordinary configured
Deleverage processing, but the pinned source also has a privileged
`deleverageWithVolAssets` override that deliberately selects assets whose
ordinary Endaoment flag is false. Its SwitchboardDelta entry is
governance-only, while the underlying Deleverage entry also accepts a
registered Ripe address or a Switchboard. Initial-launch permissions and
operations must prohibit passing Stock assets to that override, and tests must
prove there is no user-accessible or automated route to it. If security
requires the prohibition to hold even against every authorized privileged
caller rather than as a reviewed permissions/runbook constraint, the existing
configuration surface is insufficient; return that evidence to the owner
before adding a Deleverage guard, stored flag, or interface.
