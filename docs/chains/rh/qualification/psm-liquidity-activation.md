# Robinhood PSM, reserve, and launch-liquidity activation proposal

**Status:** Complete first draft with controlling owner disposition; cross-agent synthesis and fork qualification required  
**Authority commit:** `0d5994aa78f9d6f35b59bd7a2bc70fa18706e693`  
**Authority tree:** `b68dffdddbdc7c5ae8423db049099c1632b478c9`  
**Product boundary:** Product, economic, operational, and test design only  
**Activation authority:** None

This proposal binds its repository facts to the authority above. It does not
bind live addresses, deploy artifacts, signers, RPC state, Uniswap artifacts,
or final Curve artifacts. “Launch” below means an allowlisted, capped
activation after the complete ceremony and fork gate; it does not mean public,
uncapped access.

## 1. Executive recommendation

Deploy the existing shared `EndaomentPSM` bytecode with canonical Robinhood
USDG as its sole reserve asset, both user directions disabled, the yield
position exactly `(0, zero)`, and no effective GREEN-mint authority. The PSM's
immutable Department flag is expected to report `canMintGreen() == true`, but
its user mint flag, HQ tuple, and the HQ global circuit breaker keep minting
unavailable. Configure it while disabled, fund it with **100,000 USDG held
idle in the PSM**, prove redemption end to end, disable redemption again
pending production approval, and only then enter the separately approved
production activation. The PSM HQ capability tuple is the final capability
mutation and global minting is the final launch mutation.

The preferred qualification/canary candidates are:

| Parameter | Initial proposal | Classification |
| --- | ---: | --- |
| Reserve asset | canonical Robinhood USDG only | established architecture |
| Idle PSM reserve | `100,000 USDG` | preferred qualification candidate |
| Mint fee | `10 bps` | preferred qualification candidate |
| Redeem fee | `0 bps` | preferred qualification candidate |
| Global mint capacity | `25,000 GREEN` per interval | preferred qualification candidate |
| Global redeem capacity | `50,000 GREEN` per interval | preferred qualification candidate |
| Interval | `7,200` blocks, intended as one economic day | preferred candidate; fork cadence must be qualified |
| Mint allowlist | enforced | controlling canary posture |
| Redeem allowlist | enforced | controlling canary posture |
| Canary address budget | `10,000` reserve-equivalent per address per interval | operational policy; not enforced by the contract |
| Canary transaction range | `100` to `10,000` reserve-equivalent | operational/UI policy; not enforced by the contract |
| Yield | lego `0`, vault token `zero`, auto-deposit `false` | required |
| Underscore registry | `zero` | required |
| Non-governance lite-action accounts | none through the initial canary | controlling owner disposition |
| USDG effective stale ceiling | `86,400 seconds`, never zero | technical candidate/current ceiling; final production policy not accepted |
| Steady-state Echo/Charlie/Chainlink timelock | `600` blocks | current manifest value |
| Timelock maximum and expiry | `50,400` blocks | current manifest value |

Redemption **must be functional before minting is enabled**. A PSM that can
create GREEN but has not proved that it can return USDG is not launchable.
The larger redeem bucket and zero redeem fee make that ordering economically
real, not merely ceremonial. The 100,000 USDG reserve covers two proposed
50,000-GREEN redeem-cap buckets at peg before considering mint inflows. The
buckets begin on first successful use rather than on a calendar grid, and any
GREEN holder who can route through an allowlisted sender may consume them.

The smallest safe launch-critical scope does not require Curve. Chainlink is
the sole launch price authority. Uniswap is the proposed launch liquidity
venue, subject to the final Uniswap workstream. Curve remains a required
near-term observation and qualification scenario, but its absence must not
change PSM pricing or prevent the capped redemption-first launch.

The largest current limitations are:

1. the PSM has no on-chain per-user cap, minimum transaction, maximum
   transaction, or minimum-output argument;
2. any non-governance account with `canPerformLiteAction` can, while the PSM is
   unpaused, immediately transfer up to the complete idle reserve to
   EndaomentFunds through `SwitchboardEcho`;
3. generic Department recovery works while paused and sweeps the complete
   asset balance to the governance-selected recipient;
4. the approved generic reserve-alias/operator-output policy is not yet
   implemented, so compatibility-required ABI selectors still say `USDC`;
5. there is no on-chain sequencer-uptime check or recovery grace;
6. the approved 86,400-second USDG stale ceiling equals the published feed
   heartbeat and therefore has no lateness margin;
7. PriceDesk registry ID 2 must remain empty and reserved for Curve semantics;
8. an oracle-module pause does not stop oracle reads;
9. PSM reserve custody and launch DEX liquidity are separate pools of capital
   and cannot be silently netted; and
10. final Uniswap, token/oracle, Curve, role, address, and artifact inputs are
    still external to this report.

The controlling owner posture is allowlisted access through the initial
canary, with no per-user/min-max/min-output contract-change task now. Public
access requires separate approval after at least seven completed use-anchored
intervals, reconciliation, reserve coverage, incident and oracle evidence, and
final circulating-GREEN analysis; it is never a timer-only transition.

## 2. Current Base and Robinhood behavior

### Base behavior

Base migration
`migrations/base-mainnet/2026011400_EndaomentPSM.py` deploys the PSM with:

- Base USDC;
- `43,200` blocks per interval, described as one day;
- zero mint and redeem fees;
- `100,000 GREEN` mint and redeem capacity per interval;
- Underscore lego `13`; and
- a Base yield-vault token, with constructor auto-deposit enabled.

Base also creates a GREEN/USDC Curve pool with `100 USDC + 100 GREEN` in
`migrations/base-mainnet/2001_CurvePools.py`, registers Curve pricing, and
uses the Endaoment stabilization machinery. Those are Base deployment facts,
not Robinhood defaults or production-size precedents.

### Shared PSM behavior

`contracts/core/EndaomentPSM.vy`:

- initializes `canMint=false`, `canRedeem=false`, `shouldAutoDeposit=true`,
  and `isPaused=false`;
- requires a nonzero constructor interval and nonzero, finite global direction
  caps; only the later interval setter also rejects `max_value(uint256)`;
- accepts exactly one immutable six-decimal reserve address through the legacy
  `USDC` selector;
- holds fees in the PSM;
- maintains independent global mint and redeem interval buckets;
- anchors each direction's bucket at its first successful use, so neither is a
  fixed calendar grid and the two directions may drift independently;
- checks allowlists by `msg.sender`, not recipient;
- caps execution to the sender balance, interval availability, and reserve
  availability instead of guaranteeing the requested amount;
- burns only the GREEN actually accepted on redemption;
- has no per-user accumulator, transaction minimum, transaction maximum, or
  user-supplied minimum output;
- can hold reserve directly or, if configured, through an Underscore yield
  position;
- exposes all-balance, arbitrary-recipient recovery through the inherited
  Department path even while paused; and
- can transfer a caller-selected amount, capped by the idle balance, to
  `EndaomentFunds` through any valid-Ripe caller while unpaused.

For an ordinary user, pricing is intentionally asymmetric:

Let `C` be remaining GREEN interval capacity and `R` be available whole-token
USDG reserve. With zero fees and before a user-balance cap:

| USDG price | Mint 1 USDG | Redeem 1 GREEN | Maximum gross mint input | Maximum redeem payment |
| ---: | ---: | ---: | ---: | ---: |
| `$0.90` | `0.90 GREEN` | `1.00 USDG` | `max(C / 0.90, C) = 1.111111… C USDG` | `min(C, 0.90 R GREEN)` |
| `$1.00` | `1.00 GREEN` | `1.00 USDG` | `C USDG` | `min(C, R GREEN)` |
| `$1.10` | `1.00 GREEN` | about `0.909090 USDG` | `max(C / 1.10, C) = C USDG` | `min(C, R GREEN)` |

Minting uses the lesser of market value and nominal `$1` value. Redemption
uses the lesser of market reserve amount and nominal 1:1 reserve amount.
The existing test suite covers generic pause, enablement, allowlists, fees,
interval rollover, reserve availability, depeg direction, SavingsGreen,
privileged recipients, yield, events, and rounding. It is not the required
Robinhood fork qualification.

### Robinhood behavior already fixed

The Robinhood parameter manifest and planning evidence fix these points:

- canonical USDG is PSM/LP-only and is not ordinary Teller collateral;
- the repository's current evidence records mainnet USDG proxy
  `0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168` and the official USDG/USD
  Chainlink proxy `0x61B7e5650328764B076A108EFF5fa7282a1B9aD2`;
- the PSM is to be deployed and registered disabled;
- both constructor direction flags are false;
- the constructor yield tuple is `(0, zero)`;
- constructor auto-deposit is true because that is shared source behavior,
  followed by mandatory pre-activation `shouldAutoDeposit=false`;
- Underscore is omitted and its registry is zero;
- redemption is proved before mint capability;
- the PSM HQ tuple is the final capability-tuple mutation;
- global minting is disabled during tuple construction and enabled last;
- CM-048 is deployed and registered at HQ ID 22 in reserved migration `0600`,
  `0800_EndaomentPsmDisabled.py` proves the disabled posture, and
  `0900_CapabilitiesRolesAndHandoff.py` owns final capabilities and roles;
