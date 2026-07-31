# Teller balance and receipt measurement reassessment

Status: architectural research only. This report does not authorize a contract,
interface, ABI, configuration, migration, deployment, activation, or release
change.

## 1. Executive recommendation

**Preserve the current Teller deposit design. Do not replace the strict
balance helper, remove the transient measurement mutex, or extend this slice
into a generic Teller withdrawal mechanism.**

The current mechanism is correctly located at the contract that owns every
current production deposit transfer boundary. Subject to a truthful
`balanceOf`, it proves the call-local invariant that the resolved destination
vault's custody increased by exactly the validated amount `Q`, and it keeps that
proof isolated from nested Teller deposit accounting until the vault has
returned exactly `Q`.

The variable named `receiptMeasurementActive` is best understood as a
**deposit-receipt measurement mutex**:

- it identifies a measurement/accounting phase;
- it locks only overlapping `_deposit` measurement windows;
- it is a narrow reentrancy control for those windows; and
- it is not Teller's general reentrancy guard.

The raw call is deliberate strictness, not broader nonstandard-token support.
It rejects every `balanceOf` response except one successful, exactly 32-byte
word. An independently compiled typed Vyper call accepted trailing data and
decoded the first word of a 64-byte dynamic-shaped response. Replacing the
helper with that typed call would save 74 runtime bytes and approximately 914
compiler-estimated gas per `_deposit`, but would weaken the approved
return-shape invariant.

No production implementation delta is recommended from this reassessment.
That recommendation depends on preserving Teller's vault-result equality and
the current production call graph. The legacy typed
`min(Q, balanceOf(vault))` clamps remain in `BasicVault`, `SharesVault`, and
`StabVault`; M1 neutralized rather than deleted them. The four non-governance
vault entry points and RipeGov's zero-lock entry are Teller-only, while
RipeGov's lock-duration entry accepts any valid Ripe address even though Teller
is its only current production caller.

The clearest safe next work is test and documentation hardening:

1. pin the authorized caller and exact-return closure for every vault deposit
   entry, including the broader RipeGov lock-duration authorization;
2. cover the callback cross-product from undecorated
   `depositIntoGovVault` and `depositFromTrusted` windows;
3. pin Teller versus vault responsibility for nonexact withdrawals, especially
   for non-Guarded vaults;
4. cover no-return transfers, a caught nested rejection with an exact outer
   receipt, and the three distinct balance-read policies in one deposit;
5. cover a real proxy/implementation-change model; and
6. replace the now-stale "known gaps" section in the existing Teller rationale
   with the post-hardening T1-T7 evidence.

The current source should not be changed merely to rename the mutex or add
comments. Teller has only 424 bytes of EIP-170 runtime headroom, any source
change invalidates the frozen artifact identity and the T1 mutant-source hash,
and renaming the flag also breaks T1's four exact removal strings. The
controlling owner disposition prohibits spending bytecode headroom on that
readability-only change. Any separately authorized future Teller edit must
still update and revalidate the mutation harness.

## 2. Exact baseline and changed-line inventory

### Frozen authority and isolated worktree

| Item | Verified value |
| --- | --- |
| Authority commit | `0d5994aa78f9d6f35b59bd7a2bc70fa18706e693` |
| Authority tree | `b68dffdddbdc7c5ae8423db049099c1632b478c9` |
| Branch | `codex/rh-reassess-teller-measurement` |
| Isolated worktree | `/private/tmp/ripe-rh-teller-reassess.VwMGvy` |
| Worktree directory mode | `0700` |
| Initial state | clean |
| Primary worktree | not modified |

The supplied commit resolved to the supplied tree before the branch/worktree
was created. The requested branch did not previously exist.

### Current relevant identities

| Path | SHA-256 |
| --- | --- |
| `contracts/core/Teller.vy` | `4afc6ce1ccf21cb65e04ce3c56fedcf60bb79cba8e7dc51fd855a1f1f82bd909` |
| `contracts/core/TellerUtils.vy` | `c6351363db4f77318584dfc60b868f847ec894221ada37007b118881e254ecfe` |
| `interfaces/Vault.vyi` | `6769283fa780a63e1b2e2fc56b8ef51f3ff9b5883f4f1c4af8905fd0b20ffde7` |
| `contracts/mock/MockStockTokenControls.vy` | `5d1527262aad66642a6e0f6dfdaad03458abdc4085a0445ebff0af8969614ef7` |
| `docs/chains/rh/smart-contract-changes/teller.md` | `9673fd6c29dffab5d8abf20ddaf29dc611ebd6192c5db2a4f8f8d917506ce587` |

The integrated implementation is commit
`66eae5ac516466be360fe53a53a4bcd672c1ed23`, with parent
`ee07d9b6b4ae85f76646617051ec7d331e30a824`. Its exact four-path numstat is:

| Path | Added | Deleted | Purpose |
| --- | ---: | ---: | --- |
| `contracts/core/Teller.vy` | 25 | 12 | strict custody reads, exact delta, vault-result equality, transient mutex |
| `tests/core/teller/test_teller_deposit.py` | 990 | 1 | direct, trusted, callback, malformed-return, atomicity, and route evidence |
| `tests/core/teller/test_teller_rebalance.py` | 62 | 0 | deposit-first failure and whole-rebalance rollback |
| `tests/vaults/test_stock_token_vault_comparison.py` | 60 | 16 | multi-user and donation masking regressions |

The functional Teller changes, at current source lines, are exactly:

- line 217: add `receiptMeasurementActive: transient(bool)`;
- lines 289-291: reject overlap, set the flag, and read custody `C0`;
- line 297: read `C1` and require checked `C1 - C0 == Q`;
- lines 300-303: require the selected vault entry point to return exactly `Q`;
- line 305: clear the flag;
- lines 1012-1022: add the internal exact-length `_exactBalance` helper.

The remaining Teller diff is blank-line cleanup and a final newline. No later
commit through the frozen authority changes `contracts/core/Teller.vy`.

Relevant later evidence is separate from the implementation:

| Commit | Effect relevant to this reassessment |
| --- | --- |
| `77bfa69fb1510946e92dc6491f22d998799e194d` | adds the Teller rationale document |
| `a2d6b940c9b90d9ff1c78560ad61b2dd546f1760` | adds composed AuctionHouse and Deleverage route proofs; no Teller source change |
| `84b16e6482e6557470cfc21efe22f044384c7916` | adds mutation-sensitive Teller T1-T5 tests and freezes Teller artifact/layout identities; no Teller source change |

