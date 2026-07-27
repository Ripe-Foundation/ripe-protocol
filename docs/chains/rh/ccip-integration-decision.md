# Robinhood Chain CCIP integration decision

Status: **Conditional draft — external confirmation and owner approval required**

Decision date: 2026-07-23

Last revised: 2026-07-27

Scope: GREEN and RIPE on Base <-> Robinhood Chain

Current gate: Pure-Vyper reference and revised technical packet are ready for
owner review; implementation, external contact, and deployment remain gated

## Decision

Proceed conditionally with the minimal direct burn/mint bridge design as the
Track 1 working architecture. Do not begin implementation, install new
dependencies, register tokens, deploy contracts, accept external terms, or
broadcast transactions until the blocking Chainlink answers are received and
the owner approves the next phase.

Public evidence establishes the lane and a viable technical shape, but not
Chainlink's acceptance of a from-scratch pure-Vyper pool, the supported
production pool/version combination, the assisted-registration procedure, or
the final gas/audit requirements. This is therefore a conditional go for
design preparation, not authorization to deploy.

## Selected architecture

- Use a direct CCIP burn/mint topology.
- Implement the pools in pure Vyper. Maintain one GREEN pool implementation
  across Base and Robinhood Chain and one RIPE pool implementation across both
  chains.
- Preserve Chainlink's standard direct calls to `burn(uint256)` and
  `mint(address,uint256)`.
- The GREEN pool returns true only from `canMintGreen()`; the RIPE pool returns
  true only from `canMintRipe()`.
- Reproduce the Chainlink v1.6.1 execution and administration ABI needed for
  the lane, including standard chain/pool lifecycle, optional allowlist mode,
  rate-limit state preservation, monitoring events, and diagnostic errors.
- Register each pool as a RipeHq department and enable only its matching mint
  permission.
- Use the direct public Base <-> Robinhood Chain lane and the direct Base
  Sepolia <-> Robinhood Chain Testnet lane.
- Start with conservative independent per-token, per-direction rate limits.
- Treat `RipeHq.setMintingEnabled(false)` as the immediate chain-local stop for
  all RipeHq-authorized issuance, token pause as the broader token-wide stop,
  and CCIP rate limits as velocity controls. The final incident order and
  in-flight recovery procedure remain pending Chainlink confirmation and test
  evidence.

A separate registered mint adapter is technically possible: RipeHq would
authorize the adapter because it becomes the direct `msg.sender` of
`token.mint()`. It is rejected because it inserts another mint-critical
contract and trust boundary between the CCIP pool and token without solving a
token-interface problem. A wrapping topology is rejected because it changes
the asset model and is unnecessary when the native tokens already satisfy the
burn/mint interface.

### Reviewed pure-Vyper reference

[`examples/ExampleGreenCcipBurnMintPool.vy`](examples/ExampleGreenCcipBurnMintPool.vy)
is the current reference, not a deployable production contract. It compiles
with Vyper `0.4.3` and an explicit `shanghai` EVM target and now demonstrates:

- the exact CCIP v1 pool execution selectors and interface IDs;
- standard v1.6.1 chain, remote-pool, rate-limit, allowlist, Router, and
  rate-limit-admin selectors;
- complete chain removal and enumerable chain/pool state;
- rate-limit reconfiguration that preserves consumed capacity;
- refreshed Chainlink-shaped bucket getters;
- Chainlink-shaped execution/configuration events and diagnostic custom
  errors;
- an optional deployment-time allowlist mode; and
- cancellable two-step ownership.

Its Vyper bounds are part of compatibility, not invisible implementation
details: at most eight configured remote chains, eight pools per chain, 256
allowlisted senders, 64-byte remote address/pool metadata, 64-byte source pool
data, and 2,048-byte offchain token data. Those values cover the selected
EVM-to-EVM address and decimals encodings but must be frozen and tested against
the accepted lane before production.

The reference deliberately does not claim Chainlink tooling/support
eligibility, audit inheritance, destination-gas compliance, production role
selection, or Department pause/recovery compatibility. Those remain hard
activation gates.

## Decision record

