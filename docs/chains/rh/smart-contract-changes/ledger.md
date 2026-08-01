# Ledger: portable action-block identity

> **Draft authority and scope.** This is an owner-education and independent
> technical-audit record for the integrated Ledger change. It is not an owner
> approval, deployment authorization, activation approval, or claim that a
> Robinhood Ledger exists on a live network. “Required,” “recommended,” and
> “not recommended” below are agent recommendations unless expressly labeled
> as an earlier owner decision. Further Deleverage work and every CCIP workflow
> are outside this review. Integrated Deleverage composition evidence is used
> only to assess Ledger-guard rollback.

## Current `rh` rebind

The current authority for this page is `rh` commit
`5f5d22b7ee78cbb904c4fe3c6e46599c330c4353`, tree
`7454b5456ebb6cd02d716a64b408629ab501629e`. The 28 July review remains dated
historical evidence below.

| Current identity | Value |
| --- | --- |
| Ledger source Git blob / SHA-256 | `590341e3f9091105036c1cc497bd862ea3769248` / `6bd731a6ce9084de213494ebad09f8e52c782153842708b78f90fa178c06e9e3` |
| Runtime template | 13,125 bytes; SHA-256 `8fbc85b5bac4586fdb4fc432284f9c38d12ed3966b2de5630f9d4c80973dcce7`; 11,451 bytes EIP-170 headroom |
| [`test_ledger_action_block.py`](../../../../tests/data/test_ledger_action_block.py) | Git blob `800988b23656e47287b5ea752b1f46dd37f169bc`; SHA-256 `5d631ef7e6e97f31367222a74b150f829330756f8ce34765ba2b6d755b3b9b23` |
| [Teller action-block test](../../../../tests/core/teller/test_teller_action_block.py) | Git blob `25b249342e7edc9efa30da50a9f5cdee8810857a`; SHA-256 `974ac5f7bb47185f29ad4f57e1db91ec0d852ae6f9bf3b13112f48ad72a3741f` |
| [Robinhood profile test](../../../../tests/deployment_profiles/test_ledger_robinhood_profile.py) | Git blob `8c946bab5b5a867a9d0e68f457bf0f6d7a632d21`; SHA-256 `1df761c09b0f1d9f0dcc3ffcc4b6281437978a01ceef6a96e5bbc3417f3f2ab2` |
| [Artifact-bundle test](../../../../tests/deployment_profiles/test_ledger_artifact_bundle.py) | Git blob `7b7e89750576d9e7c6ceab44b14a96737c1ca91a`; SHA-256 `0645965c6a5b8df67545a59ca69f414c381e9e2621f1901f11d499ed3e45ad5c` |

Current tests cover exact 32-byte success; 33-, 64-, and 96-byte oversized
returns; typed-call, truncation, and native-fallback mutants; both
`checkAndUpdateLastTouch` selectors; and expanded `lastTouch` behavior across
users, native/ArbSys identities, trusted deposits, housekeeping, rollback, and
composition. This closes the older return-shape, dual-selector, and
`depositFromTrusted` evidence gaps. The remaining deployment gap is an actual
authorized Robinhood deployment/migration path and live-network proof, not a
local source-test gap. No behavioral suite was rerun for this documentation-only
refresh.

## Reviewed implementation snapshot

| Item | Reviewed identity or status |
| --- | --- |
| Production source | [`contracts/data/Ledger.vy`](../../../../contracts/data/Ledger.vy) |
| Originating implementation | `ed10d4d13fb22c2d00ad2dc06b4faece1e2629f3` |
| Originating parent | `db5e589e13bc39002a345d70cb9d9a38eb13fd67` |
| Originating tree | `f50070b2819d04fe6c4d328e9a682adf8c3f115b` |
| Complete reviewed S5 integration | `81478fe33dfa47a8e135682a047b64949650cb29` |
| Reviewed branch baseline | `rh` at `cca60bb85c772c977bb9fb62c1c6c5252c3a1438` |
| Reviewed baseline tree | `161fb828f3bbf4cb12596a5dfaf6c9bf1e153381` |
| Review date | 28 July 2026 |
| Current/origin source SHA-256 | `6bd731a6ce9084de213494ebad09f8e52c782153842708b78f90fa178c06e9e3` |
| Pre-change source SHA-256 | `00d86847273621857b80701be5faf7ca88ff9505f68671d5b6ab3c8b4ec972e0` |
| Committed ABI SHA-256 | `c6fc1c410e13f144ae9e9d1853378d476fa578211b08f67b23f80c2075bc415f` |
| Source integration status | Integrated into the reviewed `rh` history |
| Deployment/activation status | Not established by this record; release work remains |

The current Ledger is byte-identical to the production source introduced by
`ed10d4d…`. Later reviewed documentation and tests are assessed separately and
are not attributed to that original 41-insertion, 6-deletion source commit.

## Direct answers for the owner

### Why does Ledger use `raw_call` instead of a normal typed Vyper call?

Pinned Vyper `0.4.3+commit.bff19ea2` treats the ABI size for a typed static
`uint256` return as a **minimum**. Its generated path asserts
`returndatasize >= 32`, copies/decodes the first word, and tolerates trailing
bytes. The rejected candidate called
`ArbSys(0x64).arbBlockNumber()` through a typed interface; a controlled
implementation returned two words, `777` and `888`, and the caller accepted
the response as `777`.

