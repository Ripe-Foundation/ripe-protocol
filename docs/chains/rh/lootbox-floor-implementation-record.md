# Track 6 S3 Lootbox Floor Implementation Record

**Status:** Mandatory reviewer gate 1; inventory reconciliation is intentionally
blocked

**Evidence date:** 24 July 2026

**Starting `rh` commit:** `f0bfd0fd5ac2be1d27321463b77248c7cd91d829`

**Planning baseline named by the brief:**
`c2ded229fefe2ad614693c999bd89faeaec1535e`

**Production implementation commit:**
`f40dc25ff0352b6ce79944fb28c37499da7bf0f0`

**Branch:** `rh-track-6-s3-lootbox-floor`

**Worktree:**
`/Users/wigglez/dev/ripe-protocol-track-6-s3-lootbox-floor`

This record covers only Stage 1 of
`docs/chains/rh/track-6-s3-lootbox-floor.md`. It is not a deployment approval,
an inventory approval, or a merge-readiness claim.

## Approval provenance and implemented decisions

The integrated S3 brief records that the owner approved all four decisions on
23 July 2026 and selected Decision 3 option 1. The same record says the
independent brief reviewer approved the contract and recommended the
`max_value(uint256)` floor guard.

The implementation applies the four decisions without extension:

1. `MIN_UNDERSCORE_SEND_INTERVAL` is an immutable, is initialized even when the
   mutable interval is zero, rejects both zero and `max_value(uint256)`, and is
   exposed by `minUnderscoreSendInterval()`.
2. Distribution eligibility remains exactly
   `block.number > lastUnderscoreSend + underscoreSendInterval`; equality is
   still too early.
3. Base uses a `43_200` floor and existing default interval. The tested
   Robinhood floor is the approved final `7_200`, including a disabled
   deployment with interval zero.
4. Base and Robinhood use one source and constructor interface. Different
   immutable constructor values are allowed to produce different deployed
   runtime. Base convergence remains a future, coordinated forward rollout.

No chain ID, network, token, or address conditional was added.

## Bootstrap and untouched baseline

The integration worktree was clean and `rh`, `origin/rh`, and the integration
worktree all resolved to the starting commit. Integrated S1 head
`868e46ee03a934245df36752a96d41a7333c0091` and S2 head
`f0e556ce20bd21622752d441b358d23cb2b17ec2` were ancestors of `rh`.
The branch and worktree did not exist before bootstrap.

### Starting hashes

| Input | SHA-256 |
| --- | --- |
| S3 brief | `e90daeeb79d636d7296b1f5b6320008d41ae5fe64c26e6e7fae776ebd922c7dd` |
| Shared block-clock specification | `ad0ee08e40bdc7c1e9233dbdc33f70b5a479a2c8e59e75b5bc2350730b121c68` |
| Block-clock validation plan | `e3f5d73fa9588aba28ac8823b74c5d523d1e0e6451d29d47f352a87fe03371f2` |
| Starting `contracts/core/Lootbox.vy` file | `3c8a011b9c56c953281d3a6b2e13aa2c11a9e57026709252c5e62690122f2d00` |
| Starting `scripts/abis/Lootbox.json` file | `c3354987912c92869db649fc19b085bcc1a181d31ca907adc056f283d439a1b6` |
| S2 checked inventory | `50a842e4c1ce9ff67e520184d3e9cfcd663df77f40c3cc5ce584f843094b31dd` |

The implementation source file SHA-256 is
`669c2857e2402ef0e8f9a508dd6f342426ffbd1affce11dd429e5b5b0129ae65`.
The generated implementation ABI file SHA-256 is
`33aadc219718332ef9163f0b85c8e6fba93735d149db3fb0bb2e3fab814db17c`.
The S3 brief, both Track 6 specification inputs, and the S2 inventory retain
their starting hashes.

### Toolchain

| Tool | Version |
| --- | --- |
| Vyper CLI | `0.4.3+commit.bff19ea2` |
| Vyper package | `0.4.3` |
| Titanoboa | `0.2.7` |
| pytest | `8.4.2` |

