# Uniswap V3 TWAP price source — operator handoff

Written 2026-09-10 for whoever runs `UniswapV3TwapPrices.vy` in production. It covers what the
source does, every way it can bite you, what has to be true before the first feed goes live, the
exact procedures for adding, changing and removing feeds, what to monitor, and what to do when a
feed goes dark. Facts come from the reviewed PR #229 head `14ef0b0f` (contract byte-identical to
`c17fb8f3`), its runbook, spec and test README, and three independent review rounds.

Where this document says **recommendation**, that is reviewer advice, not a documented protocol
rule. Everything else is contract behaviour or an owner decision recorded in the PR.

---

## 1. Status: what is done and what is not

| Item | State |
| --- | --- |
| Contract, tests, tooling, docs | Complete on PR #229 head `14ef0b0f`; CI 17/17 green; three-reviewer pass required on that head before merge |
| Merge | **Must be a merge commit.** A squash or rebase merge breaks the required `twap-tooling` CI job on master (it reads commit `11d3bd30` from history) |
| Commit signing | `14ef0b0f` is unsigned (sandbox limitation); all earlier commits are signed. Amend-sign only if you also re-run CI and the fork attachment |
| Deployment | Not done. No instance exists on any chain |
| PriceDesk registration | Not done |
| FinishSetup / action timelock | Not done (owner decision D12: migration item) |
| PriceDesk first-sync hardening | Separate follow-up PR (owner decision D11) |
| Governance 2% depth threshold | **Unset.** Must be recorded before any feed proposal |
| Token upgradeability / decimals review per candidate | Not done (owner decision D18) |
| Cold gas qualification against the real Robinhood registry | Not done; the CI tests use an RH-shaped laboratory |
| Any feed, LTV, cap or borrow enablement | Not done |

The contract is finished. The operational program around it has not started.

---

## 2. How it works, on one page

**Price.** For an active feed the source returns USD18 per whole asset token:

```
geometric time-weighted average of asset/quote over the window  ×  PriceDesk.getPrice(quote)
```

The quote asset is whichever token in the pool is not the asset. The quote's USD price comes from
the canonical PriceDesk (resolved through RipeHq entry 7 every read), so the quote must already be
priced by another source, normally Chainlink. This is not an arithmetic USD TWAP.

**Per-feed configuration, locked at proposal.** Each feed stores: pool, fee, quote asset, token
order, both tokens' decimals, `twapWindow`, `maxObservationAge`, `baseLiquidity` (harmonic mean
liquidity over the window at proposal time) and `minLiquidity = ceil(baseLiquidity × ratio)`.
Defaults are `feedDefaults = (3600 s window, 1800 s age, 5000 bps = 50 %)`. A zero window or age
argument at proposal takes the default in force at that moment. Changing `feedDefaults` later never
touches an existing feed or an in-flight proposal.

**Admission (proposal time).** The proposal reverts with `invalid feed` unless all of these hold:
asset and pool are contracts, asset is token0 or token1, both decimals ≤ 18, `factory.getPool(asset,
quote, fee) == pool` on the canonical factory, window in [1800, 14400] s, `0 < age <= window`,
`slot0.observationCardinality >= window + 1`, harmonic liquidity over the window is nonzero, the
quote is priced by the desk, the source can produce a nonzero price right now, and no same-instance
loop exists (the quote has no feed or pending action here; the asset is not the quote of an active
or pending feed here). A proposal also reverts with the pool's own `OLD` if the pool lacks history
for the window.

**Confirmation.** After the timelock, `confirm*` runs in this fixed order: governance and pause
checks → identity re-check (token decimals, pool tokens, fee, factory mapping; **drift cancels the
proposal, emits a cancel event and returns False without reverting**) → structural checks and the
desk scale guard (`PriceDesk.tokenScale(asset)` must be 0 or `10**decimals`; failure reverts) →
timelock → stage the config → the desk calls back into the source under a measured gas ceiling →
clear pending, emit `NewUniV3FeedAdded` / `UniV3FeedUpdated`. Any transient failure (no history,
liquidity below floor, locked pool, zero quote, callback failure, scale mismatch) **reverts and keeps
the proposal pending**; just retry later.

