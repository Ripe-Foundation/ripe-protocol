# Deferred Base qualification and integration

**This is deferred release work, not part of the implementation/review follow-up.** The owner’s gas margins and release invariants remain in force. No live action or new operational tool is authorized by this document. Previous detailed leads are preserved in [the archived revision-5 reference](evidence/planning-v5-reference.md); its superseded design and active-task instructions do not control.

1. **Bind the final implementation and deployed dependencies.** Reconcile PR #231 drift, then pin final tree/build, constructor values, source addresses/implementations, priorities, retained dependencies, assets and state at a fresh finalized Base block/hash. Reproduce the reported undyUSDC issue separately from historical observations. Authenticate gas-sensitive catches/default returns throughout source dependencies before approving conditional quote checks. Historical priority `[1,8,2,9,4,5]` is a mock input, not a complete current inventory.

2. **Qualify source budgets and complete transactions.** Source budgets must cover ≥1.5× measured cold need; normal transaction allowance must cover ≥1.5× measured total gas and actual forwarding requirements. Model one faulty source identity exhausting/failing on every repeated or nested invocation, including selective failures that expose more work. Count disjoint exhausted envelopes once, plus 1.5× remaining healthy work, forwarding overhead and intrinsic costs. Do not double-count nested calls or multiply already-budgeted faults again. Require the maximum normal/fault bound within 80% of the applicable Base transaction cap. The recorded 16,777,216 cap gives 13,421,772 allowed and normal consumption ≤8,947,848; verify current chain/client limits before using those numbers. Measure supported batches and indivisible positions; do not silently exclude unsupported ordinary exits. The provisional 6M maximum and all defaults/overrides remain unqualified until checked under this model. Raising a maximum requires a new deployment; overriding within it still requires qualification.

3. **Retain the Pool-1 gate.** Apply [legacy-pool-claim-qualification.md](legacy-pool-claim-qualification.md) to the final composed release. Its full fork/claim matrix is deferred from the present contract task; local arithmetic preservation remains in scope now. Refresh every actual claim by full address and balance, including mcbETH and undyAERO. Qualify cold complete legacy flows, repeated pricing/readiness scans, five floor-dependent values and the naturally one-wei AERO case. The unchanged supplement’s “implementation agent” wording refers to the later release qualification phase after this scope split; its invariant is not waived.

4. **Close production D01 and caller compatibility.** Use a compatible Base fork/client’s actual `eth_estimateGas`, identical pre-state/sender/calldata/value/access list and due-state assertions for both snapshot paths. Compare estimated, submitted buffered and generous limits. Boa boundaries alone cannot close this check. Bind the final replacement through every callback, mature ring and retained source. Then assess frontend, wallets, keepers and on-chain integrators; prepare any cross-repository changes separately. Preserve Robinhood source/default compatibility without live redeployment.

5. **Prepare operational follow-up only when commissioned.** Monitoring, caller gas tables, recovery procedures and full deployment rehearsal belong here. Prior monitor preferences were 70% warning/85% critical with explicit unknown coverage and nested-route fit. Requalify after relevant code, source, budget, priority, dependency, ring/batch or chain/client changes, including Base gas repricing or changes to cold-access costs. Recheck the compiled `SOURCE_CALL_GAS_OVERHEAD` proof after these changes, compiler/optimizer changes, or call-path changes. Floors and reset-to-default are not permanent availability guarantees.

6. **Reconcile both replacements before activation.** Moving the Curve call changes Teller as well as PriceDesk: HQ slots **7 and 17** need newly built, configured, authenticated candidates. Confirm the compatible PriceDesk in slot 7 before Teller in slot 17, or both atomically with slot 7 first. A new Teller paired with an old PriceDesk reverts in housekeeping. During rollback, remove the relay Teller before restoring an incompatible PriceDesk. Keep entry points closed until the complete stack is qualified. Refresh actual HQ/Safe state and the historical nonce-477 batch; never treat its archived status as current. A proposal is not activation; inspect later confirmations and the full dependency graph. The historical PriceDesk source-registry delay was zero, while HQ replacement delay was 21,600 blocks. Do not conflate them. Preserve old manifests/executed migrations, prepare new deployment artifacts separately, simulate the final complete stack and obtain the distinct authority needed for live actions.

7. **Preserve all effective budgets when editing one.** `setSourceGasBudgets` replaces all three fields; zero resets that field to its immutable default. Read `getSourceGasBudgets(source)`, change only the intended value, submit all three effective values, and verify all three after execution. See [the committed handoff](../pricedesk-gas-implementation.md) for configuration decisions, exact local commands, margins and limitations.

