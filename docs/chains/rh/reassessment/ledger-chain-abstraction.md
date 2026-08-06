# Ledger chain-abstraction reassessment

> **Authority and scope.** This is a read-only architectural reassessment of the
> frozen `rh` source. It recommends no implementation, deployment, migration,
> configuration, activation, or release action. The only worktree change is
> this report. Historical fork and RPC artifacts were inspected as repository
> evidence; no RPC, account, signer, secret, transaction, or external system was
> accessed during this reassessment.

## 1. Executive recommendation

### First-draft recommendation

Preserve the existing shared
[`contracts/data/Ledger.vy`](../../../../contracts/data/Ledger.vy) and preserve
its exact-length `raw_call` for the initial Robinhood deployment candidate.
Make **no production contract change** solely to improve architectural
appearance. In particular:

- do not replace the raw call with a typed Vyper interface under the pinned
  Vyper `0.4.3` compiler;
- do not create a full `LedgerRh.vy`;
- do not insert a runtime clock/provider contract;
- do not add `chain.id` dispatch, a mutable provider, an arbitrary selector, or
  native fallback; and
- do not migrate the deployed Base Ledger for bytecode parity.

The current implementation is a narrow, immutable, two-mode discriminator:

```text
source == 0x0000000000000000000000000000000000000000
    -> use native EVM block.number

source == 0x0000000000000000000000000000000000000064
    -> STATICCALL ArbSys.arbBlockNumber()
    -> require exactly 32 return bytes
    -> decode uint256 child-chain block number

any other source
    -> reject construction
```

This is not a generic chain abstraction, but it is the smallest reviewed
implementation that serves the two concrete semantic families in scope. Its
chain-specific portion is already isolated behind internal helpers. A separate
provider or Ledger fork would add more code, artifacts, deployment state,
failure modes, and audit surface without adding a currently required semantic
family.

### The important qualification

The contract fails closed over the **configured source address and return
shape**, but it does not prove that the configured mode matches the chain:

- a Robinhood deployment constructed with zero would succeed and use
  Robinhood's native EVM `NUMBER` domain even though that is the wrong domain
  for the approved same-child-block policy;
- a non-Arbitrum chain with code at `0x64` that returns exactly 32 bytes for
  selector `0xa3b1b31d` would be accepted even if the value had different
  semantics; and
- any exact 32-byte word is a valid `uint256`, so response shape does not prove
  truth, monotonicity, receipt agreement, or chain identity.

The draft Robinhood deployment-profile script rejects zero and requires exact
`0x64` when it is invoked, which is the correct policy layer for the current
release. It is not yet a binding deployment control: no frozen deployment path
is proven to invoke it, and its RipeHq/Defaults inputs are deliberately labeled
`unapproved_placeholder`. Until a fail-before-deploy path makes the gate
mandatory, it is advisory evidence rather than an enforced mitigation. The
highest-value work is therefore deployment/profile binding, qualification,
replay, monitoring, and negative-test work—not another Ledger source revision.

### Contract-change verdict

**No Ledger contract change is warranted on the evidence available at this
baseline.** Revisit the boundary only if a real third chain needs neither
native `block.number` nor fixed ArbSys `0x64`, if the ArbSys ABI/address changes,
or if another chain-specific helper would otherwise enter Ledger. At that
point, prefer a small compile-time/internal adapter sharing one accounting core;
consider a narrowly typed immutable provider only if compile-time isolation is
not practical. A full `LedgerRh.vy` remains the last resort.

### Highest-value assurance work

1. Add a deployment-policy matrix that binds each supported chain/profile to
   the only approved mode: Robinhood mainnet/testnet to exact `0x64`; native
   profiles to exact zero. Include a negative native-profile case where
   compatible-looking code exists at `0x64`.
2. Under separate RPC/fork authority, execute the actual `0x64` system contract
   rather than a Boa double, compare raw ArbSys output to the transaction
   receipt child block number, and observe at least two child blocks that share
   one native ancestor `NUMBER`.
3. Prove historical Base replay resolves the original two-argument artifact,
   while every future native deployment uses a new three-argument migration
   with explicit zero.
4. Add composed critical-route tests that replace/fail/malform `0x64` after
   construction and prove full rollback for repayment, liquidation, withdrawal,
   and Stability Pool claims.
5. Add an explicit accepted-residual test showing that a well-formed but false
   32-byte value is accepted, and bind that limitation to monitor behavior.
6. Rebuild the immutable-bound runtime bundle with final approved constructor
   identities before deployment; the current bundle uses deterministic,
   unapproved placeholders and is local reproduction evidence only.
7. Pin and explain both pre-existing `checkAndUpdateLastTouch` selectors, and
   add an identity-semantics inventory guard so a new production use cannot
   silently escape block-clock classification.

## 2. Exact baseline and source identities

### Frozen repository authority

| Item | Reproduced value |
| --- | --- |
| Repository | `/Users/wigglez/dev/ripe-protocol` |
| Requested commit | `0d5994aa78f9d6f35b59bd7a2bc70fa18706e693` |
| Reproduced `HEAD` | `0d5994aa78f9d6f35b59bd7a2bc70fa18706e693` |
| Requested tree | `b68dffdddbdc7c5ae8423db049099c1632b478c9` |
| Reproduced tree | `b68dffdddbdc7c5ae8423db049099c1632b478c9` |
| Parent | `ae0cb49bad9ad615deb11cbca5d3a2c20e38bb4c` |
| Commit date | `2026-07-30T15:40:36-06:00` |
| Commit subject | `docs(rh): finalize deployment-owner handoff` |
| Isolated branch | `codex/rh-reassess-ledger-abstraction` |
| Isolated worktree | `/private/tmp/rh-reassess-ledger-abstraction.YkT2eH` |
| Worktree mode | `0700` / `drwx------` |
| Starting worktree state | clean; empty index and no untracked files |
| Primary worktree | remained clean on `rh` at the same commit/tree |

The prompt names `contracts/core/Ledger.vy`, but that path does not exist at the
frozen tree. The canonical production source is
[`contracts/data/Ledger.vy`](../../../../contracts/data/Ledger.vy). This path
correction is repository fact, not baseline drift.

### Ledger source and history identities

| Item | Reproduced value |
| --- | --- |
| Current source Git blob | `590341e3f9091105036c1cc497bd862ea3769248` |
| Current source SHA-256 | `6bd731a6ce9084de213494ebad09f8e52c782153842708b78f90fa178c06e9e3` |
| Pre-S5 commit | `db5e589e13bc39002a345d70cb9d9a38eb13fd67` |
| Pre-S5 source SHA-256 | `00d86847273621857b80701be5faf7ca88ff9505f68671d5b6ab3c8b4ec972e0` |
| Originating Ledger change | `ed10d4d13fb22c2d00ad2dc06b4faece1e2629f3` |
| Originating change subject | `fix(rh): complete S5 Ledger guard and inventory reconciliation` |
| Exact Ledger Git numstat | `41` insertions, `6` deletions |
| Exact Ledger patch SHA-256 | `bdc51282aff7f15655ff247caca26765b82e48467357cb212709237f3b2722c9` |
| Complete reviewed S5 integration | `81478fe33dfa47a8e135682a047b64949650cb29` |
| Commits after S5 integration | `42` |
| Source drift after `ed10d4d` | none; current source blob is identical |
| ABI Git blob | `5c0739c7b300747360fa6ba47249d75f33cca27d` |
| Committed ABI SHA-256 | `c6fc1c410e13f144ae9e9d1853378d476fa578211b08f67b23f80c2075bc415f` |

The current source and committed ABI remain byte-identical to the originating
production Ledger change. Later commits added review, hardening, profile,
artifact, monitoring, replay, and mutation evidence without changing the
production Ledger bytes.

The exact `41/6` Git numstat contains `40` inserted and `5` deleted substantive
diff lines plus one add/delete accounting pair caused only by normalizing the
file's missing final newline. The EOF-only pair changes no Vyper semantics.

