# Group 12 implementation guide

Work order for a fresh agent. Not a second audit. This file controls
the patch (`maxDeposit`/`maxMint` also zero for `self`, not only
`empty`).

Evidence:
[`user-flow-audit-group-12-report-combined.md`](user-flow-audit-group-12-report-combined.md).
Read once. Do not rewrite it, the four source reports, or
`user-flow-audit-token-plumbing.md`.

This ticket **authorizes** the allowlisted contract and test edits.

---

## Locked

Owner (2026-08-18, updated P2 same day): P1 token-scoped; **P2 —
allow revoke-to-zero while gated**; C1 no `permit` change
(`Bytes[65]`). Address findings 1–4, I1, and P2 on the contracts.

This ticket (do not reopen): finding 2 is **freeze-only** (no HQ
sweep). Finding 3 is **GREEN-only** `burnBlacklistTokens(sGREEN)`;
vault *blacklist* stays. Do not add a Charlie both-bits helper.
Do not widen `permit`.

---

## Ticket

Finding **4 first** (`Erc4626Token`). Then 1 + 2 + I1 + 3 + P2 in
`Erc20Token`. Minimal diffs. Do not refactor around the hunks.

| # | Work |
| ---: | --- |
| 4 | `max*` return 0 when the matching op cannot execute |
| 1 | Blacklisted sGREEN cannot `burn` (0 or nonzero) |
| 2 / I1 | Last-share `burn` / `burnBlacklistTokens` cannot leave vault GREEN |
| 3 | `GREEN.burnBlacklistTokens(sGREEN)` reverts; `setBlacklist` unchanged |
| P2 | Revoke-to-zero works while paused / blacklisted |
| P1 / C1 | Do not implement |

Do not edit Teller / PSM / stab / AH / Charlie / HQ / `config/`.
Do not deploy or push unless the owner asks.

**Size.** EIP-170 = 24,576. Tokens are not in
`test_vault_pointer_runtime_sizes.py`. Measure
`len(boa.env.get_code(address))` after each finding. Now: GREEN/RIPE
7,437 (17,139 free), sGREEN 11,285 (13,291 free). If a hunk does not
fit, or you would skip a check: **stop and tell the owner.**
`vyper==0.4.3` / `titanoboa==0.2.7`.
After all hunks: GREEN/RIPE 8,283 (16,293 free), sGREEN 12,689
(11,887 free). Per-finding intermediate sizes were not retained;
final measurements have ample EIP-170 headroom.

**Intended, do not “fix”:** last unblacklisted holder must `redeem`.
If GREEN is paused, the vault is GREEN-blacklisted, or the receiver
is GREEN-blacklisted, they can neither burn nor exit until that gate
lifts — do not weaken the strand check. Freeze-only: gov can freeze a
sole sGREEN holder, not seize (unblacklist, then they redeem). Partial
share-burn still works when other holders remain. Last-share gov burn
is allowed when assets are already 0. Finding 3 does not protect
StabVault / Endaoment (Group 5). Retargeting HQ `greenToken()` or
`savingsGreen()` bypasses the GREEN-only guard — privileged gov; do
not add more code; do not retarget either while the old vault has
shares or GREEN. RH deploys new GREEN/RIPE/sGREEN; live Base
GREEN/RIPE stay old (`Ccip.py` bridges both; sGREEN is not bridged).
`max*` assume ASSET is GREEN. RH SavingsGreen is deployed that way.
This ticket does not enforce it in `SavingsGreen.__init__`. If you are
asked to support a generic ERC-20 asset, **stop** — do not add a
fallback.

---

## Workspace — isolate first

Do **not** edit the dirty checkout at
`/Users/wigglez/dev/ripe-protocol-user-flow-audit` (other groups are
writing there). Do not edit `ripe-protocol` or `ripe-protocol-rh`.

New branch + new worktree from the pinned token baseline
`3822a59273a3b1baaff5831d288954ac2c072fc6`. This guide is not in that
commit — copy it in.

```
git -C /Users/wigglez/dev/ripe-protocol-user-flow-audit worktree add \
  -b docs/rh-g12-impl \
  /Users/wigglez/dev/ripe-protocol-user-flow-audit-g12 \
  3822a59273a3b1baaff5831d288954ac2c072fc6
cp /Users/wigglez/dev/ripe-protocol-user-flow-audit/docs/chains/rh/user-flow-audit-group-12-implementation.md \
  /Users/wigglez/dev/ripe-protocol-user-flow-audit-g12/docs/chains/rh/
cd /Users/wigglez/dev/ripe-protocol-user-flow-audit-g12
```

