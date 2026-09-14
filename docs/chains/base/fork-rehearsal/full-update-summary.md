# Base full-update rehearsal

Status: **not qualified for live activation**. All writes were confined to a
local `boa.fork`; no live deployments or governance transactions were submitted.

Pinned finalized Base block: **51,312,366**.
Block hash: `0x309867a798010d47ada7686fd2c1124118d5c76a82864e8a196a56b53c222248`.
Machine-readable evidence: [full-update-final.json](full-update-final.json).
Deployment instructions: [staged upgrade](../staged-upgrade-deployment.md).

## Follow-up: replay every live feed registration

The original replay stopped at the first failed asset within each source. The
harness now enumerates every deployed source's `getPricedAssets()`, reads its
configuration, attempts each registration independently and verifies the copied
configuration. Snapshot observations/cursors are not treated as configuration.

An oracle-only rerun at the same pinned block verified **27 of 31 per-source
asset registrations**: Chainlink 19/20, Underscore vaults 5/6, wrapped-token source
1/3 and Curve 2/2. Pyth, Stork and RedStone have no registered assets in this
snapshot. Disabled BlueChip remains disabled; legacy Aero remains retained.
The remaining failures are one Chainlink asset, one Underscore vault asset and
two removed wrapped-token routes. Source registration does not establish fresh,
nonzero prices or migrate historical snapshots.

Evidence: [oracle-registration-replay-v2.json](oracle-registration-replay-v2.json).
This narrower follow-up does not rerun treasury or user-position migration and
does not supersede the full-run balance evidence below. No live writes occurred.

## Scope

- Three readable deployment migrations stage 45 candidates, including new
  departments, MissionControl/defaults/Contributor, registries, five vaults,
  controllers, price sources, BondBooster, PSM and reserves.
- Reserves use Base USDC. Constructor economics are dormant placeholders, not
  approved launch terms. No sale allocation, permission or activation is enabled.
- HQ, Ledger, tokens and CCIP contracts are retained. Existing vault addresses
  remain at IDs 1–5; candidates are appended at 6–10. Preferred SP/governance IDs
  remain 1/2. No user vault migration occurs in wave one.

## Passed in the diagnostic

- All 45 candidates deploy within the runtime-code size limit.
- The old-vault census reconciles 1,029 registered user/asset position rows,
  including zero-share records, against vault share totals.
- Treasury transfers use governance calls, not storage edits. Supported assets
  leave the old Endaoment, EndaomentFunds and PSM; exact raw token balances are
  conserved across the new EndaomentFunds and PSM. The governance relay retains
  no extra balance from these transfers.
- PSM yield shares move directly without redemption/redeposit. Underlying value
  before and after is **38,869.251698 USDC** at the fork state.
- HQ replacement preserves the Ledger address, audited Ledger globals and all
  **55 borrower debt records**.
- After the full diagnostic, all **1,029 position rows** retain identical shares
  and Ledger deposit points; governance lock records also match exactly.
- The permission audit checks 551 users and 410 delegation pairs, replaying
  218 nonzero user configs and 292 nonzero delegations through governance calls.
  Coverage is the vault census plus the historical event signatures listed in
  the harness, not proof of every possible older-generation event format.
- PSM constructor parameters, yield destination, automatic deposit setting and
  mint/redeem allowlist enforcement match after replay. No allowlist-user events
  were discovered on the old PSM; no active interval handoff blocked this run.
- HR compensation and claimed totals match. No active pending actions were
  found in old HumanResources or Alpha–Echo. No active consumed booster needed
  a state-seeding exception at this snapshot.

## Updated findings after live checks

### Confirmed Underscore price failure causes

**Update: price-call gas is now a deploy-time immutable.** The Base candidate
uses 1,500,000 gas. The latest isolated diagnostic now returns nonzero, matching
direct-source and PriceDesk prices for undyETH and undyUSDC, with no nested call
failures. The 250,000-gas failure observations below describe the prior candidate;
the linked diagnostic JSON was refreshed for the new candidate. EURC's separate
fork-staleness issue remains unchanged. No live contract was replaced.

