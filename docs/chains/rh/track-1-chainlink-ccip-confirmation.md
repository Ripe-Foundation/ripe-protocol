# Track 1: Chainlink CCIP Confirmation

**Status:** Draft for owner review

**Prepared:** 23 July 2026

**Planning baseline:** `1bb8bd5b8837a06c818c3fb9e7b599b5dd29f2b1`

## Fresh-agent instruction

Treat this document as the task contract. Work only within the scope below. Verify all time-sensitive Chainlink and Robinhood facts against current primary sources, distinguish public evidence from answers supplied privately by Chainlink, and stop at every approval gate.

Do not contact Chainlink, submit a form, send a message, agree to commercial terms, or broadcast a transaction without explicit owner authorization. Do not implement the production pool or modify GREEN, RIPE, or RipeHq during this track.

For a new independent Track 1 execution, use a dedicated branch or worktree
named `rh-track-1-chainlink-ccip`. Do not edit `docs/chains/rh-summary.md` or
files owned by the other Robinhood tracks. Commit deliverables to the track
branch with clear messages; never push directly to or merge into the shared
`rh` or `master` branch. The owner reviews and integrates the work.

The owner integrated the pure-Vyper reference package on `rh` in commit
`8147784a` and separately directed the 2026-07-27 thin-Solidity architecture
and cross-document correction pass in the integration worktree. That was
one-time task authority, not a reusable maintenance exception. Future work
must follow this track's branch/file rules or receive new explicit owner
authority. Nothing here authorizes a commit, push, merge, deployment, external
contact, or transaction.

## Worktree bootstrap

The owner must commit the approved track briefs to the `rh` integration branch before kickoff. The fresh agent is responsible for creating its own worktree:

1. Start from `/Users/wigglez/dev/ripe-protocol`.
2. Verify that the integration worktree is clean, `rh` resolves to the approved integration commit, and this brief exists in that commit.
3. Confirm that branch `rh-track-1-chainlink-ccip` and path `/Users/wigglez/dev/ripe-protocol-track-1-chainlink-ccip` do not already exist. If either exists, stop and ask the owner; do not reuse, delete, reset, or overwrite it.
4. Create the isolated worktree from the committed `rh` baseline:

   ```bash
   git -C /Users/wigglez/dev/ripe-protocol worktree add \
     -b rh-track-1-chainlink-ccip \
     /Users/wigglez/dev/ripe-protocol-track-1-chainlink-ccip \
     rh
   ```

5. Verify the new worktree's branch, commit, and clean status. Record the full starting commit in the deliverables.
6. Run every subsequent command and make every edit inside `/Users/wigglez/dev/ripe-protocol-track-1-chainlink-ccip`.

For a new isolated Track 1 run, do not modify or commit from the integration
worktree. Leave the track worktree and branch in place for owner review; do not
remove or merge them yourself.

## Objective

Remove the external and architectural uncertainty around registering GREEN and RIPE as Chainlink Cross-Chain Tokens between Base and Robinhood.

The track must produce:

1. a source-verified public technical baseline;
2. a concise, ready-to-send Chainlink question packet;
3. a written response record when answers are received; and
4. a recommended integration decision that is specific enough to authorize the later CCIP implementation specification.

This track does not build the bridge. It determines the supported path the bridge implementation must follow.

## Controlling constraints

- Follow [`../rh-summary.md`](../rh-summary.md), which selects chain-local Ripe deployments and bridges only GREEN and RIPE.
- Preserve one canonical, chain-portable Ripe contract source as the default.
  A Robinhood-only GREEN/RIPE admin hook is technically possible before those
  tokens deploy, but it is a stop-and-owner-decision exception rather than a
  change this track may select implicitly. Do not propose Robinhood-only
  RipeHq or pool behavior.
- Prefer assisted registration of the immutable Base GREEN and RIPE tokens.
- Add `getCCIPAdmin()` only if Chainlink confirms that it is required and assisted registration is unavailable or inappropriate.
- The Ripe-compatible pool must remain the direct caller of `GreenToken.mint()` or `RipeToken.mint()`.
- Both pools retain both capability views. The GREEN pool returns true only
  from `canMintGreen()` and false from `canMintRipe()`; the RIPE pool returns
  false from `canMintGreen()` and true only from `canMintRipe()`.
