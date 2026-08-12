# Deposit-Vault Operating Rules — RH

**Scope:** the contract-enforced invariants and remaining operating conditions from
the deposit-vault hardening review. A rule marked operational is still required even
where the candidate adds defense in depth; a rule marked enforced is pinned directly
by production code and tests.

This runbook documents operational procedure only. It authorizes no production
transaction.

Evidence and measurements: [`deposit-vault-hardening-wp0-evidence.md`](deposit-vault-hardening-wp0-evidence.md).
Findings are referenced by their DV identifier from that record.

> **PR #67 remediation candidate (11 August 2026).** The isolated candidate now
> enforces DV-04, DV-05, DV-07, DV-08, DV-09, DV-10, and DV-13 in contracts:
> AuctionHouse and CreditRedeem reject same-user collateral movement before a
> vault transfer is attempted; contributor
> durations are clamped without shortening a later refreshed lock; Teller
> blocks every housekeeping route during custody receipt measurement; zero asset weight now
> earns zero governance points; AuctionHouse measures each
> Stability Pool receipt across the collateral transfer; active-claim NAV fails
> closed if aggregate custody is deficient or any active claim is unpriced; and
> StabilityPool verifies exact recipient delivery before a withdrawal or claim
> can commit. Claim custody cannot be reclassified as stability backing.
> Exact-transfer/non-rebasing admission remains defense in depth, while the Teller
> callback-free token admission remains defense in depth. Dormant claim dust
> retains the explicit pre-exit operating disposition stated below.

> **Not covered here.** DV-01/02/03 (RipeGov privileged-caller breadth) was remediated
> in code — `depositTokensWithLockDuration`, `adjustLock` and `releaseLock` are now
> Teller-only. It needs no operating rule.

---

## 0. The rules at a glance

| # | Decision point | Rule | Status | Mitigates |
|---|---|---|---|---|
| 1 | Admitting any asset that can reach the Stability Pool | exact-transfer, non-rebasing, callback-free only | operational defense in depth | DV-08, DV-09, DV-10, DV-13 |
| 2 | Deploying a `Contributor` | contract clamps `depositLockDuration` to current bounds without shortening a later refreshed lock | enforced; configuration review remains defense in depth | DV-05 |
| 3 | Configuring a RipeGov vault asset | zero weight earns zero points | enforced | DV-07 |
| 4 | Pausing RipeGov | pause Teller in the same operation | operational | DV-06 |
| 5 | Registering a price source | it must never revert | operational | DV-14 |
| 6 | Changing AuctionHouse / CreditRedeem collateral routing | reject recipient-equals-user before calling a vault transfer | enforced at callers | DV-04 |

Rule 1 carries four findings on its own. It is the single most important item in
this document.

---

## 1. Claim-asset admission — exact transfer, no rebase, no callbacks

**Where it applies.** Any asset that can become collateral and therefore reach the
Stability Pool as a claim asset via `AuctionHouse.swapForLiquidatedCollateral`, and
any asset admitted as a stability asset. In practice: every asset you call
`setAssetConfig` on with `_shouldSwapInStabPools = True`.

**The rule.** Admit an asset only if all three hold:

1. **Exact transfer.** `transfer` and `transferFrom` move exactly the requested
   amount. No fee, no burn, no skim.
2. **Non-rebasing.** Balances never change except through explicit transfers. No
   rebase, no elastic supply, no admin burn against arbitrary holders.
3. **No transfer callbacks.** No ERC-777 / ERC-1363-style hook that hands control to
   another contract during `transfer` or `transferFrom`.

**Why each one matters.**

*Fee-on-transfer, inbound.* `StabVault._addClaimableBalance` retains an aggregate
custody check, but the only production liquidation caller is AuctionHouse. It now
measures the Stability Pool's claim-token balance immediately before and after the
collateral transfer and requires an exact `Q` delta before it reports `Q` to the pool.
A donation can still mask a short receipt only in a unit test that directly
impersonates AuctionHouse and bypasses that canonical transfer path; the production
composition reverts atomically (DV-08).

