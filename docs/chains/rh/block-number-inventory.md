# Robinhood Phase-0 block-number inventory

> **30 July 2026 currentness overlay:** The checked inventory now reflects the
> corrected PR #61 integration at
> `ad831669943ccfe7b9ed57454995dfce51630a66`: 99 production occurrences, 94
> lines, 17 files, historical S5 fingerprint
> `924a559075d5b96bcac3f73d28390deee3b436fe5500adc4fb6bf769282217b4`,
> and current post-S5 fingerprint
> `07fc837ee5c9c56a4cf979c64e3d678753eeb6c263e4100d7a1f0cb4704f2122`.
> The historical ledger below remains evidence; `status.yaml` is current
> authority. Nothing is deployed or active.

**Status:** Complete analysis; BN-002 and BN-025 directions are recorded;
remaining recommendations and owner decisions are unapproved

**Track branch:** `rh-track-3-phase-0-inventory`

**Pinned starting commit:** `51a7a3996f5fec40efd554d1b025aaa9c2ed4ea2` (`3 tracks`)

**Planning baseline:** `1bb8bd5b8837a06c818c3fb9e7b599b5dd29f2b1`

**Audit timestamp:** `2026-07-23T19:59:58Z`

**Revision history:** 2026-07-23 — initial authoring and reviewer follow-ups are
consolidated in this track commit. Corrections include the BN-012 trace, CAD-001,
setter/status/decision provenance, dependency, parameter-reporting, and
presentation polish.

**Minimum-change revision:** 2026-07-24 — the audited occurrences remain
historical evidence. The owner retained BN-025's narrow shared change, kept
BN-012 behind a configuration/no-change necessity gate, and selected BN-002's
portable same-execution-block direction while leaving its exact abstraction to
Stage A.

**Controlling architecture:** `/Users/wigglez/dev/hightop-notes/random/hood/hood-chain-executive-summary.md`

This is an analysis artifact. It does not approve a clock policy or change contracts,
defaults, migrations, tests, or deployment state.

## Baseline and method

The pinned worktree was clean when the audit began. Compared with the planning
baseline, the pinned commit adds only the three Robinhood track briefs under
`docs/chains/rh/`; no production contract changed. The production population is all
Vyper under `contracts/` excluding `contracts/mock/`.

The repository-generated Base parameter snapshots cited below were generated on
**2025-12-02** (`general_output.md` at block `38,931,025`,
`prices_output.md` at `38,930,921`, `vaults_output.md` at `38,930,978`, and
`ledger_output.md` at `38,931,053`). They are dated evidence, nearly eight months
old at this audit, and are not current live-chain verification.

Run these commands from the repository root:

```bash
rg -n -F 'block.number' contracts -g '*.vy' -g '!contracts/mock/**' | wc -l
rg -o -F 'block.number' contracts -g '*.vy' -g '!contracts/mock/**' | wc -l
rg -l -F 'block.number' contracts -g '*.vy' -g '!contracts/mock/**' | wc -l

rg -n -F 'block.number' contracts/mock -g '*.vy' | wc -l
rg -o -F 'block.number' contracts/mock -g '*.vy' | wc -l
rg -l -F 'block.number' contracts/mock -g '*.vy' | wc -l
```

| Population | Matching lines | Exact occurrences | Files |
| --- | ---: | ---: | ---: |
| Production Vyper | 95 | 100 | 17 |
| `contracts/mock/` | 0 | 0 | 0 |

The exact-occurrence count, not the matching-line count, is the coverage
denominator. Tests still assume ordinary monotonically increasing block numbers
through their chain time-travel helpers; the absence of mock-contract occurrences
does not remove the need for repeated-number and jump profiles.

### Interpretation model

- **Repeated:** many transactions observe the same L1-derived number.
- **Advance by one:** ordinary progress by one L1 block number. Per-ID behavior is
  recorded separately below rather than assumed to be harmless.
- **Jump:** the observed number advances by several increments between protocol
  calls.
- **Cadence:** current Base defaults use roughly two seconds per block
  (`43,200` blocks/day); Robinhood planning uses roughly twelve seconds per
  L1-derived increment (`7,200` increments/day). These are planning assumptions,
  not chain guarantees.
- **Source disposition:** `retain` means the shared runtime expression can remain;
  `configure` means provide a Robinhood value through existing configuration;
  `modify shared` means the owner rejected the documented no-source-change
  alternatives and approved an indispensable chain-portable change.

## Inventory

The first table supplies the semantic and decision fields. The trace table supplies
the implementation, configuration, default, migration, and test fields for the same
stable IDs. Every physical occurrence is reconciled in the coverage ledger.

### Semantic inventory

