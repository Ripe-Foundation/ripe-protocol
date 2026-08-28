# PR #211 cutover

Replace these nine. Nothing else. Do not replace Ledger.

| Contract | Slot |
|---|---|
| SwitchboardFoxtrot | Switchboard 6 |
| SwitchboardCharlie | Switchboard 3 |
| MissionControl | RipeHq 5 |
| Lootbox | RipeHq 16 |
| SwitchboardAlpha | Switchboard 1 |
| SwitchboardBravo | Switchboard 2 |
| AuctionHouse | RipeHq 9 |
| Deleverage | RipeHq 18 |
| CreditRedeem | RipeHq 19 |

---

## Live assets (read 2026-08-28)

Constructor only copies WETH, RIPE, sGREEN, GREEN. The other nine are already on live MissionControl. If HQ 5 flips without them, those rows vanish. Stocks are 70% LTV; leftover deposits then block all new borrow on that account.

Copy the **live** `assetConfig` tuple. Do not invent Defaults values.

| Asset | Address | Vault | On new MC how | Checkpoint? |
|---|---|---|---|---|
| WETH | `0x0Bd7…AD73` | 3 SimpleErc20 | constructor | yes (`lastUpdate` set) |
| RIPE | `0x4D3f…883b` | 2 RipeGov | constructor | yes |
| sGREEN | `0x290a…DF73` | 1 StabilityPool | constructor | yes |
| GREEN | `0x355b…82F3` | — | constructor | no (no vault) |
| GREEN/USDG | `0x2fD1…7EB6` | 1 | Bravo `addAsset` onto the **candidate** | yes |
| SPCX | `0x4a0E…5eEa` | 3 | Bravo add onto candidate | yes |
| AAPL | `0xaF3D…93f9` | 3 | Bravo add onto candidate | yes |
| GME | `0x1b0E…153E` | 3 | Bravo add onto candidate | yes |
| UNI-V2 | `0xba6F…CEcE` | 2 | Bravo add onto candidate | yes |
| UNI-V2 | `0x9b85…769D` | 2 | Bravo add onto candidate | yes |
| NVDA | `0xd060…9EEC` | 3 | Bravo add onto candidate | no (`lastUpdate == 0`) |
| TSLA | `0x322F…3b2d` | 3 | Bravo add onto candidate | no |
| GOOGL | `0x2e08…4FE3` | 3 | Bravo add onto candidate | no |

Vault addrs: StabilityPool `0xe238b50d…C395`, RipeGov `0xFa767a19…b2f2`, SimpleErc20 `0x4F89C946…6D53`.

Live Bravo `addAsset(..., _missionControl = candidate)`. ADD_NEW execute does not require HQ-current MC. Initiate now, execute after the Bravo timelock, **then** flip HQ 5.

Constructor already set earners on WETH / RIPE / sGREEN. Bravo add does **not** set `rewardVaultId`. After new Charlie is live, `setRewardVaultId` on each copied asset to its only vault (3 / 2 / 1). Do not Charlie the four Defaults assets.

```
constructor:   rewardVaultId WETH=3, RIPE=2, sGREEN=1
               stakers RIPE=15%, sGREEN=15%, WETH=0
               ripePerBlock 0.009e18
               gen 0, borrowers 10%, stakers 90%, voters 0
```

Leave `genDepositorsAlloc` at 0. Do not call Foxtrot `startReserveEngine`, `setCanAcquireRipe`, or `setReserveEngine*`.

---

## Ledger — settle, then leave it alone

Ledger keeps deposit points, borrow points, and the RIPE buckets. Replacing Lootbox does **not** wipe unclaimed loot. Users do not have to claim first.

Do not call `resetUserBalancePoints`, `resetAssetPoints`, or `resetUserBorrowPoints`. Do not pause Ledger or the live Lootbox until the settles below have landed.

Live Lootbox is pause-gated. Live Alpha `setRipePerBlock(0)` **skips** the settle if Lootbox is paused. Leave Lootbox unpaused until that execute lands.

On the **current** Charlie (Lootbox unpaused). `checkpointAssetDepositPointsAt(asset, vaultId, vaultAddr)`.

1. `updateRipeRewards()`
2. Checkpoint every **yes** row in the table above (touched stocks and LPs too, not just stab/gov)
3. Alpha `setRipePerBlock(0)` → execute
4. Read back: those `lastUpdate`s are this block, `ripePerBlock == 0`

Borrow points use the same formula. No extra borrow step.

---

## Order

**1. Settle Ledger** (above). Cancel pending Charlie, and Foxtrot if slot 6 is filled. Pause Teller if it is unpaused.

**2. Deploy the nine candidates.** Do not flip yet.

**3. Copy the nine extra assets** onto the candidate MissionControl (live Bravo `addAsset` with the live tuple). Execute those timelocks. Read back `isSupportedAsset` for all 13 on the **candidate** before HQ 5 moves.

**4. Flip pointers** (same batch, or back-to-back with no traffic)

1. Foxtrot → Switchboard 6 **and** Charlie → Switchboard 3
2. MissionControl → HQ 5 **and** Lootbox → HQ 16, then in the **same transaction** new Charlie `updateRipeRewards()`. New MC already stores `0.009`. A later-block first settle mints that gap. Same-tx elapsed is 0.
3. New Charlie `setRewardVaultId` for each copied asset → its only vault
4. Alpha → Switchboard 1, Bravo → Switchboard 2
5. AuctionHouse → HQ 9, Deleverage → HQ 18, CreditRedeem → HQ 19

**5. Check, then start**

```
hq.getAddr(5 / 9 / 16 / 18 / 19)     new MC / AH / Lootbox / DL / CR
switchboard.getAddr(3 / 6)           new Charlie / Foxtrot
isSupportedAsset                     all 13 live assets
rewardVaultId                        every asset with a vault → that vault
totalPointsAllocs.stakers            30_00  (copied extras are 0/0)
rewardsConfig.genDepositorsAlloc     0
```

- Alpha `setRipePerBlock(0.009e18)` → execute
- Unpause Teller

To stop again: Alpha `setRipePerBlock(0)` → execute.
