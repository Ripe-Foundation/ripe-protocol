# Vault Migrator / Base Legacy RipeGov Migration — Branch State & Handoff

**Canonical worktree:** `/Users/wigglez/dev/ripe-protocol-base-gov-migration-phase1`
**Branch:** `codex/base-gov-migration-on-rh` · **PR:** #83 (draft) · **Merged base:** `rh` @ `26e8270`
**Status (2026-08-11):** VaultMigrator architecture and the latest live `rh` are integrated. The
core-remediation candidate preserves pre-wind-down lock records on both governance routes, carries
irreversible accrual-disable state, and excludes every historically classified RipeGov from the
generic balance-only migration. Teller's owner-accepted 24,525-byte runtime remains unchanged under
RH-D027. This is not deployment or fork qualification; the verification evidence below predates this
remediation unless a later paragraph explicitly says otherwise.

> Read this before touching the branch. It records what changed, *why*, what is still broken, and
> the non-obvious facts that cost real time to discover.

> **Controlling update:** the owner replaced the architecture described in historical §§0–9 below.
> This section is the current source of truth wherever it conflicts with those sections. The old
> material is retained after this update because its Base-specific safety rationale and rejected
> failure modes remain useful evidence; its ownership map, size blocker, RPC task and statement that
> a new department was rejected are superseded.

---

## Current architecture — controlling

### One department owns all migration policy

`contracts/core/VaultMigrator.vy` is a new top-level RipeHQ department at registry id **25**. RipeHQ
ids 23 and 24 are reserved for the GREEN and RIPE CCIP pools on both Base and Robinhood Chain. It owns
all orchestration, validation, lifecycle state, batching, reconciliation and migration events for:

1. ordinary deposit-vault migration;
2. exporter-capable RipeGov migration; and
3. the immutable Base legacy RipeGov migration.

The governance-facing surface now matches those three use cases exactly:

1. `migrateVaultPositions` — ordinary registered vault to ordinary registered vault;
2. `migrateRipeGovPositions` — exporter-capable RipeGov to another exporter-capable RipeGov; and
3. `migrateLegacyRipeGovPositions` — immutable Base legacy RipeGov to the current core RipeGov.

There is no separate legacy setup/window setter or asset-scoped entry point. A legacy call carries a
bounded list of at most 25 users. For each user it snapshots and migrates **all** live source assets
that the current target supports, up to five registered source-asset slots. RIPE and the supported LP
therefore use simultaneous temporary wind-down configurations. Zero-address, duplicate and
no-position entries are harmless skips; any failure for a live position reverts the entire batch.

The destination is intentionally fail-closed and must be virgin for every
`(user, supported asset)` in the manifest. Preflight must prove zero target
shares, zero in-vault amount, every `GovData` field and stored term zero, and no
`positionMigratedOut` tombstone. A zero balance alone is insufficient: an
ordinary historical full exit retains checkpoint/lock data, while a prior
migration leaves a permanent tombstone. The planned destination is new, so
this remains a census requirement rather than introducing ambiguous
overwrite/merge semantics. One dirty row reverts the complete multi-user batch.

`VaultMigrator` is also present in `contracts/modules/Addys.vy` with canonical id/address getters.
The hot `Addys` struct was deliberately not widened. Teller authenticates VaultMigrator through the
canonical Addys getter, which is rooted in Teller's immutable RipeHQ address. Lootbox has no
migration-only authorization surface; its existing claim path resolves shared dependencies through
its own immutable-RipeHQ Addys binding. `_getVaultMigratorId` and the CCIP id constants are canonical
registry documentation/accessors; current in-repo code does not call them and dead-code elimination
keeps them out of deployed consumers.

### Authority and execution boundary

```text
governance -> SwitchboardEcho -> VaultMigrator -> Teller identity step(s) -> vault / Ledger
                                         \-----> Lootbox point checkpoints

freeze lifted -> ordinary Teller claim -> Lootbox reward settlement / asset + Ledger cleanup
```

- Echo remains the governance surface and forwards the original governance caller for events.
- VaultMigrator accepts only the currently registered SwitchboardEcho (Switchboard registry id 5).
- Teller accepts migration execution calls only from the current RipeHQ VaultMigrator (id 25).
- Both RipeGov batch routes prove the current Teller is paused before inspecting
  any user. This includes zero-position batches; an unpaused Teller can never be
  mistaken for an inert migration run. The ordinary vault route remains
  fail-closed through its Teller withdrawal/deposit entrypoints.
- Teller contains no migration validation, batching, window state or postcondition logic. Its four
  methods are thin identity steps: RipeGov source export/withdrawal, RipeGov import plus target
  Ledger registration, ordinary vault withdrawal, and ordinary vault deposit plus housekeeping.
- Source and destination are separate Teller calls so VaultMigrator proves exact receipt and source
  depletion *before* authorizing import/deposit. The whole sequence remains one atomic transaction.
- VaultMigrator resolves and validates both registered endpoints before calling Teller. Teller does
  not repeat destination validation: this is the deliberate thin identity boundary, and avoids
  spending Teller's limited bytecode headroom on duplicate migration policy.
- Each migration checkpoints deposit points for the source and target asset. It deliberately leaves
  the depleted source asset registered and the source vault in Ledger.
- Exporter-capable RipeGov export calculates pending points from the stored pre-wind-down
  `unlock`/`lastTerms` without refreshing them from current MissionControl config. Legacy migration
  snapshots the same record for every supported user asset before the first withdrawal. Both routes
  import and verify the original lock record.
- An exporter source's effective global/per-user governance-point accrual-disable state is carried
  into the target as an irreversible per-user disable in the migration transaction. This preserves
  the migrated user's disabled status without globally disabling unrelated target users. The target
  records its own disable block. Exporter-capable sources must implement both
  disable-state selectors and malformed or missing responses revert; only the
  exact constructor-bound immutable Base legacy source may treat those absent
  legacy selectors as no disable state to carry.
- After the migration batches finish and the freeze is lifted, the user's ordinary Teller/Lootbox
  claim settles those checkpointed rewards, deregisters each zero-balance asset only after its
  entitlement is gone, and removes the source Ledger entry only after no source assets remain.
