# Retained StabilityPool compatibility coverage

This follow-up extends PR #233 from `ace6996059e51f85cd1fee2cfd39b436f889d6e3`. It adds 115 ordinary, network-independent test cases using the authenticated historical Pool-1 fixture. The existing CI core and supporting shards discover these files without changes to exclusions or required checks.

| Suite | New cases | Behaviors |
| --- | ---: | --- |
| `test_base_legacy_pool_arithmetic.py` | 16 | Exchange-rate growth after partial repayment; LP/sGREEN rates; seven residual amounts and both borrower orders (168 combinations inside the 12 fixed-rate cases) |
| `test_base_legacy_pool_composition.py` | 20 | Actual retained and modern pools together; both priority orders; paused, unavailable, and depleted positions; multiple redemption assets; payment/refund forms; auto-deposit; partial budgets and both internal cohort orders |
| `test_base_legacy_pool_lifecycle.py` | 12 | Unequal holders and two cohorts; partial multi-item claims; shared claims; price loss/recovery; redemption; claim removal/re-addition; full exits/redeposit; reward-budget exhaustion; direct and auto-deposit batch rollback |
| `test_base_legacy_pool_policy.py` | 32 | Minimum-debt and full-payoff boundaries; targets crossing cohorts; both internal asset orders; nonzero minimum repayment, buffer, cooldown, liquidation fees and keeper fee floors/caps |
| `test_vault_book_legacy_boundaries.py` | 26 | Final conversion and price read outcomes; short and overlong replies; full allowance consumption; multiplication limits; smallest executable payment and full NAV preservation |
| `test_legacy_keeper_composition.py` | 9 | Real local Teller simulation and receipt events; changed state/caller/batch/budget; incomplete repayment; clearing a previous preflight success after a failed retry |

The lifecycle model uses unit prices and independent dollar-entitlement/custody accounting. It checks user and aggregate shares, liabilities, token custody and delivery, debt, reward supply/budget, allowances, and claim indexes after each operation. Historical empty user-asset entries may persist until a Lootbox checkpoint, so it also checks the balance marker rather than assuming immediate index removal. Separate arithmetic and liquidation cases cover non-unit prices, exchange-rate movement and fee-bearing settlement. The synthetic sub-one sGREEN rates and uint256 limits are explicit boundary conditions, not claims about normal balances or prices.

The sGREEN rate-change regression distinguishes the correct helper from an incorrect one-for-one custody conversion: the former passes all four cases and the latter fails the zero-executable-amount assertion. Fixed-rate cases alone did not detect that incorrect conversion during the preceding review.

## Updates exposed by the tests

A reused `dry_run()` report previously retained `keeper_ready: true` and the prior batch details if a later attempt failed its checks. The new gas-budget retry regression reproduced that result. The function now clears readiness and previous execution/intent fields before any admission check. Readiness becomes true only after the new simulation and all-user reconciliation succeed. This changes the local diagnostic tool; it does not change contract settlement or send transactions.

The VaultBook ABI and completion seal have been regenerated after the preceding source reordering. Public ABI entries are unchanged when order is ignored. The implementation prompt now uses portable paths so that the existing repository hygiene check can pass.

## Running the coverage

Use the pinned repository environment and a writable `RIPE_BOA_CACHE_DIR`. Set `PYTHONDONTWRITEBYTECODE=1` when sharing an existing dependency environment. These suites are included in ordinary pytest selection:

```sh
python -m pytest -q \
  tests/registries/test_vault_book_legacy_compat.py \
  tests/registries/test_vault_book_legacy_boundaries.py \
  tests/core/auctionHouse/test_base_legacy_vault_compat.py \
  tests/core/auctionHouse/test_base_legacy_pool_arithmetic.py \
  tests/core/auctionHouse/test_base_legacy_pool_composition.py \
  tests/core/auctionHouse/test_base_legacy_pool_lifecycle.py \
  tests/core/auctionHouse/test_base_legacy_pool_policy.py \
  tests/core/deleverage/test_deleverage_sc09_stab_availability.py \
  tests/test_legacy_keeper_composition.py \
  tests/test_legacy_vault_preflight.py
python scripts/export_abis.py --check
python -m pytest -q tests/inventory/test_repository_hygiene.py
```

## Local validation results

The final focused selections passed **337 cases**: 232 existing compatibility, arithmetic, lifecycle, boundary and modern-availability cases; 52 composition and policy cases; and 53 keeper/monitoring cases. This includes all 115 additions.

- Deployment controls and repository hygiene: **877 passed, 13 deselected**, preserving the current CI exclusions.
- Runtime sizes, workflow selection, manifest consumers and ABI export tests: **23 passed**. This selection overlaps some deployment-control coverage; the counts are not a distinct-test grand total.
- ABI inventory check: **60 outputs**, current completion seal.
- Repository hygiene after staging all new files: **2 passed**.
- New test-file formatting/import checks and `git diff --check`: passed.
- Controlled incorrect sGREEN conversion: **four expected failures** at the amount assertion. The ordinary implementation passes those cases; the variant exists only in the review process and is not committed.
- Preflight retry before the fix: the over-budget retry reproduced stale readiness. The full monitoring selection passes after the fix.

No new live Base fork or production keeper run is claimed by these local results.

## Separate qualification requirements

These tests strengthen local behavioral coverage. They do not change the bridge PriceDesk configuration or replace the recorded failed Base rehearsal with a successful result. The exact nested route, mixed holders and 26-claim inventory in [issue #237](https://github.com/Ripe-Foundation/ripe-protocol/issues/237) still require successful final-configuration execution, including genuine retained token balances and runtimes. That work must preserve the original difficult routes and prove per-user settlement within the intended gas budget.

The local keeper tests exercise actual contract simulation, changed-state rejection and event reconciliation. The external production scheduler, actual keeper caller, complete current user inventory, and final receipt integration remain the separate requirements in [issue #236](https://github.com/Ripe-Foundation/ripe-protocol/issues/236). No production keeper implementation exists in this repository. These tests do not claim that external integration has been completed.

The modern pool rounding follow-up in [issue #234](https://github.com/Ripe-Foundation/ripe-protocol/issues/234) remains separately scoped. No historical fixture sources, deployed configuration, recorded manifests, or activation gates are changed by this coverage follow-up.
