# Base RH Deployment and Transition Runbook

> **DRAFT — DO NOT EXECUTE**

This is the practical transaction map for deploying RH contracts on Base while
keeping the deployed Ledger unchanged. It is not calldata or authorization.
Field-level checks and failure handling remain in the
[technical appendix](./production-runbook-technical-appendix.md).

## 1. Overall sequence

```text
Deploy inert RH contracts
  → initiate RipeHQ replacement actions
  → wait for RipeHQ timelock
  → freeze protocol writes
  → confirm RipeHQ replacements in the required order
  → apply transition configuration
  → reopen in the transitional state
  → migrate Stability Pool later
  → migrate RipeGov later
```

The Stability Pool and RipeGov migrations are not part of the core cutover.
After the core cutover, Pool 6 handles new Stability activity while Pool 1
remains legacy-only; RipeGov 2 remains active while RipeGov 7 remains paused.

## 2. What we deploy

### New contracts

| Component | Target registry position | Required initial state |
| --- | --- | --- |
| Base transition Defaults | MissionControl constructor input | Exact live Base configuration plus only the approved transition differences |
| MissionControl | RipeHQ 5 | Built from transition Defaults; `preferredStabVaultId` starts at 1 |
| Switchboard registry | RipeHQ 6 | Prepopulated with Alpha–Echo as child IDs 1–5 |
| Switchboard Alpha, Bravo, Charlie, Delta, Echo | Switchboard children 1–5 | Setup delay only until replay/pointer work completes; Alpha constructor binds the live PriceDesk Pyth child, currently expected as 4 |
| VaultBook | RipeHQ 8 | Rows 1–5 clone the exact live version-1 vault addresses; new Stability is 6; new RipeGov is 7 |
| RH Stability Pool | VaultBook 6 | Unpaused so Charlie can validate the new Stability pointer |
| RH RipeGov | VaultBook 7 | Paused, unrouted, and empty |
| RH departments | RipeHQ 9–22 | Candidate ingress blocked; Teller and AuctionHouse paused; Curve consumers bind the live PriceDesk child, currently expected as 2 |
| VaultMigrator | RipeHQ 25 | Paused; constructed with the exact Base legacy-RipeGov reference |
| RH Contributor blueprint | MissionControl HR configuration | Used only for new Contributor clones; existing Contributors remain |

RipeHQ departments 9–22 are:

| ID | Department | ID | Department |
| ---: | --- | ---: | --- |
| 9 | AuctionHouse | 16 | Lootbox |
| 10 | AuctionHouseNFT | 17 | Teller |
| 11 | Boardroom | 18 | Deleverage |
| 12 | BondRoom | 19 | CreditRedeem |
| 13 | CreditEngine | 20 | TellerUtils |
| 14 | Endaoment | 21 | EndaomentFunds |
| 15 | HumanResources | 22 | EndaomentPSM |

### Contracts we do not replace

| Registry position | Component | Required treatment |
| --- | --- | --- |
| RipeHQ itself | RipeHQ and governance Safe | Preserve |
| RipeHQ 1–3 | GREEN, sGREEN, RIPE | Preserve |
| RipeHQ 4 | Ledger | Preserve exactly; never redeploy, replace, upgrade, or migrate |
| RipeHQ 7 | PriceDesk and its children | Preserve exact live root, order, and addresses |
| RipeHQ 23–24 | RIPE and GREEN CCIP pools | Preserve |
| RipeHQ 26–27 | Reserve Engine and Vesting | Leave unused in this program |
| Next Switchboard child / Foxtrot | Reserve-related configuration board | Do not append during the core cutover |
| VaultBook 1–5 | Existing vault addresses | Re-register the same addresses in the same order |
| Existing Contributors | Existing instances and Ledger state | Preserve and prove compatibility with new HumanResources |
| BondBooster | Stateful legacy instance | Preserve is recommended; final O-11 selection is still required |

