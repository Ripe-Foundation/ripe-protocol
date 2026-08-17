# Base Legacy RipeGov Vault Migration — Corrected Decision Plan

**Status:** architecture and fork-qualification plan only; mainnet execution is blocked
**Legacy vault:** `0xe42b3dC546527EB70D741B185Dc57226cA01839D`
**Legacy VaultBook ID:** `2`
**Historical repository baseline inspected (not an execution lock):** `master` at
`91eda49ccd34a25090582aff0695075c4c806011`
**Reviewed RH contract-source anchor (not a moving-branch lock):** `origin/rh` at
`6260726d0d08a3bfec5b6e494c0adacb70be90f9`, tree
`0f8ec4bcf936873a0705f70bc4be0cc4b90b1d22`
**Merged RH migration package:** implementation commit
`f7f42db1aa1a3a4ec3e65550a0098044b66381c2`, merged into `rh` by
`24de5e62e2158114e3694c9a356c0add94b6f329`
**Live read-only recheck:** Base block `49,667,747`, 2026-08-07
**Settled owner direction:** qualify targeted Base department replacements first; migrate one asset
per transaction; never remove source participation prematurely and route eventual Ledger cleanup
through Lootbox; accept the fresh-target share-rate reset; migrate the complete manifest through
administrator-controlled calls while preserving every imported position's original lock terms;
use a measured full-protocol Teller pause for the migration window
**RH policy status:** selected patterns were reviewed at the anchor above; its blind Teller/Lootbox
source-removal behavior is a known defect and negative reference. Ongoing deployment commits and
commit/tree changes remain non-blocking because the owner directs this plan to assume the relevant
smart-contract contents remain unchanged
**Lifecycle limit:** no contract implementation, deployment, registration, configuration proposal,
Safe transaction, activation, migration or mainnet state change is authorized by this document
**Fresh-session handoff:** see `implementation-handoff.md`; it translates this architecture into
phased implementation instructions without expanding this document's authorization

This document supersedes the earlier endgame assumption that Base can register a new RipeGov vault
and then switch a `coreRipeGovVaultId` pointer. The deployed Base protocol has no usable pointer.
Getting assets and governance state out of the legacy vault is only half the problem; every route
that treats VaultBook ID 2 as the governance vault must also reach a correct steady state.

---

## 1. Corrected conclusion

A legacy-to-new migration remains technically plausible, but a temporary Teller adapter followed
by a pointer switch is not a complete or acceptable design for Base.

The selected qualification direction is a **final Base department replacement**:

1. register a new migration-aware RipeGov vault at a new VaultBook ID;
2. replace Teller with the intended long-lived Base Teller, including a narrowly scoped legacy
   source migration function and explicit routing from old producer calls to the new vault;
3. replace stateless TellerUtils with the Base-specific legacy validator, following the latest RH
   extraction pattern and preserving Teller bytecode headroom;
4. replace Lootbox so Vault IDs other than 2 receive governance-vault point treatment and so
   Lootbox—not Teller directly—governs eventual source-Ledger cleanup;
5. replace HumanResources and SwitchboardAlpha only after proving and preserving or clearing their
   pending transient state;
6. replace SwitchboardEcho with the governance-only, batch-capped administrator migration wrapper,
   after the same pending-state proof; and
7. stage all final department changes so the governance wait occurs before the migration window and
   confirmations can execute atomically in one Safe transaction.

This avoids a second Teller swap and the temporary adapter's extended total-protocol freeze. It is
not yet implementation authorization. The exact new vault ID must be bound from a final live read;
department state re-seed, Teller routing, Base cleanup/reward adaptation, and the exact measured
scope/duration of the migration-window freeze remain qualification gates.

---

## 2. Reproduced facts and hard blockers

At the live recheck, VaultBook still returned ID 2 for the legacy address and `getAddr(2)` returned
the same address. RipeHQ still returned a `21,600`-block registry timelock. Live RipeHQ ID 5
resolved MissionControl to `0x559E53F42b68b4995732Dba4aF300796761DBC19`; the previously reported
`0xB59b84B526547b6dcb86CCF4004d48E619156CF3` is a stale deployment artifact and must not be
used as current-state evidence. Calling `coreRipeGovVaultId()` on the actual current MissionControl
also reverted. The legacy vault's `numAssets()` returned `4`, meaning three registered entries at
indices 1–3 plus the unused zero sentinel.

The corrected MissionControl provenance does not collapse the Option A/Option B distinction. The
actual current contract still has no callable core-vault pointer: targeted fixed-ID department
replacements can preserve it, while adopting RH pointer indirection still requires MissionControl
replacement and state re-seeding.

