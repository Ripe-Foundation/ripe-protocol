# Group 11 implementation guide (draft 6)

> **Hunk 4 superseded by signed A+.** Draft 6 Hunk 4 — the
> single-counter / no-HashMap reserve recipe, including owner
> ruling 3 at lines 139–163 and the Hunk 4 body at lines 461–559 —
> is **not** the shipped design. The controlling work order is
> [`user-flow-audit-group-11-implementation-hunk4-a-plus.md`](user-flow-audit-group-11-implementation-hunk4-a-plus.md)
> (owner-signed 2026-08-18). Hunks 1, 2, 3, and 5 in this document
> remain in force. Findings 1, 2, 4, 5, and 6 are unchanged.
> Passages below that say “no HashMap,” “one `uint256`,” or
> “outstanding uncashed” as a single Ledger counter describe the
> superseded Hunk 4 only.

Work order for a **fresh agent**. Not a second audit. Do not re-open
dropped hypotheses. Evidence (read once, do not edit):
[`user-flow-audit-group-11-report-combined.md`](user-flow-audit-group-11-report-combined.md).
Do not edit the four source reports or `user-flow-audit-hr.md`.

Owner signed off 2026-08-18 (rulings 1–4 below). **Ready to
implement.** This ticket **authorizes** the allowlisted contract
and test edits in the isolated worktree below.

Five hunks, four production files. No extra helpers, no extra
comments, no HashMap, no RipeGov / SharesVault edits.

| File | Change |
| --- | --- |
| `Contributor.vy` | overflow-safe vest helper (~8 lines) |
| `HumanResources.vy` | a few `areValid` bounds; saturate two views; one Ledger call in `cashRipeCheck` |
| `Ledger.vy` | one `uint256`, three asserts, one new HR-only function |
| `SwitchboardDelta.vy` | one feasibility assert |

---

## Workspace — new worktree and branch (mandatory)

The audit checkout is dirty with other groups. Do **all** contract
and test edits in `$WT` on `impl/g11-hr-safety`. Do not edit
`/Users/wigglez/dev/ripe-protocol-user-flow-audit`. Do not work in
`ripe-protocol` or `ripe-protocol-rh`.

```
SRC=/Users/wigglez/dev/ripe-protocol-user-flow-audit
WT=/Users/wigglez/dev/ripe-protocol-user-flow-audit-g11-impl
PIN=3822a59273a3b1baaff5831d288954ac2c072fc6

test ! -e "$WT" || { echo "worktree path exists; stop"; exit 1; }
git -C "$SRC" worktree add -b impl/g11-hr-safety "$WT" "$PIN"
cp "$SRC/docs/chains/rh/user-flow-audit-group-11-implementation.md" \
   "$SRC/docs/chains/rh/user-flow-audit-group-11-report-combined.md" \
   "$WT/docs/chains/rh/"
cd "$WT"
```

Expect `HEAD == $PIN`, branch `impl/g11-hr-safety`, and only those
two copied docs dirty until you start. Combined-report sha256:
`cd377b333c9155a57e3ef1bb09ac36ad273634c9305f189ffbbc38a5a2cd2e3e`.
If the path exists, `status` shows anything else, or the copied
report hash mismatches, **stop**.

No `.venv` here. Every pytest:

```
RIPE_PYTHON=/Users/wigglez/dev/ripe-protocol/.venv/bin/python
RIPE_BOA_CACHE_DIR="${RIPE_BOA_CACHE_DIR:-$TMPDIR/ripe-boa-cache}"
env -u PYTHONPATH -u VIRTUAL_ENV RIPE_BOA_CACHE_DIR="$RIPE_BOA_CACHE_DIR" \
  "$RIPE_PYTHON" -m pytest <that_test> -q
```

Quote parametrized node IDs in zsh. Do not write `[below_precision-MAX]`.
Do not run whole HR / Delta / `test_g6_*.py` files. The two named
Group 6 nodes in Validation are the only `test_g6_*` exceptions.

Do not `git add`, commit, push, PR, or deploy unless the owner asks.
If you halt: leave the tree; `git diff --stat`; do not revert.

**Reuse existing helpers** (do not add a new helper module):
`g11_proof_helpers.official_delta_budget`,
`official_delta_cancel`, `initiate_contributor`,
`confirm_contributor`, `delta_confirm_and_execute`;
`g11_claude_helpers.make_contributor` / `terms`. Official budget
writes use Delta `setRipeAvailableForHr` + execute, not Ledger
impersonation, whenever the test is proving the official path.

---

## What this ticket actually closes

Do not invent a seventh finding.

This is **not** “six findings fully closed.” Honest status:

| # | This ticket | Still open |
| ---: | --- | --- |
| 1 | Vest views cannot `safemul`-revert on a newly deployed clone (`vestLen <= 2**128`). Create rejects `compensation > max_value(uint256) // 2` (the ranked `2**255` cell). | Cash / after-cliff cancel of a large *admitted* paycheck can still die in SharesVault: `_amount * totalShares` (`SharesVault.vy:270`) on a populated vault, and `_totalShares + 10**8` (`:267`) on a **second** deposit (a first mint has `_totalShares == 0`, so `0 + 10**8` does not overflow). Group 6 owns that. Already-deployed clones are not repaired (blueprint is forward-only; launch has none). |
| 2 | Create rejects `D > max_value(uint256) - 2**64` (the ranked `D = uint256.max` strand). | `D = 0` / below-min / above a live vault max stay legal at create. Group 6’s transfer clamp owns those. Huge *in-band* `newNormalized * D` can still overflow; Group 6’s clamp-to-max does not fix that multiply. Assumes `block.number < 2**64` through the final transfer. |
| 3 | Ledger tracks `hrReservedCompensation` = outstanding uncashed (add `+C`, cash `−amount`, cancel `−R`). `setRipeAvailForHr` asserts `_amount <= max_value - reserved`. No clone walk. | Hostile cash or refund larger than reserved fail-closes that call. No HashMap / no per-clone leftover store. |
| 4 | Infeasible `minCliff > maxVest` merge **reverts** on the two Delta branches that can create it. | — |
| 5 | Constructor-overflowing `startDelay` is rejected at initiate; a queued boundary can fail revalidation at confirm. | — |
| 6 | Ranked two-`2**255` construction cannot be created. Views saturate instead of reverting. Two stock `MAX // 2` clones sum to `MAX - 1` (no saturate). A third stock `MAX // 2` clone cannot be **funded** (`setRipeAvailForHr(H)` reverts once reserved is `MAX - 1`). Under reserved+setter, official stock `compensation()` sums cannot overflow (they equal reserved, and a fundable third `C` satisfies `reserved + C <= MAX`). Saturation is proved with the custom blueprint (both views). | Saturation does not stop a hostile `compensation()` that reverts or a walk that runs out of gas. |

Do not write “share-mint safe.” Do not write “finding 2 is universal transfer arithmetic safety.”

**Do not edit `RipeGov.vy` or `SharesVault.vy`.** Group 6 owns the
transfer clamp and share math.

---

## Start-of-work (in `$WT`)

```
git rev-parse HEAD
git rev-parse --abbrev-ref HEAD
git status --short
```

HEAD must be `3822a59273a3b1baaff5831d288954ac2c072fc6`, branch
`impl/g11-hr-safety`, status only the two copied docs. If not,
**stop**. Re-collect the 32 Group 11 files here and save the
counts (bind-time reference: 261 / 258 passed / 3 failed).

Do not edit `conftest.py`, `BluePrint.py`, Defaults, or shared
fixtures. Do not edit `RipeGov.vy` or any `test_g6_*.py`. RipeGov
pin at this baseline is `23493` — leave it.

---

## Owner rulings (confirmed 2026-08-18)

1. **Finding 2 is a static overflow slack, not a live-band read.**
   `if D > max_value(uint256) - 2**64: return False`.
   Do **not** read `ripeGovVaultConfig`. Do **not** reject
   `D < minLockDuration` or `D > live maxLockDuration`.
   `DefaultsLocal.ripeGovVaultConfigs()` is `[]`; the shared
   `deployedContributor` fixture never calls `setupRipeGovVaultConfig`
   before create. A live-band rule with `maxLockDuration == 0` would
   reject fixture `D = 100` and break ~129 nodes, including 9 of the
   brief’s 26 named regressions, in files this ticket must not edit.
   Group 6’s clamp is the vault-band backstop.
2. **Finding 1 create-gate is `compensation > max_value(uint256) // 2`.**
   That is the ranked vest cell (`2**255`), not a SharesVault envelope.
   `MAX // 10**8` is **forbidden** here. It is not a SharesVault
   envelope: a first empty-vault mint has `_totalShares == 0`, so
   `0 + 10**8` (`SharesVault.vy:267`) does not overflow. The real
   overflows are `_amount * totalShares` (`:270`) on a populated
   vault and `_totalShares + 10**8` on the **next** deposit. Do not
   call any ceiling “share-mint safe.” Do not install a
   `20_000_000 * 10**18` product cap (that would reject the existing
   `10**40` cash control).
3. **Finding 3 is reserved-compensation headroom, not `MAX // 2` alone.**
   A `MAX // 2` setter with `C_max = MAX // 2` leaves a **two-clone**
   cancel brick (stale `~5e7` figure was from the withdrawn
   `MAX // 10**8` cap):

   Let `H = MAX // 2`. Set budget `H`, confirm A with `C = H`
   (budget `0`). Set budget `H`, confirm B with `C = H`. Set budget
   `H` again. Pre-cliff cancel A refunds `H` → budget `2H = MAX - 1`.
   Pre-cliff cancel B does `(MAX - 1) + H` and reverts at
   `Ledger.vy:839`.

   That residual is not accepted. Maintain `hrReservedCompensation`
   on Ledger as **outstanding uncashed** (amounts HR already
   passes — no `compensation()` extcall, no `O(N)` walk):
   add `+C`, cash `−amount`, cancel `−R`. Setter:
   `_amount <= MAX - reserved`.

   **Do not accept a sticky / permanent ratchet.** Subtracting
   only `R` on cancel (and ignoring cash) leaves
   `reserved == totalClaimed` after an after-cliff cancel and
   `reserved == C` after a fully paid, never-cancelled vest.
   Two successful `H` clones would then cap the setter at `1`
   forever — the same class of brick as the two-clone cancel
   trace. Release on cash and on cancel so a finished paycheck
   restores headroom. See hunk 4.
