# Uniswap V3 TWAP tests and operation

Owner decisions D1–D20, 2026-09-09. The [current specification](../../../docs/priceSources/uniswap-v3-twap-spec.md)
and [operator runbook](../../../docs/priceSources/uniswap-v3-twap-runbook.md)
describe the shipped contract and both scale-recovery sequences.

A feed returns geometric historical asset/quote TWAP multiplied by the quote's
current PriceDesk USD price. The quote may be either pool token other than the
asset; this is not an arithmetic USD TWAP. Add/update arguments are
`(asset, pool, twapWindow=0, maxObservationAge=0)`. Each zero resolves at proposal
to the then-current default: window 3600, age 1800, ratio 5000 basis points.
The proposal stores resolved window/age, harmonic baseline, and the absolute
floor `ceil(baseline*ratio/10000)`. Defaults are three fields and never read by
active pricing. Ratio, baseline and current liquidity cannot be zero. Both
current and harmonic liquidity must reach the stored floor; every update
re-baselines. A zero floor is impossible for an admitted positive baseline.

The extrapolated fraction is `<= min(age/window, 1)`; age must be positive and
no greater than the window. The 50% bound applies only to defaults 1800/3600.
At most one observation is written per second on any chain. A full ring of N
slots spans at least N−1 seconds, so successful admission observe plus
`cardinality >= window + 1` is sufficient; cardinalityNext is not admission
cardinality. Typed preflights still revert when history is unavailable.

Precision uses one whole asset token times 1e18 through tick math and removes
that extra factor in the final full-width USD mulDiv. Independent Fraction
bounds cover low-decimal quotes and sub-cent assets, alongside compiled V3/V4
references, tick extremes, rounding branches, accumulator wraps and overflow.

Confirmation order is governance/pause/state, identity and factory mapping,
structural/loop/scale checks, timelock, staged config, measured desk callback,
then pending clear/count decrement/enumeration/event. Identity drift cancels
with one event and returns false. Every transient failure reverts and preserves
the proposal. Disable has no identity or dependency check. Internal cancel
helpers emit; public helpers do not duplicate logs. Pending inbound quote
counts protect both pending and active quote use within one source instance.

The canonical desk is always resolved through Addys. A nonzero supplied desk
must match it; `_staleTime` is ignored even when zero. Quote freshness belongs
to the quote source's policy. The priced asset's cached desk scale is checked
on confirmation and every read, not at proposal. Zero/unset or the snapshot's
exact scale is compatible; first sync and quote-scale hardening remain a
separate PriceDesk follow-up.

## Quote route and operator procedure

A quote must be priced by sources that never call back into PriceDesk, such as
Chainlink, Pyth or Stork. Order this V3 source after every quote source. D4 is
operator procedure only; there is no contract allowlist or priority walk.
Cross-instance and wrapper cycles, including wsuperOETHb-style routes, remain
an accepted limitation. Tests admit them with independent fallback and show
both prices becoming zero when that fallback is removed.

The quote-source rule applies to every source that can become authoritative for a quote asset, including fallbacks, and must be re-checked after any registry or priority change.

Before any feed proposal, review candidate token upgradeability and decimals
mutability, pool identity/history, proposed resolved policy, and every quote
route/fallback. Run the read-only helper:

```sh
"$RIPE_TWAP_PYTHON" scripts/twap_pool_depth.py "$RPC" "$POOL" "$ASSET" --source "$SOURCE"
# Without a source: --window 3600 --age 1800 --ratio 5000 (also the defaults).
# --block N pins explicitly; otherwise latest is pinned and printed.
# --price-desk ADDRESS selects an explicit desk when there is no source.
```

With `--source`, defaults and canonical desk are read from that source's RipeHq
at the pin. Without it, the helper resolves current-manifest RipeHq for RH/Base
mainnet, then the live desk ID 7; other chains require `--price-desk`. Confirm
the printed identity. All pool/quote calls use the same block and the final
header is rechecked. It prints tokens/order, fee, current/harmonic liquidity,
cardinality and its window+1 check, age, and the proposal's absolute floor.
Each 1%/2% direction walks tickBitmap and ticks, applies every liquidityNet
crossing and rounds inputs/outputs like V3 swap steps. USD input is fee-inclusive,
marked at initial spot and the pinned live desk quote. It is labelled
“market depth snapshot at block N; not a TWAP manipulation cost”. No current
in-range liquidity is extrapolated through unexamined ranges. Operator tests
compare both directions/orders against canonical multi-range swaps exactly.

Do not propose a pool whose smaller-direction 2% depth is below the value
governance sets in the runbook. That value is currently unset; this work sets
no economic threshold. The runbook also requires confirmed event verification
after scale-sync batches: Safe MultiSend does not treat returned false as
failure, so an identity cancellation can leave earlier calls in place.

