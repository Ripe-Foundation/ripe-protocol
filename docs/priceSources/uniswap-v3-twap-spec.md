# Uniswap V3 TWAP price source

Revision 7 · 2026-09-09 · owner-ratified PR #229 remediation (D1–D20).
The current specification is this body. The superseded Revision 5 packet is
preserved in Appendix A. This revision covers the two new V3 contracts, tests,
documentation and tooling; it does not authorize deployment or feed admission.

## Price and interfaces

`UniswapV3TwapPrices.vy` is a Vyper 0.4.3 `PriceSource`, optimized for codesize.
A feed selects one canonical Uniswap V3 pool containing the priced asset. The
other token is its quote asset. It returns USD18 per whole asset token:

```
geometric historical asset/quote TWAP × current quote USD price
```

This is not an arithmetic USD TWAP. The quote is obtained through the current
canonical PriceDesk resolved by Addys (`RipeHq.getAddr(7)`). A nonzero supplied
`_priceDesk` must equal that desk or the source returns zero. `_staleTime` is
ignored, including zero: pool observation age is per feed and quote freshness
belongs to the authoritative quote source and desk policy.

The constructor binds RipeHq, initial governance, a
nonempty factory and minimum/maximum action timelocks. Governance, Addys,
PriceSourceData and TimeLock interfaces are exported without modifying those
modules. Initial action delay is zero; the existing after-setup setter works,
and FinishSetup inclusion is a separate migration obligation.

| Interface | Behavior |
| --- | --- |
| `getPrice(asset, staleTime=0, priceDesk=0)` | Price, or zero for an unavailable route |
| `getPriceAndHasFeed(...)` | Price and configured-feed existence |
| `hasPriceFeed(asset)` | Active config exists; does not certify availability |
| `hasPendingPriceFeedUpdate(asset)` | Timelock action is pending; false during the qualification callback |
| `addPriceSnapshot(asset)` | Standard unsupported snapshot operation |
| `addNewPriceFeed`, `updatePriceFeed` | `(asset, pool, twapWindow=0, maxObservationAge=0)` |
| `confirmNewPriceFeed`, `confirmPriceFeedUpdate` | Confirm proposed add/update; identity drift cancels and returns false |
| `cancelNewPendingPriceFeed`, `cancelPriceFeedUpdate` | Explicit cancellation, one cancel event |
| `disablePriceFeed`, `confirmDisablePriceFeed`, `cancelDisablePriceFeed` | Separate disable lifecycle, independent of market/metadata dependencies |
| `isValidNewFeed`, `isValidUpdateFeed`, `isValidDisablePriceFeed` | Preflights; typed dependency calls can revert, including missing history |
| `setFeedDefaults(window, age, ratio)` / `isValidFeedDefaults(...)` | Three-field proposal defaults; setter governance-only and pause-gated |
| `getPoolLiquidity(pool, window=0)` | Current and harmonic liquidity; zero window uses current defaults |
| `getFeedLiquidity(asset)` | Current, harmonic over stored window, and stored absolute minimum |
| `pendingQuoteCount(quote)` | Count of pending add/update proposals using the quote |

## Proposal-bound policy and admission

`FeedDefaults` is `(twapWindow:uint32, maxObservationAge:uint32,
minLiquidityRatio:uint256)`, initialized to `(3600,1800,5000)`. Valid windows
are 1800–14400 seconds; `0 < age <= window`; `0 < ratio <= 10000`. The defaults
setter is untimelocked because it only affects future proposals.

`UniV3FeedConfig` stores, in order: `pool:address`, `fee:uint24`,
`quoteAsset:address`, `assetIsToken0:bool`, `assetDecimals:uint256`,
`quoteDecimals:uint256`, `baseLiquidity:uint128`, `twapWindow:uint32`,
`maxObservationAge:uint32`, `minLiquidity:uint128`.

At proposal, each zero window/age argument independently resolves to the
current default. The source snapshots token identity/decimals and harmonic
liquidity over the resolved window, then stores:

```
minLiquidity = ceil(baseLiquidity * minLiquidityRatio / 10000)
```

Baseline and minimum must be positive. Both token decimals must be at most 18.
The pool factory, ordered token pair, fee and canonical factory `getPool` entry
must match. Admission requires actual `observationCardinality >= window + 1`,
compared in uint256, and a successful price probe. CardinalityNext alone is
insufficient. The probe skips the priced-asset scale guard so a proposal can
start while the desk has an incompatible cached scale (D19).

Same-instance quote cycles are rejected: the quote cannot have an active feed
or pending action here, and the asset cannot be a quote of an active feed or
have nonzero `pendingQuoteCount`. Successful proposals increment the quote
count. Successful confirmation or explicit/identity cancellation decrements
exactly once. Reverts preserve the count. Disable proposals carry no quote.
An update protects the active feed's old quote until replacement confirms.

Every update re-baselines, including a same-pool update. Defaults changes do
not rewrite active feeds or in-flight proposals. The read path never reads
`feedDefaults`; it uses the stored window, age and absolute minimum. It
requires positive current liquidity and both current and harmonic liquidity
at least the stored minimum, a valid unlocked slot0, initialized latest
observation, and latest observation age at most the stored age.

At most one observation is written per second, on any chain. A full ring of
N slots spans at least N−1 seconds; successful admission `observe` plus
`cardinality >= window + 1` protects the lookback under subsequent one-second
writes. The extrapolated fraction is at most `min(age/window,1)`. The default
1800/3600 configuration bounds it to 50%; this is not a universal feed bound.

## Precision and arithmetic

Mean tick is the mathematical floor of signed cumulative delta/window;
accumulators wrap at int56/uint160 before widening. Harmonic liquidity is
`floor(window * (2**160-1) / (secondsPerLiquidityDelta << 32))`, with zero or
out-of-uint128 results unavailable.

Tick math quotes `10**assetDecimals * 10**18` raw units, then the USD step is
`mulDiv(quoteScaled, quotePrice18, 10**quoteDecimals * 10**18)`. Tick range is
−887272 through +887272. The square uses Q192 when the sqrt ratio fits uint128,
and the full-width Q128 branch above that boundary. Multiplication uses a
512-bit intermediate; unrepresentable final uint256 results and zero quotes
are unavailable, not arithmetic panics. Both orders at the extreme ticks,
amount 1e36, low-decimal sub-cent assets and independent Fraction bounds are
tested. Existing typed dependency call failures propagate; PriceDesk isolates
those reverts under its unchanged source stipend.

## Confirmation, scale recovery and cancellation

Add and update confirmations retain distinct active-state predicates. Their
order is fixed:

1. Governance, pause, pending action and correct active-state checks.
2. Re-read identity and canonical factory mapping. Drift cancels, emits once,
   and returns false, even before the timelock is ready.
3. Structural and loop checks, plus priced-asset scale compatibility; failures
   revert with `invalid feed`. There is no confirmation-time price probe.
4. Confirm the action timelock; failure reverts with `time lock not reached`.
5. Stage the new config in active storage.
6. Qualify through the current PriceDesk, measuring the warm callback. Reject
   excess cost with `route too expensive`, then reject an unsuccessful/zero
   route with `price source not executable`.
7. Clear pending state, decrement the quote count, enumerate a newly added
   asset, and emit the confirmed event.

Transient price, liquidity, OLD, locked pool, zero quote, callback and scale
failures revert the transaction, preserving the proposal and undoing staged
config and timelock consumption. Identity drift alone auto-cancels. The
internal cancellation helpers emit, so explicit cancels do not emit twice.
Disable confirmation has no identity check or dependency reads.

At confirmation and each price read, `PriceDesk.tokenScale(asset)` must be zero
or exactly `10**snapshotAssetDecimals`. Only the priced asset is guarded;
permissionless first scale sync and quote-scale hardening are a separate desk
follow-up. See the [V3 operator runbook](uniswap-v3-twap-runbook.md) for both
`[syncTokenScale, confirm]` recovery sequences and the returned-false batch case.

## Quote route, economics and gas qualification

D4 is operator policy only. Every potentially authoritative quote source,
including fallback, must never call back into PriceDesk (for example Chainlink,
Pyth or Stork). V3 must be after every quote source; recheck after registry or
priority changes. There is no on-chain source allowlist or priority walk.
Cross-instance and wrapper cycles, including wsuperOETHb-style routes, remain
possible; independent fallback removal can make both reads return zero.
Desk fallback provides availability, not independent corroboration.

Relative floors do not prove economic depth. Before proposal, check token
upgradeability/decimals mutability and run the pinned, read-only
`scripts/twap_pool_depth.py`. It walks tickBitmap/ticks, applies liquidityNet
crossings, and reports fee-inclusive 1%/2% spot depth separately by direction,
marked using the pinned live PriceDesk quote. Governance must record the
minimum acceptable smaller-direction 2% depth in the runbook before proposal.

`MAX_WARM_QUALIFY_GAS = 170000`. The measured warm-to-cold delta is 9115, so
ceiling + delta = 179115 <= 210000. The pre-callback/read intersection is:
source, pool, desk and RipeHq addresses; all ten staged feedConfig[asset]
slots; PriceDesk.tokenScale[asset]; RipeHq.addrInfo[7].addr. Pool observation,
slot0 and liquidity storage are cold; metadata immutables do not warm those
slots. HQ entry 5 and MissionControl pricing policy are first touched during
the callback. T11 prints concrete addresses and slot indices and checks the
intersection against execution reads for both add and update.

This is a scoped guarantee for that touch set. An adversarial metadata path
can warm additional quote storage and pass confirmation while failing the
cold outer route; T11 preserves that demonstration and separately checks the
quote's own stipend. T22 covers RH-shaped and fat registries. Successful
confirmation does not replace cold qualification of a production route; the
CI cold tests are the qualification.

## Events, constants and revision-bound measurements

Pending add/update events log resolved window and maxObservationAge, absolute
minLiquidity, baseline, confirmationBlock and actionId; confirmed add/update
events log resolved window, maxObservationAge and minLiquidity. All include
asset/pool and quote; updates also identify prevPool. Cancel events identify
asset/pool, plus prevPool for updates. Disable pending includes confirmationBlock
and actionId; disabled/cancelled identify asset/pool. FeedDefaultsSet has exactly
window, age and ratio. Exported ABI is `scripts/abis/UniswapV3TwapPrices.json`;
the internal math module has no standalone ABI.

