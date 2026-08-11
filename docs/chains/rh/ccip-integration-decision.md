# Robinhood Chain CCIP integration decision

> **Historical planning record.** CCIP is now deployed and activated. The
> current topology, production 1.5.1 source line, and remaining operational
> gates are recorded in [ccip-live-state.md](ccip-live-state.md). Statements
> below that deployment or registration has not happened are superseded.

Status: **Conditional draft — thin Solidity inheritance selected; external
confirmation and production implementation approval still required**

Decision date: 2026-07-23

Last revised: 2026-07-27

Scope: GREEN and RIPE on Base <-> Robinhood Chain

Current gate: The exact-hash thin-subclass reference passed Round-3 independent
source/build/Ripe-compatibility review. Supported lane/pool version, assisted
registration, destination-gas configuration, production build-package
authority, production audit, and deployment remain gated.

## Decision

Proceed conditionally with direct CCIP burn/mint pools that inherit Chainlink's
published `BurnMintTokenPool`. The 2026-07-27 owner direction reverses the
earlier pure-Vyper choice.

Use two token-specific Solidity subclasses:

- `GreenCcipBurnMintTokenPool`, which returns true from `canMintGreen()` and
  false from `canMintRipe()`; and
- `RipeCcipBurnMintTokenPool`, which returns false from `canMintGreen()` and
  true from `canMintRipe()`.

Do not override `lockOrBurn`, `releaseOrMint`, validation, rate limiting,
remote-pool configuration, ownership, Router, RMN, allowlist, decimal, event,
error, or version behavior. The constructor is an exact five-argument
pass-through to Chainlink's concrete pool. The two capability views are the
only Ripe-specific runtime behavior.

This is materially safer than a from-scratch pool because the bridge behavior
comes directly from Chainlink's standard implementation. It does **not** mean
Chainlink's audits automatically cover the subclass, RipeHq callback path,
compiler/dependency pin, deployment configuration, or Ripe's tests.

The decision authorizes this reference and documentation work. It does not
authorize installing a production dependency tree in the repository,
registering tokens, deploying contracts, accepting external terms, or
broadcasting transactions.

## Selected topology

- Deploy the same GREEN subclass on Base and Robinhood Chain.
- Deploy the same RIPE subclass on Base and Robinhood Chain.
- Configure chain-specific token, Router, RMN proxy, peer pool/token, owner,
  administrator, and rate-limit values at deployment or setup time.
- Keep the pool as the direct caller of `GREEN.mint` or `RIPE.mint`.
- Register each pool in RipeHq and enable only its matching mint flag.
- Use Chainlink-assisted Token Admin Registry registration for the immutable
  Base tokens if Chainlink confirms that path.
- Use the direct Base <-> Robinhood Chain mainnet lane and Base Sepolia <->
  Robinhood Chain Testnet lane.
- Start with an empty pool allowlist unless product policy requires
  permissioned original senders. In Chainlink v1.6.1, allowlist mode is fixed
  at deployment.
- Use capability-only Department compatibility. Do not add a second pause,
  recovery, or adapter layer to the subclasses.
- Treat `RipeHq.setMintingEnabled(false)` as a chain-local stop for **all**
  RipeHq-authorized GREEN and RIPE issuance, token pause as the broader
  token-wide stop, and CCIP rate limits/chain removal as bridge controls.

A separately registered mint adapter is technically possible because it could
become the direct caller authorized by RipeHq. It remains rejected: it adds a
mint-critical trust boundary and does not solve a token-interface problem.
Wrapped assets and lock/release pools remain rejected because they change the
asset/custody model unnecessarily.

## Reference implementation and evidence

[`examples/RipeCcipBurnMintTokenPools.sol`](examples/RipeCcipBurnMintTokenPools.sol)
contains both subclasses. It is an independently reviewed reference, not
production deployment source. The review is bound to source SHA-256
`28fea3591caf8955a4c1f47d34f5abfe249564001578687525f94fddf5cfac77`;
see the
Round-3 review record.

The reference was compiled on 2026-07-27 against:

- `@chainlink/contracts-ccip@1.6.1`;
- `@chainlink/contracts@1.4.0`;
- Solidity `0.8.26`;
- EVM target `paris`;
- optimizer enabled with `80_000` runs;
- IR compilation enabled; and
- bytecode metadata hash disabled.

