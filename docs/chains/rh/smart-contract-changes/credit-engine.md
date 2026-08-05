# CreditEngine: zero-backing debt-term containment

> [!IMPORTANT]
> **Draft explanatory synthesis.** This record explains a reviewed
> implementation snapshot. It is not controlling approval, deployment,
> activation, migration, or release evidence, and it does not authorize any
> source, test, configuration, or operational change.

## Current candidate rebind

The candidate is rooted at feature baseline
`1e36c0c3dd168dbf292456eb5760b02d1f1e4a80`; the reviewer follow-up parent is
`fdf19226f0d8f4b42741f2ce324f8ccb9ba20336`. The exact current source,
artifact, and test identities are bound below. The 28 July snapshot and its
test counts remain dated historical evidence.

| Current identity | Value |
| --- | --- |
| CreditEngine source Git blob / SHA-256 | `ef7724393d3b9f30f6e4281a1a465c5d2cc49895` / `05bb1157c6885fc734cc4831efa2fe6aa4c189d14a1bc22bb80472103de105bb` |
| Runtime template | 24,151 bytes; SHA-256 `082c3f6c124447a43bcd4835237c134864ba3036f9a8d190ef6b16ac6e8e3696`; 425 bytes EIP-170 headroom |
| [`test_stock_backing.py`](../../../../tests/core/creditEngine/test_stock_backing.py) | Git blob `12725393abbc15c1c8ce3752894defa24ddac2a8`; SHA-256 `914b97141044c616187a1c96befdfcbf5bee5cc033476260416a4bb608003e4d` |
| [`test_credit_borrow.py`](../../../../tests/core/creditEngine/test_credit_borrow.py) | Git blob `294afab81d3cbf012d1566c374efa082c7a1e9ee`; SHA-256 `5c43dff4e0c1aef5065f42807d25726c4e2c7fab42d151603205476bab35af44` |
| [`test_credit_repay.py`](../../../../tests/core/creditEngine/test_credit_repay.py) | Git blob `0c6390fcb54480cfe1376af1958c2ee97071e9cb`; SHA-256 `a65e733eb632dc74d1e69c42062ed7fda49dc60de322dd56d58aa13592490d91` |
| [BasicVault safety test](../../../../tests/vaults/test_basic_vault_safety.py) | Git blob `d648347623a705fb039789b7b1b7952726897d11`; SHA-256 `12960d088b672fd1ec0065b0fa5134115b2f7f0d4d68502fd9663f0f505c6919` |

Later integrated hardening closes the former withdrawal-surface and
many-position-gas evidence gaps with
`test_c1_max_withdrawable_numeric_null_and_terms_failure_surface` and the C2
marginal gas protocol. Later AuctionHouse/Deleverage Stock composition is also
present and inspected separately. No behavioral suite was rerun for this
documentation-only refresh.

## Authority and status labels

- **Integrated fact:** directly present in the reviewed repository snapshot.
- **Historical evidence:** a result recorded by an earlier implementation or
  validation run; it is not silently promoted to a current result.
- **Independently reproduced result:** rerun against the reviewed snapshot by
  the prior read-only audit; it was not rerun for this documentation revision.
- **Agent recommendation — not owner-approved:** advisory only.
- **Owner-approved direction:** an explicit owner instruction controlling this
  record.
- **Owner-parked work:** not a current work item or current Wave 1 blocker;
  parking does not decide eventual release disposition.
- **Deployment or release gate:** evidence required before the relevant
  deployment or activation; integration alone does not satisfy it.

## Reviewed implementation snapshot

| Field | Reviewed value and status |
| --- | --- |
| Implementation commit | `4c26d7d73bb02f7eae2e5df02314db77a426aced` |
| Implementation parent | `e39815d710ecfaf8bbeea54cabe8ae8d553a2740` |
| Reviewed `rh` commit | `cca60bb85c772c977bb9fb62c1c6c5252c3a1438` |
| Reviewed `rh` tree | `161fb828f3bbf4cb12596a5dfaf6c9bf1e153381` |
| Review date | 28 July 2026 |
| Production source | [`contracts/core/CreditEngine.vy`](../../../../contracts/core/CreditEngine.vy) |
| Production source SHA-256 | `7de649cece6e076b75775bb4ff5f397bf5ffa0a50ccdc462a061ca047b888e3d` |
| Integration status | **Integrated fact:** the implementation commit is an ancestor of the reviewed `rh`; the five implementation paths have no later byte difference at that snapshot |
| Deployment status | Not established by this record |
| Activation status | Not established or authorized by this record |