Constants: HUNDRED_PERCENT=10000, NORMALIZED_DECIMALS=18,
MAX_PRICED_ASSETS=50, MIN_TWAP_WINDOW=1800, MAX_TWAP_WINDOW=14400,
MAX_WARM_QUALIFY_GAS=170000; math uses canonical Q32/Q64/Q128/Q192 and tick bounds.
Unused sqrt-ratio constants were removed.

Contract implementation `8a9b90ec`, measurement comment/tests `cb69a688`:
Vyper 0.4.3 codesize, Python 3.12, Titanoboa 0.2.7. Runtime is 20650 bytes
(target <=22500, EIP-170 <=24576). The original 20-case matrix's maximum
successful forwarded source cost is 165782; its bounded late-failure maximum
is 174984. Intentional hostile stipend burn reaches 248173 and is a
fault-isolation case. Expanded T11 has admitted cold samples up to 179008;
T22's fat-source-last sample is 183235. These are measured maxima over named
fixtures, not a universal worst-case proof. Hard per-source stipend is 250000;
engineering forwarded target remains <=210000. The complete per-item table
and final-head evidence are maintained in the test README/evidence record.

Provenance facts: production math derives from pinned MIT V4 TickMath/FullMath;
V3 behavior references are separately licensed, compiled and hash-bound. The
upstream lock and notices are retained. Owner decision D16 closes legal review
as an implementation gate.

## Appendix A: historical specification (superseded 2026-09-09)

The following original packet, including its intermediate Revision 6 note, is
retained as history. Its old decisions, interfaces and gates are superseded by
the current body above and owner decisions D1–D20 dated 2026-09-09.

# Reusable Uniswap V3 TWAP price source — implementation specification

Revision 5 · September 7, 2026 · RIPE Protocol · contracts and tests handoff

> **Revision 6 note (September 9, 2026).** The shipped `UniswapV3TwapPrices.vy`
> was simplified to the repository's standard price-source pattern after review:
> typed `staticcall` reads instead of gas-bounded `raw_call`s, WETH priced through
> `PriceDesk.getPrice(WETH)` instead of a bound Chainlink anchor, per-operation
> add/update/disable functions and events like `ChainlinkPrices`, asset decimals
> snapshotted per proposal, and the standard `(min, max, 0, max)` time lock
> initialization. Sections 3–6 below describe the earlier design; where they
> conflict with the contract (administrative ABI, anchor, decimal binding, desk
> scale check, bounded calls and failure reserve, `quoteStaleTime`), the contract
> and `tests/priceSources/uniswap_v3/README.md` are authoritative. The quote asset
> is now whichever pool token is not the asset (any desk-priced token, not only
> WETH); per-feed liquidity minima became one governance ratio of the liquidity
> snapshotted at proposal, with window / observation-age defaults and an
> observation-cardinality floor in `feedDefaults`. The math module, reference
> artifacts, provenance and licensing requirements are unchanged.

## 1. Objective, authority and scope

Build `UniswapV3TwapPrices.vy`, a reusable Vyper 0.4.3 RIPE `PriceSource` for a governance-selected ERC-20/WETH Uniswap V3 pool. Use **PONS, CASHCAT, Artificial Inu (AI), and INDEX** as offline and fork-test targets. PONS is the token called “pawns” in discussion; INDEX's reported on-chain symbol is `Index`. These labels do not establish borrowing readiness.

Return an **18-decimal USD price for one whole asset token**:

```text
geometric historical token/WETH TWAP × validated current ETH/USD price
```

This is not an arithmetic USD TWAP over the historical interval. V1 assumes the bound WETH represents ETH 1:1. That denomination assumption, the chosen WETH implementation and the ETH/USD feed's identity require deployment qualification; neither a description string nor a valid numeric answer proves them. Do not add a WETH/ETH conversion pool.

This spec controls the implementation packet's behavior over earlier research recommendations. Subsequent user instructions can amend it. The broader collateral roadmap is not implementation background reading.

**Keep the assignment focused on contracts and tests.** No separate design memo, comprehension exercise, monitoring runbook, market/cadence research, qualification report or deployment preparation is required. Keep run commands and essential fixture/license/constructor notes in one short test README. Preserve every contract, arithmetic, failure, gas and integration requirement below. The small inventory/export/test-selection edits in §§7/9 are the only ancillary integration work.

The fresh implementation agent receives only the implementation prompt, this full spec, `docs/priceSources/uniswap-v3-twap-reference-vectors.json`, `docs/priceSources/uniswap-v3-twap-upstream-lock.json`, and access to the pinned repository/named files below. It does not need the research chat, roadmap or reviewer/resolution logs. Recording these selections finalizes the plan; it does not start implementation. Implementation starts only when the user assigns that task.

**Decision record.** Selected 2026-09-07. Confirm these three rows match the prompt and upstream lock before porting. Do not reopen them unless the user issues a new instruction.

| Decision | Selection | Status |
|---|---|---|
| D1: pool count and observation-age domain | Single-pool v1; age domain 1–86,400 seconds independent of lookback; ordinary lab age 3,600 seconds | Selected |
| D2: engineering targets | Aim for 210,000 source gas / 22,500 bytes; permit local completion above targets when actual hard-limit and all safety tests pass | Selected |
| D3: production math provenance | Pinned MIT TickMath/FullMath derivation; separately licensed V3 behavioral test references | Selected |

Single-pool v1 omits an enforced agreement guard: an off-chain disagreement cannot block its on-chain valuation. The age domain can admit an entirely extrapolated interval. These are explicit scope/availability tradeoffs, not consequences proved necessary by the raw gas estimates. No decision here approves production feed settings, legal treatment contrary to upstream terms, or deployment.

| Choice | V1 |
|---|---|
| Venue and bindings | One immutable canonical V3 factory, one immutable WETH with 18 decimals, one immutable direct Chainlink ETH/USD feed per source deployment. |
| Pools per asset | Exactly one active pricing pool. No secondary-pool or deviation fields in the contract ABI. |
| Other pools | Optional numerical comparison tests only. No monitoring work, on-chain agreement check or automatic response. |
| Lookback | Per feed, `MIN_TWAP_WINDOW = 1800` to `MAX_TWAP_WINDOW = 14400` seconds inclusive. |
| Observation age | Per feed, `1..MAX_OBSERVATION_AGE = 86400` seconds, independent of lookback. No default 24-hour setting. |
| Liquidity | Separate positive minimum current and harmonic liquidity, in that pool's raw units. |
| Administration | LocalGov, Addys, PriceSourceData and TimeLock; nonzero feed-action delay from deployment. |
| Storage | On-demand prices, no last-good cache, manual price setter or source-owned observation history. |
| Initial state | No active or pending feeds; administrative pause initially false. Constructor tests leave the source unregistered. |
| Snapshot | `addPriceSnapshot` returns `False`, with no mutation or external call. |
| Capacity | At most 50 active assets, preserving correct removal/re-add enumeration. |

Do not implement or design NET/sNET, PairOracle, Pyth, Stork, USDG quote routes/comparisons, V2, V4 pools/hooks, LP-token valuation, multi-hop pricing, liquidation routes, LTVs, deposit/debt caps, farm changes, migrations or MissionControl changes. The MIT math-reference choice in §4 is the sole V4-related exception. Do not revive the inert V2 monitor. Those workstreams remain separate. Local EVM deployments and fork simulations are necessary tests; production deployment, registration, transactions and activation are excluded.

An additional lower-priority PriceDesk source would be an availability fallback, **not corroboration**: the desk accepts the first usable price. Adding this source does not change that behavior.

## 2. Repository integration and failure contract

Reference base: `7916d2f7327198e39513308135e244306de52c6b`, on `codex/rh-reviewed-correctness-fixes` in the reference checkout named by the implementation prompt. Do not branch from `master`. The immutable base pin is authoritative; a branch name can move. This is a source-code binding, not an attestation of deployed bytecode.

Read these repository files in full where relevant to the new source:

- `interfaces/PriceSource.vyi`; `contracts/priceSources/ChainlinkPrices.vy`.
- `contracts/priceSources/modules/PriceSourceData.vy`; `contracts/modules/{TimeLock,LocalGov,Addys}.vy`.
- `contracts/registries/PriceDesk.vy`; the existing full-precision helper in `contracts/vaults/modules/SharesVault.vy`.
- `tests/priceSources/test_chainlink_prices.py`; `tests/registries/test_price_desk_isolation.py`; `tests/registries/test_price_desk_gas.py`; `tests/conf_utils.py`, especially `advance_timelock_blocks` and the initialization-only behavior of `ensure_token_scale`.
- `tests/conf_core.py`: constructor calls in `ripe_hq_deploy`, `mission_control` and `price_desk_deploy`, and the registry wiring in `ripe_hq`/`price_desk`. These are decorated pytest fixtures, not directly callable deployment helpers; follow §8's plain subprocess-helper pattern. Read `contracts/config/SwitchboardGolf.vy`'s `executePendingAction` for its zero-scale-only initialization; this contract remains outside the edit scope.
- `tests/test_price_desk_aggregate_source_count_guard.py`; applicable `tests/inventory/` checks.
- `scripts/export_abis.py`; `pytest.ini`; `tests/{conftest,conf_env}.py`; `.github/workflows/python-tests.yml`; `tests/test_lean_shard_coverage.py`; the block-clock explanation in `config/BluePrint.py` and the FinishSetup example `migrations/base-mainnet/2025071507_FinishSetup.py`. The latter two are read-only context, not allowed edits.

Paths in this spec are repository-relative so its committed copy remains portable. Preserve every selector, default-argument overload and return shape in `PriceSource.vyi`. Source-specific proposal methods are additional ABI, specified in §3.

| Source state | `getPrice` | `getPriceAndHasFeed` | `hasPriceFeed` |
|---|---:|---|---|
| No active feed, pending ADD only, or confirmed disabled | 0 | `(0, False)` | False |
| Active and valid | Positive USD18 | `(price, True)` | True |
| Active but unusable, including invalid nonzero caller forwarding | 0 | `(0, True)` | True |
| Pending UPDATE or DISABLE | Evaluate old active config | Old active coverage | Old active coverage |