Base's registry history materially narrows the operational distinction. At the live recheck,
RipeHQ IDs 1–21 contained 36 post-registration version increments in aggregate. That is not itself
an exact update-event count because a confirmed disable also increments `AddressInfo.version`.
The later reviewer re-review independently reproduced exactly 37 unique
`AddressUpdateConfirmed` logs by deduplicating on `(transaction_hash, log_index)`, spanning blocks
`32,121,519` through `43,013,380`. Its multi-event block counts were
`{32946964: 6, 33297196: 3, 34395490: 2, 38099722: 3, 38707243: 6}`. Gate 2 must reproduce that
same complete-log recipe and result rather than treating the reviewer report as permanent chain
evidence. The material examples were also reproduced directly:
RipeHQ emitted six `AddressUpdateConfirmed` events in one transaction at block `32,946,964`
(`0xa5972225bf5c4878c1e0a1c8b147f313843e9e6f5bd2ea8a897ab34fe9a1d7cc`), six more in one
transaction at block `38,707,243`
(`0x601349a460595cc462b33ddffa503a90729dfe259c7c0838e54c2b154fac3a77`), and the current
MissionControl replacement at block `39,260,591`
(`0xec2a6a04ae52f2aa0e97335635beee211d33d8bb5937871d69d9b67f4f84a845`). This proves that
multi-department confirmations can be atomic at RipeHQ and supports §1 item 5. It also means Option
B's cost must be described as state re-seeding and broader dependency qualification, not as an
unprecedented or necessarily wholesale replacement of the entire protocol.

The independent review also compared the verified deployed `RipeGov.vy`, `SharesVault.vy` and
`VaultData.vy` sources with this Base source and found byte equality modulo trailing whitespace; its
deployed/master/then-current-RH `Addys` layouts were identical. Gate 2 must reproduce and bind that result to the
chosen fork block and runtime bytecode hashes rather than treating this historical comparison as a
permanent source-authority claim.

### 2.1 Reviewed RH contract anchor and non-blocking branch movement

The remote RH ref was inspected at the historical anchor above on 2026-08-07. The local `rh`
worktree remained at old commit `be6e4e9805e9b499b10f61cd219c555e62b43857`; a worktree name or
branch commit number is not source authority. At Phase 1 kickoff, record the relevant RH contract
blob IDs/content hashes once and use those source contents. Do not require the current RH commit or
tree to equal the historical anchor.

The owner expects ongoing RH deployment work to create commits without changing the relevant smart
contracts. Those commits must not interrupt this workstream. Do not poll, merge, rebase, restart, or
stop because RH or Base has advanced. At the scheduled Phase 1 owner-review boundary, a cheap
relevant-contract blob comparison may confirm the assumption; deployment, migration, manifest,
generated, or other non-contract changes are ignored. If a relevant RH contract unexpectedly
changed, finish the Phase 1 candidate and report the exact source delta. Only a reconciliation that
changes the owner-reviewed Base production-contract diff requires renewed contract review.

The reviewed RH contract set changes the Base handoff in five material ways:

1. **Ledger preservation is now explicit upstream.** RH removed
   `Ledger.removeVaultFromUserForMigration`, routes the caller through Lootbox, and its latest stale
   contract redeployment deliberately excludes Ledger because its live accounting cannot be
   reconstructed. Base adopts both conclusions: no Ledger change or redeploy, and only Lootbox may
   call deployed `removeVaultFromUser`.
2. **TellerUtils is now part of the migration architecture.** RH moved endpoint validation out of
   size-constrained Teller. Base will replace TellerUtils and put view-only legacy/source/target
   validation there, while Teller retains the atomic state-changing withdrawal/import flow.
3. **SwitchboardEcho now provides the governance batch pattern.** RH exposes a governance-only
   `migrateRipeGovPositions` wrapper with an ABI ceiling of 25 rows. Base will use a replacement
   Echo for the admin-only batch entry, but will hard-bind the legacy source, target and active
   asset window more narrowly than RH's generic `(sourceId,targetId)` struct.
4. **The RH pause assumption cannot be copied.** Latest RH `validateRipeGovMigration` requires both
   RipeGov endpoints paused because both implement the new exporter/importer. The Base legacy source
   must remain unpaused for `SharesVault` withdrawal, while the target remains paused for import.
5. **The RH cleanup call cannot be copied.** Latest RH Teller checks only the migrated asset and
   immediately calls a Lootbox forwarder that blindly removes the entire source-vault Ledger entry.
   It neither scans remaining source assets nor settles source reward reachability first. That is
   unsafe for Base's confirmed multi-asset holders. Base instead uses the admin-driven lazy/final
   cleanup policy in §2.4.