## Tests and reproducible evidence

Run from repository root: Python 3.12, Vyper 0.4.3, Titanoboa 0.2.7 and
pytest-xdist 3.8.0. Set `RIPE_TWAP_PYTHON` to that interpreter. Omit xdist flags
for serial operation; keep file ordering with `--dist loadfile` when parallel.

```sh
export PYTHONDONTWRITEBYTECODE=1
export RIPE_BOA_CACHE_DIR="$(mktemp -d)/compile"
"$RIPE_TWAP_PYTHON" -m pytest tests/priceSources/uniswap_v3 -n 4 --dist loadfile -q
"$RIPE_TWAP_PYTHON" -m pytest -o addopts='' tests/priceSources/uniswap_v3 -m fuzz -q -s
"$RIPE_TWAP_PYTHON" -m pytest -o addopts='' tests/registries/test_price_desk_gas.py tests/priceSources/uniswap_v3 -m gas -q -s
"$RIPE_TWAP_PYTHON" -m pytest -o addopts='' tests/priceSources/uniswap_v3/test_twap_fork_config.py tests/priceSources/uniswap_v3/test_twap_artifacts.py -q
"$RIPE_TWAP_PYTHON" scripts/export_abis.py --check
"$RIPE_TWAP_PYTHON" -m pytest -o addopts='' tests/deployment/test_abi_export.py -q
"$RIPE_TWAP_PYTHON" -m pytest tests/priceSources tests/registries tests/inventory tests/test_price_desk_aggregate_source_count_guard.py tests/test_lean_shard_coverage.py -n 4 --dist loadfile -q
```

The two tooling/artifact files run in required CI job `twap-tooling`, excluded
from lean shards and explicitly required by `rh-pr-gate`. Gas stays in
`snapshot-gas`. The coverage guard proves each file has exactly one default
shard or dedicated tooling job. Default CI is offline; fork RPC is opt-in.

Cold gas tests reset access journals, metering and transient storage while
preserving snapshot IDs; only sender/top-level recipient start warm. SLOAD
controls prove cold/warm/cold behavior. Gas excludes intrinsic cost and chain
data fees. Canonical pool bytecode is verified except compiler-listed
immutables; synthetic 20000/65535 rings are calibrated against organic history.
The historical ring proof also runs 3601 organic one-second overwrites.

For contract phase `8a9b90ec` (codesize), all rows below passed the original
20-case gas matrix. These are maxima over that named matrix, not universal
worst-case bounds. Targets are 22500 runtime bytes / 210000 forwarded source
gas; hard limits are 24576 bytes / 250000 stipend. “Burn” is a deliberate hostile
source-isolation case, not supported route qualification.

| Checkpoint | Runtime B | Successful forwarded max | Late failure max | Burn | Direct successful max |
| --- | ---: | ---: | ---: | ---: | ---: |
| codesize baseline | 19544 | 167190 | 174283 | 248164 | 187829 |
| §3.1 | 19527 | 160756 | 169991 | 248064 | 181395 |
| §3.2 | 19587 | 161631 | 170820 | 248077 | 182270 |
| §3.3 | 19867 | 165094 | 174290 | 248162 | 185733 |
| §3.4 | 20185 | 165094 | 174290 | 248162 | 185733 |
| §3.5 | 20202 | 165782 | 174984 | 248173 | 185738 |
| §3.6 | 20614 | 165782 | 174984 | 248173 | 185738 |
| §3.7 | 20650 | 165782 | 174984 | 248173 | 185738 |
| §3.8 | 20650 | 165782 | 174984 | 248173 | 185738 |

Phase 2 `cb69a688` had 95 new remediation cases and 44 gas cases. The review
follow-up distinguishes **warm source child**, **admission callback**, and
**cold source child**. Across add/update, canonical and storage-heavy routes,
source-to-source delta is **18000 gas**; callback overhead is **8885** and
cold-source minus callback remains **9115**. `MAX_WARM_QUALIFY_GAS` remains
**170000**, conservatively giving **188000 <= 210000**. The touch set is:

- Addresses: source itself (top-level recipient), pool, canonical desk, RipeHq.
- Storage: all ten staged `feedConfig[asset]` fields (pool, fee, quoteAsset,
  assetIsToken0, assetDecimals, quoteDecimals, baseLiquidity, twapWindow,
  maxObservationAge, minLiquidity); `PriceDesk.tokenScale[asset]`;
  `RipeHq.addrInfo[7].addr`.

