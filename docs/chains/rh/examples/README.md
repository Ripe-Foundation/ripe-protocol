# CCIP pool references

> **Historical 1.6.1 design reference.** This directory is not live-source
> provenance. The deployed Base and Robinhood pools report
> `BurnMintTokenPool 1.5.1`; `solidity/src/RipeCcipBurnMintTokenPools.sol` is the
> current repository candidate/reference, not proof of their exact creation
> source. Current state and gates are in
> [`../ccip-live-state.md`](../ccip-live-state.md).

Status: **Independently reviewed reference — not production-ready or
deployment-authorized**

Last reviewed: 2026-07-27

## Historical thin-inheritance reference

[`RipeCcipBurnMintTokenPools.sol`](RipeCcipBurnMintTokenPools.sol) contains the
selected GREEN and RIPE reference subclasses. It is not production-ready or
deployment-authorized. The Round-3 independent review is bound to source
SHA-256
`28fea3591caf8955a4c1f47d34f5abfe249564001578687525f94fddf5cfac77`;
see the
`review record`.

Each contract inherits Chainlink contracts-CCIP v1.6.1's concrete
`BurnMintTokenPool`, passes through the standard five constructor arguments,
and adds only:

- `canMintGreen() -> bool`; and
- `canMintRipe() -> bool`.

The GREEN contract returns `(true, false)` and the RIPE contract returns
`(false, true)`. Neither contract adds storage or overrides Chainlink's bridge
behavior. RipeHq mechanically calls only the capability granted in that pool's
configuration. Keeping both views with an explicit false value for the
opposite asset preserves the shared Department ABI and provides
defense-in-depth against a wrong-asset configuration.

### Pinned reference build

The initial reference build and the 2026-07-27 independent reproduction used:

- `@chainlink/contracts-ccip@1.6.1`;
- `@chainlink/contracts@1.4.0`;
- Solidity `0.8.26`;
- EVM `paris`;
- optimizer `80_000` runs;
- via-IR compilation; and
- no bytecode metadata hash.

These reproduce the upstream v1.6.1 Foundry profile. The official source pin is
`bbab0601244ce58e2ffac0dbc178a80aab1fa4a3`.

The independent build comparison reproduced:

| Property | `BurnMintTokenPool` | Each Ripe subclass |
| --- | ---: | ---: |
| Runtime bytecode | 17,334 bytes | 17,472 bytes |
| Creation bytecode | — | 18,952 bytes |
| EIP-170 runtime margin | 7,242 bytes | 7,104 bytes |
| External method selectors | 30 | 32 |
| Storage entries | 8 | 8 |

A normalized storage-layout comparison found no added storage, and the only
added selectors were:

| Function | Selector |
| --- | --- |
| `canMintGreen()` | `0x40fd6f94` |
| `canMintRipe()` | `0x3b6fccc0` |

The initial implementation harness ran two isolated Foundry tests for the
GREEN and RIPE capability/mint paths. The token mock deliberately returned
`bool` from `mint` and `burn`, matching the Vyper GREEN/RIPE contracts, while
the inherited Chainlink interface expects no return data.

The independent reviewer then ran 28 passing scenarios with the compiled pools
and the real Vyper GREEN, RIPE, and RipeHq contracts. Those tests established
the direct OffRamp-to-pool-to-token-to-RipeHq authorization path and relevant
inherited failure behavior. Neither harness is committed as a reproducible
repository test package.

The mock gas report measured `releaseOrMint` at 78,813 gas after relevant state
was warmed and 95,902 gas on a colder path. The colder pool-call measurement
exceeds Chainlink's documented 90,000 combined default by 5,902 gas even before
the real RipeHq reads or OffRamp before/after balance checks are included.
Automatic destination execution may therefore fail under the default
configuration. Manual execution with a token gas override is a recovery path,
not acceptable normal operation. A real Base-fork/testnet measurement and a
Chainlink-supported FeeQuoter token gas configuration with margin remain hard
activation gates.

### Dependency and license boundary

The reference source uses a floating-compatible Solidity pragma, while the
review build pinned solc `0.8.26`. A production source/build package must make
the compiler pin enforceable through committed build configuration and a
dependency lock; this reference alone is not reproducible repository tooling.

The pinned Chainlink v1.6 Additional Use Grant permits developing, deploying,
and operating the token-pool contracts for CCIP integration and use.
Production packaging must retain the pinned dependency's license and notice
files and complete internal license review before deployment.

### Constructor and ownership

The constructor is the standard Chainlink v1.6.1 shape:

1. local token;
2. local token decimals;
3. initial allowlist;
4. local RMN proxy; and
5. local Router.

The deployer is the initial owner. Production setup must complete inherited
two-step ownership transfer to the approved owner before retiring the setup
account.

### What this reference does not prove

Compilation and local tests do not prove:

- that Chainlink will support/list the thin subclass for the selected lanes;
- that `1.6.1` is the final supported pool pin for lanes reporting core
  `1.6.0`;
- assisted-registration approval for GREEN/RIPE;
- full cold destination gas compliance;
- correct production roles, limits, peers, or deployment ordering;
- explorer verification and artifact-pipeline readiness; or
- automatic audit coverage for the Ripe subclass and integration.

## Superseded pure-Vyper comparison

[`ExampleGreenCcipBurnMintPool.vy`](ExampleGreenCcipBurnMintPool.vy) preserves
the earlier from-scratch Vyper design for review history and comparison. It is
not the active architecture or production source.

The exact Round-2-reviewed historical artifact is the file at commit `8147784`
with SHA-256
`7f3b46af23b9456869b0a72578d3ae295cbfb8ff112d0f7bddd1d66a4afb1e18`.
The superseded file is frozen byte-for-byte at that artifact. Do not maintain
or revise it alongside the active Solidity design; a future change would
require a separately authorized purpose and fresh review.

That implementation had to reproduce Chainlink's pool state machine and
introduced finite Vyper bounds, a nonstandard sixth constructor argument, a
post-2106 timestamp-conversion difference, and a much larger differential-test
and audit surface. Those are the reasons the thin Solidity inheritance path is
now preferred.
