# Configured Base price sources — deploy only

Migration: `2026092101_DeployConfiguredBasePriceSources.py`.

Deployment and activation are separate. The retained Aero and wrapped-OETH
sources support the new desk's combined call when passed a valid PriceDesk.
Do not test them with a zero desk address and interpret that revert as an absent
selector. Aggregate routing still needs a canonical-PriceDesk fork check.

```sh
python -m scripts.migrate --profile base-mainnet \
  --start-timestamp 2026092101 --single --fork
```

Remove `--fork` only after reviewing the rehearsal. The previous deploy-only MC
migration must be recorded complete. MC does not need to be activated for this step.
All new deployments use distinct `BasePrices20260921` labels. Normal resume is
supported by the migration journal; never force-replay or remove an in-progress
journal. Live configuration drift during a partial deployment needs review.

The migration deploys PriceDesk with **3M quote and 3M snapshot budgets**, then
only the three updated source implementations: Chainlink, Curve and Undy.
The existing Aero and wrapped-OETH sources are reused. Chainlink's complete feed configuration
is loaded in its constructor (anchors first). Curve's routes and single GREEN
reference pool are also loaded in the constructor. Other configurable sources use
temporary governance and their normal add/confirm methods before relinquishing it.
Feed policy is read from the active sources, not hardcoded from old deployment logs.
Pyth, Stork, RedStone and disabled BlueChip are not redeployed. Their IDs are
reserved with the old addresses and disabled in the new registry. If an assumed
unused source gains feeds, preflight stops instead of omitting them silently.
Source and registry delays are copied where configurable during setup.

Source IDs remain:

| ID | Source | Treatment |
|---|---|---|
| 1 | Chainlink | All live feed mappings copied |
| 2 | Curve | All live routes and reference-pool policy copied |
| 3 | BlueChip | Not redeployed; registry slot remains disabled |
| 4 | Pyth | Empty live source; not redeployed; candidate slot disabled |
| 5 | Stork | Empty live source; not redeployed; candidate slot disabled |
| 6 | Legacy Aero | Current source retained for RIPE |
| 7 | Wrapped superOETH | Current source retained unchanged |
| 8 | Undy | Live vault metadata and snapshot policies copied |
| 9 | RedStone | Empty live source; not redeployed; candidate slot disabled |

The new Aero implementation is UI-only and is not deployed here. Neither retained
source's configuration, governance, snapshots or delay is modified. Wrapped-OETH's
existing retired mcbETH/VVV fallback behavior is preserved, not newly enabled.
Disabled BlueChip's old feed mappings are not re-enabled.

Only **fresh** Curve/Undy snapshots are seeded. Historical windows, danger counters,
and accumulated observations are not imported. All token scales needed by the
configured routes and current collateral are cached on the new PriceDesk.

This migration does not change HQ, live sources, MC, vaults, or treasury balances.
It does not propose activation. Configuration readback is not price equivalence:
before activation, check all collateral quotes, fresh snapshot behavior after the
governance wait, and full liquidation/deleverage gas on the intended department set.

The current RIPE/WETH LP already has a zero PriceDesk quote, and retired VVV
has a one-wei legacy fallback. Neither is evidence of usable collateral pricing.
Canonical-forward guards make candidate PriceDesk queries return zero while the
old desk is active; aggregate qualification must make the candidate canonical on
an isolated fork through governance, not bypass those guards in production.

## Fork rehearsal — 2026-09-21

At Base block **51,626,101**, the actual standard runner completed this migration:
four deployments, 79 journaled deployment/setup transactions, and 19,745,255 total
execution gas across those transactions. The 20 Chainlink configurations, two
Curve route configurations/reference policy, and six Undy vault policies matched
their live inputs. The active HQ slot and source registry were unchanged by staging.

A separate fork-only governance proposal, 21,600-block wait (12 hours), and HQ
slot-7 confirmation exercised the candidate as canonical PriceDesk. Across all
27 MC-listed assets, no nonzero old quote became zero on the new desk. Retained
Aero RIPE and wrapped-OETH quotes matched. Freshly seeded Undy observations can
produce small differences from the old weighted snapshot window; exact price
equality is not claimed.

This is **not** an all-prices-healthy or activation approval: seven routes were
zero on both desks after the frozen-feed wait (USDC, undyUSD, undyUSDC, GREEN,
sGREEN, GREEN/USDC LP, and RIPE/WETH LP). The USDC dependency became stale without
real future oracle updates; RIPE/WETH LP was already zero before waiting. Retired
VVV remained at its existing one-wei fallback. Fresh upstream quotes and full
operation gas still need checking before real activation. No transactions were
broadcast, no oracle updates were fabricated, and no live manifest was rewritten.
