# Track 6 S5 Ledger Guard Stage B Implementation Record

> **8 August 2026 removal overlay:** The block-clock inventory this record
> reconciles against has been removed, along with
> `contracts/testing/ActionBlockIdentityProbe.vy`. The `INV-CADENCE-NEW`,
> `INV-PATH-NEW`, and source-hash rows below therefore describe entries in a
> ledger that no longer exists; they are kept as the historical record of the
> Stage B/C work, not as live authority. The Ledger guard behaviour itself is
> unaffected — no production contract changed. Removed sources are recoverable
> from git history.

**Status:** Stage B independently approved at Gate 1 artifact SHA-256
`e2c7b92b3ca51f903e0cdb8eb5c5eda3d6c1f2e644a6ee424ea67fe8e8ea9a76`;
bounded Stage C inventory reconciliation complete; mandatory Gate 2
independent review pending; every merge, deployment, configuration, and live
action remains unauthorized

**Evidence dates:** 25–26 July 2026

**Starting commit:**
`db5e589e13bc39002a345d70cb9d9a38eb13fd67`

**Starting tree:**
`e9577eb92b4b4654018581a4a2a4bacd2f1a3587`

**Controlling decision record before Stage B:** SHA-256
`15610bac4293d06320581dc1603b2980ea352af55d89f040ccab18ca26c9e739`

**Branch:** `rh-track-6-s5-ledger-guard-recreation`

**Worktree:**
`${HOME}/dev/ripe-protocol-track-6-s5-ledger-guard-recreation`

This record covers only the bounded Stage B implementation authorized from the
exact starting commit above. It is not Gate 1 approval. It is not authority to
edit inventory, begin Stage C, commit, push, merge, deploy, register,
configure, activate, govern, access a signer, sign, broadcast, or change the
deployed Base Ledger.

## 0. Gate 1 rejection and exact-length correction

Gate 1 was not approved at this record's prior SHA-256
`45db6089b0fe12a8d4c1e3bc6ffcd66de14ade0324eed31b3a7bf9941406cccd`.
Independent reproduction proved that Vyper's typed
`staticcall ArbSys(0x64).arbBlockNumber()` accepted a 64-byte return while the
consumer expected one 32-byte `uint256`: the first word decoded and the extra
word was ignored. The prior record's claim that an arbitrary malformed or
wrong-ABI return would fail closed was therefore too broad.

The correction remains inside the same 14-file ceiling and changes only:

- `contracts/data/Ledger.vy`;
- `tests/data/test_ledger_action_block.py`; and
- this implementation record.

The typed ArbSys interface has been removed. Construction and runtime now use
the same `_getArbActionBlock()` boundary:

```text
raw_call(
    0x0000000000000000000000000000000000000064,
    method_id("arbBlockNumber()", output_type=Bytes[4]),
    max_outsize=65,
    is_static_call=True,
    revert_on_failure=True,
)
```

The returned `Bytes[65]` must have length exactly 32 before
`abi_decode(..., uint256)`. Vyper records `min(returndatasize, 65)` as the
captured length, so 33 bytes, 64 bytes, and every return larger than 64 bytes
are distinguishable from 32 and reject. A short or empty return also rejects,
and an EVM call failure continues to revert. There is no fallback.

S5's `Bytes[65]` / `max_outsize=65` boundary and Track 8 M1's
`Bytes[33]` / `max_outsize=33` boundary are both correct exact-32-byte
rejection idioms. With an asserted captured length of exactly 32, any capture
ceiling of at least 33 distinguishes an oversized response: M1 uses the
smallest one-byte sentinel, while S5 retains 65 so its required 33-byte,
64-byte, and greater-than-64-byte regression cases are directly observable as
33, 64, and capped 65 bytes. Neither accepts a response other than exactly 32
bytes. Standardizing the two ceilings would not change the acceptance rule and
is not a reason to modify Ledger.

This correction changes no approved product decision, constructor ABI,
external selector, storage layout, immutable layout, source address, or
rollout boundary. Gate 1 must review the new exact package rather than relying
on the rejected record hash.

### 0.1 Gate 1 coverage and record corrections

On 26 July 2026, the implementation-task transcript records this controlling
owner clarification:

> The owner confirms that decision-record §12’s exact 14-file ceiling controls Stage B and supersedes the earlier 12-path Checkpoint 0 listing solely for the final Stage B file ceiling. This does not authorize Stage C, deployment or release action.

The clarification resolves the historical 12-path/14-file mismatch only for
the final Stage B ceiling. It authorizes no additional file, production
behavior, Stage C action, inventory edit, deployment, or release action.

Gate 1 also required dedicated ArbSys-mode same-identity rejection evidence
for the two batch members of the six-action checked set. The correction adds
only tests inside the already authorized
`tests/core/teller/test_teller_withdraw.py` and
`tests/vaults/modules/test_stab_vault_claims.py`; it changes no production
source or behavior.

## 1. Implemented decision

The production change is limited to the approved shared Ledger source
discriminator:

1. `ACTION_BLOCK_SOURCE == empty(address)` selects native `block.number`.
2. `ACTION_BLOCK_SOURCE ==
   0x0000000000000000000000000000000000000064` selects only
   `ArbSys(0x64).arbBlockNumber()`.
3. Every other constructor value rejects with
   `invalid action block source`.
4. The ArbSys constructor path makes the fixed `arbBlockNumber()` selector
   call through the shared raw boundary, requires exactly 32 return bytes, and
   decodes one `uint256`. Missing code, a revert, short data, oversized data,
   or an incompatible implementation fails construction.
5. The selected address is one read-only public immutable. There is no
   separate mode or provider field.
6. The runtime helper branches only on that immutable. There is no
   `chain.id` branch and no fallback from an ArbSys failure to
   `block.number`.

No production interface file or typed ArbSys interface remains. No provider
contract, arbitrary selector, event, monotonicity assertion, Robinhood-only
Ledger source, or mutable source selection was added.

`checkAndUpdateLastTouch` reads the selected identity exactly once, applies
the existing equality test to that value, writes the same value, and then
performs the existing locked-account assertion. The original caller
authorization and pause checks remain before the source read. A reverting
lock or later enclosing-call failure rolls back the write exactly as before.

The equality-only policy is deliberate. A repeated identity rejects a checked
action; any different identity, including a locally controlled regression,
passes. Pre-activation and runtime monitoring, not a new Ledger nondecrease
assertion, own regression detection.

## 2. Exact Stage B scope

The implementation uses exactly the 14 paths authorized by decision-record
section 12:

| Path | Stage B purpose |
| --- | --- |
| `contracts/data/Ledger.vy` | one immutable source discriminator, fixed-selector exact-length static raw-call boundary, constructor validation/call/decode, helper, and getter |
| `tests/conf_core.py` | explicit zero source for the ordinary shared fixture |
| `tests/data/test_ledger.py` | deterministic preservation of the zero-address key in native mode |
| `tests/core/teller/test_teller_deposit.py` | low-risk repeat and arming evidence |
| `tests/core/teller/test_teller_withdraw.py` | checked single/batch paths, dedicated ArbSys `withdrawMany` same-identity rejection, rollback, and delegated-user identity |
| `tests/core/teller/test_teller_rebalance.py` | post-two-leg checked action and full rollback |
| `tests/core/teller/test_teller_action_block.py` | static classification/identity ceiling plus runtime external-housekeeping matrix |
| `tests/core/deleverage/test_deleverage_swap_collateral.py` | sole production external-housekeeping route and after-effects rollback |
| `tests/core/creditEngine/test_credit_borrow.py` | checked guard before borrow effects |
| `tests/core/creditEngine/test_credit_repay.py` | lower-risk repay ordering and rearming |
| `tests/vaults/modules/test_stab_vault_claims.py` | both checked Stability Pool claim paths, dedicated ArbSys `claimManyFromStabilityPool` same-identity rejection, and rollback |
| `tests/data/test_ledger_action_block.py` | native/ArbSys, constructor, source-failure, equality, lock, pause, and zero-key matrix |
| `scripts/abis/Ledger.json` | generated Ledger ABI only |
| `docs/chains/rh/ledger-guard-implementation-record.md` | this Gate 1 evidence record |

No file outside this ceiling changed. In particular, Teller, TellerUtils,
Deleverage, MissionControl, Switchboards, Defaults, interfaces, dependencies,
inventories, migrations, manifests, shared planning records, and
`docs/chains/rh-summary.md` remain byte-identical to the starting commit.

The following unchanged Git identities provide the immutable-scope checks:

