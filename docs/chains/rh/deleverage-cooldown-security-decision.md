# Track 6 S4 Deleverage Cooldown Security and Compatibility Decision

**Status:** Stage A no-code initial-launch decisions 1-9 owner-approved;
mandatory checkpoint 0 remains open for independent security and handoff
evidence; Stage B and Stage C must not begin

**Prepared:** 24 July 2026

**Original Stage A commit:** `a7414b5b56d20fc753c9263e7b494a75189eb223`

**Independent re-review correction commit:**
`105fb9507af30d7898113cc0a05f824a40123a4f`

**Re-review correction date:** 24 July 2026

**Owner direction update:** 24 July 2026

**Owner checkpoint approval:** Decisions 1-9 at
`4d6c3ff43c3ceacbad8ff24b860acfc21bb043e8`, approved by direct owner
instruction on 24 July 2026

**Stage A launch baseline:** `3e6e6f230169fc445d0b29454457480c62efd89a`

**Branch:** `rh-track-6-s4-deleverage-cooldown`

**Worktree:** `/Users/wigglez/dev/ripe-protocol-track-6-s4-deleverage-cooldown`

## Authorization and stop condition

The owner authorized S4 Stage A only on 24 July 2026. That authorization
supersedes only the pre-kickoff status line in
`track-6-s4-deleverage-cooldown.md`. It does not approve any production
decision, Stage B file, external-repository change, deployment, governance
action, or live transaction.

The owner also selected **H-01 first**. If S4 is ever reopened for
implementation, Stage B remains blocked until:

1. H-01 is independently reviewed and integrated into `rh`;
2. this branch is reconciled with that exact dependency baseline under owner
   direction;
3. the baseline, compiler inputs, artifacts, target tests, S1, S2, collection,
   and full suite are reproduced after reconciliation; and
4. the owner and an independent security reviewer approve every reopened
   checkpoint-0 decision and the exact Stage B file set.

On 24 July 2026, the owner added two controlling inputs for the initial
Robinhood launch: Underscore will not be included, and production
smart-contract changes should be minimized where configuration or omission can
bound the risk. The owner directed Stage A to prepare the no-code recommendation
below but explicitly did **not** approve the conclusion by giving that
direction. No response to the revised checkpoint items means no S4 production
edit and no Stage B or Stage C.

The owner then separately and explicitly approved decisions 1-9 at
`4d6c3ff43c3ceacbad8ff24b860acfc21bb043e8` on 24 July 2026. That approval
accepts the no-code recommendation and its stated owner risks and handoffs. It
does not constitute independent security approval, downstream handoff
completion, implementation authority, deployment authority, or permission to
begin Stage B or Stage C.

## Re-review disposition

The original handoff incorrectly presented the unchanged original Stage A
commit as if it contained the requested re-review corrections. This revision
creates the missing audit trail and resolves the review findings as follows:

| Review item | Disposition in this revision |
| --- | --- |
| Current SwitchboardDelta registry identity was asserted from a stale historical migration | Accepted. Historical ID 4 registration, current manifest deployment, and current onchain registry identity are separated. The actual slot is a future replacement input, not an initial no-code-launch blocker. |
| BN-012 occurrence count was understated | Accepted. Deleverage has three occurrences on two source lines, not two occurrences. |
| Strict-boundary matrix omitted required number jumps, expiry skip, and two-user independence | Accepted. The required future-reopening cases are retained in section 10.5 even though the no-code initial launch adds no tests. |
| Active-cooldown context-open rule hid a legitimate multi-leg availability cost | Accepted. The trade-off and future alternatives remain explicit in sections 4 and 5; the initial launch avoids the active window by keeping cooldown `0`. |
| H-01 snapshot was stale | Accepted. The latest inspected H-01 tip and its evidence-only branch delta are recorded without treating either as integration or approval. |
| Integration worktree contains uncommitted minimum-change material of unknown provenance | The later direct owner instruction now establishes the S4 decision inputs independently of those files. The files remain uncommitted and untouched; their planning corrections are handoffs, not integrated evidence. |

## Executive security conclusion