- All migration-specific code was removed from TellerUtils.

### Permanent Lootbox terminal-dust policy

Deposit loot remains atomic across staker, voter and general-depositor categories because all three
share one user balance-point ticket. Ordinary positive proportional payouts are unchanged. Each
category independently follows this matrix when its payout rounds to zero:

- a funded category defers while the user still has a vault balance;
- an exited user with a funded category receives the minimum representable payout, exactly 1 wei of
  RIPE, and consumes the associated residual points;
- an empty category defers, for live and exited users alike, only while that category can currently
  refill (`ripePerBlock`, its allocation and the remaining Ledger reward budget are all nonzero); and
- an empty category that cannot refill consumes its terminal points at zero, even for a live user,
  so it cannot block a funded category.

The minimum is available only after exit, so a live position cannot repeatedly harvest 1 wei. A
category that must defer blocks the whole shared ticket; otherwise all resolved categories commit
together and the ordinary multi-asset cleanup runs. The public `calcSpecificLoot` ABI and its legacy
basis-point behavior remain unchanged; exact-output regressions separate that compatibility surface
from the internal claim path's point-progress guard.

### Base legacy binding and freeze

VaultMigrator's constructor is:

```text
(_ripeHq, _shouldPause, _legacyRipeGovVault)
```

An empty legacy address disables the route. The Base deployment binds the exact deployed legacy
vault, while the contract hard-codes and checks Base chain id 8453. Using the legacy route checks the chain
and proves VaultBook id 2 resolves to the immutable vault. The generic RipeGov route also rejects that
immutable source, forcing it through the legacy-only checks. This intentionally prevents the Base-only
route from becoming usable on another chain, against a replacement source or through the wrong path.

Lootbox's temporary id-2 precision exception is now also restricted to chain id 8453. The exact
immutable-vault binding remains in VaultMigrator rather than becoming a new Lootbox runtime
dependency: making ordinary claims depend on VaultMigrator availability would risk bricking claims
before registry activation or after the legacy component is removed.

The legacy route preserves the asymmetric endpoint rule: legacy source unpaused, target paused,
Teller paused and VaultMigrator unpaused. Ledger and CreditEngine must also remain unpaused because
each successfully migrated user receives one higher-risk housekeeping call, including last-touch and
post-migration debt-health validation. Operational controls may freeze other mutation surfaces, but a
"full department freeze" that pauses Ledger or CreditEngine is incompatible with this implementation.
The route performs exact position/points/lock checks and retains source Ledger participation. A normal
claim performs reward and registration cleanup only after the migration window. There is no transient
duplicate map; a duplicate user is a no-op after its first entry depleted all supported positions.

The temporary terms are global per asset, not per position. Lowering `minLockDuration` by one block
resets a position's effective legacy unlock only when the new minimum is below that position's stored
`lastTerms.minLockDuration`; changing `maxLockDuration` by one block does not generally unlock it.
The Base census must prove the chosen RIPE and LP wind-down values cover every migrating position.
The target stays paused so imported original terms cannot be refreshed while wind-down config is live.
Pause Teller **before** confirming the target as `coreRipeGovVaultId`, then pause
the still-virgin target immediately after that confirmation. Charlie's pointer
validation requires the candidate vault to be unpaused, but RipeGov deposits and
lock mutations are Teller-only; this ordering closes the otherwise dangerous
pointer-flip window without weakening Charlie's validation. Complete the target
virginity census after its pause and before the first migration batch.

The generic `migrateVaultPositions` route consults MissionControl's monotonic
`isRipeGovVaultId` classification for both endpoints. Pointer rotation never makes a former core
RipeGov eligible for the balance-only route. Historical exporter-capable vaults remain eligible only
through `migrateRipeGovPositions`; the immutable Base source remains dedicated to
`migrateLegacyRipeGovPositions`.

The planned replacement Base MissionControl supplies `coreRipeGovVaultId()`. Per owner direction,
there is no live Base RPC-check task for the old MissionControl.

### Current deployed runtime sizes

Measured from Boa-deployed code with Vyper 0.4.3; VaultMigrator and RipeGov were remeasured after the
2026-08-11 core remediation. The regression test enforces EIP-170 and headroom floors; Teller and
CreditEngine, the two contracts below RH's 200-byte default, are additionally pinned to the exact
owner-waived source, compiler output, deployed size and immutable-bearing runtime identity.

| Contract | Deployed runtime | EIP-170 headroom |
|---|---:|---:|
| VaultMigrator | 13,144 | 11,432 |
| Teller | 24,525 | **51 — RH-D027 exact waiver** |
| TellerUtils | 8,976 | 15,600 |
| SwitchboardEcho | 23,053 | 1,523 |
| Lootbox | 22,993 | 1,583 |
| RipeGov | 23,427 | 1,149 |
| Ledger | 13,306 | 11,270 |
| CreditEngine | 24,392 | **184 — RH-D026 exact waiver** |
| StabilityPool | 24,371 | 205 |

AuctionHouse remains 24,556 bytes (20 free) and Deleverage remains 24,569 bytes (7 free). Adding the
new Addys id/getters changes their transitive compiler-input identity but dead-code elimination leaves
their runtime unchanged. The pre-integration `rh` reference measured Lootbox at 22,665 bytes, so this
candidate adds 328 bytes. Lootbox is held to RH's stronger 200-byte default; RipeGov retains the
migration branch's independent 1,000-byte minimum.

The focused local legacy benchmark measured one supported asset at 1,076,775 gas for one user,
3,516,135 for five, 6,565,335 for ten and 15,712,935 for the 25-user ABI ceiling. These are local
characterization values. The settled worst-case local regression then migrated 25 users with both
supported assets (50 positions) in **28,070,872 gas**, leaving 1,929,128 gas below the repository's
30,000,000 envelope. That proves the public ceiling is locally executable but is not a Base-fork or
live-block promise; the preflight fork must remeasure the exact census/configuration and may select a
smaller operational batch if the observed envelope or safety margin requires it.

