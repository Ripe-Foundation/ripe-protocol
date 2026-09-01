# Chainlink technical question packet: GREEN/RIPE on Base <-> Robinhood Chain

> **Historical unsent draft; do not send as current state.** The pools are now
> live, but the exact live source/compiler/settings/constructor identity and
> relationship to the repository's 1.5.1 candidate are unresolved. See
> [ccip-live-state.md](ccip-live-state.md) for confirmed topology and the
> destination-gas evidence question that remains unresolved.

Status: **REVISED DRAFT — NOT SENT — FRESH OWNER APPROVAL REQUIRED**

Revised: 2026-07-27

Recipient and channel: Pending owner selection

External actions taken: None

This version reflects the selected thin Solidity inheritance design. It asks
only questions that depend on Chainlink's technology, lane configuration, or
registration process. Ripe contract questions have been resolved locally.

## Proposed subject

Thin BurnMintTokenPool subclasses and assisted registration for GREEN/RIPE on
Base and Robinhood Chain

## Proposed message

Hello Chainlink team,

Ripe is evaluating a direct CCIP burn/mint bridge for GREEN and RIPE between
Base and Robinhood Chain. Nothing has been deployed or registered.

Existing Base deployments:

- GREEN: `0xd1Eac76497D06Cf15475A5e3984D5bC03de7C707`
- RIPE: `0x2A0a59d6B975828e781EcaC125dBA40d7ee5dDC0`
- RipeHq: `0x6162df1b329E157479F8f1407E888260E0EC3d2b`

The published deployments and source are available on BaseScan:
[GREEN](https://basescan.org/address/0xd1Eac76497D06Cf15475A5e3984D5bC03de7C707#code),
[RIPE](https://basescan.org/address/0x2A0a59d6B975828e781EcaC125dBA40d7ee5dDC0#code),
and
[RipeHq](https://basescan.org/address/0x6162df1b329E157479F8f1407E888260E0EC3d2b#code).
Each token's `ripeHq()` resolves to the RipeHq address above, whose
`governance()` identifies Ripe's onchain authority. Governance is also the
authorized caller of each token's `pause(bool)`. We propose this onchain chain,
plus an owner-approved signature or non-disruptive demonstration in the form
you require, as assisted-registration authority evidence.

Both tokens use 18 decimals and expose:

- `mint(address,uint256) returns (bool)`;
- `burn(uint256) returns (bool)`;
- `balanceOf(address)`; and
- `decimals()`.

They expose neither `owner()` nor `getCCIPAdmin()`. The Base contracts are
direct, non-proxy deployments and should remain unchanged.

Both tokens are pausable and blacklistable. Pause blocks transfer, mint, and
burn; destination mint also rejects a blacklisted receiver. These local
failure modes motivate the retry/manual-execution question below.

Our proposed pool contracts inherit the concrete contracts-CCIP v1.6.1
`BurnMintTokenPool`. They do not override any CCIP function or add storage.
Each constructor passes the standard five arguments directly to
`BurnMintTokenPool`. The only additions are two unrelated parameterless pure
views used by the token's local mint-authorization system:

```solidity
function canMintGreen() external pure returns (bool);
function canMintRipe() external pure returns (bool);
```

The GREEN subclass returns `(true, false)` and the RIPE subclass returns
`(false, true)`. The pool remains the direct caller of the inherited
`burn(amount)` and `mint(receiver,amount)` paths. Local compilation against
`@chainlink/contracts-ccip@1.6.1` and `@chainlink/contracts@1.4.0` confirmed
that the subclasses add only those two selectors and no storage. Local
execution also confirmed that the tokens' extra `bool` return data is accepted
by the inherited void-return interface.

Could you please confirm these Chainlink-specific points:

1. **Supported pool shape and release.** Is a direct subclass of the concrete
   `BurnMintTokenPool` that only adds the two pure views above supported for
   assisted registration, Token Manager/Expert, Directory listing, monitoring,
   manual execution, and production lanes? For Base <-> Robinhood mainnet and
   Base Sepolia <-> Robinhood testnet, should we pin contracts-CCIP `1.6.1`
   even though the public lane records report core `1.6.0`? Is each
   directory-listed `RMN` address the RMN proxy intended for the pool
   constructor?

2. **Assisted Token Admin Registry process.** For the immutable Base tokens,
   which expose neither `owner()` nor `getCCIPAdmin()`, what exact
   `proposeAdministrator`/assisted-registration process, proof of authority,
   initiator, and ordering should we use? Can that same assisted path be used
   for unchanged Robinhood deployments? If not, which exact discovery
   interface is required on the new Robinhood tokens?

3. **Destination token gas.** What token gas overhead is configured for these
   lanes, and what measurement margin do you require for the full OffRamp
   `balanceOf` + `releaseOrMint` + `balanceOf` path? Our isolated mock measured
   `releaseOrMint` at 78,813 gas after warming and 95,902 gas on a colder path;
   the cold pool call alone exceeds the documented 90,000 combined default by
   5,902 gas before the real RipeHq work and OffRamp balance checks are
   included. We therefore treat the default as insufficient unless a
   representative full-path measurement proves otherwise. What supported
   process sets the token-specific `destGasOverhead`/FeeQuoter configuration
   when a higher value is required?

4. **Failure and pool-retirement operations.** When destination minting
   reverts because local minting is disabled, the token is paused, or a
   receiver is blacklisted, what exact CCIP state and retry/manual-execution
   procedure applies after recovery? When replacing or removing a remote pool,
   what monitoring/waiting procedure establishes that no in-flight message
   will be stranded?

For each answer, please identify whether it is required before testnet,
required before mainnet, recommended, or unsupported.

Thank you.

## Questions intentionally excluded

Ripe will not ask Chainlink to determine:

- what the two capability views mean inside Ripe;
- whether the pool is the direct token mint caller;
- whether GREEN/RIPE's existing mint and burn selectors exist;
- how RipeHq registry/config timelocks work;
- whether Ripe should add a second mint adapter or custom pause layer; or
- whether the token contracts need Ripe-side changes.

Those items are answered by the local contracts and selected architecture.

## Answer-to-decision map

| Chainlink answer | Ripe consequence |
| --- | --- |
| Thin subclass supported on `1.6.1` | Freeze the dependency/compiler pin and production artifact/test specification |
| Thin subclass must instead derive from another base or expose a different version surface | Stop and review the exact required delta; do not change bridge behavior implicitly |
| `1.6.1` not supported for these lanes | Rebase to the named release and repeat source/ABI/storage/gas review |
| Assisted registration available on both chains | Keep Base and Robinhood token source unchanged |
| Admin hook required on Robinhood only | Stop for the existing owner decision on a narrow pre-deployment exception versus shared-source policy |
| Admin hook required on Base | Stop; any Base migration or permanent divergence requires separate authority |
| Existing token gas overhead has measured margin | Keep the standard lane configuration |
| Higher overhead required and supported | Freeze the exact Chainlink configuration and test it before activation |
| Required overhead unsupported | Redesign or block activation |
| Retry/retirement procedure confirmed | Encode it in testnet acceptance and the incident runbook |

## Approval gate

Do not send this packet, select a recipient on the owner's behalf, submit a
form, accept terms, deploy, register, or broadcast a transaction without fresh
explicit authorization.
