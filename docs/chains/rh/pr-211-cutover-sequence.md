# PR #211 cutover

One sequence. Do these in order.

## Contracts being redeployed

Nine registry replacements. Nothing else.

| Contract | Registry | Slot | Current address (being replaced) |
|---|---|---|---|
| SwitchboardFoxtrot | Switchboard | 6 | `0xD11B23b6391e294DF49961E64231bddDE5bB5E89` |
| SwitchboardCharlie | Switchboard | 3 | `0xc4d4E0EBC6b40FC31893449327E7080feE2CEA20` |
| MissionControl | RipeHq | 5 | `0xC154F6fCA0788947E49Ffb4AD121F03C8332EFDe` |
| Lootbox | RipeHq | 16 | `0xc9fD8dFE6a9A0dB2dE53cC56b8E3b2892F33979a` |
| SwitchboardAlpha | Switchboard | 1 | `0xc36b4E857A6430e0D848eaA3C664B855F804Cc26` |
| SwitchboardBravo | Switchboard | 2 | `0xd7F1d8BBB1f06879fBbdda695d35C5aa0117394f` |
| AuctionHouse | RipeHq | 9 | `0x8241b4E94DBd10CEe02712b8b610142c6715E760` |
| Deleverage | RipeHq | 18 | `0xF98534c300036f7ccC6996eB6D63a5C538B53B2f` |
| CreditRedeem | RipeHq | 19 | `0x26b8733836aEeb3aa3B8Acee09dBa8E231299A87` |

Also deploy (not a registry slot): `DefaultsRobinhoodLive` — constructor argument for the new MissionControl only.

**Do not replace Ledger.** Ledger stays `0x7E1d751D168f09761b88651A4c78C996354FaeB1` (RipeHq 4). Do not replace Teller, CreditEngine, HumanResources, Delta, Echo, StabVault, RipeGov, VaultBook, PriceDesk, Chainlink, or the reserve engine. Do not run `2026082600`, `2026082601`, or `2026082602` — they deploy a fresh Ledger / RipeGov / VaultBook, bind the *previous* generation (`MC 0xD335…`, `Ledger 0xF1CD5…`), and would wipe the points this plan keeps. Against today’s HQ they revert on `require_slot`; do not “fix” their hardcoded addresses and retry.

Do not deploy the `DefaultsRobinhoodLive.vy` already in the tree (block `46,988,201`, old MC `0xD335…`, 12 assets, wrong rate). Step 4 regenerates it.

Do not Bravo `addAsset`. Do not Charlie `setRewardVaultId`. Do not `Foxtrot.startReserveEngine` / `stopReserveEngine` / rate-override (RipeReserveEngine is already `isRunning=true`; `stop` resets genesis and the epoch). The one Foxtrot call this plan needs is `setCanAcquireRipe(false)` in step 1, restored in step 8. Do not `reset*Points`. After this flip, `arePointsEnabled` is inert — the only emission stop is `Alpha.setRipePerBlock(0)` → execute.

`userConfig` / `userDelegation` do not survive the MC replace and are not enumerable. Sampled borrowers / lite signers / Safe were default `(False, False, False)`. Accept the wipe. If a live delegate appears, regrant after step 7 and before step 8.

---

## Live pin (re-read at execution)

RipeHq `0xD4e82AE1De673bba3B53386A2D2C630AE6630940`  
HQ governance (Safe) `0xE488a42d33B3af5D3E5cd5680938D8369716D1bF`  
Switchboard `0xA1872467AC4fb442aeA341163A65263915ce178a`