| Untouched input | Git identity |
| --- | --- |
| `contracts/core/Teller.vy` blob | `1f6dca65bb1fb64deb0067b89e612979c76e0bb8` |
| `contracts/core/TellerUtils.vy` blob | `ba47bd5b3b049591e405b5b1b91a5e0c87280f98` |
| `contracts/core/Deleverage.vy` blob | `9b36c6f28c3c6257768a0724b34069acb7becfe7` |
| `contracts/data/MissionControl.vy` blob | `8a7e0e1d20835d2ecf11ccc75e2743c00d722abc` |
| `docs/chains/rh-summary.md` blob | `381ec7551a2e7868f4011a84d0ea73250f658c9e` |
| `config/block-clock-inventory.json` blob | `e3e08b2e45aebcdddbf16faa6fcf99e2f908e6a9` |
| `migrations/base-mainnet` tree | `e7db6ed257f00d7ceb081716953920b897f01ee0` |
| `migration_history` tree | `12b59cf73855a673946d88f69e30000e51681992` |

## 3. Preserved guard semantics

### 3.1 Equality, ordering, and configuration

The focused Ledger matrix proves:

- native identities at repeats and advances of `+1`, `+2`, `+4`, and `+60`;
- an unchanged ArbSys identity still rejects after native block advancement;
- ArbSys `+1` permits the next checked action;
- a different regressed value remains permitted, preserving the required
  equality-only policy;
- low -> high and high -> low -> high ordering;
- two users remain isolated within one identity;
- unchecked actions still write and arm a later checked action;
- both Boolean values preserve lock and pause behavior in both source modes;
- only Teller can call the guard in either source mode; and
- the zero-address user key remains accepted and written in both modes.

The implementation does not change MissionControl's Boolean, arming behavior,
the Underscore exemption, or any configuration authority.

### 3.2 Exact high-risk set

The exact six checked actions remain:

1. `withdraw`;
2. `withdrawMany`;
3. `rebalance`;
4. `borrow`;
5. `claimFromStabilityPool`; and
6. `claimManyFromStabilityPool`.

No production Teller line changed. Runtime tests exercise all six, including
effects-before-guard rollback for withdrawals, rebalance, and Stability Pool
claims, plus guard-before-credit-effects ordering for borrow. The two batch
actions now have dedicated ArbSys-mode coverage:

- `test_withdraw_many_arb_sys_rejects_second_same_action_block`; and
- `test_claim_many_arb_sys_rejects_second_same_action_block`.

Each test performs a successful batch at one controlled child identity,
advances the native block while holding that identity constant, proves the
second otherwise-valid batch rejects, and proves all economic state and
`lastTouch` roll back.

### 3.3 Identity and reachability

The Stage B static reachability test pins all 23 Teller
`self._performHousekeeping(...)` invocations. Those are the 22 existing
classified internal call sites plus the public external wrapper's exact
parameter forwarding. The 25-item logical graph counts those 23 invocation
rows, the public external `performHousekeeping` endpoint itself as a separate
caller-boundary item, and the sole Deleverage source call:

```text
performHousekeeping(False, _user, True, a)
```

The pinned Teller literals preserve every current `_user`, `_recipient`, and
`msg.sender` choice, the exact high/low classification, and the exact debt
flag. Existing full-suite action tests continue to exercise the
recipient/keeper/liquidation-subject, caller/beneficiary, and multi-user
routes. Stage B adds direct evidence that:

- a delegated withdraw touches Bob, not delegate Sally;
- each of Deleverage, CreditEngine, SimpleErc20Vault, and SwitchboardAlpha is
  accepted by the broad valid-Ripe-caller boundary;
- an arbitrary address is rejected;
- an accepted caller can choose the victim and risk flag;
- caller-supplied Addys can select an alternate Ledger;
- a later supplied-Addys failure rolls the touch back;
- an Underscore wallet and an Underscore vault remain exempt from equality
  rejection but still receive a touch; and
- the zero-address victim behavior remains unchanged.

The successful Deleverage collateral swap proves its exact external
housekeeping route reaches Ledger after both economic legs. Pausing Ledger at
that point proves the complete swap transaction, including both token and
vault effects, rolls back.

This evidence preserves the owner-accepted external-housekeeping residual
risk; it does not narrow the broad caller/victim/Addys boundary.

## 4. Fail-closed source matrix

The constructor accepts only zero and exact `0x64`. Focused controlled doubles
prove that the external-source constructor fails for:

- no code;
- a reverting call;
- a 31-byte short return;
- a 33-byte oversized return;
- a 64-byte two-word return;
- a 96-byte return, observed as the 65-byte capture ceiling; and
- code without the required selector.

After successful construction, replacing the controlled `0x64` code with each
of those seven failures makes the next touch revert. `lastTouch` remains at its
prior child identity, and no native-block value is written. There is no
fallback.

The constructor does not call an external source in zero mode. The exact
`0x64` path sends only the fixed `arbBlockNumber()` selector; it does not use
`arbOSVersion()` at runtime. The independently accepted fork evidence remains
the pre-Stage-B version/source gate. Live receipt, mempool, sequencer,
multi-transaction, signing, broadcast, and deployment evidence remain
deployment/release-readiness requirements.

## 5. Storage and immutable code layout

Both sides were compiled from the exact starting commit and working-tree
source with the integrated locked Vyper `0.4.3+commit.bff19ea2` compiler,
optimization `gas`, experimental codegen disabled.

Compact key-sorted `storage_layout` on both sides has identical SHA-256:

```text
bb19201a6bf4f4ef2649e5054e0fce6a53f007af4e4a004365edcc245c7e45a6
```

Every existing storage field, type, width, and slot is unchanged. Slots remain
0 through 47; `lastTouch` remains slot 1 and `greenPoolDebt` remains the final
field at slot 47. No storage field was inserted, removed, or reordered.

The code-data layout retains:

- `RIPE_HQ_FOR_ADDYS` at offset 0;
- `CAN_MINT_GREEN` at offset 32; and
- `CAN_MINT_RIPE` at offset 64.

The sole addition is immutable `ACTION_BLOCK_SOURCE` at offset 96. It cannot
overwrite or shift any existing immutable or storage value.

Raw compiler layout-output SHA-256 changes from
`23b6d3c9133d416f07377b187711eaef1731b199b1564b4a08ced5c379ced12d`
to
`7213fc05a17fd978ff618610263114fc4aa4fd7471d7e1047ec3e0ea11d27227`
only because that code-data word is added; the canonical storage subobject is
identical as stated above.

## 6. ABI generation and comparison

Only Ledger's generated ABI was copied from this locked command:

```text
/private/tmp/h01-final-review.dL2pqo/candidate/bin/python \
  scripts/export_abis.py \
  --contracts-dir contracts/data \
  --output-dir /private/tmp/s5-stage-b-correction-abi
```

The temporary command generated Ledger and MissionControl outputs. Only
`Ledger.json` entered the worktree; MissionControl and every other ABI remain
untouched.

| ABI measure | Starting | Stage B |
| --- | --- | --- |
| file SHA-256 | `80ffdd691f25ae5e6feba917ec6c5fa6f6e95a6ea321b46cad3de735c1710fbd` | `c6fc1c410e13f144ae9e9d1853378d476fa578211b08f67b23f80c2075bc415f` |
| entries | 91 | 92 |
| Vyper ABI-output SHA-256 | `f7348f71f5be4ed53d08b1f3d62acbb38b8b7e11aa50ff41a31ec6936b43d99c` | `ac8cc634b24c896381e473c6dd1a8681f28de5edb926b2e65190eba26bd9ff8b` |
| normalized generated/compiler ABI SHA-256 | `0a3eacc3d8c3b82921da5aa131653463c516f628b9d4eb1399dba763e01f9a11` | `695654b0ecbe794c2c7893fdc1af1c3bbce58cd77eeb848ec07079961b34b54b` |

The semantic ABI delta is exactly:

- constructor
  `(address _ripeHq, address _defaults)` becomes
  `(address _ripeHq, address _defaults, address _actionBlockSource)`; and
- view getter `ACTION_BLOCK_SOURCE() -> address` is added with selector
  `0x3b1207da`.

Every existing function selector, event, input, and output remains. The
method-identifier output changes only by adding that getter; its raw output
SHA-256 changes from
`ec72627bf48a089e0f28496f8df472810c09b45f4611b7a882da033bddc26808`
to
`bf49ac79ece839fd3795cf39368614be787e32cf2efc725a33bc87a90e6ba6f5`.

