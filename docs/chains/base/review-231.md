# PR 231 review disposition and remaining gates

This is the current review checklist, not authorization to deploy or activate.
Historical migrations remain frozen. New diagnostic code does not supersede
historical results unless it has actually been rerun with identified inputs.

## Owner-directed follow-up scope (second review)

The owner requested practical diagnostic/reporting fixes, no additional migration
test suite, no new recovery framework, and no further contract changes. This is
a scope decision, **not reviewer approval or resolution of declined requests**.

- **C11:** Keep the existing journal-based resume mode. Inspection confirms it
  authenticates resumed deployment source/code and rejects source drift. Resume
  with unchanged reviewed sources is different from regenerating Defaults after
  a partial Stage 2. The latter remains unsupported: preserve the journal and
  candidate records, do not force-replay or skip the unfinished stage. The requested
  abort/supersede framework is deferred by owner direction; C11 remains open.
- **C14:** Stage 3 now checks the reviewed existing slots 1–9, exclusive count 10,
  named source bindings, and the disabled BlueChip address. No new feed types or
  registrations are introduced by this follow-up. Full retired-source event-history
  authentication is deferred; these lightweight checks do not close C14.
- **D05/D06:** No additional migration integration suite or broad caller-level
  test expansion in this pass. Existing checks and focused diagnostic smoke checks
  are used; the review's requested coverage remains outstanding.
- **D01:** A successful deposit with a due snapshot skipped through caller
  underfunding is **not accepted as qualified behavior**. Genuine source failure
  and not-due snapshots remain distinct cases; an aggregate Boolean is not proof
  of per-source refresh. No contract enforcement change is made in this pass.
  **Stage 3 must remain blocked** until the underfunding policy/enforcement and
  four-case regression are agreed and any required immutable PriceDesk change is
  implemented. Merely increasing a wallet gas setting does not close this issue.
- **D14/D15/D20:** Keep the conservative preflight guard: Stage 2 requires a frozen
  reviewed checkout. Any fingerprinted input change requires fresh verification.
  Optional verifier hygiene and cosmetic refactors are deferred.

Practical corrections in this follow-up: separate execution failures from
qualification gaps; serialize contract arguments; label historical permission
coverage unknown; improve credential redaction without replacing normal network
selectors; hash consumed saved-input bytes; fingerprint before initial RPC;
record rollback separately from call failure; handle throttling with bounded
backoff rather than range splitting; and record snapshot user calls and complete
capped/direct snapshot equality. These changes do not rerun historical evidence.

Validation for this scoped follow-up: 30 existing focused checks passed. Ad-hoc
offline smoke checks passed for the three reported credential cases, preservation
of `network=base` identifiers, qualification-gap continuation, bounded throttling
and actual Boa-contract serialization. Read-only RPC checks confirmed the existing
source slots 1–9 and exclusive count 10 at finalized Base block **51,359,409**.
No live transactions, new migration tests, contract-source edits or historical
migration edits were made. The full upgrade and snapshot fork diagnostics were
not rerun in this pass.

## Implementation still required before this PR is ready

- **C06:** Snapshot forwarding now has a separate nonzero immutable and profile
  budget (Base 1.5M staged, local/Robinhood 150k unchanged). The isolated snapshot
  diagnostic uses block 51,312,366 and actual live Teller operations. The
  [targeted regression](fork-rehearsal/snapshot-refresh-review-20260915.json)
  passed: 150k did not refresh; 1.5M and direct calls advanced state; two actual
  Teller withdrawal/deposit cycles refreshed, prices remained usable, and stale
  snapshots expired. Final replacement-Teller and full
  operation qualification remain separate. Do not call the whole upgrade qualified.
- **C10/C11:** Complete representable MC readback is shared with the verifier.
  Stage 2 now runs mandatory fresh-finalized-block verification in a separate
  process, using the deployment RPC and exact selected Defaults path. It binds
  contract/interface inputs, verifier scripts, configuration, the Stage 2 script
  and canonical manifest by SHA-256; checks the block hash again; and rejects
  intervening artifact changes before each deployment. The verifier also checks
  that manifest MC is still active in HQ slot 5. It never calls `verify()` in the
  runner process, which would replace Boa's environment. The fork adapter uses
  its explicit historical pin and labels that evidence historical-only.
  **Post-deployment drift recovery remains open.**
  Preserve every journal, receipt, source identity and candidate address. An
  interrupted Stage 2 must not be force-replayed, marked complete artificially,
  skipped, or retried against regenerated Defaults. An authenticated, tested
  abort/supersede lifecycle is required before Stage 2 can be offered as ready.
