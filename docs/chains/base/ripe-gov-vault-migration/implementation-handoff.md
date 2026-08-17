# Base Legacy RipeGov Migration — Fresh-Session Implementation Handoff

**Purpose:** self-contained handoff for a fresh agent in a fresh session
**Controlling architecture:** `docs/chains/base/ripe-gov-vault-migration/decision-plan.md`
**Repository:** `/Users/wigglez/dev/ripe-protocol`
**Historical planning baseline (not an execution lock):** `master` commit
`91eda49ccd34a25090582aff0695075c4c806011`, tree
`fbd958bec234081f70769045abd8f9bb638f6dd7`
**Reviewed RH contract-source anchor (not a moving-branch lock):** `origin/rh` commit
`6260726d0d08a3bfec5b6e494c0adacb70be90f9`, tree
`0f8ec4bcf936873a0705f70bc4be0cc4b90b1d22`
**Merged RH migration implementation:** `f7f42db1aa1a3a4ec3e65550a0098044b66381c2`,
merged by `24de5e62e2158114e3694c9a356c0add94b6f329`
**Legacy Base vault:** `0xe42b3dC546527EB70D741B185Dc57226cA01839D`
**Legacy VaultBook ID:** `2`
**Planning snapshot:** Base block `49,667,747` on 2026-08-07
**Status:** ready for an explicitly authorized Phase 1 production-contract-only implementation;
all compilation, tests, chain qualification, artifacts, and operations work remain owner-gated
**RH dependency status:** selected migration patterns were reviewed at the anchor above; its blind
Teller/Lootbox source-removal behavior is a known defect and negative reference, while later
deployment-only commits remain non-blocking
**Mainnet status:** no deployment, proposal, confirmation, configuration, activation, migration, or
other state-changing Base transaction is authorized by this file

This is the operational companion to the decision plan. It does not replace the decision plan and
does not silently turn an architecture decision into implementation or mainnet authorization. The
fresh agent must use the user's dispatch message to determine which phase is actually authorized.

---

## 1. Exact fresh-session directive

The owner can hand off the work with this instruction:

> Work from `/Users/wigglez/dev/ripe-protocol`. Read
> `docs/chains/base/ripe-gov-vault-migration/implementation-handoff.md` and its controlling
> `decision-plan.md` completely before acting. Rebind only the source inputs authorized for the
> active phase; Phase 1 must defer live-chain facts and all validation to Phase 2.
> Follow the phase gates, file ceilings, evidence requirements, and stop conditions exactly. Do not
> merge RH wholesale into Base, do not modify deployed-Ledger semantics,
> and do not perform any Base mainnet write. If I authorize Phase 1, edit only the seven approved
> production smart-contract files. Do not compile, run tests, perform fork or live-chain
> qualification, generate ABIs/artifacts, edit deployment or runbook files, stage, commit, or push.
> Finish the complete contract diff against the contract-source contents available when Phase 1
> starts, then stop and present it for my review. Commit or tree-number movement—especially RH
> deployment commits—is not a blocker. Begin Phase 2 validation/testing only after I explicitly
> approve the Phase 1 contract diff. Once I approve it and authorize continuation, proceed through
> all remaining non-mainnet validation, tests, fork qualification, artifacts, and runbook work to
> Gate D without stopping for routine intermediate approvals.

The receiving agent's first response should state:

1. the exact repository commit and tree it found;
2. the branch and concise worktree status, including pre-existing changes;
3. the two planning files it read;
4. the phase it believes the user's message authorizes;
5. confirmation that no architecture-level owner decision remains open and the relevant RH
   contract-source blobs/contents used for this phase; and
6. any overlapping local change or concrete architecture conflict that requires a stop.

The agent must not treat “use this implementation plan” as permission to deploy or transact. It
must not treat the word “implementation” in the title as permission to edit contracts if the
dispatch asks only for review, qualification, or planning.

Phase 1 is deliberately source-only. A compile, unit test, runtime-size measurement, ABI export,
artifact update, fork read, holder census, deployment-script edit, or runbook edit belongs to Phase
2 or later, even if it would normally be performed alongside contract development. This split is
an owner review boundary, not a claim that uncompiled source is validated.

---

## 2. Source hierarchy and conflict rules

Use this hierarchy:

1. the owner's current message controls authorization and any newly settled decisions;
2. this handoff controls execution order, deliverables, gates, and stop conditions;
3. `decision-plan.md` controls the selected Base architecture and its factual reasoning;
4. the relevant RH smart-contract contents available at the start of the active phase supply the
   reviewed upstream migration patterns; the explicit Base applicability decisions in this
   handoff control where legacy behavior must diverge;
5. current repository source controls local behavior;
6. verified deployed source, runtime bytecode, and pinned Base state control production facts.

If two layers conflict, stop and report the exact conflict. Do not resolve a contract- or
economics-level conflict by preference. Live state may have advanced since the planning snapshot;
re-read it rather than carrying forward a mutable address, registry version, pending action, asset
configuration, or proposed new vault ID.

`rh` is a moving deployment/development branch, not an execution lock. The owner has directed the
agent to assume that ongoing RH deployment commits do not change the relevant smart contracts.
Record the relevant RH contract blobs or content hashes once when Phase 1 starts and finish the
Phase 1 source diff against those contents. A later RH commit/tree—whether noticed during the phase
or merely possible—does **not** interrupt work, invalidate completed work, or require a mid-phase
fetch, merge, rebase, restart, or stop. Do not poll RH while implementing.

At the next planned phase boundary, one cheap path/blob comparison may confirm the assumption. If
the relevant contract contents are unchanged, the commit movement is ignored. If a relevant
contract unexpectedly changed, still finish and present the Phase 1 candidate; include the exact
contract delta as a review note. Reconcile it only after owner review, and require renewed owner
review only if reconciliation changes the approved production-contract diff or a settled safety
invariant. Commit numbers, trees, deployment files, generated files, migrations, manifests, and
other non-contract RH changes are never blockers for this workstream.

