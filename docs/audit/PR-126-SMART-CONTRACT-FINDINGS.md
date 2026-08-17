# PR #126 — Consolidated Smart-Contract Findings

**PR:** `Ripe-Foundation/ripe-protocol#126` (`rh-audit-remediation` → `rh`)
**Reviewed head:** `81d6146ccb6468e53ab14d723213cf28a650f121`
**Base:** `36ee0db42482c3e7d6c43d045fc02655b90bebf4`
**Review focus:** contract behavior, value conservation, authorization, liveness, pricing, liquidation, custody, and accounting
**Excluded from the approval decision:** governance-process preferences, documentation, CI presentation, deployment ceremony, and event-only polish

## Verdict

**REQUEST CHANGES. Do not approve or merge this head.**

The current code has three independently sufficient High blockers, plus unresolved conditional and Medium-severity defects:

1. Stability Pool liquidation can burn more GREEN than the debt actually reduced.
2. A fungible-auction buyer can seize collateral far beyond the remaining debt and make the borrower bear the auction discount on the excess.
3. An unseeded sGREEN deployment remains vulnerable to the first-depositor donation/inflation attack; the zero-share check does not prevent profitable partial dilution.
4. The new SharesVault exact-delta assertions have not been proven executable against index/principal-based Aave/Compound position tokens. Fresh Base state shows no current positions and disables new deposits for that set, so this is a future-enablement compatibility gate rather than present custody exposure.
5. Several Medium-severity denial-of-service, stale-state, and accounting paths remain, including unbounded gas forwarding in PriceDesk, repeatable no-progress liquidation fees, and a credible deleverage reentrancy/stale-debt shape.

This verdict is based on the contract state at the exact head above. The supplied candidate report reviewed `21f2433`; the current head adds PR #138. That later commit fixes the BondRoom booster preview/execution ordering mismatch. It does **not** remove the restart-delay epoch underflow/revert; that remaining behavior is dispositioned below as accepted preview/execution unavailability, not as a fix.

## Classification used here

- **Confirmed:** the failure follows directly from reachable contract logic.
- **Conditional but credible:** the code path is real, but exploitation depends on an admitted token, a supported integration, or a configuration state. It still requires a proof or an explicit enforced invariant before approval.
- **Valid hardening/Low:** a real correctness or availability defect with narrower impact.
- **Observation / policy choice:** the code does what it says, but the behavior may be undesirable; not treated as a defect without a contrary invariant.
- **Rejected:** the proposed failure does not follow from the current code.

“Pre-existing” does not mean “safe.” It only identifies origin. Because this review was requested as a no-merge safety gate, confirmed pre-existing loss-of-funds and conservation defects are included in the request-changes decision.

## Finding rollup

| ID | Severity | Origin | Current disposition |
|---|---|---|---|
| SC-01 | High | Pre-existing; PR #106 changes fee allocation | Confirmed blocker; code fix and conservation regression required |
| SC-02 | High | Pre-existing | Confirmed blocker; cap auction seizure by live debt |
| SC-03 | High | Pre-existing known residual | Confirmed when sGREEN is unseeded; enforce the invariant in code |
| SC-04 | Medium conditional | PR #121 | Current Base retains the affected registrations but has zero user-share liabilities and disables deposits; exact-token fork proof or enforced exclusion required before future enablement |
| SC-05 | Medium | Pre-existing; adjacent PR hardening incomplete | Confirmed ring-resize defect |
| SC-06 | Medium | PR #96 | Confirmed gas-griefing gap |
| SC-07 | Medium conditional | Pre-existing | Credible callback-token path; adversarial test/fix required |
| SC-08 | Medium | Pre-existing fee rule; made repeatable by PR #118 | Confirmed repeatable no-progress fee path |
| SC-09 | Medium | PR integration omission | Confirmed fail-soft composition gap |
| SC-10 | Medium conditional | PR quarantine behavior | Confirmed for positive-LTV assets with no acknowledged feed |
| SC-11 | Medium | Pre-existing | Confirmed repayment liveness defect |
| SC-12 | Medium | Pre-existing | Confirmed economic-accounting defect |
| SC-13 | Medium conditional | Pre-existing; PR #136 fixes one sibling | Confirmed authority boundary; dormant until integration is enabled |
| SC-14 | Medium conditional | Pre-existing | Confirmed checkpoint omission; impact depends on reward allocation |
| SC-15 | Medium conditional | Pre-existing | Confirmed stale-registration liveness defect |
| SC-16 | Medium | Pre-existing | Confirmed spot-driven danger-reset defect |
| SC-17 | Medium conditional | Pre-existing | Confirmed oracle-integrity weakness |
| SC-18 | Medium conditional | Pre-existing | Confirmed for tokens that underdeliver |
| SC-19 | Medium conditional | Pre-existing | Executability cap missing; supported-pool proof/fix required |
| SC-20 | Low/Medium | Pre-existing | Base and both RH profiles use 24 hours, but a feed-specific policy cannot tighten that bound |
| SC-21 | Low | Pre-existing | Confirmed timestamp/staleness hardening gap |
| SC-22 | Low | Mixed: PR #96 and pre-existing snapshot path | Confirmed malformed-response/return-value defects |
| SC-23 | Low | Pre-existing | Confirmed indefinite stale fallback |
| SC-24 | Low | Pre-existing | Confirmed bounded reward-fairness defect |
| SC-25 | Low | Pre-existing | Confirmed enumeration availability defect |
| SC-26 | Low conditional | Pre-existing | Confirmed dust-participation effect; policy boundary remains |
| SC-27 | Low | Pre-existing deployment footgun | Confirmed constructor invariant gap |
| SC-28 | Low | Pre-existing non-RH integration hazard | Confirmed hardcoded fallback risk if enabled |
| SC-29 | Low | Pre-existing | Confirmed registry recovery defect |
| SC-30 | Low/nit | Pre-existing | Confirmed half-open maximum-discount behavior |

---

# A. Confirmed and material findings

## SC-01 — High — Stability Pool settlement can burn GREEN that reduces no debt

**Origin:** pre-existing; PR #106 changes the fee split but not the root conservation error
**Where:** `contracts/core/AuctionHouse.vy:330-392`, `:749-785`; `contracts/vaults/modules/StabVault.vy:543-573`

The Stability Pool burns the amount returned by `swapForLiquidatedCollateral`. AuctionHouse converts that amount to `stabValueSwapped` and counts the full value as repayment progress. Later, however, AuctionHouse adds only unpaid liquidation fees to `userDebt.amount` and clamps `repayValueIn` to that smaller debt before calling `CreditEngine.repayFromDept`:

```vyper
userDebt.amount += liqFeesUnpaid
repayValueIn = min(repayValueIn, userDebt.amount)
```

The burn has already occurred, so the clamp cannot refund the excess. A depleted-collateral swap can therefore destroy more GREEN supply than the amount of debt removed.

Reachable example, ignoring only integer dust:

- debt = 90
- collateral = 105
- base liquidation fee = 9
- keeper fee = 1
- target LTV = 50%
- target repayment = 95
- Stability Pool receives all 105 of collateral and burns 94.5 GREEN using the 10% base-fee spread
- paid base fee = 9; keeper fee remains unpaid, so the debt passed forward is 91
- AuctionHouse clamps repayment from 94.5 to 91
- approximately 3.5 GREEN was burned without reducing debt

The borrower also loses collateral value beyond the debt plus recognized fees. Existing tests assert the clamped debt result but do not assert the system invariant `GREEN supply decrease == debt decrease net of explicitly minted fees`.