**Read-time gates.** Every read returns 0 (unavailable) if any of these fail: pool is mid-swap
(`slot0.unlocked == false`); current liquidity is 0 or below `minLiquidity`; the latest observation is
uninitialised or older than `maxObservationAge`; `observe([window, 0])` reverts `OLD`; the mean tick is
out of domain; harmonic liquidity over the window is below `minLiquidity`; the desk returns 0 for the
quote; the cached desk scale does not match the snapshot decimals; or a caller supplied a
non-canonical desk address. `_staleTime` is ignored.

**What unavailable means downstream.** The source reports `(0, hasFeed=True)`. PriceDesk marks the
asset as "has price config, no price": non-strict reads return 0, strict reads revert. With no
fallback source for the asset, nothing that needs its value (borrow, health check, valuation) can
proceed. This is fail-closed by design, and it is the single most important operational fact.

---

## 3. Footguns and gotchas

Ordered roughly by how likely they are to hurt you.

### 3.1 A quiet pool goes dark after 30 minutes
`maxObservationAge` defaults to 1800 s. Uniswap V3 writes an observation only on a swap that
crosses a tick or an in-range mint or burn. Thirty quiet minutes and the feed returns 0; strict desk
reads revert. Thin memecoin pools are quiet at night.
Mitigations: set an explicit longer age at proposal (max = window; that allows the whole window to
be extrapolated from the last observation), or, **recommendation**, run a keeper that does a dust
in-range mint/burn on each production pool at an interval well inside the age. Decide per asset
before proposing; a later change is a timelocked update (§6.2).

### 3.2 Cardinality is pool-side work you must do first
Admission needs the pool's actual `observationCardinality >= window + 1` (3601 for one hour, 14401
for four). Pools start at 1. Someone must call `pool.increaseObservationCardinalityNext(N)`
(anyone can; ~22k gas per slot, so batch it), and the actual cardinality then grows one slot per
written observation. Raising the target on a quiet pool and proposing the same day will fail.
Robinhood candidates today: CASHCAT, PONS, AI at 20,000; INDEX at 1,801 (30-minute window only).

### 3.3 The liquidity floor is a snapshot, and every update re-baselines it
`minLiquidity` is 50 % of the harmonic liquidity over the window at the instant of proposal. Propose
during a trough and that weak floor is permanent until the next update. A same-pool, age-only update
also re-baselines. Time proposals and updates for normal liquidity and check
`getPoolLiquidity(pool)` first.

### 3.4 One second of zero liquidity blanks the feed for the rest of the window
The harmonic mean is dominated by its smallest term. An LP removing everything and re-adding a second
later pins the harmonic liquidity near zero for up to a full window, so the feed reads 0 until the
hole leaves the window. Owner-accepted residual. Expect this from concentrated-liquidity rebalancers.

### 3.5 Confirm can succeed-by-returning-False inside a Safe batch
If identity drifted since the proposal, confirmation cancels, emits `NewUniV3FeedCancelled` /
`UniV3FeedUpdateCancelled` and returns False. Safe MultiSend does not treat a returned False as
failure, so a batch `[syncTokenScale, confirm]` can leave the sync in place and the feed dark.
After **every** confirmation, verify the `NewUniV3FeedAdded` or `UniV3FeedUpdated` event for the
exact asset, pool, quote, window, age and floor.

### 3.6 Identity is checked before the timelock
Calling `confirm*` before unlock while identity has drifted consumes the proposal. Check current
token decimals, pool tokens and factory mapping before submitting a confirm, especially for tokens
with upgradeable metadata.

### 3.7 Confirmation is not route qualification, and batching can hide that
Confirmation measures the desk callback warm, with a 170,000-gas ceiling. A batch that first reads
the quote price (or touches the quote source in any way) warms storage and lets a route pass that
later fails cold at ~247k, above the 250k stipend. Rule: **confirm alone, or with only a preceding
`PriceDesk.syncTokenScale(asset)` for that same asset.** Put preflights in a separate prior
transaction. A revert `route too expensive` means the quote route is too heavy (wrong ordering or a
storage-heavy quote source); fix the route, do not retry blindly.

### 3.8 Gas limit on confirm
The desk's inner call gets a 250,000 stipend under EIP-150. A tight outer limit starves it and the
confirm reverts `price source not executable` even for a valid route. Estimate the full transaction
and add a generous buffer (**recommendation**: at least 500k).