### Compiler and artifact inventory

Pinned compilation used CPython 3.12.0, Vyper 0.4.3, Titanoboa 0.2.7, and
codesize optimization.

| Property | Current Teller |
| --- | ---: |
| ABI entries | 131 |
| External function selectors | 123 |
| Events | 7 |
| Creation bytecode | 24,387 bytes |
| Runtime bytecode | 24,152 bytes |
| EIP-170 headroom | 424 bytes |
| Compiler gas estimate: `deposit` | 121,948 |
| Compiler gas estimate: `depositFromTrusted` | 134,370 |
| Compiler gas estimate: `depositIntoGovVault` | 127,606 |
| Runtime SHA-256 | `39ffa8d3274b74c91896a36c4d2ce9d6df5c197758a89fbfd1589b394dad5b81` |
| Creation SHA-256 | `b94a58ac0faa6cad71e58f451cb9aea27a7152bf63bfc65798103d3b97704e5a` |
| Persistent storage | inherited `deptBasics.isPaused`, slot 0 |
| Transient slot 0 | Vyper `$.nonreentrant_key` |
| Transient slot 1 | `receiptMeasurementActive` |

The repository artifact checker independently returned
`CONTRACT_ARTIFACTS_OK` for Teller at the frozen tree.

## 3. Current lifecycle/state-machine explanation

### State and transition

`receiptMeasurementActive` is transient storage, not persistent storage. Its
logical lifecycle within one EVM transaction is:

```text
IDLE (false)
  |
  | validate route, source, amount, limits, and Q
  | require flag == false
  v
MEASURING_AND_ACCOUNTING (true)
  | C0 = strict balanceOf(asset, resolved vault)
  | transfer Q to the resolved vault
  | C1 = strict balanceOf(asset, resolved vault)
  | require checked C1 - C0 == Q
  | call selected vault accounting entry point with Q
  |   - typed balanceOf(vault) and legacy min(Q, aggregate balance)
  |   - StabilityPool also performs static price/conversion reads
  | require vault result == Q
  v
IDLE (false)
  | Ledger participation
  | Lootbox points
  | optional housekeeping / debt update / Curve snapshot
  | PriceDesk asset snapshot
  | event and return
```

The exact transitions occur only in [`Teller._deposit`](../../../../contracts/core/Teller.vy):

1. `false -> true` at lines 289-290, after `validateOnDeposit` returns `Q`
   and before the pre-transfer custody observation;
2. the value remains `true` across the pre-read, token transfer, post-read,
   delta assertion, vault callback, and vault-result assertion; and
3. `true -> false` at line 305, before every Teller-initiated Ledger, Lootbox,
   housekeeping, final price snapshot, event, or return action.

There is no successful branch between acquisition and line 305. Every failure
in that interval reverts rather than returning around the clear.

### Invariant protected while true

Define:

```text
Areq = caller's raw amount
Q    = amount returned by TellerUtils.validateOnDeposit
C0   = strict vault custody immediately before transfer
C1   = strict vault custody immediately after transfer
V    = selected vault deposit function's result
```

While the flag is true, Teller protects:

```text
no second Teller _deposit measurement may overlap this interval
C1 >= C0
C1 - C0 == Q
V == Q
```

The overlap exclusion is necessary because a nested Teller deposit into the
same custody address could add units between `C0` and `C1`, allowing an outer
short transfer to appear exact while crediting the nested units once to the
nested user and again as part of the outer receipt. It does not stop the token
itself from donating or minting a missing unit directly to the vault. The
Boolean is global across assets and vaults, so it also rejects harmless
cross-asset nested deposits during the interval. That is a conservative
liveness cost.

### Deposit-route coverage

Every current Teller vault deposit reaches the same internal state machine:

| Route | Entry characteristics | Transfer source |
| --- | --- | --- |
| `deposit` | ordinary public, Vyper `@nonreentrant` | depositor via `transferFrom` |
| `depositMany` | ordinary public, one acquire/release per row | depositor via `transferFrom` |
| `depositFromTrusted` | authorized Ripe caller; no ordinary Teller decorator, required by known callback routes | trusted caller via `transferFrom` |
| `rebalance` | public `@nonreentrant`; deposit completes before withdrawal | rebalance caller via `transferFrom` |
| `convertToSavingsGreenAndDepositIntoStabPool` | public `@nonreentrant`; GREEN is converted first | Teller-held sGREEN via `transfer` |
| `depositIntoGovVault` | public for `_user == msg.sender`; delegated-user check otherwise; no ordinary Teller decorator | caller via `transferFrom` |

`_areFundsHereAlready` changes the transfer source from the depositor to Teller
but does not change the measured party: the resolved destination vault is
always measured.

Trusted callbacks include StabilityPool/StabVault, Deleverage, HumanResources,
Lootbox, BondRoom, CreditEngine, and the source-level CreditRedeem path. The
first legitimate `depositFromTrusted` callback begins with the measurement flag
clear even when the outer Teller action holds Vyper's ordinary nonreentrant
key.

### Vault-side caller and return closure

All current production calls to a vault deposit entry originate in
`Teller._deposit`. `SimpleErc20`, `RebaseErc20`, `GuardedErc20`, and
`StabilityPool` each require `msg.sender == Teller` for
`depositTokensInVault`. RipeGov applies the same Teller-only check to its
zero-lock `depositTokensInVault`.

The lock-duration endpoint is materially different:
`RipeGov.depositTokensWithLockDuration` accepts any caller for which
`Addys._isValidRipeAddr(msg.sender)` is true. The only current production
callsite found for that endpoint is Teller, so the current callsite graph is
closed but the authorization boundary is not Teller-only. A future or existing
valid Ripe contract can call it directly unless separately constrained.

Every current Teller call requires the vault result to equal `Q`. That equality
is load-bearing because the three legacy vault modules still derive
`depositAmount` from typed aggregate custody. The closure is therefore:

```text
current production transfer enters Teller _deposit
  -> Teller proves strict C1 - C0 == Q
  -> vault performs its typed aggregate-balance accounting
  -> Teller requires returned V == Q
```

