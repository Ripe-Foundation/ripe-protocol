# Stock Token Vault-Change Validation Plan

Status: **Phases D–G test contracts specified under owner-confirmed
instructions — not a finalized Phase J plan**

Date: 2026-07-24 (America/Denver)

This document keeps the Phase B invariant model, Phase C architecture
comparison, owner-confirmed Phase D deposit design, and owner-confirmed Phase E
backing/debt-health design testable, together with the owner-confirmed Phase F
external-settlement and total-loss directions and the owner-confirmed Phase G
post-zero freeze, no-automatic-allocation, and live-claim reward directions.
The instructions select option 4, containment followed by the corrected share
path, then reject a new stored per-asset collateral-use parameter and authorize
Phase E specification using existing deposit controls and `DebtTerms.ltv`.
The owner confirmed both quotes under
`stock-token-vault-change-specification.md` Section 12.1. On 2026-07-24, the
owner also approved the two Phase F policy directions, paused after they were
documented, then approved the three Phase G directions and authorized Phase G
specification work. This is checkpoint option 4, the combination of
architecture outcomes 2 and 3, not the separately numbered “another generic
shared design.” All paths below are proposed future paths. No test, fixture,
mock, production contract, interface, storage, dependency, CI file, manifest,
or ABI was created or changed.

The Phase D–G test contracts are now specific enough for later
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
| `tests/vaults/modules/test_vault_loss_properties.py` | Math/property | `CM-024`, `CM-025` | Proposed; Phase G share/loss/rounding behavior specified, implementation not approved |
| `tests/core/creditEngine/test_deficit_aware_credit.py` | CreditEngine | `CM-030`, `CM-009`, Ledger | Proposed; Phase E existing-controls behavior specified, implementation not approved |
| `tests/core/auctionHouse/test_loss_aware_auctions.py` | AuctionHouse | `CM-026`, `CM-030`, Ledger | Proposed; Phase F policy specified, enforcement mechanism not approved |
| `tests/core/deleverage/test_loss_aware_deleverage.py` | Teller/Deleverage | `CM-034`, `CM-044`, `CM-026` | Proposed; Phase F delivery bound specified |
| `tests/data/test_ledger_bad_debt_transition.py` | Ledger/CreditEngine | Ledger, `CM-030`, `CM-026` | Proposed; Phase F atomic transition specified, two selectors not approved |
| `tests/core/lootbox/test_vault_loss_rewards.py` | Rewards/monitoring | `CM-033`, `CM-025`, Ledger | Proposed; Phase G live-claim units specified, implementation and S3 integration pending |
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
| I-01 exact receipt | `test_credit_equals_call_local_balance_delta` | Vault/Teller | `A_req`, `Q`, `R`, credited, returned, and emitted amounts reconcile; prior donation excluded | Phase D specified |
| I-01 exact receipt | `test_short_second_deposit_cannot_overcredit_either_path` | Vault/Teller | Both nominal and share paths credit only actual receipt | Phase D specified |
| I-02 borrowing conservation | `test_sum_borrow_amounts_never_exceeds_live_custody` | Property/Credit | Invariant holds across users, deposits, losses, and withdrawals | Architecture |
| I-03 claim conservation | `test_all_withdrawal_orders_are_allocated_backing_bounded` | Property/Vault | Two-user orders cannot allocate more than `A <= C` and never consume `U` | Phase G specified |
| I-03 claim conservation | `test_two_buyers_cannot_allocate_same_remaining_custody` | Auction | Both purchase orders conserve custody | Phase F specified |
| I-04 pay for delivery | `test_green_and_debt_commit_only_after_actual_delivery` | Auction/Deleverage | Payment/debt value is bounded by delivered amount/value | Phase F specified |
| I-05 atomic failure | `test_pause_blocklist_false_return_and_revert_leave_state_unchanged` | Vault/Auction | Balances, debt, GREEN, rewards, and auction state unchanged | Phase F specified |
| I-06 deficit visibility | `test_zero_borrow_value_does_not_erase_existing_debt_terms` | Credit | Deficit remains resolution/liquidation-visible | Phase E specified |
| I-06 deficit visibility | `test_mixed_collateral_preserves_solvent_terms_and_unsafe_debt_signal` | Credit | Solvent collateral remains valued; deficit cannot create false health | Phase E specified |
| I-07 no new unsafe debt | `test_one_unit_deficit_contributes_zero_new_capacity` | Credit | Preview and state-changing borrow match and return/revert safely | Phase E specified |
| I-07 no new unsafe debt | `test_disabled_asset_cannot_support_new_borrow` | Governance/Credit | Existing fast disable affects every credit surface | Phase E specified |
| I-08 exactly once | `test_total_loss_moves_liability_to_bad_debt_exactly_once` | Credit/Auction/Ledger | User debt decreases by `x`, bad debt increases by `x`, repeat is no-op/revert | Phase F specified; interfaces pending |
| I-08 exactly once | `test_repayment_race_uses_one_pinned_debt_state` | Credit/Ledger | Repay and transition cannot duplicate or lose liability | Phase F specified; interfaces pending |
| I-09 repay liveness | `test_repayment_remains_available_during_deficit_freeze` | Credit/Teller | Repay succeeds while borrow/deposit/settlement are frozen | Product direction |
| I-10 post-zero | `test_new_deposit_reverts_while_old_shares_exist_at_zero` | Share vault | No new shares or value transfer under `Z_custody`, `Z_live`, or `Z_recorded` | Phase G specified |
| I-10 post-zero | `test_restoration_remains_quarantined_after_recorded_zero` | Share/property | Later custody is `U`; old/new users receive no automatic claim | Phase G specified |
| I-11 external-only | `test_issuer_asset_rejects_buyer_internal_override` | Auction/config | Internal mode unavailable; external delivery enforced | Phase F specified; mechanism pending |
| I-12 price independence | `test_deficit_guard_survives_missing_or_zero_price` | Credit | Custody status remains visible and fail-closed without price | Phase E specified |
| I-13 quarantine | `test_unsolicited_positive_delta_never_increases_allocated_backing` | Share/property | Donation/restoration changes `C` and `U`, not `A`, claims, credit, settlement, or rewards | Phase G specified; storage/interface pending |
| I-13 quarantine | `test_deposit_allocates_only_call_local_receipt_not_existing_surplus` | Vault/Teller | `A_after = A_before + R`; pre-existing `U` remains unchanged | Phase G specified |
| I-13 quarantine | `test_checkpointed_quarantine_is_not_shareholder_loss_insurance` | Share/property | After bucket checkpoint, an observed negative delta reduces `A` before `U^s`; donation cannot silently shield claims | Phase G specified; storage/interface pending |

