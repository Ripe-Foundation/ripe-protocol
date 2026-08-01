# Robinhood LP launch-admission qualification

**Decision date:** 1 August 2026
**Authority baseline:** commit
`5f5d22b7ee78cbb904c4fe3c6e46599c330c4353`, tree
`7454b5456ebb6cd02d716a64b408629ab501629e`
**Scope:** GREEN/USDG Curve LP and RIPE/WETH Uniswap V2 LP launch
qualification and repository representation only

## Decision

The owner explicitly reopened the prior “neither LP admitted at launch”
decision. This qualification evaluated each LP from the frozen source and did
not use the prior decision as a stop condition. The negative results follow
from missing verified facts, missing owner controls, and unresolved shared-path
safety properties—not merely from the old policy.

The independent outcomes are:

| Candidate | Protocol launch admission | Non-protocol launch role | Verdict |
| --- | --- | --- | --- |
| GREEN/USDG Curve LP | No | The pool and GREEN pricing route are selected launch work; the LP token itself has no protocol role | **Not launch-admissible** |
| RIPE/WETH Uniswap V2 LP | No | Conditional externally held V2 liquidity/monitoring canary only | **Not launch-admissible as a Ripe asset** |

The RIPE/WETH canary verdict is not pool-creation, funding, custody,
registration, configuration, deployment, or activation authority. It becomes
operationally actionable only after its exact external and owner inputs are
approved in a separately authorized lifecycle phase.

No production Vyper, interface, ABI, `DefaultsRobinhood` constructor, artifact
expectation, executable migration, or configuration-authority change is
warranted. Both LP rows remain omitted from `DefaultsRobinhood`; PriceDesk
priority IDs remain `[1, 3]`; unchanged `CurvePrices` is selected at PriceDesk
slot 2 for GREEN only; and the Uniswap prototype remains interface-inert. Pool
deployment and GREEN pricing selection do not admit the GREEN/USDG LP token as
collateral or another valuation-dependent Ripe asset.

## Alternatives reconsidered

| Alternative | Independent result |
| --- | --- |
| Zero LTV | Necessary for no borrowing power, but insufficient: it does not prevent trusted-department deposits or every valuation-dependent shared route. |
| Deposit-only / ordinary-only | The desired protocol role, but current shared contracts have no accepted per-asset switch or composed proof that excludes trusted and valuation-dependent routes. |
| Disabled by default | Current omission is the safe representation. Adding a dormant LP row would not supply identity, decimals, limits, custody, or negative-route proof and therefore would not make either LP admissible. |
| Observation-only | Acceptable only outside LP-token admission: the GREEN/USDG pool is selected for bounded GREEN launch pricing, while its LP token remains excluded; the RIPE/WETH monitor remains unregistered and PriceDesk-inert. |
| Externally held canary | Conditionally supportable only for RIPE/WETH after separate owner and external closure. It is not a Ripe asset and cannot use PSM reserves. |
| Separate later activation | Possible only after an explicit future reopening closes the owner, external, implementation, fork, and security blockers below. It grants no current lifecycle authority. |

## Why zero LTV is insufficient

The intended safe template is still exact and conservative: Simple ERC-20
vault ID 3, explicit `ltv=0`, all other debt fields zero, no LP price source,
no liquidation or stability route, no rewards/points allocation, and ordinary
deposit/withdraw only. The frozen contracts do prove two important properties:

- `CreditEngine._getUserBorrowTerms` skips an asset before price lookup when
  `ltv == 0`, so the LP cannot contribute borrowing power; and
- `CreditEngine.getMaxWithdrawableForAsset` returns the maximum for `ltv == 0`
  before price lookup, so the zero-LTV asset does not trap an ordinary
  withdrawal solely because it lacks a price.

Those properties do not satisfy the full admission contract:

1. `Teller.depositFromTrusted` accepts any supported asset from a valid Ripe
   department. `TellerUtils.validateOnDeposit` also bypasses per-user and
   global deposit limits for Ripe-department depositors. Current asset config
   has no per-asset ordinary-only switch.
2. Teller calls `Lootbox.updateDepositPoints` and
   `PriceDesk.addPriceSnapshot` after deposits and withdrawals. Lootbox reads
   token decimals and, when staker allocation is zero, refreshes the asset USD
   value. A missing feed currently yields zero, but the valuation path is
   reached.
3. `Deleverage.deleverageWithVolAssets` treats a supported asset with both
   liquidation flags false as a volatile transfer candidate and enters the
   price-dependent collateral transfer path. `swapCollateral` can also name a
   supported LP and requires a raising price lookup.

Making either LP supported would therefore expose trusted-deposit and
valuation-dependent paths even though the ordinary credit calculation remains
zero-LTV. Preventing that requires new asset-specific policy shared across
Teller/TellerUtils, Lootbox, Deleverage, liquidation/accounting consumers, and
their configuration/interfaces. That is not a narrow LP configuration change.
This task also expressly preserves Deleverage unchanged. The honest
contract-change verdict is therefore **no production contract change and no
LP admission**.

