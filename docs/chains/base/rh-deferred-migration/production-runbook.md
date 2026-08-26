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
| VaultBook | RipeHQ 8 | Rows 1–5 use the exact current vault addresses in the same order; new Stability is 6; new RipeGov is 7 |
| RH Stability Pool | VaultBook 6 | Unpaused so Charlie can validate the new Stability pointer |
| RH RipeGov | VaultBook 7 | Paused, unrouted, and empty |
| RH departments | RipeHQ 9–22 | Every write-capable candidate paused or otherwise blocked; Curve consumers bind the live PriceDesk child, currently expected as 2 |
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
| VaultBook 1–5 | Existing vault addresses | Re-register the same addresses in the same order |
| Existing Contributors | Existing instances and Ledger state | Preserve and prove compatibility with new HumanResources |
| BondBooster | Stateful legacy instance | Preserve is recommended; governance choice remains open below |

Register only Alpha, Bravo, Charlie, Delta, and Echo as Switchboard child IDs
1–5, then stop. Do not append a sixth child during this program.

### Current Base anchors — refresh before use

These are observations from Base blocks `50,466,318–50,466,379` on
2026-08-25. They are not calldata. Refresh the complete address/configuration
manifest immediately before deployment and again before the execution window.

| Item | Observed value |
| --- | --- |
| RipeHQ | `0x6162df1b329E157479F8f1407E888260E0EC3d2b` |
| Ledger — must remain RipeHQ 4 | `0x365256e322a47Aa2015F6724783F326e9B24fA47` |
| MissionControl / PriceDesk / VaultBook | `0x559E53F42b68b4995732Dba4aF300796761DBC19` / `0x2F7901BE53cC94AEF174f1a0764430840360Ef53` / `0xB758e30C14825519b895Fd9928d5d8748A71a944` |
| VaultBook 1–5 | `1: 0x2a157096af6337b2b4bd47de435520572ed5a439`; `2: 0xe42b3dC546527EB70D741B185Dc57226cA01839D`; `3: 0xf75b566eF80Fde0dEfcC045A4d57b540eb43ddfD`; `4: 0xce2E96C9F6806731914A7b4c3E4aC1F296d98597`; `5: 0x4549A368c00f803862d457C4C0c659a293F26C66` |
| Required PriceDesk children | Curve ID 2: `0x7B2aeE8B6A4bdF0885dEF48CCda8453Fdc1Bba5d`; Pyth ID 4: `0x16371fAf6f603f8d8D6cef8C46253c80AdEe8b98` |
| Pending RipeHQ-8 update to cancel | `0x09f45F56b218756ab092f7470F8199db56849867`; confirmable since block `49,911,775` |
| Debt/rewards | `badDebt = 0`; global debt limit `24,000 GREEN`; Stability reward `0.01 RIPE/$`; auto-stake ratio/duration ratio `75% / 33%` |
| Borrowing/oracle | Per-user debt limit `1,000 GREEN`; keeper fee `100 bps`, minimum `1 GREEN`, maximum `25,000 GREEN`; price stale time `86,400 seconds` |
| Active RipeGov terms | Both active assets: min/max `43,200 / 47,304,000`, max boost `20,000`, `canExit = true`, `exitFee = 8,000`, freeze on bad debt; weights RIPE `10,000`, RIPE/LP `15,000` |
| Current registry timing | RipeHQ and VaultBook: `21,600` blocks, approximately 12 hours at Base's approximately 2-second block cadence |

The committed `DefaultsBaseLive` still contains a `40,000 GREEN` global debt
limit. Live MissionControl is already at `24,000 GREEN`; therefore it cannot be
used unchanged as the transition Defaults.

## 3. Core deployment and RipeHQ cutover

### A. Deploy the candidates without activating them

1. Read the active and pending RipeHQ-8 state. The update to
   `0x09f45F56b218756ab092f7470F8199db56849867` was still pending at the
   observation above. Cancel that exact update, wait finality, and refresh all
   live values before continuing. If the row already changed, stop and
   rederive the topology.
2. Deploy and qualify the RH Contributor blueprint.
3. Generate and freeze the Base transition Defaults from a fresh live snapshot,
   with the actual qualified Contributor-blueprint address.
