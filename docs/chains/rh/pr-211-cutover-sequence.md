# PR #211 cutover

One sequence. Do these in order. Do not replace Ledger.

Replace only: Foxtrot (SB 6), Charlie (SB 3), MissionControl (HQ 5), Lootbox (HQ 16), Alpha (SB 1), Bravo (SB 2), AuctionHouse (HQ 9), Deleverage (HQ 18), CreditRedeem (HQ 19).

Build MissionControl as `(RipeHq, DefaultsRobinhoodLive)` — not launch `DefaultsRobinhood`. Do not Bravo `addAsset`. Do not Charlie `setRewardVaultId`. Do not call Foxtrot reserve-engine setters. Do not `reset*Points`. Leave live Lootbox **unpaused** until step 4 has executed (paused Lootbox makes live Alpha skip the settle).

---

## 1. Stamp Ledger (current Charlie + Alpha)

Current Charlie, Lootbox unpaused:

```
Charlie.updateRipeRewards()
```

Then current Charlie, one call per row (`vaultAddr` = `VaultBook.getAddr(vaultId)`):

```
Charlie.checkpointAssetDepositPointsAt(asset, vaultId, vaultAddr)
```

| asset | vaultId | vaultAddr |
|---|---|---|
| WETH `0x0Bd7D308f8E1639FAb988df18A8011f41EAcAD73` | 3 | SimpleErc20 `0x4F89C94636995eF20d40d5592bA2585348bE6D53` |
| SPCX `0x4a0E65A3EcceC6dBe60AE065F2e7bb85Fae35eEa` | 3 | same |
| AAPL `0xaF3D76f1834A1d425780943C99Ea8A608f8a93f9` | 3 | same |
| GME `0x1b0E319c6A659F002271B69dB8A7df2F911c153E` | 3 | same |
| RIPE `0x4D3f37a965b21aB4122e92Dd41D2693E742c883b` | 2 | RipeGov `0xFa767a19c0C2B80D5A8d5b88be67de153Df1b2f2` |
| UNI-V2 `0xba6F6CBa1a4104000847d4fdccB676E99166CEcE` | 2 | same |
| UNI-V2 `0x9b8537bE0FD5cf9B2AD495C5A85130D5bAe4769D` | 2 | same |
| sGREEN `0x290a52380A88f743813B8C3e9F6B0e61DB5FDF73` | 1 | StabilityPool `0xe238b50d79D566aa59A2deF4362a698eDC3dC395` |
| GREEN/USDG `0x2fD13b49F970e8C6D89283056C1c6281214b7EB6` | 1 | same |

Skip NVDA, TSLA, GOOGL (`lastUpdate == 0`) and GREEN (no vault). No borrow-points call.

---

## 2. Stop the emission rate (current Alpha)

```
Alpha.setRipePerBlock(0)
Alpha.executePendingAction(aid)     # after the Alpha timelock
```

Read back: `rewardsConfig.ripePerBlock == 0`, and each row above has `Ledger.assetDepositPoints[vaultId][asset].lastUpdate` equal to this block. `Ledger.ripeRewards.lastUpdate` equal to this block.

---

## 3. Snapshot MissionControl into DefaultsRobinhoodLive

After step 2 is on a **finalized** block. Needs `ROBINHOOD_MAINNET_RPC_URL`.

```
python scripts/prepare_defaults.py \
  --network robinhood-mainnet \
  --block-number <FINALIZED_BLOCK> \
  --dry-run
```

Coverage report: `assetConfigs` = 13. Review the printed contract. Then write and verify:

```
python scripts/prepare_defaults.py \
  --network robinhood-mainnet \
  --block-number <FINALIZED_BLOCK>

python scripts/verify_defaults.py --network robinhood-mainnet
```

Review the `DefaultsRobinhoodLive.vy` diff. Constructor will copy every live `assetConfig` and set `rewardVaultId` to each asset’s only vault.

---

## 4. Park traffic

Cancel every pending Charlie action, and Foxtrot if Switchboard 6 is filled. Pause Teller if it is unpaused.

---

## 5. Deploy (do not flip pointers yet)

Deploy `DefaultsRobinhoodLive`, then the nine replacements. MissionControl constructor: `(RipeHq, DefaultsRobinhoodLive)`.

---

## 6. Flip pointers

Same Safe batch, or back-to-back with no traffic.

```
Switchboard.startAddressUpdate / confirm     Foxtrot → slot 6
Switchboard.startAddressUpdate / confirm     Charlie → slot 3
RipeHq.startAddressUpdate / confirm          MissionControl → slot 5
RipeHq.startAddressUpdate / confirm          Lootbox → slot 16
```

In the **same transaction** as the MC + Lootbox confirms:

```
new Charlie.updateRipeRewards()
```

Then:

```
Switchboard.startAddressUpdate / confirm     Alpha → slot 1
Switchboard.startAddressUpdate / confirm     Bravo → slot 2
RipeHq.startAddressUpdate / confirm          AuctionHouse → slot 9
RipeHq.startAddressUpdate / confirm          Deleverage → slot 18
RipeHq.startAddressUpdate / confirm          CreditRedeem → slot 19
```

(If those updates were already initiated, this step is the confirms only.)

---

## 7. Read back

```
hq.getAddr(5 / 9 / 16 / 18 / 19)     new MC / AH / Lootbox / DL / CR
switchboard.getAddr(3 / 6)           new Charlie / Foxtrot
isSupportedAsset                     all 13 live assets
rewardVaultId                        every asset with a vault → that vault
totalPointsAllocs.stakers            30_00
rewardsConfig.genDepositorsAlloc     0
rewardsConfig.ripePerBlock           0
```

---

## 8. Turn the clock back on

```
new Alpha.setRipePerBlock(0.009e18)
new Alpha.executePendingAction(aid)     # after the Alpha timelock
Teller unpause
```

To stop again: `Alpha.setRipePerBlock(0)` → execute.
