# Retained vault compatibility coverage

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

These tests strengthen local behavioral coverage. They do not change the bridge PriceDesk configuration or replace the recorded failed Base rehearsal with a successful result. The later retained-RipeGov section below records successful nested pricing and selected mixed-holder settlements with #238. Full 26-claim settlement capacity in [issue #237](https://github.com/Ripe-Foundation/ripe-protocol/issues/237) remains unqualified; successful individual quotes do not establish batch capacity.

The local keeper tests exercise actual contract simulation, changed-state rejection and event reconciliation. The external production scheduler, actual keeper caller, complete current user inventory, and final receipt integration remain the separate requirements in [issue #236](https://github.com/Ripe-Foundation/ripe-protocol/issues/236). No production keeper implementation exists in this repository. These tests do not claim that external integration has been completed.

The modern pool rounding follow-up in [issue #234](https://github.com/Ripe-Foundation/ripe-protocol/issues/234) remains separately scoped. No historical fixture sources, deployed configuration, recorded manifests, or activation gates are changed by this coverage follow-up.

## Retained RipeGov follow-up with PR #238

This follow-up includes the new StabilityPool tests at `6252f649226da9739ee21a13efc79ac60bea6856`
and combines that contract source with PR #238 at
`0c43eaf53b3a9fd33c90db244b3e530b2c5f1390` for the fork checks. PR #232 is absent.
No additional RipeGov adapter or production contract edit was required by these
checks. The existing Ledger and governance vault remain in place at HQ slot 4
and VaultBook row 2 respectively.

The added historical Ledger and Contributor fixtures are byte-for-byte copies
of recorded compiler inputs, authenticated by source and runtime hashes in
`tests/fixtures/legacy_governance/provenance.json`. The governance suite covers
RIPE/LP deposits and locked/mature withdrawals, positive rewards, restaking,
StabilityPool bonuses staking into old RipeGov with the historical Ledger,
historical Contributor callbacks, transfer/cancellation boundaries, permissions,
paused-Ledger rollback, and exact shares/custody/reward-budget accounting. The
Ledger runtime substitution is isolated to each test. The Base-defaults test
executes the real MissionControl/Foxtrot configuration and reward initialization
methods, including early/repeated/unauthorized rejection and retained routing.

The existing gas diagnostic now selects HumanResources at HQ **15**, and checks
all substituted department identities and reverse IDs. HQ **14** remains the
retained Endaoment. Five cases reject wrong HR, reverse IDs, disabled rows or an
overwritten Endaoment.

[The read-only fork evidence](legacy-vault-rehearsal/retained-governance.json)
records Base block **51,614,967** and its hash, contract/runtime hashes and local
substitutions. It authenticates both registered historical Contributors and
transfers both positions, including a pending transfer spanning the department
switch. With #238's quote/snapshot allowances both set to **3,000,000** locally:

- The previously failing holder completes both reward claim modes. The default
  mode mints 25% to the wallet and stakes 75%, as configured; explicit restaking
  stakes 100%. Supply and custody deltas reconcile exactly to the returned claim.
- All four mixed holders pass strict debt valuation, and all **26 original
  stress assets** return strict prices, without token-balance or price overrides.
- One mixed-holder settlement, two-user LP/sGREEN settlements in both orders,
  and a target crossing both internal cohorts reconcile credit and debt changes.
  These consume **6.54M–8.45M execution gas** and pass with **15.95M supplied
  execution gas**, leaving 50k for intrinsic gas below a 16M transaction budget.
- At **12.8M supplied execution gas**, claims and the small mixed-holder settlement
  pass; both two-user orders and the cross-cohort target revert with
  `insufficient legacy read gas`. The 8M compatibility-read guard makes supplied
  gas materially different from consumed gas. These are measured examples,
  not a universal batch-size guarantee or a minimum-gas search.

The fork uses candidate configuration, a local retained-only VaultBook (rows
1–5), and explicitly substituted department/PriceDesk runtimes. It sends **zero
live transactions**. It is contract-composition evidence, not evidence that the
production configuration or a deployment process has been verified. Production
RPC gas estimation and external keeper execution are not certified here.

Run the ordinary governance/department tests in #233. Run the fork probe in a
combined #233 + #238 source tree, which supplies `pricedesk_gas_probe.py`:

```sh
python -m pytest -q tests/core/auctionHouse/test_base_legacy_governance.py \
  tests/test_legacy_department_graph.py
PYTHONPATH=. python tests/diagnostics/retained_governance_probe.py \
  --manifest migration_history/base-mainnet/v1/current-manifest.json \
  --block 51614967 --output /tmp/retained-governance.json
```

The probe refuses to overwrite its output. `--transaction-gas 12800000`
reproduces the lower-funding failures and exits nonzero after writing evidence.
Use the pinned Python dependencies and a writable `RIPE_BOA_CACHE_DIR` for pytest.

Accepted boundaries remain explicit: historical lock adjustment/release can
leave the Ledger reward checkpoint stale; zero weight does not disable old
points, and pausing the old vault does not freeze all lock methods. Those tests
reproduce inherited behavior, not a fix. Modern point-disable/migration methods
are unsupported on the retained vault. Keeping core vault 2 avoids requiring
legacy Contributor routing overrides; a later core rotation needs separate work.

The historical **26-claim settlement capacity remains unqualified** under 16M;
26 successful individual prices do not make that batch supported. Issue #235's
historical-runtime contract checks and the pricing/selected-settlement portions
of #237 now have evidence, while full inventory, external keeper and operator
sign-off retain their separate scope. No deployment scripts, manifests, Safe
batches, activation procedures or CI definitions were changed by this follow-up.


The added **23 governance** and **5 department-identity** cases pass. Regression
checks also pair the historical fixture with modern Contributor callbacks and
runtime pins in the same process, verifying restoration of both EVM state and
Boa's source registry. All **115** tests from the incoming #233 commit pass in
the combined source tree. Individual PR ABI checks match **60** outputs for #233
and **59** for #238; the integrated tree regenerates and checks **60** outputs.
The combined runtime pins include Teller **24,488** (88 bytes spare), PriceDesk
**18,156**, VaultBook **18,382**, AuctionHouse **24,565** and Deleverage **24,430**.

The isolated integration resolves overlapping fixture/size-pin changes using
#233's retained-VaultBook fixtures and #238's Teller/PriceDesk runtime sizes,
then regenerates the ABI completion seal. Production contract sources merge
without conflict. The PR branches remain independently reviewable; no combined
branch is substituted for either PR or for the operator's deployment process.
Historical fixture whitespace is retained intentionally for byte-for-byte
source provenance; whitespace checks cover the remaining changes.

The final combined regression selection passed **175 cases** (28 ordinary-marker
exclusions), including the corrected fixture restoration, real repayment and
Curve relay cases, PriceDesk allowance cases, runtime pins and source-count guards.
