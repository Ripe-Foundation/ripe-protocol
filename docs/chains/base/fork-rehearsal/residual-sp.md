# Post-cleanup Stability migration with governance residual

Fork-only; no live transactions. Snapshot: Base block 51,187,713, including the
owner’s live GREEN-claim cleanup. This block was not yet finalized at run start.
Defaults were regenerated at finalized block 51,187,177; the harness checks
carried configuration against the actual fork's live MC before proceeding.

During the combined run, Base finalized through block 51,187,742. A fresh
read of block 51,187,713 confirmed its hash still matches the report. Thus the
snapshot subsequently finalized unchanged; `snapshot_finalized: false` records
its status at run start, not the later confirmation.

## Controlled comparison

- Without a residual: 79 positions across 70 users moved; the last user,
  `0xf5E85494bA635F6C8B0B39709A998FB73eD61c34`, reverted with
  `source position not depleted`.
- With a governance residual: all 81 positions across 71 original funded users
  moved. Every completed user's current debt was unchanged. Underlying amount
  differences were between -2 and 0 wei, still flagged rather than called exact.
- Governance spent **0.1 GREEN** from its actual wallet to mint
  **0.099263666937123520 GREEN/USDC LP**, then deposited it in source vault 1.
  Curve minimum output was 99% of the simulated quote; token order and the
  existing minimum deposit were checked. No synthetic balances were supplied.
- Only governance's new LP position remains: **0.099263666937125639 LP-equivalent**
  at completion. All 11 claim-dust entries remain backed in the old pool.
  The old pool's other deposit asset has zero remaining shares.

The residual owner is governance Safe
`0xe488a42D33b3Af5d3E5Cd5680938d8369716D1bf`, which had no SP position beforehand.
Do not migrate this residual or deregister/decommission the old vault.
This proves the residual method on this snapshot; it is not a ready-to-sign
production transaction or a guarantee about a different ordering/state.

No Ledger clearing or contract change is required for this tested workaround.
The separately detected reward-continuity difference, final reward routing,
permissions replay, custody/HR handoffs and reopening checks remain outside
this isolated SP result.

[Per-user evidence](residual-sp-evidence.json).

## Completed combined all-vault run

The same fork subsequently completed the combined sequence: core compatibility
probe, fresh borrower audit, seven governance repayments plus the main-user
deleverage, all RipeGov moves, residual SP setup and moves, then ordinary vaults.

| Source vault | Original funded users | Positions moved |
| --- | ---: | ---: |
| Stability (1) | 71 | 81 |
| RipeGov (2) | 376 | 402 |
| Simple (3) | 31 | 40 |
| Rebase (4) | 0 | 0 |
| Underscore (5) | 39 | 45 |

All **568 original positions** moved; user counts overlap across vaults. Each
funded-user set and position count was independently reconciled against the
fresh census. RipeGov amounts and original locks matched. Ordinary-vault amounts
and current debt matched. SP current debt matched, with the same -2 to 0 wei
per-position underlying deltas. The governance residual is additional to these
568 original positions and stays behind by design.

[Combined evidence](combined-residual-evidence.json) includes per-user results,
the report digest and a fresh check that the snapshot finalized with the same
hash. No transaction execution error occurred. The overall report remains
`not_qualified` because of `REWARD_CONTINUITY_FAILED` and
`STABILITY_UNDERLYING_DRIFT`; completing position movement is not approval for
the remaining production cutover. In particular, final routing must prevent new
deposits/liquidations into the retained old SP without destroying its residual
position or custody. The rehearsal does not yet certify that final freeze.

To repeat the combined run, add `--legacy-probe --ordinary-probe` to the command
below. All calls remain fork-only; none of its newly deployed addresses should
be used as live deployment addresses.

```sh
python3 scripts/base_upgrade_fork.py \
  --block 51187713 \
  --defaults docs/chains/base/fork-rehearsal/Defaults.block-51187177.vy \
  --report /tmp/ripe-base-residual-trial.json \
  --census --probe --borrower-audit --remediate-blockers \
  --stability-probe --stability-residual
```

The original run additionally used `--allow-unfinalized-diagnostic` because the
cleanup was not finalized yet. Do not use that flag for production qualification.
