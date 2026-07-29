# Track 6 S6 / Track 7 H-04 Phase A: Robinhood Defaults and Parameter Inventory

**Status:** Phase A evidence candidate for independent complete-file Gate 1
review. This document is repository-only analysis and an owner decision
packet. It selects no production value, creates no implementation, manifest,
generator, or test, performs no RPC, secret access, deployment, migration,
governance action, signing, transaction, or external write, and does not
authorize Phase B. Phase B remains unauthorized until the complete Phase A
owner-decision packet has independent complete-file approval, exact Phase B
file ownership is reverified, and a separate file-exact owner implementation
authorization is recorded.

**Phase A evidence date:** 2026-07-27

**Controlling brief:**
`docs/chains/rh/track-6-s6-track-7-h4-defaults-parameters.md`, integrated at
the baseline below with SHA-256
`50abd02e94c0a5af8aa45d77051ccf29ee802399f68918cee21e813c5c990aec`.

**Address-literal rule for this document:** this evidence contains no raw
account, token, feed, or contract address literals. Every address-bearing fact
is cited by source path and line. This prevents any Base or provisional
address from being copied forward as a Robinhood value.

## 1. A1 — Baseline freeze and ownership map

### 1.1 Exact baseline identity

| Identity | Value |
| --- | --- |
| Phase A baseline commit (`rh` tip at kickoff) | `e39815d710ecfaf8bbeea54cabe8ae8d553a2740` |
| Phase A baseline tree | `dd0e3a852970fb971713e145908a2a58dfcdd5ec` |
| Baseline parents | `347156108cac5d9a30189dd9615d90e8745a8850` (reviewed H-04 current-state correction) and `38cef4db1665cf8258c07200356004f8aaf6eb9d` (integrated S2 inventory correction) |
| Phase A branch | `rh-track-6-s6-track-7-h4-defaults-parameters-phase-a` |
| Phase A worktree | `/Users/wigglez/dev/ripe-protocol-track-6-s6-track-7-h4-defaults-parameters-phase-a` |
| Local `rh`, cached `origin/rh`, live `origin/rh` at kickoff | all `e39815d710ecfaf8bbeea54cabe8ae8d553a2740` |
| Kickoff worktree state | clean before this file was created |

The owner authorized Phase A from this exact `rh` tip after Phase 1
reconciliation and integration of the reviewed H-04 current-state correction.
This satisfies the brief's requirement of an explicit owner instruction naming
the exact Phase A baseline and a fresh isolated branch/worktree.

### 1.2 Controlling document identities (recomputed from this worktree)

| Controlling document | SHA-256 |
| --- | --- |
| `docs/chains/rh/track-6-s6-track-7-h4-defaults-parameters.md` | `50abd02e94c0a5af8aa45d77051ccf29ee802399f68918cee21e813c5c990aec` |
| `docs/chains/rh/evidence/robinhood-blueprint-phase-a.md` | `f1f8bf077723b08b87da6244a56ea36706c82152182e227972abe02363146d22` |
| `config/robinhood_blueprint.py` | `5bcb4dc3d6bdf77a3165926a8c4c07ad658f2b219e685105591cb6a5738a945e` |
| `docs/chains/rh/ledger-guard-implementation-record.md` | `6ce94f25f00e6924b540378f09ed1a84ce401e6474863b2eae6820437b2f847b` |
| `docs/chains/rh/ledger-guard-security-decision.md` | `15610bac4293d06320581dc1603b2980ea352af55d89f040ccab18ca26c9e739` |
| `docs/chains/rh/evidence/stock-token-m1-exact-receipt.md` | `999a9dcadf0d15332f8847e198cdf82efc32e099f31b496ecdb4f3e64b78c0eb` |
| `docs/chains/rh/track-8-m0-owner-decision-packet.md` | `9fc44e47ae98bfe8e99c6554580215150461f17182ec92094588b7e650186496` |
| `docs/chains/rh/evidence/robinhood-migration-phase-a.md` | `28c3e32b9732334c4904667eeb983d057d5d96391fb5fd8b13f37a9f5033af7c` |
| `docs/chains/rh/evidence/robinhood-manifest-phase-a.md` | `54aea0a8df18d83dc53493ba561195d432d8e7df0d057932eeed7dfe60cd7c19` |
| `docs/chains/rh/ccip-integration-decision.md` | `9b668e3b6aaba48f0ec4af60af1a3d92de4e9c190aeefadd3cc69f2afc5d1ab2` |
| `docs/chains/rh/evidence/dependency-security-gate.md` | `81baca680d8f21c309d87e83f25366ea50c8d27700cd3e0d6ea7001a1892b41c` |
| `docs/chains/rh/usdg-psm-decision.md` | `5f90fd3c4cfd35b7701b6eeddc8fa8a63c49ffd51a1f2ca52060aa8852188b52` |
| `docs/chains/rh/track-6-s3-lootbox-floor.md` | `e90daeeb79d636d7296b1f5b6320008d41ae5fe64c26e6e7fae776ebd922c7dd` |
| `docs/chains/rh/deleverage-cooldown-security-decision.md` | `98cbe896e502ad280f4b3de74e45181937b5085988dd9c6d45d2ce0e167a755b` |
| `contracts/config/DefaultsBase.vy` | `be475cce20fb66baf62fbdf3815a3e5afca1881fc5174484fd38cb508bf8e50b` |
| `contracts/config/DefaultsLocal.vy` | `01b3b3b11d2c380d93921e279dfdd2a85f8ed51704e72f3cc6124c9496f7f096` |
| `interfaces/Defaults.vyi` | `933230ff3a1c02fa91f50262e4121075d232297b8e030e8f387b5641a0aa8e3f` |
| `interfaces/ConfigStructs.vyi` | `def6208cd81de43d0d33656f9d05b5394d3a74c695fdc27ffe3c9711ccd67c2c` |
| `config/block-clock-inventory.json` | `8d4b954931ae7a3bb14a1ba4ae9108d51e01568ec42d3069f599ecee76bddf96` |

The required external architecture input,
`/Users/wigglez/dev/hightop-notes/random/hood/hood-chain-executive-summary.md`,
was present and read (723 lines).

### 1.3 Validation environment record

Two environments were used, both recorded exactly:

**(a) Active project environment** — pyenv env `ripe-lite` (CPython
3.12.0), selected by the committed `.python-version`; pins pytest `8.4.2`,
titanoboa `0.2.7`, vyper `0.4.3` (all equal to the integrated lock);
`pip check` clean. It is a deliberately slimmed environment and does **not**
contain `ipython` (the full lock pins `ipython==9.8.0` at
`requirements.txt:109`), so `tests/deployment/test_dependency_gate.py:19`
(module-level `IPython.lib.lexers` import) cannot collect there. Used for
the S1/S2/H-02(partial)/H-03/collection/full-suite runs.

**(b) Fresh private exact-lock environment** — a new CPython 3.12.0 venv
in a private mode-`0700` directory outside the repository, installed from
the exact integrated `requirements.txt` lock. Used to execute the complete
H-01 dependency gate and the complete three-file H-02 boundary. Results in
Section 13.

**Truthful environment findings (facts, not owner exceptions):**

1. **H-01 reproduces from the lock.** The dependency gate passes in the
   fresh exact-lock environment (Section 13: 45 passed). The earlier
   collection failure was an **active-environment mismatch**
   (`ripe-lite` lacking `ipython`), not a lock, repository, or
   reproducibility defect. This is recorded as the factual validation
   disposition `VD-H04-ENV` (Section 13.1); it is **not** an
   owner-exception decision, and the former `D-H04-19` decision slot is
   retired accordingly.
2. **Placeholder consumption, stated exactly.** `tests/conf_env.py:18,26`
   hard-requires an `ETHERSCAN_API_KEY` environment variable at import; a
   clearly labeled non-secret placeholder string was exported for test
   invocation. The value **is consumed**: the session fixture
   `set_etherscan` (`tests/conf_env.py:104-110`) passes it to
   `boa.set_etherscan(...)` as local Boa configuration for every `env`
   fixture use. That registration caused no RPC, no authenticated access,
   no signing, no deployment, no transaction, no secret use, and no
   external-state action: under the default `--fork=local` mode all 142
   fork-marked tests are deselected, the local path enters
   `boa.set_env(Env())` (`:195-197`), and no Etherscan or provider request
   is issued. No secret store was read.
3. **Execution context of test runs.** The earlier full-suite run executed
   as a detached background process whose `git rev-parse
   --is-inside-work-tree` probe (the skip guard at
   `tests/deployment/test_base_profile_regression.py:313-322`) did not
   report a Git worktree, so
   `test_committed_base_history_inventory_is_unchanged` was skipped with
   reason "requires a Git worktree" — an execution-context artifact of
   that run, **not** a repository, dependency, or product blocker. The
   test **passes independently in the actual candidate Git worktree**
   (Section 13). Archive/non-Git-context results are labeled as such
   wherever cited; every result in Section 13 states the context it
   actually ran in.

### 1.4 Files owned by this brief

Phase A owns exactly one new file — this document:

- `docs/chains/rh/evidence/robinhood-defaults-parameters-phase-a.md`

Conditional Phase B ownership (default proposed boundary, not authorized):

- `contracts/config/DefaultsRobinhood.vy`
- `config/robinhood-parameters.json`
- `tests/config/test_defaults_robinhood.py`
- `tests/deployment/test_network_clock_profiles.py`
- one deterministic Robinhood-only generator (preferred candidate
  `scripts/params/generate_robinhood_defaults.py`; see Section 7)
- this evidence file, updated in the same commit when an approved value,
  disposition, or generator conclusion changes.

Prohibited files are exactly those listed in the controlling brief's
"Prohibited files" section; none was modified.

### 1.5 Ownership, branch census, and collision check

At the Phase A baseline:

- none of the six Phase A/B paths above exists in any ref reachable from any
  local or remote branch (`git log --all` returns empty for every path), and
  none exists on disk in any registered worktree;
- the H-06 Phase B worktree
  (`ripe-protocol-track-7-h6-manifest-schema-phase-b`) carries uncommitted
  bytes, but its conditional eight-file ceiling is disjoint from every H-04
  path; its bytes are non-controlling and were not read;
- every other registered worktree is historical provenance for an integrated
  or separately gated track and touches no H-04-owned path;
- the H-03 blueprint surface `S-049-ARTIFACT`
  (`docs/chains/rh/evidence/robinhood-blueprint-phase-a.md:1803`) records that
  the `DefaultsRobinhood` artifact is "created only by H-04", confirming no
  competing writer.

**Collision result: none.** No parallel S6 or H-04 branch owns any file
reserved by the brief.

### 1.6 Exact S6/H-04 overlap resolution

The integrated Track 6 specification assigns S6 `DefaultsRobinhood`, its
tests, the Robinhood parameter inventory, and parameter tooling; the Track 7
deployment specification assigns H-04 the same contract and tests plus
`config/robinhood-parameters.json` and deterministic generation
(`docs/chains/rh/robinhood-deployment-support-specification.md:1664`). This
combined slice resolves that overlap exactly as the brief directs:

- the reviewed JSON manifest is the typed input and value/provenance
  authority;
- `DefaultsRobinhood.vy` is a deterministic generated or mechanically
  verified projection of approved canonical-interface fields only;
- deployment-only values remain typed manifest entries for later slices,
  never forced into the contract;
- the H-03 blueprint remains the graph/disposition authority, not a
  parameter store; and
- H-05/H-08/H-09 consume these artifacts read-only.

### 1.7 Downstream consumers

| Consumer | What it consumes |
| --- | --- |
| H-05 migration planning (Phase A integrated) | reviewed typed values and exact artifact hashes; reservation `0040` is an assertion of H-04 artifacts, never a state change (`docs/chains/rh/evidence/robinhood-migration-phase-a.md`, reservation matrix) |
| H-06 manifest protocol (Phase A integrated) | none directly; H-06's deployment/evidence manifest-v2 is a distinct authority from H-04's parameter manifest |
| H-08 post-deployment proof | expected-value assertions, including the S4 zero-cooldown pin and pending-action rejections (`docs/chains/rh/deleverage-cooldown-security-decision.md:921-942`) |
| H-09 release proof | generated artifact hashes and the clock-profile test file |
| Track 8 M5 | reviewed configuration projections for the Stock activation bundle, gated by Track 8's own approvals |

## 2. A2 — Complete `Defaults` field inventory

### 2.1 Interface census and consumption model

`interfaces/Defaults.vyi` declares exactly 17 external view selectors over the
struct vocabulary of `interfaces/ConfigStructs.vyi`. The canonical
consumption model, verified by exhaustive search:

- **Two consumers, both constructors.** `MissionControl.__init__`
  (`contracts/data/MissionControl.vy:218-253`) copies 14 selector results into
  storage; `Ledger.__init__` (`contracts/data/Ledger.vy:190-205`) copies the
  three `ripeAvailFor*` buckets. Both skip seeding entirely when the defaults
  address is empty (`MissionControl.vy:226`, `Ledger.vy:202`).
- **No runtime reads.** No storage variable anywhere holds the Defaults
  address; after construction the Defaults contract is orphaned. Every
  runtime reader targets MissionControl or Ledger (for example
  `contracts/core/Teller.vy:994` reads `MissionControl.shouldCheckLastTouch`).
- **Every field is a one-time constructor seed with a governance successor
  path.** Nothing seeded from Defaults is immutable after deployment; the
  setter authority map is in Section 2.3.
- **MissionControl does not bind setters to a specific Switchboard.** Every
  setter asserts only `addys._isSwitchboardAddr(msg.sender)`
  (`contracts/data/MissionControl.vy:263` and siblings); the
  Alpha/Bravo/Charlie/Delta/Echo split is convention enforced by which
  contract implements which entrypoint.
- **Local precedent for omission.** `contracts/config/DefaultsLocal.vy`
  returns `empty(...)` structs, empty arrays, empty addresses, and
  `shouldCheckLastTouch() == False`, proving consumers tolerate empty
  seeding. Empty-array returns are therefore a reviewed, supported posture
  where the launch graph requires it — but under this brief each such return
  must be an explicit reviewed omission, never a placeholder.

### 2.2 Field-level inventory

Robinhood dispositions below use the typed vocabulary of the required
manifest semantics: `launch_initial`, `fast_follow`,
`deployment_assertion_only`, `disabled`, `omitted`, `blocked`,
`not_applicable`, `unresolved`. A value shown as approved is approved by an
integrated cross-track authority cited in place; **no new value is selected
by this document**. Every remaining `blocked`/`unresolved` row is owned by a
decision in Section 11.

**Exact counts and completeness rule.** There are exactly **17 Defaults
selectors** and exactly **109 flattened returned fields** inside their
returned structures, counting each array's element structure once and
flattening nested structs. Per-selector field counts:

| Selector | Flattened fields | Composition |
| --- | --- | --- |
| `genConfig` | 13 | `GenConfig` 13 scalars |
| `genDebtConfig` | 21 | 16 scalars + nested `AuctionParams` 5 |
| `ripeAvailForRewards` | 1 | scalar |
| `ripeAvailForHr` | 1 | scalar |
| `ripeAvailForBonds` | 1 | scalar |
| `ripeBondConfig` | 9 | `RipeBondConfig` 9 |
| `rewardsConfig` | 9 | `RipeRewardsConfig` 9 |
| `ripeGovVaultConfigs` | 8 | entry `asset` + 2 config scalars + `LockTerms` 5 |
| `hrConfig` | 6 | `HrConfig` 6 |
| `underscoreRegistry` | 1 | address |
| `trainingWheels` | 1 | address |
| `shouldCheckLastTouch` | 1 | bool |
| `assetConfigs` | 31 | entry `asset` + 19 `AssetConfig` scalars/arrays + `DebtTerms` 6 + `AuctionParams` 5 |
| `priorityLiqAssetVaults` | 2 | `VaultLite` 2 |
| `priorityStabVaults` | 2 | `VaultLite` 2 |
| `priorityPriceSourceIds` | 1 | uint element |
| `liteSigners` | 1 | address element |
| **Total** | **109** | |

This count is mechanically checkable: parse the struct blocks of
`interfaces/ConfigStructs.vyi`, take `GenConfig=13`, `GenDebtConfig=17`
(16 scalars + 1 nested), `AuctionParams=5`, `RipeBondConfig=9`,
`RipeRewardsConfig=9`, `RipeGovVaultConfig=3` (2 scalars + 1 nested),
`LockTerms=5`, `HrConfig=6`, `AssetConfig=21` (19 scalars/arrays + 2
nested), `DebtTerms=6`, `VaultLite=2`, apply the flattening rule above, and
sum with the four scalar/element selectors. The verification performed for
this document reproduced exactly 13+21+3+9+9+8+6+3+31+4+2 = 109.

The exact flattening formula for the `assetConfigs` entry — the single
convention used by this census, the Section 2.2.11 structure trace, the
Section 6 matrix, and the 109-field total:

```text
AssetConfig:
  21 top-level fields
  minus 2 container fields (debtTerms, customAuctionParams)
  plus 6 DebtTerms leaf fields
  plus 5 AuctionParams leaf fields
  equals 30 flattened AssetConfig leaf fields

AssetConfigEntry.asset:
  plus 1

Total:
  31 flattened AssetConfigEntry fields
```

