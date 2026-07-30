# Robinhood Minimal Contract-Change Reassessment

> **30 July 2026 reconciliation:** The historical minimum-change method and S4
> zero-cooldown conclusion remain controlling. Corrected PR #61 was later
> integrated at `ad831669943ccfe7b9ed57454995dfce51630a66` for distinct
> full-payoff, dust, safe-conversion, and governance boundaries; this did not
> reopen S4. `fullPayoffBuffer`, `overageBps`, `dustThreshold`, and `dustBps`
> remain zero and lack Robinhood machine-facing representation. Nothing is
> deployed, configured, active, or released, and the missing representation is
> not fixed by this documentation refresh.

**Status:** Owner directive recorded; S3 retained, S4 closed no-code, and S5
direction selected; remaining contract-by-contract decisions pending

**Prepared:** 24 July 2026

**Planning baseline:** `27765d29094256fa9619dd44a0bfd145863de8b7`

**S4 closure reconciliation:** `dd51c637f1462bede7529a53427bfb4327dbfb12`
on 24 July 2026

## Purpose

This document re-evaluates the Robinhood deployment plan under the owner's
controlling directive:

> Deploy Robinhood with the absolute minimum necessary production
> smart-contract changes. Prefer configuration, omission, disabled features,
> existing behavior, and explicit risk acceptance over broad portability or
> future-proofing changes.

This is not approval to deploy S3, disable a security control, list unsafe
collateral, omit a required component, or deploy anything. It creates a
mandatory necessity gate before any additional production-contract work.

## Controlling decision rule

For every proposed production-contract change, the owner must see and decide:

1. the exact launch requirement the current contract cannot satisfy;
2. the smallest no-source-change path;
3. the concrete risk introduced by that path;
4. the blast radius and reversibility of accepting that risk;
5. the smallest configuration, omission, operational, or monitoring
   mitigation;
6. the smallest source change if the no-change path is rejected; and
7. why that source change creates less total risk than accepting or deferring
   the behavior.

“Cleaner,” “more portable,” “more future-proof,” “consistent across chains,”
or “useful if enabled later” is not enough to justify a production-contract
change for the initial Robinhood release.

The order of preference is:

1. reuse the existing production source unchanged;
2. select Robinhood-specific values through `DefaultsRobinhood`, constructor
   arguments, governed parameters, or address/configuration data;
3. omit or leave a feature disabled;
4. accept and document a bounded residual risk;
5. add tests, deployment assertions, monitoring hooks, or operator controls
   without changing contract semantics;
6. make the smallest shared production-contract change only when the owner
   rejects every acceptable no-change path.

## Program-wide implications

- Track 6 is no longer an automatic S3-through-S5 production implementation
  sequence. The owner has accepted S3 as a narrow shared improvement, closed
  S4 without production implementation for the initial release, and selected
  a portable same-child-block direction for S5.
- Existing approvals of an implementation design do not prove that deploying
  that implementation is necessary.
- A completed and reviewed source change may still be reverted before the
  release freeze if the unchanged source satisfies the selected launch scope.
- `DefaultsRobinhood` remains the intended configuration artifact. It must not
  contain divergent protocol logic.
- Test, inventory, deployment-tooling, manifest, and verification work may
  continue when it does not force a production-contract change.
- A disabled or omitted feature must be explicit in manifests and
  post-deployment checks.
- Accepted risk must be stated in operational terms, not hidden inside a
  `false`, zero, or omitted address.

## Contract-change necessity table

### S3 — Lootbox interval floor

**Change already integrated into `rh`:**

- replace `Lootbox.ONE_DAY = 43_200` with a constructor-supplied immutable;
- add a constructor argument and getter; and
- update the ABI and tests.

**No-source-change launch path:**

- use the pre-S3 canonical Lootbox source;
- deploy Robinhood with `_underscoreSendInterval = 0`;
- keep `hasUnderscoreRewards = false`; and
- omit the Underscore registry/distributor integration.

The existing constructor skips the `ONE_DAY` assertion when the interval is
zero. Therefore the hardcoded Base floor does not block an initial Robinhood
deployment with Underscore rewards disabled.

**Risk accepted by the no-change path:**

- a later attempt to enable Underscore rewards on Robinhood would retain the
  `43_200` minimum, roughly six days at a nominal 12-second cadence rather than
  one day;
- correcting that future behavior would require a later reviewed shared
  upgrade or accepting the longer interval; and
