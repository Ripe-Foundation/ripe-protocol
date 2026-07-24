# Stock Token Vault-Change Validation Plan

Status: **Phases D–E test contracts specified — not a finalized Phase J plan**

Date: 2026-07-23 (America/Denver)

This document keeps the Phase B invariant model, Phase C architecture
comparison, owner-authorized Phase D deposit design, and owner-authorized Phase
E backing/debt-health design testable. The owner selected option 4,
containment followed by the corrected share path, then rejected a new stored
per-asset collateral-use parameter and authorized Phase E specification using
existing deposit controls and `DebtTerms.ltv`. This is checkpoint option 4,
the combination of architecture outcomes 2 and 3, not the separately numbered
“another generic shared design.” All paths below are proposed future paths. No
test, fixture, mock, production contract, interface, dependency, CI file,
manifest, or ABI was created or changed. Both direct owner instructions are
preserved verbatim in `stock-token-vault-change-specification.md` Section 12.1.

The Phase D and E test contracts are now specific enough for later
implementation planning. The full Phase J plan cannot be finalized until the
owner resolves the later policy decisions in
`stock-token-vault-change-specification.md` Section 12.

## 1. Existing regression baseline

Existing file, unchanged:

```text
tests/vaults/test_stock_token_vault_comparison.py
```

Observed at starting commit
`be6a759e15e763b633feefdce91cf8f3ee31a10e`:

```text
PYTHONPATH=. pytest --collect-only -q \
  tests/vaults/test_stock_token_vault_comparison.py
=> 90 tests collected in 0.16s

PYTHONPATH=. pytest -q \
  tests/vaults/test_stock_token_vault_comparison.py
=> 90 passed in 51.98s
```

Checkpoint-review revalidation of that unchanged suite:

```text
PYTHONPATH=. pytest -q \
  tests/vaults/test_stock_token_vault_comparison.py
=> 90 passed in 53.85s
```

This suite remains evidence of current behavior. Unsafe assertions must not be
deleted or rewritten to make a future design appear safe. Future fix tests
should fail against the unsafe starting behavior where applicable and pass only
against the owner-approved shared implementation.

## 2. Proposed future test surfaces

| Proposed path | Layer | Primary components | Status |
| --- | --- | --- | --- |
| `tests/vaults/test_vault_receipt_accounting.py` | Vault/Teller unit | `CM-024`, `CM-025`, `CM-034`, `CM-045` | Proposed; Phase D behavior specified, implementation not approved |
| `tests/core/teller/test_teller_deposit_receipts.py` | Teller integration | `CM-034`, `CM-045`, every deposit entry point | Proposed; Phase D behavior specified, implementation not approved |
| `tests/vaults/modules/test_vault_loss_properties.py` | Math/property | `CM-024`, `CM-025` | Proposed; loss/rounding policy required |
| `tests/core/creditEngine/test_deficit_aware_credit.py` | CreditEngine | `CM-030`, `CM-009`, Ledger | Proposed; Phase E existing-controls behavior specified, implementation not approved |
| `tests/core/auctionHouse/test_loss_aware_auctions.py` | AuctionHouse | `CM-026`, `CM-030`, Ledger | Proposed; settlement and bad-debt policy required |
| `tests/core/deleverage/test_loss_aware_deleverage.py` | Teller/Deleverage | `CM-034`, `CM-044`, `CM-026` | Proposed |
| `tests/core/lootbox/test_vault_loss_rewards.py` | Rewards/monitoring | `CM-033`, `CM-025` | Proposed; rewards-unit decision required |
| `tests/config/test_asset_collateral_controls.py` | Governance/config | `CM-009`, `CM-011`–`CM-013`, existing config/getters | Proposed; Phase E no-new-storage control semantics specified |
| `tests/registries/test_vault_book_migration.py` | Migration | `CM-021`, vaults, Ledger, manifests | Proposed; pending Track 7 and owner migration policy |
| `tests/vaults/test_stock_token_vault_lifecycle.py` | Full lifecycle | all primary IDs | Proposed; production direction required |
| `tests/probes/test_aapl_vault_behavior_fork.py` | Exact-token fork | Track 2 AAPL + selected shared path | Proposed; no broadcast |

Likely reusable fixtures, subject to post-checkpoint design:

- existing `MockStockTokenControls`;
- ordinary 6- and 18-decimal ERC-20 fixtures;
- short-receipt/fee-on-transfer fixture;
- exact AAPL proxy fork fixture;
- two-user/two-buyer state builder;
- mixed solvent/deficit collateral builder;
- active-auction and existing-debt builders;
- Base and Robinhood clock profiles, **pending integrated S1**; and
- checked block-number inventory assertion, **pending integrated S2**.

## 3. Invariant-to-test map

