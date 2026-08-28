# PR #211 activation — do this now

One sequence for a **new** RH HQ of this generation. Start at 1, finish at the end.
If an HQ already exists with balances or reward state, stop. Do not use this list
(replacing a live Ledger/MC/vault wipes that state; this PR does not copy it).

Do not call any Foxtrot reserve-engine function (`startReserveEngine`,
`setCanAcquireRipe`, `setReserveEngine*`). Leave that blocked.

---

## IDs

**RipeHq:** 4 Ledger · 5 MissionControl · 6 Switchboard · 7 PriceDesk · 8 VaultBook · 9 AuctionHouse · 13 CreditEngine · 15 HumanResources · 16 Lootbox · 17 Teller · 18 Deleverage · 19 CreditRedeem

**Switchboard:** 1 Alpha · 2 Bravo · 3 Charlie · 4 Delta · 5 Echo · **6 Foxtrot (you must add this; `0002` does not)**

**VaultBook:** 1 StabilityPool (sGREEN earner) · 2 RipeGov (RIPE earner) · 3 SimpleErc20 (WETH earner)

GREEN has no vault and no earner.

---

## 1. Tokens, HQ, Defaults

`0000_TokensAndHq.py`

GREEN, RIPE, sGREEN, RipeHq, Contributor blueprint, TrainingWheels, DefaultsRobinhood.

---

## 2. Ledger, then MissionControl

`0001_Registries.py`

1. Deploy Ledger with Defaults → HQ **4**.
2. Deploy MissionControl with Defaults → HQ **5**.
3. Read immediately (constructor already wrote these):

```
rewardVaultId(WETH)   == 3
rewardVaultId(RIPE)   == 2
rewardVaultId(sGREEN) == 1
rewardVaultId(GREEN)  == 0

assetConfig(WETH).stakersPointsAlloc   == 0
assetConfig(RIPE).stakersPointsAlloc   == 15_00
assetConfig(sGREEN).stakersPointsAlloc == 15_00

rewardsConfig():
  ripePerBlock            == 0.009e18
  borrowersAlloc          == 10_00
  stakersAlloc            == 90_00
  votersAlloc             == 0
  genDepositorsAlloc      == 0
  stabPoolRipePerDollarClaimed == 1e18
```

If any earner is wrong, do not continue. Do not Bravo-set allocs and do not
Charlie-set earners for these four — constructor already did it.

`ripePerBlock` is already **0.009**. The first `updateRipeRewards` (Teller
housekeep, Alpha rate write, etc.) starts the clock. Teller is still paused
later, so you have a window. Do not unpause Teller until step 10.

If you need the clock at 0 until the rest of this list is done: Alpha
`setRipePerBlock(0)` → execute **now**, before PriceDesk/Teller/Lootbox exist
enough to settle. Then turn 0.009 back on in step 10.

---

## 3. Switchboards, including Foxtrot

`0002_Switchboards.py` deploys Alpha–Echo as 1–5, then puts Switchboard on HQ 6.

**Before any auction can run, add Foxtrot:**

1. Deploy SwitchboardFoxtrot (same timelock args as Charlie).
2. `switchboard.startAddNewAddressToRegistry(foxtrot, "SwitchboardFoxtrot")`
3. `switchboard.confirmNewAddressToRegistry(foxtrot)` must return **6**.
4. `switchboard.getAddr(6) == foxtrot`

Charlie does **not** have `startAuction` / `pauseAuction`. Those are Foxtrot only.

---

## 4. PriceDesk and sources

`0003_PriceSources.py` → PriceDesk HQ **7**. Chainlink is PriceDesk id 1.

---

## 5. Vaults — this order, these ids

`0004_Vaults.py`

1. VaultBook → then HQ **8**.
2. StabilityPool → VaultBook **1**
3. RipeGov → VaultBook **2**
4. SimpleErc20 → VaultBook **3**

Confirm:

```
missionControl.coreRipeGovVaultId() == 2
missionControl.isStabVaultId(1) == true
vaultBook.getAddr(1/2/3) match those three contracts
```

Do not register vaults in any other order. Earners already point at 1/2/3.

