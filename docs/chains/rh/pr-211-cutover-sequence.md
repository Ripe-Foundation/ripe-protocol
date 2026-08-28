# PR #211 cutover sequence

How to deploy this generation without breaking reward clocks, earners, or auctions.
Two situations: **first RH HQ** vs **replacing live contracts**. Do not mix the checklists.

`Ledger.vy` does not change. Never replace a Ledger that already has points / `lastTouch`.

---

## IDs (RH)

**RipeHq**

| ID | Contract |
|---:|---|
| 4 | Ledger — do not replace if it has state |
| 5 | MissionControl |
| 6 | Switchboard (the board registry) |
| 7 | PriceDesk |
| 8 | VaultBook |
| 9 | AuctionHouse |
| 13 | CreditEngine |
| 15 | HumanResources |
| 16 | Lootbox |
| 17 | Teller |
| 18 | Deleverage |
| 19 | CreditRedeem |

**Switchboard registry**

| ID | Board |
|---:|---|
| 1 | Alpha |
| 2 | Bravo |
| 3 | Charlie |
| 4 | Delta |
| 5 | Echo |
| 6 | Foxtrot — **required**. Existing `0002_Switchboards.py` does not add it. |

**VaultBook**

| ID | Vault | Defaults earner for |
|---:|---|---|
| 1 | StabilityPool | sGREEN (15% stakers) |
| 2 | RipeGov | RIPE (15% stakers) |
| 3 | SimpleErc20 | WETH (0/0 allocs) |

GREEN has no vault and no earner.

---

## What must move together

These selector / ActionType pairs brick if mixed:

1. **Lootbox + MissionControl** — `getDepositPointsConfig(asset, vaultId)`, earners, retirement views.
2. **AuctionHouse + Deleverage** — shared withdraw wrapper. Flip HQ 9 and 18 in the same window.
3. **AuctionHouse + CreditRedeem + MissionControl** — effective auction/redeem configs.
4. **CreditEngine + MissionControl** — `indexOfAsset` / retired-collateral borrow halt.
5. **Charlie + Foxtrot** — auctions left Charlie. New Charlie cannot pause auctions. Foxtrot must be Switchboard id 6 or AuctionHouse rejects it.
6. **Alpha + Lootbox** — Alpha always settles the open RIPE interval before `setRipePerBlock` / alloc writes.

StabVault / RipeGov / SimpleErc20 are VaultBook rows. Replacing them at the same id is a **new empty vault**. Do not do that if anyone has a balance.

---

## A. First RH HQ (nothing live)

Existing migrations `0000`–`0007` plus Foxtrot.

### Deploy / register order

1. Tokens + RipeHq + Defaults (`0000`).
2. Ledger (HQ 4), then MissionControl with Defaults (HQ 5). Constructor copies Defaults and seeds `rewardVaultId`:
   - WETH → 3
   - RIPE → 2
   - sGREEN → 1
3. Switchboard registry, then Alpha…Echo as ids 1–5 (`0002`).
4. **Foxtrot** — deploy, `Switchboard.startAddNewAddressToRegistry(foxtrot, "SwitchboardFoxtrot")`, confirm = **6**. Do this before any auction can run.
5. Switchboard itself → HQ 6.
6. PriceDesk → HQ 7. Chainlink = PriceDesk 1.
7. VaultBook → HQ 8. Vaults in order: StabilityPool=1, RipeGov=2, SimpleErc20=3 (`0004`). Confirm MC `coreRipeGovVaultId()==2` and `isStabVaultId(1)`.
8. Departments (`0005`): AuctionHouse=9, … CreditEngine=13, HR=15, Lootbox=16, Teller=17 (starts paused), Deleverage=18, CreditRedeem=19.
9. Finish timelocks / Safe handoff (`0007`). Add Foxtrot to the action-timelock-after-setup list if the other boards get one.

Do not call any Foxtrot `setReserveEngine*` / `startReserveEngine` / `setCanAcquireRipe`. That surface is a separate, still-blocked activation.

### Rewards — keep the clock off until you mean it

