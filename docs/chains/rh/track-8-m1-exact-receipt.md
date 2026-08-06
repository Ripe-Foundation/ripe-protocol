# Track 8 M1: Teller Exact-Receipt Boundary

**Status:** Draft for owner and independent review; M0 is integrated and
owner-closed; M1 implementation is not authorized

**Prepared:** 25 July 2026

**Planning baseline:** `cb3fe7392c44613aaeec49bd2486369fe0da3556`

**Integrated prerequisites:** H-01 at `575d47b82055b42da2bddf1535d8076cd7cf4c63`,
H-02 original integration at `6c3052668555a7104ea12a7fb1a7c641c7e6b304`,
reviewed H-02 correction at
`5c1ba54c5d34670ddba13ce84e46f490f8a8aaa4`, H-02 correction integration at
`cb3fe7392c44613aaeec49bd2486369fe0da3556`, Track 8 reviewed M0 decisions at
`c5c8b699b229792dc61e66af35502684ea3c8155`, final M0 closure at
`11824aa672809ad49ad7b2f823b9fb02c6e4608b`, and M0 integration at
`e1f14ddb030c5ce3f44d4cdd54e8c6daaad41369`

**Proposed branch:** `rh-track-8-m1-exact-receipt`

**Reconciliation note — 25 July 2026:** The planning baseline advanced from
`e1f14ddb030c5ce3f44d4cdd54e8c6daaad41369` to
`cb3fe7392c44613aaeec49bd2486369fe0da3556` through the reviewed H-02
post-integration correction. The incoming delta is exactly seven H-02-owned
configuration, migration/console, evidence, and deployment-test files. It
changes no M1-owned file, M0 controlling document, dependency lock, compiler
input, Teller/vault behavior, or M1 assumption. This reconciliation changes no
M1 decision or implementation recommendation.

## 1. Fresh-agent instruction

Treat this document as the complete task contract for Track 8 M1. Implement
only the smallest Teller-side exact-receipt boundary approved after the M0
evidence and product freeze.

The change must prove, for every existing Teller deposit route, that the
resolved custody address received exactly the post-validation transfer amount
in that call. It must prevent any pre-existing custody—including ordinary
backing supplied by another user—from masking a short receipt. It must reject
nested deposit measurement during the transfer-and-accounting window without
changing any public selector, event, persistent storage, vault source, credit
source, deployment file, or live Base contract.

This slice is not the Stock Token containment release. It proves only ML-01.
It does not implement the proposed `GuardedErc20` vault, CreditEngine
containment, unchanged-consumer composition proof, Robinhood deployment, or
activation. The complete Stock Token release remains:

```text
M1 + M2 + M3 + M4 proof + approved M5
```

Use a fresh worktree on branch `rh-track-8-m1-exact-receipt`. Do not reuse an
old branch or worktree. Do not push, merge, deploy, configure, sign, broadcast,
or begin M2-M5 unless a later instruction explicitly authorizes that action.

M1 has two mandatory independent reviewer gates:

1. **Gate 1 — implementation and security:** review the complete uncommitted
   source/test/evidence patch, exact-receipt arithmetic, raw balance-read
   boundary, transient-mutex behavior, route coverage, ABI/storage proofs,
   artifact hashes, and targeted test evidence.
2. **Gate 2 — merge readiness:** after Gate 1 findings are resolved and the
   exact approved bytes are committed, reconcile the then-current reviewed
   `rh` baseline without rebasing, rerun every required gate, and obtain final
   review of the complete branch before any push or integration.

The implementation author may not self-approve either gate. The owner remains
the only authority for the exact file authorization, local commit, push, and
merge.

## 2. Why this source change survives the minimum-change directive

The owner requires the fewest possible production-contract changes for the
Robinhood launch. M1 survives that stress test only for the following reason:

1. Stock Tokens are a mandatory launch requirement.
2. Current Teller logic transfers the post-validation amount and then asks the
   vault to infer a deposit from its aggregate post-transfer balance.
3. `BasicVault._depositTokensInVault` credits
   `min(Q, balanceOf(vault))`, where `balanceOf(vault)` is the aggregate
   custody of every user, not the current call's receipt. Once a vault already
   holds at least `Q` for user B, user A can deliver any short amount `R<Q`
   and still receive the full nominal credit `Q`. The missing `Q-R` is
   silently socialized against existing backing. No attacker-funded donation
   or special setup is required.
4. A donation or unrelated surplus is an additional masking variant. If
   nominal accounting before the call is `N`, prior surplus is `S`, and the
   requested validated transfer is `Q`, a token can deliver only `R=Q-S`
   while the vault still observes:

   ```text
   C1 = N + S + Q - S = N + Q
   ```

5. The vault cannot reconstruct the pre-transfer balance `C0` after Teller has
   already transferred. A vault-only check therefore cannot prove the
   call-local receipt.
6. Configuration can disable an asset or route, but cannot enforce that a
   successful enabled deposit received exactly `Q`.
7. Teller already owns the transfer boundary for ordinary, batched, trusted,
   rebalance, Teller-held, and governance-vault deposit routes.

The minimum sufficient production change is therefore one call-local
measurement in the shared Teller source. Broader containment remains in later,
separately authorized slices.

### 2.1 Alternatives considered

| Alternative | Production changes | Residual risk | M1 disposition |
| --- | ---: | --- | --- |
| Do nothing and trust configured tokens | None | Token upgrades, fees, burns, hooks, or unexpected transfer behavior can create nominal credit above the current receipt | Rejected for an enabled Stock route |
| Configuration-only allowlist | None | Admission is controlled, but exact receipt is not enforced at execution time | Necessary defense, not sufficient containment |
| Vault-only post-transfer check | Vault source | Existing users' aggregate custody or a donation can mask the current short receipt because the vault lacks `C0` | Rejected as insufficient |
| Pull custody from the vault | Teller and vault redesign | Broadens source, approval, callback, and allowance behavior | Rejected for the minimum slice |
| Prepare/finalize deposit protocol | Teller, vault, and interface changes | Adds selectors, cross-contract state, and migration surface | Rejected for the minimum slice |
| Teller call-local delta | Teller only | Exact-transfer-only policy rejects fee/rebase/short-receipt tokens; later slices still required | Selected minimum |