*Fee-on-transfer, outbound.* Withdrawal, claim, and non-auto-deposit redemption now
measure the recipient balance delta and require exact delivery before shares or
liability changes can commit. A fee/burn/skim therefore rolls the transaction back
(DV-13).

*Rebase or burn.* Every backing/NAV/withdrawal/liquidation-spend path now subtracts
aggregate claim liability from custody and fails closed when custody is below that
liability. A claim token cannot be admitted as a stability asset while any aggregate
claim liability exists, and a new claim cannot use an already-registered stability
asset. A deficit can no longer be valued or spent as if it were real backing (DV-09).

*Transfer callbacks.* While `Teller._deposit` measures the destination's custody
before and after a transfer, `Teller._performHousekeeping` now rejects every nested
custody-changing route while that receipt window is active. A callback cannot complete
a withdrawal, rebalance, redemption, liquidation, claim, deleverage, or nested deposit
inside the measurement. Callback-free admission remains required as defense in depth
for token-specific behavior outside the pinned route matrix (DV-10).

**The check, before calling `setAssetConfig`.**

- [ ] Read the token's `transfer` / `transferFrom` source. Confirm the recipient
      credit equals the argument, with no fee branch and no rounding.
- [ ] Confirm no `rebase`, `setSupply`, `burnFrom(arbitrary holder)`, or share-based
      balance accounting.
- [ ] Confirm no `tokensReceived` / `onTransferReceived` / registry hook, and no
      `raw_call` to the recipient inside the transfer path.
- [ ] For a proxy token, check the **implementation**, and confirm who can upgrade it.
      An upgradeable token can acquire any of these three behaviors later.
- [ ] Record the decision and the reviewed implementation address in the asset's
      config change notes.

**If a non-conforming asset must be admitted anyway,** the code now rejects the known
short-receipt, custody-deficit, claim/backing-overlap, and claim/withdrawal/direct-
redemption short-delivery cases. The non-GREEN stability-asset liquidation-proceeds
transfer still relies on exact-transfer admission. These checks are not a general
token-behavior proof: admission must still be reopened for token-specific callbacks,
upgrades, balance semantics, and any path outside the exact checks above.

---

## 2. Contributor deployment — keep `depositLockDuration` in bounds

**The rule.** Every deployed `Contributor` must carry a `depositLockDuration` inside
the RipeGov asset's `[minLockDuration, maxLockDuration]`.

**Enforced behavior.** `RipeGov.transferContributorRipeTokens` clamps the configured
duration into the current `[minLockDuration, maxLockDuration]`. It first refreshes the
recipient's existing unlock under the current terms; when that refreshed unlock is
later than the clamped duration, the later unlock is preserved. A contributor payout
therefore cannot shorten a still-effective recipient lock (DV-05).

**The check, at Contributor deployment.**

- [ ] Read the current terms: `MissionControl.ripeGovVaultConfig(ripeToken).lockTerms`.
- [ ] Assert `minLockDuration <= depositLockDuration <= maxLockDuration`.
- [ ] Re-check every existing Contributor whenever those governance bounds change —
      a bounds change can put an already-deployed Contributor out of range.

---

## 3. RipeGov asset config — zero weight is enforced

**Current behavior.** `assetWeight = 0` earns zero new governance points. No special
operating prohibition is needed for correctness.

**Why.** The candidate applies `newPoints * assetWeight / HUNDRED_PERCENT`
unconditionally. The former zero-weight bypass, which accidentally produced full
unweighted points, is removed (DV-07).

**Current state.** `DefaultsRobinhood` sets RIPE to `100_00`, so the launch
configuration is unaffected. This rule is about future governance actions.

**The check, before `setRipeGovVaultConfig`.** Record whether a zero weight is
intentional, because it stops future accrual for that asset; code and tests now make
that meaning exact.

---