| ID | Contract, function, expression | Primary category; tags | Base value and intent | Repeated / jump behavior | Risk if unchanged | Recommended disposition and chain implications | Owner; confidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BN-001 | `Erc20Token.initiateHqChange/confirmHqChange`: pending HQ confirmation blocks | configurable economic duration; governance, token authority | `43,200` default = about 1 day; bounds `43,200..302,400` = 1..7 days | Repeat holds the pending action; a jump opens confirmation. No expiration | Base numeric value becomes about 6 days on Robinhood | Retain shared logic; configure RH default/bounds in chain defaults, provisionally `7,200`/equivalent bounds | Protocol owner; high, source/default verified |
| BN-002 | `Ledger.checkAndUpdateLastTouch`: reject `lastTouch == block.number` | true same-execution-block security guard; liquidation/borrow safety | Enabled in Base defaults; intended one higher-risk action per actual execution block | Repeated Robinhood ancestor numbers would reject later transactions across multiple child blocks; a child-block advance under the same ancestor number must clear the guard | Using Robinhood's L1-derived `block.number` turns a same-block guard into cross-child-block throttling | **Owner-selected portable redesign:** keep native `block.number` on ordinary EVM deployments and use Robinhood's actual child-block identifier, expected to be `ArbSys(0x64).arbBlockNumber()`, through the smallest immutable/fail-closed shared abstraction Stage A can justify. Preserve the current any-touch-to-checked-action policy. Do not migrate the deployed Base Ledger | Security/protocol owner; property approved, exact abstraction pending Stage A |
| BN-003 | `LocalGov.startGovernanceChange/confirmGovernanceChange` | configurable economic duration; governance | `43,200` default = about 1 day; immutable bounds from blueprint | Repeat holds; jump opens confirmation; no expiration | Sixfold wall-time drift if Base count copied | Retain; supply RH chain defaults, provisionally divide duration counts by six | Protocol owner; high |
| BN-004 | `TimeLock._initiateAction/_canConfirmAction/_isExpired`: confirmation and expiration | configurable economic duration; governance, shared module | Per-deployable action delay; generated Base snapshot contains `0`, `3,600`, `14,400`, `43,200`; max commonly `302,400` | Repeat holds. A jump can open the action or jump directly past `expiration`, making it unconfirmable | Drift changes governance latency; large jumps can erase a confirmation window | Retain module; configure every RH inheritor. Specify minimum expiration headroom against observed jumps and test pre/open/expired transitions | Protocol/security owner; high |
| BN-005 | `Contributor.initiateRipeTransfer/confirmRipeTransfer` | configurable economic duration; treasury authority | `keyActionDelay=43,200` in dated generated snapshot = about 1 day | Repeat holds transfer; jump opens it | Sixfold delay on RH if copied | Retain; chain-configure `keyActionDelay`, provisionally `7,200` for one day | Treasury/protocol owner; high |
| BN-006 | `Contributor.changeOwnership/confirmOwnershipChange` | configurable economic duration; governance/treasury authority | Same `keyActionDelay` as BN-005 | Same as BN-005 | Same as BN-005 | Retain and configure with BN-005; preserve timestamp vesting separately | Treasury/protocol owner; high |
| BN-007 | `RipeGov` deposit/withdraw/update/get points checkpoints | per-number rate or reward accrual; governance rewards | Points are `shares * elapsedBlocks`; no direct cadence scalar | Repeat accrues zero until the number advances; jump credits the last checkpointed share balance across the whole gap | Coarse attribution around balance changes; wall-time point rate is about 6x lower on RH | Retain only if coarse L1-number attribution is accepted. Add dual-chain repeat/jump tests; any normalization policy belongs in shared clock spec | Protocol/rewards owner; medium-high |
| BN-008 | `RipeGov` withdrawal and early-release unlock comparisons | configurable economic duration; lock boundary | Lock terms from Mission Control; Base min `43,200` (1 day), max `47,304,000` (3 years) | Repeat holds lock; jump may cross unlock atomically | Sixfold wall-time extension if Base counts copied | Retain; RH terms provisionally `7,200..7,884,000` for same wall time | Governance owner; high |
| BN-009 | `RipeGov.adjustLock`, bonus, weighted lock, refresh | configurable economic duration; per-number bonus math | Same min/max lock terms as BN-008 | Repeat freezes remaining duration and bonus; jump reduces it in coarse increments | Wrong lock/bonus duration if counts copied; coarse bonus transitions | Retain shared math; chain-configure lock terms and test repeat/jump/deposit reweighting | Governance/rewards owner; high |
| BN-010 | `CurvePrices.getCurrentGreenPoolStatus`: `staleBlocks` | configurable economic duration; Base-only pricing | Base migration sets `43,200` = about 1 day | Repeat never becomes stale; jump can become stale immediately | Misleading RH behavior, but Curve path is unsupported there | Retain for Base; disable/omit Curve feed on RH rather than convert this clock | Protocol/oracle owner; high |
| BN-011 | `CurvePrices._addGreenRefPoolSnapshot`: same-number guard, danger accumulation, update | configurable economic duration; same-number sampling, Base-only pricing | Uses configured `staleBlocks`; at most one snapshot per number | Repeat suppresses snapshots; jump adds the entire gap to danger blocks | Broken sampling if accidentally enabled on RH | Retain Base source; mark Curve integration disabled on RH and prevent registration | Protocol/oracle owner; high |
| BN-012 | `Deleverage.deleverageForWithdrawal`: cooldown comparison and last block | hardcoded economic duration; security/rate limit | Contract-local `deleverageCooldown` storage initializes to `0`; no default, migration assignment, or generated snapshot value exists. It is hard-capped by duplicated `7,200`; comments call the cap “~1 day at 12s/block,” but on Base it is about 4 hours | Deliberate `block.number > lastBlock` allows same-number multi-asset work; on RH it also permits many repeated-number transactions. A jump consumes cooldown | Repeated-number bypass; duplicated cap; ambiguous 4h-vs-1d intent | **Configuration-first:** keep cooldown zero and prohibit nonzero activation if owner accepts no pacing. Centralize/parameterize only if a nonzero launch policy is indispensable | Security/protocol owner; high mechanics, intent unresolved |
| BN-013 | `SwitchboardDelta.setStartEpochAtBlock`: clamp start to current | configurable economic duration; admin scheduling | Absolute block input; no duration default | Repeat clamps to same current value; jump clamps stale requested starts forward | Admin expectations can differ, but no embedded cadence | Retain; document that operators submit chain-native absolute numbers | Governance/rewards owner; high |
| BN-014 | `BondRoom.purchaseRipeBond`: epoch inclusion and progress | configurable economic duration; auction/reward progression | Mission Control `epochLength=14,400` = about 8 hours; restart delay `0` | Repeat freezes price/progress and preserves window; jump may skip part/all of epoch | Sixfold window drift if copied; missed short windows | Retain; RH epoch length provisionally `2,400` for 8h and add repeat/jump tests | Rewards/governance owner; high |
| BN-015 | `BondRoom.previewRipeBondPayout`: epoch progress | configurable economic duration; view parity | Same as BN-014 | Same number returns stable quote; jumps reprice | Preview/execution mismatch if edge behavior is untested | Retain and test parity at repeated/jump boundaries with BN-014 | Rewards owner; high |
| BN-016 | `BondRoom.startBondEpochAtBlock`: manual start clamp | configurable economic duration; admin scheduling | Absolute requested block | Same as BN-013 | Operator confusion only if absolute numbering is misinterpreted | Retain; chain-native operational runbook | Governance owner; high |
| BN-017 | `BondRoom._getLatestEpochBlockTimes`: start/restart/catch-up | configurable economic duration; epoch catch-up | `epochLength=14,400`, restart delay `0` in Base defaults | Repeat holds epoch. Jump can roll one or several epochs and reset start/end to the observed number | Skipped sale windows and different issuance cadence | Retain; configure RH durations and test multi-epoch jumps | Rewards/governance owner; high |
| BN-018 | `RipeHq.initiateHqConfigChange/confirmHqConfigChange` | configurable economic duration; capability registry | Uses HQ registry timelock; Base default `21,600` = about 12h | Repeat holds; jump opens; no expiration | Sixfold latency drift; affects Department/CCIP capabilities | Retain; provisionally `3,600` RH for 12h, subject to security review | Protocol/security owner; high |
| BN-019 | `AddressRegistry` add-address pending/confirm | configurable economic duration; registry | Shared registry delay; Base default `21,600` = about 12h | Repeat holds; jump opens | Sixfold latency drift | Retain; chain-configure same intended wall time | Protocol/security owner; high |
| BN-020 | `AddressRegistry` update-address pending/confirm | configurable economic duration; registry | Same as BN-019 | Same | Same; address replacement is high authority | Retain; configure and test jump boundary | Protocol/security owner; high |
| BN-021 | `AddressRegistry` disable-address pending/confirm | configurable economic duration; registry | Same as BN-019 | Same | Same; emergency disable latency may need different policy, but code shares one value | Retain for now; owner should confirm one shared delay is acceptable for add/update/disable | Protocol/security owner; medium-high |
| BN-022 | `Lootbox` global/asset/user deposit-point checkpoints | per-number rate or reward accrual; accounting | `elapsedBlocks` times balances/weights; no seconds normalization | Repeat accrues zero; jump attributes the full gap to the balance at its previous checkpoint | Coarse/fairness effects at L2 transaction boundaries; wall-time point rate changes | Retain only with explicit coarse-clock acceptance and dual-profile tests; do not mechanically timestamp-convert | Rewards owner; medium-high |
| BN-023 | `Lootbox` global/user borrow-point checkpoints | per-number rate or reward accrual; accounting | Same model as BN-022 | Same | Same | Same disposition as BN-022 | Rewards owner; medium-high |
| BN-024 | `Lootbox._getLatestGlobalRipeRewards`: RIPE emission | per-number rate or reward accrual; monetary emission | `ripePerBlock=0.0075 RIPE` in current source/generated snapshot | Repeat emits zero; jump emits the whole gap at the prior rate | About 6x lower wall-time emissions on RH if copied | Retain expression; configure RH rate provisionally near `0.045 RIPE` per L1 increment to preserve time-rate, subject to tokenomics approval | Tokenomics/rewards owner; high mechanics, policy unresolved |
| BN-025 | `Lootbox.distributeUnderscoreRewards`: send interval | hardcoded economic duration; unsupported integration | Planning baseline constructor/setter enforce `ONE_DAY=43,200`; integrated S3 parameterized it | Repeat blocks sends; jump opens them | The planning-baseline source cannot accept a one-day RH value, but accepts interval zero when Underscore is disabled | **Owner-selected narrow change:** retain S3; Base floor `43,200`, RH floor `7,200`, RH mutable interval `0`; deployment/convergence separately gated | Protocol/rewards owner; high |
| BN-026 | `Lootbox.distributeUnderscoreRewards` event `blockNumber` | telemetry only; observability | Emits current number | Repeats and jumps are faithfully recorded as observed | Consumers may wrongly assume unique/sequential numbers | Retain; document semantics in event consumers | Data/operations owner; high |
| BN-027 | `EndaomentPSM` mint interval availability/update | configurable economic duration; capacity limiter | Constructor/governed `numBlocksPerInterval=43,200` = about 1 day | Repeat shares one capacity bucket; first call after jump resets it | Sixfold interval drift if copied | Retain; RH `7,200` for one day if PSM is enabled. Deploy disabled while USDG price path is unresolved | Protocol/risk owner; high |
| BN-028 | `EndaomentPSM` redeem interval availability/update | configurable economic duration; capacity limiter | Same duration as BN-027; separate redeem bucket | Same | Same | Same as BN-027; test mint/redeem independence under repeat/jump | Protocol/risk owner; high |
| BN-029 | `CreditEngine` per-user borrow interval | configurable economic duration; capacity limiter | Mission Control `numBlocksPerInterval=43,200` = about 1 day | Repeat shares the user's bucket; first call after jump resets it | Sixfold interval drift if copied; jump refills atomically | Retain; RH `7,200` for one day and test exact boundary/jump. Interest remains timestamp-based | Protocol/risk owner; high |
| BN-030 | `AuctionHouse._createOrUpdateFungAuction`: start/end window | configurable economic duration; liquidation auction | Mission Control default delay `0`, duration `43,200` = about 1 day; asset overrides possible | Repeat holds pre-start/in-window; jump may skip delay or whole short auction | Wrong liquidation duration or inaccessible auction after a jump | Retain; RH duration provisionally `7,200`; specify a conservative minimum relative to jump profile | Risk/liquidation owner; high |
| BN-031 | `AuctionHouse._buyFungibleAuction`: eligibility and discount progress | configurable economic duration; liquidation pricing | Same delay/duration as BN-030 | Repeat freezes discount; jump reprices or closes the auction | Price discontinuity and skipped participation window | Retain; chain-configure and add repeat/multi-jump boundary tests | Risk/liquidation owner; high |
| BN-032 | `BondBooster.getBoostRatio/_isValidBooster`: absolute expiry | configurable economic duration; rewards/governance | `expireBlock` supplied by governance; lock terms include Base `minLockDuration=7,776,000` in dated generated snapshot | Repeat holds boost valid; jump expires it atomically | Operational error if Base absolute/duration assumptions are copied | Retain; require chain-native absolute expiry and RH lock-term configuration | Governance/rewards owner; high |