- reverting S3 now means giving up the already-tested generic floor.

**Risk created by retaining/deploying S3:**

- new constructor ABI and runtime;
- a future Base redeploy/rewire and state-reset plan;
- temporary live-version drift;
- additional migration, verification, audit, and rollback surface; and
- Robinhood becomes the first production deployment of new bytecode unless Base
  converges first.

**Owner decision — retain S3 (24 July 2026):** the owner accepts S3 as a small,
targeted shared improvement despite Underscore being omitted at launch. Deploy
the shared S3 source on Robinhood with floor `7_200` and mutable interval `0`.
Preserve Base floor `43_200` and eventual coordinated Base convergence, while
keeping every Base deployment, registry, state-continuity, capability, and live
transaction action separately gated. Different immutable inputs may produce
different deployed runtime bytes; canonical source, compiler input, constructor
interface, and creation artifact remain shared.

### S4 — Deleverage cooldown and context

**Previously proposed change:**

- replace duplicated `7_200` constants with one configurable ceiling;
- potentially change Deleverage, SwitchboardDelta, and Teller; and
- add an authorized multi-leg context to replace same-number behavior.

**No-source-change launch path:**

- deploy the current Deleverage implementation;
- leave `deleverageCooldown = 0`, which is its current initialization and is
  not populated by Defaults or a committed migration;
- do not enable a nonzero cooldown on Robinhood; and
- record nonzero cooldown activation as a future gated feature.

When the stored cooldown is zero, the duplicated maximum and same-number
cooldown exception do not constrain execution.

**Risk accepted by the no-change path:**

- Robinhood launches without Deleverage cooldown protection;
- an authorized caller can invoke otherwise-valid deleverage actions without
  cooldown pacing;
- if governance later sets a nonzero cooldown, repeated Robinhood `NUMBER`
  values can preserve the current same-number bypass;
- the four-hour-versus-one-day intent ambiguity remains unresolved; and
- a later nonzero policy would require a separate security decision.

**Risk created by implementing S4:**

- coordinated changes to up to three live shared contracts;
- new constructor/interface/ABI and transient-context behavior;
- Base migration and unenumerable-checkpoint concerns;
- downstream Underscore compatibility risk; and
- materially larger audit and rollback surface.

**Owner and independent-security decision — no-code S4 (24 July 2026):**
Robinhood launches with the existing shared Deleverage and SwitchboardDelta
source, `deleverageCooldown = 0`, no cooldown pacing, and no Underscore
integration. S4 Stage B/C do not exist for the initial release. Track 7 H-08
must prove the live zero value, actual deployed-graph omission, and absence of
pending nonzero cooldown or nonempty Underscore-registry actions. Migration
`0020` is omitted or assertion-only and never state-changing. Reopen S4 before
Underscore inclusion or any nonzero cooldown proposal or queued action.

**Decision evidence:**
[`deleverage-cooldown-security-decision.md`](deleverage-cooldown-security-decision.md).

### S5 — Ledger same-execution-block guard

**Current behavior:**

- every successful Teller housekeeping call writes
  `Ledger.lastTouch[_user] = block.number`;
- a checked higher-risk action rejects after any earlier housekeeping touch
  for that user at the same observed number;
- lower-risk calls are unchecked but still arm a later checked rejection;
- the check is per user, not a global one-action limit; and
- this is a same-execution-block identity policy, not an elapsed-time,
  rate-limit, oracle-freshness, or price-snapshot policy.

**No-source-change path considered and rejected by the owner:**

- deploy the current Ledger, Teller, MissionControl, and SwitchboardDelta
  implementations;
- set `DefaultsRobinhood.shouldCheckLastTouch()` to `false`;
- leave Base's current default and deployed behavior unchanged; and
- verify that Teller still calls
  `Ledger.checkAndUpdateLastTouch(_user, False)`.

With `_shouldCheck = false`, Ledger would skip only the same-number assertion.
It would still write `lastTouch` and reject a locked account. The owner rejected
losing the same-block property and directed S5 to preserve it using the actual
chain execution-block identity.

**Owner-selected shared-source direction — portable action-block identity
(24 July 2026):**

- update the canonical Ledger implementation to obtain a narrow
  `ActionBlockClock` identity through a reviewed abstraction;
- use native EVM `block.number` for future ordinary-EVM deployments;
- use `ArbSys(0x64).arbBlockNumber()` for Robinhood's Arbitrum child-chain
  block identity;
