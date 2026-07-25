# Stock Token Vault-Change Validation Plan

Status: **M0 owner directions recorded on 24–25 July 2026; all documentable
pre-implementation M0 validation inputs are complete for independent review;
M0 remains open pending that review and owner closure; M1 remains
unauthorized; every production file change, vault/ID, implementation,
migration, deployment, configuration, and live action remains unapproved**

Date: 2026-07-25 (America/Denver)

This document keeps the Phase B invariant model, Phase C architecture
comparison, owner-confirmed Phase D deposit design, and owner-confirmed Phase E
backing/debt-health design testable, together with the owner-confirmed Phase F
external-settlement and total-loss directions and the owner-confirmed Phase G
post-zero freeze, no-automatic-allocation, and live-claim reward directions,
plus the owner-authorized Phase H controls, governance, clock, and operational
evidence analysis and the owner-authorized Phase I compatibility/migration
inventory.
The instructions select option 4, containment followed by the corrected share
path, then reject a new stored per-asset collateral-use parameter and authorize
Phase E specification using existing deposit controls and `DebtTerms.ltv`.
The owner confirmed both quotes under
`stock-token-vault-change-specification.md` Section 12.1. On 2026-07-24, the
owner also approved the two Phase F policy directions, paused after they were
documented, then approved the three Phase G directions and authorized Phase G
specification work. The owner then authorized Phase H specification only,
directed the work to prefer existing controls and preserve repayment
liveness, and required evidence and alternatives before any new
storage/interface/dedicated-pause/caller selection. After Phase H review, the
owner assented to Phase I specification under the five directions recorded in
specification Section 12.1: existing `canLiquidate` baseline, no dedicated
checkpoint gate by default, permissionless total-loss calling only when fully
deterministic, an existing Switchboard checkpoint caller, and safe-withdraw
preservation. This is checkpoint option 4, the combination of architecture
outcomes 2 and 3, not the separately numbered “another generic shared
design.” All paths below are proposed future paths. No test, fixture, mock,
production contract, interface, storage, dependency, CI file, manifest,
runbook, or ABI was created or changed.

During final Phase I validation, integrated `rh` advanced to `3e6e6f2` with
Track 6 S3. This plan reconciles S3's Lootbox immutable floor, constructor,
getter, ABI, artifact/runtime rules, and still-open Base rollout window. It
does not import that commit into the Track 8 worktree, claim S3 is deployed,
or treat S3's Underscore send floor as the separate Track 8 loss interval.

On 2026-07-24 the owner authorized Phase J specification work only. The
instruction makes all-external fungible settlement the preferred validation
branch subject to complete integration and historical-use evidence; uses an
isolated generic corrected-share variant and `A^s/U^s` as validation targets;
models the two-selector transition without approving the Ledger migration;
preserves S3 independently if Track 8 would delay it; requires Base-first or
atomic convergence; and classifies any empty gated deployment as inactive
staging rather than launch. It expressly does not select a production vault
or ID, authorize implementation or migration, or begin Phase K.

The Phase D–I test contracts and the Phase J record/coverage model now form
the complete future validation specification. Preferred branches remain
conditional and all production mechanisms remain unapproved. Specification
Sections 3.8, 3.10, and 3.12 enumerate the Phase H, Phase I, and Phase J
reconciliation edits made to previously approved specification and
validation-plan surfaces, including gate updates and section renumbering.

On 2026-07-24 the owner authorized Phase K specification work only. The
instruction requires reviewable units, dependencies, audit boundaries, stop
conditions, and atomic Release 0/1/2 groups; preserves the Phase J candidates
as unapproved; isolates the full Ledger migration as a separate high-risk
gate; preserves S3 independence; requires Base-first or atomic convergence;
and classifies empty gated staging as inactive rather than launch. It
expressly approves no production code, test, interface, storage, ABI,
default, migration, manifest, vault/ID, deployment, configuration, or
transaction. Specification Sections 3.13 and 21 record the exact
authorization, integrated S5 reconciliation, final split, unresolved
decisions, and owner checkpoints.

The later 2026-07-24 owner clarification makes Stock Tokens mandatory
initial-launch scope and directs Track 8 to reduce the comprehensive design to
the smallest demonstrably sufficient shared containment patch. Specification
Section 23 is that controlling refinement. This plan's Section 20 validates
the reduced launch group and moves the corrected-share, automatic bad-debt,
Ledger-migration, reward-loss, and recapitalization branches to post-launch
unless a minimum-path prerequisite fails. The current contracts remain
disabled pending implementation evidence; that is an atomic safety gate, not
a product deferral.

Specification Section 3.17 records the independent-review remediation behind
the then-current four-contract profile. The later Section 3.20 reassessment
supersedes its public-short-receipt, CreditEngine raw-backing, AuctionHouse,
and unconditional Base-cutover conclusions. Its still-applicable endpoint,
reward, and eventual-debt evidence is retained.

Specification Section 3.18 records the later local-`rh` documentation advance
at `4966969`. The committed minimum-change reassessment aligns with this
profile and selects no Base Ledger migration; integration lifecycle rows that
still mention automatic bad-debt transition or Stock reward distribution are
conditional, not launch requirements, until Track 7 reconciles them to the
owner-approved Track 8 artifact.

Specification Section 3.19 records the clean independent re-review and the
pinned end-to-end Deleverage recipient trace. The onchain guard is part of
owner surface decision 5, not a separate onchain-versus-runbook choice.

Specification Sections 3.20–3.21 record the pushed-`rh` merges, narrow
reassessment, and independent-review remediation. At that stage, the Track 8
delta was exactly the specification and this plan. Section 20 now
validates a three-contract Robinhood candidate: exact Teller receipt, the
deficit-only guarded-settlement nominal vault, and CreditEngine zero-amount term
preservation. AuctionHouse/Deleverage stay byte-identical; harmless surplus
remains unallocated without freezing; exact-transfer asset compatibility and
Robinhood/Base state independence are pre-implementation evidence gates; Base
remains on existing runtimes unless refreshed evidence proves urgent live
exposure; and every production action remains unapproved. The final
reconciled pushed baseline is
`063d9459c4c0acf29a4d4e59251ad32bf2d71184`; its last increment was
documentation-only and changed no Track 8 source or test. The later M0
owner-decision revision was fast-forward reconciled without history rewrite
to exact reviewed `rh`
`fc48ac45e5f6e8c698a6464a14289aad00e1f2d4` and changes only the four Track 8
documents named in the owner packet.

On 24–25 July 2026, the owner approved the M0 product decisions recorded in
specification Section 3.22 and the M0 decision packet. For initial AAPL,
vault-enforced guarded internal settlement supersedes the earlier external-only
validation preference: external remains the frontend default. The
partial-fill invariant was owner-approved on 25 July. Under that rule, internal
movement is valid only for `0<W<=Q`, exact seller decrease and buyer increase
of `W`, known solvent pre/post custody, unchanged aggregate nominal accounting,
unchanged custody, and payment/debt reduction based only on `W`. The historical
Phase F/I/J external-only tests remain comparison evidence but are not the
operative acceptance branch.

The same decision set freezes AAPL-only Stock launch scope; CCIP as a
nonblocking disabled-if-incomplete target for a separately reviewed promotion
within seven days after launch; chain-native sGREEN day-one value paths;
PSM/Stability/RipeGov/LP targets; launch-disabled rewards with a validated
seven-day activation target; accepted AAPL fork sufficiency; unchanged Base;
fixed AAPL USD exposure targets; one-vault/no-trusted-route cardinality; and
the existing CreditRedeem/Stability/Underscore exclusions. Missing either
seven-day target leaves the feature disabled; neither target is automatic
authorization. This revision specifies tests only; no M1 or production action
is authorized.

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

Current-`rh` reconciliation revalidation of the same unchanged test file:

```text
ETHERSCAN_API_KEY=unused WEB3_ALCHEMY_API_KEY=unused PYTHONPATH=. \
  pytest -q tests/vaults/test_stock_token_vault_comparison.py
=> 90 passed in 51.58s
```

Latest pushed-`rh` merge and independent-review remediation:

```text
ETHERSCAN_API_KEY=unused WEB3_ALCHEMY_API_KEY=unused PYTHONPATH=. \
  python -m pytest -q tests/vaults/test_stock_token_vault_comparison.py
=> 90 passed in 51.05s
```

The integrated harness now reads `ETHERSCAN_API_KEY` at import even for local
selection. The literal `unused` placeholders are non-secret and no fork RPC was
used. An initial invocation without the placeholder stopped before collection
with the import-time `KeyError`; it is not counted as a test result.

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
| `tests/core/lootbox/test_vault_loss_rewards.py` | Rewards/monitoring | `CM-033`, `CM-025`, Ledger | Proposed; Phase G live-claim units specified, integrated S3 floor preserved, separate loss-interval mechanism unapproved |
| `tests/config/test_asset_collateral_controls.py` | Governance/config | `CM-009`, `CM-011`–`CM-013`, existing config/getters | Proposed; Phase E no-new-storage control semantics specified |
| `tests/config/test_stock_token_incident_controls.py` | Governance/operations | `CM-009`, `CM-011`–`CM-013`, MissionControl, LocalGov | Proposed; Phase I uses existing gate/caller directions, no dedicated gate or live action approved |
| `tests/core/creditEngine/test_stock_token_repay_liveness.py` | Credit/control liveness | `CM-030`, `CM-034`, Ledger | Proposed; Phase H requires repayment under containment |
| `tests/core/auctionHouse/test_stock_token_resolution_controls.py` | Resolution/control | `CM-026`, `CM-030`, Ledger | Proposed; existing `canLiquidate` and conditional deterministic caller specified, resolver interface not approved |
| `tests/vaults/test_corrected_share_compatibility.py` | Storage/interface compatibility | `CM-025`, `CM-021`, Vault interfaces | Proposed; Phase I recommends a generic variant but returns its storage/interface |
| `tests/config/test_asset_config_schema_compatibility.py` | Config/ABI compatibility | `CM-009`, `CM-011`–`CM-013`, `ConfigStructs` | Proposed; proves recommended no-new-parameter path and compares the unapproved settlement-mode alternative |
| `tests/config/test_core_cutover_state.py` | Direct-deployment compatibility | Teller, AuctionHouse, CreditEngine, Lootbox, Deleverage, BondRoom, HumanResources, CreditRedeem | Proposed; proves constructor/immutable, pause, local config, pending-action, and cooldown-state parity |
| `tests/data/test_ledger_state_migration.py` | Full Ledger state migration | `CM-008`, `CM-030`, all Ledger readers/writers | Proposed; mandatory if the returned two-selector design is approved |
| `tests/registries/test_vault_book_migration.py` | Vault migration/registry | `CM-021`, vaults, Ledger, manifests | Proposed; Phase I sequence specified, exact IDs/tooling pending Track 7 |
| `tests/probes/test_stock_token_artifact_parity.py` | Artifact/live-version evidence | all changed shared components | Proposed; creation/runtime/registry/manifest parity, no deployment authorized |
| `tests/probes/test_fungible_settlement_usage.py` | Read-only integration/history evidence | `CM-026`, `CM-034`, every deployed Teller/AuctionHouse generation | Proposed; required before the preferred all-external branch can become implementation-eligible |
| `tests/probes/test_stock_token_vault_evidence.py` | Read-only operational evidence | all control/accounting readers | Proposed; Phase H schema/absence/first-observation semantics specified, no probe created |
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
- Base and Robinhood clock profiles, now available on integrated `rh` and to be
  consumed only when Phase J is authorized; and
- the integrated checked block-number inventory assertion, likewise pending
  Phase J reconciliation rather than integration.

## 3. Invariant-to-test map

| Invariant | Named future assertion | Proposed layer | Required result | Owner prerequisite |
| --- | --- | --- | --- | --- |
| I-01 exact receipt | `test_credit_equals_call_local_balance_delta` | Vault/Teller | `A_req`, `Q`, `R`, credited, returned, and emitted amounts reconcile; prior donation excluded | Phase D specified |
| I-01 exact receipt | `test_short_second_deposit_cannot_overcredit_either_path` | Vault/Teller | Both nominal and share paths credit only actual receipt | Phase D specified |
| I-02 borrowing conservation | `test_sum_borrow_amounts_never_exceeds_live_custody` | Property/Credit | Invariant holds across users, deposits, losses, and withdrawals | Architecture |
| I-03 claim conservation | `test_all_withdrawal_orders_are_allocated_backing_bounded` | Property/Vault | Two-user orders cannot allocate more than `A <= C` and never consume `U` | Phase G specified |
| I-03 claim conservation | `test_two_buyers_cannot_allocate_same_remaining_custody` | Auction | Both purchase orders conserve custody | Phase F specified |
| I-04 pay for proved settlement | `test_green_and_debt_commit_only_after_actual_external_delivery`; `test_green_and_debt_commit_only_after_guarded_internal_partial_fill` | Auction/Deleverage/vault | External payment/debt is bounded by `E=min(Q,W,R)`; internal payment/debt uses only the proved `W` satisfying the owner-approved partial-fill invariant below | M0 direction supersedes historical external-only branch |
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
| I-11 guarded settlement | `test_issuer_asset_internal_partial_fill_requires_exact_user_deltas_and_known_solvent_custody`; `test_issuer_asset_external_remains_frontend_default` | Vault/Auction integration | Unsafe internal mode reverts; owner-approved safe partial/full fills preserve nominal, custody, and payment atomicity | Controlling direction |
| I-12 price independence | `test_deficit_guard_survives_missing_or_zero_price` | Credit | Custody status remains visible and fail-closed without price | Phase E specified |
| I-13 quarantine | `test_unsolicited_positive_delta_never_increases_allocated_backing` | Share/property | Donation/restoration changes `C` and `U`, not `A`, claims, credit, settlement, or rewards | Phase G specified; storage/interface pending |
| I-13 quarantine | `test_deposit_allocates_only_call_local_receipt_not_existing_surplus` | Vault/Teller | `A_after = A_before + R`; pre-existing `U` remains unchanged | Phase G specified |
| I-13 quarantine | `test_checkpointed_quarantine_is_not_shareholder_loss_insurance` | Share/property | After bucket checkpoint, an observed negative delta reduces `A` before `U^s`; donation cannot silently shield claims | Phase G specified; storage/interface pending |

The internal-settlement invariant below is the owner-approved validation
target:

```text
0 < W <= Q
sellerNominalDecrease == W
buyerNominalIncrease == W
aggregateNominalAfter == N
known(C0,C1)
C0 >= N
C1 >= N
C1 == C0
payment and debt reduction are based only on W
```

External delivery remains governed by `E=min(Q,W,R)`.

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
| `test_share_deposit_uses_predeposit_allocated_backing_and_rounds_down` | Under specification Section 17, shares equal `floor(R * (S + 10^8) / (A_0 + 1))`; `Q`, aggregate post-custody, and pre-existing `U` cannot enter as the call receipt or allocated denominator. |
| `test_positive_receipt_that_mints_zero_shares_reverts` | No positive custody can be donated through zero-share credit. |
| `test_stab_vault_uses_measured_receipt_without_economic_drift` | GREEN/sGREEN value, claimable-value, virtual-offset, and existing share rules are unchanged except for the verified receipt input. |
| `test_registration_occurs_only_after_credit` | Failed/zero credit cannot add Ledger participation. |
| `test_points_read_postcredit_balance` | Lootbox input state reflects shares/nominal credit from `R`. |
| `test_price_snapshot_occurs_after_measured_credit` | Snapshot is absent on failure and sees the successful post-credit state. |
| `test_deposit_many_measures_each_item_and_is_atomic` | Independent `(C0,C1,R,V,C2,C3)` per item; one failed item rolls back all items and final housekeeping. |
| `test_rebalance_uses_received_deposit_amount` | `TellerRebalance.depositAmount == R`; deposit, withdrawal, and final health check are atomic. |

Specification Section 17 supplies the permanent corrected-share denominator after the owner
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
6. generated ABI/interface consequences match specification Section 19's
   Phase I inventory; and
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
10. specification Section 19's Phase I impact table explicitly records the repayment
    raising-to-non-raising price behavior change and worst-case hot-path call/gas
    results; and
11. the owner separately authorizes implementation.

These are future acceptance conditions, not evidence that any implementation
exists. Phase F policy is specified separately below; its implementation
mechanisms remain gated.

## 8. Phase F settlement and total-loss validation contract