### Advance-by-one behavior

This ledger makes the nominal `+1` transition explicit for every BN ID. It does not
change the 100-occurrence denominator.

| IDs | Behavior when the observed number advances by exactly one |
| --- | --- |
| BN-001, BN-003, BN-005, BN-006, BN-008, BN-018, BN-019, BN-020, BN-021, BN-025, BN-027, BN-028, BN-029, BN-032 | Remaining delay, lock, interval, or expiry distance decreases by one; an exact boundary changes eligibility. |
| BN-002 | The prior action-block ID no longer equals the current action-block ID, so the same-execution-block rejection clears. On RH this must occur on the next child block even when inherited `block.number` does not advance. |
| BN-004 | Confirmation/expiration distance advances one; the action opens or expires exactly at its configured boundary. |
| BN-007, BN-022, BN-023, BN-024 | Exactly one unit of points or RIPE reward accrual is added for the checkpointed balance/rate. |
| BN-009 | Remaining lock duration/bonus decreases by one while one unit of governance points can accrue. |
| BN-010 | Snapshot age increases by one and may cross the staleness threshold. |
| BN-011 | The same-number snapshot guard clears; an in-danger prior snapshot adds one danger block. |
| BN-012 | The deliberate same-number exception ends; for cooldowns greater than one, the cooldown check becomes active until its boundary. |
| BN-013, BN-016 | A stale requested absolute start is clamped one number later. |
| BN-014, BN-015, BN-031 | Epoch/auction progress advances by one numerator step and may change the quote or eligibility at a boundary. |
| BN-017 | Epoch state advances one step and can enter, end, or restart at an exact boundary. |
| BN-026 | Telemetry emits the incremented observed number; no state policy depends on uniqueness. |
| BN-030 | A newly created auction's absolute start/end shift by one because `startBlock` is derived from the current number. |

