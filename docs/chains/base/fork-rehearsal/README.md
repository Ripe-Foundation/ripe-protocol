# Base upgrade fork rehearsal — not approved for production

For the current two-wave deployment scope and subsequent price-call gas fix,
start with [the full-update summary](full-update-summary.md) and
[staged deployment instructions](../staged-upgrade-deployment.md). The reports
below describe earlier vault-migration experiments, not the current activation
status or a freshly generated defaults snapshot.

This is a diagnostic rehearsal of master `1ede3835`, not a deploy command or a
ready-to-sign Safe batch. **No live transactions are submitted.** All contract
creation, governance impersonation, time travel and migration calls execute in
Titanoboa's local fork. The only external calls are reads against Base.

## Reproduction

Use the repository Python environment with Titanoboa, requests, python-dotenv,
eth-abi and eth-utils installed. Set `BASE_MAINNET_RPC_URL` in `.env`; no wallet
key is required.

```sh
python3 scripts/base_upgrade_fork.py \
  --block 51135337 \
  --defaults docs/chains/base/fork-rehearsal/Defaults.block-51135337.vy \
  --report /tmp/ripe-base-rehearsal.json \
  --census --probe --legacy-probe --ordinary-probe
```

The pinned finalized block hash is
`0x6e981b6f8c318546dcd3ffbec24d277a7156b806c83728afe8c7ed56b56e001e`.
The Defaults snapshot was generated with `scripts/prepare_defaults.py` at that
block. It is **not** a fresh production configuration.

`--census-input /path/to/previous-report.json` can replace `--census` on later
diagnostic runs. The block hash, vault addresses and aggregate share balances
are checked before accepting the cached census. Use a locally generated report.

Reports deliberately distinguish deployment, core compatibility, position
movement and full qualification. Exit status zero does **not** mean approval:
inspect `status`, `blockers`, `probes` and migration results. Any false parity
check blocks production. A partial diagnostic can still test position movement
after discovering a reward discrepancy; this is not permission to ignore it.

## Live inventory and invariants

Latest follow-ups: [governance remediation and completed vault-2–5 sweep](remediation.md)
and [post-cleanup residual SP workaround](residual-sp.md), following the
[initial Stability Pool diagnostic](stability-migration.md). The initial failure
counts below are historical, not the latest post-remediation results.

The live HQ registry, not the manifest's newest candidate address, selects each
active department. In particular, active VaultBook is
`0xB758e30C14825519b895Fd9928d5d8748A71a944`, not the pending candidate recorded
in the manifest. Keep the same HQ and Ledger; do not reset debt or rewards.

| Existing vault | Registered user/asset rows | Treatment |
| --- | ---: | --- |
| Stability 1 | 223 | Preserve claim basket as well as deposits; separate closeout decision |
| RipeGov 2 | 548 | Dedicated Base legacy migration; 402 funded positions, 376 users |
| Simple ERC20 3 | 148 | Ordinary migration candidate |
| Rebase ERC20 4 | 15 | Share-aware migration candidate |
| Underscore vault 5 | 97 | Separate ordinary migration candidate |

These are registered rows, not all positive balances. Summed user balances
reconcile exactly to every asset's recorded vault total. There are 56 current
borrowers; their Ledger debt records are included in the report. Historical
reward-only users and permission-only users require additional event census.

Required position invariants are underlying amount, ownership, original unlock,
original lock terms and governance points. Share counts may change when the new
vault uses a different share precision; equal raw shares are not the invariant.
The legacy migrator itself checks imported governance-point totals and exact
token transfers; the harness independently checks underlying amounts and locks.

## Intended operational sequence

1. Refresh finalized inventory, deployments, configuration, permissions,
   delegation, treasury custody, borrowers, claims, user points and pending
   governance actions. Reconcile a complete census before preparing calldata.
2. Stage replacements, retaining Ledger and token state. Rebuild registry rows
   in their original order, then append new vaults. Do not overwrite funded
   vault entries. Install Alpha through Golf and the Base-bound VaultMigrator.
3. Propose HQ changes and honor the actual 21,600-block timelock. Immediately
   before cutover, freeze user/trusted ingress and refresh all changed state.
   Ledger and CreditEngine must remain callable for migration housekeeping.
4. Switch the compatible core, replay non-constructor state, and complete
   custody handoffs. The diagnostic core probe intentionally retains the old
   Endaoment/Funds/PSM routes; their migration is not certified by that probe.
5. For each ordinary reward-bearing asset, checkpoint/clear its reward earner
   before modifying vault membership. Preserve original settings for restoration.
6. For RipeGov, pause Teller before rotating the core pointer. Pause the virgin
   target immediately after rotation. Temporarily lower the asset minimum lock
   duration below every stored source minimum to activate the legacy courtesy
   exit. All funded positions in this snapshot store 43,200 blocks. Keep the
   source unpaused and restore the original config before reopening the target.
7. Migrate users through Echo/VaultMigrator in gas-bounded transactions. Preserve
   the old Ledger participation until ordinary reward claims clean it up. Restore
   reward routing/allocations using checkpointed governance actions.
8. Independently settle the Stability Pool migration plan. Its claim basket is
   nonempty; moving only shares is not proof of economic conservation. Do not
   silently substitute a governance seed/claim strategy for users' claim rights.
