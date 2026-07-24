# Track 6 S4 Deleverage Cooldown Security and Compatibility Decision

**Status:** Stage A record revised after independent re-review; mandatory
checkpoint 0 open; Stage B blocked

**Prepared:** 24 July 2026

**Original Stage A commit:** `a7414b5b56d20fc753c9263e7b494a75189eb223`

**Re-review correction date:** 24 July 2026

**Stage A launch baseline:** `3e6e6f230169fc445d0b29454457480c62efd89a`

**Branch:** `rh-track-6-s4-deleverage-cooldown`

**Worktree:** `/Users/wigglez/dev/ripe-protocol-track-6-s4-deleverage-cooldown`

## Authorization and stop condition

The owner authorized S4 Stage A only on 24 July 2026. That authorization
supersedes only the pre-kickoff status line in
`track-6-s4-deleverage-cooldown.md`. It does not approve any production
decision, Stage B file, external-repository change, deployment, governance
action, or live transaction.

The owner also selected **H-01 first**. S4 Stage B remains blocked until:

1. H-01 is independently reviewed and integrated into `rh`;
2. this branch is reconciled with that exact dependency baseline under owner
   direction;
3. the baseline, compiler inputs, artifacts, target tests, S1, S2, collection,
   and full suite are reproduced after reconciliation; and
4. the owner and an independent security reviewer approve every checkpoint-0
   decision and the exact Stage B file set.

This record therefore recommends a design but does not select it. No response
to a checkpoint item means no production edit.

## Re-review disposition

The original handoff incorrectly presented the unchanged original Stage A
commit as if it contained the requested re-review corrections. This revision
creates the missing audit trail and resolves the review findings as follows:

| Review item | Disposition in this revision |
| --- | --- |
| Current SwitchboardDelta registry identity was asserted from a stale historical migration | Accepted. Historical ID 4 registration, current manifest deployment, and current onchain registry identity are now separated. The actual current registry slot is an unresolved rollout input and a stop condition. |
| BN-012 occurrence count was understated | Accepted. Deleverage has three occurrences on two source lines, not two occurrences. |
| Strict-boundary matrix omitted required number jumps, expiry skip, and two-user independence | Accepted. Every required case is now explicit in section 10.2. |
| Active-cooldown context-open rule hid a legitimate multi-leg availability cost | Accepted. The trade-off and three checkpoint alternatives are now explicit in sections 5.1, 10.3, 10.4, 12, and 13. |
| H-01 snapshot was stale | Accepted. The latest inspected H-01 tip and its evidence-only branch delta are recorded without treating either as integration or approval. |
| Integration worktree contains uncommitted minimum-change material of unknown provenance | Verified and quarantined logically, not modified. Section 1.1 records the exact dirty scope and requires an owner provenance decision before it can affect S4. |

## Executive security conclusion

The current same-number exception is not a transaction boundary. Independent
transactions in one sequencer batch can share `block.number`, so
`block.number > lastBlock` permits every one of them to bypass an active
cooldown. The exception must not be retained.

The actual committed multi-leg consumer is Underscore
`LevgVaultWallet`, not Ripe `Teller`. `Teller.withdraw`,
`Teller.withdrawMany`, and `Teller.rebalance` contain no production call to
`deleverageForWithdrawal`. Selecting Teller as coordinator would introduce new
production behavior rather than preserve an existing flow.

The recommended direction is:

- preserve one shared chain-portable source;
- preserve the currently enforced Base maximum of `7_200` and derive a
  Robinhood candidate of `1_200` only after S4-specific cadence approval;
- preserve initial stored cooldown `0` and leave nonzero activation to S6 or a
  later separately approved governance release;
- make Deleverage the only maximum authority and make Delta query the current
  registered Deleverage at queue time while Deleverage revalidates at
  execution;
- retain the four-argument ABI as a strict no-context path;
- if an exact coordinator is approved, add a separately named context-aware
  path backed by a Deleverage-managed, transient, nonzero, opaque `bytes32`
  context bound to coordinator and user;
- recognize that denying context opening during an active cooldown can block a
  legitimate multi-leg redemption until expiry, and require checkpoint 0 to
  choose that liveness cost, a tightly bounded alternative, or no active
  nonzero-cooldown context release;
- do not select Teller without a separately reviewed new Teller integration;
- require a separate Underscore brief, owner, tests, and deployment gate if
  the existing Base multi-leg flow is to use the context; and
- release the maximum and context as one final reviewed artifact set rather
  than deploy a maximum-only intermediate version.

There is a material residual risk even under that design: the existing
four-argument function accepts any valid Ripe address and qualifying
Underscore earn vault or lego. A malicious eligible caller can make a minimal
successful deleverage for a victim and write the victim's cooldown checkpoint.
S4 is not authorized to change the underlying trusted-caller policy. Keeping
the governed cooldown at `0` avoids activating that denial-of-withdrawal
surface. Any later nonzero activation must explicitly accept or separately
remediate this risk.

## 1. Frozen launch and evidence record

### 1.1 Repository and integration prerequisites

| Item | Frozen result |
| --- | --- |
| Repository | `/Users/wigglez/dev/ripe-protocol` |
| Integration branch | `rh` |
| Local `rh` at bootstrap | `3e6e6f230169fc445d0b29454457480c62efd89a` |
| `origin/rh` and live `ls-remote` result | `3e6e6f230169fc445d0b29454457480c62efd89a` |
| Integration status at bootstrap | Clean, `rh...origin/rh`, zero local divergence |
| S4 branch/worktree before bootstrap | Both absent |
| S4 branch/worktree after bootstrap | Created from the exact local `rh` commit above |
| Local bootstrap time | 24 July 2026 12:12:46 MDT (`-0600`) |
| UTC bootstrap time | 24 July 2026 18:12:46 UTC |
| S4 worktree evidence-freeze recheck | 24 July 2026 12:36:45 MDT / 18:36:45 UTC |
| S4 worktree state before this record | Clean; only the branch header in `git status` |

Ancestry and approval evidence:

| Slice | Integrated/review evidence |
| --- | --- |
| S1 clock harness | reviewed head `868e46ee03a934245df36752a96d41a7333c0091`; integrated by `f03e128905de395b7162110cab42582866e7ccc4` |
| S2 checked inventory | reviewed head `f0e556ce20bd21622752d441b358d23cb2b17ec2`; integrated by `454fbeb8e1bc1401fe1db0c44b98e9c487f3c504` |
| S3 gate 1 | `db7ae895d1b32ae6708f2405274c32c1e3f5222e` |
| S3 inventory | `51e5c5a47ac74083affb16516cd07dd8321c0fbb` |
| S3 gate 2 | evidence clarification `c823300c7af418a7b226093e3a9ddf1d970e1998`; approval tip `6f4264528bf54554020d3b44a6bb232619879ea2` |
| S3 integration / S4 launch | `3e6e6f230169fc445d0b29454457480c62efd89a` |

All active worktrees were checked before bootstrap. No active branch owned the
Stage A file or the proposed Stage B files. The in-flight H-01 branch was
rechecked during original evidence collection at
`cc0fd9977b854756114e2c3fda2185f2a81f0ce2`. During this re-review it had
advanced to clean tip `22eb097e86a123c01a7117d5166b87ed11ae30c9`,
`docs(rh): complete H-01 rereview evidence`. Its entire committed delta from
the S4 launch baseline remains only
`docs/chains/rh/evidence/dependency-security-gate.md`. Neither the earlier nor
current H-01 tip is an ancestor of `rh`, so neither is an integrated dependency
baseline. These observations are not an H-01 review or approval.

After S4 bootstrap, another local worktree advanced only the local `rh` ref to
`27765d29094256fa9619dd44a0bfd145863de8b7` at 12:35:41 MDT with
`docs: record owner-approved Track 6 S5 plan`. That commit adds only
`docs/chains/rh/track-6-s5-ledger-guard.md`; it does not overlap this Stage A
file or the proposed Stage B set. The live remote `rh` remained at the required
launch commit. This S4 branch deliberately retains the exact authorized parent
`3e6e6f230169fc445d0b29454457480c62efd89a`; no reconciliation with the
post-bootstrap local-only S5 documentation commit was performed.

#### Post-launch integration-worktree hygiene and candidate directive

