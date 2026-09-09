# PR #223 rehearsal-to-launch runbook

Use the existing asset and existing reward vault. No new asset or vault is required.

This runbook has two separate jobs:

1. **Part 1 — contract cutover:** install PR #223 once, while the launch is still private.
2. **Part 2 — asset launch:** move each launch row from internal rehearsal, through the public announced collection window, to live rewards.

Do not describe every pre-launch state as "pre-announcement." There are two materially different pre-announcement phases:

- **Internal rehearsal:** deposits earn real points and RIPE. The clock is `0`.
- **Launch staging:** rehearsal has been erased and the row is armed. Deposits are closed and the clock is `max_value(uint256)`.

## Lifecycle at a glance

There are four durable phases. The milestones are the transactions that move the row from one phase to the next.

| Phase | Public status | Clock | Deposits | Voter allocation | What happens |
|---|---|---:|---|---:|---|
| 1. Internal rehearsal | Not announced | `0` | Tester policy | Test value may be nonzero | Test real balances, points, allocations, and RIPE claims. PR #223 is installed during this phase. |
| 2. Launch staging | Not announced | `max` | Closed | `0` | Rehearsal is erased. Install final vault membership, limits, and whitelist; queue the launch action. |
| 3. Announced collection | Announced | `max` | Open | `0` | Deposits are public, but balances earn no points or RIPE during the operational countdown. |
| 4. Live rewards | Live | `B` | Production policy | Production nonzero value | Depositors present at or after `B` accrue rewards from `B`. |

The key milestones are therefore:

1. **End rehearsal:** initiate and then execute `preparePromotionalCollection`. Deposits close immediately; execution clears rehearsal points and changes the clock from `0` to `max`.
2. **Public announcement:** after final config reads pass, open deposits and announce the no-reward collection window.
3. **Start rewards:** execute the previously queued voter-only action; the clock changes from `max` to that execution block, `B`.

There is no onchain 24-hour timer. If the public countdown is 24 hours, governance must wait 24 hours between milestones 2 and 3. Executing late starts rewards late. Executing early starts rewards early.

## Clock rules

The clock is `accrualStartBlock[asset][vaultId]` on the reward row:

| Value | Meaning |
|---|---|
| `0` | Ordinary operation / internal rehearsal. Points and RIPE are real. |
| `max_value(uint256)` | Armed collection. Balances update, but points do not accrue. |
| `B` | Live rewards. `B` is the block that executed the production voter action. |

After `max` or `B`, the clock cannot return to `0`. After `B`, voter allocation is permanent. Staker allocation stays `0` throughout this launch. LTV stays `0` while the clock is `max`.

---

## Part 1 — one-time PR #223 contract cutover

Do this once, while the launch is still in **Phase 1: internal rehearsal** and before any row is armed or publicly announced. Part 1 installs the machinery; it does not end rehearsal or announce the launch.

### 1. Freeze and verify the deployment candidates

Do not replace MissionControl after any launch row is already `max` or `B`; PR #223 does not carry clocks into another MissionControl generation.

Before deployment:

1. Freeze unrelated MissionControl, RipeHq registry, and Switchboard registry changes.
2. Cancel pending actions on the old Bravo, Charlie, and Foxtrot.
3. Confirm every launch row still has `accrualStartBlock(asset, vaultId) == 0`.
4. Pin a finalized Robinhood block for the MissionControl state snapshot.
5. Generate and verify `DefaultsRobinhoodLive` from that same block:

```text
python scripts/prepare_defaults.py --network robinhood-mainnet --block-number <FINALIZED_BLOCK>
python scripts/verify_defaults.py --network robinhood-mainnet --block-number <FINALIZED_BLOCK>
```

The checked-in file currently identifies its own snapshot block. Do not assume that pin is the deployment pin: intentionally approve it or regenerate, review, and commit a final candidate before deployment.

`DefaultsRobinhoodLive` does **not** carry `userConfig` or `userDelegation`. Inventory known entries and either reapply them to the candidate MissionControl or explicitly accept and communicate their loss. The verifier must exact-match observable vault pointers, reward-vault pointers, and historical vault classifications. If it fails, stop and prepare separate state-carry actions before connecting the replacement.

Deploy and verify the exact reviewed candidates:

| Contract | Registry slot | Requirement |
|---|---:|---|
| Ledger | RipeHq 4 | Do not replace. |
| DefaultsRobinhoodLive | none | Exact approved snapshot used by the new MissionControl constructor. |
| MissionControl | RipeHq 5 | Constructor `(ripeHq, defaults)`. Its new promo clock mapping starts empty, so rows start at `0`. |
| Lootbox | RipeHq 16 | Replace after MissionControl is connected. |
| SwitchboardGolf | Switchboard 7 | New board. Owns `addAsset`, liquidation, debt/LTV, and whitelist. It must receive ID `7`. |
| SwitchboardCharlie | Switchboard 3 | Replace. Guards reward-vault retargeting and deregistration after a clock is nonzero. |
| SwitchboardFoxtrot | Switchboard 6 | Replace. The GREEN reference-pool snapshot entrypoint moved from Bravo to Foxtrot. |
| SwitchboardBravo | Switchboard 2 | Replace after Golf and MissionControl. Owns deposit parameters and `preparePromotionalCollection`; it no longer owns `addAsset`. |

Bravo, Charlie, Foxtrot, and Golf use:

```text
(ripeHq, tempGov, minConfigTimeLock, maxConfigTimeLock)
```

Their `actionTimeLock` starts at `0`. `setActionTimeLockAfterSetup(n)` can be called once; passing `0` sets the minimum, not zero. Leave it untouched to retain a zero action delay, or set the intentionally approved delay before the temporary governor relinquishes governance.

Before registering Golf, read `Switchboard.numAddrs()`. It must make Golf the next ID, `7`, with no competing registration pending. A merely nonzero ID is not sufficient because follow-on Robinhood work reads `Switchboard.getAddr(7)`.

### 2. Queue all registry changes

RipeHq and Switchboard registry updates are timelocked. Queue first; do not put each `start*` directly beside its `confirm*` and expect both to succeed in one transaction.

```text
Switchboard.startAddNewAddressToRegistry(newGolf, "SwitchboardGolf")

RipeHq.startAddressUpdateToRegistry(5, newMissionControl)
RipeHq.startAddressUpdateToRegistry(16, newLootbox)

Switchboard.startAddressUpdateToRegistry(3, newCharlie)
Switchboard.startAddressUpdateToRegistry(6, newFoxtrot)
Switchboard.startAddressUpdateToRegistry(2, newBravo)
```

Read both registries' live `registryChangeTimeLock` values and record every emitted confirmation block. Wait until all six updates are mature. An early registry confirmation reverts; it does not return `False`.

### 3. Confirm in the safe operational order

Immediately before execution, simulate every confirmation from the Safe and require Golf to return `7` and every update to return `True`. Freeze other registry activity until completion.

Use an assertion-capable batch if available. A raw Safe MultiSend does not fail merely because a child call returns `False`; if using one, the simulations and immediate pointer readbacks below are mandatory.

The order below minimizes the time spent in a mixed old/new generation and is required if confirmations are separate transactions. It is not a magic contract-level ordering rule: if every confirmation is inside one atomic batch and there are no business calls between confirmations, the final verified pointer set is what matters. Never make deposits, checkpoints, or configuration calls while only part of the cutover is connected.

Execute the confirmations in this order:

```text
# 1. Golf must be live before Bravo
golfId = Switchboard.confirmNewAddressToRegistry(newGolf)
# require golfId == 7 and Switchboard.getAddr(7) == newGolf

# 2. MissionControl before contracts that read it dynamically
RipeHq.confirmAddressUpdateToRegistry(5)
# require RipeHq.getAddr(5) == newMissionControl

# 3. Lootbox against the new MissionControl generation
RipeHq.confirmAddressUpdateToRegistry(16)
# require RipeHq.getAddr(16) == newLootbox

# 4. Charlie
Switchboard.confirmAddressUpdateToRegistry(3)
# require Switchboard.getAddr(3) == newCharlie

# 5. Foxtrot preserves the GREEN snapshot entrypoint
Switchboard.confirmAddressUpdateToRegistry(6)
# require Switchboard.getAddr(6) == newFoxtrot

# 6. Bravo last
Switchboard.confirmAddressUpdateToRegistry(2)
# require Switchboard.getAddr(2) == newBravo
```