## 7. Reproducible artifacts

The baseline source was exported from exact commit `db5e589...`; the Stage B
source was compiled from the worktree. Both used the same locked compiler and
settings. Hashes over raw bytecode exclude the CLI's `0x` prefix and newline.

| Artifact | Starting | Stage B |
| --- | --- | --- |
| Ledger file SHA-256 | `00d86847273621857b80701be5faf7ca88ff9505f68671d5b6ab3c8b4ec972e0` | `6bd731a6ce9084de213494ebad09f8e52c782153842708b78f90fa178c06e9e3` |
| source bytes | 25,370 | 26,492 |
| compiler integrity | `78d1e5c6d0fdc5ec8f8aeada465a090f09e523ef34bd7d2aee8c21025541413f` | `62cc9e492ee1b1a3e84ad104507d684dc81edecef969fc0ae0f7a1586dd0d830` |
| base64 archive SHA-256 | `12a8b22b1a05eb97706283744d036dcd8e296ae61bd465988ae83142ae6a0d9f` | `b395594f9ab271671fc43543c2fec9d1df27bbb37ef953f7d56116cdd3cf56af` |
| creation bytes | 13,226 | 13,730 |
| creation raw SHA-256 | `455296a8399e335497458079d72c1f2e5da6c84a40b6f9ba375bd08345cda583` | `a31f400f5364f8dbbd22b79bea2557f7f3dd57538eb659c06a21e18e9d8e9127` |
| creation Keccak-256 | `0x3ada2426a09236a71c8fd3c13ac3428571bf2fbbbcda1f076f7749cb601d56da` | `0xe9d55d68fa1bb9122e93a69b8b2a37f81033c3a9e958c8caac5e8bc134be47fd` |
| runtime template bytes | 12,874 | 13,125 |
| runtime-template raw SHA-256 | `de25c7d840667f61564b50f5b481c773298f2bc22e1a25a6d928fc6786f30f19` | `8fbc85b5bac4586fdb4fc432284f9c38d12ed3966b2de5630f9d4c80973dcce7` |
| runtime-template Keccak-256 | `0xd6336c81f1da3522c15b1c7af5ab551c33a5c0ba094ca4509defb109b21fa9b4` | `0xf45131f4322bf240a2285d39d6c00f04a0a1c158dcdb693919112746474c49c2` |

Additional exact compiler-output SHA-256 values:

| Output | Starting | Stage B |
| --- | --- | --- |
| settings | `94e854f66051117f6988116763754f6b43f7cd33902ca927e278d902e61eaa11` | same |
| creation CLI output | baseline not separately retained | `5af8f96a89c226233bf5cc264818a66ce3db3cb5e50684dc6518e4a6591eac29` |
| runtime CLI output | baseline not separately retained | `28f0f80a383251472ef3a40116ab5b6fb25d1141e3df586a307e3c0d3972a1ad` |
| integrity-output file | baseline not separately retained | `04e43bd3f6b29ab5070a98f53a79db1274de26d2e0b59513f0b5d9bdab0c5cfb` |
| metadata | `69d84f1fbf9b8aaefb86f40a789fbdee77c37c193c0f6d3be1aaee45f2a86f1c` | `e8375b768c959cbfe005420ee3fa1a12c3dc60286805c79ef2ba50294f3b7b2a` |
| combined JSON | `ebcb55555656d45e6a3711286330e266af5ac1cee9eb94e5e8bf42bbaa96eafc` | `15e19b2c17e39b6d37776c2aa1f671e13ff38f307b6f3e63a5585ae224bc8d83` |
| ABI with gas estimates | `8641eda3b0ff9de4ec93df288a7a65848ded5cf08af986bfbf9111a252b82c08` | `eeb67f2516cf2af7deffc1a0d42f5e95470d5c0ebe7e609b39fb4603057abf22` |

The runtime template is not a final deployed-runtime identity because RipeHq,
the existing inherited immutables, and the new source immutable are bound at
construction. A future Robinhood deployment manifest must pin the final
RipeHq, source, constructor arguments, creation artifact, and resulting
deployed runtime. No final Robinhood RipeHq or deployed runtime is asserted
here.

## 8. Gas evidence

Vyper's conservative estimate for either
`checkAndUpdateLastTouch` overload changes from `45,800` to `49,484`, a
`+3,684` upper-bound delta that includes the exact-length source boundary.

A controlled local Boa comparison deployed the exact starting and Stage B
sources against the same minimal RipeHq/Teller double, reset the gas tracker
before each operation, and used an exact `0x64` double returning `777`.
Results are local EVM measurements, not a Robinhood fee or production
deployment prediction:

| Operation | Starting native | Stage B native | Stage B ArbSys |
| --- | ---: | ---: | ---: |
| deploy | 2,600,084 | 2,656,927 (`+56,843`) | 2,659,871 (`+59,787`) |
| unchecked touch | 31,805 | 31,929 (`+124`) | 34,856 (`+3,051`) |
| checked successful touch | 31,890 | 32,018 (`+128`) | 34,945 (`+3,055`) |
| deployed runtime bytes in the controlled comparison | 12,970 | 13,253 | 13,253 |

The Base deployment incurs none of these deployment or runtime deltas because
its existing Ledger remains deployed and untouched indefinitely.

## 9. Locked-runtime validation

All pytest runs use the integrated H-01 Candidate A environment:

```text
Python 3.12.0
Vyper 0.4.3 / compiler 0.4.3+commit.bff19ea2
Titanoboa 0.2.7
pytest 8.4.2
cbor2 5.9.0
```

Every run removes Base and Robinhood RPC/signing variables, supplies only
`ETHERSCAN_API_KEY=local-placeholder`, uses `PYTHONPATH=.`, redirects Boa's
cache to a scope-specific `/private/tmp/s5-stage-b-validation` directory, uses
a scope-specific pytest `--basetemp`, and disables pytest's cache provider.
No RPC, endpoint value, signer, secret, live preflight, signature, broadcast,
or transaction was accessed.

The common launcher is:

```text
env -u BASESCAN_API_KEY -u WEB3_ALCHEMY_API_KEY -u TEST_PRIVATE_KEY \
  -u BASE_MAINNET_RPC_URL -u BASE_SEPOLIA_RPC_URL \
  -u ROBINHOOD_MAINNET_RPC_URL -u ROBINHOOD_TESTNET_RPC_URL \
  -u ROBINHOOD_TESTNET_PRIVATE_KEY -u DEPLOYER_PRIVATE_KEY \
  -u PYTHON_DOTENV_DISABLED \
  ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. \
  /private/tmp/h01-final-review.dL2pqo/candidate/bin/python -c \
  'from boa.interpret import set_cache_dir; set_cache_dir("<CACHE>"); \
  import pytest; raise SystemExit(pytest.main(<ARGS>))'
```

H-02 uses the same launcher with `PYTHON_DOTENV_DISABLED=1`, matching its
test boundary.

| Gate | Exact scope | Result |
| --- | --- | --- |
| H-01 | `tests/deployment/test_dependency_gate.py` | `16 passed, 3 warnings in 1.55s` |
| integrated H-02 and Base profile | `test_network_profiles.py`, `test_secret_handling.py`, `test_base_profile_regression.py` | `99 passed, 3 warnings in 13.84s` |
| S1 | `tests/clock/test_clock_profiles.py` | `57 passed, 3 warnings in 106.08s`, exit `0` |
| complete pre-production probe suites | `tests/probes` | `154 passed, 3 warnings in 33.20s`, exit `0` |
| focused Stage B Ledger/Teller matrix | `tests/data/test_ledger_action_block.py`, `tests/core/teller/test_teller_action_block.py` | correction run: `45 passed, 3 warnings in 128.49s`, exit `0`; prior Gate 1 freeze rerun: `45 passed, 3 warnings in 138.44s`, exit `0`; current findings-correction rerun: `45 passed, 3 warnings in 141.48s`, exit `0`; six exact-length failure parameters were added over the rejected package |
| exact new batch cases | `test_withdraw_many_arb_sys_rejects_second_same_action_block`, `test_claim_many_arb_sys_rejects_second_same_action_block` | `2 passed, 3 warnings in 107.24s`, exit `0` |
| exact nine-file targeted authority | section 18.1 set from the decision record | `447 passed, 3 warnings in 141.36s`, exit `0` |
| S2 inventory unit suite | `tests/inventory/test_block_clock_inventory.py` | `57 passed, 3 failed, 3 warnings in 25.42s`; only the three clean-current-inventory assertions fail |