It would be incorrect to generalize this into a claim that every vault deposit
entry is authorized only for Teller.

### Withdrawal, transfer, and snapshot boundaries

Teller's exact-receipt state machine is deposit-only.

- `withdraw` and `withdrawMany` call
  `Vault.withdrawTokensFromVault(..., recipient=_user)` and trust its returned
  amount and depletion flag.
- `rebalance` completes its measured deposit first, then performs the
  withdrawal, then higher-risk housekeeping. Any later failure rolls back the
  measured deposit.
- `SimpleErc20/BasicVault` and `RebaseErc20/SharesVault` check a transfer
  Boolean but do not measure the recipient's before/after balance.
- `GuardedErc20` separately measures both the vault outflow and recipient
  increase on withdrawal. This is the exact outbound Stock Token boundary.
- Internal `transferBalanceWithinVault` moves accounting, not token custody;
  Guarded verifies nominal deltas and unchanged custody.
- `_handleGreenPayment`, GREEN-to-sGREEN conversion, and bond payment
  transfers use typed ERC-20 calls and are outside the deposit receipt window.
  If a downstream component later calls `depositFromTrusted`, that call starts
  its own window.

The final `PriceDesk.addPriceSnapshot(asset)` call occurs after the flag is
cleared. Housekeeping likewise occurs after the clear and may update Ledger,
`CurvePrices`, and CreditEngine. The T5 hardening test proves that an authorized
post-clear snapshot callback can begin a fresh measurement successfully.

That does not place all price-related I/O after the clear. During a
StabilityPool vault call, `StabVault._depositTokensInVault` uses typed
`balanceOf(self)` and then static-calls either
`IERC4626.convertToAssets` or `PriceDesk.getUsdValue`; it also values claimable
assets before returning. Those reads cannot reenter because they are
`STATICCALL`s, but a revert or gas-consuming implementation fails the deposit
inside the measurement window and rolls the entire transaction back.

### Ordinary versus measurement-specific reentrancy

The ordinary Vyper key covers the principal public action surface: ordinary
deposit/withdraw/rebalance, debt, redemption, liquidation, auction, stability,
reward, lock-management, and bond actions. It cannot be added naively to
`depositFromTrusted`, because an outer nonreentrant Teller action can call a
trusted component that must callback into Teller to deposit proceeds. No
equivalent necessity was found in source or history for the missing decorator
on `depositIntoGovVault`.

The following relevant entries are not substitutes for the ordinary key:

- `depositFromTrusted` relies on Ripe-address authorization plus the measurement
  mutex for nested `_deposit` exclusion;
- public same-user `depositIntoGovVault` relies on the measurement mutex, not
  caller authorization, for nested `_deposit` exclusion;
- Deleverage entry points delegate to Deleverage and do not use the receipt
  flag unless a later trusted deposit occurs;
- configuration/delegation helpers and external `performHousekeeping` are
  outside the measurement invariant; and
- the receipt flag does not block a non-deposit Teller function merely because
  a measurement is active.

It is therefore inaccurate to call the flag Teller's reentrancy guard without
qualification. It is a reentrancy control only for overlapping deposit receipt
measurements.

## 4. Rationale reconstructed from Git, tests, and evidence

Before M1, Teller:

1. validated the raw request into `Q`;
2. transferred `Q` to the vault;
3. asked the vault to infer the deposit amount from aggregate post-transfer
   custody; and
4. overwrote Teller's amount with whatever the vault returned.

Before M1, and still in the frozen tree, `BasicVault` uses:

```text
depositAmount = min(Q, balanceOf(vault))
```

That balance includes every prior user's backing and any donation. If custody
already exceeded `Q`, a token could deliver `Q-1` on the new transfer and the
vault could still return and credit `Q`. `SharesVault` and `StabVault` retain
the same typed aggregate-balance clamp, and Shares/Stab reconstruct a presumed
pre-deposit balance from the post-transfer aggregate and `Q`. None can recover
the missing `C0` after Teller has already transferred.

M1 did not delete those expressions. It made the defect dormant on current
Teller routes by proving the transfer delta before accounting and then requiring
the vault's returned `V == Q`. A vault clamp that silently reduces the credited
amount below `Q` now reverts the whole Teller transaction. A direct caller of a
vault endpoint would not inherit Teller's receipt proof or equality check; this
is why both the current caller graph and RipeGov's broader lock-duration
authorization are part of the security boundary.

The selected M1 design followed from three facts:

- Teller owns every current production transfer boundary for ordinary, batch,
  trusted, Teller-held, rebalance, and governance-vault deposits;
- Teller is the current component positioned to observe custody immediately on
  both sides of that transfer; and
- moving the transfer into every vault or adding prepare/finalize interfaces
  would broaden approvals, callbacks, storage, ABIs, and migration scope.

The implementation commit added the smallest shared proof. Later evidence
strengthened, rather than changed, that architecture:

- the original M1 tests cover zero, short, percentage-fee, excess, false,
  reverting, custody-decreasing, malformed-balance, vault-result, batch,
  governance-vault, trusted-producer, Teller-held, and rebalance cases;
- the T1 no-mutex mutant turns an outer `Q-1` receipt plus a nested unit into
  false nominal credit, while the current source rejects it;
- T2 proves the flag remains active during the vault callback;
- T3 proves a caught failed Teller call rolls transient state back so a second
  deposit can succeed in the same transaction;
- T4 deliberately demonstrates that a canonical but false balance report can
  defeat the proof; and
- T5 proves post-clear callbacks start a fresh measurement rather than being
  globally disabled.

The current rationale document predates those T1-T5 additions. Its statements
that the mutex test is not mutation-sensitive, vault callback mode 5 is unused,
and rollback requires manual transient clearing are historical gaps, not
current-tree gaps.

## 5. `raw_call` analysis

### Exact behavior

The helper constructs `balanceOf(address)` calldata, makes a static call with
`max_outsize=33`, requires the returned dynamic byte length to be 32, and
decodes one `uint256`.

| Token call/result | Current strict helper |
| --- | --- |
| call reverts or exhausts gas | reverts |
| EOA/no-code target; empty success | rejects; typed Vyper also rejects, so this is not a differentiator |
| 0 bytes | rejects |
| 1-31 bytes | rejects |
| exactly 32 bytes | accepts and decodes any 256-bit word |
| exactly 33 bytes | rejects |
| more than 33 bytes | captured length reaches 33; rejects |
| 64-byte dynamic-shaped response | rejects |

