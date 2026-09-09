# Generic Deposit-Vault Position Migration — RH Implementation Plan

**Status:** owner decisions CLOSED 2026-08-07; ready to implement in one continuous run
**Primary branch:** `rh` only
**Bound commit:** `610b43f4508e85628a1362532a79d68d71ea902c`
**Bound tree:** `d7f194d1d5cd7597271bc48a20eed5a8d3a405f9`
**Remote verification:** `HEAD == origin/rh == FETCH_HEAD` after `git fetch origin rh`, 2026-08-07
**Toolchain:** `.python-version` = `ripe-lite`; Vyper `0.4.3`; use the pinned repository requirements
**Base back-port:** explicitly out of scope; see Appendix C

This document replaces the earlier plan measured at `0372d48`. That baseline is obsolete.
The late `rh` merges through `610b43f` added the lean/comprehensive pytest lanes. Production
contract bytes remain those integrated through `2c026b0`, but all qualification commands in
this plan use the new lane contract.

---

## 0. Owner decisions — CLOSED, do not reopen

Three design forks were resolved with the owner on 2026-08-07 **before** this plan was finalised,
each backed by a measurement reproduced in §2. They are settled inputs, not open questions. The
former "Phase 0 owner gate" is therefore **removed**: everything it existed to decide has been
decided, and everything it existed to prove has been proven and recorded below.

### D-1 — Headroom: refactor the RipeGov validation into TellerUtils

**Decision: approved.** No authorized caller of `withdrawTokensFromVault` had room for the
migration primitive at the bound commit (Teller 437 bytes free, CreditEngine 184, AuctionHouse
~20). The cause is measurable: `migrateRipeGovPosition` occupies **2,467 bytes** of Teller.

Moving its validation preamble into `TellerUtils.validateRipeGovMigration` — a behaviour-preserving
refactor — frees **753 bytes** of Teller. Boa-verified end state with the migration primitive
added: **Teller deploys at 23,773 bytes, 803 bytes of margin** (§2.4). This replaces the earlier
39-byte and 50-byte proposals, both of which are rejected as unsafely tight.

The refactor must be *pure*: identical asserts, identical order, identical revert reasons. The 46
existing tests in `tests/vaults/test_ripe_gov_controls_and_migration.py` are the proof obligation
and must pass unchanged, without edits.

### D-2 — Security tier: core invariants plus session binding

**Decision: approved.** Build all of: absolute RipeGov exclusion at both endpoints, forced
recipient, exact-caller authorization, zero-residual custody, `assert isDepleted`, mandatory batch
state guards, per-user expected source shares, strictly-increasing user lists, and timelocked
sessions that bind source/target/asset/Teller.

**Not built:** the code-hash vault-class registry, the three-class taxonomy, class epochs and their
approval/disable lifecycle. Its purpose is served at a fraction of the surface by a single
invariant (§3.3):

```
isStabVaultId(sourceVaultId) == isStabVaultId(targetVaultId)
```

That blocks the one economically dangerous pairing — moving a position between a collateral vault
and a non-collateral one, which would silently zero a user's borrowing power. Simple↔Rebase pairing
is *not* dangerous: both are collateral-bearing, and the withdraw/deposit path preserves value
across them. Rationale for rejecting the registry: it was the single largest block of new surface
in an authority contract that can move user funds, and more code there is itself a risk.

### D-3 — Migrator binding: hardcode Switchboard child ID 6

**Decision: approved.** Teller authorizes exactly one address. Replacing VaultMigrator later
requires a Teller redeploy; accepted, because this is a one-off migration tool.

> **Naming hazard — read carefully.** There are two different sixes.
> `Addys.SWITCHBOARD_ID = 6` is the **RipeHq** registry id *of the Switchboard registry contract*.
> VaultMigrator is registered as **child id 6 inside that Switchboard registry** (Alpha=1,
> Bravo=2, Charlie=3, Delta=4, Echo=5, VaultMigrator=6 — verified against `tests/conf_core.py:500`).
> Teller resolves it as `AddressRegistry(a.switchboard).getAddr(VAULT_MIGRATOR_ID)` where
> `VAULT_MIGRATOR_ID = 6` is the **child** id. Do not conflate these; declare the Teller constant
> with a name that cannot be mistaken for `SWITCHBOARD_ID`.

---

## 0.1 Working cadence — binding

Implementation is **one continuous run**. There is no pre-implementation gate and no intermediate
owner report. Build contracts, fixtures, tests, deployment wiring and artifacts in a single pass.
Targeted tests are iteration tools, not owner gates. Do not provide partial hand-backs or ask for
permission between files. The next time you speak to the owner is Phase 5.

Interrupt only when:

- the bound commit/tree does not reproduce;
- the exact design does not deploy under EIP-170;
- the 25-user path does not fit the owner-approved RH gas envelope;
- an invariant in Sections 3–6 cannot be implemented without changing a vault contract;
- a file outside the ceiling in Section 8 is required;
- a new production-contract behavior not authorized here is required; or
- a commit, push, merge, deployment or on-chain transaction is requested. All remain owner-gated.

Do not weaken an assertion, reduce test coverage, rewrite a frozen failure as “pre-existing,” or
change a vault to keep moving. Stop and report the exact evidence.

---

## 1. Scope and non-scope

### 1.1 Authorized goal

Add an RH mechanism for governance to migrate a user's **entire balance in one ERC-20 asset**
from one compatible registered deposit vault to another compatible registered deposit vault,
atomically and without the user's transaction.

The primary use is a future Stability Pool replacement. The implementation may also support
SimpleErc20 and RebaseErc20 vault pairs when the source and target pass the same explicit session
validation.

### 1.2 Hard exclusions

- **Every RipeGov vault is excluded as both source and target.** This is an on-chain invariant,
  not an operator convention. It includes current, previous, replacement and non-core RipeGov
  vault IDs.
- The existing RipeGov-only `Teller.migrateRipeGovPosition` path is not part of this design and
  must remain behaviorally unchanged.