The three S2 failures are mandatory Stage C work, not Stage B implementation
failures. Their fixture copies the current changed Ledger source with the
intentionally unchanged inventory and correctly reports that the approved
clock read moved from two direct reads into one helper read. Stage B is
prohibited from editing the inventory or its tests, so this record does not
mask, xfail, skip, or repair them.

The standalone checker was rerun after the exact-length correction and exits
`1` with exactly 28 findings:

| Finding | Count |
| --- | ---: |
| `INV-CADENCE-MISSING` | 1 |
| `INV-CADENCE-MOVE` | 2 |
| `INV-CADENCE-NEW` | 20 |
| `INV-DIRECT-COUNT` | 1 |
| `INV-DIRECT-MISSING` | 2 |
| `INV-DIRECT-NEW` | 1 |
| `INV-PATH-NEW` | 1 |

Exactly 20 findings arise from Stage B source/test changes. The other eight
arise from the previously committed isolated-probe package: seven
`INV-CADENCE-NEW` and one `INV-PATH-NEW`. Production direct occurrences move
from `100/95/17` to `99/94/17` because the two old Ledger `block.number` reads
become one helper read. Stage C must independently review and reconcile this
complete delta before Gate 2 or merge.

The ordered findings are reproduced here rather than inferred from the
rejected package. Line identities affected by this correction moved and were
re-measured. Each row also states its proposed Stage C disposition. Those
dispositions are review inputs only: they do not edit inventory, authorize
Stage C, or waive Gate 1.

| # | Code | Path / function | Line | Expected -> actual or detected surface | Proposed Stage C reconciliation, if separately authorized |
| ---: | --- | --- | ---: | --- | --- |
| 1 | `INV-CADENCE-MISSING` | `contracts/data/Ledger.vy` / `checkAndUpdateLastTouch` | 207 | `cadence-comment:per block` -> missing | Retire the stale direct-guard cadence entry only when replacement finding 4 is added. |
| 2 | `INV-CADENCE-MOVE` | `contracts/data/Ledger.vy` / `<module>` | 208 | line 197 -> 208, `# one action per block` | Repin the existing production module-comment entry to line 208; its semantic classification is unchanged. |
| 3 | `INV-CADENCE-MOVE` | `tests/data/test_ledger.py` / `test_ledger_check_and_update_last_touch_mixed_check_modes` | 1626 | line 1633 -> 1626 | Repin the existing test cadence entry to line 1626; its semantic classification is unchanged. |
| 4 | `INV-CADENCE-NEW` | `contracts/data/Ledger.vy` / `checkAndUpdateLastTouch` | 242 | production cadence comment on `actionBlock` | Add the replacement production action-block equality cadence entry linked to the source helper in finding 27. |
| 5 | `INV-CADENCE-NEW` | `contracts/testing/ActionBlockIdentityProbe.vy` / `readActionBlocks` | 30 | testing block-unit identifier | Add the already approved isolated-probe contract cadence entry as test-only evidence. |
| 6 | `INV-CADENCE-NEW` | `scripts/probes/action_block_identity_probe.py` / `analyze_observations` | 1594 | key `child_block` | Add this approved probe-runner observation key as tooling cadence evidence. |
| 7 | `INV-CADENCE-NEW` | same / `analyze_observations` | 1611 | key `first_child_block` | Add this approved probe-runner topology key as tooling cadence evidence. |
| 8 | `INV-CADENCE-NEW` | same / `analyze_observations` | 1612 | key `second_child_block` | Add this approved probe-runner topology key as tooling cadence evidence. |
| 9 | `INV-CADENCE-NEW` | same / `analyze_observations` | 1646 | key `distinct_child_blocks` | Add this approved probe-runner aggregate key as tooling cadence evidence. |
| 10 | `INV-CADENCE-NEW` | same / `preflight` | 979 | key `latest_block` | Add this approved probe-runner preflight key as tooling cadence evidence. |
| 11 | `INV-CADENCE-NEW` | `tests/core/creditEngine/test_credit_borrow.py` / `test_borrow_guard_runs_before_credit_effects_and_rejects_second_action` | 98 | test cadence comment | Add the Stage B borrow-ordering regression as non-production cadence evidence. |
| 12 | `INV-CADENCE-NEW` | `tests/core/creditEngine/test_credit_repay.py` / `test_repay_low_risk_succeeds_between_checked_actions_and_rearms_guard` | 97 | test cadence comment | Add the Stage B repay/rearming regression as non-production cadence evidence. |
| 13 | `INV-CADENCE-NEW` | `tests/core/teller/test_teller_action_block.py` / `test_external_housekeeping_valid_caller_can_select_victim_and_risk_flag` | 124 | test cadence comment | Add the Stage B external-housekeeping risk/classification regression as non-production cadence evidence. |
| 14 | `INV-CADENCE-NEW` | `tests/core/teller/test_teller_rebalance.py` / `test_rebalance_after_effects_guard_rejection_rolls_back_every_leg` | 134 | test cadence comment | Add the Stage B rebalance rollback regression as non-production cadence evidence. |
| 15 | `INV-CADENCE-NEW` | `tests/core/teller/test_teller_withdraw.py` / `test_checked_withdraw_rejects_second_same_action_block_and_rolls_back` | 165 | test cadence comment | Add the Stage B checked-withdraw rollback regression as non-production cadence evidence. |
| 16 | `INV-CADENCE-NEW` | same / `test_low_risk_deposit_arms_same_action_block_withdraw_rejection` | 114 | test cadence comment | Add the Stage B low-to-high arming regression as non-production cadence evidence. |
| 17 | `INV-CADENCE-NEW` | `tests/data/test_ledger_action_block.py` / `test_arb_sys_identity_not_native_block_controls_equality` | 155 | test cadence comment | Add the ArbSys-vs-native equality regression as non-production cadence evidence. |
| 18 | `INV-CADENCE-NEW` | same / `test_arb_sys_keeps_users_isolated_within_one_action_block` | 215 | first test cadence comment | Add the first per-user isolation assertion as non-production cadence evidence. |
| 19 | `INV-CADENCE-NEW` | same / `test_arb_sys_keeps_users_isolated_within_one_action_block` | 217 | second test cadence comment | Add the second per-user isolation assertion as non-production cadence evidence. |
| 20 | `INV-CADENCE-NEW` | same / `test_arb_sys_preserves_low_high_and_high_low_high_ordering` | 191 | first test cadence comment | Add the low-to-high ordering assertion as non-production cadence evidence. |
| 21 | `INV-CADENCE-NEW` | same / `test_arb_sys_preserves_low_high_and_high_low_high_ordering` | 197 | second test cadence comment | Add the high-to-low-to-high ordering assertion as non-production cadence evidence. |
| 22 | `INV-CADENCE-NEW` | `tests/probes/test_action_block_identity_probe.py` / `test_probe_emits_native_and_arb_sys_values_from_compatible_double` | 310 | probe call `readActionBlocks()` | Add the approved focused-probe call site as non-production cadence evidence. |
| 23 | `INV-CADENCE-NEW` | `tests/vaults/modules/test_stab_vault_claims.py` / `test_claim_after_effects_guard_rejection_rolls_back_second_claim` | 530 | test cadence comment | Add the Stage B Stability Pool rollback regression as non-production cadence evidence. |
| 24 | `INV-DIRECT-COUNT` | global | 0 | `100/95/17` -> `99/94/17` | Update aggregate direct counts only after findings 25–27 are reconciled atomically. |
| 25 | `INV-DIRECT-MISSING` | `contracts/data/Ledger.vy` / `checkAndUpdateLastTouch` | 207 | old first `block.number` read missing | Retire the first superseded `BN-002` direct occurrence as part of the atomic helper move. |
| 26 | `INV-DIRECT-MISSING` | same / `checkAndUpdateLastTouch` | 210 | old second `block.number` read missing | Retire the second superseded `BN-002` direct occurrence as part of the atomic helper move. |
| 27 | `INV-DIRECT-NEW` | `contracts/data/Ledger.vy` / `_getActionBlock` | 229 | native `block.number` helper read | Add the sole native-mode helper read as the reviewed replacement for findings 25 and 26. |
| 28 | `INV-PATH-NEW` | `contracts/testing/ActionBlockIdentityProbe.vy` | 0 | new testing path | Add the already approved probe contract to the testing-path classification; never classify it as production. |

Compared with the rejected package, the count and categories happen to remain
the same, but the Ledger module comment moved from line 211 to 208, the new
guard surface moved from 231 to 242, the native helper read moved from 218 to
229, and corrected-test line identities moved. The dedicated batch coverage
adds no new checker finding; it only shifts the three test-line identities
updated above. No inventory conclusion relies on the prior run.