4. Deploy the Defaults, MissionControl, and the remaining RH candidate stack.
5. Populate the new VaultBook in this exact order:
   `legacy 1, legacy 2, legacy 3, legacy 4, legacy 5, RH Stability 6,
   RH RipeGov 7`.
   Bind the exact current source addresses and names immediately before the
   append. Source-registry version metadata is not cloned; every fresh row in
   the candidate registry starts at version 1.
6. Populate the new Switchboard registry with Alpha, Bravo, Charlie, Delta,
   and Echo as child IDs 1–5.
7. Call `setRegistryTimeLockAfterSetup(approvedNonzeroDelay)` on the candidate
   VaultBook and Switchboard registry before either registry becomes active.
8. Deploy Teller and VaultMigrator paused. Through the still-active legacy
   Charlie, pause candidate AuctionHouse and RipeGov 7. For each remaining
   candidate with an effective pause control and exposed write ingress, pause
   it; otherwise bind and assert its exact ingress-blocking mechanism. If a
   target is already paused, assert its state instead of submitting a no-op
   pause. Do not globally pause candidate CreditEngine or Lootbox. Keep them
   unpaused, block all of their upstream user/trusted producer entrypoints, and
   prove debt/point housekeeping is callable before IDs 13 and 16 confirm.
   Pool 6 stays unpaused so Charlie can validate the pointer to 6.

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

Replacing a RipeHQ address does not move that contract's storage, balances, or
allowances. Complete source custody/pending-action work before confirmation;
complete candidate configuration replay before reopening. Every old address
also needs a fresh token/native-balance and allowance manifest.

| RipeHQ ID | State that does not move | Required disposition before confirmation/reopen |
| ---: | --- | --- |
| 9, 10, 11, 19, 20 | No material user state; possible token dust/allowances | **Before confirm:** require zero or explicitly recovered balances/allowances. **Before reopen:** verify applicable pause state. |
| 12 BondRoom | Local `bondBooster` pointer | **At deployment:** preserve the live Booster, observed as `0xA1872467AC4fb442aeA341163A65263915ce178a`, unless governance separately approves a complete Booster-state migration. |
| 13 CreditEngine | `undyVaulDiscount`, `buybackRatio`, Curve child ID | **At deployment:** bind Curve ID 2. **After ID 13 confirms and before reopen:** if either fresh live value differs from the constructor, unpause CreditEngine only after all of its Teller/AuctionHouse/CreditRedeem/Deleverage ingress is blocked, initiate/execute the zero-delay Alpha action(s), and verify. Keep `updateDebtForUser` callable through the Pool-6 seed; do not re-pause CreditEngine before that deposit. Observed values are `5,000 / 2,000`; the constructor sets `5,000 / 0`. |
| 14 Endaoment + 21 EndaomentFunds | Native/ERC-20 treasury custody, allowances, WETH/ETH and Curve bindings | **Before confirming either ID:** use active Endaoment to convert native ETH to WETH, sweep every old Funds/Endaoment balance to governance, fund candidate Funds, and prove old balances/allowances are zero. |
| 15 HumanResources | Pending Contributor actions and `legacyContributorRipeGovVaultId` rows | **Before confirm:** complete/cancel every pending action. **Before reopen:** replay every required legacy-vault mapping; each existing Contributor instance retains its own operational state and remains registered in Ledger. |
| 16 Lootbox | Underscore reward settings and `lastUnderscoreSend`; points/rewards themselves remain in Ledger | **At deployment:** use the legacy `43,200`-block minimum and fresh-read interval/reward values. **Before reopen:** preserve the old cooldown by delaying enablement if necessary because the new contract resets `lastUnderscoreSend`. |
| 17 Teller | Pause state and Curve child ID; no user configuration | **At deployment:** paused with Curve ID 2. **Throughout freeze:** block every `depositFromTrusted` producer because Teller pause does not block that path. |
| 18 Deleverage | Four live legacy parameters, four RH-only payoff/dust parameters, and per-user `lastDeleverageBlock` | **At deployment:** fresh-read the four legacy values and use the approved RH-only values. The existing Base migration candidate is `10^15 / 100 / 0 / 0` for full-payoff buffer, overage bps, dust threshold, and dust bps. **Before reopen:** approve the per-user cooldown reset or keep Deleverage paused until one old cooldown has elapsed. |
| 22 EndaomentPSM | USDC/yield custody, flags, fees, caps, allowlists, yield position, interval length and counters | **Before confirm:** disable mint/redeem and move or unwind custody. **Before reopen:** replay all settings and wait for active intervals to expire or explicitly approve the counter reset. |