## 4. Sixteen-state matrix

| State | Named future test(s) | Core diagnostics |
| --- | --- | --- |
| Solvent ordinary | `test_ordinary_lifecycle_6_decimals`, `test_ordinary_lifecycle_18_decimals`, `test_one_base_unit_lifecycle` | `C`, `A^s`, `U^s`, `A`, `U`, shares, claim, credit, delivery, events |
| Pre-existing donation | `test_preexisting_donation_is_quarantined_and_not_depositor_receipt` | before/after `C`, `A^s`, `U^s`, `A`, `U`, `R`, credited amount |
| Donation between deposits | `test_between_deposit_donation_stays_quarantined` | both users' shares/claims, unchanged `A`, increased `U` |
| Short receipt / fee | `test_short_receipt`, `test_fee_on_transfer_receipt` | requested/received/credited/event amounts |
| Partial issuer reduction | `test_partial_admin_burn_checkpoints_allocated_backing_pro_rata` | `C`, `A^s`, `U^s`, `A`, `U`, shares, credit, delivery |
| Aggregate nominal deficit | `test_nominal_deficit_propagates_to_health` | deficit status, weighted terms, max borrow |
| Total custody loss | `test_total_loss_no_paid_auction`, `test_total_loss_bad_debt_once` | debt, bad debt, auctions, GREEN |
| Zero custody/nonzero shares | `test_zero_custody_old_shares_freeze` | raw shares, `Z_custody`, `Z_live`, `Z_recorded`, zero claim/reward, rejected deposit/withdraw |
| Restoration after zero | `test_post_zero_restoration_is_quarantine_not_allocation` | `C`, `A^s=0`, `U^s`, `A=0`, `U`, unchanged shares/claims/rewards |
| New deposit after zero | `test_post_zero_new_deposit_reverts_atomically` | `C`, `A^s`, `U^s`, `A`, `U`, shares, user state unchanged |
| Paused transfer | `test_paused_deposit_withdraw_and_settlement_atomicity` | state roots or all relevant balances/state |
| Sender/recipient/operator blocklist | parameterized `test_blocklist_role_atomicity` | actor role, revert reason, unchanged state |
| Active auction before action | `test_active_auction_revalidates_after_loss` | pre/post custody, auction progress, buyer GREEN |
| Liquidation after action | `test_post_loss_liquidation_uses_resolution_not_zero_auction` | health, auction count, debt resolution state |
| Implementation/beacon change | `test_behavior_switch_fails_closed_until_reenabled` | implementation identity, flags, receipt/delivery |
| Recovery/migration with debt | `test_live_state_migration_reconciles_or_aborts` | users, assets, `C`, `A^s`, `U^s`, `A`, `U`, raw accounting, debt, auctions, registry |

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

- `Σ claims <= A <= C` for arbitrary user share vectors;
- both two-user withdrawal orders;
- both two-buyer settlement orders;
- partial loss from one unit through `C-1`;
- total loss with nonzero `S`;
- donation before first deposit and between deposits remain `U`;
- checkpointed restoration remains `U` and attempted fresh deposit after zero
  reverts;
- unobserved reduce→restore is labeled indistinguishable rather than detected;
- amount→shares round down for deposit, claim round down, withdrawal share burn
  round up, and final-share allocated-backing sweep;
