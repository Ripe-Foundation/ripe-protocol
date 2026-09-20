# Implement configurable PriceDesk gas budgets

Implement governance-settable gas budgets with per-source overrides in the single canonical `contracts/registries/PriceDesk.vy` used by Base and Robinhood. Deliver the contract change, focused tests, Base qualification, a read-only budget monitor and an activation handoff. Configurability is the main deliverable. Complete the three stages below in this task; no separate tasks are required.

The reported trigger is candidate `getPrice(undyUSDC) == 0` while the active desk returns a price. PR #231 already supports constructor-configured quote/snapshot immutables; make recovery possible through governance without another redeployment for each adjustment. Undy cost drift is a hypothesis, not an established cause. Stage 3 **D01** also requires preventing caller underfunding from silently skipping due snapshots; quote parity alone cannot clear it.

Allowed production edits: PriceDesk, necessary ABI/interface declarations, constructor/configuration/migration consumers, and directly related tests/tools/docs. Preserve price arithmetic, freshness, source ordering, smoothing, vault/department logic and source-call ABIs. Pricing-policy alternatives are proposals only. Finish with local reviewable commits or patches. Publication, live deployment, Safe signing/submission/execution and activation require separate authorization.

## Decisions and setup

- **Approved:** normal gas with 1.5× headroom plus one faulty source identity per transaction, including every repeated/nested invocation. This is not a one-failed-call allowance.
- **Pending:** configurable feed checks alongside quote/snapshot budgets, preserving existing defaults. Recommended: yes.
- **Approved:** stack on PR #231. **Pending:** combine narrow-fix/hardening into one replacement branch. Recommended: yes.

The design below describes the recommended combined, three-budget version. Resolve pending answers before treating this draft as final implementation instructions.

Use an isolated `codex/pricedesk-configurable-gas` branch from PR #231's frozen head `bdf7f3da7113aabde60ab8eceab6a960a841bb88`. Its eventual PR targets `codex/base-upgrade-fork-rehearsal`, if publication is later authorized. Record upstream drift; continue at the frozen pin and reconcile the actual integrated tree before deployment qualification. Preserve unrelated work. Copy this entire uncommitted packet into the implementation checkout; it is absent from the pinned commit.

Read [implementation-reference.md](implementation-reference.md) for exact tooling, cold-fork mechanics, test lanes and activation details. Older prompts in `evidence/` are superseded.

## Stage 1 — Contract design and focused tests

Implement independently readable/adjustable quote, snapshot and feed-check defaults with **address-keyed overrides** in local PriceDesk storage. Preserve Robinhood/local defaults **250,000 / 150,000 / 75,000**. Base's **1.5M / 1.5M / 75k** is an unqualified reference; **3M/3M** is a starting diagnostic configuration, not an approved release value. Select Base release settings in Stage 2.

Specify initialization, finite upper/positive effective lower bounds, per-field inheritance/reset, getters and old/new events. Preserve the PR's public allowance getter selectors where practical; separately expose effective per-source values. Select actual numeric bounds from qualification, not arbitrary large maxima. Use `gov._canGovern`: recovery setters remain usable while paused and by HQ governance after local governance relinquishment. Test unauthorized callers. Use immediate governance updates without a new budget timelock, preserving existing registry/source timelocks. Any separate continuation reserve must be readable/adjustable within proved safe bounds; no setting may disable funding protection.

Explicitly pack the three override fields into one `uint256`, with another word for defaults, validated widths/masks and zero-as-inherit semantics. Vyper does not automatically pack a small-integer struct. Load the override once; inheritance can require a defaults read. Verify compiled layout/reads. Test independent updates, boundaries, overflow, clearing and round trips. A demonstrated correctness or material maintenance cost can justify a simpler layout with recorded measurements/tradeoffs.

Overrides follow addresses, never slot numbers. Define removal/replacement/re-registration and changed-code behavior, including candidate qualification before registration. Admission and execution use the same effective quote budget. Default updates preserve explicit overrides and predictably update inherited fields.

