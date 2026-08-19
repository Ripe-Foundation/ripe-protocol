# Group 10 implementation guide

> **Owner decision, 2026-08-19 — current StabVault membership policy.**
> This supersedes row B’s call-site-only placement of the live-share
> residual guard, supersedes row B’s GREEN exclusion, and supersedes
> row E only for microscopic residuals. Sticky membership remains for
> meaningful live residuals. Live-prune stays a no-op for every nonzero
> row. Activation stays empty-cohort-only. There is no
> governance-controlled live activation route.
>
> Residual membership is centralized in `_reduceClaimableBalances` and
> applies to claim, redeem, and `swapWithClaimableGreen`:
>
> - `LIVE_RESIDUAL_DIVISOR = 10**10`
> - inclusive `R <= P // D`, where `P` is `_prevClaimableBalance` and
>   `R` is the new pair balance after `_claimAmount`
> - zero residual → `DEACTIVATION_ZERO`
> - empty-cohort priced residual below `$0.05` → `DEACTIVATION_DUST`
> - live microscopic residual below `$0.05` (`R <= P // D`) →
>   `DEACTIVATION_DUST`
> - live meaningful residual below `$0.05` → remain active
> - zero/unavailable remaining USD → never classified as dust
>
> Deactivation removes active-list membership only. It does not erase a
> nonzero pair balance, aggregate liability, or custody. A later receipt
> may accumulate onto the dormant residual and reactivate it normally.
>
> **Operational recovery:** meaningful dormant balances can be consumed
> through configured redemption after the oracle price is correct. Do
> not redeem while the oracle remains wrong-low. Before removing a
> former claim asset’s price feed, verify
> `totalClaimableBalances[asset] == 0` and that no active row depends
> on it.
>
> **Test node ID mapping** (names that stated the opposite of the
> current assertions; historical citations below keep the old IDs):
>
> - `test_g10_1b_low_quote_prune_then_deposit_captures_omitted_value`
>   → `test_g10_1b_low_quote_prune_then_deposit_cannot_capture_omitted_value`
> - `test_prune_reenables_share_actions_while_claim_custody_is_still_short`
>   → `test_prune_does_not_reenable_share_actions_while_claim_custody_is_still_short`
> - `test_g10_low_quote_prune_lets_new_depositor_capture_restored_claim_nav`
>   → `test_g10_low_quote_prune_does_not_let_new_depositor_capture_restored_claim_nav`
> - `test_high_quote_activate_lets_an_exiting_holder_take_phantom_value`
>   → `test_high_quote_activate_does_not_let_an_exiting_holder_take_phantom_value`
> - `test_prune_reenables_share_actions_positive_control_full_custody`
>   → `test_full_custody_share_actions_remain_available_after_live_prune_noop`
> - `test_low_quote_prune_moves_value_from_existing_to_new_shareholders`
>   → `test_low_quote_live_prune_does_not_move_value_between_existing_and_new_shareholders`
> - `test_prune_reenables_liquidation_acceptance_while_custody_is_short`
>   → `test_prune_does_not_reenable_liquidation_acceptance_while_custody_is_short`
> - `test_g10_low_quote_prune_withdrawal_delta_is_realizable`
>   → `test_g10_low_quote_live_prune_does_not_create_meaningful_withdrawal_capture`
> - `test_g10_pruned_dormant_pile_remains_claimable_by_funded_shareholder`
>   → `test_g10_dormant_receipt_remains_claimable_by_funded_shareholder`
> - `test_g10_high_quote_activate_inflates_dormant_pile_into_nav`
>   → `test_g10_high_quote_live_activation_does_not_inflate_dormant_pile_into_nav`
> - `test_g10_dust_prune_then_thin_claim_still_delivers`
>   → `test_g10_dormant_receipt_thin_claim_still_delivers`
> - `test_g10_dormant_pruned_claim_still_delivers_for_funded_holder`
>   → `test_g10_dormant_receipt_still_delivers_for_funded_holder`
> - `test_cap_rejects_new_receipt_then_prune_allows_activation`
>   → `test_cap_rejects_new_receipt_then_zero_claim_frees_slot_for_activation`
>
> The historical work order below remains the 2026-08-18 Group 10
> implementation trail (rows A–G, call-site `remainingUsdValue = 0`,
> GREEN out of scope). Do not treat those superseded rows as the
> current production policy.

## Historical work order — superseded 2026-08-19

Work order for a **fresh agent**. Not a second audit. **Read this
entire file once before any edit.** The traps are pre-classified
here (`test_der02_*`, the three `_reduceClaimableBalances` callers,
last-share ordering, empty-cohort setup). Skimming will miss them.

This file is enough to implement. The combined report is why-only,
optional. Do not edit the report, the four source reports, the
brief, or the DER-02 register.

This ticket **authorizes** the allowlisted `StabVault.vy` and test
edits. That supersedes the brief’s “do not patch production
contracts.” A–G are **already approved**. Implement those
defaults.

**This is not a rewrite.** Three `continue`s in
`_maintainClaimableAssets`, two `remainingUsdValue = 0` assigns,
one compare in `canActivateClaimAsset`, one comment typo. Do not
redesign StabVault. Do not add helpers, storage, or exports.

