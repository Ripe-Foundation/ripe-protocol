# Implement Base legacy-vault compatibility

Revision 6, September 19, 2026. Implement the contract changes and focused tests below. This document is the complete instruction for an agent with no prior context. Release qualification and earlier reviews are separate background, not required reading, prerequisites or deliverables.

New Base departments must work with retained Stability Pool 1 and RipeGov 2. Keep one shared source that also supports modern vaults. Implement VaultBook read helpers, AuctionHouse readiness, Deleverage traversal, and Alpha/Charlie structural validation. Preserve borrowing-collateral exclusion, authorized value-moving callers, accounting and settlement checks. Do not change VaultBook's replacement validator, PriceDesk, the immutable legacy vaults, migration policy or release configuration.

## Finish the task without intermediate review

The owner will review at the end. Continue through setup, implementation, focused validation, fixes and a local commit in one task. These are work steps, not approval checkpoints. Do not stop after a plan, prototype, individual contract, test failure or status update, and do not wait for an answer to a routine implementation question. Choose the smallest correct solution within this specification, repair relevant failures and continue. Save nonessential questions and tradeoffs for the final response; the deferred release choices do not block this work.

Preserve the specified behavior and scope. If a genuine environment restriction or unresolved contract constraint prevents part of the task, try reasonable in-scope alternatives and complete all independent work; report the exact remaining constraint at the end without claiming that an incomplete result passed. Tool permission requirements still apply. No implementation step requires owner review before the next step.

Use neutral, precise descriptions such as “boundary-case coverage,” “authorization consistency,” “state consistency” and “settlement consistency.” Preserve the actual assertions, expected reverts and existing identifiers; this is a wording preference, not reduced test coverage.

## Worktree and scope

The dedicated worktree is already prepared at `../ripe-protocol-legacy-vault-compat`, on branch `codex/base-legacy-vault-compat`, initially at the frozen commit below. The current prompt and two fixture-evidence JSON files are already copied there. Verify before editing; do not create it again. Only if this prepared worktree is absent in the execution environment, create it with:

```sh
git -C ../ripe-protocol worktree add -b codex/base-legacy-vault-compat ../ripe-protocol-legacy-vault-compat bdf7f3da7113aabde60ab8eceab6a960a841bb88
```

Before the first edit, run `git rev-parse --show-toplevel`, `git branch --show-current`, `git rev-parse HEAD` and `git status --short` in the dedicated worktree. Verify the expected root/branch and initial baseline, or documented task commits descending from it when resuming. Run repository commands with that explicit working directory and resolve absolute edit paths from the verified worktree root. Keep every repository edit there; do not switch or edit the main checkout, reset existing work, remove other worktrees or move this task under `/private/tmp`. If a filesystem restriction occurs, use the normal tool permission mechanism; never work around it by changing the main checkout. The supplied prompt/evidence are expected untracked task inputs, not unrecognized implementation changes.

The baseline is `bdf7f3da7113aabde60ab8eceab6a960a841bb88`, from `codex/base-upgrade-fork-rehearsal`. Build on that pin; no remote/PR refresh, live RPC survey, release planning or full-suite run is required. Fixture inputs live in `docs/chains/base/legacy-vault-phase-1-planning-evidence/` within this worktree: `source-authentication.block-51532106.json` and `readback.block-51532106.json`. If recovering missing copies, their original source is `../ripe-protocol/docs/chains/base/legacy-vault-phase-1-planning-evidence/`; read it without editing it. Earlier prompts/operational documents do not add work to this task.

Production scope is these five files, plus necessary interface declarations:

- `contracts/registries/VaultBook.vy`
- `contracts/core/AuctionHouse.vy`
- `contracts/core/Deleverage.vy`
- `contracts/config/SwitchboardAlpha.vy`
- `contracts/config/SwitchboardCharlie.vy`