The current same-number exception is not a transaction boundary. Independent
transactions in one sequencer batch can share `block.number`, so
`block.number > lastBlock` permits every one of them to bypass an active
cooldown. It would therefore be unsafe to activate a nonzero Robinhood
cooldown without reopening and resolving S4.

The actual committed multi-leg consumer is Underscore
`LevgVaultWallet`, not Ripe `Teller`. `Teller.withdraw`,
`Teller.withdrawMany`, and `Teller.rebalance` contain no production call to
`deleverageForWithdrawal`. Selecting Teller as coordinator would introduce new
production behavior rather than preserve an existing flow.

For the initial Robinhood launch, Underscore is omitted and the configured
cooldown is `0`. At `0`, the cooldown guard and its unsafe same-number
exception are dormant. There is no normal initial-launch caller for the
Underscore withdrawal flow, while the existing caller authorization,
debt-position, withdrawal-value, repayment, and collateral checks remain.

The revised Stage A recommendation is owner-approved; independent security
approval remains pending:

- deploy the existing shared Deleverage and SwitchboardDelta source unchanged;
- configure Robinhood `deleverageCooldown = 0`;
- make no S4 change to Deleverage, SwitchboardDelta, Teller, interfaces, ABIs,
  tests, production migrations, or Base deployment state;
- retain both `MAX_COOLDOWN_BLOCKS = 7_200` constants as documented latent
  debt rather than changing production bytecode solely to deduplicate a
  dormant limit;
- do not begin Stage B or Stage C;
- keep migration reservation
  `0020_Track6S4DeleverageCooldown.py` inert as a predeployment/assertion hook;
  and
- require S4 to be reopened before Underscore is enabled on Robinhood or
  governance proposes any nonzero deleverage cooldown.

This zero-cooldown rule is **procedural, not enforced by current onchain
code**. SwitchboardDelta governance technically retains the ability to queue
and later execute a nonzero value up to the existing duplicated `7_200`
ceiling. Adding an onchain Robinhood-specific prohibition would itself require
the production-contract change this recommendation avoids. The safety boundary
therefore depends on approved defaults, an exact parameter manifest,
post-deployment assertion, governance procedure, and mandatory S4 reopening.

The owner accepted the following bounded initial-launch risks; independent
security acceptance remains pending:

- cooldown `0` provides no pacing between otherwise valid deleverage actions;
- Underscore is omitted, so there is no normal initial-launch caller for its
  withdrawal deleverage flow;
- the underlying authorization and debt/withdrawal checks remain;
- the current same-number exception would defeat intended pacing for separate
  transactions if a future nonzero cooldown were activated; and
- any Underscore inclusion or nonzero proposal must therefore reopen S4 before
  governance queues the change.

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

#### Post-launch integration-worktree hygiene and planning-correction status

At the independent re-review snapshot, the integration worktree was checked
read-only. Local `rh` was at
`27765d29094256fa9619dd44a0bfd145863de8b7`, one local documentation commit
ahead of `origin/rh`, and the worktree had nine modified tracked
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

That snapshot also had one untracked 373-line file,
`docs/chains/rh/minimal-contract-change-reassessment.md`, with SHA-256
`57c94b7f6b4e7a9609803567c0dd90442210f8aa88cbc9c2b06629fe222a769c`.
The floating S4 edits appear to add a minimum-change amendment, Phase A0, and
decision 0, while other files alter previously checked clock-plan statements.
There is no commit or other Git provenance tying those working-copy edits to
owner authorization.

This owner-direction revision rechecked that local `rh` is still at the same
commit and the same ten paths remain dirty/untracked, so the batch has not
landed. The foreign active worktree continued changing during this revision;
its historical snapshot counts and hash above are retained rather than
silently restamped as S4 evidence.

Those post-launch edits remain **unintegrated input, not repository
authority**. The direct owner direction dated 24 July 2026 independently
establishes the S4 constraints used by this revision: no initial Underscore,
minimum production-contract change, cooldown `0`, no Stage B/C, and explicit
reopening triggers. This revision does not rely on the floating files for that
authority and does not copy, modify, stage, discard, or otherwise normalize
them.