4. **Finding 4 execute reverts** (`# dev: infeasible hr config`).
   Pending stays. No event. Config unchanged.
5. **Do not restore launch setter values. Do not change freeze / residue.**
6. **Do not `@pytest.mark.xfail`.** Invert until the node **passes**.

---

## Size — stop and tell the owner

Measured on this tree at `3822a59` (`vyper==0.4.3` / `titanoboa==0.2.7`).
EIP-170 is **24,576**. If HEAD changed, you should already have stopped.

| Contract | Runtime at `3822a59` | Headroom | This ticket |
| --- | ---: | ---: | --- |
| **HumanResources** | 12,542 | **12,034** | hunks 2, 3, 4 (one call) |
| **Ledger** | 13,306 | **11,270** | hunk 4 |
| **RipeGov** | 23,493 | — | **do not edit** |
| **Teller** | 24,556 | **20** | **do not edit** |
| **SwitchboardDelta** | not pinned | measure | hunk 5 |
| **Contributor** | blueprint, not pinned | measure | hunk 1 |

After every **pinned** hunk, run
`tests/test_vault_pointer_runtime_sizes.py -s`. Update only the pin
you changed (`HumanResources` and/or `Ledger`). Teller `24556`,
AuctionHouse `24568`, and RipeGov `23493` stay put.

**Temporary size prints — explicit exemption.** These two files are
**not** otherwise allowlisted. You may add **one** print, run once,
then **delete the print** so `git status` is clean on that file.
Do not leave the print in the handoff.

Delta — first line of
`tests/config/test_switchboard_delta.py::test_switchboard_delta_lite_action_permissions`:

```
print("DELTA_RUNTIME", len(switchboard_delta.env.get_code(switchboard_delta.address)))
```

```
env -u PYTHONPATH -u VIRTUAL_ENV RIPE_BOA_CACHE_DIR="$RIPE_BOA_CACHE_DIR" \
  "$RIPE_PYTHON" -m pytest -q -s \
  tests/config/test_switchboard_delta.py::test_switchboard_delta_lite_action_permissions
```

Contributor — in
`tests/core/humanResources/test_hr_add_contributor.py::test_hr_confirm_new_contributor_success`,
after `event = events[0]`:

```
print("CONTRIBUTOR_RUNTIME", len(boa.env.get_code(event.contributorAddr)))
```

(`c` is not defined in that test.)

If **any** hunk would push a contract to 24,576, or you would weaken,
drop, relocate, or substitute a check to fit — **stop and tell the
owner.** Hunk 5 is the only likely squeeze.

Do not deploy.

---

## Abort (other than size)

Stop and tell the owner if:

- `$WT` HEAD is not `3822a59273a3b1baaff5831d288954ac2c072fc6`.
- `$WT` already existed, or start-of-work `status` was not just
  the two copied docs.
- The vest helper disagrees with Python `C * e // L` on the
  differential cases in hunk 1.
- Either Group 6 smoke **errors at create / fixture / initiate**
  (you rejected a legal `D`). Unlock-assert failures are **not**
  an abort — see Validation.
- You think you need to edit RipeGov, SharesVault, Teller, Defaults,
  `conftest.py`, `test_hr_other.py`, or a `test_g6_*.py` file.
- After hunks, any Group 11 node fails, xfails, xpasses, or errors
  in setup.

---

## Allowlist

- `contracts/modules/Contributor.vy` — `_getTotalVested` and one
  internal vest helper. No other Contributor entrypoints.
- `contracts/core/HumanResources.vy` — `_areValidContributorTerms`
  (keep the existing signature unless a caller already has a value
  you would otherwise re-fetch; you do **not** need a new
  MissionControl method), `getTotalCompensation`, `getTotalClaimed`,
  and one Ledger call inside `cashRipeCheck`. No other HR
  entrypoints.
- `contracts/data/Ledger.vy` — `hrReservedCompensation` plus the
  four HR-budget writes: `addHrContributor`, `setRipeAvailForHr`,
  `refundRipeAfterCancelPaycheck`, and new
  `reduceHrReservedCompensation`. No other Ledger functions.
- `contracts/config/SwitchboardDelta.vy` — feasibility assert on
  `HR_CONFIG_MIN_CLIFF` and `HR_CONFIG_VESTING` only.
- `tests/test_vault_pointer_runtime_sizes.py` — pins you changed.
- Existing Group 11 proofs, in place:

  - `tests/core/humanResources/test_g11_*.py`
  - `tests/core/humanResources/test_user_flow_audit_group11_codex_*.py`
- `tests/data/test_ledger.py` — HR-budget tests only (add /
  duplicate / unauthorized / setter+refund / failed-add /
  pause-block HR lines). Do not refactor the rest of the file.
- **New** test blueprint
  `tests/core/humanResources/Group11OverflowViewContributor.vy`
  (hunk 3 proof). Constructor ABI must match Contributor
  (`_ripeHq` … `_maxKeyActionDelay`). `compensation()` and
  `totalClaimed()` return `max_value(uint256) // 2 + 1` **regardless
  of constructor args**.
