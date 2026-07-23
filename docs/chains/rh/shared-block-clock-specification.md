# Shared block-clock specification

**Status:** Specification complete; owner decisions remain open and block only
their dependent implementation slices

**Prepared:** 23 July 2026

**Track:** `rh-track-6-block-clock-spec`

**Integrated `rh` launch commit:** `5018da6d19516509e0d8674b3728e73bca92e2ad`

**Track 3 content commit:** `4408aa2184cfa80e8f0fed5482397856a9aedfb7`

**Track 3 reviewed merge:** `5b22e4e84364e7f4fde85844f39393089e90ac4c`

**Inventory SHA-256:** `3f111accff58e51b91986f134df6d15ed7401d692ef0cca28b2cafb1c89ad2d4`

**Component-matrix SHA-256:** `73bf9963af8d3680bf4e1149421b6cfd48b47c0c94adb04be82fd7be83553a0e`

This is a decision-ready specification, not an approval or implementation. Every
Robinhood value below is a candidate until the named owner approves it. No
production contract, test, default, script, migration, generated report, CI file,
or `rh-summary.md` is changed by this track.

## Authority, launch record, and architecture

The local `rh` integration worktree was clean at launch. Its reviewed Track 3 merge
contains both authoritative inventory files, all required inventory sections, and
the component IDs they reference. The owner confirmed on 23 July 2026 that Track 3
was unblocked and asked that its completion be verified. No production-contract
delta exists between the Track 3 content commit and the launch commit.

This document consumes:

- [`block-number-inventory.md`](block-number-inventory.md) and
  [`component-matrix.md`](component-matrix.md) for stable IDs and audited scope;
- [`usdg-psm-decision.md`](usdg-psm-decision.md) for the integrated Track 4
  `go — existing feed` decision and its still-disabled PSM posture;
- Section 2 of [`../rh-summary.md`](../rh-summary.md); and
- the selected local Hightop Notes executive summary.

The resulting architecture is one canonical contract source for Base, Robinhood,
and future EVM chains. Chain differences are constructor data, governed storage,
defaults, and migrations. There is no `chain.id` clock branch and no
Robinhood-only protocol implementation. Curve, Aerodrome, BlueChip yield,
Underscore, Pyth, Stork, RedStone, and Base-only wrapped-yield price paths are
omitted or unregistered on Robinhood until separately approved. Timestamp-domain
logic remains seconds-domain.

## Observed-number models and evidence

### Names that must not be conflated

`NUMBER` below means the value returned by the EVM `NUMBER` opcode and exposed to
Vyper as `block.number`.

