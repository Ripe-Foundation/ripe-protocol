# GuardedErc20 typed ERC-20 call candidate

> [!IMPORTANT]
> **Feature-branch candidate only.** This change is based on `rh` commit
> `7a721b9329aee3257d800924c109f0a44118486f`. It is not an `rh` integration,
> artifact reseal, deployment binding, configuration change, or activation.

## Scope

This candidate changes only GuardedErc20 token interaction semantics and its
focused tests. Teller remains unchanged.

- Every `balanceOf(address)` observation now directly uses a typed
  `staticcall IERC20(...).balanceOf(...)` with no wrapper helper.
- Withdrawal directly uses a typed
  `extcall IERC20(...).transfer(..., default_return_value=True)` with no
  wrapper helper.
- Both backing-aware getters directly compare typed custody with total nominal
  liability; there is no shared backing helper.
- GuardedErc20 contains no `raw_call`.

## Preserved behavior

The change preserves:

- Teller-only deposit accounting;
- aggregate custody covering nominal liabilities before a deposit credit;
- exact deposit credit and exact nominal-liability increase;
- pre-withdraw solvency;
- exact vault outflow and exact recipient receipt;
- post-withdraw solvency;
- exact seller and buyer deltas for internal movement;
- unchanged custody and total nominal liability during internal movement;
- authorization, pause, prohibited-recipient, nonreentrancy, and atomic rollback
  boundaries; and
- zero credit-facing value and blocked mutation when an exact typed balance
  reports custody below nominal liability.

Teller continues to own the call-local exact deposit-receipt proof. Guarded's
aggregate solvency proof does not replace it.

## Intentional typed-call differences

The prior raw helpers enforced exact returndata length and converted a failed or
malformed balance observation into an internal `(False, 0)` result. Typed calls
instead use Vyper's normal ERC-20 behavior:

- a reverting, empty, short, or malformed `balanceOf` reverts the Guarded call,
  including backing-aware views;
- a typed return may accept trailing returndata after a valid ABI value;
- an empty transfer return remains supported through
  `default_return_value=True`;
- false, malformed, short, or reverting transfers still revert; and
- exact vault-outflow and recipient-receipt assertions remain authoritative
  even when the typed transfer return is accepted.

These differences are intentional for governance-qualified ERC-20 assets. They
do not weaken the custody, nominal-accounting, or exact-delivery invariants.

## Candidate evidence

The candidate compiles with the repository-locked Vyper `0.4.3` toolchain.
Its canonical ABI, 34 function selectors, storage layout, transient layout, and
code layout remain compatible with SimpleErc20.

| Identity | Candidate value |
| --- | --- |
| Source Git blob | `77605be5fe22858b9c4a2e4f49286f937932dad3` |
| Source SHA-256 | `bb817278b748e40bb7756252b535c67976174ae71ea6fef9db3b022aaa20dc6e` |
| Creation size / SHA-256 | 10,390 bytes / `682fe2face8dcb3353c01d524b1874292dfba9813de4bed679da82ff3576c889` |
| Runtime template size / SHA-256 | 10,223 bytes / `d016b180fc3be1458baa6ac53274fa69fab8c680bb162c94ce95be948cee91cb` |
| EIP-170 headroom | 14,353 bytes |
| Canonical ABI SHA-256 | `453d702567897a4ec89f9ea25502deac64c0d86f9700c597140e5c044f51740a` |
| Selector SHA-256 | `884259b81c166e48aff3cf2d424dcddf7a64eba157a58987521206dc617b1c2b` |

Validation performed on the candidate:

- focused GuardedErc20 suite: **81 passed**;
- Guarded consumer inventory, Stock comparison, AuctionHouse Stock delivery,
  Deleverage Stock delivery, and ABI/layout comparison: **109 passed**; and
- source compilation and `git diff --check`: passed.

The reviewed `rh` artifact expectations, block-clock inventory, BluePrint
binding, and historical Guarded explainer intentionally remain bound to the
integrated `rh` artifact. Updating those authorities requires a separate
review/integration decision rather than being inferred from this feature
branch.