| Invariant | Named future assertion | Proposed layer | Required result | Owner prerequisite |
| --- | --- | --- | --- | --- |
| I-01 exact receipt | `test_credit_equals_call_local_balance_delta` | Vault/Teller | `A`, `Q`, `R`, credited, returned, and emitted amounts reconcile; prior donation excluded | Phase D specified |
| I-01 exact receipt | `test_short_second_deposit_cannot_overcredit_either_path` | Vault/Teller | Both nominal and share paths credit only actual receipt | Phase D specified |
| I-02 borrowing conservation | `test_sum_borrow_amounts_never_exceeds_live_custody` | Property/Credit | Invariant holds across users, deposits, losses, and withdrawals | Architecture |
| I-03 claim conservation | `test_all_withdrawal_orders_are_custody_bounded` | Property/Vault | Two-user orders cannot allocate more than custody | Loss allocation |
| I-03 claim conservation | `test_two_buyers_cannot_allocate_same_remaining_custody` | Auction | Both purchase orders conserve custody | Settlement model |
| I-04 pay for delivery | `test_green_and_debt_commit_only_after_actual_delivery` | Auction/Deleverage | Payment/debt value is bounded by delivered amount/value | Settlement policy |
| I-05 atomic failure | `test_pause_blocklist_false_return_and_revert_leave_state_unchanged` | Vault/Auction | Balances, debt, GREEN, rewards, and auction state unchanged | External-only policy |
| I-06 deficit visibility | `test_zero_borrow_value_does_not_erase_existing_debt_terms` | Credit | Deficit remains resolution/liquidation-visible | Phase E specified |
| I-06 deficit visibility | `test_mixed_collateral_preserves_solvent_terms_and_unsafe_debt_signal` | Credit | Solvent collateral remains valued; deficit cannot create false health | Phase E specified |
| I-07 no new unsafe debt | `test_one_unit_deficit_contributes_zero_new_capacity` | Credit | Preview and state-changing borrow match and return/revert safely | Phase E specified |
| I-07 no new unsafe debt | `test_disabled_asset_cannot_support_new_borrow` | Governance/Credit | Existing fast disable affects every credit surface | Phase E specified |
| I-08 exactly once | `test_total_loss_moves_liability_to_bad_debt_exactly_once` | Credit/Auction/Ledger | User debt decreases by `x`, bad debt increases by `x`, repeat is no-op/revert | Bad-debt policy |
| I-08 exactly once | `test_repayment_race_uses_one_pinned_debt_state` | Credit/Ledger | Repay and transition cannot duplicate or lose liability | Bad-debt policy |
| I-09 repay liveness | `test_repayment_remains_available_during_deficit_freeze` | Credit/Teller | Repay succeeds while borrow/deposit/settlement are frozen | Product direction |
| I-10 post-zero | `test_new_deposit_reverts_while_old_shares_exist_at_zero` | Share vault | No new shares or value transfer | Freeze/recap decision |
| I-10 post-zero | `test_restoration_has_only_owner_approved_allocation` | Share/property | No automatic capture by old/new users outside selected policy | Donation policy |
| I-11 external-only | `test_issuer_asset_rejects_buyer_internal_override` | Auction/config | Internal mode unavailable; external delivery enforced | Settlement policy |
| I-12 price independence | `test_deficit_guard_survives_missing_or_zero_price` | Credit | Custody status remains visible and fail-closed without price | Phase E specified |

## 4. Sixteen-state matrix

| State | Named future test(s) | Core diagnostics |
| --- | --- | --- |
| Solvent ordinary | `test_ordinary_lifecycle_6_decimals`, `test_ordinary_lifecycle_18_decimals`, `test_one_base_unit_lifecycle` | `C`, accounting, claim, credit, delivery, events |
| Pre-existing donation | `test_preexisting_donation_is_not_depositor_receipt` | before/after custody, `R`, credited amount |
| Donation between deposits | `test_between_deposit_donation_is_not_second_receipt` | both users' accounting/claims, surplus |
| Short receipt / fee | `test_short_receipt`, `test_fee_on_transfer_receipt` | requested/received/credited/event amounts |
| Partial issuer reduction | `test_partial_admin_burn_pro_rata_or_freeze` | `C`, `δ`, shares/nominal, credit, delivery |
| Aggregate nominal deficit | `test_nominal_deficit_propagates_to_health` | deficit status, weighted terms, max borrow |
| Total custody loss | `test_total_loss_no_paid_auction`, `test_total_loss_bad_debt_once` | debt, bad debt, auctions, GREEN |
| Zero custody/nonzero shares | `test_zero_custody_old_shares_freeze` | raw shares, `Z`, rejected deposit/withdraw |
| Restoration after zero | `test_post_zero_restoration_policy` | source/amount/allocation event and claims |
| New deposit after zero | `test_post_zero_new_deposit_reverts_atomically` | custody/accounting/shares unchanged |
| Paused transfer | `test_paused_deposit_withdraw_and_settlement_atomicity` | state roots or all relevant balances/state |
| Sender/recipient/operator blocklist | parameterized `test_blocklist_role_atomicity` | actor role, revert reason, unchanged state |
| Active auction before action | `test_active_auction_revalidates_after_loss` | pre/post custody, auction progress, buyer GREEN |
| Liquidation after action | `test_post_loss_liquidation_uses_resolution_not_zero_auction` | health, auction count, debt resolution state |
| Implementation/beacon change | `test_behavior_switch_fails_closed_until_reenabled` | implementation identity, flags, receipt/delivery |
| Recovery/migration with debt | `test_live_state_migration_reconciles_or_aborts` | users, assets, custody, raw accounting, debt, auctions, registry |

Each test must separately report safety and liveness. A passing revert assertion
is not evidence that debt can progress.

## 5. Architecture-specific matrices

