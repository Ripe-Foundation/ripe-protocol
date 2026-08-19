# Group 11 Hunk 4-A+ — revised reserve / cancel-credit work order

**Status: SIGNED — implement exactly as specified.**

Architecture: **A+** (owner-signed 2026-08-18).

This document **supersedes draft 6 Hunk 4 and owner ruling 3’s
single-counter recipe** (`docs/chains/rh/user-flow-audit-group-11-implementation.md`
lines 139–163 and 461–559). Hunks 1, 2, 3, and 5 in that file stay
in force. Findings 1, 2, 4, 5, and 6 are unchanged.

Treat original Hunk 4 as **internally inconsistent**, not as a
completed implementation and not as a minor patch. One Ledger
uint256 cannot be both outstanding mintable compensation and
maximum cancellation budget credit after a pre-cliff cash.

Workspace, pytest prefix, PIN, `$SRC` / `$WT`, named-26, Group 6
smokes, and “do not edit RipeGov / SharesVault / Teller /
`conftest.py` / `test_hr_other.py` / `test_g6_*.py`” remain as in
draft 6. Combined-report hash remains
`cd377b333c9155a57e3ef1bb09ac36ad273634c9305f189ffbbc38a5a2cd2e3e`.
Do not edit that report.

There are **no optional ABI or call-order forks** in this brief.
Implement the names, signatures, asserts, and order below exactly.

---

## Why Hunk 4 cannot ship as written

Official `Contributor.cancelPaycheck` is **not** allowlisted and
must keep today’s semantics:

| Path | Contributor sends to HR | Burns position? |
| --- | --- | --- |
| Pre-cliff | full original `C` | yes |
| Post-cliff (incl. frozen) | `C - totalClaimed` after an optional cash | no |

`Contributor._cashRipeCheck` no-ops when frozen (`amount == 0 or
isFrozen: return 0`) and does **not** revert. A frozen post-cliff
cancel after a pre-cliff cash `P` therefore sends `C - P` and burns
nothing.

After `C = 100`, pre-cliff cash `P = 10`:

| Quantity | Value | Role |
| --- | ---: | --- |
| Outstanding mintable | 90 | how much this clone may still mint |
| Pre-cliff cancel budget credit | 100 | what official clawback adds to `ripeAvailForHr` |
| Frozen post-cliff cancel budget credit | 90 | `C - claimed`; no extra credit (no burn) |
| Cancel-credit liability still stored | 100 | setter headroom until this clone is settled |

A 1:1 `reserved -= amount; budget += amount` cannot do this.
A two-argument refund `(budgetCredit, reserveRelease)` cannot do
the frozen case (`90`, `90`, **`100`**) unless liability is
released by a **third** delta.

Setter using only mintable is also wrong:

```
legal write MAX - 90
pre-cliff cancel credits 100
(MAX - 90) + 100 overflows
```

The setter must reserve **cancel-credit liability**, not mintable.

There is no HashMap-free repair that preserves pre-cliff cash,
full clawback, hostile-cash safety, cancel liveness after every
legal setter write, and `MAX` headroom after a finished paycheck
when two clones overlap. Per-contributor state is required. Draft 6
“no per-contributor HashMap” is **lifted** by this brief.

---

## What this revision closes (finding 3 only)

| This brief | Still open / not this ticket |
| --- | --- |
| Every HR cash consumes **that clone’s** remaining mintable. | SharesVault / RipeGov overflows (Group 6). |
| Setter headroom is `MAX - globalCancelCreditLiability`. | Changing freeze, residue vault behavior, or Contributor cash/cancel. |
| Finished paycheck releases **both** globals for that clone. | Auto-release at `endTime` without cash or cancel. |
| Extra cancel budget credit never exceeds this grant’s HR-tracked minted paycheck. Any actually burned RIPE may back that credit; residue cannot raise the cap above tracked minted. This is **not** paycheck-token provenance (the pooled vault cannot prove that). | Per-clone leftover store beyond the grant struct. |

Do not invent a seventh finding.

---

## Lifted restrictions (explicit)

This brief authorizes, for Hunk 4-A+ only:

1. Per-contributor grant struct + HashMap on **HumanResources**.
2. Ledger global `hrCancelCreditLiability`.
3. Exactly the Ledger externals named below. **Remove**
   `reduceHrReservedCompensation` and the one-argument
   `refundRipeAfterCancelPaycheck` (they must not remain as
   production entrypoints).
4. The public `hrGrant` getter named below. No new HR
   state-changing entrypoints. `cashRipeCheck` and
   `refundAfterCancelPaycheck` **keep their current signatures**.
5. Removing any `HrContributor.cliffTime()` staticcall from
   `cashRipeCheck`.
6. One new function in the **existing**
   `tests/core/humanResources/g11_proof_helpers.py` (no new module):
   `settle_unsettled_hr_grants`, specified under Helper.

Still forbidden: RipeGov / SharesVault / Teller / Defaults /
Charlie / Alpha / `conftest.py` / `test_hr_other.py` / `test_g6_*.py`
edits; Contributor cash or cancel edits; `compensation()` extcalls
from Ledger; `O(N)` clone walks on **production** cash, refund, or
setter (the test-only helper may walk `ledger.contributors`).

---

## Allowlist delta vs draft 6

| File | Hunk 4-A+ |
| --- | --- |
| `contracts/core/HumanResources.vy` | Grant map; confirm writes the grant; cash/refund as specified. **Do not** read `msg.sender.cliffTime()`. |
| `contracts/data/Ledger.vy` | Two globals; exact externals below; **delete** the obsolete one-arg reduce/refund. |
| `contracts/modules/Contributor.vy` | **No Hunk 4-A+ edits.** Hunk 1 vest helper only. |
| `contracts/config/SwitchboardDelta.vy` | No Hunk 4-A+ edits. |
| `tests/core/humanResources/g11_proof_helpers.py` | Add `settle_unsettled_hr_grants` only. |
| Group 11 tests + `tests/data/test_ledger.py` HR-budget lines | Invert / add the proofs in “Exact tests”. |
| `tests/test_vault_pointer_runtime_sizes.py` | Pins you change. **Keep** baseline runtime prints. |

`HumanResources.refundAfterCancelPaycheck(_amount, _shouldBurnPosition)`
and `HumanResources.cashRipeCheck(_amount, _lockDuration)` **keep
their current external signatures** (`test_hr_other.py` is not
allowlisted and must stay green).

---

## Storage

### Ledger (globals only)

```
ripeAvailForHr: public(uint256)
hrReservedCompensation: public(uint256)      # SUM of remaining mintable
hrCancelCreditLiability: public(uint256)     # SUM of cancel-credit
```

**Defining invariants** (Ledger must assert these after every
write in this ticket, not only rely on HR). Express the budget
headroom invariant with overflow-safe subtraction, never
`ripeAvailForHr + liability` (that addition overflows before
the relational check can fire):

```
hrCancelCreditLiability >= hrReservedCompensation
ripeAvailForHr <= max_value(uint256) - hrCancelCreditLiability
```

The second is the setter/cancel headroom invariant. After a
legal settlement it is preserved by
`budgetCredit <= liabilityRelease`:

```
budget' <= MAX - liability'
  because budgetCredit <= liabilityRelease
  ⇒ budget + budgetCredit <= MAX - (liability - liabilityRelease)
```

### HumanResources (per contributor)

One struct, one HashMap. Production cash/refund/setter do not walk it.

```
struct HrGrant:
    initialized: bool
    remainingMintable: uint256
    cancelCreditLiability: uint256
    mintedPaycheck: uint256
    cliffTime: uint256
    settled: bool

hrGrant: public(HashMap[address, HrGrant])
```

**Exact getter ABI.** `public` generates this and only this:

```
hrGrant(_contributor: address) -> HrGrant
```

Do not add `hrGrantOf` or parallel accessors.

**Existence vs settled.** A missing Vyper mapping entry is
`initialized = False`, all uints `0`, `settled = False`. That is
**not** a settled grant. Cash and refund **require
`g.initialized`** (`# dev: hr grant not initialized`) and
**`not g.settled`** (`# dev: hr grant settled`).

`settled` is set **true** only when `initialized` is already true
and both remaining balances have just become zero. It is never
inferred from “both zeros” alone.