### 2.2 Risk accepted by keeping M1 small

M1 deliberately does **not**:

- make a deficit unusable for credit;
- guard internal nominal settlement;
- prove recipient delivery during auction or deleverage settlement;
- preserve repayment through a failed backing read;
- allocate donations or losses;
- create bad debt;
- harden the deployed Base Teller;
- deploy or register the Robinhood Teller; or
- make Stock Tokens safe to activate by itself.

Those limits must remain visible in every review and completion report. Passing
M1 tests is not permission to list, borrow against, liquidate, auction,
deleverage, deploy, or activate a Stock Token.

## 3. Controlling authorities

Read these complete files from the integrated baseline before doing any work:

1. this brief;
2. `docs/chains/rh/track-8-m0-owner-decision-packet.md`, especially Sections
   7-10;
3. `docs/chains/rh/stock-token-m0-evidence.md`, especially the caller/route and
   exact-transfer matrices;
4. `docs/chains/rh/stock-token-vault-change-specification.md`, especially
   Sections 23.1-23.11;
5. `docs/chains/rh/stock-token-vault-change-validation-plan.md`, especially
   Sections 20.6-20.10;
6. `docs/chains/rh/minimal-contract-change-reassessment.md`;
7. `docs/chains/rh/robinhood-deployment-support-specification.md`;
8. `docs/chains/rh/robinhood-deployment-validation-plan.md`;
9. `docs/chains/rh/evidence/dependency-security-gate.md`;
10. `contracts/core/Teller.vy`;
11. `contracts/core/TellerUtils.vy`;
12. `interfaces/Vault.vyi`;
13. `contracts/vaults/SimpleErc20.vy`;
14. `contracts/vaults/RebaseErc20.vy`;
15. `contracts/vaults/StabilityPool.vy`;
16. `contracts/vaults/RipeGov.vy`;
17. `contracts/vaults/modules/BasicVault.vy`;
18. `contracts/vaults/modules/SharesVault.vy`;
19. `contracts/vaults/modules/StabVault.vy`;
20. every production caller of `Teller.depositFromTrusted`;
21. the three M1-owned test files; and
22. `scripts/abis/Teller.json`.

If this brief conflicts with the integrated M0 packet or specification, stop
and return the conflict. Do not silently choose one. The integrated M0 product
decisions control economics and route posture; this brief controls the M1
implementation workflow and gates.

The integrated specification preserves two intentionally different design
layers. Its earlier Phase D describes the larger permanent measured-receipt
architecture, where a general route may accept `0 < R <= Q`. Its later
owner-directed minimum-change launch proposal in Section 23 supersedes that
behavior for M1 and requires `R == Q` on every route. Specifically,
specification Section 23.3.A supplies the exact five-step Teller delta, while
Section 23.10 item 6 assigns generalized short-receipt Teller semantics to the
post-launch backlog. For this slice, those provisions and M0 owner-packet
Section 10 are the controlling mechanism authority; the earlier
measured-receipt design is not an M1 implementation alternative. Any ambiguity
beyond that explicit supersession is a stop and owner-review condition.

## 4. Owner decisions required before kickoff

Approval of this draft as documentation is not M1 implementation
authorization. Before creating the implementation worktree, the fresh agent
must find an explicit, dated owner approval of all decisions below and the
exact 40-character launch baseline.

### M1-D01 — exact production, test, and evidence file ceiling

Approve exactly:

- production: `contracts/core/Teller.vy`;
- tests: `tests/core/teller/test_teller_deposit.py`;
- tests: `tests/core/teller/test_teller_rebalance.py`;
- tests: `tests/vaults/test_stock_token_vault_comparison.py`; and
- durable evidence:
  `docs/chains/rh/evidence/stock-token-m1-exact-receipt.md`.

No other implementation, test, or evidence file may change. In particular, no
mock contract, fixture, shared test configuration, ABI JSON, interface, vault,
CreditEngine, AuctionHouse, Deleverage, Ledger, defaults, migration, manifest,
dependency, CI, or `rh-summary.md` file belongs to M1.

Test-only contracts may be defined inline inside one of the three authorized
Python test files if necessary. They must not be imported by production code,
must not create a new repository file, and must remain clearly labeled as
test-only. If the required coverage cannot be expressed cleanly inside the
approved test ceiling, stop and return a revised exact file proposal before
creating or editing another file.

The integrated M0 Section 10 proposal fixed the one-production/three-test file
ceiling and required exit evidence, but did not assign that evidence a
repository path. The fifth path above is a governance/evidence artifact, not a
second implementation surface. It must preserve the approved rationale,
source/caller matrices, hashes, test evidence, gate provenance, and
supersession history for the later composed audit.

**Recommendation:** approve. The production/test surface remains the
M0-reviewed minimum, while the durable record prevents the most important
Track 8 implementation evidence from existing only in chat history.

### M1-D02 — exact-receipt invariant and amount identity

Approve:

```text
Areq = external caller's raw amount argument
Q    = amount returned by existing TellerUtils.validateOnDeposit
C0   = exact-length vault custody balance immediately before transfer
C1   = exact-length vault custody balance immediately after transfer
R    = C1 - C0

require Q > 0
require C1 >= C0
require R == Q
require vaultResult == Q
```

`Q`, not `Areq`, controls the receipt proof. This preserves `max_value(uint256)`
behavior, depositor-balance capping, per-user limits, global limits, and every
other existing validation adjustment.

The existing Teller event and return value remain `Q`, now proved equal to the
call-local receipt and the vault result.

**Recommendation:** approve. Comparing against the raw external amount would
break existing bounded-deposit semantics.

### M1-D03 — exact balance-read boundary

Approve one internal, contract-local observation helper that:

- performs a static `balanceOf(vaultAddr)` call;
- accepts only a successful response of exactly 32 bytes;
- decodes one `uint256`;
- rejects revert, false call status, empty response, short response, and
  oversized response; and