### 3.9 Registry order is a hard rule with no on-chain enforcement
Quote assets must be priced by sources that never call back into the desk (Chainlink, Pyth, Stork).
This source must be registered **after** every such source, and the MissionControl priority list
must keep them ahead of it. On Robinhood today: Chainlink id 1, Curve id 2, V2 monitor id 3,
priority `[1, 2]`, so V3 becomes id 4. With V3 first and a fat registry, the nested quote lookup
exceeds the stipend and every V3 feed reads 0. A later priority reorder can revive that. Re-check
after any registry or priority change. Cross-instance and wrapper cycles (two V3 instances quoting
each other, or a wrapper source that prices via the desk) are an accepted limitation: nothing stops
them on-chain, and both prices go to 0 if the independent fallback is removed.

### 3.10 Decimals-changing or upgradeable tokens
The feed snapshots the asset's decimals. If the token later reports different decimals, or someone
syncs the desk scale while it does, the scale guard fails and the feed goes dark until governance
runs the recovery sequence (§6.4). The desk's permissionless first sync is a known sibling-wide
weakness (owner D11 follow-up). Review token upgradeability before proposing (owner D18).

### 3.11 Token scale is a separate, mandatory step
A feed can be confirmed while `PriceDesk.tokenScale(asset)` is 0. Price reads work; `getUsdValue`
and `getAssetAmount` return 0 non-strictly and revert `missing token scale` strictly. Sync the scale in
the confirmation batch or immediately after. `SwitchboardGolf.executePendingAction` auto-syncs a zero
scale during non-NFT asset addition; it does not repair a wrong nonzero scale.

### 3.12 No instant per-feed kill switch on the source
`pause` blocks governance actions (add/update/disable/cancel/setFeedDefaults). It does **not** stop
reads. `disablePriceFeed` is timelocked. Fast levers live elsewhere: MissionControl asset config
(deposit cap, LTV, disable) through the switchboards, or a PriceDesk registry disable of the whole
source. Know their timelocks before you need them.

### 3.13 Fifty feeds per instance
Beyond 50 active feeds, every new proposal reverts (loop bound). Deploy a second instance if needed
and never let instances quote each other.

### 3.14 Pending actions block, expire, and must be cancelled
One pending action per asset. An expired action still blocks (`pending feed action`) until
`cancel*` is called. Expiration equals the constructor's maximum timelock, in blocks.

### 3.15 TWAP depth is not manipulation cost
The depth helper reports fee-inclusive spot depth at a pinned block, labelled "not a TWAP
manipulation cost". Moving a one-hour TWAP by X % costs roughly the capital to hold spot moved by
X % against arbitrage for a proportional part of the window. On a thin pool that can be cheap.
Treat V3-priced assets as their own risk tier: low LTV, tight deposit caps (**recommendation**).

### 3.16 Miscellaneous rules that surprise people
- Exactly one pool per asset; no aggregation across fee tiers. Pick the deepest canonical pool.
- The asset must be an ERC-20 contract; the native-ETH sentinel is rejected.
- Both tokens must have ≤ 18 decimals. Zero-decimal assets are allowed but a legitimately tiny quote
  can round to 0 and read as unavailable.
- Preflight views (`isValidNewFeed`, `getPoolLiquidity`) revert when the pool lacks history; that
  is "no history", not a bug.
- Desk rotation is automatic: the source always follows RipeHq entry 7. A stale desk address passed
  by a caller gets 0.
- Block-based timelocks on Robinhood run on the chain's modelled block clock (about five per
  minute), not wall-clock seconds. Size delays in that domain.

---

## 4. Before the first production feed: gate checklist

- [ ] PR #229 merged with a **merge commit**; three reviewers signed off on the merged head.
- [ ] Instance deployed with `(RipeHq, tempGov, minTimeLock, maxTimeLock, factory)`; factory is the
      canonical Robinhood V3 factory `0x1f7d7550B1b028f7571E69A784071F0205FD2EfA`; constructor
      timelocks chosen in the block-clock domain.
- [ ] `setActionTimeLockAfterSetup(delay)` called once (it can only be set once; zero-delay until
      then). Add the instance to the FinishSetup sweep so this cannot be forgotten on redeploys.
- [ ] Registered in PriceDesk **after** Chainlink, Curve and V2; MissionControl priority list left at
      `[1, 2]`. Check the desk registry timelock (it was 0 in the August audit).
- [ ] Cold T11/T22 gas qualification re-run against the real registry shape and every quote
      fallback, not only the laboratory (runbook requirement).
