# PR #126 — Independent merge-readiness review

**PR:** `Ripe-Foundation/ripe-protocol#126` (`rh-audit-remediation` → `rh`)
**Reviewed head:** `5f3848c051655e6b9b7e439fb6db13348d87ade3`
**Base:** `36ee0db42482c3e7d6c43d045fc02655b90bebf4`
**Date:** 2026-08-17
**Scope:** merge safety, whether the 30 consolidated SC findings are fixed in
contract source, collateral damage, and whole-system integrity.

**Classification:** independent review record. This is not a deployment
authorization, a release approval, or a substitute for the owner decisions named
below.

## Relationship to the sibling reviews

This review was conducted independently against `5f3848c`, without reference to
the sibling merge-readiness records that landed on this branch while it was in
progress:

- [`PR-126-RH-MERGE-READINESS.md`](PR-126-RH-MERGE-READINESS.md) (`8ebb0e7`)
- [`PR-126-MERGE-READINESS.md`](PR-126-MERGE-READINESS.md) (`7c4753c`)
- [`PR-126-FINAL-MERGE-READINESS-REVIEW.md`](PR-126-FINAL-MERGE-READINESS-REVIEW.md) (`8c6e6c1`)

All three are documentation-only commits. Contract source is byte-identical
across `5f3848c` and `8c6e6c1`, so every source-bound finding here applies
unchanged to the current head.

**These four records reach the same merge verdict by independent routes**, which
is the useful property. None supersedes another. The disagreements are of
emphasis, not of fact, and are confined to SC-03 — see below.

This document is retained because three findings appear in no sibling record:
the committed `scratchpad/` file publishing live governance state to a public
repository, the BasicVault consumer inventory that is red at HEAD and hidden
from CI by a module-level marker, and the `Teller.setUserConfig` default
inversion. It also carries the measured EIP-170 headroom table.

**Consolidation note.** Four overlapping merge-readiness documents in
`docs/audit/` is more than this decision needs. Once the merge lands, these
should be folded into a single record with the others retired, so that a later
reader is not left guessing which one is authoritative.

## Method and epistemic rules

Every claim below was checked against contract source at the reviewed head. The
repository's own remediation documents (`docs/audit/`, `docs/chains/rh/`) were
treated as *claims to be verified*, not as evidence. Where a repository document
and the source disagreed, the source won.

Work performed:

- Fourteen parallel domain reviews, each instructed to verify against source and
  to distinguish *fixed in contract code* from *mitigated by configuration*,
  *accepted residual*, and *still open*.
- Two hand-run mutation tests in an isolated throwaway worktree (SC-01, SC-02):
  the fix was reverted and the regression suite re-run to prove the tests bite.
- Direct measurement of deployed runtime sizes including immutables.
- Independent local runs of the EIP-170 suites, `tests/tokens`, the ABI-currency
  checks, the AuctionHouse keeper-accounting regressions, and the BasicVault
  consumer inventory.

"Fixed in code" below means: the contract changed, **and** a regression exists
that would fail if the change were reverted.

## Verdict

**Merge-ready after three cleanups. None require contract changes.**

The merge is mechanically trivial. `git merge-base rh rh-audit-remediation`
returns `rh`'s head exactly, so this is a strict fast-forward — 172 commits
ahead, 0 behind, no conflict surface. GitHub reports `MERGEABLE`. Both exact-head
CI runs pass every lane (PR run `32055765249`, push run `32055761077`).

The contract work is high quality and the regression coverage is real. The branch
adds **zero** `xfail`, `skip`, or `skipif` markers anywhere in `tests/` — verified
across the whole diff. No test in the base suite was weakened to make CI green.

One High-severity finding (SC-03) has no contract fix and no regression test. It
now carries an explicit operational disposition as a launch gate, recorded in the
sibling review after this work began. This document does not contest that call;
it records the two specifics the gate should be checked against.

Of the three items below, only the second and third are genuinely merge-gating,
and both are single-file changes.

## Pre-merge items

### 1. SC-03 — confirm the disposition covers the redeploy window