**Approach one: the same pre-call funding check in every PriceDesk frame.** Before each bounded quote, feed-check and snapshot call, prove sufficient gas to forward its full effective budget and retain the required continuation reserve. Adapt [Optimism SafeCall's minimum-gas principle](https://github.com/ethereum-optimism/optimism/blob/develop/packages/contracts-bedrock/src/libraries/SafeCall.sol), retaining exact bounded forwarding rather than its forward-all-gas helper. Derive overhead from compiled Vyper: EIP-150 rounding, cold access, memory, intervening instructions and bounded return-data handling. Do not copy its Solidity buffer unchanged.

A failed check reverts that frame, including non-strict calls. A nested desk failure inside a fully funded source remains an isolatable source failure at the parent. No root/nested classifier, membership shortcut or static-path storage/transient writes are needed. Healthy nested routes must still fit parent budgets. Parent ≥ child is insufficient: model repeated dependencies, prior fallbacks, overhead and cycles. Preserve healthy fallback after genuine source failure.

A post-call retained-gas threshold alone cannot prove full forwarding when a source catches an inner failure and returns/reverts with gas left. Test that case; this is a PriceDesk composition requirement, not a claim of an OpenZeppelin vulnerability. Approach one is production-eligible if its compiled argument and acceptance matrix pass. Allow one evidence-driven alternative within scope. Remove the old four-hour cutoff. After two genuine design failures, deliver the smallest concrete scope decision and complete unaffected work. Harness errors do not count as design failures.

Focused acceptance covers strict/non-strict `getPrice`, `getUsdValue`, `getAssetAmount`, ETH helpers, standalone sources, registered/unregistered callbacks and qualification; caller-gas boundaries; revert/malformed/OOG sources followed by healthy fallback; caught inner failure; full-ring/nested/cyclic routes; override lifecycle; governance/packing/bounds; feed checks; due snapshots versus valid no-ops; and rollback of earlier snapshot/user writes when funding failure propagates. Distinguish genuine source failure from caller underfunding.

Deliver code and focused results before the full measurement campaign. Keep both chains' constructor/ABI consumers coherent. Early baseline reproduction is useful; immutable-only sweeps are not a prerequisite to setters.

## Stage 2 — Base measurements, values and monitoring

Reuse `scripts/diagnose_base_undy_prices.py` and `scripts/base_full_update_fork.py::FullUpdate`, respecting the reference's block/fixture caveats. Investigate the historical failure and qualify separately at a fresh finalized pin. Inventory **all** configured Undy assets, expressly undyUSDC, undyAERO and undyUSD. The reviewer reports 1,719,201 gas and near-cap AERO/USD cases; reproduce or retain frame-level provenance. Refresh the historical ~$40.6k exposure before calling it current.

Verify quotes and conversions for every supported asset through its configured sources. Measure consumed gas and minimum correctly executing caller limits from identical cold states, authenticating callbacks to the replacement. Exercise mature rings, supported vault-state growth, actual dependencies and final department/retained-vault composition. Use 1.5M/2M/3M/6M quote/snapshot points where useful to locate boundaries, including the 150k snapshot baseline. Vary budgets independently; avoid a mandatory Cartesian sweep. Remeasure the selected storage/guard configuration and its overhead.

Choose source budgets with at least 1.5× worst measured cold minimum-required forwarding headroom over supported states; increase for observed variance. Solve/retest dependencies at final settings. A reported measurement is not invariant. Uniform 3M is not pre-rejected under the new fault model, but remains unqualified and may waste fallback gas. Per-source configurability remains required even if uniform defaults fit.

**Transaction acceptance:** qualify normal operation with 1.5× measured gas headroom, then each possible single faulty identity exhausting its full allowance on every reachable invocation. Include new fallback work, repeated quotes, feed/snapshot calls, intrinsic and non-pricing gas. Build disjoint call-tree bounds: nested work consumes its enclosing allowance, not an additional copy. Also cover the minimum outer gas needed by pre-call checks. Require the worst bound to fit `floor(0.80 × T)` for the verified transaction ceiling `T`, retaining 20% reserve. Recorded Base `T = 16,777,216` gives **13,421,772**; verify current rules/submission constraints, not Robinhood's envelope.

Document the fault-bound calculation and validate with exhausting mocks and complete transactions: deposits/withdrawals, borrowing/valuation, liquidation, deleveraging, snapshot-producing actions, multi-asset positions and keeper batches. Healthy fallback is required where an independent valid route exists; losing the only valid source need not yield a positive price. All-source exhaustion remains correctness stress coverage, not the selected transaction-liveness promise.

Qualify actual defaults/overrides and their admitted upper-bound configuration against the selected fault model, topology, state envelope and supported batch sizes. Setter bounds ensure valid encodings/funding arithmetic, not automatic qualification of every governance-selected combination. Publish qualified configurations and requalification triggers. A failed admitted-bound test requires revised bounds/design or an explicit owner decision, not a hidden waiver. Identify endpoints/batches that cannot meet the selected model instead of omitting them or relaxing margins.

Add D01 coverage using real `eth_estimateGas`: from identical pre-state, its returned limit must produce the same due snapshot/user-state transition as a generous limit. Test the submitted buffered limit too, including feed-check underfunding, later failure and atomic rollback. Receipt success is insufficient.

Preserve Robinhood defaults, source-count/topology guards, independent aggregate-gas ceilings and qualification tests. Remeasure new lookup/guard overhead; unchanged values are insufficient. Keep complete deployed runtimes within repository EIP-170 limits. The reference lists existing lanes and marker handling.

Deliver a **read-only monitoring CLI**, with human/JSON output and an approximately **70%** budget-usage warning. Cover quote/snapshot/feed frames across configured assets/sources at a recorded block. Report source/kind, effective allowance, frame consumption/minimum-required estimate, utilization and provenance. Failed/exhausted/unknown measurements are explicit, never zero usage; missing coverage or unresolved dependencies produce warnings. Whole-quote gas is not per-source gas. Use supported tracing or reproducible fork probes and document limits. No scheduler/external notifications are authorized. Monitoring supplements qualification; it cannot guarantee intervention before failure.

## Stage 3 — Rehearsal and activation handoff

Reconstruct registry IDs/order/disabled state, governance, budgets/overrides and scales through the reference checklist. Preserve ETH/sentinel handling and retained-vault coverage. Rehearse deployment/setup and governance proposal/confirmation on a pinned fork with final artifacts and intended stack. Bind source/tree, compiler inputs, complete runtime, configuration, block/hash and tests. Existing Stage 2/3 upgrade gates remain independently applicable.

Treat the old **nonce-477 slot-7 proposal as a separate owner action now**, not something that waits for these stages. Refresh status and provide precise hold/removal/replacement instructions without modifying the Safe. Changed calldata needs a new hash/signatures; on-chain re-proposal semantics differ. The reference contains historical addresses/evidence. Canonical active manifests change only after separately authorized activation; label candidates distinctly.

Write `docs/chains/base/pricedesk-gas/README.md`, `decision-log.md`, `qualification.json`, `activation-handoff.md` and sanitized `evidence/`. Include reproducible monitor/test commands, counts, supported limits, unresolved dependencies and provenance. Preserve prior artifacts. Completion means implementation plus meaningful passing evidence for the claimed configuration; an investigation report alone does not complete the contract task. Live activation remains separate.