Once the pointer reads pass, apply the approved action delays, if any, and have the temporary governor call `relinquishGov()` on each new board.

### 4. Part 1 completion reads

Do not end rehearsal until all of these pass:

- Ledger is unchanged at `RipeHq.getAddr(4)`.
- MissionControl, Lootbox, Bravo, Charlie, Foxtrot, and Golf pointers equal the reviewed candidates.
- `Switchboard.getAddr(7)` is Golf.
- General config, asset configs, `vaultIds`, `rewardVaultId`, allocation totals, whitelist, vault pointers, and vault classifications match the approved snapshot.
- The treatment of known `userConfig` and `userDelegation` entries is complete and recorded.
- Every launch row has `accrualStartBlock(asset, vaultId) == 0`.
- `Golf.addAsset` exists.
- `Bravo.preparePromotionalCollection` exists and `Bravo.addAsset` does not.
- `Foxtrot.addGreenRefPoolSnapshot` exists.
- Each new board has the approved governor, `actionTimeLock`, and `expiration`.

At this point PR #223 is installed, but you are **still in internal rehearsal**. Perform a final private deposit/checkpoint/claim sanity test if desired. It earns real points and RIPE because the clock is still `0`.

---

## Part 2 — per-asset rehearsal and launch

Repeat Part 2 for each reward row. Multiple voter actions executed in the same transaction receive the same `B`.

Use `address(0)` for `_missionControl` in the calls below so the boards resolve the current MissionControl. Bravo cannot change `vaultIds` and an allocation in the same action.

### Phase 1 — internal rehearsal, before public announcement

This is the testing phase.

Expected state:

- clock `0`
- `asset` is supported, `vaultId` is its existing `rewardVaultId`, and the asset is supported in that vault
- staker allocation `0` and LTV `0` before the prepare action
- tester-only access policy as desired
- deposits open or closed according to the test
- test voter allocation may be nonzero
- balance points, voter allocations, RIPE accrual, claims, and withdrawals are real

Test the full lifecycle you care about. Keep a census of every address that has rehearsal `balancePoints`; `preparePromotionalCollection` accepts at most 40 unique, nonzero tester addresses. An empty list is valid only if aggregate `balancePoints` is already `0`.

Before ending rehearsal, cancel any old pending Bravo allocation action. Do not reuse a rehearsal allocation action for launch.

### Milestone 1 — end rehearsal

#### 1A. Close deposits and queue cleanup

```text
prepareId = Bravo.preparePromotionalCollection(asset, vaultId, testers)
```

Immediate effect: `canDeposit = false`. The clock is still `0`, and existing balances may continue ordinary accrual until the prepare action executes. Record:

- `prepareId`
- `Bravo.getActionConfirmationBlock(prepareId)`
- `Bravo.pendingActions(prepareId).expiration`

Testers do not have to withdraw. The small amount of rehearsal RIPE already paid or left in the reward bucket is an accepted launch expense.

#### 1B. Erase rehearsal and arm the row

Execute while `block.number` is at or after the confirmation block and strictly before expiration:

```text
Bravo.executePendingAction(prepareId)
```

For Switchboard actions, an early execute returns `False`. An expired execute cancels the action and returns `False`. Always read the state; never treat Safe success alone as proof.

Required reads:

- `accrualStartBlock(asset, vaultId) == max_value(uint256)`
- voter `0`, staker `0`, LTV `0`
- `canDeposit == false`
- asset `balancePoints`, `ripeStakerPoints`, `ripeVotePoints`, and `ripeGenPoints` are all `0`
- asset `lastUsdValue == 0`
- `lastBalance` may remain nonzero

If an omitted tester still has balance-point tickets, execution reverts and the clock remains `0`.

The asset is now in **Phase 2: launch staging**. Rehearsal is over. There is no path back to `0`.

### Phase 2 — launch staging, before public announcement

Deposits stay closed, the clock stays `max`, and voter stays `0` while final production settings are installed.

#### 1. Final vault membership and deposit limits

Skip if already correct.

```text
configId = Bravo.setAssetDepositParams(
    asset,
    productionVaultIds,
    0,                         # staker
    0,                         # voter remains off
    productionPerUserLimit,
    productionGlobalLimit,
    productionMinBalance,
    address(0),
)
Bravo.executePendingAction(configId)
```