**Status changed during this review.** When this work began, SC-03 had no fix, no
test, and no disposition anywhere: the derived follow-up register refreshed on
2026-08-17 dispositioned SC-10, SC-13, SC-14, SC-24, SC-25, SC-26, SC-28 and
SC-30, and did not mention SC-03 at all. That gap has since been closed by
[`PR-126-RH-MERGE-READINESS.md`](PR-126-RH-MERGE-READINESS.md), which records it
as *"Operational, not contract-closed … Launch gate, not a source-merge blocker"*
and carries it as a hard activation gate.

That disposition is reasonable and this review does not contest the merge
verdict. What follows is the residual technical detail the disposition should be
checked against, because two specifics are not reflected in it.

The first-depositor donation/inflation attack on `SavingsGreen` is live at the
reviewed head. `_amountToShares` / `_sharesToAmount` in
`contracts/tokens/modules/Erc4626Token.vy:238-296` carry no virtual shares and no
dead-share offset, and `deposit()` at `:67-77` is permissionless with no minimum
(`_deposit` at `:110-113` asserts only nonzero amount, nonzero shares, nonzero
recipient). A proof of concept executed against this head profits the attacker
~250 GREEN on a victim's 1,000 GREEN deposit, with a deposit-denial variant.

The original closure requirement was explicit.
`docs/audit/PR-126-SMART-CONTRACT-FINDINGS.md:142` requires *"virtual/dead shares
or an immutable non-withdrawable seed. A release checklist is not a contract
invariant."* `docs/audit/REMEDIATION-GUIDE.md` (B-AUD-007 row) says only
*"Operational closure is not proven by this branch."* An operational disposition
is a decision to accept that requirement being unmet, which is a legitimate
owner call — provided the seed procedure it relies on actually covers the window.

Two details bear on whether it does:

- This branch adds `assert _initialSupply == 0` to `contracts/tokens/SavingsGreen.vy`.
  That is correct for SC-27, but it also makes an atomic constructor seed
  impossible: any seed is now a separate transaction, and the exposure window is
  whatever sits between deployment and that transaction. No RH migration seeds
  sGREEN — `migrations/robinhood-mainnet/` contains no sGREEN deposit.
- RH-mainnet sGREEN is already deployed at
  `0x290a52380A88f743813B8C3e9F6B0e61DB5FDF73` carrying pre-remediation source,
  so this PR's sGREEN changes only reach RH through a redeploy — and a redeployed
  sGREEN starts empty, opening the window at t=0.

The remedy pattern already exists in this codebase: `SharesVault` and `StabVault`
both use `DECIMAL_OFFSET = 10 ** 8`. sGREEN does not.

**Required before launch, not before merge:** confirm the recorded operational
gate explicitly covers (a) the redeploy case, since the currently deployed RH
sGREEN predates this remediation, and (b) the non-atomic seed, since the
constructor can no longer carry one. If the seed is a separate transaction, the
gate needs to state who executes it, in which block relative to enabling
deposits, and how the seed shares are made non-withdrawable. A virtual-share
offset would remove the dependency on procedure entirely and is the lower-risk
option if a Teller/AuctionHouse-style size constraint does not prevent it —
`Erc4626Token.vy` is not near the EIP-170 ceiling.

### 2. Remove the committed scratchpad file

`scratchpad/contributor-admin-state-live-evidence-2026-08-14.md` (299 lines,
added 2026-08-14 in `9a0f6e4`) is the only tracked file under `scratchpad/`, is
referenced by nothing in the repository, and describes itself in its first line
as *"Local, uncommitted evidence."*

This repository is **public**. The file publishes, in one place: live RipeHq and
registry addresses; the finding that every active registry, Switchboard,
price-source and HumanResources timelock reads zero; the explicit operational
consequence that *"A Safe MultiSend can therefore place registry start and
confirm calls in the same child transaction/block; there is no configured
observation delay"*; and the specific hardening missing from the live Contributor
blueprint.

The exposure already exists — the file has been public since 2026-08-14, so
merging does not create it. It should nonetheless be deleted, `scratchpad/` added
to `.gitignore`, and the zero-timelock condition handled as the separate
live-governance item the file itself recommends.

### 3. Rebind or retire the BasicVault consumer inventory

`tests/vaults/test_basic_vault_consumer_inventory.py` fails at this head — two of
three tests fail on a stale `contracts/core/AuctionHouse.vy` source hash. It runs
in no CI lane because `pytestmark = pytest.mark.artifact` (line 11) excludes it
from every marker expression. The marker landed 2026-08-15 (`1880fad`); the
change that invalidated the hashes landed 2026-08-17 (`c9ae47e`).