- the `0800` reservation remains blocked by `B-PSM-SEQUENCE`;
- PriceDesk ID 1 is Chainlink, while ID 2 stays empty and reserved exclusively
  for Curve semantics; a non-Curve source at ID 2 is forbidden;
- Base migrations and Base history are not Robinhood inputs; and
- the current manifest approves a `600`-block minimum and `50,400`-block
  maximum/expiry for Switchboard Echo, Switchboard Charlie, and Chainlink,
  plus an `86,400`-second USDG stale ceiling.

The same manifest still carries typed nulls for PSM fees, capacities,
interval, allowlists, reserve funding, and executable sequence binding. The
numeric recommendations in this report are proposals to close those inputs,
not claims that the manifest already approves them.

### Program and prior-authority binding

This proposal is a subordinate first draft under `RH-D009 — USDG price path`
and the existing `docs/chains/rh/usdg-psm-decision.md`; it does not create new
canonical `RH-D` identifiers. It proposes bindings for:

| Program row | Destination | Proposal here |
| --- | --- | --- |
| `P-H04-361` | `DP-08.psm.mintFee` | 10 bps |
| `P-H04-362` | `DP-08.psm.redeemFee` | 0 bps |
| `P-H04-363` | `DP-08.psm.maxMintPerInterval` | 25,000 GREEN |
| `P-H04-364` | `DP-08.psm.maxRedeemPerInterval` | 50,000 GREEN |
| `P-H04-365` | `DP-08.psm.numBlocksPerInterval` | 7,200 blocks, cadence-rebind required |
| `P-H04-366` | `DP-08.psm.allowlists` | two canary actors total; both directions enforced |
| `P-H04-367` | `DP-08.psm.reserveFunding` | 100,000 USDG |
| `P-H04-370` | `DP-09.psm.executionBinding` | Section 6 mapped to `0600`/`0800`/`0900` and separate activation |
| `P-H04-408` | `DP-17.staleWindows.usdgCeiling` | current 86,400-second technical candidate/ceiling; production policy remains blocked on operating margin |

The approved ordering rows `P-H04-368` and `P-H04-369`, together with
`NEG-H03-PSM-REDEEM-FIRST`, `NEG-H03-PSM-MINT-LAST`,
`NEG-H03-GLOBAL-MINT-SEQUENCE`, `NEG-018`, `NEG-019`, and
`S-046-PSM-ACTIVATION`, control the ceremony and are reconciled in Sections 6
and 10.

Two prior-authority dispositions are preserved explicitly:

- the owner-approved reserve-naming option is generic shared aliases and
  operator output while compatibility-required legacy selectors remain; the
  remaining issue is implementation, not a reopened naming choice; and
- the pre-production redemption canary is disabled again after proof. Keeping
  redemption active is reserved for the later production-activation approval,
  so this report does not silently change the prior posture; and
- prior language to “configure” fees, caps, interval, and no-yield state is
  interpreted as binding those values in constructor inputs and asserting them
  after deployment. Reapplying identical values is not a ceremony step because
  the shared setters revert `no change`.

### Frozen-tree evidence anchors

The controlling repository sources for this proposal are:

- [`contracts/core/EndaomentPSM.vy`](../../../../contracts/core/EndaomentPSM.vy)
  for pricing, intervals, user gates, reserve flows, no-op setters, and the
  expected-true Department mint flag;
- [`contracts/config/SwitchboardEcho.vy`](../../../../contracts/config/SwitchboardEcho.vy),
  [`contracts/config/SwitchboardCharlie.vy`](../../../../contracts/config/SwitchboardCharlie.vy),
  and [`contracts/modules/DeptBasics.vy`](../../../../contracts/modules/DeptBasics.vy)
  for lite authority, pause, and both reserve-extraction paths;
- [`contracts/registries/PriceDesk.vy`](../../../../contracts/registries/PriceDesk.vy),
  [`contracts/registries/modules/AddressRegistry.vy`](../../../../contracts/registries/modules/AddressRegistry.vy),
  and [`contracts/priceSources/ChainlinkPrices.vy`](../../../../contracts/priceSources/ChainlinkPrices.vy)
  for price fall-through, sequential IDs, and round validity;
- [`docs/chains/rh/usdg-psm-decision.md`](../usdg-psm-decision.md) and
  [`docs/chains/rh/decision-register.md`](../decision-register.md) for prior
  PSM authority and canonical `RH-D009`;
- [`docs/chains/rh/robinhood-deployment-support-specification.md`](../robinhood-deployment-support-specification.md)
  for PriceDesk ID 2, CM-046/047/048, and `0600`/`0800`/`0900`; and
- [`config/robinhood-parameters.json`](../../../../config/robinhood-parameters.json),
  [`config/robinhood_blueprint.py`](../../../../config/robinhood_blueprint.py),
  and [`scripts/utils/migration_runner.py`](../../../../scripts/utils/migration_runner.py)
  for P-H04, NEG/S, and migration reservations.

### Deliberate Robinhood differences from Base

| Surface | Base | Robinhood proposal | Reason |
| --- | --- | --- | --- |
| Reserve | USDC | canonical USDG | chain-native approved reserve identity |
| Yield | lego 13 plus Base vault | `(0, zero)`, auto-deposit false | no Underscore/yield inheritance |
| Initial fee | 0 / 0 bps | 10 / 0 bps mint/redeem | constrain issuance while preserving redemption |
| Daily direction cap | 100k / 100k | 25k / 50k GREEN | smaller launch loss envelope; redemption-first |
| Interval blocks | 43,200 | proposed 7,200 | same intended day, Robinhood cadence |
| Initial access | public flags once enabled | allowlisted canary | missing per-user/min/max enforcement |
| Price authority | Base price graph | Chainlink USDG/USD only for PSM | no DEX fallback |
| Launch DEX | Curve GREEN/USDC | provisionally Uniswap GREEN/USDG and RIPE/WETH | parallel venue decision |
| Curve | price/stabilizer integration | absent or observation-only at launch | keep PSM independent |
| Endaoment | treasury, liquidity, stabilization | no launch PSM funding or stabilization dependency | reduce authority and routing surface |
| Reserve custody | may auto-deposit | idle PSM balance | deterministic redeemability |
| Sequencer policy | no Robinhood-specific policy | operational down/recovery gate | no on-chain uptime adapter |

## 3. Proposed disabled deployment state

### Constructor and registration state

Deploy the shared PSM with:

```text
reserve immutable / legacy USDC() = canonical Robinhood USDG
numBlocksPerInterval             = 7_200
mintFee                          = 10
maxIntervalMint                  = 25_000e18
redeemFee                        = 0
maxIntervalRedeem                = 50_000e18
yieldLegoId                      = 0
yieldVaultToken                  = 0x0000000000000000000000000000000000000000
```

Immediately after deployment and before registration, assert:

```text
canMint()                        == false
canRedeem()                      == false
canMintGreen()                   == true  # immutable Department capability
shouldAutoDeposit()              == true
isPaused()                       == false
USDC()                           == canonical USDG
getUsdcYieldPositionVaultToken() == zero
getUnderlyingYieldAmount()       == 0
USDG balance                     == 0
HQ registration                 == absent
HQ GREEN mint capability        == absent/false
HQ global mintEnabled            == false before registration/configuration
```

Registration at the canonical PSM slot is permitted only with the HQ tuple
`(canMintGreen=false, canMintRipe=false, canSetTokenBlacklist=false)`.
Registration is not activation. Effective GREEN mint authority has three
factors: global `RipeHq.mintEnabled`, the PSM's HQ tuple, and the PSM's
immutable `canMintGreen()` Department flag. The third is expected true; the
first two must be false during disabled deployment, and the user-facing
`canMint` flag supplies an additional PSM execution gate.

### Disabled configuration

While both directions and global minting remain false:

1. bind the Chainlink-only USDG PriceDesk profile;
2. set and confirm `shouldAutoDeposit=false`;
3. assert the constructor-set fees, caps, interval, and `(0, zero)` yield tuple
   without scheduling setters for identical values;
4. add only the approved canary senders to both allowlists;
5. set both allowlist-enforcement flags true;
6. confirm zero Underscore;
7. finish the setup-only zero-timelock phase;
8. set steady-state Echo, Charlie, and Chainlink action timelocks to
   `600` blocks and confirm `50,400`-block expiry; and
9. require no pending or expired action before funding.

Every PSM setter rejects a no-op. Constructor-set fees, caps, interval, and
yield therefore must never be “re-applied”: doing so would create a pending
Echo action whose execution reverts and must then be explicitly canceled.
The only intended post-deployment PSM mutations in this phase are
`shouldAutoDeposit=false`, two allowlist-enforcement flips, and the approved
allowlist-member additions.

The PSM setters reject while the PSM is paused. Therefore initial exact
configuration occurs unpaused but unreachable through both user flags and the
HQ mint gate. After configuration and funding, pause the PSM while waiting for
the activation ceremony. Governance unpauses it only immediately before the
approved redemption action is executed.

### Disabled-state invariants

