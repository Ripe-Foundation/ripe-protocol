# Stability Pool migration diagnostic

Fork-only at Base block 51,135,337, with governance debt remediation first.
No live transactions, fabricated funding, or protocol source changes.

The other registered vaults are already covered by the previous complete
[vault-2–5 sweep](remediation.md): 487 positions. Vault 4 has no funded positions.
This additional run exercises the 82 funded Stability Pool positions separately;
it is not a claim that all five vaults completed in one combined run.

```sh
python3 scripts/base_upgrade_fork.py \
  --block 51135337 \
  --defaults docs/chains/base/fork-rehearsal/Defaults.block-51135337.vy \
  --report /tmp/ripe-base-stability-final.json \
  --census --probe --remediate-blockers --stability-probe
```

The probe appends target-vault membership, switches the preferred Stability
Pool to registered target 6, and migrates through governance Echo/VaultMigrator.
It records each immediately-before/after underlying amount and checks unchanged
current debt. Differences remain explicit qualification blockers; the diagnostic
continues after amount drift to expose subsequent execution failures.

Initial sweep: 64 positions across 57 users moved before an execution revert
for `0xF1133e9AeF370d8BD8a71abDd64ADbb9298b4f4F`. Earlier amount discrepancies
were 1–2 wei. This is not a successful complete Stability migration.

The legacy pool includes claim assets in its reported deposit value. The ordinary
migrator moves only the deposited ERC20, not the claim basket. Therefore a
successful early withdrawal does not establish that every remaining user can
exit or that the basket is preserved. No claim liquidation, governance purchase,
subsidy, or change to user entitlement is silently performed by this probe.

## Confirmed blocker

The repeated sweep confirms `dev: source position not depleted` in VaultMigrator.
The legacy withdrawal can return a partial withdrawal when the full NAV-backed
entitlement exceeds available deposited-token custody. The migrator correctly
refuses a partial exit and reverts the user's transaction. Earlier users received
deposited tokens against a NAV that includes the basket; the remaining shares
are increasingly backed by claim assets rather than liquid deposit tokens.

All 12 recorded claim-asset entries remain in the old pool, with zero received
by the target. The claim basket must be settled or explicitly migrated before
claiming a complete wind-down. This requires a separately reviewed strategy;
the rehearsal does not authorize selling claims or having governance buy them.

See [per-user evidence and failure state](stability-evidence.json). Of 82 funded
positions, 64 moved in this diagnostic; 18 are not completed. Current debt was
unchanged for each completed user. Nonzero underlying deltas were -1 or -2 wei
and remain flagged as `STABILITY_UNDERLYING_DRIFT`, not silently tolerated as
exact preservation. The unrelated reward-continuity blocker also remains.
