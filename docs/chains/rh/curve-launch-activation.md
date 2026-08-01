# Robinhood Curve launch activation authority

**Status:** current bounded source-authority candidate

**Candidate baseline:** commit `5f5d22b7ee78cbb904c4fe3c6e46599c330c4353`, tree `7454b5456ebb6cd02d716a64b408629ab501629e`

**Lifecycle effect:** configuration source and validation only; no deployment, migration execution, pool creation, funding, registration, production configuration, activation, or release

This decision supersedes every current-facing statement that Curve is absent
at launch, PriceDesk ID 2 is empty, or Curve is exclusively a
Profile 2 component. The current synthesis explicitly marks the older
hash-bound qualification reports as historical for this topology; their bytes
remain preserved as evidence.

## Selected launch boundary

| Surface | Current authority |
| --- | --- |
| PriceDesk registry | ID 1 `ChainlinkPrices`; ID 2 `CurvePrices`; ID 3 `BlueChipYieldPrices`; IDs 4 and 5 empty |
| PriceDesk priorities | Exactly `[1, 3]` |
| Curve-configured asset | GREEN only |
| GREEN route | GREEN → Curve GREEN/USDG pool → PriceDesk USDG lookup → Chainlink USDG/USD feed |
| USDG | Chainlink-only; no Curve USDG feed |
| Production contract | Existing `contracts/priceSources/CurvePrices.vy`, unchanged |

The ordering is mandatory because `AddressRegistry` assigns IDs sequentially.
There is no sparse-slot reservation mechanism. A missing Curve registration,
a placeholder, or registering BlueChipYield immediately after Chainlink would
give BlueChipYield ID 2 and fails the topology gate.

## Human-readable value authority

`config/BluePrint.py` is the sole authority for Curve identities, topology,
constructor bindings, pool candidates, ownership, provenance, resolution
state, explicit inactive capabilities, and deployment-produced outputs. The
canonical rows are `ROBINHOOD_CURVE_LAUNCH_INPUTS` and the derived profile
view is `CURVE_PARAMS["robinhood"]`.

`contracts/config/DefaultsRobinhood.vy` remains the source for readable
protocol defaults, including priority IDs `[1, 3]`.
`config/robinhood-parameters.json` remains mechanically derived evidence; the
Curve launch rows are not copied into JSON as another value surface.

The official Curve deployment repository identifies Robinhood chain ID 4663,
the AddressProvider, and its registry/factory bindings. The repository also
pins the Curve Lite source used by the StableSwapNG factory. Those repository
facts were checked against:

- [curve-core Robinhood production deployment](https://github.com/curvefi/curve-core/blob/6222dda9959091db94d61f6d6378234a624cdd66/deployments/prod/robinhood.yaml)
- [curve-core AddressProvider IDs](https://github.com/curvefi/curve-core/blob/6222dda9959091db94d61f6d6378234a624cdd66/scripts/deploy/constants.py)
- [curve-core AddressProvider registration](https://github.com/curvefi/curve-core/blob/6222dda9959091db94d61f6d6378234a624cdd66/scripts/deploy/registries/address_provider.py)
- [pinned Curve Lite StableSwapNG factory](https://github.com/curvefi/curve-lite/blob/5a9e1ab34c1319de69b987900d859ad2e965d0e2/contracts/amm/stableswap/factory/factory_v_100.vy)

Repository verification is not a live-chain observation. The five selected
Curve identities therefore remain `selected_external_fact_unverified` until
the later owner-bound H-07/H-08/H-09 evidence closes them.

## Pool candidate and blockers

The selected research candidate is StableSwapNG with coin 0 USDG, coin 1
GREEN, decimals `(6, 18)`, `A=100`, `fee=4_000_000`, off-peg fee multiplier
`20_000_000_000`, and `ma_exp_time=600`. `ma_exp_time=866` is only an
alternative test vector. None of these research values is an owner approval.

The factory uses `create_from_blueprint` without a salt, so the pool address is
a CREATE-derived deployment output. It is intentionally symbolic. The
following remain typed blockers:

- live observations of the selected AddressProvider and IDs 7, 11, 12, and 13;
- owner approval of coin order, decimals, A, fee, off-peg multiplier, and
  `ma_exp_time=600`;
- pool name and symbol;
- the deployment-produced pool address and production observation;
- production liquidity amount, funding source, custodian, approving account,
  minimum minted LP, slippage limit, withdrawal authority, and minimum
  retained liquidity.

The canonical readiness result is `deployment_ready=false` with 80 blockers:
the remaining 57 non-Curve blockers plus 23 Curve-specific typed blockers.
Missing blockers do not
prevent deterministic source, validation, H-09 safe-default, or migration
interface work; they do prevent executable deployment use.

## Explicitly inactive capabilities

The launch candidate does not configure or activate:

- a Curve feed for USDG or Curve authority for the PSM;
- GREEN/USDG LP or RIPE/WETH LP collateral/admission;
- Curve LP valuation or either LP as an oracle;
- Curve-driven dynamic rates;
- the GREEN reference-pool configuration or Teller snapshots;
- Endaoment Curve stabilization;
- any Stock pricing route; or
- any Uniswap accounting or pricing route.

With no GREEN reference-pool configuration, `getCurrentGreenPoolStatus()` is
zero, so CreditEngine retains the named base/static rate. Teller still resolves
ID 2 and calls `addGreenRefPoolSnapshot()`, but the real `CurvePrices` call
returns false without pool access and is inert. Endaoment reads an empty
stabilizer configuration and remains inactive.

## Pricing and failure behavior

For GREEN, `CurvePrices` reads StableSwapNG `price_oracle(0)`. Because GREEN is
coin 1, it asks PriceDesk for coin 0 USDG with non-raising mode and multiplies
the Chainlink USDG price by the Curve oracle ratio. USDG has no Curve feed, so
the nested lookup terminates at Chainlink and cannot recurse under the
canonical configuration.

A configured GREEN feed with a zero pool oracle, zero/stale Chainlink result,
or missing USDG evidence returns zero in non-raising PriceDesk mode and raises
`has price config, no price` in raising mode. A reverting or ABI-incompatible
pool reverts the composed read; it still fails closed and cannot fabricate a
price. An uninitialized Curve feed returns `(0, false)`.

## Incident response

`CurvePrices.pause(true)` blocks feed/reference-pool configuration changes and
makes snapshot addition return false. It does not stop ordinary view price
reads. Therefore pause is a configuration/snapshot control, not removal of
GREEN pricing authority.

When Curve pricing authority must be removed:

1. Pause `CurvePrices` to stop configuration and snapshot mutation.
2. Start and confirm PriceDesk ID 2 disable through the reviewed governance and
   registry timelock.
3. Confirm ID 2 is zero, GREEN returns zero in both PriceDesk modes when no
   other approved GREEN source exists, and USDG still prices through Chainlink.
4. Repair the pool/feed dependency while ID 2 remains disabled.
5. Verify pool identity, registered handler/factory, exact coins and decimals,
   nonzero oracle response, Chainlink USDG freshness, no Curve USDG feed, empty
   reference-pool configuration, and priorities `[1, 3]`.
6. Unpause only after those checks pass.
7. Start and confirm the governed ID 2 address update, then repeat GREEN/USDG,
   safe/unsafe, topology, and inactive-capability checks.

Do not use a manual constant, a generic test source, a non-Curve placeholder,
or BlueChipYield at ID 2 as recovery. Pool funding or custody recovery is a
separate operational decision and is not implied by oracle re-enable.

## Remaining lifecycle gates

Configuration consistency, focused tests, H-09 safe-default behavior, and an
independent review do not close external facts or owner inputs. H-07 artifacts,
H-08 topology, separately authorized H-09 archive-fork qualification, H-10
live rehearsal, deployment, production configuration, activation, and release
remain separate gates.