The disabled deployment is acceptable only when all are true:

- mint and redeem revert before token transfer;
- funding the PSM changes only its USDG balance;
- no approval is granted from the PSM to any external address;
- `getAvailableUsdc()` equals the idle USDG balance exactly;
- PriceDesk ID 1 is the approved Chainlink source and ID 2 is exactly zero,
  with no pending registration capable of placing a non-Curve source there;
- `MissionControl.canPerformLiteAction(account)` is false for every
  non-governance account under the controlling initial-canary disposition;
- direct calls and scheduled execution of every constructor-value no-op setter
  revert `no change`, and no such action remains pending;
- no Base address is present in constructor inputs, registry rows, pending
  actions, approvals, role rows, or reports;
- no Base migration or history path is read as Robinhood history;
- the USDG feed is complete, positive, fresh, and the only PSM price authority;
- Curve and Uniswap state cannot change the returned USDG PSM price;
- SavingsGreen true-flags are disabled in clients unless its final deployment
  result is bound; and
- operator output displays `USDG`, its exact address, and six decimals even
  if legacy ABI labels still say USDC.

## 4. Reserve and liquidity design

### Canonical reserve

The PSM has one canonical reserve: Robinhood mainnet USDG. Do not add USDC,
WETH, LP tokens, Curve vault tokens, or a basket to the PSM. The immutable
single-reserve source does not implement baskets, haircut allocation, or
cross-reserve redemption.

The reserve token must be rebound at the release block to its canonical
proxy, implementation, runtime hashes, decimals, exact-transfer behavior,
pause/freeze state, and relevant administrator roles. Drift is an abort, not a
reason to substitute another stablecoin.

### Initial reserve funding

Fund exactly **100,000 USDG** from an owner-approved treasury/custody Safe
after disabled-state proof. Use a direct USDG transfer to the PSM; do not route
through Endaoment, an Underscore lego, a DEX, a bridge helper, or a Base
migration.

Evidence must include:

- pre/post sender balance;
- pre/post PSM balance;
- exact `100,000e6` sender decrease and PSM increase;
- unchanged PSM flags, pause, fees, caps, interval, allowlists, yield tuple,
  approvals, HQ tuple, PriceDesk profile, and global mint state;
- exact token proxy/implementation/code identities; and
- transaction receipt and finalized block identity.

Anyone can transfer USDG to the PSM. Unsolicited funding is therefore possible
and must be treated as a reconciliation item, not automatically as owner
capital or permission to enlarge caps.

### Reserve custody

Idle reserve remains in the PSM. The owner treasury Safe owns pre-funding
capital. After transfer, the unchanged shared source exposes two materially
different extraction paths:

| Path | Caller and timing | Destination and amount | Pause behavior |
| --- | --- | --- | --- |
| `SwitchboardEcho.transferUsdcToEndaomentFundsInPsm` | governance or any account for which `MissionControl.canPerformLiteAction` is true; immediate and untimelocked | fixed HQ ID 21 EndaomentFunds; caller-selected amount capped by the complete idle balance | PSM must be unpaused |
| `SwitchboardCharlie.recoverFunds` into inherited `DeptBasics.recoverFunds` | governance initiates and executes after the Charlie timelock | any nonzero recipient selected in the action; complete balance of the selected asset, with no partial recovery option | works while the PSM is paused |

Pause therefore contains the immediate Echo-to-EndaomentFunds path but does
not contain generic Department recovery. The latter is all-or-nothing for
USDG. Policy may require a pre-bound recovery Safe, but the shared contract
does not enforce that recipient.

The controlling unchanged-source canary has **no non-governance lite-action
accounts through the initial canary**. This makes both extraction paths
governance-controlled, but it also means there is no non-governance lite
guardian for immediate pause. The governance Safe must be operationally able
to call Charlie pause.

The owner does not accept the coupled lite pause/reserve authority and does not
authorize a shared permission split now. If immediate non-governance pause
becomes a release requirement, stop and reopen `RH-D001` as a separate minimal
contract/security decision. The present role map cannot grant that pause
without also granting the immediate Echo reserve-transfer surface because both
use the same global `canPerformLiteAction` predicate.

Both paths are exceptional. Routine liquidity management never uses them;
each call is monitored, and any recovery while redemption is active or while
GREEN remains outstanding requires a specific insolvency/exit decision.

### Reserve coverage and replenishment

Monitor these separate quantities:

```text
idleReserve            = USDG.balanceOf(PSM)
circulatingGreen       = GREEN.totalSupply() minus provably noncirculating balances
allowlistedGreen       = GREEN held or controllable by approved redeem senders
psmNetFlowAttribution  = sum(MintGreen.greenOut) - sum(RedeemGreen.greenIn)
redeemBucketLeft       = getAvailIntervalRedemptions()
hardRedeemCapacity     = min(redeemBucketLeft, reserve-backed executable amount)
bucketCoverage         = idleReserve / max(redeemBucketLeft at peg, 1 USDG)
```

Event-derived PSM net flow is only an attribution and must not be used as the
reserve liability. GREEN is fungible: LP allocations, borrowing, bonds, and
other mint paths can all reach an allowlisted sender. The 100,000 USDG reserve
is a bounded outflow envelope, not full GREEN backing. At peg, any qualifying
holders can exhaust it across two 50,000-GREEN use-anchored redeem buckets.
The provisional GREEN/USDG LP alone introduces 50,000 GREEN, and the final
activation packet must bind total initial supply, noncirculating allocations,
allowlisted-sender balances/control, and every other GREEN creation path.

Removing the redeem allowlist is therefore a reserve-sizing and solvency
decision, not merely a permission change. Before removal, size the reserve and
cap against total circulating GREEN and the intended redemption-coverage
horizon, then repeat the stress and incident analysis.

Recommended thresholds:

| Condition | Response |
| --- | --- |
| idle reserve `>= 100,000 USDG` and no mismatch | normal canary |
| idle reserve `< 100,000` but `>= 75,000` | warning; no cap increase or liquidity withdrawal |
| idle reserve `< 75,000` | disable/pause mint; reconcile before resuming |
| idle reserve `< 50,000` or next-bucket coverage `< 1.0x` | pause PSM; owner incident |
| unexplained accounting difference `> 1` USDG atomic unit | pause and reconcile |
| USDG frozen/paused or implementation drift | immediate pause; no funding or recovery transfer until assessed |

Replenishment is a new direct custody transfer under the same proof as initial
funding. It never auto-enables mint, raises a cap, clears an incident, or
authorizes use of DEX liquidity.

### Launch liquidity

PSM reserve and DEX liquidity are separate. The provisional launch-liquidity
budget is:

- **50,000 USDG plus 50,000 GREEN** for the GREEN/USDG Uniswap position; and
- **50,000 USD equivalent of WETH plus 50,000 USD equivalent of RIPE** for the
  separate RIPE/WETH Uniswap position; and
- no PSM reserve may be used for that position.

The final Uniswap agent must replace the venue version, factory, pool, fee
tier, initialization price, tick spacing/range, position-manager address,
position custody, rebalance permissions, TWAP/observation policy, and effective
depth calculation for both launch pools. The WETH quantity must use the final
approved Chainlink WETH/USD round and the RIPE quantity must use the
owner-approved launch price at the ceremony snapshot. Until then, production
pool creation and funding values remain provisional even though the capital
envelope is recommended. GREEN used for liquidity must come from the separately
approved initial-supply allocation; creating the LP does not authorize the PSM
or another department to mint.

The position token or LP claim is held by a dedicated governance Safe or a
separately reviewed liquidity manager, never by the PSM. The proposed minimum
observable target is `25,000 USD` of executable two-sided depth within
`+/-1%` of the relevant launch reference after fees in each pool. If the
selected Uniswap design cannot provide that from the provisional budget, the
owner must increase the separate LP budget or narrow the launch, not consume
PSM reserve.

## 5. Parameter proposal with rationale

### Economic and access parameters

| Parameter | Preferred qualification candidate | Rationale | Enforcement |
| --- | ---: | --- | --- |
| `mintFee` | `10 bps` | modest issuance friction and fee reserve | on-chain |
| `redeemFee` | `0 bps` | make redemption proof and peg exit strongest | on-chain |
| `maxIntervalMint` | `25,000e18` | limits one-day new GREEN exposure to 25% of initial reserve at peg | on-chain global |
| `maxIntervalRedeem` | `50,000e18` | permits a meaningful exit while preserving one additional funded interval | on-chain global |
| `numBlocksPerInterval` | `7,200` | proposed Robinhood one-day cadence | on-chain; final cadence gate |
| mint allowlist enforcement | `true` | compensates partially for missing per-user limit | on-chain sender gate |
| redeem allowlist enforcement | `true` | bounded canary and known actors | on-chain sender gate |
| canary per-address budget | `10,000` per interval | no one operator consumes the full bucket | operational only |
| transaction minimum | `100` reserve-equivalent | avoids dust/operator error | UI/operator only |
| transaction maximum | `10,000` reserve-equivalent | bounds one-call/canary loss | UI/operator only; global cap remains on-chain |
| initial allowlist size | `2` operational addresses total, one of which is the designated test actor | independent execution without letting three 10,000 budgets exceed the 25,000 mint cap | owner-bound addresses |