Also update related test fixtures/tests, measured runtime pins and generated `scripts/abis/`. VaultBook's direct constructor consumers include `vault_book_deploy` in `tests/conf_core.py` and the local rehearsal deployment in `scripts/base_upgrade_fork.py` near line 737 at the pin. Update necessary constructor arguments there; keep the latter change limited to test-harness compatibility. Search for additional direct consumers rather than editing unrelated deployment files. Historical migrations, recorded deployment manifests and live Robinhood artifacts stay untouched. Commit the scoped implementation locally on the named branch after validation; do not push, open a PR or deploy. Stage explicit scoped paths, including necessary test-harness constructor changes, not all untracked files; the provided prompt/evidence may remain untracked task inputs.

## Fixture and size check first

Use historical commit `d0957e497261a52e7a7b460eb986a6e9fb27f051` for the real legacy StabilityPool/VaultData behavior. Existing `source-authentication.block-51532106.json` and `readback.block-51532106.json` in the evidence directory authenticate all five retained runtimes. Pool 1 is `0x2a157096af6337b2b4bd47de435520572ed5a439`, bound to canonical HQ `0x6162df1b329E157479F8f1407E888260E0EC3d2b`. Vyper `0.4.3+commit.bff19ea2`, default gas optimization/Prague, reproduces the historical runtime plus one 32-byte HQ immutable. Use this evidence; no new live census or RPC authentication campaign is required.

Build a deterministic ordinary-test fixture from the minimal historical source/dependency closure or an authenticated fixture artifact, retaining provenance. The fixture must preserve real share/NAV behavior and missing selectors; do not add modern methods to the old pool. A fixture may bind a local test HQ; account for that explicit immutable substitution when comparing runtime. Deploy on Base chain ID using `boa.env.evm.patch.chain_id = 8453`, and restore the prior chain ID after each scoped test. Test a non-Base chain separately. Keep fixture setup local and network-independent.

Compile the minimal shared-helper/caller prototype before expanding the patch. Use the pinned Vyper/Titanoboa versions (`0.4.3`/`0.2.7`) and repository optimization pragmas; count the complete deployed code including immutables:

| Contract | Baseline deployed bytes | Space under 24,576 | Reviewer caller probe |
| --- | ---: | ---: | --- |
| AuctionHouse | 24,564 | 12 | Three-argument helper call: 24,565 |
| Deleverage | 24,559 | 17 | Whole traversal relocation: about 24,430 |
| VaultBook | 14,410 | 10,166 | Remeasure complete helpers and new immutable |

These probes are expectations, not final sizes. An extra address immutable costs 32 bytes, so keep legacy identity in VaultBook rather than either tight caller. Update exact expected sizes in `tests/test_vault_pointer_runtime_sizes.py` from actual intentional changes, including Alpha/Charlie, without weakening its 24,576-byte ceiling. Resolve size pressure with focused equivalent refactors inside the stated contract scope and remeasure; do not wait for prototype approval. Preserve the selected shared-source design and all specified checks. If it still cannot fit, finish unaffected work and report the measured remaining constraint/options in the final response; do not remove checks, exceed the limit or silently introduce a new architecture.

## VaultBook helpers and identity

Add an immutable constructor parameter `_legacyPool` and these external view functions, with matching consumer interfaces:

```vyper
interface VaultBookCompatibility:
    def canAcceptLiquidationAsset(_vaultAddr: address, _stabAsset: address, _claimAsset: address) -> bool: view
    def getDeleverageTraversalAsset(_user: address, _vaultAddr: address, _index: uint256, _isStabVault: bool) -> (address, uint256): view
    def hasStabilityPoolInterface(_vaultAddr: address, _stabAsset: address, _probeClaimAsset: address) -> bool: view
```

