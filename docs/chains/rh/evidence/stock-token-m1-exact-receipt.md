# Track 8 M1 Phase A exact-receipt evidence

**Evidence date:** 25 July 2026

**Checkpoint captured:** `2026-07-25T20:58:23Z` (`2026-07-25T14:58:23-0600`, MDT)

**Durability update date:** 26 July 2026

**Durability replay captured:** `2026-07-26T07:30:42Z`
(`2026-07-26T01:30:42-0600`, MDT)

**Owner-disposition correction captured:** `2026-07-26T15:05:29Z`
(`2026-07-26T09:05:29-0600`, MDT)

**Exact-candidate owner approval captured:** `2026-07-26T15:17:24Z`
(`2026-07-26T09:17:24-0600`, MDT)

**Final evidence-only reconciliation captured:** `2026-07-26T16:14:31Z`
(`2026-07-26T10:14:31-0600`, MDT)

**Lifecycle and provenance reconciliation captured:** `2026-07-26T22:22:50Z`
(`2026-07-26T16:22:50-0600`, MDT)

**Current-`rh` convergence refresh captured:** `2026-07-26T22:34:34Z`
(`2026-07-26T16:34:34-0600`, MDT)

**Status:** **Phase A closed when the independently reviewed evidence was
committed byte-for-byte at `2935f0e2fc7c1f0a783e5b822ca560dc11f375f5`;
this lifecycle-only follow-up is unstaged for independent exact-hash review;
Phase B remains unauthorized and unstarted**

**Review and re-review correction date:** 25 July 2026

**First-review chat-attachment SHA-256 (informational, non-durable):**
`a9f470cfe84b099ff23258dc066fa1792a6fbe1d0d77192f9f38dddb192317ff`

**Re-review chat-attachment SHA-256 (informational, non-durable):**
`3dd6359939fa962d081ffbbf99bfe627301b18f476ac72c77d9848c6e2e260a3`

**Review-correction validation captured:** `2026-07-25T21:49:07Z`
(`2026-07-25T15:49:07-0600`, MDT)

**Controlling brief:** `docs/chains/rh/track-8-m1-exact-receipt.md`

**Controlling brief SHA-256:** `34749b58c6bd3b0452cb2d73987ce86aa5ff7269a86429c466bd7b1cdae64270`

**Owner-approved launch baseline:** `332ae2bc8e0ce4b694766d6d20759295d9267ec3`

**Baseline tree:** `f67dc91e47331785837de879b6557b285aec3b1b`

**Feature branch:** `rh-track-8-m1-exact-receipt`
**Feature worktree:** `/Users/wigglez/dev/ripe-protocol-track-8-m1-exact-receipt`
**Phase A evidence commit:** `2935f0e2fc7c1f0a783e5b822ca560dc11f375f5`
**Committed evidence SHA-256:**
`9ef48b80fc0fe1e37ee6878d81201274a1ac7eda682d96de0205439e2242917e`
**Current local/cached/live `rh`:**
`8e4a965f034dc3d11b60fbb674ebbb4095b57d98`
**Current `rh` tree:** `d0a6048d902a035bf69158359dc80e9786792f38`

The durable record itself is the only repository file created in Phase A.
The current working copy's SHA-256 is reported in the checkpoint response
rather than embedded here, because embedding a file's own digest would change
the bytes being hashed. The embedded `9ef48b80...917e` identity is explicitly
the approved and committed predecessor, not a self-digest claim for this
follow-up revision.

Sections 1 through 12 retain the historical 25 July Phase A evidence and
commands, with current-disposition annotations where their original
present-tense status became stale. Sections 0 and 12.3 control where a
historical statement below differs from the current disposition. Section 0
is the later, owner-directed exact-feasibility durability addendum. In
particular, the owner has now resolved the
CreditEngine/CreditRedeem nomenclature and reachability question, approved the
fixed-sGREEN test ceiling, authorized reproduction under the exact reviewed
lock, and accepted the exact Teller source form and its limited headroom under
the byte-specific conditions below. The task transcript later records exact-hash
approval of evidence SHA-256 `9ef48b80...917e`, its byte-identical one-file
commit, and Phase A closure. This lifecycle-only follow-up does not reopen
Phase A and authorizes neither candidate modification, Phase B, Gate 1,
staging, a commit, nor any later action.

## 0. Exact-feasibility durability addendum

### 0.1 Authority, drift check, and exact owner approval provenance

The isolated feasibility task used the exact owner-approved baseline:

```text
commit  332ae2bc8e0ce4b694766d6d20759295d9267ec3
tree    f67dc91e47331785837de879b6557b285aec3b1b
```

The baseline contains the controlling M1 brief. A byte comparison found no
drift between that commit and the active M1 worktree for any of the five
controlling documents:

| Controlling document | SHA-256 |
| --- | --- |
| `docs/chains/rh/track-8-m1-exact-receipt.md` | `34749b58c6bd3b0452cb2d73987ce86aa5ff7269a86429c466bd7b1cdae64270` |
| `docs/chains/rh/stock-token-vault-change-specification.md` | `84e3368991803a92ffe2f82f47ef762045cdd9ed90ddd6a833e1531c866d4059` |
| `docs/chains/rh/stock-token-vault-change-validation-plan.md` | `675f31c7245243b286649b95f1d621c42fc9a662bc3f70cf446c76bb028325bf` |
| `docs/chains/rh/stock-token-m0-evidence.md` | `1ca5ec599e7bab406dd63e2d220251bb085ac2fbf9416bc8f4585632e283e4be` |
| `docs/chains/rh/track-8-m0-owner-decision-packet.md` | `9fc44e47ae98bfe8e99c6554580215150461f17182ec92094588b7e650186496` |

For the feasibility prototype, the owner expressly approved these
interpretations:

1. prior exact-lock validation could be supporting evidence, provided every
   result material to this prototype was reproduced;
2. CreditRedeem's surplus-deposit branch is intentionally dormant because
   its only current caller supplies `_shouldEnterStabPool=False`, and M1 must
   not change CreditRedeem to activate it;
3. CreditEngine's live route is borrower-proceeds auto-deposit;
4. fixed-sGREEN failure may be induced with an existing authorized test seam
   or a narrowly scoped inline mock, but never by changing production behavior
   merely to create the test; and
5. Teller is the sole production-change boundary. Any need to modify
   CreditRedeem, CreditEngine, a vault, an interface, or any other production
   contract is a stop.

The owner supplied this approval against the then-untracked Phase A evidence at
SHA-256
`f5ed7d1e2e63b0491369e91932ba4a8aa2391e3dbd83a31749a8016c41831075`
and the preserved exact-candidate identities in Sections 0.2 through 0.6.
That provenance snapshot remains read-only at
`phase-a-evidence-after-durability.md`.

The owner expressly approved all of the following:

1. the exact feasibility candidate's Teller source form at SHA-256
   `4afc6ce1ccf21cb65e04ce3c56fedcf60bb79cba8e7dc51fd855a1f1f82bd909`;
2. its measured **24,152-byte deployed runtime and 424-byte EIP-170
   headroom** as a bounded, M1-specific maintenance risk;
3. acceptance only for those exact Teller bytes: any Teller source-byte
   change invalidates it and requires fresh compilation, runtime measurement,
   creation/runtime artifact hashes, complete tests, and independent review;
4. no additional Teller functionality and no widening of the approved M1
   production scope;
5. a repository-level automated size guard inside an already authorized M1
   test file, with no additional implementation file, that proves both
   `runtime <= 24_576` and `runtime <= 24_152`; any later growth must fail
   until separately reviewed and approved;
6. recording the Phase A owner questions as approved while, at that
   checkpoint, keeping Phase A open until the complete evidence and preserved
   candidate received independent exact-hash approval; and
7. keeping official Phase B unauthorized unless and until independent Phase A
   review completed, the reviewed Phase A evidence was committed, S5's final
   integration state is reconciled because the workstreams overlap Teller
   tests, and the owner gives separate explicit file-exact Phase B
   authorization.

The independent Phase A review and evidence-commit conditions in items 6 and
7 are now complete. The S5/current-`rh` reconciliation and separate
file-exact Phase B authorization conditions remain pending.

Because the exact Teller source form is now approved, that approval includes
its use of Vyper's checked unsigned subtraction as the `C1 >= C0` failure
boundary rather than a separate redundant source assertion. It does not
authorize different Teller bytes.

The exact-source acceptance expressly includes the behavior-neutral,
source-line-stabilizing formatting hunks in the preserved Teller patch:
line-neutral blank-line removals, removal of inherited trailing whitespace at
EOF, and addition of the missing final newline. Those hunks are part of source
SHA-256
`4afc6ce1ccf21cb65e04ce3c56fedcf60bb79cba8e7dc51fd855a1f1f82bd909`;
they must not be stripped, rewritten, or resealed independently.

An earlier independent candidate review substantively approved the exact
Teller candidate and independently reproduced its source, complete patch,
invariant behavior, ABI/layout invariance, and 24,152-byte runtime. Its
evidence target, however, was the superseded
`f5ed7d1e2e63b0491369e91932ba4a8aa2391e3dbd83a31749a8016c41831075`
snapshot, not the then-current evidence at
`b32a15c8cc07543625d24234c509e9b74d8607ed1051a6b5f03f30e08a24da95`.
It therefore supplied substantive candidate approval but not exact-hash
approval of that reconciled record. The evidence-only reconciliation from
`b32a15c8...da95` subsequently produced
`9ef48b80fc0fe1e37ee6878d81201274a1ac7eda682d96de0205439e2242917e`.

The task transcript then records the exact lifecycle provenance:

1. at `2026-07-26T20:44:16.018Z`, the owner stated that the independent
   exact-hash review had approved the complete Phase A evidence at
   `9ef48b80...917e`, authorized one local commit containing exactly this
   evidence file with those bytes unchanged, and specified that Phase A would
   close with that exact commit;
2. at `2026-07-26T20:45:52.710Z`, the resulting handoff reported commit
   `2935f0e2fc7c1f0a783e5b822ca560dc11f375f5`, tree
   `a805c4b2fa0145b8bf0d80f822ed05cc730af318`, parent
   `332ae2bc8e0ce4b694766d6d20759295d9267ec3`, exact one-file scope, and
   committed-file SHA-256 `9ef48b80...917e`; and
3. after a separate push authorization at `2026-07-26T20:47:39.116Z`, the
   `2026-07-26T20:48:41.225Z` handoff reported local, tracking, and live
   remote feature refs all at `2935f0e2...75f5`.

Current Git inspection independently reproduces those commit, tree, parent,
scope, file-hash, and ref identities. The transcript proves the owner's
statement of independent exact-hash approval and the exact commit
authorization; this record does not invent a reviewer identity or claim
access to a separate review artifact that the transcript does not contain.

The current working copy changes only lifecycle, provenance, Git-state, and
current-baseline wording on top of the closed Phase A commit. It is deliberately
unstaged for a new independent exact-hash review before any later
documentation-only commit. That follow-up review is not a condition that
reopens Phase A and is not Phase B authorization.

The two earlier evidence snapshots that were never committed remain preserved
for auditability:

- `phase-a-evidence-before-durability.md`, SHA-256
  `bbe08bc624403b0c4ecd76f6ab3505f6be318650099aed89070e20f4d0029c0e`;
  and
- `phase-a-evidence-superseded-acceptance-characterization.md`, SHA-256
  `65321cd9f0d697f8a1f434cf36266fa5dc549bd5c3fe4e2731e586f61c0eba77`.

Neither older snapshot substitutes for the independently approved and
committed `9ef48b80...917e` evidence. Phase A is closed. Phase B remains
unauthorized and unstarted.

### 0.2 Exact reconstruction and durable preservation

The disposable prototype had been removed. Its exact edit history was replayed
against the approved baseline into this detached, isolated worktree:

```text
/Users/wigglez/dev/ripe-protocol-track-8-m1-feasibility-review
```

The reconstruction has no branch, remains at detached
`332ae2bc8e0ce4b694766d6d20759295d9267ec3`, and contains exactly these four
unstaged modifications:

```text
contracts/core/Teller.vy
tests/core/teller/test_teller_deposit.py
tests/core/teller/test_teller_rebalance.py
tests/vaults/test_stock_token_vault_comparison.py
```

No fifth file is modified or untracked in that worktree. Its index is empty.
The active M1 worktree was not used to reconstruct or run the candidate and
was clean at the reviewed Phase A commit before this reconciliation. At this
handoff it contains only this evidence file as an unstaged modification on
top of that commit, and its index is empty.

The exact patches and the pre-update evidence snapshot are preserved outside
every worktree in a mode-`0700` directory:

```text
/Users/wigglez/dev/ripe-protocol-track-8-m1-feasibility-artifacts
```

| Preserved artifact | Bytes | Mode | SHA-256 |
| --- | ---: | ---: | --- |
| `teller-exact-receipt.patch` | 4,234 | `0444` | `748cb1ce3e6cce17b15d279ecdb8c1cb419cc9357b5e1c56c5dfb2ff634c4b40` |
| `four-file-exact-receipt.patch` | 39,875 | `0444` | `556a3553930da1008ac1bb75751ad4be2c5c28faf6fc6d9138e8b85e4b00768f` |
| `phase-a-evidence-before-durability.md` | 98,462 | `0444` | `bbe08bc624403b0c4ecd76f6ab3505f6be318650099aed89070e20f4d0029c0e` |

The separate superseded-characterization snapshot is 122,323 bytes, mode
`0444`, and has the SHA-256 recorded in Section 0.1. It is retained to make
the pre-commit evidence history independently diffable rather than silently
overwriting the only prior bytes.

`git apply --check` accepted the preserved four-file patch against the clean
approved baseline. The exact reconstruction reproduced every previously
reported file and patch identity:

| Reconstructed file | SHA-256 |
| --- | --- |
| `contracts/core/Teller.vy` | `4afc6ce1ccf21cb65e04ce3c56fedcf60bb79cba8e7dc51fd855a1f1f82bd909` |
| `tests/core/teller/test_teller_deposit.py` | `e31838927cdf3f428001aca002dbba9b5677e0946ac87a55b62ab1d22843b7ce` |
| `tests/core/teller/test_teller_rebalance.py` | `d6b818db1de15bbce61c154033dcf48940d52f86632c08265d8b3b6eb3d14093` |
| `tests/vaults/test_stock_token_vault_comparison.py` | `cfff4d7e4eadc224a2e96b461bd82e7a2dbe0069fe3b1f58e8cc56a7a46b7e3f` |

The complete patch is 1,096 insertions and 29 deletions:

| File | Insertions | Deletions |
| --- | ---: | ---: |
| `contracts/core/Teller.vy` | 25 | 12 |
| `tests/core/teller/test_teller_deposit.py` | 950 | 1 |
| `tests/core/teller/test_teller_rebalance.py` | 61 | 0 |
| `tests/vaults/test_stock_token_vault_comparison.py` | 60 | 16 |

The Teller-only patch also reproduces at 25 insertions and 12 deletions.
Line-neutral blank-line removals keep the existing S2 cadence candidate on
line 992. Removing inherited trailing whitespace at EOF and adding the missing
final newline make `git diff --check` clean; neither changes runtime behavior.
They are nevertheless accepted bytes of the exact Teller source identity and
must remain unchanged in any official Phase B package and every later review.

### 0.3 Exact candidate structure

The exact Teller source adds one private transient Boolean:

```vyper
receiptMeasurementActive: transient(bool)
```

After existing vault resolution, Ledger reads, and
`TellerUtils.validateOnDeposit`, `_deposit`:

1. requires the measurement mutex to be clear and sets it;
2. reads destination-vault custody `C0`;
3. performs the unchanged `transfer` or `transferFrom` of validated amount
   `Q`;
4. reads `C1` and requires checked `C1 - C0 == Q`;
5. calls the unchanged zero-lock or locked vault endpoint and requires its
   returned amount to equal `Q`;
6. clears the mutex; and
7. preserves the existing Ledger, Lootbox, housekeeping, PriceDesk, event,
   and return ordering and amount identity.

For M1-D02, the checked unsigned subtraction is also the semantic
`C1 >= C0` enforcement. If `C1 < C0`, Vyper reverts while evaluating the
subtraction before the equality can succeed. The approved source therefore
requires no separate `C1 >= C0` assertion. Gate 1 must reproduce and test that
custody-decrease failure behavior from the exact approved bytes.

The internal balance helper is exactly:

```vyper
@view
@internal
def _exactBalance(_asset: address, _holder: address) -> uint256:
    response: Bytes[33] = raw_call(
        _asset,
        abi_encode(_holder, method_id=method_id("balanceOf(address)")),
        max_outsize=33,
        is_static_call=True,
    )
    assert len(response) == 32
    return abi_decode(response, uint256)
```

The 33-byte capture makes oversized output observable. Empty, short, 33-byte,
64-byte, and longer responses cannot be silently accepted as one word.

The separately supplied S5 Gate 1 review is direct cross-slice corroboration:
an earlier typed Vyper `staticcall` expecting one `uint256` accepted a 64-byte
return and ignored the second word. S5 corrected that separate boundary with
`raw_call`, an output ceiling above 32, and `len(response) == 32`. The current
uncommitted S5 recreation bytes have continued to move and are not an M1
authority or baseline, so this record consumes only the owner-supplied
behavioral finding. M1 independently compiles and tests its own 33-byte
balance-read boundary.

No interface, ABI file, vault, CreditEngine, CreditRedeem, Ledger, mock,
configuration, dependency, migration, or other production contract changes.
CreditRedeem remains dormant and retains its current user-refund behavior.
CreditEngine remains borrower-proceeds auto-deposit.

### 0.4 Locked compiler and exact artifact reproduction

A fresh external mode-`0700` virtual environment was installed from the
reviewed `requirements.txt`; no repository dependency file changed.

| Identity | Reproduced value |
| --- | --- |
| CPython | `3.12.0` |
| pip | `23.2.1` |
| Vyper | `0.4.3+commit.bff19ea2` |
| Titanoboa | `0.2.7` |
| pytest | `8.4.2` |
| Frozen distributions | 92 |
| Canonical `pip freeze` SHA-256 | `6d8d1dfe85ac175030f2fd5248b4e8697ba0d2be9f8ad725412d8c7df980867f` |
| `pip check` | `No broken requirements found.` |
| `requirements.in` SHA-256 | `2523c04409946a6625e30e5e4aa4f711663924f4a674f4cfd5fee5b7bbb3b80d` |
| `requirements.txt` SHA-256 | `d2e12a6f0cfd128c3891634efafbba8305878bef7a7c5db33e25ebe93b0d2bce` |
| Compiler settings | `optimize=codesize`; experimental codegen disabled |
| Canonical settings SHA-256 | `1bff982534eddbbfdfe01e01229e3c4d6016d0eec6dbe240aa4b49a1cd05f99f` |

