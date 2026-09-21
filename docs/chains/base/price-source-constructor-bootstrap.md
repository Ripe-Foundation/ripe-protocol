# Migration-only price-source bootstrap

ChainlinkPrices and CurvePrices accept initial configuration in their deployment
arguments. This avoids calling `qualifyCallerPriceSource` on the legacy active
PriceDesk while staging replacement sources. There is no post-deployment bypass:
existing governance setters, timelocks and confirmation qualification remain.

## Constructor inputs

Append to ChainlinkPrices' existing ten arguments:

```python
initial_feeds = [
    (asset, feed, stale_time_seconds, needs_eth_to_usd, needs_btc_to_usd),
]
```

Decimals are read from the feed, not trusted from supplied metadata. Entries
are checked against real rounds and conversion anchors after the entire list is
installed. Conversion anchors can therefore appear anywhere in the list.
Zero stale time retains its existing meaning: inherit the active MissionControl
policy; explicit nonzero stale times avoid that dependency during staging.
Duplicate assets, including collisions with the existing ETH/WETH/BTC default
feed arguments, revert. To supply those anchors through the list, pass zero for
the corresponding old default feed addresses. The total asset limit, including
default feeds, remains 50.

Append to CurvePrices' existing seven arguments:

```python
initial_feeds = [(asset, pool)]
initial_green_ref_pool = (ZERO, ZERO, 0, ZERO, 0, 0, 0, 0, 0, 0)
# Or supply the single full GreenRefPoolConfig tuple; this is not an array.
```

The reference tuple fields are `pool, lpToken, greenIndex, altAsset,
altAssetDecimals, maxNumSnapshots, dangerTrigger, staleBlocks,
stabilizerAdjustWeight, stabilizerMaxPoolDebt`. Read them from the reviewed live
source. Use the entirely zero-valued struct to leave it unconfigured; a zero
pool skips reference-pool initialization. Metadata is validated against the registry and token; a fresh pool
snapshot is seeded. Historical snapshots and accumulated danger time are not
copied, and snapshot warmup must be reviewed before activation.

Pool metadata is read from the Curve registry. Duplicate assets, invalid pool
structure and dependency cycles revert. Constructor loading intentionally does
not test pool routes through PriceDesk, so a configured route can still be
unpriceable. An empty initial list preserves unconfigured deployment behavior.

## Activation gate

Use a **new migration** and fresh labels; do not rerun or rewrite historical
migrations/manifests. Re-read live configuration into the lists and verify exact
readback, feed enumeration, deployment gas and initcode size. This change does
not select production addresses or submit a deployment.

Before HQ/source activation, qualify every route on a fork with the intended
new PriceDesk and real gas budget, including Undy dependencies, GREEN reference
snapshots, retained-vault liquidation and deleverage. Constructor loading solves
staging order, not the existing gas/compatibility qualification blockers.
