# PR #223 cutover

Two parts:

1. Install the PR #223 contracts onto the live 211 HQ.
2. Run the promotional collection and reward launch on the existing asset and
   vault rows.

This does **not** require a new asset, a new vault, or a virgin Ledger row.

---

## Part 1 — contract install

This is not a normal one-board replace. Live 211 Bravo still has `addAsset`.
Live 211 MissionControl / Lootbox do not speak the promotional-clock ABI.
Golf is not installed.

### What moves

| Contract | Action |
|---|---|
| Ledger | Do not replace. |
| MissionControl | Replace. Copy every live asset, vault, reward-vault, alloc, whitelist, and rewards field. The new `accrualStartBlock` mapping starts at `0` for every row. That is correct for this first 223 MissionControl. |
| Lootbox | Replace after MissionControl, same session. |
| SwitchboardGolf | Register as a new Switchboard board before Bravo is confirmed. |
| SwitchboardBravo | Replace after Golf is a live Switchboard and after MissionControl. 223 Bravo has no `addAsset`. |
| SwitchboardCharlie | Replace in the same session. It blocks reward-vault retarget and deregister once a clock is nonzero. |
| SwitchboardFoxtrot | Optional. 223 Foxtrot has no promotional path. Flip it only if you also want this branch's reserve/auction bytecode. |
| Alpha, Teller, VaultBook, PriceDesk, reserve engine | Do not replace for this PR. |

Do not flip MissionControl with launch Defaults or `prepare_defaults`. Those
do not copy live state and do not carry clocks.

After any row reaches `max` or `B`, do not replace MissionControl again. There
is no clock carry.

### ABI

Regenerate Bravo and Foxtrot ABIs from this branch before building Safe
transactions. The checked-in JSON does not yet match these contracts:
`preparePromotionalCollection` is missing, and Foxtrot still exports the
removed `setAccrualClockArmed`.

### Before the flip

Cancel every pending action on a board you are about to replace. Old action IDs
do not survive the new bytecode. Do not execute a leftover 211 Bravo
`setAssetDepositParams` after the new Bravo is live.

### Install order

Same session. Fatal if reordered:

1. Register Golf on Switchboard. Confirm it before Bravo.
2. RipeHq MissionControl, then confirm.
3. RipeHq Lootbox, then confirm.
4. Switchboard Charlie, then confirm.
5. Switchboard Bravo, then confirm.

MissionControl must precede Lootbox. New Lootbox cannot decode old
`getDepositPointsConfig`; old Lootbox cannot decode the new struct that
includes `accrualStartBlock`. Do not leave those mixed.

MissionControl must precede Bravo. Bravo reads `accrualStartBlock`.

Golf must precede Bravo. Confirming 223 Bravo without Golf removes `addAsset`
from the protocol.

### After the flip, before any `prepare`

Verify onchain:

- Ledger address is unchanged.
- Copied MissionControl asset configs, `vaultIds`, `rewardVaultId`, allocs, and
  whitelist match the pre-flip values.
- `accrualStartBlock(asset, vaultId) == 0` for every launch asset.
- `Golf.addAsset` exists.
- `Bravo.preparePromotionalCollection` exists.
- `Bravo.addAsset` does not exist.

Existing live assets stay ordinary (`clock = 0`) until `prepare`. Do not
`prepare` an asset that still has nonzero LTV or a staker allocation.

---

## Part 2 — promotional collection and reward launch

Do not start this part until Part 1 is registered and verified.

## Public sequence

The public launch has three simple stages:

1. Deposits are open, but no balance points or RIPE rewards accrue.
2. A public countdown runs (for example, 24 hours).
3. Rewards start at the block where governance executes the final Bravo voter
   allocation action.

The countdown is operational only. There is no onchain scheduled-start value
and no permissionless keeper. The actual reward start block, `B`, is always the
block in which the governor executes the final Bravo action. An execution later
than the announced target produces a later `B`; there is no retroactive catch-up.

## Function-call summary

| Phase | Contract call | Result |
|---|---|---|
| Pre-announce | `SwitchboardBravo.preparePromotionalCollection(...)` | Immediately closes deposits and queues rehearsal cleanup plus arming. |
| Pre-announce | `SwitchboardGolf.setWhitelistForAsset(...)` | Queues the production whitelist if a change is needed. |
| Announce batch — first | `SwitchboardBravo.executePendingAction(prepareActionId)` | Clears rehearsal points, writes `max`, clears gen funding weight, and leaves deposits off. |
| Announce batch — second | `SwitchboardGolf.executePendingAction(whitelistActionId)` | Installs the production whitelist if a change was queued. |
| Announce batch — third | `SwitchboardCharlie.setCanDepositAsset(asset, True, address(0))` | Opens deposits only after preparation and whitelist installation. |
| Announce batch — fourth | `SwitchboardBravo.setAssetDepositParams(...)` | Queues the exact production voter allocation and deposit configuration. It does not start rewards. |
| Post-announce | No required write | Monitor the frozen collection state and pending voter action during the countdown. |
| Reward launch | `SwitchboardBravo.executePendingAction(voterActionId)` | Writes actual block `B`, installs voter allocation, and starts rewards. |
| Abort before preparation | `SwitchboardBravo.cancelPendingAction(...)` and, if applicable, `SwitchboardGolf.cancelPendingAction(...)` | Cancels pending work; deposits remain off until Charlie explicitly reopens them. |