The planning files currently live under an untracked `docs/` directory in the original worktree.
They are user-requested artifacts, not disposable noise. Preserve them. A fresh agent should not
stop merely because those two known files are untracked, but it must stop before overwriting any
overlapping user change or before using an otherwise dirty worktree for a build candidate.

---

## 3. Problem statement and required end state

The deployed Base RipeGov vault predates the RH migration exporter. It can withdraw a user's full
position to a recipient, but it cannot return the migration struct expected by the new importer.
The deployed Ledger also cannot be changed and allows only the registered Lootbox to remove a vault
from a user's enumeration.

The required design therefore uses the long-lived replacement Teller to synthesize the legacy
migration record from public source state, withdraw tokens directly from the legacy vault to the
new vault, and invoke the new vault's importer atomically. A replacement Lootbox—not Teller and not
a new Ledger—must settle source points, protect source reward claimability, retain source
enumeration until administrator settlement/cleanup, and call the existing Ledger remover only
after the source vault no longer needs to participate.

The intended end state is:

- all live RIPE and current Aero RIPE/WETH LP positions are in the new RipeGov vault;
- token amount, saved governance-point stock, pending governance points through the migration
  block, original unlock, and original last lock terms are preserved once per position;
- the chosen target share-rate policy is implemented exactly and disclosed;
- the target is the only destination for ordinary RipeGov deposits and lock operations;
- source Lootbox rewards are administrator-claimed to each user before that source asset is
  deregistered; forfeiture and user-performed migration/cleanup are out of scope;
- users retain correct collateral enumeration and debt health throughout;
- the deprecated RIPE/WETH pool is proved empty and cleaned deliberately;
- source Ledger participation is removed only through replacement Lootbox after complete
  source-depletion, administrator reward settlement, and asset-cleanup conditions are satisfied;
- Ledger and MissionControl remain the deployed Base contracts under the selected narrow option;
- normal Teller, Lootbox, HumanResources, BondRoom, Stability Pool, and Switchboard behavior works
  against the new vault; and
- the legacy vault is retired without an unaccounted holder or replayable migration path.

---

## 4. Settled architecture and prohibited shortcuts

### 4.1 Settled direction

Qualify final Base replacements for these departments:

- Teller;
- TellerUtils;
- Lootbox;
- HumanResources; and
- SwitchboardAlpha; and
- SwitchboardEcho.

Deploy and register a migration-aware target RipeGov vault at the next confirmed VaultBook ID.
Preserve deployed Ledger and MissionControl. Preserve BondRoom and Stability Pool; route only their
known RipeGov producer calls from legacy ID 2 to the target inside the final Teller. Stage all
department changes through the existing registry delay and confirm them atomically.

Migrate a single asset type per operational batch. Within a batch, each migration call is exactly
one `(user, asset)` position. Never mix RIPE and LP calls in one outer Safe transaction and never
overlap their wind-down configuration windows.

### 4.2 Prohibited shortcuts

Do not:

- add, restore, or depend on `Ledger.removeVaultFromUserForMigration`;
- redeploy Ledger;
- modify the legacy vault;
- assume Base MissionControl has RH's core-vault pointer;
- copy the RH migration flow's source-first Ledger removal;
- copy latest RH's both-endpoints-paused validator onto the legacy Base source;
- copy latest RH's blind `Lootbox.removeVaultFromUserForMigration` pass-through;
- use `getNumUserAssets(user) == 0` as the pre-cleanup balance predicate;
- remove source Ledger participation after migrating only one of several source assets;
- treat target token receipt as sufficient without exact amount and source-depletion checks;
- send assets to Teller, a Safe, an EOA, or any off-chain custodian between source and target;
- use AuctionHouse or CreditEngine as the migration exporter;
- route every ID-2 trusted deposit blindly to the target;
- use an all-zero RipeGov configuration to unlock positions;
- overlap RIPE and LP wind-down terms;
- touch imported target governance data while that asset's wind-down terms are active;
- waive a nonzero raw-share census residual as dust;
- publish the lower-bound holder count as complete;
- use an unbound RH worktree, test expectation, ABI, or byte-size projection as Base evidence; or
- create a temporary Teller adapter unless the owner explicitly reopens that rejected option.

---

## 5. Settled owner decisions and RH contract-source binding

These architecture decisions are closed. Their implementation consequences remain hard gates.

| Item | What the decision actually means | Implementation consequence |
|---|---|---|
| Target VaultBook ID | **Settled rule:** use the next available ID proved by a final pinned live read. `6` remains only a hypothesis until then. | No architecture choice remains; bind and requalify the actual ID before deployment. |
| Share-rate policy | **Settled:** accept the fresh-target vault accounting share-rate reset. This means shares per token, not governance points. Imported governance-point stock remains separately preserved. | Record/disclose the future accrual change; do not design legacy-rate seeding. |
| Unlock and stragglers | **Settled intent:** administrators migrate every complete-manifest row; users do nothing; each successful target position preserves its original unlock/last terms; failures revert atomically; no source residual is waived; no retirement before 100% reconciliation. | Translate this into fail-closed code, tests, and operations. |
| Freeze scope | **Settled:** use a full-protocol Teller pause for the measured migration window. It blocks ordinary deposits, withdrawals, borrowing, repayment, liquidation, auctions, claims, and other Teller routes. Teller pause does not itself block ungated `depositFromTrusted` or every other department authorized by the legacy vault. | Keep the administrator migration entry callable while paused; independently block/reroute every other legacy touch; measure and qualify the total outage before mainnet authorization. |
| Source rewards and cleanup | **Settled Base adaptation:** checkpoint each migrated source asset, retain claimable enumeration, administrator-claim its accrued rewards to the user with no staking, deregister it only through Lootbox, and remove the source Ledger entry only after every asset/reward/registration is gone. | Fork-prove the ordinary broad claim route or implement a narrow bounded settlement/cleanup route. Never forfeit or require user action. |
| Reviewed RH implementation | **Content-bound pattern:** migration implementation `f7f42db1...` was reviewed in `origin/rh@6260726...`. Reuse TellerUtils extraction, Echo's 25-row governance batch pattern, Lootbox-only Ledger authority and no-Ledger-redeploy. Reject the RH source-first immediate RipeGov removal and both-paused validation for Base. | Use the relevant RH contract contents at Phase 1 kickoff and implement only the documented Base delta. Later commit/tree movement is non-blocking. |