Coverage/enumeration/pending getters are storage-only. `hasPendingPriceFeedUpdate(asset)` is true for any uncleared pending ADD, UPDATE or DISABLE. An expired action remains pending until cancelled: TimeLock's `hasPendingAction` tests existence, not whether confirmation is currently allowed.

### Caller and quote freshness

- `_staleTime == 0` is the direct-call sentinel, never “disable freshness.” With zero, ignore the supplied registry for authority/dependency selection.
- Accept nonzero `_staleTime` only if both `msg.sender` and the supplied PriceDesk/registry argument equal HQ's **current** PriceDesk. A forged or unreadable identity makes an active feed unavailable. Do not cache a former desk indefinitely.
- A feed's `quoteStaleTime == 0` inherits the authenticated forwarded policy, or canonical MissionControl for a direct call. A nonzero local value is an **absolute override**, not `min(global, local)`.
- `MIN_LOCAL_STALE_TIME = 300`; `MAX_EFFECTIVE_STALE_TIME = 604800`. Inherited policy must be in `(0, 604800]`; explicit local policy in `[300, 604800]`.
- Resolve inherited policy once. Unreadable/invalid policy is unavailable only when inheritance is needed. An explicit local override does not depend on the global age value **inside the source**.
- PriceDesk still reads MissionControl before calling sources, even with a local override. Its own upstream failure can revert the outer call; this source does not remove that dependency.
- Quote age governs only the dollar leg. Pool lookback and observation age are separate, in seconds.
- Pause retains PriceSourceData's administrative meaning: it blocks governed feed mutations, including cancellation/disable, but does not stop price reads. It is not an oracle circuit breaker.

### Actual PriceDesk composition

Assuming the desk's own configuration reads succeed, and absent another usable source:

| Situation | Non-strict `PriceDesk.getPrice` | Strict |
|---|---:|---|
| Every contacted source reports no feed | 0 | 0 |
| Active feed returns unavailable | 0 | Revert: `has price config, no price` |
| A source reverts or returns malformed/inconsistent data | 0 | Same revert |
| Any later eligible source returns a usable price | That price | That price |

This table concerns price retrieval. Missing token scale has its own valuation behavior in §3. Do not equate an unavailable feed with collateral being safely valued at zero. Unavailability can block health checks and liquidation, while fallback may bypass this source entirely.

## 3. Exact administrative ABI and lifecycle

Use the following public ABI names, field order and types; internal helper names and storage packing remain implementation choices:

```text
constructor(
  ripeHq: address, tempGov: address,
  minActionTimeLock: uint256, maxActionTimeLock: uint256,
  factory: address, weth: address, ethUsdFeed: address
)

struct FeedParams:
  pool: address
  twapWindowSeconds: uint32
  minCurrentLiquidity: uint128
  minHarmonicLiquidity: uint128
  maxObservationAgeSeconds: uint32
  quoteStaleTime: uint256

struct UniV3FeedConfig:
  params: FeedParams
  assetIsToken0: bool
  assetDecimals: uint8
  fee: uint24

# Numeric operation values: NONE=0, ADD=1, UPDATE=2, DISABLE=3.
struct PendingUniV3Feed:
  actionId: uint256
  kind: uint256
  config: UniV3FeedConfig

addNewPriceFeed(asset: address, params: FeedParams) -> bool
updatePriceFeed(asset: address, params: FeedParams) -> bool
getFeedConfig(asset: address) -> UniV3FeedConfig
getPendingFeed(asset: address) -> PendingUniV3Feed
getBoundAssetDecimals(asset: address) -> (bool, uint8)
```

Also implement the interface's exact confirm/cancel/disable methods; do not add variants of proposal methods with ambiguous defaults. All successful mutations return True where the interface declares bool. Failed confirmations revert; they never return False. The full tuple always replaces the full tuple, and zero quote age explicitly restores inheritance.

`getFeedConfig` returns the fully zeroed config for an unknown or disabled asset. `getPendingFeed` returns the fully zeroed pending struct after confirmation/cancellation or for no action. An expired uncleared action retains its complete pending struct. `getBoundAssetDecimals` returns `(False, 0)` before any successful binding, `(True, 0)` for a bound zero-decimal asset, and retains the bound result after disable.

Export immutable getters `factory() -> address`, `weth() -> address`, `ethUsdFeed() -> address`, and `anchorDecimals() -> uint8`.

Events are `UniV3FeedProposed`, `UniV3FeedConfirmed` and `UniV3FeedCancelled`. Each has indexed `asset: address` and `actionId: uint256`, followed by `kind: uint256`. Proposed/Confirmed additionally expose, in order: `confirmationBlock: uint256`, `expirationBlock: uint256`, then the six flattened FeedParams fields and `assetIsToken0: bool`, `assetDecimals: uint8`, `fee: uint24`. Use the types above. Cancellation is linked to the complete proposal by actionId. For DISABLE, proposal/confirmation events carry the config being removed. This fixes the public event schema without requiring nested struct event encoding.

### Constructor and admission

Initialize modules with these exact argument meanings, subject to their existing validity checks:

```text
gov.__init__(ripeHq, tempGov, 0, 0, 0)
addys.__init__(ripeHq)
priceData.__init__(False)
timeLock.__init__(minActionTimeLock, maxActionTimeLock, minActionTimeLock, maxActionTimeLock)
```

Do not copy Chainlink's `(min, max, 0, max)` TimeLock initialization. The minimum is the initial delay; the maximum is the expiration **duration after unlock**, so an action expires at `proposalBlock + initialDelay + expirationDuration`. There is no zero-delay setup phase. The inherited `setActionTimeLockAfterSetup` rejects with `already set`; do not override it to reopen setup.

Include this constructor caveat in the source comment or short test README: **exclude this source from any FinishSetup-style `setActionTimeLockAfterSetup` sweep; its delay is already set in the constructor.** Test that rejection on a fresh deployment. Existing migration scripts remain unchanged; no deployment notes or migration work is required.

Administrative delays use contract-visible `block.number`; confirmation is allowed in `[confirmationBlock, expirationBlock)`. On Robinhood, the repository models this as an L1 ancestor estimate, approximately five increments per minute, rather than the much faster RPC child height. At that modeled cadence, 21,600 counts is roughly three days and 302,400 roughly six weeks (42 days), not seven weeks. Those are existing PriceDesk **registry** bounds for context, not chosen feed-action delays for this source. Deployment must choose the constructor inputs in the correct clock domain. Oracle lookback/freshness uses seconds.

Keep RPC state-selection height/hash, timestamp, and contract-visible NUMBER distinct in evidence. Installed Boa sets its fork's NUMBER from the RPC child header; that is a local emulation choice, not proof of Robinhood's live governance clock. Preserve lifecycle assertions against the local clock, but never assert that real EVM NUMBER equals the pinned child height. Use `advance_timelock_blocks` to advance governance blocks without aging the pinned oracle timestamp, and assert the timestamp is unchanged across fixture setup.

Validate nonzero contract identities for HQ/factory/WETH/anchor, WETH decimals exactly 18 and anchor decimals in 0..18; bind anchor decimals for the deployment. Temporary governance follows LocalGov's rules and need not be a contract. Preserve module validation for governance/timelock constructor arguments. There is no constructor token list.

For ADD and UPDATE proposals, and again at confirmation:

1. Reject zero, native-token sentinel and WETH as the asset. Require asset decimals in 0..18. Bind the proposed metadata and never silently replace it during confirmation.
2. Validate that the selected pool contains exactly asset/WETH, that `pool.factory()` equals the bound factory, and that `factory.getPool(asset, WETH, pool.fee())` returns the exact selected pool. Validate token order and the fee's width; derive metadata from bounded calls. Canonical factory identity is a deployment requirement, not something proved merely by these matching getters.
3. Validate window, observation-age and quote-age domains, positive representable liquidity thresholds, and initialized usable pool state.
4. Enforce the permanent decimal rule below. At confirmation, check canonical PriceDesk's existing tokenScale: zero is allowed for source-only admission, matching scale is allowed, a nonzero mismatch or unreadable/malformed response rejects confirmation.
5. Require a usable candidate price under the proposed settings. A rejected proposal must create no action or decimal binding. A failed confirmation must preserve the proposal and previous active state.
6. Revalidate proposed asset decimals, pool token order/factory/fee and anchor decimals against their bound values. Pool price and liquidity may evolve, but derived identity metadata cannot amend a pending action.

There are no production defaults for liquidity, observation age or quote freshness. Bounds establish accepted input domains. A setting that merely passes a numerical or gas test is not an economically qualified setting.

### Permanent decimals and PriceDesk token scale

Bind asset decimals on **first successful ADD confirmation**, using a separate bound flag because zero-decimal tokens are valid. Preserve that binding through UPDATE, DISABLE and re-ADD. Cancelled/failed initial admission does not bind. With an existing binding, a changed decimal value cannot be adopted by updating the feed or cycling disable/re-add.

Every active read compares live asset decimals and anchor decimals to their bindings. It also resolves HQ's current canonical PriceDesk with a bounded read and reads that desk's `tokenScale(asset)` with a bounded read. Require a valid desk identity/response and a scale of either **zero or exactly `10**boundDecimals`**. A nonzero mismatch makes the source unavailable even when token decimals have returned to the bound value. Apply this compatibility check to all active price reads, including direct calls, callback reads with stale argument zero, and forwarded calls. Reuse the same resolved desk for caller authentication; do not cache a previous desk across rotation or trust a caller-supplied desk.

Zero remains permitted for price-only reads/admission to avoid a bootstrap cycle; the unchanged desk rejects nonzero-amount valuation while its scale is zero. Coverage remains true while unavailable, so permissionless initialization can still occur. That operation is **not** treated as proof that the resulting scale is correct. The runtime mismatch check is what prevents this source from resuming a bad valuation after restoration.

Drift, scale mismatch or malformed required reads makes the feed unavailable. Restoring original decimals resumes pricing only if the current desk scale is zero or matching and every other guard passes. Intentional migration to new decimals requires separately coordinated recovery covering PriceDesk's scale; there is no v1 rebinding setter.

