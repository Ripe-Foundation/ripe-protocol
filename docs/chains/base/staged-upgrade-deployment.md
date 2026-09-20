# Base: deploy now, migrate later

Current review status and mandatory gates: [PR 231 review checklist](review-231.md).
**The CCIP history prerequisite is reconciled** as of 2026-09-18; Stage 1 now
passes the runner's start-point guard. This is not full deployment qualification
or PR approval. Stage 2 recovery and the other review items remain open.
**Oracle cutover remains blocked** pending final source-budget qualification and
production D01 checks using the actual RPC estimator. The current PriceDesk
implements caller-underfunding checks and the Teller relay; local tests do not
close those release gates. Its constructor is incompatible with the frozen
`2026091402`/`2026091403` migrations, which must not be rerun from this checkout. Existing rerun support does
not authorize regenerating Defaults after a partially completed Stage 2.
Stage 2 must run from a frozen reviewed checkout; changes to any fingerprinted
input require fresh verification before continuing.
Evidence: [historical summary](fork-rehearsal/full-update-summary.md).
Prepared cancellation (not executed): [Safe batch](cancel-pending-vaultbook.safe.json).

These scripts stage candidates against the existing Base RipeHq and populate
replacement registries using temporary deployer governance, then relinquish it.
They do not modify active canonical manifest entries, move funds,
repay debt, migrate positions, change vault IDs, enable mint permissions, or
unpause contracts. Deployment is not approval for cutover.

## Historical stages (executed migrations remain frozen)

1. `2026091400_StageBaseUpgrade.py`: 29 deployments. Switchboard and Alpha–Golf;
   VaultBook; StabilityPool; RipeGov; SimpleErc20; RebaseErc20; a separate
   SimpleErc20 for the Underscore vault; VaultMigrator; AuctionHouse;
   AuctionHouseNFT; Boardroom; CreditRedeem; TellerUtils; EndaomentFunds;
   BondBooster; BondRoom; CreditEngine; HumanResources; Lootbox; Teller; Deleverage; Endaoment.
2. `2026091401_StageBaseMissionControl.py`: a candidate Contributor blueprint,
   DefaultsBaseLive, empty MissionControl, and replacement SwitchboardFoxtrotSetup
   with temporary deployer governance for the one-time defaults loader; populated replacement Switchboard and
   VaultBook under new labels. Vault IDs 1–5 retain live vaults; 6–10 register
   the staged vaults without moving positions.
   Existing contributor contracts remain.
   This is separate because its configuration snapshot can become stale while
   ordinary contract deployment is taking place. Generate and verify the
   snapshot immediately before running this stage. No Ledger is deployed.
3. `2026091402_StageBaseOraclesPsmReserves.py`: 13 deployments: PriceDesk;
   Chainlink, Curve, BlueChipYield, Pyth, Stork, wsuperOETHb, RedStone and
   UndyVault price sources; the standalone Aero monitor; EndaomentPSM;
   RipeReserveEngine and RipeReserveVesting. Reserves use Base USDC and remain
   paused, with no allocation or approved sale economics.
   PriceDesk is populated at source IDs 1–9, with slot 3 disabled and the legacy
   Aero source retained at 6. Deployer governance is relinquished afterward.
   Registry membership is not asset-feed configuration or oracle qualification.
4. `2026091403_StageBaseBridgePriceDesk.py`: deploys **only a bridge PriceDesk**,
   registers the CURRENT live sources in their existing slots, retains disabled
   BlueChip slot 3 and the legacy Aero source at slot 6, and caches token scales
   for current collateral plus assets enumerated by the live sources. Existing
   feeds, stale times and source observations stay in those original contracts.
   It relinquishes temporary governance without proposing any HQ update.

### Current PriceDesk/Teller staging inputs

Two fork-rehearsal scripts compile the current nine-argument PriceDesk constructor.
They live outside `migrations/base-mainnet/` and are **not in the live runner queue**:

- [`oracles_psm_reserves.py`](../../../scripts/rehearsal/base_candidates/oracles_psm_reserves.py)
  stages the full replacement-oracle and treasury set under
  `BasePriceDeskGasCandidate20260919` labels. The full wave-one fork diagnostic
  loads this path instead of frozen `2026091402`.
- [`price_desk_gas_bridge.py`](../../../scripts/rehearsal/base_candidates/price_desk_gas_bridge.py)
  stages a bridge PriceDesk and paused compatible Teller under
  `PriceDeskBridgeGasCandidate20260919` and `TellerPriceDeskGasCandidate20260919`.
  The bridge retains current source addresses, the disabled BlueChip slot, and
  token-scale bootstrap. Neither script proposes or confirms HQ changes.