The integration worktree was rechecked read-only during this independent
re-review. Local `rh` remains at
`27765d29094256fa9619dd44a0bfd145863de8b7`, one local documentation commit
ahead of `origin/rh`, but the worktree now also has nine modified tracked
documents totaling 394 insertions and 136 deletions:

- `docs/chains/rh-summary.md`;
- `docs/chains/rh/block-clock-validation-plan.md`;
- `docs/chains/rh/block-number-inventory.md`;
- `docs/chains/rh/component-matrix.md`;
- `docs/chains/rh/robinhood-deployment-support-specification.md`;
- `docs/chains/rh/robinhood-deployment-validation-plan.md`;
- `docs/chains/rh/shared-block-clock-specification.md`;
- `docs/chains/rh/track-6-s4-deleverage-cooldown.md`; and
- `docs/chains/rh/track-6-s5-ledger-guard.md`.

It also has one untracked 373-line file,
`docs/chains/rh/minimal-contract-change-reassessment.md`, with SHA-256
`57c94b7f6b4e7a9609803567c0dd90442210f8aa88cbc9c2b06629fe222a769c`.
The floating S4 edits appear to add a minimum-change amendment, Phase A0, and
decision 0, while other files alter previously checked clock-plan statements.
There is no commit or other Git provenance tying those working-copy edits to
owner authorization.

Those post-launch edits are therefore **candidate input, not S4 authority**.
The owner's Stage A authorization named the committed launch brief as the
complete contract, and this correction does not copy, modify, stage, discard,
or otherwise normalize the integration-worktree material. Before the material
can alter this decision record, the owner must choose one of two provenance
paths:

1. if authorized, preserve and land it through an explicitly reviewed commit,
   repair any checked-item and baseline audit trail it changes, and direct
   whether S4 must adopt its Phase A0/decision-0 contract; or
2. if unauthorized or abandoned, preserve a reviewable patch or quarantine as
   directed and restore the integration worktree only under explicit owner
   authority.

Until that provenance decision is recorded, checkpoint 0 is not final and
Stage B remains blocked. The present recommendation—unchanged shared source,
stored cooldown `0`, and no initial nonzero activation—is compatible with a
minimum-change outcome, but the floating text cannot silently become the
controlling decision.

### 1.2 Frozen hashes

All hashes are SHA-256 unless identified as a compiler integrity hash.

| Input | Hash |
| --- | --- |
| S4 task contract | `0e612120c587e5ba89f964f20bc12de0574a42b410ef60c46ed4ef22463fb882` |
| Shared block-clock specification | `ad0ee08e40bdc7c1e9233dbdc33f70b5a479a2c8e59e75b5bc2350730b121c68` |
| Block-clock validation plan | `e3f5d73fa9588aba28ac8823b74c5d523d1e0e6451d29d47f352a87fe03371f2` |
| `contracts/core/Deleverage.vy` | `eb28c2d22a695c3148acfc00b54507d3b2f3e4462aeae119ba4183d09832815b` |
| `contracts/config/SwitchboardDelta.vy` | `2c76e1a2b985884adc2db1b419776eddf7bd6c355268dc527d573453421bfbe1` |
| `contracts/core/Teller.vy` | `51cf13e3c9d58262ba446a462332d8f4f181c07ce689031b2398c20137f04198` |
| `contracts/core/TellerUtils.vy` | `c6351363db4f77318584dfc60b868f847ec894221ada37007b118881e254ecfe` |
| `contracts/modules/Addys.vy` | `2a46a2fbb26fed9ed5d59414833fb6c2f85a7ddf72e82ffc2d6e122296e1d4e6` |
| Deleverage ABI | `0ba82a99c130e01149052add397299aeb6a40dcf1b65de98fa168feaf82553d3` |
| SwitchboardDelta ABI | `461275efff3493e0787f63b6b9756e3557801093df25b7ed1df5f04098421147` |
| Teller ABI | `e5b696f0e22c2196806cd84f27a037d21ca567d702a357f3a61a574fd514e1f4` |
| Checked clock inventory | `cebc434d4e2628afd404ff3c76874e26d6e947783dd75ec74dd10001458df6fb` |
| Narrative block-number inventory | `3f111accff58e51b91986f134df6d15ed7401d692ef0cca28b2cafb1c89ad2d4` |
| S2 checked-inventory brief | `3da15c1c5f5e98e28ee27786e5ab4093911cb83081feb3d797c04f4e7f0cb693` |
| Inventory checker | `cc86f73629589c6a2ee0c9b60e480761d88e1e033e452c1f0843c18db9e28642` |
| Inventory tests | `d9007158565979f7e5027a012a0cf6efdc6be354f0a96b16b7d35c87ba58a39c` |
| S1 clock tests | `2b1bbd8c77f97e614c9db54fcb98b284d3db95a6bb47d1ee9ab020bf6d725cc4` |
| Dependency lock (`requirements.txt`) | `18df0aad224f2a10febc9e155e4a530e1000ec553916c8ef78dc9859c6c92ba0` |
| Current Base manifest | `06ac6dcf3d5c3d2366bd33118023fd6603fc4d759a7a5103901b29ae67007b00` |

Vyper compiler-input integrity:

| Contract | `vyper -f integrity` |
| --- | --- |
| Deleverage | `0d18f99eb6c0d8ec7c314a81e6c1ba65d8dee45dc14493e0b6459795eeac0dfd` |
| SwitchboardDelta | `ee5bb5bc2eaa9cbd1247c17248f1f2b7237faba7353d2520deddcf722dd4e40a` |
| Teller | `ae5ab1888fa6a7136fb113d6969acbb145b78468307f0f0c6118c3f9ff3ce12f` |

The integrity hashes include the compiler's resolved input graph and therefore
complement, rather than replace, the direct source hashes. They must be
regenerated after H-01 integration.

### 1.3 Toolchain

| Tool | Version |
| --- | --- |
| Python | `3.12.0` |
| Vyper CLI | `0.4.3+commit.bff19ea2` |
| Vyper package | `0.4.3` |
| Titanoboa | `0.2.7` |
| pytest | `8.4.2` |

The first sandboxed test attempt could read Titanoboa's cache but could not
create cache entries under `~/.cache/titanoboa`. That produced two
`PermissionError` results in the withdrawal file and one collection
`PermissionError` in the Delta file. The same exact repository commands were
rerun with cache write access and passed. These were environment permission
errors, not repository failures. The test environment used the non-secret
placeholder `ETHERSCAN_API_KEY=local-placeholder`; no RPC or live-chain action
was performed.

Specifically, the first withdrawal attempt ended with 67 passed and two cache
permission errors, and the first Delta attempt stopped at collection with one
cache permission error. The authoritative reruns are in the table below.

### 1.4 Constructors and deployment call sites

Current constructors:

```text
Deleverage(_ripeHq: address)
SwitchboardDelta(
    _ripeHq: address,
    _tempGov: address,
    _minConfigTimeLock: uint256,
    _maxConfigTimeLock: uint256,
)
Teller(_ripeHq: address, _shouldPause: bool)
```

Committed Base migration deployment call sites:

| Contract | Every matching `migration.deploy` call site |
| --- | --- |
| Deleverage | `2025111100_NewDepts.py:45`; `2025112500_New_Endaoment_Features.py:50`; `2026021900_DeleverageOptimizations.py:9`; `2026022000_DeleverageFix.py:7` |
| SwitchboardDelta | `1006_Switchboard.py:51`; `2025071502_Switchboard.py:66`; `2025071601_Switchboards.py:44`; `2025071801_LootBoxPointsRefresh.py:62`; `2025072001_SwitchboardDelta.py:11`; `2025072201_BondRoom.py:19`; `2025072901_SwitchboardsAndAssetsConfig.py:149`; `2025081200_New_Endaoment_BondBooster.py:64`; `2025111100_NewDepts.py:23`; `2025120200_New_Switchboards.py:43`; `2026021900_DeleverageOptimizations.py:14`; `2026043000_RedeploySBDelta.py:11` |
| Teller | `1017_Teller.py:10`; `2025071506_Teller.py:10`; `2025072301_UpdatesForUnderscore.py:143`; `2025080401_TellerUnderscoreWallet.py:11`; `2025081800_NewTeller_CreditEngine.py:7`; `2025111100_NewDepts.py:49` |

Historical migrations are immutable and must not be edited. A future
owner-approved migration would supply the new Deleverage immutable. Test
deployment call sites are centralized at `tests/conf_core.py:295` for
Deleverage, `:435` for Teller, and `:572` for SwitchboardDelta, plus the direct
fresh-Deleverage loader at `tests/core/deleverage/conftest.py:82`.

