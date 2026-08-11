# Deposit-vault position migration runbook

Scope: governance-operated, bounded migration of many users. For each user,
the migrator enumerates and moves every supported source asset in the same
transaction. The production call path is:

```text
governance
  -> SwitchboardEcho.migrateVaultPositions(users, sourceVaultId, targetVaultId)
  -> VaultMigrator.migrateVaultPositions(...)
  -> Teller withdrawal/deposit helpers
```

RipeGov uses the separate
`SwitchboardEcho.migrateRipeGovPositions(users, sourceVaultId)` route. The Base
legacy vault uses `SwitchboardEcho.migrateLegacyRipeGovPositions(users)`.
Operators do not call a `Teller.migrate*` function; no such public Teller
entrypoint exists.

This document describes procedure only. It authorizes no transaction,
deployment, registry update, or release.

## On-chain constraints

| Constraint | Operational consequence |
| --- | --- |
| Echo is governance-only | Submit the batch through the approved governance/Safe path. |
| VaultMigrator accepts only a registered switchboard | Calling VaultMigrator directly from an EOA reverts. |
| VaultMigrator is RipeHq id 25 | Read back the exact candidate at id 25; a deployment or manifest label without registry activation has no Teller authority. |
| VaultMigrator must be unpaused | Confirm its department state before the window. |
| Teller must be paused | Ordinary user actions are closed while its migration-only helpers remain available to VaultMigrator. |
| Generic source and target vaults must be unpaused | Their normal withdrawal/deposit accounting is reused. |
| Ledger and CreditEngine must remain unpaused | Per-user housekeeping and debt reconciliation run after a migrated user. |
| Source and target must be distinct valid VaultBook entries | Bind both registry IDs and addresses immediately before execution. |
| Historical RipeGov vaults are excluded from the generic route | Use only a dedicated RipeGov migration function; changing the current core pointer does not turn an old RipeGov into a generic vault. |
| Source and target must agree on Stability Pool classification | A generic move cannot cross the Stability/non-Stability boundary. |
| Every migrated asset must fully deplete at the source | A partial withdrawal reverts the entire batch. |
| The batch is atomic | A failure for a late user rolls back every earlier user in the transaction. |

The ABI ceiling is 25 users, not an instruction to submit 25. Select a batch
size from a fork rehearsal of the actual users, asset counts, vault types, and
chain gas limit.

## User and asset semantics

Deduplicate by user. One user appears at most once in a transaction, and one
call handles all supported source assets for that user. Do not split RIPE and
RIPE-LP into separate calls merely because they are distinct assets.

The migrator snapshots or reads the user's source positions before mutation,
skips unsupported target assets, and migrates supported positions atomically.
The returned count and events count positions, not users. A zero address or a
user with no eligible balance does not establish that the user census is
complete; reconcile every manifest row against live state.

`Ledger.checkAndUpdateLastTouch` still applies through housekeeping. Pause
Teller, then execute after a later action block and preflight `lastTouch` for
every user. A user action earlier in the same action block can revert the whole
batch even if the manifest itself contains no duplicate.

## Bind the environment

Record and independently verify:

1. chain ID, RPC identity, snapshot block number/hash, and Safe;
2. RipeHq, Switchboard, SwitchboardEcho, VaultMigrator, Teller, TellerUtils,
   Ledger, CreditEngine, Lootbox, MissionControl, VaultBook, source, and target
   addresses;
3. registry IDs, deployed runtime hashes, constructor immutables, pause states,
   and governance owners;
4. the complete historical-RipeGov ID set and the current
   `coreRipeGovVaultId`;
5. target asset support and source/target Stability classification; and
6. every trusted producer or alternate deposit route that can change a source
   position during the window.

Abort if any readback differs from the approved manifest. A source-code or
template hash is not a deployed-runtime identity when constructor immutables
exist.