At least two canary actors should exist so the shared global bucket and sender
allowlist semantics are proven. They must not be Underscore vaults or
contracts that could be classified as such.

The current PSM cannot enforce the per-address budget or transaction range.
The fork suite must prove that fact. These values are not security controls
against a compromised allowlisted key. The controlling canary posture is two
allowlisted actors and no per-user/min-max/min-output contract-change task.
Reconsider a minimum shared change only if canary evidence demonstrates need.
Public access remains a separate later approval under Section 12.

### Oracle parameters

Use the official canonical USDG/USD Chainlink feed through the existing
`ChainlinkPrices` and `PriceDesk` contracts:

```text
needsEthToUsd = false
needsBtcToUsd = false
feed staleTime = 86,400 seconds
effective staleTime = max(MissionControl global, feed) = 86,400 seconds
PriceDesk USDG source profile = Chainlink only
```

Zero effective stale time is forbidden. A longer value is also forbidden by
the current USDG ceiling. Alert at 20 hours without a new complete round and
pause no later than the 24-hour hard boundary. A new round must be positive,
non-future, have nonzero `roundId`, and satisfy
`answeredInRound >= roundId`.

The current technical `86,400`-second candidate/ceiling equals the feed's
published `86,400`-second heartbeat. The contract accepts age exactly equal to
the threshold and returns zero one second later, so there is no
publisher-lateness margin. A heartbeat slip makes PSM redemption unavailable
as well as minting:
the reserve-backed redeem maximum becomes zero and execution reverts. This is
in tension with redemption-first availability, and the owner does not yet
accept it as final production policy. Activation remains blocked unless the
network/token/oracle qualification establishes an acceptable operating margin
beneath the ceiling or a separate feed/ceiling policy is approved. A DEX
fallback is not an acceptable cure.

Do not configure a Curve or Uniswap USDG feed as a fallback. `PriceDesk`
iterates to later sources when an earlier configured source returns zero.
Adding a DEX fallback would silently promote it to price authority during a
Chainlink failure, contrary to this proposal.

### Parameter changes

After setup:

- actual changes to fee, cap, interval, allowlist-enforcement,
  allowlist-member, yield, and enable state use Switchboard Echo and wait `600`
  blocks; constructor-identical values are asserted, never resubmitted;
- all Chainlink feed changes wait `600` blocks;
- pending actions expire under the `50,400`-block window;
- governance must cancel stale or conflicting actions before ceremony;
- cap increases, fee decreases, allowlist removal, auto-deposit enablement,
  and yield changes require a fresh economic/security review;
- no non-governance lite account is configured through the canary; if one
  becomes a release requirement, stop and reopen `RH-D001` because it would
  simultaneously gain the immediate PSM-to-EndaomentFunds reserve-transfer
  surface; and
- immediate containment uses Switchboard Charlie pause, not a slow flag
  change.

## 6. Activation sequence

### Preparation

1. Freeze the final release commit/tree, bytecode, ABI, constructor inputs,
   chain ID, token/oracle identities, PriceDesk profile, roles, Safe
   thresholds, caps, fees, cadence, reserve funding, and DEX inputs.
2. Generate the Robinhood defaults and semantic migration plan only through
   their owning workstreams. Do not copy a Base migration or history.
3. Rehearse the exact sequence on testnet and on two fresh deterministic
   forks. No production ceremony proceeds from a partially passing matrix.
4. Confirm the monitoring stack and governance containment path before
   deploying any enabled capability. Bind governance response times and
   incident ownership under the controlling no-lite posture.

### Reserved migration sequence

5. In the HQ bootstrap, account for the fact that `RipeHq.__init__` sets
   `mintEnabled=true`. Governance calls the direct, untimelocked
   `setMintingEnabled(false)` as soon as that authority is available and proves
   the global breaker false before any mint-capable Department receives an HQ
   tuple.
6. In reserved `0400_PriceSources.py`, deploy/bind Chainlink and PriceDesk,
   register Chainlink at PriceDesk ID 1, leave ID 2 exactly empty and reserved
   for Curve semantics, and add USDG with the exact feed and nonzero
   `86,400`-second stale value.
7. Prove valid and invalid round behavior, the zero-margin heartbeat boundary,
   ID-2 reservation, and no competing USDG source before the PSM exists.
8. In reserved `0600_CoreDepartments.py`, deploy the PSM with the exact
   constructor state in Section 3 and register it at HQ ID 22 with tuple
   `(false, false, false)`.
9. Still in `0600`, verify bytecode, immutable reserve, user flags, expected
   `psm.canMintGreen()==true`, effective `RipeHq.canMintGreen(psm)==false`,
   zero balance, zero yield, and no approvals.
10. In reserved `0800_EndaomentPsmDisabled.py`, set only
    `shouldAutoDeposit=false`, the two allowlist-enforcement flags, and the two
    approved allowlist members. Assert—do not re-set—the constructor fees,
    caps, interval, and `(0, zero)` yield.
11. `0800` proves `NEG-018`, `NEG-019`,
    `NEG-H03-PSM-REDEEM-FIRST`, `NEG-H03-PSM-MINT-LAST`,
    `NEG-H03-GLOBAL-MINT-SEQUENCE`, and the disabled
    `S-046-PSM-ACTIVATION` posture. It ends with no pending or expired action.
12. In reserved `0900_CapabilitiesRolesAndHandoff.py`, finalize non-PSM
    capability tuples, nonzero steady-state timelocks, governance handoff, and
    the approved no-lite posture. The PSM tuple remains false and global
    minting remains false. Deployment handoff is not PSM activation.

### Funding and pre-production redemption qualification

13. Execute disabled-state negative tests against the bound deployment.
14. Fund exactly `100,000 USDG` through the approved treasury Safe.
15. Reconcile the exact balance delta and re-read all disabled state, including
    both reserve-extraction paths and the no-lite posture.
16. Pause the PSM while the funding and qualification evidence is independently
    reviewed.
17. Pre-stage the timelocked `canRedeem=true` action. After its confirm block
    and all gates pass, governance unpauses the PSM and executes only that
    action.
18. Execute an allowlisted `100 GREEN` redemption, then `10,000 GREEN`, using
    GREEN obtained without the PSM mint path. Verify USDG output, GREEN burn,
    zero fee, reserve delta, events, interval state, and total-supply delta.
19. Run a second actor redemption to prove the global shared bucket and sender
    allowlist.
20. Initiate and execute `canRedeem=false`, then pause and prove both user
    directions disabled again. This preserves the prior-authority requirement
    that a qualification canary grants no continuing production authority.

### Separately approved production activation

21. Obtain the owner’s exact production-activation authorization and rebind all
    identities, balances, rounds, roles, pending actions, PriceDesk ID 2,
    reserve coverage, circulating GREEN, and monitoring readiness.
22. Timelock-enable `canRedeem=true` first. Unpause only when execution is
    ready, execute the action, and perform a bounded second redemption proof.
    If redemption cannot complete, stop; mint activation is forbidden.
23. While global minting and the PSM HQ tuple remain false, timelock-enable
    the user `canMint=true` flag.
24. Prove a mint attempt still fails atomically at the HQ/global factors.
25. Confirm that `0900` left the complete non-PSM launch tuple set final and
    that no later non-PSM capability mutation is required.
26. Mutate the PSM HQ tuple to `(true, false, false)` as the final capability
    tuple change.
27. Re-read every HQ tuple, registry entry, PSM parameter, oracle input,
    disabled/omitted route, reserve balance, approval, pending action, recovery
    destination, and role.
28. Enable global minting through direct governance
    `RipeHq.setMintingEnabled(true)` as the final launch mutation. This call is
    not timelocked by RipeHq, so the exact Safe transaction and immediate
    post-state evidence are ceremony-critical.
29. Execute an allowlisted `100 USDG` mint, then at most `10,000 USDG`.
    Verify fee, GREEN output, reserve, event, supply, cap, and oracle
    asymmetry.
30. Make no further registry, capability, route, or parameter mutation in the
    launch plan. Any required mutation aborts the ceremony and returns to the
    appropriate review gate.

### Post-canary

Keep both allowlists enforced for at least seven completed, use-anchored
buckets in the relevant direction and until the owner reviews the monitoring
record. These are not calendar days: each direction starts its own bucket on
first successful use. Removing either allowlist or increasing either cap is a
separate launch-expansion decision, not an automatic time promotion; removing
the redeem allowlist also requires reserve resizing against circulating GREEN.

## 7. Roles, timelocks, and emergency authority