The exact compiler output reproduced:

| Artifact | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| Creation bytecode | 24,141 bytes | 24,387 bytes | +246 |
| Deployed runtime | 23,906 bytes | **24,152 bytes** | +246 |
| EIP-170 headroom | 670 bytes | **424 bytes** | -246 |
| Runtime utilization | 97.27% | **98.27%** | +1.00 percentage point |

The exact candidate consumes 246 of the baseline's remaining 670 bytes:
**36.7% of the prior reserve**. It leaves 424 bytes. The owner's bounded
maintenance-risk acceptance is specific to the exact approved Teller source
bytes and establishes neither a general minimum-headroom policy nor precedent
for later Teller changes.

| Artifact | Baseline SHA-256 | Candidate SHA-256 |
| --- | --- | --- |
| Creation bytecode | `0c20af1d404d46d28a733bcf9b4b2ec1f258231a4403dceb6e76206b0b52f897` | `b94a58ac0faa6cad71e58f451cb9aea27a7152bf63bfc65798103d3b97704e5a` |
| Deployed runtime | `3736bc669f225b463219defe27fc4627db96400093dab45ff081582ccec881f4` | `39ffa8d3274b74c91896a36c4d2ce9d6df5c197758a89fbfd1589b394dad5b81` |

| Artifact | Baseline Keccak-256 | Candidate Keccak-256 |
| --- | --- | --- |
| Creation bytecode | `0xf79a7babb06bf514bd1f72a90fa87be9a242cc4a175af64b31cc3966095d8467` | `0xa22f045e956d107d73ea1fb4f1591b9c4c663d05eb935cf04569ad250bb33f83` |
| Deployed runtime | `0x19b8c58290b9736fe6336df7b003e70a85792b5f96c621810eed9f186ba19d53` | `0xde3a405af398843a0f0e94ed8e805dff4cd24049aef3c3e0748075bacecc45d0` |

The durability replay executed an automated assertion:

```text
assert len(deployedRuntimeBytecode) <= 24_576
EIP170_ASSERTION_OK runtime_bytes=24152 limit=24576 headroom=424
```

The exact preserved four-file feasibility snapshot contains no repository
test that performs this compile-time check. The owner now requires the
official implementation to add a guard inside an already authorized M1 test
file, without adding an implementation file. It must compile Teller and
assert both:

```text
runtime_bytes <= 24_576
runtime_bytes <= 24_152
```

Any future runtime growth must fail the second assertion until separately
reviewed and approved. Adding the guard will change one authorized test-file
hash and the complete implementation patch hash, but it may not change the
approved Teller bytes. Because official Phase B remains unauthorized, this
evidence-only update does not add the guard or modify the preserved
feasibility candidate. The already executed external assertion proves the
size calculation is implementable without falsely claiming the preserved
patch contains the required repository test.

### 0.5 ABI, selector, event, and layout invariance

Every required external or persistent surface reproduced exactly:

| Surface | Reproduction result |
| --- | --- |
| ABI | Identical: 131 entries, 123 functions, 7 events, 1 constructor |
| Canonical ABI SHA-256 | `319169528ec22722c7f912a0f93d3a0560feb17c2d6349770c17a643e1f00e20` |
| Checked ABI JSON | Identical to baseline and candidate |
| Checked ABI raw-file SHA-256 | `e5b696f0e22c2196806cd84f27a037d21ca567d702a357f3a61a574fd514e1f4` |
| Selectors | All 123 identical; none added or removed |
| Selector-map SHA-256 | `48ff38c54c9879b56bb6c8b16774028b4b31e14c68d1a510e3d800bfe19a0a61` |
| Events/topics | All 7 identical |
| Event-map SHA-256 | `6d7cda4cd8a2245aff1e0b5b559df3660ce9688871cc342a3c3c64adb86bcaf8` |
| Code layout | Identical |
| Code-layout SHA-256 | `2c77aa8465e34115aeb86592f9878fdb2cf895ec4a7460c9edbaf48d540d9d96` |
| Persistent storage layout | Identical |
| Persistent-layout SHA-256 | `2558002963f9b545aac0e44df655f4547256f439b6ba76d8e52975005c697c68` |

The baseline complete-layout hash is
`dac3acdb8263039970917f14410e3a284cc71f71614b094bb938d4ba4e9f94d6`;
the candidate complete-layout hash is
`ff59be454b3c826bae2e6ae611d799de47350ec5fb5f8e4415a9cfaa3b398443`.
The only difference is the approved transient Boolean:

```text
existing $.nonreentrant_key       transient slot 0, unchanged
new receiptMeasurementActive      transient bool slot 1
```

The baseline transient-layout hash is
`1605375841cfedfb24d569df284637d636c22f2cc5028bfe2cc4b2663962dee8`;
the candidate transient-layout hash is
`a9c1ff6412a56079143ac301dadac249687609edc9dcafe88668b299d7c6202d`.
Persistent storage remains only `deptBasics.isPaused` at slot 0. No getter or
selector is generated.

### 0.6 Exact behavior and validation reproduction

The candidate tests exercise:

- ordinary direct deposit and every `depositMany` element;
- RipeGov deposit with and without lock, rebalance deposit/withdraw ordering,
  and unchanged housekeeping;
- `depositFromTrusted` and every authorized producer category;
- ordinary exact receipt;
- zero, short, excess, custody-decrease, empty, short, oversized, malformed,
  and reverting `balanceOf` responses;
- vault-result mismatch;
- nested measurement rejection and complete revert atomicity;
- the Teller-held fixed-sGREEN conversion route, including an induced
  short-sGREEN failure through a test-local RipeHq registry replacement;
- CreditEngine borrower-proceeds auto-deposit and zeroed approvals;
- CreditRedeem's intentionally dormant deposit branch, current sGREEN refund,
  unchanged StabilityPool state, and absence of a Teller deposit event; and
- unchanged direct/batch/Gov/rebalance permissions, pause behavior, selectors,
  events, locks, accounting, and unrelated routes.

The fixed-sGREEN construction uses only an authorized test file and an
existing registry-update seam. It changes no production behavior and requires
no repository mock file.

All final durability runs used the exact reconstructed hashes, one external
mode-`0700` Titanoboa cache, distinct external mode-`0700` pytest basetemps,
the reviewed lock, and an environment with all live RPC and signer variables
unset. No run contacted a live RPC.

| Gate | Original exact result | Durability replay |
| --- | ---: | ---: |
| H-01 + S1 + S2 tests | 133 passed | **133 passed** |
| S2 checker | Clean `100/95/17`; 455 cadence candidates | **Exact match** |
| M1 focused | 49 passed, 136 deselected | **Exact match** |
| Three authorized files | 185 passed | **185 passed** |
| Targeted downstream/Base/S5-sensitive regression | 1,794 passed, 21 deselected | **Exact match** |
| Baseline masking counterexamples | 4 passed | **4 passed** |
| Baseline collection | 2,837 selected, 142 deselected, 2,979 total | **Exact match** |
| Candidate collection / full selection | 2,884 selected, 142 deselected, 3,026 total | **Exact match** |
| Complete final serial suite | 2,884 passed, 142 deselected | **2,884 passed, 142 deselected** |
| Selected skips / xfails | 0 / 0 | **0 / 0** |
| Modified Python test compilation | Passed | **Passed** |
| `git diff --check` | Clean | **Clean** |
| Automated EIP-170 assertion | External exact-candidate check | **Passed: 24,152 <= 24,576** |

Durability replay times were 122.07 seconds for H-01/S1/S2, 36.36 seconds for
focused M1, 58.45 seconds for the three authorized files, 246.86 seconds for
targeted regression, 28.19 seconds for baseline counterexamples, and 302.94
seconds for the complete serial suite.

The four reproduced baseline counterexamples retain their exact material
outputs:

| Baseline case | Material output |
| --- | --- |
| Multi-user SimpleErc20 | custody `199999999999999999998`; aggregate nominal `199999999999999999999`; second receipt `99999999999999999999`; reported `100000000000000000000` |
| Multi-user RebaseErc20 | custody/aggregate `199999999999999999998`; second receipt `99999999999999999999`; reported `100000000000000000000`; share/accounting result differs from a correctly measured receipt |
| Donation SimpleErc20 | custody before `25000000000000000000`; call receipt `99999999999999999999`; reported/user credit `100000000000000000000`; donation masks the one-unit shortfall |
| Donation RebaseErc20 | custody before `25000000000000000000`; call receipt `99999999999999999999`; reported/user credit `100000000000000000000`; aggregate folds in donated custody |

The exact candidate rejects all four atomically. It also rejects zero, short,
excess, malformed-return, vault-mismatch, and nested-measurement cases without
leaving token movement, nominal credit, shares, locks, points, debt effects,
events, approvals, or transient state.

Every Boa-first pytest invocation emitted the same three non-fatal
`PytestAssertRewriteWarning` messages for `_hypothesis_globals`,
`hypothesis`, and `boa`, because Boa was imported before pytest to set the
isolated cache. The shell emitted the known non-test
`pyenv: cannot rehash` warning. pip disabled its unwritable user cache and
then completed successfully. There were no unresolved test, compiler, lock,
collection, ABI, layout, or patch failures.

One final composite hygiene check used `status` as a shell variable, which is
read-only in zsh, and stopped after printing each worktree status. The
corrected command used `task_stage_rc`; it returned `staged_exit=0` for the
integration, active M1, and preserved candidate worktrees. The diagnostic
changed no file or index.

The exact durability command families were:

```bash
git worktree add --detach \
  /Users/wigglez/dev/ripe-protocol-track-8-m1-feasibility-review \
  332ae2bc8e0ce4b694766d6d20759295d9267ec3

/Users/wigglez/.pyenv/versions/3.12.0/bin/python -m venv \
  /private/tmp/ripe-track8-m1-durability-env-019f9b45/venv

/private/tmp/ripe-track8-m1-durability-env-019f9b45/venv/bin/python \
  -m pip install --no-cache-dir -r requirements.txt

/private/tmp/ripe-track8-m1-durability-env-019f9b45/venv/bin/pip check

PYTHONPYCACHEPREFIX=<external-pycache> \
  <locked-python> -m py_compile \
  tests/core/teller/test_teller_deposit.py \
  tests/core/teller/test_teller_rebalance.py \
  tests/vaults/test_stock_token_vault_comparison.py

PYTHONPATH=. <locked-python> \
  scripts/check_block_clock_inventory.py --check

<locked-vyper> -p . -f combined_json contracts/core/Teller.vy
<locked-vyper> -p . -f bytecode_runtime contracts/core/Teller.vy
git diff --check
```

Every test used this Boa-first wrapper, with all seven live RPC/signer
variables removed and `ETHERSCAN_API_KEY=local-placeholder`:

```bash
PYTHONPATH=. <locked-python> -c '
from pathlib import Path
from boa.interpret import set_cache_dir
set_cache_dir(Path("<external-mode-0700-cache>"))
import pytest
raise SystemExit(pytest.main(<arguments>))
'
```

The exact test argument sets were:

```text
-q --basetemp=<external>/gates
  tests/deployment/test_dependency_gate.py
  tests/clock/test_clock_profiles.py
  tests/inventory/test_block_clock_inventory.py

-q --basetemp=<external>/focused
  tests/core/teller/test_teller_deposit.py
  tests/core/teller/test_teller_rebalance.py
  tests/vaults/test_stock_token_vault_comparison.py
  -k "m1 or short_received_after or donation_cannot"

-q --basetemp=<external>/authorized
  tests/core/teller/test_teller_deposit.py
  tests/core/teller/test_teller_rebalance.py
  tests/vaults/test_stock_token_vault_comparison.py

-q --basetemp=<external>/targeted
  tests/core/teller tests/vaults tests/core/creditEngine
  tests/core/deleverage tests/core/lootbox tests/core/bondRoom
  tests/core/humanResources tests/core/auctionHouse
  tests/data/test_ledger.py tests/config/test_switchboard_delta.py
  tests/config/test_switchboard_charlie.py tests/config/test_bond_booster.py
  tests/priceSources/blueChip/test_bluechip_local.py
  tests/priceSources/test_aero_ripe.py
  tests/priceSources/test_undy_vault_prices.py
  tests/tokens/test_erc20.py tests/tokens/test_erc4626.py
  tests/modules/test_local_gov.py

-q -rs --basetemp=<external>/full
```

Baseline collection used the same lock and external cache with
`--collect-only -p no:terminal -p no:cacheprovider`. The temporary detached
baseline worktree used for the four printed counterexamples was removed with
`git worktree remove --force`. The virtual environment, Boa cache, all
basetemps, pycache, and artifact-comparison helper under the three exact
`/private/tmp/ripe-track8-m1-durability-*` paths were deleted and their
absence verified. The preserved candidate worktree and read-only artifacts
were intentionally retained for the then-pending independent review and
remain preserved. Ignored `.pytest_cache`, `.hypothesis`, `__pycache__`, and
compiled-Python files created by validation were removed from the preserved
worktree; an ignored-inclusive status now shows only the same four
source/test modifications.

### 0.7 Current feasibility disposition and remaining decisions

The exact result is now:

> **Feasible as the exact owner-approved and independently reviewed
> Teller-only M1 candidate, subject to every still-pending Phase B gate
> below.**

No other production contract or interface is needed. No required regression
fails. The exact lock, fixed-sGREEN failure, CreditEngine route,
CreditRedeem dormancy/refund behavior, and full atomicity are all reproduced.

The following limitations remain controlling:

- the 424-byte reserve is small and is accepted only for Teller source
  SHA-256
  `4afc6ce1ccf21cb65e04ce3c56fedcf60bb79cba8e7dc51fd855a1f1f82bd909`
  as an M1-specific risk;
- any Teller source-byte change voids this result;
- no additional Teller behavior or broader production scope is permitted;
- the preserved feasibility patch contains no repository EIP-170 guard; an
  authorized Phase B implementation must add the dual-threshold guard inside
  an already authorized M1 test file and reseal the complete patch while
  leaving Teller bytes unchanged;
- Gate 1 must independently reproduce all compiler artifacts, surface/layout
  invariants, test counts, and the complete serial suite from the exact
  implementation package;
- the S5 truncation finding is corroboration, not an integrated M1 dependency;
- S5's final integration state must be reconciled before Phase B because the
  two workstreams overlap Teller tests; any relevant Teller/Ledger or
  controlling-object change requires the brief's stop and reconciliation;
- nothing here establishes a later Teller headroom policy or precedent.

The owner questions are approved, and the exact-hash review and one-file
evidence commit that closed Phase A are complete. The current
lifecycle/provenance edit remains deliberately unstaged for independent
exact-hash review before any later documentation-only commit; that review
does not reopen Phase A. The still-pending gates are:

1. reconcile current `rh` at `8e4a965f...7d98`, S5's final reviewed and
   integrated state, and all overlapping Teller-test effects;
2. reseal the two overlapping Teller test files and complete M1 patch against
   that reconciled baseline;
3. obtain separate explicit, file-exact owner authorization for official
   Phase B;
4. only during that later authorized Phase B, add the dual-threshold size
   guard inside an already authorized M1 test file, without changing the
   accepted Teller bytes or adding an implementation file;
5. require Gate 1 to reproduce the exact compiler output, 24,152-byte runtime,
   artifact hashes, ABI/selectors/events/layout invariance, guard result, and
   complete validation;
6. separately decide whether to authorize a local implementation commit after
   Gate 1; and
7. retain all existing later merge, Gate 2, deployment, configuration,
   signing, broadcasting, live-RPC, activation, and M2-M5 gates.

At this handoff, **Phase B remains unauthorized and unstarted**. This
reconciliation leaves exactly this evidence file modified but unstaged and
the index empty. The earlier authorized Phase A evidence commit and feature
push are recorded in Section 0.1; no new commit, push, merge, deployment,
configuration, signature, transaction, broadcast, external-human contact, or
live RPC occurred in this reconciliation.

### 0.8 Current authority, `rh`, and S5 refresh

The read-only convergence refresh at `2026-07-26T22:34:34Z` found:

- the integration worktree clean on `rh`;
- integration `HEAD`, local `rh`, cached `origin/rh`, and live remote `rh`
  all equal
  `8e4a965f034dc3d11b60fbb674ebbb4095b57d98`, with tree
  `d0a6048d902a035bf69158359dc80e9786792f38`;
- the net incoming H-03 Phase A R6 movement adds
  `docs/chains/rh/evidence/robinhood-blueprint-phase-a.md` and modifies
  `docs/chains/rh/track-7-h3-robinhood-blueprint-omissions.md`;
- current `rh` is ten commits beyond the owner-approved launch baseline. Its
  full net delta is documentation-only: three added evidence records and two
  modified Robinhood briefs. The incoming H-03 movement and full net delta
  change none of the five controlling M0/M1 documents, `Teller.vy`, the three
  M1 test files, the feasibility candidate, or either preserved patch;
- the official M1 feature branch, its tracking ref, and the live remote
  feature ref all equal
  `2935f0e2fc7c1f0a783e5b822ca560dc11f375f5`, with tree
  `a805c4b2fa0145b8bf0d80f822ed05cc730af318`;
- the feature/current-`rh` merge base remains the launch baseline
  `332ae2bc...7ec3`; the feature is one commit ahead and ten commits behind
  current `rh` and remains unintegrated. No feature reconciliation, merge,
  rebase, or amendment has occurred;
- the official M1 worktree was clean before this reconciliation and now has
  exactly this evidence file modified but unstaged, with an empty index; and
- the five controlling M0/M1 authority hashes unchanged:

| Controlling authority | Refreshed SHA-256 |
| --- | --- |
| `docs/chains/rh/track-8-m1-exact-receipt.md` | `34749b58c6bd3b0452cb2d73987ce86aa5ff7269a86429c466bd7b1cdae64270` |
| `docs/chains/rh/stock-token-vault-change-specification.md` | `84e3368991803a92ffe2f82f47ef762045cdd9ed90ddd6a833e1531c866d4059` |
| `docs/chains/rh/stock-token-vault-change-validation-plan.md` | `675f31c7245243b286649b95f1d621c42fc9a662bc3f70cf446c76bb028325bf` |
| `docs/chains/rh/stock-token-m0-evidence.md` | `1ca5ec599e7bab406dd63e2d220251bb085ac2fbf9416bc8f4585632e283e4be` |
| `docs/chains/rh/track-8-m0-owner-decision-packet.md` | `9fc44e47ae98bfe8e99c6554580215150461f17182ec92094588b7e650186496` |