---

## 6. Departments

`0005_Departments.py` — keep this order, these HQ ids:

9 AuctionHouse · 10 AuctionHouseNFT · 11 Boardroom · 12 BondRoom · 13 CreditEngine · 14 Endaoment · 15 HumanResources · 16 Lootbox · 17 Teller (**starts paused**) · 18 Deleverage · 19 CreditRedeem · 20 TellerUtils · 21 EndaomentFunds · 22 EndaomentPSM (mint/redeem off)

AuctionHouse and Deleverage both go in on this step. Do not ship one without the other.

---

## 7. Curve pool / leftover migrations

`0006_CurvePool.py`, `0008_UniswapV2Prices.py` if those are in this packet.
Do not run `0009` / `0010` Ledger or vault replacements.

---

## 8. Timelocks and Safe

`0007_FinishSetup.py`

Include **Foxtrot** in `setActionTimeLockAfterSetup` if Alpha–Echo get one.
Then `hq.finishRipeHqSetup(GOVERNANCE)`.

After this, every Alpha/Bravo/Charlie/Foxtrot write is a timelock + execute.

---

## 9. Readback before anything is live

```
HQ 5  == this MissionControl
HQ 9  == this AuctionHouse
HQ 16 == this Lootbox
HQ 17 == this Teller (paused)
HQ 18 == this Deleverage
HQ 19 == this CreditRedeem

Switchboard 3 == this Charlie
Switchboard 6 == this Foxtrot

rewardVaultId WETH/RIPE/sGREEN == 3/2/1
totalPointsAllocs.stakers == 30_00   # 15 RIPE + 15 sGREEN
rewardsConfig.genDepositorsAlloc == 0
rewardsConfig.ripePerBlock == 0.009e18   # or 0 if you zeroed in step 2
```

If `genDepositorsAlloc` is ever nonzero, WETH (earner, 0/0) starts earning gen.
Leave it 0.

---

## 10. Turn the protocol on

Only after step 9 matches.

1. If you zeroed the rate in step 2: Alpha `setRipePerBlock(0.009e18)` → execute.
   That settles the last interval (0), then writes 0.009.
2. Unpause Teller.
3. First deposit or borrow starts deposit/borrow clocks. First `updateRipeRewards`
   after a nonzero rate starts RIPE emission. That is intended.

Do **not** raise `genDepositorsAlloc`. Do **not** Bravo-change WETH/RIPE/sGREEN
allocs or Charlie-repoint their earners in this activation. Defaults is the
intended live policy.

---

## If you must change policy in this same session

Do it **after step 9, before step 10** (Teller still paused).

**Add another asset**

1. Bravo `addAsset(..., canDeposit=False, stakers=0, voter=0)` → execute.
2. Charlie `setRewardVaultId(asset, vaultId)` → execute (`vaultId` already in `vaultIds`).
3. Enable `canDeposit`.
4. Bravo set allocs only if needed. Nonzero stakers require earner 1 or 2.

**Rotate an earner**

1. Charlie `setRewardVaultId(asset, 0)` → execute (zeros that asset’s allocs too).
2. Move balances / Bravo `vaultIds` if needed.
3. Charlie `setRewardVaultId(asset, newVault)` → execute.
4. Bravo set allocs.

**Retire an asset**

1. Migrate balances first if you need VaultMigrator.
2. Charlie `setRewardVaultId(asset, 0)` → execute.
3. Charlie `deregisterAsset` → execute.
   Any leftover positive-LTV balance (including 1 wei) blocks **all** new borrow
   on that account. Positive-LTV NFTs cannot be retired.

**Stop emissions**

Alpha `setRipePerBlock(0)` → execute. Pause Lootbox only stops claims, not clocks.

---

## Stop if

- Ledger / MissionControl / vault 1–3 would be “replaced” on an HQ that already ran.
- Foxtrot is missing from Switchboard 6.
- AuctionHouse is live and Deleverage is not (or the reverse).
- Any Defaults earner is 0.
- `genDepositorsAlloc != 0` and you did not mean to pay WETH gen.
- Someone is about to call Foxtrot reserve-engine setters.