- Temporary size-print exemption (add, measure, **delete**):
  `tests/config/test_switchboard_delta.py`,
  `tests/core/humanResources/test_hr_add_contributor.py`.

Do not edit `RipeGov.vy`, `SharesVault.vy`, `Teller.vy`, Defaults,
Charlie, Alpha, `conftest.py`, Group 6 proofs, or reports.

Do not change external ABI of production contracts (no new public
functions, no signature changes on existing externals), **except**
hunk 4: `hrReservedCompensation()` (same shape as
`ripeAvailForHr()`) and `reduceHrReservedCompensation(_amount)`.

---

## Hunk 1 — overflow-safe vest (finding 1, forward-only)

**Today.** `Contributor.vy:499`:

```
min(compensation, compensation * (timestamp - startTime) // (endTime - startTime))
```

**Required.** Internal helper used by `_getTotalVested`. Keep the
`timestamp <= startTime` and `compensation == 0` early returns. Then:

```
elapsed = timestamp - startTime
vestLen = endTime - startTime
if elapsed >= vestLen: return compensation
return (compensation // vestLen) * elapsed + (compensation % vestLen) * elapsed // vestLen
```

Hunk 2 adds `vestingLength <= 2**128`. The helper may
`assert vestLen <= 2**128`. On that domain the identity equals
`compensation * elapsed // vestLen`.

**Differentials** (Python `C * e // L`, `e < L`, `L <= 2**128`):

- `(10**40, fixture vest, 2)`
- `(20_000_000 * 10**18, 2, 1)`
- `(2**128 - 1, 2**128, 2**128 - 1)` — **required.**
  `C % L = L - 1` and `e = L - 1` → product `(2**128 - 1)**2`,
  the exact maximum that must fit. Do **not** use
  `(2**128, 2**128, 2**128 - 1)`: `C % L == 0`, second term is 0.
- `(1, 2**128, 1)`
- Compensation-gate boundary: `C = max_value(uint256) // 2` with a
  legal fixture `L` and `e = 2`
- A handful of random integer triples on the same domain

Do not import a 512-bit `mulDiv` unless those two lines cannot
express the helper. Do not touch RipeGov / SharesVault.

**Land hunks 1 and 2 before rewriting overflow-create tests.**
After hunk 1 alone, `test_g11_overflow_compensation_cash_stays_callable`
can go green on vest and then die in SharesVault. After hunk 2 the
same node must be the initiate-revert invert. Do not touch it until
both hunks are in.

---

## Hunk 2 — validator (findings 1, 2, 5)

Keep `_areValidContributorTerms(terms, hrConfig, ledger)`. No
RipeGov read. Existing zero / order / budget checks stay. Add:

```
if compensation > max_value(uint256) // 2: return False
if vestingLength > 2**128: return False
if depositLockDuration > max_value(uint256) - 2**64: return False
if startDelay > max_value(uint256) - block.timestamp: return False
startTime = block.timestamp + startDelay
if vestingLength > max_value(uint256) - startTime: return False
if cliffLength > max_value(uint256) - startTime: return False
if unlockLength > max_value(uint256) - startTime: return False
```

Keep `if maxCompensation != 0 and compensation > maxCompensation`.

**Exact acceptance / rejection (named asserts):**

| Check | Accept | Reject |
| --- | --- | --- |
| compensation | `max_value(uint256) // 2` | that `+ 1` |
| vestingLength | `2**128` | `2**128 + 1` |
| `D` | `max_value(uint256) - 2**64` | that `+ 1` (and `uint256.max`) |
| startDelay (finding 5) | representable at `block.timestamp` | `uint256.max` at initiate |

`10**40` compensation **accepts** (below `MAX // 2`). Fixture `D = 100`
**accepts** with no RipeGov row. `D = 0`, below-min, `max+1` **accept**
(Group 6’s surface).

**Finding 5 — two tests, no “or”:**

1. New `startDelay = uint256.max` with `maxStartDelay == 0`:
   `initiateNewContributor` **reverts**. No pending.
2. Initiate at the exact representable boundary, `time_travel` seconds
   so confirm-time adds overflow: confirm returns `False`, no clone,
   neither event, pending cleared.

Invert Grok / Codex / Claude constructor-overflow traces onto (1) or
(2). Enormous-but-representable delay still creates. Do not reject
`setMaxStartDelay(0)` in Delta.

**Finding 2 tests — only overflow-sized `D` changes at create.**

Re-parameterize; do not invert a setup that still deploys:

- Grok lock matrix: `0`, `50`, `100`, `1000`, `1001` still **create
  and run** cash vs transfer. `MAX` → `areValid` False and initiate
  reverts. Quote the real id; do not write `[below_precision-MAX]`.
- Codex `[dust-branch-overflow]` / `[weighted-branch-overflow]` →
  create-reject. `[dust-branch-zero]` **keep**.
- `test_g11_raw_duration_transfer_revert_rolls_back_confirm_optional_cash`,
  `test_g11_confirm_overflow_duration_after_cash_rolls_back_pending_stays`,
  Claude strand / after-cliff-no-release, Claude two-step `D=MAX`
  (~line 354), Kimi overflow confirm (~389) → create-reject.