### Implementation trace

| ID | State/config source; setters and validators | Defaults/migrations and current evidence | Affected tests / required Robinhood additions |
| --- | --- | --- | --- |
| BN-001 | `hqChangeTimeLock`; constructor immutable min/max; governed setter in token module | `config/BluePrint.py`, `contracts/config/DefaultsBase.vy`; dated `scripts/params/general_output.md` | `tests/tokens/test_erc20.py`; repeat, +1, multi-jump confirm |
| BN-002 | `lastTouch`; `Ledger.checkAndUpdateLastTouch`; future immutable action-block source; caller flag derived by Teller from `MissionControl.shouldCheckLastTouch` and action risk; governed path `SwitchboardDelta.setShouldCheckLastTouch` → `MissionControl.setShouldCheckLastTouch` | Live Base retains current bytecode and `shouldCheckLastTouch=True`; `DefaultsLocal=False`; the 2025-12-02 `ledger_output.md` is runtime accounting evidence, not the flag's configuration source | `tests/data/test_ledger.py`, `tests/config/test_switchboard_delta.py`, focused S5 source/provider tests; prove native behavior, RH same-child rejection, next-child allowance under repeated ancestor number, provider failure, and no Base migration |
| BN-003 | `govChangeTimeLock`; `LocalGov.setGovChangeTimeLock`; immutable constructor bounds | `config/BluePrint.py`, `DefaultsBase` | `tests/modules/test_local_gov.py`; add RH values and jumps |
| BN-004 | `TimeLock.actionTimeLock`, `expiration`; setters validate immutable min/max | Every inheritor's blueprint/default/migration; dated `scripts/params/general_output.md` and `prices_output.md` are last repo-generated live snapshots, not current-chain proof | `tests/modules/test_time_lock.py` plus inheritor suites; add jump-over-entire-window |
| BN-005–006 | `Contributor.keyActionDelay`; owner setter validates constructor min/max | Contributor deployment/default generation; dated general snapshot `43,200` | `tests/core/humanResources/test_hr_contributor.py`, `test_hr_other.py`; add RH and mixed timestamp/block boundary cases |
| BN-007–009 | Per-user `lastPointsUpdate`, `unlock`; Mission Control lock terms; `SwitchboardAlpha` setters validate lock range | `DefaultsBase`: min `43,200`, max `3 * YEAR_IN_BLOCKS`; dated `scripts/params/vaults_output.md` | `tests/vaults/test_ripe_gov_vault.py`, `tests/config/test_switchboard_alpha.py`; add repeated/jump attribution |
| BN-010–011 | `CurvePrices.greenRefPoolConfig.staleBlocks`, snapshot `update`/danger blocks; config setter validates pool but has no cadence max | `migrations/base-mainnet/2001_CurvePools.py` sets `43,200`; Base-only integration | `tests/priceSources/curve/test_green_ref_pool.py`, `test_curve_prices.py`; add RH negative registration/omission assertion |
| BN-012 | Contract-local `Deleverage.deleverageCooldown` (`Deleverage.vy:175`); timelocked governed path `SwitchboardDelta.setDeleverageCooldown` → `Deleverage.setDeleverageCooldown`; both setters validate their own duplicated `MAX_COOLDOWN_BLOCKS=7_200` | Storage initializes to `0` because the constructor does not assign it. No `DefaultsBase`, migration, Mission Control field, or generated parameter snapshot sets/reports this value; current live Base state requires an RPC read | `tests/core/deleverage/test_deleverage_for_withdrawal.py`, `tests/config/test_switchboard_delta.py`; add repeated-number multi-transaction and cross-asset same-call cases |
| BN-013, BN-016 | Absolute requested block; Switchboard clamps then calls BondRoom | No duration default at these sites | `tests/config/test_switchboard_delta.py`, `tests/core/bondRoom/test_ripe_bonds.py`; add stale/future request under jumps |
| BN-014–017 | `MissionControl.ripeBondConfig.epochLength/restartDelay`; Switchboard setters | `DefaultsBase`: `14,400` / `0`; dated general snapshot agrees | `tests/core/bondRoom/test_ripe_bonds.py`, `tests/config/test_switchboard_delta.py`; repeat, boundary, multi-epoch jump |
| BN-018 | Reads HQ registry's `registryChangeTimeLock`; registry config-change functions | `config/BluePrint.py`: `21,600..302,400` | `tests/registries/test_ripe_hq.py`; add CCIP Department capability-change case |
| BN-019–021 | `AddressRegistry.registryChangeTimeLock`; governed setter, immutable bounds | `config/BluePrint.py`: `21,600..302,400`; `DefaultsBase` | `tests/registries/test_address_registry.py`; add RH and jump cases for add/update/disable |
| BN-022–024 | Point structs' `lastUpdate`; RewardsConfig includes `ripePerBlock`; Switchboard Charlie controls rewards configuration | `DefaultsBase.ripePerBlock=75 * 10**14`; dated general snapshot `0.0075` | `tests/core/lootbox/test_loot_deposit_points.py`, `test_loot_borrow_points.py`, `test_loot_ripe_rewards.py`, `tests/config/test_switchboard_charlie.py`; add dual cadence profiles |
| BN-025–026 | `underscoreSendInterval`; constructor and `setUnderscoreSendInterval` both enforce `ONE_DAY`; event emits number | `contracts/core/Lootbox.vy:193`; Base interval `43,200`; Underscore disabled on RH | `tests/core/lootbox/test_underscore_rewards.py`; parameterized minimum and disabled-path tests |
| BN-027–028 | `EndaomentPSM.numBlocksPerInterval`, mint/redeem `IntervalData`; timelocked governed path `SwitchboardEcho.setPsmNumBlocksPerInterval` (`PSM_SET_NUM_BLOCKS_PER_INTERVAL`) → `EndaomentPSM.setNumBlocksPerInterval` | Base migration/default value `43,200`; 2025-12-02 general snapshot agrees | `tests/core/endaoment/test_endaoment_psm_mint.py`, `test_endaoment_psm_redeem.py`, `test_endaoment_psm_config.py`, `tests/config/test_switchboard_echo.py`; repeat/jump, full governance flow, and disabled PSM |
| BN-029 | `MissionControl.genDebtTerms.numBlocksPerInterval`; Switchboard Alpha validates nonzero/nonmax | `DefaultsBase=43,200`; dated general snapshot agrees | `tests/core/creditEngine/test_credit_borrow.py`, `tests/config/test_switchboard_alpha.py`; repeated/jump refill |
| BN-030–031 | `MissionControl` default/custom `AuctionParams.delay/duration`; Switchboard Bravo setters/validators | `DefaultsBase`: delay `0`, duration `43,200`; dated general snapshot | `tests/core/auctionHouse/test_ah_auctions.py`, `test_ah_auction_mgmt.py`, `tests/config/test_switchboard_bravo.py`; repeated/jump price and skipped-window cases |
| BN-032 | `BondBooster.boosterConfig.expireBlock`; Switchboard Delta validates via contract; lock terms in Mission Control | Dated general snapshot `minLockDuration=7,776,000`; absolute expiries are operator inputs | `tests/config/test_bond_booster.py`, `tests/config/test_switchboard_delta.py`; add RH absolute-number runbook fixtures |