Defaults already store `ripePerBlock = 0.009`, 10% borrowers / 90% stakers, **gen = 0**, **voters = 0**.

First successful `updateRipeRewards` (Teller housekeep, Alpha rate write, etc.) sets `lastUpdate` and pays **zero** for that call, then the clock is live at the current rate.

**If you do not want emissions yet:**

1. Read `missionControl.rewardsConfig()` and every `rewardVaultId` (WETH=3, RIPE=2, sGREEN=1).
2. Alpha `setRipePerBlock(0)` → execute **before** any Teller/Lootbox/department settle.
3. Optionally Alpha-set Stability `stabPoolRipePerDollarClaimed` to 0 the same way.
4. Leave Teller paused until deposits should work.

**When you want emissions:**

1. Confirm earners still match the table above.
2. Confirm `genDepositorsAlloc == 0` unless you intend WETH (earner, 0/0 allocs) to start earning gen.
3. Alpha `setRipePerBlock(0.009e18)` → execute. That call settles the last interval (zero if you already zeroed), then writes the new rate.
4. Unpause Teller.
5. First user deposit/borrow starts deposit/borrow clocks. That is intended.

Do not raise `genDepositorsAlloc` until every asset that should earn gen has a Charlie/constructor earner. WETH already does. A later Bravo-listed asset does **not**.

---

## B. Replacing contracts on a live HQ

Do this only if the live HQ is already this generation’s shape, or you accept that a **new MissionControl is empty** except Defaults constructor seed.

### Never

- Replace Ledger.
- HQ-swap MissionControl if Bravo/Charlie have written anything Defaults did not. There is no copy/carry. Post-swap assets have no earner until you write them again; the next clock uses the new (empty or Defaults-only) policy for the whole unpaid window.
- Replace VaultBook ids 1/2/3 if they hold balances.
- Promote new Charlie without Foxtrot in Switchboard id 6.
- Flip AuctionHouse without Deleverage (or the reverse).

### Stop the clock first

1. Alpha `setRipePerBlock(0)` → execute. This **settles** the last live interval, then writes 0.
2. Set Stability claim rate to 0 if it is nonzero.
3. Confirm Lootbox `ripePerBlock` path is 0 (next `updateRipeRewards` pays 0).
4. Pause Teller if you want no new deposits during the flip.
5. Cancel or let expire **every** pending Charlie action (new Charlie is empty storage; in-flight auction actions on old Charlie die).
6. Same for Foxtrot if it already exists.

### Flip order (after new contracts are deployed and verified)

Keep the old addresses as rollback until the group is live.

1. **Foxtrot** — add as Switchboard 6, or address-update 6 if it exists.
2. **Charlie** — address-update Switchboard 3. Do 1 and 2 in the same window. In between, nothing can `pauseAuction`.
3. **MissionControl** — only if you are allowed to wipe live MC. HQ 5. Immediately write every `rewardVaultId` and Bravo alloc you still need (see day-2). If you cannot reconstruct them, do not flip MC.
4. **Lootbox** — HQ 16. Same generation as the MC you just pointed at. First settle after this is at the current (should be 0) rate.
5. **Alpha / Bravo / Delta** — Switchboard 1 / 2 / 4. Bravo after MC so alloc writes hit the live MC.
6. **AuctionHouse + Deleverage** — HQ 9 and 18 together.
7. **CreditRedeem** — HQ 19 (after MC).
8. **CreditEngine** — HQ 13 (after MC).
9. **Teller** — HQ 17. Unpause only when the stack above is live.
10. **HumanResources, ChainlinkPrices, Contributor** — no reward-pointer coupling; can follow.

Then:

11. Re-read every `rewardVaultId`, both stored allocs, `totalPointsAllocs`, and `rewardsConfig`.
12. If those match what you intended, Alpha `setRipePerBlock(...)` → execute to resume. That settles the zero-rate tail, then starts the new rate.

---

## Day-2 writes (live HQ, this generation)

All Charlie/Bravo/Alpha items are timelocked. Execute in the order below. Charlie-clear zeros that asset’s allocs and totals in the same write.

