# PriceDesk gas budgets — contract implementation prompt

This is the original approved revision-7 prompt. The packet was untracked at the
baseline and is now versioned in the designated branch after review. See the
[current handoff](../pricedesk-gas-implementation.md) for follow-up changes and
configuration decisions; historical implementation approvals below are preserved.

Implement configurable per-source quote, snapshot and feed-check budgets with caller-underfunding protection. Move Teller’s Curve reference-pool snapshot call into PriceDesk. **All design decisions below are approved. Deliver contracts and directly related tests only; do not run the full suite.** Base qualification and operations are deferred; [follow-up-qualification.md](follow-up-qualification.md) is background, not work to execute now. Only this prompt and the short test reference are required reading.

Work continuously through steps 1–4, implementation fixes and affected tests. These are sequencing steps, **not review checkpoints**. Do not stop at a plan, pause between steps or wait for interim owner review. Resolve routine choices within this specification and record them in the final report. If a genuine blocker remains after reasonable local attempts, complete all independent work and report the exact remaining issue at the end; never waive a required check or describe incomplete work as passing.

## Workspace and scope

Work only in `/Users/wigglez/dev/ripe-protocol-pricedesk-gas`, branch `codex/pricedesk-configurable-gas`. This dedicated worktree is already prepared from PR #231 head `bdf7f3da7113aabde60ab8eceab6a960a841bb88`; its packet is the current handoff. Verify the path, branch and baseline ancestry, then continue there, preserving existing progress. Do not edit the original checkout or recreate/reset an existing worktree. On another machine, create it only if both path and branch are unused:

```sh
git -C /Users/wigglez/dev/ripe-protocol worktree add -b codex/pricedesk-configurable-gas /Users/wigglez/dev/ripe-protocol-pricedesk-gas bdf7f3da7113aabde60ab8eceab6a960a841bb88
```

Required filesystem permissions still apply. If transferring the packet, use `packet-hashes.json`, excluding `.claude/`; it is absent from the baseline commit and is now tracked with the review follow-up. Eventual integration targets `codex/base-upgrade-fork-rehearsal`; keep the frozen baseline and note upstream drift at the end.

Read PriceDesk, Teller, CurvePrices and their registry/governance interfaces. Change only PriceDesk, Teller’s identified path, necessary interfaces/constructor wiring/ABIs, and related tests. Preserve pricing, freshness, source order, smoothing, conversion/dust floors and genuine-source failure isolation. No live deployment, Safe actions, monitoring tools, other-repository edits, CI work or publication. Describe tests plainly as boundary cases, source availability, permission checks and state consistency; preserve their full technical coverage.

## 1. Establish the Teller relay and check size first

Unchanged Teller’s complete deployed runtime is **24,552 bytes**, leaving **24 bytes** below EIP-170. Implement the minimal relay wiring and dependencies needed to compile first, then deploy locally and measure complete Teller/PriceDesk runtimes, including immutables. Both must satisfy repository size checks. If Teller initially exceeds the limit, make local size reductions within this relay change and remeasure; continue independent PriceDesk/tests work while resolving it. Do not broadly refactor Teller or waive funding/size checks; report any unresolved result at the end.

Add `PriceDesk.addGreenRefPoolSnapshot(_curveSourceId: uint256) -> bool`, callable only by HQ’s current Teller. Teller passes its existing immutable `CURVE_PRICES_ID`, preserving its constructor ABI. PriceDesk resolves its own registry route; absent/disabled routes remain successful no-ops. Otherwise it eagerly proves funding, then calls Curve’s `addGreenRefPoolSnapshot()` using that address’s effective **snapshot** budget.

The relay returns **low-level call success**, ignoring successful return data as Teller currently does. Curve returning `False` is a valid no-op, not failure. Teller uses an ordinary typed call: funding reverts propagate; relay `False` emits Teller’s existing `CurveSnapshotFailed` event and continues. Keep the event on Teller. Do not reuse a helper whose Boolean means “snapshot updated.” Test Curve’s existing authorization with canonical PriceDesk; do not broaden Curve permissions.

## 2. Store and govern budgets

Retain `PRICE_SOURCE_PRICE_GAS` and `PRICE_SOURCE_SNAPSHOT_GAS` public immutable defaults. Append constructor arguments `_priceSourceHasFeedGas` and `_maxSourceGas`; expose immutable `PRICE_SOURCE_HAS_FEED_GAS` and `MAX_SOURCE_GAS`. Preserve earlier argument positions. Validate positive defaults, defaults ≤ maximum and overflow-safe bounds.

Use address-keyed `SourceGasBudgets` with plain `uint256` fields `quoteGas`, `snapshotGas`, `hasFeedGas`; read only the needed field on call paths. Define:

- `setSourceGasBudgets(_source: address, _quoteGas: uint256, _snapshotGas: uint256, _hasFeedGas: uint256) -> bool`: return true after storing; each zero independently resets to its immutable default.
- `getSourceGasBudgets(_source: address) -> (uint256, uint256, uint256)`: effective quote/snapshot/feed values, in that order.
- `SourceGasBudgetsUpdated`: indexed `source`, then `oldQuoteGas`, `oldSnapshotGas`, `oldHasFeedGas`, `newQuoteGas`, `newSnapshotGas`, `newHasFeedGas` (six raw uint256 overrides).

No global-default setter or separate reset method. Each nonzero override must be ≥ its corresponding default and ≤ `MAX_SOURCE_GAS`. Require a nonzero deployed source; allow pre-registration configuration. Overrides follow addresses, survive disable/re-enable, and never transfer to a replacement address; explicit zero resets reused-address settings.

Authorize setters with **`gov._canGovern` only**, including while paused and after local governance relinquishment. Switchboard/protocol membership alone grants nothing. Preserve existing default getter selectors. Floors and immediate setters do not guarantee ongoing source availability.

Keep Base quote/snapshot defaults **1.5M/1.5M**, Robinhood/local **250k/150k**, and feed defaults **75k**. Add provisional constructor maximum **6M** to these profiles. These are unqualified configuration inputs, not measured safe maxima; 3M/3M remains an experiment. Update current fixtures/builders, including `tests/conf_core.py`, aggregate gas fixtures, `config/BluePrint.py` and affected ABIs through `scripts/export_abis.py`. Freeze executed migrations `2026091402`/`2026091403` and deployed-candidate manifests. Preserve historical constructor-position assertions in `tests/test_base_review_safety.py`; add separate current-constructor checks.

## 3. Enforce funding without breaking nested quotes

Keep capped raw calls and exact 64-byte canonical quote decoding. Capture gas immediately before each call; prove full allowance forwarding using overflow-safe EIP-150 rounding and one conservative, compiler-checked `SOURCE_CALL_GAS_OVERHEAD` constant covering intervening instructions, memory and cold access. **No continuation-reserve parameter.** Later parent OOG rolls back atomically.

For ordinary quotes, decide whether proof is required from the result:

- Canonical `(price > 0, true)` or `(0, false)`: accept without requiring full-budget proof.
- Revert/OOG, non-canonical length/Boolean, positive price with false feed, or `(0, true)`: require the saved pre-call proof. Missing proof reverts even non-strict calls; sufficient proof preserves existing statuses/fallback behavior.

Feed checks, both snapshot paths and `qualifyCallerPriceSource` admission use **eager** checks; admission uses effective quote gas. Pass admission’s eager mode explicitly to the shared helper; ordinary quote callers retain conditional checks. A parent isolates nested failure only after proving its own call was fully funded. Never classify underfunding from a source’s returned revert data. No context/depth storage writes on static quote paths.

Review local source/dependency behavior and test gas-dependent canonical replies: this design cannot detect every canonically encoded incorrect answer. Resolve any relevant mismatch within the approved behavior where possible; if it requires a policy change, preserve a focused reproduction, finish independent work and explain the choice in the final report. Deployed historical dependency verification remains deferred.

## 4. Focused acceptance

Use mock priority order `[1,8,2,9,4,5]`, including Chainlink exhaustion → Undy underlying lookup → Undy no-feed revisit → healthy fallback. Test static calls, admission, strict/non-strict behavior, non-canonical responses/revert/OOG/caught-inner failures, governance, bounds, resets/events and address lifecycle. Include repeated/nested failures of one source identity. Preserve independent Robinhood topology/gas guards.

For **each** snapshot path test: `test_d01_due_funded_writes`, `test_d01_due_underfunded_reverts_and_rolls_back`, `test_d01_not_due_is_valid_noop`, and `test_d01_genuine_failure_is_isolated`. Assert earlier snapshot/user writes roll back on propagated underfunding. Restore identical cold pre-state for gas-boundary trials and compare successful state/events with generous gas; inspect neighboring limits and report non-monotonic bands. Boa bisection is local evidence, not RPC-estimator qualification.

Eager checks can require roughly **1.5M gas available at a Base snapshot step even when no update is due**; the moved Curve path now shares its source’s snapshot budget instead of the old 500k cap. Test that consequence explicitly.

Run only the focused lanes in [implementation-reference.md](implementation-reference.md), including conversion-floor regressions and complete runtime checks. Finish with the complete local code/tests in this branch and one concise report: changes, commands/counts, runtime sizes and remaining limitations. Passing these tests completes this contract task; it does not close Base gas qualification, production D01 acceptance or release readiness.