- Kimi matrix (~436) and `D=0` (~491): only the `MAX` cell create-rejects.
- Acceptance sets (`test_g11_deposit_lock_duration_acceptance_set`,
  Kimi / Claude equivalents): `0` / 50 / 100 / 1000 / 1001 **accept**;
  `MAX` **reject**.

Named regression
`test_contributor_final_transfer_honors_its_separate_deposit_lock_term`
stays green.

There is **no** initiate→confirm band-narrow race. Do not add that
test.

---

## Hunk 3 — saturating views (finding 6)

In `getTotalCompensation` and `getTotalClaimed`, if the next add
would overflow, `return max_value(uint256)`. Do not revert.

Two stock clones at `C = MAX // 2` sum to `MAX - 1` — **no**
saturate. A third stock `MAX // 2` clone would overflow the view,
but hunk 4 then has `reserved == MAX - 1`, so
`setRipeAvailForHr(H)` **reverts** and the third clone cannot be
funded. More strongly: any official third `C` must satisfy
`C <= MAX - reserved`, so the stock `compensation()` sum cannot
overflow. Do not add a three-stock-clone saturation proof — it is
unfundable / unconstructable once finding 3 is correct. The
`hr reserve overflow` assert on `addHrContributor` is defense in
depth (not reachable through official setter+confirm for `C = H`).

Codex’s existing custom template
(`Group11AggregateViewContributor.vy`) **echoes constructor
compensation**, so it also cannot construct the overflow under the
create-gate. Do not write “if it still constructs.”

**Required reachable proof (both views).** Add
`Group11OverflowViewContributor.vy` as specified in the allowlist
(`compensation()` and `totalClaimed()` return `MAX // 2 + 1`
regardless of constructor args; HR add reserves the *terms*
compensation, which is ordinary). Two confirms with fixture
compensation and a legal budget. Then:

```
assert human_resources.getTotalCompensation() == max_value(uint256)
assert human_resources.getTotalClaimed() == max_value(uint256)
```

No revert. The custom getters are the only reason the walk
overflows; reserved stays small so both confirms succeed.

Also: two stock `MAX // 2` clones, `getTotalCompensation() == MAX - 1`
and does not revert. `getTotalClaimed()` is `0` unless cashed
(cashing `MAX // 2` is Group 6 / SharesVault — do not use stock
clones to prove claimed-view saturation).

Saturation does **not** protect against a getter that reverts or an
`O(N)` gas walk. Do not claim that.

**`test_g11_aggregate_compensation_sum_two_clones`:** invert to
initiate-revert on `2**255`. Same file: two `10**40` (or
`MAX // 2`) stock clones, view returns the exact sum and does not
revert.

Invert Codex / Kimi / Claude two-`2**255` stock-template traces to
initiate-revert. Rewrite
`test_g11_custom_template_can_overflow_both_aggregate_views` to the
new blueprint (do not keep `UINT256_MAX` budget writes).

---

## Hunk 4 — budget overwrite (finding 3)

Do **not** implement `assert _amount <= MAX // 2` as the sole guard.
That is the two-clone cancel brick in ruling 3.

`hrReservedCompensation` is outstanding uncashed, not historical
paid compensation. Add `hrReservedCompensation: public(uint256)`
next to `ripeAvailForHr`. Update only from amounts HR already
passes (no `compensation()` extcall, no walk). Increment **only**
on the new-contributor path — after
`if self.indexOfContributor[_contributor] != 0: return`, and after
the existing `ripeAvailForHr -= _compensation`:

```
# addHrContributor, new-contributor path only
self.ripeAvailForHr -= _compensation
assert self.hrReservedCompensation <= max_value(uint256) - _compensation  # dev: hr reserve overflow
self.hrReservedCompensation += _compensation

# setRipeAvailForHr
assert _amount <= max_value(uint256) - self.hrReservedCompensation  # dev: exceeds hr budget headroom
self.ripeAvailForHr = _amount

# reduceHrReservedCompensation (new, HR-only, same pause/auth as refund)
assert _amount <= self.hrReservedCompensation  # dev: hr reserve underflow
self.hrReservedCompensation -= _amount
# do not touch ripeAvailForHr

# refundRipeAfterCancelPaycheck
assert _amount <= self.hrReservedCompensation  # dev: hr reserve underflow
self.hrReservedCompensation -= _amount
self.ripeAvailForHr += _amount   # existing add; reserved now guarantees it fits
```

In `HumanResources.cashRipeCheck`, after the contributor check and
**before** mint, call `reduceHrReservedCompensation(_amount)`.
Add the method to the Ledger interface. Over-cash then fail-closes
instead of minting past reserved (clone-impersonation proofs invert;
official `Contributor.cashRipeCheck` still passes because it sends
`getClaimable()`).

Do not saturate the refund. Do not skip the underflow asserts.
Do not add a per-contributor HashMap. Do not change
`Contributor.vy` cash.

**Exact tests.**

- No clones (`reserved == 0`): `setRipeAvailForHr(MAX)` **succeeds**.
- One ordinary live clone (`reserved = C`): official Delta
  `setRipeAvailableForHr(MAX)` **reverts**
  (`# dev: exceeds hr budget headroom`). Budget unchanged, pending
  retained, no success event. `MAX - C` accepted; `MAX - C + 1`
  rejected (same rollback shape).