The reviewed RH anchor contains a known multi-asset correctness defect: Teller checks depletion of
only the migrated asset and then unconditionally calls a Lootbox function that blindly removes the
whole source-vault Ledger entry. RH has both RIPE and RIPE/WETH LP governance assets, so this is a
reachable migration hazard rather than a theoretical mismatch. Treat those exact Teller/Lootbox
hunks as a negative reference. The separately assigned RH workstream owns its remediation and
deployment decision; the Base agent must neither fix RH here nor wait for that workstream.

The reviewer also reports that the separate RH plan's candidate-state wording and frozen test hash
are stale after the merge, and that its residual-suite equivalence claim still needs independent
reproduction. Those are RH-track evidence obligations, not Base inputs. Do not import or wait on
them; Phase 2 must independently establish Base source, test, artifact, and failure evidence.

The settled operational interpretation for stragglers is fail closed: the manifest must
close exactly before wind-down, each failed row remains atomic and retryable, normal terms are
restored if the batch program is aborted, and the legacy vault is not retired while any positive
raw share remains. That settlement does not authorize forced forfeiture, arbitrary custody, or
permanent unlock of an unmigrated holder.

No architecture-level owner decision remains open. The fresh agent must still present measured
share-rate disclosure, exact holder/borrower/reward census, Base cleanup-path proof, and freeze
duration before requesting later lifecycle approval.
Those remaining items are evidence and acceptance measurements, not open share-rate or straggler
policy choices. The share-rate reset and fail-closed administrator straggler policy are settled in
the table above.

For provenance, the former external worktree was clean at implementation commit
`f7f42db1aa1a3a4ec3e65550a0098044b66381c2`, tree
`863d68ef61cf194e58bae76fc27f7b703a63b2e4`, and that implementation was included in the reviewed
RH anchor. The local `/Users/wigglez/dev/ripe-protocol-rh` worktree was stale at
`be6e4e9805e9b499b10f61cd219c555e62b43857`; do not treat that worktree name as proof of current
content. Read the relevant contract files from the current RH ref or a clean detached view, record
their blobs/content hashes, and proceed. Do not modify either RH worktree for this Base task.

Reviewed RH comparison blobs (historical content anchors):

| Source | Git blob at `6260726...` |
|---|---|
| `contracts/vaults/RipeGov.vy` | `2cc26d104a86a181b6a53966778c25daf50507ec` |
| `contracts/core/Teller.vy` | `57e99b8be73bb3b8dcda1e2fc703a40067969cf3` |
| `contracts/core/TellerUtils.vy` | `5e8a7d34b9572d0e3bdd5ac6878dc125091b4b8b` |
| `contracts/core/Lootbox.vy` | `0373d6f2dd9360352c237f16d71347d28f959b44` |
| `contracts/core/HumanResources.vy` | `2cfa7ba8e393fc02acb7cccc9aee833590dedf3f` |
| `contracts/config/SwitchboardAlpha.vy` | `47c4501e3f8b3d147bf6310fa47ba0866d4cf4ac` |
| `contracts/config/SwitchboardEcho.vy` | `32f646860598cbb72fe9b451959ac125b5cffefb` |
| `contracts/data/Ledger.vy` | `ec345579b350de3bda04686e656ef936c331873f` |

These are comparison anchors, not required current commit identities and not permission to copy RH
wholesale. If the current RH contract blobs match, no further RH reconciliation is necessary even
when its commit/tree differs. The Base candidate must show the delta from the correct Base source
and explain every adopted RH hunk.

---

## 6. Lifecycle and authorization gates

### Preflight 0 — source-only intake (not a delivery phase)

**Default authority:** read-only.

1. Read both planning files completely.
2. Run `git status --short --branch`, `git rev-parse HEAD^{commit}`, and
   `git rev-parse HEAD^{tree}`.
3. Record all pre-existing changes. Do not clean, stage, restore, or reformat them.
4. Resolve the current RH ref once, record the blob IDs or content hashes of the relevant contract
   files, and compare them with the historical anchors in §5. Do not require RH's commit/tree to
   equal the historical anchor, do not poll it during Phase 1, and do not inspect deployment-only
   drift as a prerequisite.
5. Confirm that the current Base smart-contract files do not overlap pre-existing local changes.
   Do not perform live-chain reads, a holder census, compilation, tests, fork work, or generated
   artifact checks during this preflight.

Commit/tree movement in Base or RH is not itself a stop. Record the Base commit from which the
candidate worktree was created for provenance, then continue on that stable worktree. Stop only for
an overlapping smart-contract edit, an actual relevant-contract-content conflict that prevents a
coherent candidate, or a new owner-level architecture decision. If an RH contract-content change
is merely discovered after work begins, finish Phase 1 and report it at Gate A.

### Phase 1 — isolated production smart-contract candidate

**Authority required:** explicit local Phase 1 contract-implementation authorization. This does
not authorize compilation, tests, validation, chain/RPC access, evidence generation, artifacts,
deployment files, a commit, push, registry action, or chain write.

Create a clean isolated worktree and `codex/` branch from the current owner-designated Base source
at kickoff. Record its path, branch, commit, tree, and clean status, but treat those identifiers as
provenance rather than branch-motion stop gates. Copy no RH working-tree bytes or generated
artifacts into it. Compare only the relevant RH contract contents, then implement the documented
Base adaptation as one reviewable production-contract diff.

Phase 1 does not live-read or freeze the eventual target VaultBook ID. The source must use the
architecture's reviewed constructor/configuration mechanism and must not hard-code the historical
ID-6 hypothesis. Phase 2 binds the actual next available ID and validates that mechanism.

