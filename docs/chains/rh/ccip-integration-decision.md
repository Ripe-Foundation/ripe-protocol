# Robinhood Chain CCIP integration decision

Status: **Conditional draft — external confirmation and owner approval required**

Decision date: 2026-07-23

Scope: GREEN and RIPE on Base <-> Robinhood Chain

Current gate: Owner review of Track 1 evidence and outbound question packet

## Decision

Proceed conditionally with the minimal direct burn/mint bridge design as the
Track 1 working architecture. Do not begin implementation, install new
dependencies, register tokens, deploy contracts, accept external terms, or
broadcast transactions until the blocking Chainlink answers are received and
the owner approves the next phase.

Public evidence establishes the lane and a viable technical shape, but not the
supported production pool version, Chainlink's acceptance of the thin custom
pool, assisted-registration procedure, or commercial/security requirements.
This is therefore a conditional go for design preparation, not authorization to
build or deploy.

## Selected architecture

- Use a direct CCIP burn/mint topology. Do not introduce a mint adapter.
- Maintain one thin GREEN pool implementation across Base and Robinhood Chain
  and one thin RIPE pool implementation across both chains.
- Preserve Chainlink's standard direct calls to `burn(uint256)` and
  `mint(address,uint256)`.
- Add only `canMintGreen() -> true` to the GREEN pool and only
  `canMintRipe() -> true` to the RIPE pool.
- Register each pool as a RipeHq department and enable only its matching mint
  permission.
- Use the direct public Base <-> Robinhood Chain lane and the direct Base
  Sepolia <-> Robinhood Chain Testnet lane.
- Start with conservative independent per-token, per-direction rate limits.

An adapter is rejected because RipeHq authorizes the direct `msg.sender` of each
token's mint call. A wrapping topology is rejected because it changes the asset
model and is unnecessary when the native tokens already satisfy the burn/mint
interface.

## Decision record

| Field | Current decision | Confidence / gate |
| --- | --- | --- |
| Production lane | Direct Base <-> Robinhood Chain | Confirmed by current public directory |
| Test lane | Direct Base Sepolia <-> Robinhood Chain Testnet | Confirmed by current public directory |
| Pool model | Thin direct custom burn/mint pool; no adapter | Selected from code and interface evidence |
| GREEN capability | GREEN pool exposes only `canMintGreen() -> true` | Required by RipeHq |
| RIPE capability | RIPE pool exposes only `canMintRipe() -> true` | Required by RipeHq |
| Final inheritance base | `BurnMintTokenPool` subclass or `BurnMintTokenPoolAbstract` | Chainlink answer required |
| Candidate CCIP pin | `1.6.1` commit `bbab0601244ce58e2ffac0dbc178a80aab1fa4a3` | Provisional; compatibility confirmation required |
| Candidate shared EVM pin | `e06cc226086ad91cfede63e96c63e5b3440c9801` | Provisional exact dependency pin |
| Compiler floor | Solidity `0.8.24` | From candidate source; exact compiler patch pending |
| Base token registration | Assisted/manual for immutable tokens | Public path identified; process confirmation required |
| Robinhood token registration | Prefer unchanged token source and assisted registration | Conditional; Chainlink should confirm versus asymmetric `getCCIPAdmin()` |
| Pool owner | Two-step production multisig | Proposed; signer and supported transition pending |
| Token administrator | Production multisig | Proposed; registration sequence pending |
| Rate-limit administrator | Separate narrowly scoped incident multisig | Proposed; operational confirmation pending |
| RipeHq authority | Existing Ripe governance | Required for department registration and matching mint flag |
| Initial limits | Conservative nonzero caps, separately configured by token and direction | Quantitative recommendation pending |
| Implementation toolchain | Foundry subproject integrated with the existing Python migration system | Selected, not installed |

## Toolchain decision

### Selected boundary

Add a narrowly scoped Foundry project under `solidity/ccip/` while retaining the
existing titanoboa/Vyper migration system as the single deployment and manifest
authority.

Proposed structure:

```text
solidity/ccip/
  foundry.toml
  remappings.txt
  src/
    RipeGreenBurnMintTokenPool.sol
    RipeRipeBurnMintTokenPool.sol
  test/
  script/
```

No Node or Hardhat toolchain is justified. The repository currently contains no
Solidity build configuration, package manifest, or Solidity CI path; adding a
small Foundry boundary avoids imposing a second JavaScript dependency graph on
the Vyper repository.

### Reproducibility pins

The implementation specification should lock, not float:

- the exact Foundry release (the local research environment currently reports
  `forge 1.3.5-stable`, but the implementation phase must record and approve the
  project pin);
- an exact Solidity `0.8.24` patch compatible with the accepted CCIP release;
- `smartcontractkit/chainlink-ccip` at the accepted exact commit, provisionally
  `bbab0601244ce58e2ffac0dbc178a80aab1fa4a3`;
- `smartcontractkit/chainlink-evm` at its exact compatible commit,
  provisionally `e06cc226086ad91cfede63e96c63e5b3440c9801`;
- remappings and dependency lock state in version control.

New dependencies must not be installed until the owner approves implementation.

### Build artifacts and migration integration

Foundry should compile and test only the CCIP Solidity boundary. A deterministic
export step should record:

- contract ABI;
- creation bytecode and deployed bytecode;
- compiler version and full compiler settings;
- exact source/dependency revisions;
- build-info or standard JSON input/output needed for explorer verification;
- hashes for the normalized deployment artifacts.

Generated cache and broad `out/` contents should not become a competing
deployment record.