The harmonization preflight also observed local `rh`, checked-out `HEAD`, and
cached `origin/rh` at the same reviewed commit and tree. The phrase “reviewed
implementation snapshot” is intentional: the implementation commit is not
treated as permanently synonymous with whatever `rh` may contain later.

## Direct answers to the owner's questions

| Owner question | Direct answer |
| --- | --- |
| Why did CreditEngine change? | A nonempty `(asset, 0)` can mean an existing nominal position whose backing is unsafe or unknown. The old code skipped it and erased its liquidation, redemption, fee, rate, and LTV terms from the account calculation. |
| What was the rationale? | Give the unsafe position zero value and borrowing capacity without making existing debt invisible or blocking healthy co-collateral and repayment with an unnecessary zero-amount price lookup. |
| What does the change actually do? | It skips only an empty asset address, retains configured terms for a nonempty position, values a zero amount at zero, and calls PriceDesk only for a nonzero amount. |
| Does CreditEngine inspect token custody? | No. The selected vault owns backing classification and reports the `(asset, amount)` pair. CreditEngine consumes that canonical vault result. |
| Can Stability Pool positions affect borrowing terms? | No. CreditEngine explicitly skips vault ID `1`; the Stability Pool getter remains truthful so non-borrow consumers such as AuctionHouse can enumerate positions. |
| Why is `raw_call` used? | It is not used. BasicVault calls typed `IERC20.balanceOf` directly, and CreditEngine consumes the vault's result rather than duplicating custody policy. |
| Does zero backing automatically liquidate a user? | No. It can immediately change computed value, health, and eligibility. An authorized transaction must still pass Teller and AuctionHouse gates before liquidation state or auctions change, and later settlement remains vault-dependent. |
| Is a CreditEngine source correction currently recommended? | No active Wave 1 correction is recommended or authorized by this record. `lowestLtv`, interest treatment, settlement, loss allocation, and bad-debt ideas are unapproved, owner-parked research findings. |

## Executive verdict

| Question | Conclusion |
| --- | --- |
| Is the integrated source technically justified? | **Yes.** It is a six-line functional containment correction with a narrow, coherent responsibility. |
| Is a source correction currently recommended? | **No active correction.** The reviewed source should remain the reference snapshot unless the owner reopens a parked research question. |
| What remains before deployment or activation? | Exact artifact/configuration binding, release-snapshot focused and composed validation, deployment evidence, monitoring, and an operational response path. These are gates around the source, not proof of a source defect. |
| What is owner-parked? | Cross-asset `lowestLtv`, post-loss interest policy, settlement, recapitalization, loss allocation, and bad-debt design. They are not current Wave 1 blockers or automatic implementation assignments. |

The current integrated Deleverage source and composition tests were inspected
for the package-level rebind; they do not enlarge this CreditEngine rationale
or authorize further Deleverage work. CCIP remains outside this analysis.

## Behavior before the change and the concrete failure mode

BasicVault distinguishes two superficially similar results:

```text
(empty address, 0)  = no position exists
(asset address, 0)  = a nominal position exists, but backing is unsafe or unknown
```

The old CreditEngine skipped both. That was safe for a genuinely closed
position but dangerous for existing debt backed by an unsafe asset: skipping
the nonempty position also erased its configured liquidation, redemption,
fee, rate, and LTV terms.

For a sole zero-backed position with debt, the old result could be:

- zero collateral value;
- zero capacity;
- zero liquidation threshold; and therefore
- `canLiquidateUser == false`.

The debt had become unsafe but less discoverable and less actionable. The
source correction was therefore about preserving debt-resolution visibility,
not manufacturing collateral value.

## Exact source delta and complete execution flow

The implementation hunk is reproducible with the command in the final section.
Git reports four additions and four deletions. Six changed lines are
functional; the remaining two deletions are blank-line cleanup and were not
necessary to the behavior:

```diff
-            if asset == empty(address) or amount == 0:
+            if asset == empty(address):
                 continue
 ...
-            collateralVal: uint256 = staticcall PriceDesk(_a.priceDesk).getUsdValue(asset, amount, _shouldRaise)
+            collateralVal: uint256 = 0
+            if amount != 0:
+                collateralVal = staticcall PriceDesk(_a.priceDesk).getUsdValue(asset, amount, _shouldRaise)
```

CreditEngine now skips only an empty asset address. For a nonempty asset it:

1. loads the configured debt terms;
2. still excludes an asset whose configured LTV is zero;
3. initializes collateral value to zero;
4. calls PriceDesk only when the reported amount is nonzero;
5. calculates zero maximum debt when collateral value is zero;
6. uses fallback aggregation weight `1` when maximum debt is zero; and
7. retains the position in lowest-LTV and weighted-term calculations.

In simplified form:

```text
asset, amount = vault.getUserAssetAndAmountAtIndex(user, index)

if asset is empty:
    skip

terms = MissionControl.getDebtTerms(asset)
if terms.ltv == 0:
    skip

value = 0
if amount != 0:
    value = PriceDesk.getUsdValue(asset, amount)

maxDebt = value * terms.ltv
weight = max(maxDebt, 1)
aggregate terms
```

CreditEngine does not read underlying token custody. The vault remains the
custody/accounting authority; CreditEngine consumes the canonical amount
reported through the existing Vault interface.

The complete relevant flow is:

1. BasicVault returns `(empty address, 0)` for a genuinely empty index and
   `(asset, 0)` when a nominal position exists but backing is unusable
   ([`BasicVault.vy:133-146`](../../../../contracts/vaults/modules/BasicVault.vy#L133-L146)).
2. CreditEngine reads the pair, skips only the empty address, loads terms,
   still excludes configured LTV zero, bypasses PriceDesk for amount zero, and
   calculates value, capacity, fallback weight, and aggregates
   ([`CreditEngine.vy:727-786`](../../../../contracts/core/CreditEngine.vy#L727-L786)).
3. The read itself writes neither collateral nor user debt. Health views use
   the computed `totalMaxDebt`, collateral value, and retained thresholds
   ([`CreditEngine.vy:920-979`](../../../../contracts/core/CreditEngine.vy#L920-L979)).
4. A caller must explicitly invoke Teller's liquidation entry; Teller pause
   and transaction guards still apply
   ([`Teller.vy:551-561`](../../../../contracts/core/Teller.vy#L551-L561)).
5. AuctionHouse requires Teller authority, an unpaused Department, enabled
   liquidation configuration, a non-Earn-vault user, nonzero debt, no existing
   liquidation, a nonzero threshold, and the threshold inequality before
   setting the in-memory liquidation flag
   ([`AuctionHouse.vy:231-247`](../../../../contracts/core/AuctionHouse.vy#L231-L247),
   [`AuctionHouse.vy:283-320`](../../../../contracts/core/AuctionHouse.vy#L283-L320)).
6. Liquidation phases run, debt is updated, and auctions are created only if
   health was not restored
   ([`AuctionHouse.vy:351-375`](../../../../contracts/core/AuctionHouse.vy#L351-L375),
   [`AuctionHouse.vy:789-807`](../../../../contracts/core/AuctionHouse.vy#L789-L807)).
7. Auction creation is not settlement. Under a continuing BasicVault deficit,
   the deficient purchase returns zero before nominal movement while a batch
   preserves earlier healthy purchases
   ([`test_basic_vault_safety.py:1216-1337`](../../../../tests/vaults/test_basic_vault_safety.py#L1216-L1337)).

## Why this was selected

| Alternative | Benefit | Failure or dead end |
| --- | --- | --- |
| Keep skipping `(asset, 0)` | Smallest source footprint | Unsafe debt can lose all resolution terms and appear non-liquidatable |
| Retain zero value but omit liquidation terms | Avoids term influence | Preserves the same non-actionable-debt failure |
| Make the vault revert | Makes the failure conspicuous | Can block debt-health views and repayment, including healthy co-collateral paths |
| Rely on configuration or operator shutdown | Avoids CreditEngine source change | Cannot preserve existing debt terms after backing loss |
| Omit Stock Tokens | Lowest technical risk | Rejected as the initial product disposition |
| Add complete settlement and bad-debt resolution | Could close the lifecycle | Much larger accounting, storage, migration, auction, and policy change |

The integrated change was the smallest generic source correction that kept
zero capacity, repayment, and debt-resolution visibility without adding raw
token reads, configuration fields, interfaces, or a repayment mode.

## Debt-health and liquidation behavior

For a nonempty zero-backed position:

- `collateralVal` contributes zero;
- `totalMaxDebt` contributes zero;
- PriceDesk is not called for the zero amount;
- nonzero configured liquidation and redemption terms remain;
- interest/rate terms remain;
- the account may become immediately eligible when debt-health is next
  calculated.

"Immediately liquidatable" means immediately computed eligibility, not an
automatic state transition.

An explicit authorized transaction must still pass through Teller and
AuctionHouse. Pause, configuration, caller, user, debt, threshold, vault, and
existing-liquidation gates still apply. Auction creation is separate from
auction purchase, and purchase is separate from successful collateral
delivery.

For BasicVault under a continuing deficit, AuctionHouse returns zero for the
affected purchase. A single Teller purchase then reverts with no GREEN spent;
a batch preserves earlier healthy rows and skips the deficient row. Eligibility
therefore does not imply successful settlement or bad-debt resolution.

## Scenario summary

| Scenario | Value/capacity | Terms | Eligibility |
| --- | --- | --- | --- |
| True empty `(empty, 0)` | Zero | Omitted | No position |
| Nonempty zero-backed asset, no debt | Zero | Retained | No liquidation because debt is zero |
| Nonempty zero-backed asset, debt, nonzero threshold | Zero | Retained | Liquidatable when the threshold inequality is satisfied |
| LTV-zero asset | Zero | Omitted | Excluded as before |
| Healthy co-collateral sufficient | Healthy value/capacity retained | Mixed terms | Account can remain healthy |
| Healthy co-collateral insufficient | Healthy value only | Mixed terms | Can become liquidatable |
| Partial aggregate backing deficit in BasicVault | Zero for the affected asset | Retained | Same fail-closed treatment as total deficit |
| Reverting or ABI-invalid typed `balanceOf` | View reverts | No terms returned by that call | Fail-closed, but not soft-zero containment |
| Nonzero amount with missing oracle price | Existing PriceDesk behavior | Depends on raising mode | Not changed by the zero-amount correction |

## Owner-parked research findings and one established null result

The first two subsections are accurate technical observations, but the owner
has parked their policy disposition. They are not planned work, source-change
authorization, or current Wave 1 blockers.

### Cross-asset `lowestLtv` — owner-parked

Fallback weight `1` prevents division by zero and retains configured weighted
terms. Against 18-decimal healthy capacity, its effect on weighted averages is
normally negligible.

For healthy aggregate weight `W` and a raw term difference `delta`, roughly
`W / (delta - 1)` zero-weight entries are required to move a floored weighted
term by one raw unit. Comparable total weight would require roughly `W`
entries. Those counts are operationally infeasible for ordinary accounts.

`lowestLtv` is different: it is not weighted. One zero-backed lower-LTV asset
can set the account-wide target used by the two reviewed-snapshot AuctionHouse
sites
([`AuctionHouse.vy:351`](../../../../contracts/core/AuctionHouse.vy#L351),
[`AuctionHouse.vy:1340`](../../../../contracts/core/AuctionHouse.vy#L1340)),
the two CreditRedeem sites
([`CreditRedeem.vy:226`](../../../../contracts/core/CreditRedeem.vy#L226),
[`CreditRedeem.vy:322`](../../../../contracts/core/CreditRedeem.vy#L322)), and
the two integrated-baseline Deleverage sites
([`Deleverage.vy:628`](../../../../contracts/core/Deleverage.vy#L628),
[`Deleverage.vy:1006`](../../../../contracts/core/Deleverage.vy#L1006)).

In a mixed account, the zero-backed asset can therefore increase the healthy
collateral or debt targeted by those mechanisms. Disabling redemption for the
Stock asset prevents direct redemption of Stock; it does not remove the Stock
position from the account-wide terms used while redeeming another enabled
asset. Trusted Deleverage bypasses the lowest-LTV cap; the untrusted path does
not.

The previously suggested change to exclude zero-capacity collateral from
`lowestLtv` is an **agent research proposal, not owner-approved**. It is parked.
This document does not recommend, schedule, or authorize that source change.
The Deleverage references above describe integrated current source behavior;
the later Stock composition tests were also inspected for the package rebind.

### Interest treatment — owner-parked

Interest first accrues from the debt terms already stored on the user's debt.
After the next state-changing debt-term refresh:

- old zero-skip behavior stored a zero borrow rate if the skipped zero-backed
  asset was the only position;
- current behavior stores the retained configured rate.

Interest therefore continues after that refresh on sole-position unbacked debt.
That continuation is attributable to this change rather than inherited
behavior. Whether to retain, stop, or otherwise classify interest after
confirmed loss is owner-parked research; no change is authorized.

### Withdrawal-limit null result — integrated analysis

`getMaxWithdrawableForAsset` uses:

- the selected asset's own LTV;
- collateral value excluding that asset; and
- total maximum debt excluding that asset.

A zero-backed other asset contributes zero to the last two values, so the
successful numeric withdrawal-limit result is unchanged. The path reads only
the selected asset's own LTV plus the other positions' collateral value and
maximum debt
([`CreditEngine.vy:1246-1283`](../../../../contracts/core/CreditEngine.vy#L1246-L1283));
it does not consume the other positions' weighted terms or `lowestLtv`.

The path is not byte-for-byte inert: CreditEngine now loads the zero-backed
asset's debt configuration and performs aggregation, adding gas and a
configuration-call failure surface. That dependency surface lacks a dedicated
targeted test.

## Test-to-invariant matrix

The status “independently reproduced” below refers to the prior read-only audit
at the reviewed `rh` snapshot. This documentation-only revision did not rerun
tests.

| Primary test evidence | Invariant proved | Path and mutation sensitivity | Known limit |
| --- | --- | --- | --- |
| [`test_unsafe_backing_failures_keep_terms_with_zero_capacity`, lines 327-417](../../../../tests/core/creditEngine/test_stock_backing.py#L327-L417) | Deficit, missing, failed, and malformed backing yield zero value/capacity while all configured terms remain and debt becomes unhealthy/liquidatable | Synthetic vault plus real CreditEngine; reintroducing the `amount == 0` skip or pricing the unsafe asset fails the assertions | Does not prove live token truth or settlement |
| [`test_true_zero_nominal_position_remains_absent`, lines 420-466](../../../../tests/core/creditEngine/test_stock_backing.py#L420-L466) | `(empty address, 0)` remains absent with zero terms | Synthetic true-empty producer; merging empty and nonempty zero handling fails | Does not enumerate every legacy vault |
| [`test_safe_backing_surplus_values_only_nominal_user_amount`, lines 469-512](../../../../tests/core/creditEngine/test_stock_backing.py#L469-L512) | Surplus does not create extra user value or capacity | Synthetic backing observer plus real pricing/CreditEngine | Vault, not CreditEngine, owns surplus policy |
| [`test_mixed_safe_collateral_remains_exact_and_liquidatable`, lines 515-602](../../../../tests/core/creditEngine/test_stock_backing.py#L515-L602) | Healthy co-collateral remains priced; unsafe zero amount is not priced; preview, health, and stored refresh agree | Real ordinary deposit plus synthetic unsafe vault and a PriceDesk that reverts if the unsafe asset is queried | Uses homogeneous terms; does not cover parked heterogeneous `lowestLtv` research |
| [`test_backing_observation_mutation_fails_closed`, lines 638-687](../../../../tests/core/creditEngine/test_stock_backing.py#L638-L687) | A position can move from safe to failed observation without stale positive capacity | Runtime mutation of the observer plus real CreditEngine | Proves current observation, not a malicious truthful-looking report |
| [`test_get_user_borrow_terms_asset_with_zero_amount`, lines 1208-1252](../../../../tests/core/creditEngine/test_credit_borrow.py#L1208-L1252) | A real SharesVault total-loss `(asset, 0)` retains terms with zero capacity | Integrated Rebase/SharesVault path | Not the BasicVault custody classifier |
| [`test_repay_uses_safe_collateral_without_pricing_zero_amount_position`, lines 803-896](../../../../tests/core/creditEngine/test_credit_repay.py#L803-L896) | Repayment stays live with healthy collateral and an unsafe zero-amount position | Real borrow/repay; replacement PriceDesk reverts on any unsafe-asset lookup | Does not decide parked post-loss interest policy |
| [`test_auction_started_after_total_issuer_loss`, lines 1606-1695](../../../../tests/vaults/test_stock_token_vault_comparison.py#L1606-L1695) | Eligibility can become an actual liquidation transaction and auction; failed later purchase rolls back GREEN/debt/state | Real Teller, AuctionHouse, Ledger, CreditEngine, token control, and legacy comparison vault | Settlement behavior remains vault-specific |
| [`test_real_teller_batch_later_deficit_preserves_earlier_healthy_row`, lines 1216-1337](../../../../tests/vaults/test_basic_vault_safety.py#L1216-L1337) | A later deficient BasicVault row returns zero while earlier healthy batch purchases, debt repayment, GREEN spend, balances, and events are preserved | Real Teller batch and integrated contracts | Proves per-row containment, not a future loss-resolution policy |
| [`test_zero_amount_containment_path_has_bounded_gas`, lines 690-739](../../../../tests/core/creditEngine/test_stock_backing.py#L690-L739) | One zero path is cheaper than its priced comparator and below an arbitrary one-million-gas smoke ceiling | One synthetic position | Not a scalability, block-budget, or marginal-per-position bound |

The suite is strongly mutation-sensitive to the two core properties: retaining
terms for `(asset, 0)` and skipping its oracle call. It is not mutation-complete
for every downstream term consumer. Known gaps are classified later rather
than converted into unapproved implementation work.

## ABI, storage, runtime, gas, migration, and compatibility

| Surface | Reviewed result |
| --- | --- |
| Source delta | Four additions/four deletions; six functional changed lines plus two blank-line deletions |
| Compiler | `Vyper 0.4.3+commit.bff19ea2` |
| ABI | 51 functions, six events, one constructor |
| ABI identity | Git blob `29232f8fb95b78a488a617e2d4efb664bc5b4562` at the implementation parent, implementation commit, and reviewed `rh` |
| Constructor | Unchanged: one `_ripeHq: address` input |
| Selectors/events/interfaces | Unchanged |
| Persistent storage | Unchanged; the diff adds no state declaration or write |
| Reviewed deployed runtime | 24,132 bytes |
| EIP-170 headroom | 444 bytes |
| Gas evidence | One-position smoke comparison only; no measured scaling bound |
| Migration/deployment | Source integration deploys nothing; only a deployment or upgrade using this source gains the behavior |
| Existing Base | Existing deployed bytecode and state did not change automatically |

Because runtime headroom is small, any future CreditEngine source edit requires
fresh pinned-compiler size, ABI, selector, event, constructor, and storage
comparison. That is a compatibility gate, not authorization to edit the
contract.

## Residual risks and trust assumptions

| Finding | Classification | Present consequence | Current disposition |
| --- | --- | --- | --- |
| Sudden eligibility and no automatic grace period | Accepted residual risk / operational concern | A public liquidation call may become eligible as soon as the vault reports zero and debt crosses the retained threshold | Preserve accurate monitoring and transaction-sequence documentation; no grace-period change is authorized |
| Cross-asset `lowestLtv` | Owner-parked research | One zero-backed lower-LTV position can affect account-wide liquidation, redemption, and untrusted-deleverage targets in a mixed account | No source change or test expansion is currently authorized |
| Continued interest after refresh | Owner-parked research and direct M3 behavior | A sole zero-backed position retains its configured rate after the next debt-term refresh | Eventual policy disposition undecided |
| Settlement, loss allocation, and bad debt | Owner-parked product policy | Eligibility and auction creation do not guarantee deliverable collateral or liability resolution | Not a current Wave 1 item or blocker; parking does not decide release disposition |
| Erroneous or malicious `(asset, 0)` report | Trust assumption / accepted residual | CreditEngine correctly trusts the selected Vault and can remove capacity or trigger eligibility on a false report | Vault admission, artifact binding, and monitoring remain required |
| Fallback weight `1` | Accepted arithmetic residual | Weighted terms can move only after an operationally infeasible number of ordinary 18-decimal zero-capacity entries; `lowestLtv` is the separate one-entry asymmetry | No active change |
| Withdrawal dependency surface | Later integrated regression | C1 pins the successful numeric null and debt-configuration failure surface | Preserve current regression |
| Many-position gas | Later integrated measurement protocol | C2 records marginal gas across configured position counts; it is local evidence, not a chain fee guarantee | Re-measure at release snapshot |
| Oracle bypass | Integrated safety property | Zero amount is deliberately not priced; a nonzero amount with an unavailable price retains pre-existing PriceDesk behavior | Preserve and regression-test |

CreditEngine assumes that the selected Vault reports position identity and
amount according to its reviewed policy, MissionControl returns the intended
terms, and downstream callers use the returned fields with their documented
semantics. It does not prove underlying token truth, custody recovery, auction
delivery, or loss allocation. The correct description is **debt-health
containment**, not complete zero-backing resolution.

## Next actions

### Currently required

These are deployment or release gates around the integrated source; they are
not authorization to edit CreditEngine:

1. Bind the exact release commit/tree, CreditEngine source, pinned compiler and
   settings, ABI, constructor input, creation artifact, deployed runtime, and
   registry/configuration identities.
2. At the eventual release snapshot, rerun the focused CreditEngine and
   composed vault/liquidation tests applicable to the enabled asset and record
   failures, skips, xfails, environment, and exact commands.
3. Prove that the enabled vault supplies the reviewed `(empty, 0)` versus
   `(asset, 0)` semantics and that asset terms, auction posture, and borrowing
   posture match the approved deployment configuration.
4. Monitor backing-observation failures, custody deficits, sudden health
   transitions, liquidation/auction entry, and settlement reverts; maintain a
   pause/escalation/recovery runbook.
5. Keep operator-facing documentation explicit that eligibility, liquidation
   state, auction creation, purchase, delivery, and bad-debt recognition are
   separate transitions.

Current H-04 and M4 evidence is reflected only for its exact integrated scope;
it does not authorize deployment, configuration, CCIP, or further Deleverage
work.

### Recommended hardening

These are **agent recommendations, not owner-approved requirements**:

1. Retain the integrated C1 `getMaxWithdrawableForAsset` regression and C2
   marginal-gas protocol.
2. Add change-triggered CI that records CreditEngine ABI/blob identity,
   selectors, events, constructor, persistent layout, runtime size/headroom,
   focused tests, and the exact compiler/tool versions.
3. Retain mutation checks that fail if `(asset, 0)` is skipped again or if a
   zero amount reaches PriceDesk.

### Parked by owner

The following are accurate research subjects but not current work items,
current Wave 1 blockers, or authorized source/test changes:

- whether zero-capacity collateral should participate in account-wide
  `lowestLtv`, including tests across its six reviewed-baseline consumers;
- whether interest should continue, stop, or transition after confirmed
  backing loss;
- grace periods, recapitalization, settlement, restoration, loss allocation,
  and exactly-once bad-debt accounting;
- further Deleverage work beyond the integrated source and composition
  evidence; and
- every CCIP workflow.

Parking does not approve the present behavior forever and does not decide an
eventual release disposition. The owner must explicitly reopen a subject
before it becomes an implementation or release assignment.

### Explicitly not recommended

- Do not restore the old `amount == 0` skip.
- Do not call PriceDesk for a zero amount.
- Do not add a second raw custody reader to CreditEngine.
- Do not make debt-health evaluation revert merely because one vault reports
  unsafe or unknown backing.
- Do not present a `lowestLtv`, interest, settlement, or bad-debt proposal as
  planned work while it remains parked.
- Do not change the reviewed source solely to restore the two deleted blank
  lines.
- Do not describe source integration as deployment, activation, successful
  settlement, or complete loss resolution.

## Historical versus current validation evidence

| Evidence class | Snapshot and result | Disposition |
| --- | --- | --- |
| Historical implementation seal | `40 + 19 + 10 = 69 passed` across `test_credit_borrow.py`, `test_credit_repay.py`, and `test_stock_backing.py` | Preserve as historical. The phrase “five M3-owned files: 69 passed” was inaccurate: the contract contributes no tests and the 92-case comparison file was not included. |
| Historical complete CreditEngine | `163 passed` | Historical implementation evidence; later independently reproduced at the reviewed snapshot |
| Historical complete serial suite | `3,214 passed, 142 deselected`, zero failures/skips/xfails | Historical only; neither the prior read-only audit nor this documentation revision reran the full suite |
| Independently reproduced at reviewed `rh` | Collections: borrow `40`, repay `19`, stock backing `10`, comparison `92`, Guarded `55`; complete CreditEngine `163` | Exact reviewed-snapshot collection |
| Independently reproduced at reviewed `rh` | Complete CreditEngine `163 passed`; comparison plus Guarded `147 passed`; `310` unique focused cases total | Zero failures, skips, or xfails; commands below |
| This harmonization revision | No behavioral tests or compiler run | Documentation validation only, as bounded by the owner |

No historical S2 count is presented as a current CreditEngine result, and no
full-suite result is described as independently rerun when it was not.

## Primary source links and reproducible commands

Primary repository evidence:

- [`CreditEngine.vy`](../../../../contracts/core/CreditEngine.vy)
- [`BasicVault.vy`](../../../../contracts/vaults/modules/BasicVault.vy)
- [`test_stock_backing.py`](../../../../tests/core/creditEngine/test_stock_backing.py)
- [`test_credit_borrow.py`](../../../../tests/core/creditEngine/test_credit_borrow.py)
- [`test_credit_repay.py`](../../../../tests/core/creditEngine/test_credit_repay.py)
- [`test_stock_token_vault_comparison.py`](../../../../tests/vaults/test_stock_token_vault_comparison.py)
- [`test_basic_vault_safety.py`](../../../../tests/vaults/test_basic_vault_safety.py)
- [`minimal-contract-change-reassessment.md`](../minimal-contract-change-reassessment.md#L249-L305)
- [`stock-token-vault-change-validation-plan.md`](../stock-token-vault-change-validation-plan.md#L2152-L2167)
- [`stock-token-vault-fix-recommendations.md`](../stock-token-vault-fix-recommendations.md#L181-L225)

Snapshot, ancestry, exact delta, and ABI identity:

```text
git rev-parse 'refs/heads/rh^{commit}' 'refs/heads/rh^{tree}'
git rev-parse 'refs/remotes/origin/rh^{commit}' \
  'refs/remotes/origin/rh^{tree}'
git merge-base --is-ancestor \
  4c26d7d73bb02f7eae2e5df02314db77a426aced \
  cca60bb85c772c977bb9fb62c1c6c5252c3a1438
git diff --numstat \
  4c26d7d73bb02f7eae2e5df02314db77a426aced^ \
  4c26d7d73bb02f7eae2e5df02314db77a426aced \
  -- contracts/core/CreditEngine.vy
git diff --unified=20 \
  4c26d7d73bb02f7eae2e5df02314db77a426aced^ \
  4c26d7d73bb02f7eae2e5df02314db77a426aced \
  -- contracts/core/CreditEngine.vy
shasum -a 256 contracts/core/CreditEngine.vy
git hash-object scripts/abis/CreditEngine.json
git rev-parse \
  e39815d710ecfaf8bbeea54cabe8ae8d553a2740:scripts/abis/CreditEngine.json \
  4c26d7d73bb02f7eae2e5df02314db77a426aced:scripts/abis/CreditEngine.json \
  cca60bb85c772c977bb9fb62c1c6c5252c3a1438:scripts/abis/CreditEngine.json
```

Pinned-compiler artifact reproduction:

```text
vyper --version
vyper -p . -f abi,layout,bytecode,bytecode_runtime \
  contracts/core/CreditEngine.vy
```

The prior independent snapshot reproduction created a private temporary root
with:

```text
mktemp -d /tmp/ripe-m3-audit.XXXXXX
chmod 700 /tmp/ripe-m3-audit.V2mDuB
mkdir -m 700 \
  /tmp/ripe-m3-audit.V2mDuB/boa \
  /tmp/ripe-m3-audit.V2mDuB/xdg \
  /tmp/ripe-m3-audit.V2mDuB/hypothesis
```

It then used these exact focused execution commands. The placeholder API values
were non-secret import-time configuration; no external RPC or fork was used:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
ETHERSCAN_API_KEY=local-placeholder \
WEB3_ALCHEMY_API_KEY=local-placeholder \
XDG_CACHE_HOME=/tmp/ripe-m3-audit.V2mDuB/xdg \
HYPOTHESIS_STORAGE_DIRECTORY=/tmp/ripe-m3-audit.V2mDuB/hypothesis \
RIPE_AUDIT_CACHE=/tmp/ripe-m3-audit.V2mDuB/boa \
python -c 'import os, sys; from boa.interpret import set_cache_dir; set_cache_dir(os.environ["RIPE_AUDIT_CACHE"]); import pytest; raise SystemExit(pytest.main(sys.argv[1:]))' \
-p no:cacheprovider \
--basetemp /tmp/ripe-m3-audit.V2mDuB/run-credit-escalated \
-q -ra tests/core/creditEngine

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
ETHERSCAN_API_KEY=local-placeholder \
WEB3_ALCHEMY_API_KEY=local-placeholder \
XDG_CACHE_HOME=/tmp/ripe-m3-audit.V2mDuB/xdg \
HYPOTHESIS_STORAGE_DIRECTORY=/tmp/ripe-m3-audit.V2mDuB/hypothesis \
RIPE_AUDIT_CACHE=/tmp/ripe-m3-audit.V2mDuB/boa \
python -c 'import os, sys; from boa.interpret import set_cache_dir; set_cache_dir(os.environ["RIPE_AUDIT_CACHE"]); import pytest; raise SystemExit(pytest.main(sys.argv[1:]))' \
-p no:cacheprovider \
--basetemp /tmp/ripe-m3-audit.V2mDuB/run-vaults \
-q -ra \
tests/vaults/test_stock_token_vault_comparison.py \
tests/vaults/test_basic_vault_safety.py
```

Those test commands require the local session fixture to bind an ephemeral
host port. That harness permission was granted for the reproduced runs; it did
not authorize or perform network-backed protocol access.
