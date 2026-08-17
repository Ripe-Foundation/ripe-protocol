# PR #126 — Source Merge-Readiness Review

**PR:** [`Ripe-Foundation/ripe-protocol#126`](https://github.com/Ripe-Foundation/ripe-protocol/pull/126) (`rh-audit-remediation` → `rh`)

**Author context:** Independent source-merge review, 17 August 2026. Persisted here at Mick Hagen’s request. This memo is the merge-ability record for landing the remediation branch into `rh`. It is **not** a Base production-risk assessment, a deploy authorization, or a launch decision.

**Reviewed remediation head:** `5f3848c051655e6b9b7e439fb6db13348d87ade3`

**Reviewed `rh` base:** `36ee0db42482c3e7d6c43d045fc02655b90bebf4`

**Origin tips re-checked while writing this memo:** `origin/rh` is still `36ee0db`. `origin/rh-audit-remediation` has since moved one **docs-only** commit to `8ebb0e7b7fac72ab67f176c561e61127045e036d` (`docs: record remediations-to-RH merge-readiness review`, adding [`PR-126-RH-MERGE-READINESS.md`](PR-126-RH-MERGE-READINESS.md)). No contract change after `5f3848c`. This memo’s source-merge verdict is bound to the reviewed contract head `5f3848c`; the current remote tip is that head plus the later docs commit.

**GitHub state at review:** draft; `mergeable_state: blocked`; zero reviews. At `5f3848c`: 260 files, `+64,262 / −20,908`, 71 merged component PRs, 172 commits ahead of `rh`. At the current remote tip: 173 commits ahead, 0 the other way.

**Classification:** source-integration verdict only. Fast-forwarding this branch into `rh` does **not** deploy, rebind, seed, activate, or make remediations live on-chain.

## Document status

This memo **supersedes** [`PR-126-SMART-CONTRACT-FINDINGS.md`](PR-126-SMART-CONTRACT-FINDINGS.md) for merge-readiness.

That findings document is **stale**. It is bound to `81d6146ccb6468e53ab14d723213cf28a650f121`, predates PR #143 and the later remediation wave, and still says **REQUEST CHANGES**. Do not use it as the merge verdict for the current head.

Companion records that remain useful, but are not this verdict:

- [`PR-126-RH-MERGE-READINESS.md`](PR-126-RH-MERGE-READINESS.md) — sibling merge-readiness write-up already on the branch at `8ebb0e7`; same wave, different filename
- [`PR-126-DERIVED-FOLLOW-UP-REGISTER.md`](PR-126-DERIVED-FOLLOW-UP-REGISTER.md) — derived residuals, activation gates, and live-config follow-ups
- [`REMEDIATION-GUIDE.md`](REMEDIATION-GUIDE.md) — Auditor B finding map (historical; B-AUD-007 / SC-03 remains operational)
- RH decision register entries RH-D034, RH-D036, RH-D038, RH-D043

## Verdict

**YES — fast-forward `origin/rh-audit-remediation` into `origin/rh`.**

Source-merge only. Not deploy, activate, or launch.

The merge is a clean fast-forward: `origin/rh` is a strict ancestor of remediations (172 commits ahead at the reviewed head; 173 at the current docs-only tip; 0 the other way). Exact-head CI on `5f3848c` is green. The High loss-of-funds bugs this wave was supposed to close in contract code (SC-01, SC-02) are closed. The remaining High-shaped item (SC-03 / sGREEN first-depositor) was never a contract fix on this branch.

Quality is high. It is not perfect, and it is not production-activation ready.

Use **`origin/rh-audit-remediation`**. Fast-forward the current origin tip (`8ebb0e7`, which is `5f3848c` plus one docs commit) or the reviewed contract head (`5f3848c`) — not a stale local `rh-audit-remediation` pointer (historically `e9b4b48`). If merging a tip other than the exact-head CI SHA, re-run `rh-pr-gate` on that tip.

## What was checked

This was not a rubber-stamp of the PR write-up. The reviewer read the current AuctionHouse, CreditEngine, Deleverage, TellerUtils, PriceDesk, RipeGov, Endaoment, StabVault, and sGREEN paths and matched them to the regressions that claim to prove the invariants. Further source passes on liquidation/auth, pricing/Endaoment, High SC-01/02/03, and Medium findings reached the same merge conclusion. The Medium pass also executed 13 focused regressions, all green.

GitHub CI on this exact head is green (PR run [32055765249](https://github.com/Ripe-Foundation/ripe-protocol/actions/runs/32055765249) and push run [32055761077](https://github.com/Ripe-Foundation/ripe-protocol/actions/runs/32055761077): lean shards, snapshot-gas, solidity, rh-pr-gate). PR #126 is still a draft with zero reviews and `mergeable_state: blocked`.

Status key used below:

| Status | Meaning |
| --- | --- |
| **FIXED** | Contract change is in the reviewed source and the intended invariant is closed |
| **ACCEPTED** | Owner-accepted residual or trust/policy decision; not a missed fix |
| **RESIDUAL** | Remaining gap that does not block this source merge |
| **OPERATIONAL** | Deploy, seed, config, or activation work; not a contract edit on this PR |

## High findings

| ID | Area | Status | What the current code does |
| --- | --- | --- | --- |
| SC-01 | Stability Pool can burn GREEN that reduces no debt | **FIXED** | Stab swap is sized from remaining creditable repayment before collateral moves. Settlement asserts `repayValueIn <= debt` after unpaid fees. `test_depleted_collateral_burn_is_capped_by_creditable_debt` asserts supply drop == debt reduction. |
| SC-02 | Auction buyer seizes collateral far beyond live debt | **FIXED** | Each purchase caps `greenAmount` at `getUserDebtAmount` (includes interest) before transfer. Tests assert spend and discounted collateral stay at live debt. |
| SC-03 | Unseeded sGREEN first-depositor donation | **OPERATIONAL** | Not a contract fix. Constructor now requires zero initial supply (SC-27). Conversion math is still raw 1:1 on empty supply with no virtual/dead shares. Pause/blacklist on exits is separate (B-AUD-017). No sGREEN donation-attack regression exists. An unseeded deploy remains High. Original Auditor B disposition (B-AUD-007): no contract remediation required; seed/burn is a deploy action. |

High-path sources: AuctionHouse liquidation/stab/buy paths; CreditEngine `getUserDebtAmount`; `Erc4626Token._amountToShares`; SavingsGreen constructor; `tests/core/auctionHouse/test_ah_liq_sgreen.py` and `test_ah_auctions.py`.

## Medium and low ledger

Status is from current source at `5f3848c`, not the historical REQUEST CHANGES memo at `81d6146`.

| ID | Area | Status | Evidence |
| --- | --- | --- | --- |
| SC-04 / DER-03 | SharesVault indexed exits | **OPERATIONAL** (activation gate) | `DECIMAL_OFFSET` plus ±2 wei delivery tolerance. Real Comet multi-holder full-exit can still be rounding-blocked; current assets were deposit-disabled with zero shares. |
| SC-05 | Snapshot ring resize | **FIXED** | Capacity change clears the ring, seeds a fresh observation, and resets `nextIndex`. Same pattern in BlueChip, Undy, and Curve. |
| SC-06 | PriceDesk unbounded gas | **FIXED** | `raw_call` sites use `PRICE_SOURCE_*_GAS` stipends. |
| SC-07 | Deleverage stale-debt reentry | **FIXED** + **RESIDUAL** | Deleverage routes share `@nonreentrant`. Settlement rereads debt and reverts if the amount changed. The overwrite path is closed. Some Teller deleverage helpers still omit the guard. |
| SC-08 | Repeatable no-progress fees | **FIXED** | Fees charge only when not already `inLiquidation`. Inert first pass zeroes fees. Retries are fee-free by policy (issue #160). |
| SC-09 | Stab fail-soft in broad Deleverage | **FIXED** | Cohort probe returns 0 on pause/price/custody miss. Phase 2 skips stab IDs. Broad sweep uses the same fail-soft iterator. |
| SC-10 | Account-wide quarantine | **ACCEPTED** | Owner kept whole-account fail-closed when any positive-LTV asset is unpriced. Not a missed fix. |
| SC-11 | Repay blocked by any oracle | **FIXED** | STANDARD repay uses `shouldRaise=False` and preserves terms when a price is unavailable. Debt still burns. |
| SC-12 | RipeGov exit-fee recapture | **FIXED** + **ACCEPTED** residual | Burns shares so remaining claim matches the fee-adjusted claim. Requires another holder. Same-owner split-address recapture is accepted policy. |
| SC-13 | Underscore global authority | **FIXED** | `isUnderscoreOwnerOrLego` now requires `doesUndyLegoHaveAccess(user, caller)`. Deleverage no longer grants registry-only cross-user trust. Issue #161 remains an activation gate. |
| SC-14 | Sender reward checkpoint | **FIXED** | AuctionHouse, CreditEngine, and Deleverage checkpoint the sender after collateral movement. |
| SC-15 | Vault-ID repoint brick | **FIXED** | CreditEngine skips `numUserAssets == 0` instead of `range(1, 0)`. |
| SC-16 | Curve danger reset | **FIXED** | PR #157; duration-weighted reference state. RH-D043 accepts ancestor `block.number` semantics. |
| SC-17 | Snapshot weighting / zero throttle | **FIXED** + **ACCEPTED** residual | Zero PPS no longer disarms the upside throttle. Observation-interval TWAP (not supply-weighted) is retained under RH-D034. |
| SC-18 | Partner mint on nominal amount | **FIXED** | Endaoment measures EndaomentFunds inflow and values only the received amount. |
| SC-19 | Stabilizer over-withdraw | **FIXED** + **RESIDUAL** | Quotes LP via `calc_token_amount`, then binary-searches the largest executable GREEN. Real-pool proof passed at pinned Base 34,471,929. Fork proof is not in default CI. |
| SC-20 | Looser stale bound wins | **FIXED** | Chainlink/Pyth/Stork/RedStone use `min(nonzero caller, nonzero feed)`. BlueChip/Undy still ignore caller stale time (DER-T03). |
| SC-21 | Future Pyth/Stork timestamps | **FIXED** | `publishTime > block.timestamp` returns 0 instead of underflowing. |
| SC-22 | Contradictory PriceDesk responses | **FIXED** | Nonzero price with `hasFeed=false` is malformed. Snapshot success is no longer `resultWord <= 1`. |
| SC-23 | Unbounded lastSnapshot fallback | **FIXED** | BlueChip `lastSnapshot` is age-checked against `staleTime` before use. |
| SC-24 | Dust funds rewards, earns 0 | **FIXED** | PR #169 reward-dust funding correction. |
| SC-25 | Price-source enum brick | **FIXED** | PR #169 bounds registration/enumeration. |
| SC-26 | Dust `lowestLtv` unwind | **FIXED** | `lowestLtv` ignores zero-capacity dust; withdrawn-to-zero still sets the conservative floor. |
| SC-27 | Nonzero sGREEN init supply | **FIXED** | `assert _initialSupply == 0`. |
| SC-28 | wsuper hardcoded fallbacks | **RESIDUAL** (dormant / non-RH) | `MCBETH=1` and `VVV=$2.40` are still in `wsuperOETHbPrices.vy`. Do not enable that integration. |
| SC-29 | Disabled VaultBook recovery | **FIXED** | PR #164. |
| SC-30 | Max discount unattainable | **FIXED** | Duration-1 auctions use `maxDiscount`; longer windows reach it on the last purchasable block. |
| DER-01 | Teller housekeeping | **ACCEPTED** | Owner accepted: Ripe contracts are trusted. Housekeeping by a registered department/vault/switchboard on any user is intended. No Teller auth change. |

## Holistic system

RH still does what it is supposed to do, with more conservative fail-closed edges. Deposit, borrow, repay, liquidation, auction, deleverage, rewards, and vault exit still compose. The behavior changes are intentional:

| Flow | Still works | What changed |
| --- | --- | --- |
| Repay | Yes | No longer reverts because an unrelated collateral oracle is down. |
| Liquidation / SP | Yes | GREEN burn cannot exceed creditable debt. First inert pass freezes without fees; retries are fee-free. |
| Fungible auctions | Yes | Buyer cannot take collateral beyond live debt plus the discount math on that cap. |
| Deleverage | Yes | Reentry cannot publish stale debt. Unhealthy stab cohorts skip; ordinary collateral still runs. |
| Underscore | Safe while disabled | A registered Lego can no longer act for arbitrary users. Do not turn the registry on until #161 is deployed and verified. |
| RipeGov early exit | Yes, multi-holder | Sole holder can no longer self-recapture the fee. That is the fix. |
| sGREEN | Unsafe if unseeded | Pause/blacklist and zero init supply are in. The empty-vault donation attack is not. |

## Residuals that are not source-merge blockers

| Item | Class | Why it can wait for `rh` |
| --- | --- | --- |
| SC-03 / B-AUD-007 | Operational High residual | Seed/burn is a deploy action, not this PR. |
| DER-01 Teller housekeeping | Owner-accepted trust | No Teller edit. |
| #153 CreditEngine repay bound | Defense in depth | AuctionHouse already caps before transfer. CreditEngine still refunds excess if a future caller overpays. |
| DER-T01 nested BlueChip gas | Activation blocker | Direct 9-asset / 3-source envelope qualified. Nested composition can exhaust the 250k stipend. Do not enable that topology. |
| DER-02 / DER-03 | Accepted / enablement | Stab dormant dust and Comet full-exit rounding are documented and tested, including a strict xfail for DV-15. |
| #161 / #160 / live config | Activation / ops | Underscore, fee-free retry monitor, PriceDesk timelock, stock inventory, per-feed stale times. |
| PR #156 Instant Bond | Separate `rh` feature | Intentionally outside this wave. It will need a rebase after this merge. |
| SC-07 Teller helper guards | Residual | Overwrite path is closed; some Teller deleverage helpers still omit `@nonreentrant`. |
| SC-12 split-address recapture | Accepted residual | Same-owner split-address fee recapture remains policy. |
| SC-17 TWAP timing | Accepted residual | Observation-interval TWAP retained (RH-D034). |
| SC-19 fork proof | Residual | Code-fixed; `fork_qualification` is not in default CI. |
| SC-28 wsuper fallbacks | Dormant / non-RH | Still in source. Do not enable. |
| SC-04 / DER-03 | Activation gate | Indexed SharesVault / Comet full-exit rounding. |

## EIP-170 runtime room

From `tests/test_vault_pointer_runtime_sizes.py`. EIP-170 is 24,576 bytes. CI pins these exact sizes. Tight room is a constraint on the *next* change, not a merge blocker.

| Contract | Bytes | Room |
| --- | --- | --- |
| AuctionHouse | 24,568 | 8 |
| Teller | 24,556 | 20 |
| SwitchboardAlpha | 24,506 | 70 |
| Lootbox | 24,444 | 132 |
| Deleverage | 24,424 | 152 |
| CreditEngine | 24,382 | 194 |

AuctionHouse has 8 bytes of deploy room, so the next AH change will be painful. Default CI does not run `fork_qualification`.

## Process gates before merge

| Gate | State | Action |
| --- | --- | --- |
| Git topology | `rh`..remediation was 172 / 0 at `5f3848c`; 173 / 0 at current origin tip `8ebb0e7` | Fast-forward only. Use `origin/rh-audit-remediation`, not a stale local branch. |
| Exact-head CI | Green | PR run 32055765249 and push run 32055761077. |
| PR #126 | Draft, blocked, 0 reviews | Undraft after the residual list is accepted. GitHub will not merge a draft. GitHub approval is still required. |
| Component PRs | None open into remediation | Aggregate is complete. |
| Instant Bond #156 | Open draft into `rh` ([PR #156](https://github.com/Ripe-Foundation/ripe-protocol/pull/156)) | Rebase after this lands. Do not mix it into this merge. |

Recommended next process step: undraft PR #126, approve it, and fast-forward `origin/rh-audit-remediation` into `origin/rh`. Keep the PR description’s activation list attached to `rh` after merge so nobody reads a green `rh` as “ready to enable Underscore, nested BlueChip, Comet, or unseeded sGREEN.”

## Remaining merge questions

These were open on the review canvas and are still the process questions for merging now:

1. Confirm SC-03 stays an operational seed/burn on deploy, not a virtual-share contract change, before `rh` becomes the launch source of truth.
2. After this lands, Instant Bond (#156) rebases onto `rh`. Is that the order you want?
3. Who undrafts and approves #126? There is no GitHub review on the aggregate yet. This memo is that independent review.

## Operational follow-ups (not this verdict)

Merging source does not make remediations live. Users still run old bytecode until the changed contracts are deployed, registries and MissionControl are rebound, and privileged writes are executed and read back.

The remediations do not take effect as intended until, at least:

- sGREEN is seeded and the seed shares cannot leave (SC-03 / B-AUD-007);
- a protocol keeper/monitor exists for fee-free liquidation retries (#160 / SC-08);
- the Underscore registry stays at zero until the new TellerUtils/Deleverage are deployed and a nonzero registry is verified user-bound (#161 / SC-13);
- assets are admitted only with a usable feed before positive LTV / deposit (B-AUD-002 / SC-10);
- live PriceDesk and Stock configuration are reconciled against the repo (DER-C01, DER-T01, DER-T04, DER-C02).

Keep nested BlueChip composition, Comet/indexed SharesVault assets, and `wsuperOETHb` off until their extra work is done. Instant Bond (PR #156) and the Base RipeGov migration (#150) are nearby work this PR does not do.

Those items are operational and activation work. They are not a substitute for a Base live-risk walk, and this memo does not record one.

## Summary

Fast-forward `origin/rh-audit-remediation` into `origin/rh` (`36ee0db`). The independent review was of contract head `5f3848c`; current origin tip `8ebb0e7` adds only this docs wave. SC-01 and SC-02 are fixed in contract code. SC-03 remains an operational High residual. DER-01 and SC-10 are owner-accepted. Process still requires undrafting and GitHub approval of PR #126. Merging is source-only; it does not activate anything on-chain.