Local pytest imports require `ETHERSCAN_API_KEY` to exist even for non-fork
tests. Validation used the non-secret value `local-placeholder`; no secret or
live fork was accessed. Titanoboa used its existing local compiler cache.

### Clean S2 baseline

The untouched starting commit returned:

```text
CLOCK_INVENTORY_OK schema=1 production_occurrences=100 production_lines=95 production_files=17 bn_ids=32 bn_records=100 indirect_ids=1 cadence_candidates=424 seconds_unit_candidates=58 timestamp_ids=11 timestamp_occurrences=37 mixed_clock_functions=4 vyper_paths=92
CLOCK_INVENTORY_NONPROD mock=0/0/0 testing=0/0/0 test=27/25/4
CLOCK_INVENTORY_NONPROD_CADENCE mock=0 testing=0 test=130
```

### Baseline source and call-site findings

- `ONE_DAY` was declared once and used only by the constructor and setter
  minimum checks.
- The separate distribution gate used strict `>` before S3 and still does.
- A zero initial interval skipped the interval check and left rewards disabled.
- The active test fixture passed interval `43_200`.
- SwitchboardCharlie timelocked and forwarded the interval without its own
  floor.
- `DefaultsBase.vy` had no Lootbox floor or interval.
- `scripts/params/general.py` formats `underscoreSendInterval` through
  `format_blocks_to_time`. That CAD-001 reporting work remains owned by S10 and
  is unchanged.
- The active source-based deployment call is the central fixture in
  `tests/conf_core.py`.
- Historical constructor call sites are
  `migrations/base-mainnet/1016_Lootbox.py`,
  `migrations/base-mainnet/2025071801_LootBoxPointsRefresh.py`,
  `migrations/base-mainnet/2025080900_Lootbox.py`, and
  `migrations/base-mainnet/2025112500_New_Endaoment_Features.py`. They are
  historical records and were not updated.
- A future Robinhood deployment is owned by Track 7. Its reserved
  `0010_Track6S3LootboxFloor.py` meaning is a predeployment artifact assertion;
  S3 did not create that file.

Historical file hashes remain:

| Historical input | SHA-256 |
| --- | --- |
| `1016_Lootbox.py` | `fce8645fe23f65085ffe8b6b0c6098a857c298f14f3185b84331577c02f2a0c0` |
| `2025071801_LootBoxPointsRefresh.py` | `3665b0334902a764b9d51c29022c2b99701f51d301c3034e8738164149c9b893` |
| `2025080900_Lootbox.py` | `f98b8884a35a412503d43ef8772197fd8e2c05415e8806773ae5cf9aebb9260a` |
| `2025112500_New_Endaoment_Features.py` | `bdbe2ae2749da6c42b0a347034515544cfb5b60498a6180af66c38960155edb1` |
| Current Base manifest | `06ac6dcf3d5c3d2366bd33118023fd6603fc4d759a7a5103901b29ae67007b00` |

The starting Git tree IDs are
`e7db6ed257f00d7ceb081716953920b897f01ee0` for
`migrations/base-mainnet` and
`12b59cf73855a673946f88f69e30000e51681992` for `migration_history`.
Both trees are byte-identical on the implementation commit.

## Production change

The constructor order is now:

```text
(
  _ripeHq,
  _minUnderscoreSendInterval,
  _underscoreSendInterval,
  _undyDepositRewardsAmount,
  _undyYieldBonusAmount
)
```

The floor is immediately before the mutable initial interval. This is the
smallest insertion that keeps all existing arguments in their relative order
and puts the two easily confused interval values adjacent, with the immutable
safety bound first.

The production delta is limited to:

- replacing the Base-specific `ONE_DAY` constant with immutable
  `MIN_UNDERSCORE_SEND_INTERVAL`;
- validating and unconditionally assigning the constructor floor;
- using that immutable in the nonzero constructor interval check and setter;
  and
- adding the external view `minUnderscoreSendInterval()`.

Every other constructor assignment, permission, pause guard, setter check and
order, state write, event, allocation, reward amount, RIPE availability rule,
and strict distribution boundary is preserved.

The exact Stage 1 changed-file set is:

- `contracts/core/Lootbox.vy`;
- `tests/conf_core.py`;
- `tests/core/lootbox/test_underscore_rewards.py`;
- `tests/config/test_switchboard_charlie.py`;
- `scripts/abis/Lootbox.json`; and
- this new `docs/chains/rh/lootbox-floor-implementation-record.md`.

## Test evidence

### Constructor matrix

All nine required rows pass:

| Floor | Initial interval | Result |
| ---: | ---: | --- |
| `0` | `0` | `invalid floor` |
| `max_value(uint256)` | `0` | `invalid floor` |
| `43_200` | `43_199` | `invalid interval` |
| `43_200` | `43_200` | Base-enabled deployment |
| `43_200` | `43_201` | deployment |
| `7_200` | `0` | Robinhood-disabled deployment |
| `7_200` | `7_199` | `invalid interval` |
| `7_200` | `7_200` | explicit future-enabled deployment |
| `7_200` | `7_201` | deployment |

The `7_200`/zero case also proves the getter retains `7_200`, the mutable
interval and both reward amounts remain zero, `hasUnderscoreRewards` remains
false, distribution is blocked, and a later setter call is bounded by `7_200`
without automatically enabling rewards.

### Setter and boundary matrix

For both `43_200` and `7_200`, focused tests cover an unauthorized caller,
floor minus one, `max_value(uint256)`, exact floor, floor plus one, emitted
`UnderscoreSendIntervalUpdated.numBlocks`, no change, and pause rejection.
SwitchboardCharlie separately proves that a timelocked floor-minus-one value is
forwarded unchanged and rejected by Lootbox while the pending action and
original interval remain intact.

Using the integrated S1 controller under `base_canonical` and
`robinhood_candidate` parameter profiles:

- `last + interval - 1` and equality both revert `too early`;
- `last + interval + 1` distributes;
- BN-026 observes identical `lastUnderscoreSend` and
  `UnderscoreRewardsDistributed.blockNumber`;
- a repeated number remains ineligible under BN-025/CM-033; and
- every point after the initial send in `R-J2-J4` and `R-STRESS60` remains
  inside the interval and cannot bypass it.

The optimized Vyper user assertion is exposed to the generic S1 observed-call
normalizer as `0x`. Each checked rejection therefore first asserts the named
`too early` revert directly with Titanoboa, then records the same call through
the BN-025/CM-033 observed-call diagnostic as `0x`. The two assertions cover
both the contract-level revert contract and the reusable S1 trace format.

The same `contracts/core/Lootbox.vy` deployer supplies both parameter profiles.

## ABI generation and comparison

The ABI was generated, not hand-edited, with the pinned compiler:

```text
PYTHONPATH=. python scripts/export_abis.py --output-dir /private/tmp/rh-track-6-s3-abi.DzgL7S
```

The temporary run produced 49 ABI files and reported known compilation
failures in other modules. Comparison found pre-existing generated-output
differences in `Deleverage.json`, `EndaomentPSM.json`,
`SwitchboardAlpha.json`, `SwitchboardDelta.json`, and
`wsuperOETHbPrices.json`. Those unrelated outputs are outside S3 and were not
copied. Only the generated `Lootbox.json` was updated.

| ABI measure | Starting | Implementation |
| --- | --- | --- |
| File SHA-256 | `c3354987912c92869db649fc19b085bcc1a181d31ca907adc056f283d439a1b6` | `33aadc219718332ef9163f0b85c8e6fba93735d149db3fb0bb2e3fab814db17c` |
| Normalized JSON SHA-256 | `5529602a50f22396d9af92ac108582e8c22ea0463be1d330c50b63aa4ffd2cc7` | `e752a206ba5c78cb573c734c7bfd1c407f1cb98898d3d8e9d3513836c56f5fb2` |
| Entries | 50 | 51 |

Normalization used compact, key-sorted JSON. The semantic diff is:

- constructor changes from
  `(address,uint256,uint256,uint256)` to
  `(address,uint256,uint256,uint256,uint256)`, inserting
  `_minUnderscoreSendInterval` immediately after `_ripeHq`; and
- one view function is added:
  `minUnderscoreSendInterval() -> uint256`.