Execute the frozen cutover in this order:

Complete or cancel non-custody timelocked source actions, including every
pending HumanResources action, before entering this table. Do not perform the
final custody sweep until the refill paths are frozen in step 1.

| Step | Write or check | Required result |
| ---: | --- | --- |
| 1 | Safe batch: pause each still-open Teller, AuctionHouse, HR, BondRoom, CreditRedeem, Deleverage, and every other producer that can refill custody or mutate positions. Do **not** globally pause CreditEngine or Lootbox: block their borrow/redeem/claim/auto-stake and trusted-deposit callers while keeping only `CreditEngine.updateDebtForUser`, Lootbox point accounting, and required settlement reads callable. Disable PSM mint/redeem and block its user routes, but leave only the exact old PSM/Endaoment custody helpers callable. Freeze unrelated configuration and price writes. | No producer can refill old custody; only the named custody and housekeeping paths remain callable; already-paused candidates are read/asserted, not paused again |
| 2 | One atomic disposition batch: move or unwind old PSM custody, then pause PSM if still open (otherwise assert paused); convert old EndaomentFunds native ETH to WETH, sweep all old Endaoment/Funds assets to governance, fund the candidate addresses, then pause old Endaoment if still open (otherwise assert paused) | After the full freeze, every old balance/allowance/pending-state readback is zero or matches the approved residual list |
| 3 | Read-only: wait until the Ledger action block advances, then compare source balances and position counts | State is unchanged before the first registry confirmation |
| 4 | Execute and assert `confirmAddressUpdateToRegistry(8) == True` | Active VaultBook resolves exact rows 1–7 |
| 5 | One atomic transaction: execute `confirmAddressUpdateToRegistry(5)` and then `confirmAddressUpdateToRegistry(6)` through an executor that reverts unless both return `True` | MissionControl and Switchboard both change or neither does; Alpha–Echo resolve the new MissionControl |
| 6 | Read-only: recheck the full freeze plus candidate AuctionHouse and RipeGov-7 pause states | Nothing changed except the intended registry rows |
| 7 | Execute and assert `confirmAddressUpdateToRegistry(id) == True` for each ID 9–22 | Every ID resolves its exact RH department and all ingress remains blocked |
| 8 | Execute `confirmNewAddressToRegistry(VaultMigrator)` and assert its returned ID | Exactly ID 25; VaultMigrator remains paused |
| 9 | Require `Charlie.actionTimeLock == 0`; execute all **before reopen** department settings plus the approved MissionControl `userConfig`, delegation, and stale/pending-state replay not established by the transition Defaults. For an ordinary target whose setter rejects the paused state, atomically unpause, set, verify, and re-pause it. For CreditEngine and Lootbox, instead end in the approved housekeeping-only posture: both are unpaused, their upstream producer entrypoints remain blocked, and `updateDebtForUser`/point accounting are proven callable. | Every readback matches the approved configuration table; no user or trusted producer ingress is open |
| 10 | Through new Charlie call `setPreferredStabVaultId(6)`, record its action ID, then call `executePendingAction(actionId)` while the setup delay is zero | Pool 6 is unpaused and supports sGREEN; final pointer is 6 |
| 11 | Clear every zero-delay setup action, prove no production-surviving action was started at zero delay, then call `setActionTimeLockAfterSetup(approvedNonzeroDelay)` on Alpha–Echo and HumanResources | All production delays are nonzero before normal governance actions begin |
| 12 | If Pool 6 is funded, use one atomic bundle to assert the freeze and housekeeping posture, unpause Teller, deposit every approved seed asset with explicit `vaultId = 6`, and re-pause Teller. Otherwise prove the approved empty-pool posture. | The entire seed bundle succeeds or reverts; Pool-6 balances/capacity and auction fallback match the chosen launch posture |
| 13 | Reopen Teller and approved producers; run Pool-6 and legacy-explicit-ID canaries; reopen AuctionHouse last | New Stability activity uses 6, fallback works, and RipeGov 2 remains active |