Every one of the 109 fields is represented individually in the subsections
below (assetConfigs fields are traced once at structure level here, and
receive per-asset typed statuses for all seven launch assets in Section 6,
USDG's column being `not_applicable` throughout).

**Shared trace attributes.** For every field, the selector-level attributes
are stated once per subsection: exact selector and return type
(`interfaces/Defaults.vyi`), source definition site
(`contracts/config/DefaultsBase.vy`), constructor/bootstrap read site,
destination storage field, applicable tests, and operational path. The
per-field rows then carry: unit/type, Base value with line cite
(evidence-only), post-construction mutation authority (exact setter and
timelock class), lifecycle classification, owning track, and the
blocker/decision reference where unresolved. Lifecycle vocabulary:
**seed+governed** = one-time constructor seed, later mutable via the cited
governance setter; no Defaults-seeded field is immutable after deployment.

#### 2.2.1 `genConfig() -> cs.GenConfig` (13 fields)

- Selector: `interfaces/Defaults.vyi:11`; source definition
  `contracts/config/DefaultsBase.vy:42-57`.
- Bootstrap read: `contracts/data/MissionControl.vy:227` into storage
  `MissionControl.genConfig` (`MissionControl.vy:176`) via
  `setGeneralConfig` (`:262`).
- Applicable tests: current — `tests/config/test_switchboard_alpha.py`
  (setter/authority paths), H-02/S1/S2 suites for profile and clock
  surfaces; proposed — `tests/config/test_defaults_robinhood.py` (parity),
  `tests/deployment/test_network_clock_profiles.py` (none of these 13 is
  block-denominated; `priceStaleTime` is seconds-domain under `MIXED`).
- Operational path: numeric fields change only through the timelocked
  governance action; each boolean has an immediate setter where a governor
  may enable and any MissionControl lite signer may disable
  (`_hasPermsToEnable`, `SwitchboardAlpha.vy:433`; `_setGenConfigFlag`
  `:619`, extcall `:676`).

| Field | Unit/type | Base value | Mutation authority | Lifecycle | Owner | Disposition |
| --- | --- | --- | --- | --- | --- | --- |
| `perUserMaxVaults` | count / uint256 | `5` (`DefaultsBase.vy:44`) | Alpha `setVaultLimits` (`:493`, timelocked) | seed+governed | OWN-H04 | `unresolved` → `D-H04-05` (cadence-free) |
| `perUserMaxAssetsPerVault` | count / uint256 | `15` (`:45`) | Alpha `setVaultLimits` (`:493`, timelocked) | seed+governed | OWN-H04 | `unresolved` → `D-H04-05` |
| `priceStaleTime` | seconds / uint256 | `1 * DAY_IN_SECONDS` (`:46`) | Alpha `setStaleTime` (`:514`, timelocked) | seed+governed | OWN-H04 | `unresolved` → `D-H04-08`; seconds-domain, no block conversion; reconcile with per-feed stale times and the 86,400-second heartbeats |
| `canDeposit` | bool | `True` (`:47`) | Alpha `setCanDeposit` (`:569`, immediate, lite-disable) | seed+governed | OWN-H04 | `unresolved` → `D-H04-03`; interacts with `I-TELLER-INITIAL-PAUSE` (blocked) |
| `canWithdraw` | bool | `True` (`:48`) | Alpha `setCanWithdraw` (`:574`, immediate, lite-disable) | seed+governed | OWN-H04 | `unresolved` → `D-H04-03`; sGREEN day-one withdrawals (M0 decision 6) require this `True` unless routed otherwise |
| `canBorrow` | bool | `True` (`:49`) | Alpha `setCanBorrow` (`:579`, immediate, lite-disable) | seed+governed | OWN-H04 | `unresolved` → `D-H04-03`; interacts with `D-H04-04` caps |
| `canRepay` | bool | `True` (`:50`) | Alpha `setCanRepay` (`:584`, immediate, lite-disable) | seed+governed | OWN-H04 | `unresolved` → `D-H04-03`; M5 config bundle expects `canRepay=True` at Stock activation |
| `canClaimLoot` | bool | `True` (`:51`) | Alpha `setCanClaimLoot` (`:589`, immediate, lite-disable) | seed+governed | OWN-H04 | `unresolved` → `D-H04-03`; inert while points disabled |
| `canLiquidate` | bool | `True` (`:52`) | Alpha `setCanLiquidate` (`:594`, immediate, lite-disable) | seed+governed | OWN-H04 | `unresolved` → `D-H04-03`; zero initial debt makes it inert-but-enabled unless explicitly disabled |
| `canRedeemCollateral` | bool | `True` (`:53`) | Alpha `setCanRedeemCollateral` (`:599`, immediate, lite-disable) | seed+governed | OWN-H04 | `unresolved` → `D-H04-03` |
| `canRedeemInStabPool` | bool | `True` (`:54`) | Alpha `setCanRedeemInStabPool` (`:604`, immediate, lite-disable) | seed+governed | OWN-H04 | `unresolved` → `D-H04-03` |
| `canBuyInAuction` | bool | `True` (`:55`) | Alpha `setCanBuyInAuction` (`:609`, immediate, lite-disable) | seed+governed | OWN-H04 | `unresolved` → `D-H04-03` |
| `canClaimInStabPool` | bool | `True` (`:56`) | Alpha `setCanClaimInStabPool` (`:614`, immediate, lite-disable) | seed+governed | OWN-H04 | `unresolved` → `D-H04-03` |

#### 2.2.2 `genDebtConfig() -> cs.GenDebtConfig` (21 flattened fields)

- Selector: `interfaces/Defaults.vyi:20`; source definition
  `contracts/config/DefaultsBase.vy:65-90`.
- Bootstrap read: `MissionControl.vy:228` into `MissionControl.genDebtConfig`
  (`:177`) via `setGeneralDebtConfig` (`:268`).
- Applicable tests: current — `tests/config/test_switchboard_alpha.py`;
  S2 inventory suite (BN-029, BN-030/031, CAD-001 sites); proposed — Phase B
  parity plus clock-profile coverage for the three block-denominated fields.
- Operational path: all grouped setters are governor + timelock via
  `_setPendingDebtConfig` (`SwitchboardAlpha.vy:942`) and
  `executePendingAction` (`:1477-1531`); only `setIsDaowryEnabled` is
  immediate with lite-signer disable (`:1048`, extcall `:1055`).

| Field | Unit/type | Base value | Mutation authority | Lifecycle | Owner | Disposition |
| --- | --- | --- | --- | --- | --- | --- |
| `perUserDebtLimit` | GREEN base units (18-dec) | 20,000e18 (`DefaultsBase.vy:67`) | Alpha `setGlobalDebtLimits` (`:689`, timelocked) | seed+governed | OWN-H04 | `unresolved` → `D-H04-04` (economic, not conversion) |
| `globalDebtLimit` | GREEN base units | 200,000e18 (`:68`) | Alpha `setGlobalDebtLimits` (`:689`) | seed+governed | OWN-H04 | `unresolved` → `D-H04-04` |
| `minDebtAmount` | GREEN base units | 1e18 (`:69`) | Alpha `setGlobalDebtLimits` (`:689`) | seed+governed | OWN-H04 | `unresolved` → `D-H04-04` |
| `numAllowedBorrowers` | count | 1,000 (`:70`) | Alpha `setGlobalDebtLimits` (`:689`) | seed+governed | OWN-H04 | `unresolved` → `D-H04-04` |
| `maxBorrowPerInterval` | GREEN base units | 10,000e18 (`:71`) | Alpha `setBorrowIntervalConfig` (`:714`, timelocked) | seed+governed | OWN-H04 | `unresolved` → `D-H04-04` |
| `numBlocksPerInterval` | blocks (BN-029) | `1 * DAY_IN_BLOCKS` = 43,200 (`:72`) | Alpha `setBorrowIntervalConfig` (`:714`) | seed+governed | OWN-H04 | `blocked` → `D-H04-06`; candidate 7,200 unapproved |
| `minDynamicRateBoost` | bps/10000 | 100_00 (`:73`) | Alpha `setDynamicRateConfig` (`:738`, timelocked) | seed+governed | OWN-H04 | `unresolved` → `D-H04-07` |
| `maxDynamicRateBoost` | bps/10000 | 500_00 (`:74`) | Alpha `setDynamicRateConfig` (`:738`) | seed+governed | OWN-H04 | `unresolved` → `D-H04-07` |
| `increasePerDangerBlock` | rate_per_block_1e6 (denominator 1,000,000; `contracts/core/CreditEngine.vy:182,1066-1067`) | `10` = 0.001%/danger number (`:75`) | Alpha `setDynamicRateConfig` (`:738`) | seed+governed | OWN-H04 (risk/oracle review) | `blocked` → `D-H04-07`; CAD-001; explicit inert value required; S10 display fix supplies no runtime value |
| `maxBorrowRate` | bps/10000 (rate semantics) | 100_00 (`:76`) | Alpha `setDynamicRateConfig` (`:738`) | seed+governed | OWN-H04 | `unresolved` → `D-H04-07`; economic decision, never reciprocal duration conversion |
| `maxLtvDeviation` | bps/10000 | 10_00 (`:77`) | Alpha `setMaxLtvDeviation` (`:767`, timelocked) | seed+governed | OWN-H04 | `unresolved` → `D-H04-04` |
| `keeperFeeRatio` | bps/10000 | 1_00 (`:78`) | Alpha `setKeeperConfig` (`:786`, timelocked) | seed+governed | OWN-H04 | `unresolved` → `D-H04-04` |
| `minKeeperFee` | GREEN base units | 1e18 (`:79`) | Alpha `setKeeperConfig` (`:786`) | seed+governed | OWN-H04 | `unresolved` → `D-H04-04` |
| `maxKeeperFee` | GREEN base units | 25,000e18 (`:80`) | Alpha `setKeeperConfig` (`:786`) | seed+governed | OWN-H04 | `unresolved` → `D-H04-04` |
| `isDaowryEnabled` | bool | `True` (`:81`) | Alpha `setIsDaowryEnabled` (`:1048`, immediate, lite-disable) | seed+governed | OWN-H04 | `unresolved` → `D-H04-03` |
| `ltvPaybackBuffer` | bps/10000 | 10_00 (`:82`) | Alpha `setLtvPaybackBuffer` (`:818`, timelocked) | seed+governed | OWN-H04 | `unresolved` → `D-H04-04` |
| `genAuctionParams.hasParams` | bool | `True` (`:84`) | Alpha `setGenAuctionParams` (`:837`, timelocked) | seed+governed | OWN-H04 | `unresolved` → `D-H04-10` |
| `genAuctionParams.startDiscount` | bps/10000 | 1_00 (`:85`) | Alpha `setGenAuctionParams` (`:837`) | seed+governed | OWN-H04 | `unresolved` → `D-H04-10` |
| `genAuctionParams.maxDiscount` | bps/10000 | 50_00 (`:86`) | Alpha `setGenAuctionParams` (`:837`) | seed+governed | OWN-H04 | `unresolved` → `D-H04-10` |
| `genAuctionParams.delay` | blocks (BN-030) | `0` (`:87`) | Alpha `setGenAuctionParams` (`:837`) | seed+governed | OWN-H04 | `blocked` → `D-H04-06`; zero legitimate only if reviewed (`D-H04-20`) |
| `genAuctionParams.duration` | blocks (BN-030/031) | `1 * DAY_IN_BLOCKS` (`:88`) | Alpha `setGenAuctionParams` (`:837`) | seed+governed | OWN-H04 | `blocked` → `D-H04-06`; skip-policy headroom under `D-H04-10` |

#### 2.2.3 `ripeAvailForRewards()` / `ripeAvailForHr()` / `ripeAvailForBonds()` (3 scalar fields)

- Selectors: `interfaces/Defaults.vyi:29,35,41`; source definitions
  `contracts/config/DefaultsBase.vy:98,104,110`.
- Bootstrap read: **Ledger**, not MissionControl —
  `contracts/data/Ledger.vy:203,204,205` into `Ledger.ripeAvailForRewards`
  (`:153`), `.ripeAvailForHr` (`:172`), `.ripeAvailForBonds` (`:183`).
- Applicable tests: current — `tests/config/test_switchboard_delta.py`
  (setter path) and Ledger/Lootbox/HR/BondRoom suites (runtime accounting);
  proposed — Phase B parity.
- Operational path: governor + timelock via SwitchboardDelta; runtime
  decrements by consumers; the HR bucket is also re-credited on paycheck
  cancellation.

| Field | Unit/type | Base value | Mutation authority | Lifecycle | Owner | Disposition |
| --- | --- | --- | --- | --- | --- | --- |
| `ripeAvailForRewards` | RIPE base units | 1,000e18 (`DefaultsBase.vy:99`) | Delta `setRipeAvailableForRewards` (`SwitchboardDelta.vy:956`, timelocked); runtime `-=` in `Ledger.vy:516,527-530` | seed+governed+runtime-decremented | OWN-H04 | `unresolved` → `D-H04-09`; safe-state candidate is zero/minimal while rewards disabled; zero must be typed legitimate |
| `ripeAvailForHr` | RIPE base units | 1,000e18 (`:105`) | Delta `setRipeAvailableForHr` (`:972`, timelocked); runtime `-=`/`+=` in `Ledger.vy:819,830-833` | seed+governed+runtime-adjusted | OWN-H04 | `unresolved` → `D-H04-11`; interacts with `hrConfig.maxCompensation` Base precedent `0` |
| `ripeAvailForBonds` | RIPE base units | 1,000e18 (`:111`) | Delta `setRipeAvailableForBonds` (`:988`, timelocked); runtime `-=` in `Ledger.vy:880-885` | seed+governed+runtime-decremented | OWN-H04 | `unresolved` → `D-H04-11` |

These three fields are also the allocation members of `I-LEDGER-DEFAULTS`
(H-03 symbolic input, `blocked`, owner OWN-H04, blockers `B-S5-LEDGER` and
`B-H04-PARAMS`): the Ledger constructor takes the defaults dependency
alongside the S5 action-block source; the S5 constructor discriminator
itself is **deployment-only** and never an H-04 field (Section 3, DP-04).

#### 2.2.4 `ripeBondConfig() -> cs.RipeBondConfig` (9 fields)

- Selector: `interfaces/Defaults.vyi:50`; source definition
  `contracts/config/DefaultsBase.vy:119-130`.
- Bootstrap read: `MissionControl.vy:230` into
  `MissionControl.ripeBondConfig` (`:179`) via `setRipeBondConfig` (`:280`).
- Applicable tests: current — `tests/config/test_switchboard_delta.py`,
  BondRoom suites, S2 inventory (BN-014/015/017 sites); proposed — Phase B
  parity + clock profiles for the two block fields.
- Operational path: grouped values governor + timelock; the purchase flag is
  immediate with lite-signer disable.

| Field | Unit/type | Base value | Mutation authority | Lifecycle | Owner | Disposition |
| --- | --- | --- | --- | --- | --- | --- |
| `asset` | address | Base USDC constant (`DefaultsBase.vy:121`; evidence-only) | Delta `setRipeBondConfig` (`SwitchboardDelta.vy:846`, timelocked) | seed+governed | OWN-H04 | `blocked` → `D-H04-11`; no Robinhood bond payment asset approved; Base address must never be copied |
| `amountPerEpoch` | payment-asset base units (6-dec on Base) | 2,000e6 (`:122`) | Delta `setRipeBondConfig` (`:846`) | seed+governed | OWN-H04 | `unresolved` → `D-H04-11` |
| `canBond` | bool | `False` (`:123`) | Delta `setCanPurchaseRipeBond` (`:925`, immediate, lite-disable) | seed+governed | OWN-H04 | candidate `launch_initial: False` (disabled; matches `S-013-REWARD-ACTIONS`); selection `D-H04-11` |
| `minRipePerUnit` | RIPE per payment unit (18-dec) | `0` (`:124`) | Delta `setRipeBondConfig` (`:846`) | seed+governed | OWN-H04 | `unresolved` → `D-H04-11`; zero must be typed legitimate if kept (`D-H04-20`) |
| `maxRipePerUnit` | RIPE per payment unit | 1e18 (`:125`) | Delta `setRipeBondConfig` (`:846`) | seed+governed | OWN-H04 | `unresolved` → `D-H04-11` |
| `maxRipePerUnitLockBonus` | bps/10000 | 200_00 (`:126`) | Delta `setRipeBondConfig` (`:846`) | seed+governed | OWN-H04 | `unresolved` → `D-H04-11` |
| `epochLength` | blocks (BN-014/015/017) | `8 * HOUR_IN_BLOCKS` = 14,400 (`:127`) | Delta `setRipeBondEpochLength` (`:896`, timelocked) | seed+governed | OWN-H04 | `blocked` → `D-H04-06`; candidate 2,400 unapproved |
| `shouldAutoRestart` | bool | `True` (`:128`) | Delta `setRipeBondConfig` (`:846`) | seed+governed | OWN-H04 | `unresolved` → `D-H04-11` |
| `restartDelayBlocks` | blocks (BN-017) | `0` (`:129`) | Delta `setRipeBondConfig` (`:846`) | seed+governed | OWN-H04 | `blocked` → `D-H04-06`; zero must be typed legitimate if kept (`D-H04-20`) |

#### 2.2.5 `rewardsConfig() -> cs.RipeRewardsConfig` (9 fields)

- Selector: `interfaces/Defaults.vyi:59`; source definition
  `contracts/config/DefaultsBase.vy:138-149`.
- Bootstrap read: `MissionControl.vy:231` into
  `MissionControl.rewardsConfig` (`:192`) via `setRipeRewardsConfig`
  (`:366`).
- Applicable tests: current — `tests/config/test_switchboard_alpha.py`,
  Lootbox/reward suites, S2 inventory (BN-024); proposed — Phase B parity
  (launch-disabled assertions) and clock profiles for the emission field.
- Operational path: numeric groups governor + timelock via
  `_setPendingRipeRewardsConfig` (`SwitchboardAlpha.vy:1127`); the points
  flag is immediate with lite-signer disable. The M0-frozen kill-switch
  asymmetry — points disable fast, emission-zero timelocked and already
  zero at launch — is `track-8-m0-owner-decision-packet.md:320-323`.

| Field | Unit/type | Base value | Mutation authority | Lifecycle | Owner | Disposition |
| --- | --- | --- | --- | --- | --- | --- |
| `arePointsEnabled` | bool | `True` (`DefaultsBase.vy:140`) | Alpha `setRewardsPointsEnabled` (`:1187`, immediate, lite-disable) | seed+governed | OWN-H04 (OWN-REWARDS promotion) | **approved `launch_initial: False`** (M0 decision 3) |
| `ripePerBlock` | RIPE base units per NUMBER increment (BN-024) | 75e14 = 0.0075 RIPE (`:141`) | Alpha `setRipePerBlock` (`:1070`, timelocked) | seed+governed | OWN-H04 (OWN-REWARDS promotion) | **approved `launch_initial: 0`**; nonzero is `fast_follow` under `B-REWARD-PROMOTION` → `D-H04-09` |
| `borrowersAlloc` | percentage_allocation bps/10000 | 10_00 (`:142`) | Alpha `setRipeRewardsAllocs` (`:1081`, timelocked) | seed+governed | OWN-H04 | `fast_follow`/`unresolved` → `D-H04-09`; allocation group must conserve 100_00 when enabled |
| `stakersAlloc` | percentage_allocation | 90_00 (`:143`) | Alpha `setRipeRewardsAllocs` (`:1081`) | seed+governed | OWN-H04 | `fast_follow`/`unresolved` → `D-H04-09` |
| `votersAlloc` | percentage_allocation | `0` (`:144`) | Alpha `setRipeRewardsAllocs` (`:1081`) | seed+governed | OWN-H04 | `fast_follow`/`unresolved` → `D-H04-09`; zero typed legitimate while inert |
| `genDepositorsAlloc` | percentage_allocation | `0` (`:145`) | Alpha `setRipeRewardsAllocs` (`:1081`) | seed+governed | OWN-H04 | `fast_follow`/`unresolved` → `D-H04-09` |
| `autoStakeRatio` | bps/10000 | 75_00 (`:146`) | Alpha `setAutoStakeParams` (`:1106`, timelocked) | seed+governed | OWN-H04 | `fast_follow`/`unresolved` → `D-H04-09` |
| `autoStakeDurationRatio` | bps/10000 | 33_00 (`:147`) | Alpha `setAutoStakeParams` (`:1106`) | seed+governed | OWN-H04 | `fast_follow`/`unresolved` → `D-H04-09` |
| `stabPoolRipePerDollarClaimed` | RIPE base units per dollar | 1e16 (`:148`) | Alpha `setAutoStakeParams` (`:1106`) | seed+governed | OWN-H04 | `fast_follow`/`unresolved` → `D-H04-09` |

#### 2.2.6 `ripeGovVaultConfigs() -> DynArray[cs.RipeGovVaultConfigEntry, 5]` (8 flattened fields per entry)

- Selector: `interfaces/Defaults.vyi:68`; source definition
  `contracts/config/DefaultsBase.vy:158-190` (two Base entries: RIPE and the
  RIPE/WETH LP).
- Bootstrap read: per-asset loop at `MissionControl.vy:236-238` into
  `MissionControl.ripeGovVaultConfig[asset]` (`:196`) via
  `setRipeGovVaultConfig` (`:397`).
- Applicable tests: current — `tests/config/test_switchboard_alpha.py`,
  RipeGov vault suites, S2 inventory (BN-008/BN-009); proposed — Phase B
  parity + clock profiles for the two lock-duration fields.
- Operational path: governor + timelock; validation hard-codes vault id 2 as
  the governance vault (`SwitchboardAlpha.vy:1417`).

| Field | Unit/type | Base value | Mutation authority | Lifecycle | Owner | Disposition |
| --- | --- | --- | --- | --- | --- | --- |
| entry `asset` | address (symbolic `I-RIPE` / `I-RIPE-WETH-LP` identity) | RIPE and vAMM-RIPE/WETH constants (`DefaultsBase.vy:162,177`; evidence-only) | Alpha `setRipeGovVaultConfig` (`:1359`, timelocked) | seed+governed | OWN-H04 (identities OWN-H05 / OWN-H04) | RIPE entry `launch_initial` structurally (M0 decision 8), identity `blocked` → `B-H05-PLAN`, `B-SECOPS-HANDOFF` (per `I-RIPE`); LP entry `blocked` → `B-LP-ARTIFACTS`, `B-ORACLE-FREEZE` (per `I-RIPE-WETH-LP`), never copied from Base |
| `config.lockTerms.minLockDuration` | blocks (BN-008/009) | `1 * DAY_IN_BLOCKS` (`:165,180`) | same setter | seed+governed | OWN-H04 | `blocked` → `D-H04-06` |
| `config.lockTerms.maxLockDuration` | blocks (BN-008/009) | `3 * YEAR_IN_BLOCKS` = 47,304,000 (`:166,181`) | same | seed+governed | OWN-H04 | `blocked` → `D-H04-06`; candidate 7,884,000 unapproved |
| `config.lockTerms.maxLockBoost` | bps/10000 | 200_00 (`:167,182`) | same | seed+governed | OWN-H04 | `unresolved` → `D-H04-10` |
| `config.lockTerms.canExit` | bool | `True` (`:168,183`) | same | seed+governed | OWN-H04 | `unresolved` → `D-H04-10` |
| `config.lockTerms.exitFee` | bps/10000 | 80_00 (`:169,184`) | same | seed+governed | OWN-H04 | `unresolved` → `D-H04-10` |
| `config.assetWeight` | bps/10000 | 100_00 / 150_00 (`:171,186`) | same | seed+governed | OWN-H04 | `unresolved` → `D-H04-10` |
| `config.shouldFreezeWhenBadDebt` | bool | `True` (`:172,187`) | same | seed+governed | OWN-H04 | `unresolved` → `D-H04-10` |

#### 2.2.7 `hrConfig() -> cs.HrConfig` (6 fields)

- Selector: `interfaces/Defaults.vyi:77`; source definition
  `contracts/config/DefaultsBase.vy:198-206`.
- Bootstrap read: `MissionControl.vy:229` into `MissionControl.hrConfig`
  (`:178`) via `setHrConfig` (`:274`).
- Applicable tests: current — `tests/config/test_switchboard_delta.py`, HR
  suites, S2 seconds-domain records (TS-002); proposed — Phase B parity and
  the `MIXED` seconds/NUMBER separation profile.
- Operational path: all governor + timelock via `_setPendingHrConfig`
  (`SwitchboardDelta.vy:710`).

| Field | Unit/type | Base value | Mutation authority | Lifecycle | Owner | Disposition |
| --- | --- | --- | --- | --- | --- | --- |
| `contribTemplate` | address | Base constant `CONTRIB_TEMPLATE` (`DefaultsBase.vy:27,200`; evidence-only) | Delta `setContributorTemplate` (`SwitchboardDelta.vy:648`, timelocked) | seed+governed | OWN-H04 (identity OWN-SECOPS) | `blocked` → `D-H04-11`; no Robinhood contributor-template identity exists; HR is a required inert topology artifact (HQ row 15) |
| `maxCompensation` | GREEN base units | `0` — "set this later" (`:201`) | Delta `setMaxCompensation` (`:660`, timelocked) | seed+governed | OWN-H04 | candidate `launch_initial: 0` (legitimate zero, HR inert) → `D-H04-11`, `D-H04-20` |
| `minCliffLength` | seconds (TS-002) | `1 * WEEK_IN_SECONDS` (`:202`) | Delta `setMinCliffLength` (`:672`, timelocked) | seed+governed | OWN-H04 | `unresolved` → `D-H04-08`; no block conversion |
| `maxStartDelay` | seconds (TS-002) | `3 * MONTH_IN_SECONDS` (`:203`) | Delta `setMaxStartDelay` (`:684`, timelocked) | seed+governed | OWN-H04 | `unresolved` → `D-H04-08` |
| `minVestingLength` | seconds (TS-002) | `1 * WEEK_IN_SECONDS` (`:204`) | Delta `setVestingLengthBoundaries` (`:696`, timelocked) | seed+governed | OWN-H04 | `unresolved` → `D-H04-08` |
| `maxVestingLength` | seconds (TS-002) | `10 * YEAR_IN_SECONDS` (`:205`) | Delta `setVestingLengthBoundaries` (`:696`) | seed+governed | OWN-H04 | `unresolved` → `D-H04-08` |

#### 2.2.8 `underscoreRegistry() -> address` (1 field)

| Attribute | Value |
| --- | --- |
| Selector / source | `interfaces/Defaults.vyi:86`; `contracts/config/DefaultsBase.vy:214-215` (constant `:29`) |
| Bootstrap read → storage | `MissionControl.vy:232` → `MissionControl.underscoreRegistry` (`:207`) via `setUnderscoreRegistry` (`:503`) |
| Mutation authority | Delta `setUnderscoreRegistry` (`SwitchboardDelta.vy:1009`, timelocked, interface-probed `:1028`) |
| Runtime readers | `PriceDesk.vy:333`, `AuctionHouse.vy:1375`, `EndaomentPSM.vy:708,724` (via MissionControl, never Defaults) |
| Applicable tests | current — Delta suite, PSM suites; proposed — Phase B parity zero assertion; H-08 live assertion + pending-action rejection |
| Lifecycle / unit | seed+governed; address |
| Owner | OWN-H04 (posture from M0 decision 11) |
| Disposition | **Approved `launch_initial: empty(address)`** — legitimate typed zero (`D-H04-20`); Underscore omitted at launch; `DefaultsRobinhood.underscoreRegistry()` must return zero and MissionControl must be asserted zero before each PSM enablement (`usdg-psm-decision.md:277-286`); governed mutable state with monitoring obligation, not a code invariant; H-08 owns the live proof (`deleverage-cooldown-security-decision.md:921-942`) |

#### 2.2.9 `trainingWheels() -> address` (1 field)

| Attribute | Value |
| --- | --- |
| Selector / source | `interfaces/Defaults.vyi:95`; `contracts/config/DefaultsBase.vy:223-224` (constant `:28`) |
| Bootstrap read → storage | `MissionControl.vy:233` → `MissionControl.trainingWheels` (`:208`) via `setTrainingWheels` (`:494`) |
| Mutation authority | Charlie `setTrainingWheels` (`SwitchboardCharlie.vy:860`, timelocked); allowlist contents separately via Charlie `setManyTrainingWheelsAccess` (`:880`, governor, no timelock) |
| Runtime reader | `SwitchboardBravo.vy:473` (whitelist comparison) |
| Applicable tests | current — `tests/config/test_training_wheels.py`, Charlie suite; proposed — Phase B parity (symbolic binding only) |
| Lifecycle / unit | seed+governed; address |
| Owner | OWN-H04 (`I-TRAINING-WHEELS`; authority handoff OWN-SECOPS) |
| Disposition | **`blocked`** → `B-H04-PARAMS` + `B-SECOPS-HANDOFF` (`I-TRAINING-WHEELS`, deadline "before testnet"); H-03 surface `S-006-ALLOWLIST` blocked; requires a Robinhood TrainingWheels deployment referenced by `DefaultsRobinhood`, never copied Base addresses (`robinhood-deployment-support-specification.md:1044`); policy shape in `D-H04-15` |

#### 2.2.10 `shouldCheckLastTouch() -> bool` (1 field)

| Attribute | Value |
| --- | --- |
| Selector / source | `interfaces/Defaults.vyi:104`; `contracts/config/DefaultsBase.vy:232-233` |
| Bootstrap read → storage | `MissionControl.vy:234` → `MissionControl.shouldCheckLastTouch` (`:209`) via `setShouldCheckLastTouch` (`:521`) |
| Mutation authority | Delta `setShouldCheckLastTouch` (`SwitchboardDelta.vy:1046`, timelocked) |
| Runtime reader | `Teller.vy:994` (housekeeping guard arm/check) |
| Applicable tests | current — S5 matrix suites (`tests/data/test_ledger_action_block.py`, Teller action-block tests); proposed — Phase B parity `True` assertion |
| Lifecycle / unit | seed+governed; bool |
| Owner | OWN-H04 (policy fixed by integrated S5) |
| Disposition | **Approved `launch_initial: True`** — disabling as the selected Robinhood policy is an explicitly prohibited path (`track-6-s5-ledger-guard.md:747`; `ledger-guard-security-decision.md:318`); the Boolean controls only the equality assertion, every housekeeping call still writes `lastTouch`; no S5 source, constructor, ABI, or deployment input is inferred here (Section 3, DP-04) |

#### 2.2.11 `assetConfigs() -> DynArray[cs.AssetConfigEntry, 50]` (31 flattened fields per entry)

- Selector: `interfaces/Defaults.vyi:113`; source definition
  `contracts/config/DefaultsBase.vy:240-1230` (24 Base entries,
  evidence-only).
- Bootstrap read: `MissionControl.vy:241-243` → internal `_setAssetConfig`
  (`:297`), which also registers the asset (`_registerAsset` `:310`) and
  accumulates `totalPointsAllocs` (`:375`); destination storage
  `MissionControl.assetConfig[asset]` (`:182`) plus registration fields
  (`:183-185`).
- Applicable tests: current — `tests/config/test_switchboard_bravo.py`,
  `tests/config/test_switchboard_charlie.py`, vault/credit/auction suites;
  proposed — Phase B parity + the Section 6.1 matrix proofs.
- Operational path: full-structure changes via Bravo governor + timelock
  (`addAsset` `SwitchboardBravo.vy:223`, `setAssetDepositParams` `:349`,
  `setAssetLiqConfig` `:411`, `setAssetDebtTerms` `:501`,
  `setWhitelistForAsset` `:574`, all through `_setPendingAssetConfig`
  `:597`); six per-asset boolean flags via Charlie immediate setters with
  lite-signer disable (exact setters cited per row); removal via Charlie
  `deregisterAsset` (`:899`, timelocked) → MissionControl `deregisterAsset`
  (`:318`).

Structure-level trace (per entry; the per-asset typed statuses for all
seven launch assets are the Section 6 matrix):

| Field | Unit/type | Mutation authority | Owner | Structural disposition |
| --- | --- | --- | --- | --- |
| entry `asset` | address (symbolic identity) | Bravo `addAsset` (`:223`) / Charlie `deregisterAsset` (`:899`) | OWN-H04 / OWN-T8 for Stock | `blocked` — per-identity exact blockers: GREEN/RIPE `B-H05-PLAN` + `B-SECOPS-HANDOFF`; sGREEN `B-H05-PLAN`; both LPs `B-LP-ARTIFACTS` + `B-ORACLE-FREEZE`; AAPL `B-T8-FREEZE` (Section 12.2 rows) |
| `vaultIds` | registry_id list (VaultBook) | Bravo `setAssetDepositParams` (`:349`, timelocked) | OWN-H04; Stock vault ID OWN-T8/Track 7 | `blocked` → vault IDs unapproved (`B-H04-STOCK`, VaultBook rows) |
| `stakersPointsAlloc` | percentage_allocation bps/10000 | Bravo `setAssetDepositParams` (`:349`) | OWN-H04 | `fast_follow`/`unresolved` → `D-H04-09`; inert while points disabled; group must conserve |
| `voterPointsAlloc` | percentage_allocation | same | OWN-H04 | same |
| `perUserDepositLimit` | asset base units | same | OWN-H04 / OWN-T8 for AAPL | `blocked`/`unresolved` → `D-H04-13`; AAPL integers `B-H04-STOCK` (DP-10) |
| `globalDepositLimit` | asset base units | same | same | same |
| `minDepositBalance` | asset base units | same | OWN-H04 | `unresolved` → `D-H04-13` |
| `debtTerms.ltv` | bps/10000 | Bravo `setAssetDebtTerms` (`:501`, timelocked) | OWN-H04 (risk) | LP rows **approved explicit 0**; others `unresolved` → `D-H04-13` |
| `debtTerms.redemptionThreshold` | bps/10000 | same | OWN-H04 | LP rows explicit 0; others `unresolved` |
| `debtTerms.liqThreshold` | bps/10000 | same | OWN-H04 | same |
| `debtTerms.liqFee` | bps/10000 | same | OWN-H04 | same |
| `debtTerms.borrowRate` | bps/10000 | same | OWN-H04 | same |
| `debtTerms.daowry` | bps/10000 | same | OWN-H04 | same |
| `shouldBurnAsPayment` | bool | Bravo `setAssetLiqConfig` (`:411`, timelocked) | OWN-H04 | per-asset, Section 6 |
| `shouldTransferToEndaoment` | bool | same | OWN-H04 | per-asset, Section 6 |
| `shouldSwapInStabPools` | bool | same | OWN-H04 / OWN-T8 for Stock | Stock **approved explicit False** (M0 decision 8); others Section 6 |
| `shouldAuctionInstantly` | bool | same | OWN-H04 | per-asset, Section 6 |
| `canDeposit` | bool | Charlie `setCanDepositAsset` (`SwitchboardCharlie.vy:1184`, immediate, lite-disable) | OWN-H04 | per-asset, Section 6 |
| `canWithdraw` | bool | Charlie `setCanWithdrawAsset` (`:1189`, immediate, lite-disable) | OWN-H04 | per-asset, Section 6 |
| `canRedeemCollateral` | bool | Charlie `setCanRedeemCollateralAsset` (`:1209`, immediate, lite-disable) | OWN-H04 | per-asset, Section 6 |
| `canRedeemInStabPool` | bool | Charlie `setCanRedeemInStabPoolAsset` (`:1194`, immediate, lite-disable) | OWN-H04 | per-asset, Section 6 |
| `canBuyInAuction` | bool | Charlie `setCanBuyInAuctionAsset` (`:1199`, immediate, lite-disable) | OWN-H04 | per-asset, Section 6 |
| `canClaimInStabPool` | bool | Charlie `setCanClaimInStabPoolAsset` (`:1204`, immediate, lite-disable) | OWN-H04 | per-asset, Section 6 |
| `specialStabPoolId` | registry_id (VaultBook) | Bravo `setAssetLiqConfig` (`:411`) | OWN-H04 | `blocked` → `B-H04-PARAMS` (`I-STABILITY-CONFIG` binding; named in the H-03 blocker text) |
| `customAuctionParams.hasParams` | bool | Bravo `setAssetLiqConfig` (`:411`) | OWN-H04 | per-asset, Section 6; Base precedent all-inert (`hasParams=False`) |
| `customAuctionParams.startDiscount` | bps/10000 | same | OWN-H04 | per-asset, Section 6 |
| `customAuctionParams.maxDiscount` | bps/10000 | same | OWN-H04 | per-asset, Section 6 |
| `customAuctionParams.delay` | blocks (inert while `hasParams=False`; invisible to the cadence scanner — Phase B must enumerate from the struct) | same | OWN-H04 | per-asset, Section 6 |
| `customAuctionParams.duration` | blocks (same caveat) | same | OWN-H04 | per-asset, Section 6 |
| `whitelist` | address | Bravo `setWhitelistForAsset` (`:574`, timelocked) | OWN-H04 | per-asset, Section 6; Base precedent `empty(address)` |
| `isNft` | bool | Bravo `addAsset` group | OWN-H04 | per-asset, Section 6; `isNft=False` applies only to the six assets that may receive `AssetConfig` entries; USDG receives no ordinary `AssetConfig` entry, so USDG `isNft` is `not_applicable` |

#### 2.2.12 `priorityLiqAssetVaults()` / `priorityStabVaults() -> DynArray[cs.VaultLite, 20]` (2 fields per element, per list)

- Selectors: `interfaces/Defaults.vyi:122,128`; source definitions
  `contracts/config/DefaultsBase.vy:1237-1250,1255-1259` (evidence-only).
- Bootstrap read: `MissionControl.vy:246,247` →
  `MissionControl.priorityLiqAssetVaults` (`:197`) /
  `.priorityStabVaults` (`:198`) via setters `:416,425`.
- Applicable tests: current — Alpha suite (sanitization
  `SwitchboardAlpha.vy:1255`), liquidation/stability suites; proposed —
  Phase B parity + deterministic-ordering test.
- Operational path: governor + timelock.

| Field | Unit/type | Mutation authority | Lifecycle | Owner | Disposition |
| --- | --- | --- | --- | --- | --- |
| element `vaultId` (both lists) | registry_id (VaultBook) | Alpha `setPriorityLiqAssetVaults` (`:1209`) / `setPriorityStabVaults` (`:1232`), timelocked | seed+governed | OWN-H04 | `blocked` → `D-H04-14`; Track 7-owned vault IDs unapproved |
| element `asset` (both lists) | address (symbolic identity) | same | seed+governed | OWN-H04 | `blocked` → `D-H04-14`; each referenced asset identity carries its own exact H-03 blockers (GREEN/RIPE `B-H05-PLAN` + `B-SECOPS-HANDOFF`; sGREEN `B-H05-PLAN`; LPs `B-LP-ARTIFACTS` + `B-ORACLE-FREEZE`; Section 12.2 rows); structural candidates: liquidation list empty-or-ordinary-only (no Stock, no LP borrowing power); stability list only GREEN Stability Pool entries per VaultBook row 1 with Stock exclusions |

#### 2.2.13 `priorityPriceSourceIds() -> DynArray[uint256, 10]` (1 element field)

| Attribute | Value |
| --- | --- |
| Selector / source | `interfaces/Defaults.vyi:134`; `contracts/config/DefaultsBase.vy:1264-1265` (Base `[1, 8, 2, 9, 4, 5]`, evidence-only) |
| Bootstrap read → storage | `MissionControl.vy:248` → `MissionControl.priorityPriceSourceIds` (`:206`) via `:512` |
| Mutation authority | Alpha `setPriorityPriceSourceIds` (`SwitchboardAlpha.vy:1277`, timelocked, sanitized `:1298`) |
| Applicable tests | current — Alpha suite, PriceDesk suites; proposed — Phase B parity |
| Lifecycle / unit | seed+governed; registry_id elements (PriceDesk) |
| Owner | OWN-H04 |
| Disposition | `unresolved` → `D-H04-14`; the integrated PriceDesk expectation is Chainlink at ID 1 with IDs 2-5 empty reserved (`robinhood-blueprint-phase-a.md:2566-2576`), so the only structurally valid launch candidate is exactly `[1]`; the Base list references source IDs that do not exist on Robinhood and must be schema-rejected |

#### 2.2.14 `liteSigners() -> DynArray[address, 10]` (1 element field)

| Attribute | Value |
| --- | --- |
| Selector / source | `interfaces/Defaults.vyi:143`; `contracts/config/DefaultsBase.vy:1272-1276` (two Base signer addresses, evidence-only) |
| Bootstrap read → storage | `MissionControl.vy:251-253` → `_addLiteSigner` (`:454`) into `liteSigners`/`indexOfLiteSigner`/`numLiteSigners` (`:201-203`) via `setCanPerformLiteAction` (`:436`) |
| Mutation authority | Alpha `setCanPerformLiteAction` (`SwitchboardAlpha.vy:1333`): **revoke immediate** (`:1340`), **grant timelocked** (`OTHER_CAN_PERFORM_LITE_ACTION`, `:1588-1591`) |
| Applicable tests | current — Alpha suite, lite-action authority tests; proposed — Phase B parity + drift rejection |
| Lifecycle / unit | seed+governed (asymmetric); address elements |
| Owner | OWN-H04 (identities OWN-SECOPS under `B-SECOPS-HANDOFF`) |
| Disposition | `blocked` → `D-H04-15`; lite signers hold disable-only emergency powers (reward points, asset flags, bond purchases, PSM pause), so an empty launch array is viable only if the owner accepts losing the fast-disable path at launch — stated in `D-H04-15`, not decided here. Drift precedent: the Base generator emits an empty list while the committed artifact carries two addresses — exactly the drift class Phase B parity tests must reject |

### 2.3 Setter-authority summary (trace complete for all 17 selectors)

| Config family | Owning Switchboard (by convention) | Timelocked? | Lite-signer power |
| --- | --- | --- | --- |
| genConfig numerics | Alpha | yes | none |
| genConfig / asset booleans | Alpha / Charlie | no (immediate) | disable only |
| genDebtConfig (all but daowry flag) | Alpha | yes | none |
| `isDaowryEnabled`, `setRewardsPointsEnabled`, `setCanPurchaseRipeBond` | Alpha/Delta | no | disable only |
| ripeAvail buckets | Delta | yes | none |
| ripeBondConfig, hrConfig, underscoreRegistry, shouldCheckLastTouch | Delta | yes | none |
| rewardsConfig numerics | Alpha | yes | none |
| ripeGovVaultConfigs, priority lists, liteSigners (grant) | Alpha | yes | none (revoke immediate) |
| assetConfig structures | Bravo | yes | none |
| trainingWheels pointer | Charlie | yes | none |
| TrainingWheels allowlist contents | Charlie | no | none (governor only) |

Timelock bounds themselves are per-contract constructor inputs
(`I-CLOCK-PARAMS`, `I-ECHO-TIMELOCKS`, `I-HR-TIMELOCKS`,
`I-CHAINLINK-TIMELOCKS`) — deployment-only block-denominated values in
Section 3, not Defaults fields.

## 3. A3 — Deployment-only parameter inventory

Values needed by H-05/H-08/H-09 that are **not** `Defaults` fields. Forcing
any of these into the contract or interface is prohibited by the brief's
minimum-change rules.

| # | Deployment-only input | Controlling authority | Status | Owner / blocker |
| --- | --- | --- | --- | --- |
| DP-01 | S3 Lootbox immutable floor `7_200` (constructor `_minUnderscoreSendInterval`) | S3 final owner approval 2026-07-23 (`track-6-s3-lootbox-floor.md:82,95-98`); constructor interface at `:350` | **approved, final** | S6/H-04 carries it as a typed constructor input; the S3 cadence basis is approved for this isolated floor only |
| DP-02 | S3 initial governed `underscoreSendInterval = 0` (disabled posture) | `track-6-s3-lootbox-floor.md:312,404`; owner retention decision (`minimal-contract-change-reassessment.md:115-122`) | **approved** | legitimate zero; later enablement bounded by the immutable floor |
| DP-03 | S4 `deleverageCooldown` expected live value, exact integer `0` | S4 closure (`deleverage-cooldown-security-decision.md:907-919`) | **approved `deployment_assertion_only`** | manifest pins the expected value verbatim with the required statement "activation requires reopening S4"; the live proof and pending-action rejections are H-08-owned (`:921-942`); no Defaults field, constructor argument, or setter may be added (`:901-905`) |
| DP-04 | S5 Ledger action-block source constructor discriminator (zero = native; exact `0x64` = ArbSys child-block identity) | Integrated S5 implementation record (`ledger-guard-implementation-record.md:104-118`) | **approved semantics; deployment binding `blocked`** | the Robinhood deployment passes the exact `0x64` discriminator per integrated source semantics; the concrete deployment transaction input, address environment proof, and live verification remain S5/H-05/H-08-owned (`B-S5-LEDGER`); H-04 must not infer any further S5 input |
| DP-05 | Registry/action timelock bounds per governed contract (RipeHq, Switchboard family, PriceDesk, VaultBook, HR, Echo) | `I-CLOCK-PARAMS` (blocker `B-H04-PARAMS`), `I-ECHO-TIMELOCKS` (`B-H04-PARAMS`), `I-HR-TIMELOCKS` (`B-H04-PARAMS`, deferred), `I-CHAINLINK-TIMELOCKS` (`B-H04-PARAMS` + `B-ORACLE-FREEZE`) — all owner OWN-H04; S7 owns lifecycle validation (reservation `0050`) | `blocked` | block-denominated; cadence gate `D-H04-06` plus per-class bounds `D-H04-08`; Base registry delay precedent about 12h is comparison evidence only |
| DP-06 | Action expiry / headroom rules (TimeLock `_isExpired`, `contracts/modules/TimeLock.vy:137`) | S6 clock spec + `D-H04-08` | `blocked` | must be stress-tested under jump profiles (Section 5); expiry headroom must survive `+60` jumps without silently expiring pending actions |
| DP-07 | PSM staging constants: constructor `canMint=false`, `canRedeem=false`, `shouldAutoDeposit=true` then mandatory timelocked `setPsmShouldAutoDeposit(false)`; yield fields exactly `(0, zero)` | USDG decision (`usdg-psm-decision.md:236-254,336`) | **approved architecture invariants** | `S-048-AUTO-DEPOSIT` disabled→pre-activation configuration; auto-deposit false is an invariant, not a tunable |
| DP-08 | PSM fees, interval caps, `numBlocksPerInterval`, allowlists, reserve funding amount | USDG decision — "no numeric production fee or capacity was approved" (`usdg-psm-decision.md:323`); provisional interval `7_200` explicitly not accepted (`:529`); `I-PSM-CONFIG` (owner OWN-H04, blockers `B-H04-PARAMS` + `B-PSM-SEQUENCE`) | `blocked` | `D-H04-12`; caps derive from an owner loss/exposure envelope; interval closes under the shared clock spec (BN-027/BN-028) |
| DP-09 | PSM ordered activation sequence (redemption-first, GREEN mint authority last, canary steps, final capability-tuple mutation) | USDG decision (`usdg-psm-decision.md:343-405`); H-03 `D-H03-006` six-step global-mint order (`robinhood-blueprint-phase-a.md:2693-2714`) | **approved sequence; execution `blocked`** | `B-PSM-SEQUENCE` (H-05 co-owned); H-04 records the sequence as typed manifest gates only |
| DP-10 | AAPL exposure targets `$5,000` per-user / `$25,000` global; conversion `capAtomic = floor(D * 10^(18+8) / P8)`, round down; review at >110% drift or 7 days | M0 decision 12 (`track-8-m0-owner-decision-packet.md:170-176,192-205`) | **approved formula; integers `blocked`** | `B-T8-FREEZE`; final freeze price and fixed 18-dec cap integers are typed blockers until the pre-activation freeze |
| DP-11 | Stock asset routes and disabled controls (one enabled vault, no trusted/Department routes, Stability/CreditRedeem exclusions, atomic M1-M5 activation bundle) | M0 decisions 12-14; integrated M1 exact receipt; M5 config bundle (`stock-token-vault-change-validation-plan.md:2270-2284`) | **approved constraints; values `blocked`** | `B-T8-M1` (integrated implementation, blocker remains open pending its official Phase B lifecycle), `B-T8-M2`, `B-T8-M3`, `B-T8-M4`, `B-T8-M5`; vault artifact and Track 7-owned VaultBook ID unapproved |
| DP-12 | Complete owner-closed M0 launch graph (AAPL, GREEN, RIPE, chain-native sGREEN, canonical USDG, GREEN/USDG LP, RIPE/WETH LP) with per-asset route/activation/disabled/blocked distinctions | M0 packet Section 8 rows 1-14 | **approved graph** | Section 6 carries the full matrix; all identities symbolic: `I-GREEN`/`I-RIPE` (owner OWN-H05, blockers `B-H05-PLAN` + `B-SECOPS-HANDOFF`), `I-SGREEN` (OWN-H05, `B-H05-PLAN`), `I-USDG` (OWN-T8, `B-H05-PLAN`), `I-WETH` (OWN-H04, `B-H05-PLAN`), `I-GREEN-USDG-LP`/`I-RIPE-WETH-LP` (OWN-H04, `B-LP-ARTIFACTS` + `B-ORACLE-FREEZE`), `I-AAPL-TOKEN` (OWN-T8, `B-T8-FREEZE`) |
| DP-13 | GREEN Stability Pool and RIPE governance-vault launch-active inputs | M0 decision 8; VaultBook rows 1-2; `I-STABILITY-CONFIG` (owner OWN-H04, blockers `B-H04-PARAMS` + `B-T8-M5`); `I-RIPE-GOV-CONFIG` (owner OWN-H04, blocker `B-H04-PARAMS`) | **approved participation; values `blocked`** | `D-H04-13`; `specialStabPoolId` binding open under `B-H04-PARAMS`; Stock-exclusion enforcement tied to `B-T8-M5` |
| DP-14 | GREEN/USDG LP and RIPE/WETH LP deposit-only inputs, explicit legitimate `ltv=0`; unproved DEX/factory/pool/oracle/artifact/address inputs | M0 decision 9; `S-024-LP-ZERO-LTV` | **`ltv=0` approved; artifacts `blocked`** | `B-LP-ARTIFACTS` (OWN-H04 co-owned) — a hard launch stop until closed |
| DP-15 | Reward initial state (`arePointsEnabled=false`, `ripePerBlock=0`) and separately reviewed fast-follow activation | M0 decision 3; `P-REWARDS-SEVEN-DAY` | **initial approved; promotion `blocked`** | `B-REWARD-PROMOTION`; elapsed time never promotes |
| DP-16 | GREEN/RIPE CCIP disabled-at-launch, within-seven-day separately reviewed promotion; permanent sGREEN no-CCIP rule; provisional HQ/23-24 reservations carry no artifact/address/capability | M0 decision 2; `P-CCIP-SEVEN-DAY`; CCIP reference decision (non-production) | **approved posture** | `B-T1-CCIP`, `B-T1-TOOLCHAIN`; no pool ID, address, role, route, or capability value enters this slice |
| DP-17 | External price-source stale times and priorities (global + per-feed; both integrated feeds publish 86,400-second heartbeats) | USDG decision (`usdg-psm-decision.md:334`); M0 feed freeze facts; `I-CHAINLINK-TIMELOCKS` (blockers `B-H04-PARAMS` + `B-ORACLE-FREEZE`); `I-CHAINLINK-CORE` (owner OWN-ORACLE, blocker `B-ORACLE-FREEZE`) | `blocked` | `D-H04-08`; zero effective stale time is a hard manifest reject; ceiling policy owner-approved |
| DP-18 | Role, signer, and TrainingWheels symbolic inputs (deployer handoff, governance/Safe path, guardian scope, lite actors, TrainingWheels target and allowlist) | `ROLE-G` (`robinhood-deployment-support-specification.md:1021`); `I-TRAINING-WHEELS` (owner **OWN-H04**, blockers `B-H04-PARAMS` + `B-SECOPS-HANDOFF`); `I-GOV-HANDOFF` (owner OWN-SECOPS, blocker `B-SECOPS-HANDOFF`) | `blocked` | TrainingWheels policy/binding is H-04-owned under `B-H04-PARAMS` with handoff under `B-SECOPS-HANDOFF`; other role/signer identities under `B-SECOPS-HANDOFF`; symbolic only, never concrete addresses in this slice |
| DP-19 | Token constructor initial supplies (GREEN/RIPE/sGREEN quantities) | `I-GREEN-INITIAL-SUPPLY`, `I-RIPE-INITIAL-SUPPLY`, `I-SGREEN-INITIAL-SUPPLY` (all owner OWN-H04, blocker `B-H04-PARAMS`); recipients `I-GREEN-INITIAL-SUPPLY-RECIPIENT`, `I-RIPE-INITIAL-SUPPLY-RECIPIENT`, `I-SGREEN-INITIAL-SUPPLY-RECIPIENT` (owner OWN-SECOPS, blocker `B-SECOPS-HANDOFF`) | `blocked` | `D-H04-16`; quantities are H-04-owned manifest entries; recipients are SecOps-owned |
| DP-20 | Teller constructor `_shouldPause` launch-safety state | `I-TELLER-INITIAL-PAUSE` (owner OWN-H04, status blocked, blockers `B-H04-PARAMS` + `B-H05-PLAN`; `robinhood-blueprint-phase-a.md:1781`) | `blocked` | `D-H04-03`; must not be inferred from asset settings or defaulted |
| DP-21 | Endaoment WETH/native metadata | `I-ENDAOMENT-NATIVE-METADATA` (owner OWN-H04, blockers `B-H04-PARAMS` + `B-H05-PLAN`, deadline before Endaoment deployment) | `blocked` | `D-H04-16`; `B-H05-PLAN` gates the deployment-plan binding; identity symbolic (chain-operator-listed WETH is M0-frozen as LP constituent only) |
| DP-22 | BondBooster constructor bounds (`maxBoostRatio`, `maxUnits`, `minLockDuration`) | `I-BOND-BOOSTER-CONFIG` (owner OWN-H04, status deferred, blockers `B-H04-PARAMS` + `B-REWARD-PROMOTION`, deadline before any bond release); BondBooster constructor (`contracts/config/BondBooster.vy:53-66`) | `blocked`/`deferred` | `D-H04-11`; `B-REWARD-PROMOTION` gates any bond release; `minLockDuration` is block-denominated (cadence gate, BN-032) |

No exact address or unreviewed value is assigned anywhere above. The M0
product graph is controlling; future addresses, runtime hashes,
vault/registry selections, freeze-time cap integers, and post-deployment
facts remain typed blockers until their later gates close.

## 4. A4 — Initial launch versus fast follow

### 4.1 Phase classification

Every field or action carries exactly one phase from the required vocabulary.

| Phase | Members |
| --- | --- |
| `deployed initial value` | All approved launch-state values: rewards `arePointsEnabled=False` and `ripePerBlock=0`; `underscoreRegistry=empty`; `shouldCheckLastTouch=True`; S3 floor `7_200` with governed interval `0`; every other Defaults field once its owner decision closes with a `launch_initial` status |
| `pre-activation configuration` | PSM disabled staging: timelocked `setPsmShouldAutoDeposit(false)`, fees/caps/interval/allowlists confirmation, yield `(0, zero)` reassertion (DP-07/DP-08); the six-step global-mint tuple configuration while `setMintingEnabled(False)` holds (DP-09); MissionControl production values behind `S-009-VALUES` |
| `atomic Stock activation` | The complete M1+M2+M3+M4-proof+M5 group: AAPL asset row, cap integers, vault/VaultBook ID, route disables, one reviewed transaction sequence (DP-10/DP-11); nothing in it may be reachable earlier |
| `within-seven-day separately reviewed CCIP promotion` | GREEN and RIPE CCIP capabilities, pool artifacts, registration (`P-CCIP-SEVEN-DAY`; six surfaces); disabled continuously until the promotion review closes |
| `within-seven-day separately reviewed reward activation` | `arePointsEnabled=True`, nonzero `ripePerBlock`, live allocation set, auto-stake parameters, stability-pool claim rate (`P-REWARDS-SEVEN-DAY`; seven surfaces) |
| `post-launch release` | Additional Stock Tokens (token-specific evidence); Base cutover (separate proposal); any BondRoom/HR enablement beyond the launch posture if the owner defers them |
| `omitted` | Underscore integration and registry value semantics beyond the typed zero; Curve/Pyth/Stork/RedStone and every other omitted H-03 component's parameters; `DefaultsBase`/`DefaultsLocal` as Robinhood artifacts; sGREEN CCIP permanently |
| `blocked` | Every value listed `blocked` in Sections 2-3: cadence-gated block counts, TrainingWheels binding, `specialStabPoolId`, LP artifacts, PSM numerics, AAPL integers, vault IDs, addresses, roles, signers, initial supplies |

### 4.2 Required reconciliations

- **Rewards:** deployed globally disabled (`deployed initial value`) versus a
  separately validated activation target: the launch manifest encodes only
  the disabled state; any activation values live in `fast_follow` entries
  that the schema forbids from entering generated launch defaults. The
  M0-frozen kill-switch asymmetry (points disable fast; emission-zero
  timelocked and already zero at launch) is carried as a manifest note, not a
  new mechanism.
- **AAPL:** disabled staging versus the complete atomic activation group: the
  asset matrix (Section 6) represents AAPL as `blocked` for every
  reachability-granting field until the M5 same-block configuration bundle
  executes; deployment of disabled M1-M3 artifacts for ordered setup is
  permitted only while no Stock value path is reachable.
- **CCIP:** GREEN/RIPE disabled at launch through promotion; provisional
  HQ/23-24 reservations carry no artifact, address, or capability; sGREEN is
  permanently excluded (`omitted`, never `fast_follow`).
- **USDG/PSM:** redemption-first, GREEN-mint-last is a sequencing constraint
  inside `pre-activation configuration`; an enabled PSM target never
  bypasses its ordered disabled-deploy, funding, canary, and mint-authority
  gates.
- **sGREEN:** chain-native deposits and withdrawals are `deployed initial
  value` launch requirements (M0 decision 6).
- **Stability Pool / RipeGov:** launch-active roles (M0 decision 8) with
  Stock exclusions; concrete parameters blocked as recorded.
- **LP rows:** deposit-only with explicit legitimate `ltv=0` at launch;
  every unproved DEX/factory/pool/oracle/address input `blocked`
  (`B-LP-ARTIFACTS` is a hard launch stop).
- **Additional Stock Tokens:** `post-launch release` only, after
  token-specific evidence.
- **Guarded internal settlement:** a Track 8 mechanism direction; its M1-M5
  implementation and activation remain blocked; H-04 records no settlement
  parameter.

**No time target converts a later action into an initial default.** An
elapsed seven-day window changes nothing without its own fresh review
(blueprint rule: "an elapsed deadline never mutates the referenced launch
state"; the manifest schema rejects fast-follow values used as launch
defaults).

## 5. A5 — Clock and economic field disposition (BN/CAD mapping)

### 5.1 Authorities and method

The S2 checked inventory (`config/block-clock-inventory.json`, validated by
`scripts/check_block_clock_inventory.py --check`, output
`CLOCK_INVENTORY_OK ... bn_ids=32 ... cadence_candidates=474`) enumerates 99
production `block.number` occurrences over 94 lines in 17 files under 32 BN
IDs, plus exactly one CAD ID (`CAD-001`, 27 sites) and 11 TS timestamp IDs.
The shared clock specification supplies per-ID semantics, Base→Robinhood
targets, and the conversion formula `count = ceil(D / q)` with planning
quanta `qBase = 2 s`, `qRH = 12 s` (configuration assumptions, not chain
guarantees) and the derived `ceil(Base/6)` candidate rule with upward
rounding, zero preserved, no conversion of absolute operator-supplied
numbers, no cadence multiplier on relative point ratios, and no `chain.id`
branch.

**Approval state:** the cadence basis is owner-approved **only** for the S3
Lootbox floor (`43_200` → `7_200`, dated S3-only approval). Every other `/6`
value below is an unapproved candidate. This document selects none of them.

**S6-scope BN set** (per the spec's slice assignment): BN-001, BN-003 to
BN-009, BN-012 to BN-025, BN-027 to BN-032, and CAD-001. Excluded from this
slice: BN-002 (S5 same-block guard), BN-010/BN-011 (S9, Curve omitted),
BN-026 (S8 telemetry).

**Defaults-file linkage caveats (recorded for reviewers):** the inventory's
`semanticIds` are empty for every `DefaultsBase.vy`/`MissionControl.vy`
cadence candidate except the four CAD-001 sites, so field→BN linkage below
derives from the specification tables; and the per-asset
`customAuctionParams` zero pairs in `DefaultsBase.vy` produce no cadence
candidates (inert while `hasParams=False`) — Phase B parity tests must
enumerate them from the struct, not from the inventory.

**Clock-inventory history (exact).** The current controlling authority is
the committed checked inventory: **99 occurrences, 94 lines, 17 files, 32 BN
IDs, and the single indirect ID CAD-001**, revalidated green in this Phase A
(Section 13). The earlier 100-occurrence / 95-line baseline was reduced to
99/94 by the reviewed S5 Ledger reconciliation commit
`ed10d4d13fb22c2d00ad2dc06b4faece1e2629f3`
("fix(rh): complete S5 Ledger guard and inventory reconciliation"), which
replaced the two direct `checkAndUpdateLastTouch` `block.number` records
with one `_getActionBlock` record for BN-002 — mechanically confirmed from
that commit's `config/block-clock-inventory.json` diff (two removed
production records with `"function": "checkAndUpdateLastTouch"`, one added
with `"function": "_getActionBlock"`). The reduction is **not** attributable
to the later S2/CCIP inventory change. The older
`docs/chains/rh/shared-block-clock-specification.md` still states 100/95 and
requires a separately owned correction; that document is not edited under
this authorization.

### 5.2 Timelocks and action expiries

S1 profile outcomes required for every row: `B-ORD`, `R-REP128` (no progress
while NUMBER repeats), `R-PLUS1`, `R-J2-J4`, `R-STRESS60` (a `+60` jump may
cross a confirmation boundary or an expiry window in one step), plus
`BOUNDARY-OPEN`/`BOUNDARY-WINDOW` with exact `B`, `B±1`, `S`, `S+1`, `E-1`,
`E`, `E+1` assertions.

| Field (BN) | Where configured | Base value / bounds (blocks) | Candidate (unapproved) | No-change alternative | Owner |
| --- | --- | --- | --- | --- | --- |
| Erc20Token `hqChangeTimeLock` (BN-001) | token constructor class | 43,200 / 43,200..302,400 | 7,200 / 7,200..50,400 | keep Base counts (≈6× longer wall time) | protocol/security via `D-H04-08` |
| LocalGov `govChangeTimeLock` (BN-003) | constructor per governed contract | 43,200 / same bounds | 7,200 / 7,200..50,400 | same | same |
| TimeLock `actionTimeLock` + `expiration` (BN-004) | per-inheritor constructor (`config/BluePrint.py` timelock keys) | per-inheritor table | ceil `/6`, zero preserved; `expiration >= approvedStressJump + 1` (≥ 61) mandatory | keep Base counts | same |
| Contributor `keyActionDelay` (BN-005/BN-006) | HR constructor term | 43,200 | 7,200 | same | same |
| RipeHq config/registry delay (BN-018) | HQ constructor | 21,600 / 21,600..302,400 | 3,600 / 3,600..50,400 | same | same |
| AddressRegistry add/update/disable delay (BN-019/020/021) | registry constructors (PriceDesk setup precedent 0) | 21,600 | 3,600; one shared-delay policy must be owner-accepted (BN-021 blocked on it) | same | same |

Action-expiry headroom rule (`D-H04-08`): every expiry window must survive
the approved stress jump without silently expiring a pending action
(`expiration >= 61` under `R-STRESS60`), and boundary semantics keep
TimeLock valid at confirmation and invalid at exact expiration.

### 5.3 Governance locks and boosts

| Field (BN) | Base (blocks) | Candidate | Notes |
| --- | --- | --- | --- |
| Gov-vault `minLockDuration`/`maxLockDuration` (BN-008/BN-009) | 43,200 .. 47,304,000 | 7,200 .. 7,884,000 | lock bonus math retained shared; economic boost/exit terms are `D-H04-10`, not conversions |
| BondBooster `minLockDuration` floor (BN-032) | 7,776,000 | 1,296,000 | booster `expireBlock` is an absolute operator number — **never converted** |

### 5.4 Capacity refill intervals, PSM buckets, and debt intervals

| Field (BN) | Base (blocks) | Candidate | Boundary semantics |
| --- | --- | --- | --- |
| `genDebtConfig.numBlocksPerInterval` borrow bucket (BN-029) | 43,200 | 7,200 | fresh bucket at exact equality; `R-REP128` shares one bucket across repeats; jumps skip refills without carry |
| PSM `numBlocksPerInterval` mint bucket (BN-027) | 43,200 | 7,200 (Track 4 provisional, explicitly not accepted) | interval active while `start + interval > NUMBER`; equality starts a new bucket; same-NUMBER calls share one bucket |
| PSM redeem bucket (BN-028) | inherits BN-027 | independent bucket, same candidate | same |

A jump that crosses one or more whole windows performs exactly one reset with
no retroactive capacity (one-reset/no-carry semantics; the Phase B clock
tests must prove multi-window jumps).

### 5.5 Auctions and bonds

| Field (BN) | Base | Candidate | Notes |
| --- | --- | --- | --- |
| `genAuctionParams.delay` / `.duration` (BN-030/BN-031) | 0 / 43,200 | 0 / 7,200 | window `[start, end)`: valid at start, invalid at end; minimum duration must exceed stress-jump headroom or the owner explicitly accepts auction-skip behavior (`D-H04-10`) |
| Bond `epochLength` / `restartDelayBlocks` (BN-014/015/017) | 14,400 / 0 | 2,400 / 0 | catch-up interval semantics retained; no retroactive capacity |
| `setStartEpochAtBlock` / `startBondEpochAtBlock` (BN-013/BN-016) | absolute heights | **no conversion** — absolute operator-supplied numbers | operator runbook items, not manifest values |

### 5.6 Reward point attribution and RIPE emission

| Field (BN) | Semantics | Disposition |
| --- | --- | --- |
| RipeGov points accrual (BN-007) | `shares × elapsed NUMBER`; no cadence scalar | retain formula; **no numeric multiplier or normalization change**; blocked on rewards attribution economics (`D-H04-09`) |
| Lootbox deposit points (BN-022) | accrual across elapsed NUMBER | same rule; blocked on point-attribution approval; repeated numbers attribute zero elapsed increments — an accepted property of the L1-increment clock the owner must acknowledge |
| Lootbox borrow points (BN-023) | accrual on prior principal | same |
| `rewardsConfig.ripePerBlock` (BN-024) | monetary emission per NUMBER increment | launch value **0 (approved)**; the fast-follow candidate derives from the approved rational amount per second, rounded once at the smallest token unit (`0.0075 × 6 = 0.045` RIPE is exact; nominal 324 RIPE/day on both chains) and requires tokenomics approval (`D-H04-09`) |
| `stabPoolRipePerDollarClaimed` | RIPE per dollar (cadence-free) | fast-follow economics, `D-H04-09` |

Uniform cadence factors cancel from ideal point ratios, so allocation splits
(`borrowersAlloc` etc.) need no conversion — they are economic choices that
must conserve `100_00` exactly when points are enabled.

### 5.7 Dynamic-rate fields (CAD-001)

`increasePerDangerBlock` is an integer numerator over runtime denominator
`1_000_000` (`contracts/core/CreditEngine.vy:182,1066-1067`); the Base raw
seed `10` means an ideal slope of 0.001% per danger number. It has 27
inventory sites plus the interface declaration (`ConfigStructs.vyi:29`,
outside the CAD site set — recorded for completeness). The known reporting
defect (generic formatter divides by `10_000`, printing 0.10%) is owned by
S10; **S10's display correction supplies no runtime value**. Robinhood
disposition: `blocked` under `D-H04-07` — with Curve omitted there is no
Robinhood danger-number producer at launch, so the manifest must carry an
explicit inert reviewed value (a legitimate typed zero or an explicitly
inert raw value), and the deployment must prove no Curve producer or
PriceDesk registration exists. The raw `60` (= nominal `/6` of an ideal
per-second slope) is only a future candidate gated on Curve re-enablement
plus risk approval.

### 5.8 Cooldown assertions

BN-012 (`deleverageCooldown`): S4 is closed no-code; the expected live value
is the exact integer `0`; the dormant duplicated `MAX_COOLDOWN_BLOCKS =
7_200` constants remain documented latent debt; activation requires
reopening S4 (verbatim manifest statement, DP-03). The Robinhood-floor
option table for the maximum is deferred with S4.

### 5.9 Timestamp-only fields (no conversion)

| Field | Domain | Base value | Disposition |
| --- | --- | --- | --- |
| `genConfig.priceStaleTime` | seconds | 1 day (86,400) | `unresolved` (`D-H04-08`); reconcile with per-feed stale times against the two integrated 86,400-second feed heartbeats; zero effective stale time is a hard reject |
| `hrConfig` cliff/delay/vesting terms (TS-002) | seconds | 1 wk / 3 mo / 1 wk / 10 yr | `unresolved` (`D-H04-08`); **no block conversion applies**; sequencer timestamps are nondecreasing and are not an alias for NUMBER; the `MIXED` profile proves domain separation |

### 5.10 S3 anchor (approved)

BN-025: immutable Lootbox floor `7_200` (constructor input), governed
interval `0`, strict `>` boundary retained (equality remains too early);
the only owner-approved cadence conversion, explicitly non-generalizable.

## 6. A6 — Asset-configuration matrix

The launch asset universe is exactly the owner-closed M0 seven-asset graph.
**Omission rule:** every asset not named below is omitted; an omitted asset
receives no `AssetConfig` entry, no vault, no route, and no price source,
and no omitted field inherits an enabling default. Base's 24-entry
`assetConfigs` array is comparison evidence only; none of its addresses or
values carries forward.

Asset roles: AAPL (`I-AAPL-TOKEN`, Track 8) receives its `AssetConfig` entry
**only inside the atomic M5 bundle**; GREEN (`I-GREEN`), RIPE (`I-RIPE`),
sGREEN (`I-SGREEN`), and both LPs (`I-GREEN-USDG-LP`, `I-RIPE-WETH-LP`) are
`launch_initial` structural rows; canonical USDG (`I-USDG`) is
**`not_applicable` for every ordinary Teller configuration field** — it is
PSM/LP-only (M0 decision 10), must not receive an `AssetConfig` entry, and
its identity/exact-transfer/feed facts are consumed by the PSM route only.
sGREEN additionally may never generate a CCIP surface (permanent rule);
GREEN/RIPE CCIP capabilities are component capabilities outside
`AssetConfig` and remain disabled through promotion.

Cell legend (every cell carries exactly one typed status):

- `T✓` / `F✓` / `Z✓` — approved explicit `True` / `False` / zero, fixed by
  the cited integrated authority or structural source constraint
  (all `Z✓`/`F✓` cells are members of the `D-H04-20` legitimate-zero/false
  register);
- `D◦` — approved derived formula; the concrete integer remains prohibited
  until the named later gate;
- `B◦<gate>` — blocked: concrete value prohibited until the named gate;
- `U◦D-nn` — unresolved owner decision `D-H04-nn` (structural candidate, if
  any, in the footnotes);
- `NA` — not_applicable.

| `AssetConfig` field | AAPL | GREEN | RIPE | sGREEN | USDG | GREEN/USDG LP | RIPE/WETH LP |
| --- | --- | --- | --- | --- | --- | --- | --- |
| entry `asset` (identity) | B◦B-T8-FREEZE | B◦B-H05-PLAN +B-SECOPS-HANDOFF | B◦B-H05-PLAN +B-SECOPS-HANDOFF | B◦B-H05-PLAN | NA | B◦B-LP-ARTIFACTS +B-ORACLE-FREEZE | B◦B-LP-ARTIFACTS +B-ORACLE-FREEZE |
| `vaultIds` | B◦B-T8-M2 ¹ | U◦D-13 ² | T✓ `[2]` ³ | T✓ `[1]` ⁴ | NA | U◦D-13 ⁵ | U◦D-13 ⁵ |
| `stakersPointsAlloc` | Z✓ (launch) ⁶ | Z✓ (launch) ⁶ | Z✓ (launch) ⁶ | Z✓ (launch) ⁶ | NA | Z✓ (launch) ⁶ | Z✓ (launch) ⁶ |
| `voterPointsAlloc` | Z✓ (launch) ⁶ | Z✓ (launch) ⁶ | Z✓ (launch) ⁶ | Z✓ (launch) ⁶ | NA | Z✓ (launch) ⁶ | Z✓ (launch) ⁶ |
| `perUserDepositLimit` | D◦ cap formula ⁷ | U◦D-13 | U◦D-13 | U◦D-13 | NA | U◦D-13 | U◦D-13 |
| `globalDepositLimit` | D◦ cap formula ⁷ | U◦D-13 | U◦D-13 | U◦D-13 | NA | U◦D-13 | U◦D-13 |
| `minDepositBalance` | B◦B-T8-M5 | U◦D-13 | U◦D-13 | U◦D-13 | NA | U◦D-13 | U◦D-13 |
| `debtTerms.ltv` | B◦B-T8-M5 ⁸ | Z✓ ⁹ | Z✓ ⁹ | Z✓ ⁹ | NA | **Z✓ (M0-approved)** ¹⁰ | **Z✓ (M0-approved)** ¹⁰ |
| `debtTerms.redemptionThreshold` | B◦B-T8-M5 | Z✓ ⁹ | Z✓ ⁹ | Z✓ ⁹ | NA | Z✓ ¹⁰ | Z✓ ¹⁰ |
| `debtTerms.liqThreshold` | B◦B-T8-M5 | Z✓ ⁹ | Z✓ ⁹ | Z✓ ⁹ | NA | Z✓ ¹⁰ | Z✓ ¹⁰ |
| `debtTerms.liqFee` | B◦B-T8-M5 | Z✓ ⁹ | Z✓ ⁹ | Z✓ ⁹ | NA | Z✓ ¹⁰ | Z✓ ¹⁰ |
| `debtTerms.borrowRate` | B◦B-T8-M5 | Z✓ ⁹ | Z✓ ⁹ | Z✓ ⁹ | NA | Z✓ ¹⁰ | Z✓ ¹⁰ |
| `debtTerms.daowry` | B◦B-T8-M5 | Z✓ ⁹ | Z✓ ⁹ | Z✓ ⁹ | NA | Z✓ ¹⁰ | Z✓ ¹⁰ |
| `shouldBurnAsPayment` | B◦B-T8-M5 | U◦D-13 ¹¹ | U◦D-13 ¹¹ | U◦D-13 ¹¹ | NA | U◦D-13 ¹¹ | U◦D-13 ¹¹ |
| `shouldTransferToEndaoment` | B◦B-T8-M5 | U◦D-13 ¹¹ | U◦D-13 ¹¹ | U◦D-13 ¹¹ | NA | U◦D-13 ¹¹ | U◦D-13 ¹¹ |
| `shouldSwapInStabPools` | **F✓ (M0-approved)** ¹² | U◦D-13 ¹¹ | U◦D-13 ¹¹ | U◦D-13 ¹¹ | NA | U◦D-13 ¹¹ | U◦D-13 ¹¹ |
| `shouldAuctionInstantly` | B◦B-T8-M5 | U◦D-13 ¹¹ | U◦D-13 ¹¹ | U◦D-13 ¹¹ | NA | U◦D-13 ¹¹ | U◦D-13 ¹¹ |
| `canDeposit` | B◦B-T8-M5 ¹³ | U◦D-13 ¹¹ | **T✓ (M0-8)** ¹⁴ | **T✓ (M0-6)** ¹⁵ | NA | **T✓ (M0-9)** ¹⁶ | **T✓ (M0-9)** ¹⁶ |
| `canWithdraw` | B◦B-T8-M5 ¹³ | U◦D-13 ¹¹ | U◦D-13 ¹⁷ | **T✓ (M0-6)** ¹⁵ | NA | U◦D-13 ¹⁷ | U◦D-13 ¹⁷ |
| `canRedeemCollateral` | **F✓ (M0-11)** ¹⁸ | F✓ ⁹ | U◦D-13 ¹¹ | U◦D-13 ¹¹ | NA | U◦D-13 ¹¹ | U◦D-13 ¹¹ |
| `canRedeemInStabPool` | **F✓ (M0-8)** ¹² | U◦D-13 ¹¹ | U◦D-13 ¹¹ | U◦D-13 ¹¹ | NA | U◦D-13 ¹¹ | U◦D-13 ¹¹ |
| `canBuyInAuction` | B◦B-T8-M5 ¹⁹ | U◦D-13 ¹¹ | U◦D-13 ¹¹ | U◦D-13 ¹¹ | NA | U◦D-13 ¹¹ | U◦D-13 ¹¹ |
| `canClaimInStabPool` | **F✓ (M0-8)** ¹² | U◦D-13 ¹¹ | U◦D-13 ¹¹ | U◦D-13 ¹¹ | NA | U◦D-13 ¹¹ | U◦D-13 ¹¹ |
| `specialStabPoolId` | B◦B-H04-PARAMS ²⁰ | B◦B-H04-PARAMS ²⁰ | B◦B-H04-PARAMS ²⁰ | B◦B-H04-PARAMS ²⁰ | NA | B◦B-H04-PARAMS ²⁰ | B◦B-H04-PARAMS ²⁰ |
| `customAuctionParams.hasParams` | B◦B-T8-M5 | U◦D-13 ²¹ | U◦D-13 ²¹ | U◦D-13 ²¹ | NA | U◦D-13 ²¹ | U◦D-13 ²¹ |
| `customAuctionParams.startDiscount` | B◦B-T8-M5 | U◦D-13 ²¹ | U◦D-13 ²¹ | U◦D-13 ²¹ | NA | U◦D-13 ²¹ | U◦D-13 ²¹ |
| `customAuctionParams.maxDiscount` | B◦B-T8-M5 | U◦D-13 ²¹ | U◦D-13 ²¹ | U◦D-13 ²¹ | NA | U◦D-13 ²¹ | U◦D-13 ²¹ |
| `customAuctionParams.delay` | B◦B-T8-M5 | U◦D-13 ²¹ | U◦D-13 ²¹ | U◦D-13 ²¹ | NA | U◦D-13 ²¹ | U◦D-13 ²¹ |
| `customAuctionParams.duration` | B◦B-T8-M5 | U◦D-13 ²¹ | U◦D-13 ²¹ | U◦D-13 ²¹ | NA | U◦D-13 ²¹ | U◦D-13 ²¹ |
| `whitelist` | B◦B-T8-M5 | U◦D-13 ²² | U◦D-13 ²² | U◦D-13 ²² | NA | U◦D-13 ²² | U◦D-13 ²² |
| `isNft` | **F✓** ²³ | **F✓** ²³ | **F✓** ²³ | **F✓** ²³ | NA | **F✓** ²³ | **F✓** ²³ |

Footnotes (structural candidates and authority cites — candidates are not
selections):

1. Exactly one enabled vault at activation under a new Track 7-owned
   VaultBook ID; replacement of funded live IDs rejected; unapproved until
   `B-T8-M2`/M5.
2. Base precedent is the empty list (GREEN holds no vault); the Robinhood
   row must be explicitly selected in `D-H04-13`.
3. VaultBook row 2 (Ripe Gov Vault) is source-hard-coded in
   Teller/BondRoom/HR/Lootbox and RIPE governance-vault participation is a
   launch requirement (M0 decision 8), fixing `[2]` structurally.
4. VaultBook row 1 (Stability Pool) is source-hard-coded in
   Teller/CreditEngine/CreditRedeem; sGREEN's stability membership follows
   the integrated graph.
5. Structural candidates from the integrated graph: GREEN/USDG LP → `[1]`
   (stability), RIPE/WETH LP → `[2]` (governance); owner selection in
   `D-H04-13` because vault participation is per-asset policy.
6. Points allocations are inert-zero at launch (rewards globally disabled,
   M0 decision 3); any nonzero split is `fast_follow` under
   `B-REWARD-PROMOTION` and must conserve the 100_00 denominator
   (`D-H04-09`).
7. `capAtomic = floor(D * 10^(18+8) / P8)` with `D = 5,000` (per-user) and
   `D = 25,000` (global), round down, at the final price freeze
   (M0 decision 12); integers prohibited until `B-T8-FREEZE`.
8. The activation bundle requires finite reviewed DebtTerms with finite LTV
   staged under disabled routes; every concrete value is prohibited until
   `B-T8-M5`.
9. GREEN, RIPE, and sGREEN carry no borrowing power in the owner-closed M0
   launch graph; all six DebtTerms fields are structural explicit zeros
   (typed legitimate, never omitted-masquerading-as-zero). GREEN's
   collateral-redemption flag is likewise structurally `False`.
10. `ltv = 0` is the M0-approved explicit legitimate zero for both LP rows
    (M0 decision 9); the remaining five DebtTerms zeros follow structurally
    from zero borrowing power.
11. Owner selection in `D-H04-13`; Base values (Section 2.2.11 and
    `DefaultsBase.vy:1040-1230`) are labeled comparison evidence only.
12. Stock Tokens are excluded from Stability Pool custody and swaps
    (M0 decision 8): swap, stab-redeem, and stab-claim surfaces are
    approved explicit `False` for AAPL.
13. AAPL reachability flags stay `False` through staging; the complete
    atomic M1+M2+M3+M4-proof+M5 group flips the reviewed set in one
    sequence (`B-T8-M5`).
14. RIPE governance-vault deposits are a launch requirement (M0 decision 8).
15. Chain-native sGREEN deposits **and** withdrawals are day-one launch
    requirements (M0 decision 6).
16. Both LPs are launch deposit tokens (M0 decision 9), ordinary Teller
    `deposit`/`depositMany` only; `depositFromTrusted` and every
    Department/direct-vault bypass are excluded (`S-024-LP-ORDINARY-ONLY`).
17. Withdrawal posture is not fixed by the route restriction; candidate
    `True`, owner selection in `D-H04-13`.
18. CreditRedeem Stock extraction remains disabled (M0 decision 11).
19. Auction purchasing of AAPL is blocked until the activation bundle;
    the settlement direction is Track 8 mechanism authority.
20. The concrete `specialStabPoolId` binding by asset is named inside the
    H-03 blocker `B-H04-PARAMS` (`I-STABILITY-CONFIG`); any valid VaultBook
    ID is source-permitted, so no target edge is asserted before binding.
21. Structural candidate is the inert Base shape (`hasParams=False`, four
    zeros); the pairs are invisible to the cadence scanner while inert and
    must be enumerated from the struct by Phase B tests (Section 5.1).
22. Candidate `empty(address)` (no whitelist), Base precedent.
23. The six assets that receive `AssetConfig` entries are ERC-20s under
    integrated identity evidence; `isNft = False` is factual for exactly
    those six. USDG receives no `AssetConfig` entry, so no `isNft` value
    (or any other `AssetConfig` value) exists for it — its column is
    `not_applicable` throughout.

### 6.1 Matrix proofs (each becomes a Phase B test obligation)

1. AAPL has exactly one enabled vault at activation, and none before.
2. AAPL trusted/Department deposit routes cannot bypass caps (they are
   disabled; M1 exact-receipt enforcement covers every route including
   trusted ones).
3. Stock Stability Pool and CreditRedeem routes are disabled
   (`shouldSwapInStabPools=False`, stab-pool custody exclusion, CreditRedeem
   extraction disabled).
4. Both LP rows have explicit legitimate zero borrowing power; the schema
   distinguishes typed zero from missing.
5. Chain-native sGREEN deposits and withdrawals are launch requirements;
   no sGREEN CCIP route can be generated.
6. GREEN Stability Pool and RIPE governance-vault participation match M0.
7. USDG is not ordinary Teller collateral (no AssetConfig row exists).
8. PSM configuration preserves redemption-first and GREEN-mint-last
   activation (sequence gates in the manifest; DP-09).
9. Underscore and Base-only integrations are absent (no Underscore rows;
   `underscoreRegistry` zero; no Curve/Aero/Pyth/Stork configuration).
10. Reward allocations match the approved initial phase (points disabled;
    zero emission; allocations inert).
11. No omitted field inherits an enabling default (schema rejects missing
    fields; explicit statuses everywhere).
12. Every exact address remains blocked until identity evidence is approved
    (symbolic identities only; the generator rejects address literals that
    are not approved manifest values).

AAPL auction purchasing, borrowing, and internal settlement remain blocked
until the complete Track 8 group is approved, implemented, audited,
configured, and atomically activated; the owner-approved settlement
direction is not reinterpreted or implemented here.

## 7. A7 — Deterministic generation

### 7.1 How the existing Base generator actually works (evidence)

`scripts/params/regenerate_defaults.py` (1,143 lines) is a live-fork reader,
not a manifest renderer:

- it requires `ETHERSCAN_API_KEY`, forks live Base mainnet at the **latest**
  block through the shared params library, and reads MissionControl,
  PriceDesk, and VaultBook state through the hardcoded Base RipeHq entry
  (`scripts/params/params_utils.py:28-29,275-296`;
  `regenerate_defaults.py:844-926`);
- it recomputes deposit limits from USD constants through **live oracle
  prices** (`:35-37,164-182`) and orders assets by live TVL (`:1007-1014`),
  so output changes block to block;
- it embeds two sets of literal Base asset addresses (`:59-76`), Base
  cadence constants (`HOUR_IN_BLOCKS = 1_800`, `:45`, re-emitted into the
  artifact at `:654-658`), registry IDs, and a hardcoded gov-vault ID;
- it writes `contracts/config/DefaultsBase.vy` directly (`:1122-1128`) with
  no check-only or dry-run mode;
- silent-failure paths exist (symbol `"???"` fallback, decimals defaulting
  to 18, `price = 0` on RPC failure, `(0,0,0)` limits on conversion
  failure);
- it is **already non-idempotent with its own artifact**: it emits an empty
  `liteSigners()` while the committed `DefaultsBase.vy:1272-1276` carries
  two signer addresses (post-generation hand edit);
- only ~200 lines are network-free (the value formatters and the template
  scaffold); `run_all.py` does not invoke it (the report pipeline is
  separate).

The consumer contract is the ABI alone: `MissionControl.__init__` calls the
17 interface selectors; the hand-written 156-line `DefaultsLocal.vy` already
satisfies it, proving no structural coupling to `DefaultsBase.vy`'s layout.

### 7.2 Three-option comparison

| Criterion | (a) New deterministic network-free generator | (b) Narrow refactor of `regenerate_defaults.py` | (c) Manual source + parity verifier |
| --- | --- | --- | --- |
| Live-read entanglement | none by construction | requires making a 1,100-line interleaved `main()` network-optional; Base facts embedded at nine distinct levels | none |
| Determinism / two-build identity | trivial (pure function of manifest) | achievable only after deep restructuring | source is static; verifier deterministic |
| Prohibited-file pressure | none | **high** — the refactored file is the sole writer of prohibited `DefaultsBase.vy`; a refactor bug is a prohibited-file change discovered late; the script itself is a listed consumer surface | none |
| Duplication | ~200 lines of pure value formatting + template shape | single formatter | verifier logic duplicates struct traversal |
| Check-only mode | natural | absent today, must be added | natural (the verifier is the check) |
| Mechanical-generation requirement of the brief | satisfied | satisfied | **not satisfied on its face** ("generate mechanically"); would need owner re-scoping |
| Failure modes | fails closed on unresolved fields | inherits silent-failure paths unless all are removed | manual-edit drift (the exact `liteSigners` failure mode) — though the verifier catches it |

### 7.3 Recommendation (owner decision `D-H04-01`)

**Option (a): a new deterministic, network-free, Robinhood-only generator**
at `scripts/params/generate_robinhood_defaults.py`, consistent with the
brief's stated default. No consumer incompatibility exists (interface-only
coupling), and the duplication is small, mechanical, and low-risk compared
with refactoring the sole writer of a prohibited file.

