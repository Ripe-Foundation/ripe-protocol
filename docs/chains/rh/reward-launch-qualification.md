# Robinhood RIPE reward launch approved product-decision packet

> [!WARNING]
> **Superseded economics snapshot.** This packet records the earlier 1,000-RIPE
> decision and is retained as historical evidence. The selected Defaults source
> now contains a shared 1,000,000-RIPE reward bucket; see
> [`rh-production-vyper-remediation.md`](rh-production-vyper-remediation.md).
> Neither the old packet nor the current source grants deployment or activation
> authority.

## Verdict

The existing PR #66 reward values are the **owner-approved product
configuration** for initial launch. DP15 is bound to the concrete packet hash
and P-H04-399 is approved. B-REWARD-PROMOTION remains open for the operational
prerequisites listed below. Nothing in this packet authorizes deployment,
configuration, activation, RPC, governance, signing, operation, publication,
integration, or release.

The approved values remain unchanged in the two existing configuration
authorities: contracts/config/DefaultsRobinhood.vy and config/BluePrint.py. The
machine packet at config/robinhood-reward-launch-plan.json is derived evidence,
not a third value authority. Its SHA-256 identity is
7395a0bff4abd75e11f832fbd0dee2f6569244dafa2ba52604d3f5989662acec.
That hash binds the exact approved product-decision bytes; it grants no
lifecycle authority.

## Approved economics and accepted runway limits

The approved configuration has points enabled, 0.009 RIPE/block, a 10%
borrower and 90% staker allocation, zero voter and general-depositor
allocation, a 75% auto-stake ratio for an explicit non-staking claim, a 33%
lock-duration ratio, 1 RIPE/$ for Stability claims, and one shared initial
1,000 RIPE reward budget. Stock rewards remain disabled.

At five blocks per minute, emission alone is 64.8 RIPE/day: 6.48 to the
borrower bucket and 58.32 to the staker bucket. The continuous emission-only
runway is 15.432098765... days. Integer block accounting first caps the budget
on block increment 111,112, or 1,333,344 seconds:
**15 days, 10 hours, 22 minutes, 24 seconds**.

That duration is only an emission-only maximum measured from the first
successful global Lootbox checkpoint. Stability claims draw from the same
budget and can theoretically exhaust it immediately, so the shared-budget
minimum runway is **zero**. A 30-day emission-only target requires at least
1,944 RIPE, or a rate no higher than approximately 0.00462963 RIPE/block,
before reserving anything for Stability claims. The owner accepts the shared
budget, the approximately 15.432-day emission-only runway, the possibility
that Stability claims shorten it, and the theoretical zero minimum. No
dedicated Stability reserve or separate budget is selected; no Stability
redesign or launch disablement is selected. Those risks are accepted as part
of the launch product configuration.

## Exact lifecycle and checkpoint behavior

Configuration occurs during deployment; deployment block is not emission
start. When global Lootbox lastUpdate is zero, the first successful
updateRipeRewards sets lastUpdate and distributes zero. Accrual begins only
after that checkpoint. A later update recognizes all elapsed blocks at the
reward rate current when that later update executes.

Lootbox pause blocks claims and Underscore only. Deposit, borrow, and RIPE
clocks (`updateDepositPoints`, `updateBorrowPoints`, `updateRipeRewards`,
`reset*`) keep running. Pause does not zero `ripePerBlock` and does not freeze
accrual. `SwitchboardAlpha.setRewardsPointsEnabled` does not exist; stored
`arePointsEnabled` is inert. If `ripePerBlock` is still nonzero, the next
clock update distributes the elapsed interval at that rate even while Lootbox
is paused. A safe transition therefore confirms `setRipePerBlock(0)` (and the
Stability rate zero) before treating emissions as contained. Then an
explicitly bound registered RIPE contract caller may run a zero-rate
checkpoint.

