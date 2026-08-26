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

These are observations from Base blocks `50,466,318–50,467,897` on
2026-08-25–26. They are not calldata. Refresh the complete address/configuration
manifest immediately before deployment and again before the execution window.

| Item | Observed value |
| --- | --- |
| RipeHQ | `0x6162df1b329E157479F8f1407E888260E0EC3d2b` |
| Ledger — must remain RipeHQ 4 | `0x365256e322a47Aa2015F6724783F326e9B24fA47` |
| MissionControl / PriceDesk / VaultBook | `0x559E53F42b68b4995732Dba4aF300796761DBC19` / `0x2F7901BE53cC94AEF174f1a0764430840360Ef53` / `0xB758e30C14825519b895Fd9928d5d8748A71a944` |
| VaultBook 1–5 | `1: 0x2a157096af6337b2b4bd47de435520572ed5a439`; `2: 0xe42b3dC546527EB70D741B185Dc57226cA01839D`; `3: 0xf75b566eF80Fde0dEfcC045A4d57b540eb43ddfD`; `4: 0xce2E96C9F6806731914A7b4c3E4aC1F296d98597`; `5: 0x4549A368c00f803862d457C4C0c659a293F26C66` |
| Required PriceDesk children | Curve ID 2: `0x7B2aeE8B6A4bdF0885dEF48CCda8453Fdc1Bba5d`; ID 3 is empty and must remain empty; Pyth ID 4: `0x16371fAf6f603f8d8D6cef8C46253c80AdEe8b98` |
| Pending RipeHQ-8 update to cancel | `0x09f45F56b218756ab092f7470F8199db56849867`; confirmable since block `49,911,775` |
| Debt/rewards | `badDebt = 0`; global debt limit `24,000 GREEN`; Stability reward `0.01 RIPE/$`; auto-stake ratio/duration ratio `75% / 33%` |
| Borrowing/oracle | Per-user debt limit `1,000 GREEN`; keeper fee `100 bps`, minimum `1 GREEN`, maximum `25,000 GREEN`; price stale time `86,400 seconds` |
| Active RipeGov terms | Both active assets: min/max `43,200 / 47,304,000`, max boost `20,000`, `canExit = true`, `exitFee = 8,000`, freeze on bad debt; weights RIPE `10,000`, RIPE/LP `15,000` |
| Current registry timing | RipeHQ and VaultBook: `21,600` blocks, approximately 12 hours at Base's approximately 2-second block cadence |
| Mutable-board timing | Active Switchboard registry, Alpha–Echo, and preserved PriceDesk currently read `0`. Every replacement board/registry setup delay must be finalized to its approved nonzero production value; PriceDesk has no core-cutover write. |
| Relevant `vaultIds` / special routes | sGREEN `[1]`; GREEN/USDC LP `[1]`; WETH `[3]`; cbBTC `[3]`. Separately, at block `50,467,473`, all 27 active MissionControl assets had `specialStabPoolId = 0`; none was `1` |
| Current EndaomentPSM state | Unpaused; `canMint = true`; `canRedeem = true`. Disable both through Echo before custody disposition |

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
   Charlie, pause candidate AuctionHouse and RipeGov 7. Pause every other
   candidate write path reachable by users or registered departments. Where a
   contract's own pause does not guard that path, pause or disable every caller
   that can reach it. If a target is already paused, assert its state instead
   of submitting a no-op pause. Leave candidate CreditEngine and Lootbox
   unpaused only so `updateDebtForUser` and deposit-point accounting remain
   callable; keep Teller, AuctionHouse, HumanResources, BondRoom,
   CreditRedeem, Deleverage, claim/auto-stake routes, and every other upstream
   producer paused. Pool 6 stays unpaused so Charlie can validate the pointer
   to 6.

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