- preserve the existing any-touch/checked-higher-risk ordering semantics unless
  Stage A finds an independent defect and returns it for separate approval;
- prohibit `chain.id` branching and prohibit using this action-block identity
  for durations, rates, timelocks, auctions, emissions, or oracle freshness;
- make Robinhood the first production deployment of the revised Ledger; and
- leave the current Base Ledger deployed indefinitely because migrating its
  extensive accounting state creates more risk than live-bytecode parity.

The exact abstraction shape remains an S5 Stage A and security-review decision.
Stage A must compare at least an immutable generic provider interface with the
smallest reviewed internal-source helper. A provider must fail closed; it may
not silently fall back from child-chain identity to ancestor
`block.number`.

**Risks accepted by the selected direction:**

- Robinhood is the first production deployment of a changed, high-state Ledger
  artifact;
- every checked action gains a clock dependency whose misconfiguration or
  failure may halt higher-risk actions;
- another higher-risk action is allowed in the next child block even when that
  block follows quickly, which is intentional;
- Base and Robinhood retain permanent deployed-bytecode divergence even though
  the repository keeps one forward canonical source;
- possible Underscore and delegated-action behavior changes; and
- a new abstraction, external call, ABI, constructor, gas, failure, and audit
  surface unless Stage A proves a smaller safe boundary.

**Minimal-change implementation rule:** change no unrelated Ledger accounting,
do not add a time or freshness layer, do not migrate Base, and do not broaden
the action set. Stage A must validate the owner-selected threat, prove live
Robinhood ArbSys behavior, choose the smallest safe abstraction, quantify gas
and failure behavior, and return the exact implementation/audit surface before
Stage B begins.

**Owner decision:** the security property, Robinhood clock source, canonical
source direction, Robinhood-first rollout, and permanent Base live-version
exception are approved for Stage A specification work. Production
implementation, provider shape, file set, ABI, deployment, and activation
remain unapproved.

### Track 8 — Stock Token vault behavior

**No-source-change path A, considered and rejected by the owner:**

- do not list Stock Tokens as collateral in the initial release.

**Risk accepted by path A:**

- the initial Robinhood deployment does not deliver Stock Token-backed credit,
  which may remove a central product objective.

The owner requires Stock Tokens in the initial Robinhood release, so omission
is no longer a passing launch disposition.

**No-source-change path B:**

- list Stock Tokens through an existing vault and explicitly accept its known
  behavior.

**Risk accepted by path B:**

- `SimpleErc20` can preserve phantom collateral after issuer-controlled custody
  loss, allow first-withdrawer capture, and permit a zero-backed internal
  auction to charge GREEN and reduce debt;
- `RebaseErc20`/`SharesVault` improves partial-loss socialization but does not
  provide an approved complete total-loss and debt-resolution policy; and
- issuer pause, blocklist, burn, forced redemption, and upgrade controls can
  turn these conditions into protocol bad debt or user loss.

These are not merely convenience or timing risks. They can affect collateral
value, debt reduction, liquidator payment, and loss allocation.

**Risk created by changing vault/accounting contracts:**

- broad custody, settlement, liquidation, debt, reward, and migration changes;
- shared Base behavior changes;
- high audit burden; and
- new-code vulnerability risk in the most financially sensitive path.

**Owner-selected product direction — mandatory initial-launch Stock Tokens
(24 July 2026):** Stock Tokens must be available in the initial Robinhood
release. Track 8 must actively define the smallest demonstrably sufficient
shared containment patch. This is not approval of Track 8's comprehensive
corrected-share design and not authorization to implement.

The minimum launch boundary must prevent new borrowing against missing custody,
prevent nominal internal settlement from masquerading as delivery, bound GREEN
payment and debt reduction by collateral actually delivered, measure deposits
by actual receipt, preserve repayment, and fail closed on an aggregate deficit.
Every proposed share, reward, total-loss, Ledger, storage, or migration change
must separately prove initial-launch necessity or move to a post-launch backlog.

Listing unchanged through a known-defective vault is not the selected path.
Any later request to accept that path must quantify exposure and separately
obtain owner/security approval. If no reasonably small patch can prove the
minimum boundary, Track 8 must return that evidence rather than silently select
either an unsafe listing or the comprehensive redesign.

### GREEN and RIPE CCIP

**Minimal existing-token path:**