S5 is not integrated into `rh`, but its local recreation state is no longer
the docs-only snapshot recorded historically in Section 2.2:

| S5 identity or state | Current result |
| --- | --- |
| Local recreation head | `db5e589e13bc39002a345d70cb9d9a38eb13fd67` |
| Cached/live remote recreation head | `444b3c91711ab79fc0fa2c36063dd11701481f51` |
| Local versus remote | `0 behind / 12 ahead` |
| Merge base with `rh` | `332ae2bc8e0ce4b694766d6d20759295d9267ec3` |
| Recreation head ancestor of `rh` | No |
| Worktree state | 14 unstaged modified paths, three untracked paths, empty index |
| Working `contracts/data/Ledger.vy` SHA-256 | `6bd731a6ce9084de213494ebad09f8e52c782153842708b78f90fa178c06e9e3` |
| Working `contracts/core/Teller.vy` SHA-256 | `51cf13e3c9d58262ba446a462332d8f4f181c07ce689031b2398c20137f04198` |

The current unstaged S5 delta changes Ledger action-block behavior and
modifies both M1-owned Teller test files
`tests/core/teller/test_teller_deposit.py` and
`tests/core/teller/test_teller_rebalance.py`, among other tests. No S5 byte is
present in current `rh`, and S5 does not change Teller source. The
documentation-only advance in current `rh` likewise changes no controlling
M1 object or production/test byte. Neither movement retroactively invalidates
the exact feasibility result against baseline `332ae2bc...`. Local, cached,
and live `rh` are converged and add no separate ref-state stop. S5 must still
reach a final reviewed and integrated state; current `rh`, its Ledger
behavior, and the overlapping Teller-test effects must then be reconciled and
rerun before separate file-exact Phase B authorization.

## 1. Historical 25 July owner authorization and gate ledger

The kickoff authorization received from the owner is:

> On 25 July 2026, I approved M1-D01 through M1-D07 exactly as presented in the reviewed brief at SHA-256:
>
> `34749b58c6bd3b0452cb2d73987ce86aa5ff7269a86429c466bd7b1cdae64270`
>
> The exact owner-approved launch baseline is:
>
> `332ae2bc8e0ce4b694766d6d20759295d9267ec3`
>
> This authorization permits bootstrap and Phase A evidence work only. Phase B production/test implementation is not yet authorized.

| Decision or gate | Historical checkpoint and current disposition |
| --- | --- |
| M1-D01 exact five-file ceiling | Approved 25 July 2026; size and fixed-sGREEN inducibility were unproved at that checkpoint and are now proved by the exact preserved four-file feasibility candidate in Section 0 |
| M1-D02 exact-receipt invariant and amount identity | Approved 25 July 2026 |
| M1-D03 exact-length balance-read boundary | Approved 25 July 2026 |
| M1-D04 transient measurement mutex | Approved 25 July 2026 |
| M1-D05 one exact-transfer policy for every route | Approved 25 July 2026; the later owner disposition resolves the historical CreditRedeem reachability conflict by preserving dormancy |
| M1-D06 Robinhood-first and unchanged live Base | Approved 25 July 2026 |
| M1-D07 review, commit, and non-activation boundary | Approved 25 July 2026 |
| Bootstrap and Phase A | Authorized and performed; exact feasibility reproduced; complete evidence independently exact-hash approved and committed byte-for-byte at `2935f0e2...75f5`; **closed** |
| Phase B production/test implementation | **Not authorized; not started** |
| Gate 1 complete-file review | Pending; the preserved feasibility patch exists, but no official Phase B repository implementation patch exists because Phase B has not begun |
| Local implementation commit | Pending separate owner authorization |
| Reconciliation with current `rh` and S5 | Not applicable at the historical checkpoint; local, cached, and live `rh` now converge at `8e4a965f...7d98`, while final S5/current-`rh` reconciliation remains required before separate file-exact Phase B authorization |
| Gate 2 | Pending |
| Feature push / merge | Evidence-only feature push later separately authorized and performed at exact commit `2935f0e2...75f5`; merge remains unauthorized and unperformed |
| Deploy / configure / sign / broadcast / activate | Not authorized; not performed |
| M2 through M5 | Not authorized; not started |

The substantive M1 semantic authority was not silently reinterpreted. The
specification's earlier general `0 < R <= Q` design is superseded for M1 by
specification Section 23 and the controlling brief, which require `R == Q`.
The separate environment-authorization inference is the disclosed,
unratified deviation in Section 4.1.

### 1.1 Post-checkpoint independent review input

The first post-checkpoint review input is a 116-line chat attachment whose
informational digest is recorded above. It independently reproduced the
pre-review evidence record at SHA-256
`8814d60ea51382839367ff62aa24a188f50f8cfc2f93caf20e6599e1951c5d71`
and confirmed its baseline identity, sampled authority hashes, ancestry,
caller inventory, compiler artifacts, vault returns, primitive layout,
temporary-path cleanup, and CreditRedeem reachability finding.

The 89-line re-review chat attachment independently reproduced the resulting
1,620-line record at SHA-256
`363526e5fb13fd89bd546a6ccbe541bbd79a54f20505b93d6390fabccd511dc6`
and supplied N1-N8. This revision reconciles those findings too.

Neither attachment is stored in the repository. A future repository-only
auditor cannot independently reconstruct either attachment from its digest;
the digests are continuity aids, not durable provenance, authority, or review
approval. The material findings, source anchors, agent-run commands, and
dispositions are restated in this durable record so no gate relies on access
to the chat artifacts. Neither review is Gate 1. Where the first review reports
its own approximate M1-shaped compilation, this record continues to attribute
that result rather than absorb it as agent-generated evidence.

## 2. Bootstrap, identity, and topology

### 2.1 Integration baseline

Bootstrap began in `/Users/wigglez/dev/ripe-protocol`.

Before branch or worktree creation:

- the integration worktree was clean on `rh`;
- integration `HEAD`, local `refs/heads/rh`, cached
  `refs/remotes/origin/rh`, and live `refs/heads/rh` all resolved to
  `332ae2bc8e0ce4b694766d6d20759295d9267ec3`;
- the tree was `f67dc91e47331785837de879b6557b285aec3b1b`;
- local and remote branch `rh-track-8-m1-exact-receipt` did not exist;
- path `/Users/wigglez/dev/ripe-protocol-track-8-m1-exact-receipt` did not
  exist; and
- neither proposed target was deleted, reset, cleaned, reused, or overwritten.

The live-ref check was credential-free:

```bash
git ls-remote origin refs/heads/rh refs/heads/rh-track-8-m1-exact-receipt
```

It returned only:

```text
332ae2bc8e0ce4b694766d6d20759295d9267ec3 refs/heads/rh
```

The required integration ancestors were proved with
`git merge-base --is-ancestor <commit> <baseline>`:

| Authority/integration | Exact commit | Ancestor |
| --- | --- | --- |
| H-01 | `575d47b82055b42da2bddf1535d8076cd7cf4c63` | Yes |
| H-02 | `6c3052668555a7104ea12a7fb1a7c641c7e6b304` | Yes |
| Track 6 S1 | `f03e128905de395b7162110cab42582866e7ccc4` | Yes |
| Track 6 S2 | `454fbeb8e1bc1401fe1db0c44b98e9c487f3c504` | Yes |
| Track 6 S3 | `3e6e6f230169fc445d0b29454457480c62efd89a` | Yes |
| Track 8 M0 closure | `e1f14ddb030c5ce3f44d4cdd54e8c6daaad41369` | Yes |
| H-02 focused correction | `cb3fe7392c44613aaeec49bd2486369fe0da3556` | Yes |

The M0 packet records M0 closed and its historical M1 proposal as
unauthorized. The dated kickoff above is the later explicit authorization
required by the controlling brief, limited to bootstrap and Phase A.

### 2.2 Historical S5 disposition

At the 25 July review-correction snapshot, S5 had not integrated:

| Local S5 line | Head | Ancestor of launch baseline |
| --- | --- | --- |
| `rh-track-6-s5-ledger-guard` | `6652a10e4de2a74ca27be0da94be4331aeef18f6` | No |
| `rh-track-6-s5-ledger-guard-recreation` | `fc3fa82b5ab2982d9057fbe4f23a99b1e21110fe` | No |

The launch baseline's latest `contracts/data/Ledger.vy` commit is
`e2ea68d631efede500c1527c264d94d1cfa3a8a8` (`updated abis`). Therefore the
brief's “S5 integrated before kickoff” branch does not apply. Any later S5
integration or relevant Ledger/Teller behavior change requires the specified
stop, reconciliation, renewed owner baseline authorization, byte proof, and
additional regressions.

During post-review and re-review handoff validation, the recreation line
advanced twice from `017c931dd5953c9369fc83c0070bf2ba0b270f56`. Commit
`7f8f93c047debe5d4a756f301e69ffeca407e974` (`docs(rh): record S5 faucet and
owner-value provenance`) changes only
`docs/chains/rh/evidence/ledger-action-block-testnet-proof.md` (+181 lines).
The then-current head was merge commit
`fc3fa82b5ab2982d9057fbe4f23a99b1e21110fe`, with parents `7f8f93c...` and
the approved `rh` baseline `332ae2bc...`; relative to `7f8f93c...`, it adds
only `docs/chains/rh/track-8-m1-exact-receipt.md`.

Across both movements, the `contracts/data/Ledger.vy` bytes remain SHA-256
`00d86847273621857b80701be5faf7ca88ff9505f68671d5b6ab3c8b4ec972e0`
and the `contracts/core/Teller.vy` bytes remain the sealed
`51cf13e3c9d58262ba446a462332d8f4f181c07ce689031b2398c20137f04198`.
The recreation head was not an ancestor of `rh`; rather, `rh` was its second
parent and exact merge base. At that snapshot, S5 had moved and absorbed the
launch baseline but had not integrated into `rh` or changed relevant
Ledger/Teller behavior. Section 0.8 supersedes this historical status with
the current unintegrated but behavior-changing S5 worktree and the resulting
pre-Phase-B coordination stop.

### 2.3 Fresh branch and worktree

Only after the integration bootstrap passed, the prescribed command was run:

```bash
git -C /Users/wigglez/dev/ripe-protocol worktree add \
  -b rh-track-8-m1-exact-receipt \
  /Users/wigglez/dev/ripe-protocol-track-8-m1-exact-receipt \
  332ae2bc8e0ce4b694766d6d20759295d9267ec3
```

The resulting feature identity at creation was:

| Check | Result |
| --- | --- |
| Branch | `rh-track-8-m1-exact-receipt` |
| HEAD | `332ae2bc8e0ce4b694766d6d20759295d9267ec3` |
| Tree | `f67dc91e47331785837de879b6557b285aec3b1b` |
| Merge base with approved baseline | `332ae2bc8e0ce4b694766d6d20759295d9267ec3` |
| Ahead / behind approved baseline | `0 / 0` |
| Remote feature branch | Absent at creation; Section 0.8 records its later exact preservation |
| Integration worktree | Clean and unmodified |
| Feature worktree before this record | Clean |

The first sandboxed worktree-add attempt was denied because Git needed to
write the integration repository's `.git` administrative state. A read-only
check proved that it had created neither branch nor path. The same exact
command was then run with the required filesystem approval and succeeded. No
partial target was reused.

## 3. Read authorities and frozen hashes

All 22 controlling entries in brief Section 3 were read completely. “Every
production caller” required reading the seven direct-caller files plus the
upstream Contributor callback source used by HumanResources.

| Authority or frozen input | SHA-256 |
| --- | --- |
| `docs/chains/rh/track-8-m1-exact-receipt.md` | `34749b58c6bd3b0452cb2d73987ce86aa5ff7269a86429c466bd7b1cdae64270` |
| `docs/chains/rh/track-8-m0-owner-decision-packet.md` | `9fc44e47ae98bfe8e99c6554580215150461f17182ec92094588b7e650186496` |
| `docs/chains/rh/stock-token-m0-evidence.md` | `1ca5ec599e7bab406dd63e2d220251bb085ac2fbf9416bc8f4585632e283e4be` |
| `docs/chains/rh/stock-token-vault-change-specification.md` | `84e3368991803a92ffe2f82f47ef762045cdd9ed90ddd6a833e1531c866d4059` |
| `docs/chains/rh/stock-token-vault-change-validation-plan.md` | `675f31c7245243b286649b95f1d621c42fc9a662bc3f70cf446c76bb028325bf` |
| `docs/chains/rh/minimal-contract-change-reassessment.md` | `e29a1163b4cb1b4837ed8857775e9d1ea557bd3dc56213a594fa3fde0267987f` |
| `docs/chains/rh/robinhood-deployment-support-specification.md` | `1e3fc931ecab674e3ec61640f5c649458d1d6793eecb30465614455090312906` |
| `docs/chains/rh/robinhood-deployment-validation-plan.md` | `5ffbcfc14cb33e9a5cdc5f2c300cf3d1f9bae90fd90e14d04a408cbe274a94fb` |
| `docs/chains/rh/evidence/dependency-security-gate.md` | `5cb0d37aa50ab66b13d8389eecafd2bcd1f47dd7a3fd6fb6648e34470393fa87` |
| `contracts/core/Teller.vy` | `51cf13e3c9d58262ba446a462332d8f4f181c07ce689031b2398c20137f04198` |
| `contracts/core/TellerUtils.vy` | `c6351363db4f77318584dfc60b868f847ec894221ada37007b118881e254ecfe` |
| `interfaces/Vault.vyi` | `6769283fa780a63e1b2e2fc56b8ef51f3ff9b5883f4f1c4af8905fd0b20ffde7` |
| `contracts/vaults/SimpleErc20.vy` | `6b6794f1e5aaef3b53c3e931eb8fe3596aa3d44dc5d4dcc17f487340f5c89c22` |
| `contracts/vaults/RebaseErc20.vy` | `14fe0db39f96ffebbb8fa4b28fc6fe6fb173ab51095c2853885f4c37c8c41b42` |
| `contracts/vaults/StabilityPool.vy` | `04d0a7dddb8b562e8e384f61e6b83c76f5bc4a761070fd069f52d6ae8a4e22eb` |
| `contracts/vaults/RipeGov.vy` | `b949f3bed8d3a72970a2d841bc65b3e7fb3998f857f730f69b0e20e43f3d80c5` |
| `contracts/vaults/modules/BasicVault.vy` | `a21a33be9b805f5ce4fd42c66f976525032b92836149c74526be613dae79d89d` |
| `contracts/vaults/modules/SharesVault.vy` | `7a0ccbfc8c98f8274c3788ef577741053426b9a7ee6618cefb84768425989b3f` |
| `contracts/vaults/modules/StabVault.vy` | `4779448a8eef01363a697efc2cdd2eaec345afdb51349a57de220f743bb0e847` |
| `tests/core/teller/test_teller_deposit.py` | `9d1b24b3feae8b3cafa0afafaed862872a0f12892a6b34617f194c2553b2c390` |
| `tests/core/teller/test_teller_rebalance.py` | `cdcfd601704013f4aefee5c86d97aab57b4f5f21cf6bda20f24a56aa2019c4cf` |
| `tests/vaults/test_stock_token_vault_comparison.py` | `1f3723db14349f30a8b4990c8c993ef1a6add65c5b798871c86192aa7cd08c6c` |
| `scripts/abis/Teller.json` | `e5b696f0e22c2196806cd84f27a037d21ca567d702a357f3a61a574fd514e1f4` |
| `requirements.in` | `2523c04409946a6625e30e5e4aa4f711663924f4a674f4cfd5fee5b7bbb3b80d` |
| `requirements.txt` | `d2e12a6f0cfd128c3891634efafbba8305878bef7a7c5db33e25ebe93b0d2bce` |

Additional direct-caller and callback-chain hashes:

| Source | SHA-256 |
| --- | --- |
| `contracts/core/Deleverage.vy` | `eb28c2d22a695c3148acfc00b54507d3b2f3e4462aeae119ba4183d09832815b` |
| `contracts/core/HumanResources.vy` | `5f5712002ae22fed15829b8488c1cdf2e17cfef4f82ce66903b04fa562c749cb` |
| `contracts/core/Lootbox.vy` | `669c2857e2402ef0e8f9a508dd6f342426ffbd1affce11dd429e5b5b0129ae65` |
| `contracts/core/BondRoom.vy` | `b74f2592e2588620bd8e47043ca84aa64a7b0710c33b15a9c5781f6ace2f55fc` |
| `contracts/core/CreditEngine.vy` | `23129f8f6e87805bc47712d06f7ddf6c0de920866ad36ca78ee96e9c57ef96d8` |
| `contracts/core/CreditRedeem.vy` | `0567b9118868f7fc37a0e583580ab6c5cd1e85274747860a6394f1f1c4364c0e` |
| `contracts/modules/Contributor.vy` | `2b19c20b89acb5bb7c8f94c042cb7a5b43baf0421481d985850529f438576af9` |

## 4. Version-exact environment and baseline validation

### 4.1 Dependency identity and isolation

The ambient `ripe-lite` environment did not match the integrated requirements
versions: after
normalizing extras, 14 pins were missing and six pins differed
(`cbor2`, `idna`, `python-dotenv`, `requests`, `urllib3`, and `wheel`).

The implementation agent created the historical disposable environment below after
inferring authorization from the kickoff's instruction to perform every
dependency check. That inference did **not** satisfy brief Section 6, which
requires the agent to stop or obtain *explicit* owner authorization when the
active environment differs. This was an authority-process deviation. It is
disclosed rather than retroactively characterized as authorized. It is no
longer relied upon for exact-candidate feasibility: Section 0 records the
owner-authorized fresh exact-lock reconstruction and complete replay. No
repository dependency file was changed, and all task-specific temporary paths
were later removed.

Commands:

```bash
/Users/wigglez/.pyenv/versions/3.12.0/bin/python -m venv \
  /private/tmp/rh-m1-exact-lock.VWd4DN/candidate

/private/tmp/rh-m1-exact-lock.VWd4DN/candidate/bin/python \
  -m pip install --no-cache-dir -r requirements.txt
```

The task parent, Boa cache, and each pytest basetemp were mode `0700`.
The installed environment matched all 92 normalized version pins, had 93
installed distributions, zero missing pins, and zero version mismatches.
`pip check` returned
`No broken requirements found.` The canonical `pip freeze` stream SHA-256 was:

```text
6d8d1dfe85ac175030f2fd5248b4e8697ba0d2be9f8ad725412d8c7df980867f
```