The independent review measured a two-asset claim at 408,507 gas versus 403,496 on `rh`: +5,011
(about 1.2%, or roughly 2.5k per asset). The increase comes from the balance/reward-flow reads needed
for terminal-category liveness and is recorded here rather than treated as free.

### Local verification completed

Before the 2026-08-11 core-remediation changes, the combined feature surface produced **965 passed, 4
deselected, 13 xfailed**. It covers all Lootbox and Teller tests; ordinary, current-governance and
legacy-governance migrations; RipeGov controls and vault behavior; MissionControl; the exact runtime
waivers; all three Lootbox deployment postures; and the deterministic contract-artifact inventory.
The xfails are the suite's recorded expectations; there were no unexpected failures or XPASSes.

The exact command was:

```bash
python -m pytest -q tests/core/lootbox \
  tests/core/teller \
  tests/vaults/test_vault_migration.py \
  tests/vaults/test_vault_migrator_legacy.py \
  tests/vaults/test_ripe_gov_controls_and_migration.py \
  tests/vaults/test_ripe_gov_vault.py \
  tests/data/test_mission_control.py \
  tests/test_vault_pointer_runtime_sizes.py \
  tests/deployment_profiles/test_lootbox_deployment_profiles.py \
  tests/inventory/test_contract_artifacts.py
```

The repository's default lean lane was also run after the live-`rh` merge and
the final consumer-inventory rebind. It produced **8 failed, 3,488 passed, 282
deselected, 22 xfailed, 25 errors**. That lane is not globally green on the
live RH baseline: `docs/simplification/validation-evidence.md` records 13
failures and the same 25 errors before this integration. Normalizing test-node
identities shows **zero new failure or error identities** here. This candidate
removes five inherited failure identities; the remaining eight failures and all
25 Morpho V2 constructor errors are the documented RH subset. The command was
the repository-default `python -m pytest -q` with network and credential
environment variables unset and Boa/pytest caches isolated under `/private/tmp`.

### Independent-review remediation and open decisions

An independent review found that the first VaultMigrator version let callers supply Lootbox's Addys
tuple before the VaultMigrator permission check. Because the check and reward dependencies were then
rooted in caller-selected addresses, that version allowed a forged registry/reward graph to drive the
real mint-authorized Lootbox. That privileged eager-settlement API has now been deleted entirely.
Migration only checkpoints points; the existing ordinary claim path owns reward settlement and
multi-asset-safe cleanup. ABI regressions assert that the removed entry point cannot reappear.

A second independent review found that the first terminal-dust implementation let any zero-paying
category block whenever the user still had a balance, even if that category had zero reward
allocation and could never pay. That could freeze funded categories behind residual voter/general
points. The corrected matrix above resolves structurally inactive categories at zero, preserves
funded live dust for later, and keeps active empty categories atomic until they refill. The same
review also caught a public-calculator compatibility regression; the external legacy behavior is now
separated from the internal point-progress rule and pinned by exact-output tests.

No migration batch has an on-chain transient dedupe. Each user entry owns all supported assets for
that user, so an exact duplicate is a harmless no-op after the first entry depletes those balances.
Off-chain manifests should still deduplicate for gas efficiency. The 25-user ABI bound is a ceiling,
not an operational batch-size promise; Base-fork gas measurement and failure-isolation policy choose
the actual batch size.

The same review identified two separate branch decisions. The owner resolved both explicitly on
2026-08-09:

1. **RipeGov pause gates approved.** `updateUserGovPoints`, `adjustLock` and `releaseLock` remain
   blocked while RipeGov is paused. This prevents an imported position's preserved terms or balance
   from being rewritten during the migration window. The pause matrix and DV-06 hardening checks now
   record the approved semantics instead of the superseded Robinhood characterization.
2. Adding the canonical VaultMigrator getter to Addys changes compiler metadata for the frozen Robinhood
   `SimpleErc20` artifact while leaving its executable prefix and runtime unchanged. The current artifact
   inventory is internally consistent. The owner approved rebinding the full creation hash from
   `cafe6aa7...` to `6df95ffc...`; the source Git blob, source SHA-256, runtime-template hash, ABI,
   selectors and layouts remain unchanged. Both frozen-binding records now pin the reviewed artifact.

### Remaining work before deployment

1. Independent re-review of the remediated authority boundary and the Base legacy constructor values.
2. Base fork/census qualification and the all-assets runbook: activate the validated RIPE and LP
   wind-down terms together, migrate bounded user batches, restore and read back both configurations,
   then lift the target/Teller pause.
3. Re-prove ordinary-claim reward liveness and per-user collateral parity on the Base fork. Ledger
   and CreditEngine must remain active for the per-user final housekeeping call; prove same-action-
   block preconditions and healthy debt for every manifest user before submission.
4. Bind deployment evidence that SwitchboardEcho is Switchboard id 5, the CCIP pools receive RipeHQ
   ids 23 and 24, and VaultMigrator receives RipeHQ id 25 before activation; no live RPC check against
   the replaced MissionControl is required.
5. Production deployment/replacement sequencing and address evidence. The published WIP branch does
   not imply deployment, registry update or activation authority.
6. Lootbox is now pinned at 23,131 bytes after the terminal-dust review remediation. Re-measure
   every future Lootbox change and preserve the independent 20-byte minimum-margin floor.

### Eventual removal boundary

After Base legacy migration completes, delete only the Base-specific legacy constructor binding,
legacy migration batch, snapshots/checks/events, and Lootbox legacy precision
exception. Keep VaultMigrator's ordinary vault and exporter-capable RipeGov paths, Addys/RipeHQ id
25, the ordinary Lootbox claim cleanup path, and the permanent Lootbox/Ledger no-forfeiture fixes.

---

## Historical pre-VaultMigrator snapshot

Everything from historical §0 through §9 below describes the superseded oversized-Teller candidate.
Use it for rationale only, not for current file ownership, status, next steps or rejected architecture.

---

## 0. Strategic context — read this first, it changes what "good" looks like

