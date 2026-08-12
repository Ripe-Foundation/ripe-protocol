# Teller: exact deposit receipt

> **11 August 2026 CCIP currentness note:** “owner-parked” CCIP statements below
> preserve the reviewed snapshot's historical scope boundary. GREEN/RIPE CCIP
> topology is now confirmed live; see
> [`../ccip-live-state.md`](../ccip-live-state.md). No further transaction or
> release is implied.

> **Draft explanatory synthesis — not controlling approval evidence.** This
> document explains a reviewed implementation snapshot. It does not authorize
> a source change, deployment, activation, migration, release, or parked work.
> Controlling evidence and owner decisions remain in their designated records.

## Current review candidate

This uncommitted review candidate is based on `rh` commit
`1ac64deb5f65fc39f4362f02ed86a118d7554deb`. It preserves Teller's exact
custody-delta, vault-return, mutex, and rollback requirements while replacing
the two strict raw balance observations with direct typed Vyper `balanceOf`
calls. The dated 28 July snapshot and its validation counts remain historical
evidence below; they do not describe the candidate's source or artifacts.

| Candidate identity | Value |
| --- | --- |
| Teller source Git blob / SHA-256 | `dea818cde0901b02248e3824158e5c422ed02a80` / `f2e01e1cc9cf4cdfca380f329836732fd2d6d0201565828093257a0df8451b9a` |
| Runtime template | 24,082 bytes; SHA-256 `76abbbfc443f0e7ff84d9800df0145858344096d4342e9a9e3941887f2055502`; 494 bytes EIP-170 headroom |
| Creation bytecode | 24,317 bytes; SHA-256 `9ebd4682ea6fd0eaf73f5124bd131d240fa6f9d6f4c91ee5f1a28c05643a12cb` |
| [`test_teller_deposit.py`](../../../../tests/core/teller/test_teller_deposit.py) | Git blob `ccdc62c9e37e9430b14cd43d3d67a6d9ad3e9b29`; SHA-256 `56e914d0e7aef661a5342f339a1ad09ae6365cae301aa2db4ca4cfd37ab148f9`; preserves short/reverting failures and accepts 33-byte trailing returndata |
| [`test_teller_action_block.py`](../../../../tests/core/teller/test_teller_action_block.py) | Git blob `cbc0bbf77dbeeec4d45cd03f16948fd754704ee7`; SHA-256 `1b28378d68836caae0ffd2cf0cfc2bf649ff1592a65a45b0a3e00e8146da5323` |
| [`test_teller_rebalance.py`](../../../../tests/core/teller/test_teller_rebalance.py) | Git blob `e176bfe64c32514fcce45fba930ded42ff16458d`; SHA-256 `959ad5961e525d7fd2711b0e268026c3783e47ddae52be136cbf50388e352261` |
| [Stock comparison test](../../../../tests/vaults/test_stock_token_vault_comparison.py) | Git blob `b8c33f0df312d1ed1e04343337685c4f8c88a377`; SHA-256 `288f8d3fb5cc5de902e4d3918f1ab0c1b7946af243148af34dc6f084e681191c` |

Later integrated tests close the former mutex and rollback gaps: the current
suite uses vault callback mode 5, a mutex-removal mutant, three typed
balance-return policies, undecorated-route reentrancy composition, and a
caught nested rejection that preserves the exact outer receipt. The candidate
also accepts trailing returndata and decodes the first word, matching Vyper's
typed ABI behavior. The remaining trust boundary is any token that reports a
dishonest decoded balance value.

## Reviewed implementation snapshot

| Field | Reviewed value |
| --- | --- |
| Implementation commit | `66eae5ac516466be360fe53a53a4bcd672c1ed23` |
| Implementation parent | `ee07d9b6b4ae85f76646617051ec7d331e30a824` |
| Committed patch SHA-256 | `d9604593f536822cf84a9f46cd555b3863370de8ba8dcdfe82cdc657433509ba` |
| Reviewed `rh` commit | `cca60bb85c772c977bb9fb62c1c6c5252c3a1438` |
| Reviewed `rh` tree | `161fb828f3bbf4cb12596a5dfaf6c9bf1e153381` |
| Review date | 28 July 2026 |
| Production source | [`contracts/core/Teller.vy`](../../../../contracts/core/Teller.vy) |
| Source SHA-256 | `4afc6ce1ccf21cb65e04ce3c56fedcf60bb79cba8e7dc51fd855a1f1f82bd909` |
| Integration status | **Historical integrated fact:** the implementation commit is contained in the reviewed snapshot; the current review candidate intentionally changes its balance-reading policy |
| Deployment/activation status | **Not established here:** source integration does not prove deployment, upgrade, asset enablement, route activation, or release approval |

The commit and tree above are a dated reviewed snapshot, not a permanent claim
about the tip of `rh`. Workstream names such as M1 appear only as provenance.

Status language is deliberate:

- **Integrated fact** means proven in the reviewed repository snapshot.
- **Historical evidence** means a result recorded by an earlier implementation
  or review process and not rerun for this revision.
- **Independently reproduced result** means rerun against the reviewed snapshot
  during the Teller audit.