No existing function, event, output, or named interface surface is removed or
renamed.

## Reproducible artifacts

Titanoboa's `CompilerData.source_code`, `integrity_sum`, `bytecode`, and
`bytecode_runtime` were read from the pinned compiler. SHA-256 and Keccak-256
were computed over raw byte arrays; the source hash is SHA-256 over
`CompilerData.source_code`. The file hash and compiler source hash differ
because compiler input is Titanoboa's normalized source representation.

| Artifact | Starting | Implementation |
| --- | --- | --- |
| Compiler source SHA-256 | `3d7fdd84ec2ed9e4f2008e5b104b73f7ed55a3f24ba988e38aa7b626f544d33e` | `ebb4dcca8fa95bafe8e38ddc1d01886bfaceaf06302fe195f63db0bb7b3ef1da` |
| Compiler input integrity | `d968edd935c3f2d321690a5693471c74868a55615cd7439675511e4d33968ded` | `83995dbf831851f53870db14fec4daaea419fb036b7d081a1948ed02222974e1` |
| Creation bytes | 21,799 | 21,911 |
| Creation SHA-256 | `756ea05256de11539786d68ff2ccf1fc48d25f9ff73c2e97832c5d46e32d60b9` | `9246a6d9dbee596750dc3a50d27d4418f318a62b7b4826a13f76aee37621e6ce` |
| Creation Keccak-256 | `05b44353899b59584d548cfcb91dc82a2763f343bd305a165c6bda777f611c99` | `eac656469e5c692146b583e6047d0df3e6792b6fb55a3cfb79c821d599cdea6d` |
| Runtime template bytes | 21,541 | 21,569 |
| Runtime template SHA-256 | `62d5c161a7e00709b58593581ee66ef3437cfc23c9e5c2b6311685bb741582d5` | `db9c2b91497a6e11191a181c9cbe1776e96532e50ff3e60e17f0bd447354e097` |
| Runtime template Keccak-256 | `a00bf2fb14db4a8d8ca345201739d536df80772a39e3cb004dc5785ea0ac624f` | `52bac86d5299ed7625f548a69057d02971630c39b269e06782131a8d8c9ad909` |

### Candidate deployed runtimes

For deterministic comparison, both new candidates use committed Base RipeHq
`0x6162df1b329E157479F8f1407E888260E0EC3d2b`. No Robinhood RipeHq has been
assigned by Track 7, so the Robinhood row is a floor-isolation candidate, not a
claim about final Robinhood deployed runtime. The future manifest must
recompute the hash with the approved Robinhood RipeHq.

All reward amounts below are raw integers:
`100000000000000000000` equals 100 tokens at 18 decimals.

| Profile | Constructor arguments after `_ripeHq` | Runtime bytes | SHA-256 | Keccak-256 |
| --- | --- | ---: | --- | --- |
| Starting/live Base | `43200, 100000000000000000000, 100000000000000000000` | 21,637 | `db139674e84185d013b77211eb769631a9d3c0b5cc45ff90a00e0086095843da` | `b3a2f6516aab23a9842e504b8cc8140167369b84d4f1f4fe787d76078019c6eb` |
| New Base candidate | `43200, 43200, 100000000000000000000, 100000000000000000000` | 21,697 | `fa638d6a25a1386a6afd18afccab2ece9f04029088556b3acc33163a374c7673` | `ce618917599928903b0233cb400fe28a61bbda45d3417aecff14eda417b4136d` |
| New Robinhood floor-isolation candidate | `7200, 0, 100000000000000000000, 100000000000000000000` | 21,697 | `a992e766fd5e8252ded0b2da6e2b1f90ace39a4644936065f1240f17ea65809d` | `9ea55bcdff1d8b39c9db8d89e5cab5b540f83a146904f6998df53ffb5b5f74dc` |

The two new rows use the identical implementation source, compiler input, and
creation artifact (`9246a6...e6ce` SHA-256 /
`eac656...ea6d` Keccak-256). Their deployed runtimes differ exactly as expected
because `MIN_UNDERSCORE_SEND_INTERVAL` is immutable. Holding RipeHq constant in
this comparison isolates that approved floor difference. Mutable constructor
state such as interval and reward amounts does not establish a promise that
future manifests will have these illustrative storage values.