### 5.1 Outcome 1 — no listing

- Assert Stock Token addresses are absent or disabled for deposit, collateral
  use, auction purchase, redemption, and unsupported integrations.
- Preserve the Base regression suite.
- No exact-token custody lifecycle is a launch gate because the feature is not
  listed.

### 5.2 Outcome 2 — containment

Required future matrix:

- nominal exact receipt at first and later deposits;
- one-unit, partial, and total deficit;
- preview/state-changing borrow equivalence;
- mixed solvent and deficit collateral;
- existing debt with zero affected borrowing value;
- internal transfer guard;
- no new zero-backed auction;
- repayment during freeze;
- per-asset disable/re-enable permissions; and
- Base old/new version migration and reconciliation.

Containment does not pass the permanent total-loss/post-zero matrix unless the
owner expands its scope.

### 5.3 Outcome 3 — corrected share path

Required future property matrix:

- `Σ claims <= C` for arbitrary user share vectors;
- both two-user withdrawal orders;
- both two-buyer settlement orders;
- partial loss from one unit through `C-1`;
- total loss with nonzero `S`;
- donation before first deposit and between deposits;
- restoration and attempted fresh deposit after zero;
- amount→shares round down for deposit and round up where needed for bounded
  withdrawal;
- 6- and 18-decimal minimum-positive deposits;
- `DECIMAL_OFFSET` and virtual-asset dust bounds;
- raw shares versus live claims in rewards, events, getters, and reports; and
- migration from nominal and prior share versions.

### 5.4 Standing configuration assertions for every listed outcome

The following future assertions are mandatory and are not reopened by the vault
architecture choice:

- `test_stock_token_redeem_collateral_stays_disabled`: stored
  `AssetConfig.canRedeemCollateral` and
  `MissionControl.getRedeemCollateralConfig()` both remain false for every
  Stock Token.
- `test_stock_token_stability_pool_swap_stays_disabled`:
  `shouldSwapInStabPools` remains false unless a separate governance decision
  explicitly accepts issuer-controlled Stability Pool custody.
- `test_stock_token_has_no_unsupported_routes`: no Base treasury, Endaoment
  partner-liquidity, Curve, Aerodrome, Underscore, yield, or other unsupported
  integration is reachable.
- `test_stock_token_features_default_disabled_until_gates`: deposit,
  collateral use/borrowing, auction purchase, and any retained internal
  settlement remain disabled until their exact gates close.
- `test_auction_house_nft_is_not_a_fungible_consumer`: current `CM-027`
  remains outside the fungible path; any future implementation that calls the
  common Vault interface must fail the checked consumer inventory until
  dispositioned.

Proposed home: `tests/config/test_asset_collateral_controls.py`, with the
consumer-inventory assertion also eligible for the future S2 checked-inventory
test.

## 6. Phase D deposit-accounting validation contract

This section is normative for later implementation. It validates the Teller
boundary selected in specification Section 14 without approving production
changes now.

### 6.1 Measurement and conservation matrix

For every successful case, capture:

```text
A = raw Teller input
Q = post-validation transfer attempt
C0 = vault custody immediately before transfer
C1 = vault custody immediately after transfer
R = C1 - C0
V = vault return / credited amount
C2 = vault custody after credit
C3 = vault custody after post-credit external work and before success events
```

and assert:

```text
0 < R <= Q <= A
V == R
C1 == C0 + R
C2 == C1
C3 == C1
existing Teller/vault deposit event amount == R
TellerDepositMeasured == (A, Q, R, V, vault, vaultId)
```

The `Q <= A` comparison remains literal when `A` is
`max_value(uint256)`; the test must also show the source-balance/limit cap that
produced `Q`.

Required cases in
`tests/vaults/test_vault_receipt_accounting.py` and
`tests/core/teller/test_teller_deposit_receipts.py`:

| Test | Setup | Required result |
| --- | --- | --- |
| `test_ordinary_receipt_reconciles_all_amounts` | Ordinary token; `A == Q` | `R == Q == V`; all applicable events reconcile. |
| `test_max_request_records_capped_transfer_attempt` | `A = max_value`; finite balance/limit | Event preserves `A`, records capped `Q`, and credits measured `R`. |
| `test_preexisting_donation_is_not_depositor_receipt` | Donate `D` before call | `C0` includes `D`; only current call delta `R` is credited. |
| `test_between_deposit_donation_is_not_second_receipt` | Deposit, donate, deposit again | Neither user's credit absorbs the donation; each call has an independent `C0`. |
| `test_short_first_deposit_credits_only_receipt` | Transfer receives `0 < R < Q` | Simple and share paths credit/return/emit `R`, not `Q`. |
| `test_short_second_deposit_cannot_overcredit_either_path` | Existing user/accounting plus `0 < R < Q` | No aggregate-balance clamp overcredits the second depositor and no accounted deficit is created. |
| `test_fee_on_transfer_receipt_is_measured` | Fee-token transfer | General deposit succeeds for net `R`; fee is not credited. |
| `test_zero_receipt_reverts_atomically` | Successful-looking transfer with no vault receipt | No custody/accounting/registration/points/snapshot/event change persists. |
| `test_negative_delta_reverts_before_subtraction` | Transfer callback burns existing vault custody | Whole transaction reverts; depositor receives no accounting and existing state is restored. |
| `test_excess_delta_reverts_without_capping` | Transfer callback creates `R > Q` | Whole transaction reverts; no surplus is silently assigned. |
| `test_false_return_and_token_revert_are_atomic` | False-return and revert variants | Identical pre/post protocol state and no successful event. |
| `test_no_return_token_still_requires_positive_delta` | No-return token variants | Ordinary receipt succeeds; zero/invalid delta fails. |
| `test_vault_return_mismatch_reverts` | Vault test double returns `V != R` | Whole transaction reverts. |
| `test_vault_credit_cannot_mutate_custody` | Vault test double changes token balance during credit | `C2 != C1` reverts. |
| `test_postcredit_callback_cannot_mutate_custody` | Ledger/Lootbox/housekeeping/PriceDesk test double changes custody | `C3 != C1` reverts before success events. |
| `test_ordinary_housekeeping_enabled_deposit_preserves_custody_and_succeeds` | Ordinary deposit with real Ledger, Lootbox, housekeeping, and PriceDesk paths enabled | `C3 == C1`; credit and success events complete, proving the guard does not break the pinned ordinary path. |