## 3. Core deployment and RipeHQ cutover

### A. Deploy the candidates without activating them

1. Read the active and pending RipeHQ-8 state. If the previously identified
   update is still pending, cancel that exact update, wait finality, and bind
   the post-cancellation block before continuing. If HQ 8 already changed,
   rederive the topology.
2. Deploy and qualify the RH Contributor blueprint.
3. Generate and freeze the Base transition Defaults from a fresh live snapshot,
   with the actual qualified Contributor-blueprint address.
4. Deploy the Defaults, MissionControl, and the remaining RH candidate stack.
5. Populate the new VaultBook in this exact order:
   `legacy 1, legacy 2, legacy 3, legacy 4, legacy 5, RH Stability 6,
   RH RipeGov 7`.
   Each live row 1–5 must still be version 1; otherwise stop and redesign.
6. Populate the new Switchboard registry with Alpha, Bravo, Charlie, Delta,
   and Echo as child IDs 1–5.
7. Call `setRegistryTimeLockAfterSetup(approvedNonzeroDelay)` on the candidate
   VaultBook and Switchboard registry before either registry becomes active.
8. Keep candidate Teller, AuctionHouse, RipeGov 7, and VaultMigrator paused.
   Candidate AuctionHouse and RipeGov 7 must be paused through the still-active
   legacy Charlie before RipeHQ 6 is replaced.

Deploying these contracts does not change production routing.

### B. Initiate the RipeHQ actions

Initiate these native RipeHQ operations while the legacy system remains live:

| Operation | RipeHQ IDs |
| --- | --- |
| `startAddressUpdateToRegistry(id, newAddress)` | 5, 6, and 8–22 |
| `startAddNewAddressToRegistry(VaultMigrator, description)` | VaultMigrator as the only append, expected to become 25 |
| No action | 1–4, 7, 23–24, and 26–27 |

Wait until every operation reaches its actual `confirmBlock`. Do not assume a
fixed delay. If the live configuration copied into MissionControl changes
while these actions mature, rebuild the transition candidate rather than
patching the difference during cutover.

### C. Execute the core cutover

Before each affected RipeHQ activation, execute its approved custody/allowance
disposition and clear every temporary local governor or pending governance
change. Department balances, approvals, and local authority do not move when
the RipeHQ address changes.

| Order | Transaction | Required result |
| ---: | --- | --- |
| 1 | Pause both legacy- and candidate-generation Teller, AuctionHouse, HR/Bond/Lootbox/Credit trusted producers, Deleverage, and every other affected write path; freeze unrelated configuration and price writes; wait the qualified later Base block | Source balances and position counts are unchanged before the first confirmation |
| 2 | Execute `confirmAddressUpdateToRegistry(8)` for VaultBook | Active VaultBook resolves exact rows 1–7 |
| 3 | In one assertion-capable atomic transaction, execute `confirmAddressUpdateToRegistry(5)` for MissionControl and then `confirmAddressUpdateToRegistry(6)` for Switchboard | Both calls return `True`; new boards resolve the new MissionControl; the complete freeze still holds and candidate AuctionHouse/RipeGov 7 remain paused before continuing |
| 4 | Execute `confirmAddressUpdateToRegistry(id)` for RipeHQ 9–22 | Each ID resolves its exact RH department; ingress remains blocked |
| 5 | Execute `confirmNewAddressToRegistry(VaultMigrator)` | It returns exactly RipeHQ ID 25 and remains paused |
| 6 | Require fresh `Charlie.actionTimeLock == 0`, then replay the approved configuration, `userConfig`, delegations, and pending-state dispositions not established by the transition Defaults | Every readback matches the transition manifest; a nonzero Charlie delay is a stop |
| 7 | Through new Charlie, call `setPreferredStabVaultId(6)` and execute the resulting zero-delay setup action | Pool 6 is unpaused before initiation and execution; final value is 6 |
| 8 | Execute and clear every setup-zero action, prove no production-surviving action was started at zero delay, then call `setActionTimeLockAfterSetup(approvedNonzeroDelay)` on Alpha–Echo and HumanResources | Every applicable `actionTimeLock` is the approved nonzero value; only afterward may an approved production-surviving action be initiated |
| 9 | Establish the approved Pool-6 seed/capacity, or execute the approved empty-pool posture | Pool-6 balances/capacity and auction fallback match the selected launch policy |
| 10 | Reopen Teller and approved trusted producers; run Pool-6 and legacy-path canaries; reopen AuctionHouse last | New Stability activity uses 6; fallback works; RipeGov 2 remains active |

