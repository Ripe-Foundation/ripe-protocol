# Shared Stock Token Vault-Change Specification

Status: **Phase H control/evidence analysis complete for owner review; no new
storage, interface, dedicated pause, or caller policy selected; Phases I–K
intentionally not finalized**

Date: 2026-07-24 (America/Denver)

This document is the Track 8 working specification required by
`track-8-stock-token-vault-change.md`. It records the evidence reconciliation,
formal state and invariant model, architecture comparison, mandatory early
owner checkpoint, exact deposit-accounting design, and backing/debt-health
design, plus the settlement/liquidation/total-loss and corrected share-vault
designs, and the Phase H current-control, governance, clock, and operational
evidence analysis. It does not select a production vault, approve an automatic
donation/restoration allocation or recapitalization, authorize a Base
migration, approve any newly identified storage/interface mechanism, select a
dedicated pause or caller policy, or authorize implementation.

The owner-confirmed instruction selects option 4 as the architecture direction
for specification work only. Until the later gates are approved and
implemented, the operative conclusion remains:

> **Do not list Stock Tokens under the current vault designs.**

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
11–17 and the corresponding earlier validation-plan surfaces. Phase H handoff
commit `1e414983946633c5f58e15c9bfb464aa84d067b5` did not enumerate that
reach-back clearly enough. For an explicit audit trail, those edits were:

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
| Base canonical shared-version hardening and migration | **Recommended as urgent**, pending owner live-version and migration approval. |
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

The remaining phase gates below remain operative. The current production
posture is still `do not list Stock Tokens under the current vault designs`.

### 12.2 Checkpoint decisions and their actual gates

The product/architecture direction required for Phase D, the existing-controls
direction required for Phase E, the two policy directions required for Phase
F, and the three policy directions required for Phase G are owner-confirmed as
satisfied for specification work. Phase H specification work is also
owner-authorized, but its control/caller alternatives are deliberately
returned without selection. The remaining two original decisions gate Phase I
and implementation planning. The Phase F–H source traces also create narrower
implementation-mechanism/caller/compatibility decisions; none is implied by a
policy approval.

| Decision | Options | Evidence and recommendation | Owner | Affected components | Prerequisite / milestone | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Product outcome | Five checkpoint options above | Staged containment then corrected share path | Product + protocol owner | Whole track | Before Phase D | **Owner-confirmed: option 4, specification work only** |
| Per-asset collateral use | Add a stored flag / compose existing controls | Reuse `canDeposit`, `DebtTerms.ltv`, and automatic backing state; do not add storage or a deployed selector | Protocol owner + security | `CM-009`, `CM-011`–`013`, `CM-030`, existing config/getters | Before Phase E | **Owner-confirmed: existing-controls Phase E specification only; implementation not approved; Phase F was authorized separately on 2026-07-24** |
| Issuer-controlled settlement | Always external / permit bounded internal | Current internal mode can charge for undeliverable nominal claims; external-only selected | Protocol owner + risk/security | `CM-026`, `CM-030`, `CM-043`, `CM-044`, Vault interface | Before Phase F | **Owner-confirmed: external-only Phase F specification; enforcement mechanism and implementation not approved** |
| Total-loss transition | Approved user-debt→Ledger-bad-debt design / another existing-accounting design / no listing | Current system has no atomic exactly-once path; atomic transition selected for specification | Protocol owner + accounting/security | `CM-026`, `CM-030`, Ledger, interfaces | Before Phase F | **Owner-confirmed: atomic exactly-once Phase F specification; identified interfaces and implementation not approved** |
| Post-zero state | Freeze / explicit recapitalization | Freeze selected; old shares persist with zero claim and no fresh deposits | Protocol owner + risk | `CM-025`, deposit callers, controls | Before Phase G | **Owner-confirmed: freeze for Phase G specification; implementation not approved** |
| Later donation/restoration | Old holders / donor return / protocol / explicit recapitalization allocation / no automatic allocation | No automatic allocation selected; any later allocation/recovery requires a separate owner plus counsel/risk decision | Protocol owner + counsel/risk | Share math, recovery, migration | Before Phase G | **Owner-confirmed: no automatic allocation; no recapitalization/recovery transaction approved** |
| Reward attribution | Raw shares / live claims / hybrid explicit units | Live-claim-based economic units selected; raw shares remain accounting evidence only and S3 coordination is mandatory | Protocol owner + economics | `CM-033`, `CM-025` | Before Phase G/H | **Owner-confirmed: live-claim units for Phase G specification; Lootbox/interface implementation not approved** |
| Base live-version posture | Migrate before RH / bounded temporary drift / justified permanent exception | Funded ID 3 and live controlled assets make this material; recommend Release 1 Base migration subject to plan | Protocol owner + security/operations | Base vault consumers, VaultBook, manifests | Before Phase I/release | Requested at checkpoint; gates Phase I/release |
| Release 1 Base priority | Hardening requirement / RH prerequisite only / no release | Recommend urgent Base hardening | Protocol owner + security | Containment atomic group | Before implementation track | Requested at checkpoint; gates implementation split |

