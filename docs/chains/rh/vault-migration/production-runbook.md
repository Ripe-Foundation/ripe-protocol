# Deposit-Vault Position Migration — RH Production Runbook

**Scope:** governance-operated migration of one user's entire balance of one ERC-20 asset from one
compatible registered deposit vault to another, via
`SwitchboardEcho.migrateVaultPositions` → `Teller.migrateVaultPosition`.

**Primary use:** replacing a Stability Pool. The same path supports compatible SimpleErc20 and
RebaseErc20 pairs. The core RipeGov vault is excluded by design and keeps its own separate
migration path (`Teller.migrateRipeGovPosition`).

This runbook documents operational procedure only. It authorizes no production transaction.
Execution, commit, push and deployment all remain separately owner-gated.

---

## 0. Hard operational constraints

These are properties of the deployed code, not preferences. Each is enforced on-chain and each has
a corresponding test in `tests/vaults/test_vault_migration.py`.

| constraint | why | consequence if ignored |
|---|---|---|
| Caller must be a registered switchboard | `Teller.migrateVaultPosition` asserts `addys._isSwitchboardAddr(msg.sender)` | call reverts `only switchboard allowed` |
| Echo wrapper is governance-only | `gov._canGovern` | call reverts `no perms` |
| **Teller must be paused** | migration is unavailable during ordinary operation | reverts `teller not paused` |
| **Both endpoint vaults must be UNPAUSED** | the ordinary deposit/withdraw internals assert `not vaultData.isPaused` | reverts `source vault paused` / `target vault paused` |
| Neither endpoint may be the current `coreRipeGovVaultId` | current-pointer exclusion rule | reverts `source is core ripe gov` / `target is core ripe gov` |
| Both endpoints must share `isStabVaultId` | prevents collateral ↔ non-collateral stability moves | reverts `stab vault mismatch` |
| Source must have Ledger participation | proves a real position exists | reverts `source vault missing from Ledger` |
| Source must fully deplete | partial migration is not supported | reverts `source position not depleted` |
| **At most one migration per user per action block** | see §0.1 | reverts `one action per block`, rolling back the entire batch |

### 0.1 One migration per user per action block — binding manifest rule

Every migration ends with `_performHousekeeping(_isHigherRisk=True, ...)`, which calls
`Ledger.checkAndUpdateLastTouch(user, shouldCheck=True)` whenever
`MissionControl.shouldCheckLastTouch()` is enabled. **RH enables it**
(`DefaultsRobinhood.shouldCheckLastTouch()` returns `True`).

That guard asserts `lastTouch[user] != actionBlock`. Therefore:

- A user may appear **at most once per action block**, across *all* batches in that block — not
  merely once per `(user, asset, source)` tuple.
- A user holding **N** assets in the source vault requires **N separate blocks**.
- Splitting a batch into several transactions within the same block does **not** help.
- Any prior Teller action for that user in the same block (including a trusted deposit) also
  stamps `lastTouch` and will block the migration.

**Manifest rule: deduplicate by USER, not by (user, asset, source).** Build one batch per block
containing each user at most once.

The existing RipeGov migration has no such constraint, because `migrateRipeGovPosition` does not
call `_performHousekeeping`. Do not carry RipeGov batching habits over to this path.

### 0.1a The generic path does not remove source Ledger participation

Unlike `migrateRipeGovPosition`, this path deliberately leaves the user's source-vault
participation in place with a zero balance. Ordinary `Lootbox` cleanup removes it on the user's
next `claimLoot`: zero-balance assets are deregistered from the vault, and a vault with no
remaining assets is dropped from the user. Expect migrated users to remain enumerated in the
source vault until then; this is temporary and harmless.

For reference, the RipeGov path removes participation immediately through
`Ledger.removeVaultFromUserForMigration`. That narrow helper authorizes only the current Teller
address and is unavailable while Ledger itself is paused. Teller proves that the source position
is empty before cleanup, proves the source Ledger entry was removed afterward, and only adds the
target Ledger entry when the user is not already participating there. Lootbox is not on this
migration cleanup route.

### 0.2 Trusted producers bypass the Teller pause

`Teller.depositFromTrusted` is intentionally **not** pause-gated. Pausing Teller therefore does not
freeze the endpoint vaults the way the RipeGov path's vault-pause does. Trusted producers must be
rerouted away from the source **before** the migration window opens, and re-checked after the
pause. This is a procedural control, not an on-chain one.