## 4. Pausing RipeGov — pause Teller too

**The rule.** Any operation that pauses the RipeGov vault must also pause Teller, and
unpause them in the reverse order.

**Why.** `VaultData.isPaused` is only consulted by the SharesVault deposit, withdraw
and transfer helpers. `RipeGov.adjustLock` and `RipeGov.releaseLock` never read it —
and `releaseLock` reduces balances through `vaultData._reduceBalanceOnWithdrawal`
directly, bypassing the shares layer altogether. Both therefore stay fully live while
the vault is "paused", and `releaseLock` will burn a user's exit fee out of a paused
vault (DV-06).

Since the DV-01/02/03 remediation, both are reachable only through Teller, so pausing
Teller closes the path.

**The check, in any pause procedure.**

- [ ] Pause Teller **before or in the same transaction as** the vault.
- [ ] Confirm `teller.isPaused()` is true before treating the vault as quiesced.
- [ ] Note the exception: the migration and point-disable escapes are deliberately
      *not* pause-gated, so a paused vault can still be migrated or have point accrual
      disabled. That is intended recovery behavior.

The full per-method pause behavior is pinned by
`tests/vaults/test_ripe_gov_controls_and_migration.py::test_ripe_gov_pause_matrix_while_paused`.

---

## 5. Price sources — must never revert

**The rule.** Every contract registered in `PriceDesk` must return cleanly for every
asset and every input. It may return zero. It must not revert, and it must not return
malformed data.

**Why.** `PriceDesk._getPriceFromPriceSource` calls each registered source with a bare
`staticcall` and no failure isolation. One reverting source therefore propagates out
of **every** price query — including the non-raising `_shouldRaise = False` path that
the Stability Pool's NAV calculation relies on. Measured effect: a single reverting
source takes down `getTotalValue`, `getTotalUserValue`, deposit, withdrawal, claim and
prune (DV-14).

This is broader than the deposit vaults. It is a protocol-wide liveness property of
the price layer.

**Current candidate price policy.** Any nonzero active claim liability is part of its
cohort's NAV until settled. A zero price, absent feed, or reverting source therefore
fails NAV-dependent share movement closed. Price restoration resumes operation
without changing claim registration, liabilities, or historical shares.

**The check, before registering a price source.**

- [ ] Confirm `getPrice` and `getPriceAndHasFeed` cannot revert: no bare `assert`,
      no unchecked external call, no division by a value that can be zero, no array
      access that can be out of range.
- [ ] Confirm they return zero rather than reverting for an unknown asset.
- [ ] For a source that wraps a third-party oracle, confirm the wrapper catches the
      upstream failure instead of propagating it.

---

## 6. AuctionHouse / CreditRedeem — never emit a same-address vault transfer

**Enforced behavior.** AuctionHouse rejects an auction purchase when the buyer
recipient equals the liquidated user. CreditRedeem likewise rejects a
redemption recipient equal to the user whose collateral would move. These
checks run before AuctionHouse or CreditEngine can call
`transferBalanceWithinVault`. RipeGov does not duplicate this routing policy.

**The check, when changing seizure or liquidation routing.**

- [ ] Retain both caller-side recipient-equals-user checks.
- [ ] Add a caller-level regression for every new path that can reach
      `transferBalanceWithinVault`.

---

## 6b. Current StabilityPool contract disposition

The earlier no-change disposition is superseded by the PR #67 remediation
candidate. The final composition now includes all of the following:

- AuctionHouse measures the exact claim-token receipt across its collateral
  transfer before invoking StabilityPool;
- StabilityPool fails closed when aggregate claim custody is deficient;
- backing, NAV, withdrawals, and liquidation spending use custody net of claim
  liabilities;
- claim tokens and stability assets cannot overlap while either role is active;
- unavailable active-claim prices stop share movement without deleting claims;
  and
- withdrawal, claim, and direct redemption delivery is measured exactly at the
  recipient.