Because the batch planning-correction pass has not landed, section 10 records
the required BN-012, decision-register, S6, Track 7 H-08, and migration-0020
corrections as cross-track handoffs only. Their absence from the integrated
documents does not authorize S4 to edit another active track. The owner
approval is now recorded, but checkpoint 0 remains open for independent
security approval and the named cross-track handoff evidence.

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

Historical migrations are immutable and must not be edited. The initial
no-code recommendation needs no S4 migration or new Deleverage immutable. Test
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

This section preserves the evidence needed if S4 is reopened. It does not
recommend adding a coordinator, context, selector, or contract change for the
initial Robinhood launch. Underscore is absent from that launch graph.

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

Initial-launch compatibility overlay:

- every existing selector and ABI remains unchanged;
- no context entry point or coordinator authority is added;
- `deleverageCooldown = 0` leaves the same-number guard dormant;
- the Robinhood graph contains no Underscore caller or address; and
- any proposal to add Underscore or make the cooldown nonzero invalidates this
  no-code conclusion and reopens the option analysis in section 5.

External calls inside the Deleverage execution reach CreditEngine, Mission
Control, PriceDesk, VaultBook/Registry, vaults, AuctionHouse, token/vault
implementations, Endaoment/PSM-related assets, and repayment logic. Context
authorization would have to be established before these calls and remain bound
through callbacks if a future reopened S4 selected a context design. It could
not rely on a callback-visible block number or `msg.sender` alone.

## 4. Threat model and residual risk

“Owner” below means the role that must accept the residual risk in addition to
independent security review.

For the initial no-code launch, the mitigation is omission of Underscore plus
procedural/configuration enforcement of cooldown `0`. The “future reopen
mitigation” column below is retained analysis, not current implementation
scope.

| Threat | Asset/invariant and required authority | Current behavior | Future reopen mitigation | Residual risk, proof, rollout, owner |
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

## 5. Dormant context architecture comparison for a future reopening

No context option is selected or implemented for the initial Robinhood launch.
This analysis becomes active only if Underscore inclusion or nonzero cooldown
activation reopens S4.

| Option | Same-number protection and authorization | Binding, lifetime, nesting/replay | Compatibility and change surface | Test/rollback result | Future disposition |
| --- | --- | --- | --- | --- | --- |
| 1. No exception | Strongest: every later call obeys cooldown; no coordinator authority | No context risk | Four-argument ABI unchanged; no Teller/Underscore code change, but legitimate nonzero-cooldown Underscore multi-leg flows may fail | Easy to test and roll back; unsafe for known downstream availability unless owner chooses no coordinator/nonzero activation | Reassess only after a reopen; not an initial-launch change |
| 2. Deleverage-managed explicit context | Strict default plus exception only for exact approved coordinator | Deleverage-issued ID bound to caller/user in transient storage; reject zero, mismatch, nesting, reuse | Deleverage ABI/runtime changes; exact coordinator must open/pass/close; old wrapper can remain | Central state is directly testable; rollback requires mixed-version plan | Strong future security primitive, but expressly outside the initial launch |
| 3. Coordinator-managed transient scope | Deleverage must trust or query coordinator-reported state | Coordinator owns scope; a malicious or replaceable coordinator can self-attest unless Deleverage independently binds it | Larger downstream-specific interface; Ripe security depends on external transient implementation | Harder cross-contract proof and rollback; coordinator replacement is high risk | Not recommended without a stronger independently verifiable flow proof |
| 4. Four-argument wrapper plus new context entry | Strict old path; approved context path uses option 2 controls | Same as option 2 | Preserves old selector; adds new selector/open/close/getter/events. Teller unchanged unless separately selected. Underscore needs a new version to consume it. | Best old-caller compatibility; old callers cannot obtain exception | Preferred future ABI envelope if a reopened review selects option 2 |
| 5. Coordinated Ripe/Underscore ABI replacement | Can implement exact downstream flow | Binding can be strong but both repositories and deployments must move in safe order | Broadest cross-repo surface; old/new mismatches can revert | Requires separate Underscore brief, full end-to-end tests, deployment owner, rollback, and live gate | Required rollout work if Underscore is selected, but prohibited as an S4 edit and not a substitute for option 2/4 |

