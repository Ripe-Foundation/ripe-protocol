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