The short-receipt cases must run against both Simple/Basic and
Rebase/Shares-backed wrappers. At minimum, include 6-decimal, 18-decimal, and
one-base-unit ordinary-token cases.

Implementation review must repeat a call-graph inventory of every operation
between `C2` and `C3` and confirm none legitimately moves the target vault's
measured asset. The positive liveness test above and the mutation-revert test
are a required pair; either one alone is insufficient.

### 6.2 Reentrancy, callback, and behavior-change matrix

The deposit lock requires adversarial tests, not only a happy-path annotation:

| Test | Required result |
| --- | --- |
| `test_nonreentrant_claim_may_enter_first_trusted_deposit` | A legitimate nonreentrant Teller claim → StabVault → `depositFromTrusted` callback can begin one `_deposit`; it is not rejected merely because the outer Teller function is guarded. |
| `test_transfer_callback_cannot_reenter_same_deposit` | Callback into the same asset/vault deposit fails and the outer call cannot credit combined receipts. |
| `test_transfer_callback_cannot_reenter_other_deposit` | Callback into another asset or vault is also rejected while the shared deposit mutex is held. |
| `test_vault_callback_cannot_open_nested_deposit` | Nested entry during the vault credit call fails. |
| `test_batch_final_housekeeping_cannot_reenter_deposit` | `depositMany` retains one mutex through its final housekeeping and rejects a nested trusted deposit. |
| `test_rebalance_retains_deposit_mutex_through_withdrawal` | A withdrawal callback cannot open a nested deposit before rebalance's final health check and return. |
| `test_failed_nested_callback_is_fully_atomic` | If callback failure bubbles, token balances, accounting, points, Ledger participation, price snapshot, and events equal pre-state. |
| `test_transfer_time_behavior_switch_revalidates_delta` | A proxy/mock behavior change during transfer cannot bypass zero, negative, or excess checks. |
| `test_transfer_coupled_unrelated_mutation_is_unsupported` | A mock demonstrates the documented observational limit; asset enablement must fail unless its behavior gate excludes unrelated custody mutation. |

The first case is mandatory because placing the existing global
`@nonreentrant` guard directly on `depositFromTrusted` would break this
legitimate call graph. The remaining cases prove that the dedicated mutex
protects the measurement window across every deposit entry point.

The other-asset/other-vault case must assert the selected policy, not treat the
failure as an accidental limitation: the mutex is global across Teller
deposits, the nested cross-asset deposit fails closed, and the caller may retry
it only as a separate transaction after the outer deposit completes.

### 6.3 Limit, minimum, rounding, and post-credit ordering

| Test | Required result |
| --- | --- |
| `test_short_receipt_cannot_exceed_user_or_global_limit` | `Q` is pre-capped and `R <= Q`; final credited state remains within both upper limits. |
| `test_short_receipt_rechecks_minimum_on_live_balance` | If final live user amount after credit is below `minDepositBalance`, the non-trusted deposit reverts atomically. |
| `test_trusted_deposit_is_measured_despite_limit_exemption` | Trusted flow skips current user/global/min policy but still proves `0 < R <= Q` and `V == R`. |
| `test_share_deposit_uses_predeposit_custody_and_rounds_down` | Shares equal `floor(R * (S + 10^8) / (C0 + 1))`, never a formula using `Q` or aggregate post-custody as the call receipt. |
| `test_positive_receipt_that_mints_zero_shares_reverts` | No positive custody can be donated through zero-share credit. |
| `test_stab_vault_uses_measured_receipt_without_economic_drift` | GREEN/sGREEN value, claimable-value, virtual-offset, and existing share rules are unchanged except for the verified receipt input. |
| `test_registration_occurs_only_after_credit` | Failed/zero credit cannot add Ledger participation. |
| `test_points_read_postcredit_balance` | Lootbox input state reflects shares/nominal credit from `R`. |
| `test_price_snapshot_occurs_after_measured_credit` | Snapshot is absent on failure and sees the successful post-credit state. |
| `test_deposit_many_measures_each_item_and_is_atomic` | Independent `(C0,C1,R,V,C2,C3)` per item; one failed item rolls back all items and final housekeeping. |
| `test_rebalance_uses_received_deposit_amount` | `TellerRebalance.depositAmount == R`; deposit, withdrawal, and final health check are atomic. |

