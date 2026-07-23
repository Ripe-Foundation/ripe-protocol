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
- Treat `RipeHq.setMintingEnabled(false)` as the immediate chain-local inbound
  mint stop, token pause as the broader token-wide stop, and CCIP rate limits as
  velocity controls. The final incident order and in-flight recovery procedure
  remain pending Chainlink confirmation and test evidence.

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
| Inbound mint circuit breaker | Immediate governance call to `RipeHq.setMintingEnabled(false)` | Verified in Ripe code; retry behavior must be confirmed |
| Token pause/blacklist | Pause stops transfer, burn, and mint; blacklist can reject source or receiver | Verified in Ripe code; CCIP failure recovery must be tested |
| Department lifecycle surface | Capability views required; `pause`/recovery surface undecided | Chainlink compatibility answer required |
| Ripe registration schedule | Deploy pool, timelocked address registration, then timelocked Hq config | Verified in Ripe code; Robinhood block semantics must be tested |
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
    GreenTokenBurnMintPool.sol
    RipeTokenBurnMintPool.sol
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
- immediate inbound failure under `mintEnabled == false`, followed by the
  accepted re-enable/retry path;
- source and destination token-pause failures, blacklisted sender/receiver
  failures, and recovery after the blocking condition is removed;
- proof that the opposite mint capability is absent or false;
- the accepted Department lifecycle decision: either pool pause/recovery
  behavior or proof that those selectors are intentionally absent and
  Switchboard targeting fails as documented;
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

## Department lifecycle compatibility

`interfaces/Department.vyi` declares `isPaused()`, `pause(bool)`, and recovery
functions in addition to the mint capability views. RipeHq registration does
not enforce that whole interface: it validates only a capability when the
matching mint flag is enabled. `SwitchboardCharlie.pause(address,bool)` is a
generic targeted call rather than an automatic registry sweep, but it will
revert if the selected pool lacks `pause(bool)`.

The current decision is **pending Chainlink response**, not an assumption that
the full Department surface is required. The implementation specification must
choose and test one of:

1. add a Chainlink-approved lifecycle surface that gates the standard pool
   paths without changing accounting or recovery invariants; or
2. keep the pool capability-only, explicitly exclude it from
   SwitchboardCharlie pause operations, and rely on the RipeHq mint circuit
   breaker, token pause, and CCIP rate controls.

The first option expands custom code and review scope. The second leaves no
pool-local true pause. Neither option may be selected silently.

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

The incident-control hierarchy is:

1. set `RipeHq.mintEnabled` false for an immediate stop to all inbound GREEN and
   RIPE mints on that chain;
2. pause the affected token only when a broader stop to transfers, outbound
   burns, and inbound mints is justified;
3. reduce both lane-direction rate limits to Chainlink's documented emergency
   values to minimize velocity; and
4. monitor failed and in-flight messages, then use only the confirmed retry or
   manual-execution path after recovery.

Because step 1 affects both tokens and step 2 affects all token activity, the
final runbook must define who may invoke each control, escalation thresholds,
cross-chain coordination, and re-enable sequencing.

The final signer matrix, delay policy, role-transfer order, rate-limit values,
monitoring, manual-execution coverage, and emergency response require
authoritative review before any governance or deployment transaction is
prepared.

## Ripe sequencing and block-number constraints

Ripe-side pool authorization cannot be collapsed into one transaction:

1. deploy the pool with its intended capability view already live;
2. governance calls `startAddNewAddressToRegistry`;
3. after `registryChangeTimeLock`, governance calls
   `confirmNewAddressToRegistry` and receives the pool's registry ID;
4. governance calls `initiateHqConfigChange` with only the matching mint flag;
5. after another `registryChangeTimeLock`, governance calls
   `confirmHqConfigChange`; and
6. confirmation re-validates by staticcalling the pool capability and clears
   rather than applies an invalid pending config.

The pool must therefore be deployed before even initiating the Hq config, and
its capability must remain callable at both initiation and confirmation.
Both waits are measured in `block.number`. Before using them on Robinhood,
the `rh-summary.md` section 2 clock work must approve a Robinhood value and test
repeated, delayed, and jumping L1-estimate block numbers. Chainlink can advise
where its registration steps fit around this sequence, but cannot resolve these
Ripe timing semantics.

## Live-version implications for immutable Base tokens

