# Small PriceDesk gas change

Based on `master` at `1ede38351e6da918806dff70d34b2066bf8cde8c`, independently of
PRs #231 and #232. This is a contract implementation candidate, not a deployment.

## Contract changes

- Replace the hardcoded 250,000 quote / 150,000 snapshot caps with two positive
  constructor immutables, exposed by `PRICE_SOURCE_PRICE_GAS()` and
  `PRICE_SOURCE_SNAPSHOT_GAS()`.
- Append `_priceSourcePriceGas` and `_priceSourceSnapshotGas` after the existing
  five constructor arguments. The feed-check cap remains 75,000.
- Route Teller's Curve reference-pool call through
  `PriceDesk.addGreenRefPoolSnapshot(CURVE_PRICES_ID)`. Only HQ's current Teller
  can call the relay. PriceDesk resolves its own source registry and uses the
  same immutable snapshot allowance as generic asset snapshots.
- Preserve low-level success semantics: absent/disabled routes and successful
  False/no-op or empty replies are successful. A reverted/exhausted source call
  returns False and Teller emits its existing `CurveSnapshotFailed` event.

Quote selection, strict/non-strict behavior, source failure isolation, freshness,
token scales, and conversion rounding retain the master implementation. There
are no per-source overrides, governance setters, maximum-budget parameter, or
caller-funding checks.

## Constructor values and limits

Existing local fixtures explicitly retain 250,000 / 150,000 to exercise the
previous pricing limits. Larger-allowance regressions use 1,500,000 as a test
input, not an approved Base deployment value. Quote and snapshot allowances can
be selected independently; changing them later requires another deployment.

The relay replaces Teller's former independent 500,000 cap. Its actual allowance
is now the supplied snapshot argument, including when that value is below
500,000. Select and verify this value for both snapshot paths before deployment.

A larger allowance does not supply more transaction gas or guarantee completion
of nested fallback routes. The previous fail-soft underfunding behavior remains:
a caller can complete while an attempted snapshot is skipped. Tests explicitly
preserve this behavior; this patch does not implement PR #232's funding policy.

## Deployment follow-up

Measure the affected deployed source/dependency routes and full user transactions
before selecting final constructor values. Include cold/mature state, nested and
repeated source failures, and actual estimated/submitted gas compared with a
generous limit. Check due snapshot writes and fallback results, not just receipts.

A replacement desk needs its source IDs, registry settings, and token scales
initialized and verified. Activate compatible PriceDesk at HQ slot 7 before the
relay Teller at slot 17; reverse that dependency order for rollback. Historical
migrations/manifests are unchanged and retain their historical constructor ABIs.
A new deployment must pass all seven arguments and use a separately reviewed
current migration rather than replaying an old five-argument migration.

## Local validation

After updating the two intentional runtime pins and the callback mock's relay
interface, all **653 distinct selected tests passed**. The selection covers new
constructor/relay cases, existing PriceDesk isolation and token-scale cases,
Teller flows and reentrancy/accounting proofs, Curve and Aero composition,
configuration/ABI checks, and gas boundaries. No full suite was run.

The 33-case gas/integration run passed, including all 19 new allowance/relay
cases, full-capacity Curve housekeeping, nested source failure, and runtime
checks. All 59 ABI exports match their current sources. Four existing cases
were deselected in the ordinary regression command by its marker filter; the
three Curve gas cases ran explicitly in the gas selection.

Complete deployed runtime with Vyper 0.4.3 / Titanoboa 0.2.7:

| Contract | Before | After | EIP-170 headroom |
| --- | ---: | ---: | ---: |
| PriceDesk | 17,742 | 18,156 | 6,420 |
| Teller | 24,552 | 24,488 | 88 |

The existing 150,000-gas complete Curve-housekeeping ceiling passed at 70,719
gas in its local fixture. These are local implementation results, not Base
deployment qualification. The contract diff changes only PriceDesk's constructor
and immutable declarations, adds its relay, and replaces Teller's Curve call.

