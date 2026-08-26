# Base RH Deployment and Deferred-Migration Runbook

> **DRAFT — DO NOT EXECUTE**

**Goal:** deploy the RH-generation contracts on Base without replacing,
upgrading, redeploying, or semantically changing the deployed Ledger.

The work is deliberately split into three programs, each with one or more
separately authorized Base write windows:

1. RH core cutover.
2. Stability Pool 1 → 6 migration.
3. RipeGov 2 → 7 migration.

The core cutover does **not** require either user migration to happen
immediately. After the core cutover, Pool 6 handles new Stability activity,
Pool 1 remains available for qualified legacy exits and claims, RipeGov 2
remains active, and RipeGov 7 remains paused.

This concise runbook controls program order and gates. The
[technical appendix](./production-runbook-technical-appendix.md) controls
field-level acceptance criteria, evidence, operation cards, edge cases, and
execution records. **Both must pass.** A contradiction is a stop condition,
not permission to choose the easier rule.

This document authorizes no deployment, Safe transaction, registry change,
configuration write, pause, migration, cleanup, or other Base write. Every
write window requires its own exact payload review and owner authorization.

Historical anchors and reviewed source evidence remain in the appendix. They
are not a release lock: rebind the live RH release, deployed runtimes, and
finalized Base state before preparing any payload.

---

## 1. Plan at a glance

```text
Prepare
  → RH core cutover
  → monitored transition
  → Stability Pool 1 → 6 migration
  → RipeGov 2 → 7 migration
  → closeout

Reserve and vesting remain a separate Base program.
```

| Program | Result | Current status |
| --- | --- | --- |
| RH core cutover | RH departments live; Ledger unchanged; Pool 6 receives new Stability activity; RipeGov 2 remains core | Architecture selected; engineering and qualification incomplete |
| Stability migration | Legacy Pool-1 claims close and intended user positions move to Pool 6 | Separate later window; not payload-ready |
| RipeGov migration | Intended positions move from 2 to 7; exact terms restored; legacy rewards and registrations settle | Separate later window after Stability; not payload-ready |
| Reserve/vesting | Uses its separately qualified Base topology | Outside this runbook’s core window |

Legacy exit/claim/redeem availability remains subject to the live pause,
permission, delegation, debt-health, and asset-configuration checks. Removing
Pool 1 from normal deposit routes does not bypass those controls.

### Non-negotiable invariants

- Ledger is never replaced, upgraded, redeployed, migrated, or semantically
  modified.
- Pool 1 is never routed to RH AuctionHouse. It lacks the RH
  `canAcceptLiquidationAsset(...)` interface, so AuctionHouse’s typed call
  reverts rather than returning `False`.
- Pool 6 is the only normal post-cutover Stability deposit and liquidation
  destination.
- RipeGov 2 remains core until Stability migration is complete and the
  separately authorized RipeGov pointer window begins.
- RipeGov 7 remains paused and pristine until that window.
- Stability migration completes before RipeGov migration.
- Teller pause is never treated as a complete freeze.
- Planning balances, user counts, prices, delays, IDs, and batch sizes are
  always recomputed from a fresh finalized block.

---

## 2. Selected topology

### RipeHQ

The existing RipeHQ contract and governance Safe are preserved.

| HQ IDs | Components | Core posture |
| --- | --- | --- |
| 1–4 | GREEN, sGREEN, RIPE, Ledger | Preserve; Ledger at 4 is non-negotiable |
| 5 | MissionControl | Replace |
| 6 | Switchboard registry | Replace with a prepopulated Alpha–Echo registry |
| 7 | PriceDesk | Preserve exact live root and children |
| 8 | VaultBook | Replace with exact rows 1–5 plus new rows 6 and 7 |
| 9–22 | Protocol departments | Replace with the qualified RH generation |
| 23–24 | RIPE and GREEN CCIP pools | Preserve |
| 25 | VaultMigrator | Append; required exact ID |
| 26–27 | Reserve engine and vesting | No core write; separate Base program |

Any change to this preserve/replace/append posture is an architecture change
requiring a new snapshot, transition build, fork, and approval.

### VaultBook

The replacement VaultBook assigns IDs sequentially. There is no explicit-ID
append call.

| Vault ID | Required row |
| ---: | --- |
| 1 | Exact live legacy Stability Pool |
| 2 | Exact live legacy RipeGov |
| 3–5 | Exact live rows in their current order |
| 6 | New RH Stability Pool |
| 7 | New RH RipeGov |

Live rows 1–5 must each still be version 1 when cloned. If not, exact cloning
through fresh sequential appends is impossible and the architecture must be
replanned.

### Switchboards