The failure is bookkeeping, not behavior — the inventory records which contracts
were reviewed for BasicVault consumer semantics, and `AuctionHouse.vy`
legitimately changed. Nothing in the protocol is broken. But a gate that is red
and unwatchable should be rebound against the current sources or retired by an
explicit decision, not shipped hidden.

## Finding dispositions

24 of 30 fixed in contract code; 3 partial; 1 accepted residual; 2 open.

| ID | Sev | Status | Basis |
| --- | --- | --- | --- |
| SC-01 | High | **Fixed** | Phase budget capped at `min(targetRepayAmount, userDebt.amount + keeperFee)` (`AuctionHouse.vy:352`) before any collateral moves; spread rate narrowed to the nominal base fee (`:340`); exact ceiling gross-up (`:736`). Mutation-proven. |
| SC-02 | High | **Fixed** | `greenAmount` clamped by live `getUserDebtAmount` per iteration (`AuctionHouse.vy:1164-1167`), applied before collateral sizing. Mutation-proven. |
| SC-03 | High | **Open, dispositioned** | No contract fix and no regression test. Carried as an operational launch gate per `PR-126-RH-MERGE-READINESS.md`. See above for the redeploy and non-atomic-seed specifics. |
| SC-04 | Med | Partial | Bounded `MAX_TRANSFER_DELTA = 2` tolerance on both deltas; shares recomputed from actual outflow (`SharesVault.vy:57-100`). Not an enforced asset exclusion. |
| SC-05 | Med | Fixed | Snapshot-ring resize no longer resurrects discarded slots. |
| SC-06 | Med | Fixed | All three `raw_call` sites bounded: 250k / 75k / 150k (`PriceDesk.vy:58-60`). |
| SC-07 | Med | Fixed | All five state-changing `Deleverage` externals are `@nonreentrant`; settlement re-reads debt after external interaction. |
| SC-08 | Med | Fixed | Fee-bearing retries cannot recharge the same economic liquidation. |
| SC-09 | Med | Fixed | Broad deleverage skips an unavailable stability cohort; strict paths stay atomic. |
| SC-10 | Med | Accepted | Whole-account quarantine retained by owner decision. See composition note below. |
| SC-11 | Med | Fixed | `_repayDebt` skips collateral revaluation entirely when debt reaches zero (`CreditEngine.vy:559-570`), so full repayment survives a total oracle outage. |
| SC-12 | Med | Fixed | Exit fee computed in asset terms against the live claim (`RipeGov.vy:828-895`). |
| SC-13 | Med | Fixed | Underscore callers bound to per-user grants; Deleverage no longer confers registry-only cross-user trust. |
| SC-14 | Med | Fixed | Sender checkpointed post-mutation and recipient after, on AuctionHouse, CreditEngine and Deleverage paths, withdrawal included. No missed path found. |
| SC-15 | Med | Partial | `range(1, 0)` revert closed on all six loops, so no user is bricked. The stale registration is never pruned (`Lootbox.vy:308` `continue` skips `vaultsToRemove`) and permanently occupies one of five `perUserMaxVaults` slots. |
| SC-16 | Med | Fixed | Danger duration requires a sustained safe window on a time-weighted ratio. |
| SC-17 | Med | Fixed | Snapshot weighting and zero-write throttle corrected. |
| SC-18 | Med | Fixed | Partner liquidity mints against tokens actually received. |
| SC-19 | Med | Fixed | Removal cap derived from real pool state via `calc_token_amount`. Real-pool proof runs only in a fork lane CI does not execute. |
| SC-20 | Med | Fixed | `min(nonzero global, nonzero feed)` applied to Chainlink, Pyth, RedStone, Stork. |
| SC-21 | Low | Partial | Future-timestamp guards added; RedStone's ETH-denominated leg still drops the caller's tighter bound. |
| SC-22 | Low | Fixed | Malformed-response and return-value handling corrected. |
| SC-23 | Low | Fixed | Stale fallback is age-bounded. |
| SC-24 | Low | Fixed | Rewards funded from attributable underlying rather than share units. |
| SC-25 | Low | Fixed | Price-source enumeration bounded. |
| SC-26 | Low | Fixed | Value-aware `lowestLtv`; the zero-balance LTV floor is preserved. |
| SC-27 | Low | Fixed | `assert _initialSupply == 0`. All chain configs already pass 0, so no migration breaks. |
| SC-28 | Low | Open | Hardcoded MCBETH = 1 wei and VVV = $2.40 fallbacks remain. Dormant — source not registered for RH. Gate before enabling. |
| SC-29 | Low | Fixed | VaultBook disabled-slot recovery restored. |
| SC-30 | Low | Fixed | Maximum discount attainable. Residual: `maxDiscount == 100%` would divide by zero at `AuctionHouse.vy:1196`; only `SwitchboardAlpha.vy:888` prevents it. |