| slot | now |
|---|---|
| HQ 4 Ledger | `0x7E1d751D168f09761b88651A4c78C996354FaeB1` — keep |
| HQ 5 MissionControl | `0xC154F6fCA0788947E49Ffb4AD121F03C8332EFDe` |
| HQ 16 Lootbox | `0xc9fD8dFE6a9A0dB2dE53cC56b8E3b2892F33979a` |
| HQ 17 Teller | `0x2d3cb2b39289f402187d7dc9b609ead6646f2506` — keep |
| HQ 15 HumanResources | `0xfe4BAbbD48D31228872A7010E792244E66A22952` — keep |
| HQ 26 RipeReserveEngine | `0xc60af65F0bF8a1456aD822e98c45769552B13190` — keep |
| HQ 27 RipeReserveVesting | `0x92ea6b99F1a0Cf95863DBf5CD83B0a09449ad396` — keep |
| SB 1 / 2 / 3 | Alpha `0xc36b4E…cC26` / Bravo `0xd7F1d8…394f` / Charlie `0xc4d4E0…CEA20` |
| SB 6 Foxtrot | `0xD11B23b6391e294DF49961E64231bddDE5bB5E89` (Aug 25 reserve-engine; **no** auction selectors) |
| Contributor template | `0x619DcD2d3a4Ef3146f0A9B132bF72A333B916E68` |

`registryChangeTimeLock = 0` and every board `actionTimeLock = 0`, so start→confirm and set→execute are same-transaction. HQ/SB `confirmAddressUpdateToRegistry` returns **`False` without reverting** if the pending update is invalid — Safe MultiSend still sees success. Every confirm in this plan goes through the step-6 helper so `false` reverts.

`current-manifest.json` MissionControl / Ledger must equal `hq.getAddr(5)` / `hq.getAddr(4)` before step 4. Today they match (`0xC154…` / `0x7E1d…`). The manifest `UniswapV2Prices` row may disagree with live PriceDesk 3; `prepare_defaults` / `verify_defaults` do not read that row.

Solidity `block.number` / Ledger clocks are **L1** (~12s). Child height is ~48.7M and is not what the clocks use.

---

## 1. Park traffic first

Leave live Lootbox **unpaused** through step 3. Live Alpha skips settle when Lootbox is paused and the new rate is 0 — that forfeits the open ripe window.

`cancelPendingAction` **reverts** when `hasPendingAction(aid)` is false (`TimeLock._cancelAction` returns false if `confirmBlock == 0`; Charlie/Alpha/Bravo/Delta assert it). Walked 2026-08-29: Charlie `actionId=1` and Delta `actionId=1` have nothing pending; Alpha 9 / Bravo 10 / Foxtrot 5 are historical and cleared. Cancel only aids that read `hasPendingAction(aid) == true` at execution. Blind-cancelling `aid=1` aborts the park transaction.

```
# current boards — only if board.hasPendingAction(aid) == true
Charlie.cancelPendingAction(aid)
Foxtrot.cancelPendingAction(aid)
Bravo.cancelPendingAction(aid)
Alpha.cancelPendingAction(aid)
Delta.cancelPendingAction(aid)

# current Charlie — Teller is unpaused
Charlie.pause(teller, true)

# current Foxtrot — permissionless acquire is live
Foxtrot.setCanAcquireRipe(false)

# current Charlie — vesting is unpaused; claims still auto-deposit without this
Charlie.pause(ripeReserveVesting, true)
```

Read back before step 2:

- `Teller.isPaused() == true`
- `RipeReserveEngine.canAcquireRipe() == false`
- `RipeReserveEngine.isRunning() == true` (do not stop it)
- `RipeReserveVesting.isPaused() == true`
- `Lootbox.isPaused() == false`

**What Teller pause actually stops.** `Teller.deposit` / `depositMany` / `withdraw*` / `purchaseRipeBond` / `claimLoot` / `deleverage*` assert `deptBasics.isPaused`. BondRoom is Teller-only, so bonds stop.

**What Teller pause does not stop.** `Teller.depositFromTrusted` and `_deposit` have **no** pause gate. Nine protocol callers reach it. The ones that matter here:

| path | parked by | walked 2026-08-29 |
|---|---|---|
| RipeReserveEngine.acquireRipe → auto-deposit | `setCanAcquireRipe(false)` | `isRunning=true`, `canAcquireRipe=true`, vesting unpaused, `previewAcquireRipe` `available=true` |
| RipeReserveEngine.claimVestedRipe(_autoDeposit=true) | pause vesting (`_isMintReady` fail-closes) | vesting unpaused; `setCanAcquireRipe` / `isRunning` are **not** checked on claim |
| Charlie.claimLootForUser → Lootbox auto-stake | Lootbox pause (after step 3 only) | Lootbox unpaused; this path does not go through Teller |
| HumanResources.cashRipeCheck | HR’s own pause | `Ledger.numContributors == 0`; re-read. Do not pause HR unless a contributor appears |
| BondRoom.purchaseRipeBond | Teller pause | Teller-gated |

Do not treat the engine as halted because the Teller is paused. Do not `stopReserveEngine` — that zeros `genesisBlock` and resets the epoch. `setCanAcquireRipe(false)` is the acquire off-switch; vesting pause is the claim off-switch.

Pause Teller and close RE acquire/claim **before** the rate goes to 0 so those paths cannot stamp `assetDepositPoints[2][RIPE]` against a frozen `ripeRewards` bucket.

After step 4, do **not** Bravo-write on the live MC. Live Bravo still talks to the old MC and would desync the snapshot. “HEAD Bravo reverts on the old MC” is the wrong window — HEAD Bravo is not live yet.

---

## 2. Stamp Ledger (current Charlie)

Lootbox still unpaused. Current Charlie:

```
Charlie.updateRipeRewards()
```

Then one call per row whose `Ledger.assetDepositPoints[vaultId][asset].lastUpdate != 0`. Re-read that field **now**. The table below was exact on 2026-08-28/29; a first NVDA/TSLA/GOOGL deposit (UniswapV2Prices moved 08-28 23:39Z) would add a row. Checkpoint every nonzero row. Skip GREEN (no vault). No borrow-points call.

```
Charlie.checkpointAssetDepositPointsAt(asset, vaultId, vaultAddr)
```

`vaultAddr` = `VaultBook.getAddr(vaultId)`.

`Lootbox._getUsdValueForAmount` calls `PriceDesk.getUsdValue(asset, amount)` with `_shouldRaise=False`. A stale/missing price writes `lastUsdValue = 0` and does not revert. `genDepositorsAlloc = 0` so nothing pays on gen; still re-read `lastUsdValue` after each checkpoint and do not treat a silent 0 as “verified.”

| asset | vaultId | vaultAddr | last walked |
|---|---|---|---|
| WETH `0x0Bd7D308f8E1639FAb988df18A8011f41EAcAD73` | 3 | SimpleErc20 `0x4F89C94636995eF20d40d5592bA2585348bE6D53` | checkpoint |
| SPCX `0x4a0E65A3EcceC6dBe60AE065F2e7bb85Fae35eEa` | 3 | same | checkpoint |
| AAPL `0xaF3D76f1834A1d425780943C99Ea8A608f8a93f9` | 3 | same | checkpoint |
| GME `0x1b0E319c6A659F002271B69dB8A7df2F911c153E` | 3 | same | checkpoint (balance may be 0) |
| RIPE `0x4D3f37a965b21aB4122e92Dd41D2693E742c883b` | 2 | RipeGov `0xFa767a19c0C2B80D5A8d5b88be67de153Df1b2f2` | checkpoint |
| UNI-V2 `0xba6F6CBa1a4104000847d4fdccB676E99166CEcE` | 2 | same | checkpoint (`canDeposit=false`; still has points) |
| UNI-V2 `0x9b8537bE0FD5cf9B2AD495C5A85130D5bAe4769D` | 2 | same | checkpoint (stakers 2500) |
| sGREEN `0x290a52380A88f743813B8C3e9F6B0e61DB5FDF73` | 1 | StabilityPool `0xe238b50d79D566aa59A2deF4362a698eDC3dC395` | checkpoint |
| GREEN/USDG `0x2fD13b49F970e8C6D89283056C1c6281214b7EB6` | 1 | same | checkpoint (stakers 4500) |
| NVDA / TSLA / GOOGL | 3 | SimpleErc20 | skip only if `lastUpdate == 0` |
| GREEN `0x355bB7F0f6c730e4460d620420a300fa08FF82F3` | — | — | skip (no vault, 0/0 allocs) |