[Isolated diagnostic evidence](undy-price-diagnosis.json), reproduced by
`python -m scripts.diagnose_base_undy_prices`, separates these issues at block
51,312,366 without live writes or protocol-source modifications:

- undyETH registers, has a nonzero share snapshot and underlying WETH price,
  and returns a nonzero direct source quote. That quote uses 255,194 gas in the
  measured call. PriceDesk caps each source at 250,000 gas; its nested vault
  conversion runs out of gas and the aggregate returns zero. This is a real
  price-path budget incompatibility, not missing registration or snapshots.
- undyUSDC exhibits the same failure, with a measured direct quote of 882,014
  gas. Increasing wallet transaction gas does not change PriceDesk's internal
  cap. The quote cost or source budget needs a qualified solution before cutover.
- In a separate anchored branch BEFORE the governance wait, undyEURC registers
  and returns a nonzero direct quote using the unchanged pinned EURC observation.
  After the wait, EURC is stale and registration fails for lack of an underlying
  price. This confirms the fork-time issue without loosening stale limits or
  synthesizing an oracle observation.

Direct-call gas measurements are diagnostic observations, not a proposed safe
production stipend. A fix needs testing through the full canonical price path.

At finalized Base block 51,314,278, the pending slot-8 proposal still targets
`0x09f45F56b218756ab092f7470F8199db56849867`. Cancellation by the governance Safe
passed `eth_call`. The Safe requires two signatures. The unsigned
[cancellation batch](../cancel-pending-vaultbook.safe.json) is prepared, not
submitted or executed. It leaves the active VaultBook unchanged.

The four failed routes are EURC, undyEURC, mcbETH and VVV. EURC is not directly
registered as collateral but prices undyEURC. mcbETH has no configured vaults.
VVV has no deposit vaults but retains collateral-redemption configuration, so
its route must not be silently discarded without checking remaining exposure.

EURC's feed observation is timestamp 1,789,368,953. It is fresh at the pinned
fork timestamp 1,789,414,079, but the simulated 43,200-second governance wait
makes its age 88,326 seconds, exceeding its unchanged 86,400-second stale limit.
This explains the EURC registration failure; the dependent undyEURC failure is
consistent with the missing underlying price and still requires a confirming
replay with fresh oracle observations. Do not loosen the stale limit as a fix.

The operator confirmed Aero is UI-only; live RIPE debt terms have zero LTV.
The earlier reports' Aero-collateral blocker is therefore superseded. Keep the
new monitor separate from collateral pricing and coordinate its frontend use.

## Cutover blockers and limitations

- HQ already has a pending slot-8/VaultBook update to
  `0x09f45F56b218756ab092f7470F8199db56849867`. The alternate diagnostic explicitly
  cancels this **only on the fork**. Production needs a decision about that proposal.
- The diagnostic retains old PriceDesk slot 6 during the Aero UI handoff and
  leaves disabled slot 3 disabled. Aero is not a collateral-migration blocker.
- Oracle replay fails for a Chainlink feed and an Underscore vault feed; the
  current wrapped-token source also removes a legacy route. Several active
  assets have zero prices after this incomplete replay. This is not a qualified
  oracle cutover or a conclusion that every failure is a live oracle outage:
  fork time advances while external oracle observations remain pinned.
- Snapshot warm-up, full historical permission coverage, security timelocks,
  mint permissions and operational/reward continuity still need qualification
  before reopening. The passing preservation checks do not establish this.
- Unreviewed unsolicited treasury tokens are not transferred. Three token
  addresses discovered through Transfer logs cannot be balance-read; they are
  explicitly reported rather than treated as zero.
- The standard migration runner has unresolved earlier CCIP history prerequisites.
  Do not bypass history guards or fabricate completed migrations.

Teller, PSM entry points and reserve sales remain closed in the diagnostic.
Successful registration alone is **not** successful operational activation.
The production activation/funds-migration batch must not be signed from this
diagnostic until these blockers are resolved and the full rehearsal passes.