### Current compiler and artifact identities

The focused reproduction used Python `3.12.0`, Vyper
`0.4.3+commit.bff19ea2`, Titanoboa `0.2.7`, and pytest `8.4.2`.

| Artifact | Current raw-call Ledger |
| --- | ---: |
| Creation bytecode | `13,730` bytes |
| Runtime template | `13,125` bytes |
| Local immutable-bound runtime in the recorded profile | `13,253` bytes |
| EIP-170 headroom from runtime template | `11,451` bytes |
| Persistent storage entries | `37`, unchanged from pre-S5 |
| Transient storage entries | `0` |
| `ACTION_BLOCK_SOURCE` code-layout offset | `96`, length `32`, type `address` |
| Compiler optimization | source-governed default `gas` |
| Compiler-input integrity | `62cc9e492ee1b1a3e84ad104507d684dc81edecef969fc0ae0f7a1586dd0d830` |

The runtime template is not a deployed-runtime identity because four immutable
words are constructor-bound. The committed local bundle is explicitly labeled
local reproduction evidence and contains deterministic placeholder RipeHq and
Defaults addresses.

### Fresh focused validation

All focused-pytest caches, pyc files, Hypothesis state, Boa compiler cache, and
pytest basetemps were placed below private mode-`0700`
`/private/tmp/ledger-reassess-validation.AW54fX`. The later typed-return probe
used private mode-`0700`
`/private/tmp/ledger-typed-return-check.ehMf7X`. All known RPC, account, signer,
and secret variables were unset. No whole-suite run was performed.

| Validation | Fresh result |
| --- | --- |
| Ledger/Teller action-block, Robinhood profile, artifact bundle, artifact negatives, and block-clock inventory modules | `248 passed`, `3` established pytest rewrite warnings |
| Native `test_ledger.py` last-touch selection | `14 passed`, `87 deselected`, same `3` warnings |
| Standalone block-clock checker | exit `0`; `99/94/17`, `606` cadence candidates, `95` Vyper paths |
| Fresh Vyper typed-return probe | `0`/`31` bytes reverted; `32`/`33`/`64`/`96` bytes accepted and decoded first word |
| Initial sandboxed attempt | `143 passed`, `105` setup errors solely because the sandbox denied the session-level loopback bind |
| Identical local-only retry with loopback permission | all `248` selected tests passed |

The exact selected module command, inside the external-cache environment
described above, was:

```bash
PY=/Users/wigglez/dev/ripe-protocol-validation-envs/rh-wave2-py312/bin/python
VALIDATION_ROOT=/private/tmp/ledger-reassess-validation.AW54fX
RIPE_AUDIT_CACHE="$VALIDATION_ROOT/boa"

env \
  -u WEB3_ALCHEMY_API_KEY -u ALCHEMY_API_KEY \
  -u ETH_RPC_URL -u BASE_RPC_URL -u RPC_URL -u WEB3_PROVIDER_URI \
  -u PRIVATE_KEY -u MNEMONIC \
  -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY \
  PYTHONDONTWRITEBYTECODE=1 \
  PYTHONPYCACHEPREFIX="$VALIDATION_ROOT/pycache" \
  XDG_CACHE_HOME="$VALIDATION_ROOT/xdg" \
  HYPOTHESIS_STORAGE_DIRECTORY="$VALIDATION_ROOT/hypothesis" \
  ETHERSCAN_API_KEY=local-placeholder \
  RIPE_AUDIT_CACHE="$RIPE_AUDIT_CACHE" \
  "$PY" -c \
  'import os,sys; from boa.interpret import set_cache_dir; set_cache_dir(os.environ["RIPE_AUDIT_CACHE"]); import pytest; raise SystemExit(pytest.main(sys.argv[1:]))' \
  -q -p no:cacheprovider --basetemp="$VALIDATION_ROOT/basetemp-rerun" \
  tests/data/test_ledger_action_block.py \
  tests/core/teller/test_teller_action_block.py \
  tests/deployment_profiles/test_ledger_robinhood_profile.py \
  tests/deployment_profiles/test_ledger_artifact_bundle.py \
  tests/inventory/test_contract_artifacts.py \
  tests/inventory/test_block_clock_inventory.py
```

The initial sandbox-denied attempt used `basetemp`; the identical local-only
retry used `basetemp-rerun`. A future rerun should substitute a fresh
mode-`0700` validation root rather than reuse this recorded path.

The three warnings are the known import-order rewrite warnings for
`_hypothesis_globals`, `hypothesis`, and `boa`, caused by setting Boa's external
cache before importing pytest. They were not skips, suppressions, xfails, or
product warnings.

## 3. Line-by-line explanation of the current chain-specific behavior

### Direct dependency boundary

Ledger directly imports or composes:

| Dependency | Use in Ledger | Chain-abstraction relevance |
| --- | --- | --- |
| [`contracts/modules/Addys.vy`](../../../../contracts/modules/Addys.vy) | Stores immutable RipeHq; resolves Teller and Switchboard through typed RipeHq/Switchboard interfaces and registry IDs | Authorizes the only runtime caller of the clock path; does not select a clock |
| [`contracts/modules/DeptBasics.vy`](../../../../contracts/modules/DeptBasics.vy) | Supplies pause, mint-capability, recovery, and `Department` implementation | `isPaused` rejects housekeeping before the clock read; no chain selection |
| [`interfaces/Department.vyi`](../../../../interfaces/Department.vyi) | Implemented/exported department ABI | No ArbSys or block-number semantics |
| [`interfaces/Defaults.vyi`](../../../../interfaces/Defaults.vyi) | Constructor reads three RIPE allocation values | Unrelated to clock selection, but a failing Defaults call reverts construction |
| [`interfaces/ConfigStructs.vyi`](../../../../interfaces/ConfigStructs.vyi) | Supplies `DebtTerms` embedded in Ledger structs | Persistent-layout dependency; unrelated to the clock |
| `IERC20` through `DeptBasics` | Fund recovery | No clock relevance |

There is deliberately **no ArbSys interface import in production Ledger**.
Ledger uses Vyper built-ins `method_id`, `raw_call`, `len`, and `abi_decode`.
The test-only
[`ActionBlockIdentityProbe.vy`](../../../../contracts/testing/ActionBlockIdentityProbe.vy)
does declare a typed `ArbSys` interface, but it is not imported or called by
production Ledger.