Immediately before transaction 5, require:

- `RipeHQ.getNumAddrs() == 24`;
- raw `RipeHQ.numAddrs() == 25`;
- no other pending append, mature or immature.

Immediately after transaction 5, require:

- `getAddr(25) == VaultMigrator`;
- `getNumAddrs() == 25`;
- raw `numAddrs() == 26`.

Reconfirm after the cutover that RipeHQ ID 4 still points to the exact deployed
Ledger.

## 4. Core configuration changes

Most configuration must be present in MissionControl at deployment through the
dedicated transition Defaults. Do not deploy the greenfield RH Defaults and do
not plan to reconstruct the complete live configuration after RipeHQ 5 changes.

### Values set by the transition Defaults

| Parameter/configuration | Transition value |
| --- | --- |
| sGREEN `vaultIds` | `[6]` |
| GREEN/USDC LP `vaultIds` | `[6]` |
| `priorityStabVaults` | `[(6, LP), (6, sGREEN)]` in the approved asset order |
| Every `specialStabPoolId` | `0` or `6`; never `1` |
| RIPE `vaultIds` | `[2]` |
| RIPE/LP `vaultIds` | `[2]` |
| `coreRipeGovVaultId` | `2` |
| `preferredStabVaultId` | `1` temporarily; changed to `6` during the frozen cutover |
| `stabPoolRipePerDollarClaimed` | Preserve the approved live transitional rate; do not zero it during the core cutover |
| RipeGov lock/boost/fee terms | Preserve exact live values |
| `hrConfig.contribTemplate` | New RH Contributor blueprint |
| PriceDesk, TrainingWheels, Underscore, pools, feeds, debt, reward, HR, bond, whitelist, and signer configuration | Preserve exact live values unless separately listed as an approved transition difference |

### Values changed during the cutover

| When | Parameter/state | Change |
| --- | --- | --- |
| After RipeHQ 5/6 replacement | `userConfig` and delegations | Replay exact approved live rows |
| After RipeHQ 5/6 replacement | `preferredStabVaultId` | `1 → 6` through Charlie |
| After pointer execution | Alpha–Echo and HumanResources `actionTimeLock` | Setup value `0 →` approved nonzero production delay |
| Before reopen | Pool-6 seed/capacity | Exact fresh calculated amount, or approved empty-pool state |
| Before reopen | Teller/producers/AuctionHouse pause state | Teller and approved producers reopen first; AuctionHouse reopens last |

The exact production delays, Pool-6 seed amount/assets, and any inactive
MissionControl-state dispositions remain run-specific inputs; they are not
hardcoded planning values.

## 5. State immediately after the core cutover

| Component | Live state |
| --- | --- |
| Ledger | Original deployed Ledger, unchanged at RipeHQ 4 |
| Stability Pool 1 | Legacy explicit-ID exits, claims, and redemptions only; never an RH liquidation route; `isStabVaultId(1) == True` |
| Stability Pool 6 | All new Stability deposits and all Stability liquidation routing; `isStabVaultId(6) == True` |
| RipeGov 2 | Still the active core RipeGov; RIPE and RIPE/LP routes remain `[2]` |
| RipeGov 7 | Paused, unrouted, and empty |
| VaultMigrator | Registered at RipeHQ 25 and paused |