There is no invalid 32-byte ABI encoding for `uint256`; every word is a valid
number. That means strict length does not prove semantic truth. A malicious
token can return a canonical 32-byte lie, and a one-word value such as `32`
could still be semantically intended as an offset. The helper will accept the
number because exact shape, not token honesty, is its enforceable boundary.

Using an output bound of 32 would be insufficient because oversized data could
be truncated to an apparently valid 32-byte result. The 33rd byte is a
one-byte oversize detector.

### Typed Vyper comparison

The independent probe at Vyper 0.4.3 produced:

```text
canonical 32 bytes: typed=123, strict=123
empty:              typed=revert, strict=revert
1 byte:             typed=revert, strict=revert
31 bytes:           typed=revert, strict=revert
33 bytes:           typed=123, strict=revert
64-byte dynamic:    typed=32,  strict=revert
```

The typed call enforces enough data for a word but accepts trailing data. This
is numerically convenient and smaller, but not equivalent to the approved
canonical-response policy.

There are three balance-read policies in one `_deposit`, not two:

1. before the window, `TellerUtils.validateOnDeposit` uses typed
   `IERC20.balanceOf(holder)` to cap `Q`;
2. Teller uses the strict raw helper for destination-vault `C0` and `C1`; and
3. inside the vault call and while the flag remains true, `BasicVault`,
   `SharesVault`, or `StabVault` uses typed `IERC20.balanceOf(self)` to derive
   its legacy aggregate-balance clamp.

A caller-dependent token can therefore expose trailing data to the typed source
or vault read while returning a canonical word to Teller's strict reads.
Teller's `V == Q` normally makes a shorter vault result fail closed, but the
complete three-policy interaction is not pinned by a test. The strict-return
thesis applies specifically to Teller's custody evidence; it is not a
contract-wide balance-call policy.

### Compatibility conclusion

The raw call does not make `balanceOf` compatible with no-return or malformed
tokens. It makes receipt evidence stricter and more auditable:

- no-return `transfer`/`transferFrom` can be accepted by Vyper's
  `default_return_value=True`, provided custody changes exactly;
- no-return `balanceOf` is rejected;
- false transfer returns and transfer reverts are rejected before credit;
- trailing or dynamic-shaped `balanceOf` returns are rejected; and
- truthful canonical 32-byte balance reporting remains a token-admission
  assumption.

The manual selector, byte buffer, length check, and decode add code and audit
surface, but they reduce return-shape ambiguity relative to the pinned typed
call.

## 6. Token behavior and adversarial matrix

| Token behavior | Deposit result in Teller | Withdrawal/result boundary | Residual or qualification |
| --- | --- | --- | --- |
| Standard ERC-20 | succeeds when destination delta and vault result both equal `Q` | ordinary vault behavior; Guarded additionally proves outflow and delivery | supported |
| Fee deducted from received amount | destination delta `< Q`; entire deposit reverts | Simple/Rebase/RipeGov/Stability may underdeliver while returning nominal; Guarded rejects | exact-transfer policy requires Guarded or explicit exclusion for outbound use |
| Fee charged in addition to `Q`, vault still receives `Q` | can succeed; Teller does not prove the source lost only `Q` | route-specific | depositor-side extra charge is outside the receipt invariant and needs a policy test |
| Reflection/excess receipt | destination delta `> Q`; reverts | Guarded exact recipient/vault deltas reject nonexact delivery | intentionally unsupported during the window |
| Token-side donation or mint during transfer | can make a short causal transfer's net delta equal `Q` without entering Teller | route-specific | mutex cannot establish provenance; truthful net balance can still include unrelated units |
| Transfer-time negative rebase or recipient burn | delta `< Q` or `C1<C0`; checked arithmetic/assertion reverts | Guarded rejects; non-Guarded withdrawal may underdeliver | atomic when rejected |
| Ordinary rebase outside the transfer window | deposit may succeed if the measured net delta remains exactly `Q` | SharesVault accounts by shares; delivery is not made exact by Teller | Teller proves one interval, not future solvency |
| ERC-777-like transfer callback | ordinary nested public action is blocked by Vyper key; trusted nested `_deposit` is blocked by receipt mutex | callback into non-deposit functions is not blocked by this flag | current test callback propagates rejection; caught-callback outer success remains a missing test |
| Callback from destination vault | nested `_deposit` remains blocked until the vault returns `Q` | not applicable | T2 covers the exact phase |
| Callback after clear (PriceDesk/housekeeping) | may start a fresh authorized measurement | not applicable | intentional composability; T5 covers PriceDesk |
| Malicious canonical `balanceOf` lie | can fabricate `C1-C0 == Q` and defeat the guarantee | can also defeat Guarded observations | accepted trust boundary, explicitly demonstrated by T4 |
| Empty/short/33-byte/oversized/dynamic `balanceOf` | strict vault observation rejects | Guarded marks unknown; other typed vault reads follow Vyper typed behavior | fail-closed availability |
| `balanceOf` reverts or consumes gas | deposit fails before credit | Guarded fails/marks unknown; typed paths revert | denial-of-service risk for that asset |
| Transfer returns false | Vyper Boolean assertion reverts | route-specific; Guarded rejects | covered |
| Transfer returns no data | Vyper defaults it to true, then custody delta decides | Guarded explicitly permits empty transfer returndata and measures movement | Teller-specific no-return success/failure cases are missing |
| Proxy token with stable truthful implementation | same as underlying implementation | same as configured vault boundary | pin proxy and implementation identities |
| Proxy upgrades or changes behavior during transfer | post-read observes new behavior; malformed/revert/nonexact results fail, but a canonical lie can pass | route-specific | actual delegatecall/proxy transition not covered by current mock |
| Paused/blocklisted token | transfer or balance observation fails and transaction reverts | Guarded composed tests prove rollback/retry behavior | operational liveness, not accounting success |
| Stability oracle/ERC-4626 read reverts or consumes gas | StabilityPool deposit fails during the vault call while the flag is true | not applicable | static calls cannot reenter but add in-window availability dependencies |