Phase G may replace the permanent share formula after its loss/post-zero policy
is approved. Until then, these tests pin Phase D's receipt input and rounding
direction without purporting to approve the current formula as the permanent
architecture.

### 6.4 Consumer exactness and compatibility

The following integration assertions are mandatory:

| Proposed existing/new test surface | Assertion |
| --- | --- |
| `tests/core/teller/test_teller_deposit.py` | `deposit` and `depositIntoGovVault` return/emit measured `R`; `depositMany` preserves its count return and emits measured `R` for every item. |
| `tests/core/teller/test_teller_rebalance.py` | Rebalance event and return use `R`. |
| `tests/vaults/modules/test_stab_vault.py` | Ordinary GREEN/sGREEN regression yields `R == Q` and retains current economics; measured `R` remains the accounting input if behavior changes. |
| `tests/vaults/modules/test_stab_vault_claims.py` | Collateral claim auto-deposit may accept short `R`; claim-routed amount and vault-credit amount remain explicitly distinct. RIPE reward stake requires exact receipt. |
| `tests/vaults/test_ripe_gov_vault.py` | Teller-measured `R` drives shares, lock, points, and event; direct production deposit authorization is Teller-only. |
| `tests/core/deleverage/test_deleverage_swap_collateral.py` | Swap reverts unless Teller return equals calculated deposit amount; successful event uses verified `R`. |
| `tests/core/bondRoom/test_ripe_bonds.py` | RIPE payout/stake reverts on short receipt. |
| `tests/core/lootbox/test_loot_ripe_rewards.py` | RIPE reward stake reverts on short receipt. |
| `tests/core/humanResources/test_hr_contributor.py` | RIPE compensation stake reverts on short receipt. |
| `tests/core/creditEngine/test_credit_repay.py` | Any CreditEngine sGREEN recipient deposit requires exact receipt. |
| `tests/core/creditEngine/test_credit_redemptions.py` | Any CreditRedeem sGREEN recipient deposit requires exact receipt. |

For every exact path, inject both `Q < A` source-capping and `R < Q`
short-receipt results. Prove the caller compares Teller's return with `A` and
the entire upstream transaction rolls back, including minted/accrued payout
state, withdrawn claim state, approvals, housekeeping, and events. For the one
measured trusted exception, StabVault collateral-claim auto-deposit, prove only
`R` becomes vault credit and the Teller event exposes both `Q` and `R`.

### 6.5 Event and ABI compatibility checks

Required assertions:

- existing function selectors and return shapes are unchanged;
- existing successful-deposit event signatures are unchanged;
- `TellerDeposit.amount`, `SimpleErc20VaultDeposit.amount`,
  `RebaseErc20VaultDeposit.amount`, `StabilityPoolDeposit.amount`, and
  `RipeGovVaultDeposit.amount` equal `R`;
- share-event fields equal shares actually minted from `R`;
- exactly one `TellerDepositMeasured` and one existing `TellerDeposit` are
  emitted per successful `_deposit` item, in that order;
- no success event is emitted on a reverted deposit;
- `inputAmount`, `transferAmount`, `receivedAmount`, and `creditedAmount` map
  exactly to `A`, `Q`, `R`, and `V`; and
- every production deposit call enters through Teller. A checked caller
  inventory must fail if a new direct vault depositor appears.

### 6.6 Phase D implementation acceptance

A future Phase D implementation cannot be accepted unless:

1. all tests in Sections 6.1–6.5 pass;
2. the unchanged 90-case comparison suite still passes and unsafe historical
   behavior remains clearly labeled as evidence rather than a desired result;
3. full repository regression passes;
4. the diff contains no asset-name, issuer, vault-ID, or chain-ID behavior
   branch;
5. the integrated-source call graph proves that all operations between `C2`
   and `C3` preserve measured custody, with both the positive housekeeping
   liveness case and negative mutation case passing;
6. generated ABI/interface consequences are reviewed under the later Phase I
   inventory; and
7. the owner separately authorizes implementation.

These are future acceptance conditions, not evidence that any implementation
now exists.

## 7. Phase E backing and debt-health validation contract

All tests in this section are proposed. They specify future acceptance
behavior; no test or implementation is authorized by this document.

### 7.1 Existing-control and no-new-schema matrix