#### 6.1 Strict Phase 1 contract ceiling

The expected production ceiling is:

- `contracts/vaults/RipeGov.vy`;
- `contracts/core/Teller.vy`;
- `contracts/core/TellerUtils.vy`;
- `contracts/core/Lootbox.vy`;
- `contracts/core/HumanResources.vy`;
- `contracts/config/SwitchboardAlpha.vy`; and
- `contracts/config/SwitchboardEcho.vy`.

`contracts/vaults/RipeGov.vy` in this ceiling is the source used to build the **new target vault**.
It does not authorize changing, upgrading, replacing in place, or otherwise mutating the deployed
legacy vault at `0xe42b3dC546527EB70D741B185Dc57226cA01839D`; that bytecode remains untouched.

No Ledger, MissionControl, BondRoom, Stability Pool, CreditEngine, AuctionHouse, Boardroom, Addys,
or unrelated contract change is within the expected ceiling. If implementation requires any such
production file, stop and request an architecture/file-ceiling expansion with the precise reason
and blast radius.

Phase 1 may modify **only** the seven production `.vy` files listed above. Do not create or modify
tests, fixtures, mocks, interfaces, ABIs, artifact expectations, migrations, deployment scripts,
parameter files, runbooks, evidence files, or documentation in the implementation worktree. Do not
compile or run any test, formatter, generator, size check, fork, RPC query, or validation command.
After the source diff is complete, inspect only the source diff and worktree status, then stop at
Gate A. ABI exports, artifact expectations, deployment scripts, Base parameter/runbook files, and
all test changes belong to later owner-approved phases.

The reviewed RH `0009_RedeployStaleContracts.py` is a deployment reference, not a Base migration to
merge. Its useful rules are: deploy replacements before Safe registry writes, print/review exact
start/confirm calldata, seed from live state rather than launch defaults, and deliberately preserve
Ledger. Do not deploy `DefaultsRobinhoodLive` or copy Robinhood constructor values onto Base.
MissionControl remains deployed on Base; every changed Base constructor/immutable/scalar and pending
action must instead be derived from pinned Base state. In particular, compare the reviewed RH
Lootbox constructor/immutable shape with Base and review the exact Base-compatible choice rather
than silently adopting it.

#### 6.2 Target RipeGov requirements

The target importer must:

1. accept only the currently registered final Teller;
2. operate only in the deliberately selected migration pause/mode;
3. reject zero user, asset, source, amount, or an invalid source contract;
4. reject an existing target position or prior replay for `(user, asset)`;
5. prove the target already received exactly the imported amount in the same transaction context;
6. calculate nonzero target shares using the owner-approved share-rate policy;
7. register the target asset position exactly once;
8. write saved plus pending governance points, original unlock, original last terms, target shares,
   and current last-update block directly;
9. update per-user and global governance-point totals exactly;
10. avoid every normal gov-data refresh while wind-down terms are active;
11. emit a complete import event; and
12. return target shares for Teller post-checking.

Do not weaken the generic RH importer merely to accommodate the legacy source. The legacy-specific
synthesis and allowlisting belong in the Base Teller/control path.

#### 6.3 Final Teller requirements

The external migration entry must assert that Teller is paused, remain reachable only through the
intended registered SwitchboardEcho control path, and hard-bind:

- legacy source vault ID 2 and exact source address;
- the exact target ID/address;
- the approved RIPE and current Aero LP asset set;
- one user and one asset per internal migration call; and
- the active asset migration window.

For a call, Teller must:

1. validate user/asset, source/target registration, source unpaused state, target migration state,
   support/configuration, source Ledger membership, and no target replay;
2. read source raw shares, token amount, and the complete original `userGovData` before withdrawal;
3. calculate pending points through the execution block using source `getLatestGovPoints`, original
   `lastTerms`, original unlock/last-update/shares, and the unchanged current asset weight;
4. snapshot target token balance;
5. call legacy `withdrawTokensFromVault(user, asset, max_value, target, addys)`;
6. require full source-share and source-amount depletion and the withdrawal's depleted result;
7. require exact target receipt with no Teller balance or allowance residue;
8. call target `importPositionForMigration` with amount, saved-plus-pending points, original unlock,
   and original last terms;
9. require returned shares and target state to match the expected import exactly;
10. add target Ledger participation exactly once and retain source participation while any source
    asset, reward entitlement, or cleanup-relevant registration remains;
11. settle target and source Lootbox points while the source asset remains enumerable;
12. leave source enumeration claimable until the administrator settlement path claims that asset's
    reward to the user with no staking; only then may Lootbox deregister that zero-balance asset,
    and only after the final asset/reward/registration may it remove source Ledger participation;
13. post-check the source asset registration, all source balances, both Ledger memberships, and
    target state; and
14. run the real borrower housekeeping/health path last, reverting the whole call if unsafe.

The legacy withdrawal destroys source gov-point state on a full withdrawal, so all original data
and pending points must be captured before that call. Off-chain manifest values are evidence, not
the execution input for time-sensitive pending points.

The final Teller must also replace all ordinary fixed-ID-2 behavior correctly:

- direct user deposits/lock operations resolve the target;
- HumanResources uses the target;
- Lootbox reward staking uses the target;
- BondRoom and Stability Pool's known trusted ID-2 deposits are translated to the target only for
  the expected caller, RIPE asset, and operation;
- unsupported callers or arbitrary ordinary use of legacy ID 2 fail closed; and
- repayment, liquidation, auction, rebalance, claim, withdrawal, and unrelated deposits retain
  their existing behavior.

#### 6.4 Replacement Lootbox requirements

Lootbox must recognize the target ID as the RipeGov vault for points scaling. Do not leave target
governance shares on the ordinary-vault precision divisor path.

The administrator reward settlement/cleanup path must:

1. accept only the exact final Teller/Echo call graph and require the approved migration window;
2. accept only legacy source ID 2/address and an approved asset/user;
3. require source points settled, claim the source reward to the user with no staking, and prove the
   entitlement is no longer stranded before deregistration;
