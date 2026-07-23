# Robinhood Stock Token Vault Comparison

**Status:** Complete for owner review; no production vault approved

**Prepared:** 23 July 2026

**Track branch:** `rh-track-5-stock-token-vault`

**Starting commit:** `1a87e59ede2b0a08fc37c24af7f54fd864f3079f`

**Final test evidence commit:** `05940a5273cb7ff625ad0dc9bfb5ddc52c22844d`

## Executive result

Neither existing path should be approved unchanged on the present evidence.

- `SimpleErc20` conforms to its nominal-accounting implementation, but an issuer
  custody reduction bypasses that accounting. It preserves phantom collateral,
  gives early withdrawers a claim on all remaining live tokens, and—most
  importantly—allows an internal auction buyer to spend GREEN and reduce the
  borrower's debt for a zero-backed nominal claim.
- `RebaseErc20` with `SharesVault` immediately reflects the live token balance,
  socializes partial loss pro rata, and rejects zero-backed auction settlement
  atomically. At total loss, however, collateral and debt-term weights collapse
  to zero. A new liquidation cannot be started, an already-open auction cannot
  settle, and the tested Deleverage withdrawal cannot progress. Fresh deposits
  after zero also dilute the old shares to a zero-rounded claim.
- Both vaults infer a deposit from the requested amount and aggregate
  post-transfer balance rather than measuring the per-call balance delta. Once a
  vault already has assets, a short-received transfer can be reported as fully
  received. `SimpleErc20` overcredits nominal balance; `SharesVault` mints from an
  incorrect `depositAmount` and `prevTotalBalance`.

The Track 5 recommendation is therefore:

> **conditional — shared vault change specification required**

This is a recommendation, not owner acceptance of a risk and not authorization
to change production code.

## Provenance and tested sources

The worktree was created from the committed `rh` integration branch exactly as
required by the Track 5 bootstrap. Relevant production contract code is
unchanged between planning baseline
`d6efb34b5c28741fb25b053ea9b10af084fe7e53` and the starting commit.

SHA-256 source hashes:

| Source | SHA-256 |
|---|---|
| `contracts/vaults/SimpleErc20.vy` | `6b6794f1e5aaef3b53c3e931eb8fe3596aa3d44dc5d4dcc17f487340f5c89c22` |
| `contracts/vaults/RebaseErc20.vy` | `14fe0db39f96ffebbb8fa4b28fc6fe6fb173ab51095c2853885f4c37c8c41b42` |
| `contracts/vaults/modules/BasicVault.vy` | `a21a33be9b805f5ce4fd42c66f976525032b92836149c74526be613dae79d89d` |
| `contracts/vaults/modules/SharesVault.vy` | `7a0ccbfc8c98f8274c3788ef577741053426b9a7ee6618cefb84768425989b3f` |
| `contracts/vaults/modules/VaultData.vy` | `d84d81ccf45405954404fa6af2c6651ed251efeca958242934eda8f032917e7f` |
| `interfaces/Vault.vyi` | `6769283fa780a63e1b2e2fc56b8ef51f3ff9b5883f4f1c4af8905fd0b20ffde7` |
| `contracts/mock/MockStockTokenControls.vy` | `5d1527262aad66642a6e0f6dfdaad03458abdc4085a0445ebff0af8969614ef7` |
| `tests/vaults/test_stock_token_vault_comparison.py` | `1f3723db14349f30a8b4990c8c993ef1a6add65c5b798871c86192aa7cd08c6c` |

The controlling architecture was read from
`/Users/wigglez/dev/hightop-notes/random/hood/hood-chain-executive-summary.md`.
It calls for the existing ERC-20 path, comparison of `SharesVault`, disabled
Stock Token `CreditRedeem`, no special issuer-aware vault, and explicit testing
of donation, deposit measurement, zero-balance, restricted-transfer, and
internal-liquidation behavior.

### Cross-track evidence

- **Track 2:** The integration baseline contains only the Track 2 task brief, not
  a completed candidate-token or live-transfer evidence record. No live token
  behavior is claimed here. Exact candidate identity, decimals, implementation,
  and transferability remain **pending Track 2**.
- **Track 3:** The integration baseline contains only the Track 3 task brief, not
  `component-matrix.md`. Component IDs for `SimpleErc20`,
  `RebaseErc20`/`SharesVault`, `VaultBook`, `AuctionHouse`,
  `CreditEngine`, and `CreditRedeem` are **pending Track 3**. Test fixture IDs 3
  and 4 are not production IDs.
- **Reconciliation list:** replace all `pending Track 3` labels with the
  integrated stable IDs; confirm the selected vault's source/live-version
  status; reconcile any Track 2 mock overlap; rerun this suite with the exact
  candidate token on a pinned fork after Track 2 identifies it.

## Test environment and commands

- macOS; Python 3.12.0
- pytest 8.4.2
- Titanoboa 0.2.7
- Vyper 0.4.3

Commands and observed results:

```text
PYTHONPATH=. pytest -q tests/vaults/test_stock_token_vault_comparison.py -vv
90 passed in 51.19s

PYTHONPATH=. pytest -q \
  tests/vaults/modules/test_basic_vault.py \
  tests/vaults/modules/test_shares_vault.py \
  tests/vaults/modules/test_vault_data.py \
  tests/core/teller/test_teller_deposit.py \
  tests/core/teller/test_teller_withdraw.py \
  tests/core/creditEngine/test_credit_borrow.py \
  tests/core/auctionHouse/test_ah_auctions.py::test_ah_auction_buy_with_balance_transfer_basic \
  tests/core/deleverage/test_deleverage_vol_assets.py::test_single_volatile_asset_deleverage \
  tests/core/lootbox/test_loot_deposit_points.py::test_loot_deposit_points_balance_changes \
  tests/core/creditEngine/test_credit_redemptions.py::test_credit_redemption_config_disabled
133 passed in 42.72s
```