Those settings reproduce the pinned upstream CCIP v1.6.1 Foundry profile. The
official v1.6.1 Foundry source pin is
`bbab0601244ce58e2ffac0dbc178a80aab1fa4a3`.

Local compile evidence:

| Property | `BurnMintTokenPool` | Each Ripe subclass |
| --- | ---: | ---: |
| Runtime bytecode | 17,334 bytes | 17,472 bytes |
| EIP-170 margin | 7,242 bytes | 7,104 bytes |
| External method selectors | 30 | 32 |
| Storage entries | 8 | 8 |

The derived storage layout is identical to the base layout after normalizing
the compiler's contract-name annotation. The only added selectors are:

- `canMintGreen()` -> `0x40fd6f94`; and
- `canMintRipe()` -> `0x3b6fccc0`.

The inherited constructor ABI remains:

1. `IBurnMintERC20 token`;
2. `uint8 localTokenDecimals`;
3. `address[] allowlist`;
4. `address rmnProxy`; and
5. `address router`.

The deployer is the initial owner through inherited
`Ownable2StepMsgSender`; production setup must transfer ownership and complete
acceptance before the deployer is retired. The inherited
`typeAndVersion()` remains `"BurnMintTokenPool 1.6.1"`.

The initial implementation harness ran two isolated Foundry tests:

- GREEN capability values plus burn/mint execution; and
- RIPE capability values plus mint execution.

The mock token deliberately returned `bool` from `mint` and `burn`, matching
the Vyper GREEN/RIPE ABI, while the inherited Chainlink interface expects no
return value. Both calls succeeded, confirming the compatible extra-return-data
behavior on the tested EVM path.

The independent reviewer then ran 28 passing integration scenarios with the
compiled Solidity pools and the real Vyper GREEN, RIPE, and RipeHq contracts.
That matrix verified the direct authorization call path, real balance/supply
changes, both capability combinations, the extra boolean return data, and the
relevant inherited authorization, peer, RMN, decimal, rate-limit, allowlist,
pause/blacklist, and ownership failures. Neither test harness is a committed
repository build input.

Diagnostic gas from the initial mock harness was:

- `78,813` for a `releaseOrMint` after a preceding call had warmed relevant
  state; and
- `95,902` for a colder `releaseOrMint` path.

These are not accepted production measurements. The mock omits the real
RipeHq registry/config reads and the OffRamp's before/after `balanceOf` calls.
The cold pool-call result exceeds Chainlink's documented 90,000 combined
default by 5,902 gas before that omitted work. Automatic destination execution
may therefore fail under the default configuration. Manual execution with a
token gas override is a recovery path, not acceptable normal service.
Activation remains blocked on a representative Base-fork/testnet full-path
measurement and a Chainlink-supported FeeQuoter token gas overhead with margin.

## Decision record

| Field | Current decision | Confidence / gate |
| --- | --- | --- |
| Production lane | Direct Base <-> Robinhood Chain | Confirmed by current public directory |
| Test lane | Direct Base Sepolia <-> Robinhood Chain Testnet | Confirmed by current public directory |
| Pool model | Thin Solidity subclass of concrete `BurnMintTokenPool`; no adapter | Owner-selected on 2026-07-27; exact-hash Round-3 reference review passed |
| GREEN capability | Both views exist; `canMintGreen() -> true`, `canMintRipe() -> false` | Ripe policy |
| RIPE capability | Both views exist; `canMintGreen() -> false`, `canMintRipe() -> true` | Ripe policy |
| Custom storage | None | Confirmed by compiler storage-layout comparison |
| Custom bridge overrides | None | Confirmed by source and ABI comparison |
| Candidate CCIP pin | `1.6.1` commit `bbab0601244ce58e2ffac0dbc178a80aab1fa4a3` | Publicly documented; live-lane compatibility confirmation still required |
| Shared dependency | `@chainlink/contracts@1.4.0` | Exact dependency declared by the `1.6.1` npm package |
| Compiler/profile | Solidity `0.8.26`, `paris`, via-IR, optimizer `80_000`, no metadata hash | Matches upstream v1.6.1 profile; production lock/tooling still required |
| Constructor ownership | Deployer initially owns; two-step transfer afterward | Inherited Chainlink behavior; setup EOA lifetime is a production control |
| Destination gas | Mock pool call: 78,813 warm / 95,902 colder | Cold pool call exceeds the documented 90,000 combined default; real RipeHq plus full OffRamp path and supported FeeQuoter configuration are hard gates |
| Base token registration | Assisted/manual for immutable tokens | Public path identified; exact process confirmation required |
| Robinhood token registration | Prefer unchanged token source and assisted registration | Conditional; add a discovery hook only if Chainlink requires it and owner approves |
| Pool owner | Owner-approved production multisig | Exact backend/signers and transition pending |
| Token administrator | Owner-approved production multisig | Proposed; chain support must be proven |
| Rate-limit administrator | Separate narrowly scoped incident multisig | Proposed; operational confirmation pending |
| RipeHq authority | Existing Ripe governance | Required for registry plus matching mint flag |
| Department lifecycle | Capability-only; no pool-local Ripe pause/recovery additions | Selected by the “only required functions” direction; residual risk documented below |
| Initial allowlist | Empty / permissionless original sender | Minimum configuration; owner may change only by redeployment because mode is immutable |
| Initial limits | Conservative nonzero caps per token and direction | Quantitative values pending |