- No NFT migration.
- No percentage or partial migration.
- No cross-asset conversion.
- No vault-contract modification.
- No Base implementation, Base deployment or live-chain execution in this assignment.
- No production migration transaction, Safe bundle, activation, commit or push.

### 1.3 What “position migrated” means

The economic balance in the selected asset moves. Other assets in the source vault do not move.
Ledger participation and source Lootbox points follow the ordinary full-withdrawal lifecycle:

- the source asset balance becomes zero;
- source deposit points are checkpointed to a zero current balance;
- the target participation entry is added if needed;
- the source vault remains enumerable while the user has another source asset or unclaimed
  source rewards; and
- ordinary Lootbox claim/cleanup removes stale zero-balance source metadata later.

Do not delete source Ledger participation during this asset-level migration. Immediate removal
would make multi-asset and unclaimed-reward behavior unsafe. Tests must prove the lazy cleanup.

---

## 2. Current RH facts that must reproduce

### 2.1 Branch and test lanes

Root `pytest.ini` now defines:

- default `python -m pytest`: lean lane; ignores deployment, deployment_profiles, inventory and
  probes, and deselects release/artifact/fuzz/gas/fork-qualification tests;
- comprehensive `python -m pytest -o addopts=''`: restores the excluded directories and markers.

Therefore a green default command is not a full gate. This plan always records both lanes and
runs explicit artifact/deployment slices for final migration qualification;
that plan-specific release work is not an ordinary remediation-PR requirement.

### 2.2 Current deployed runtime facts

`tests/test_vault_pointer_runtime_sizes.py` binds constructor-resolved deployed code, which is
the authoritative EIP-170 measurement. At the bound commit:

| contract | deployed runtime bytes | EIP-170 headroom |
|---|---:|---:|
| MissionControl | 15,998 | 8,578 |
| Teller | 24,139 | 437 |
| CreditEngine | 24,392 | 184 |
| StabilityPool | 24,575 | 1 |

Direct `vyper -p . -f bytecode_runtime` reports runtime templates, not constructor-bound deployed
code. Current templates relevant here are:

| contract | template bytes | template headroom |
|---|---:|---:|
| Teller | 24,043 | 533 |
| TellerUtils | 8,880 | 15,696 |
| SwitchboardEcho | 22,703 | 1,873 |
| StabilityPool | 24,543 | 33 |
| RipeGov | 24,499 | 77 |

Never use a template margin as the deployed margin.

### 2.3 Rejected size candidates — measured, do not retry

All measured on a pristine `git archive` of the bound commit, in a disposable directory.
**Compile in a pristine extract, never in the live worktree** — `rh` carried concurrent
uncommitted edits to `StabilityPool.vy` and `StabVault.vy` on 2026-08-07, and compiling in place
silently measures someone else's in-flight work.

| candidate | Teller template | deployed | verdict |
|---|---:|---:|---|
| Inline function, full validation in Teller | 24,564 | 24,660 | **84 over.** Boa refuses to deploy |
| Split: Teller thin + TellerUtils validator, no refactor | 24,441 | 24,537 | 39 free — rejected as unsafely tight |
| Thin Teller, all policy in VaultMigrator, no refactor | 24,430 | 24,526 | 50 free — rejected |
| …same, minus `@nonreentrant` | 24,414 | 24,510 | 66 free. Buys 16 bytes; never worth dropping the guard |
| Thin Teller, `_a` omitted so the vault self-resolves | 24,486 | 24,582 | **Worse.** Vyper inlines an empty 18-field Addys struct at the call site |

Alternative hosts were also measured and all fail — every contract the vaults authorize is
effectively full:

| host | deployed | free |
|---|---:|---:|
| Teller (unmodified) | 24,139 | 437 |
| CreditEngine | 24,392 | 184 |
| AuctionHouse | ~24,556 (template-derived; not in the Boa size test) | ~20 |

### 2.4 Accepted size result — Boa-verified

With D-1's refactor applied and the migration primitive added:

| contract | template | deployed | margin |
|---|---:|---:|---:|
| Teller | 23,677 | **23,773** | **803** |
| TellerUtils | 10,212 | — | ~14,364 template headroom |

The refactor alone takes Teller from 24,043 → 23,290 template (**−753**). The Teller
template→deployed delta is a stable **+96** bytes (3 immutables); this held exactly for Teller,
CreditEngine and MissionControl, but **not** for StabilityPool (+32) or RipeGov. Use +96 only for
Teller, and only as a projection — the Boa figure is the gate.

`tests/test_vault_pointer_runtime_sizes.py` pins `EXPECTED_DEPLOYED_RUNTIME_BYTES`, currently
`Teller: 24_139`. It **will** fail until updated. Update it only from a real Boa deployment of
final source, never from a template measurement or from this document.

### 2.5 Toolchain facts already proven — no spike required

Both were verified by compiling and deploying a probe under the pinned toolchain, so neither needs
re-proving before implementation:

- **`address.codehash` is supported** by Vyper 0.4.3 here. Note: an account with no code hashes to
  `0x0000…0000`, *not* the EIP-1052 empty-string hash — so a nonzero-codehash test doubles as an
  is-contract test.
- **Numeric address ordering** via `convert(_a, uint256) < convert(_b, uint256)` compiles and
  behaves correctly. Vyper 0.4.3 has no direct address comparison.

Note that under D-2 the code-hash *class registry* is not built; `codehash` remains available and
is still used for the RipeGov implementation-hash exclusion in §4.1.

### 2.4 Existing interfaces to reuse

- `Teller.depositFromTrusted` already performs exact receipt validation, target Ledger add,
  target Lootbox checkpoint, price snapshot and `TellerDeposit` event.
- `Teller.performHousekeeping(True, user, True)` is callable by a valid Ripe address and enforces
  post-action debt health.
- `MissionControl.isStabVaultId` is monotonic and identifies vaults excluded from collateral.
- `MissionControl.setCoreRipeGovVaultId` already sees every new core RipeGov ID; it must also mark
  every such ID and its deployed runtime hash in new monotonic RipeGov exclusion sets.
- All supported deposit vaults allow Teller to call `withdrawTokensFromVault` with an arbitrary
  recipient. The new Teller entrypoint must force that recipient to the exact VaultMigrator.