There are no unexplained test failures.

Titanoboa starts a local Anvil process for this suite. Reproduction therefore
requires permission to bind a loopback port and write the normal Titanoboa
cache; a sandbox that forbids local listeners may fail before test collection.

## Mock capability and limitation

`MockStockTokenControls.vy` is test-only. It models ordinary `transfer`,
`transferFrom`, and approval; global pause; independent sender, recipient, and
operator blocklists; administrator mint; arbitrary-holder burn; forced transfer;
forced redemption; and an administrator-selected transfer behavior.

The behavior switch can make transfers revert, return false, or deliver one base
unit less than requested. It is a behavioral stand-in for a token implementation
change. It is **not** a proxy, and the tests do not prove proxy storage layout,
upgrade authorization, initializer safety, or implementation compatibility.

The mock deliberately applies pause/blocklist controls to token movement, not
`approve()`. Exact Stock Token approval gating remains pending Track 2 and must
not be inferred from these tests. Mode 3 overlaps the short-delivery behavior of
`MockFeeOnTransferErc20`; it remains here so the same issuer-control fixture can
switch behavior after setup and exercise both vaults uniformly. It is not
presented as a separate fee-token model.

No new reentrancy scenario was added. Both deployable vault entry points used by
the matrix are `@nonreentrant`, and the issuer-control assumptions do not add an
ERC-777-style callback. The repository's `MockReentrantErc20` only attempts a
generic callback and is not a model of the Stock Token issuer controls. A
candidate token with callback behavior would materially contradict the current
Track 2 assumptions and require a pinned-token rerun.

## Accounting map

### Deposit

1. `Teller._deposit` validates the requested amount, transfers that amount to
   the chosen vault, and then calls `depositTokensInVault`; the returned vault
   amount becomes the event and API result (`Teller.vy:271-321`).
2. `TellerUtils.validateOnDeposit` obtains the pre-transfer common view for
   user/global limits (`TellerUtils.vy:104-165`), but the pre-transfer ERC-20
   balance is not passed to the vault.
3. `BasicVault` credits
   `min(requestedAmount, token.balanceOf(vault))`
   (`BasicVault.vy:23-39`). It does not measure this call's balance delta.
4. `SharesVault` also derives `depositAmount` from requested amount and aggregate
   post-transfer balance, then assumes
   `prevTotalBalance = postBalance - depositAmount`
   (`SharesVault.vy:25-46`). A short-received later transfer can therefore be
   masked by pre-existing assets.
5. `TellerDeposit.amount`, price snapshots, deposit limits, and Lootbox
   housekeeping all consume the vault-returned amount. They inherit any
   overstatement.

For `SharesVault`, raw `VaultData.userBalances` and `totalBalances` are shares,
not token amounts. `DECIMAL_OFFSET = 10**8`; conversions use virtual
`+1` asset and `+10**8` shares (`SharesVault.vy:12,199-268`). Deposits round
shares down; requested token withdrawals convert to shares with round-up;
share-to-asset views round down. The virtual terms make direct donation attacks
expensive and keep first-deposit math defined, but can dilute tiny first deposits
after a pre-existing balance and create sub-unit residual dust.

### Loss, views, and withdrawal

| Dimension | `SimpleErc20` / `BasicVault` | `RebaseErc20` / `SharesVault` |
|---|---|---|
| Stored user/total | Nominal token amount | Raw shares |
| Common user view | Stored nominal amount | Pro-rata live claim |
| Common vault-total view | Stored nominal total | Live ERC-20 balance |
| Issuer reduction | Does not change accounting | Does not change shares; lowers every live claim |
| Partial loss | Phantom collateral; first withdrawer can receive more | Loss socialized pro rata, subject to rounding |
| Total loss | Nominal balances and borrowing value persist | Live claim and collateral value become zero |
| Later donation | Old nominal mismatch persists | Old shares regain pro-rata claim |
| Fresh deposit after zero | Old claimant can take fresh tokens | Fresh shares dominate; old claim can round to zero |

`BasicVault` reduces nominal accounting before capping the outbound transfer by
the live token balance (`BasicVault.vy:43-65`). The call reverts atomically if
the cap is zero, but a nonzero cap lets an early user take the remaining live
balance. Its internal transfer moves nominal accounting without consulting or
moving the token (`BasicVault.vy:69-87`).

`SharesVault` derives withdrawals and internal transfers from the live balance
and raw shares (`SharesVault.vy:49-93,151-181`). It rejects both paths when the
live token balance is zero. The loss allocation is pro rata; rounding can leave
one or two base units in ordinary test scales.

### Borrowing power, rewards, registry, and monitoring

- `CreditEngine._getUserBorrowTerms` iterates
  `getUserAssetAndAmountAtIndex` and prices the returned common amount
  (`CreditEngine.vy:687-807`). Simple therefore retains borrowing power against
  missing assets. Rebase immediately lowers borrowing power with live custody.
  At zero, its zero amount contributes no debt-term weight; liquidation and
  redemption thresholds can become zero as well.