8. **Keep rehearsal drafts outside the live migration queue.** The current bodies live in `scripts/rehearsal/base_candidates/` and are loaded by path. Their per-profile overrides are provisional and must be applied to the exact source addresses and read back before relinquishing setup governance. Retain Base's 1.5M/1.5M immutable floors for the approved implementation and rehearsal scope. Production qualification and any owner decision to lower those floors remain separate; no later lower-floor decision is recorded. Record the final decision and its date when established. Lowering a deployed floor requires a replacement PriceDesk; source overrides cannot accomplish it. Qualify any proposed replacement floors together with Curve snapshot and both Undy quote/snapshot overrides. Add any final production migration only after qualification and separate deployment authorization, with fresh timestamps and labels.

Missing external evidence keeps these release checks open. It does not prevent delivery of the scoped contract implementation and its focused tests.


## Complete production route inventory

This inventory is **not yet complete or qualified**. For every final enabled source
and priced asset, record the profile, registry slot/address, implementation/code
hash, constructor/config readback, priority order, underlying dependencies,
recursive PriceDesk entry points and catch/default-return behavior. Include
admission, snapshot and quote routes where applicable. Record disabled/absent
sources explicitly; do not infer them from test fixtures or deployment labels.
The [selected source examples](../pricedesk-gas-implementation.md#remaining-release-work-and-limitations)
cover Curve, Undy, BlueChip, wsuperOETHb, conditional RedStone and retained legacy
Aero. Authenticate legacy Aero independently of the current monitor source.
Qualify repeated and nested faults across the final inventory, including supported
batches, ordinary exits and indivisible positions. These requirements do not
claim that all deployed routes fail.

## D01 caller and estimator evidence matrix

**D01 remains deferred.** Use one row per caller/entry point and relevant state
combination on a compatible Base fork/client. Repeat each comparison from the
same snapshot. Actual RPC estimation and complete submitted transactions are
required; a local Boa execution boundary is insufficient.

| Evidence field | Required record |
| --- | --- |
| Caller / entry point | Frontend transaction builder, wallet and buffering policy; keeper; liquidation executor; on-chain integration including Appraiser; target and function selector. Identify any callback or intermediary. |
| Snapshot path | Generic per-asset, reference-pool relay, or both; concrete source address and effective allowance at every enclosing call. |
| State dimensions | Due versus enabled-source no-op; absent/disabled control; new/partially filled/full or mature ring; asset count, batch size and relevant position size. Record the assertions proving the selected state. |
| Identical inputs / pre-state | Finalized chain/block/hash, saved fork snapshot, sender, target, calldata, value, access list, timestamp/block progression, balances, allowances, observations and cold transaction state. Restore all of these before each trial. |
| Gas limits | Actual `eth_estimateGas` RPC request/result and client version; caller's buffering formula and submitted allowance; generous comparison limit; measured total gas and applicable chain/client cap. |
| Outcomes | Success/revert and reason, source/callback trace, snapshot update or genuine no-op, and full state/event comparison across estimated, buffered and generous trials. Include accounting/rollback and gas-dependent success differences. |
| Final binding | Commit/tree, compiler/optimizer/build, deployed code hashes and immutable data, PriceDesk/Teller/HQ slots, source/dependency implementations, feed configuration, priorities, raw/effective budgets and acceptance evidence. |

At minimum, include frontend/wallet deposit, withdrawal, borrow, repayment and
claim routes; keeper maintenance/snapshot routes; liquidation callers at supported
batch/position limits; and integration/Appraiser valuation paths with their actual
snapshot/callback composition. Record a reason when a caller cannot reach one
snapshot path rather than fabricating coverage. Vary due/no-op/ring state and
batches only where relevant, and include the repeated/nested fault model from
item 2. An enabled-source no-op still reaches the eager funding check;
an absent/disabled source returns earlier. They are distinct evidence rows.

## Integration and runtime binding

The 2026-09-20 refresh found PR #231 open with changes requested and PR #232 a
draft on its parent branch. Parent merge, retargeting #232 to `master`, and renewed
integration validation remain later actions. An eligible PR or merge-group run
must execute and pass `rh-pr-gate`; manual dispatch skips it, and retargeting alone
is not guaranteed to trigger the workflow's current event selection.

Preserve the complete deployed-runtime checks: Teller **24,488 bytes**, with
**88 bytes** remaining, and PriceDesk **19,541 bytes**. Rebuild/remeasure for the
final integration and after compiler/optimizer/code changes, alongside the
compiled forwarding-overhead proof described above. Historical harness hashes
cannot reconstruct missing original harness bytes. Source review and successful
local tests do not authenticate deployed dependencies or authorize activation.
