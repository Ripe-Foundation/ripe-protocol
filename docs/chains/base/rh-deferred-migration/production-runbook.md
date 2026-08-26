# Base RH Deferred-Migration Production Runbook

> **DRAFT — DO NOT EXECUTE**

**Purpose:** operator-oriented planning and execution checklist for replacing the
Base protocol departments with the reviewed RH generation while preserving the
deployed Ledger and deferring user-position migrations.

**Status:** draft architecture and operator checklist; **not execution-ready and
not authorization**

**Planning source anchors:**

- Base legacy source: `91eda49ccd34a25090582aff0695075c4c806011`
- Reviewed RH candidate: `5c30234e855cd8cbb54d199aef48e5ee07538244`
- Local `origin/rh` observation on 2026-08-25:
  `853214fd4c986dd176be63b15b9336caf22fd662`; its delta from the reviewed
  candidate changes migration history/tooling/tests, not `contracts/`, but it
  is still not a production release lock.
- Legacy Base RipeGov: `0xe42b3dC546527EB70D741B185Dc57226cA01839D`
- Legacy RipeGov VaultBook ID: `2`

These commits are evidence anchors, not a release lock. Bind a fresh release,
deployed runtime, and finalized Base block before preparing any payload.

> This document authorizes no deployment, Safe transaction, registry update,
> configuration change, pause, unpause, migration, or other Base write. Every
> state-changing phase requires a separately approved payload and execution
> window.

---

## 1. How to use this checklist

### Runbook map