- On Base, committed L2 blocks form a sequential L2 chain. Base documents sealed
  L2 blocks at about two-second intervals. Flashblocks provide approximately
  200 ms preconfirmations, and a pending-call endpoint can expose lagged pending
  context; neither changes the committed `NUMBER` used by an included state
  transition. Sources retrieved 23 July 2026:
  [transaction troubleshooting](https://docs.base.org/base-chain/network-information/troubleshooting-transactions),
  [Flashblocks FAQ](https://docs.base.org/base-chain/flashblocks/faq), and
  [OP Stack derivation](https://docs.base.org/base-chain/specs/protocol/consensus/derivation).
- Robinhood Chain documents itself as an Arbitrum L2 on Ethereum.
  [Robinhood connection documentation](https://docs.robinhood.com/chain/connecting/)
  was retrieved 23 July 2026.
- For an Arbitrum L2, EVM `NUMBER` is an estimate of the first non-Arbitrum
  ancestor's block number, Ethereum in this case. The standard RPC block
  `number` is the child-chain height, `l1BlockNumber` is the ancestor estimate,
  `ArbSys.arbBlockNumber()` is the child-chain height, and `block.timestamp` is
  the sequencer timestamp. The authoritative
  [Arbitrum block-number and time documentation](https://docs.arbitrum.io/time),
  retrieved 23 July 2026, documents repeats and jumps and gives the example
  EVM sequence `1000,1000,1000,1000,1004,1004`. It describes ancestor estimate
  synchronization around 13–15 seconds and occasionally longer; it does not
  guarantee a maximum jump.
- Robinhood timestamps follow the Arbitrum sequencer clock: nondecreasing and
  bounded by the documented validity window. They are not an alias for either
  child height or EVM `NUMBER`.

### Reproducible empirical evidence

A read-only sample from `https://rpc.mainnet.chain.robinhood.com` at
`2026-07-23T21:36:01Z` covered 128 consecutive child blocks
`17,615,178..17,615,305`. Their RPC `l1BlockNumber` ancestor-estimate field was
`25,598,150..25,598,152`: 88 child blocks repeated `25,598,150`, 40 repeated
`25,598,152`, and the observed transition was `+2`. Child timestamps advanced by
zero or one second. Because no onchain probe was authorized, this is not a direct
opcode observation; the authoritative Arbitrum documentation supplies the EVM
model. The sample is a reproducible observation window, not a maximum, guarantee,
or production parameter approval.

### Exact synthetic profiles

Let `N = 1_000_000`, `T = 2_000_000_000`, opening boundary `B`, and a finite
window `[S,E)` where `E > S`. A pair is `(NUMBER,timestamp)` immediately before
the named state-changing call.

| Profile | Exact sequence | Purpose and status |
| --- | --- | --- |
| `B-ORD` | `(N,T),(N+1,T+2),(N+2,T+4),(N+3,T+6),(N+4,T+8)` | Ordinary committed Base cadence and exact boundaries; documented model |
| `R-REP128` | `(N,T+floor(i/4))` for integer `i=0..127` | 128 transactions with one `NUMBER`; conservative repeat based on the 88-block empirical run |
| `R-PLUS1` | `(N,T),(N,T+1),(N+1,T+12),(N+1,T+13)` | Exact `+1`, including a repeat on each side |
| `R-J2-J4` | `(N,T),(N,T+1),(N+2,T+24),(N+2,T+25),(N+4,T+48)` | Representative `+2` and `+4`; evidence-backed candidates, owner approval open |
| `BOUNDARY-OPEN` | `(B-1,T),(B+1,T+24)` | Skips an exact opening/refill/unlock/cooldown boundary |
| `BOUNDARY-WINDOW` | `(S-1,T),(E+1,T+24)` | Skips the whole confirmation, auction, or epoch window |
| `R-STRESS60` | `(N,T),(N,T+1),(N+60,T+720)` | Test-only conservative jump larger than ordinary evidence; not a protocol maximum; owner approval open |
| `MIXED` | `(N,T),(N,T+3600),(N+2,T+3600),(N+2,T+7200)` | Moves seconds and `NUMBER` independently |

Every boundary suite also sets exactly `B`, `B+1`, `S`, `S+1`, `E-1`, `E`, and
`E+1`; a skipped sequence does not replace exact-boundary assertions. The pinned
`titanoboa==0.2.7` runtime permits direct, independent assignment to
`boa.env.evm.patch.block_number` and `.timestamp`; no new runtime is needed.

### Conversion rule

The planning quanta are `qBase = 2 seconds` and `qRH = 12 seconds`. They are
configuration assumptions, not chain guarantees. For a duration whose approved
intent is `D` seconds:

```text
count(chain) = ceil(D / q(chain))
RH candidate = ceil(Base count / 6)
```

Round duration minima and maxima upward so a configured window is never shorter
than its approved wall-time intent. Zero delay remains zero. Never convert an
absolute operator-supplied number. To preserve a nominal monetary amount per unit
time, derive the rate from the approved rational amount per second and round only
once at the smallest token unit; `0.0075 RIPE * 6 = 0.045 RIPE` is exact. Current
integer allocation floors remain explicit protocol behavior; no hidden remainder
accumulator is introduced by configuration.

These conversion rules and all numeric candidates are **recommended/open**, not
approved.

## Current Base deployment evidence and version rule

Repository-generated parameter reports dated 2 December 2025 remain useful
historical evidence but are not current-chain proof. Read-only calls on 23 July
2026 through `https://base-rpc.publicnode.com`, anchored by the endpoint height
`49,026,989`, confirmed the key live scalar values used below. The current
manifest supplied the addresses; `eth_getCode` supplied the current runtime bytes.

| Contract | Manifest address | Runtime bytes | Keccak-256 runtime hash |
| --- | --- | ---: | --- |
| `Ledger` | `0x365256e322a47Aa2015F6724783F326e9B24fA47` | 12,970 | `0xdcb94574dd9e625451c96086c7a03c2516457e7ced0b9d3545bab4a005921b7d` |
| `Deleverage` | `0x62591b3058c1428FA4b5eD2160387725be285a64` | 24,135 | `0x40fb3758b1d04308fcea0752e04d8aefa39843c483a4f26ef9821e41a530f5cc` |
| `SwitchboardDelta` | `0xCdD15077231FEbe9e6393cf91d500984973FFcA0` | 21,712 | `0xdbb9504af5719965870d9911d101a975ed2539af19be6ade49b1aa75c6cfca5f` |
| `Lootbox` | `0x1f90ef42Da9B41502d2311300E13FAcf70c64be7` | 21,637 | `0xb3a2f6516aab23a9842e504b8cc8140167369b84d4f1f4fe787d76078019c6eb` |

The version rule is:

1. configuration-only Robinhood values do not require a Base runtime upgrade;
2. a canonical shared-source change creates a new version on both chains;
3. permanent source divergence is rejected;
4. temporary Base divergence is allowed only through an owner-approved,
   time-bounded rollout record with old/new code hashes, ABI compatibility,
   migration order, rollback, and closure evidence; and
5. no shared modification below is authorized until the owner approves its Base
   upgrade or bounded-drift plan.

## Authoritative BN and cadence disposition

The following two normalized tables jointly form the authoritative row for each
ID. Each `BN-*` and `CAD-*` appears exactly once in each table. “Live” means the
read-only Base call above; “dated” means the 2 December 2025 reports; “repo” means
source/default evidence only. Values in the `RH target` column remain candidates.

### Source, intent, values, and bounds

| ID; components | Contract/function; setter, validator, source | Category; current Base evidence | Intended meaning | Base target and bounds | RH target and bounds; conversion |
| --- | --- | --- | --- | --- | --- |
| BN-001; CM-001,002,009 | `Erc20Token.initiate/confirmHqChange`; `setHqChangeTimeLock`; immutable min/max; Blueprint/Defaults | Governance duration; live GREEN and RIPE `43,200`, bounds `43,200..302,400` | HQ authority waits 1d; governed range 1–7d | `43,200`; `43,200..302,400` | `7,200`; `7,200..50,400`; ceil duration `/6` |
| BN-002; CM-008,009,034 | `Ledger.checkAndUpdateLastTouch`; `MissionControl.shouldCheckLastTouch`; Delta setter; Defaults | Same-number security guard; live flag `true` | Current property: at most one checked higher-risk Teller housekeeping action per user per EVM `NUMBER`; Underscore callers are exempt | Policy unresolved; current Base stays enabled until replacement approval | Same shared policy; no cadence conversion |
| BN-003; CM-004,009–014,021,032 | inherited `LocalGov.start/confirmGovernanceChange`; governed setter; immutable Blueprint bounds | Governance duration; live HQ/VaultBook/PriceDesk `43,200`, bounds `43,200..302,400` | Governance replacement waits 1d, range 1–7d | `43,200`; `43,200..302,400` | `7,200`; `7,200..50,400`; ceil `/6` |
| BN-004; CM-011–014,016–020,032,039–041,046,050 | `TimeLock._initiateAction/_canConfirmAction/_isExpired`; action setter; immutable min/max and `expiration`; per-deployment config | Governance duration/window; live values in inheritor table below | Delay before a queued action, then finite exclusive confirmation window | Per inheritor below | Per inheritor below; ceil `/6`, zero preserved |
| BN-005; CM-005,032 | `Contributor.initiateRipeTransfer/confirm`; `keyActionDelay` constructor/config validation | Treasury duration; dated/repo `43,200` | RIPE transfer authority waits 1d | `43,200`; constructor term must be nonzero/not max | `7,200`; same semantic validator; ceil `/6` |
| BN-006; CM-005,032 | `Contributor.changeOwnership/confirm`; same `keyActionDelay` | Treasury/governance duration; dated/repo `43,200` | Contributor ownership transfer waits 1d | same BN-005 | same BN-005 |
| BN-007; CM-023,009,028 | `RipeGov` points checkpoint helpers; `RipeGovVaultConfig` asset weight/lock terms | Relative reward points; no cadence scalar | Prior checkpointed shares earn `shares * elapsed NUMBER`, then weight/lock bonus floors apply | Retain current formula pending rewards acceptance | Same formula candidate; no numeric target or implicit normalization |
| BN-008; CM-023,009,014 | `RipeGov` withdraw/early-release unlock; governed lock terms and validators | Lock duration; dated Base `43,200..47,304,000` | 1d minimum, 3y maximum governance lock | `43,200..47,304,000` | `7,200..7,884,000`; ceil `/6` |
| BN-009; CM-023,009,014 | `RipeGov.adjustLock`, bonus, weighted lock, refresh; same terms | Lock/bonus math; dated Base as BN-008 | Same wall-time lock and linear remaining-duration bonus | BN-008 bounds | BN-008 bounds |
| BN-010; CM-017,015,009 | `CurvePrices.getCurrentGreenPoolStatus`; governed `greenRefPoolConfig.staleBlocks`; migration | Base-only snapshot age; repo/migration `43,200` | Curve snapshot stale after about 1d | `43,200`; Base-only governed value | N/A: omit/de-register Curve; no converted RH value |
| BN-011; CM-017,015,030 | `CurvePrices._addGreenRefPoolSnapshot`; same config; feeds `CreditEngine` | Base-only same-number sampling and danger accumulation; repo/migration | At most one snapshot per `NUMBER`; accumulate observed danger-number gaps | Retain Base `43,200` staleness and raw behavior | N/A: Curve absent; assert no registration and base-rate fallback |
| BN-012; CM-044,014,034 | `Deleverage.deleverageForWithdrawal`; `setDeleverageCooldown`; Delta timelock; duplicate `MAX_COOLDOWN_BLOCKS` validators | Cooldown/security; live cooldown `0`, hard max `7,200` in two contracts | Limit repeated withdrawal deleverages while allowing multiple legs in one authorized withdrawal context and near-redemption safety bypass | Owner option A: max `7,200` (~4h); B: max `43,200` (~1d); configured value separately chosen | A: max `1,200`; B: max `7,200`; ceil `/6`; final value and bounds open |
| BN-013; CM-014,029 | `SwitchboardDelta.setStartEpochAtBlock`; BondRoom clamp; absolute governed input | Admin scheduling; no duration default | Operator supplies chain-native absolute start; stale input clamps to current `NUMBER` | Absolute Base height | Absolute RH EVM `NUMBER`; no conversion |
| BN-014; CM-029,009,014 | `BondRoom.purchaseRipeBond`; governed `ripeBondConfig` | Epoch duration; dated/repo `14,400`, restart `0` | 8h bond epoch; zero automatic restart delay | `14,400`, restart `0`; nonzero epoch | `2,400`, restart `0`; ceil `/6` |
| BN-015; CM-029,009 | `BondRoom.previewRipeBondPayout`; same config | View parity; same evidence BN-014 | Preview uses identical epoch and price progression | BN-014 | BN-014 |
| BN-016; CM-029,014 | `BondRoom.startBondEpochAtBlock`; absolute input | Admin scheduling | Same chain-native start rule as BN-013 | absolute Base height | absolute RH EVM `NUMBER`; no conversion |
| BN-017; CM-029,009,014 | `BondRoom._getLatestEpochBlockTimes`; epoch/restart config | Epoch catch-up; repo `14,400/0` | Advance to the unique epoch containing current `NUMBER`; skipped epochs issue no retroactive capacity | `14,400/0` | `2,400/0`; ceil `/6` |
| BN-018; CM-004,009 | `RipeHq.initiate/confirmHqConfigChange`; HQ registry delay | Capability-governance duration; live `21,600`, bounds `21,600..302,400` | Department/capability change waits 12h | `21,600`; `21,600..302,400` | `3,600`; `3,600..50,400`; ceil `/6` |
| BN-019; CM-004,010,015,021 | `AddressRegistry` add pending/confirm; governed registry delay, immutable bounds | Registry duration; live HQ/VaultBook `21,600`; PriceDesk setup value `0`; bounds vary by deployment | Add address waits 12h after setup | target `21,600`; HQ/VaultBook bounds `21,600..302,400`, PriceDesk blueprint min `3,600` | target `3,600`; proposed common RH bounds `3,600..50,400`, owner must accept one policy |
| BN-020; CM-004,010,015,021 | `AddressRegistry` update pending/confirm; same | Registry duration; same BN-019 | High-authority address replacement waits 12h | BN-019 | BN-019 |
| BN-021; CM-004,010,015,021 | `AddressRegistry` disable pending/confirm; same | Registry/emergency duration; same BN-019 | Current source gives disable same delay as add/update | BN-019 unless owner selects separate shared redesign | BN-019; owner must confirm shared delay |
| BN-022; CM-033,009,023 | `Lootbox` global/asset/user deposit checkpoints; rewards/point allocations | Relative reward points; repo, no cadence scalar | Prior balance/value earns points across elapsed `NUMBER`; allocation ratios, not supply, consume points | Retain pending rewards approval | Same formula candidate; no implicit multiplier |
| BN-023; CM-033,009,030 | `Lootbox` global/user borrow checkpoints; same | Relative reward points | Prior principal earns points across elapsed `NUMBER` | Retain pending rewards approval | Same formula candidate |
| BN-024; CM-033,009,028 | `Lootbox._getLatestGlobalRipeRewards`; governed `rewardsConfig.ripePerBlock` | Monetary emission; repo/dated `0.0075 RIPE` per number | Nominal `324 RIPE/day`, capped by available reward balance | `0.0075 RIPE`; current validator/config bounds retained | candidate `0.045 RIPE`; exact `*6`; tokenomics approval open |
| BN-025; CM-033,013,055 | `Lootbox.distributeUnderscoreRewards`; constructor/setter enforce `ONE_DAY`; Charlie governance | Hardcoded minimum interval; live interval `43,200` | Underscore sends no more often than one nominal day; feature is absent on RH | floor and default `43,200`; setter `< max`; current strict `>` eligibility retained unless separately approved | immutable floor `7,200`; feature disabled/omitted; ceil `/6` |
| BN-026; CM-033,055 | Lootbox distribution event `blockNumber`; consumers/reports | Telemetry; observed-number field | Record EVM `NUMBER`, which may repeat or jump | Retain | Retain and document; no conversion |
| BN-027; CM-048,046,009 | `EndaomentPSM` mint interval get/update; constructor and Echo-governed setter validate nonzero/not max | Capacity interval; live `43,200`; mint bucket independent | One nominal-day bucket; repeat shares capacity; equality starts one fresh bucket | `43,200`; `1..max-1` technical bounds, risk cap separately governed | candidate `7,200`; same validator; PSM deployed disabled and unregistered pending owner gates |
| BN-028; CM-048,046,009 | same for redeem bucket | Capacity interval; live `43,200`; separate redeem bucket | Same duration, separate accounting | BN-027 | BN-027 |
| BN-029; CM-030,009,011 | `CreditEngine._getAvailDebtInInterval`; MissionControl/Alpha governed debt config | Per-user capacity interval; repo/dated `43,200` | One nominal-day borrow bucket per user; equality refills once | `43,200`; nonzero config validation required in follow-on | candidate `7,200`; ceil `/6` |
| BN-030; CM-026,009,011,012 | `AuctionHouse._createOrUpdateFungAuction`; MissionControl default or asset override; Alpha/Bravo validator | Auction delay/duration; repo/dated `0/43,200`; duration nonzero/not max, delay not max | Zero delay and 1d exclusive auction window | delay `0`, duration `43,200` | delay `0`, duration candidate `7,200`; ceil `/6` |
| BN-031; CM-026,009 | `AuctionHouse._buyFungibleAuction`; active auction copies params | Eligibility/discount progression; same BN-030 | Eligible on `[start,end)`; linear integer discount from start toward max | BN-030 | BN-030 |
| BN-032; CM-038,029,014 | `BondBooster.getBoostRatio/_isValidBooster`; absolute `expireBlock`; governed `minLockDuration` | Absolute expiry plus duration floor; dated min lock `7,776,000` (~180d) | Booster expires exactly at supplied chain-native number; associated bond lock floor is 180d | absolute expiry; min lock `7,776,000` | absolute RH EVM `NUMBER`; candidate min lock `1,296,000`; ceil `/6` |
| CAD-001; CM-007,009,011,017,030,049,055 | `MissionControl.genDebtConfig.increasePerDangerBlock` consumed by `CreditEngine._getDynamicBorrowRate`; Alpha setter/validator; Defaults/report formatter | Indirect per-danger-number rate; raw Base `10`; report says `0.10%`, runtime ideal slope is `10/1,000,000 = 0.001%` before integer flooring | Increase dynamic debt-rate boost per Curve danger `NUMBER`, capped by configured max | raw `10`, retain runtime; fix display denominator to `1,000,000` | inactive explicit value while Curve omitted; future nominal candidate raw `60` (`*6`) only after risk approval |

### Profile behavior, implementation, approvals, and version effects

Abbreviations: `R` repeat, `+1` exact advance, `J` ordinary `+2/+4` jump,
`B` boundary skip, `S` stress `+60`. “Artifact” means production runtime bytecode.

| ID | Required profile result | Disposition and exact follow-on change | Tests | Owner/status | Artifact consequence; slice/dependency |
| --- | --- | --- | --- | --- | --- |
| BN-001 | R holds; +1/J reduce wait; B/S crossing confirm enables once; no expiry | Configuration-only: add RH constructor/default/bounds and migration values | token HQ before/exact/after confirm on all profiles | Protocol/security; recommended/open | Same source; RH artifact differs only immutables; S6 after parameter approval |
| BN-002 | R currently rejects all later checked calls; +1/J clear; B/S have no separate meaning | Shared-source change, separately gated: replace `NUMBER` identity only after threat choice; preserve locked-account check and Teller-only authority | same-user independent txs, nested/reentrant calls, borrow/withdraw/liquidation, Underscore exemption | Security; blocked pending threat/policy approval | New Ledger artifact and Base upgrade required; S5 |
| BN-003 | R holds; +1/J progress; B/S crossing opens once | Configuration-only RH LocalGov values | every deployable LocalGov flow at `B-1/B/B+1` | Protocol; recommended/open | No shared logic change; S6/S7 |
| BN-004 | R holds; +1/J progress; open at confirm; valid through expiry-1; invalid at expiry; B/S can erase window | Configuration-only per-inheritor values; require expiration headroom greater than approved stress jump | module plus every inheritor, including jump past entire window | Protocol/security; open | No logic change; S7 after headroom/value approval |
| BN-005 | R holds; +1/J progress; B/S opens once; timestamp vesting independent | Configuration-only key delay | transfer authority plus `MIXED` vesting | Treasury/protocol; open | No shared change; S6/S7 |
| BN-006 | same BN-005 | Configuration-only | ownership plus `MIXED` vesting | Treasury/protocol; open | No shared change; S6/S7 |
| BN-007 | R accrues zero; +1 one unit; J/S credit full gap to pre-jump shares; B can cross unlock and changes later bonus only | Retain candidate; no normalization unless rewards owner says absolute cross-chain points matter | deposit/change immediately before/after J/S; allocation conservation and floors | Rewards; blocked on attribution/economic approval | No artifact change if retained; S6/S8 |
| BN-008 | R holds lock; +1/J decrease; B/S crossing unlock enables withdrawal once | Configuration-only lock terms | `B-1/B/B+1`, early release, parameter change | Governance; open | No source change; S6/S8 |
| BN-009 | R freezes remaining duration; +1/J reduce and may floor bonus; pre-jump shares get elapsed points | Configuration-only terms; retain shared math | weighted deposit before/after J, exact min/max, term change | Governance/rewards; open | No source change; S6/S8 |
| BN-010 | R never ages; +1/J/S add snapshot age; B can become stale atomically | Base retain; RH omitted and unregistered | Base stale boundaries; RH manifest/routing absence | Oracle/risk; recommended/open | No new artifact; S9 |
| BN-011 | R suppresses later snapshot; +1 allows one; J/S add full gap to danger; B may cross staleness | Base retain; RH omitted; future enable requires separate spec | same-number suppression, J danger delta/cap, RH fallback | Oracle/risk; recommended/open | No new artifact; S9/S10 |
| BN-012 | R must not globally bypass cooldown; +1/J enforce until exact end; B/S at/past end allows; near-redemption bypass remains | Shared-source: one authoritative immutable max in `Deleverage`; Delta queries `maxDeleverageCooldown()`; replace same-number exception with explicit authorized withdrawal context; storage duration remains governed | independent same-N tx, authorized multi-leg same context, forged/reused context, exact expiry, near redemption | Security/protocol; blocked on duration and exception | New Deleverage/Delta and likely caller ABI; Base upgrade; S4 |
| BN-013 | R same clamp; +1/J/S clamp stale input to current | Retain; operator runbook says EVM `NUMBER`, not child height | past/equal/future input under both profiles | Governance/ops; recommended/open | No change; S8 |
| BN-014 | R freezes epoch/progress; +1 progresses; J/B/S may skip part/all, issuing no retroactive capacity | Configuration-only epoch/restart | start-1/start/start+1/end-1/end/end+1; one/multi epoch | Rewards/governance; open | No source change; S6/S8 |
| BN-015 | same BN-014 and preview equals execution at one state | Retain | quote/execution parity at every boundary/jump | Rewards; open | No source change; S8 |
| BN-016 | same BN-013 | Retain, operational documentation | absolute start tests | Governance/ops; recommended/open | No source change; S8 |
| BN-017 | R holds; +1 at end rolls; J/B/S selects containing epoch and skips earlier capacity | Retain catch-up; no per-skipped-epoch mint/capacity | exact end, +1, one/many skipped epochs | Rewards/governance; open | No source change; S8 |
| BN-018 | R holds; +1/J open; no expiry | Configuration-only HQ registry delay; CCIP Department sequence specified below | pool add, confirm, capability grant and negative pre-confirm calls | Protocol/security; open | No source change; S6/S7 |
| BN-019 | R holds; +1/J opens; no expiry | Configuration-only; owner resolves common delay/bounds | add at exact boundary; CCIP pool registration | Protocol/security; open | No source change; S7 |
| BN-020 | same BN-019 | Configuration-only | update including jump boundary | Protocol/security; open | No source change; S7 |
| BN-021 | same BN-019; emergency delay does not shorten on jump except elapsed count | Retain one shared delay unless owner requests separate design | disable and pending-add/update interaction | Protocol/security; blocked on shared-delay approval | No source change if retained; S7 |
| BN-022 | R zero; +1 one; J/S full gap to prior balances/value; B affects lock eligibility separately | Retain candidate; no automatic seconds conversion | old/new balance around jump, global/asset/user conservation and floors | Rewards; blocked on point attribution approval | No artifact change if retained; S6/S8 |
| BN-023 | same BN-022 for prior principal | Retain candidate | borrow/repay immediately around jump; user/global conservation | Rewards; blocked on attribution | No artifact change if retained; S6/S8 |
| BN-024 | R zero emission; +1 one rate unit; J/S full gap at prior rate, capped once; allocations floor and unallocated dust remains in available accounting | Configuration-only rate after tokenomics approval | rate change before/after J; cap, zero allocation, conservation, daily nominal comparison | Tokenomics/rewards; blocked | No source change; S6/S8 |
| BN-025 | R holds; +1/J progress; current strict `>` means exact `last+interval` remains too early; B/S past it enables | Shared-source: constructor immutable `MIN_UNDERSCORE_SEND_INTERVAL`, public getter, constructor/setter validator; no chain branch; preserve strict `>` for Base parity unless separately approved | min-1/min/min+1, constructor/setter, disabled RH no address/permission | Protocol/rewards; recommended/open | New Lootbox artifact and Base upgrade; S3 |
| BN-026 | R may duplicate; J/S may gap; no state semantics | Retain; document dashboards/indexers must key by tx/log identity, not number | repeated/gapped event consumer fixture | Data/ops; recommended/open | No protocol artifact change; S8 |
| BN-027 | R shares bucket; +1/J remain or cross; equality resets once; B/S crossing many intervals still resets once; no carry | Retain/configure; deploy disabled if Track 4 implementation approved, otherwise omit; changing interval mid-bucket immediately re-evaluates original start/amount | mint/redeem independence, exact equality, multi-interval J, interval shrink/grow, disabled flags | Risk/protocol; semantics recommended, value/activation open | No source change; S6/S8 after Track 4 gates |
| BN-028 | same BN-027, independent redeem bucket | same BN-027 | same, prove mint does not consume redeem | Risk/protocol; same status | No source change; S6/S8 |
| BN-029 | R shares per-user bucket; +1/J progress; equality refills once; B/S multiple elapsed intervals still one reset; no carry | Configuration-only MissionControl value | independent users, exact equality, J/S, repay with `MIXED` seconds interest | Risk/protocol; open | No source change; S6/S8 |
| BN-030 | R freezes window; +1/J progress; B/S may skip start or whole window; active auction retains copied params | Configuration-only default/asset override | start/end triplets, entire-window skip, future vs active parameter change | Risk/liquidation; open | No source change; S6/S8 |
| BN-031 | R same discount; +1/J integer progress; exact end rejects; B/S can make all prices unreachable | Retain/configure; require accepted skip policy and minimum duration greater than stress headroom | discount monotonicity/floors, exact end, skip-safe failure | Risk/liquidation; open | No source change; S8 |
| BN-032 | R valid; +1/J approach expiry; exact expiry invalid; B/S can expire atomically | Retain; operator derives absolute expiry from approved chain duration and current EVM `NUMBER` | before/exact/after expiry, units, min lock, stale admin input | Governance/rewards; open | No source change; S6/S8 |
| CAD-001 | R no new danger; +1 one raw step; J/S add gap then cap; RH has no active producer | Tooling correction and RH inactive configuration; change report field metadata/formatter from generic `100_00` to runtime denominator `1_000_000`; future raw `60` separately gated | raw `10`, display `0.001%`, runtime integer steps/cap; RH Curve absence | Risk/oracle; correction recommended/open, future slope blocked | Tool only, no runtime artifact; S10 |

## Deployable `TimeLock` inheritors

Read-only Base calls anchored by endpoint height `49,026,989` supersede the older
generated report where they disagree. An action delay of zero is reported as
current state, not endorsed as a launch value. `expiration` is headroom *after* `confirmBlock`;
confirmation is valid on `[confirmBlock, confirmBlock + expiration)`. The proposed
minimum invariant is `expiration >= approvedStressJump + 1`. With the candidate
stress jump `60`, that is at least `61`; every numeric candidate below exceeds it.
The protocol/security owner must approve every action delay, bound, expiration,
and any zero-delay posture.

| Inheritor; components | Live Base action / min / max / expiration | Base target | RH candidate action / min / max / expiration | Robinhood posture |
| --- | --- | --- | --- | --- |
| `SwitchboardAlpha`; CM-011 | `0 / 3,600 / 302,400 / 302,400` | current values pending owner review | `0 / 600 / 50,400 / 50,400` | deploy; zero action delay not final |
| `SwitchboardBravo`; CM-012 | `0 / 3,600 / 302,400 / 302,400` | current values pending owner review | `0 / 600 / 50,400 / 50,400` | deploy; zero action delay not final |
| `SwitchboardCharlie`; CM-013 | `0 / 3,600 / 302,400 / 302,400` | current values pending owner review | `0 / 600 / 50,400 / 50,400` | deploy; Underscore actions remain unusable |
| `SwitchboardDelta`; CM-014 | `0 / 3,600 / 302,400 / 302,400` | current values pending owner review | `0 / 600 / 50,400 / 50,400` | deploy; zero action delay not final |
| `SwitchboardEcho`; CM-046 | `0 / 3,600 / 302,400 / 302,400` | current values pending owner review | `0 / 600 / 50,400 / 50,400` | deploy if PSM deployed disabled; otherwise omit with PSM |
| `HumanResources`; CM-032 | `43,200 / 43,200 / 302,400 / 302,400` | retain 1d / 1d / 7d / 7d | `7,200 / 7,200 / 50,400 / 50,400` | deploy only if HR included |
| `ChainlinkPrices`; CM-016 | `0 / 3,600 / 302,400 / 302,400` | current values pending owner review | `0 / 600 / 50,400 / 50,400` | deploy; feed changes must still follow governance policy |
| `CurvePrices`; CM-017 | `14,400 / 14,400 / 302,400 / 302,400` | retain 8h / 8h / 7d / 7d | N/A | omit and do not register |
| `BlueChipYieldPrices`; CM-018 | `21,600 / 21,600 / 302,400 / 302,400` | retain 12h / 12h / 7d / 7d | N/A | omit and do not register |
| `PythPrices`; CM-019 | `0 / 3,600 / 302,400 / 302,400` | current values pending owner review | N/A | omit and do not register |
| `StorkPrices`; CM-020 | `0 / 3,600 / 302,400 / 302,400` | current values pending owner review | N/A | omit and do not register |
| `AeroRipePrices`; CM-050 | absent from current Base manifest | no live target established | N/A | omit and do not register |
| `wsuperOETHbPrices`; CM-039 | `0 / 3,600 / 302,400 / 302,400` | Base-only current values pending review | N/A | omit and do not register |
| `UndyVaultPrices`; CM-041 | `0 / 3,600 / 302,400 / 302,400` | Base-only current values pending review | N/A | omit and do not register |
| `RedStone`; CM-040 | `0 / 3,600 / 302,400 / 302,400` | current values pending owner review | N/A | omit and do not register |

Every deployed row gets the same boundary assertions: initiate at `I`; reject at
`I+delay-1`; accept at `I+delay`; accept at
`I+delay+expiration-1`; reject at `I+delay+expiration`; reject after
`BOUNDARY-WINDOW` and `R-STRESS60` jump past expiry. Changing a timelock affects
future queued actions; an already queued action retains its stored confirmation
and expiration.

The CCIP Department sequence is: register the approved pool address through the
RipeHq `AddressRegistry` add flow; wait and confirm using EVM `NUMBER`; initiate
the RipeHq capability config; wait and confirm; then verify only the approved pool
has `canMintGreen` (and separately `canMintRipe` if applicable). Before each
confirmation, after a cancelled/expired action, and for every unregistered
address, mint capability must be false.

## Shared semantic and configurability changes

### BN-002: Ledger guard — separate security gate

The current code-enforced property is precise: when the MissionControl flag is
true, a non-Underscore user's second higher-risk Teller housekeeping action with
the same EVM `NUMBER` reverts. Lower-risk calls and Underscore wallet/vault users
are not checked. This can prevent atomic sequencing of multiple debt-sensitive
actions, but the repository does not identify whether the protected threat is
reentrancy/nested execution, multiple separately ordered transactions before a
price/snapshot change, or both. Robinhood turns the property into a potentially
long multi-transaction throttle, so keeping it unchanged is not recommended.

The decision-ready replacement is:

- If the owner confirms the threat is nested/reentrant composition, use a
  transient per-user `higherRiskActionActive` guard entered by Teller for the
  whole top-level action and cleared by transaction end. Separate transactions
  are allowed.
- If the owner confirms a cross-transaction pacing threat, use an explicit
  governed minimum elapsed-seconds policy stored per user. The owner must select
  the seconds value and accept timestamp trust/bounds; a one-second placeholder
  is not approval.
- If both threats apply, use both layers. Do not use EVM `NUMBER` equality as the
  second layer.

The recommended starting point is both layers with the elapsed-seconds value left
unset until a security review demonstrates the required pacing. The implementation
must add explicit mode/value fields rather than silently repurpose
`shouldCheckLastTouch`; retain the Teller-only Ledger call, locked-account check,
and an event for governed persistent policy changes. Transient entry/exit needs no
persistent migration, but persistent last-action timestamps and policy config do.
The ABI should expose policy and last-action time for diagnostics. Base keeps the
old binary and enabled flag until its reviewed migration; Robinhood must not
launch the old policy.

Rejected designs are: `chain.id` branching; an injected Robinhood-only contract;
unconditionally setting the existing flag false; timestamp equality with no
elapsed-policy definition; `tx.origin`; and retaining `NUMBER` while merely
shrinking a duration. The security audit boundary includes Teller entry points,
delegated actions, reentrancy, liquidation/withdraw/borrow ordering, Underscore
exemptions, policy migration, and old-to-new Base behavior. Slice S5 remains
blocked until the security owner selects the threat and policy.

### BN-012: Deleverage ceiling and authorized call context

The shared mechanical design is:

1. add `_maxDeleverageCooldown` as a `Deleverage` constructor immutable and expose
   `maxDeleverageCooldown()`;
2. make the Deleverage setter the sole range validator;
3. make `SwitchboardDelta` query that getter before it queues a change, removing
   its duplicate constant;
4. enforce cooldown for every later independent call with
   `currentNumber < lastNumber + cooldown`, including `currentNumber == lastNumber`;
5. preserve exact-boundary eligibility at equality and the existing
   near-redemption safety bypass; and
6. replace the same-number exception with a transient, authorized withdrawal
   context.

For step 6, Teller opens a per-user transient context at the start of one
top-level `withdrawMany`/approved multi-leg flow and passes an opaque context ID
to each Deleverage leg. Deleverage accepts same-context follow-up legs only from
the registered Teller (or another separately approved coordinator), only in that
transaction, and only for that user. A direct or Underscore call without an open
context receives no multi-leg bypass. Transient state makes cross-transaction
reuse impossible; explicit caller/user binding prevents a forged context. The
implementation may preserve the old four-argument entry point as a no-context
wrapper if ABI compatibility is required.

No new persistent cooldown storage is needed; current `lastDeleverageBlock`
continues to govern NUMBER-denominated duration. Constructor ABI, Deleverage
getter, Delta interface, Teller/authorized coordinator interface, deployment
arguments, defaults, migrations, ABIs, and events for the governed cooldown all
require review. The owner must choose 4h versus 1d maximum and the authorized
coordinator set before S4. A duration change applies to the existing
`lastDeleverageBlock` immediately, matching current storage semantics.

Rejected designs are the current same-number check, `msg.sender` alone as context,
`tx.origin`, a reusable persistent bypass nonce, duplicate hard caps, and
chain-specific source. The audit boundary is cooldown arithmetic/overflow,
near-redemption bypass, transient lifetime, caller authorization, nested calls,
multi-asset withdrawals, old ABI compatibility, and Base migration.

### BN-025: Lootbox interval floor

Replace `ONE_DAY` with constructor immutable
`MIN_UNDERSCORE_SEND_INTERVAL`, expose
`minUnderscoreSendInterval()`, and use it in the constructor and governed setter.
The minimum is immutable because governance must not be able to weaken the
deployment's owner-approved floor. Keep the existing event and stored governed
interval. Add the constructor argument to Base (`43,200`) and Robinhood (`7,200`)
deployment/default paths; Robinhood still omits or disables Underscore and must
have no distributor registration or rewards permission.

For bounded Base parity, retain current strict eligibility
`NUMBER > lastSend + interval`; this means equality is still too early. Changing
it to `>=` is a separate semantic decision, not smuggled into parameterization.
Existing Base storage is compatible, but the constructor/ABI and runtime artifact
change, so Base needs a new deployment/version plan. No persistent migration is
otherwise required.

Rejected designs are `chain.id`, a mutable zero floor, leaving the Base constant
in shared source because Robinhood disables the feature, and silently changing
the exact boundary. S3 requires protocol/rewards approval of the immutable design
and Base rollout.

### CAD-001: units and inactive Robinhood path

The raw governed value is an integer numerator over the runtime denominator
`1,000,000`. Raw `10` therefore has an ideal slope of `0.001%` per danger number,
subject to the contract's integer-step order and cap. The generic report formatter
currently divides by `10,000` and prints `0.10%`, 100 times too high.

The follow-on tool change must attach field-specific unit metadata to
`increasePerDangerBlock`, render raw `10` as `0.001%`, and regression-test the raw
default, display, runtime integer outputs for danger counts `0,1,2,99,100` and the
configured cap. Robinhood defaults must contain an explicit inert value and its
deployment must prove there is no Curve producer or PriceDesk registration. Raw
`60` is only a future nominal `/6` cadence candidate if Curve is separately
reenabled and risk-approved. The report correction changes no protocol bytecode.

## Economic attribution, rounding, and conservation

RipeGov and Lootbox points are relative allocation measures inside one chain. A
uniform cadence factor cancels from ideal ratios, so the recommendation is no
numeric cadence multiplier and no shared normalization change. This does **not**
make jump attribution harmless: on a jump, the full elapsed gap belongs to the
shares, USD value, or principal saved at the prior checkpoint. Tests therefore
mutate a balance/rate immediately before and immediately after `+2`, `+4`, and
`+60` and prove the old value receives the entire gap and the new value starts at
the checkpoint.

Current arithmetic floors shares, weights, lock bonuses, user/global ratios, and
reward-bucket allocations. There is no accumulated remainder. In
`_getLatestGlobalRipeRewards`, the entire `newRipeDistro` is charged against the
available reward budget when allocations are nonzero even if per-bucket integer
floors sum to less than that amount; the dust is not assigned to a bucket. The
specification does not silently change this. Tests must measure the dust and the
tokenomics owner must either approve it or open a separate accumulator/remainder
design.

At nominal cadence, Base `0.0075 * 43,200 = 324 RIPE/day`; the Robinhood candidate
`0.045 * 7,200 = 324 RIPE/day`. `R-REP128` emits zero until the next number,
`R-J2-J4` emits `2*rate` at each jump to the pre-jump rate, and `R-STRESS60` emits
`60*rate`, capped once by `ripeAvailForRewards`. A governed rate change immediately
before a jump applies the new rate to the whole uncheckpointed gap unless the
configuration flow checkpoints first. The implementation test must expose that
ordering and the rewards owner must approve it. S6/S8 remain blocked for point
and emission economics even though unrelated mechanical slices may proceed.

## Capacity, auctions, bonds, locks, and price sources

CreditEngine, PSM mint, and PSM redeem use a half-open active bucket:
`start != 0 && start + interval > NUMBER`. Equality is fresh. A jump over any
number of intervals resets exactly once at the first subsequent use; unused
capacity does not carry and missed intervals do not accumulate. Mint and redeem
are independent. A governed interval change immediately re-evaluates the current
stored start and amount, so shortening can end a bucket and lengthening can
extend it. Combined tests hold NUMBER while advancing timestamp interest, then
jump NUMBER while holding timestamp, proving CreditEngine interest remains
seconds-based.

Track 4's integrated result is `go — existing feed`, but it does not authorize
deployment or activation. If its later owner gates approve implementation, PSM is
deployed with `canMint=false`, `canRedeem=false`, no GREEN mint authority, and the
approved reserve naming; Echo is present so a later governed enablement exists.
Otherwise PSM/Echo are omitted. Both outcomes test no active price/mint path.

Auction eligibility is exactly `[startBlock,endBlock)`. Discount progression is
integer-floored from `(NUMBER-start)*10,000/(end-start)`. A jump may make prices
unreachable or skip the entire auction, which must fail closed at/after `end`.
Parameters are copied into an auction, so a governed parameter change affects
future auctions and does not rewrite an active one. BondRoom similarly computes
the unique epoch containing current NUMBER, skips any intervening epoch capacity,
and keeps preview/execution identical. RipeGov and BondBooster use exact expiry:
valid before, invalid at equality. These jump/skip policies and their candidate
durations require risk/rewards/governance approval.

Curve's same-number suppression and danger count remain Base-only. Chainlink,
Pyth, Stork, RedStone, BlueChip, Aero, Undy, and wrapped-yield timestamp checks
remain seconds-domain. On Robinhood only approved Chainlink sources are initially
registered; every omitted adapter and external integration gets manifest absence,
zero registry entry, no permission, and PriceDesk routing failure assertions.

## Timestamp-context disposition

Each integrated `TS-*` appears exactly once. “No conversion” explicitly means no
Robinhood-only change is required.

| ID; components | Seconds-domain purpose and NUMBER interaction | Disposition; mixed-clock/omission test | Config/default implication |
| --- | --- | --- | --- |
| TS-001; CM-001,002 | EIP-2612 signed deadline; independent of BN-001 HQ delay | Retain; `MIXED` exact deadline/future/expired signature; no conversion | Unix-seconds input remains |
| TS-002; CM-005,032 | Contributor start, cliff, end, unlock, vesting; mixed with BN-005/006 authority delay | Retain; advance each clock alone through vesting and authority boundaries; no conversion | Seconds terms unchanged |
| TS-003; CM-019 | Pyth publish-time staleness/future check; no NUMBER dependency | Disabled on RH; Base fresh/stale/future and RH omission; no conversion | Seconds stale config retained on Base |
| TS-004; CM-018 | BlueChip snapshots, delay, staleness and same-timestamp guard | Disabled on RH; Base repeated timestamp and stale/future plus RH omission; no conversion | Seconds values remain |
| TS-005; CM-016 | Chainlink `updatedAt` future/stale checks; coexists with BN-004 governance | Retain; `MIXED` stale/future at held NUMBER and governance at held timestamp; no conversion | Approved feed heartbeat/stale seconds only |
| TS-006; CM-050 | Aero snapshots/delay/staleness | Disabled on RH; Base domain tests and RH omission; no conversion | Seconds Base config remains |
| TS-007; CM-020 | Stork publish-time staleness | Disabled on RH; Base stale/future and RH omission; no conversion | Seconds Base config remains |
| TS-008; CM-041 | Undy vault snapshot delay/staleness | Disabled on RH; Base repeated timestamp and RH omission; no conversion | Seconds Base config remains |
| TS-009; CM-040 | RedStone future/stale oracle timestamp | Disabled on RH; Base stale/future and RH omission; no conversion | Seconds Base config remains |
| TS-010; CM-030,009 | Credit interest elapsed seconds while BN-029 limits borrow capacity | Retain; hold NUMBER/advance time, then jump NUMBER/hold time; no conversion | `ONE_YEAR` and rate units remain seconds |
| TS-011; CM-004,010,015,021 | AddressRegistry `lastModified` telemetry while BN-019–021 authorize changes | Retain; confirmation driven only by NUMBER, telemetry only by timestamp; no conversion | Consumer docs must not infer delay from timestamp |

## Checked inventory and future CI contract

The canonical follow-on artifact is
`config/block-clock-inventory.json`, schema version 1. It contains:

```json
{
  "schemaVersion": 1,
  "productionRoots": ["contracts"],
  "excludedProductionGlobs": ["contracts/mock/**"],
  "directOccurrences": [
    {
      "id": "BN-001",
      "path": "contracts/tokens/modules/Erc20Token.vy",
      "function": "initiateHqChange",
      "normalizedExpression": "block.number",
      "ordinalInFunction": 1,
      "semanticReview": {"owner": "protocol", "status": "reviewed", "commit": "..."}
    }
  ],
  "indirectCadence": [],
  "timestampContext": [],
  "allowedNonProductionGlobs": ["tests/**", "contracts/mock/**"]
}
```

Line numbers are diagnostics, not identity. The stable occurrence key is
`path + function + normalizedExpression + ordinalInFunction`. The checker parses
Vyper function boundaries, normalizes whitespace only, and performs a separate
fixed-string count so parser omissions cannot hide occurrences. A moved
occurrence with the same function/expression is reported as moved; a rename,
addition, removal, duplicate, or changed expression is unmapped until semantic
review updates the record.

`scripts/check_block_clock_inventory.py --check` and
`pytest -q tests/inventory/test_block_clock_inventory.py` must both:

- find exactly 100 literal production `block.number` occurrences on the launch
  baseline, 95 matching lines, and 17 files, while reporting mock/test counts
  separately;
- map every literal occurrence to exactly one `BN-*`;
- validate all 32 BN records, CAD-001, and 11 timestamp-context records;
- scan production/config/migration/tool paths for approved cadence patterns,
  including `*_IN_BLOCKS`, `BLOCKS`, `ONE_DAY`, `staleBlocks`,
  `numBlocksPerInterval`, `ripePerBlock`, `increasePerDangerBlock`, cadence
  comments, Base/RH defaults, and generated report metadata;
- keep `block.timestamp` and `*_IN_SECONDS` in the separate TS domain;
- fail on an unmapped addition, missing occurrence, duplicate mapping, moved
  occurrence requiring review, stale count, new indirect pattern, or schema
  record without non-placeholder semantic owner/status/commit;
- print the source path, function, current line, normalized snippet, candidate
  stable ID, direct/indirect domain, active baseline count, and remediation; and
- refuse an “ignore” entry with no semantic review rather than teaching authors
  to suppress findings.

The local command is:

```bash
python scripts/check_block_clock_inventory.py --check
pytest -q tests/inventory/test_block_clock_inventory.py
```

The future CI job, once an owner selects a repository CI integration point, runs
the same two commands and `git diff --check`; no new dependency is needed. The
protocol/security owner owns BN semantics, risk/oracle owns CAD entries, and the
author of a source change must obtain their review. The repository currently has
no committed `.github` workflow, so S2 ends with a locally executable guard and
leaves CI wiring explicitly open.

## Follow-on implementation slices

Migration IDs and the Robinhood migration namespace belong to Track 7. Where a
row says “Track 7-reserved migration,” the exact path must be reserved and added
to that slice before kickoff; this is a prerequisite, not permission to improvise
one. No slice may combine with S5 merely because both touch a clock.

| Slice | IDs/components; exact expected files | Prerequisites and owner decisions | Artifact/Base policy | Commands and acceptance | Review, abort, and consumer |
| --- | --- | --- | --- | --- | --- |
| S1 — harness foundation | all BN/CAD/TS; CM-059. New `tests/utils/clock_profiles.py`, `tests/clock/test_clock_profiles.py`; update `tests/conftest.py` only to register fixture | Approve `J2/J4` and stress `+60`; pinned Boa/pytest already sufficient | Test-only; identical compiled artifacts, no production bytecode | `pytest -q tests/clock/test_clock_profiles.py`; prove exact sequences, independent clocks, trace output, snapshot isolation | Test-infra review; abort on runtime auto-mining or non-isolation; consumed by S3–S10 |
| S2 — checked inventory | BN-001–032, CAD-001, TS-001–011; CM-055,059. New `config/block-clock-inventory.json`, `scripts/check_block_clock_inventory.py`, `tests/inventory/test_block_clock_inventory.py` | Approve inventory ownership and local/CI posture; no CI dependency selected here | Tool/test only | the two commands above; baseline 100/95/17; mutation tests add/remove/move/direct/indirect dependencies and must fail | Protocol/security + tooling review; abort if parser can suppress fixed-string delta; consumed by every source PR |
| S3 — Lootbox floor | BN-025/026; CM-033,013. `contracts/core/Lootbox.vy`, `contracts/config/DefaultsBase.vy`, future `contracts/config/DefaultsRobinhood.vy`, `tests/core/lootbox/test_underscore_rewards.py`, `tests/config/test_switchboard_charlie.py`, `scripts/abis/Lootbox.json`, Track 7-reserved RH and owner-reserved Base migrations | Approve immutable floor, strict `>` parity, Base rollout | New Lootbox bytecode/constructor; Base deploy/rewire required, old/new hash record and rollback | targeted pytest files plus S1/S2; Base 43,200 and RH 7,200 floor/min-1/min/min+1; RH distributor absent | Protocol/rewards + contract audit; abort before migration if ABI/rewire plan incomplete; consumed by S6/Track 7 |
| S4 — Deleverage cooldown/context | BN-012; CM-044,014,034. `contracts/core/Deleverage.vy`, `contracts/config/SwitchboardDelta.vy`, `contracts/core/Teller.vy`, `tests/core/deleverage/test_deleverage_for_withdrawal.py`, `tests/config/test_switchboard_delta.py`, `tests/core/teller/test_teller_withdraw.py`, `scripts/abis/Deleverage.json`, `scripts/abis/SwitchboardDelta.json`, `scripts/abis/Teller.json`, Track 7-reserved RH and owner-reserved Base migrations | Owner selects 4h vs 1d, configured default, Teller context, ABI compatibility, Base rollout | New Deleverage/Delta/Teller bytecode; coordinated Base upgrade | targeted suites plus S1/S2; independent same-N call blocked; only bound transient context bypasses; exact expiry and near-redemption pass | Security audit mandatory; abort if context is reusable/forgeable or migration cannot be atomic; consumed by S6/Track 7 |
| S5 — Ledger portable guard | BN-002; CM-008,009,014,034. `contracts/data/Ledger.vy`, `contracts/core/Teller.vy`, `contracts/data/MissionControl.vy`, `contracts/config/SwitchboardDelta.vy`, `contracts/config/DefaultsBase.vy`, future `contracts/config/DefaultsRobinhood.vy`, `tests/data/test_ledger.py`, `tests/core/teller/test_teller_withdraw.py`, `tests/core/creditEngine/test_credit_borrow.py`, `tests/config/test_switchboard_delta.py`, `scripts/abis/Ledger.json`, `scripts/abis/Teller.json`, `scripts/abis/MissionControl.json`, `scripts/abis/SwitchboardDelta.json`, reserved migrations | Security owner identifies protected threat and chooses nested, elapsed-seconds, both, or explicitly accepts disable; approve seconds and Base rollout | New Ledger and possibly Teller/MissionControl/Delta bytecode; no permanent Base divergence | targeted suites plus S1/S2; exact selected property, locked accounts, delegation, Underscore, reentrancy, migration | Independent security PR/audit; abort if threat remains ambiguous or seconds trust is unacceptable; consumed by Track 7 only after approval |
| S6 — per-chain defaults/bounds/rates | BN-001,003–009,012–025,027–032, CAD-001; CM-007,009,049,055,060. New `contracts/config/DefaultsRobinhood.vy` and `tests/config/test_defaults_robinhood.py`; `config/BluePrint.py`, `contracts/config/DefaultsBase.vy` only for approved shared constructor interfaces, `scripts/params/params_utils.py`, `scripts/params/general.py`, `scripts/params/regenerate_defaults.py`, Track 7-reserved RH migrations | Approve every included parameter; point/emission economics; Track 4 activation fields; S3/S4 interfaces if included | Chain default artifact/config changes; core artifacts only where approved constructors changed; existing Base values otherwise unchanged | defaults/config/parameter tests plus S1/S2; generated table equals approved manifest and rejects Base/local fallback | Protocol, risk, tokenomics, deployment reviews; omit any unresolved field/slice rather than guess; consumed by S7–S9/Track 7 |
| S7 — timelock/registry flows | BN-001,003–006,018–021; CM-001,002,004,005,010–021,032,046. `tests/modules/test_time_lock.py`, `tests/modules/test_local_gov.py`, `tests/core/humanResources/test_hr_contributor.py`, `tests/core/humanResources/test_hr_add_contributor.py`, `tests/registries/test_address_registry.py`, `tests/registries/test_ripe_hq.py`, `tests/tokens/test_erc20.py`, `tests/config/test_switchboard_alpha.py`, `tests/config/test_switchboard_bravo.py`, `tests/config/test_switchboard_charlie.py`, `tests/config/test_switchboard_delta.py`, `tests/config/test_switchboard_echo.py`, `tests/priceSources/test_chainlink_prices.py`, `tests/priceSources/curve/test_curve_prices.py`, `tests/priceSources/blueChip/test_bluechip_local.py`, `tests/priceSources/test_pyth_prices.py`, `tests/priceSources/test_stork_prices.py`, `tests/priceSources/test_aero_ripe.py`, `tests/priceSources/test_superoethb.py`, `tests/priceSources/test_undy_vault_prices.py`, new `tests/priceSources/test_redstone_prices.py`, new `tests/integration/test_ccip_department_registration.py` | Approve per-inheritor table, expiration headroom, one registry delay, CCIP pool authority facts | Tests/config only unless S6 changes deployment args; no shared runtime logic | targeted suites plus S1/S2; every inheritor exact open/expiry/jump; CCIP pool has no capability early | Protocol/security/CCIP review; abort on jump-erased approved window; consumed by Track 7/CCIP implementation |
| S8 — capacity/economic lifecycle tests | BN-007–009,013–017,022–024,027–032; TS-010; CM-023,026,029,030,033,038,048. `tests/vaults/test_ripe_gov_vault.py`, `tests/core/lootbox/test_loot_deposit_points.py`, `tests/core/lootbox/test_loot_borrow_points.py`, `tests/core/lootbox/test_loot_ripe_rewards.py`, `tests/core/endaoment/test_endaoment_psm_mint.py`, `tests/core/endaoment/test_endaoment_psm_redeem.py`, `tests/core/endaoment/test_endaoment_psm_config.py`, `tests/core/creditEngine/test_credit_borrow.py`, `tests/core/creditEngine/test_credit_dyn_rate.py`, `tests/core/auctionHouse/test_ah_auctions.py`, `tests/core/bondRoom/test_ripe_bonds.py`, `tests/config/test_bond_booster.py`, new `tests/integration/test_block_clock_lifecycle.py` | Approved points/emission, capacity, auction, epoch, lock, PSM fields and jump policy | Test/config only; no chain-specific artifact | targeted suites plus S1/S2; every exact boundary, one/multi epoch jump, no carry, mint/redeem independence, preview parity, seconds interest | Risk/rewards/tokenomics review; abort dependent cases only when their decision is open; consumed by Track 7 |
| S9 — disabled price integrations | BN-010/011/025/027/028, TS-003/004/006–009, CAD-001; CM-017–020,035–042,048,050. New `tests/integration/test_robinhood_disabled_integrations.py` and `tests/deployment/test_robinhood_manifest.py`; the Track 7-reserved RH manifest path | Approved deployment graph; Track 4 outcome | No disabled contract needs RH bytecode; Base unchanged | targeted price tests plus S1/S2; no address, registry row, permission, route, Curve danger producer, Underscore distributor, or active PSM flags | Oracle/risk/deployment review; abort launch on any accidental registration; consumed by Track 7 |
| S10 — CAD report correction | CAD-001; CM-055. `scripts/params/params_utils.py`, `scripts/params/general.py`, new `tests/scripts/test_params_cadence_units.py`; regenerated reports only after owner authorizes generated-output update | Approve field-specific denominator and report regeneration; future RH raw rate remains separate | Tooling only | `pytest -q tests/scripts/test_params_cadence_units.py`; raw 10/display 0.001%/runtime steps; S2; report diff reviewed | Risk/oracle + tooling review; abort if generic percent fields change unexpectedly; consumed by S6 parity reporting |

The aggregate full-suite command after each implementation slice remains
`pytest -q`; slice-specific commands run first for diagnostics. Formatting and
repository validation commands are added only from existing project tooling; a
new dependency returns to owner approval.

## Decision register

Recommendations are not approvals. No clock parameter in this register is final.

| Decision | Options | Evidence | Recommendation | Affected IDs/components | Owner | Needed before | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Shared clock posture | retain/configure; timestamp conversion; redesign all | Track 3 separates acceptable clocks from BN-002/012/025 defects | Retain observed-number semantics where valid; redesign only demonstrated failures; no chain branch | all BN/CAD; CM-007–059 | Protocol/security | S3–S9 | recommended/open |
| Cadence basis | 2s/12s; other measured quantile; no wall-time mapping | Base/Arbitrum docs and RH sample | 2s Base, 12s RH nominal; ceil duration `/6`; label assumptions | duration/rate IDs | Protocol/risk | S6 | recommended/open |
| Representative jumps | `+2/+4`; another set | RH live `+2`; Arbitrum example `+4` | approve `+2/+4` | all number IDs; CM-059 | Protocol/security | S1 | recommended/open |
| Stress jump | `+60`; larger owner value; no stress | no authoritative max; occasional longer sync documented | test `+60` as conservative, not maximum | all number IDs; CM-059 | Protocol/security/risk | S1 and parameter signoff | recommended/open |
| Shared-change Base policy | coordinated upgrade; time-bounded drift; permanent divergence | live hashes above; canonical-source constraint | coordinated upgrade, with bounded drift only as explicit fallback | BN-002/012/025; CM-008,014,033,044 | Protocol/security/deployment | S3–S5 | open |
| Ledger threat | nested/reentrant; cross-tx pacing; both; disable accepted | current one-checked-action-per-NUMBER property, no threat document | security review selects threat before code | BN-002; CM-008,009,034 | Security | S5 | blocked |
| Ledger replacement | transient guard; elapsed-seconds; both; explicit disable | repeated RH NUMBER makes current guard a long throttle | both layers if both threats confirmed; seconds unset until evidence | BN-002 | Security | S5 | blocked |
| Deleverage maximum | Base 7,200/RH 1,200 (~4h); Base 43,200/RH 7,200 (~1d) | code cap vs comment intent conflict; live value 0 | owner resolves intent | BN-012; CM-014,044 | Security/protocol | S4/S6 | blocked |
| Deleverage exception | authorized transient context; no exception; retain same NUMBER | multi-leg intent and repeated-number bypass | authorized user/caller-bound transient context | BN-012 | Security/protocol | S4 | recommended/open |
| Lootbox interval floor | immutable constructor floor; governed floor; retain constant | Base hardcode rejects RH day | immutable per-deployment floor; strict `>` retained | BN-025; CM-033 | Protocol/rewards | S3 | recommended/open |
| Point attribution | prior checkpoint gets full gap; seconds normalization; checkpoint-before-config | current RipeGov/Lootbox math | retain prior-checkpoint gap attribution only with rewards acceptance | BN-007,022,023; CM-023,033 | Rewards/tokenomics | S6/S8 | blocked |
| RIPE emission | RH 0.045; retain 0.0075; new economics | 324/day nominal comparison; jump/cap behavior | 0.045 candidate, current floor/dust explicit | BN-024; CM-033 | Tokenomics/rewards | S6/S8 | blocked |
| Timelocks and headroom | table values; revised values; zero-delay policy | live calls and `+60` profile | ceil `/6`, expiry at least stress+1; review every live zero | BN-001,003–006,018–021; CM-001–021,032,046 | Protocol/security | S6/S7 | open |
| Registry action policy | one delay; separate disable delay via shared redesign | current shared field | retain one 12h intent only if owner accepts disable latency | BN-019–021 | Protocol/security | S6/S7 | blocked |
| Capacity refill | one reset/no carry; catch up every elapsed interval | current CreditEngine/PSM code and Track 4 | preserve one reset/no carry, independent PSM buckets | BN-027–029; CM-030,048 | Risk/protocol | S6/S8 | recommended/open |
| Auction/bond skip | current containing-window behavior; catch-up issuance; fail | current source skips unreachable windows/capacity | preserve skip/no retroactive capacity; require minimum approved duration | BN-014–017,030/031 | Risk/rewards/governance | S6/S8 | recommended/open |
| Lock/booster values | converted table; alternate product terms | dated Base terms and exact expiry code | ceil `/6`, absolute inputs chain-native | BN-008/009/032 | Governance/rewards | S6/S8 | open |
| Disabled price/dynamic rate | omit; deploy unregistered; enable | selected architecture, Track 3, Track 4 | omit unsupported adapters; PSM disabled if deployed; CAD inert | BN-010/011/025/027/028, CAD-001; price CMs | Oracle/risk/protocol | S6/S9 | recommended/open |
| CAD report correction | field metadata; special-case formatter; leave wrong | raw/display/runtime trace | field-specific denominator metadata and regression | CAD-001; CM-055 | Risk/oracle/tooling | S10 | recommended/open |
| Harness mechanism | Boa patch; Anvil; new runtime | pinned Boa direct patch verified | Boa patch with snapshot/reset; no dependency | all; CM-059 | Engineering/test | S1 | recommended/open |
| Inventory/CI integration | script+pytest local; future CI; workflow now | no committed `.github`; fixed-string baseline | script+pytest now, identical future CI command | all; CM-055,059 | Protocol/security/tooling | S2 | recommended/open |
| PSM posture consumed from Track 4 | omit; deploy disabled; activate | integrated `go — existing feed`; activation gates remain | if implemented, deploy disabled/no GREEN mint; otherwise omit | BN-027/028; CM-046,048 | Track 4 owners/risk | S6/S8/S9 | approved only as Track 4 decision; activation blocked |

## Approval boundary and completion

This specification intentionally stops before every owner gate. The unresolved
decisions above block only their listed slices: S1/S2 analysis tooling can proceed
after their narrow mechanism/ownership approvals; S3, S4, S5, economic portions
of S6/S8, and parameterized governance flows cannot.

The following Section 2 surfaces are eligible for owner review, not closure:
shared clock posture and profiles; BN-002 guard threat/policy; BN-012 duration and
context; BN-025 immutable floor; point/emission economics; all timelocks,
capacities, auctions, epochs, and locks; disabled price/dynamic-rate posture;
CAD-001 reporting; harness; inventory guard; and Base rollout policy.
`rh-summary.md` remains unchanged.

The specification is reproducible from the recorded launch commit and hashes,
dispositions BN-001–BN-032, CAD-001, and TS-001–TS-011, records current Base
runtime hashes and live scalar evidence, contains no chain-specific runtime
branch, and assigns every implementation change to a separately reviewable
follow-on slice.