---

## 3. Stop the emission rate (current Alpha)

```
Alpha.setRipePerBlock(0)
Alpha.executePendingAction(aid)
```

Live `actionTimeLock = 0` — initiate and execute are the same transaction. The comment “after the Alpha timelock” is a no-op wait today.

This settles the open window at the **live** rate (`41666666666666666`), then writes 0. Lootbox must still be unpaused.

Read back:

- `rewardsConfig.ripePerBlock == 0`
- `Ledger.ripeRewards.lastUpdate` equals this L1 block

Do **not** require every asset row’s `lastUpdate` to equal this block. Alpha only stamps `ripeRewards.lastUpdate`. Asset rows were stamped in step 2.

Record the live rate you just replaced. Step 8 restores **that** number, not launch `0.009e18`. Walked 2026-08-28/29:

```
ripePerBlock = 41666666666666666    # 0.041666…e18, set 2026-08-28 18:17Z
```

After this read-back, close Charlie-direct loot claims (they bypass Teller pause and auto-stake through `depositFromTrusted`):

```
Charlie.pause(lootbox, true)
```

Do not pause Lootbox before this point. After the step-6 flip the **new** Lootbox starts unpaused — pause that one the same way until step 8.

---

## 4. Snapshot MissionControl into DefaultsRobinhoodLive

After step 3 is on a **finalized** child block.

`prepare_defaults.py` reads MC/Ledger from `migration_history/robinhood-mainnet/v1/current-manifest.json`, not from `hq.getAddr`. Before generate:

```
manifest.MissionControl.address == hq.getAddr(5) == 0xC154F6…2EFDe
manifest.Ledger.address         == hq.getAddr(4) == 0x7E1d75…aeB1
```

**Archive RPC.** Public `https://rpc.mainnet.chain.robinhood.com` prunes state ~6.2k child blocks back while `finalized` lags ~9–11k, so `prepare_defaults` fail-closes (`could not read MissionControl code at snapshot block`). There is no finalized-and-still-served block on that endpoint. Set `ROBINHOOD_MAINNET_RPC_URL` to an archive endpoint. Prove `eth_getCode(0xC154F6…, snapshotBlock)` returns bytecode **before** generate. The snapshot block must be `≤ finalized` **and** still served.

```
python scripts/prepare_defaults.py \
  --network robinhood-mainnet \
  --block-number <FINALIZED_AND_STILL_SERVED_BLOCK> \
  --dry-run
```

Coverage: `assetConfigs` = 13. Inventory printed allocs. They must reconstruct

```
RIPE 1000 + sGREEN 1000 + GREEN/USDG 4500 + UNI-V2 0x9b85… 2500 = 9000
```

(or whatever is live at the snapshot block — use the printed inventory, not `30_00`). Then write and verify:

```
python scripts/prepare_defaults.py \
  --network robinhood-mainnet \
  --block-number <FINALIZED_AND_STILL_SERVED_BLOCK>

python scripts/verify_defaults.py --network robinhood-mainnet
```

Review the `DefaultsRobinhoodLive.vy` diff. Header must show this MC `0xC154…`, this Ledger `0x7E1d…`, 13 assets, `ripePerBlock == 0`.

Constructor will copy every live `assetConfig` and set `rewardVaultId = vaultIds[0]` when `len == 1`. GREEN has `vaultIds=[]` and 0/0 allocs — constructor will not revert. `verify_defaults` does **not** compare `rewardVaultId`; step 7 does.

`verify_defaults` deploys Defaults with the **live** Contributor. Deploy Defaults the same way (step 5).

Do not Bravo-configure the live MC after this snapshot. A Safe-only `setAssetConfig` on the old MC would desync the new MC.

---

## 5. Deploy (do not flip pointers yet)