- adds no public or external selector.

The helper must not accept truncation of an oversized response. A typed call
that cannot distinguish exact from oversized return data is insufficient for
this slice.

**Recommendation:** approve. Exact observation is necessary for the proof
being claimed; accepting malformed ABI data would weaken it.

### M1-D04 — transient measurement mutex

Approve one contract-local transient Boolean mutex for the deposit measurement
window:

1. reject if already set;
2. set before observing `C0`;
3. keep it set through transfer, `C1`, delta validation, and the vault
   accounting call;
4. require the vault result to equal `Q`;
5. clear it immediately after the vault accounting call; and
6. perform existing Ledger, Lootbox, housekeeping, PriceDesk, event, and
   return work only after it is cleared.

A revert must roll back the transient state naturally. Do not add persistent
state, a public getter, an event, a per-user mutex, a token allowlist, or a
second reentrancy system.

The mutex blocks only a nested deposit measurement during the sensitive
window. It must not block the first legitimate trusted `depositFromTrusted`
call or existing post-window housekeeping.

**Recommendation:** approve. Without a measurement mutex, a token or vault
callback can contaminate the `C0`/`C1` window.

### M1-D05 — one exact-transfer policy for every route

Approve one policy for public and trusted routes: a successful deposit must
receive exactly `Q`. There is no trusted-caller short-receipt exception.

The implementation must cover:

- `deposit`;
- every element of `depositMany`;
- `depositFromTrusted`;
- the deposit leg of `rebalance`;
- `convertToSavingsGreenAndDepositIntoStabPool`; and
- `depositIntoGovVault`, with and without lock duration.

It must also source-trace and regression-test the named existing
`depositFromTrusted` producers:

- Stability claim auto-deposit;
- Stability RIPE reward;
- Deleverage;
- HumanResources;
- Lootbox auto-stake;
- BondRoom;
- CreditEngine surplus; and
- CreditRedeem surplus.

Configuration may keep some Robinhood launch routes disabled, but disabled
launch posture does not excuse shared-source regression coverage.

**Recommendation:** approve. A privileged or protocol caller cannot make a
short receipt safe.

### M1-D06 — Robinhood-first and unchanged live Base

Approve:

- one shared forward Teller source for future deployments;
- Robinhood as the first intended deployment of the M1 Teller;
- no Base deployment, migration, registry rewire, state move, or live action
  in M1;
- the existing deployed Base Teller remaining unchanged;
- any future Base adoption requiring a separate per-asset compatibility,
  migration, state, governance, and rollout decision; and
- no claim that Base is remediated merely because repository source changes.

The M1 source must remain chain-neutral. Do not use `chain.id`, a
Robinhood-specific contract, or address-based policy.

**Recommendation:** approve. This preserves the owner's minimum-change
directive and avoids an unnecessary live Base core migration.

### M1-D07 — review, commit, and non-activation boundary

Approve:

- Gate 1 complete-file review before committing the implementation patch;
- a reviewer-verified evidence-only update recording Gate 1 provenance before
  that commit;
- an owner-authorized local commit of the exact approved bytes;
- current-`rh` reconciliation without rebase only after the reviewed patch is
  committed;
- full Gate 2 validation and independent merge-readiness review;
- a separate reviewer-verified and owner-authorized evidence-only follow-up
  commit recording Gate 2 provenance, without amending history;
- no feature push until separately authorized;
- no merge into `rh` until separately authorized; and
- no deployment, configuration, signing, transaction, or Stock activation.

**Recommendation:** approve. This is the first Track 8 production-contract
slice and should retain the program's strongest review path.

## 5. Bootstrap and baseline seal

The planning reconciliation baseline is:

```text
cb3fe7392c44613aaeec49bd2486369fe0da3556
```

That commit contains the integrated M0 closure and reviewed H-02 correction,
but it does not contain this currently untracked draft and therefore cannot be
the M1 launch baseline. The brief must first complete review and be committed
and integrated through the normal owner-controlled documentation workflow.

The exact launch baseline must be the future reviewed `rh` commit containing
the approved brief. A commit cannot name its own future SHA, so the owner must
supply and approve that full 40-character post-integration commit in the M1
kickoff message, and Phase A must record it in the durable evidence record. Do
not edit this brief merely to insert its own containing commit.

If `rh` advances after the brief integrates but before kickoff, do not
substitute the newer hash. Return the complete delta, reconcile this brief and
the M0 authorities, and obtain a new exact baseline authorization.

The fresh agent must:

1. Start in `/Users/wigglez/dev/ripe-protocol`.
2. Verify the integration worktree is clean.
3. Fetch or otherwise verify the live `origin/rh` ref without altering
   history.
4. Verify local `rh`, cached `origin/rh`, and live remote `rh` equal the
   owner-approved 40-character commit.
5. Verify the H-01, H-02, S1, S2, S3, and M0 integration commits are
   ancestors.
6. Verify the M0 owner packet records M0 closed and M1 unauthorized except for
   the new explicit owner message required by this brief.
7. Record SHA-256 hashes for:
   - this brief;
   - all four integrated M0 documents;
   - `contracts/core/Teller.vy`;
   - `scripts/abis/Teller.json`;
   - the three authorized test files;
   - `requirements.in`; and
   - `requirements.txt`.
8. Record exact Python, pip, Vyper, Titanoboa, and pytest versions.
9. Run the H-01 dependency gate and `pip check` in an environment installed
   from the integrated lock.
10. Run S1 and S2 baseline gates and the baseline targeted Teller tests.
11. Verify branch `rh-track-8-m1-exact-receipt` does not exist locally or
    remotely.
12. Verify path
    `/Users/wigglez/dev/ripe-protocol-track-8-m1-exact-receipt` does not
    exist.

If the branch or path exists, stop. Do not reuse, delete, reset, clean, or
overwrite it without an explicit owner decision.

After all checks pass, create:

```bash
git -C /Users/wigglez/dev/ripe-protocol worktree add \
  -b rh-track-8-m1-exact-receipt \
  /Users/wigglez/dev/ripe-protocol-track-8-m1-exact-receipt \
  <owner-approved-full-rh-commit>
```

