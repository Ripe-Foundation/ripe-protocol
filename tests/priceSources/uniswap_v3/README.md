# Uniswap V3 TWAP tests

Run from the repository root. Set `RIPE_TWAP_PYTHON` to a Python 3.12 environment
with Vyper 0.4.3 and Titanoboa 0.2.7; use scratch caches.

```sh
export PYTHONDONTWRITEBYTECODE=1
export RIPE_BOA_CACHE_DIR="$(mktemp -d)/compile"
export RIPE_TWAP_FORK_CACHE="$(mktemp -d)/fork"
"$RIPE_TWAP_PYTHON" -m pytest tests/priceSources/uniswap_v3 -q
"$RIPE_TWAP_PYTHON" -m pytest -o addopts='' tests/priceSources/uniswap_v3 -m fuzz -q -s
"$RIPE_TWAP_PYTHON" -m pytest -o addopts='' tests/registries/test_price_desk_gas.py tests/priceSources/uniswap_v3 -m gas -q -s
"$RIPE_TWAP_PYTHON" scripts/export_abis.py --check
"$RIPE_TWAP_PYTHON" -m pytest -o addopts='' tests/deployment/test_abi_export.py -q
"$RIPE_TWAP_PYTHON" -m pytest tests/priceSources tests/registries tests/inventory tests/test_price_desk_aggregate_source_count_guard.py tests/test_lean_shard_coverage.py -q
# After staging, include all newly tracked fixtures in hygiene checks.
"$RIPE_TWAP_PYTHON" -m pytest tests/inventory/test_repository_hygiene.py -q
```

Rebuild actual Solidity wrappers and compare checked artifact bytes:

```sh
forge build --root tests/priceSources/uniswap_v3/reference/v3 --use 0.7.6
forge build --root tests/priceSources/uniswap_v3/reference/v4 --use 0.8.26
"$RIPE_TWAP_PYTHON" tests/priceSources/uniswap_v3/reference/artifacts.py --check
"$RIPE_TWAP_PYTHON" -m pytest tests/priceSources/uniswap_v3/test_twap_math.py -q -s
# Intentional reference regeneration: omit --check from artifacts.py.
```

Ordinary CI reads offline artifacts, without compiler downloads or RPC.
Artifact JSON records source/executable hashes, immutable offsets and storage
layout: V3 solc 0.7.6/Istanbul, V4 solc 0.8.26/Cancun, optimizer 800 runs.
Compiled comparisons cover 303 ticks and 2,424 quotes. Explicit fuzz covers
2,048 signed-floor and 2,048 mulDiv cases, with remainder/overflow strata.

Production math derives from pinned MIT V4; its full notice remains in the
Vyper module. V3 references and compiled fixtures are separate: GPL-2.0-or-later
applies to TickMath, OracleLibrary, the wrapper and the pool after its license
change date (no later than April 1, 2023). Original notices/core LICENSE and
GPL text (SPDX license-list-data v3.25.0) are retained under `reference/v3`;
MIT notices remain under `reference/v4`. The upstream lock pins vendored hashes.
This does not replace the specification's later release legal review.

The original frozen rows remain unchanged; missing metadata is explicitly
synthetic in their replay. `fixtures/fresh-57185814.json` separately captures
live return bytes. Offline replay uses synthetic dispatch, not live lookup gas.
Stress tests deploy the canonical pinned factory/pool, verify its runtime except
compiler-listed immutable offsets, calibrate storage packing against organic
history, and reuse synthetic 20,000/65,535-slot rings. Live runtime hashes and
fork gas are separate; local compiled runtime is not claimed identical to live.

Cold measurements reset metering, transient storage and Boa access journals,
then mark only sender/top-level recipient warm. Snapshot IDs are restored into
an empty access journal for pytest rollback. SLOAD controls prove cold/warm/cold;
two-call wrappers separate child costs from wrapper overhead. Tests print
per-dependency gas, lookup depth/slots, platform/setup timing and final size.
Gas excludes transaction intrinsic cost and chain data fees. The gas file has
a five-minute local target within the unchanged 30-minute CI job. On Python
3.12.13/arm64 with the compile cache warm, 26 gas tests took 8.99s; the combined
34-test required gas selection took 63.35s. Diagnostic sizes: math wrapper 3,166 bytes; guarded read skeleton 15,452; lifecycle/final
source 20,635, including constructor immutables.

Fork workers deploy the entire graph after selecting the pin. Laboratory
liquidity minima are 1, observation age 3,600, local quote age 0, local global
quote age 86,400. Source delay/expiry are 2/100 block counts; block-only advances
preserve the pinned timestamp. Constructor delays use contract-visible block
counts; oracle windows use seconds. Exclude this source from FinishSetup's
`setActionTimeLockAfterSetup` sweep: its delay is already set.

```sh
unset RIPE_TWAP_BLOCK RIPE_TWAP_BLOCK_HASH
RIPE_TWAP_PIN_MODE=fresh RIPE_TWAP_RPC_URL=https://rpc.mainnet.chain.robinhood.com "$RIPE_TWAP_PYTHON" -m pytest -o addopts='' tests/priceSources/uniswap_v3/test_twap_fork_qual.py -m fork_qualification -q -s
RIPE_TWAP_PIN_MODE=pinned RIPE_TWAP_RPC_URL=https://rpc.mainnet.chain.robinhood.com RIPE_TWAP_BLOCK=57037442 RIPE_TWAP_BLOCK_HASH=0x2488e1b687eaa880ee85ddbe92b903039500f7e03ef6ead1bdb1374a4659fc27 "$RIPE_TWAP_PYTHON" -m pytest -o addopts='' tests/priceSources/uniswap_v3/test_twap_fork_qual.py -m fork_qualification -q -s
```

Pinned mode prefers explicitly supplied `RIPE_TWAP_ARCHIVE_RPC_URL`. Missing
state remains unverified, with no fresh fallback. RPC retries/timeouts are finite;
the worker checks the same header again at completion. Passing laboratory tests
does not qualify production routes or approve borrowing.