New Phase F implementation-mechanism/caller decisions, returned because no
current field or selector safely expresses the approved policies and the
transition caller's timing authority requires separate security review:

| Decision | Options | Recommendation | Required before | Status |
| --- | --- | --- | --- | --- |
| External-settlement enforcement | Disable buyer-selected internal settlement for all fungible auctions / add a generic per-asset settlement mode if bounded internal settlement must survive for other assets | Prefer the all-external simplification if product compatibility permits; otherwise approve the narrowly named per-asset mode after Phase I impact review | Any Phase F implementation design | **Returned; no new field, getter, setter, default, migration, or ABI selected** |
| Atomic bad-debt mechanism | Approve the two-selector CreditEngine→Ledger transition in Section 16.10 / approve another reviewed atomic shared-contract design / do not list | Approve the no-new-storage, compare-and-set two-selector design after accounting/security review | Any Phase F implementation design | **Returned; interfaces and implementation not approved** |
| Total-loss transition caller | Permissionless/keeper-callable under deterministic predicates / restricted approved keeper or Department / governed per-transition action | Phase H Section 18.8 compares timing, griefing, liveness, and pause coordination without proposing or selecting a caller | Any Phase F implementation design | **Returned after Phase H analysis; caller policy not proposed or approved** |

New Phase G compatibility decisions, returned because current source derives
claims directly from all custody and existing reward/recovery surfaces cannot
express the approved policies:

| Decision | Options | Recommendation | Required before | Status |
| --- | --- | --- | --- | --- |
| Allocated-backing mechanism | Append explicit allocated/quarantine checkpoint state to a generic share path / deploy a generic vault-level policy variant / another audited mechanism proving `A^s/U^s/A/U` / do not list | Preserve the Section 17 semantics and prefer a generic vault-level boundary over a new Stock-specific contract or token-name branch; assess storage and current positive-rebase compatibility in Phase I | Any Phase G implementation design | **Returned; no storage slot, selector, wrapper, or production vault approved** |
| Quarantine loss ordering | Preserve checkpointed `U` and reduce `A` first / use `U` as shareholder loss insurance / pro-rata reduction | Preserve `U` and reduce `A` first; otherwise the donation is automatically allocated for shareholder benefit contrary to the selected policy. Counsel/risk must confirm this property treatment before implementation | Phase I/accounting/counsel-risk review | **Reference behavior specified; implementation approval pending counsel/risk confirmation** |
| Positive-delta compatibility | Quarantine unsolicited positive deltas in the corrected path / explicitly allocate positive rebases in a separately reviewed generic mode | Do not silently apply quarantine semantics to existing yield/rebase users; separate the generic behaviors explicitly and test both | Phase I source/storage/interface impact review | **Returned; no mode/configuration field approved** |
| Reward integration surface | Reuse live-amount getters with explicit semantics / add an explicit economic-weight getter / global index or other S3-compatible model | Preserve raw shares for accounting, use live claims for economic weight, exclude `U` from global value, and let S3 close interval-boundary mechanics | Phase I plus integrated S3 | **Returned; no Vault/Lootbox/Ledger ABI or storage change approved** |

New Phase H control decisions are returned because current source has useful
fast controls but no dedicated total-loss/checkpoint gate and because broad
contract pauses violate the owner-required repayment-liveness boundary:

| Decision | Alternatives returned | Evidence and recommendation | Owner | Affected components | Prerequisite / needed-before milestone | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Total-loss resolution gate | Reuse existing global `canLiquidate` consumption / rely on broad Department pauses / later consider a dedicated narrow gate / no listing | `canLiquidate` is immediate, fast-disable/governance-enable, observable, and does not gate repayment, but couples resolution to all ordinary liquidation. Broad Teller/CreditEngine/Ledger pauses block repayment or transition dependencies and are rejected as the normal gate. A dedicated gate would be more precise but is outside the no-new-interface/storage authorization. | Protocol owner + security | MissionControl, SwitchboardAlpha/Charlie, AuctionHouse, CreditEngine, Ledger | Owner/security accept an existing control's full blast radius, or separately authorize later dedicated-gate analysis, before Phase I or any Phase F implementation design | **Alternatives returned; existing-control reuse not selected; no dedicated pause proposed** |
| Share-loss checkpoint gate | Require existing asset containment plus reuse an existing global control / broad vault pause / later consider a dedicated narrow gate / no listing | `canDeposit=false` and `canBuyInAuction=false` contain new exposure but do not authorize a checkpoint. Vault pause is immediate but affects every asset in the vault. No clean existing control is recommended; a dedicated gate would require later interface/storage review. | Protocol owner + security/risk | MissionControl, SwitchboardAlpha/Charlie, selected share-vault boundary, Teller, Lootbox | Owner/security accept an existing control's blast radius, or separately authorize later dedicated-gate analysis, before Phase I or any Phase G implementation design | **Alternatives returned; no checkpoint gate or dedicated pause selected** |
| Total-loss transition caller | Permissionless deterministic / restricted existing Department or approved actor / governance per transition / no listing | Permissionless maximizes liveness but creates timing/griefing questions; a restricted existing actor bounds initiation but adds availability/trust; governance per transition is slow and `NUMBER`-dependent. Phase H returns the tradeoff without ranking it into policy. | Protocol owner + security/operations | CreditEngine, Ledger, AuctionHouse, selected resolution gate and evidence event | Resolution gate and caller-discretion/race analysis completed before interface design or any Phase F implementation design | **Returned; no caller policy proposed or selected** |
| Share-loss checkpoint caller | Permissionless deterministic / restricted existing Department or approved actor / governance per checkpoint / combine atomically with a later approved total-loss transition / no listing | Timing determines whether later restoration is quarantined, so caller discretion and observation evidence are property-sensitive. Combining calls may reduce races but would itself be an interface choice. | Protocol owner + security/risk/operations | Selected share-vault boundary, checkpoint gate, Teller, Lootbox, operational evidence surface | Checkpoint gate, property/counsel-risk treatment, and timing analysis completed before interface design or any Phase G implementation design | **Returned; no caller or atomic-combination policy proposed or selected** |
| Incident withdrawal posture | Preserve safe withdrawals asset-by-asset / disable affected-asset withdrawal when delivery is unsafe / broader freeze | Preserve repayment in every normal response and preserve withdrawals when actual delivery is safe. A per-asset freeze is the narrowest current fallback when delivery is unsafe; any broader freeze requires explicit incident evidence. | Protocol owner + security/operations | MissionControl, SwitchboardAlpha/Charlie, Teller/TellerUtils, selected vault and all co-resident assets | Exact delivery failure and blast radius evidenced before any incident action or later runbook approval | **Returned; no production flag action or standing withdrawal freeze approved** |

### 12.3 Decisions explicitly deferred but registered

These must not be treated as approved by the checkpoint recommendation:

| Decision area | Options/recommendation | Needed before | Status |
| --- | --- | --- | --- |
| Deposit measurement boundary | Teller measures the call-local custody delta and passes only verified receipt to the vault; see Section 14 | Phase D completion | **Specified; implementation not approved** |
| Requested/received/excess semantics | Validated transfer attempt `Q`; received/credited `R`; zero, negative, or excess delta reverts; see Section 14 | Phase D completion | **Specified; implementation not approved** |
| Nominal partial loss | Freeze unresolved or owner-approved allocation; never silent pro rata | Phase E/F | Deferred |
| Rounding | Retain `10^8` virtual shares and one virtual asset; deposit down, withdrawal share burn up, claim down, last-share sweep; see Section 17 | Phase G | **Specified; implementation not approved** |
| Emergency disable/re-enable | Section 18 maps the current fast flags and broad pauses, rejects broad Teller/CreditEngine/Ledger pause as the normal resolution gate because it blocks repayment, and returns existing-`canLiquidate`, vault-pause, dedicated-gate, and caller alternatives without selecting any. | Owner/security decision before Phase I or implementation design | **Phase H evidence complete; control/caller selection pending and no live action approved** |
| Vault selection | No production vault selected | Phase I owner gate | Deferred |
| Migration atomicity/rollback | Explicit live users/funds/debt/auctions plan | Phase I | Pending Track 7 |
| Exact-token evidence | Pinned AAPL fork plus behavior-switch/loss tests | Phase J | Pending implementation |
| S1/S2 identical artifacts | Base/RH profiles and checked inventory | Phase J | Pending integrated S1/S2 |
| Audit/release | Atomic group, reviewers, testnet, smoke, soak | Phase K | Deferred |

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

1. `CreditEngine.resolveUserTotalLoss(user, ...) -> transitionedAmount`
   performs the complete Section 16.8 scan, accrues `Y`, pins the Ledger debt
   snapshot, and invokes the Ledger transition. Its caller policy is a separate
   returned decision rather than part of the selected interface.
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
order accounting-safe; it does not by itself decide whether that timing power
is an acceptable product/security property. Before selection, security review
must prove that the caller cannot choose the amount, recipient, collateral
allocation, bad-debt destination, or any value-sensitive eligibility input;
model public-mempool and same-block repayment races; and compare the liveness,
griefing, and operational risk of all three options. The owner must approve the
caller policy separately.

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
transitions, and future Phase I review must ensure an overwrite cannot
accidentally erase bad debt accumulated by atomic transitions.

The two selectors and event/ABI changes are an exact proposal, not an
approval. The caller policy is an explicit unresolved sub-decision. All are
returned to the owner for accounting/security review before any implementation
design. If rejected, the fallback remains: do not list.

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

Phase H Section 18 now closes the evidence/control inventory, rejects broad
Department pause as the normal gate, and returns the existing
`canLiquidate`-reuse, dedicated-gate, and caller alternatives without selecting
them. It defines fast-stop/governance-restart evidence and the repayment-safe
runbook boundary. The final gate and caller remain owner/security decisions;
Phase F may not inherit “Department pause is enough” or assume a dedicated
pause merely because both appear as alternatives.

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
13. the later owner-selected Phase H gate stops and resumes resolution without
    blocking standard repayment, and its exact authority/event/getter/clock
    tests pass; and
14. no new storage, interface, ABI, default, migration, or production behavior
    is treated as approved by this document.

Phase F does not select any returned mechanism or caller/control sub-decision.
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
  wait for a borrower action, but Phase H intentionally leaves its caller
  policy unproposed and unselected.

The caller and selector for a standalone checkpoint are not approved here and
must be resolved with Phase H controls and Phase I interfaces. Tests must
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
`SharesVault` allocates their positive custody changes. Phase I must choose a
generic compatibility boundary—such as a vault-level behavior variant or an
explicitly reviewed generic mode—without a Stock-specific contract,
token-name test, `chain.id` branch, or silently changed existing semantics. No
mode or parameter is approved by Phase G.

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
without letting untouched users accrue stale raw-share weight. Track 6 S3 owns
the interval-floor design; Phase I must reconcile its integrated output before
choosing a Vault/Lootbox/Ledger interface or global index.

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
Phase I decisions.

The existing `amountToShares`/`sharesToAmount` signatures can remain only if
their denominators change from raw `C` to `A`; the existing
`getTotalAmountForUser` is the natural live-claim surface. The current
`getTotalAmountForVault` name is ambiguous because it returns custody for
SharesVault and nominal accounting for Simple. Phase I must choose explicit
getters or a precisely versioned semantic change; no selector is approved
here.

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

That creates a real Phase I choice:

1. append allocated/quarantine checkpoint state to a compatible generic share
   implementation and migrate/reconcile every live asset;
2. deploy a generic vault-level behavior variant that shares canonical modules
   but isolates positive-delta policy;
3. approve another audited generic mechanism that proves the same
   `A^s/U^s/A/U` invariants; or
