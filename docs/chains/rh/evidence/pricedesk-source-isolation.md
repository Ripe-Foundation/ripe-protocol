# PriceDesk source-isolation and admission record

**Decision:** RH-D042 — PriceDesk source isolation uses bounded policy-only
admission

**Candidate date:** 15 August 2026

**Lifecycle:** source, test, artifact, and preflight candidate only; no
deployment, registration, configuration, activation, or release authority

## Controlling policy

PriceDesk gives each external price-source call a distinct compile-time gas
allowance:

| Channel | Allowance |
| --- | ---: |
| `getPriceAndHasFeed` | 250,000 gas |
| `hasPriceFeed` | 75,000 gas |
| `addPriceSnapshot` | 150,000 gas |

The calls use `raw_call(..., revert_on_failure=False)` and require exact return
lengths and canonical Boolean words. A revert, allowance exhaustion, truncated
or oversized response, or noncanonical Boolean is a source failure. PriceDesk
continues to later healthy sources. Strict price callers fail closed only when
no healthy source establishes a price.

EIP-150 still applies: the callee receives the lesser of the requested
allowance and the caller's remaining gas after the one-sixty-fourth reserve.
Qualification therefore uses outer transaction limits high enough that the
explicit allowance is the binding boundary. That retained caller gas is part
of the availability design: one hostile source cannot consume the caller's
entire remaining budget before PriceDesk attempts a fallback.

The allowances are constants in `PriceDesk.vy`. They are not normal governance
configuration. Changing any allowance changes the PriceDesk artifact and
requires a new artifact review, deployment, registry-pointer migration, and
activation package.

## Measurement and selected margin

The focused Boa tests compile the pinned Vyper 0.4.3 source, isolate PriceDesk,
register real production sources or adversarial raw-return/gas-burning mocks,
and measure top-level local-EVM gas. Stipend-sweep variants change only the
single PriceDesk allowance under test. The evidence covers:

- flat Chainlink, Pyth, Stork, RedStone, and wsuperOETHb paths;
- BlueChip and Undy feeds at 25 snapshots for price, feed-presence, and
  snapshot channels;
- a four-underlying flat-source Curve route in registry position 10;
- the final healthy source behind nine allowance-exhausting sources; and
- the 5-vault by 15-asset, 75-position valuation envelope; and
- the separate StabilityPool 20-active-claim / 15-maintenance-batch ceiling.

For the supported four-underlying flat Curve topology, a 10,000-gas-resolution
sweep fails at 90,000 and first succeeds at 100,000 forwarded gas. The selected
250,000 price allowance is 2.5 times that upper boundary, retaining at least
150,000 gas or 150% headroom. The highest supported real-source top-level feed
check measured 27,229 gas, so 75,000 retains 47,771 gas or 175% headroom even
before subtracting PriceDesk overhead. The highest real snapshot route measured
56,113 gas, so 150,000 retains 93,887 gas or 167% headroom on the same
conservative comparison. These are channel-specific measurements; the smaller
allowances are not inferred from the price-channel result.

The unsupported four-coin Curve-over-max-25-snapshot-BlueChip graph fails at
the selected 250,000 allowance, still fails at 350,000, and first succeeds at
400,000 in a 50,000-gas-resolution sweep. That is an admission boundary, not a
reason to enlarge the general allowance.

The affected StabilityPool node measured the exact PriceDesk parent and head
under the same isolated environment:

| Ceiling case | Parent `f563cbb` | PriceDesk head | Delta | New ceiling |
| --- | ---: | ---: | ---: | ---: |
| Deposit | 508,587 | 513,480 | +4,893 | 530,000 |
| Withdrawal | 446,932 | 451,825 | +4,893 | 470,000 |

The repeated 4,893-gas delta is the guarded PriceDesk source-call path. Removing
that work would remove the isolation behavior being remediated, and no cheaper
equivalent preserving the exact fallback and response-validation semantics was
identified. Under the minimum-production-change rule, the consumer ceiling is
therefore intentionally rebaselined rather than weakening PriceDesk.