This fifth item is a verified known defect in the reviewed RH anchor, not merely a hypothetical
Base incompatibility. At `6260726...`, Teller performs only per-asset zero checks before the
unconditional call, and Lootbox is a Teller-gated pass-through to
`Ledger.removeVaultFromUser`. RH configuration includes RIPE and RIPE/WETH LP in the governance
vault, while `0009_RedeployStaleContracts.py` includes both Teller and Lootbox. The RH remediation
and deployment decision belongs to its separately assigned workstream; this Base plan neither fixes
nor approves that deployment. For Base, the defective code is a negative test/reference only. It
must never be copied, and its existence does not block the Base contract-only phase.

The focused RH lane was also rerun from a detached worktree at the reviewed anchor:
`107 passed, 51 xfailed` in `161.60s` for the RipeGov migration-focused tests plus the deployed
runtime-size gate. Expected xfails are not Base correctness evidence; they merely confirm that the
reviewed RH contract contents reproduced their committed test expectations.

The reviewed RH deployed-runtime expectations are the relevant upstream size warning:

| RH contract at `6260726...` | Boa deployed runtime | EIP-170 headroom |
|---|---:|---:|
| Teller | 24,258 | 318 |
| TellerUtils | 11,900 | 12,676 |
| Lootbox | 22,665 | 1,911 |
| SwitchboardEcho | 22,912 | 1,664 |

RH Teller is only 18 bytes above the project's 300-byte safety floor. This supersedes the prior
437-byte baseline and the earlier unbound “29 bytes above floor” candidate. It reinforces, but does
not automatically prove, the Base split: view-only validation belongs in TellerUtils, governance
batching belongs in Echo, and only unavoidable atomic state transitions stay in Teller. Final Base
Boa deployments—not these RH figures or Vyper templates—control acceptance.

### 2.2 Vault-ID-2 and migration dependency inventory

| Deployed surface | Current address | ID-2 dependency | Required disposition |
|---|---|---|---|
| Teller | `0xae87deB25Bc5030991Aa5E27Cbab38f37a112C13` | constant ID 2; direct gov-vault operations | replace with final Teller and prove caller-scoped legacy routing |
| TellerUtils | resolve live RipeHQ ID 20 in Gate 2 | no legacy migration validator | replace with the Base-specific view-only validation extracted from Teller |
| Lootbox | `0x1f90ef42Da9B41502d2311300E13FAcf70c64be7` | constant ID 2 plus literal `_vaultId != 2` points scaling | replace; never leave new-vault points on the ordinary-vault `1e9` divisor path |
| HumanResources | `0xF9aCDFd0d167b741f9144Ca01E52FcdE16BE108b` | constant ID 2 and direct vault lookups/calls | replace after pending-action inventory |
| BondRoom | `0x707f660A7834d00792DF9a28386Bb2cCC6446154` | sends RIPE rewards to Teller with ID 2 | preserve contract; final Teller must translate only the intended producer route |
| Stability Pool | `0x2a157096af6337b2b4bd47de435520572ed5a439` | sends RIPE claims to Teller with ID 2 | preserve contract; final Teller must translate only the intended producer route |
| SwitchboardAlpha | `0x4bf9025D76FeDd6331661C5de482b0a607D912B9` | validates RipeGov config against ID 2 | replace or provide a separately proved compatible configuration path |
| SwitchboardEcho | Base manifest records `0xd379595D192DddcDcdCeb3fCA5022A0e994c9988`; live-read ID 5 in Gate 2 | reviewed RH places governance-only migration batching here | replace after pending-action inventory; hard-cap and hard-bind Base batches |
| MissionControl | `0x559E53F42b68b4995732Dba4aF300796761DBC19` | no callable core-vault pointer | preserve under the narrow option; do not assume RH indirection exists |
| Ledger | `0x365256e322a47Aa2015F6724783F326e9B24fA47` | removal is Lootbox-only; no RH migration removal function | preserve; replacement Lootbox may provide a Teller-gated forwarder |

The final Teller must not blindly rewrite every `depositFromTrusted(..., 2, ...)` call to the new
ID. The compatibility shim must be explicitly caller-, asset- and operation-scoped to the known
legacy governance producers. Ordinary use of ID 2 must fail closed once the old vault is retired.

### 2.3 Lootbox is a hard correctness dependency

Deployed Lootbox treats only literal Vault ID 2 as the governance vault. At another ID, an
18-decimal asset's loot share is divided by precision `10^9`. Registering a new vault without
replacing this behavior would effectively eliminate migrated users' deposit-point share. Teller
cannot repair this because the scaling occurs inside Lootbox.

### 2.4 Reviewed-RH-informed Base cleanup policy

Base Ledger's `removeVaultFromUser` accepts only the registered Lootbox. It has no
`removeVaultFromUserForMigration`. A temporary Teller adapter therefore cannot perform the claimed
source cleanup. The latest merged RH code confirms the correct authority route but not the correct
Base timing: its RipeGov path removes immediately after one asset, while its generic vault runbook
deliberately retains source enumeration for later reward claim/ordinary cleanup.