---

## 3. Settled security architecture

### 3.1 Dedicated VaultMigrator

Use a new `contracts/config/VaultMigrator.vy`, registered as Switchboard registry ID **6**.
Do not add the flow to SwitchboardEcho. Echo has unrelated permanent authority and limited
headroom; a dedicated contract provides session scoping, expiry and an independently removable
capability.

Teller must authorize exactly `Switchboard.getAddr(6)`, not every switchboard.

### 3.2 Timelocked homogeneous sessions

Governance does not pass arbitrary source/target/asset tuples to each batch. It first creates a
timelocked migration session containing exactly:

```python
struct MigrationSession:
    sourceVaultId: uint256
    targetVaultId: uint256
    sourceVault: address
    targetVault: address
    teller: address
    asset: address
    isStabPair: bool
    expiresAtBlock: uint256
    isActive: bool
```

Session confirmation resolves, validates and freezes the IDs, the exact endpoint addresses, the
current Teller, the asset and the shared stability classification. Batch execution must prove
VaultBook and RipeHq still resolve those exact addresses and that the classification still matches.
Each batch supplies only the session ID, a strictly increasing user list, matching source shares and
mandatory source/target state guards. This makes every batch homogeneous and prevents a one-entry
guard from silently covering unrelated targets or a registry rebind.

Per **D-2**, the session carries no code hashes, class ids or epochs.

### 3.3 Pair invariants

At session confirmation and again at batch execution:

- source and target IDs are nonzero, valid and different;
- source and target addresses are nonzero contracts and different;
- the current VaultBook resolutions equal the addresses frozen in the confirmed session;
- the current RipeHq Teller equals the Teller frozen in the confirmed session;
- both support the selected asset in MissionControl;
- neither ID is in `isRipeGovVaultId`;
- neither endpoint's `codehash` is in `isRipeGovVaultCodeHash`;
- **`isStabVaultId(sourceVaultId) == isStabVaultId(targetVaultId)`**, and that shared value equals
  the `isStabPair` frozen in the session;
- the session has not expired; and
- the source and target vaults are unpaused.

The stability-classification equality is the load-bearing economic invariant. Migrating a position
from a collateral-bearing vault into a Stability Pool — or the reverse — would silently change
whether that balance counts as collateral, zeroing a user's borrowing power or conjuring it. The
final mandatory `Teller.performHousekeeping(True, user, True)` would catch the indebted case, but
a debt-free user would be silently harmed; this invariant fails the batch closed instead.

Simple↔Rebase pairing is deliberately permitted: both are collateral-bearing and the
withdraw/deposit path preserves value across them.

### 3.4 Authority and custody invariants

- `Teller.withdrawForMigration` accepts no recipient parameter.
- Teller sends withdrawn tokens only to `msg.sender`.
- TellerUtils proves `msg.sender` is the exact registered VaultMigrator at ID 6.
- VaultMigrator is `@nonreentrant`.
- VaultMigrator records its pre-withdraw token balance, proves the exact withdrawal receipt,
  approves Teller for exactly that amount, deposits exactly that amount, resets allowance to zero,
  and proves its final balance returned to the pre-withdraw balance.
- No successful call may leave migrated funds or a nonzero Teller allowance in VaultMigrator.

### 3.5 Mandatory batch state guard

Define one state guard:

```python
struct VaultStateGuard:
    rawAssetBalance: uint256
    totalShares: uint256
    totalAmount: uint256
```

Each batch requires an expected guard for both source and target. Before the first withdrawal,
require exact matches for ERC-20 `balanceOf(vault)`, vault `totalBalances(asset)` and vault
`getTotalAmountForVault(asset)`. The total-amount guard also detects a Stability Pool
claimable-value change that raw stab-asset balance and shares alone miss. No field has a
sentinel/default that disables checking.

The batch also requires `_expectedSourceShares`, one entry per user. Immediately before each
withdrawal, require the source's public `userBalances(user, asset)` equals the corresponding
nonzero expected value. Shares stay stable when earlier users leave the same share vault, so this
detects stale or mutated manifests without introducing amount-rounding drift. For Stability Pool
sessions, the operator must still prove off-chain that the target is absent from every liquidation
route and has zero claimable basket.

### 3.6 User-list determinism

Require 1–25 users, all nonzero, with the parallel expected-source-shares list at the same length.
Require addresses to be strictly increasing after `convert(address, uint256)`; Vyper 0.4.3 does not
support direct address ordering. This rejects duplicates, makes batch manifests deterministic and
prevents an accidental second withdrawal from reverting an otherwise valid batch.

---

## 4. Contract specification

### 4.1 MissionControl

File: `contracts/data/MissionControl.vy`

Add:

```python
isRipeGovVaultId: public(HashMap[uint256, bool])
isRipeGovVaultCodeHash: public(HashMap[bytes32, bool])
```

Constructor:

```python
self.isRipeGovVaultId[RIPE_GOV_VAULT_ID] = True
```

Add `markRipeGovVaultId(_vaultId)`, callable only by a registered switchboard. It must resolve the
current VaultBook, require the registry and resolved vault are nonzero contracts, and monotonically
mark both the ID and `vaultAddress.codehash`. `setCoreRipeGovVaultId` must always mark the ID before
setting the pointer;
only when the current VaultBook itself exists and the ID resolves to a nonzero contract may it also
mark that code hash. It must not newly require a deployed VaultBook or a registered ID, because
existing shared behavior and tests intentionally permit direct switchboard callers to set arbitrary
nonzero IDs. There is no removal setter. A retired governance vault ID and every discovered
RipeGov implementation hash stay excluded forever.

The constructor can mark initial ID 2 but cannot resolve its not-yet-deployed code. During RH setup,
VaultMigrator must call the new marker after VaultBook/RipeGov exist and before approving ordinary
classes. Tests must prove initial ID 2, its deployed hash, every later core ID/hash, and all previous
IDs/hashes remain true.

### 4.2 TellerUtils

File: `contracts/core/TellerUtils.vy`