Zero binding disables legacy support and is used by existing modern fixtures. A nonzero binding requires `chain.id == 8453`, a contract with the required legacy getters, and `getRipeHq()` equal to VaultBook's HQ constructor input. HQ identity and chain need no repeated runtime check. Classify the nonzero bound legacy address **first**, then require `getRegId(address) == 1`, `getAddr(1) == address` and `isValidRegId(1)`. Invalid legacy registration returns `False` from boolean helpers and `(empty(address), 0)` from traversal; never fall through to a missing modern selector. No failed call or matching codehash may classify some other address as legacy.

For other addresses, readiness forwards the modern pool's two-argument call unchanged, including its boolean/revert behavior. Traversal preserves the full existing Deleverage dispatch: modern stability vaults use `getUserAssetAndAmountAtIndex`; ordinary vaults use `getUserAssetAtIndexAndHasBalance` and return the existing 1/0 presence marker. Do not add a registry-membership prerequisite to those modern/ordinary forwarding paths. A legacy address is recognized before `_isStabVault`; test fixtures must still configure MissionControl ID 1 as a stability vault because downstream accounting uses that classification.

Structural support is independent of readiness. On a modern pool, the structural helper calls `canAcceptLiquidationAsset(stabAsset, probeClaimAsset)` and returns `True` after successful decoding even if the decoded value is `False`; missing or unexpected methods still fail. On verified legacy Pool 1, successfully decode `indexOfAsset(stabAsset)`, `claimableBalances(stabAsset, probeClaimAsset)`, `totalClaimableBalances(stabAsset)` and `isPaused()`, then return `True`. Zero values and paused/empty pools do not negate interface support; caller policy checks still apply.

Keep helpers read-only. AuctionHouse still directly swaps with the original pool; Deleverage still uses the AuctionHouse withdrawal bridge; Teller still directly deposits/withdraws. Add no custody, wrapper vault, delegatecall or forwarded value-moving caller.

## Deleverage and caller changes

Move the **entire** `_getBroadTraversalAsset` dispatch from Deleverage into VaultBook, remove the superseded caller branch and update all consumers, including `getDeleverageInfo`. For the legacy branch:

1. Discover the asset/presence with `getUserAssetAtIndexAndHasBalance`; preserve empty/zero results when absent.
2. If paused, or raw stabilization-token custody is less than or equal to `totalClaimableBalances(asset)`, return `(asset, 0)` before strict NAV valuation.
3. Otherwise return `(asset, getTotalAmountForUser(user, asset))`. This is a monetary amount, **never marker 1**. Preserve legitimate rounding/zero/reverts; do not cap NAV to cash or add an arbitrary dust threshold.

`_getDeleverageInfo` uses stability amounts directly for maximum repayment and weighted LTV. Ordinary vaults retain their marker because their real amount is fetched afterward. Legacy NAV can include claims and exceed immediately withdrawable cash; assert actual tokens/payment/debt changes separately. Positive-custody legacy NAV retains its strict pricing failures; modern health behavior remains unchanged.

Route AuctionHouse's readiness call through VaultBook's three-argument helper. Leave AuctionHouse position traversal unchanged under the retained configuration: LP has `shouldTransferToEndaoment = True`, sGREEN has `shouldBurnAsPayment = True`, and AuctionHouse skips those positions after enumeration. Test that source/configuration condition and prove actual Pool-1 repayment through Deleverage; AuctionHouse does not invoke it automatically. If a concrete supported fixture exposes an actionable missed AuctionHouse position, reproduce it and measure any necessary traversal fix together with the readiness patch. Do not expand that caller for a hypothetical route.

## Legacy liquidation readiness without claim enumeration

Implement these checks only for the authenticated legacy branch; modern readiness forwards unchanged:

| Check | Required legacy behavior |
| --- | --- |
| Identity, pause and assets | Reject invalid binding/registration, paused pool, unregistered stabilization asset, zero incoming collateral or incoming collateral already registered as a pool deposit asset. |
| Stabilization reservations | Reject when `totalClaimableBalances(stabAsset) != 0`, before either payment path. |
| Selected cohort's GREEN claim | If positive, require actual pool GREEN custody to cover **aggregate** `totalClaimableBalances(GREEN)` across all cohorts. Otherwise reject this pool/stability-asset pair before collateral moves. With no GREEN claim in this cohort, impose no GREEN-custody requirement. |
| Positive stabilization custody | Require a non-raising, positive USD value for that actual spendable amount, preserving existing GREEN/sGREEN conversions and LP PriceDesk semantics. A zero LP price returns `False`, allowing next-pair/auction fallback before the caller's raising quote. Apply this gate even if the cohort also has GREEN claims, because a residual normal-token payment can follow. |
| Zero stabilization custody | Allow a positive, fully backed GREEN claim when the preceding checks pass. Otherwise return `False`. An unfunded empty cohort is unavailable; donated spendable custody can pass the ordinary price check. |
| Non-GREEN claims, claim counts and NAV | Do **not** enumerate, value or check aggregate backing for unrelated claims; do not recompute cohort NAV or its inverse conversion. Do not impose the modern 20-active-claim cap. |

This removes revision 4's full claim-health scan. The legacy swap records incoming collateral and spends stabilization tokens or GREEN; neither swap entry point values or pays existing non-GREEN claims. Unrelated claim health therefore must not add an unbounded eligibility loop to this helper. Its call count is bounded independently of those claims; oracle cost can still vary. Strict legacy NAV/ordinary user-flow pricing is unchanged and must still be tested. Readiness is permission to attempt the selected swap, not certification of the cohort's entire balance sheet.

Keep AuctionHouse's sizing and exact settlement check `abs(paid - requestedGreen) <= requestedGreen // 100`. The legacy pool's `min(requested, cohortGreenClaim, actualGreenCustody)` payment is not automatically acceptable to that caller. The aggregate backing gate deliberately rejects some small swaps that the old tolerance might have accepted; implement this conservative fallback without adding partial-payment sizing. Do not catch arbitrary PriceDesk failures or alter its funding protection: use its normal zero-price boundary and preserve actual reverts/rollback.

## Alpha and Charlie

Replace only their missing readiness-interface probes with `hasStabilityPoolInterface`. Alpha preserves registry/support/contract/pause checks and its zero-address probe argument. Charlie preserves nonzero/different candidate, registry/contract, sGREEN support, `vaultAssets(1)`, reservation and pause checks, using its existing sGREEN/sGREEN probe arguments. Test proposal and execution separately, including a structurally valid empty pool. Do not broaden governor permissions or change timelocks. No Switchboard registry deployment/setup work is needed in this task.

## Focused tests and completion

Put new ordinary tests in `tests/registries/test_vault_book_legacy_compat.py` (shared helpers/identity) and `tests/core/test_base_legacy_vault_compat.py` (composed legacy flows), reusing existing affected test modules when that is clearer. The focused run must cover:

- Constructor Base/non-Base and zero/nonzero bindings; wrong HQ/ID/address; invalid legacy row; unchanged modern forwarding and missing or unexpected methods; valid empty/paused structural probes.
- Real legacy NAV returned instead of 1; paused/cash-empty broad traversal skips without calling withdrawal and lets `deleverageManyUsers` process another eligible user, preserving skipped shares/claims. Explicit-asset/direct-getter paths that bypass the helper retain separately asserted behavior.
- A borrower withdrawing **positive-LTV ordinary collateral in vault 3** while holding Pool-1 assets: assert maximum repayable USD, weighted LTV, required repayment/caps/rounding, actual burn/transfer, debt and shares. For LP/sGREEN withdrawal preparation with IDs 1/0, assert the zero-LTV `False` result or an earlier getter/price failure with rollback; do not require impossible forced repayment from zero-LTV collateral.
- Actual funded LP/sGREEN swaps; backed GREEN with zero stabilization custody; aggregate GREEN deficits across two cohorts; exact 1%/integer boundaries and rollback; paused/invalid pairs; synthetic stabilization reservations; zero LP price and next-pair/auction fallback.
- Eleven non-GREEN dust claims matching the saved 1–56 raw-unit inventory, including unpriceable/under-backed non-GREEN cases: readiness does not enumerate or price them and an otherwise valid swap still works. Separately assert legacy NAV's strict pricing behavior, six one-USD-wei quotes/five floor-dependent cases using controlled prices, and unchanged accounting. Ordinary test price stubs are allowed; do not describe them as live gas qualification. Compare helper call counts/gas for 0, 11 and more than 20 unrelated claims to prove no claim-count-dependent loop was introduced.
- Alpha/Charlie proposal/execution, modern pool regressions, unchanged borrowing-collateral exclusion and actual authorized callers. Retain the existing VaultBook funded-replacement/uniqueness tests in the selected suite; no validator change or additional release test campaign is required.