## Base retained-vault measurements

[The pinned evidence](pricedesk-simple-gas-evidence.json) uses this PR's exact
PriceDesk source at `0c43eaf53b3a9fd33c90db244b3e530b2c5f1390`, without #232, and the
recorded Base source registry. At block **51,614,967** the nested price route for
`0x99e65176F7FA8743E3fbaEF277d1Da448e361367` behaves as follows. Measurements start
cold; snapshot cases advance local time until a write is due and verify the
stored snapshot, rather than accepting a successful outer receipt.

| Per-source allowance | Strict quote | Due generic snapshot |
| --- | --- | --- |
| 1,500,000 | Reverts | Returns False; no stored update |
| 2,000,000 | Succeeds | Returns True; stored update advances |
| 3,000,000 | Succeeds | Returns True; stored update advances |
| 4,000,000 | Succeeds | Returns True; stored update advances |
| 6,000,000 | Succeeds | Returns True; stored update advances |

A successful complete PriceDesk quote consumes **1,749,770 execution gas**; a
successful due snapshot consumes **1,619,441**. These enclosing-call measurements
are not exact source-cap thresholds. **3M quote / 3M snapshot** is the measured
recommendation with margin for these routes, not a universal sufficiency bound.
The contract still takes both constructor arguments explicitly. No deployment
configuration is changed here.

The combined #233 + #238 fork also passes the previously failing retained
RipeGov holder's reward claim (configured cash/stake split and full restaking),
strict valuation of four mixed holders, all 26 original stress-asset price
routes, and four retained settlement examples. Claims consume **5.45M–5.48M** and
settlements **6.54M–8.45M** execution gas. All pass with **15.95M supplied execution
gas**. Several settlements reject 12.8M supplied gas because #233 deliberately
requires enough remaining gas for its full 8M legacy read. Consumed gas alone
therefore cannot select the transaction limit. Details and negative funding
results live in #233's retained-governance evidence.

Five additional local cases cover one, two and three consecutive 3M source
exhaustions before successful fallback, and both snapshot entry points with a
source requiring more than 1.5M. The underfunded calls return False without
writing; properly funded calls write. The actual Curve/Teller tests authorize
PriceDesk as the new caller, and the repayment price mock implements the relay.
Those fixture updates resolve the three failures present on the incoming PR
head without changing the protocol implementation.

Reproduce the source measurement from #238 with a read-only copy of the #233
manifest (the ordinary master manifest lacks the recorded candidate setup):

```sh
PYTHONPATH=. python tests/diagnostics/pricedesk_gas_probe.py \
  --manifest /path/to/pr233/migration_history/base-mainnet/v1/current-manifest.json \
  --block 51614967 --output /tmp/pricedesk-base-gas.json
```

The probe refuses to overwrite output; omitting `--block` selects a finalized
block and records its hash. Its RPC transport permits reads only. Candidate
configuration and code substitutions occur solely inside Boa; no live
transactions are sent. Runtime/source/manifest hashes and all tested source
identities are in the evidence. Inner reverted frames can be expected feature
probes; the top-level `passed` flag and state assertions determine each result.

This does not qualify the historical 26-claim settlement batch, production RPC
estimation, external keeper behavior or deployment wiring. Fail-soft snapshot
underfunding remains part of #238's deliberately small design. The fork checks
actual Undy due writes; Curve relay permissions, due writes, repeated block
numbers and full-capacity gas bounds are exercised by local contract tests.

Follow-up validation: **221 selected cases passed** (96 allowance/isolation/route
cases, 116 repayment/Curve cases, and 9 runtime/source-count/hygiene checks).
The Curve selection used the ordinary marker filter (28 cases deselected);
the separate 96-case selection explicitly included its gas cases. ABI export
validation still matches all **59** outputs. This is focused validation, not a
new full-suite claim.