**(a) The D-1 refactor — do this first, and prove it before anything else.**

Extract the validation preamble of `Teller.migrateRipeGovPosition` verbatim into a new view:

```python
@view
@external
def validateRipeGovMigration(
    _user: address,
    _asset: address,
    _sourceVaultId: uint256,
    _targetVaultId: uint256,
    _a: addys.Addys = empty(addys.Addys),
) -> (address, address):
```

It performs, in the **same order and with the same revert reasons** as the current Teller code:
nonzero user/asset; nonzero and distinct vault IDs; `isValidRegId` on both; asset supported in both
via MissionControl; resolve both addresses; both nonzero contracts; distinct; both paused. It
returns `(sourceVault, targetVault)`.

`addys._isSwitchboardAddr(msg.sender)` **stays in Teller** — it is a `msg.sender` check and must not
be relocated or passed as a parameter.

Requires two interface additions in TellerUtils: `MissionControl.isSupportedAssetInVault` and
`AddressRegistry.isValidRegId`.

Measured effect: TellerUtils 8,880 → 10,212 template; Teller 24,043 → 23,290 template (**−753**).

**Proof obligation:** `tests/vaults/test_ripe_gov_controls_and_migration.py` (46 tests) must pass
**completely unedited**. That file is deliberately excluded from the writable list in §8. If a test
there needs changing, the refactor was not behaviour-preserving — stop and report.

**(b) The migration validator.** Under D-2 there is no class registry, and the accepted Teller shape
(§4.3) performs the caller check inline. Add a TellerUtils validator for the migration path **only
if** the implementer's own Boa measurement shows it reduces deployed Teller. With 803 bytes of
margin the pressure that motivated it is gone; do not add indirection for its own sake. If it is
added, it must reject zero user/asset/source, require the source registered in VaultBook, and reject
both `isRipeGovVaultId(sourceId)` and `isRipeGovVaultCodeHash(source.codehash)`.

If it is **not** added, those two RipeGov rejections must be enforced in VaultMigrator instead
(§4.4), and the plan's absolute-exclusion tests in §7.3 apply unchanged.

### 4.3 Teller

File: `contracts/core/Teller.vy`

Add a minimal `@nonreentrant` external function. This exact form was compiled and Boa-deployed at
**23,773 bytes, 803 free**:

```python
@nonreentrant
@external
def withdrawForMigration(
    _user: address,
    _asset: address,
    _sourceVault: address,
) -> uint256:
    a: addys.Addys = addys._getAddys()
    assert msg.sender == staticcall AddressRegistry(a.switchboard).getAddr(VAULT_MIGRATOR_ID) # dev: no perms

    amount: uint256 = 0
    isDepleted: bool = False
    amount, isDepleted = extcall Vault(_sourceVault).withdrawTokensFromVault(_user, _asset, max_value(uint256), msg.sender, a)
    assert isDepleted # dev: partial migration
    return amount
```

with `VAULT_MIGRATOR_ID: constant(uint256) = 6` — the **Switchboard child id** (see the naming
hazard in D-3).

Binding properties:

- **No recipient parameter.** Tokens can only ever go to `msg.sender`, which the caller check has
  already pinned to the exact VaultMigrator. There is no target ID, percentage or optional bypass.
- **Always pass `a` explicitly** to the vault call. Omitting it costs 56 bytes, because Vyper
  inlines an empty 18-field Addys struct at the call site (§2.3).
- **Do not check `deptBasics.isPaused`.** This is deliberate and security-relevant: production
  migration runs *while Teller is paused* so ordinary user entrypoints are frozen (§6). State it
  explicitly in a code comment so it is never "fixed" by a later reader. Vault pause checks remain
  inside the unchanged vaults.
- Do not add events, Ledger changes, Lootbox calls, price snapshots or housekeeping here; those
  belong in VaultMigrator or the reused deposit/housekeeping routes.

### 4.4 VaultMigrator

File: `contracts/config/VaultMigrator.vy`

Use LocalGov and TimeLock scaffolding consistent with the other switchboards. Constructor:
`(_ripeHq, _tempGov, _minConfigTimeLock, _maxConfigTimeLock)`.

Per **D-2, the code-hash vault-class registry is not built.** There is no `approvedVaultClass`, no
`vaultClassEpoch`, no class taxonomy and no approve/disable/epoch lifecycle. Pair compatibility is
enforced by the single invariant in §3.3:

```
isStabVaultId(sourceVaultId) == isStabVaultId(targetVaultId)
```

frozen into the session as `isStabPair` at confirmation and re-proven at every batch.

`codehash` is still used, but only for the RipeGov implementation-hash exclusion — an endpoint whose
`codehash` is in `MissionControl.isRipeGovVaultCodeHash` is rejected regardless of its vault ID.
Both `address.codehash` and numeric address ordering are already proven under the pinned toolchain
(§2.5); no compiler spike is required. Remember that an account with no code hashes to `0x00…0`, so
require a nonzero codehash as the is-contract test.

Use `MAX_MIGRATION_SESSION_BLOCKS: constant(uint256) = 50_400` (seven days under RH's approved
five-blocks-per-minute clock). At session start and confirmation require
`block.number < expiresAtBlock <= block.number + MAX_MIGRATION_SESSION_BLOCKS`. A longer operation
uses a newly timelocked session; no session may be made effectively permanent.

Required external functions:

- `getVaultClassForAddress(vault) -> (codeHash, vaultClass, epoch)` (view)
- `markRipeGovVaultExclusion(vaultId, expectedVault) -> bool`
- `startVaultClassApproval(vaultId, expectedVault, vaultClass) -> actionId`
- `confirmVaultClassApproval(actionId) -> bool`
- `cancelVaultClassApproval(actionId) -> bool`
- `disableVaultClass(codeHash) -> bool`
- `startMigrationSession(sourceVaultId, targetVaultId, asset, expiresAtBlock) -> actionId`
- `confirmMigrationSession(actionId) -> sessionId`
- `cancelMigrationSession(actionId) -> bool`
- `closeMigrationSession(sessionId) -> bool`
- `migrateVaultPositions(sessionId, users, expectedSourceShares, expectedSourceState,
  expectedTargetState) -> uint256`