All options are testable under the S1 number controller, but with different
proof surfaces. Option 1 needs only strict-boundary Ripe fixtures. Options 2
and 4 add transient lifetime, callback, and mixed-ABI fixtures. Option 3 also
needs an adversarial external coordinator implementation. Option 5 needs the
same Ripe fixtures plus a real cross-repository end-to-end suite. For the
context surface, options 2-5 change Deleverage bytecode and external ABI;
option 4 uniquely preserves the old selector as an explicit compatibility
envelope. Options 3 and 5 also change downstream bytecode. The independent
authoritative-maximum work would change Deleverage and Delta under every S4
implementation option. The initial recommendation selects none of them and
keeps the duplicated maximums as latent debt.

### 5.1 Future provisional context contract, not initial-launch scope

If a reopening selects a context, the exact names would become checkpoint
decisions. The strongest provisional semantics identified by Stage A are:

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

The owner and reviewer may select different names, but they would have to
approve the exact selectors and semantics before any future Stage B.

#### Availability trade-off on future reopening

Rule 5 deliberately prevents a near-redemption result from becoming reusable
context-opening authority, but it has a material liveness cost. If a user
already has an active cooldown, a legitimate multi-leg redemption cannot open
the context. Even if the first leg independently qualifies for the
near-redemption bypass, later legs that do not independently qualify remain
blocked, so the complete withdrawal may have to wait until cooldown expiry.
This is a protocol availability decision, not an implementation detail.

A future reopened checkpoint must select and independently approve exactly one
of:

1. **deny active-window opening:** keep rule 5 and explicitly accept that a
   legitimate multi-leg redemption may be unavailable until expiry;
2. **qualified bootstrap:** allow opening only from a first leg that
   independently satisfies the near-redemption condition, then specify the
   exact continuation scope and prove that the condition cannot be
   manufactured, cached, or broadened for later legs; or
3. **no active context release:** keep governed cooldown `0` and ship no
   active nonzero-cooldown context behavior in the initial release.

The no-code initial launch is option 3 in practical effect: cooldown remains
`0` and no context behavior ships. If S4 reopens, deny-open is viable only if
its liveness loss is accepted, while qualified bootstrap is not recommended
without a substantially stronger, flow-specific proof.

### 5.2 Designs rejected if S4 reopens

- retaining the current `block.number > lastBlock` exception while activating
  a nonzero cooldown;
- `tx.origin`;
- `msg.sender` alone as proof of one top-level flow;
- a persistent or cross-transaction bypass nonce;
- an unbound boolean;
- caller-supplied ID treated as authority;
- a context open to every valid Ripe or Underscore address;
- implicit or unreviewed context creation from the near-redemption result;
- a context that survives the top-level transaction;
- `chain.id` branching or a Robinhood-only contract; and
- claiming Teller integration where none exists.

The duplicated maximum constants are not endorsed as good design; they are
recommended for acceptance as dormant initial-launch technical debt to avoid
an otherwise unnecessary production-contract change.

## 6. Initial-launch maximum and activation disposition

The initial-launch recommendation does not choose a Robinhood wall-time
maximum and does not change either existing `MAX_COOLDOWN_BLOCKS = 7_200`
constant. Both constants remain in the shared Deleverage and SwitchboardDelta
source. Their duplication and the stale “~1 day at 12s/block” comment are
documented latent debt, not approved portable timing semantics.

| Control | Pending initial-launch recommendation |
| --- | --- |
| Shared source | Deploy existing Deleverage and SwitchboardDelta source unchanged |
| Immutable/source ceiling | Retain both existing numeric `7_200` constants unchanged |
| Robinhood stored value | Exactly `0` |
| Underscore | Omitted from the initial Robinhood graph |
| Nonzero activation | Procedurally prohibited until S4 is reopened |
| Enforcement owners | S6 defaults/parameter manifest, Track 7 H-08 assertion, governance procedure |
| Contract-enforced Robinhood prohibition | Deliberately not added because it would require production bytecode divergence or another shared production change |