- Use one shared GREEN pool implementation on both chains and one shared RIPE pool implementation on both chains. Network addresses and permissions belong in configuration.
- Implement each selected pool as a thin Solidity subclass of Chainlink's
  concrete `BurnMintTokenPool`. Add only the standard constructor pass-through
  and the two Ripe capability views; do not add storage or override CCIP
  behavior.
- CCIP is the sole active minting bridge.

## Required repository reading

Read and verify the current versions of:

- `docs/chains/rh-summary.md`
- `contracts/registries/RipeHq.vy`
- `contracts/registries/modules/AddressRegistry.vy`
- `contracts/tokens/GreenToken.vy`
- `contracts/tokens/RipeToken.vy`
- `contracts/tokens/modules/Erc20Token.vy`
- `contracts/mock/MockDepartment.vy`
- `tests/registries/test_ripe_hq.py`
- `tests/tokens/test_erc20.py`
- `scripts/migrate.py`
- `scripts/utils/migration.py`
- `scripts/utils/migration_runner.py`
- the selected architecture at `/Users/wigglez/dev/hightop-notes/random/hood/hood-chain-executive-summary.md`

If the local Hightop Notes checkout is unavailable, use the [GitHub copy](https://github.com/mickhagen/hightop-notes/blob/main/random/hood/hood-chain-executive-summary.md). If neither source is accessible, stop rather than silently skipping the required architecture.

Record the actual starting commit. If contract code has changed since the planning baseline, describe the relevant delta before continuing.

## Phase A: Verify the public technical baseline

- [ ] Confirm current CCIP support for Base and Robinhood mainnet and the relevant test networks.
- [ ] Confirm whether a direct Base-to-Robinhood lane exists for each required environment; do not infer a lane merely from both chains being supported independently.
- [ ] Pin the currently supported CCIP/CCT contract release and official source repository.
- [ ] Record the official Router, Token Admin Registry, chain selector, OnRamp, OffRamp, and other required addresses from current Chainlink sources.
- [ ] Document every available registration path for:
  - existing immutable Base tokens without ordinary `owner()` or `getCCIPAdmin()` discovery; and
  - newly deployed Robinhood GREEN and RIPE tokens.
- [ ] Verify the required BurnMint token and pool interfaces against the current GREEN, RIPE, and RipeHq implementations.
- [ ] Confirm which burn signature the pinned pool implementation invokes—such as `burn(uint256)` or `burnFrom(address,uint256)`—and verify compatibility with GREEN and RIPE's current `burn(uint256)` self-burn behavior.
- [ ] Prove from current Ripe code why the selected design keeps the pool as the
  direct token-mint caller. Record that a separately registered adapter is
  technically possible but rejected for added attack surface and governance
  complexity.
- [ ] Identify any Chainlink review, allowlisting, audit, deployment, or
  operational requirements for a thin subclass of the concrete standard pool.
- [ ] Verify current rate-limit, manual-execution, ownership-transfer, pause, and recovery behavior relevant to the proposed design.
- [ ] Treat program availability, fees, service levels, feed availability, and deprecation terms as unconfirmed until supported by a current primary source or direct written answer.

Write the evidence to:

`docs/chains/rh/ccip-public-evidence.md`

Every time-sensitive claim must include a retrieval date and direct source. Clearly label inferences.

## Phase B: Produce the technical question packet

Create:

`docs/chains/rh/ccip-chainlink-question-packet.md`

The packet must be concise enough to send to a Chainlink technical contact while including the minimum code facts needed for an authoritative answer.

Ask only what cannot be answered from Ripe code or current public Chainlink
sources:

1. support for the two-view-only `BurnMintTokenPool` subclass, the pool/API
   version for the live `1.6.0` lanes, and confirmation that the directory RMN
   value is the constructor proxy;
2. the exact assisted Token Admin Registry process for unchanged tokens with no
   `owner()` or `getCCIPAdmin()`;
3. destination token-gas overhead, required margin, and the supported
   `TokenTransferFeeConfig.destGasOverhead`/FeeQuoter configuration path; and
4. failed-message retry/manual execution plus safe remote-pool retirement.

Include:

- exact Base GREEN and RIPE addresses;
- immutable/ownership facts verified from code and deployment evidence;
- the relevant `RipeHq`, `GreenToken`, and `RipeToken` call path;
- a minimal interface sketch for the proposed compatibility layer; and
- a decision table showing how each possible answer affects Ripe code.

### Approval gate

Stop after drafting the packet. Present it to the owner for review. Do not send it or initiate external contact without explicit authorization for the message, recipient, and channel.

## Phase C: Confirm the thin-Solidity toolchain boundary

Use a path-scoped, reproducible Foundry/Solidity build for the pool subclasses
while preserving the existing Python migration and manifest workflow as the
deployment authority. The owner-selected reference inherits
contracts-CCIP v1.6.1's concrete `BurnMintTokenPool` and adds no storage or
bridge override.

The recommendation must address:

- exact Chainlink dependency, Solidity compiler, EVM, optimizer, via-IR, and
  metadata pinning;
- reproducible builds;
- Solidity unit, ABI/storage-delta, invariant, fork, and integration tests;
- interaction with Vyper RipeHq and token deployments;
- ABI/artifact export;
- migration integration;
- explorer verification;
- CI impact; and
- proof that no storage or CCIP behavior differs from the pinned base;
- exact standard selectors, events, errors, lifecycle, and rate-limit
  inheritance;
- independent review scope because the standard-pool audit does not
  automatically cover the subclass, RipeHq integration, dependency pin, or
  deployment configuration; and
- destination gas measurement through the real RipeHq-authorized mint path.

Create `docs/chains/rh/ccip-integration-decision.md` during this phase rather than waiting for Chainlink's response. Record the toolchain recommendation immediately and leave explicit `pending Chainlink response` fields for unresolved external decisions. Do not install dependencies or modify the build until the recommendation is approved.

## Phase D: Capture authoritative answers

After the owner supplies or authorizes external responses:

- [ ] Preserve the full dated response or an exact durable summary with provenance.
- [ ] Separate confirmed answers from unanswered or conditional items.
- [ ] Re-verify any addresses or release versions named in the response.
- [ ] Identify contradictions between public documentation, the response, and Ripe's current implementation.
- [ ] Escalate any requirement that would force token migration, a
      Robinhood-only contract, nonstandard mint authority, or a second bridge.
      For a required Robinhood token admin hook, present both the shared-source
      default and the smaller pre-deployment exception; do not choose for the
      owner.

Do not silently resolve contradictory guidance.

## Final deliverable

Create during Phase C and finalize after authoritative answers are captured:

`docs/chains/rh/ccip-integration-decision.md`

It must record:

- supported networks and lanes;
- pinned CCIP release;
- Base token registration path;
- Robinhood token registration path;
- whether `getCCIPAdmin()` is required;
- accepted pool compatibility design;
- required contracts and administrative roles;
- selected thin-Solidity toolchain and Chainlink inheritance/delta boundary;
- unresolved external dependencies;
- live-version implications for immutable Base tokens;
- required follow-on implementation and test specifications; and
- an explicit `go`, `conditional go`, or `blocked` conclusion for the minimal bridge spike.

## Stop conditions

Stop and involve the owner if:

- external outreach or a commercial commitment is required;
- a current address, lane, or release cannot be verified;
- assisted registration is unavailable;
- Chainlink rejects or materially changes the thin-subclass design;
- a solution requires a Robinhood-only token or RipeHq implementation without
  the explicit owner policy decision described above;
- production GREEN or RIPE migration becomes necessary;
- two simultaneous minting bridges would exist; or
- the answer materially expands the architecture selected in `rh-summary.md`.

## Completion criteria

This track is complete only when:

- public evidence is reproducible and current;
- the owner-approved question packet has an authoritative response or every unanswered item is explicitly recorded;
- the registration, pool, toolchain, and live-version paths are decided or clearly blocked;
- no external action was taken without approval; and
- the final decision record is sufficient to write the CCIP implementation specification without rediscovering Phase-0 facts.

Do not mark any checkbox in `rh-summary.md` yourself. In the completion report, identify the exact checklist items that are now eligible for owner review and closure.