The only production caller of the relevant Ledger entry point is the typed
`Ledger` interface in
[`contracts/core/Teller.vy:82-85`](../../../../contracts/core/Teller.vy#L82).
Teller derives `_shouldCheck` from:

```text
MissionControl.shouldCheckLastTouch()
&& action is classified higher-risk
&& user is not an Underscore wallet/vault
```

It then calls `Ledger.checkAndUpdateLastTouch(user, shouldCheck)`. Six direct
Teller action families are higher-risk: `withdraw`, `withdrawMany`,
`rebalance`, `borrow`, `claimFromStabilityPool`, and
`claimManyFromStabilityPool`. Lower-risk housekeeping still writes a touch and
can arm a later checked action. The external
`Teller.performHousekeeping` boundary is broader and remains a separate
authorization/griefing concern.

The Underscore exemption is preserved shared-source behavior, but the approved
initial Robinhood launch posture omits the Underscore registry, wallets,
vaults, routes, and reward bypass. No legitimate Underscore caller should
exercise that branch at initial launch. It remains relevant to later,
separately reviewed Underscore enablement and must remain negative-tested; it
should not be counted as active launch complexity.

### Lines 130-131: fixed system address and immutable discriminator

```vyper
ARB_SYS: constant(address) = 0x0000000000000000000000000000000000000064
ACTION_BLOCK_SOURCE: public(immutable(address))
```

- `ARB_SYS` is compile-time code, not storage and not configurable.
- Address `0x64` is decimal `100`, the fixed Nitro ArbSys system-contract
  address assumed by the reviewed design.
- `ACTION_BLOCK_SOURCE` is constructor-bound code data, not a persistent
  storage slot.
- `public` adds `ACTION_BLOCK_SOURCE() -> address` to the ABI.
- The address-shaped value is a mode discriminator, not a generic provider:
  only zero and exact `0x64` are accepted.

### Lines 189-192: constructor allowlist and binding

```vyper
def __init__(_ripeHq: address, _defaults: address, _actionBlockSource: address):
    assert _actionBlockSource in [empty(address), ARB_SYS]
    ACTION_BLOCK_SOURCE = _actionBlockSource
```

- The constructor ABI changed from two addresses to three.
- Zero selects native mode.
- Exact `0x64` selects ArbSys mode.
- Every other address reverts before module initialization.
- The value cannot later be changed, preventing governance from redefining the
  domain of already stored `lastTouch` values.
- No `chain.id`, code hash, ArbOS version, or chain/profile pairing is checked.

### Lines 194-197: construction-time source probe

```vyper
if _actionBlockSource == ARB_SYS:
    _: uint256 = self._getArbActionBlock()
```

- Native mode performs no external clock call.
- ArbSys mode must successfully perform and decode the approved call during
  deployment.
- If address `0x64` is missing, reverts, or returns a non-exact response, the
  entire creation transaction reverts.
- The decoded value is intentionally discarded; the probe checks present-time
  compatibility, not a minimum value or monotonicity.
- A later system-contract outage or upgrade is not prevented by this one-time
  probe.

### Lines 199-205: unrelated constructor dependencies

After the source probe:

- `addys.__init__(_ripeHq)` requires a nonzero RipeHq and binds the registry
  immutable;
- `deptBasics.__init__(False, False, False)` starts unpaused and with no mint
  capabilities; and
- a nonzero Defaults address is typed-called for rewards, HR, and bond
  allocations.

These calls do not alter chain selection. Any failure still reverts the whole
deployment atomically.

### Lines 211-222: exact ArbSys call

```vyper
response: Bytes[65] = raw_call(
    ARB_SYS,
    method_id("arbBlockNumber()", output_type=Bytes[4]),
    max_outsize=65,
    is_static_call=True,
    revert_on_failure=True,
)
assert len(response) == 32
return abi_decode(response, uint256)
```

The exact call contract is:

| Property | Exact behavior |
| --- | --- |
| EVM operation | `STATICCALL` |
| Target | `0x0000000000000000000000000000000000000064` |
| Function signature | `arbBlockNumber()` |
| Selector/calldata | `0xa3b1b31d`, exactly four selector bytes and no arguments |
| Value | none; static call |
| Explicit gas cap | none; the Vyper call uses the available call-gas policy |
| Captured returndata | at most `65` bytes into `Bytes[65]` |
| Accepted length | exactly `32` |
| Decode | ABI-decode the single word as `uint256` |
| Returned meaning assumed | Nitro child-chain block identity |
| Native fallback | none |

Failure behavior:

| Target behavior | Ledger behavior |
| --- | --- |
| Missing/no code | call returns empty data; exact-length assertion reverts |
| Explicit revert or failed call | failure propagates because `revert_on_failure=True` |
| Empty or 1-31 bytes | exact-length assertion reverts |
| Exactly 32 bytes | accepted; any 32-byte word is a valid `uint256` |
| 33-65 bytes | observed length is not 32; reverts |
| More than 65 bytes | captured sentinel length is 65; reverts |
| ABI-looking dynamic or two-word data | rejected unless total observed length is exactly 32 |
| Well-formed but false value | accepted; truth is outside the ABI check |

`65` is conservative rather than uniquely necessary. A `33`-byte bound would
also provide a one-byte overlength sentinel. A `32`-byte bound would be unsafe
for this policy because longer returndata could be truncated into an apparently
canonical word.

`is_static_call=True` prevents state modification throughout the called frame
tree. It does not prove that the returned word is truthful.

### Lines 225-230: internal dispatch

```vyper
if ACTION_BLOCK_SOURCE == empty(address):
    return block.number
return self._getArbActionBlock()
```

- Chain logic is already behind an internal helper.
- Zero returns the EVM `NUMBER` opcode exposed by Vyper as `block.number`.
- Because constructor validation allows only zero or `0x64`, the final return is
  intended to be ArbSys mode.
- There is no mutable provider, arbitrary selector, third branch, or fallback.
- A future chain with a different execution-block identity has no safe mode
  unless its approved semantics happen to be native or exact ArbSys `0x64`.

### Lines 233-248: ABI overload, compare, write, and rollback semantics

The external signature is:

```vyper
def checkAndUpdateLastTouch(
    _user: address,
    _shouldCheck: bool,
    _mc: address = empty(address),
):
```

`_mc` is unused in the body and predates the Robinhood/S5 change. Vyper emits
two live external selectors:

| Signature | Selector | In-repository caller |
| --- | --- | --- |
| `checkAndUpdateLastTouch(address,bool)` | `0x222a390e` | Teller interface/callsite |
| `checkAndUpdateLastTouch(address,bool,address)` | `0xec74f007` | None located |

Both selectors enter the same Teller-gated body and therefore both reach the
selected clock path. Removing `_mc` would be an unrelated ABI change and is
not justified in this release. Its unused second selector is accepted
low-severity ABI complexity, pinned by dual-selector tests and artifact gates,
not a Robinhood-introduced defect.

1. Resolve the current Teller address through RipeHq and require it as caller.
2. Require Ledger not paused.
3. Read the selected action-block identity.
4. If `_shouldCheck`, require `lastTouch[user] != actionBlock`.
5. Write `lastTouch[user] = actionBlock` for checked and unchecked calls.
6. Require the account not locked.

The final lock check occurs after the tentative write, but any revert rolls the
write back. A later failure in Teller's enclosing transaction also rolls the
Ledger write back.

The comparison is equality-only. A different lower value is accepted. This
preserves the historical same-identity policy but leaves source regression and
truthfulness to qualification and monitoring.

## 4. Historical rationale reconstructed from code, tests, Git, and evidence

### Evidence traceability

This reassessment used the following frozen repository records as evidence,
while treating their historical statuses as historical and the current status
overlay as controlling:

| Record | Contribution to this reassessment |
| --- | --- |
| [`block-number-inventory.md`](../block-number-inventory.md) | Complete production `block.number` population, semantic categories, BN-002 identity defect, and configuration-first disposition of other clock uses |
| [`shared-block-clock-specification.md`](../shared-block-clock-specification.md) | Owner-approved same-execution-block direction, no fallback/`chain.id` policy, Base exception, and cadence/value boundaries |
| [`minimal-contract-change-reassessment.md`](../minimal-contract-change-reassessment.md) | Prior no-change/configuration/disable alternatives and owner-selected shared-source direction |
| [`ledger-guard-security-decision.md`](../ledger-guard-security-decision.md) | Exact internal-discriminator architecture, raw/typed/provider comparison, threat model, accepted risks, and approval history |
| [`ledger-guard-implementation-record.md`](../ledger-guard-implementation-record.md) | Exact source/ABI/layout/artifact identities, validation, and historical controlled Boa gas measurements |
| [`block-clock-validation-plan.md`](../block-clock-validation-plan.md) | Repeated/jump profile, BN-002 proof requirements, and cross-domain regression plan |
| [`smart-contract-changes/ledger.md`](../smart-contract-changes/ledger.md) | Later consolidated Ledger audit, dual-selector ABI, external-consumer, and residual-risk findings |
| [`hardening-pass-report.md`](../hardening/hardening-pass-report.md) | Post-S5 test, artifact, mutation, replay, and monitoring hardening scope |
| [`ledger-local-artifact-bundle.json`](../hardening/ledger-local-artifact-bundle.json) | Local placeholder-bound artifact evidence and its non-deployment boundary |
| [`ledger-monitoring-runbook.md`](../hardening/ledger-monitoring-runbook.md) | Proposed runtime observation and incident controls |
| [`ledger-replay-policy.md`](../hardening/ledger-replay-policy.md) | Historical Base two-argument artifact and forward three-argument deployment policy |
| [`status.yaml`](../status.yaml) | Current overlay: S5 architecture/implementation approved, reviewed, and integrated; downstream binding, deployment proof, monitoring, and release still open |

### Original behavior and problem statement

The pre-S5 Ledger stored native `block.number` and rejected a checked action
after any same-number touch. That policy was intended to mean one checked
action per user per actual execution block, with lower-risk touches also arming
the guard.

Repository specifications distinguish:

- on ordinary native-EVM semantics, `block.number` is the intended execution
  identity; and
- on the targeted Nitro family, in-contract EVM `NUMBER` is an ancestor
  estimate that may repeat while multiple child execution blocks advance,
  while `ArbSys.arbBlockNumber()` and receipt block numbers identify the child
  chain.

Using inherited `block.number` on Robinhood could therefore reject a checked
action in a later child block merely because both child blocks shared one
ancestor estimate. Disabling the guard would remove the protection rather than
port it.

### Why the broader protocol does not need this identity abstraction

The current checker freezes `99` production `block.number` occurrences across
`94` lines and `17` files. Only one occurrence—the native branch inside
Ledger's BN-002 action-block helper—is selected to change **identity source**
between supported chain families. The other `98` occurrences deliberately
remain in the chain's native `NUMBER` domain.

Those other occurrences are not one homogeneous `/6` conversion bucket. The
inventory separately classifies configurable durations/capacity windows,
absolute-number inputs, per-number rewards/rates, checkpoints, telemetry,
sampling, auctions/epochs, and disabled or omitted integrations. Where the
owner approves equivalent wall-time duration, a Base `43_200` count may become
a Robinhood `7_200` count using the narrow nominal `/6` policy; rates,
absolute numbers, identity checks, telemetry, and disabled features require
their own dispositions.

This separation is the strongest protocol-level reason not to introduce a
generic runtime clock provider: Ledger needs a chain-family-specific execution
**identity**, while the remaining native-number uses are configuration,
economic-policy, telemetry, or feature-admission questions. A future chain
requires new contract clock code only if its required identity semantics fit
neither native `block.number` nor qualified ArbSys `0x64`; a different cadence
alone is not such a trigger.

### Owner/design decisions reflected in the repository

The history is staged. The shared specification first recorded the direction
as owner-approved while leaving exact architecture and ArbSys evidence to S5
Stage A. The later security decision approved the exact immutable
zero/`0x64` internal discriminator, and the current status overlay records S5
as approved, reviewed, and integrated. Therefore this reassessment does **not**
reopen the following settled architecture:

1. preserve the same-execution-block equality policy;
2. keep native mode for ordinary EVM deployments;
3. use fixed ArbSys child-block identity for Robinhood;
4. bind the choice immutably at deployment;
5. fail construction and runtime calls closed, with no native fallback;
6. reject arbitrary providers and selectors;
7. keep one forward accounting source;
8. leave the deployed Base Ledger on its historical bytecode; and
9. do not migrate state-bearing Base Ledger merely for source parity.

Still-open work is downstream constructor/profile binding, authentic
deployment proof, monitoring/operations ownership, and release—not owner
selection of the shared Ledger/raw-call architecture.

### Git history

Commit `ed10d4d...` made the complete production source change:

- added `ARB_SYS` and `ACTION_BLOCK_SOURCE`;
- changed the constructor from two to three arguments;
- added the construction probe;
- added `_getArbActionBlock` and `_getActionBlock`;
- replaced direct `block.number` comparison/write with one selected identity;
  and
- updated the `lastTouch` comment.

Its exact `41/6` numstat is `40/5` substantive diff lines plus one add/delete
pair from adding the final LF to a file that previously lacked it.

No debt, vault, points, rewards, auction, contributor, bond, bad-debt, or pool
accounting changed. The current source remains byte-identical to that commit.

### Why the first typed-call candidate was rejected

The rejected candidate used a normal typed Vyper interface:

```vyper
interface ArbSys:
    def arbBlockNumber() -> uint256: view

return staticcall ArbSys(ARB_SYS).arbBlockNumber()
```

Under pinned Vyper `0.4.3`, the generated typed-call decoder treats 32 bytes as
a minimum for a static `uint256` return. Controlled responders confirmed the
general boundary: `0` and `31` bytes revert, while `32`, `33`, `64`, and `96`
bytes all succeed and decode the first word. The typed path therefore accepts
any observed return size of at least one word, ignoring trailing data.

The committed test suite mutation-tests the representative `64`-byte case,
while its production raw-call matrix rejects `33`, `64`, and `96` bytes. The
fresh controlled probe extended the typed side to `33` and `96` bytes. The raw
call was therefore selected to enforce an exact trust boundary, not because
ArbSys cannot be called through a typed interface. Adding the `33`/`96` typed
cases to the committed mutation test would make the general rule durable.

### Later hardening

Post-S5 hardening added, without modifying Ledger:

- source/profile mutation tests for typed substitution, 32-byte truncation,
  removed constructor probe, native fallback, monotonic comparison, zero/wrong
  Robinhood source, and missing readbacks;
- a draft exact-`0x64` Robinhood profile;
- deterministic constructor encoding and local immutable-bound artifact
  evidence;
- artifact, ABI, code-layout, and persistent-layout gates;
- dual-selector behavior tests;
- trusted-deposit non-arming and rollback proof;
- a historical/native replay policy;
- `lastTouch` consumer semantics; and
- monitoring/topology and release-packet documents.

These close several gaps listed in the older
[`smart-contract-changes/ledger.md`](../smart-contract-changes/ledger.md), but
they remain offline candidate evidence. They do not prove an authentic
Robinhood deployment, receipt agreement, monitor installation, or release
authority.

### Fork/replay evidence boundary

The committed mainnet/testnet fork JSON records historical read-only observations
of:

- chain IDs `4663` and `46630`;
- code marker `0xfe` at `0x64`;
- expected selector and ArbOS version facts;
- adjacent child identities;
- repeated ancestor `l1BlockNumber`; and
- explicit limitations.

The evidence also states that Boa/PyEVM could not execute Nitro's native `0xfe`
system contract, so local action probes substituted an exact observed-value
controlled double. The artifacts contain no authentic receipt, sequencer,
multi-transaction inclusion, signature, broadcast, or Ledger deployment proof.
They are useful historical topology evidence, not a substitute for a real
precompile execution test.

## 5. Raw-call versus typed-interface analysis

### Direct answers

**Why raw call?** To observe returndata length and require exactly one 32-byte
word before decoding a security-bucket identity.

**Is raw call required by Vyper?** It is not required to invoke ArbSys or decode
a canonical response. It is required by the selected exact-length policy under
the pinned Vyper `0.4.3` typed-call behavior, because that typed path does not
expose or reject trailing returndata.

**Is it required by the ArbSys/precompile ABI?** No. The official-shaped ABI is
ordinary `arbBlockNumber() -> uint256`, and the test-only probe uses a typed
interface. The special constraint comes from Ledger's stronger caller-side
return-shape policy.

**Is it required for compatibility?** Not for a correct Nitro implementation.
It is a fail-closed hardening choice against missing, malformed, incompatible,
or overlong responses.

**Is it required for return-data handling?** Yes, if exact length remains a
requirement. Vyper `0.4.3` typed decoding accepts any tested return of at least
one word (`32`, `33`, `64`, and `96` bytes); `raw_call` lets Ledger retain a
one-byte-overlength sentinel and inspect the observed length.

### Fresh compiler comparison

Compiled from the frozen tree with the same Vyper version and source-owned gas
optimization:

| Variant | Creation bytes | Runtime-template bytes | Persistent layout | Conservative gas estimate for either touch overload |
| --- | ---: | ---: | ---: | ---: |
| Pre-S5 native-only | `13,226` | `12,874` | `37` entries | `45,800` |
| Current exact-length raw helper | `13,730` | `13,125` | `37` entries | `49,484` |
| Typed-interface mutant | `13,515` | `13,018` | `37` entries | `49,006` |

Replacing raw with typed would save `215` creation bytes, `107` runtime-template
bytes, and `478` units in Vyper's conservative function estimate. Those are
small savings relative to the security-policy change. The compiler estimate is
not a measured per-chain transaction cost.

The gas-estimate values are not emitted by `vyper -f abi` or metadata output.
They were reproduced through Vyper `0.4.3`'s internal compiler API by
constructing each variant with the same input bundle/settings and
`CompilerData(..., show_gas_estimates=True)`, then reading
`_ir_info.gas_estimate` for the touch overloads. This is an internal,
compiler-version-specific inspection recipe, which is another reason to treat
the figures as conservative comparisons rather than transaction predictions.

Historical controlled Boa measurements recorded in
[`ledger-guard-implementation-record.md`](../ledger-guard-implementation-record.md)
found:

| Operation | Pre-S5 native | Current native | Current ArbSys |
| --- | ---: | ---: | ---: |
| Unchecked touch | `31,805` | `31,929` | `34,856` |
| Checked successful touch | `31,890` | `32,018` | `34,945` |

Thus the current native branch adds about `124-128` local-EVM gas versus the
old source, while the ArbSys path adds about `3,051-3,055`. A provider contract
would add another external call frame and code/deployment surface.

### Security comparison

| Property | Current raw call | Typed Vyper `0.4.3` call |
| --- | --- | --- |
| Missing/empty return | rejects | rejects for minimum-size failure |
| Short return | rejects | rejects |
| Exact 32-byte return | accepts | accepts |
| Any return longer than 32 bytes | rejects (`33`, `64`, and `96` tested) | accepts any tested size at least 32 (`33`, `64`, and `96`) and decodes first word |
| Reverting source | propagates | propagates |
| Static context | explicit | typed `staticcall` |
| False exact word | accepts | accepts |
| ABI/storage compatibility | current ABI/layout | can remain ABI/layout-equal |
| Bytecode/artifact identity | reviewed current identity | entirely new creation/runtime identities |

The typed alternative is smaller but weaker against ambiguous return shape. No
evidence shows that the small size/gas saving outweighs reopening the accepted
security boundary.

## 6. Cross-chain behavior matrix

| Environment/configuration | Construction | Runtime identity | Failure/semantic result | Assessment |
| --- | --- | --- | --- | --- |
| **Existing Base deployment** | Historical two-argument Ledger already deployed | Native `block.number` in old bytecode | No raw call and no S5 deployment/runtime cost | Keep permanently untouched |
| **Fresh Base deployment of current source with zero** | Succeeds if other constructor dependencies succeed | Native `block.number` | Same intended native semantic family; new ABI/artifact | Supported forward-native mode, but requires a new migration |
| **Fresh Base current source with `0x64`** | Normally expected to fail if `0x64` has no compatible code; would succeed if compatible exact-return code exists | Whatever exact word `0x64` reports | Contract does not know this is Base | Deployment profile must reject; contract alone is not chain-bound |
| **Ethereum current source with zero** | Succeeds if other constructor dependencies succeed | Ethereum `block.number` | Native execution-block identity | Architecturally compatible forward-native mode; no deployment asserted |
| **Ethereum current source with `0x64`** | Expected to fail on empty/incompatible `0x64`; would accept compatible exact-return code | Returned word | No chain-ID defense | Must be rejected by deployment policy |
| **Robinhood with exact `0x64`** | Requires successful exact 32-byte constructor probe | ArbSys child-chain number | Runtime source failure blocks housekeeping; no fallback | Intended Robinhood mode |
| **Robinhood with zero** | **Contract construction succeeds** | Native EVM `NUMBER`/ancestor domain | Wrong approved security bucket despite syntactic success | Draft profile script rejects this only when invoked; no binding deployment path is yet proven |
| **Local Boa with zero** | Succeeds | Boa native block number | Used by ordinary fixtures | Valid native behavioral model, not chain proof |
| **Local Boa with `0x64` and no code** | Reverts | none | Empty returndata fails exact-length assertion | Correct fail-closed behavior |
| **Local Boa with installed exact double at `0x64`** | Succeeds | Controlled storage value | Enables held/advanced/malformed behavior tests | Strong compiler/EVM behavior evidence, not authentic Nitro proof |
| **Future chain with correct native semantics** | Zero succeeds | Native `block.number` | Safe only if native number is the approved execution identity | Extensible without source change, but needs explicit profile review |
| **Future chain with exact Nitro-compatible `0x64`** | `0x64` succeeds if return shape matches | Reported child identity | Safe only if address, ABI, truth, and topology are qualified | Reuse is possible but not automatic |
| **Future chain with another semantic family** | Nonzero non-`0x64` rejects; zero may succeed syntactically but be semantically wrong | No safe approved mode | Fail-closed over configured addresses, not over wrong-zero semantics | Requires architecture/source decision |

### Is the code Arbitrum-specific, Robinhood-specific, or universal?

- The raw helper is **Arbitrum Nitro/ArbSys-specific**.
- Nothing in the source is Robinhood-chain-ID-specific.
- The shared Ledger is safely applicable to supported deployments only when
  deployment policy supplies the right mode and the chain satisfies that
  mode's semantic assumptions.
- It is not safely universal for every EVM chain.
- Robinhood is the current reason for the ArbSys branch, but any separately
  qualified Nitro chain with the same system address and ABI could use it.

### Does it fail closed?

It fails closed for:

- every configured address other than zero or exact `0x64`;
- missing, reverting, short, or overlong ArbSys responses;
- source failure after deployment;
- unauthorized caller, pause, equal checked identity, and locked account; and
- partial writes when an enclosing call reverts.

It does **not** fail closed for:

- zero selected on a chain whose native number has the wrong semantics;
- `0x64` selected on another chain with compatible-shaped but different code;
- a false, stale, repeated, or regressed exact 32-byte word;
- a chain upgrade that preserves shape while changing meaning; or
- deployment tooling that binds the wrong reviewed artifact/profile.

### Can a chain-specific value be accepted on another chain?

Yes. There is no `chain.id` check and no code-hash check. If another chain
supplies code/system behavior at `0x64` that responds to `0xa3b1b31d` with
exactly 32 bytes, Ledger accepts the decoded word. This is not necessarily a
runtime exploit—the deployer must choose `0x64`—but it is a configuration and
release-integrity risk. The recommended mitigation is an exact supported-chain
deployment-profile matrix plus immutable readback and artifact proof, not a new
contract branch. The current draft script demonstrates the policy but is not
the mitigation until an authoritative deployment workflow must execute it and
fail before any deployment or registration action.

## 7. Alternative architecture comparison

### Summary decision table

| Alternative | First-draft disposition | Principal reason |
| --- | --- | --- |
| Preserve existing shared Ledger | **Recommend** | Smallest reviewed two-mode solution; exact-return fail-closed behavior |
| Replace raw call with typed interface | **Reject now** | Weakens exact-length boundary for small byte/gas savings |
| Isolate chain logic behind internal helper | **Already implemented** | `_getActionBlock` and `_getArbActionBlock` already provide this boundary |
| Inject clock/block-number adapter | **Defer** | Adds contract/deployment/liveness surface without a third semantic family |
| Select behavior using immutable deployment configuration | **Already implemented; strengthen external binding** | Current address-shaped immutable selects mode; profile-to-chain binding remains external |
| Create `LedgerRh.vy` | **Reject** | Duplicates the complete state-bearing accounting source |
| Create reusable chain-clock module or contract | **Compile-time module is future preference; runtime contract deferred** | Useful only when another semantic family justifies added build/runtime complexity |
| No contract change; improve tests/docs only | **Recommend** | Directly addresses the remaining evidence and deployment risks |

### A. Preserve the existing shared Ledger

| Dimension | Assessment |
| --- | --- |
| Security properties | Immutable two-value allowlist; exact returndata; static call; constructor probe; no fallback; one canonical accounting source |
| Failure modes | Wrong zero/`0x64` deployment pairing; exact-word false value; runtime ArbSys outage creates housekeeping denial of service |
| Upgrade/deployment complexity | Lowest for fresh Robinhood deployment; exact third constructor word and readback required; existing Base stays untouched |
| Storage/ABI compatibility | Current 37-entry storage; current 92-entry ABI; constructor differs from historical Base artifact |
| Gas/bytecode | Current measured/compiled values above; ample EIP-170 headroom |
| Future-chain extensibility | Native and exact ArbSys families only; source decision required for a third family |
| Test burden | Maintain both modes, malformed returns, route rollback, profile, artifact, and replay gates |
| Audit burden | One Ledger source plus explicit chain-specific helper review |
| Blast radius | Any source edit affects the canonical forward Ledger; deployed Base bytes do not change |
| Rollback strategy | Before deployment, select the prior reviewed artifact; after stateful deployment, no trivial in-place rollback—pause/contain and owner-approved state strategy |

### B. Replace `raw_call` with a typed interface

| Dimension | Assessment |
| --- | --- |
| Security properties | Typed ABI clarity and static call; loses exact overlength rejection under Vyper `0.4.3` |
| Failure modes | Accepts every tested return size at least 32 bytes (`33`, `64`, `96` included); still accepts false exact word and source outage |
| Upgrade/deployment complexity | Small source edit but invalidates reviewed bytecode, artifact bundle, mutation evidence, and Gate records |
| Storage/ABI compatibility | Persistent layout and external ABI can remain identical; internal interface adds no public selector |
| Gas/bytecode | About `-215` creation bytes, `-107` runtime-template bytes, and `-478` conservative gas estimate versus current |
| Future-chain extensibility | No improvement; still fixed `0x64` |
| Test burden | Must deliberately relax/remove overlength negatives and justify the changed trust policy |
| Audit burden | Reopens the exact-return decision and requires compiler-version-specific review |
| Blast radius | All future shared Ledger deployments and every ArbSys-mode action |
| Rollback strategy | Revert to reviewed raw-call artifact before deployment; after deployment, stateful replacement remains operationally difficult |

### C. Isolate chain logic behind an internal helper

| Dimension | Assessment |
| --- | --- |
| Security properties | Current source already isolates dispatch and ArbSys decoding in two internal helpers |
| Failure modes | A cosmetic refactor cannot remove source truth/configuration risks; a mistaken refactor can change dispatch or returndata policy |
| Upgrade/deployment complexity | Any byte change regenerates creation/runtime identities for no new capability |
| Storage/ABI compatibility | Can remain unchanged if purely internal |
| Gas/bytecode | Likely negligible or compiler-dependent differences; current compiler already inlines/organizes the helper boundary |
| Future-chain extensibility | A clearer helper name alone adds no new mode |
| Test burden | Full existing mutation/profile/artifact set must rerun |
| Audit burden | Low code delta but poor risk/reward before release |
| Blast radius | Canonical forward Ledger artifact |
| Rollback strategy | Use current reviewed artifact |

### D. Inject an immutable clock/block-number adapter contract

| Dimension | Assessment |
| --- | --- |
| Security properties | Can isolate ArbSys and exact-length logic; can code-hash-pin a narrow adapter; adds adapter correctness and availability assumptions |
| Failure modes | Adapter misconfiguration, destroyed/unavailable code where possible, adapter/source revert, semantic lie, extra call-frame failure |
| Upgrade/deployment complexity | Deploy and bind another artifact/address; choose upgradeability policy; add constructor/code-hash/readback checks and registration ordering |
| Storage/ABI compatibility | Ledger persistent layout can remain unchanged if adapter address is immutable; constructor/getter semantics or ABI likely change |
| Gas/bytecode | Ledger may shrink, but each non-native touch adds another external call; total deployed bytecode grows |
| Future-chain extensibility | Strong: new adapters can represent new semantic families without editing accounting code |
| Test burden | Ledger/provider integration, every adapter, code-hash/config negatives, liveness, rollback, and deployment ordering |
| Audit burden | Ledger boundary plus each adapter and its deployment configuration |
| Blast radius | Adapter outage can block all housekeeping on every Ledger bound to it |
| Rollback strategy | Before Ledger deployment, replace adapter candidate; after immutable binding, cannot redirect without deploying/migrating Ledger state |

This becomes proportionate only when a concrete third family exists.

### E. Select behavior using immutable deployment configuration

| Dimension | Assessment |
| --- | --- |
| Security properties | Already present: immutable zero/`0x64` discriminator avoids mutable semantic drift |
| Failure modes | Wrong mode can still be chosen for the chain; address shape overstates provider generality |
| Upgrade/deployment complexity | Current approach requires only one third constructor word and readback |
| Storage/ABI compatibility | No persistent slot; current constructor and getter ABI already encode the choice |
| Gas/bytecode | Native mode avoids external clock call; ArbSys mode pays one direct system call |
| Future-chain extensibility | Only two modes; adding an enum/mode branch would require a new source release |
| Test burden | Exact profile/chain matrix and constructor negative cases |
| Audit burden | Small, enumerable configuration state |
| Blast radius | A wrong immutable choice is permanent for that deployment |
| Rollback strategy | Fail before registration/activation on readback mismatch; after deployment, use an unregistered replacement before state accrues |

A refined enum plus chain-ID binding would make intent more explicit but would
change constructor/bytecode and introduce fork/chain-ID policy. External
deployment profiles are the smaller current control, but the present draft
profile is only advisory until wired into the authoritative deployment path.

### F. Create `LedgerRh.vy`

| Dimension | Assessment |
| --- | --- |
| Security properties | Strong visual chain isolation; a direct ArbSys variant cannot be misconfigured to native mode |
| Failure modes | Source drift, missed accounting fixes, ABI/layout divergence, wrong artifact selection, duplicated bugs |
| Upgrade/deployment complexity | Separate source, ABI, compiler output, migration, profile, inventory, release, and monitoring track |
| Storage/ABI compatibility | Can start identical except constructor, but equivalence becomes a continuing invariant rather than a fact |
| Gas/bytecode | Similar per-call behavior; may remove the runtime branch/immutable but duplicates the full deployment artifact |
| Future-chain extensibility | Encourages one large Ledger fork per chain family |
| Test burden | Every Ledger, Teller, CreditEngine, Auction, Lootbox, HR, Bond, and Endaoment test must cover both variants |
| Audit burden | Near-double review of roughly 900 lines of state-bearing accounting plus drift detection |
| Blast radius | Chain-local at runtime, but forward fixes can be omitted from one variant |
| Rollback strategy | Before deployment, select shared Ledger; after state accrues, replacing either variant faces the same non-enumerable-state problem |

The isolation benefit is outweighed by permanent accounting-source risk. A
separate `LedgerRh.vy` is not justified.

### G. Create a reusable chain-clock module

| Dimension | Compile-time Vyper module | Runtime module/contract |
| --- | --- | --- |
| Security properties | Shared accounting with chain adapter chosen at build time; no extra runtime trust | Similar to injected provider; separate runtime trust/liveness |
| Failure modes | Wrong build artifact, module initialization/layout drift | Wrong address/code, call failure, semantic lie |
| Upgrade/deployment complexity | Multiple builds/artifacts and provenance | Extra deployment/address/order |
| Storage/ABI compatibility | Must prove module composition produces equivalent persistent layout and ABI | Ledger layout can stay stable if immutable, but constructor/getter likely changes |
| Gas/bytecode | No extra external call; per-variant code can be small | Extra call frame and total code |
| Future-chain extensibility | Good compile-time extensibility | Good runtime extensibility |
| Test burden | Cross-build ABI/layout/initialization and full behavior parity | Provider plus Ledger integration matrix |
| Audit burden | Shared core plus each module/build recipe | Shared core plus every runtime provider |
| Blast radius | Wrong artifact selection at deployment | Provider outage affects every dependent action |
| Rollback strategy | Choose prior artifact before deployment | Immutable binding prevents simple post-deployment redirection |

If a third family appears, the compile-time module/internal-adapter version is
the preferred first investigation because it preserves one accounting core
without an extra liveness dependency. Vyper `0.4.3` module initialization,
export, immutable, and layout behavior would need exact proof.

### H. Make no contract change and improve tests/documentation only

| Dimension | Assessment |
| --- | --- |
| Security properties | Preserves reviewed runtime; can strengthen deployment binding, evidence, and operational detection once the profile gate is mandatory |
| Failure modes | Cannot make Ledger detect a truthful-looking false word; controls remain preventive/operational |
| Upgrade/deployment complexity | No contract/artifact churn; add profile, replay, qualification, and release gates |
| Storage/ABI compatibility | Perfectly preserved |
| Gas/bytecode | No change |
| Future-chain extensibility | Documents explicit trigger for later architecture work |
| Test burden | Focused on missing cross-chain/profile, authentic-precompile, replay, critical-route, and monitor properties |
| Audit burden | Delta-only review of tests/docs/tooling; contract audit stays sealed |
| Blast radius | No production byte impact |
| Rollback strategy | Revert only candidate test/doc/tooling changes before adoption; deployed contracts unaffected |

This is the recommended implementation scope, if the owner authorizes a later
implementation phase.

## 8. Existing test coverage and weaknesses

### Tests that prove behavior

The current suites do more than pin source text:

- missing, reverting, 31-byte, 33-byte, 64-byte, and 96-byte source behavior;
- constructor and runtime failure with no fallback or partial write;
- native versus held/advanced ArbSys identity;
- equality-only behavior including a decreasing different value;
- low-to-high and high-to-low-to-high ordering;
- user isolation;
- pause, Teller authority, lock rollback, and zero-address behavior;
- complete Teller callsite classification;
- Underscore exemption while retaining writes;
- external-housekeeping propagation and rollback;
- trusted-deposit non-arming plus explicit housekeeping and enclosing rollback;
- source mutants for typed call, truncation, removed probe, fallback, and
  monotonic comparison;
- Robinhood profile mutants for zero/wrong source and missing readbacks;
- exact three-word constructor encoding;
- both pre-existing `_mc` overload selectors reaching the same Teller-gated
  body;
- deterministic local artifact reproduction in fresh processes; and
- source, ABI, storage, immutable layout, runtime size, and compiler integrity.

The typed-call mutant is particularly valuable: it compiles and demonstrates
that a `64`-byte response gets through the typed path. This is behavioral,
mutation-sensitive evidence for retaining `raw_call`; it should be
parameterized over `33`, `64`, and `96` bytes so the general minimum-size rule
is committed rather than established only by fresh review.

The Underscore tests prove preserved forward behavior, but initial Robinhood
launch configuration omits the Underscore integration. They should not be read
as proof that the exemption is reachable by a legitimate launch caller.

### Tests and checks that pin the current implementation

Other tests intentionally pin implementation:

- source-text counts for the allowlist and branch;
- complete mutant SHA-256 values;
- exact source, ABI, compiler-input, creation, runtime, and layout hashes;
- exact byte sizes;
- exact selector values; and
- inventory source locations and counts.

These are useful supply-chain and drift gates, but they do not independently
prove that the selected architecture is necessary. They should be described as
artifact/implementation pins, not behavioral chain proof.

### What the tests do not prove

1. The exact chain/profile is bound to the right mode by an approved production
   deployment process.
2. A final Robinhood deployment passes exact `0x64`, uses approved RipeHq and
   Defaults identities, or has the recorded immutable-bound runtime.
3. Nitro's authentic `0xfe` system contract executes in the test EVM.
4. ArbSys output equals a real transaction receipt child block number.
5. Multiple real Robinhood child blocks can be exercised while EVM `NUMBER`
   repeats in-contract.
6. A well-formed 32-byte value is truthful, monotonic, or sourced from the
   intended chain implementation.
7. Monitoring is installed, thresholds are adopted, or pause/unpause owners are
   assigned.
8. Historical Base replay is mechanically pinned to the original two-argument
   artifact.
9. Every critical user route fully rolls back when `0x64` becomes malformed
   after deployment.
10. A future chain has native or ArbSys-compatible semantics.
11. The draft profile is mandatory in an authoritative deployment path; today
    its rejection logic executes only if the script is invoked.
12. No new production `block.number` site introduces execution-identity
    semantics outside the reviewed BN-002 boundary.
13. External frontends, subgraphs, indexers, analytics, and monitors interpret
    public `lastTouch` in its deployment-selected domain. No production
    contract outside Ledger reads `lastTouch`, but off-chain consumers are not
    inventoried or tested here.
14. The initial-launch zero/omitted Underscore configuration makes the
    exemption unreachable by legitimate Robinhood launch routes.

### Bottom line on test quality

The current tests prove the intended local EVM/compiler behavior and are
mutation-sensitive for the main implementation choices. They are not merely
snapshot pins. The remaining weakness is chiefly **chain truth and deployment
binding**, which cannot be closed by more controlled doubles alone.

## 9. Required negative, fork, artifact, layout, and regression tests

### P0: deployment/profile negatives

1. Define one supported-chain profile matrix:

   ```text
   Robinhood mainnet 4663  -> required source 0x64
   Robinhood testnet 46630 -> required source 0x64
   approved native profile -> required source zero
   ```

2. Reject zero for Robinhood before construction.
3. Reject `0x64` for every native profile even when test code at `0x64` returns
   a canonical 32-byte word.
4. Reject chain-ID/profile disagreement, missing chain identity, missing
   immutable readback, placeholder final inputs, and runtime/code-hash mismatch.
5. Prove failure occurs before registration, configuration, state seeding, or
   activation.

The contract itself should remain chain-ID-neutral unless these deployment
controls cannot be made reliable.

### P0: authentic fork/live qualification, separately authorized

1. Pin exact Robinhood mainnet/testnet block hashes and node/Nitro/ArbOS
   evidence.
2. Execute the real system contract at `0x64` in an environment that supports
   Nitro precompiles; do not substitute a controlled double for the qualifying
   assertion.
3. Capture raw selector, raw returndata, exact length, decoded value, receipt
   block number, EVM `NUMBER`, transaction/block hashes, and code/version
   evidence in one context.
4. Require ArbSys decoded value equals receipt child block number.
5. Observe same-child repeated transactions and different-child advancement.
6. Observe at least two child blocks sharing one native ancestor `NUMBER`.
7. Test missing/reverting/malformed behavior only in a controlled environment;
   do not mutate a live system contract.

No RPC/fork execution is authorized by this report.

### P0: artifact and immutable-bound runtime

1. Rebuild source, ABI, compiler-input integrity, creation bytecode, runtime
   template, code layout, persistent layout, and final immutable-bound runtime
   from the frozen release commit.
2. Replace deterministic placeholders with final separately approved RipeHq and
   Defaults identities only under deployment authority.
3. Pin all three encoded constructor words and the resulting runtime hash.
4. Assert current source still has 37 persistent entries and no transient
   entries.
5. Compare both `checkAndUpdateLastTouch` selectors and the
   `ACTION_BLOCK_SOURCE()` getter.
6. Fail on optimizer/compiler/version drift or use of a template hash as a
   deployed-runtime identity.

### P0: Base historical replay and forward-native deployment

1. Reproduce historical Base creation/runtime from the original source or
   compiled artifact and exactly two constructor arguments.
2. Fail if historical migration discovery resolves `Ledger` to current
   three-argument source.
3. Fail if the old migration is edited to append zero while retaining its old
   migration identity.
4. For any future native deployment, require a new migration/profile with an
   explicit zero third word and zero immutable readback.
5. Prove the existing deployed Base address/code remains outside the migration
   target set.

### P1: critical-route runtime failure and rollback

After successful ArbSys-mode construction, replace the local double with each
failure shape and run:

- repayment;
- borrowing;
- withdrawal and `withdrawMany`;
- liquidation entry/settlement paths that require housekeeping;
- single and batch Stability Pool claims; and
- lower-risk touch followed by a checked action.

For each, assert:

- the expected source failure;
- unchanged `lastTouch`;
- unchanged balances, debt, vault accounting, rewards, and auction state;
- no native fallback; and
- successful recovery only after the controlled source is restored.

These are safety tests, not a claim that runtime unavailability is acceptable.

### P1: accepted-residual and monitoring tests

1. Install a source that returns an exact but deliberately false word and prove
   Ledger accepts it. Label this as the explicit contract boundary.
2. Feed repeated, advanced, jumped, and regressed identities into monitor logic.
3. Require receipt disagreement, finalized regression, wrong source getter,
   malformed response, or same-user same-child unexpected success to alert
   critically.
4. Do not page merely because native ancestor `NUMBER` repeats or jumps.
5. Pin incident evidence fields and pause/unpause authority once owners are
   assigned.

### P1: ABI surface, identity inventory, and consumer semantics

1. Pin both `checkAndUpdateLastTouch` selectors and document that the unused
   `_mc` parameter predates S5, both selectors share one Teller-gated body, and
   Teller exposes/calls only the two-argument selector.
2. Parameterize the typed-call mutant over exact `33`, `64`, and `96` byte
   responses; require all to survive typed decoding while production
   `raw_call` rejects all.
3. Add an inventory admission test requiring every new production
   `block.number` occurrence to declare its semantic class. Fail if a new
   execution-identity site appears outside the reviewed BN-002 helper without
   an explicit architecture review.
4. Add a consumer fixture showing that public `lastTouch` is a
   deployment-selected action-block identity, not universally native EVM
   `NUMBER`. Off-chain event identity should use transaction/log identity;
   the BN-026 guidance is analogous telemetry policy, not an on-chain
   `lastTouch` consumer.
5. Bind the approved launch omission to a negative test: zero Underscore
   registry and absent routes must make the exemption unreachable by legitimate
   initial-launch callers.

### P2: future architecture trigger tests

If a third semantic family is proposed:

- first write a failing profile test demonstrating that neither zero nor exact
  `0x64` is correct;
- compare compile-time module, provider, and full-fork artifacts;
- prove shared ABI, persistent layout, initialization, and accounting test
  parity; and
- require an explicit owner decision before adding a third production branch.

## 10. Recommended implementation scope, if any

### Recommended scope

No production Ledger, interface, ABI, inventory, migration, configuration, or
shared-documentation edit is recommended by this reassessment.

If the owner later authorizes implementation, the smallest useful package is:

1. supported-chain deployment/profile negative tests;
2. historical Base replay tests and a forward-native explicit-zero rule;
3. critical-route runtime-source failure/rollback tests;
4. accepted-false-word/monitor tests;
5. dual-selector, typed-overlength, identity-inventory, and external-consumer
   regression tests;
6. initial-launch Underscore-unreachability proof;
7. final immutable-bound artifact generation/readback checks; and
8. separately authorized authentic Nitro precompile/receipt qualification.

That package should not change `contracts/data/Ledger.vy`.

### Revisit triggers

Reopen the contract architecture only if:

- a third chain needs a non-native, non-ArbSys clock;
- `0x64`, the selector, returndata ABI, or ArbSys governance assumptions change;
- another chain-specific helper would enter Ledger;
- exact deployment/profile binding proves unreliable without an onchain check;
- chain-specific logic grows beyond the current small auditable boundary; or
- a proven Vyper module build can share accounting while producing
  ABI/storage/initialization-equivalent native and Robinhood artifacts.

### Preferred future order

```text
current shared internal helper
    -> compile-time/internal adapter with one accounting core
        -> narrowly typed immutable provider with code-hash proof
            -> full Ledger fork only if accounting itself must diverge
```

## 11. Owner decisions

The initial-release contract architecture is **not an open owner decision**.
The repository records the same-execution-block policy, shared-source
direction, exact immutable zero/`0x64` internal discriminator, raw exact-return
boundary, no-fallback/no-`chain.id` posture, and permanent Base live-bytecode
exception as approved, reviewed, implemented, and integrated. This report
confirms rather than reopens them.

Authentic ArbSys/receipt qualification and historical Base artifact replay are
also recorded evidence/release gates, not invitations to relax policy in this
reassessment. The remaining material owner/operations decisions are:

1. **Binding enforcement and authority:** select the authoritative deployment
   workflow that must execute the exact chain/profile matrix and immutable
   readback before construction/registration can proceed, and name its
   approver. Until then, the existing draft profile is advisory.
2. **Monitoring and incident authority:** assign read access, alert thresholds,
   incident classifier, pause quorum, chain-provider escalation, recovery
   evidence, and unpause authority.
3. **Future-chain admission:** if a concrete third semantic family or changed
   ArbSys assumption appears, decide whether to reopen architecture review.
   Cadence differences alone remain configuration work and do not trigger a
   provider/module/fork study.

No decision from the owner is needed to finish or accept this report's
no-contract-change recommendation. Any proposal to replace `raw_call`, add a
provider/module, introduce `chain.id`, or create `LedgerRh.vy` would be a new
architecture decision requiring separate authority.

## 12. Residual risks and explicit non-actions

### Residual risks if the current design is preserved

- Exact return length proves shape, not truthful child identity.
- Equality-only logic accepts a different regressed value.
- Runtime ArbSys unavailability can deny housekeeping-dependent user and
  protocol actions.
- The constructor does not bind source mode to chain ID or profile.
- Compatible-shaped code at `0x64` on another chain can be accepted.
- Robinhood zero mode is syntactically valid at the contract layer and must be
  rejected by deployment tooling.
- The current draft profile rejects zero only when explicitly invoked; it is
  not proven to be a mandatory deployment-path gate.
- Constructor probing does not protect against later system-contract upgrades.
- Local Boa doubles cannot establish authentic Nitro precompile behavior.
- The current local artifact bundle contains placeholders and is not deployment
  evidence.
- Historical Base migration is not replayable against current source without
  explicit artifact versioning.
- Existing Base and forward Ledger bytecode intentionally diverge.
- The public `lastTouch(address)` getter keeps its ABI but changes semantic
  domain in ArbSys mode. No production contract outside Ledger reads it;
  unidentified off-chain consumers may still assume native EVM `NUMBER`.
- The pre-existing unused `_mc` default parameter exposes a second live
  selector. It shares the Teller-gated clock path but remains unnecessary ABI
  complexity until a separately versioned cleanup.
- The Underscore exemption remains in shared source even though approved
  initial Robinhood launch configuration omits every legitimate Underscore
  route; later enablement reactivates its policy significance.
- External `Teller.performHousekeeping` caller-supplied user/risk/Addys behavior
  remains a separate accepted/reviewed concern.
- Monitor installation and operational owners are not established by source,
  tests, or this report.

### Explicit non-actions

This reassessment did not:

- edit any production contract, interface, ABI, configuration, inventory,
  migration, shared documentation, test, or script;
- create `LedgerRh.vy`, a provider, adapter, module, or implementation patch;
- stage, commit, push, merge, deploy, register, configure, activate, pause, or
  release anything;
- access a remote, RPC, fork endpoint, account, signer, secret, wallet, or
  transaction;
- run the complete repository test suite;
- mutate or clean the primary worktree;
- claim that a Robinhood Ledger is deployed;
- claim that repository fork evidence is authentic precompile execution;
- treat passing tests or local artifact reproduction as deployment authority;
  or
- authorize any later lifecycle phase.

The recommended stopping point is this revised report. The three open
binding/operations/future-admission controls above do not authorize contract
changes or any later lifecycle phase.