4. enumerate authoritative source user-asset entries and read balances, rather than using the
   registration count as a balance predicate;
5. call the source vault's existing Lootbox-only `deregisterUserAsset` for zero-balance entries;
6. handle swap-and-pop enumeration without skipping the item moved into the removed index;
7. fail closed if a fixed cleanup cap is reached, an entry cannot be classified, or any positive
   source share remains;
8. preserve source Ledger membership while any positive balance, reward entitlement, or
   cleanup-relevant registered asset remains;
9. call deployed `Ledger.removeVaultFromUser` only after complete depletion/cleanup;
10. post-check the Ledger result and source state; and
11. emit enough data to reconcile which assets were cleaned and whether the vault was removed.

`getNumUserAssets` may be used only as an enumeration bound or postcondition. It is not evidence of
a positive balance and cannot gate entry to the cleanup path.

The broad ordinary claim loop traverses borrow points and every participating vault. Reuse it only
if fork evidence proves the complete side-effect/accounting surface and its availability for every
manifest user. Otherwise implement the smallest narrow admin settlement path. Forfeiture and user
action are not fallbacks.

#### 6.5 TellerUtils, HumanResources and switchboard requirements

TellerUtils must follow the reviewed RH validation extraction but implement Base's exact asymmetry:
legacy source ID 2/address is valid only while unpaused, the exact target is valid only in its
paused migration state, both support the active asset, source Ledger membership exists, and every
address resolves from the same RipeHQ/address bundle as Teller. Do not copy RH's both-paused check.

HumanResources must use the target vault for every balance read, transfer, burn, and trusted deposit
that formerly used ID 2. Re-seed or deterministically resolve every pending contributor action and
preserve all non-ID-related behavior.

SwitchboardAlpha must validate/configure the target rather than literal ID 2. Preserve/re-seed every
scalar and pending action or prove it empty before replacement.

SwitchboardEcho must follow the reviewed RH governance-only batch pattern with a hard ceiling of 25
but must not accept arbitrary source/target IDs. Each batch hard-binds source ID 2, the exact target and
one active asset; it may contain many unique users but never RIPE and LP together. Preserve/re-seed
every scalar and pending action or prove it empty before replacement. Measure a lower operational
batch limit on the fork rather than treating 25 as a required size.

The migration function must not become an arbitrary token-moving governance primitive. Its source,
target, assets, lifecycle state, and recipient are fixed by reviewed configuration/code.

### Gate A — mandatory owner review of Phase 1 contracts

Phase 1 ends here. Present only the production smart-contract candidate:

- the kickoff Base commit/tree as provenance, current branch/status, and isolated worktree path;
- the seven-file-or-smaller changed-path list and complete production source diff;
- a concise contract-by-contract explanation of the migration flow, permissions, external calls,
  storage changes, and known assumptions;
- a source-level trace for a user holding RIPE and LP proving that migrating the first asset cannot
  remove source Ledger participation and that final removal is reachable only after the second
  asset, reward settlement, and complete registration cleanup;
- confirmation that Ledger, MissionControl, tests, fixtures, interfaces, ABIs, artifacts,
  migrations, deployment scripts, runbooks, and every other file are unchanged;
- the relevant RH contract blob/content hashes used, plus any unexpectedly changed RH contract
  content discovered without treating RH commit/tree motion as a blocker; and
- any unresolved design issue that truly requires an owner decision.

Do **not** compile, test, validate, query Base, generate files, stage, commit, push, or begin follow-up
edits while presenting Gate A. Explicitly state that the source is intentionally uncompiled and
unvalidated. Stop and wait for the owner's express approval of the Phase 1 contract diff and
authorization to begin the remaining non-mainnet work through Gate D. Silence, general plan
approval, or “looks good so far” is not Phase 2 authorization.

If RH or Base receives new commits while waiting, commit movement does not invalidate the Gate A
package. At most, compare the relevant smart-contract blobs when Phase 2 begins. Deployment-only or
other non-contract changes are ignored. If relevant contract contents unexpectedly changed, record
the exact delta; do not discard or restart the reviewed candidate. Only a required change to the
owner-reviewed production diff returns to Gate A.

### Phase 2 — owner-approved validation, tests, and qualification evidence

**Authority required:** explicit owner approval of the Phase 1 production-contract diff and
explicit authorization to continue. That single approval authorizes the agent to proceed through
Phases 2, 3, and 4 and deliver Gate D without routine approval pauses. These phases perform the
census, source/runtime qualification, compilation, test implementation/execution, fork testing,
size/layout/ABI review, local artifacts, and Safe runbook. They still do not authorize staging,
commit, push, deployment, registry action, or a mainnet write.

At Phase 2 kickoff, record the then-current Base/RH commits for provenance. Commit/tree movement is
not a stop. Confirm only whether the relevant smart-contract file contents changed. Non-contract
deployment churn is out of scope and ignored. If reconciliation changes any owner-reviewed
production-contract byte, return only that concrete diff to Gate A; otherwise continue Phase 2
without another owner interruption.

Bind:

- chain ID, RPC endpoint class, pinned block number/hash/timestamp;
- RipeHQ, VaultBook, Ledger, MissionControl, Teller, TellerUtils, Lootbox, HumanResources,
  SwitchboardAlpha, SwitchboardEcho, BondRoom, Stability Pool, legacy vault, Boardroom, CreditEngine,
  AuctionHouse, PriceDesk, RIPE, and both LP addresses;
- registry IDs, versions, active addresses, pending actions, confirmation blocks, and delay;
- the complete RipeHQ `AddressUpdateConfirmed` history, deduplicated by transaction hash plus log
  index; reproduce the reviewer-reported 37 unique events and listed multi-event blocks in the
  decision plan or report the exact discrepancy;
- verified deployed source metadata and runtime bytecode hashes;
- compiler version/settings and source-content hashes for every comparison;
- every RipeGov asset index, support flag, configuration, token balance, total raw shares, and
  pause state;