## Indirect cadence configuration

The required Mission Control/default sweep found one economic field that contains
no literal `block.number` itself but consumes BN-011's danger-block counter. It is
tracked as CAD-001 and is deliberately excluded from the 95-line/100-occurrence
BN totals.

### CAD-001 rate and reporting semantics

At the pinned commit, `DefaultsBase.vy:75` supplies raw
`increasePerDangerBlock=10`. `CreditEngine._getDynamicBorrowRate` computes
`10 * numBlocksInDanger * 100_00 // 100_0000`, or
`numBlocksInDanger // 10` internal rate units. One internal rate unit is `0.01%`,
so the ideal pre-floor slope is `0.001%` per danger block; integer division
realizes it as one `0.01`-percentage-point step per 10 accumulated danger blocks.

The 2025-12-02 general snapshot instead displays `0.10%` because
`scripts/params/general.py` sends the raw value to generic `format_percent`,
whose default denominator is `100_00`. That display overstates the ideal runtime
slope 100×. It is a reporting defect, not evidence that the raw parameter should
change.

On Robinhood at launch, the field is inert: when `CurvePrices` is unregistered,
CreditEngine returns the base rate at line 1048. The governed path is
`SwitchboardAlpha.setDynamicRateConfig` → Mission Control, and
`_isValidDynamicRateConfig` rejects zero and maximum values. Existing coverage is
in `tests/core/creditEngine/test_credit_dyn_rate.py`,
`tests/config/test_switchboard_alpha.py`,
`tests/data/test_mission_control.py`, and
`tests/priceSources/curve/test_green_ref_pool.py`. Before any future enablement,
fix the report formatter, calibrate the raw slope for RH cadence (a roughly 6×
candidate preserves the Base time-rate), and test the raw, displayed, and
runtime-effective values together.

| ID | Field and runtime path | Category / Base evidence | Repeated, +1, and jump behavior | Robinhood risk and disposition | Setters, validators, tests, owner |
| --- | --- | --- | --- | --- | --- |
| CAD-001 | `MissionControl.genDebtConfig.increasePerDangerBlock` → `CreditEngine._getDynamicBorrowRate` line 1067; consumes BN-011's `CurvePrices.numBlocksInDanger` | Per-danger-number economic rate; Base raw value `10`. See the arithmetic and reporting distinction above | Repeat adds no danger count; +1 can add one; a jump adds the elapsed-number gap at the next snapshot before rate calculation | Mark explicitly inactive in `DefaultsRobinhood`. Before any future enablement, calibrate the raw slope for RH cadence, retain the integer-step model, and test jumps/caps | Governed path, validator, tests, and reporting fix are listed above. Risk/oracle owner; high |

## Exact occurrence coverage ledger

The line lists are pinned-commit evidence. A line can contain more than one exact
occurrence; the final column prevents that from being hidden.