Base adopts an administrator-driven version of the safer lazy policy:

1. after each asset withdrawal, checkpoint that source asset's Lootbox points to a zero current
   balance while its source metadata and Ledger participation are still reachable;
2. preserve the source vault in Ledger while another positive source asset or unclaimed source
   reward remains;
3. before deregistering a zero-balance source asset, have the administrator settle/claim its
   accrued source rewards to the user with `_shouldStake=False`; forfeiture is not authorized;
4. use Lootbox to deregister the settled zero-balance source asset; and
5. only after every source asset is zero, every source reward is settled, and no cleanup-relevant
   registration remains may Lootbox call deployed `Ledger.removeVaultFromUser`.

The existing broad claim route may implement step 3 only if the fork proves it is callable for
every manifest user, does not touch forbidden target gov data, does not introduce unrelated borrow
or vault side effects, and cleans swap-and-pop enumeration correctly. Otherwise the replacement
Lootbox needs a narrow Teller/Echo-controlled migration settlement/cleanup entry that:

- accepts only the currently registered Teller or the exact registered Echo control route selected
  by the final call graph;
- accepts only the approved legacy source vault ID and active migration asset;
- enumerates authoritative source entries with balance-bearing getters rather than treating
  `getNumUserAssets(user)` as a balance predicate;
- settles source deposit points and claims the user's source reward entitlement for each asset
  before that asset is deregistered, asks the source vault to deregister every zero-balance asset
  through its existing Lootbox-only path, and fails closed if cleanup is capped or incomplete;
- calls existing Ledger removal only after no positive source balance remains and no registered
  source asset/reward still requires participation; and
- performs the entire transition without changing or redeploying Ledger.

`getNumUserAssets(user)` counts registrations. Export and withdrawal reduce balances but do not
deregister assets; only Lootbox can cause `VaultData.deregisterUserAsset` to decrement that count.
Therefore a pre-forwarder `getNumUserAssets(user) == 0` branch is dead for an eligible migrating
user and is forbidden. The exact depletion predicate must include every registered source asset
and any source state that keeps participation necessary. A per-asset zero is insufficient. Teller
must post-check that Ledger participation matches the authoritative balance/reward result. The
latest RH `removeVaultFromUserForMigration` pass-through is explicitly forbidden as-is.

The reviewer's proposed balance-enumeration guard is the minimum RH correction, but it is not the
complete Base policy: Base must also preserve source reward reachability and cleanup-relevant
registrations before removal. Therefore the stricter five-step sequence above remains controlling.

### 2.5 Temporary Teller adapter cost and authority

Installing and later removing a temporary adapter requires two registry waits of 21,600 Base
blocks, roughly 24 hours in aggregate at two-second blocks, plus migration execution time. While an
adapter occupies Teller's registry slot, every protocol path gated to Teller is unavailable unless
the adapter reimplements it, including repayment, liquidation and auction paths. The adapter also
inherits Teller-gated authority across the protocol. Its internal allowlist would be the only loss
boundary and could not be replaced immediately after a defect.

For those reasons, a temporary adapter is a fallback only, not the preferred plan. A final Teller
replacement still has a governance wait, but it is one intended long-lived swap and need not be
swapped back after migration.

### 2.6 Other legacy withdrawal callers are deliberately rejected

The legacy vault also accepts AuctionHouse and CreditEngine as withdrawal callers. They are not a
shortcut:

- neither is the target vault's Teller-authorized importer;
- neither can request Ledger removal from the deployed Base Ledger;
- occupying or modifying either authority expands liquidation/credit blast radius; and
- splitting export and import authority makes the atomic receipt and rollback proof harder.

Use of either requires a new architecture review and is not authorized by this plan.

---

## 3. Legacy export without an export function

The viable mechanism is for the **final replacement Teller** to synthesize the migration record,
not for the legacy vault to return one.

For one user and one asset in a single transaction, Teller can:

1. read the legacy vault's public `userGovData(user, asset)` fields before withdrawal;
2. read the current asset-scoped RipeGov configuration;
3. calculate pending points at the transaction's block with the legacy vault's public
   `getLatestGovPoints(...)`, preserving the saved points, original unlock and original last terms;
4. measure the target vault's token balance;
5. call legacy `withdrawTokensFromVault(user, asset, max, targetVault, addys)` while the source is
   unpaused and its restrictions have been deliberately released;
6. prove the exact target receipt and complete source-asset depletion;
7. call the paused target's `importPositionForMigration` with amount, total captured points,
   original unlock and original last terms;
8. add target Ledger participation if absent;
9. settle source and target Lootbox deposit points while the migrated source asset is still
   registered;