- `test_g11_near_uint256_budget_overwrite_keeps_cancel_live` —
  invert to the one-clone MAX revert, then a legal write
  (`<= MAX - C`) and official cancel **succeeds**.
- **Two-clone headroom (required):** confirm A and B at `C = H`
  (`H = MAX // 2`) with intervening legal budget writes.
  `hrReservedCompensation() == MAX - 1`. `setRipeAvailForHr(H)`
  and `setRipeAvailForHr(2)` **revert**; `setRipeAvailForHr(1)`
  **succeeds** (exact headroom). Write budget back to `0` before
  the cancel pair (do not leave the `1` write in place).
  Pre-cliff cancel A then cancel B both **succeed**; budget ends
  at `MAX - 1`; reserved ends at `0`; `setRipeAvailForHr(MAX)`
  then succeeds. This is the trace that a `MAX // 2`-only setter
  would fail.
- **Third stock `H` clone (required):** after the two-clone
  reserved is `MAX - 1` and budget is restored to `0`,
  `setRipeAvailForHr(H)` **reverts**, so a third `C = H` cannot be
  initiated. `getTotalCompensation()` stays `MAX - 1`. That is
  why stock clones cannot saturate the view — do not write a
  confirm-time `hr reserve overflow` proof for this cell (the
  official path dies at the setter). A third `C = 1` confirm
  **does** succeed (`1 <= MAX - reserved`); views stay exact
  (`MAX`); reserved becomes `MAX`. Keep that as a **separate**
  node from the two-clone cancel pair.
- Codex / Kimi / Claude near-uint traces invert to “MAX revert
  while any reserved > 0,” then legal write + cancel.
- **Release, not ratchet (required):** ordinary clone, cash the
  full vest, `hrReservedCompensation() == 0`, then
  `setRipeAvailForHr(MAX)` **succeeds**. After-cliff cancel of a
  partly-cashed clone also ends at reserved `0`.
- Invert clone-impersonation over-cash to revert
  (`# dev: hr reserve underflow`):
  `test_g11_hr_layer_uncapped_cash_is_clone_impersonation`,
  `test_g11c_hr_cash_ripe_check_uncapped_is_clone_impersonation_only`.
  Official owner/manager cash of `getClaimable()` stays green.
- `tests/data/test_ledger.py` (edit in place, keep passing):
  - `test_ledger_add_hr_contributor` — also assert reserved `+= C`.
  - `test_ledger_add_hr_contributor_duplicate` — reserved
    unchanged (early return).
  - `test_ledger_hr_contributor_compensation_exceeds_available` —
    reserved unchanged on the failed add.
  - `test_ledger_set_ripe_avail_for_hr` — **add first** with
    `C >= refund`, then refund; today it refunds at reserved `0`
    and will revert. Assert budget and reserved.
  - Pause-test HR block (`test_ledger_all_functions_paused`):
    refund and `reduceHrReservedCompensation` also revert
    `not activated`.

---

## Hunk 5 — merged HR config (finding 4)

Only `HR_CONFIG_MIN_CLIFF` and `HR_CONFIG_VESTING`. After merge,
before `setHrConfig`, **revert**:

```
assert not (maxVestingLength != 0 and minCliffLength > maxVestingLength)  # dev: infeasible hr config
```

`minCliffLength == maxVestingLength` **accepts**. Do not assert
`minVest > maxVest` (impossible: written together, setter already
`min < max`). Do not run this on `MAX_COMP` or `MAX_START_DELAY`.
Do not return `False`. Measure Delta before and after. If it does
not fit, stop. Do not move the check to HR / MissionControl.

**Exact tests.** Infeasible execute **reverts**; live `hrConfig`
unchanged; action retained; no HrConfig event. `minCliff == maxVest`
succeeds. Parallel pendings: second execute reverts if the merge
would be infeasible. Restore-and-create stays green.

---

## Invert checklist (every node here must **pass** at the end)

Rewrite in place until green. This is the after-diff list.

**Finding 1 / 6 create-gate (`2**255` initiate reverts):**

- `test_g11_cash_vest_proofs.py::test_g11_overflow_compensation_cash_stays_callable`
- `test_g11_cash_vest_proofs.py::test_g11_overflow_clone_pre_cliff_cancel_still_recovers`
- `test_g11_cash_vest_proofs.py::test_g11_overflow_clone_after_cliff_cancel_also_bricks`
- `test_g11_terms_budget_proofs.py::test_g11_overflow_compensation_create_succeeds_under_uncapped_max`
- `test_g11_cash_vest_proofs.py::test_g11_aggregate_compensation_sum_two_clones`
- Codex / Kimi / Claude individual-overflow and two-clone aggregate
  stock-template nodes (same invert)

**Finding 1 stays green (do not invert):**

- `test_g11_cash_vest_proofs.py::test_g11_overflow_compensation_safe_cash_control`

**Finding 2 `D = MAX` create-reject; other matrix cells still deploy:**

- Grok `test_g11_lock_matrix_cash_clamped_transfer_raw[…MAX…]` (both branches)
- Codex `[dust-branch-overflow]`, `[weighted-branch-overflow]`
- `test_g11_raw_duration_transfer_revert_rolls_back_confirm_optional_cash`
- `test_g11_confirm_overflow_duration_after_cash_rolls_back_pending_stays`
- Claude lock-matrix strand + after-cliff-no-release
- Claude two-step `D=MAX`
- Kimi overflow confirm; Kimi / Grok / Claude acceptance-set `MAX` cell