- **C14:** Slot/address guards are now present, including allocated IDs 1–9,
  exclusive `numAddrs() == 10`, slot 3 zero and named manifest bindings. Complete
  retired BlueChip history authentication before Stage 3 broadcasts remains open:
  decode authenticated old-PriceDesk disable history for BlueChip at ID 3.
  Membership alone is not sufficient. Reconcile all later registry events at
  the selected finalized block; do not treat ID 10 as an existing source.
- **C18:** Four isolated standard-runner ordering regressions now cover refusal
  with 2026082400/01 unfinished and ordered staging acceptance after the runner
  itself completes synthetic prerequisites. Their bodies intentionally do no
  deployments: these prove routing/checkpoint behavior, not actual candidate
  deployment or interrupted Stage 2 recovery. Those remaining lifecycle scenarios
  still require coverage. Do not modify real completion history to advance.

### Follow-up preflight validation

- 30 focused preflight, verifier-coverage and review-safety tests passed.
- 869 deployment tests passed (13 intentionally deselected), followed by four
  additional standard-runner ordering tests passing.
- The actual subprocess preflight passed against the existing Defaults artifact
  at historical Base block **51,318,877**, hash
  `0xc3fb0c9e51cbeb6472b2476c4576a755effcc9bfb98812d7734e2ba5eefac6a5`.
  This was a read-only fork check, **not** fresh-finalized deployment clearance
  or a rerun of the full upgrade rehearsal. No live transactions were sent.

## Implemented review changes (with scope limits)

**C02 timing disposition:** preserve the active restrictions for this candidate;
the pending VaultBook's lower floor is not adopted. Reconcile any live drift
before deployment; the staging scripts check both selected live and new floors.

| Contract | Active minimum (blocks) | Pending minimum | Selected candidate minimum |
| --- | ---: | ---: | ---: |
| VaultBook | 21,600 | 3,600 | 21,600 — preserve active |
| CurvePrices | 14,400 | none reviewed | 14,400 — preserve active |
| Disabled BlueChip | 21,600 | none reviewed | 21,600 — preserve disabled source floor |
| Other checked sources | 3,600 | none reviewed | 3,600 — unchanged |

- **C01/C03:** HR uses HQ min/max 43,200/302,400, with readback. Lootbox's named
  immutable minimum is 43,200, with copied current interval/reward readbacks.
  HR's mutable delay still starts at zero: set and verify the approved production
  delay during activation, not in deploy-only staging.
- **C04:** Quote budgets live in profile parameters, with explicit production
  binding guards; Base's 1.5M remains staged/unqualified. Normal local/Robinhood
  fixtures use 250k and are not evidence for Base's larger envelope.
- **C08:** Reserve constructor fields are annotated with units. They are
  unapproved dormant placeholders. Before *any* allocation, mint permission,
  acquisition or sale, replace and read back the complete approved configuration,
  then separately approve enabling the paused/not-running engine and vesting.
- **C15:** Entry points reject optimized Python before RPC/deployment work.
  Transactions are outside assertion expressions; returned IDs are explicitly
  checked. This includes the older compatibility probe.
- **C17b/C20/C21:** New reports identify constructor arguments/profile, project
  input hashes (including selected Defaults), dirty status and tool versions.
  Rolled-back diagnostic calls have branch IDs and `reverted: true`.
- **C22a/b:** Explicit diagnostic CLI, help before RPC, output overwrite opt-in,
  finalized pin/hash and expected oracle cases; pending proposal replacement is
  fork-only and opt-in. Fatal/incomplete and completed/unqualified are distinct.
- **C24:** Required child failures fail the parent; Curve green-reference and
  wrapped immutable readbacks added; price exceptions retain categorized causes.
  Retired routes remain unresolved until their exposure dispositions are approved.
- **C25:** Booster user/config/usage readbacks added, zero-case coverage explicit.
  PSM transfer flag depends on positive share conservation, not an unconditional
  assignment. Underlying before/after spans the wait and may accrue; raw token
  conservation is the invariant. HR totals are labelled Ledger-backed totals.