**Deployment assumption.** This ticket’s HR/Ledger pair is
deployed with **zero pre-existing registered contributors**.
Confirm always writes a grant for each new address. An upgrade
onto a Ledger that already has `contributors[]` entries is **out
of scope**; those addresses would have `initialized = False` and
could not cash or refund until a separate migration.

**Cliff.** On `confirmNewContributor`, after `addHrContributor`
succeeds, from the **pending terms** (adds cannot overflow):

```
self.hrGrant[contributorAddr] = HrGrant(
    initialized=True,
    remainingMintable=terms.compensation,
    cancelCreditLiability=terms.compensation,
    mintedPaycheck=0,
    cliffTime=block.timestamp + terms.startDelay + terms.cliffLength,
    settled=False,
)
```

Never read `HrContributor.cliffTime()`, `compensation()`, or
`totalClaimed()` for mint consumption, extra credit, or setter
headroom. Extra credit uses `mintedPaycheck` and the **asserted**
burn amount only.

Duplicate `addHrContributor` (early return) must not write a grant
and must not bump globals.

Custom `Group11OverflowViewContributor` getters may return
`MAX//2+1`; the grant and Ledger globals still use **terms** `C`.

---

## Ledger API (mandatory names — no alternatives)

Same pause/auth as today’s HR-only Ledger writes:
`msg.sender == addys._getHumanResourcesAddr()`,
`assert not deptBasics.isPaused`.

**Delete** `reduceHrReservedCompensation` and one-arg
`refundRipeAfterCancelPaycheck`.

### `addHrContributor` (new-contributor path only)

After `ripeAvailForHr -= _compensation`:

```
assert self.hrReservedCompensation <= max_value(uint256) - _compensation  # dev: hr reserve overflow
assert self.hrCancelCreditLiability <= max_value(uint256) - _compensation  # dev: hr cancel liability overflow
self.hrReservedCompensation += _compensation
self.hrCancelCreditLiability += _compensation
assert self.hrCancelCreditLiability >= self.hrReservedCompensation
assert self.ripeAvailForHr <= max_value(uint256) - self.hrCancelCreditLiability
```

(The last line holds if it held before: budget drops by `C` and
liability rises by `C`. Still assert it.)

### `setRipeAvailForHr`

```
assert _amount <= max_value(uint256) - self.hrCancelCreditLiability  # dev: exceeds hr budget headroom
self.ripeAvailForHr = _amount
assert self.ripeAvailForHr <= max_value(uint256) - self.hrCancelCreditLiability
```

### `consumeHrContributorCash(_mintableReduction: uint256, _liabilityReduction: uint256)`

```
assert _mintableReduction <= self.hrReservedCompensation          # dev: hr reserve underflow
assert _liabilityReduction <= self.hrCancelCreditLiability        # dev: hr cancel liability underflow
self.hrReservedCompensation -= _mintableReduction
self.hrCancelCreditLiability -= _liabilityReduction
assert self.hrCancelCreditLiability >= self.hrReservedCompensation
# do not touch ripeAvailForHr
```

### `applyHrContributorSettlement(_budgetCredit: uint256, _mintableRelease: uint256, _liabilityRelease: uint256)`

```
assert _mintableRelease <= self.hrReservedCompensation            # dev: hr reserve underflow
assert _liabilityRelease <= self.hrCancelCreditLiability          # dev: hr cancel liability underflow
assert _budgetCredit <= _liabilityRelease                         # dev: hr settlement credit exceeds liability
self.hrReservedCompensation -= _mintableRelease
self.hrCancelCreditLiability -= _liabilityRelease
self.ripeAvailForHr += _budgetCredit
assert self.hrCancelCreditLiability >= self.hrReservedCompensation
assert self.ripeAvailForHr <= max_value(uint256) - self.hrCancelCreditLiability
```

`budgetCredit <= liabilityRelease` is what keeps
`ripeAvailForHr <= MAX - liability` when HR miscomputes. Do not saturate.
Ledger does not see burn; HR still enforces the extra-credit cap
before this call. Official pre-cliff `(100, 90, 100)` and frozen
`(90, 90, 100)` both satisfy `budgetCredit <= liabilityRelease`.

---

## HumanResources transitions