| ID | Source path | Lines | Exact occurrences |
| --- | --- | --- | ---: |
| BN-001 | `contracts/tokens/modules/Erc20Token.vy` | 447, 450, 465 | 3 |
| BN-002 | `contracts/data/Ledger.vy` | 207, 210 | 2 |
| BN-003 | `contracts/modules/LocalGov.vy` | 193, 196, 208 | 3 |
| BN-004 | `contracts/modules/TimeLock.vy` | 68, 70, 119, 121, 141 | 5 |
| BN-005 | `contracts/modules/Contributor.vy` | 230, 233, 250 | 3 |
| BN-006 | `contracts/modules/Contributor.vy` | 304, 307, 317 | 3 |
| BN-007 | `contracts/vaults/RipeGov.vy` | 203, 298, 505, 630, 632 | 5 |
| BN-008 | `contracts/vaults/RipeGov.vy` | 284, 571 | 2 |
| BN-009 | `contracts/vaults/RipeGov.vy` | 543, 668, 671, 705, 710, 711, 721, 771 | 8 |
| BN-010 | `contracts/priceSources/CurvePrices.vy` | 986 | 1 |
| BN-011 | `contracts/priceSources/CurvePrices.vy` | 1020, 1041, 1048 | 3 |
| BN-012 | `contracts/core/Deleverage.vy` | 520 (2), 583 | 3 |
| BN-013 | `contracts/config/SwitchboardDelta.vy` | 915 | 1 |
| BN-014 | `contracts/core/BondRoom.vy` | 151 (2), 159 | 3 |
| BN-015 | `contracts/core/BondRoom.vy` | 299 | 1 |
| BN-016 | `contracts/core/BondRoom.vy` | 367 | 1 |
| BN-017 | `contracts/core/BondRoom.vy` | 422 (2), 427 (2), 431, 436 | 6 |
| BN-018 | `contracts/registries/RipeHq.vy` | 232, 235, 256 | 3 |
| BN-019 | `contracts/registries/modules/AddressRegistry.vy` | 160, 163, 177 | 3 |
| BN-020 | `contracts/registries/modules/AddressRegistry.vy` | 245, 248, 262 | 3 |
| BN-021 | `contracts/registries/modules/AddressRegistry.vy` | 335, 337, 351 | 3 |
| BN-022 | `contracts/core/Lootbox.vy` | 663, 664, 667, 698, 699, 702, 734, 735, 738 | 9 |
| BN-023 | `contracts/core/Lootbox.vy` | 904, 905, 908, 929, 930, 933 | 6 |
| BN-024 | `contracts/core/Lootbox.vy` | 1096, 1097, 1100 | 3 |
| BN-025 | `contracts/core/Lootbox.vy` | 1211, 1255 | 2 |
| BN-026 | `contracts/core/Lootbox.vy` | 1265 | 1 |
| BN-027 | `contracts/core/EndaomentPSM.vy` | 340, 353, 358 | 3 |
| BN-028 | `contracts/core/EndaomentPSM.vy` | 512, 525, 530 | 3 |
| BN-029 | `contracts/core/CreditEngine.vy` | 251, 443 | 2 |
| BN-030 | `contracts/core/AuctionHouse.vy` | 917 | 1 |
| BN-031 | `contracts/core/AuctionHouse.vy` | 1100 (2), 1119 | 3 |
| BN-032 | `contracts/config/BondBooster.vy` | 78, 201 | 2 |
| **Total** | **17 production files** | **95 matching lines** | **100** |

Per-file exact-occurrence cross-check:

| File | Count | File | Count |
| --- | ---: | --- | ---: |
| `AuctionHouse.vy` | 4 | `BondBooster.vy` | 2 |
| `BondRoom.vy` | 11 | `Contributor.vy` | 6 |
| `CreditEngine.vy` | 2 | `CurvePrices.vy` | 4 |
| `Deleverage.vy` | 3 | `EndaomentPSM.vy` | 6 |
| `Erc20Token.vy` | 3 | `Ledger.vy` | 2 |
| `LocalGov.vy` | 3 | `Lootbox.vy` | 21 |
| `RipeGov.vy` | 15 | `RipeHq.vy` | 3 |
| `SwitchboardDelta.vy` | 1 | `TimeLock.vy` | 5 |
| `AddressRegistry.vy` | 9 | **Total** | **100** |

## Cadence and duplication findings

| Finding | Enforcement path | Configuration path | Resolution surface |
| --- | --- | --- | --- |
| `Lootbox.ONE_DAY = 43_200 # on Base` | Constructor and `setUnderscoreSendInterval` reject smaller values | Interval itself is governed | Shared contract must receive a chain-portable minimum/bounds source; RH Underscore remains disabled |
| `MAX_COOLDOWN_BLOCKS = 7_200` appears twice | `Deleverage.deleverageCooldown` is consumed and validated locally; `SwitchboardDelta.setDeleverageCooldown` independently validates, timelocks, then calls the Deleverage setter | Contract-local storage starts at `0`; no Defaults, migration, Mission Control, or generated-snapshot assignment exists | One canonical limit; owner defines whether ceiling means Base 4h or wall-clock 1d; same-number exception requires redesign/spec |
| Base time constants | `DefaultsBase.HOUR/DAY/WEEK/MONTH/YEAR_IN_BLOCKS` feed defaults | Generated into deploy configuration | Add corresponding `DefaultsRobinhood`; do not place divergent runtime logic there |
| 2025-12-02 generated snapshots | `scripts/params/*_output.md` report Base values at blocks `38,930,921..38,931,053` | Nearly eight months old at the audit and not current RPC/live deployment verification | Use only as dated evidence; implementation kickoff must compare deployed Base bytecode/config with proposed canonical source |
| Indirect danger-block rate | `CreditEngine` consumes `MissionControl.increasePerDangerBlock` against Curve's BN-011 counter | Base default raw value `10`; zero is rejected by `SwitchboardAlpha` | CAD-001 must be explicit in `DefaultsRobinhood` even though Curve is disabled at launch |
| Parameter-report formatting drift | `scripts/params/general.py` renders `increasePerDangerBlock` with generic `format_percent` (`100_00` denominator), while runtime uses `DANGER_BLOCKS_DENOMINATOR=100_0000` | Snapshot `0.10%` is 100× the ideal pre-floor runtime slope of `0.001%` per danger block; integer division realizes the rate in `0.01`-percentage-point steps | Correct reporting tooling and add a raw/formatted/runtime regression test before DefaultsRobinhood parity reports; do not alter the raw parameter merely to match the faulty display |
| Comment drift | `VaultBook` blueprint value `3,600` is labeled “12 hours,” while Base cadence implies about 2 hours | Constructor bounds | Correct comments during implementation; numeric owner intent must be confirmed rather than inferred from the comment |
| HR seconds-bound drift | `DefaultsBase` sets minimum cliff/vesting to 1 week and maximum vesting to 10 years; `SwitchboardDelta` setters require minimum cliff `>1 week`, minimum vesting `>1 month`, and maximum vesting `<=5 years` | Initial defaults versus governed HR setters | Existing shared validation mismatch: specify the intended bounds and make initial/governed values round-trip before copying them to RH |

## Timestamp context appendix

This appendix is outside BN IDs and totals. Reproduction:

```bash
rg -n -F 'block.timestamp' contracts -g '*.vy' -g '!contracts/mock/**' | wc -l
rg -o -F 'block.timestamp' contracts -g '*.vy' -g '!contracts/mock/**' | wc -l
rg -l -F 'block.timestamp' contracts -g '*.vy' -g '!contracts/mock/**' | wc -l
```

Result: **37 matching lines, 37 exact occurrences, 11 production files**.

| ID | Contract/function and lines | Purpose, unit, configuration | Mixed boundary and portability | Tests / separate review |
| --- | --- | --- | --- | --- |
| TS-001 | `Erc20Token.permit`, line 356 | EIP-2612 deadline; Unix seconds supplied by signer | No block-duration conversion; chain-portable | `tests/tokens/test_erc20.py`; preserve deadline boundary tests |
| TS-002 | `Contributor` constructor, unlock/cancel/vesting views and updates, lines 151, 226, 431, 435, 443, 489, 492, 529, 530, 548, 549 | Contributor start, cliff, end, unlock and vesting durations in seconds; constructor and HR actions | **Mixed:** compensation lifecycle is seconds while transfer/ownership authority delay is block-number based (BN-005/006). Both can remain, but runbooks/tests must name units | `tests/core/humanResources/test_hr_contributor.py`, `test_hr_add_contributor.py`, `test_hr_other.py` |
| TS-003 | `PythPrices._getPrice`, line 197 | Oracle publish-time staleness in seconds; per-feed/global stale config | Chain-portable; review feed timestamp semantics and future timestamps | `tests/priceSources/test_pyth_prices.py` |
| TS-004 | `BlueChipYieldPrices` current/snapshot paths, lines 750, 787, 791, 848 | Snapshot last update, minimum delay, staleness; seconds | Same-timestamp guard is appropriate for timestamp sampling. Integration is disabled initially on RH | `tests/priceSources/blueChip/*`; negative RH registration test |
| TS-005 | `ChainlinkPrices._getChainlinkData`, lines 273, 283 | Reject future update and stale oracle update; seconds; feed/global stale config | Chain-portable and required for Stock Token feeds; no multiplier should be applied twice | `tests/priceSources/test_chainlink_prices.py`; RH official-feed fixtures pending Track 1 facts |
| TS-006 | `AeroRipePrices` current/snapshot paths, lines 332, 367, 371, 417 | Snapshot delay/staleness in seconds | Chain-portable clock, but Aerodrome integration disabled initially on RH | Price-source tests plus negative RH registration |
| TS-007 | `StorkPrices._getPrice`, line 168 | Publish-time staleness in seconds | Chain-portable; source disabled initially on RH | `tests/priceSources/test_stork_prices.py` |
| TS-008 | `UndyVaultPrices` current/snapshot paths, lines 650, 686, 690, 733 | Snapshot delay/staleness in seconds | Chain-portable clock; Underscore integration disabled initially on RH | `tests/priceSources/test_undy_vault_prices.py`; negative RH registration |
| TS-009 | `RedStone._getRedStoneData`, lines 228, 238 | Reject future update and stale oracle update; seconds | Chain-portable; source disabled initially on RH | Add/retain RedStone future/stale tests and RH omission test |
| TS-010 | `CreditEngine._updateUserDebt`, lines 898, 899, 903, 909 | Interest accrual elapsed time; `ONE_YEAR = 60*60*24*365` seconds | **Mixed:** interest accrues in seconds while borrow capacity resets by block-number interval (BN-029). This is intentional if separately configured | `tests/core/creditEngine/test_credit_dyn_rate.py`, `test_credit_borrow.py`; combined repeat/jump test |
| TS-011 | `AddressRegistry` add/update/disable writes, lines 190, 272, 361 | `lastModified` telemetry in Unix seconds | **Mixed:** authorization delay is block-number based (BN-019–021), while final change time is seconds. Portable and useful if consumers do not derive confirmation duration from it | `tests/registries/test_address_registry.py` |

Timestamp-denominated constant/config boundaries found in the same audit:

- `DefaultsBase.DAY_IN_SECONDS`, `WEEK_IN_SECONDS`, `MONTH_IN_SECONDS`, and
  `YEAR_IN_SECONDS` are explicitly separate from its `*_IN_BLOCKS` constants.
  Mission Control `priceStaleTime` defaults to `86,400` seconds, and its bounds
  are seconds.
- `SwitchboardDelta.DAY_IN_SECONDS`, `WEEK_IN_SECONDS`, `MONTH_IN_SECONDS`, and
  `YEAR_IN_SECONDS` validate Human Resources cliff, start-delay, and vesting
  configuration. They are seconds-domain constraints paired with TS-002, not
  block-clock candidates. The pinned defaults/setter bounds do not currently
  round-trip: defaults use one-week minimum cliff/vesting and ten-year maximum
  vesting, while governed setters require a strict greater-than-one-week cliff,
  greater-than-one-month vesting, and at-most-five-year maximum.
- `CreditEngine.ONE_YEAR` is `31,536,000` seconds and is correctly used only in
  interest math.
- Chainlink, RedStone, Pyth, and Stork stale times are seconds; the common default
  is one day where supplied.
- BlueChip, Aero, and Undy snapshot defaults use a five-minute minimum delay,
  one-day staleness, and validate a maximum one-week minimum delay.
- These timestamp clocks should not be converted solely for Robinhood. Disabled
  integrations still require omission/registration tests, not clock rewrites.

## Decision register

All statuses below mean **unapproved** unless explicitly recorded by the named
owner in a later artifact.