The current `MockStockTokenControls` models pause, sender/recipient/operator
blocklists, transfer revert, false return, and one-unit burn/short receipt. The
inline Teller adversarial token adds zero, fee, reflection, custody decrease,
callback, malformed balance, and canonical-lie modes. Neither is a literal
upgradeable proxy or elastic-supply token.

## 7. Reentrancy, rollback, and atomicity analysis

### Can the flag remain true?

Under production EVM semantics, no completed transaction can leave this
transient Boolean stuck:

- a successful `_deposit` has one path through the explicit clear;
- a revert in `C0`, transfer, `C1`, arithmetic, vault call, or equality check
  rolls back the `TSTORE` in that call frame;
- if an outer contract catches the failed Teller call with
  `revert_on_failure=False`, the failed frame's transient write is still rolled
  back; T3 proves an immediate same-transaction retry succeeds;
- if a callback fails and the outer measurement continues, the outer flag
  remains true as intended until the outer vault result is verified;
- out-of-gas and unusual token reverts roll back rather than bypassing the
  clear; and
- EIP-1153 transient storage is cleared at the end of the transaction in all
  cases.

Titanoboa 0.2.7 does not clear transient state at its simulated top-level
boundary in the same way as a production EVM, which explains the manual clear
in the older recovery test. The later same-transaction rollback probe avoids
that simulator artifact.

This design requires an EVM target that supports EIP-1153. Deploying the
compiled runtime to a pre-Cancun environment would be a compatibility failure,
not a persistent-lock risk.

### Atomicity and ordering

Token movement, both strict observations, vault accounting, Ledger
participation, Lootbox points, debt/housekeeping, both snapshot classes, event,
and return are one EVM transaction. A revert at any later step rolls all prior
state back.

The narrower statement is:

- receipt measurement and the vault's deposit accounting are inside the
  protected phase;
- Ledger/Lootbox/debt/snapshot accounting is atomic with the transaction but
  outside the protected phase; and
- withdrawal accounting is atomic with the Teller transaction but has no
  Teller receipt flag.

Clearing before downstream calls is a deliberate composability boundary. It
avoids blocking the first legitimate trusted deposit triggered by later
protocol work. The cost is that a post-clear callback can interleave a complete
new deposit before the outer deposit emits its event. T5 expects nested event
ordering `[nested, outer]`.

### Reentrancy cross-product

Teller has 33 external functions: 23 use Vyper's `@nonreentrant` key and 10 do
not. When `_deposit` is entered through an ordinary guarded route, the ordinary
key blocks callbacks into those 23 functions. When it is entered through
`depositFromTrusted` or `depositIntoGovVault`, that key is not held. A
transfer-time callback can therefore reach an otherwise guarded Teller
function, including withdrawal, rebalance, redemption, or liquidation paths.

The paths traced in this reassessment fail closed when they affect the measured
asset or reach another deposit: an out-move reduces `C1 - C0`, and any nested
`_deposit` hits `receiptMeasurementActive`. That is not a general reentrancy
proof. A callback can still execute a non-deposit action affecting unrelated
state, and a malicious token can combine callbacks with false or offsetting
balance behavior. The missing cross-product tests should begin with the fully
public same-user `depositIntoGovVault` route and then cover the authorized
`depositFromTrusted` route.

### Why the mutex remains worth keeping

The mutex does not prevent a transfer hook from directly donating or minting a
missing unit into the vault. Its distinct protection is accounting isolation:
protocol-routed nested deposit units cannot be credited to their nested
beneficiary and simultaneously counted inside the outer caller's measured
receipt. T1's no-mutex mutant demonstrates that double-credit shape. Removing
the mutex would therefore reopen a concrete protocol-accounting path even
though the broader causal-provenance limitation would remain.

### What the mutex does not protect

The mutex does not:

- prove the causal source of each unit in a net delta;
- prove a canonical balance word is truthful;
- stop a token from changing its own accounting during `transfer`;
- block callback access to every Teller function;
- make the ordinary Vyper key active on undecorated deposit routes;
- reread custody after the vault, Ledger, Lootbox, or snapshot calls;
- make non-Guarded withdrawals exact; or
- make an untrusted vault truthful merely because it returns `Q`.

Those are admission, vault-trust, downstream-callback, or broader reentrancy
boundaries.

## 8. Alternative comparison

Compiler estimates below are relative and not transaction measurements.
Current versus typed and no-mutex variants were compiled from the frozen source
with only the named in-memory substitution.