10. retain claimable source enumeration until the administrator claims that asset's accrued source
    rewards to the user, then have Lootbox deregister the zero-balance asset; remove the source
    Ledger entry only after the final source asset/reward/registration is gone; and
11. run debt-health housekeeping after the complete Ledger transition, reverting the whole
    transaction if health is unacceptable.

Each transaction migrates one asset. The import must be atomic with that asset's source withdrawal.
There is no off-chain custody step and no
governance-controlled arbitrary recipient. Exact receipt, no Teller residual, target-returned
shares, source depletion, target balance and debt health are transaction invariants.

### 3.1 Minimal wind-down configuration

For the one asset in the current migration window whose observed minimum is 43,200 blocks, change
only:

`minLockDuration: 43,200 -> 43,199`

Keep `assetWeight`, `shouldFreezeWhenBadDebt`, `maxLockDuration`, `maxLockBoost`, `canExit` and
`exitFee` unchanged. This single worsening comparison makes `_areKeyTermsSame` false, causing the
legacy withdrawal touch to set unlock to zero. The earlier all-zero proposal is rejected because
it unnecessarily changes weight, boost, exit behavior and pending-point semantics.

Technical nuance: an all-zero configuration would not make pending-point capture mathematically
impossible if a replacement Teller independently calculated it from preserved terms. It would,
however, make the source withdrawal's current-config calculation drop lock boost and greatly expand
the blast radius. The minimal one-block duration change is strictly preferable.

### 3.2 Irreversibility and the shared-config landmine

Restoring normal terms does not restore a legacy user's old unlock after that user is touched under
the wind-down terms. The release is a one-way state transition for each touched source position.
This originally required an explicit governance decision and a complete straggler policy. Both are
now settled in §8: administrators migrate the exact-closure manifest, failures remain atomic and
retryable, original target lock data is preserved, no residual is waived, and retirement waits for
100% reconciliation.

MissionControl's RipeGov config is keyed by asset, not vault. During the wind-down window it applies
to both source and target. Therefore:

> No function may refresh, update or otherwise touch imported target gov data while wind-down terms
> are active. Import's direct state write is allowed; any path that calls the normal gov-data update
> flow is forbidden until normal terms are restored.

Fork tests must enumerate every target-side call reachable from migration, Ledger, Lootbox,
Boardroom and housekeeping and prove that none refreshes the imported lock. Merely having the
steps in a favorable order is not enough.

### 3.3 Multi-asset source handling

The source has three registered assets:

- RIPE at index 1;
- old RIPE/WETH pool `0xF8D92a9531205AB2Dd0Bc623CDF4A6Ab4c3a2526` at index 2,
  currently zero-balance and unsupported; and
- current Aero RIPE/WETH pool `0x765824aD2eD0ECB70ECc25B0Cf285832b335d6A9` at index 3.

The migration manifest must enumerate per-user assets from authoritative vault getters, not assume
two active global assets. The unsupported zero-balance legacy pool must be explicitly classified
and proved absent per user. Ledger source participation remains until all supported per-user source
balances are zero. This requirement also guards against the confirmed RH special-migration bug in
which one asset's migration removes the entire source-vault entry.

**Only one active asset may use wind-down terms at a time.** A legacy withdrawal of asset A calls
`_updateUserGovPoints` and refreshes every other source asset still held by that user. If RIPE and LP
wind-down terms were active together, migrating RIPE would zero the remaining LP unlock before its
later per-asset migration could capture the original lock. The mandatory sequence is:

1. apply wind-down terms to RIPE only;
2. migrate and reconcile every RIPE manifest row;
3. restore normal RIPE terms and prove imported RIPE locks survived;
4. apply wind-down terms to the current LP only;
5. migrate and reconcile every LP manifest row; and
6. restore normal LP terms.

Reverse the asset order only if the fork proves the same invariants. Never overlap the two
wind-down windows.

---

## 4. End-state options

### Option A — targeted Base department replacements — selected for qualification

Replace final Teller, TellerUtils, Lootbox, HumanResources, SwitchboardAlpha and SwitchboardEcho
while preserving heavy-state Ledger and MissionControl. Preserve BondRoom and Stability Pool with
a narrow final-Teller compatibility route. The owner selected this option to fork-qualify first
because it minimizes heavy-state re-seeding and eliminates the second Teller swap. Historical
RipeHQ transactions prove that its multi-department confirmations can be executed atomically; the
fork and final Safe calldata must still reproduce that property for this exact replacement set.

It is not a constants-only change. Qualification must prove:

- final Teller's exact producer routing and all normal Teller behavior;
- TellerUtils resolves the same RipeHQ/address bundle as Teller and enforces the Base-specific
  source-unpaused/target-paused, exact-ID, exact-asset validation;
- all five Lootbox scalar values are re-seeded exactly and its admin-driven reward/cleanup path uses
  authoritative balances and fail-closed Ledger removal through Lootbox only;