Collection and the final serial rerun against the complete corrected Stage B
implementation/test bytes are recorded in section 12.

The three warnings in each pytest run are the established
`PytestAssertRewriteWarning` notices for already imported
`_hypothesis_globals`, `hypothesis`, and `boa`. No warning or selected test was
suppressed.

## 10. Base regression and rollout boundary

The integrated H-02/Base profile suite passes. The shared local fixture uses
explicit zero source, so all existing protocol tests continue exercising
native `block.number`. No Base migration, manifest, registry, configuration,
or live source changed. The existing deployed Base Ledger is not a candidate
for replacement by this work and remains untouched indefinitely.

`migrations/base-mainnet/1004_Ledger.py` intentionally remains historical and
unchanged at SHA-256
`476487b1e7cbdc7bc482f8fdd01e7c269262687799afe81228f4bcf762d82cbf`
(Git blob `a0b2967067742f4419667b5294f74101176159f1`). It passes only the
historical `_ripeHq` and `_defaults` constructor arguments and is therefore
not replayable against the revised three-argument Ledger source. This record
does not edit or retrofit that Base migration. A future Robinhood deployment
migration, owned and reviewed through its separately gated deployment
workstream, must supply the third source argument and verify the immutable
getter and resulting deployment identities.

Robinhood is the first intended deployment of the revised shared source.
Before deployment readiness, a separately approved later gate must:

1. assign the final Robinhood RipeHq and all operational roles;
2. reproduce source/compiler/ABI/creation/runtime identities;
3. pass exact source `0x64` and raw `arbOSVersion()` `116` preflight gates;
4. complete the real-network receipt/ArbSys, sequencer, and bounded
   multi-transaction evidence deferred by row 2;
5. pin the immutable source in the final manifest and verify its getter;
6. prohibit activation on any source/version/identity mismatch;
7. retain fail-closed incident response, with pause/containment rather than a
   source swap; and
8. leave Base state and deployment untouched.

Once a new Ledger has state, ordinary rollback cannot mean replacing it
without a separately reviewed state migration. The only approved failure
posture remains pause, containment, and owner/security review.

## 11. Gate 1 questions for the independent reviewer

Gate 1 must decide, against the exact final hashes in section 12:

1. Is the production source exactly the one-immutable zero/`0x64` design?
2. Does constructor and runtime source failure remain fail-closed without
   native fallback?
3. Are equality, write ordering, lock, pause, authority, arming, high-risk,
   Underscore, identity, zero-address, and configuration semantics preserved?
4. Does the 25-item Teller/Deleverage logical-graph evidence close Checkpoint 0
   row 6 without silently endorsing the residual external-housekeeping risk?
5. Are storage and ABI deltas exact and acceptable?
6. Are artifact and gas identities reproducible and correctly bounded?
7. Is the exact 14-file ceiling preserved?
8. Are the 28 S2 findings correctly deferred in full to Stage C?
9. Does this evidence approve the Stage B production implementation and the
   implementation-sufficiency portion of row 13 while leaving authentic
   receipt/mempool/sequencer behavior, bounded live topology, testnet soak,
   deployment evidence, and the explicit dedicated-external-audit decision
   open as deployment/release-readiness gates?

Gate 1 approval is mandatory before any Stage C work. A same-agent test pass or
this record cannot approve row 6 or any part of row 13. Gate 1 may approve only
row 13's bounded implementation-sufficiency disposition; it cannot close the
remaining deployment/release-readiness requirements listed above.

### 11.1 Exact Gate 1 handoff boundary

The requested Gate 1 dispositions are deliberately bounded:

- **Row 6:** approve the 25-item logical reachability graph and its preservation
  of every current classification, identity, ordering, and broad
  valid-Ripe-caller/external-housekeeping behavior. This is implementation
  evidence, not a new endorsement or expansion of the already accepted
  residual external-housekeeping risk.
- **Row 13:** approve the production implementation and its
  implementation-sufficiency evidence only. Authentic
  receipt/mempool/sequencer behavior, bounded live topology, testnet soak,
  deployment evidence, and the explicit dedicated-external-audit decision
  remain open deployment/release-readiness gates.

The technical approval target is the exact 14-file package:

- constructor and runtime both use the same fixed-selector exact-32-byte raw
  boundary and fail closed for missing, reverting, short, 33-byte, 64-byte,
  greater-than-64-byte, and incompatible returns without native fallback;
- the canonical storage layout is unchanged; the ABI changes only the
  constructor's third source argument and the immutable source getter;
- the deployed Base Ledger remains untouched indefinitely, and its historical
  two-argument migration remains unchanged and intentionally non-replayable;
  and
- Stage C, if separately authorized after Gate 1, is limited to independently
  reconciling the 28 enumerated inventory findings and restoring the clean-S2
  invariant. It may not alter the approved production semantics, expand the
  14-file Stage B implementation, or begin deployment work.

## 12. Final package identity and validation

The final collection and serial commands use the common launcher in section 9
with these exact arguments:

```text
collection:
["--collect-only", "-q", "-p", "no:cacheprovider",
 "--basetemp=/private/tmp/s5-stage-b-validation/pytest-collection-final"]

serial:
["-q", "-p", "no:cacheprovider",
 "--basetemp=/private/tmp/s5-stage-b-validation/pytest-full-final"]
```

Final collection reports:

```text
3,006/3,148 tests collected; 142 deselected; 3 warnings in 1.64s
```

The selected count is the pre-Stage-B 2,951 plus 33 Ledger source-mode and
exact-length cases, 12 Teller classification/reachability cases, and ten
economic-path cases: `2,951 + 33 + 12 + 10 = 3,006`. Relative to the rejected
package, the six additional constructor/runtime parameters are the 33-, 64-,
and greater-than-64-byte return cases. Relative to the prior Gate 1 freeze,
the two additional economic-path cases are the dedicated ArbSys-mode
`withdrawMany` and `claimManyFromStabilityPool` same-identity rejections.

Final serial execution reports:

```text
3,003 passed, 3 failed, 142 deselected, 3 warnings in 348.53s
```

The three failures are exactly:

1. `test_clean_approved_fixture_passes_without_git_or_network`;
2. `test_discovery_order_does_not_change_output`; and
3. `test_command_runs_outside_repository_root_and_is_deterministic`.

Each failure is caused only by applying the intentionally unchanged S2
inventory to the approved Stage B Ledger clock move. All other 3,003 selected
tests pass. No failure is waived as an implementation pass; the package is
correctly blocked from Gate 2 or merge until Stage C reconciles the exact
inventory delta.

`python -m pip check` reports `No broken requirements found.` A final direct
Vyper compile exits `0` and reproduces creation-output SHA-256
`5af8f96a89c226233bf5cc264818a66ce3db3cb5e50684dc6518e4a6591eac29`.

The final non-record file identities are:

| Stage B file | SHA-256 |
| --- | --- |
| `contracts/data/Ledger.vy` | `6bd731a6ce9084de213494ebad09f8e52c782153842708b78f90fa178c06e9e3` |
| `tests/conf_core.py` | `eb83edff2d431de8326d416cd43c274f3add44b2ae739639570a2fa7e749905b` |
| `tests/data/test_ledger.py` | `02171b15e8af2487f416385039ff277d6426e14e2129b75fba94bec616b24d4e` |
| `tests/core/teller/test_teller_deposit.py` | `b58659053054382ed0e9909f1f29dc21121e7d1a4481dbddb6a95e991f414041` |
| `tests/core/teller/test_teller_withdraw.py` | `54b01a66d56189113c1eae48ad6cb7377bb4fe83cc27830fb5f96b444da8f943` |
| `tests/core/teller/test_teller_rebalance.py` | `fb923e7ce7671d9d2f6db52d07e581361774fc00e7db7c8d9d13c8b888eead6d` |
| `tests/core/teller/test_teller_action_block.py` | `747712c09ba45d5495ec77a19e936399c81078e5e82c05496dc878602078936c` |
| `tests/core/deleverage/test_deleverage_swap_collateral.py` | `aa5c584f4fe4d934ac0bb8d167e2b0616b4cd6966dd9ff54588232dbd62ec98f` |
| `tests/core/creditEngine/test_credit_borrow.py` | `1e483db3ff6f824f6dd241bbe00740b3e661de14986e047734eda4c5d914cef9` |
| `tests/core/creditEngine/test_credit_repay.py` | `8d1558bf5a8725e25173583de745f7048e713897e93d531991984e0c01d2da76` |
| `tests/vaults/modules/test_stab_vault_claims.py` | `c24392238771547162ace1e83473113c71881a389c15d6f47ec6c0b457e86d97` |
| `tests/data/test_ledger_action_block.py` | `37d71202a8d7efb81bd014c747eb7984763ada57dad17a2f111668f0124b6f16` |
| `scripts/abis/Ledger.json` | `c6fc1c410e13f144ae9e9d1853378d476fa578211b08f67b23f80c2075bc415f` |

