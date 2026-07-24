# Stock Token Vault-Change Validation Plan

Status: **pre-decision checkpoint scaffold — not a finalized Phase J plan**

Date: 2026-07-23 (America/Denver)

This document keeps the Phase B invariant model and Phase C architecture
comparison testable while Track 8 is paused at its mandatory owner checkpoint.
All paths below are proposed future paths. No test, fixture, mock, production
contract, interface, dependency, CI file, manifest, or ABI was created or
changed.

The plan cannot be finalized until the owner selects a product/architecture
direction and resolves the policy decisions in
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
| `tests/vaults/test_vault_receipt_accounting.py` | Vault/Teller unit | `CM-024`, `CM-025`, `CM-034`, `CM-045` | Proposed; Phase D decision required |
| `tests/vaults/modules/test_vault_loss_properties.py` | Math/property | `CM-024`, `CM-025` | Proposed; loss/rounding policy required |
| `tests/core/creditEngine/test_deficit_aware_credit.py` | CreditEngine | `CM-030`, `CM-009`, Ledger | Proposed; collateral flag and deficit interface required |
| `tests/core/auctionHouse/test_loss_aware_auctions.py` | AuctionHouse | `CM-026`, `CM-030`, Ledger | Proposed; settlement and bad-debt policy required |
| `tests/core/deleverage/test_loss_aware_deleverage.py` | Teller/Deleverage | `CM-034`, `CM-044`, `CM-026` | Proposed |
| `tests/core/lootbox/test_vault_loss_rewards.py` | Rewards/monitoring | `CM-033`, `CM-025` | Proposed; rewards-unit decision required |
| `tests/config/test_asset_collateral_controls.py` | Governance/config | `CM-009`, `CM-011`–`CM-013`, config/interfaces | Proposed; flag/role decision required |
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
| I-01 exact receipt | `test_credit_equals_call_local_balance_delta` | Vault/Teller | Requested, received, credited, returned, and emitted amounts reconcile; prior donation excluded | Measurement boundary |
| I-01 exact receipt | `test_short_second_deposit_cannot_overcredit_either_path` | Vault/Teller | Both nominal and share paths credit only actual receipt | Measurement boundary |
| I-02 borrowing conservation | `test_sum_borrow_amounts_never_exceeds_live_custody` | Property/Credit | Invariant holds across users, deposits, losses, and withdrawals | Architecture |
| I-03 claim conservation | `test_all_withdrawal_orders_are_custody_bounded` | Property/Vault | Two-user orders cannot allocate more than custody | Loss allocation |
| I-03 claim conservation | `test_two_buyers_cannot_allocate_same_remaining_custody` | Auction | Both purchase orders conserve custody | Settlement model |
| I-04 pay for delivery | `test_green_and_debt_commit_only_after_actual_delivery` | Auction/Deleverage | Payment/debt value is bounded by delivered amount/value | Settlement policy |
| I-05 atomic failure | `test_pause_blocklist_false_return_and_revert_leave_state_unchanged` | Vault/Auction | Balances, debt, GREEN, rewards, and auction state unchanged | External-only policy |
| I-06 deficit visibility | `test_zero_borrow_value_does_not_erase_existing_debt_terms` | Credit | Deficit remains resolution/liquidation-visible | Deficit interface |
| I-06 deficit visibility | `test_mixed_collateral_preserves_solvent_terms_and_unsafe_debt_signal` | Credit | Solvent collateral remains valued; deficit cannot create false health | Deficit interface |
| I-07 no new unsafe debt | `test_one_unit_deficit_contributes_zero_new_capacity` | Credit | Preview and state-changing borrow match and return/revert safely | Collateral flag |
| I-07 no new unsafe debt | `test_disabled_asset_cannot_support_new_borrow` | Governance/Credit | Fast disable affects every credit surface | Flag/roles |
| I-08 exactly once | `test_total_loss_moves_liability_to_bad_debt_exactly_once` | Credit/Auction/Ledger | User debt decreases by `x`, bad debt increases by `x`, repeat is no-op/revert | Bad-debt policy |
| I-08 exactly once | `test_repayment_race_uses_one_pinned_debt_state` | Credit/Ledger | Repay and transition cannot duplicate or lose liability | Bad-debt policy |
| I-09 repay liveness | `test_repayment_remains_available_during_deficit_freeze` | Credit/Teller | Repay succeeds while borrow/deposit/settlement are frozen | Product direction |
| I-10 post-zero | `test_new_deposit_reverts_while_old_shares_exist_at_zero` | Share vault | No new shares or value transfer | Freeze/recap decision |
| I-10 post-zero | `test_restoration_has_only_owner_approved_allocation` | Share/property | No automatic capture by old/new users outside selected policy | Donation policy |
| I-11 external-only | `test_issuer_asset_rejects_buyer_internal_override` | Auction/config | Internal mode unavailable; external delivery enforced | Settlement policy |
| I-12 price independence | `test_deficit_guard_survives_missing_or_zero_price` | Credit | Custody status remains visible and fail-closed without price | Collateral flag/interface |

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

## 6. Exact-token fork plan

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

## 7. Dual-clock and identical-artifact integration

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

## 8. Migration validation scaffold

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

## 9. Diagnostics and evidence requirements

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

## 10. Proposed tiers and commands

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

## 11. Review and launch gates

Only owner selection of the architecture/product direction blocks entry into
Phase D. Finalization and later implementation/release gates remain blocked on
the following decisions at their recorded phase boundaries:

- owner architecture selection;
- per-asset collateral flag approval;
- external-only issuer settlement decision;
- total-loss and exactly-once bad-debt policy;
- post-zero/restoration/loss-allocation policy;
- reward-unit decision;
- Base live-version/migration posture;
- integrated S1/S2 and Track 7 interfaces;
- implementation review and audit decision; and
- exact-token, Base regression, migration, testnet, and smoke evidence.

At this checkpoint, only the evidence baseline, formal invariant map, proposed
test names, and required matrices are ready for owner review. No test or launch
gate is passed by this draft.