- `Lootbox` uses `getUserLootBoxShare`, then divides by token precision for
  non-Ripe-Gov vaults (`Lootbox.vy:805-818`). Simple returns nominal units.
  Rebase returns raw shares divided once by `10**8`, so a donation or loss does
  not change a user's reward weight until shares move. The global asset USD
  refresh uses `getTotalAmountForVault` (`Lootbox.vy:824-833`): nominal for
  Simple, live for Rebase. `test_lootbox_points_update_after_donation_and_total_loss`
  runs the real `Lootbox.updateDepositPoints`/Ledger path: user balance points
  continue accruing from the unchanged weight, while the Rebase asset/global
  USD input rises on donation and falls to zero on total loss. Monitoring must
  not label Rebase raw shares as tokens.
- `VaultBook._doesVaultIdHaveAnyFunds` delegates to the vault before update or
  disable (`VaultBook.vy:94-147`). Asset/user deregistration additionally
  requires cleared raw accounting and index state in `VaultData`. A zero live
  balance is not enough while nominal balances or shares remain.
- `scripts/params/vaults.py` and
  `scripts/params/regenerate_defaults.py` call
  `getTotalAmountForVault`. Their “total balance” output means nominal units for
  Simple and live token balance for Rebase.

## Downstream interface-consumer map

| Consumer | Common method | Consequence of vault semantics |
|---|---|---|
| `TellerUtils` | `getVaultDataOnDeposit` | Limits and minimums consume nominal amounts or converted live claims. |
| `Teller` | `withdrawTokensFromVault`, `getTotalAmountForUser` | Events and post-withdraw minimum checks use returned/live-visible values. |
| `CreditEngine` | `getUserAssetAndAmountAtIndex`, `getTotalAmountForUser`, transfer/withdraw | Borrowing, debt health, CreditRedeem, and max-withdraw inherit nominal-vs-live behavior. |
| `AuctionHouse` | `transferBalanceWithinVault`, `withdrawTokensFromVault` | Internal settlement trusts the returned amount as collateral; external settlement requires a token transfer. |
| `Deleverage` | `getTotalAmountForUser`, AuctionHouse withdrawal wrapper | Sizing uses the common claim and actual settlement uses external withdrawal. |
| `Lootbox` | `getUserLootBoxShare`, `getTotalAmountForVault` | Rebase user weight is scaled raw shares; global value is live. |
| Parameter scripts | `getTotalAmountForVault` | Same field has nominal meaning for Simple and live meaning for Rebase. |

`CreditRedeem` reaches the same CreditEngine transfer/withdraw wrapper. Stock
Token `canRedeemCollateral` must remain false; the harness verifies this flag.

Deleverage has no internal `transferBalanceWithinVault` mode. Both its volatile
asset path and its collateral-swap helper route settlement through
`AuctionHouse.withdrawTokensFromVault` (`Deleverage.vy:433,1065`). DV-01
therefore tests the complete applicable Deleverage custody surface rather than
omitting an internal branch.

## Confirmed zero-backed internal-auction issue

### Scope

This issue is confirmed in the repository-owned local test environment for the
`SimpleErc20` internal-balance-transfer auction path. The total-loss external
withdrawal path reverts atomically. `RebaseErc20` internal and external paths
also revert atomically at zero live balance.

### Deterministic maintainer reproduction

```text
PYTHONPATH=. pytest -q \
  tests/vaults/test_stock_token_vault_comparison.py::test_internal_auction_after_total_issuer_burn \
  -vv
```

The test uses only local fixtures and `MockStockTokenControls`:

1. Register the mock asset in test vault ID 3 (`SimpleErc20`), with $1 price,
   50% LTV, 80% liquidation threshold, instant auction,
   `canRedeemCollateral=false`, and `shouldSwapInStabPools=false`.
2. Bob deposits 200 tokens and borrows 100 GREEN.
3. Set token price to $0.50 and open Bob's auction while custody still exists.
4. Invoke the modeled issuer authority to burn all 200 tokens held by the vault.
5. Alice approves 20 GREEN and buys with
   `shouldTransferBalance=true`.
6. Observe: Alice spends 20 GREEN; Bob's debt falls by 20 GREEN; the internal
   transfer gives Alice a 40-token nominal vault balance; Alice receives zero
   ERC-20 tokens; vault custody remains zero; CreditEngine assigns positive
   collateral value of exactly $20 to Alice; Alice's withdrawal reverts.

The same failure is separately proved when the issuer loss happens **before**
liquidation starts:

```text
PYTHONPATH=. pytest -q \
  'tests/vaults/test_stock_token_vault_comparison.py::test_auction_started_after_total_issuer_loss[simple-erc20]' \
  -vv
```

At total loss, Simple still enters liquidation, starts the auction, charges 20
GREEN, reduces debt by 20 GREEN, and creates the same 40-token zero-backed
claim. Rebase does not enter liquidation or create an auction because its
weighted liquidation threshold collapses to zero.

### Root cause and exact state transition

1. The issuer reduction changes ERC-20 custody without calling `VaultData`.
2. `BasicVault._transferBalanceWithinVault` reduces and adds stored nominal
   balances without checking the live ERC-20 balance
   (`BasicVault.vy:69-87`).
3. `AuctionHouse._transferCollateral` accepts that returned nominal amount as
   `amountSent` (`AuctionHouse.vy:1200-1228`).
4. Auction settlement prices `amountSent`, transfers GREEN, and repays debt
   (`AuctionHouse.vy:1076-1162`).
5. CreditEngine later prices Alice's nominal common view as collateral.