Revert reasons that tests name: `# dev: hr reserve underflow`,
`# dev: hr grant settled`, `# dev: hr grant not initialized`,
`# dev: ripe burn failed`.

### Create (confirm)

`addHrContributor(addr, C)` then write `hrGrant` as specified.

### Cash (`cashRipeCheck`) — every call, no time-dependent skip

After pause + `isHrContributor`, **before mint**:

```
g: HrGrant = self.hrGrant[msg.sender]
assert g.initialized                          # dev: hr grant not initialized
assert not g.settled                          # dev: hr grant settled
assert _amount <= g.remainingMintable         # dev: hr reserve underflow
g.remainingMintable -= _amount
g.mintedPaycheck += _amount
liabilityReduce: uint256 = 0
if block.timestamp >= g.cliffTime:
    if g.cancelCreditLiability > g.remainingMintable:
        liabilityReduce = g.cancelCreditLiability - g.remainingMintable
        g.cancelCreditLiability = g.remainingMintable
if g.remainingMintable == 0 and g.cancelCreditLiability == 0:
    g.settled = True
self.hrGrant[msg.sender] = g
extcall Ledger(a.ledger).consumeHrContributorCash(_amount, liabilityReduce)
# then existing mint + teller deposit
```

- Consume **this** clone’s mintable only.
- Pre-cliff: `liabilityReduce == 0`.
- Post-cliff: liability pulled down to remaining mintable.
- Do **not** call the clone for cliff.

### Refund (`refundAfterCancelPaycheck`) — exact order

`_amount` is caller-supplied. HR must not trust it past the cap.

**Mandatory order:**

1. Load grant; `assert g.initialized` and `assert not g.settled`.
2. If `_shouldBurnPosition`:
   existing withdraw-to-burn + Lootbox `updateDepositPoints`, then:

   ```
   burnAmount = min(withdrawalAmount, ripe.balanceOf(self))
   actualBurned = 0
   if burnAmount != 0:
       assert extcall RipeToken(a.ripeToken).burn(burnAmount)  # dev: ripe burn failed
       actualBurned = burnAmount
   ```

   Assign `actualBurned` **only after** a successful burn (or leave
   `0` when `burnAmount == 0`). A `False` return or revert rolls
   back the whole call. If `_shouldBurnPosition` is false, do not
   touch the vault; `actualBurned = 0`.
3. Compute the three deltas from the **post-burn** grant and
   `actualBurned`.
4. Mutate and store the grant (including `settled`).
5. `applyHrContributorSettlement`.

Burn and Lootbox **complete before** grant mutation and Ledger
settlement because `actualBurned` authorizes extra credit.

```
# after step 2
mintableRelease = min(_amount, g.remainingMintable)
extraWanted = _amount - mintableRelease
maxExtra = min(g.mintedPaycheck, actualBurned)
assert extraWanted <= maxExtra                # dev: hr reserve underflow
budgetCredit = _amount

g.remainingMintable -= mintableRelease
if g.remainingMintable == 0:
    liabilityRelease = g.cancelCreditLiability
    g.cancelCreditLiability = 0
    g.settled = True
else:
    liabilityRelease = mintableRelease
    assert g.cancelCreditLiability >= liabilityRelease
    g.cancelCreditLiability -= liabilityRelease

self.hrGrant[msg.sender] = g
extcall Ledger(a.ledger).applyHrContributorSettlement(
    budgetCredit, mintableRelease, liabilityRelease
)
```

**Extra-credit policy (precise):**

```
maxExtra = min(this grant’s mintedPaycheck, actualBurned)
```

Any actually burned RIPE may back the extra credit, but extra
credit can **never** exceed this grant’s HR-tracked minted
paycheck. Residue `B` cannot raise the cap above that tracked
amount. This does **not** prove the burned tokens were the
paycheck tokens; the pooled vault cannot prove provenance
without more accounting. Do not claim that it does.

- Official pre-cliff after cash `P`, burn `>= P` (position may
  also contain `B`): `maxExtra = P`. Official `_amount = C` ⇒
  `extraWanted = P` if all cash went through HR.
- Official / frozen post-cliff: no burn, `maxExtra = 0`, so
  `_amount` cannot exceed remaining mintable.
