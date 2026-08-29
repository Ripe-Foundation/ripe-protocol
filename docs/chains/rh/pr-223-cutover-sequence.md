# PR #223 cutover

Connect the contracts, then configure the promo. No new asset. No new vault.

Clock on the reward row (`accrualStartBlock[asset][vaultId]`):

| value | meaning |
|---|---|
| `0` | ordinary / rehearsal — real points and RIPE |
| `max_value(uint256)` | collection — balances update, no points |
| `B` | live — rewards from that block |

After `max` or `B`, the clock cannot go back to `0`. After `B`, voter is permanent. Staker stays `0` the whole time. LTV stays `0` while the clock is `max`.

`executePendingAction` returns `False` (does not revert) if the action is early or expired. After every execute, read the write. If it did not happen, stop.

---

## Part 1 — connect

### What moves

| Contract | Slot | Action |
|---|---|---|
| Ledger | RipeHq 4 | Do not touch. |
| MissionControl | RipeHq 5 | Replace. Constructor `(ripeHq, defaults)`. Defaults must be the live configs. New `accrualStartBlock` is empty, so every row starts at `0`. |
| Lootbox | RipeHq 16 | Replace after MissionControl. |
| SwitchboardGolf | new Switchboard id | Register and confirm before Bravo. Owns `addAsset`, liq, debt/LTV, whitelist. |
| SwitchboardCharlie | Switchboard 3 | Replace. Blocks reward-vault retarget / deregister once a clock is nonzero. |
| SwitchboardBravo | Switchboard 2 | Replace after Golf and MissionControl. Owns deposit params and `preparePromotionalCollection`. No `addAsset`. |
| SwitchboardFoxtrot | Switchboard 6 | Leave it. |
| Everything else | | Leave it. |

Do not replace MissionControl after any row is `max` or `B`. There is no clock carry.

Cancel pending actions on Bravo and Charlie before you replace them.

### Constructors

Bravo, Charlie, Golf:

```text
(ripeHq, tempGov, minConfigTimeLock, maxConfigTimeLock)
```

`actionTimeLock` starts at `0`. `setActionTimeLockAfterSetup(n)` can be called once; if you pass `0` it writes `minConfigTimeLock`, not `0`. Live RH boards are already at `0`. Leave them at `0` unless you want a delay. Temp deployer stays a governor until `relinquishGov()`.

MissionControl:

```text
(ripeHq, defaults)
```

### Order

Fatal if reordered.

```text
# 1. Golf — new board
Switchboard.startAddNewAddressToRegistry(golf, "SwitchboardGolf")
Switchboard.confirmNewAddressToRegistry(golf)          # returns golfId; must be nonzero

# 2. MissionControl
RipeHq.startAddressUpdateToRegistry(5, newMc)
RipeHq.confirmAddressUpdateToRegistry(5)
# read: RipeHq.getAddr(5) == newMc

# 3. Lootbox — after MissionControl
RipeHq.startAddressUpdateToRegistry(16, newLootbox)
RipeHq.confirmAddressUpdateToRegistry(16)
# read: RipeHq.getAddr(16) == newLootbox

# 4. Charlie
Switchboard.startAddressUpdateToRegistry(3, newCharlie)
Switchboard.confirmAddressUpdateToRegistry(3)
# read: Switchboard.getAddr(3) == newCharlie

# 5. Bravo — after Golf and MissionControl
Switchboard.startAddressUpdateToRegistry(2, newBravo)
Switchboard.confirmAddressUpdateToRegistry(2)
# read: Switchboard.getAddr(2) == newBravo
```

`start*` / `confirm*` also return `False` without reverting. Read the pointer after each confirm.

Optional, on each new board, before Part 2:

```text
board.setActionTimeLockAfterSetup(desiredDelay)   # skip to keep 0
tempGov → board.relinquishGov()
```

### After connect

- Ledger still `RipeHq.getAddr(4)`.
- Copied asset configs, `vaultIds`, `rewardVaultId`, allocs, whitelist match live.
- `accrualStartBlock(asset, vaultId) == 0` on every launch row.
- `Golf.addAsset` exists.
- `Bravo.preparePromotionalCollection` exists.
- `Bravo.addAsset` does not exist.

---

## Part 2 — configure the promo

Do not start until Part 1 is connected and the reads above pass.

### Parameters