`requirements.txt` contains 92 exact-version requirement lines and zero
`--hash=sha256:` entries; its generation header also lacks
`--generate-hashes`. Therefore this was a **version-exact** install, not an
artifact-exact or supply-chain-hash-exact install. The file SHA-256 seals the
requirements text, and the `pip freeze` digest seals the installed version
listing, but neither proves the downloaded wheel or source-distribution bytes.
That limitation belongs to H-01 and is not silently upgraded by this record.

| Tool | Exact version |
| --- | --- |
| CPython | `3.12.0` |
| pip | `23.2.1` |
| Vyper | `0.4.3+commit.bff19ea2` |
| Titanoboa | `0.2.7` |
| pytest | `8.4.2` |

All Boa/pytest commands used:

```text
WEB3_ALCHEMY_API_KEY unset
BASE_MAINNET_RPC_URL unset
BASE_SEPOLIA_RPC_URL unset
ROBINHOOD_MAINNET_RPC_URL unset
ROBINHOOD_TESTNET_RPC_URL unset
DEPLOYER_PRIVATE_KEY unset
TEST_PRIVATE_KEY unset
ETHERSCAN_API_KEY=local-placeholder
PYTHONPATH=.
```

Boa cache setup was explicit:

```python
from pathlib import Path
from boa.interpret import set_cache_dir
set_cache_dir(Path("/private/tmp/rh-m1-boa-cache.XgfTL6"))
```

No test requested a live RPC, fork, signer, private key, broadcast, or
transaction. The H-01 five bounded exceptions remain before their 15 August
2026 review and `2026-08-31T23:59:59Z` hard expiry; no invalidation trigger
was observed. This record does not claim that the 13 open dependency alerts
are closed.

### 4.2 Integration and feature replay

The pytest wrapper was:

```bash
env -u WEB3_ALCHEMY_API_KEY \
    -u BASE_MAINNET_RPC_URL \
    -u BASE_SEPOLIA_RPC_URL \
    -u ROBINHOOD_MAINNET_RPC_URL \
    -u ROBINHOOD_TESTNET_RPC_URL \
    -u DEPLOYER_PRIVATE_KEY \
    -u TEST_PRIVATE_KEY \
    ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. \
    /private/tmp/rh-m1-exact-lock.VWd4DN/candidate/bin/python -c \
    'from pathlib import Path; from boa.interpret import set_cache_dir; set_cache_dir(Path("/private/tmp/rh-m1-boa-cache.XgfTL6")); import pytest, sys; raise SystemExit(pytest.main(sys.argv[1:]))' \
    <pytest arguments>
```

| Gate | Integration worktree | Feature worktree |
| --- | --- | --- |
| H-01: `tests/deployment/test_dependency_gate.py -q` | 16 passed; 1.50 s | 16 passed; 1.49 s |
| S1: `tests/clock/test_clock_profiles.py -q` | 57 passed; 104.24 s | 57 passed; 105.67 s |
| S2 checker: `python scripts/check_block_clock_inventory.py --check` | Clean | Clean |
| S2: `tests/inventory/test_block_clock_inventory.py -q` | 60 passed; 25.47 s | 60 passed; 25.38 s |
| Three complete M1-owned test files | 138 passed; 54.46 s | 138 passed; 55.60 s |
| Full repository collection | 2,837 selected / 142 deselected / 2,979 total; exit 0 | Same exact counts; exit 0 |

Distinct basetemps:

| Run | Integration | Feature |
| --- | --- | --- |
| H-01 | `/private/tmp/rh-m1-pytest-h01-integration.G7nwxE` | `/private/tmp/rh-m1-pytest-h01-feature.yU48vH` |
| S1 | `/private/tmp/rh-m1-pytest-s1-integration.9Hzj0w` | `/private/tmp/rh-m1-pytest-s1-feature.xoATqi` |
| S2 | `/private/tmp/rh-m1-pytest-s2-integration.XEhgyj` | `/private/tmp/rh-m1-pytest-s2-feature.zv64Tg` |
| Three M1 files | `/private/tmp/rh-m1-pytest-target-integration.8tEsC2` | `/private/tmp/rh-m1-pytest-target-feature.fp3M0s` |
| Ordinary full collection | `/private/tmp/rh-m1-pytest-collect-integration.DSkRMi` | `/private/tmp/rh-m1-pytest-collect-feature.M7H1Ed` |
| Final count-only collection seal | Not repeated | `/private/tmp/rh-m1-pytest-collect-seal.Sk3Lz5` |

The final count-only collector printed:

```text
M1_COLLECTION_SELECTED=2837 DESELECTED=142 TOTAL=2979 EXIT=0
```

Per-file collection:

| Authorized test file | Collected |
| --- | ---: |
| `tests/core/teller/test_teller_deposit.py` | 26 |
| `tests/core/teller/test_teller_rebalance.py` | 22 |
| `tests/vaults/test_stock_token_vault_comparison.py` | 90 |
| **Total** | **138** |

Six focused current-vault semantic tests also passed in 104.20 s:

```text
tests/vaults/modules/test_basic_vault.py::test_basic_vault_deposit_validation
tests/vaults/modules/test_shares_vault.py::test_shares_vault_initial_deposit
tests/vaults/modules/test_stab_vault.py::test_stab_vault_initial_deposit
tests/vaults/modules/test_stab_vault.py::test_stab_vault_multiple_deposits
tests/vaults/test_ripe_gov_vault.py::test_ripe_gov_vault_initial_deposit_no_lock
tests/vaults/test_ripe_gov_vault.py::test_ripe_gov_vault_deposit_with_lock_duration
```

Their basetemp was
`/private/tmp/rh-m1-vault-semantics.5pi9TI`.

Every pytest run through the Boa-first wrapper emitted three
`PytestAssertRewriteWarning` messages because `_hypothesis_globals`,
`hypothesis`, and `boa` had already been imported before pytest plugin rewrite.
No executed selected test skipped or xfailed. The shell also emitted the
non-test warning `pyenv: cannot rehash: /Users/wigglez/.pyenv/shims isn't
writable`. `pip check` emitted a cache-disabled warning because the user's pip
cache was not writable. None changed a result.

Two auxiliary count-only command formulations failed before the successful
seal: one had a Python one-line class-definition syntax error and never
started pytest; one combined `-p no:terminal` with terminal-only `-q`, so
pytest exited 4 before collection. Their private paths were
`/private/tmp/rh-m1-pytest-collect-seal.FXsBXZ` and
`/private/tmp/rh-m1-pytest-collect-seal.TZtCBX`. They were diagnostics, not
gate runs, and are disclosed rather than hidden.

The clean S2 output was:

```text
CLOCK_INVENTORY_OK schema=1 production_occurrences=100 production_lines=95 production_files=17 bn_ids=32 bn_records=100 indirect_ids=1 cadence_candidates=455 seconds_unit_candidates=58 timestamp_ids=11 timestamp_occurrences=37 mixed_clock_functions=4 vyper_paths=92
CLOCK_INVENTORY_NONPROD mock=0/0/0 testing=0/0/0 test=31/29/5
CLOCK_INVENTORY_NONPROD_CADENCE mock=0 testing=0 test=159
```

At the historical checkpoint, a serial full test execution was treated as a
Gate 2 requirement and was not run. The later exact-feasibility work in
Section 0 did run the complete serial candidate suite: 2,884 passed and 142
deselected, with zero selected skips or xfails. That result does not begin or
replace official Gate 2.

## 5. A1: frozen Teller semantics

### 5.1 `Q` and validation

`TellerUtils.validateOnDeposit` is at `TellerUtils.vy:104-165`. It:

1. resolves the deposit configuration and requires protocol, asset, vault,
   user, and sender eligibility (`118-129`);
2. selects the depositor, or Teller when funds are already held (`131-135`);
3. caps the external request by that holder's token balance (`135`);
4. requires a nonzero result (`136`);
5. returns that result immediately for a valid Ripe Department (`138-140`);
6. otherwise applies vault/asset-count checks, per-user limit, global limit,
   and minimum balance (`142-163`); and
7. returns the capped amount at `165`.

Therefore:

```text
Areq = the external caller's raw amount argument
Q    = validateOnDeposit(...) return after holder balance and configuration caps
```

`Q` is not `Areq`. This preserves `max_value(uint256)`, depositor-balance
capping, per-user limits, global limits, and minimum-balance behavior.

### 5.2 Route entry points

| Route | Current lines | Existing nonreentrant section | `_deposit` details |
| --- | --- | --- | --- |
| `deposit` | `Teller.vy:229-240` | Yes | `msg.sender` custody; housekeeping in `_deposit` |
| `depositMany` | `243-251` | Yes | one `_deposit` per element; housekeeping once after loop |
| `depositFromTrusted` | `254-265` | No | requires Ripe Department; producer custody; limits bypassed; no housekeeping |
| `rebalance` deposit leg | `399-456` | Yes | deposits before withdrawal; housekeeping after both |
| `convertToSavingsGreenAndDepositIntoStabPool` | `626-642` | Yes | GREEN to Teller, ERC-4626 sGREEN to Teller, `_areFundsHereAlready=True` |
| `depositIntoGovVault` | `761-772` | No | RipeGov ID 2; sender prevalidated; optional lock; housekeeping |

`depositMany` deliberately discards each internal `_deposit` return and returns
`len(_deposits)` at `Teller.vy:251`. Its external return therefore cannot equal
each element's `Q`. T5 must preserve the batch return and prove each element
through its custody delta, successful internal `vaultResult == Q` check,
`TellerDeposit.amount == Q`, vault/user accounting, and complete-batch rollback.
It must not change the ABI merely to expose per-element return values.

### 5.3 Current `_deposit`

`Teller.vy:272-321` currently:

1. resolves vault address/ID (`285-288`);
2. reads Ledger participation data (`290-291`);
3. obtains `Q` into local `amount` from `validateOnDeposit` (`292`);
4. calls token `transfer(vaultAddr, Q)` when Teller already has the funds, or
   `transferFrom(depositor, vaultAddr, Q)` otherwise (`294-298`);
5. overwrites `amount` with
   `RipeGov.depositTokensWithLockDuration(..., Q, ...)` for a nonzero lock, or
   `Vault.depositTokensInVault(..., Q, ...)` otherwise (`300-304`);
6. adds first-time Ledger vault participation (`306-308`);
7. updates Lootbox points (`310-311`);
8. optionally performs housekeeping (`313-315`);
9. adds the PriceDesk snapshot (`317-318`);
10. emits the existing `TellerDeposit` with the overwritten `amount`
    (`320`); and
11. returns that same value (`321`).

There is no pre/post custody delta. The transfer's Boolean success and the
vault's aggregate-balance-derived return are the only current inbound checks.
The vault result is not separately compared with `Q`.

The approved mutex window begins **after** vault resolution, the Ledger data
read, and `validateOnDeposit`, and immediately before `C0`. The three
pre-window operations at `Teller.vy:288`, `291`, and `292` are all
`staticcall`s. `validateOnDeposit`'s configuration, holder-balance, and vault
data reads are likewise static calls. They cannot mutate Teller or open a
state-changing deposit measurement, so leaving them outside the transient
window is intentional and safe.

After successful validation, acquire the contract-local transient mutex before
`C0`; keep it through transfer, `C1`, `R == Q`, and the vault call; require
`vaultResult == Q`; clear immediately; then leave Ledger, Lootbox,
housekeeping, PriceDesk, event, and return ordering unchanged. This narrow
window also closes nested entry into `depositIntoGovVault` (and
`depositFromTrusted`) during an active measurement even though those two
external functions are not on Teller's broad `@nonreentrant` surface. It does
not add a whole-function reentrancy decorator or block unrelated post-window
actions.

M1-D02's `C1 >= C0` boundary is enforced semantically by Vyper's checked
unsigned evaluation of `C1 - C0 == Q`. When `C1 < C0`, the subtraction itself
reverts before the equality can succeed. No separate source assertion is
required, and the exact approved Teller source intentionally contains none.
Gate 1 must verify the checked-subtraction custody-decrease failure behavior
without changing the accepted Teller bytes.

### 5.4 Masking counterexample status and no-change risk

The baseline test
`test_short_received_second_deposit_is_reported_as_requested_amount`
(`test_stock_token_vault_comparison.py:587-636`) is a concrete **multi-user
preexisting-custody** masking counterexample for both SimpleErc20 and
RebaseErc20. It is not a donation counterexample:

- requested amount is `100 * 10**18`;
- the token delivers one unit short;
- hostile mode is enabled before Bob's first deposit, so Bob and Alice both
  receive one unit short; this is close to, but not identical to, T2's required
  “user B deposits normally, then user A receives short” setup;
- the first deposit reports `requested - 1`;
- a second one-unit-short deposit reports the full `requested` because the
  vault's aggregate preexisting balance satisfies `min(Q, balanceOf(vault))`;
- actual custody after both transfers is `2 * requested - 2`;
- SimpleErc20 nominal accounting is `2 * requested - 1`; and
- RebaseErc20 mints a share amount different from the correctly measured
  receipt.

At the historical checkpoint, the donation tests at
`test_stock_token_vault_comparison.py:318-405` prove allocation/view and
residue-recovery behavior only. They do **not** combine a prior donation with a
short later receipt. The required donation-masking baseline counterexample is
therefore missing from that original suite, and the exact T2 multi-user
sequence was not yet literal.

The preserved feasibility candidate later added and executed both exact
baseline counterexamples in the authorized comparison file, recorded custody,
user nominal credit, aggregate nominal accounting, and backing shortfall, and
proved atomic rejection under the exact Teller candidate. The official Phase
B repository implementation remains unstarted; if separately authorized, it
must preserve those candidate test semantics and Gate 1 must reproduce them
without changing Teller.

Without M1, earlier ordinary user custody is sufficient to mask a later short
receipt and allocate unbacked nominal balance or wrong shares. A prior donation
can create the same aggregate surplus; the later exact baseline replay
executed and recorded that donation-plus-short result. The 138-test historical
baseline passed the existing multi-user/preexisting-custody case as an
expected description of current behavior. The preserved candidate inverts
that outcome while the official Phase B worktree remains unchanged.

### 5.5 Required test inversion and suite blast radius

The existing two-parameter test above is the only suite use of short-transfer
mode 3:

```text
tests/vaults/test_stock_token_vault_comparison.py:613:
    stock_token.setUpgradeBehavior(3, sender=deploy3r)

contracts/mock/MockStockTokenControls.vy:80-88:
    mode 3 delivers one unit short and burns the difference
```

The baseline test treats M1's target defect as expected behavior. The
preserved feasibility candidate renamed/inverted it after capturing the exact
baseline outputs, so its SimpleErc20 and RebaseErc20 cases expect atomic
rejection and unchanged token, vault, user-accounting, share, event, and
downstream state. Any later authorized official Phase B implementation must
retain that inversion.

The baseline assertion remains durably reproducible after inversion from the
approved commit and sealed test-file hash:

```bash
git show \
  332ae2bc8e0ce4b694766d6d20759295d9267ec3:tests/vaults/test_stock_token_vault_comparison.py
```

At that commit the file SHA-256 is
`1f3723db14349f30a8b4990c8c993ef1a6add65c5b798871c86192aa7cd08c6c`,
and the two node IDs are the function at baseline lines 587-636 parameterized
as `simple-erc20` and `rebase-erc20`. Gate 1 must point to this immutable
baseline source plus the evidence-recorded baseline command/output; the
candidate test itself will correctly assert the opposite behavior.

The baseline Track 5 traceability header maps
`M-01 -> short-received second deposit` at baseline line 8. Because this is one
of the three authorized test files, the preserved feasibility candidate
updates that header in place to preserve the historical M-01 baseline mapping
while adding the M1 exact-receipt rejection mapping. No Track 5 documentation
or sixth file is needed.

The wider source/test search is favorable but not a full-suite result:

- `setUpgradeBehavior(3` has exactly the one suite occurrence above;
- `TRANSFER_GUARD_CASES` at baseline lines 950-954 uses modes 0, 1, and 2
  (pause, revert, and false return), all of which already fail closed;
- `MockFeeOnTransferErc20` appears only in
  `tests/probes/test_stock_token_transfer_probe.py:275` and
  `tests/core/endaoment/test_endaoment_funds.py:496`; neither invokes Teller
  `_deposit`;
- `MockReentrantErc20` appears only in the Endaoment transfer test at
  `tests/core/endaoment/test_endaoment_funds.py:572`; and
- the `stock_token` fixture is function-scoped and local to the authorized
  comparison file at baseline lines 44-51.

The A6 counts—90 comparison cases, 138 cases across the three M1-owned files,
and 2,837 selected repository tests—are **baseline seals**, not candidate count
targets. Mandatory M1 additions and the inversion will change names and likely
counts. Gate 1 and Gate 2 must recollect, report exact per-file and full-suite
candidate counts, and explain every delta instead of asserting count identity.
The exact feasibility candidate's complete serial execution selected and
passed 2,884 tests with 142 deselected; no selected test skipped or xfailed.
Gate 1 and Gate 2 must nevertheless reproduce the then-current official
implementation independently rather than treating that feasibility run as
their execution.

## 6. A2: complete trusted-caller and callback inventory

The fixed-string inventory command was:

```bash
rg -n -F 'depositFromTrusted(' contracts
```

The raw fixed-string search returned 16 lines: seven local Teller-interface
declarations, the Teller entry-point definition, and exactly eight production
`extcall` sites. The eight calls reconcile the eight M1-D05 producer
categories:

```text
contracts/core/Deleverage.vy:456
contracts/core/HumanResources.vy:426
contracts/core/Lootbox.vy:1160
contracts/core/BondRoom.vy:223
contracts/core/CreditEngine.vy:1207
contracts/core/CreditRedeem.vy:293
contracts/vaults/modules/StabVault.vy:756
contracts/vaults/modules/StabVault.vy:994
```

“Inside another nonreentrant action” is not “inside a Teller deposit
measurement window.” The proposed measurement mutex is set only by `_deposit`
and is separate from Teller's existing nonreentrant lock. Every reachable
trusted chain below first reaches `depositFromTrusted` with the proposed
measurement mutex clear.

### 6.1 Stability claim auto-deposit

- **Call site:** `StabVault.vy:982-995`.
- **Asset/custody:** the claimed or redeemed asset is already in StabVault;
  Teller pulls from StabVault's own custody.
- **Vault ID:** `MissionControl.getFirstVaultIdForAsset(asset)` at `989`.
- **Claim chain:** `Teller.claimFromStabilityPool` or
  `claimManyFromStabilityPool` (`650-679`) ->
  `StabVault.claimFromStabilityPool`/`claimManyFromStabilityPool`
  (`590-628`) -> `_claimFromStabilityPool` (`632-684`) ->
  `_handleAssetForUser` (`681`, then `982-995`) ->
  `Teller.depositFromTrusted`.
