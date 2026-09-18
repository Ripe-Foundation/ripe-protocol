# Base: deploy now, migrate later

Current review status and mandatory gates: [PR 231 review checklist](review-231.md).
**The CCIP history prerequisite is reconciled** as of 2026-09-18; Stage 1 now
passes the runner's start-point guard. This is not full deployment qualification
or PR approval. Stage 2 recovery and the other review items remain open.
**Stage 3 is also blocked** pending the caller-underfunding snapshot policy and
any necessary immutable PriceDesk enforcement change (D01). No such contract
change is included in the owner-directed follow-up. Existing rerun support does
not authorize regenerating Defaults after a partially completed Stage 2.
Stage 2 must run from a frozen reviewed checkout; changes to any fingerprinted
input require fresh verification before continuing.
Evidence: [historical summary](fork-rehearsal/full-update-summary.md).
Prepared cancellation (not executed): [Safe batch](cancel-pending-vaultbook.safe.json).

These scripts stage candidates against the existing Base RipeHq. They do not
register candidates, modify active canonical manifest entries, move funds,
repay debt, migrate positions, change vault IDs, enable mint permissions, or
unpause contracts. Deployment is not approval for cutover.

## Stages

1. `2026091400_StageBaseUpgrade.py`: 29 deployments. Switchboard and Alpha–Golf;
   VaultBook; StabilityPool; RipeGov; SimpleErc20; RebaseErc20; a separate
   SimpleErc20 for the Underscore vault; VaultMigrator; AuctionHouse;
   AuctionHouseNFT; Boardroom; CreditRedeem; TellerUtils; EndaomentFunds;
   BondBooster; BondRoom; CreditEngine; HumanResources; Lootbox; Teller; Deleverage; Endaoment.
2. `2026091401_StageBaseMissionControl.py`: a candidate Contributor blueprint,
   DefaultsBaseLive, empty MissionControl, and a replacement SwitchboardFoxtrot
   with a one-time defaults loader.
   Existing contributor contracts remain.
   This is separate because its configuration snapshot can become stale while
   ordinary contract deployment is taking place. Generate and verify the
   snapshot immediately before running this stage. No Ledger is deployed.
3. `2026091402_StageBaseOraclesPsmReserves.py`: 13 deployments: PriceDesk;
   Chainlink, Curve, BlueChipYield, Pyth, Stork, wsuperOETHb, RedStone and
   UndyVault price sources; the standalone Aero monitor; EndaomentPSM;
   RipeReserveEngine and RipeReserveVesting. Reserves use Base USDC and remain
   paused, with no allocation or approved sale economics.

All labels end in `BaseUpgradeCandidate20260914`. Active canonical labels remain
untouched. The Underscore vault candidate has its own label and address, despite
using the same SimpleErc20 source as the ordinary ERC20 vault.

PriceDesk now takes separate `_priceSourcePriceGas` and `_priceSourceSnapshotGas`
constructor arguments and exposes both as immutable getters. Stage 3 supplies
**1,500,000 gas each** for Base's nested quotes and snapshot refreshes. These are
staged/unqualified budgets. Local/Robinhood retain 250k quote and 150k snapshot
budgets; has-feed stays 75k. There is no governance setter; changing a budget
requires another PriceDesk deployment. The earlier targeted quote replay confirms undyETH
and undyUSDC return matching direct-source and aggregate PriceDesk prices at this
budget. This is not a full aggregate-operation gas qualification for reopening.

Retain RipeHq, tokens, Ledger, pools and CCIP contracts. The separate Underscore
repository's contracts still need their own deployment. PriceDesk slot 3 is
disabled on Base and must stay disabled. Aero is UI-only, as confirmed by the
operator; RIPE has zero LTV. The new AeroRipePrices is a standalone monitor, not
a collateral source. The diagnostic retains legacy slot 6 during the UI handoff;
requiring a replacement collateral oracle for Aero was an overstatement, not a
cutover blocker. Coordinate the frontend monitor address separately.

## Runner prerequisite — reconciled from the old system