No test in this section exists yet. The policy outcomes are owner-confirmed.
Phase J uses all-external as the preferred validation branch, conditional on
complete integration and historical-use evidence; it does not approve that
behavior change. The per-asset branch remains an unselected comparison/fallback.
The proposed CreditEngine/Ledger selectors and transition caller policy also
remain unapproved. Common tests below are mandatory under either settlement
mechanism. Branch-specific all-external evidence is active for Phase J
planning; no branch becomes production-eligible until its prerequisite owner,
product, security, and migration decisions close.

### 8.1 Current-behavior and mechanism boundary

| Test | Setup | Required result |
| --- | --- | --- |
| `test_current_internal_auction_reproduces_nominal_only_delivery` | Pinned current Simple path after total issuer burn, buyer selects internal | Preserve the Track 5 regression: nominal buyer balance moves and GREEN/debt commit without token delivery |
| `test_current_external_auction_delivery_precedes_payment` | Pinned ordinary external purchase | Token transfer occurs before GREEN transfer and debt reduction |
| `test_no_existing_asset_config_field_means_external_settlement` | Inspect compiled/source `AssetConfig`, `AuctionBuyConfig`, and getters | No existing field is mislabeled or overloaded as the new policy |
| `test_all_external_option_rejects_internal_for_every_fungible_asset` | Preferred Phase J branch after the Section 11.3 usage-evidence gate | Every `_shouldTransferBalance = true` auction request fails/skips without payment; external mode remains functional |
| `test_per_asset_mode_option_is_generic_and_default_safe` | Only if the per-asset mechanism is owner-selected | No token/name/vault/chain branch; issuer fixture is external-required; every migrated existing asset has an explicit reviewed value |
| `test_unselected_mechanism_has_no_schema_or_abi_delta` | Compare a future approved implementation against the selected option | No field/selector/default/migration from the rejected option appears |

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
| `test_phase_h_resolution_gate_matches_later_approved_control` | Existing `canLiquidate` is the Phase I-directed baseline; permissionless calling passes only for a resolver with no caller-supplied value-relevant discretion |
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
5. security review proves the owner-directed conditional permissionless caller
   has no eligibility, amount, recipient, subset, or timing-sensitive value
   discretion and passes repayment-race/griefing analysis;
6. the existing `canLiquidate` branch and caller condition pass Sections 10
   and 11;
7. no nominal partial-loss or recovery allocation is inferred;
8. exact source/interface/storage/ABI diffs match specification Section 19;
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
map them only after the owner selects one of specification Section 19.9's
returned semantics.

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
| `test_issuer_share_asset_has_no_internal_settlement_override` | Historical external-only comparison; the initial AAPL path instead uses specification Section 23.4's guarded nominal-vault proof |

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
| `test_untouched_user_cannot_accrue_stale_post_loss_weight` | A separately approved Track 8 loss epoch/index or checkpoint mechanism handles global share-price change without per-user iteration drift; S3's send floor alone is insufficient |
| `test_pre_loss_points_are_not_clawed_back` | Historical earned points persist while future weight changes |
| `test_price_failure_does_not_change_A_or_backing` | Reward USD may be zero/unavailable, but custody/allocation safety remains visible |
| `test_ripe_gov_lock_points_keep_separate_semantics` | Vault ID 2 governance points are not interpreted as token live claims |
| `test_existing_positive_rebase_mode_is_not_silently_quarantined` | Any retained yield/rebase behavior is an explicit generic mode/variant with separate tests and approval |
| `test_zero_asset_reward_allocations_do_not_prove_stock_rewards_disabled` | Zero staker/voter allocations can enter the current general-depositor value path; they are not accepted as a Stock-specific reward-off switch |
| `test_stock_deposits_remain_disabled_until_loss_reward_gate_closes` | Before the Track 8 loss interval/index/callback is approved, the Stock asset remains omitted or `canDeposit=false`; no live claim can begin accruing stale reward weight |
| `test_inactive_staging_has_zero_stock_reward_state` | Empty gated staging has no Stock users, points, claims, eligible USD value, or reward events and is not reported as launch-ready |

Integrated S3 tests remain mandatory and unchanged for
`MIN_UNDERSCORE_SEND_INTERVAL`, the five-argument constructor, getter, strict
send boundary, and Base/Robinhood floor profiles. The loss-interval tests
remain skipped pending the owner-selected Track 8 mechanism because S3 adds no
loss epoch/index or checkpoint callback.

### 9.8 Events, getters, storage, and compatibility assertions

| Test | Required result |
| --- | --- |
| `test_every_share_surface_declares_its_unit` | Raw shares, `C`, `A^s`, `U^s`, `A`, `U`, claims, normalized reward weight, and USD value are unambiguous |
| `test_deposit_withdraw_transfer_events_reconcile_amount_and_shares` | Amount is allocated call-local token units; shares are raw units |
| `test_loss_and_quarantine_evidence_reconstructs_state` | Asset, old/new `A^s/U^s`, `C`, `A`, `U`, caller, block/clock, and reason reconcile with getters |
| `test_amount_share_conversion_getters_use_A` | Existing-signature or replacement getters match the specification Section 17 reference model and exclude `U` |
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
3. owner/security approve one of specification Section 19.9's returned
   allocated-backing mechanisms, storage/ABI boundary, and live migration;
4. positive-rebase/yield compatibility is explicitly separated and tested;
5. no automatic donation/restoration/recovery/recapitalization path exists;
6. counsel/risk remain a hard gate for any later quarantine disposition;
7. Phase F delivery and exactly-once liability invariants compose with share
   burn and allocated backing;
8. integrated S3's floor/constructor/getter/strict-boundary behavior remains
   intact and a separately approved Track 8 mechanism closes loss-interval
   semantics and stale-user weighting;
9. RipeGov governance units remain intact;
10. Base vault-ID-4 dust and every custody-bearing live vault are reconciled;
11. exact-token fork, Base regression, dual-clock, migration, and audit gates
    pass; and
12. owner approval explicitly names the production vault/version and atomic
    release group.

This Phase G validation contract approves no implementation mechanism or
later phase.

## 10. Phase H controls, governance, and evidence validation contract

These are future test and evidence contracts for specification Section 18.
They do not approve a transaction, new storage/interface/event/ABI, dedicated
pause, total-loss or checkpoint caller, Robinhood default, production vault,
implementation, or migration.

Proposed future paths, aligned with existing repository directories:

```text
tests/config/test_stock_token_incident_controls.py
tests/core/creditEngine/test_stock_token_repay_liveness.py
tests/core/auctionHouse/test_stock_token_resolution_controls.py
tests/registries/test_vault_book_migration.py
tests/probes/test_stock_token_vault_evidence.py
```

No path is created by Phase H. At the Phase H handoff every
alternative-specific branch remained skipped. The later Phase I direction
activates only the existing-`canLiquidate`, conditional zero-discretion
resolver, existing-Switchboard checkpoint caller, and safe-withdraw test
branches; any new-gate, new-role, or discretionary-caller alternative remains
skipped pending a separate owner decision.

### 10.1 Current control-map assertions

| ID | Test | Required result |
| --- | --- | --- |
| T8H-01 | `test_global_borrow_fast_disable_and_governed_enable` | Governance and current lite actor can set `canBorrow=false` immediately; lite re-enable fails; event caller/value and post-state getter reconcile |
| T8H-02 | `test_collateral_use_is_derived_not_a_hidden_flag` | Repository storage/interface inventory finds no dedicated field; result composes asset `canDeposit`, nonzero LTV, backing safety, and nonzero live position exactly as Phase E specifies |
| T8H-02 | `test_ltv_nonzero_to_zero_is_not_an_incident_switch` | Current Bravo validation rejects nonzero→zero and all debt-term actions use `TimeLock` |
| T8H-03 | `test_deposit_requires_general_and_asset_flags` | Either false blocks Teller validation; fast asset disable removes affected new-borrow capacity without changing debt |
| T8H-04 | `test_auction_purchase_requires_general_and_asset_flags` | Either false makes every purchase recheck return zero without GREEN spend, debt reduction, collateral movement, or auction progress |
| T8H-05 | `test_current_settlement_mode_is_buyer_input_not_config` | `getAuctionBuyConfig` has no settlement field; default false remains overrideable by current caller and is not mislabeled enforced external-only |
| T8H-06 | `test_withdraw_requires_general_and_asset_flags` | Each flag has the documented immediate asymmetric authority; safe per-asset withdrawal remains separable from deposit/borrow/purchase containment |
| T8H-07 | `test_repay_requires_can_repay_and_unpaused_dependencies` | `canRepay`, Teller, CreditEngine, and Ledger are all independently observed; a successful repayment changes exact user/global debt and emits the existing repay evidence |
| T8H-08 | `test_liquidation_initiation_requires_can_liquidate` | False blocks ordinary liquidation immediately without blocking standard repayment |
| T8H-09 | `test_current_bad_debt_setter_is_global_timed_overwrite` | Current Delta action is governance/timelocked and writes an absolute Ledger value; no per-user exactly-once selector/event/control exists |
| T8H-10 | `test_asset_and_vault_registration_authority_and_events` | Bravo/VaultBook/Charlie callers, pending state, confirmation blocks, execution events, and iterable getters reconcile; deposit-side vault-local registration is identified separately |
| T8H-10 | `test_deregistered_asset_stale_config_is_not_supported` | MissionControl iterable/index membership is removed while the raw config mapping may persist; operations and reports key eligibility from explicit supported membership plus config, never stale config alone |
| T8H-11 | `test_vault_registry_change_never_moves_state` | Update/disable changes only registry authority after its guard/timelock; custody, raw accounting, users, debt, and auctions do not migrate |
| T8H-12 | `test_emergency_controls_are_composed_not_single_state` | General flags, asset flags, and target pauses are read separately with exact caller/event/getter evidence |

Every control test must assert both authority failure and state-root
equivalence on rejection. An expected revert is not sufficient if a previous
partial write or token transfer can survive.

### 10.2 Defaults and fail-closed configuration

| Test | Required result |
| --- | --- |
| `test_defaults_base_general_flags_match_source` | All ten `DefaultsBase.genConfig` booleans are decoded and the T8H-01/T8H-03/T8H-04/T8H-06/T8H-07/T8H-08 values are true |
| `test_add_asset_omitted_booleans_are_not_stock_safe` | Current omitted arguments are proven to enable swap/instant-auction/deposit/withdraw/redeem/auction/claim routes named in Section 18.4 |
| `test_robinhood_defaults_contract_is_absent` | Absence is reported as “not implemented,” not as a deployed false value |
| `test_stock_asset_action_requires_every_boolean_explicit` | Future action-construction test fails if a standing Stock constraint is omitted or inherits a function default |
| `test_stock_prelaunch_posture_is_disabled_or_omitted` | Deposit, LTV/capacity, auction purchase, collateral redemption, Stability Pool, Endaoment, Curve, Aerodrome, Underscore, and yield routes remain absent/disabled |
| `test_repayment_liveness_is_explicit_not_inferred_from_absence` | A future RH config cannot pass merely because no config exists; it must prove `canRepay=true` and unpaused dependencies before debt is possible |
| `test_source_default_is_not_reported_as_live_base_state` | Reports separate committed default values from a pinned live getter read |

No test may generate or modify `DefaultsRobinhood`, a parameter file, or a
manifest until separately authorized.

### 10.3 Fast-control authority and event/getter reconciliation

For every Alpha/Charlie fast flag and Charlie broad pause:

1. governance disable succeeds;
2. configured lite-signer disable succeeds;
3. unconfigured actor disable fails atomically;
4. governance enable/unpause succeeds;
5. lite-signer enable/unpause fails atomically;
6. same-value writes fail without a misleading event;
7. event transaction hash, block, log index, target, value, and caller match;
8. operation-specific MissionControl getter or target `isPaused` matches the
   post-state; and
9. the authority snapshot at that block identifies the caller's actual role.

Named tests:

| Test | Required result |
| --- | --- |
| `test_lite_actor_can_only_reduce_operational_surface` | Lite actor can disable/pause and cannot re-enable/unpause |
| `test_governance_and_lite_getters_match_authority` | `canGovern`, `getGovernors`, `canPerformLiteAction`, and lite-signer iteration agree |
| `test_flag_event_and_consumer_getter_match_same_block` | Raw storage and operation-specific composed getter both show the intended value |
| `test_pause_emits_switchboard_and_target_events` | `PauseExecuted` plus exact target pause event reconcile to `isPaused` |
| `test_fast_actions_do_not_depend_on_number_progress` | Same/repeated/jumping block-number profiles do not add a timelock or authority bypass |

### 10.4 Repayment-safe containment and blast radius

| Test | Required result |
| --- | --- |
| `test_repay_succeeds_with_asset_deposit_and_auction_disabled` | Indebted user can repay while affected asset deposit/capacity/purchase are frozen |
| `test_repay_succeeds_with_global_borrow_and_auction_disabled` | Conservative global bridge does not consume `canRepay` or block standard repayment |
| `test_fast_asset_disable_tightens_capacity_without_false_liquidation` | Phase E capacity/resolution split remains intact and no control action itself manufactures liquidation eligibility |
| `test_teller_pause_blocks_standard_repayment_current_behavior` | Pinned current behavior demonstrates why Teller broad pause is not normal containment |
| `test_credit_engine_pause_blocks_standard_repayment_current_behavior` | Pinned current behavior demonstrates the same for CreditEngine |
| `test_ledger_pause_blocks_repayment_debt_commit_current_behavior` | Pinned current behavior demonstrates the same for Ledger |
| `test_asset_withdrawal_stays_open_when_delivery_is_safe` | Incident containment does not automatically block a deliverable user exit |
| `test_unsafe_delivery_uses_asset_not_global_withdraw_freeze` | If delivery is unsafe, per-asset freeze contains that route and records the liveness loss without unnecessarily freezing unrelated assets |
| `test_incident_sequence_never_reenables_automatically` | Runbook/monitor has no signer, broadcast, or re-enable path |

Each liveness test must begin with nonzero debt and end with exact reduced debt,
not merely a successful boolean or non-reverting preview.

### 10.5 Resolution-gate alternatives

Common tests run against any later owner-selected gate:

| Test | Required result |
| --- | --- |
| `test_resolution_gate_blocks_transition_before_any_write` | Disabled gate leaves user debt, global debt, bad debt, auctions, yield, shares, and events unchanged |
| `test_resolution_gate_reenable_requires_governance` | No lite or arbitrary caller resumes resolution |
| `test_resolution_gate_state_is_event_and_getter_reconstructible` | Caller, target/value, transaction/log identity, and post-state are exact |
| `test_resolution_gate_does_not_block_standard_repayment` | User can repay while resolution is disabled |
| `test_resolution_gate_number_profile_is_explicit` | Immediate or timed semantics match the selected existing control under repeated/jumping `NUMBER` |

Alternative-specific placeholders:

| Alternative test | Required result / gate |
| --- | --- |
| `test_can_liquidate_gate_couples_resolution_and_all_liquidation` | If owner selects reuse, disabling it blocks both flows, preserves repayment, and exposes the full global blast radius |
| `test_department_pause_is_rejected_as_normal_resolution_gate` | Current Teller/CreditEngine/Ledger pause cases fail I-09; no implementation may satisfy acceptance with only these pauses |
| `test_dedicated_resolution_pause_matches_owner_approved_surface` | Skipped until a later owner authorization names the exact interface/storage/event/default; Phase H supplies no expected ABI |
| `test_no_gate_means_no_listing` | Without an approved safe gate, launch validation fails closed |

### 10.6 Caller-policy alternatives

No test assumes that “keeper,” “Department,” or “governance” has been selected.
The later owner-selected branch must satisfy its entire row:

| Alternative | Required future tests |
| --- | --- |
| Permissionless deterministic | `test_public_caller_has_no_eligibility_amount_recipient_or_timing_value_input`; `test_public_repay_race_is_accounting_safe`; separate security assertion on timing/griefing acceptability |
| Restricted existing actor | `test_restricted_actor_is_proven_by_existing_getter`; `test_unapproved_actor_fails_atomically`; `test_actor_unavailability_does_not_block_repayment`; no invented offchain role name |
| Governance per transition | `test_pending_transition_requires_governance`; `test_repeated_number_stalls`; `test_jump_enters_or_expires_window`; `test_repay_before_confirmation_wins_compare_and_set` |
| No listing | `test_missing_caller_policy_blocks_release` |

The total-loss and checkpoint callers are separate decisions even if a later
proposal combines them atomically. Tests must not inherit one policy from the
other.