Set `MAX_MIGRATION_USERS = 25`; the two parallel lists are
`DynArray[address, MAX_MIGRATION_USERS]` and `DynArray[uint256, MAX_MIGRATION_USERS]`, and the two
state arguments use `VaultStateGuard`. Define a narrow local vault-data interface in VaultMigrator
for `userBalances` and `totalBalances`; reuse the existing Vault interface for
`getTotalAmountForVault` and pause checks. Do not expand `interfaces/Vault.vyi` or any other file
outside Section 8 merely to expose public getters already present in every eligible vault.

Every state-changing function requires governance, including confirmation and batch execution.
Confirmation requires the normal timelock and repeats all pair validation against current state.
Closing is immediate governance risk-reduction and may only change active to false. Closed or
expired sessions never reactivate. Session IDs start at 1, increase monotonically and are never
reused; successful batch execution returns exactly the number of migrated users.

Class-approval start and confirmation must resolve `vaultId` through the current VaultBook, require
it equals `expectedVault`, require a nonzero contract and derive the code hash on-chain. They must
reject a marked RipeGov ID or code hash and require the ID's Stability bit exactly matches the requested class.
The pending payload and events bind vault ID, address, derived hash and requested class; a registry
rebind or code-hash change before confirmation fails.

`markRipeGovVaultExclusion` is immediate, governance-only and one-way. It binds the expected
VaultBook address, calls `MissionControl.markRipeGovVaultId`, and verifies both monotonic mappings.
It can only remove migration eligibility; it cannot set the core pointer or classify a vault.

Tag each pending action by type. Reject a mismatched confirm/cancel function, and delete the
timelock record, type tag and typed pending payload on confirmation, cancellation or expiry. Reject
zero/invalid classes, zero hashes, already-classified hash approvals and already-unapproved hash
disables.

Session confirmation stores both code hashes, their epochs and the shared class. Batch execution
requires all five values to remain exact. Disabling a hash therefore permanently invalidates every
affected active session; later reapproval increments the epoch and cannot resurrect it. Governance
must confirm a new timelocked session.

Emit pending/executed/cancelled events for code-hash actions and sessions; immediate events for a
RipeGov exclusion, hash disable and session close; and the per-user migration event. Pending events
include action ID and confirmation block; session events include IDs, bound addresses, Teller,
asset and expiry.

`migrateVaultPositions` is also `@nonreentrant`. Before entering the loop:

- prove the current Teller is the session-bound Teller and is paused;
- re-run every pair, address, code-hash, classification and expiry invariant;
- validate user/share-list lengths and numeric address ordering; and
- validate the complete source and target state guards.

The exact migration withdrawal route remains callable while Teller is paused; an unpaused Teller
means ordinary user state is not frozen, so the whole batch must revert. For each user:

1. Require source `userBalances(user, asset)` equals the matching nonzero expected source shares.
2. Save `migratorBalanceBefore`.
3. Call Teller `withdrawForMigration`.
4. Require the migrator balance increased by exactly the returned amount.
5. Require amount nonzero.
6. Approve Teller exactly; assert ERC-20 boolean with `default_return_value=True`.
7. Call `depositFromTrusted(user, targetVaultId, asset, amount, 0)`.
8. Reset Teller allowance to zero and assert success.
9. Require deposited amount equals withdrawn amount.
10. Require migrator balance equals `migratorBalanceBefore`.
11. Checkpoint source Lootbox points. Target points were checkpointed by `_deposit`.
12. Call `Teller.performHousekeeping(True, user, True)`.
13. Emit the migration event.

Event fields: session ID, user, asset, source ID/address, target ID/address, amount and caller.

Do not include fund recovery for session assets. Unrelated accidental-token recovery, if desired,
is a separate owner decision; it must never weaken the zero-residual invariant.

### 4.5 RH deployment and artifact wiring

- In `0002_Switchboards.py`, leave IDs 1–5 unchanged, deploy VaultMigrator separately after Echo,
  register it as child ID 6 and assert the ID/readback. Do not rename it to
  `SwitchboardVaultMigrator` or shift an existing registry ID.
- In `0007_FinishSetup.py`, before setting nonzero action timelocks, first mark and verify the
  registered RipeGov ID/hash exclusion through VaultMigrator. Then bootstrap classes through the
  actual registered SimpleErc20 and StabilityPool IDs/addresses, read back their on-chain-derived
  hashes/classes/epochs, and assert the RipeGov address remains class zero. Finally include
  VaultMigrator in `ACTION_TIMELOCK_COMPONENTS` and verify its final timelock.
- Add the exact component, switchboard-registry row, timelock facts, contract source and ABI to both
  RH blueprint representations. Preserve every existing component/registry identifier.
- Regenerate Teller, TellerUtils, MissionControl and VaultMigrator ABIs from final source. Extend
  `contract-artifact-expectations.json` and its exact required set to bind TellerUtils and
  VaultMigrator as well as every already-bound changed contract.
- Deployment tests must prove fresh-deployment order, child ID 6, bootstrap hash values, RipeGov
  exclusion, final nonzero timelock, constructor arguments, ABI/source parity and rerun behavior.

---

## 5. Stability Pool requirements

### 5.1 Source claimable basket

`assert isDepleted` reverts a migration when a source Stability Pool cannot fully pay the user in
the stab asset. This is a final failsafe, not the operator's primary preflight.

Before the first production batch, record for every stab asset:

- total shares;
- raw stab-asset balance and USD value;
- every claimable asset, balance and USD value;
- exact claimable total, not “approximately zero”; and
- the maximum full-exit amount under the current prices.

The batch manifest is not executable until claimable value is exactly zero or a separately
reviewed rounding bound proves every listed user can fully exit in the chosen order.

### 5.2 Clearing claimables

- sGREEN bucket: governance may use the existing redemption path that converts GREEN payment to
  sGREEN and drains claimables while replenishing stab asset.