The implementation behaves as written, so this is **implementation-conformant**
but violates the protocol safety invariant that a charged liquidation amount
must represent live-backed, economically deliverable collateral.

### Required remediation specification

No fix is implemented in Track 5. A separately approved, shared,
chain-portable vault-change specification must:

1. define a live-backing invariant for every amount returned from an internal
   liquidation transfer;
2. cap, reconcile, or reject internal transfer when stored accounting exceeds
   live custody;
3. prevent the recipient from receiving borrowing power for zero-backed units;
4. preserve atomic GREEN payment and debt repayment;
5. define liquidation and bad-debt progress at total live-balance loss;
6. measure the balance delta of each deposit call, including later
   short-received transfers;
7. define post-zero donation and fresh-deposit allocation;
8. preserve one canonical production source without a Robinhood-only branch;
   and
9. add migration, registry, monitoring, ABI/event, and cross-chain regression
   requirements before implementation.

## Scenario result table

Legend: **Conform** means observed behavior matches current code; **Safe** means
the stated protocol invariant holds; **Unsafe** means it does not; **Blocked**
means the operation safely reverts but required protocol progress is unavailable.
“Not accepted” is a Track 5 risk status, not a legal or commercial conclusion.
The original 60 cases use evidence commit `d8f11e9`; the next six use
`ee270ab`; the 24 re-review cases use `05940a5`, which contains the complete
90-case suite.

Evidence classification is explicit:

- **Tested** means the named test exercises the stated state transition through
  the cited integration or focused path and asserts the resulting state.
- **Source-traced** means the statement describes a code path with no distinct
  behavioral branch to execute, such as Deleverage having no internal-transfer
  mode.
- **Derived** means a forward-looking consequence follows from the asserted
  state or cited consumer path but was not a separate transaction in that row.
- **Pending** means no claim is made from this harness, including proxy
  mechanics, exact candidate-token approval rules, and live token behavior.

Concrete state transitions in the result cells are Tested. Cross-references
(`See ...`) and modal consequences (`can`, `could`, or `may`) are Derived unless
the evidence note names a separate test. Source-traced, Derived, and Pending
boundaries appear in the evidence notes where they affect the decision. In
particular, the former I-04 external-auction and A-01 later-delivery
extrapolations now have direct I-08 and A-05 tests.