Optional sub-decision for the owner: lift the pure formatter functions
(`regenerate_defaults.py:236-348,432-456`) into a new shared module imported
by the new generator, leaving `regenerate_defaults.py` byte-for-byte
untouched. This removes the duplication objection but adds one file beyond
the default Phase B ceiling, so it requires file-exact approval; the default
recommendation is plain duplication inside the new generator.

The selected design must (all are Phase B test obligations): run without
RPC, credentials, mutable environment values, or wall-clock dependence; read
one reviewed manifest; render deterministically and byte-identically twice;
fail on any unresolved included field; preserve canonical `Defaults`
selectors and tuple order; reject Base/local address leakage; support a
check-only mode; never overwrite `DefaultsBase.vy`; print no secret-bearing
values; write atomically; and emit readable, reviewable Vyper. The generated
artifact must declare its own Robinhood cadence constants rather than
inheriting Base's `HOUR_IN_BLOCKS = 1_800` family, and must keep
`increasePerDangerBlock` raw (the runtime denominator is `1_000_000`;
S10's display fix is irrelevant to the emitted value).

**Tooling class:** the generator is development-only tooling, not production
tooling: it runs at authoring time, its output is the reviewed artifact, and
it must never run in deployment or runtime paths. Future changes to it are
owned by this combined S6/H-04 slice (post-integration, by whoever owns the
parameter manifest), with any change re-triggering the deterministic
two-build comparison and mutation tests.

### 7.4 Typed manifest schema proposal (`config/robinhood-parameters.json`)

This remains a proposed Phase A schema, not implementation authority.

Top-level document shape: `schema_version` (semver string), `baseline`
(object: `rh` commit, tree, controlling-document SHA-256 map per Section
1.2), and `parameters` — an array of records. **Every record must contain
all 19 required top-level keys.** Missing keys are rejected; JSON `null` is
rejected everywhere (typed nulls are tagged objects, below). The 19 key
names, individually:

1. `id`
2. `h03_ref`
3. `destination`
4. `description`
5. `value`
6. `unit`
7. `status`
8. `source`
9. `owner`
10. `reviewer_class`
11. `approval`
12. `launch_phase`
13. `blockers`
14. `zero_semantics`
15. `base_comparison`
16. `conversion`
17. `generated_repr`
18. `consumers`
19. `invalidation`

Closed type and validation rule per key (nested members are listed
explicitly and are **not** counted as top-level keys):

| # | Key | Closed type | Validation rule |
| --- | --- | --- | --- |
| 1 | `id` | string matching `^P-H04-[0-9]{3}$` | unique across the array; duplicates rejected |
| 2 | `h03_ref` | tagged object `{"kind": "component", "cm": "CM-0NN"}` or `{"kind": "track", "track": <closed track enum>}` | `cm` must exist in the integrated blueprint; unknown kinds/tracks rejected |
| 3 | `destination` | tagged object `{"kind": "defaults_field" \| "deployment_input" \| "assertion", "path": string}` | exact artifact+field path; unique; `deployment_input`/`assertion` paths naming a `Defaults` field rejected; `defaults_field` paths not in the 109-field census rejected |
| 4 | `description` | string, 1..500 chars | placeholder strings rejected; address-shaped literals (`0x` + 40 hex) in any narrative field rejected |
| 5 | `value` | tagged union: `{"kind": "concrete", "raw": int \| bool \| string}` · `{"kind": "inherited", "raw": ..., "inherited_from": citation}` · `{"kind": "derived", "formula": string, "inputs": [id...]}` · `{"kind": "typed_null", "reason": "blocked" \| "unresolved" \| "not_applicable" \| "omitted" \| "disabled_no_value"}` | kind must be consistent with `status` (matrix below); `concrete`/`inherited` require approved-bearing status; `derived` requires the formula's own approval citation and leaves the integer prohibited; strings must not be address-shaped unless `unit` is `address` **and** status is approved-bearing |
| 6 | `unit` | object `{"kind": <closed enum>, "denominator": int \| absent}` with kinds `blocks`, `seconds`, `basis_points`, `token_base_units`, `percentage_allocation`, `boolean`, `address`, `registry_id`, `hash`, `count`, `rate_per_block_1e6` | unknown kinds rejected; `denominator` **required** for `basis_points` (10000), `percentage_allocation` (10000), `rate_per_block_1e6` (1000000) and **forbidden** otherwise; `blocks` additionally requires a non-null `conversion` or an explicit `{"kind": "no_conversion", "why": ...}` member |
| 7 | `status` | closed enum of exactly the eight approved statuses: `launch_initial`, `fast_follow`, `deployment_assertion_only`, `disabled`, `omitted`, `blocked`, `not_applicable`, `unresolved` | unknown statuses rejected |
| 8 | `source` | object `{"citation": string, "commit": 40-hex string}` | both members required |
| 9 | `owner` | string: `D-H04-NN` decision ID or closed owner enum (`OWN-*` vocabulary) | unknown owners rejected |
| 10 | `reviewer_class` | closed enum: `protocol_security`, `risk_oracle`, `treasury`, `tokenomics`, `secops`, `engineering_tooling`, `governance`, `owner_direct` | unknown classes rejected |
| 11 | `approval` | tagged object `{"kind": "approved", "date": ISO-8601, "provenance": string}` or `{"kind": "pending"}` | `approved` required when `value.kind` is `concrete`/`inherited`; `pending` required otherwise; date/provenance required members of `approved` |
| 12 | `launch_phase` | closed enum of exactly the eight A4 phases | unknown phases rejected |
| 13 | `blockers` | array (possibly empty) of blocker/decision ID strings | every blocker entry must be one of the exact 18 active H-03 blocker IDs or one of the exact 12 active Section 12 H-04 wrapper IDs, and every decision entry a `D-H04-NN` ID from the Section 11 packet; the retired historical identifier `B-H04-ENV` is **explicitly rejected** in any current blocker array; all other unknown IDs rejected; must be non-empty when `status` is `blocked` |
| 14 | `zero_semantics` | closed enum: `legitimate_zero`, `legitimate_false`, `zero_forbidden`, `not_zero_typed` | required for every record; a `concrete` raw `0`/`false` with `zero_forbidden` rejected |
| 15 | `base_comparison` | tagged object `{"kind": "evidence", "raw": ..., "cite": string, "label": "evidence_only"}` or `{"kind": "none"}` | label literal required; Base/local address values in any non-`base_comparison` key rejected |
| 16 | `conversion` | tagged object `{"kind": "converted", "rule": string, "rounding": "ceil" \| "floor" \| "exact", "basis": "D-H04-06:<class>"}` · `{"kind": "no_conversion", "why": string}` · `{"kind": "not_applicable"}` | `blocks` unit with `converted` requires an approved cadence-basis reference; seconds values with `converted` block-rules rejected (block/seconds swap) |
| 17 | `generated_repr` | tagged object `{"kind": "vyper", "repr": string}` or `{"kind": "not_generated"}` | `vyper` required iff `destination.kind == "defaults_field"` and status is generation-bearing (`launch_initial`/`disabled` with value); `not_generated` otherwise |
| 18 | `consumers` | non-empty array of strings | — |
| 19 | `invalidation` | non-empty array of strings (trigger descriptions) | — |

**Missing/empty/null semantics (closed).** `missing key` → reject the
document. `JSON null` → reject. `numeric zero` / `boolean false` → legal
only inside `value.raw` with an approved-bearing status **and**
`zero_semantics` of `legitimate_zero`/`legitimate_false`. `empty string` →
reject wherever a string is required; `empty list` → legal only for
`blockers` (when status is not `blocked`); `empty object` → reject.
`blocked`/`unresolved`/`not_applicable`/`omitted` → the record is still
fully present with `value.kind = "typed_null"` carrying the matching
`reason`; `inherited`/`derived`/`concrete` are `value.kind` tags as above.
**Missing is never equivalent to null, zero, false, blocked, or
not_applicable** — each is a distinct, individually validated
representation, so the schema is closed: every field of every record is
always present with exactly one typed state.

**Status ↔ value-kind consistency matrix** (`✓` = allowed, blank =
rejected):

| `status` \ `value.kind` | `concrete` | `inherited` | `derived` | `typed_null` |
| --- | --- | --- | --- | --- |
| `launch_initial` | ✓ | ✓ | ✓ (integer still prohibited) | |
| `fast_follow` | ✓ | ✓ | ✓ | ✓ (`unresolved` reason only) |
| `deployment_assertion_only` | ✓ | | | |
| `disabled` | ✓ (the disabling value) | ✓ | | ✓ (`disabled_no_value`) |
| `omitted` | | | | ✓ (`omitted`) |
| `blocked` | | | ✓ (formula only) | ✓ (`blocked`) |
| `not_applicable` | | | | ✓ (`not_applicable`) |
| `unresolved` | | | | ✓ (`unresolved`) |

**Complete valid example record** (the S4 assertion pin):

```json
{
  "id": "P-H04-003",
  "h03_ref": {"kind": "component", "cm": "CM-044"},
  "destination": {"kind": "assertion", "path": "live:Deleverage.deleverageCooldown"},
  "description": "Expected post-deployment deleverage cooldown; activation requires reopening S4",
  "value": {"kind": "concrete", "raw": 0},
  "unit": {"kind": "blocks"},
  "status": "deployment_assertion_only",
  "source": {"citation": "docs/chains/rh/deleverage-cooldown-security-decision.md:907-919", "commit": "e39815d710ecfaf8bbeea54cabe8ae8d553a2740"},
  "owner": "D-H04-18",
  "reviewer_class": "protocol_security",
  "approval": {"kind": "approved", "date": "2026-07-24", "provenance": "S4 closure; owner + independent security decision"},
  "launch_phase": "deployed initial value",
  "blockers": [],
  "zero_semantics": "legitimate_zero",
  "base_comparison": {"kind": "none"},
  "conversion": {"kind": "no_conversion", "why": "assertion of an existing constructor-default zero"},
  "generated_repr": {"kind": "not_generated"},
  "consumers": ["H-08 live assertion", "H-05 reservation 0020"],
  "invalidation": ["S4 reopening", "any pending nonzero DELEVERAGE_COOLDOWN action"]
}
```

(The `unit` example above omits `denominator` because `blocks` forbids it;
the `conversion` member carries the mandatory no-conversion rationale for a
blocks-unit record.)

**Rejection matrix** (each row is a mutation the validator must reject,
proving closure and type-completeness):

| # | Mutation | Rejected by |
| --- | --- | --- |
| R1 | any of the 19 keys missing | required-key check |
| R2 | JSON `null` anywhere | null ban |
| R3 | duplicate `id` or duplicate `destination.path` | uniqueness |
| R4 | unknown `status`/`unit.kind`/`launch_phase`/`reviewer_class`/`value.kind` tag | closed enums |
| R5 | `value.raw = 0`/`false` with `zero_semantics = "zero_forbidden"` or with a non-approved status | zero/false gating |
| R6 | `typed_null` reason disagreeing with `status` (for example reason `blocked` under status `unresolved`) | consistency matrix |
| R7 | `status = "blocked"` with empty `blockers` | blocker requirement |
| R8 | Base/local address string outside `base_comparison` | address leak scan |
| R9 | address-shaped literal in `description` or any narrative member | narrative scan |
| R10 | `unit.kind = "blocks"` with `conversion.kind = "converted"` but no `D-H04-06` basis reference | cadence gate |
| R11 | `unit.kind = "seconds"` carrying a block conversion rule | block/seconds swap |
| R12 | `h03_ref` naming a `CM-*` component absent from the integrated blueprint, or an unknown track enum value | key 2 closed-reference rule |
| R13 | `fast_follow` record with a `generated_repr.kind = "vyper"` | launch-default gate |
| R14 | `destination.kind = "deployment_input"` whose path names a `Defaults` field | destination partition |
| R15 | `approval.kind = "pending"` with `value.kind = "concrete"` | approval gating |
| R16 | placeholder string (`TBD`, `TODO`, `<...>`) in any string member | placeholder scan |
| R17 | `denominator` present for `boolean`/`address`/`count` etc., or absent for the three denominator-bearing kinds | unit typing |
| R18 | RPC URL, key material, or secret-bearing string anywhere | secret scan |
| R19 | empty `consumers` array or empty `invalidation` array | keys 18/19 non-empty rule |

Every rejection row above is derivable from a specific declared rule of the
19-key schema (the cited key rule or document-level rule), and the 19
mutations are pairwise distinct, so a future validator can execute each one
mechanically.

**Deliberately outside the schema:** percentage-allocation group
conservation is **not** a schema rejection, because the 19-key record shape
carries no allocation-group identifier and therefore cannot determine group
membership. Conservation (for example the reward allocation split summing
to exactly `100_00` when points are enabled) remains a separately stated
protocol obligation enforced by the Phase B generator and tests (Sections
9.1 and 9.3), not by manifest-schema validation. Likewise, no
executable-plan flag exists in the declared top-level document shape; the
obligation that no executable plan may proceed while any required value is
pending, blocked, or unresolved is a downstream consumer obligation
(H-05 planning and the Phase B generator's fail-closed rule), not a schema
key.

The generated Vyper contains no provenance or status logic; governance and
deployment tooling consume the manifest, the contract returns only approved
canonical interface values. The manifest distinguishes values pending final
deployment freeze from approved fixed values and never contains RPC URLs,
keys, private addresses, raw provider payloads, or signer secrets.

## 8. Exact Phase B file proposal (`D-H04-02`)

Exactly six paths, unchanged from the brief's default boundary:

1. `contracts/config/DefaultsRobinhood.vy` — generated projection;
   implements every current `Defaults` selector exactly once; no chain-ID
   branch, no Base/local address, no runtime environment access, no storage,
   owner, setter, or protocol logic.
2. `config/robinhood-parameters.json` — the typed manifest (Section 7.4).
3. `tests/config/test_defaults_robinhood.py` — parity, mutation, and
   boundary tests (Section 9).
4. `tests/deployment/test_network_clock_profiles.py` — clock-profile proofs
   (Section 9); the basename avoids the S1 `tests/clock/test_clock_profiles.py`
   collision per the deployment spec's planning correction.
5. `scripts/params/generate_robinhood_defaults.py` — the recommended new
   generator (option a).
6. This evidence file, updated in the same commit for any approved
   conclusion or value change.

Any need for a different or additional file (including the optional shared
formatter module) is a stop condition requiring file-exact owner approval
before creation.

## 9. Complete Phase B test matrix (proposed; no test exists yet)

### 9.1 `tests/config/test_defaults_robinhood.py`

| Obligation | Source |
| --- | --- |
| canonical selector and tuple compatibility (all 17 selectors, exact struct order) | brief contract requirements |
| every generated field equals the approved manifest | parity core |
| deterministic generation; byte-identical double build; check-only mode | Section 7.3 |
| no Base/local address leakage (scan generated source against `DefaultsBase.vy`/`DefaultsLocal.vy` literals and any address not in the approved manifest) | brief |
| no unresolved or fast-follow value enters launch defaults | schema + generator fail-closed |
| every legitimate zero explicitly typed (`zero_semantics`) | Sections 2, 6 |
| deterministic array ordering (assets, gov-vault entries, priority lists, signers) | replaces the Base generator's live-TVL ordering |
| allocation denominators conserve exactly (points allocs; any percentage group) | generator/test validation obligation — the 19-key record schema cannot infer allocation-group membership, so conservation is enforced here, not by manifest-schema validation; any future schema-level enforcement requires an approved grouping identifier or equivalent closed grouping rule (Section 7.4) |
| omitted/disabled/blocked distinctions survive generation | A4 phases |
| `DefaultsBase.vy` and `DefaultsLocal.vy` each byte-identical to kickoff baseline (hashes in Section 1.2) | no-change proof |
| S3/S4/S5 boundaries preserved (no Lootbox floor field in Defaults; no S4 field exists; `shouldCheckLastTouch` True; no S5 constructor input in Defaults) | Sections 2-3 |
| AAPL cannot be accidentally active before Track 8 gates (no reachability-granting AAPL value generated pre-M5) | Section 6 |
| Stock Stability Pool / CreditRedeem / trusted routes disabled | Section 6 proofs |
| chain-native sGREEN launch routing present; no sGREEN CCIP route generatable | Section 6 |
| GREEN Stability Pool, RIPE governance-vault, both LP rows match the integrated graph incl. explicit zero LTV | Section 6 |
| USDG PSM ordering: redemption first, GREEN mint last (manifest gate order) | DP-09 |
| rewards globally disabled at launch unless a separately reviewed promotion proves the post-launch state | DP-15 |
| incomplete GREEN/RIPE CCIP promotion inputs remain disabled without blocking launch | DP-16 |
| Underscore remains omitted (registry zero; no Underscore rows) | Section 2.2.8 |
| repeated generation produces byte-identical Vyper | Section 7.3 |

### 9.2 `tests/deployment/test_network_clock_profiles.py`

Prove every approved block-based field under the integrated S1 profiles
`B-ORD`, `R-REP128`, `R-PLUS1`, `R-J2-J4`, `BOUNDARY-OPEN`,
`BOUNDARY-WINDOW`, `R-STRESS60`, and `MIXED` (seconds/NUMBER interaction),
covering exact-before/equality/after boundaries, multi-window jumps,
one-reset/no-carry semantics, rounding, nonzero floors, expiry headroom
(`expiration >= 61` under the stress jump), and initial-versus-fast-follow
values, using the integrated S1 fixtures and S2 checked inventory without
copying production logic into expected-value helpers. Per-family boundary
semantics follow Section 5 (strict `>` for the S3 floor; fresh-at-equality
for interval buckets; valid-at-confirmation/invalid-at-expiration for
timelocks; `[start, end)` for auctions).

### 9.3 Generator and manifest mutation tests

Each mutation must fail: missing or duplicate parameter; unknown
unit/status; zero replacing missing; Base address insertion; unresolved
included value; fast-follow value promoted to initial; tuple reordering;
allocation overflow/underflow; block/seconds swap; unapproved cadence
conversion; nondeterministic key ordering; stale generated source; changed
manifest after source generation; output path targeting `DefaultsBase.vy`;
RPC/environment access (environment probe in the generator test harness).

## 10. Base compatibility, no-change proof, and minimum-change stress test

### 10.1 No-change proof at Phase A

- This Phase A created exactly one file (this document). `git status` at
  freeze shows the single untracked evidence file and no modification to any
  tracked path.
- `DefaultsBase.vy`, `DefaultsLocal.vy`, `Defaults.vyi`, `ConfigStructs.vyi`
  hashes are frozen in Section 1.2 and re-assertable by reviewers.
- No shared contract, ABI, migration, manifest, dependency file, or
  prohibited path was touched; no test or tooling file was modified.

### 10.2 Minimum-change stress test of the proposed Phase B boundary

Applying the owner's minimum-change order to the only proposed production
artifact:

1. **No production change at all?** Rejected by the integrated component
   matrix itself: CM-007 `DefaultsBase` is `replaced` on Robinhood by CM-049
   and CM-060 `DefaultsLocal` is not a deployment artifact — a Robinhood
   deployment cannot seed MissionControl/Ledger without *some* Defaults
   source. Passing an empty defaults address (both constructors tolerate it)
   would deploy an unseeded MissionControl requiring dozens of post-deploy
   governance transactions to configure — strictly more operational risk and
   authority surface than one reviewed data-only artifact.
2. **Manifest-only configuration?** Insufficient alone: the constructor
   seeding path is how the deployed system acquires its initial values; the
   manifest cannot reach MissionControl without either a Defaults contract
   or a large scripted setter sequence (rejected above).
3. **Existing shared behavior?** Fully preserved — `DefaultsRobinhood.vy`
   is data-only, implements the unchanged canonical interface, adds no
   protocol logic, and changes no consumer.
4. **Disabled/omitted/deferred?** Applied field-by-field (Sections 2-6);
   the artifact itself encodes the disabled-first launch posture.
5. **Smallest approved production change:** one new data-only Vyper file
   whose Base blast radius is zero (no Base artifact or behavior changes;
   Base regression suite must stay green) and whose Robinhood blast radius
   is the initial seed of MissionControl/Ledger — every seeded value has a
   governed successor path (Section 2.3), so a wrong non-security value is
   correctable by governance, while wrong security-posture values are
   prevented by the fail-closed manifest gates.

Residual risk the owner is asked to accept: a data-only contract can still
encode a wrong approved value; mitigations are the typed manifest, mutation
tests, parity tests, two-build determinism, independent review, and the
governance successor path. Per the brief, every *field-level* proposal in
the packet also carries its own no-change/disabled alternative.

No `chain.id` branching, no Robinhood-only protocol behavior, no Base
migration, and no change to the deployed Base Ledger exception are proposed
anywhere in this packet.

## 11. A8 — Owner decision packet

**Exactly twenty genuine owner decisions** with stable IDs `D-H04-01`
through `D-H04-18`, `D-H04-20`, and `D-H04-21`, ordered by blast radius
(state- and authority-enabling first, presentation last). The former
`D-H04-19` was **not** an owner decision and has been retired: it is now the
factual validation disposition `VD-H04-ENV` (Section 13.1); its ID is not
reused, no other decision is renumbered, and the decision count is
truthfully twenty.

Each decision below is self-contained and records the nine mandatory
elements of the controlling brief in fixed order: (1) exact decision
question; (2) complete alternatives; (3) recommended choice; (4) risk of no
decision/no change; (5) smallest sufficient value or scope; (6) blast
radius (Base and Robinhood separately); (7) accepted residual risk; (8)
required reviewers and invalidation/reopen conditions; (9) exact copy-paste
owner approval language. Where a contract field is proposed, element (5)
also states why manifest-only configuration is insufficient. No decision is
approved by silence; if the owner gives no answer, Phase B remains
prohibited. **Nothing in this packet checks, approves, or resolves any
decision on the owner's behalf.**

Brief-item mapping: 1→D-H04-01/02, 2→D-H04-03, 3→D-H04-04/05/07,
4→D-H04-06, 5→D-H04-08, 6/7→D-H04-09, 8→D-H04-10, 9→D-H04-11,
10/12→D-H04-13, 11→D-H04-17, 13→D-H04-12, 14→D-H04-18, 15→D-H04-14,
16→D-H04-15, 17→D-H04-20, 18→D-H04-21, 19→D-H04-02.

**Packet organization.** The twenty decisions partition into four groups:

- **Group 1 — required before Phase A approval is recorded:** D-H04-01,
  D-H04-02, D-H04-20, D-H04-21 (they fix the boundary, the zero/false
  register, and the omitted/blocked register that Gate 1 review approves).
- **Group 2 — required before Phase B implementation:** D-H04-03, D-H04-04,
  D-H04-05, D-H04-06, D-H04-07, D-H04-08, D-H04-09, D-H04-10, D-H04-11,
  D-H04-13, D-H04-14 (every value that enters the manifest or generated
  source with an approved-bearing status).
- **Group 3 — deployment/release-only; may remain typed blockers through
  Phase B:** D-H04-12 (PSM numerics), D-H04-16, D-H04-17, D-H04-18's
  deployment bindings (the pins themselves are integrated).
- **Group 4 — safely retainable as open blockers through Phase A:**
  D-H04-15 (role/signer identities under the SecOps freeze) and every
  Group 2/3 decision the owner elects to leave `blocked` rather than
  select, which keeps the affected fields out of generated launch source.

### D-H04-13 — Initial and staged asset configuration (highest blast radius)

1. **Question:** Is the Section 6 per-field matrix — seven assets, the
   omission rule, the typed statuses in every cell, and the twelve proof
   obligations — the complete and correct launch asset universe for the
   Robinhood parameter manifest?
2. **Alternatives:** (a) approve the matrix as written; (b) approve with
   named cell-level changes (each change re-reviewed); (c) reject and
   return to the M0/H-03 owners for graph changes. An empty asset set is
   not an alternative — it contradicts the owner-closed M0 launch graph.
3. **Recommended:** (a).
4. **Risk of no decision:** no asset row can enter the manifest; Phase B
   cannot begin; launch planning has no collateral/routing surface.
5. **Smallest sufficient scope:** the seven symbolic rows plus typed
   constraints, all concrete values blocked until their gates close.
   Contract field justification: `assetConfigs` seeding is the integrated
   constructor mechanism; configuring every asset post-deploy through
   Bravo would need many timelocked governance transactions during launch,
   a strictly larger authority and error surface.
6. **Blast radius:** Base — zero (no Base artifact changes). Robinhood —
   the entire collateral, routing, stability, and auction surface.
7. **Accepted residual risk:** a wrong approved non-security value is
   governance-correctable through the cited setters; wrong route flags are
   caught by the Section 6.1 matrix-proof tests before deployment.
8. **Reviewers / invalidation:** protocol/security + risk. Reopen on any
   M0, M5, LP-artifact, vault-ID, or H-03 graph change.
9. **Approval language:** "I approve D-H04-13: the Section 6 asset matrix,
   its omission rule, its per-cell typed statuses, and its twelve proof
   obligations are the complete launch asset universe for the H-04
   manifest. Cell-level changes: none / as listed. — Owner, date."

### D-H04-17 — AAPL exposure and activation values

1. **Question:** Does the manifest carry the M0-approved cap formula
   `capAtomic = floor(D * 10^(18+8) / P8)` (round down; `D` = 5,000
   per-user and 25,000 global), the >110%/seven-day review rule, and
   typed-blocked cap integers until the pre-activation freeze?
2. **Alternatives:** (a) carry as stated (formula approved, integers
   blocked); (b) additionally pre-compute indicative integers labeled
   evidence-only (adds drift-confusion risk); (c) reopen M0 decision 12
   (outside this slice).
3. **Recommended:** (a).
4. **Risk of no decision:** the AAPL manifest rows cannot exist even as
   typed blockers, splitting the Track 8 M5 config bundle from the
   parameter authority.
5. **Smallest sufficient scope:** two derived-formula records
   (per-user/global) plus the review-cadence invalidation triggers. No
   contract field beyond the M5-bundle AAPL row.
6. **Blast radius:** Base — zero. Robinhood — Stock exposure bounds only.
7. **Accepted residual risk:** feed drift between freeze and activation,
   mitigated by the >110%/7-day rule and the two-person arithmetic review.
8. **Reviewers / invalidation:** risk + Track 8 owner. Reopen on AAPL
   identity or feed change (M0 decision 4 revalidation).
9. **Approval language:** "I approve D-H04-17: the manifest carries the M0
   cap formula and review cadence with cap integers typed-blocked until
   the pre-activation freeze. — Owner, date."

### D-H04-12 — PSM parameters and ordered activation gates

1. **Question:** Are the DP-07 architecture invariants (constructor
   `canMint=false`, `canRedeem=false`, `shouldAutoDeposit=true` then
   mandatory timelocked `setPsmShouldAutoDeposit(false)`; yield exactly
   `(0, zero)`) and the DP-09 redemption-first/GREEN-mint-last sequence
   encoded as manifest gates, with every PSM numeric (fees, caps,
   interval, allowlists, funding) left typed-blocked for the owner's
   loss/exposure envelope?
2. **Alternatives:** (a) encode gates now, numerics blocked; (b) omit the
   PSM from the launch graph entirely (the minimum-change register holds
   this open at the deployment-graph level while the M0 packet makes
   USDG/PSM a launch target — choosing (b) reopens M0 decision 7); (c)
   supply numerics now (rejected: no approved economic envelope exists).
3. **Recommended:** (a).
4. **Risk of no decision:** an unordered PSM activation path could grant
   GREEN mint authority before redemption is proved — the exact two-factor
   failure the integrated sequence prevents.
5. **Smallest sufficient scope:** manifest gate records only; no contract
   field — every PSM value is a deployment-only constructor/governance
   input, never a `Defaults` field.
6. **Blast radius:** Base — zero. Robinhood — GREEN supply integrity and
   reserve custody.
7. **Accepted residual risk:** issuer-side USDG controls per the M0/USDG
   accepted-risk register (pause/freeze/upgrade authority outside Ripe).
8. **Reviewers / invalidation:** protocol/security + treasury. Reopen on
   canonical USDG identity drift, feed change, or M0 decision 7 reopening.
9. **Approval language:** "I approve D-H04-12: DP-07 invariants and the
   DP-09 ordered activation sequence enter the manifest as gates; every
   PSM numeric remains typed-blocked pending my loss/exposure envelope.
   — Owner, date."

### D-H04-03 — Complete initial global flags and Teller initial pause

1. **Question:** What is the exact launch value of each of the ten
   `genConfig` booleans (individually: `canDeposit`, `canWithdraw`,
   `canBorrow`, `canRepay`, `canClaimLoot`, `canLiquidate`,
   `canRedeemCollateral`, `canRedeemInStabPool`, `canBuyInAuction`,
   `canClaimInStabPool`), of `isDaowryEnabled`, of `ripeBondConfig.canBond`,
   and of the Teller constructor `_shouldPause` (DP-20)?
2. **Alternatives per flag:** (a) enabled at launch; (b) disabled at launch
   with a named re-enable owner/runbook; (c) for `_shouldPause`: deploy
   paused with a named unpause step in the launch sequence, or deploy
   unpaused. Base parity (all enabled) is an alternative **set**, not a
   default.
3. **Recommended:** record each flag explicitly against the reviewed launch
   graph; recommend `canBond=False` (matches the disabled-bonds surface)
   and defer the other twelve selections to the owner with the Section 2
   interaction notes; no flag value is recommended by silence.
4. **Risk of no decision:** either enabled routes with no configured
   backing state or a launch-paused system nobody planned to unpause.
5. **Smallest sufficient scope:** thirteen boolean manifest records;
   `genConfig` members are contract fields (constructor seeding is the
   integrated mechanism — the manifest alone cannot reach MissionControl);
   `_shouldPause` is a deployment-only constructor input.
6. **Blast radius:** Base — zero. Robinhood — every user-facing action
   gate.
7. **Accepted residual risk:** flag flips are immediate governance actions
   with lite-signer disable, so a wrong enablement is quickly reversible;
   a wrong disablement delays launch functions without safety impact.
8. **Reviewers / invalidation:** protocol/security. Reopen on launch-graph
   changes or Teller deployment-plan changes (`B-H05-PLAN`).
9. **Approval language:** "I approve D-H04-03 with the following exact
   values — canDeposit: __, canWithdraw: __, canBorrow: __, canRepay: __,
   canClaimLoot: __, canLiquidate: __, canRedeemCollateral: __,
   canRedeemInStabPool: __, canBuyInAuction: __, canClaimInStabPool: __,
   isDaowryEnabled: __, canBond: __, Teller _shouldPause: __. — Owner,
   date."

### D-H04-18 — S3/S4/S5 deployment inputs

1. **Question:** Do the three integrated pins enter the manifest exactly
   as typed: S3 immutable floor `7_200` plus governed interval `0`
   (approved, final); S4 expected live cooldown exactly `0` as
   `deployment_assertion_only` with the verbatim statement "activation
   requires reopening S4"; S5 exact `0x64` discriminator semantics with
   the deployment binding typed-blocked?
2. **Alternatives:** (a) confirm the three pins as typed; (b) none other
   exists — all three are integrated owner decisions; H-04 merely types
   them, and any substantive change requires reopening S3/S4/S5.
3. **Recommended:** (a).
4. **Risk of no decision:** losing the typed pins would let a later slice
   guess or re-derive them outside their controlling authorities.
5. **Smallest sufficient scope:** three manifest records; no contract
   field — none of the three is a `Defaults` field, and adding one is
   prohibited (S4 explicitly bars a Defaults field, constructor argument,
   or setter).
6. **Blast radius:** Base — zero. Robinhood — zero state impact
   (assertions and constructor pins only).
7. **Accepted residual risk:** the accepted S4 procedural posture
   (governance technically retains the ability to queue a nonzero
   cooldown; H-08's pending-action rejections are the control).
8. **Reviewers / invalidation:** protocol/security. Reopen on S4 or S5
   reopening, or any Lootbox constructor-interface change.
9. **Approval language:** "I approve D-H04-18: the S3 floor/interval, S4
   zero-cooldown assertion with its verbatim reopening statement, and S5
   `0x64` discriminator semantics enter the manifest exactly as typed in
   DP-01 through DP-04. — Owner, date."

### D-H04-15 — Role, signer, and TrainingWheels symbolic inputs

1. **Question:** Is the symbolic role model recorded correctly (deployer
   setup-only authority; timelock/Safe governance; enumerated guardian
   powers; lite-signer disable-only emergency set; TrainingWheels target
   plus allowlist policy), with every concrete identity typed-blocked
   under `B-SECOPS-HANDOFF` (and the TrainingWheels policy/binding under
   `B-H04-PARAMS`)? Sub-question: is an empty `liteSigners` launch array
   acceptable (losing the fast-disable path), or must the SecOps identity
   set close before launch?
2. **Alternatives:** (a) symbolic model as recorded + SecOps set must
   close before launch; (b) symbolic model + accept an empty lite-signer
   array at launch; (c) reject the role model shape (returns to SecOps).
3. **Recommended:** (a) — preserves emergency fast-disable at launch.
4. **Risk of no decision:** unusable emergency response at launch, or an
   unreviewed authority surface.
5. **Smallest sufficient scope:** symbolic manifest records only.
   `liteSigners` and `trainingWheels` are `Defaults` interface fields, so
   their eventual concrete values are contract-seeded — which is exactly
   why the identities must close before generation, not why they should
   be guessed now.
6. **Blast radius:** Base — zero. Robinhood — the emergency-response and
   launch-restriction authority surface.
7. **Accepted residual risk:** lite signers can only disable, bounding
   abuse of a compromised lite key to availability, not funds or
   enablement.
8. **Reviewers / invalidation:** SecOps + protocol/security. Reopen on any
   role-freeze change or TrainingWheels policy change.
9. **Approval language:** "I approve D-H04-15 with alternative (a)/(b):
   the symbolic role model as recorded; lite-signer launch posture: __.
   — Owner, date."

### D-H04-08 — Timelocks, expiries, and staleness windows

1. **Question:** For each timelock class in the Section 5.2 table
   (token-HQ change, LocalGov, TimeLock inheritors, Contributor, HQ
   config/registry, AddressRegistry add/update/disable), which policy
   applies; is the expiry-headroom rule `expiration >= 61` adopted; is the
   registry shared-delay model (BN-019/020/021 one delay) accepted or must
   disable get its own delay; and what are the global `priceStaleTime` and
   per-feed staleness ceilings against the two 86,400-second heartbeats?
2. **Alternatives per class:** (a) `ceil /6` candidate counts; (b) Base
   counts retained (≈6× longer wall time on Robinhood — conservative,
   viable, must be explicit); (c) bespoke owner values.
3. **Recommended:** decide per class under D-H04-06's basis outcome; adopt
   the `>= 61` headroom rule unconditionally (it is profile-derived, not
   cadence-dependent).
4. **Risk of no decision:** governance latency and stale-price acceptance
   windows that differ from intent; every timelock constructor input stays
   blocked.
5. **Smallest sufficient scope:** one manifest record per class bound
   (BluePrint timelock keys are deployment inputs); `priceStaleTime` is
   the only `Defaults` field here (constructor seeding justification as in
   D-H04-03).
6. **Blast radius:** Base — zero. Robinhood — governance safety margins
   and oracle freshness acceptance.
7. **Accepted residual risk:** jump behavior can compress wall-time
   guarantees within a window; covered by the stress profiles and the
   headroom rule.
8. **Reviewers / invalidation:** protocol/security. Reopen on
   cadence-basis change or feed-heartbeat change.
9. **Approval language:** "I approve D-H04-08: per-class timelock policies
   as follows — [class: choice ...]; expiry headroom >= 61 adopted;
   registry shared-delay: __; priceStaleTime: __; per-feed ceilings: __.
   — Owner, date."

### D-H04-06 — Cadence basis per duration class

1. **Question:** For each duration class — timelocks, capacity/debt
   intervals, bond epochs, governance locks, auction windows — is the
   2s/12s (`ceil /6`, zero preserved) basis extended, declined in favor of
   Base-count retention, or replaced with bespoke values, given that the
   S3 approval is explicitly non-generalizable and each class must accept
   its wall-time range under repeat/`+1`/`+2/+4`/boundary-skip/`+60`
   behavior?
2. **Alternatives per class:** (a) extend the `/6` basis; (b) retain Base
   counts; (c) bespoke values with their own wall-time acceptance.
3. **Recommended:** none preselected — this is the cross-cutting economic
   acceptance the S3 approval deliberately withheld.
4. **Risk of no decision:** every block-denominated field in Sections 2, 3,
   and 5 stays blocked and Phase B cannot generate any of them.
5. **Smallest sufficient scope:** one recorded basis choice per duration
   class (five classes), consumed by the per-field conversions; no
   contract field of its own.
6. **Blast radius:** Base — zero. Robinhood — cross-cutting over every
   block-denominated parameter.
7. **Accepted residual risk:** the 2s/12s quanta are configuration
   assumptions, not chain guarantees; live-cadence monitoring must confirm
   the nominal.
8. **Reviewers / invalidation:** protocol + risk. Reopen if observed
   Robinhood cadence deviates materially from the 12-second nominal or the
   L1-increment behavior changes.
9. **Approval language:** "I approve D-H04-06 per class — timelocks: __;
   intervals: __; epochs: __; locks: __; auction windows: __ (each: /6
   basis, Base counts, or bespoke). — Owner, date."

### D-H04-04 — Debt caps and capacity values

1. **Question:** What are the launch values for `perUserDebtLimit`,
   `globalDebtLimit`, `minDebtAmount`, `numAllowedBorrowers`,
   `maxBorrowPerInterval`, `maxLtvDeviation`, `keeperFeeRatio`,
   `minKeeperFee`, `maxKeeperFee`, and `ltvPaybackBuffer`?
2. **Alternatives:** (a) owner-selected Robinhood values (Base values are
   labeled evidence-only candidates); (b) a disabled-borrowing launch
   (zero caps as typed legitimate zeros) as the safe-state fallback; (c)
   leave blocked (keeps borrowing out of generated launch defaults).
3. **Recommended:** none preselected; (b) must be explicitly chosen or
   rejected rather than implied.
4. **Risk of no decision:** the credit surface stays blocked; launch
   either has no borrowing or an unreviewed one.
5. **Smallest sufficient scope:** ten manifest records; contract fields
   (`genDebtConfig` seed) with the constructor-seeding justification of
   D-H04-03.
6. **Blast radius:** Base — zero. Robinhood — total credit exposure
   envelope.
7. **Accepted residual risk:** wrong values are governance-correctable via
   the timelocked Alpha setters before exposure accumulates.
8. **Reviewers / invalidation:** risk + treasury. Reopen on launch-graph
   or collateral-set changes.
9. **Approval language:** "I approve D-H04-04 with exact values —
   perUserDebtLimit: __, globalDebtLimit: __, minDebtAmount: __,
   numAllowedBorrowers: __, maxBorrowPerInterval: __, maxLtvDeviation: __,
   keeperFeeRatio: __, minKeeperFee: __, maxKeeperFee: __,
   ltvPaybackBuffer: __. — Owner, date."

### D-H04-07 — Dynamic-rate fields (CAD-001 family)

1. **Question:** What are the launch values for `minDynamicRateBoost`,
   `maxDynamicRateBoost`, `maxBorrowRate`, and the explicit inert
   `increasePerDangerBlock` (unit `rate_per_block_1e6`, runtime
   denominator 1,000,000), given that no Robinhood danger-number producer
   exists at launch (Curve omitted)?
2. **Alternatives:** (a) explicit inert value for the danger slope (raw
   `0` as typed legitimate zero, or an explicitly inert raw value) plus
   owner-selected boosts/max rate; (b) Base raw values labeled
   evidence-only; (c) zero boosts (flat-rate launch).
3. **Recommended:** decide the danger slope as an explicit inert value
   under (a); the deployment must additionally prove no Curve producer or
   PriceDesk registration exists.
4. **Risk of no decision:** the borrow-pricing family stays blocked.
5. **Smallest sufficient scope:** four manifest records; contract fields
   (same seed justification). The future raw `60` candidate remains gated
   on Curve re-enablement plus risk approval and is not part of this
   decision.
6. **Blast radius:** Base — zero. Robinhood — borrow pricing only; the
   danger term is inert without a producer.
7. **Accepted residual risk:** none while inert; a later producer
   registration reopens this decision before the term can act.
8. **Reviewers / invalidation:** risk/oracle. Reopen on any danger-number
   producer registration or S10 unit-metadata change (display only).
9. **Approval language:** "I approve D-H04-07 with exact values —
   minDynamicRateBoost: __, maxDynamicRateBoost: __, maxBorrowRate: __,
   increasePerDangerBlock (inert): __. — Owner, date."

### D-H04-09 — Rewards: attribution, allocations, emission, buckets

1. **Question:** Are the launch values `arePointsEnabled=False` and
   `ripePerBlock=0` carried as the only generation-bearing reward values;
   does the owner (i) select the fast-follow candidate set now as
   `fast_follow` manifest entries (allocation split conserving 100_00,
   `autoStakeRatio`, `autoStakeDurationRatio`,
   `stabPoolRipePerDollarClaimed`, emission per the exact `×6`
   rational-rate rule) or (ii) leave every fast-follow entry `unresolved`
   for the activation review; and what is `ripeAvailForRewards` at launch?
2. **Alternatives:** (i) record fast-follow candidates now (still
   activation-gated); (ii) leave all fast-follow entries unresolved; both
   with either a zero or a minimal `ripeAvailForRewards` bucket.
3. **Recommended:** launch values as integrated (M0-approved); no
   preselection between (i)/(ii); acknowledge that repeated block numbers
   attribute zero elapsed increments (an accepted property of the
   L1-increment clock).
4. **Risk of no decision:** the launch-disabled posture cannot enter the
   manifest, blocking every reward surface record.
5. **Smallest sufficient scope:** two approved launch records + the bucket
   + optional fast-follow records; contract fields (`rewardsConfig` and
   the Ledger bucket seed) with the constructor justification of
   D-H04-03.
6. **Blast radius:** Base — zero. Robinhood — RIPE emissions and points.
7. **Accepted residual risk:** brief post-incident accrual after a later
   activation, accepted by M0 with the rehearsed kill runbook (points
   disable fast; emission-zero timelocked).
8. **Reviewers / invalidation:** tokenomics + SecOps. Reopen at the
   separately reviewed reward activation (`B-REWARD-PROMOTION`).
9. **Approval language:** "I approve D-H04-09: launch rewards disabled
   exactly as integrated (points False, emission 0);
   ripeAvailForRewards: __; fast-follow entries: recorded now / left
   unresolved (choose). — Owner, date."

### D-H04-10 — Governance lock/boost terms and auction parameters

1. **Question:** What are the gov-vault lock durations (under the
   D-H04-06 locks class), `maxLockBoost`, `canExit`, `exitFee`,
   `assetWeight` per entry, `shouldFreezeWhenBadDebt`, the general auction
   `hasParams`/`startDiscount`/`maxDiscount`/`delay`/`duration`, and the
   auction-skip policy under jump behavior (minimum duration exceeding
   stress-jump headroom, or explicit acceptance of skippable auctions)?
2. **Alternatives:** (a) owner-selected values (Base economics labeled
   evidence-only); (b) auctions effectively disabled at launch (interacts
   with D-H04-03 flags); (c) leave blocked.
3. **Recommended:** none preselected; the skip-policy question must be
   answered explicitly whichever way.
4. **Risk of no decision:** governance staking economics and the
   liquidation-auction path remain blocked.
5. **Smallest sufficient scope:** per-field manifest records; contract
   fields (`ripeGovVaultConfigs`, `genAuctionParams`) with the seeding
   justification of D-H04-03.
6. **Blast radius:** Base — zero. Robinhood — governance-stake economics
   and liquidation auctions.
7. **Accepted residual risk:** wrong economics are governance-correctable;
   auction-window behavior under jumps is bounded by the stress profiles.
8. **Reviewers / invalidation:** governance + risk. Reopen on cadence or
   stability/vault graph changes.
9. **Approval language:** "I approve D-H04-10 with exact values — lock
   min/max: __/__, maxLockBoost: __, canExit: __, exitFee: __,
   assetWeight(s): __, shouldFreezeWhenBadDebt: __, auction
   hasParams/start/max/delay/duration: __/__/__/__/__, skip policy: __.
   — Owner, date."

### D-H04-11 — Bond and HR inclusion and values

1. **Question:** What is the launch posture and value set for BondRoom
   (`canBond`, payment asset, `amountPerEpoch`, `minRipePerUnit`,
   `maxRipePerUnit`, `maxRipePerUnitLockBonus`, `epochLength`,
   `shouldAutoRestart`, `restartDelayBlocks`), BondBooster bounds (DP-22),
   HR (`contribTemplate` binding, `maxCompensation`, the four seconds
   terms), and the `ripeAvailForHr`/`ripeAvailForBonds` buckets?
2. **Alternatives:** (a) fully disabled/inert bonds and HR at launch
   (`canBond=False`, `maxCompensation=0`, minimal buckets — the safe
   state); (b) owner-selected active values; (c) leave blocked.
3. **Recommended:** (a) as the launch posture, with all activation values
   deferred to their own release reviews.
4. **Risk of no decision:** the bond/HR families remain blocked; no
   treasury-emission surface can be generated.
5. **Smallest sufficient scope:** per-field records; contract fields
   (`ripeBondConfig`, `hrConfig`, buckets) with the seeding justification
   of D-H04-03; the bond payment asset has **no approved Robinhood
   identity** and stays blocked regardless.
6. **Blast radius:** Base — zero. Robinhood — treasury emissions (inert
   under (a)).
7. **Accepted residual risk:** disabled surfaces are inert; later
   enablement passes through `B-REWARD-PROMOTION` for any bond release.
8. **Reviewers / invalidation:** treasury. Reopen on bond-asset identity
   approval or HR activation planning.
9. **Approval language:** "I approve D-H04-11 with launch posture (a)/(b):
   canBond: __, maxCompensation: __, ripeAvailForHr: __,
   ripeAvailForBonds: __, remaining values: as listed / blocked.
   — Owner, date."

### D-H04-16 — Token initial supplies and Endaoment metadata

1. **Question:** What are the GREEN, RIPE, and sGREEN constructor
   initial-supply quantities (H-04-owned; recipients are SecOps-owned and
   not part of this decision), and what is the Endaoment WETH/native
   metadata binding (symbolic, DP-21)?
2. **Alternatives:** (a) zero initial supplies where the launch graph
   permits; (b) owner-selected nonzero quantities with treasury
   justification; (c) leave blocked.
3. **Recommended:** none preselected.
4. **Risk of no decision:** token deployment planning (H-05) lacks its
   typed supply inputs.
5. **Smallest sufficient scope:** three quantity records + one metadata
   record; manifest-only (constructor inputs, not `Defaults` fields).
6. **Blast radius:** Base — zero. Robinhood — initial token distribution.
7. **Accepted residual risk:** recipients are separately gated under
   `B-SECOPS-HANDOFF`, so a quantity decision alone moves nothing.
8. **Reviewers / invalidation:** treasury + SecOps. Reopen on token
   deployment-plan changes (`B-H05-PLAN`).
9. **Approval language:** "I approve D-H04-16: GREEN initial supply: __,
   RIPE: __, sGREEN: __; Endaoment native metadata: as recorded.
   — Owner, date."

### D-H04-14 — Priority vault and price-source lists

1. **Question:** What are the launch contents and order of
   `priorityLiqAssetVaults`, `priorityStabVaults`, and
   `priorityPriceSourceIds` (structural candidate exactly `[1]`)?
2. **Alternatives:** (a) empty lists where consumers tolerate them
   (`DefaultsLocal` precedent — must be explicit, not accidental); (b)
   structural candidates (`[1]` for price sources; stability entries per
   VaultBook row 1 once identities close); (c) leave blocked pending
   vault IDs/identities.
3. **Recommended:** (b) for `priorityPriceSourceIds`; (c) for the two
   vault lists until their `(vaultId, asset)` inputs exist.
4. **Risk of no decision:** liquidation/stability routing order and price
   fallback order are ungenerated.
5. **Smallest sufficient scope:** three list records; contract fields
   (three list selectors) with the seeding justification of D-H04-03.
6. **Blast radius:** Base — zero. Robinhood — liquidation/stability
   routing order and price-source fallback order.
7. **Accepted residual risk:** order mistakes are governance-correctable
   through the timelocked Alpha setters.
8. **Reviewers / invalidation:** protocol/security. Reopen on vault-ID or
   price-registry changes.
9. **Approval language:** "I approve D-H04-14: priorityPriceSourceIds:
   __; priorityLiqAssetVaults: __ / blocked; priorityStabVaults: __ /
   blocked. — Owner, date."

### D-H04-05 — Structural counts

1. **Question:** What are `perUserMaxVaults` and
   `perUserMaxAssetsPerVault`? (`numAllowedBorrowers` is decided in
   D-H04-04.)
2. **Alternatives:** (a) Base parity (5 / 15; cadence-free, low risk,
   recorded as an explicit selection, never a default); (b) other
   owner-selected counts.
3. **Recommended:** none preselected; (a) is viable.
4. **Risk of no decision:** `genConfig` cannot be generated.
5. **Smallest sufficient scope:** two records; contract fields
   (`genConfig`) with the seeding justification of D-H04-03.
6. **Blast radius:** Base — zero. Robinhood — UX/limit surface only.
7. **Accepted residual risk:** minimal; governance-correctable.
8. **Reviewers / invalidation:** protocol. Reopen on vault-graph changes.
9. **Approval language:** "I approve D-H04-05: perUserMaxVaults: __,
   perUserMaxAssetsPerVault: __. — Owner, date."

### D-H04-01 — Generator selection

1. **Question:** Which generator design implements deterministic Robinhood
   parameter generation: (a) the new network-free
   `scripts/params/generate_robinhood_defaults.py`; (b) a narrow
   parameterized refactor of `scripts/params/regenerate_defaults.py`; (c)
   checked-in manual source plus a deterministic parity verifier? And is
   the optional shared-formatter module (lifting the pure formatters into
   a new file imported by the new generator) approved as a seventh Phase B
   file, or is plain duplication inside the new generator selected?
2. **Alternatives:** (a), (b), (c) as analyzed with code evidence in
   Section 7.2; sub-option formatter-module versus plain duplication.
3. **Recommended:** (a) with plain duplication (no seventh file), per the
   brief's stated default and the Section 7.2 evidence (no consumer
   incompatibility exists; ~200 lines of mechanical formatting duplication
   versus refactoring the sole writer of a prohibited file).
4. **Risk of no decision:** Phase B has no generation path; the manifest
   cannot be projected into `DefaultsRobinhood.vy`.
5. **Smallest sufficient scope:** one new development-only tool file; the
   generator never runs in deployment or runtime paths; future changes are
   owned by this combined slice and re-trigger the two-build comparison
   and mutation tests.
6. **Blast radius:** Base — zero (prohibited files untouched; the Base
   generator remains byte-identical). Robinhood — tooling only.
7. **Accepted residual risk:** formatter duplication can drift
   stylistically from the Base formatter; the drift is cosmetic by
   construction and caught by parity tests.
8. **Reviewers / invalidation:** engineering/tooling + protocol/security.
   Reopen on any Section 7.3 generator-requirement change.
9. **Approval language:** "I approve D-H04-01: generator option
   (a)/(b)/(c) = __; formatter module: approved as seventh file / plain
   duplication. — Owner, date."

### D-H04-02 — Exact Phase B file ownership

1. **Question:** Is the Section 8 six-path boundary the exact and complete
   Phase B file ownership (to be reconfirmed against then-current
   worktrees at Phase B kickoff), with any additional file a stop
   condition requiring file-exact owner approval?
2. **Alternatives:** (a) approve the six paths; (b) approve six paths plus
   the optional formatter module from D-H04-01; (c) amend the list
   (file-exact).
3. **Recommended:** (a), or (b) if the formatter sub-option is selected in
   D-H04-01.
4. **Risk of no decision:** Phase B has no authorized write surface.
5. **Smallest sufficient scope:** the six named paths; nothing else.
6. **Blast radius:** Base — zero. Robinhood — bounded to the named files.
7. **Accepted residual risk:** none beyond the files themselves; a
   competing writer appearing is a stop condition, not a risk acceptance.
8. **Reviewers / invalidation:** owner directly. Reopen if any competing
   writer or ownership collision appears.
9. **Approval language:** "I approve D-H04-02: Phase B may touch exactly
   the Section 8 file set (six paths / six-plus-formatter). — Owner,
   date."

### D-H04-20 — Legitimate-zero and legitimate-false register

1. **Question:** Is the explicit register complete and correct — every
   zero/false the manifest may carry as a typed legitimate value: launch
   `ripePerBlock=0` and `arePointsEnabled=False`;
   `underscoreRegistry=empty(address)`; all six DebtTerms zeros on both
   LP rows (LTV zero M0-approved) and the structural DebtTerms zeros on
   GREEN/RIPE/sGREEN; AAPL's approved False cells (stab swap/redeem/claim
   and collateral redemption); launch-zero points allocations;
   `hrConfig.maxCompensation=0` (candidate); S3 governed interval `0`; S4
   cooldown `0` (assertion); `isNft=False` for exactly the six assets that
   receive `AssetConfig` entries (USDG receives none, so no USDG
   `AssetConfig` value of any kind is authorized by this register); plus
   any zero/false the owner selects in D-H04-03/04/07/10/11 (for example
   auction `delay=0`, bond `restartDelayBlocks=0`)?
2. **Alternatives:** (a) approve the register as listed; (b) approve with
   named additions/removals.
3. **Recommended:** (a).
4. **Risk of no decision:** every zero/false is schema-rejected as
   zero-as-missing and generation fails closed.
5. **Smallest sufficient scope:** the register itself; no contract change.
6. **Blast radius:** none directly on either chain; the register only
   permits typed zeros already decided elsewhere.
7. **Accepted residual risk:** a wrongly registered zero could mask a
   missing value — mitigated by requiring each member to cite its
   approving decision.
8. **Reviewers / invalidation:** protocol/security. Reopen whenever any
   ancestor decision changes a zero/false cell.
9. **Approval language:** "I approve D-H04-20: the legitimate-zero/false
   register as listed (additions/removals: none / as listed). — Owner,
   date."

### D-H04-21 — Omitted/blocked field register

1. **Question:** Are the omission set (Underscore integration;
   Curve/Pyth/Stork/RedStone-class sources; Base-only integrations; sGREEN
   CCIP permanently; `DefaultsBase`/`DefaultsLocal` as Robinhood
   artifacts) and the blocked set (the Section 12 registers, wrapping all
   18 H-03 blockers and all 48 symbolic inputs) together the complete
   non-launch surface?
2. **Alternatives:** (a) approve both registers; (b) approve with named
   changes.
3. **Recommended:** (a).
4. **Risk of no decision:** omitted/blocked distinctions cannot be
   schema-enforced; an omission could silently inherit an enabling
   default.
5. **Smallest sufficient scope:** the registers; no contract change.
6. **Blast radius:** none directly on either chain; enforcement lives in
   the schema and tests.
7. **Accepted residual risk:** none — the registers only restrict.
8. **Reviewers / invalidation:** protocol/security. Reopen on any H-03
   graph or cross-track gate change.
9. **Approval language:** "I approve D-H04-21: the omission register and
   blocked register as listed are the complete non-launch surface.
   — Owner, date."

## 12. Complete H-03 wrapping: blockers, symbolic inputs, and partition proof

Nothing in this section closes, flattens, reinterprets, or assigns a
concrete value to any blocker. All IDs below were extracted mechanically
from the integrated `config/robinhood_blueprint.py` public accessors
(`ROBINHOOD_BLUEPRINT.blockers`, `.symbolic_inputs`) at the Phase A
baseline; the raw row tables are deleted at import, so the frozen dataclass
graph is the only consumption path.

### 12.1 All 18 exact H-03 blocker IDs (each wrapped individually)

| H-03 blocker | Primary owner | Co-owners | Deadline gate | What it holds against H-04 | H-04 disposition |
| --- | --- | --- | --- | --- | --- |
| `B-S5-LEDGER` | OWN-S5 | OWN-SECOPS | before CM-008 enters an H-05 plan | the S5 deployment binding behind DP-04 and the Ledger-seed context of `I-LEDGER-DEFAULTS` | wrapped as `B-H04-S5-BIND`; semantics consumed, binding blocked |
| `B-H04-PARAMS` | OWN-H04 | OWN-ORACLE, OWN-SECOPS | before H-05 plan freeze | TrainingWheels binding, `specialStabPoolId`, MissionControl production values, every unresolved Defaults field | wrapped as `B-H04-VALUES`; closes only through the Section 11 owner decisions being recorded |
| `B-H05-PLAN` | OWN-H05 | OWN-H04 | before any migration execution | deployment identities (`I-GREEN`, `I-RIPE`, `I-SGREEN`, `I-USDG`, `I-WETH`), `I-TELLER-INITIAL-PAUSE` and `I-ENDAOMENT-NATIVE-METADATA` plan bindings (DP-12, DP-20, DP-21) | wrapped as `B-H04-PLAN-BINDINGS`; H-04 supplies typed values, H-05 owns the plan |
| `B-T8-M1` | OWN-T8 | OWN-SECOPS | before Track 8 M4 composed proof | the Stock exact-receipt lifecycle referenced by DP-11 (implementation integrated; official Phase B lifecycle open) | mapped in DP-11; no H-04 value depends on it beyond the Stock bundle |
| `B-T8-M2` | OWN-T8 | OWN-H05 | before Track 8 M5 activation | AAPL `vaultIds` (Section 6 cell), `I-STOCK-VAULT-ARTIFACT`/`I-STOCK-VAULT-SLOT` | wrapped as `B-H04-STOCK` |
| `B-T8-M3` | OWN-T8 | OWN-SECOPS | before Track 8 M4 composed proof | the credit-containment leg of the Stock bundle (DP-11) | wrapped as `B-H04-STOCK` |
| `B-T8-M4` | OWN-T8 | OWN-H09 | before Track 8 M5 activation | the composed-proof leg of the Stock bundle (DP-11) | wrapped as `B-H04-STOCK` |
| `B-T8-M5` | OWN-T8 | OWN-SECOPS, OWN-H09 | before Stock activation | every AAPL `B◦B-T8-M5` cell in Section 6; `I-ASSET-CONFIG-STOCK`, `I-AUCTION-CREDIT-STOCK`, `I-STABILITY-CONFIG` Stock enforcement (DP-13) | wrapped as `B-H04-STOCK` |
| `B-T8-FREEZE` | OWN-T8 | OWN-ORACLE, OWN-H04 | at final pre-activation freeze | AAPL identity cell and cap integers (DP-10, `D-H04-17`); `I-AAPL-TOKEN`, `I-AAPL-FEED`, `I-AAPL-RISK` | wrapped as `B-H04-STOCK` (freeze leg) |
| `B-ORACLE-FREEZE` | OWN-ORACLE | OWN-H04, OWN-H05 | before the oracle plan is frozen | stale-time ceilings beyond structure, LP oracles, `I-CHAINLINK-CORE`, `I-CHAINLINK-TIMELOCKS`, `I-AAPL-FEED`, `I-USDG-FEED`, both LP inputs' oracle legs (DP-17) | wrapped as `B-H04-ORACLE` |
| `B-LP-ARTIFACTS` | OWN-H04 | OWN-H05, OWN-ORACLE | before the launch plan can close | both LP identity cells and every artifact/pool/oracle/address input (DP-14, Section 6) | wrapped as `B-H04-LP`; a hard launch stop |
| `B-PSM-SEQUENCE` | OWN-H05 | OWN-H04, OWN-T8, OWN-SECOPS | before launch plan can close | executable PSM/global-mint ordering (DP-09); `I-PSM-CONFIG` sequence leg | wrapped as `B-H04-PSM-SEQ` |
| `B-REWARD-PROMOTION` | OWN-REWARDS | OWN-SECOPS | at `within_seven_day_separately_reviewed_reward_activation` | every fast-follow reward value's activation (DP-15); `I-REWARDS-PROMOTION`; bond-release gating of `I-BOND-ROOM-CONFIG`/`I-BOND-BOOSTER-CONFIG` (DP-22) | wrapped as `B-H04-REWARD-PROMO` |
| `B-T1-CCIP` | OWN-T1 | OWN-SECOPS | at `within_seven_day_separately_reviewed_ccip_promotion` | any CCIP-adjacent value — none exists in this slice by design (DP-16) | wrapped as `B-H04-CCIP` |
| `B-T1-TOOLCHAIN` | OWN-T1 | OWN-SECOPS | before any CCIP artifact is built | same (DP-16); also `I-VERIFY-EXPORT`'s toolchain leg | wrapped as `B-H04-CCIP` |
| `B-H08-PROOF` | OWN-H08 | OWN-H09 | after approved deployment fixtures exist | nothing upstream in H-04; H-08 **consumes** H-04's `deployment_assertion_only` records (S4 zero pin, Underscore-zero assertion) | mapped as downstream consumer; recorded to complete the partition |
| `B-H09-RELEASE` | OWN-H09 | OWN-SECOPS | before testnet or production activation | nothing upstream in H-04; H-09 consumes H-04 artifact hashes and the clock-profile test; gates `I-MANIFEST-HISTORY`, `I-VERIFY-EXPORT`, `I-RELEASE-PROOF` | mapped as downstream consumer; recorded to complete the partition |
| `B-SECOPS-HANDOFF` | OWN-SECOPS | OWN-H05 | before testnet or production handoff | signers, roles, TrainingWheels handoff, supply recipients (DP-18, DP-19; `D-H04-15`) | wrapped as `B-H04-ROLES` |

H-04 wrapper index — **exactly 12 active H-04 wrapper IDs** may satisfy a
current blocker entry (wrappers group, they never replace the exact IDs
above):

1. `B-H04-CADENCE` (the `D-H04-06` basis gate — H-04-internal, wraps no
   H-03 ID)
2. `B-H04-VALUES` ← {`B-H04-PARAMS`}
3. `B-H04-PLAN-BINDINGS` ← {`B-H05-PLAN`}
4. `B-H04-STOCK` ← {`B-T8-M1`, `B-T8-M2`, `B-T8-M3`, `B-T8-M4`,
   `B-T8-M5`, `B-T8-FREEZE`}
5. `B-H04-ORACLE` ← {`B-ORACLE-FREEZE`}
6. `B-H04-LP` ← {`B-LP-ARTIFACTS`}
7. `B-H04-PSM-SEQ` ← {`B-PSM-SEQUENCE`}
8. `B-H04-PSM-NUM` (Track 4 open numerics — H-04-internal)
9. `B-H04-REWARD-PROMO` ← {`B-REWARD-PROMOTION`}
10. `B-H04-CCIP` ← {`B-T1-CCIP`, `B-T1-TOOLCHAIN`}
11. `B-H04-ROLES` ← {`B-SECOPS-HANDOFF`}
12. `B-H04-S5-BIND` ← {`B-S5-LEDGER`}

Downstream-consumer rows (not wrappers) ← {`B-H08-PROOF`,
`B-H09-RELEASE`}.

**Retired historical identifier (thirteenth documented identifier, not an
admissible wrapper):** `B-H04-ENV` is retired, non-operative, and
**explicitly inadmissible as a current blocker entry** — the environment
question resolved factually (`VD-H04-ENV`, Section 13.1) and is no longer
a blocker. The documented-identifier arithmetic is: 12 active H-04
wrappers + 1 retired historical identifier = 13 documented identifiers.
No current DP row, A2/A6 disposition, symbolic-input row, manifest
example, decision, or blocker requirement uses `B-H04-ENV`; its only
occurrences in this document are this retirement record, the Section 7.4
blocker-rule rejection statement, and the Section 12.3
documented-identifier arithmetic.

### 12.2 All 48 exact H-03 symbolic-input IDs

Columns: primary owner → co-owners; deadline gate; blueprint status;
exact blocker IDs; where H-04 handles it (DP row, section, or decision).

| Symbolic input | Owner → co-owners | Deadline gate | Status | Blocker IDs | H-04 handling |
| --- | --- | --- | --- | --- | --- |
| `I-GREEN` | OWN-H05 → OWN-SECOPS | before H-05 execution | required | `B-H05-PLAN`, `B-SECOPS-HANDOFF` | DP-12; Section 6 GREEN identity cell |
| `I-RIPE` | OWN-H05 → OWN-SECOPS | before H-05 execution | required | `B-H05-PLAN`, `B-SECOPS-HANDOFF` | DP-12; Section 6 RIPE identity cell |
| `I-SGREEN` | OWN-H05 → OWN-H04 | before H-05 execution | required | `B-H05-PLAN` | DP-12; Section 6 sGREEN identity cell |
| `I-GREEN-INITIAL-SUPPLY` | OWN-H04 → OWN-H05, OWN-SECOPS | before H-05 plan freeze | required | `B-H04-PARAMS` | DP-19; `D-H04-16` |
| `I-GREEN-INITIAL-SUPPLY-RECIPIENT` | OWN-SECOPS → OWN-H04, OWN-H05 | before H-05 execution | required | `B-SECOPS-HANDOFF` | DP-19 (recipient leg; SecOps-owned) |
| `I-RIPE-INITIAL-SUPPLY` | OWN-H04 → OWN-H05, OWN-SECOPS | before H-05 plan freeze | required | `B-H04-PARAMS` | DP-19; `D-H04-16` |
| `I-RIPE-INITIAL-SUPPLY-RECIPIENT` | OWN-SECOPS → OWN-H04, OWN-H05 | before H-05 execution | required | `B-SECOPS-HANDOFF` | DP-19 (recipient leg) |
| `I-SGREEN-INITIAL-SUPPLY` | OWN-H04 → OWN-H05, OWN-SECOPS | before H-05 plan freeze | required | `B-H04-PARAMS` | DP-19; `D-H04-16` |
| `I-SGREEN-INITIAL-SUPPLY-RECIPIENT` | OWN-SECOPS → OWN-H04, OWN-H05 | before H-05 execution | required | `B-SECOPS-HANDOFF` | DP-19 (recipient leg) |
| `I-GOV-HANDOFF` | OWN-SECOPS → OWN-H05 | before testnet/production handoff | required | `B-SECOPS-HANDOFF` | DP-18; `D-H04-15` role model |
| `I-CLOCK-PARAMS` | OWN-H04 → OWN-H05, OWN-SECOPS | before H-05 plan freeze | required | `B-H04-PARAMS` | DP-05; `D-H04-06`/`D-H04-08` |
| `I-TRAINING-WHEELS` | OWN-H04 → OWN-SECOPS | before testnet | required | `B-H04-PARAMS`, `B-SECOPS-HANDOFF` | DP-18; Section 2.2.9; `D-H04-15` |
| `I-LEDGER-BLOCK-SOURCE` | OWN-S5 → OWN-SECOPS | before CM-008 enters H-05 | blocked | `B-S5-LEDGER` | DP-04 (S5-owned; H-04 consumes semantics only) |
| `I-LEDGER-DEFAULTS` | OWN-H04 → OWN-S5, OWN-H05 | before CM-008 enters H-05 | blocked | `B-S5-LEDGER`, `B-H04-PARAMS` | Section 2.2.3; `D-H04-09`/`D-H04-11` buckets |
| `I-RH-DEFAULTS` | OWN-H04 → OWN-H05 | before H-05 plan freeze | required | `B-H04-PARAMS` | the entire artifact; `D-H04-01`/`D-H04-02` |
| `I-TELLER-INITIAL-PAUSE` | OWN-H04 → OWN-H05, OWN-SECOPS | before Teller enters the H-05 plan | blocked | `B-H04-PARAMS`, `B-H05-PLAN` | DP-20; `D-H04-03` |
| `I-CHAINLINK-CORE` | OWN-ORACLE → OWN-H04, OWN-H05 | before oracle plan freeze | required | `B-ORACLE-FREEZE` | DP-17 (oracle-owned; H-04 consumes) |
| `I-CHAINLINK-TIMELOCKS` | OWN-H04 → OWN-ORACLE, OWN-H05 | before oracle plan freeze | required | `B-H04-PARAMS`, `B-ORACLE-FREEZE` | DP-05/DP-17; `D-H04-08` |
| `I-AAPL-TOKEN` | OWN-T8 → OWN-ORACLE, OWN-H04 | final pre-activation freeze | required | `B-T8-FREEZE` | Section 6 AAPL identity; `D-H04-17` |
| `I-AAPL-FEED` | OWN-ORACLE → OWN-T8, OWN-H04 | final pre-activation freeze | required | `B-T8-FREEZE`, `B-ORACLE-FREEZE` | DP-10 (oracle-owned) |
| `I-AAPL-RISK` | OWN-T8 → OWN-H04, OWN-ORACLE, OWN-SECOPS | before M5 activation | blocked | `B-H04-PARAMS`, `B-T8-FREEZE`, `B-T8-M5` | DP-10/DP-11; `D-H04-17` |
| `I-STOCK-VAULT-ARTIFACT` | OWN-T8 → OWN-SECOPS | before M2/M5 | blocked | `B-T8-M2` | DP-11 (Track 8-owned) |
| `I-STOCK-VAULT-SLOT` | OWN-T8 → OWN-H05 | before M5/H-05 plan | blocked | `B-T8-M2`, `B-H05-PLAN` | DP-11; Section 6 AAPL `vaultIds` cell |
| `I-USDG` | OWN-T8 → OWN-H05, OWN-ORACLE | before PSM/LP plan freeze | required | `B-H05-PLAN` | DP-12; Section 6 USDG `NA` column |
| `I-USDG-FEED` | OWN-ORACLE → OWN-T8, OWN-H04 | final pre-activation freeze | required | `B-ORACLE-FREEZE` | DP-17 (oracle-owned) |
| `I-PSM-CONFIG` | OWN-H04 → OWN-T8, OWN-SECOPS | before PSM staging | required | `B-H04-PARAMS`, `B-PSM-SEQUENCE` | DP-07/DP-08/DP-09; `D-H04-12` |
| `I-ECHO-TIMELOCKS` | OWN-H04 → OWN-H05, OWN-SECOPS | before SwitchboardEcho deployment | required | `B-H04-PARAMS` | DP-05; `D-H04-08` |
| `I-WETH` | OWN-H04 → OWN-H05, OWN-ORACLE | before LP/Endaoment plan freeze | required | `B-H05-PLAN` | DP-12 (constituent-only identity) |
| `I-GREEN-USDG-LP` | OWN-H04 → OWN-H05, OWN-ORACLE | before launch plan close | blocked | `B-LP-ARTIFACTS`, `B-ORACLE-FREEZE` | DP-14; Section 6 LP column; `D-H04-13` |
| `I-RIPE-WETH-LP` | OWN-H04 → OWN-H05, OWN-ORACLE | before launch plan close | blocked | `B-LP-ARTIFACTS`, `B-ORACLE-FREEZE` | DP-14; Section 6 LP column; `D-H04-13` |
| `I-ASSET-CONFIG-NONSTOCK` | OWN-H04 → OWN-T8, OWN-ORACLE | before M5/H-05 plan freeze | required | `B-H04-PARAMS` | Section 6 non-Stock columns; `D-H04-13` |
| `I-ASSET-CONFIG-STOCK` | OWN-T8 → OWN-H04, OWN-ORACLE | before M5 activation | blocked | `B-H04-PARAMS`, `B-T8-M5` | Section 6 AAPL column; `D-H04-17` |
| `I-STABILITY-CONFIG` | OWN-H04 → OWN-T8 | before M5/H-05 plan freeze | required | `B-H04-PARAMS`, `B-T8-M5` | DP-13; `specialStabPoolId` row; `D-H04-13` |
| `I-RIPE-GOV-CONFIG` | OWN-H04 → OWN-H05 | before H-05 plan freeze | required | `B-H04-PARAMS` | DP-13; Section 2.2.6; `D-H04-10` |
| `I-AUCTION-CREDIT-NONSTOCK` | OWN-H04 → OWN-T8 | before M5/H-05 plan freeze | required | `B-H04-PARAMS` | Sections 2.2.2/5.5; `D-H04-04`/`D-H04-07`/`D-H04-10` |
| `I-AUCTION-CREDIT-STOCK` | OWN-T8 → OWN-H04, OWN-SECOPS | before M4/M5 | blocked | `B-T8-M1`, `B-T8-M2`, `B-T8-M3`, `B-T8-M4`, `B-T8-M5` | DP-11 (Track 8-owned) |
| `I-LOOTBOX-CONFIG` | OWN-H04 → OWN-REWARDS | before H-05 plan freeze | required | `B-H04-PARAMS` | DP-01/DP-02; `D-H04-18` |
| `I-REWARDS-PROMOTION` | OWN-REWARDS → OWN-SECOPS, OWN-H04 | within_seven_day_separately_reviewed_reward_activation | deferred | `B-REWARD-PROMOTION` | DP-15; `D-H04-09` fast-follow leg |
| `I-BOND-ROOM-CONFIG` | OWN-H04 → OWN-REWARDS | before any bond release | deferred | `B-H04-PARAMS`, `B-REWARD-PROMOTION` | Section 2.2.4; `D-H04-11` |
| `I-BOND-BOOSTER-CONFIG` | OWN-H04 → OWN-REWARDS | before any bond release | deferred | `B-H04-PARAMS`, `B-REWARD-PROMOTION` | DP-22; `D-H04-11` |
| `I-HR-TIMELOCKS` | OWN-H04 → OWN-SECOPS | before any HR release | deferred | `B-H04-PARAMS` | DP-05; `D-H04-08`/`D-H04-11` |
| `I-ENDAOMENT-NATIVE-METADATA` | OWN-H04 → OWN-H05, OWN-SECOPS | before Endaoment deployment | required | `B-H04-PARAMS`, `B-H05-PLAN` | DP-21; `D-H04-16` |
| `I-CCIP-ARTIFACTS` | OWN-T1 → OWN-SECOPS | within_seven_day_separately_reviewed_ccip_promotion | deferred | `B-T1-CCIP`, `B-T1-TOOLCHAIN` | DP-16 (Track 1-owned; nothing enters this slice) |
| `I-CCIP-REGISTRATION` | OWN-T1 → OWN-SECOPS | within_seven_day_separately_reviewed_ccip_promotion | deferred | `B-T1-CCIP` | DP-16 (Track 1-owned) |
| `I-MIGRATION-PLAN` | OWN-H05 → OWN-H04 | before any plan execution | blocked | `B-H05-PLAN` | Section 1.7 (H-05 consumer; H-04 supplies typed values) |
| `I-MANIFEST-HISTORY` | OWN-H05 → OWN-H09 | before rehearsal | blocked | `B-H05-PLAN`, `B-H09-RELEASE` | Section 1.7 (H-05/H-06 boundary; distinct from H-04's parameter manifest) |
| `I-VERIFY-EXPORT` | OWN-H09 → OWN-H05, OWN-T1 | before verification | blocked | `B-H09-RELEASE`, `B-T1-TOOLCHAIN` | Section 1.7 (H-09 consumer of artifact hashes) |
| `I-RELEASE-PROOF` | OWN-H09 → OWN-H08, OWN-SECOPS | before testnet/production activation | blocked | `B-H08-PROOF`, `B-H09-RELEASE` | Section 1.7 (H-09 consumer; includes the clock-profile test) |

### 12.3 Mechanical partition proof

Method: the 18 blocker IDs and 48 symbolic-input IDs were enumerated from
the blueprint's public accessors; each ID was then counted in this
document's Sections 12.1/12.2 register rows. Every ID appears as **exactly
one register row** (IDs may additionally be *referenced* elsewhere in the
document; the registers are the partition).

| Universe | Blueprint count | Register rows | Row-per-ID check |
| --- | --- | --- | --- |
| H-03 blockers (`B-*`) | 18 | 18 (Section 12.1) | each of the 18 IDs heads exactly one row; none compressed, none omitted, none duplicated |
| H-03 symbolic inputs (`I-*`) | 48 | 48 (Section 12.2) | each of the 48 IDs heads exactly one row; the 23 OWN-H04-owned inputs map to a DP row or decision; the 25 non-H-04-owned inputs map to their consuming DP/section with their owning track named |
| H-04 deployment-only inputs (`DP-*`) | 22 (Section 3) | 22 | every DP row cites its exact symbolic-input and blocker IDs |
| Wrapper index | 12 active H-04 wrappers + 1 retired historical identifier (`B-H04-ENV`) = 13 documented identifiers; plus 2 downstream-consumer rows | — | every active wrapper's member set is listed explicitly in Section 12.1; the union of the active member sets plus the two downstream rows equals the 18-blocker universe with no overlap; the retired identifier wraps nothing and is inadmissible as a current blocker |

Blocker-ID reference floor (each exact ID appears at least in its register
row and every compressed form has been expanded): `B-S5-LEDGER`,
`B-H04-PARAMS`, `B-H05-PLAN`, `B-T8-M1`, `B-T8-M2`, `B-T8-M3`, `B-T8-M4`,
`B-T8-M5`, `B-T8-FREEZE`, `B-ORACLE-FREEZE`, `B-LP-ARTIFACTS`,
`B-PSM-SEQUENCE`, `B-REWARD-PROMOTION`, `B-T1-CCIP`, `B-T1-TOOLCHAIN`,
`B-H08-PROOF`, `B-H09-RELEASE`, `B-SECOPS-HANDOFF`.

Phase B cannot begin while any value included in the contract or manifest is
pending, recommended/open, blocked, provisional, or conditional; copied from
Base merely because no Robinhood value exists; or converted by an unapproved
cadence ratio.

## 13. Phase A validation results

All runs executed in the Phase A candidate Git worktree at baseline
`e39815d710ecfaf8bbeea54cabe8ae8d553a2740`, with private external basetemp
directories and a private bytecode-cache root (`PYTHONPYCACHEPREFIX`)
outside the repository, and with pytest's cache provider disabled so no new
cache was written into the worktree.

### 13.1 `VD-H04-ENV` — exact-lock validation disposition (factual; not an owner decision)

**H-01 passes 45 tests in a fresh private mode-`0700` CPython 3.12.0
environment installed from the exact integrated lock.** The environment was
built as a new venv in a mode-`0700` directory outside the repository and
installed offline from a locally assembled wheelhouse of the exact 92
pinned distributions (fetched per-pin from the PyPI CDN with a working HTTP
client after python-process TLS to `pypi.org` was observed to hang on this
host while `curl` succeeded — an execution-host network condition, recorded
here for reproducibility). `pip check` reports no broken requirements, and
`pip list --format=freeze` compared against the lock's 92 pins (extras
markers normalized, `pip` itself excluded) produced an **empty diff** — the
environment's installed set equals the integrated lock exactly.

The earlier collection failure of the dependency-gate module was an
**active-environment mismatch** — the slimmed `ripe-lite` environment lacks
`ipython==9.8.0`, which `tests/deployment/test_dependency_gate.py:19`
imports at module level. It was not a lock, repository, or reproducibility
defect, and it is not an owner exception: the gate reproduces exactly from
the lock. No blocker or owner decision exists for this item.

### 13.2 Fresh exact-lock environment results

| Suite | Command target | Result |
| --- | --- | --- |
| H-01 dependency gate | `tests/deployment/test_dependency_gate.py` | **45 passed** (2.41s) |
| H-02 complete three-file boundary | `python -m pytest tests/deployment/test_network_profiles.py tests/deployment/test_base_profile_regression.py tests/deployment/test_secret_handling.py -q` | **99 passed** (11.90s) |
| S1 clock profiles | `tests/clock` | **57 passed** (24.67s) |
| S2 checker | `scripts/check_block_clock_inventory.py --check` | **`CLOCK_INVENTORY_OK`** — schema 1; production 99 occurrences / 94 lines / 17 files; 32 BN IDs; 1 indirect (CAD) ID; 474 cadence candidates; 58 seconds-unit candidates; 11 timestamp IDs; 4 mixed-clock functions; 94 vyper paths |
| S2 inventory tests | `tests/inventory/test_block_clock_inventory.py` | **76 passed** (32.54s) |
| H-03 targeted | `tests/deployment/test_robinhood_blueprint.py` + `test_robinhood_omissions.py` | **104 passed** (25.73s) |
| Base-history inventory test | `tests/deployment/test_base_profile_regression.py::test_committed_base_history_inventory_is_unchanged` | **1 passed** (0.05s) — **in the actual candidate Git worktree**, no skip |

### 13.3 Prior-run archive results (labeled; execution context stated)

These earlier results were produced in the **active `ripe-lite`
environment** during the rejected candidate's preparation and are retained
as archive context, distinguished from the Section 13.2 runs actually
executed for this corrected candidate:

- Collection: 3,158 selected / 3,300 collected / 142 fork-deselected, zero
  errors (dependency-gate module excluded for the `ripe-lite` reason above).
- Serial full suite: **3,157 passed, 1 skipped, 142 deselected** (367.42s).
  That run executed as a **detached background process in which the skip
  guard's `git rev-parse --is-inside-work-tree` probe did not report a Git
  worktree**, so `test_committed_base_history_inventory_is_unchanged` was
  the sole skip, with reason "requires a Git worktree" — an
  execution-context artifact, not a repository, dependency, or product
  blocker. The same test **passes in the actual candidate Git worktree**
  (Section 13.2). No other test skipped.
- The sandboxed harness initially blocked titanoboa compilation with
  `PermissionError: [Errno 1]`; compile-bearing suites were rerun outside
  the sandbox, and the two previously erroring collection modules
  (`tests/config/test_switchboard_delta.py`,
  `tests/core/humanResources/test_hr_contributor.py`) collect and pass in
  the full run.

### 13.4 Placeholder and network statement (exact)

A clearly labeled non-secret placeholder string was exported as
`ETHERSCAN_API_KEY` for test invocation. The value **is consumed**: the
session fixture `set_etherscan` (`tests/conf_env.py:104-110`) passes it to
`boa.set_etherscan(...)` as local Boa configuration whenever the `env`
fixture is used. That configuration caused **no RPC, no authenticated
access, no signing, no deployment, no transaction, no secret use, and no
external-state action**: under the default `--fork=local` mode all 142
fork-marked tests are deselected and the local path runs entirely in-memory
(`boa.set_env(Env())`). No secret store was read at any point.

## 14. Checkpoint confirmations

- Exactly one repository path was created across Phase A and this Gate 1
  correction: `docs/chains/rh/evidence/robinhood-defaults-parameters-phase-a.md`.
  No other tracked or untracked repository path was added, modified,
  staged, or deleted.
- No implementation, production source, manifest, generator, or test file
  was created; no contract change, ABI change, migration, deployment,
  configuration, governance action, signing, or transaction occurred; no
  RPC, fork, account, or secret access occurred; no external state was
  mutated.
- No production value was guessed: every address, role, oracle, cap, LTV,
  fee, rate, cadence value, reward value, PSM numeric, TrainingWheels
  binding, `specialStabPoolId`, and Stock/M2-M5 input remains typed
  `blocked`/`unresolved` under a named decision or blocker.
- **Every owner decision (all twenty of D-H04-01 through D-H04-18,
  D-H04-20, D-H04-21) remains open.** Nothing in this document approves,
  checks, or resolves any of them.
- The corrected candidate is left **unstaged and uncommitted** for
  complete-file independent Gate 1 re-review.
- **H-04 Phase B remains unauthorized.** A recommendation, owner-decision
  request, or Phase A approval is not Phase B approval; Phase B additionally
  requires reverified file ownership and a separate file-exact owner
  implementation authorization on a then-current reviewed baseline.

## 15. Ignored-state disclosure at freeze

Recomputed at the final freeze of this corrected candidate (ignored state
is environment-produced and may change; these are the exact current
numbers, not repetitions of prior observations):

| Measure | Count |
| --- | --- |
| Ignored files (`git ls-files --others --ignored --exclude-standard`) | **140** |
| Unique directories containing those files | **32** |
| Collapsed top-level ignored entries (`git status --porcelain --ignored`) | **31** — 29 `__pycache__/` directories (1 under `config/`, 3 under `scripts/`, 25 under `tests/`), plus `.pytest_cache/` and `.hypothesis/` |
| Files under `__pycache__/` paths | 119 |
| Files under `.pytest_cache/` + `.hypothesis/` | 21 |
| `.claude/` | present on disk, matched by `.gitignore:10`, contains **zero files** (one empty session subdirectory), therefore invisible to git listings |

None of this ignored material was deleted, modified, or inspected for
content; `.claude/` and any other user-owned material remain untouched and
unclaimed. All new validation in this correction used private external
basetemp and bytecode/cache roots, so it added no ignored state to the
worktree. **Every ignored artifact is outside the one-file candidate
identity**: the candidate is exactly the single untracked evidence file,
and the identities recorded in the Gate 1 handoff are computed over that
file alone.

## 16. Owner approval record — Group 1 (2026-07-28)

This section is an append-only approval-provenance amendment. The complete
Gate 1-approved evidence is preserved as an **exact byte prefix** of this
file: bytes 1 through 173,400 are byte-identical to the approved candidate
with evidence SHA-256
`0da6abd224347fd71789924bfe34d0936cf1e0abcc1222a4280ebfbedb37082b`,
Git blob `fedb94317892c2850a05d76c4b57d3030004b7a0`, creation-patch SHA-256
`a75163972c358e0f54d923a29fef4ecad9f523d1ef46b2dc7e5ddd75b871ba8e`
(mechanical check: `head -c 173400 <this file> | shasum -a 256` reproduces
the approved evidence SHA-256). This section is the only addition; no
technical recommendation, alternative, inventory, matrix, schema, blocker,
symbolic input, validation result, or non-Group-1 decision byte was
altered.

### 16.1 Approvals recorded

On **2026-07-28** the owner approved the four Group 1 decisions of the
Section 11 packet, against the exact candidate identity above:

- **D-H04-01 — Generator selection: APPROVED, option (a).** A new
  network-free `scripts/params/generate_robinhood_defaults.py` generator
  using plain formatter duplication inside that file. No shared formatter
  module and no seventh Phase B file are approved.
- **D-H04-02 — Exact Phase B file ownership: APPROVED.** The exact
  six-path Phase B file ceiling stated in Section 8. Any seventh path,
  competing writer, ownership collision, or additional required artifact
  is a stop condition requiring new file-exact owner authorization.
- **D-H04-20 — Legitimate-zero and legitimate-false register: APPROVED
  exactly as reviewed**, with no additions or removals. It authorizes no
  USDG `AssetConfig` value because USDG receives no ordinary `AssetConfig`
  entry.
- **D-H04-21 — Omitted and blocked registers: APPROVED exactly as
  reviewed** as the complete non-launch surface. This approval closes no
  blocker and supplies no concrete production value.

### 16.2 Lifecycle effect (dated supersession of status statements only)

As of 2026-07-28, the four Group 1 decisions above carry status
**approved** with this section as their approval provenance; their
Section 11 bodies remain the approved decision content, and only their
open-status presentation (including the blank approval-language templates
for these four) is superseded by this record. Where the Section 11
preamble, Section 13, or Section 14 states that every owner decision
remains open, that statement now holds for **the sixteen remaining open
decisions, D-H04-03 through D-H04-18**; it is superseded by this dated
record for the four Group 1 decisions only. Every unresolved concrete
value remains typed `blocked`, exactly as before.

### 16.3 What this approval does not authorize

- H-04 Phase B implementation (a separate file-exact owner implementation
  authorization on a then-current reviewed baseline remains required);
- any Group 2 or Group 3 value;
- closing any H-03 or cross-track blocker (all 18 H-03 blockers remain
  exactly as registered in Section 12);
- production addresses, identities, roles, signers, oracle values, caps,
  rates, fees, cadence values, supplies, PSM numerics, rewards, or
  deployment bindings (`signers` excludes signer identity selection,
  approval, or binding; the separate `signing` item below excludes the act
  of producing a signature);
- staging, commit, push, merge, deployment, configuration, migration,
  RPC, signing, broadcasting, or external-state activity.

## 17. Owner approval record — Group 2 proposal R2 (2026-07-28)

This section is a bounded, append-only approval-provenance amendment. The
complete evidence through Section 16 is preserved as an **exact byte prefix**
of this file: bytes 1 through 176,874 are byte-identical to the pre-amendment
evidence with SHA-256
`73a94a8bf8d8635862c16648b943c6a4d8d401d1c5d99f6886952d811dd743d2`
and Git blob `584580d501d291256b1b3b055a6dae31a0666a95`. That prefix is 2,407
lines. No historical evidence, technical recommendation, inventory, matrix,
schema, blocker, symbolic input, validation result, or prior approval byte was
altered.

### 17.1 Controlling proposal identity and supersession

On **2026-07-28** the owner approved the complete corrected H-04 Group 2
proposal R2 as the controlling owner direction, bound to this exact artifact:

- file: `h04-group2-proposal-R2.md`;
- SHA-256:
  `05069136bf2bcbbd1a0dcc698fe84c31ba54cb1daaa9d4587e143fbc54f71e0e`;
- size: 39,944 bytes;
- length: 486 lines;
- baseline `rh`:
  `cca60bb85c772c977bb9fb62c1c6c5252c3a1438`;
- baseline tree:
  `161fb828f3bbf4cb12596a5dfaf6c9bf1e153381`.

R2 supersedes the reviewed R1 proposal at SHA-256
`e2f04ccb1e51d025a0e3d0cc06316333f1d5ade80227736fc5fe27b1fb571556`.
R2 is controlling wherever it expands or clarifies R1; the abbreviated R1
language is not approval authority in those places.

### 17.2 Approvals recorded

Exactly these eleven Group 2 decisions are **APPROVED**, with their complete
values, statuses, classifications, risks, tests, invalidation conditions, and
implementation treatment controlled by the exact R2 artifact in Section 17.1:

- D-H04-03;
- D-H04-04;
- D-H04-05;
- D-H04-06;
- D-H04-07;
- D-H04-08;
- D-H04-09;
- D-H04-10;
- D-H04-11;
- D-H04-13;
- D-H04-14.

No other decision is approved by this Group 2 record.

### 17.3 Explicit owner acknowledgments

This approval includes all of the following:

1. The ten general capability flags retain the reviewed Base values and seed
   `true` behind a paused Teller. Teller unpause remains a separately
   controlled activation edge.
2. The Base-derived 20,000 / 200,000 GREEN debt caps are retained. They remain
   inert while every applicable asset has zero LTV, and any later LTV or Stock
   activation remains separately owner-gated.
3. The reviewed block-duration fields use the approved Robinhood `/6`
   conversion where applicable. Seconds-domain fields and zero/absolute values
   remain unconverted.
4. D-H04-08 includes the complete R2 deployment-input enumeration:
   SwitchboardAlpha stale-window immutable bounds of 300 / 604,800 seconds;
   ChainlinkPrices `_defaultStaleTime` of 86,400 seconds; and the reviewed
   shared AddressRegistry bounds policy, including its conservative increase
   in the minimum wall-time bounds for some registries.
5. The 86,400-second price-staleness ceiling is accepted despite having no
   nominal heartbeat-delay margin. Late updates therefore fail closed until a
   fresh price is available.
6. The reviewed Base governance-vault and auction economics are accepted as
   initial Robinhood defaults: 200% boost; 80% early-exit fee; 100% / 150%
   weights; bad-debt freeze; 1% to 50% auction discount; zero auction delay;
   and the reviewed Robinhood-converted auction duration.
7. `increasePerDangerBlock=10` is retained. It remains inert while the
   reviewed danger-producing source slot is empty. Registration of such a
   source invalidates that inertness assumption and requires fresh review.
8. Reward allocations remain zero and promotable through existing governed
   setters.
9. The inert bond representation and five of six reviewed HR values are
   constructor-valid but cannot be reproduced through their current governed
   setters. This existing Base seed/setter mismatch is accepted as recorded in
   R2 and does not authorize bond or HR activation.
10. The five reviewed asset tuples and the reviewed priority-list policy are
    accepted exactly as R2 specifies. No blocked identity or value may be
    represented with an invented address, placeholder, or zero substitution.
11. Identity-bearing asset rows and stability-list entries must remain omitted
    from generated Vyper until their identities are bound. The typed manifest
    must retain their blocked/deferred provenance.
12. `DefaultsRobinhood.vy` is not currently renderable or compilable as a
    final deployment artifact because required identities, `trainingWheels`,
    and `liteSigners` remain unresolved. The generator must fail closed rather
    than substitute zero or placeholders.
13. This approval does not select a zero-backing settlement or bad-debt
    policy, does not activate AAPL/Stock, and does not change the separately
    parked Deleverage or CCIP work.

### 17.4 Decision lifecycle and exact status counts

The existing Group 1 approvals for **D-H04-01, D-H04-02, D-H04-20, and
D-H04-21 remain approved and unchanged**. Together with the eleven approvals
in Section 17.2, the exact operative decision status is:

- **15 approved:** D-H04-01 through D-H04-11, D-H04-13, D-H04-14,
  D-H04-20, and D-H04-21;
- **5 open:** exactly D-H04-12 and D-H04-15 through D-H04-18;
- **1 retired and non-operative historical ID:** D-H04-19.

Thus the twenty genuine owner decisions comprise exactly 15 approved and 5
open decisions. D-H04-19 remains retired, is not counted among the twenty
genuine decisions, and supplies no authority.

Where Sections 11, 13, 14, or 16 describe the Group 2 decisions as open, that
status presentation is superseded by this dated record only for the eleven
decision IDs in Section 17.2. Their historical bodies remain evidence; the
exact R2 artifact is the controlling approved direction. The five decisions
listed as open above remain open exactly, with no inferred value.

### 17.5 Scope and phase boundary

This approval-provenance amendment does not:

- begin or authorize H-04 Phase B;
- modify or authorize modification of any source, generator, manifest, test,
  migration, ABI, configuration, or second documentation file;
- infer or bind any unresolved address, signer, role, oracle, feed, identity,
  supply, PSM value, TrainingWheels binding, Stock activation value, or S5
  binding;
- close any H-03 or cross-track blocker;
- authorize staging, commit, push, integration, merge, deployment,
  configuration, migration, signing, transaction, activation, or external
  state change.