Read `vaultIds` and all three limits. Required relationships are `perUser > 0`, `global >= perUser`, and `min <= perUser`.

#### 2. Final whitelist

Skip if already correct. Use `address(0)` for unrestricted public access.

```text
whitelistId = Golf.setWhitelistForAsset(asset, productionWhitelist, address(0))
Golf.executePendingAction(whitelistId)
```

Read the whitelist.

#### 3. Queue the voter-only launch action

The action must change only voter allocation. All other values must exactly match the production config already installed.

```text
voterId = Bravo.setAssetDepositParams(
    asset,
    currentVaultIds,
    0,
    productionVoterAlloc,      # nonzero
    currentPerUserLimit,
    currentGlobalLimit,
    currentMinBalance,
    address(0),
)
```

This queues the launch; it does not start rewards. Record:

- `voterId`
- `voterConfirmBlock = Bravo.getActionConfirmationBlock(voterId)`
- `voterExpiration = Bravo.pendingActions(voterId).expiration`

Choose the public launch time so `voterConfirmBlock <= plannedLaunchBlock < voterExpiration`. If the action delay is longer than the desired public countdown, queue it earlier. If it will expire before launch, cancel it and queue a fresh action before announcing.

Do not change `vaultIds` in this action. Bravo rejects changing membership and allocations together.

### Milestone 2 — announce and open deposits

Only announce after all Phase 2 reads pass and the voter action will remain executable through the intended launch time.

```text
Charlie.setCanDepositAsset(asset, True, address(0))
```

This is immediate. Read all of the public-launch state:

- `canDeposit == true`
- public whitelist is correct
- clock is `max_value(uint256)`
- voter `0` and staker `0`
- production `vaultIds` and deposit limits are correct
- all four rehearsal point buckets are `0`
- `lastUsdValue == 0`

Now make the public announcement:

> Deposits are open. Rewards have not started. Rewards are planned to start after the announced countdown.

This begins **Phase 3: announced collection**. Opening deposits and making the announcement should be treated as one operational milestone; make the announcement only after the transaction and reads succeed.

### Phase 3 — announced collection window

During the countdown:

- clock remains `max`
- deposits are open
- voter remains `0`
- balances update
- no points or RIPE accrue
- do not execute `voterId`

Monitor both `voterConfirmBlock` and `voterExpiration`. Before launch, require `Bravo.canConfirmAction(voterId) == true` and `lastBalance != 0`. Activation reverts if everyone withdrew and nobody deposited.

Anyone still deposited when rewards start—including a leftover tester—earns from `B`.

### Milestone 3 — start rewards

At or after the publicly announced time:

```text
Bravo.executePendingAction(voterId)
```

Required reads:

- the call returned `True`
- `accrualStartBlock(asset, vaultId) == block.number`
- voter equals `productionVoterAlloc`
- staker remains `0`

That execution block is `B`. The row is now in **Phase 4: live rewards**. A later execution produces a later `B`; there is no retroactive accrual for the collection window.

---

## Abort rules by phase

| Where you stop | What can be done |
|---|---|
| Phase 1, after prepare is queued but before it executes | Cancel `prepareId`, or let it expire. Deposits remain off because initiation closed them; Charlie may reopen them. Clock remains `0`. |
| Phase 2, after clock is `max` | Cancel or let `voterId` expire and queue another later. Charlie may close deposits. The clock remains `max`; there is no disarm. |
| Phase 3, announced collection | Close deposits and cancel the voter action if launch must pause. Communicate the pause. The clock still remains `max`. |
| Phase 4, after `B` | No disarm. Voter allocation and reward start are permanent for this lifecycle. |

## Hard stops

- Do not connect Bravo before Golf is live at Switchboard ID `7`.
- Do not connect Lootbox to the new generation before MissionControl, or leave the old Lootbox connected afterward.
- Do not leave the old Foxtrot connected; the new Foxtrot owns `addGreenRefPoolSnapshot`.
- Do not replace MissionControl after any row is `max` or `B`.
- Do not replace Ledger.
- Do not announce or open deposits before the clock is `max` and production membership, limits, and whitelist read correctly.
- Do not change `vaultIds` in the voter action.
- Do not execute the voter action before the announced reward-start time.
- Do not rely on Safe transaction success when the called function can return `False`; read the resulting state.