| Alternative | Security | ABI and storage compatibility | Gas, bytecode, and code size | Composability and token compatibility | Auditability and migration |
| --- | --- | --- | --- | --- | --- |
| **Current strict helper plus transient Boolean** | exact call-local deposit receipt and vault-result equality, subject to truthful 32-byte balances; blocks overlapping `_deposit` windows | ABI and persistent layout unchanged; transient slots 0/1 frozen | 24,152-byte runtime; 424-byte headroom; estimates 121,948 for `deposit`, 134,370 for `depositFromTrusted`, and 127,606 for `depositIntoGovVault`; mutex costs 16 runtime bytes and 523 estimated `deposit` gas versus the no-mutex mutant | exact-transfer-only; rejects malformed/trailing balances and nonexact net receipt; post-clear trusted callbacks remain live | already integrated, artifact-frozen, mutation-tested; no persistent migration |
| **Typed `IERC20.balanceOf`** | preserves numeric delta for canonical results but accepts trailing/dynamic-shaped data | ABI, persistent, and transient layout unchanged | 24,078-byte runtime, 74 bytes smaller; estimates about 914 gas less per `_deposit` | broader malformed-return tolerance, not meaningful no-return compatibility | simpler syntax but weaker exact-shape evidence; requires Teller redeploy/upgrade and complete artifact requalification |
| **Narrow reusable safe-balance helper** | can preserve exact semantics only if it keeps success and exact-length rules | an internal/module helper can preserve ABI/storage; an external library changes deployment dependencies | inlined module likely similar code; an external helper adds call gas and deployment code; central reuse could reduce duplication only across separately changed contracts | policy must distinguish Teller's hard revert from Guarded's `(known,value)` soft observation | current `_exactBalance` is already narrowly reusable inside Teller; cross-contract centralization adds coordination/migration without a demonstrated defect |
| **Transient dedicated state machine** | current Boolean is already transient; an enum could distinguish acquisition/accounting phases but adds no needed invariant today | no persistent migration; transient layout/name/value expectations change | more comparisons/TSTOREs and likely more bytes/gas in a contract with 424-byte headroom | could improve diagnostics or permit scoped concurrency; extra states create stale-transition review burden | clearer only if future phases require different callback policy; current two-state machine is easier to audit |
| **Persistent lock/checkpoint** | can survive across calls but creates stuck-state and upgrade risks for a transaction-local problem | changes persistent layout and upgrade/migration assumptions | SLOAD/SSTORE cost and more bytecode | unnecessarily blocks/requires recovery across transactions | inferior to EIP-1153 here; requires migration and operational recovery design |
| **Separate Teller deposit and withdrawal measurement** | could make Teller prove user delivery, but duplicates or conflicts with vault-owned share/accounting logic; would need vault outflow and recipient delta, not one balance | likely no public ABI change if internal, but adds transient state/logic and changes behavior of every vault | at least two additional balance reads per withdrawal plus lock/state code; material headroom pressure | improves exact-transfer policy for non-Guarded vaults but intentionally rejects fee/rebase delivery and may break current routes | broad cross-vault migration/testing; Guarded already owns the Stock Token outbound boundary; pursue only after an owner chooses protocol-wide exact withdrawal |
| **Token-adapter normalization** | can intentionally normalize shares, wrappers, fees, or rebases but shifts truth and custody to the adapter | adds interfaces, configuration, addresses, approvals, and possibly storage | extra external calls/deployments; can move code out of Teller but adds system bytecode/gas | best route if the product deliberately supports a nonexact token rather than rejecting it | highest operational and migration burden; each adapter becomes a trusted accounting component |
| **Tighten vault entry authorization and legacy clamps** | Teller-only authorization on RipeGov's lock endpoint would close the direct-call gap; replacing `min` with an equality/assertion prevents silent reduction but still cannot reconstruct call-local `C0` or prove causal receipt | changes RipeGov behavior and vault bytecode but can preserve public ABI/storage; may reject valid-Ripe callers if that breadth is intentional | distributed changes across Basic/Shares/Stab consumers; likely modest per-vault gas/size, no Teller headroom cost | narrower caller composability; aggregate-balance equality alone can still be masked by preexisting custody | defense-in-depth, not a substitute for Teller; requires cross-vault qualification, artifact updates, deployment/migration planning, and an owner decision on valid-Ripe callers |
| **No contract change; stronger docs/tests** | preserves the proven invariant and adds evidence around uncovered boundaries | exact ABI/storage/artifact identity preserved | zero runtime/gas cost and no headroom consumption | no new token support; makes unsupported behavior explicit | **recommended now**; tests/docs need separate authorization but no deployment migration |

A per-asset transient mutex is a further variant. It could allow unrelated
cross-asset nested deposits, but requires additional transient key derivation
and state, complicates same-vault/multi-asset reasoning, and addresses no
demonstrated production liveness problem.

## 9. Existing tests and precise missing tests

### Current focused validation

All reruns used external mode-`0700` Boa, XDG, Python, Hypothesis, and pytest
temporary directories. RPC, provider, private-key, mnemonic, and cloud
credential variables were unset. No fork, signer, or external protocol state
was used.

| Focused selection | Result |
| --- | --- |
| `tests/core/teller/` | 150 passed |
| two call-local masking tests in `test_stock_token_vault_comparison.py` | 4 passed |
| AuctionHouse and Deleverage composed Stock delivery files | 13 passed |
| Guarded unknown-balance/shared-mutex/recipient-delta mutation selection | 12 passed, 62 deselected |
| **Total executed test cases** | **179 passed** |

The exact pytest selections, after the external-cache and credential-unset
preamble described above, were:

```text
pytest -q -p no:cacheprovider tests/core/teller

pytest -q -p no:cacheprovider \
  tests/vaults/test_stock_token_vault_comparison.py::test_short_received_after_existing_user_backing_reverts_atomically \
  tests/vaults/test_stock_token_vault_comparison.py::test_donation_cannot_mask_short_current_receipt

pytest -q -p no:cacheprovider \
  tests/core/auctionHouse/test_auctionhouse_stock_delivery.py \
  tests/core/deleverage/test_deleverage_stock_delivery.py

pytest -q -p no:cacheprovider tests/vaults/test_guarded_erc20.py \
  -k 'post_transfer_unknown_balance or shared_mutex_rejects_authorized_callback or recipient_delta_mutant_accepts_short_delivery'
```

Parameterization accounts for four cases from the two masking node IDs and 13
cases from the 10 composed-route test functions.

Each pytest batch emitted only the three established assert-rewrite warnings
for Boa/Hypothesis imports. The first sandboxed launch failed uniformly at the
session fixture's local ephemeral-port bind before any test body ran; the
identical local-only rerun with loopback permission produced the results above.
That setup denial is not counted as a semantic test result.

Targeted compiler inspection also:

- reproduced the frozen runtime, creation bytecode, hashes, ABI count, and
  persistent/transient layouts;
- passed the repository Teller artifact checker;
- reproduced typed versus strict returndata behavior;
- compiled the typed helper at 24,078 runtime bytes; and
- compiled a no-measurement-mutex mutant at 24,136 runtime bytes. The maintained
  T1 test independently demonstrates why that smaller mutant is unsafe.

### Coverage that is now strong

The current tree has direct or mutation-sensitive evidence for:

- exact, zero, one-unit-short, percentage-fee, excess/reflection, custody
  decrease, false-return, and reverting deposits;
- pre/post reverting, empty, 1-, 31-, 33-, and 64-byte balance observations;
- exact vault return and zero/less/more/revert mismatches;
- ordinary, batch, trusted, rebalance, Teller-held sGREEN, and RipeGov routes;
- prior-user and donation masking;
- a dedicated-mutex deletion mutant;
- token and vault callbacks during the protected interval;
- caught-call same-transaction transient rollback and retry;
- a canonical offsetting balance lie;
- a successful post-clear callback measurement;
- exact outbound Guarded measurement; and
- composed AuctionHouse/Deleverage rollback.

### Precise missing tests

#### Release gates (Priority 1; controlling owner disposition)