**This codebase is shared across chains.** One repo, per-chain deployments.

**The legacy migration is transitional.** The owner's stated plan: deploy a Teller carrying the
legacy migration on Base, run the migration, then replace it with the forward-looking Teller and
**delete the legacy migration code from the repo**. The "forward-looking Teller" already effectively
exists — it is `rh`'s Teller plus the shared fixes in §5.2 and §5.3.

Three consequences that should govern every decision on this branch:

1. **Two classes of change live here, and they have opposite lifetimes.**

   | Class | Commits | Lifetime |
   |---|---|---|
   | **Permanent, shared, all chains** | `74e7215` (Lootbox reward fixes), `4e64563` (Ledger multi-asset fix) | Keep forever |
   | **Transitional, Base-only** | `2bc618f`, `5d9894c`, `848fc04` (legacy migration path) | Delete after Base migrates |

   Whoever removes the legacy migration later must keep the first class. The commits are cleanly
   separated for exactly this reason — preserve that separation.

2. **Do not permanently refactor shared production code to make room for transitional code.**
   This retires the earlier "move unrelated Teller functionality into TellerUtils" idea as the
   preferred fix for §5.1. It would leave shared Teller permanently restructured to accommodate code
   that is scheduled for deletion. Prefer trimming the transitional path instead — and since the
   migration Teller is itself transitional and supervised, the 300-byte safety floor is arguably not
   required for that deployment (it needs to fit, not to have room to grow).

3. **Keep the legacy code cleanly separable.** Removal should be a delete, not surgery. Note the
   tension this creates with `5d9894c`, which merged the legacy path *into*
   `migrateRipeGovPosition` to recover 745 bytes: that trade bought size now at the cost of later
   separability. If the size problem is solved another way, consider reverting to a standalone
   function purely so the eventual deletion is trivial and low-risk.

Everything below reflects the state as built. Where §0 conflicts with an earlier recommendation
in §5 or §6, §0 wins.

---

## 1. What this branch does

The deployed Base legacy RipeGov vault (`0xe42b3dC546527EB70D741B185Dc57226cA01839D`, VaultBook id
**2**) must be wound down and its positions moved to a new gov vault. It predates the migration
exporter and **cannot be changed**, so the standard `exportPositionForMigration` route is unavailable.

This branch adds a legacy migration path that synthesizes the record from the source vault's own
public state, drains it through its ordinary `SharesVault` withdrawal, and imports through the
existing importer — plus the safety work that path requires.

Along the way it fixes **three defects that affect `rh` today**, independent of Base (§5.2–5.4).

---

## 2. Provenance and history

The branch was originally cut from `master` and later rebuilt on `rh`. That rebuild is why it is
much smaller than it once was.

**Why `rh` and not `master`:** `rh` had already solved the "vault id 2 is hardcoded" problem
generically, via `MissionControl.coreRipeGovVaultId()`, threaded through Lootbox, HumanResources,
SwitchboardAlpha, SwitchboardBravo, SwitchboardCharlie and BondRoom. On `master` this branch had to
change 7 files; on `rh` it changes 5, and `HumanResources.vy` / `SwitchboardAlpha.vy` need **no
change at all**.

The superseded master-based candidate is preserved at tag **`base-gov-migration-premaster-725f578`**.
Keep it until §5.1 (the MissionControl assumption) is verified — if that assumption fails, that
candidate is the fallback shape.

---

## 3. Commits, and why each exists

| Commit | What | Why |
|---|---|---|
| `2bc618f` | Port onto `rh` | Rebuild on the branch that already resolves the gov vault dynamically. Drops 2 files entirely. |
| `74e7215` | Lootbox: remove two reward-forfeiture paths | Two live defects that silently redistributed value away from small/exiting holders. §5.2 |
| `4e64563` | Teller: don't drop the whole source Ledger entry after one asset | Multi-asset defect that could push a borrower toward liquidation. §5.3 |
| `6a904de` | Drop three Teller immutables, restore constructor | The added constructor args broke every test fixture; they were also the wrong design on this base. §4.4 |
| `5d9894c` | Merge legacy migration into `migrateRipeGovPosition` | Deduplicate; recovered 745 bytes toward the EIP-170 gap. §4.5 |
| `848fc04` | Remove housekeeping the freeze guarantees would revert | Both legacy paths asserted a precondition that made their own final step revert. §5.4b |
| `25cfe08`, `7f7c380` | This document | Handoff. |

---

## 4. Design decisions, and the reasoning behind them

### 4.1 The legacy validator is deliberately **asymmetric**

`validateRipeGovMigration` (upstream) requires **both** endpoints paused. Base cannot use that: the
legacy vault has no exporter, so the migration uses its ordinary `SharesVault` withdrawal, which
asserts `not vaultData.isPaused`. So `validateLegacyRipeGovMigration` requires **source unpaused,
target paused**. Do not "fix" this to match upstream.

### 4.2 Source Ledger participation is retained until full cleanup

A Base user may hold both RIPE and the Aero LP. The migration never removes source Ledger
participation; `Lootbox.settleAndCleanupMigratedSource` removes it only after every asset, reward
and registration is gone. This is also now true of the upstream path (§5.3).

### 4.3 A Teller pause alone does **not** freeze the legacy vault

`TellerUtils._assertExclusiveFreeze` requires **Teller, AuctionHouse, CreditEngine, HumanResources
and Deleverage** all paused, asserted on both the migration and settlement paths.

The deployed legacy vault keeps its pre-migration permissions, so it authorizes AuctionHouse and
CreditEngine on `withdrawTokensFromVault` / `transferBalanceWithinVault`, HumanResources on the
contributor routes, and any valid Ripe department on `updateUserGovPoints` / `adjustLock` /
`releaseLock`. **Deleverage is named explicitly** because it is reachable from a switchboard, checks
only its *own* pause flag, and then withdraws through AuctionHouse against a caller-supplied vault.

### 4.4 No deploy-bound migration immutables

An earlier revision bound the legacy vault address, the LP asset and a migration-control id as
constructor immutables. All three are gone:

- legacy vault → resolved from VaultBook at id 2;
- control id → `addys._isSwitchboardAddr(msg.sender)`, matching upstream;
- LP asset → `verifyLegacyRipeGovSettlement` walks the source vault's own `vaultAssets` list.

That last change also **closed an open item**: the deprecated pool is covered by enumeration rather
than deferred to the census. Teller's constructor is back to `(_ripeHq, _shouldPause)`, so **no test
fixture changes are required**.

### 4.5 One migration entry point, not two

`migrateRipeGovPosition` branches on `_sourceVaultId == LEGACY_RIPE_GOV_VAULT_ID`. Only source
acquisition and validation differ; receipt check, import, depletion asserts, target Ledger
registration, Lootbox points and the event are shared. The legacy branch additionally runs
`verifyLegacyRipeGovImport`. It deliberately runs **no** debt-health housekeeping — see §5.4b.

---

### 4.6 Complete change inventory

Every change in this PR, with its rationale. **T** = transitional (delete when the legacy migration
is removed, §0.1 and §11); **P** = permanent, shared, all chains.

#### `contracts/vaults/RipeGov.vy` (+10)

| Change | Why | |
|---|---|---|
| `assert not vaultData.isPaused` on `updateUserGovPoints`, `adjustLock`, `releaseLock` | All three reach `_updateGovPointsForUserAsset`, which rewrites `unlock` and `lastTerms` from the *current* asset config **unconditionally** — the accrual-disable flag gates only the points. Under live wind-down terms that destroys the preserved unlock an import just wrote. These were the only gov-data mutators not already pause-gated; deposit/withdraw/transfer are gated inside `SharesVault`. | P |

#### `contracts/core/TellerUtils.vy` (+255)

| Change | Why | |
|---|---|---|
| `_assertExclusiveFreeze` | Teller's pause alone does not close the legacy vault. §4.3 | T |
| `validateLegacyRipeGovMigration` | Asymmetric endpoint validation — source unpaused, target paused. §4.1 | T |
| `getLegacyRipeGovSourceSnapshot` | Captures the complete original record *before* the withdrawal destroys it, and computes pending gov points **through this block** using the source vault's own `getLatestGovPoints` with the original terms/unlock/last-update/shares. Off-chain manifest values are evidence, never the execution input for a time-sensitive number. Also captures the target's point totals pre-import so the import's effect is checked as an exact delta. | T |
| `verifyLegacyRipeGovImport` | Post-import sweep: source depletion, source registration and Ledger membership retained, exact target shares/registration/points/unlock/terms, and exact deltas on both target point totals. | T |
| `verifyLegacyRipeGovSettlement` | Post-settlement sweep, including walking the source vault's own `vaultAssets` list to prove no residual deposit points remain on any supported asset. §4.4 | T |
| `interface SourceVault` (`vaultAssets`, `numAssets`) | Vault-level asset enumeration, which is what makes the residual-points check complete rather than a hardcoded asset pair. | T |
| `MAX_SOURCE_VAULT_ASSETS = 21` | Bound for that walk (1-based index, so cap + 1). Fails closed if the vault's asset list exceeds it, rather than silently checking a prefix. | T |
| `struct UserDepositPoints`, `GovData`, `LegacySourceSnapshot` | Mirrors of `Ledger.UserDepositPoints` and `RipeGov.GovData`. Duplicated because **each contract is its own compilation unit** and this work may not add a shared file under `interfaces/`. Keep them byte-identical to their originals. | T |
| Interface additions (`ripeGovVaultConfig`, `RipeGovVault` reads, `Ledger` reads), `cs` import | Support the above. | T |

#### `contracts/core/Lootbox.vy` (+248/−54)

| Change | Why | |
|---|---|---|
| `_calcSpecificLoot` takes raw point counts instead of a basis-point share | Removes the quantisation that floored any holder under 0.01% of an asset's points to a zero payout. §5.2 | P |
| External `calcSpecificLoot` forwards `HUNDRED_PERCENT` as denominator | Keeps that view's ABI **and** behaviour byte-identical, so its existing expectations still hold. | P |
| `_getDepositLootData` computes categories into locals and commits atomically; new `_isCategoryBlocked` | The old `didReceiveLoot` OR cleared the single shared `balancePoints` backing all three pools. Also fixes partial pool mutations that were written inline *before* the OR was evaluated. §5.2 | P |
| `_flushDepositPoints` removed, `_shouldFlush` plumbing removed | It zeroed points while paying nothing. Points never blocked `deregisterUserAsset` (that only checks balance), so its stated rationale did not hold. §5.2 | P |
| Claim loop defers deregistration until entitlement is gone | `claimDepositLootForAsset` is department-gated, so points on a deregistered asset are unrecoverable by the user. §8 | P |
| Precision divisor exempts `LEGACY_RIPE_GOV_VAULT_ID` as well as `_coreRipeGovVaultId` | The legacy vault's positions stay enumerable and claimable until settled. Without the exemption its governance loot share is divided by `assetPoints.precision` (1e9 for an 18-decimal asset) for the whole window. **Must be removed with the legacy code (§11).** | T |
| `settleAndCleanupMigratedSource` | Administrator settlement/cleanup; the only route that may remove source Ledger participation, and only after every asset, reward and registration is gone. Settles depleted assets only, leaving still-positive ones untouched. | T |
| `MAX_SOURCE_ASSET_INDEX = 21` | Bound for the per-user source enumeration; fails closed above the cleanup cap rather than cleaning a prefix. | T |
| `MigratedSourceAssetSettled`, `MigratedSourceAssetDeregistered`, `MigratedSourceSettledAndCleaned` | Per-asset reconciliation — the summary counts alone cannot prove *which* assets were cleaned. | T |
| `Ledger.isParticipatingInVault` added to interface | Used by the settlement pre/post-conditions. | T |

#### `contracts/core/Teller.vy` (+177/−16)