- **Redemption chain:** `Teller.redeemFromStabilityPool` or
  `redeemManyFromStabilityPool` (`687-722`) ->
  `StabVault.redeemFromStabilityPool`/`redeemManyFromStabilityPool`
  (`766-826`) -> `_redeemFromStabilityPool` (`839-924`) ->
  `_handleAssetForUser` (`924`, then `982-995`) ->
  `Teller.depositFromTrusted`.
- **Mutex/nonreentrancy:** both top-level Teller paths are inside Teller's
  existing `@nonreentrant`, but neither has entered `_deposit`; the first
  trusted callback therefore sees the measurement mutex clear. Multiple
  claims/redemptions are sequential, and each completed `_deposit` clears
  before the next.
- **Destination callback:** the supported vault implementations do not call
  back into StabVault while accounting the deposit. A nested deposit from a
  malicious token/vault would be rejected by the measurement mutex.
- **Robinhood launch:** arbitrary Stock auto-deposit remains disabled;
  permitted non-Stock configuration is shared-source behavior.
- **Planned authorized regression:** exact and failing claim-origin and
  redemption-origin auto-deposits in
  `tests/core/teller/test_teller_deposit.py`.

### 6.2 Stability RIPE reward

- **Call site:** `StabVault.vy:735-757`.
- **Asset/custody:** VaultBook mints RIPE for the claim reward into the calling
  StabVault flow; StabVault approves Teller, so Teller pulls from StabVault
  custody.
- **Vault ID:** fixed RipeGov ID `2`.
- **Chain:** the same Teller claim entry -> StabVault claim -> completed
  `_claimFromStabilityPool` -> `_handleClaimRewards` -> VaultBook mint ->
  `Teller.depositFromTrusted`.
- **Mutex/nonreentrancy:** the outer Teller claim is nonreentrant, but no
  `_deposit` measurement precedes the reward callback; the mutex is clear.
  Any earlier claim auto-deposit has returned and cleared before reward
  handling.
- **Destination callback:** RipeGov does not call back into StabVault during
  deposit accounting.
- **Robinhood launch:** named RIPE producer route only; future RIPE runtime
  proof remains a launch gate.
- **Planned authorized regression:** exact RIPE reward staking and lock
  duration in `tests/core/teller/test_teller_deposit.py`. The production RIPE
  fixture cannot induce a short or malformed receipt; see Section 6.9.

### 6.3 Deleverage

- **Call site:** `Deleverage.vy:400-460`, call at `456`.
- **Asset/custody:** governance/caller transfers the configured replacement
  asset into Deleverage at `452`; Deleverage approves Teller at `455`, so
  Teller pulls from Deleverage custody.
- **Vault ID:** `_depositVaultId` supplied to `swapCollateral`, after registry
  and LTV checks.
- **Chain:** authorized caller -> `Deleverage.swapCollateral` -> AuctionHouse
  withdrawal -> PriceDesk conversion -> transfer into Deleverage -> approval
  -> `Teller.depositFromTrusted`.
- **Mutex/nonreentrancy:** this chain does not originate in Teller and has not
  entered `_deposit`; the mutex is clear. `swapCollateral` is not in Teller's
  nonreentrant section.
- **Destination callback:** supported vaults do not call Deleverage while
  accounting the deposit.
- **Robinhood launch:** trusted Stock substitution remains disabled; exact
  shared-source non-Stock behavior must remain.
- **Planned authorized regression:** exact producer-custody pull, short and
  malformed atomic failure, unchanged approval/housekeeping in
  `tests/core/teller/test_teller_deposit.py`.

### 6.4 HumanResources

- **Call site:** `HumanResources.vy:415-428`, call at `426`.
- **Asset/custody:** HumanResources mints RIPE to itself at `422`, approves
  Teller at `425`, and Teller pulls from HumanResources custody.
- **Vault ID:** fixed RipeGov ID `2`.
- **Chains:** `Contributor.cashRipeCheck` (`180-199`) ->
  `HumanResources.cashRipeCheck`; or Contributor
  `initiateRipeTransfer`/`confirmRipeTransfer` (`211-255`) ->
  `_cashRipeCheck` -> HumanResources; the cancel-paycheck cliff path at
  `Contributor.vy:433-438` can also cash first.
- **Mutex/nonreentrancy:** Contributor initiate/confirm are nonreentrant in
  Contributor, but no Teller `_deposit` is active. Direct cash and cancel
  likewise enter the first Teller trusted deposit with the mutex clear.
- **Destination callback:** RipeGov does not call HumanResources/Contributor
  while accounting the deposit.
- **Robinhood launch:** named RIPE producer only.
- **Planned authorized regression:** direct and Contributor-origin exact
  cashing, lock duration, and producer custody in
  `tests/core/teller/test_teller_deposit.py`. The production RIPE fixture
  cannot induce a short or malformed receipt; see Section 6.9.

### 6.5 Lootbox auto-stake

- **Call site:** `Lootbox.vy:1134-1161`, call at `1160`.
- **Asset/custody:** Lootbox mints RIPE to itself at `1148`, approves Teller,
  and Teller pulls the stake amount from Lootbox custody.
- **Vault ID:** fixed RipeGov ID `2`.
- **Chain:** Teller `claimLoot`/`claimLootForManyUsers` (`735-753`) ->
  Lootbox `claimLootForUser`/`claimLootForManyUsers` (`224-252`) ->
  `_claimLoot` -> `_handleRipeMint` -> `Teller.depositFromTrusted`.
- **Mutex/nonreentrancy:** the outer Teller claim is nonreentrant but has not
  called `_deposit`; the first auto-stake sees a clear measurement mutex.
  Multi-user staking is sequential.
- **Destination callback:** RipeGov does not call Lootbox during deposit
  accounting.
- **Robinhood launch:** named RIPE producer only.
- **Planned authorized regression:** single/multi-user exact auto-stake,
  partial auto-stake, and lock behavior in
  `tests/core/teller/test_teller_deposit.py`. The production RIPE fixture
  cannot induce a short or malformed receipt; see Section 6.9.

### 6.6 BondRoom

- **Call site:** `BondRoom.vy:120-230`, call at `223`.
- **Asset/custody:** when lock duration is nonzero, BondRoom mints RIPE to
  itself at `221`, approves Teller, and Teller pulls from BondRoom custody.
- **Vault ID:** fixed RipeGov ID `2`.
- **Chain:** Teller `purchaseRipeBond` -> payment transfer to BondRoom ->
  `BondRoom.purchaseRipeBond` -> RIPE mint/approval ->
  `Teller.depositFromTrusted`.
- **Mutex/nonreentrancy:** the outer Teller purchase is nonreentrant but has
  not entered `_deposit`; the mutex is clear.
- **Destination callback:** RipeGov does not call BondRoom during deposit
  accounting.
- **Robinhood launch:** named RIPE producer only.
- **Planned authorized regression:** locked exact bond payout and
  producer-custody pull in `tests/core/teller/test_teller_deposit.py`. The
  production RIPE fixture cannot induce a short or malformed receipt; see
  Section 6.9.

### 6.7 CreditEngine call site: reachable borrower route, not a refund route

- **Call site:** `CreditEngine.vy:1181-1208`, call at `1207`.
- **Asset/custody:** CreditEngine mints/holds GREEN, deposits it into the
  ERC-4626 SavingsGreen with CreditEngine as recipient when
  `_shouldEnterStabPool=True`, approves Teller, and Teller pulls sGREEN from
  CreditEngine custody.
- **Vault ID:** fixed StabilityPool ID `1`.
- **Chain:** Teller `borrow` (`469-478`) -> `CreditEngine.borrowForUser`
  (`207-306`) -> `_handleGreenForUser(..., _shouldEnterStabPool, ...)`
  (`303`, `1181-1208`) -> SavingsGreen deposit ->
  `Teller.depositFromTrusted`.
- **Reachability boundary:** the only other `_handleGreenForUser` invocation is
  the repayment refund at `CreditEngine.vy:576`, and that invocation supplies
  literal `False` for `_shouldEnterStabPool`. Thus the trusted call is live
  only for borrower proceeds when the caller selects
  `_shouldEnterStabPool=True`; no CreditEngine repayment-refund/surplus path
  reaches it on this baseline.
- **Mutex/nonreentrancy:** the outer Teller borrow is nonreentrant and performs
  pre-borrow housekeeping, but no `_deposit` is active. The trusted callback
  sees the measurement mutex clear.
- **Destination callback:** StabilityPool does not call CreditEngine while
  accounting the deposit.
- **Robinhood launch:** named sGREEN producer only; runtime proof is later.
- **Planned authorized regression:** `borrow(...,
  _shouldEnterStabPool=True)` exact route and approvals to zero in
  `tests/core/teller/test_teller_deposit.py`. The production SavingsGreen
  fixture cannot induce a short or malformed receipt; see Section 6.9.
- **Authority reconciliation:** M0/M1 call this category “CreditEngine
  surplus.” The live source behavior is borrower-proceeds auto-deposit. The
  call site is not missing, but the owner should correct or explicitly affirm
  this nomenclature when resolving Section 6.8 so the later regression does
  not claim to test a refund/surplus path.

### 6.8 CreditRedeem source call site and reachability stop

- **Call site:** `CreditRedeem.vy:267-297`, syntactic call at `293`.
- **Intended asset/custody if reached:** CreditRedeem would deposit excess
  GREEN into SavingsGreen with itself as recipient, approve Teller, and Teller
  would pull sGREEN from CreditRedeem custody into StabilityPool ID `1`.
- **Only production invocation:** `CreditRedeem.vy:155` calls
  `_handleGreenForUser(_caller, totalGreenRemaining,
  _shouldRefundSavingsGreen, False, a)`.
- **Reachability proof:** the call at `293` is guarded by
  `if _shouldEnterStabPool` at `291`. The only invocation supplies literal
  `False`. Fixed-string search found no second invocation and no external
  entry for the internal helper.
- **Actual chain:** Teller `redeemCollateral` or
  `redeemCollateralFromMany` (`Teller.vy:504-540`) ->
  `CreditRedeem.redeemCollateralFromMany` (`126-155`) -> leftover call with
  literal `False` -> SavingsGreen is minted directly to `_caller` (or GREEN is
  transferred); `depositFromTrusted` is not reached.
- **Baseline test corroboration:**
  `tests/core/creditEngine/test_credit_redemptions.py:870-908` and
  `1715-1749` assert that excess redemption payment produces an increased
  `savings_green.balanceOf(alice)`, not a StabilityPool deposit.
- **Mutex/nonreentrancy:** the outer Teller redemption is nonreentrant, but
  the named trusted deposit route is unreachable, so no legitimate first
  mutex entry can be demonstrated.
- **Robinhood launch:** shared source, not a Stock route.
- **Required regression under the brief:** T7 says
  “CreditEngine/CreditRedeem sGREEN surplus routing remains live.” There is no
  live CreditRedeem route to preserve or regression-test.
- **Disposition:** **hard Phase A stop**. Treating the source branch as live
  would be false. Making it live requires a `CreditRedeem.vy` production
  change and corresponding test authority outside M1-D01; testing a modified
  inline copy would not prove the production chain. Reclassifying it as
  intentionally dormant requires an explicit revised authority and test
  expectation.

The defect predates the M1 brief. The integrated, owner-closed
`docs/chains/rh/stock-token-m0-evidence.md` labels
`CreditEngine.vy:1192-1207` and `CreditRedeem.vy:278-293` as “surplus” routes
at lines 289-290, then relies on the named
“CreditEngine/CreditRedeem surplus-to-Stability routes” at line 314. Correcting
that controlling M0 object is a separate documentation slice with its own
exact baseline, hash, owner authority, review, and integration. Once
integrated, M1 must stop and reconcile the changed M0 object under brief
Section 14; this M1 evidence-only correction does not edit or reopen M0 by
itself.

### 6.9 Per-producer failure inducibility

The baseline has no test reference to `depositFromTrusted`:

```bash
rg -n -F 'depositFromTrusted(' tests
# no matches
```

All T7 producer coverage is therefore greenfield. “Yes” below means an
adversarial short or malformed asset can be supplied to the real producer
chain without editing a fixture or adding a repository mock. “No” means the
real producer resolves a fixed, exact-behaving session fixture from
`Addys`/RipeHq; it does not mean the exact success route is untestable.

| Producer category | Production asset selection | Short/malformed failure inducible with the existing production fixture? | Phase B disposition within the three test files |
| --- | --- | --- | --- |
| Stability claim/redemption auto-deposit | Arbitrary configured claim asset | **Yes** | Use an inline hostile token in `test_teller_deposit.py`; prove both claim and redemption origins revert atomically |
| Stability RIPE reward | Fixed `a.ripeToken` | **No** | Prove the real RIPE exact/lock route; rely on T7's “where that behavior can be induced” qualifier for producer-specific failure |
| Deleverage | Caller/governance-supplied configured replacement asset | **Yes** | Use an inline hostile token and prove producer-custody rollback |
| HumanResources | Fixed `a.ripeToken` | **No** | Prove direct and Contributor-origin exact/lock routes |
| Lootbox | Fixed `a.ripeToken` | **No** | Prove exact single/multi-user and partial auto-stake behavior |
| BondRoom | Fixed `a.ripeToken` | **No** | Prove exact locked payout and producer custody |
| CreditEngine | Fixed `a.savingsGreen` | **No** | Prove the borrower-proceeds exact route and approvals returning to zero |
| CreditRedeem | Fixed `a.savingsGreen`, but branch is unreachable | **N/A** | Recommended revised authority is a dormancy invariant, not a fabricated failure route |

The fixed token addresses are not literally immutable in the test EVM:
`RipeHq.startAddressUpdateToRegistry`/`confirmAddressUpdateToRegistry`
(`contracts/registries/RipeHq.vy:159-168`) can replace registry IDs 2 or 3
after the timelock, and
`tests/core/lootbox/test_underscore_rewards.py:47-57` demonstrates that update
pattern. An inline test-only RIPE or ERC-4626 replacement can therefore make a
fixed-token failure inducible without editing `tests/conf_core.py`. The exact
feasibility candidate later executed the required T8 sGREEN substitution
through this authorized seam. That result does not upgrade the other fixed
T7-token rows to “Yes”; they remain exact-success coverage under T7's express
“where that behavior can be induced” qualifier.

T8 is stricter: it unconditionally requires a short or malformed sGREEN
transfer on the Teller-held route. Source inspection shows the same test-local
RipeHq ID-2 substitution can be defined inline in
`test_teller_deposit.py`. The preserved feasibility candidate executes that
exact setup, induces the short-sGREEN failure, and proves complete atomic
reversion without a production or repository-mock change. Official Phase B
remains unstarted, and Gate 1 must reproduce this result.

### 6.10 Transfer-source versus destination-vault identity

The M1 delta intentionally computes zero when the transfer source is already
the destination vault: `C1 == C0`, so `R == 0 != Q`. The current source
topology is safe for the intended reachable producer routes, subject to the
configuration conditions below:

| Producer | Transfer source | Destination | Source/destination disposition |
| --- | --- | --- | --- |
| Stability auto-deposit | Calling StabVault | First configured vault for claim asset | Standard StabilityPool is vault ID 1, and `_canPerformAutoDeposit` rejects IDs 0 and 1 at `StabVault.vy:1008-1010`; distinct for the baseline topology |
| Stability RIPE reward | Calling StabVault | RipeGov ID 2 | Distinct component roles and baseline addresses |
| Deleverage | Deleverage | Caller-selected registered vault | Distinct baseline addresses; source code does not enforce cross-registry inequality |
| HumanResources | HumanResources | RipeGov ID 2 | Distinct component roles and baseline addresses |
| Lootbox | Lootbox | RipeGov ID 2 | Distinct component roles and baseline addresses |
| BondRoom | BondRoom | RipeGov ID 2 | Distinct component roles and baseline addresses |
| CreditEngine | CreditEngine | StabilityPool ID 1 | Distinct component roles and baseline addresses |
| CreditRedeem | CreditRedeem | StabilityPool ID 1 | Intended addresses are distinct, but the route is dormant |

The StabVault guard is keyed to the hard-coded ID 1, not to
`vaultAddr != self`. A second StabVault registered at another ID could select
itself and is not protected by that guard. Before any deployment/configuration,
the route matrix must assert the actual transfer source differs from the
actual destination for every enabled route. Phase B must also prove that an
explicit self-transfer attempt reverts atomically under M1 rather than
silently crediting preexisting custody.

## 7. A3: current vault return semantics

| Supported vault route | Source proof | Exact-receipt result |
| --- | --- | --- |
| SimpleErc20 / BasicVault | `BasicVault.vy:24-39` takes `min(Q, balanceOf(vault))`, credits it, and returns it; `SimpleErc20.vy:54-64` returns that deposit amount | If `C1=C0+Q`, then `balanceOf(vault)=C1>=Q`, so the return is exactly `Q` |
| RebaseErc20 / SharesVault | `SharesVault.vy:26-46` derives `depositAmount=min(Q,totalAssetBalance)`, separately calculates `newShares`, and returns both; `RebaseErc20.vy:58-70` returns only `depositAmount` | Deposit amount is `Q`; shares may differ and are not the external amount |
| StabilityPool / StabVault | `StabVault.vy:110-141` derives `depositAmount=min(Q,totalAssetBalance)`, separately values/mints shares, and returns both; `StabilityPool.vy:71-84` returns only `depositAmount` | Deposit amount is `Q`; value-derived shares may differ |
| RipeGov no lock | `RipeGov.vy:133-140` delegates to `_depositTokensInRipeGovVault`; `157-179` delegates to SharesVault and returns `depositAmount` | Returns `Q`; shares/lock data are separate |
| RipeGov with lock | `RipeGov.vy:145-153` delegates to the same internal routine with lock duration | Returns `Q`; lock duration does not replace the token-amount return |

The six focused tests listed in Section 4.2 passed. The complete three-file
baseline also passed existing SimpleErc20/RebaseErc20 exact lifecycle cases.
No currently supported vault legitimately returns a deposit amount other than
`Q` after an exact receipt. The `vaultResult == Q` assertion is already
present in the exact preserved feasibility candidate and passed every
supported-vault and complete-suite reproduction. Official Phase B repository
implementation remains unstarted; no weakening is required or authorized.

## 8. A4: exact-transfer compatibility reconciliation

### 8.1 Robinhood launch graph

No new runtime fact was invented and no RPC was contacted. This section
consumes the integrated M0 matrix.

