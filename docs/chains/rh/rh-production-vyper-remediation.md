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
HumanResources, Switchboard, PriceDesk, VaultBook, and RipeHq. BlueChip is not
deployed in this candidate and must not be fetched or finalized. The Safe
handoff remains last.

## Ledger and action-block source

Robinhood selects the ArbSys precompile at exact address
`0x0000000000000000000000000000000000000064`. Ledger stores that immutable
source without probing it in the constructor. Registration is fail-closed and
separately proves both exact immutable readback and a live, exactly 32-byte
`arbBlockNumber()` result that decodes to a nonzero action block. Missing RPC,
wrong source, malformed data, or a zero result blocks registration. This is a
lazy deployment-time validation, not a constructor-time health call.

## Stability stale-price recovery

Dormant activation is exactly `$0.10`; active retention is exactly `$0.05`.
The hysteresis is deliberate. No aggregate dormant-pair or dormant-value
counter is added, so many individually sub-threshold balances may accumulate
material aggregate exposure outside iterable NAV. Monitoring must therefore
track token custody and pair liabilities offchain.

### Code-size, storage, and gas disclosure

The required recovery path did not fit beneath EIP-170 with the prior module
immutables. As a bounded local code-size optimization,
`StabVault.greenToken` and `StabVault.savingsGreen` are now two private storage
slots rather than `immutable(address)` values. The module constructor writes
them once from the RipeHq registry-derived addresses and no setter exists, so
the values remain deployment-initialized and externally nonmutable. This is
nevertheless a real storage-layout and gas change: the layout gains two slots,
the deployed immutable section loses two addresses, and valuation paths that
read these cached identities incur storage reads. The external ABI and selected
addresses do not change. The final StabilityPool deployed runtime is `24,575`
bytes, leaving `1` byte of EIP-170 headroom.

The mock oracle used by tests also changed semantics: `setPrice(asset, 0)` now
means a configured feed reporting zero, while `disablePriceFeed(asset)` removes
feed registration. This distinction lets tests cover strict configured-zero
failure separately from the no-feed routing fallback; it is not a production
oracle change.

If an active claim asset becomes unpriced:

1. Pause StabilityPool before maintenance.
2. Call the bounded prune path for each affected Stability-asset/claim-asset
   pair. A zero price marks that exact pair as a no-price quarantine,
   increments the global quarantine count, and removes it from active NAV
   without changing custody, claimable balance, aggregate liability, or user
   shares.
3. Repair or reconfigure the oracle through separately authorized governance.
4. While still paused, reactivate each marked pair only after its price is
   nonzero and cumulative value meets `$0.10`. Reactivation clears the pair
   marker and decrements the count exactly once.
   While any quarantine remains, slots released by quarantine are reserved for
   marked pairs; ordinary dormant pairs cannot consume them and strand unpause.
5. Verify custody, liabilities, shares, exact pair markers, active membership,
   and `noPriceQuarantineCount == 0`.
6. Only then may any Switchboard unpause path succeed.

Recovery depends on operational oracle repair and keeper/governance execution;
pause and quarantine preserve accounting but do not restore the feed. A
mispriced nonzero feed is outside this zero-price recovery. Stability positions
remain excluded from borrowing power, but otherwise eligible positions remain
phase-2 liquidatable.

`getClaimAssetState(stabAsset, claimAsset)` returns `0` for absent, `1` for
dormant, `2` for active, and `3` for an exact no-price-quarantined pair. The
quarantined state is a new view result. Permissionless pruning outside pause
continues to skip unpriced active entries and process later batch items; only a
paused pool may turn an unpriced active pair into state `3`.

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