The SwitchboardDelta call sites prove deployments, not the current Switchboard
registry mapping. `1006_Switchboard.py` registered the Delta deployed in that
historical migration at ID 4. The Delta currently named in the committed
manifest was instead deployed by `2026043000_RedeploySBDelta.py`, which deploys
the contract and relinquishes temporary governance but contains no committed
Switchboard address-update or confirmation for ID 4. Manifest bookkeeping in
`scripts/utils/migration.py` does not update the onchain registry. Therefore
the current manifest address must not be called the current ID 4 contract
without a fresh registry read and version/pending-update proof.

### 1.5 Direct clock and cadence counts

The checked inventory reports:

```text
production_occurrences=100
production_lines=95
production_files=17
bn_ids=32
bn_records=100
indirect_ids=1
cadence_candidates=455
seconds_unit_candidates=58
timestamp_ids=11
timestamp_occurrences=37
mixed_clock_functions=4
vyper_paths=92
```

Within the S4 production trio, direct `block.number` occurrences are:

- Deleverage: 3 occurrences on 2 source lines, all in BN-012—two reads on one
  guard line and one checkpoint write;
- SwitchboardDelta: 1 occurrence on 1 source line, in the unrelated bond
  epoch-start helper; and
- Teller: 0.

The trio therefore has 4 direct occurrences on 3 source lines.

The S4 cooldown maximum occurs twice, once in Deleverage and once in
SwitchboardDelta. Both values are `7_200`.

### 1.6 Baseline validation

All authoritative reruns used the untouched post-S3 launch commit.
Each pytest or Python command used the exact prefix
`ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=.`.

| Command | Result | pytest/runtime |
| --- | --- | --- |
| `pytest -q tests/core/deleverage/test_deleverage_for_withdrawal.py` | 69 passed | 51.14s / 91.76s wall |
| `pytest -q tests/core/deleverage/test_deleverage_permissions.py` | 36 passed | 34.77s / 73.79s wall |
| `pytest -q tests/config/test_switchboard_delta.py` | 109 passed | 31.10s / 71.26s wall |
| `pytest -q tests/core/teller/test_teller_withdraw.py` | 32 passed | 33.77s / 71.91s wall |
| `pytest -q tests/core/teller/test_teller_rebalance.py` | 22 passed | 30.15s / 67.29s wall |
| `pytest -q tests/clock/test_clock_profiles.py` | 57 passed | 28.16s / 68.13s wall |
| `python scripts/check_block_clock_inventory.py --check` | `CLOCK_INVENTORY_OK`; counts above | 1.49s wall |
| `pytest -q tests/inventory/test_block_clock_inventory.py` | 60 passed | 26.82s / 29.15s wall |
| `pytest --collect-only -q` | 2,864 discovered; 2,722 selected; 142 deselected | 5.15s / 6.51s wall |
| `pytest -q` | 2,722 passed; 142 deselected | 300.19s / 361.27s wall |

`git diff --check` reported no diagnostics. Because this document was
untracked at validation time, `git diff --no-index --check /dev/null
docs/chains/rh/deleverage-cooldown-security-decision.md` was also run: it
reported no whitespace diagnostics and returned the expected `1` status for a
new-file difference.

## 2. Code facts, dated live evidence, test behavior, and assumptions

### 2.1 Code facts

- Fresh Deleverage storage sets `minDeleverageBps`,
  `deleverageBuffer`, and `deleverageCooldown` to `0` by default and explicitly
  sets `underscoreSafeSpreadBps` to `100`.
- `lastDeleverageBlock[user] == 0` is the unset sentinel.
- Successful `deleverageForWithdrawal` writes current `block.number`.
- With nonzero cooldown and initialized checkpoint, the current guard blocks
  only when:

  ```text
  block.number > lastBlock
  and block.number < lastBlock + cooldown
  ```

- A separate transaction at the same number is therefore allowed.
- Equality at `lastBlock + cooldown` is eligible.
- A position projected at or below the redemption threshold may bypass both
  cooldown and minimum-deleverage filtering.
- Permission is not Teller-only. The caller may be any current valid Ripe
  address or an address recognized as an Underscore earn vault or valid
  Underscore lego.
- `_vaultId = 0` resolves through
  `MissionControl.getFirstVaultIdForAsset(_asset)`.
- `didHandleVaultId[user][vaultId]` and
  `didHandleAsset[user][vaultId][asset]` are transaction-transient. They
  suppress reuse of liquidation collateral processing within the top-level
  transaction independently of the cooldown.
- SwitchboardDelta validates `<= 7_200` when an action is queued. At execution
  it resolves current Deleverage from RipeHq ID 18 and calls its setter, which
  independently validates `<= 7_200`.
- `migrations/base-mainnet/1006_Switchboard.py` historically registered the
  Delta deployed by that migration as Switchboard ID 4. The current manifest
  Delta was deployed by `2026043000_RedeploySBDelta.py`, which has no committed
  current-registry update. The current Delta's Switchboard ID is therefore
  ambiguous until rollout preflight proves it. Deleverage and Teller remain
  source-defined RipeHq IDs 18 and 17 respectively in
  `contracts/modules/Addys.vy`.
- A fixed-string search of current Ripe production contracts finds only the
  Deleverage function definition. Teller, TellerUtils, and every other Ripe
  production contract contain no call to `deleverageForWithdrawal`.

### 2.2 Dated live evidence

The integrated Track 6 specification records read-only Base evidence from
23 July 2026 at endpoint height `49,026,989`:

| Component | Manifest address | Runtime bytes | Runtime Keccak-256 |
| --- | --- | ---: | --- |
| Deleverage | `0x62591b3058c1428FA4b5eD2160387725be285a64` | 24,135 | `0x40fb3758b1d04308fcea0752e04d8aefa39843c483a4f26ef9821e41a530f5cc` |
| SwitchboardDelta | `0xCdD15077231FEbe9e6393cf91d500984973FFcA0` | 21,712 | `0xdbb9504af5719965870d9911d101a975ed2539af19be6ade49b1aa75c6cfca5f` |

The current committed manifest additionally maps Teller to
`0xae87deB25Bc5030991Aa5E27Cbab38f37a112C13` and RipeHq to
`0x6162df1b329E157479F8f1407E888260E0EC3d2b`.

This runtime and manifest evidence proves code at the named Delta address; it
does not prove which Switchboard registry ID currently resolves to that
address.

The same dated read observed Base `deleverageCooldown == 0`. This is not a
permanent onchain fact. No fresh RPC read was performed for Stage A. The other
current governed values, pause/governance state, registry timelocks, and
pending Delta actions remain rollout-time live inputs.

### 2.3 Existing test behavior and gaps

Current tests prove:

- fresh cooldown and buffer are zero;
- only a registered switchboard may set the Deleverage value;
- Deleverage and Delta accept `7_200` and reject `7_201`;
- a later `+1` call inside cooldown returns false;
- zero cooldown permits another call, subject to existing transient handling;
- qualifying Underscore earn-vault callers are accepted; and
- direct test calls can use `teller.address` as the simulated sender.

They do not currently prove:

- two independent transactions at the same EVM number are blocked;
- exact-expiry execution succeeds rather than only observing state;
- a second near-redemption call actually executes;
- a bound context cannot be forged, copied, nested, replayed, or substituted;
- old/new ABI combinations;
- registry replacement between Delta queue and execution; or
- real Ripe-to-Underscore end-to-end multi-leg behavior.

The direct `teller.address` tests are caller simulations, not evidence that
Teller production source coordinates the flow.

### 2.4 Underscore committed input

The Underscore repository was inspected read-only at committed input
`5b0a6354caf102865ab173aaa0c6bab0b492030f`.

| Input | SHA-256 |
| --- | --- |
| `contracts/vaults/modules/LevgVaultWallet.vy` | `05870c3da72ba0b16fc9ccdf521b394d39fe4a47d1855ef331c3491d05b906d6` |
| `contracts/vaults/LevgVault.vy` | `0b09093fcfce8b9f77c586a024112b7eab1ffdafbfe8d24202c8c8fc1df74287` |
| `contracts/mock/MockRipe.vy` | `47fdfabd7297c945c05ad1a249b4fe9f750e57d4bd5eb5252146bfde0ffc16fd` |