| Change | Why | |
|---|---|---|
| `Ledger.removeVaultFromUserForMigration` call **and** interface line removed | Multi-asset defect. §5.3 | P |
| `migrateRipeGovPosition` branches on `_sourceVaultId == LEGACY_RIPE_GOV_VAULT_ID` | One entry point for both sources. §4.5 | T |
| No debt-health housekeeping on either legacy path | The freeze requires CreditEngine paused, which would make it revert. §5.4b | T |
| ~~`activeMigrationAsset` storage + `setLegacyRipeGovMigrationAsset`~~ | **Removed in the three-use-case simplification.** The asset was already an explicit legacy-batch argument; the extra governance latch weakly modeled a runbook without proving configuration restoration. | removed |
| `settleAndCleanupLegacyRipeGovSource` | Teller-side wrapper for the Lootbox settlement; exists in Teller only because the Lootbox function is Teller-gated (see §5.1 lever 3). | T |
| `LEGACY_RIPE_GOV_VAULT_ID = 2` constant, `LegacySourceSnapshot` struct | Legacy binding and the snapshot mirror. | T |
| `LegacyRipeGovPositionMigrationExecuted` | Per-user legacy reconciliation. The separate asset-window event was removed with its setter. | T |
| Interface additions (4 × TellerUtils, `MissionControl.isSupportedAssetInVault`, `Lootbox.settleAndCleanupMigratedSource`) | Support the above. | T |

#### `contracts/config/SwitchboardEcho.vy` (+108)

| Change | Why | |
|---|---|---|
| `migrateLegacyRipeGovPositions` | The sole governance-facing Base legacy function. It follows the other two migration shapes: bounded batch, explicit asset, per-user event and return count. | T |
| Wrapper carries **no** source/target ids and no recipient | VaultMigrator binds the immutable legacy source and resolves the target from `coreRipeGovVaultId`; the explicit asset is fully revalidated on every call. Keeps the batch from becoming an arbitrary token-moving primitive. | T |
| `MAX_LEGACY_MIGRATIONS = 25` | Hard ceiling, not a target size — the operational batch limit is measured on the fork and will be lower. | T |
| `legacyUserDedupe` transient map | A repeated user hits the target's replay protection on the second row and reverts the whole batch after burning every preceding row's gas. Rejected up front with a specific reason. Uses the transient-dedupe pattern already in `SwitchboardAlpha`. | T |
| One legacy `…Executed` event | Per-user reconciliation; ordinary and exporter-capable paths have their own events. | T |
| `MissionControl.coreRipeGovVaultId` added to interface | Echo resolves the target id to pass to the merged entry point. | T |

---

## 5. Open issues

### 5.1 🔴 BLOCKER — Teller exceeds EIP-170 by 1,898 bytes

Everything else is downstream of this.

| Contract | rh baseline | This branch | Headroom |
|---|---:|---:|---:|
| **Teller** | 24,247 | **26,474** | **−1,898** |
| Lootbox | 22,091 | 24,539 | +37 |
| RipeGov | 24,522 | 24,540 | +36 |
| SwitchboardEcho | 22,912 | 24,081 | +495 |
| TellerUtils | 11,900 | 18,207 | +6,369 |

Teller must shed **1,898 bytes** to fit. The project's 300-byte safety floor would make it 2,198 — but per §0.2 that floor is arguably not required for a deployment that is itself transitional and scheduled for replacement. Confirm with the owner before relying on the lower target.

**This also blocks all testing.** Boa cannot deploy an over-size contract, so the fixture chain dies
with `RuntimeError: Contract address is not set` and *every* test errors. The same tests pass on an
unmodified `rh` baseline. So the Lootbox and Ledger fixes below are currently **unverified**.

Levers, with estimates:

1. Collapse `validateLegacyRipeGovMigration` + `getLegacyRipeGovSourceSnapshot` into a single
   TellerUtils call. Mechanical, ~150–250 bytes, no safety loss. **Do this regardless.**
2. Shrink or drop `verifyLegacyRipeGovImport` — a 10-argument staticcall carrying a 7-field struct,
   the most expensive thing left in the legacy branch. Worth a few hundred bytes, but it is
   post-condition safety that review specifically asked for. Owner decision.