| Asset/class | Integrated exact-transfer evidence | M1 route disposition |
| --- | --- | --- |
| AAPL Stock Token | Exact base-unit deposit/withdraw at RH-T2-01; refreshed identity parity at RH-M0-01 | Future ordinary deposit only through one enabled vault; every trusted/Department Stock route remains prohibited |
| Other Stock Tokens | No initial-launch row | Omitted; each later proxy needs an independent complete row |
| RIPE | New Ripe artifact; no Robinhood runtime exists | RipeGov ordinary route plus only StabVault, HumanResources, Lootbox, and BondRoom named producers; later runtime/composition proof |
| sGREEN | New Ripe artifact; no Robinhood runtime exists | GREEN conversion and only named CreditEngine/CreditRedeem source dispositions; no CCIP; later runtime/composition proof. CreditRedeem's current reachability conflict is Section 6.8 |
| GREEN | New Ripe artifact; no Robinhood runtime exists | Wrapper input to SavingsGreen/core debt token; no raw-GREEN trusted `_deposit`; later proof |
| Canonical USDG | Exact six-decimal, fee-free, non-rebasing transfer under pinned runtime | PSM and future GREEN/USDG LP only; never ordinary Teller collateral; trusted routes omitted |
| GREEN/USDG LP | Does not yet exist | Future ordinary deposit only, `ltv=0`; trusted routes omitted; DEX/pool/oracle/runtime remain hard launch gates |
| RIPE/WETH LP | Does not yet exist | Future ordinary deposit only, `ltv=0`; trusted routes omitted; DEX/pool/oracle/runtime remain hard launch gates |
| Any other asset | Not approved | Omitted until a complete independent row is approved |

AAPL's consumed identity condition is:

| Field | M0 authority |
| --- | --- |
| Chain / block | chain ID `4663`; block `18,538,327`; hash `0x1f3920aded6d22dd6afc0234d7b0088bdbdfcdc98bd40cddb8e6dbd8e8889eba` |
| Proxy | `0xaF3D76f1834A1d425780943C99Ea8A608f8a93f9` |
| Proxy runtime hash | `0x6c1fdd40002dcb440c7fff6a84171404d279ccb057803b65826f7546acd65630` |
| Beacon | `0xe10b6f6B275de231345c20D14Ab812db62151b00` |
| Beacon runtime hash | `0x8b465c0b53a2ba499566e9b4ca67d8c90ed6131743df806a570d156956a7e90e` |
| Implementation | `0xb35490d6f9163DE4F80d88dc75c3516eb64C5aE2` |
| Implementation runtime hash | `0xdc07e86ee482f99641bdafb9a0d772846b167401e094d90a666b94dbdcd1eec7` |
| Pauses | global/token/oracle `false/false/false` |
| Exact fork amount | `1000000000000000` base units at RH-T2-01 |

Compatibility remains conditional on unchanged implementation and transfer
controls. Pause, blocklist, burn, multiplier, beacon upgrade, and issuer
authority remain residual risks. Identity parity is not a fresh fork.

Canonical USDG remains:

```text
proxy:          0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168
implementation: 0x68184C449E1a8f34fA18d289737129FD27B66f8F
proxy hash:     0x864cc9ad53b338b82da1f7cab85ab0b3d5c8861acb422b6fec63cf36234f36a6
impl hash:      0x3a551ac5c744af57e68a1d1431ac403c0f516ffd7d224a75746aee11fc4f3baf
pinned block:   17,572,269
```

### 8.2 Complete Base ID-3 reconciliation

The count comes from the M0 Section 10 checked closure row and is reconciled
against every row in underlying Section 6, not a partial grep.

| # | Asset | Custody/config at BASE-M0-01 | Forward-source classification |
| ---: | --- | --- | --- |
| 1 | USDC | `C=N=0`; deposit/support false | Conditional exact controlled proxy; route proof pending |
| 2 | cbBTC | funded; `C=N`; deposit/support true | Conditional exact controlled proxy; route proof pending |
| 3 | WETH | funded; `C=N+1`; deposit/support true | Fixed exact WETH units; one-unit solvent surplus; route proof pending |
| 4 | cbDOGE | funded; `C=N`; deposit/support true | Conditional exact controlled proxy; route proof pending |
| 5 | uSOL | funded; `C=N`; deposit/support true | Conditional exact beacon proxy; route proof pending |
| 6 | Morpho Spark USDC | `C=N=0`; inactive | Exact share units; underlying value changes; route proof pending |
| 7 | AERO | funded; `C=N`; deposit/support true | Fixed exact units with minter; route proof pending |
| 8 | Moonwell AERO | `C=N=0`; inactive | Exact cToken units; upgrade/seize/value risk; route proof pending |
| 9 | cbXRP | `C=N=0`; deposit/support true | Conditional exact controlled proxy; route proof pending |
| 10 | WELL | funded; `C=N`; deposit/support true | Conditional exact upgradeable token; route proof pending |
| 11 | VIRTUAL | funded; `C=N`; deposit/support true | Conditional exact bridge token; route proof pending |
| 12 | VVV | `C=N=0`; inactive | Fixed exact units with mint control; route proof pending |
| 13 | DEGEN | `C=N=0`; deposit/support true | Exact current units with pause/self-burn; route proof pending |
| 14 | Moonwell cbETH | `C=N=0`; inactive | Exact cToken units; upgrade/seize/value risk; route proof pending |
| 15 | cbETH | funded; `C=N`; deposit/support true | Conditional exact bridge proxy; route proof pending |
| 16 | Moonwell USDC | `C=N=0`; inactive | Exact cToken units; upgrade/seize/value risk; route proof pending |
| 17 | Morpho Moonwell USDC | `C=N=0`; inactive | Exact share units; underlying value changes; route proof pending |
| 18 | Morpho Seamless USDC | `C=N=0`; inactive | Exact share units; underlying value changes; route proof pending |
| 19 | Fluid USDC | `C=N=0`; inactive | Exact fToken units; share value changes; route proof pending |
| 20 | Euler USDC | `C=N=0`; inactive | Exact share units; beacon/value risk; route proof pending |
| 21 | Moonwell cbBTC | `C=N=0`; inactive | Exact cToken units; upgrade/seize/value risk; route proof pending |
| 22 | Morpho Moonwell WETH | `C=N=0`; inactive | Exact share units; underlying value changes; route proof pending |
| 23 | Morpho Seamless WETH | `C=N=0`; inactive | Exact share units; underlying value changes; route proof pending |
| 24 | Euler WETH | `C=N=0`; inactive | Exact share units; beacon/value risk; route proof pending |
| 25 | Morpho Moonwell cbBTC | `C=N=0`; inactive | Exact share units; underlying value changes; route proof pending |
| 26 | sUSDe | funded; `C=N`; deposit/support true | Conditional exact transfer; blacklist redistribution can create an independent deficit; route proof pending |
| 27 | wrapped superOETH | `C=N=0`; deposit false/support true | Exact wrapped-share units; upgrade/value risk; route proof pending |

All nine custody-positive rows (2, 3, 4, 5, 7, 10, 11, 15, 26) were nominally
solvent at the M0 pin. No row was shown to charge an ordinary transfer fee or
rebase units on transfer under its inspected source class. All 27 per-route
fork proofs remain incomplete, so every row blocks a future Base forward
Teller cutover until separately closed. No Base-only row blocks Robinhood
while Base retains its deployed old Teller. M1 does not deploy, migrate,
rewire, or remediate Base.

No enabled existing Robinhood token in the frozen launch graph is classified
as fee-on-transfer, rebasing-on-transfer, short-receipt, or unknown. New Ripe
artifacts and LPs remain later proof obligations, not fabricated Phase A
runtime rows.

## 9. A5: pinned Vyper primitive proof

Temporary probes were created only under
`/private/tmp/rh-m1-primitives.4KRqjh` and were never repository files:

| Probe | SHA-256 |
| --- | --- |
| `ExactReceiptPrimitiveProbe.vy` | `4f0db3f692a9bbc6cdc48191278d14ca0ea444374060394d0684b12ca0ef43b5` |
| `ExactReceiptPrimitiveObserver.vy` | `376993f46986f7428ad52072f06973164d77d8c9ae999b95386e1c43f0940baf` |
| `run_probe.py` | `e123e81d65a6cf7c7816354337b82dee6422e2a4856161f01a6aed5e0003c232` |

Command:

```bash
env -u WEB3_ALCHEMY_API_KEY \
    -u BASE_MAINNET_RPC_URL \
    -u BASE_SEPOLIA_RPC_URL \
    -u ROBINHOOD_MAINNET_RPC_URL \
    -u ROBINHOOD_TESTNET_RPC_URL \
    -u DEPLOYER_PRIVATE_KEY \
    -u TEST_PRIVATE_KEY \
    ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. \
    /private/tmp/rh-m1-exact-lock.VWd4DN/candidate/bin/python \
    /private/tmp/rh-m1-primitives.4KRqjh/run_probe.py
```

| Required primitive | Proof |
| --- | --- |
| Contract-local transient Boolean | Vyper compiled `receiptMeasurementActive: transient(bool)`; layout contains transient slot 1 and no persistent storage |
| Static raw balance read | `raw_call(..., max_outsize=33, is_static_call=True)` compiled and returned exact data |
| Exact response length | exact 32 bytes accepted; 0-byte and 31-byte responses reverted |
| Oversized rejection without truncation | a 64-byte responder produced the 33-byte capped observation; `len(response) != 32` reverted |
| 32-byte `uint256` decode | decoded `57896044618658097711785492504343953926634992332820282019728792003956688276757`, proving the high bit is handled as unsigned |
| Transient rollback on revert | a reverting external self-call set the transient Boolean; the caller caught failure and observed false in the same transaction |
| Clear before later external calls | observer invoked after clear recorded `measurementActive == false` |
| Nested measurement rejection | observer attempted `measure` while active; raw call failed; outer call then cleared successfully |

Probe output:

```text
exact-length rejection short-31: PASS
exact-length rejection oversized-64: PASS
exact-length rejection empty-0: PASS
transient rollback within one transaction: PASS
mutex cleared before later external call: PASS
nested measurement rejection: PASS
primitive probe suite: 8 assertions/groups PASS
```

The probe layout was:

```json
{"transient_storage_layout":{"receiptMeasurementActive":{"n_slots":1,"slot":1,"type":"bool"}}}
```

Its canonical layout SHA-256 was
`8611256115192c1058d70efd5d883885e0acdc4ac48bee6e0a80a787551cf590`.
The explicit probe test endpoints are not proposed production selectors. A
plain contract-local variable adds no getter unless marked `public`; the M1
helper can be internal and the mutex can be private transient state inside
`Teller.vy`. No interface, persistent slot, second production file, or
dependency change is needed for the primitive itself.

## 10. A6: baseline artifact and behavior seal

### 10.1 Compiler and artifact identity

Commands:

```bash
/private/tmp/rh-m1-exact-lock.VWd4DN/candidate/bin/vyper --version
/private/tmp/rh-m1-exact-lock.VWd4DN/candidate/bin/vyper \
  -p . -f integrity,settings contracts/core/Teller.vy
/private/tmp/rh-m1-exact-lock.VWd4DN/candidate/bin/vyper \
  -p . -f combined_json contracts/core/Teller.vy
```

| Field | Baseline value |
| --- | --- |
| Primary compiler input | `contracts/core/Teller.vy` |
| Teller source SHA-256 | `51cf13e3c9d58262ba446a462332d8f4f181c07ce689031b2398c20137f04198` |
| Compiler | Vyper `0.4.3+commit.bff19ea2` |
| Vyper integrity | `ae5ab1888fa6a7136fb113d6969acbb145b78468307f0f0c6118c3f9ff3ce12f` |
| Settings | `{"experimental_codegen":false,"optimize":"codesize"}` |
| Canonical settings SHA-256 | `1bff982534eddbbfdfe01e01229e3c4d6016d0eec6dbe240aa4b49a1cd05f99f` |
| Creation bytecode length | 24,141 bytes |
| Creation bytecode SHA-256 | `0c20af1d404d46d28a733bcf9b4b2ec1f258231a4403dceb6e76206b0b52f897` |
| Creation bytecode Keccak-256 | `0xf79a7babb06bf514bd1f72a90fa87be9a242cc4a175af64b31cc3966095d8467` |
| Runtime bytecode length | 23,906 bytes |
| Runtime bytecode SHA-256 | `3736bc669f225b463219defe27fc4627db96400093dab45ff081582ccec881f4` |
| Runtime bytecode Keccak-256 | `0x19b8c58290b9736fe6336df7b003e70a85792b5f96c621810eed9f186ba19d53` |
| Generated ABI entries | 131: 123 functions, 7 events, 1 constructor |
| Generated ABI canonical SHA-256 | `319169528ec22722c7f912a0f93d3a0560feb17c2d6349770c17a643e1f00e20` |
| Committed ABI raw-file SHA-256 | `e5b696f0e22c2196806cd84f27a037d21ca567d702a357f3a61a574fd514e1f4` |
| Committed ABI canonical SHA-256 | `319169528ec22722c7f912a0f93d3a0560feb17c2d6349770c17a643e1f00e20` |
| Generated versus committed ABI | Semantically identical |
| Complete layout canonical SHA-256 | `dac3acdb8263039970917f14410e3a284cc71f71614b094bb938d4ba4e9f94d6` |

No generated output was written into the repository.

#### 10.1.1 EIP-170 runtime-size budget

The EIP-170 deployed-runtime ceiling is 24,576 bytes. The sealed baseline is
23,906 bytes, leaving only **670 bytes** (2.73% of the ceiling):

| Measurement | Runtime bytes | Delta from baseline | Remaining EIP-170 headroom |
| --- | ---: | ---: | ---: |
| Sealed baseline | 23,906 | 0 | 670 |
| Independent reviewer's deliberately minimal M1-shaped approximation | 24,280 | +374 | 296 |
| Agent-run disclosed scratch approximation | 24,275 | +369 | 301 |
| Exact preserved feasibility candidate | **24,152** | **+246** | **424** |

The exact preserved candidate consumes 246 of the baseline's remaining 670
bytes, or **36.7% of the prior reserve**, and leaves 424 bytes. The owner's
bounded acceptance applies only to exact Teller source SHA-256
`4afc6ce1ccf21cb65e04ce3c56fedcf60bb79cba8e7dc51fd855a1f1f82bd909`.
Any source-byte change invalidates the measurement and acceptance. Official
Phase B repository implementation has not begun.

The historical reviewer described its approximation as one transient Boolean, one
internal exact-length static `raw_call` balance helper used twice, and the
scratch assertions shown below, compiled with pinned Vyper
`0.4.3+commit.bff19ea2`. No exact probe source accompanied the review input, so
the 24,280-byte result remains attributed reviewer evidence. It is superseded
for decision purposes by the exact candidate's independently reproduced
24,152-byte runtime.

The re-review correctly identified that brief Section 7 permits temporary
artifact generation and A5 expressly requires compiler probes. A
compiler-only scratch approximation therefore did not require a new owner
approval. The agent copied the sealed baseline Teller to a mode-`0700`
`/private/tmp/rh-m1-size-probe.*` directory, applied only the disclosed
size-shape below, compiled it with ambient pinned Vyper
`0.4.3+commit.bff19ea2`, and removed the directory:

```diff
+receiptMeasurementActive: transient(bool)
+
+@view
+@internal
+def _exactBalance(_asset: address, _holder: address) -> uint256:
+    response: Bytes[33] = raw_call(
+        _asset,
+        concat(method_id("balanceOf(address)"), convert(_holder, bytes32)),
+        max_outsize=33,
+        is_static_call=True,
+    )
+    assert len(response) == 32
+    return extract32(response, 0, output_type=uint256)
+
 def _deposit(...):
     amount: uint256 = staticcall TellerUtils(...).validateOnDeposit(...)
+    assert not self.receiptMeasurementActive
+    self.receiptMeasurementActive = True
+    custodyBefore: uint256 = self._exactBalance(_asset, vaultAddr)
     # unchanged transfer / transferFrom of amount
+    custodyAfter: uint256 = self._exactBalance(_asset, vaultAddr)
+    assert custodyAfter >= custodyBefore
+    assert custodyAfter - custodyBefore == amount
+    vaultResult: uint256 = 0
     if _lockDuration != 0:
-        amount = extcall RipeGovVault(...).depositTokensWithLockDuration(...)
+        vaultResult = extcall RipeGovVault(...).depositTokensWithLockDuration(...)
     else:
-        amount = extcall Vault(...).depositTokensInVault(...)
+        vaultResult = extcall Vault(...).depositTokensInVault(...)
+    assert vaultResult == amount
+    self.receiptMeasurementActive = False
```

The scratch source SHA-256 was
`b4678bb6518b96892ce4687e61d5ca1d0cf0fd14301c11f095dc11c474e20c01`.
Its runtime was 24,275 bytes, five bytes smaller than the reviewer's
unpublished approximation, and its layout kept persistent slot 0 unchanged,
kept the compiler nonreentrant key at transient slot 0, and added only
`receiptMeasurementActive` at transient slot 1.

The scratch diff above is retained as historical approximation provenance.
Unlike the exact approved source, it included a separate
`custodyAfter >= custodyBefore` assertion. M1-D02 does not require that
redundant source assertion: the exact candidate enforces the same failure
boundary through Vyper's checked unsigned subtraction, and Gate 1 must verify
that `C1 < C0` reverts.

Commands and material output:

```bash
set -o pipefail
vyper --version
# 0.4.3+commit.bff19ea2

vyper -p /Users/wigglez/dev/ripe-protocol-track-8-m1-exact-receipt \
  -f bytecode_runtime \
  /private/tmp/rh-m1-size-probe.I6k2ND/TellerSizeProbe.vy |
  awk '{print (length($0)-2)/2}'
# 24275

vyper -p /Users/wigglez/dev/ripe-protocol-track-8-m1-exact-receipt \
  -f layout \
  /private/tmp/rh-m1-size-probe.I6k2ND/TellerSizeProbe.vy
```

```json
{
  "storage_layout": {
    "deptBasics": {
      "isPaused": {"type": "bool", "n_slots": 1, "slot": 0}
    }
  },
  "transient_storage_layout": {
    "receiptMeasurementActive": {"type": "bool", "n_slots": 1, "slot": 1},
    "$.nonreentrant_key": {
      "type": "nonreentrant lock",
      "slot": 0,
      "n_slots": 1
    }
  }
}
```

The first scratch decode used `convert(response, uint256)` and failed to
compile with `TypeMismatch: Can't convert Bytes[33] to uint256`; replacing it
with the already-proved exact `extract32(..., output_type=uint256)` primitive
produced the result above. The failed diagnostic did not produce a usable size
and is not hidden.

