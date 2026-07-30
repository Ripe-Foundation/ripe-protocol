# Robinhood deployment decision register

**Snapshot date:** 30 July 2026
**Program subject:** commit
`ad831669943ccfe7b9ed57454995dfce51630a66`, tree
`3467f4a75aa37203d615407d5baf9c5fc9035639`
**Current status authority:** [`status.yaml`](status.yaml)
**Stable architecture:** [`../rh-summary.md`](../rh-summary.md)
**Private dashboard:** [Deployment operating picture](https://ripe-robinhood-status.mickhagen.chatgpt.site)

This register is the canonical `RH-D` identifier and title namespace for
controlling owner decisions and accepted risks. The `decisions` list in
[`status.yaml`](status.yaml) must mirror every identifier and title here
exactly. This register does not replace the linked decision records, authorize
a new phase, or convert an approved direction into implementation, integration,
deployment, configuration, or activation authority.

Corrected PR #61 is integrated into `rh`; upstream PR #61 remains separately
open and unmerged as of the fresh live check. No Robinhood deployment,
migration execution or history, production configuration, activation, or
release has occurred. The four corrected-PR controls remain zero and deferred
and lack Robinhood machine-facing parameter/planning representation. That gap
belongs to a separately authorized future implementation track. The S4
zero-cooldown decision remains closed; CCIP and zero-backing policy work remain
deferred and nonblocking.

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
[`track-8-m0-owner-decision-packet.md`](track-8-m0-owner-decision-packet.md).

### RH-D005 — Stock routes remain unreachable until containment closes

**Status:** Approved; implementation chain open.

Stock Tokens are required for the initial product, but every ordinary, trusted,
Department, borrowing, settlement, and activation path remains blocked until
the complete M1-M5 containment group, audit, exact configuration, and activation
gates close.

Sources:
[`track-8-m0-owner-decision-packet.md`](track-8-m0-owner-decision-packet.md) and
[`track-8-m1-exact-receipt.md`](track-8-m1-exact-receipt.md).

### RH-D006 — Exact receipt on every Teller deposit route

**Status:** M1 implementation reviewed and integrated; Stock remains disabled
and unreachable.

Every authorized Teller deposit route proves that custody increased by the
exact requested amount and that the destination vault accepted that same
amount. The integrated implementation is controlling for that exact scope. It
does not select a vault, configure AAPL, close M5, or authorize Stock
registration, deployment, reachability, or activation.

Source:
[`evidence/stock-token-m1-exact-receipt.md`](evidence/stock-token-m1-exact-receipt.md).

### RH-D007 — Chain-native sGREEN, never bridged

**Status:** Approved.

Chain-native sGREEN deposits and withdrawals are launch requirements. sGREEN
must never receive a CCIP route.

Source:
[`track-8-m0-owner-decision-packet.md`](track-8-m0-owner-decision-packet.md).

### RH-D008 — CCIP complete or disabled

**Status:** Approved launch posture; external and implementation gates open.

GREEN and RIPE CCIP are separately reviewed promotion targets within seven days
after launch. If any identity, role, route, supply, accounting, monitoring,
rollback, or state-independence gate is incomplete, launch and remain with CCIP
disabled.

Source:
[`track-8-m0-owner-decision-packet.md`](track-8-m0-owner-decision-packet.md).

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
integrated at `ad831669943ccfe7b9ed57454995dfce51630a66`; keep Robinhood
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
[`track-6-s5-checkpoint-0-owner-decision-packet.md`](track-6-s5-checkpoint-0-owner-decision-packet.md)
and [`track-6-s5-ledger-guard.md`](track-6-s5-ledger-guard.md).

## Deployment-system decisions

### RH-D013 — Typed network profiles

**Status:** Approved, reviewed, and integrated.

Use one immutable typed registry. Profiles store opaque environment-variable
references rather than secrets. Identity validation precedes authority.
Blocked or unsupported operations fail before account, provider, path, or
transaction work.

Sources:
[`track-7-h2-network-profiles-cli.md`](track-7-h2-network-profiles-cli.md) and
[`evidence/network-profile-cli-implementation.md`](evidence/network-profile-cli-implementation.md).

### RH-D014 — Symbolic blueprint before concrete values

**Status:** H-03 Phase A evidence and implementation integrated; all concrete
values and all 18 typed blockers remain open.

H-03 controls the typed launch graph, symbolic inputs, explicit omissions,
relation semantics, provenance, and blocker ownership. It does not approve
concrete addresses, artifacts, parameters, roles, or activation.

Sources:
[`track-7-h3-robinhood-blueprint-omissions.md`](track-7-h3-robinhood-blueprint-omissions.md)
and
[`evidence/robinhood-blueprint-phase-a.md`](evidence/robinhood-blueprint-phase-a.md).

### RH-D015 — One combined defaults and parameter workstream

**Status:** H-04 schema v2 integrated; 20 decisions approved and operative,
`D-H04-19` retired and non-operative, zero open; binding and rendering remain
gated.

H-04 and S6 share one owner and file boundary. The typed manifest is the value
and provenance authority. `DefaultsRobinhood` is a deterministic compatible
projection, not an independent source of values.

All genuine decisions are approved, and the integrated manifest carries 14
binding schedules. Required identities, `TrainingWheels`, and `liteSigners`
remain unresolved, so `DefaultsRobinhood.vy` is absent and the generator fails
closed. The corrected PR #61 four-control machine representation gap remains a
separate future implementation track.

Source:
[`track-6-s6-track-7-h4-defaults-parameters.md`](track-6-s6-track-7-h4-defaults-parameters.md).

### RH-D016 — Shared migration source, isolated histories

**Status:** H-05 deterministic blocked planning integrated; execution
unauthorized and no Robinhood migration history exists.

Use one shared `migrations/robinhood/` source and separate immutable
Robinhood-testnet and Robinhood-mainnet histories if and only if later
execution is authorized. Current deterministic reports are predeployment
planning: a reservation, assertion, omission, blocked row, deferred row,
rejection, or tooling-only row is not an executable migration; `plan_hash`
remains null while planning is blocked.

Source:
[`evidence/robinhood-migration-phase-a.md`](evidence/robinhood-migration-phase-a.md).

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
`330916b03d939c62bb8b05fc51691a2dbc70948f`.

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

### RH-D019 — Private dashboard is a temporary presentation mirror

**Status:** Owner-ratified temporarily for the immediate team handoff on 27
July 2026, against exact candidate commit
`330916b03d939c62bb8b05fc51691a2dbc70948f`.

The dashboard may remain privately published through Mick Hagen's personal
Sites account while the team adopts it. It is an optional human-facing mirror,
not a status, decision, implementation, integration, or deployment authority.
The repository documents are the complete durable handoff and must remain
sufficient if the site is unavailable.

Access remains explicit-allowlist only. Move the site to a team-owned
destination at the next natural republish after the team has adopted it, or
immediately if anyone besides Mick needs publishing rights. Changing the
hosting destination must not change the authority hierarchy.

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
- any testnet funding, signing, broadcast, deployment, or governance action;
- any production deployment, configuration, activation, or role transfer; and
- any claim that current dependency pins caused authoritative GitHub alert
  closure.

See [`status.yaml`](status.yaml), `hard_gates`, for the current stop surface.

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