- LP bucket: do not assume redemption drains value. The prior design indicates governance may
  need to deposit working capital at least equal to claimable value, migrate other users, claim as
  the final shareholder, and migrate its residual. Reproduce this on a bound fork with exact
  rounding margin before production use.

No implementation code in this assignment automates claim clearing.

### 5.3 Target isolation

Before and throughout migration, the target Stability Pool must not appear in `priorityStabVaults`
or any `specialStabPoolId`. Otherwise a liquidation can create target claimables between batches.
The total-amount guard makes that batch fail closed, but route isolation prevents repeated liveness
failures and keeps the target economically clean.

### 5.4 Dust and zero-output positions

VaultMigrator requires both nonzero source shares and a nonzero withdrawal receipt. If a Stability
Pool row has nonzero shares but rounds to zero withdrawable amount, it must revert and remain out of
the completed manifest. The current RH StabilityPool recovery functions raise, and no vault change
is authorized here. The production runbook must enumerate these rows and route any residual through
a separate, owner-approved economic/remediation decision; never erase shares, Ledger data or
Lootbox entitlement merely to report completion.

---

## 6. Operational freeze and cutover model

This is documentation and test scope only; do not execute it in this assignment.

1. Deploy and qualify the target vault while it is absent from automated deposit/liquidation
   routes.
2. Register target in VaultBook and add it to the asset's supported vault IDs.
3. For Stability Pool sessions, remove the source from priority/special liquidation routes.
4. For Stability Pool sessions, flip `preferredStabVaultId` to the target before user migration so
   trusted automatic deposits stop selecting the source. For every vault class, verify every
   trusted producer's explicit/default route no longer selects the source.
5. If the target's deployed hash is not already assigned to the correct class, complete its
   separate timelocked class approval and verify the resulting epoch before starting the session.
6. Pause **Teller**, not either vault. Ordinary user deposit/withdraw entrypoints stop; the exact
   migration functions remain usable. Verify all other trusted producers now select the target.
7. For Stability Pool sessions, clear and re-prove the source claimable basket.
8. Confirm the timelocked migration session.
9. Execute deterministic guarded batches.
10. Reconcile all source users/assets, target receipts, events, Ledger participation, Lootbox
   checkpoints and debt health.
11. Close the session immediately after reconciliation.
12. Remove the source from the asset's supported vault IDs, then pause and retire the source vault
    only after its economic positions are empty.
13. Unpause Teller only after pointers and supported-vault ordering are independently verified.

Do not set `canDepositAsset = False` during migration; `depositFromTrusted` also requires that flag
and would revert. `canWithdrawAsset` is not a substitute for the Teller pause because migration
intentionally bypasses ordinary withdrawal configuration.

Successful batches are not idempotent: replaying one encounters empty source positions and
reverts. Only a reverted transaction can be retried unchanged. Track completion by transaction
receipt and event reconciliation, not by resubmitting an entire manifest.

Do not call `Lootbox.resetAssetPoints` until every user's source entitlement has been claimed or a
separately approved forfeiture policy exists.

---

## 7. Required tests

### 7.1 Fixtures

Add and register:

- `vault_migrator` as Switchboard ID 6;
- `stability_pool_two`;
- `simple_erc20_vault_two`; and
- `rebase_erc20_vault_two`.

Use deterministic test VaultBook IDs 5, 6 and 7 for the three targets. Update exact fixture-count
assertions deliberately:

- Switchboard count: 5 to 6;
- VaultBook count: 4 to 7.

Finish the VaultMigrator action timelock in the same fixture phase as other switchboards.
Before that finish step, mark the fixture RipeGov ID/hash exclusion, then bootstrap the deployed
SimpleErc20 and StabilityPool hashes with their exact classes. Leave RipeGov and RebaseErc20 at
class zero until each test explicitly exercises approval.

### 7.2 Contract and permission coverage

- Only exact registered VaultMigrator can call Teller migration withdrawal.
- Alpha, Bravo, Charlie, Delta, Echo, Teller, vaults and EOAs all fail.
- Caller cannot choose an external recipient.
- Non-governance cannot start, cancel, close or execute sessions.
- Non-governance cannot approve/disable hashes or confirm any pending action.
- Confirmation before timelock fails.
- Mismatched action-type confirmation/cancellation fails and cannot consume the other action.
- Closed and expired sessions fail permanently.
- Zero/nonexistent session IDs fail and confirmed session IDs are monotonic/non-reused.
- Zero, past and more-than-50,400-block session expiries fail.
- Invalid/zero/same source and target fail.
- Unregistered/EOA targets fail.
- A VaultBook endpoint rebind or RipeHq Teller rebind after confirmation fails.
- Unsupported assets fail.
- Class approval binds a registered ID/address/hash; a rebind before approval confirmation fails.
- A marked RipeGov ID/hash class approval and a class/`isStabVaultId` mismatch fail.
- Unclassified endpoint code hashes fail; timelocked classification enables only the intended hash
  and immediate disable stops an already-active session.
- Zero/unknown classes, zero hashes, already-classified approvals, direct nonzero reclassification
  and already-unapproved disables fail.
- Disable followed by timelocked reapproval increments the epoch and cannot revive an old session.
- Empty, duplicate, unsorted and over-25 user lists fail.
- User/source-share length mismatch, a zero expected share and a stale user share fail.

### 7.3 Absolute RipeGov exclusion

- Current core RipeGov fails as source and target.
- Initial ID 2 and its deployed hash are both monotonically marked during setup.
- Deploy a second RipeGov, set it as core, and prove both old and new IDs stay marked.
- Both old and new RipeGov IDs/hashes remain marked and fail as source and target.
- Existing direct-switchboard behavior for arbitrary nonzero core IDs remains accepted and marks
  the ID; an unresolved address simply contributes no code hash.
- A same-bytecode RipeGov whose ID was never marked still fails because its hash is monotonically
  excluded and remains class zero.
- A valid RipeGov balance that would otherwise withdraw must still fail at the explicit type gate.
- Existing `migrateRipeGovPosition` success and failure behavior remains unchanged.

### 7.4 Value and atomicity

