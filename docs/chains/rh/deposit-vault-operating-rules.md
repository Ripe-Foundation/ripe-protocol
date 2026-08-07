# Deposit-Vault Operating Rules — RH

**Scope:** the operating conditions that the deposit-vault hardening review left as
*accepted residual risk* rather than contract changes. Each rule below is the thing
that makes an acceptance safe. If a rule is broken, the corresponding risk becomes
live in production.

This runbook documents operational procedure only. It authorizes no production
transaction.

Evidence and measurements: [`deposit-vault-hardening-wp0-evidence.md`](deposit-vault-hardening-wp0-evidence.md).
Findings are referenced by their DV identifier from that record.

> **Not covered here.** DV-01/02/03 (RipeGov privileged-caller breadth) was remediated
> in code — `depositTokensWithLockDuration`, `adjustLock` and `releaseLock` are now
> Teller-only. It needs no operating rule.

---

## 0. The rules at a glance

| # | Decision point | Rule | Mitigates |
|---|---|---|---|
| 1 | Admitting any asset that can reach the Stability Pool | exact-transfer, non-rebasing, callback-free only | DV-08, DV-09, DV-10, DV-13 |
| 2 | Deploying a `Contributor` | `depositLockDuration` inside `[minLockDuration, maxLockDuration]` | DV-05 |
| 3 | Configuring a RipeGov vault asset | never set `assetWeight = 0` | DV-07 |
| 4 | Pausing RipeGov | pause Teller in the same operation | DV-06 |
| 5 | Registering a price source | it must never revert | DV-14 |
| 6 | Changing AuctionHouse / CreditEngine seizure logic | never emit a same-address `transferBalanceWithinVault` | DV-04 |

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

*Fee-on-transfer, inbound.* `StabVault._addClaimableBalance` validates a settlement
receipt against the **aggregate** free surplus (`custody − totalClaimableBalances`),
not against a delta measured across the transaction. If anyone has donated `D` of the
token to the pool beforehand, a liquidation that declares `Q` while delivering `Q − D`
still passes the check. The donation is silently consumed and the pool books a
liability it cannot cover. Without a donation the guard fires correctly — the donation
is what defeats it (DV-08).

*Fee-on-transfer, outbound.* A claim burns the user's shares and clears the recorded
liability for the full amount, while `_handleAssetForUser` transfers out and never
measures what the recipient actually received. The difference is lost by the claimer
(DV-13).

*Rebase or burn.* Recorded liability stays fixed while custody shrinks. Only the
*activation* paths assert `custody >= priorLiability`; NAV, deposit and withdrawal do
not. The pool keeps valuing collateral that no longer exists and keeps accepting
deposits and withdrawals against that inflated number, socializing the shortfall
across every depositor in that stability asset (DV-09).

*Transfer callbacks.* While `Teller._deposit` measures the destination's custody
before and after a transfer, the mutex it sets is only read inside `_deposit` itself,
and `depositFromTrusted` / `depositIntoGovVault` are not `@nonreentrant`. A callback
fired mid-transfer can complete a nested withdrawal or liquidation against a different
vault and invalidate the measurement (DV-10).

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

**If a non-conforming asset must be admitted anyway,** the four accepted risks above
become live simultaneously. Reopen RH-CHANGE-01 first. Note the measured constraint:
StabilityPool has **205 bytes** of EIP-170 headroom, the preferred pull-and-measure
fix needs **+295**, and the custody-deficit and exact-delivery guards need **+78** and
**+151** — so at most one of them fits today, and the preferred one does not fit at
all. A size reduction has to come first.

---

## 2. Contributor deployment — keep `depositLockDuration` in bounds

**The rule.** Every deployed `Contributor` must carry a `depositLockDuration` inside
the RipeGov asset's `[minLockDuration, maxLockDuration]`.

**Why.** `RipeGov.transferContributorRipeTokens` forwards the configured duration
straight into `_getWeightedLockOnTokenDeposit` **without clamping it**. On a recipient
with no prior position the resulting unlock is exactly `block.number + duration` — so
a duration of 0 leaves the position immediately withdrawable, and a duration above the
maximum sticks. On a recipient who already holds a locked position, a large contributor
payout with a short duration drags their existing unlock down, and the result can land
**below** `minLockDuration` (DV-05).

**The check, at Contributor deployment.**

- [ ] Read the current terms: `MissionControl.ripeGovVaultConfig(ripeToken).lockTerms`.
- [ ] Assert `minLockDuration <= depositLockDuration <= maxLockDuration`.
- [ ] Re-check every existing Contributor whenever those governance bounds change —
      a bounds change can put an already-deployed Contributor out of range.