Repeat the commit, tree, status, file-hash, dependency, H-01, S1, S2, and
targeted-test checks inside the new worktree. All later M1 commands and edits
must run there.

Do not modify or commit from the integration worktree.

## 6. Environment and test isolation

Use the integrated H-01 lock exactly. If the active environment differs, stop
or obtain explicit authorization for a disposable exact-lock environment. Do
not refresh or loosen dependency pins in M1.

Where Boa requires a compiler cache:

- create a task-specific mode-`0700` directory under `/private/tmp`;
- use `from boa.interpret import set_cache_dir`;
- use a distinct mode-`0700` pytest basetemp parent for each command;
- set `ETHERSCAN_API_KEY=local-placeholder` only where the existing tests
  require the non-secret placeholder;
- unset live RPC, private-key, explorer, and deployment credentials; and
- remove and verify absence of all task-specific temporary paths afterward.

No M1 test needs a live RPC, fork acquisition, signer, private key, or
broadcast. If a test unexpectedly requests one, stop and report it.

The five H-01 exceptions and their review/expiry controls remain authoritative.
If an exception review or hard expiry occurs before M1 validation, stop and
resolve H-01 before relying on the environment.

### 6.1 S5 and H-02 coordination

Track 6 S5 is a parallel production slice with no current file overlap: S5
owns the forward `contracts/data/Ledger.vy`, while M1 owns
`contracts/core/Teller.vy`. The slices nevertheless share a live call path.
After an M1 deposit, Teller housekeeping calls
`Ledger.checkAndUpdateLastTouch`; S5 changes how that Ledger operation obtains
the action-block identity on Robinhood.

Apply these ordering rules:

- if S5 integrates before M1 kickoff, M1 must start from that integrated
  Ledger and include the complete S5 targeted regressions in its baseline and
  Gate 2 runs;
- if S5 integrates after M1 Gate 1, M1 must stop, reconcile the exact S5
  integration commit with owner authorization, prove the reviewed M1 bytes
  unchanged, and re-establish post-window housekeeping liveness plus the S5
  Ledger/Teller regressions;
- if M1 integrates first, S5 must rerun the M1 Teller deposit and
  post-window-housekeeping regressions before S5 can integrate; and
- neither slice may edit the other's production file, reinterpret the other's
  security decision, or absorb the other's deployment/migration ownership.

The H-02 production work and its focused second-pass correction are integrated
at this draft's baseline. The correction removes Base Sepolia's stale
Base-mainnet blueprint alias, requires any nonempty blueprint ID to resolve to
an existing migration namespace, and hardens sanitized fork-teardown
diagnostics. It changes no M1-owned file, M0 authority, dependency lock,
compiler behavior, Teller/vault behavior, or M1 assumption and therefore adds
no M1 mechanism or implementation gate. Any later H-02 change that affects one
of those boundaries must be reconciled before M1 continues.

## 7. Exact file ownership

The complete M1 diff may contain only:

```text
contracts/core/Teller.vy
tests/core/teller/test_teller_deposit.py
tests/core/teller/test_teller_rebalance.py
tests/vaults/test_stock_token_vault_comparison.py
docs/chains/rh/evidence/stock-token-m1-exact-receipt.md
```

The evidence record is mandatory if M1-D01 is approved. It must include:

- exact owner authorization and baseline identity;
- the minimum-change/no-change risk analysis;
- the Phase A caller, callback-chain, vault-return, and token-compatibility
  matrices;
- compiler-primitive evidence;
- exact source, artifact, ABI, selector, event, and layout hashes;
- baseline and candidate counterexamples;
- every targeted and full-suite command/result;
- S5 and current-`rh` reconciliation;
- Gate 1 and Gate 2 findings, responses, identities, dates, and approval
  provenance;
- all accepted residual risks and M2-M5 dependencies; and
- exact file hashes and supersession history.

The record reports evidence; it may not create authority. Pending decisions
must remain visibly pending until the named owner or reviewer acts. Material
changes to the source, tests, matrices, conclusions, or gate status must update
the record in the same commit or evidence-only follow-up commit and trigger
review of both the changed implementation and the complete record.

The completion messages must remain self-contained and repeat the important
evidence, but chat messages are not the durable source of provenance.

The following are explicitly prohibited:

- every file under `interfaces/`;
- every vault production source;
- `contracts/core/CreditEngine.vy`;
- `contracts/core/AuctionHouse.vy`;
- `contracts/core/Deleverage.vy`;
- `contracts/data/Ledger.vy`;
- every default or Switchboard source;
- every migration or manifest;
- every generated ABI or artifact file;
- shared fixtures including `tests/conf_core.py`;
- new mock or testing-contract files;
- dependency and CI files;
- checked clock inventory files; and
- `docs/chains/rh-summary.md`.

Reading and temporary artifact generation are allowed. Repository edits are
not.

## 8. Required Phase A: source, caller, and compatibility audit

Phase A is read-only with respect to production and tests. It may create only
the M1-D01-authorized evidence record. It must finish before editing a
production or test file.

### A1. Freeze current Teller semantics

Record exact source lines and behavior for:

- `TellerUtils.validateOnDeposit`;
- `_deposit`;
- `deposit`;
- `depositMany`;
- `depositFromTrusted`;
- `rebalance`;
- `convertToSavingsGreenAndDepositIntoStabPool`;
- `depositIntoGovVault`;
- the existing transfer/transferFrom split;
- the vault call with and without lock duration;
- Ledger participation;
- Lootbox points;
- housekeeping;
- PriceDesk snapshot;
- `TellerDeposit`; and
- the return value.

Explicitly confirm that `Q` is the value returned by
`validateOnDeposit`, after depositor balance and configuration limits, rather
than the raw external amount.

### A2. Enumerate every trusted caller

Regenerate the complete fixed-string inventory of production
`depositFromTrusted` call sites. For each, record:

- caller contract and function;
- asset source;
- destination vault-ID source;
- whether the producer can be reached, directly or through any callback chain,
  while another Teller `_deposit` measurement mutex is already active;
- the complete top-level entry-to-`depositFromTrusted` call chain supporting
  that conclusion;
- whether the caller transfers from its own custody;
- whether the call occurs inside another nonreentrant section;
- whether the destination can call back into the caller;
- Robinhood launch disposition; and
- exact regression test planned in one of the three authorized test files.

The inventory must at least reconcile the eight producer categories in
M1-D05. One discovered caller not covered by the integrated M0 matrix is a
stop, not an invitation to add a best-effort test.

Do not equate “inside another contract's nonreentrant section” with “inside a
Teller deposit measurement window.” The deciding question is whether the
mutex is already set when Teller receives the trusted call. Source-trace both
StabVault `_handleAssetForUser` origins—the claim path and the redemption
path—and prove that each first enters `depositFromTrusted` with the Teller
measurement mutex clear.

### A3. Prove current vault return semantics

Trace `depositTokensInVault` and `depositTokensWithLockDuration` for:

- SimpleErc20/BasicVault;
- RebaseErc20/SharesVault;
- StabilityPool/StabVault; and
- RipeGov.

Prove from source and baseline tests that an exact receipt of `Q` causes each
route to return `Q`, including share-based accounting and lock-duration
deposits. Shares may differ from `Q`; the external deposit-amount return may
not.

If any existing supported route legitimately returns a deposit amount other
than `Q`, stop before implementation. Do not weaken `vaultResult == Q`.

### A4. Confirm exact-transfer compatibility

Consume the integrated M0 matrix rather than inventing new runtime facts.
Reconcile:

- AAPL exact-transfer evidence and identity conditions;
- canonical USDG;
- launch sGREEN, RIPE, GREEN, and LP route dispositions;
- omitted assets and disabled trusted Stock routes; and
- all 27 Base ID-3 assets for forward-source/later-cutover compatibility.

The 27-row authority is the checked closure row in
`docs/chains/rh/stock-token-m0-evidence.md` Section 10:
“All 27 Base ID-3 assets refreshed for `C/N`, deposit support, LTV,
transferability/controls, and runtime identity.” Reconcile that row with its
underlying Section 6 table; do not re-derive the count from a partial grep.

New Ripe artifacts without deployed runtimes remain later proof obligations;
do not fabricate live rows for them.

Any enabled existing Robinhood token classified as fee-on-transfer,
rebasing-on-transfer, short-receipt, or unknown stops M1. A Base-only
incompatible row does not block Robinhood while Base remains on its old Teller,
but it must be recorded as blocking any future Base cutover.

### A5. Prove the pinned Vyper primitives

Before relying on the implementation design, create temporary compilation
probes outside the repository or inline inside an authorized test file to
prove the pinned compiler supports:

- a contract-local transient Boolean;
- exact response-length inspection for a static raw call;
- rejecting an oversized `balanceOf` result rather than truncating it;
- decoding a 32-byte `uint256`;
- rollback of transient state on revert; and
- clearing the mutex before later external calls.

The probe is evidence, not a new repository file. Remove it after use.

If the pinned toolchain cannot express the exact read and mutex inside
`Teller.vy` without a public selector, persistent state, interface edit, or
second production file, stop and return to the owner.

### A6. Baseline artifact and behavior seal

Record:

- Teller source SHA-256;
- compiler input/settings/version;
- creation and deployed bytecode hashes;
- complete ABI hash;
- every function selector;
- every event signature/topic;
- persistent storage-layout output;
- existing nonreentrant surface;
- targeted Teller test counts;
- full collected test count; and
- S2 inventory totals and clean status.

Do not inherit a historical collected count. Run `pytest --collect-only` on
the exact baseline and record the actual result.

### A7. Phase A stop report

Before editing, return a compact Phase A report with:

- exact baseline and hashes;
- caller matrix;
- vault-return matrix;
- exact-token reconciliation;
- compiler-primitive results;
- test/file-ceiling feasibility;
- no-change risk restatement; and
- every unresolved question.

Create the initial durable evidence record at
`docs/chains/rh/evidence/stock-token-m1-exact-receipt.md` with the same
material, exact commands/hashes, and every approval still truthfully marked.
The evidence record may be created only after M1-D01 explicitly authorizes its
path.

If Phase A identifies a stop condition, do not continue to Phase B.

## 9. Required Phase B: implement only ML-01

### B1. Add the internal exact-balance helper

Add one internal view helper in `Teller.vy` that:

1. statically calls `_asset.balanceOf(_holder)`;
2. captures call success and raw return bytes;
3. requires success;
4. requires exactly 32 returned bytes;
5. decodes one unsigned integer; and
6. returns it.

Use an output bound that allows the code to detect an oversized response. Do
not rely on a 32-byte output cap that silently truncates longer data.

Do not:

- expose the helper;
- add an interface method;
- use a token-specific branch;
- use a chain-specific branch;
- fall back to a different observation;
- accept empty data as zero; or
- emit observation diagnostics onchain.

### B2. Add the transient measurement mutex

Add exactly one transient Boolean with a clear chain-neutral name. The first
line of the sensitive window must reject an already-active measurement.

The protected interval is:

```text
mutex=true
C0=exactBalance(asset,vault)
transfer Q
C1=exactBalance(asset,vault)
require C1>=C0
require C1-C0==Q
vaultResult=deposit(Q)
require vaultResult==Q
mutex=false
```

Keep the mutex active through the vault accounting call because the vault is
an external callback boundary whose nested deposit could otherwise contaminate
the measurement/accounting relationship.

Clear it before Ledger, Lootbox, housekeeping, PriceDesk, event, and return
work. Preserve their current order exactly.

Do not add `@nonreentrant` annotations as a substitute for the approved
measurement mutex. Existing top-level reentrancy choices and unrelated Teller
actions are outside M1.

### B3. Preserve amount and route behavior

The implementation must:

- calculate `Q` with the unchanged `validateOnDeposit`;
- preserve `_areFundsHereAlready` transfer versus transferFrom behavior;
- measure the resolved destination vault, not Teller or the depositor;
- pass exactly `Q` to the vault;
- require exactly `Q` back from either vault entry point;
- emit `TellerDeposit.amount == Q`;
- return `Q`;
- preserve `depositMany` housekeeping behavior;
- preserve rebalance deposit-before-withdraw behavior;
- preserve sGREEN conversion semantics; and
- preserve RipeGov lock-duration semantics.

Do not introduce post-receipt limit recalculation. Existing validation occurs
before transfer and already defines `Q`.

### B4. Preserve fail-closed atomicity

Every failure in the observation, transfer, delta, nested-call, or vault-result
proof must revert the entire transaction. Tests must show no residual:

- token movement;
- nominal vault credit;
- shares;
- user-vault registration;
- deposit points;
- housekeeping touch;
- price snapshot;
- event;
- lock state; or
- rebalance withdrawal.

Do not catch and downgrade a failed exact-receipt proof.

## 10. Mandatory test matrix

All new and modified tests must live in the three authorized files.

### T1. Ordinary exact deposits

Cover:

- first exact deposit;
- later exact deposit;
- user B's existing exact-backed position followed by user A's exact deposit;
- deposit after a prior donation;
- donation between two deposits;
- multiple users;
- SimpleErc20;
- RebaseErc20;
- `max_value(uint256)`;
- depositor-balance capping;
- per-user limit capping;
- global limit capping;
- minimum-balance behavior;
- event amount;
- return amount;
- nominal amount; and
- share accounting where applicable.

Every successful case must assert:

```text
vaultCustodyDelta == Q
vaultResult == Q
eventAmount == Q
tellerReturn == Q
```

### T2. Short, fee, zero, negative, and excess receipt

Cover atomically reverting:

- zero receipt;
- one-unit short receipt;
- percentage fee-on-transfer;
- sender burn;
- receiver burn;
- custody decrease during the transfer window;
- receipt greater than `Q`;
- reflection/excess receipt;
- transfer returning false;
- transfer reverting;
- user B's ordinary existing backing masking user A's short receipt under the
  integrated baseline; and
- donation masking a short second deposit.

Both masking counterexamples must be demonstrated against the integrated
baseline and fixed only by the M1 change:

1. **ordinary multi-user masking:** user B deposits normally, then user A's
   short receipt is credited in full because aggregate custody already
   exceeds `Q`; and
2. **surplus masking:** a prior donation offsets the short current receipt.

For each, record the baseline's custody, user-level nominal credit, aggregate
nominal accounting, and resulting backing shortfall, then prove the candidate
reverts atomically. The multi-user case is the primary loss path; the donation
case is defense-in-depth evidence. Do not frame an attacker-funded donation as
a prerequisite for exploitation.

### T3. Balance-observation failures

Cover pre-transfer and post-transfer:

- target reversion;
- unsuccessful raw call;
- empty return;
- return shorter than 32 bytes;
- 31-byte return;
- return longer than 32 bytes;
- 33-byte return;
- malformed dynamic-shaped data; and
- a valid 32-byte maximum uint value.

Each malformed case must stop before any nominal credit. A post-transfer
failure must revert the transfer as part of the transaction.

### T4. Vault-result mismatch

Prove atomic rejection when:

- vault returns zero after exact receipt;
- vault returns less than `Q`;
- vault returns more than `Q`;
- vault reverts; and
- the lock-duration vault route returns a mismatched amount.

Do not modify a production vault or create a repository mock file. Use an
inline test-only contract or an existing fixture within the authorized test
files.

### T5. Batched deposits

Cover:

- all-exact `depositMany`;
- donation before one element;
- short receipt on the first element;
- short receipt on a later element;
- malformed balance read on a later element;
- exact deposits across two assets and vaults; and
- complete batch rollback when any element fails.

The mutex must acquire and release per `_deposit` window. It must not remain
set between successful batch elements.

### T6. Rebalance

Cover:

- exact deposit and withdrawal;
- `max_value(uint256)`;
- share-vault route;
- deposit-limit-capped `Q`;
- short deposit receipt;
- malformed balance read;
- vault-result mismatch; and
- failure before the withdrawal leg.

On any deposit-proof failure, the withdrawal leg, housekeeping, event, debt
health, and all balances must remain unchanged.

### T7. Trusted routes

Prove:

- a first legitimate `depositFromTrusted` call succeeds;
- transferFrom uses the trusted producer's custody;
- every named producer category retains its successful exact route;
- every named producer category fails atomically on a short or malformed
  receipt where that behavior can be induced;
- lock duration remains correct for RIPE producers;
- Stability auto-deposit remains live;
- CreditEngine/CreditRedeem sGREEN surplus routing remains live;
- Deleverage source behavior remains unchanged; and
- disabled Robinhood Stock trusted routes are still represented as disabled,
  not silently tested as launch-enabled.

If a named producer cannot be covered within the authorized files, stop and
request a revised test-file ceiling.

### T8. Teller-held sGREEN route

Cover:

- GREEN transfer to Teller;
- SavingsGreen deposit;
- exact sGREEN movement from Teller to StabilityPool;
- receipt proof at the StabilityPool custody address;
- sGREEN result/event reconciliation;
- short or malformed sGREEN transfer rollback; and
- existing approvals returning to zero.

M1 does not change SavingsGreen, GREEN, or StabilityPool.

### T9. RipeGov route

Cover:

- no-lock deposit;
- locked deposit;
- lock-duration capping;
- deposit for self;
- authorized deposit for another user;
- exact receipt and vault result;
- shares, lock data, points, event, and return;
- short/malformed receipt rollback; and
- no change to RipeGov source or ABI.

### T10. Measurement-window reentrancy

Cover nested deposit attempts:

- from token transfer/transferFrom;
- from pre-transfer balance observation if the test EVM permits the attempted
  callback under static context;
- from post-transfer balance observation;
- from the destination vault accounting call; and
- through `depositFromTrusted`.

Every nested measurement attempt during the window must fail closed and revert
the outer call atomically. Also prove:

- the first top-level public deposit succeeds;
- the first top-level trusted deposit succeeds;
- the mutex is clear in a later transaction after success;
- the mutex is clear in a later transaction after revert;
- a second `depositMany` element succeeds after the first releases;
- existing post-window housekeeping remains live; and
- unrelated Teller actions are not blocked outside the measurement window.

### T11. ABI, selector, event, and storage invariance

Compile from the exact source with the pinned compiler and prove:

- generated ABI bytes are identical to integrated
  `scripts/abis/Teller.json`;
- every pre-M1 selector is identical;
- no selector is added or removed;
- every event signature/topic is identical;
- every persistent storage entry is identical;
- exactly the approved transient mutex is added to transient layout;
- no public getter exists for the mutex or balance helper;
- compiler settings are identical; and
- creation/runtime bytecode changes are fully explained by the approved source
  delta.

Do not write generated output back to the repository.

### T12. Base and shared-source regression

Run the existing Base-oriented Teller, vault, Stability, RipeGov, CreditEngine,
CreditRedeem, Deleverage, Lootbox, BondRoom, HumanResources, AuctionHouse,
price-snapshot, deposit-points, and rebalance tests needed to prove that exact
tokens retain behavior.

Record:

- existing Base deployed Teller remains unchanged;
- no Base migration exists in the diff;
- no Base registry action exists;
- forward-source tests pass for Base-supported exact tokens;
- any Base-only incompatible token remains a future cutover blocker; and
- the Robinhood implementation uses the same source without a chain branch.

## 11. Gate 1 — independent implementation and security review

After Phase B and all targeted tests pass:

1. Leave all five files unstaged and uncommitted.
2. Produce the complete patch and SHA-256.
3. Produce final SHA-256 for each changed file.
4. Record exact compiler/tool versions and commands.
5. Record source, compiler input, creation bytecode, runtime bytecode, ABI,
   selector, event, persistent-layout, and transient-layout hashes.
6. Record targeted test names, counts, durations, skips, xfails, warnings, and
   temporary-path cleanup.
7. Record baseline-versus-candidate results for both the ordinary multi-user
   masking and donation-masking counterexamples.
8. Record the complete caller/route and vault-return matrices.
9. Record the exact `git diff --name-status`, diff stat, and
   `git diff --check`.
10. State every accepted residual risk and every M2-M5 dependency.

Independent reviewers must cover:

- protocol accounting;
- security and reentrancy;
- Base compatibility; and
- complete source/test implementation.

At least one reviewer must independently read the complete five-file patch,
not only the agent summary. At least one reviewer must independently reproduce
the exact-receipt and reentrancy tests. Reviewer identity and dated approval
provenance must be recorded in the approval message. An anonymous or
self-authored approval cannot close Gate 1.

Gate 1 must reject:

- raw `Areq` used instead of validated `Q`;
- aggregate post-balance used without `C0`;
- non-exact response decoding;
- oversized return truncation;
- mutex clearing before the vault call;
- trusted-route exceptions;
- changed downstream ordering;
- persistent storage;
- ABI/event/selector changes;
- an untested caller;
- an unexplained runtime change; or
- any file outside the exact ceiling.

After independent Gate 1 approval, the implementation agent may update only
the evidence record to quote the exact dated reviewer disposition and mark
Gate 1 accurately. Leave that evidence-only delta uncommitted. The same
reviewer must verify the complete record, its new hash, the exact provenance,
and that the four implementation/test files remain byte-identical.

Only after that evidence verification may the owner authorize a local commit
of the exact reviewed five-file bytes.

## 12. Post-Gate-1 commit and reconciliation

The owner authorization must name:

- the complete patch hash;
- all five final file hashes;
- Gate 1 approval provenance; and
- the exact commit permission.

Commit only the approved bytes. Do not amend the commit later to hide
sequencing or provenance. Any content change after approval reopens Gate 1.

After the approved commit:

1. fetch or verify the then-current live `origin/rh`;
2. compare the complete incoming delta with the authorized baseline;
3. stop on any overlap with the five M1-owned files, M0 controlling documents,
   H-01 lock/gate, compiler/toolchain behavior, or an M1 assumption;
4. obtain owner authorization for the exact current `rh` commit;
5. merge that exact commit into the feature branch with a normal merge commit,
   without rebase or history rewriting;
6. resolve no semantic conflict without renewed review;
7. prove the reviewed M1 bytes remained identical; and
8. rerun all Gate 2 validation on the reconciled tree.

If `rh` has not advanced, record that fact and do not create a meaningless
merge commit.

## 13. Gate 2 — final validation and merge readiness

Gate 2 requires:

1. H-01 dependency gate;
2. `pip check`;
3. S1 clock profiles;
4. S2 checker with a clean production inventory;
5. S2 inventory tests;
6. all three complete M1-owned test files;
7. all named downstream caller regressions;
8. the complete applicable S5 Ledger/Teller regression set against the exact
   integrated or reconciled S5 disposition;
9. all required Base/shared-source regressions;
10. ABI/selector/event/storage/transient-layout proof;
11. Python compilation for modified Python tests;
12. exact Vyper compilation and artifact hashes;
13. full repository collection;
14. full serial repository suite;
15. no selected test skipped or xfailed;
16. `git diff --check`;
17. whitespace checks that include new inline source strings;
18. sensitive-literal and credential scan;
19. production-scope diff proof;
20. worktree collision scan against active branches; and
21. exact virtual-merge tree proof against current `rh`.

The S2 checker must remain clean. M1 introduces no `block.number`,
timestamp, cadence, or new production path. Do not add inventory exceptions or
classifications for M1.

The full-suite record must include the exact environment prefix, interpreter,
command, private basetemp, cache path, collected/selected/deselected counts,
result, duration, warnings, and cleanup.

The final independent reviewer must compare:

- the Gate 1 approved patch;
- the committed bytes;
- the reconciled bytes;
- the exact current `rh`;
- the complete durable evidence record;
- all test/artifact evidence; and
- the final virtual-merge tree.