- Simple to Simple preserves exact amount.
- Rebase to Rebase preserves value within an explicit integer bound after donation/rebase.
- Stability Pool to Stability Pool with zero claimables preserves value within an explicit bound.
- Nonzero source claimables causing a partial exit revert on `isDepleted`.
- Nonzero Stability shares that round to a zero receipt fail without changing shares or metadata.
- Clearing the same basket makes the same migration succeed.
- A target deposit failure rolls the source withdrawal back completely.
- A later failing user rolls the entire batch back.
- Fee-on-transfer and false-return approval mocks revert without residual custody or allowance.
- Pre-funded migrator balance is preserved exactly and cannot subsidize an inexact receipt.

### 7.5 State guards and classification

- Wrong source or target raw balance, total shares or total amount fails.
- Direct donation, ordinary deposit and withdrawal between snapshot and batch all fail the guard.
- A target Stability Pool claimable-basket change fails the total-amount guard even when target
  stab-asset balance and shares are unchanged.
- Omitted guards are impossible at the ABI level.
- Simple↔Rebase and every ordinary↔Stability session fail by class, even if a Stability ID was not
  yet marked. Different approved runtime hashes in the same class may pair.
- A Stability-class hash with an unmarked ID, or an ordinary-class hash with a marked ID, fails.
- Source or target vault pause fails.
- Teller must be paused for batch execution; unpaused Teller fails at VaultMigrator.

### 7.6 Ledger, Lootbox and debt

- Target participation is added once.
- Existing target participation is not duplicated.
- Source deposit points checkpoint to zero current balance.
- A single-asset source remains claimable through Lootbox and ordinary cleanup eventually removes
  stale source participation.
- A multi-asset source stays participating and its untouched asset/rewards remain unchanged.
- A user at the configured vault limit migrates, then reconciles to the correct count after source
  reward cleanup.
- Indebted non-stability users retain good debt health.
- A deliberately unhealthy post-state reverts the whole migration.
- Stability positions remain excluded from collateral before and after.

### 7.7 Events, gas and size

- One event per migrated user with exact session, pair, amount and caller fields.
- Pending, confirmation, cancellation, disable and close events contain the exact action/session
  bindings and no stale pending payload survives completion. Hash/class events include the old and
  new class plus resulting epoch; session events include both hashes and epochs.
- No event survives a reverted batch.
- Measure `boa.env.get_gas_used()` for 1, 5, 10 and 25-user batches for each vault class.
- Extend the deployed runtime test for every touched/deployed contract, including VaultMigrator.
- Update exact expected deployed bytes only from deployed Boa code.
- Recompile Teller/TellerUtils through both direct Vyper and Boa deployment paths.
- Add TellerUtils and VaultMigrator to the frozen artifact expectation set; do not leave a changed
  production ABI or a new production contract outside `REQUIRED_CONTRACTS`.

---

## 8. Exact implementation file ceiling

Core implementation may touch only:

- `contracts/core/Teller.vy`
- `contracts/core/TellerUtils.vy`
- `contracts/data/MissionControl.vy`
- `contracts/config/VaultMigrator.vy` (new)

Test implementation may touch only:

- `tests/conf_core.py`
- `tests/vaults/test_vault_migration.py` (new)
- `tests/data/test_mission_control.py`
- `tests/registries/test_ripe_hq.py`
- `tests/test_vault_pointer_runtime_sizes.py`

RH deployment/artifact integration may touch only:

- `migrations/robinhood-mainnet/0002_Switchboards.py`
- `migrations/robinhood-mainnet/0007_FinishSetup.py`
- `config/BluePrint.py`
- `config/robinhood_blueprint.py`
- `config/contract-artifact-expectations.json`
- `scripts/abis/Teller.json`
- `scripts/abis/TellerUtils.json`
- `scripts/abis/MissionControl.json`
- `scripts/abis/VaultMigrator.json` (new)
- `tests/inventory/test_contract_artifacts.py`
- `tests/deployment/test_robinhood_blueprint.py`
- `tests/deployment/test_robinhood_production_remediation.py`

Documentation may add only:

- `docs/chains/rh/vault-migration/production-runbook.md` (new)

This plan file may be updated only to record final re-derived facts. If another file is required,
stop before editing it and explain the exact dependency.

No vault file is authorized.

---

## 9. Execution phases

### Phase 0 — identity, disposable size spike and owner gate

From an isolated `codex/...` worktree created at the bound commit:

1. Require clean status before adding this plan; do not implement on mutable `rh`.
2. Recompute commit, tree, plan SHA-256, Python, Vyper, Boa and pytest identities.
3. Reproduce current deployed runtime facts.
4. In a disposable directory, compile and Boa-deploy the exact proposed Teller/TellerUtils split,
   MissionControl ID/hash mappings and VaultMigrator interface.
5. Prove Vyper 0.4.3 accepts `address.codehash` and numeric address ordering; compute the
   constructor-resolved SimpleErc20, StabilityPool, RebaseErc20 and RipeGov hashes under the bound
   RipeHq, prove intended same-type instances match, and prove RipeGov is disjoint.
6. Execute representative 1- and 25-user batches for all three classes against the disposable
   contracts; report gas and compare it with an explicitly sourced RH transaction/block envelope.
7. Report exact deployed sizes, hash evidence, gas evidence and the complete production-contract/
   file ceiling.
8. Obtain explicit owner approval for the four production-contract changes and RH deployment/
   artifact integration.

No repository source edit occurs before step 8.

### Phase 1 — pre-change baselines

Use private mode-0700 caches and basetemps outside the worktree, unset RPC/private-key/cloud
credentials, set `ETHERSCAN_API_KEY=local-placeholder`, and retain commands plus outputs.

Run and record:

1. Lean lane: `python -m pytest`.
2. Comprehensive lane: `python -m pytest -o addopts=''`.
3. Explicit artifact slice with comprehensive addopts.
4. Explicit deployment/blueprint slice with comprehensive addopts.
5. Current deployed-runtime test.

Record collection, pass/fail/error/skip/xfail/deselection counts and exact failing node IDs. The
late test-speed integration documents known red lanes; never call a post-change failure
“pre-existing” without matching baseline node evidence.