On 2026-09-18 the operator confirmed completion under the former migration system
and authorized history reconciliation. The existing read-only finalization
checker passed at finalized Base block **51,478,064**, including routing,
ownership, mint capabilities, Robinhood peer settings and rate policies.
[Reconciliation record](../../../migration_history/base-mainnet/v1/ccip-external-completion-20260918.md)
links the detailed readback evidence. The two empty deployment maps for
`2026082400`/`2026082401` attribute no new contracts to this reconciliation;
canonical addresses and earlier history are unchanged. Original receipts are not
reconstructed, and the newer migration bodies were not run.

The normal start-point guard now accepts Stage 1. Do not rerun CCIP wiring,
force-replay it, or remove the history guard. Once the separate Stage 1 readiness
decision is made, run only the selected stage:

```sh
python scripts/migrate.py --profile base-mainnet --start-timestamp 2026091400 --single
```

For a NEW config stage, choose a fresh finalized Base block and use the existing
snapshot tools (replace BLOCK with the actual block number):

```sh
python scripts/prepare_defaults.py --network base-mainnet --block-number BLOCK
python scripts/verify_defaults.py --network base-mainnet \
  --defaults contracts/config/DefaultsBaseLive.vy --block-number BLOCK
```

Review the generated Defaults, ABI, and provenance diff. If regeneration changed
them, record the reviewed revision before Stage 2; confirm deployment uses that
same source. If byte-identical, the existing source review still applies. Record
candidate manifests and receipts after deployment. **The commands below remain
blocked until the review checklist's recovery and runner gates close.**

```sh
python scripts/migrate.py --profile base-mainnet --start-timestamp 2026091401 --single
python scripts/migrate.py --profile base-mainnet --start-timestamp 2026091402 --single
```

Use the configured deployment account/environment as usual. Adding `--fork`
to the migration command rehearses it without broadcasting, but does not bypass
the same history prerequisite. Preserve and commit the resulting candidate
manifests and the generated defaults provenance after real deployment.

## Required later cutover work

### Stage 2 continuation after the partial live deployment

Do not regenerate Defaults or discard the deployment journal. Contributor
`0x57f64a8FA104c18dE76dEe6817E45Cf43b6B459E` and DefaultsBaseLive
`0x249c4798C49Fc8Ad86a43dC425D80396971E7AcC` already deployed.
The resumed migration reuses them, deploys the unchanged MissionControl with a
zero Defaults argument, and deploys updated Foxtrot under the new label
`SwitchboardFoxtrotWithDefaultsBaseUpgradeCandidate20260914`.
The Stage 1 Foxtrot deployment remains recorded but is superseded for cutover;
populate the replacement Switchboard's Foxtrot slot with this NEW address.
Golf is unchanged: adding the loader there exceeded the runtime size limit.

Resume only this unfinished stage from the repository root:

```sh
python -m scripts.migrate --profile base-mainnet --start-timestamp 2026091401 --single
```

Do not use `--force-replay` / `--is-retry`, restart Stage 1, or delete the
`2026091401-log.json` / pending manifest. The first two deployment calls stay
in the same journal slots and are skipped after authenticating their records.

The migration deliberately stops with `BASE_MC_AWAITING_SAFE_INIT` until:

1. Governance registers the printed replacement Foxtrot address in the CURRENT active
   Switchboard: `startAddNewAddressToRegistry`, wait its registry delay, then
   `confirmNewAddressToRegistry`.
2. Governance calls `foxtrot.startDefaultsInitialization(candidateMC, deployedDefaults)`
   once. Both addresses are then permanently bound for this deployment.
   Governance calls `foxtrot.initConfig()` until `initStep() == 5`.
   Each call is independently committed; asset calls copy at most five entries.
   For the current 27 assets this is nine calls in total. Split Safe batches
   to respect the transaction gas ceiling; do not put all nine in one batch.
3. Resume Stage 2 normally (no force-replay). It checks every represented MC
   config against live, except rewards, which must still be zero. It separately
   verifies the saved rewards defaults match live. Drift blocks continuation;
   do not edit the already-deployed Defaults to bypass it.