## Contract states

| State | `accrualStartBlock` | Voter allocation | Deposits | Effect |
|---|---:|---:|---|---|
| Rehearsal / ordinary | `0` | May be nonzero | Tester configuration | Real points and RIPE rewards accrue normally. |
| Promotional collection | `max_value(uint256)` | `0` | Public configuration | Balances update, but balance, staker, voter, and gen points do not accrue. |
| Rewards live | Actual activation block `B` | Nonzero | Public configuration | Points and rewards accrue beginning at `B`. |

A successful transition to promotional collection cannot be disarmed back to
`0`. After activation at `B`, the promotional voter allocation is permanent.

## Required launch inputs

Record and independently review the following for every launch asset before
creating Safe transactions:

| Input | Requirement |
|---|---|
| Asset | Existing supported asset address. |
| Reward vault ID | Existing nonzero `rewardVaultId` for the asset; the asset must already be supported in this vault. |
| Tester list | Every address with rehearsal `balancePoints` that must be cleared; maximum 40, unique, and nonzero. An empty list is allowed only if aggregate `balancePoints` is already zero. Anyone still deposited at `B` earns from `B`, including leftover testers. |
| Public whitelist | Exact production whitelist address, or `address(0)` if the intended production configuration is unrestricted. |
| Vault IDs | Exact production `vaultIds` array to preserve in the final Bravo action. |
| Staker allocation | Must remain `0`. |
| Voter allocation | Exact nonzero production allocation that will activate rewards. |
| Deposit limits | Exact production per-user limit, global limit, and minimum balance. The final Bravo action writes all of these fields. |
| Countdown | Public duration or target time. It must not end before the final Bravo action is confirmable. |

For calls with the optional `_missionControl` argument, omit it or pass
`address(0)` to target the current MissionControl.

## Phase 0: launch prerequisites

Part 1 must already be done. Do not start the launch sequence until all of
these are true:

- The intended PR #223 Bravo, Charlie, Golf, MissionControl, and Lootbox
  contracts are the live registry pointers from Part 1.
- Ledger and VaultBook still resolve to the pre-223 addresses.
- The asset and reward vault are already registered and supported.
- `rewardVaultId(asset)` equals the intended reward vault ID.
- `accrualStartBlock(asset, vaultId) == 0`.
- Asset LTV is `0`.
- Staker allocation is `0`.
- The tester census is complete. The chain cannot enumerate every address with
  residual user points, so the rehearsal allowlist and operator records are the
  source of this list.
- All old or unintended pending Bravo asset-deposit actions for the launch asset
  have been identified and cancelled. Do not reuse a rehearsal allocation action
  for launch.
- The current Bravo and Golf `actionTimeLock`, action expiration, and expected
  confirmation blocks have been read onchain.

Testers may keep their deposits. They do not need to withdraw. They should claim
any rehearsal RIPE they intend to keep before the preparation action executes.
RIPE already paid is not clawed back, and any accepted residual RIPE expense is
outside the point reset.

### Stale action cancellation

For each unintended pending action, call the cancellation function on the board
that owns it:

```text
SwitchboardBravo.cancelPendingAction(bravoActionId)
SwitchboardGolf.cancelPendingAction(golfActionId)
```

Do not execute a stale Bravo voter-allocation action. If it executes while the
clock is still `0`, it changes the ordinary voter configuration without writing
the launch block `B`.

## Phase 1: pre-announce — initiate preparation

Use one atomic Safe batch for all launch assets where practical.

### Call 1 — initiate rehearsal cleanup and promotional collection

Call Bravo once per asset:

```text
SwitchboardBravo.preparePromotionalCollection(
    asset,
    rewardVaultId,
    testers,
)
```

This call immediately disables deposits and initiates the timelocked preparation
action. It does not yet reset points or change the clock. Record the returned
Bravo action ID and the `confirmationBlock` from `PendingPromotionalCollection`.

### Call 2 — initiate the production whitelist change

If the current whitelist is not already the intended public whitelist, call Golf
once per asset:

```text
SwitchboardGolf.setWhitelistForAsset(
    asset,
    publicWhitelist,
    address(0),
)
```