**Required closure:** cap the Stability Pool payment before the burn, or carry the full burned amount into debt settlement/refund accounting. Add a regression asserting GREEN supply, debt, keeper minting, collateral outflow, and paid/unpaid fee conservation in depleted-collateral cases.

## SC-02 — High — Fungible-auction purchases are not capped by remaining debt

**Origin:** pre-existing
**Where:** `contracts/core/AuctionHouse.vy:1173-1205`; `contracts/core/CreditEngine.vy:491-508`, `:624-627`

AuctionHouse sizes collateral solely from buyer-supplied GREEN:

```vyper
maxCollateralUsdValue = greenAmount * HUNDRED_PERCENT // (HUNDRED_PERCENT - discount)
```

There is no clamp against the borrower’s live debt or actual liquidation shortfall. CreditEngine later limits the debt reduction and refunds excess GREEN to the borrower, but the collateral transfer has already occurred at the auction discount. The borrower therefore pays the discount on collateral that did not need to be liquidated.

Example: with $1,000 remaining debt, $100,000 auction collateral, and a 20% discount, a buyer can take all $100,000 for $80,000 GREEN. CreditEngine uses $1,000 to clear debt and refunds $79,000 to the borrower, leaving the borrower with $79,000 for $100,000 of seized collateral: a $20,000 loss caused by a $1,000 shortfall.

**Required closure:** cap GREEN spent/collateral seized by the live debt plus only an explicitly approved, tightly bounded overage. Test interest accrued between auction creation and purchase and a buyer balance much larger than debt.

## SC-03 — High — sGREEN remains vulnerable to a profitable first-depositor donation attack

**Origin:** pre-existing known residual (B-AUD-007)
**Where:** `contracts/tokens/modules/Erc4626Token.vy:238-263`

When `totalSupply == 0`, assets mint shares 1:1. Later conversions use raw `assets * totalSupply / totalAssets` with no virtual shares or permanently locked seed. Direct GREEN donations increase `totalAssets` without increasing shares.

The new zero-share rejection prevents the worst “deposit transfers assets and receives zero” form, but it does **not** prevent profitable dilution when the victim still receives one wei of shares. Example, with all share calculations performed in base units:

1. attacker deposits **1 wei of GREEN** and receives 1 wei of sGREEN shares;
2. attacker donates 500 GREEN directly;
3. victim deposits 1,000 GREEN and receives `floor(1,000e18 * 1 / (500e18 + 1)) = 1` wei of shares;
4. total assets are 1,500 GREEN plus 1 wei and total shares are 2 wei;
5. attacker redeems approximately 750 GREEN after spending 500 GREEN plus 1 wei, profiting approximately 250 GREEN at the victim’s expense.

The proposed operational seed works only if it is always executed and the seed shares can never leave. The contract does not enforce either condition.

**Required closure:** add virtual/dead shares or enforce an immutable non-withdrawable seed. A release checklist is not a contract invariant.

## SC-04 — Medium conditional compatibility risk — SharesVault exact delivery may brick future rebase-token exits

**Origin:** introduced by PR #121
**Where:** `contracts/vaults/modules/SharesVault.vy:65-78`

Every SharesVault withdrawal now requires both:

```vyper
vault balance decrease == withdrawalAmount
recipient balance increase == withdrawalAmount
```

A fresh read-only Base series on 2026-08-14, beginning at block **49,972,042**, confirms the current integration premise rather than relying on the December 2025 dump:

- VaultBook ID 4 still resolves to RebaseErc20 vault `0xce2E96C9F6806731914A7b4c3E4aC1F296d98597`.
- The vault enumerates six assets: `0x784e…cE89`, Aave V3 cbBTC `0xBdb9…8EE6`, Aave V3 USDC `0x4e65…c0AB`, Aave V3 WETH `0xD4a0…8bb7`, Compound V3 USDC `0xb125…b2F`, and Compound V3 WETH `0x46e6…0bf`.
- The current MissionControl returns `true` for `isSupportedAssetInVault(4, asset)` for all six, meaning vault ID 4 remains in each asset’s retained vault-ID list.
- A stricter `getTellerDepositConfig(4, asset, user)` read returns `canDepositGeneral = true`, `canDepositAsset = false`, and `doesVaultSupportAsset = true` for every asset. Teller therefore **cannot create new positions** in this set under the current Base configuration.
- The vault’s `totalBalances(asset)` was zero for every enumerated asset, and `doesVaultHaveAnyFunds()` returned false. `totalBalances` is the vault’s user-share liability, so the read found **no current user position exposure** in vault ID 4; it did not show funds already trapped.

