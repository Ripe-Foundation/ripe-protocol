# Governance debt remediation — Base fork

No live transactions were sent. The source state is Base block **51,135,337**;
the upgrade and remediation run locally after the simulated HQ timelock. All
calls use governance Safe `0xe488a42D33b3Af5d3E5Cd5680938d8369716D1bf` as caller.
No wallet funding was fabricated and no protocol contract code was modified.

## Requested deleverage

User: `0x28E2b238a3a7634C6C7e23b895790505B1C31Cd0`.

An ordinary `deleverageManyUsers` call from governance reverts. Governance is
not automatically a trusted caller, and this position does not qualify for
the untrusted deleverage route at the snapshot.

The successful tested sequence is:

1. Replay the user's original configuration into the replacement MC.
2. Through Charlie, temporarily grant governance `canBorrow` delegation, which
   also authorizes specific-asset deleverage. Preserve the other delegation bits.
3. Call Teller `deleverageWithSpecificAssets([(1, sGREEN, 10**18)], user)`.
4. Restore and verify the exact original delegation.

| Field | Before | After |
| --- | ---: | ---: |
| Debt (GREEN) | 295.390359294423333333 | 294.390359294423333333 |
| Vault-1 sGREEN | 268.343998732271985495 | 267.430174527712425923 |
| RIPE deposit | 686.115358927338975876 | unchanged |
| Original RIPE governance record / lock | original | unchanged |
| Debt health | failing | passing |

The deliberate sGREEN reduction is **0.913824204559559572**, repaying exactly
**1 GREEN**. This is not a subsidy from governance to that user.

## Seven full repayments

For each other address in `borrower-blockers.json`, the run replays the original
user configuration, temporarily enables third-party repayment, approves exactly
the current debt to the new Teller, repays it from governance, and restores the
original configuration. It verifies zero remaining debt and allowance, healthy
status, unchanged deposited amounts/governance records, and restored permission.

Total governance GREEN spent: **1.878963825205795738**.

Safe GREEN: **9.239380679435388320 → 7.360416854229592582**.

All seven repayments passed. The three previously failing RipeGov users and the
affected ordinary-vault users subsequently passed the isolated migration retries.

## Completed full position sweep

The subsequent sequential full sweep passed for all funded positions in vaults
2–5, with funded users and position counts reconciled against the pinned census:

| Source vault | Users | Positions | Verified at each move |
| --- | ---: | ---: | --- |
| RipeGov (2) | 376 | 402 | Underlying amount and original locks unchanged |
| Simple (3) | 31 | 40 | Underlying amount and current debt unchanged |
| Rebase (4) | 0 | 0 | No funded positions |
| Underscore (5) | 39 | 45 | Underlying amount and current debt unchanged |

Total: **487 positions**. User counts overlap between vaults. Amount comparisons
are immediately before/after each move, after the intentional debt remediation;
they are not a claim that old share rounding cannot change between users' moves.
Stability Pool vault 1 is not part of this sweep.

See [saved evidence](remediation-evidence.json) for every migrated user, repayment
results, source block/hash, harness hash and full-report digest. The full run
finished without an execution error, but remains `not_qualified` because of
`REWARD_CONTINUITY_FAILED`; final routes and reward restoration are not completed.

## Reproduction and limits

Historical reproduction only: [remediation-evidence.json](remediation-evidence.json) records contract source
`1ede38351e6da918806dff70d34b2066bf8cde8c` and harness SHA-256
`ba8cde187d788dc01c71d2d481be51cb56fe933beb5fc6b77756a9568b4e8f12`. Both must be bound; checking out the contract revision
alone does not recover the recorded harness. No matching harness body was found in the available tracked history; recover
and verify the original harness bytes before claiming an exact reproduction.
The current `compatibility_probe` rejects before its first simulated registry
mutation because its retained plan omits the compatible PriceDesk. For current
source use `scripts/base_full_update_fork.py` and the [current full-update scope](full-update-summary.md),
not the historical command below. Shared imports and `--help` remain supported.

```sh
python3 scripts/base_upgrade_fork.py \
  --block 51135337 \
  --defaults docs/chains/base/fork-rehearsal/Defaults.block-51135337.vy \
  --report /tmp/ripe-base-remediation-full-sweep.json \
  --census --probe --remediate-blockers --legacy-probe --ordinary-probe
```

This is not ready-to-sign production calldata. Fork deployment addresses are
not live deployment addresses. Production must refresh balances, account
permissions, deployed addresses and action IDs, honor actual timelocks and
execute permission grant/use/restoration atomically. Deleverage deliberately
changes this user's sGREEN position; the original all-balances-unchanged
requirement applies to the subsequent migration, not to that approved repayment.

The broader upgrade is still not qualified: reward precision/continuity,
Stability Pool claim-basket treatment, treasury/PSM/HR state and final routing,
permission replay and reopening canaries remain separate work items. The fork
runner returns exit code 2 for the previously detected reward parity difference,
even when this remediation and the tested position migrations pass.
