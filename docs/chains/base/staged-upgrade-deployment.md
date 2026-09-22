# Base: deploy now, migrate later

**Current flow:** use [the fresh three-contract deployment](#fresh-deployment-flow-2026-09-21).
All older staging commands and qualification reports below are historical only.
The September 14/19 migrations are archived and are not runnable by the normal CLI.

## Current phase-1 compatibility staging

The current source uses a five-argument VaultBook constructor. **Do not resume
Stage 1 or Stage 2 from this checkout**: their frozen migrations pass four
arguments and their recorded candidates predate retained-pool compatibility.
The Stage 1/2 commands and recovery evidence below are historical instructions
for their frozen reviewed source revision, not the current production path.

For the compatibility release, use the new step after the normal runner has
verified the recorded history frontier:

```sh
python -m scripts.migrate --profile base-mainnet --start-timestamp 2026091900 --single
```

[StageLegacyVaultCompatibility](../../../migrations/base-mainnet/2026091900_StageLegacyVaultCompatibility.py)
stages VaultBook, AuctionHouse, Deleverage, SwitchboardAlpha, SwitchboardCharlie,
SwitchboardGolf and Switchboard under fresh
`<Contract>BaseLegacyCompatCandidate20260919` labels. It preserves retained vault
rows **1–5 only**, supplies the Pool-1 binding, populates the compatible controller
set, restores registry delays and relinquishes temporary governance. It records
addresses and constructor inputs in the normal journal and completed
`migration_history/base-mainnet/v1/2026091900-manifest.json`. It sends no HQ
proposal or activation and leaves the pending slot-8 proposal untouched.

Before deploying, it authenticates each reused controller against its recorded
label/source/runtime, HQ and local/pending governance. Deleverage inherits four
parameters from **active HQ slot 18** and fixes the four newer policy values to
`10**15`, `100`, `0`, `0`; the previous staged candidate is not authoritative.
Repeat `python -m scripts.verify_legacy_vault_cutover` after staging and before
activation with the final full manifest, stager and pinned block. See the
[read-only command and production-runner evidence](legacy-vault-compatibility.md#repeatable-read-only-cutover-verification).
The same release notes define classified silent-skip monitoring and link the
[modern rounding tracker #234](https://github.com/Ripe-Foundation/ripe-protocol/issues/234)
and [historical Contributor tracker #235](https://github.com/Ripe-Foundation/ripe-protocol/issues/235).

The staged **VaultBook, AuctionHouse, Deleverage, SwitchboardAlpha and
SwitchboardCharlie** from `BaseUpgradeCandidate20260914` are all superseded,
including the populated VaultBook. **SwitchboardGolf** is also superseded by its
explicit retained-Pool-1 special-pool restriction. Replace the old populated
Switchboard with the new registry containing these controller addresses.
Existing staging and Safe material cannot serve as the final compatibility
candidate set. Preserve historical migration files, journals and manifests.

Follow the [compatibility release checks](legacy-vault-compatibility.md) for the
public `LEGACY_POOL()` binding, forward/reverse/valid row-1 identities, structural
helper, exact retained-only topology, claim pricing and gas, and historical
Contributor qualification. Re-read and resolve `pendingAddrUpdate(8)` before
activation. The existing full-update diagnostic uses rows **1–10** and does not
qualify the required phase-1 topology. These are staging instructions; release
qualification and production activation remain separate owner decisions.

## Historical staging record

Current review status and mandatory gates: [PR 231 review checklist](review-231.md).
**The historical CCIP history prerequisite is reconciled** as of 2026-09-18; Stage 1 now
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

These scripts stage candidates against the existing Base RipeHq and populate
replacement registries using temporary deployer governance, then relinquish it.
They do not modify active canonical manifest entries, move funds,
repay debt, migrate positions, change vault IDs, enable mint permissions, or
unpause contracts. Deployment is not approval for cutover.

## Stages

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

### Bridge PriceDesk staging

```sh
python -m scripts.migrate --profile base-mainnet --start-timestamp 2026091403 --single
```

Use `PriceDeskBridgeBaseUpgradeCandidate20260914` as the proposed HQ slot 7
candidate, **not** Stage 3's PriceDesk containing unconfigured replacement
sources. That bridge-only instruction applies to its historical step. The compatibility
release additionally requires the seven fresh candidates listed above. Historical
migrations and deployment records are retained.

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

All historical Stage 1–4 labels end in `BaseUpgradeCandidate20260914`; the new
compatibility step uses `BaseLegacyCompatCandidate20260919`. Active canonical labels remain
untouched. The Underscore vault candidate has its own label and address, despite
using the same SimpleErc20 source as the ordinary ERC20 vault.

PriceDesk now takes separate `_priceSourcePriceGas` and `_priceSourceSnapshotGas`
constructor arguments and exposes both as immutable getters. New Base deployments
must supply **3,000,000 gas each** for nested quotes and snapshot refreshes, as
configured in `BluePrint.PARAMS["base"]`. These are not yet operation-qualified
budgets. Local/Robinhood retain 250k quote and 150k snapshot
budgets; has-feed stays 75k. There is no governance setter; changing a budget
requires another PriceDesk deployment. Historical Stage 3 used 1,500,000 each;
its recorded assertions, manifests, and earlier quote-replay evidence are not
3M qualification. Do not rerun that historical migration to redeploy: its fixed
1.5M assertions and recorded deployment labels belong to the old generation.
Use a new deployment label/migration for the 3M candidate and requalify aggregate
operations before activation or reopening.

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

At reconciliation, the normal start-point guard accepted Stage 1. Do not rerun CCIP wiring,
force-replay it, or remove the history guard. Once the separate Stage 1 readiness
decision was made, the frozen-source command was:

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
candidate manifests and receipts after deployment. **These historical commands require their frozen reviewed source and recovery
and runner gates; they must not be resumed from the compatibility checkout.**

```sh
python scripts/migrate.py --profile base-mainnet --start-timestamp 2026091401 --single
python scripts/migrate.py --profile base-mainnet --start-timestamp 2026091402 --single
```

Use the configured deployment account/environment as usual. Adding `--fork`
to the migration command rehearses it without broadcasting, but does not bypass
the same history prerequisite. Preserve and commit the resulting candidate
manifests and the generated defaults provenance after real deployment.

## Required later cutover work

### Historical Stage 2 continuation after the partial live deployment

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
Golf was unchanged in that historical loader change: adding the loader there
exceeded the runtime size limit. The compatibility step now replaces Golf to
enforce its retained-Pool-1 special-pool restriction.

Historical resume command, from the frozen Stage-2 reviewed checkout only
(never from the compatibility checkout):

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
2. For the compatibility release, select the new compatible Switchboard described
   above, not the old populated candidate. Confirm it in HQ slot 6, respecting HQ's
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
- Populate the phase-1 VaultBook with retained rows 1–5 only, preserving every
  live address and excluding rows 6–10. The historical diagnostic used SP 6,
  governance 7, and ordinary 8–10; that topology is not the phase-1 release.
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

## Fresh deployment flow (2026-09-21)

The September 14/19 staging migrations above are superseded and archived under
`migrations/archive/base-mainnet`; the runner no longer discovers them. Their
deployment manifests and logs remain historical records, not activation approval.

Run only the fresh deploy-only step:

```sh
python -m scripts.migrate --profile base-mainnet \
  --start-timestamp 2026092100 --single --fork
```

After reviewing the fork result, the same command without `--fork` deploys
DefaultsBaseLive, an empty MissionControl, and SwitchboardFoxtrot under new labels.
The current Contributor template is reused. Defaults must pass the existing
live-config preflight; regenerate them if it reports drift. There are no registry
writes, initialization calls, treasury transfers, or HQ proposals in this step.

Governance then registers/confirms the new Foxtrot in the **current Switchboard**
(inspect the live registry to choose add vs. replace). Once registered, governance
calls `startDefaultsInitialization(newMC, newDefaults)` once, then `initConfig()`
until `initStep() == 5`. Review the populated, still-inactive MC before proposing
its HQ activation. `initRewards()` remains a separate call after MC activation;
`initConfig()` does not initialize rewards or migrate per-user settings.

No new fork qualification of this flow is claimed by the historical evidence above.