| ID | Setup and actors | Issuer action | Expected invariant | Simple result | Rebase result | Actual token balance | Stored nominal balance or shares | User-visible claim | Borrowing-power effect | Withdrawal effect | Internal-liquidation effect | External-liquidation effect | Rounding or dust | Implementation conformance | Safety invariant | Accepted-risk posture | Owner approval | Test name and commit | Evidence notes | Owner decision implication |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| N-01 | Bob first deposit/withdraw; 6 and 18 decimals | None | Exact base-unit lifecycle | Exact | Within one unit | Returns to ≤1 unit | Simple nominal; Rebase shares | Equals live claim | Normal | Completes | N/A | N/A | Rebase ≤1 | Both Conform | Safe | Acceptable ordinary behavior | Pending | `test_first_deposit_and_withdrawal_at_token_decimals` @ `d8f11e9` | Candidate decimals still pending Track 2 | No differentiator |
| N-02 | Bob 100, Alice 60; partial/final withdrawals | None | Multi-user conservation | Exact | Within ≤2 units | Ends ≤2 units | Nominal vs shares | Sum tracks accounting/live | Normal | Both complete | N/A | N/A | Rebase ≤2 | Both Conform | Safe | Acceptable | Pending | `test_normal_multi_user_lifecycle_and_internal_transfer` @ `d8f11e9` | Equivalent ordinary path | No differentiator |
| N-03 | Bob internally transfers 20 to Alice | None | Recipient gets transferable live-backed claim | Nominal 20 | Live claim 20 | Unchanged | Nominal moved vs shares moved | 20 | Positive only while live-backed | Later succeeds normally | Both return 20 | N/A | None at scale | Both Conform | Safe while custody intact | Acceptable only with live-backing rule | Pending | same as N-02 | Token is not moved internally | Drives required invariant |
| N-04 | Bob deposits and withdraws one base unit | None | Smallest positive unit survives conversion | Exact 1 | Exact 1 | 1 → 0 | Nominal 1 vs `10**8` shares | 1 | Normal | Completes | N/A | N/A | None | Both Conform | Safe | Acceptable ordinary behavior | Pending | `test_one_base_unit_lifecycle` @ `ee270ab` | Empty-vault rounding boundary | No differentiator |
| D-01 | Donate 100 before Bob deposits 100 | Donation | Donation cannot cheaply steal deposit; residue is recoverable | Bob claim 100; donation unallocated | Bob claim about 99.9999995; donation/virtual terms dilute | About 200 before withdrawal | Nominal 100 vs diluted shares | As left | Mirrors claim | Completes; residue remains | N/A | N/A | Rebase dilution ≈0.0000005 | Both Conform | Safe at tested scale | Exact dilution not accepted yet | Pending | `test_donation_before_first_deposit_can_be_deregistered_and_recovered` @ `d8f11e9` | Recovery works after raw/index cleanup | Specify dust/operator UX |
| D-02 | Bob 100; donate 100; Alice deposits 100 | Donation | Allocation is explicit | Donation invisible; each claim 100 | Bob claim about 200; Alice about 100 | 300 | Nominal total 200 vs shares | 200 aggregate vs ≈300 | Simple ignores; Rebase allocates | Normal | Live-backed at time | Live-backed at time | ≤3 units | Both Conform | Both solvent; different allocation | Owner has not accepted allocation | Pending | `test_donation_between_deposits_and_common_views` @ `d8f11e9` | Rebase donation accrues to existing shares | Owner must accept allocation |
| D-03 | All raw positions removed, residue remains | Donation/residue | Governance recovery only after cleanup | Recoverable | Recoverable | Residue → 0 | Total raw → 0 | User claim 0 | None | Final user completes | N/A | N/A | Rebase residue | Both Conform | Safe with governance process | Acceptable subject to runbook | Pending | donation-before-first test @ `d8f11e9` | User and asset deregister before recovery | Add smoke/runbook |
| M-01 | Second 100-unit Teller deposit receives 99.999…999 | Behavior mode 3 | Credit and event equal per-call receipt | Reports 100; total overstates live by 1 | Reports 100; mints using wrong deposit/previous balance | 199.999…998 | Simple nominal 199.999…999; Rebase wrong shares | Simple overstated; Rebase live view hides share error | Derived state uses wrong deposit event/accounting | Later allocation differs | Can inherit error | Can inherit error | One-unit test delta | Both Conform | **Unsafe** deposit measurement | **Not accepted** | Pending | `test_short_received_second_deposit_is_reported_as_requested_amount` @ `d8f11e9` | **Tested:** wrong return/accounting; **Derived/source-traced:** downstream consumers inherit the return | Shared per-call delta spec required |
| L-01 | Bob 100; issuer removes 25 via burn/redeem/forced transfer | Issuer reduction | Claims immediately match 75 live | Claim stays 100 | Claim becomes about 75 | 75 | Nominal/shares unchanged | 100 vs ≈75 | Stale vs reduced | Simple first mover can take live | Simple nominal; Rebase live-scaled | Both can transfer ≤live | Rebase ≤1 | Both Conform | Simple **Unsafe**; Rebase Safe pro rata | Simple loss behavior not accepted | Pending | `test_partial_issuer_reduction_updates_only_live_share_claims` @ `d8f11e9` | Three issuer actions are accounting-equivalent | Reject Simple unchanged |
| L-02 | Bob 200 debt 100; issuer burns all | Total burn | Missing collateral has zero value | Claim/collateral persist | Claim/collateral zero | 0 | Nominal 200 vs old shares | 200 vs 0 | Simple stays $100 at $0.50; Rebase 0 | Both cannot pay token at zero | See A-03 | See A-04 | None | Both Conform | Simple **Unsafe**; Rebase reflects solvency | Neither total-loss behavior accepted | Pending | `test_liquidation_eligibility_after_total_issuer_burn` @ `d8f11e9` | Rebase debt terms also collapse | Shared zero-state spec required |
| L-03 | Bob/Alice each 100; live reduced to 100; reverse withdrawal order | Partial burn | Loss is order-independent | First takes 100; second gets 0 | Each gets about 50 | Ends 0/≤2 | Simple leaves second nominal 100; Rebase clears shares | Simple stale; Rebase depleted | Simple remains phantom | First-mover advantage vs pro rata | N/A | N/A | Rebase ≤2 | Both Conform | Simple **Unsafe**; Rebase Safe pro rata | First-mover risk not accepted | Pending | `test_partial_loss_withdrawal_order` @ `d8f11e9` | **Tested:** both orderings run | Reject Simple unchanged |
| L-04 | Bob retains raw position after partial or total loss; governance attempts cleanup/recovery | Partial/total burn | Cleanup reflects raw state, not only live custody | User/asset remain registered | Same | 75 or 0 | Nominal/shares remain nonzero | Nominal vs live/zero | Stale vs reduced/zero | Position cannot deregister | N/A | N/A | None | Both Conform | Recovery is correctly blocked; operational cleanup unavailable | Requires zero-state policy | Pending | `test_loss_state_blocks_deregistration_and_governance_recovery` @ `05940a5` | **Tested:** four vault/state cases; partial recovery rejects registered funds, total reports no funds | Specify cleanup/migration path |
| Z-01 | Bob old shares/nominal; total loss; later donate 25 | Donation after zero | Allocation is explicit and no phantom claim | Bob still claims 100 against 25 | Bob regains about 25 | 25 | Nominal 100 vs old shares | 100 vs ≈25 | Stale vs live | Simple can take all 25; Rebase pro rata | Same semantics | Same semantics | Rebase ≤1 | Both Conform | Simple **Unsafe** | Not accepted | Pending | `test_donation_after_total_loss_revalues_only_share_claims` @ `d8f11e9` | Rebase old shares revive | Specify recovery/donation policy |
| Z-02 | Bob 100 lost; Alice newly deposits 50 | Fresh deposit after zero | New deposit cannot be captured; old loss treatment explicit | Bob takes Alice's 50; Alice then cannot withdraw | Bob claim rounds to 0; Alice gets ≈50 | 50 → 0 | Simple nominal 150; Rebase huge new share mint | Bob 100/Alice 50 vs Bob 0/Alice ≈50 | Simple phantom; Rebase live | Simple cross-user capture; Rebase fresh user exits | Simple could transfer stale claim | External Simple first-mover exposure | Rebase ≤1 | Both Conform | Simple **Unsafe**; Rebase protects fresh deposit but erases old claim | Neither policy accepted | Pending | `test_new_deposit_after_total_loss_with_old_accounting` @ `d8f11e9` | Zero denominator plus virtual terms drives dilution | Shared post-zero policy required |
| I-01 | Pause before Teller deposit; then unpause | Pause | Revert atomically and retry | Reverts; retry succeeds | Same | 0 after failure | No accounting change | 0 | None | N/A | N/A | N/A | None | Both Conform | Safe atomicity | Accepted architecture input | Pending | `test_transfer_guards_block_deposit_atomically_and_retry` @ `d8f11e9` | Borrower=sender; vault=recipient; Teller=operator | Monitoring/runbook |
| I-02 | Pause after deposit; internal move then withdrawal | Pause | No token movement falsely proves deliverability | Internal nominal move succeeds; withdrawal blocked | Internal live-share move succeeds; withdrawal blocked | Unchanged | Accounting moves | Recipient claim positive | Positive until custody/pricing changes | Reverts; succeeds after unpause | Succeeds without token call | External path blocked | None | Both Conform | **Blocked**, not proof of delivery | Accepted transfer-revert input; false-proof risk not accepted | Pending | `test_issuer_pause_blocks_external_transfer_but_not_internal_balance_transfer` @ `d8f11e9` | Vault sender/operator; recipient user | Internal settlement needs live/deliverable rule |
| I-03 | Block borrower, vault, or Teller before deposit; unblock/retry | Blocklist | Role-specific atomic failure | All three fail/retry | Same | 0 after failure | No change | 0 | None | N/A | N/A | N/A | None | Both Conform | Safe atomicity | Accepted architecture input | Pending | `test_deposit_blocklist_roles_and_retry` @ `d8f11e9` | ERC-20 roles tested separately | Add operations checks |
| I-04 | Block vault sender, user recipient, or vault operator before withdrawal | Blocklist | Role-specific atomic failure | All three fail/retry | Same | Unchanged after failure | No change | Preserved | Preserved | Fails then succeeds | No token role check internally | See I-08 | None | Both Conform | Safe atomicity; internal caveat | Accepted architecture input | Pending | `test_withdraw_blocklist_roles_and_retry` @ `d8f11e9` | **Tested:** ordinary withdrawal roles; auction roles tested separately in I-08 | Monitoring required |
| I-05 | Transfer implementation reverts or returns false; restore mode | Behavior change | Deposit stays atomic and retryable | Fails atomically/retries | Same | 0 after failure | No change | 0 | None | N/A | N/A | N/A | None | Both Conform | Safe for tested transfer change | Proxy risk untested/not accepted | Pending | `test_transfer_guards_block_deposit_atomically_and_retry` @ `d8f11e9` | Behavior switch is not proxy proof | Track 2 fork + upgrade review |
| I-06 | Pause after auction opens; Alice tries external purchase; unpause/retry | Pause | Failed token delivery cannot charge GREEN or reduce debt | Atomic revert; retry delivers 40 | Same | Unchanged on failure; -40 on retry | Unchanged on failure | Unchanged on failure | Unchanged on failure | Buyer receives 0 then 40 | N/A | Fails then succeeds | None | Both Conform | Safe atomicity | Accepted transfer-revert input | Pending | `test_paused_external_auction_purchase_is_atomic_and_retryable` @ `ee270ab` | GREEN and debt explicitly reconciled | Operations retry/runbook |
| I-07 | Pause after auction opens; Alice buys internally, then tries withdrawal | Pause | Internal success must not imply immediate delivery | Charges 20; creates 40 nominal claim | Charges 20; creates ≈40 live claim | Custody unchanged | Nominal/shares move | Positive | Buyer gains collateral value | Reverts until unpause; then succeeds | Succeeds while paused | N/A | Rebase ≤1 | Both Conform | **Blocked delivery after successful payment** | **Not accepted as proof of deliverability** | Pending | `test_paused_internal_auction_purchase_charges_green_but_blocks_withdrawal` @ `05940a5` | **Tested:** real Teller/AuctionHouse path; GREEN and debt both change | Shared settlement/operations policy required |
| I-08 | Block vault sender, buyer recipient, or vault operator during external auction purchase | Blocklist | Failed delivery cannot charge GREEN or reduce debt | All three fail atomically/retry | Same | Unchanged on failure; ≈-40 on retry | Unchanged on failure | Buyer 0 then ≈40 tokens | Unchanged on failure | External delivery succeeds after unblock | N/A | Fails then succeeds | Rebase ≤1 | Both Conform | Safe atomicity | Accepted transfer-revert input | Pending | `test_blocklisted_external_auction_purchase_is_atomic_and_retryable` @ `05940a5` | **Tested:** six vault/role cases; Simple retry receipt exact, Rebase tolerance ≤1 | Operations retry/runbook |
| B-01 | Borrow against 200 then partial custody loss | Partial burn | Borrowing power tracks live custody | Remains nominal | Falls pro rata | 100 after 100 loss | Nominal 200 vs shares | 200 vs ≈100 | Stale vs live | See L-03 | See A-01 | See A-02 | Rebase ≤1 | Both Conform | Simple **Unsafe** | Not accepted | Pending | partial issuer and auction tests @ `d8f11e9` | CreditEngine prices common view | Reject Simple unchanged |
| B-02 | Debt 100; total loss; attempt liquidation eligibility | Total burn | Bad debt can enter defined resolution | `canLiquidateUser=true` on phantom collateral | `canLiquidateUser=false` because weighted threshold becomes zero | 0 | Nominal/shares remain | 200 vs 0 | Phantom vs none | Blocked at zero | Simple unsafe settlement; Rebase blocked | Both blocked | None | Both Conform | Neither supplies complete total-loss resolution | **Not accepted** | Pending | `test_liquidation_eligibility_after_total_issuer_burn` @ `d8f11e9` | Rebase avoids phantom but cannot start liquidation | Shared bad-debt/liquidation spec |
| B-03 | Bob deposits 100; total loss; then requests 40 GREEN | Total burn | New debt cannot use missing collateral | Borrow succeeds; debt becomes 40 | Borrow reverts; debt stays 0 | 0 | Nominal 100 vs old shares | 100 vs 0 | Simple max debt remains 50; Rebase max debt 0 | Blocked at zero | Simple claim remains internally movable | External token unavailable | None | Both Conform | Simple **Unsafe**; Rebase Safe borrow rejection | **Not accepted for Simple** | Pending | `test_new_borrow_after_total_issuer_burn` @ `ee270ab` | Direct proof of new phantom-backed borrowing | Reject Simple unchanged |
| A-01 | Auction opened; partial loss; Alice pays 20 at $0.50 internally | Partial burn | Charged amount is currently live-backed | Gets 40 nominal while 100 live remains | Gets ≈40 live claim | Vault remains 100 | Nominal moved vs shares moved | ≈40 | Recipient gains value | Currently withdrawable if early | Both settle; Simple inherits insolvency order risk | N/A | Rebase ≤1 | Both Conform | Rebase Safe; Simple conditionally deliverable only before others | Simple risk not accepted | Pending | `test_auction_after_partial_issuer_loss_reconciles_payment_and_delivery` @ `d8f11e9` | **Tested:** current delivery; later insolvency ordering proved separately in A-05 | Live-backing invariant required |
| A-02 | Same auction, external delivery | Partial burn | GREEN/debt match actual tokens delivered | Delivers 40 | Delivers ≈40 | Falls from 100 to ≈60 | Accounting reduced | Seller reduced | Recomputed | Buyer receives token | N/A | Both settle | Rebase ≤1 | Both Conform | Safe while transfer succeeds | Accepted architecture input | Pending | same as A-01 @ `d8f11e9` | Return amount is bounded by live transfer | Prefer external proof where policy allows |
| A-03 | Auction opened before total loss; Alice pays internally | Total burn | No GREEN for nonexistent collateral | **Spends 20; debt falls 20; receives 40 nominal; token receipt 0** | Reverts; GREEN/debt unchanged | 0 | Simple nominal moves; Rebase shares unchanged | Simple positive; Rebase 0 | Simple recipient gets phantom value | Simple cannot withdraw | Simple **unsafe settlement**; Rebase blocked atomically | N/A | None | Both Conform | Simple **Unsafe**; Rebase Safe atomicity but no progress | **Not accepted; owner stop gate triggered** | Owner approved analysis continuation only | `test_internal_auction_after_total_issuer_burn` @ `d8f11e9` | Confirmed critical invariant failure | Reject Simple; specify shared fix |
| A-04 | Auction opened before total loss; external delivery | Total burn | Failure cannot charge GREEN or reduce debt | Reverts atomically | Reverts atomically | 0 | Unchanged | Unchanged | Unchanged | No token | N/A | No payment/debt change | None | Both Conform | Safe atomicity; progress blocked | Atomicity accepted; total-loss dead end not accepted | Pending | `test_external_auction_after_total_issuer_burn_reverts_atomically` @ `d8f11e9` | Auction remains open | Define bad-debt path |
| A-05 | Two buyers each pay 40 internally after partial loss; reverse withdrawal order | Partial burn | Purchased claims remain order-independent and live-backed | Each receives 80 nominal against 100 live; first withdraws 80, second 20 | N/A | 100 → 0 | Buyers hold 160 nominal before withdrawal | 80 each before race | Each initially gets $40 value | First-mover captures 60 more tokens | Both purchases settle | N/A | None | Simple Conform | Simple **Unsafe** | Not accepted | Pending | `test_simple_internal_auction_two_buyer_withdrawal_order` @ `05940a5` | **Tested:** both buyer withdrawal orderings | Reject Simple unchanged |
| A-06 | Issuer burns 100 before liquidation starts; buy internally and externally | Partial burn before auction | Post-action auction uses current live state | Both modes settle; internal remains order-sensitive | Both modes settle pro rata | 100 before buy | Nominal vs shares | 40/≈40 | Debt falls 20 | Internal claim or external receipt | Settles | Settles | Rebase ≤1 | Both Conform | Rebase Safe; Simple order risk remains | Simple risk not accepted | Pending | `test_auction_started_after_partial_issuer_loss_settles` @ `05940a5` | **Tested:** four vault/mode cases and purchase event; Simple exact, Rebase tolerance ≤1 | Post-action half of lifecycle is now explicit |
| A-07 | Issuer burns all before liquidation starts | Total burn before auction | Missing collateral cannot create paid auction | Starts auction; 20 GREEN buys 40 zero-backed nominal | No liquidation mode and no auction | 0 | Nominal/shares remain | 200 vs 0 before purchase | Simple phantom threshold; Rebase threshold zero | Simple buyer cannot withdraw | Simple unsafe settlement | N/A | None | Both Conform | Simple **Unsafe**; Rebase blocks progress | **Not accepted** | Owner approved analysis continuation only | `test_auction_started_after_total_issuer_loss` @ `05940a5` | **Tested:** both vaults; Rebase decline returns zero, starts no auction, and leaves debt outside liquidation | Shared total-loss specification required |
| DV-01 | Governance volatile-asset Deleverage after partial then total loss | Partial then total burn | Repaid debt equals delivered collateral; zero failure atomic | Partial repays 20; zero attempt reverts | Same | 80 after partial; 0 after total | Reduced on partial; unchanged on failed zero attempt | Live/nominal semantics persist | Debt -20 only on delivery | External delivery only | N/A | Atomic | Rebase rounding none at scale | Both Conform | Safe atomicity; total progress blocked | Stock Tokens must not route to Endaoment in production | Pending | `test_deleverage_external_withdrawal_after_partial_and_total_loss` @ `d8f11e9` | **Tested:** applicable external path; **Source-traced:** Deleverage has no internal mode | Keep integrations disabled; specify zero path |
| E-01 | Deposit 100, internally move 20, withdraw 30 | None | Events equal returned amounts, token deltas, and raw share deltas | Amount fields exact | Amount and share fields exact | Reconciles after each call | Nominal/share deltas equal events | Matches resulting state | Normal | Exact event/receipt | Exact event/internal delta | N/A | None at scale | Both Conform | Safe event-state reconciliation | Acceptable current interface | Pending | `test_vault_events_reconcile_amounts_shares_and_state` @ `05940a5` | **Tested:** Teller plus all three vault event families | Preserve/add explicit units in follow-on spec |
| R-01 | Donation/loss while raw positions remain | Donation/reduction | Reward and monitoring units are explicit | User/global nominal | User raw-share weight unchanged; global total live | Varies live | Nominal vs shares | Nominal vs live claim | As common claim | As above | As above | As above | Share scaling `10**8` | Both Conform | Safe only if consumers label units | Monitoring risk not accepted silently | Pending | donation and issuer-reduction tests @ `d8f11e9` | **Tested:** direct Vault view invariants | Update schemas/dashboards if Rebase |
| R-02 | Real Lootbox update after donation, elapsed blocks, then total loss | Donation then burn | Points state uses explicit user and global units | User weight and $100 global input remain nominal | User weight unchanged; global input $100→$200→$0 | 100→200→0 | Nominal vs shares unchanged | Reward weight unchanged | Balance points accrue for both; global USD diverges | N/A | N/A | N/A | Precision `10**9`; Rebase share offset applied before | Both Conform | Monitoring labels required | Not accepted silently | Pending | `test_lootbox_points_update_after_donation_and_total_loss` @ `05940a5` | **Tested:** `Lootbox.updateDepositPoints` and Ledger state, not view-only | Specify reward policy and alerts |
| C-01 | Register/configure both fixture vaults | None | Required flags and exact registry selection | Test ID 3 | Test ID 4 | N/A | N/A | N/A | Configured | Enabled | Internal available | External available | N/A | Both Conform | `CreditRedeem=false`, Stab swap=false verified | Required posture | Pending | `test_registry_and_required_asset_flags` @ `d8f11e9` | IDs are fixtures, pending Track 3 for production | No production default yet |