- HumanResources has no unresolved `pendingContributor` action, or every pending action is
  deterministically preserved/cancelled;
- SwitchboardAlpha has no unresolved pending action, or every pending action is preserved/cancelled;
- SwitchboardEcho has no unresolved pending action, or every pending action is
  preserved/cancelled, and exposes only the hard-bound governance batch wrapper;
- all replacement actions can be staged and confirmed atomically without an intermediate mixed-ID
  state; and
- runtime size, ABI, source/artifact parity and every caller permission remain correct.

### Option B — adopt RH core-vault indirection

Replace MissionControl and every dependent department with the RH pointer model. Because the RH
field is not available in deployed Base and stateful layouts differ, this requires a complete
MissionControl configuration, user-configuration and delegation re-seed plus full dependency
qualification. Base's replacement history shows that the department confirmations themselves can
be atomic and are not unprecedented. The real incremental cost over Option A is the stateful
MissionControl re-seed and the larger dependent-contract proof surface—not a migration of Ledger,
vault balances or every protocol department. Keep it as the fallback because the owner selected
Option A for first qualification, but compare both options honestly on fork evidence. Do not mix
individual RH state-layout changes into Base piecemeal.

### Option C — temporary custodial Teller adapter

This remains technically conceivable only if it reproduces every required Teller path or the
protocol explicitly accepts a full freeze, coordinates a replacement Lootbox for Ledger cleanup,
and has a separate correct steady-state routing plan. It requires two Teller waits and grants broad
Teller authority to bespoke code. It is rejected as the default.

---

## 5. Economics and borrower safety

### 5.1 Share-rate discontinuity

The prior live snapshot measured approximately:

| Asset | Legacy shares per token | Empty target rate | Change |
|---|---:|---:|---:|
| RIPE | 73,382,252.5 | 100,000,000 | +36.27% |
| current Aero LP | 98,595,819.0 | 100,000,000 | +1.42% |

Because future points accrue from shares, a fresh empty target increases RIPE's accrual rate by
roughly 34% relative to the LP even if the stock of imported points is exact. “Preserves points”
must mean preserved point stock and original lock, not preserved future relative accrual flow.

The owner accepted the fresh-vault rate reset on 2026-08-07. The implementation therefore uses the
standard empty-target share calculation and must preserve imported governance-point stock and lock
terms while explicitly recording the changed future accrual flow. No legacy-rate seeding mechanism
is in scope.

Do not improvise target seeding or token donations. A seeder owns claims on donated value unless
the ownership and removal mechanics are explicitly designed, and changing the target import share
formula changes the vault contract under review.

### 5.2 Borrowers and debt health

For every indebted holder, the fork must prove uninterrupted collateral enumeration and valuation
through this sequence:

1. source remains in Ledger while any source asset remains;
2. target is added exactly once before any policy-permitted source removal;
3. target valuation works while the migration-only target is paused;
4. any Lootbox deregistration/removal occurs only after the accepted policy's authoritative
   depletion and reward conditions, while a lazy path remains explicitly enumerable/claimable; and
5. final Teller housekeeping re-evaluates debt health and atomically reverts an unhealthy result.

Test healthy, boundary-health, unhealthy, bad-debt, max-vault-count and liquidation-eligible users.
Also test price movement between batches. No plan may rely on “paused” meaning either included or
excluded from collateral without executing the real Ledger/CreditEngine path on a pinned Base fork.

---

## 6. Manifest and scale gate

An incomplete capped log walk found 429 candidate addresses and at least 349 current holders:
318 RIPE-only, 5 LP-only and 26 with both assets. Those are lower bounds, not a completed census,
because the walk stopped before the deployment block and left approximately 0.79% of RIPE and 0.76%
of LP unreconciled. They imply at least 375 per-asset positions and at least 15 batches at a batch-25
ceiling. Do not publish 349 as the exact holder count.

The approximate 3,510 vault token-transfer events are also not a holder count. Produce a reproducible
manifest from deployment block through a pinned final block by:

1. collecting deposit events;
2. collecting both sides of normal vault transfers;
3. collecting both sides of RipeGov-specific `RipeTokensTransferred` events;
4. deduplicating addresses;
5. batch-reading authoritative `doesUserHaveBalance`, `getTotalAmountForUser`, user-asset
   enumeration, raw `userBalances(user, asset)` shares and gov-data getters at the pinned block; and
6. recording debt, source Ledger participation, assets, amounts, shares, points, unlock and terms.

The manifest is complete only when all of these closure checks pass for every registered asset:

1. `sum(userBalances(user, asset)) == totalBalances(asset)` exactly. Both sides are raw shares; any
   nonzero share residual proves at least one holder is missing and cannot be waived as dust.
