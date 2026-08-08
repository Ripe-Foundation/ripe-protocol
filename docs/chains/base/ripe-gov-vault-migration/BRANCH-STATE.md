# Base Legacy RipeGov Migration — Branch State & Handoff

**Branch:** `codex/base-gov-migration-on-rh` · **PR:** #83 (draft) · **Base:** `rh` @ `9354d05`
**Status:** compiles, **not deployable**, **not tested** — Teller is 1,898 bytes over EIP-170, which
also blocks the test suite from running at all.

> Read this before touching the branch. It records what changed, *why*, what is still broken, and
> the non-obvious facts that cost real time to discover.

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
| `activeMigrationAsset` storage + `setLegacyRipeGovMigrationAsset` | One open asset window at a time, enforced close-before-open so no single transaction hands the window from RIPE to LP. Does **not** prove MissionControl terms were restored — that is a runbook invariant. §5.6 | T |
| `settleAndCleanupLegacyRipeGovSource` | Teller-side wrapper for the Lootbox settlement; exists in Teller only because the Lootbox function is Teller-gated (see §5.1 lever 3). | T |
| `LEGACY_RIPE_GOV_VAULT_ID = 2` constant, `LegacySourceSnapshot` struct | Legacy binding and the snapshot mirror. | T |
| `LegacyRipeGovMigrationAssetSet`, `LegacyRipeGovSourceSettled` events | Window and settlement observability. | T |
| Interface additions (4 × TellerUtils, `MissionControl.isSupportedAssetInVault`, `Lootbox.settleAndCleanupMigratedSource`) | Support the above. | T |

#### `contracts/config/SwitchboardEcho.vy` (+108)

| Change | Why | |
|---|---|---|
| `setLegacyRipeGovMigrationAsset`, `migrateLegacyRipeGovPositions`, `settleAndCleanupLegacyRipeGovSources` | Governance-only batch layer — without it the flow is unreachable. Follows the existing `migrateRipeGovPositions` shape: bounded array, per-row extcall, per-row event, return count. | T |
| Wrappers carry **no** source/target ids and no recipient | Teller binds the legacy source, resolves the target from `coreRipeGovVaultId`, and enforces the open asset window. Keeps the batch from becoming an arbitrary token-moving primitive. | T |
| `MAX_LEGACY_MIGRATIONS = 25` | Hard ceiling, not a target size — the operational batch limit is measured on the fork and will be lower. | T |
| `legacyUserDedupe` transient map | A repeated user hits the target's replay protection on the second row and reverts the whole batch after burning every preceding row's gas. Rejected up front with a specific reason. Uses the transient-dedupe pattern already in `SwitchboardAlpha`. | T |
| 3 `…Executed` events | Per-row reconciliation. | T |
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
3. **Move the settlement path and the asset window out of Teller entirely.** `Lootbox`'s
   `settleAndCleanupMigratedSource` is gated on `msg.sender == addys._getTellerAddr()`, which is the
   *only* reason `settleAndCleanupLegacyRipeGovSource` lives in Teller — settlement needs no Teller
   privilege otherwise. Re-gate it to `addys._isSwitchboardAddr` and the whole path (plus
   `setLegacyRipeGovMigrationAsset` and the `activeMigrationAsset` storage and getter) can move to
   SwitchboardEcho, which has 495 bytes free. **This is the most promising remaining lever** and,
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
Claims now **defer** rather than partially pay and forfeit; a dust-level bucket can stall a claim
until it refills (self-clearing; a zero-allocation category never blocks).

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
- **Serial wind-down.** On-chain only enforces close-before-open. Restoring the prior asset's
  MissionControl terms and reading them back is a **runbook** invariant: close window → restore terms
  → read back and compare against pinned baseline → open next. Fail closed at each step.
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
- **`Lootbox.vy`** — remove `settleAndCleanupMigratedSource`, the three `MigratedSource*` events,
  `MAX_SOURCE_ASSET_INDEX`, `LEGACY_RIPE_GOV_VAULT_ID`, and **the legacy arm of the precision-divisor
  exemption** (`_vaultId != LEGACY_RIPE_GOV_VAULT_ID`). Do **not** touch the reward-math changes —
  `_calcSpecificLoot`, `_isCategoryBlocked`, the atomic commit, the flush removal and the claim-loop
  deregistration gating are all **P**.
- **`TellerUtils.vy`** — the entire legacy block is **T**: `_assertExclusiveFreeze`, all four
  `…Legacy…` functions, `interface SourceVault`, `MAX_SOURCE_VAULT_ASSETS`, and the three mirrored
  structs. Check whether `cs` and the `RipeGovVault`/`Ledger` interface additions are still used by
  anything else before removing them.
- **`Teller.vy`** — remove the legacy branch inside `migrateRipeGovPosition`, `activeMigrationAsset`,
  `setLegacyRipeGovMigrationAsset`, `settleAndCleanupLegacyRipeGovSource`, `LEGACY_RIPE_GOV_VAULT_ID`,
  `LegacySourceSnapshot`, both `Legacy*` events, and the four TellerUtils interface lines. **Keep**
  the Ledger-removal deletion (**P**) — do not reinstate `removeVaultFromUserForMigration`.
- **`SwitchboardEcho.vy`** — the whole added block is **T**.
- **This document** — delete it, or reduce it to a historical note.

Two cautions:

1. `5d9894c` merged the legacy path *into* `migrateRipeGovPosition`, so removal there is surgery
   inside a shared function rather than deleting a standalone one. Diff against `rh` at `9354d05`
   for the pre-merge shape of that function. See §0.3.
2. After removal, re-measure. Teller should return to roughly its `rh` baseline; if it does not,
   something transitional was missed.