**Work in a new worktree and a new branch**
([Fresh worktree](#fresh-worktree)). Do not edit the dirty audit
checkout.

574 bytes of StabilityPool headroom is **unproven** until these
hunks compile. Measure after each contract edit, **before** the
test rewrites. A size ping on the first reply is fine. Do not
pick a weaker patch to fit.

---

## Decision record (7 rows)

| # | Item | Recommended default | Owner |
| ---: | --- | --- | --- |
| A | **#1b-i** live-share prune guard | **Yes.** | APPROVED (owner 2026-08-18) |
| B | **#1b-i claim/redeem** — zero `remainingUsdValue` when shares remain, **only** at the two quote-derived call sites | **Yes, extend at call sites.** Do **not** put the guard in `_reduceClaimableBalances`. Do **not** change `swapWithClaimableGreen`. | APPROVED — extend at call sites (owner 2026-08-18) |
| C | **#1a** prune-time custody skip | **Yes.** Per-asset, `continue` not revert. | APPROVED (owner 2026-08-18) |
| D | **#1b-ii** live-share activate gate | **Yes.** Not a global no-op. | APPROVED (owner 2026-08-18) |
| E | **20-cap sticky** while shares remain; AH skip-at-cap unmeasured (Group 1) | **Accept.** Launch pair is `(sGREEN, WETH)`. Require the two-arm cap test. | APPROVED (owner 2026-08-18) |
| F | **Empty-cohort prune stays** (G5-1 interaction) | **Accept.** G5 still owns last-exit capture. | APPROVED (owner 2026-08-18) |
| G | **Test-scope expansion** as listed below | **Yes.** | APPROVED (owner 2026-08-18) |

`_shouldRaise=True` is **not** a fix (`PriceDesk.vy:178-181` raises
only when `price == 0`). Do **not** drop `activateClaimAssets` from
`StabilityPool` exports. Do not edit the register, the DV-15 xfail
reason, or
`test_der02_deployment_manifests_bind_recovery_control_and_scope`.
A global activate no-op is **rejected** (DER-02 / PR #174):
recovery still runs when `totalBalances == 0`.

The live-share signal is **cohort** `totalBalances[stab]` (share
supply), not “the caller holds shares.”

**Residuals (do not “fix”):**

1. `_addClaimableBalance` can still seat on a wrong-high **receipt**
   quote (Groups 1 / 7).
2. Empty-cohort membership → G5 finding 1. Last-exit capture
   already works without prune. Empty-cohort prune can still feed
   it. Do not refuse empty-cohort prune to “help” G5. Do not
   implement `numClaimablePairs`.
3. `swapWithClaimableGreen` (`StabVault.vy:597`) still dust-unlists
   leftover GREEN `< RETENTION`. GREEN is 1:1 — no oracle. Do not
   edit AuctionHouse.vy.
4. AuctionHouse routing at 20 active is **unmeasured** (Group 1).

Owner confirmed 2026-08-18 — do not reopen: last-share claim may
still dust-unlist (post-burn `totalBalances`; do **not** check
before the burn). Claim vs redeem asymmetry is accepted. 20-cap
stays sticky while shares remain. Empty-cohort prune stays.
#1a is `continue`, not revert. Paused activate while shares
remain is a no-op; DER-02 recovery is empty-cohort only.

---

## Goal

| # | Combined rank | Edit |
| ---: | --- | --- |
| 1 | #1b-i | Prune: no dust-delist of a nonzero pair while the cohort has shares. Zero `remainingUsdValue` at the claim + redeem call sites (row B). |
| 2 | #1a | Prune: skip dust-delist when `balanceOf < totalClaimableBalances` |
| 3 | #1b-ii | Activate: skip `_registerClaimableAsset` while the cohort has shares. Empty-cohort seating unchanged. Align `canActivateClaimAsset`. |

Land 1, 2, and B in one StabVault pass (Order step 3). Then 3
(Order step 4). The listing below is the **final** body — three
inserts into today’s function, not a rewrite. Rewrite tests
**once** against that policy (Order step 5).

Comment at `StabVault.vy:1376`:
`< $0.10` → `RETENTION` `$0.05`.

Do **not** implement Group 5 finding 1. Do not put dormant into NAV.
Do not flip `_shouldRaise=True` on prune / activate.

**Goal, stated honestly:** a fail-soft (or claim/redeem-derived) dust
quote must not hide a **nonzero** pre-existing pile from the NAV used
to mint new shares **while `totalBalances[stab] != 0`**, via prune
and via the two quote-derived `_reduceClaimableBalances` callers.
Empty-cohort membership, receipt-path seating, and GREEN
`swapWithClaimableGreen` are out of that sentence.

---

## Size — stop and tell the owner

Pin table at required HEAD
`3822a59273a3b1baaff5831d288954ac2c072fc6`
(`vyper==0.4.3` / `titanoboa==0.2.7`):

| Contract | Runtime | Headroom | This ticket |
| --- | ---: | ---: | --- |
| **StabilityPool** (compiles `StabVault`) | 24,002 | **574** | all hunks |
| AuctionHouse | 24,568 | 8 | **do not edit** |
| Teller | 24,556 | 20 | **do not edit** |
| Ledger | 13,306 | ample | **do not edit** |

`# pragma optimize codesize` is already on `StabilityPool.vy`.

**Pre-edit measure** — print
`len(stability_pool.env.get_code(address))` from
`test_deployed_runtime_fits_eip170 -s`. Record that number in the
completion reply.

This ticket should **grow** a little: two `totalBalances` continues
in `_maintainClaimableAssets`, two call-site `remainingUsdValue = 0`
assigns, one compare in `canActivateClaimAsset`.

After **each** contract hunk, run both size tests (`-s`). That run
**is** the compile check. The activate and prune branches each
declare their own `custody: uint256` (same pattern as today’s
`usdValue`). Do not spend time on a suspected Vyper scoping issue;
if it compiles in boa, it compiles.

**Between hunks, before the final pin update,**
`test_vault_pointer_runtime_sizes.py` **will fail** on
`EXPECTED_RUNTIME_BYTES` drift for StabilityPool. That exact
mismatch is the only acceptable pin-test failure. The EIP-170
hardening node (`len(runtime) <= EIP170_LIMIT`) must stay **green**
the whole time. Do not change either comparison
(`size >= EIP170_LIMIT` in the pin test, `<= EIP170_LIMIT` in
hardening). Exact 24,576 is an owner ping.

**Edit the StabilityPool pin once**, after all hunks. Teller must
stay **24,556**. AuctionHouse must stay **24,568**.

If **any** hunk would push StabilityPool to 24,576, or if you are
tempted to drop, weaken, relocate, or skip a prescribed check to
make it fit — **stop immediately and tell the owner.** Do not pick
a weaker patch.

Owner ping: which item; runtime before → after; the hunk you then
**removed**; what you did not do; what is already landed.

Do not deploy. Redeploy is a later RipeHq swap.

---

## Fresh worktree

Do **all** contract and test edits in a **new git worktree and a
new branch**. Do not edit
`/Users/wigglez/dev/ripe-protocol-user-flow-audit`
(`docs/rh-user-flow-audit-priority` — dirty, other groups). Do not
work in `/Users/wigglez/dev/ripe-protocol` or
`/Users/wigglez/dev/ripe-protocol-rh`.

Start point is the contract baseline
`3822a59273a3b1baaff5831d288954ac2c072fc6` (this guide’s size pin).
The dirty audit checkout may be a docs-only commit ahead of that;
`StabVault.vy` / `StabilityPool.vy` are identical. This guide and
the combined report are **not** in that commit. Copy **only** those
two files. Do not copy other dirty / untracked files.

```
SRC=/Users/wigglez/dev/ripe-protocol-user-flow-audit
WT=/Users/wigglez/dev/ripe-protocol-user-flow-audit-g10-impl
PIN=3822a59273a3b1baaff5831d288954ac2c072fc6

test ! -e "$WT" || { echo "worktree path exists; stop"; exit 1; }
git -C "$SRC" worktree add -b impl/g10-stab-claim-membership "$WT" "$PIN"
cp "$SRC/docs/chains/rh/user-flow-audit-group-10-implementation.md" \
   "$SRC/docs/chains/rh/user-flow-audit-group-10-report-combined.md" \
   "$WT/docs/chains/rh/"
cd "$WT"
```

Required after that:

- `pwd` is `$WT`
- `git branch --show-current` prints `impl/g10-stab-claim-membership`
- `git rev-parse HEAD` prints `3822a59273a3b1baaff5831d288954ac2c072fc6`
- `git status --short` shows **only** those two docs
- `git diff HEAD -- contracts/vaults/modules/StabVault.vy contracts/vaults/StabilityPool.vy` is empty
- `numClaimablePairs` is not in StabVault

If `$WT` already exists on `impl/g10-stab-claim-membership` at
`$PIN` with a clean contract tree, use it. If the path exists on
a different branch, or `status` shows unrelated files, **stop**.
Do not recreate over a dirty tree. Do not edit `$SRC` after this.

**Hard stop.** If HEAD is not `$PIN`, or StabVault /
`_maintainClaimableAssets` / `_reduceClaimableBalances` /
`swapWithClaimableGreen` have drifted, stop for re-review. Do not
“just re-measure.”

No `.venv` here. Interpreter and cache:

```
RIPE_PYTHON=/Users/wigglez/dev/ripe-protocol/.venv/bin/python
RIPE_BOA_CACHE_DIR="${TMPDIR:-/tmp}/ripe-boa-cache-g10"
```

First run against a fresh cache is a cold titanoboa compile (~30s;
not a hang). Always:

```
env -u PYTHONPATH -u VIRTUAL_ENV RIPE_BOA_CACHE_DIR="$RIPE_BOA_CACHE_DIR" \
  "$RIPE_PYTHON" -m pytest
```

If a line number has drifted **and** HEAD is still `$PIN`, trust
the file.

In `$WT` only: undo a bad StabVault hunk with
`git checkout -- contracts/vaults/modules/StabVault.vy`, then
re-apply. Do not `git clean -fd` (deletes the copied untracked
guide). Do not `git reset --hard`. Do not `git add`, commit,
push, PR, or deploy unless the owner asks.

---

## Allowlist

**Edit:**

- `contracts/vaults/modules/StabVault.vy`
- Tests listed below. Do not add test **files**. Adding the named
  nodes to `test_g10_prune_activate_proofs.py` is required.

**Protected / read-only (do not edit):**

- `contracts/vaults/StabilityPool.vy` — keep `activateClaimAssets`
  exported; do not export `canActivateClaimAsset` (D-13).
- AuctionHouse, Ledger, PriceDesk, Teller, Defaults, BluePrint
- All Group 5 test files (`test_g5_*`, `test_user_flow_audit_group5.py`)
- Reports, brief, DER-02 register, this guide (except a command
  that is wrong in `$WT`)

**Rewrite setup / obsolete characterization only** (see
[What to rewrite](#what-to-rewrite)):

- `tests/vaults/modules/test_g10_prune_activate_proofs.py`
- `tests/vaults/modules/test_user_flow_audit_group10_codex.py`
- `tests/vaults/modules/test_user_flow_audit_group10.py`
- `tests/vaults/modules/test_user_flow_group10_stab_maintenance.py`
- Hardening nodes in [Hardening](#hardening-nodes)
- `tests/vaults/modules/test_stab_vault_claims.py::test_dust_deactivated_pair_with_residual_balance_remains_claimable`
- `tests/vaults/modules/test_stab_vault_claim_data_fuzz.py` — update
  the in-test **model** to the new membership rules (named below).
  File already uses `@settings(derandomize=True)`. Green = one
  clean run of all four nodes. Do not chase a flake into a
  contract change; do not drop `derandomize=True`.
- `tests/test_vault_pointer_runtime_sizes.py` — StabilityPool pin,
  once at the end

---

## What to rewrite

Safety-property tests that already assert “must not capture / must
stay blocked / must not seat” **pass after the fix**. Remove
`xfail` where that was the only reason they were yellow. **Do not
rewrite the property assert.**

Rewrite only:

- setup that used live-share prune/activate to *create* a state
  the new rule will not produce
- obsolete characterization numbers (`$4` / `$5` / `$50` capture,
  “state became DORMANT” after a live-share prune)
- “measure the bypass” blocks that assert a successful withdraw

Never weaken the contract to turn a test green. Enumerate every
node you touched in the completion reply.

---

## Claim/redeem — call sites only (row B)

`_reduceClaimableBalances` has **three** callers:

| Line | Caller | Remaining USD | Oracle? |
| ---: | --- | --- | --- |
| 597 | `swapWithClaimableGreen` (AuctionHouse only) | `maxClaimableGreen - amount` (GREEN 1:1) | **No** |
| 801 | `_claimFromStabilityPool` | quote-derived | Yes |
| 1047 | redeem loop | quote-derived | Yes |

Row B is approved as **extend at call sites**. Do **not** edit the
helper. After computing `remainingUsdValue`, insert the matching
snippet. The names differ:

```vyper
# claim (`_claimFromStabilityPool`, after :800)
if vaultData.totalBalances[_stabAsset] != 0:
    remainingUsdValue = 0
```

```vyper
# redeem loop (`_redeemFromStabilityPool`, after :1046, before :1047)
if vaultData.totalBalances[stabAsset] != 0:
    remainingUsdValue = 0
```

Redeem’s local is `stabAsset` (`StabVault.vy:1027`), not `_stabAsset`.
Do not copy the claim snippet into the redeem loop.

The helper’s dust branch already requires `_remainingUsdValue != 0`,
so a live book will not dust-unlist. Zero-balance remove is
untouched. `swapWithClaimableGreen` is untouched.

**Last-share ordering (claim only).** `_reduceBalanceOnWithdrawal`
(`StabVault.vy:791`) decrements `totalBalances` **before** the
claim-site assign at `:801`. A claim that burns the last shares
sees `totalBalances == 0` and may still dust-unlist. That is
empty-cohort delist (G5), not the while-shares capture. **Do not**
save a pre-burn flag or check shares before the burn. Redeem
does not burn stab shares in that helper; the cohort-supply check
is the live-book signal.

**Discriminating proofs** (add to
`test_g10_prune_activate_proofs.py`):

- `test_g10_partial_claim_wrong_low_quote_keeps_row_active`
  — sliver claim at a wrong-low quote; residual ≠ 0; shares remain;
  state stays ACTIVE.
- `test_g10_partial_redeem_wrong_low_quote_keeps_row_active`
  — same membership consequence on redeem.
- `test_g10_partial_claim_then_deposit_does_not_capture`
  — two arms, `boa.env.anchor()`. Both arms use the **same** sliver
  claim amount, shares burned, ERC-20 custody, residual pair
  balance, and honest price restoration. The only isolation
  variable is list membership (old bug: attack unlists, control
  does not). After this ticket both arms stay ACTIVE, so later
  depositor withdraws match (≤ 1 wei). If amount / shares /
  custody / residual / restored price are not identical across
  arms, the comparison is confounded — fix the fixture, not the
  bound. Do not invent a third “force unlist” arm.
- `test_g10_swap_with_claimable_green_still_dust_unlists`
  — partial GREEN consume leaving `< RETENTION` still dust-unlists
  (policy unchanged). Use existing
  `swapWithClaimableGreen` fixtures / impersonation as the suite
  already does.

---

## G5 — report-only, expected reds

G10 does **not** fix G5. Do **not** edit G5 files. Do **not** invert
G5 safety properties.

**Pre-edit baseline** (save the failed node ids + first assert /
revert string):

```
g10_pytest tests/vaults/modules/test_g5_stab_zero_share_deposit.py
g10_pytest tests/vaults/modules/test_user_flow_audit_group5.py
g10_pytest tests/vaults/modules/test_g5_liq_price_batch_proofs.py
```

At HEAD `3822a59` the draft-2 “G5 smoke” was already **10 passed /
2 failed**. Those two are G5 open properties, not G10 regressions:

- `test_g5_stab_zero_share_deposit.py::test_nonzero_deposit_must_not_commit_custody_with_zero_shares`
- `test_user_flow_audit_group5.py::test_group5_appreciated_dormant_value_cannot_be_captured_after_zero_share_exit`

The whole `test_user_flow_audit_group5.py` file has more expected
reds (G5 findings 1 and 3). After G10, compare to the pre-edit
list. **Same node + same failure signature = OK.** A previously
**passing** G5 node that now fails, or a red whose revert/assert
changed, is a stop-and-ping.

The live-share **activate** gate should not break G5 fixtures that
activate after `totalBalances == 0` (zero-share fixture,
post-exit activate). Those fixtures are how G5 *builds* some reds.
If a G5 **setup** breaks, stop and ping — do not rewrite G5.

---

## Final `_maintainClaimableAssets` (after Order steps 3 and 4)

Today’s function is `StabVault.vy:1243-1279`. Insert three
`continue`s. Do not restructure the loop. The listing is the
end state (prune guards **and** the activate gate). Do not ship
the prune half and leave activate as today.

Insert 1 — first lines inside `if _shouldActivate:`:

```vyper
            if vaultData.totalBalances[_stabAsset] != 0:
                continue
```

Insert 2 and 3 — after the `balance == 0` remove, **before**
`usdValue = self._getUsdValue(...)`:

```vyper
        if vaultData.totalBalances[_stabAsset] != 0:
            continue

        custody: uint256 = staticcall IERC20(claimAsset).balanceOf(self)
        if custody < self.totalClaimableBalances[claimAsset]:
            continue
```

End state (paste-check):

```vyper
@internal
def _maintainClaimableAssets(_stabAsset: address, _claimAssets: DynArray[address, MAX_CLAIM_ASSET_MAINTENANCE], _shouldActivate: bool):
    greenToken: address = empty(address)
    savingsGreen: address = empty(address)
    priceDesk: address = empty(address)
    greenToken, savingsGreen, priceDesk = self._getStabAddys()

    for claimAsset: address in _claimAssets:
        if _shouldActivate:
            # live book: fail-soft quote must not seat a pair onto NAV
            if vaultData.totalBalances[_stabAsset] != 0:
                continue

            pairBalance: uint256 = self.claimableBalances[_stabAsset][claimAsset]
            if pairBalance == 0 or self.indexOfClaimableAsset[_stabAsset][claimAsset] != 0:
                continue

            custody: uint256 = staticcall IERC20(claimAsset).balanceOf(self)
            priorLiability: uint256 = self.totalClaimableBalances[claimAsset]
            assert custody >= priorLiability # dev: claim custody deficit

            usdValue: uint256 = self._getUsdValue(claimAsset, pairBalance, greenToken, savingsGreen, priceDesk, False)
            if usdValue < ACTIVATION_USD_THRESHOLD:
                continue

            if self._getNumActiveClaimAssets(_stabAsset) >= MAX_ACTIVE_CLAIM_ASSETS:
                continue

            self._registerClaimableAsset(_stabAsset, claimAsset)
            continue

        if self.indexOfClaimableAsset[_stabAsset][claimAsset] == 0:
            continue

        balance: uint256 = self.claimableBalances[_stabAsset][claimAsset]
        if balance == 0:
            self._removeClaimableAsset(_stabAsset, claimAsset, DEACTIVATION_ZERO)
            continue

        # live book: fail-soft dust quote must not hide a nonzero pile
        if vaultData.totalBalances[_stabAsset] != 0:
            continue

        custody: uint256 = staticcall IERC20(claimAsset).balanceOf(self)
        if custody < self.totalClaimableBalances[claimAsset]:
            continue

        usdValue: uint256 = self._getUsdValue(claimAsset, balance, greenToken, savingsGreen, priceDesk, False)
        if usdValue != 0 and usdValue < RETENTION_USD_THRESHOLD:
            self._removeClaimableAsset(_stabAsset, claimAsset, DEACTIVATION_DUST)
```

Wrappers stay as they are. Prune: **skip** (`continue`), do not
revert the batch. Activate still **reverts** the batch on deficit.
Do not add a global `totalClaimableBalances` walk (`:106` is not
enumerable). Zero-balance remove skips both new compares.
`totalBalances` is share supply, not ERC-20 custody.

### `canActivateClaimAsset` — align, do not delete

Module-only (`StabVault.vy:1204`). Change **only** the return
predicate (`:1212`):

```vyper
    return (
        vaultData.totalBalances[_stabAsset] == 0
        and usdValue >= ACTIVATION_USD_THRESHOLD
        and capacityRemaining != 0
    ), usdValue, capacityRemaining
```

**Pause is not modeled** (pre-existing, keep it). Add one comment
on the function: `# pause not modeled; execute still asserts isPaused`.
Custody deficit still reverts. Do not export. Do not delete
`_getClaimAssetActivationData`. Update
`test_g10_can_activate_helper_not_exported_and_source_semantics`.

---

## Empty-cohort setup (do not “just withdraw”)

Active nonzero claim value is **in NAV**
(`_calcWithdrawalSharesAndAmount`, `StabVault.vy:435`). An ordinary
max stab withdraw will **not** burn the last shares and leave those
rows active.

Proven sequence (G5
`test_g5_stab_zero_share_deposit.py::zero_share_cohort_with_priced_claimable`):

1. Receive the pair **below** `ACTIVATION` so it stays dormant.
2. Fully exit. Dormant is omitted from NAV, so last shares burn.
3. Appreciate the inventory above `$0.10`.
4. Pause and `activateClaimAssets` while `totalBalances == 0`.
5. Then apply dust pricing / deficit / prune as the test needs.

Use this for every “empty cohort + active row” arm, including #1a
and the empty cap arm. Do **not** take a live 20-active book and
withdraw it to zero expecting 20 rows to remain.

---

## #1a — dedicated empty-cohort proofs

The live-share prune guard **short-circuits before** the custody
compare. Existing #1a nodes that keep Bob’s shares prove **#1b-i
retention**. Keep their property asserts (stay blocked). Add these
nodes in `test_g10_prune_activate_proofs.py`, using the sequence
above:

- `test_g10_1a_empty_full_custody_dust_prune_delists`
  — empty + whole custody + dust quote → `DEACTIVATION_DUST`;
  `getTotalValue` is stab-only (0 if no stab left).
- `test_g10_1a_empty_custody_deficit_dust_prune_keeps_active`
  — same, then 1-wei impersonated transfer out; prune does not
  delist; `getTotalValue` / later deposit still
  `claim custody deficit`.
- `test_g10_1a_empty_batch_short_row_skips_safe_row_continues`
  — two activated dust pairs on the empty cohort; only A is short;
  prune `[A, B]`; A stays; B delists; no batch revert.
- `test_g10_1a_empty_cross_cohort_global_deficit_blocks_prune`
  — empty cohort A and live cohort B share a claim asset;
  `balanceOf < totalClaimableBalances[asset]`; empty-cohort prune
  of A’s pair skips.

Keep `test_custody_deficit_blocks_share_actions_without_the_prune`.

---

## 20-cap — two arms, one node

`test_g10_live_cap_blocks_21st_and_empty_dust_prune_frees_slot`
in `test_g10_prune_activate_proofs.py`:

**Live arm:** 20 active pairs, shares remain. 21st new-asset
receipt reverts `max active claim assets`.
`canAcceptLiquidationAsset` is False for a fresh probe. Dust-quote
prune of an occupant is a no-op (count stays 20).

**Empty arm (separate fixture, do not withdraw the live 20):**

1. 20 below-floor receipts (stay dormant).
2. Last-exit (dormant omitted from NAV).
3. Donate **at least one unit** of stab custody back to the pool
   (transfer from the whale). After a full exit
   `_getUnreservedBalance` is 0 and `swapForLiquidatedCollateral`
   reverts `nothing to transfer` (`StabVault.vy:558`).
4. Appreciate all 20 above `$0.10`.
5. Pause. `activateClaimAssets` takes at most
   `MAX_CLAIM_ASSET_MAINTENANCE = 15` addresses per call
   (`StabVault.vy:116`). Activate as **15 + 5** (two calls), not
   one call of 20.
6. Dust-quote prune of one full-custody occupant (one address is
   enough). Count becomes 19.
7. **Unpause** before the 21st receipt. `swapForLiquidatedCollateral`
   asserts `not vaultData.isPaused`.
8. 21st receipt succeeds.

That is the accepted residual made visible, not a Group 1 audit.

---

## DER-02 nodes (not one blanket)

| Node | Effect | Instruction |
| --- | --- | --- |
| `test_der02_deployment_manifests_bind_recovery_control_and_scope` | Frozen manifests + source markers | Must stay green. Do not touch. |
| `test_der02_appreciated_post_exit_dormant_pair_uses_paused_activation` | Asserts `totalBalances == 0` before activate | Must stay green. Do not touch. |
| `test_der02_direct_creation_exit_and_replenishment_partitions` | Below-floor / threshold receipts, no live-share dust-prune | Must stay green. Do not touch. |
| `test_der02_direct_dormant_claim_value_accrues_to_current_share_cohort` | Dormant claim math | Must stay green. Do not touch. |
| `test_der02_dormant_price_sensitivity_and_replenishment_reactivation` | Dormant stays dormant across price; receipt reactivates | Must stay green. Do not touch. |
| `test_der02_multiple_dormant_pairs_remain_non_iterable` | Below-floor receipts | Must stay green. Do not touch. |
| `test_der02_active_to_dormant_multi_holder_exit_orders` | **Will fail.** Live-share prune at `retention_price - 1` is fixture mechanics to create dormancy, not DER-02 policy | **Pre-authorized:** re-seed dormancy with a below-floor receipt (or an empty-cohort dust prune after the G5 sequence). Keep the node id and the exit-order / unpaid-dormant asserts. |
| `test_dormant_dust_remains_recoverable_after_full_exit` | DV-15 strict xfail | See [DV-15](#dv-15). Do not rewrite. |

If any **non-authorized** `test_der02_*` fails, stop and ping.

---

## DV-15

`pytest.mark.xfail(strict=True)` accepts **any** failure, so
“failed for a new reason” is invisible on a normal run.

**Pre-edit and post-edit:**

```
g10_pytest --runxfail \
  tests/vaults/modules/test_stab_vault_hardening.py::test_dormant_dust_remains_recoverable_after_full_exit
```

Expected today: full exit succeeds; the following
`claim_from_stability_pool` reverts inside
`_claimManyFromStabilityPool` at
`assert totalUsdValue != 0 # dev: nothing claimed`
(`StabVault.vy:749`). It does **not** reach a later `== dust`
balance assert. After G10 the failure stage must be that **same
claim-time revert**. If withdraw now reverts, the revert string
changes, or the claim delivers `dust` (XPASS), stop and ping. Do
not edit the xfail reason.

---

## Tests — existing G10 / hardening

**Expect ~40 additional reds** from old live-share membership pins.
Run each G10 file **whole**.

### #1b-i safety properties (keep the assert; they should pass)

- `test_g10_1b_low_quote_prune_then_deposit_captures_omitted_value`
  — today failed (`125e18` vs `100e18−1`). After: stay ACTIVE;
  withdraws match. Drop the “became DORMANT” setup assert.
- `test_low_quote_prune_moves_value_from_existing_to_new_shareholders`
- `test_g10_low_quote_prune_does_not_transfer_prior_claim_value_to_new_depositor`
  — remove `xfail`.
- Live-share #1a property nodes (stay blocked; remove Codex xfail):
  `test_g10_1a_dust_prune_must_not_reenable_nav_with_custody_deficit`,
  `test_g10_prune_custody_deficit_does_not_reenable_nav_safety_property`,
  `test_prune_reenables_share_actions_while_claim_custody_is_still_short`,
  `test_prune_reenables_liquidation_acceptance_while_custody_is_short`
  — delete “measure the bypass” withdraw-succeeds blocks only.

Mixed capture **characterizations** (rewrite numbers, not the
contract):
`test_g10_low_quote_prune_composition_characterization`,
`test_g10_low_quote_prune_withdrawal_delta_is_realizable`,
`test_g10_low_quote_prune_lets_new_depositor_capture_restored_claim_nav`
→ delta ≤ 1 wei.

### #1b-ii safety properties (keep the assert)

- `test_g10_1b_high_quote_activate_then_withdraw_vs_control`
- `test_high_quote_activate_lets_an_exiting_holder_take_phantom_value`
- `test_g10_high_quote_activate_then_honest_withdrawal_characterization`
- `test_g10_high_quote_activate_inflates_dormant_pile_into_nav`

Capacity tests that **seated while shares remained** — rewrite
recovery: empty-cohort activate (G5 sequence) or claim an occupant
to zero, then a receipt. Do not keep asserting live-share seating:
`test_g10_activate_capacity_order_and_persistence`,
`test_g10_activate_capacity_order_charlie_pause_and_recovery`,
`test_activate_capacity_ordering_decides_who_takes_the_last_slot`,
`test_g10_activate_capacity_last_slot_first_come_first_served`.

`test_g10_1a_activate_reverts_while_deficit_then_replenish_restores`
— write **once**, final policy, G5 empty sequence + deficit;
activate still reverts `claim custody deficit`; replenish then
seats.

### Identity / hysteresis (setup only)

Empty-cohort sequence, or claim the pair to zero, or assert
live-book prune/activate is a no-op:

Claude: `test_prune_reenables_share_actions_positive_control_full_custody`,
`test_prune_swap_and_pop_middle_last_and_only_row`,
`test_prune_batch_a_then_c_after_c_moved_into_a_index`,
`test_prune_duplicates_remove_once`,
`test_prune_retention_band_and_paused_call_are_independent_of_pause`,
`test_empty_state_num_one_re_registers_at_index_one`,
`test_green_as_claim_asset_uses_the_one_to_one_branch`,
`test_activate_skip_matrix_and_boundaries`,
`test_activate_under_charlie_governor_and_lite_pause`,
`test_cross_cohort_custody_deficit_blocks_activate_on_the_other_cohort`

Grok / Codex: `test_g10_prune_identity_unpaused_and_paused`,
`test_g10_prune_swap_and_pop_middle_last_only_and_moved_tail`,
`test_g10_dust_prune_then_thin_claim_still_delivers`,
`test_g10_prune_identity_swap_pop_and_balance_layers`,
`test_g10_prune_full_custody_dust_control_keeps_nav_live`,
`test_g10_dormant_pruned_claim_still_delivers_for_funded_holder`

Kimi: `test_g10_prune_dust_by_eoa_moves_no_value_and_uses_reason_2`,
`test_g10_prune_hysteresis_boundaries_and_source_zero_skip`,
`test_g10_prune_batch_swap_and_pop_middle_then_shifted_tail`,
`test_g10_pruned_dormant_pile_remains_claimable_by_funded_shareholder`

Zero-balance prune, source-zero retain, unpaused-activate revert,
export checks,
`test_permanently_unpriced_active_row_has_no_maintenance_exit`
should need little change.

`test_dormant_pile_is_stranded_after_a_full_cohort_exit` /
`test_dormant_pile_is_still_claimable_by_a_funded_shareholder`:
do not “fix” stranding. If setup used live-share prune, seed
below-floor instead.

### Hardening nodes

Save a pre-edit full-file result (`-q --no-header -rf`). At the
end, every ordinary node (not `test_der02_*`, not DV-15) must
**match that baseline or pass after an authorized rewrite below**.
“Report-only” does not allow an unexplained new red.

Authorized setup/model rewrite:

```
test_value_and_maintenance_gas_remain_bounded_at_active_claim_ceiling
test_prune_skips_unpriced_pair_and_continues_batch_while_paused_or_unpaused
test_dormant_thresholds_have_exact_hysteresis_boundaries
test_cap_rejects_new_receipt_then_prune_allows_activation
test_receipts_accumulate_then_activate_once_at_exact_floor
test_claim_data_batch_activation_reverts_atomically_on_custody_deficit
test_claim_data_model_survives_batched_lifecycle_mutations
test_claim_data_model_tracks_dust_claim_reactivation_and_zero_removal
test_claim_data_model_tracks_redemption_reduction_and_green_addition
```

The last one (`:2353`) currently expects a **partial redeem** to
dust-unlist a nonzero row while Bob holds shares. After row B the
claim pair on charlie stays active; GREEN addition still happens.

Gas ceiling: keep the deposit/withdraw gas matrix. Live-share
prune/activate will not change the 20-count — assert that, or
measure prune/activate gas on an empty-cohort arm (G5 sequence).
Do not drop the deposit/withdraw ceilings.

`test_cap_rejects_new_receipt_then_prune_allows_activation`:
free a slot by claiming an occupant to **zero**, then a 21st
**receipt** — or the empty-arm sequence. Keep the node id.

`test_dust_deactivated_pair_with_residual_balance_remains_claimable`:
live-share prune is a no-op; residual is still claimable while
active. Or use the empty-cohort sequence if you still need a
dormant residual.

### Fuzz model (`derandomize=True` — one clean run)

All four nodes. Expected model changes (do this up front, not
“if it fails”):

- `test_fuzz_claim_data_add_prune_activate_sequences`: prune
  dust-delists only when `totalBalances[stab] == 0`; activate
  seats only when `totalBalances[stab] == 0` (and paused, ≥
  floor, cap). Bob is seeded with shares, so those ops are
  no-ops on membership unless a withdraw in the sequence
  empties the cohort.
- `test_fuzz_capacity_rejection_existing_receipt_and_readdition`:
  same live-share prune/activate rules when the model prunes or
  activates.
- `test_fuzz_claim_data_reductions_preserve_shared_liability_model`
  / `test_fuzz_redemptions_preserve_claim_and_green_registry_model`:
  a live-book dust remaining-USD does **not** delist. Zero-balance
  still delists. GREEN from redeem still adds.

---

## Hysteresis

| Pair USD | New receipt | Prune, shares ≠ 0 | Prune, empty + custody ok | Activate, shares ≠ 0 | Activate, empty + paused |
| --- | --- | --- | --- | --- | --- |
| `0` | new/dormant reverts | stays | stays | no-op | skip |
| `0 < x < $0.05` | stays dormant; **reverts at cap** | **stays** | removed | no-op | skip |
| `$0.05 ≤ x < $0.10` | stays dormant; **reverts at cap** | stays | stays | no-op | skip |
| `≥ $0.10` | seats if cap; **reverts at cap** | stays | stays | no-op | seats if cap |

---

## Order

1. Create the [fresh worktree](#fresh-worktree). `cd` there. Stop
   if HEAD / branch / status checks fail.
2. Pre-edit StabilityPool runtime printed. Pre-edit G5 + hardening
   baselines saved (including DV-15 `--runxfail`).
3. Prune hunk + custody skip + comment + row-B call-site assigns.
   Size tests (`-s`). Do not edit the pin. Pin-test drift on
   StabilityPool only is expected.
4. Activate gate + `canActivateClaimAsset` align + pause comment,
   matching the Final `_maintainClaimableAssets` listing.
   Size tests (`-s`). If either hunk does not fit, **stop and ping**
   before rewriting tests.
5. Rewrite tests **once**. Add the four `test_g10_1a_empty_*`
   nodes, `test_g10_live_cap_blocks_21st_and_empty_dust_prune_frees_slot`,
   and the four row-B nodes.
6. Full G10 files + claims node + fuzz (one run) + GREEN swap
   commands below.
7. Full hardening. Compare to the pre-edit baseline. Every
   ordinary (non-`test_der02_*`, non-DV-15) node must **match
   that baseline or pass after an authorized rewrite**. A new
   unexplained red is a stop-and-ping, not “report-only.” DER-02
   table. DV-15 `--runxfail`.
8. Full G5 files report-only; compare to pre-edit signatures.
9. Pin StabilityPool **once**. Teller 24,556. AuctionHouse 24,568.
10. `git diff --check` and `git status --short` in `$WT`. Do not
    commit.

---

## Commands

```
RIPE_PYTHON=/Users/wigglez/dev/ripe-protocol/.venv/bin/python
RIPE_BOA_CACHE_DIR="${TMPDIR:-/tmp}/ripe-boa-cache-g10"

g10_pytest() {
  env -u PYTHONPATH -u VIRTUAL_ENV \
    RIPE_BOA_CACHE_DIR="$RIPE_BOA_CACHE_DIR" \
    "$RIPE_PYTHON" -m pytest "$@" -q
}
```

Size (each hunk + end):

```
g10_pytest tests/test_vault_pointer_runtime_sizes.py -s
g10_pytest tests/vaults/modules/test_stab_vault_hardening.py::test_deployed_runtime_fits_eip170 -s
```

G10 + auction (auction: do not edit; must stay all-pass):

```
g10_pytest \
  tests/vaults/modules/test_g10_prune_activate_proofs.py \
  tests/vaults/modules/test_user_flow_audit_group10_codex.py \
  tests/vaults/modules/test_user_flow_audit_group10.py \
  tests/vaults/modules/test_user_flow_group10_stab_maintenance.py \
  tests/core/auctionHouse/test_user_flow_group10_auction_cleanup.py \
  tests/core/auctionHouse/test_user_flow_audit_group10_codex_auction.py \
  tests/core/auctionHouse/test_g10_remove_expired_proofs.py \
  tests/core/auctionHouse/test_user_flow_audit_group10_auctions.py
```

Claims + fuzz + GREEN swap. **Two commands.** `-k swapWithClaimableGreen`
collects **zero** tests (camelCase is not in the node names).

```
g10_pytest \
  tests/vaults/modules/test_stab_vault_claims.py::test_dust_deactivated_pair_with_residual_balance_remains_claimable \
  tests/vaults/modules/test_stab_vault_claim_data_fuzz.py \
  tests/vaults/modules/test_stab_vault_hardening.py::test_claimable_green_swap_depletes_active_pair_and_emits_deactivation_zero_reason_one

g10_pytest tests/vaults/modules/test_stab_vault.py -k swap_with_claimable_green
```

The second command must collect **nine** nodes. If it collects
zero, you used the wrong `-k` string.

Brief’s 14 named regressions (inline):

```
g10_pytest \
  tests/vaults/modules/test_stab_vault_hardening.py::test_prune_skips_unpriced_pair_and_continues_batch_while_paused_or_unpaused \
  tests/vaults/modules/test_stab_vault_hardening.py::test_dormant_thresholds_have_exact_hysteresis_boundaries \
  tests/vaults/modules/test_stab_vault_hardening.py::test_cap_rejects_new_receipt_then_prune_allows_activation \
  tests/vaults/modules/test_stab_vault_hardening.py::test_receipts_accumulate_then_activate_once_at_exact_floor \
  tests/vaults/modules/test_stab_vault_hardening.py::test_active_zero_price_stays_registered_and_recovers_after_price_restore \
  tests/vaults/modules/test_stab_vault_hardening.py::test_claim_data_batch_activation_reverts_atomically_on_custody_deficit \
  tests/core/auctionHouse/test_ah_auction_mgmt.py::test_remove_expired_fungible_auction_is_permissionless_and_emits_event \
  tests/core/auctionHouse/test_ah_auction_mgmt.py::test_remove_expired_fungible_auction_before_expiry_is_non_mutating \
  tests/core/auctionHouse/test_ah_auction_mgmt.py::test_remove_expired_fungible_auction_exact_boundary_and_missing_are_safe \
  tests/core/auctionHouse/test_ah_auction_mgmt.py::test_remove_expired_fungible_auction_preserves_paused_auction \
  tests/core/auctionHouse/test_ah_auction_mgmt.py::test_remove_expired_fungible_auctions_preserves_swap_and_pop_registries \
  tests/core/auctionHouse/test_ah_auction_mgmt.py::test_final_expired_auction_cleanup_restores_liquidation_retry \
  tests/core/auctionHouse/test_ah_auction_mgmt.py::test_remove_expired_fungible_auction_respects_both_pause_boundaries \
  tests/config/test_switchboard_charlie.py::test_switchboard_three_pause_action_immediate
```

Hardening full file (end) + DV-15:

```
g10_pytest tests/vaults/modules/test_stab_vault_hardening.py
g10_pytest --runxfail \
  tests/vaults/modules/test_stab_vault_hardening.py::test_dormant_dust_remains_recoverable_after_full_exit
```

G5 full files (report-only; compare to pre-edit):

```
g10_pytest tests/vaults/modules/test_g5_stab_zero_share_deposit.py
g10_pytest tests/vaults/modules/test_user_flow_audit_group5.py
g10_pytest tests/vaults/modules/test_g5_liq_price_batch_proofs.py
```

After this ticket: the 17 property nodes **all passed** (no xfail
on the two Codex safety nodes); the five new nodes
(`test_g10_1a_empty_*` ×4,
`test_g10_live_cap_blocks_21st_and_empty_dust_prune_frees_slot`)
pass; the four row-B nodes pass; brief’s 14 pass (after authorized
setup rewrites).

---

## Out of scope

AuctionHouse.vy / Ledger / `removeExpiredFungibleAuction`.
`swapWithClaimableGreen` behavior change. PriceDesk staleness
(Group 7). Group 5 last-exit / `numClaimablePairs` / editing G5
tests. Dormant in NAV. Always-register below `$0.10`. Exporting
`canActivateClaimAsset`. Dropping `activateClaimAssets`. Global
activate no-op. Editing the DER-02 register or DV-15 xfail reason.
Unpriceable-active recovery (D-12). Charlie `startAuction`
(Group 9). Production creation of a custody deficit.
sGREEN-as-claim (Group 12). Measuring AH 21st-receipt routing
(Group 1).

---

## Done

- Worked only in
  `/Users/wigglez/dev/ripe-protocol-user-flow-audit-g10-impl` on
  `impl/g10-stab-claim-membership`. Dirty audit checkout untouched.
- HEAD was exactly `3822a59273a3b1baaff5831d288954ac2c072fc6`.
- #1, #2, #3, and row B landed as prescribed, **or** a hunk was
  removed and the owner already pinged with numbers.
- These new nodes exist and pass: the four `test_g10_1a_empty_*`,
  `test_g10_live_cap_blocks_21st_and_empty_dust_prune_frees_slot`,
  and the four `test_g10_partial_*` / GREEN nodes.
- Former reds / xfails on the 17 property nodes pass. Full G10
  files pass. Auction proofs untouched and green.
- Brief’s 14 named regressions pass.
- Hardening full file: every ordinary node matches the pre-edit
  baseline or passed after an authorized rewrite; no unexplained
  new red. DER-02 table honored; DV-15 `--runxfail` still fails at
  `nothing claimed` (`StabVault.vy:749`). Rewritten nodes listed.
- G5 files untouched; post-edit reds match pre-edit signatures
  (plus the two known smoke reds).
- Fuzz: one clean `derandomize=True` run.
- `swapWithClaimableGreen` tests still pass (behavior unchanged).
- StabilityPool pin matches `env.get_code` **once**. Teller
  24,556. AuctionHouse 24,568. EIP-170 hardening green the whole
  time.
- `git status --short` in `$WT` is the two copied docs plus the
  allowlist. No commit.

Completion reply: worktree path and branch; files changed;
StabilityPool size before / after; every node touched; pytest
commands and results; production still needs a RipeHq swap;
Group 1 still owns AH routing at cap.