Optional: also copy
`user-flow-audit-group-12-report-combined.md` if you want the
evidence file locally. This guide is enough to execute.

All contract and test edits happen only in that worktree, on
`docs/rh-g12-impl`. Do not `reset` / `restore` / `clean` / `stash`
the original tree. If the five token sources in the new worktree
differ from that commit, stop.

Local commits on `docs/rh-g12-impl` are fine. Do not push, and do
not merge back, unless the owner asks.

```
RIPE_PYTHON=/Users/wigglez/dev/ripe-protocol/.venv/bin/python
RIPE_BOA_CACHE_DIR="${RIPE_BOA_CACHE_DIR:-$TMPDIR/ripe-boa-cache-g12}"
G12_TMP="${TMPDIR:-/tmp}/ripe-pytest-g12"
mkdir -p "$G12_TMP"
env -u PYTHONPATH -u VIRTUAL_ENV \
  PYTHONDONTWRITEBYTECODE=1 \
  RIPE_BOA_CACHE_DIR="$RIPE_BOA_CACHE_DIR" \
  "$RIPE_PYTHON" -m pytest -p no:cacheprovider --basetemp="$G12_TMP" \
  <selectors> -q
```

No `.venv` here. Do not run bare `pytest`.

**Allowlist:** `contracts/tokens/modules/Erc4626Token.vy` (four
`max*`); `contracts/tokens/modules/Erc20Token.vy` (`burn`,
`burnBlacklistTokens`, `_isValidNewRipeHq`, add
`savingsGreen()` to the local `RipeHq` interface, self-`asset()`
probe, `approve` / `decreaseAllowance` / `permit` /
`_validateNewApprovals` for P2); the test files named below; new
`tests/tokens/test_g12_impl_fixes.py`.

Do not edit `SavingsGreen.vy` / `GreenToken.vy` / `RipeToken.vy`.
Do not change `setBlacklist` or `_redeem`. Do not put the strand
check in `_burn`. Do not auto-clear allowances on pause.

---

## 4 — `max*`

Add this and fold it into the four existing `max*` bodies. Do not
rewrite the rest of the module.

```
interface AssetToken:
    def isPaused() -> bool: view
    def blacklisted(_addr: address) -> bool: view

@view
@internal
def _assetBlocked() -> bool:
    return staticcall AssetToken(ASSET).isPaused() or staticcall AssetToken(ASSET).blacklisted(self)

@view
@internal
def _zeroBacking() -> bool:
    return token.totalSupply != 0 and staticcall IERC20(ASSET).balanceOf(self) == 0
```

- All four `max*`: 0 if `token.isPaused`, `_assetBlocked()`, or
  `_zeroBacking()`
- `maxDeposit`/`maxMint` also 0 if `_receiver` is `empty` or `self`
  (keep the existing sGREEN-blacklisted-receiver 0)
- `maxWithdraw`/`maxRedeem` also 0 if owner is sGREEN-blacklisted
  (already there)
- `supply == 0` is not `_zeroBacking()` — keep unlimited
  `maxDeposit`/`maxMint`
- Do not change `preview*`

Zero-backing after finding 3 (official vault burn is gone):

```
green_token.burn(green_token.balanceOf(savings_green), sender=savings_green.address)
```

Keep `max* == 0`. Leave
`tests/tokens/test_erc4626.py::test_erc4626_max_views_report_pause_blacklist_and_conversion_limits`
sGREEN-side expects alone.

**Invert** (expect 0; same fixtures):

- `tests/tokens/test_g12_wrap_unwrap.py::test_g12_max_views_overquote_green_paused`
- `tests/tokens/test_g12_wrap_unwrap.py::test_g12_max_views_overquote_vault_green_blacklisted`
- `tests/tokens/test_g12_wrap_unwrap.py::test_g12_max_views_degenerate_queries`
  (`empty` and `self`)
- `tests/tokens/test_g12_sgreen_wrap.py::test_g12_max_views_vs_executable`
- `tests/tokens/test_g12_sgreen_wrap.py::test_g12_shares_nonzero_assets_zero_is_reachable_via_backing_burn`
  (`maxRedeem` → 0; keep preview / redeem-revert)