The prohibition is not an onchain invariant. SwitchboardDelta can still queue
a nonzero value within its current ceiling, and Deleverage can still accept
that value from an authorized switchboard. The recommendation relies on
configuration, deployment validation, governance discipline, and the explicit
reopening gate. It must never be described as technically impossible for
governance to activate the cooldown.

At cooldown `0`, reads of the existing checkpoint mapping do not pace calls.
Existing checkpoints are neither cleared nor reinterpreted. If governance ever
proposes a nonzero value, the reopened review must analyze immediate effects on
old checkpoints, same-number bypass, wall-time intent, caller graph, and
multi-leg availability before the value is queued.

## 7. ABI and version disposition

There is no old/new S4 ABI matrix for the initial Robinhood launch because S4
recommends no production artifact change:

| Surface | Pending initial-launch disposition |
| --- | --- |
| Deleverage constructor and external ABI | Existing shared source and ABI unchanged |
| `deleverageForWithdrawal` | Existing four-argument behavior unchanged |
| SwitchboardDelta interface and ABI | Existing shared source and ABI unchanged |
| Teller and TellerUtils | Existing shared source and ABI unchanged |
| Context selectors/events | Not added |
| Base versions | No S4 replacement, migration, or convergence work |
| Robinhood versions | Deploy the same existing shared source selected by the ordinary deployment track |

There is no mixed-version interval and no S4-specific Base drift to manage.
The future ABI/context analysis in sections 3-5 is dormant until a reopening.

## 8. Initial Robinhood deployment boundary

The initial deployment must:

1. deploy the existing shared Deleverage and SwitchboardDelta source without
   an S4 patch or Robinhood-only branch;
2. omit Underscore addresses and caller integration from the Robinhood graph;
3. source `deleverageCooldown = 0` from the approved Robinhood defaults and
   parameter manifest;
4. assert the deployed/live value is exactly `0`;
5. keep reservation `0020_Track6S4DeleverageCooldown.py` inert as a
   predeployment/artifact assertion hook; and
6. record that any nonzero governance proposal or Underscore inclusion reopens
   S4 before queueing, deployment, or registration.

No S4 action changes Base state, RipeHq ID 18, the current Switchboard registry,
governance ownership, pending actions, ABI, or bytecode. The unresolved
historical-versus-current SwitchboardDelta registry-ID evidence remains useful
for a future replacement, but it is not an initial-launch blocker because S4
recommends no Delta replacement.

The no-code rollback is simple: before deployment, correct the defaults or
manifest if the value is not `0`; after deployment, H-08 must fail the handoff
if the live value is not `0`. This record does not authorize a governance
transaction to repair a mismatch, and it does not define deployment
remediation owned by Track 7.

## 9. Stage B and Stage C disposition

The pending checkpoint recommendation is **do not proceed to Stage B or Stage
C**. Therefore S4 has no approved Stage B file set. In particular, S4 must not
modify:

- `contracts/core/Deleverage.vy`;
- `contracts/config/SwitchboardDelta.vy`;
- `contracts/core/Teller.vy` or TellerUtils;
- interfaces or generated ABIs;
- `tests/conf_core.py` or any Deleverage, Delta, Teller, clock, or inventory
  test;
- production migrations, manifests, defaults, parameter files, dependencies,
  S1/S2 inventory, or the Underscore repository.

If either reopening trigger occurs, the previous proposed Stage B subset is
not automatically authorized. A new baseline, exact file set, owner approval,
and independent security approval are required at that time.

## 10. Cheap enforcement and cross-track handoffs

S4 implements none of the work below. These are exact acceptance criteria for
the owning tracks because the batch planning-correction pass has not landed.

### 10.1 S6 defaults and parameter manifest

S6 must ensure both `DefaultsRobinhood` and the approved Robinhood parameter
manifest:

- set `deleverageCooldown` to the exact integer `0`;
- do not inherit or infer a nonzero Base value;
- state verbatim: **“activation requires reopening S4”**; and
- fail generation or review if the field is absent, nonzero, or ambiguous.