This scratch probe was deliberately not the exact candidate: names, dev
revert strings, source placement, and final reviewed bytes can change code
size. It is retained only as chronology. Section 0 records the later
owner-authorized, exact-lock construction, 24,152-byte runtime, complete test
execution, and fixed-sGREEN construction for the exact preserved feasibility
candidate. Official Phase B repository implementation and Gate 1 remain
unauthorized and unstarted.

The baseline count was rechecked during review correction without changing a
file:

```bash
vyper --version
# 0.4.3+commit.bff19ea2

vyper -p . -f bytecode_runtime contracts/core/Teller.vy |
  awk '{print (length($0)-2)/2}'
# 23906
```

The historical repository search found no EIP-170/code-size assertion in
`scripts/` or `tests/`. The owner now requires official Phase B, if separately
authorized, to add the guard inside an already authorized M1 test file. Gate 1
and Gate 2 must each compile the exact approved `Teller.vy` with the identical
pinned compiler and settings, record its exact runtime byte count and
remaining headroom, and assert both:

```text
len(deployedRuntimeBytecode) <= 24_576
len(deployedRuntimeBytecode) <= 24_152
```

Any count above 24,576 violates EIP-170; any growth above the accepted 24,152
bytes fails the approved-source tripwire until separately reviewed and
approved. The optimizer/settings may not be changed to recover space because
T11 requires identical settings. Exact four-file feasibility is proved by the
preserved candidate, but official implementation and Gate 1 have not begun.
Any M2-M5 or later maintenance proposal that touches Teller inherits no
approval from M1 and must repeat compilation, size measurement, complete
tests, and independent review.

### 10.2 Persistent and transient baseline layout

```json
{
  "code_layout": {
    "addys": {
      "RIPE_HQ_FOR_ADDYS": {
        "length": 32,
        "offset": 0,
        "type": "address"
      }
    },
    "deptBasics": {
      "CAN_MINT_GREEN": {
        "length": 32,
        "offset": 32,
        "type": "bool"
      },
      "CAN_MINT_RIPE": {
        "length": 32,
        "offset": 64,
        "type": "bool"
      }
    }
  },
  "storage_layout": {
    "deptBasics": {
      "isPaused": {
        "n_slots": 1,
        "slot": 0,
        "type": "bool"
      }
    }
  },
  "transient_storage_layout": {
    "$.nonreentrant_key": {
      "n_slots": 1,
      "slot": 0,
      "type": "nonreentrant lock"
    }
  }
}
```

The only persistent Teller slot is inherited `deptBasics.isPaused` at slot 0.
The existing compiler-managed nonreentrant key is transient slot 0. The exact
preserved candidate adds only `receiptMeasurementActive` at transient slot 1
and leaves persistent layout unchanged, as reproduced in Section 0.5.
Official Phase B has not begun; Gate 1 must independently reproduce that
invariance from the exact approved Teller bytes.

### 10.3 Existing nonreentrant surface

The exact baseline has 23 `@nonreentrant` external functions:

```text
deposit (decorator line 229)
depositMany (243)
withdraw (329)
withdrawMany (345)
rebalance (399)
borrow (467)
repay (484)
redeemCollateral (502)
redeemCollateralFromMany (524)
liquidateUser (551)
liquidateManyUsers (564)
buyFungibleAuction (580)
buyManyFungibleAuctions (600)
convertToSavingsGreenAndDepositIntoStabPool (626)
claimFromStabilityPool (648)
claimManyFromStabilityPool (666)
redeemFromStabilityPool (685)
redeemManyFromStabilityPool (705)
claimLoot (733)
claimLootForManyUsers (746)
adjustLock (775)
releaseLock (791)
purchaseRipeBond (812)
```

`depositFromTrusted` and `depositIntoGovVault` are intentionally not on this
existing surface. M1-D04 does not authorize adding them to the general
nonreentrant decorator; it authorizes only the narrow measurement mutex.

### 10.4 Event signatures and topics

| Event signature | Topic 0 |
| --- | --- |
| `DepartmentFundsRecovered(address,address,uint256)` | `0xc2bfa18928a62b432789c9dda1f6bb4c519799a6b51f4dc2f74374e8f34207cf` |
| `DepartmentPauseModified(bool)` | `0xdd3e5b8936c85b0f24d27616bb5cd2bc155c70d2d372e734a6e1a5be777acd9b` |
| `TellerDeposit(address,address,address,uint256,address,uint256)` | `0xfea6f3dacc57406b0007933d492eb1d67328e5d55c8ede1fc213c6d63edca049` |
| `TellerRebalance(address,address,address,address,uint256,uint256,uint256,uint256)` | `0x645f42ccd582db84e20aea9313073cbc6b1b20dd51cdbe68024e713263020d57` |
| `TellerWithdrawal(address,address,address,uint256,address,uint256,bool)` | `0x6b0d92ac92e3ebfdb54eaa7f092d7be054f8939df0c41f1c961f80fdb5d1e422` |
| `UserConfigSet(address,bool,bool,bool,address)` | `0xa1df7ba437478e42ba351e23d5875bc241b38d2f42357ce394db3831110d9fc7` |
| `UserDelegationSet(address,address,bool,bool,bool,bool,address)` | `0xe57f0d8a88a7e27cf4de7394d7913a3c69cdc3a26b5d956d55c8abe3d9f04271` |

### 10.5 Complete function-selector baseline

The compiler's 123 method identifiers, normalized to four-byte hex, are:

| Canonical signature | Selector |
| --- | --- |
| `adjustLock(address,uint256)` | `0x53992db7` |
| `adjustLock(address,uint256,address)` | `0xce644259` |
| `borrow()` | `0xe68d3569` |
| `borrow(uint256)` | `0xc5ebeaec` |
| `borrow(uint256,address)` | `0x4b3fd148` |
| `borrow(uint256,address,bool)` | `0x918c3447` |
| `borrow(uint256,address,bool,bool)` | `0x8b655a37` |
| `buyFungibleAuction(address,uint256,address)` | `0xb30420f9` |
| `buyFungibleAuction(address,uint256,address,uint256)` | `0x91774d06` |
| `buyFungibleAuction(address,uint256,address,uint256,bool)` | `0x81c63a8d` |
| `buyFungibleAuction(address,uint256,address,uint256,bool,bool)` | `0xc0ac8675` |
| `buyFungibleAuction(address,uint256,address,uint256,bool,bool,bool)` | `0x4fa3d65c` |
| `buyFungibleAuction(address,uint256,address,uint256,bool,bool,bool,address)` | `0x4567d2d4` |
| `buyManyFungibleAuctions((address,uint256,address,uint256)[])` | `0x5481c8c0` |
| `buyManyFungibleAuctions((address,uint256,address,uint256)[],uint256)` | `0x87a5b716` |
| `buyManyFungibleAuctions((address,uint256,address,uint256)[],uint256,bool)` | `0xd4c21c8e` |
| `buyManyFungibleAuctions((address,uint256,address,uint256)[],uint256,bool,bool)` | `0x57d094c5` |
| `buyManyFungibleAuctions((address,uint256,address,uint256)[],uint256,bool,bool,bool)` | `0x56cc9045` |
| `buyManyFungibleAuctions((address,uint256,address,uint256)[],uint256,bool,bool,bool,address)` | `0xf412e5e8` |
| `canMintGreen()` | `0x40fd6f94` |
| `canMintRipe()` | `0x3b6fccc0` |
| `claimFromStabilityPool(uint256,address,address)` | `0x36b20ad4` |
| `claimFromStabilityPool(uint256,address,address,uint256)` | `0x2f280083` |
| `claimFromStabilityPool(uint256,address,address,uint256,address)` | `0x843fdaee` |
| `claimFromStabilityPool(uint256,address,address,uint256,address,bool)` | `0xe64fe31f` |
| `claimLoot()` | `0xc9a6eea7` |
| `claimLoot(address)` | `0xb7097b4e` |
| `claimLoot(address,bool)` | `0x815a4392` |
| `claimLootForManyUsers(address[])` | `0xf0ae5286` |
| `claimLootForManyUsers(address[],bool)` | `0x8785beba` |
| `claimManyFromStabilityPool(uint256,(address,address,uint256)[])` | `0x6bc67a22` |
| `claimManyFromStabilityPool(uint256,(address,address,uint256)[],address)` | `0xf29c9f63` |
| `claimManyFromStabilityPool(uint256,(address,address,uint256)[],address,bool)` | `0xbe6979e5` |
| `convertToSavingsGreenAndDepositIntoStabPool()` | `0x79942b96` |
| `convertToSavingsGreenAndDepositIntoStabPool(address)` | `0x94863d36` |
| `convertToSavingsGreenAndDepositIntoStabPool(address,uint256)` | `0x9401e3ac` |
| `deleverageManyUsers((address,uint256)[])` | `0x4f08c95c` |
| `deleverageUser()` | `0xad8c13cf` |
| `deleverageUser(address)` | `0x227aec66` |
| `deleverageUser(address,uint256)` | `0x656e1c12` |
| `deleverageWithSpecificAssets((uint256,address,uint256)[])` | `0x6cf888aa` |
| `deleverageWithSpecificAssets((uint256,address,uint256)[],address)` | `0x34e994f1` |
| `deposit(address)` | `0xf340fa01` |
| `deposit(address,uint256)` | `0x47e7ef24` |
| `deposit(address,uint256,address)` | `0xf45346dc` |
| `deposit(address,uint256,address,address)` | `0xc6f1649f` |
| `deposit(address,uint256,address,address,uint256)` | `0x3fb7de52` |
| `depositFromTrusted(address,uint256,address,uint256,uint256)` | `0xdb89bf59` |
| `depositFromTrusted(address,uint256,address,uint256,uint256,(address,address,address,address,address,address,address,address,address,address,address,address,address,address,address,address,address,address))` | `0xa321c628` |
| `depositIntoGovVault(address,uint256,uint256)` | `0x246f9d99` |
| `depositIntoGovVault(address,uint256,uint256,address)` | `0xdd74b310` |
| `depositMany(address,(address,uint256,address,uint256)[])` | `0x025699f5` |
| `getAddys()` | `0xa5c7434a` |
| `getRipeHq()` | `0x09b9f556` |
| `isPaused()` | `0xb187bd26` |
| `isUnderscoreWalletOwner(address,address)` | `0x3ea63e81` |
| `isUnderscoreWalletOwner(address,address,address)` | `0xdb33279d` |
| `liquidateManyUsers(address[])` | `0x8d5c9efc` |
| `liquidateManyUsers(address[],bool)` | `0xea5bda94` |
| `liquidateUser(address)` | `0xb8b41974` |
| `liquidateUser(address,bool)` | `0xbdc62a7c` |
| `pause(bool)` | `0x02329a29` |
| `performHousekeeping(bool,address,bool)` | `0x07e1a067` |
| `performHousekeeping(bool,address,bool,(address,address,address,address,address,address,address,address,address,address,address,address,address,address,address,address,address,address))` | `0xefc5b8cf` |
| `purchaseRipeBond(address)` | `0x75828948` |
| `purchaseRipeBond(address,uint256)` | `0xc7c77bb2` |
| `purchaseRipeBond(address,uint256,uint256)` | `0xb1e16838` |
| `purchaseRipeBond(address,uint256,uint256,address)` | `0x2cf0fd55` |
| `rebalance(address,uint256,address,uint256)` | `0x1312f6d8` |
| `rebalance(address,uint256,address,uint256,uint256)` | `0x487fd516` |
| `rebalance(address,uint256,address,uint256,uint256,uint256)` | `0x9c1c0b63` |
| `rebalance(address,uint256,address,uint256,uint256,uint256,address)` | `0xe15979ed` |
| `recoverFunds(address,address)` | `0x24ae6a27` |
| `recoverFundsMany(address,address[])` | `0x7053a18f` |
| `redeemCollateral(address,uint256,address)` | `0x556bfd9c` |
| `redeemCollateral(address,uint256,address,uint256)` | `0x8b8a2389` |
| `redeemCollateral(address,uint256,address,uint256,bool)` | `0x3dcbe860` |
| `redeemCollateral(address,uint256,address,uint256,bool,bool)` | `0xcfca2319` |
| `redeemCollateral(address,uint256,address,uint256,bool,bool,bool)` | `0xf813ce6e` |
| `redeemCollateral(address,uint256,address,uint256,bool,bool,bool,address)` | `0x71b78d17` |
| `redeemCollateralFromMany((address,uint256,address,uint256)[])` | `0x4a9186b1` |
| `redeemCollateralFromMany((address,uint256,address,uint256)[],uint256)` | `0x74ff30f4` |
| `redeemCollateralFromMany((address,uint256,address,uint256)[],uint256,bool)` | `0x225b962e` |
| `redeemCollateralFromMany((address,uint256,address,uint256)[],uint256,bool,bool)` | `0x0128d538` |
| `redeemCollateralFromMany((address,uint256,address,uint256)[],uint256,bool,bool,bool)` | `0xeba2073a` |
| `redeemCollateralFromMany((address,uint256,address,uint256)[],uint256,bool,bool,bool,address)` | `0xc5f7de4e` |
| `redeemFromStabilityPool(uint256,address)` | `0xa9d12127` |
| `redeemFromStabilityPool(uint256,address,uint256)` | `0x2febc58d` |
| `redeemFromStabilityPool(uint256,address,uint256,address)` | `0x9ab7eb6b` |
| `redeemFromStabilityPool(uint256,address,uint256,address,bool)` | `0x6a0ac6c0` |
| `redeemFromStabilityPool(uint256,address,uint256,address,bool,bool)` | `0x64505a3e` |
| `redeemFromStabilityPool(uint256,address,uint256,address,bool,bool,bool)` | `0x263fe583` |
| `redeemManyFromStabilityPool(uint256,(address,uint256)[])` | `0x3969c94c` |
| `redeemManyFromStabilityPool(uint256,(address,uint256)[],uint256)` | `0x1768d1cc` |
| `redeemManyFromStabilityPool(uint256,(address,uint256)[],uint256,address)` | `0x7dd5da70` |
| `redeemManyFromStabilityPool(uint256,(address,uint256)[],uint256,address,bool)` | `0x2cc7d2e3` |
| `redeemManyFromStabilityPool(uint256,(address,uint256)[],uint256,address,bool,bool)` | `0x06dfaff2` |
| `redeemManyFromStabilityPool(uint256,(address,uint256)[],uint256,address,bool,bool,bool)` | `0x60f23e37` |
| `releaseLock(address)` | `0xd1c46916` |
| `releaseLock(address,address)` | `0x9cb2b062` |
| `repay()` | `0x402d8883` |
| `repay(uint256)` | `0x371fd8e6` |
| `repay(uint256,address)` | `0xacb70815` |
| `repay(uint256,address,bool)` | `0x2fe0f37f` |
| `repay(uint256,address,bool,bool)` | `0x897b357b` |
| `setUndyLegoAccess(address)` | `0x9d361ff9` |
| `setUserConfig()` | `0xf74ade68` |
| `setUserConfig(address)` | `0x205f9409` |
| `setUserConfig(address,bool)` | `0x61484d1d` |
| `setUserConfig(address,bool,bool)` | `0x958c288b` |
| `setUserConfig(address,bool,bool,bool)` | `0x8dc17754` |
| `setUserDelegation(address)` | `0xcf29e4c9` |
| `setUserDelegation(address,address)` | `0x2ef838b6` |
| `setUserDelegation(address,address,bool)` | `0x34146458` |
| `setUserDelegation(address,address,bool,bool)` | `0xb206b9c9` |
| `setUserDelegation(address,address,bool,bool,bool)` | `0xc7211986` |
| `setUserDelegation(address,address,bool,bool,bool,bool)` | `0x5fd76b71` |
| `withdraw(address)` | `0x51cff8d9` |
| `withdraw(address,uint256)` | `0xf3fef3a3` |
| `withdraw(address,uint256,address)` | `0x69328dec` |
| `withdraw(address,uint256,address,address)` | `0xdfcd412e` |
| `withdraw(address,uint256,address,address,uint256)` | `0x5501f1c6` |
| `withdrawMany(address,(address,uint256,address,uint256)[])` | `0x4edab157` |

## 11. A7: stop report, feasibility, risks, and pending decisions

### 11.1 Stop-condition assessment

| Controlling stop | Result |
| --- | --- |
| “the exact baseline is missing, stale, or ambiguous” | No; all four `rh` identities were exact at bootstrap, and current local, cached, and live `rh` converge at `8e4a965f...7d98`. Section 0.8 proves the incoming H-03 movement is documentation-only and changes no M1 byte. The feature remains unintegrated at one ahead / ten behind; Phase B still requires final S5/current-`rh` reconciliation and separate baseline authority |
| “the integration worktree is dirty” | No |
| “the proposed branch or worktree already exists” | No; both were absent before fresh creation |
| “an H-01 gate fails or an exception control is stale” | No; the owner-authorized exact-lock replay passed H-01/S1/S2 with 133 tests and the clean inventory result |
| “S5 integrates or changes its Ledger/Teller behavior” without reconciliation | **Active for any progression beyond evidence-only work.** S5 remains unintegrated, but its current worktree changes Ledger behavior and overlapping Teller tests as recorded in Section 0.8. The exact feasibility result remains baseline-specific; official Phase B cannot begin until S5 reaches a final reviewed state and the required reconciliation and regressions pass |
| “a controlling M0 object changed without reconciliation” | No object has yet changed; the required future M0 correction will trigger this stop |
| “the durable evidence record ... claims an approval that did not occur” | No after this correction; Section 4.1 now calls the environment action unratified |
| “the pinned compiler cannot implement an exact-length read” or oversized response rejection | No; the primitive probes passed |
| “a discovered deposit caller is absent from the approved matrix” | No; eight fixed-string call sites reconcile to eight categories |
| “a legitimate trusted route cannot remain live” | No; CreditRedeem's branch was never live at the baseline and the owner approved preserving its dormancy; CreditEngine's borrower-proceeds route remains live |
| “an approved exact-transfer route requires `R != Q`” | No |
| “a supported vault legitimately returns an amount other than `Q`” | No |
| “a required test needs a fourth test file or a repository mock change” | No; the exact candidate induces fixed-sGREEN failure with an authorized inline seam and uses only the three authorized test files |
| **“a production file other than `Teller.vy` appears necessary”** | **No; the exact candidate preserves CreditRedeem dormancy and changes Teller only** |
| “any interface, ABI JSON, selector, event, persistent layout ... edit appears necessary” | No; the exact candidate reproduces ABI, selectors, events, and persistent layout exactly; Gate 1 must reproduce |
| “a mandatory test fails, skips, xfails, or is relaxed” | No in exact feasibility: the complete serial suite passed 2,884 selected tests with zero skips/xfails; official Gate 1 and Gate 2 remain unstarted |