**Finding 3 reserved headroom + legal cancel:**

- `test_g11_near_uint256_budget_overwrite_keeps_cancel_live`
- Codex / Kimi / Claude near-uint nodes
- New two-`H` clone cancel pair (must **pass**)
- New third-`H` fund-revert + separate `C = 1` confirm (must **pass**)
- New full-cash then `setRipeAvailForHr(MAX)` (must **pass**)
- `test_g11_hr_layer_uncapped_cash_is_clone_impersonation` —
  invert to underflow revert
- `test_g11c_hr_cash_ripe_check_uncapped_is_clone_impersonation_only`
  — invert to underflow revert

**Finding 4 / 5** — invert to the exact behaviors above.

**Finding 6 saturation** — new / rewritten custom-template node
using `Group11OverflowViewContributor.vy` (must pass).

---

## Do not implement

- Live RipeGov-band validation; `conftest.py` / Defaults edits.
- Setter ratchet; freeze-then-cancel; residue `B+P`.
- SharesVault / RipeGov share-mint or transfer clamp.
- `setMaxStartDelay(0)` rejection in Delta.
- Contributor-count cap; clone walks; `compensation()` extcalls
  from Ledger; per-contributor reserved HashMap. (The uint256
  reserved counter plus `reduceHrReservedCompensation` **is**
  hunk 4.)
- Permanent reserved ratchet (do not ship “subtract R only”).
- Coverage matrices, registers, `evidence/`, `hardening/`.

---

## Validation

Use the 32-file counts saved at start-of-work as the after-diff
baseline (not the bind-time numbers in this document).

```
tests/core/humanResources/test_g11_*.py
tests/core/humanResources/test_user_flow_audit_group11_codex_*.py
```

**After all hunks, the ticket is not done unless all of these hold:**

1. **All 32 Group 11 files are fully green.** Zero failures, zero
   xfails, zero xpasses, zero setup errors. Every invert-checklist
   node **passes** (invert-list membership is not a license to fail).
   Record exact collected / passed counts (parametrize splits may
   change collected).
2. `tests/test_vault_pointer_runtime_sizes.py -s` — only HR / Ledger
   pins you intended. RipeGov pin unchanged from start-of-work.
   Report HR, Ledger, Delta, Contributor before → after.
   Both diagnostic prints **removed**.
3. Group 6 collision smokes (**these two nodes only**):

   ```
   tests/core/humanResources/test_g6_claude_hr_transfer.py::test_g6_hr_transfer_installs_an_unclamped_recipient_lock
   tests/core/humanResources/test_g6_claude_hr_transfer.py::test_g6_hr_transfer_recipient_can_withdraw_immediately
   ```

   **Create must succeed** (fixture + `initiateNewContributor` +
   confirm). If either errors before the unlock/withdraw assert, you
   broke `D = 0` create — abort. If they fail **only** the Group 6
   safety assert (`unlock >= minLock` / withdraw reverts), that is
   Group 6’s still-red property and is **permitted**. Do not edit
   those files. Combined shipment with Group 6 is a later owner call;
   this ticket does not require those asserts green.
4. Brief named regression — **26 passed** (25 selectors;
   `test_scenario_b_*` collects two). Run these names only:

   ```
   tests/core/humanResources/test_hr_contributor.py::test_contributor_pre_cliff_claim_stays_in_contributor_custody_until_unlock
   tests/core/humanResources/test_hr_contributor.py::test_contributor_pre_cliff_cancel_burns_claimed_position_and_stays_terminal
   tests/core/humanResources/test_hr_contributor.py::test_contributor_cancel_paycheck_success
   tests/core/humanResources/test_hr_contributor.py::test_contributor_cancel_before_future_start_keeps_terminal_views_callable
   tests/core/humanResources/test_hr_contributor.py::test_contributor_zero_share_paycheck_reverts_atomically_and_can_retry
   tests/core/humanResources/test_hr_contributor.py::test_contributor_confirm_ripe_transfer_success
   tests/core/humanResources/test_hr_contributor.py::test_contributor_final_transfer_honors_its_separate_deposit_lock_term
   tests/core/humanResources/test_hr_contributor.py::test_contributor_ownership_change_blocks_ripe_transfer
   tests/core/humanResources/test_hr_contributor.py::test_contributor_cash_ripe_check_when_frozen
   tests/core/humanResources/test_contributor_pending_state_exclusion.py::test_pending_ripe_transfer_blocks_ownership_change
   tests/core/humanResources/test_contributor_admin_state_consistency.py::test_fixture_hr_provenance_and_default_delay
   tests/core/humanResources/test_contributor_admin_state_consistency.py::test_default_minimum_frozen_handoff_has_only_initiation_warning_and_can_cancel
   tests/core/humanResources/test_contributor_admin_state_consistency.py::test_ownership_initiated_before_freeze_can_confirm_after_freeze
   tests/core/humanResources/test_contributor_admin_state_consistency.py::test_confirmed_hostile_handoff_is_irreversible_and_can_drain_after_unfreeze
   tests/core/humanResources/test_contributor_admin_state_consistency.py::test_scenario_b_raised_then_lowered_frozen_handoff
   tests/core/humanResources/test_contributor_admin_state_consistency.py::test_direct_manager_rotation_cannot_change_pending_transfer_economics
   tests/core/humanResources/test_contributor_admin_state_consistency.py::test_lite_action_signer_can_freeze_and_cancel_frozen_handoff
   tests/core/humanResources/test_contributor_admin_state_consistency.py::test_frozen_paycheck_cancellation_forfeits_vested_unclaimed_compensation
   tests/core/humanResources/test_contributor_admin_state_consistency.py::test_delay_change_after_ownership_initiation_does_not_retime_pending_action
   tests/core/humanResources/test_contributor_admin_state_consistency.py::test_pending_ownership_initiation_is_cancel_replace_with_timer_restart
   tests/core/humanResources/test_hr_add_contributor.py::test_hr_are_valid_contributor_terms_insufficient_balance
   tests/core/humanResources/test_hr_add_contributor.py::test_hr_confirm_new_contributor_success
   tests/core/humanResources/test_hr_other.py::test_hr_cash_ripe_check_not_contributor
   tests/config/test_switchboard_delta.py::test_switchboard_delta_lite_action_permissions
   tests/config/test_switchboard_delta.py::test_switchboard_delta_execute_pending_cancel_paycheck
   ```