### 10.7 Share-loss checkpoint controls

| Test | Required result |
| --- | --- |
| `test_asset_containment_is_prerequisite_not_checkpoint_authority` | Deposit/purchase disable changes no `A^s/U^s`, shares, claim, or loss record |
| `test_checkpoint_caller_cannot_choose_loss_or_allocation` | Any later caller observes current custody and specified stored state; it cannot supply beneficial allocation or donation-recipient inputs |
| `test_checkpoint_timing_and_restoration_are_explicit` | Reduce→checkpoint→restore produces `U`; reduce→restore without observation is recorded as indistinguishable |
| `test_vault_pause_blast_radius_covers_every_asset` | If used as containment, all vault deposit/withdraw/transfer paths are enumerated and standard repayment remains separately tested |
| `test_checkpoint_gate_and_caller_are_unselected` | Phase H ABI/storage/event inventory contains no invented expected selector or field |
| `test_no_durable_checkpoint_means_no_listing` | Persistent post-zero freeze cannot pass without a later approved mechanism |

### 10.8 Operational snapshot and first-divergence evidence

The future repository probe must be tested without network secrets or writes:

| Test | Required result |
| --- | --- |
| `test_snapshot_requires_block_hash_consistency` | Requested block, returned block, and every `eth_call` block tag agree or the probe exits nonzero |
| `test_snapshot_records_raw_and_decoded_values` | Raw response hex, decoded integer/address/struct, unit, source selector, target, and failure class are retained |
| `test_basic_units_separate_custody_and_nominal` | `C`, aggregate/user `N`, and `max(N-C,0)` reconcile without rewriting either |
| `test_share_units_separate_custody_shares_and_claim` | `C`, aggregate/user raw shares, and current live-claim getters are distinct; shares are never labeled tokens |
| `test_unimplemented_allocation_fields_are_null` | Current path reports `A^s/U^s/A/U` unavailable/not implemented, never derives them from a donation |
| `test_borrower_enumeration_matches_ledger` | `getNumBorrowers()` and `borrowers(1..count)`, then each normalized user-vault count/index, debt, and affected position read reconcile |
| `test_auction_enumeration_matches_ledger` | One-based next-index values for liquidation users and user auctions are converted to `1..value-1`; every entry reconciles with direct lookup and debt state |
| `test_debt_free_depositor_limit_is_disclosed` | Report identifies event/indexer/known-user source and never claims Ledger borrower enumeration covers all depositors |
| `test_first_divergence_is_an_observation_window` | Output names last clean and first unsafe pinned observations; without both, causal block remains unknown |
| `test_external_balance_change_needs_no_ripe_event` | Issuer burn/donation can change `C` without a Ripe accounting event; polling comparison detects but does not backfill a fictitious event |
| `test_does_vault_have_funds_is_not_used_as_custody` | Base ID-4 dust case reports the boolean and positive custody/raw accounting separately |
| `test_snapshot_is_read_only` | No private key, signer, transaction construction, state override presented as live, or broadcast RPC method is reachable |
| `test_monitor_cannot_allocate_write_resolve_migrate_or_reenable` | Schema/tool has no action field or side-effect callback; unsupported action request fails |

Fixture coverage must include:

- Basic nominal solvent, one-unit deficit, partial deficit, and total deficit;
- Shares solvent, partial loss, total loss, restored custody after a recorded
  loss, and donation dust with zero shares;
- zero, one, and multiple borrowers;
- debt-free depositor not present in Ledger borrower iteration;
- inactive, active, paused, expired-by-jump, and removed auctions;
- missing registry address, unsupported asset, reverting token getter,
  missing historical/archive state, and rate-limited RPC; and
- multiple relevant transactions/logs in one block, with final block-state
  reads and transaction/log indices used to reconstruct ordering without
  claiming intermediate `eth_call` state.

### 10.9 Clock, registry, and absence assertions

| Test | Required result |
| --- | --- |
| `test_config_action_repeated_number_cannot_confirm` | Bravo/Charlie/Delta pending action remains pending before confirmation |
| `test_config_action_jump_can_enter_or_skip_expiration` | Exact confirmation/expiration inequalities match `TimeLock`; skipped window does not execute |
| `test_registry_repeated_number_cannot_confirm` | VaultBook/AddressRegistry remains pending |
| `test_registry_jump_can_confirm_without_expiration` | Once at/after `confirmBlock`, governance may confirm after revalidation; jump alone does not execute |
| `test_active_auction_rechecks_flag_after_number_jump` | Time jump never bypasses current purchase flag or custody/delivery check |
| `test_missing_mission_control_fails_closed` | No flag/config consumer becomes enabled |
| `test_missing_vault_returns_zero_or_reverts_at_documented_boundary` | Exact current boundary is recorded and no payment/debt/state survives |
| `test_unsupported_asset_fast_flag_fails_atomically` | Charlie rejects before MissionControl mutation/event |
| `test_registry_update_guard_reads_accounting_and_snapshot_reads_custody` | Current guard result and independent custody/share/accounting evidence are both retained |

### 10.10 Phase H acceptance and historical owner stop

Phase H validation specification is acceptable when:

1. T8H-01–T8H-12 each have authority, timing, asymmetry, event, getter, default,
   clock, and absence assertions;
2. fast disable and governance-only re-enable are proven for every relied-on
   flag;
3. standard repayment succeeds under normal containment and the broad-pause
   current-behavior failures remain pinned;
4. `addAsset` omitted defaults cannot pass a Stock Token configuration review;
5. live Base state, source defaults, and absent Robinhood defaults are never
   conflated;
6. the snapshot schema exposes custody, nominal accounting, raw shares, live
   claims, flags, users, debt, auctions, and observation limits with explicit
   units;
7. first divergence is an evidence window, not an invented historical fact;
8. no monitor or probe can write, allocate, resolve, migrate, or re-enable;
9. gate/caller alternatives remained skipped at the Phase H checkpoint and no
   expected new ABI was invented; and
10. Phase H stopped before Phase I.

The later owner direction recorded in specification Section 12.1 resolves the
Phase I control/caller assumptions only as tested in Section 11 below. It does
not retroactively make Phase H an interface/storage approval.

## 11. Phase I compatibility, artifact, and migration validation contract

All tests in this section are proposed. They verify the alternatives and
migration consequences returned by specification Section 19; they do not
approve an interface, storage layout, artifact, migration, or production
vault.

### 11.1 Direct-deployment and storage-layout assertions

| Test | Required result |
| --- | --- |
| `test_protocol_components_are_direct_deployments_not_upgradeable_proxies` | Pinned Base Ripe components have direct runtime code; no repository proxy/beacon/delegatecall upgrade path is assumed. A future live run resolves every registry address and code hash independently. |
| `test_module_change_recompiles_every_consuming_wrapper` | A controlled compile demonstrates that changing `SharesVault`/`VaultData` changes every composing wrapper artifact; no module is treated as a separately patchable library. |
| `test_teller_deposit_mutex_is_transient_only` | Approved implementation candidate adds no persistent Teller slot; lock is transaction-local, clears on every success/revert, and has no external getter/setting authority. |
| `test_existing_vault_balance_units_never_change` | `VaultData.userBalances/totalBalances` remain nominal units for Basic and raw shares for share wrappers; no migration or source change reinterprets stored units. |
| `test_corrected_variant_minimum_state_is_two_buckets` | Candidate fresh layout represents `A^s` and `U^s`; `S>0 && A^s==0` persists the freeze without an extra allocation/beneficiary/collateral-use field. |
| `test_corrected_variant_storage_layout_matches_compiler_metadata` | Declared layout/order and compiled storage metadata match exactly; migration tooling refuses a different compiler/source/layout hash. |
| `test_direct_department_cutover_preserves_pause_and_constructor_posture` | Teller, AuctionHouse, CreditEngine, Lootbox, and Deleverage reproduce reviewed RipeHq/mint-permission immutables and current pause state; constructor defaults are not substituted for live reads. |
| `test_credit_engine_cutover_preserves_live_local_config` | `undyVaulDiscount` and `buybackRatio` match the pinned old deployment before activation and all setters/events remain compatible. |
| `test_lootbox_cutover_reconciles_local_reward_timing_config` | Integrated S3 immutable floor/constructor posture plus Underscore enablement, send interval, reward amounts, and pause match the approved chain profile/live snapshot. `lastUnderscoreSend` follows the separately owner-selected S3 final-distribution/partial-window/continuity policy; zero-reset is not silently accepted. Ledger-owned point state is reconciled separately. |
| `test_deleverage_cutover_cannot_shorten_user_cooldown` | Config and per-user `lastDeleverageBlock` migrate exactly, or a separately approved disable-and-wait cutover proves every remaining cooldown elapsed before activation; zero-map reset fails. |
| `test_stability_pool_wrapper_change_requires_full_state_and_custody_migration` | A StabVault caller-exactness edit recompiles StabilityPool; every user/asset share, enumeration, claimable balance/asset, pause, and token custody root migrates exactly before activation. |
| `test_bond_room_cutover_preserves_booster_pause_and_ledger_bond_state` | Local booster/pause/constructor state and Ledger bond/bad-debt epoch state reconcile; exact Teller stake return is atomic with payout accounting. |
| `test_human_resources_cutover_preserves_governance_timelock_and_pending_actions` | LocalGov, TimeLock, pending contributor actions, pause, and Ledger contributor/reward state migrate without changing caller authority or confirmation windows. |
| `test_credit_redeem_cutover_preserves_pause_and_stock_redemption_disable` | Exact Teller sGREEN return is enforced while constructor/pause parity and the standing Stock redemption-disabled posture remain unchanged. |
| `test_fresh_ledger_deployment_starts_empty` | Demonstrates why registry replacement without full migration loses Ledger state; test must not normalize an empty fresh Ledger into success. |
| `test_fresh_mission_control_deployment_requires_complete_config_import` | Every general/debt/reward/asset/user/config and enumeration value plus pause/constructor posture differs from or is unproven against a populated source unless explicitly migrated; manifest address replacement alone is insufficient. |

### 11.2 Interface, selector, event, and schema compatibility

| Test | Required result |
| --- | --- |
| `test_canonical_vault_interface_remains_unchanged` | Existing Vault selectors/return tuple shapes are byte-for-byte identical under the recommended generic-variant boundary. |
| `test_corrected_variant_is_a_vault_abi_superset` | Candidate specialized state/checkpoint views are additive; every canonical Vault call retains its exact encoding and documented per-wrapper unit. |
| `test_checkpoint_has_no_caller_supplied_value_or_allocation` | Candidate call accepts only the asset, derives bucket changes from current state, and gives caller no amount, recipient, beneficiary, or mode discretion. |
| `test_checkpoint_requires_existing_asset_containment` | `canDeposit=false` and `canBuyInAuction=false` are required; neither flag alone authorizes the call. |
| `test_checkpoint_requires_existing_switchboard_actor` | `addys._isSwitchboardAddr(caller)` is required with no new role mapping; unauthorized Ripe Departments, users, and keepers fail atomically. |
| `test_checkpoint_remains_live_while_vault_paused` | Broad vault pause does not prevent the restricted accounting checkpoint; deposits/withdrawals retain their separate pause behavior. |
| `test_resolution_consumes_existing_can_liquidate` | Resolver succeeds only while the existing global control is true; disabling it stops ordinary liquidation and resolution but not repayment. |
| `test_permissionless_resolution_has_zero_caller_discretion` | Candidate resolver accepts only `user`; contract derives all positions, debt, amount, auction cleanup, and bad-debt target. An implementation with caller-supplied subsets/amounts fails this gate. |
| `test_two_selector_transition_encoding_and_authority` | CreditEngine external selector and CreditEngine-only Ledger selector encode exactly as reviewed; unauthorized direct Ledger call fails. |
| `test_existing_events_and_selectors_remain_compatible` | Teller/Auction/vault existing event signatures and public selectors are unchanged except explicitly approved additive surfaces. |
| `test_new_events_report_units_and_before_after_state` | Measurement, checkpoint, and loss-transition events expose exact units, previous/new values, caller, and ordering without reusing `RepayDebt`. |
| `test_track8_lootbox_preserves_integrated_s3_abi_and_boundary` | Candidate keeps S3's five-argument constructor order, immutable floor, getter, strict send condition, and approved Base/Robinhood floor profiles byte-for-byte unless a separately reviewed S3 reopening approves a delta. |
| `test_s3_send_floor_is_not_treated_as_loss_interval` | The existing S3 getter/floor cannot make untouched users adopt a changed vault claim; Track 8 loss-interval tests stay skipped until their own mechanism is approved. |

### 11.3 Settlement-mechanism alternatives and usage evidence

These are branch tests. All-external is the owner-directed preferred Phase J
validation path, not an approved behavior change; the per-asset mode is an
unselected fallback comparison.

| Test | All-external candidate | Per-asset-mode candidate |
| --- | --- | --- |
| `test_internal_auction_request_is_never_silently_reinterpreted` | `_shouldTransferBalance=true` rejects before custody/payment/debt changes | Rejects for an external-required asset; succeeds only for a separately enabled internal-safe asset |
| `test_all_external_preserves_config_schema` | `AssetConfig`, MissionControl storage, Switchboards, defaults, getters, and ABIs unchanged | Not applicable |
| `test_per_asset_mode_full_struct_round_trip` | Not applicable | Every existing field survives add/update/migration byte-for-byte and new field is explicit |
| `test_per_asset_mode_default_is_fail_closed` | Not applicable | Omitted/new assets cannot inherit internal settlement; every Base asset gets an explicit migrated value |
| `test_no_current_product_depends_on_internal_auction_settlement` | Inventory/fork every current asset and historical relevant event; product owner evidence required before branch approval | Existing internal consumers are identified and explicitly configured |
| `test_external_delivery_is_measured_for_every_asset` | Required | Required for every external-mode asset |

This historical all-external comparison branch cannot pass on code reasoning
or default arguments alone. The proposed
`tests/probes/test_fungible_settlement_usage.py` evidence job must:

1. enumerate every chain/environment in which the shared fungible
   Teller/AuctionHouse path has been production-reachable, every registry
   address generation, activation/retirement block, selector, and runtime
   hash;
2. inventory every repository, frontend, SDK, keeper, bot, and operational
   integration identified by product/operations, pinning its revision and
   searching both named and encoded calls for `buyFungibleAuction`,
   `buyManyFungibleAuctions`, and `_shouldTransferBalance=true`;
3. scan the complete activation-block-to-pinned-tip transaction range for
   calls to every Teller generation, decode both fungible purchase selectors,
   and record the boolean argument for successful and reverted transactions;
4. correlate decoded calls with AuctionHouse purchase events, token transfers,
   vault nominal/share changes, and internal `transferBalanceWithinVault`
   effects so an indexer omission cannot be mistaken for external-only use;
5. record RPC/indexer providers, chain IDs, block hashes/ranges, archive
   capability, pagination, rate limits, failed ranges, duplicate handling,
   raw transaction hashes/calldata, decoder/source/ABI hashes, and a coverage
   root;
6. fail closed on any unscanned block range, unknown historical runtime,
   undecodable relevant calldata, incomplete offchain integration inventory,
   or disagreement between providers; and
7. require product plus protocol/security sign-off that every discovered
   internal-mode dependency is absent or intentionally removable.

Named assertions:

- `test_every_teller_generation_has_complete_history_coverage`;
- `test_fungible_purchase_calldata_decodes_settlement_boolean`;
- `test_true_internal_mode_call_is_reported_with_transaction_evidence`;
- `test_history_gap_or_unknown_runtime_blocks_all_external_approval`;
- `test_offchain_integration_inventory_is_revision_pinned`;
- `test_default_false_is_not_usage_evidence`; and
- `test_no_current_product_depends_on_internal_auction_settlement`.

Zero matching `true` calls is meaningful only when all seven conditions pass.
Any `true` call does not automatically select the per-asset mode, but it
returns the behavior/removal decision to product, protocol, and security
before implementation.

Acquisition is a separately authorized read-only RPC/indexer operation. The
pytest surface consumes a sanitized, content-hashed evidence artifact and
replays decoding/coverage checks offline; it contains no private key, signer,
transaction builder, or broadcast method. Phase J neither performs the scan
nor creates that artifact.

### 11.4 Corrected-variant compatibility and migration import