Fixed-string production results:

```text
contracts/vaults/modules/LevgVaultWallet.vy:29   four-argument interface
contracts/vaults/modules/LevgVaultWallet.vy:706  call with (self, 0, asset, amount)
contracts/vaults/modules/LevgVaultWallet.vy:835  call with (self, ripeVaultId, vaultToken, amount)
```

`contracts/mock/MockRipe.vy:376` is a four-argument stub that always models the
old surface; it is not an end-to-end proof.

The Underscore worktree already contained two unrelated untracked HTML files
under `docs/wallets-v3/`. Stage A did not edit, stage, or otherwise touch them.

## 3. Real call and state-transition graph

### 3.1 Production call chain

For Base Underscore redemption:

```text
external user or delegated allowance caller
  -> LevgVault.withdraw / redeem / redeemWithMinAmountOut
  -> LevgVault._redeemFromVault
  -> LevgVaultWallet._prepareRedemption
     -> optional raw-underlying Ripe collateral leg
        -> Deleverage.deleverageForWithdrawal(self, 0, asset, amount)
        -> MissionControl.getFirstVaultIdForAsset(asset)
        -> LevgVaultWallet._removeCollateral
     -> optional collateral-vault-token Ripe leg
        -> _withdrawVaultTokenForRedemption
        -> Deleverage.deleverageForWithdrawal(
             self, collateralRipeVaultId, collateralVaultToken, amount
           )
        -> _removeCollateral
        -> yield-protocol withdrawal
     -> optional leverage-vault-token Ripe leg for USDC flows
        -> _withdrawVaultTokenForRedemption
        -> Deleverage.deleverageForWithdrawal(
             self, leverageRipeVaultId, leverageVaultToken, amount
           )
        -> _removeCollateral
        -> yield-protocol withdrawal
```

All legs occur inside one top-level EVM transaction. Deleverage sees
`msg.sender == LevgVault` and `_user == LevgVault`; it does not see the
external EOA or delegated spender. The first successful leg writes the
checkpoint and every later successful leg rewrites the same EVM number under
the current exception.

### 3.2 Flow matrix

| Flow | Caller/user and contracts crossed | Legs, checkpoint, transient/revert behavior | Chain and compatibility |
| --- | --- | --- | --- |
| Direct Teller-style test | Boa transaction with `sender=teller.address` directly to Deleverage; one Ripe user | Usually one leg; success writes checkpoint. This does not execute Teller source. | Test-only on Base fixture. Old four-argument and retained wrapper work. |
| `Teller.withdraw` | External caller -> Teller -> vault/ledger/housekeeping | No call to withdrawal Deleverage; no S4 checkpoint write. | Shared Ripe source; no Teller context dependency exists. |
| `Teller.withdrawMany` | External caller -> Teller -> multiple withdrawal actions for one declared user | No call to withdrawal Deleverage; no S4 checkpoint write. | Shared Ripe source; a Teller coordinator would be new behavior. |
| `Teller.rebalance` | External caller -> Teller rebalance path -> vault actions/housekeeping | No call to withdrawal Deleverage; no S4 checkpoint write. | Shared Ripe source; no current cooldown dependency. |
| Teller delegated withdrawal validation | External/delegated caller -> Teller withdraw path -> `TellerUtils.validateOnWithdrawal` view -> vault action | TellerUtils contains no call to withdrawal Deleverage; no S4 checkpoint write. | Shared Ripe source; delegation does not create a coordinator context. |
| Underscore raw underlying | User/delegate -> LevgVault -> wallet module -> Deleverage -> MissionControl ID resolution -> Ripe vault removal | One of several possible legs. `_vaultId=0` resolves first vault. Success writes checkpoint. Top-level revert unwinds checkpoint and transient flags. | Existing Base integration. Robinhood initial graph omits Underscore. Old caller works with old or retained wrapper; strict nonzero new cooldown can block later legs. |
| Underscore collateral vault token | Same top level -> helper -> Deleverage with exact Ripe vault ID and vault token -> removal -> yield withdrawal | May follow raw leg. Depends on current same-number exception when cooldown is nonzero. Distinct liquidation collateral may remain available; already handled collateral is suppressed by transient maps. | Existing Base integration; requires context-aware downstream version if nonzero cooldown is activated. |
| Underscore leverage vault token | Same top level, USDC-specific step 4b | May be a third Ripe collateral leg. Same checkpoint/context constraints. | Existing Base integration only in selected launch graph. |
| Two distinct withdrawal assets for one user | Plausible coordinator batch; no current Teller implementation | Multiple calls may share one transaction. Each success writes the same checkpoint number. Deleverage liquidation-asset transient state can reduce later repayment sources. | New context may permit only if exact coordinator and user binding are approved. |
| Same asset/vault repeated | Plausible duplicate or callback | Cooldown should block the no-context repeat. Even with context, `didHandleAsset`/`didHandleVaultId` may make the later deleverage return zero because the repayment collateral was already marked handled. | Must be tested; context must not override existing transient guards. |
| Two users in one top-level call | Plausible future coordinator batch; no current Underscore redemption does this | Separate `(coordinator,user)` contexts would be required. No ID may cross users. A revert unwinds only according to top-level transaction semantics. | Pending policy; default should not infer multi-user permission. |
| Delegated caller | EOA/spender uses LevgVault allowance -> same LevgVault flow | Deleverage sees the LevgVault as both caller and user, not the delegate. External delegation cannot be the context identity. | Existing Base path; binding must use the onchain coordinator and Deleverage user. |
| Valid Ripe Department | Registered Ripe address calls four-argument function directly | Current permission allows it; success writes victim/user checkpoint. No generic context authority should follow from registration. | Shared behavior on deployed chains; griefing residual if cooldown nonzero. |
| Valid Underscore address | Any recognized earn vault or valid lego calls directly | Current permission allows it; success writes checkpoint. Recognition is broader than one approved coordinator. | Base integration; not selected for initial Robinhood. Broad recognition must not open context. |
| Arbitrary contract or EOA | Direct call | Permission assertion reverts; all state unwinds. | Preserve rejection on both chains. |
| Registry replacement during pending Delta action | Governance queues in current Delta -> RipeHq ID 18 changes -> execute resolves new Deleverage | Current queue uses Delta's duplicate ceiling; execution targets whatever ID 18 resolves then. New Deleverage must revalidate its own immutable maximum. A revert leaves the action unexecuted under current timelock behavior. | Base convergence risk and future Robinhood governance behavior; enumerate/cancel/expire pending actions before replacement. |

Compatibility overlay for every flow:

- option 1 leaves all current selectors intact but can block later legitimate
  Underscore legs whenever cooldown is nonzero;
- option 2 changes only flows whose exact coordinator is approved and upgraded;
  every other flow remains strict no-context;
- option 3 would make those same flows depend on downstream self-reported
  transient state and is not recommended;
- option 4 preserves every old four-argument call while routing only the
  upgraded approved flow through option 2; and
- option 5 requires the Ripe and Underscore versions in the production chain
  above to move under the mixed-version order in section 7. Teller, TellerUtils,
  arbitrary Ripe callers, and arbitrary Underscore callers receive no context
  unless separately named and approved.

External calls inside the Deleverage execution reach CreditEngine, Mission
Control, PriceDesk, VaultBook/Registry, vaults, AuctionHouse, token/vault
implementations, Endaoment/PSM-related assets, and repayment logic. Context
authorization must be established before these calls and remain bound through
callbacks. It must not rely on a callback-visible block number or `msg.sender`
alone.

## 4. Threat model and residual risk

“Owner” below means the role that must accept the residual risk in addition to
independent security review.