5. Directly affected existing HR nodes — **all pass** (names, not
   whole files):

   ```
   tests/core/humanResources/test_hr_add_contributor.py::test_hr_initiate_new_contributor_success
   tests/core/humanResources/test_hr_add_contributor.py::test_hr_confirm_new_contributor_success
   tests/core/humanResources/test_hr_add_contributor.py::test_hr_are_valid_contributor_terms_success
   tests/core/humanResources/test_hr_add_contributor.py::test_hr_are_valid_contributor_terms_no_template
   tests/core/humanResources/test_hr_add_contributor.py::test_hr_are_valid_contributor_terms_zero_compensation
   tests/core/humanResources/test_hr_add_contributor.py::test_hr_are_valid_contributor_terms_insufficient_balance
   tests/core/humanResources/test_hr_add_contributor.py::test_hr_are_valid_contributor_terms_exceeds_max_compensation
   tests/core/humanResources/test_hr_add_contributor.py::test_hr_are_valid_contributor_terms_zero_cliff
   tests/core/humanResources/test_hr_add_contributor.py::test_hr_are_valid_contributor_terms_cliff_below_minimum
   tests/core/humanResources/test_hr_add_contributor.py::test_hr_are_valid_contributor_terms_zero_vesting
   tests/core/humanResources/test_hr_add_contributor.py::test_hr_are_valid_contributor_terms_unlock_greater_than_vesting
   tests/core/humanResources/test_hr_add_contributor.py::test_hr_are_valid_contributor_terms_cliff_greater_than_unlock
   tests/core/humanResources/test_hr_add_contributor.py::test_hr_are_valid_contributor_terms_empty_owner
   tests/core/humanResources/test_hr_add_contributor.py::test_hr_are_valid_contributor_terms_empty_manager
   tests/core/humanResources/test_hr_add_contributor.py::test_hr_are_valid_contributor_terms_start_delay_too_long
   tests/core/humanResources/test_hr_add_contributor.py::test_hr_are_valid_contributor_terms_vesting_below_minimum
   tests/core/humanResources/test_hr_add_contributor.py::test_hr_are_valid_contributor_terms_vesting_above_maximum
   tests/core/humanResources/test_g11_terms_budget_proofs.py::test_g11_two_overlapping_pendings_second_confirm_false_no_extra_clone
   tests/core/humanResources/test_hr_other.py::test_hr_cash_ripe_check_success
   tests/core/humanResources/test_hr_other.py::test_hr_refund_after_cancel_paycheck_no_burn
   tests/core/humanResources/test_hr_other.py::test_hr_refund_after_cancel_paycheck_with_burn_no_position
   tests/data/test_ledger.py::test_ledger_add_hr_contributor
   tests/data/test_ledger.py::test_ledger_add_hr_contributor_duplicate
   tests/data/test_ledger.py::test_ledger_add_hr_contributor_unauthorized
   tests/data/test_ledger.py::test_ledger_set_ripe_avail_for_hr
   tests/data/test_ledger.py::test_ledger_set_ripe_avail_for_hr_unauthorized
   tests/data/test_ledger.py::test_ledger_hr_contributor_compensation_exceeds_available
   tests/data/test_ledger.py::test_ledger_all_functions_paused
   ```

   `test_hr_other.py` is **not** allowlisted — those three nodes
   must stay green without editing the file. If one fails, stop.

6. `git diff --check` clean. Changed-file audit is **allowlist plus
   the two size-print files (must be print-free)**. No stray ABI
   changes on production externals.

Handoff: worktree path + branch + HEAD; 32-file collected/passed
vs start; named 26; HR + Ledger selectors; G6 create-reached
(assert outcome); runtimes; invert checklist green; prints gone;
`git diff --stat` in `$WT`. Did not edit `$SRC`. Did not commit.