- Burn shortfall (`actualBurned < mintedPaycheck`) on a pre-cliff
  cancel that asks for full `C`: revert the whole cancel.
- Zero prior cash, `burnAmount == 0`: `extraWanted = 0`. Today’s
  `test_hr_refund_after_cancel_paycheck_with_burn_no_position`
  still works.

Worked examples (`C = 100`, `P = 10`):

| Event | budgetCredit | mintableRelease | liabilityRelease |
| --- | ---: | ---: | --- |
| Pre-cliff cash `10` | 0 | 10 (cash) | 0 |
| Official pre-cliff cancel after that cash | **100** | **90** | **100** |
| Later post-cliff cash of remaining `90` (no cancel) | 0 | 90 (cash) | 100 (cash sync) |
| Frozen post-cliff cancel after pre-cliff cash `10` | **90** | **90** | **100** |
| `test_hr_other` refund `25K`, no burn, no prior cash | 25K | 25K | 25K |

### Full vest without cancel

Last cash is at/after `endTime` ⇒ after stored cliff. The cash
pseudocode sets `settled = True` when both balances hit zero.
Then `setRipeAvailForHr(MAX)` succeeds (after test cleanup of
any other live grants — see Helper).

### Failed / paused paths

- HR or Ledger paused: existing `contract paused` / `not activated`.
- `initialized == False`: `# dev: hr grant not initialized`.
- Retry after revert: grant, both globals, budget, vault, and
  Contributor cancel fields unchanged.

---

## Helper (mandatory, existing module only)

Session-scoped fixtures leave registered contributors in the
Ledger. Tests that assert both globals `== 0` or
`setRipeAvailForHr(MAX)` success are otherwise false.

**Remove** `cancel_live_contributors` from
`test_g11_terms_budget_proofs.py` and all imports of it.

**Add** to `g11_proof_helpers.py` exactly this (name + contract).
There is **no** `except_addr` / keep-set. The helper settles
every initialized unsettled grant, including a live
`contributor_contract` fixture.

```
def settle_unsettled_hr_grants(human_resources, ledger):
    """Deterministic test-only settlement. Fail loudly."""
    n = ledger.numContributors()
    for i in range(1, n):
        addr = ledger.contributors(i)
        g = human_resources.hrGrant(addr)
        if not g.initialized or g.settled:
            continue
        human_resources.refundAfterCancelPaycheck(
            g.remainingMintable, False, sender=addr
        )
        g2 = human_resources.hrGrant(addr)
        assert g2.settled
    assert ledger.hrReservedCompensation() == 0
    assert ledger.hrCancelCreditLiability() == 0
```

**Ordering (mandatory).** Tests that need a clean global pair or
that will create their own A/B (or one ordinary clone) as the
subject:

1. Call `settle_unsettled_hr_grants` **first**.
2. **Then** create the subject grant(s) through the official
   initiate/confirm (or `make_contributor` / `initiate_contributor`)
   path.
3. Do **not** request the session `contributor_contract` /
   `deployedContributor` fixture in those tests. That fixture is
   already created before the test body runs; the helper would
   settle it (or, if called after, settle the subject).
4. Do **not** pass `except_addr`. Remove that pattern with
   `cancel_live_contributors`.

After the subject is created, do not call the helper again until
the test has finished asserting that subject’s grant, unless the
test has already cancelled/settled the subject itself and wants
a global-zero / `MAX` write.

Rules for the helper:

- Uses HR grant state and `refundAfterCancelPaycheck(remainingMintable, False)`.
  When remaining mintable is `0` and liability is not, `_amount = 0`
  is the specified non-extra-credit terminal path
  (`mintableRelease = 0`, `liabilityRelease = remaining liability`).
- No `Contributor.at`, no bytecode length, no `endTime`, no
  `except Exception`, no Switchboard impersonation, no official
  cancel (ended clones cannot cancel).
- Every test that asserts both globals are `0` or that
  `setRipeAvailForHr(MAX)` **succeeds** must follow the ordering
  above. Tests that only check deltas against a recorded baseline
  do not have to call the helper.

Do not add another helper module. Do not reintroduce
bytecode-size cleanup.

---

## Exact tests (in addition to draft 6 invert checklist)