The source's unit is price per whole token. PriceDesk separately caches `10**decimals`. `qualifyCallerPriceSource` validates source execution, not amount conversion. This source must not call `syncTokenScale` or alter desk storage. Zero scale permits source admission and price-only reads, but nonzero-amount `getUsdValue`/`getAssetAmount` return 0 non-strictly and revert `missing token scale` strictly until scale setup. Zero-amount shortcuts still return 0.

Required regression with actual PriceDesk: admit/bind 18 decimals while scale is zero → token reports 6 → outsider permissionlessly calls `syncTokenScale` → scale becomes `10**6` → token restores 18. The source must remain `(0, True)`; with no usable fallback, both amount conversions return zero non-strictly and strict price/conversion calls revert. After governance or Switchboard re-syncs while live decimals equal the binding, both conversions must recover correctly. A $1 token and `10**18` raw units must never produce the erroneous USD18 value `10**30` through this source. Repeat with a newly HQ-current desk after rotation, and test the normal permissionless initialization path with unchanged decimals.

Repair a **nonzero wrong scale** with an explicit `PriceDesk.syncTokenScale(asset)` from governance accepted by that desk, or an address recognized by its HQ-current Switchboard. An arbitrary caller cannot overwrite it. Tests may deploy the local desk with an explicit `tempGov`, restore the token's bound decimals, call sync from that governor and assert the stored scale and both conversions. `SwitchboardGolf.executePendingAction` auto-syncs only a zero scale during non-NFT asset addition; it does not repair a nonzero mismatch. Likewise, `tests/conf_utils.py::ensure_token_scale` skips existing nonzero scales and can suppress a Boa error, so it is not a recovery assertion or a substitute for the explicit call.

Before describing valuations as qualified, require a matching nonzero scale. Test 0-, 6-, 9- and 18-decimal assets, disable/re-add, unknown/missing/wrong scale, caller/desk rotation, and both conversions. Another usable fallback can bypass this source's mismatch result, so the production fallback graph still needs independent scale qualification. This task does not repair PriceDesk or assert protection for arbitrary noncanonical desks. All new scale/identity reads enter the early gas budget.

Retain PriceDesk's existing dust behavior: positive sub-unit USD value can round up to 1. Its `price * amount` and `usdValue * tokenScale` intermediates are still checked uint256 arithmetic; the source's full-precision math does not remove extreme-input conversion overflow/reverts. Document and test that existing limit rather than editing the desk.

### Feed state transitions and confirmation atomicity

Only one pending action per asset, including expired uncleared actions. ADD requires no active feed; UPDATE/DISABLE require an active feed. Reject an exact full-config no-op UPDATE. Pending ADD does not count as active capacity, so recheck the 50-active limit at confirmation; another pending ADD may have filled the last slot.

All feed mutations require governance and an unpaused administrative state. For add/update confirmation, enforce operation, active-state, capacity and timelock predicates, then revalidate candidate metadata and scale. Candidate validation uses the proposed metadata without requiring a pre-existing first-ADD binding; ordinary external reads still use only active state. Next assert `timeLock._confirmAction(actionId)` with `# dev: time lock not reached`. That helper clears the action on success: consume it only within this same transaction, which must fully revert on any later failure.

After consumption and before the callback, provisionally write the complete active config and, for the first ADD, the bound-decimals flag/value. During the callback, `getFeedConfig` sees the candidate, `getBoundAssetDecimals` sees the provisional binding, and `hasPriceFeed`/price reads derive active coverage from that config, **not enumeration**. Enumeration remains unchanged until success. The pending source proposal remains readable and `hasPendingPriceFeedUpdate` remains true until finalization; TimeLock's separate `hasPendingAction` is false after consumption. Rollback restores both records on failure. Then call the **canonical `PriceDesk.qualifyCallerPriceSource(asset)` with default stale argument 0**. Nonzero callback stale time is rejected by the current desk as `(0, 2)`.

Require positive callback price and status 1. The desk calls the candidate itself under 250,000 gas; unrelated registered sources cannot rescue it. The desk must exist even when the candidate is unregistered. Do not copy Chainlink's missing-desk bootstrap exception. Local fixtures already provide the canonical desk.

Only successful completion finalizes enumeration, clears remaining pending state and emits confirmation. Any provisional config/binding, consumed action, enumeration delta and transaction logs revert on failure; the pre-existing proposal and its earlier proposal event remain. Require first-ADD success for both zero- and 18-decimal assets and explicit rollback tests. Do not introduce a reentrancy lock that prevents the desk's required static callback into the staged source.

| Confirmation condition | Required result |
|---|---|
| Not yet confirmable or expired | Revert; preserve pending action and active config |
| Changed metadata, bad price, scale mismatch or callback failure | Same atomic rollback; no cancellation event |
| Valid ADD/UPDATE and positive callback status 1 | Commit full config and clear action |
| Valid DISABLE, even if pool or quote is broken | Remove active config/enumeration; retain permanent decimals; clear action |
| Cancel, including expired action, with correct operation | Clear pending action only; no pool, quote or desk dependency |

This deliberately differs from Chainlink's mixed behavior: it auto-cancels some invalid revalidations before consumption, while later callback assertions revert. V1 always reverts failed confirmations. DISABLE and cancellation never need a working pool, quote or desk; an administrative pause still blocks them.

### Revert catalog

Use these exact `# dev:` strings for the new source's assertions. These are Boa developer-revert annotations, not a promise of distinct production revert payloads. Test each cause with all preceding predicates valid. Invalid external calldata may be rejected by Vyper's ABI decoder before these checks.

| Predicate, in validation order where applicable | Developer string |
|---|---|
| Unauthorized | `no perms` |
| Administrative pause | `contract paused` |
| Invalid constructor dependency identity/decimals | `invalid dependencies` |
| Forbidden asset | `invalid asset` |
| ADD while active | `feed already exists` |
| UPDATE/DISABLE without active feed | `no active feed` |
| Proposal while any action remains pending | `pending feed action` |
| Confirm/cancel without pending action | `no pending feed action` |
| Pending kind differs from invoked selector | `wrong feed operation` |
| Confirmation outside allowed interval | `time lock not reached` |
| Invalid numeric domain, pool identity, or unusable proposal | `invalid feed` |
| Exact no-op UPDATE | `no change` |
| Existing permanent decimal binding differs | `asset decimals changed` |
| Proposed identity metadata no longer matches | `feed metadata changed` |
| Missing/malformed canonical desk or nonzero wrong tokenScale | `invalid price desk` / `token scale mismatch`, respectively |
| Candidate source callback fails, has zero price or status other than 1 | `price source not executable` |
| 51st active asset | `too many assets` |

Existing module-owned assertions retain their existing strings. For overlapping conditions, follow the lifecycle order above and make any necessary finer ordering explicit in the relevant test; do not make tests depend on an unlisted accidental decode revert. Runtime price-read failures in §4–5 return unavailable, not these administrative reverts.

## 4. Complete price path and exact arithmetic

### Pool read and guard sequence

For an active feed, resolve HQ's current desk once, enforce the §3 scale compatibility check, authenticate nonzero forwarding, resolve effective quote age, and validate live asset/anchor decimals. Use HQ-bound identities, never an address supplied by the caller to choose a dependency. On the hot path, use bounded raw reads for required HQ/MissionControl/desk-scale lookups as well as market dependencies; importing Addys must not accidentally introduce unbounded typed calls where this spec requires unavailable-on-failure behavior. Its immutable HQ getter can be reused without an external lookup. PriceDesk's own upstream failure behavior does not remove this source's direct-call and authentication obligations.

For the one bound pool:

1. Read canonical `slot0()`; require initialized state and `unlocked == True`.
2. Require `liquidity() >= minCurrentLiquidity > 0`.
3. Read `observations(observationIndex)` using the returned index. Require initialized and compute age as uint32 modular subtraction of observation timestamp from `block.timestamp % 2**32`. Age must be at most the configured ceiling; equality passes.
4. Call exactly `observe([twapWindowSeconds, 0])`. Validate its two arrays as specified below. `OLD`, insufficient history or any ordinary dependency failure means unavailable. Never shorten the interval, substitute spot, increase cardinality or write an observation.
5. Decode each accumulator to its actual width, compute the modular delta at that width, then widen: signed int56 for cumulative ticks and unsigned uint160 for cumulative seconds per liquidity. Checked subtraction at the narrow width would reject valid wraps.
6. Calculate mean tick as **mathematical floor** of signed tick delta divided by the positive window, then validate the Uniswap domain `[-887272, 887272]`. A zero tick delta is valid and produces mean tick zero; constant tick zero and cancelling positive/negative contributions are both valid. It is the seconds-per-liquidity denominator, not the tick delta, that must be nonzero.
7. Match the pinned OracleLibrary harmonic-liquidity calculation:

   `floor(window * (2**160 - 1) / (secondsPerLiquidityDelta * 2**32))`.

   Reject zero denominator and a result above uint128 maximum; require harmonic liquidity at or above its positive threshold. The numerator and shifted denominator fit uint192 for the permitted inputs. On malicious values, reject a nonrepresentable result rather than reproducing a narrowing cast's truncation.
8. Quote `10**assetDecimals` raw asset units into raw WETH using upstream `getSqrtRatioAtTick` and `getQuoteAtTick`, including both numeric-address-order branches. A zero quote is unavailable.

For a zero-decimal asset, one whole token is one raw unit. Its positive theoretical value can be less than one raw WETH unit (one wei), so the canonical integer quote legitimately rounds to zero. Keep this unavailable result; do not clamp it to one wei or treat zero-decimal assets as categorically unsupported. A separate positive-price fixture must still prove successful first ADD at decimals 0.

The observation-age ceiling limits extrapolation, not guaranteed trade age. Liquidity actions can write observations; some swaps do not create a distinct observation. For example, with a 30-minute lookback, an eight-hour-old last observation and a 24-hour configured ceiling, **both requested endpoints can be extrapolated after the last observation**, with no newly recorded observation inside the window. V1's proposed domain permits this when every guard passes; it does not certify fresh market information.

Test explicit outcomes: with lookback 1,800 and age ceiling 3,600, latest-observation ages 1,799/1,800/1,801 all pass the age predicate; a fully extrapolated valid interval at age 3,000 can return a price; age 3,600 passes and 3,601 fails. A boundary-only fixture may use age ceiling 86,400 to exercise the eight-hour example. Do not use 86,400 as the ordinary lab or a recommended candidate setting. Under an age ceiling equal to lookback, lookback+1 fails. These predicates are separate from sufficient history, liquidity and anchor freshness.