- 6- and 18-decimal minimum-positive deposits;
- `DECIMAL_OFFSET` and virtual-asset dust bounds;
- raw shares, `C`, `A`, `U`, live claims, and live-claim reward units in events,
  getters, and reports; and
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
A_req = raw Teller input
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
0 < R <= Q <= A_req
V == R
C1 == C0 + R
C2 == C1
C3 == C1
existing Teller/vault deposit event amount == R
TellerDepositMeasured == (A_req, Q, R, V, vault, vaultId)
```

The `Q <= A_req` comparison remains literal when `A_req` is
`max_value(uint256)`; the test must also show the source-balance/limit cap that
produced `Q`.

Required cases in
`tests/vaults/test_vault_receipt_accounting.py` and
`tests/core/teller/test_teller_deposit_receipts.py`:

| Test | Setup | Required result |
| --- | --- | --- |
| `test_ordinary_receipt_reconciles_all_amounts` | Ordinary token; `A_req == Q` | `R == Q == V`; all applicable events reconcile. |
| `test_max_request_records_capped_transfer_attempt` | `A_req = max_value`; finite balance/limit | Event preserves `A_req`, records capped `Q`, and credits measured `R`. |
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
| `test_share_deposit_uses_predeposit_allocated_backing_and_rounds_down` | Under Section 17, shares equal `floor(R * (S + 10^8) / (A_0 + 1))`; `Q`, aggregate post-custody, and pre-existing `U` cannot enter as the call receipt or allocated denominator. |
| `test_positive_receipt_that_mints_zero_shares_reverts` | No positive custody can be donated through zero-share credit. |
| `test_stab_vault_uses_measured_receipt_without_economic_drift` | GREEN/sGREEN value, claimable-value, virtual-offset, and existing share rules are unchanged except for the verified receipt input. |
| `test_registration_occurs_only_after_credit` | Failed/zero credit cannot add Ledger participation. |
| `test_points_read_postcredit_balance` | Lootbox input state reflects shares/nominal credit from `R`. |
| `test_price_snapshot_occurs_after_measured_credit` | Snapshot is absent on failure and sees the successful post-credit state. |
| `test_deposit_many_measures_each_item_and_is_atomic` | Independent `(C0,C1,R,V,C2,C3)` per item; one failed item rolls back all items and final housekeeping. |
| `test_rebalance_uses_received_deposit_amount` | `TellerRebalance.depositAmount == R`; deposit, withdrawal, and final health check are atomic. |

Section 17 supplies the permanent corrected-share denominator after the owner
approved the Phase G policies. These tests pin Phase D's receipt input and
rounding direction and must now compose with `A_0`; they do not approve a
storage/interface mechanism for representing `A_0`.

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

For every exact path, inject both `Q < A_req` source-capping and `R < Q`
short-receipt results. Prove the caller compares Teller's return with `A_req` and
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
  exactly to `A_req`, `Q`, `R`, and `V`; and
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
| `test_fast_disable_existing_borrower_blast_radius` | Existing debt supported partly/wholly by a solvent asset, then lite actor sets `canDeposit=false` | Affected capacity becomes zero; max borrow never increases and falls when collateral capacity binds; health/withdraw preview tighten according to remaining collateral; live resolution value prevents disable-only spurious liquidation |
| `test_deficit_cannot_appear_healthy_via_amount_zero_skip` | Existing debt supported only by a now-zero-claim or deficient asset | `hasGoodDebtHealth` is false; the unsafe entry is processed rather than skipped |
| `test_deficit_preserves_nonzero_liquidation_terms` | Existing debt and only configured asset becomes fully missing | Collateral value/capacity are zero, but configured liquidation threshold remains nonzero and `canLiquidateUser` is not false merely because amount is zero |
| `test_mixed_collateral_preserves_exact_solvent_capacity` | One deficient position and one unrelated solvent/enabled/priced position | Unsafe contribution is zero; solvent value and capacity exactly equal the single-position control case |
| `test_mixed_collateral_health_uses_only_actual_capacity` | Vary debt below/above the solvent position's capacity | Health is true only when unrelated eligible collateral alone covers debt |
| `test_missing_price_cannot_hide_deficit` | Deficit position with stale, zero, or missing price | Deficit remains fail-closed and terms remain visible without a price call |
| `test_safe_missing_price_is_independently_fail_closed` | Backing-safe enabled position with invalid price | Preview/health give no optimistic value; state-changing borrow reverts under the existing raising mode |
| `test_current_repayment_raising_price_regression` | On the pinned pre-fix implementation, configure a nonzero-LTV position whose configured feed yields no price | Repayment reproduces the current revert caused by `_getUserBorrowTerms(..., True, ...)`; the test is retained as explicit before/after evidence |
| `test_repayment_succeeds_without_unsafe_asset_price` | Existing debt, known disabled/deficit position, unusable price | Repayment reduces Ledger debt, updates conservatively, and does not require the unsafe asset price |
| `test_repayment_succeeds_without_any_configured_collateral_price` | Existing debt and one or more LTV-bearing positions whose configured feeds yield no price | Future non-raising refresh permits repayment, records conservative value/health fields, and decreases debt exactly by payment |
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
- `test_no_stored_deficit_bit_can_disagree_with_live_backing`;
- `test_monitoring_labels_read_failure_unknown_not_solvent`;
- `test_phase_e_hot_path_staticcall_inventory`; and
- `test_phase_e_worst_case_gas_budget`.

The bundle must record block number/hash, vault/asset/user identities, raw
responses, decoded values, and derived `C<T`, zero-claim, eligibility, value,
capacity, and health results. Event evidence proves config transitions; live
getters prove current backing. Gas evidence must cover maximum configured user
vault/asset enumeration for borrow, preview, health, liquidation, repayment,
and withdrawal preview; record external/staticcall counts as well as gas.

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
   disable and zero new-borrow support;
10. the Phase I impact table explicitly records the repayment
    raising-to-non-raising price behavior change and worst-case hot-path call/gas
    results; and
11. the owner separately authorizes implementation.

These are future acceptance conditions, not evidence that any implementation
exists. Phase F policy is specified separately below; its implementation
mechanisms remain gated.

## 8. Phase F settlement and total-loss validation contract

No test in this section exists yet. The policy outcomes are owner-confirmed;
the all-external-versus-per-asset enforcement mechanism and the proposed
CreditEngine/Ledger selectors and transition caller policy remain unapproved.
Common tests below are mandatory under either settlement mechanism. Branch-
specific tests become mandatory only if the owner later selects that
mechanism/caller policy.

### 8.1 Current-behavior and mechanism boundary

| Test | Setup | Required result |
| --- | --- | --- |
| `test_current_internal_auction_reproduces_nominal_only_delivery` | Pinned current Simple path after total issuer burn, buyer selects internal | Preserve the Track 5 regression: nominal buyer balance moves and GREEN/debt commit without token delivery |
| `test_current_external_auction_delivery_precedes_payment` | Pinned ordinary external purchase | Token transfer occurs before GREEN transfer and debt reduction |
| `test_no_existing_asset_config_field_means_external_settlement` | Inspect compiled/source `AssetConfig`, `AuctionBuyConfig`, and getters | No existing field is mislabeled or overloaded as the new policy |
| `test_all_external_option_rejects_internal_for_every_fungible_asset` | Only if the all-external mechanism is owner-selected | Every `_shouldTransferBalance = true` auction request fails/skips without payment; external mode remains functional |
| `test_per_asset_mode_option_is_generic_and_default_safe` | Only if the per-asset mechanism is owner-selected | No token/name/vault/chain branch; issuer fixture is external-required; every migrated existing asset has an explicit reviewed value |
| `test_unselected_mechanism_has_no_schema_or_abi_delta` | Compare approved implementation against the selected option | No field/selector/default/migration from the rejected option appears |

The first current-behavior test must remain pinned and passing against the
unsafe baseline. The corresponding future behavior test must fail against that
baseline and pass only against the approved shared implementation.

### 8.2 Delivery, payment, and custody conservation

For every test below, record vault custody, liquidated-user claim, recipient
balance, vault-reported withdrawal `W`, measured recipient delta `R`,
chargeable delivery `E`, GREEN owner balances, user debt, aggregate debt,
auction data, participation, points, and events before and after.

| Test | Scenario | Required result |
| --- | --- | --- |
| `test_issuer_asset_rejects_buyer_internal_override` | Solvent issuer-controlled asset, buyer requests internal mode | No claim move, token move, GREEN spend, debt change, point change, or auction mutation |
| `test_external_delivery_commits_before_green_and_debt` | Ordinary external purchase | Positive `E` exists before GREEN/debt commit; `P <= V(E)` |
| `test_zero_recipient_delta_cannot_charge_green` | Transfer returns true but recipient delta is zero | Entire purchase reverts or contributes zero with all payment/debt state unchanged |
| `test_short_outbound_receipt_cannot_overcharge` | Vault debit/return `W`, recipient gets `R < W` | Charge and debt reduction use at most `V(R)`; `W-R` remains explicit in diagnostics, or the transaction rejects the token atomically |
| `test_recipient_delta_above_vault_debit_reverts` | Reflection/rebase gives `R > W` | No collateral windfall is priced as liquidated delivery; full atomic revert |
| `test_paused_external_settlement_is_atomic_and_retryable` | Issuer pause before purchase, then unpause | Paused attempt changes nothing and does not create bad debt; same auction can settle after unpause |
| `test_sender_recipient_operator_blocklist_is_atomic` | Each relevant token role blocked separately | All affected state unchanged; removal of the block permits retry |
| `test_two_buyers_cannot_allocate_same_remaining_custody` | Both buyer orders after partial custody reduction | Sum of `E` across purchases is no greater than safely allocable custody in either order |
| `test_batch_rows_recheck_live_custody` | Duplicate asset/user rows in one batch | Later row sees prior row's custody/claim/debt result and cannot reuse it |
| `test_custody_loss_after_auction_creation_reprices_delivery` | Start solvent auction, then reduce custody before buy | Purchase uses current `L_u`/`E`, not creation-time nominal amount |
| `test_total_loss_after_auction_creation_cannot_be_paid` | Start auction, then make `C = 0` | No GREEN or debt commit; stale auction is removed/canceled before resolution |
| `test_new_total_loss_position_cannot_start_paid_auction` | `C = 0` before liquidation/start/restart | Liquidation may be resolution-eligible, but no paid auction is created |
| `test_nominal_partial_deficit_freezes_settlement` | `0 < C < N` with no approved allocation | Internal and external settlement remain frozen; no first-caller allocation |
| `test_bounded_internal_other_asset_is_aggregate_safe` | Only if internal mode is retained for a non-issuer asset | Returned internal amount is live-claim bounded and aggregate post-move claims remain `<= C` |

Atomic-failure tests must compare complete relevant state or state roots, not
only the function return value.

### 8.3 Settlement consumer matrix

| Consumer | Named test | Required result |
| --- | --- | --- |
| AuctionHouse single | `test_single_auction_uses_measured_external_delivery` | `E` controls payment, debt, event, and depletion |
| AuctionHouse batch | `test_batch_mixed_policy_rows_do_not_cross_charge` | Disallowed issuer/internal row consumes neither GREEN nor custody; allowed rows reconcile independently |
| CreditRedeem | `test_stock_token_redemption_remains_disabled` | General and asset config reads remain false for Stock Tokens; no internal or external redemption |
| CreditRedeem future external-required fixture | `test_external_required_redemption_cannot_use_internal_mode` | If this route is ever separately enabled, positive measured `E` precedes burn/debt; zero `E` cannot burn |
| Deleverage | `test_deleverage_repay_is_bounded_by_recipient_delta` | Sum repaid is no greater than sum of delivered values; target amount alone has no effect |
| Deleverage zero/failed leg | `test_deleverage_zero_delivery_contributes_zero_repayment` | Later valid legs may continue if designed to do so; missing leg cannot repay |
| Stability Pool | `test_stock_token_stability_pool_route_remains_disabled` | `shouldSwapInStabPools = false`; no Stock Token custody enters a pool |
| Standing integration exclusions | `test_stock_token_has_no_unsupported_settlement_route` | No Endaoment, Curve, Aerodrome, Underscore, or yield path |

### 8.4 Total-loss eligibility matrix

| Test | Setup | Required result |
| --- | --- | --- |
| `test_total_loss_resolution_requires_positive_current_debt` | Zero-debt user with missing collateral accounting | No transition and no bad-debt increment |
| `test_total_loss_resolution_requires_liquidation_state` | Unhealthy/zero-backed but not yet in liquidation | Resolution entry rejects until the approved liquidation state is established |
| `test_mixed_solvent_collateral_must_be_exhausted_first` | Missing issuer asset plus another positive deliverable claim | No bad-debt transition while any safely deliverable claim remains |
| `test_nominal_partial_deficit_is_not_total_loss` | Positive shared custody with unresolved nominal ownership | No transition; no allocation of residual custody |
| `test_paused_positive_custody_is_not_total_loss` | Positive custody but token paused/blocklisted | No transition; retry after token control clears |
| `test_missing_price_is_not_total_loss` | Positive custody and missing/stale price | No transition based solely on price failure |
| `test_zero_custody_eligibility_is_price_independent` | No live custody or other claim, missing price | Token-unit zero remains visible and can satisfy the custody part of eligibility |
| `test_active_positive_auction_blocks_resolution` | Purchasable active auction | No transition |
| `test_zero_backed_auction_is_canceled_atomically` | Active stale auction with zero live claim | Transition removes it in the same transaction |
| `test_resolution_scan_covers_every_user_vault_and_asset` | Mixed vault types and ordering | Omission of any positive claim blocks acceptance; iteration order cannot change result |

### 8.5 Atomic Ledger transition and exactly-once properties

Use at least two borrowers so aggregate `totalDebt`, borrower indexes, auctions,
and unrelated state can be checked independently.

| Test | Required result |
| --- | --- |
| `test_total_loss_moves_full_liability_to_bad_debt_once` | For `X = D_s.amount + Y`, user debt becomes zero and `badDebt` increases by exactly `X` in one transaction |
| `test_transition_reduces_total_debt_by_stored_amount` | Aggregate `totalDebt_after = totalDebt_before - D_s.amount`; unrelated borrower debt is unchanged |
| `test_accrued_interest_moves_and_books_once` | `Y` is included in `X`; `unrealizedYield_after = unrealizedYield_before + Y`; no flush or mint occurs during transition |
| `test_transition_clears_principal_borrower_and_auctions` | Principal/amount zero, liquidation false, borrower removed, all fungible auctions removed |
| `test_transition_does_not_mutate_vault_claim_or_custody` | Raw accounting/shares and token custody are byte-for-byte unchanged |
| `test_transition_does_not_mint_burn_or_transfer_green` | GREEN supply and all relevant balances are unchanged |
| `test_duplicate_transition_cannot_increment_bad_debt` | Second call is no-op/revert and `badDebt` stays at first result |
| `test_expected_debt_compare_and_set_rejects_stale_snapshot` | Change amount or last timestamp before commit; stale transition changes nothing |
| `test_repay_then_transition_uses_reduced_debt` | Repayment first reduces `D_f`; only residual enters bad debt |
| `test_transition_then_repay_cannot_retain_duplicate_liability` | Transition first leaves zero user debt; later `repayForUser` rejects without changing liability |
| `test_auction_purchase_then_transition_rechecks_state` | Successful delivery/payment first changes custody/debt; transition uses new residual or is ineligible |
| `test_transition_then_auction_purchase_cannot_pay` | Auction removal/zero debt makes later purchase return/revert without GREEN spend |
| `test_transition_revert_rolls_back_every_state_write` | Force failure at final Ledger step/event boundary; debt, bad debt, borrower, auctions, and yield all equal pre-state |
| `test_manual_bad_debt_setter_cannot_erase_atomic_addition_silently` | Governed reconciliation after accumulated transitions is explicitly reviewed/evented and cannot masquerade as a per-user transition |
| `test_bad_debt_global_consumers_observe_increment` | BondRoom data and configured RipeGov freeze read the exact new global bad debt |
| `test_clearing_bad_debt_does_not_restore_user_liability` | BondRoom `didClearBadDebt` lowers global bad debt only; resolved user debt remains zero |

Property sequences must randomize deposits, issuer reductions, auction starts,
external purchase attempts, repayments, pauses, blocklists, total-loss
finalization, duplicate finalization, and bad-debt clearing. At every step:

```text
sum(chargeable delivered collateral) <= safely allocable live custody
GREEN/debt committed for settlement <= priced chargeable delivery
userDebt_reduction_on_transition == badDebt_increase_on_transition
no liability is simultaneously user debt and newly added bad debt
```

### 8.6 Controls, liveness, events, and ABI gates

| Test | Required result |
| --- | --- |
| `test_can_buy_false_blocks_purchase_not_repayment_or_writeoff_accounting` | Purchase control has its documented blast radius only |
| `test_department_pause_blocks_total_loss_transition` | CreditEngine or Ledger pause causes atomic failure |
| `test_unpause_retries_same_eligible_transition` | No stale marker/state blocks progress after resume |
| `test_repayment_remains_available_before_transition` | Existing repay control succeeds while deposit/borrow/auction are frozen |
| `test_permissionless_caller_has_no_resolution_discretion` | If permissionless calling is selected, caller cannot choose eligibility, `X`, recipient, allocation, bad-debt destination, or any value-sensitive input |
| `test_repayment_and_permissionless_resolution_race_is_accounting_safe` | Both mined orders conserve liability; security evidence separately assesses whether keeper timing/griefing is acceptable |
| `test_restricted_caller_option_rejects_unapproved_sender` | If a restricted caller is selected, every unapproved caller fails without state change and the approved role remains live |
| `test_phase_h_resolution_pause_matrix_matches_approved_control` | Final Phase H tests cover the selected pause/resume authority, timing, caller interaction, events, and repayment-while-paused behavior |
| `test_transition_event_reconstructs_liability_move` | User, stored debt, `Y`, `X`, `BD_0`, `BD_1`, caller, and canceled-auction count are reconstructible |
| `test_settlement_event_reconstructs_q_w_r_e_and_payment` | Requested, vault-debited, recipient-received, chargeable, GREEN, debt, route, and recipient values reconcile |
| `test_repay_event_not_emitted_for_bad_debt_transition` | A write-off is not mislabeled as repayment |
| `test_no_new_storage_for_two_selector_bad_debt_design` | If selected, storage layout is byte-for-byte unchanged |
| `test_interface_delta_matches_owner_approved_mechanism_only` | ABI/interface diff contains exactly the later-approved selectors/fields/events and nothing from an unselected option |
| `test_total_loss_scan_worst_case_gas` | Maximum allowed vault/asset/auction traversal stays within reviewed gas bounds |

### 8.7 Phase F implementation acceptance

A future Phase F implementation is not acceptable unless:

1. every common and selected-mechanism test above passes;
2. all unsafe current-behavior regressions remain pinned rather than rewritten;
3. the owner separately approves one settlement enforcement mechanism;
4. accounting/security separately approve the exact atomic interface and
   source-consistent accrued-interest/yield-booking treatment;
5. the owner/security review separately approves the total-loss transition
   caller policy after repayment-race and griefing analysis;
6. Phase H explicitly closes the resolution pause/resume control model;
7. no nominal partial-loss or recovery allocation is inferred;
8. exact source/interface/storage/ABI diffs match the later Phase I table;
9. the implementation is included in the atomic containment/release grouping;
10. Base and exact-token fork evidence is attached; and
11. reviewer, security, and owner gates are recorded.

This Phase F validation contract does not approve any mechanism or caller
policy, any new selector or storage field, implementation, or launch. Phase G
was authorized separately and is specified in Section 9 below.

## 9. Phase G corrected share-vault validation contract

These are future test contracts for specification Section 17. They do not
authorize a storage field, selector, wrapper, positive-delta mode, Lootbox
change, migration, or production vault.

### 9.1 Current-behavior pins and future fixture state

Keep the unchanged Track 5 cases that prove current behavior:

- a donation between deposits increases current Rebase shareholder claims;
- a donation after total loss revives current Rebase claims;
- a fresh deposit after total loss mints against the one-unit virtual
  denominator and dilutes old shares;
- raw Lootbox user weight survives total loss while aggregate Rebase value
  follows raw custody; and
- vault ID 4 can report no accounted funds while live token dust exists.

Future tests must not rewrite those assertions in place. New behavior belongs
in:

```text
tests/vaults/modules/test_vault_loss_properties.py
tests/vaults/test_stock_token_vault_lifecycle.py
tests/core/lootbox/test_vault_loss_rewards.py
tests/registries/test_vault_book_migration.py
```

The share fixture must expose, as distinct diagnostics:

```text
C, A^s, U^s, A=min(A^s,max(C-U^s,0)), U=C-A, S, each s_u,
each live claim, each normalized reward weight, global eligible USD value,
and all three zero flags
```

If the approved implementation chooses different names, the test adapter may
map them only after Phase I records the exact semantics.

### 9.2 Formula and rounding properties

| Test | Required result |
| --- | --- |
| `test_initial_share_mint_is_receipt_times_decimal_offset` | With `S=A=0`, receipt `R` mints exactly `R * 10^8` shares; pre-existing `U` is excluded |
| `test_deposit_share_mint_rounds_down_against_predeposit_A` | Mint equals `floor(R*(S+10^8)/(A_0+1))`, is positive, and no `C`, `U`, or `Q` substitution changes it |
| `test_live_claim_rounds_down_against_effective_A` | Non-final claim equals `floor(s*(A+1)/(S+10^8))` and never exceeds allocated backing |
| `test_sole_holder_live_claim_matches_final_sweep` | When `s_u=S>0`, the getter/preview claim is exactly `A`, matching executable full withdrawal |
| `test_partial_withdrawal_share_burn_rounds_up` | Burn equals `ceil(x*(S+10^8)/(A+1))`, capped by user shares; transfer is at most `x` |
| `test_final_share_burn_sweeps_only_remaining_A` | Final real shares receive all remaining allocated backing and none of `U`; ending `S=A^s=0` while `U^s=U=C` if quarantine remains |
| `test_positive_receipt_minting_zero_shares_reverts` | Receipt and custody transfer roll back rather than become uncredited custody |
| `test_zero_shares_positive_allocated_checkpoint_fails_closed` | Malformed `S=0,A^s>0` cannot admit a deposit, deregister, recover, or activate migration until reconciled |
| `test_claim_partition_is_allocated_backing_bounded` | For arbitrary positive share partitions, sum of non-final floor claims is `<= A <= C` |
| `test_complete_withdrawal_orders_conserve_allocated_backing` | Every two-user order transfers at most starting `A`; final sweep occurs once; `U` is unchanged |
| `test_rounding_loss_is_strictly_bounded` | Deposit loses `<1` raw share, non-final claim loses `<1` asset base unit, partial burn adds `<1` raw share |
| `test_share_math_handles_safe_max_operands_or_reverts` | No wrap; implementation either returns the exact integer result or reverts before mutation |

Property generators cover:

- `S = 0`, one user, many users, one share, and highly skewed share vectors;
- `A = 0`, one base unit, partial losses `1..A-1`, and near-maximum safe
  integers;
- prior `U = 0`, one unit, and greater than `A`;
- both withdrawal orders and randomized complete permutations; and
- exact floor/ceil comparison against an unbounded-integer reference model.

### 9.3 Decimal and minimum-deposit matrix

Run the same lifecycle for 6- and 18-decimal tokens:

| Test | Required result |
| --- | --- |
| `test_share_lifecycle_one_base_unit_6_decimals` | One verified base unit mints `10^8` shares from empty allocated state and can exit under the final-sweep rule |
| `test_share_lifecycle_one_base_unit_18_decimals` | Same invariant without an 18-decimal special case |
| `test_share_deposit_below_configured_minimum_reverts_after_receipt` | Atomic rollback; no shares, `A`, points, registration, or event |
| `test_share_deposit_at_and_above_minimum` | Uses actual `R`, not `Q`, for the minimum and formula |
| `test_reward_normalization_reports_6_decimal_floor` | Explicit `p_a=10^6`; sub-unit reward floor is visible and labeled |
| `test_reward_normalization_reports_18_decimal_floor` | Under the current compatible convention, `p_a=10^9`; label is normalized claim units, not token/share/USD |

### 9.4 Loss checkpoint, donation, restoration, and zero state

| Test | Required result |
| --- | --- |
| `test_partial_loss_checkpoints_A_and_reprices_all_users_pro_rata` | `A^s` decreases to `min(old A^s,max(C-U^s,0))`; `S` unchanged; user claims fall proportionally within rounding bounds |
| `test_observed_external_reduction_hits_A_before_checkpointed_U` | After both buckets are checkpointed, a custody reduction lowers `A` and shareholder claims while preserving `U^s` until `A=0` |
| `test_preexisting_donation_stays_U_through_first_deposit` | Donation changes only `C/U`; first receipt changes `A` by exactly `R` |
| `test_between_deposit_donation_stays_U_and_does_not_change_price` | Existing claims/rewards and second depositor's share price exclude the donation |
| `test_positive_delta_never_raises_A_without_approved_allocation` | Arbitrary external increases change `U` and checkpoint into `U^s`, never `A^s`, claims, credit, settlement, or rewards |
| `test_observed_partial_loss_then_restoration_quarantines_recovery` | After checkpointing reduced `A^s` and preserved `U^s`, restoration is additional `U` |
| `test_literal_total_custody_loss_sets_all_zero_predicates` | With `C=0` and `S>0`, `Z_custody` and `Z_live` are immediate; a successful checkpoint sets `A^s=U^s=0` and `Z_recorded` |
| `test_successful_loss_checkpoint_sets_recorded_zero` | Explicit checkpoint or successful Phase F transition produces `A=A^s=0`, `S>0`, live claim/reward zero, and raw shares unchanged; `C/U^s/U` may remain positive quarantine |
| `test_reverting_zero_observation_cannot_persist_checkpoint` | Deposit/settlement revert leaves all storage unchanged; test does not falsely expect a reverted write to set `Z_recorded` |
| `test_post_zero_restoration_preserves_recorded_freeze` | New custody is entirely `U`; `A` and old claims remain zero |
| `test_post_zero_deposit_reverts_before_any_commit` | Token transfer, shares, `A^s`, `U^s`, `A`, `U`, registration, points, snapshots, and events equal pre-state |
| `test_old_shares_survive_bad_debt_transition` | Phase F liability move does not burn/reassign property shares or allocate later custody |
| `test_reduce_restore_without_observation_is_indistinguishable` | Final state matches no-loss path; test labels the fundamental ERC-20 observation limit and does not expect impossible history detection |
| `test_loss_checkpoint_then_restore_is_distinguishable` | The persisted lower `A^s` makes restoration `U`; evidence includes checkpoint caller/block/reason |

The final two cases are a pair. An implementation may not pass the
checkpointed case by claiming it detects the unobserved case, and it may not
use the unobserved limitation to skip mandatory checkpoints on protocol state
transitions.

### 9.5 Withdrawal and settlement conservation

| Test | Required result |
| --- | --- |
| `test_withdrawal_cannot_consume_quarantine` | User with all non-final claim can receive at most `A`; `U` stays in vault |
| `test_two_withdrawal_orders_never_exceed_starting_A` | Both user orders conserve allocated backing and leave identical quarantine |
| `test_two_settlement_orders_never_exceed_starting_A` | Both buyer orders re-read `A/C/S`; allocated delivery cannot repeat |
| `test_share_burn_delivery_and_A_reduction_reconcile` | Successful external call reconciles shares, `A^s`, unchanged `U^s`, vault debit `W`, recipient receipt, GREEN, and debt |
| `test_short_external_delivery_uses_phase_f_E_bound` | Payment/debt use `E=min(Q,W,R)`; no nominal share amount overcharges |
| `test_failed_delivery_rolls_back_share_checkpoint_and_rewards` | Shares, `A^s`, `U^s`, debt, GREEN, auctions, and points equal pre-state |
| `test_issuer_share_asset_has_no_internal_settlement_override` | Phase F external-only policy remains true under the corrected share path |

### 9.6 Deregistration, recovery, and live-funds guards

| Test | Required result |
| --- | --- |
| `test_zero_claim_nonzero_shares_block_user_deregistration` | Total loss does not erase the registered property record |
| `test_zero_custody_nonzero_shares_block_asset_deregistration` | `S>0` is sufficient to block retirement |
| `test_zero_shares_positive_U_blocks_asset_deregistration` | Donation dust cannot be made recoverable by declaring the asset empty |
| `test_does_vault_have_funds_counts_shares_or_live_custody` | True for `S>0`, `A^s>0`, `U^s>0`, or `C/U>0` |
| `test_base_id4_dust_inventory_is_not_empty_under_corrected_semantics` | The three pinned one-unit custody rows with zero shares are classified as `U` and keep the live-funds result true |
| `test_current_whole_balance_recovery_is_not_used_for_quarantine` | No registered `A/U` split is passed to current all-balance recovery |
| `test_future_recovery_cannot_exceed_separately_approved_U` | Placeholder remains skipped/blocked until owner plus counsel/risk approve recipient, amount, and interface |

Migration tests later initialize `A^s` and `U^s` only from an owner-approved
reconciliation of custody, user entitlement, and quarantine. `A^s := C` is
not an acceptable generic migration shortcut.

### 9.7 Reward and monitoring units

| Test | Required result |
| --- | --- |
| `test_reward_user_weight_uses_live_claim_not_raw_shares` | Solvent weight follows normalized live claim; partial loss reduces it; total loss makes it zero |
| `test_reward_global_value_prices_A_not_C` | Donation/restoration `U` never increases eligible global USD value |
| `test_raw_shares_remain_visible_but_are_not_economic_weight` | Raw accounting is reported separately and cannot be mislabeled or consumed alone |
| `test_loss_checkpoint_closes_reward_interval` | Pre-loss blocks accrue at prior economics; post-checkpoint blocks use reduced/zero live economics |
| `test_untouched_user_cannot_accrue_stale_post_loss_weight` | Integrated S3 mechanism handles global share-price change without per-user iteration drift |
| `test_pre_loss_points_are_not_clawed_back` | Historical earned points persist while future weight changes |
| `test_price_failure_does_not_change_A_or_backing` | Reward USD may be zero/unavailable, but custody/allocation safety remains visible |
| `test_ripe_gov_lock_points_keep_separate_semantics` | Vault ID 2 governance points are not interpreted as token live claims |
| `test_existing_positive_rebase_mode_is_not_silently_quarantined` | Any retained yield/rebase behavior is an explicit generic mode/variant with separate tests and approval |

The interval-boundary tests are **pending integrated S3**. They are mandatory
before reward implementation approval; Phase G does not invent S3's storage or
index.

### 9.8 Events, getters, storage, and compatibility assertions

| Test | Required result |
| --- | --- |
| `test_every_share_surface_declares_its_unit` | Raw shares, `C`, `A^s`, `U^s`, `A`, `U`, claims, normalized reward weight, and USD value are unambiguous |
| `test_deposit_withdraw_transfer_events_reconcile_amount_and_shares` | Amount is allocated call-local token units; shares are raw units |
| `test_loss_and_quarantine_evidence_reconstructs_state` | Asset, old/new `A^s/U^s`, `C`, `A`, `U`, caller, block/clock, and reason reconcile with getters |
| `test_amount_share_conversion_getters_use_A` | Existing-signature or replacement getters match the Section 17 reference model and exclude `U` |
| `test_manifest_declares_accounting_version_not_dynamic_balance` | Manifest/runtime evidence identifies capability and getter semantics without stale balance claims |
| `test_storage_upgrade_preserves_raw_share_units` | Existing user/total balances remain raw shares; any appended state follows the Phase I layout |
| `test_rebase_and_ripe_gov_consumer_inventory_is_complete` | Every wrapper, reader, event, ABI, and reward path is dispositioned before semantic change |

Exact selector/event/storage assertions remain placeholders until the owner
approves one Phase I mechanism. Tests must fail closed rather than guessing an
ABI.

### 9.9 Phase G implementation acceptance

A future implementation is not eligible for review until:

1. every Section 9 property/matrix test passes for 6- and 18-decimal assets;
2. current unsafe-behavior tests remain pinned and new tests demonstrate the
   intentional delta;
3. owner/security approve an allocated-backing mechanism after Phase I maps
   storage, ABI, wrappers, and live migration;
4. positive-rebase/yield compatibility is explicitly separated and tested;
5. no automatic donation/restoration/recovery/recapitalization path exists;
6. counsel/risk remain a hard gate for any later quarantine disposition;
7. Phase F delivery and exactly-once liability invariants compose with share
   burn and allocated backing;
8. integrated S3 closes reward interval semantics and stale-user weighting;
9. RipeGov governance units remain intact;
10. Base vault-ID-4 dust and every custody-bearing live vault are reconciled;
11. exact-token fork, Base regression, dual-clock, migration, and audit gates
    pass; and
12. owner approval explicitly names the production vault/version and atomic
    release group.

This Phase G validation contract approves no implementation mechanism or
later phase.

## 10. Exact-token fork plan

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

## 11. Dual-clock and identical-artifact integration

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

## 12. Migration validation scaffold

Pending owner live-version policy and Track 7 namespace/tooling:

1. pin old/new source, runtime, registry, and manifest identities;
2. enumerate every old-vault asset/user plus `C`, `A^s`, `U^s`, `A`, `U`,
   nominal/shares, claims, debt, rewards, and active auctions;
3. disable old deposits before movement;
4. prove debt and auction behavior is frozen or safely serviced during the
   window;
5. move/re-register custody and user state only through the approved procedure;
6. reconcile aggregate and per-user state before registry activation;
7. abort on any mismatch without leaving two authoritative claim ledgers;
8. prove partial-failure recovery;
9. independently reconcile registered assets, live token custody,
   allocated/quarantined backing, and nominal/share accounting; specifically
   retain the pinned Base ID 4 inventory of six registered assets and three
   one-unit custody donations with zero shares as a
   `doesVaultHaveAnyFunds()` semantics regression;
10. retire the old address only after live-funds/accounting checks pass; and
11. run post-migration Base and Robinhood smoke/reconciliation tests.

Rollback reality must be tested as a state migration, not described as merely
switching an address back.

## 13. Diagnostics and evidence requirements

Every future test record must include:

- proposed/actual file and stable component IDs;
- prerequisite owner decision;
- setup, users, buyer(s), issuer/admin, operator, and governance actor;
- token behavior and exact implementation identity;
- starting `C`, `A^s`, `U^s`, `A`, `U`, `N` or `S`, per-user
  nominal/shares/claims, `δ`, debt, bad debt, and auctions;
- requested, received, credited, delivered, paid, and repaid amounts;
- expected state transition and exact invariant ID;
- clock profile;
- emitted events/getter values;
- all relevant ending state or state-root equivalence on atomic failure;
- runtime tier and duration;
- source/runtime hashes and pinned block for fork/live-version evidence; and
- reviewer, security approver, and owner approval status.

Unknown pause/blocklist/upgrade state must be labeled unknown, not false.

## 14. Proposed tiers and commands

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

## 15. Review and launch gates

The owner-confirmed instructions select option 4, authorize Phase D
specification, then authorize Phase E specification under the explicit
existing-controls/no-new-storage constraint, then approve the Phase F
external-settlement and exactly-once total-loss directions for specification
only, and then approve the Phase G freeze, no-automatic-allocation, and
live-claim reward directions for specification only. The Phase D–G designs and
future test contracts are complete; no implementation or test change is
authorized. Phase H and later implementation/release gates remain blocked on
the following decisions at their recorded boundaries:

- all-external versus per-asset settlement enforcement mechanism;
- exact CreditEngine/Ledger transition interfaces;
- permissionless versus restricted/governed total-loss caller policy;
- allocated/quarantine checkpoint storage/wrapper mechanism;
- accounting/counsel-risk confirmation that observed losses reduce `A` before
  checkpointed `U`;
- positive-delta compatibility boundary for existing yield/rebase assets;
- Vault/Lootbox/Ledger reward integration surface after S3;
- Phase H resolution pause/resume authority, timing, and caller interaction;
- share-loss checkpoint caller, pause, and evidence policy;
- Base live-version/migration posture;
- integrated S1/S2 and Track 7 interfaces;
- implementation review and audit decision; and
- exact-token, Base regression, migration, testnet, and smoke evidence.

At this checkpoint, the evidence baseline, formal invariant map, Phase C
comparison, Phase D deposit-accounting design, Phase E backing/debt-health
design, Phase F settlement/total-loss design, Phase G corrected-share design,
proposed test names, and required matrices are ready for owner review. Work
stops before Phase H. No implementation, interface, storage, test, migration,
production-vault, Phase H, or launch gate is passed by this specification.