The Aave and Compound tokens use index/principal-based accounting. Official Aave code converts between scaled and observable balances, and Aave’s own newer implementation/audit material explicitly addresses one-unit transfer imprecision. See the official [Aave V3 AToken implementation](https://github.com/aave/aave-v3-core/blob/master/contracts/protocol/tokenization/AToken.sol) and [Aave v3.5 transfer-rounding discussion](https://github.com/aave-dao/aave-v3-origin/blob/main/audits/2025-07-17_StErMi_Aave-v3.5.md).

That does not prove the exact deployed tokens fail every transfer. It does prove that strict equality is not safe to approve without exact-token fork evidence. The current positive-rebase test deliberately uses a 2x index where even amounts are exactly representable; it does not test fractional indexes, arbitrary recipient balances, or liquidation-computed amounts.

There is meaningful evidence on both sides. The pre-existing Teller deposit path already requires an exact **recipient/vault inflow** (`Teller.vy:313-323`), so exact observable delivery often works for tokens accepted today. PR #121 adds a second, independently restrictive condition on exits: exact **sender/vault outflow** as well as exact recipient inflow. The live deposit assertion does not prove that arbitrary withdrawal amounts computed from shares, prices, or liquidation math are exactly representable on both sides.

If either delta is `withdrawalAmount ± 1`, the transaction reverts after the token transfer call and rolls the whole exit back. If a future deployment or configuration enables a susceptible token, this affects user withdrawal, redemption, deleverage, and liquidation seizure. The impact upon activation can be High, but current likelihood/exposure is absent: Base has no outstanding vault-share liabilities and disables new deposits for all six assets, while the reviewed RH profiles use the Simple ERC-20 vault rather than this Base token set. The consolidated severity is therefore Medium conditional.

**Required closure before future enablement:** fork-test every intended Aave/Compound or similar rebase token across fractional indexes, nonzero recipient balances, small values, max withdrawal, and liquidation-derived amounts. If any mismatch occurs, use token-aware share accounting or a rigorously bounded tolerance that cannot admit fee-on-transfer loss. For this PR, an enforced exclusion that prevents these assets from being enabled under the artifact is also valid closure; the present disabled Base state is evidence of current safety, not an immutable contract invariant.

## SC-05 — Medium — Snapshot-ring resizing reads the wrong history and can resurrect discarded slots

**Origin:** pre-existing resizing defect; the PR improves pending-update cursor freshness but does not make resizing safe
**Where:** `contracts/priceSources/BlueChipYieldPrices.vy:650-667`, `:853-895`, `:930-938`; `contracts/priceSources/UndyVaultPrices.vy:443-460`, `:641-668`, `:698-706`

On config confirmation, the current cursor is reduced modulo the new capacity:

```vyper
d.config.nextIndex = currentConfig.nextIndex % d.config.maxNumSnapshots
```

But the snapshot mapping is not reordered or cleared. If a 20-slot full ring has `nextIndex = 17` and capacity is reduced to 5, the active read becomes slots `0..4`, not the five newest snapshots. The cursor becomes 2 and begins overwriting that arbitrary subset. If capacity later grows, untouched slots `5..19` become active again and old observations re-enter the weighted price if their timestamps remain admissible or staleness is disabled.

This can materially change a collateral oracle and combines badly with supply-weighted snapshots (SC-17).

**Required closure:** either forbid capacity changes after initialization or explicitly migrate the newest `min(oldN,newN)` snapshots in chronological order and clear excluded slots. Test shrink, writes while shrunk, and regrowth.

## SC-06 — Medium — PriceDesk source isolation forwards unbounded gas

**Origin:** introduced by PR #96
**Where:** `contracts/registries/PriceDesk.vy:183-211`, `:264-280`, `:383-396`

All three isolation `raw_call` sites omit a `gas=` bound. A registered source that loops until out of gas does not cleanly return control with a useful budget: EIP-150 leaves only about 1/64 of the caller’s gas. Multi-source and multi-asset valuation can then fail before PriceDesk reaches a healthy later source.

The change contains ordinary reverts and malformed returndata, but not gas griefing—the same failure class B-AUD-011 was intended to isolate.

**Required closure:** set a measured per-source gas stipend and test a source that deliberately consumes its allowance before a healthy source.

## SC-07 — Medium conditional — Deleverage can be reentered and later overwrite inner debt with stale outer debt

**Origin:** pre-existing; not fixed by the PR’s reentrancy assessment
**Where:** `contracts/core/Teller.vy:839-850`; `contracts/core/Deleverage.vy:292-374`, `:655-727`, `:864-925`

The two public Teller deleverage routes are conspicuous exceptions to the contract’s `@nonreentrant` pattern. Deleverage captures `userDebt` before transferring collateral, performs external vault/token calls, and writes debt only after all collateral handling.

With an admitted callback-capable token, its transfer can call Teller again. The transient `didHandleVaultId` / `didHandleAsset` maps stop the exact same item from being processed twice, but they do not protect the captured debt snapshot:

1. outer call captures debt D and begins vault A;
2. token callback reenters and processes a different vault/asset, then writes debt D−Y;
3. outer call resumes, skips the inner-handled item because of transient flags, and calls `repayFromDept` using stale debt D;
4. the outer write can restore debt already cleared by the inner call while both collateral transfers remain consumed.

This requires a callback-capable admitted token; B-AUD-002 explicitly leaves token admission to policy, so the code cannot assume all assets are callback-free.

**Required closure:** put the Teller deleverage entries under the same reentrancy guard or redesign settlement around a single fresh debt write. Add an adversarial token test spanning two vaults.

## SC-08 — Medium — Expired-auction cleanup makes no-progress liquidation fees repeatable

**Origin:** pre-existing fee rule made repeatedly reachable by PR #118
**Where:** `contracts/core/AuctionHouse.vy:365-392`, `:1030-1059`

The “economically inert” guard zeroes fees only when `repayValueIn == 0` **and no auction was queued**. A call that queues an auction but repays no debt still adds liquidation fees and can mint the keeper fee. The new permissionless expired-auction cleanup removes the auction after expiry, allowing another caller to repeat the no-progress liquidation and fee charge.

This is self-limited by collateral surplus because fees are capped, but it can consume the borrower’s entire safety buffer and mint keeper GREEN without debt repayment.

**Required closure:** charge fees and keeper compensation only in proportion to actual debt repaid/collateral successfully sold, or make the first auction’s fee state persistent across cleanup/retry.

## SC-09 — Medium — Stability-cohort fail-soft behavior was not composed into broad Deleverage routes

**Origin:** PR integration omission
**Where:** `contracts/core/Deleverage.vy:773-817`, `:959-990`, `:1040-1097`; `contracts/vaults/modules/StabVault.vy:371-390`, `:435-470`

CreditEngine deliberately skips Stability Pool vaults when valuing borrower collateral, and AuctionHouse now treats an unhealthy cohort as unavailable for optional routing. Broad Deleverage still walks the user’s stability vault first. Calculating a user’s withdrawable stability asset invokes strict claim-asset valuation, so one unpriceable claim asset can revert the entire broad deleverage before healthy ordinary collateral is reached.

The candidate report overstates this as “neither liquidatable nor deleveragable” in all cases: ordinary auction paths and `deleverageWithSpecificAssets` may route around it. The valid issue is that the default/broad fail-soft path is not actually fail-soft as a composed system.

**Required closure:** skip an unavailable stability cohort in optional broad deleverage and continue to ordinary collateral; preserve strict failure for direct claims/withdrawals. Test a borrower with healthy ordinary collateral plus a Stability Pool claim asset whose price source fails.

## SC-10 — Medium conditional — A positive-LTV no-feed asset quarantines an entire account

**Origin:** introduced by the PR’s account-wide quarantine behavior
**Where:** `contracts/core/CreditEngine.vy:740-767`; consumers at `:981` and in AuctionHouse/Deleverage/CreditRedeem

A nonzero balance with positive LTV and `collateralVal == 0` sets `hasQuarantinedAsset`. PriceDesk strict mode returns zero without reverting when **no source acknowledges a feed**. Holding one such asset therefore suppresses liquidation, redemption, and deleverage for all other collateral in the account.

The supplied claim was too broad in two ways:

- ordinary dust is not enough if it still produces a usable price;
- a configured source that fails causes strict valuation to revert; the no-acknowledged-feed case instead returns zero even in strict mode and reaches the quarantine branch.

The real vector requires an admitted positive-LTV asset with no acknowledged feed—a configuration error, incomplete feed cutover, or feed removal. Deposit does not enforce feed coverage, so the state is reachable.

A configured-but-failing feed creates a related two-call liveness trap: non-strict `canLiquidateUser` receives zero, sets `hasQuarantinedAsset`, and returns false, while strict actual liquidation and strict repayment revert. Thus repayment and liquidation are both unavailable during the outage. The composition is valid, but it is not wholly introduced by the PR: actual liquidation already used strict valuation and reverted at the base head. The PR changes the non-strict eligibility/quarantine side, not that pre-existing strict revert.

**Required closure:** enforce usable feed coverage before granting positive LTV/deposit eligibility, or quarantine only the affected asset while valuing/liquidating healthy collateral conservatively.

## SC-11 — Medium — Ordinary repayment depends on every collateral oracle being healthy

**Origin:** pre-existing
**Where:** `contracts/core/CreditEngine.vy:546-588`

`_repayDebt` reduces the local debt value, then recomputes every collateral term with `_shouldRaise=True` before persisting the repayment or burning GREEN. An outage in any acknowledged positive-LTV collateral feed therefore prevents a borrower from reducing debt—even a full repayment—while interest continues.

This is not newly created by the quarantine PR. P-5 is valid as an outage-liveness interaction with SC-10, but inaccurate if framed as a wholly new regression. It is nevertheless undesirable debt-liveness behavior.

**Required closure:** allow repayment to commit independently of collateral-price availability. Price health may determine whether `inLiquidation` can be cleared, but should not block debt reduction.

## SC-12 — Medium — RipeGov’s early-exit fee is redistributed back to the exiting holder

**Origin:** pre-existing
**Where:** `contracts/vaults/RipeGov.vy:807-850`

`releaseLock` charges the fee by burning a fraction of the user’s shares while leaving underlying custody unchanged. That increases the asset value of every remaining share—including the exiter’s remaining shares. A sole holder that pays an 80% nominal fee still owns 100% of the underlying through its remaining 20% of shares, making the effective fee zero. A dominant holder recovers most of the nominal fee similarly.

The function also reduces `lastShares` but leaves already accumulated `govPoints` intact. The economic exit penalty therefore does not behave like the configured percentage.

**Required closure:** transfer/burn underlying value or send fee shares to a nonparticipating recipient; test sole-holder and 90%-holder cases.

## SC-13 — Medium conditional — Underscore registration confers global cross-user authority

**Origin:** pre-existing; PR #136 fixes only one sibling route
**Where:** `contracts/core/TellerUtils.vy` (`isUnderscoreOwnerOrLego`); `contracts/core/Deleverage.vy:269-271`, `:297-311`; Teller gov-vault lock routes

The authorization helper returns true if the caller is either the user’s wallet owner **or any registered Underscore address**. The second condition is not scoped to the user. Any registered Lego can therefore satisfy third-party gates for arbitrary victims, including lock extension/release/deposit routes. The two broad deleverage routes also treat any Underscore address as trusted for every user, bypassing the untrusted near-redemption and LTV caps.

This is dormant while the Underscore registry is unset and requires a trusted integration address; that reduces present exposure but does not make the authority boundary correct.

**Required closure:** bind every Underscore authorization to ownership/installation/delegation for the specific user and apply the same rule to all deleverage siblings.

## SC-14 — Medium conditional — Liquidation/redemption transfer checkpoints omit the sender’s reward state

**Origin:** pre-existing
**Where:** `contracts/core/AuctionHouse.vy:1293-1295`; `contracts/core/CreditEngine.vy:1155-1177`

When collateral is moved within a vault, the code checkpoints only the recipient’s Lootbox deposit points. The sender’s `lastBalance` remains at the pre-transfer amount, so the sender continues accruing rewards on collateral no longer owned. When collateral is withdrawn out of the vault instead, the sender is likewise not checkpointed.

The general depositor/voter allocation is zero in the checked default profiles, so current payout exposure is dormant. Enabling those rewards makes duplicate accrual possible.

**Required closure:** checkpoint the sender before balance mutation and the recipient after mutation, mirroring the HR transfer remediation.

## SC-15 — Medium conditional — Repointing a remembered vault ID to a fresh vault can brick a user

**Origin:** pre-existing
**Where:** `contracts/core/CreditEngine.vy:720-731`; `contracts/core/Lootbox.vy:294-302`, `:353-359`; `contracts/vaults/modules/VaultData.vy:115-151`

Two consumers execute `range(1, numUserAssets)` without guarding `numUserAssets == 0`. In Vyper 0.4.3, `range(1, 0, bound=...)` reverts. A user can retain a Ledger reference to vault ID V after withdrawing, while VaultBook later points V to a fresh vault where the user’s raw `numUserAssets` is zero. CreditEngine and Lootbox then revert before they can clean up the stale reference, potentially blocking all Teller housekeeping for that user.

**Required closure:** add the same zero guards already used by AuctionHouse/Deleverage and test a vault-ID replacement with historical users.

## SC-16 — Medium — Curve danger duration can be reset with a one-transaction spot manipulation

**Origin:** pre-existing
**Where:** `contracts/priceSources/CurvePrices.vy` danger snapshot logic around `:1035-1039`

The danger decision uses the pool’s instantaneous balance ratio, and any non-danger observation resets `numBlocksInDanger` to zero. An attacker can temporarily move the pool ratio with a flash-funded swap, trigger snapshot housekeeping through a small Teller action, and reverse the swap. The persistent danger duration is erased even though the smoothed state and underlying depeg have not recovered.

**Required closure:** drive entry and reset from a manipulation-resistant observation and require a sustained safe period before clearing accumulated danger.

## SC-17 — Medium conditional — Snapshot weighting and zero-write behavior weaken BlueChip/Undy integrity

**Origin:** pre-existing; zero-consumption behavior was hardened but write-side behavior remains
**Where:** `contracts/priceSources/BlueChipYieldPrices.vy:857-895`, `:930-1004`; `contracts/priceSources/UndyVaultPrices.vy:645-668`, `:698-748`

Snapshots are weighted by the external vault’s `totalSupply` at the snapshot instant. Snapshot timing is reachable through protocol housekeeping, and many external vault supplies can be changed in the same transaction. A flash-inflated supply observation can dominate the purported multi-observation average.

Separately, a zero price-per-share read is stored as `lastSnapshot = 0`. Consumption now fails closed on zero, but the next positive observation bypasses upside throttling because `_throttleUpside` returns the new value unchanged when `_prevValue == 0`. One zero write therefore disarms the next upside cap.

**Required closure:** use time/duration weighting rather than externally mutable supply, and do not advance the throttle anchor on an invalid zero observation.

## SC-18 — Medium conditional — Partner-liquidity minting uses nominal rather than received tokens

**Origin:** pre-existing
**Where:** `contracts/core/Endaoment.vy:1071-1094`

`_mintPartnerLiquidity` transfers `partnerAmount` to EndaomentFunds, but never measures the recipient delta. It values the nominal amount and mints GREEN against that nominal USD value. A fee-on-transfer or otherwise inexact admitted partner asset therefore causes undercollateralized GREEN minting and can make the later liquidity operation consume treasury inventory to cover the shortfall.

**Required closure:** measure exact recipient inflow and value only the received amount, or enforce token behavior at the contract boundary.

## SC-19 — Medium conditional — Stabilizer removal can request more GREEN than its LP can withdraw

**Origin:** pre-existing
**Where:** `contracts/core/Endaoment.vy:879-925`

The removal cap is:

```vyper
maxGreenToRemove = max(poolDebt, proportionalGreenEntitlement)
```

When pool debt exceeds the GREEN value withdrawable by Endaoment’s LP balance, `remove_liquidity_imbalance` can be asked to withdraw an unsupported amount and revert. That is most likely when the pool is imbalanced and stabilization is needed.

The candidate’s proposed mechanical `max → min` change is not proven universally correct because debt repayment and profit withdrawal are separate objectives. The bug is the absence of a cap derived from the actual maximum withdrawable amount for the held LP.

**Required closure:** derive the maximum executable imbalance withdrawal from LP ownership/pool math and cap the requested GREEN accordingly; test debt above LP entitlement.

---

# B. Valid lower-severity findings and hardening gaps

## SC-20 — Low/Medium — Oracle staleness resolution lets the looser bound win

**Where:** `ChainlinkPrices.vy:186,196`; same pattern in Pyth, Stork, and RedStone

Effective staleness uses `max(caller/global staleTime, feed staleTime)`. A feed-specific value can loosen the global bound but cannot make one feed stricter. Zero disables the time check. This is a real safety-policy limitation in contract code.

A fresh read-only Base call on 2026-08-14 at block **49,971,787** to MissionControl `0xB59b84B526547b6dcb86CCF4004d48E619156CF3` returned `genConfig.priceStaleTime = 86,400 seconds`. The older repository dump showing zero is stale. The exact reviewed RH source is aligned: `DefaultsRobinhood.vy:72` sets `1 * DAY_IN_SECONDS`, and the generated live/replacement profile `DefaultsRobinhoodLive.vy:55` sets `86400`.

The residual is narrower but real. Because each oracle resolves with `max(global/caller staleTime, feed staleTime)`, 24 hours is the **strictest** effective threshold under those profiles; an individual feed cannot be configured to reject data sooner, while a larger feed/caller value can loosen the threshold further. Final deployment still must bind the intended defaults, but the reviewed Base state and both RH profiles all select the same one-day global value.

The stronger claim—“no staleness enforcement in the live Base deployment”—is therefore rejected as outdated. Missing Chainlink range/circuit-breaker and L2 sequencer checks remain valid oracle-hardening gaps, but chain/feed applicability must be established before assigning higher severity.

## SC-21 — Low — Pyth/Stork future timestamps can underflow; cross-feed stale policy is misapplied

**Where:** `PythPrices.vy:197`; `StorkPrices.vy:168`; `ChainlinkPrices.vy:213-223`; `RedStone.vy:172-177`

Pyth and Stork compute `block.timestamp - publishTime` without first rejecting/handling `publishTime > block.timestamp`; checked arithmetic reverts. Pyth’s own reference implementations use saturating age logic rather than this subtraction, so a slightly future update need not be invalid.

For Chainlink ETH/BTC-denominated feeds, the cross leg is read using the base asset’s effective stale parameter, not an independently resolved ETH/BTC feed policy. RedStone similarly delegates the ETH leg without preserving a per-leg stale constraint.

## SC-22 — Low — PriceDesk accepts contradictory feed responses and misreports false snapshot updates

**Where:** `contracts/registries/PriceDesk.vy:149-176`, `:183-211`, `:383-396`

- A source response `(nonzero price, hasFeed = false)` is accepted because `_getPrice` breaks on nonzero price before using status. A contradictory response should be malformed/failure, not a usable price.
- `_safeAddPriceSnapshot` returns `resultWord <= 1`, so both canonical `false` (`0`) and `true` (`1`) count as success. This can make `addPriceSnapshot` report that an update occurred when every source returned false.

These require a buggy/compromised registered source and are narrower than SC-06, but they violate the isolation API contract.

## SC-23 — Low — Snapshot stale fallback is not itself age-bounded

**Where:** `BlueChipYieldPrices.vy:888-894`; `UndyVaultPrices.vy:661-666`; analogous Curve fallback

If every ring entry is invalid/stale, the weighted read falls back to `lastSnapshot.pricePerShare` without checking the age of `lastSnapshot`. This can turn staleness filtering into an indefinite last-value fallback. It may be an intentional availability choice, but then the `staleTime` field does not mean “fail when no fresh observation exists” and downstream risk should be explicit.

## SC-24 — Low — Small SharesVault holders can fund a reward bucket while earning zero points

**Where:** `contracts/core/Lootbox.vy` deposit-point conversion; `contracts/vaults/modules/SharesVault.vy` share-to-amount conversion

Two floor divisions can record a sub-unit holder’s `lastBalance` as zero while aggregate vault value still contributes to asset-level reward sizing. Many dust holders can therefore contribute value to the pool but receive no depositor points. This is bounded precision/fairness, not a conservation failure.

## SC-25 — Low — Price-source enumeration can be bricked after the configured bound

**Where:** `contracts/priceSources/modules/PriceSourceData.vy:44-51`, `:82-91`

Registration has no `MAX_ASSETS` check, but `getPricedAssets` uses a fixed `bound=MAX_ASSETS`. Once the raw count exceeds the view bound, the enumeration reverts. No core on-chain value path was found to consume the view, so impact is tooling/monitoring availability.

## SC-26 — Low conditional — `lowestLtv` includes zero-value/dust registrations and governs the full unwind target

**Where:** `contracts/core/CreditEngine.vy:747-780`; consumers in AuctionHouse, CreditRedeem, and Deleverage

The minimum LTV is updated even when `maxDebt == 0` and the asset contributes only the fallback weight of one. Liquidation/redemption/deleverage then apply that minimum to the whole portfolio. A dust low-LTV registration can therefore make the target unwind much larger than its economic contribution. The code comments intentionally choose the lowest LTV for conservatism, so the defect is dust participation rather than the conservative rule itself.

## SC-27 — Low deployment footgun — Nonzero initial sGREEN supply has no backing

**Where:** `contracts/tokens/SavingsGreen.vy:31-42`; `Erc4626Token.vy` conversion math

The constructor forwards arbitrary `_initialSupply` to the ERC-20 share token without adding GREEN assets. A nonzero value produces shares against zero assets; conversions then return zero and normal deposit/redeem behavior becomes unusable. Existing deployments/fixtures use zero. Enforce zero or deposit matching backing atomically.

## SC-28 — Low deployment/integration hazard — Hardcoded wsuper oracle fallbacks convert outage into wrong price

**Where:** `contracts/priceSources/wsuperOETHbPrices.vy`

VVV is hardcoded to a fixed USD price and MCBETH to a literal unit value. If those addresses are enabled and higher-priority feeds fail, PriceDesk may accept these as authoritative rather than failing closed. This is outside the Robinhood launch path described by PR #126, but it is a real contract hazard for the referenced Base deployment work.

## SC-29 — Low lifecycle defect — Disabled VaultBook slots cannot be repointed through the normal update path

**Where:** `contracts/registries/VaultBook.vy:102-112`, `:149-153`

The update guard calls `doesVaultHaveAnyFunds()` on the current address. After a slot is disabled, that address is zero, so the staticcall itself reverts. The disabled ID cannot be restored/repointed through `startAddressUpdateToRegistry`. This is a recovery-path defect, not a live value-flow exploit.

## SC-30 — Low/nit — Auctions never attain the exact configured maximum discount

**Where:** `contracts/core/AuctionHouse.vy:1160-1181`

Purchases are allowed for `[startBlock, endBlock)`, so maximum progress is `(duration - 1) / duration`. The exact `maxDiscount` is never returned unless start and max discounts are equal. The half-open boundary is otherwise internally consistent.

---

# C. Conditional observations and deployment security boundaries needing an owner decision

1. **Bond bad-debt RIPE budget:** `BondRoom` checks total payout against `ripeAvailForBonds` but deducts only the non-bad-debt portion. This is suspicious if there is meant to be one mint budget; it may be intentional if bad-debt RIPE is a separately authorized uncapped lane. The code needs an explicit invariant and separate cap if that is the design.
2. **Partner LP fixed 50/50 split:** the protocol gives the partner half of LP tokens regardless of the exact asset composition. That is safe only if the supported liquidity Lego consumes equal-value inputs as assumed. The candidate report did not prove a supported path that leaves partner residue while assigning half the LP.
3. **Contributor freeze/cancellation and “cliff”:** the contract uses the cliff as a cancellation boundary, not as a claim gate. Freeze-then-cancel can forfeit vested-but-unclaimed compensation, but both actions are authorized HR controls. This is a compensation-policy question unless the agreement promises vested value survives freeze/cancellation.
4. **Liquidation freeze hysteresis:** `inLiquidation` is entered by AuctionHouse/CreditEngine at the liquidation threshold and cleared only after returning to ordinary LTV health. That is conservative and explicitly described in code; it is not an off-by-one defect.
5. **GREEN/sGREEN pause coupling:** pausing tokens blocks burns/redemptions used for repayment or Stability Pool settlement. This is a strong emergency-stop policy with liveness consequences, not an accidental logic path.
6. **BasicVault shortfall quarantine:** refusing all withdrawals while nominal balances exceed custody is intentionally fail-closed. A pro-rata insolvency/recovery mode may be desirable, but the PR deliberately selected quarantine.
7. **Capacity-weighted debt terms:** CreditEngine explicitly weights thresholds/rates by borrowing capacity. A collateral-value-weighted model would produce different risk results, but the present implementation is internally consistent with the stated model.
8. **Base PriceDesk zero registry timelock:** a fresh read-only Base call on 2026-08-14 at block 49,971,787 returned `registryChangeTimeLock = 0` for PriceDesk `0x68564c6035e8Dc21F0Ce6CB9592dC47B59dE2Ff6`. The constructor/setup lifecycle permits this state, and an authorized oracle-source repoint can therefore be proposed and confirmed without a block delay. This is a real deployment security boundary requiring an explicit owner decision and deployment invariant, but it is not a permissionless PR #126 contract exploit.
9. **Base MissionControl ABI compatibility:** at the same block, `coreRipeGovVaultId()` reverted on the deployed Base MissionControl. That is different from X-36’s claimed reachable zero-ID state: the source contract initializes the ID nonzero and forbids setting it to zero, but new BondRoom/VaultMigrator callers still require a compatible MissionControl deployment before activation.
10. **RIPE price-source cutover:** the repository’s Base price inventory at block 38,930,921 lists Aero regId 6 as RIPE’s only source, while PR #113 makes the replacement Aero `PriceSource` surface intentionally return `(0, false)`. Rebinding that slot before an alternate RIPE feed exists makes strict PriceDesk calls return zero without raising because no source acknowledges a feed. Any launch/rebinding sequence must prove a replacement RIPE source first; otherwise on-chain RIPE valuation consumers, including reward-value and auction/claim paths, lose a usable price. The removal of raw Aerodrome spot pricing is correct; the risk is cutover ordering.

---

# D. Complete disposition of the supplied P findings

| Candidate | Disposition | Consolidated result |
|---|---|---|
| P-1 | **Valid compatibility premise; current severity reduced** | SC-04. Fresh Base reads confirm retained Aave/Compound registrations, but all six have zero `totalBalances` and `canDepositAsset = false`. There is no current Base custody exposure; exact-token fork proof or enforced exclusion is required before future enablement under PR #121’s exit assertions. |
| P-2 | **Partially valid, origin/severity corrected** | SC-13. The global Underscore trust boundary predates the PR; the PR fixes only one sibling. Dormant until integration is enabled. |
| P-3 | **Valid after narrowing** | SC-09. Broad Deleverage is not fail-soft, but specific-asset and ordinary auction routes can still exist. |
| P-4 | **Partially valid** | SC-10. Strict acknowledged-feed outages revert; the persistent quarantine-without-revert vector is a positive-LTV asset with no acknowledged feed. Non-strict eligibility during a configured outage is covered with P-5. |
| P-5 | **Valid liveness interaction; PR-origin claim narrowed** | SC-10/SC-11. Non-strict eligibility reports quarantine/non-liquidatable while strict actual liquidation and repayment revert during a configured-feed outage. Both routes are unavailable, but strict liquidation and repayment oracle dependence predate this PR. |
| P-6 | **Accepted behavior / policy** | Pause now applies to exits and therefore to sGREEN-backed liquidation settlement. This follows the PR’s explicit exit-control policy. |
| P-7 | **Valid** | SC-06. All isolation calls forward unbounded gas. |
| P-8 | **Valid residual observation** | Trusted full-payoff extras can consume bounded collateral above debt; current reviewed defaults are zero. Keep as a configuration-sensitive policy, not a present exploit. |
| P-9 | **Rejected** | Empty AuctionHouse/Lootbox arrays perform only caller/self housekeeping; no victim state is affected. |
| P-10 | **Observation** | Aero monitor recovery is intentionally inert. Accidental token donations can be stuck, but there is no protocol custody path into it. |
| P-11 | **Observability nit only** | The repayment event lacks the payer/refund recipient after third-party refund semantics changed. No accounting error follows. |
| P-12 | **Test/invariant nit, no current bug** | All current burning callers pass a nonzero recipient; zero would be dangerous only after a future caller change. |
| P-13 | **Valid duplicate** | Folded into repeatable no-progress fee finding SC-08. |
| P-14 | **Rejected as production issue** | Single-item claim/redeem helpers are not exported by production contracts; dead source does not create an ABI surface. |
| P-15 | **Future maintainability nit** | Enum default could mislabel after sender-set growth; no current caller is misclassified. |
| P-16 | **Event-only nit** | No value/state error. Excluded from contract-logic approval. |
| P-17 | **Valid integration/deprecation observation** | Aero’s spot alias is monitoring-only and not a PriceDesk feed. The stored Base inventory shows Aero as RIPE’s only source, so a replacement feed must precede rebinding the inert implementation; legacy-selector consumers can still read manipulable monitoring spot meanwhile. |

---

# E. Complete disposition of the supplied X findings

| Candidate | Disposition | Consolidated result |
|---|---|---|
| X-0 | **Partially valid; live claim disproved** | SC-20. Fresh Base state and both reviewed RH default profiles use a nonzero 86,400-second global bound, so the old live-zero claim is stale. Looser-bound-wins prevents any feed from being stricter than 24 hours; circuit-breaker/sequencer items remain hardening gaps. |
| X-1 | **Confirmed deployment security boundary** | Fresh Base state at block 49,971,787 confirms PriceDesk’s registry timelock is zero. Listed in section C for an explicit owner/deployment invariant; not treated as a permissionless PR logic exploit. |
| X-2 | **Valid High** | SC-02. |
| X-3 | **Valid, severity reduced to Medium** | SC-12. Economic penalty is recycled to the exiter; no unauthenticated theft. |
| X-4 | **Valid conditional** | SC-13. |
| X-5 | **Valid conditional** | SC-14. Dormant while relevant reward allocations remain zero. |
| X-6 | **Accepted emergency policy** | Token pause blocks burns/repayment; intentional broad pause semantics. |
| X-7 | **Valid conditional** | SC-15. |
| X-8 | **Accepted fail-closed design** | BasicVault deliberately quarantines shortfall rather than socializing it pro rata. A recovery mode is product design. |
| X-9 | **Valid** | SC-08, combined with P-13. |
| X-10 | **Overstated / policy** | Empty collateral terms can set borrow rate to zero, but “permanent” is false: adding valid collateral can restore terms. Bad-debt interest policy needs definition. |
| X-11 | **Valid** | SC-16. |
| X-12 | **Valid conditional** | SC-17. |
| X-13 | **Owner-intent required** | Potential separate-budget mismatch; listed in section C rather than asserted as a bug. |
| X-14 | **Valid registry semantics observation** | Deregistration removes enumeration but retains asset config used by runtime callers. This is a de-risking/recovery-control issue, not a PR value-flow regression. |
| X-15 | **Excluded governance lifecycle** | Pending registry actions do not expire. No permissionless contract exploit. |
| X-16 | **Rejected as Medium** | Permissionless pruning is bounded below the retention threshold, leaves direct batch claimability, and is intended dust maintenance. |
| X-17 | **Valid conditional** | SC-26. |
| X-18 | **Risk-model choice** | Capacity weighting is explicit and internally consistent; not treated as a code defect. |
| X-19 | **Partially valid** | Nominal partner transfer and withdrawal sizing become SC-18/SC-19. Fixed LP split and pool-debt attribution were not proven defective for a supported Lego. |
| X-20 | **Policy/contract-term ambiguity** | “Cliff” is used as a cancellation boundary, not a claim gate. Freeze/cancel forfeiture needs agreement semantics, not a security severity. |
| X-21 | **Valid deployment hazard** | SC-28. Not part of the described Robinhood runtime. |
| X-22 | **Valid Low** | SC-27. |
| X-23 | **Valid and severity raised** | SC-03. Zero-share rejection does not remove profitable one-share dilution. |
| X-24 | **Valid Low** | SC-21. |
| X-25 | **Valid Low / intentional availability possible** | SC-23. Live-age claims from the older report were not refreshed. |
| X-26 | **Policy / footgun** | Zero values intentionally disable or relax controls in several modules. Bounds may be desirable, but zero is not uniformly erroneous. |
| X-27 | **Conditional future-listing observation** | Curve lock-probe concern depends on registering a callback/reentrant pool; current supported pool behavior was not shown exploitable. |
| X-28 | **Low risk-model observation** | Stabilizer sizes from spot, but keeper authorization and post-state net-position checks constrain it. |
| X-29 | **Excluded governance defense-in-depth** | Setter validation is delegated to switchboards. Not a permissionless smart-contract bug. |
| X-30 | **Valid Low lifecycle defect** | SC-29. |
| X-31 | **Valid** | Root cause used by SC-10: strict mode silently returns zero when no source acknowledges a feed. |
| X-32 | **Valid and severity raised conditionally** | Deleverage portion is SC-07. Gov-vault deposit path is separately constrained by receipt-measurement state. |
| X-33 | **Rejected as current bug** | The leaked last config presently contains global, not per-asset, reward fields. Future refactor hazard only. |
| X-34 | **Valid Low** | SC-24. |
| X-35 | **Rejected** | Lootbox mints the requested RIPE to itself immediately before distribution; underdelivery is not reachable under the current flow. |
| X-36 | **Rejected as stated; separate deployed-ABI issue confirmed** | `coreRipeGovVaultId` is initialized nonzero and its setter forbids zero, so the asserted reachable zero-ID state is false. The current Base MissionControl instead lacks/reverts on the getter; section C records that separate deployment compatibility gate. |
| X-37 | **Accepted current behavior; separate mismatch resolved** | The restart-delay epoch subtraction still reverts, and execution is unavailable in the same window, so no preview/execution authorization mismatch follows. PR #138 fixed only booster bonus ordering; it did not change this underflow site. |
| X-38 | **Intentional conservative behavior** | Liquidation freeze clears at ordinary health, not merely below liquidation threshold. Explicit in code. |
| X-39 | **Rejected as exploitable** | GREEN has no callback hooks; the proposed ERC-4626 reentrancy path lacks a reachable callback. |
| X-40 | **Valid Low** | SC-25. |
| X-41 | **Valid gas/complexity observation** | Nested derived prices can rescan sources and amplify SC-06; a concrete current cycle was not shown. |
| X-42 | **Trust/integration observation** | Hardcoded Underscore registry ID is an external-interface assumption, not independently an exploit. |
| X-43 | **Accepted custody semantics** | Registered BasicVault donations are not assigned to users and cannot be swept while liabilities exist; safer than allowing admin extraction. |
| X-44 | **Valid Low** | SC-21 cross-leg stale-policy issue. |
| X-45 | **Interface-quality nit** | Stub methods return success without work, but no value path relies on them. |
| X-46 | **Unverified external-ABI claim** | Current local interface uses `uint256`; public Stork documentation located during review did not expose enough struct typing to confirm the alleged `int192` mismatch. Obtain the exact deployed ABI before filing. |
| X-47 | **Rejected** | BondRoom clamps `_paymentAmount` to its actual token balance before crediting. With no preexisting residue, fee-on-transfer under-receipt is not overcredited. |
| X-48 | **Future integration observation** | Boardroom callback is currently a stub; migration callback expectations must be revisited when it becomes stateful. |
| X-49 | **Tokenomics choice** | Booster cap is all-or-nothing by implementation; no arithmetic or authorization violation. |
| X-50 | **Valid but materially understated** | Folded into High conservation finding SC-01. It is more than a second-pass/nit issue. |
| X-51 | **Valid nit** | SC-30. |
| X-52 | **Rejected** | Refund to `_caller` is correct payer-refund semantics and bounded by funds actually received. |
| X-53 | **No reachable failure shown** | Current accounting invariants bound the bare subtraction. Defensive symmetry would be harmless but is not a finding. |
| X-54 | **Rejected as loss** | ETH is swept to EndaomentFunds, which has a payable empty default; the value remains protocol-controlled. |
| X-55 | **No current bug** | Downstream lock logic clamps the duration; missing early validation does not produce invalid storage/arithmetic. |
| X-56 | **Governance/policy semantics** | Lowering minimum lock releases positions by design of adverse-term comparison; exclude from contract security verdict. |

---

# F. Important findings not present in the supplied P/X report

The supplied report did not identify these, and they must remain visible:

1. **SC-01:** GREEN burn/debt-reduction conservation failure in Stability Pool liquidation.
2. **SC-05:** snapshot-ring capacity changes select/resurrect the wrong stored history.
3. **SC-22:** PriceDesk accepts `(price > 0, hasFeed = false)` and treats a `false` snapshot return as success.

It also underrated X-23: zero-share rejection does not eliminate profitable sGREEN dilution, so that item is High when deployment is unseeded rather than merely an operational Low.

---

# G. Verified-clean coverage

These areas were affirmatively reviewed at the bound head and did not produce an additional finding. This section records checked ground; it is not a claim that unlisted code was proven correct.

1. **Caller-supplied `Addys` structs:** the combined review enumerated 63 external functions accepting the struct. State-mutating routes were gated by Teller or an equivalent trusted caller, including gates placed in internal helpers. Public views can still return caller-selected-registry results if an off-chain integrator deliberately supplies a forged struct, but no protocol-state mutation route was found.
2. **SharesVault/StabVault share math:** deposit rounding down, partial-withdrawal share rounding up, full-withdrawal amount rounding down, and the `DECIMAL_OFFSET = 1e8` virtual-share construction were internally consistent. This clean result does **not** cover sGREEN, which uses different ERC-4626 math and is SC-03, or the external-token exact-delta compatibility issue in SC-04.
3. **Ordinary Ledger/VaultData indexing:** the one-based arrays and swap-and-pop bookkeeping for user vaults, assets, borrowers, and auctions were consistent in ordinary registration/removal flows. SC-15 is a separate registry-repoint edge case, not an ordinary indexing failure.
4. **Overflow-sensitive proportional rewards:** the new `_mulDivFloor` high/low product split, overflow guard, power-of-two factoring, and modular inverse structure are consistent with exact floor proportional allocation. No unjustified `unsafe_*` use was found in the inventoried AuctionHouse, CreditRedeem, Ledger, CreditEngine, Deleverage, Lootbox, or BlueChip sites.
5. **Validated denominators and unit normalization:** reviewed `HUNDRED_PERCENT - x` denominators are protected by their parameter validators; Chainlink/RedStone decimal normalization, Curve’s USDC lift, and BlueChip/Undy decimal separation were dimensionally consistent.
6. **Selected remediation paths:** the merged-traversal Stability Pool cohort sizing, maximum-discount denominator guard, expired-auction live-window separation, zero-epoch/whole-unit bond guards, zero PPS fail-closed consumption, sGREEN max-view/exit-policy alignment, HR lifecycle fixes, empty Teller batch rejection, and TellerUtils default MissionControl resolution matched their focused intent. Findings elsewhere in this report describe residual composition or adjacent behavior, not a blanket rejection of those fixes.
7. **Merge integrity:** no conflict markers or obvious contract-file conflict-resolution damage were found at `81d6146`.

---

# H. Verification limits

- Review was read-only except for creation of this report. No contract/test source was modified.
- The exact reviewed PR ref was available locally at `81d6146`. A fresh GitHub API status refresh was unavailable during the pass, so any new commit after that hash reopens affected conclusions.
- Read-only Base RPC calls refreshed the disputed global `priceStaleTime = 86,400`, PriceDesk `registryChangeTimeLock = 0`, deployed MissionControl ABI gap, and SC-04’s current vault address/asset/support/deposit/liability premise. The first series was pinned at block 49,971,787; the SC-04 series began at block 49,972,042.
- `general_output.md`, `vaults_output.md`, `assets_output.md`, and `prices_output.md` were all generated on 2025-12-02 at blocks 38,930,870–38,931,025—about 8.5 months before this review. The X-0 error demonstrates that these dumps must be treated only as historical evidence; any current-state conclusion resting on them requires an RPC or other current-state refresh.
- The exact reviewed source confirms both RH default profiles specify `priceStaleTime = 86,400`; no RH RPC state was inferred from the Base reads, and deployment must still bind the intended profile.
- SC-04 is a conditional compatibility risk rather than a claimed reproduction on the exact deployed Aave/Compound implementations. Fresh Base state confirms retained vault-ID registrations but also confirms zero current vault-share liabilities and disabled per-asset deposits. Official upstream rounding behavior makes future enablement without the fork matrix or an enforced exclusion unsafe.
- Findings marked conditional require an adversarial regression or a contract-enforced exclusion; a verbal assumption about token behavior is not closure.
- No broad test suite was rerun merely to consolidate this document. Existing passing CI does not exercise the missing adversarial invariants identified here.

---

# I. Reproduction and review appendix

The review used an isolated detached worktree, leaving the user’s active branch unchanged:

```bash
git worktree add --detach /private/tmp/pr126-repro 81d6146ccb6468e53ab14d723213cf28a650f121
git -C /private/tmp/pr126-repro rev-parse HEAD
git -C /private/tmp/pr126-repro diff --stat 36ee0db42482c3e7d6c43d045fc02655b90bebf4..81d6146ccb6468e53ab14d723213cf28a650f121
```

High/blocking source checks:

```bash
# SC-01: Stability Pool burn, liquidation accounting, and post-burn repayment clamp
nl -ba contracts/core/AuctionHouse.vy | sed -n '330,392p;749,785p'
nl -ba contracts/vaults/modules/StabVault.vy | sed -n '543,573p'

# SC-02: buyer-sized discounted seizure versus later debt/refund clamp
nl -ba contracts/core/AuctionHouse.vy | sed -n '1173,1205p'
nl -ba contracts/core/CreditEngine.vy | sed -n '491,508p;624,627p'

# SC-03: zero-supply 1:1 branch and raw ERC-4626 conversion
nl -ba contracts/tokens/modules/Erc4626Token.vy | sed -n '238,263p'

# SC-04: new exact sender/recipient exit deltas and pre-existing deposit inflow check
nl -ba contracts/vaults/modules/SharesVault.vy | sed -n '55,80p'
nl -ba contracts/core/Teller.vy | sed -n '309,327p'

# SC-05: snapshot read window, resize modulo, and untouched mapping slots
nl -ba contracts/priceSources/BlueChipYieldPrices.vy | sed -n '650,667p;853,895p;930,938p'
nl -ba contracts/priceSources/UndyVaultPrices.vy | sed -n '443,460p;641,668p;698,706p'
```

The SC-10/SC-11/P-5 composition can be followed by comparing non-strict eligibility with strict execution/repayment:

```bash
nl -ba contracts/core/CreditEngine.vy | sed -n '546,588p;692,762p;938,989p'
nl -ba contracts/core/AuctionHouse.vy | sed -n '289,312p'
nl -ba contracts/registries/PriceDesk.vy | sed -n '145,178p'
```

The first fresh Base reads used standard `eth_call` at block 49,971,787. Relevant selectors and targets were:

| Fact | Target | Selector | Result |
|---|---|---|---|
| `genConfig()` | MissionControl `0xB59b84B526547b6dcb86CCF4004d48E619156CF3` | `0xf112abed` | third ABI word `0x15180` = 86,400 seconds |
| `registryChangeTimeLock()` | PriceDesk `0x68564c6035e8Dc21F0Ce6CB9592dC47B59dE2Ff6` | `0x06400479` | `0` |
| `coreRipeGovVaultId()` | same MissionControl | `0x955cb352` | reverted |

The SC-04 inventory refresh used a second read-only series beginning at Base block 49,972,042:

| Fact | Target | Selector | Result |
|---|---|---|---|
| `getAddr(4)` | VaultBook `0xB758e30C14825519b895Fd9928d5d8748A71a944` | `0xd81f84b7` | RebaseErc20 vault `0xce2E96C9F6806731914A7b4c3E4aC1F296d98597` |
| `getNumVaultAssets()` | RebaseErc20 vault | `0x28788f26` | `6` |
| `vaultAssets(index)` | RebaseErc20 vault | `0x346d7cbc` | six addresses listed below |
| `isSupportedAssetInVault(4, asset)` | MissionControl | `0x7f4cb07e` | `true` for all six |
| `getTellerDepositConfig(4, asset, user)` | MissionControl | `0x969ea76d` | global deposit `true`; asset deposit `false`; vault support `true` for all six |
| `totalBalances(asset)` | RebaseErc20 vault | `0xaee9c872` | `0` for all six |
| `doesVaultHaveAnyFunds()` | RebaseErc20 vault | `0xa82e46fc` | `false` |

| Index | Asset/address | Vault ID retained | Asset deposit enabled | Vault user-share liability |
|---|---|---|---|---|
| 1 | `0x784efeB622244d2348d4F2522f8860B96fbEcE89` | Yes | No | 0 |
| 2 | Aave V3 cbBTC `0xBdb9300b7CDE636d9cD4AFF00f6F009fFBBc8EE6` | Yes | No | 0 |
| 3 | Aave V3 USDC `0x4e65fE4DbA92790696d040ac24Aa414708F5c0AB` | Yes | No | 0 |
| 4 | Aave V3 WETH `0xD4a0e0b9149BCee3C920d2E00b5dE09138fd8bb7` | Yes | No | 0 |
| 5 | Compound V3 USDC `0xb125E6687d4313864e53df431d5425969c15Eb2F` | Yes | No | 0 |
| 6 | Compound V3 WETH `0x46e6b214b524310239732D51387075E0e70970bf` | Yes | No | 0 |

Every finding’s `Where` field is the per-finding source map. The complete candidate audit crosswalk is preserved in sections D and E so rejected, accepted, duplicate, and unresolved claims can be reproduced rather than silently dropped.

# Summary

The pasted report contained substantial useful material, but it mixed real contract defects, deployment/governance state, intentional policies, future hazards, duplicates, and several invalid claims. After rebinding it to the current head:

- PR #138 resolves the BondRoom booster ordering mismatch, while the unchanged restart-delay preview revert is accepted only because execution is unavailable in the same window;
- the Stability Pool conservation failure and snapshot-ring resize defect must be added;
- the sGREEN first-depositor issue is more severe than reported;
- fresh Base state disproves present SharesVault/Aave-Compound custody exposure: all six assets retain vault ID 4 but have deposits disabled and zero vault-share liabilities. SC-04 is therefore a Medium conditional future-enablement risk, requiring exact-token fork proof or enforced exclusion before activation;
- the configured-feed outage does suppress liquidation eligibility while strict repayment and actual liquidation revert, but the strict half predates this PR;
- the old live-zero staleness claim is disproved by fresh Base state and both RH default profiles; the residual is that no feed can be stricter than the uniform 24-hour global bound, while the zero PriceDesk registry timelock and missing deployed `coreRipeGovVaultId()` ABI remain explicit release/security gates;
- the Aero rewrite correctly removes consumable raw spot pricing, but its inert PriceSource surface must not be rebound before a replacement RIPE feed exists;
- the auction over-liquidation, repay-oracle dependency, no-progress fee retry, PriceDesk gas isolation, global Underscore trust, reward checkpoint, stale-vault, Curve danger-reset, snapshot weighting, and Endaoment nominal-accounting issues remain valid at varying severities;
- many governance/event/pause/recovery candidates are not smart-contract logic blockers.

**Final recommendation: REQUEST CHANGES.** SC-01 through SC-03 require code fixes or contract-enforced invariants before approval. SC-04 requires exact-token fork proof or an enforced exclusion before any future enablement, but fresh Base state does not make it a current custody blocker. SC-05 through SC-11 need fixes or strong executable closure evidence; SC-12 through SC-19 need remediation or explicit, test-backed acceptance of their stated preconditions and losses. Low findings should be dispositioned rather than silently ignored.