| Field | Rule |
|---|---|
| `asset` | Existing supported asset. |
| `vaultId` | Existing `rewardVaultId`. Already supported in that vault. |
| `testers` | Every address with rehearsal `balancePoints`. Max 40, unique, nonzero. Empty only if aggregate `balancePoints` is already `0`. |
| `vaultIds` | Production membership. Must already be on the asset before deposits open and before the voter action. |
| `stakersPointsAlloc` | `0` |
| `voterPointsAlloc` | `0` until the last action. Then the production nonzero value. |
| `perUserDepositLimit`, `globalDepositLimit`, `minDepositBalance` | Production limits. Must already be on the asset before deposits open. `perUser > 0`, `global >= perUser`, `min <= perUser`. |
| `whitelist` | Production whitelist, or `address(0)` for unrestricted. |
| `canDeposit` | Closed by prepare. Stay closed until clock is `max` and vaultIds / limits / whitelist are already production. Charlie opens it immediately (no timelock). |

`_missionControl` is `address(0)` on every call below (current MissionControl). Bravo cannot change `vaultIds` and an allocation in the same action.

### 1. Close deposits and queue the arm

```text
Bravo.preparePromotionalCollection(asset, vaultId, testers)
```

Immediate: `canDeposit = false`. Queues the reset and the `max` write. Record the action id.

### 2. Arm

Wait until confirmable if `actionTimeLock > 0`.

```text
Bravo.executePendingAction(prepareId)
```

Then read, or stop:

- `accrualStartBlock(asset, vaultId) == max_value(uint256)`
- voter `0`, staker `0`, LTV `0`
- `canDeposit == false`
- asset `balancePoints`, `ripeStakerPoints`, `ripeVotePoints`, `ripeGenPoints` all `0`
- asset `lastUsdValue == 0`
- `lastBalance` may be nonzero

If an unlisted tester still has tickets, this execute reverts and the clock stays `0`.

### 3. Production vaultIds and limits — deposits still off, voter still 0

Skip if they already match production.

```text
Bravo.setAssetDepositParams(
    asset,
    productionVaultIds,
    0,                    # staker
    0,                    # voter stays 0
    productionPerUserLimit,
    productionGlobalLimit,
    productionMinBalance,
    address(0),
)
Bravo.executePendingAction(configId)
```

Read `vaultIds` and the three limits. Do not open deposits until they match.

### 4. Production whitelist — deposits still off

Skip if it already matches.

```text
Golf.setWhitelistForAsset(asset, publicWhitelist, address(0))
Golf.executePendingAction(whitelistId)
```

Read the whitelist.

### 5. Open deposits

Only after steps 2–4 read back.

```text
Charlie.setCanDepositAsset(asset, True, address(0))
```

Immediate. Read `canDeposit == true`.

### 6. Queue voter only

Same `vaultIds` and limits already on the asset. Only voter changes.

```text
Bravo.setAssetDepositParams(
    asset,
    currentVaultIds,      # already production; do not change
    0,
    productionVoterAlloc, # nonzero
    currentPerUserLimit,
    currentGlobalLimit,
    currentMinBalance,
    address(0),
)
```

This does not write `B`. If you change `vaultIds` here, Bravo reverts (`cannot change membership and allocs together`). If this action runs while the clock is still `0`, it sets ordinary voter and never writes `B`.

### 7. Collection

Public countdown is ops. Anyone who deposits (or stayed in) updates `lastBalance` and earns nothing until `B`. Do not execute the voter action until you intend to start rewards.

Activation requires `lastBalance != 0`. If everyone withdrew and nobody deposited, it reverts.

### 8. Start rewards

```text
Bravo.executePendingAction(voterId)
```

Read: `accrualStartBlock(asset, vaultId) == block.number`, voter equals the production value, staker still `0`. That block is `B`. Late execute is a later `B`. Same-tx executes share `B`.

---

## Abort

- Before prepare executes: `Bravo.cancelPendingAction(prepareId)`. Deposits stay off until Charlie opens them.
- After `max`, before `B`: cancel or let the voter action expire and queue another. Clock stays `max`. Charlie can close deposits; that does not disarm the clock.
- After `B`: no disarm.

---

## Do not

- Confirm Bravo before Golf is a live Switchboard.
- Confirm Lootbox against the old MissionControl, or leave the old Lootbox on the new MissionControl.
- Open deposits, change the whitelist, or queue voter before the clock is `max`.
- Open deposits before production `vaultIds` and limits are on the asset.
- Change `vaultIds` in the voter action.
- Reuse a rehearsal Bravo action as the launch action.
- Replace MissionControl after any clock is `max` or `B`.
- Replace Ledger.
- Touch Foxtrot for this promo.