## Observed behavior versus accepted behavior

The selected architecture accepts that an issuer may pause, blocklist, burn,
force-transfer/redeem, or upgrade the Stock Token. Acceptance of the issuer
authority is not acceptance of every downstream accounting result.

The controlling executive summary previously accepted interim phantom
overstatement after an administrative burn
(`hood-chain-executive-summary.md:196`). Track 5 supplies materially stronger
evidence than that earlier framing: the stale amount is not only passive
reporting or delayed borrowing-power drift. AuctionHouse can actively treat it
as delivered collateral, charge a third-party buyer GREEN, reduce borrower
debt, and give the buyer an undeliverable claim. That active settlement harm,
plus the proved two-buyer ordering, reopens and supersedes the interim
accepted-consequence framing for vault selection. It does not reverse the
owner's acceptance of issuer authority; it shows that the present vault
response to that authority requires a new decision.

Current Track 5 acceptance state:

- ordinary ERC-20 operation: technically acceptable;
- transfer reverts with atomic rollback: technically acceptable, with operations
  monitoring;
- paused internal-auction settlement: implementation-conformant but not accepted
  as proof of delivery; GREEN/debt can move before the buyer can withdraw;
- Simple phantom collateral, first-mover loss, post-zero capture, and
  zero-backed internal-auction payment: **not accepted**;
- Rebase pro-rata partial-loss treatment: recommended behavior, not yet owner
  approved;
- Rebase donation allocation, raw-share rewards, post-zero dilution, and
  total-loss liquidation dead end: **not accepted**;
- per-call deposit mismeasurement: **not accepted for either path**;
- proxy upgrade compatibility and exact candidate-token behavior: unproven.

## Remaining evidence gaps

1. Track 2 exact token identity, decimals, current implementation, and live
   third-party-contract transferability, including whether approval itself is
   pause- or blocklist-gated.
2. A pinned-fork rerun against that exact token; mock behavior is not live proof.
3. Track 3 stable component IDs and source/live deployment status.
4. Owner-defined minimum invariants for total-loss bad-debt resolution,
   post-zero allocations, donation allocation, reward units, and monitoring.
5. A separately approved shared vault-change specification and implementation
   review if the owner wants to proceed.
6. Production manifest/default/migration/smoke evidence after—not before—the
   vault and change specification are approved.
7. Proxy storage, upgrade authorization, initializer safety, and callback-token
   behavior if Track 2 shows the candidate differs from the present
   non-callback behavior-switch model.

No live transaction, deployment, signing key, production configuration, or
production contract was used or changed in this track.