| Role | Proposed authority | Explicit exclusions |
| --- | --- | --- |
| Protocol governance Safe | execute Echo/Chainlink timelocks, HQ tuples, direct global mint circuit breaker, pause/unpause, Echo-to-EndaomentFunds transfer, and recovery initiation/execution | no unilateral key; final address/threshold owner-bound; exceptional reserve routes require incident decision |
| Local Switchboard governance | initiate and execute exact PSM actions under governance policy | no independent economic policy; cannot treat no-op setters as assertions |
| Non-governance lite account | **none through initial canary** | if later granted, the same role can both pause through Charlie and immediately move PSM reserve to EndaomentFunds through Echo while unpaused |
| Oracle governor | initiate/execute approved Chainlink feed lifecycle actions | cannot use Curve/Uniswap as PSM fallback |
| Reserve treasury Safe | send exact approved USDG funding | no protocol role required merely to fund; no PSM withdrawal |
| Recovery Safe | policy-designated recipient after timelocked incident decision | recipient is not contract-enforced; generic recovery is full-balance and not routine custody |
| Liquidity Safe/manager | hold and manage Uniswap position under final venue policy | no PSM reserve, no oracle authority, no GREEN mint authority |
| Monitoring operator | observe and alert | no signer or mutation authority |

Actual governance/Safe addresses, thresholds, signers, role handoff, incident
owners, and recovery recipient remain open inputs. Non-governance
lite-action membership is resolved to none through the initial canary. A role
name in a manifest is not evidence that the account exists, is controlled, or
is ready.

The `600`-block action timelock is proposed as the steady-state minimum for
PSM economics and Chainlink changes. Under the controlling no-lite posture,
the immediate emergency path is a governance Charlie pause; unpause is also
governance-only. `RipeHq.setMintingEnabled` is direct governance and has no
RipeHq timelock. Because that global breaker affects all GREEN/RIPE
mint-capable departments, use it when the incident is systemic or the
PSM-specific pause cannot contain mint risk; always record its blast radius.

Parameter timelocks do not replace transaction simulation, independent
review, or a final same-block state re-read. No action may be executed merely
because its confirm block arrived.

## 8. Failure and rollback behavior

### Normal fail-closed behavior

| Failure | Required behavior |
| --- | --- |
| PSM disabled | mint/redeem revert before transfer |
| PSM paused | both directions, PSM setters, and Echo-to-EndaomentFunds transfer revert; generic full-balance Department recovery remains reachable through timelocked governance |
| no USDG source | executions produce zero/revert; never substitute DEX price |
| stale/zero/negative/future/incomplete Chainlink round | price returns zero; strict path reverts; both mint and redemption become unavailable; pause incident |
| price-source call reverts | revert propagates atomically |
| no reserve | redeem reverts at zero amount |
| partial reserve | execution may cap below request; client must preview and display actual executable amount; round-trip integer divergence can still reach atomic `insufficient USDC` |
| reserve changes between view and execution | execution uses current state and may cap/revert atomically |
| yield absent | no withdrawal source; idle reserve is the complete reserve |
| Uniswap stress | PSM price remains Chainlink; caps and reserve limit arbitrage |
| Curve absent | PSM unchanged; CreditEngine uses base rate; Teller skips Curve snapshot |
| sequencer down | operational monitor triggers immediate pause; no on-chain uptime guard is assumed |

### Reserve shortfall

Do not socialize losses through an invented haircut, mint unsupported GREEN,
pull from DEX liquidity, or enable yield. On a shortfall:

1. pause the PSM;
2. disable PSM mint and, if required, global minting;
3. preserve reserve and evidence;
4. reconcile token, event, recovery, and balance history;
5. identify whether the cause is accounting, token control, unauthorized
   recovery, price error, or missing custody funding;
6. fund only after an owner-approved cure; and
7. re-run redemption readiness before any mint restart.

The current contract may partially fill by capping the accepted GREEN to
reserve availability. There is no minimum-output parameter. Operator software
must show the fresh executable maximum immediately before submission. Canary
transactions must use bounded explicit amounts, not `max_value(uint256)`.
Fork qualification must also hit the residual `insufficient USDC` assertion
after maximum calculation/rounding; partial-fill coverage alone is
insufficient.

### Oracle and sequencer failure

The Chainlink source has no sequencer-uptime check. Until the final token/oracle
result supplies a supported on-chain design, the operational policy is:

- pause immediately on a confirmed sequencer-down signal or inability to
  establish canonical ordering/finality;
- keep both directions paused during recovery;
- require at least one new complete USDG round whose `updatedAt` is after the
  recovery point;
- wait a **3,600-second recovery grace** with stable finality and no token/feed
  drift;
- re-read PriceDesk, feed, reserve, roles, flags, and pending actions; and
- resume redemption before mint.

This grace is an operational launch-controller rule, not current PSM
enforcement. The final oracle agent must replace the signal source and confirm
whether `3,600` seconds is compatible with Robinhood and Chainlink policy.

### Emergency states

For an incident not caused by redemption, preserve redemption only while
pricing, reserve, token behavior, and accounting remain safe. Disable
redemption when the incident directly compromises any of those conditions.
This is an evidence-based incident decision, not a blanket “always open” rule.

1. **PSM-specific danger:** Charlie pause immediately.
2. **Mint-system danger:** pause PSM, then governance disables global minting.
3. **Oracle danger:** pause PSM; initiate feed/source disable or replacement
   only under timelock. Pausing the price-source module alone is insufficient
   because current price reads ignore that pause state.
4. **USDG issuer/admin danger:** pause PSM and DEX liquidity operations; do not
   recover or transfer a frozen asset until the incident plan is approved.
5. **Role compromise:** pause with an independent guardian, cancel pending
   actions, rotate governance through its own lifecycle, then requalify.
6. **DEX danger:** stop LP management and pause PSM if the stress can exhaust
   the reserve bucket; do not change price authority.

Under the controlling no-lite posture, each “immediate” pause above means the
governance Safe calls Charlie directly. Governance response time and incident
ownership must be bound before activation. If that cannot meet the required
response time, activation stops and `RH-D001` is reopened; coupled lite
authority is not accepted.

### Rollback and abort

A deployed immutable contract cannot be rolled back. The reversible response
is capability withdrawal:

```text
pause PSM
set PSM mint false
set PSM redeem false if redemption itself is unsafe
disable global minting if mint risk is systemic
cancel pending actions
retain reserve; if recovery is approved, choose explicitly between:
  - immediate unpaused Echo transfer to fixed EndaomentFunds, or
  - timelocked Charlie/Department full-balance recovery to the bound recipient
```

Abort before activation on any identity drift, unresolved role, failed fork
row, missing monitor, nonzero yield/Underscore state, competing USDG source,
Base dependency, insufficient reserve, unexplained reconciliation difference,
sequencer instability, stale oracle, token pause/freeze, DEX artifact mismatch,
or required post-final global-mint mutation.

After activation, rollback is complete only when the pause/flags/global gate
are proved, pending actions are empty, balances and supply are reconciled, and
the incident owner records whether redemption remains open for users. Never
drain reserve merely to make the PSM appear disabled.

## 9. Uniswap/Curve/oracle relationships

### Chainlink

Chainlink is the launch price authority for USDG. `ChainlinkPrices` normalizes
the feed to 18 decimals and `PriceDesk` converts between six-decimal USDG and
18-decimal USD/GREEN accounting. Chainlink validity and freshness are
launch-critical. Chainlink does not authorize PSM activation merely by
returning a price.

### PriceDesk profiles

| Profile | USDG authority | Curve | Uniswap | Launch use |
| --- | --- | --- | --- | --- |
| P0 disabled/launch | Chainlink only | absent | external venue only | required |
| P1 observation | Chainlink only | absent or off-chain observation | off-chain price/depth monitor | permitted without changing PSM authority |
| P2 near-term Curve | Chainlink only | registered only for GREEN reference observation/snapshots | external price/depth monitor | separate promotion after final Curve qualification |
| Forbidden | Chainlink plus DEX fallback for USDG | USDG fallback | USDG fallback | never implicit |

Any PriceDesk profile change is a semantic price-authority change and requires
fork replay. Source order is not cosmetic because `PriceDesk` falls through
when a source returns zero. Registry topology is also semantic:
`Teller`, `CreditEngine`, and `Endaoment` hardcode `CURVE_PRICES_ID = 2`.
PriceDesk assigns IDs sequentially, so P0 must register Chainlink as ID 1 and
leave ID 2 empty and reserved. Registering AAPL or any other non-Curve source
second would make core contracts call Curve selectors on the wrong contract;
the plan rejects that topology before runtime.

### Uniswap

Uniswap is provisionally the GREEN/USDG launch venue and a monitoring/reference
input. It is not a PSM oracle. Monitor:

- spot and time-weighted GREEN/USDG price;
- executable depth and slippage at `100`, `1,000`, and `10,000` USDG;
- active liquidity, position range, fee accrual, and ownership;
- divergence from the Chainlink-implied PSM quote;
- reserve-bucket consumption during arbitrage; and
- pool/factory/implementation/position-manager drift.

The final Uniswap result must replace every provisional venue field before the
LP artifact gate closes.

### Curve

Curve is not required for the smallest safe PSM launch. Preserve these
near-term scenarios:

1. **Curve absent:** PriceDesk ID 2 is proved zero and reserved. PSM works from
   Chainlink; Teller housekeeping sees no CurvePrices address and skips the
   GREEN snapshot; CreditEngine returns the configured base rate.
2. **Curve present, observation-only:** the GREEN reference pool and snapshots
   may be observed, but Curve is not configured for USDG PSM pricing and cannot
   trigger Endaoment stabilization.