This is configuration enforcement, not a contract-level prohibition.

### 10.2 Track 7 H-08 post-deployment validation

The H-08 read-only post-deployment checker must assert that live Robinhood
`Deleverage.deleverageCooldown()` is exactly `0`. A nonzero value is a hard
failure, not a warning or accepted drift. H-08 must also prove the intended
Underscore omission through its ordinary deployment-graph/manifest assertions.
S4 does not add the checker or its tests.

### 10.3 Reserved migration 0020

`0020_Track6S4DeleverageCooldown.py` remains only a predeployment/artifact
assertion hook. It must not contain an S4 contract upgrade, registry
replacement, ABI change, or state-changing cooldown transaction unless S4 is
later reopened and implementation is separately approved.

### 10.4 BN-012 and decision-register planning correction

The next authorized batch planning-correction pass must change BN-012 and the
Track 6 decision-register disposition from the old modify-shared default to:

> accepted dormant at initial launch; reopen on Underscore inclusion or
> cooldown activation

The correction must preserve the evidence that BN-012 has three Deleverage
occurrences on two source lines, the duplicated `7_200` caps, the unsafe
same-number behavior under nonzero cooldown, and the absence of normal initial
Underscore callers. It must be landed with proper checked-item and baseline
provenance. This S4 branch does not edit the inventory, shared specification,
validation plan, component matrix, Track 7 documents, or `rh-summary.md`.

### 10.5 Reopening gate

Before either trigger proceeds:

1. stop before Underscore is added to the Robinhood graph or before a nonzero
   cooldown is queued;
2. reopen S4 against the then-integrated `rh` and dependency baseline;
3. revalidate the actual caller graph, governance path, current code and
   registry identities;
4. resolve the same-number pacing failure and multi-leg behavior;
5. approve an exact implementation/no-implementation decision and file set;
   and
6. obtain explicit owner and independent security approval.

Any reopened implementation validation must retain the already identified
boundary cases: repeated independent same-number calls,
`last + cooldown - 1`, exact expiry, `last + cooldown + 1`, representative
`+2/+4` jumps, synthetic `+60` stress, a direct before-to-after-expiry skip,
and two users at the same number. Recording those future cases does not
authorize S4 test changes now.

## 11. H-01 consequence

The no-code initial-launch recommendation changes no dependency, compiler
input, source, ABI, test, or artifact. H-01 integration is therefore not
required to evaluate this documentation-only checkpoint recommendation.

The owner's **H-01 first** direction remains fully binding if S4 is reopened
for Stage B. Before any future S4 implementation:

1. H-01 must be independently reviewed and integrated into `rh`;
2. the S4 branch must be reconciled with that exact baseline under owner
   direction;
3. the full source, ABI, compiler, artifact, test, S1, S2, collection, and
   suite baseline must be regenerated; and
4. the exact reopened decisions and file set must receive owner and independent
   security approval.

No floating H-01 branch tip or documentation-only candidate satisfies that
future gate.

## 12. Open blockers

1. Independent security approval of the owner-approved conclusion and bounded
   risks:
   no pacing at `0`, procedural rather than onchain enforcement, retained
   governance ability, duplicated ceiling debt, and unsafe future nonzero
   same-number behavior.
2. S6 acceptance of the exact defaults/manifest handoff.
3. Track 7 acceptance of the exact H-08 and migration-0020 handoffs.
4. An authorized planning-correction commit that updates BN-012 and the Track 6
   decision register without rewriting checked history in place.
5. Governance/runbook ownership for stopping any nonzero proposal before queue
   and reopening S4.
6. Independent confirmation that the initial Robinhood graph omits Underscore.

Maximum intent, context architecture, ABI changes, Base convergence, current
Delta registry identity, H-01 reconciliation, and an exact Stage B file set are
not initial-launch blockers because the recommendation selects no S4
implementation. They become blockers immediately if either reopening trigger
occurs.

## 13. Mandatory checkpoint 0 approval record