| Test | Required result |
| --- | --- |
| `test_existing_rebase_positive_delta_semantics_unchanged` | Current Rebase/yield assets continue to allocate their intended positive balance changes; corrected quarantine behavior is isolated. |
| `test_ripe_gov_lock_and_points_semantics_unchanged` | RipeGov shares, locks, points, and exits remain exact; only the separately approved Teller-only locked-deposit authorization changes. |
| `test_corrected_variant_positive_delta_is_quarantine` | Candidate variant alone applies specification Section 17 `U` semantics. |
| `test_migration_import_preserves_exact_raw_shares_and_indexes` | One-time candidate import reproduces every user/asset share, aggregate, and one-based enumeration exactly. |
| `test_migration_import_sets_proven_allocated_and_quarantine_buckets` | Seeding requires a pinned entitlement/custody proof; it never defaults `A^s=C`. |
| `test_migration_import_is_paused_authorized_idempotent_and_sealed` | Unauthorized/duplicate/post-finalize imports fail; finalization is irreversible and leaves no standing migration mint power. |
| `test_ordinary_deposit_replay_is_not_accepted_as_state_migration` | Reordered deposits/rounding/donation setup demonstrates non-equivalence and the rehearsal rejects it. |
| `test_empty_robinhood_inactive_staging_needs_no_user_import` | Fresh empty state has zero users/shares/buckets and needs no user import; it remains unreachable/disabled and makes no claim about Base migration or production eligibility. |
| `test_empty_gated_state_is_not_launch_evidence` | Empty custody plus disabled deposit/borrow/auction/reward paths can prove artifact/config staging only; launch/listing/selected-vault gates remain failed. |
| `test_inactive_staging_can_be_abandoned_without_registry_or_user_state` | Before any activation, seed, custody, or economic write, abandoning the candidate leaves all live registries, users, custody, debt, auctions, and rewards unchanged. |

### 11.5 Ledger full-state migration

Phase J models the two-selector transition for atomicity but does not authorize
its interfaces or Ledger migration. If that option is later selected, every
current Ledger domain must migrate and reconcile. Named assertions:

- `test_ledger_migration_preserves_last_touch_and_locked_accounts`;
- `test_ledger_migration_preserves_user_vault_indexes_bidirectionally`;
- `test_ledger_migration_preserves_user_total_debt_borrowers_and_intervals`;
- `test_ledger_migration_preserves_unrealized_yield`;
- `test_ledger_migration_preserves_global_asset_user_deposit_points`;
- `test_ledger_migration_preserves_global_and_user_borrow_points`;
- `test_ledger_migration_preserves_fungible_auctions_and_liquidation_users`;
- `test_ledger_migration_preserves_hr_bond_bad_debt_and_pool_debt`;
- `test_ledger_migration_preserves_department_pause_and_constructor_posture`;
- `test_ledger_migration_preserves_all_aggregate_sums_and_one_based_indexes`;
- `test_ledger_migration_rejects_missing_duplicate_or_reordered_entries`;
- `test_ledger_cutover_is_blocked_until_source_and_target_roots_match`; and
- `test_post_cutover_total_loss_transition_is_exactly_once`.

No partial domain migration may pass. The fixture must populate every mapping
class, not only debt/bad debt.
`test_two_selector_runtime_cannot_activate_without_full_ledger_migration`
must fail any plan that treats interface approval, a manifest address, or an
empty fresh Ledger as sufficient activation evidence.

### 11.6 Vault migration state machine

Run property/state-machine tests over:

```text
uncontained
-> contained
-> enumerated
-> reconciled
-> new artifacts deployed inactive
-> batches seeded/moved
-> roots reconciled
-> registry/config activated disabled
-> old address retired
-> post-state soaked
```

Required named tests:

| Test | Required result |
| --- | --- |
| `test_event_and_storage_user_enumeration_reconcile` | Historical candidates plus Vault/Ledger state produce no missing/duplicate user/asset; borrower enumeration alone is explicitly insufficient. |
| `test_failed_token_read_is_not_zero_balance` | Revert/malformed/rate-limit/archive failure stops reconciliation. |
| `test_nominal_deficit_blocks_migration_without_owner_allocation` | `C<T` never becomes implicit pro rata or first-user allocation. |
| `test_positive_unresolved_custody_blocks_migration` | Donation/restoration cannot be assigned by migration order. |
| `test_active_auction_is_settled_or_paused_before_move` | No auction retains a claim on moved custody; no zero-delivery payment occurs. |
| `test_repayment_stays_live_for_every_migration_state` | Borrow/deposit/auction containment never pauses standard repay. |
| `test_partial_batch_failure_is_atomic_and_resumable` | Failed transaction changes neither side; prior committed batches remain uniquely recorded and both vaults stay non-credit-eligible. |
| `test_old_and_new_positions_are_never_both_credit_eligible` | Across every intermediate state, aggregate capacity counts each entitlement at most once. |
| `test_literal_custody_blocks_old_vault_retirement` | ID-4-style `shares=0,C>0` fails retirement despite current legacy funds boolean. |
| `test_old_user_asset_and_ledger_indexes_are_cleaned` | Zero raw balances, deregistration, points checkpoint, and Ledger participation removal all reconcile. |
| `test_vault_book_address_change_never_moves_state` | Registry update alone leaves custody/storage at the old address and cannot satisfy migration. |
| `test_forward_and_reverse_migration_stop_on_issuer_freeze` | Transfer restriction is a stop; no claim rewrite is permitted. |

### 11.7 Artifact, manifest, and live-version checks

| Test | Required result |
| --- | --- |
| `test_manifest_deployment_is_not_registry_activation` | New manifest address with old live registry resolution is reported as inactive/version-skew, not successful deployment. |
| `test_manifest_records_source_abi_args_creation_and_runtime_hashes` | Every approved artifact has complete reproducible metadata and a content hash. |
| `test_track_8_does_not_invent_or_reuse_track_7_ids` | Every Track 8 RH migration ID/namespace remains `pending Track 7`; S3's recorded `0010_Track6S3LootboxFloor.py` meaning is recognized as S3-owned and cannot be reused for Track 8. Duplicate/ad-hoc values fail. |
| `test_base_and_robinhood_shared_artifact_and_immutable_runtime_derivation` | Source/compiler/constructor schema/creation artifact match; each runtime hash is reproduced from approved chain constructor args, including S3 RipeHq/floor immutables. Any other difference is version skew with expiry/abort evidence. |
| `test_s3_source_live_skew_and_pending_window_are_explicit` | Integrated S3 source/ABI and the dated old Base Lootbox runtime are reported separately; no Track 8 record claims S3 deployment or resolves its open distribution window. |
| `test_track8_lootbox_delta_reopens_or_sequences_after_s3_review` | A combined source delta fails unless it is ready without delaying S3 and S3 review is explicitly reopened; otherwise S3 proceeds independently and a later Track 8 cutover includes its own migration/window/rollback record. |
| `test_track8_cannot_delay_required_s3_safety_rollout` | If Track 8 loss-weighting design, economics, audit, or migration gates are still open at the S3 release decision, the combined branch fails and the independent S3 branch remains available. |
| `test_base_release_one_can_retain_reconciled_simple_storage` | ID-3 custody need not move when live nominal state is fully backed/reconciled and remains disabled for Stock listing, but every Teller exact-receipt caller and its local/Ledger/vault state satisfies the reviewed cutover plan. |
| `test_teller_and_affected_consumers_never_run_mixed_while_value_paths_are_live` | Any staggered registry update keeps affected deposits, claims, payouts, stakes, redemptions, and deleverage routes contained until Teller and every measured/exact consumer are compatible; repayment remains available throughout. |
| `test_release_two_requires_custody_bearing_vault_migration` | Corrected share adoption cannot be represented by a core-only registry change. |
| `test_robinhood_enablement_requires_base_first_or_atomic_convergence` | RH deposit/borrow/auction/reward enablement fails unless Base already runs the approved shared safety semantics or the reviewed atomic cutover proves both chains converge without a live unsafe value path. |
| `test_inactive_preconvergence_staging_is_unreachable_and_time_bounded` | If an artifact is staged before convergence, no registry/config/value path can reach it, all Stock features remain disabled, an expiry/abort owner is recorded, and the state is never labeled deployment completion or launch. |
| `test_post_deploy_bundle_reconciles_all_roots_and_controls` | Code, registry, immutable/constructor posture, pause, core-local config/cooldown timing, custody, claims, buckets, debt, auctions, rewards, flags, and pending actions match the reviewed bundle before enablement. |
| `test_failed_post_deploy_assertion_keeps_asset_disabled` | No probe auto-repairs or re-enables state. |

### 11.8 Rollback and audit assertions

| Test | Required result |
| --- | --- |
| `test_inactive_deployment_can_be_abandoned_without_state_change` | Before seeding/activation, old live state is unchanged. |
| `test_partial_migration_requires_forward_or_explicit_reverse_plan` | Address flip is rejected as rollback after any seed/custody batch. |
| `test_post_economic-write_address_flip_is_not_rollback` | After borrow, settlement, reward, or bad-debt write under new semantics, old address activation cannot restore prior economics. |
| `test_rollback_never_erases_new_bad_debt_or_rewards` | Reverse reconciliation includes every post-cutover write exactly once. |
| `test_security_review_boundaries_match_source_impact_table` | Teller delta/mutex, Credit backing, Auction delivery, Ledger transition/migration, share math/storage/import, rewards/S3, registry/config, and exact-token behavior each have named reviewers and artifacts. |

### 11.9 Phase I acceptance and historical owner stop

Phase I validation specification is acceptable when:

1. every required source-impact row has storage, compatibility, caller,
   artifact, live-version, migration, rollback, and audit assertions;
2. direct-deployment versus proxy behavior is proven from live/runtime and
   source evidence;
3. recommended no-new-parameter paths preserve ConfigStructs/MissionControl
   schemas;
4. every owner-returned alternative has branch-specific tests and is skipped
   until selected;
5. any Ledger selector approval is inseparable from the full-state migration
   matrix;
6. any corrected-vault approval is inseparable from bucket storage,
   specialized evidence, and one-time import/finalization review;
7. integrated S3 floor/constructor/getter tests stay green, while Track 8
   reward-loss integration remains skipped until the owner approves a
   separate interval/index or checkpoint authority and S3 rollout sequencing;
8. Track 7 owns exact IDs/manifests/tooling and no identifier is improvised;
9. Base/RH artifact parity and post-state reconciliation fail closed; and
10. work stopped before Phase J at the historical Phase I handoff.

The later Phase J authorization selects validation targets only; it does not
retroactively approve a test implementation, new selector, storage,
production vault, or migration.

## 12. Exact-token fork plan

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
8. historical external-only auction delivery comparison plus the controlling
   guarded-internal branch;
9. total-loss repayment and exactly-once resolution; and
10. post-zero freeze/restoration policy;
11. loss-aware reward weighting with no raw-share or quarantine attribution;
12. proxy/beacon/implementation identity before every behavior-sensitive
    phase and fail-closed behavior on an unapproved implementation switch; and
13. inactive staged configuration remains disabled and cannot satisfy launch.

No live signing or broadcast is part of this plan. Live sender/recipient
eligibility, acquisition, gas, approvals, and legal permission remain separate
owner/counsel gates.

## 13. Dual-clock and identical-artifact integration

The narrow S1/S2 kickoff choices were owner-approved in post-bootstrap
integration commit `ce3805d6079ee87d727486ea82b75cbddc12e46d`. Their implementation
and checked inventory are now available on integrated `rh`; Track 8 has not
imported them. Phase J consumes their reviewed interfaces as future gates:

- run the same reviewed source/compiler/creation artifact under Base and
  Robinhood profiles and reproduce approved immutable-derived runtime
  differences;
- exercise repeated `block.number`, `+1`, and multi-number jumps;
- verify emergency disable, timelocked/stronger re-enable, auctions, debt
  transition, registry changes, and migration sequencing;
- assert no `chain.id` or issuer-name behavior branch;
- run the checked `block.number` inventory enforcement; and
- record source hash, creation/runtime hash, constructor/config differences,
  and approved live-version exceptions.

The integrated command contract is:

```text
pytest -q tests/clock/test_clock_profiles.py
python scripts/check_block_clock_inventory.py
pytest -q tests/inventory/test_block_clock_inventory.py
pytest -q
```

Track 8-specific future tests use the integrated `clock_controller` and
`deployed_system(clock_profile, parameter_profile)` fixtures rather than
copying or approximating repeated `NUMBER`. Every applicable state-machine
case runs ordinary Base, Robinhood `+1`, repeated-number, ordinary-jump, and
stress-jump profiles. A fixture/runtime/version mismatch is a stop, not a
reason to silently replace the integrated harness.

Clock behavior must not change custody conservation. Repeated or jumping numbers
may delay a timelock or auction but cannot permit payment for undelivered
collateral or duplicate bad debt.

## 14. Migration validation scaffold

This concise scaffold is retained for test-run orchestration and is
subordinate to the complete Phase I state machine in Sections 11.5–11.8 and
specification Section 19.6. Phase J requires Base-first or atomic convergence
before RH enablement but authorizes no migration; Track 7 still owns
namespace/tooling:

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

## 15. Diagnostics and evidence requirements

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

## 16. Proposed tiers and commands

Commands are exact future test-surface shapes; they remain non-runnable until
the proposed files and an owner-approved implementation exist:

| Tier | Purpose | Proposed command shape |
| --- | --- | --- |
| T0 | Existing evidence | `PYTHONPATH=. pytest -q tests/vaults/test_stock_token_vault_comparison.py` |
| T1 | Math/vault/credit focused | `PYTHONPATH=. pytest -q tests/vaults/test_vault_receipt_accounting.py tests/vaults/modules/test_vault_loss_properties.py tests/core/teller/test_teller_deposit_receipts.py tests/core/creditEngine/test_deficit_aware_credit.py tests/core/creditEngine/test_stock_token_repay_liveness.py` |
| T2 | Settlement, debt, rewards, and controls | `PYTHONPATH=. pytest -q tests/core/auctionHouse/test_loss_aware_auctions.py tests/core/auctionHouse/test_stock_token_resolution_controls.py tests/core/deleverage/test_loss_aware_deleverage.py tests/data/test_ledger_bad_debt_transition.py tests/core/lootbox/test_vault_loss_rewards.py tests/config/test_asset_collateral_controls.py tests/config/test_stock_token_incident_controls.py` |
| T3 | Compatibility, migration, and evidence | `PYTHONPATH=. pytest -q tests/vaults/test_corrected_share_compatibility.py tests/config/test_asset_config_schema_compatibility.py tests/config/test_core_cutover_state.py tests/data/test_ledger_state_migration.py tests/registries/test_vault_book_migration.py tests/probes/test_stock_token_artifact_parity.py tests/probes/test_fungible_settlement_usage.py tests/probes/test_stock_token_vault_evidence.py` |
| T4 | Exact AAPL fork, no broadcast | `PYTHONPATH=. pytest -q tests/probes/test_aapl_vault_behavior_fork.py` under the approved pinned Track 2 fork profile |
| T5 | Integrated dual-clock and checked inventory | `pytest -q tests/clock/test_clock_profiles.py`; `python scripts/check_block_clock_inventory.py`; `pytest -q tests/inventory/test_block_clock_inventory.py`; then the approved Track 8 cases under every applicable profile |
| T6 | Full Base/RH regression | serial `pytest -q`, followed by the Track 7 clean migration rehearsal only after its identifiers/tooling and the relevant migration are approved |

Every command records duration, source/compiler/runtime hashes, fixture/profile
versions, seed, and failure diagnostics. No dependency, tool, network secret,
test implementation, migration, or live action is authorized by this
scaffold.

## 17. Phase J authorization and decision-bound validation branches

The owner authorized Phase J on 2026-07-24:

> I authorize Phase J specification work only. Use all-external fungible
> settlement as the preferred path subject to complete integration and
> historical-usage evidence; use an isolated generic corrected-share variant
> and the A^s/U^s model as validation targets; and model the two-selector
> bad-debt transition without authorizing a Ledger migration. Preserve S3
> independently if Track 8 would delay it, require Base-first or atomic
> convergence, and treat any empty gated deployment as inactive staging
> rather than launch. Do not select a production vault or ID, authorize
> implementation or migration, or begin Phase K.

The resulting branch contract is:

| Area | Active Phase J validation target | Branches kept open or blocked | What remains unapproved |
| --- | --- | --- | --- |
| Fungible settlement | All-external after the complete Section 11.3 integration/history gate | Per-asset generic mode and `do not list` remain comparisons/fallbacks; a discovered dependency returns the choice | Behavior change, config field, ABI, defaults, migration |
| Corrected-share boundary | Isolated generic variant; existing Rebase/RipeGov semantics are controls | Blanket module change and generic positive-delta mode remain rejected/unselected; `do not list` remains safe fallback | File, wrapper, storage layout, ABI, vault, ID |
| Allocated backing | Reference `A^s/U^s/A/U` formulas and checkpoint evidence | Audited equivalent may be returned; migration import remains a separate gate | Mappings, selector names/tuples/events, import/finalizer |
| Total-loss transition | Two-selector compare-and-set model | Another atomic design or `do not list` remains possible | Both selectors, event, implementation, full Ledger migration |
| Rewards/S3 | Preserve S3 unchanged and independently releasable; test Track 8 loss weighting separately | Combined cutover only if it does not delay S3 and reopens review | Loss epoch/index/callback, economics, window policy, migrations |
| Live versions | Base-first or atomic convergence before RH enablement | Inactive unreachable staging may be rehearsed but is not convergence or launch | Base/RH migration, cutover, runtime, registry/config action |
| Production identity | None | Track 7 retains ID/manifest/tooling ownership | Production vault, VaultBook ID, listing, launch |

An inactive staging test may prove code identity, constructor/config posture,
disabled reachability, and abandonment. It may not contain users, custody,
debt, auctions, or Stock reward state; may not enable a value path; and may
not satisfy any production launch row.

## 18. Complete future-test record model

### 18.1 Record composition

Every backticked `test_...` identifier in Sections 3–11 is a named future
assertion. Its complete test record is the deterministic union of:

1. the exact case row or bullet, which owns setup-specific token behavior and
   the expected state transition/result;
2. the most-specific profile in Section 18.3, which owns the primary proposed
   file, components, prerequisite, actors/behavior domain, invariant or
   validation obligation, clock, diagnostics, tier, and reviewers;
3. any explicit file path in the case row, which overrides the profile's
   primary path for that case only; and
4. Sections 15–16, which add the common evidence schema and command/tier
   contract.

Sections 3–5 are index/coverage views. A name introduced there and not
repeated in Sections 6–11 uses profile J-P00. A repeated name uses its
most-specific detailed-section profile and is not a second test record.
Conflicting profiles, an absent profile, a missing field, or a fixture that
weakens the case result is a document/test-review failure.

### 18.2 Validation obligations beyond economic invariants

Economic tests cite I-01–I-13. Tests whose primary subject is compatibility,
evidence, or process cite one or more of these equally normative Phase J
obligations:

| ID | Validation obligation |
| --- | --- |
| J-01 authorization exactness | No unapproved storage, selector, ABI, event, default, role, migration, vault, ID, or live action appears in a passing branch. |
| J-02 source/artifact identity | Source, compiler input, constructor schema/args, creation/runtime hashes, ABI, registry address, and accounting version reconcile. |
| J-03 state/migration completeness | Every user, index, aggregate, custody bucket, debt, auction, reward, config, pause, cooldown, and pending action is reconciled exactly or migration stops. |
| J-04 fail-closed evidence | Missing, malformed, stale, unscanned, rate-limited, or inconsistent evidence is unknown/failure, never zero, safe, or complete. |
| J-05 clock/profile invariance | Ordinary, repeated, `+1`, jump, and stress profiles change only approved timing; custody/payment/liability invariants remain identical. |
| J-06 standing Stock constraints | Redemption, Stability Pool swap, unsupported integrations, and unapproved deposit/borrow/auction/reward routes remain disabled or absent. |
| J-07 inactive is not launch | Empty gated staging cannot satisfy production selection, migration, listing, enablement, behavior, or launch evidence. |
| J-08 reviewer/provenance closure | Every result names the frozen inputs, owner prerequisite, reviewer/security/accounting/economics/counsel gates, and approval state. |
| J-09 settlement-usage completeness | All current integrations and every historical Teller generation/range are pinned, decoded, gap-free, provider-reconciled, and product-dispositioned before all-external eligibility. |
| J-10 S3 and convergence sequencing | S3 remains independently releasable if Track 8 is late, and RH value paths cannot enable before Base-first or atomic convergence. |

### 18.3 Test profiles

The “actors/behavior” column supplements, rather than replaces, each case's
exact setup. “All relevant” clock means Base ordinary plus Robinhood
ordinary/`+1`/repeated/jump/stress where the path consumes `NUMBER`; otherwise
the recorded clock is `N/A`.

| Profile | Governs | Primary proposed file | Components | Prerequisite | Actors / token behavior | Invariant or obligation; clock | Diagnostics; tier; required review |
| --- | --- | --- | --- | --- | --- | --- | --- |
| J-P00 | Sections 3–5 names not repeated later | `tests/vaults/test_stock_token_vault_lifecycle.py` | all primary IDs plus exact row IDs | option 4; detailed branch prerequisite | users, buyer, issuer/admin, operator, governance; ordinary/controlled token selected by row | exact cited I-01–I-13, J-06/J-07; all relevant | Section 15 full state; T1/T2; protocol + security + row owner |
| J-P01 | Sections 6.1–6.3 | `tests/vaults/test_vault_receipt_accounting.py` | `CM-024`, `CM-025`, `CM-034`, `CM-045` | Phase D behavior; implementation approval later | depositor, recipient, Teller, vault, token admin/callback; ordinary/no-return/short/fee/negative/excess/reentrant | I-01/I-02/I-05/I-10; all relevant | `A_req/Q/C0..C3/R/V`, shares, events, full failure root; T1; protocol + vault/Teller security |
| J-P02 | Sections 6.4–6.5 | row's exact existing test path, otherwise `tests/core/teller/test_teller_deposit_receipts.py` | `CM-034`, `CM-045` plus named consumer | Phase D behavior and consumer disposition | caller-specific producer/recipient, Teller, vault, Ledger/Lootbox; short and exact receipt | I-01/I-05; all relevant | upstream payout/mint/claim plus receipt/events/root; T1/T2; consumer owner + protocol/security |
| J-P03 | Section 7.1 | `tests/config/test_asset_collateral_controls.py` | `CM-009`, `CM-011`–`CM-013`, `CM-030` | owner no-new-collateral-flag direction | governance, lite actor, borrower; solvent ordinary token | I-07/I-09, J-01/J-06; ordinary and TimeLock profiles | config/debt-term tuples, events, capacity/debt roots; T1/T2; protocol + config security |
| J-P04 | Sections 7.2–7.4 | `tests/core/creditEngine/test_deficit_aware_credit.py` | `CM-030`, `CM-009`, Ledger, vault IDs from case | Phase E behavior | multiple users/vaults, borrower, repayer, issuer/admin; ordinary/short/deficit/zero/read-failure | I-02/I-06/I-07/I-09/I-12; all relevant | custody/accounting/terms/value/capacity/health/debt/gas; T1; credit + protocol/security |
| J-P05 | Section 7.5 | `tests/probes/test_stock_token_vault_evidence.py` | `CM-009`, `CM-030`, vaults, token | Phase E evidence model | read-only observer; safe/deficit/missing-read fixtures | I-02/I-06/I-07/I-12, J-04/J-08; pinned same block | raw/decoded calls, block hash, derivation and gas/staticcalls; T3; protocol + security/operations |
| J-P06 | Sections 8.1 and 11.3 | `tests/probes/test_fungible_settlement_usage.py` | `CM-026`, `CM-034`, every Teller/AuctionHouse generation | complete integration/history plus product inventory | read-only product/integration inventory; decoded successful/reverted auction calls | I-11, J-01/J-04/J-09; every production block range | runtimes, ranges, raw calldata/tx/events/provider gaps/coverage root; T3; product + protocol/security + operations |
| J-P07 | Sections 8.2–8.3 | `tests/core/auctionHouse/test_loss_aware_auctions.py`; row-named Deleverage path overrides | `CM-026`, `CM-030`, `CM-034`, `CM-044`, Ledger, vault | Phase F policy; all-external branch still conditional | liquidated user, one/two buyers, recipient, issuer/operator, Deleverage; ordinary/short/paused/blocked/loss | I-03/I-04/I-05/I-11; all relevant | `Q/W/R/E`, custody/claims/GREEN/debt/auction/points/events/root; T2; protocol + auction/security |
| J-P08 | Sections 8.4, 8.6, 10.5–10.6 | `tests/core/auctionHouse/test_stock_token_resolution_controls.py` | `CM-026`, `CM-030`, `CM-009`, Ledger | deterministic existing-`canLiquidate` direction; selectors unapproved | borrower, repayer, caller/keeper/governance, buyer; total/partial/paused/price-failure | I-06/I-08/I-09/I-12, J-01; all relevant | eligibility scan, caller inputs, debt/auction/gate/events/root/gas; T2; accounting + protocol/security |
| J-P09 | Section 8.5 | `tests/data/test_ledger_bad_debt_transition.py` | `CM-008`, `CM-030`, `CM-026` | two-selector validation target; no migration approval | two borrowers, repayer/resolver, CreditEngine, unauthorized caller; debt/yield/auction races | I-08/I-09, J-01; same/repeated/jump around interest/touch state | user/global debt, yield, bad debt, indexes, auctions, GREEN/events/root; T2; accounting + Ledger/security |
| J-P10 | Sections 9.2–9.6 | `tests/vaults/modules/test_vault_loss_properties.py` | `CM-025`, `CM-021`, Vault interfaces | isolated generic `A^s/U^s` target; mechanism unapproved | multiple users/orderings, issuer/admin, donor; 6/18 decimal, donation, partial/total loss, restoration | I-01–I-05/I-10/I-13; all relevant | `C/A^s/U^s/A/U/S/s_u`, claims, delivery, dust, events/root; T1; vault/math security + economics/counsel-risk where allocation relevant |
| J-P11 | Section 9.7 | `tests/core/lootbox/test_vault_loss_rewards.py` | `CM-033`, `CM-025`, Ledger, S3 `CM-013` | live-claim units; loss mechanism unapproved; S3 independent | touched/untouched users, reward operator, issuer/donor; partial/total loss, restoration, global rewards on/off | I-10/I-13, J-06/J-10; ordinary/repeated/jump/interval boundaries | raw shares/live weight/global value/points/epochs/S3 config/events; T2; economics + Track 6 + protocol/security |
| J-P12 | Sections 9.8, 11.1–11.2, 11.4 | `tests/vaults/test_corrected_share_compatibility.py`; direct-Department cases use `tests/config/test_core_cutover_state.py` | `CM-021`, `CM-024`, `CM-025`, `CM-033`, interfaces and affected consumers | isolated variant and `A^s/U^s` test targets only | existing Rebase/RipeGov users plus fresh corrected fixture; positive rebase/donation/loss | I-10/I-13, J-01/J-02; all relevant | compiler layout, selectors/ABI/events/units/consumer inventory/code hashes; T3; protocol + compiler/vault/security + economics |
| J-P13 | Sections 10.1–10.4 | `tests/config/test_stock_token_incident_controls.py`; repayment cases use `tests/core/creditEngine/test_stock_token_repay_liveness.py` | T8H-01–T8H-12 and named component IDs | existing-control and repay-liveness directions | governance, lite/unapproved actors, indebted user; ordinary/paused/missing integration | I-07/I-09, J-01/J-04/J-06; immediate and TimeLock profiles | roles/getters/events/flags/debt/withdrawal/root; T2; protocol + governance/security/operations |
| J-P14 | Section 10.7 | `tests/vaults/test_corrected_share_compatibility.py` | `CM-025`, `CM-009`, `CM-011`–`CM-013` | existing Switchboard checkpoint caller; selector/storage unapproved | Switchboard, unauthorized caller, users/donor/issuer; reduce/checkpoint/restore | I-10/I-13, J-01; ordinary/repeated/jump | flags, authority, bucket/claim/reward evidence and root; T2/T3; protocol + vault/security + counsel-risk |
| J-P15 | Sections 10.8–10.9 | `tests/probes/test_stock_token_vault_evidence.py` | all accounting/control readers, `CM-021`, `CM-008`, `CM-009` | read-only evidence only | observer; missing registry/archive/rate-limit/revert and same-block multi-log cases | I-02/I-06/I-12/I-13, J-04/J-05/J-08; pinned/repeated/jump | raw calls, block/log identity, enumerations, unknown/failure class; T3; security/operations + protocol |
| J-P16 | Section 11.5 | `tests/data/test_ledger_state_migration.py` | `CM-008` and every Ledger reader/writer | only if two-selector interface and full migration later approved | migration authority/reviewer, users across every Ledger domain; populated source and fresh target | I-08/I-09, J-01/J-03; all relevant | complete source/target roots, sums/indexes, pause/constructor, cutover event; T3/T6; accounting + Ledger/security/operations |
| J-P17 | Sections 11.6 and 14 | `tests/registries/test_vault_book_migration.py` | `CM-021`, vaults, Ledger, Track 7 tooling | migration/interface/vault/ID approvals all later | users, governance, migration actor, issuer/operator; live funds/debt/auctions/dust/failures | I-02–I-05/I-08–I-10/I-13, J-03/J-04/J-07; all relevant | old/new roots, custody, buckets, debt/rewards/auctions/registry/pending actions; T3/T6; protocol + security/operations + accounting/counsel-risk |
| J-P18 | Sections 11.7–11.8 | `tests/probes/test_stock_token_artifact_parity.py`; local-state cases use `tests/config/test_core_cutover_state.py` | all changed shared components, manifests/registries | Base-first/atomic posture; no live action | read-only/build observer, governance cutover model; old/new/inactive/mixed artifacts | J-01–J-05/J-07/J-08/J-10; both chain profiles | source/compiler/creation/runtime/ABI/config/state roots, expiry/abort/rollback; T3/T5/T6; protocol + security/operations + compiler/deployment |
| J-P19 | Section 12 | `tests/probes/test_aapl_vault_behavior_fork.py` | Track 2 AAPL plus selected shared components | implementation, exact-token and counsel/live-probe gates | fork users, buyer, issuer/admin/operator; exact proxy at pinned block and behavior switch | I-01–I-13, J-02/J-04/J-06/J-07; RH profiles | proxy/beacon/implementation hashes, custody/buckets/debt/rewards/events/root; T4; Track 2 + protocol/security + counsel |
| J-P20 | Section 13 | integrated `tests/clock/test_clock_profiles.py` and `tests/inventory/test_block_clock_inventory.py`, plus the detailed case's primary path | `CM-059` and every referenced BN/CAD/TS/component | integrated S1/S2 plus later implementation | actors/token from detailed case; same source under Base/RH parameter profiles | detailed I/J obligation plus J-05; every applicable profile | trace/profile/seed/source/artifact/inventory delta; T5 then T6; Track 6 + test-infra + component reviewer |

### 18.4 Required-layer and scenario closure

| Task-contract layer | Normative plan coverage |
| --- | --- |
| Math/property | Sections 7.4, 8.5, 9.2–9.5; profiles J-P04/J-P09/J-P10 |
| Vault unit | Sections 6, 9; J-P01/J-P02/J-P10/J-P12 |
| CreditEngine | Sections 7, 8.4–8.6; J-P04/J-P08/J-P09 |
| AuctionHouse | Sections 8.1–8.6; J-P06–J-P09 |
| Teller/Deleverage | Sections 6 and 8.3; J-P01/J-P02/J-P07 |
| Rewards/monitoring | Sections 7.5, 9.7–9.8, 10.8; J-P05/J-P11/J-P12/J-P15 |
| Governance/config | Sections 7.1, 10; J-P03/J-P13–J-P15 |
| Migration | Sections 11.4–11.8 and 14; J-P12/J-P16–J-P18 |
| Exact-token fork | Section 12; J-P19 |
| Dual-clock/cross-chain | Section 13; J-P20, composed with every detailed profile |