---

## 1. Bind the environment

1. Bind chain ID and snapshot block/hash.
2. Record current addresses for Teller, TellerUtils, SwitchboardEcho, VaultBook, MissionControl,
   Ledger, Lootbox and both endpoint vaults.
3. Record endpoint code hashes.
4. **Prove Teller and TellerUtils share the same RipeHq.** `Teller.migrateVaultPosition` delegates
   endpoint resolution to TellerUtils, which resolves its own address bundle from its own immutable
   RipeHq. Verify:
   - `Teller.getRipeHq() == TellerUtils.getRipeHq() == <expected RipeHq>`
   - both resolve the same Switchboard, VaultBook, MissionControl, Ledger and Teller addresses
   - both are the exact implementations the live registry pointers select

---

## 2. Prepare the target

5. Register and configure the target vault and asset through the normal governed path.
6. For a Stability Pool replacement: remove the source from liquidation/priority routes, set the
   target as preferred, and prove the target is absent from every liquidation route with an empty
   claimable basket.
7. For any vault type: identify every trusted producer and prove it no longer selects the source.
8. Verify neither endpoint is the current `coreRipeGovVaultId`, and that both endpoints have equal
   `isStabVaultId` values.

---

## 3. Open the window

9. **Pause Teller.** Keep both vaults **unpaused** — their deposit/withdraw internals require it.
10. Re-read all bound addresses and code hashes after the pause.

---

## 4. Build and prove the manifest

11. Discover holders from logs and reconcile against live source balances.
12. Sort and deduplicate the manifest **by user** (§0.1). Split into gas-safe batches.
    Twenty-five is an ABI ceiling, not a required batch size.
13. Fork-simulate every final Safe calldata batch against the bound snapshot. Reconcile source
    withdrawal, target deposit, Echo migration event, Ledger, Lootbox and debt health.

### Measured gas (local Boa, SimpleErc20 → SimpleErc20)

| users | total gas | per user |
|---:|---:|---:|
| 1 | 582,820 | 582,820 |
| 5 | 2,124,740 | 424,948 |
| 10 | 4,052,140 | 405,214 |
| 25 | 9,834,340 | 393,373 |

A 25-user batch fits comfortably inside a standard block envelope. Re-measure on the target chain
before signing; these are local-EVM figures, not chain-calibrated. Other pairings (Rebase,
Stability) cost more per user; size batches from a fork simulation of the actual pairing.

---

## 5. Execute

14. Execute a canary batch, reconcile it fully, then execute the remaining batches.
15. Repeat holder discovery and live reconciliation to catch late trusted deposits; migrate any
    residual positions before retiring the source.

The function moves the user's **entire live position at execution time**. A late trusted deposit is
therefore included in the migration, not treated as stale-manifest corruption.

---

## 6. Close out

16. Remove source support, then pause/retire the source, only after its economic positions are
    empty.
17. Do **not** call `Lootbox.resetAssetPoints` until all source rewards are claimed or a separate
    forfeiture policy is approved.
18. Unpause Teller only after independent pointer, route, supported-vault and residual checks.

---

## 7. Stability Pool specifics

A nonempty source claimable basket normally prevents full depletion: the withdrawal computes value
including claimables but can transfer only the stability asset, so `isDepleted` stays false and
Teller reverts.

**Clear and re-prove the basket before migrating. Never remove the `isDepleted` assertion to work
around it.**

---

## 8. Failure and recovery

Atomicity is the recovery mechanism. Any failure after the withdrawal reverts the withdrawal and
every metadata update, for the **whole Echo batch** — no partial batch can land, and no migration
event survives a reverted batch.

Successful calls are **not idempotent**: a replay finds no source balance and reverts. Re-running a
partially-successful plan is safe only because the successful entries now fail closed.

---

## 9. Trust boundaries

- Governance controls SwitchboardEcho calls; any registered switchboard can reach
  `Teller.migrateVaultPosition`. Keeping migration wrappers confined to Echo is a governance
  convention, not an on-chain guarantee.
- RipeHq and VaultBook registry changes follow their own governance/timelock processes.
- The current core pointer is the on-chain RipeGov exclusion boundary. Governance must not register
  and support an unpaused, non-core RipeGov as an ordinary deposit-vault endpoint. The rule is a
  current-pointer rule; it does not claim to identify every RipeGov bytecode.
- Operators must reroute trusted producers before pausing Teller (§0.2).