1. **Complete vault caller-authorization matrix.** Assert that every
   `depositTokensInVault` entry rejects non-Teller callers. Separately pin that
   `RipeGov.depositTokensWithLockDuration` rejects a non-Ripe caller but
   currently accepts a valid Ripe caller, and demonstrate that this direct route
   does not inherit Teller's receipt proof. Do not encode a Teller-only
   assumption for the lock-duration entry.
2. **Dormant clamp/equality closure.** Across Basic, Shares, and Stab-backed
   routes, force the typed vault clamp to return below `Q` and prove Teller's
   equality assertion rolls token movement and accounting back. Include a
   direct-entry control where authorization permits it, so the test records what
   Teller—not the clamp itself—provides.
3. **Undecorated-route reentrancy cross-product.** Enter the window through
   public same-user `depositIntoGovVault`, callback into representative guarded
   withdrawal, rebalance, redemption, and liquidation actions, and assert
   fail-closed rollback or explicitly bounded unrelated-state behavior. Repeat
   the deposit-reaching cases through authorized `depositFromTrusted`.
4. **Withdrawal responsibility matrix.** Use the same fee, burn, rebase, false,
   no-return, malformed-return, and callback token modes across Teller
   withdrawals from SimpleErc20, RebaseErc20, RipeGov, StabilityPool, and
   GuardedErc20. Assert the correct vault/recipient before/after points and
   explicitly identify which non-Guarded results are unsupported rather than
   implying Teller measures them.
5. **Three-policy balance-return matrix.** Independently vary return shape and
   value for (a) the typed source cap, (b) strict vault `C0/C1`, and (c) the
   typed in-window vault clamp. Include 33- and 64-byte returns, caller-dependent
   behavior, and EOA/no-code asset configuration. Pin which stage rejects and
   prove atomic rollback.
6. **Exact outer receipt after a caught nested rejection.** Have the token
   catch a blocked nested trusted deposit, then deliver exactly `Q` and allow
   the outer deposit to finish. Assert the flag remains active through the outer
   vault call and clears normally afterward.

These six tests are release gates. They are requirements for the combined
test-hardening implementation wave, not implementation authorization in this
report.

#### Pre-release hardening tranche

7. **Real proxy/implementation-change behavior.** Exercise a delegatecall proxy
   whose implementation or return behavior changes during transfer, including
   canonical, malformed, reverting, and canonical-lie post-reads.
   `MockStockTokenControls` is an upgrade-behavior stand-in, not a proxy.
8. **Bounded expensive-`balanceOf` availability.** Add a bounded gas-grief
   probe and record the intentional all-gas-forwarding availability boundary;
   do not add a gas stipend without token/proxy qualification.

These two tests are also required before release, in the pre-release hardening
tranche.

#### Additional evidence backlog

9. **No-return Teller transfer.** Prove an exact no-return `transferFrom`
   succeeds because custody is exact, while a no-return short transfer reverts
   on the delta. False and reverting returns are covered; empty transfer
   returndata is not covered at this Teller boundary.
10. **Elastic-supply phase matrix.** Rebase before `C0`, during transfer, between
   transfer and `C1`, during vault accounting, and after the clear. Distinguish
   a net exact delta from causal transfer receipt and verify share-vault
   accounting/snapshot effects.
11. **Sender-pays-extra fee.** Deliver exactly `Q` while debiting the depositor
   by `Q+fee`; decide and assert whether this is supported or rejected by
   admission policy.
12. **Stability in-window dependency failures.** Revert and gas-grief the
    `PriceDesk.getUsdValue` and ERC-4626 conversion reads during a StabilityPool
    vault call; prove receipt state, custody, and accounting roll back.
13. **Remaining original boundary cases.** Explicitly exercise the valid
   `uint256.max` balance mode, a malformed later `depositMany` row, and two
   successful batch elements with a direct assertion that the mutex releases
   between them.
14. Add full upstream failure-inducibility for trusted producers that current
   tests impersonate, especially a reachable active CreditRedeem deposit if
   product behavior ever enables it.

## 10. Recommended implementation delta, if any

**None now.**

The current production mechanism is the smallest sound implementation for the
approved exact-deposit policy. The higher-value delta is evidence-only:

- add the Priority 1 tests under separate test authorization;
- revise `docs/chains/rh/smart-contract-changes/teller.md` so its test-gap
  section reflects integrated T1-T7 hardening and current line numbers;
- explicitly cross-link Teller inbound measurement to Guarded outbound
  measurement and to the asset-admission checklist; and
- keep artifact, ABI, persistent layout, transient layout, and 24,152-byte
  ceiling checks mandatory for any future Teller edit.

The controlling owner disposition rejects renaming
`receiptMeasurementActive`, adding source comments, or otherwise spending
Teller bytecode headroom merely for readability. Independently, the T1 mutation
helper removes four exact source strings, requires the current identifier to
disappear, and pins `T1_MUTEX_REMOVAL_SHA256`. Any future separately authorized
Teller edit, including whitespace, changes the mutant hash. Its source loader
also uses the cwd-dependent relative path
`Path("contracts/core/Teller.vy")`.

The mandatory future-edit checklist must therefore also:

- update T1's exact removal strings and expected mutant SHA-256;
- resolve Teller source from a repository root rather than the process cwd;
- prove the mutant still compiles and that T1 still kills it; and
- rerun the vault caller/equality and undecorated-route callback matrices.

Do not add a persistent checkpoint, a post-vault `C2`, per-token adapters, or
Teller-wide withdrawal measurement until an owner decision establishes the
new product invariant and migration scope.

## 11. Owner decisions

The reassessment identified the following decision questions:

1. Confirm exact-transfer-only as the admission policy for every asset routed
   through this Teller, not only the current Stock Token.
2. Confirm that strict exact-32-byte custody reads are preferred over the
   smaller typed Vyper behavior that accepts trailing data.
3. Accept or reject canonical-but-false `balanceOf` as a token qualification
   boundary. No balance-delta implementation can solve a lying token alone.
4. Decide whether sender-paid extra fees are supported when the vault still
   receives exactly `Q`.
5. Confirm that exact outbound delivery is Guarded/vault-owned rather than a
   generic Teller withdrawal invariant.
6. Decide whether any non-Guarded vault may admit an issuer-controlled,
   fee-bearing, callback-capable, or upgradeable token.