T11 derives member offsets from compiler layout/types, prints concrete
addresses/slots, and verifies the intersection with executed reads. The pool's
metadata immutables do not warm slot0/liquidity/observations. HQ entry 5 and
MissionControl policy are first read during the callback. CI preserves these
printed measurements with `-s`. The [dated review response](../../../docs/priceSources/uniswap-v3-twap-review-response.md)
records current samples; the table above preserves the original checkpoints.

Both a hostile metadata path and a governance batch that reads the quote
before confirming can warm extra storage, pass admission, and fail cold.
Confirm in a transaction whose only other call is a preceding scale sync for
the same asset. Quote reads and preflights belong in a separate transaction.
The runbook covers gas estimation, zero-scale conversion failures, identity
cancellation before unlock, and verification of confirmed events after a batch.

Successful confirmation does not replace cold qualification of a production route; the CI cold tests are the qualification.

## Fresh fixed-WETH laboratory

Fork qualification uses pinned live pools and ETH/USD anchor, with locally
deployed RipeHq/PriceDesk/ChainlinkPrices/V3 contracts. It is a fixed-WETH
laboratory, not production route qualification. Defaults use the new model;
expected results derive independently from raw captured inputs and compiled
reference tick math, never copied contract outputs. Each case and the complete
run verify the pinned header. Missing header/state stays unverified; a second
downgrade preserves the first observed status. `qualified`, `expected_rejected`
and `unverified` are separate buckets; behavioral failures remain explicit.
Engineering target overruns fail qualification. Rejections assert the expected
`invalid feed` or `OLD` reason, not an arbitrary revert.

```sh
unset RIPE_TWAP_BLOCK RIPE_TWAP_BLOCK_HASH
RIPE_TWAP_PIN_MODE=fresh RIPE_TWAP_RPC_URL="$RPC" RIPE_TWAP_FORK_OUTPUT=/tmp/twap-fresh.json "$RIPE_TWAP_PYTHON" -m pytest -o addopts='' tests/priceSources/uniswap_v3/test_twap_fork_qual.py -m fork_qualification -q -s
# Pinned replay: set mode=pinned and both RIPE_TWAP_BLOCK and RIPE_TWAP_BLOCK_HASH.
# RIPE_TWAP_ARCHIVE_RPC_URL is preferred for pinned mode; there is no fallback pin.
```

Atomic checkpoints retain inputs, stages, discrepancies, dependency traces
and sanitized failure reasons. A 600-second worker deadline retains evidence
but fails incomplete execution. The active fixture selected by `fork_inputs.py`
is regenerated from the current model. Its source hashes cover the contract,
math, worker, graph/gas helpers and transitive Vyper dependencies. A canonical
hash of `LAB` plus reference vectors excludes the fixture filename, avoiding
a self-reference. Required offline tests reject source/model drift. Captures
also record their Git revision and whether the worktree was dirty; content
hashes, rather than that revision alone, identify the replayed implementation.

The exact reviewed-head `11d3bd30` output is preserved unchanged in
[repository evidence](../../../docs/priceSources/evidence/uniswap-v3-twap/README.md),
with all recorded hashes checked against that Git revision. Its 10 qualified /
2 expected-rejected split belongs to that pin, not a permanent pool assumption.
The final follow-up head's complete raw JSON is attached losslessly to the PR
report, outside the commit it qualifies, to avoid a self-referential commit hash.

## Provenance and ratified residuals

Production math retains the pinned MIT V4 notice. Separate V3 references retain
GPL-2.0-or-later notices, core LICENSE and SPDX license-list-data v3.25.0 text;
the pool's license change date is no later than April 1, 2023. V4 notices/upstream
hashes remain pinned. Compiler artifacts bind source, executable bytes,
immutables and storage layout: V3 solc 0.7.6/Istanbul; V4 solc 0.8.26/Cancun;
optimizer 800 runs. Rebuild/check commands:

```sh
forge build --force --root tests/priceSources/uniswap_v3/reference/v3 --use 0.7.6
forge build --force --root tests/priceSources/uniswap_v3/reference/v4 --use 0.8.26
"$RIPE_TWAP_PYTHON" tests/priceSources/uniswap_v3/reference/artifacts.py --check
```

Ratified residuals — **2026-09-09, source: owner** (verbatim):

zero-delay setup with FinishSetup as a migration item; preflights revert on missing history; same-pool
update always re-baselines; one-second age minimum; `hasPendingPriceFeedUpdate` is false during the
callback; quote freshness is the quote source's policy (no V3-specific quote age); desk fallback is
availability, not corroboration; a one-second liquidity hole pins the harmonic floor for the rest of the
window under the tested settings; `setFeedDefaults` is untimelocked because it is proposal-scoped; a later
MissionControl priority reorder can revive the expensive nested quote route; there is no in-transaction
cold proof of the stipend (see §3.6).
