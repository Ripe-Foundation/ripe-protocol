# PriceDesk source-isolation and admission record

**Decision:** RH-D042 — PriceDesk source isolation uses bounded policy-only
admission

**Candidate date:** 15 August 2026

**Authority:** proposed and pending explicit owner approval. No stable approval
provenance currently establishes acceptance of the policy-only enforcement
boundary or its operating residuals.

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

- direct Chainlink, Pyth, and Stork adapters plus selected nested RedStone and
  wrapped-yield conversion paths;
- BlueChip Morpho, selected Morpho V2, and Undy feeds at 25 snapshots for price, feed-presence, and
  snapshot channels;
- a four-underlying Curve route over direct underlying sources in registry
  position 10, distinct from recursive and snapshot-backed compositions;
- the final healthy source behind nine allowance-exhausting sources; and
- the separate StabilityPool 20-active-claim / 15-maintenance-batch ceiling.

The focused tests do not execute a 5-vault by 15-asset borrower scan. The
75-position figures below are explicitly derived projections from committed
per-lookup measurements and selected stipends.

For the supported four-underlying direct-source Curve topology, a 10,000-gas-resolution
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

The affected StabilityPool node was rerun and instrumented on exact current
target `e7b6eeab768a009469a38a7ce8a35bb7e8d8f4bc` and on the PriceDesk head
under isolated local-EVM environments. The current target reproduces the
earlier `348f8c1` values exactly:

| Ceiling case | Parent `e7b6eea` | PriceDesk head | Delta | New ceiling |
| --- | ---: | ---: | ---: | ---: |
| Deposit | 508,587 | 513,480 | +4,893 | 530,000 |
| Withdrawal | 446,932 | 451,825 | +4,893 | 470,000 |

The parent rerun used an instrumentation-only print addition to the test; the
contracts and execution path were exact `e7b6eea`. The earlier historical
`f563cbb` measurement reference is superseded; no tree-equivalence claim is
made for it.

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

The broader 5-vault by 15-asset envelope remains a composition residual rather
than a per-source stipend failure. No committed test executes that borrower-wide
scan. The reproducible arithmetic projections are:

- honest: `127,922 × 75 = 9,594,150` gas;
- measured one-hostile lookup: `283,132 × 75 = 21,234,900` gas;
- full selected hostile allowance plus the measured honest lookup:
  `(250,000 + 127,922) × 75 = 28,344,150` gas; and
- two full hostile allowances plus the measured honest lookup:
  `(2 × 250,000 + 127,922) × 75 = 47,094,150` gas before additional
  PriceDesk and borrower-loop overhead.

The previously stated 51.57-million two-hostile value is removed because no
committed harness or preserved formula reproduced it. These projections are not
top-level transaction measurements; the two-hostile lower-bound projection
already exceeds a 32-million transaction ceiling. The manifest therefore
freezes the selected vault/asset envelope and requires requalification; the
stipend does not promise arbitrary composition executability.

## Admitted topology and fail-closed preflight

The selected Robinhood activation plan is exact:

1. PriceDesk ID 1: `ChainlinkPrices`;
2. PriceDesk ID 2: `CurvePrices`;
3. PriceDesk ID 3: `BlueChipYieldPrices` candidate;
4. priority order `[1, 2]`; and
5. one Curve feed for GREEN through the GREEN/USDG pool, with USDG resolving
   through Chainlink and no snapshot-backed underlying;
6. the complete enumerated `CurvePrices.getPricedAssets()` result is exactly
   `[GREEN]`; and
7. sGREEN is an explicit derived route through GREEN plus
   `SavingsGreen.convertToAssets`, not a second stored Curve configuration.

`config/robinhood-price-source-admission.json` binds that list, order, complete
stored/derived route set, and qualification envelope. Its controls are not all
described as live-bound:

| Field | Control classification |
| --- | --- |
| 250k / 75k / 150k allowances | exact active PriceDesk deployed-runtime hash |
| selected three-source slots and priorities | live state readback |
| five vaults, 15 assets, and derived 75 positions | live MissionControl readback |
| S=10 maximum | committed-test qualification only |
| four Curve underlyings | prospective Curve source-artifact bound; selected live routes are read in full |
| 25 snapshot observations | prospective BlueChip source-artifact bound and committed test |
| 20 active claims / 15 maintenance batch | committed StabilityPool test qualification only |

The current Robinhood manifest points RipeHq ID 7 to PriceDesk
`0x694a1F8525483cFf3142770395Ec310bf954b0C0`. Its embedded PriceDesk source hash
is `7611139b85f93d042fcf7ddf964052909166b4bd98bdd4b7ee8c685c54641d2a`, not the
hardened source hash
`7fd7e8eedd883a10ee7a225cb666896324d7b9b47de3a136175f62e00267561c`.
Attaching the current ABI to that address is not runtime proof. Migrations 0011
and 0012 now compare the live deployed bytes with the exact governed hardened
runtime size/hash and verify the RipeHq pointer before any promotion,
deployment, finalization, execution, or calldata generation. The current
record therefore fails closed.

The activation path is deliberately deferred: 0011 and 0012 emit no slot-3
start or confirmation calldata and perform no BlueChip promotion. A separately
governed PriceDesk replacement must deploy the exact hardened artifact,
reconstruct and verify Chainlink/Curve registry IDs, descriptions, priorities,
governance, and timelocks, update RipeHq ID 7, and repeat the runtime check.
Activation tooling must then either atomically assert runtime, complete graph,
empty slot/resulting ID, and confirmation, or run a fresh post-timelock
preflight in an exclusive Safe window with a named operator and tested
rollback/disable steps. Until that package and owner acceptance exist, there is
no preflight-to-activation race because this repository produces no actionable
activation call.

The live observer enumerates `getPricedAssets()`, reads every returned
`curveConfig`, resolves every non-target underlying against all current sources
and a pending candidate when supplied, and checks the derived sGREEN behavior.
Negative migration tests reject source count/address drift, priority
reordering, wrong pool, changed/additional underlyings, missing USDG Chainlink
resolution, envelope growth, extra/reordered/duplicate Curve assets, missing
sGREEN derivation, and extra Curve-over-BlueChip, Curve-over-Undy, generic
snapshot-backed, or otherwise-direct routes. Each negative proves no promotion,
candidate deployment, finalization, execution, or slot-3 calldata occurs.

This candidate proposes policy-only enforcement under the
minimum-production-change direction. There is no on-chain source-count or
topology-aware admission guard. Governance can bypass the generator and create
an availability-breaking graph. That residual is not owner-approved on the
current record. Before approval, an identified owner must explicitly accept the
policy-only boundary, exact stipends, selected topology and envelope, bypass
ability, monitoring/disable requirements, and composition residual, with stable
approval provenance linked here. An on-chain guard is a separately scoped
contract change and is not authorized by this record.

The selected Morpho V2 local qualification uses the Morpho V2 protocol flag,
fills all 25 observations, places BlueChip at slot 3 behind priorities `[1,2]`,
and exercises its nested underlying PriceDesk lookup for price, feed presence,
and snapshot update. The measured top-level local-EVM values are 74,625 gas for
price, 4,515 for feed presence, and 18,761 for registry-mediated snapshot
update, each below its respective stipend. Before any future production
activation, the exact selected external Morpho V2 factory and representative
vault must repeat this qualification on a fork; the local mock result is not
external-factory proof.

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

It collects eight PriceDesk tests and one BlueChip benchmark. It is not the
repository-wide gas collection, the unmarked StabilityPool consumer
test, or a full repository-suite run. The affected consumer is reproduced
separately with:

```sh
python -m pytest -q \
  tests/vaults/modules/test_stab_vault_hardening.py::test_value_and_maintenance_gas_remain_bounded_at_active_claim_ceiling
```

The manifest, exact-runtime binding, complete live-graph observer, deferred
migration gates, and all drift/no-write negatives are reproduced with:

```sh
python -m pytest -q \
  tests/config/test_price_source_admission.py \
  tests/deployment/test_pr67_deployment_migrations.py
```
