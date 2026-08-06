# RH stock-backing containment monitoring and incident runbook

> **DRAFT — no live action authorized.** This runbook covers the composed
> GuardedErc20 and CreditEngine boundary. It does not authorize a pause,
> configuration transaction, liquidation, auction, recovery, or deployment;
> those lifecycle boundaries are explicit in the reviewed component records
> ([guarded-erc20.md](../smart-contract-changes/guarded-erc20.md),
> [credit-engine.md](../smart-contract-changes/credit-engine.md)).

Use `C` for the exact observed token `balanceOf(vault)` and `N` for
GuardedErc20 `getTotalAmountForVault(asset)`, which is the stored nominal
liability
([GuardedErc20.vy:242-254](../../../../contracts/vaults/GuardedErc20.vy#L242-L254)).

## 1. Signals and exact sources

| Signal | Exact source and evidence | Required capture |
| --- | --- | --- |
| Backing observation | Raw `balanceOf(address)` against the admitted token and Guarded vault; Guarded requires call success and exactly 32 response bytes ([GuardedErc20.vy:278-292](../../../../contracts/vaults/GuardedErc20.vy#L278-L292)) | Token/vault addresses, calldata, raw response, RPC endpoint class, observation block/hash |
| Nominal liability | `GuardedErc20.getTotalAmountForVault(asset)` ([GuardedErc20.vy:242-245](../../../../contracts/vaults/GuardedErc20.vy#L242-L245)) | `N`, block/hash, eth_call result |
| Backing-aware user value | `getUserAssetAndAmountAtIndex(user,index)` and `getTotalAmountForUser(user,asset)`; nonempty `(asset,0)` distinguishes an unsafe existing position from an empty one ([GuardedErc20.vy:204-239](../../../../contracts/vaults/GuardedErc20.vy#L204-L239)) | User, index, asset, amount, block/hash |
| Guarded activity | `GuardedErc20VaultDeposit`, `GuardedErc20VaultWithdrawal`, and `GuardedErc20VaultTransfer` event topics ([GuardedErc20.vy:20-36](../../../../contracts/vaults/GuardedErc20.vy#L20-L36)) | Transaction/block hashes, log index, emitter, topics/data, decoded fields |
| Repeated containment reverts | Failed receipts/traces for the exact Guarded dev guards: unknown backing/delivery, insufficient backing, invalid token movement/outflow/delivery, or token transfer failure ([GuardedErc20.vy:61-76](../../../../contracts/vaults/GuardedErc20.vy#L61-L76), [GuardedErc20.vy:93-135](../../../../contracts/vaults/GuardedErc20.vy#L93-L135)) | Selector, sender, user/asset, revert bytes, transaction/block hashes |
| Debt and health | `CreditEngine.getUserCollateralValueAndDebtAmount(user)`, `getUserBorrowTerms(user,...)`, and `canLiquidateUser(user)` ([CreditEngine.vy:649-685](../../../../contracts/core/CreditEngine.vy#L649), [CreditEngine.vy:815-832](../../../../contracts/core/CreditEngine.vy#L815), [CreditEngine.vy:926-979](../../../../contracts/core/CreditEngine.vy#L926)) | Before/after values at one block/hash and the price inputs used |
| Liquidation state | `Ledger.isUserInLiquidation(user)` reads the stored debt flag ([Ledger.vy:493-494](../../../../contracts/data/Ledger.vy#L493)) | User, boolean, block/hash |
| Auction entry and purchase | `LiquidateUser`, `FungibleAuctionUpdated`, `FungibleAuctionPaused`, and `FungAuctionPurchased` event topics ([AuctionHouse.vy:152-196](../../../../contracts/core/AuctionHouse.vy#L152-L196)) | Complete receipt/log evidence and decoded auction key/state |
| Settlement failure | Failed purchase/withdraw transaction plus unchanged GREEN, debt, buyer collateral, token custody, and auction state; the composed suite proves that atomic pattern ([test_stock_token_vault_comparison.py:719-793](../../../../tests/vaults/test_stock_token_vault_comparison.py#L719)) | Pre/post calls at the same pinned block context plus receipt/trace |
| Issuer/admin change | Exact production-token ownership, upgrade, pause, blocklist, burn, seizure, and redemption event topics are **UNRESOLVED — exact token ABI/address owner input required**; the local test token models these as separate powers ([MockStockTokenControls.vy:8-44](../../../../contracts/mock/MockStockTokenControls.vy#L8)) | Runtime code hash, admin/role membership, event topic and decoded fields |

## 2. Threshold logic

The backing state is derived, not guessed
([GuardedErc20.vy:248-254](../../../../contracts/vaults/GuardedErc20.vy#L248-L254)):

```text
observation unknown  := balanceOf call failed OR response length != 32
healthy              := observation known AND C == N
unexpected surplus   := observation known AND C > N
deficit              := observation known AND C < N
deficit amount       := N - C
surplus amount       := C - N
```

| Condition | Threshold and derivation | Severity |
| --- | --- | --- |
| Unknown observation | One failed or non-32-byte observation; Guarded itself treats that state as unusable backing ([GuardedErc20.vy:278-292](../../../../contracts/vaults/GuardedErc20.vy#L278-L292)) | Critical immediately |
| Custody below nominal | Any `C < N`, including one base unit; every Guarded value-moving path requires known solvency ([GuardedErc20.vy:68](../../../../contracts/vaults/GuardedErc20.vy#L68), [GuardedErc20.vy:99](../../../../contracts/vaults/GuardedErc20.vy#L99), [GuardedErc20.vy:157](../../../../contracts/vaults/GuardedErc20.vy#L157)) | Critical immediately |
| Unexpected surplus | Any `C > N`; Guarded leaves surplus uncredited and the tests prove it cannot mask a short current receipt ([GuardedErc20.vy:66-76](../../../../contracts/vaults/GuardedErc20.vy#L66-L76), [test_stock_token_vault_comparison.py:639-684](../../../../tests/vaults/test_stock_token_vault_comparison.py#L639)) | Warning immediately; escalation amount threshold **UNRESOLVED — owner decision** |
| Repeated guarded reverts | First backing/delivery-class revert is an incident signal because the guards identify unusable backing or non-exact delivery ([GuardedErc20.vy:93-135](../../../../contracts/vaults/GuardedErc20.vy#L93-L135)) | Warning on first; paging count/window **UNRESOLVED — owner decision** |
| Backing-aware zero | Nonempty `(asset,0)` for a user with nominal balance; this is the contract representation of unsafe/unknown backing ([GuardedErc20.vy:204-218](../../../../contracts/vaults/GuardedErc20.vy#L204-L218)) | Critical immediately |
| Sudden health transition | Same-block before/after change from `canLiquidateUser=false` to `true`, or positive collateral value to zero, correlated with nonempty `(asset,0)` ([CreditEngine.vy:727-769](../../../../contracts/core/CreditEngine.vy#L727-L769), [CreditEngine.vy:926-979](../../../../contracts/core/CreditEngine.vy#L926)) | Critical immediately |
| Liquidation/auction entry | Any new `LiquidateUser`/auction event involving the admitted asset after a backing alert ([AuctionHouse.vy:152-196](../../../../contracts/core/AuctionHouse.vy#L152-L196)) | Critical correlation |
| Settlement revert | One failed purchase/delivery after auction entry; continuing Guarded deficit is expected to revert atomically but does not resolve debt ([test_stock_token_vault_comparison.py:719-793](../../../../tests/vaults/test_stock_token_vault_comparison.py#L719)) | Critical immediately |
| Issuer/admin change | Any exact-token admin, implementation, pause, blocklist, burn, seizure, or redemption change once its ABI is bound | Severity mapping **UNRESOLVED — owner decision** |

## 3. Expected and anomalous states

| State | Expected | Anomalous |
| --- | --- | --- |
| Healthy | `C == N`; credit-facing values remain nominal; successful Guarded events reconcile exactly to observed custody and nominal deltas ([GuardedErc20.vy:51-79](../../../../contracts/vaults/GuardedErc20.vy#L51-L79), [GuardedErc20.vy:82-182](../../../../contracts/vaults/GuardedErc20.vy#L82-L182)) | Any event whose decoded amount does not reconcile, or a successful value move while the same-block observation shows unknown/deficit |
| Surplus | `C > N`; user credit remains nominal and surplus remains unallocated ([GuardedErc20.vy:233-254](../../../../contracts/vaults/GuardedErc20.vy#L233-L254)) | Surplus credited to a user, used to cover a short current receipt, or recovered without separately approved evidence |
| Deficit/unknown | Credit-facing amount becomes zero and deposit, withdrawal, and internal movement fail closed ([GuardedErc20.vy:51-76](../../../../contracts/vaults/GuardedErc20.vy#L51-L76), [GuardedErc20.vy:93-100](../../../../contracts/vaults/GuardedErc20.vy#L93-L100), [GuardedErc20.vy:151-179](../../../../contracts/vaults/GuardedErc20.vy#L151-L179)) | Positive credit value or successful Guarded value movement while the condition persists |
| Debt health | The nonempty zero-backed asset contributes zero collateral/max debt while retaining configured resolution terms ([CreditEngine.vy:727-769](../../../../contracts/core/CreditEngine.vy#L727-L769)) | The position disappears as though empty, is priced at nonzero value, or makes debt terms unreadable |
| Resolution lifecycle | Eligibility, liquidation state, auction creation, purchase, delivery, and bad-debt recognition are separate transitions; no earlier transition proves a later one ([credit-engine.md, execution flow](../smart-contract-changes/credit-engine.md#exact-source-delta-and-complete-execution-flow)) | An operator/report labels eligibility as liquidation, auction creation as settlement, or a reverted delivery as debt resolution |

## 4. Pause, escalation, and recovery

No row below grants transaction authority.

| Step | Required action and evidence | Authority |
| --- | --- | --- |
| 1. Confirm | Re-read `C`, `N`, backing-aware user values, health, liquidation flag, and relevant token roles/code from two independent endpoints at one pinned block/hash; preserve raw responses and errors. Exact getters are listed in Section 1. | Read authority: **UNRESOLVED — owner decision** |
| 2. Contain | Stop new operational submissions for the affected asset and prepare the smallest existing asset-level disable/pause action; do not infer authority from technical necessity. The reviewed specification directs asset-level containment while preserving repayment when safe ([stock-token-vault-change-specification.md, checkpoint decisions](../stock-token-vault-change-specification.md#122-checkpoint-decisions-and-their-actual-gates)). | Pause/config signer and quorum: **UNRESOLVED — owner decision** |
| 3. Escalate | Provide the pinned observations, first bad block/transaction, issuer/admin changes, affected users/debt/auctions, attempted actions, and exact revert bytes. | Incident lead, security owner, protocol owner, issuer contact: **UNRESOLVED — owner decision** |
| 4. Preserve separation | Record eligibility, liquidation flag, auction creation, each purchase attempt, delivery result, and bad-debt state as separate evidence rows. The code and tests do not collapse these transitions ([credit-engine.md, debt-health behavior](../smart-contract-changes/credit-engine.md#debt-health-and-liquidation-behavior), [test_stock_token_vault_comparison.py:719-793](../../../../tests/vaults/test_stock_token_vault_comparison.py#L719)). | Evidence custodian: **UNRESOLVED — owner decision** |
| 5. Recover | Require owner-approved cause removal or token/role correction, then prove `C >= N`, exact observations, exact smallest-unit delivery, health, auction/debt state, and retry atomicity before proposing re-enable. The maintained tests demonstrate pause/blocklist retry expectations ([test_stock_token_vault_comparison.py:1275-1351](../../../../tests/vaults/test_stock_token_vault_comparison.py#L1275)). | Recovery and re-enable signer/quorum: **UNRESOLVED — owner decision** |
| 6. Close | Attach before/after code hashes, configs, roles, balances, debt/auction state, successful and failed receipts, commands, environment, and monitoring restoration evidence. | Incident closure approver and retention policy: **UNRESOLVED — owner decision** |

## 5. Residual risk after recovery

Restoring `C >= N` and exact transfer behavior does not prove the issuer cannot
repeat a burn, seizure, pause, blocklist, or upgrade; exact-token governance and
monitoring remain dependencies
([test_stock_token_vault_comparison.py:856-892](../../../../tests/vaults/test_stock_token_vault_comparison.py#L856)).
A truthful-looking but false `balanceOf` response remains outside Guarded's
ability to detect
([guarded-erc20.md, residual risk](../smart-contract-changes/guarded-erc20.md#residual-risks-and-trust-assumptions)).
Recovery also does not allocate prior losses, recognize bad debt, repair an
auction, or authorize reactivation; those are separate owner-controlled
decisions
([credit-engine.md, executive verdict](../smart-contract-changes/credit-engine.md#executive-verdict)).