The replacement Switchboard registry contains only:

| Child ID | Board |
| ---: | --- |
| 1 | Alpha |
| 2 | Bravo |
| 3 | Charlie |
| 4 | Delta |
| 5 | Echo |

Foxtrot is not a hardcoded child ID. A later append expected to receive 6 is a
separate Reserve-program decision and must be rebound to the then-live
topology.

### Preserved dependencies and explicit exceptions

- Deploy a new RH Contributor blueprint for future HR clones.
- Preserve all existing Contributor instances and prove they work with
  replacement HumanResources.
- Preserve the exact PriceDesk root and child order. Bind Alpha’s Pyth child
  from live Base state, currently expected as 4, and Curve consumers,
  currently expected as 2.
- Resolve O-11 before Gate 1. The recommended posture is to preserve the
  stateful legacy BondBooster and explicitly accept the RH-source semantic
  difference. Pointing replacement BondRoom at an empty new Booster is not
  acceptable.
- Preserve exact live TrainingWheels, Underscore, external pool, and oracle
  references unless a separately approved architecture row says otherwise.
- Give every allowance and every token/native balance held by a replaced
  department an exact disposition.

---

## 3. Universal safety model

These rules apply to every write window.

1. **Fresh binding.** Bind a finalized Base block/hash, final release/tree,
   compiler, runtime hashes, immutables, addresses, topology, configuration,
   balances, pending actions, authorities, pause state, Safe configuration,
   nonce, and exact calldata.
2. **Exact rehearsal.** Fork from that state with the actual candidate
   addresses and exact proposed payloads. Rehearse success, soft failure,
   revert, gas, safe hold, and forward recovery.
3. **Separate authorization.** Phase 0A, candidate deployment, RipeHQ action
   starts, core execution, Stability action starts/execution, and RipeGov
   staging/Gates 9A/9B are separate approvals. Approval for an action start
   does not authorize its later execution.
4. **No silent drift.** A changed release, runtime, state value, action ID,
   expiry, nonce, payload byte, authority, or policy invalidates the affected
   artifact and approval.
5. **Semantic success.** EVM transaction success is insufficient for calls
   returning `bool`, assigned IDs, counts, or USD totals. Assert the exact
   result in-transaction or stop at a rehearsed safe-hold boundary before any
   dependent step. Raw MultiSend plus a later readback is insufficient when a
   soft failure could allow dependent calls to continue.
6. **Forward recovery.** After the first irreversible write, unexpected state
   is a frozen forward-recovery event. Do not route RH AuctionHouse back to
   Pool 1 as a rollback.

### Complete freeze profile

Teller pause does not block every trusted producer, and
`depositFromTrusted` does not honor Teller pause.

For any migration or cutover freeze:

- Block Teller user writes.
- Block AuctionHouse/liquidation intake.
- Block HR contributor deposits and transfers.
- Block BondRoom deposits and auto-stake.
- Block Lootbox claim/auto-stake ingress while keeping required point and
  cleanup functions callable.
- Block CreditEngine and CreditRedeem mutation routes while keeping required
  housekeeping callable.
- Block Deleverage and governance withdrawal paths.
- Block every other `_isValidRipeAddr` or trusted producer discovered in the
  bound source/runtime census.
- Freeze unrelated configuration and price-source writes.
- Keep Ledger, required CreditEngine housekeeping, Lootbox accounting/cleanup,
  PriceDesk, pricing sources, and exact migration dependencies callable.
- Block candidate-generation ingress before each candidate becomes active and
  keep legacy-generation ingress blocked through the handoff.