Both drafts apply the profile table in `config/BluePrint.py` to the exact Curve
and Undy source addresses and read back all four constructor values and all
three effective source budgets before relinquishing setup governance. Missing
entries, wrong address bindings, invalid budgets and readback mismatches stop
that handoff. The table is independently pinned in the focused tests.

These drafts are local rehearsal inputs. Final constructor values and per-address
budgets require the separate qualification in
[the implementation handoff](pricedesk-gas-implementation.md). Only after that
qualification and explicit deployment authorization may a reviewed body be added
to the live migration directory with a fresh timestamp and fresh candidate labels.
Do not substitute an old candidate's address or journal. No migration-history
change or runner bypass is needed to use these drafts in the fork diagnostic.

`TellerBaseUpgradeCandidate20260914` is the historical pre-relay Teller candidate.
The separate `TellerPriceDeskGasCandidate20260919` requires authentication of its
actual deployment bytecode and configuration; compiling current source in a
rehearsal authenticates neither historical nor future live candidates.

At an authorized cutover, confirm the compatible PriceDesk in **HQ slot 7 before
Teller in slot 17**, or confirm both in one atomic batch with slot 7 first. Check
that slot 7 implements `addGreenRefPoolSnapshot(uint256) -> bool` and that its
source overrides are correct before confirming/unpausing Teller. A new Teller
with an old PriceDesk reverts in housekeeping, including otherwise valid user
actions. A rollback must remove that dependency in reverse order: move away from
the relay Teller before restoring a desk without the relay. Keep user entry
points closed until the complete stack passes the release gates.

### Historical bridge evidence

`PriceDeskBridgeBaseUpgradeCandidate20260914` is the historical candidate below.
Its evidence does not authenticate either new candidate or the new relay.

At cutover, the bridge allows existing source routes to remain while replacement
sources are configured and qualified through the new PriceDesk interface. Keep
each old source registered until its replacement is configured and validated;
then propose/confirm that source slot update. Price parity, snapshot handling and
treasury/user-state handoffs still require cutover checks. Merely adding a source
to the registry does not configure its feeds.

Bridge fork evidence (Base block **51,491,284**): the real migration completed
all 54 journal entries, and replay skipped all of them without additional writes.
All source slots matched the current desk, temporary governance was relinquished,
and staging left HQ unchanged. After proposing HQ slot 7, advancing 21,600 blocks
(12 hours at 2 seconds/block), and confirming, all **27 MC asset prices matched**
the old desk exactly. They also matched before activation. The RIPE/WETH pool
`0x765824aD2eD0ECB70ECc25B0Cf285832b335d6A9` returned zero on both desks;
this is retained behavior, not a claim that every asset is priceable.
The largest migration execution consumed 3,663,675 gas (excluding intrinsic gas).
No live transactions were sent. This checks the bridge, not the later source
replacements or the full protocol cutover.

The historical stage labels end in `BaseUpgradeCandidate20260914`. Active canonical labels remain
untouched. The Underscore vault candidate has its own label and address, despite
using the same SimpleErc20 source as the ordinary ERC20 vault.

The current PriceDesk constructor appends `_priceSourceHasFeedGas` and
`_maxSourceGas` after the existing quote and snapshot arguments. It exposes all
four immutable getters and governs address-specific quote/snapshot/feed overrides
through `setSourceGasBudgets`. Defaults are permanent floors; an override can
increase a budget or reset it to its default, never lower the floor. The
provisional maximum is 6M. The earlier 1.5M quote replay was historical evidence
for its exact source tree and inputs, not qualification of the current nested
fault model or complete user transactions.

`setSourceGasBudgets` replaces all three fields: zero means **reset**, not “keep.”
Use the read-modify-write and readback procedure in
[the implementation handoff](pricedesk-gas-implementation.md) whenever changing one
field. The relay uses Curve's effective snapshot budget, shared with its generic
asset snapshots. Confirm that configured value and its cold margin before cutover.

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
MC `0xD2c97549F4D44ca8Eb000d2AB2f3c5da8623D1D7` and updated Foxtrot
`0x49eE0bD53cbE59Fee1fbE7161CB6e794Ad096Dc0` are also now deployed.
The resumed migration reuses all four deployment slots, then deploys a new
`SwitchboardFoxtrotSetupBaseUpgradeCandidate20260914` with temporary deployer
governance. The prior HQ-only Foxtrot is retained in history but not registered
in the populated replacement registry. Its source stays frozen for resume
authentication; the setup variant changes only inactive-MC initialization permissions.
The Stage 1 Foxtrot deployment remains recorded but is superseded for cutover;
the migration populates the replacement Switchboard's Foxtrot slot with this
NEW address. It deploys `SwitchboardPopulatedBaseUpgradeCandidate20260914`
and `VaultBookPopulatedBaseUpgradeCandidate20260914` with deployer governance,
registers entries in order, validates their IDs, and relinquishes local governance.
The empty Stage 1 registries remain in history but are not the cutover candidates.
Golf is unchanged: adding the loader there exceeded the runtime size limit.