VaultBook goes first because the replacement MissionControl routes Stability
assets to ID 6, which the old VaultBook does not contain. Keep the protocol
frozen until step 5 completes: RH VaultBook's classification-dependent
update/disable and Stability-mint checks are unavailable against the old
MissionControl. If step 5 fails, hold the freeze and use the separately
rehearsed forward-recovery transaction.

Immediately before the VaultMigrator append confirmation, require:

- `RipeHQ.getNumAddrs() == 24`;
- raw `RipeHQ.numAddrs() == 25`;
- no other pending append, mature or immature.

Immediately after the VaultMigrator append confirmation, require:

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

New Pool-1 deposits fail once the asset routes are `[6]`. Existing users can
still withdraw, claim, and redeem by explicitly passing `vaultId = 1`, subject
to normal pause, permission, and debt-health checks. The UI must expose that
explicit legacy-ID exit path and must not pass zero for Pool-1 claims or
redemptions. New/default Stability selection uses Pool 6.

This is a valid production state. The two user migrations can happen in later,
separately scheduled windows.

## 6. Later Stability Pool 1 → 6 migration

Do this before the RipeGov migration. Recompute all users, shares, claims,
prices, custody, and the governance seed from the execution block. Do not use
`$250` or another planning amount as calldata: the seed entitlement must cover
the freshly valued claim basket plus the approved buffer. Require
`Ledger.badDebt() == 0` before the canary and every migration batch.

| Step | Write or check | Required result |
| ---: | --- | --- |
| 1 | Alpha: initiate `setAutoStakeParams(liveRatio, liveDurationRatio, 0)` and, if required, the exact terminal restoration tuple | Auto-stake ratios stay unchanged; record each action ID/maturity/expiry |
| 2 | Bravo: separately initiate the temporary asset routes `[6,1]` and the restorations `[6]` | Record both action sets; Pool 6 stays first |
| 3 | Initiate each required timelocked claim-asset registration and its corresponding later deregistration action; list but do not execute each immediate Charlie claim-permission enable/disable write | Each selected tail-remediation pair has an explicit open/close lifecycle; already-active claim pairs stay unchanged unless the fresh census requires otherwise |
| 4 | Wait for the actual maturities and recheck every action ID, expiry, route, claim pair, price, and governance entitlement | No stale planning value enters calldata |
| 5 | Freeze AuctionHouse, trusted producers, unrelated configuration, and price changes | Teller remains open only for the governance seed/claim calls |
| 6 | Execute the Alpha reward-zero action | `stabPoolRipePerDollarClaimed = 0`; both auto-stake ratios are unchanged |
| 7 | One atomic transaction: execute `[6,1]`, deposit the calculated governance seed into Pool 1, then execute the restorations `[6]`; revert unless every action succeeds | No route remains `[6,1]` after the transaction |
| 8 | In a later Base action block, claim the full eligible Pool-1 basket to governance and execute the approved claim-asset closeout | Never seed and claim for the same user in one block; each later claim gets a fresh entitlement preflight |
| 9 | Pause Teller and prove claim closure | Economic claims are zero; any raw remainder is only the explicitly approved nonclaimable/dust list |
| 10 | Wait for the next required action block, refresh the user/asset census and `lastTouch`, recheck `badDebt == 0`, then unpause VaultMigrator and migrate a canary, measured batches, and governance last through Echo; recheck `badDebt == 0` before every batch | Pool 1 and 6 remain unpaused; Teller remains paused; each return count matches the manifest |
| 11 | Pause VaultMigrator, execute the approved terminal reward tuple, reopen Teller/producers, and reopen AuctionHouse last | Every intended position and custody delta reconciles in Pool 6 |

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
Require `Ledger.badDebt() == 0` immediately before the canary and every
migration batch. If it is nonzero, stop: both legacy RipeGov asset configs have
`shouldFreezeWhenBadDebt = true`, so the source withdrawals will revert.