- [ ] Governance minimum smaller-direction 2 % depth (USD) recorded in the runbook.
- [ ] PriceDesk first-sync hardening PR (D11) scheduled or shipped.
- [ ] Monitoring from §7 in place before the first feed, not after.
- [ ] Emergency levers from §8 identified with their current timelocks.

---

## 5. Deployment and setup procedure

1. Deploy `UniswapV3TwapPrices` with the constructor above. Verify `FACTORY()` and `getRipeHq()`.
2. Call `setActionTimeLockAfterSetup(delay)` from governance. Verify `actionTimeLock()`.
3. Leave `feedDefaults` at `(3600, 1800, 5000)` unless you have a reason. `setFeedDefaults` is
   governance-only, pause-gated, untimelocked, and only affects future proposals. Bounds: window
   1800–14400, `0 < age <= window`, `0 < ratio <= 10000`.
4. Register the source in PriceDesk as the last source. Confirm `PriceDesk.getRegId(source)` is
   greater than every quote source's id and that the source is not in the priority list.
5. Record the deployed address, the registry id, the timelock, and the defaults in the deployment
   manifest. Resolve live addresses through RipeHq (`getAddr(7)` for PriceDesk, `getAddr(5)` for
   MissionControl); manifests have been stale before.

---

## 6. Per-asset procedures

### 6.1 Add a feed

**Pre-checks (off-chain, record the results):**
1. Token review: proxy/upgradeability, whether `decimals()` can change, fee-on-transfer or rebasing
   behaviour, blacklist controls. Reject or cap accordingly (owner D18).
2. Pool: `factory.getPool(asset, WETH_or_quote, fee)` must equal the pool you intend to use. The
   quote token must be priced by Chainlink (or another non-recursive source) in the desk right now:
   `PriceDesk.getPrice(quote) != 0`.
3. Cardinality: `pool.slot0().observationCardinality >= window + 1`. If not, call
   `increaseObservationCardinalityNext` in batches and wait for enough writes.
4. History: `source.getPoolLiquidity(pool, window)` returns without reverting and the harmonic value
   is sane; `isValidNewFeed(asset, pool[, window, age])` returns true.
5. Depth: run the helper at a pinned block and compare with the recorded governance threshold:

   ```sh
   python scripts/twap_pool_depth.py https://rpc.mainnet.chain.robinhood.com POOL ASSET --source SOURCE
   ```
   It prints block, token order, fee, current and harmonic liquidity, cardinality vs window+1,
   latest observation age, the floor a proposal would lock, and fee-inclusive 1 %/2 % depth per
   direction valued through the live desk. Do not propose if the smaller-direction 2 % depth is below
   the threshold, or while the threshold is unset.
6. Decide window and age explicitly for this pool (see §3.1). Decide LTV and deposit cap.
7. Loop check: the quote must have no feed or pending action in this instance; the asset must not be
   the quote of any active or pending feed here (`pendingQuoteCount(asset) == 0`).

**Propose:** `addNewPriceFeed(asset, pool)` or `addNewPriceFeed(asset, pool, window, age)` from
governance, at a normal-liquidity moment. Read back `pendingUpdates(asset)` and the
`NewUniV3FeedPending` event: resolved window, age, `baseLiquidity`, `minLiquidity`, confirmation block.

**Confirm (after the timelock, before expiry):**
- Re-check identity has not drifted (decimals, pool tokens, factory mapping).
- Transaction contents: `[PriceDesk.syncTokenScale(asset), confirmNewPriceFeed(asset)]` and nothing
  else, or confirm alone followed immediately by a sync. Generous gas limit.
- Verify: `NewUniV3FeedAdded` event with the expected fields; `pendingUpdates(asset).actionId == 0`;
  `hasPriceFeed(asset)`; `PriceDesk.tokenScale(asset) == 10**decimals`; a cold
  `PriceDesk.getPrice(asset, True)` returns a sane value; `getFeedLiquidity(asset)` shows current and
  harmonic liquidity above the floor.
- If confirm reverted `price source not executable`, `invalid feed` or `route too expensive`, the
  proposal is still pending: diagnose (pool state, scale, route) and retry. If it returned False,
  identity drifted: re-run the pre-checks and re-propose.

**Enable:** add the asset in MissionControl through the switchboard with the agreed LTV and deposit
cap. Golf's asset addition auto-syncs a zero scale; it will not fix a wrong nonzero one.