2. The sum of per-user `getTotalAmountForUser` values reconciles to the vault token balance within a
   documented bound derived from the vault's share-to-amount formula, decimal offset and per-user
   rounding-down. Do not require exact equality here: user amounts are token units while
   `totalBalances(asset)` is shares, and independent user conversions can round down.
3. The deprecated `0xF8D92a9531205AB2Dd0Bc623CDF4A6Ab4c3a2526` pool has zero total shares,
   zero token balance and no nonzero user shares.

Exact raw-share closure is the only independent completeness proof. Do not add
`getTotalAmountForVault(asset) == ERC20(asset).balanceOf(legacyVault)` as another gate:
`SharesVault._getTotalAmountForVault` directly returns that ERC-20 balance, so the comparison is a
tautology. Record the token balance as manifest evidence, and use check 2 only as a derived rounding
consistency check—not as an independent closure claim.

If any closure check fails, expand the log walk to earlier blocks, rebuild the candidate set and
repeat. No migration manifest or holder count is final before exact share closure.

Every sampled assertion must include its user address, asset, block and getter/calldata. Do not use
an anonymous “sampled recent position.” The exact active holder count, multi-asset holder count,
borrower count, straggler count and projected batches/gas remain open until this census completes.

---

## 7. Fork-qualification plan

Use a pinned Base block and exact deployed bytecode/state. No mainnet write is authorized.

### Gate 0 — settled decisions and operational bindings

Settled owner directions:

- qualify targeted replacements in the existing Base protocol before broader RH-style pointer
  adoption; and
- migrate per asset, retaining source Ledger participation until the accepted replacement-Lootbox
  policy permits cleanup after settling points and protecting every source balance/reward;
- accept the fresh-target share-rate reset;
- administrator-migrate every manifest position without user action, preserve each original target
  unlock/last terms, fail closed on any row, and do not retire the legacy vault while any positive
  raw share remains; and
- use the next live-confirmed available VaultBook ID rather than assuming ID 6.

The owner approved a full-protocol Teller pause for the measured migration window. It stops ordinary
deposits, withdrawals, borrowing, repayment, liquidation, auction purchases, claims and other
Teller routes. The administrator migration entry must remain callable while Teller is paused.

Pausing Teller alone is not a complete RipeGov freeze: `depositFromTrusted` is not pause-gated, and
the legacy vault also authorizes HumanResources, AuctionHouse and CreditEngine operations. The
candidate must independently block or reroute those paths and prove that only the administrator
migration route can touch legacy RipeGov state while wind-down terms are active. Fork qualification
must measure the complete protocol outage and establish the accepted maximum duration before any
mainnet authorization.

Operational binding deferred to post-approval Phase 2:

- re-read VaultBook before the compiled/fork-qualified candidate is bound and use the actual next
  available ID. Phase 1 contract source must not hard-code the historical ID-6 hypothesis.

RH contract-pattern dependency is closed for planning purposes:

- the clean implementation commit `f7f42db1...` was reviewed in `origin/rh@6260726...`;
- Base adopts its TellerUtils extraction, Echo batch ceiling, Lootbox-only Ledger authority and
  no-Ledger-redeploy rule; and
- Base explicitly does not copy its blind immediate RipeGov source removal. The Base delta is the
  admin-driven reward settlement and complete-source cleanup policy in §2.4.

Commit/tree movement after that reviewed anchor is not a blocker. The implementation handoff binds
relevant smart-contract contents and ignores ongoing deployment-only churn.

### Phase 1 / Gate 1 — production smart contracts only, then owner review

The first delivery phase edits only the seven approved production contracts: RipeGov, Teller,
TellerUtils, Lootbox, HumanResources, SwitchboardAlpha, and SwitchboardEcho. It performs no compile,
tests, runtime-size measurement, RPC/fork work, census, interface/ABI/artifact generation,
deployment/runbook work, staging, commit, or push. Ledger, MissionControl, and every other file stay
unchanged.

Present the complete source diff to the owner and stop. State explicitly that it is intentionally
uncompiled and unvalidated. Branch commit/tree changes do not invalidate the candidate. The agent
may compare relevant contract blobs at the boundary, but deployment-only RH changes are ignored.
Phase 2 begins only after the owner explicitly approves the Phase 1 contract diff and authorizes
the remaining non-mainnet qualification work.

### Phase 2 / Gate 2 — post-approval evidence, compilation, and tests

Bind deployment block, final census block, repository commits/trees, verified deployed source and
runtime bytecode hashes. Reproduce every address, registry ID, timelock, permission, asset config,
department scalar and pending-action value. Bind relevant source-content hashes and the Base
applicability decisions in §2.1; do not require the RH branch commit/tree to stay fixed. Complete
the exact holder/borrower/reward census and raw-share closure, compile the owner-approved contracts,
add and run focused unit/integration tests, measure actual runtime sizes, compare storage layouts
and ABIs, and review every new authority path. No tests or artifacts may normalize an incorrect
contract design. Any validation fix that changes a production contract returns that exact diff to
Gate 1 for owner review.