- `tests/tokens/test_g12_blacklist_compose.py::test_g12_green_vault_blacklist_blocks_wrap_while_max_reports_capacity`
- `tests/tokens/test_g12_token_plumbing_sgreen.py::test_g12_max_and_preview_trace_under_green_pause_and_vault_blacklist`
- `tests/tokens/test_g12_token_plumbing_sgreen.py::test_g12_green_vault_blacklist_blocks_both_directions_while_sgreen_max_views_stay_open`
- `tests/tokens/test_g12_token_plumbing_sgreen.py::test_g12_max_deposit_mint_overquote_invalid_receiver_and_zero_backing_trace`

**Keep assert, setup already valid:**
`tests/tokens/test_g12_token_plumbing_sgreen.py::test_g12_max_views_should_zero_when_green_pause_blocks_every_matching_operation_property`

**Rewrite setup only, keep `max* == 0`:**
`tests/tokens/test_g12_token_plumbing_sgreen.py::test_g12_max_redeem_should_zero_when_zero_backing_makes_redeem_impossible_property`

---

## 1 / 2 / I1 — last-share share-burn

Self-probe only. Copy this helper:

```
@view
@internal
def _selfAsset() -> address:
    success: bool = False
    response: Bytes[64] = b""
    success, response = raw_call(
        self,
        method_id("asset()", output_type=Bytes[4]),
        max_outsize=64,
        is_static_call=True,
        revert_on_failure=False,
    )
    if not success or len(response) != 32:
        return empty(address)
    return abi_decode(response, address)
```

`burn`:

1. `assert not self.isPaused`
2. If `self.blacklisted[msg.sender]` and `self._selfAsset() != empty(address)`:
   revert (`dev: sender blacklisted`) — **any** amount, including 0
3. If `_amount != 0` and `_amount == self.totalSupply` and
   `self.balanceOf[msg.sender] >= _amount`:
   `asset: address = self._selfAsset()`; if `asset != empty(address)`:
   `assert staticcall IERC20(asset).balanceOf(self) == 0`
   (`dev: cannot strand vault assets`)
4. `self._burn(msg.sender, _amount)`

GREEN/RIPE: `_selfAsset()` is empty. Blacklisted GREEN/RIPE still
hit the probe, then fall through.

`burnBlacklistTokens` — **clamped `amount` only** (raw `_amount`
misses `remaining + 1` on the named node):

```
assert msg.sender == staticcall RipeHq(self.ripeHq).governance()
assert self.blacklisted[_addr]
amount: uint256 = min(_amount, self.balanceOf[_addr])
assert amount != 0
if self == staticcall RipeHq(self.ripeHq).greenToken():
    assert _addr != staticcall RipeHq(self.ripeHq).savingsGreen()  # dev: cannot burn vault backing
asset: address = self._selfAsset()
if amount == self.totalSupply and asset != empty(address):
    assert staticcall IERC20(asset).balanceOf(self) == 0  # dev: cannot strand vault assets
self._burn(_addr, amount)
```

Add `savingsGreen()` to the existing `RipeHq` interface. In
`_isValidNewRipeHq`, also require
`staticcall RipeHq(_newHq).savingsGreen() != empty(address)`.

**Rewrite to exact revert** (do not loosen `recovered <= 1e18`):

- `tests/tokens/test_g12_token_plumbing_sgreen.py::test_g12_blacklisted_last_share_self_burn_should_not_allow_fresh_address_recovery_property`
- `tests/tokens/test_g12_token_plumbing_sgreen.py::test_g12_governance_last_share_burn_should_not_redirect_backing_to_a_new_depositor_property`
- `tests/tokens/test_g12_token_plumbing_sgreen.py::test_g12_last_share_self_burn_creates_assets_without_supply_and_next_depositor_captures_it`
- `tests/tokens/test_g12_token_plumbing_sgreen.py::test_g12_last_share_governance_burn_redirects_blacklisted_backing_to_next_depositor`
- `tests/tokens/test_g12_blacklist_compose.py::test_g12_last_share_self_burn_leaves_assets`
- `tests/tokens/test_g12_blacklist_compose.py::test_g12_gov_burn_last_sgreen_shares_leaves_assets`
- `tests/tokens/test_g12_blacklist_composition.py::test_g12_degenerate_last_holder_self_burn`
- `tests/tokens/test_g12_blacklist_composition.py::test_g12_degenerate_gov_burn_last_shares`
- `tests/tokens/test_g12_sgreen_wrap.py::test_g12_degenerate_last_share_self_burn`
- `tests/tokens/test_g12_sgreen_wrap.py::test_g12_degenerate_gov_burn_last_shares`
- `tests/tokens/test_erc4626.py::test_erc4626_governance_blacklist_burn_bypasses_exit_controls`
  — `shares//3` still succeeds; `remaining + 1` reverts
  `cannot strand vault assets`; shares and vault GREEN stay