| Named future assertion | Setup | Required result |
| --- | --- | --- |
| `test_asset_config_and_debt_terms_layout_unchanged` | Compare pre/post `AssetConfig`, `DebtTerms`, MissionControl storage, canonical interfaces, selectors, and ABI | No new stored field, external getter/setter, selector, event, default, or migration; existing tuple layouts remain identical |
| `test_existing_can_deposit_is_fast_disable_and_governance_reenable` | Governance and authorized lite actor each attempt disable/re-enable | Lite actor may set per-asset `canDeposit=false`; only governance may restore `true`; `CanDepositAssetSet` proves asset/value/caller |
| `test_per_asset_disable_blocks_deposit_and_new_credit` | Solvent asset with nonzero LTV and existing user collateral | `canDeposit=false` rejects new deposit and makes the asset's new-borrow contribution zero across preview and state-changing validation |
| `test_general_deposit_pause_does_not_zero_all_collateral` | Set general `GenConfig.canDeposit=false` while per-asset flags and backing remain safe | Deposits pause, but existing per-asset credit capacity and health do not change solely because of the general maintenance switch |
| `test_disable_does_not_mutate_debt_terms` | Record all six `DebtTerms`, disable and re-enable deposits | LTV, redemption threshold, liquidation threshold, fee, rate, and daowry are byte-for-byte unchanged |
| `test_ltv_zero_remains_prelaunch_non_collateral` | Backing-safe asset with `canDeposit=true`, `ltv=0` | Deposits may follow existing config, but the asset adds zero borrow capacity and no artificial resolution terms |
| `test_deposit_limits_bound_admission_not_existing_value` | Change per-user/global/minimum deposit parameters around an existing position | Deposit validation changes as configured; existing collateral value/health is not recalculated from the limits |
| `test_nonzero_to_zero_ltv_guard_is_unchanged` | Existing nonzero LTV; attempt direct zero through SwitchboardBravo | Existing guarded/pending behavior remains; the emergency path is `canDeposit=false`, not an LTV bypass |

### 7.2 Automatic backing matrix

| Named future assertion | Setup | Required result |
| --- | --- | --- |
| `test_one_unit_simple_deficit_zeroes_every_users_capacity` | Two or more Simple users; reduce aggregate custody from `T` to `T-1` | Every user of that `(vault, asset)` contributes zero, regardless of position size or enumeration order |
| `test_nominal_deficit_never_uses_min_user_nominal_live_total` | Two nominal claims each individually `<= C`, but `sum claims > C` | Neither claim is treated as backed by `min(userNominal,C)`; both are frozen for new capacity |
| `test_simple_surplus_is_safe_but_not_user_allocated` | Donate so `C>T` | Backing check passes; existing nominal amounts remain unchanged; the surplus is not added to any user's amount |
| `test_simple_exact_backing_preserves_existing_capacity` | `C==T`, enabled, valid price | Existing user values and `amount * price * ltv` capacities are unchanged |
| `test_share_partial_loss_uses_live_round_down_claims` | Two share users, partial custody reduction | Each user's capacity uses its live pro-rata claim; sum of live claims and resulting delivery allocation is custody-bounded |
| `test_nonzero_shares_zero_claim_is_not_skipped` | Nonzero user shares whose live round-down amount is zero | Asset remains identified, capacity/collateral value are zero, and configured resolution terms remain present |
| `test_total_loss_share_position_is_visible_without_new_getter` | Nonzero shares and `C=0` | Existing indexed asset/amount getter is sufficient to expose `(asset,0)`; no new external status selector is required |
| `test_backing_is_isolated_per_vault_and_asset` | Same asset in two vaults; deficit only one vault | Only the deficient `(vault,asset)` contribution is automatically zero; the other vault's distinct custody is counted once |
| `test_backing_read_failure_never_returns_positive_capacity` | Make token `balanceOf` or Vault total read fail/malformed | State-changing borrow reverts; preview returns zero or fails, never a positive optimistic amount |
| `test_stability_pool_empty_asset_signal_remains_excluded` | User has StabilityPool and ordinary vault positions | `(empty,0)` StabilityPool entry remains outside CreditEngine collateral; the ordinary entry follows Phase E rules |

### 7.3 Preview, borrow, health, liquidation, and repayment matrix

| Named future assertion | Setup | Required result |
| --- | --- | --- |
| `test_preview_and_borrow_share_identical_phase_e_capacity` | Snapshot state with safe, disabled, and deficit positions | At unchanged state and valid prices, preview and state-changing validation derive identical per-position and aggregate capacity |
| `test_preview_never_optimistic_when_borrow_would_revert` | Required safe-asset price invalid or backing read fails | Preview is zero/failing, never positive while the matching borrow fails |
| `test_disabled_solvent_asset_has_zero_capacity_but_live_resolution_value` | `C>=T`, valid price, nonzero LTV, then `canDeposit=false` | New-borrow contribution is zero; safely deliverable existing collateral remains in liquidation/redemption value and uses its configured terms |
| `test_deficit_cannot_appear_healthy_via_amount_zero_skip` | Existing debt supported only by a now-zero-claim or deficient asset | `hasGoodDebtHealth` is false; the unsafe entry is processed rather than skipped |
| `test_deficit_preserves_nonzero_liquidation_terms` | Existing debt and only configured asset becomes fully missing | Collateral value/capacity are zero, but configured liquidation threshold remains nonzero and `canLiquidateUser` is not false merely because amount is zero |
| `test_mixed_collateral_preserves_exact_solvent_capacity` | One deficient position and one unrelated solvent/enabled/priced position | Unsafe contribution is zero; solvent value and capacity exactly equal the single-position control case |
| `test_mixed_collateral_health_uses_only_actual_capacity` | Vary debt below/above the solvent position's capacity | Health is true only when unrelated eligible collateral alone covers debt |
| `test_missing_price_cannot_hide_deficit` | Deficit position with stale, zero, or missing price | Deficit remains fail-closed and terms remain visible without a price call |
| `test_safe_missing_price_is_independently_fail_closed` | Backing-safe enabled position with invalid price | Preview/health give no optimistic value; state-changing borrow reverts under the existing raising mode |
| `test_repayment_succeeds_without_unsafe_asset_price` | Existing debt, known disabled/deficit position, unusable price | Repayment reduces Ledger debt, updates conservatively, and does not require the unsafe asset price |
| `test_repayment_does_not_clear_or_allocate_deficit` | Repay during deficit freeze | Debt decreases only by paid amount; custody/accounting and deficit state are unchanged; no bad debt is created |
| `test_max_withdraw_preview_uses_same_backing_state` | Existing debt with disabled or deficient target asset | Preview returns zero for unsafe collateral and uses exact Phase E contributions for remaining assets |
| `test_debt_free_solvent_disabled_asset_keeps_normal_exit` | No user debt, `C>=T`, per-asset deposits disabled, withdrawals enabled | CreditEngine does not unnecessarily block ordinary solvent exit; Teller/Vault withdrawal controls remain authoritative |