The owner's post-Gate-1 authorization allows the agent to continue through Gates 2, 3, and 4 and
deliver the complete non-mainnet package without routine approval pauses. Only a production-contract
change, real safety/design blocker, or request for a mainnet/external write requires another stop.

### Gate 3 — pinned-fork execution

Execute the exact staged/confirmed department replacements, target registration/configuration,
one-asset-at-a-time wind-down actions, representative migrations, full per-asset manifest
migrations, normal-config restoration after each asset, and final activation. Prove:

- no mixed-ID deposit route exists at any intermediate point;
- the approved full-protocol Teller pause blocks every ordinary Teller path, the administrator
  migration remains callable, every non-pause-gated legacy touch is blocked/rerouted, and the total
  outage is measured;
- exact assets, point stock and original locks import once;
- RIPE and LP wind-down windows never overlap, and migrating one asset does not alter the other
  asset's saved unlock or terms;
- target locks survive until normal terms are restored;
- source Ledger participation remains while any positive source balance, reward entitlement, or
  cleanup-relevant registration remains, and disappears only through Lootbox after administrator
  reward settlement and complete cleanup;
- borrowers stay healthy and collateral never disappears from valuation;
- the deprecated asset is handled deliberately;
- no migrated or failed user can be replayed; and
- target points, share-rate policy and Boardroom power reconcile to the manifest.

### Gate 4 — operations and rollback

Build a calldata-complete Safe runbook with action IDs, earliest confirmation blocks, dependency
order, pre/post reads, batch size/gas, pause state, abort criteria and named rollback. A registry
rollback itself has a 21,600-block delay, so “swap back” is not an immediate safety control.

### Gate 5 — mainnet authorization

Requires a separate owner decision after independent review of the fork evidence and runbook. No
earlier gate authorizes deployment, proposal, confirmation, activation or migration.

---

## 8. Settled decisions and remaining lifecycle gates

Settled on 2026-08-07:

1. **Deployment scenario:** targeted upgrades to the existing Base protocol are the first
   qualification path. Broader RH-style pointer adoption and MissionControl state re-seeding remain
   a fallback only.
2. **Multi-asset transaction model:** migrate per asset. Add the target Ledger entry once, preserve
   the source entry after early assets, administrator-settle each source reward to the user before
   asset deregistration, and allow only Lootbox to remove the source after no balance, reward
   entitlement, or registration still requires it. Fork tests must cover users at the configured
   vault limit, stale zero-balance registrations, and uninterrupted collateral valuation between
   asset transactions.
3. **Share economics:** accept the fresh target's asset-specific share-rate reset. Preserve point
   stock and original lock terms, but do not attempt legacy vault-share-rate preservation.
4. **Migration ownership and completion:** administrators migrate the complete manifest; users take
   no migration action. Each successful target import preserves the original unlock/last terms. A
   failed row reverts atomically, no positive raw-share residual may be waived, and the legacy vault
   is not retired until reconciliation reaches 100%.
5. **Target ID rule:** use the next available ID proved by the final live VaultBook read; do not
   assume ID 6.
6. **Freeze scope:** use a full-protocol Teller pause for the measured migration window. Keep only
   the administrator migration entry callable, independently block/reroute every non-pause-gated
   legacy touch, and require fork evidence for the total duration and borrower/operations risk.
7. **RH applicability:** use the relevant RH contract contents reviewed at historical anchor
   `6260726...`; reuse its TellerUtils validation split, Echo batch ceiling, Lootbox-only removal
   authority and Ledger-preservation rule. Do not require RH's moving commit/tree to match that
   anchor, and ignore deployment-only churn. Do not copy its both-paused endpoint assumption or
   blind immediate RipeGov source removal. Use §2.4's Base administrator reward/cleanup adaptation.
8. **Lifecycle order:** Phase 1 is production smart contracts only and ends at a mandatory owner
   review before compilation or testing. After the owner approves that diff and authorizes
   continuation, the agent completes all remaining non-mainnet evidence, validation, tests, fork
   qualification, artifacts, and runbook work without routine intermediate approval pauses.

No architecture-level Base owner decision remains open. Phase 1 implementation still requires an
explicit dispatch. Its contract diff then requires owner approval before the remaining non-mainnet
work. Deployment, registry actions, activation and mainnet migration always remain separately
unauthorized.

The correct next action after an explicit implementation dispatch is the Phase 1 contract-only
candidate—not census, compilation, testing, or a mainnet proposal. If implementation has not been
explicitly dispatched, remain read-only.