`_tempGov` on Alpha / Bravo / Charlie / Foxtrot **must not** equal HQ governance (`0xE488…`). LocalGov reverts if it does. `_tempGov` is the deployer EOA. After deploy, that EOA can still `setRipePerBlock`, `pause`, `recoverFunds`, `setRewardVaultId`, and Foxtrot reserve setters **until** `relinquishGov`.

Prefer **EOA deploy → EOA `relinquishGov` → Safe flip**. A helper-as-`_tempGov` in the same Safe batch also works, but that helper holds full board gov until it relinquishes. Strictly more surface. Do not make the Safe `_tempGov`.

Copy live values. Re-read Deleverage and Lootbox immediately before deploy; the numbers below were live 2026-08-28/29.

```
DefaultsRobinhoodLive(0x619DcD2d3a4Ef3146f0A9B132bF72A333B916E68)

MissionControl(RipeHq, DefaultsRobinhoodLive)

Lootbox(RipeHq, 1, 0, 0, 0)

AuctionHouse(RipeHq)
CreditRedeem(RipeHq)
Deleverage(
  RipeHq,
  0,                # minDeleverageBps
  0,                # deleverageBuffer
  0,                # deleverageCooldown
  100,              # underscoreSafeSpreadBps
  1000000000000000, # deleverageFullPayoffBuffer (1e15)
  100,              # deleverageOverageBps
  0,                # deleverageDustThreshold
  0                 # deleverageDustBps
)

# boards: timeLock.__init__(min, max, 0, max) → actionTimeLock starts at 0
# SWITCHBOARD_MIN/MAX = 600 / 50400 (config/robinhood_launch.py)
Alpha(RipeHq, deployerEOA, 300, 604800, 600, 50400, 0)
Bravo(RipeHq, deployerEOA, 600, 50400)
Charlie(RipeHq, deployerEOA, 600, 50400)
Foxtrot(RipeHq, deployerEOA, 600, 50400)
```

Then, from the deployer EOA, on each new board:

```
Alpha.relinquishGov()
Bravo.relinquishGov()
Charlie.relinquishGov()
Foxtrot.relinquishGov()
```

Read back `governance() == 0x0` on all four. After this, only the Safe can govern them.

Also deploy the confirm helper (not a registry slot; abandon after the flip):

```
# ConfirmRegistryUpdate.vy — compile with the repo Vyper, deploy once
interface Registry:
    def confirmAddressUpdateToRegistry(_regId: uint256) -> bool: nonpayable

@external
def confirm(_registry: address, _regId: uint256):
    assert extcall Registry(_registry).confirmAddressUpdateToRegistry(_regId)
```

Do not flip yet. EIP-170: AuctionHouse 24,564 (12 B free), Deleverage 24,559 (17 B). Remeasure if those two sources moved after `42fec6da`. Bravo / Charlie / MC / Lootbox moved in #222; they are not the tight pair.

---

## 6. Flip pointers

The **flip itself** (this step) can be one Safe transaction: every registry timelock is 0, every new board `actionTimeLock` is 0, so start+confirm and `setRipePerBlock`+execute are same-block. Deploy + relinquish + flip + step-8 restart can also be that same transaction once the bytecode exists.

The **whole plan cannot**. Step 4 is off-chain (`prepare_defaults` + compile) and must run after step 3 is on a finalized, still-served block. Park / stamp / zero stay in an earlier transaction so the snapshot sees `ripePerBlock == 0`.

Safe MultiSend does not check return data. Call `Helper.confirm(registry, id)` — never `registry.confirmAddressUpdateToRegistry` from the Safe directly. With `registryChangeTimeLock = 0`, start+helper-confirm in the same tx is valid for a fresh contract (`_isValidNewAddress`: is contract and `addrToRegId == 0`). The `false` branch is then near-unreachable; keep the helper anyway.

Same-tx start+confirm+`newCharlie.updateRipeRewards()` (new Charlie is already SB 3; new MC should have `ripePerBlock == 0`):