| Threat | Asset/invariant and required authority | Current behavior | Recommended behavior | Residual risk, proof, rollout, owner |
| --- | --- | --- | --- | --- |
| Independent transactions share one `NUMBER` | Cooldown pacing; any eligible caller | Every transaction at `lastBlock` bypasses because `current > last` is false. | Strictly block whenever `current < last + cooldown`, including equality with `last`; only a live bound context may continue. | Prove with two independently committed Boa transactions at identical number; no artifact release until green. Security/protocol owner. |
| Sequencer bundle or batch | Same; any eligible caller able to submit many transactions | All bundled transactions at one number may pass. | Same strict rule; transient context cannot cross transaction boundaries. | Batch several committed calls under one number; block activation until all but the first fail. Security owner. |
| Repeated calls in one transaction | Pacing and legitimate multi-leg availability; eligible caller | Same-number exception allows all; transient collateral guards may suppress repayment sources. | No-context repeat blocked; approved context continuation allowed without disabling existing transient guards. | Prove the exact downstream flow and duplicate asset/vault cases before coordinator rollout. Security and downstream owner. |
| Malicious registered Ripe caller | Victim withdrawal availability; valid Ripe address | Can call for a victim and, if repayment succeeds, write victim checkpoint. | Registration alone never grants context. Preserve current first-call permission under S4. | Adversarial caller test; keep activation at `0` or separately approve trusted-caller remediation. Protocol/security owner. |
| Malicious registered Underscore caller | Same; recognized earn vault or lego | Broad current permission can write victim checkpoint. | Only exact approved coordinator may open/use context; broad caller retains only strict no-context path. | Test non-coordinator earn vault and lego; do not register context authority until exact source/address review. Ripe, Underscore, and security owners. |
| Minimal successful cooldown grief | Availability; any current eligible caller with a repayable victim | Small successful call writes checkpoint, delaying a later withdrawal. | Context does not waive or broaden first-call permission. Initial cooldown remains `0`. | Prove a minimal grief case; any nonzero activation is blocked on explicit acceptance or separate mitigation. Protocol/security owner and S6. |
| Forged, guessed, copied, or zero context ID | Cooldown integrity; caller with observed or guessed ID | No context exists. | Deleverage issues a nonzero opaque `bytes32`; active transient record binds exact coordinator and user; zero and unknown IDs reject. | Unit/fuzz every ID class; do not ship context selectors before proof. Security owner. |
| Cross-user substitution | One user's pacing; approved coordinator | No context exists. | ID record includes user; argument must match; active user lock rejects mismatch. | Test both directions and do not enable multi-user scope without separate approval. Security owner. |
| Cross-coordinator substitution | Coordinator authority; approved or malicious other caller | Broad caller permission applies to no-context path. | ID record includes opening coordinator; `msg.sender` must match on every leg and close. | Mock coordinator/registry replacement and wrong-caller callbacks before coordinator registration. Security owner. |
| Reuse after close or later transaction | Transaction-only exception | Current same-number exception is reusable across transactions. | Explicit close deletes transient authority; transaction end clears it; stale ID rejects. | Test same-tx post-close and later-tx reuse at the same number; block release on either success. Security owner. |
| Nested context opening | Scope uniqueness; approved coordinator or reentrant callback | No context exists. | Reject a second active context for the same `(coordinator,user)`; policy for separate users remains explicit. | Test direct and callback nesting; default multi-user/nested rollout off. Security owner. |
| Token/vault/PriceDesk/CreditEngine/PSM/Teller callbacks | Context integrity and user assets; callback-capable dependency | Current broad permission and same-number bypass may be reentered from eligible callback actors. | Open context locks the user to its exact coordinator; no-context calls for that user reject while open; only context-aware calls by bound coordinator proceed. | Adversarial callback suite plus exact coordinator reentrancy review before registration. Security owner. |
| Failed middle leg then recovery | Atomicity and liveness; normal coordinator/dependency failure | Uncaught Vyper external-call failure reverts checkpoint and transient flags. | Preserve atomic revert. If a future coordinator catches a failure, require explicit close and forbid continuation unless separately designed and tested. | Prove full unwind; no catch-and-continue rollout without a separately approved retry matrix. Downstream/security owner. |
| Near-redemption manufactured between legs | Solvency exception and legitimate multi-leg availability; caller able to alter collateral/debt during callbacks | Each call may bypass cooldown when projected withdrawal leaves position near redemption. | Preserve near-redemption as a per-call independent safety bypass; it must not silently create, authenticate, or extend a context. Denying context open during an active cooldown protects that boundary but may defer a legitimate multi-leg redemption until expiry. | Test callback state changes, threshold recomputation, and the selected deny-open/qualified-bootstrap/no-active-release policy; block activation if context broadens the bypass or the liveness cost is unapproved. Risk/security owner. |
| Cooldown `0 -> nonzero` | User availability; governance | Existing checkpoint immediately becomes relevant under new value; same-number bypass still exists. | Maximum/context artifact may deploy with stored `0`; activation is separate. On activation, document all existing-checkpoint jump behavior. | Transition tests and a fresh checkpoint report are an S6/later activation gate. S6/protocol owner. |
| Cooldown `nonzero -> 0 -> nonzero` | Same | Zero disables checks but does not clear mapping; later nonzero can reactivate old checkpoints if still in range. | Preserve storage semantics and test transitions explicitly. | Test reactivation and require governance runbook language before nonzero rollout. Protocol owner. |
| Maximum reduction/increase during window | Availability and governance bound; Delta governance | Delta validates its own fixed cap at queue; stored cooldown can change immediately on execution. | Delta queries current target at queue; target validates at execution. Immutable maximum itself changes only by deployment. | Test lower/higher target replacements and enumerate/drain pending actions before registry change. Deployment/protocol owner. |
| Registry replacement between queue/execution | Correct target/maximum; registry governance | Delta resolves current ID 18 only at execution. | Retain execution-time target validation and add tests with a lower-max replacement. | Prove lower-max execution revert and record zero pending actions before rollout. Deployment/security owner. |
| Arithmetic at unset/exact expiry/max | Liveness; no special attacker | `last + cooldown` uses checked arithmetic; unset skips; exact expiry passes. | Reject constructor maximum `0` and `max_value(uint256)`; prove approved maxima cannot overflow realistic EVM numbers; preserve exact equality eligibility. | Boundary/fuzz proof plus approved constructor maximum before artifact release. Security owner. |
| Base upgrade resets unenumerable checkpoints | Cooldown continuity; deployment authority | New contract starts with empty mapping; committed artifacts cannot enumerate users. | With cooldown `0`, record reset but do not claim continuity. If live value is nonzero, pause old calls, wait at least the live cooldown from the last possible old call, then replace, or obtain separate risk approval. | Fresh live read plus pause/wait/expiry evidence gates ID 18 replacement; rollback must account for stale old mapping. Deployment/protocol owner. |

## 5. Context architecture comparison

| Option | Same-number protection and authorization | Binding, lifetime, nesting/replay | Compatibility and change surface | Test/rollback result | Disposition |
| --- | --- | --- | --- | --- | --- |
| 1. No exception | Strongest: every later call obeys cooldown; no coordinator authority | No context risk | Four-argument ABI unchanged; no Teller/Underscore code change, but legitimate nonzero-cooldown Underscore multi-leg flows may fail | Easy to test and roll back; unsafe for known downstream availability unless owner chooses no coordinator/nonzero activation | Viable only if owner accepts no multi-leg exception or keeps cooldown `0`; not recommended for intended Base behavior |
| 2. Deleverage-managed explicit context | Strict default plus exception only for exact approved coordinator | Deleverage-issued ID bound to caller/user in transient storage; reject zero, mismatch, nesting, reuse | Deleverage ABI/runtime changes; exact coordinator must open/pass/close; old wrapper can remain | Central state is directly testable; rollback requires mixed-version plan | Recommended security primitive, subject to exact coordinator and independent review |
| 3. Coordinator-managed transient scope | Deleverage must trust or query coordinator-reported state | Coordinator owns scope; a malicious or replaceable coordinator can self-attest unless Deleverage independently binds it | Larger downstream-specific interface; Ripe security depends on external transient implementation | Harder cross-contract proof and rollback; coordinator replacement is high risk | Not recommended without a stronger independently verifiable flow proof |
| 4. Four-argument wrapper plus new context entry | Strict old path; approved context path uses option 2 controls | Same as option 2 | Preserves old selector; adds new selector/open/close/getter/events. Teller unchanged unless separately selected. Underscore needs a new version to consume it. | Best old-caller compatibility; old callers cannot obtain exception | Recommended ABI envelope combined with option 2 |
| 5. Coordinated Ripe/Underscore ABI replacement | Can implement exact downstream flow | Binding can be strong but both repositories and deployments must move in safe order | Broadest cross-repo surface; old/new mismatches can revert | Requires separate Underscore brief, full end-to-end tests, deployment owner, rollback, and live gate | Required rollout work if Underscore is selected, but prohibited as an S4 edit and not a substitute for option 2/4 |