- keep GREEN and RIPE token source unchanged;
- use Chainlink-assisted token administration if supported; and
- add only the smallest Department-compatible pool contracts required for the
  selected CCIP release.

**No-new-pool path:**

- omit cross-chain GREEN/RIPE bridging from the initial release.

**Risk accepted by omitting CCIP:**

- no Base/Robinhood token portability;
- isolated liquidity and supply on Robinhood; and
- dependent launch flows must remain local.

**Minimal-change recommendation:** do not modify GREEN/RIPE for
`getCCIPAdmin()` unless the owner decides CCIP is launch-critical and Chainlink
confirms there is no assisted-registration path. If bridging is not
launch-critical, defer the pools and bridge rather than modifying tokens.

**Owner decision:** pending Chainlink response and launch-scope decision.

### USDG PSM

**No-source-change path:**

- omit the PSM; or
- deploy the existing PSM disabled and without GREEN mint authority, only if
  downstream address requirements make omission more complex.

The existing official USDG/USD Chainlink path needs no price-adapter contract
change.

**Risk accepted by omission/disablement:**

- no Robinhood USDG↔GREEN PSM liquidity or redemption path at launch.

**Minimal-change recommendation:** prefer omission unless a required downstream
contract needs a PSM address; otherwise deploy existing source disabled. Do not
rename or generalize PSM code merely for Robinhood.

**Owner decision:** pending deployment-graph confirmation.

### SavingsGreen/sGREEN

**No-source-change paths:**

- omit SavingsGreen and disable dependent paths; or
- deploy the same existing implementation with chain-local configuration.

**Risk accepted by omission:**

- Stability Pool, insurance, reward, and lifecycle paths that assume sGREEN may
  need to be disabled or reconfigured; and
- omission may create more deployment-graph complexity than reusing the
  existing contract.

**Minimal-change recommendation:** choose between omission and unchanged reuse
based on the deployment graph. Do not write a new Robinhood SavingsGreen
variant.

**Owner decision:** pending.

### DefaultsRobinhood and deployment tooling

`DefaultsRobinhood`, network profiles, migration discovery, manifests,
verification adapters, and deployment assertions are configuration/tooling
work rather than broad core-protocol redesign.

**Minimal-change recommendation:**

- retain one interface-compatible `DefaultsRobinhood` configuration contract;
- keep protocol logic out of it;
- preserve `DefaultsBase`;
- implement only the tooling required to deploy, verify, and prove omissions;
  and
- do not let deployment convenience trigger unrelated core changes.

## Immediate program changes

1. Treat S4 as closed no-code for the initial release; do not create Stage B/C.
2. Carry S4's zero-value, omitted-Underscore, pending-action, and reopening
   assertions into S6 and Track 7 H-08 without adding production behavior.
3. Revise and review the S5 brief before launch. Stage A must treat the
   owner-selected same-child-block action clock as its controlling property,
   minimize the abstraction, and exclude Base migration.
4. Continue H-01 and deployment-tooling work because they do not require a
   production-contract redesign.
5. Keep Track 8 active on the critical path. Require an implementation-ready
   minimum-containment proposal and post-launch backlog before any code patch.
6. Retain S3 in the release source, but do not infer Robinhood deployment or
   Base convergence authorization from that source decision.
7. Draft S6 only after S5 Stage A and the Track 8 minimum-containment decision
   define the remaining minimal parameter and activation surface; consume S4
   as an approved zero/omission assertion rather than a contract field.

## Owner decision queue

The next owner discussion should answer these in order:

1. **Deleverage cooldown — resolved:** zero cooldown and its lost pacing are
   accepted for initial launch; reopen S4 before Underscore or any nonzero
   proposal or queued action.
2. **Ledger action clock:** which minimal abstraction safely returns native
   execution-block identity on ordinary EVM chains and ArbSys child-block
   identity on Robinhood without a Base Ledger migration?
3. **Stock Token containment:** which changes are indispensable for safe
   launch, and which loss-allocation, bad-debt, reward, and migration features
   can be deferred with explicit risk acceptance?
4. **CCIP:** is bridging required at launch, or may it be deferred if assisted
   registration is unavailable?
5. **PSM and SavingsGreen:** omit, deploy disabled, or reuse unchanged?

No production implementation should be inferred from answering a scope
question. Each accepted code change still needs its own exact diff, tests,
review, and deployment authorization.
