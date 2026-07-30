# Robinhood smart-contract change rationale

**Current frozen source snapshot:** `rh` commit
`ae0cb49bad9ad615deb11cbca5d3a2c20e38bb4c`, tree
`a6a34a385b48819bbf66249d518d76da3806b033` (30 July 2026).
PR #61 is merged and closed at final head `7293cf87…` and `master` squash merge
`91eda49…`; its production contract changes are integrated into `rh`. No
Robinhood deployment, migration execution, production configuration,
activation, RPC, account, key, signer, or release action has occurred.

> [!IMPORTANT]
> **Draft explanatory synthesis.** This directory explains production source
> changes present in the reviewed `rh` snapshot below. It is not controlling
> approval, deployment, configuration, migration, activation, or release
> evidence. Each page distinguishes integrated facts, historical evidence,
> independently reproduced results, agent recommendations, owner directions,
> owner-parked work, and deployment or release gates.

This directory is the contract-centric explanation of production smart-contract
changes carried by the Robinhood (`rh`) branch. It answers:

- which production contracts changed;
- why each source change was necessary;
- what behavior changed;
- what tests support the change;
- what the change does not prove; and
- which risks or deployment decisions remain open.

The individual records intentionally use contract names and behavior as their
primary structure. Historical workstream labels such as M1, M2, M3, S3, and S5
appear only in provenance sections.

Current rationale pages:

- [`deleverage.md`](deleverage.md) — trusted full-payoff boundaries, collateral
  and debt caps, bounded dust write-off, zero defaults, and seven-byte EIP-170
  headroom;
- [`auction-house.md`](auction-house.md) — safe conversion, clamps, soft-zero
  behavior, batch isolation, and Deleverage consistency;
- [`switchboard-delta.md`](switchboard-delta.md) — four timelocked actions,
  hard ceilings, and unactivated zero configuration;
- [`credit-engine.md`](credit-engine.md);
- [`guarded-erc20.md`](guarded-erc20.md);
- [`ledger.md`](ledger.md);
- [`lootbox.md`](lootbox.md); and
- [`teller.md`](teller.md).

The four Deleverage controls remain zero and deferred, but they currently lack
Robinhood machine-facing parameter/planning representation. The deployment
owner owns their final disposition and binding; the machine change still
requires separate authority and is not fixed here.
`DefaultsRobinhood.vy` remains absent and fail-closed.

## Documentation standard

Each contract record is intended to stand on its own. It should explain:

- the behavior before the change and a concrete failure scenario;
- the security property or chain-specific requirement being enforced;
- the complete modified execution flow;
- why the chosen implementation was preferred over simpler alternatives;
- the tests and compiler evidence that support each claim;
- known gaps, unsupported behaviors, and accepted residual risks; and
- the distinction between integrated source, historical validation, deployment,
  configuration, and live activation.

Claims are labeled or written so readers can distinguish repository evidence,
compiler or specification evidence, independently reproduced results,
historical results, and technical inference. The records are rationale and
audit documents, not merely summaries of workstream completion.

## Owner-facing contract index