The implementation record's own complete-file SHA-256 is reported externally
after this final section is written; embedding it here would create a
self-referential hash.

Final scope and whitespace checks confirm:

- exactly the 14 authorized Stage B paths differ from the starting commit;
- the index is empty;
- every change is unstaged and uncommitted;
- `git diff --check` passes for tracked paths;
- `git diff --no-index --check /dev/null <path>` reports no whitespace error
  for each new path; and
- every excluded production, inventory, migration, manifest, dependency, and
  planning path remains unchanged.

Stage B stops here for mandatory Gate 1 independent review. Rows 6 and 13,
Stage C, Gate 2, commit, push, merge, deployment, registration,
configuration, governance, signer access, signing, broadcast, and Base
migration all remain open or prohibited as applicable.

## 13. Gate 1 approval and bounded Stage C reconciliation

Section 12 is the immutable Stage B / Gate 1 freeze state. Independent Gate 1
review approved that exact 14-file package at this record's then-complete
SHA-256
`e2c7b92b3ca51f903e0cdb8eb5c5eda3d6c1f2e644a6ee424ea67fe8e8ea9a76`.
That hash is historical `reviewed-at` provenance and does not claim to be the
SHA-256 of this live Stage C record. Gate 1 approved row 6 and only the bounded
implementation-sufficiency portion of row 13. It did not approve Stage C,
Gate 2, integration, merge, deployment, release readiness, or any live action.

The owner subsequently authorized bounded Stage C against that frozen
artifact. The exact Stage C ceiling is:

1. `config/block-clock-inventory.json`;
2. `scripts/check_block_clock_inventory.py`;
3. `tests/inventory/test_block_clock_inventory.py`; and
4. this implementation record.

No production file or Stage B test byte changed in Stage C. Current-`rh`
reconciliation remains a separate Gate 2 prerequisite and was not performed.

### 13.1 Exact 28-finding reconciliation

The 28-row table in section 9 remains the row-by-row disposition authority.
Stage C applied it without adding or dropping a finding:

| Original finding(s) | Final inventory action |
| --- | --- |
| 1 | remove the superseded direct-guard cadence candidate |
| 2–3 | repin the two existing cadence candidates and add exact S5 review-artifact provenance |
| 4–23 | add or replace the 20 reviewed cadence candidates with exact S5 review-artifact provenance |
| 24 | change the top-level production baseline from `100/95/17` to the source-derived `99/94/17` |
| 25–26 | remove the two superseded BN-002 direct occurrences |
| 27 | add the sole replacement BN-002 occurrence at `_getActionBlock` / `return block.number`, retaining the existing BN-002 semantic classification and commit provenance and adding S5 review-artifact provenance |
| 28 | add `contracts/testing/ActionBlockIdentityProbe.vy` as a testing path with its source hash and S5 review-artifact provenance |

The final inventory therefore contains 99 direct records, 474 cadence
candidates, and 93 Vyper path classifications. Twenty-four surviving records
from the 28 dispositions carry the additional per-record field
`s5ReviewArtifactSha256`: 22 cadence records, one direct BN-002 replacement,
and one testing-path record. Its only accepted value is the lowercase
64-hex frozen Gate 1 artifact hash above.

All original `semanticReview.commit` values remain unchanged. All roots,
exclusions, cadence patterns, stable semantic IDs, authorities, historical
provenance, and inventory records outside the exact reconciliation set remain
unchanged. The checker pins a canonical fingerprint of those excluded legacy
bytes:

```text
924a559075d5b96bcac3f73d28390deee3b436fe5500adc4fb6bf769282217b4
```

The checker rejects:

- missing S5 artifact provenance on any enumerated surviving record;
- malformed, uppercase, legacy-commit-length, mismatched, or live-record
  hashes in that field;
- the S5 field on any record outside the exact allowlist;
- any mutation of the byte-preserved legacy inventory subset; and
- any source, classification, count, cadence, or path drift already covered
  by the pre-existing fail-closed checks.

The aggregate count change is not itself a record. It is deterministically
bound by `EXPECTED_PRODUCTION_COUNTS = (99, 94, 17)`, the inventory's matching
top-level declaration, source recomputation, and the existing
`INV-DIRECT-COUNT` / `INV-SCHEMA-BASELINE` failures.

### 13.2 Gate 1 errata and validation boundary

Gate 1 Minor M-1 was a 41-character Teller blob typo in section 2. This live
record corrects it to the actual unchanged 40-character blob
`1f6dca65bb1fb64deb0067b89e612979c76e0bb8`. No Teller byte changed.

Gate 1 Minor M-2 remains a deliberately deferred test-byte erratum. The two
dedicated ArbSys batch tests use bare `boa.reverts()` for the second batch.
Their first identically shaped batch succeeds, their full before/after state
tuples prove rollback, and independent review proved both tests fail if
Ledger regresses to native `block.number`; Gate 1 therefore did not condition
approval on reopening them. Whenever either authorized S5 test file next
legitimately reopens, both assertions must be strengthened to the exact
`one action per block` reason and the inventory must reconcile the two
additional cadence entries produced by those literals. Stage C does not
change either test byte and does not hide or close this tracked erratum.

The controlled ArbSys tests install code at `0x64`, replace the RipeHq Ledger
registry entry, and enable the guard. Their isolation depends on Titanoboa's
automatically loaded pytest plugin wrapping each test in `boa.env.anchor()`.
Disabling pytest plugin autoload is unsupported for this validation and would
allow state to leak between tests. The locked runner retains plugin autoload;
it disables only pytest's cache provider.

### 13.3 Stage C validation and Gate 2 boundary

Stage C adds exactly nine selected inventory-security cases:

1. one complete 24-record allowlist, pinned-value, legacy-commit-preservation,
   and legacy-fingerprint case;
2. six fail-closed cases for missing, malformed, uppercase, mismatched,
   legacy-commit-length, and live-record hashes;
3. one case rejecting the S5 field on a legacy record; and
4. one case rejecting a mutation outside the S5 reconciliation set.

No pre-existing test or parameter case was deleted, renamed,
de-parameterized, weakened, skipped, or xfailed. No warning or assertion was
suppressed. Against the reviewed Gate 1 baseline of 3,006 selected and 142
deselected tests, `N = 9`, so final collection must select 3,015 tests and
retain the same 142 deselections.

The final locked-runtime results are:

| Gate | Stage C result |
| --- | --- |
| standalone inventory checker | exit `0`; zero findings; `CLOCK_INVENTORY_OK` with `99/94/17`, 99 BN records, 474 cadence candidates, and 93 Vyper paths |
| complete S2 inventory suite | final exact-byte rerun: `69 passed, 3 warnings in 29.31s`, including all nine new Stage C cases and the three formerly failing clean-inventory cases |
| collection | `3,015/3,157 tests collected; 142 deselected; 3 warnings in 1.72s`; exact arithmetic `3,006 + N(9) = 3,015` |
| complete serial suite | `3,015 passed, 142 deselected, 3 warnings in 343.69s`; no failure, skip, or xfail |
| `python -m pip check` | `No broken requirements found.` |
| whitespace and four-file Stage C scope | tracked Stage C delta: inventory `+367/-27`, checker `+380/-3`, inventory tests `+136/-5`; this record is the fourth authorized file; tracked and untracked whitespace checks clean; index empty; only these four hashes differ from the frozen Gate 1 package |

The final Stage C file identities are:

| Stage C file | SHA-256 |
| --- | --- |
| `config/block-clock-inventory.json` | `862b585ff8deafcffa58eb8518a04473e2c154e33d5ec42f0a08ea0e72c85946` |
| `scripts/check_block_clock_inventory.py` | `be62e87a065482431fadc710c793d1c11b9c4946cf78f03f7d5c060f29f42b3b` |
| `tests/inventory/test_block_clock_inventory.py` | `c2c0897888d99c75377d5f1352944d33a3dad7342285ddfefdd62748d619df87` |