The exact constructor-bound candidate measured in the focused regression is
**24,313 deployed bytes**, leaving **263 bytes** below EIP-170. ABI and storage
layout are unchanged. The final artifact ledger must rebind this value from the
fully integrated source before release; this runbook measurement is not a
deployment identity.

Two boundaries remain explicit. First, direct unit-level impersonation of
AuctionHouse can bypass its call-local receipt measurement; production authority
and composition are what close that boundary. Second, dormant sub-threshold claim
dust remains directly claimable only while the owner still holds stability shares.
Its final product disposition is recorded separately rather than being hidden by
the completed DV-08/09/13 fixes.

### Dormant claim dust before final share exit

A sub-threshold dormant claim remains directly claimable while its owner still holds
stability shares, but there is intentionally no post-exit recovery ABI. Before burning
the final stability share, the UI/operator must enumerate and claim every claimable
balance, including dormant entries, and confirm the user's claimable balances read
back as zero. Final share exit must not be treated as complete until that check passes.
This is an accepted product workflow limitation, not a claim that dormant liabilities
become recoverable after exit.

---

## 7. What is verified in tests, and what is not

The table distinguishes passing contract-enforcement regressions from the single strict
expected-failure characterization that pins the accepted dormant-dust limitation.
Operational admission rules still require human review; tests cannot prove
that a newly admitted or upgraded token is exact-transfer, non-rebasing, or callback-
free.

| Rule | Test evidence | Status |
|---|---|---|
| 1 (inbound fee, donation) | `test_ah_liq_stab.py::test_stability_swap_rejects_donation_masked_short_receipt_from_shares_vault`, `test_stab_vault_hardening.py::test_direct_stability_pool_primitive_relies_on_auctionhouse_receipt_delta` | passing enforcement/composition regression |
| 1 (rebase / burn) | `test_stab_vault_hardening.py::test_active_claim_custody_deficit_fails_closed_for_value_extracting_actions`, `::test_claim_reserve_cannot_be_reclassified_as_stability_backing` | passing enforcement regression |
| 1 (outbound fee) | `::test_outbound_fee_on_transfer_short_delivery_reverts_atomically`, `::test_outbound_fee_on_transfer_stability_asset_does_not_burn_shares` | passing enforcement regression for the named paths |
| 1 (callbacks) | `test_teller_deposit.py::test_predeployment_undecorated_route_reentrancy_cross_product`, `::test_receipt_window_blocks_every_custody_changing_nested_route`, `::test_after_credit_callback_cannot_corrupt_the_measured_receipt` | passing central-guard regressions |
| 2 | `test_ripe_gov_controls_and_migration.py::test_contributor_duration_lands_clamped_on_a_fresh_recipient`, `::test_contributor_transfer_cannot_shorten_existing_lock` | passing enforcement regressions |
| 3 | `test_ripe_gov_vault.py::test_zero_asset_weight_means_zero_points`, `::test_nonzero_asset_weight_boundaries_are_exact` | passing policy regression |
| 4 | `test_ripe_gov_controls_and_migration.py::test_ripe_gov_pause_matrix_while_paused` | passing enforcement regression |
| 5 | `test_stab_vault_hardening.py::test_reverting_price_source_takes_down_every_nav_dependent_action` | passing enforcement regression |
| 6 | `test_ah_auction_mgmt.py::test_auction_buyer_cannot_be_liquidated_user`, `test_credit_redemptions.py::test_credit_redemption_recipient_equals_user` | passing caller-level enforcement regressions |
| Dormant dust | `test_stab_vault_hardening.py::test_dormant_dust_is_claimable_before_exit_but_stranded_after`, `::test_dormant_dust_remains_recoverable_after_full_exit` | first is passing characterization; post-exit recovery remains `xfail(strict=True)` by accepted product disposition |

The remaining `xfail(strict=True)` checkpoint records only the accepted dormant-dust
post-exit limitation. Completed DV-04/05/07/08/09/10/13 changes are ordinary passing
tests, not expected failures.
