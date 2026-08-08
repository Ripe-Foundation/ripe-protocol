# Base Legacy RipeGov Migration — Branch State & Handoff

**Branch:** `codex/base-gov-migration-on-rh` · **PR:** #83 (draft) · **Base:** `rh` @ `9354d05`
**Status:** compiles, **not deployable**, **not tested** — Teller is 1,967 bytes over EIP-170, which
also blocks the test suite from running at all.

> Read this before touching the branch. It records what changed, *why*, what is still broken, and
> the non-obvious facts that cost real time to discover.

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
`verifyLegacyRipeGovImport` and `_performHousekeeping`.

---

## 5. Open issues

### 5.1 🔴 BLOCKER — Teller exceeds EIP-170 by 1,967 bytes

Everything else is downstream of this.

| Contract | rh baseline | This branch | Headroom |
|---|---:|---:|---:|
| **Teller** | 24,247 | **26,543** | **−1,967** |
| Lootbox | 22,091 | 24,539 | +37 |
| RipeGov | 24,522 | 24,540 | +36 |
| SwitchboardEcho | 22,912 | 24,081 | +495 |
| TellerUtils | 11,900 | 18,207 | +6,369 |

With the project's 300-byte safety floor, Teller must shed **~2,267 bytes**.

**This also blocks all testing.** Boa cannot deploy an over-size contract, so the fixture chain dies
with `RuntimeError: Contract address is not set` and *every* test errors. The same tests pass on an
unmodified `rh` baseline. So the Lootbox and Ledger fixes below are currently **unverified**.

Levers, with estimates:

1. Collapse `validateLegacyRipeGovMigration` + `getLegacyRipeGovSourceSnapshot` into a single
   TellerUtils call. Mechanical, ~150–250 bytes, no safety loss. **Do this regardless.**
2. Shrink or drop `verifyLegacyRipeGovImport` — a 10-argument staticcall carrying a 7-field struct,
   the most expensive thing left in the legacy branch. Worth a few hundred bytes, but it is
   post-condition safety that review specifically asked for. Owner decision.
3. **Move unrelated existing Teller functionality into TellerUtils** (6,369 bytes free). The only
   lever that definitely closes the gap. Touches production paths outside this workstream's scope
   and needs its own review. **Owner sign-off required.**

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

The legacy branch calls `_performHousekeeping(True, …)`; the upstream branch does not. With §5.3
fixed, collateral is preserved across a migration, so this would be a no-op safety net — its real
value is catching a config mismatch if the target vault has different collateral parameters than the
source. Adding it could make migrations revert for already-unhealthy users. **Deliberately not
changed. Owner decision.**

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