4. do not list.

Because SharesVault is consumed by both RebaseErc20 and RipeGov and existing
positive-rebase assets may rely on automatic yield allocation, a blanket
semantic/storage change is not assumed compatible. Phase I must map storage
order, module export/runtime artifacts, selectors, events, every reader,
upgrade versus redeployment, Base live state, migration initialization,
rollback limits, and audit boundary before the owner selects an implementation
mechanism or production vault.

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
12. reward interval behavior is reconciled with integrated S3 and does not
    accrue stale post-loss raw-share economics;
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

Decisions required from the owner before Phase I or any implementation design:

| Decision | Alternatives requiring owner direction | Current recommendation/status | Required owner/reviewers | Affected surface |
| --- | --- | --- | --- | --- |
| Resolution gate | Accept the global coupling of existing `canLiquidate` / authorize later analysis of a dedicated narrow gate / no listing | Existing `canLiquidate` is the preferred existing-control candidate, **not selected** | Protocol owner + security | MissionControl/Alpha, AuctionHouse, CreditEngine, Ledger |
| Share-loss checkpoint gate | Reuse an existing global gate / tolerate whole-vault pause / authorize later dedicated-gate analysis / no listing | No clean current control; **no gate selected or dedicated pause proposed** | Protocol owner + security/risk | MissionControl/Charlie, share vault, Teller, Lootbox |
| Total-loss caller | Permissionless deterministic / restricted existing actor / governance per transition / no listing | Evidence and tradeoffs returned; **no caller policy proposed or selected** | Protocol owner + security/operations | CreditEngine, Ledger, AuctionHouse, resolution gate |
| Share-loss checkpoint caller | Permissionless deterministic / restricted existing actor / governance per checkpoint / combine atomically with later approved total-loss transition / no listing | Timing affects restoration/quarantine classification; **no caller policy proposed or selected** | Protocol owner + security/risk/operations | Share vault, checkpoint gate, evidence surface |
| Incident withdrawal posture | Preserve safe withdrawals asset-by-asset / freeze affected asset withdrawal when delivery is unsafe / broader freeze | Preserve repayment always and preserve withdrawals when safe; any exit freeze must be explicit and evidenced | Protocol owner + security/operations | MissionControl/Alpha/Charlie, Teller, vault/co-resident assets |

Approving the control map or one later option would not approve a storage
layout, interface, event, ABI, production vault, implementation, Base
migration, Robinhood registration, or live transaction. Phase I remains
blocked until the owner expressly authorizes it.

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
7. returns resolution/checkpoint gate and caller alternatives without
   selecting any new state/interface/dedicated pause/caller policy; and
8. preserves the `do not list` fallback and stops before Phase I.

## 19. Phases I–K hold

The following are deliberately **not finalized**:

- the owner-returned Phase H resolution/checkpoint gate and caller decisions;
- exact source/storage/interface/migration impact table and the returned Phase
  F/G mechanisms;
- final Phase J validation plan;
- implementation PR split and atomic deployable groups; and
- exact `rh-summary.md` handoff.

Work must not continue into Phase I or later until the owner resolves the
corresponding Section 12/18 gate and expressly authorizes that phase.

## 20. Checklist handoff at this checkpoint

No `rh-summary.md` checkbox is edited or closed.

Eligible for owner review:

- Phase 0, **resolve the deployable Stock Token vault path** (line 85 at the
  `be6a759` reconciliation baseline) — option 4 is the architecture direction,
  but no production vault, implementation, or migration is approved. The item
  remains unchecked in post-bootstrap `ce3805d`.
- Section 4, **finish the Simple versus Rebase comparison** (line 186 at the
  baseline) — Track 5 evidence is hash-verified, source-reconciled, and rerun.
- Section 4, **write a separate vault-change specification if current behavior
  is unacceptable** (line 190 at the baseline) — Phases A–H are specified, but
  the item is not eligible for closure until Phases I–K are owner-directed and
  completed.

Not eligible for closure:

- chosen-vault behavior testing (line 189);
- vault/feed/config/risk-parameter selection;
- issuer-failure implementation evidence;
- the Section 4 exit condition; or
- any technical launch gate that requires a selected vault, production code,
  migration, audit, exact-token lifecycle, or owner approval.