The exact per-component freeze matrix and probes are in the
[technical appendix](./production-runbook-technical-appendix.md#811-producer-freeze-and-dependency-matrix).

---

## 4. Owner decisions and technical blockers

No phase may proceed while a decision or blocker due at that phase remains
open.

### Owner decisions

| ID | Decision | Recommended/current posture | Due |
| --- | --- | --- | --- |
| O-1 | Pool-6 launch capacity | Recompute seed or approve exact empty-pool posture | Gate 4 |
| O-2 | Transition deadline and escalation | Open | Gate 6 |
| O-3 | Users at Ledger vault limit | UX decision; controlled VaultMigrator deposits bypass the ordinary depositor limit | Gate 6 |
| O-4 | Transitional user treatment | Define legacy exits, claims, notice, incentives, and residual support | Gate 3 |
| O-5 | Stability reward and swept-asset policy | Sweep reward rate must be 0; bind exact terminal three-field tuple and custody | Gate 8A |
| O-6 | VaultMigrator ID | Required constraint: exactly HQ ID 25 | Gates 2 and 5 |
| O-7 | Production governance delays | Bind approved nonzero delays and freeze budget | Gate 4 |
| O-8 | RipeGov migration procedure | Resolve current all-assets-per-user implementation versus older serial policy | Before Phase-9 payloads |
| O-9 | Stability governance-seed ingress | Qualify temporary `[6,1]` support with 6 remaining default | Gate 8A |
| O-10 | Legacy Stability claim tail | Exact remediation-to-zero or exact owner-approved raw-tail manifest | Gate 8A |
| O-11 | BondBooster continuity | Preserve legacy recommended; otherwise design full state migration | Gate 1 |

Assign an owner and due gate now. Add an approval reference and immutable
evidence only when that decision actually closes; an empty future approval is
not a Gate-O failure.

### Technical blockers

| Blocker | Required closure | Due |
| --- | --- | --- |
| `TRANSITION-DEFAULTS` | Dedicated Base-transition Defaults generated from exact live state | Gate 1 |
| `MC-INACTIVE-STATE` | Census every ever-touched asset, inactive mapping, and stale slot; prove none or disposition each | Gate 1 |
| `TX-ASSERT` | Bind assertion-capable execution or exact safe-hold semantics for every soft return | Gates 4, 8B, and 9B as applicable |
| `SP-SWEEP` | Exact governance seed, claim, tail, restoration, and unwind proof | Gate 8A |
| `RG-PROCEDURE` | Exact deployed-legacy migration procedure selected and fork-proven | Before Phase-9 payloads |
| `RG-CLEANUP` | No-forfeiture reward, registration, and Ledger cleanup implementation and proof | Before Phase-9 payloads |
| Release and candidate evidence | Final build, runtime/immutable dossier, composed forks, payload review | Before the applicable write |

---

## 5. RH core deployment and cutover

### Phase 0 — Bind decisions and live state

**Goal:** establish one canonical starting point.

- [ ] Assign owners and due gates to O-1 through O-11; record each approval
  reference only when its decision closes.
- [ ] Bind the candidate source/build and a finalized Base block/hash.
- [ ] Inventory RipeHQ, VaultBook, Switchboards, MissionControl, PriceDesk,
  Safe, authorities, pause states, balances, and all pending actions.
- [ ] Inspect the native pending update for RipeHQ ID 8.
- [ ] If that update is still pending, cancel it only through its separately
  reviewed and authorized Phase-0A payload.
- [ ] If it already confirmed or the active VaultBook changed, stop and
  rederive the complete architecture.
- [ ] After any Phase-0A write, wait for the approved finality threshold and
  bind a new canonical block/hash.
- [ ] Build the exact configuration, user/delegation, vault, custody, claims,
  rewards, authority, and pending-state snapshots.
- [ ] Give every replaced storage value and pending action an explicit
  constructor, replay, preserve, reset, execute, cancel, expire/harmless, or
  deferred disposition. “Abandoned” is not a disposition.
- [ ] Independently reproduce the snapshot and disposition matrix.

**Gate 0:** canonical state artifact reproduced; no unexplained topology,
configuration, custody, authority, or pending-action drift.

### Phase 1 — Build the transition release

**Goal:** create a deterministic Base transition configuration, not a
greenfield launch configuration.

- [ ] Generate an exact-live snapshot artifact.
- [ ] Generate a separate transition overlay mechanically from it.
- [ ] Allowlist only:
  - Pool-6 Stability routing;
  - the new RH Contributor blueprint;
  - separately approved inactive-MissionControl reset/replay dispositions.
- [ ] Keep RIPE and RIPE/LP routes at `[2]`.
- [ ] Configure normal Stability assets for `[6]`, priority Stability routing
  for 6 only, and every `specialStabPoolId` as 0 or 6.
- [ ] Keep the transitional Stability reward rate at the owner-approved live
  value; the sweep-zero change belongs only to Phase 8.
- [ ] Start replacement MissionControl with `preferredStabVaultId == 1` and
  protect that temporary mismatch through the core freeze until Charlie
  rotates it to 6.
- [ ] Do not deploy unchanged `DefaultsBaseLive` or greenfield
  `DefaultsRobinhood`.
- [ ] Close `TRANSITION-DEFAULTS`, `MC-INACTIVE-STATE`, and O-11.
- [ ] Prove existing Contributor compatibility and new RH Contributor creation.
- [ ] Bind the exact PriceDesk/Pyth/Curve topology and selected BondBooster.
- [ ] Freeze the final release, compiler, creation/runtime bytecode,
  immutables, sizes, deployment manifests, and transition diff.
- [ ] Independently reproduce the final build and fork deployment.

**Gate 1:** deterministic transition overlay and final production build pass;
no non-allowlisted difference remains.

### Phase 2 — Deploy and qualify the inert candidate

**Goal:** deploy everything needed for cutover without exposing production
traffic.

- [ ] Independently review the exact candidate deployment and bounded-setup
  bundle and obtain separate authorization. It includes the qualified
  candidate pause/finalization writes (including legacy-Charlie pauses) but
  excludes RipeHQ action starts and activation.
- [ ] Deploy the RH Contributor blueprint and complete candidate stack.
- [ ] Build the replacement VaultBook in exact sequential order:
  live rows 1 → 5, new Stability Pool 6, new RipeGov 7.
- [ ] Require live rows 1–5 to be version 1 and verify every assigned ID,
  address, version, event, and counter before advancing.
- [ ] Build the replacement Switchboard registry in exact Alpha → Echo order.
- [ ] Deploy MissionControl only from the qualified transition Defaults.
- [ ] Deploy the RH departments and VaultMigrator with exact runtimes,
  immutables, authorities, and external references.
- [ ] Keep Teller and VaultMigrator paused.
- [ ] Keep AuctionHouse and RipeGov 7 paused before the HQ-6 authority handoff;
  use legacy Charlie while it still has authority.
- [ ] Keep Pool 6 unpaused when Charlie must validate the Stability pointer.
- [ ] Keep RipeGov 7 pristine.
- [ ] Finalize VaultBook and Switchboard registry delays before activation.
- [ ] Use only the qualified setup authority; remove temporary local governors
  and pending governance changes before HQ activation.
- [ ] Produce the checksum-bound candidate address/runtime/immutable/pause/
  authority dossier.

**Gate 2:** exact inert candidate qualified; no candidate can receive
unintended production traffic.

### Phase 3 — Prepare clients and operations

**Goal:** make the transitional topology usable before it becomes live.

- [ ] Frontend, indexer, keeper, and support tooling understand explicit
  legacy IDs 1 and 2 and new IDs 6 and 7.
- [ ] Present Pool 1 as legacy exit/claim/redeem only.
- [ ] Route new Stability deposits to 6 and test auction fallback.
- [ ] Present RipeGov 2 as active and RipeGov 7 as unavailable.
- [ ] Preserve historical events across replaced addresses.
- [ ] Deploy alerts for routes, pointers, pause state, Pool-6 capacity,
  fallback, pending actions, and any touch of RipeGov 7.
- [ ] Publish the owner-approved transition communication and incident path.

**Gate 3:** end-to-end off-chain flows and monitoring pass; O-4 is closed.

### Phase 4 — Rehearse and authorize the core cutover

**Goal:** prove the exact production sequence before any core action is
initiated.

- [ ] Fork from a fresh finalized Base block using actual candidate addresses.
- [ ] Rehearse the complete freeze and candidate/legacy ingress handoff.
- [ ] Rehearse candidate AuctionHouse and RipeGov-7 pauses before HQ-6 changes.
- [ ] Rehearse VaultBook-first activation and atomic HQ 5 → HQ 6 confirmation.
- [ ] Rehearse every department confirmation, VaultMigrator ID 25, config
  replay, pointer rotation, timelock finalization, Pool-6 capacity action, and
  reopen.
- [ ] Inject wrong IDs, soft `False`, zero/short returns, expired actions,
  stale nonces, wrong pause state, dependency failures, and late failures.
- [ ] Close the core `TX-ASSERT` branch.
- [ ] Measure gas, action timing, expiry headroom, freeze duration, and
  forward-recovery boundaries.
- [ ] Independently decode and verify the exact Safe payloads.
- [ ] Close O-1 and O-7 and obtain the exact Phase-5 action-start
  authorization. This does not authorize Phase-6 execution.

**Gate 4:** exact composed fork, failure tests, action-start payload hashes,
timing, and Phase-5 authorization pass.

### Phase 5 — Pre-stage RipeHQ actions

**Goal:** mature only the selected topology changes.

- [ ] Rebind and verify the Gate-4 action-start authorization before the first
  initiation.
- [ ] Initiate replacements for HQ IDs 5, 6, and 8–22.
- [ ] Initiate VaultMigrator as the sole append, expected to become ID 25.
- [ ] Do not touch preserved IDs 1–4, 7, 23, or 24.
- [ ] Do not write Base IDs 26 or 27 in the core program.
- [ ] Bind every native pending-operation key, old/new address, start block,
  confirmation block, and exact later execution.
- [ ] Monitor all copied state, pending actions, Safe state, and candidate
  pause/authority state while the delay matures.
- [ ] Rebuild and reauthorize if any bound value changes.
- [ ] Immediately before cutover, prove every action remains mature and exact,
  candidate AuctionHouse/RipeGov 7/Teller/VaultMigrator have the required
  pause posture, and no unrelated executable or future-maturing action remains.
- [ ] Bind the current Safe nonce and exact Phase-6 calldata, independently
  review them, and obtain a new Phase-6 execution authorization.

**Gate 5:** exact operations are mature and unchanged; current-nonce,
current-calldata Phase-6 execution is separately authorized.

### Phase 6 — Execute the core cutover

**Goal:** activate the RH stack and reach the stable transitional state.

Execute this order under the complete freeze:

1. Rebind the final block/hash, Safe nonce, payloads, pending actions, pause
   states, and candidate dossier.
2. Pause Teller, AuctionHouse, and every alternate trusted producer.
3. Wait the qualified later Base action block. Prove source counts and balances
   stopped changing before the first confirmation and re-prove that after each
   generation handoff.
4. Confirm the replacement VaultBook first and verify exact IDs 1–7.
5. In one assertion-capable atomic child, confirm HQ 5 MissionControl and then
   HQ 6 Switchboard. Assert both semantic returns and read back both addresses.
6. Confirm the remaining selected HQ 9–22 departments while blocking each
   candidate’s ingress before it becomes active.
7. Immediately before the VaultMigrator confirmation, require
   `getNumAddrs() == 24`, raw `numAddrs() == 25`, and no unrelated pending
   append, mature or immature. Confirm it and require the semantic return/event
   to assign exactly ID 25, then require counters 25/26 and exact address
   readback. Because appends are irreversible, do not wait until afterward to
   discover a pre-confirm mismatch.
8. Reconfirm Ledger is unchanged at HQ ID 4.
9. Freshly require `Charlie.actionTimeLock == 0` before any replay or pointer
   initiation. A nonzero value is a stop and replan, not a wait-and-continue.
10. Replay only approved configuration, user configuration, delegations, and
   pending-state dispositions during the bounded setup posture.
11. While the full freeze remains active, prove Pool 6 unpaused immediately
   before both Charlie initiation and execution; rotate
   `preferredStabVaultId` from 1 to 6 and read it back.
12. Clear every zero-delay setup action.
13. Finalize every applicable nonzero production timelock.
14. Only after finalization, initiate any approved production-surviving action
    with timing derived from the production delay.
15. Prove normal Stability routes point only to 6, Pool 1 remains historically
    classified and explicitly accessible, and no `specialStabPoolId` points to
    1.
16. Establish the owner-approved Pool-6 seed/capacity or exact empty-pool
    posture.
17. Prove RipeGov 2 remains core and RipeGov 7 remains paused and pristine.
18. Reopen Teller and approved producers after all readbacks.
19. Run bounded canaries for new Pool-6 flow and qualified legacy paths.
20. Reopen AuctionHouse last and run the qualified liquidation/fallback smoke
    test.

No zero-delay pending action, temporary governor, unapproved legacy action, or
unexplained custody/configuration difference may survive reopen.

**Gate 6:** Ledger unchanged; RH departments resolve the intended dependencies;
Pool 6 is the sole new Stability route; Pool 1 is legacy-only; RipeGov 2 is
core; RipeGov 7 is pristine; O-2 and O-3 are closed.

### Phase 7 — Operate the transition

This is a valid production state, not a failed migration.

- [ ] Pool 1 is absent from every RH liquidation route.
- [ ] Pool 6 is the sole Stability liquidation destination.
- [ ] No Pool-1 deposit occurs except the exact Phase-8 governance seed bundle.
- [ ] Qualified explicit Pool-1 exit, claim, and redeem paths remain usable.
- [ ] RipeGov 2 remains core and receives normal governance activity.
- [ ] RipeGov 7 remains paused, pristine, and absent from normal routes.
- [ ] VaultMigrator remains paused.
- [ ] Monitor Pool-6 spendable capacity, auction fallback, legacy holders and
  claims, RipeGov-2 census growth, pending actions, and the transition
  deadline.
- [ ] Escalate on route drift, fallback failure, capacity shortfall, legacy
  liveness failure, any RipeGov-7 touch, or an unapproved action.
- [ ] Never respond by routing RH AuctionHouse back to Pool 1.

**Gate 7:** the transition observation artifact is signed for the current
owner-approved period, no unresolved alert remains, and Phase-8 preparation is
separately authorized.

---

## 6. Stability Pool 1 → 6 migration

This is a separate later window. There is no requirement to combine it with
the core cutover.

### Stability entry requirements

- Gate 7 is signed for the current observation period and Phase-8 preparation
  is separately authorized.
- O-5, O-9, O-10, `SP-SWEEP`, and the preliminary Phase-8 `TX-ASSERT`
  executor/safe-hold design are closed.
- A fresh release/runtime bind, finalized block/hash, and complete Pool-1/6
  census exist. Final live-bound fork, payload, and `TX-ASSERT` closure belongs
  to Gate 8B; it is not implied here.
- `badDebt == 0` and every migration health/dependency check passes.

### Stability sequence

1. **Design without writing.** Enumerate every user, registered asset, balance,
   share, Ledger/Lootbox record, active and dormant/raw claim row, custody
   balance, price/claim status, and reward field. On the exact fork, design the
   governance seed/sweep, tail treatment, terminal reward tuple, custody, and
   partial-sweep unwind. Prepare—but do not initiate—the exact reward-zero,
   `[6,1]`/`[6]`, terminal restoration, and O-10 actions.
2. **Gate 8A and stage.** Gate 8A authorizes only those exact action starts.
   After it passes, initiate them and record every ID, tuple, maturity, expiry,
   nonce, and payload hash.
3. **Gate 8B.** After maturity, bind a new finalized block/hash; rebuild the
   census and economics; fork-execute the whole sequence; close final
   deployed-runtime/live-state/payload `TX-ASSERT`; and obtain separate exact
   execution authorization.
4. **Close claims.** Freeze AuctionHouse, alternate producers, unrelated
   configuration, and price writes while Teller has only the qualified bounded
   seed/claim availability. Execute reward zero without changing either
   auto-stake ratio. In one assertion-capable transaction, execute every
   `[6,1]` route, seed governance into Pool 1, and restore every route to `[6]`.
   Never use `[1,6]`.
5. **Respect action blocks.** An ordinary same-user seed and claim must occur
   in different Base blocks unless the exact identity/path is fork-proven
   exempt and separately owner-approved. Every additional same-user claim
   requires another qualified later block plus fresh `lastTouch`, claim,
   price, NAV, share, and entitlement preflight.
6. **Prove closure.** Execute the exact O-10 enable/register → claim →
   restore/deregister lifecycle, then pause Teller. Independently reproduce a
   closure artifact proving economic claims zero; raw remainder zero or exactly
   the approved tail manifest; and custody, shares, NAV, routes, reward tuple,
   and MissionControl terminal state reconciled. Do not migrate users first.
7. **Migrate.** Hold Teller paused; keep Pools 1 and 6 unpaused because the
   generic endpoint validates both; keep required dependencies callable; wait
   the qualified later block; recensus and preflight `lastTouch`; then unpause
   VaultMigrator only for a canary and measured SwitchboardEcho batches.
8. **Enforce batch semantics.** A generic child has 1–25 unique users and each
   included user has at most 20 registered source slots. An explicit-by-assets
   child has at most 20 unique positive assets; same-user explicit chunks use
   separate later blocks. Require the actual migrated-position count to equal
   the positive manifest count and reconcile every balance, share, Ledger,
   Lootbox, debt, custody, `lastTouch`, and event delta before advancing.
9. **Close out.** If O-10 approves a residual, every preceding user must match
   the exact fork and only the final governance position may absorb the exact
   approved rounding/tail effect. Migrate governance last, pause VaultMigrator,
   confirm the terminal reward tuple, reopen Teller/producers, and reopen
   AuctionHouse last.

A short positive count, skipped supported position, unapproved raw remainder,
stranded `[6,1]` route, changed auto-stake ratio, or unexplained one-unit delta
is a stop.

**Gate 8:** every intended Pool-1 position reconciles in 6; economic claims are
closed; raw accounting is zero or equals only the approved tail manifest; the
terminal reward policy is exact; Pool 1 can no longer create claim-reward
positions in RipeGov 2.

Detailed seed math, O-10 variants, `lastTouch` behavior, claim ceilings,
batching, return observation, and reconciliation fields are in the
[technical appendix](./production-runbook-technical-appendix.md#12-phase-8--stability-pool-1-to-6-migration).

---

## 7. RipeGov 2 → 7 migration

This is a separate later window and cannot begin until Stability Gate 8 passes.

### RipeGov entry requirements

- Gate 8 is complete.
- O-8, `RG-PROCEDURE`, `RG-CLEANUP`, and the preliminary Phase-9 `TX-ASSERT`
  executor/safe-hold design are closed.
- The exact deployed legacy RipeGov behavior—not the new contract as a
  substitute—passes the composed Base fork.
- A fresh census covers users, contributors, every registered source slot,
  balances, shares, points, pending points, unlocks, historical terms, rewards,
  Ledger membership, target support, custody, health, and `lastTouch`.
- Any user above the legacy 20-slot ceiling or any unsupported positive target
  asset has a reviewed new design or explicit owner disposition.
- The no-forfeiture cleanup implementation and fork proof are complete.
- Final live-bound `TX-ASSERT`, action IDs, payloads, nonces, and execution
  authorization close at Gate 9B; they are not implied here.

### RipeGov sequence

1. **Authorize staging.** Complete the fresh census and prepare exact bridge,
   temporary-term, restoration, freeze, and pointer-start packets. Obtain the
   separate `OP-RG-01` bridge/action-start authorization before any live write;
   it authorizes neither Gate 9A nor Gate 9B.
2. **Stage.** While 2 remains core and 7 paused/pristine, execute RIPE and
   RIPE/LP bridges `[2,7]` without changing other fields. Initiate—but do not
   execute—both temporary-term and exact-original restoration actions. Record
   every action ID, tuple, confirmation block, expiry, nonce, and payload hash.
3. **Gate 9A and pointer start.** Gate 9A authorizes only the exact freeze and
   pointer-initiation bundle. Freeze Teller and every HR, BondRoom, Lootbox,
   Credit, Deleverage/AuctionHouse, trusted-producer, and unrelated-config path;
   wait the required later block and prove the census stopped changing. In one
   atomic bundle, unpause 7, initiate `coreRipeGovVaultId: 2 → 7`, and re-pause
   7. Require the expected action ID and pristine readbacks, then hold the full
   freeze throughout Charlie’s timelock.
4. **Gate 9B.** At maturity, bind a fresh frozen block/hash, exact pointer
   action/timing, census, batches, failure branches, and count-observation
   method. Complete the composed fork, final runtime/live-state/payload
   `TX-ASSERT`, and separate execution authorization. Gate 9A grants none of
   this authority.
5. **Rotate and stage final routes.** In one atomic bundle, unpause 7, execute
   the pointer, and re-pause 7; require semantic success and exact readbacks.
   Only then initiate final `[7]` routes and hold the freeze through maturity.
   Gate 9B is not blanket authority for later-created action IDs: each such
   child waits for its actual ID, maturity, expiry, calldata, nonce, and hash to
   be rebound, independently reviewed, and separately signed.
6. **Open the legacy migration condition.** Before the temporary term change,
   prove the final routes mature, pointer 7, source 2 unpaused, target 7
   paused/pristine, and full freeze. The census must prove 43,199 is below every
   migrating position’s stored historical minimum. Execute
   `minLockDuration: 43,200 → 43,199` for both approved assets while asset
   weight, freeze flag, max duration, max boost, `canExit`, and `exitFee` remain
   unchanged. Do not substitute the fee-based courtesy-unlock mechanism. Wait
   the required later action block and preflight every user’s `lastTouch`.
7. **Migrate.** Unpause VaultMigrator only for migration; keep Teller paused,
   source 2 unpaused, target 7 paused, producers frozen, and Ledger/accounting/
   pricing/housekeeping dependencies callable. Canary through SwitchboardEcho,
   then use measured batches of at most 25 unique users and 20 aggregate
   registered source slots. Require exact migrated-position count equality and
   full source/target reconciliation after every batch.
8. **Restore and route.** Restore both exact original term tuples, execute the
   separately authorized matured `[7]` routes, pause VaultMigrator, and require
   `isRipeGovVaultId(2) == True` even though no new route points to 2.
9. **Clean up without forfeiture.** Settle every source reward directly to its
   user without auto-staking. Deregister only after balance and reward are zero;
   remove Ledger participation only after all assets, registrations, and
   rewards settle. Use only the approved Lootbox/deployed-Ledger authority
   path—never a direct or nonexistent migration-only remover.
10. **Close.** Run an independent terminal census, then reopen RipeGov 7,
    Teller, and approved producers only after exact reconciliation.

If the owner selects the older serial one-asset procedure, stop until the
required contract change is reviewed, tested, size-qualified, and fork-proven.
The current reviewed migrator must not be described as serial.

**Gate 9:** every approved user and contributor reconciles in 7; exact terms
are restored; no new route points to 2; `isRipeGovVaultId(2) == True`; every
retained legacy residual has an owner and continuing support policy; no reward,
registration, Ledger, HR, debt, or producer dependency required for retirement
remains unexplained.

Detailed legacy-term behavior, action ordering, cleanup mechanics, batching,
return observation, and reconciliation fields are in the
[technical appendix](./production-runbook-technical-appendix.md#13-phase-9--ripegov-2-to-7-migration).

---

## 8. Final closeout

- [ ] Run a second independent terminal census for legacy Pools 1 and 2.
- [ ] Confirm Ledger remains the exact original deployed contract and address.
- [ ] Confirm active RipeHQ, VaultBook, Switchboard, department, pointer, route,
  pause, authority, and timelock state matches the approved final manifest.
- [ ] Confirm VaultMigrator is paused.
- [ ] Keep legacy vaults and explicit legacy paths available until every
  residual has a named owner and support policy.
- [ ] Reconcile every Safe transaction, native pending-operation key, event,
  balance, share, point, reward, registration, debt, and residual custody item.
- [ ] Archive the exact release, build evidence, manifests, forks, payloads,
  signatures, receipts, readbacks, and accepted exceptions.
- [ ] Keep Reserve and vesting as a separate authorized Base program.

**Gate 10:** terminal censuses and final manifest reconcile; the evidence
archive is complete; no cleanup write is inferred from this gate.

---

## 9. Global stop conditions

Stop the affected program, maintain or enter the rehearsed safe hold, rebuild
from live state, re-fork, and reauthorize if any of these categories applies:

1. **Release mismatch:** source, tree, compiler, runtime, immutable, address, or
   artifact differs from the approved manifest.
2. **Ledger/topology mismatch:** Ledger changes; an HQ, VaultBook, Switchboard,
   PriceDesk, or required ID/order differs.
3. **Transition-state mismatch:** Defaults, inactive MissionControl state,
   Contributor compatibility, PriceDesk child binding, BondBooster posture,
   custody, or allowance disposition is incomplete or different.
4. **Authority/timing mismatch:** an unexpected governor, pending action,
   assigned ID, timelock, confirmation block, expiry, or zero-delay action
   exists.
5. **Freeze failure:** any unapproved producer or configuration path can mutate
   source/target state, or a required dependency is unavailable.
6. **Route/pause failure:** Pool 1 enters an RH liquidation route; Pool 6 is
   incomplete; RipeGov 7 is touched early; a pointer, route, pause, or pristine
   invariant differs.
7. **Semantic-success failure:** a `bool`, ID, count, USD total, event, or
   state delta differs; a soft failure or short positive return can advance a
   dependent operation.
8. **Migration/reconciliation failure:** a user/slot cap is exceeded, a
   supported position is skipped, claim/reward/raw-tail/term/cleanup state
   differs, or any balance/share/point/debt/registration/custody delta is
   unexplained.
9. **Safe/authorization drift:** nonce, calldata, payload hash, guard, module,
   owner set, threshold, signature, or approval differs.
10. **Policy gap:** a required owner decision is missing, stale, or contradicted
    by live state.

The exhaustive stop dictionary and recovery record are in the
[technical appendix](./production-runbook-technical-appendix.md#15-global-stop-conditions).

---

## 10. Gate and artifact dashboard

| Gate | Required outcome | Primary artifact/status |
| --- | --- | --- |
| O | Owners and due gates assigned; approval references added as each decision closes | Decision register |
| 0 | Canonical post-Phase-0A live state reproduced | `ART-CORE-01` |
| 1 | Transition Defaults and final release qualified | `ART-CORE-02` |
| 2 | Inert candidate identities and protections qualified | `ART-CORE-05` |
| 3 | Frontend/indexer/keeper/monitoring ready | `ART-CORE-03` |
| 4 | Exact core fork, failures, gas, and payloads pass | `ART-CORE-04`; core `TX-ASSERT` |
| 5 | Only exact mature RipeHQ actions remain | Core action manifest |
| 6 | Stable RH transitional production state live | Core receipts/readbacks |
| 7 | Transition controlled for approved period | `ART-TRANSITION-01` |
| 8A | Stability design and action starts approved | `ART-SP-DESIGN-01` |
| 8B | Fresh Stability execution package approved | `ART-SP-01`; `ART-SP-TAIL-01` |
| 8 | Stability migration and claim closure complete | `ART-SP-CLOSURE-01` |
| 9A | RipeGov freeze and pointer initiation approved | `ART-RG-EXEC-01` |
| 9B | Mature pointer and migration execution approved | `ART-RG-EXEC-02` |
| 9 | RipeGov migration and cleanup complete | Terminal RipeGov census |
| 10 | Final topology, residuals, and archive reconcile | `ART-CLOSEOUT-01` |

Blank evidence, owner, checksum, or **due** approval fields are blockers. The
detailed artifact register and dated operation cards live in the
[technical appendix](./production-runbook-technical-appendix.md#16-execution-record-templates).

**Current status:** architecture selected. Owner decisions, transition Defaults,
inactive MissionControl-state dispositions, final release binding, candidate
dossier, composed forks, typed-return enforcement, migration procedures,
payloads, and production authorizations remain incomplete.