## GREEN/USDG Curve LP verdict

### Bound facts and candidate vector

- Robinhood chain ID: `4663`.
- Official Curve AddressProvider:
  `0x4574921eb950d3Fd5B01562162EC566Cb8bc3648`.
- Official StableSwapNG factory:
  `0x8271e06E5887FE5ba05234f5315c19f3Ec90E8aD`.
- Canonical USDG:
  `0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168`.
- Candidate pool: two-coin StableSwapNG plain pool, USDG coin 0 and GREEN coin
  1; the pool is also the LP token.
- Minimum-change vector: `A=100`, `fee=4_000_000`,
  `offpeg_fee_multiplier=20_000_000_000`, `ma_exp_time=600`, implementation
  index 0 after live getter proof, asset types `[0, 0]`, zero rate oracles.
- Explicit alternatives: `ma_exp_time=866` and stabilizer adjustment `7_500`
  bps. They are test vectors, not approved substitutions.
- Preferred stabilizer candidate: `5_000` bps.
- Preferred staleness candidate: `7_200` L1-derived number units.
- Rejected staleness values: `0` and Base-derived `43_200`.

The 100 USDG + 100 GREEN seed remains a deterministic fork vector only. It is
not a production liquidity amount or funding authority. The pool address is a
`CREATE` result and depends on the factory nonce/order; parameters alone do
not determine it.

### Blocking facts

- final GREEN identity is deployment-produced and absent;
- exact pool/LP identity, implementation/runtime, creation order and token
  getters are absent;
- LP decimals are not accepted from convention without the exact runtime
  getter;
- USDG proxy/implementation/layout and the candidate slots 1/2 overlay remain
  fork-only proof inputs, never production mutation authority;
- production deposit limits and minimum balance are absent;
- LP recipient, fee custody, approvals, withdrawal delay, minimum retained
  reserves, pause/disable and recovery owners are absent;
- no complete ordinary-only and valuation-negative route artifact exists; and
- the selected PriceDesk ID-2 GREEN route does not supply an LP-token price or
  close Teller housekeeping, trusted-deposit, Lootbox, Deleverage, liquidation,
  or other valuation-dependent reachability for an admitted LP asset.

Verdict: pool deployment and bounded GREEN pricing are selected launch work,
subject to their 23 typed blockers. No GREEN/USDG LP asset row, collateral
admission, custody, valuation route, funding, or activation is admitted by this
qualification.

## RIPE/WETH Uniswap V2 LP verdict

### Bound facts and recomputed economics

- Robinhood chain ID: `4663`.
- Official V2 factory:
  `0x8bceaa40b9acdfaedf85adf4ff01f5ad6517937f`.
- Official Router02:
  `0x89e5db8b5aa49aa85ac63f691524311aeb649eba`.
- Official WETH:
  `0x0Bd7D308f8E1639FAb988df18A8011f41EAcAD73`.
- Exact token order remains unresolved until the deployment-produced RIPE
  identity is frozen; the factory's numeric ordering is controlling.
- The V2 fee is 30 bps and the position is full-range constant product. No V3,
  V4, NFT wrapper, hook, range, or redundant GREEN/USDG Uniswap venue is
  selected.

For equal-value reserves of USD 50,000 per side and fee factor `997/1000`, an
average execution-price deviation no greater than 1% requires:

`dx <= x * ((997/1000) - (99/100)) / ((99/100) * (997/1000))`

At `x = 50,000`, this is exactly `35,000,000 / 98,703`, or approximately USD
354.599. Conversely, an unsupported USD 25,000 trade at that same ceiling
requires one-side reserve of exactly `24,675,750 / 7`, or approximately USD
3,525,107.143. The repository rounds the required ceiling up to USD 3,525,108.
These recomputations reject any implication that USD 50,000 per side supports
USD 25,000 within 1% and grant no capital authority.

### Blocking facts

- final RIPE identity, exact factory-derived pair/LP identity, creation/first
  liquidity evidence, runtime/init hash, token order and LP getters are absent;
- LP decimals are not accepted from V2 convention without the exact pair
  runtime getter;
- funding source and amount are absent; PSM funds are categorically not LP
  capital;
- custodian/Safe, approvals, transfer permissions, fee handling, withdrawal
  delay, retained reserve floor, provisional-liquidity aborts, incident owner,
  and recovery sequence are absent;
- the shared ordinary-only and valuation-negative route proof is incomplete;
  and
- thin liquidity and spot manipulation make the pair unsuitable for protocol
  valuation. There is no accepted Uniswap oracle.

The existing `RobinhoodUniswapV2RipePrices` source remains useful only for
research/monitoring: protocol-accounting construction raises, `getPrice`
returns zero, `getPriceAndHasFeed` returns `(0, false)`, and `hasPriceFeed`
returns false. It must not be registered in PriceDesk.