Keep an adjacent last-holder `redeem` that returns `totalAssets`.

**Split** (GREEN/RIPE unchanged; sGREEN blacklisted `burn` reverts).
If the sGREEN holder is the sole supply, leave a second holder for
partial/clamp loops:

- `tests/tokens/test_g12_erc20_gates.py::test_g12_pause_gates_and_burn_split`
- `tests/tokens/test_g12_erc20_gates.py::test_g12_burn_bounds`
- `tests/tokens/test_g12_erc20_gates.py::test_g12_burn_blacklist_bounds`
- `tests/tokens/test_g12_token_erc20_gates.py::test_g12_burn_bounds`
- `tests/tokens/test_g12_token_erc20_gates.py::test_g12_burn_blacklist_tokens_bounds`
- `tests/tokens/test_g12_token_plumbing_erc20_permit.py::test_g12_burn_bounds_pause_blacklist_split_and_blacklist_admin_edges`

---

## 3 — do not burn GREEN in canonical sGREEN

Do **not** probe `asset()` on the target. The GREEN-only `if` is in
the `burnBlacklistTokens` snippet above (after `amount != 0`).

RIPE `burnBlacklistTokens(sGREEN)` must still work. Do not change
`setBlacklist`.

**Rewrite to exact revert** (vault GREEN, GREEN supply, sGREEN
supply/assets, PPS unchanged):

- `tests/tokens/test_g12_token_plumbing_sgreen.py::test_g12_green_vault_backing_burn_should_not_leave_outstanding_shares_without_assets_property`
- `tests/tokens/test_g12_token_plumbing_sgreen.py::test_g12_zero_backing_with_outstanding_shares_is_reachable_and_recovers_only_after_external_reseed`
- `tests/tokens/test_g12_blacklist_compose.py::test_g12_green_vault_burn_creates_shares_gt_zero_assets_eq_zero`
- `tests/tokens/test_g12_blacklist_composition.py::test_g12_degenerate_shares_no_assets_bricks_vault`

**Keep** (GREEN-vault blacklist is the late-failure trigger):

- `tests/tokens/test_g12_wrap_unwrap.py::test_g12_redeem_late_failure_rollback` (`green-vault-blacklisted`)
- `tests/tokens/test_g12_sgreen_wrap.py::test_g12_redeem_late_failure_atomicity`
- `tests/tokens/test_g12_token_plumbing_sgreen.py::test_g12_shared_redeem_late_failure_rolls_back_after_share_burn_and_retries`

**Setup-only** (impersonation burn for pps<1; keep the 0-vs-1 asserts):

- `tests/tokens/test_g12_wrap_unwrap.py::test_g12_smallest_redeem_zero_assets_on_loss_vault`
- `tests/tokens/test_g12_token_plumbing_sgreen.py::test_g12_smallest_share_amounts_that_redeem_to_zero_and_one_after_partial_green_loss`

---

## P2 — revoke-to-zero while gated

Do not auto-clear allowances. Transfer / `transferFrom` stay blocked
by pause and blacklist. Only shrink or zero an approval.

Keep `_validateNewApprovals` for **new or increased** approvals.
Revokes skip pause / owner-blacklist / spender-blacklist (spender
still cannot be `empty`):

```
@view
@internal
def _validateSpender(_spender: address):
    assert _spender != empty(address) # dev: invalid spender

@view
@internal
def _validateNewApprovals(_owner: address, _spender: address):
    self._validateSpender(_spender)
    assert not self.isPaused # dev: token paused
    assert not self.blacklisted[_owner] # dev: owner blacklisted
    assert not self.blacklisted[_spender] # dev: spender blacklisted
```

- `approve`: `_amount == 0` → `_validateSpender` only; else
  `_validateNewApprovals`