Also fresh-read active Echo's delay and census Endaoment, EndaomentFunds, PSM,
and yield custody. Predict the unique ERC-20s that will remain in old Funds
after PSM unwind and direct-balance consolidation; do not include a yield token
that the unwind burns. Require
`PriceDesk.getUsdValue(asset, fullAmount, false) > 0` for every planned transfer
asset. If Echo's delay is nonzero, pre-initiate the applicable
`setPsmCanMint(false)` and/or `setPsmCanRedeem(false)` action plus one
`performEndaomentTransfer(asset, MAX_UINT)` per predicted post-unwind Funds
asset; if it is zero, initiate/execute required actions at freeze. Execute only
actions fresh state still requires and cancel every
zero/no-change or otherwise unexecuted old-Echo action before RipeHQ 6 changes.
If work remains, pause old PSM and/or old Endaoment as applicable, then recreate
missing actions through the new zero-delay boards after the change. Finish
while old IDs 14, 21, and 22 still resolve and before any confirms. An
unpriceable asset is a stop/replan, not a sweep attempt.

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
| 14 Endaoment + 21 EndaomentFunds | Native/ERC-20 treasury custody, allowances, WETH/ETH and Curve bindings | **Before confirming either ID:** if a nonzero sweep is required and old Endaoment is paused, unpause it only inside the atomic disposition. Move direct holdings with nonempty `transferFundsToVaultInEndaoment(assets)` calls of at most 10 assets each; assert and skip empty/zero branches. Convert native ETH only when nonzero. Require decoded `PriceDesk.getUsdValue(asset, fullAmount, false) > 0`; then for every nonzero ERC-20 call `performEndaomentTransfer(asset, MAX_UINT)` and assert execution `True`. Prove old balances/allowances zero, pause old Endaoment if open (otherwise assert paused), then apply the approved candidate-Funds inventory. |
| 15 HumanResources | Pending Contributor actions and `legacyContributorRipeGovVaultId` rows | **Before confirm:** complete/cancel every pending action. **Before reopen:** replay every required legacy-vault mapping; each existing Contributor instance retains its own operational state and remains registered in Ledger. |
| 16 Lootbox | Underscore reward settings and `lastUnderscoreSend`; points/rewards themselves remain in Ledger | **At deployment:** use the fresh live settings. Planning values were enabled, interval `43,200`, deposit reward `25 RIPE`, yield reward `150 RIPE`, and `lastUnderscoreSend = 50,463,734`. **At freeze:** record enablement/last/interval and conditionally disable old distribution. **At ID-16 confirmation:** atomically force the new flag false and keep it false through replay, pointer rotation, and seeding. **At final reopen:** compute `desiredEnabled = recordedEnabled && block.number > recordedLast + recordedInterval`, conditionally set it, and assert. If recorded enabled but immature, governance may enable only after the threshold; if recorded disabled, preserve that policy until separately changed. |
| 17 Teller | Pause state and Curve child ID; no user configuration | **At deployment:** paused with Curve ID 2. **Throughout freeze:** block every `depositFromTrusted` producer because Teller pause does not block that path. |
| 18 Deleverage | Four live legacy parameters, four RH-only payoff/dust parameters, and per-user `lastDeleverageBlock` | **At deployment:** fresh-read `minDeleverageBps / deleverageBuffer / deleverageCooldown / underscoreSafeSpreadBps`; planning values were `0 / 0 / 0 / 100`. A zero cooldown means the current `lastDeleverageBlock` reset creates no waiting requirement; if the fresh cooldown is nonzero, keep Deleverage paused until the approved continuity rule passes. The existing RH-only candidate is `10^15 / 100 / 0 / 0` for full-payoff buffer, overage bps, dust threshold, and dust bps. |
| 22 EndaomentPSM | USDC/yield custody, flags, fees, caps, allowlists, yield position, interval length and counters | **Before confirm:** execute the bound Echo actions and verify `canMint == false` and `canRedeem == false`; while the old PSM remains unpaused, call `withdrawFromYieldInPsm(MAX_UINT, true, true)` or the fresh-census equivalent, then `transferUsdcToEndaomentFundsInPsm(MAX_UINT)` for any remaining USDC; verify custody, then pause the old PSM. **Before reopen:** replay all approved settings and resolve any fresh nonzero interval-counter continuity requirement. |

Execute the frozen cutover in this order:

Complete or cancel non-custody timelocked source actions, including every
pending HumanResources action, before entering this table. Do not perform the
final custody sweep until the refill paths are frozen in step 1.

| Step | Write or check | Required result |
| ---: | --- | --- |
| 1 | Safe batch: record old Lootbox enablement/last/interval and conditionally disable Underscore distribution through old Charlie; execute each required mature Echo PSM-disable action and assert both flags false; if either flag remains true, pause old PSM (or assert it already paused) and bind the post-HQ6 recovery branch. Then pause Teller, AuctionHouse, HumanResources, BondRoom, CreditRedeem, Deleverage, every claim/auto-stake route, and every other producer that can refill custody or mutate positions. Leave only CreditEngine `updateDebtForUser`, Lootbox deposit-point accounting, and approved custody helpers callable. | No user/trusted producer or Underscore distribution can mutate old state; the PSM is either disabled or paused; CreditEngine and Lootbox stay unpaused only for the two named functions |
| 2 | If PSM mint/redeem are already disabled, unwind nonzero yield and transfer nonzero USDC to old EndaomentFunds while it is unpaused, verify custody, then pause it; otherwise defer this work to step 6. If a nonzero Endaoment sweep is required and it is paused, unpause only inside this atomic disposition. Move direct holdings only with a nonempty list; convert native ETH only when nonzero; execute every mature transfer for a nonzero ERC-20. Assert and skip zero branches. If nothing is deferred, pause old Endaoment and apply the approved candidate-Funds inventory. If anything is deferred, pause old Endaoment now and fund only after step 6 closes it; if already paused, assert instead of no-op pausing. | Every completed balance/allowance readback is zero or approved; all deferred custody is held under pause; candidate funding follows the final old-custody proof |
| 3 | Read-only: wait until the Ledger action block advances, then compare source balances and position counts | State is unchanged before the first registry confirmation |
| 4 | Execute and assert `confirmAddressUpdateToRegistry(8) == True` | Active VaultBook resolves exact rows 1–7 |
| 5 | One atomic transaction: execute `confirmAddressUpdateToRegistry(5)` and then `confirmAddressUpdateToRegistry(6)` through an executor that reverts unless both return `True` | MissionControl and Switchboard both change or neither does; Alpha–Echo resolve the new MissionControl |
| 6 | Close every deferred custody item through the new zero-delay boards. For PSM recovery, one reverting atomic bundle must unpause old PSM if paused; initiate/execute the applicable `setPsmCanMint(false)` and/or `setPsmCanRedeem(false)` action; assert both flags false; unwind/transfer all custody; and re-pause it. For Endaoment recovery, conditionally unpause old Endaoment inside the bundle, execute each missing nonzero `MAX_UINT` transfer, prove zero/residual custody, and pause it if open (otherwise assert paused); then apply the approved candidate-Funds inventory. Do not confirm IDs 14, 21, or 22 until this closes. | Old PSM/Endaoment/Funds custody is closed; nothing else changed except the intended registry rows |
| 7 | Execute and assert `confirmAddressUpdateToRegistry(id) == True` for each ID 9–22. ID 16 is one reverting atomic bundle: confirm it, call new Charlie `setHasUnderscoreRewards(false)` only if candidate state is true, and assert false. | Every ID resolves its exact RH department; Lootbox distribution remains disabled throughout the remaining freeze; all ingress remains blocked |
| 8 | Execute `confirmNewAddressToRegistry(VaultMigrator)` and assert its returned ID | Exactly ID 25; VaultMigrator remains paused |
| 9 | Require `Charlie.actionTimeLock == 0`; execute all **before reopen** department settings plus approved MissionControl `userConfig`, delegation, and stale/pending-state replay not established by the transition Defaults. For a target whose setter rejects paused state, atomically unpause, set, verify, and re-pause it. Keep Lootbox distribution false; do not replay its pre-freeze flag. Keep Teller, AuctionHouse, HumanResources, BondRoom, CreditRedeem, Deleverage, claim/auto-stake routes, and every other upstream producer paused; CreditEngine and Lootbox remain unpaused only for `updateDebtForUser` and deposit-point accounting. | Every readback matches the approved configuration table; no user or trusted producer ingress is open |
| 10 | Through new Charlie call `setPreferredStabVaultId(6)`, record its action ID, then call `executePendingAction(actionId)` while the setup delay is zero | Pool 6 is unpaused and supports sGREEN; final pointer is 6 |
| 11 | Clear every zero-delay setup action, prove no production-surviving action was started at zero delay, then call `setActionTimeLockAfterSetup(approvedNonzeroDelay)` on Alpha–Echo and HumanResources | All production delays are nonzero before normal governance actions begin |
| 12 | If Pool 6 is funded, use one atomic bundle to assert all named producer pauses and Lootbox distribution false, prove CreditEngine `updateDebtForUser` and Lootbox deposit-point accounting remain callable, unpause Teller, deposit every approved seed asset with explicit `vaultId = 6`, and re-pause Teller. Otherwise prove the approved empty-pool posture. | The entire seed bundle succeeds or reverts; Pool-6 balances/capacity and auction fallback match the chosen launch posture |
| 13 | In the final reopen bundle, compute `desiredEnabled = recordedEnabled && block.number > recordedLast + recordedInterval`; conditionally set/assert the Lootbox flag, then reopen Teller and approved producers, run Pool-6 and legacy-explicit-ID canaries, and reopen AuctionHouse last. | New Stability activity uses 6, fallback works, RipeGov 2 remains active, and Lootbox matches legacy policy/cadence without becoming callable mid-freeze |

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
| Every `specialStabPoolId` | Enumerate every active asset. Require `0` or an explicitly approved `6`, never `1`. The pinned 27-asset snapshot was all `0`, so the current plan makes no special-route write; if the fresh snapshot drifts, use Bravo to set the full asset liquidation configuration before reopen. |
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
| Lootbox Underscore send | Forced false throughout the core freeze; at final reopen, `hasUnderscoreRewards = recordedEnabled && block.number > recordedLast + recordedInterval`; any later enable follows the recorded legacy policy/cadence rule |

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
| 3 | **Only if the fresh census selects registration as the approved tail treatment:** initiate each required registration and corresponding later deregistration action; list but do not execute each immediate Charlie claim-permission enable/disable write. Otherwise skip this step and record the approved raw-tail manifest. | Each selected remediation pair has an explicit open/close lifecycle; no registration occurs merely to recover immaterial raw residue |
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
| Department continuity | Approve the fresh-read Lootbox disable/re-enable threshold, any nonzero Deleverage cooldown handling, and any nonzero PSM interval-counter handling described above |
| Deleverage RH-only parameters | Approve the existing Base candidate `10^15 / 100 / 0 / 0`, or bind another qualified payoff/dust tuple |
| Endaoment treasury handoff | Exact asset/amount inventory transferred from governance to candidate EndaomentFunds after the old treasury sweep, plus any amount intentionally retained by governance |
| Stability closeout | Final reward tuple plus the exact nonclaimable/dust asset treatment. Recommended default: if the fresh census still shows exactly one raw token unit of mcbETH and the fork proves no share, value, custody, or migration effect, retain it as a named raw tail; register it only if governance approves the complete registration/claim/deregistration lifecycle. |
| Migration freeze budget | Approve a fork-measured target and hard maximum for each later migration window. Do not use a two-hour target/four-hour maximum: RipeGov requires two sequential governed maturities, and at a selected `3,600`-block delay the waiting alone is at least `7,200` blocks (approximately four hours) before execution and incident reserve. |
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
- `Ledger.badDebt() != 0` immediately before any Stability or RipeGov canary or
  migration batch;
- a `bool`, assigned ID, migrated count, or claimed USD result cannot be
  asserted before its dependent transaction;
- the freeze is incomplete or source balances continue changing;
- calldata, Safe nonce, action ID, maturity, expiry/headroom, runtime, or live configuration
  differs from the forked transaction package.

For detailed field assertions, tail cases, action records, and recovery paths,
use the [technical appendix](./production-runbook-technical-appendix.md).