- **C27/C28:** Debt remediation and locked-user migration coverage remain separate;
  healthy locked users are not automatically repaid. Census reconciles the union
  of vault inventory/user-slot assets and flags orphan/unreadable totals, including
  cached census input. Regression cases cover live/saved audit populations with
  unhealthy borrowers, healthy locked borrowers and locked debt-free depositors.
- **C29/C30/C31:** Recursive RPC/path sanitization, bounded/adaptive log retrieval,
  range-completion records, authenticated HQ/Switchboard emitter discovery, and
  ABI-layout validation. Unsupported generation/history coverage must remain
  unknown, never be advertised as complete permission continuity.

## Required before deployment / cutover

| Review | Gate and completion criteria |
| --- | --- |
| C05 / D18 | Qualify final replacement-Teller deposits/withdrawals, borrow/redeem/liquidate/deleverage and batches with actual source ordering/nested routes and combined quote/snapshot work. Include real RPC estimation, supported wallet/caller buffers, insufficient caller gas versus genuine source failure, D01 policy enforcement, exhausted/malformed sources, and atomic rollback above supported batch sizes. Record measured limits for the final candidate combination under Base's 16,777,216 ordinary-transaction maximum. Execution-gas observations are not RPC estimates. D01 immutable-code requirements block Stage 3, not merely activation. RH DER-T01's 250k/32M envelope is not Base evidence. |
| C07 | For EURC/undyEURC repeat registration/pricing with legitimate fresh observations across the governance wait, without weakening stale limits. For mcbETH/VVV inventory positions and redemption exposure before retiring routes (VVV retains redemption config). For every route record old/final source, config, exposure, expected pricing and retain/retire disposition. Aero stays UI-only with reviewed frontend monitor address; BlueChip stays disabled. |
| C12 | Reconciled 2026-09-18 by explicit operator authorization for completion through the old system. Existing activation checker passed at finalized Base block 51,478,064; the adjacent history evidence records all 54 getter results and source/manifest hashes. Empty 2026082400/01 contract maps record no deployments and remove the Stage 1 ordering blocker. Original receipts were not reconstructed; neither newer migration body nor live wiring was replayed. This is not full upgrade qualification. |
| C16 | Before promotion, restrict deletion to `consumed_labels` and test partial promotion preserving unrelated candidates/Defaults/Contributor. Authenticate Contributor with blueprint-aware code checks and read back MC's template; never invent an HQ slot or use ordinary-runtime validation. Staging does not call promotion. |
| C23 / D21 | Inventory all pending registry additions/updates/disables/governance, controllers/HR queues and separate mechanisms, source feeds/configuration queues, and controller proposals affecting Endaoment/PSM. Each entry records mechanism, target, proposed change, initiation/confirmation/expiry timing, pinned status and disposition. Use authenticated history to include proposed new keys absent from active lists. Reconcile unique discovered count with decoded plus unsupported count, then decoded count across non-overlapping status categories. Unsupported/unreadable entries remain unknown. Tests must include pending new registry and feed entries. |
| C26 / D22 | Reward sampling is explicitly limited/deduplicated and compares total and borrow components. Record candidate and sampled population counts, exclusions, unreadable cases and actual nonzero cases exercised. Retain equivalent-state before/after values and quantified differences for total and borrow rewards; approve/correct differences. An all-zero sample cannot establish nonzero reward continuity. A sample is not complete continuity. |
| C32 | ERC20-like three-topic Transfer logs plus native balances are not all-asset custody coverage. Classify every discovered holding; record readable balance or unknown, and transfer/retain/defer disposition. Three unreadable contracts remain unknown; sixteen unreviewed assets remain untouched. If NFTs are in scope, inventory ownership with the appropriate interfaces. Required transfers need token-unit conservation and zero relay residue; discovery never authorizes unsolicited-token transfers. |

## Evidence attribution (C19/C20)

All five JSON files below have block 51,312,366 and **not-qualified** scope.
They are historical, not a complete execution of the current source combination.