Verdict: the external V2 canary is conditionally supportable after its owner
and external inputs are bound, but its LP token is not launch-admissible in
Ripe.

## DP-14 disposition

The reopened decision resolves the policy direction but does not fabricate
deployment facts. All four DP-14 leaves remain typed blockers:

| DP-14 leaf | State | Required closure |
| --- | --- | --- |
| `Deployment.DP-14.lp.identities` | `blocked_per_lp` | exact GREEN/pool and RIPE/pair identities, factory derivation, runtime/init and token-order evidence |
| `Deployment.DP-14.lp.decimals` | `blocked_per_lp` | exact LP runtime getter and metadata proof for each LP |
| `Deployment.DP-14.lp.depositLimits` | `blocked_per_lp` | owner-approved per-user/global limits and minimum balance, plus custody/withdrawal controls |
| `Deployment.DP-14.lp.oracleArtifacts` | `blocked_negative_route_artifact` | accepted no-feed policy plus complete ordinary-only and valuation-negative composed proof |

The oracle policy itself is resolved: neither LP has an accepted launch price
feed. That decision does not close the required negative-route artifact.

## Owner decisions that could reopen the result

For a later RIPE/WETH external canary, the owner must separately approve the
canary role, initial reference price and abort bound, non-PSM funding source and
maximum, custodian and signer policy, approval ceilings, withdrawal delay,
retained-reserve floor, monitoring and incident owner, and pause/unwind/recovery
plan. External-canary approval would not approve protocol admission.

For the selected GREEN/USDG launch-pricing work, the owner must separately choose the
`600` versus `866` EMA vector, `5_000` versus `7_500` stabilizer adjustment,
accepted `7_200` staleness calibration, production liquidity source and amount,
Endaoment/custody roles, deposit and minimum-balance policy, and the
pause/disable/recovery plan. Closing those pool-operation inputs would not
itself approve the LP token as a Ripe asset, collateral, or launch oracle.

For either future protocol admission, the owner must explicitly reopen that LP
and approve exact per-user/global deposit limits, minimum balance, custody and
withdrawal controls, the no-feed posture, and a production design that enforces
per-asset ordinary-only deposits while excluding every unpriced
valuation-dependent route. PSM reserves are unavailable for every LP funding
case.

## Externally verifiable facts still required

GREEN/USDG requires the final GREEN identity; live AddressProvider and factory
bindings; implementation getter and runtime; creation order; exact pool/LP
identity; coin order; LP decimals and metadata getters; and USDG
proxy/implementation/layout proof. RIPE/WETH requires the final RIPE identity;
live factory and Router02 bindings; the factory-derived pair identity and init
evidence; exact token order; pair runtime; LP decimals and metadata getters;
and first-liquidity evidence. Each fact must be independently bound to an
accepted chain, block, provider, and code identity. No such LP identity or
runtime observation was accepted in this qualification.

## Implementation and test work after a future reopen

No implementation work is authorized now. A future protocol-admission effort
would first need a reviewed shared-contract design covering Teller/TellerUtils,
Lootbox, Deleverage, liquidation/accounting consumers, and configuration
interfaces. Any values would then enter only through the two existing editable
authorities—`config/BluePrint.py` and
`contracts/config/DefaultsRobinhood.vy`—with the derived ledger regenerated
from them. Only after those prerequisites could a separately authorized H-05
plan, migration, artifact update, or activation step be proposed.

Future tests must derive from the canonical authorities and fail on fabricated
pool identity, decimals, deposit limits, forbidden oracle registration, LP
activation, and LP reachability. Snapshotting a negative verdict is not a
substitute for those mutation-resistant properties.

## Fork and security evidence after a future reopen

No LP fork qualification, accepted pool observation, runtime execution, or new
H-09 ledger/classification occurred here. After identities and owner inputs are
bound, a separately authorized network-disabled H-09 archive-fork run would
need to verify factory derivation, code/runtime/getters, token order, decimals,
USDG layout where applicable, limits, custody, and the full ordinary/trusted
deposit, withdrawal, rewards, snapshot, deleverage, swap, liquidation, pause,
and recovery route set. Independent security review must cover manipulation,
custody and signer compromise, approval exposure, thin-liquidity aborts,
reserve retention, and unwind/recovery behavior.

## Current-state and lifecycle boundary

No LP token is configured, registered, held as a Ripe asset, admitted, or
active. No LP token is a launch oracle. The GREEN/USDG pool and bounded GREEN
pricing route are selected launch work but remain undeployed and unfunded;
RIPE/WETH remains only a conditionally possible externally held canary. This
documentation-only qualification performed no RPC, fork execution, migration,
configuration, funding, custody, registration, deployment, activation, or
external-state action. Future owner, external, implementation, fork, and
security work may reopen an LP-admission verdict, but passing a later
qualification still would not authorize configuration, deployment,
activation, or release.
