# Robinhood production Vyper remediation — current-state correction

**Effective 2026-08-06.** This document is the current-state correction for
the implementation governed by
`rh-production-vyper-remediation-implementation-plan.md`. Earlier evidence is
preserved as historical evidence; where it conflicts with this document and
the final source, it is superseded. Nothing here authorizes commit, push,
deployment, activation, RPC use, signing, integration, or release.

## Defaults and deployment topology

`contracts/config/DefaultsRobinhood.vy` is the selected value authority. Its
constructor has exactly seven arguments: contributor template, training
wheels, RIPE, GREEN, sGREEN, USDG, and WETH. Steakhouse is absent from the
constructor, active assets, yield tokens, and priority liquidation. The
priority price sources are `[1, 2]`.

The literal current values include `maxBorrowPerInterval = 25e18`,
`ripeAvailForRewards = 1_000_000e18`, `ripeAvailForHr = 0`,
`ripeAvailForBonds = 1_000_000e18`, bond `amountPerEpoch = 100e6`,
`maxRipePerUnit = 50e18`, `restartDelayBlocks = 600`, and WETH
`minDepositBalance = 5e14`. At `0.009 RIPE/block` and five blocks per minute,
emission alone is `64.8 RIPE/day`; the continuous emission-only runway is
approximately `15,432.10 days`. Stability rewards draw from the same bucket,
so aggregate minimum runway remains zero. The source matrix does not itself
authorize reward activation.

## Setup invariants

Fresh MissionControl state initializes `coreRipeGovVaultId = 2`,
`preferredStabVaultId = 1`, and `isStabVaultId(1) = true`. MissionControl is
deployed before those vaults, so its constructor sets numeric policy only. The
post-vault migration must prove VaultBook ID 1 is an unpaused StabilityPool,
ID 2 is RipeGov, and all three MissionControl reads agree.

Setup-time action and registry timelocks may begin at zero. Before the Safe
handoff, the migration must finalize and read back the approved nonzero values
for Alpha, Bravo, Charlie, Delta, Echo, ChainlinkPrices, CurvePrices,
HumanResources, Switchboard, PriceDesk, VaultBook, and RipeHq. BlueChipYield is
not deployed in this candidate and must not be fetched or finalized. The Safe
handoff remains last.

## Ledger and action-block source

Robinhood selects the ArbSys precompile at exact address
`0x0000000000000000000000000000000000000064`. Ledger stores that immutable
source without probing it in the constructor. Registration is fail-closed and
separately proves both exact immutable readback and a live, exactly 32-byte
`arbBlockNumber()` result that decodes to a nonzero action block. Missing RPC,
wrong source, malformed data, or a zero result blocks registration. This is a
lazy deployment-time validation, not a constructor-time health call.

## Stability unavailable-price behavior

**Owner correction effective 2026-08-07.** This section supersedes the paused
quarantine/reactivation design selected by D-02 in the implementation plan.
The final contract deliberately has no no-price pair marker, quarantine count,
special claim-asset state, capacity reservation, or oracle-specific unpause
guard.

Dormant activation is exactly `$0.10`; active retention is exactly `$0.05`.
The hysteresis is deliberate. No aggregate dormant-pair or dormant-value
counter is added, so many individually sub-threshold balances may accumulate
material aggregate exposure outside iterable NAV. Monitoring must therefore
track token custody and pair liabilities offchain.

When an active claim-asset balance has no nonzero USD price, valuation requests
the non-reverting PriceDesk result and skips that asset when the result is zero.
The collateral remains in custody and stays claimable, but contributes zero to
the Stability asset's NAV until a nonzero price returns. NAV views, deposits,
withdrawals, and operations involving other priced claim assets therefore
remain live without an additional quarantine state machine. Claiming or
redeeming the unpriced asset itself still requires a usable price and cannot
complete until pricing returns.

This is an explicit liveness-over-accounting tradeoff. While claim collateral
is omitted from NAV, depositing users may receive shares without paying for its
eventual recovery and withdrawing users may exit without receiving its value.
Restoring the oracle can therefore redistribute the recovered value among the
shareholders present at that time. Monitoring should alert on every active
claim balance whose returned price is zero.