| Required scenario family | Named coverage location |
| --- | --- |
| 6/18 decimals, ordinary lifecycle, one base unit, minimum deposit | Sections 4, 6.1, 6.3, 9.2–9.3 |
| Donation before/between deposits, short receipt, fee on transfer | Sections 4, 6.1, 9.4 |
| Partial/total issuer loss, post-zero donation/restoration/new deposit | Sections 4, 7.2–7.4, 9.4 |
| Two users and both withdrawal orders; two buyers and both orders | Sections 5.3, 8.2, 9.2, 9.5 |
| Active internal/external auction before loss; liquidation after loss | Sections 8.1–8.4 |
| Pause and sender/recipient/operator blocklists | Sections 6.1, 8.2, 10.3–10.4, 12 |
| Implementation/proxy behavior switch | Sections 4, 10.8, 11.1–11.2, 12 |
| Mixed collateral and existing debt at deficit/zero | Sections 7.2–7.4, 8.4 |
| Repayment before transition and exactly-once bad debt | Sections 7.3, 8.5–8.6 |
| Failed settlement leaves every relevant state unchanged | Sections 8.2, 8.5 |
| Migration with live users/funds/debt/auctions and partial failure | Sections 11.5–11.8, 14 |
| Unsupported Stock Token features remain disabled | Sections 5.4, 8.3, 10.2, 12 |
| Historical all-external compatibility | Sections 8.1 and 11.3 |
| S3 independence, loss-aware rewards, Base/RH convergence | Sections 9.7, 11.2, 11.7, 13 |
| Empty gated staging is not launch | Sections 11.4, 11.7, 12, 17 |

### 18.5 Phase J document and future-result acceptance

The Phase J authoring audit found 441 backticked future-test mentions, 436
unique names, and zero names outside the profiled Sections 3–11. Four repeated
mentions are invariant/state/architecture indexes pointing to one detailed
record. The fifth is the deliberate same-profile Section 11.3 repetition of
the internal-settlement product-dependency assertion in both the
branch-comparison table and the named-evidence summary. None is a duplicate
execution requirement.

The Phase J document is acceptable only if:

1. every named assertion resolves to exactly one J-P profile;
2. every case has a setup/result plus all Section 18.1 inherited fields;
3. every I-01–I-13 invariant, J-01–J-10 obligation, formal state, required
   layer, and required scenario has a coverage location;
4. the all-external branch fails on any integration/history gap and requires
   product plus protocol/security disposition;
5. the isolated variant, `A^s/U^s`, and two-selector model remain test targets,
   never production selections;
6. zero staker/voter allocation is not accepted as Stock reward disablement;
7. Track 8 cannot delay required S3 safety, and any later Track 8 Lootbox
   cutover has a separate reviewed migration/window/rollback record;
8. no RH value path enables before Base-first or atomic convergence;
9. empty gated staging cannot satisfy launch or production-vault evidence;
10. the full Ledger migration stays blocked and inseparable from any future
    two-selector activation;
11. exact-token, S1/S2, Base regression, migration, artifact, and diagnostics
    fail closed; and
12. document-integrity, scope, reviewer, and owner gates pass.

These conditions define future evidence. Phase J creates no tests and does not
claim that any future command passes.

## 19. Phase K implementation and release validation handoff

### 19.1 Authorization and evidence boundary

The exact owner authorization is quoted in specification Section 12.1. Phase
K does not create or execute any test. It maps the complete Phase J profiles
to the review units and economically atomic release groups in specification
Section 21.

At Phase K entry:

- the Track 8 branch and backup were synchronized at `b18b426`;
- local `rh` was at committed Track 6 S5 planning brief `27765d2`, one commit
  ahead of `origin/rh` at `3e6e6f2`;
- the merge base remained `be6a759`;
- the S5 brief was read completely and requires a separate exhaustive,
  independently audited gate for any Ledger replacement/migration;
- the only post-baseline production/artifact delta remained the previously
  reconciled S3 Lootbox source/ABI; and
- the integration worktree's external uncommitted documentation changes,
  including `rh-summary.md`, S4/S5 and the untracked reassessment document,
  were not read as committed authority or changed by Track 8. Specification
  Section 3.15 records the exact handoff paths and distinguishes the committed
  S5 hash from its later uncommitted working-tree edit.

The future evidence source of truth remains the case rows in Sections 3–14
plus profiles J-P00–J-P20 and obligations J-01–J-10. Phase K does not add
unnormalized test cases. The 441 mentions / 436 unique assertions remain the
historical Phase J authoring audit of Sections 3–11; Phase K's file and profile
cross-references do not create additional assertion records.

### 19.2 Review-unit validation matrix

Every unit is independently reviewable but not independently activatable
unless specification Section 21 explicitly says so. “Base regression” means
the current live/stateful behavior relevant to the unit plus the ordinary
Base parameter profile, not merely a fresh local fixture.

| Unit | Governing Phase J profiles / tiers | Required unit evidence | Integrated S1/S2 and Base gate | Unit exit reviewers |
| --- | --- | --- | --- | --- |
| K-00 evidence/operations | J-P05, J-P06, J-P15; T0/T3 | Pinned inputs, gap-free runtime/range/calldata/integration coverage, raw/decoded roots, unknown/failure classification, sanitized provenance | Record integrated harness/inventory versions; same-block Base custody/accounting/config refresh; no source delta | Product + operations + protocol/security |
| K-01 Teller receipt | J-P01; T1/T5/T6 | `Q/C0..C3/R/V`, mutex entry/exit, callback and housekeeping liveness, event/return compatibility, state-root equality on revert | All clock profiles despite clock-independent custody math; full existing Teller/vault Base suites | Teller/vault security + protocol |
| K-02 receipt consumers | J-P02 and J-P07 where Deleverage composes; T1/T2/T5/T6 | Every producer captures measured/exact return as specified; no requested-amount accounting; combined runtime/ABI/state evidence | Integrated S3/S4 fixtures and all affected component suites; Base local/pause/constructor/cooldown/pending-action state | Each consumer owner + protocol/security |
| K-03 existing controls | J-P03, J-P13; T1/T2/T5/T6 | Negative source/storage/tuple/ABI diff; exact disable/re-enable authority and events/getters; no hidden flag | TimeLock/repeated/jump profiles and full Base configuration round trip | Config/governance security + protocol |
| K-04 deficit/debt health | J-P04, J-P08; T1/T2/T5/T6 | Backing read, capacity/resolution split, mixed collateral, zero/short/read failure, non-raising repay, preview/state and gas/staticcall evidence | Every applicable clock profile; Base existing users/debt/config and oracle-unavailability regression | Credit/risk + protocol/security |
| K-05 settlement/delivery | J-P06, J-P07; T2/T3/T5/T6 | Complete all-external eligibility evidence or explicit alternative; `Q/W/R/E`, two-buyer ordering, payment/debt/points atomicity, active-auction cutover | Auction clocks under Base and RH profiles; current Base product/auction regression and historical call coverage | Product + auction/protocol security |
| K-06 total-loss accounting | J-P08, J-P09; T2/T5/T6 | Deterministic eligibility/caller, debt/yield/borrower/auction/bad-debt conservation, CAS races, exactly-once event, repay-first ordering | Interest/touch clocks and full Base existing-debt/auction regressions | Accounting + CreditEngine/Ledger security |
| K-07 Ledger migration | J-P16; T3/T6 plus all Ledger domain suites | Every storage domain/key and aggregate, pause/constructor/lock/lastTouch state, source/target roots, cutover and reverse-plan proof | S1/S2 and S5 state/guard evidence; populated Base rehearsal, never empty-only | Separate external accounting/security audit + operations/Track 7 |
| K-08 corrected share | J-P10, J-P12, J-P14; T1/T2/T3/T5/T6 | `C/A^s/U^s/A/U/S/s_u`, rounding/dust, partial/total loss, donation/restoration/freeze, authority, layout/ABI/import evidence | All clocks; existing Base Rebase positive-delta, RipeGov, Simple, ID-4 dust and common-consumer regressions | Independent vault/math security + economics/counsel-risk |
| K-09 reward/monitoring | J-P11, J-P12; T2/T3/T5/T6 | Live-claim weight, `U` exclusion, untouched-user loss boundary, global conservation, getters/events/units, S3 sequence/window | Reward interval/repeated/jump profiles; integrated S3 constructor/floor/getter/ABI and current Base reward-state regression | Economics + Track 6 + protocol/security |
| K-10 defaults/config | J-P03, J-P13, J-P18; T2/T3/T5/T6 | Preferred negative schema proof, explicit per-chain values/actions, standing disables, roles/events/getters and no omitted-argument enable | Full generated Base/local/RH profiles, TimeLock clocks and checked inventory; current Base config snapshot | Governance/config security + operations/S6/Track 7 |
| K-11 migration/registry | J-P17, J-P18; T3/T5/T6 | Exact approved IDs/paths, dry plan, artifact/constructor/ABI hashes, state/custody/debt/auction/reward roots, partial failure/retirement/post-state | S1/S2 plus Base and RH profiles; Base migration runner/history regression; clean Track 7 rehearsal | Independent migration/security/operations + Track 7 |
| K-12 exact-token/full release | J-P00, J-P19, J-P20 composed with all profiles; T0–T6 | Exact AAPL identity/lifecycle/behavior switch, every invariant/obligation, full diagnostics, audit/evidence hashes, no relaxed result | Every clock/profile, checked inventory, serial full suite, complete Base regression and approved RH rehearsal | Independent release reviewer + Track 2/6/7 and each failed-row owner |

A unit exit proves only that the reviewed branch satisfies that unit's
contract. It does not approve merging, deployment, migration, configuration,
or activation. Files touched by more than one unit require a combined-artifact
review after the individually owned hunks compose.

### 19.3 Common unit evidence bundle

Each future unit record must contain:

```text
unitId
ownerApprovalAndConditions
integrationCommitAndMergeBase
allowedFilesAndActualDiff
componentIds
sourceCompilerCreationRuntimeHashes
storageAndAbiDeltaOrNegativeProof
fixtureClockInventoryVersions
targetedProfilesAndTierResults
baseRegressionStateAndResults
downstreamConsumerInventory
auditScopeReviewersAndFindings
migrationAndRollbackBoundary
stopConditionsAndDisposition
```

Unknown, skipped, stale, rate-limited, unenumerated, or conflicting evidence
fails the unit. A documentation assertion or fresh empty fixture cannot stand
in for live-state, historical-usage, exact-token, or migration proof.

### 19.4 Release 0 validation

Release 0 passes only when:

1. K-00's exact source/runtime/range/integration inventory is complete;
2. read-only Base evidence reconciles custody, accounting, controls, debt, and
   registry identities at one pinned block;
3. the operations and migration runbook templates name all authorities,
   clocks, stop/abort/rollback boundaries, reviewers, and evidence fields;
4. T0 and the integrated S1/S2 command interfaces reproduce on the frozen
   baseline; and
5. every missing production decision is visibly open.

Release 0 contains no production source, interface, storage, ABI, default,
migration, manifest, deployment, configuration, or Stock enablement. A future
read-only evidence acquisition and any proposed test/probe creation require
K-CP1. An empty deployed artifact cannot satisfy Release 0.

### 19.5 Release 1 atomic-containment validation

Release 1 has a single economic activation gate over K-01–K-06, K-10–K-12,
and K-07 whenever the selected debt transition changes Ledger. Individually
reviewed PRs are preparation only.

Before activation, validation must prove:

1. K-00 closed and the owner selected the settlement and atomic debt
   mechanisms;
2. every affected deposit producer/consumer, CreditEngine, AuctionHouse,
   Deleverage, and any selected Ledger runtime is built from one reconciled
   integration baseline;
3. all stateful replacements reproduce exact live constructor/immutable,
   pause, local config, cooldown, pending action, points, debt, auction, and
   custody/state roots;
4. the selected Ledger path passed its separate K-CP3 and complete K-07
   audit/migration rehearsal;
5. T0–T6 applicable tiers, S1/S2, full serial suite, complete Base regression,
   artifacts, and audits pass;
6. all affected value paths stay contained and repayment stays live through
   preparation/migration;
7. one reviewed activation boundary exposes only the complete compatible
   group; and
8. post-state evidence shows no false health, zero-backed charge, duplicate
   debt/bad debt, mixed caller, or old/new double eligibility.

The release fails if any partial deployment can combine fail-closed zero
collateral with old debt progress, new Teller returns with old consumers,
measured delivery with larger payment/debt, or a new resolver with old or
partially migrated Ledger state.

All-external validation is ineligible on a gap or unresolved historical
dependency. The two-selector validation target is ineligible without its
separate full Ledger migration. In either case the result is another
owner-approved design or no Release 1, never partial activation.

Release 1 is Base shared hardening, not Stock Token listing or vault
selection. Robinhood Stock value paths remain disabled. If Base cannot
harden first, only an expressly approved atomic convergence plan can proceed.

### 19.6 Release 2 corrected-path validation

Release 2 has a single economic activation gate over approved K-08/K-09,
K-10/K-11, and all K-12 evidence, after Release 1 acceptance or within a
separately approved atomic convergence.

Validation must prove:

1. exact generic corrected-share paths, storage, interfaces, ABI, events, and
   positive-delta boundary are owner/security approved;
2. counsel/risk and economics approve loss-before-quarantine ordering,
   donation/recovery disposition, reward units, and the untouched-user loss
   boundary;
3. S3 is not delayed; a later Track 8 Lootbox cutover has its own reviewed
   state/window/rollback record, or a combined artifact has explicitly
   reopened and passed S3 review;
4. the production vault and Track 7 ID are approved, with no invented or
   reused migration identifier;
5. migration/import/finalization, literal custody, users/shares/buckets,
   Ledger participation, debt, auctions, and rewards reconcile exactly;
6. the full corrected-vault property suite, Base regressions, S1/S2, exact
   AAPL fork, artifact parity, clean migrations, testnet/rehearsal, and audit
   gates pass; and
7. Base is already safe or converges atomically before any Robinhood deposit,
   borrow, auction, reward, or other Stock value path.

An empty gated artifact proves only inactive staging. It fails production
vault selection, state migration, Base convergence, exact-token lifecycle,
listing, reward, launch, and enablement until those gates pass. It must remain
unreachable, state-empty, disabled, time-bounded, and abandonable.

### 19.7 Release evidence and rollback assertions

Each future release candidate supplies one pre-state and one post-state bundle
per affected chain with the Section 19.8 schema from the specification plus:

```text
releaseIdAndAtomicGroup
unitRecordHashes
ownerCheckpointRecords
auditReportsAndFindingDisposition
activationPlanAndExactTransactionDigest
containedValuePathMatrix
repaymentLivenessEvidence
rollbackOrForwardRecoveryBoundary
smokeSoakWindowAndResults
remainingDisabledFeatures
```

Activation atomicity is economic, not a false claim that every migration fits
in one blockchain transaction. A multi-transaction migration is acceptable
only if each transaction is internally atomic and resumable while old/new
systems remain contained and exactly one claim set can contribute capacity,
settlement, or rewards. After any new borrow, settlement, bad-debt, reward, or
custody write, an address flip is not rollback.

### 19.8 Final owner/reviewer gates and stop

The future workflow must stop at each specification checkpoint K-CP0 through
K-CP11. In particular:

- K-CP0 accepts the documents only;
- K-CP1 separately authorizes Release 0 evidence/probe/test work;
- K-CP2 selects Release 1 mechanisms;
- K-CP3 separately gates any Ledger runtime/state migration;
- K-CP4 authorizes an exact implementation file set;
- K-CP5 separately gates merge/integration readiness;
- K-CP6 separately authorizes exact Base migration/deployment transactions;
- K-CP7 accepts Base containment evidence;
- K-CP8 selects the corrected mechanism, reward behavior, production vault,
  and VaultBook ID;
- K-CP9 authorizes exact Release 2 implementation/audit work;
- K-CP10 authorizes only named migration/testnet/rehearsal actions; and
- K-CP11 separately authorizes exact Robinhood deployment/config/enable
  transactions.

Phases A–K are now specification-complete and ready for final owner and
independent review. Still unresolved are the complete settlement-usage
evidence, final settlement enforcement, exact corrected-share
files/storage/interfaces, counsel/risk property treatment, reward loss
boundary and S3 window/sequence, bad-debt selectors/interest/caller semantics,
the separate full Ledger migration and S5 posture, Track 7 migration paths,
production vault/ID, Base cutover, exact-token evidence, audits, and every
live action.

No implementation, interface, storage, test, dedicated pause, ABI, default,
migration, manifest, production vault/ID, RPC acquisition, deployment,
configuration, signer use, transaction, enablement, or launch gate is passed
by this specification. Section 20 supersedes the old product-default sentence:
Stock Tokens are mandatory initial-launch scope, but every value path remains
disabled until the complete minimum group passes.

## 20. Minimum-change initial-launch validation

### 20.1 Proposed candidate and negative-scope proof

The candidate under review is:

```text
contracts/core/Teller.vy
proposed contracts/vaults/GuardedErc20.vy
contracts/core/CreditEngine.vy
```

plus tests and later Track 6/7-owned configuration, artifact, migration,
manifest, and release evidence. This planning branch changes none of those
files.

This three-source candidate is the smallest proved Robinhood launch surface.
Teller and CreditEngine are shared source and require full caller/consumer
regression. The M0 evidence now proves exact-transfer compatibility for every
already-existing external token proposed in the Robinhood route graph, freezes
the route/file disposition for not-yet-built Ripe artifacts, and classifies all
27 Base ID-3 assets for forward-source/later-cutover compatibility. Existing
Base deployments remain unchanged under the Robinhood-first proposal only if
the proposed file/deployment graph proves no state/economic propagation path
between chains; actual new Robinhood addresses/runtime hashes are later
proof. AuctionHouse and Deleverage are negative-diff requirements: their
current ordering must be proved sufficient with the selected vault, not
edited.

The implementation diff must prove the absence of:

- persistent storage changes in Teller, CreditEngine, AuctionHouse,
  MissionControl, Switchboards, or Ledger;
- a change to canonical `interfaces/*.vyi`;
- an existing selector or event-signature change (the fresh vault has one new
  generated ABI/artifact using the existing canonical Vault shapes);
- a new AssetConfig, DebtTerms, or auction-mode field;
- any `AuctionHouse.vy` or `Deleverage.vy` production change;
- a CreditEngine raw custody/vault-total helper, `AssetConfig` getter, or
  `_repayDebt` behavior change;
- a `Deleverage.vy` source change for the Endaoment route prohibition;
- any Ledger source/artifact/migration change;
- share, allocation, checkpoint, bad-debt-transition, reward-loss, or
  recapitalization logic;
- token-, issuer-, chain-, or production-VaultBook-ID branching; and
- a Robinhood-only source fork or `chain.id` branch.

The fresh launch vault may use only the existing `VaultData` persistent layout.
Teller's deposit mutex must compile as transient state. AuctionHouse has no new
mutex or state.

The vault-only deposit candidate must first fail the algebraic negative proof:
with `C0=N+S` and `R=Q-S`, its post-only equality or solvency check sees
`C1=N+Q` and cannot detect the short receipt. Acceptance therefore requires
Teller's independently observed `R==Q`; removing Teller is a test failure, not
an optimization. Once Teller proves that call-local fact, the vault must use
`C>=N`, not `C==N`: a surplus remains uncredited and cannot support extra
capacity, while a one-unit donation cannot grief-freeze nominal operations.

### 20.2 Property-to-test map

| Property | Required named future assertions |
| --- | --- |
| ML-01 exact deposits | `test_min_teller_requires_r_equal_q_on_every_route`; `test_min_vault_only_post_check_fails_donation_short_counterexample`; `test_min_short_fee_zero_negative_excess_receipt_reverts_state_root`; `test_min_failed_empty_short_long_balance_read_reverts`; `test_min_deficit_excess_cancellation_reverts`; `test_min_vault_requires_c1_gte_n_plus_q`; `test_min_preexisting_surplus_remains_uncredited`; `test_min_vault_return_must_equal_q`; `test_min_measurement_mutex_blocks_nested_cross_asset_deposit`; `test_min_legitimate_first_trusted_callback_still_succeeds`; `test_min_post_window_housekeeping_still_succeeds` |
| ML-02 no borrowing from missing custody | `test_min_one_unit_nominal_deficit_zeros_every_user_capacity`; `test_min_one_unit_surplus_preserves_only_nominal_user_capacity`; `test_min_surplus_never_creates_user_claim_or_capacity`; `test_min_total_loss_get_max_borrow_is_zero`; `test_min_nonzero_nominal_unsafe_getter_returns_asset_zero`; `test_min_true_zero_nominal_getter_returns_empty_zero`; `test_min_safe_mixed_collateral_keeps_exact_capacity`; `test_min_failed_empty_short_long_vault_balance_read_is_not_optimistic`; `test_min_preview_and_borrow_share_vault_classification` |
| ML-03 honest health/liquidation | `test_min_asset_zero_position_retains_resolution_terms`; `test_min_shares_total_loss_asset_zero_retains_terms`; `test_min_stab_vault_empty_zero_remains_excluded`; `test_min_basic_true_zero_is_deregistered_or_empty`; `test_min_nonzero_legacy_vault_paths_unchanged`; `test_min_deficit_debt_is_not_healthy`; `test_min_zero_collateral_nonzero_threshold_is_liquidatable`; `test_min_other_safe_collateral_can_keep_account_healthy`; `test_min_can_deposit_false_alone_does_not_erase_solvent_value` |
| ML-04 proved settlement before payment | `test_min_external_payment_uses_e_min_q_w_r`; `test_min_launch_vault_outflow_equals_report_equals_recipient_delta`; `test_min_guarded_internal_partial_fill_precedes_green_and_debt`; `test_min_internal_payment_and_debt_use_only_w`; `test_min_sender_or_recipient_fee_reverts_all_state`; `test_min_reflection_or_excess_reverts_all_state`; `test_min_failed_malformed_delivery_reads_revert_all_state`; `test_min_loss_after_auction_creation_cannot_charge_green`; `test_min_batch_each_row_uses_its_proved_e_or_w`; `test_min_two_buyers_cannot_reuse_custody`; `test_min_auctionhouse_source_and_abi_unchanged`; `test_min_deleverage_source_and_abi_unchanged`; `test_min_deleverage_repay_is_bounded_by_vault_return`; `test_min_swap_collateral_binds_exact_withdrawal_and_deposit` |
| ML-05 no unsafe nominal-only Stock settlement — owner-approved partial-fill invariant | `test_min_internal_full_fill_succeeds`; `test_min_internal_partial_fill_when_seller_balance_below_q`; `test_min_internal_partial_fill_reports_seller_depletion`; `test_min_internal_over_request_never_moves_more_than_seller_or_q`; `test_min_internal_batch_accounts_each_partial_fill_independently`; `test_min_internal_seller_decrease_equals_w`; `test_min_internal_buyer_increase_equals_w`; `test_min_internal_zero_w_reverts_all_state`; `test_min_internal_overfill_reverts_all_state`; `test_min_internal_unknown_pre_read_reverts_all_state`; `test_min_internal_unknown_post_read_reverts_all_state`; `test_min_internal_pre_deficit_reverts_all_state`; `test_min_internal_post_deficit_reverts_all_state`; `test_min_internal_user_delta_mismatch_reverts_all_state`; `test_min_internal_nominal_total_change_reverts_all_state`; `test_min_internal_custody_change_reverts_all_state`; `test_min_internal_failure_is_atomic_across_green_debt_auction_points_and_events`; `test_min_internal_does_not_exercise_token_transfer_controls`; `test_min_external_remains_frontend_default`; `test_min_true_is_not_silently_reinterpreted`; `test_min_legacy_internal_mode_unchanged` |
| ML-06 repayment liveness | `test_min_repay_keeps_current_raising_mode`; `test_min_repay_with_failed_stock_backing_observation_reduces_debt`; `test_min_unsafe_stock_does_not_call_price_desk`; `test_min_safe_co_collateral_health_survives_failed_stock_read`; `test_min_safe_co_collateral_liquidation_survives_failed_stock_read`; `test_min_safe_co_collateral_auction_purchase_survives_failed_stock_read`; `test_min_repay_during_deficit_does_not_allocate_loss`; `test_min_unrelated_nonzero_missing_price_defect_remains_pinned` |
| ML-07 issuer-loss fail closed | `test_min_deficit_blocks_new_deposit`; `test_min_deficit_blocks_withdrawal_for_every_user`; `test_min_deficit_blocks_internal_transfer`; `test_min_surplus_does_not_block_nominal_deposit_withdraw_or_guarded_internal_delivery`; `test_min_partial_and_total_loss_freeze_equally`; `test_min_reduce_then_restore_gte_nominal_preserves_claims`; `test_min_restored_solvency_remains_config_disabled_until_review`; `test_min_launch_vault_rejects_endaoment_funds_recipient`; `test_min_launch_vault_rejects_endaoment_psm_recipient`; `test_min_volatile_override_propagates_registry_recipient_end_to_end`; `test_min_volatile_override_cannot_bypass_vault_recipient_guard`; `test_min_normal_external_recipient_remains_live` |

Every failure assertion compares all relevant custody, nominal accounting,
user debt, aggregate debt, GREEN balances, auction state, Ledger
participation, points, and emitted logs. A revert-only assertion is
insufficient.

### 20.3 Vault state matrix

For at least two users and 6- and 18-decimal assets, exercise:

| Pre-state | Deposit | Withdrawal | Internal | Capacity/value | External auction |
| --- | --- | --- | --- | --- | --- |
| `C=N=0` | Exact `R==Q` and `C1>=N+Q` succeeds | No claim | No positive claim to move | Based only on credited `Q` and LTV | No auction |
| donation `C>N=0` | Exact `R==Q` succeeds; donation remains surplus | No claim before deposit | No positive claim to move | Based only on nominal credited claim, never the donation | No auction before a nominal claim |
| solvent `C=N>0` | Succeeds with `N'=N+R` | Exact recipient delta required | Owner-approved guarded full or partial move succeeds with `0<W<=Q`, exact seller/buyer deltas, and `C1==C0` | Ordinary configured amount | External uses `E=min(Q,W,R)`; internal uses only `W` |
| solvent surplus `C>N>0` | Succeeds; `C-N` remains unallocated | Exact nominal withdrawal succeeds; surplus remains | Guarded move succeeds without consuming surplus | Ordinary nominal user amount only | External or guarded internal; surplus is not sold |
| one-unit deficit `0<C<N` | Reverts | Reverts for every user | Reverts | Zero for all affected users; terms retained | Reverts before payment |
| total loss `C=0<N` | Reverts | Reverts | Reverts | Zero; existing debt unhealthy/liquidatable | Reverts before payment |
| restored `C>=N` with flags disabled | Source backing is safe but admission remains disabled | Remains disabled until governance action | Reverts | Solvent nominal value exists; no deposit admission, and general borrow control may remain disabled | Remains disabled by `canBuyInAuction=false` |

Property runs randomize deposit/withdraw/loss/donation/restore/borrow/repay/
auction ordering and prove:

```text
successful deposit => N' - N == C' - C == R == Q
C < N or unknown backing => no deposit, withdrawal, capacity, or value
successful exact deposit or withdrawal => (C-N)' == C-N
C >= N => no operation allocates surplus C-N or counts it as user capacity
successful launch-vault withdrawal => V0 - V1 == B1 - B0 == W
sum successful external auction delivery <= custody actually delivered
failed operation => complete relevant state unchanged
```

### 20.4 Credit and repayment test details

The future candidate must retain an unsafe nonzero nominal position in the
loop even when the vault reports zero usable amount. Required diagnostics per
position:

```text
asset
nominalUserAmount M
vaultReturnedAmount
backingKnown
custody C
nominalTotal N
solventBacking
ltv
priceReadAttempted
collateralContribution
capacityContribution
resolutionWeight
```

Tests must show:

1. backing classification happens inside the selected vault before the
   existing getter returns to CreditEngine;
2. a known deficit or unknown observation returns `(asset,0)` and never needs
   a price to contribute zero, while a surplus returns the unchanged nominal
   user amount and never exposes the surplus as a claim;
3. reverting, empty, short, or long token `balanceOf` responses classify only
   that Stock position as unknown/unsafe and contribute zero;
4. unknown Stock backing cannot revert repayment, mixed-account health, or
   eligibility and actual auction purchase of a separate safe collateral
   position;
5. a state-changing borrow against a safe but unpriced position fails closed;
6. a non-raising preview returns no optimistic capacity;
7. current raising repayment mode succeeds when the only unsafe observation is
   the Stock `(asset,0)` position because PriceDesk is skipped for zero;
8. `canDeposit=false` alone does not erase exact solvent value; existing
   general `canBorrow=false` is the pre-loss broad emergency stop; and
9. maximum configured user vault/asset counts stay within an accepted gas
   budget without CreditEngine raw backing calls or persistent/stale cache;
   and
10. every existing `(asset,0)`/`(empty,0)` producer has the disposition in
    specification Section 23.3.C, including named SharesVault total-loss,
    StabVault empty-zero, BasicVault true-zero, and unchanged nonzero legacy
    regressions, with no new terms for a true empty position.

The pinned current-behavior repayment test that raises through
`_repayDebt -> _getUserBorrowTerms(..., True) -> PriceDesk` remains as evidence
of a broader defect for a **nonzero** missing-price position. The minimum Stock
candidate does not change `_repayDebt`; tests must prove both the narrower
success and the unchanged broader limitation honestly. The vault helper must
use a low-level static call whose failure does not escape the getter and whose
output buffer detects any response length other than exactly 32 bytes.

### 20.5 Settlement comparison evidence

The owner-selected launch direction is vault-enforced guarded settlement with
external delivery as the frontend default. Validation must retain the
comparison:

| Branch | Required evidence | Acceptance |
| --- | --- | --- |
| Global all-external AuctionHouse | Complete code/integration caller inventory plus decoded historical Base call data for both single and batch selectors, coverage gaps, and product/security disposition | Deferred defense-in-depth; eligible only if no live dependency or every dependency has an approved migration |
| Stored per-asset mode | Full config layout/getter/setter/event/default/migration/authority/fail-safe proof | Not eligible for minimum launch unless the owner rejects vault capability and explicitly reopens storage/interface scope |
| Guarded-settlement launch vault with unchanged AuctionHouse | Owner-approved internal selector invariant proves `0<W<=Q`, exact seller decrease/buyer increase, known `C>=N` before/after, unchanged aggregate nominal, and unchanged custody; external selector preserves `E=min(Q,W,R)` and exact vault outflow/return/recipient increase/post-withdraw solvency; current payment/debt ordering is source-pinned; AuctionHouse/Deleverage source and ABI are byte-identical | **Owner-selected direction; implementation evidence is post-M0** |

Historical call evidence remains useful for later global hardening and Base
review, but it is not a logical prerequisite for the isolated
vault-capability choice because that choice changes no other vault or
AuctionHouse behavior.

### 20.6 Configuration and reward gates

Before any Stock value path enables, one same-block bundle must prove:

```text
canDeposit
canWithdraw
canBuyInAuction
canRedeemCollateral == false
shouldSwapInStabPools == false
all unsupported routing fields disabled
DebtTerms including finite ltv
finite per-user/global deposit limits
canRepay == true
reward points/emission posture
launch vault address, ID, code hash, and registered asset
```

The reward assertion fails if only per-asset
`stakersPointsAlloc/voterPointsAlloc` are zero while global generic-depositor
or borrower rewards can still accrue. Activation must prove
`arePointsEnabled=false` and `ripePerBlock=0`. A later reward activation,
targeted within seven days, may include AAPL depositors and borrowers only
after:

1. all reward assertions and live monitoring pass;
2. the global kill-switch runbook is rehearsed;
3. the accepted brief nominal/global accrual window after an incident is
   recorded; and
4. no test assumes a Stock-specific accounting contract change.

M0 freezes the activation-day disable policy and its operational runbook; the
actual deployed disabled-state proof is a later release gate. The
within-seven-day reward target is a later operational gate and is not
permission to distribute rewards without its validation record.

The M0 runbook check is source-exact:

- `SwitchboardAlpha.setRewardsPointsEnabled(false)` must be callable
  immediately by governance or a configured lite actor and must read back
  `MissionControl.getRewardsConfig().arePointsEnabled == false`;
- `SwitchboardAlpha.setRipePerBlock(0)` is governance-only and timelocked, so
  launch must start at zero and a later incident must record initiation,
  action ID, confirmation block, first-eligible execution, event, and zero
  readback;
- the monitoring test triggers on AAPL identity/control change, unknown
  backing, `C<N`, or delivery failure, preserves `canRepay=true`, and
  quantifies any exposure during the emission timelock; and
- no test may describe the two controls as simultaneous fast stops.

The route proof must distinguish ordinary configuration from privileged
override behavior. `shouldTransferToEndaoment=false` keeps Stock out of normal
configured Deleverage processing, while the launch vault must independently
reject a nonzero recipient equal to either current RipeHq Endaoment Funds or
Endaoment PSM address. Tests must exercise the ordinary route, the
governance-only `SwitchboardDelta.deleverageWithVolAssets` entry, and a direct
authorized underlying Deleverage caller. Every path must fail at the launch
vault without delivery, debt reduction, or partial state. Normal user and
AuctionHouse recipients must remain live. The proof also records the live
registry IDs/addresses and shows an authorized endpoint update changes the
rejected recipient without new storage or a Deleverage/config change.