- all five replacement Lootbox scalar values and all relevant pending state in HumanResources,
  SwitchboardAlpha and SwitchboardEcho; and
- the current MissionControl configuration, user configuration, and delegation surface that the
  selected narrow option promises not to migrate.

#### 6.6 Census construction

Walk from the vault's actual deployment block through the pinned final block. Do not use a page or
log-count cap as a completion boundary. Build the candidate set from:

1. deposits;
2. both sides of ordinary vault transfers;
3. both sides of `RipeTokensTransferred` events;
4. withdrawals and any other event that exposes a participant address; and
5. any authoritative indexed source discovered during source/event review.

For every candidate, read at the pinned block:

- source asset enumeration and registration indexes;
- `doesUserHaveBalance`;
- `getTotalAmountForUser` token amount;
- `userBalances` raw shares;
- `userGovData`, including saved points, last shares, last update, unlock, and last terms;
- total user governance points;
- Ledger source participation and full user vault enumeration;
- debt amount, liquidation/bad-debt status, and relevant health values;
- source Lootbox user/asset deposit points and claimable reward inputs; and
- whether the user already has any target entry if a target exists on the fork.

The manifest should have one row per `(user, registered source asset)` and retain zero-balance
registrations until deliberately classified. Include at least:

`user`, `asset`, `asset_index`, `registered`, `raw_shares`, `token_amount`, `saved_gov_points`,
`pending_gov_points_at_pin`, `unlock`, `last_points_update`, `last_terms`, `total_user_gov_points`,
`source_ledger_member`, `user_vault_ids`, `debt`, `liquidation_state`, `source_loot_points`,
`source_claimable_inputs`, `candidate_origin`, and `pinned_block`.

#### 6.7 Mandatory closure

For every registered asset:

```text
sum(manifest.raw_shares for asset) == legacyVault.totalBalances(asset)
```

This equality is exact. A nonzero residual means the candidate walk is incomplete. Expand it and
repeat. Do not waive dust.

Also reconcile summed per-user token amounts to the vault token balance within a documented bound
derived from the exact shares-to-amount rounding formula. This amount reconciliation is secondary,
because separate user conversions round down. Do not use
`getTotalAmountForVault(asset) == token.balanceOf(legacyVault)` as an independent proof; the former
returns the latter in this implementation.

The deprecated pool `0xF8D92a9531205AB2Dd0Bc623CDF4A6Ab4c3a2526` must have zero total raw
shares, zero token balance, and no positive user raw share. If any condition fails, it becomes a
real migration asset and the architecture returns to owner review.

**Census deliverable:** reproducible manifest, scripts/commands, raw read evidence, closure report,
exact holder and position counts, multi-asset count, borrower cohort, reward exposure, and batch/gas
projection.

The Phase 2 test ceiling includes:

- existing RipeGov, Teller, TellerUtils, Lootbox, HumanResources, SwitchboardAlpha,
  SwitchboardEcho, Ledger, and borrower tests;
- new migration-specific unit/integration tests under the corresponding existing test folders; and
- a new Base-fork migration suite in a clearly named `tests/` subtree.

No production contract outside the Phase 1 ceiling may change. Validation-driven corrections
inside the seven approved production files are permitted only as an explicit follow-up diff and
must return to Gate A for owner review before more validation proceeds.

### Gate B — post-approval validation review

Before fork operation, assemble the following internal gate evidence. If it is green, continue to
Phase 3 without another owner check-in; if resolving it changes an owner-reviewed production
contract, return that delta to Gate A:

- baseline/final commit and tree for provenance only;
- the owner-approved production diff plus any separately re-approved correction and changed-file
  list;
- storage-layout comparison for every changed stateful contract;
- ABI/selectors/events/constructor comparison;
- permission and external-call graph for each new route;
- actual compiled and Boa-deployed runtime sizes;
- focused test results and coverage matrix;
- gas measurements for worst-case cleanup and operational batches; and
- explicit confirmation that Ledger and every other forbidden production file are unchanged.

Base enforces the 24,576-byte EIP-170 runtime limit. Use actual Boa-deployed code as the controlling
measurement, not only Vyper's runtime template. At the reviewed RH anchor `6260726...`, the Boa
expectations are Teller `24,258` bytes/`318` headroom, TellerUtils `11,900`/`12,676`, Lootbox
`22,665`/`1,911`, and SwitchboardEcho `22,912`/`1,664`. That RH Teller is only 18 bytes above
the project's 300-byte floor; this supersedes the old 437-byte baseline and prior unbound 29-byte
warning. The final Base contracts are different shapes and must be Boa-deployed independently.
Require at least 300 bytes of actual final Teller headroom unless the owner explicitly changes the
safety floor after review. If it does not fit, retain pause, reentrancy, receipt, depletion, points,
and housekeeping checks; move only view validation to TellerUtils and governance batching to Echo,
or stop and redesign instead of deleting safety invariants.

Do not confuse runtime-template size with deployed runtime size. The reviewer reproduced Teller's
`24,162` template plus 96 constructor-bound bytes as `24,258` deployed, and Lootbox's `22,537`
template/`2,039` template headroom. The controlling Lootbox deployment measurement remains
`22,665`/`1,911`; Phase 2 must independently measure the final Base deployment.

### Phase 3 — pinned Base-fork qualification

**Authority:** inherited from the owner's post-Gate-A authorization to complete the non-mainnet
qualification package. Do not pause for another routine approval. No mainnet write.

Use an archival Base fork pinned to the accepted block/hash and execute the real governance and
protocol paths. Deploy the candidate contracts exactly as production would. Use actual registry
staging, delay advancement, confirmations, activation/pause state, vault registration, support
configuration, and Safe/MultiSend-equivalent calldata.

#### 6.8 Required fork sequence