### 7.4 Conservation and property matrix

Property/state-machine runs must cover 6- and 18-decimal assets, one-base-unit
amounts, multiple users, multiple vaults, reordered user/asset enumeration,
donations, partial and total loss, disable/re-enable, stale prices, borrow,
repay, and withdrawal preview.

Required properties:

```text
nominal C < T
    => capacity(user, vault, asset) == 0 for every user

nominal C >= T
    => sum(user nominal claims) == T <= C

shares
    => sum(roundDown(user live claims)) <= C

totalMaxDebt
    == sum(each eligible position's live value * configured LTV)

disabled or unsafe position
    => new-capacity contribution == 0

preview(state) > 0
    => state-changing validation at identical state cannot reject because of
       a different backing/config calculation
```

Named assertions:

- `test_sum_borrow_amounts_never_exceeds_live_custody`;
- `test_user_and_vault_iteration_order_cannot_allocate_nominal_deficit`;
- `test_same_asset_two_vaults_never_share_backing`;
- `test_donation_deficit_and_restore_sequence_never_double_counts`;
- `test_disabled_asset_capacity_is_zero_for_every_user`;
- `test_safe_mixed_collateral_matches_isolated_control`; and
- `test_phase_e_state_machine_preserves_i02_i06_i07_i09_i12`.

Restoring `C>=T` does not itself authorize re-enable, loss allocation, or
post-zero deposits. Those remain governance/policy gates.

### 7.5 Monitoring and event evidence

At one pinned block, future diagnostics must record:

```text
assetConfig(asset).canDeposit
getDebtTerms(asset)
IERC20(asset).balanceOf(vault)
Vault(vault).getTotalAmountForVault(asset)
Vault(vault).getUserAssetAndAmountAtIndex(user,index)
CreditEngine.getMaxBorrowAmount(user)
CreditEngine.hasGoodDebtHealth(user)
CreditEngine.canLiquidateUser(user)
```

Required assertions:

- `test_same_block_getter_bundle_reconstructs_backing_and_capacity`;
- `test_can_deposit_event_matches_applied_asset_config`;
- `test_pending_and_applied_debt_term_events_match_getter`;
- `test_no_stored_deficit_bit_can_disagree_with_live_backing`; and
- `test_monitoring_labels_read_failure_unknown_not_solvent`.

The bundle must record block number/hash, vault/asset/user identities, raw
responses, decoded values, and derived `C<T`, zero-claim, eligibility, value,
capacity, and health results. Event evidence proves config transitions; live
getters prove current backing.

### 7.6 Phase E implementation acceptance

A future Phase E implementation cannot be accepted unless:

1. all tests in Sections 7.1–7.5 pass;
2. the Phase D deposit tests and unchanged 90-case comparison baseline pass;
3. full repository regression passes;
4. no new storage/config field, canonical interface method, external selector,
   event, ABI, default, migration, or manifest change appears;
5. the implementation consumes existing `canDeposit` and `DebtTerms.ltv`
   exactly as specified and does not weaken existing role/timelock rules;
6. backing classification is call-time, oracle-independent, and generic;
7. every CreditEngine preview/state/health/repay/withdraw consumer is covered;
8. source and tests contain no asset-name, issuer, vault-ID, or chain-ID branch;
9. security review accepts the deliberate coupling between per-asset deposit
   disable and zero new-borrow support; and
10. the owner separately authorizes implementation.

These are future acceptance conditions, not evidence that any implementation
exists. Phase F settlement and bad-debt behavior remains separately gated.

## 8. Exact-token fork plan

Proposed future file:
`tests/probes/test_aapl_vault_behavior_fork.py`.

Use the integrated Track 2 fork facts:

- Robinhood chain ID: `4663`
- pinned block: `17,558,441`
- pinned block hash:
  `0x35e8e2a3803cb42c4553cb5f3528b187508c6cc200a8b761943374003b8f0243`
- AAPL proxy: `0xaF3D76f1834A1d425780943C99Ea8A608f8a93f9`
- beacon/registry: `0xe10b6f6B275de231345c20D14Ab812db62151b00`
- implementation:
  `0xb35490d6f9163DE4F80d88dc75c3516eb64C5aE2`
- implementation code hash:
  `0xdc07e86ee482f99641bdafb9a0d772846b167401e094d90a666b94dbdcd1eec7`