Use `../ripe-protocol/.venv/bin/python` as a read-only dependency runtime, while keeping the command working directory in the dedicated worktree. It was verified here with Vyper 0.4.3, Titanoboa 0.2.7 and pytest 8.4.2. Do not install into or modify that shared environment. If unavailable, create a worktree-local environment from the pinned dependency files without upgrading versions. Set the writable Boa cache before any Boa-based compile/test probe; the default `~/.cache/titanoboa` can fail in the sandbox. The pytest configuration reads `RIPE_BOA_CACHE_DIR`; standalone Boa probes must call `boa.interpret.set_cache_dir` explicitly with that writable directory. Disable Python bytecode writes to the shared runtime. The focused final command is:

```sh
mkdir -p "${TMPDIR:-/tmp}/ripe-legacy-vault-compat-boa"
PYTHONDONTWRITEBYTECODE=1 RIPE_BOA_CACHE_DIR="${TMPDIR:-/tmp}/ripe-legacy-vault-compat-boa" \
  ../ripe-protocol/.venv/bin/python -m pytest -q \
  tests/registries/test_vault_book.py \
  tests/core/auctionHouse \
  tests/core/deleverage \
  tests/config/test_switchboard_alpha.py \
  tests/config/test_switchboard_charlie.py \
  tests/test_vault_pointer_runtime_sizes.py \
  tests/registries/test_vault_book_legacy_compat.py \
  tests/core/test_base_legacy_vault_compat.py
```

If new tests are instead placed in existing selected modules, remove only the unused proposed paths. Keep them as ordinary tests so default marker exclusions do not silently omit them. Run individual affected files or test cases while iterating, then the selected affected set after the final change; include each required behavior above. The listed directories are the affected subsystem regression set, not permission to run the repository suite. Add tests outside that set only for a specific changed dependency, and name why. After relevant checks pass, proceed to the local commit instead of starting unrelated validation. Fix failures caused by this patch; establish any claimed baseline failure with the same test at the frozen baseline, and report it separately. Do not run the whole suite, change CI or add release/fuzz/artifact/fork campaigns.

Using the same interpreter and `PYTHONDONTWRITEBYTECODE=1`, regenerate affected ABIs with `scripts/export_abis.py`, review the diff, then run `scripts/export_abis.py --check` once at the end. Do not fold unrelated generated changes into the commit: establish and report any pre-existing ABI mismatch separately. Preserve historical deployment records and update exact size pins only from measurements.

Completion requires:

- The five-contract compatibility patch and its constructor/interface consumers are coherent; selected existing/new tests and ABI check pass, with any genuine baseline failure clearly separated.
- Every changed deployable fits 24,576 bytes, including immutables; readiness has no unrelated-claim scan; modern behavior and settlement checks remain intact.
- Scoped changes are committed locally on `codex/base-legacy-vault-compat`. Continue through the commit without waiting for review. Return one final handoff with worktree/branch, commit, short change summary, affected test commands/results, exact changed-contract sizes and any remaining constraint/question. State what is incomplete if anything could not be finished. No separate report package, live-state survey, deployment plan or PR is required.