### 6.2 Change window, age or pool
`updatePriceFeed(asset, pool[, window, age])` → timelock → `confirmPriceFeedUpdate(asset)` with the
same batching rules. The active feed keeps its old settings until confirmation. Every update
re-baselines the floor (§3.3). A longer window re-checks cardinality. During the pending update the
old quote stays protected and no other proposal for the asset is possible.

### 6.3 Remove a feed
`disablePriceFeed(asset)` → timelock → `confirmDisablePriceFeed(asset)`. Disable has no identity or
dependency checks by design, so it works when the token, pool, quote or desk is broken. Remove the
asset from MissionControl config first or at the same time, or strict valuations will revert.

### 6.4 Scale recovery sequences (token decimals or desk scale changed)
- Mismatch after a valid proposal: wait for the timelock, then batch
  `[PriceDesk.syncTokenScale(asset), confirm*]`. A transient failure reverts both; an identity-drift
  cancel returns False and leaves the sync in place, which can darken an existing feed until you
  re-propose. Check the confirmed event.
- Mismatch already present on an active feed: `updatePriceFeed(asset, pool)` → wait → batch
  `[syncTokenScale, confirmPriceFeedUpdate]`. The active feed keeps pricing until the sync because its
  snapshot still matches the old cached scale; it is dark only if the confirm in that batch fails.
- Disable and re-add does not bypass the confirmation scale check.

### 6.5 Cancel
`cancelNewPendingPriceFeed`, `cancelPriceFeedUpdate`, `cancelDisablePriceFeed` from governance,
also for expired actions. Each emits exactly one cancel event.

---

## 7. What to monitor

Poll per feed (every few minutes, **recommendation**) and alert on:

| Signal | Source of truth | Alert when |
| --- | --- | --- |
| Availability | `PriceDesk.getPrice(asset)` non-strict | returns 0 while `hasPriceFeed(asset)` is true |
| Observation age | `pool.observations(slot0.observationIndex).blockTimestamp` | age approaching the feed's `maxObservationAge` (e.g. 70 %) |
| Liquidity vs floor | `getFeedLiquidity(asset)` → (current, harmonic, floor) | current or harmonic within 20 % of floor, or a zero-liquidity second observed |
| Cardinality | `pool.slot0()` | never shrinks; alert if a new window proposal would fail |
| Desk scale | `PriceDesk.tokenScale(asset)` vs `feedConfig(asset).assetDecimals` | mismatch |
| Token metadata | `asset.decimals()` | differs from snapshot |
| Registry / priority | `PriceDesk` registry, `MissionControl.getPriceConfig()` | any change: re-run the ordering check and cold qualification |
| Pending actions | `pendingUpdates(asset)`, `hasPendingPriceFeedUpdate` | an action nearing expiry, or one nobody expects |
| Events | `NewUniV3Feed*`, `UniV3Feed*`, `DisableUniV3Feed*`, `FeedDefaultsSet` | any event outside a planned change |
| Price sanity | source price vs an off-chain reference | divergence beyond your tolerance for the window length |

Keep the cold gas numbers from the CI `snapshot-gas` log (source read ~140–165k forwarded; direct
calls ~185k; stipend 250k) as the baseline; a production route that reads materially above them is
a registry-ordering problem.

---

## 8. Incident playbook

**Feed reads 0.** Check, in order: pool locked; current liquidity vs floor; latest observation age vs
feed age; `observe([window,0])` reverting `OLD`; harmonic liquidity vs floor; quote price in the desk;
desk scale vs snapshot decimals; registry ordering. Most cases are the quiet-pool or
liquidity-hole residuals and clear on their own; a scale mismatch needs §6.4; a route failure needs
a registry fix.

**Suspected manipulation.** The source cannot pause reads. Use MissionControl asset config (cap, LTV
0, disable) immediately, then `disablePriceFeed` through the timelock. Preserve the block range for
analysis.

**Token changed decimals or was upgraded.** Expect the feed to go dark (scale guard). Do not sync the
scale blindly; run the §6.4 sequence deliberately and verify the confirmed event.

**Registry or priority change by anyone.** Re-run the ordering check and the cold qualification
before assuming V3 feeds still read.

**Desk rotation.** No action on the source; it follows RipeHq. Re-sync token scales on the new desk
and re-register the source after all quote sources.

**Confirm keeps reverting.** `time lock not reached` also means expired; cancel and re-propose.
`route too expensive` is a route problem, not a retry problem.

---

## 9. Owner-ratified residuals (accepted, dated 2026-09-09)