## Production toolchain boundary

The repository is currently Vyper-centric and has no production Solidity
package/build path. A later implementation phase must add one bounded,
reproducible Solidity path without replacing the existing Python migration and
manifest authority.

The production implementation specification must:

- pin the two Chainlink package versions and lock their resolved integrity;
- pin Solidity `0.8.26` and every compiler setting listed above;
- pin the exact CCIP source revision and retain its license/notice files;
- run the subclass build in a path-scoped Foundry job;
- export ABI, creation bytecode, runtime bytecode, storage layout, method
  identifiers, compiler input/output, and normalized artifact hashes;
- make the existing migration runner consume only declared, hash-checked
  Solidity artifacts;
- record the five constructor arguments, deployer, initial owner, ownership
  handoff, source hashes, and dependency hashes in the current manifest
  format;
- verify exact source and compiler settings on BaseScan and the Robinhood
  Blockscout explorers; and
- obtain internal license review for the Chainlink BUSL-1.1 dependency before
  deployment or distribution.

The pinned
[`v1.6 Additional Use Grant`](https://github.com/smartcontractkit/chainlink-ccip/blob/bbab0601244ce58e2ffac0dbc178a80aab1fa4a3/chains/evm/contracts/v1.6-CCIP-License-grants.md)
permits developing, deploying, and operating the token-pool contracts solely
for CCIP integration and use. The `1.6.1` npm tarball includes
`contracts/LICENSE.md`, which references that grant, but does not itself
contain the referenced grant file. A production package must therefore retain
both the bundled license and the exact grant from the pinned upstream commit
and complete internal review before deployment.

The reference download used npm tarballs with these published shasums and SRI
integrity values:

- `@chainlink/contracts-ccip@1.6.1`:
  shasum `9b0f5665634110bfa1d249eb58c141e358e05945`,
  integrity
  `sha512-2ainz7DhzSPyUTD01e0roRHQ4V895peJ6rlu+GgxOYCZVFVtuwXEbT27ByyaJSFsB9ZubAtu1zhAijuL0OwPzw==`;
  and
- `@chainlink/contracts@1.4.0`:
  shasum `e976e012fe9104067e9f00ef397de6d48a7d1593`,
  integrity
  `sha512-SpNCJ0TPOI6pa2l702Wk4WIP8ccw5ARcRP1E/ZTqaFffXNoZeF03WhsVL8f3l3OTRFA9Z40O5KcZzmJmZQkoFA==`.

Those values are evidence for this local check, not a substitute for a
committed production lockfile or independently verified release provenance.

## Test and review boundary

Production acceptance must include:

- source/ABI checks proving that only the constructor pass-through and two
  capability views differ from the pinned base;
- storage-layout equality and method-identifier delta checks;
- exact inherited selector, event, custom-error, ERC-165, chain-removal,
  remote-pool, allowlist, ownership, rate-limit, Router, RMN, and decimal tests;
- GREEN and RIPE capability truth-table tests;
- direct use of the real Vyper GREEN/RIPE token and RipeHq contracts;
- authorization failure before RipeHq registration and after removal;
- `mintEnabled == false`, token pause, blacklist, and recovery cases;
- supply-conservation invariants across source burn, in-flight state, and
  destination mint;
- wrong Router, ramp, selector, token, peer pool, decimal, and Department
  permission failures;
- compiler/artifact reproducibility and EIP-170 guards;
- the complete cold OffRamp `balanceOf` + `releaseOrMint` + `balanceOf` gas
  path on both target runtimes;
- two-chain testnet transfers in both directions for both assets;
- upgrade/overlapping-pool/in-flight-message retirement tests; and
- an independent review focused on the subclass delta, dependency pin,
  RipeHq authorization, role/configuration, artifact pipeline, and operational
  assumptions.

Round 3 completed the exact-reference source/build/Ripe-compatibility portion
of that review. Production acceptance still requires review/audit of the
authorized dependency lock, committed build/test/gas harness, artifact
pipeline, chain configuration, and operational package.

Production deployment is never a CI action.

## Alternatives considered

| Alternative | Decision | Reason |
| --- | --- | --- |
| Thin subclass of concrete `BurnMintTokenPool` | **Selected** | Smallest behavioral delta; inherits standard CCIP logic and adds only Ripe capability views |
| Pure-Vyper v1.6.1-shaped pool | Superseded | Larger reimplementation, parity, audit, bounds, timestamp, and maintenance burden |
| Custom pool inheriting `BurnMintTokenPoolAbstract` | Rejected | Appropriate when burn behavior must change; Ripe already matches standard `burn(uint256)` |
| Generic one-contract asset flag | Rejected | Adds immutable configuration and wrong-asset deployment risk for no material code benefit |
| Separate Ripe mint adapter | Rejected | Adds a mint-critical trust boundary without solving an interface problem |
| `BurnFromMintTokenPool` | Rejected | GREEN and RIPE do not implement `burnFrom` |
| Lock/release pool | Rejected | Adds custody/liquidity management unnecessarily |
| Wrapped assets | Rejected | Changes the user-facing asset model unnecessarily |
| Rewrite deployment orchestration in Solidity | Rejected | Would duplicate the repository's manifest and migration authority |

The superseded Vyper comparison is frozen byte-for-byte at its Round-2-reviewed
commit `8147784` artifact. It is retained only for history and must not be
maintained alongside the active Solidity design without separately authorized
purpose and fresh review.

The prior Vyper reference remains under `examples/` as a documented comparison
artifact; it is not the active architecture or production source.

## Department lifecycle compatibility

`interfaces/Department.vyi` includes `isPaused()`, `pause(bool)`, and recovery
functions, but RipeHq registration validates only the capability view
associated with an enabled mint flag. Therefore the two capability-only
subclasses can be registered and authorized.

The selected subclasses intentionally do not implement the broader Department
surface. Consequences:

- `SwitchboardCharlie.pause(pool, ...)` will revert;
- there is no second pool-local Ripe pause flag;
- Chainlink's inherited RMN checks, rate limits, remote-chain/pool removal, and
  Router access controls remain available;
- `RipeHq.setMintingEnabled(false)` stops inbound minting but also every other
  RipeHq-authorized GREEN/RIPE mint on that chain; and
- token pause stops transfers, burns, and mints more broadly.

This is the minimum-change choice implied by adding only the required
capability functions. Security review must accept the lack of a Ripe-specific
pool pause and the global circuit breaker's wider blast radius before
production.

## Governance and operational model

The intended role separation is:

1. a two-step multisig owns each pool and controls Router/remote configuration;
2. a token-administrator multisig controls Token Admin Registry association;
3. a separate incident multisig holds `rateLimitAdmin`;
4. existing Ripe governance controls RipeHq registration and mint enablement;
5. deployer/setup EOAs surrender temporary privileges after verified handoff.

Pool ownership is mint-critical. The owner can replace the Router, and a
malicious Router can nominate attacker-controlled ramps that reach the pool's
RipeHq mint permission. Use governance-quality controls and monitoring.

The incident hierarchy remains:

1. use RipeHq mint disable only when its protocol-wide issuance impact is
   justified;
2. pause the token only when the wider transfer/burn/mint stop is justified;
3. use inherited rate limits, peer removal, and chain removal according to the
   confirmed CCIP procedure; and
4. monitor failed/in-flight messages and use only the confirmed retry/manual
   execution path after recovery.

The final signer matrix, delays, role-transfer order, rate-limit values,
monitoring, manual execution, and re-enable sequence remain owner and
operations gates.

## Ripe sequencing

Ripe-side authorization requires:

1. deploy the pool with the correct capability views;
2. start pool address registration;
3. after `registryChangeTimeLock`, confirm address registration;
4. initiate Hq configuration with only the matching mint flag;
5. after another `registryChangeTimeLock`, confirm Hq configuration; and
6. confirm that RipeHq re-validates the capability view at both config stages.

The waits use `block.number`. Robinhood's repeated/jumping-number clock profile
must be approved before using these timelocks there.

Chainlink Token Admin Registry association and peer configuration are separate
steps. Their exact ordering relative to the Ripe steps must be frozen in the
deployment packet; capability enablement should remain last so a partially
configured pool cannot mint.

## Immutable Base-token implications

The selected pool path requires no change to GREEN, RIPE, or RipeHq. The
existing Base tokens already expose compatible selectors and their extra
`bool` return data was accepted by the tested inherited pool path.

Because the Base tokens expose neither `owner()` nor `getCCIPAdmin()`, the
preferred registration route remains Chainlink-assisted. If Chainlink requires
an admin-discovery hook, stop for an owner decision. Do not infer a Base
migration or Robinhood-only token fork from this pool decision.

## Required follow-on sequence

1. Obtain Chainlink confirmation of the exact supported pool/lane release,
   thin-subclass eligibility, assisted registration, gas overhead, and
   failure/retirement procedure.
2. Freeze the dependency, compiler, licensing, artifact, constructor,
   administration, allowlist, rate-limit, and ownership-transfer decisions.
3. Obtain explicit implementation authority before adding a production
   Solidity dependency/build path or production pool source.
4. Add the production subclasses and full acceptance suite.
5. Obtain independent review/audit of the authorized production dependency,
   build/test/artifact, deployment-configuration, and operational surface. The
   exact-hash reference-source review does not close this gate.
6. Measure the real cold destination path on a fork and both testnets; obtain a
   supported custom gas overhead if required.
7. Prepare a separate testnet transaction packet with exact addresses,
   constructor arguments, roles, peer configuration, limits, Ripe timelocks,
   and rollback/retirement steps.
8. Receive explicit approval before each deployment or registration
   transaction set.
9. Prove both assets in both directions and retain explorer, event, balance,
   supply, gas, and CCIP-message evidence.
10. Return to an owner gate before any mainnet action.

Nothing in this record authorizes a later step.

## Unresolved external fields

- Is a direct subclass of `BurnMintTokenPool` that only adds two unrelated
  pure views supported for assisted registration, Token Manager/Expert,
  Directory listing, monitoring, and production lanes?
- Is token-pool `1.6.1` the supported target for the live directory lanes that
  report core `1.6.0`, and is the directory RMN value the constructor proxy?
- What exact assisted-registration proof and ordering apply to the unchanged
  Base and Robinhood token contracts?
- What destination token-gas overhead is configured, and how is a higher
  supported value applied if the measured full path exceeds the default?
- What retry/manual-execution and remote-pool retirement procedure applies to
  Ripe's pause/blacklist/mint-disable cases?

These are Chainlink-technology or Chainlink-process questions. Ripe's
capability meanings, token selectors, RipeHq registration, and subclass code
do not need to be explained back to Ripe by Chainlink.

## External-contact gate

The question packet remains **not sent** and requires fresh owner approval of
the exact text, recipient, channel, and act of sending. Text approval does not
cover terms acceptance, dependency installation, production implementation,
role changes, deployment, registration, or transaction broadcast.

When an authoritative response is received, preserve the dated response and
provenance in `docs/chains/rh/ccip-chainlink-response-record.md`.

## `rh-summary.md` checklist mapping

No checkbox state changed in this revision.

| Exact checklist item | Review / closure status |
| --- | --- |
| Pin the supported CCIP pool/API reference and decide how the selected thin Solidity subclasses and artifacts will be dependency-locked, built, delta-tested, verified, and deployed with exact compiler/EVM settings. | Thin inheritance and a candidate reproducible profile are selected; the item remains open pending supported-version confirmation and owner/security approval of the production build package. |
| Select Chainlink-assisted registration as the preferred path so Robinhood can deploy the same existing GREEN and RIPE token implementations without adding a Robinhood-only `getCCIPAdmin()` change. | Internal topology preference selected; authoritative support/process confirmation is still open and no registration is authorized. |
| Confirm the supported registration path with Chainlink. | Packet is ready for owner review; not eligible for closure until an authoritative answer is captured. |

The direct-lane evidence, Ripe interface proof, exact-hash independently
reviewed thin-subclass reference, and revised packet are ready. Version
support, registration, full-path gas, production toolchain authority,
production-package review/audit, operational parameters, and external action
remain open.