All options are testable under the S1 number controller, but with different
proof surfaces. Option 1 needs only strict-boundary Ripe fixtures. Options 2
and 4 add transient lifetime, callback, and mixed-ABI fixtures. Option 3 also
needs an adversarial external coordinator implementation. Option 5 needs the
same Ripe fixtures plus a real cross-repository end-to-end suite. For the
context surface, options 2-5 change Deleverage bytecode and external ABI;
option 4 uniquely preserves the old selector as an explicit compatibility
envelope. Options 3 and 5 also change downstream bytecode. The independent
authoritative-maximum work changes Deleverage and Delta under every S4
implementation option. Any shared-source change requires the Base convergence
and rollback record in section 8.

### 5.1 Recommended provisional context contract

The exact names remain checkpoint decisions. The recommended semantics are:

1. keep
   `deleverageForWithdrawal(user, vaultId, asset, amount)` as a strict
   no-context function;
2. add a separately named context-aware function rather than an ambiguous
   default argument;
3. let only an exact approved coordinator call an open function;
4. issue a nonzero opaque `bytes32` from Deleverage and store, transiently,
   the context's coordinator, user, active state, opening checkpoint, and
   successful-leg state;
5. reject opening when that user already has an active nonzero cooldown;
   near-redemption remains available per call but does not authenticate
   context opening;
6. reject another context for the same coordinator/user and default to no
   multiple-user context support unless a real approved flow requires it;
7. while a context is active, reject no-context calls for that user so a
   callback cannot interfere;
8. apply normal cooldown rules to the first context leg; after its successful
   checkpoint write, allow only bound follow-up legs in that same context;
9. preserve `didHandleAsset` and `didHandleVaultId` behavior;
10. require exact coordinator/user/ID match for every leg and close;
11. invalidate on explicit close and rely on transient clearing at transaction
    end as a backstop; and
12. emit auditable open/close/use events only if the security reviewer approves
    their data and gas surface.

An identifier is a handle, not a capability secret. The exact coordinator
gate and stored bindings are the authorization.

Suggested interface names for checkpoint discussion:

```text
openDeleverageWithdrawalContext(user) -> bytes32
deleverageForWithdrawalWithContext(user, vaultId, asset, amount, contextId) -> bool
closeDeleverageWithdrawalContext(user, contextId)
```

The owner and reviewer may select different names, but they must approve the
exact selectors and semantics before Stage B.

#### Availability trade-off requiring decisions 5 and 6

Rule 5 deliberately prevents a near-redemption result from becoming reusable
context-opening authority, but it has a material liveness cost. If a user
already has an active cooldown, a legitimate multi-leg redemption cannot open
the context. Even if the first leg independently qualifies for the
near-redemption bypass, later legs that do not independently qualify remain
blocked, so the complete withdrawal may have to wait until cooldown expiry.
This is a protocol availability decision, not an implementation detail.

Checkpoint 0 must select and independently approve exactly one of:

1. **deny active-window opening:** keep rule 5 and explicitly accept that a
   legitimate multi-leg redemption may be unavailable until expiry;
2. **qualified bootstrap:** allow opening only from a first leg that
   independently satisfies the near-redemption condition, then specify the
   exact continuation scope and prove that the condition cannot be
   manufactured, cached, or broadened for later legs; or
3. **no active context release:** keep governed cooldown `0` and ship no
   active nonzero-cooldown context behavior in the initial release.

The provisional recommendation remains option 1 only if checkpoint 0 accepts
its liveness loss. Option 3 is the safer initial-release fallback. Option 2 is
not recommended without a substantially stronger, flow-specific proof. No
option is selected by this Stage A record.

### 5.2 Explicitly rejected designs

- retaining the current `block.number > lastBlock` exception;
- `tx.origin`;
- `msg.sender` alone as proof of one top-level flow;
- a persistent or cross-transaction bypass nonce;
- an unbound boolean;
- caller-supplied ID treated as authority;
- a context open to every valid Ripe or Underscore address;
- implicit or unreviewed context creation from the near-redemption result;
- a context that survives the top-level transaction;
- duplicate maximum constants;
- `chain.id` branching or a Robinhood-only contract; and
- claiming Teller integration where none exists.

## 6. Maximum and activation comparison

| Policy | Base immutable maximum | Robinhood immutable maximum | Security/availability effect | Disposition |
| --- | ---: | ---: | --- | --- |
| Preserve enforced Base ceiling | `7_200` | `1_200` candidate | Approximately four hours under the planning cadence. Preserves current maximum governance authority while making RH wall-time comparable. | Recommended, but S4-specific owner/security cadence approval remains pending |
| Preserve stale source-comment intent | `43_200` | `7_200` candidate | Approximately one day. Expands Base governance authority by 6x and can delay legitimate withdrawal longer. | Not recommended without explicit evidence that one day, not current enforced ceiling, is intended |
| Another owner-supplied duration | owner value | derived only after cadence approval | Unknown until exact wall-time, chain cadence, and availability analysis exist. | Blocked pending exact values and proof |

These are distinct controls:

| Control | Recommended posture |
| --- | --- |
| Immutable maximum | One per Deleverage deployment; nonzero; not `max_value(uint256)` |
| Initial stored cooldown | `0` on Base replacement and Robinhood initial deployment |
| Later governed cooldown | Remains mutable through Delta/Deleverage within the immutable maximum |
| Activation approval | Not part of S4; S6 or a later named governance release |
| Parameter-manifest ownership | S6 |

Security benefit grows with a nonzero window because repeated successful
withdrawal deleverages are paced. Availability cost and governance authority
also grow with it. The stale “~1 day at 12s/block” comment is not evidence that
Base governance should gain a sixfold larger cap, and the dated Base value was
`0`.

A governed value applies immediately to the existing checkpoint mapping:

- lowering it can make a user eligible earlier;
- raising it can extend or reactivate a still-relevant old checkpoint;
- setting `0` disables checks without clearing checkpoints; and
- restoring nonzero may make old checkpoints relevant again.

S4 should preserve these semantics and test them; it must not silently clear,
saturate, or reinterpret checkpoints.

## 7. ABI and mixed-version matrix

| Caller/coordinator | Old Deleverage | New Deleverage under recommendation |
| --- | --- | --- |
| Old four-argument caller | Current behavior, including unsafe same-number exception | Selector retained. First eligible call works; later no-context call obeys strict cooldown. Multi-leg compatibility is guaranteed only while cooldown is `0` or no checkpoint is active. |
| New context-aware caller | New selectors absent and revert. A fallback to old selector loses context safety. | Open/new-call/close work only for exact approved coordinator and bound user. |
| Arbitrary valid Ripe caller | Four-argument path allowed; same-number exception applies | Four-argument path remains allowed for compatibility, but has no context and strict cooldown applies. |
| Arbitrary valid Underscore caller | Four-argument path allowed; same-number exception applies | Four-argument path remains allowed, but broad Underscore validity does not grant context. |
| Arbitrary contract/EOA | Rejected | Rejected on both entry points |

ABI consequences:

- Deleverage constructor gains an immutable maximum argument, recommended
  position `(_ripeHq, _maxDeleverageCooldown)`;
- Deleverage gains the maximum getter and, if approved, context functions and
  events;
- the old four-argument function remains in `scripts/abis/Deleverage.json`;
- SwitchboardDelta's external ABI need not change merely because its internal
  Deleverage interface and queue-time logic change; regenerate and compare,
  but do not commit a byte-identical generated file;
- Teller's ABI and source do not change under the recommendation; and
- no new caller may be deployed before the Deleverage version that supports
  its selectors.

Safe mixed-version posture:

1. hold the live governed cooldown at `0`;
2. deploy/review new Deleverage while old callers still use the retained
   four-argument selector;
3. deploy the separately approved downstream coordinator version only after
   new Deleverage is registered and verified;
4. prove open/use/close against the registered addresses;
5. replace Delta under its own registry/timelock plan;
6. keep cooldown `0` until all old multi-leg callers are retired or proven
   safe; and
7. activate a nonzero value only through the separately approved release.

Old four-argument Underscore callers plus new Deleverage are not safe under an
active nonzero cooldown if their redemption needs multiple successful legs.
New context-aware callers plus old Deleverage revert. There is therefore no
safe order that activates nonzero cooldown during the mixed-version window.

## 8. Base state and convergence

### 8.1 State that must be preserved or explicitly accepted

At rollout preflight, re-read and record:

- Deleverage RipeHq ID 18 address, code, ABI, pause and governance state;
- Teller RipeHq ID 17 only if a later design changes Teller;
- the actual Switchboard ID that resolves to the current manifest
  SwitchboardDelta address, including `getAddr(4)`, the reverse registry lookup
  for that address, registry version, and pending address updates; do not
  assume the historical ID 4 mapping still applies;
- `minDeleverageBps`;
- `deleverageBuffer`;
- `deleverageCooldown`;
- `underscoreSafeSpreadBps`;
- every pending Delta action and its confirmation/expiry state;
- the exact registry update timelocks;
- exact old/new creation and deployed bytecode hashes; and
- exact approved downstream coordinator addresses and versions.

The new Deleverage constructor initializes the first three governed fields to
zero and safe spread to `100`. Those defaults must not be assumed equal to live
state. The per-user `lastDeleverageBlock` mapping is unenumerable and cannot be
copied from a manifest.

### 8.2 Recommended staged order

No claim of three-way atomicity is made. Under the recommended no-Teller-change
design:

1. obtain fresh read-only Base state and prove cooldown is still `0`; otherwise
   stop for the nonzero reset policy below;
2. drain by cancellation, execution, or expiry every pending Delta action that
   could affect Deleverage; record closure;
3. deploy the reviewed new Deleverage candidate with the approved Base
   immutable maximum, without registry change;
4. verify code, constructor args, ABI, pause/governance posture, and the
   four-argument compatibility surface;
5. execute the separately approved RipeHq ID 18 registry replacement;
6. keep cooldown `0` and accept only owner-bounded temporary drift while the
   other governed values are restored through the actual timelocked governance
   path;
7. deploy and verify the approved downstream coordinator version, if any,
   after new Deleverage is active;
8. prove real context flows and retire or constrain old callers;
9. after proving the current Delta's actual Switchboard registry slot, deploy
   and replace it only at that proven slot after proving its current-target
   queue check and execution-time target validation; stop and revise this
   rollout if ID 4 does not resolve to the expected current address;
10. close all temporary drift with fresh reads and old/new hashes; and
11. leave nonzero cooldown activation to S6/later approval.

The deployment owner must supply a deadline and accountable owner for every
temporary drift interval. If current non-cooldown values cannot be restored
without an unacceptable interval, checkpoint 0 must revise the rollout or the
brief; S4 may not add unapproved constructor state.

If the live cooldown is nonzero, the safe default is:

1. pause or otherwise prevent new calls to old Deleverage under separately
   approved authority;
2. record the last possible old-call number;
3. wait at least the live cooldown through the exact expiry boundary;
4. prove no checkpoint can remain active under that value;
5. replace ID 18; and
6. preserve new stored cooldown `0`.

Any faster reset accepts loss of unenumerable checkpoint continuity and needs
explicit protocol/security approval.

### 8.3 Rollback and forward remediation

Before ID 18 changes, rollback is abandonment of the candidate and has no
protocol effect. After ID 18 changes, re-registering the old Deleverage
restores its old storage, including its old checkpoint mapping; it does not
restore state written only to the new contract. Rollback is therefore safest
while cooldown is `0` and before downstream callers depend on new selectors.

After a downstream context-aware caller is deployed, old Deleverage is not a
compatible rollback target. Forward remediation must then deploy/register a
fixed Deleverage that preserves the approved selectors or roll the downstream
caller back first under its own safe order.

Delta rollback is independently staged at the exact Switchboard registry slot
proven during preflight; this record does not establish that the current slot
is ID 4. A pending action must never be assumed to bind the target code seen at
queue time.

### 8.4 Robinhood

Track 7 reservation `0020_Track6S4DeleverageCooldown.py` remains a
predeployment artifact assertion. S4 does not create or execute it. The initial
Robinhood graph omits Underscore, so no Base Underscore coordinator should be
silently registered there. Deploy with the approved RH immutable maximum and
stored cooldown `0`; assert exact source/ABI/artifact identity and the absence
of unapproved context coordinators.

Permanent Base/Robinhood source divergence is rejected. Temporary version
drift requires an owner, deadline, exact hashes, rollback, and closure proof.

## 9. Recommended exact Stage B ownership

This is a proposed subset, not authorization:

- `contracts/core/Deleverage.vy`;
- `contracts/config/SwitchboardDelta.vy`;
- `tests/conf_core.py`;
- `tests/core/deleverage/test_deleverage_for_withdrawal.py`;
- `tests/core/deleverage/test_deleverage_permissions.py`;
- `tests/config/test_switchboard_delta.py`;
- generated `scripts/abis/Deleverage.json`; and
- new `docs/chains/rh/deleverage-cooldown-implementation-record.md`.

Not included under the recommendation:

- `contracts/core/Teller.vy`;
- Teller tests or ABI;
- `scripts/abis/SwitchboardDelta.json` unless generation proves its external
  ABI actually changed;
- migrations, manifests, defaults, parameter files, dependencies, S1, S2
  inventory, or Underscore files.

Stage C inventory reconciliation remains a later reviewer-gated stage and is
not part of the Stage B file set.

Mechanical maximum and context work may be separate reviewable commits, but
the final production artifact/release should be atomic. Deploying a
maximum-only intermediate Deleverage increases Base registry churn and leaves
the same-number vulnerability unresolved. If the context decision cannot
close, the recommended result is **do not deploy S4 yet**, not a live
maximum-only version. A different split requires explicit checkpoint approval.

If the selected coordinator is Teller, or if another Ripe file is required,
this file set is invalid and the owner must approve a revised exact subset
within the brief's ceiling or a reviewed brief amendment.

## 10. Proposed validation matrix

### 10.1 Mechanical maximum

- constructor maximum `0` rejects;
- constructor maximum `max_value(uint256)` rejects;
- approved maximum minus one, exact maximum, and plus one;
- getter returns the deployment immutable;
- governed cooldown `0`;
- Delta queries the current ID 18 maximum before queueing;
- current target changes to a lower maximum before execution;
- Deleverage revalidates at execution;
- duplicate constant is absent;
- Base and RH immutable artifact differences are exactly the approved
  immutables, not hidden source divergence; and
- existing checkpoint behavior under cooldown decrease, increase, zero, and
  reactivation.

### 10.2 Strict no-context behavior

- first eligible call succeeds and writes exact current number;
- second independent transaction at the same number is blocked;
- many independently committed calls in a synthetic same-number batch are
  blocked;
- second call at `+1` remains blocked;
- exact `last + cooldown - 1` blocked;
- exact `last + cooldown` succeeds;
- exact `last + cooldown + 1` succeeds;
- representative `+2` and `+4` number jumps are decided solely by the strict
  boundary: blocked before expiry and eligible at or after expiry;
- a synthetic `+60` jump has the same boundary behavior;
- a direct skip from just before expiry to after expiry succeeds without
  requiring an equality-number transaction;
- two users evaluated at the same number have independent checkpoints: each
  user's first eligible call succeeds, one user's write does not block the
  other, and later calls are blocked per user;
- unset checkpoint succeeds;
- zero cooldown remains disabled;
- maximum arithmetic is checked and does not wrap; and
- successful versus false-return versus reverted calls update state exactly as
  specified.

### 10.3 Context security

- exact coordinator opens for exact user;
- non-coordinator open rejects;
- zero, unknown, guessed, and copied IDs reject;
- wrong user and wrong coordinator reject;
- first context leg obeys preexisting cooldown;
- active preexisting cooldown prevents context opening;
- under the recommended deny-open policy, a legitimate multi-leg redemption
  attempted during the active window cannot complete through the context and
  remains unavailable until expiry unless every leg independently qualifies;
- if checkpoint 0 instead selects qualified bootstrap, the first leg must
  independently satisfy near redemption and every continuation boundary,
  state change, callback, close, and replay case must prove that authorization
  cannot broaden;
- successful first leg establishes only that context's continuation;
- two approved distinct legs pass;
- no-context call while context active rejects;
- same asset/vault repeat retains transient suppression;
- explicit close invalidates;
- same-transaction use after close rejects;
- later-transaction replay rejects even at the same number;
- nested same-user opening rejects;
- two users are rejected unless checkpoint 0 explicitly approves and tests
  independent contexts;
- token, vault, PriceDesk, CreditEngine, PSM, and coordinator callbacks cannot
  substitute caller/user/context;