Verbatim from the test README: zero-delay setup with FinishSetup as a migration item; preflights
revert on missing history; same-pool update always re-baselines; one-second age minimum;
`hasPendingPriceFeedUpdate` is false during the callback; quote freshness is the quote source's policy
(no V3-specific quote age); desk fallback is availability, not corroboration; a one-second liquidity
hole pins the harmonic floor for the rest of the window under the tested settings; `setFeedDefaults`
is untimelocked because it is proposal-scoped; a later MissionControl priority reorder can revive the
expensive nested quote route; there is no in-transaction cold proof of the stipend.

Two statements the docs require verbatim, because they are the ones people forget:
"Successful confirmation does not replace cold qualification of a production route; the CI cold
tests are the qualification." and "The quote-source rule applies to every source that can become
authoritative for a quote asset, including fallbacks, and must be re-checked after any registry or
priority change."

---

## 10. Reference

**Constants.** Window 1800–14400 s; defaults 3600 / 1800 / 5000 bps; `MAX_PRICED_ASSETS` 50;
`MAX_WARM_QUALIFY_GAS` 170,000; runtime 20,698 bytes; desk stipend per source 250,000; engineering
target 210,000 forwarded.

**Governance entry points.** `addNewPriceFeed`, `confirmNewPriceFeed`, `cancelNewPendingPriceFeed`,
`updatePriceFeed`, `confirmPriceFeedUpdate`, `cancelPriceFeedUpdate`, `disablePriceFeed`,
`confirmDisablePriceFeed`, `cancelDisablePriceFeed`, `setFeedDefaults`, `pause`,
`setActionTimeLockAfterSetup`.

**Views.** `getPrice`, `getPriceAndHasFeed`, `hasPriceFeed`, `hasPendingPriceFeedUpdate`,
`feedConfig(asset)`, `pendingUpdates(asset)`, `pendingQuoteCount(quote)`, `feedDefaults()`,
`getPoolLiquidity(pool, window=0)`, `getFeedLiquidity(asset)`, `isValidNewFeed`,
`isValidUpdateFeed`, `isValidDisablePriceFeed`, `isValidFeedDefaults`.

**Revert strings.** `no perms`, `contract paused`, `pending feed action`, `invalid feed`,
`invalid defaults`, `no pending new feed` / `no pending update feed` / `no pending disable feed`,
`time lock not reached`, `route too expensive`, `price source not executable`, `cannot cancel action`.

**Robinhood chain facts (chain id 4663).** Canonical V3 factory
`0x1f7d7550B1b028f7571E69A784071F0205FD2EfA`; WETH `0x0Bd7D308f8E1639fAb988Df18A8011F41EacAd73`;
resolve PriceDesk, MissionControl and the registry through RipeHq at the time you act. Public RPC
`https://rpc.mainnet.chain.robinhood.com` (first request can be slow; the publicnode mirror rejects
the fork worker mid-run).

**Repository material.** Contract `contracts/priceSources/UniswapV3TwapPrices.vy`; math module
`contracts/priceSources/modules/UniswapV3TwapMath.vy`; runbook
`docs/priceSources/uniswap-v3-twap-runbook.md`; spec `docs/priceSources/uniswap-v3-twap-spec.md`;
review response `docs/priceSources/uniswap-v3-twap-review-response.md`; test README and suites
`tests/priceSources/uniswap_v3/`; depth helper `scripts/twap_pool_depth.py`; fork evidence tool
`scripts/twap_fork_evidence.py`.

**Re-running the evidence.**
```sh
export RIPE_BOA_CACHE_DIR="$(mktemp -d)/compile"
python -m pytest tests/priceSources/uniswap_v3 -n 4 --dist loadfile -q                 # default lane
python -m pytest -o addopts='' tests/priceSources/uniswap_v3/test_twap_gas.py -m gas -s  # T11/T22 gas
RIPE_TWAP_PIN_MODE=fresh RIPE_TWAP_RPC_URL=https://rpc.mainnet.chain.robinhood.com \
  RIPE_TWAP_FORK_OUTPUT=/tmp/twap-fresh.json \
  python -m pytest -o addopts='' tests/priceSources/uniswap_v3/test_twap_fork_qual.py -m fork_qualification -q -s
```
Expected today: 10 qualified, 2 expected rejected (INDEX at 3600 and 14400 s), 0 unverified,
0 failed.