The Lootbox emission path and Stability claim path both decrement Ledger's
ripeAvailForRewards. Budget exhaustion produces zero new emission and zero new
Stability reward, but does not delete already allocated Lootbox buckets or
stored points; qualifying old buckets remain claimable while their claim gates
and mint capability permit.

## Emergency containment runbook pending operational acceptance

No authority identity is invented here. “Governance” and “qualified lite
signer” mean the identities actually bound and independently verified for the
deployment. Lite qualification must already exist; this procedure does not
silently create it.

Execute and verify in this order:

1. Call SwitchboardCharlie.pause(Lootbox, true) first. Governance or an already
   qualified lite signer may pause immediately. Only governance may unpause.
   Verify Lootbox is paused. This stops claims and Underscore only; clocks
   still run.
2. Immediately call SwitchboardAlpha.setCanClaimLoot(false). Verify
   canClaimLoot=false.
3. Immediately call SwitchboardAlpha.setCanClaimInStabPool(false). Verify the
   separate Stability claim gate is false.
4. Governance calls SwitchboardAlpha.setRipePerBlock(0). This is the emission
   stop. Record the returned action ID and the emitted/read confirmation block.
   After post-setup initialization the confirmation delay must be at least the
   Robinhood minimum of **600 blocks**.
5. Governance reads the current auto-stake ratio and duration ratio, then calls
   SwitchboardAlpha.setAutoStakeParams(currentRatio, currentDurationRatio, 0).
   Record this distinct action ID and confirmation block. The two ratios must be
   passed unchanged; only the Stability rate is zeroed. This action also has the
   exact 600-block minimum.
6. Do not execute either action early. Keep Lootbox paused and both claim gates
   disabled until both recorded confirmation blocks. Do not call
   `setRewardsPointsEnabled`; that function is gone.
7. Governance executes both pending actions before expiration. Verify each
   pending action is cleared, ripePerBlock=0,
   stabPoolRipePerDollarClaimed=0, and both auto-stake ratios are unchanged.
   Keep Lootbox paused after this verification.
8. RipeHq.setMintingEnabled(false) is a last-resort, governance-only, immediate
   global breaker. It disables GREEN and RIPE mint permission across the
   system. It is not a routine reward step and does not erase accrued reward
   accounting.

The containment end state is: Lootbox paused (claims blocked, clocks still
live); both claim gates off; both reward rates confirmed zero.

## Re-enable conditions

There is no automatic rollback. Before any re-enable, the owner must accept the
incident resolution; revalidate the approved configuration if its bytes
change; bind emergency identities; accept monitoring owners, thresholds, alert
routes, and zero-budget response; and record fresh action IDs and confirmation
blocks for any nonzero restart.

While both claim gates remain disabled, keep Lootbox paused through any restart
timelock. At confirmed zero, governance may unpause Lootbox and an explicitly
bound registered RIPE contract caller must perform a zero-rate global
checkpoint. Verify zero distribution and unchanged budget. Immediately
before executing a new nonzero rate, perform the final zero-rate global
checkpoint so the new rate cannot apply retroactively. Do not re-enable
Lootbox or Stability claims until the owner accepts the restart. There is no
points-disable flag to flip.

## Operational prerequisites still open

- owner-approved reward-configuration checkpoint procedure;
- owner-approved zero-rate and claim-gate re-enable procedure;
- exact governance identity, any qualified lite-signer identity, and the
  registered RIPE checkpoint-caller identity;
- operational acceptance of the emergency runbook;
- monitoring owners, thresholds, alert routes, and zero-budget response;
- the H-05 deterministic plan, H-06 operator binding, H-08 post-deployment
  assertions, and H-09 fork qualification;
- testnet rehearsal; and
- release authorization.

Passing focused tests or approving the product values does not close any item
above. DP15 and P-H04-399 are approved, while B-REWARD-PROMOTION remains open
and narrowed to these operational prerequisites.
