# RH Deposit-Vault Hardening — WP0 / WP1 evidence bundle (rev 2, rebound)

> **Path note (8 August 2026):** some paths cited below no longer exist in the
> active tree — the block-clock inventory, the `contracts/testing/` probes, and
> the extracted deploy manifests and review records were removed. The citations
> were accurate when written and are left intact. See
> [`REMOVED.md`](../../simplification/REMOVED.md) for the full index; everything is
> recoverable from git history. No production contract was modified.

Produced by the implementation agent for
`docs/chains/rh/deposit-vault-smart-contract-hardening-implementation-plan.md`.

**Rev 2 supersedes rev 1.** It incorporates
an independent review and a mid-session rebind: `rh` advanced to `24de5e6`
(PR #75, the vault-migration lane), which this branch has merged. Every number
below was re-measured against that new baseline. **No production contract is
edited by this branch.**

---

## 0. What changed in rev 2

| Review finding | Disposition |
|---|---|
| P1 — strict-xfail loops did not execute the claimed matrices | **Fixed.** Every caller, action, and boundary is now an independently parametrized node. This immediately exposed three boundary sets that already satisfy their invariant and were being hidden by the first loop iteration (§4). |
| P1 — Work Package 8 not corrected as claimed | **Fixed.** The two tests that claimed to prove a lock now assert the absence of one explicitly; the §15 matrix is completed including exact point contribution and the MissionControl source swap. |
| P1 — most WP1 matrices missing | **Largely fixed.** Added the §8.4 token/custody matrix, the §9.4 pause matrix, the §12.1 PriceDesk matrix, the remaining §8.3 zero-price transitions, §11.3 outbound delivery, §11.4 dormant dust, and the missing §13 callback rows. Remaining gaps are named in §8. |
| P1 — RH-CHANGE-01 table not decision-gate compliant | **Fixed.** All fields populated for every row; the pull-and-measure design and the central Teller boundary are now measured; rows added for outbound delivery, dormant dust, and the price-source failure. |
| P1 — "Option A is infeasible" overstated | **Retracted and corrected.** A shrinkage search found a 523-byte semantics-preserving reduction that makes Option A viable with 477 bytes of deployed headroom. See §6 E-2. Exact patches are now retained. |
| P2 — atomicity assertions incomplete | **Fixed.** Shared complete-snapshot helpers for RipeGov and StabilityPool, used at every failure node. |
| P2 — evidence overstated / not durable | **Fixed.** Node IDs enumerated from a real run, raw logs and exact probe patches retained alongside this file, and the work is now a signed commit. |
| P2 — startup-report ordering | **Acknowledged, not repairable retroactively.** See §9. |

---

## 1. Section 19 startup report (rebound)

| Field | Value |
|---|---|
| Repository anchor | `/Users/wigglez/dev/ripe-protocol` |
| Worktree | `/Users/wigglez/dev/ripe-protocol-rh-deposit-vault-hardening-plan` |
| Branch | `codex/rh-deposit-vault-hardening-plan` |
| **Original bound baseline** | `be6e4e9805e9b499b10f61cd219c555e62b43857` / tree `dba8a4e557e3a943e25bb84d9911842c74371415` |
| **Rebound baseline** | `24de5e62e2158114e3694c9a356c0add94b6f329` / tree `863d68ef61cf194e58bae76fc27f7b703a63b2e4` (`origin/rh`, "Merge pull request #75 from Ripe-Foundation/codex/rh-vault-migration-phase1") |
| Branch HEAD after merge | `9a71ed2b591ab9e4d285be7448047125760f8fb7` / tree `36616dd4eea74277a35283a50f6775369bdbff49` |
| Commits | work `f3fe3bf` (signed), merge `9a71ed2` |
| Working tree | clean |
| Delta vs rebound baseline | the plan Markdown (administrative) + 6 test/mock files; **zero production contracts** |
| Merge conflicts | none |

### Pinned environment (unchanged, reproduced)

```
Python 3.12.0
vyper 0.4.3          (0.4.3+commit.bff19ea2)
titanoboa 0.2.7
pytest 8.4.2
hypothesis 6.138.15
```

### Runtime sizes at the rebound baseline

Per-file pragma compilation, no `-O` flag, compiled from the root of the tree
being measured. Deployed = template + constructor immutables.

| Contract | Optimization | Template | Template headroom | **Deployed** | **Deployed headroom** | vs `be6e4e9` |
|---|---|---:|---:|---:|---:|---|
| `contracts/vaults/RipeGov.vy` | default gas | 24,499 | 77 | 24,531 | **45** | unchanged |
| `contracts/vaults/StabilityPool.vy` | `optimize codesize` | 24,275 | 301 | 24,371 | **205** | unchanged |
| `contracts/core/Teller.vy` | `optimize codesize` | 24,162 | 414 | 24,258 | **318** | **−119 bytes of headroom** |
| `contracts/core/TellerUtils.vy` | — | 11,804 | 12,772 | 11,900 | 12,676 | newly in the size gate |

Deployed figures cross-checked against `config/contract-artifact-expectations.json`
at the rebound baseline.

**The merged migration work consumed 119 bytes of Teller headroom and set its
own floor.** `tests/test_vault_pointer_runtime_sizes.py` now carries
`MIN_TELLER_MARGIN = 300` with a comment that any further Teller growth is
gated. That floor is stricter than this plan's 200-byte rule and directly
constrains Work Package 6 — see §5.3 and §6 E-8.

### Effect of the rebind on every finding

The merge touched `Teller.vy`, `TellerUtils.vy`, `SwitchboardEcho.vy`,
`Ledger.vy`, and `Lootbox.vy`. It did **not** touch `RipeGov.vy`,
`StabilityPool.vy`, `StabVault.vy`, `SharesVault.vy`, or `VaultData.vy`.

| Findings | Contracts they depend on | Rebind effect |
|---|---|---|
| DV-01 … DV-07 | RipeGov, SharesVault, VaultData | **unaffected** — sources byte-identical |
| DV-08, DV-09, DV-12, DV-13, DV-14, DV-15 | StabVault, StabilityPool, PriceDesk | **unaffected** — sources byte-identical |
| DV-10 | Teller | **survives.** Re-checked on the merged source: `receiptMeasurementActive` is still `transient(bool)` checked only inside `_deposit` (line 323), and `depositFromTrusted` (line 279) and `depositIntoGovVault` (line 837) are still undecorated. All DV-10 checkpoints still xfail. |

The merge also added `Teller.migrateVaultPosition` (line 580), a new
`@nonreentrant` custody-changing route. It is switchboard-only, so not
attacker-reachable from a token callback, but it is a new row for any Section 13
guard and is included in §5.3.

### Decision gates

| Gate | State after the rebind |
|---|---|
| **RH-LANE-01** | **RESOLVED by the owner's action.** The migration lane went first and is integrated as `24de5e6`. This plan is rebound onto it. No second live lane is modifying Teller. |
| SP-PRICE-01 | Option A by default. Characterized; no production change needed for A. But see DV-14: option A's liveness claim does not hold for a reverting price source. |
| GOV-WEIGHT-01 | **UNRESOLVED.** No autonomous default. |
| RG-SIZE-01 | **RESOLVED by the owner 2026-08-08:** the 200-byte floor governs. See the disposition below. §6 E-2 shows Option A is feasible at a stated cost. |
| RH-CHANGE-01 | **PARTIALLY RESOLVED — 3 of 12 gated rows.** The owner approved the DV-01/02/03 RipeGov least-privilege row, merged 2026-08-07 as `30cf436` (PR #78). The other 9 rows (DV-04/05/06/08/09/10/13/14/15) remain unapproved and no production source is edited for them. See the disposition below. |

**Stop condition encountered at WP0:** GOV-WEIGHT-01, RG-SIZE-01 and
RH-CHANGE-01 were all unresolved *at the time this evidence was recorded*, so no
production-contract edit was made in WP0. Dispositions reached after that point
are recorded below rather than by rewriting the WP0 narrative.

#### RG-SIZE-01 disposition — owner, 2026-08-08

**The hardening plan's 200-byte floor governs.** `MIN_TELLER_MARGIN` in
`tests/test_vault_pointer_runtime_sizes.py` is lowered from 300 to 200 to match,
resolving E-8. This is a deliberate relaxation of the floor the vault-migration
workstream set, made so that the §13 central receipt-window guard (M7c, **+81
bytes → 237 deployed headroom**) is admissible; at 300 it would be blocked. The
plan's requirement at §5.3 line 236 — that anything *below* 200 needs a separate
exact owner waiver — is unchanged and still binding.

Nothing about any deployed contract changed with this decision: Teller's measured
headroom is 318 bytes, which cleared both floors already. The decision only
governs what future Teller growth is admissible.

#### RH-CHANGE-01 disposition — owner, 2026-08-07 (partial)

**One row approved: DV-01/02/03, RipeGov least privilege.** All three call sites
(`depositTokensWithLockDuration`, `adjustLock`, `releaseLock`) went from
`assert addys._isValidRipeAddr(msg.sender)` to
`assert msg.sender == addys._getTellerAddr()`. Merged as `30cf436` (PR #78) with
RipeGov's own block in `config/contract-artifact-expectations.json` regenerated in
the same change. Measured effect: runtime template 24,490 bytes, deployed 24,522
with the +32 immutable, **EIP-170 headroom 45 → 54** — the only candidate row that
*shrinks* RipeGov.

**RipeGov must be redeployed.** Its runtime bytecode changed; this is not a
source-only edit.

**The remaining 9 rows are still unapproved** (DV-04, DV-05, DV-06, DV-08, DV-09,
DV-10, DV-13, DV-14, DV-15) and no production source is edited for them, so §17
continues to apply to each. Note that DV-10's candidate (M7c, §13) is now
*admissible on size* following the RG-SIZE-01 disposition above, but admissibility
is not approval — it still needs its own RH-CHANGE-01 row.

---

## 2. RH-LANE-01 — resolved, with the drift recorded

The lane was observed three times during this session. It is drift-prone exactly
as Section 5.5 warns, and it moved twice while work was in progress.

| Observation | State |
|---|---|
| Session start | branch at `be6e4e9`, **uncommitted** edits to `SwitchboardEcho.vy`, `Teller.vy`, `TellerUtils.vy`; no checkpoint commit or archive existed. Diff bytes SHA-256 `3e1d45d190c50f29d00a1985a409a1a1f4dea559588f3376ea7ad7f062421326`. |
| Mid-session | owner committed `649a855` ("work", 11:11:40) carrying those three contracts; the worktree then held a *different* uncommitted set (artifact expectations, ABIs, blueprint, runtime-size test) plus two untracked files. |
| Later | the uncommitted set grew to include `Teller.vy`, `Ledger.vy`, `Lootbox.vy`, and **`tests/vaults/test_ripe_gov_controls_and_migration.py`** — a direct file-level collision with this branch. Diff bytes SHA-256 `5f86f7dcee0b3916cf492bbb37a38db57ce3971a206b91060da017061598d1bc`. |
| Now | the lane is merged to `rh` as PR #75 (`24de5e6`) and this branch is rebound onto it. The collision resolved cleanly: `rh` changed 5 lines near line 1556 of that test file, this branch appends a new section, and `git merge` produced no conflict. |

**Nothing in this session ever wrote to that worktree.** All observations were
`git status` / `git diff` / `shasum` reads.

---

## 3. Existing zero-price test inventory (replaces the §3.5 "small example" assessment)

Unchanged by the rebind.

| Test | Cohorts | Claim assets | Size of the zero-priced asset | Transitions | What it asserts |
|---|---|---|---|---|---|
| `test_stab_vault_claims.py::test_stab_vault_claims_price_oracle_zero` | 1 | 1 | $150 | price→0 | claim **reverts**. No cohort value computed. |
| `test_stab_vault_redemptions.py::…_price_oracle_zero` | 1 | 1 | $150 | price→0 | redemption **reverts**. No cohort value. |
| `test_stab_vault_hardening.py::test_unpriced_new_receipt_reverts_without_claim_accounting` | 1 | 1 | $1 | 0 at settlement | settlement reverts atomically. |
| `…::test_active_zero_price_stays_registered_and_recovers_after_price_restore` | 2 | 1 | **$0.10** | 0 → feed off → restored | registration survives; 1e18 deposit/withdraw stay live. **No cohort-value assertion.** |
| `…::test_prune_skips_unpriced_pair_and_continues_batch_…` | 1 | 2 ($0.10, 100 000 wei) | $0.10 | price→0 | prune skips the unpriced pair. |
| `test_ah_liq_stab_edge_cases.py` (green-LP zero feed, `test_ah_liquidation_zero_price`) | 1 | n/a | stab/collateral, not an active claim asset | 0, feed off | liquidation fails closed / routes to auction. |

**Verdict: §3.5 CONFIRMED, with one refinement.** Two tests do use a $150 claim
asset, but both only assert reversion. The largest zero-priced **active claim
asset** whose NAV effect is exercised was **$0.10**, and no existing test
computed cohort value across an outage. This branch adds that at $1,000 scale.

---

## 4. Section 6.1(B) expected-red table

Generated from a real `-rxX` run, not hand-written. The enumerated table with
every node ID is `expected-red-table.md` beside this file; the raw run is
`expected-red-run.log`. Structure:

| Finding | Invariant | Checkpoint nodes | Gate |
|---|---|---|---|
| DV-01 | SV-1, SV-4 | one per registered non-Teller caller (13) | RH-CHANGE-01 |
| DV-02 | SV-4, RG-4 | one per registered non-Teller caller (13) | RH-CHANGE-01 |
| DV-03 | SV-4, RG-4 | one per registered non-Teller caller (13) | RH-CHANGE-01 |
| DV-04 | RG-5 | caller × portion (2 × 2) | RH-CHANGE-01 §9.2 |
| DV-05 | RG-4 | shorten-existing (1) + out-of-bounds duration (5) | RH-CHANGE-01 §9.3 |
| DV-06 | SV-5 | adjustLock, releaseLock (2) | RH-CHANGE-01 §9.4 |
| DV-07 | GOV-WEIGHT-01 | 1 | GOV-WEIGHT-01 |
| DV-08 | SV-1, SP-6 | 1 | RH-CHANGE-01 §11.2 |
| DV-09 | SP-1 | deposit, withdrawal, total value (3) | RH-CHANGE-01 §11.1 |
| DV-10 | SV-6 | before-credit × 2 routes, after-credit × 1 (3) | RH-CHANGE-01 §13 |
| DV-13 | SP-4 | 1 | RH-CHANGE-01 §11.3 |
| DV-14 | SP-3 | deposit, withdrawal (2) | RH-CHANGE-01 §12 |
| DV-15 | SP-5 | 1 | RH-CHANGE-01 §11.4 |

**Boundaries that parametrization proved already safe** — hidden by the rev-1
loops, now plain passing regressions rather than checkpoints:

- same-address transfer with **zero amount** already reverts (`no withdrawal amount`);
- contributor durations **at min, ordinary, at max** already land in bounds;
- every **unregistered** caller is already rejected atomically for all four methods.

Every finding also has a plain **passing** characterization pinning the exact
current behavior, so the record survives whichever way the owner decides.

---

## 5. RH-CHANGE-01 minimum-change table

Bytecode deltas are **diagnostic estimates** measured at the rebound baseline in
`/private/tmp/rh-size-probe` (a non-git copy, tests removed), per-file pragma,
no `-O`. **The exact patch for every row is retained** in `size-probes/` beside
this file so each delta can be re-derived byte for byte. These are not
acceptance builds.

Deployed = template + immutables (RipeGov +32, StabilityPool +96, Teller +96).

### 5.1 RipeGov rows — deployed headroom starts at 45 bytes

| # | Change | Concrete failure without it | Reachability / blast radius | No-change option | Config / shared-behavior alternative | Smallest mitigation | Template Δ | Deployed headroom | ABI / storage | New-code + residual risk |
|---|---|---|---|---|---|---|---:|---:|---|---|
| **M1** | Teller-only on `depositTokensWithLockDuration`, `adjustLock`, `releaseLock` | Any registered RIPE address mints governance shares for an arbitrary beneficiary against custody already owned by another user, moving no tokens (DV-01); can extend or force-release any lock (DV-02/03) | Needs control of a registered address (core dept, registered vault, or switchboard) — not EOA-reachable. Blast radius: total dilution of every RipeGov depositor for that asset | Accept: the vault trusts the whole registry | None. The predicate *is* the authority; no config narrows it | Replace the predicate with `msg.sender == addys._getTellerAddr()` in three places | **−9** | 54 | none | Very low in production. **Test blast radius is the cost:** 25 direct call sites (20 sending as `switchboard_alpha`), one of which is the `_direct_deposit` helper reused at 9 more sites. Residual after fix: Teller's own callers still choose `_user` |
| **M2** | Same-address short-circuit in `transferBalanceWithinVault` | A same-user AuctionHouse/CreditEngine transfer burns the proportional point penalty and re-weights the unlock toward `minLockDuration`; a **full** same-address transfer destroys the user's entire point balance (DV-04) | Only via AuctionHouse/CreditEngine, not user-callable | Accept: current callers do not produce same-address transfers | Fix in the two callers instead, leaving RipeGov untouched | `if _fromUser == _toUser: return 0, False` before any mutation | **+31** | 14 | none | Low. §9.2 forbids changing SharesVault family-wide without a full consumer inventory. Residual: the same defect remains in any other vault sharing the helper |
| **M3** | Clamp contributor lock duration to governance bounds | `transferContributorRipeTokens` forwards the raw configured duration into the weighted blend, dragging a max-locked recipient below `minLockDuration` (DV-05) | Needs an HR contributor payout; recipient is the contributor's owner | Accept | **Config alternative exists:** require every deployed `Contributor` to carry a `depositLockDuration` inside `[min,max]`. Zero contract change | `max(min, d)` then `min(max, …)` before `_handleGovDataOnTransfer` | **+50** | −5 | none | Low. Residual under the config alternative: a future misconfigured Contributor re-opens it |
| **M4** | Pause gate on `adjustLock` / `releaseLock` | Both stay live while RipeGov is paused; `releaseLock` reduces balances via `vaultData._reduceBalanceOnWithdrawal`, bypassing SharesVault's pause check entirely (DV-06) | Post-M1 only Teller can reach them, and Teller has its own pause. Residual: switchboard-initiated `Teller.adjustLock` still works while the vault is paused | Accept: pause is a custody control, not a lock control | Pause Teller as well as the vault in the runbook. Zero contract change | `assert not vaultData.isPaused` in both | **+12** | 33 | none | Low. §9.4 requires migration and overflow escapes to stay available; both are separate methods and unaffected |
| **M5** | GOV-WEIGHT-01 "zero means zero" | A configured zero weight silently behaves as 100 % (DV-07) | Governance-config only. `DefaultsRobinhood` sets RIPE `assetWeight = 100_00`, so **the bound launch default does not change**; only the meaning of a future governed zero | Accept and document | **Config alternative exists:** validate `assetWeight != 0` in the SwitchboardAlpha setter. Zero RipeGov delta | Always apply the multiplier, early-return on zero | **+7** | 38 | none | Low |

**Combined M1+M2+M3+M4+M5 (`size-probes/s2.patch`): template 24,590 → deployed
24,622 → EIP-170 headroom −46. This shape does not deploy.** §6 E-2 gives the
reduction that fixes it.

### 5.2 StabilityPool / StabVault rows — deployed headroom starts at 205 bytes

That 205 bytes is the entire budget for Work Package 4.

| # | Change | Concrete failure without it | Reachability / blast radius | No-change option | Config / shared-behavior alternative | Smallest mitigation | Template Δ | Deployed headroom | ABI / storage | New-code + residual risk |
|---|---|---|---|---|---|---|---:|---:|---|---|
| **M8b** | §11.2 pull-and-measure settlement | A donation of D lets an AuctionHouse settlement declare Q while transferring only Q−D; `_addClaimableBalance` validates against *aggregate* free surplus, so the donation is silently consumed as liquidation proceeds (DV-08) | Needs a lossy/deflationary claim token plus any prior donation. Overstates recorded claim liability against real custody | Accept with characterization | Restrict the accepted claim-asset set to exact-transfer tokens by configuration. Zero contract change | StabilityPool pulls from the authenticated AuctionHouse and records only its own measured delta | **+295** | **−90** | AuctionHouse must approve instead of transfer → **cross-contract ABI/behavior change** | **Does not fit.** Also needs a matching AuctionHouse edit, a second production change outside the smallest-change principle |
| **M8-naive** | Require exact free surplus | same as M8b | same | — | — | change `<=` to `==` in the free-surplus assert | **+0** | 205 | none | **Rejected as specified.** §11.2 explicitly forbids this shape: any donation would become a denial-of-service on liquidation settlement |
| **M9** | Custody-deficit guard on the shared NAV helper | A rebase/burn against claim custody leaves recorded liability above real balance; NAV, deposit, and withdrawal never check, so the pool keeps valuing value it cannot deliver and socializes the hole (DV-09). Only the *activation* paths check today | Any deflationary/rebasing claim asset. Blast radius: every depositor in that stab asset | Accept with characterization | Restrict claim assets to non-rebasing tokens by configuration. Zero contract change | `assert balanceOf(self) >= totalClaimableBalances[asset]` inside `_getValueOfClaimableAssets` | **+78** | **127** | none | Below the 200-byte floor → needs an exact RG-SIZE-01 waiver. Residual: a deficit then bricks the pool until replenished; the repair path is proven live by `test_active_claim_custody_deficit_is_repaired_by_replenishment` |
| **M10** | §11.3 exact outbound delivery | A claim burns shares and clears the liability in full while a fee-on-transfer claim asset delivers strictly less; nothing measures the recipient (DV-13) | Any fee/burn-on-transfer claim asset | Accept with characterization | Same config alternative as M9 | Measure recipient balance across the transfer in `_handleAssetForUser` | **+151** | **54** | none | Below the floor. **M9+M10 together (+229) exceed EIP-170.** At most one fits |
| **M11** | §11.4 dormant-dust exit liveness | A dormant-only claim balance is unreachable once the owner's stability shares are burned; recovery depends on someone else's future liquidation (DV-15) | Any user whose last position is dormant dust | Accept with characterization — the amount is bounded below `$0.10` per pair by `ACTIVATION_USD_THRESHOLD` | Runbook: sweep dormant pairs via a governed replenishment. Zero contract change | Not sized — every shape needs a new external method and there is no room for one | not sized | n/a | new external method → ABI change | **No budget exists.** Recommend accepted residual risk with the characterization |

### 5.3 Teller row — deployed headroom is 318 bytes, with a 300-byte floor

| # | Change | Concrete failure without it | Reachability / blast radius | No-change option | Config alternative | Smallest mitigation | Template Δ | Deployed headroom | ABI / storage | New-code + residual risk |
|---|---|---|---|---|---|---|---:|---:|---|---|
| **M7c** | §13 central receipt-window guard | `receiptMeasurementActive` is checked only inside `_deposit`, and `depositFromTrusted` / `depositIntoGovVault` are undecorated. A token callback fired during measurement completes a nested protected withdrawal or liquidation while the outer deposit still succeeds — for both the before-credit and after-credit callback placements (DV-10) | Needs a callback-capable asset admitted to a vault. Invalidates the before/after custody measurement SV-1 rests on | Accept with the full callback matrix characterized | Admit only callback-free assets by configuration. Zero contract change | One `_assertNoReceiptMeasurement()` helper, called from the shared `_deposit`/`_withdraw` prologue plus 7 named routes | **+81** | **237** | none | Above this plan's 200 floor but **below the merged work's 300 floor** — the two floors conflict and the owner must pick. Route list should also cover the new `migrateVaultPosition` (switchboard-only, low priority) |
| **M7b** | Same, duplicated per entry point | same | same | same | same | the assert copied to all 25 routes carrying the pause assert | **+175** | 143 | none | Below both floors. §13 asks for the smallest central boundary; this is the shape to avoid |

---

## 6. Errata against the plan (measured, not opinion)

**E-1 — RG-SIZE-01 measures the wrong quantity for an EIP-170 gate.**
`-f bytecode_runtime` reports the runtime *template*, excluding constructor
immutables; EIP-170 binds deployed code. Real deployed headroom at the rebound
baseline is **RipeGov 45, StabilityPool 205, Teller 318**. The repository
already records both figures in `config/contract-artifact-expectations.json`,
and `tests/test_vault_pointer_runtime_sizes.py` asserts the deployed values
live. §16.5's recipe should measure deployed size or add the immutable offsets.

**E-2 — CORRECTED FROM REV 1. Option A is feasible, at a stated cost.**
Rev 1 claimed Option A was infeasible. That was wrong: it generalized from a
single implementation shape without running the shrinkage search Option A
explicitly permits. Measured at the rebound baseline:

| Candidate | Patch | Template | Deployed | Deployed headroom |
|---|---|---:|---:|---:|
| unchanged RipeGov | — | 24,499 | 24,531 | 45 |
| hardening set alone | `s2.patch` | 24,590 | 24,622 | **−46 (does not deploy)** |
| drop 5 consumer-less public view wrappers | `s1.patch` | 23,976 | 24,008 | 568 |
| **hardening set + those reductions** | `s3.patch` | **24,067** | **24,099** | **477** |
| hardening set + reductions + codesize pragma | `s4.patch` | 22,570 | 22,602 | 1,974 |

The accurate statement is: **the naïve M1–M5 shape needs at least 246 bytes of
reduction to clear the 200-byte floor (24,590 → 24,344 template), and a
523-byte semantics-preserving reduction exists.** Option A is viable.

The reduction is not free, and the owner must weigh it:

- The five wrappers are `getLatestGovPoints`, `getLockBonusPoints`,
  `getWeightedLockOnTokenDeposit`, `areKeyTermsSame`, `refreshUnlock`. A fresh
  grep finds **no production Vyper consumer** — they appear only in
  `scripts/abis/RipeGov.json` and in tests.
- Removing them is nonetheless an **ABI-breaking change**: five external
  functions and their selectors disappear. §17 stops on an unapproved
  ABI-breaking change, and §16.5 requires every changed selector to be intended
  and approved.
- Off-chain consumers (frontend, dashboards, subgraphs) are outside this plan's
  scope and were **not** verified. That check is the owner's.
- It breaks the tests that call them, including two added by this branch.
- **This was one candidate reduction, not an exhaustive search.** Other
  non-ABI-breaking reductions may exist and were not looked for.

**E-3 — any production edit also breaks frozen-artifact gates the plan does not
list.** `config/contract-artifact-expectations.json` freezes source SHA-256,
canonical ABI hash, storage layout, runtime-template size/hash, and creation
hashes. Editing RipeGov, StabilityPool or Teller additionally requires
regenerating that JSON and updating `tests/inventory/test_contract_artifacts.py`,
`tests/test_vault_pointer_runtime_sizes.py`, and
`tests/vaults/modules/test_stab_vault_hardening.py::test_deployed_runtime_fits_eip170`.
Only the last is inside §3.3's file list. The merged migration work had to do
exactly this, which confirms the cost is real.

**E-4 — the derived stability-reward lock does not include `minLockDuration`.**
`MissionControl._getLockDuration` returns `(maxLock − minLock) × ratio / 100_00`
when the ratio is nonzero; the minimum is *not* added back, it is re-applied by
`RipeGov._depositTokensInRipeGovVault`'s clamp. §15's matrix should assert
against that formula. Confirmed by measurement: ratio 50 % over [100, 1 100]
yields 500 blocks, not 600.

**E-5 — §5.3's diagnostic global `-O codesize` figure equals the source-pragma
figure exactly** (22,927 on unchanged RipeGov at both baselines).

**E-6 — pre-existing baseline failures the plan does not mention.** Classified
in §7.

**E-7 — the frozen-artifact suite that E-3's remediation runs through is itself
broken.** `tests/inventory` gives 11 failed / 43 passed / 176 errors on the
clean baseline, byte-identically on the candidate. Root cause: the suite and
`scripts/check_block_clock_inventory.py` reference
`scripts/utils/robinhood_backends.py`, which does not exist. That lane is **not**
one of §16's lanes; it was run only to check E-3 exposure. The artifact
*expectations* are current — `scripts/check_contract_artifacts.py` returns
`CONTRACT_ARTIFACTS_OK`.

**E-8 — RESOLVED 2026-08-08: two conflicting Teller size floors existed.** This
plan sets 200 bytes; the merged migration work set `MIN_TELLER_MARGIN = 300` in
`tests/test_vault_pointer_runtime_sizes.py`. The §13 central guard (M7c, +81)
lands at **237 bytes deployed headroom** — passing this plan's floor and failing
the merged one, which is why the two had to be reconciled before Work Package 6.

**Disposition:** the owner ruled on 2026-08-08 that the 200-byte floor governs,
and `MIN_TELLER_MARGIN` was lowered from 300 to 200 to match, so a single floor
now exists in the tree. M7c is therefore admissible on size. Recorded in full
under the RG-SIZE-01 disposition in §1. No deployed contract changed: Teller's
measured headroom is 318 bytes, which already cleared both.

---

## 7. Suite health

Measured at the rebound baseline. Raw logs are retained outside the repository
at `~/dev/ripe-protocol-review-archives/rh-deposit-vault/logs/`.

| Lane | Baseline `24de5e6` | Candidate |
|---|---|---|
| 16.1 RipeGov focused | 313 passed | 372 passed, 52 xfailed |
| 16.1 two RipeGov files only | 146 passed | 205 passed, 52 xfailed |
| 16.2 StabilityPool focused | 183 passed | see note |
| 16.2 existing fuzz | 4 collected, 4 passed | unchanged |
| 16.3 composed | 377 passed, 1 failed | see note |
| 16.4 shared-vault deterministic | 446 passed, 1 failed | see note |
| 16.4 shared-vault fuzz | 4 passed, 543 deselected | unchanged |
| migration regression (added by the merged rh work) | 86 passed | see note |

The two baseline failures are the pre-existing ones classified below; neither is
in a file this branch edits.

1. `tests/core/teller/test_teller_withdraw.py::test_withdraw_many_arb_sys_rejects_second_same_action_block`
   — aggregate-only `AttributeError: 'IntegerT' object has no attribute 'key_type'`
   from titanoboa 0.2.7 trace pollution at reused addresses. Passes in isolation
   (1 passed) and with its whole file (36 passed). Not a contract defect.
2. `tests/vaults/test_basic_vault_consumer_inventory.py::test_basic_vault_consumer_inventory_matches_reviewed_sources`
   — frozen inventory pinned to baseline `1e36c0c3…` while `AuctionHouse.vy`,
   `Lootbox.vy` and `CreditEngine.vy` source hashes have moved. Stale frozen
   inventory, unrelated to deposit-vault scope.

"see note": the candidate lanes for 16.2 / 16.3 / 16.4 / migration were still
executing when this record was written and are recorded in the archive logs.
Every individual test group added by this branch was run and is green, and the
pre-merge equivalents of these lanes were green apart from the same two
pre-existing failures.

---

## 8. What was deliberately NOT done, and why

- **All production-contract edits.** At the time of WP0, RH-CHANGE-01 approved no
  row and GOV-WEIGHT-01 and RG-SIZE-01 were both unresolved; §17 applied. *Both
  of those have since moved — RG-SIZE-01 was resolved by the owner on 2026-08-08
  (see §1), and a RH-CHANGE-01 row was subsequently approved and merged. This
  bullet records the WP0 position, not the current one.*
- **Work Package 3 §10.3 (RipeGov stateful model) and Work Package 7
  (StabilityPool stateful model).** Test-only, but their required invariants are
  the ones currently violated: RG-4 (DV-02/03/05), RG-5 (DV-04), SP-1 (DV-09),
  SP-4 (DV-13), SP-6 (DV-08). A state machine asserting RG-1…RG-7 and SP-1…SP-6
  after every step cannot pass until the paired fixes land; writing it now would
  only produce a second, less legible copy of the expected-red table. It should
  follow the approved fixes.
- **Work Package 3 §10.2 (overflow-disable escape from a genuine arithmetic
  failure).** Requires constructing a real point-overflow state. Not attempted;
  it is independent of the open gates and is the clearest remaining test-only gap.
- **§12.1 empty / malformed price-source return data.** `MockPriceSource` can
  now revert (added here), be zero, and have its feed removed. Producing
  *malformed* return data needs a non-conforming source contract registered in
  PriceDesk through its timelocked registry. The revert case already proves the
  class — `PriceDesk._getPriceFromPriceSource` uses a bare `staticcall` with no
  failure isolation, so **any** non-conforming source propagates.
- **§8.4 token callback during StabVault outbound delivery.** Both
  StabilityPool's external entry points and `Teller.claimManyFromStabilityPool`
  are `@nonreentrant`, so this row is expected to be closed; it was not proven
  with a purpose-built re-entrant claim asset.
- **Repairing the two pre-existing baseline failures and the broken
  `tests/inventory` suite** — out of scope.

---

## 9. Process disclosures

Two mistakes were made during this session. Both are recorded because they
affect how the evidence should be read.

1. **The detached baseline worktree was contaminated mid-run.** The Bash working
   directory persists between calls; a `cat >>` intended for the candidate
   landed in `/private/tmp/rh-deposit-vault-baseline` instead. Lanes 16.3, 16.4,
   16.4-fuzz and the RipeGov-only lane were run against a polluted tree. The
   worktree was restored with `git checkout --`, verified back at the bound
   tree, and **every affected lane was re-run from the clean tree**; only the
   re-run numbers were ever reported. All later scripts assert the baseline tree
   hash and refuse to run on a dirty tree.
2. **The Section 19 report was produced after baseline work had begun, not
   before.** Baseline identity, lane state, versions and sizes were all bound
   before the first file was written, but the report itself was emitted later.
   The gate exists to make that binding visible up front; that ordering cannot
   be repaired retroactively.

A third, smaller one: rev 1's WP8 subset was verified with `-k stab_reward`,
which did not re-run the two pre-existing tests the same change had edited. They
failed in the next full lane and were fixed. All touched files are now run whole.

---

## 10. Reproduction

- Runner: §16.0 verbatim, `RH_VAULT_TEST_ROOT=/private/tmp/rh-deposit-vault-tests.session1`.
- Baseline worktree: `/private/tmp/rh-deposit-vault-baseline`, detached at
  `24de5e6`, tree asserted `863d68ef…` before every baseline lane.
- Size probes: `/private/tmp/rh-size-probe` (plain copy, tests removed, no git);
  script retained as `size-probes/size_probe3.py`, patches as `size-probes/*.patch`.
- Artifacts retained at `~/dev/ripe-protocol-review-archives/rh-deposit-vault/`:
  `SUITE-HEALTH.md`, `expected-red-table.md`, `expected-red-run.log`, `logs/`,
  `size-probes/` (every diagnostic patch plus the probe script), and
  `WP0-EVIDENCE-rev1.md`.