| Contract | Direct answers | Executive verdict |
| --- | --- | --- |
| Teller | [`receiptMeasurementActive`, explicit clear, and strict `raw_call`](teller.md#direct-answers-to-the-owners-questions) | [Reviewed conclusion](teller.md#executive-verdict) |
| GuardedErc20 | [Why a new guarded nominal vault was selected](guarded-erc20.md#direct-answers-for-the-owner) | [Reviewed conclusion](guarded-erc20.md#executive-verdict) |
| CreditEngine | [Zero value, retained terms, and liquidation implications](credit-engine.md#direct-answers-to-the-owners-questions) | [Reviewed conclusion](credit-engine.md#executive-verdict) |
| Ledger | [`raw_call`, ArbSys knowledge, and architecture alternatives](ledger.md#direct-answers-for-the-owner) | [Reviewed conclusion](ledger.md#executive-verdict) |
| Lootbox | [Per-deployment floor, Base preservation, and Robinhood configuration](lootbox.md#direct-answers-for-the-owner) | [Reviewed conclusion](lootbox.md#executive-verdict) |

## Current owner scope

The following directions control this explanatory package:

- Corrected PR #61 entered `rh` through historical integration ancestor
  `ad831669943ccfe7b9ed57454995dfce51630a66` and is retained by frozen
  baseline `ae0cb49…`. The Deleverage, AuctionHouse, and SwitchboardDelta pages
  bind their rationale to that source; the older import hash is not current
  branch authority, and integration does not imply deployment, configuration,
  activation, or release.
- CCIP workflows are owner-parked and outside the current work program.
- Zero-backing settlement, loss allocation, and bad-debt policy are
  owner-parked for later analysis.
- Sites account/workspace recovery and dashboard deployment are owner-parked.
- Parked subjects are not current Wave 1 work items or blockers. Parking does
  not decide their eventual release disposition.
- H-04 schema v2, H-05 deterministic blocked planning, H-06 candidate-class
  qualification, and M4 proof are integrated for their exact scopes. None is
  final operator, machine, volume, deployment, or release authority.

The two Base migration scripts and three Base migration-history paths touched
by the upstream work remain Base-only provenance outside Robinhood parity. At
the current comparison, the three history paths and the first migration script
differ; the second migration script is byte-identical. `tests/conf_core.py` is
the fifth differing squash-touched path because of independent `rh` branch
evolution. None justifies merging `master` into `rh` or importing Base history.

## Reviewed implementation snapshot

This inventory was regenerated on 28 July 2026 from:

| Ref | Commit | Tree |
| --- | --- | --- |
| `master` comparison point | `91d846e8618fbaf3d8fb6770361b48d542d82a76` | `07e0426d3d0bf5a8599ddd6afed87cecc35e75f2` |
| `rh` reviewed snapshot | `cca60bb85c772c977bb9fb62c1c6c5252c3a1438` | `161fb828f3bbf4cb12596a5dfaf6c9bf1e153381` |

The production-contract comparison for the five reviewed components comes
from:

```text
git diff --numstat master...rh -- \
  contracts/core/Teller.vy \
  contracts/vaults/GuardedErc20.vy \
  contracts/core/CreditEngine.vy \
  contracts/data/Ledger.vy \
  contracts/core/Lootbox.vy
```

This explicit path list reproduces the five reviewed contract deltas. It is
not a discovery proof for every possible contract change in the repository.
The commit and tree above are a dated reviewed snapshot, not a permanent claim
about the future tip of `rh`.

## Changed production contracts

| Contract | Production delta | Why it changed | Current boundary |
| --- | --- | --- | --- |
| [`Teller`](teller.md) | Measures exact token receipt before crediting a deposit | A requested transfer amount is not proof that the vault actually received that amount | Integrated source; deployment and activation remain separate |
| [`GuardedErc20`](guarded-erc20.md) | New generic vault with live-backing and exact-delivery guards | Nominal vault accounting can remain positive after issuer-controlled custody loss | Integrated source; not independently launch-ready |
| [`CreditEngine`](credit-engine.md) | Preserves debt-resolution terms for a nonempty zero-backed position while assigning zero value | Skipping `(asset, 0)` hid unsafe debt by erasing its liquidation and redemption terms | Integrated source; settlement and bad-debt policy are owner-parked |
| [`Ledger`](ledger.md) | Selects native or Arbitrum action-block identity through one immutable source | Robinhood child blocks cannot use inherited `block.number` as the intended same-execution-block identity | Integrated shared source; deployed Base Ledger remains unchanged |
| [`Lootbox`](lootbox.md) | Replaces the Base-specific reward interval floor with an immutable constructor value | One hardcoded Base cadence could not safely represent both Base and Robinhood deployments | Integrated shared source; live deployment and Base convergence remain separate |

Current SHA-256 identities:

| Contract | SHA-256 |
| --- | --- |
| `contracts/core/Teller.vy` | `4afc6ce1ccf21cb65e04ce3c56fedcf60bb79cba8e7dc51fd855a1f1f82bd909` |
| `contracts/vaults/GuardedErc20.vy` | `0fcdb02a0b3adf56ef0fd04397c57ac40325a37c87a32f29979dadc5eaf353ed` |
| `contracts/core/CreditEngine.vy` | `7de649cece6e076b75775bb4ff5f397bf5ffa0a50ccdc462a061ca047b888e3d` |
| `contracts/data/Ledger.vy` | `6bd731a6ce9084de213494ebad09f8e52c782153842708b78f90fa178c06e9e3` |
| `contracts/core/Lootbox.vy` | `669c2857e2402ef0e8f9a508dd6f342426ffbd1affce11dd429e5b5b0129ae65` |

## How the Stock Token changes fit together

The Stock Token containment changes are three different controls at three
different trust boundaries:

```text
Teller
  proves the amount received during this deposit call
      |
      v
GuardedErc20
  proves aggregate backing and exact delivery while it owns custody
      |
      v
CreditEngine
  gives unsafe backing zero value without erasing debt-resolution terms
```

None of the three can replace the others:

- a vault cannot reconstruct Teller's pre-transfer balance after the transfer;
- Teller cannot continuously prove custody after the deposit transaction; and
- CreditEngine should not duplicate token-specific custody reads already owned
  by the vault.

The combined behavior is containment, not complete loss resolution. A
zero-backed position may become eligible for liquidation, but liquidation
entry, auction creation, settlement, collateral delivery, debt reduction, and
bad-debt accounting remain distinct transitions. The later policy transitions
are described for technical accuracy but are owner-parked rather than active
work in this package.

## Shared release boundary

An integrated source change is not proof that:

- the contract is deployed;
- an existing deployment was upgraded;
- a Stock asset or route is enabled;
- the Robinhood constructor/configuration values are final;
- a zero-backed auction can settle;
- unrecoverable debt is moved into bad-debt accounting; or
- an existing Base deployment changed.

Any later deployment or activation claim still requires the exact
owner-approved configuration, artifact binding, applicable composed-route
evidence, monitoring, and release authority. This statement does not reopen
the parked settlement, loss-allocation, bad-debt, or CCIP subjects. The
Ledger and Lootbox records have their own deployment and live-version
boundaries.

## Supporting contracts not treated as production components

The `master...rh` contract diff also contains test and probe contracts:

- `contracts/mock/MockProbeErc20.vy`;
- `contracts/mock/MockStockTokenControls.vy`;
- `contracts/testing/ActionBlockIdentityProbe.vy`; and
- `contracts/testing/StockTokenTransferProbe.vy`.

They support adversarial or environment validation. They are intentionally not
given production-change rationale records in this directory.

## Relationship to detailed records

These files summarize behavior at the reviewed implementation snapshot. They
do not replace the
controlling approval, implementation, validation, migration, or release
records elsewhere in `docs/chains/rh/`. Each contract page links its primary
evidence and records important residual risks, recommendations, parked work,
and deployment or release gates.