| Field | Current decision | Confidence / gate |
| --- | --- | --- |
| Production lane | Direct Base <-> Robinhood Chain | Confirmed by current public directory |
| Test lane | Direct Base Sepolia <-> Robinhood Chain Testnet | Confirmed by current public directory |
| Pool model | Pure-Vyper direct custom burn/mint pool; no adapter | Owner selected pure Vyper; adapter rejected on simplicity and attack-surface grounds |
| GREEN capability | GREEN pool exposes only `canMintGreen() -> true` | Exact-one-capability policy selected by Ripe; RipeHq checks the matching flag and view but not exclusivity |
| RIPE capability | RIPE pool exposes only `canMintRipe() -> true` | Exact-one-capability policy selected by Ripe; RipeHq checks the matching flag and view but not exclusivity |
| Solidity inheritance | None | Pure-Vyper owner decision; the pool must reimplement and verify the selected Chainlink behavior |
| Candidate CCIP pin | `1.6.1` commit `bbab0601244ce58e2ffac0dbc178a80aab1fa4a3` | Provisional; compatibility confirmation required |
| Candidate Chainlink EVM oracle pin | `e06cc226086ad91cfede63e96c63e5b3440c9801` | Provisional differential-reference pin, not a Vyper build dependency |
| Compiler | Vyper `0.4.3` | Matches the repository pin; do not change without separate dependency review |
| EVM target | `shanghai` in the reference example | Explicit conservative pin; Base and Robinhood runtime compatibility still require live/fork proof |
| Base token registration | Assisted/manual for immutable tokens | Public path identified; process confirmation required |
| Robinhood token registration | Prefer unchanged token source and assisted registration | Conditional; a required admin hook triggers an owner choice between the shared-source default and a narrow pre-deployment Robinhood exception |
| Pool owner | Two-step owner-approved production multisig | Required security posture; exact backend/signers and supported transition pending |
| Token administrator | Owner-approved production multisig | Proposed; do not assume Safe support on Robinhood |
| Rate-limit administrator | Separate narrowly scoped incident multisig | Proposed; operational confirmation pending |
| RipeHq authority | Existing Ripe governance | Required for department registration and matching mint flag |
| Global mint circuit breaker | Immediate governance call to `RipeHq.setMintingEnabled(false)` | Stops every RipeHq-authorized GREEN and RIPE mint on that chain; CCIP retry behavior must be confirmed |
| Token pause/blacklist | Pause stops transfer, burn, and mint; blacklist can reject source or receiver | Verified in Ripe code; CCIP failure recovery must be tested |
| Department lifecycle surface | Capability views required; reference omits `pause`/recovery | Production choice remains an explicit owner/security decision |
| Ripe registration schedule | Deploy pool, timelocked address registration, then timelocked Hq config | Verified in Ripe code; Robinhood block semantics must be tested |
| Initial limits | Conservative nonzero caps, separately configured by token and direction | Quantitative recommendation pending |
| Implementation toolchain | Existing pinned Vyper/titanoboa workflow | Selected by owner; artifact/export/deployment support still requires implementation |

## Toolchain decision

### Selected boundary

Use the repository's existing Vyper `0.4.3`, titanoboa, pytest, Python
migration, and manifest workflow. Do not add Foundry, Solidity, Node, or
Hardhat merely for the CCIP pools. The pure-Vyper selection avoids a second
compiler/dependency stack, but it also means no Chainlink Solidity audit
coverage transfers to the implementation.

### Reproducibility pins

The implementation specification must lock:

- Vyper `0.4.3` and the repository's existing titanoboa dependency;
- an explicit EVM version after Base and Robinhood compatibility checks (the
  reference uses `shanghai` so a compiler-default change cannot silently add
  newer opcodes);
- the Chainlink contract/API baseline used for differential tests,
  provisionally contracts-CCIP `1.6.1` commit
  `bbab0601244ce58e2ffac0dbc178a80aab1fa4a3`; and
- every bounded Vyper ABI limit, including remote-chain, remote-pool,
  allowlist, and dynamic-bytes ceilings.

### Build artifacts and migration integration

A deterministic Vyper export step should record:

- contract ABI;
- creation bytecode and deployed bytecode;
- Vyper version, EVM target, optimization settings, and source hash;
- the exact Chainlink reference revisions used for parity verification;
- compiler output needed for BaseScan and Robinhood explorer verification;
- hashes for the normalized deployment artifacts.

Generated compiler caches must not become a competing deployment record. The
existing Python migration runner remains authoritative and must record the
constructor arguments, address, ABI, compiler settings, source metadata, and
transaction evidence in the current manifest/migration-history format.

Explorer verification should use exact source and compiler settings on:

- BaseScan for Base/Base Sepolia; and
- the Robinhood Chain Blockscout explorers named in the chain documentation.

That work requires explicit Robinhood chain configuration rather than extending
the migration runner's current Base-specific assumptions implicitly.

### Test and CI boundary

The implementation acceptance suite must include:

- unit tests for the single correct capability view on each pool;
- burn and mint paths with token balances and supply deltas;
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
- exact selectors for the standard v1.6.1 execution and administration ABI;
- exact event parameter types/indexing and security/rate-limit custom-error
  encodings;
- complete chain removal, remote-pool enumeration, and no-stale-approval tests;
- proof that rate-limit reconfiguration refills at the old rate and clamps to
  the new capacity rather than resetting full;
- Vyper dynamic-bytes bound tests against the intended EVM-to-EVM peer format;
- fuzz or invariant coverage for burn/mint supply conservation;
- gas measurement for the complete release/mint pool path against the 90,000
  combined allowance;
- a titanoboa/fork integration harness using the real Vyper token and RipeHq
  contracts plus the actual Router/OffRamp/RMN proxy where feasible;
- a threat-model comparison with the rejected extra-adapter topology;
- differential tests against the pinned Solidity TokenPool behavior;
- two-chain testnet evidence in both directions for both tokens.

CI should add path-scoped Vyper/pytest jobs for the CCIP pool files and keep the
existing suite intact. State-sharing integration tests should run serially.
Production deployment is not a CI action.

## Alternatives considered

| Alternative | Decision | Reason |
| --- | --- | --- |
| Pure-Vyper v1.6.1-shaped pool | Selected | Owner preference and repository consistency; accepts the larger audit, differential-test, and version-tracking burden |
| Thin subclass of `BurnMintTokenPool` | Rejected by owner preference | Smallest behavioral delta and strongest inherited parity, but adds a Solidity toolchain boundary |
| Custom pool inheriting `BurnMintTokenPoolAbstract` | Rejected by owner preference | Still adds Solidity and owns more behavior than the thin-subclass alternative |
| Separate Ripe mint adapter | Rejected | Technically viable if separately registered in RipeHq, but adds a mint-critical trust boundary with no compensating benefit |
| `BurnFromMintTokenPool` | Rejected | GREEN and RIPE do not implement `burnFrom` |
| Lock/release pool | Rejected | Adds custody and liquidity management without solving a token-interface constraint |
| Wrapped assets | Rejected | Changes the user-facing asset model and is unnecessary |
| Foundry or Hardhat toolchain | Rejected for the selected design | Unnecessary for pure-Vyper pools |
| Rewrite deployment orchestration in Solidity | Rejected | Would duplicate the repository's manifest and migration authority |

## Department lifecycle compatibility

`interfaces/Department.vyi` declares `isPaused()`, `pause(bool)`, and recovery
functions in addition to the mint capability views. RipeHq registration does
not enforce that whole interface: it validates only a capability when the
matching mint flag is enabled. `SwitchboardCharlie.pause(address,bool)` is a
generic targeted call rather than an automatic registry sweep, but it will
revert if the selected pool lacks `pause(bool)`.

The reviewed reference example makes the omission explicit: it is
capability-only and does not claim to implement the full Department interface.
That is not yet a production decision. The implementation specification must
choose and test one of:

1. add a Chainlink-approved lifecycle surface that gates the standard pool
   paths without changing accounting or recovery invariants; or
2. keep the pool capability-only, explicitly exclude it from
   SwitchboardCharlie pause operations, and rely on the RipeHq mint circuit
   breaker, token pause, and CCIP rate controls.

The first option expands custom code and review scope. The second leaves no
pool-local true pause and makes a generic
`SwitchboardCharlie.pause(pool, ...)` call revert. The minimum-change
recommendation is option 2, backed by chain removal, rate limits,
`RipeHq.setMintingEnabled(false)`, and token pause; the owner/security review
must accept that residual blast-radius tradeoff before production.

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

Pool ownership is mint-critical, not ordinary maintenance authority. The owner
can replace the Router and rate-limit configuration; a malicious replacement
Router can nominate attacker-controlled ramps and reach the pool's RipeHq mint
permission. The owner role therefore requires at least the same governance
quality, delay, monitoring, and signer hygiene as other protocol-solvency
roles. No production Safe or other backend is assumed until Robinhood support
is proven and the owner approves it.

The incident-control hierarchy is:

1. call `RipeHq.setMintingEnabled(false)` for an immediate stop to every
   RipeHq-authorized GREEN and RIPE mint on that chain;
2. pause the affected token only when a broader stop to transfers, outbound
   burns, and inbound mints is justified;
3. reduce both lane-direction rate limits to Chainlink's documented emergency
   values to minimize velocity; and
4. monitor failed and in-flight messages, then use only the confirmed retry or
   manual-execution path after recovery.