## Committed and live Base evidence

The current committed Base manifest records:

- RipeHq:
  `0x6162df1b329E157479F8f1407E888260E0EC3d2b`; and
- Lootbox:
  `0x1f90ef42Da9B41502d2311300E13FAcf70c64be7`.

Read-only JSON-RPC verification used `https://base-rpc.publicnode.com` without
a secret or transaction. At Base block `49,059,353`, timestamp
`2026-07-24T15:47:33Z`:

- `RipeHq.getAddr(16)` returned the committed Lootbox address;
- `eth_getCode` returned 21,637 bytes;
- live runtime SHA-256 was
  `db139674e84185d013b77211eb769631a9d3c0b5cc45ff90a00e0086095843da`;
  and
- live runtime Keccak-256 was
  `b3a2f6516aab23a9842e504b8cc8140167369b84d4f1f4fe787d76078019c6eb`.

The live hash exactly matches the starting candidate, not the new artifact.
That is the approved temporary old/new version distinction; this record does
not change it.

A read-only latest-state snapshot taken immediately before block `49,059,477`
returned:

| Getter | Value |
| --- | ---: |
| `hasUnderscoreRewards` | `true` |
| `underscoreSendInterval` | `43_200` |
| `undyDepositRewardsAmount` | `25000000000000000000` |
| `undyYieldBonusAmount` | `150000000000000000000` |
| `lastUnderscoreSend` | `49,037,562` |

These values are dated rollout inputs, not authorization to preserve or change
state. A live rollout must resnapshot atomically at its execution block.

## Validation results

### Untouched starting commit

Commands ran serially from the clean integration worktree at
`f0bfd0fd5ac2be1d27321463b77248c7cd91d829`:

| Command | Result | Wall time |
| --- | --- | ---: |
| `PYTHONPATH=. pytest -q tests/core/lootbox/test_underscore_rewards.py` | 41 passed | 63.93 s |
| `PYTHONPATH=. pytest -q tests/config/test_switchboard_charlie.py` | 90 passed | 72.13 s |
| `PYTHONPATH=. pytest -q tests/clock/test_clock_profiles.py` | 57 passed | 63.50 s |
| `PYTHONPATH=. python scripts/check_block_clock_inventory.py --check` | clean S2 output above | 1.67 s |
| `PYTHONPATH=. pytest -q tests/inventory/test_block_clock_inventory.py` | 56 passed | 25.45 s |
| `PYTHONPATH=. pytest -q` | 2,699 passed, 142 deselected | 430.26 s |
| `git diff --check` | clean | <0.01 s |

### Stage 1 implementation

| Command | Result | Wall time |
| --- | --- | ---: |
| `PYTHONPATH=. pytest -q tests/core/lootbox` | 175 passed | 79.06 s |
| `PYTHONPATH=. pytest -q tests/core/lootbox/test_underscore_rewards.py` | 59 passed | 69.42 s |
| `PYTHONPATH=. pytest -q tests/config/test_switchboard_charlie.py` | 91 passed | 73.55 s |
| `PYTHONPATH=. pytest -q tests/clock/test_clock_profiles.py` | 57 passed | 64.76 s |
| `PYTHONPATH=. python scripts/check_block_clock_inventory.py --check` | expected exit 1; exact drift below | 1.43 s |
| `git diff --check` | clean | 0.03 s |

The full Lootbox directory supplies the requested claim, points, RIPE reward,
and Underscore regression coverage. The full repository suite is intentionally
reserved for the post-reconciliation Gate 2 sequence; its untouched baseline
is green as shown above.

## Expected S2 drift before reconciliation

The S2 inventory and checker are unchanged. The Stage 1 checker emits exactly
120 diagnostics:

| Code and path | Count |
| --- | ---: |
| `INV-CADENCE-MISSING`, `contracts/core/Lootbox.vy` | 3 |
| `INV-CADENCE-MOVE`, `contracts/core/Lootbox.vy` | 32 |
| `INV-CADENCE-MOVE`, `tests/core/lootbox/test_underscore_rewards.py` | 35 |
| `INV-CADENCE-NEW`, `tests/core/lootbox/test_underscore_rewards.py` | 29 |
| `INV-DIRECT-MOVE`, `contracts/core/Lootbox.vy` | 21 |