After a halt, a new observation can satisfy the age check without establishing a fresh full historical interval. Test passing guards returning the extrapolated/historical result and stale anchor or other failing guards returning unavailable; do not assert a nonexistent restart circuit breaker. Current/harmonic liquidity thresholds do not prove manipulation is uneconomic or establish stressed liquidation proceeds. Longer age limits need cadence and economic evidence, and actual per-asset settings remain unapproved.

### Vyper arithmetic requirements

Verified in the repository's Vyper 0.4.3 environment:

```text
Vyper: -1801 // 1800 = -1; -1801 % 1800 = -1
Required mean tick: floor(-1801 / 1800) = -2

delta = widen(unsafe_sub(narrow_new, narrow_old))
mean = delta // window
if delta < 0 and delta % window != 0:
    mean -= 1
```

`unsafe_sub` on int56 and uint160 operands gives the required narrow wraps. Do not widen operands first. Test positive/negative divisible and non-divisible deltas and both accumulator wrap boundaries.

In TickMath, the initial Q128 ratio can equal `2**128`; multiplication by each selected constant, which is below `2**128`, still fits uint256. Subsequent products use the canonical `>> 128` truncation. Positive ticks invert with `(2**256 - 1) // ratio`. Converting Q128.128 to Q64.96 rounds up exactly as upstream. Do not replace this sequence with one theoretical exponentiation and a final rounding.

Preserve both quote branches: square directly only when the sqrt ratio fits uint128; otherwise use full-precision multiplication/division by `2**64` to form the Q128 ratio. Implement floor `mulDiv` with a 512-bit intermediate when needed. Distinguish a representable quotient despite intermediate overflow from an unrepresentable quotient. Use internal status returns/prechecks so invalid math inputs reach the public unavailable result.

The SharesVault helper is reference material; do not import vault state, refactor shared math, or assume copying it proves correctness. Use no floating point, approximate exponentiation or externally deployed mutable math helper.

### Dollar anchor

Read the bound anchor directly; no recursive `PriceDesk.getPrice(WETH)`. Require:

- Exact canonical ABI and unchanged anchor decimals in 0..18.
- Positive answer and nonzero uint80 round ID; phase-encoded IDs above `2**64` are valid.
- `answeredInRound >= roundId`.
- `0 < updatedAt <= block.timestamp`, and age at most effective quote stale time.
- Safe normalization of the answer to USD18. `startedAt` must be a valid uint256 ABI word but does not add an independent freshness predicate.

Then return:

`floor(wethPerWholeAssetRaw * ethUsdPrice18 / 10**18)`.

Use full-precision multiplication/division when the intermediate overflows but the quotient fits. Final zero, division by zero or quotient/normalization overflow means unavailable; never saturate. Do not multiply again by asset decimals or by a user's balance.

### Production provenance and revision-pinned reference math