Keep checklist **function names**. Update docstrings. Every node
below must **pass**.

### Hostile cash (two-clone, not self-contradictory)

1. Settle leftovers, then create two ordinary clones A and B
   (no fixture clone), each with remaining mintable `C > 0`.
2. A calls `cashRipeCheck(A.remainingMintable, …)` and exhausts A.
3. Global mintable remains `== B.remainingMintable` and is `> 0`.
4. A calls `cashRipeCheck(1, …)`.
5. `1 <=` global mintable and `1 > A.remainingMintable` (now 0).
6. Revert `# dev: hr reserve underflow`. Globals, B’s grant, and
   A’s grant unchanged by the second call.

Separately: custom template with `cliffTime() = MAX` still
consumes mintable on every cash. After A is exhausted, a further
in-range-vs-global call still reverts.

Existing `2C` / `1000C` impersonation nodes stay underflow
reverts (`_amount > remainingMintable`).

### Setter / cancel liveness after early cash

Ordinary clone, cash `P` before stored cliff. Follow helper
ordering: settle leftovers first, then create this clone (and
optional B). Do not use `contributor_contract`.

1. `setRipeAvailForHr(MAX)` reverts.
2. `setRipeAvailForHr(MAX - (C - P))` **reverts** (liability is
   still `C`).
3. `setRipeAvailForHr(MAX - C)` **succeeds**.
4. `setRipeAvailForHr(MAX - C + 1)` reverts.
5. Official Delta pre-cliff cancel **succeeds** after (3);
   budget `+= C`; this grant settled; if no other live grants,
   both globals `0` and `setRipeAvailForHr(MAX)` succeeds.

At least one node also has overlapping live clone B so a global
“gap = P” catch-up cannot steal B’s cancel headroom.

### Release, not ratchet

Periodic vest tests (Claude / cash_vest_proofs / Kimi timestamp
progressions): settle leftovers first, then create the subject
(no fixture clone) if the test will assert global zeros or a
`MAX` write. After `totalClaimed == compensation`, that grant
is settled. Do not call the helper while the subject is still
the grant under assertion.

New: settle leftovers, then create the subject (no fixture
clone). Cash `P` before cliff, cash the rest at `endTime`; this
grant settled; both globals `0`; `MAX` write succeeds. Do not
call the helper between create and those asserts.

New: cash `P` before cliff, official unfrozen cancel after cliff;
this grant settled.

Draft 6 full-vest-at-`endTime` and after-cliff-only partial cash
+ cancel remain green and must assert this grant settled.

### Frozen cancel

Cash `P` before cliff, freeze, official cancel after stored
cliff: settlement `(C-P, C-P, C)`; budget `+= C-P`; grant
settled. Named-26 frozen-forfeit node stays green (no file edit).

### Extra-credit / residue / shortfall / nested failure

- Pre-cliff cash `P`, official pre-cliff cancel, vault has only
  the paycheck: budget `+= C`, burn `P`, grant settled.
- Same with residue `B`: burn may be `B+P`; budget still `+= C`;
  `maxExtra` stays `P`. Do not claim this proves paycheck
  provenance.
- Pre-cliff cash `P`, position moved so `actualBurned < P`,
  official pre-cliff cancel of `C` **reverts**; grant, both
  globals, budget, vault, and Contributor compensation / claimed /
  endTime unchanged. Retry after restoring paycheck tokens
  succeeds.
- **Failed burn:** `burnAmount > 0` and `RipeToken.burn` returns
  `False` or reverts → `# dev: ripe burn failed` (or the token
  revert). Same rollback snapshot as the shortfall case.
- **Lootbox or vault withdraw revert** on the burn path: same
  rollback snapshot (grant, budget, both globals, vault position,
  Contributor cancel fields unchanged).
- Zero `burnAmount`, `_amount == remainingMintable`: succeeds.

### Near-uint / two-`H` / third-`H`

Setter assertions use **`hrCancelCreditLiability`**. Settle
leftovers first, then create A and B (no `contributor_contract`).
After two `H` clones with no cash, both globals are `MAX-1`. After
both pre-cliff cancels of those same handles, both globals are
`0` (do not call the helper between create and that assert). A
third `H` cannot be funded while liability is `MAX-1`. `C = 1`
still confirms when liability is `MAX-1` and budget is `1`.