The current helper at
[`Ledger.vy:211-222`](../../../../contracts/data/Ledger.vy#L211-L222) needs a
stronger property because this value defines a privileged security bucket. It
captures up to 65 bytes, requires **exactly** 32, and only then decodes the
word. That rejects missing, short, dynamic-shaped, and oversized responses
that a typed call could accept.

This is proven behavior of the pinned Vyper version, not a universal ABI rule.
The Solidity ABI defines how values are encoded; it does not require every
caller wrapper to reject harmless trailing returndata.

### Why is Arbitrum-specific code inside the shared Ledger?

The change was the smallest safe way to preserve one forward accounting source
while supporting the only two action-block semantic families then required:

```text
zero address -> native EVM block.number
exact 0x64   -> ArbSys child-chain block identity
anything else -> reject construction
```

That choice avoids copying roughly 900 lines of state-bearing accounting into
`LedgerRh.vy`, and avoids adding a provider deployment, address, runtime hash,
and call boundary for a two-mode problem. It also makes the trusted source set
fully enumerable in one source file.

The tradeoff is real: `ACTION_BLOCK_SOURCE` is not a generic provider
abstraction. It is an address-shaped two-mode discriminator, and the shared
Ledger now knows the ArbSys address and selector. The design is technically
sound and appropriate as the smallest initial-release patch, but it should not
be presented as the final multi-chain abstraction.

### Do I recommend changing `Ledger.vy` again before the initial release?

**No production-source refactor is recommended before the initial Robinhood
release.** A provider or chain-specific Ledger would add fresh audit and
deployment risk without serving a third concrete semantic family.

**I do recommend changes outside Ledger source.** The exact `0x64` deployment
path, immutable-bound artifact proof, native-profile policy, current
Robinhood/ArbOS qualification, monitoring, and several mutation-sensitive
tests should be completed as described in
[Recommended changes](#recommended-changes).

## Executive verdict

| Question | Independent conclusion |
| --- | --- |
| Is the current implementation technically sound? | Yes |
| Does it preserve the same-execution-block policy? | Yes, under native semantics or the approved ArbSys ABI and truthful system behavior |
| Is the raw call justified? | Yes; it enforces an exact response shape the rejected typed Vyper 0.4.3 call did not |
| Is `ACTION_BLOCK_SOURCE` a real generic provider? | No; it is a narrow two-mode discriminator |
| Is this the best abstract multi-chain design? | No |
| Is it the smallest safe patch for the current two modes? | Yes |
| Should it be replaced by `LedgerRh.vy` before release? | No; the full-source drift risk is greater than the isolation benefit |
| Should it be replaced by a provider before release? | No, absent a real third source family |
| Is there a release-blocking Ledger runtime defect? | None identified |
| Is there release-blocking surrounding work? | Yes: deployment binding, artifact proof, real-network qualification, and operational controls |

## Before the change: the failure being corrected

### Original guard semantics

The original guard used `block.number`:

```text
if shouldCheck:
    require lastTouch[user] != block.number

lastTouch[user] = block.number
```

The exact policy was always asymmetric:

- every successful Teller housekeeping call writes `lastTouch`;
- only checked higher-risk actions assert inequality;
- an unchecked lower-risk touch therefore arms a later checked action;
- a checked action followed by an unchecked touch can succeed, but another
  checked action in the same identity rejects;
- each user has an independent mapping key;
- Underscore-classified users skip equality but still write;
- Teller-only authority, pause state, and account locking are independent
  controls; and
- any enclosing revert restores the previous `lastTouch`.

The current guard and write ordering are visible at
[`Ledger.vy:233-248`](../../../../contracts/data/Ledger.vy#L233-L248).

### Why the policy is “same actual execution block”

The property is:

> For a guarded user, a checked action must reject after any prior successful
> housekeeping touch in the same actual execution block.

It is not a minimum delay, generic rate limit, timestamp window, ancestor-block
epoch, monotonic sequence requirement, oracle-freshness rule, or complete
flash-loan defense. A different child block is allowed even if little time has
elapsed; an equal execution-block identity rejects even if wall-clock time has
advanced.

This narrow definition explains why timestamps and elapsed-time rules are poor
substitutes: they would change both the policy and its failure modes rather
than port the existing equality guard.

### Why inherited `block.number` fails on the intended chain family

As checked on 28 July 2026, Robinhood's official documentation describes
Robinhood Chain as an Arbitrum Chain running Nitro. Offchain Labs documents
that, inside an Arbitrum contract, `block.number` identifies an approximate
first non-Arbitrum ancestor block, while RPC receipts and ArbSys expose child
block numbers. A single parent block can contain multiple child blocks.

Concretely:

```text
child execution block:  9100  9101  9102  9103
EVM block.number:       5000  5000  5000  5000
```

With the old source, an unchecked touch in child block 9100 could reject a
checked action in child block 9103. That is broader than “same actual
execution block.”

Primary current sources:

- [Robinhood full-node documentation](https://docs.robinhood.com/chain/run-a-full-node/)
- [Arbitrum block-number documentation](https://docs.arbitrum.io/arbitrum-essentials/arbitrum-vs-ethereum/block-numbers-and-time)
- [Arbitrum precompile reference](https://docs.arbitrum.io/arbitrum-essentials/precompiles/reference)
- [Pinned ArbSys interface](https://github.com/OffchainLabs/nitro-precompile-interfaces/blob/e7e6566ae5b0efa0ad4d779138f64ead11928c66/ArbSys.sol)

No live RPC was used. Official documentation establishes the expected
protocol family, not the behavior of a particular future deployment. Receipt
agreement and topology remain deployment qualifications.

### Why not disable `shouldCheckLastTouch`?

Setting it to false would preserve writes but remove equality rejection for
ordinary higher-risk users. That does not adapt the security property; it
deletes it. The owner rejected that configuration-only alternative.

## Exact production delta and call flow

The originating source delta is exactly:

```text
git diff \
  ed10d4d13fb22c2d00ad2dc06b4faece1e2629f3^..ed10d4d13fb22c2d00ad2dc06b4faece1e2629f3 \
  -- contracts/data/Ledger.vy
```

It is one file, 41 insertions and 6 deletions.

| Source area | Before | After | Rationale |
| --- | --- | --- | --- |
| Constant/immutable | No source selection | Fixed `ARB_SYS` and public immutable `ACTION_BLOCK_SOURCE` | Bind the identity mode at construction |
| `lastTouch` description | “block number” | “action-block identity” | Record its chain-dependent domain |
| Constructor | Two arguments | Third source argument, strict allowlist, immutable write, ArbSys probe | Reject unsupported or malformed deployments |
| ArbSys helper | Absent | Fixed selector, static raw call, 65-byte ceiling, exact-32 assertion | Enforce approved return shape |
| Identity helper | Absent | Native-zero or ArbSys dispatch | Centralize the selected domain |
| Equality/read-write | Direct `block.number` | One selected `actionBlock` value | Compare and write the same execution identity |

No unrelated debt, auction, points, rewards, lock, bond, or pool-debt
accounting changed.

### Complete policy flow

```text
protocol action
  -> Teller entry point
  -> Teller._performHousekeeping(isHigherRisk, user, updateDebt, addys)
      -> MissionControl.shouldCheckLastTouch()
      -> classify user as Underscore wallet/vault
      -> shouldCheck = enabled && isHigherRisk && !isUnderscore
      -> Ledger.checkAndUpdateLastTouch(user, shouldCheck)
          -> require caller is current Teller
          -> require Ledger is not paused
          -> read selected action-block identity
          -> if shouldCheck: require lastTouch[user] != identity
          -> write lastTouch[user] = identity
          -> require account is not locked
      -> update price snapshot
      -> optionally update debt
  -> later enclosing effects or return
```

Teller's implementation is at
[`Teller.vy:973-1005`](../../../../contracts/core/Teller.vy#L973-L1005).
Because EVM state changes are transactional, a later failure—including the
locked-account check after the write—rolls back the touch.

### Route and policy map

The six checked/higher-risk families are:

1. `withdraw`;
2. `withdrawMany`;
3. `rebalance`;
4. `borrow`;
5. `claimFromStabilityPool`; and
6. `claimManyFromStabilityPool`.

Deposits, repayments, and other lower-risk housekeeping calls are unchecked
but still write, so they can arm a later checked action. `depositFromTrusted`
is the exception: it passes `_shouldPerformHouseKeeping=False`, so the deposit
itself does not touch Ledger. Some trusted producers perform separate
housekeeping afterward.

For an Underscore-classified user, only the equality assertion is removed.
Teller still calls Ledger and Ledger still writes `lastTouch`.

`Teller.performHousekeeping` accepts caller-supplied risk, user, debt-update,
and optional Addys values from a valid Ripe address. Tests prove that this
broad boundary can select a victim/risk classification and alternate Ledger,
and that later failure rolls the call back. It is a separate pre-existing
Teller authorization/griefing concern, not introduced or solved by Ledger S5.

## Selected source, constructor, and runtime behavior

The implementation at
[`Ledger.vy:130-131`](../../../../contracts/data/Ledger.vy#L130-L131) declares:

```vyper
ARB_SYS: constant(address) = 0x0000000000000000000000000000000000000064
ACTION_BLOCK_SOURCE: public(immutable(address))
```

The constructor at
[`Ledger.vy:189-205`](../../../../contracts/data/Ledger.vy#L189-L205) supports:

| Input | Mode | Constructor behavior |
| --- | --- | --- |
| Zero | Native | Stores zero; makes no source call |
| Exact `0x64` | ArbSys | Stores `0x64`; immediately probes `arbBlockNumber()` |
| Any other value | Unsupported | Reverts |

### Native mode

```text
construct with zero
  -> allowlist succeeds
  -> immutable is zero
  -> no external source call

housekeeping
  -> _getActionBlock()
  -> block.number
  -> equality check if requested
  -> lastTouch write
```

This supports ordinary EVM chains only when native `block.number` is the
desired execution-block identity.

### ArbSys mode

```text
construct with exact 0x64
  -> allowlist succeeds
  -> immutable is 0x64
  -> fixed selector is called
  -> call must succeed and return exactly 32 bytes

every housekeeping call
  -> repeat the same fixed exact-length source read
  -> equality check if requested
  -> lastTouch write
```

Missing code, revert, short data, oversized data, or incompatible response
aborts construction. The same failures at runtime abort housekeeping before a
successful `lastTouch` update; there is no native fallback.

Constructor validation is useful but not permanent proof. A system-contract
outage or chain upgrade can still break runtime reads. That can block
repayment, liquidation, and other actions that require housekeeping. The
current operational response is pause and containment; there is no in-place
source recovery.

The source is immutable because a setter would allow governance to change the
meaning of stored `lastTouch` values and the guard bucket under live state.

## Raw-call and returndata analysis

The exact helper is:

```vyper
@view
@internal
def _getArbActionBlock() -> uint256:
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

The selector for `arbBlockNumber()` is `0xa3b1b31d`; the official interface
returns `uint256`. Offchain Labs currently documents ArbSys at fixed address
`0x0000000000000000000000000000000000000064` and describes the result as the
current L2 block number.

### Typed-call evidence

For a static ABI type requiring one word, the pinned Vyper external-call
generator computes a minimum return size and emits a greater-than-or-equal
returndata assertion. A controlled 64-byte return:

```text
word 1 = 777
word 2 = 888
```

was accepted by the rejected typed implementation as `777`. The second word
was ignored. The behavior was established from the Vyper 0.4.3 compiler source,
generated behavior, and a disposable probe.

This distinction matters because `arbBlockNumber()` is not ordinary
application data: it selects which protocol actions are considered to share a
security identity. Accepting an ambiguous response weakens the trust boundary
and makes malformed or incorrect system code look compatible.

### Why 65 bytes?

- `Bytes[32]` is insufficient: a longer response can be truncated to 32 and
  become indistinguishable from a canonical response.
- `Bytes[33]` is sufficient as a one-byte sentinel for all overlong data.
- `Bytes[65]` additionally preserves a complete common two-word/64-byte
  malformed response plus one sentinel byte.

The selected 65-byte size is conservative, not uniquely necessary.
`raw_call(max_outsize=65)` returns an observed length of
`min(65, actualReturndataSize)`. Responses longer than 65 are captured as 65
and therefore fail the exact-32 assertion.

### Exact failure behavior

| Source behavior | Observed result |
| --- | --- |
| No code/missing precompile | EVM call succeeds with empty data; length assertion rejects |
| Call revert/failure | `revert_on_failure=True` propagates failure |
| Empty data | Reject |
| 1–31 bytes | Reject |
| Exactly 32 bytes | Decode as `uint256` |
| 33 bytes | Reject |
| 64 bytes | Capture 64; reject |
| More than 64 bytes | Capture at most 65; reject |
| Dynamic-shaped data | Reject by length unless exactly 32; an exact word decodes as some `uint256` |

After the length assertion, `abi_decode(..., uint256)` is shape-safe because
every 32-byte word is a valid unsigned integer.

`is_static_call=True` prevents state changes anywhere in the source call tree.
`revert_on_failure=True` prevents a failed read from being converted into an
alternate value. Both make the security intent explicit even though static
context and call-success policy are separate EVM concerns.

The helper proves response shape, not truth. An incorrect system implementation
at `0x64` can return a well-formed false value. The address and behavior are
ArbOS protocol conventions implemented by the chain, not protections Ledger
can enforce against a malicious chain. Future chain governance or an ArbOS
upgrade can change the implementation; deployment qualification and monitoring
remain required.

A precompile/system-contract call uses the ordinary EVM call interface from
Ledger's perspective. Its special trust comes from chain implementation and
governance, not from stronger ABI semantics.

## Equality-only semantics

Ledger rejects only:

```text
lastTouch[user] == currentActionBlock
```

It deliberately permits:

```text
750 -> 749
```

This preserves the original equality property. It does not ask Ledger to
diagnose source progress.

A regressed but different value can allow two actions that a stable identity
would have grouped together. Conversely, requiring `new > old` could turn a
reorganization, chain anomaly, or system-contract regression into indefinite
protocol denial of service.

Official Nitro documentation describes child block numbers as sequentially
updating, but Ledger does not independently enforce that chain property.
Classification: **sound equality policy with an accepted residual risk and an
active monitoring dependency**, not a current source defect.

## Architecture and alternatives

### What abstraction exists today?

`ACTION_BLOCK_SOURCE` sounds more generic than it is. Its only valid values are
zero and the exact address that selects the embedded ArbSys helper. It is a
two-mode discriminator stored in an address-shaped immutable.

The design supports:

- ordinary EVM chains whose native `block.number` is the chosen execution
  identity;
- Robinhood and other approved Nitro-compatible chains with ArbSys at `0x64`
  and the expected exact ABI; and
- no other semantic family.

An unsupported future chain fails closed at construction. That is both a
security feature and a portability limitation.

### Comparison table

| Design | Security / fail-closed | Portability / future chains | Audit and constructor complexity | Runtime gas / call surface | Production artifacts / drift | ABI, storage, migration | Operational burden / smallest change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **A. Current shared Ledger** | Fixed allowlist, immutable mode, exact-length ArbSys call, no fallback | Native and exact ArbSys only | Small constructor branch; chain code remains visible in Ledger | No external call in native mode; one system call per housekeeping in ArbSys mode | One forward source; deployed runtimes differ by immutable/version | Constructor changes to three args; persistent layout preserved | Lowest current burden and smallest sufficient change |
| **B. Separate `LedgerRh.vy`** | Strong chain isolation if variants remain exact | Explicit artifacts can serve each chain | Every accounting fix and audit must cover both complete sources | Same native/ArbSys runtime behavior per variant | Two roughly 900-line sources; high missed-fix and canonical-source risk | ABI/layout can start aligned but may drift; migration evidence doubles | Clear locally, expensive permanently |
| **C. Immutable provider contract** | Can be narrow, immutable, code-hash pinned, and fail-closed; misconfiguration/provider compromise adds risk | Best runtime extensibility | Provider deployment, constructor verification, code hash, provider tests | Extra call frame in non-native mode; native provider call would be unnecessary | Shared Ledger plus provider artifacts | Ledger constructor/ABI changes again; provider versioning enters migrations | Conceptually clean once a third family justifies it |
| **D. Internal/module or generated adapter** | Can isolate chain logic at compile time without a mutable runtime source | Strong if build variants are tightly controlled | Vyper module initialization/storage composition and generated-source provenance require proof | No extra provider call | Shared core but multiple compiled entry artifacts | Must prove identical storage/ABI across variants | Promising future direction, not a low-risk pre-release refactor |
| **E. Generic address + selector** | Exact length can be enforced, but semantic allowlist disappears | Superficially broad | Constructor becomes a programmable call description | One arbitrary external call | One source, many potentially unsafe deployments | ABI/layout manageable; deployment configuration becomes security-critical | Too permissive for current needs |
| **F. `chain.id` dispatch** | Hardcoded branches can fail closed, but wrong/forked deployments select hidden behavior | Every new chain requires source release | Source grows chain cases and fork assumptions | Efficient runtime branch | One source with accumulating chain logic | Constructor simpler; source/version migration burden grows | Convenient initially, brittle over time |

### Independent judgment on `LedgerRh.vy`

A separate Robinhood artifact would improve:

- conceptual clarity;
- visual chain isolation;
- local source readability; and
- containment of ArbSys-specific failure to the Robinhood artifact.

Those benefits do not justify copying the full Ledger. Ledger stores
participation, debt, borrower indexes, points, rewards, auctions, locks,
contributors, bonds, bad debt, and pool debt. Duplicating that state-bearing
source creates a permanent obligation to:

- apply every accounting/security fix twice;
- prove ABI and storage alignment twice;
- keep fixtures and migration evidence aligned;
- detect source drift before deployment; and
- decide which variant is canonical.

Live Base already runs older bytecode, but versioned deployed-bytecode
divergence is different from maintaining two forward source forks.

Inheritance, a Vyper module, or generated entry artifact could isolate the
adapter without duplicating all accounting. Under Vyper 0.4.3, that still
requires careful initialization, export, storage-layout, compiler-artifact,
and dual-build proof. It is the more credible future correction if a real
third family appears.

### Independent judgment on a provider

A provider is conceptually cleaner:

```text
Ledger -> ActionBlockProvider.getActionBlock()
```

It can isolate ArbSys, support additional semantics, and keep Ledger
chain-neutral. But for the present modes:

```text
current:  Ledger -> fixed ArbSys 0x64
provider: Ledger -> configured provider -> fixed ArbSys 0x64
```

The second form adds an address, deployment, runtime hash, call frame,
liveness dependency, constructor proof, gas cost, and monitoring target
without adding current capability. Native mode should not pay an external-call
cost merely for architectural symmetry.

If adopted later, the provider should be immutable, narrowly typed,
non-upgradeable unless separately justified, exact-length validating, and
code-hash pinned at deployment. Ledger should still avoid arbitrary selectors
or native fallback.

### Why the other rejected choices remain rejected

- **`chain.id` branching:** convenient but hides source behavior behind a
  deployment environment and grows with each chain/fork.
- **Mutable provider:** can redefine the meaning of stored identities after
  deployment.
- **Arbitrary provider/selector:** converts a small allowlist into a semantic
  configuration surface.
- **Native fallback:** silently weakens child-block identity after source
  failure.
- **Timestamp:** changes equality buckets and introduces sequencer-time
  assumptions.
- **Cached value:** needs a trusted refresh mechanism and can become stale.
- **Disable guard:** removes the selected protection.
- **Migrate Base for parity:** risks non-enumerable, state-bearing accounting
  solely to align bytecode.

## Shared source, Base divergence, and migration compatibility

The policy is:

- one forward canonical Ledger source;
- existing Base remains permanently on its older deployed bytecode;
- fresh Robinhood deployment uses the revised source with `0x64`; and
- a future native deployment uses the revised source with zero.

Permanent live-bytecode divergence is therefore already accepted. It is
coherent versioning because old live state stays on its reviewed artifact while
new deployments use a later version. The awkward part is that the forward
source embeds an ArbSys adapter and changes constructor arity.

The historical Base migration at
[`1004_Ledger.py:10-14`](../../../../migrations/base-mainnet/1004_Ledger.py#L10-L14)
passes only RipeHq and Defaults. The current source requires a third argument.
If migration tooling resolves the historical contract name to current source,
that replay fails.

Adding zero to the historical migration would not be an honest replay: it
would deploy the new creation/runtime code under an old migration identity.
The coherent policy is:

1. preserve the historical migration unchanged;
2. bind historical replay to the original source or compiled artifact;
3. use a new migration for every new native deployment and pass zero
   deliberately; and
4. use the separately controlled Robinhood deployment path to pass exact
   `0x64`.

Keeping one forward source still reduces long-term accounting drift even
though deployed bytecode differs. The canonical source for future native
chains is the current shared `Ledger.vy`, deliberately constructed in zero
mode—not the historical two-argument artifact and not an implied
`LedgerRh.vy`.

## Test invariant matrix

### Focused Ledger source tests

All named tests below are in
[`test_ledger_action_block.py`](../../../../tests/data/test_ledger_action_block.py).

| Test / lines | Mode and invariant | Expected state/result | Mutation sensitivity | Remaining limit |
| --- | --- | --- | --- | --- |
| [`native source getter`, 79](../../../../tests/data/test_ledger_action_block.py#L79) | Native getter and native `block.number` | Getter is zero; stored touch follows native number | Detects calling ArbSys or writing another value in native mode | Fixture, not a real native deployment |
| [`reject non-ArbSys source`, 101](../../../../tests/data/test_ledger_action_block.py#L101) | Constructor allowlist | Every nonzero non-`0x64` source reverts | Detects arbitrary-provider acceptance | Does not test production deployment profile |
| [`constructor failure matrix`, 122](../../../../tests/data/test_ledger_action_block.py#L122) | Missing/revert/short/33/64/96/incompatible ArbSys | Construction reverts | Detects probe removal; 64-byte case detects rejected typed call | Controlled code at `0x64` |
| [`constructor success/getter`, 132](../../../../tests/data/test_ledger_action_block.py#L132) | Exact ArbSys response | Construction succeeds; immutable getter is `0x64` | Detects wrong immutable or missing success path | Local double |
| [`ArbSys overrides native`, 141](../../../../tests/data/test_ledger_action_block.py#L141) | Native advances while child identity is held | Same child identity rejects | Detects native fallback | Does not prove live chain topology |
| [`equality-only`, 165](../../../../tests/data/test_ledger_action_block.py#L165) | Same, next, then `750 -> 749` | Equal rejects; different/decreasing succeeds | Detects monotonic comparison | Accepts monitored source-regression risk |
| [`low/high ordering`, 180](../../../../tests/data/test_ledger_action_block.py#L180) | Low→high and high→low→high | Low arms high; second high rejects | Detects loss of unchecked writes or wrong ordering | Direct Ledger calls, not every enclosing route |
| [`user isolation`, 201](../../../../tests/data/test_ledger_action_block.py#L201) | Two users in one child identity | Each mapping key is independent | Detects global rather than per-user guard | Does not model shared wallet ownership |
| [`runtime source failures`, 233](../../../../tests/data/test_ledger_action_block.py#L233) | Missing/revert/malformed after construction | Revert, no fallback, no partial write | Detects native fallback and write-before-source | Local system-code replacement |
| [`locked-account rollback`, 256](../../../../tests/data/test_ledger_action_block.py#L256) | Native and ArbSys | Lock rejects after tentative write; state rolls back | Detects reordered/removed lock enforcement | Direct Ledger path |
| [`pause/Teller authority`, 286](../../../../tests/data/test_ledger_action_block.py#L286) | Both modes | Unauthorized or paused call reverts without touch | Detects weakened authority/pause | Teller registry is fixture-controlled |
| [`zero-address user`, 322](../../../../tests/data/test_ledger_action_block.py#L322) | Both modes | Zero mapping key remains writable | Detects newly added user-address rejection | Preserves existing behavior, not endorsement |

### Teller and composed-route tests

| Test / file | Route and policy | State/rollback proof | Mutation sensitivity / gap |
| --- | --- | --- | --- |
| [`classification matrix`](../../../../tests/core/teller/test_teller_action_block.py#L31) | All Teller housekeeping callsites, user identity, risk and debt flags | Static callsite contract remains exact | Strong against reclassification; source-shape evidence |
| [`external housekeeping`](../../../../tests/core/teller/test_teller_action_block.py#L80) | Valid/invalid caller, selected victim/risk/Addys, zero user | Touch/write or complete rollback | Detects authority and propagation changes; also exposes separate broad-caller concern |
| [`Underscore writes`](../../../../tests/core/teller/test_teller_action_block.py#L143) | Equality exemption only | Repeated call succeeds but touch updates | Detects skipping the entire Ledger call |
| [`deposit arms`](../../../../tests/core/teller/test_teller_deposit.py#L343) | Lower-risk deposit | Repeats; arms current identity | Detects removal of unchecked write |
| [`deposit then withdrawal`](../../../../tests/core/teller/test_teller_withdraw.py#L90) | Low-risk then checked | Withdrawal rejects in same identity | Directly proves arming across routes |
| [`checked withdrawal`](../../../../tests/core/teller/test_teller_withdraw.py#L130) | High-risk twice | Second rejects; economic state rolls back | Detects missing equality guard |
| [`withdrawMany`](../../../../tests/core/teller/test_teller_withdraw.py#L373) | Batch withdrawal in held child identity | Second batch rejects | Detects missing batch guard |
| [`rebalance rollback`](../../../../tests/core/teller/test_teller_rebalance.py#L83) | Guard occurs after both legs | Later rejection restores all legs | Sensitive to transaction ordering/atomicity |
| [`borrow ordering`](../../../../tests/core/creditEngine/test_credit_borrow.py#L61) | Checked before credit effects | Second action rejects before mint/debt changes | Detects guard movement after credit effects |
| [`repay ordering`](../../../../tests/core/creditEngine/test_credit_repay.py#L58) | Low-risk repay between checked actions | Repay succeeds and rearms; later checked rejects | Detects changing repay classification/write |
| [`Stability claim`](../../../../tests/vaults/modules/test_stab_vault_claims.py#L450) | Checked single claim after effects | Second claim rejects and rolls back | Detects missing post-claim guard/rollback |
| [`claimMany`](../../../../tests/vaults/modules/test_stab_vault_claims.py#L717) | Checked batch claim | Second same-child call rejects | Detects missing batch classification |
| [`external-route rollback`](../../../../tests/core/deleverage/test_deleverage_swap_collateral.py#L187) | Integrated caller reaches external housekeeping | Later failure restores all earlier effects | Cited only for Ledger guard coverage; Deleverage itself is out of scope |

Existing baseline tests in
[`test_ledger.py:1484-1653`](../../../../tests/data/test_ledger.py#L1484)
also preserve first use, same/next native block, user isolation, pause,
authority, zero user, unchecked repeats, and mixed modes.

### Mutation conclusions and gaps

- Replacing the raw helper with the original typed call makes the malformed
  64-byte constructor case fail to reject, so the test is mutation-sensitive.
- Adding native fallback is detected by the held-child-identity and runtime
  failure tests.
- Allowing arbitrary providers is detected by the constructor allowlist test.
- Removing the constructor probe is detected by constructor failure cases.
- Changing equality to monotonic comparison is detected by `750 -> 749`.
- Locked-account and later-route tests detect observable rollback/order
  changes.

Remaining evidence gaps after later integrated hardening:

- no authorized Robinhood migration/deployment execution proves the final
  creation arguments and deployed runtime at exact `0x64`;
- no external-consumer test proves frontend/indexer interpretation of
  `lastTouch`;
- no live-network execution was authorized;
- a separate `LedgerRh.vy` could be silently undertested unless every suite is
  explicitly parameterized over both artifacts.

## ABI, storage, artifacts, gas, and migration impact

### ABI and storage

The semantic ABI delta is:

- constructor changes from two arguments to three; and
- `ACTION_BLOCK_SOURCE() -> address` is added.

The generated and committed ABI are byte-identical and contain 92 entries.
Persistent storage remains 37 entries in the same order; `lastTouch` stays in
its existing slot. `ACTION_BLOCK_SOURCE` is immutable code data at offset 96,
not a new persistent slot.

The existing optional `_mc` argument to `checkAndUpdateLastTouch` predates S5
and remains unused. Vyper therefore exposes:

| Signature | Selector |
| --- | --- |
| `checkAndUpdateLastTouch(address,bool)` | `0x222a390e` |
| `checkAndUpdateLastTouch(address,bool,address)` | `0xec74f007` |

Teller declares and calls only the two-argument selector. Both Ledger selectors
execute the same Teller-gated body. Removing `_mc` now would be an unrelated
ABI change.

`lastTouch(address)` retains the same getter ABI but now means “the
Ledger-selected action-block identity”: native EVM block number in zero mode,
ArbSys child-block number in `0x64` mode. No in-repository runtime consumer
outside Ledger reads it; external consumer assumptions remain a release
confirmation item.

### Reproduced artifact identities

| Artifact | Reviewed result |
| --- | --- |
| Ledger source | `6bd731a6ce9084de213494ebad09f8e52c782153842708b78f90fa178c06e9e3` |
| Committed/generated ABI | `c6fc1c410e13f144ae9e9d1853378d476fa578211b08f67b23f80c2075bc415f` |
| Persistent storage subobject | 37 entries; canonical SHA-256 `bb19201a6bf4f4ef2649e5054e0fce6a53f007af4e4a004365edcc245c7e45a6` |
| Creation bytecode | 13,730 bytes; SHA-256 `a31f400f5364f8dbbd22b79bea2557f7f3dd57538eb659c06a21e18e9d8e9127` |
| Runtime template | 13,125 bytes; SHA-256 `8fbc85b5bac4586fdb4fc432284f9c38d12ed3966b2de5630f9d4c80973dcce7` |

The runtime template is not a final deployed-runtime identity because
constructor immutables are bound during deployment.

### Historical local gas evidence

These are historical local Boa measurements from the implementation record,
not current Robinhood fee predictions:

| Operation | Pre-change native | Revised native | Revised ArbSys |
| --- | ---: | ---: | ---: |
| Deploy | 2,600,084 | 2,656,927 (`+56,843`) | 2,659,871 (`+59,787`) |
| Unchecked touch | 31,805 | 31,929 (`+124`) | 34,856 (`+3,051`) |
| Checked successful touch | 31,890 | 32,018 (`+128`) | 34,945 (`+3,055`) |

## Residual-risk register

| Risk | Severity | Likelihood | Impact | Mitigation | Release-blocking? |
| --- | --- | --- | --- | --- | --- |
| Robinhood deployment selects zero or lacks an executable path | High | Present gap | Guard uses ancestor identity or deployment cannot proceed | Exact-profile deployment tests, immutable getter, final runtime/manifest proof | **Yes** |
| ArbSys unavailable or malformed after deployment | High availability | Low/unknown | Housekeeping-dependent actions can fail | Constructor probe, runtime fail-closed, monitoring, pause/runbook | Qualification/operations gate |
| Well-formed but false value from `0x64` | High | Low; chain-governance dependent | Wrong security buckets | Official source/version pin, receipt agreement, monitoring | Qualification gate |
| Equality-only regression/anomaly | Moderate | Low/unknown | Different regressed identities may permit actions | Activation proof and monitoring | No if monitoring gate closes |
| External consumer assumes `lastTouch == EVM NUMBER` | Moderate | Unknown | Analytics/indexing mismatch | Document domain; consumer-owner sign-off | Conditional |
| Historical Base migration loads current three-arg source | Moderate operational | Certain under that resolution model | Replay fails or is misrepresented | Version-pin historical artifact; new migrations for new deployments | Blocks replayability claims |
| Broad external Teller housekeeping parameters | Moderate | Existing/accepted | Valid Ripe caller can select victim/risk/Addys | Registry control, existing tests, separate Teller review | No new Ledger blocker |
| `depositFromTrusted` itself does not arm | Low/policy | Expected and covered by current composition tests | Trusted deposit alone does not block a later checked action | Preserve current policy regression | No |
| Optional unused `_mc` selector | Low | Certain | ABI complexity/confusion | Preserve now; remove only in versioned cleanup | No |
| Third source family | Architectural | Event-driven | Current Ledger cannot deploy without source change | Trigger adapter/provider decision | No current blocker |

## Recommended changes

The recommendation is deliberately split by authority and urgency. Nothing in
this section changes the already integrated owner decisions by implication.

### Currently required

These are agent-identified release or activation gates, not Ledger source
corrections:

1. **Build the executable Robinhood Ledger deployment path.** It must compile
   the reviewed source, pass exact `0x64`, reject zero and every unsupported
   source in the Robinhood profile, read back the immutable, and stop before
   registration/activation on any mismatch.
2. **Produce a reproducible deployment bundle.** Record commit/tree, source and
   ABI hashes, Vyper/settings, compiler input, constructor encoding, creation
   bytecode, final immutable-bound runtime, `ACTION_BLOCK_SOURCE()`, and
   manifest/registry identity.
3. **Define native and historical replay policy.** Keep the historical
   two-argument Base migration unchanged and bind replay to its original
   source/artifact. Any future native deployment needs a new migration that
   explicitly passes zero.
4. **Complete real-network qualification under separate authorization.**
   Confirm the current Nitro/ArbOS family, ArbSys address/selector/return shape,
   receipt agreement, same-child/different-child behavior, and repeated native
   `block.number` topology. No live RPC is authorized by this document.
5. **Complete monitoring and incident response before activation.** Detect
   source-call failures, identity disagreement/regression, code/version drift,
   and abnormal housekeeping reverts. Define pause, diagnosis, repayment and
   liquidation assessment, recovery evidence, and unpause authority.
6. **Confirm `lastTouch` consumers.** Frontend, subgraph, indexer, analytics,
   and monitoring owners must treat it as a deployment-selected action-block
   identity rather than universally as the EVM `NUMBER` opcode.

The missing exact-`0x64` production binding is the most important current
Ledger-associated release gap.

### Recommended hardening

These improve assurance but do not identify a defect in the current runtime:

- retain the current `depositFromTrusted`, dual-selector, and deployment-profile
  mutation tests for zero/wrong source, removed constructor
  probe, typed-call substitution, `max_outsize=32`, native fallback, monotonic
  comparison, and omitted immutable/runtime assertions;
- automate source/ABI/compiler/layout/runtime-size and immutable-bound artifact
  comparisons for every future Ledger change;
- keep inventory counts snapshot-labeled: the S5 record's 69 is historical,
  while the reviewed current inventory suite collects 95; and
- document monitoring thresholds and expected chain-topology behavior with
  dated primary sources.

### Parked by owner

These subjects are not current Ledger release blockers and are not expanded
into Ledger recommendations:

- further Deleverage work beyond the integrated composition evidence;
- every CCIP workflow; and
- zero-backing settlement, loss allocation, and bad-debt policy.

The integrated Deleverage tests remain relevant only as guard-rollback consumer
evidence.

### Explicitly not recommended

- Do not refactor `Ledger.vy` before the initial release solely to make the
  source look generic.
- Do not create `LedgerRh.vy` by copying the full state-bearing Ledger.
- Do not add a mutable provider, arbitrary provider address, or arbitrary
  selector.
- Do not add native fallback after an ArbSys failure.
- Do not add `chain.id` dispatch.
- Do not disable the equality guard on Robinhood.
- Do not add monotonicity enforcement without a separate liveness/reorg policy.
- Do not edit the historical Base migration to masquerade as a replay of the
  old artifact.
- Do not migrate the existing Base Ledger merely for bytecode parity.
- Do not remove `_mc` as part of this release; make that a versioned ABI change
  if it is ever undertaken.

### Architecture revisit triggers

Reopen the source boundary when any one of these occurs:

1. a third chain requires neither native `block.number` nor ArbSys `0x64`;
2. ArbSys address, selector, ABI, version, or governance assumptions change;
3. another chain-specific helper would be added to Ledger;
4. native deployments cannot be reproduced under explicit versioning;
5. chain-specific code grows beyond a small auditable adapter;
6. a demonstrated provider requirement outweighs its added call/deployment
   surface; or
7. Vyper module/build support can isolate a common accounting core with proven
   ABI, storage, and initialization equivalence.

At that point, first evaluate a small compile-time/internal adapter with shared
accounting. If that is not safe or practical, use a narrowly typed immutable
provider with code-hash and exact-returndata checks. Fork the complete Ledger
only if the shared accounting core itself can no longer remain canonical.

## Historical versus current evidence

### Historical reviewed evidence

The sealed S5 integration reported:

| Gate | Historical result |
| --- | --- |
| Focused Ledger/Teller action-block suite | 45 passed |
| Dedicated batch cases | 2 passed |
| Targeted regressions | 447 passed |
| Probe suite | 154 passed |
| Inventory suite at that snapshot | 69 passed |
| Complete serial suite | 3,044 passed, 142 deselected |
| Failures/skips/xfails | Zero |
| Compiler | `Vyper 0.4.3+commit.bff19ea2` |
| Persistent layout | 37 entries, unchanged |
| ABI | Committed/generated parity |

These are historical integration results. This harmonization revision did not
rerun the complete repository suite.

### Independently reproduced audit evidence

The independent read-only Ledger audit:

- verified current source identity against the originating production commit;
- reconstructed the 41-insertion, 6-deletion source delta;
- inspected Vyper 0.4.3's minimum-return-size typed-call behavior;
- reproduced the typed 64-byte acceptance and raw exact-length rejection;
- confirmed ABI, selectors, persistent storage count, immutable offset, and
  bytecode identities;
- ran the focused action-block suite successfully;
- confirmed no in-repository external runtime consumer of `lastTouch`;
- confirmed Boa test isolation; and
- ran the reviewed-current inventory suite with `95 passed`.

The 95-test current result does not rewrite the historical 69-test S5 record.
This documentation-only harmonization did not rerun those tests.

## Research and provenance

The design history separates into:

1. **Initial analysis:** repeated ancestor block numbers were identified and
   the same-execution-block property was defined.
2. **Owner decisions:** preserve the guard, keep native mode, add ArbSys child
   identity, fail closed, maintain one forward source, and leave Base state
   unmigrated.
3. **Rejected candidate:** typed Vyper accepted a two-word response and decoded
   only its first word.
4. **Corrected production source:** fixed selector, exact response length,
   constructor probe, immutable discriminator, and no fallback.
5. **Gate 1/Gate 2:** action classification, mutation-sensitive behavior,
   ABI/storage/artifacts/gas, inventory, and regression evidence were reviewed.
6. **Integration:** the production Ledger source remained byte-identical
   through the later reviewed S5 integration and current baseline.
7. **Unperformed release work:** final deployment binding, real-network
   qualification, immutable-bound artifact/manifest identity, monitoring,
   incident response, and activation.

### Time-sensitive Robinhood and ArbOS facts

As checked on 28 July 2026:

- Robinhood documentation says the chain runs Arbitrum Nitro and lists ArbOS
  profile `61`;
- Offchain Labs documents ArbSys at `0x64`;
- `arbBlockNumber()` returns the current L2 block number; and
- the pinned ArbSys interface defines `arbOSVersion()` as `55 +` the Nitro
  ArbOS profile, making the historical expected raw value `116`.

Ledger does **not** call `arbOSVersion()` and has no runtime dependency on
`116`. Profile `61`, raw value `116`, Nitro image/version, and current chain
governance are deployment-qualification facts, not permanent constants. They
must be revalidated against current official documentation and separately
authorized live evidence at release time.

## Evidence appendix

### Primary repository records

- [`ledger-guard-security-decision.md`](../ledger-guard-security-decision.md)
- [`ledger-guard-implementation-record.md`](../ledger-guard-implementation-record.md)
- [`track-6-s5-ledger-guard.md`](../track-6-s5-ledger-guard.md)
- [`track-6-s5-checkpoint-0-owner-decision-packet.md`](../track-6-s5-checkpoint-0-owner-decision-packet.md)
- [`shared-block-clock-specification.md`](../shared-block-clock-specification.md)
- [`block-clock-validation-plan.md`](../block-clock-validation-plan.md)
- [`ledger-action-block-testnet-proof.md`](../evidence/ledger-action-block-testnet-proof.md)
- [`ledger-action-block-mainnet-fork.json`](../evidence/ledger-action-block-mainnet-fork.json)
- [`ledger-action-block-testnet-fork.json`](../evidence/ledger-action-block-testnet-fork.json)
- [`Ledger ABI`](../../../../scripts/abis/Ledger.json)
- [`block-clock inventory`](../../../../config/block-clock-inventory.json#L95)
- [`inventory checker`](../../../../scripts/check_block_clock_inventory.py#L110)

### Primary external sources

- [Robinhood Chain full-node documentation](https://docs.robinhood.com/chain/run-a-full-node/)
- [Robinhood Chain overview](https://docs.robinhood.com/chain/)
- [Arbitrum block numbers and time](https://docs.arbitrum.io/arbitrum-essentials/arbitrum-vs-ethereum/block-numbers-and-time)
- [Arbitrum precompile reference](https://docs.arbitrum.io/arbitrum-essentials/precompiles/reference)
- [Pinned ArbSys Solidity interface](https://github.com/OffchainLabs/nitro-precompile-interfaces/blob/e7e6566ae5b0efa0ad4d779138f64ead11928c66/ArbSys.sol)
- [ArbSys Nitro implementation](https://github.com/OffchainLabs/nitro/blob/master/precompiles/ArbSys.go)
- [Vyper 0.4.3 external-call generator](https://github.com/vyperlang/vyper/blob/v0.4.3/vyper/codegen/external_call.py)
- [Vyper 0.4.3 raw-call implementation](https://github.com/vyperlang/vyper/blob/v0.4.3/vyper/builtins/functions.py)
- [Vyper 0.4.3 `raw_call` documentation](https://docs.vyperlang.org/en/v0.4.3/built-in-functions.html#raw-call)
- [Solidity ABI specification](https://docs.soliditylang.org/en/latest/abi-spec.html)
- [EIP-211: returndata buffer](https://eips.ethereum.org/EIPS/eip-211)
- [EIP-214: static-call context](https://eips.ethereum.org/EIPS/eip-214)

### Reproducible read-only commands

```text
git rev-parse HEAD HEAD^{tree}
git rev-parse refs/remotes/origin/rh refs/remotes/origin/rh^{tree}
git show ed10d4d13fb22c2d00ad2dc06b4faece1e2629f3:contracts/data/Ledger.vy |
  shasum -a 256
git diff --numstat \
  ed10d4d13fb22c2d00ad2dc06b4faece1e2629f3^..ed10d4d13fb22c2d00ad2dc06b4faece1e2629f3 \
  -- contracts/data/Ledger.vy
shasum -a 256 \
  contracts/data/Ledger.vy \
  scripts/abis/Ledger.json \
  docs/chains/rh/ledger-guard-implementation-record.md \
  docs/chains/rh/ledger-guard-security-decision.md
PYTHONDONTWRITEBYTECODE=1 python3 -c \
  'import inspect, vyper.codegen.external_call as m; print(inspect.getsource(m._unpack_returndata))'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
  python scripts/check_block_clock_inventory.py --check
```

The exact focused audit command that produced 45 passes was:

```text
env -u BASESCAN_API_KEY -u WEB3_ALCHEMY_API_KEY -u TEST_PRIVATE_KEY \
  -u BASE_MAINNET_RPC_URL -u BASE_SEPOLIA_RPC_URL \
  -u ROBINHOOD_MAINNET_RPC_URL -u ROBINHOOD_TESTNET_RPC_URL \
  -u ROBINHOOD_TESTNET_PRIVATE_KEY -u DEPLOYER_PRIVATE_KEY \
  PYTHONDONTWRITEBYTECODE=1 PYTHON_DOTENV_DISABLED=1 \
  ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. \
  XDG_CACHE_HOME=/private/tmp/ledger-audit.sSYbjV/test-cache \
  TMPDIR=/private/tmp/ledger-audit.sSYbjV/test-tmp \
  /private/tmp/h01-final-review.dL2pqo/candidate/bin/python -c \
  'from boa.interpret import set_cache_dir; set_cache_dir("/private/tmp/ledger-audit.sSYbjV/test-cache/boa"); import pytest; raise SystemExit(pytest.main(["-q","-p","no:cacheprovider","--basetemp=/private/tmp/ledger-audit.sSYbjV/pytest","tests/data/test_ledger_action_block.py","tests/core/teller/test_teller_action_block.py"]))'
```

The exact current-inventory command that produced 95 passes was:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
  XDG_CACHE_HOME=/private/tmp/ledger-feedback-inventory.iqwKxh/cache \
  ETHERSCAN_API_KEY=local-placeholder \
  /private/tmp/h01-final-review.dL2pqo/candidate/bin/pytest \
  -q -p no:cacheprovider \
  --basetemp=/private/tmp/ledger-feedback-inventory.iqwKxh/pytest \
  tests/inventory/test_block_clock_inventory.py
```

Those private audit directories were mode 0700 and removed after use. The
commands are historical reproduction evidence, not authorization to rerun
them or use external RPC.

Facts not independently proven against a live network:

- the code and semantics actually present at `0x64` on a final deployment;
- receipt and ArbSys identity agreement on that deployment;
- repeated ancestor identity across observed Robinhood child blocks;
- topology behavior through upgrades or failover; and
- any deployed Ledger constructor input, runtime, registry entry, or activation
  state.

## Bottom-line owner summary

- **Guarantee:** successful housekeeping uses one immutable identity mode:
  native zero or exact ArbSys `0x64`.
- **Guarantee:** every successful touch writes; only higher-risk,
  non-Underscore actions enforce same-identity rejection.
- **Guarantee:** malformed, failed, short, or oversized ArbSys responses fail
  closed without native fallback.
- **Guarantee:** the corrected current source is byte-identical to the
  originating production commit and preserves persistent storage layout.
- **Non-guarantee:** exact 32-byte returndata does not prove that the reported
  identity is true or that future chain governance preserves ArbSys behavior.
- **Non-guarantee:** equality-only logic does not detect a different but
  regressed identity.
- **Non-guarantee:** integrated source and tests do not prove an exact-`0x64`
  live deployment or activation.
- **Architecture:** the current code is technically sound but is a two-mode
  discriminator, not a proper generic provider abstraction.
- **Recommendation:** retain the current source for the initial release; do not
  create `LedgerRh.vy` or add a provider without a concrete third semantic
  family.
- **Required next work:** close deployment, artifact, native-replay,
  real-network qualification, consumer, monitoring, and incident-response
  gates; revisit the architecture on the explicit triggers above.