```
# auctions: live Charlie has start/pause; live Foxtrot does not; HEAD is the reverse.
# Confirming Charlie first clears its addrToRegId. New Charlie + old Foxtrot
# ⇒ AuctionHouse has no registered board that can start/pause.

Switchboard.startAddressUpdateToRegistry(6, newFoxtrot)
Helper.confirm(Switchboard, 6)
Switchboard.startAddressUpdateToRegistry(3, newCharlie)
Helper.confirm(Switchboard, 3)

# Bravo calls rewardVaultId — live MC does not have that selector.
# Flip MC before Bravo.
RipeHq.startAddressUpdateToRegistry(5, newMissionControl)
Helper.confirm(RipeHq, 5)
RipeHq.startAddressUpdateToRegistry(16, newLootbox)
Helper.confirm(RipeHq, 16)
newCharlie.updateRipeRewards()
newCharlie.pause(newLootbox, true)

Switchboard.startAddressUpdateToRegistry(1, newAlpha)
Helper.confirm(Switchboard, 1)
Switchboard.startAddressUpdateToRegistry(2, newBravo)
Helper.confirm(Switchboard, 2)

RipeHq.startAddressUpdateToRegistry(9, newAuctionHouse)
Helper.confirm(RipeHq, 9)
RipeHq.startAddressUpdateToRegistry(18, newDeleverage)
Helper.confirm(RipeHq, 18)
RipeHq.startAddressUpdateToRegistry(19, newCreditRedeem)
Helper.confirm(RipeHq, 19)
```

AH / Deleverage / CreditRedeem are settlement-math only — they do not ABI-brick if left mixed with the new MC. Still flip them in this session so the 100% LTV / overshoot patch is live.

Fatal other orders: Charlie confirm without Foxtrot confirm; Bravo confirm before MC confirm; MC flip with launch Defaults or the checked-in Live file.

---

## 7. Read back

```
hq.getAddr(4)                        still 0x7E1d75…          (Ledger untouched)
hq.getAddr(5 / 9 / 16 / 18 / 19)     new MC / AH / Lootbox / DL / CR
switchboard.getAddr(1 / 2 / 3 / 6)   new Alpha / Bravo / Charlie / Foxtrot
board.governance()                   0x0 on Alpha / Bravo / Charlie / Foxtrot
isSupportedAsset                     all 13 live assets (not the 12-asset checked-in file)
rewardsConfig.genDepositorsAlloc     0
rewardsConfig.ripePerBlock           0
totalPointsAllocs.stakers            9000     # not 30_00
totalPointsAllocs.voters             0
RipeReserveEngine.canAcquireRipe     false
RipeReserveEngine.isRunning          true
RipeReserveVesting.isPaused          true
new Lootbox.isPaused                 true
```

`rewardVaultId` (constructor-seeded; `verify_defaults` does not check this):

| asset | earner |
|---|---|
| WETH, SPCX, NVDA, TSLA, AAPL, GOOGL, GME | 3 |
| RIPE, UNI-V2 `0xba6F…`, UNI-V2 `0x9b85…` | 2 |
| sGREEN, GREEN/USDG | 1 |
| GREEN | 0 |

If `totalPointsAllocs.stakers` is 9000 and you expected 3000, the MC is correct. Do not Bravo-zero extras.

---

## 8. Turn the clock back on

Restore the rate recorded in step 3, then reopen the parked paths. Walked live rate:

```
new Alpha.setRipePerBlock(41666666666666666)
new Alpha.executePendingAction(aid)
new Charlie.pause(teller, false)
new Charlie.pause(newLootbox, false)
new Charlie.pause(ripeReserveVesting, false)
new Foxtrot.setCanAcquireRipe(true)
```

Not `0.009e18` (launch Defaults). Not `0.0009e18` (checked-in Live file). HEAD Alpha settles at the old rate (0) then writes — no gap mint if step 3 held.

Teller unpause is `Charlie.pause(teller, false)` (gov-only). Not a direct Teller call. Same for Lootbox and vesting. `setCanAcquireRipe(true)` is Foxtrot gov-only.

To stop again: `Alpha.setRipePerBlock(0)` → execute. Pause Lootbox does **not** stop clocks after this flip.
