# Solidity contracts

Ripe is written in Vyper. This directory exists for the one place where that is not
practical: Chainlink CCIP token pools, which have to be a `TokenPool` subclass to be
usable by CCIP, and Chainlink only publishes those in Solidity.

```
src/RipeTokenPool.sol   # the pool ripe deploys
src/v0.8/...            # vendored chainlink ccip 1.5.1, unmodified
```

## RipeTokenPool

`BurnMintTokenPool 1.5.1` plus the two functions RipeHq staticcalls on any address it
grants minting rights to:

- `canMintGreen()` / `canMintRipe()` - set as constructor flags, immutable after that.
  A pool declares which token it is for, and RipeHq can only grant it what it declared.
  Deploy one pool per token.

Without them the stock Chainlink pool can never mint: `RipeToken.mint()` asks
`RipeHq.canMintRipe(pool)`, which staticcalls `canMintRipe()` back on the pool and
reverts when it is missing.

The extra constructor args are the only departure from the stock pool's signature -
`(token, localTokenDecimals, allowlist, rmnProxy, router, canMintGreen, canMintRipe)`.

Everything else - `lockOrBurn`, `releaseOrMint`, rate limits, allowlist, ownership,
`typeAndVersion` - is the stock 1.5.1 pool, so CCIP tooling treats it like any other
burn/mint pool.

## Vendored sources

`src/v0.8/` is the exact standard-json input of the verified
`BurnMintTokenPool 1.5.1` deployment on base-sepolia
([0x4DFd9eBB670F22b0cf53A53088E38636855CC600](https://sepolia.basescan.org/address/0x4DFd9eBB670F22b0cf53A53088E38636855CC600)),
the pool the CCIP token manager UI deploys. `foundry.toml` mirrors the compiler settings
Chainlink used for it (solc 0.8.26, paris, via-ir, 80000 runs), so the vendored code
compiles here the same way it does upstream. Those files are BUSL-1.1, keep the headers.

## Build

```sh
forge build --root solidity
```

Migrations do this for you - `migration.deploy_solidity("RipeTokenPool", ...)` builds,
deploys from the foundry artifact and records the address in the manifest.

## Verify

Boa's etherscan verification only knows how to bundle Vyper sources, so verify these with
foundry. The migration logs the exact command, including the encoded constructor args:

```sh
forge verify-contract --root solidity --chain base-sepolia \
    --constructor-args <printed by the migration> \
    --etherscan-api-key $ETHERSCAN_API_KEY \
    <address> src/RipeTokenPool.sol:RipeTokenPool
```