This implementation record's new complete-file SHA-256 is reported externally
after this section is final; embedding it would be self-referential.

Stage C implementation is not Gate 2 approval. Gate 2 must independently
recompute `99/94/17` from source, review the checker and provenance enforcement
as security-critical, verify the exact four-file Stage C delta and final
hashes, confirm current-`rh` reconciliation separately, and decide final
merge readiness. Commit, push, merge, deployment, registration,
configuration, activation, governance, signer access, signing, broadcast,
Base migration, and release activity remain prohibited.

## 14. Post-H-01 reconciliation and locked validation — 27 July 2026

This section is the controlling post-H-01 reconciliation and validation
snapshot. It appends to and supersedes only the current-candidate identities,
topology, environment, and results in the historical Gate 1 and Stage C
sections above. It does not rewrite or invalidate their contemporaneous
results or review boundaries.

### 14.1 Reconciliation identity, ancestry, and scope

The final controlling `rh` identity was:

| Item | Exact identity |
| --- | --- |
| controlling `rh` commit | `7098211db5693f986b65ec7a9e897f3518e9538c` |
| controlling `rh` tree | `c07329ed9fcc2dc99afbef3f7888f478024d1ede` |
| frozen S5 parent | `ed10d4d13fb22c2d00ad2dc06b4faece1e2629f3` |
| original S5 / `rh` merge base | `332ae2bc8e0ce4b694766d6d20759295d9267ec3` |
| reconciliation merge commit | `89c832cd35cee3acce6bc08569ae95cc3facce8a` |
| reconciliation merge tree | `7c86b23b0ce9b5eae779e28ee7949a8dc323623f` |
| merge parent 1 | `ed10d4d13fb22c2d00ad2dc06b4faece1e2629f3` |
| merge parent 2 | `7098211db5693f986b65ec7a9e897f3518e9538c` |

The merge used normal Git merge ancestry: no rebase, squash, amendment,
cherry-pick, or history rewrite. The frozen S5 commit `ed10d4d…` remains
unchanged as first parent and is an ancestor of the reconciled candidate.
After the merge, `git rev-list --left-right --count rh...HEAD` returned
`0 19`: the candidate is 19 commits ahead of and zero commits behind the
controlling `rh`.

The exact 11-path incoming contribution from the original merge base through
the controlling `rh` was:

1. `docs/chains/rh/evidence/dependency-exception-exit-preflight.md`;
2. `docs/chains/rh/evidence/dependency-security-gate.md`;
3. `docs/chains/rh/evidence/h01-exception-retirement-feasibility.md`;
4. `docs/chains/rh/evidence/robinhood-blueprint-phase-a.md`;
5. `docs/chains/rh/evidence/robinhood-migration-phase-a.md`;
6. `docs/chains/rh/evidence/stock-token-m1-exact-receipt.md`;
7. `docs/chains/rh/track-6-s6-track-7-h4-defaults-parameters.md`;
8. `docs/chains/rh/track-7-h3-robinhood-blueprint-omissions.md`;
9. `requirements.in`;
10. `requirements.txt`; and
11. `tests/deployment/test_dependency_gate.py`.

Its intersection with the complete 24-path S5 contribution was empty. The
merge preview and completed merge therefore had zero candidate-path conflict
and did not change an approved S5 byte.

### 14.2 Final H-01 lock and private validation environment

The final H-01 requirement identities were:

| File or inventory | SHA-256 |
| --- | --- |
| `requirements.in` | `1227d9681d8b37f6820a7c09fa33b87798229e613748085e45454efea962a2b9` |
| `requirements.txt` | `214f6c32c628df1eb2bbb1979b3bae8147ceaf338e68959dd58d82394b9be010` |
| canonical installed inventory, 93 rows | `f0393df6e4c1728b28d95e5034fee7b6ca4c5463df8fb387dbae839e15b87e4d` |

Relative to the pre-H-01 lock, exactly three packages changed:

| Package | Previous | Final |
| --- | --- | --- |
| Click | `8.2.1` | `8.3.3` |
| Pygments | `2.19.2` | `2.20.0` |
| Pymdown Extensions | `10.16.1` | `10.21.3` |

The security-relevant execution stack remained `pytest 8.4.2`,
`titanoboa 0.2.7`, and `vyper 0.4.3`; `cbor2 5.9.0` also remained pinned.

Validation used Python `3.12.0` in the fresh mode-`0700` root
`/private/tmp/s5-post-h01-reconcile.WIZBZp`, with its private virtual
environment, gate-specific Boa caches under `boa/`, and unique pytest base
temporary directories under `basetemps/`. Tests that require the non-secret
explorer placeholder used `ETHERSCAN_API_KEY=local-placeholder`. No RPC or
signing credential was present or read.

The installed-inventory digest was independently recomputed before this
section was written from the documented canonical serialization:

```python
from importlib.metadata import distributions
import sys

rows = sorted(
    "{}=={}".format(d.metadata["Name"].lower(), d.version)
    for d in distributions()
)
sys.stdout.buffer.write(("\n".join(rows) + "\n").encode("utf-8"))
```

The exact private interpreter produced 93 newline-terminated rows and
SHA-256
`f0393df6e4c1728b28d95e5034fee7b6ca4c5463df8fb387dbae839e15b87e4d`.
This is the controlling lowercase 64-hex value. A prior handoff omitted its
final `d`; that truncated value is invalid and is not used here.

The complete non-semantic retry chronology was:

1. the initial sandboxed `git merge --no-edit 7098211d…` was blocked before
   ref mutation because Git could not lock the worktree `ORIG_HEAD`; the exact
   authorized merge command then succeeded with the necessary filesystem
   access;
2. the preserved historical interpreter at
   `/private/tmp/h01-final-review.dL2pqo/candidate/bin/python` still contained
   Click `8.2.1`, Pygments `2.19.2`, and Pymdown Extensions `10.16.1`, so it
   was rejected before any validation test ran;
3. the first fresh-environment installation attempt was blocked by sandbox
   DNS restrictions; the identical approved public-PyPI installation
   succeeded without changing the lock;
4. S1's first sandboxed attempt produced 57 setup errors because the
   `free_port` fixture could not bind a local socket; the identical local-only
   retry with socket permission produced 57 passes;
5. the first standalone checker command omitted its required `--check`
   option and returned usage exit `2`; the corrected invocation returned exit
   `0` with zero findings; and
6. during preparation of this section, an ambient-interpreter digest check
   was discarded because that interpreter contained 119 packages. Repeating
   the exact canonical serialization with the private validation interpreter
   produced the controlling 93-row digest above before any repository byte
   was edited.

None of these retries changed source, tests, assertions, selection,
dependencies, or expected behavior.

### 14.3 Reconciled validation results

The complete locked-runtime validation results were:

| Gate | Reconciled result |
| --- | --- |
| H-01, ambient `NO_COLOR` absent | `45 passed, 3 warnings in 2.60s` |
| H-01, `NO_COLOR=1` | `45 passed, 3 warnings in 2.45s` |
| H-02 / Base | `99 passed, 3 warnings in 14.17s` |
| S1 clock profiles | `57 passed, 3 warnings in 106.03s` |
| complete probe suite | `154 passed, 3 warnings in 32.12s` |
| focused Ledger / Teller action-block suite | `45 passed, 3 warnings in 139.19s` |
| dedicated batch cases | `2 passed, 3 warnings in 109.07s` |
| exact nine-file targeted regression set | `447 passed, 3 warnings in 143.61s` |
| standalone S2 checker | exit `0`; zero findings; exact production `99/94/17` |
| complete S2 inventory suite | `69 passed, 3 warnings in 29.36s` |
| `python -m pip check` | `No broken requirements found.` |
| fresh collection | `3,044/3,186 tests collected; 142 deselected in 7.04s` |
| complete serial suite | `3,044 passed, 142 deselected, 3 warnings in 352.72s` |

The checker emitted:

```text
CLOCK_INVENTORY_OK schema=1 production_occurrences=99 production_lines=94 production_files=17 bn_ids=32 bn_records=99 indirect_ids=1 cadence_candidates=474 seconds_unit_candidates=58 timestamp_ids=11 timestamp_occurrences=37 mixed_clock_functions=4 vyper_paths=93
CLOCK_INVENTORY_NONPROD mock=0/0/0 testing=2/2/1 test=34/32/7
CLOCK_INVENTORY_NONPROD_CADENCE mock=0 testing=1 test=172
```

There were zero failures, skips, xfails, warning suppressions, assertion
relaxations, or new deselections. The three warnings were the established
pytest assertion-rewrite warnings for `_hypothesis_globals`, `hypothesis`,
and `boa`.