- [Operator quick reference and operation skeleton](#operator-quick-reference)
- [Checklist conventions and run dossier](#checklist-conventions)
- [Architecture and owner decisions](#2-selected-deferred-cutover-architecture)
- [Candidate/live-state bind and transition Defaults](#4-phase-0--bind-candidate-inputs-and-live-base-state)
- [Candidate deployment and off-chain readiness](#6-phase-2--deploy-and-qualify-the-inert-candidate-stack)
- [Fork rehearsal and core cutover](#8-phase-4--composed-base-fork-rehearsal)
- [Transitional operation](#11-phase-7--transitional-operation)
- [Stability Pool migration](#12-phase-8--stability-pool-1-to-6-migration)
- [RipeGov migration](#13-phase-9--ripegov-2-to-7-migration)
- [Global stops and execution records](#15-global-stop-conditions)
- [Source index and readiness declaration](#17-reviewed-source-index)

### Operator quick reference

**The namespace/deferred-migration architecture is selected; execution is not
authorized.** The core RH cutover, Stability migration, and RipeGov migration
are three separate programs. O-11 still requires an owner decision on the
stateful BondBooster source-divergence exception. A later migration blocker
does not block core engineering, and no later migration is part of the core
maintenance window.

| Workstream | Current status | What must happen before its scoped Base write |
| --- | --- | --- |
| Phase 0A registry-ID-8 cancellation | **LIVE REBIND REQUIRED; NOT AUTHORIZED** | Bind the exact live active/pending branch, simulate the cancellation, independently review its separate Safe payload, and obtain separate authorization |
| Core RH cutover, Phases 0–7 after Phase 0A | **DESIGN SELECTED; ENGINEERING OPEN; NOT PAYLOAD-READY** | Close each applicable decision by its controlling due gate, close `TX-ASSERT`, freeze the release, qualify transition Defaults, complete the composed fork, independently review exact payloads, and obtain separate authorization |
| Stability Pool 1 to 6, Phase 8 | **BLOCKED FOR PAYLOAD/EXECUTION** | Close O-5, O-9, O-10, `SP-SWEEP`, and the Phase-8 branch of `TX-ASSERT`; pass Gates 8A and 8B from a fresh block/hash |
| RipeGov 2 to 7, Phase 9 | **BLOCKED FOR PAYLOAD/EXECUTION** | Complete Gate 8; close O-8, `RG-PROCEDURE`, `RG-CLEANUP`, and the Phase-9 branch of `TX-ASSERT`; pass the exact deployed-legacy fork plus Gates 9A and 9B |
| Reserve Engine/Vesting | **SEPARATE PROGRAM** | Keep RipeHQ IDs 26 and 27 and the future Switchboard slot available; do not add Reserve work to the core window |

Ledger remains deployed and unchanged in every row.

#### Operation-ordered skeleton

The stable IDs below identify operation families and evidence work packages.
They are a dependency map, **not calldata, authorization, or permission to
skip the detailed phase gate**. `ART-*` identifiers are evidence artifacts
that must be complete before their dependent operation. A dated execution
packet must mint a deterministic child ID for every actual transaction or
atomic bundle and map that child—not a multi-transaction parent—to one exact
call list, command or script version, expected typed returns/readbacks, Safe
nonce, payload hash, receipt, and independent verifier.

| Order | Stable ID | Operation or required artifact | Detailed control |
| ---: | --- | --- | --- |
| 1 | `ART-0A-01` | Read active RipeHQ registry ID 8 and its pending update; bind the cancel/no-pending/already-confirmed branch | §4.3 |
| 2 | `OP-0A-02` | If separately authorized and still pending, cancel the registry-ID-8 update | §4.3 |
| 3 | `ART-CORE-01` | Bind the canonical post-Phase-0A block and build complete configuration, topology, vault, user, and authority snapshots | §§4.4–4.7 |
| 4 | `ART-CORE-02` | Generate the exact-live snapshot and the separately named transition Defaults overlay | §5 |
| 5 | `OP-CORE-01` | After Gate 1, deploy the complete candidate stack inert; confirm candidate VaultBook appends in exact order 1→5→6→7 and Switchboard children Alpha→Echo; finalize both registry delays; clear any temporary local governors; pause AuctionHouse explicitly | §6 |
| 6 | `ART-CORE-05` | Bind the deployed-candidate address, runtime, immutable, pause, authority, and registry-order dossier | §6.5 |
| 7 | `ART-CORE-03` | Release and verify frontend, indexer, keeper, and monitoring support for the transitional topology | §7 |
| 8 | `ART-CORE-04` | Fork-rehearse the exact composed cutover, negative controls, soft-return handling, failure boundaries, payloads, and gas | §8 |
| 9 | `OP-CORE-02` | Initiate only the closed RipeHQ replacement allowlist and the VaultMigrator append at ID 25 | §9 |
| 10 | `OP-CORE-03` | After the live-bound RipeHQ delay and final revalidation, complete the full producer/configuration freeze | §§9–10.2 |
| 11 | `OP-CORE-04` | Confirm the replacement VaultBook first; prove IDs 1–7 exactly | §10.3 |
| 12 | `OP-CORE-05` | Atomically confirm HQ 5 MissionControl then HQ 6 Switchboard with asserted typed returns; confirm the remaining closed allowlist and VaultMigrator ID 25 under the complete freeze | §10.3 |
| 13 | `OP-CORE-06` | Replay and independently read back every approved configuration, user config, delegation, and pending-state disposition | §10.3 |
| 14 | `OP-CORE-07` | With Pool 6 unpaused at both validations, initiate/execute the qualified Stability pointer rotation 1 to 6 while the freeze remains complete | §10.3 |
| 15 | `OP-CORE-08` | After all setup-zero writes clear, finalize every applicable production action delay; only then reinitiate explicitly approved production-surviving pending actions and prove their new timing | §10.3 |
| 16 | `OP-CORE-09` | Establish the owner-approved Pool-6 launch capacity or prove the approved empty-capacity posture | §10.4 |
| 17 | `OP-CORE-10` | Reopen Teller and approved producers only after all readbacks; reopen AuctionHouse last | §10.6 |
| 18 | `MON-TRANSITION-01` | Operate and monitor the valid transitional state: Pool 6 is new-flow Stability, Pool 1 is legacy exit/claim only, and RipeGov 2 remains core | §11 |
| 19 | `ART-SP-DESIGN-01` | Before Gate 8A, fork-qualify the exact claim-tail remediation/exception branch, action inventory, typed-return enforcement, and unwind | §§12.2–12.3 |
| 20 | `OP-SP-01` | After Gate 8A, initiate only the qualified reward, route, and timelocked O-10 remediation/restoration actions; execute none while staging | §12.4 |
| 21 | `ART-SP-01` | From a fresh matured-action pin, rebuild the census and fork-execute the exact complete Stability sequence | §§12.5–12.6 |
| 22 | `OP-SP-02` | After Gate 8B, execute reward zero and verify its typed return/state | §12.6 |
| 23 | `OP-SP-03` | Using a mechanism that converts any soft `False`/zero result into an EVM revert, atomically execute `[6,1]` bridge, governance seed, and restoration to `[6]` | §12.6 |
| 24 | `OP-SP-04` | In a qualified later action block, refresh entitlement and execute the exact remediation/claim/post-state-restoration sweep | §§12.6–12.7 |
| 25 | `OP-SP-05` | Prove exact economic-claim closure and the approved raw-tail disposition, then complete the migration freeze | §§12.7–12.8 |
| 26 | `OP-SP-06` | Unpause VaultMigrator, run the canary, and migrate measured batches through SwitchboardEcho | §12.9 |
| 27 | `OP-SP-07` | Reconcile, pause VaultMigrator, restore the approved reward posture, and reopen | §12.10 |
| 28 | `OP-RG-01` | Execute the ordered RIPE and RIPE/LP `[2,7]` bridges while ID 2 remains default and stage both temporary and exact-original restoration term actions | §13.3 |
| 29 | `ART-RG-EXEC-01` | After staged actions mature, bind the pre-freeze state and exact `OP-RG-02`/`OP-RG-03` containment and pointer-initiation payloads | Gate 9A |
| 30 | `OP-RG-02` | Complete the RipeGov producer/configuration freeze | §13.4 |
| 31 | `OP-RG-03` | `RG7-UNPAUSE-A`: atomically unpause 7, initiate pointer 2 to 7, and re-pause 7 | §13.5 |
| 32 | `ART-RG-EXEC-02` | After the Charlie action exists and matures, bind its exact ID/timing, the final frozen census/batches, every remaining payload, Phase-9 soft-return handling, and the complete execution fork | Gate 9B |
| 33 | `OP-RG-04` | After Gate 9B, `RG7-UNPAUSE-B`: atomically unpause 7, execute pointer 2 to 7, and re-pause 7 | §13.5 |
| 34 | `OP-RG-05A` | Only after pointer-to-7 readback, initiate the final Bravo RIPE and RIPE/LP `[7]` routes; maturity is a monitored dependency, not an operation | §13.5 |
| 35 | `OP-RG-05B` | Only after the full freeze, pointer-to-7 readback, and final-route maturity, execute the approved Alpha temporary legacy terms as the final governed term writes before the required later action-block boundary and migration | §13.6 |
| 36 | `OP-RG-06` | Unpause VaultMigrator, run the exact-legacy canary, and migrate gas-qualified batches | §13.7 |
| 37 | `OP-RG-07` | Execute the pre-staged exact-original term restorations, execute final `[7]` routes, and pause VaultMigrator | §13.8 |
| 38 | `OP-RG-08` | Complete source reward, registration, and Ledger-membership cleanup through the approved administrator route | §13.9 |
| 39 | `OP-RG-09` | Reconcile terminal state, then unpause RipeGov 7, Teller, and approved producers | §§13.10–14 |

`OP-RG-05` is retired before payload authorship because it combined two boards,
two transaction types, and a maturity wait. It must never appear in a dated
packet; use `OP-RG-05A` and `OP-RG-05B`.

#### Phase guardrails

| Phase | Do | Do not | Immediate stop example |
| --- | --- | --- | --- |
| 0 | Bind active and pending topology, then pin a post-write block | Treat an already-confirmed ID-8 replacement as `N/A` | Active ID 8 or its runtime differs from the expected legacy topology |
| 1 | Maintain exact-live and transition artifacts separately | Hand-edit or storage-patch a candidate to resemble the overlay | Any non-allowlisted configuration difference |
| 2 | Deploy only after Gate 1 and keep the stack inert | Infer registry activation from a manifest or deployment | An immutable, runtime, ID, or pause state differs |
| 3 | Release explicit legacy/new-vault UX and monitoring first | Hide Pool 1 merely because it is no longer the default | A client cannot address IDs 1, 2, 6, and 7 correctly |
| 4 | Rehearse the composed order and injected failures | Qualify isolated calls as a substitute for the full sequence | Any fork or payload byte differs from the proposed window |
| 5 | Start approved actions and monitor them to maturity | Confirm, cancel, or replace during the staging-only window | Action state, target, live registry delay, or an applicable board-action expiry drifts |
| 6 | Freeze completely; confirm VaultBook before ID-6 validation; reopen AuctionHouse last | Treat Teller pause as a full freeze | Charlie delay/order or AuctionHouse route differs from rehearsal |
| 7 | Monitor both legacy and new paths with a deadline | Route RH AuctionHouse to legacy Pool 1 | Unexpected legacy ingress, liquidation route, or census drift |
| 8 | Use the two-gate fresh-fork process and later-block claim | Leave `[6,1]` live outside the atomic seed transaction | Claim residue, entitlement shortfall, or last-touch conflict |
| 9 | Keep every trusted producer frozen through both named ID-7 unpause bundles | Assume Teller pause protects `depositFromTrusted` | Any target-7 touch, cleanup gap, term mismatch, or action-expiry risk |
| 10 | Close from independently reproduced state | Retire a vault from registration count alone | Any unexplained residual custody, reward, registration, or Ledger state |

#### Decision and role control

| Item | Initial status | Owner | Must close before | Due / approval evidence |
| --- | --- | --- | --- | --- |
| O-1 Pool-6 launch capacity | `OPEN` |  | Gate 4 |  |
| O-2 transitional deadline | `OPEN` |  | Gate 6 |  |
| O-3 vault-limit users | `OPEN` |  | Gate 6 |  |
| O-4 transitional user treatment | `OPEN` |  | Gate 3 |  |
| O-5 claim/reward policy | `OPEN` |  | Gate 8A |  |
| O-6 VaultMigrator at ID 25 | `REQUIRED CONSTRAINT` |  | Verify at Gates 2 and 5 |  |
| O-7 timelock posture | `OPEN` |  | Gate 4 |  |
| O-8 RipeGov procedure | `OPEN` |  | Phase 9 payload |  |
| O-9 governance-seed ingress | `OPEN` |  | Gate 8A |  |
| O-10 legacy Stability claim-tail disposition | `OPEN` |  | Gate 8A |  |
| O-11 BondBooster source-divergent posture | `OPEN — PRESERVE LEGACY RECOMMENDED` |  | Gate 1 |  |
| `TX-ASSERT` soft-return enforcement | `BLOCKED` |  | Gate 4 / Gate 8B / Gate 9B as applicable |  |
| `TRANSITION-DEFAULTS` dedicated Base overlay implementation | `BLOCKED` |  | Gate 1 |  |
| `MC-INACTIVE-STATE` dormant asset/stale-slot disposition | `BLOCKED` |  | Gate 1 |  |
| `SP-SWEEP` exact sweep qualification | `BLOCKED` |  | Gate 8A |  |
| `RG-PROCEDURE` exact deployed-legacy procedure | `BLOCKED` |  | Phase 9 payload |  |
| `RG-CLEANUP` implementation/qualification | `BLOCKED` |  | Phase 9 payload |  |

- **Document owner:** maintains this canonical checklist and resolves document
  status; does not substitute prose for an owner policy decision.
- **Payload preparer:** converts only signed gate outputs into the dated
  execution packet and Safe payload.
- **Independent verifier:** reproduces decoding, simulation, runtime identity,
  expected readbacks, and payload hash; must not be the payload preparer.
- **Technical operator:** executes only authorized `OP-*` rows in order and
  records receipts/readbacks before advancing.
- **Incident lead / stop authority:** can stop the window immediately and owns
  the approved forward-recovery branch.

Research and fork proofs are discharged as hash-bound `ART-*` artifacts before
the live window. Day-of operators confirm the artifact identity and its
preconditions; they do not repeat open-ended research while the protocol is
frozen.

#### Critical-path and freeze budget

Do not copy a historical block delay into the schedule. Read each live
`registryChangeTimeLock`, action timelock, confirmation block, and—only where
the action type exposes one—expiry from the bound contracts and pending action.
Legacy RipeHQ address-registry operations have no action ID or expiry: an
update is keyed by registry ID, an append is keyed by candidate address, and
either can remain executable after its `confirmBlock`. Fill this table before
payload review.

| Window / long pole | Planned start | Live-bound blocks / dependency | Assumed seconds per Base block + source | Conservative wall-clock range | Maximum freeze | Expiry headroom + incident margin | Owner |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Phase 0A cancellation/finality |  | Separate Safe approval and finality policy |  |  | None unless separately required |  |  |
| Transition Defaults + final-release forks |  | Gate-1 build and independent reproduction |  |  | None | N/A |  |
| Core RipeHQ transition |  | Live RipeHQ `registryChangeTimeLock` plus Gate 5 |  |  |  | `N/A` for registry-operation expiry; bind exact pending state |  |
| Core pointer/replay window |  | Candidate Alpha/Bravo/Charlie delays and exact confirmation blocks |  |  |  |  |  |
| Stability staging/execution |  | Gates 8A/8B, live reward/Bravo delays, later action block, final fork |  |  |  |  |  |
| RipeGov staging/execution |  | Live Bravo, Charlie, asset-term, route, cleanup, and final-action delays |  |  |  |  |  |

- [ ] No freeze starts until every safely pre-stageable action is mature and
  the measured worst-case execution plus reconciliation and incident margin
  fits the approved maximum freeze and action-expiry headroom.
- [ ] Every elapsed-time estimate records the assumed Base block cadence and a
  conservative range; confirmation is always by block/readback, never by wall
  clock alone.
- [ ] Every in-scope row is nonblank before its payload gate; blank cells are
  proof that the window remains unscheduled, not permission to estimate live.
- [ ] Each dated packet contains a pre-window abort deadline and a post-first-
  write forward-recovery budget.

#### Stable-ID and command-catalog rules

The hundreds of proof and reconciliation checkboxes are acceptance criteria,
not independent Base transactions. Reference them by section plus exact text;
do not promote each one into an executable operation. The `OP-*` IDs above
remain stable across dated runs and must appear in every transaction ledger,
incident message, and evidence filename.

- A top-level `OP-*` identifies a state-changing operation family. It is not a
  transaction identifier when the family contains multiple calls, actors, or
  waits.
- Every actual Base transaction or atomic bundle receives exactly one child
  ID, such as `OP-CORE-05-HQ-0005` or `OP-SP-06-BATCH-0001`. One child maps to
  one Safe nonce/payload hash and one receipt. Separate transactions, boards,
  confirmation waits, or post-receipt checks never share a child ID.
- `ART-*` identifies an immutable, checksum-bound evidence artifact.
- `MON-*` identifies a recurring monitoring control and produces dated
  `ART-*` evidence instances.
- Stable IDs are semantic: never renumber, reuse, or silently change one. If
  semantics materially change, retire the old ID and mint a new one.
- Repeated actions use a zero-padded child suffix, such as
  `OP-SP-06-BATCH-0001`; each child binds one deduplicated manifest, pre-state,
  Safe nonce, transaction hash, and reconciliation artifact.
- Maturity and waiting are dependencies recorded by `ART-*`/`MON-*`, not
  state-changing `OP-*` rows.
- A successful low-level call that decodes to `False` or zero is a failed
  operation. Post-transaction readback detects that failure but does not make
  a dependent MultiSend atomic. Any bundle whose safety depends on all calls
  succeeding must use a fork-qualified execution primitive that asserts typed
  return values and converts semantic failure into an EVM revert.

Exact `cast`, RPC, deployment, and Safe commands are deliberately not frozen in
this architecture document before addresses, ABI/runtime identities, release,
and canonical block are bound. Section 16 requires a generated companion
command catalog with expected decoded results. No `OP-*` row is executable
until that catalog is populated, independently dry-run, checksum-bound, and
approved against the final release and live state.

- [ ] Make a dated copy for each deployment or migration window.
- [ ] Fill every evidence field with a value or write `N/A — <reason>`.
- [ ] Treat every **GATE** as fail-closed. Do not begin the next phase until the
  gate owner and independent reviewer sign it.
- [ ] Rebind all mutable chain state before each later maintenance window.
- [ ] Preserve transaction hashes, native pending-operation keys, calldata
  hashes, fork evidence, readbacks, and reconciliations in one run dossier.
- [ ] Resume from reconciled chain state after any failure; never resume from a
  local success log alone.

### Checklist conventions

| Mark | Meaning |
| --- | --- |
| `[ ]` | Not proven or not completed |
| `[x]` | Proven or completed with evidence in the run dossier |
| `N/A` | Inapplicable with a written, reviewed reason |
| **STOP** | Do not proceed without a newly approved disposition |

### Run dossier

| Field | Value |
| --- | --- |
| Document version |  |
| Document status | `DRAFT — DO NOT EXECUTE` |
| Document owner |  |
| Run name |  |
| Phase/window |  |
| Environment | Base mainnet / Base fork / other: |
| Date |  |
| Technical operator |  |
| Independent verifier |  |
| Incident lead / stop authority |  |
| Incident channel |  |
| Governance Safe |  |
| Safe nonce |  |
| Chain ID |  |
| RPC/provider identity |  |
| Finalized snapshot block |  |
| Snapshot block hash |  |
| Release commit |  |
| Release tree |  |
| Compiler identity |  |
| Deployment manifest hash |  |
| Safe payload hash |  |
| Fork rehearsal evidence |  |
| Evidence dossier root/hash |  |
| Owner authorization |  |

---

## 2. Selected deferred-cutover architecture

### Required end state after the RH core cutover

| Component | Required state |
| --- | --- |
| Ledger | Exact deployed contract remains at the same RipeHQ entry |
| VaultBook IDs 1–5 | Exact legacy address bindings are preserved |
| Stability Pool 1 | Legacy exit/claim/redeem only; no new deposits or liquidations except the one separately approved atomic governance seed bundle |
| Stability Pool 6 | New deposits and all Stability Pool liquidation routing |
| RipeGov 2 | Remains the active core RipeGov during transitional operation |
| RipeGov 7 | Deployed, paused, unrouted, and pristine until its migration window |
| VaultMigrator | Registered at RipeHQ ID 25; paused outside migration windows |
| Reserve contracts | Outside the core cutover; preserve RipeHQ IDs 26 and 27 |

### Target-state timeline

| State | Stability | Ripe governance | Operator interpretation |
| --- | --- | --- | --- |
| RH core live | Pool 6 receives new deposits and is the sole Stability-pool liquidation route/target; rejected or partial fills use the proven auction fallback; Pool 1 is explicit-ID exit/claim/redeem only | ID 2 remains core; ID 7 is paused and pristine | Valid transitional production state |
| Transitional operation | Pools 1 and 6 coexist, but Pool 1 is never an RH AuctionHouse route | New rewards, HR, bonds, and normal deposits continue to ID 2 | Monitor and rebind before each later window |
| Stability migration complete | Claim accounting is closed and intended Pool-1 positions are in 6 | ID 2 remains core; Pool-1 claim rewards can no longer create ID-2 positions | Required predecessor to RipeGov migration |
| RipeGov migration complete | Pool 6 remains active; Pool 1 is residual-cleanup only | ID 7 is core and final deposit route; ID 2 remains historically classified for cleanup | Final RH vault topology, subject to terminal residual proof |

“Exit available” remains conditional on Teller and Pool 1 being unpaused, the
relevant withdrawal/claim/redeem flags, caller/delegation permissions, debt
health, and compatible live configuration. Removal from deposit `vaultIds`
does not bypass those controls.

### Non-negotiable invariants

- [ ] Ledger is neither redeployed, replaced, upgraded, nor semantically
  modified.
- [ ] New VaultBook IDs 1–5 resolve to the exact current vault addresses.
- [ ] New Stability Pool is VaultBook ID 6.
- [ ] New RipeGov is VaultBook ID 7.
- [ ] RH AuctionHouse is never callable while Pool 1 appears in
  `priorityStabVaults` or any `specialStabPoolId`.
- [ ] Ordinary sGREEN and GREEN/USDC LP deposits resolve to Pool 6 after cutover.
- [ ] Pool 1 remains reachable through explicit ID-1 withdrawal, claim, and
  redemption paths.
- [ ] The only permitted post-cutover Pool-1 deposit is the exact
  fork-qualified governance seed inside the atomic bridge-open/seed/restore
  transaction in Phase 8.
- [ ] `coreRipeGovVaultId` remains 2 until the final RipeGov migration window.
- [ ] RIPE and RIPE/LP routes remain `[2]` during transitional operation.
- [ ] RipeGov 7 receives no deposit, reward, bond, HR position, or user touch
  before its migration window.
- [ ] Stability Pool migration completes before RipeGov migration.
- [ ] Teller pause is never treated as a complete freeze; every alternate
  trusted producer and governance withdrawal path is included.
- [ ] Planning figures are never copied into production calldata without a
  fresh block/hash-bound calculation.

### Why Pool 1 cannot remain an RH liquidation route

RH AuctionHouse performs a typed `staticcall` to
`canAcceptLiquidationAsset(...)`. Legacy Pool 1 does not expose that selector.
The typed call to that unsupported selector reverts; it does not gracefully
return `False`.

Evidence anchors:

- `5c30234e:contracts/core/AuctionHouse.vy:625-654`
- `91eda49:scripts/abis/StabilityPool.json:338,926-969,1242-1289`
- `91eda49:contracts/vaults/modules/StabVault.vy:609-628,793-815`

---

## 3. Owner policy decisions

No production specification or Safe payload for a phase may be finalized while
a decision required by that phase remains open. Later migration decisions may
remain open during evidence collection and core engineering, but must have a
named owner, target gate, and due date.

### Decision O-1 — Pool 6 launch capacity

- [ ] Approved capacity target: ______________________________
- [ ] Approved stability asset(s): ___________________________
- [ ] Approved seed owner/depositor: _________________________
- [ ] Approved withdrawal/unwind policy: _____________________
- [ ] Accepted auction-fallback posture: _____________________
- [ ] Capacity calculation is block/hash-bound.
- [ ] Calculation distinguishes raw custody, spendable custody,
  reservations, asset mix, priority order, and price risk.

Do not use `$57.5K`, `$250`, or any other prior planning figure as an approved
amount without recomputation.

### Decision O-2 — Transitional-operation deadline

- [ ] Target completion date/block: __________________________
- [ ] Escalation threshold: __________________________________
- [ ] Authorized response if the deadline is missed: _________

There is no automatic rollback to Pool 1 while RH AuctionHouse is active.

### Decision O-3 — Users already at the Ledger vault limit

- [ ] Affected-user census completed.
- [ ] Approved treatment: ____________________________________
- [ ] The plan does not casually raise `perUserMaxVaults` for the whole
  protocol.

A user participating in both Pool 1 and Pool 6 consumes two Ledger vault slots.
This is a transitional UX/ordinary-user-operation decision, not a controlled
VaultMigrator capacity blocker: a registered migration department uses the
Ledger department path and bypasses the ordinary depositor vault-count limit.

### Decision O-4 — Transitional user treatment

- [ ] User notice approved.
- [ ] Opt-in movement or incentive policy approved.
- [ ] Frontend wording explains that Pool 1 no longer receives liquidation
  collateral.
- [ ] Claims, redemptions, and withdrawals permitted during the transition are
  explicitly defined.
- [ ] Residual-retirement policy for Pool 1 and RipeGov 2 is approved.

### Decision O-5 — Stability claim-reward policy

- [ ] Reward rate during transitional operation: ______________
- [ ] Reward rate during the legacy sweep: `0` **(required by this runbook)**.
- [ ] Post-migration Pool-6 reward policy: _____________________
- [ ] Exact pre-sweep `autoStakeRatio` and `autoStakeDurationRatio` are
  preserved through the reward-zero action and restored unchanged unless a
  separately approved policy changes them.
- [ ] Dormant/unpriceable claim and dust disposition: __________
- [ ] Custody/disposition of assets received by the governance sweep:
  _____________________________________________________________

A nonzero legacy-sweep rate is not an owner-selectable payload variation in
this runbook; it requires a reviewed branch with new entitlement, RipeGov-2
side-effect, fork, and closeout proofs.

### Constraint O-6 — VaultMigrator registration

- [ ] Deploy and register VaultMigrator in the core program at exactly RipeHQ
  ID 25.
- [ ] Bind the final Base legacy RipeGov immutable.
- [ ] Keep VaultMigrator paused outside separately approved migration windows.

RipeHQ ID 25 is not a preference. RH `Addys` and `SwitchboardEcho` hardcode the
VaultMigrator lookup at ID 25. This runbook does not retain a deferred branch:
deferral would require a new deployment, runtime qualification, RipeHQ action,
timelock, registration, and activation gate before Phase 8. Registering the
migrator at any later ID is not a valid substitute.

### Decision O-7 — Switchboard timelock posture

- [ ] Approved nonzero production delay/expiry tuple for every applicable
  component: _________________________________________________
- [ ] Core cutover uses a newly deployed Charlie with
  `actionTimeLock == 0` only for the bounded replay/pointer window.
- [ ] Normal production timelocks are finalized immediately after the core
  replay and Pool-6 pointer rotation.
- [ ] Every later Stability/RipeGov freeze budget includes the actual Alpha,
  Bravo, Charlie, and lock-term action delays under the selected posture.

Because migration may be deferred by days or weeks, the selected architecture
finalizes normal timelocks after core cutover and pre-stages later actions
where validation permits. Retaining zero-delay governance after the bounded
setup window is not a branch in this runbook; it requires a reviewed
architecture amendment.

### Decision O-8 — Controlling RipeGov migration procedure

- [ ] Current all-supported-assets-per-user `VaultMigrator` behavior selected
  and exact deployed-legacy fork-qualified.
- [ ] Or the older serial RIPE/RIPE-LP policy selected, with the required
  implementation change and fresh review identified.
- [ ] Conflicting Base and generic RH documents are reconciled or formally
  superseded.
- [ ] Exact temporary-terms sequence and freeze duration are approved.

The reviewed RH migrator snapshots and migrates all supported positions for a
user in one call. Older Base decision documents require one asset per call and
non-overlapping RIPE and RIPE-LP windows. Phase 9 is blocked until this conflict
is resolved and the selected procedure passes exact deployed-legacy fork
qualification.

### Decision O-9 — Stability governance-seed ingress

- [ ] Live-bound seed asset/cohort set: ________________________
- [ ] For every selected seed asset, approve a temporary
  `vaultIds = [6, 1]` bridge, preserving ID 6 as the default while allowing the
  governance Safe to select explicit ID 1.
- [ ] Or another exact-source and composed-fork-qualified seed mechanism:
  _____________________________________________________________
- [ ] Bridge-open and restore-to-`[6]` actions can coexist, mature, execute in
  the required order, and preserve every non-route deposit parameter.
- [ ] If GREEN/USDC LP is the only seed cohort, the fresh claim census and
  entitlement math prove no other stability-asset cohort needs governance
  shares.

After core cutover, each Stability deposit asset has `vaultIds == [6]`;
ordinary Teller validation rejects an explicit ID-1 deposit because Pool 1 is
no longer supported for that asset. A later governance seed therefore needs a
temporary support bridge (normally `[6, 1]`, never `[1, 6]`) for every required
cohort, or another separately reviewed mechanism. Phase 8 is blocked until
this is fork-proven.

### Decision O-10 — Legacy Stability claim-tail disposition

- [ ] Fresh execution-block census enumerates every active iterable row, every
  dormant/raw `claimableBalances` row, `totalClaimableBalances`, token custody,
  decimals, price result, claim/redeem flags, MissionControl registration
  index, and configuration source.
- [ ] Approved primary path: temporarily enable/re-register and fully clear
  every row / exact residual exception: ______________________
- [ ] Classify every temporary MissionControl mutation by its actual control
  path. Enabling a supported asset through Charlie
  `setCanClaimInStabPoolAsset(..., True)` is an immediate `bool`-return
  governance action, not a timelocked action; disabling can also admit
  configured lite authority, but this runbook binds the exact authorized
  governance caller for both directions. A Bravo asset re-registration and a
  Charlie asset deregistration are separate timelocked actions with distinct
  action IDs. Give every actual write its own child ID, authorization,
  typed-success predicate, composed fork proof, and readback.
- [ ] Bind the complete per-row lifecycle: approved pre-state; any matured
  registration action; any immediate flag enablement; the exact claim batch;
  immediate flag restoration and/or matured deregistration/restoration; and
  the approved terminal MissionControl state. No temporary mutation may be
  left for an operator to infer during the window.
- [ ] If an unsupported asset is re-registered, approve the exact resulting
  dormant-storage footprint. `deregisterAsset` clears the active index/count
  but does not erase `assetConfig` or every stale terminal `assets[]` slot, so
  “restore exact pre-registration storage” is not a valid promise. Diff routes,
  allocations, limits, flags, config mapping, active list, and stale slots.
- [ ] Any residual exception binds exact asset, stability cohort, raw amount,
  token decimals, USD-value calculation, active/dormant status, and custody
  disposition; it is never expressed as a generic dust threshold.
- [ ] The exact deployed-legacy fork proves an approved residual cannot change
  any preceding user's source withdrawal, target receipt, shares, or
  depletion; the governance residual position migrates last and absorbs only
  the exact proven rounding/tail effect.
- [ ] Final terminology distinguishes “economic claims closed” from “all raw
  accounting zero”; a vault with retained raw custody is not called retired.

Read-only planning observation only: at Base block `50,459,811`, VVV
`0xacfe6019ed1a7dc6f7b508c02d1b04ec88cc21bf` and mcbETH
`0x3bf93770f2d4a794c3d9EBEfBAeBAE2a8f09A5E5` each had one raw claim unit and
both asset-level claim flags were false. VVV was registered at MissionControl
index 19; mcbETH was not registered. This observation is mutable and does
**not** approve a one-unit exception, prove either row's price/share effect, or
eliminate re-registration as a possible qualified remediation. Gate 8A uses a
fresh census and owner decision.

### Decision O-11 — BondBooster source-divergent posture

- [ ] Approve the recommended posture: preserve the exact live legacy
  BondBooster and all of its grant/usage state, accepting that the RH source's
  expired/absent-grant `unitsUsed` reset behavior is not activated.
- [ ] Or require the new RH BondBooster, in which case identify and qualify an
  exact state-migration/continuity design before Gate 1; pointing replacement
  BondRoom at an empty new booster is not an acceptable migration.
- [ ] Bind the replacement BondRoom's constructor-initialized but
  Switchboard-mutable booster pointer and prove the preserved booster still
  resolves the active HQ-6/HQ-12 permissions after both registry swaps.
- [ ] Census and reconcile every booster parameter, grant, expiry, units-used
  value, caller, and pending/configuration state.
- [ ] Owner acceptance/evidence: ______________________________

Preserving the legacy booster is the simplest state-continuity posture, but it
is an explicit exception to “all latest RH source,” not an invisible
implementation detail.

### GATE O — Decision register initialized

- [ ] Every decision has an owner, target gate, due date, and approval/evidence
  field.
- [ ] The due gate in the §1 decision table controls: O-4 closes before Gate
  3; O-1 and O-7 before Gate 4; O-2 and O-3 before Gate 6; and O-6 is verified
  as a mandatory constraint at Gates 2 and 5.
- [ ] O-11 closes before Gate 1; its selected Booster identity and compatibility
  proof are immutable inputs to the transition build and candidate dossier.
- [ ] `TRANSITION-DEFAULTS` and `MC-INACTIVE-STATE` close before Gate 1; the
  latter includes every ever-touched inactive asset and stale array slot, not
  only the active iterator.
- [ ] O-5, O-9, O-10, `SP-SWEEP`, and the applicable `TX-ASSERT` proof close
  before their stated Phase-8 gates.
- [ ] O-8/`RG-PROCEDURE` and `RG-CLEANUP` close before any Phase-9 payload is
  finalized.
- [ ] Gate 9A authorizes only the exact RipeGov freeze and pointer-initiation
  package; the Phase-9 branch of `TX-ASSERT` closes at Gate 9B before pointer
  execution or any migration child is authorized.
- [ ] No phase executes while any decision or technical blocker due at or
  before that phase remains open, even if Gate O was signed earlier.
- [ ] No closed decision relies on an unpinned balance, price, user count, or
  batch count.
- [ ] Independent reviewer sign-off: __________________________

---

## 4. Phase 0 — Bind candidate inputs and live Base state

**Environment / writes / authority:** Base reads are evidence collection.
Phase-0A cancellation is the only Base write and requires a separate Safe
authorization; this document supplies none.

### 4.1 Candidate-source binding

- [ ] Fetch/rebind the intended RH candidate only when authorized.
- [ ] Record exact commit and tree.
- [ ] Record every production source blob/hash used by the candidate.
- [ ] Record compiler version and compiler binary hash.
- [ ] Compile and record runtime sizes and hashes under the approved build
  environment.
- [ ] Confirm every contract remains within EIP-170.
- [ ] Bind constructor arguments and immutable values.
- [ ] Bind deployment scripts and generated artifact hashes.
- [ ] Prove the candidate contains no unreviewed contract delta from the accepted
  architecture.

### 4.2 Discovery-state binding

- [ ] Record chain ID 8453 and provider identity.
- [ ] Record finalized block number and hash.
- [ ] Record Safe address, threshold, owners, and module/guard configuration.
- [ ] Record current RipeHQ address and registry count.
- [ ] Record every RipeHQ ID/address/runtime hash.
- [ ] Record every VaultBook ID/address/runtime hash.
- [ ] Confirm VaultBook IDs 1–5 have not changed.
- [ ] Record MissionControl, Switchboard child registries, PriceDesk, and board
  registries.
- [ ] Record all pause states and governance owners.
- [ ] Record all pending operations and their initiation, confirmation,
  cancellation/replacement, and—where the action type exposes one—expiry
  state.
- [ ] Reconstruct every candidate-keyed pending RipeHQ append from events and
  getters, including immature entries. No unrelated append may remain without
  an exact pre-authorized cancellation or terminal disposition; “not yet
  executable” is not harmless when IDs 25–27 are reserved.

### 4.3 Pending RipeHQ registry-ID-8 update

This is a separate Phase-0A Base mainnet governance window. It requires its own
authorization, Safe payload, simulation, and receipt; the discovery block is
not the canonical deployment snapshot after this write.

- [ ] Read active `getAddr(8)`, `addrInfo(8)`, its version/runtime identity, and
  the complete current `pendingAddrUpdate(8)` row.
- [ ] Confirm the active address is still the expected legacy VaultBook from
  the discovery manifest.
- [ ] Record the pending row's `newAddr`, `initiatedBlock`, `confirmBlock`, and
  current executability. This registry update has **no Switchboard-style
  action ID**; it is keyed by RipeHQ registry ID 8.
- [ ] Classify exactly one branch: unchanged active address with pending update;
  unchanged active address with no pending update; or active address/version
  already changed.
- [ ] Compare it to the separately approved cancellation package.
- [ ] Simulate the exact cancellation.
- [ ] Obtain separate authorization for cancellation.
- [ ] Execute cancellation only if authorized and the live active/pending row
  still matches the approved branch byte-for-byte.
- [ ] Read back that the pending update is cleared.
- [ ] Read back that active registry ID 8, version, runtime, and registry count
  remain exactly as expected after cancellation.
- [ ] Record cancellation transaction hash: ___________________

**STOP:** any historical statement that the action is “already executable” is
not sufficient. Use the live readback from this run.

**STOP — already confirmed/replaced:** if active registry ID 8 or its version
no longer matches the expected legacy VaultBook, or the event/readback history
shows that the pending replacement already confirmed, this is **not** a
reviewed `N/A` cancellation. Stop the inherited plan and rederive the entire
active topology, VaultBook ID/address bindings, transition Defaults, censuses,
deployment manifests, composed fork, and payloads from the new state.

### 4.4 Canonical post-cancellation state pin

- [ ] Wait for the approved finality threshold after the cancellation or its
  reviewed `N/A` disposition.
- [ ] Record a new finalized Base block number/hash and RPC identity.
- [ ] Re-read RipeHQ, VaultBook, every pending action, Safe nonce, pause state,
  and authority from that new block.
- [ ] Use only this post-write block/hash for the exact configuration,
  user/vault censuses, transition Defaults, fork, and deployment manifests.

### 4.5 Configuration and user-state snapshot

- [ ] Generate an exact MissionControl global-configuration snapshot.
- [ ] Inventory every nonzero `userConfig` row.
- [ ] Inventory every nonzero `userDelegation` row.
- [ ] Inventory pending HR, Alpha, Bravo, Charlie, Delta, Echo, PriceDesk, and
  governance state that constructors do not preserve.
- [ ] Record all asset `vaultIds`, staker/voter allocations, debt terms,
  liquidation flags, and `specialStabPoolId` values.
- [ ] Record `priorityStabVaults`, `priorityLiqAssetVaults`, and priority price
  sources.
- [ ] Record `preferredStabVaultId`, `coreRipeGovVaultId`, and historical vault
  classifications.
- [ ] Record reward parameters, including
  `stabPoolRipePerDollarClaimed`.

### 4.6 Vault-state snapshots

- [ ] Pool 1 holder census scans deployment-to-pin events and reconciles every
  candidate user against live balances, raw shares, registered assets, Lootbox
  state, and Ledger participation.
- [ ] For every Pool-1 asset, summed per-user raw shares/balances close exactly
  to the corresponding vault aggregate getter; every delta is explained.
- [ ] Pool 1 stability-asset custody is recorded separately from accounting
  balances and claim reservations.
- [ ] Every active and dormant claim pair is enumerated.
- [ ] Every claim pair has a live priceability and claimability classification.
- [ ] RipeGov 2 census scans deployment-to-pin events and includes users,
  contributors, every registered asset slot (including deprecated legacy LP
  entries), balances, raw shares, points, pending points, unlocks, historical
  terms, registrations, and Ledger participation.
- [ ] For every RipeGov-2 asset, summed user raw shares/balances and points close
  exactly to the applicable aggregate getters.
- [ ] Alternate trusted producers for Pools 1 and 2 are enumerated.
- [ ] Users already at `perUserMaxVaults` are identified.

### 4.7 Replaced-state disposition matrix

Create a machine-readable row for every non-default storage value in every
replaced stateful contract. “Replayed” or “preserved” is not evidence unless the
row names the exact write/readback that establishes it.

| Component / field | Legacy value + block evidence | Disposition | Candidate expected value | Establishing constructor/action/tx | Post-cutover getter/event | Owner / verifier |
| --- | --- | --- | --- | --- | --- | --- |
|  |  | constructor / Defaults / replay / shared Ledger / reset / cancel / defer |  |  |  |  |

- [ ] MissionControl coverage includes asset ordering/indices, every asset
  config, reward values, aggregate point allocations, priority lists, lite
  signers, historical Stability/RipeGov classifications, user configs, and
  delegations.
- [ ] Build an event-derived, storage-reconciled census of every asset ever
  touched by MissionControl, including assets that are no longer active,
  inactive non-default `assetConfig` mappings, `assetIndex`/count state, and
  stale terminal `assets[]` slots left by deregistration. Do not infer this
  universe from the current active-asset iterator alone.
- [ ] For every inactive non-default asset row or stale list slot, close exactly
  one Gate-1 branch: prove none exists; allowlist its reset as an explicit
  transition difference; or specify and composed-fork-prove an exact
  post-constructor register/deregister replay with its resulting terminal
  mapping, index, count, active list, and stale-slot footprint. Supplying an
  inactive row through Defaults is not an exact replay because `_setAssetConfig`
  registers every supplied asset.
- [ ] VaultBook coverage includes every ID/address in order, authority,
  timelocks, and pending actions.
- [ ] RipeHQ, every Switchboard, PriceDesk, HR, Boardroom, and other governance
  component covers every pending action and whether it executes, cancels,
  recreates, or is proven already expired/permanently non-executable and
  target-harmless. “Abandoned on the old component” is not a disposition:
  preserved RipeHQ governance can retain authority over legacy boards, and a
  legacy action may resolve the replacement MissionControl dynamically.
- [ ] Lootbox coverage includes its own global configuration/timestamps and
  distinguishes them from rewards/points state retained in Ledger.
- [ ] CreditEngine parameters, BondRoom booster, HR pending contributors and
  historical contributor mappings are covered.
- [ ] Active auctions, liquidation state held in Ledger, and residual custody
  held by replaced departments are covered.
- [ ] Every department's pause, mint authority, governance owner, temporary
  governor, and relinquishment state is covered.
- [ ] Independent comparison finds no replaced storage field without an
  explicit disposition.

### GATE 0 — Bound inputs

- [ ] Candidate source/build evidence is complete; the production release
  rebind remains a Gate-1 requirement.
- [ ] Live-state snapshot is complete and independently reproduced.
- [ ] Pending ID-8 state is cleared or has an approved blocking disposition.
- [ ] No unexpected registry or configuration drift remains unexplained.
- [ ] Gate evidence: __________________________________________
- [ ] Independent reviewer: __________________________________

---

## 5. Phase 1 — Build exact snapshot and transition Defaults

**Environment / writes / authority:** local build plus Base fork only; no Base
mainnet writes.

Maintain two separate artifacts. Do not overwrite history by calling the
transition configuration an exact live snapshot.

### 5.1 Exact live snapshot artifact

- [ ] Generated from the Gate-0 finalized block.
- [ ] Contains exact current Pool-1 deposit and priority routes.
- [ ] Contains exact current RipeGov-2 routes and terms.
- [ ] Contains exact current reward parameters.
- [ ] Generator, inputs, block/hash, compiler, and artifact hashes are recorded.
- [ ] Independent regeneration matches byte-for-byte.

### 5.2 Transition Defaults overlay

- [ ] Derived mechanically from the exact live snapshot.
- [ ] Has a machine-readable allowlist of permitted differences.
- [ ] sGREEN `vaultIds` is exactly `[6]`.
- [ ] GREEN/USDC LP `vaultIds` is exactly `[6]`.
- [ ] `priorityStabVaults` is exactly `[(6, LP), (6, sGREEN)]`, subject to the
  owner-approved asset order.
- [ ] Every `specialStabPoolId` is 0 or 6 and none is 1.
- [ ] RIPE `vaultIds` remains exactly `[2]`.
- [ ] RIPE/LP `vaultIds` remains exactly `[2]`.
- [ ] RipeGov lock terms remain unchanged.
- [ ] `stabPoolRipePerDollarClaimed` remains at the approved transitional rate.
- [ ] Select a new RH `Contributor` blueprint and make the transition Defaults
  constructor-bindable to its eventual Phase-2 address. Allowlist exactly one
  HR snapshot difference: `hrConfig.contribTemplate` changes from the live
  legacy blueprint to that bytecode-qualified RH blueprint. Every other HR
  field remains exact-live unless a separately approved row says otherwise.
- [ ] Preserve all existing Contributor instances and Ledger contributor state;
  fork-prove their legacy ABI/behavior against replacement HumanResources and
  separately prove new-clone creation/operation through the RH blueprint.
- [ ] Every other global, asset, debt, reward, HR, bond, whitelist, signer, and
  price-source value matches the exact snapshot.
- [ ] The ever-touched-asset and stale-slot census in §4.7 proves either that
  no inactive non-default MissionControl state exists or that every such row
  has an explicit reset/replay disposition in the transition allowlist. The
  candidate expected-state artifact compares the complete approved terminal
  storage footprint, not merely the active assets returned by iteration.
- [ ] Automated diff reports no non-allowlisted change.

**BLOCKED — TRANSITION-DEFAULTS:** the checked-in `DefaultsBaseLive` snapshot
hardcodes the legacy Contributor template, while `DefaultsRobinhood` is a
greenfield launch configuration. Neither is the production transition artifact
unchanged. Engineering must generate and review a dedicated Base-transition
Defaults implementation that consumes the new RH blueprint address, preserves
all exact-live values, and applies only the allowlisted Pool-6 route plus
Contributor-template differences. MissionControl is not deployable until that
artifact and its byte-for-byte independent reproduction pass Gate 1.

**BLOCKED — MC-INACTIVE-STATE:** MissionControl construction cannot reproduce
an arbitrary dormant live footprint from Defaults. `_setAssetConfig` actively
registers every supplied asset, while `deregisterAsset` does not erase every
config/list slot. Gate 1 therefore requires a prove-none result or an explicit
reset/replay branch for every inactive non-default row; an unconditional
“exact-live” assertion over only active assets is insufficient.

### 5.3 Bootstrap-cycle proof

A literal live copy starts with only Pool 1 classified as Stability. It cannot
preserve nonzero staker allocations while moving routes to 6 through the normal
Alpha/Bravo/Charlie validation sequence without a separately designed bridge.

- [ ] Transition Defaults initialize asset support for Pool 6.
- [ ] Transition priority rows cause MissionControl to classify Pool 6 as a
  Stability vault.
- [ ] MissionControl still initializes `preferredStabVaultId = 1`; this
  temporary mismatch is explicitly protected by the full cutover freeze.
- [ ] Charlie can validate and execute `preferredStabVaultId = 6` after the new
  VaultBook is RipeHQ-visible.
- [ ] The replacement MC is never opened to Teller/trusted-producer traffic
  while the pointer remains 1.
- [ ] Fork deployment proves every expected constructor value and historical
  classification.

Evidence anchors:

- `5c30234e:contracts/data/MissionControl.vy:221-258`
- `5c30234e:contracts/config/SwitchboardAlpha.vy:1227-1284`
- `5c30234e:contracts/config/SwitchboardBravo.vy:365-423`
- `5c30234e:contracts/config/SwitchboardCharlie.vy:585-627`

### 5.4 Final production-release rebind

- [ ] Commit the qualified transition Defaults source and generator output into
  the intended release tree.
- [ ] Record the new final release commit and tree; Phase-0 candidate anchors
  are not the production release lock.
- [ ] Rebuild with the final compiler binary and settings; record artifact,
  creation-bytecode, runtime, immutable, and size hashes.
- [ ] Re-run the exact snapshot/allowlisted overlay diff from the bound Base
  block against the committed artifact.
- [ ] Re-run constructor and composed-fork qualification from the final tree.
- [ ] Update every deployment manifest and Safe-planning input to the final
  release identity.
- [ ] Independent reproduction matches byte-for-byte.

### GATE 1 — Defaults qualification

- [ ] Exact snapshot and transition overlay both exist.
- [ ] `TRANSITION-DEFAULTS` is closed with the dedicated constructor/generator,
  exact blueprint binding, and allowlisted diff; neither checked-in defaults
  variant is substituted unchanged.
- [ ] Their relationship is deterministic and independently reviewed.
- [ ] Transition MC deploys with only the approved differences.
- [ ] `MC-INACTIVE-STATE` is closed by a reproduced prove-none result or by an
  explicit, fork-qualified reset/replay disposition for every inactive
  non-default mapping and stale list slot.
- [ ] The new Contributor blueprint/transition-Defaults binding and legacy
  Contributor compatibility proof pass; O-11 is closed and its exact Booster
  posture is encoded in the candidate manifest.
- [ ] Bootstrap cycle is proven closed on a fork.
- [ ] Final production commit/tree, compiler, artifacts, and manifests are
  rebound after the transition Defaults implementation.
- [ ] Gate evidence: __________________________________________
- [ ] Independent reviewer: __________________________________

---

## 6. Phase 2 — Deploy and qualify the inert candidate stack

**Environment / writes / authority:** intended Base mainnet contract creation
plus the bounded one-time candidate setup/finalization writes below, all kept
inert; requires a separate deployment authorization and exact manifest.
Fork-only rehearsals cannot satisfy this phase's deployed-address gate.

**Operation family:** `OP-CORE-01`; every deployment and bounded candidate
setup write receives its own deterministic child ID and manifest row.

### 6.1 Replacement VaultBook

- [ ] Candidate governance and registry timelocks are correct.
- [ ] Record that `confirmNewAddressToRegistry(address)` assigns the current
  sequential `numAddrs`; there is no explicit-ID append call.
- [ ] Start and confirm the exact live VaultBook rows in live ID order 1→5.
  Require each typed confirmation result to equal its expected ID and read
  back that ID/address before advancing.
- [ ] Before building the clone, read every live ID-1–5 version and require it
  to be exactly 1. A fresh append initializes version 1 and has no explicit
  version input; if any live row is above 1, exact version cloning by append is
  impossible and the architecture must be replanned.
- [ ] IDs 1–5 map to the exact current legacy vault addresses and names in the
  same order, and every candidate row reads back version 1.
- [ ] Immediately after cloning IDs 1–5, read both counters:
  `getNumAddrs() == 5` and raw public `numAddrs() == 6`.
- [ ] Only after the 1–5 checkpoint, start/confirm the new RH Stability Pool
  and require assigned ID 6.
- [ ] Only after the ID-6 checkpoint, start/confirm the new RH RipeGov and
  require assigned ID 7.
- [ ] After adding IDs 6 and 7, read both counters:
  `getNumAddrs() == 7` and raw public `numAddrs() == 8`.
- [ ] Event-derived candidate-registry census plus getters proves no pending
  new-address, address-update, or address-disable row remains after 1–7.
- [ ] After the final ID-7 append and before Gate 2, execute the one-time
  `setRegistryTimeLockAfterSetup` with the approved nonzero production value;
  independently read back the value and its min/max bounds.
- [ ] Registry counts/read semantics are tested; display count is not confused
  with the internal next-index value.
- [ ] No vault is appended before the approved IDs.

**STOP — sequential assignment:** if any confirmation returns zero/an
unexpected ID, any counter/address differs, or a candidate confirms out of
order, discard the inert candidate VaultBook and redeploy/requalify it. Do not
repair the clone with address updates or carry it into a payload.

Read-only feasibility observation: at Base block `50,460,701`, hash
`0xb52810cead12b2734deaa91f1b00b898de448d7af5a68f212bf3f9276a3f5d15`,
active VaultBook `0xb758e30c14825519b895Fd9928d5d8748A71a944` reported version 1 for IDs
1–5. This makes exact append cloning feasible at that historical pin; it is
not Gate-0 production evidence, and any later version drift is a stop.

### 6.2 Replacement MissionControl and Switchboards

- [ ] Deploy and bytecode-qualify the RH Contributor blueprint before the
  transition Defaults and MissionControl; bind its address in the Defaults
  constructor/output and read back `hrConfig.contribTemplate` after MC
  deployment.
- [ ] Do not create the candidate MissionControl before Gate 1. Its constructor
  must consume the final, checksum-bound transition Defaults artifact.
- [ ] MissionControl uses the qualified transition Defaults artifact.
- [ ] If the transition Defaults source, generator output, allowlist, release,
  compiler, or constructor inputs change after deployment, discard and
  redeploy MissionControl and repeat qualification. Never patch storage to
  approximate the intended constructor state.
- [ ] Start and confirm Alpha, Bravo, Charlie, Delta, and Echo in that exact
  order. Require typed confirmation results 1, 2, 3, 4, and 5 respectively,
  with counter/address readbacks after each or after one assertion-capable
  atomic ordered batch.
- [ ] Bind Alpha's `PYTH_PRICES_ID` immutable to the preserved live Base
  PriceDesk child that is Pyth, expected ID 4 from the pinned Base
  configuration—not the RH greenfield default `0`. Bind Curve child ID 2 in
  every candidate consumer. Stop if the fresh live PriceDesk topology differs.
- [ ] After Echo, read `getNumAddrs() == 5` and raw public `numAddrs() == 6`.
- [ ] Event-derived candidate-registry census plus getters proves no pending
  new-address, address-update, or address-disable row remains after Alpha–Echo.
- [ ] After the child registry is complete and before Gate 2, execute
  Switchboard's one-time `setRegistryTimeLockAfterSetup` with the approved
  nonzero production value; independently read back the value and its min/max
  bounds.
- [ ] Initial zero-delay setup state, if used, has a bounded purpose and an
  approved finalization step.
- [ ] Pending-action mappings start empty. The only zero-delay actions allowed
  are explicitly approved setup actions that execute and clear before
  timelock finalization; no production-surviving pending row is seeded while
  the action delay is zero.
- [ ] Gate 2 binds candidate ID-6/7 runtimes, interfaces, and pause states, but
  does not claim a live Charlie ID validation: until HQ 8 is swapped, Charlie
  resolves the active legacy VaultBook where IDs 6/7 do not exist. Execute the
  real probes only in the composed fork and immediately after `OP-CORE-04`.

Read-only feasibility observation at the same Base block `50,460,701`: HQ ID 7
was PriceDesk `0x2F7901be53cC94AEf174f1a0764430840360ef53`; its ID 2 was
`0x7b2AEE8B6a4bdF0885dEF48cCda8453fdC1BBA5d` and ID 4 was
`0x16371Faf6f603F8d8D6cef8c46253C80aDeE8b98`. Gate 0 must rebind names,
runtimes, and roles; these addresses do not by themselves prove which source
is Curve/Pyth or authorize constructor inputs.

**STOP — sequential assignment:** if any child confirmation returns
zero/an unexpected ID, a counter/address differs, or the order is not exactly
Alpha→Bravo→Charlie→Delta→Echo, discard the inert candidate Switchboard and
redeploy/requalify it. The core program appends no sixth child.

### 6.3 Departments

- [ ] Teller is constructed paused.
- [ ] AuctionHouse is explicitly paused after deployment and before RipeHQ
  confirmation; its constructor starts unpaused.
- [ ] RipeGov 7 is paused after deployment and remains untouched.
- [ ] Bind the active legacy Charlie from the still-live RipeHQ-ID-6
  Switchboard and use its arbitrary-target `pause(address,bool)` path for the
  separately authorized candidate AuctionHouse and RipeGov-7 pause writes.
- [ ] Read back both candidate pause states before any RipeHQ-ID-6 replacement
  initiation is treated as payload-ready. Once HQ ID 6 points to the new
  Switchboard, legacy boards no longer have candidate pause authority.
- [ ] Stability Pool 6 is unpaused at deployment and remains unpaused at both
  Charlie pointer initiation and execution; record both readbacks. If an
  earlier approved incident pause changed this, an exact authority-bound
  unpause must be fork-qualified and executed under the full cutover freeze.
- [ ] TellerUtils, Lootbox, CreditEngine, CreditRedeem, HR, BondRoom, Boardroom,
  Deleverage, Endaoment paths, and every other approved department have bound
  addresses and runtime hashes.
- [ ] For every candidate that constructs unpaused, `ART-CORE-04` binds an
  exact candidate-address-side mechanism that blocks each externally reachable
  producer/write path before its RipeHQ activation and keeps required
  housekeeping callable. Do not infer safety from “not registered yet,” and
  do not globally pause Lootbox/CreditEngine if doing so blocks migration or
  debt housekeeping.
- [ ] Every candidate dynamically resolves the intended RipeHQ dependencies.
- [ ] No candidate embeds an unintended old/new address.
- [ ] Replacement HumanResources works against every preserved legacy
  Contributor instance, and a new Contributor clone created from the RH
  blueprint passes its complete lifecycle on the composed fork.
- [ ] Replacement BondRoom points to the exact O-11 Booster. If legacy is
  preserved, prove its dynamic active-HQ permissions, every state/config row,
  and the explicitly accepted missing RH reset semantic after HQ6/HQ12 swap.
- [ ] Inventory local `governance`, `pendingGov`, `numGovChanges`, and
  `govChangeTimeLock` state for every candidate. Constructors should use zero
  local governance where qualified; any authorized temporary local governor
  must relinquish before RipeHQ activation, with zero-governance and empty-
  pending readbacks. The preserved RipeHQ Safe remains the global governor.
- [ ] Bind the exact authorized caller for every candidate setup write. A
  candidate that embeds the preserved RipeHQ can be governed by RipeHQ
  governance before it is registry-visible; temporary local governance is
  optional, never assumed, and must be eliminated if used.

### 6.4 VaultMigrator and RipeHQ topology

- [ ] Current RipeHQ IDs 23 and 24 are the expected deployed contracts.
- [ ] At the canonical block, prove `getNumAddrs() == 24` and raw public
  `numAddrs() == 25`; the former is the last assigned ID/count and the latter
  is the next-index counter. Any drift is a stop, not permission to place
  VaultMigrator at another ID.
- [ ] VaultMigrator constructor binds the correct RipeHQ.
- [ ] VaultMigrator constructor binds legacy RipeGov
  `0xe42b3dC546527EB70D741B185Dc57226cA01839D`.
- [ ] VaultMigrator is paused after deployment.
- [ ] The prepared RipeHQ addition manifest/action targets VaultMigrator at
  the next append expected to become ID 25; Phase 2 does not register it and
  the append call itself has no explicit ID argument.
- [ ] Source and compiled-bytecode review confirm the ID-25 hardcoding in
  `Addys` and `SwitchboardEcho`.
- [ ] IDs 26 and 27 remain reserved for the separate Reserve/vesting rollout.
- [ ] The confirmation packet requires immediately pre-confirm
  `getNumAddrs() == 24`, raw `numAddrs() == 25`, and an event/getter census
  showing no other pending append at all unless its exact cancellation/
  terminal disposition was separately approved and completed. Require exact
  typed confirmation result/event `25`, then
  `getAddr(25) == VaultMigrator`, `getNumAddrs() == 25`, and raw
  `numAddrs() == 26`. Any difference is a stop; do not continue to HQ 26.

### 6.5 Candidate-address dossier

`ART-CORE-05` is the checksum-bound output of this section. The RipeHQ,
Switchboard, and VaultBook namespace posture below is closed for the selected
core program; changing any `PRESERVE`, `REPLACE`, `APPEND`, or `NO CORE WRITE`
row is an architecture change that requires a new snapshot, Defaults diff,
composed fork, and approval. Non-RipeHQ dependency rows are mandatory selected
postures, but their identities/compatibility proofs—and O-11—must close before
Gate 1/2 as specified; a blank is a blocker, not permission to choose during
deployment. These are source-pinned ID names and posture—not current-address
proof. Fill all blank identity fields from the canonical Gate-0 block and
deployed receipts.

The existing RipeHQ contract and governance Safe are preserved; RipeHQ itself
is not redeployed.

| HQ ID | Component | Selected core posture | Active address / version | Target address | Runtime + immutables | State / pause / authority disposition | Verifier |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | GREEN token | `PRESERVE` |  | same as active |  | blacklist/mint authority unchanged |  |
| 2 | Savings GREEN | `PRESERVE` |  | same as active |  | token state unchanged |  |
| 3 | RIPE token | `PRESERVE` |  | same as active |  | blacklist/mint authority unchanged |  |
| 4 | Ledger | `PRESERVE — NON-NEGOTIABLE` |  | same as active |  | all accounting remains in place |  |
| 5 | MissionControl | `REPLACE` |  |  |  | transition Defaults + replay/disposition matrix |  |
| 6 | Switchboard registry | `REPLACE` |  |  |  | prepopulated Alpha–Echo; one HQ-6 swap |  |
| 7 | PriceDesk | `PRESERVE` |  | same as active |  | registry and sources unchanged in core |  |
| 8 | VaultBook | `REPLACE` |  |  |  | prepopulated exact 1–5 plus 6/7 |  |
| 9 | AuctionHouse | `REPLACE` |  |  |  | candidate paused before confirmation |  |
| 10 | AuctionHouseNFT | `REPLACE` |  |  |  | state/pause disposition bound |  |
| 11 | Boardroom | `REPLACE` |  |  |  | pending/state disposition bound |  |
| 12 | BondRoom | `REPLACE` |  |  | constructor-initialized, Switchboard-mutable legacy BondBooster pointer bound | BondBooster exception/config/permission proof bound |  |
| 13 | CreditEngine | `REPLACE` |  |  |  | debt/config state disposition bound |  |
| 14 | Endaoment | `REPLACE` |  |  |  | custody/allowance disposition bound |  |
| 15 | HumanResources | `REPLACE` |  |  |  | existing Contributor compatibility + new RH blueprint + TimeLock setup bound |  |
| 16 | Lootbox | `REPLACE` |  |  |  | local config replay; Ledger rewards preserved |  |
| 17 | Teller | `REPLACE` |  |  |  | constructed paused |  |
| 18 | Deleverage | `REPLACE` |  |  |  | configuration and route state bound |  |
| 19 | CreditRedeem | `REPLACE` |  |  |  | configuration/custody disposition bound |  |
| 20 | TellerUtils | `REPLACE` |  |  |  | runtime/immutable bound |  |
| 21 | EndaomentFunds | `REPLACE` |  |  |  | custody/allowance disposition bound |  |
| 22 | EndaomentPSM | `REPLACE` |  |  |  | enablement, caps, intervals, custody bound |  |
| 23 | RIPE CCIP pool | `PRESERVE` |  | same as active |  | CCIP state unchanged |  |
| 24 | GREEN CCIP pool | `PRESERVE` |  | same as active |  | CCIP state unchanged |  |
| 25 | VaultMigrator | `APPEND — REQUIRED` | expected absent |  | Base legacy-RipeGov immutable | paused outside windows |  |
| 26 | RipeReserveEngine | `NO CORE WRITE — RESERVED` | expected absent | N/A | N/A | separate Reserve program |  |
| 27 | RipeReserveVesting | `NO CORE WRITE — RESERVED` | expected absent | N/A | N/A | separate Reserve program |  |

| Switchboard child ID | Board | Selected core posture | Active child | Candidate child | Runtime / TimeLock / authority proof | Verifier |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | Alpha | `REPLACE IN NEW REGISTRY` |  |  | live-bound preserved-PriceDesk Pyth child ID, expected 4; stop on drift |  |
| 2 | Bravo | `REPLACE IN NEW REGISTRY` |  |  |  |  |
| 3 | Charlie | `REPLACE IN NEW REGISTRY` |  |  |  |  |
| 4 | Delta | `REPLACE IN NEW REGISTRY` |  |  |  |  |
| 5 | Echo | `REPLACE IN NEW REGISTRY` |  |  |  |  |
| next append, currently expected 6 | Foxtrot candidate | `UNASSIGNED IN CORE; POLICY-RESERVED FOR SEPARATE RESERVE PROGRAM` | N/A | N/A | fresh topology/source/activation bind required |  |

The pinned RH tree contains `SwitchboardFoxtrot.vy`, but no contract hardcodes
Foxtrot to child ID 6. The core program registers only Alpha–Echo. “6” is the
expected next sequential append only if the fresh topology is still 1–5; it is
not a fixed namespace or permission to append Foxtrot.

| VaultBook ID | Selected core posture | Active/target address | Runtime/version proof | Pause/state proof | Verifier |
| ---: | --- | --- | --- | --- | --- |
| 1 | `PRESERVE` exact live legacy Stability Pool |  |  |  |  |
| 2 | `PRESERVE` exact live legacy RipeGov | `0xe42b3dC546527EB70D741B185Dc57226cA01839D` |  |  |  |
| 3 | `PRESERVE` exact live row |  |  |  |  |
| 4 | `PRESERVE` exact live row |  |  |  |  |
| 5 | `PRESERVE` exact live row |  |  |  |  |
| 6 | `APPEND` new RH Stability Pool |  |  | unpaused for Charlie |  |
| 7 | `APPEND` new RH RipeGov |  |  | paused/pristine |  |

| Non-RipeHQ dependency | Selected core posture | Exact identity / constructor consumer / state proof | Verifier |
| --- | --- | --- | --- |
| Contributor blueprint for future HR clones | `DEPLOY NEW RH BLUEPRINT; ALLOWLIST ONLY MC hrConfig.contribTemplate` | bytecode, constructor/blueprint identity, Defaults consumer, new-clone test |  |
| Existing Contributor instances in Ledger | `PRESERVE` | complete instance census plus legacy-instance/replacement-HR compatibility proof |  |
| BondBooster used by replacement BondRoom | `PRESERVE LEGACY — SOURCE-DIVERGENT EXCEPTION SUBJECT TO O-11` | bind pointer, all config/grant/usage state, dynamic HQ6/HQ12 permissions, and accepted omission of RH expired/absent-grant reset semantics |  |
| PriceDesk root and child registry | `PRESERVE EXACT LIVE ROOT, ORDER, AND CHILD ADDRESSES` | bind every child; Alpha Pyth child ID expected 4 and every Curve consumer ID expected 2; stop if live differs |  |
| TrainingWheels | `PRESERVE EXACT LIVE ADDRESS` | transition Defaults and consumer readbacks |  |
| Underscore registry | `REPLAY EXACT LIVE ADDRESS INTO REPLACEMENT MC` | transition Defaults and post-constructor readback |  |
| External pools/oracle feeds referenced by candidates | `PRESERVE EXACT LIVE REFERENCES` | one constructor/config row per consumer; any change is an explicit architecture diff |  |
| Allowances granted to or by replaced departments | `EXACT PER-COMPONENT DISPOSITION REQUIRED; NO IMPLICIT CARRYOVER` | §4.7 before/after allowance rows and establishing/revoking child operations |  |
| Token/native custody held by replaced departments | `EXACT PER-COMPONENT DISPOSITION REQUIRED; NO STRANDED CUSTODY` | §4.7 balance owner, transfer/recovery route, receipt, and terminal reconciliation |  |

### GATE 2 — Inert candidate qualification

- [ ] Every candidate is deployed and bytecode-qualified.
- [ ] `ART-CORE-05` is complete, checksum-bound, and independently reproduced.
- [ ] Contributor blueprint/legacy-instance compatibility, Alpha Pyth/Curve ID
  bindings, O-11 BondBooster posture, external references, allowances, and
  custody dispositions are exact and independently reproduced; no non-RipeHQ
  dependency row remains generic or blank.
- [ ] The candidate stack is inert or protected by the approved pause/freeze
  posture.
- [ ] Registry IDs and constructor immutables are final.
- [ ] Candidate VaultBook and Switchboard registry delays are the approved
  nonzero production values; neither remains in setup-zero registry mode.
- [ ] No unapproved temporary local governor or pending governance change
  remains on a candidate.
- [ ] ID 25 remains available and no registry activation is inferred from the
  inert deployment or local manifest.
- [ ] No RipeHQ or VaultBook activation has been inferred from a local manifest.
- [ ] Gate evidence: __________________________________________
- [ ] Independent reviewer: __________________________________

---

## 7. Phase 3 — Frontend, indexer, keeper, and monitoring readiness

**Environment / writes / authority:** application/operations environments;
release and communication changes require their normal owner approvals. No Base
contract write is authorized here.

### 7.1 Legacy Pool-1 access

- [ ] Frontend/indexer displays positions in both Pools 1 and 6.
- [ ] Pool-1 withdrawal supplies explicit `vaultId = 1`.
- [ ] Pool-1 claim supplies explicit `vaultId = 1`.
- [ ] Pool-1 redemption supplies explicit `vaultId = 1`.
- [ ] No Pool-1 operation relies on zero-ID resolution after cutover.
- [ ] Callers use the RH batch claim/redemption interfaces.
- [ ] Removed or obsolete single-item selectors are not called.
- [ ] Pool 1 is clearly labeled legacy/exit-only.

### 7.2 New Pool-6 access

- [ ] Zero-ID sGREEN and LP deposits resolve to VaultBook ID 6.
- [ ] `convertToSavingsGreenAndDepositIntoStabPool` resolves to ID 6 after the
  Charlie pointer change.
- [ ] CreditEngine and CreditRedeem trusted deposits resolve to ID 6.
- [ ] Pool 6 deposit, withdrawal, claim, and redemption displays are correct.
- [ ] Users at the Ledger vault limit receive an explicit, tested UX path.

### 7.3 RipeGov transitional behavior

- [ ] RipeGov 2 remains visible and is shown as the active core vault.
- [ ] RipeGov 7 is not offered as a deposit target.
- [ ] HR, bonds, and Lootbox auto-stake continue resolving to 2.
- [ ] No UI or keeper calls RH-only accrual-disable or migration selectors
  against legacy RipeGov 2.

### 7.4 Monitoring and alerting

- [ ] Alert if Pool 1 appears in any priority or special liquidation route.
- [ ] Alert on any new Pool-1 deposit after cutover unless it exactly matches
  the separately approved Phase-8 atomic seed transaction.
- [ ] Alert on any RipeGov-7 balance, shares, points, or registered user before
  its migration window.
- [ ] Monitor Pool-6 spendable capacity separately by stability asset.
- [ ] Monitor auction fall-through, failed liquidations, and unauctioned
  residual collateral.
- [ ] Monitor user/delegation replay completeness.
- [ ] Monitor VaultMigrator pause state.
- [ ] Monitor all source-vault holder and claim counts through closeout.

### GATE 3 — Off-chain readiness

- [ ] Production frontend/indexer/keeper releases are deployed and verified.
- [ ] Explicit legacy-ID paths pass end-to-end tests.
- [ ] Monitoring and incident contacts are live.
- [ ] User communication and transitional deadline are published.
- [ ] Teller reopening is blocked until this gate passes.
- [ ] Gate evidence: __________________________________________
- [ ] Independent reviewer: __________________________________

---

## 8. Phase 4 — Composed Base-fork rehearsal

**Environment / writes / authority:** Base fork only; reproduce intended writes
without broadcasting any Base mainnet transaction.

After inert candidates are deployed, bind a fresh finalized pre-cutover Base
block/hash and fork from it. Use the exact on-chain candidate addresses,
runtime/immutable readbacks, configuration artifacts, registry payloads, and
Safe calldata intended for the operation. If rehearsing before deployment,
replay every deterministic deployment and later repeat the composed rehearsal
from the actual post-deployment pin; Gate-0 alone is not sufficient.

`ART-CORE-05` is a required input. No fork using placeholder candidate
addresses, runtimes, pause states, or authorities can satisfy this phase.

### 8.1 Core-cutover rehearsal

- [ ] Mature the exact RipeHQ actions while the legacy stack remains live.
- [ ] Exercise the complete freeze, including Teller, AuctionHouse,
  Deleverage/governance paths, HR, bonds, Lootbox auto-stake, CreditEngine,
  CreditRedeem, and every trusted producer.
- [ ] Confirm the replacement VaultBook before any ID-6 validation.
- [ ] Rehearse the pre-activation candidate pauses through the still-active
  legacy Charlie, then prove candidate AuctionHouse and RipeGov 7 are paused
  before the one HQ-ID-6 Switchboard-registry replacement removes legacy-board
  authority.
- [ ] In one assertion-capable atomic child, confirm HQ 5 MissionControl first
  and exactly one replacement HQ 6 Switchboard registry second, then read both
  back before the closed department allowlist. Do not update Alpha–Echo
  children in the live legacy Switchboard.
- [ ] Read back fresh Charlie `actionTimeLock == 0` before replay or pointer
  initiation.
- [ ] Initiate and execute all approved nonzero `userConfig` and
  `userDelegation` replays during the same bounded frozen setup window.
- [ ] Reconcile every pending-state disposition.
- [ ] After the simulated HQ swaps, attempt every retained legacy pending row at
  its relevant before/maturity/expiry boundaries. Prove no unapproved row can
  mutate the replacement stack, including legacy rows whose stored
  MissionControl is zero and therefore fall back to current HQ ID 5.
- [ ] Prove setup-zero actions execute and clear before timelock finalization;
  initiate every approved production-surviving pending action only afterward
  and verify its confirmation/expiry were calculated from the production
  delay.
- [ ] Initiate and execute Charlie `preferredStabVaultId: 1 -> 6` during that
  same zero-delay setup window.
- [ ] Verify no externally reachable write occurs during the temporary
  route/pointer mismatch.
- [ ] Finalize normal Charlie and other Switchboard action timelocks only after
  all replay and pointer readbacks pass.
- [ ] Seed Pool 6 according to policy, or exercise the approved empty-pool
  posture.
- [ ] Exercise every preserved legacy Contributor instance against replacement
  HR, create/use a new RH-blueprint Contributor, execute the selected O-11
  Booster compatibility cases, and prove Alpha resolves the preserved Pyth and
  Curve children at their live-bound IDs.
- [ ] Unpause only after all route readbacks pass.

#### 8.1.1 Producer-freeze and dependency matrix

This blank table is a template, not evidence. Instantiate it for the core,
Stability, and RipeGov windows inside checksum-bound `ART-CORE-04`; Gate 4 is
unpassable while the applicable instance contains a blank mechanism or proof.
“Blocked” means the named producer entrypoints cannot be reached; it does not
mean a shared dependency may be globally paused. During the core handoff,
instantiate separate rows for the exact legacy and candidate address of every
component; a consolidated component label without generation/address is not
evidence.

| Component / generation / exact address | Entry points/state-changing roles that must be blocked | Functions/state that must remain callable | Window-specific proof |
| --- | --- | --- | --- |
| Teller | Ordinary user writes while frozen | Bounded seed calls only when explicitly listed; migration helpers while Teller itself is paused |  |
| AuctionHouse | Liquidations, swaps, auction intake | Required read-only reconciliation |  |
| CreditEngine / CreditRedeem | Borrow/redeem/trusted deposits that can mutate source or seed a vault | `updateDebtForUser` and debt-health reads |  |
| Lootbox | User/keeper reward claims and auto-stake producer paths | `updateDepositPoints`, approved settlement/cleanup, point reads |  |
| Ledger | Unauthorized direct mutation | `checkAndUpdateLastTouch`, participation, debt/reward state |  |
| PriceDesk / price sources | Governance/config changes | Price reads and required snapshots |  |
| HR / BondRoom / Deleverage / other trusted departments | Every deposit, auto-stake, transfer, or withdrawal producer path | Required read-only reconciliation |  |
| Source / target vaults | As specified by the exact route | Exact route-specific pause matrix |  |

- [ ] Every `_isValidRipeAddr` producer is assigned an exact block mechanism.
- [ ] Ledger, CreditEngine, Lootbox, PriceDesk, and every required pricing
  source remain unpaused/callable at each seed and migration canary.
- [ ] A composed negative test proves each blocked producer cannot mutate the
  source while every required dependency call still succeeds.

### 8.2 Negative and fallback tests

- [ ] Negative control proves RH AuctionHouse reverts if Pool 1 is deliberately
  placed in a Stability liquidation route.
- [ ] Production candidate proves Pool 1 is absent from every such route.
- [ ] For every live `shouldSwapInStabPools` asset, prove behavior with:
  - [ ] empty Pool 6;
  - [ ] partially funded Pool 6;
  - [ ] enough Pool-6 capacity;
  - [ ] unavailable/ineligible Pool-6 cohort; and
  - [ ] auction fallback and residual accounting.
- [ ] Confirm every swap-enabled asset has `shouldAuctionInstantly = True` at
  the bound block or stop.
- [ ] Confirm every `specialStabPoolId` is 0 or 6.
- [ ] Confirm GREEN/sGREEN burn routes and Endaoment-transfer routes are tested
  separately from Stability swaps.

### 8.3 Failure atomicity and rollback boundaries

- [ ] Simulate failure before any registry confirmation.
- [ ] Simulate failure after VaultBook confirmation but before pointer change.
- [ ] Simulate failure after MissionControl confirmation but before reopen.
- [ ] Simulate a user/config replay failure.
- [ ] Simulate a seed failure.
- [ ] Simulate a late readback mismatch.
- [ ] Inject an expired/invalid TimeLock action that returns `False` and clears
  itself without reverting; prove no dependent write is treated as successful.
- [ ] Inject a legacy RipeHQ append/update confirmation that returns zero or
  `False`; prove the exact child operation stops and no later confirmation is
  inferred from low-level call success.
- [ ] For every safety-dependent atomic bundle, prove the selected execution
  primitive decodes and asserts every typed return and reverts the EVM
  transaction on semantic failure. A raw Safe MultiSend plus a later readback
  does not meet this requirement.
- [ ] Prove the system remains paused/frozen on every pre-reopen failure.
- [ ] Document the exact separately rehearsed registry rollback, if any.
- [ ] Do not use Pool 1 as a rollback liquidation route while RH AuctionHouse is
  active.
- [ ] Prove pause-only incident containment after reopen.

### 8.4 Safe and gas qualification

- [ ] Exact Safe calldata decodes to the approved call list and order.
- [ ] Safe nonce, guard, modules, and signers match production.
- [ ] Every timelock and native pending-operation key is recorded: action ID
  where exposed, registry ID for an address update, and candidate address for
  a registry append.
- [ ] Every call card declares `revert-only`, `returns bool`, `returns uint`, or
  another exact return type, plus its required success value.
- [ ] `TX-ASSERT` names the exact assertion-capable executor/wrapper or the
  deliberately separated fail-safe transaction/readback boundary for each
  soft-return call. Its deployed runtime, authority, calldata, and failure
  behavior are fork-qualified; no mechanism is assumed from the word
  “MultiSend.”
- [ ] Composed gas fits Base limits with approved margin.
- [ ] Canary and late-failure rehearsals pass.
- [ ] Post-transaction readbacks are scripted and independently reproduced.

### GATE 4 — Fork-qualified cutover

- [ ] `ART-CORE-04` and `ART-CORE-05` are complete and checksum-bound.
- [ ] The core branch of `TX-ASSERT` is closed for every soft-return call.
- [ ] Exact cutover payload passes the composed fork rehearsal.
- [ ] Every negative control fails for the expected reason.
- [ ] Every postcondition has a deterministic readback.
- [ ] Incident containment and rollback boundaries are understood.
- [ ] Gate evidence: __________________________________________
- [ ] Independent reviewer: __________________________________

---

## 9. Phase 5 — Pre-stage the RipeHQ transition

**Environment / writes / authority:** Base mainnet governance action starts;
each initiation requires a separately approved Safe payload.

**Operation family:** `OP-CORE-02`; one child ID per native RipeHQ replacement
or append initiation.

- [ ] Obtain separate authorization to initiate each RipeHQ registry
  operation.
- [ ] Include the VaultMigrator addition at exactly RipeHQ ID 25 in the
  separately approved action-start manifest.
- [ ] Diff the action-start manifest against the closed §6.5 posture: updates
  are exactly IDs 5, 6, and 8–22; IDs 1–4, 7, 23, and 24 have no core update;
  ID 25 is the only append; IDs 26 and 27 have no core write.
- [ ] For every address replacement, bind operation type, registry ID, exact
  old/new address, `initiatedBlock`, and `confirmBlock`.
- [ ] For every append, bind operation type, candidate-address native key,
  description, expected assigned registry ID, `initiatedBlock`, and
  `confirmBlock`.
- [ ] Immediately before starting the VaultMigrator append, repeat the complete
  pending-append census and clear every unrelated entry through its separately
  approved disposition; do not rely on current immaturity.
- [ ] Do not invent an action ID or expiry for either RipeHQ operation type.
- [ ] Initiate only that exact replacement/addition allowlist. Any omitted,
  extra, reordered, or changed-posture row is an architecture stop.
- [ ] Keep the legacy system operating while the bound live
  `registryChangeTimeLock` delay matures; record each actual confirmation
  block rather than assuming 21,600.
- [ ] Monitor every global, asset, reward, route, signer, authority, userConfig,
  delegation, and other value copied into the candidate MissionControl or
  disposition matrix.
- [ ] Require exact equality with the qualified transition manifest immediately
  before cutover, including an event-derived and getter-verified no-drift
  report.
- [ ] If any copied value changes, abort the candidate action package, rebuild
  the transition artifact/candidate state, repeat the fork, and re-mature the
  required governance actions; do not patch an unreviewed delta in the window.
- [ ] Confirm every RipeHQ operation remains pending, mature, byte-exact, and
  neither cancelled nor replaced. RipeHQ registry operations do not expire;
  expiry checks apply separately to TimeLock-based board actions.
- [ ] Re-read all pending actions on both legacy and candidate components
  immediately before the freeze. For every legacy board action that has not
  been executed or cancelled, bind its exact target/value, confirmation and
  expiry blocks, authority after the HQ swaps, and target resolution after
  replacement MissionControl activation.
- [ ] Re-simulate the exact confirmation payload against current state.
- [ ] Through the still-active legacy Charlie, confirm the separately
  authorized candidate AuctionHouse and RipeGov-7 pause calls have executed
  and read back `True`; do not defer either pause until after HQ-ID-6
  replacement.
- [ ] Confirm the candidate Teller is paused.
- [ ] Confirm RipeGov 7 is paused and pristine.
- [ ] Confirm VaultMigrator is paused.

### GATE 5 — Mature, unchanged actions

- [ ] Every approved action is mature and exactly matches its manifest.
- [ ] The exact §6.5 replacement allowlist and single ID-25 append match; no
  preserve/reserved row has a pending core action.
- [ ] Candidate AuctionHouse and RipeGov 7 are paused while legacy Charlie
  still has authority; their pause receipts/readbacks are in `ART-CORE-05`.
- [ ] No unapproved legacy or candidate action is executable now or can mature
  later. A legacy action may be left without cancellation only if it is
  already expired or otherwise permanently non-executable and the fork proves
  its exact target is harmless; a merely immature action is not abandoned.
- [ ] The core-cutover authorization binds current calldata and Safe nonce.
- [ ] Gate evidence: __________________________________________
- [ ] Independent reviewer: __________________________________

---

## 10. Phase 6 — Execute the RH core cutover

**Environment / writes / authority:** Base mainnet cutover writes; requires a
new, exact-payload authorization after Gates 0–5. This runbook is not that
authorization.

### 10.1 Final preflight

- [ ] Re-record finalized block/hash and Base head.
- [ ] Re-read every registry address, pause state, pending action, configuration
  value, and Safe parameter.
- [ ] Reconcile any user activity since the fork snapshot.
- [ ] Confirm every copied configuration/state value is exactly equal to the
  transition manifest; any mismatch invalidates the candidate and cutover.
- [ ] Confirm no critical oracle, auction, debt, claim, or bad-debt condition is
  active outside the rehearsed envelope.
- [ ] Confirm operators, reviewers, incident responders, and signers are live.
- [ ] Confirm Gate 3 off-chain releases are active.

### 10.2 Complete freeze

**Operation family:** `OP-CORE-03`.

- [ ] Pause legacy Teller.
- [ ] Pause/disable legacy AuctionHouse liquidation entry.
- [ ] Pause or disable Deleverage paths that can reach vault withdrawal.
- [ ] Disable HR deposits/transfers that can mutate source positions.
- [ ] Disable BondRoom auto-stake/deposits.
- [ ] Block externally reachable Lootbox claim/auto-stake producer entrypoints
  without pausing the Lootbox functions required for point accounting.
- [ ] Block CreditEngine/CreditRedeem borrow, redeem, and trusted-deposit
  producer entrypoints without pausing `CreditEngine.updateDebtForUser`.
- [ ] Disable every other `_isValidRipeAddr` trusted producer.
- [ ] Apply the same entrypoint-level controls to every candidate generation
  address before it becomes the active HQ row. Keep both the legacy and
  candidate generations blocked through their handoff; for each, separately
  prove the exact Lootbox/CreditEngine/price/housekeeping calls that must remain
  callable.
- [ ] Wait for the required later action-block boundary.
- [ ] Prove source position counts and balances stop changing before the first
  confirmation and after each generation handoff.

### 10.3 Registry and configuration order

**Operation families:** `OP-CORE-04` through `OP-CORE-08`. Every actual
confirmation, action execution, or setup-finalization transaction uses its own
dated child ID.

- [ ] Confirm replacement VaultBook first (`OP-CORE-04`). Require typed
  `True`, the expected event, and active ID-8 address/version readback before
  any dependent validation.
- [ ] Read back IDs 1–7 and exact addresses.
- [ ] With candidate VaultBook now active but before HQ5/HQ6 confirmation,
  verify the candidate Pool-6/7 interfaces and pause states. Run only board
  validations whose target MissionControl can be supplied explicitly; run
  validations that necessarily resolve active HQ5/HQ6 immediately after their
  atomic swap/readback. Never treat a Gate-2 placeholder probe as production
  evidence.
- [ ] Under one assertion-capable atomic `OP-CORE-05` child, confirm
  MissionControl at HQ ID 5 first and exactly one prepopulated Switchboard-
  registry replacement at HQ ID 6 second. Require typed `True` from both
  confirmations and revert the whole transaction if either semantic result
  fails. Do not submit Alpha–Echo child updates to the legacy Switchboard.
- [ ] Immediately after that atomic receipt, read back exact HQ IDs 5 and 6,
  candidate board resolution to the new MC, and unchanged complete freeze
  posture before confirming any department or replaying configuration. A raw
  MultiSend or separated 5/6 swap is not selected; either would require a new
  gap-specific authority/freeze proof.
- [ ] Confirm exactly the remaining §6.5 `REPLACE` rows—HQ IDs 9–22—while
  AuctionHouse remains paused. Require the typed `True`, event, and exact
  address/version readback for each child operation before marking it complete.
- [ ] Immediately before each ID 9–22 confirmation, prove the specific
  candidate's externally reachable ingress is blocked; immediately afterward,
  prove both its replaced legacy address and newly active candidate address
  remain blocked while the required dependency calls remain callable. Stop on
  any source-state delta.
- [ ] Immediately before confirming the VaultMigrator append, require
  `getNumAddrs() == 24`, raw public `numAddrs() == 25`, and an independently
  reproduced event/getter census with no other pending append at all except an
  explicitly approved terminal disposition already completed. Require the
  typed confirmation result/event to assign exactly ID 25, then read back
  `getAddr(25) == VaultMigrator`,
  `getNumAddrs() == 25`, raw `numAddrs() == 26`, its paused state, runtime
  hash, and Base legacy RipeGov immutable. Any different result is a stop;
  the append call has no explicit ID argument.
- [ ] Confirm Ledger remains the exact deployed address at RipeHQ ID 4.
- [ ] Re-prove candidate AuctionHouse and RipeGov 7 remained paused across the
  HQ-ID-6 authority handoff; only the new Charlie may change their pause state
  after that confirmation.
- [ ] Under `OP-CORE-06`, read back fresh Charlie `actionTimeLock == 0` before initiating any
  replay or pointer action.
- [ ] Initiate and execute every approved `userConfig` row during the bounded
  zero-delay setup window.
- [ ] Initiate and execute every approved `userDelegation` row during that
  same window.
- [ ] Resolve every legacy/candidate pending-state row by explicit disposition.
  A setup-only row may be initiated, executed, read back, and cleared while
  delay is zero. A production-surviving row must be executed before the swap,
  cancelled on the old component, or left uninitiated on the candidate until
  after production timelock finalization; it may not be “reseeded” at zero
  delay. Treat a legacy row as closed without execution/cancellation only when
  it is already expired or permanently non-executable and its exact target is
  fork-proven harmless. Mere intent not to call it is not cancellation.
- [ ] Read back every replayed row.
- [ ] Under `OP-CORE-07`, verify Pool 6 is unpaused immediately before Charlie
  initiation and again immediately before execution.
- [ ] Initiate and execute Charlie `preferredStabVaultId = 6` while
  `actionTimeLock == 0` and the complete protocol freeze remains in force.
- [ ] Read back `preferredStabVaultId == 6`.
- [ ] Under `OP-CORE-08`, only after every setup-zero replay and pointer action
  is complete, call the one-time `setActionTimeLockAfterSetup` on every—and
  only—newly deployed TimeLock component whose `ART-CORE-05` row proves an
  initial zero delay. For the selected posture this expected set is
  Alpha–Echo and HumanResources; stop if the final manifest differs.
- [ ] For each component, bind the approved nonzero value, verify its min/max
  bounds, and independently read back `actionTimeLock` after the call.
- [ ] Only after every applicable production delay is nonzero, initiate each
  explicitly approved production-surviving action as its own child. Bind its
  new action ID, stored tuple, initiation/confirmation blocks, expiry, and
  proof that its confirmation block reflects the production delay; execute it
  only under its separately authorized later operation.
- [ ] Re-read the already-finalized VaultBook and Switchboard
  `registryChangeTimeLock` values; neither may be zero or differ from Gate 2.
- [ ] Re-read every candidate local governor and pending governance change;
  require the approved zero/empty posture and unchanged preserved RipeHQ Safe
  governance before any reopen.
- [ ] Prove no pending action created under a zero action delay remains on any
  candidate at reopen.
- [ ] Prove no unapproved pending action remains on any legacy or candidate
  component that is executable now or can become executable later. This check
  includes old boards still governed through preserved RipeHQ authority and
  actions that dynamically resolve the now-active HQ-5 MissionControl.

**STOP:** if fresh Charlie has a nonzero action timelock, this ordered cutover
cannot use the rehearsed same-window sequence. Re-plan the activation order or
accept a separately measured, fully frozen timelock interval; do not improvise
around the governance delay.

### 10.4 Pool-6 initialization and activation

**Operation family:** `OP-CORE-09`.

- [ ] Read back sGREEN `vaultIds == [6]`.
- [ ] Read back LP `vaultIds == [6]`.
- [ ] Read back `priorityStabVaults` contains only ID 6.
- [ ] Read back every `specialStabPoolId` is 0 or 6.
- [ ] Read back `preferredStabVaultId == 6`.
- [ ] Read back `isStabVaultId(1) == True`.
- [ ] Read back `isStabVaultId(6) == True`.
- [ ] Verify Pool 6 is unpaused.
- [ ] Keep AuctionHouse paused.
- [ ] Confirm Ledger, CreditEngine housekeeping, Lootbox point accounting,
  PriceDesk, and every required price source are callable.
- [ ] If Decision O-1 requires funding, atomically unpause Teller, deposit each
  approved seed asset into explicit `vaultId = 6`, and re-pause Teller.
- [ ] Treat each first deposit as that asset's Pool-6 registration; do not
  assume a separate public registration call exists.
- [ ] Prove every injected approval/deposit/re-pause failure reverts the whole
  bundle.
- [ ] If Decision O-1 accepts an empty Pool 6, record the approved `N/A` seed
  disposition and the exact empty-pool fallback proof.
- [ ] Record shares, custody, total balances, registered assets, and claim
  reservations after the seed or empty-pool decision.
- [ ] Re-run the auction-fallback preflight with production values.

**STOP:** if Decision O-1 requires funding and the exact depositor identity,
explicit-ID-6 route, Teller pause bundle, allowance, housekeeping, receipt, or
post-deposit readback did not pass the composed production fork, do not unpause
AuctionHouse. If an empty Pool 6 is approved, the exact empty and partial
fallback cases must pass instead.

### 10.5 RipeGov continuity readbacks

- [ ] `coreRipeGovVaultId == 2`.
- [ ] `isRipeGovVaultId(2) == True`.
- [ ] RIPE routes are exactly `[2]`.
- [ ] RIPE/LP routes are exactly `[2]`.
- [ ] RipeGov 7 remains paused.
- [ ] RipeGov 7 has zero balances, shares, users, registrations, points, and
  migrated-position markers.

### 10.6 Reopen

**Operation family:** `OP-CORE-10`.

- [ ] All configuration/state readbacks match the approved post-cutover
  manifest.
- [ ] Seed or accepted fallback posture matches Decision O-1.
- [ ] Unpause RH Teller.
- [ ] Execute the approved bounded Pool-6 deposit canary, or record `N/A` if
  the owner-approved empty-pool posture prohibits funding.
- [ ] Re-enable only the approved replacement-generation trusted producers;
  keep replaced department addresses blocked except for exact residual paths
  in the disposition matrix.
- [ ] Execute a canary explicit Pool-1 read/exit path if economically safe and
  pre-approved.
- [ ] Execute/read a canary legacy RipeGov-2 operation.
- [ ] Unpause RH AuctionHouse last.
- [ ] Execute/read the approved liquidation/fallback smoke test.
- [ ] Confirm monitoring observes the new routes.

### 10.7 Post-cutover transaction record

| Action | Transaction / native pending-operation key | Block | Readback status |
| --- | --- | ---: | --- |
| Freeze |  |  |  |
| VaultBook confirmation |  |  |  |
| MissionControl/Switchboard confirmation |  |  |  |
| Department confirmations |  |  |  |
| User config/delegation replay |  |  |  |
| Charlie pointer change |  |  |  |
| Pool-6 seed |  |  |  |
| Teller/producers unpause |  |  |  |
| AuctionHouse unpause last |  |  |  |

### GATE 6 — RH core live

- [ ] Ledger continuity is proven.
- [ ] All RH departments resolve the intended new dependencies.
- [ ] Pool 1 is legacy exit-only.
- [ ] Pool 6 receives all new Stability deposits and is the sole Stability-pool
  liquidation route/target; rejected or partial fills follow the proven
  AuctionHouse fallback.
- [ ] RipeGov 2 remains core and RipeGov 7 remains pristine.
- [ ] No unexplained revert, balance delta, event, or monitoring alert remains.
- [ ] Gate evidence: __________________________________________
- [ ] Independent reviewer: __________________________________

---

## 11. Phase 7 — Transitional operation

**Environment / writes / authority:** Base mainnet monitoring is read-only.
Only pre-authorized incident pauses or separately governed configuration writes
may change state.

**Monitoring family:** `MON-TRANSITION-01`; each cadence emits a checksum-bound
`ART-TRANSITION-01` record.

### Daily/recurring controls

Create a new signed checklist instance for every monitoring interval; do not
check these once for the entire transition.

| Observation time | Finalized block/hash | Operator | Checklist evidence/hash | Alerts / disposition | Verifier |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |

| Transitional control | Automated cadence | Signed-attestation cadence | Alert threshold | Response SLA | Owner | Evidence sink |
| --- | --- | --- | --- | --- | --- | --- |
| Pool 1 absent from liquidation routes |  |  | Any occurrence |  |  |  |
| No unauthorized Pool-1 deposit |  |  | Any occurrence |  |  |  |
| RipeGov 7 remains pristine |  |  | Any nonzero state |  |  |  |
| Pool-6 spendable capacity |  |  | Decision O-1 threshold |  |  |  |
| Explicit legacy exits remain functional |  |  | Any failed approved canary/synthetic check |  |  |  |
| Transition census and deadline |  |  | Decision O-2 threshold |  |  |  |

- [ ] Verify Pool 1 is absent from every liquidation route.
- [ ] Verify no new Pool-1 deposits have occurred outside the exact approved
  Phase-8 atomic seed transaction.
- [ ] Verify explicit Pool-1 exits/claims/redemptions remain functional.
- [ ] Track Pool-1 users, shares, custody, active claims, dormant claims, and
  Ledger participation.
- [ ] Track Pool-6 capacity, claims, liquidations, auctions, and residuals.
- [ ] Verify Pool 7 remains pristine.
- [ ] Track growth/change in the RipeGov-2 migration census.
- [ ] Track users blocked by the Ledger vault limit.
- [ ] Track the approved transition deadline.
- [ ] Reconcile any configuration or registry change against this runbook.

### Important interpretation

Removing Pool 1 from AuctionHouse routing prevents new liquidation-driven
claim additions. It does not freeze the basket: claims can reduce it,
redemptions can transform it, and prices/share distribution can change.

### Escalation triggers

- Pool 1 reappears in a liquidation route.
- Any RipeGov-7 state becomes nonzero before migration.
- Auction fallback fails or leaves unhandled collateral.
- Pool-6 capacity falls below the approved threshold.
- An explicit legacy exit path fails.
- User/delegation replay is found incomplete.
- Transition deadline or user-impact threshold is breached.
- An unapproved registry/configuration action is initiated.

If any trigger fires, pause the affected entry points and invoke the approved
incident plan. Do not route RH AuctionHouse back to Pool 1.

### GATE 7 — Transitional operation controlled

- [ ] Core invariants have remained continuously true for the reviewed
  observation period.
- [ ] No unresolved transition alert or user-impact escalation remains.
- [ ] Decision O-5 and the owner/due-date fields for O-9 and O-10 are current.
- [ ] A separate owner authorization permits preparation—not execution—of the
  fresh Phase-8 evidence and fork package.
- [ ] Gate evidence: __________________________________________
- [ ] Independent reviewer: __________________________________

---

## 12. Phase 8 — Stability Pool 1 to 6 migration

**Environment / writes / authority:** Base mainnet migration writes; this phase
requires a separate new Safe authorization after a fresh fork qualification.

This is a separate maintenance window. Re-run the binding,
census, fork rehearsal, Safe simulation, and approval gates; do not reuse the
core-cutover snapshot.

### 12.1 Fresh bind and census

- [ ] Bind current release/runtime hashes and all addresses.
- [ ] Bind finalized block/hash.
- [ ] Re-enumerate every Pool-1 user, asset, balance, share, Ledger entry, and
  Lootbox record.
- [ ] Re-run the deployment-to-pin event census and prove per-asset raw-share
  closure against every Pool-1 aggregate getter.
- [ ] Re-enumerate every active iterable and dormant/raw claim pair, including
  residue outside the current `numClaimableAssets` endpoint; do not infer the
  number of active rows from stale array slots.
- [ ] Recompute exact claim USD values with bound price sources.
- [ ] Classify every claim pair as claimable, redeemable, dormant, dust,
  unpriceable, or otherwise blocked.
- [ ] Record current Pool-1 custody and reservations by stability asset.
- [ ] Record current Pool-6 user state and capacity.
- [ ] Recalculate batch size and gas from actual users/assets.
- [ ] Confirm `badDebt == 0` and every migration health gate.
- [ ] Snapshot the full rewards auto-stake tuple:
  `autoStakeRatio`, `autoStakeDurationRatio`, and
  `stabPoolRipePerDollarClaimed`.
- [ ] Re-adjudicate the block-50,459,811 VVV/mcbETH planning observation; no
  address, raw amount, registration state, or claim flag from that observation
  is carried into production without the fresh readback.

### 12.2 Fork-only reward and sweep design

- [ ] Record the live three-field rewards auto-stake tuple and prepare—but do
  not initiate or execute—the proposed Alpha action that preserves the first
  two fields exactly and sets only `stabPoolRipePerDollarClaimed` to 0.
- [ ] If the exact O-5 terminal three-field tuple differs in any field from the
  reward-zero sweep tuple, prepare and fork-qualify a separate exact-terminal-
  tuple action early enough to mature before closeout. Record `N/A` only when
  all three terminal fields already equal the sweep tuple; a zero terminal
  rate does not by itself make restoration unnecessary.
- [ ] Compute the governance seed from the bound basket and exact share/NAV
  math.
- [ ] Include an approved execution buffer without turning it into an
  unbounded treasury position.
- [ ] Confirm the active claim list fits the legacy batch ceiling or define
  multiple batches.
- [ ] Ensure every claim batch contains at least one positively valued pair.
- [ ] Define an unwind path if the sweep cannot complete.
- [ ] Identify any pair that cannot be claimed under current configuration and
  complete Decision O-10 before proceeding.
- [ ] Fork-qualify the selected closure route supported by this runbook:
  temporary claim-flag enablement; temporary re-registration with an exact
  config plus claim and restoration; or the exact owner-approved raw-tail
  branch. Redemption or another mechanism is not selected here and requires a
  reviewed runbook amendment with its own operation family, funding/custody/
  return predicates, restoration, artifacts, and global stops before Gate 8A.
- [ ] A re-registration branch uses an owner-approved least-privilege config
  and binds the non-identical post-deregistration storage residue explicitly;
  no stale config, allocation, or route is silently accepted.
- [ ] If a raw residual exception is selected, prove its exact effect through
  every preceding withdrawal and the final governance migration; “small” or
  “dust” is not a proof.
- [ ] Perform no Base write in Sections 12.1–12.3.

### 12.3 Sweep-isolation and action-block qualification

Every action in this subsection is a Base-fork simulation/read unless Gate 8A
later authorizes the separate live action-start package.

The normal governance deposit and `claimManyFromStabilityPool` entry points
both require Teller to be unpaused. An ordinary deposit writes `lastTouch` when
the position owner is also the depositor; `depositFromTrusted` performs no
housekeeping. A same-user claim is a higher-risk action and, when last-touch
checking is enabled, cannot execute in the same action block as that ordinary
deposit. Therefore **do not** encode the proposed same-user seed and claim as
one same-block Safe MultiSend unless an exact fork proves a legitimate exempt
identity/path and the owner separately approves it.

- [ ] Record the exact seed depositor, position owner, claim user, caller,
  delegate, and recipient addresses.
- [ ] Read back `shouldCheckLastTouch`, the position owner's `lastTouch`, and
  whether the owner is legitimately exempt as an Underscore wallet/vault.
- [ ] Prove the selected seed path and claim path against the deployed Ledger,
  replacement Teller, and legacy Pool 1 on the exact Base fork.
- [ ] Prove the seed-to-claim action-block separation required by that path.
- [ ] On the exact fork, simulate initiating and maturing, for every approved
  seed asset, the temporary route `[6, 1]` and exact restoration route `[6]`;
  prove multiple pending actions for one asset execute safely in order.
- [ ] Prove every bridge preserves ID 6 as the zero-ID/default deposit route
  and changes no allocation, limit, minimum, or other deposit parameter.
- [ ] Prove one atomic bundle can execute every bridge-open action, seed every
  required Pool-1 cohort, and execute every restore-to-`[6]` action. Bind the
  exact assertion-capable execution primitive that decodes each Bravo return
  and turns `False` into an EVM revert; raw MultiSend is insufficient.
- [ ] On the fork, pause/disable AuctionHouse intake and every trusted
  Stability deposit producer while leaving Teller in the exact state required
  by the qualified seed/claim calls.
- [ ] Freeze relevant configuration and price-source changes.
- [ ] Document how permissionless Pool-1 claims/redemptions during any
  inter-block interval are detected and included in the final calculation.
- [ ] Define an abort/unwind path for a seed position if the sweep cannot close.

**BLOCKED — SP-SWEEP:** no production action-start payload may be authored
until `ART-SP-DESIGN-01` records a composed-fork proof of the temporary ID-1
support bridge set (or alternative ingress), exact seed/claim identities,
pause posture, action-block separation, entitlement calculation, complete
O-10 remediation/terminal-state lifecycle, typed-return design, atomic
restoration to `[6]`, and partial-sweep unwind. Teller cannot be paused during
these normal calls, and a same-user same-block seed-plus-claim bundle is
expected to fail the Ledger last-touch guard. Gate 8A closes the design and
owner-policy branch; the final live-bound `TX-ASSERT`, `ART-SP-01`, and
`ART-SP-TAIL-01` proofs close only at Gate 8B.

### GATE 8A — Stability action-staging authorization

- [ ] The fork-only design and every SP-SWEEP blocker above pass.
- [ ] O-5, O-9, and O-10 are closed with block/hash-bound evidence.
- [ ] `ART-SP-DESIGN-01` is complete, checksum-bound, independently
  reproduced, and enumerates every timelocked action to initiate plus every
  immediate write to execute later. Its assertion design and injected-failure
  tests pass; this preliminary proof does not substitute for Gate 8B's exact
  deployed-runtime, live-state, and final-payload `TX-ASSERT` closure.
- [ ] Independent review approves exact action-start calldata only; no sweep,
  claim, pause, or migration execution is authorized by this gate.
- [ ] Safe nonce/payload hash: ________________________________
- [ ] Owner authorization: ___________________________________
- [ ] Independent reviewer: __________________________________

### 12.4 Live governance-action staging

**Operation family:** `OP-SP-01`; one child ID per action initiation.

- [ ] Rebind Base block/hash, Safe nonce, live rate, asset configs, routes, and
  every relevant pending action immediately before staging.
- [ ] Initiate the approved reward-zero action.
- [ ] If required by O-5, initiate the separately identified exact-tuple
  restoration action; do not execute it during staging.
- [ ] Initiate every approved `[6, 1]` bridge action and matching `[6]`
  restoration action.
- [ ] For the selected O-10 branch, initiate every required timelocked Bravo
  registration/re-registration action and every matching Charlie
  deregistration or other timelocked terminal-state restoration action.
  Immediate Charlie claim-flag writes are listed in the execution manifest but
  are not initiated here and have no action ID.
- [ ] Record each action ID, start transaction/block/hash, confirmation block,
  expiry, decoded stored parameters, controlling board, and exact later child
  that will execute it. Prove paired O-10 actions can coexist and execute in
  the approved order.
- [ ] Execute none of these actions during staging.
- [ ] Monitor claim/user/configuration drift while actions mature; any
  non-reconcilable drift invalidates the execution package.

### 12.5 Final bind, fork, and execution authorization

- [ ] After all actions mature, bind a new finalized Base block/hash and rebuild
  the full holder/claim/price/share/entitlement census.
- [ ] Recompute the exact governance seed, buffer, claim arrays, batches, gas,
  freeze duration, and unwind from that pin.
- [ ] Fork-execute the exact action IDs and complete intended Safe transaction
  sequence, including reward zero, atomic bridge/seed/restore, later-block
  claim-tail enable/re-registration, claim, exact flag/config/registration
  restoration, exact closure, Teller pause, canary, batches, and closeout.
- [ ] `ART-SP-01` names the exact assertion-capable bridge/seed/restore
  and O-10 execution primitive, its deployed runtime and authority, every
  required return value/count, the unchanged reward tuple fields, and injected
  false/zero/short-return tests.
- [ ] `ART-SP-TAIL-01` records the exact raw-zero target and composed-fork
  proof or the complete owner-approved O-10 residual manifest and full
  migration/share-math proof; live closure is recorded only afterward in
  `ART-SP-CLOSURE-01`.
- [ ] Prove every staged action's remaining validity exceeds worst-case
  execution/reconciliation time plus incident margin.
- [ ] Independent decoder and reviewer approve the exact execution payloads,
  Safe nonces, action IDs, and calldata hashes.

### GATE 8B — Stability execution authorization

- [ ] Exact final bind and composed fork pass.
- [ ] Final `ART-SP-01` and `ART-SP-TAIL-01` are complete, checksum-bound, and
  independently reproduced; every matured action and immediate O-10 write is
  traceable to the Gate-8A design or to a newly reviewed superseding branch.
- [ ] The Phase-8 branch of `TX-ASSERT` is closed; every safety-dependent
  soft-return result, including immediate Charlie flag writes and O-10 board
  executions, becomes an EVM revert in the exact proposed bundle or ends in an
  explicitly qualified safe hold state that permits no subsequent child.
- [ ] Bind how every actual migration count is observed. If the selected Safe
  executor does not expose internal returndata, use the approved wrapper or
  reconstruct the count from qualified events and exact state deltas; do not
  label an ordinary Safe receipt as a decoded VaultMigrator return.
- [ ] Obtain separate execution authorization: __________________
- [ ] Independent reviewer: ____________________________________
- [ ] If any final bind, fork result, action ID, expiry, payload byte, Safe
  parameter, or approval differs, do not execute the reward-zero action or any
  later Phase-8 write.

### 12.6 Governance seed and claim sweep

**Operation families:** `OP-SP-02` through `OP-SP-04`.

- [ ] Execute the matured reward-zero action as its own child operation. If
  the selected executor exposes/asserts returndata, require decoded `True`;
  otherwise apply the Gate-8B safe-hold rule. In either branch, read back the
  full tuple: both auto-stake ratios exactly unchanged and
  `stabPoolRipePerDollarClaimed == 0` before the seed/sweep.
- [ ] In one atomic `OP-SP-03` child bundle using the exact `ART-SP-01`
  assertion-capable primitive, execute every matured seed-asset
  `vaultIds = [6, 1]` action, execute each qualified governance seed deposit,
  then execute every matured restoration to `[6]`.
- [ ] Require the exact typed success value from every bridge and restoration
  action. Prove the transaction reverted as a whole in every injected
  `False`, zero, expiry/self-cancel, allowance, deposit, and restoration
  failure; post-receipt route readback alone is not atomicity evidence.
- [ ] Read back every seed asset at exactly `[6]` immediately after the bundle.
- [ ] Record the seed transaction/action block and exact governance shares by
  stability-asset cohort.
- [ ] If required, wait until a later action block without reopening any
  trusted ingress. “Action block” here is the preserved deployed Ledger's Base
  `block.number` semantics, not elapsed wall time or a local transaction
  counter.
- [ ] Immediately before the claim, refresh claim balances, prices, total
  shares, Pool-1 NAV, governance shares, and governance entitlement.
- [ ] Confirm the approved seed/buffer still covers the entire refreshed
  valued basket.
- [ ] Immediately before **each** claim call, read the claim user's `lastTouch`
  from the preserved deployed Ledger and require it to differ from the current
  execution action block unless the exact fork proved a legitimate exemption.
- [ ] If the claim list requires multiple calls for the same user, execute each
  call in a separately qualified later action block, then refresh `lastTouch`,
  basket, prices, shares, NAV, and entitlement again. Do not place two
  same-user higher-risk claim calls in one block merely because both batches
  fit the Safe payload.
- [ ] Different claim users may share one block only when each user's own
  `lastTouch` preflight passes and the exact batch/fork proves independent
  entitlement and gas; the action-block rule is per user, not a global
  one-claim-per-block lock.
- [ ] For each selected O-10 remediation cohort, execute the exact qualified
  lifecycle under `OP-SP-04`: any matured registration action; any immediate
  Charlie claim-flag enablement; the claim batch; immediate restoration of the
  original flag; and any matured deregistration or other terminal-state
  restoration. Require the typed success value from every board/immediate
  write and the exact expected claim result. If the lifecycle cannot be made
  atomic, the composed fork must prove a bounded safe hold at every child
  boundary and no next child may begin until its readbacks pass.
- [ ] Execute the qualified claim batch or batches while Teller is unpaused;
  a row selected for the approved raw-tail branch is never silently omitted
  from the claim manifest.
- [ ] Ensure each batch contains at least one positively valued pair; the
  legacy batch function rejects an all-zero-value batch.
- [ ] Record every claimed token amount and destination.
- [ ] Record actual claim USD value and any reward output.
- [ ] Confirm no unexpected RIPE reward was auto-staked into RipeGov 2.
- [ ] Before economic-closure evaluation, read back every O-10 flag, asset
  config, registration index/count, ordered active list, route/allocation/
  limit field, and approved stale-storage footprint at its exact terminal
  value.
- [ ] The final successful claim/restoration child ends by pausing Teller when
  the exact authority/call composition is fork-qualified. Otherwise Teller is
  paused in the immediate next child under a bound maximum block gap, and any
  intervening claim/redeem/configuration drift invalidates the closure pin.
- [ ] If any material pair remains, complete the approved seed unwind/residual
  disposition and stop before user migration.

**Emergency rule:** if production state ever shows an approved seed asset at
`[6, 1]` outside the atomic seed transaction, pause Teller immediately, then
execute/rebuild the approved restoration to `[6]`. Emergency pause takes
priority over waiting for a governance restore.

### 12.7 Economic-claim closure and raw-tail disposition gate

- [ ] Teller is paused at the terminal claim receipt or immediate bounded next
  child, AuctionHouse and trusted producers remain blocked, and the closure
  block/hash is bound before reconciliation begins.
- [ ] Every economically claimable/redeemable row selected for the sweep is
  exactly zero after execution.
- [ ] Every nonzero raw `claimableBalances` row is either remediated to zero or
  appears exactly once in the approved `ART-SP-TAIL-01` exception manifest.
- [ ] For each claim asset, `totalClaimableBalances` equals zero or the exact
  sum of approved exception rows; no approximate aggregate passes.
- [ ] No unenumerated active or dormant claim entry remains. Stale iterable
  slots outside the active endpoint are distinguished from active rows.
- [ ] Every approved residual has the exact custody, NAV/share contribution,
  user-withdrawal effect, and terminal governance disposition proven on the
  exact deployed-legacy composed fork.
- [ ] Every bridged seed asset is restored exactly to `[6]`; explicit Pool-1
  deposits are closed again.
- [ ] Pool-1 stability-asset custody, claim-asset custody, remaining shares,
  and any approved raw tail reconcile under the exact legacy math.
- [ ] `ART-SP-CLOSURE-01` records the live terminal claim receipts, exact
  raw/economic closure, terminal MissionControl state, and custody/share
  reconciliation; an independent verifier reproduces it before user
  migration begins.

**STOP:** any nonzero row not in `ART-SP-TAIL-01`, any changed exception, or any
unproven NAV/share/withdrawal effect keeps the entitlement branch unresolved
and can make full-depletion migration fail. Do not hard-code a one-unit tail
from an earlier block.

### 12.8 Complete migration freeze

**Operation family:** `OP-SP-05`.

- [ ] Prove Teller has remained paused since the §12.7 closure pin.
- [ ] Keep AuctionHouse/liquidation intake paused or disabled.
- [ ] Keep every trusted Stability deposit producer paused or disabled.
- [ ] Freeze all Pool-1 claims and redemptions through Teller pause.
- [ ] Keep relevant configuration and price-source changes frozen.
- [ ] Keep Ledger and CreditEngine in the state required by the generic
  VaultMigrator route.
- [ ] Keep Lootbox, price sources, and required housekeeping dependencies
  callable.
- [ ] Keep both Pool 1 and Pool 6 unpaused as required by the generic
  VaultMigrator endpoint checks.
- [ ] Wait for the qualified later action-block boundary.
- [ ] Re-run the holder/claim census and prove it is unchanged.
- [ ] Preflight every batch user's `lastTouch` against the execution action
  block.

### 12.9 User migration

- [ ] `ART-SP-CLOSURE-01` is complete and independently reproduced from the
  frozen terminal-claim state; no migration child starts before it passes.
- [ ] Unpause VaultMigrator for the controlled window.
- [ ] Confirm Teller remains paused.
- [ ] Confirm source and target classification both report Stability.
- [ ] Execute through the approved SwitchboardEcho route; do not call
  VaultMigrator directly from an EOA.
- [ ] Every generic batch contains 1–25 unique, nonzero user addresses. Bind a
  per-user source-position manifest that classifies every registered slot as
  positive-and-target-supported, empty/no-balance, or target-unsupported; no
  skip is inferred from a successful transaction.
- [ ] For the generic route, each child contains no more than 25 users and the
  preflight proves every included user has no more than 20 registered source
  asset slots; one over-capacity user pre-reverts the entire child.
- [ ] A user above 20 registered slots uses only the separately fork-qualified
  explicit-by-assets Echo/VaultMigrator route with no more than 20 unique
  assets per child. Each child ends in higher-risk housekeeping for that user,
  so same-user chunks use separately qualified later action blocks with a
  fresh `lastTouch` preflight; the final proof shows no supported economic
  asset was skipped. If that route cannot close the user, stop for a reviewed
  contract/policy change.
- [ ] Execute a canary user/batch first.
- [ ] Before every generic child, calculate the exact positive expected
  `numPositions` result from the approved manifest. If the Gate-8B executor
  exposes/asserts the returned `uint`, record it; otherwise reconstruct the
  actual count by the approved event/state method and do not claim a Safe
  receipt exposes internal returndata. Require that count, the migration
  events, and source/target deltas all to match. A zero or short positive
  result is semantic failure even if the EVM transaction succeeded; stop in
  the reconciled safe hold state and do not advance.
- [ ] For every explicit-by-assets child, require a nonzero user, 1–20 unique
  positive source assets, target support for each, and an actual count—observed
  by the Gate-8B-approved method—exactly equal to the asset-array length.
- [ ] Reconcile exact source debit and target credit.
- [ ] Reconcile shares, custody, Ledger participation, Lootbox state,
  `lastTouch`, debt health, and events.
- [ ] Execute only gas-qualified batches.
- [ ] Repeat the live holder census after every batch.
- [ ] Migrate the governance sweep/seed position last.
- [ ] If O-10 approved a residual, prove every preceding user migrated exactly
  as in the fork and that the final governance migration alone absorbs the
  exact approved rounding/tail effect; stop on any one-unit difference.
- [ ] Confirm Teller and VaultMigrator retain no residual tokens.
- [ ] Inject a reverting late failure and prove atomic rollback; separately
  inject/construct every possible semantic short-return case and prove it is
  detected before a later child, because a short successful return does not
  itself revert prior migrations.

### 12.10 Stability closeout

**Operation family:** `OP-SP-07`.

- [ ] Second independent census finds no unmigrated economic position.
- [ ] Pool 1 has no unresolved or unmanifested claim, reward, registration,
  Ledger, debt, or trusted-producer dependency.
- [ ] Remove Pool 1 from every remaining deposit/configuration path.
- [ ] Keep Pool 1 registered for residual cleanup until terminal proof permits
  retirement.
- [ ] Pause VaultMigrator.
- [ ] Execute the already-mature exact O-5 terminal-tuple action, or use the
  reviewed `N/A` branch only when the sweep tuple already equals that terminal
  tuple; require typed success where applicable and read back all three fields
  before reopen.
- [ ] Unpause Teller and approved producers only after all readbacks match.
- [ ] Unpause AuctionHouse last, then run the qualified liquidation/fallback
  smoke test.

### GATE 8 — Stability migration complete

- [ ] `ART-SP-CLOSURE-01` is complete, checksum-bound, and independently
  reproduced from the terminal claim/freeze block before the first migration
  child.
- [ ] Economic claim accounting is exactly closed; raw accounting is either
  exactly zero or equals only the exact owner-approved `ART-SP-TAIL-01`
  manifest.
- [ ] Every approved Pool-1 user position is migrated or has an explicit owner
  disposition.
- [ ] Every migration child returned exactly its manifest position count; no
  zero/duplicate user or target-unsupported positive position was silently
  accepted as migrated.
- [ ] Pool 6 aggregates and user positions reconcile.
- [ ] Pool 1 can no longer create a claim-reward deposit in RipeGov 2.
- [ ] The full Stability reward tuple equals the exact O-5 terminal policy.
- [ ] Gate evidence: __________________________________________
- [ ] Independent reviewer: __________________________________

---

## 13. Phase 9 — RipeGov 2 to 7 migration

**Environment / writes / authority:** Base mainnet migration and governance
writes; this phase requires a separate new Safe authorization after all Phase-9
blockers close.

This is a separate maintenance window. Exact deployed-legacy
source/fork fidelity is a release blocker; the reviewed tests explicitly defer
that proof to issue #150.

**BLOCKED — RG-PROCEDURE:** the current RH `VaultMigrator` migrates all
supported positions for each user in one call, while older Base decision and
handoff documents require one asset per call and non-overlapping RIPE and
RIPE-LP windows. Do not prepare calldata until Decision O-8 names the
controlling procedure, the conflicting documents are reconciled, and the exact
deployed legacy contract passes the composed Base-fork qualification.

### 13.1 Preconditions

- [ ] Stability migration Gate 8 is complete.
- [ ] Pool 1 can no longer auto-stake claim rewards into RipeGov 2.
- [ ] Bind current release/runtime hashes, addresses, finalized block/hash, and
  Safe payload.
- [ ] Rebuild the complete RipeGov-2 user and contributor census.
- [ ] Re-run the deployment-to-pin event census and enumerate every registered
  asset slot, including deprecated/zero-balance legacy LP entries.
- [ ] Prove exact per-asset raw-share/balance and point closure against RipeGov-2
  aggregate getters.
- [ ] Count registered asset slots, not merely users or positive balances.
- [ ] Prove every legacy user has no more than 20 registered source slots and
  every proposed batch has no more than 20 aggregate registered slots. The
  Base-immutable legacy entry point has no exposed explicit-by-assets fallback;
  any over-capacity user blocks payload authorship pending a reviewed contract
  change or exact owner-approved nonmigration disposition.
- [ ] For every positive source position, prove the asset is supported in
  target 7 or bind an explicit owner-approved residual/nonmigration
  disposition. The legacy entry point silently skips target-unsupported
  assets; transaction success is not proof of complete user migration.
- [ ] Record RIPE and RIPE/LP balances, shares, points, pending points, unlocks,
  last terms, registrations, and Ledger participation.
- [ ] Recalculate gas-qualified batches from actual registered slots.
- [ ] Confirm `badDebt == 0` and all health gates.
- [ ] Prove RipeGov 7 is virgin for every user/asset pair and aggregate.
- [ ] Prove no HR, bond, Lootbox, Teller, or other producer has touched 7.
- [ ] Before authoring or authorizing the first `OP-RG-01` child, complete and
  independently reproduce `ART-RG-CENSUS-01`, `ART-RG-PROCEDURE-01`, and
  `ART-RG-CLEANUP-01`. Refresh the census and batch manifests again from the
  final frozen state before `OP-RG-06`; the earlier artifact is not permission
  to reuse stale users, slots, balances, support flags, or counts.

### 13.2 Controlling procedure and exact legacy behavior qualification

- [ ] Record the exact `VaultMigrator` source/runtime selected for deployment.
- [ ] Confirm whether its legacy entry point migrates every supported
  registered position for a user or only one requested asset.
- [ ] Reconcile the generic RH production runbook with the Base decision plan
  and implementation handoff.
- [ ] Record the owner-approved controlling procedure and superseded document
  references: ________________________________________________
- [ ] If the serial one-asset policy is selected, stop until the required
  contract change receives source review, tests, size qualification, and an
  exact fork rehearsal; the reviewed RH implementation is not serial.

- [ ] Fork uses the exact deployed legacy RipeGov runtime/source behavior, not
  the new RH contract as a stand-in.
- [ ] Prove legacy `43,200 -> 43,199` makes `_areKeyTermsSame` false and the
  withdrawal touch stores `unlock = 0`.
- [ ] Prove the same decrease does not accidentally apply new-target semantics
  through a normal target touch.
- [ ] Prove original unlock and historical terms are imported intact.
- [ ] Prove a failed import rolls back the source withdrawal.
- [ ] Prove no target-side normal refresh occurs while temporary shared terms
  are active.

Evidence anchors:

- `91eda49:contracts/vaults/RipeGov.vy:735-771`
- `5c30234e:contracts/vaults/RipeGov.vy:1054-1068`
- `5c30234e:docs/chains/rh/vault-migration/production-runbook.md:145-171`
- `5c30234e:tests/vaults/test_vault_migrator_legacy.py:12-16,96-101`

### 13.3 Governance-action staging before the freeze

**Operation family:** `OP-RG-01`; action initiations, bridge executions, and
their maturity evidence receive separate child/artifact IDs.

- [ ] Obtain separate authorization for the exact action-start and bridge
  children only after the three prerequisite design artifacts
  (`ART-RG-CENSUS-01`, `ART-RG-PROCEDURE-01`, and `ART-RG-CLEANUP-01`) and O-8
  are closed; this authorization does not cover the Gate-9A freeze/pointer
  initiation, pointer execution, or migration batches.
- [ ] Read and record the production action timelocks for Bravo, Charlie, and
  the board that controls RipeGov asset terms.
- [ ] Snapshot the complete RIPE and RIPE/LP deposit configuration: ordered
  `vaultIds`, staker/voter allocations, per-user/global limits, and minimum
  balance.
- [ ] While `coreRipeGovVaultId == 2`, RipeGov 7 is paused, and RIPE/LP default
  deposits still resolve to the first route entry, initiate and mature the
  approved Bravo bridge actions for RIPE `[2, 7]` and RIPE/LP `[2, 7]`.
- [ ] Prove each bridge and final-route action changes only `vaultIds` and
  preserves every snapshotted non-route field exactly.
- [ ] Execute both bridge actions before Charlie initiation and read back the
  exact ordered arrays plus every preserved non-route field.
- [ ] Prove RipeGov 7 remained untouched because it was paused and ID 2
  remained the first/default route.
- [ ] From each exact pre-window RIPE and RIPE/LP tuple, initiate two distinct
  Alpha actions: the approved temporary wind-down tuple and the exact-original
  restoration tuple. Record all four action IDs, decoded stored tuples,
  initiation/confirmation blocks, expiries, and execution-time revalidation;
  prove both actions per asset can coexist and are unambiguously ordered.
- [ ] Execute none of the temporary or restoration term actions during
  staging. The temporary pair belongs only to `OP-RG-05B` after pointer/freeze
  gates; the exact-original pair belongs only to `OP-RG-07` after migration.
- [ ] Prove the restoration actions' remaining validity covers the entire
  measured pointer, final-route maturity, migration, reconciliation, cleanup,
  and incident budget. If not, replace and mature the package before the
  freeze begins.
- [ ] Calculate the full freeze duration through core-pointer confirmation,
  migration batches, exact term restoration, and final `[7]` route
  confirmation.
- [ ] Obtain explicit approval for that measured freeze duration.

**STOP:** Charlie cannot validate ID 7 until MissionControl reports RIPE
support in ID 7, and Bravo cannot validate a final `[7]` staker route while
core is still ID 2. The `[2, 7]` bridge must therefore be live before Charlie
starts; the final `[7]` action can only be initiated after core becomes 7.

### GATE 9A — RipeGov freeze and pointer-initiation authorization

- [ ] Gate 8 is complete; O-8, `RG-PROCEDURE`, and `RG-CLEANUP` are closed;
  `ART-RG-CENSUS-01`, `ART-RG-PROCEDURE-01`, and `ART-RG-CLEANUP-01` are
  checksum-bound and independently reproduced.
- [ ] Every `OP-RG-01` bridge and staged term/restoration action matches its
  approved tuple, ID, maturity, and expiry; no unrelated pending action can
  execute or mature during the window.
- [ ] From a fresh finalized block/hash, bind the release/runtimes, complete
  pre-freeze census, routes, terms, pause/producer posture, Safe nonce, and the
  exact calldata and payload hashes for `OP-RG-02` and `OP-RG-03` only.
- [ ] Bind the expected next Charlie action ID and prove on the exact composed
  fork that `RG7-UNPAUSE-A` starts and ends with ID 7 paused, emits/stores the
  expected pointer action, and leaves target 7 pristine. The live emitted ID
  must equal the expectation or Gate 9A is invalidated.
- [ ] `ART-RG-EXEC-01` records the injected-failure/containment proof and the
  exact maximum time from freeze start through pointer initiation. It does not
  authorize pointer execution, temporary-term execution, migration, cleanup,
  restoration, final routes, or reopen.
- [ ] Exact Gate-9A Safe nonce/payload hashes: __________________
- [ ] Owner authorization: _____________________________________
- [ ] Independent reviewer: ____________________________________

If any Gate-9A state, payload byte, expected action ID, or approval changes,
do not start the freeze. Rebind, re-fork, and obtain a new authorization.

### 13.4 Complete RipeGov freeze

**Operation family:** `OP-RG-02`.

- [ ] Execute only the exact Gate-9A-authorized freeze children; a generic
  “Phase 9 approved” statement is not authority for these writes.
- [ ] Pause Teller.
- [ ] Disable HR contributor deposits/transfers that can mutate positions.
- [ ] Disable BondRoom deposits/auto-stake.
- [ ] Block Lootbox claim/auto-stake producer entrypoints without pausing the
  point-accounting and cleanup functions required by migration.
- [ ] Block CreditEngine/CreditRedeem borrow, redeem, and trusted-deposit
  producer entrypoints without pausing CreditEngine housekeeping.
- [ ] Disable Deleverage/AuctionHouse governance paths capable of withdrawing
  from the legacy vault.
- [ ] Freeze relevant configuration changes except the exact approved bridge/
  final-route, pointer, temporary-term, and exact-original restoration actions
  bound to this window.
- [ ] Wait for the required later action block.
- [ ] Re-read the complete census and prove it is unchanged.

### 13.5 Route and pointer rotation

`RG7-UNPAUSE-A` and `RG7-UNPAUSE-B` are the only intentional pre-migration
windows in which RipeGov 7 is unpaused. `depositFromTrusted` does not check
Teller's pause state, so Teller pause would not protect an accidentally
non-atomic or stranded-unpaused state. A correctly formed Safe MultiSend has no
inter-transaction gap, and the reviewed unpause/Charlie/re-pause sequence has
no untrusted callback through which another transaction can interleave. The
complete producer freeze in §13.4 nevertheless remains a hard precondition: it
keeps source state deterministic through the pointer delay and protects the
window if atomicity, ordering, or the expected start/end pause state differs.
Any such difference or unexpected target-7 state is an immediate stop and
fresh census.

- [ ] Read back temporary RIPE deposit support exactly `[2, 7]`.
- [ ] Read back temporary RIPE/LP deposit support exactly `[2, 7]`.
- [ ] Prove RipeGov 7 remains virgin after the route write.
- [ ] In atomic bundle `RG7-UNPAUSE-A` (`OP-RG-03`), unpause RipeGov 7, initiate
  `coreRipeGovVaultId: 2 -> 7`, and re-pause RipeGov 7; record the action ID
  and confirmation block.
- [ ] Prove `RG7-UNPAUSE-A` starts and ends with 7 paused and re-read every
  target-7 aggregate immediately after the receipt.
- [ ] Keep RipeGov 7 paused and every alternate producer frozen throughout
  Charlie's action timelock.
- [ ] Keep VaultMigrator paused throughout pointer validation.

### GATE 9B — RipeGov pointer and migration execution authorization

- [ ] Wait until the Charlie pointer action is mature, then bind a new
  finalized Base block/hash and its exact action ID, stored tuple, initiation/
  confirmation/expiry blocks, and remaining incident headroom.
- [ ] Refresh the complete frozen RipeGov-2/7 census and batch manifests from
  that block. Rebind every registered slot, target-support result, expected
  migrated-position count, route, term, pause, producer, Ledger, reward, debt,
  and custody value; do not reuse the Gate-9A census.
- [ ] Re-read the staged temporary/restoration term actions and prove their
  exact IDs, tuples, ordering, maturity, expiry, and validity through the
  measured migration/cleanup/reopen budget.
- [ ] From this exact frozen state, composed-fork execute `OP-RG-04` through
  `OP-RG-09`, including the later action-block boundary, canary, measured
  batches, term restoration, final-route actions, cleanup, reconciliation,
  failure injection, and safe hold/recovery branches.
- [ ] `ART-RG-EXEC-02` binds the Safe nonce sequence and exact payload hashes
  for every presently knowable child. A later action-ID-dependent child is not
  authorized until its actual ID/maturity/expiry and exact calldata/hash are
  rebound in a dated child packet, independently reviewed, and separately
  signed; the enclosing Gate 9B approval is not blanket calldata authority.
- [ ] Close the Phase-9 branch of `TX-ASSERT` per safety-dependent call. For
  each Charlie/Alpha/Bravo `bool` and SwitchboardEcho/VaultMigrator `uint`
  result, select either an assertion-capable executor that decodes the return
  and reverts on the wrong value, or an isolated safe-hold child after which no
  dependent operation may start until exact events/getters/deltas reconcile.
- [ ] Bind how the actual migrated-position count is observed. Prefer a wrapper
  that consumes and asserts the returned `uint`; otherwise reconstruct it from
  the qualified migration events and exact source/target deltas while holding
  safely before the next child. If the Safe/executor does not expose internal
  returndata, do not label a receipt or RPC decode as the raw return value.
- [ ] Prove every `RG7-UNPAUSE-*` bundle performs its mandatory re-pause even
  on a soft failure and that no failed/short result can advance the operation.
- [ ] Exact Gate-9B and immediate `OP-RG-04` nonce/payload hashes: __________
- [ ] Owner execution authorization: ___________________________
- [ ] Independent reviewer: ____________________________________

Any drift in frozen state, action ID/timing, batch manifest, payload byte,
nonce, fork result, or approval invalidates the affected child. Keep the
protocol in the reconciled freeze/paused posture, rebuild, and reauthorize.

- [ ] Immediately before confirmation, prove RipeGov 7 is still pristine and
  re-read the complete freeze posture.
- [ ] After Gate 9B, use atomic bundle `RG7-UNPAUSE-B` (`OP-RG-04`) to unpause
  RipeGov 7, execute the Charlie pointer action, and re-pause RipeGov 7.
- [ ] If the selected executor asserts returndata, require Charlie's decoded
  execution return to be `True`. Otherwise do not claim the Safe receipt
  exposes that internal return: require the pointer event/getter readback and
  the Gate-9B safe-hold rule. On `False` or any semantic mismatch, the mandatory
  re-pause must still execute and no next operation begins until a new action
  is qualified and separately authorized.
- [ ] Prove `RG7-UNPAUSE-B` starts and ends with 7 paused and re-read every
  target-7 aggregate immediately after the receipt.
- [ ] Read back `isRipeGovVaultId(2) == True`.
- [ ] Read back `isRipeGovVaultId(7) == True`.
- [ ] Read back that RipeGov 7 is paused for legacy import.
- [ ] Keep legacy source RipeGov 2 unpaused.
- [ ] Keep Teller paused.
- [ ] Under `OP-RG-05A`, only after the successful pointer-to-7 readback,
  initiate the final Bravo RIPE `[7]` and RIPE/LP `[7]` route actions; record
  their maturity and expiry. Maturity is `MON/ART` evidence, not part of the
  state-changing child.
- [ ] Keep Teller and every normal producer frozen until those final route
  actions mature, execute, and read back, unless a different composed-fork-
  qualified bridge is separately approved.

### 13.6 Temporary legacy wind-down terms

- [ ] Keep every temporary-term execution pending while the pointer is 2 and
  while the §13.4 freeze is incomplete. Alpha stores the proposed terms and
  does not revalidate the core RipeGov ID at execution; an early execution can
  affect legacy users.
- [ ] Wait until both final `[7]` route actions are mature, then re-prove the
  complete freeze, `coreRipeGovVaultId == 7`, ID 7 paused/pristine, and source
  ID 2 unpaused.
- [ ] Record exact pre-window RIPE RipeGov configuration.
- [ ] Record exact pre-window RIPE/LP RipeGov configuration.
- [ ] Census proves 43,199 is below every migrating position's stored
  historical minimum.
- [ ] Under `OP-RG-05B` and the current all-assets-per-user procedure, execute
  the mature Alpha actions that apply
  `minLockDuration: 43,200 -> 43,199` to both approved assets together.
- [ ] Under a selected serial procedure, use only its newly reviewed,
  non-overlapping asset sequence; do not mix the two models.
- [ ] Keep asset weight, freeze flag, max duration, max boost, `canExit`, and
  `exitFee` unchanged.
- [ ] Wait for the required action-block boundary.
- [ ] Prove no normal target-side function can refresh imported data under the
  temporary terms.
- [ ] Preflight every batch user's `lastTouch` against the execution action
  block.

`exitFee: 8000 -> 8001` also makes the deployed legacy classifier treat the
terms as changed and can trigger the legacy courtesy unlock, but it worsens a
fee-bearing field and can affect a stray exit/touch. The selected
`minLockDuration: 43,200 -> 43,199` is a one-block, user-favorable reduction
that avoids changing exit economics. It is still a live policy change, not an
“economically neutral” no-op: do not substitute either mechanism or weaken the
complete freeze without reopening owner approval and exact-legacy fork proof.

### 13.7 Migration execution

**Operation family:** `OP-RG-06`; one child for the canary and one zero-padded
child per measured batch.

- [ ] Bind the matured term-restoration and final `[7]` route action IDs.
- [ ] Prove their remaining validity exceeds the measured worst-case canary,
  all batches, per-batch reconciliation, cleanup, closeout, and incident margin.
- [ ] If expiry headroom is insufficient, stop before the first migration batch
  and replace/re-mature the action package.
- [ ] Unpause VaultMigrator immediately before the canary, not while governance
  actions are merely maturing.
- [ ] Confirm the exact Base legacy pause matrix immediately before the
  canary: Teller paused; VaultMigrator unpaused; source ID 2 unpaused; target
  ID 7 paused; Ledger, CreditEngine, Lootbox, pricing, and housekeeping
  dependencies callable; all trusted producers frozen.
- [ ] Execute a canary batch through the approved SwitchboardEcho legacy route.
- [ ] Do not call VaultMigrator directly from an EOA.
- [ ] Reconcile exact source debit and target receipt for each asset.
- [ ] Reconcile original unlock, historical terms, points, pending points,
  shares, and balances.
- [ ] Reconcile source and target Lootbox state.
- [ ] Preserve source Ledger participation until every source asset, reward,
  and registration is settled.
- [ ] Reconcile contributor/HR positions and any required historical-vault
  mappings.
- [ ] Reconcile debt health and `lastTouch`.
- [ ] Deduplicate users and enforce both ceilings: no more than 25 user entries
  and no more than 20 aggregate registered asset slots per legacy batch.
- [ ] Every batch has 1–25 unique, nonzero users and a checksum-bound manifest
  of every registered slot, target-support result, expected migrated position,
  and approved skip/disposition.
- [ ] Require the actual migrated-position count to equal the exact positive
  manifest count and match the position events and source/target deltas. When
  the Gate-9B executor exposes/asserts the returned `uint`, record that value;
  otherwise reconstruct the count by the approved event/state method and do
  not claim a Safe receipt contains internal returndata. A zero or short
  positive result is semantic failure even if the transaction succeeds; stop
  before a later batch and reconcile every included user.
- [ ] Execute only measured batches; either ABI ceiling is an upper bound, not
  the production batch size.
- [ ] Re-census after every batch.
- [ ] Prove every late failure is atomic and retry from reconciled chain state.

### 13.8 Restore terms and final routes

**Operation family:** `OP-RG-07`.

- [ ] Execute the exact pre-staged RIPE restoration action; when the Gate-9B
  executor exposes/asserts returndata, require decoded `True`, otherwise apply
  the safe-hold rule. Require the expected event and exact getter readback.
- [ ] Execute the exact pre-staged RIPE/LP restoration action under the same
  decoded-`True` or safe-hold rule, with its expected event/readback.
- [ ] Independently read back every restored field.
- [ ] After migration reconciliation and term restoration, execute the matured
  RIPE `[7]` route action.
- [ ] Execute the matured RIPE/LP `[7]` route action.
- [ ] Read back both final ordered route arrays and every staker/voter
  allocation, limit, and minimum-balance field exactly.
- [ ] Keep ID 2 historically classified as RipeGov.
- [ ] Pause VaultMigrator.

### 13.9 Source reward, registration, and Ledger cleanup

**Operation family:** `OP-RG-08`.

**BLOCKED — RG-CLEANUP:** the selected release must expose and fork-qualify an
administrator-controlled cleanup route that preserves every source reward and
uses Lootbox's deployed-Ledger authority. The planning candidate's ordinary
broad claim/cleanup path is not accepted automatically: it must prove no-stake
delivery despite user auto-stake configuration, complete enumeration, bounded
gas, and fail-closed cleanup, or the release needs a reviewed narrow route.

- [ ] Enumerate every source asset registration for every migrated user,
  including zero-balance and deprecated legacy LP slots.
- [ ] Checkpoint/reconcile each source asset's post-migration deposit points and
  reward entitlement.
- [ ] Administrator-settle each source reward directly to its user with no
  staking; prove no user auto-stake ratio can redirect any portion to ID 7.
- [ ] Require no user transaction and forfeit no entitlement.
- [ ] Only after an asset balance and reward entitlement are both exactly zero,
  have Lootbox call the source vault's deregistration path for that asset.
- [ ] Fail closed on a cleanup cap, unclassified entry, positive balance,
  nonzero points, unavailable reward, or incomplete enumeration.
- [ ] Only after every source asset, reward, and cleanup-relevant registration
  is gone, have Lootbox call deployed `Ledger.removeVaultFromUser` for ID 2.
- [ ] Do not call a nonexistent/direct migration-only Ledger remover.
- [ ] Execute a cleanup canary and gas-qualified batches, reconciling reward
  delivery, points, registrations, `numUserAssets`, and Ledger participation
  after every batch.
- [ ] Run an independent second source census and prove exact closure.

### 13.10 Reopen

- [ ] Exact pre-window terms are restored and final `[7]` routes match the
  approved terminal manifest.
- [ ] Source cleanup Gate is complete or every retained residual has an
  explicit owner-approved non-retirement disposition.
- [ ] Unpause RipeGov 7.
- [ ] Unpause Teller and approved producers.
- [ ] Verify HR, bonds, and Lootbox auto-stake now resolve to 7.
- [ ] Keep any required legacy ID-2 residual cleanup path available until its
  terminal census.

### GATE 9 — RipeGov migration complete

- [ ] Every approved user and contributor is migrated or has an explicit owner
  disposition.
- [ ] Every legacy batch returned exactly its manifest position count; no
  over-capacity user or target-unsupported positive position was silently
  treated as migrated.
- [ ] RipeGov-7 balances, shares, points, locks, terms, registrations, and
  Ledger state reconcile.
- [ ] Temporary terms are exactly restored.
- [ ] No new-deposit route points to 2.
- [ ] RipeGov 2 has no unresolved reward, registration, Ledger, HR, debt, or
  trusted-producer dependency required for retirement.
- [ ] Gate evidence: __________________________________________
- [ ] Independent reviewer: __________________________________

---

## 14. Phase 10 — Final closeout

**Environment / writes / authority:** Base mainnet reconciliation is read-only;
any cleanup, pause, registry, or UI retirement write requires its separately
approved action/payload.

**Evidence artifact:** `ART-CLOSEOUT-01`; it records reconciliation and does
not authorize any cleanup write.

- [ ] Run a second independent terminal census for Pools 1 and 2.
- [ ] Confirm Ledger remains the exact original deployed contract and address.
- [ ] Confirm every active department, VaultBook entry, and Switchboard child
  matches the approved final manifest.
- [ ] Confirm normal governance and action timelocks are finalized.
- [ ] Confirm VaultMigrator is paused.
- [ ] Confirm old vaults remain registered until all residual cleanup and user
  support obligations are complete.
- [ ] Remove legacy UI paths only after terminal on-chain proof.
- [ ] Reconcile all Safe transactions, native pending-operation keys, events,
  balances, shares, points, debt, and residual token custody.
- [ ] Archive the exact release, build evidence, manifests, fork evidence,
  payloads, signatures, receipts, and readbacks.
- [ ] Record every accepted residual risk and policy exception.
- [ ] Keep Reserve/vesting deployment as a separate authorized program using
  the reserved RipeHQ IDs.

### GATE 10 — Final closeout

- [ ] Independent terminal censuses and final manifest reconciliation pass.
- [ ] Every retained legacy registration/residual has a named owner and
  continuing support policy.
- [ ] Evidence archive is complete and checksum-bound.
- [ ] No closeout write is inferred from this gate's signature.
- [ ] Gate evidence: __________________________________________
- [ ] Independent reviewer: __________________________________

### Final status record

| Gate | Status | Evidence | Owner | Independent reviewer |
| --- | --- | --- | --- | --- |
| O — Decision register |  |  |  |  |
| 0 — Bound inputs |  |  |  |  |
| 1 — Defaults qualification |  |  |  |  |
| 2 — Inert candidate qualification |  |  |  |  |
| 3 — Off-chain readiness |  |  |  |  |
| 4 — Fork-qualified cutover |  |  |  |  |
| 5 — Mature actions |  |  |  |  |
| 6 — RH core live |  |  |  |  |
| 7 — Transitional operation controlled |  |  |  |  |
| 8A — Stability action staging |  |  |  |  |
| 8B — Stability execution |  |  |  |  |
| 8 — Stability migration complete |  |  |  |  |
| 9A — RipeGov freeze/pointer initiation |  |  |  |  |
| 9B — RipeGov pointer/migration execution |  |  |  |  |
| 9 — RipeGov migration complete |  |  |  |  |
| 10 — Final closeout |  |  |  |  |

---

## 15. Global stop conditions

Stop and obtain a newly approved disposition if any of the following occurs:

- Intended release commit/tree or a production source blob changes.
- Deployed runtime, constructor immutable, compiler, or artifact hash does
  not match the approved manifest.
- Ledger address or semantics differ from the bound original.
- RipeHQ or VaultBook ID topology differs from the approved sequence.
- Any live VaultBook ID 1–5 version is not exactly 1 at the clone pin.
- A sequentially assigned candidate VaultBook or Switchboard child receives an
  unexpected ID, typed return, event, counter, or address binding.
- VaultMigrator is not registered at exactly RipeHQ ID 25.
- Any unrelated pending RipeHQ append—mature or immature—lacks a completed,
  separately approved terminal disposition while IDs 25–27 are reserved.
- A `PRESERVE` or `NO CORE WRITE` row in `ART-CORE-05` is changed by the core
  program, or a `REPLACE`/`APPEND` row is omitted or substituted.
- The dedicated transition Defaults does not bind the exact RH Contributor
  blueprint and allowlisted live overlay, a preserved Contributor instance is
  incompatible with replacement HR, or new-clone qualification fails.
- The complete ever-touched MissionControl asset census is absent, an inactive
  non-default mapping/stale array slot lacks a prove-none or explicit terminal
  disposition, or Defaults would activate a row that is inactive live.
- Alpha's Pyth/Curve child binding differs from the freshly authenticated
  preserved PriceDesk topology, including Pyth ID 0 or a non-Pyth live child.
- O-11 is unresolved, the selected Booster pointer/state differs, or the
  preserved-source semantic exception lacks explicit owner acceptance.
- Candidate AuctionHouse or RipeGov 7 is not proven paused before the RipeHQ
  ID-6 Switchboard authority handoff, or either pause state drifts across it.
- HQ5 MissionControl and HQ6 Switchboard are not confirmed in the selected
  assertion-capable atomic 5→6 order, or any replacement candidate becomes
  active before its exact candidate-side producer controls are proven.
- A candidate registry or post-setup action timelock remains zero after its
  required finalization point, or differs from the approved production value.
- A pending action created under a zero setup delay survives finalization or
  reopen, or a production-surviving action's confirmation/expiry does not
  reflect the finalized production delay.
- Any unapproved legacy or candidate action remains executable or capable of
  maturing after reopen. “Abandoned” is accepted only for an already-expired
  or permanently non-executable action whose exact target is fork-proven
  harmless; preserved RipeHQ authority over an old board is not harmlessness.
- An unapproved temporary local governor or pending governance change remains
  before candidate activation/reopen.
- Pool 1 appears in any RH AuctionHouse Stability route.
- Pool 6 route, pointer, classification, or asset support is incomplete.
- Any `specialStabPoolId` points to 1.
- Auction fallback is not proven for a live swap-enabled asset.
- An expected burn, Endaoment-transfer, or auction path is unhandled.
- User configuration/delegation replay is incomplete.
- Frontend/indexer/keeper explicit legacy-ID support is not live.
- A required trusted producer remains able to mutate the source during a
  freeze.
- Pool 7 is not pristine before RipeGov migration.
- `OP-RG-02` or `OP-RG-03` starts without Gate 9A, or `OP-RG-04` or any
  later RipeGov execution child starts without Gate 9B and its separately
  authorized exact dated child payload.
- The Phase-9 `TX-ASSERT` branch is open, the actual migrated-position count
  has no qualified observation method, or a Safe receipt is mislabeled as
  exposing internal returndata that the selected executor does not surface.
- The Stability sweep identity, action-block spacing, Teller posture, or
  unwind has not passed the exact composed fork.
- The live-bound temporary Pool-1 seed bridge set differs from Decision O-9,
  changes a non-route field, or is not restored to `[6]` atomically with the
  seed.
- The reward-zero action changes either pre-bound auto-stake ratio.
- The terminal restoration or retained-zero branch ends with any reward tuple
  field different from the exact Decision O-5 terminal policy.
- An O-10 temporary claim flag, asset configuration, active registration/list,
  route/allocation/limit, or approved stale-storage footprint does not end at
  its exact terminal manifest value.
- Stability economic claims are not closed, or raw claim accounting is neither
  zero nor exactly equal to the owner-approved, independently reproduced
  `ART-SP-TAIL-01` manifest before user migration.
- The controlling RipeGov all-assets-versus-serial procedure remains
  unresolved or contradicts the deployed migrator.
- A governance timelock makes the required freeze longer than the approved
  measured window.
- A bridge, restore, or final-route action lacks enough expiry headroom for
  worst-case execution, reconciliation, and incident margin.
- Temporary RipeGov terms are not exactly restored.
- `badDebt`, debt health, `lastTouch`, or pause state differs from the
  rehearsed migration gate.
- Ledger, required CreditEngine housekeeping, Lootbox point/cleanup,
  PriceDesk, or a required pricing source is paused or unavailable at a seed or
  migration canary.
- A canary or late-failure atomicity test fails.
- A Stability or RipeGov migration child contains a zero/duplicate user,
  silently skips an unapproved positive position, exceeds a bound slot cap, or
  returns a migrated-position count different from its exact manifest,
  including a short positive return.
- A safety-dependent call returns anything other than its exact typed success
  predicate/manifest—including `False`, zero, an unexpected assigned ID, an
  unexpected count or USD total, or a short-positive O-10 claim result—without
  reverting the containing atomic operation or ending in its explicitly
  qualified safe hold state.
- Safe calldata, nonce, guard, module, owner set, or threshold differs from
  the approved simulation.
- An unexplained balance, share, point, claim, event, registration, debt, or
  residual-token delta appears.
- An owner policy decision is missing, stale, or contradicted by live state.

---

## 16. Execution-record templates

### 16.1 Qualification-artifact register

Open-ended research, source review, census construction, and composed-fork
work must finish before a live freeze. Register the immutable result here; the
day-of packet verifies its checksum and continued applicability.

| Artifact ID | Required artifact | Required before | Source block/release | Checksum | Status | Independent verifier |
| --- | --- | --- | --- | --- | --- | --- |
| `ART-0A-01` | Live active/pending RipeHQ-ID-8 branch bind and cancellation/no-op decision | Any `OP-0A-02` payload |  |  |  |  |
| `ART-CORE-01` | Canonical post-Phase-0A state snapshot and disposition matrix | Gate 0 |  |  |  |  |
| `ART-CORE-02` | Exact-live snapshot, ever-touched/inactive MissionControl asset and stale-slot census, explicit reset/replay dispositions, dedicated transition Defaults, RH Contributor blueprint binding, and allowlisted diff | Gate 1 |  |  |  |  |
| `ART-CORE-03` | Client, keeper, indexer, and monitoring qualification | Gate 3 |  |  |  |  |
| `ART-CORE-04` | Freeze matrix plus exact composed core-fork report | Gate 4 |  |  |  |  |
| `ART-CORE-05` | Deployed-candidate addresses, runtimes, immutables, sequential registry results, pause states, and authorities | Gate 2 / input to Gate 4 |  |  |  |  |
| `ART-SP-DESIGN-01` | Pre-staging O-5/O-9/O-10 branch, action inventory, preliminary typed-return design, composed-fork proof, and unwind | Gate 8A |  |  |  |  |
| `ART-SP-01` | Fresh matured-action census plus reward tuple, bridge/seed/action-block, O-10 lifecycle, claim, restoration, migration-count, and unwind fork proof | Gate 8B |  |  |  |  |
| `ART-SP-TAIL-01` | Final pre-execution exact raw-zero target or owner-approved raw-tail manifest plus full legacy share/withdrawal/migration proof | Gate 8B / before `OP-SP-04` |  |  |  |  |
| `ART-SP-CLOSURE-01` | Live economic-claim closure, raw-zero/tail reconciliation, terminal MissionControl state, and custody/share proof | Produced after `OP-SP-04`; required before the first `OP-SP-06` migration child and Gate 8 |  |  |  |  |
| `ART-RG-CENSUS-01` | Fresh RipeGov user/slot census, per-asset target support, capacity blockers, dispositions, and exact batch return manifests | Before first `OP-RG-01` payload; refresh before `OP-RG-06` |  |  |  |  |
| `ART-RG-PROCEDURE-01` | Exact deployed-legacy migration, temporary/restoration-term action, return-count, and failure-boundary fork proof | Before first `OP-RG-01` payload |  |  |  |  |
| `ART-RG-CLEANUP-01` | Exact reward/registration/Ledger cleanup implementation and fork proof | Before first `OP-RG-01` payload |  |  |  |  |
| `ART-RG-EXEC-01` | Fresh pre-freeze state plus exact RipeGov freeze and pointer-initiation containment payloads/fork | Gate 9A / before `OP-RG-02` |  |  |  |  |
| `ART-RG-EXEC-02` | Mature Charlie action, final frozen census/batches, exact remaining payloads, Phase-9 `TX-ASSERT`, composed execution fork, and recovery proof | Gate 9B / before `OP-RG-04` |  |  |  |  |
| `ART-TRANSITION-01` | Signed recurring transitional-operation evidence | Gate 7 / each cadence |  |  |  |  |
| `ART-CLOSEOUT-01` | Independent terminal census and archive index | Gate 10 |  |  |  |  |

### 16.2 Run-specific command and readback catalog

Generate one catalog for each write window only after the final release,
canonical block, address/runtime manifest, ABI set, Safe nonce, and exact
payload are bound. Prefer checksum-bound scripts that emit typed JSON. Ad hoc
commands copied from review prose are not execution artifacts.

#### Window binding

| Field | Bound value |
| --- | --- |
| Run ID / window |  |
| Canonical runbook version and hash |  |
| Chain ID | `8453` |
| Finalized source block/hash |  |
| Release commit/tree |  |
| Address/runtime/immutable manifest hash |  |
| ABI/artifact manifest hash |  |
| RPC and toolchain versions |  |
| Governance Safe / nonce |  |
| Approved payload hash |  |
| Authorization record |  |
| Action expiries / minimum headroom |  |
| Operator / verifier / incident lead |  |

#### Operation and verification cards

| Stable child `OP-*` ID | Detailed section / entry gate | Prepared invocation artifact + checksum | Target address source | Independent decoded call-list checksum | Expected raw return + typed success predicate + events/readbacks | Maximum operation/reconciliation budget | Stop/recovery record |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |

| Evidence/readback ID | Bound query command or script + version/checksum | Block tag/finality | Expected named and typed result | Actual raw + decoded output hash | Result | Verifier |
| --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |

- [ ] Every invocation is generated from the bound ABI/address manifest; no
  freehand target, selector, argument, value, or address is permitted.
- [ ] An independent decoder reproduces target, value, operation type,
  selector, arguments, ordering, Safe nonce, calldata hash, and payload hash.
- [ ] Expected tuple values use named decoded fields and an explicit output
  signature, never a positional comment such as “field 9.”
- [ ] Every soft-return call records its expected raw return bytes and decoded
  success predicate. Low-level call success is never substituted for `True`,
  the expected assigned ID, or another contract-level result.
- [ ] Every `ART-*` dependency exists, matches its checksum, and remains
  applicable to the final live pre-state.
- [ ] A command/readback was dry-run against the exact composed fork before it
  appears in an authorized packet.
- [ ] No subsequent `OP-*` row begins before mandatory receipt, event, and
  getter verification completes.
- [ ] Any mismatch invokes the canonical stop condition; retry or recovery
  requires a new live reconciliation and, where state/payload changed, a newly
  reviewed artifact and authorization.

### 16.3 Governance/Safe action ledger

Complete one row per initiated, cancelled, confirmed, or directly executed
action. Keep decoded arguments and raw calldata as hashed dossier artifacts.

| Stable child `OP-*` ID / parent operation family | Target / selector / value / operation | Decoded arguments | Safe nonce + calldata/payload hash | Start tx + native key (`actionId`, registry ID, or `N/A`) + block/hash | Confirm block / expiry / cancel state | Confirm tx + events | Post-getter result | Operator / verifier / time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |  |

- [ ] Independent decoder reproduces every target, selector, argument, value,
  operation type, nonce, calldata hash, and payload hash.
- [ ] Fork record names snapshot block/hash, tool/version, output hash, gas,
  and expected negative controls.
- [ ] Runtime hash and immutable readbacks match; source/template hashes alone
  are not accepted as deployment identity.
- [ ] Before/after machine-readable snapshots have checksums.
- [ ] Shareable evidence contains no private key, signer secret, or sensitive
  RPC credential.

### 16.4 Migration batch reconciliation

| Window | Batch ID | Users / registered slots | Manifest expected positions | Pre-block/hash | Tx/hash | Gas | Raw/decoded actual return | Source delta | Target delta | Ledger/Lootbox/debt/lastTouch | Residual custody | Result / verifier |
| --- | --- | ---: | ---: | --- | --- | ---: | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |  |  |  |  |  |

- [ ] Batch manifest is deduplicated and checksum-bound before execution.
- [ ] A failed batch is treated as atomic only after receipt and getter
  verification; prior successful batches are not assumed reversible.
- [ ] A successful receipt with a return count different from the manifest is
  recorded as semantic failure/partial progress and blocks every later batch
  pending full live reconciliation and a newly reviewed disposition.
- [ ] Resume only from a new live census, never from the last local success
  record.

### 16.5 Abort and forward-recovery record

| Failure boundary | Confirmed on-chain state | Safe pause posture | Immediate permitted action | Delayed/governed recovery | New approval/evidence required | Incident owner |
| --- | --- | --- | --- | --- | --- | --- |
| Before first write |  |  | Abort window |  |  |  |
| Partial core registry confirmation |  | Teller/AuctionHouse/producers frozen | Hold | Approved forward-recovery only | Fresh census + fork + payload |  |
| Migration batch revert |  | Teller/producers remain frozen | Reconcile | Retry only from live state | Fresh batch manifest |  |
| Post-batch mismatch |  | Teller/producers remain frozen | Stop | Owner-approved disposition | Full independent reconciliation |  |

- [ ] Do not call a registry replacement rollbackable unless the reverse
  actions are already mature, authorized, and fork-proven.
- [ ] Emergency pause authority, callers, payloads, and incident channel are
  rehearsed before each window.

---

## 17. Reviewed source index

These anchors explain the architecture. They do not replace current deployed
runtime verification or a fresh release bind.

| Topic | Evidence anchor |
| --- | --- |
| RH AuctionHouse capability call and empty-pool behavior | `5c30234e:contracts/core/AuctionHouse.vy:58-62,560-565,625-667` |
| Legacy Pool-1 ABI lacks the RH capability selector | `91eda49:scripts/abis/StabilityPool.json:338,926-969,1242-1289` |
| Legacy RipeHQ address-registry initiation/confirmation timing | `91eda49:contracts/registries/modules/AddressRegistry.vy:156-198,239-285` and `91eda49:contracts/registries/RipeHq.vy:138-174` |
| Legacy RipeHQ pending address updates are registry-ID keyed and have no action ID | `91eda49:contracts/registries/modules/AddressRegistry.vy:20-24,110-113,239-299` and `91eda49:contracts/registries/RipeHq.vy:159-174` |
| Registry displayed-count versus next-index semantics | `91eda49:contracts/registries/modules/AddressRegistry.vy:108,136-139,181-187,567-577` |
| Sequential registry ID assignment occurs at append confirmation | `5c30234e:contracts/registries/modules/AddressRegistry.vy:175-198` and `5c30234e:migrations/robinhood-mainnet/0002_Switchboards.py:16-17,36-63` |
| Fresh registry appends always initialize version 1 | `5c30234e:contracts/registries/modules/AddressRegistry.vy:175-198` |
| Candidate pause caller must be an active Switchboard child, including VaultData-based RipeGov pause | `5c30234e:contracts/modules/DeptBasics.vy:63-68`, `5c30234e:contracts/modules/Addys.vy:190-194`, `5c30234e:contracts/vaults/RipeGov.vy:24-37`, `5c30234e:contracts/vaults/modules/VaultData.vy:274-279`, and `91eda49:contracts/config/SwitchboardCharlie.vy:490-496` |
| Candidate registry/action-timelock finalization and governance handoff pattern | `5c30234e:contracts/registries/VaultBook.vy:64-74`, `5c30234e:contracts/registries/Switchboard.vy:40-50`, `5c30234e:contracts/modules/TimeLock.vy:263-273`, `5c30234e:contracts/registries/modules/AddressRegistry.vy:441-452`, `5c30234e:contracts/core/HumanResources.vy:149`, and `5c30234e:migrations/robinhood-mainnet/0007_FinishSetup.py:7-49` |
| Action confirmation/expiry timing is fixed when initiated | `5c30234e:contracts/modules/TimeLock.vy:64-75,263-273` |
| Candidate departments can start unpaused and expose trusted producer paths after activation | `5c30234e:contracts/core/HumanResources.vy:141-149,493-504`, `5c30234e:contracts/core/BondRoom.vy:108-110`, `5c30234e:contracts/core/Lootbox.vy:203-211,1314-1318`, `5c30234e:contracts/core/CreditEngine.vy:194-197,1221-1227`, `5c30234e:contracts/core/CreditRedeem.vy:116-118,304-310`, `5c30234e:contracts/core/Deleverage.vy:242-254`, and `5c30234e:contracts/core/Teller.vy:266-277` |
| RH Contributor blueprint is selected through Defaults and replacement MC | `5c30234e:migrations/robinhood-mainnet/0000_TokensAndHq.py:82-95`, `5c30234e:contracts/config/DefaultsRobinhood.vy:44-77,221-234`, `5c30234e:contracts/data/MissionControl.vy:233-242`, and `5c30234e:contracts/core/HumanResources.vy:226-229` |
| Alpha Pyth child ID is immutable and zero disables Pyth governance; Base expects child 4 | `5c30234e:config/robinhood_launch.py:73-77`, `5c30234e:config/BluePrint.py:71-73`, and `5c30234e:contracts/config/SwitchboardAlpha.vy:420-441,916-925,1568-1570` |
| BondRoom booster pointer is mutable and RH Booster reset semantics differ from legacy | `5c30234e:contracts/core/BondRoom.vy:104-112,354-358`, `5c30234e:contracts/config/BondBooster.vy:119-128`, and `91eda49:contracts/config/BondBooster.vy:119-130` |
| Foxtrot exists but is not a core fixed child-ID namespace | `5c30234e:contracts/config/SwitchboardFoxtrot.vy`, `5c30234e:migrations/robinhood-mainnet/0002_Switchboards.py:16-17`, and `5c30234e:config/ripe-reserve-engine-activation.json:118-129` |
| New Stability capability view | `5c30234e:contracts/vaults/modules/StabVault.vy:1219-1243` |
| MC constructor loads every Defaults asset through active registration | `5c30234e:contracts/data/MissionControl.vy:221-265,306-329` |
| Asset deregistration does not erase the full config/storage footprint | `5c30234e:contracts/data/MissionControl.vy:306-357` |
| Preserved RipeHQ governance remains a governor of old boards, and a legacy Alpha action can target the current HQ-5 MC when its stored MC is zero | `91eda49:contracts/modules/LocalGov.vy:125-158` and `91eda49:contracts/config/SwitchboardAlpha.vy:1448-1473` |
| Checked-in live Defaults routes; not the transition artifact | `5c30234e:contracts/config/DefaultsBaseLive.vy:1031-1168,1276-1282` |
| Base live Defaults hardcodes the legacy Contributor while RH launch Defaults selects a blueprint | `5c30234e:contracts/config/DefaultsBaseLive.vy:46-81,219-229` and `5c30234e:contracts/config/DefaultsRobinhood.vy:44-77,221-234` |
| Zero-ID asset routing | `5c30234e:contracts/core/TellerUtils.vy:238-271` |
| Explicit deposits still require vault support | `5c30234e:contracts/core/TellerUtils.vy:103-130` and `5c30234e:contracts/core/Teller.vy:266-307` |
| Controlled VaultMigrator deposits bypass ordinary user deposit-count limits | `5c30234e:contracts/core/TellerUtils.vy:105-148` and `5c30234e:contracts/core/Teller.vy:504-509` |
| Explicit legacy claims/redemptions | `5c30234e:contracts/core/Teller.vy:693-724` |
| Legacy Pool-1 batch ceilings and replacement-Teller claim/redeem surfaces | `91eda49:contracts/vaults/modules/StabVault.vy:91-92,609-628,793-815` and `5c30234e:contracts/core/Teller.vy:220-221,691-724` |
| Legacy claim NAV, disabled-claim soft return, and raw/dormant dust behavior | `91eda49:contracts/vaults/modules/StabVault.vy:539-581,642-678,1058-1075` |
| Alpha priority validation | `5c30234e:contracts/config/SwitchboardAlpha.vy:1227-1284` |
| Bravo deposit-route write/validation | `5c30234e:contracts/config/SwitchboardBravo.vy:365-423,833-844` |
| Bravo auction-fallback invariant | `5c30234e:contracts/config/SwitchboardBravo.vy:465-479` |
| Board and legacy registry confirmations can soft-fail without reverting | `5c30234e:contracts/modules/TimeLock.vy:83-124`, `5c30234e:contracts/config/SwitchboardBravo.vy:807-815`, and `91eda49:contracts/registries/modules/AddressRegistry.vy:175-181,260-268` |
| Stability reward-zero action writes a three-field tuple | `5c30234e:contracts/config/SwitchboardAlpha.vy:1101-1176,1589-1596` |
| Stability claim-tail mutation control paths | `5c30234e:contracts/config/SwitchboardBravo.vy:239-337,807-831` and `5c30234e:contracts/config/SwitchboardCharlie.vy:1042-1060,1209-1217,1311-1351,1373-1376` |
| Charlie Stability pointer validation | `5c30234e:contracts/config/SwitchboardCharlie.vy:585-627` |
| Fresh Charlie starts with zero action delay | `5c30234e:contracts/config/SwitchboardCharlie.vy:458-466` |
| Charlie user-config/delegation actions | `5c30234e:contracts/config/SwitchboardCharlie.vy:1085-1130,1240-1253` |
| MC RipeGov pointer behavior | `5c30234e:contracts/data/MissionControl.vy:411-431` |
| Charlie RipeGov pointer validation | `5c30234e:contracts/config/SwitchboardCharlie.vy:539-578` |
| VaultMigrator hardcoded RipeHQ ID 25 | `5c30234e:contracts/modules/Addys.vy:64,487-499` and `5c30234e:contracts/config/SwitchboardEcho.vy:489-539` |
| SwitchboardEcho migration authority, ceilings, and uint return forwarding | `5c30234e:contracts/config/SwitchboardEcho.vy:483-487,562-609` |
| VaultMigrator Base legacy binding | `5c30234e:contracts/core/VaultMigrator.vy:129-138,354-372` |
| VaultMigrator pause, generic skip/return behavior, and batch constraints | `5c30234e:contracts/core/VaultMigrator.vy:123-203,206-265,312-457,593-623,629-652` |
| Teller seed/claim pause and deployed-Ledger last-touch behavior | `5c30234e:contracts/core/Teller.vy:240-277,341-343,691-704,1005-1024` and `91eda49:contracts/data/Ledger.vy:197-213` |
| RipeGov-7 trusted-deposit exposure while unpaused | `5c30234e:contracts/core/Teller.vy:266-277`, `5c30234e:contracts/vaults/RipeGov.vy:170-212`, and `5c30234e:contracts/config/SwitchboardCharlie.vy:539-578,1188-1197` |
| Legacy Pool-1 reward deposits hardcode RipeGov 2 | `91eda49:contracts/vaults/modules/StabVault.vy:95,735-757` |
| Lootbox ordinary reward/cleanup ordering | `5c30234e:contracts/core/Lootbox.vy:265-336,1326-1352` |
| Legacy RipeGov key-term classifier | `91eda49:contracts/vaults/RipeGov.vy:735-771` |
| New RH RipeGov courtesy predicate | `5c30234e:contracts/vaults/RipeGov.vy:1054-1068` |
| Alpha RipeGov-term actions store independent timelocked tuples | `5c30234e:contracts/config/SwitchboardAlpha.vy:1377-1423,1621-1627` |
| Base legacy pause matrix and wind-down | `5c30234e:docs/chains/rh/vault-migration/production-runbook.md:145-171` |
| Conflicting serial Base procedure | `5c30234e:docs/chains/base/ripe-gov-vault-migration/decision-plan.md:300-370,595` and `5c30234e:docs/chains/base/ripe-gov-vault-migration/implementation-handoff.md:165-166` |
| Base reward/registration/Ledger cleanup policy | `5c30234e:docs/chains/base/ripe-gov-vault-migration/decision-plan.md:198-244` and `5c30234e:docs/chains/base/ripe-gov-vault-migration/implementation-handoff.md:415-434` |
| Exact-legacy fork-fidelity caveat | `5c30234e:tests/vaults/test_vault_migrator_legacy.py:12-16,96-101` |

---

## 18. Readiness declaration

Complete this section only after all relevant gates are signed.

- [ ] Core deferred-cutover architecture approved.
- [ ] Engineering specification ready.
- [ ] Exact release frozen.
- [ ] Transition Defaults qualified.
- [ ] Off-chain clients ready.
- [ ] Core-cutover fork rehearsal passed.
- [ ] Core Safe payload independently reviewed.
- [ ] Core mainnet execution separately authorized.
- [ ] Stability migration fork rehearsal passed.
- [ ] Stability Safe payload independently reviewed.
- [ ] Stability mainnet execution separately authorized.
- [ ] Exact deployed-legacy RipeGov fork qualification passed.
- [ ] RipeGov Safe payload independently reviewed.
- [ ] RipeGov mainnet execution separately authorized.

**Current planning status:** the core deferred-cutover architecture is selected;
owner policies (including O-11), `TX-ASSERT`, `ART-CORE-05`, the
`MC-INACTIVE-STATE` census/dispositions, the Stability sweep/raw-tail
procedure, RipeGov procedure/cleanup, exact release, transition Defaults
implementation, composed fork evidence, RipeGov Gates 9A/9B artifacts, Safe
payloads, and mainnet authorization remain outstanding.