7. Accept the global cross-asset measurement exclusion or require evidence of
   a real liveness problem before considering a per-asset mutex.
8. Decide whether `depositIntoGovVault` being public for the same user and
   lacking `@nonreentrant` is deliberate. Source and history establish the
   callback need for `depositFromTrusted`, but not for this route.
9. Decide whether `RipeGov.depositTokensWithLockDuration` should remain callable
   by every valid Ripe address or be restricted to Teller. The current
   production callsite is Teller-only; the authorization is not.
10. Decide whether the dormant Basic/Shares/Stab aggregate-balance clamps should
    remain as defense-in-depth compatibility logic, be tightened alongside
    caller authorization, or only be pinned by Teller closure tests.
11. Accept post-clear callback composability and nested-before-outer event
   ordering, or specify a different downstream callback policy.
12. Bind the supported chain/EVM revision to EIP-1153 and pin proxy,
   implementation, admin, pause, blocklist, and upgrade identities for every
   admitted token.
13. Decide whether the Priority 1 tests and stale Teller-document correction
    are release gates or post-release hardening.

The research itself did not resolve those questions. The controlling owner
disposition below now resolves them for this reassessment.

### Controlling owner disposition

Recorded 2026-07-30:

1. Preserve the current Teller production implementation.
2. Preserve the strict `raw_call` balance reader requiring a successful,
   exactly-32-byte return.
3. Preserve `receiptMeasurementActive` as a global deposit-receipt measurement
   mutex. It is not Teller's general reentrancy guard.
4. Preserve Teller's exact destination-custody delta and exact vault-return
   equality requirements.
5. Confirm exact-transfer-only and truthful-balance behavior as the default
   asset-admission policy for Teller-routed assets.
6. Treat canonical-looking but false `balanceOf` results as an asset/token
   qualification failure. Teller is not required to defend against a token that
   deliberately lies about custody.
7. Sender-paid fees are not generally approved. A token with such behavior
   requires explicit qualification even when the vault receives exactly `Q`.
8. Preserve exact outbound delivery as a Guarded/vault responsibility rather
   than adding a generic Teller withdrawal-measurement mechanism.
9. Do not admit issuer-controlled, fee-bearing, callback-capable, rebasing, or
   upgradeable tokens into non-Guarded vaults without explicit asset-specific
   qualification.
10. Preserve the global cross-asset measurement exclusion unless real liveness
    evidence demonstrates that per-asset separation is required.
11. Preserve the current `depositIntoGovVault` behavior provisionally. Its
    public/same-user and undecorated callback behavior must be pinned by the
    Priority 1 regression matrix before release qualification closes.
12. Preserve `RipeGov.depositTokensWithLockDuration` authorization for every
    valid Ripe address for now. Its broader authorization is an explicitly
    supported and tested boundary, not a Teller-only assumption.
13. Any future proposal to restrict that endpoint to Teller is a separate
    RipeGov compatibility, contract, migration, and consumer-review decision.
14. Preserve the Basic/Shares/Stab clamps as defense-in-depth compatibility
    behavior. Do not tighten or remove them in this task.
15. Accept current post-clear callback composability and nested-before-outer
    event ordering, subject to exact regression coverage.
16. Require EIP-1153 support and exact proxy, implementation, admin, pause,
    blocklist, and upgrade bindings for every admitted token.
17. Make all Priority 1 missing tests release gates:

    - complete vault authorization matrix;
    - legacy clamp plus Teller equality/rollback closure;
    - undecorated-route reentrancy cross-product;
    - nonstandard-token withdrawal responsibility for every vault type;
    - three-policy balance-return matrix; and
    - exact outer receipt after a caught nested callback rejection.

18. Include the real proxy/implementation-change model and bounded
    expensive-`balanceOf` availability test in the pre-release hardening
    tranche.
19. Do not rename the mutex, add source comments, refactor Teller, or spend its
    bytecode headroom merely for readability.
20. This disposition does not authorize contract, interface, ABI,
    configuration, migration, deployment, activation, or release changes.

The missing tests will be combined with findings from the other reassessments
into one larger test-hardening implementation wave. This report records the
gates but does not authorize that implementation.

## 12. Residual risk and explicit non-actions

### Residual risk

- A token that returns truthful-looking but false 32-byte balances can fabricate
  an exact delta.
- Net delta does not identify the causal source of the units; offsetting
  rebase, donation, burn, mint, or callback effects can cancel.
- The legacy typed aggregate-balance clamps remain live in Basic, Shares, and
  Stab modules. Current Teller delta/equality checks neutralize silent reduction,
  but direct vault callers do not inherit those checks.
- RipeGov's lock-duration deposit authorization admits any valid Ripe address;
  only its current production callsite graph is Teller-only.
- There is no custody reread after vault accounting or downstream callbacks.
- A trusted vault can return `Q` without truthful internal accounting.
- Reverting or expensive `balanceOf` creates fail-closed asset-level denial of
  service.
- The global mutex rejects unrelated synchronous nested deposits during the
  protected interval.
- The strict helper and transient opcodes require the pinned compiler and an
  EIP-1153-capable target.
- Non-Guarded withdrawals do not inherit Teller's deposit measurement.
- Post-clear callbacks can interleave a fresh deposit before the outer event.
- Undecorated `depositFromTrusted` and `depositIntoGovVault` windows do not hold
  Teller's ordinary key, so callbacks can reach guarded non-deposit functions;
  traced same-asset paths fail closed, but the cross-product is not test-pinned.
- StabilityPool accounting adds static oracle/ERC-4626 availability
  dependencies while the measurement flag is true.
- Teller has only 424 bytes of accepted runtime headroom.
- Proxy/admin behavior can drift after qualification unless deployment and
  monitoring controls bind it.

### Explicit non-actions

This reassessment:

- changed no contract, interface, ABI, configuration, migration, inventory,
  shared document, or test;
- created no adapter, mock, deployment artifact, or manifest;
- did not stage, commit, push, merge, deploy, activate, or release;
- did not use RPC, forks, signers, credentials, or external protocol state;
- did not modify the primary worktree;
- did not authorize a Teller refactor or any later lifecycle phase; and
- leaves this report as the sole unstaged, uncommitted worktree change.