3. **Curve promoted:** only after final Profile 2 artifacts, clock semantics,
   pool parameters, and fork evidence are bound. Dynamic rates, Teller
   snapshots, and stabilization are promoted separately.

The retained conditional Profile 2 test design uses a disposable GREEN/USDG
pool with `A=100`, fee `4_000_000`, off-peg multiplier `20_000_000_000`,
preferred `ma_exp_time=600` and alternative `866` forks,
`100 USDG + 100 GREEN` initial liquidity, `7,200` unchanged-EVM-number
staleness stress, and reserve-fraction stress in both directions. The value
`866` is not a frozen-tree constant or preferred candidate: it is retained as
an alternative parallel conditional-architecture fork vector consistent with
the derived Curve EMA convention
`600 / ln(2) = 865.6…`, rounded to 866. It must be replaced or explicitly
confirmed by the final Curve result. These are qualification vectors, not
production liquidity values. Missing Curve artifacts do not waive the Profile
1/2 fork rows; they keep the promotion blocked while P0 can still qualify.

### Dynamic rates

At launch, dynamic Curve-derived borrow-rate adjustment is disabled by
absence of the CurvePrices registry entry. `CreditEngine.getDynamicBorrowRate`
must return the configured base rate without a Curve call. No DEX condition
may change PSM fees or caps automatically.

If Curve is later promoted, the current CreditEngine may add rate boost and
danger-duration boost based on the Curve GREEN pool status, capped by the
MissionControl maximum borrow rate. That is a credit-policy promotion, not a
PSM activation step.

### Teller snapshots

Teller housekeeping calls `addGreenRefPoolSnapshot()` only when the
CurvePrices registry entry exists. Launch acceptance must prove both branches:
absence is a clean no-op, while a later present profile writes only the
expected observation and does not change PSM accounting, reserve, or price.

### Endaoment stabilization

Endaoment stabilization is **off at launch**. Do not deploy or enable it merely
to create liquidity or fund the PSM. The current stabilizer can mint GREEN,
add/remove Curve liquidity, record pool debt, and assert nondecreasing
stabilizer profit. Those authorities and capital flows are materially larger
than the launch-critical PSM.

A later promotion requires its own:

- Curve artifact and clock qualification;
- Endaoment/EndaomentFunds custody and role map;
- stabilizer weight and pool-debt cap;
- profitability and accounting tests;
- pause and recovery plan; and
- proof that PSM reserve remains segregated.

## 10. Complete fork-test matrix

All rows run against the final integrated Robinhood release candidate and
final artifacts. Unit tests are supporting evidence, not substitutes.

| # | Area | Required cases | Required result/evidence |
| ---: | --- | --- | --- |
| 1 | Disabled state rejects mint and redeem | both user flags false; each independently false; Department `canMintGreen()==true`; HQ PSM tuple false; global mint false; PSM paused; funded and unfunded | no token movement, approval, interval change, supply change, or event on failure; all three HQ mint factors and the user gate recorded; expected-true Department flag is not misclassified |
| 2 | Reserve funding without mint | direct `100,000e6` USDG transfer while both flags/HQ/global mint false; unsolicited extra atomic unit; no non-governance lite account | exact balance delta; flags, caps, approvals, tuples, oracle, and supply unchanged; unsolicited amount appears only as reconciliation variance; reserve-transfer surfaces unchanged |
| 3 | Redemption before mint | actor receives GREEN without PSM mint; fund reserve; enable redeem only; redeem `100` then `10,000`; second actor; disable after qualification; re-enable only after separate production approval | exact burn/output/reserve/event/bucket; PSM mint and HQ mint remain unavailable throughout qualification; disabled-again proof precedes production approval; production redemption proof precedes any mint authority |
| 4 | Mint/redeem asymmetry | USDG prices `$0.90`, `$1.00`, `$1.10`; ordinary recipient; requested and max views | exact directional table in Section 2 including six/18-decimal rounding; no privileged branch |
| 5 | Fee boundaries | 0, 1, 10, 9,999, and 10,000 bps for both directions; last executable atomic unit and first zero/revert; fee accumulation | exact retained fee; no divide-by-zero; 100% views return zero; atomic failure where post-fee output is zero |
| 6 | Caps and intervals | cap minus one, exact cap, cap plus one; multiple users/calls same block; mint/redeem independence; first-use anchoring; block `start+N-1`, `start+N`, `start+N+1`; cap change mid-bucket; direct and Echo-scheduled no-op writes for fee/cap/interval/yield/flags/allowlists | exact accepted amount and bucket state; equality starts a new use-anchored interval; directions may drift; no over-cap GREEN; capped partial execution explicit; every no-op reverts and leaves no unresolved action |
| 7 | Insufficient reserve | zero, one atomic unit, below requested, exact requested, 49,999/50,000/50,001 USDG; balance changes after preview; no yield; partial-fill cases; targeted round-trip division case reaching `insufficient USDC`; both extraction paths pending/executed | zero reverts; partial reserve caps accepted GREEN where exact; residual post-calculation insufficiency reverts atomically; no LP/yield pull; full-balance recovery and fixed-destination partial transfer accounted separately |
| 8 | Oracle invalidity | no feed, age exactly 86,400 and 86,401 seconds, zero, negative, future timestamp, round ID zero, `answeredInRound<roundId`, decimals >18, source revert, source disabled, effective stale time zero mutation, heartbeat slip during redeem | all invalid launch states reject or return zero as current code specifies; equality accepted and +1 stale; mint and redeem availability loss evidenced; manifest rejects stale time zero and competing fallback; no DEX substitution |
| 9 | Sequencer down/recovery | down before submit, down during pending ceremony, stale round during outage, recovery with pre-recovery round, first post-recovery round, 3,599/3,600-second grace | operational controller pauses; no activation during down/grace; one post-recovery complete round plus grace required; current absence of on-chain check explicitly evidenced |
| 10 | Uniswap stress | no pool, pool not initialized, 90% liquidity removal, out-of-range position, `+/-1%`, `+/-10%`, and `+/-30%` spot displacement, both swap directions, fee/depth exhaustion | PSM quote remains Chainlink-only; global caps bound arbitrage; reserve threshold alerts; LP ownership and accounting exact; final venue-specific assertions supplied by Uniswap agent |
| 11 | Curve present/absent | ID 2 empty; correct Curve observation contract at ID 2; dangerous non-Curve contract at ID 2; no USDG Curve feed; stale/repeated snapshot; `A=100`, fee `4_000_000`, off-peg `20_000_000_000`, preferred `ma_exp_time=600` and alternative-derived `866`, `100+100` initial liquidity, 7,200-number staleness, and both reserve-fraction directions once final inputs arrive | empty ID 2 gives Teller no-op and base rate; non-Curve ID 2 demonstrates selector/topology failure and is rejected; correct observation does not affect PSM; no stabilization; missing Curve blocks promotion, not P0 |
| 12 | PriceDesk profile changes | P0 Chainlink at ID 1 and ID 2 empty; attempt AAPL/other source as second registration; reorder; Chainlink zero with later DEX source; add/disable/update source; pending/expired action; strict and non-strict reads | only exact P0 topology accepted for launch; ID 2 remains Curve-reserved; any non-Curve ID 2 or USDG DEX fallback fails manifest/acceptance; exact fail-closed behavior and no silent authority change |
| 13 | Governance and roles | random user, canary user, proposed no-lite state, lite account enabled on a separate case, former lite account, governance, wrong Safe threshold, wrong local gov; pause/unpause/enable/disable/feed/economic action; immediate Echo PSM-to-EndaomentFunds transfer; Charlie/Department recovery | no-lite launch has no non-governance immediate authority; when lite is enabled it can pause **and** move up to the complete unpaused reserve to EndaomentFunds, but cannot unpause/change economics/oracle; generic recovery is governance-timelocked, arbitrary-recipient, full-balance, and works paused; all action IDs/events bound |
| 14 | Pause/emergency/rollback | pause before/after funding, during each direction, with pending action, global mint off, cancel/expiry, role compromise, oracle failure, token freeze; Echo transfer paused/unpaused; generic recovery paused/unpaused; partial amount vs complete balance | pause blocks user paths, setters, and Echo transfer but not generic recovery; atomic in-flight revert; disabled tuple/pending-action inventory; destination and complete-balance effects exact; neither extraction path treated as routine rollback |
| 15 | Deterministic replay/evidence | two fresh forks from same block/hash; exact `0400`/`0600`/`0800`/`0900` boundaries plus separate activation; identical action list; restart at each ceremony boundary; reordered unauthorized action; evidence serialization | identical state roots/digests for intended replay; `P-H04-361..367/370`, `P-H04-368/369`, CM/NEG/S identifiers reconciled; reordered action fails; receipts, events, code hashes, storage reads, balances, rounds, and plan hash captured deterministically |
| 16 | No hidden Base or history dependency | poison Base USDC/feed/yield/Curve/Endaoment addresses; remove Base history; nonempty foreign history; wrong profile/chain; source/history alias; canonical Robinhood source only | plan and runtime remain Robinhood-bound or fail closed; no Base file/address/RPC fallback; no migration-history inference; no hidden legacy address needed |