1. Reproduce pre-state and manifest closure.
2. Deploy target and replacement departments with exact constructor/state values.
3. Register/configure target at the confirmed ID while it is in migration-safe state.
4. Stage all replacement department actions.
5. Advance exactly through the registry delay.
6. Confirm replacements atomically and prove there is no mixed-department intermediate state.
7. Activate the approved full-protocol Teller pause. Prove the administrator migration route
   remains callable while every ordinary Teller path stops, and measure the full protocol outage.
8. Independently block or reroute every legacy touch not covered by Teller pause, including
   `depositFromTrusted` and reachable HumanResources, AuctionHouse and CreditEngine paths. Prove no
   non-migration call can refresh legacy or imported target gov data during wind-down.
9. Stage/confirm RIPE's minimal wind-down config: only `minLockDuration 43,200 -> 43,199` unless
   the current live value has changed and a new reviewed one-step worsening is required.
10. Migrate RIPE-only, multi-asset, zero-registration, borrower, boundary-health, liquidation, and
    worst-case cleanup representatives; then migrate the full RIPE manifest in asset-only batches.
    Administrator-settle each migrated RIPE source reward to its user before Lootbox deregisters
    that source asset; retain source Ledger participation for any remaining LP/reward.
11. Reconcile RIPE balance, reward and registration state completely, restore normal RIPE terms,
    and prove every imported RIPE unlock and last term survived unchanged.
12. Only then apply the current Aero LP wind-down terms.
13. Repeat representative and full-manifest LP migration plus administrator reward settlement.
14. Reconcile LP completely, have Lootbox perform final eligible source cleanup/removal, and restore
    normal LP terms.
15. Prove the deprecated asset is empty/cleaned for every affected user.
16. Activate/unpause the target only after all shared terms are normal and all migration checks
    pass.
17. Exercise ordinary target deposits, lock adjustment/release, HR, BondRoom, Stability Pool,
    Lootbox stake/claim, Boardroom power, borrower, liquidation, auction, repay, withdraw, and
    rebalance paths.
18. Prove replay and unsupported source/target/caller/asset attempts fail.

#### 6.9 Required test cohorts

At minimum:

- RIPE-only holder;
- LP-only holder;
- holder of both active assets;
- explicit sequential two-asset regression: migrate RIPE while LP remains, assert source Ledger
  participation and LP collateral valuation survive, then migrate LP, settle both source rewards,
  complete Lootbox cleanup, and assert source participation is removed exactly once;
- stale deprecated-asset registration with zero balance;
- stale zero-balance registration in another source asset;
- user with target Ledger membership already present;
- user at and beyond configured `perUserMaxVaults` during the temporary dual-membership interval;
- healthy borrower;
- borrower exactly at the accepted health boundary;
- unhealthy borrower whose migration must revert;
- liquidation-eligible/in-liquidation user;
- protocol bad-debt state;
- maximum source user-asset enumeration and swap-and-pop ordering;
- source reward claim-to-user success, disabled/unavailable claim failure, and no-stake enforcement;
- failed import, inexact receipt, fee/rebase-like receipt mismatch, and rollback;
- repeated migration/replay;
- late trusted producer deposit before the migration call;
- ordinary legacy-ID attempt after final routing; and
- price movement between batches.

#### 6.10 Transaction invariants

For every successful row:

- source token amount and raw shares for the asset are zero;
- target token balance increased by exactly the withdrawn amount;
- Teller token balance and allowance residue are zero;
- target raw shares equal the chosen share policy's exact calculation;
- target saved points equal source saved points plus pending points through that transaction block;
- target original unlock and last terms match the captured source values;
- target Ledger membership exists exactly once;
- source Ledger membership remains whenever any source participation or reward claimability still
  requires it and disappears only through Lootbox after final cleanup;
- each source reward is administrator-claimed to the user before that asset is deregistered;
- total source/target token and point accounting reconciles; and
- borrower health passes after the complete Ledger transition.

For every revert, all source balances/data, target balances/data, points, rewards, registrations,
and Ledger enumerations must be unchanged.

**Gate C deliverable:** deterministic fork command/environment, full results, gas and batch limits,
before/after state bundle, manifest reconciliation, event reconciliation, and every failure trace.

### Phase 4 — artifacts and Safe runbook

**Authority:** inherited from the owner's post-Gate-A authorization to complete the non-mainnet
qualification package. Do not pause for another routine approval. Still no mainnet write.

Only after Gate B and Gate C acceptance:

1. generate ABIs and artifact expectations from final reviewed source;
2. bind creation/runtime bytecode hashes, compiler inputs, constructors, immutables, selectors,
   events, layouts, sizes, and deployed-size margins;
3. write deployment/verification parameters without secrets;
4. produce exact Safe calldata for deployment, registrations, staging, confirmations, target setup,
   wind-down actions, migration batches, restoration, activation, and any retirement action;
5. derive each action ID and earliest confirmation block;
6. include preflight reads and postconditions for every transaction;
7. specify batch membership, ordering, gas ceiling, signer review fields, and retry behavior;
8. define pause/freeze start and maximum duration;
9. define abort triggers and the exact safe state after abort; and
10. re-run the complete calldata against a fresh pinned fork.

Registry rollback also has a 21,600-block delay. “Swap back” is not an immediate control. The
runbook must distinguish transaction-level atomic rollback, pre-confirmation cancellation, delayed
department reversion, config restoration, and a legacy-vault straggler remedy.

### Gate D — independent review and owner presentation

Present one bounded package:

- resolved owner decisions;
- source/evidence authority;
- exact holder/position/borrower/reward census;
- final contract diff and file ceiling compliance;
- test matrix and results;
- deployed runtime sizes/headroom;
- gas/batch/freeze estimates;
- exact Safe runbook and simulations;
- independent reviewer findings and resolution of every item, including nits;
- residual risks and explicit non-actions; and
- the precise next lifecycle action being requested.

Do not stage, commit, push, deploy, propose, or transact unless each action is separately authorized.

### Phase 5 — mainnet execution

This handoff does not authorize Phase 5. A future mainnet authorization must bind the final commit,
tree, artifacts, bytecode, deployed addresses, pinned preflight state, Safe calldata hashes,
manifest, batches, signer set, action IDs, timing, monitoring, abort authority, and independent
review. Any live-state drift after authorization requires a defined revalidation or a stop.