The selected path leaves the existing Base GREEN and RIPE bytecode unchanged
and seeks assisted registration on both chains using the same canonical token
source. That avoids a live-version exception.

If Chainlink makes `getCCIPAdmin()` or another token change unavoidable, it must
be designed as a new shared, chain-portable token revision rather than a
Robinhood-only variant. Because the current Base deployments are immutable for
this purpose, that outcome triggers the `rh-summary.md` live-version policy:
the owner must separately choose Base token migration, bounded temporary
deployed-version drift with convergence, or an explicitly approved permanent
live-bytecode exception. It is a Track 1 stop condition, not an implementation
detail.

## Required follow-on sequence

After Chainlink responds and the owner accepts the final design:

1. freeze the accepted version, compiler, dependency, registration, and role
   decisions in an implementation specification;
2. receive explicit approval to install pinned dependencies and implement the
   Foundry boundary;
3. implement and run unit, invariant, cross-runtime, and gas tests;
4. obtain any required audit or Chainlink review;
5. deploy the test pools before preparing either RipeHq registration sequence,
   then prove the capability selectors are live;
6. prepare a separate testnet transaction packet with exact addresses,
   constructor arguments, role assignments, rate limits, and rollback steps;
7. include two separately timed Ripe governance stages per pool—address
   registration followed by Hq config—and the approved Robinhood
   `block.number` timing assumptions;
8. receive explicit approval before each deployment/registration transaction
   set;
9. validate both tokens in both directions, circuit-breaker and token
   pause/blacklist failures, in-flight recovery, and the Department lifecycle
   decision on testnet; retain explorer, event, balance, supply, gas, and CCIP
   message evidence;
10. return to an owner gate before any mainnet transaction or external terms
   acceptance.

Nothing in this decision record authorizes a later step.

When an authoritative response is received, preserve it with date, sender,
channel, full text or exact durable summary, and source links in:

`docs/chains/rh/ccip-chainlink-response-record.md`

## Unresolved decision fields

- final supported pool release, commit, compiler patch, and dependency graph;
- compatibility of a `1.6.1` pool with the live `1.6.0` lane;
- preferred thin-pool inheritance pattern and type/version string;
- Chainlink review, audit, and production-support requirements;
- assisted registration evidence and timing for both immutable Base tokens;
- whether Robinhood tokens remain bytecode-equivalent or add an admin hook;
- exact role-transfer and configuration ordering;
- accepted Department pause/recovery surface;
- recommended initial limits, incident-control order, and in-flight retry
  behavior under RipeHq mint disable, token pause, and blacklist;
- Robinhood registry timelock value and repeated/jumping-block acceptance;
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

## Exact `rh-summary.md` checklist mapping

No checkbox in `docs/chains/rh-summary.md` was edited. The exact section 0 items
now map as follows:

| Exact checklist item | Review / closure status |
| --- | --- |
| “Pin the supported CCIP contracts release and decide how its Solidity contracts and artifacts will be built, tested, and deployed from this currently Vyper-focused repository.” | Toolchain boundary is ready for owner review; the checkbox is not ready for full closure because the `1.6.1` release pin remains provisional pending Chainlink compatibility confirmation. |
| “Prefer Chainlink-assisted registration so Robinhood can deploy the same existing GREEN and RIPE token implementations without adding a Robinhood-only `getCCIPAdmin()` change.” | Public evidence supports this preference; it is eligible for owner review and closure as the selected policy. |
| “Confirm the supported registration path with Chainlink. If `getCCIPAdmin()` is unavoidable, design it as part of a new shared token revision usable on every chain and explicitly resolve the resulting Base migration, temporary live-version mismatch, or permanently accepted live divergence for the immutable Base tokens.” | Question packet and authority evidence are ready for owner review; the checkbox is not eligible for closure until an authoritative Chainlink response is captured. |

The section 2 item “Confirm that RipeHq and registry timelocks behave correctly
before using them to register CCIP pools as Departments” is now an explicit
follow-on dependency, but it is not eligible for closure until both Base and
Robinhood clock-profile tests pass.

The Phase A direct-lane/address evidence, Ripe interface proof, operational
baseline, complete question packet, and Foundry recommendation are otherwise
ready for owner review. Supported custom-pool form and version,
assisted-registration procedure, Department lifecycle surface, external review
requirements, fees/commercial terms, and service/support commitments remain
open.