At the separately approved cutover, confirm HQ slot 5 first, then call
`foxtrot.initRewards()`, then confirm the replacement Switchboard (slot 6).
Keep these ordered in the same Safe batch where possible, and do not reopen
user operations before rewards readback matches Defaults. If slot 6 is changed
first, the initializer must also be registered there before it can set rewards.
The reward setter requires MC to be active; the initializer enforces that
condition and allows the reward copy only once. Loading other defaults is
disabled once MC is active. Keep updated Foxtrot registered in the new
Switchboard for its normal reserve/auction governance functions.

No user positions or historical Ledger state are copied by this loader.

### Remaining cutover requirements

- Refresh/reconcile MissionControl's entire live configuration, including asset
  configs, governance lock terms, reward routes, signers and migration topology.
  Stage 2 checks representable config/asset equality, not complete state equivalence.
  Redeploy its snapshot candidate under a new migration if it has become stale.
- Populate candidate registries with the reviewed old/new topology. No vault IDs
  are assigned by these scripts; do not assume fresh VaultBook IDs 1/2 can replace
  live position IDs. The rehearsal used SP 6, governance 7, and ordinary 8–10.
  Wave one must leave MissionControl's preferred SP/core governance IDs at 1/2;
  changing them belongs to wave two, with the associated position transfers.
- Set registry/action delays and permissions before activation. New switchboards
  have no temporary deployer governance; they inherit HQ governance. Their
  configured min/max bounds use the Base profile, not rehearsal-only short locks.
- Teller and VaultMigrator deploy paused. Only unpause in the coordinated cutover.
- Reconcile stateful departments, custody, rewards continuity, debtor remediation,
  locks, old/new share accounting and SP dust. Deployment alone does none of this.
- Move configured PSM yield shares and supported treasury tokens through actual
  governance calls; check exact token-unit conservation and no governance relay
  residue. Do not transfer unsolicited tokens merely because their Transfer logs
  mention the treasury. Reconcile PSM allowlists and active interval counters
  before reopening mint/redeem.
- Activate the compatible Underscore-side RipeLego/agent/helpers and update stored
  collateral/leverage vault IDs in coordination with the funds migration.

The new Deleverage-only constructor fields match the rehearsal: 0.001 GREEN
full-payoff buffer, 1% overage, and dust forgiveness disabled. Existing readable
Deleverage, Lootbox, Endaoment and BondRoom inputs are taken from active HQ slots
at execution time. Review these plus the Base profile parameters before signing.

## Full wave-one diagnostic

The review snapshot in `contracts/config/DefaultsBaseLive.vy` was refreshed from
finalized Base block **51,318,877**, hash
`0xc3fb0c9e51cbeb6472b2476c4576a755effcc9bfb98812d7734e2ba5eefac6a5`.
`DefaultsBase.vy` remains the launch configuration. The older snapshots below
are retained only to reproduce their corresponding historical fork evidence.
`verify_defaults.py --network base-mainnet` successfully compared **131 live
values across 27 assets** against a reconstructed MissionControl at that block.

```sh
python scripts/base_full_update_fork.py --block 51312366 \
  --defaults docs/chains/base/fork-rehearsal/Defaults.wave1-51312366.vy \
  --report /tmp/base-full-update-NEW-RUN.json \
  --diagnose-replacing-pending
```

This uses actual migration constructor calls inside `boa.fork`, checks custody,
prepares registries and attempts the department/oracle update. It never signs
or broadcasts and does not edit live migration history. At normal completion it
writes `not_qualified` and exits 2; this does not prove that every check ran or
passed. Inspect `checks` and `blockers`. A fatal earlier error is incomplete and
may exit with a different nonzero status. The JSON lists
actual calls, failures, and preservation checks. No user vault migration runs.

The diagnostic flag records and cancels a conflicting pending HQ slot-8 update
**inside the fork only**, to exercise the rest of the upgrade. Without this flag
the existing pending update blocks activation. This is not authorization to
cancel the live proposal: its disposition must be decided before production.

Do not interpret successful HQ registration as a usable cutover. The diagnostic
keeps Teller and PSM entry points closed, and keeps reserve sales disabled. Oracle
route compatibility, fresh snapshot history, permissions and outstanding actions
must all be qualified before reopening. Focused review regressions are offline;
standard-runner lifecycle coverage remains an explicit open gate.