The exact preserved four-file candidate proves deployable Teller-only
feasibility, including the vault-return invariant, 24,152-byte runtime,
fixed-sGREEN failure construction, CreditEngine live route, and CreditRedeem
dormancy/refund behavior. That feasibility result is not an official Phase B
repository implementation. The complete Phase A evidence was independently
exact-hash approved and committed byte-for-byte at `2935f0e2...75f5`, closing
Phase A. This unstaged lifecycle-only follow-up requires its own exact-hash
review before any later documentation commit but does not reopen Phase A.

### 11.2 Historical reachability blocker and owner resolution

The historical checkpoint found a controlling-language conflict: it named a
live CreditRedeem `depositFromTrusted` route even though CreditRedeem's only
call to `_handleGreenForUser` supplies `_shouldEnterStabPool=False`. That
branch is intentionally unreachable, and existing behavior refunds sGREEN to
the redeemer. CreditEngine has a separate reachable route from `borrow` when
the user selects auto-deposit.

The owner resolved the conflict for M1 feasibility:

1. CreditRedeem's surplus-deposit route remains intentionally dormant;
2. CreditRedeem must not be changed to activate it;
3. its current sGREEN refund, unchanged StabilityPool state, and absence of a
   Teller deposit event must be tested;
4. CreditEngine's live route is named borrower-proceeds auto-deposit; and
5. Teller remains the only permitted production-contract change.

The exact preserved candidate implements that resolution in authorized tests
without modifying CreditRedeem or CreditEngine. It proves CreditRedeem's
dormancy and refund behavior and CreditEngine's borrower-proceeds
auto-deposit, including approval cleanup. This historical blocker is closed
for feasibility. It does not authorize an M0-document edit or official Phase
B; current `rh`/S5 reconciliation and separate file-exact Phase B
authorization remain required.

### 11.3 Exact five-file feasibility

| Authorized path | Preserved feasibility result | Official M1 worktree |
| --- | --- | --- |
| `contracts/core/Teller.vy` | Exact approved source exists at SHA-256 `4afc6ce1ccf21cb65e04ce3c56fedcf60bb79cba8e7dc51fd855a1f1f82bd909`; runtime 24,152 bytes; ABI/selectors/events/persistent layout invariant | Byte-identical to baseline; official Phase B edit has not begun |
| `tests/core/teller/test_teller_deposit.py` | Exact candidate covers direct, batch, Gov, trusted callers, fixed-sGREEN failure, CreditEngine, CreditRedeem dormancy/refund, permissions, pause, and atomicity | Byte-identical to baseline; official Phase B edit has not begun |
| `tests/core/teller/test_teller_rebalance.py` | Exact candidate covers rebalance exact and failure behavior | Byte-identical to baseline; official Phase B edit has not begun |
| `tests/vaults/test_stock_token_vault_comparison.py` | Exact candidate records both masking baselines, inverts M-01, and proves exact-candidate rejection | Byte-identical to baseline; official Phase B edit has not begun |
| `docs/chains/rh/evidence/stock-token-m1-exact-receipt.md` | Complete Phase A evidence independently approved at SHA-256 `9ef48b80...917e` and committed byte-for-byte at `2935f0e2...75f5` | Committed at feature `HEAD`; this lifecycle-only working-copy revision is the sole unstaged modification, and the index is empty |

The exact preserved four-file candidate proves the Teller-only mechanism
within the approved four-file Phase B production/test ceiling:

1. runtime is 24,152 bytes, below EIP-170 by 424 bytes;
2. T8's fixed-sGREEN failure is induced inside an authorized test file;
3. both exact masking baselines are recorded and rejected atomically;
4. CreditRedeem dormancy/refund and CreditEngine borrower-proceeds
   auto-deposit are both reproduced without another production change; and
5. all required focused, targeted, and complete serial validation passed.

The official repository implementation remains unstarted. If Phase B is
separately authorized, it must use the exact accepted Teller bytes and add the
dual-threshold size guard inside an already authorized M1 test file. That
guard changes no file ceiling. No sixth file or second production contract is
required or authorized.

### 11.4 Residual and no-change risks

#### 11.4.1 Intentional fail-closed semantic changes

M1 is designed to make the following deposits fail atomically, including some
calls that the aggregate-balance baseline can currently report as successful:

- transfer source equals destination vault, producing `R == 0`;
- receipt is zero, short, fee-reduced, sender/receiver-burned, or otherwise
  less than `Q`;
- receipt is reflection-increased, donated during the transfer, or otherwise
  greater than `Q`;
- custody decreases during the measurement window (`C1 < C0`);
- the pre- or post-transfer `balanceOf` call reverts, fails, returns empty,
  returns fewer or more than exactly 32 bytes, or returns malformed
  dynamic-shaped data;
- a token, vault, or callback attempts a nested Teller deposit while the
  measurement mutex is active; or
- the destination vault reverts or reports `vaultResult != Q` after exact
  receipt.

Token transfers that return false or revert and malformed pre-validation
balance reads already fail and continue to fail. There is no compatibility
fallback: discovery of a legitimate approved route in any category above is a
stop, not grounds to weaken `R == Q` or `vaultResult == Q`.

#### 11.4.2 Retained residual risks

- The current Teller can report/credit `Q` when only `Q-1` arrived if
  preexisting aggregate vault custody masks the short receipt.
- The baseline Teller has only 670 runtime bytes below EIP-170. The exact
  candidate consumes 246 bytes, **36.7% of that prior reserve**, and leaves
  424 bytes. The owner accepts that bounded risk only for exact Teller source
  SHA-256
  `4afc6ce1ccf21cb65e04ce3c56fedcf60bb79cba8e7dc51fd855a1f1f82bd909`;
  any source-byte change voids the acceptance and requires fresh measurement,
  complete tests, and independent review.
- `requirements.txt` is exact-version pinned but artifact-hash-free. The
  owner-authorized exact replay matched all reviewed versions and recorded its
  canonical freeze, but the repository lock itself does not pin downloaded
  artifact hashes.
- Five fixed RIPE/sGREEN producer fixtures cannot themselves induce
  short/malformed behavior. T7 qualifies those cases. The exact candidate
  separately satisfies T8 by inducing short sGREEN through the authorized
  test-local registry seam.
- The Teller-held conversion route mints `sGreenAmount` to Teller before
  `_deposit`. If the unchanged per-user or global limit reduces `Q` below
  `sGreenAmount`, only `Q` moves to StabilityPool and the remainder stays in
  Teller. A minimum-balance failure instead reverts the whole conversion; it
  does not strand funds. Later conversions remain capped by their own newly
  minted `sGreenAmount`, so they do not automatically sweep the residue.
  Switchboard-authorized `DeptBasics.recoverFunds` can move Teller's full token
  balance, but the route has no automatic user-attributed refund. This is
  pre-existing behavior, not introduced or repaired by M1; T8 must record it
  without widening production scope.
- The StabVault self-deposit guard covers IDs 0 and 1 only. A second StabVault
  at another ID could still self-target unless deployment/configuration proves
  source and destination differ.
- The exact candidate ran the donation-plus-short and literal multi-user
  masking baselines, then proved both fail atomically.
- The preserved candidate inverts the two-case M-01 test and its complete
  serial suite passes 2,884 selected tests with 142 deselected and zero
  skips/xfails. Gate 1 and Gate 2 remain independent reproduction gates for
  any later official implementation.
- M1's exact candidate check proves only call-local reported custody delta and
  vault return equality. A malicious token that lies consistently in
  `balanceOf` remains outside the guarantee; the approved token matrix and
  later runtime gates remain necessary.
- Exact inbound receipt does not prevent issuer pause, blocklist,
  administrative burn/confiscation, multiplier change, beacon upgrade,
  post-deposit loss, oracle failure, withdrawal failure, liquidation freeze,
  or liquidity failure.
- AAPL compatibility is conditional on the pinned identity and controls.
  Identity parity is not a new fork execution.
- New RIPE, GREEN, sGREEN, LP, DEX, pool, oracle, and deployment runtimes do
  not exist in M0/M1 evidence and remain hard launch gates.
- Base retains the old deployed Teller and its nominal accounting risk. An M1
  repository change would not remediate Base.
- Every Base ID-3 row still lacks composed per-route proof for a future
  cutover; sUSDe has an additional blacklist-redistribution deficit risk.
- The transient mutex is deliberately narrow. It rejects nested deposit
  measurement only while `C0`, transfer, `C1`, delta validation, and vault
  accounting are in flight; existing post-window calls remain outside it.
- The five H-01 bounded exceptions and 13 open alerts remain governed by H-01
  review, expiry, custody, and invalidation rules.
- S5 remains parallel. Its final integration state and current `rh` must be
  reconciled before Phase B because it can affect overlapping Teller tests or
  behavior even without changing the approved candidate source.

### 11.5 Historical owner decisions as of 25 July

This subsection is retained as the initial checkpoint record. Section 0.1
records the owner's later dispositions, and Section 0.7 is the current list of
remaining decisions.

The historical decision list now has these dispositions:

1. **Exact-lock authority and replay — resolved for feasibility.** The owner
   explicitly authorized the fresh disposable exact-lock reconstruction, and
   Section 0 records the complete replay. The earlier inferred-environment
   deviation remains disclosed but is not relied upon.
2. **CreditEngine/CreditRedeem semantics — resolved for feasibility.**
   CreditEngine is borrower-proceeds auto-deposit; CreditRedeem remains
   intentionally dormant and retains its current refund behavior.
3. **T8 feasibility — resolved.** The exact candidate induces fixed-sGREEN
   failure inside an authorized test file and proves atomic rollback.
4. **T7 inducibility — resolved for the approved candidate.** Arbitrary-asset
   producers receive induced failure coverage; fixed-token producers receive
   exact-success coverage under the approved qualifier.
5. **Exact Teller source and headroom — owner approved.** Acceptance is only
   for source SHA-256
   `4afc6ce1ccf21cb65e04ce3c56fedcf60bb79cba8e7dc51fd855a1f1f82bd909`,
   its 24,152-byte runtime, and its 424-byte reserve; any source-byte change
   invalidates it.
6. **Phase A closure — complete.** The task transcript records independent
   exact-hash approval of evidence SHA-256 `9ef48b80...917e`; the exact bytes
   were committed as the sole file in `2935f0e2...75f5`, closing Phase A, and
   were later preserved on the remote feature branch. This unstaged
   lifecycle-only follow-up needs a new exact-hash review before any later
   documentation commit but does not reopen Phase A.
7. **Pre-Phase-B reconciliation — still required.** Reconcile current `rh`,
   S5's final integration state, and overlapping Teller-test effects.
8. **Official Phase B — still unauthorized.** It requires a separate,
   explicit, file-exact owner authorization. If authorized, it must retain the
   exact Teller bytes, add the dual-threshold repository size guard within an
   already authorized M1 test file, and pass Gate 1's independent compiler,
   artifact, invariant, layout, behavior, and complete-suite reproduction.

The owner is not being asked to waive `vaultResult == Q`, permit trusted
short receipts, add a chain-specific branch, modify Base, or approve any live
action.

## 12. Checkpoint scope and prohibited actions

In the official M1 feature worktree at this lifecycle reconciliation
checkpoint:

- `Teller.vy` is byte-identical to the approved baseline;
- all three authorized test files are byte-identical to the approved baseline;
- no production, interface, ABI, vault, dependency, fixture, default,
  migration, manifest, inventory, CI, or summary file changed;
- the independently reviewed Phase A evidence is committed at feature `HEAD`
  `2935f0e2...75f5`, and the local, tracking, and live remote feature refs
  have exact parity;
- this evidence file is the sole working-copy modification and is unstaged;
  the index is empty;
- no new commit or push and no merge, amendment, rebase, deployment,
  configuration, signature, transaction, live RPC call, signer use,
  broadcast, external-human contact, or activation occurred in this
  reconciliation; and
- Phase B and M2-M5 did not begin.

These worktree statements do not deny the separate, detached feasibility
candidate documented in Section 0. That candidate is intentionally preserved
outside the official M1 worktree with four unstaged modifications; it is not
an official Phase B repository implementation.

The expected lifecycle-reconciliation handoff state is one unstaged
modification:

```text
 M docs/chains/rh/evidence/stock-token-m1-exact-receipt.md
```

### 12.1 Review-correction handoff validation

At `2026-07-25T21:49:07Z`:

- the integration worktree was clean on `rh`;
- integration `HEAD`, local `rh`, cached `origin/rh`, and live remote `rh`
  were all
  `332ae2bc8e0ce4b694766d6d20759295d9267ec3`;
- live remote `rh-track-8-m1-exact-receipt` was absent;
- feature `HEAD` and merge base were the approved baseline, feature tree was
  `f67dc91e47331785837de879b6557b285aec3b1b`, and ahead/behind was `0/0`;
- the feature status was exactly one untracked evidence file,
  `?? docs/chains/rh/evidence/stock-token-m1-exact-receipt.md`, with no
  staged content;
- Teller and the three authorized tests reproduced their Section 3 SHA-256
  values;
- exact Vyper `0.4.3+commit.bff19ea2` reproduced the 23,906-byte baseline
  runtime;
- a disclosed, permitted compiler-only M1-shaped scratch approximation
  produced a 24,275-byte runtime, left 301 bytes of EIP-170 headroom, and was
  removed; at that historical timestamp the exact candidate had not yet been
  reconstructed or measured, while Section 0 records its later exact
  24,152-byte result and durable preservation;
- `git diff --no-index --check /dev/null <evidence>` emitted zero bytes;
- no `/private/tmp/rh-m1-*` or `/private/tmp/rh-track-8-m1-*` path existed; and
- at that historical timestamp, the S5 recreation movement was the docs-only,
  non-integrated change recorded in Section 2.2; Section 0.8 supersedes that
  historical status with the current unintegrated but behavior-changing S5
  worktree.

No pytest suite was rerun for that historical evidence-only correction because
production and all authorized test bytes in the official worktree remained
unchanged. Section 0 separately records the later owner-authorized
exact-candidate replays; those results supersede the historical environment
run for feasibility without beginning Gate 1 or Gate 2.

The temporary version-exact environment (whose path was historically named
`rh-m1-exact-lock`), Boa-cache, pytest-basetemp, primitive-probe, and
re-review size-probe paths were removed before validation and remained absent
at handoff. Their verified absence and this record's final SHA-256 are reported
with the checkpoint handoff.

### 12.2 Pre-closure evidence-only reconciliation handoff (historical)

At the pre-closure handoff, this reconciliation chain:

- started from evidence SHA-256
  `b32a15c8cc07543625d24234c509e9b74d8607ed1051a6b5f03f30e08a24da95`;
- produced the first complete stale-status reconciliation at SHA-256
  `b9deb6d4eca46fa5bad6e9a06f1033d3feb45a2de83cf24e4c0b996c142195e3`,
  then used those live bytes for this final editorial and current-state pass;
- changed only the then-untracked Phase A evidence record;
- did not alter or rerun the exact feasibility candidate, its tests, or either
  preserved patch;
- read-only reverified Teller source SHA-256
  `4afc6ce1ccf21cb65e04ce3c56fedcf60bb79cba8e7dc51fd855a1f1f82bd909`
  and four-file patch SHA-256
  `556a3553930da1008ac1bb75751ad4be2c5c28faf6fc6d9138e8b85e4b00768f`;
- recorded that the substantive independent candidate review targeted
  superseded evidence SHA-256
  `f5ed7d1e2e63b0491369e91932ba4a8aa2391e3dbd83a31749a8016c41831075`
  and therefore was not exact-hash approval of that record;
- read-only refreshed the unchanged M0/M1 authority hashes and exact local,
  cached, and live `rh` identity, and recorded the current unintegrated S5
  behavior/test delta in Section 0.8;
- at that time, left the evidence unstaged and uncommitted for a new
  independent exact-hash review; and
- at that time, left Phase B unauthorized and unstarted behind exact-hash
  approval, evidence commit, final S5/current-`rh` reconciliation, and
  separate explicit file-exact owner authorization. The first two conditions
  later completed; the latter two remain pending.

No compiler, pytest, feasibility, deployment, configuration, signing,
broadcast, live-RPC, or external-contact action was run for this
historical reconciliation. Those lifecycle statements were later superseded
by the exact-hash approval and one-file commit recorded in Sections 0.1 and
12.3.

### 12.3 Lifecycle and provenance reconciliation handoff

This documentation-only reconciliation:

- starts from feature commit
  `2935f0e2fc7c1f0a783e5b822ca560dc11f375f5`, whose sole committed path is
  this evidence record and whose committed file SHA-256 is the independently
  approved `9ef48b80fc0fe1e37ee6878d81201274a1ac7eda682d96de0205439e2242917e`;
- records only transcript-proved provenance: the owner's explicit statement
  of completed independent exact-hash review, the file-exact commit
  authorization, the reported and Git-reproduced commit/tree/parent/scope,
  Phase A closure with that commit, and the later separately authorized
  remote preservation;
- leaves local, tracking, and live remote feature refs unchanged at
  `2935f0e2...75f5`, with exactly this evidence file modified but unstaged
  and an empty index;
- records local, cached, and live `rh` converged at
  `8e4a965f034dc3d11b60fbb674ebbb4095b57d98`, tree
  `d0a6048d902a035bf69158359dc80e9786792f38`. Its ten-commit advance from
  `332ae2bc...7ec3` changes only unrelated documentation paths, leaves every
  controlling M0/M1 authority and all four prospective Phase B
  production/test paths byte-identical, and leaves the unintegrated feature
  one commit ahead and ten commits behind, with merge base
  `332ae2bc...7ec3`;
- leaves the exact feasibility candidate and preserved patches unchanged;
- does not apply or rerun the candidate, modify a production or test file,
  stage, commit, push, merge, amend, rebase, deploy, configure, sign,
  broadcast, contact a live RPC, or begin Phase B; and
- leaves Phase B explicitly unauthorized and unstarted pending S5's final
  reviewed and integrated state, current-`rh`/S5 reconciliation, resealing
  the two overlapping Teller test files and complete M1 patch, complete
  required validation and review, and separate file-exact owner
  authorization.

This revised working copy requires independent exact-hash review before any
later documentation-only commit. That review is provenance for this follow-up
revision; it is not a reopening of Phase A and grants no Phase B authority.
The revised evidence SHA-256 is reported outside the file so the record does
not attempt to embed its own changing digest.
