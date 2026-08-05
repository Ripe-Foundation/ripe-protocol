# Robinhood Uniswap price-source decision

**Frozen authority:** Ripe `rh` commit
`0d5994aa78f9d6f35b59bd7a2bc70fa18706e693`, tree
`b68dffdddbdc7c5ae8423db049099c1632b478c9`.

**Assessment date:** 30 July 2026.

**Scope:** read-only architecture, product, oracle, and ecosystem decision. No
RPC, signer, pool, deployment, configuration, migration, or external-state
action was used. External facts below come only from official Robinhood,
Uniswap, Chainlink, and Arbitrum documentation or official Uniswap deployment
repositories. Repository facts are bound to the frozen authority above.

**Controlling owner disposition:** the report-closure disposition dated
30 July 2026 supersedes the frozen plan's earlier LP-admission and venue
sequencing where this report says so. It does not rewrite the historical frozen
tree, authorize pool creation/funding, activate an asset, or authorize a
contract.

## 1. Executive decision

**Robinhood launch does not need a new Uniswap-based Ripe price-source
contract.** The frozen launch architecture intentionally leaves PriceDesk
source slots 2–5 empty, keeps Chainlink in source slot 1, omits Curve and
Aerodrome, and defers a GREEN/RIPE local price adapter. RIPE-market-price-
dependent features remain disabled. Ordinary RIPE mint and BondRoom payout
quantities are governed protocol quantities rather than market-derived
RIPE/USD values. Rewards are a configuration-dependent exception:
`Lootbox` can value deposit assets through PriceDesk, but Robinhood launch
globally disables points with `arePointsEnabled=false` and `ripePerBlock=0`.
A public Uniswap market can therefore be a liquidity venue and an off-chain
monitoring signal without becoming protocol oracle authority at launch.

The frozen tree historically calls GREEN/USDG LP and RIPE/WETH LP launch
deposit tokens with `ltv=0`, ordinary Teller routing, and CM-024
`SimpleErc20` custody. The controlling owner disposition now supersedes that
admission timing: **neither LP token is admitted as a Ripe deposit asset at
launch; both admissions move to Profile 2.** Pool preparation is separate from
protocol admission. Uniswap V2 is the selected candidate for an externally
held RIPE/WETH launch-liquidity canary because its LP claim is ERC-20. GREEN/USDG
liquidity remains governed by the Profile 2 Curve qualification plan; do not
create a redundant GREEN/USDG Uniswap V2 launch pool absent a later, separate
owner decision. V3 and V4 positions remain unsuitable for the current
`SimpleErc20` LP roles without a new wrapper or custody architecture.

The launch recommendation is:

1. use the existing `ChainlinkPrices` path for each approved launch-critical
   Stock Token and USDG price, after the exact proxy, decimals, quote,
   heartbeat, stale-time ceiling, market-hours behavior, and outage policy are
   frozen and fork-qualified;
2. do not register a Uniswap source in PriceDesk;
3. use Uniswap V2 only as the candidate RIPE/WETH launch-liquidity canary,
   externally held and not admitted to Ripe;
4. leave GREEN/USDG to the Profile 2 Curve qualification plan and do not
   recommend a redundant launch Uniswap pool;
5. move both LP-token admissions to Profile 2. If either is later admitted,
   keep `SimpleErc20`, `ltv=0`, no PriceDesk feed, and require the complete
   negative-route package plus separate activation authority;
6. do not use Uniswap as a Chainlink fallback; and
7. keep every RIPE-market-price-dependent feature off until a separate owner,
   risk, security, pool, custody, and exposure decision is approved.

If a follow-on feature later makes an on-chain RIPE market price
security-relevant while RIPE/WETH remains on V2, the compatible candidate
is a **new Robinhood-specific Uniswap V2 cumulative-price TWAP source** over the
same canonical pair. It must maintain external checkpoints, use an
authoritative quote price, enforce reserve/depth and update-freshness guards,
and never return spot. V3 has the technically stronger native oracle primitive,
but selecting it would reopen the ERC-20 LP-deposit architecture. Do not create
a separate thin V3 “oracle pool,” reuse `AeroRipePrices`, generalize
`CurvePrices`, or build a generic multi-DEX source. The conditional V2 design
is specified in section 8; it is not a launch requirement or implementation
authorization.

**Version decision.**

- **RIPE/WETH launch-liquidity candidate under the owner disposition: V2.**
  Its pair claim is ERC-20, but that token remains externally held rather than
  admitted to Ripe until Profile 2.
- **GREEN/USDG:** no Uniswap launch venue is selected. Its liquidity and any LP
  artifact are governed by the Profile 2 Curve qualification plan.
- **Best native Uniswap oracle primitive: V3**, because V3 core has a built-in
  observation array and exposes tick and seconds-per-liquidity cumulatives.
  It is not the RIPE/WETH venue recommendation and cannot serve a later
  `SimpleErc20` LP role unless the owner separately changes the custody/wrapper
  architecture.
- **V4:** not appropriate for this oracle decision. Uniswap states that V4 has
  no built-in oracle; a particular audited hook would add hook identity,
  upgrade, and custom-state assumptions, while its position remains
  incompatible with the possible Profile 2 `SimpleErc20` deposit role.

**Minimum depth decision.** There is no defensible universal “minimum TVL.”
No DEX price may be security-relevant until a parameterized attack simulation
shows that the least-cost manipulation across the complete oracle window,
including fees, arbitrage, range movement, MEV, liquidity withdrawal, and
sequencer conditions, exceeds a risk-owner-selected multiple of the maximum
value extractable from Ripe during that window. A technical reserve or
liquidity number is a tripwire, not this economic proof.

For RIPE/WETH launch-liquidity planning, `50,000 USD` per side is only a
provisional canary capital envelope. The earlier `25,000 USD` executable depth
within `+/-1%` promise is rejected. Including the 30 bp V2 fee, `50,000 USD`
per side supports only about `355 USD` of one-direction input at no more than
1% average execution-price deviation. A `25,000 USD` input at that deviation
would require about `3.53 million USD` on the input-reserve side, but that
calculation is **not an approved funding commitment**. Replace the depth
promise with later owner-approved maximum trade size, acceptable slippage,
retained reserves, monitoring, and withdrawal criteria. PSM reserves are not
LP funding capital. The first-draft future-oracle security multiple is `S=5`,
but no DEX price becomes security-relevant until exposure `E` is fixed and
`C_attack > 5E` or an approved replacement is proved.

## 2. Verified Robinhood Uniswap deployment facts