- `decreaseAllowance`: `_validateSpender` only (never increases)
- `increaseAllowance`: still `_validateNewApprovals` (including `0`)
- `permit`: `_value == 0` → `_validateSpender` only, then the
  existing signature / nonce / deadline path; `_value != 0` →
  `_validateNewApprovals` as today

**Must go green** (keep the assert — this was the authored-to-fail
lockout proof):
`tests/tokens/test_g12_token_plumbing_erc20_permit.py::test_g12_allowance_should_remain_revocable_during_pause_property`

**Invert** (revoke must succeed; `approve(n>0)` / `increaseAllowance`
still revert). Transfer still blocked during the gate:

- `tests/tokens/test_g12_erc20_gates.py::test_g12_pause_gates_and_burn_split`
  (`decreaseAllowance` while paused)
- `tests/tokens/test_g12_erc20_gates.py::test_g12_allowance_persistence_and_revival`
- `tests/tokens/test_g12_erc20_gates.py::test_g12_sgreen_allowance_revival_delegated_exit`
- `tests/tokens/test_g12_token_erc20_gates.py::test_g12_pause_blocks_user_ops_not_gov_burn_and_same_value_reverts`
  (`decreaseAllowance` while paused)
- `tests/tokens/test_g12_token_erc20_gates.py::test_g12_allowance_revival_lifecycle`
- `tests/tokens/test_g12_token_plumbing_erc20_permit.py::test_g12_allowance_persists_and_revives_after_each_gate`
- `tests/tokens/test_g12_token_plumbing_erc20_permit.py::test_g12_permit_created_allowance_revives_after_owner_blacklist`
- `tests/tokens/test_g12_token_plumbing_erc20_permit.py::test_g12_sgreen_allowance_revives_into_delegated_exit`
- `tests/tokens/test_g12_permit.py::test_g12_permit_created_allowance_persists_and_revives`

---

## Tests

`tests/tokens/test_g12_impl_fixes.py` — only what the list above does
not already prove:

- all four `max*` are 0 under GREEN pause **and** GREEN-vault
  blacklist; `empty`/`self` deposit views are 0; empty vault and
  pre-first-deposit donation keep unlimited `maxDeposit`/`maxMint`
- last-share burn/gov-burn revert when assets remain; succeed when
  assets are 0; last holder `redeem` still works
- blacklisted sGREEN `burn(0)` **and** a positive partial `burn`
  revert; snapshot unchanged; GREEN/RIPE blacklisted burn still works
- `GREEN.burnBlacklistTokens(sGREEN)` reverts; a mock with
  `asset()→GREEN` is still burnable; `RIPE.burnBlacklistTokens(sGREEN)`
  still works; HQ with `savingsGreen()==empty` returns False; HQ
  missing the `savingsGreen()` getter reverts
- P2: nine parameterized nodes (gate × method). While paused
  **and** while owner- or spender-blacklisted, `approve(0)` /
  `decreaseAllowance` / `permit(..., 0)` each start from a live
  nonzero allowance and zero it; `permit(..., 0)` also increments
  nonce; `approve(n>0)` / `increaseAllowance` / nonzero `permit`
  still revert; `transferFrom` remains blocked during the gate;
  after the gate lifts, revoked authority remains unusable until a
  fresh approval

**Expected red** (leave failing; do not `xfail`):

- `tests/tokens/test_g12_token_plumbing_erc20_permit.py::test_g12_eip1271_long_signature_should_be_accepted_property`

Run **only** `test_g12_impl_fixes.py`, every `file::node` named in
this guide, and the 26 named selectors in
`user-flow-audit-token-plumbing.md` (34 nodes), with:

```
--deselect tests/tokens/test_g12_token_plumbing_erc20_permit.py::test_g12_eip1271_long_signature_should_be_accepted_property
```

Do not glob `test_g12_*.py`. Do not run the full suite. Named 26 must
be 34 passed (includes the rewritten erc4626 last-share node). Green
run: 0 failed. The C1 node, run alone: still fail.

If a test not listed here fails: **stop and tell the owner.** Do not
debug it into a weaker assert. Never green a red by loosening
`recovered <= 1e18` or `maxRedeem == 0`.

---

## Done

Patches 1–4, I1, and P2 are in. Finding 3 is GREEN-only.
`setBlacklist` unchanged. P1 / C1 untouched. Runtimes `< 24,576`.
Reply with files touched, runtimes, and which listed nodes were
inverted / rewritten / setup-only. No extra markdown record.