Under selected decision D3, derive the production math module from **MIT-licensed** [V4 TickMath](https://github.com/Uniswap/v4-core/blob/46c6834698c48bc4a463a86d8420f4eb1d7f3b75/src/libraries/TickMath.sol) and [V4 FullMath](https://github.com/Uniswap/v4-core/blob/46c6834698c48bc4a463a86d8420f4eb1d7f3b75/src/libraries/FullMath.sol), commit `46c6834698c48bc4a463a86d8420f4eb1d7f3b75`. This selects math-source provenance only; pools, factory admission and observe semantics remain V3.

The new math module should retain MIT treatment, the upstream copyright and full permission notice for its derived portions, with source provenance documented; RIPE-owned source integration keeps its existing license treatment. Do not represent the external MIT material as covered exclusively by the restrictive RIPE license. Do not alter the repository-wide license as part of this source task.

Port only the needed MIT tick-to-sqrt and floor-mulDiv operations, including the initial tick ratio and nineteen subsequent conditional multiplications. V4's `getSqrtPriceAtTick` corresponds to V3's `getSqrtRatioAtTick`; map names explicitly and retain V3 bounds and required output behavior. Do not import or port `BitMath`, `CustomRevert` or `getTickAtSqrtPrice` into the production Vyper module. The pinned Solidity reference project still needs the upstream import dependencies to compile its unmodified libraries. Write quote/mean/harmonic composition from this arithmetic specification, rather than copying the GPL V3 implementation text. Do not claim that this instruction or owner selection is a formal clean-room process or legal clearance.

The nineteen subsequent multiplier pairs and initial ratio agree between these pinned V3/V4 files; their round-up expressions are mathematically equivalent. A **compiled** V3/V4/production-port differential is still required; this source inspection does not replace it.

Use these pins, resolved during this revision; retain upstream notices and record any vendored dependencies from the same revisions:

| Repository | Exact commit | Required references |
|---|---|---|
| Uniswap v3-core, tag v1.0.0 resolved | `e3589b192d0be27e100cd0daaf6c97204fdb1899` | [TickMath](https://github.com/Uniswap/v3-core/blob/e3589b192d0be27e100cd0daaf6c97204fdb1899/contracts/libraries/TickMath.sol), [FullMath](https://github.com/Uniswap/v3-core/blob/e3589b192d0be27e100cd0daaf6c97204fdb1899/contracts/libraries/FullMath.sol), [Oracle](https://github.com/Uniswap/v3-core/blob/e3589b192d0be27e100cd0daaf6c97204fdb1899/contracts/libraries/Oracle.sol) |
| Uniswap v3-periphery | `0682387198a24c7cd63566a2c58398533860a5d1` | [OracleLibrary](https://github.com/Uniswap/v3-periphery/blob/0682387198a24c7cd63566a2c58398533860a5d1/contracts/libraries/OracleLibrary.sol) |

The companion `docs/priceSources/uniswap-v3-twap-upstream-lock.json` records separate production-port references, V3 behavioral references, dependencies/license text, SHA-256 values and URLs. Do not use a floating branch during implementation.

V3 TickMath and OracleLibrary carry GPL-2.0-or-later notices. V3 Oracle retains a BUSL-1.1 header, but the pinned [repository license](https://github.com/Uniswap/v3-core/blob/e3589b192d0be27e100cd0daaf6c97204fdb1899/LICENSE) specifies a Change Date no later than April 1, 2023 and a GPL-2.0-or-later Change License. Do not describe present use as relying simply on BUSL's original non-production grant. Keep V3 reference source/compiled fixtures and their applicable notices in the separate reference-test subtree; test-only labeling does not waive licensing obligations. Keep derivation and reference-artifact license notes with the reference tests. The provenance choice is not permission to disregard those terms.

Schedule legal review of the actual derivation, notices and distribution of reference artifacts before any mainnet deployment. This is a later release requirement; it does not add a legal-review prerequisite to local implementation once D3 is selected. Implementation must still preserve the applicable terms from the outset. The [pinned MIT notice](https://github.com/Uniswap/v4-core/blob/46c6834698c48bc4a463a86d8420f4eb1d7f3b75/licenses/MIT_LICENSE) expressly requires retaining its copyright and permission notice.

Require **bit-exact differential comparison** with separately compiled pinned upstream Solidity for TickMath and quote outputs, or independently generated vectors from that harness. Python big integers independently verify multiply/divide and modular arithmetic. Theoretical rational/high-precision formulas assess rounding error with justified bounds; they are not bit-exact substitutes for upstream's intermediate fixed-point rounding. No arbitrary epsilon to conceal mismatches. Tick rounding is not universally conservative after quote inversion.

Use separate reference projects/profiles: V3 Solidity 0.7.6, and V4 Solidity 0.8.26 with its pinned MIT dependencies. Record optimizer/EVM settings and artifact hashes. The existing `solidity/foundry.toml` is a CCIP build; leave it alone. Compiler availability must be checked early; obtain required pinned compilers in an isolated setup environment when needed, without modifying the reference venv. Ordinary Python CI consumes checked, reproducible local reference artifacts and must not fetch compilers or RPC state.

Before production math porting, create minimal compilable wrappers importing the needed pinned libraries and run `forge build --root tests/priceSources/uniswap_v3/reference/v3 --use 0.7.6` and `forge build --root tests/priceSources/uniswap_v3/reference/v4 --use 0.8.26`. Keep compiler versions/settings and reference-artifact identities with the reference tests; put runnable commands in the test README, without workstation-specific paths in committed files. Verify that each wrapper and its required libraries actually compiled; an empty project or missing artifact is not a successful check. Missing compiler downloads must surface here, with the affected gate incomplete and independent work continuing. These builds establish toolchain availability, not differential correctness.

Provide and run committed regeneration/check commands and exact compiled differential evidence before declaring implementation complete. Merely documenting a Forge command is insufficient. If compiler/setup access remains unavailable, finish independent work and label that required gate incomplete; do not waive it because the twelve frozen vectors pass. Those historical vectors cover 18-decimal tokens and only one quote-precision branch, so endpoints, the other branch and other decimals remain separate tests.

## 5. External-call ABI and unavailable outcomes

All price-path dependencies use static, explicitly gas-bounded calls with `revert_on_failure=False`. For an expected payload of **N bytes, capture N+1 and accept only length N**. Capturing N would conceal surplus bytes by truncation.

Validate raw words before a potentially reverting decode. `abi_decode` rejects malformed encodings by reverting; do not rely on that for the source's ordinary `(0, True)` contract. Do not use unchecked/unsafe decode without the complete checks.

| Response | N bytes / minimum capture | Required validation |
|---|---:|---|
| Scalar: address, decimals, fee, liquidity, HQ address, global age or tokenScale | 32 / 33 | Correct declared type; zero high bits for uint8/24/128/160 and addresses; semantic constraints at use |
| `slot0()` | 224 / 225 | uint160 sqrt ratio, sign-extended int24 tick, three uint16 values, uint8 feeProtocol, boolean exactly 0 or 1 |
| `observations(uint256)` | 128 / 129 | uint32 timestamp, sign-extended int56 cumulative tick, uint160 cumulative liquidity, canonical bool |
| `observe(uint32[])` for two inputs | 256 / 257 | Offsets exactly 64 and 160; array lengths exactly 2; sign-extended int56 tick words and uint160 liquidity words |
| `latestRoundData()` | 160 / 161 | uint80 round/answered IDs, canonical int256 answer, uint256 timestamps; semantic checks in §4 |
| Admission `qualifyCallerPriceSource` | 64 / 65 | Two uint256 words; price positive, status exactly 1 |

For observe's 32-byte words, require positions: `[64, 160, 2, tickPast, tickNow, 2, liquidityPast, liquidityNow]`. Reject short/long payloads, overlapping/reordered offsets, extra elements and noncanonical sign extension.

Valid initialized slot0 requires `MIN_SQRT_RATIO <= sqrtPriceX96 < MAX_SQRT_RATIO`, tick within the canonical domain, `1 <= observationCardinality <= 65535`, `observationIndex < observationCardinality`, `observationCardinality <= observationCardinalityNext <= 65535`, and unlocked true. Use pinned TickMath constants. Do not require slot0's tick to equal a fresh inverse calculation from its sqrt price: canonical tick-boundary states can differ. CardinalityNext need not be fully initialized. The selected current observation must be initialized separately.

Addresses/metadata used only at constructor/proposal/confirmation still require bounded, canonical responses. Governance may revert with the specified administrative reason on invalid inputs. The price path returns unavailable for:

| Active-feed condition | Result |
|---|---|
| Locked/uninitialized pool, bad index/state, stale observation, too little current/harmonic liquidity | `(0, True)` |
| OLD, zero seconds-per-liquidity delta, out-of-domain tick or invalid/unrepresentable quote | `(0, True)`; zero tick delta remains valid |
| Bad Chainlink round, stale/future timestamp, nonpositive answer, normalization overflow | `(0, True)` |
| Changed/malformed asset or anchor decimals; nonzero mismatched/malformed current desk scale | `(0, True)` |
| Forged nonzero forwarding or required identity/policy lookup failure | `(0, True)` |
| Dependency revert, no-code/empty response, malformed ABI or bounded gas exhaustion | `(0, True)` |

A caller can supply insufficient outer transaction gas; no source can guarantee it never reverts. PriceDesk's status-2 isolation remains required. Tests must show that ordinary bounded dependency failures leave enough source gas to return the specified result.

## 6. Gas, runtime size and early feasibility gate

| Budget | Requirement |
|---|---|
| PriceDesk source price call | Unchanged hard stipend: **250,000 gas** |
| Source coverage call | Unchanged stipend: **75,000 gas**; coverage remains storage-only |
| Snapshot call | Unchanged stipend: **150,000 gas**; hook remains a no-op |
| Complete cold source execution | Optimization target **at most 210,000 gas**, including current desk-scale checks, all source-invoked dependencies, validation, math and return; overrun disposition requires D2 |
| Constructor-bound deployed runtime | Optimization target **at most 22,500 bytes**; overrun disposition requires D2 |
| EIP-170 | Hard ceiling **24,576 bytes**; report actual headroom |

The 40,000-gas target margin is measured **inside the source's forwarded stipend**. PriceDesk's external wrapper/configuration/iteration overhead lies outside it and must be reported separately. A full PriceDesk transaction above 250,000 gas does not by itself mean a source stipend failure. Distinguish source execution, complete desk execution, transaction intrinsic gas and chain-specific data fees; do not add/subtract unexplained multicall overhead.

Reviewer A reported single-pool raw dependency totals 112,691–130,789 and dual-pool totals 214,948–232,776 gas. These are planning evidence, not acceptance measurements: full traces were not supplied, some required source calls are missing, and dual totals below 250,000 do not prove impossibility. V1 selects one pool for lower complexity and more likely headroom. It does not reserve dead secondary fields or authorize a later stipend increase.

Starting ceilings for the feasibility experiment:

| Dependency | Per-call ceiling |
|---|---:|
| `observe([window,0])` | 120,000 |
| Anchor `latestRoundData` | 30,000 |
| Pool slot0, liquidity, current observation; asset decimals; anchor decimals | 15,000 each |
| Required HQ address lookup, current desk tokenScale, or MissionControl global-age scalar | 15,000 each |
| Admission-only desk qualification callback | 400,000, allowing its wrapper plus 250,000 source call |
| Admission-only metadata/desk tokenScale scalar | 30,000 each |

These are **starting caps, not measurements or a proved aggregate bound**. Observe/round plus the five listed market/scalar ceilings alone sum to 225k; the required HQ/current-desk-scale reads and local logic are additional. Not all policy calls run on every path. Resolve the canonical desk once per read and reuse it for scale/authentication. Document actual call counts and cold/warm costs, then tune caps and the failure reserve within the unchanged hard stipend. A sum of ceilings neither proves a valid read exceeds 210k nor proves sufficient gas remains.

The design must retain a tested reserve for decoding and returning failure. After an expensive successful observe, a later bounded gas burner must still produce `(0, True)`. Include scale, HQ and policy failures at their actual call positions too. Cap tuning/ordering or an explicit remaining-gas reserve are implementation choices; before proceeding beyond the spike, record concrete values and traces that prove the complete successful and failure paths. No guard may be removed or silently skipped for gas. Passing a gas counter below 250k is insufficient unless the actual desk's 250k static call returns the specified successful/failure result.

**Work gate, before full governance:** prove math, assemble the entire read path with realistic cold storage and configured feed state, and call it through actual local PriceDesk with authentic local observation fixtures and a pinned Robinhood fork where historical state is available. Local stress evidence is mandatory; unavailable fork evidence remains an explicit route-qualification gap. Include caller authentication, both decimal reads, the direct anchor, normalization and all ABI guards. Use a minimal state-seeding test fixture for this experiment; no production configuration setter or bypass may ship.

Measure:

- PONS/CASHCAT single-pool reads at 30 minutes and four hours; all three windows for all four assets in the fork tests when RPC state is available.
- Genuine deep observation searches: fully populated capacity 65,535, partial growth, rotated/wrapped rings and targets chosen to force deep search. Report measured search depth/slots; high cardinality alone is insufficient.
- Cold/warm inherited and local-override paths, direct reads, canonical forwarding and desk rotation.
- Expensive successful pool work followed by each later dependency failure/gas burn; legitimate OLD separately from out-of-gas.
- Coverage, snapshot, malformed responses and failure status through the unchanged desk.

Use the **canonical V3 pool runtime**, not merely a library wrapper, for the main lookup-cost proof. Record its source/compiler/settings, runtime identity and storage layout; if it differs from the candidate runtime, account for that difference explicitly rather than calling it exact live-pool gas. Small fault-injection mocks still serve malformed-response tests. A library wrapper can prove numerical behavior but cannot silently substitute for pool dispatch/storage costs.

Derive storage slots/packing from the pinned compiler's layout, validate them against a small organically populated pool, then use installed `boa.env.evm.set_storage(address, slot, value)` to seed internally consistent larger rings, slot0/index/cardinality state and relevant liquidity. Do not generate 65,535 swaps for every test. Compare seeded and organic histories for matching outputs and relevant state before trusting the large fixture. Label seeded rings **synthetic**; they establish stress behavior, never that a candidate pool had that live history.

Keep a representative 65,535-slot deep lookup, 20,000-slot lookup, wrap and partial-growth cases in the explicitly selected, required `gas` suite, with the large seed prepared once/reused under isolated snapshots. Ordinary default tests exclude `gas`. An exhaustive ring/target campaign may use an additional opt-in fuzz suite, but do not silently remove the representative worst-case gate from required CI. Target less than five minutes for the new gas file on a documented local baseline and measure its contribution to the existing 30-minute CI job; optimize fixture setup before requesting a test-runtime change. Wall time is not inferred from cardinality alone.

For cold measurements after all setup/confirmation/seeding, call `boa.env.reset_gas_metering_behavior()`, clear transient storage with `boa.env.evm.vm.state.clear_transient_storage()`, then call `boa.env.reset_gas_used()` immediately before the measured transaction. The latter resets account/storage access counters in installed Titanoboa 0.2.7; an anchor alone does not prove coldness. When using Boa's message-level API, explicitly mark the transaction sender and top-level recipient warm via the installed state's `mark_address_warm` with canonical address bytes, as the EVM transaction executor does. Preserve standard precompile/access-list rules without warming unrelated dependencies. For a desk call, natural warming by the desk's own pre-source work remains part of the measurement; do not subtract it artificially.

No intervening contract inspection may warm the target. Use a control test proving a known SLOAD is cold, then warm, then cold again after reset. Measure intentional warm behavior with two source/desk calls within one test wrapper transaction; report each child call and wrapper overhead separately. Keep gas measurement enabled and validate caller/target warmness against actual EVM transaction rules. Record this pinned-Boa recipe in committed test documentation so a future toolchain change revalidates the assumptions.

Size checkpoints: (1) math in a minimal deployed test wrapper, diagnostic only; (2) full read-path skeleton with guards; (3) lifecycle added; (4) final source after all changes. Internal modules have no standalone deployable runtime budget; inlining/composition affects final size. Measure `len(boa.env.get_code(source.address))` after actual constructor execution, including immutables, and record compiler/settings/constructor bindings. Reviewer template byte counts are not deployed sizes. The repository's former blanket 200-byte headroom floor is retired; 22,500 is this plan's selected engineering target.

| Experiment result | Authorized next step |
|---|---|
| Complete source ≤210k, size ≤22,500, all guards and failure paths pass | Preferred; proceed to lifecycle and repeat gates after composition |
| Above target, but successful through unchanged 250k desk call and runtime ≤24,576 with all required tests passing | Under selected D2, proceed with local implementation/completion; report target breach, full traces and headroom. No per-overrun permission round trip; no claim of deployment approval |
| Cannot return valid price under 250k, or runtime >24,576 | Feasibility fails; stop dependent lifecycle work and report smallest needed scope change |
| Historical RPC/state unavailable | Finish independent local work; label affected route/fork evidence unverified. Authentic local stress gates still apply |

Do not optimize by deleting getters/events required by this ABI, weakening guard assertions, changing lookback, caching prices or lifting desk stipends. Reducing duplication and unnecessary operations is permitted. Under D2, exceeding a target is a disclosed review result, not permission to weaken the hard limit or a safety property. A public ABI/scope reduction still requires a new decision.

## 7. Required tests and evidence

Tests must falsify mistakes, with deterministic seeds and explicit developer-revert expectations. Avoid using a duplicate of the port as its only oracle.

| Area | Required cases |
|---|---|
| Tick/quote | Both token orders; zero, ±1, both domain endpoints and neighbors; signed-floor remainder cases; both quote precision branches; invalid ticks; decimals 0, 6, 9, 18; zero/extreme quotes; exact compiled upstream comparison; valid zero cumulative-tick delta through full source and actual PriceDesk |
| mulDiv | Exact/remainder divisions; 256-bit intermediate overflow with valid quotient; zero divisor; quotient overflow; independent Python integer expectations |
| History | Exact-window boundary; OLD; populated and partially grown/wrapped rings; deep searches at 65,535; uint32 timestamp, int56 and uint160 accumulator wraps; repeated timestamps; zero liquidity |
| Guard boundaries | Current/harmonic liquidity below/at/above independently; observation age below/at/above, including greater than lookback; initialized/unlocked flags; malformed slot0 relations |
| Market behavior | Abrupt moves/crash lag; observation write without independent trading; the exact pass/fail fully extrapolated and halt/restart cases in §4 |
| Anchor/policy | Fresh/exact-age/stale; zero/future timestamp; invalid answer/rounds; phase-encoded rounds; changed decimals; overflow; local override and inherited boundaries; forwarded global zero; forged caller/registry; HQ desk rotation; required HQ/MC failure |
| ABI | Every relevant boundary: revert, empty/short/surplus data, bad offsets/lengths, noncanonical sign extension/bools/widths, EOA, gas burner |
| Lifecycle | First action cannot confirm immediately; nonzero initial timelock; all add/update/disable/cancel paths; wrong kind; pending collision; exact no-op; before/at/after confirmation and expiry; replay; pause; unauthorized caller |
| Atomicity/decimals | First ADD at decimals 0 and 18 with observable staged callback state; snapshot active/pending/action/enumeration/decimal state and logs around failures; no surviving provisional binding; permanent binding across disable/re-add; exact permissionless scale-poisoning/restoration/rotation case; outage-time disable/cancel |
| Capacity | 50 active; 51st rejected; competing pending ADDs for last slot; first/middle/last remove and re-add; account for PriceSourceData's one-based enumeration |
| Desk composition | Failure matrix from §2; missing/wrong/correct tokenScale; both amount conversions and dust; candidate unregistered; another source cannot rescue callback; direct success but stipend failure rejects confirmation |
| Cost/size | All §6 cold/warm and failure paths; no externally warmed setup masquerading as cold; actual deployed runtime with immutables; no-op snapshot/coverage under their own stipends |

Local test doubles should separate malformed-response injection from authentic upstream observation behavior. Validate gas instrumentation itself: storage warmed in prior calls inside the same test transaction can conceal costs. Admission often warms metadata, so successful confirmation is not cold-read evidence. Reuse `MockChainlinkFeed.vy`'s `setDecimals` and `setMockData` for supported cases; add a fault mock only for behavior that existing fixtures cannot express.

Add a low-price zero-decimal regression with all other guards valid and the whole-token quote rounding to zero WETH. Its docstring must explain the less-than-one-wei rounding boundary. For an already active feed, require `(0, True)` and the actual desk's unavailable behavior with no usable fallback; admission with that unusable candidate must reject without binding. Keep the separate successful first-ADD zero-decimal test. A minimal numerical example is asset-as-token0, one raw asset unit and mean tick -1: the quote floors to zero, whereas mean tick 0 quotes one wei.

The explicit fuzz run must exercise meaningful properties with deterministic seeds and reported input counts: signed floor correction versus Python floor division over positive/negative deltas, and floor mulDiv versus Python arbitrary-precision products, including valid quotients after intermediate overflow and rejection of invalid/unrepresentable results. Include at least 1,000 deterministic cases for each, with mandatory signed remainder/overflow strata; one vacuous marked test does not satisfy the gate. Broader tick/quote comparisons retain the boundary and compiled-reference requirements above.

Add `"UniswapV3TwapPrices.vy"` to `PRODUCTION_PRICE_SOURCES` in `tests/registries/test_price_desk_gas.py`, preserving **all ten existing names** and assertions. This repository inventory is not permission to register another source in deployment configuration. The aggregate-source-count guard must remain unchanged; production graph growth requires later gas requalification.

Run and report ordinary inventory, `tests/inventory/test_repository_hygiene.py`, the aggregate-count guard and `tests/test_lean_shard_coverage.py`, plus explicit gas/fuzz selections. Hygiene covers all tracked evidence, including JSON; no personal filesystem paths or machine hostnames, and do not delete evidence to hide violations. `tests/inventory/` also contains artifact/release-marked tests excluded by default: report selection and explicitly run an excluded check if affected. Do not claim the whole inventory ran merely because its directory was passed. Do not touch the V2 test tree `tests/priceSources/uniswap/`.

The existing lean price-source shard already covers this new subtree; no shard edit is needed. Add `tests/priceSources/uniswap_v3/test_twap_gas.py` to the explicit snapshot-gas path list in `.github/workflows/python-tests.yml`, preserving its gas marker, 30-minute timeout, credentials restrictions and loadfile conventions. Extend only the corresponding required-suite assertion in `tests/test_lean_shard_coverage.py` so omission of the new gas suite fails a workflow guard. Keep all other workflow-shape assertions. Tests must not depend on cross-file fixture state.

The aggregate source-count guard depends on unchanged `ROBINHOOD_REGISTRY_TOPOLOGY`, not discovery of another source file. Do not change topology to satisfy it. Measure this source's deployed size in its named source-specific gate; adding it to an unrelated historical `EXPECTED_RUNTIME_BYTES` table is not a requirement of this task.

## 8. Candidate bindings, frozen vectors and route characterization

These are September 7 research inputs, not production config. Use addresses for identity and independently revalidate the selected block. The contract must not hardcode this list.

| Target | Asset | One V3/WETH pricing-pool candidate |
|---|---|---|
| PONS | `0x39dBED3a2bd333467115dE45665cC57F813C4571` | `0x10CC6BD38112cAc182db90B6a71d8Bb5939526bA` |
| CASHCAT | `0x020bfC650A365f8BB26819deAAbF3E21291018b4` | `0xA70fc67C9F69da90B63a0e4C05D229954574E313` |
| Artificial Inu / AI | `0x2E8c31162b855A2ffa90F6F8634643Ad6F111e18` | `0xc4a21f9d6485FC5893DD4A491B320a83DAF4Da1D` |
| INDEX; reported symbol Index | `0x56910D4409F3a0C78C64DD8D0545FF0705389870` | `0xD29893fFac8b29eC4Db2cfE0CDB3FE1377c028Ff` |

Factory `0x1f7d7550B1b028f7571E69A784071F0205FD2EfA`; WETH `0x0Bd7D308f8E1639FAb988df18A8011f41EAcAD73`; ETH/USD `0x78F3556b67E17Df817D51Ef5a990cDaF09E8d3A9`. All four assets were reported at 18 decimals, fee 10000, tick spacing 200. CASHCAT is token0; WETH is token0 for the other three. AI's reported name is Artificial Inu; PONS is Pons; CASHCAT is Cash Cat; INDEX is The Index.

Historical comparison-pool references; additional comparison analysis is not required for this contract/test assignment:

| Asset | 0.3% V3/WETH comparison pool | Reviewer B's observation at block 57,036,425 |
|---|---|---|
| PONS | `0xEd50bDeeA8aDC232f159486192a4157281D722ff` | Cardinality 1,400; 30m/60m served; 4h OLD |
| CASHCAT | `0xd42A491087a15E5afd51FEb3606066Cc152d2b09` | Cardinality 14,400; 30m/60m/4h served |
| AI | `0xD78480CAFEf722D75519e13B9f516e5704D0D659` | Cardinality 500; 30m/60m served; 4h OLD |
| INDEX | None selected | Do not invent a comparison pool |

These are historical reviewer observations; B did not supply the block hash. Fresh results can differ. A comparison OLD at that pin is not an implementation failure and does not authorize shortening the window or substituting another pool. No 0.05% pools are in scope. All four 1% pools reportedly served 30m, 60m and 4h in both reviews. Main-pool cardinalities were 20,000 for PONS/CASHCAT/AI and 1,801 for INDEX.

### Frozen numerical fixtures

Companion artifact: `docs/priceSources/uniswap-v3-twap-reference-vectors.json`. It contains all twelve raw cumulative pairs, modular deltas, mean ticks, harmonic liquidity, sqrt ratios, WETH quotes and USD18 results. Large integers are decimal strings to prevent JavaScript precision loss.

Pinned chain 4663, block **57,037,442**, hash `0x2488e1b687eaa880ee85ddbe92b903039500f7e03ef6ead1bdb1374a4659fc27`, timestamp **1788804620**. Reported ETH/USD: 8 decimals, round **18446744073709553653**, answer **249098276109**, updatedAt **1788801662**, USD18 **2490982761090000000000**.

| Asset | Window seconds | Mean tick | Harmonic liquidity | Raw WETH / whole asset | USD18 |
|---|---:|---:|---:|---:|---:|
| CASHCAT | 1800 | -94298 | 206975634290094062884840 | 80333122194428 | 200108422530856619 |
| CASHCAT | 3600 | -94304 | 205253329089144967230813 | 80284939186569 | 199988399488902386 |
| CASHCAT | 14400 | -94257 | 203140459086215891896988 | 80663147584192 | 200930510087480751 |
| PONS | 1800 | 81443 | 190506869180815814431768 | 290504116276662 | 723640745670849919 |
| PONS | 3600 | 81442 | 189906289444801875138098 | 290533166688290 | 723713109745417835 |
| PONS | 14400 | 81218 | 213799737786542519910638 | 297114213136054 | 740106382996730540 |
| AI | 1800 | 93296 | 251654032820954579348919 | 88799143694168 | 221197136141726267 |
| AI | 3600 | 93399 | 249426631986423090184027 | 87889251993985 | 218930611602111543 |
| AI | 14400 | 94048 | 235278192998887715009316 | 82366661913355 | 205173934914695580 |
| INDEX | 1800 | 110488 | 182511466635101678193593 | 15915014329930 | 39644026338355947 |
| INDEX | 3600 | 110584 | 178065673190930086761249 | 15762968780799 | 39265283496570163 |
| INDEX | 14400 | 110641 | 166394531022695686027661 | 15673379908952 | 39042119161213785 |

During revision 2, all twelve rows were recomputed exactly with Python integers using constants extracted from the pinned upstream TickMath. The block header was independently matched. Historical contract `eth_call` by both block number and hash returned `-32000: metadata is not found, 57037445`; the contract data therefore remains reviewer-supplied. No compiled upstream differential harness has yet been run. The JSON records those limits, rather than describing these rows as independently chain-qualified.

The full historical slot0/return bytes, startedAt and answeredInRound were not supplied. Missing fields stay unknown in the frozen JSON. Add an **offline end-to-end regression** for all twelve rows through the new source and actual local PriceDesk, using the recorded cumulative pairs/anchor answer plus a separately labeled synthetic metadata fixture: initialized/unlocked state, canonical mock bindings/order, valid missing round fields and a compatible scale. Do not overwrite nulls in the historical JSON or imply these synthetic supplements were observed on-chain. This proves source behavior on those inputs, not historical route validity or real lookup gas.

The reported anchor is **2,958 seconds old** at the pinned timestamp. A 1,800-second quote-age policy must reject it; 2,958 passes the age predicate alone. The numerical USD output is not a promise that the complete source returns it under every tested policy. Latest pool observations were reported 9–24 seconds old. The AI seconds-per-liquidity accumulator is large but valid uint160; preserve it without lossy conversions.

### Laboratory settings and fork tests

For comparable primary-pool numerical runs use this explicit **laboratory** tuple, not production recommendations:

```text
windowSeconds ∈ {1800, 3600, 14400}
minCurrentLiquidity = 1
minHarmonicLiquidity = 1
maxObservationAgeSeconds = 3600
quoteStaleTime = 0
local test graph's inherited global quote age = 86400 seconds
```

These raw liquidity minima only avoid inventing economic floors in the numerical experiment. Test threshold behavior separately around nontrivial synthetic values. Do not use the 86,400 observation-age ceiling as the default lab tuple. For the frozen round, a separate inherited quote-age case at 1,800 must be unavailable; also cover a configured local 1,800 override after a valid admission followed by synthetic quote aging. In a fork graph, record the exact local test settings and do not claim they are deployed MissionControl settings.

Use an opt-in `fork_qualification` entry point in a dedicated subprocess so it cannot invalidate session-wide local protocol fixtures. Compile/prepare local artifacts before selecting fresh state, fork first, then deploy the entire temporary HQ/desk/source/mock graph **inside that environment**. Do not carry local contract objects across an environment replacement. Use `advance_timelock_blocks` for fixture governance and preserve the pin's timestamp through every setup step; record any separate clock emulation. No keys, live-state writes or real-chain mutations.

Build the graph in a plain helper under the new test subtree, called by a standalone `fork_worker.py`; reuse the constructor/registration patterns in `tests/conf_core.py` and the plain isolated-desk helper in `tests/registries/test_price_desk_isolation.py`. Do not directly invoke decorated pytest fixtures, unwrap them through pytest internals, or import the full session bootstrap into the worker. Create every local dependency after `boa.fork`, preserve canonical HQ registry identities and deploy the **unchanged actual PriceDesk**, not a mock or a stipend-modified variant. Do not deploy unrelated vaults/engines/all legacy sources solely to obtain the minimal graph. The outer pytest launcher should not request the full session graph; where its autouse fixture would run, use the existing module-local no-op `ripe_hq` fixture pattern from the aggregate-count/workflow tests. Shared fixtures and core deployment helpers remain unchanged. Assert current desk/policy wiring and the unchanged timestamp before qualification reads.

Require explicit `RIPE_TWAP_PIN_MODE`:

| Mode | Inputs and behavior |
|---|---|
| `fresh` | Explicitly choose `eth_blockNumber - 32` after asserting chain 4663 and sufficient head height. Read and record its child number, hash and timestamp once before calls; every subsequent RPC/fork read uses that fixed pin. The 32-block offset is not a finality claim. Reject simultaneously supplied explicit block/hash arguments |
| `pinned` | Require both `RIPE_TWAP_BLOCK` and `RIPE_TWAP_BLOCK_HASH`, verify the returned header and chain, and use only that pin. Prefer an explicitly supplied `RIPE_TWAP_ARCHIVE_RPC_URL` when present; otherwise use `RIPE_TWAP_RPC_URL`. Missing historical state remains unverified; no automatic fresh fallback |
| Missing/invalid mode or partially supplied pin | Configuration error before qualification; never guess a mode or mix datasets |

Fresh mode uses `RIPE_TWAP_RPC_URL`; do not silently substitute archive/provider inputs. In both modes, call `boa.fork(rpc, block_identifier=childBlock, cache_dir=...)` only in the isolated environment, and use **the pinned timestamp** for age calculations. Read the same block header again at the end where available and report a mismatch/unverified consistency check rather than accepting mixed state. Existing global `--fork` accepts local/mainnet/base; do not invent `--fork robinhood`, repoint a fixture or change defaults.

The public RPC has failed historical calls at the frozen pin; that does not establish a universal retention interval or archive guarantees for any provider. Use finite request timeouts and bounded backoff for transient/429 responses; HTTP 403 or missing-state responses are infrastructure evidence, not contract reverts. Capture raw inputs promptly and record partial results if state becomes unavailable mid-run. A new explicit fresh run creates a different dataset; it never replaces a requested pin inside an existing run.

For the four primary pools, implement the 1,800/3,600/14,400-second fork cases and attempt them when RPC state is available. Print compact results: asset, window, fixed block/hash/timestamp, exact laboratory settings, actual/reference price, passed/failed/unverified and reason. A failed or unavailable route is not an implementation failure when the source follows the specified failure behavior. Do not manufacture four passing routes.

Keep sanitized raw inputs needed to reproduce a test in the source-specific test fixtures, clearly distinguishing live observations from synthetic supplements. Preserve missing fields and the frozen JSON. No separate evidence bundle or qualification report is required. Ordinary CI remains offline.

Extended observation/anchor cadence analysis, monitoring thresholds, token-control investigation and economic qualification are deferred to asset admission. The existing comparison pool table is retained as reference, not extra implementation scope. V1 still has no sequencer-uptime/grace-period guard; a new observation after a halt does not establish a trustworthy full interval. The stale-tick, liquidation-availability and fallback limitations already stated remain unchanged. Passing these contract tests does not approve borrowing settings.

## 9. Build, test and finish

1. Use the pinned isolated worktree and the four-file packet; D1–D3 are already selected. Copy the spec and two JSON inputs into the worktree. Missing inputs must be obtained, not regenerated. Do not perform another planning round or write a pre-port design memo.
2. Build both pinned Solidity reference projects, implement the internal math and run actual compiled differentials plus independent integer tests.
3. Prove the complete guarded read path through unchanged actual PriceDesk, with the authentic cold/warm and failure-gas fixtures, before completing governance. Keep all guards and apply D2 to disclosed target overruns.
4. Complete lifecycle and integration tests, including scale poisoning/recovery/desk rotation, callback atomicity, zero-decimal cases, malformed ABI, fuzz and deployed size. Implement and attempt the fork cases; record infrastructure gaps without blocking independent local completion.
5. Make only the small inventory/export/test-selection edits below, run affected regressions, inspect the diff and commit the complete scoped result locally without signing or pushing.

Expected implementation surface (private helpers/test splits may change; required behavior and coverage may not):

```text
contracts/priceSources/UniswapV3TwapPrices.vy
contracts/priceSources/modules/UniswapV3TwapMath.vy
contracts/mock/<source-specific fault mocks where existing mocks are insufficient>
tests/priceSources/uniswap_v3/test_twap_math.py
tests/priceSources/uniswap_v3/test_twap_lifecycle.py
tests/priceSources/uniswap_v3/test_twap_price_path.py
tests/priceSources/uniswap_v3/test_twap_pricedesk.py
tests/priceSources/uniswap_v3/test_twap_gas.py
tests/priceSources/uniswap_v3/test_twap_fork_qual.py
tests/priceSources/uniswap_v3/fork_worker.py
tests/priceSources/uniswap_v3/reference/v3/<pinned Solidity harness and notices>
tests/priceSources/uniswap_v3/reference/v4/<pinned Solidity harness and notices>
tests/priceSources/uniswap_v3/<necessary helpers, fixtures and one short README>
docs/priceSources/uniswap-v3-twap-spec.md                  # copy of the input spec
docs/priceSources/uniswap-v3-twap-reference-vectors.json   # frozen input
docs/priceSources/uniswap-v3-twap-upstream-lock.json      # input provenance, extended for required reference dependencies
```

Only these ancillary edits are allowed:

- `tests/registries/test_price_desk_gas.py`: add the new source to the inventory, retaining all ten existing names.
- `scripts/export_abis.py`: add `priceSources/modules/UniswapV3TwapMath.vy` to `NON_STANDALONE_VYPER_SOURCES`; generate only the new source's ABI and required export/completion deltas. Do not refresh unrelated ABI artifacts.
- `.github/workflows/python-tests.yml`: add the new gas test to the existing snapshot-gas path list. `tests/test_lean_shard_coverage.py`: add its corresponding required-suite assertion. No new jobs, shard changes, CI redesign or deployment workflow work.

The test README should contain only the commands needed to rerun local, differential, gas and fork tests, reference/fixture provenance and essential FinishSetup/clock caveats. Keep measured gas and case details in reproducible tests/fixtures and concise test output, not parallel reports. License notices remain required. Do not commit the root handoff prompt, review logs or unrelated research.

Finish when all required local contract/math/behavioral/integration/gas/deployed-size checks pass and the scoped result is committed. A missing compiled differential or a hard-limit failure is incomplete. Disclosed engineering-target overruns are allowed under selected D2. Missing RPC state leaves the corresponding fork cases unverified and does not waive any local test.

Final response: branch/worktree/commit; test outcomes and meaningful fuzz input counts; source/desk gas and deployed bytes/headroom; target overruns; fork-case status; unresolved concrete issues. Keep it concise. No separate design, monitoring, readiness or qualification report is required. Implementation completion is distinct from production route qualification and borrowing readiness; deployment, registration, LTVs/caps/liquidation settings and activation remain outside this task.