- uncaught failed middle leg reverts context, checkpoint, and transient state;
- any approved caught-failure recovery has its own exact close/retry tests; and
- events, if selected, contain no misleading persistent-authority claim.

### 10.4 Near redemption and formula preservation

- near-redemption no-context call retains its independent safety bypass;
- near-redemption cannot open or forge a context;
- deny-open behavior demonstrates the explicit legitimate multi-leg liveness
  cost during an active cooldown;
- any selected qualified-bootstrap alternative proves that the first-leg
  condition cannot be manufactured and does not authorize an otherwise
  ineligible later leg outside the exact approved continuation scope;
- context cannot broaden or cache the redemption threshold;
- state changes between legs are re-evaluated;
- minimum-deleverage bypass remains independent;
- deleverage formulas, caps, repayment, and collateral handling are unchanged;
  and
- `_vaultId=0` resolution remains exact.

### 10.5 Compatibility and downstream

- old four-argument caller -> old Deleverage fixture;
- old four-argument caller -> new Deleverage fixture;
- new context caller -> old Deleverage expected selector failure;
- new context caller -> new Deleverage success;
- arbitrary valid Ripe and Underscore callers have no context;
- arbitrary caller remains rejected;
- Teller withdraw, withdrawMany, and rebalance remain no-call regressions under
  the no-Teller recommendation;
- separate Underscore tests cover raw underlying, collateral vault token,
  leverage vault token, early returns, delegated allowance caller, and real
  Ripe rather than `MockRipe`; and
- Base staged-order and rollback simulations use RipeHq ID 18 plus the actual
  Switchboard ID proven for the current Delta; they must not assume ID 4.

### 10.6 Required gates

After H-01 reconciliation and again after implementation as required:

- all five S4 targeted files;
- S1 clock harness;
- deterministic S2 checker;
- S2 inventory tests;
- full collection;
- full suite;
- ABI regeneration and diff;
- compiler integrities and creation/deployed bytecode hashes;
- `git diff --check`;
- exact changed-file allowlist; and
- independent security and compatibility review.

## 11. H-01 consequence

The owner-selected order is H-01 first. The current S4 hashes and green
baseline are launch evidence only, not Stage B inputs. H-01 may change Vyper,
Titanoboa, pytest, transitive dependencies, compilation, cache behavior,
bytecode, or tests even if S4 source is untouched.

When H-01 is integrated:

1. record the integrated H-01 commit and new `rh` head;
2. obtain owner direction for rebase/merge/recreation of this S4 branch;
3. verify the old S4 commit and this decision record against the reconciled
   tree;
4. regenerate dependency, source, ABI, compiler-integrity, creation-bytecode,
   and runtime hashes;
5. rerun the entire Stage A baseline serially;
6. revise any design assumption affected by dependency/compiler behavior; and
7. obtain owner and independent security approval on that exact baseline and
   exact Stage B file set.

No floating H-01 candidate lock, alert analysis, branch tip, or unreviewed
working tree satisfies this gate.

At this re-review's final read-only check, the clean H-01 branch tip was
`22eb097e86a123c01a7117d5166b87ed11ae30c9` and its only committed delta from
the S4 launch baseline was its dependency-security evidence document. That
moving documentation branch is evidence of H-01 work in flight, not proof of
independent approval or integration into `rh`.

## 12. Open blockers

1. Exact maximum wall-time intent and S4-specific cadence approval.
2. Exact Base and Robinhood immutable maxima.
3. Exact activation release; recommended initial value is `0`.
4. Exact coordinator identity and authorization source. “Any valid
   Underscore address” is not exact enough.
5. Exact context selectors, ID generation, binding, nesting, multiple-user,
   callback, close, replay, and active-window opening policy, including explicit
   acceptance of the deny-open availability cost or approval of a fully
   specified alternative.
6. Security acceptance of first-call cooldown grief under the unchanged broad
   trusted-caller policy.
7. Exact near-redemption interaction with context opening, including selection
   among deny-open, qualified bootstrap, and no active context release.
8. Exact four-argument and old/new compatibility requirements.
9. A separate Underscore brief, owner, tests, version order, and deployment
   gate if the real Base multi-leg flow is selected.
10. Fresh Base governed values, pause/governance state, pending actions,
    timelocks, reset/rollback plan, and proof of the current Delta's actual
    Switchboard registry slot; historical ID 4 is insufficient.
11. An owner/deadline for every temporary Base drift window.
12. H-01 independent review, integration commit, S4 reconciliation direction,
    and post-H-01 validation.
13. Exact Stage B file set and release atomicity.
14. Independent security-review approval of the complete record.
15. S6 ownership of any nonzero cooldown and Track 7 deployment assertions.
16. Owner disposition of the ten floating integration-worktree documents:
    confirm authorized provenance and land them through review, or explicitly
    direct preservation/quarantine and restoration. If authorized, the owner
    must also direct whether their proposed Phase A0/decision 0 amends S4.

## 13. Mandatory checkpoint 0 approval record

Stage A kickoff approval and H-01-first direction are recorded from the owner
instruction dated 24 July 2026. They are not approvals of the rows below.
Before these rows can become final, the owner must separately resolve the
post-launch integration-worktree provenance in section 1.1. That resolution
does not become a new S4 decision 0 unless the owner confirms that the floating
amendment was authorized and expressly adopts it.

| # | Mandatory decision | Stage A recommendation | Owner status | Independent security status |
| ---: | --- | --- | --- | --- |
| 1 | Maximum wall-time intent | Preserve approximately four hours | **PENDING** | **PENDING** |
| 2 | Per-chain immutable values and cadence | Base `7_200`; RH `1_200`, only with S4-specific cadence approval | **PENDING** | **PENDING** |
| 3 | Activation posture | Preserve initial stored `0`; nonzero belongs to S6/later release | **PENDING** | **PENDING** |
| 4 | Coordinator set | Exact identified Underscore coordinator if real multi-leg support is required; no Teller by default; none on initial RH | **PENDING exact identity** | **PENDING** |
| 5 | Context architecture | Option 4 ABI envelope plus option 2 Deleverage-managed transient context; select deny-open and accept its liveness cost, approve a fully specified qualified-bootstrap alternative, or select no active context release | **PENDING exact selectors/opening policy** | **PENDING** |
| 6 | Near-redemption policy | Preserve independent per-call bypass; never use it as reusable context authority; explicitly approve its interaction with the row-5 opening policy | **PENDING exact interaction/liveness acceptance** | **PENDING** |
| 7 | ABI compatibility | Retain strict four-argument path; add separately named context path | **PENDING** | **PENDING** |
| 8 | Cross-repository policy | Separate Underscore brief/change/deployment gate required if coordinator selected; no Underscore edits in S4 | **PENDING** | **PENDING** |
| 9 | Base live-version policy | Staged two-registry convergence using RipeHq ID 18 and the freshly proven current Delta registry slot, cooldown `0`, bounded drift, no permanent divergence | **PENDING exact live plan and registry proof** | **PENDING** |
| 10 | H-01/S4 order | H-01 first | **OWNER DIRECTION RECORDED; exact integrated commit and reconciliation still PENDING** | **PENDING dependency baseline** |
| 11 | Stage B file set and atomicity | Exact subset in section 9; separate commits allowed, one final artifact/release | **PENDING** | **PENDING** |

### Required approval fields

```text
Owner:
Owner approval date:
Owner disposition of integration-worktree provenance:
Owner direction on proposed Phase A0/decision 0, if authorized:
Owner-approved exact answers 1-11:
Owner-approved exact Stage B files:
Owner-approved H-01 integrated commit:
Owner S4 reconciliation direction:

Independent security reviewer:
Security review date:
Security review evidence/commit:
Security-approved exact answers 1-11:
Security-approved exact Stage B files:
Residual risks explicitly accepted:

Independent compatibility/downstream reviewer, if separate:
Compatibility review date:
Compatibility evidence:
Underscore brief/owner/version/deployment gate, if selected:
```

Until every required field is complete and points to the post-H-01 reconciled
baseline, checkpoint 0 remains open and Stage B must not begin.

## 14. Stage A integrity and handoff

Stage A changed only this decision record. It did not modify contracts, ABIs,
tests, inventory, dependencies, migrations, manifests, defaults, the
Underscore repository, or live state. It did not push, merge, deploy, sign, or
execute a governance or state-changing transaction.

Checkpoint outcome: **stop; do not implement yet**.