For this reconciled candidate, `3,044 selected / 3,186 total / 142
deselected` supersedes the historical Stage C snapshot of `3,015 selected /
3,157 total / 142 deselected`. The historical section 13 snapshot remains
unchanged as the contemporaneous pre-H-01 result.

### 14.4 Reproduced Ledger compiler and artifact identities

The reconciled candidate reproduced the following identities under Vyper
`0.4.3+commit.bff19ea2`:

| Artifact or comparison | Exact result |
| --- | --- |
| baseline Ledger source SHA-256 | `00d86847273621857b80701be5faf7ca88ff9505f68671d5b6ab3c8b4ec972e0` |
| current Ledger source SHA-256 | `6bd731a6ce9084de213494ebad09f8e52c782153842708b78f90fa178c06e9e3` |
| settings/compiler-input output SHA-256 | `94e854f66051117f6988116763754f6b43f7cd33902ca927e278d902e61eaa11` |
| raw current storage-layout output SHA-256 | `7213fc05a17fd978ff618610263114fc4aa4fd7471d7e1047ec3e0ea11d27227` |
| canonical baseline/current storage-layout SHA-256 | `bb19201a6bf4f4ef2649e5054e0fce6a53f007af4e4a004365edcc245c7e45a6`, equal, 37 entries |
| integrity-output file SHA-256 | `04e43bd3f6b29ab5070a98f53a79db1274de26d2e0b59513f0b5d9bdab0c5cfb` |
| compiler integrity value | `62cc9e492ee1b1a3e84ad104507d684dc81edecef969fc0ae0f7a1586dd0d830` |
| ABI compiler-output SHA-256 | `ac8cc634b24c896381e473c6dd1a8681f28de5edb926b2e65190eba26bd9ff8b` |
| normalized compiler/generated ABI SHA-256 | `695654b0ecbe794c2c7893fdc1af1c3bbce58cd77eeb848ec07079961b34b54b` |
| ABI-with-gas-estimates SHA-256 | `eeb67f2516cf2af7deffc1a0d42f5e95470d5c0ebe7e609b39fb4603057abf22` |
| committed/generated `Ledger.json` | byte-identical; SHA-256 `c6fc1c410e13f144ae9e9d1853378d476fa578211b08f67b23f80c2075bc415f` |
| creation CLI-output SHA-256 | `5af8f96a89c226233bf5cc264818a66ce3db3cb5e50684dc6518e4a6591eac29` |
| creation bytecode | 13,730 bytes; raw SHA-256 `a31f400f5364f8dbbd22b79bea2557f7f3dd57538eb659c06a21e18e9d8e9127`; Keccak-256 `0xe9d55d68fa1bb9122e93a69b8b2a37f81033c3a9e958c8caac5e8bc134be47fd` |
| runtime CLI-output SHA-256 | `28f0f80a383251472ef3a40116ab5b6fb25d1141e3df586a307e3c0d3972a1ad` |
| runtime bytecode template | 13,125 bytes; raw SHA-256 `8fbc85b5bac4586fdb4fc432284f9c38d12ed3966b2de5630f9d4c80973dcce7`; Keccak-256 `0xf45131f4322bf240a2285d39d6c00f04a0a1c158dcdb693919112746474c49c2` |
| method identifiers SHA-256 | `bf49ac79ece839fd3795cf39368614be787e32cf2efc725a33bc87a90e6ba6f5` |
| metadata SHA-256 | `e8375b768c959cbfe005420ee3fa1a12c3dc60286805c79ef2ba50294f3b7b2a` |
| combined JSON SHA-256 | `15e19b2c17e39b6d37776c2aa1f671e13ff38f307b6f3e63a5585ae224bc8d83` |
| compiler archive, raw | `385b6d53fa03a13880cb5f6da195c59aaeb196f74c95d37f7846907b31a6a08d` |
| compiler archive, base64 | `1a4151fa1175ccb5293e3b53f2bd20098b3667e1f1e35cfcaaf7a472784d6138` |

### 14.5 Preserved S5 bytes and authority boundary

Only this implementation record changes in the present append-and-supersede
update. The other 16 approved Stage B / Stage C files remain at their reviewed
identities:

| File | SHA-256 |
| --- | --- |
| `config/block-clock-inventory.json` | `862b585ff8deafcffa58eb8518a04473e2c154e33d5ec42f0a08ea0e72c85946` |
| `contracts/data/Ledger.vy` | `6bd731a6ce9084de213494ebad09f8e52c782153842708b78f90fa178c06e9e3` |
| `scripts/abis/Ledger.json` | `c6fc1c410e13f144ae9e9d1853378d476fa578211b08f67b23f80c2075bc415f` |
| `scripts/check_block_clock_inventory.py` | `be62e87a065482431fadc710c793d1c11b9c4946cf78f03f7d5c060f29f42b3b` |
| `tests/conf_core.py` | `eb83edff2d431de8326d416cd43c274f3add44b2ae739639570a2fa7e749905b` |
| `tests/core/creditEngine/test_credit_borrow.py` | `1e483db3ff6f824f6dd241bbe00740b3e661de14986e047734eda4c5d914cef9` |
| `tests/core/creditEngine/test_credit_repay.py` | `8d1558bf5a8725e25173583de745f7048e713897e93d531991984e0c01d2da76` |
| `tests/core/deleverage/test_deleverage_swap_collateral.py` | `aa5c584f4fe4d934ac0bb8d167e2b0616b4cd6966dd9ff54588232dbd62ec98f` |
| `tests/core/teller/test_teller_action_block.py` | `747712c09ba45d5495ec77a19e936399c81078e5e82c05496dc878602078936c` |
| `tests/core/teller/test_teller_deposit.py` | `b58659053054382ed0e9909f1f29dc21121e7d1a4481dbddb6a95e991f414041` |
| `tests/core/teller/test_teller_rebalance.py` | `fb923e7ce7671d9d2f6db52d07e581361774fc00e7db7c8d9d13c8b888eead6d` |
| `tests/core/teller/test_teller_withdraw.py` | `54b01a66d56189113c1eae48ad6cb7377bb4fe83cc27830fb5f96b444da8f943` |
| `tests/data/test_ledger.py` | `02171b15e8af2487f416385039ff277d6426e14e2129b75fba94bec616b24d4e` |
| `tests/data/test_ledger_action_block.py` | `37d71202a8d7efb81bd014c747eb7984763ada57dad17a2f111668f0124b6f16` |
| `tests/inventory/test_block_clock_inventory.py` | `c2c0897888d99c75377d5f1352944d33a3dad7342285ddfefdd62748d619df87` |
| `tests/vaults/modules/test_stab_vault_claims.py` | `c24392238771547162ace1e83473113c71881a389c15d6f47ec6c0b457e86d97` |

The seven previously committed S5 probe/evidence paths also remain unchanged:

| File | SHA-256 |
| --- | --- |
| `contracts/testing/ActionBlockIdentityProbe.vy` | `95716e4e2b383f2a07826be94d9ee402d263eec522bb4f77efd72a5e5f6eafe5` |
| `docs/chains/rh/evidence/ledger-action-block-mainnet-fork.json` | `69baafbe41a73b2c3f447ce505d65156f9380b1081428faa587f1f0b193bea37` |
| `docs/chains/rh/evidence/ledger-action-block-testnet-fork.json` | `ff66834d5d961047a3be3094df2ff01d0edc6efab92ede10e719cd14d31f9f15` |
| `docs/chains/rh/evidence/ledger-action-block-testnet-proof.md` | `3cca1e14aa9103cd94388184c4a7e6c69aea66d448683ebcdc38e7943c7cf428` |
| `docs/chains/rh/ledger-guard-security-decision.md` | `15610bac4293d06320581dc1603b2980ea352af55d89f040ccab18ca26c9e739` |
| `scripts/probes/action_block_identity_probe.py` | `00fd4a4194a8da87fcf9f49f43cfae9fbdc6af3ddeb6437e5f9812f66a5fa507` |
| `tests/probes/test_action_block_identity_probe.py` | `e81e9279f0a44426f3c9a841108fbe2a5c3df626ea65426682eca76be0601f74` |

Reconciliation, validation, and this bounded documentation update are not
independent Gate 2 approval, push authority, `rh` integration authority,
deployment authority, or release readiness. No commit, push, integration,
deployment, registration, configuration, activation, governance, RPC or
signer access, signing, broadcast, Base migration, or release action is
authorized by this record.