### Additional matrix requirements

The matrix must also:

- run direct GREEN paths with SavingsGreen flags false;
- run SavingsGreen true-flags against the final deployed/omitted result,
  including exactly `1 GREEN` falling back to plain GREEN and the first atomic
  amount above `1 GREEN` entering the sGREEN path;
- prove the two allowlisted actors' combined 10,000 budgets do not exceed the
  25,000 mint cap and that no third actor is implied;
- prove no address is recognized as an Underscore vault;
- test the caller-supplied `_isUnderscoreVault` view boolean is never treated
  as authorization;
- bind exact event fields despite legacy USDC labels;
- prove reserve and LP capital never cross;
- capture block number, timestamp, child/L1/ArbSys values required by the final
  clock design; and
- end every scenario with tracked state and pending-action reconciliation.

No row may use a noncanonical USDG clone and call it canonical qualification.
Any disposable storage overlay must follow the final owner-approved layout
proof and be labeled non-authoritative local fork qualification.

## 11. Inputs from parallel agents

### Facts independently established here

- the frozen repository commit/tree and shared contract behavior;
- Base PSM constructor values and Base yield/Curve coupling;
- canonical USDG and the selected Chainlink price path as recorded in the
  repository;
- the current Robinhood disabled/no-yield/redemption-first/mint-last
  architecture;
- current PSM absence of per-user, min/max transaction, min-output, sequencer,
  and reserve-liability storage;
- expected-true immutable PSM Department mint flag and the separate global/HQ
  effective mint gates;
- immediate governance-or-lite PSM-to-EndaomentFunds transfer, paused-state
  blocking of that path, and paused-state full-balance Department recovery;
- no-op rejection on every PSM setter;
- current PriceDesk fall-through behavior;
- the hardcoded PriceDesk ID-2 Curve topology requirement and Curve-absent
  Teller/CreditEngine behavior;
- Endaoment stabilization authority and capital flow;
- current approved Echo/Charlie/Chainlink timelock bounds and USDG stale
  ceiling in the manifest; and
- current open `B-ORACLE-FREEZE`, `B-LP-ARTIFACTS`, and `B-PSM-SEQUENCE`.

### Controlling constraints on parallel results

- final token/oracle evidence may replace identities and operating parameters,
  but Chainlink remains the sole PSM price authority and the zero-margin stale
  policy remains unaccepted;
- final Uniswap results own venue, pool, custody, and capital recommendations,
  but cannot use PSM reserve or become a PSM fallback;
- final Curve results use `600` as the preferred `ma_exp_time` candidate and
  retain `866` as an alternative fork vector; Profile 2 remains
  observation-only and is not active at launch;
- Teller snapshots, dynamic rates, and Endaoment stabilization remain Profile
  2 concerns and cannot change launch PSM accounting or price authority; and
- deployment-owner role output must bind no non-governance lite-action account
  through the initial canary.

### Provisional assumptions used for this first draft

- Uniswap is the GREEN/USDG and RIPE/WETH launch venue;
- `50,000 USD` per side in each launch pool is the initial separate LP budget;
- `25,000 USD` within `+/-1%` in each pool is an achievable depth target;
- `7,200` blocks remains the intended economic-day PSM interval after final
  cadence binding, with each direction anchored to first use rather than a
  calendar grid;
- an operational sequencer signal is available to the monitor;
- a 3,600-second post-recovery grace is appropriate; and
- final initial/circulating GREEN supply and allowlisted-sender control are
  compatible with the proposed reserve envelope.

### Inputs that must be replaced by final results

**Uniswap agent**

- venue version, deployment status, canonical factory/router/quoter/position
  manager, pool-creation and initialization rules for GREEN/USDG and RIPE/WETH;
- fee tier, tick spacing, range, custody artifact, rebalance and collect roles;
- final LP amount and effective depth;
- TWAP/observation reliability and manipulation/stress results; and
- exact fork fixtures, addresses, code hashes, and aborts.

**Token/oracle agent**

- final USDG proxy/implementation/runtime/admin/freeze evidence at release
  block;
- final Chainlink proxy/aggregator/decimals/heartbeat/failure evidence;
- Robinhood sequencer/finality model, supported uptime signal, and recovery
  policy;
- final GREEN/sGREEN identities and SavingsGreen disposition; and
- PriceDesk P0 artifact and oracle monitoring thresholds.

**Curve agent**

- final Curve source graph, compiler/settings/artifact identities and address
  provider;
- final pool/factory/implementation and clock semantics;
- final Profile 1/Profile 2 fixtures, parameters, reserve-fraction stresses,
  observation/snapshot assertions, and failure stops;
- confirmation that Curve remains non-authoritative for PSM USDG pricing; and
- conditions for any later dynamic-rate or Endaoment-stabilization promotion.

**Deployment owner**

- final integrated release and semantic plan APIs;
- exact governance/Safe/TrainingWheels bindings, with every non-governance
  `canPerformLiteAction` membership false through canary;
- executable `0600` deploy/register, `0800` disabled-proof, `0900`
  capabilities/roles/handoff, and separate global-mint activation binding;
- final monitoring/escalation/incident owners; and
- evidence schema, storage, review, and release packet identities.

No final agent result may silently enlarge authority. A conflict with the
launch-critical recommendation stops the affected gate and produces a
reconciled revision.

## 12. Owner decisions

The identifiers below are report-local decision keys mapped under canonical
`RH-D009`; they do not amend `decision-register.md` or invent new canonical
`RH-D` rows.

| Local key | Owner disposition or remaining decision | Status | Program binding |
| --- | --- | --- | --- |
| `PSM-OD-01` | 100,000 USDG idle reserve | preferred qualification candidate; production value open | `P-H04-367` |
| `PSM-OD-02` | 10 bps mint / 0 bps redeem | preferred qualification candidate; production values open | `P-H04-361/362` |
| `PSM-OD-03` | 25,000 mint / 50,000 redeem per 7,200 blocks | preferred qualification candidates; fork clock and production values open | `P-H04-363/364/365` |
| `PSM-OD-04` | allowlisted canary with operational limits; no per-user/min-max/min-output contract task now | resolved for qualification | `P-H04-366`, `RH-D001` |
| `PSM-OD-05` | no non-governance lite accounts through canary; coupled authority rejected; no shared split now | resolved for qualification; reopen `RH-D001` only if immediate guardian becomes required | `RH-D001`, CM-046/048 |
| `PSM-OD-06` | accept canonical USDG issuer/admin/upgrade/freeze risk | open on final token evidence | `RH-D009` |
| `PSM-OD-07` | accept market-price/nominal asymmetry and GREEN created outside the PSM | open | `RH-D009` |
| `PSM-OD-08` | size against circulating GREEN excluding only provably noncirculating balances; redeem-allowlist removal requires reserve resizing | methodology resolved; final quantities open | `P-H04-367` |
| `PSM-OD-09` | approve Uniswap venue and separate LP capital after final agent result | open | `B-LP-ARTIFACTS` |
| `PSM-OD-10` | 86,400-second stale value is a technical candidate/ceiling; zero-margin policy is not accepted | activation-blocking pending acceptable operating margin or separate policy | `P-H04-408`, `RH-D009` |
| `PSM-OD-11` | approve sequencer signal and recovery grace | open | `B-ORACLE-FREEZE` |
| `PSM-OD-12` | approve governance, treasury, recovery, liquidity, monitoring identities, thresholds, response times, and incident owners | open | `0900`, `P-H04-370` |
| `PSM-OD-13` | bind SavingsGreen as deployed/available or omitted/unavailable | open for final deployment plan | CM-003/048 |
| `PSM-OD-14` | preserve redemption during non-redemption incidents only while pricing, reserve, token, and accounting remain safe | resolved policy; incident application remains evidence-bound | `RH-D009` |
| `PSM-OD-15` | Curve Profile 2 observation-only; 600 preferred, 866 alternative; no launch activation | resolved posture; final qualification artifacts open | CM-017 |
| `PSM-OD-16` | no reserve movement while GREEN is outstanding without explicit incident decision and reconciled destination/evidence/rollback | resolved policy; each incident decision remains separate | CM-046/047/048 |
| `PSM-OD-17` | public access only after seven completed use-anchored intervals and the full evidence gate | criteria resolved; public approval remains separate | `P-H04-366/367` |

The largest unresolved decisions are final oracle operating margin, production
economics after fork-clock and circulating-supply evidence, governance response
times and identities, and the final Uniswap/token/oracle/SavingsGreen inputs.
The lite posture and initial allowlisted access are no longer open choices for
this canary.

### Controlling owner disposition — 30 July 2026

**Status:** Approved conservative qualification/canary architecture.  
**Authority granted:** Report, fork-matrix, and acceptance-gate disposition
only.  
**Authority not granted:** Production activation, implementation, deployment,
configuration, funding, RPC, signer/account use, Git publication, or external
mutation.

1. Deploy and register the PSM in a fully disabled state.
2. Preserve separate preparation, pre-production qualification, and production
   activation phases.