### Pause / retry

Paused Ledger: both new Ledger externals revert `not activated`.
Charlie pause of HR: official cash/cancel revert; pending Delta
cancel retries after unpause.

### `tests/data/test_ledger.py`

- Create bumps **both** globals by `C`; post-write invariants hold.
- Duplicate add: both unchanged.
- Failed add: both unchanged.
- Setter uses **liability**.
- Settlement happy path: official-shaped `(C, C-P, C)` and
  frozen-shaped `(C-P, C-P, C)` with `P > 0`.
- Negative settlement (budget and both globals **unchanged**):
  - `mintableRelease > hrReservedCompensation`;
  - `liabilityRelease > hrCancelCreditLiability`;
  - `budgetCredit > liabilityRelease`;
  - a triple that would leave
    `liabilityAfter < mintableAfter`
    (e.g. `liabilityRelease` large and `mintableRelease` small
    enough to invert the gap).
- Direct `consumeHrContributorCash` proofs (impersonate HR; do
  **not** rely on `HumanResources.cashRipeCheck` — per-grant
  checks would hide Ledger):
  - Setup: `addHrContributor` once so mintable = liability = `C`,
    then a valid pre-cliff-shaped consume `(_P, 0)` so mintable
    is `C-P` and liability stays `C` (the gap).
  - Valid catch-up: `consumeHrContributorCash(C-P, C)` leaves
    both globals `0` and `liability >= mintable`.
  - Negative (budget and both globals **unchanged**):
    - `_mintableReduction > hrReservedCompensation`;
    - `_liabilityReduction > hrCancelCreditLiability`;
    - a pair that would leave `liabilityAfter < mintableAfter`
      (e.g. after the `(_P, 0)` gap, `consumeHrContributorCash(0, C)`
      would drop liability to `0` while mintable is still `C-P`).
- Pause block includes `consumeHrContributorCash` and
  `applyHrContributorSettlement` (not the deleted one-arg APIs).

---

## Size

Measure HR and Ledger after Hunk 4-A+. Update only those pins.
RipeGov `23493`, Teller `24556`, AuctionHouse `24568` stay.
If any hunk would reach **24,576**, or you would weaken a check
to fit — **stop**. Keep baseline runtime prints; delete only
temporary Delta/Contributor instrumentation.

Draft-6 start-of-work sizes at `3822a59` are the “before” column.
The current unsafe-compromise sizes are **not** the baseline.

---

## Validation (after signature + implementation)

Same gates as draft 6, plus every node in “Exact tests”:

1. 32 Group 11 files fully green (record collected / passed).
2. Runtime-size test green; HR / Ledger / Delta / Contributor
   before (`3822a59`) → after; baseline prints present;
   temp prints gone.
3. Two Group 6 smokes: create reached; unlock/withdraw assert
   failures permitted.
4. Named 26 passed, including pre-cliff cancel-after-cash
   (budget `+= C`) and the frozen-forfeit node.
5. Directly affected HR/Ledger selectors passed;
   `test_hr_other.py` untouched.
6. `git diff --check` clean; `$SRC` clean; no commit unless asked.

Handoff must include: worktree + branch + HEAD; 32-file counts vs
start-of-work; named 26; HR+Ledger selectors; G6 outcome; runtimes;
invert checklist; this brief’s extra proofs; “Hunk 4-A+ signed and
implemented”; `$SRC` untouched. Commit and PR were deferred until
a final production-code review after validation.

---

## Historical pre-signing state

Group 11 was **blocked / incomplete**. The pre-cliff
check-without-consume branch was a reusable mint allowance and a
permanent ratchet. That 270/270 run was not shipment-ready.
A PR from `impl/g11-hr-safety` was not authorized until
implementation and review completed.

---

## Owner signature

```
A+ Hunk 4 revised brief
Status: SIGNED

I have reviewed this document and authorize implementation
in $WT on impl/g11-hr-safety as specified. Original draft 6
Hunk 4 and the single-counter setter recipe in ruling 3 are
superseded. HashMap / refund-ABI / HR-grant restrictions are
lifted to the extent written here.

Signed: owner  Date: 2026-08-18
```