This only initiates the timelocked Golf action; it does not open access yet.
Record the returned Golf action ID and the `confirmationBlock` from
`PendingAssetWhitelistChange`.

The preferred Safe ordering is Bravo preparation initiation first, then Golf
whitelist initiation. Deposits are closed by the first call before any later
launch work proceeds.

## Phase 2: private timelock window

Do not announce that deposits are open during this phase. Deposits must remain
disabled.

While waiting:

- Testers may claim rehearsal RIPE.
- Testers may remain deposited or withdraw.
- Confirm the Bravo and Golf actions have not expired.
- Confirm no one has re-enabled deposits through Charlie.
- Confirm the tester list still covers every address with residual rehearsal
  `balancePoints`.
- Prepare and review the complete production values for the final
  `setAssetDepositParams` call. It writes the vault array and all deposit limits,
  not only the voter allocation.

Do not proceed until every action needed in the announcement batch is
confirmable. If the Golf whitelist is already correct, only the Bravo preparation
action needs to mature.

## Phase 3: announce — prepare, open deposits, and start the countdown

Use one atomic Safe batch. The call order is mandatory.

### Call 1 — execute Bravo preparation

```text
SwitchboardBravo.executePendingAction(prepareActionId)
```

This execution atomically:

- checkpoints and sets voter allocation to `0` when necessary;
- resets the listed testers' balance-point tickets;
- resets the asset's staker, voter, and gen point buckets;
- requires aggregate `balancePoints` and all three RIPE point buckets to be `0`;
- writes `accrualStartBlock = max_value(uint256)`;
- removes the asset's gen-funding USD weight from global accounting;
- requires asset `lastUsdValue == 0`; and
- leaves deposits disabled.

Existing `lastBalance` may remain nonzero. If an unlisted user retains rehearsal
balance points, the aggregate clean check fails and this entire execution reverts.

### Call 2 — execute the production whitelist

Skip this call if the production whitelist was already installed.

```text
SwitchboardGolf.executePendingAction(whitelistActionId)
```

This installs the production whitelist. It must happen after Bravo preparation.

### Call 3 — open deposits

```text
SwitchboardCharlie.setCanDepositAsset(
    asset,
    True,
    address(0),
)
```

This opens deposits only after the clock is frozen at `max` and the public
whitelist is installed.

### Call 4 — initiate the production voter allocation

Call Bravo with the complete production deposit configuration:

```text
SwitchboardBravo.setAssetDepositParams(
    asset,
    productionVaultIds,
    0,                         # stakersPointsAlloc
    productionVoterAllocation,
    productionPerUserLimit,
    productionGlobalLimit,
    productionMinBalance,
    address(0),
)
```

This call only queues the action. It does not change voter allocation and does
not start rewards. Record its action ID, confirmation block, and expiration from
`PendingAssetDepositParamsChange` and the board's pending-action getters.

Do not initiate this action before the preparation execution. Do not use an older
rehearsal action as the launch action.

### Announcement-batch postconditions

Verify every condition onchain before making the public announcement:

- `accrualStartBlock(asset, vaultId) == max_value(uint256)`.
- Voter allocation is `0`.
- Staker allocation is `0`.
- LTV is `0`.
- `canDeposit == True`.
- The production whitelist is installed.
- Asset `balancePoints == 0`.
- Asset `ripeStakerPoints == 0`.
- Asset `ripeVotePoints == 0`.
- Asset `ripeGenPoints == 0`.
- Asset `lastUsdValue == 0`.
- `lastBalance` may be nonzero.
- The new Bravo voter action contains exactly the reviewed production vault IDs,
  allocation, and deposit limits.
- The voter action will be confirmable before the announced reward-start target
  and will not have expired by that target.

Only after these checks pass should the public countdown begin. The public
message should state:

> Deposits are open. No balance points or RIPE rewards accrue during the
> collection period. Rewards are expected to begin at or after the announced
> target. The actual start is the onchain execution block.

## Phase 4: post-announce collection window

During the countdown:

- Public users may deposit according to the production whitelist and limits.
- Deposits update `lastBalance`, but the `max` clock prevents balance, staker,
  voter, and gen points from accruing.
- Do not execute the pending Bravo voter action early.
- Do not replace MissionControl or Ledger.
- Monitor the pending action's confirmation block and expiration.
- Monitor that the clock remains `max`, voter remains `0`, deposits remain open,
  and `lastUsdValue` and all four point buckets remain `0` after collection
  activity.

The countdown is not enforced onchain. A governor can execute a confirmable
action early, so Safe policy and transaction review are the launch guard.

If Bravo's configured delay is longer than the intended countdown, announce a
longer countdown.