Those ceilings preserve approximately 3.2% and 4.0% local-EVM headroom. A
later `claimMany` assertion already measured 7,013,069 at the parent against a
7,000,000 ceiling, proving that failure was pre-existing. Head measures
7,089,959; its separate 7,250,000 ceiling retains about 2.3% headroom. That
multi-claim path and baseline debt remain distinct from the 4,893-gas single
deposit/withdrawal delta.

The broader 5-vault by 15-asset scan remains a composition residual rather than
a per-source stipend failure. The conservative 75-position measurements are
approximately 9.59 million gas with honest sources, 21.23 million with one
hostile source, and 51.57 million with two hostile sources. A separate
one-hostile composition that charges the full hostile allowance plus the
highest measured honest lookup is approximately 28.34 million before
surrounding overhead. The two-hostile case exceeds a 32-million transaction
ceiling. The manifest therefore freezes the selected vault/asset envelope and
requires requalification; the stipend does not promise arbitrary composition
executability.

## Admitted topology and fail-closed preflight

The selected Robinhood activation plan is exact:

1. PriceDesk ID 1: `ChainlinkPrices`;
2. PriceDesk ID 2: `CurvePrices`;
3. PriceDesk ID 3: `BlueChipYieldPrices` candidate;
4. priority order `[1, 2]`; and
5. one Curve feed for GREEN through the GREEN/USDG pool, with USDG resolving
   through Chainlink and no snapshot-backed underlying.

`config/robinhood-price-source-admission.json` binds that list, order, route,
the selected three-source state, the S=10 qualification maximum, four Curve
underlyings, 25 snapshot observations, five vaults by 15 assets (75 valuation
positions), 20 active claim assets, and a 15-asset maintenance batch. Migration
0011 validates the manifest and exact graph before it produces Safe calldata.
Negative tests reject source growth, priority reordering, envelope growth, and
Curve-over-BlueChip, Curve-over-Undy, or generic Curve-over-snapshot graphs.

This remains deliberately policy-only under the minimum-production-change
decision. There is no on-chain source-count or topology-aware admission guard.
Governance can bypass the generator and create an availability-breaking graph.
That residual is explicitly accepted only with the required manifest review,
preflight, monitoring, and disable response. An on-chain guard is a separately
scoped contract change and is not authorized by this record.

## Reopen conditions

Requalification is mandatory before any change to:

- an allowance or the PriceDesk source/compiler/dependency identity;
- registered-source count, identity, order, or priority list;
- a source implementation, external dependency, or return shape;
- a Curve pool, underlying count, or underlying price-source graph;
- snapshot capacity or snapshot-source composition;
- the 75-position vault/asset ceiling or another affected consumer bound; or
- the outer transaction-gas assumptions used by the S=10 hostile-source test.

## Monitoring and disable procedure

Operators must monitor per-source failure/malformed-response counts, fallback
frequency, strict no-price reverts, transaction gas, snapshot success, and
allowance-exhaustion simulations. Any sustained new fallback, malformed
response, or near-allowance behavior pauses activation of the affected feed and
opens incident review.

For an active failing source, first remove its ID from MissionControl priority
ordering so a healthy source is tried first. Prepare the PriceDesk
`startAddressDisableInRegistry(id)` action, observe the registry timelock and
continued fallback health, then confirm with
`confirmAddressDisableInRegistry(id)`. If no healthy price remains, pause the
affected product instead of forcing a zero or raising an allowance. Restoring
or replacing the source requires fresh artifact, topology, gas, and consumer
qualification under the reopen rules above.

## Reproduction scope

The focused gas command is:

```sh
python -m pytest -m gas \
  tests/registries/test_price_desk_gas.py \
  tests/priceSources/blueChip/test_bluechip_local.py
```

It collects seven PriceDesk tests and one BlueChip benchmark. It is not the
repository-wide 18-node gas collection, the unmarked StabilityPool consumer
test, or a full repository-suite run. The affected consumer is reproduced
separately with:

```sh
python -m pytest -q \
  tests/vaults/modules/test_stab_vault_hardening.py::test_value_and_maintenance_gas_remain_bounded_at_active_claim_ceiling
```