## Deployability — EIP-170

Deployed runtime measured at this head, including immutables. The limit is 24,576
bytes. Everything deploys; nothing here blocks the merge.

| Contract | Deployed | Headroom |
| --- | ---: | ---: |
| AuctionHouse | 24,568 | **8** |
| Teller | 24,556 | **20** |
| SwitchboardAlpha | 24,506 | 70 |
| Lootbox | 24,444 | 132 |
| Deleverage | 24,424 | 152 |
| CreditEngine | 24,382 | 194 |
| Endaoment | 24,212 | 364 |

This is the most important structural fact about the merged system. Eight bytes in
AuctionHouse means the next security fix to the liquidation engine cannot be
written without removing something first, and the pressure is already visible in
the source. From `contracts/core/CreditEngine.vy`, on an invariant deliberately
left unenforced:

```
# Burning paths must always pass a nonzero address; passing zero would silently
# skip the burn. This is not asserted here because CreditEngine has effectively
# no EIP-170 headroom.
```

That invariant is not currently reachable — both call sites pass a real address
and `msg.sender` cannot be zero — but an unasserted invariant on GREEN burning is
a latent hazard. Elsewhere, `range(2) + break` loops are chosen over two
straight-line calls purely for bytecode size, annotated as such in-source.

Compounding this: the 200-byte minimum-headroom floor (RG-SIZE-01) and its
exact-artifact pinning were deleted in this branch, while six contracts sit below
that floor and Teller sits below its own previously ratified RH-D027 exception of
71 bytes. A Teller or AuctionHouse decomposition should be treated as scheduled
work, not a footnote.

## Whole-system observations

**Quarantine composition (Medium, open).** A single positive-LTV asset with no
usable price sets `hasQuarantinedAsset`, which now simultaneously blocks
borrowing, liquidation, redemption and deleverage for that account, while
repayment stays available via the SC-11 fix. The asymmetry is defensible — the
borrower can always exit, and the protocol refuses to act on collateral it cannot
value — but a feed outage on one admitted asset makes positions unliquidatable
for its duration. SC-10's acceptance was recorded on narrower grounds than the
behavior now covers. This strengthens the case for enforcing usable feed coverage
before an asset receives a positive LTV.

**`Teller.setUserConfig` default arguments inverted (Medium, undisclosed).**
Commit `bc515be` flipped `_canAnyoneDeposit`, `_canAnyoneRepayDebt` and
`_canAnyoneBondForUser` from `True` to `False`. `setUserConfig(user)` with
defaults now *revokes* where it previously *granted*. The selector is unchanged,
so nothing signals the reversal to an existing caller. The change is intentional,
coherent with that PR's fail-safe intent, and covered by a test — but it is absent
from the PR body's behavior section and from `docs/`. Integrators and the
frontend should be told before this ships.

**Deployment atomicity is not encoded anywhere executable (Medium).** The
`UserBorrowTerms` struct gained a field and is decoded across CreditEngine,
AuctionHouse, Deleverage and CreditRedeem. Endaoment↔SwitchboardEcho,
Teller↔Deleverage↔SwitchboardDelta, Boardroom↔MissionControl↔RipeGov,
VaultBook↔MissionControl↔Ledger and Lootbox↔MissionControl are newly coupled.
This is one atomic deployment unit, and `tests/deployment/test_dependency_gate.py`
was deleted in the same branch. The contract set that must deploy together needs
to be written down and checked by a person.