**Alternate timing path.** Execute preparation and queue the voter action in an
earlier private Safe transaction while deposits remain disabled, then open
deposits and announce only when the action's remaining delay fits the public
window. This is not a second reading of Phase 3: never queue the voter action
before preparation has executed, and never promise a start before the action
can be confirmed.

## Phase 5: pre-reward-launch checks

Immediately before creating or signing the launch Safe transaction, verify for
every asset:

- The public countdown has completed.
- The intended Bravo voter action is confirmable and not expired.
- The pending action still contains the exact approved production configuration.
- No stale or competing Bravo asset-deposit action is intended for execution.
- MissionControl is still the same contract captured by the pending action.
- Clock is still `max`.
- Voter and staker allocations are still `0`.
- LTV is still `0`.
- Deposits and the intended public whitelist are still enabled.
- The four asset point buckets and asset `lastUsdValue` remain `0`.
- Asset `lastBalance != 0`.

The final condition is mandatory. If testers all withdrew and nobody deposited
during collection, activation reverts until a deposit produces a nonzero
`lastBalance`.

Anyone deposited at the activation block earns beginning at `B`, including any
tester who remained deposited.

## Phase 6: reward launch

Execute the intended Bravo voter action:

```text
SwitchboardBravo.executePendingAction(voterActionId)
```

The execution checkpoints the frozen row, requires a nonzero `lastBalance`,
writes `accrualStartBlock = block.number`, and installs the nonzero production
voter allocation. That transaction's block is `B`.

For a multi-asset launch, place every final Bravo execution in the same atomic
Safe transaction if the reviewed gas envelope permits it. Successful calls in
the same transaction share the same `B`. If assets are launched in separate
transactions or blocks, they have different start blocks.

There is no disarm after this execution. This is the production reward launch.

## Phase 7: post-launch verification and communication

Immediately after the Safe transaction confirms, record and verify:

- Safe transaction hash.
- Actual launch block `B` for every asset.
- `accrualStartBlock(asset, vaultId) == B`.
- Production voter allocation is nonzero and equals the approved value.
- Staker allocation remains `0`.
- Deposits and production whitelist remain enabled.
- The emitted `AssetDepositParamsSet` values match the approved production
  configuration.
- A later-block checkpoint or representative deposit position begins accruing
  from `B`, with no collection-period catch-up.

Publish the actual transaction hash and block `B`. If execution occurred later
than the announced target, state the actual later start; do not describe rewards
as having started retroactively.

## Failure and abort handling

### Before Bravo preparation executes

- Cancel the Bravo preparation action with
  `SwitchboardBravo.cancelPendingAction(prepareActionId)`.
- Cancel any pending Golf whitelist action with
  `SwitchboardGolf.cancelPendingAction(whitelistActionId)`.
- Cancellation or expiry does not reopen deposits. If returning to ordinary
  rehearsal, governance must explicitly call
  `SwitchboardCharlie.setCanDepositAsset(asset, True, address(0))` after verifying
  that doing so is intended and safe.

### Bravo preparation execution reverts

The execution is atomic: voter, point resets, clock changes, and checkpoints
revert together. Deposits remain disabled from initiation.

- If the tester census was incomplete, cancel and re-initiate with the corrected
  list, or clear the omitted tickets through an independently reviewed existing
  reset action before retrying.
- Do not open the public whitelist or deposits while the clock is still `0`.

### After preparation succeeds but before reward launch

The clock remains `max`; points stay off.

- If the voter action expires, initiate a new action with the exact approved
  production configuration.
- If launch must be delayed, do not execute the voter action. Publicly communicate
  the delay. Charlie may close deposits if required, but that does not disarm the
  clock.
- There is no supported transition from `max` back to `0`.

### After reward launch

There is no promotional disarm or rewind after `B`. Use separately reviewed
emergency controls if another protocol incident requires pausing user actions;
do not attempt to reset the launch clock or voter allocation through this
runbook.

## Permanent operational restrictions

- Never confirm 223 Bravo before Golf is a live Switchboard.
- Never confirm 223 Lootbox against the pre-223 MissionControl, or leave the
  pre-223 Lootbox against the 223 MissionControl.
- Never execute Golf whitelist or Charlie deposit-opening calls before the Bravo
  preparation execution.
- Never execute an old rehearsal voter-allocation action as the launch action.
- Never execute the final voter action before the announced countdown ends.
- Do not replace MissionControl after any row reaches `max` or `B`. Defaults and
  `prepare_defaults` do not carry `accrualStartBlock`; replacement would silently
  lose the launch state.
- Do not replace Ledger as part of this sequence.
- Do not assume a 24-hour countdown matches the Bravo timelock. Read the actual
  pending action confirmation and expiration blocks.
- Do not assert global `lastUsdValue == 0`; it may legitimately contain funding
  weight from other assets. The launch requirement is that this asset's
  `lastUsdValue == 0`.