Step 1 is protocol-wide issuance control, not a bridge-local switch. It also
halts fresh GREEN or RIPE issuance through native paths such as CreditEngine
borrowing, EndaomentPSM issuance, and Lootbox rewards, plus every other
Department routed through the same RipeHq checks. Because that blast radius is
larger than the CCIP incident itself, the final runbook must define who may
invoke each control, escalation thresholds, cross-chain coordination, and
re-enable sequencing.

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

If Chainlink makes `getCCIPAdmin()` or another token change unavoidable, the
standing shared-source policy defaults to a new chain-portable token revision.
Because the Robinhood tokens are not yet deployed, an asymmetric
Robinhood-only admin hook is also technically possible and may be the smallest
production-contract change. It would be an explicit exception to that policy,
not an implementation detail. The owner must choose among:

1. a shared revision plus separately authorized Base migration;
2. a shared revision with bounded deployed-version drift and an approved
   convergence plan;
3. a shared revision with an explicitly approved permanent Base live-bytecode
   exception; or
4. a narrowly scoped Robinhood-only pre-deployment admin-hook exception.

This is a Track 1 stop condition. No Base migration or Robinhood token-source
change follows implicitly from a Chainlink answer.

## Required follow-on sequence

After Chainlink responds and the owner accepts the final design:

1. freeze the accepted version, compiler, dependency, registration, and role
   decisions in an implementation specification;
2. implement the production pure-Vyper pool from the reviewed reference only
   after explicit implementation authority;
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

- final supported Chainlink pool/API baseline and exact source commit;
- compatibility of a `1.6.1` pool with the live `1.6.0` lane;
- Chainlink eligibility, review, audit, and production-support requirements
  for a non-Chainlink-derived pure-Vyper pool;
- exact production `typeAndVersion` string and bounded Vyper ABI limits;
- Base and Robinhood EVM-version compatibility evidence;
- measured destination execution gas and required margin/configuration;
- assisted registration evidence and timing for both immutable Base tokens;
- whether Robinhood tokens remain bytecode-equivalent or add an admin hook;
- exact role-transfer and configuration ordering;
- accepted Department pause/recovery surface;
- recommended initial limits, incident-control order, and in-flight retry
  behavior under RipeHq mint disable, token pause, and blacklist;
- Robinhood registry timelock value and repeated/jumping-block acceptance;
- monitoring, manual-execution, upgrade, and incident responsibilities.

## Current approval gate

The 2026-07-23 packet approval no longer applies because the packet has been
materially shortened and revised for the pure-Vyper decision. The revised
technical text requires fresh owner approval. No agent is authorized to contact
Chainlink. If delivery is later approved and occurs, the record must capture:

- the exact outbound text;
- the recipient or form;
- the channel; and
- the delivery date and sender.

Text approval does not cover terms acceptance, dependency installation,
contract implementation, role changes, deployments, or transaction broadcast.

## Exact `rh-summary.md` checklist mapping

No checkbox completion state in `docs/chains/rh-summary.md` was changed; its
CCIP wording was updated to record the pure-Vyper decision and reviewer
corrections. The section 0 items now map as follows:

| Exact checklist item | Review / closure status |
| --- | --- |
| “Pin the supported CCIP contracts release and decide how its Vyper contracts and artifacts will be built, tested, and deployed from this Vyper repository.” | The pure-Vyper toolchain boundary is selected; the checkbox is not ready for closure because the Chainlink reference pin, custom-pool eligibility, and EVM/gas evidence remain provisional. |
| “Prefer Chainlink-assisted registration so Robinhood can deploy the same existing GREEN and RIPE token implementations without adding a Robinhood-only `getCCIPAdmin()` change.” | Public evidence supports this preference; it is eligible for owner review and closure as the selected policy. |
| “Confirm the supported registration path with Chainlink. If `getCCIPAdmin()` is unavoidable, design it as part of a new shared token revision usable on every chain and explicitly resolve the resulting Base migration, temporary live-version mismatch, or permanently accepted live divergence for the immutable Base tokens.” | Question packet and authority evidence are ready for owner review; the checkbox is not eligible for closure until an authoritative Chainlink response is captured. |

The section 2 item “Confirm that RipeHq and registry timelocks behave correctly
before using them to register CCIP pools as Departments” is now an explicit
follow-on dependency, but it is not eligible for closure until both Base and
Robinhood clock-profile tests pass.

The Phase A direct-lane/address evidence, Ripe interface proof, operational
baseline, revised technical packet, and pure-Vyper toolchain decision are ready
for owner review. Custom-pool eligibility/version, assisted-registration
procedure, Department lifecycle surface, gas budget, and external
review/support requirements remain open.