Every diagnostic is accounted for below. There is no `INV-DIRECT-MISSING` or
`INV-DIRECT-NEW`: the 100 direct production occurrences, 95 lines, 17 files,
32 BN IDs, and 100 BN records retain their identities. Stage 2 must still
review and reconcile their diagnostic line positions and the cadence surface.

### Three obsolete cadence rows

The checker reports the removed `ONE_DAY` declaration, constructor comparison,
and setter comparison at former lines 193, 208, and 1299. These are the three
intentional `INV-CADENCE-MISSING` rows.

### Thirty-two moved production cadence rows

All are mechanically moved by the constructor insertion, except the setter
event row also moves past the new getter:

- `_getLatestGlobalDepositPoints`: `662->665`, `664->667`, `670->673`,
  `674->677`, `675->678`, `676->679`;
- `_getLatestAssetDepositPoints`: `697->700`, `699->702`, `705->708`,
  `709->712`, `710->713`, `711->714`, `714->717`;
- `_getLatestUserDepositPoints`: `733->736`, `735->738`, `741->744`,
  `745->748`;
- `_getLatestGlobalBorrowPoints`: `903->906`, `905->908`, `911->914`,
  `915->918`;
- `_getLatestUserBorrowPoints`: `928->931`, `930->933`, `936->939`,
  `940->943`;
- `_getLatestGlobalRipeRewards`: `1095->1098`, `1097->1100`,
  `1103->1106` twice, and `1107->1110` twice; and
- `setUnderscoreSendInterval` event: `1302->1311`.

The duplicate rows are separate cadence tokens on the same source line and
match the checker's cardinality.

### Thirty-five moved existing test cadence rows

The new import moves module `ONE_DAY_BLOCKS` from `7->8`. The focused Section 0
test block then moves these existing rows by 380 lines:

- `test_distribute_underscore_rewards_happy_path`: `51->431`;
- `test_distribute_underscore_rewards_multiple_times`: `87->467`;
- `test_distribute_returns_correct_amounts`: `113->493`;
- `test_distribute_updates_last_send_block`: `138->518`, `147->527`;
- `test_distribute_with_sufficient_ripe`: `167->547`;
- `test_distribute_with_limited_ripe`: `195->575`;
- `test_distribute_requires_switchboard_permission`: `229->609`;
- `test_distribute_reverts_when_paused`: `247->627`;
- `test_distribute_reverts_when_disabled`: `264->644`;
- `test_distribute_reverts_too_early`: `284->664`, `287->667`;
- `test_distribute_exactly_at_interval`: `303->683`, `310->690`;
- `test_distribute_long_after_interval`: `328->708`, `332->712`;
- `test_distribute_reverts_both_amounts_zero`: `387->767`;
- `test_distribute_with_only_deposit_rewards`: `407->787`;
- `test_distribute_with_only_yield_bonus`: `436->816`;
- `test_distribute_with_zero_available_ripe`: `461->841`;
- `test_distribute_with_one_wei`: `481->861`;
- `test_distribute_exact_ripe_match`: `506->886`;
- `test_distribute_reverts_no_underscore_distributor`: `530->910`;
- `test_distribute_decrements_ripe_avail_for_rewards`: `551->931`;
- `test_distribute_after_global_rewards_update`: `589->969`;
- `test_distribute_respects_pending_allocations`: `615->995`, `623->1003`;
- `test_distribute_updates_ledger_new_ripe_rewards`: `647->1027`;
- `test_distribute_emits_correct_event`: `681->1061`;
- `test_set_underscore_send_interval_success`: `767->1147`;
- `test_set_underscore_send_interval_requires_switchboard`: `780->1160`;
- `test_set_underscore_send_interval_reverts_when_paused`: `791->1171`; and
- `test_set_underscore_send_interval_validation`: `803->1183`, `805->1185`.

### Twenty-nine new test cadence rows