This is a valid production state. The two user migrations can happen in later,
separately scheduled windows.

## 6. Later Stability Pool 1 → 6 migration

Do this before the RipeGov migration. Recompute all users, shares, claims,
prices, custody, and the governance seed from the execution block. Do not use
`$250` or another planning amount as calldata: the seed entitlement must cover
the freshly valued claim basket plus the approved buffer. `badDebt` must be
zero.

| Order | Transaction | Key parameter/result |
| ---: | --- | --- |
| 1 | Through Alpha call `setAutoStakeParams(liveRatio, liveDurationRatio, 0)`; initiate and mature the Bravo `[6,1]`/`[6]`, claim-tail registration/deregistration, and—if needed—terminal reward-tuple actions | Record each actual Alpha/Bravo/Charlie action ID, maturity, expiry, and restoration; reserve immediate Charlie claim-flag writes for the execution window |
| 2 | Freeze AuctionHouse, trusted producers, unrelated configuration, and price changes | Teller remains available only for the qualified governance seed/claim window |
| 3 | Execute the legacy Stability reward change | Set `stabPoolRipePerDollarClaimed` to `0`; preserve `autoStakeRatio` and `autoStakeDurationRatio` |
| 4 | In one assertion-capable atomic transaction, execute `[6,1]`, deposit the calculated governance seed into Pool 1, then restore `[6]` | Pool 6 remains first/default; no route remains `[6,1]` afterward |
| 5 | In a later Base block, claim the full eligible Pool-1 basket to governance and execute the approved tail-clearing lifecycle | Same-user ordinary seed and claim are not placed in the same block; every additional same-user claim uses another qualified later block and fresh entitlement preflight |
| 6 | Pause Teller and prove claim closure | Economic claims are zero; any raw remainder equals only the explicitly approved tail manifest |
| 7 | Wait the qualified later block, refresh the census and `lastTouch`, then unpause VaultMigrator and migrate a canary, measured user batches, and governance last through Echo | Pool 1 and Pool 6 remain unpaused; Teller remains paused during migration |
| 8 | Pause VaultMigrator, establish the exact terminal reward tuple, reopen Teller/producers, and reopen AuctionHouse last | Every intended position and custody delta reconciles in Pool 6 |

Batch limits:

- A generic migration child contains 1–25 unique users.
- Each included generic-route user has at most 20 registered source slots.
- An explicit-by-assets child contains at most 20 unique positive assets.
- The returned migrated-position count must equal the positive manifest count.
- Each claim call contains at most 15 asset pairs and at least one positively
  valued pair.

## 7. Later RipeGov 2 → 7 migration

Start only after Stability migration is complete. Before transaction authorship,
select and qualify the actual migrator behavior (current all-assets-per-user or
a newly implemented serial procedure) and the no-forfeiture cleanup route. The
known temporary-term mechanism expects a freshly confirmed pre-window
`minLockDuration` of 43,200; if live state differs, stop and requalify it.