### Rotate an earner

1. Charlie `setRewardVaultId(asset, 0)` → execute. Checkpoints, clears earner, zeros that asset’s staker/voter allocs + totals.
2. Move balances / Bravo-change `vaultIds` if needed. New vault must already be in `vaultIds` before step 3. Do not drop the live earner from `vaultIds` before step 1.
3. Charlie `setRewardVaultId(asset, newVault)` → execute. If stored stakers will be nonzero, `newVault` must be RipeGov (2) or a stab vault (1).
4. Bravo `setAssetDepositParams` to set allocs, or leave 0/0 for gen-only.

Do **not** Bravo-raise stakers onto a plain vault. It reverts.

### List a new asset

1. Bravo `addAsset(..., canDeposit=False, stakers=0, voter=0)`.
2. Charlie `setRewardVaultId(asset, vaultId)` → execute. Vault must already be in `vaultIds`.
3. Charlie/Bravo enable `canDeposit`.
4. Bravo set allocs if needed.

If you list with `canDeposit=True` and skip step 2, users can deposit and earn nothing. If you later turn **gen** on, that asset still pays 0 until an earner exists.

### Change staker / voter allocs only

Bravo `setAssetDepositParams` (keep the same `vaultIds`). Earner must already be set. Nonzero stakers require earner 1 or 2.

On a staker `0 ↔ nonzero` crossing, MultiSend Charlie-pre checkpoint → Bravo execute → Charlie-post for every initialized historical row. Same block is not enough if something else hits Lootbox between the txs.

### Retire an asset

1. If anyone still needs VaultMigrator, migrate **before** retire. After retire, sweeps skip and explicit migrate reverts. Users can still withdraw.
2. Repair exit flags first: `canWithdraw`, and if LTV > 0 then `canBuyInAuction` plus (`canRedeemCollateral` or Endaoment). Stab-swap does **not** count. Positive-LTV NFTs cannot be retired.
3. Charlie `setRewardVaultId(asset, 0)` → execute.
4. Confirm `rewardVaultId == 0`, both allocs 0, `hasPointsAlloc == false`.
5. Charlie `deregisterAsset` → execute. Execute requires the MC captured at initiate to still be HQ-current.

Any remaining positive-LTV balance (including 1 wei) sets `highestLtv = 10001` and **blocks all new borrow** on that account until they exit that position. Zero-LTV leftovers do not.

### Turn gen on / off

- On: every asset that should receive gen needs an earner and `stakersPointsAlloc == 0`. WETH already will. Then Alpha `setRipeRewardsAllocs` with nonzero `genDepositorsAlloc`.
- Off: Alpha set `genDepositorsAlloc = 0`. Zeroing **stakers** on an asset that still has an earner **starts gen** if the global gen bucket is nonzero.

### Emergency stop (emissions)

1. Alpha `setRipePerBlock(0)` → execute (pays the last window, then stops).
2. Zero the Stability RIPE-per-dollar rate if needed.
3. Pause Lootbox if you need to stop **claims / Underscore** only. Clocks keep running.

`arePointsEnabled` does nothing. There is no `setRewardsPointsEnabled`.

---

## Quick “did we brick rewards?” checks

After any flip or reward write:

```
missionControl.rewardVaultId(WETH) == 3
missionControl.rewardVaultId(RIPE) == 2
missionControl.rewardVaultId(sGREEN) == 1
missionControl.assetConfig(RIPE).stakersPointsAlloc
missionControl.assetConfig(sGREEN).stakersPointsAlloc
missionControl.totalPointsAllocs()
missionControl.rewardsConfig()          # ripePerBlock, gen, stakers/voters/borrowers
switchboard.getAddr(6) == foxtrot
auctionHouse can be paused via Foxtrot, not Charlie
```

If `rewardVaultId` is 0 on an asset that still has deposits, that asset pays no staker / voter / gen until Charlie sets an earner. Historical `balancePoints` remain and will start earning under the **new** earner on the next clock.