Resume only this unfinished stage from the repository root:

```sh
python -m scripts.migrate --profile base-mainnet --start-timestamp 2026091401 --single
```

Do not use `--force-replay` / `--is-retry`, restart Stage 1, or delete the
`2026091401-log.json` / pending manifest. The first four deployment calls stay
in the same journal slots and are skipped after authenticating their records.

The migration preserves completed slots 1–44, binds setup Foxtrot to the
candidate MC and deployed Defaults, then relinquishes Foxtrot's temporary
governance in slot 45. It finishes staging without changing any HQ pointers.
**MC remains uninitialized. Do not activate it after staging.**

At the separately approved governance cutover:

1. Reconcile the saved Defaults against live configuration again; staging
   preflight is not a cutover parity guarantee.
2. Confirm the populated replacement Switchboard in HQ slot 6, respecting HQ's
   proposal delay. Keep the old MC active.
3. From the governance Safe, call the bound Foxtrot's `initConfig()` until
   `initStep() == 5` (nine calls for this 27-asset snapshot). On interruption,
   read progress before preparing remaining calls.
4. Compare all staged MC configuration against live, excluding rewards which
   must still be zero; separately compare saved rewards defaults against live.
   Resolve drift before activation.
5. Confirm HQ slot 5 and call `foxtrot.initRewards()` in the same Safe batch.
   Verify rewards before reopening operations.

No migration rerun is needed for initialization after Stage 2 completes.
HQ governance remains authorized after temporary governance is relinquished.
Keep updated Foxtrot registered for its normal governance functions.

No user positions or historical Ledger state are copied by this loader.

### Remaining cutover requirements

#### Temporary-governance Foxtrot rehearsal — 2026-09-18 (superseded activation-during-staging flow)

Rehearsed migration `2026091401` against Base fork block **51,486,661**,
using an isolated copy of the four recorded live deployment entries:

- Reused the recorded deployments, deployed the setup Foxtrot and populated
  registries, then stopped before HQ Switchboard activation.
- Re-running before activation skipped all 44 completed journal entries.
- After switching HQ slot 6 on the fork, the deployer executed all nine MC
  initialization calls and relinquished Foxtrot governance (54 total entries).
- A further resume repeated no writes. Deployer initialization calls reverted
  after relinquishment; HQ governance could initialize rewards after confirming MC.
- The staged configuration comparison passed. No live transactions were sent,
  and the live deployment journal and pending manifest were unchanged.

This qualifies the setup/resume sequence, not the remaining oracle and funds cutover.

#### Registry/resume rehearsal — 2026-09-18 (prior HQ-only Foxtrot version)

The actual Stage 2 and Stage 3 migration bodies passed on a local Base fork at
block **51486661**, starting from a COPY of the operator's four-entry Stage 2
journal and pending manifest. Defaults preflight passed at finalized block
**51485935**. The fork uses a later, then-unfinalized block because
the newly deployed MC/Foxtrot did not yet exist at the finalized block.

- All four recorded deployments were authenticated and reused.
- Switchboard IDs 1–7 and VaultBook IDs 1–10 matched; live vaults remain at 1–5.
- A second Stage 2 run skipped all 42 recorded entries without new transactions.
- The registry-first HQ slot-6 switch authorized Foxtrot; MC defaults loaded and
  the normal Stage 2 readback comparison passed before completing its journal.
- Stage 3's 13 deployments and 21 registration/handoff calls succeeded, then a
  second run skipped all 34 entries, including the already-disabled slot 3.
- All three populated registries relinquished deployer governance and retained
  HQ Safe governance. PriceDesk kept legacy Aero at 6 and disabled BlueChip at 3.
- MC confirmation followed by rewards initialization succeeded.
- Largest measured deployment/setup execution gas: **4,784,235** (intrinsic gas
  excluded); all checked calls were below the 16M rehearsal threshold.
- Eleven existing Defaults/preflight checks passed; no new migration test suite.

The live journal and pending manifest remained byte-identical. No live writes.
This validates deployment, registration and resume mechanics, NOT complete
oracle configuration, user-state/vault migration, or resolution of the existing
Stage 3 review gates.

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

This uses historical staging bodies and current rehearsal drafts inside `boa.fork`, checks custody,
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