| Order | Transaction | Key parameter/result |
| ---: | --- | --- |
| 1 | Through Bravo `setAssetDepositParams`, initiate both RIPE and RIPE/LP `[2,7]` bridge actions, wait for their actual maturity, then execute both while 2 remains core/default | `[2] → [2,7]`; every other deposit parameter remains unchanged |
| 2 | Through Alpha, initiate both temporary term actions and both exact-original restoration actions | Record actual IDs; do not execute the term changes yet |
| 3 | Freeze Teller and every HR, BondRoom, Lootbox, Credit, Deleverage/AuctionHouse, trusted-producer, and unrelated-configuration path; wait the required later Base block and refresh the census | RipeGov 2/7 state is unchanged before pointer initiation |
| 4 | In one atomic transaction, unpause 7, initiate Charlie `coreRipeGovVaultId: 2 → 7`, then re-pause 7 | 7 remains empty/pristine while the pointer action matures |
| 5 | After Charlie maturity, atomically unpause 7, execute the pointer, and re-pause 7 | `coreRipeGovVaultId == 7`; `isRipeGovVaultId(2) == True`; `isRipeGovVaultId(7) == True`; 7 is still paused |
| 6 | Initiate final RIPE and RIPE/LP routes `[7]` and wait for maturity | Keep `[2,7]` active and the protocol frozen until migration finishes |
| 7 | Execute both temporary legacy term actions | Expected `minLockDuration: 43,200 → 43,199`; weight, freeze flag, max duration, max boost, `canExit`, and `exitFee` do not change; never substitute `exitFee: 8000 → 8001` |
| 8 | In the required later block, unpause VaultMigrator and migrate canary plus measured batches through Echo | Teller paused; source 2 unpaused; target 7 paused; exact migrated-position counts reconcile |
| 9 | Restore both exact pre-window term tuples, execute matured final routes `[7]`, and pause VaultMigrator | `minLockDuration` returns to the freshly bound original value, currently expected as `43,200`; RIPE and RIPE/LP routes become `[7]` |
| 10 | Settle source rewards directly to users, then clean registrations and Ledger participation through the approved Lootbox/deployed-Ledger authority path | No reward is forfeited or auto-staked; `isRipeGovVaultId(2) == True` remains |
| 11 | Reopen RipeGov 7, Teller, and approved producers | 7 is active and every migrated user/contributor reconciles |

RipeGov legacy batch limits are at most 25 unique users and 20 aggregate
registered source slots per batch.

## 8. Values required before production calldata

| Required input | Why it is still open |
| --- | --- |
| Final RH release, compiler, deployments, runtimes, and Base block/hash | Must bind the actual release and live state |
| Dedicated Base transition Defaults | Neither unchanged `DefaultsBaseLive` nor greenfield `DefaultsRobinhood` is correct |
| Inactive/stale MissionControl-state dispositions | Constructor Defaults do not reproduce every dormant storage row automatically |
| Final BondBooster posture | Preserving the stateful legacy instance is recommended but O-11 remains open until approved |
| Pool-6 seed/capacity or empty-pool choice | Must be calculated and approved from current assets and fallback behavior |
| Production registry/action delays | Exact nonzero VaultBook and Switchboard-registry `registryChangeTimeLock` plus Alpha–Echo and HumanResources `actionTimeLock` values are policy inputs |
| Action IDs, maturity, expiry, and incident headroom | Must cover the actual ordered execution window; native RipeHQ confirmations have a `confirmBlock` but no board-style expiry |
| Assertion-capable executor or exact safe-hold mechanism | Registry, board, claim, and migration calls can return soft `False`/zero values |
| Stability terminal reward tuple and claim-tail treatment | Depends on the fresh claim census and custody policy |
| RipeGov migration procedure | Current all-assets behavior conflicts with the older serial policy |
| RipeGov cleanup implementation | Must deliver every legacy reward without user action, auto-staking, or forfeiture |

Do not create Safe calldata until these values are closed and the exact
transactions above pass the Base fork.

## 9. Hard execution stops

Do not continue if:

- RipeHQ ID 4 or the deployed Ledger changes;
- VaultBook rows 1–7, Switchboard children 1–5, or VaultMigrator ID 25 differ;
- Pool 1 appears in an RH AuctionHouse route;
- RipeGov 7 receives state before its migration window;
- a `bool`, assigned ID, migrated count, or claimed USD result cannot be
  asserted before its dependent transaction;
- the freeze is incomplete or source balances continue changing;
- calldata, Safe nonce, action ID, maturity, expiry/headroom, runtime, or live configuration
  differs from the forked transaction package.

For detailed field assertions, tail cases, action records, and recovery paths,
use the [technical appendix](./production-runbook-technical-appendix.md).