- **Agent recommendation — not owner-approved** means suggested follow-up, not
  authorization or a release decision.
- **Owner-approved direction** means a controlling scope or status instruction,
  not automatic authorization to implement, deploy, or release.
- **Owner-parked work** is not a current work item or Wave 1 blocker; parking
  does not decide its eventual release disposition.
- **Deployment or release gate** means evidence needed before making a
  readiness claim, not permission to deploy.

The integrated Deleverage source and later composition tests were inspected for
the current package and are documented separately. They are not used to enlarge
Teller's source rationale or authorize Deleverage work. CCIP is owner-parked.
Zero-backing settlement, loss allocation, and bad-debt policy are also
owner-parked; Teller does not resolve them.

## Direct answers to the owner's questions

### Why does `receiptMeasurementActive` exist?

Teller measures vault custody before and after one transfer. A nested deposit
inside that interval could make the outer delta describe two transfers.
[`receiptMeasurementActive`](../../../../contracts/core/Teller.vy#L217) is a
global, transaction-local mutex: the first `_deposit` may measure, while another
`_deposit` is rejected until receipt and vault return are validated.

The ordinary Vyper `@nonreentrant` lock cannot replace it:

- public [`deposit`](../../../../contracts/core/Teller.vy#L229-L240) and
  [`depositMany`](../../../../contracts/core/Teller.vy#L242-L250) use the
  ordinary key, but
  [`depositFromTrusted`](../../../../contracts/core/Teller.vy#L252-L263) and
  [`depositIntoGovVault`](../../../../contracts/core/Teller.vy#L761-L772) do
  not;
- `depositFromTrusted` must remain available as the first legitimate callback
  from an already-running Teller action; and
- adding the ordinary key there would reject both that safe first callback and
  an unsafe second measurement. The dedicated flag distinguishes them.

### Why is it set to `True` and later set to `False`?

In plain English, Teller closes the measurement window while it counts one
deposit, then reopens it for later work in the same transaction:

```text
false -> true -> C0 -> transfer Q -> C1 -> require C1-C0=Q
      -> require vaultResult=Q -> false -> later effects
```

The exact acquire/release is at
[`Teller.vy:289-305`](../../../../contracts/core/Teller.vy#L289-L305). The
explicit clear defines a shorter critical section than the transaction:
`depositMany` can measure its next element and later trusted callbacks can
start with a fresh `C0`. If protected work reverts, EVM frame rollback restores
the transient value that existed before the call; transaction completion also
clears all transient storage.

### Why does Teller now call typed `balanceOf` directly?

Pinned Vyper `0.4.3+commit.bff19ea2` accepts a typed `uint256` result when
returndata is at least 32 bytes, decodes the first word, and tolerates trailing
data. The candidate deliberately adopts that normal typed behavior instead of
maintaining a one-function raw-call wrapper solely to reject oversized output.

This matches `BasicVault` and the protocol's ordinary ERC-20 observation
policy, removes custom decoding code, and reclaims 70 runtime bytes. It does
not change the meaningful receipt invariant: the decoded post-transfer balance
minus the decoded pre-transfer balance must still equal `Q`. A dishonest token
could already return a well-shaped 32-byte lie, so token truthfulness remains
an asset-admission and monitoring assumption rather than a property that
returndata-length enforcement can prove.

## Executive verdict

- **Review candidate:** preserves the exact-transfer-only policy and the
  protection against the stated call-local receipt failure while simplifying
  balance observations to direct typed calls.
- **Source status:** uncommitted and awaiting owner review; this page does not
  claim integration, deployment, activation, or release.
- **Before deployment or activation:** bind and verify the exact artifact,
  compiler, token, vault, configuration, size, and composed route; obtain the
  applicable owner release decision.
- **Recommended hardening:** document the truthful-balance boundary and retain
  artifact/size gates; the former mutex and caught-rejection gaps are closed by
  later integrated tests.
- **Owner-parked:** further Deleverage work, CCIP, and zero-backing
  settlement/loss/bad-debt policy are not current Teller assignments or current
  Wave 1 blockers.

## Behavior before the change and concrete failure

Define:

```text
Q  = validated amount Teller attempts to transfer
C0 = target vault custody immediately before this transfer
C1 = target vault custody immediately after this transfer
R  = C1 - C0, the measured call-local receipt
V  = amount returned by the vault accounting function
N  = aggregate nominal vault accounting before this deposit
S  = pre-existing donation or custody surplus
```

The former Teller flow validated `Q`, trusted transfer success, called the
vault with `Q`, and emitted/returned the vault-selected `V`. BasicVault,
SharesVault, and StabVault derive their deposit amount from aggregate
post-transfer custody:

```text
depositAmount = min(Q, balanceOf(vault))
```

That is not call-local. For example:

```text
Q  = 100 tokens
N  = 0
C0 = 25 tokens donated before this call
R  = 99.999999999999999999 tokens received now (one wei short)
C1 = 124.999999999999999999 tokens
V  = min(Q, C1) = 100
```

The user could receive nominal credit for 100 although this call delivered one
wei less. The general masking construction is:

```text
C0 = N + S
R  = Q - S
C1 = C0 + R = N + Q
```

Vault-only equality and aggregate-solvency checks both pass. A pre-existing
deficit can likewise cancel an excess current receipt. Only `C0` and `C1`
separate this call from prior custody. A transfer Boolean proves only reported
call success; a vault return is program output; and a post-transfer balance
alone cannot attribute custody to the current call.

## Exact source delta and complete execution flow

The historical implementation added the transient declaration at
[`Teller.vy:217`](../../../../contracts/core/Teller.vy#L217), replaces
vault-selected amount assignment with exact receipt and return assertions at
[`Teller.vy:289-305`](../../../../contracts/core/Teller.vy#L289-L305). This
review candidate replaces the helper calls at lines 291 and 297 with direct
typed `IERC20.balanceOf` static calls and removes the helper.
Reconstruct the exact implementation patch with:

```text
git diff \
  ee07d9b6b4ae85f76646617051ec7d331e30a824 \
  66eae5ac516466be360fe53a53a4bcd672c1ed23 \
  -- contracts/core/Teller.vy
```

The resulting `_deposit` flow is:

```text
resolve vault address and ID
read Ledger participation data
Q = TellerUtils.validateOnDeposit(...)
assert receiptMeasurementActive is false
receiptMeasurementActive = true
C0 = typed IERC20(asset).balanceOf(vault)
transfer(vault,Q) if Teller holds funds; otherwise transferFrom(depositor,vault,Q)
C1 = typed IERC20(asset).balanceOf(vault)
assert checked(C1 - C0) == Q
V = ordinary deposit if lockDuration=0; otherwise locked RipeGov deposit
assert V == Q
receiptMeasurementActive = false
Ledger participation -> Lootbox points -> optional housekeeping -> PriceDesk
emit TellerDeposit(amount=Q)
return Q
```

`C1 - C0` is unsigned Vyper arithmetic. If `C1 < C0`, the subtraction itself
reverts before equality evaluation. Both vault branches compare the returned
amount with `Q`; neither may replace the event or return amount. The transfer,
receipt check, and vault-accounting branches are directly visible at
[`Teller.vy:291-303`](../../../../contracts/core/Teller.vy#L291-L303).

For a zero-duration RipeGov request, the vault applies its configured minimum
internally; a nonzero requested lock is clamped between its configured minimum
and maximum. All protected failures revert the upstream operation, including a
complete `depositMany` batch.

## The measurement mutex in detail

### Ordinary versus measurement-specific nonreentrancy

At the reviewed snapshot, 23 of Teller's 33 external entry points use the
ordinary Vyper mutex:

```text
deposit, depositMany, withdraw, withdrawMany, rebalance, borrow, repay,
redeemCollateral, redeemCollateralFromMany, liquidateUser,
liquidateManyUsers, buyFungibleAuction, buyManyFungibleAuctions,
convertToSavingsGreenAndDepositIntoStabPool, claimFromStabilityPool,
claimManyFromStabilityPool, redeemFromStabilityPool,
redeemManyFromStabilityPool, claimLoot, claimLootForManyUsers, adjustLock,
releaseLock, purchaseRipeBond
```

The 10 undecorated externals are:

```text
depositFromTrusted, depositIntoGovVault, deleverageUser,
deleverageManyUsers, deleverageWithSpecificAssets, setUserConfig,
setUserDelegation, setUndyLegoAccess, performHousekeeping,
isUnderscoreWalletOwner
```

Only `depositFromTrusted` and `depositIntoGovVault` directly enter `_deposit`.
The three Teller deleverage wrappers do not. The current integrated Deleverage
source and composition tests were examined for the package-level rebind;
Teller's ordinary trusted-producer boundary remains sufficient for this source
analysis.

A legitimate first callback must remain possible:

```text
Teller @nonreentrant action -> trusted component
    -> depositFromTrusted -> first measurement
```

Reviewed examples include CreditEngine borrower proceeds, Stability Pool
claims/redemptions and RIPE rewards, Lootbox auto-stake, and BondRoom payout.
The ordinary key is already held, but the measurement flag is still false.

### Contamination, vault callbacks, and the release point

Without the dedicated flag, a short outer transfer can be masked by a nested
deposit:

```text
outer request 100; outer receipt 99
nested deposit receives and credits 1
outer observed delta 100 and outer credit 100
total custody +100; total nominal credit +101
```

The flag is global across assets, vaults, and users, so even an unrelated
synchronous nested deposit is rejected. This is an accepted liveness and
composability cost of the smallest design.

The reviewed supported vault endpoints are caller-restricted,
`@nonreentrant`, and do not callback into Teller. Their decorators
prevent reentry into the vault, not an outbound Teller call. Teller therefore
holds the flag through `V == Q` as defense-in-depth. Clearing after `C1` but
before the vault result would reopen a nested deposit too early.

Teller performs no post-vault `C2` reread. The property is exact arrival before
vault accounting, not custody retention through the rest of the function.
After the explicit clear, Teller calls Ledger, Lootbox, housekeeping
dependencies, and PriceDesk at
[`Teller.vy:307-321`](../../../../contracts/core/Teller.vy#L307-L321). A later
callback starts a new measurement with a fresh `C0`; it cannot alter the
already-proven first delta, although it may change later aggregate state.

### Revert, batch, and storage semantics

A revert in either observation, token transfer, subtraction/equality, vault
call, or vault-result equality rolls back that call frame, including the
transient write. A low-level outer caller may catch the failure, but then sees
the value from before the failed Teller call. A failed nested call made while
an outer window is active leaves the outer `True` intact.

`depositMany` acquires and releases once per element. A later failure reverts
the complete transaction, including prior elements, token movements,
accounting, and events.

| Mechanism | Assessment |
| --- | --- |
| Function-local or memory value | Invisible to other Teller call frames |
| Compiler key alone | Rejects the legitimate first trusted callback |
| Persistent Boolean | Changes persistent layout and outlives the needed transaction-local domain |
| Transient Boolean | Shared across Teller frames, revert-journaled, transaction-scoped, and migration-free |

The persistent layout remains `deptBasics.isPaused` at slot 0. Transient slot 0
remains Vyper's nonreentrant key; `receiptMeasurementActive` is added at
transient slot 1. Explicitly writing false shortens the critical section inside
the transaction; automatic end-of-transaction clearing supplies the outer
lifetime bound.

## Typed `balanceOf` behavior

For a typed external call returning one `uint256`, Vyper 0.4.3 computes a
minimum return size and accepts:

```text
assert returndatasize >= 32
```

It decodes the first word, so 32, 33, and 64 bytes are accepted and trailing
bytes are ignored. A dynamic-shaped first word can be interpreted as the
balance. This was independently confirmed from pinned compiler source,
generated behavior, and repository tests.

| Token behavior | Teller result |
| --- | --- |
| Revert | Revert |
| Empty return | Reject |
| 1–31 bytes | Reject |
| Exactly 32 bytes | Decode first word as `uint256` |
| Exactly 33 bytes | Decode first word; ignore trailing byte |
| More than 33 bytes | Decode first word; ignore trailing bytes |
| 64-byte dynamic-shaped data | Decode the first word, including an ABI offset if present |

The compiler emits a static call, preventing state writes, transient writes,
logs, creation, and value transfer throughout the observation call tree. It
does not prevent computation, gas grief, read-only subcalls, deliberate
revert, or a false decoded value.

The accepted truthful-token boundary is therefore:

```text
reported C0 = X
reported C1 = X + Q
actual receipt < Q
```

Teller cannot distinguish this from exact receipt. The integrated adversarial
token's unused constant-maximum mode does not demonstrate the boundary because
its pre/post delta is zero. No checked-in test currently supplies offsetting
canonical lies whose difference is `Q`.

## Routes covered by the change

Every route reaches the same
[`_deposit`](../../../../contracts/core/Teller.vy#L267-L322) measurement:

| Route | How `Q` is derived | Token owner before transfer | Transfer | Later behavior |
| --- | --- | --- | --- | --- |
| `deposit` | Request capped by caller balance and ordinary limits | `msg.sender` | `transferFrom` | Full housekeeping |
| `depositMany` | Independently per element | `msg.sender` | `transferFrom` | Per-element accounting, one final housekeeping |
| `depositFromTrusted` | Request capped by producer balance; trusted producer bypasses ordinary deposit caps | Trusted producer | `transferFrom` | No internal housekeeping |
| `rebalance` | Request capped by caller balance and limits | Rebalance caller | `transferFrom` | Deposit first, withdrawal second, then higher-risk housekeeping |
| Teller-held sGREEN conversion | ERC-4626 result capped by Teller's sGREEN balance and applicable limits | Teller | `transfer` | Full housekeeping |
| `depositIntoGovVault` | Request capped by caller balance and applicable limits | Caller | `transferFrom` | RipeGov route with lock handling |

Both observations always target the resolved destination vault. A failed
Teller-held sGREEN deposit rolls back the preceding GREEN transfer and
ERC-4626 mint. Rebalance deposits before withdrawing; a deposit failure never
reaches withdrawal, while a later withdrawal or health failure rolls the
deposit back.

The integrated source contains eight `depositFromTrusted` call sites:

| Producer path | Asset held by the producer before Teller pulls it |
| --- | --- |
| Stability claim/redemption auto-deposit | Claimed or redeemed asset |
| Stability RIPE reward | Newly minted RIPE |
| Deleverage collateral swap | Replacement collateral received by Deleverage |
| HumanResources | Newly minted RIPE |
| Lootbox auto-stake | Newly minted RIPE |
| BondRoom locked payout | Newly minted RIPE |
| CreditEngine borrower proceeds | sGREEN minted from borrower proceeds |
| CreditRedeem | Syntactic sGREEN path; dormant in the reviewed snapshot because its only caller passes `shouldEnterStabPool=False` |

The producer owns tokens, approves Teller, Teller pulls and measures, and the
producer resets approval after return. Reviewed production callers do not catch
a Teller failure, so upstream minting, approvals, transfers, and accounting
roll back. The M1 parameterized trusted-producer test begins at
[`test_teller_deposit.py:1928`](../../../../tests/core/teller/test_teller_deposit.py#L1928);
the real CreditEngine callback case begins at
[`test_teller_deposit.py:2599`](../../../../tests/core/teller/test_teller_deposit.py#L2599).

## Exact-transfer and vault-result policy

Teller requires `R == Q`; it does not accept and credit a smaller `R`.

| Token behavior | Result |
| --- | --- |
| Standard exact receipt | Supported |
| Empty transfer return but exact receipt | Retains prior support through `default_return_value=True` |
| Transfer returns `False` | Rejected |
| Transfer reverts | Rejected |
| Zero receipt | Rejected |
| Fee deducted from the amount delivered | Rejected |
| Recipient burn or short receipt | Rejected |
| Excess/reflection credited to the vault | Rejected when net `R > Q` |
| Transfer-time rebase changing vault net balance | Rejected unless the final net delta happens to equal `Q` |
| Sender-side fee charged in addition to an exact vault receipt | Can pass if the vault still receives exactly `Q` |
| Canonical but false `balanceOf` reports | Outside the guarantee |

Crediting short `R` would change limits, locks, events, returns, approvals,
batch semantics, and downstream assumptions. Exact-transfer-only preserves the
meaning of success: the validated request was fully credited.

The vault result is independently required to equal `Q`. For supported vaults
and a truthful token:

```text
C1 = C0 + Q
C1 >= Q
depositAmount = min(Q, balanceOf(vault)) = Q
```

SimpleErc20/BasicVault, RebaseErc20/SharesVault,
GuardedErc20/BasicVault, StabilityPool/StabVault, and both RipeGov endpoints
have no legitimate rounding success path. The equality is redundant for their
honest success case but remains a fail-closed interface invariant. It does not
prove that an arbitrary vault really updated accounting: a malicious vault can
return `Q` without crediting it.

## Test evidence and limitations

The implementation commit changed exactly Teller and these three test files:

- [`test_teller_deposit.py`](../../../../tests/core/teller/test_teller_deposit.py);
- [`test_teller_rebalance.py`](../../../../tests/core/teller/test_teller_rebalance.py);
  and
- [`test_stock_token_vault_comparison.py`](../../../../tests/vaults/test_stock_token_vault_comparison.py).

Teller and both Teller test files still match their implementation-commit
hashes at the reviewed snapshot. The comparison file changed later in a
separate region; its exact-receipt tests remain unchanged. Later edits are not
attributed to M1.

### Test-to-invariant matrix

| Test or group | Invariant and assertions | Mutation sensitivity / limitation |
| --- | --- | --- |
| [Nonexact direct receipt](../../../../tests/core/teller/test_teller_deposit.py#L1541) | Zero, short, fee, excess, false-return, and reverting transfers leave custody, Ledger, and events unchanged | Receipt modes are exact-delta sensitive; false/revert were already rejected by the Boolean check |
| [Custody decrease](../../../../tests/core/teller/test_teller_deposit.py#L1571) | Checked unsigned subtraction rejects `C1 < C0` and rolls back | Directly sensitive to subtraction/receipt enforcement |
| [Balance observation policy](../../../../tests/core/teller/test_teller_deposit.py#L1598) | Revert, empty, 1-, and 31-byte responses fail atomically; a dynamic-shaped first-word mismatch fails the receipt delta; 33-byte trailing returndata is accepted before or after transfer | Directly pins Vyper typed first-word decoding without weakening `R == Q` |
| [Vault mismatch](../../../../tests/core/teller/test_teller_deposit.py#L1687) | Vault results `0`, `Q-1`, `Q+1`, or revert roll back exact transfer | Directly sensitive to `V == Q`; false return of exactly `Q` is undetectable |
| [Locked-vault mismatch](../../../../tests/core/teller/test_teller_deposit.py#L1836) | Nonzero-lock endpoint also requires `Q` | Adversarial test vault |
| [Batch rollback](../../../../tests/core/teller/test_teller_deposit.py#L1878) | Bad first or later row reverts the entire batch | Proves transaction atomicity; does not isolate flag release between successful rows |
| [Trusted producers](../../../../tests/core/teller/test_teller_deposit.py#L1928) | Authorized producer addresses succeed exactly and short receipt is atomic | Most cases impersonate the producer rather than execute its full upstream flow |
| [Callback/recovery](../../../../tests/core/teller/test_teller_deposit.py#L1977) | Nested public deposit reverts and a later deposit succeeds | Historical case is not mutex-sensitive; later T1/T3 cases close that gap |
| [Governance vault](../../../../tests/core/teller/test_teller_deposit.py#L2421) | Exact receipt, event, shares, authorization, and min/exact/max locks | Supported RipeGov implementation only |
| [Teller-held sGREEN](../../../../tests/core/teller/test_teller_deposit.py#L2550) | Failure rolls back GREEN transfer, ERC-4626 mint, balances, approvals, and claims | Replaceable adversarial test token |
| [CreditEngine callback](../../../../tests/core/teller/test_teller_deposit.py#L2599) | Real first trusted callback remains live | Success path only |
| [Dormant CreditRedeem route](../../../../tests/core/teller/test_teller_deposit.py#L2651) | Reviewed route refunds rather than deposits | Does not prove an active trusted deposit |
| [Runtime guard](../../../../tests/core/teller/test_teller_deposit.py#L3268) | Enforces EIP-170 and the accepted 24,082-byte ceiling | Does not itself guard ABI or layout |
| [Rebalance rollback, line 1309](../../../../tests/core/teller/test_teller_rebalance.py#L1309) | Short deposit leaves both legs, claims, debt, and events unchanged | Proves deposit-first ordering and whole-operation rollback |
| [Donation masking](../../../../tests/vaults/test_stock_token_vault_comparison.py#L616) | Prior donation cannot substitute for short receipt in Simple or share vault | Directly sensitive to pre/post Teller measurement |

### Current limitations after later integrated hardening

The first three gaps recorded by the 28 July audit are now closed. Current
tests make the callback mutex-sensitive with a removal mutant, exercise vault
callback mode 5 while the flag remains held through vault accounting, and catch
a nested rejection while proving the outer exact receipt remains valid.

Genuine residual limits remain:

- any successfully decoded `balanceOf` first word can still be dishonest;
- producer parameterization does not execute every possible upstream call
  chain;
- short-return tests select representative shapes rather than every byte
  length at every observation site, while oversized data follows typed decoding;
- artifact compatibility is enforced by the central current artifact gate,
  not solely by the Teller unit file.

## Historical versus reviewed-snapshot validation

**Historical evidence — not rerun for this documentation revision:** the
sealed implementation record reported:

- 188 cases across the three M1-owned test files;
- 3,196 selected full-suite cases passing;
- 142 established deselections;
- no skips or xfails; and
- independent ABI, selector, layout, and bytecode checks.

**Independently reproduced result at the reviewed snapshot:** the preceding
read-only Teller audit ran 54 focused reviewed-tree cases covering every M1 test
plus ordinary exact deposit, successful batch, successful Teller-held sGREEN,
`max_value` rebalance, and the two exact-receipt comparison tests. Result:
`54 passed, 134 deselected, 3 warnings in 120.60s`. The process used a
mode-0700 `/private/tmp` workspace and local loopback Anvil; RPC and private-key
variables were unset, and no external protocol state was accessed.

No full suite was rerun for that audit or this editorial revision. Historical
S2 counts such as 60, 69, 76, or 84 are neither substituted for the results
above nor presented as current.

**Current review-candidate validation — focused only:** 12 typed-balance policy
cases passed (`12 passed, 132 deselected in 33.65s`), followed by the runtime
dual guard and machine-readable exact-receipt policy checks (`2 passed in
29.41s`). The standalone Teller artifact checker also returned
`CONTRACT_ARTIFACTS_OK`. No full suite was run.

## ABI, storage, constructor, runtime, gas, and compatibility

### Pinned toolchain

```text
CPython     3.12.0
Vyper       0.4.3+commit.bff19ea2
Titanoboa   0.2.7
pytest      8.4.2
```

### ABI and layout

Reviewed-snapshot and implementation-parent compilation produced:

```text
ABI entries              131
functions                123
unique selectors         123
events                    7
constructors              1
persistent layout         unchanged
new transient state       receiptMeasurementActive at slot 1
```

No external selector, return type, event signature, constructor, or persistent
storage slot changed. No persistent-state migration is required. The new
transient slot exists only for the transaction and does not alter deployed
state initialization.

### Bytecode

The current review candidate independently compiled to:

```text
runtime template bytes    24,082
runtime SHA-256           76abbbfc443f0e7ff84d9800df0145858344096d4342e9a9e3941887f2055502
EIP-170 headroom          494 bytes
creation bytecode bytes   24,317
creation SHA-256          9ebd4682ea6fd0eaf73f5124bd131d240fa6f9d6f4c91ee5f1a28c05643a12cb
```

The direct typed calls reclaim 70 runtime bytes and increase headroom from 424
to 494 bytes. Any later Teller source change requires fresh compilation and
size review.

### Compiler-estimated gas delta

The following pinned compiler estimates are historical M1 evidence and were
not regenerated for this review candidate:

| Route | Parent estimate | M1 estimate | Increase |
| --- | ---: | ---: | ---: |
| `deposit` | 114,383 | 121,948 | 7,565 |
| `depositFromTrusted` | 126,805 | 134,370 | 7,565 |
| `rebalance` | 175,354 | 182,919 | 7,565 |
| Teller-held sGREEN | 135,559 | 143,124 | 7,565 |
| `depositIntoGovVault` | 120,041 | 127,606 | 7,565 |
| `depositMany` maximum bound | 1,330,989 | 1,482,289 | 151,300 |

The compiler attributes about 7,565 additional gas per `_deposit`; the batch
maximum is 20 times that amount. These are static estimates, not empirical
transactions. Actual cost depends on cold/warm access and token behavior.

## Alternatives and tradeoffs

| Alternative | Assessment |
| --- | --- |
| Typed Vyper `balanceOf` | **Selected in this candidate:** smaller, consistent with current vault observations, and accepts trailing returndata under pinned 0.4.3 |
| Trust transfer Boolean | Does not prove the amount received |
| Trust vault result | A vault result is program output, not custody evidence |
| Observe post-transfer custody only | Cannot separate old custody from the current call |
| Check aggregate solvency only | Donations and deficit/excess cancellation can mask current behavior |
| Add ordinary `@nonreentrant` to trusted deposit | Breaks legitimate first callbacks from outer Teller actions |
| No dedicated mutex | Leaves unguarded trusted/governance deposit entries open during measurement |
| Persistent mutex | Changes persistent layout and is unnecessary for a transaction-local invariant |
| Per-asset mutex | Reduces cross-asset exclusion but adds mapping state/code and is not the smallest patch |
| Make the vault pull tokens | Changes approvals, custody routing, and every trusted producer |
| Prepare/finalize vault interface | Adds coordination state, stale-state rules, and a new interface |
| Accept and credit measured `R` | More token-compatible but changes product semantics and downstream assumptions |
| Require `R == Q` | Preserves the meaning of success and fails closed on nonexact receipt |

## Guarantees

The Teller review candidate guarantees, subject to truthful decoded token
balance reports:

- a successful deposit observed typed pre- and post-transfer balances;
- the vault's net custody increase during that window was exactly `Q`;
- a donation or prior user custody cannot mask a short current receipt;
- the selected vault endpoint returned exactly `Q`;
- Teller's event and return retain the validated `Q`;
- every route uses the same exact-transfer-only policy; and
- failure rolls back the complete deposit, upstream operation, or batch unless
  an arbitrary outer caller deliberately catches the failure.

## Non-guarantees and residual risks

| Concern | Classification | Consequence |
| --- | --- | --- |
| False decoded `balanceOf` value | Accepted residual | A malicious token can fabricate an apparent exact delta with or without trailing returndata |
| Offsetting transfer-time rebase/reflection | Accepted residual | Teller proves net delta, not the causal source of each unit |
| Direct custody movement after `C1` | Outside M1 | No post-vault `C2` or post-housekeeping `C3` reread |
| Vault returns `Q` without accounting | Trusted-vault boundary | Teller validates the interface result, not arbitrary vault internals |
| Global cross-asset mutex | Accepted liveness restriction | Unrelated synchronous nested deposits are rejected |
| Expensive or reverting `balanceOf` | Fail-closed availability risk | Deposits for that asset can be gas-griefed or denied |
| Fee, short, recipient-burn, excess, or transfer-time rebase tokens | Intentionally unsupported when net receipt differs from `Q` | Deposits revert |
| Weak mutex regression test | Test defect | Future flag removal could pass the reviewed callback test |
| 494-byte runtime reserve | Maintenance risk | Small future Teller growth can breach EIP-170 |

## Next actions

These classes separate release evidence from optional recommendations and
parked policy. An agent recommendation is not owner approval, implementation
authorization, or a deployment decision.

### Currently required

The direct typed-balance source change is a review candidate. It is not yet
committed, integrated, deployed, activated, or released.

Before anyone claims this Teller implementation is ready for deployment or
activation, the release process must:

- bind the deployed artifact to the reviewed source and pinned Vyper compiler;
- recheck runtime size, ABI/selectors/events/constructor, persistent layout,
  and transient layout;
- qualify each exact token implementation and configuration for truthful
  decoded `balanceOf` values, exact net receipt, transfer return/revert behavior, and
  reasonable gas;
- review each supported vault and composed route for callbacks, custody
  movement during deposit, and truthful accounting; and
- complete deployment/configuration readback, operational monitoring, and the
  applicable owner release decision.

These are deployment or release gates, not authorization to perform them.

### Recommended hardening

The following are **agent recommendations — not owner-approved**:

1. Retain the current mutex-removal, callback-mode-5, return-policy,
   reentrancy-composition, and caught-nested-rejection regressions.
2. Add a canonical offsetting-lie token mode: deliver `Q-1` while reporting an
   apparent delta of `Q`. The expected success must be documented as the
   truthful-balance trust boundary, not supported behavior.
3. Retain focused post-clear liveness coverage, and name or remove opaque fixture
   modes such as constant `balance_mode == 7` and exact-transfer alias
   `transfer_mode == 8`.
4. Retain the 24,576-byte EIP-170 test and stricter 24,082-byte accepted
   ceiling. For every later Teller source change, run one reproducible
   pinned-compiler artifact comparison; prefer an existing central artifact
   gate over duplicate unit-test constants.
5. State exact-transfer-only and truthful-balance assumptions in asset
   admission and monitoring material.

A post-vault `C2` reread is worth reconsidering only if supported vaults become
untrusted, upgradeable without equivalent review, or allowed to move custody
during deposit. A per-asset mutex is worth reconsidering only after a
demonstrated global-mutex liveness problem. Neither production change is
recommended for the reviewed system.

### Parked by owner

- Further Deleverage work is separately owner-gated; the integrated source and
  composition evidence are documented in this package without reopening it.
- All CCIP workflows are outside this process until the owner reopens them.
- Zero-backing settlement, loss allocation, and bad-debt policy remain future
  analysis subjects.

Parking does not decide eventual release disposition. These subjects are not
current Teller work items or current Wave 1 blockers.

### Explicitly not recommended

- removing the dedicated transient mutex or clearing it before `V == Q`;
- replacing transient storage with a persistent mutex/checkpoint;
- removing the vault-result equality check because it is redundant for current
  honest vaults;
- accepting and crediting `R` when `R != Q`;
- moving custody into a vault-pull or prepare/finalize architecture;
- adding `C2` or a per-asset mutex without the triggers above; or
- changing reviewed Teller source solely to undo cosmetic whitespace churn.

These alternatives weaken the stated guarantee, change supported-token
semantics, expand custody/interfaces, or consume scarce bytecode without a
demonstrated requirement.

## Technical verdict

The Teller candidate remains technically justified for an exact-transfer-only
product policy. Direct typed balance observations simplify the implementation
and align it with current vault policy while preserving the call-local receipt
invariant, custody routing, external interfaces, and persistent storage.

No release-readiness conclusion is made for this uncommitted candidate. Its
source, artifacts, targeted behavior, and documentation must be reviewed before
any separate integration decision; that review still does not clear the whole
Stock workflow, deployment, activation, or release.

## Primary sources and reproducible commands

### Repository sources

- [`Teller.vy:217`](../../../../contracts/core/Teller.vy#L217):
  transient declaration.
- [`Teller.vy:267-322`](../../../../contracts/core/Teller.vy#L267-L322):
  complete `_deposit` flow.
- [`Teller.vy:289-297`](../../../../contracts/core/Teller.vy#L289-L297):
  mutex acquisition and direct typed pre/post balance observations.
- [`test_teller_deposit.py:1541`](../../../../tests/core/teller/test_teller_deposit.py#L1541):
  start of M1 adversarial deposit cases.
- [`test_teller_rebalance.py:1309`](../../../../tests/core/teller/test_teller_rebalance.py#L1309):
  rebalance rollback.
- [`test_stock_token_vault_comparison.py:616`](../../../../tests/vaults/test_stock_token_vault_comparison.py#L616):
  donation masking.
- `stock-token-m1-exact-receipt.md`:
  sealed historical evidence.
- `track-8-m1-exact-receipt.md`:
  implementation chronology.
- `stock-token-vault-change-specification.md`:
  owner specification and design constraints.

### Primary external specifications

- [Vyper 0.4.3 external-call decoding](https://github.com/vyperlang/vyper/blob/v0.4.3/vyper/codegen/external_call.py)
- [ERC-20](https://eips.ethereum.org/EIPS/eip-20)
- [EIP-1153: transient storage](https://eips.ethereum.org/EIPS/eip-1153)
- [EIP-214: static-call context](https://eips.ethereum.org/EIPS/eip-214)
- [EIP-170: contract code-size limit](https://eips.ethereum.org/EIPS/eip-170)
- [Solidity ABI specification](https://docs.soliditylang.org/en/latest/abi-spec.html)

### Reproducible commands

Identity and exact implementation patch:

```sh
git rev-parse HEAD HEAD^{tree} rh rh^{tree} origin/rh origin/rh^{tree}
shasum -a 256 contracts/core/Teller.vy
git diff ee07d9b6b4ae85f76646617051ec7d331e30a824 \
  66eae5ac516466be360fe53a53a4bcd672c1ed23 \
  -- contracts/core/Teller.vy
```

Pinned compilation outputs:

```sh
env PYTHONDONTWRITEBYTECODE=1 \
  XDG_CACHE_HOME=/private/tmp/teller-compile-cache vyper --version
env PYTHONDONTWRITEBYTECODE=1 \
  XDG_CACHE_HOME=/private/tmp/teller-compile-cache \
  vyper -f abi,layout,method_identifiers,bytecode,bytecode_runtime \
  contracts/core/Teller.vy
```

The exact recorded shell invocation for the independently reproduced result
was:

```sh
env -u MAINNET_RPC_URL -u RPC_URL -u WEB3_PROVIDER_URI \
  -u PRIVATE_KEY -u ETHERSCAN_TOKEN \
  PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
  ETHERSCAN_API_KEY=local-placeholder \
  XDG_CACHE_HOME=/private/tmp/ripe-m1-audit.RjEZprFy/xdg \
  python /private/tmp/ripe-m1-audit.RjEZprFy/run_focused_tests.py
```

That temporary wrapper passed the following equivalent selection to pytest:

```sh
env -u MAINNET_RPC_URL -u RPC_URL -u WEB3_PROVIDER_URI \
  -u PRIVATE_KEY -u ETHERSCAN_TOKEN \
  PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
  ETHERSCAN_API_KEY=local-placeholder \
  XDG_CACHE_HOME=/private/tmp/teller-audit-cache \
  pytest -q -p no:cacheprovider \
  --basetemp=/private/tmp/teller-audit-pytest \
  tests/core/teller/test_teller_deposit.py \
  tests/core/teller/test_teller_rebalance.py \
  tests/vaults/test_stock_token_vault_comparison.py \
  -k "m1 or test_teller_basic_deposit or test_teller_deposit_many or \
test_teller_get_savings_green_and_enter_stab_pool_basic or \
test_teller_rebalance_using_max_value or \
test_short_received_after_existing_user_backing_reverts_atomically or \
test_donation_cannot_mask_short_current_receipt"
```

Before reproducing, create every named `/private/tmp` directory mode 0700,
replace the historical random path with a fresh private directory, and remove
only the private material created for the run. The commands are provenance,
not a request to rerun them for documentation-only changes.