---

## 7. Validation commands and evidence hygiene

This section is forbidden during Phase 1. Use it only after the owner approves the production
contract diff and authorizes Phase 2.

Use the repository's pinned Python/Vyper dependencies. Do not install or upgrade dependencies
without approval. Record interpreter, Boa, Vyper, pytest, and compiler optimization/settings.

Keep test caches outside the repository and disable bytecode/pytest cache churn. A representative
pattern is:

```bash
audit_root=$(mktemp -d /private/tmp/base-ripe-gov-migration.XXXXXX)
chmod 700 "$audit_root"
mkdir -p "$audit_root/pycache" "$audit_root/xdg" "$audit_root/boa" "$audit_root/pytest"
env PYTHONDONTWRITEBYTECODE=1 \
  PYTHONPYCACHEPREFIX="$audit_root/pycache" \
  XDG_CACHE_HOME="$audit_root/xdg" \
  ETHERSCAN_API_KEY=local-placeholder \
  RIPE_AUDIT_CACHE="$audit_root/boa" \
  python -c 'import os,sys; from boa.interpret import set_cache_dir; set_cache_dir(os.environ["RIPE_AUDIT_CACHE"]); import pytest; raise SystemExit(pytest.main(sys.argv[1:]))' \
  -q -p no:cacheprovider --basetemp="$audit_root/pytest" <focused-test-paths>
```

Adapt only the interpreter path and focused paths to the qualified environment. Never expose RPC
credentials, API keys, private keys, mnemonics, Safe secrets, or shell history in evidence.

For each test run record:

- exact command with secrets redacted;
- commit/tree and dirty status;
- environment/tool versions;
- fork chain/block/hash if used;
- selected/collected/passed/failed/skipped counts;
- duration;
- complete failure identity; and
- artifact/log path and hash.

Do not report a grep zero or partial suite as broader proof. Do not update expected ABI/size/hash
fixtures merely to make a failing candidate green; first prove the new expectation is the intended
reviewed artifact.

Historical RH validation evidence reproduced while authoring this plan: detached
`origin/rh@6260726d0d08a3bfec5b6e494c0adacb70be90f9`, tree
`0f8ec4bcf936873a0705f70bc4be0cc4b90b1d22`; focused RipeGov migration plus deployed-runtime-size
lane `107 passed, 51 xfailed, 3 warnings` in `161.60s`. This is a contract-content reference, not an
RH-branch commit gate. Re-run the applicable validation in Phase 2 rather than treating this
historical result as permanent, and inspect expected xfails instead of counting them as passes.
The later re-review found that RH's RipeGov migration tests exercise only RIPE for the relevant
Teller path; its separate multi-asset test covers the generic vault path. Therefore the RH green
suite is specifically not evidence for Base's sequential RIPE-plus-LP Ledger-retention invariant.

---

## 8. Stop conditions

Stop and ask the owner before continuing if:

- an overlapping dirty change exists;
- any settled §5 consequence cannot be implemented without a new owner choice;
- the exact raw-share manifest does not close;
- the deprecated asset is not truly empty;
- the target ID is occupied or pending state changes the order;
- deployed source/runtime does not match the assumed legacy implementation;
- HumanResources, SwitchboardAlpha or SwitchboardEcho has unresolved state without an exact
  disposition;
- implementation needs Ledger, MissionControl, or another file outside the accepted ceiling;
- target imports require normal gov-data refresh under active wind-down terms;
- source reward state would become unreachable on asset deregistration;
- source Ledger removal would occur while any source participation remains;
- a borrower loses collateral enumeration or becomes unhealthy;
- exact receipt, replay, or atomic rollback cannot be proved;
- actual final Teller headroom is below the accepted floor;
- worst-case cleanup or batch gas is unsafe;
- the operational freeze exceeds the approved bound;
- Safe calldata differs from the fork-qualified bytes; or
- the requested action is a later lifecycle phase than the owner authorized.

Do **not** stop merely because Base or RH has a new commit or tree, including commits created by an
ongoing deployment. Do not continuously fetch or rebase. Relevant smart-contract-content drift is
handled at the scheduled Gate A/Phase 2 boundary as described above; non-contract drift is ignored.

When stopped, report the smallest blocking fact, its evidence, the affected phase, safe alternatives,
and the exact decision or authority required. Do not perform adjacent cleanup or speculative edits.

---

## 9. Definition of done for a handoff-ready implementation package

The implementation package is ready for owner review—not mainnet—only when:

1. every mutable live-state input required by Phase 2 or later is rebound, while commit-only drift
   remains non-blocking;
2. the census closes exactly in raw shares for all three registered assets;
3. all §5 decisions are recorded;
4. the relevant RH contract contents used by the candidate are recorded and every Base
   adopt/reject decision is implemented;
5. the production diff stays within its approved ceiling;
6. Ledger and MissionControl are unchanged;
7. legacy synthesis preserves amount, point stock plus pending points, unlock, and last terms;
8. source reward disposition occurs before each asset deregistration;
9. administrators claim source rewards to users with no staking before asset deregistration, and
   Lootbox alone removes the source vault from deployed Ledger after complete cleanup;
10. RIPE and LP windows are serial and imported data is never refreshed under wind-down terms;
11. every ordinary fixed-ID-2 producer/consumer route has an explicit final disposition;
12. borrower enumeration and health are proved across representative and full-manifest fork runs;
13. replay, receipt, failure atomicity, deprecated asset, and straggler cases pass;
14. final actual deployed bytecode fits with accepted safety margin;
15. ABIs/artifacts/layouts/hashes match final reviewed source;
16. the calldata-complete Safe runbook reproduces on a fresh fork; and
17. independent review has no unresolved blocking finding.

The package must end by stating exactly what remains unauthorized. In particular, a green fork and
approved contract diff still do not authorize deployment, registry actions, activation, or Base
migration.