---

## 3. RipeGov asset config — never set `assetWeight = 0`

**The rule.** `assetWeight` must be nonzero on every asset configured for the RipeGov
vault.

**Why.** `RipeGov._getLatestGovPoints` guards the multiplier with `if _weight != 0`,
so a configured zero **skips the multiplication entirely** and produces the full
unweighted points — identical to 100.00%, the exact opposite of the intent (DV-07).

**Current state.** `DefaultsRobinhood` sets RIPE to `100_00`, so the launch
configuration is unaffected. This rule is about future governance actions.

**The check, before `setRipeGovVaultConfig`.**

- [ ] Assert `_assetWeight != 0`.
- [ ] To give an asset no governance weight, do **not** use zero. Remove the asset
      from the vault, or use the smallest meaningful nonzero weight and record why.

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

**Note on the accepted price policy.** SP-PRICE-01 option A says an unpriceable claim
asset is skipped from NAV while deposits and withdrawals stay live. That holds for a
**zero price** and for an **absent feed**. It does **not** hold for a source that
reverts — the whole vault stops. Do not treat the three cases as equivalent.

**The check, before registering a price source.**

- [ ] Confirm `getPrice` and `getPriceAndHasFeed` cannot revert: no bare `assert`,
      no unchecked external call, no division by a value that can be zero, no array
      access that can be out of range.
- [ ] Confirm they return zero rather than reverting for an unknown asset.
- [ ] For a source that wraps a third-party oracle, confirm the wrapper catches the
      upstream failure instead of propagating it.

---

## 6. AuctionHouse / CreditEngine — never emit a same-address vault transfer

**The rule.** Collateral-seizure logic must never call
`Vault.transferBalanceWithinVault` with `_fromUser == _toUser`.

**Why.** `RipeGov.transferBalanceWithinVault` has no owner-equals-recipient
short-circuit. A same-address move runs the full withdrawal-then-deposit governance
bookkeeping against one user: it burns the proportional point penalty and re-weights
the unlock toward `minLockDuration`. A **full** same-address transfer destroys the
user's entire point balance, because the withdrawal side reduces all points and the
caller passes `_shouldTransferPoints = False`, so nothing is credited back (DV-04).

**Current state.** Neither production caller produces this today. It is a latent
condition preserved by the callers, not by the vault.

**The check, when changing seizure or liquidation routing.**

- [ ] Confirm the liquidated user and the recipient can never be the same address on
      any path, including self-liquidation and any keeper-as-recipient flow.
- [ ] Zero-amount same-address transfers already fail closed
      (`no withdrawal amount`) — that corner is safe and is covered by
      `test_gov_same_user_zero_amount_transfer_reverts_without_state_change`.

---

## 7. What is verified in tests, and what is not

Every behavior above is pinned by a passing characterization test, so a future code
change that alters the behavior will fail CI. **No test enforces the operating rules
themselves** — nothing prevents an operator from admitting a fee-on-transfer token or
configuring a zero weight.

| Rule | Behavior pinned by |
|---|---|
| 1 (inbound fee, donation) | `test_stab_vault_hardening.py::test_preexisting_donation_masks_short_stability_receipt`, `::test_inbound_fee_on_transfer_settlement_reverts_atomically` |
| 1 (rebase / burn) | `::test_active_claim_custody_deficit_does_not_block_value_extracting_actions` |
| 1 (outbound fee) | `::test_outbound_fee_on_transfer_short_delivery_still_clears_the_liability` |
| 1 (callbacks) | `test_teller_deposit.py::test_predeployment_undecorated_route_reentrancy_cross_product`, `::test_after_credit_callback_cannot_corrupt_the_measured_receipt` |
| 2 | `test_ripe_gov_controls_and_migration.py::test_contributor_duration_lands_unclamped_on_a_fresh_recipient`, `::test_contributor_transfer_shortens_recipient_lock_below_minimum` |
| 3 | `test_ripe_gov_vault.py::test_zero_asset_weight_behaves_as_full_weight` |
| 4 | `test_ripe_gov_controls_and_migration.py::test_ripe_gov_pause_matrix_while_paused` |
| 5 | `test_stab_vault_hardening.py::test_reverting_price_source_takes_down_every_nav_dependent_action` |
| 6 | `test_ripe_gov_controls_and_migration.py::test_gov_same_user_transfer_mutates_lock_and_points` |

Each finding also carries an `xfail(strict=True)` checkpoint stating the invariant the
hardening plan wants. Those are the tests to un-skip if a rule is ever traded for a
contract change.
