# CCIP pure-Vyper reference

`ExampleGreenCcipBurnMintPool.vy` is a reviewed reference for the selected
GREEN pool architecture. It is not production-ready or deployment-authorized.
The RIPE pool should use the same reviewed behavior while returning false from
`canMintGreen()` and true from `canMintRipe()`.

## Reproducible local checks

Use the repository's pinned Vyper `0.4.3`. The source pins EVM target
`shanghai`; passing a conflicting CLI target should be treated as an error, not
an alternate artifact.

```bash
vyper --version
vyper -f settings,abi,method_identifiers \
  docs/chains/rh/examples/ExampleGreenCcipBurnMintPool.vy
vyper -f bytecode,bytecode_runtime \
  docs/chains/rh/examples/ExampleGreenCcipBurnMintPool.vy
```

The standard selectors that must remain fixed include:

| Function | Selector |
| --- | --- |
| `lockOrBurn((bytes,uint64,address,uint256,address))` | `0x9a4575b9` |
| `releaseOrMint((bytes,uint64,address,uint256,address,bytes,bytes,bytes))` | `0x39077537` |
| `applyChainUpdates(uint64[],(uint64,bytes[],bytes,(bool,uint128,uint128),(bool,uint128,uint128))[])` | `0xe8a1da17` |
| `addRemotePool(uint64,bytes)` | `0x62ddd3c4` |
| `removeRemotePool(uint64,bytes)` | `0xacfecf91` |
| `setChainRateLimiterConfig(uint64,(bool,uint128,uint128),(bool,uint128,uint128))` | `0xcf7401f3` |
| `getCurrentOutboundRateLimiterState(uint64)` | `0xc75eea9c` |
| `getCurrentInboundRateLimiterState(uint64)` | `0xaf58d59f` |

## Explicit compatibility bounds

Vyper requires finite dynamic-array and bytes bounds. The reference supports:

- 8 remote chains;
- 8 remote pools per chain;
- 256 allowlist entries;
- 64-byte remote token and pool addresses;
- 64-byte receiver, original-sender, source-pool, and source-pool-data fields;
  and
- 2,048-byte offchain token data.

The selected EVM-to-EVM peers encode token/pool addresses as 32-byte
`abi.encode(address)` values and decimal metadata as 32 bytes. Do not configure
a non-EVM or custom peer format without re-reviewing every bound; oversized
calldata reverts during Vyper decoding before a custom error can be emitted.

## What local compilation does not prove

Compilation, selector parity, in-memory execution, and bytecode-size checks do
not prove:

- Chainlink acceptance, assisted-registration eligibility, Token
  Manager/Expert compatibility, Directory listing, or monitoring support;
- parity with every present or future contracts-CCIP behavior;
- Base or Robinhood fork/runtime compatibility;
- compliance with the destination token-gas overhead;
- safe testnet or mainnet configuration;
- Department pause/recovery compatibility; or
- audit readiness.

Before testnet, obtain the Chainlink technical answers and write the production
implementation/test specification. Before mainnet, require an independent
audit, differential tests against the accepted Chainlink source, a real
OffRamp/Router/RMN-proxy destination-gas measurement with approved margin,
two-chain testnet evidence, exact role/configuration review, and separate
transaction authority.