- 18 decimals and test amount `0.001 AAPL`

Required fork cases after an implementation exists:

1. ordinary approve/deposit/repay/withdraw lifecycle;
2. exact receipt and event reconciliation;
3. token pause and oracle-pause independence;
4. sender, vault/recipient, and operator blocklists;
5. administrative partial and total burn/forced reduction;
6. multiplier changes without applying the UI multiplier twice;
7. implementation behavior switch;
8. external-only auction delivery;
9. total-loss repayment and exactly-once resolution; and
10. post-zero freeze/restoration policy.

No live signing or broadcast is part of this plan. Live sender/recipient
eligibility, acquisition, gas, approvals, and legal permission remain separate
owner/counsel gates.

## 9. Dual-clock and identical-artifact integration

The narrow S1/S2 kickoff choices were owner-approved in post-bootstrap
integration commit `ce3805d6079ee87d727486ea82b75cbddc12e46d`. Their implementation
artifacts remain pending. Once integrated:

- run the same compiled artifacts under Base and Robinhood profiles;
- exercise repeated `block.number`, `+1`, and multi-number jumps;
- verify emergency disable, timelocked/stronger re-enable, auctions, debt
  transition, registry changes, and migration sequencing;
- assert no `chain.id` or issuer-name behavior branch;
- run the checked `block.number` inventory enforcement; and
- record source hash, creation/runtime hash, constructor/config differences,
  and approved live-version exceptions.

Clock behavior must not change custody conservation. Repeated or jumping numbers
may delay a timelock or auction but cannot permit payment for undelivered
collateral or duplicate bad debt.

## 10. Migration validation scaffold

Pending owner live-version policy and Track 7 namespace/tooling:

1. pin old/new source, runtime, registry, and manifest identities;
2. enumerate every old-vault asset/user plus `C`, nominal/shares, claims, debt,
   rewards, and active auctions;
3. disable old deposits before movement;
4. prove debt and auction behavior is frozen or safely serviced during the
   window;
5. move/re-register custody and user state only through the approved procedure;
6. reconcile aggregate and per-user state before registry activation;
7. abort on any mismatch without leaving two authoritative claim ledgers;
8. prove partial-failure recovery;
9. independently reconcile registered assets, live token custody, and
   nominal/share accounting; specifically retain the pinned Base ID 4 inventory
   of six registered assets and three one-unit custody donations with zero
   shares as a `doesVaultHaveAnyFunds()` semantics regression;
10. retire the old address only after live-funds/accounting checks pass; and
11. run post-migration Base and Robinhood smoke/reconciliation tests.

Rollback reality must be tested as a state migration, not described as merely
switching an address back.

## 11. Diagnostics and evidence requirements

Every future test record must include:

- proposed/actual file and stable component IDs;
- prerequisite owner decision;
- setup, users, buyer(s), issuer/admin, operator, and governance actor;
- token behavior and exact implementation identity;
- starting `C`, `N` or `S`, per-user nominal/shares/claims, `δ`, debt, bad debt,
  and auctions;
- requested, received, credited, delivered, paid, and repaid amounts;
- expected state transition and exact invariant ID;
- clock profile;
- emitted events/getter values;
- all relevant ending state or state-root equivalence on atomic failure;
- runtime tier and duration;
- source/runtime hashes and pinned block for fork/live-version evidence; and
- reviewer, security approver, and owner approval status.

Unknown pause/blocklist/upgrade state must be labeled unknown, not false.

## 12. Proposed tiers and commands

Commands are placeholders until files exist and the owner approves
implementation:

| Tier | Purpose | Proposed command shape |
| --- | --- | --- |
| T0 | Existing evidence | `PYTHONPATH=. pytest -q tests/vaults/test_stock_token_vault_comparison.py` |
| T1 | Math/vault/credit focused | `PYTHONPATH=. pytest -q <approved focused files>` |
| T2 | Core settlement/governance | `PYTHONPATH=. pytest -q <approved AuctionHouse/Deleverage/control files>` |
| T3 | Base full regression | repository-standard full test command, serial if required by environment |
| T4 | Exact AAPL fork | approved no-broadcast fork command with pinned block |
| T5 | Dual-clock/clean migration | integrated S1/S2 profile commands plus Track 7 rehearsal |

No dependency or tool addition is authorized by this scaffold.

## 13. Review and launch gates

The owner selected option 4, authorized Phase D specification, then authorized
Phase E specification under the explicit existing-controls/no-new-storage
constraint. The Phase D and E designs and future test contracts are complete;
no implementation or test change is authorized. Entry into Phase F and
finalization of later implementation/release gates remain blocked on the
following decisions at their recorded phase boundaries:

- external-only issuer settlement decision;
- total-loss and exactly-once bad-debt policy;
- post-zero/restoration/loss-allocation policy;
- reward-unit decision;
- Base live-version/migration posture;
- integrated S1/S2 and Track 7 interfaces;
- implementation review and audit decision; and
- exact-token, Base regression, migration, testnet, and smoke evidence.

At this checkpoint, the evidence baseline, formal invariant map, Phase C
comparison, Phase D deposit-accounting design, Phase E backing/debt-health
design, proposed test names, and required matrices are ready for owner review.
No implementation, test, or launch gate is passed by this specification.