The checker reports:

- module line 9: one `ROBINHOOD_DAY_BLOCKS` declaration;
- constructor-matrix lines 80-86: six `ONE_DAY_BLOCKS` occurrences and seven
  `ROBINHOOD_DAY_BLOCKS` occurrences;
- setter parameter line 164: one occurrence of each identifier;
- strict-boundary profile lines 235-236 and jump-profile lines 347-348: two
  occurrences of each identifier across the two tables;
- lines 263 and 379: two `"governed_interval"` block-default-key rows;
- Robinhood disabled test lines 136, 140, 151, 155, and 158: five
  `ROBINHOOD_DAY_BLOCKS` occurrences; and
- setter event assertions at lines 204 and 216: two `numBlocks`
  block-unit-identifier rows.

These multiplicities sum to 29 and correspond to every `INV-CADENCE-NEW`
diagnostic.

### Twenty-one moved direct production rows

All retain their BN identity and move by three lines:

- BN-022, `_getLatestGlobalDepositPoints`: `663->666`, `664->667`,
  `667->670`;
- BN-022, `_getLatestAssetDepositPoints`: `698->701`, `699->702`,
  `702->705`;
- BN-022, `_getLatestUserDepositPoints`: `734->737`, `735->738`,
  `738->741`;
- BN-023, `_getLatestGlobalBorrowPoints`: `904->907`, `905->908`,
  `908->911`;
- BN-023, `_getLatestUserBorrowPoints`: `929->932`, `930->933`,
  `933->936`;
- BN-024, `_getLatestGlobalRipeRewards`: `1096->1099`, `1097->1100`,
  `1100->1103`;
- BN-025, `distributeUnderscoreRewards`: `1211->1214`, `1255->1258`; and
- BN-026, `distributeUnderscoreRewards`: `1265->1268`.

No diagnostic was ignored, suppressed, restamped, or reconciled. Gate 1 must
supply immutable approval provenance for this exact Stage 1 implementation
before any S2-owned file changes.

## Proposed Base forward rollout — not authorized or executed

This is review analysis only. Track 7 and the integration owner must turn it
into a newly numbered forward migration after both S3 gates close.

1. **Pin inputs and owners.** Select a new Track 7 migration ID; pin the
   reviewed implementation commit, compiler input, creation hash, ABI, current
   manifest, current ID-16 address/code hash, and named rollout, rollback, and
   temporary-drift owners. Set an explicit convergence deadline before the
   first live transaction.
2. **Fresh execution-block snapshot.** At one identified Base block, resnapshot
   ID 16 and old/new code hashes plus `hasUnderscoreRewards`,
   `underscoreSendInterval`, `undyDepositRewardsAmount`,
   `undyYieldBonusAmount`, `lastUnderscoreSend`, pending registry/timelock
   actions, and old Lootbox RIPE mint capability. Abort on unexplained drift.
3. **Resolve the pending-window policy.** A new Lootbox has fresh storage and
   `lastUnderscoreSend == 0`; S3 deliberately adds no state-import setter.
   Reviewers must choose whether to make a final eligible old-contract
   distribution immediately before cutover, accept a forfeited partial window,
   or approve a separate continuity design. The new contract must remain
   disabled until the chosen first-send boundary is controlled. Exact state
   continuity would require a new owner/security decision and a production
   change that reopens Gate 1.
4. **Deploy safely.** Deploy the reviewed shared artifact with Base floor
   `43_200`. A conservative sequence is initial interval zero, which keeps
   Underscore rewards disabled and leaves both reward amounts zero, followed by
   reviewed Switchboard restoration of the snapshotted interval and amounts
   while rewards remain disabled. If reviewers instead choose nonzero
   constructor state, the new contract must still lack effective mint
   authority and remain outside ID 16 until cutover checks pass.
5. **Verify the inactive candidate.** Check source/compiler/creation/runtime
   hashes, immutable floor getter, stored values, paused state, Switchboard
   permissions, and the absence of unexpected capabilities. Record the actual
   constructor arguments and manifest.