The existing Python migration runner should remain authoritative. A later,
narrow artifact loader can read the normalized Foundry artifact, ABI-encode the
constructor arguments, deploy through titanoboa's existing environment, and
record the address, ABI, source metadata, and transaction evidence in the
current manifest/migration-history format. This keeps sequencing, environment
selection, and deployment evidence in one system.

Explorer verification should use exact source and compiler settings on:

- BaseScan for Base/Base Sepolia; and
- the Robinhood Chain Blockscout explorers named in the chain documentation.

That work requires explicit Robinhood chain configuration rather than extending
the migration runner's current Base-specific assumptions implicitly.

### Test and CI boundary

The implementation acceptance suite should include:

- unit tests for the single correct capability view on each pool;
- inherited burn and mint paths with token balances and supply deltas;
- authorization failures before RipeHq registration and after permission
  removal;
- proof that the opposite mint capability is absent or false;
- ownership, token-admin, rate-limit-admin, allowlist, remote-pool, and
  remote-chain configuration tests;
- fuzz or invariant coverage for burn/mint supply conservation;
- gas measurement for the complete release/mint pool path against the 90,000
  combined allowance;
- an Anvil/titanoboa integration harness using the real Vyper token and RipeHq
  contracts rather than Solidity-only mocks;
- a negative architecture test showing that a separate adapter cannot replace
  the direct pool caller;
- two-chain testnet evidence in both directions for both tokens.

CI should add a path-scoped Foundry job for `solidity/ccip/**` and keep the
existing Python test suite intact. Cross-runtime tests should run serially if
they share chain state. Production deployment is not a CI action.

## Alternatives considered

| Alternative | Decision | Reason |
| --- | --- | --- |
| Thin subclass of `BurnMintTokenPool` | Candidate | Smallest behavioral delta; needs confirmation that the inherited type/version and custom subclass are acceptable |
| Custom pool inheriting `BurnMintTokenPoolAbstract` | Candidate | Matches public custom-pool guidance; creates a clearer custom type but owns more implementation surface |
| Separate Ripe mint adapter | Rejected | Adapter becomes the token mint caller, violating the direct-pool authorization requirement |
| `BurnFromMintTokenPool` | Rejected | GREEN and RIPE do not implement `burnFrom` |
| Lock/release pool | Rejected | Adds custody and liquidity management without solving a token-interface constraint |
| Wrapped assets | Rejected | Changes the user-facing asset model and is unnecessary |
| Hardhat/Node toolchain | Rejected | Adds a broad second dependency ecosystem for two small Solidity contracts |
| Rewrite deployment orchestration in Solidity | Rejected | Would duplicate the repository's manifest and migration authority |

## Governance and operational model

The intended production role separation is:

1. a two-step multisig owns each token pool and controls remote configuration;
2. a token-administrator multisig controls Token Admin Registry association;
3. a separate incident multisig holds `rateLimitAdmin` with no broader pool
   ownership;
4. existing Ripe governance registers each pool in RipeHq and enables only the
   matching mint permission;
5. deployer and setup EOAs surrender temporary privileges after verified role
   transfer.

The final signer matrix, delay policy, role-transfer order, rate-limit values,
monitoring, manual-execution coverage, and emergency response require
authoritative review before any governance or deployment transaction is
prepared.

## Required follow-on sequence

After Chainlink responds and the owner accepts the final design:

1. freeze the accepted version, compiler, dependency, registration, and role
   decisions in an implementation specification;
2. receive explicit approval to install pinned dependencies and implement the
   Foundry boundary;
3. implement and run unit, invariant, cross-runtime, and gas tests;
4. obtain any required audit or Chainlink review;
5. prepare a separate testnet transaction packet with exact addresses,
   constructor arguments, role assignments, rate limits, and rollback steps;
6. receive explicit approval before each deployment/registration transaction
   set;
7. validate both tokens in both directions on testnet and retain explorer,
   event, balance, supply, and CCIP message evidence;
8. return to an owner gate before any mainnet transaction or external terms
   acceptance.

Nothing in this decision record authorizes a later step.

## Unresolved decision fields

- final supported pool release, commit, compiler patch, and dependency graph;
- compatibility of a `1.6.1` pool with the live `1.6.0` lane;
- preferred thin-pool inheritance pattern and type/version string;
- Chainlink review, audit, and production-support requirements;
- assisted registration evidence and timing for both immutable Base tokens;
- whether Robinhood tokens remain bytecode-equivalent or add an admin hook;
- exact role-transfer and configuration ordering;
- recommended initial limits and true emergency-stop design;
- monitoring, manual-execution, upgrade, support, and incident responsibilities;
- onboarding, recurring, commercial, SLA, security, and terms requirements.

## Current approval gate

The owner may now review the three Track 1 artifacts and request edits. To
contact Chainlink, the next approval must explicitly identify and approve:

- the exact outbound text;
- the recipient or form;
- the channel; and
- the act of sending.

That approval would not cover terms acceptance, dependency installation,
contract implementation, role changes, deployments, or transaction broadcast.

## Track 1 checklist items eligible for owner review

Without editing `docs/chains/rh-summary.md`, the following work is ready for
owner review:

- public direct-lane and network-contract evidence;
- Ripe token and RipeHq direct-caller compatibility evidence;
- public registration-path evidence and immutable-token constraint;
- custom-pool architecture evidence and unresolved review question;
- operational, rate-limit, gas, upgrade, billing, and responsibility baseline;
- complete draft Chainlink question packet;
- Foundry toolchain and existing-migration integration recommendation;
- conditional architecture and governance decision record.

Items requiring an authoritative Chainlink response remain open: supported
custom-pool form and version, assisted-registration procedure, external review
requirements, fees/commercial terms, and service/support commitments.