| Order | Transaction | Key parameter/result |
| ---: | --- | --- |
| 1 | Through Bravo `setAssetDepositParams`, initiate both RIPE and RIPE/LP `[2,7]` bridge actions, wait for their actual maturity, then execute both while 2 remains core/default | `[2] → [2,7]`; every other deposit parameter remains unchanged |
| 2 | Through Alpha, initiate both temporary term actions and both exact-original restoration actions | Record actual IDs; do not execute the term changes yet |
| 3 | Freeze Teller and every HR, BondRoom, Lootbox, Credit, Deleverage/AuctionHouse, trusted-producer, and unrelated-configuration path; wait the required later Base block and refresh the census | RipeGov 2/7 state is unchanged before pointer initiation |
| 4 | In one atomic transaction, unpause 7, initiate Charlie `coreRipeGovVaultId: 2 → 7`, then re-pause 7 | 7 remains empty/pristine while the pointer action matures |
| 5 | After Charlie maturity, atomically unpause 7, execute the pointer, and re-pause 7 | `coreRipeGovVaultId == 7`; `isRipeGovVaultId(2) == True`; `isRipeGovVaultId(7) == True`; 7 is still paused |
| 6 | Initiate final RIPE and RIPE/LP routes `[7]` and wait for maturity | Keep `[2,7]` active and the protocol frozen until migration finishes |
| 7 | Execute both temporary legacy term actions | Expected `minLockDuration: 43,200 → 43,199`; weight, freeze flag, max duration, max boost, `canExit`, and `exitFee` do not change; never substitute `exitFee: 8000 → 8001` |
| 8 | In the required later block, recheck `badDebt == 0`, unpause VaultMigrator, and migrate the canary plus measured batches through Echo; recheck `badDebt == 0` before every batch | Teller paused; source 2 unpaused; target 7 paused; exact migrated-position counts reconcile |
| 9 | Restore both exact pre-window term tuples, execute matured final routes `[7]`, and pause VaultMigrator | `minLockDuration` returns to the freshly bound original value, currently expected as `43,200`; RIPE and RIPE/LP routes become `[7]` |
| 10 | Settle source rewards directly to users, then clean registrations and Ledger participation through the approved Lootbox/deployed-Ledger authority path | No reward is forfeited or auto-staked; `isRipeGovVaultId(2) == True` remains |
| 11 | Reopen RipeGov 7, Teller, and approved producers | 7 is active and every migrated user/contributor reconciles |

RipeGov legacy batch limits are at most 25 unique users and 20 aggregate
registered source slots per batch. The observed source has three raw registered
asset rows, although only RIPE and RIPE/LP are active; count every registered
slot, not only positive balances or active configurations.

## 8. Decisions still required

| Decision | Required choice |
| --- | --- |
| Production delays | Set the nonzero VaultBook/Switchboard registry delays and Alpha–Echo/HumanResources action delays |
| BondBooster | Preserve the live stateful Booster (recommended), or approve and qualify a complete state migration |
| Pool-6 launch | Exact seed/capacity, or an explicitly tested empty-pool launch |
| Department resets | Approve or avoid the Lootbox cooldown, Deleverage per-user cooldown, and PSM interval-counter resets described above |
| Deleverage RH-only parameters | Approve the existing Base candidate `10^15 / 100 / 0 / 0`, or bind another qualified payoff/dust tuple |
| Stability closeout | Final reward tuple plus the exact nonclaimable/dust asset treatment |
| RipeGov procedure | Use and qualify the current all-assets-per-user migrator, or implement and qualify a serial alternative |
| RipeGov reward cleanup | Exact no-forfeiture payment and registration/Ledger cleanup transaction |
| Return-value enforcement | Executor that reverts on soft `False`/zero results, or a separately approved safe-hold mechanism for each such call |

After those choices are closed, bind the exact RH commit/compiler/runtimes and
deployed addresses; generate the dedicated transition Defaults from the fresh
live snapshot; and fill the actual Safe nonce, action IDs, confirmation blocks,
expiries, and incident headroom. Do not create production calldata until that
package passes the Base fork.

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
