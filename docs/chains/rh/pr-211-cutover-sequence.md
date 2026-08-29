# PR #211 cutover

One sequence. Do these in order.

Replace only: Foxtrot (SB 6), Charlie (SB 3), MissionControl (HQ 5), Lootbox (HQ 16), Alpha (SB 1), Bravo (SB 2), AuctionHouse (HQ 9), Deleverage (HQ 18), CreditRedeem (HQ 19).

**Do not replace Ledger.** Do not run `2026082600`, `2026082601`, or `2026082602` — they deploy a fresh Ledger / RipeGov / VaultBook, bind the *previous* generation (`MC 0xD335…`, `Ledger 0xF1CD5…`), and would wipe the points this plan keeps. Against today’s HQ they revert on `require_slot`; do not “fix” their hardcoded addresses and retry.

Do not deploy the `DefaultsRobinhoodLive.vy` already in the tree (block `46,988,201`, old MC `0xD335…`, 12 assets, wrong rate). Step 4 regenerates it.

Do not Bravo `addAsset`. Do not Charlie `setRewardVaultId`. Do not call Foxtrot reserve-engine setters (RipeReserveEngine is already `isRunning=true`). Do not `reset*Points`. After this flip, `arePointsEnabled` is inert — the only emission stop is `Alpha.setRipePerBlock(0)` → execute.

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
| SB 1 / 2 / 3 | Alpha `0xc36b4E…cC26` / Bravo `0xd7F1d8…394f` / Charlie `0xc4d4E0…CEA20` |
| SB 6 Foxtrot | `0xD11B23b6391e294DF49961E64231bddDE5bB5E89` (Aug 25 reserve-engine; **no** auction selectors) |
| Contributor template | `0x619DcD2d3a4Ef3146f0A9B132bF72A333B916E68` |

`registryChangeTimeLock = 0` and every board `actionTimeLock = 0`, so start→confirm and set→execute are same-transaction. HQ/SB `confirmAddressUpdateToRegistry` returns **`False` without reverting** if the pending update is invalid — Safe MultiSend still sees success. Every confirm in this plan must be asserted `== true` in the same transaction before later calls run.

`current-manifest.json` MissionControl / Ledger must equal `hq.getAddr(5)` / `hq.getAddr(4)` before step 4. Today they match (`0xC154…` / `0x7E1d…`).

Solidity `block.number` / Ledger clocks are **L1** (~12s). Child height is ~48.7M and is not what the clocks use.

---

## 1. Park traffic first

Leave live Lootbox **unpaused** through step 3. Live Alpha skips settle when Lootbox is paused and the new rate is 0 — that forfeits the open ripe window.

```
# current Charlie / Foxtrot / Bravo / Alpha / Delta — cancel any pending aid
Charlie.cancelPendingAction(aid)
Foxtrot.cancelPendingAction(aid)
Bravo.cancelPendingAction(aid)
Alpha.cancelPendingAction(aid)
Delta.cancelPendingAction(aid)

# current Charlie — Teller is unpaused
Charlie.pause(teller, true)
```

Nothing was pending at the 2026-08-28/29 walks. Cancel is still required at execution. Bravo can change `assetConfig` between snapshot and flip; HEAD Bravo then reverts on the old MC. Pause Teller **before** the rate goes to 0 so deposits cannot accrue points against a frozen ripe bucket.

RipeReserveEngine is already running. Teller paused will fail its `depositFromTrusted` until step 8. That is expected. Do not start or reconfigure the reserve engine.

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

---

## 4. Snapshot MissionControl into DefaultsRobinhoodLive

After step 3 is on a **finalized** child block.

`prepare_defaults.py` reads MC/Ledger from `migration_history/robinhood-mainnet/v1/current-manifest.json`, not from `hq.getAddr`. Before generate:

```
manifest.MissionControl.address == hq.getAddr(5) == 0xC154F6…2EFDe
manifest.Ledger.address         == hq.getAddr(4) == 0x7E1d75…aeB1
```

**Archive RPC.** Public `https://rpc.mainnet.chain.robinhood.com` prunes state ~6.2k child blocks back while `finalized` lags ~9–11k, so `prepare_defaults` fail-closes (`could not read MissionControl code at snapshot block`). Set `ROBINHOOD_MAINNET_RPC_URL` to an archive endpoint. Prove `eth_getCode(0xC154F6…, snapshotBlock)` returns bytecode **before** generate. The snapshot block must be `≤ finalized` **and** still served.

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

---

## 5. Deploy (do not flip pointers yet)

`_tempGov` on Alpha / Bravo / Charlie / Foxtrot **must not** equal HQ governance (`0xE488…`). LocalGov reverts if it does. `_tempGov` is the deployer EOA. After deploy, that EOA can still `setRipePerBlock`, `pause`, `recoverFunds`, `setRewardVaultId`, and Foxtrot reserve setters **until** `relinquishGov`.

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

Do not flip yet. EIP-170: AuctionHouse 24,564 (12 B free), Deleverage 24,559 (17 B). Remeasure if source moved after `42fec6da`.

---

## 6. Flip pointers

One assertion-backed Safe batch (or a helper that reverts if any call returns `false`). `registryChangeTimeLock = 0` so start+confirm can be the same tx. Do **not** treat a `false` confirm as success.

```
# auctions: live Charlie has start/pause; live Foxtrot does not; HEAD is the reverse.
# Confirming Charlie first clears its addrToRegId. New Charlie + old Foxtrot
# ⇒ AuctionHouse has no registered board that can start/pause.
# assert each start/confirm == true
Switchboard.startAddressUpdateToRegistry(6, newFoxtrot)
Switchboard.confirmAddressUpdateToRegistry(6)
Switchboard.startAddressUpdateToRegistry(3, newCharlie)
Switchboard.confirmAddressUpdateToRegistry(3)

# Bravo calls rewardVaultId — live MC does not have that selector.
# Flip MC before Bravo.
RipeHq.startAddressUpdateToRegistry(5, newMissionControl)
RipeHq.confirmAddressUpdateToRegistry(5)
RipeHq.startAddressUpdateToRegistry(16, newLootbox)
RipeHq.confirmAddressUpdateToRegistry(16)
```

In the **same transaction** as the MC + Lootbox confirms (new Charlie is already SB 3; new MC should have `ripePerBlock == 0`):

```
newCharlie.updateRipeRewards()
```

Then:

```
Switchboard.startAddressUpdateToRegistry(1, newAlpha)
Switchboard.confirmAddressUpdateToRegistry(1)
Switchboard.startAddressUpdateToRegistry(2, newBravo)
Switchboard.confirmAddressUpdateToRegistry(2)

RipeHq.startAddressUpdateToRegistry(9, newAuctionHouse)
RipeHq.confirmAddressUpdateToRegistry(9)
RipeHq.startAddressUpdateToRegistry(18, newDeleverage)
RipeHq.confirmAddressUpdateToRegistry(18)
RipeHq.startAddressUpdateToRegistry(19, newCreditRedeem)
RipeHq.confirmAddressUpdateToRegistry(19)
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

Restore the rate recorded in step 3. Walked live value:

```
new Alpha.setRipePerBlock(41666666666666666)
new Alpha.executePendingAction(aid)
new Charlie.pause(teller, false)
```

Not `0.009e18` (launch Defaults). Not `0.0009e18` (checked-in Live file). HEAD Alpha settles at the old rate (0) then writes — no gap mint if step 3 held.

Teller unpause is `Charlie.pause(teller, false)` (gov-only). Not a direct Teller call.

To stop again: `Alpha.setRipePerBlock(0)` → execute. Pause Lootbox does **not** stop clocks after this flip.