3. **Historical lever, resolved.** Move the settlement path and operational state out of Teller.
   `Lootbox`'s
   `settleAndCleanupMigratedSource` is gated on `msg.sender == addys._getTellerAddr()`, which is the
   *only* reason `settleAndCleanupLegacyRipeGovSource` lives in Teller — settlement needs no Teller
   privilege otherwise. Re-gate it to `addys._isSwitchboardAddr` and the whole path (plus
   legacy state could move to SwitchboardEcho, which had 495 bytes free. The final architecture
   instead centralized migration policy in VaultMigrator, removed eager settlement, and later removed
   the redundant active-asset state entirely. This preserved the intended outcome and,
   unlike option 4, it removes transitional code from shared Teller rather than adding permanent
   scars to it. Unverified estimate; measure before committing to it.
4. **Move unrelated existing Teller functionality into TellerUtils** (6,369 bytes free). Definitely
   closes the gap, but **discouraged by §0.2** — it permanently restructures shared production code
   to accommodate code scheduled for deletion. Last resort, owner sign-off required.

Constraint that rules out the obvious alternative: the migration driver **must carry Teller's
identity**, because the deployed legacy vault gates withdrawal on `addys._getTellerAddr()`. A new
department cannot drive it. A temporary Teller adapter is prohibited by the controlling plan unless
the owner explicitly reopens it.

### 5.2 🟠 Lootbox reward fixes are unverified — and change RH's live behaviour

`74e7215` fixed two forfeiture paths in **shared** code:

- **Precision.** `userShareOfAsset` was quantised to basis points, so any holder under 0.01% of an
  asset's points was floored to a zero payout. `_calcSpecificLoot` now applies the ratio directly.
  The external `calcSpecificLoot` keeps its old signature and forwards `HUNDRED_PERCENT`, so its
  behaviour and ABI are unchanged.
- **Cross-category erasure.** `didReceiveLoot` was an `or` across three reward pools but cleared the
  single shared `balancePoints` backing all of them. Categories are now computed into locals and
  committed **atomically**; if any attributable category pays nothing, the whole claim defers
  without mutating state.
- **Flush removed.** It zeroed points while paying nothing. Points never blocked
  `deregisterUserAsset` (that only checks balance), so the "storage optimization" rationale did not
  hold.

**Behaviour changes to be aware of:** payouts shift **upward** for small holders and
`ripeAvailForRewards` draws down marginally faster — a distribution change, not purely a bug fix.
Claims now **defer** rather than partially pay and forfeit; a funded dust-level bucket can stall a
live claim until it becomes payable. An empty category blocks only while it has nonzero allocation,
active emissions and remaining reward budget; a structurally inactive category resolves at zero and
cannot freeze another funded category.

`tests/core/lootbox/test_loot_deposit_points.py` exercises this math directly. **Any expectation that
moves must be justified as the intended new behaviour, not fitted to make red go green.**

### 5.3 🟠 Ledger fix is unverified — and changes RH's qualified migration flow

`4e64563` removed an unconditional `Ledger.removeVaultFromUserForMigration` call from
`migrateRipeGovPosition`. It asserted depletion of only the **migrated** asset, then removed the
user's **entire** source-vault entry.

For a user holding two governance assets, the remaining position stayed physically in the vault but
left `Ledger.userVaults` — the enumeration `CreditEngine._getUserBorrowTerms` walks to compute
`collateralVal` / `totalMaxDebt`, and `AuctionHouse` walks to seize collateral. Health degraded with
nothing to revert it, and a liquidation could not even see the asset to take it.

RH has both RIPE and the RIPE/WETH LP, so this is reachable there. RH's migration suite should be run
against this change.

### 5.4 🟡 `migrateRipeGovPosition` runs no housekeeping on the upstream path

Neither branch runs debt-health housekeeping — the legacy one cannot (§5.4b), and the upstream one
never did. Its value would be catching a config mismatch if the target vault has different
collateral parameters than the source. For the upstream path (no freeze, so CreditEngine is not
paused) adding it is technically possible, but could make migrations revert for already-unhealthy
users. **Deliberately not changed. Owner decision.**

### 5.4b 🟠 No on-chain debt-health check is possible during the freeze

Fixed in `848fc04`, but the consequence is permanent and must be carried into qualification.

`_assertExclusiveFreeze` requires **CreditEngine paused**. `CreditEngine.updateDebtForUser` asserts
`not deptBasics.isPaused`. So any `_performHousekeeping(..., _shouldUpdateDebt=True)` on a legacy
path reverts unconditionally — both legacy paths originally did exactly that and **could never have
succeeded**. This was invisible because §5.1 prevents the suite from deploying Teller.

The freeze and an on-chain health assertion are therefore mutually exclusive by construction. Health
now rests on two structural arguments that **the fork must prove**:

1. no liquidation can occur during the window, because the protocol is frozen; and
2. the migration preserves collateral — the position moves between two vaults the user is enumerated
   in — **provided the target vault's MissionControl collateral parameters match the source's**.

Point 2 is the one that can silently fail. If the target vault is configured with a different LTV,
liquidation threshold or redemption threshold, a user's borrowing power changes across the migration
with nothing on-chain to catch it. **Fork qualification must assert collateral parity per user,
before and after.**

### 5.5 🟡 The MissionControl redeploy assumption is unverified

This entire design assumes Base gets a **redeployed MissionControl** carrying
`coreRipeGovVaultId()`. That is why `HumanResources.vy` and `SwitchboardAlpha.vy` need no change.

The deployed Base MissionControl is understood to **revert** on `coreRipeGovVaultId()`, but this has
never been checked against live Base state. It needs one RPC read. If it fails, four files come back
and the shape reverts toward tag `base-gov-migration-premaster-725f578`.

`coreRipeGovVaultId` is set via **SwitchboardCharlie** (see `SwitchboardCharlie.vy`, which reads the
previous value when changing it) — that contract is therefore also in the deployment path.

### 5.6 🟡 Preconditions that must be discharged before deployment

- **Pending state** in HumanResources, SwitchboardAlpha and SwitchboardEcho must be proved empty as a
  hard replacement precondition, or a reseed mechanism is needed.
- **Reward liveness.** The settlement fails closed if an entitlement cannot be paid in full. "Retry
  when the buckets grow" is not a completion guarantee — the census must prove every manifest user
  can reach a payable state.
- **Serial wind-down.** Each call validates its explicit asset, but on-chain code does not claim to
  prove operational sequencing. Restoring MissionControl terms and reading them back is a **runbook**
  invariant: finish all batches for asset A → restore A → read back and compare against the pinned
  baseline → begin asset B. Fail closed at each step.
- **Target pause window.** The target must stay paused from registration until every migration
  completes. HR resolves the target from registration onward, so during that interval a contributor's
  real position is still in the legacy vault; every HR mutating path routes into the paused target
  and reverts, which is what keeps HR inert.
- **Trusted-producer outage.** BondRoom and Stability Pool RIPE deposits revert for the whole window.
  Intended, but must be in the measured outage.

### 5.7 🟢 RipeGov headroom is 36 bytes

Not caused by this branch — `rh`'s own RipeGov baseline has only **54** bytes free. That contract is
effectively frozen. This branch adds 10 lines (pause gates) and leaves 36.

---

## 6. Next steps, in order

1. **Verify §5.5** — one RPC read against live Base MissionControl. Cheap, and it determines whether
   the current branch shape is even correct. Do this first.
2. **Close §5.1.** Lever 1 unconditionally; then lever 3 with owner sign-off. Nothing else can be
   validated until Teller deploys.
3. **Run the suites** once Teller fits: `tests/core/lootbox/`, `tests/core/teller/`,
   `tests/vaults/test_ripe_gov_vault.py`, plus RH's migration tests. Compare against an `rh` baseline
   worktree — several expectations will legitimately move (§5.2).
4. **Decide §5.4.**
5. **Discharge §5.6** as part of census/runbook work.

---

## 7. Reproduction

### Sizes

```bash
vyper -f bytecode_runtime contracts/core/Teller.vy | tr -d '\n0x' | wc -c
```

Deployed size = runtime template + **32 bytes per immutable** (own declarations *plus* every
initialized module). Immutables by module: `Addys` 1, `DeptBasics` 2, `LocalGov` 3, `TimeLock` 2,
`Contributor` 3, `VaultData` 0, `SharesVault` 0. Teller/Lootbox/TellerUtils have 3 each; RipeGov 1;
SwitchboardEcho 5. **Never pass a global `-O`** — `pragma optimize codesize` is in-file on Teller,
Lootbox and SwitchboardAlpha only.

### Tests

The sandbox blocks titanoboa's `~/.cache` write, which aborts collection. Use an out-of-repo plugin:

```bash
cat > /tmp/boacache.py <<'EOF'
import os
from boa.interpret import set_cache_dir
set_cache_dir(os.environ["RIPE_BOA_CACHE"])
EOF
env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp RIPE_BOA_CACHE=/tmp/boa \
  ETHERSCAN_API_KEY=local-placeholder \
  python3 -m pytest tests/core/lootbox/ -q -p no:cacheprovider \
  -p no:unraisableexception -p boacache
```

For a baseline comparison use `git worktree add --detach <dir> origin/rh` — **never `git archive`**
(no `.git` produces ~90 spurious failures).

---

## 8. Landmines — non-obvious facts that cost time to find

- **`_reduceBalanceOnWithdrawal` does not deregister.** It zeroes the balance and returns
  `isDepleted`. So after a migration the asset stays *registered* with a zero balance. This means
  `numUserAssets <= 1` is **not** a valid "fully exited" predicate on the migration path.
- **`claimDepositLootForAsset` is department-gated** (`_isValidRipeAddr`), not user-callable. Points
  left on a deregistered asset are therefore unrecoverable by the user — which is why cleanup now
  waits for the entitlement to be gone.
- **`SharesVault` pause-gates deposit, withdrawal and transfer** (lines 31/56/80). A paused target
  rejects ordinary deposits, so the trusted-producer path reverts rather than corrupting state. The
  real freeze holes were `updateUserGovPoints` / `adjustLock` / `releaseLock`, now pause-gated.
- **`_updateGovPointsForUserAsset` rewrites `unlock` and `lastTerms` unconditionally.** The
  gov-point-accrual-disable flag gates only the *points*. Under live wind-down terms that would
  destroy a preserved unlock.
- **`rh`'s Ledger re-added `removeVaultFromUserForMigration`.** Base must not depend on it — the
  deployed Base Ledger does not have it, and Ledger is not being redeployed. After `4e64563` Teller
  no longer references it at all.
- **Vyper 0.4.3:** member access cannot be chained onto a `staticcall` expression, and `log` argument
  order must match the event declaration order.

---

## 9. Rejected approaches — do not re-tread

| Approach | Why rejected |
|---|---|
| Use `migrateRipeGovPosition` unchanged for Base | Requires both endpoints paused; the legacy source has no exporter and must stay unpaused. |
| A new department as the migration driver | The deployed legacy vault gates withdrawal on `addys._getTellerAddr()`. Only Teller's identity works. |
| AuctionHouse / CreditEngine as the exporter | Prohibited by the controlling plan. |
| Temporary Teller adapter | Prohibited unless the owner explicitly reopens it. |
| `numUserAssets <= 1` as the "fully exited" predicate | Export does not deregister — see §8. |
| Deploy-bound migration immutables | Broke every fixture and diverged from how this base resolves everything else. §4.4 |
| Keeping the Base-only settleability helpers | Subsumed by the shared per-category guard in `74e7215`; removing them is what got Lootbox under EIP-170. |

---

## 10. Controlling documents

`docs/chains/base/ripe-gov-vault-migration/decision-plan.md` and `implementation-handoff.md` govern
this work. **They are untracked** in the `/Users/wigglez/dev/ripe-protocol` worktree and are not on
this branch — read them from there if available. Note the branch has since departed from the
handoff's original phase structure by explicit owner direction: compiling, size checks, pushing, PR
creation, reopening the Ledger prohibition, and folding shared-code changes into this PR were all
authorized after the fact.

---

## 11. Removal checklist — when the legacy migration is deleted

Per §0, the transitional code comes out once Base has migrated and the forward-looking Teller is
deployed. Delete everything marked **T** in §4.6. Specifically:

- **`RipeGov.vy`** — keep the three pause gates. They are marked **P**: they close a real hole
  independent of the migration.
- **`Lootbox.vy`** — remove `LEGACY_RIPE_GOV_VAULT_ID` and **the legacy arm of the precision-divisor
  exemption** (`_vaultId != LEGACY_RIPE_GOV_VAULT_ID`). The eager settlement function, its three
  events and its bound have already been removed. Do **not** touch the reward-math changes or the
  ordinary claim cleanup path — `_calcSpecificLoot`, `_isCategoryBlocked`, the atomic commit, the
  flush removal and the claim-loop deregistration gating are all **P**.
- **`VaultMigrator.vy`** — remove the Base-only constructor binding, chain/vault binding checks,
  exclusive-freeze helper, legacy migration batch, legacy snapshot/import
  validation and legacy events. Keep the ordinary vault and exporter-capable RipeGov paths.
- **`Teller.vy`** — remove only the legacy-specific branch/argument from the thin RipeGov source
  identity step if it is no longer used. Keep the Ledger-removal deletion (**P**) — do not reinstate
  `removeVaultFromUserForMigration`.
- **`SwitchboardEcho.vy`** — remove the two remaining Base-only legacy wrappers and their interface
  lines; keep the ordinary vault and exporter-capable RipeGov governance surfaces.
- **This document** — delete it, or reduce it to a historical note.

Two cautions:

1. `5d9894c` merged the legacy path *into* `migrateRipeGovPosition`, so removal there is surgery
   inside a shared function rather than deleting a standalone one. Diff against `rh` at `9354d05`
   for the pre-merge shape of that function. See §0.3.
2. After removal, re-measure. Teller should return to roughly its `rh` baseline; if it does not,
   something transitional was missed.
