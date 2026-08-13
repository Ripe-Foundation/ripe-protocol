# Solidity contracts

Ripe is written in Vyper. This directory exists for the one place where that is not
practical: Chainlink CCIP token pools, which have to be a `TokenPool` subclass to be
usable by CCIP, and Chainlink only publishes those in Solidity.

```
src/RipeCcipBurnMintTokenPools.sol  # RIPE and GREEN pool candidate/reference
src/RipeTokenPool.sol               # retained legacy testnet-only pool source
src/v0.8/...                        # vendored Chainlink CCIP 1.5.1 sources
```

## Repository candidate/reference pool source

`RipeCcipBurnMintTokenPools.sol` defines the repository candidate/reference
implementation: one token-specific subclass of
`BurnMintTokenPool 1.5.1` for GREEN and one for RIPE. Each adds the two functions
RipeHq staticcalls on any address it grants minting rights to:

- `GreenCcipBurnMintTokenPool` returns `(true, false)` from
  `canMintGreen()` / `canMintRipe()`.
- `RipeCcipBurnMintTokenPool` returns `(false, true)`.

The answers are compiled-in pure functions, not constructor flags. That prevents a
deployment from accidentally swapping capabilities while preserving the stock
five-argument pool constructor.

Without them the stock Chainlink pool can never mint: `RipeToken.mint()` asks
`RipeHq.canMintRipe(pool)`, which staticcalls `canMintRipe()` back on the pool and
reverts when it is missing.

Everything else - `lockOrBurn`, `releaseOrMint`, rate limits, allowlist, ownership,
`typeAndVersion` - is the stock 1.5.1 pool, so CCIP tooling treats it like any other
burn/mint pool.

`RipeTokenPool.sol` is the earlier configurable-capability implementation retained for
the existing Base Sepolia/Robinhood testnet migration history. Neither it nor this
candidate/reference implementation should be cited as proof of exact live-pool creation
provenance. The live topology, capabilities, reported type/version, and runtime hashes
are recorded separately, but the exact live source set, compiler version/settings,
constructor arguments, and creation bytecode/artifact identity remain unresolved.

## Vendored sources

`src/v0.8/` is the exact standard-json input of the verified
`BurnMintTokenPool 1.5.1` deployment on base-sepolia
([0x4DFd9eBB670F22b0cf53A53088E38636855CC600](https://sepolia.basescan.org/address/0x4DFd9eBB670F22b0cf53A53088E38636855CC600)),
the pool the CCIP token manager UI deploys. `foundry.toml` mirrors the compiler settings
Chainlink used for that Base Sepolia deployment (solc 0.8.26, paris, via-ir, 80000
runs), so the vendored source is compiled with the same settings here. Those repository
settings are not evidence of the settings used to create the live mainnet pools.
Preserve every source file's SPDX header.
This README records technical source provenance only; it makes no conclusion about
license interpretation or legal sufficiency.

## Build

```sh
forge build --root solidity
```

Repository mainnet migrations are configured to use the token-specific contract name
and `source_file="RipeCcipBurnMintTokenPools.sol"`; a future/replacement deployment
through them would use the Foundry artifact and record the address in the manifest.
That configuration does not prove how the existing live pools were created.

## Verify

Boa's etherscan verification only knows how to bundle Vyper sources, so verify these with
foundry. The migration logs the exact command, including the encoded constructor args:

```sh
forge verify-contract --root solidity --chain 8453 \
    --constructor-args <printed by the migration> \
    --etherscan-api-key $ETHERSCAN_API_KEY \
    <address> src/RipeCcipBurnMintTokenPools.sol:RipeCcipBurnMintTokenPool
```
