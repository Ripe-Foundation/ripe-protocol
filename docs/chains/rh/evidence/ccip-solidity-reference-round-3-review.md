# CCIP thin-Solidity reference: Round-3 independent review record

Status: **Independent reference review complete — production acceptance not
granted**

Review received: 2026-07-27

Repository head observed by the reviewer:
`70dd76516ca9b4af8c0797c327bf15732634e5f6`

Reviewed source:
[`../examples/RipeCcipBurnMintTokenPools.sol`](../examples/RipeCcipBurnMintTokenPools.sol)

Reviewed source SHA-256:
`28fea3591caf8955a4c1f47d34f5abfe249564001578687525f94fddf5cfac77`

Received review transcript SHA-256:
`c8c76e22910adbfec0a5e3f4425d97a2d8a0aa20011de14b6aba7d4377818e1a`

## Verdict and boundary

The independent reviewer found no defect in the 49-line Solidity source. The
review reproduced the pinned build and verified that the two token-specific
contracts are exact constructor-pass-through subclasses of Chainlink
contracts-CCIP v1.6.1's concrete `BurnMintTokenPool`. The subclasses add only
the two Ripe capability views, add no storage, and override no inherited bridge
behavior.

This review closes the independent-review gate only for the exact reference
source hash above and its Ripe compatibility claim. It does not approve a
production Solidity package, dependency lock, artifact pipeline, gas
configuration, deployment, registration, or activation. Any source-byte or
dependency-setting change reopens the exact-byte review.

## Independently reproduced results

The reviewer independently reproduced:

| Property | Result |
| --- | --- |
| Chainlink source | npm contracts-CCIP `1.6.1` pool sources matched commit `bbab0601244ce58e2ffac0dbc178a80aab1fa4a3` |
| Shared dependency | `@chainlink/contracts@1.4.0` |
| Compiler profile | solc `0.8.26`, EVM `paris`, optimizer `80_000`, via-IR, metadata hash disabled |
| Standard pool runtime | 17,334 bytes |
| Each Ripe subclass runtime / creation | 17,472 / 18,952 bytes |
| EIP-170 runtime margin | 7,104 bytes |
| ABI delta | only `canMintGreen()` and `canMintRipe()` |
| Storage delta | none; eight inherited entries remain identical |
| Constructor | exact five-argument forwarding |
| Version string | inherited `"BurnMintTokenPool 1.6.1"` |
| Capability values | GREEN `(true,false)`; RIPE `(false,true)` |

The reviewer also ran 28 passing integration scenarios with the compiled
Solidity pools and the real Vyper `GreenToken`, `RipeToken`, and `RipeHq`
contracts in one local EVM. The matrix covered the capability truth tables,
RipeHq's two-factor authorization, real mint/burn balance and supply changes,
the Vyper tokens' extra boolean return data, ramp/source-pool/RMN failures,
decimal conversion, rate limits, allowlist behavior, token mint-disable/pause/
blacklist recovery, and two-step pool ownership.

The test and gas harnesses were isolated reviewer artifacts and are not
repository build inputs. Their successful execution is review evidence, not a
substitute for the separately authorized production build/test package.

## Open findings carried forward

1. The existing diagnostic cold `releaseOrMint` measurement is `95,902` gas,
   which exceeds Chainlink's documented `90,000` combined default by `5,902`
   before the real RipeHq path and OffRamp before/after `balanceOf` checks are
   included. A real Base-fork/testnet measurement and supported FeeQuoter token
   gas configuration remain hard activation gates. Manual execution with a
   token gas override is a recovery path, not acceptable normal service.
2. The repository has no authorized production Solidity dependency lock,
   compiler/build configuration, committed tests, gas harness, or explorer
   standard-JSON package. Adding that bounded path remains an owner/security
   implementation decision.
3. Chainlink must still confirm the supported pool/API release, thin-subclass
   eligibility, assisted-registration path, destination token-gas
   configuration, and safe failed-message/pool-retirement operations.
4. The Chainlink dependency's v1.6 Additional Use Grant covers developing,
   deploying, and operating token-pool contracts for CCIP integration and use.
   A production package must retain the pinned dependency's license and notice
   files and complete internal license review before deployment.

## Reviewer environment and repository boundary

The reviewer reported Node `22.19.0`, solc
`0.8.26+commit.8a97fa7a`, titanoboa `0.2.7`, Vyper `0.4.3`, eth-abi
`5.2.0`, and Forge `1.3.5` present but unused. Dependencies, compilation, and
tests ran outside the repository. The worktree and reviewed source hash were
unchanged at the beginning and end. No repository edit, commit, push,
deployment, registration, transaction, or Chainlink contact occurred.