For first activation, prove RipeHq ids 23 and 24 are the approved CCIP pools,
`numAddrs()` is 25 before the append, the confirmation returns 25, and
`getAddr(25)` equals the VaultMigrator candidate afterwards. Robinhood's
candidate must bind `(RipeHq, false, zero-address)` as its constructor inputs:
unpaused for the controlled window and with no Base legacy-vault address.

## Prepare the route

1. Register and fully configure the target through its normal timelocked
   governance path.
2. For a Stability Pool replacement, prove the target supports every selector
   used by liquidation, including `canAcceptLiquidationAsset`, and prove its
   claim-asset state is compatible with the move.
3. Remove or reroute trusted producers from the source.
4. Build the holder census from events and reconcile it to live source
   balances and Ledger participation.
5. Sort and deduplicate users. Record every eligible asset and every skipped
   asset with the exact reason.

For a Stability Pool, a nonempty claimable basket or custody deficit can make
full depletion impossible. Clear and reconcile the economic state through an
approved route; never remove the `isDepleted` assertion to force migration.

## Open and rehearse the window

1. Pause Teller.
2. Keep VaultMigrator, Ledger, CreditEngine, and the endpoint states required
   by the selected migration route available.
3. Wait for a later action block, then re-read every bound address, pause
   state, route, user `lastTouch`, balance, debt, and lock record.
4. Fork-rehearse the exact Safe calldata at the bound block. Include a canary,
   the maximum intended batch, a late-user failure, and a same-action-block
   failure.
5. Prove a late failure leaves all source/target balances, shares, locks,
   points, Ledger entries, Lootbox records, debt state, and events unchanged.

Do not extrapolate old single-asset gas measurements to the all-assets-per-user
implementation.

## Execute and reconcile

Execute a canary batch first. For every position, reconcile:

- exact source debit and target credit;
- Teller and VaultMigrator residual token balances;
- source depletion and target shares;
- Ledger participation and `lastTouch`;
- Lootbox point updates;
- debt and liquidation health; and
- emitted user/asset migration events.

Only then execute the remaining measured batches. After each batch, repeat the
live holder census. A late trusted deposit changes the live position and must
be included or explicitly blocked before source retirement.

A replay of a fully depleted user is normally a zero-position no-op, but that
does not make an unchecked batch idempotent: skipped, residual, newly added, or
partially eligible positions can produce a different result, and any late
failure remains atomic. Resume from reconciled chain state, not from a local
success log.

## RipeGov-specific rules

The generic route is never a substitute for RipeGov migration. Dedicated
RipeGov migration must preserve the original unlock, stored lock terms,
governance points, pending points, and accrual-disable state.

The pause matrix differs by dedicated route. A registered same-chain
`migrateRipeGovPositions` move requires both source and target RipeGov vaults
paused. The Base legacy route requires the legacy source unpaused and the new
target paused. Teller remains paused and VaultMigrator remains unpaused in
both cases. Bind the selected function and prove its exact matrix; do not carry
the generic unpaused-endpoint rule into a RipeGov batch.

For the Base legacy wind-down, governance may reduce the RIPE and RIPE-LP
minimum lock durations together by one block only after the census proves the
new minimum is below every migrating position's stored historical minimum.
The controlled sequence is:

1. pause Teller;
2. apply and confirm the approved lock-configuration change;
3. wait for the required action-block boundary;
4. call `migrateLegacyRipeGovPositions(users)` in gas-qualified multi-user
   batches; and
5. restore or advance configuration exactly as the approved migration plan
   specifies.

Changing the configuration does not authorize loss of the user's stored lock.
The target import must restore that original lock and terms.

## Closeout

Retire a source only after a second independent census proves no economic
position, claim, reward, debt dependency, or trusted producer remains.
Pause VaultMigrator to close the privileged migration window unless a separate
owner-approved operating policy keeps it available. Unpause Teller only after
that decision and all registry, route, accounting, and residual-token
readbacks match the approved post-migration manifest.

Keep the candidate deployment records, Safe transaction IDs, timelock action
IDs, fork evidence, per-batch receipts, and final reconciliation together. A
green aggregate test count or a local manifest update is not proof that a
registry activation occurred.