| Artifact | Actual scope/version limitation | Superseding evidence |
| --- | --- | --- |
| full-update-wave1.json | Early full wave-one diagnostic; embedded per-contract/source hashes, not complete input provenance | full-update-final.json for that subsequent historical run only |
| full-update-final.json | Historical 45-deployment/custody/1,029-position/55-debtor checks. PriceDesk deployed size 17,742 and source hash prefix `47f5e723`; not the immutable candidate. Old Aero blocker remains in this artifact. | Narrower oracle runs below do not rerun custody/positions. Aero collateral interpretation is superseded by agreed UI-only treatment. |
| oracle-registration-replay.json | Historical oracle-only replay, not custody or user migrations | oracle-registration-replay-v2.json |
| oracle-registration-replay-v2.json | Historical 27/31 registrations; not fresh/final-route qualification | Isolated quote diagnosis for its limited cases |
| undy-price-diagnosis.json | Isolated 1.5M quote-budget experiment (17,828-byte PriceDesk generation); no enlarged snapshot allowance or full-operation qualification | New snapshot regression only when its result is recorded and passing |
| snapshot-refresh-review-20260915.json | Targeted snapshot evidence with dirty bd7d922f provenance; seven fingerprinted inputs differ from da510218, while PriceDesk, BluePrint and snapshot diagnostic match that reviewed head. Retained live Teller and experimental deployment/timelock setup; 17,898-byte candidate, not the historical 17,828-byte quote experiment. | Not a full final-candidate qualification. Later diagnostic/reporting edits have not rerun this preserved artifact. |

Truncated historical hashes are identifiers, not complete authentication. Full
input provenance was not recovered for these historical runs. Dirty-tree future
runs are usable when their complete input fingerprints are retained.

Sanitization disclosure: between commits `55876cd7` and `bd7d922f`, each of these
five reports had one error string's local repository prefix shortened. Other
parsed values were unchanged. This was a post-processing pass (legacy local-path
redaction v1), not a rerun. New reports record `fork-report-v3` and redact nested
RPC credentials/path forms during output. Historical files are not overwritten.

## Historical constructor compatibility (C17a)

Related prior work: [PR 152](https://github.com/Ripe-Foundation/ripe-protocol/pull/152).
The constructor-selected budget is a change from that fixed-stipend design, not
evidence of approval under it. Base's 1.5M quote and 1.5M snapshot budgets are
staged/unqualified; Robinhood stays at 250k/150k. The snapshot change repairs a
different bounded call path than quotes. This note does not claim or reallocate
RH-D042. RH-D042 refers to the earlier PR #152 isolation work; that decision does
not qualify or approve the new Base budgets.

Current PriceDesk requires **seven** constructor arguments (six at bd7d922f).
Frozen replay requires matching historical sources or an explicit adapter.

| Historical file | Original argument count |
| --- | ---: |
| base-mainnet/1007_PriceDesk.py:12 | 4 |
| base-mainnet/2025071503_PriceDesk.py:12 | 5 |
| base-mainnet/2025072301_UpdatesForUnderscore.py:10 | 5 |
| base-mainnet/2025112400_New_Price_Desk.py:12 | 5 |
| base-mainnet/2026030500_New_Price_Desk_ETH_fix.py:12 | 5 |
| robinhood-mainnet/0003_PriceSources.py:63 | 5 |
| robinhood-mainnet/2026082100_RedeployDepartments.py:361 | 5 |
| robinhood-mainnet/2026082405_RedeployPr208.py:111 | 5 |

## Optional dispositions (C09/C33/C36)

- C09: Fresh blueprint authentication is deferred: the fresh path is controlled
  by `deploy_bp()`, and resumed blueprints already compare exact authenticated
  EIP-5202 creation bytes. Do not weaken that resume check. Defaults zero-template
  rejection remains enforced. Blueprint activation still requires C16.
- C33: Borrower renderer metadata resilience/output-stem polish is deferred;
  it is not used by deploy-only staging. A metadata exception must not be read as
  an empty/zero position report. Do not overwrite historical rendered reports.
- C36: New blueprint reports include deployed size/code hash. Empty blueprint
  labels are rejected; omitted labels retain name. Starved quote strict-path
  assertion added. Runtime baseline is recalculated after contract changes;
  bd7d922f's 17,828 bytes remains a historical observation. Broad cosmetic
  refactoring is deferred, especially AuctionHouse/Deleverage (12/17-byte
  headroom). No changes to their code were made for this review.