### Phase 2 — one continuous build

After owner approval, implement all files in Section 8 without intermediate owner reports:

1. MissionControl monotonic RipeGov-ID set.
2. TellerUtils validation.
3. Minimal Teller withdrawal.
4. VaultMigrator sessions and batches.
5. Fixtures and complete tests.
6. RH deployment topology and timelock integration.
7. ABI/artifact/blueprint updates from final source bytes.
8. Documentation fact refresh in this plan.

Use targeted tests freely while iterating. Do not run the comprehensive lane repeatedly.

### Phase 3 — targeted qualification

Run, with the comprehensive addopts where markers/directories require it:

- new migration and MissionControl tests;
- Teller/TellerUtils deposit, withdrawal, rebalance and housekeeping tests;
- Ledger and Lootbox deposit-point tests affected by migration metadata;
- Stability Pool withdrawal/claim suites;
- runtime-size test;
- registry, artifact and deployment topology tests; and
- gas-marked migration tests.

Every new or behaviorally touched test must be green. A baseline exception is allowed only for an
unrelated node ID with the same failure evidence in Phase 1; never waive a new/touched failure.

### Phase 4 — final lanes

Run the lean and comprehensive commands once each against final bytes using fresh isolated
basetemps. Compare every result with Phase 1. Also run explicit artifact and deployment slices so
their status is visible even if comprehensive collection aborts elsewhere.

### Phase 5 — independent review

A fresh reviewer must re-derive, not copy:

- bound commit/tree and complete diff;
- every deployed runtime size;
- exact VaultMigrator-only Teller authority;
- forced recipient and zero-residual custody;
- exact source/target/Teller address binding across registry changes;
- positive endpoint-code-hash classification, epoch binding and immediate disable behavior;
- old/current/future RipeGov ID/hash exclusion at both endpoints;
- session timelock, expiry, close and homogeneous guard;
- mandatory source/target state guards and per-user source-share binding;
- equal stability classification and final debt-health check;
- lazy source Ledger/Lootbox behavior;
- absence of vault changes;
- RH deployment/ABI/artifact parity; and
- lean/comprehensive baseline comparison.

No finding is resolved by weakening a test or changing a recorded expectation without regenerating
and reviewing the underlying source/artifact evidence.

### Phase 6 — single owner presentation

Present together:

1. Baseline and final lean/comprehensive results.
2. Targeted test and gas results.
3. Exact deployed sizes and margins.
4. Complete diff and file list.
5. Artifact/ABI/blueprint hashes.
6. Independent-review findings and resolutions.
7. Every judgment call not explicitly specified here.
8. Explicit non-actions: no Base work, no deployment, no activation, no commit and no push.

Commit and push remain owner-gated.

---

## 10. Production runbook deliverable

Implementation must not execute transactions. It must add
`docs/chains/rh/vault-migration/production-runbook.md`, giving a future operator:

- chain ID, snapshot block/hash and code-hash binding;
- source/target/session/config tuple;
- exact endpoint runtime-hash classes/epochs and evidence that RipeGov's hash is monotonically
  excluded and remains class zero;
- deterministic holder discovery from logs plus live-balance reconciliation;
- asset and claimable-basket census plus source/target `VaultStateGuard` snapshots;
- sorted users with parallel expected source shares;
- sorted batch manifests and manifest hashes;
- preflight `eth_call`/fork simulation and gas limit;
- Safe nonce/receipt/event reconciliation;
- canary batch before mass execution;
- late-deposit and residual sweep;
- source reward-claim/cleanup tracking;
- session close, source retirement and Teller unpause checks;
- reverse-migration/emergency procedure; and
- explicit treatment of RH StabilityPool dust, whose recovery functions raise.

No public copy may call a migration complete until every manifest row, balance, event, Ledger row,
Lootbox entitlement, pointer and retired-source residual has been reconciled.

---

## Appendix A — exact size commands

Template only:

```bash
out=$(vyper -p . -f bytecode_runtime contracts/core/Teller.vy)
n=$(( (${#out} - 2) / 2 ))
printf 'template=%s template_margin=%s\n' "$n" "$((24576-n))"
```

Authoritative deployed size: deploy the fixture through Boa and use
`len(contract.env.get_code(contract.address))`, as in
`tests/test_vault_pointer_runtime_sizes.py`.

Never pass a global optimizer flag. Honor in-file pragmas.

## Appendix B — minimum production invariants

```text
source != target
asset != 0
user != 0
source and target registered contracts
source and target addresses equal session bindings
current Teller equals session binding
source and target support asset
not isRipeGovVaultId[source]
not isRipeGovVaultId[target]
not isRipeGovVaultCodeHash[source.codehash]
not isRipeGovVaultCodeHash[target.codehash]
source and target code hashes have the same nonzero approved class
source and target class epochs equal the frozen session epochs
isStabVaultId for both endpoints exactly matches whether class is StabilityPool
Teller paused
source and target vaults unpaused
session active, unexpired and within the maximum duration
source and target raw balance, total shares and total amount match mandatory expectations
each source user share matches its mandatory nonzero expectation
withdrawal fully depletes the selected source asset
withdraw receipt == deposit receipt
VaultMigrator residual and Teller allowance unchanged/zero
source Lootbox checkpointed
target Lootbox checkpointed
post-migration debt health valid
```

## Appendix C — Base follow-up, not authorized here

A Base migration requires a separately rebound plan covering:

- Base Teller/TellerUtils/MissionControl/VaultMigrator deployed sizes;
- RipeHq activation of the replacement Teller;
- dynamic `preferredStabVaultId` reads in Teller, CreditEngine and CreditRedeem;
- monotonic Stability Pool and RipeGov vault-ID sets;
- SwitchboardCharlie validators and timelocks;
- the SwitchboardBravo hardcoded staker-ID validator;
- preventing new deposits to retired vault ID 1;
- Base artifact/ABI/deployment history; and
- live Base block/code/config qualification.

Do not copy RH byte measurements or registry IDs into that follow-up without re-deriving them.
