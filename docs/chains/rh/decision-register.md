# Robinhood deployment decision register

**Snapshot date:** 11 August 2026
**Current production-source candidate:** commit
`e12b1abe26218acb804d84670099c41169e5f515`, tree
`b680f0016f29f9a217054db9f80c0bbf9f0b9916`, under draft PR #73 status
reconciliation
**Current status authority:** [`status.yaml`](status.yaml)
**Stable architecture:** [`../rh-summary.md`](../rh-summary.md)
**Prior private dashboard:** [Deployment operating picture](https://ripe-robinhood-status.mickhagen.chatgpt.site)

This register is the canonical `RH-D` identifier and title namespace for
controlling owner decisions and accepted risks. The `decisions` list in
[`status.yaml`](status.yaml) must mirror every identifier and title here
exactly. This register does not replace the linked decision records, authorize
a new phase, or convert an approved direction into implementation, integration,
deployment, configuration, or activation authority.

PR #61 is merged and closed at final head `7293cf87…` and `master` squash
merge `91eda49…`; its production contract changes are integrated into `rh`.
The historical import ancestor `ad831669…` is not the present branch authority.
No launch-remediation candidate execution or release is authorized. Separately,
the GREEN/RIPE CCIP topology is confirmed live as recorded in
[`ccip-live-state.md`](ccip-live-state.md); that state does not authorize another
transaction or release action. The four corrected-PR controls remain zero and deferred and lack
Robinhood machine-facing parameter/planning representation. Every Deleverage
task is parked, and no Deleverage implementation track is open. The current
five parked lanes match the canonical [`status.yaml`](status.yaml) inventory
exactly: CreditEngine zero-backing reassessment and policy; every Deleverage
task; UniswapV2Prices admission and deployment; Sites recovery; and dashboard
deployment. The S4 zero-cooldown decision remains closed. All five lanes are
nonblocking until explicitly reopened.

The earlier `ae0cb49…` protocol/pause baseline remains historical evidence.
`DefaultsRobinhood.vy` now exists and compiles, Blueprint and Defaults are the
two editable value authorities, and the ledger is derived and synchronized.
The exact current result is `configuration_consistent=true`,
`deployment_ready=false`, with 64 readiness blockers. Repository configuration
is prepared and consistent; production/onchain configuration has not occurred.

## Program-level decisions

### RH-D001 — Minimum production-contract change

**Status:** Approved and controlling.

Prefer, in order:

1. unchanged production source;
2. deployment/configuration values;
3. omitted or disabled features;
4. explicit residual-risk acceptance;
5. the smallest indispensable shared production change.

Before any production-contract edit, show the no-change risk, blast radius,
smallest mitigation, new-code risk, and exact owner decision.

Source: [`minimal-contract-change-reassessment.md`](minimal-contract-change-reassessment.md).

### RH-D002 — One canonical shared source line

**Status:** Approved and controlling.

Robinhood does not receive a separate core-contract fork. Chain differences
belong in typed defaults, constructor arguments, governed parameters, addresses,
and migrations. `DefaultsRobinhood` is the intended chain-specific
configuration exception and must not contain divergent protocol logic.

Source: [`../rh-summary.md`](../rh-summary.md).

### RH-D003 — Chain-local protocol and limited bridging

**Status:** Approved and controlling.

Positions, collateral, pricing, liquidation, parameters, and governance remain
chain-local. Only GREEN and RIPE are candidates for bridging. No cross-chain
position accounting, global allocator, or cross-chain governance executor is
in the selected release.

Source: [`../rh-summary.md`](../rh-summary.md).

## Launch-product decisions

### RH-D004 — AAPL is the only initial Stock Token

**Status:** Approved.

Every later Stock Token requires its own identity, proxy/implementation,
runtime, transfer, oracle, administrative-control, and route evidence.

Source:
`track-8-m0-owner-decision-packet.md`.

### RH-D005 — Stock routes remain unreachable until containment closes

**Status:** Approved; implementation chain open.

Stock Tokens are required for the initial product, but every ordinary, trusted,
Department, borrowing, settlement, and activation path remains blocked until
the complete M1-M5 containment group, audit, exact configuration, and activation
gates close.

Sources:
`track-8-m0-owner-decision-packet.md` and
`track-8-m1-exact-receipt.md`.

### RH-D006 — Exact receipt on every Teller deposit route

**Status:** M1 implementation reviewed and integrated; Stock remains disabled
and unreachable.

Every authorized Teller deposit route proves that custody increased by the
exact requested amount and that the destination vault accepted that same
amount. The integrated implementation is controlling for that exact scope. It
does not select a vault, configure AAPL, close M5, or authorize Stock
registration, deployment, reachability, or activation.

Source:
`evidence/stock-token-m1-exact-receipt.md`.

### RH-D007 — Chain-native sGREEN, never bridged

**Status:** Approved.

Chain-native sGREEN deposits and withdrawals are launch requirements. sGREEN
must never receive a CCIP route.

Source:
`track-8-m0-owner-decision-packet.md`.

### RH-D008 — CCIP complete or disabled

**Status:** Historical disabled posture superseded by confirmed live state;
operational gates open.

GREEN and RIPE CCIP registration, routing, reciprocal wiring, governance
ownership, and mint capabilities are live. The owner has not yet disposed the
disabled rate-limit/zero-rate-admin posture, the full real-token OffRamp
destination-gas evidence remains open, and no live send backend or further
transaction/release authority is implied.

Source:
[`ccip-live-state.md`](ccip-live-state.md).

### RH-D009 — USDG price path

**Status:** Price path approved; PSM deployment and activation gated.

Use the existing official Chainlink USDG/USD feed through the shared
`ChainlinkPrices`/`PriceDesk` path. Do not inherit Base USDC yield routes.
Initial PSM minting, redemption, auto-deposit, and yield remain disabled unless
separately approved.

Source: [`usdg-psm-decision.md`](usdg-psm-decision.md).

## Shared-contract decisions

### RH-D010 — Lootbox immutable floor

**Status:** Approved, reviewed, and integrated.

- Base floor: `43_200`.
- Robinhood floor: `7_200`.
- Comparison: strict `block.number > lastUnderscoreSend + interval`.
- The decision does not authorize general cadence conversion.
- Historical migrations remain immutable.

Source:
[`lootbox-floor-implementation-record.md`](lootbox-floor-implementation-record.md).

### RH-D011 — Deleverage initial no-code posture

**Status:** Historical zero-cooldown posture approved and still closed;
corrected PR #61 source integrated without reopening S4.

Use the corrected shared Deleverage, AuctionHouse, and SwitchboardDelta source
introduced by historical import ancestor
`ad831669943ccfe7b9ed57454995dfce51630a66` and retained at the frozen
`ae0cb49…` baseline; keep Robinhood
`deleverageCooldown` zero and omit Underscore. The four new payoff/dust controls
also remain zero and deferred. Reopen S4 only before a nonzero cooldown, queued
cooldown action, or Underscore inclusion. The separately tracked machine-facing
representation gap for the four new controls does not reopen this decision.

Source:
[`deleverage-cooldown-security-decision.md`](deleverage-cooldown-security-decision.md).

### RH-D012 — Portable Ledger child-block identity

**Status:** Reviewed implementation integrated; downstream binding and proof
remain open.

- Native source discriminator `0`: use native `block.number`.
- Exact source `0x64`: use `ArbSys.arbBlockNumber()` child-block identity.
- Every other source: fail closed.
- No `chain.id` branch, fallback, or mutable provider.
- Keep the deployed Base Ledger untouched as a permanent live-bytecode
  exception; deploy the revised canonical source fresh on Robinhood.

Integration closes the implementation predicate only. Constructor binding,
deployment evidence, negative-path verification, monitoring, activation, and
release remain separately gated.

Sources:
`track-6-s5-checkpoint-0-owner-decision-packet.md`
and `track-6-s5-ledger-guard.md`.

## Deployment-system decisions

### RH-D013 — Typed network profiles

**Status:** Approved, reviewed, and integrated.

Use one immutable typed registry. Profiles store opaque environment-variable
references rather than secrets. Identity validation precedes authority.
Blocked or unsupported operations fail before account, provider, path, or
transaction work.

Sources:
`track-7-h2-network-profiles-cli.md` and
`evidence/network-profile-cli-implementation.md`.

### RH-D014 — Symbolic blueprint before concrete values

**Status:** H-03 Phase A evidence and implementation integrated; all concrete
values and all 28 canonical blockers remain open, including nine
Curve-specific typed inputs.

H-03 controls the typed launch graph, symbolic inputs, explicit omissions,
relation semantics, provenance, and blocker ownership. It does not approve
concrete addresses, artifacts, parameters, roles, or activation.

Sources:
`track-7-h3-robinhood-blueprint-omissions.md`
and
`evidence/robinhood-blueprint-phase-a.md`.

### RH-D015 — One combined defaults and parameter workstream

**Status:** H-04 source authority integrated; 21 decisions approved and
operative, `D-H04-19` retired and non-operative, zero open; deployment binding
and readiness remain gated.

H-04 and S6 share one owner and file boundary. `config/BluePrint.py` and
`contracts/config/DefaultsRobinhood.vy` are the two editable value authorities;
the typed JSON ledger is derived evidence, not an input surface.

All operative decisions are approved, and the integrated manifest carries 14
binding schedules. Defaults exists and compiles, and the ledger is
synchronized. Required external verification and deployment-produced bindings
remain unresolved, so deployment readiness fails closed with 64 blockers. The
corrected PR #61 four-control machine representation gap remains
preserved, but every Deleverage task is parked and no implementation track is
open until explicit owner reopening.

Source:
`track-6-s6-track-7-h4-defaults-parameters.md`.

### RH-D016 — Shared migration source, isolated histories

**Status:** Eight-file imperative Robinhood migration candidate under draft PR
#73 review; no executable plan is authorized or currently censused, execution
is unauthorized, and no Robinhood migration history exists.

The current candidate uses `migrations/robinhood-mainnet/0000_TokensAndHq.py`
through `0007_FinishSetup.py`. Review those repository files deterministically
against Blueprint and Defaults. The former shared declarative source, runner,
transaction executor, 17-stage/action census, and 86-key plan census are
retired historical evidence. Do not create history or infer an executable plan
from repository migration files.

Source:
`evidence/robinhood-migration-phase-a.md`.

### RH-D017 — Immutable manifest and evidence chain

**Status:** H-06 implementation and candidate macOS/APFS operator/storage-class
qualification integrated; final operator machine/volume, operational
publication, deployment, and release remain unauthorized.

H-06 owns canonical serialization, plan digest, immutable hash-linked evidence,
atomic publication, and current-attempt selection for the supported
macOS/APFS boundary. The reviewed implementation and its exact evidence are
integrated. Its accepted case-sensitive history-path and bounded power-loss
residuals remain controlling; Linux is unsupported and fails closed, and Linux
qualification is not an initial macOS/APFS release prerequisite.

This `RH-D017` section is the canonical durable decision record. Current H-06
status remains in [`status.yaml`](status.yaml), workstream `H-06`. Integration
does not authorize an operator run, operational publication, migration,
deployment, promotion, activation, production use, or release.

## Handoff-resource governance

### RH-D018 — Dashboard tooling is separate from launch dependencies

**Status:** Owner-ratified for the current handoff repository shape on 27 July
2026, against exact candidate commit
`330916b03d939c62bb8b05fc51691a2dbc70948f`. **Its repository-placement clause is
superseded by [RH-D024](#rh-d024--the-dashboard-is-extracted-from-the-active-tree)
on 7 August 2026.** The dependency-scope and H-01 isolation clauses below remain
in force.

Keep the self-contained dashboard application under
`docs/chains/rh/dashboard/` during the current handoff phase. Co-locating it
with [`status.yaml`](status.yaml) preserves same-commit updates across the
machine-readable authority, generated presentation, reading assets, and
integrity tests. Its directory boundary must remain clean enough for a later
move without disturbing protocol source.

The dashboard's npm packages are documentation tooling outside H-01's
launch-toolchain dependency and exception scope. Dashboard dependency alerts
must be owned and triaged separately. A dashboard package state, alert,
exception, update, or CI result cannot close, reopen, satisfy, replace, or
otherwise affect an H-01 launch-toolchain disposition.

The owner later authorized exact Next.js and eslint-config-next 16.2.12 pins,
plus only their required lockfile transitives. The post-update production-only
audit still reports three high-severity groups. With Node.js `v22.19.0` and npm
`10.9.3`, the tooling-inclusive full-tree audit against the exact committed
lockfile reports 46 groups: 38 high, 4 moderate, 4 low, and 0 critical. The update
therefore does not establish dashboard audit or alert closure. Development and
documentation tooling remains separately triaged under this decision and has
no H-01 effect.

Path-scoped CI must run the dashboard build, integrity tests, and lint whenever
`docs/chains/rh/**`, [`../rh-summary.md`](../rh-summary.md), or that workflow
changes. This workflow is a post-push backstop and manual verification surface,
not a substitute for the required local validation or explicit merge authority.

**Superseded in part.** The repository-placement clause above — "keep the
self-contained dashboard application under `docs/chains/rh/dashboard/`" — and its
path-scoped CI requirement are superseded by RH-D024. Everything else in RH-D018,
including the dependency-scope boundary and the rule that no dashboard package
state can affect an H-01 disposition, remains in force.

### RH-D024 — The dashboard is extracted from the active tree

**Status:** Owner-ratified on 7 August 2026, against the RH codebase
simplification branch `codex/rh-codebase-simplification` on baseline
`610b43f4508e85628a1362532a79d68d71ea902c`.

The self-contained dashboard application and its `rh-handoff-dashboard.yml`
workflow are removed from the active tree. This supersedes the RH-D018
repository-placement clause and its path-scoped CI requirement: there is no
dashboard build, integrity-test, or lint job in this repository, and
`docs/chains/rh/**` changes trigger no workflow.

All 27 files remain recoverable from
`610b43f4508e85628a1362532a79d68d71ea902c`, with per-file Git mode, blob ID, byte
length, and SHA-256 in
[`extracted-files.tsv`](../../simplification/extracted-files.tsv). Restoration is
a Git checkout of that commit and requires no reconstruction.

This decision changes repository placement only. It does not revoke the RH-D018
dependency-scope boundary, does not alter the RH-D019 publication posture — Sites
recovery, dashboard deployment, and access changes stay parked and nonblocking —
and does not authorize any Sites action. [`status.yaml`](status.yaml) is
unaffected as the sole machine-readable current-status authority; it was never
part of the dashboard directory.

### RH-D019 — Private dashboard is a temporary presentation mirror

**Status:** Owner-ratified temporarily for the immediate team handoff on 27
July 2026, against exact candidate commit
`330916b03d939c62bb8b05fc51691a2dbc70948f`.

The dashboard may remain privately published through Mick Hagen's personal
Sites account while the team adopts it. It is an optional human-facing mirror,
not a status, decision, implementation, integration, or deployment authority.
The repository documents are the complete durable handoff and must remain
sufficient if the site is unavailable.

**Current overlay:** Sites account/workspace recovery, dashboard version
creation, deployment, publication, and access changes are parked and
nonblocking. The historical ratification above is preserved; it does not
authorize a new Sites action.

Access remains explicit-allowlist only. Move the site to a team-owned
destination at the next natural republish after the team has adopted it, or
immediately if anyone besides Mick needs publishing rights. Changing the
hosting destination must not change the authority hierarchy.

## Reassessment and qualification disposition

### RH-D020 — Consolidated Profile 1 launch and Profile 2 follow-on

**Status:** Approved; superseded by RH-D021 only for the Curve launch topology.

The eight-report reassessment and qualification corpus is one consolidated
program package. The controlling disposition is:

- preserve current Ledger and Teller architecture;
- use the protected shared `BasicVault` behavior through `SimpleErc20` and
  retire the separate `GuardedErc20` artifact;
- preserve the launch boundaries that RH-D021 does not change: no Uniswap
  price source admitted or deployed and neither LP token admitted;
- treat RIPE/WETH V2 only as an optional externally held liquidity canary;
- retain GREEN/USDG follow-on higher powers and both LP admissions as
  separately gated, subject to RH-D021's bounded GREEN pricing route;
- keep the PSM disabled, allowlisted, canary-first, redemption-first, and
  separately activated;
- keep H-09 network-disabled by default with explicit opt-in read-only
  archive-fork qualification; and
- keep H-10 as the separate live-rehearsal lane.

CreditEngine zero-backing reassessment, every Deleverage task including
size/headroom work, UniswapV2Prices admission and deployment, Sites recovery,
and non-CCIP live deployment are deferred or separately unauthorized. CCIP is
confirmed live, while further operational work, transactions, and release are
separately gated. Future work is grouped
into the large packages defined by
[`reassessment-and-qualification-synthesis.md`](reassessment-and-qualification-synthesis.md),
not eight report-specific trains.

This decision records architecture and sequencing only. It does not authorize
contract, interface, ABI, migration, configuration, generator, test, RPC,
account, signer, deployment, activation, Sites, publication, or external-state
work.

### RH-D021 — Bounded Curve launch pricing

**Status:** Approved for this bounded repository candidate; deployment and
every external-state phase remain blocked.

Select unchanged `CurvePrices` at PriceDesk ID 2 for GREEN only, while keeping
Chainlink at ID 1, IDs 4 and 5 empty, and priority IDs `[1, 2]`. BlueChipYield
remains structurally selected at ID 3 in the blueprint but is deliberately not
deployed or finalized by the current production-remediation candidate. The
exact configured route is GREEN -> Curve GREEN/USDG -> PriceDesk -> Chainlink
USDG. USDG has no Curve feed, so the route cannot recurse.

This decision does not admit either LP token, add another Curve feed or
consumer, enable dynamic rates, create Teller reference snapshots, enable
Endaoment stabilization, use Curve in the PSM, or add Stock/Uniswap behavior.
Five official provider and binding identities remain unverified; the pool
address must be deployment-produced; and the slippage limit, minimum retained
liquidity, and production observation remain open. Those nine Curve-specific
blockers contribute to the current 64-binding fail-closed readiness result.

Current correction source:
[`rh-production-vyper-remediation.md`](rh-production-vyper-remediation.md).
The earlier Curve qualification remains historical risk provenance.

### RH-D022 — RIPE reward launch product decision approved; operations open

**Status:** Approved product decision; DP15 and P-H04-399 approved;
B-REWARD-PROMOTION remains operationally blocked.

Current source enables points at `0.009 RIPE/block`, assigns 10% to borrowers
and 90% to stakers, assigns zero to voters and general depositors, uses 75%
auto-stake for an explicit non-staking claim, a 33% lock-duration ratio, and
`1 RIPE/$` Stability rewards. It assigns `1,000,000e18` RIPE to rewards, zero
to HR, and `1,000,000e18` RIPE to bonds. Stock rewards remain disabled.

The controlling source values are in `DefaultsRobinhood`; the current
candidate correction is recorded in
[`rh-production-vyper-remediation.md`](rh-production-vyper-remediation.md).
The former reward qualification and derived packet remain historical
pre-remediation evidence, not current source authority. Initial checkpoints;
governance, lite-signer, and registered checkpoint-caller identities;
emergency-runbook acceptance; monitoring owners/routes; H-05/H-06/H-08/H-09;
testnet rehearsal; and release authorization remain open. This record
authorizes no deployment, activation, RPC, governance, signer, operator, or
release action.

### RH-D023 — LP launch admission reconsidered independently

**Status:** Qualification completed; neither LP token is launch-admissible as
a Ripe asset.

The owner explicitly reopened both LP launch-admission decisions on 1 August
2026. The fresh qualification did not treat RH-D020's prior no-admission
posture as a stop condition. It independently found:

- the GREEN/USDG pool and bounded GREEN pricing route are selected launch work,
  but the GREEN/USDG LP token is not launch-admissible as collateral or another
  valuation-dependent Ripe asset;
- RIPE/WETH may remain a conditional externally held V2 liquidity/monitoring
  canary, but its LP token is not launch-admissible in Ripe; and
- neither zero LTV nor a missing price feed proves ordinary-only routing under
  the current shared contracts. Trusted deposit and valuation-dependent
  routes remain reachable if an LP becomes a supported asset.

Both Defaults LP rows therefore remain omitted, every DP-14 leaf remains a
typed blocker, priority IDs are `[1, 2]`, unchanged `CurvePrices` remains
selected at PriceDesk ID 2 for GREEN only, and the Uniswap monitor stays
interface-inert. Pool selection and GREEN pricing do not grant LP-token
admission. Closing the LP route gap would require shared production design
beyond a narrow LP configuration change and outside the preserved Deleverage
boundary.

This negative LP-admission result follows from missing verified identities,
decimals, limits, custody controls, and negative-route evidence—not merely
RH-D020's prior policy. No LP token is configured, registered, held as a Ripe
asset, admitted, or active; the selected GREEN/USDG pool remains undeployed and
unfunded. Future owner, external, implementation, fork, and security work may
explicitly reopen the result.

See
`qualification/lp-launch-admission.md`.
This decision grants no pool creation, funding, custody, RPC, migration,
registration, configuration, deployment, activation, or release authority.

## Dated security obligations

The two retained and operative H-01 dependency-security exceptions
(`EX-H01-PYTEST-01` and `EX-H01-PYMDOWN-B64-01`) require review on **15 August
2026** and hard-expire at **2026-08-31T23:59:59Z**. Missing the review makes an
affected exception stale for deployment rehearsal; expiry blocks rehearsal and
merge unless the exception has been retired or valid replacement authority
exists. See
[`evidence/dependency-security-gate.md`](evidence/dependency-security-gate.md).

## External and live-action decisions still open

The following are explicitly not decided or authorized:

- the exact Chainlink message, recipient, channel, supported release, and
  toolchain;
- a live Stock Token probe sender, recipient, provenance path, signer, amount,
  gas ceiling, and transaction sequence;
- final Robinhood addresses, roles, parameters, and manifests;
- exact archive-fork pin/provider/engine, token/proxy/layout, oracle/sequencer,
  pool/custody, and H-07/H-08/H-09 interface packets;
- final PSM production economics, reserve coverage, authorities, and activation
  ceremony;
- every Curve use beyond the bounded GREEN launch route and both LP-token
  admissions;
- Sites account/workspace recovery, dashboard deployment, or access changes;
- any testnet funding, signing, broadcast, deployment, or governance action;
- any production deployment, configuration, activation, or role transfer; and
- any claim that current dependency pins caused authoritative GitHub alert
  closure.

See [`status.yaml`](status.yaml), `hard_gates`, for the current stop surface.

### RH-D025 — Production clock usage is no longer scanned

**Status:** Owner-accepted on 8 August 2026, against the RH codebase
simplification branch `codex/rh-codebase-simplification`.

The block-clock inventory is removed from the active tree:
`scripts/check_block_clock_inventory.py`,
`config/block-clock-inventory.json`, and
`tests/inventory/test_block_clock_inventory.py`. Nothing replaces it.

**Scope of what is no longer checked.** The inventory scanned production sources
for `block.number` and `block.timestamp` usage, for mixed-clock arithmetic, and
for Vyper paths absent from its classification. None of those is scanned now. A
new production timestamp occurrence, a moved occurrence, or a new unclassified
path can enter with nothing objecting.

**Rationale.** The inventory enforced an exact repository file census —
`EXPECTED_PRODUCTION_COUNTS = (102, 97, 18)`, with remediation text forbidding
mechanical updates — which made every deletion require a semantic-owner
ceremony, and it was itself contributing 176 errors. The cost was paid on every
change to the repository, whether or not that change went anywhere near a clock.

An earlier revision of this rationale added that the inventory "could not detect
a contract defect" and that "its benefit was a listing." A review judged that too
categorical, and it was — it also contradicted this record's own scope paragraph
above. Stated accurately: the inventory was a **static policy scanner**, and it
did detect things. It flagged new `block.number`/`block.timestamp` occurrences,
mixed-clock arithmetic, and Vyper paths missing from its classification. What it
could not do is prove a clock-semantics defect in contract behaviour; it reported
on the shape of the source, and a correct occurrence and an incorrect one look
alike to it.

So the trade being accepted is not "no benefit for a cost." It is: a real
early-warning signal over clock-affecting source edits, given up because it was
welded to a whole-repository file census that fired on every unrelated change.
The reconsideration trigger below asks for the signal back without the census.

**Residual risk, accepted.** A clock-semantics regression on Robinhood is the
failure this guarded against, and it is now caught only by contract behaviour
tests and human review of clock-affecting changes.

**Reconsideration trigger.** Reopen if a clock-related defect reaches a
deployment candidate, if a second chain with a divergent block clock is added,
or if production clock usage is changed by someone without Robinhood cadence
context. A replacement should be a narrower maintained scanner over
`block.number`/`block.timestamp` occurrences, not a file census.

**Source:** `docs/simplification/REMOVED.md`, `docs/simplification/validation-evidence.md` section 14.

### RH-D026 — CreditEngine carries an exact headroom waiver at 184 bytes

**Status:** Retired on 11 August 2026. The owner-granted 8 August waiver remains
historical evidence for the exact prior version on
`codex/rh-codebase-simplification`.

**Retirement.** The liquidation-state change produced a new CreditEngine
version and therefore reopened this exact-version decision as required. A
behavior-preserving size consolidation leaves the new constructor-bound runtime
at 24,367 bytes, with 209 bytes of EIP-170 headroom. CreditEngine is again
governed by the default 200-byte floor; its override and pinned waiver identity
have been removed from `tests/test_vault_pointer_runtime_sizes.py`. No new
below-floor waiver was granted.

The deposit-vault hardening plan section 11.5 sets at least 200 bytes of
EIP-170 headroom as the acceptance threshold for a changed deployed contract,
and anything below 200 requires an exact owner waiver under RG-SIZE-01. This is
that waiver.

**Scope.** `CreditEngine` only, at its measured 24,392-byte runtime, leaving
**184 bytes** of headroom. `tests/test_vault_pointer_runtime_sizes.py` records
it as a per-contract override; every other contract in that set is held to the
ratified 200, and `Teller` states 200 explicitly.

**What exactly is waived.** One *contract version*, pinned by five identities,
not a size band:

| Identity | Value |
| --- | --- |
| `contracts/core/CreditEngine.vy` sha256 | `d8fae4e9cffff0d95adbe48a59e57c622585f021017b94089f8a70e615c36e43` |
| Runtime template sha256 (immutable-free) | `e75de103fc42b14907ddc409e55cc1366a82c6c8f9cf0719dd3dbe197610b943` |
| Runtime template bytes | 24,296 |
| Deployed runtime bytes (with immutables) | 24,392 |
| Deployed runtime sha256 at declared HQ `0x…00A1` | `12a781ca7793d79a866c3285f67f80fce65342dffc86239054a00653e94f7ac5` |

Two reviews shaped this list, and each defeated the version before it.

The first revision recorded only the 184-byte floor. A reviewer changed a
production rule — `assert _discount <= HUNDRED_PERCENT` to
`assert _discount < HUNDRED_PERCENT`, making a 100% discount invalid — and the
deployed runtime stayed at exactly 24,392 bytes, so the floor passed. The source
hash closes that: it moves on any source edit, size-preserving or not.

The second revision added the source and template hashes and then claimed to bind
"one exact artifact." **That was still false**, and a second reviewer proved it:
deploying CreditEngine with a different `RIPE_HQ_FOR_ADDYS` changes the deployed
byte string — including the registry authority the contract trusts — while the
length stays at exactly 24,392, so every recorded identity still matched. The
last row closes it, by deploying at a *declared* constructor input and hashing
the complete result.

**What this does not bind, deliberately.** The constructor arguments of any
particular deployment. `0x…00A1` is a declared constant that exists only to make
the deployed bytes reproducible; it is not a real HQ. Rewiring the test fixture
to a different HQ still passes this guard, and that is correct: constructor
arguments are deployment configuration, not contract version, and a code *size*
waiver must not fail on test wiring that cannot affect code size. A wrong HQ in a
real deployment is a deployment defect, caught by the behaviour suites that
resolve addresses through it, not by an EIP-170 waiver.

**Rationale.** The 184-byte position is inherited from `rh`. This branch changes
no production Vyper, so it neither caused the shortfall nor can repair it. The
alternative considered and rejected was lowering the default floor to 150 for
every contract, which an independent review correctly identified as silently
weakening a ratified rule — a synthetic StabilityPool at 176 bytes would have
passed.

**Residual risk, accepted.** CreditEngine has less margin than the ratified rule
allows. An earlier revision of this record said a future change "has 184 bytes to
work in before the guard fails," which conflated two different quantities. Stated
precisely:

- **184 bytes** is the absolute EIP-170 headroom — the room a change could use
  before the 24,576-byte limit itself is breached.
- **0 bytes** is the growth this waiver permits. The deployed size is pinned at
  exactly 24,392, so any change to the contract — larger, smaller, or
  size-preserving — fails the guard and reopens this decision. That is the
  intent: the waiver covers one contract version, not a range. (A change to a
  *deployment's* constructor arguments is not a change to the contract; see the
  exclusion recorded above.)

**Reconsideration trigger.** Withdraw this waiver when CreditEngine is next
changed on `rh`: either the change brings it back above 200, or it needs its own
owner waiver at the new figure. Lowering the recorded 184, or refreshing any
pinned hash above, requires a new decision — not an edit to the test. Refreshing
a constant to restore green is precisely the failure this record exists to
prevent.

**Self-retiring.** This exceptional binding applies only while CreditEngine sits
below the ratified floor. Once it is back at 200+ bytes of headroom, its
`MIN_HEADROOM_OVERRIDES` entry and its pinned identity are both removed, and it
returns to being governed by the floor like every other contract. A test asserts
the two tables cannot drift apart in either direction.

**Source:** `tests/test_vault_pointer_runtime_sizes.py`,
`docs/chains/rh/deposit-vault-smart-contract-hardening-implementation-plan.md` section 11.5.

### RH-D027 — Teller carries an exact migration and receipt-guard waiver at 71 bytes

**Status:** Owner-granted on 10 August 2026 for the VaultMigrator integration
candidate in PR #83; exact artifact replaced by owner decision on 11 August
2026 for PR #95.

The ratified runtime-size rule remains at least 200 bytes of EIP-170 headroom.
The integrated VaultMigrator design deliberately keeps Teller as the thin,
identity-authenticated router for actions only Teller may perform. The owner
reviewed that result, accepted Teller's measured size, and authorized this
integration. This record applies the existing exact-waiver policy to that
approval rather than lowering the shared rule.

The replacement retains the housekeeping guard that prevents an external
receipt-measurement callback from entering Teller housekeeping. To recover
headroom without changing behavior, the one-use preferred-StabilityPool helper
was inlined at its sole caller. The same MissionControl view call and nonzero-ID
check remain, and no public ABI or storage item changed.

**Scope.** `Teller` only, at a measured 24,505-byte deployed runtime, leaving
**71 bytes** of EIP-170 headroom. Every non-waived contract remains subject to
the 200-byte floor; RipeGov separately retains its 1,000-byte migration-branch
guard.

**What exactly is waived.** One contract version and one complete deployed-byte
identity at declared constructor inputs:

| Identity | Value |
| --- | --- |
| `contracts/core/Teller.vy` sha256 | `fe99197239821ef0eae63409fdca39aa4bd84b501697915150d0fec050406476` |
| Runtime template sha256 (immutable-free) | `3e1fa83b151ee933d28a0268975a47610f87d14ca18f248e79e0db80563398c8` |
| Runtime template bytes | 24,409 |
| Deployed runtime bytes (with immutables) | 24,505 |
| Deployed runtime sha256 at declared HQ `0x…00A2`, `_shouldPause = false` | `8980ea1cae7a32927d120e3fc333d3a1039d778cf09c1b7293a57cd755d67ea9` |

The declared HQ is not a real deployment address. Together with the explicit
pause input it makes Teller's immutable-bearing deployed byte string
deterministic. A deployment's actual constructor configuration remains a
separate deployment concern.

**Residual risk, accepted.** Only 71 bytes remain before EIP-170. This waiver
permits **0 bytes** of runtime growth: the exact size and identities above are
pinned, so a larger, smaller, or size-preserving Teller change fails the guard.
The narrow margin makes future Teller work likely to require deletion,
refactoring, or another explicit owner decision.

**Reconsideration trigger.** Reopen on any Teller source or compiler-output
change, and reassess when the transitional legacy-governance route is removed.
If Teller then has at least 200 bytes of headroom, remove both the override and
its identity record. Updating a pinned identity merely to restore a green test
does not continue this approval.

**Source:** `tests/test_vault_pointer_runtime_sizes.py`,
`docs/chains/base/ripe-gov-vault-migration/BRANCH-STATE.md`.

## Maintenance rule

When an owner decision changes, update:

1. the controlling decision/evidence record;
2. this register;
3. [`status.yaml`](status.yaml), preserving exact identifier/title parity; and
4. the generated dashboard.

Keep the distinction between:

- an approved direction;
- approved exact bytes;
- an implemented package;
- independent review;
- feature publication;
- `rh` integration;
- live validation; and
- deployment or activation.