Stage A kickoff, H-01-first ordering for any implementation, omission of
Underscore from the initial graph, and the standing minimum-change directive
were recorded owner directions dated 24 July 2026. In a separate direct
instruction on 24 July 2026, the owner approved decisions 1-9 exactly as
recorded at `4d6c3ff43c3ceacbad8ff24b860acfc21bb043e8`.

| # | Mandatory decision | Stage A recommendation | Owner status | Independent security status |
| ---: | --- | --- | --- | --- |
| 1 | Initial S4 production scope | Deploy existing shared Deleverage and SwitchboardDelta source unchanged; no S4 contract, interface, ABI, test, state-changing migration, Base, or Underscore change | **APPROVED at `4d6c3ff`; 24 July 2026** | **PENDING** |
| 2 | Initial cooldown | Pin Robinhood `deleverageCooldown = 0` in S6 defaults and parameter manifest | **APPROVED at `4d6c3ff`; 24 July 2026** | **PENDING** |
| 3 | Enforcement model | Accept that zero is procedural/configuration-enforced, not prohibited by current onchain code; governance technically retains the ability to queue nonzero | **APPROVED at `4d6c3ff`; 24 July 2026** | **PENDING** |
| 4 | Latent debt | Retain duplicated `MAX_COOLDOWN_BLOCKS = 7_200` constants and stale wall-time comment as documented dormant debt | **APPROVED at `4d6c3ff`; 24 July 2026** | **PENDING** |
| 5 | Initial caller graph | Omit Underscore; no Teller coordinator or context is added | **APPROVED at `4d6c3ff`; 24 July 2026** | **PENDING graph/risk confirmation** |
| 6 | Stage progression | Do not begin Stage B or Stage C; no Stage B file set exists | **APPROVED at `4d6c3ff`; 24 July 2026** | **PENDING** |
| 7 | Reopening triggers | Reopen S4 before Underscore inclusion or before governance proposes/queues any nonzero cooldown | **APPROVED at `4d6c3ff`; 24 July 2026** | **PENDING** |
| 8 | Cheap enforcement handoffs | S6 manifest/default pin, H-08 live-zero assertion, inert 0020 hook, BN-012/decision-register correction | **APPROVED at `4d6c3ff`; 24 July 2026** | **PENDING** |
| 9 | Initial risk proposed for acceptance | No cooldown pacing, no normal Underscore caller, underlying checks remain, same-number bypass unsafe on future activation | **APPROVED at `4d6c3ff`; 24 July 2026** | **PENDING** |

### Required approval fields

```text
Owner: repository owner, by direct instruction
Owner approval date: 24 July 2026
Owner-approved exact answers 1-9: approved exactly as recorded at 4d6c3ff43c3ceacbad8ff24b860acfc21bb043e8
Owner-approved initial Robinhood cooldown value: 0
Owner acceptance that enforcement is procedural, not onchain: yes; governance retains technical ability to queue nonzero
Owner acceptance of dormant duplicated-constant debt: yes
Owner-approved reopening triggers: before Underscore inclusion or any nonzero cooldown proposal/queue
Owner-approved S6 / H-08 / 0020 / planning-correction handoffs: yes, exactly as recorded in section 10

Independent security reviewer: PENDING
Security review date: PENDING
Security review evidence/commit: PENDING
Security-approved exact answers 1-9: PENDING
Residual risks explicitly accepted: PENDING

S6 handoff owner/review evidence: PENDING
Track 7 H-08 and 0020 handoff owner/review evidence: PENDING
Planning-correction commit: PENDING
Governance/runbook reopening owner: PENDING
```

Until every required field is complete, checkpoint 0 remains open. Stage B and
Stage C must not begin.

## 14. Stage A integrity and handoff

Stage A changed only this decision record. It did not modify contracts, ABIs,
tests, inventory, dependencies, migrations, manifests, defaults, the
Underscore repository, or live state. It did not push, merge, deploy, sign, or
execute a governance or state-changing transaction.

Owner-approved checkpoint recommendation, still pending independent security
approval and cross-track handoff evidence: **accept S4 as dormant for the
initial Robinhood launch; deploy unchanged shared source with cooldown `0`; do
not begin Stage B or Stage C; reopen before Underscore inclusion or any
nonzero cooldown proposal**.