Before that review, update the evidence record with the exact reconciliation,
Gate 2 commands/results, hashes, residuals, and a visibly pending Gate 2
status. After approval, update only the evidence record with the exact dated
reviewer disposition. The reviewer must verify the complete final record and
that every implementation/test byte remains unchanged. Commit that
evidence-only provenance update as a separate, owner-authorized follow-up; do
not amend or rewrite the implementation commit.

Gate 2 approval plus the verified provenance update means only “ready for
owner integration into `rh`.” It is not push, merge, deploy, activation,
external audit, or release authorization.

## 14. Stop conditions

Stop immediately and return evidence if:

- any M1-D01 through M1-D07 decision lacks explicit owner approval;
- the exact baseline is missing, stale, or ambiguous;
- the integration worktree is dirty;
- the proposed branch or worktree already exists;
- M0 is not integrated and owner-closed;
- a controlling M0 object changed without reconciliation;
- an H-01 gate fails or an exception control is stale;
- S5 integrates or changes its Ledger/Teller behavior without the coordination
  and regression rules in Section 6.1;
- the durable evidence record is absent, stale, contradicts the implementation,
  or claims an approval that did not occur;
- the pinned compiler cannot implement an exact-length read;
- an oversized response would be silently accepted;
- the transient mutex requires persistent storage or a public selector;
- a discovered deposit caller is absent from the approved matrix;
- a legitimate trusted route cannot remain live;
- an approved exact-transfer route requires `R != Q`;
- a supported vault legitimately returns an amount other than `Q`;
- a required test needs a fourth test file or a repository mock change;
- a production file other than `Teller.vy` appears necessary;
- any interface, ABI JSON, selector, event, persistent layout, default,
  migration, manifest, dependency, CI, inventory, or summary edit appears
  necessary;
- a `chain.id`, chain name, token address, or Robinhood-specific source branch
  appears;
- any failure leaves token movement, credit, shares, points, touch, snapshot,
  event, lock, or rebalance state behind;
- an M2-M5 mechanism is pulled into M1;
- a Base live cutover is proposed;
- a mandatory test fails, skips, xfails, or is relaxed;
- the feature patch changes after reviewer approval;
- current `rh` overlaps M1 or invalidates an assumption; or
- any RPC, secret, signer, transaction, deployment, configuration, or
  governance access becomes necessary.

The safe response is a bounded evidence return and owner decision. Do not widen
the slice to make the stop go away.

## 15. Prohibited claims

Do not claim that:

- M1 makes Stock Tokens launch-ready;
- M1 fixes custody deficits;
- M1 fixes auction or deleverage settlement;
- M1 fixes bad debt;
- M1 changes deployed Base;
- an ABI hash proves runtime semantics;
- a unit test authorizes deployment;
- a disabled route is implemented;
- a future Ripe token has live compatibility evidence;
- an omitted or unknown token is compatible;
- a clean merge proves a security review;
- Gate 1 or Gate 2 authorizes a live action; or
- repository source parity means live bytecode parity.

## 16. Completion report

Return a complete, self-contained report containing:

### Identity

- branch and worktree;
- authorized baseline commit and tree;
- current `rh` and live `origin/rh`;
- feature HEAD and tree;
- merge base;
- ahead/behind;
- clean/dirty status; and
- local/remote feature status.

### Authorization

- verbatim dated owner M1-D01 through M1-D07 approval;
- exact baseline authorization;
- Gate 1 reviewer identities and approval;
- local commit authorization;
- reconciliation authorization;
- Gate 2 reviewer identities and approval; and
- explicit list of actions still unauthorized.

### Scope

- exact changed files;
- diff stat and patch hash;
- per-file SHA-256;
- prohibited-path negative proof;
- production-source count;
- current Base-runtime no-change statement; and
- M2-M5 exclusion statement.

### Semantics

- final `Areq/Q/C0/C1/R/vaultResult` definitions;
- exact balance-read implementation;
- transient-mutex lifetime;
- route/caller matrix;
- vault-return matrix;
- ordinary multi-user and donation-masking baseline/candidate results;
- failure atomicity result; and
- accepted residual risks.

### Artifacts

- compiler input/settings/version;
- source hash;
- creation and runtime bytecode hashes;
- ABI hash and byte-identity proof;
- selector/event proof;
- persistent-layout proof;
- transient-layout proof; and
- no generated repository edit.

### Validation

- environment and lock identity;
- H-01, S1, and S2 results;
- applicable S5 Ledger/Teller regression and ordering result;
- each targeted matrix result;
- downstream/Base regression result;
- collection and full-suite result;
- skips/xfails/warnings;
- whitespace and sensitive-literal scans;
- temporary-path cleanup; and
- virtual-merge tree proof.

### Remaining gates

State plainly:

- M1 by itself is not economically activatable;
- M2, M3, M4 proof, and approved M5 remain required;
- independent audit of the complete composed containment group remains
  required;
- Base adoption remains a separate unapproved decision; and
- no deployment, registration, configuration, Stock listing, borrowing,
  signing, or transaction is authorized.

## 17. Definition of done

M1 is ready for owner integration review only when:

- the seven M1 decisions and exact baseline are explicitly approved;
- Phase A finds no stop condition;
- exactly one production file and three existing test files contain the entire
  implementation/test patch;
- exactly one durable M1 evidence record contains the Phase A, Gate 1, Gate 2,
  reconciliation, provenance, and residual-risk evidence;
- every successful deposit route proves `vaultCustodyDelta == Q` and
  `vaultResult == Q`;
- malformed, short, excess, negative, and nested cases revert atomically;
- every trusted producer and special route is covered;
- selectors, events, ABI, and persistent storage are unchanged;
- the single transient mutex is fully proven;
- live Base remains untouched;
- Gate 1 and Gate 2 are independently approved with attributable provenance;
- the final evidence-only approval updates are independently hash-verified;
- all targeted and full-suite validation passes on current reconciled `rh`;
- the feature branch is clean; and
- the owner, not the implementation agent, decides whether to push and merge.

Anything less is an evidence checkpoint, not a completed M1 slice.