The privileged-path test must execute the real composed call chain, capture
the recipient argument at both `AuctionHouse.withdrawTokensFromVault` and the
launch vault, and prove it equals the same live RipeHq Endaoment Funds or PSM
address selected by Deleverage. A direct call to the vault, a mocked
intermediary that substitutes the expected address, or a revert without
argument evidence is not acceptance.

The approved launch graph adds the following M0 document/evidence checks and
later implementation/deployment assertions. A launch-time state assertion is
not an M0 closure requirement merely because M0 freezes its expected policy:

The AAPL cap checks pin feed proxy
`0x6B22A786bAa607d76728168703a39Ea9C99f2cD0`, eight answer decimals,
86,400-second heartbeat, and
`capAtomic=floor(D*10^(18+8)/P8)` for `D=5,000` and `D=25,000`. The final
freeze must prove a positive complete nonfuture fresh round at one
block/hash/timestamp, current proxy/aggregator runtime identities, round-down
arithmetic, two-person review, and configuration readback. The feed-valued
stored cap is reviewed at least every seven days and whenever it exceeds 110%
of its target.

| Owner direction | M0 pre-implementation check | Post-M0 implementation, deployment, or promotion assertions |
| --- | --- | --- |
| AAPL-only Stock launch | `check_m0_aapl_only_scope_and_later_token_evidence_rule` | `test_launch_only_aapl_stock_route_enabled`; `test_additional_stock_requires_complete_identity_transfer_oracle_control_route_row` |
| CCIP target, nonblocking | `check_m0_ccip_policy_targets_separate_promotion_within_seven_days`; `check_m0_ccip_incomplete_or_missed_target_means_disabled`; `check_m0_ccip_promotion_requires_fresh_review_package`; `check_m0_sgreen_never_has_ccip_route` | `test_launch_green_ripe_ccip_disabled`; `test_promoted_ccip_has_complete_route_and_propagation_evidence`; `test_deployed_sgreen_has_no_ccip_route` |
| sGREEN day-one | `check_m0_sgreen_chain_native_day_one_route_disposition`; `check_m0_sgreen_never_bridgeable` | `test_launch_sgreen_chain_native_deposit_withdraw_active`; `test_launch_sgreen_not_bridgeable` |
| USDG/Endaoment PSM | `check_m0_psm_canonical_usdg_and_approved_usdg_usd_feed`; `check_m0_psm_redemption_first_and_green_mint_last`; `check_m0_curve_not_psm_dependency`; `check_m0_usdg_not_ordinary_teller_collateral` | `test_launch_psm_redemption_proved_before_mint`; `test_launch_green_mint_authority_granted_last`; `test_launch_usdg_not_ordinary_teller_collateral` |
| Stability/RipeGov | `check_m0_stability_ripegov_route_dispositions_and_stock_exclusion` | `test_launch_green_stability_pool_active`; `test_launch_ripe_governance_vault_active`; `test_launch_stock_excluded_from_stability_custody_and_swaps` |
| Launch LPs | `check_m0_lp_constituent_identities_and_route_dispositions`; `check_m0_lp_artifacts_are_future_and_no_dex_is_silently_selected`; `check_m0_launch_lps_require_zero_ltv` | `test_launch_green_usdg_lp_identity_factory_pool_implementation_oracle_route`; `test_launch_ripe_weth_lp_identity_factory_pool_implementation_oracle_route`; `test_launch_lps_have_zero_ltv` |
| Stock exclusions | `check_m0_credit_redeem_stock_disabled`; `check_m0_underscore_and_base_only_integrations_omitted` | `test_launch_credit_redeem_stock_disabled`; `test_launch_underscore_and_base_only_integrations_omitted` |
| AAPL exposure | `check_m0_aapl_feed_proxy_decimals_heartbeat_and_identity`; `check_m0_aapl_cap_formula_is_floor_d_times_10_pow_26_over_p8`; `check_m0_aapl_cap_freeze_round_quality_and_two_person_review`; `check_m0_exactly_one_aapl_vault_policy`; `check_m0_all_aapl_trusted_department_routes_disabled_policy` | `test_launch_aapl_caps_equal_fixed_18_decimal_freeze_values`; `test_launch_aapl_cap_price_source_is_approved`; `test_launch_aapl_cap_review_above_ten_percent_upward_drift`; `test_launch_aapl_cap_review_every_seven_days`; `test_launch_exactly_one_aapl_vault_enabled`; `test_launch_all_aapl_trusted_department_routes_disabled` |
| Reward lifecycle | `check_m0_launch_disabled_reward_policy_and_runbook`; `check_m0_points_disable_is_fast_but_ripe_per_block_zero_is_timelocked`; `check_m0_reward_activation_target_requires_separate_validation`; `check_m0_no_reward_contract_delta_by_default` | `test_launch_rewards_globally_disabled`; `test_reward_activation_not_before_validation`; `test_aapl_depositor_and_borrower_reward_eligibility`; `test_reward_incident_monitoring_triggers_global_kill`; `test_are_points_enabled_and_ripe_per_block_runbook`; `test_emission_zero_action_executes_at_first_eligible_block` |

### 20.7 Exact-token, Base, and release tiers

| Tier | Required run |
| --- | --- |
| T0 | Static source/interface/storage/ABI/caller/config inventory, exact-transfer asset compatibility matrix, Robinhood/Base deployment-independence graph, and document checks |
| T1 | Targeted Teller, guarded-settlement vault, CreditEngine, unchanged AuctionHouse/Deleverage integration, repayment, and configuration unit tests |
| T2 | Cross-component issuer-loss state machine; frozen 90-case baseline on `be6a759`; candidate successor cases with every intentional safety inversion explicitly dispositioned |
| T3 | Read-only pinned Base refresh: ID 3's 27 assets/9 funded rows, custody/accounting/debt/auctions/config, code hashes, exact-transfer compatibility classification, plus ID 4 dust semantics |
| T4 | Integrated S1/S2 Base/Robinhood clock profiles and checked component inventory; S3 preserved independently |
| T5 | Full serial repository suite with generated artifact/ABI/storage negative proofs |
| T6 | Pinned AAPL proxy/beacon/implementation fork: transfer, pause/blocklist, implementation switch, deficit, borrow/health/auction/repay, restoration/config hold |
| T7 | Approved Robinhood clean-deployment rehearsal, explicit unchanged-Base runtime record, proved per-chain state independence, atomic enable sequence, post-state smoke/soak, and independent audit; any Base migration is a separate later tier/gate |

T3 and T6 raw results must record block number/hash, RPC provenance, contract
identity/code hashes, requests, responses, decoded values, timestamps, and
failure/unknown classification. This section does not authorize RPC
acquisition or a live transaction; later execution uses the named owner gate.

Before M1 authorization, the exact-transfer matrix must enumerate:

1. every already-existing external Stock Token and non-Stock token that the
   approved launch graph could route to the candidate Robinhood Teller, and
   the proposed route/file disposition for each not-yet-built Ripe artifact;
2. every one of the 27 current Base ID-3 registrations for forward-source and
   later-cutover compatibility, without implying that current Base runtime is
   changed;
3. proxy/beacon/implementation identities and transfer-relevant controls for
   already-existing external tokens;
4. pinned-fork or equivalent evidence for `balanceOf(vault)` deltas on each
   reachable route whose external token and route exist, including token
   pause/blocklist and implementation-change cases; and
5. an explicit exact, short/fee, rebasing-on-transfer, or unknown
   classification.

No already-existing external token proposed for an enabled Robinhood route
may be short, fee-taking, rebasing-on-transfer, or unknown. New Ripe contracts
that do not yet exist are not assigned fabricated M0 runtime rows: their
source/compiler/storage/ABI/runtime evidence, composed route tests, deployment
addresses, and post-deployment proof are post-M0 gates. A Base-only
incompatible row does not by itself block Robinhood while Base remains on its
old runtime, but it blocks any future Base cutover to the forward Teller until
separately resolved.

The independence proof must pin both chains' registries, contract addresses,
runtime hashes, custody, debt, auction, configuration, bridge/message
authorities, and token mint/burn routes. It fails on any stateful or economic
path by which a Base custody, debt, or settlement failure can change
Robinhood protocol state. Shared source or shared offchain operators alone is
not such a path.

### 20.8 Implementation-slice gates

M0–M5 from specification Section 23.9 are independently reviewable and
economically non-activatable. Each implemented slice record after M0 includes:

```text
owner authorization
integration commit and merge base
allowed and actual files
source/compiler/creation/runtime hashes
storage and ABI delta or negative proof
targeted ML tests and results
full downstream consumer inventory
Base and exact-token evidence
reviewers and findings
deployment/migration dependency
stop conditions
```

Composition gates:

1. M0 cannot pass without the existing-external-token compatibility matrix;
   approved launch graph and route dispositions; AAPL feed, price-pin
   procedure, cap formula/inputs/rounding/review rules; CCIP
   complete-or-disabled policy and separate seven-day promotion target;
   launch-disabled reward policy and operational runbook; exact proposed
   three-contract/file and unchanged-consumer boundary; source-traced
   mechanism plausibility; owner-approved partial-fill invariant;
   Robinhood/Base independence conclusion; Base urgent-risk refresh; and a
   file-exact M1 authorization proposal. Any incompatible or unknown
   already-existing external token proposed for enablement, unproved
   propagation path, or urgent Base criterion stops M0 and returns to the
   owner. Implemented GuardedErc20 evidence, composed tests, new Ripe
   addresses/runtime hashes, post-deployment route/configuration proof, exact
   freeze-time cap integers, and final M1–M5 evidence are later gates.
2. M1 cannot pass with an unreviewed deposit caller or trusted callback,
   without `R==Q` on every route, or without the donation/short-receipt
   counterexample and measurement-window mutex proof.
3. M2 cannot pass if it adds persistent policy state, permits an unguarded
   internal transfer, operates while `C<N` or backing is unknown, freezes
   solely because `C>N`, allocates a deficit/donation/surplus, returns a
   positive external amount without exact recipient delivery, returns a
   positive internal amount without the complete custody-neutral ML-05 proof,
   or permits either current Endaoment recipient.
4. M3 cannot pass if preview/state/health/repay use different backing rules or
   if one failed Stock backing read blocks repayment or safe co-collateral;
   CreditEngine raw backing reads, config consumption, or repay-mode changes
   fail the minimum-diff gate.
5. M4 cannot pass if AuctionHouse/Deleverage source or ABI changes, payment or
   Deleverage debt reduction can exceed the launch vault's proved return,
   internal mode is silently reinterpreted, either collateral-swap leg is
   request-accounted, or legacy behavior is falsely described as hardened.
6. M5 cannot pass if rewards/routes remain reachable, Base's existing runtime
   state is not exactly recorded as unchanged, per-chain state independence
   is unproven, the refreshed Base evidence trips an urgent criterion without
   owner disposition, the vault/ID is unapproved, or any intermediate enable
   state exposes only part of M1–M4.

Only the complete composed M1+M2+M3+M4-proof+M5 candidate may be described as
Stock launch-ready.

### 20.9 Accepted-risk evidence and stop conditions

The release record must quantify:

- current custody and nominal accounting for every enabled Stock Token;
- number of users and their claims;
- aggregate/user debt and mixed-collateral capacity;
- finite deposit limits and LTV;
- active auctions;
- price/issuer/token implementation state; and
- the origination/incident-time capacity bound
  `globalDepositLimit * ltv / 100%`.

Owner, risk, security, accounting, and operations must explicitly accept that
an issuer loss can freeze withdrawals/liquidation, leave residual custody
unallocated, leave user debt outstanding, accrue existing interest beyond the
capacity bound, and require a later governance/upgrade process. The record
must report full outstanding/accruing user debt separately from
Stock-attributable capacity. It must separately record that `C>N` does not
freeze nominal operations or create user entitlement: surplus may remain
stranded, but a one-unit donation is not an accepted liveness DoS.

Stop and return to the owner before implementation or activation if:

- the three-source surface plus unchanged-consumer proof cannot prove
  ML-01–ML-07;
- any asset reachable through the candidate Robinhood Teller is
  fee-on-transfer, rebasing-on-transfer, short-receipt, or unknown under an
  ordinary or trusted route;
- the deployment graph exposes a bridge, message, shared custody, credit,
  debt, settlement, or accounting path by which a Base failure can alter
  Robinhood state;
- launch-day rewards cannot be proved globally disabled, or later activation
  lacks monitoring and the two-switch kill runbook;
- guarded internal settlement cannot be enforced vault-locally without new
  persistent storage, a canonical interface change, or an AuctionHouse change;
- refreshed Base evidence proves an urgent live vulnerability and no separately
  approved Base containment can precede or safely compose with Robinhood;
- a canonical interface, persistent core storage, Ledger change, or
  corrected-share/bad-debt mechanism becomes necessary;
- exact AAPL can mutate unrelated vault custody during the measurement window;
- repayment or safe co-collateral evaluation/liquidation fails because an
  unsafe Stock position reports zero or its backing observation fails; the
  separate pinned nonzero-collateral missing-price defect remains explicit
  backlog rather than a hidden launch assertion;
- either Endaoment endpoint can receive Stock from the launch vault through an
  ordinary or privileged route;
- a partial Robinhood group can create credit, capacity, payment, or debt
  change;
- a mandatory test is skipped/relaxed; or
- owner/security/risk rejects the accepted freeze and stranded-debt model.

The safe stop is evidence return, not automatic Stock deferral and not silent
expansion into the permanent architecture.

### 20.10 Owner-review handoff

The prerequisite M0 documentation/evidence authorization was granted and used
on a separate evidence branch for read-only RPC/indexer and pinned-fork work.
It did not authorize a production test/source edit, deployment, migration,
configuration, signer, or transaction.

The 24–25 July 2026 owner record selects the guarded-settlement design direction,
activation-day reward disable with a validated seven-day reward-activation
target, accepted AAPL evidence, Robinhood-first/unchanged Base, AAPL-only
Stock scope, launch topology targets, and conservative AAPL USD targets. It
also targets a separately reviewed GREEN/RIPE CCIP promotion within seven days
after launch; the target is not automatic authorization, an incomplete or
late package leaves CCIP disabled, and sGREEN never has a CCIP route.

All documentable pre-implementation evidence and product-freeze inputs are now
complete:

1. existing external-token identities and exact-transfer compatibility;
2. the approved launch graph and route dispositions;
3. AAPL feed, price-pin procedure, cap formula/inputs/rounding/review rules;
4. CCIP complete-or-disabled policy and launch-disabled reward/runbook posture;
5. the exact proposed Teller/`GuardedErc20`/CreditEngine file boundary,
   unchanged-consumer boundary, and source-traced mechanism plausibility;
6. the owner-approved partial-fill invariant; and
7. the file-exact M1 authorization proposal naming branch, baseline, allowed
   files/tests/reviewers, stop conditions, and non-authorizations.

The proposed M1 branch is `rh-track-8-m1-exact-receipt`. Its baseline must be
the exact future reviewed `rh` commit containing the integrated M0 package;
the full hash must be inserted and separately approved before work. Its only
production file is `contracts/core/Teller.vy`; allowed existing tests are
`tests/core/teller/test_teller_deposit.py`,
`tests/core/teller/test_teller_rebalance.py`, and
`tests/vaults/test_stock_token_vault_comparison.py`. Exact stop conditions and
review roles are in specification Section 23.9.1 and owner-packet Section 10.
This is a proposal, not authorization.

Implemented GuardedErc20 source/compiler/storage/ABI/runtime evidence,
composed tests, actual new Ripe deployment addresses/runtime hashes,
post-deployment route/configuration proof, exact freeze-time cap integers, and
final M1–M5 integration/activation evidence are post-M0 checkpoints. The
vault-level onchain Endaoment prohibition remains in the proposed M2
mechanism; a runbook-only launch is not a separate or fallback option.

M0 remains open pending independent review and explicit owner closure.
VaultBook ID, defaults, manifests, migration names, deployment transactions,
and enablement remain later Track 7 and owner gates. This validation handoff
selects none of them.

This is the owner checkpoint. No test, production source, ABI, default,
migration, manifest, vault/ID, deployment, configuration, transaction, or
merge into `rh` may begin from this plan alone.