3. Preserve exact migration boundaries: `0400` price sources/PriceDesk;
   `0600` PSM deployment/registration; `0800` disabled Endaoment/PSM
   preparation; `0900` capabilities/roles/handoff; and separately authorized
   production activation outside those migrations.
4. Keep PriceDesk ID 1 as the approved Chainlink source.
5. Keep PriceDesk ID 2 exactly empty and Curve-reserved during Profile 1.
6. Reject every non-Curve source at PriceDesk ID 2.
7. Do not configure Uniswap or Curve as PSM fallback price authority.
8. Keep Chainlink as the sole PSM price authority.
9. Treat 100,000 USDG reserve, 10/0 bps mint/redeem fees, 25,000/50,000 GREEN
   mint/redeem caps, 7,200 blocks, both enforced allowlists, two canary actors,
   a 10,000 per-actor interval budget, and a 100–10,000 reserve-equivalent
   transaction range as preferred qualification candidates, not immutable
   production values.
10. Treat per-user and transaction limits as operational only; a compromised
    allowlisted actor can consume the shared bucket.
11. Do not open a per-user/min-max/min-output contract-change task now;
    reconsider only if canary evidence demonstrates need.
12. Require Robinhood fork clock qualification before freezing 7,200 as the
    production interval.
13. Resize or reject every economic candidate if final block semantics, token
    decimals, reserve identities, or circulating-supply evidence differ.
14. Configure no non-governance lite account through the initial canary.
15. Reject the coupled authority that would let the same lite account pause
    through Charlie and immediately transfer PSM reserve through Echo.
16. Do not implement a shared permission split now.
17. If immediate non-governance pause becomes a release requirement, reopen
    `RH-D001` as a separate minimal contract/security decision.
18. Bind governance response times and incident ownership explicitly before
    activation under the no-lite posture.
19. Prove pre-production redemption before any mint authority exists.
20. Disable redemption again after the pre-production proof.
21. Re-enable production redemption only under separate production-activation
    authority.
22. Prove production redemption succeeds before enabling PSM, HQ, or global
    mint authority.
23. Size reserve coverage against all circulating GREEN after excluding only
    provably noncirculating balances; do not size only against PSM-originated
    GREEN.
24. Require a separate reserve-sizing and solvency decision before removing
    the redeem allowlist.
25. Keep PSM reserve in the PSM and separate from Uniswap/Curve liquidity
    capital.
26. Do not use PSM reserve to seed or maintain a DEX pool.
27. During a non-redemption incident, preserve redemption when pricing,
    reserve, token, and accounting remain safe; disable it when the incident
    directly compromises safe redemption.
28. Do not transfer or recover reserve while GREEN remains outstanding without
    an explicit incident decision, liability reconciliation, destination,
    evidence, and rollback plan.
29. Distinguish immediate fixed-destination Echo transfer from
    governance-timelocked full-balance recovery in every runbook and test.
30. Treat the 86,400-second Chainlink stale time as a current technical
    candidate and ceiling, not accepted final production policy.
31. Do not accept the current zero publisher-lateness margin.
32. Require final feed, observed cadence, heartbeat, decimals, implementation,
    and failure evidence from the network/token/oracle qualification.
33. If the final feed cannot provide an acceptable operating margin beneath
    the ceiling, keep activation blocked pending a separately approved feed or
    ceiling policy.
34. Do not cure a Chainlink outage with a DEX fallback.
35. Require alerting before the hard boundary and explicit mint/redeem outage
    procedures.
36. Leave Uniswap venue, pool parameters, custody, and LP capital to the final
    Uniswap recommendation.
37. Keep Curve observation-only in Profile 2.
38. Use `ma_exp_time=600` as the preferred candidate, retain `866` as an
    alternative fork-test vector, and do not activate Profile 2 or Curve at
    launch.
39. Keep Teller snapshots, dynamic rates, and Endaoment stabilization as
    Profile 2 concerns that do not change launch PSM accounting or price
    authority.
40. Bind SavingsGreen client behavior explicitly as deployed/available or
    omitted/unavailable; do not infer it.
41. Preserve allowlisted access through the initial canary.
42. Require separate public-access approval after at least seven completed
    use-anchored intervals, reconciliation, reserve coverage, incident
    evidence, oracle evidence, and final circulating-GREEN analysis.
43. Never treat public access as a timer-only transition.

The complete Section 10 fork matrix and Section 13 activation acceptance
criteria are release gates. Dangerous PriceDesk-ID-2 topology, pause/recovery,
rounding, reserve-extraction, three-factor mint-authority, and deterministic
replay cases may not be waived.

## 13. Launch acceptance criteria

Launch is accepted only if:

- the final commit/tree and every artifact/address identity are frozen;
- the semantic plan maps `0400`, `0600`, `0800`, `0900`, and separate
  activation exactly, and `P-H04-370`/`B-PSM-SEQUENCE` are closed;
- all 16 fork matrix rows pass on two deterministic fresh forks;
- testnet rehearsal of the exact ceremony passes;
- canonical USDG and Chainlink evidence are current;
- PriceDesk P0 has Chainlink at ID 1, ID 2 exactly empty/reserved for Curve,
  no pending non-Curve second registration, and no USDG DEX fallback;
- Uniswap final artifacts and depth meet the approved separate liquidity gate;
- Curve absence is proven safe and near-term Curve scenarios remain recorded;
- the PSM is configured exactly, yield and Underscore are zero, and both
  allowlists are enforced;
- constructor values were asserted rather than re-set and there is no failed
  or pending no-op action;
- `100,000 USDG` funding reconciles exactly;
- total initial/circulating GREEN, allowlisted-sender control, and reserve
  coverage are bound;
- pre-production redemption succeeds and is disabled again; production
  redemption is separately approved and succeeds before any PSM/HQ/global
  mint enablement;
- the PSM HQ tuple is the final tuple mutation;
- the complete tuple and disabled-route set is re-read before global mint;
- global mint is the last launch mutation;
- every non-governance lite-action membership is false, and governance
  response times and incident ownership are bound and tested;
- both reserve-extraction paths, paused-state asymmetry, destination, and
  full-balance semantics are exercised;
- final oracle evidence proves acceptable operating margin beneath the stale
  ceiling, or a separate feed/ceiling policy is approved; the current
  zero-margin candidate is not accepted;
- monitors, pages, governance pause/unpause, recovery, sequencer, oracle,
  token, reserve, cap, use-anchored interval, Uniswap, and accounting
  procedures are exercised;
- there are no unexpected approvals, pending actions, expired actions,
  untracked ceremony inputs, Base addresses, or history dependencies;
- the independent reviewer signs the evidence digest; and
- the owner separately authorizes the exact activation ceremony.

### Post-activation monitoring

For the first hour, monitor continuously; for the first 24 hours, review at
least every 15 minutes; for the remaining seven completed use-anchored buckets,
review at least hourly with daily reconciliation.

Alert and page on:

- any PSM/HQ/global mint/pause/allowlist/cap/fee/interval/yield change;
- any pending Echo, Charlie, Chainlink, PriceDesk, HQ, or governance action;
- any `canPerformLiteAction` membership change;
- any Echo PSM-to-EndaomentFunds call or Charlie/Department recovery,
  including destination and full-balance effect;
- reserve thresholds or any accounting difference;
- mint/redeem event, fee, bucket, or supply mismatch;
- USDG proxy/implementation/admin/pause/freeze/transfer drift;
- Chainlink aggregator/round/answer/age/decimals drift;
- sequencer/finality loss or recovery grace;
- PriceDesk source/order change or any nonzero/pending ID-2 registration;
- nonzero Underscore registry or yield position;
- unexpected PSM approval or reserve transfer;
- Uniswap implementation/ownership/range/depth/price divergence;
- Curve registration, snapshot, dynamic-rate, or stabilization activity; and
- any Base address or history path entering a Robinhood artifact.

Do not auto-change fees, caps, rates, liquidity, allowlists, or price sources
from monitoring. Automation may alert or submit a pre-approved pause only
within the final guardian design.

## 14. Explicit non-actions

This proposal does not:

- deploy, register, configure, fund, pause, unpause, or activate the PSM;
- enable or disable global minting;
- create, initialize, or fund a Uniswap or Curve pool;
- configure PriceDesk, Chainlink, dynamic rates, Teller snapshots, or
  Endaoment stabilization;
- access RPC, accounts, keys, signers, Safes, custody, or external state;
- execute testnet, fork, migration, or ceremony transactions;
- create Robinhood migrations or history;
- modify contracts, ABIs, defaults, manifests, blueprints, inventories,
  existing documentation, or tests;
- add this owner-specified qualification namespace to `START-HERE.md`,
  `AGENT-HANDOFF.md`, or `status.yaml`; that integration remains a separately
  authorized documentation action;
- copy or execute Base migrations/history;
- select final external addresses or operator identities;
- approve a shared contract change;
- promote Curve to PSM authority;
- treat Uniswap as a PSM oracle;
- use PSM reserve as launch-liquidity capital;
- erase the near-term Curve Profile 1/Profile 2 scenarios;
- treat elapsed time or passing documentation as activation authority; or
- authorize staging, commit, push, deploy, funding, RPC, signer, release, or
  external publication.