6. **Prepare the timelocked rewire.** Initiate the RipeHq ID-16 replacement
   under the existing timelock. Until confirmation, Addys and
   SwitchboardCharlie must continue resolving the old Lootbox. Recheck the
   pending action at confirmation time.
7. **Avoid simultaneous mint authority.** Remove or disable the old Lootbox's
   RIPE mint capability before granting it to the new address, using a
   reviewer-approved sequence that never leaves both addresses authorized.
   Confirm ID 16 and then restore the capability only to the address actually
   resolved as Lootbox. If the capability/registry timelocks cannot make that
   invariant atomic, keep rewards disabled through the gap and require an
   explicit security-approved sequence.
8. **Restore and enable.** Through the resolved Switchboard path, verify or
   restore interval `43_200` and the fresh execution-block reward amounts.
   Enable `hasUnderscoreRewards` only at the controlled first-send point.
   Confirm SwitchboardCharlie and every Addys consumer resolve the new ID-16
   address.
9. **Post-change proof.** Verify getters, stored values, floor, ID 16, sole
   mint capability, old/new code hashes, manifests, emitted registry/capability
   and configuration events, strict boundary behavior, one controlled
   distribution, RIPE availability accounting, and no ability for the old
   contract to mint.
10. **Convergence evidence.** Record the actual Base artifact and compare it
    with the Robinhood shared-source/compiler/creation commitment. Close
    temporary live-bytecode drift only when manifests and read-only code hashes
    prove both deployments are on the reviewed shared version.

### Reversibility and rollback reality

- Before registry initiation, abandoning the inactive deployment is
  reversible and does not affect users.
- Before registry confirmation, canceling an allowed pending action or letting
  it remain unconfirmed preserves the old resolution; exact cancellation
  mechanics must be confirmed from the live governance state.
- After ID-16 confirmation but before the capability transition completes,
  rollback is another governed/timelocked registry and capability sequence, not
  an instant local revert. Rewards must stay disabled through any gap.
- After a new-contract distribution, its fresh `lastUnderscoreSend` and reward
  accounting cannot be copied back automatically. Returning to the old
  contract can double count or skip a window unless the execution-block state
  is reviewed; recovery is a forward fix.
- After old mint authority is revoked, restoring it is a privileged live
  action with its own controls. No rollback plan may grant both contracts mint
  authority.

The current live snapshot is useful only for planning. Values and pending
windows can change before execution.

### Temporary live-version drift

The owner approved bounded temporary drift, not permanent divergence. The
Track 7/integration owner must name the accountable rollout owner, start
condition, calendar deadline, maximum allowed state, and escalation path
before deployment. Until those fields are supplied, Base deployment and any
Robinhood claim of convergence remain blocked.

### Robinhood handoff

Track 7 must use the final Robinhood RipeHq address, floor `7_200`, interval
`0`, no Underscore registry/distributor/reward permission at launch, and the
same reviewed source/compiler/creation artifact. The reserved
`0010_Track6S3LootboxFloor.py` is an initial-deployment artifact assertion, not
an onchain upgrade transaction. S6 still owns defaults and the parameter
manifest.

## Gate 1 unresolved items

- An independent reviewer must approve the exact implementation commit,
  generated ABI, hashes, tests, S2 diagnostics, and rollout analysis.
- The reviewer or owner must then provide immutable approval provenance before
  S2 inventory reconciliation begins.
- Stage 2 inventory/checker/test changes, the reconciled S1/S2 run, full suite,
  and mandatory reviewer Gate 2 remain open.
- Production-contract security/audit review remains open.
- Track 7 migration ID, deployment graph, Base and Robinhood RipeHq/capability
  sequencing, manifests, and actual artifact assertions remain open.
- The pending Underscore distribution-window/state-continuity decision remains
  open.
- The temporary-drift owner, exact bounds, and deadline remain open.
- S6 defaults/manifest work and S10 interval-report correction remain open.
- Every live deployment, registry, capability, configuration, verification,
  signing, and transaction approval remains open.
- Owner merge and push remain open.

No historical migration, S2 inventory file, defaults file, parameter report,
dependency, CI file, unrelated ABI, or `docs/chains/rh-summary.md` changed.
No live state-changing action, deployment, push, or merge was performed.