| Decision | Available options | Evidence | Recommendation | Affected components / IDs | Owner / approver | Needed by | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Live Base parity | Reuse unchanged; upgrade Base before/together; allow bounded drift; justified permanent exception | BN-002's live Base Ledger is state-heavy and unsafe to replace merely for parity; BN-012 has a no-change candidate; BN-025 S3 is owner-retained and creates optional Base convergence work | Keep the deployed Base Ledger indefinitely and record a permanent live-bytecode exception while maintaining one forward canonical source; keep S4 unchanged unless its separate necessity gate approves work; treat S3 convergence as a separately gated rollout | BN-002, BN-012, BN-025; CM-008, CM-014, CM-033, CM-044 | Protocol/deployment owner | Release freeze | BN-002 permanent Base exception owner-approved; S3 retained; S4 open |
| Shared clock posture | Retain/configure/disable; timestamp-convert all; redesign only semantic failures | BN-001–032 plus CAD-001 separate configurable clocks from true block-identity guards and dormant features | Retain/configure first; apply the approved narrow shared changes for BN-002/025; leave BN-012 unchanged unless its necessity gate closes | BN-001–032, CAD-001 | Protocol/security owner | Block-clock specification approval | Analysis and BN-002/025 direction approved; remaining implementation/value decisions open |
| Cooldown maximum intent | Keep cooldown zero; preserve numeric `7,200`; preserve one-day intent; another limit | Duplicated cap/comment verified; zero disables the path | Accept zero/no pacing for launch unless a nonzero policy is required | BN-012; CM-014, CM-044 | Security/protocol owner | S4 checkpoint | Open |
| Ledger same-execution-block guard | Disable on RH; retain ancestor-number throttling; portable action-block source | Owner requires the check to mean the same actual execution block, not a time span or L1-derived-number interval; Robinhood Nitro exposes child-block identity through ArbSys | Preserve the current action policy and change only the shared block-identity boundary: native `block.number` on ordinary EVM deployments and a fail-closed Robinhood child-block source. Existing Base Ledger remains deployed indefinitely | BN-002; CM-008, CM-034 | Security owner | S5 Stage A checkpoint and RH deployment inputs | Property and Base exception owner-approved; exact abstraction/evidence pending Stage A |
| SavingsGreen deployment | Include local sGREEN; omit and specify all dependent behavior | Existing AuctionHouse, Stability Pool, address, and lifecycle paths reference sGREEN; see CM-003 | Include provisionally unless the owner approves and specifies omission changes | CM-003, CM-022, CM-026 | Protocol/product owner | Frozen deployment graph | Open; see component register |
| Stock Token vault | Existing vault with accepted risk; smallest demonstrably sufficient shared containment patch; broader corrected-share design | Track 5 rejects both existing paths unchanged for Stock Tokens; Track 8 owns the formal invariant and minimum patch evidence | Stock Tokens are mandatory for initial launch. Select only the smallest containment patch proven sufficient; do not expand into broader share/reward redesign without a separate necessity decision | CM-021, CM-024–026, CM-030, CM-043 | Protocol/risk/security owner | Before asset migration or borrowing enablement | Product direction owner-approved; exact patch and activation remain gated by Track 8 |
| USDG price path / PSM | Existing reviewed Chainlink feed/adapter; separate fixed/capped adapter; PSM disabled | No approved USDG price path is established; BN-027/028 describe PSM cadence and CM-048 the activation boundary | Prefer an existing reviewed source; otherwise launch disabled | BN-027, BN-028; CM-015, CM-016, CM-048 | Risk/oracle owner | Before PSM activation | Open |
| CCIP registration/admin | Assisted registration; add shared token `getCCIPAdmin()` revision if required | Existing token source can remain unchanged under assisted registration; exact support is pending Track 1 | Prefer assisted registration; any token revision must be shared and include a Base live-version decision | BN-001, BN-018; CM-001, CM-002, CM-051–053 | Security/deployment owner | After Track 1, before pool implementation | Pending Track 1 and owner |
| CCIP thin-Solidity inheritance boundary | Existing deployment path is Vyper-centric; no production Solidity build exists | Owner selected concrete Chainlink-pool inheritance with only two capability views; the exact-hash reference passed Round-3 review, while production compatibility still depends on an exact dependency/compiler pin, artifact delta checks, gas evidence and production-package review/audit | Add one path-scoped Solidity build that feeds the existing Python manifest/deployment authority; do not create a parallel deployment truth source | CM-051–053, CM-057–059 | Engineering/deployment/security owner | Before production CCIP code | Direction selected and reference review complete; exact support/tooling and production gates open |

## Specification handoff and validation

The next shared block-clock specification can use BN IDs directly. It must:

1. define the Robinhood observed-number model and a concrete maximum jump test
   profile;
2. list every per-chain value, bound, and rate conversion, including CAD-001;
3. implement the approved BN-002/025 direction in one canonical source, decide
   whether BN-012 needs a source change at all, and use no `chain.id` branches;
4. state the live Base upgrade/divergence plan; and
5. include Base ordinary cadence plus Robinhood repeated, +1, and multi-jump tests;
   and
6. correct the CAD-001 parameter-report denominator and test raw, displayed, and
   runtime-effective values together.

Validation completed against the pinned commit:

- exact fixed-string production counts: 95 lines, 100 occurrences, 17 files;
- all 100 occurrences mapped to BN-001–BN-032 and summed independently by file;
- mock-contract count recorded separately as zero;
- 37 timestamp occurrences in 11 files mapped outside BN totals;
- indirect Mission Control cadence field CAD-001 traced outside the literal
  occurrence denominator;
- CAD-001's generated `0.10%` display traced to the generic `100_00`
  parameter-report denominator and distinguished from the runtime `100_0000`
  denominator, `0.001%` ideal slope, and integer-step behavior;
- hardcoded constants, setters, validators, defaults, migrations, dated generated
  parameter sources, comments, and representative tests traced;
- selected executive-summary architecture used; no federated architecture imported;
- 2025-12-02 generated values labeled as stale point-in-time evidence, not current
  live truth.

Structural checks used in addition to the fixed-string source commands:

```bash
# Stable semantic and coverage IDs
sed -n '/^### Semantic inventory/,/^### Advance-by-one behavior/p' \
  docs/chains/rh/block-number-inventory.md | rg '^\| BN-' | wc -l
sed -n '/^## Exact occurrence coverage ledger/,/^Per-file exact-occurrence/p' \
  docs/chains/rh/block-number-inventory.md | rg '^\| BN-' | wc -l

# Sum the exact-occurrence column; expected: 32 rows / 100 occurrences
awk -F'|' '
  /^## Exact occurrence coverage ledger/{on=1; next}
  /^Per-file exact-occurrence/{on=0}
  on && $2 ~ /BN-[0-9][0-9][0-9]/ {
    value=$5; gsub(/[^0-9]/, "", value); sum+=value; rows++
  }
  END{print rows, sum}
' docs/chains/rh/block-number-inventory.md

git diff --check
git show --check --oneline HEAD
```