Permissionless pruning skips an unpriced active pair in either pause state and
continues processing later batch entries. It never removes or reclassifies the
pair, and preserves its active index, custody, pair liability, aggregate
liability, and user shares. Repairing or replacing the price feed restores NAV
and economic operations immediately; no activation call or persistent recovery
bookkeeping is required.

The standard Switchboard pause path has no oracle-specific unpause predicate.
`getClaimAssetState(stabAsset, claimAsset)` therefore has only the existing
states `0` absent, `1` dormant, and `2` active.

`StabVault.GREEN_TOKEN` and `StabVault.SAVINGS_GREEN` are again
constructor-bound immutables. Removing the quarantine state machine eliminates
the private storage slots and repeated storage reads introduced solely for its
EIP-170 optimization. The final StabilityPool deployed runtime is `24,371`
bytes, leaving `205` bytes of EIP-170 headroom.

The mock oracle used by tests distinguishes `setPrice(asset, 0)`, a configured
feed reporting zero, from `disablePriceFeed(asset)`, which removes feed
registration. Both cases exclude the active claim balance from NAV without
deactivating it, and a later nonzero price restores it to NAV automatically.
A mispriced nonzero feed remains outside this zero-price behavior. Stability
positions remain excluded from borrowing power, while otherwise eligible
positions remain phase-2 liquidatable.

## RipeGov and migration invariants

Overflow disable remains a no-update escape: it preserves stored points rather
than forcing the arithmetic that overflowed. A later full exit from one asset
must nevertheless clear that asset's stored points and subtract the exact
global/user totals without accruing new points, so disable cannot block asset
exit. A disabled sender already skips its own Boardroom callback. Its healthy
recipient would otherwise still call Boardroom and could strand the emergency
transfer, so both callbacks are suppressed for that transaction; the existing
public update path remains the recipient retry mechanism.

RipeGov migration first proves source Ledger participation, exports/imports an
exact zero-balance, zero-governance-data target position, proves the source
vault is empty, removes the source Ledger entry through the dedicated
Teller-only method, proves removal, and only then adds the target if absent.
Failure at any step rolls back the cross-contract transition. An already
registered, exact-zero target is accepted without duplication. A position
whose source Ledger entry was already removed cannot currently migrate; that
pre-cleaned-source liveness case remains an explicit residual rather than
bypassing the source-first position-count invariant.

SC-12 corrects early-release fee accounting by burning shares while retaining
the largest post-release share balance whose exact floored claim is no greater
than the fee-adjusted live target. The accepted integration invariant is
`claim(postShares) <= target < claim(postShares + 1)`; indivisible shares can
therefore produce more than one asset base unit of unavoidable fee granularity.
The fee remains inside the same asset pool. A remaining holder **address** is
required, so a genuine single-address holder cannot release early; common
beneficial ownership across multiple addresses is neither detectable nor
prevented, and a controller of both addresses can recapture redistributed
value.

Early release accrues through the release and preserves saved governance
points, while an equivalent ordinary partial withdrawal proportionally reduces
them. A 100%-fee release can leave nonzero points with zero shares. That record
does not accrue further and cannot migrate, but a later deposit reattaches the
points and a later complete withdrawal clears them. Active or future
governance-power consumers must treat that interim point stock as live. The
complete owner-facing policy and Base-candidate rollout consequence are in
[`smart-contract-changes/ripe-gov.md`](smart-contract-changes/ripe-gov.md).

## Special targets, price configuration, and CCIP

SwitchboardBravo validates every nonzero special vault ID before monotonic
classification. A proposed Stability ID must resolve through VaultBook to
nonzero contract code and satisfy the StabilityPool interface probes; a normal
vault, EOA, zero address, or partial-interface contract is rejected.

UniswapV2Prices confirmation merges only the four approved policy fields into
the latest live config. It preserves `lastSnapshot`, stored snapshot slots, and
the live cursor unless a smaller ring requires `nextIndex % newMaxNumSnapshots`.
The existing spot-price/manipulation weakness is intentionally deferred and
remains a strict expected failure; this remediation adds no TWAP, cumulative
prices, liquidity floor, or price-formula change.

`getCCIPAdmin()` remains the shared token implementation: before setup,
`ripeHq == 0` causes the external governance lookup to revert even though
`tempGov` is nonzero; after setup it returns only `RipeHq.governance()`. No
`tempGov` fallback is present.
