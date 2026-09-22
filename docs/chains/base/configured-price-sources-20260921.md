# Configured Base price sources — deploy only

Migration: `2026092101_DeployConfiguredBasePriceSources.py`.

```sh
python -m scripts.migrate --profile base-mainnet \
  --start-timestamp 2026092101 --single --fork
```

This revision retains the existing source order, including empty sources. Current
compiled executable bytecode differs from the recorded live deployments for
Chainlink, Curve, BlueChip, Pyth, Stork, wrapped-OETH, Undy and RedStone. Aero has
changed to a UI-only monitor. Eight source implementations and PriceDesk are
deployed anew; wrapped-OETH is deliberately retained for legacy StabilityPool
compatibility. PriceDesk uses **3M quote and 3M snapshot budgets**.

| ID | Source | Configuration |
|---|---|---|
| 1 | Chainlink | All live feed mappings, anchors first, in constructor |
| 2 | Curve | All live pools and single GREEN reference configuration in constructor |
| 3 | BlueChip | New implementation; slot remains disabled; no historical feeds revived |
| 4 | Pyth | Current network/confidence policy, currently no feeds |
| 5 | Stork | Current network, currently no feeds |
| 6 | Aero | New UI-only monitor; no protocol RIPE feed |
| 7 | Wrapped superOETH | Live source retained unchanged, including mcbETH/VVV fallbacks |
| 8 | Undy | All six live vault configurations, fresh snapshots |
| 9 | RedStone | Current ETH binding, currently no feeds |

MC priority stays **`[1, 8, 2, 9, 4, 5]`**. No MC writes or priority migration are
needed. No legacy source is temporarily registered: the new BlueChip is registered
then disabled solely to preserve the existing disabled ID 3. Other sources remain
registered, including the Aero monitor at ID 6. The UI must call the monitor's
`getRipeUsdMonitoringPrice()` directly (its oracle methods deliberately return no
feed). Aero still obtains WETH/USD through the canonical PriceDesk.

RIPE no longer has the legacy Aero protocol quote. Wrapped-OETH remains at
`0x064488f53849616eeE3EE32c29307922B319bb7C`, with no deployment or state changes.
The mcbETH/VVV one-wei fallbacks are required for legacy SP claim-basket dust,
not collateral valuation. Historical BlueChip feeds and a new Morpho V2 factory
are not enabled by this deployment.

Chainlink/Curve/Undy policy is copied from live sources, not old logs. Empty-source
preflight stops if Pyth, Stork or RedStone gains feeds, so newly added mappings are
not silently lost. Setup governance is relinquished, but newly deployed source action
timelocks and the new PriceDesk registry delay deliberately stay **zero** for this
deployment wave. Neither `setActionTimeLockAfterSetup` nor
`setRegistryTimeLockAfterSetup` is called. Constructor minimum/maximum bounds
remain unchanged for future governance configuration. No live sources
are modified. Wrapped-OETH and Aero have no temporary
governor. Only fresh Curve/Undy observations are seeded; historical windows and
danger counters are not imported. Token scales for configured assets are cached.

## Execution and validation

The preceding MC deployment must be recorded complete; MC need not be activated.
All deployments use `BasePrices20260921` labels. This all-source revision changes
transaction ordering from earlier drafts: do not resume an earlier partially
executed draft with it or delete/force-replay its journal. Normal resume applies
only to this unchanged revision. Live configuration drift during deployment
requires review.

Deployment leaves HQ unchanged. Activation requires a separate governance action
and fresh price checks. Do not treat zero quotes through an inactive candidate as
proof of a broken source: canonical-forward guards require the candidate to be
activated inside a fork for aggregate comparisons.

Undy's existing contract test suite passed **82 tests** on 2026-09-21. The revised
superseded ten-deployment sequence, before the zero-delay and retained-source edits,
completed on a read-only-upstream Base fork at block
**51,627,234**: 84 journaled transactions and 36,158,243 aggregate execution gas.
Feed configuration readbacks passed and staging left HQ unchanged. A separate
fork-only HQ proposal, 21,600-block wait and confirmation exercised the new desk.
Across 27 MC assets, the only nonzero-to-zero changes were the intentional RIPE
and retired VVV removals. Aero's UI quote was nonzero. Undy prices can differ
slightly because its snapshot windows are freshly seeded.

Seven other routes were zero on both desks after the frozen-feed wait: USDC,
undyUSD, undyUSDC, GREEN, sGREEN, GREEN/USDC LP and RIPE/WETH LP. The stale USDC
dependency and pre-existing unpriced RIPE LP remain activation caveats, not new
source losses. No future oracle updates were fabricated. No live transactions
were sent and the user's deployment history was not modified.
Full liquidation/deleverage and department activation qualification remain
separate from this price-source migration.

At block **51,628,844**, a focused fork proved why wrapped-OETH must be retained:
the live GREEN/USDC SP basket contained one raw unit each of mcbETH and VVV.
Its total-value call succeeded before replacing the source and reverted after
replacement, without advancing time. The MC-only price scan was insufficient
to qualify these outstanding claim liabilities. This revised nine-deployment
migration retains the live source; syntax/static checks passed, but the complete
revised sequence has not yet been rerun on a fork.