**Keeper batch sizes far exceed their qualification (Medium, disclosed).**
`Teller.vy:219,222` expose `MAX_LIQ_USERS = 50` and `MAX_DELEVERAGE_USERS = 25`;
`tests/registries/price_desk_aggregate_qualification.py:41-42` qualifies 2 and 3
against a 32M limit under a saturated nine-asset topology, with a measured OOG at
N+1. The repository states plainly that it has no keeper batch-size config and
that larger batches are a manual operations gate. The qualified figures are a
saturated worst case, not the expected RH topology, but the operator limit should
be owned before keepers run.

**SC-04 / DER-03 exit reverts reach liquidation.** Neither `AuctionHouse.vy` nor
`Deleverage.vy` contains a `raw_call`, so a vault withdrawal revert propagates and
aborts the whole liquidation or deleverage transaction. The
`# dev: remaining holder loss` path in `SharesVault.vy` is therefore a
liquidation-liveness concern, not only a withdrawal-UX one. It is gated by asset
admission: the affected Base assets were observed deposit-disabled with zero
shares, and RH uses the simple ERC-20 vault. Treat it as an enablement gate.

## Gates that no longer run in CI

Not defects, but the evidence base is narrower than a green run suggests:

- The checked-in ABIs **do** match the compiled contracts — verified by running
  `tests/deployment/test_abi_export.py` directly. Those three tests were marked
  `artifact` by this branch and now run in no automatic lane, so future drift
  will not be caught.
- `-m fork_qualification` collects zero tests without `--fork base`. The sixteen
  fork tests behind it — including the SC-04 qualification module and the SC-19
  real-pool proof — execute in no CI job. This is accurately disclosed in the
  derived register; the proofs are manual-only.
- 22 newly added gas tests in `tests/registries/` run in no CI job.
- The required `deployment-controls` job gained a marker expression the base did
  not have, dropping several tests from the required gate.
- RH-D037 and RH-D039 through RH-D042 are allocated to merged PRs in
  `decision-register.md:1132-1134` but have no decision bodies.
  `scripts/check_rh_decision_ids.py` validates uniqueness only, so it passes.

## Merge-gating vs launch-gating

Merge-gating: the three pre-merge items above.

Launch-gating, and explicitly **not** addressed by merging this PR: live zero
timelocks across registries/Switchboard/HR; the PriceDesk registry slot-3
divergence (repository expects BlueChipYieldPrices, live was Uniswap V2 Prices);
admitted equity LTV and containment configuration; per-feed stale-time inventory;
the nested BlueChip/PriceDesk topology; and the sGREEN seed procedure if SC-03 is
accepted rather than fixed. Each requires a read against live chain state.
Repository intent is not evidence for any of them.

## Sequencing

1. Delete the scratchpad file; add `scratchpad/` to `.gitignore`.
2. Rebind or retire the BasicVault consumer inventory.
3. Re-run CI on the resulting head, then fast-forward `rh`.
4. Announce the `setUserConfig` default change to Teller integrators.
5. Before launch, not before merge: confirm the SC-03 operational gate covers the
   redeploy window and the non-atomic seed.

PR #156 (Instant Bond Lane) has already merged this branch into itself, so landing
#126 first reduces that PR to its feature diff. This is the correct order.

## Reproducing the checks

```
# deployed runtime sizes incl. immutables
pytest "tests/vaults/test_basic_vault_quarantine.py::test_changed_contract_deployed_runtime_sizes_include_immutables" -s
pytest tests/test_vault_pointer_runtime_sizes.py

# ABI currency (excluded from CI by the artifact marker)
pytest tests/deployment/test_abi_export.py -o addopts="" -m artifact

# the red, CI-invisible inventory gate
pytest tests/vaults/test_basic_vault_consumer_inventory.py -o addopts=""

# SC-01 conservation regressions
pytest tests/core/auctionHouse/test_ah_liq_sgreen.py tests/core/auctionHouse/test_ah_keeper_accounting.py
```

Set `RIPE_BOA_CACHE_DIR` to a writable directory if collection aborts.

Mutation procedure used for SC-01 and SC-02: check the head out into a throwaway
worktree, revert the single guard, re-run the named suite, confirm failure,
destroy the worktree. Reverting SC-01's `:352` ceiling reproduces the audit's
worked example exactly — 94.5 GREEN burned against 91 GREEN of creditable debt on
a 90-debt position.