9. Reconcile every balance, debt, lock and claim; test claims, withdrawals,
   borrowing, repayment and new deposits. Only then restore ingress and normal
   timelocks. Refresh and simulate exact Safe batches before production signing.

## Known qualification gaps

### Follow-up: exhaustive debt-health and account-lock census

See [borrower-blockers.md](borrower-blockers.md) and
[borrower-blockers.json](borrower-blockers.json). All 56 current borrowers were
checked under the replacement core at simulated block 51,156,937, with no read
errors. Eight fail debt health; four have funded positions and all four have
isolated migration reverts. The other four have residual debt/liquidation flags
but no funded positions. None of the 405 funded depositors are account-locked.
This exhausts those blocker classes, not every possible migration failure.

Reproduce the borrower scan and isolated RipeGov trials with the common command
above, replacing `--legacy-probe --ordinary-probe` with
`--borrower-audit --legacy-probe --audit-blocker-migrations`.
The fourth funded blocker has only an ordinary-vault position; reproduce it
separately with `--probe --ordinary-probe --only-user
0xbA49a3d456de4e670a94E13b8b1E5315929C97Ad` and a census/census-input.

### Initial migration sweep and remaining qualification work

- **Blocking legacy RipeGov account:**
  `0x28E2b238a3a7634C6C7e23b895790505B1C31Cd0` already fails
  `CreditEngine.hasGoodDebtHealth` before the attempted move. At the isolated
  migration block its collateral value is `368504001270526553948` and its
  current debt is `295390360230950243836` (18 decimals). The call fails in
  `Teller.performHousekeeping`: migration requests higher-risk housekeeping,
  which asserts `CreditEngine.updateDebtForUser` returns true. An existing
  above-LTV account therefore blocks even a RIPE position migration. Do not
  repay debt, change LTVs, unlock users or bypass this check silently. A narrow,
  reviewed preservation/non-worsening migration policy is needed, or these
  accounts must remain in the source vault. No protocol code has been changed.
- The RipeGov sweep passed **59 funded positions for 56 users** before that
  account stopped the run. This is not the full 402-position/376-user migration.
- The ordinary vault-3 sweep passed **40 positions for 31 users**. Vault 4 has
  registered historical rows but no funded positions at this snapshot.
  The vault-5 sweep is incomplete.
- The initial ordinary sweep also found the Ledger's **one action per user per
  block** rule. The runner now advances between migrations. A previously failing
  user (`0x19284cD63083583cf5C5e1F945fAE112a39976c6`) then passed both vault-3 and
  vault-5 movement, with underlying amount and current debt equal before/after.
- The core switch preserves the stored Ledger globals and all **56 borrower
  records** exactly. This does not certify future accrual, permission replay or
  the complete migration. See `evidence.block-51135337.json` for compact evidence.
- Same-block old/new Lootbox claimable rewards differ even with the same Ledger.
  The archived old source quantizes user shares to basis points; the new source
  uses the full ratio. This is a likely explanation, not permission to change
  the user's requested preservation standard. Resolve/approve the transition
  policy and check all affected users before production.
- The full Stability claim-basket handoff has not been qualified.
- Treasury/PSM custody, HR state, user delegation/config replay, pending actions,
  final route restoration and reopened-system canaries remain required.
- Deployment constructor settings in this diagnostic are not a reviewed Base
  production manifest. Some new-only settings use provisional values. No
  production migration should be generated from them without explicit review.
- The diagnostic uses local governance calls in one simulated block for the
  core switch, then advances blocks between position migrations. A realistic
  fully frozen multi-block rollout and
  executable Safe gas limits require a subsequent full-sequence rehearsal.

## Governance remediation rehearsal

Add `--remediate-blockers` to the fork command to test the owner's requested
remediation before migration. This spends only the governance Safe's actual
forked GREEN balance; there is no synthetic funding or direct storage editing.

The ordinary permissionless `deleverageManyUsers` attempt from governance
reverts. The tested alternative explicitly grants governance a temporary
`canBorrow` delegation via Charlie, uses `deleverageWithSpecificAssets` against
the user's sGREEN position in vault 1 to repay 1 GREEN, and restores the original
delegation. This intentionally reduces sGREEN, not the RIPE position or its lock.
Governance is not automatically a trusted deleverage caller.

The seven remaining listed borrowers are repaid in full using governance GREEN.
Their exact original user configurations are replayed from the old MC, then
`canAnyoneRepayDebt` is temporarily enabled and restored after payment. Each
repayment checks zero remaining debt, zero approval residue, unchanged deposited
amounts/governance records and restored permissions. The main user's original
configuration is replayed too.

`--legacy-probe --audit-blocker-migrations` tests only the previously identified
RipeGov blockers in isolated rollback scopes. Add `--ordinary-probe` to test the
affected ordinary-vault users as well. Omit `--audit-blocker-migrations` for the
full position sweeps. These modes do not qualify the Stability Pool claim
handoff, final reward-route restoration or production timelock sequencing.

The temporary delegation grants borrowing authority while active. Production
must stage the required timelocked actions and execute grant/use/restoration
atomically, with fresh permission and balance checks. The fork's zero-delay
setup is not a ready-to-sign live Safe transaction.