Robinhood documents Robinhood Chain mainnet as chain ID `4663`, built on
Arbitrum Dedicated Blockchains with first-come-first-served sequencing, and
identifies Uniswap as the public DEX and Chainlink as the oracle provider.
Official references:
[Robinhood Chain overview](https://docs.robinhood.com/chain/),
[connection details](https://docs.robinhood.com/chain/connecting/), and
[contract addresses](https://docs.robinhood.com/chain/contracts/). Robinhood's
documented WETH is `0x0Bd7D308f8E1639FAb988df18A8011f41EAcAD73`
and USDG is `0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168`.

The official Uniswap
[unified deployment feed](https://developers.uniswap.org/deployments.json) was
generated on 15 July 2026 from the official `Uniswap/contracts` repository at
commit `37936185dee7decf681360ec799c124e0e034672`. At that snapshot its chain
`4663` records cover V4, not V2 or V3. The V2 and V3 facts below come from their
version-specific official pages. These are deployment facts, not proof that a
RIPE pool exists, has liquidity, or is safe as an oracle.

| Version | Role | Official Robinhood mainnet deployment | Primary source |
| --- | --- | --- | --- |
| V2 | Factory | `0x8bceaa40b9acdfaedf85adf4ff01f5ad6517937f` | [V2 deployments](https://developers.uniswap.org/docs/protocols/v2/deployments) |
| V2 | Router02 | `0x89e5db8b5aa49aa85ac63f691524311aeb649eba` | [V2 deployments](https://developers.uniswap.org/docs/protocols/v2/deployments) |
| V2 | Manager / quoter / position manager | None in the V2 deployment model | [V2 deployments](https://developers.uniswap.org/docs/protocols/v2/deployments) |
| V3 | Factory | `0x1f7d7550b1b028f7571e69a784071f0205fd2efa` | [V3 Robinhood deployments](https://developers.uniswap.org/docs/protocols/v3/deployments/v3-robinhood-chain-deployments) |
| V3 | SwapRouter02 | `0xcaf681a66d020601342297493863e78c959e5cb2` | [V3 Robinhood deployments](https://developers.uniswap.org/docs/protocols/v3/deployments/v3-robinhood-chain-deployments) |
| V3 | UniversalRouter | `0x8876789976decbfcbbbe364623c63652db8c0904` | [V3 Robinhood deployments](https://developers.uniswap.org/docs/protocols/v3/deployments/v3-robinhood-chain-deployments) |
| V3 | QuoterV2 | `0x33e885ed0ec9bf04ecfb19341582aadcb4c8a9e7` | [V3 Robinhood deployments](https://developers.uniswap.org/docs/protocols/v3/deployments/v3-robinhood-chain-deployments) |
| V3 | NonfungiblePositionManager | `0x73991a25c818bf1f1128deaab1492d45638de0d3` | [V3 Robinhood deployments](https://developers.uniswap.org/docs/protocols/v3/deployments/v3-robinhood-chain-deployments) |
| V3 | TickLens | `0x7dfd4f31be6814d2906bde155c3e1b146eac1468` | [V3 Robinhood deployments](https://developers.uniswap.org/docs/protocols/v3/deployments/v3-robinhood-chain-deployments) |
| V3 | InterfaceMulticall | `0x282a3c4d320cc7f0d5eaf56b8029e4b88338f0a3` | [V3 Robinhood deployments](https://developers.uniswap.org/docs/protocols/v3/deployments/v3-robinhood-chain-deployments) |
| V4 shared infrastructure | Permit2 | `0x000000000022D473030F116dDEE9F6B43aC78BA3` | [V4 deployments](https://developers.uniswap.org/docs/protocols/v4/deployments) |
| V4 | PoolManager | `0x8366a39cc670b4001a1121b8f6a443a643e40951` | [V4 deployments](https://developers.uniswap.org/docs/protocols/v4/deployments) |
| V4 | UniversalRouter | `0x8876789976decbfcbbbe364623c63652db8c0904` | [V4 deployments](https://developers.uniswap.org/docs/protocols/v4/deployments) |
| V4 | Quoter | `0x8dc178efb8111bb0973dd9d722ebeff267c98f94` | [V4 deployments](https://developers.uniswap.org/docs/protocols/v4/deployments) |
| V4 | PositionManager | `0x58daec3116aae6d93017baaea7749052e8a04fa7` | [V4 deployments](https://developers.uniswap.org/docs/protocols/v4/deployments) |
| V4 | PositionDescriptor | `0x9639443158e8c5efa35bd45287bf2effd3d8dc06` | [V4 deployments](https://developers.uniswap.org/docs/protocols/v4/deployments) |
| V4 | StateView | `0xf3334192d15450cdd385c8b70e03f9a6bd9e673b` | [V4 deployments](https://developers.uniswap.org/docs/protocols/v4/deployments) |
| V4 | ReservesLens | `0x0000001b173C3bbF3984D417d8614E3eed34865B` | [V4 deployments](https://developers.uniswap.org/docs/protocols/v4/deployments) |
| V4 | Factory | None; pools are keyed state inside the singleton `PoolManager` | [V4 deployments](https://developers.uniswap.org/docs/protocols/v4/deployments) |

Router and quoter deployments are integration conveniences; an oracle adapter
should read the exact pool or PoolManager state and should not price through a
router quote.

The versions have different pool identities:

- V2 uses one pair contract per sorted token pair. The pair has one fee model
  and cumulative prices. Pair creation is controlled by the factory, and the
  pair claim is an ERC-20 token compatible with the frozen architecture's
  `SimpleErc20` model if Profile 2 later authorizes admission.
- V3 uses one pool per sorted token pair and fee tier. Fee tier fixes tick
  spacing through the factory. Liquidity positions are NFTs managed through
  the `NonfungiblePositionManager`. A pool contains the built-in observation
  array used by `observe`.
- V4 uses a `PoolKey`: sorted currencies, fee, tick spacing, and hook address.
  Pool state lives in `PoolManager`; there is no pool contract or V4 factory.
  Hooks may change fees or accounting and may implement oracle storage.
  Official [V4 pool creation documentation](https://developers.uniswap.org/docs/protocols/v4/guides/create-pool)
  makes all of those fields part of pool identity.

No official source reviewed here states that a RIPE pair or pool already
exists. No RPC was permitted or used. Pair existence, initialization,
liquidity, observation history, position custody, and trading activity are
therefore unresolved owner/fork-qualification inputs, not inferred deployment
facts.

## 3. Protocol price requirements

### Launch-critical prices

The frozen repository assigns PriceDesk routing to CM-015 and keeps it
initially Chainlink-focused. CM-016 reuses `ChainlinkPrices` for official Stock
Token feeds and an approved USDG feed. CM-017 and CM-050 omit Curve and
Aerodrome. CM-054 explicitly states that there is no approved GREEN/RIPE local
price and keeps dependent functionality off:
`docs/chains/rh/component-matrix.md:108-113,128-147,251-264`.
The deployment-support record repeats that GREEN- and RIPE-market-price-
dependent features remain disabled and that future adapter slots must not
select a market:
`docs/chains/rh/track-7-robinhood-deployment-support.md:285-297,611-621`.

The blueprint keeps Chainlink at PriceDesk semantic slot 1, reserves slots 2–5
as empty, omits unsupported fallback and WETH-feed choices, and defers a future
GREEN/RIPE adapter behind the oracle freeze. The frozen tree's exact LP
artifact and oracle bindings for GREEN/USDG and RIPE/WETH were blocked owner
inputs:
`config/robinhood_blueprint.py` entries `S-015-RESERVED-SLOTS`,
`S-016-FEED-REG`, `S-016-SOURCE-FALLBACK`, `S-016-WETH-FEED`,
`S-054-ADAPTER`, `I-GREEN-USDG-LP`, and `I-RIPE-WETH-LP`.
The parameter manifest has no selected Uniswap integration and does not
substitute zero addresses for an approved LP/oracle artifact.

That is historical frozen-plan language, not the controlling admission
sequence. The M0 record described GREEN/USDG LP and RIPE/WETH LP as launch
deposit tokens with legitimate `ltv=0`, ordinary Teller routing, and unresolved
factory, pool, oracle, artifact, runtime, address, and composed-route gates:
`docs/chains/rh/track-6-s6-track-7-h4-defaults-parameters.md:361-372` and
`docs/chains/rh/stock-token-vault-change-specification.md:6538-6548`.
Their CM-024 dependency binds them to the registered `SimpleErc20` vault, not
an NFT vault: `config/robinhood_blueprint.py:4577-4585,4783-4790`. The owner
disposition moves both deposit-token admissions to Profile 2. It separately
permits preparation of an externally held RIPE/WETH V2 liquidity canary at
launch and leaves GREEN/USDG liquidity to the Profile 2 Curve plan.

Robinhood's official
[oracle guidance](https://docs.robinhood.com/chain/oracles-and-price-feeds/)
states that Stock Tokens use standard Chainlink `AggregatorV3Interface` feeds,
that the Stock Token price incorporates the applicable multiplier, and that
Stock Token feeds operate 24/5. It requires consumers to address staleness,
sequencer status, issuer `oraclePaused` state, and corporate-action handling.
Robinhood also states that `oraclePaused` is advisory and is not enforced
on-chain. The existing `ChainlinkPrices` adapter does not read that flag.
Accordingly, “Chainlink covers the feed” is not “Ripe has a complete
market-hours, issuer-pause, or corporate-action control”; an independent
monitor and explicit pause/response policy remain launch-critical.
The official
[Stock Token integration guide](https://docs.robinhood.com/chain/building-with-stock-tokens/)
also distinguishes launch RFQ liquidity from AMM liquidity. A Uniswap pool is
not the authoritative Stock Token price source.

For USDG, the repository's primary-source record identifies the official
Robinhood mainnet Chainlink USDG/USD proxy
`0x61B7e5650328764B076A108EFF5fa7282a1B9aD2`, 8 decimals, an 86,400-second
heartbeat, and a 0.5% deviation threshold. That standard proxy is compatible
with `ChainlinkPrices` without a new adapter:
`docs/chains/rh/usdg-public-evidence.md:148-216`. The PSM remains disabled
until the feed and all PSM gates are approved; price compatibility is not PSM
activation authority.

Accordingly, an authoritative source can cover every **selected**
launch-critical price:

- approved Stock Tokens: official Chainlink Stock Token feeds, qualified by
  separate 24/5, advisory `oraclePaused`, corporate-action, staleness, and
  sequencer controls;
- USDG, if the PSM is later activated: the reviewed Chainlink USDG/USD feed;
- RIPE: no launch-critical market-price consumer while the recorded
  price-dependent features remain disabled;
- GREEN: no fabricated market peg and no launch-critical local-market-price
  consumer under the frozen omission posture;
- WETH: no independent launch PriceDesk feed has been selected, and none is
  required merely because an externally held RIPE/WETH liquidity pool exists.
  Any future RIPE valuation, LP valuation, USD-value reward, borrowing-power,
  or other valuation-dependent feature must stop until an approved WETH/USD
  authority and its complete oracle/fork qualification are frozen;
- GREEN/USDG LP: not admitted at launch. Its venue/artifact and possible later
  admission are Profile 2 Curve decisions, not a reason to create a launch
  Uniswap pool; and
- RIPE/WETH V2 LP: may be externally held for launch liquidity but is not a
  launch Ripe deposit asset. Any Profile 2 admission must use `SimpleErc20`,
  retain `ltv=0`, assign no PriceDesk feed, prove no valuation-dependent route,
  pass the complete negative-route package, and receive separate activation
  authority. A RIPE TWAP source alone would not price the LP token.

This is a conditional completeness conclusion: it depends on preserving the
recorded feature omissions and keeping both LP tokens unadmitted at launch. It
does not claim that Chainlink publishes a RIPE or LP-token feed.

### RIPE pricing and liquidity assumptions

The inspected production code does not use a market RIPE price to determine
the ordinary RIPE mint quantity in `BondRoom`, Human Resources, `Lootbox`, or
vault reward claims. For example, `BondRoom` calculates a governed
`totalRipePayout` and mints that quantity; it does not query PriceDesk for
RIPE/USD: `contracts/core/BondRoom.vy:186-227`.

That statement is limited to mint quantity. `Lootbox` has a separate deposit
points path: when an asset's `stakersPointsAlloc == 0`, it calls
`PriceDesk.getUsdValue` to refresh the vault asset's points weight; when the
allocation is nonzero it skips that valuation:
`contracts/core/Lootbox.vy:775-836`. Robinhood launch globally disables points
with `arePointsEnabled=false` and `ripePerBlock=0`
(`docs/chains/rh/track-6-s6-track-7-h4-defaults-parameters.md:368-372`).
The call also uses PriceDesk's non-raising default and accepts zero. Thus no
market price is required for launch rewards, but that is a configuration
conclusion, not an inherent property of `Lootbox`. Any rewards promotion must
re-evaluate RIPE and LP price reachability and source failures.

CreditEngine skips `ltv=0` assets before asking PriceDesk for collateral value
(`contracts/core/CreditEngine.vy:732-744`). Zero LTV does not make every other
consumer inert: Deleverage and AuctionHouse contain raising PriceDesk calls on
reachable asset routes. Launch avoids that issue by not admitting either LP
token. Before any Profile 2 admission, composed tests must prove that the asset
cannot enter borrowing-power, liquidation-value, rewards, points, solvency,
PSM, or any other valuation-dependent route. RIPE/WETH liquidity may still
help price discovery and exit while its LP token remains externally held.

Base deployment behavior cannot be transplanted by analogy. Base created
Curve liquidity/reference integrations through
`migrations/base-mainnet/2001_CurvePools.py`, deployed `CurvePrices` through
`2025080800_CurvePrices.py`, and later deployed `AeroRipePrices` against
`RipePoolAero` through `2025082000_AeroPrices.py`. Robinhood's component
matrix deliberately omits all three pools/sources. Historical Base operation
establishes integration provenance only; it does not establish Robinhood pool
identity, liquidity, manipulation resistance, or oracle suitability.

### Proper uses of a Uniswap price

At launch, Uniswap evidence is useful for:

- public liquidity and price discovery;
- off-chain monitoring of RIPE price, spreads, depth, volume, and LP
  concentration;
- comparing DEX execution to any governance or treasury reference;
- warning on pool initialization, range exhaustion, liquidity withdrawal, or
  anomalous movement; and
- informing a later owner decision.

It is not useful as an automatic launch fallback. A follow-on on-chain price
could support a bounded governance sanity check or circuit breaker, or could
support protocol accounting only after exposure and liquidity proof. An
off-chain monitor is the lowest-trust, lowest-blast-radius first use because a
monitoring failure does not change solvency or settlement.

## 4. Existing price-source compatibility

### PriceDesk and the common interface

Every current price source implements `interfaces/PriceSource.vyi`, including
`getPrice`, `getPriceAndHasFeed`, `hasPriceFeed`, snapshot, priced-asset, and
timelocked feed-change functions. This is ABI compatibility, not semantic
interchangeability.

`PriceDesk._getPrice` reads MissionControl's global stale time and priority
IDs, asks priority sources first, and returns the first nonzero result. If none
returns a price, it scans all remaining registry sources by registry ID. If at
least one source reports that it has a feed but all return zero,
`_shouldRaise=true` reverts with `has price config, no price`:
`contracts/registries/PriceDesk.vy:134-187`. PriceDesk does not compare
sources, take a median, apply a deviation bound, distinguish “primary failed”
from “fallback valid,” or know why a source returned zero. Registering a
Uniswap adapter anywhere in the registry can therefore make it an implicit
fallback even if it is not listed as a priority source. Monitoring-only means
**do not register it in PriceDesk**.

Tests cover MissionControl priority-array validation, ordering, de-duplication,
and the maximum of ten sources
(`tests/data/test_mission_control.py:784-799,917-929,1063-1074` and
`tests/config/test_switchboard_alpha.py`). The current suite has no
Robinhood-Uniswap composition tests for primary failure, fallback promotion,
cross-source deviation, or correlated manipulation.

### `AeroRipePrices` cannot be reused safely

`AeroRipePrices` is not a generic constant-product or TWAP adapter. Its
Aerodrome-specific and source-specific assumptions are:

1. The immutable pool implements Aerodrome Classic's nonstandard
   `tokens()` and `getReserves()` interface. Uniswap V2 uses `token0()`,
   `token1()`, and `getReserves()`; V3 uses `token0()`, `token1()`,
   `slot0()`, `liquidity()`, `observations()`, and `observe()`; V4 state lives
   in `PoolManager`. The existing call surface would revert or misdecode.
2. It assumes the immutable pool is the intended RIPE/WETH pool but does not
   verify it against an Aerodrome factory or assert that RIPE is either token.
   If RIPE is not token0, it simply treats token0 as the alternate asset.
3. It converts the instantaneous reserve ratio to USD by recursively asking
   PriceDesk for the other token's price. It has no factory, invariant-style,
   fee, pool-code, liquidity, or quote-source validation.
4. Its “weighted price” is an equal-weight arithmetic mean of permissioned,
   transaction-triggered snapshots. It is neither time weighted nor liquidity
   weighted. Snapshot spacing can vary.
5. It returns `min(current reserve spot, snapshot average)`. Upside snapshots
   are throttled, but downside movement is not. A temporary downward reserve
   manipulation can immediately lower the returned price.
6. It ignores PriceDesk/MissionControl's `_staleTime`, uses its own
   `block.timestamp` settings, and if every stored snapshot is stale falls back
   to `lastSnapshot.price` rather than failing closed.
7. Any valid Ripe address can trigger a snapshot through PriceDesk. The system
   therefore trusts caller timing as well as pool state.
8. Configuration caps snapshot count at 25, delay at one week, and upside
   deviation at 100%, but imposes no ceiling on local stale time.

These properties are visible at
`contracts/priceSources/AeroRipePrices.vy:27-44,72-103,114-146,181-229,288-345,351-427`.
The Base-only tests verify positive live fork pricing, pool reserves, snapshot
delay and rotation, arithmetic averaging, staleness filtering, and upside
throttling. They do not prove economic manipulation cost, same-block
resistance, observation independence, factory provenance, liquidity-removal
safety, sequencer downtime behavior, or MEV resistance:
`tests/priceSources/test_aero_ripe.py`.

Adapting this contract would require replacing its pool interface, pricing
primitive, provenance, snapshot model, failure behavior, liquidity checks, and
tests. That is a new contract disguised as reuse and would retain dangerous
names and assumptions. Reuse is rejected.

### `CurvePrices` should not be generalized

`CurvePrices` encodes Curve semantics rather than a reusable “DEX price”
abstraction. It depends on Curve's Address Provider and MetaRegistry; registry
handler IDs; pool discovery; `get_virtual_price`, `price_oracle`, `lp_price`,
`balances`, and underlying-coin rules; and distinct StableSwap and CryptoSwap
valuation branches. Its separate GREEN reference-pool feature uses
block-number snapshots and danger-block accumulation.

Uniswap has none of that registry graph or LP-token valuation model. V3 and V4
positions are nonfungible, concentrated-liquidity positions; V4 pools are
state keys in a singleton. Generalizing `CurvePrices` would either fill it with
protocol branches or create a broad adapter framework whose shared interface
hid distinct trust and failure behavior. It would also risk carrying Base
`block.number` snapshot logic onto Robinhood, where the documented inherited
number is an L1 estimate rather than a child-block counter. Keep
`CurvePrices` unchanged and omitted on Robinhood. If needed, build a small
source around one exact Uniswap version and pool.

### Chainlink coverage and limits

`ChainlinkPrices` validates feed decimals and rounds, rejects nonpositive
answers, zero or incomplete rounds, future timestamps, and stale data under a
nonzero effective threshold, then normalizes to 18 decimals:
`contracts/priceSources/ChainlinkPrices.vy`. The effective threshold is the
maximum of the global and feed-specific values; configuration must therefore
prove a positive approved ceiling rather than assume the feed-specific value
tightens a looser global value.

The adapter does not check a sequencer-uptime feed. Robinhood tells oracle
consumers to check sequencer status, but Chainlink's current official
[L2 sequencer feed list](https://docs.chain.link/data-feeds/l2-sequencer-feeds)
does not list a Robinhood feed or address. No address may be invented. This is
an unresolved launch safety/operations decision for all Chainlink consumers:
obtain an official supported address or explicitly freeze a conservative
pause, restart-grace, and monitoring policy. A Uniswap fallback would not fix
sequencer downtime because the Uniswap observations and protocol calls share
the same sequencer and clock.

## 5. Threat model

The protected assets are protocol solvency, collateral valuation, liquidation
ordering, issuance/redemption quantities, treasury funds, governance
decisions, and users relying on availability. The adversary may trade and
provide/remove liquidity, split actions across transactions or blocks, choose
positions and ranges, observe pending order flow, trigger public pool writes,
control or compromise an LP key, exploit source ordering, and act before or
after sequencer interruption. The adversary does not need to permanently hold
the manipulated price if value can be extracted while the oracle accepts it.

### Low liquidity and manipulation

Spot price is unacceptable for any security-relevant use. In V2 the attacker
moves reserves; in V3/V4 the attacker can move price across concentrated
ranges, and quoted TVL outside the active range may offer no defense. A longer
TWAP makes an attacker maintain distortion for longer but does not guarantee
safety in an inactive or attacker-seeded market. Fees, arbitrage, inventory,
range topology, and the action's maximum extractable value determine the
economic cost.

V3's harmonic mean liquidity is useful as a window-wide tripwire, but Uniswap's
[V3 oracle guide](https://developers.uniswap.org/docs/protocols/v3/concepts/price-oracles)
warns that tick and in-range liquidity can be entirely uncorrelated. Liquidity
can also be added and removed. A threshold cannot replace an attack simulation
or controlled custody of the liquidity counted in the security case. V2 has no
harmonic-liquidity oracle; reserve floors and full-range constant-product
attack simulation are required instead.

### MEV and sequencing

Robinhood documents first-come-first-served sequencing rather than priority
gas auctions. That changes ordering mechanics; it does not eliminate MEV,
private order advantages, multi-transaction manipulation, or sequencer
discretion/failure. A spot read in the same transaction or block can still
reflect an adversarial state. A full-window cumulative-price TWAP reduces
single-block influence. It must not use the latest spot as a substitute on
failure.

### Sequencer downtime, finality, and clocks

Robinhood's
[Ethereum differences](https://docs.robinhood.com/chain/differences-from-ethereum/)
state that EVM `block.number` is an L1 estimate that updates periodically and
that `ArbSys(0x64).arbBlockNumber()` provides the actual L2 number. Therefore:

- do not port Curve's block-number snapshot window or “danger blocks” to a
  Robinhood oracle;
- V3 observations correctly use seconds and `block.timestamp`, not the
  inherited number; and
- a sequencer outage or restart still affects timestamp advancement, pool
  writes, and access. The source must fail closed during an outage and for an
  approved grace period after recovery.

Robinhood's
[finality documentation](https://docs.robinhood.com/chain/transaction-finality/)
distinguishes soft sequencer confirmation from later data posting and Ethereum
finality. Governance or risk operations must decide whether a monitoring or
accounting action may rely on soft confirmation and how to respond to a
reorganization or delayed posting.

### Stale and sparse observations

V3 stores observations at most once per block, initially has only one slot,
and populates additional slots only when swaps or position modifications write
the pool. Anyone can raise `observationCardinalityNext`, but allocation does
not create history. `observe` can synthesize a counterfactual current
observation from the last written tick/liquidity. A quiet pool can therefore
produce a mathematical TWAP while its last actual write is old. The adapter
must separately verify:

- the requested window is fully covered by initialized observations;
- the latest actual observation is recent enough;
- observation cardinality and initialized count are sufficient;
- the pool has completed a full bootstrap window after initialization; and
- the harmonic-liquidity floor holds across the same window.

Official details are in Uniswap's
[V3 price-oracle documentation](https://developers.uniswap.org/docs/protocols/v3/concepts/price-oracles)
and [V3 SDK oracle guide](https://developers.uniswap.org/docs/sdks/v3/guides/price-oracle).

V2 instead exposes cumulative prices but does not store a historical
observation ring. A Ripe V2 adapter must checkpoint the cumulative value and
timestamp in its own storage. A missed or too-recent checkpoint, zero elapsed
time, timestamp-wrap error, absent completed average, or stale completed
average must return unavailable. An instantaneous reserve read is never a TWAP
and cannot repair a missing checkpoint.

### Initialization, replacement, and liquidity removal

The initial pool price is established by initial liquidity. A pair with an
incorrect initial ratio, attacker liquidity, or insufficient elapsed
checkpoint history must not activate an oracle. The exact factory-derived pair
must be immutable; changing the pair requires a newly reviewed adapter rather
than a mutable pointer. Activation requires an independently checked initial
price, full TWAP-window aging, normal trading, and depth proof.

V3 positions are NFTs. Whoever controls the position-manager NFT can withdraw
or move liquidity. A protocol security argument cannot count “protocol-owned”
liquidity without exact NFT IDs, owner/custodian, range, withdrawal authority,
timelock, emergency policy, and monitoring. Third-party liquidity may vanish
without notice. A withdrawal can reduce manipulation cost before the oracle's
next use even if historical harmonic liquidity remains high, so current
in-range depth and a withdrawal shock test are both required.

For the candidate RIPE/WETH V2 launch canary, LP custody is an ERC-20 balance
rather than an NFT. That preserves compatibility with a possible later
`SimpleErc20` admission but does not admit the token at launch or solve
withdrawal risk: the externally held LP-token owner can burn the pair claim and
remove reserves. Exact amount, custodian, approval surface, transfer
restrictions, withdrawal delay, minimum retained reserves, monitoring, and
emergency-unwind ordering remain required before creation or funding.

### Source-order and governance failure

PriceDesk's first-nonzero behavior can silently promote a registered Uniswap
source when Chainlink returns zero. Governance can also change priorities,
source registry entries, stale ceilings, pool parameters, and LP custody.
Timelocks provide reaction time only if events are monitored and emergency
actions are tested. The safest launch configuration removes the unwanted
fallback path by not registering the Uniswap source at all.

## 6. Option comparison

“Manipulation cost” below is qualitative because no RIPE pool, ranges,
liquidity, exposure, or attack model is frozen. “Small/medium/large” code and
gas are relative to the alternatives, not measured deployment values.

### Security and operations

| Option | Trust assumptions | Manipulation cost | Liveness and failure | Governance risk | Clock dependency |
| --- | --- | --- | --- | --- | --- |
| **No Uniswap price source** | Chainlink for selected launch assets; RIPE-price features stay off | N/A for protocol; DEX cannot affect accounting | Best protocol liveness for omitted RIPE functions; unavailable RIPE price by design | Lowest; omission must be preserved | Chainlink timestamps and unresolved sequencer policy only |
| **Uniswap liquidity plus monitoring evidence** | RIPE/WETH V2 users trust execution; external custodian holds LP; operators interpret evidence; Ripe does not consume it | Market-dependent, but no direct protocol extraction path | Trading/monitor can fail without protocol oracle failure | Pool/custody choices affect users, not PriceDesk or deposit admission | Monitor uses chain timestamps and activity |
| **Off-chain monitoring only** | Monitor/indexer/RPC/operator alerting; on-chain protocol independent | No direct protocol extraction; alerts can be spoofed or delayed | Alert availability only; fail-open for protocol, fail-loud operationally | Alert thresholds and response runbook | RPC, sequencer, timestamp, finality |
| **V2 TWAP source** | Exact V2 factory/pair; adapter checkpoint callers; quote source | Window-dependent; weak in thin pair; full-range liquidity | Needs regular external checkpoints; missed checkpoint makes source unavailable/stale | Checkpoint, window, quote source, pool/exposure config | Pair cumulative timestamp plus adapter checkpoint cadence |
| **V3 TWAP source** | Exact factory/pool/fee; V3 core observations; quote source; sufficient activity/depth; changed LP deposit architecture | Window- and range-dependent; strongest native Uniswap candidate when liquid | `observe` fails if history insufficient; must reject stale writes/low liquidity/outage | Window, bounds, pool, quote, NFT/wrapper custody, PriceDesk registration | Pool `block.timestamp`; sequencer outage/grace |
| **V4-aware source** | PoolManager plus exact `PoolKey`, immutable audited oracle hook, hook admin/state | Entirely hook/design/liquidity dependent | Hook or custom state failure; V4 core provides no built-in oracle | Highest: hook identity, permissions, upgrades, dynamic fee/custom accounting | Hook-defined plus sequencer |
| **Chainlink primary + Uniswap sanity bound** | Independent Chainlink feed and sufficiently independent liquid canonical pair | Requires corrupting Chainlink or moving DEX outside bound to get accepted bad price; RIPE lacks a Chainlink primary | Can halt on disagreement; not a fallback | Bound, response, source priority, quote/pair config | Both feed timestamps and DEX window; sequencer policy |
| **Uniswap fallback** | DEX remains trustworthy exactly when authoritative source fails | Often lowest when market is stressed or sequencer restarts | Appears live but can return the least trustworthy source; shared sequencer means correlated outage | Very high due to PriceDesk first-nonzero promotion | V3/V2 plus shared sequencer; source failure transition |
| **Reusable generic DEX source** | Correct per-DEX modules, adapters, registry, and governance | Varies invisibly across pool types | Broad revert/semantic surface | High: arbitrary pool/version/quote configuration | Multiple incompatible models |
| **Robinhood-specific source** | Exact Robinhood version and one canonical RIPE pair/quote; explicit guards | Same economics as selected version but fewer substitution paths | Strict zero without propagating pair/feed failures | Bounded to one pair and reviewed config | V2 checkpoint time or V3 observation time; sequencer/grace |

### Engineering, audit, and lifecycle fit

| Option | Deployment complexity | Runtime gas / code size | Audit burden | Required testing | Launch suitability | Follow-on suitability |
| --- | --- | --- | --- | --- | --- | --- |
| **No Uniswap price source** | None | None | Omission/config review | Negative registration, disabled-feature, no-implicit-fallback assertions | **Recommended** | Reassess if a real consumer appears |
| **Uniswap liquidity plus monitoring evidence** | RIPE/WETH pool/LP work only; external custody; no Ripe source or deposit admission | No Ripe oracle gas/code | Pool/custody/product review | Pool identity, execution, capital source, approvals, withdrawal, monitor alerts | **Approved architecture; creation/funding still separately gated** | Good evidence source |
| **Off-chain monitoring only** | Monitor/indexer/runbook | No on-chain code/gas | Operational/data review | Reorg, outage, stale RPC, pool replacement, alert delivery | **Recommended first** | Good; can inform later calibration |
| **V2 TWAP source** | New source plus checkpoint operations | Medium reads/writes; adapter stores checkpoints | High custom accumulator/math/operations | Wraparound, checkpoint timing, sparse trading, manipulation, liquidity removal, PriceDesk composition | Not needed | **Research candidate if RIPE/WETH V2 remains canonical and every new gate closes** |
| **V3 TWAP source** | New source, cardinality preparation, bootstrap, PriceDesk config, plus wrapper/NFT-vault/drop-LP decision | Medium view cost; compact bounded source; extra LP architecture may dominate | High oracle burden plus changed custody/deposit architecture | V3-specific equivalent of section 10 plus new LP artifact tests | Reject for the possible Profile 2 `SimpleErc20` LP role | Technically preferred only after explicit plan change |
| **V4-aware source** | New hook or hook consumer plus V4 integration | Hook-dependent; potentially large | Very high custom oracle and hook surface | Hook lifecycle, permissions, swaps/liquidity, custom accounting, reentry/unlock, manipulation | Reject | Reassess only after audited canonical hook |
| **Chainlink primary + sanity bound** | Comparator/guard plus two sources | Higher per read; comparator code | High cross-source semantics | Divergence, depeg, stale one/both, outage, bounds, decimals, order | Existing Chainlink alone at launch | Strong for assets with both independent sources |
| **Uniswap fallback** | Easy to register, hard to make safe | Medium | Very high economic/failure-state review | Every primary-failure transition and attack timing | **Reject** | Reject for value-bearing paths |
| **Reusable generic DEX source** | Framework, registry, plugins/config | Large or many contracts | Highest abstraction and integration burden | Per-version matrices plus cross-module substitution/config | Reject | Only if several proven consumers justify it |
| **Robinhood-specific source** | One bounded deployment and config | Small/medium; exact pair reads/checkpoints | Lower than generic, still full oracle audit | Full section 10 matrix and fork evidence | Not needed | **Research-only shape if later warranted; no implementation authority** |

The “no source,” “liquidity plus monitoring,” and “off-chain monitoring” rows
are complementary: launch may have all three by having a Uniswap pool, an
external monitor, and no PriceDesk registration.

## 7. Launch versus follow-on recommendation

### Launch

1. **Do not build or register a Uniswap price source.**
2. Preserve Chainlink as the only selected PriceDesk source and preserve empty
   reserved source slots. Freeze exact feeds and positive stale ceilings.
3. Resolve Robinhood sequencer-outage handling through an official feed if one
   becomes available, or an explicitly approved pause/monitor/restart-grace
   policy. Do not infer an address.
4. Preserve omission of RIPE/GREEN market-price-dependent features and global
   rewards-off configuration.
5. Use V2 only as the selected candidate for an externally held RIPE/WETH
   launch-liquidity canary. Pool preparation or funding does not admit the LP
   token to Ripe.
6. Do not create a redundant GREEN/USDG Uniswap launch pool. Its liquidity,
   artifact, and possible admission remain in the Profile 2 Curve
   qualification plan absent a separate owner decision.
7. Move both LP-token admissions to Profile 2. Before either activation, retain
   `SimpleErc20`, `ltv=0`, and no PriceDesk feed; prove exclusion from
   borrowing-power, liquidation-value, rewards, points, solvency, PSM, and
   every other valuation-dependent route; and obtain separate activation
   authority.
8. Treat `50,000 USD` per side only as a provisional RIPE/WETH canary capital
   envelope. Reject the `25,000 USD within +/-1%` target, and do not treat the
   section 9 `3.53 million USD` calculation as funding authority. PSM reserves
   are not LP funding capital.
9. Before pool creation or funding, freeze every operational binding in
   section 9: chain/factory/router, token ordering, pair, initialization price,
   funding source, custodian, approvals, LP custody, withdrawal delay, retained
   reserves, monitoring/incident owner, and emergency unwind.
10. Do not use a router quote, spot reserve ratio, or current tick as a protocol
   price.
11. Do not create a second thin pool solely to supply an oracle. Liquidity
   fragmentation reduces manipulation resistance.

This is the smallest change and smallest blast radius. It also preserves the
current migration posture: Robinhood migration namespaces and history are
planned but absent, `DefaultsRobinhood.vy` remains absent/fail-closed, and no
deployment/configuration/activation is authorized by
`docs/chains/rh/current-owner-priorities.md`.

### Follow-on trigger

Reopen this decision only when an approved feature specification names:

- the function that needs RIPE/USD or RIPE/quote;
- whether the price is informational, a bound, a pause condition, or direct
  accounting input;
- maximum value extractable per oracle window;
- required availability and acceptable fail-closed effects;
- canonical pool, quote asset, and liquidity/custody policy; and
- why an authoritative off-chain/Chainlink feed or governance-set bounded
  value is insufficient.

If the need is only dashboards, treasury review, or governance information,
continue off-chain. If the need is a sanity bound, prefer a comparator against
an independent authoritative primary. If direct RIPE protocol accounting is
unavoidable and no authoritative RIPE feed exists, the conditional V2 design
below is compatible with the RIPE/WETH venue candidate. It remains research
only until the owner approves an official sequencer feed or accepted
alternative policy, exact window, exposure `E`, manipulation/reserve model,
`C_attack > 5E` or its replacement, exact stale-data and
sequencer-recovery behavior, independent fork and adversarial tests, and
separate implementation/security review. A V3 TWAP is the stronger native
primitive only after a separate custody/wrapper architecture decision. There
is no launch Chainlink-to-Uniswap fallback.

## 8. Historical contract specification (superseded)

This section records the **superseded future research-only** cumulative-price
design that was formerly named `RobinhoodUniswapV2RipePrices`. That source has
been deleted. The current `UniswapV2Prices` candidate instead reuses the
`AeroRipePrices` snapshot shape with an Underscore-style Uniswap V2 reserve
reader. It is documented separately in
[`uniswap-v2-prices.md`](../smart-contract-changes/uniswap-v2-prices.md) and is
also non-admitted. The historical specification below is retained as decision
history, not as a description or authorization of the current contract.

**Current deployability:** no security-relevant mode is deployable today under
this specification. Robinhood recommends a sequencer check, but Chainlink's
official supported sequencer-feed list provides no Robinhood address.
`PROTOCOL_ACCOUNTING` therefore remains blocked. A monitoring-only contract
would not be registered in PriceDesk and is unnecessary while an off-chain
monitor suffices. The owner may later approve an explicit alternative sequencer
policy, but that would require revising and reviewing this specification before
implementation. This section is a research boundary, not a current deployment
candidate.

### Purpose and interface

The research design prices RIPE only from one immutable Robinhood Uniswap V2
RIPE/WETH pair. A different quote or pair requires a new owner decision and
review. It implements every selector in
`interfaces/PriceSource.vyi`; the third read argument retains the interface
name `_oracleRegistry` even though the supplied address is PriceDesk:

- `getPrice(_asset, _staleTime, _oracleRegistry) -> uint256`
- `getPriceAndHasFeed(_asset, _staleTime, _oracleRegistry) -> (uint256, bool)`
- `hasPriceFeed(_asset) -> bool`
- `hasPendingPriceFeedUpdate(_asset) -> bool`
- `getPricedAssets() -> [RIPE]`
- `addPriceSnapshot(_asset) -> false`
- `confirmNewPriceFeed`, `cancelNewPendingPriceFeed`,
  `confirmPriceFeedUpdate`, `cancelPriceFeedUpdate`, `disablePriceFeed`,
  `confirmDisablePriceFeed`, and `cancelDisablePriceFeed`;
- `actionTimeLock`, `hasPendingAction`, `getActionConfirmationBlock`,
  `setActionTimeLock`, and `setActionTimeLockAfterSetup`;
- `isPaused` and `pause`; and
- `recoverFunds(_recipient, _asset)` and
  `recoverFundsMany(_recipient, _assets)`.

Add read-only diagnostics rather than broad pricing APIs:

- `getTwapQuotePerRipe() -> (quotePerRipe, averagingPeriodSeconds,
  averageUpdatedAt)`
- `getCurrentCumulativePrices() -> (price0Cumulative, price1Cumulative,
  timestamp)`
- `getCheckpoint() -> (price0Cumulative, price1Cumulative, timestamp,
  reserve0, reserve1)`
- `getReserveHealth() -> (reserveRipe, reserveQuote, averageAge,
  updateDue)`
- `getSafetyState(oracleRegistry) -> (statusCode, ripeUsd, quoteUsd,
  reserveRipe, reserveQuote, averageAge, spotDeviation)`

`getPriceAndHasFeed(RIPE, ...)` returns `(0, true)` on an unsafe or unavailable
observation so PriceDesk can distinguish configured-but-unavailable from no
feed. Every other asset returns `(0, false)`. The contract never stores or
returns a last-good price.

### Constructor and immutables

The constructor receives and validates:

- RipeHq and temporary governance;
- the official Robinhood V2 factory
  `0x8bceaa40b9acdfaedf85adf4ff01f5ad6517937f`;
- exact RIPE token;
- exact official Robinhood WETH quote token;
- exact V2 pair;
- minimum and maximum governance timelocks;
- approved sequencer-uptime feed, if an official Robinhood feed exists; and
- immutable mode: `MONITOR_BOUND` or `PROTOCOL_ACCOUNTING`.

Deployment validation must prove:

- nonzero/distinct tokens;
- factory `getPair(RIPE, quote) == pair`;
- pair `factory`, `token0`, and `token1` match;
- pair reserves and total supply are nonzero;
- token decimals are bounded and cached;
- quote token identity matches official Robinhood documentation;
- in `PROTOCOL_ACCOUNTING` mode, a nonzero officially verified sequencer feed
  is mandatory; absent one, only `MONITOR_BOUND` mode is deployable; and
- no mutable pair, token, factory, or mode pointer exists. A new pair requires
  a new adapter and review.

Router02 is not an oracle dependency, and V2 has no quoter, manager, or
position manager. The pair's LP claim is ERC-20, but the launch RIPE/WETH
position remains externally held; its token does not become a Ripe deposit
artifact unless a separately authorized Profile 2 admission closes.

### Storage and governed configuration

Store only:

- live `OracleConfig`;
- pending config plus timelock action ID;
- the prior V2 cumulative-price checkpoint;
- the latest completed cumulative-price average and its period/timestamp;
- pause/disable state inherited from the standard source modules; and
- optional activation timestamp.

`OracleConfig` contains:

- `twapWindowSeconds`;
- `maxAveragingPeriodSeconds`;
- `maxAverageStalenessSeconds`;
- `minRipeReserve`;
- `minQuoteReserve`;
- `maxSpotToTwapDeviationBps`;
- `sequencerRestartGraceSeconds`;
- `maxQuoteStaleSeconds`; and
- `activated`.

`Checkpoint` contains both cumulative prices, the V2 32-bit pair timestamp, the
full local timestamp, and the two reserves observed when the checkpoint is
accepted. `Average` contains the two direction-normalized UQ112x112 averages,
the actual averaging period, and the full local timestamp when that completed
average was stored. Store exactly one prior checkpoint and one latest completed
average; do not maintain caller-chosen price snapshots, an unbounded
observation history, or a governance-posted price.

Proposed hard validation ceilings, intended to prevent nonsensical
configuration rather than select production values:

- `30 minutes <= twapWindowSeconds <= 24 hours`;
- `twapWindowSeconds <= maxAveragingPeriodSeconds <= 2 *
  twapWindowSeconds`;
- `twapWindowSeconds <= maxAverageStalenessSeconds <= 2 *
  twapWindowSeconds`;
- `minRipeReserve > 0`;
- `minQuoteReserve > 0`;
- `0 < maxSpotToTwapDeviationBps <= 2,000` (20%);
- `30 minutes <= sequencerRestartGraceSeconds <= 24 hours`;
- `0 < maxQuoteStaleSeconds <= 48 hours`; and
- MissionControl's supplied stale time and `maxQuoteStaleSeconds` use the
  **stricter nonzero minimum**, not Aero's ignored value or Chainlink's current
  maximum behavior.

The owner must select materially narrower production values from fork and
economic evidence. Any config update is initiated, evented, timelocked,
independently checked, and confirmed. Activation is a separate timelocked
action after bootstrap evidence; configuration confirmation does not activate
the feed. A permissionless `update()` may advance a checkpoint only when at
least `twapWindowSeconds` has elapsed. The first successful call only
bootstraps the checkpoint and cannot activate or produce a price. Each later
accepted call atomically computes and stores a completed average from the old
checkpoint, then advances the checkpoint. Too-early calls return false and
cannot reset the window or erase the last completed average. The update uses
the official [Uniswap V2 oracle method](https://developers.uniswap.org/docs/protocols/v2/guides/building-an-oracle)
and upstream
[`UniswapV2OracleLibrary`](https://github.com/Uniswap/v2-periphery/blob/master/contracts/libraries/UniswapV2OracleLibrary.sol)
counterfactual cumulative-price math, not current reserves as a price. Uniswap
documents core formal verification and core/periphery review in its
[V2 audit record](https://developers.uniswap.org/docs/protocols/v2/audits);
the Ripe translation and all added failure/configuration logic still require
independent audit.

### Observation and price rules

For every price read:

1. Require not paused/disabled and `activated`.
2. Read every external dependency through a bounded low-level static call with
   failure capture and exact return-length/range validation. A pair, token,
   sequencer, or quote-source revert or malformed return becomes unavailable;
   it must not propagate.
3. If configured, read the sequencer feed. Reject outage, malformed answer,
   future timestamp, or recovery inside the restart grace.
4. Read V2 reserves, cumulative prices, and timestamp. Require nonzero reserves
   at or above both configured reserve floors.
5. Require a completed stored average whose age is no more than
   `maxAverageStalenessSeconds`; the bootstrap checkpoint alone is not a price.
6. Normalize the stored RIPE/quote average for token order and decimals with
   checked full-precision math.
8. Calculate the current reserve ratio only as a safety signal. Reject if
   spot-to-TWAP deviation exceeds the configured bound; never return spot or
   substitute it for TWAP.
9. Ask the supplied PriceDesk (`_oracleRegistry`) for the quote/USD price.
   Require nonzero and independently fresh. The adapter must not claim a feed
   for the quote, which breaks direct recursion; a composition test must still
   prove that the registered source ordering cannot cycle.
10. Multiply TWAP RIPE/quote by quote/USD with full-precision checked math and
    return 18-decimal RIPE/USD.

For the permissionless checkpoint `update()`:

1. apply the same captured-call, sequencer, pair-identity, reserve-floor, and
   timestamp checks;
2. construct current counterfactual cumulative prices with audited upstream V2
   oracle-library math so elapsed time since the pair's last reserve update is
   included without calling `sync`;
3. if no checkpoint exists, store the bootstrap checkpoint, emit its event,
   return true, and leave the average absent;
4. otherwise return false without storage writes if the minimum window has not
   elapsed;
5. if elapsed time exceeds `maxAveragingPeriodSeconds`, invalidate the stale
   completed average, advance only the checkpoint as a resynchronization,
   emit the resync/checkpoint events, and require a new full window before a
   price can return;
6. otherwise subtract cumulative values across the elapsed period, including V2's
   deliberate 32-bit timestamp and cumulative arithmetic wrap, then divide by
   elapsed time to obtain both UQ112x112 arithmetic averages;
7. atomically store the completed averages and their actual period/timestamp,
   then advance the checkpoint to the current cumulatives; and
8. emit both average and checkpoint events. Caller identity never changes the
   arithmetic and cannot backdate an endpoint or erase a completed average
   with a too-early call. Because a caller can choose when to call within the
   bounded update interval, caller timing is explicitly adversarial in section
   10.

For `MONITOR_BOUND` mode, PriceDesk registration remains prohibited; the
diagnostic methods may be read by monitoring or a separately specified
comparator. For `PROTOCOL_ACCOUNTING`, PriceDesk integration requires a new
approval after all section 10 gates pass and remains impossible until an
official sequencer feed is verified.

Do not average spot with TWAP, do not average a stale last-good value, do not
use caller-triggered Ripe snapshots, and do not combine multiple thin pools
without a separate robust aggregation specification. External observations
may be used off-chain to validate the source, not silently injected into the
contract.

### Failure behavior

Every unsafe condition returns zero for `getPrice` and `(0, true)` for
`getPriceAndHasFeed`. **No pair, token, sequencer, or quote-source revert or
malformed return may propagate.** Each call uses failure capture, a fixed gas
budget where the language/runtime permits, exact return-length checks, and
bounded decoding before arithmetic. All arithmetic and decimal/timestamp
domains are prevalidated so an unsafe value returns zero rather than panics.
PriceDesk with `_shouldRaise=true` then fails closed if no other approved
source returns a price. There is:

- no spot fallback;
- no alternate V2 pair, V3, or V4 fallback;
- no fallback to a different fee pool;
- no last-good-price fallback;
- no automatic Chainlink-to-Uniswap fallback; and
- no governance-set emergency price inside this adapter.

Emergency operation is source disablement or feature pause. If a product
requires a bounded emergency price, specify it as a separate, timelocked,
exposure-capped governance mechanism with its own audit.

This requirement is stricter than ordinary source code style because
`PriceDesk._getPriceFromPriceSource` uses an uncontained `staticcall`
(`contracts/registries/PriceDesk.vy:181-187`). Any unexpected adapter revert
would bubble through PriceDesk. Depending on enabled routes, it could block
collateral valuation, AuctionHouse settlement, or Deleverage valuation
(`CreditEngine.vy:743`, `AuctionHouse.vy:695`, and
`Deleverage.vy:522,1096`). Tests must prove non-reversion for every malformed
or reverting external dependency and every arithmetic boundary; residual
uncontained EVM failure remains a reason not to register this source at
launch.

### Events

Emit:

- `CumulativePriceCheckpointUpdated(price0Cumulative, price1Cumulative,
  pairTimestamp, localTimestamp, reserve0, reserve1)`;
- `CumulativePriceAverageUpdated(price0Average, price1Average,
  averagingPeriodSeconds, averageUpdatedAt)`;
- `CumulativePriceCheckpointResynchronized(previousTimestamp,
  newTimestamp, reasonCode)`;
- `OracleConfigUpdatePending(actionId, config, confirmationBlock)`;
- `OracleConfigUpdateConfirmed(actionId, oldConfig, newConfig)`;
- `OracleConfigUpdateCancelled(actionId)`;
- `OracleActivationPending(actionId, confirmationBlock)`;
- `OracleActivated(actionId, activationTimestamp)`;
- `OracleDeactivated(reasonCode)`;
- standard pause/disable events; and
- no event from view price reads.

Off-chain monitors derive unsafe-state alerts from `getSafetyState`; do not add
a state-changing “poke” solely to emit health events. The permissionless
`update()` exists only because V2 needs a stored historical checkpoint.

### Required `PriceSource` feed lifecycle

The common interface exposes a multi-feed lifecycle, but this contract has one
immutable RIPE feed. Its selectors have fixed semantics rather than allowing an
implementer to invent a second configuration system:

- deployment creates RIPE as a pending, inactive feed;
- `confirmNewPriceFeed(RIPE)` can activate feed configuration only after the
  source timelock, full checkpoint window, reserve/depth proof, and mode gates;
- `cancelNewPendingPriceFeed(RIPE)` cancels that pending activation;
- `hasPendingPriceFeedUpdate(RIPE)` reports pending activation, config update,
  or disable; every other asset is false;
- `confirmPriceFeedUpdate(RIPE)` and `cancelPriceFeedUpdate(RIPE)` confirm or
  cancel the single pending `OracleConfig`;
- `disablePriceFeed(RIPE)` initiates timelocked deactivation;
- `confirmDisablePriceFeed(RIPE)` deactivates and makes all reads return zero;
- `cancelDisablePriceFeed(RIPE)` cancels that action;
- every feed-lifecycle call for another asset returns false;
- no selector can change the immutable pair, tokens, factory, quote, or mode;
  those changes require a new deployment; and
- `recoverFunds`/`recoverFundsMany` follow standard Ripe governance and pause
  authorization, may rescue only accidental token balances held by the
  adapter, and cannot move pair reserves or LP tokens held elsewhere.

Source feed activation is distinct from PriceDesk registry insertion and from
consumer-feature activation. Each needs its own evidence and authority.

### PriceDesk integration

Registration is a distinct timelocked governance action after deployment and
qualification. Before registration:

- freeze a dedicated source ID and allowlist it in the Robinhood blueprint;
- update negative omission tests deliberately;
- prove the quote source is earlier, independent, and cycle-free;
- specify whether it is sole RIPE authority or only a comparator;
- add source-state semantics so a comparator cannot become a generic fallback;
  and
- preserve an emergency feature pause.

The current PriceDesk cannot express “Chainlink primary plus Uniswap sanity
bound.” That option requires a dedicated comparator/guard or consumer-level
bound, not merely two PriceDesk sources. Registering the V2 adapter after
Chainlink would create a fallback, which is rejected.

### Threat-model commitments

The implementation and audit must assume:

- adversarial swaps, reserve donation/sync behavior, and LP removal;
- low/sparse activity and missed/adversarial checkpoint timing;
- same-block and multi-block manipulation with front/back ordering;
- quote-feed staleness/depeg and decimal errors;
- sequencer outage/restart and delayed L1 finality;
- observation counterfactuals after no actual writes;
- governance or custodian compromise;
- pool substitution attempts and creation of other fee pools;
- price extremes near fixed-point/math bounds and timestamp wrap;
- denial of service through pool/quote calls; and
- maximum extraction in one window, not only historical volume.

The contract does not solve economic depth. Activation depends on the external
liquidity/custody/exposure controls in section 9.

## 9. Pool/liquidity owner decisions

These decisions remain required before creating any pool and, where marked,
before making a price security-relevant:

| Decision | Required owner answer | Oracle consequence |
| --- | --- | --- |
| Product use | Launch RIPE/WETH is liquidity plus off-chain monitoring only; no PriceDesk registration or protocol accounting | No Uniswap contract is warranted in this tranche |
| Venue sequencing | V2 is the RIPE/WETH launch canary candidate; GREEN/USDG stays in the Profile 2 Curve plan, with no redundant launch Uniswap pool | Prevents the liquidity decision from silently changing the oracle or PSM plan |
| Protocol admission | Neither LP token is admitted at launch; both admissions are Profile 2 actions with separate activation authority | Pool creation/funding cannot activate a Ripe deposit asset |
| Later LP posture | If admitted: existing `SimpleErc20`, `ltv=0`, no PriceDesk feed, and complete negative-route proof | Any valuation reachability blocks activation rather than triggering an improvised LP price |
| Chain and deployments | Exact chain ID, official V2 factory and Router02 code/addresses, and abort-on-mismatch rule | Router is operational infrastructure, never the price source |
| Pair / ordering | Exact RIPE, WETH, token0/token1 order, factory-derived pair address, and counterfeit-pair rejection | Freezes the launch canary identity before creation or funding |
| V2 fee / range | Fixed 30 bp fee and full-range constant-product liquidity; no tick spacing, range, hook, cardinality, quoter, or position manager | See the official [Uniswap V2 whitepaper](https://docs.uniswap.org/whitepaper.pdf) |
| Initial price | Independent reference, acceptable initialization bound, authorized initializer, and abort rule | Prevents false-price bootstrap |
| Funding source | Exact source and amount; PSM reserves are prohibited as LP funding capital | Keeps PSM backing separate from discretionary market liquidity |
| Capital and execution | `50,000 USD` per side is only a provisional RIPE/WETH canary envelope; later approve maximum trade, slippage, retained-reserve, monitoring, and withdrawal criteria | Rejects the unsupported `25,000 USD within +/-1%` promise and does not approve `3.53 million USD` |
| Liquidity custody | Exact Safe or other custodian, signers, LP-token custody, approval ceilings, transfer permissions, and fee handling | Determines who can burn, transfer, or dilute the liquidity claim |
| Withdrawal | Exact delay, minimum retained reserves, authorization, monitoring precondition, and emergency unwind sequence | Liquidity may not fall below the approved operating bound without the approved response |
| Operations | Named monitoring and incident owner, alert thresholds, response clock, and emergency-unwind procedure | Makes pool liveness and custody failures actionable |
| WETH/USD authority | None is required solely for the external pool; any future valuation-dependent use must stop until an approved authority and complete qualification are frozen | Separates liquidity existence from protocol valuation |
| V3/V4 alternative | Do not use their NFT or more complex positions for current LP roles; any wrapper/custody redesign requires a separate decision | Avoids silently adding wrapper, NFT-vault, hook, or custom-accounting risk |
| Future checkpoint history | If TWAP research advances: exact window, maximum period, caller automation, average staleness, bootstrap, and 32-bit timestamp handling | Missing or stale observations make the source unavailable |
| Future liquidity floor | Exact exposure `E`, manipulation/reserve model, first-draft `S=5` or replacement, and current reserve thresholds | No security-relevant use until frozen and proved |
| Future governance | Config owner, guardian, timelocks, event monitors, emergency pause, and independent review authority | Bounds configuration and response risk |

### Minimum security-relevant depth

Let:

- `E` be the maximum net value an attacker can extract from all protocol
  actions during one oracle window, including correlated positions and
  liquidation/issuance caps;
- `δ` be the smallest price distortion that produces profitable protocol
  behavior;
- `W` be the TWAP window;
- `C_attack(δ,W,state)` be the least net cost to maintain the distortion across
  the observed range and window, after recovered arbitrage, LP fees, own LP
  fees, MEV, and unwind proceeds; and
- `S` be the security multiple plus explicit gas/ordering reserve; this first
  draft proposes `S=5`.

Activation requires, at minimum:

`C_attack(δ,W,worst-approved-state) > 5 × E`

under each tested state: ordinary ranges, edge of active range, approved LP
withdrawal shock, third-party liquidity removal, low activity, sequencer
restart, and quote-asset stress. It also requires a protocol-owned,
timelocked/custodied minimum of **pair reserve** depth that survives the
approved withdrawal shock. `E`, `δ`, and the stress states are owner/risk
decisions. The correct present security minimum remains “not established; zero
security-relevant use” until those inputs exist.

That does not prevent checking a provisional **RIPE/WETH liquidity-canary**
envelope. For an equal-value V2 pair with reserve value `R` on each side,
input `d`, and V2 fee factor
`f=0.997`, the average execution price relative to pre-trade spot is:

`executionRatio = fR / (R + fd)`

Requiring `executionRatio >= 0.99` gives:

`R >= (0.99 × 0.997 / (0.997 - 0.99)) × d ≈ 141.0d`

Consequences:

- with `R=50,000 USD`, the maximum one-direction input at no more than 1%
  average deviation is about `354.6 USD`;
- a `25,000 USD` one-direction input requires about `3.53 million USD` of
  input-side reserve and the matched other-side value; and
- these are execution-depth figures, not oracle-security proof. The security
  reserve may be larger because manipulation is assessed over a TWAP window
  against value extractable from Ripe.

Neither number approves a pool budget, maximum trade, slippage promise, or
funding source. Those are later owner decisions, and PSM reserves are excluded.

The contemporaneous untracked
`docs/chains/rh/qualification/psm-liquidity-activation.md` in
`codex/rh-psm-liquidity-activation` supplies the `50,000 USD` per-side budget
and `25,000 USD within +/-1%` target as non-authoritative coordination inputs.
This disposition narrows the former budget to a provisional RIPE/WETH canary
envelope and rejects the depth target. The sibling draft must also remove any
launch GREEN/USDG Uniswap assumption, preserve PSM reserves, and consume the
Profile 2 Curve/admission sequencing before its LP artifact gate closes.

## 10. Fork-test requirements

No RPC or fork was used in this reassessment. The following is the complete
minimum qualification matrix before any follow-on source can be approved.
Profile A uses exact Robinhood mainnet state at a pinned block. Profile B uses
a deterministic local deployment/state fixture capable of adversarial
mutations that public mainnet state cannot safely exercise. Every result must
record chain ID, block identity, commit, pair, factory, quote feed, checkpoint
state, and commands.

### Launch-liquidity preparation and Profile 2 admission

Before any RIPE/WETH V2 pair creation or funding, the owner packet and
deterministic qualification fixtures must bind:

- chain ID `4663`, official factory/Router02 identities and code, RIPE/WETH
  token addresses and ordering, factory-derived pair, initialization reference,
  acceptable bound, initializer, and abort conditions;
- exact funding source and amount, explicitly excluding PSM reserves;
- liquidity Safe or other custodian, signers, approval ceilings, LP-token
  custody, fee handling, withdrawal delay, minimum retained reserves, and
  emergency-unwind authorization/order;
- monitoring and incident owner, alert thresholds, response timing, reporting,
  and pool/pair substitution detection; and
- later owner-approved maximum intended trade size and acceptable slippage
  instead of the rejected `25,000 USD within +/-1%` promise.

The launch configuration must prove that neither LP token is admitted or
active in Ripe and that no Uniswap source is registered in PriceDesk. It must
also prove no GREEN/USDG Uniswap launch pool is assumed by configuration or
migration planning. The Profile 2 package, not launch, must test any later LP
admission with `SimpleErc20`, `ltv=0`, no PriceDesk feed, and complete
exclusion from borrowing-power, liquidation-value, rewards, points, solvency,
PSM, redemption, auction, deleveraging, and all other valuation-dependent
routes. Passing that package does not itself authorize activation.

### Future TWAP baseline and provenance

- Recompute source commit/tree and require a clean isolated worktree.
- Verify chain ID `4663`, official WETH identity, V2 factory code and exact
  deployment binding.
- Verify factory `getPair` matches immutable pair, tokens, reserves, LP total
  supply, and initialized state.
- Prove rejection of counterfeit factory, pair, token ordering, quote, and
  router.
- Inventory all pools for the pair across V2/V3/V4 and fees for monitoring,
  while proving only the exact V2 pair is consumed.
- Record pair creation/first-liquidity time, reserves, cumulative prices,
  pair timestamp, LP total supply, LP holders/approvals, volume/activity, and
  current/previous checkpoints.

### Math and decimals

- RIPE as token0 and token1.
- Quote decimals below, equal to, and above RIPE decimals.
- Both cumulative-price directions and UQ112x112 decode/normalization.
- Reserve-ratio and cumulative-delta boundary cases; multiplication overflow
  and rounding direction.
- Compare adapter output against audited Uniswap oracle math and independent
  off-chain computation.
- Quote/USD values at decimal extremes, depeg, zero, negative, future,
  incomplete, and stale rounds.
- No double application of a Stock Token multiplier; Stock Tokens are not the
  RIPE quote.

### Checkpoint behavior

- No checkpoint; bootstrap checkpoint with no price; first completed average;
  and later completed averages.
- `update()` one second before the minimum window, exactly at it, and after it;
  too-early calls do not alter either the checkpoint or last average.
- Update one second before the maximum averaging period, exactly at it, and
  one second after it; the overlong case invalidates/resynchronizes and needs a
  new full window rather than blessing an arbitrarily long average as fresh.
- Average fresh, exactly at maximum staleness, and one second stale.
- Quiet pair where current counterfactual cumulative values advance from the
  last reserve timestamp; verify the completed average and staleness rule.
- Multiple `update()` calls in one block and adversarial caller timing.
- Sparse swaps, regular swaps, mint/burn, `sync`, and `skim`.
- Full bootstrap window not elapsed, exactly elapsed, and elapsed with
  unchanged reserves but positive counterfactual cumulative delta.
- Accepted update atomically stores both directional averages before advancing
  the checkpoint; subsequent too-early calls preserve that usable average.
- V2 32-bit pair timestamp wrap, local full-timestamp staleness, and subtraction
  wrap behavior exactly matching audited upstream math.

### Manipulation and MEV

- One-transaction spot manipulation with read before unwind.
- Same-block front/read/back sequence under Robinhood ordering.
- Multi-block/window manipulation for each proposed window.
- Attacker adds V2 liquidity, moves reserves, invokes a protocol action, burns
  LP tokens, and unwinds.
- Flash swap and external flash-liquidity manipulation.
- Direct token donations with and without `sync`; `skim` behavior.
- Thin reserves and asymmetric reserves despite nominal LP-token value.
- Third-party arbitrage absent, delayed, and active; conservative test must not
  assume benevolent arbitrage.
- Fixed 30 bp fee and parallel V2/V3/V4 market divergence.
- Spot/TWAP bound at, below, and above threshold.
- Demonstrate net attack-cost model exceeds approved `5 × E`; do not accept
  only percent-price-change assertions.

### Liquidity and custody

- RIPE and quote reserves below, exactly at, and above their independent
  thresholds.
- Current reserves below threshold despite a healthy historical checkpoint.
- LP token transferred, approved, partially burned, and fully burned.
- Partial and full third-party withdrawal.
- Partial and full withdrawal by the approved liquidity custodian;
  oracle deactivation must precede any threshold breach.
- Compromised LP custodian attempts immediate transfer/burn.
- Fee accrual, mint/burn dilution, and `MINIMUM_LIQUIDITY` behavior.
- Verify `50,000 USD` per-side reserves yield the derived roughly `355 USD`
  one-direction 1%-deviation input, and calculate the reserve required for the
  rejected sibling `25,000 USD` target without treating either value as funding
  authority.
- Approved withdrawal-shock state still satisfies the economic proof.

### Sequencer, clock, and finality

- Sequencer feed up, down, malformed, future-dated, and unavailable if an
  official feed exists.
- Recovery at grace start, one second before expiry, exactly at expiry, and
  after expiry.
- No fabricated feed: accounting mode deployment rejects zero/unverified
  sequencer dependency.
- Repeated inherited `block.number`, jumps, and actual child blocks prove the
  source is timestamp-based and never uses Curve's number semantics.
- Timestamp stops/advances around outage and pair has no fresh writes after
  restart.
- Soft confirmation versus delayed posting/reorganization in the operational
  monitor and activation runbook.

### Failure, governance, and PriceDesk composition

- Pair `getReserves`, cumulative-price, token, factory, or total-supply read
  reverts, returns short/long data, or returns out-of-domain values.
- Token decimals, sequencer, and quote PriceDesk return zero, revert, or return
  malformed data; adapter captures every failure without reverting.
- Adapter returns `(0,true)` on every unsafe/missing/stale average and never
  last-good or spot fallback.
- `_shouldRaise=false` and `true` end-to-end consumer behavior.
- Priority source healthy, zero, stale, or reverting; prove no implicit
  Uniswap fallback.
- Source registered and unregistered; disabled and paused; consumer features
  disabled.
- Quote-source recursion/cycle attempts.
- Config initiation, timelock boundaries, confirmation, cancellation,
  supersession, invalid ceilings, activation separation, and event fields.
- Every required `PriceSource.vyi` feed lifecycle selector for RIPE and a
  non-RIPE asset; recovery authorization and no pair/LP custody reach.
- Unauthorized governance/guardian/custodian callers.
- Emergency source disable and dependent-feature pause.
- New V2 pair impostor, V3 pool, V4 hook, or router change does not change the
  adapter's source.

### Existing-suite deltas

- Retain Base `AeroRipePrices` and `CurvePrices` tests unchanged.
- Add Robinhood negative assertions that Aero/Curve remain undeployed or
  unregistered and reserved PriceDesk slots remain empty for launch.
- Assert neither GREEN/USDG LP nor RIPE/WETH LP is admitted or active under
  launch configuration, and that no migration/configuration path implicitly
  activates either asset.
- Assert no GREEN/USDG Uniswap launch pool or LP artifact is required; preserve
  its Profile 2 Curve qualification boundary.
- In Profile 2 admission tests for either LP, assert `SimpleErc20`, `ltv=0`, no
  PriceDesk feed, and no reachability into borrowing power, liquidation value,
  Deleverage, AuctionHouse, redemption, rewards, points, solvency, PSM, or any
  other valuation-dependent route.
- Prove launch RIPE/WETH pool existence alone neither requires WETH/USD
  authority nor creates a RIPE/WETH LP or RIPE price feed.
- Add explicit tests for manipulation, activity staleness, liquidity removal,
  sequencer behavior, and source ordering; the present Aero/Curve snapshot
  suites do not cover those V2 security properties.
- Run ordinary local, Base, and both Robinhood profiles so shared interface or
  PriceDesk changes cannot silently alter Base behavior.
- Measure runtime bytecode against Robinhood's documented 96 KB contract-size
  limit and the repository's current EIP-170 compatibility bar of 24,576 bytes
  (`docs/chains/rh/START-HERE.md:94-101`); record checkpoint/write gas, read
  gas, and worst-case consumer transaction gas.
- Require independent oracle/security review and audited-upstream source
  matching for V2 cumulative-price and fixed-point helpers.

## 11. Residual risks and non-actions

### Residual risks

- Official deployments do not prove a canonical RIPE pair, liquidity,
  checkpoint history, activity, or safe custody.
- Chainlink coverage is complete only for the selected launch set while
  RIPE/GREEN market-price features stay off. A RIPE/WETH pool alone does not
  require WETH/USD; any future valuation-dependent feature does reopen and
  block on the oracle freeze.
- Robinhood recommends sequencer checks, but no Robinhood address was found in
  Chainlink's current official sequencer-feed list. Existing
  `ChainlinkPrices` has no such check. This remains an owner/security/operations
  gate, and Uniswap cannot diversify it.
- Stock Token feeds are 24/5 and include corporate-action/multiplier semantics.
  `oraclePaused` is advisory and `ChainlinkPrices` does not check it; stale
  checks alone are not a complete market-hours or issuer-pause policy.
- The frozen tree's former launch LP-token blockers are superseded as launch
  admissions, not silently satisfied: both activations move to Profile 2.
  Exact no-feed and complete negative-route proofs remain mandatory before any
  later admission.
- A liquid-looking V2 pair can have inadequate reserves for the required trade
  size. Third-party liquidity and volume can disappear.
- A long TWAP raises manipulation cost but increases lag and can make the
  protocol unavailable after pair bootstrap, missed checkpoints, or outage.
- A V2 TWAP and quote/USD feed are not fully independent if both rely on the
  same sequencer and shared market infrastructure.
- No security-relevant DEX adapter is currently deployable under section 8:
  no official Robinhood sequencer-uptime feed address is verified, while the
  only allowed monitor mode is deliberately unregistered from PriceDesk.
- PriceDesk cannot natively express comparator/sanity-bound semantics. Two
  registered sources create first-nonzero ordering, not consensus.
- Governance, oracle configuration, and LP custody can dominate the technical
  oracle risk.
- The numeric configuration ceilings in section 8 are proposed hard bounds,
  not approved operating values or evidence of sufficient liquidity.
- The sibling `codex/rh-psm-liquidity-activation` draft and this report are
  untracked parallel inputs. Its `25,000 USD within +/-1%` depth assumption is
  rejected; its budget can only be a provisional RIPE/WETH canary envelope;
  GREEN/USDG remains Profile 2 Curve; and PSM reserves are not LP capital.
  Neither file is integrated authority.
- Several isolated worktrees create `docs/chains/rh/reassessment/`. There is no
  filename collision for this report, but the integration owner must preserve
  deliberate ordering and review rather than merging the directory wholesale.
- This report remains untracked in a mode-0700 `/private/tmp` worktree. The
  closure task also preserves a byte-identical mode-0600 archive under
  mode-0700 archive directories; that copy is durability evidence, not Git,
  integration, implementation, or activation authority.

### Non-actions

This assessment did not:

- implement or modify a contract, interface, ABI, configuration, migration,
  manifest, inventory, existing document, or Git history;
- stage, commit, push, deploy, register, activate, create a pair, write a
  checkpoint, add liquidity, or move an LP token;
- use RPC, a fork endpoint, account access, a signer, or external
  coordination;
- claim that a RIPE Uniswap pool exists;
- select exact pair address, initialization price, funding source, custody,
  approvals, withdrawal authority, retained reserves, monitoring/incident
  owner, checkpoint window, exposure, source priority, or security-relevant
  liquidity for the owner;
- treat PSM reserves as LP funding or the `3.53 million USD` calculation as a
  commitment;
- promote a report recommendation into launch, implementation, deployment,
  configuration, or activation authority; or
- change the current Robinhood launch gate.

**Final decision:** no new Uniswap price-source contract is needed for launch.
Use V2 only as the candidate for an externally held RIPE/WETH
launch-liquidity canary. Do not admit its LP token at launch. Do not create a
redundant GREEN/USDG Uniswap launch pool; keep that liquidity and both
LP-token admissions in their Profile 2 tracks. If a later approved
security-relevant RIPE-price consumer makes a contract necessary, the
Robinhood-specific V2 cumulative-price TWAP remains research-only until every
section 7 gate receives separate approval. Until then, Uniswap is a liquidity
venue and off-chain monitoring signal, not protocol oracle authority or a
Chainlink fallback.
