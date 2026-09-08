# Uniswap V3 TWAP tests

Run from the repository root with Python 3.12, Vyper 0.4.3, Titanoboa 0.2.7
and the pinned pytest-xdist 3.8.0. Set `RIPE_TWAP_PYTHON` to that interpreter.

```sh
export PYTHONDONTWRITEBYTECODE=1
export RIPE_BOA_CACHE_DIR="$(mktemp -d)/compile"
export RIPE_TWAP_FORK_CACHE="$(mktemp -d)/fork"
"$RIPE_TWAP_PYTHON" -m pytest tests/priceSources/uniswap_v3 -n 4 --dist loadfile -q
"$RIPE_TWAP_PYTHON" -m pytest -o addopts='' tests/priceSources/uniswap_v3 -m fuzz -q -s
"$RIPE_TWAP_PYTHON" -m pytest -o addopts='' tests/registries/test_price_desk_gas.py tests/priceSources/uniswap_v3 -m gas -q -s
"$RIPE_TWAP_PYTHON" scripts/export_abis.py --check
"$RIPE_TWAP_PYTHON" -m pytest -o addopts='' tests/deployment/test_abi_export.py -q
"$RIPE_TWAP_PYTHON" -m pytest tests/priceSources tests/registries tests/inventory tests/test_price_desk_aggregate_source_count_guard.py tests/test_lean_shard_coverage.py -n 4 --dist loadfile -q
# After staging, include newly tracked fixtures in hygiene checks.
"$RIPE_TWAP_PYTHON" -m pytest tests/inventory/test_repository_hygiene.py -q
```

Rebuild the actual Solidity wrappers and compare checked artifact bytes:

```sh
forge build --force --root tests/priceSources/uniswap_v3/reference/v3 --use 0.7.6
forge build --force --root tests/priceSources/uniswap_v3/reference/v4 --use 0.8.26
"$RIPE_TWAP_PYTHON" tests/priceSources/uniswap_v3/reference/artifacts.py --check
"$RIPE_TWAP_PYTHON" -m pytest tests/priceSources/uniswap_v3/test_twap_math.py -q -s
# Intentional reference regeneration: omit --check from artifacts.py.
```

Ordinary CI uses offline artifacts without downloads or RPC. Artifact JSON pins
sources, executable hashes, immutable offsets and storage layout: V3 solc
0.7.6/Istanbul, V4 solc 0.8.26/Cancun, optimizer 800 runs. Compiled comparisons
cover 303 ticks and 2,424 quotes; fuzz covers 2,048 signed-floor cases (all four
sign/exactness strata) and 2,048 mulDiv cases (four guaranteed overflow strata).

Production math retains the pinned MIT V4 notice in its Vyper module. Separate
V3 references/fixtures retain GPL-2.0-or-later notices, core LICENSE and the GPL
text from SPDX license-list-data v3.25.0; the pool's license change date is no
later than April 1, 2023. V4 MIT notices and all upstream hashes remain pinned.
The specification's later release legal review remains required.

Frozen rows are unchanged; missing replay metadata is synthetic. The separately
captured `fixtures/fresh-57185814.json` uses synthetic dispatch offline, which
does not measure live lookup gas. Stress tests verify canonical compiled pool
runtime except compiler-listed immutables, calibrate storage against organic
history, and reuse synthetic 20,000/65,535-slot rings. The independent search
model predicts a subset of measured observation slots, not the live read order.

Cold tests reset metering, transient storage and access journals, preserving
snapshot IDs in an empty journal. Only sender/top-level recipient are warmed;
SLOAD controls prove cold/warm/cold. The private journal recipe has an explicit
version/layout guard. Gas excludes intrinsic cost and chain data fees. Tests
enforce 210,000 source gas and 22,500 deployed bytes; any D2 exception must be
named, bounded and explained in `gas_tools.py`. The deliberate cumulative-burn
failure has one such exception; hard stipend/EIP-170 limits always apply.
The 27 gas tests took 11.66s on Python 3.12.13/arm64 with a warm compile cache,
within the five-minute target and unchanged 30-minute CI job. Final source size
is 20,635 bytes; canonical peak cold direct/forwarded source gas is 170,809/156,699.

Fork workers deploy the graph after selecting the pin. Laboratory liquidity
minima are 1, observation age 3,600, local quote age 0 and global quote age 86,400.
Delay/expiry are 2/100 block counts; block-only advances preserve the timestamp.
Exclude this source from FinishSetup's `setActionTimeLockAfterSetup` sweep.

```sh
unset RIPE_TWAP_BLOCK RIPE_TWAP_BLOCK_HASH
RIPE_TWAP_PIN_MODE=fresh RIPE_TWAP_RPC_URL=https://rpc.mainnet.chain.robinhood.com "$RIPE_TWAP_PYTHON" -m pytest -o addopts='' tests/priceSources/uniswap_v3/test_twap_fork_qual.py -m fork_qualification -q -s
RIPE_TWAP_PIN_MODE=pinned RIPE_TWAP_RPC_URL=https://rpc.mainnet.chain.robinhood.com RIPE_TWAP_BLOCK=57037442 RIPE_TWAP_BLOCK_HASH=0x2488e1b687eaa880ee85ddbe92b903039500f7e03ef6ead1bdb1374a4659fc27 "$RIPE_TWAP_PYTHON" -m pytest -o addopts='' tests/priceSources/uniswap_v3/test_twap_fork_qual.py -m fork_qualification -q -s
```

Pinned mode prefers explicit `RIPE_TWAP_ARCHIVE_RPC_URL`; missing state remains
unverified with no fresh fallback. RPC retries/timeouts are finite. Atomic
checkpoints retain raw replies, stages, measured mismatches and sanitized reasons.
Dependency traces include forwarded/used gas, headroom and nested proxy calls.
Each completed case and the final run recheck the pinned header. A 600s worker
timeout retains verified cases and marks unfinished work unverified. Expected
route rejection is `unavailable`; a behavior mismatch is `failed`. Passing
laboratory tests does not qualify production routes or approve borrowing.
