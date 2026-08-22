# PR #67 lane synthesis — Lane 3B

Draft only. Not a source of truth. If this file and the contracts disagree,
the contracts win.

- master: 91eda49ccd34a25090582aff0695075c4c806011
- rh:     251ac9e228a8af80326e8fe30f607511c78fe820
- date:   2026-08-22

# PR #67 behavior delta — Lane 3B — 91eda49c vs 251ac9e2

Pins verified:

- master `91eda49ccd34a25090582aff0695075c4c806011`, tree `fbd958bec234081f70769045abd8f9bb638f6dd7`
- rh `251ac9e228a8af80326e8fe30f607511c78fe820`, tree `204de8657d9cd2eded1212028b9b5ba8d87b6506`

All R1–R5 matched the lane and pins; none was skipped. This was read-only: no fetch, branch, worktree, edits, tests, compilers, or repository scripts.

## Brief

### VERIFIED — SOURCE-REACHABLE

- **BD-01 Token-scale valuation gate** — R1:J-DESK-SCALE; R2:UC-J-01; R3:UC-J-02; R4:J-02; R5:J-01.
- **BD-02 Token-scale lifecycle/onboarding** — R1:J-DESK-SCALE; R2:UC-J-01; R3:UC-J-05; R5:J-01.
- **BD-03 Price-source quote isolation and 250k stipend** — R1:J-DESK-ISOLATE; R2:UC-J-02; R3:UC-J-03; R4:J-01; R5:J-02/J-03.
- **BD-04 `hasPriceFeed` isolation** — R1:J-DESK-ISOLATE; R2:UC-J-10; R3:UC-J-03; R4:J-03; R5:J-15.
- **BD-05 Snapshot fanout isolation** — R1:J-DESK-ISOLATE; R2:UC-J-10; R3:UC-J-03; R4:J-03; R5:J-15.
- **BD-06 Caller-supplied PriceDesk stale bound** — R1:J-STALE-MIN; R2:UC-J-03; R3:UC-J-01; R4:J-04; R5:J-16.
- **BD-08 Pyth batch-update ABI** — R1:J-KEEPER-UPDATE; R3:UC-J-12; R4:J-14.
- **BD-09 Stork typed batch-update ABI** — R1:J-KEEPER-UPDATE; R3:UC-J-12; R4:J-14.
- **BD-10 GREEN ratio model** — R1:J-CURVE-BORROW; R2:UC-J-07; R3:UC-J-15; R5:J-14.
- **BD-11 GREEN danger/recovery model** — R1:J-CURVE-BORROW; R2:UC-J-07; R3:UC-J-15; R5:J-14.

### VERIFIED — CONFIGURATION-CONTINGENT

- **BD-07 RedStone nested stale-bound forwarding** — R1:J-STALE-MIN; R2:UC-J-03; R3:UC-J-01; R4:J-04; R5:J-16.
- **BD-12 Runtime oracle freshness: `max` → nonzero `min`** — R1:J-STALE-MIN; R2:UC-J-03; R3:UC-J-10; R4:J-04; R5:J-04.
- **BD-13 Oracle admission freshness** — R2:UC-J-03; R4:J-04.
- **BD-14 Future Pyth/Stork timestamps** — R1:J-FUTURE-SOFT; R2:UC-J-04; R3:UC-J-09/11; R4:J-05; R5:J-06/J-07.
- **BD-15 Stork signed runtime values** — R2:UC-J-04; R3:UC-J-09; R4:J-05; R5:J-06.
- **BD-16 Stork admission validation** — R2:UC-J-04; R3:UC-J-09; R4:J-05.
- **BD-17 Chainlink conversion-feed freshness** — R4:J-04; R5:J-05.
- **BD-18 Chainlink empty conversion-feed guard** — R2:UC-J-02; R5:J-05.
- **BD-19 RedStone direct-helper empty-feed guard** — R2:UC-J-02; R5:J-05.
- **BD-20 Aero RIPE pricing removal** — R1:J-AERO-INERT; R2:UC-J-09; R3:UC-J-06; R4:J-11; R5:J-08.
- **BD-21 Aero administrative retirement/inert compatibility surface** — R2:UC-J-09; R3:UC-J-06.
- **BD-22 MCBETH/VVV removal from wsuperOETHbPrices** — R1:J-VVV-UNPRICED; R2:UC-J-08; R3:UC-J-08; R4:J-12; R5:J-10.
- **BD-23 Yield-source weighting rewrite** — R1:J-YIELD-TWAP; R2:UC-J-05; R3:UC-J-16/17; R4:J-06; R5:J-11.
- **BD-24 Zero live PPS becomes fatal** — R2:UC-J-05; R3:UC-J-16/17; R4:J-07; R5:J-11.
- **BD-25 Yield configuration-history handling** — R2:UC-J-05; R3:UC-J-16/17; R4:J-08.
- **BD-26 Zero-snapshot and activation handling** — R2:UC-J-05; R3:UC-J-16/17.
- **BD-27 Morpho V2 BlueChip eligibility** — R1:J-BLUECHIP-M2; R2:UC-J-12; R3:UC-J-17; R4:J-09; R5:J-12.
- **BD-28 Curve runtime residual guards** — R1:J-CURVE-LOOP; R2:UC-J-06; R3:UC-J-13; R4:J-10; R5:J-13.
- **BD-29 Curve admission and live-stipend qualification** — R1:J-CURVE-QUALIFY; R2:UC-J-06; R3:UC-J-04/14; R4:J-10; R5:J-13.
- **BD-30 Fifty-asset registration ceiling** — R1:J-SRC-CAP; R2:UC-J-11; R4:J-13; R5:UC-J-6.

### VERIFIED — ROUTE NOT PROVEN

- **BD-31 New UniswapV2 monitoring-only source** — R1:J-UNI-MONITOR; R2:UC-J-09; R3:UC-J-07; R4:J-15; R5:J-09.

## Catalog

- **BD-01** — R1:J-DESK-SCALE; R2:UC-J-01; R3:UC-J-02; R4:J-02; R5:J-01 — **CHANGED failure policy; SOURCE-REACHABLE.** Master conversions read token decimals live. rh requires cached `tokenScale`; missing scale returns zero or raises `"missing token scale"`. Valuation callers notice. Refs: M `PriceDesk.vy:84-124`; R `PriceDesk.vy:97-140,357-368`; consumer path M `Deleverage.vy:475-527`, R `:483-536`.

- **BD-02** — R1:J-DESK-SCALE; R2:UC-J-01; R3:UC-J-05; R5:J-01 — **NEW lifecycle/eligibility; SOURCE-REACHABLE.** Master has no cached-scale lifecycle. rh permits permissionless sync only for an existing feed with unset scale; governors/switchboards may overwrite, decimals must be ≤77, and new non-NFT assets auto-sync. Asset onboarders notice. Refs: M `SwitchboardBravo.vy:733-752`; R `PriceDesk.vy:341-354`, `SwitchboardBravo.vy:804-829`.

- **BD-03** — R1:J-DESK-ISOLATE; R2:UC-J-02; R3:UC-J-03; R4:J-01; R5:J-02/J-03 — **CHANGED failure policy; SOURCE-REACHABLE.** Master’s typed source call bubbles failure and can accept `(price,false)`. rh uses a 250k safe call; failure, wrong length, invalid bool, or positive price with false feed becomes status 2 and traversal continues. PriceDesk valuation callers notice. Refs: M `PriceDesk.vy:142-187`; R `:158-202,208-257`.

- **BD-04** — R1:J-DESK-ISOLATE; R2:UC-J-10; R3:UC-J-03; R4:J-03; R5:J-15 — **CHANGED failure policy; SOURCE-REACHABLE.** Master directly probes every source, so failure or bad ABI bubbles. rh applies a 75k safe probe and ignores failed or malformed responses. Direct integrators and onboarding checks notice. Refs: M `PriceDesk.vy:220-232`; R `:290-333`.

- **BD-05** — R1:J-DESK-ISOLATE; R2:UC-J-10; R3:UC-J-03; R4:J-03; R5:J-15 — **CHANGED failure policy; SOURCE-REACHABLE.** Master aborts snapshot fanout when one source reverts. rh uses 75k probes and 150k snapshot calls, skipping failures while preserving successful updates. Teller deposit/withdraw and snapshot callers notice. Refs: M `PriceDesk.vy:308-327`, `Teller.vy:313-388`; R `PriceDesk.vy:444-485`, `Teller.vy:340-416`.

- **BD-06** — R1:J-STALE-MIN; R2:UC-J-03; R3:UC-J-01; R4:J-04; R5:J-16 — **NEW integrator control; SOURCE-REACHABLE.** Master `getPrice` accepts only asset/raise and forwards MissionControl’s bound. rh adds caller `_staleTime`, using the tighter nonzero value against MissionControl. Direct integrators notice. Refs: M `PriceDesk.vy:132-153`; R `:148-176`.

- **BD-07** — R1:J-STALE-MIN; R2:UC-J-03; R3:UC-J-01; R4:J-04; R5:J-16 — **CHANGED failure policy; CONFIGURATION-CONTINGENT.** Master RedStone’s nested ETH/USD PriceDesk lookup drops the caller freshness bound. rh forwards it, so a RedStone price can fail on a nested ETH leg earlier. Configured RedStone users notice. Refs: M `RedStone.vy:29-30,172-178`; R `:29-30,172-178`.

- **BD-08** — R1:J-KEEPER-UPDATE; R3:UC-J-12; R4:J-14 — **CHANGED keeper API; SOURCE-REACHABLE.** Master Pyth update functions accept one `Bytes[2048]`; rh accepts up to twenty byte payloads. Authorized keepers must use new calldata and can batch. Refs: M `PythPrices.vy:550-578`; R `:563-591`.

- **BD-09** — R1:J-KEEPER-UPDATE; R3:UC-J-12; R4:J-14 — **CHANGED keeper API; SOURCE-REACHABLE.** Master Stork update functions accept one opaque `Bytes[2048]`; rh accepts up to twenty typed `TemporalNumericValueInput` values containing signed prices. Authorized keepers notice. Refs: M `StorkPrices.vy:486-514`; R `:46-53,522-550`.

- **BD-10** — R1:J-CURVE-BORROW; R2:UC-J-07; R3:UC-J-15; R5:J-14 — **CHANGED economics; SOURCE-REACHABLE.** Master balance-weights fresh GREEN ratios and falls back to the last ratio. rh duration-weights chronological minimum endpoints and returns zero for stale, malformed, incomplete, or overflowing history. Normal borrowers reach this through fixed Curve source ID 2. Refs: M `CurvePrices.vy:969-1003`, `CreditEngine.vy:1046-1069`; R `CurvePrices.vy:1175-1242`, `CreditEngine.vy:1027-1050`.

- **BD-11** — R1:J-CURVE-BORROW; R2:UC-J-07; R3:UC-J-15; R5:J-14 — **CHANGED economics/state; SOURCE-REACHABLE.** Master clears danger credit on any safe observation and adds all elapsed blocks for danger→danger. rh counts only non-stale danger→danger intervals; safe→safe accumulates recovery, mixed intervals preserve it, and a later danger pair resets recovery. Borrow rates notice. Refs: M `CurvePrices.vy:1018-1063`; R `:1257-1368`.

- **BD-12** — R1:J-STALE-MIN; R2:UC-J-03; R3:UC-J-10; R4:J-04; R5:J-04 — **CHANGED failure policy; CONFIGURATION-CONTINGENT.** Chainlink, Pyth, RedStone, and Stork change from the looser `max(caller,feed)` window to the tighter nonzero `min`. Configured quotes can become zero earlier. Refs: M `ChainlinkPrices.vy:182-197`, `PythPrices.vy:150-165`, `RedStone.vy:141-156`, `StorkPrices.vy:139-154`; corresponding R `:182-208,252-257`, `:150-165,255-260`, `:141-156,205-210`, `:148-163,208-213`.

- **BD-13** — R2:UC-J-03; R4:J-04 — **CHANGED eligibility; CONFIGURATION-CONTINGENT.** Governance-time Chainlink, Pyth, and RedStone validation changes from the looser maximum freshness bound to the tighter nonzero minimum. A feed master admitted can fail rh admission. Refs: M `ChainlinkPrices.vy:525-530`, `PythPrices.vy:438-450`, `RedStone.vy:463-478`; R `:540-545`, `:450-463`, `:475-491`.

- **BD-14** — R1:J-FUTURE-SOFT; R2:UC-J-04; R3:UC-J-09/11; R4:J-05; R5:J-06/J-07 — **CHANGED failure policy; CONFIGURATION-CONTINGENT.** Master accepts a future Pyth/Stork timestamp when effective freshness is zero; otherwise subtraction can underflow and revert. rh returns zero before subtraction. Stork compares truncated seconds, so a sub-second future value within the current second is not distinguished. Refs: M `PythPrices.vy:188-198`, `StorkPrices.vy:159-171`; R `:188-200`, `:168-183`.

- **BD-15** — R2:UC-J-04; R3:UC-J-09; R4:J-05; R5:J-06 — **CHANGED outcome; CONFIGURATION-CONTINGENT.** Master decodes Stork `quantizedValue` as `uint256` and rejects only zero. rh decodes `int192` and rejects nonpositive values. Interpreting an officially encoded negative int192 as a huge master value is an ABI-type inference from those declarations. Refs: M `StorkPrices.vy:33-35,159-171`; R `:42-44,168-183`.

- **BD-16** — R2:UC-J-04; R3:UC-J-09; R4:J-05 — **CHANGED eligibility; CONFIGURATION-CONTINGENT.** Master Stork admission checks nonzero asset and timestamp. rh additionally requires a positive value, a nonfuture publish second, and freshness under the tighter bound. Feed governors notice. Refs: M `StorkPrices.vy:381-386`; R `:403-422`.

- **BD-17** — R4:J-04; R5:J-05 — **CHANGED failure policy; CONFIGURATION-CONTINGENT.** Master Chainlink conversion legs reuse the main asset’s effective freshness. rh resolves the caller bound against the conversion feed’s own configured bound. Converted Chainlink assets notice. Refs: M `ChainlinkPrices.vy:202-223`; R `:200-225`.

- **BD-18** — R2:UC-J-02; R5:J-05 — **CHANGED failure policy; CONFIGURATION-CONTINGENT.** Master immediately calls an empty Chainlink conversion-feed address and can revert. rh returns zero before calling it. Misconfigured converted feeds notice. Refs: M `ChainlinkPrices.vy:261-284`; R `:273-289`.

- **BD-19** — R2:UC-J-02; R5:J-05 — **CHANGED helper outcome; CONFIGURATION-CONTINGENT.** Master’s direct RedStone data helper calls an empty configured feed; rh returns zero first. Normal `getPrice` already exits on an empty feed on both pins, so this is limited to direct helper behavior. Refs: M `RedStone.vy:208-217`; R `:218-229`.

- **BD-20** — R1:J-AERO-INERT; R2:UC-J-09; R3:UC-J-06; R4:J-11; R5:J-08 — **REMOVED pricing route; CONFIGURATION-CONTINGENT.** Master configures RIPE locally and returns a pool-derived price/feed result. rh exposes monitoring values but its PriceSource functions always return zero/false. Users notice only if governance routes their asset through Aero. Refs: M `AeroRipePrices.vy:93-155`; R `:69-113,187-202`.

- **BD-21** — R2:UC-J-09; R3:UC-J-06 — **REMOVED/CHANGED admin capability; CONFIGURATION-CONTINGENT.** Master exposes mutable pricing, snapshot, governance, registry, and timelock administration. rh removes much of that surface; retained compatibility actions return false/zero or raise `"monitoring only"`. Aero operators notice. Refs: M `AeroRipePrices.vy:8-11,65-73,238-465`; R `:187-303`.

- **BD-22** — R1:J-VVV-UNPRICED; R2:UC-J-08; R3:UC-J-08; R4:J-12; R5:J-10 — **REMOVED pseudo-feeds; CONFIGURATION-CONTINGENT.** Master this-source outputs are MCBETH raw `1` and VVV `2.4e18`; VVV can reset to raw `1`. rh prices only wrapped superOETHb. Users notice only if these assets route through this source; removal from every possible source is not proven. Refs: M `wsuperOETHbPrices.vy:49-102,171-177`; R `:47-82`.

- **BD-23** — R1:J-YIELD-TWAP; R2:UC-J-05; R3:UC-J-16/17; R4:J-06; R5:J-11 — **CHANGED economics/failure policy; CONFIGURATION-CONTINGENT.** Master supply-weights fresh samples and uses `lastSnapshot` even when stale. rh duration-weights chronological intervals plus a live tail and returns zero for stale, nonmonotonic, incomplete, or overflowing history. Configured BlueChip/Undy collateral notices. Refs: M `BlueChipYieldPrices.vy:736-763`, `UndyVaultPrices.vy:636-663`; R `:796-877`, `:676-757`.

- **BD-24** — R2:UC-J-05; R3:UC-J-16/17; R4:J-07; R5:J-11 — **CHANGED failure policy; CONFIGURATION-CONTINGENT.** Master keeps a historical wrapper quote when current `convertToAssets` returns zero. rh makes current-zero fatal to the source quote. Configured ERC-4626/Moonwell/Undy assets notice. Refs: M `BlueChipYieldPrices.vy:868-883,968-983`, `UndyVaultPrices.vy:753-768`; R `:1014-1046,1149-1176`, `:852-868`.

- **BD-25** — R2:UC-J-05; R3:UC-J-16/17; R4:J-08 — **CHANGED outcome; CONFIGURATION-CONTINGENT.** Master confirmation restores proposal-time snapshot state, discarding progress made while pending. rh same-capacity changes preserve current history; capacity changes clear and seed a new ring. BlueChip direct-underlying Aave/Compound changes clear without seeding. Governors and later price users notice. Refs: M `BlueChipYieldPrices.vy:510-519,538-557`, `UndyVaultPrices.vy:416-425,443-462`; R `:532-541,560-588`, `:422-431,449-474`.

- **BD-26** — R2:UC-J-05; R3:UC-J-16/17 — **CHANGED keeper/activation failure policy; CONFIGURATION-CONTINGENT.** Master periodic snapshots can store zero; snapshot-backed BlueChip feeds can activate before the seed attempt. rh refuses zero snapshots and requires a valid BlueChip reset seed. Undy already required live nonzero PPS on master; rh changes reset atomicity, not eligibility. Refs: M BlueChip `335-356,777-805`, Undy `251-272,334-361,680-704`; R BlueChip `345-369,762-781,891-925`, Undy `253-273,335-367,643-661,774-800`.

- **BD-27** — R1:J-BLUECHIP-M2; R2:UC-J-12; R3:UC-J-17; R4:J-09; R5:J-12 — **NEW eligibility; CONFIGURATION-CONTINGENT.** Master has no Morpho V2 route. rh adds an append-only protocol flag, validates through `isVaultV2`, derives `asset()`, and uses ERC-4626 pricing. Configured Morpho V2 vault users notice. Refs: M `BlueChipYieldPrices.vy:61-68,440-469`; R `:65-73,273-276,459-475,1080-1083`.

- **BD-28** — R1:J-CURVE-LOOP; R2:UC-J-06; R3:UC-J-13; R4:J-10; R5:J-13 — **CHANGED failure policy; CONFIGURATION-CONTINGENT.** Master attempts residual `numUnderlying>4` and self-referential LP configurations. rh reports feed-without-price for oversized configurations and zero when an underlying canonicalizes to the LP, including GREEN/sGREEN equivalence. Configured Curve users notice. Refs: M `CurvePrices.vy:277-294,327-349`; R `:286-305,338-385`.

- **BD-29** — R1:J-CURVE-QUALIFY; R2:UC-J-06; R3:UC-J-04/14; R4:J-10; R5:J-13 — **CHANGED eligibility; CONFIGURATION-CONTINGENT.** Master largely admits by membership/direct priceability and permits an empty eco-pool bypass. rh enforces structural exclusions, nonzero LP supply, and exact staged-source nonzero/status-1 execution through PriceDesk’s 250k production call. Governors notice. Refs: M `CurvePrices.vy:500-521,556-670`; R `:529-559,594-605,640-668,703-766`; `PriceDesk.vy:219-257`.

- **BD-30** — R1:J-SRC-CAP; R2:UC-J-11; R4:J-13; R5:UC-J-6 — **NEW failure; CONFIGURATION-CONTINGENT.** Master can store asset index 51 despite `getPricedAssets` being bounded to 50. rh rejects registration when the next index exceeds 50; the 50th succeeds and the 51st reverts. Source governors notice. Refs: M `PriceSourceData.vy:44-51`; R `:27,45-52`; representative confirmation M `ChainlinkPrices.vy:341-360`, R `:356-375`.

- **BD-31** — R1:J-UNI-MONITOR; R2:UC-J-09; R3:UC-J-07; R4:J-15; R5:J-09 — **NEW monitoring-only source; ROUTE NOT PROVEN.** The file is absent on master. rh exposes RIPE/WETH monitoring views, but every PriceSource read and feed mutation is inert, so no value-returning PriceDesk route exists. Operators can call monitoring views directly. Refs: M path absent; R `UniswapV2Prices.vy:69-120,165-286`.

## Ledger

| id | surface | class | master ref | rh ref | master ≤15w | rh ≤15w | reach | R-aliases | status |
|---|---|---|---|---|---|---|---|---|---|
| BD-01 | J | CHANGED failure policy | PriceDesk.vy:84-124 | PriceDesk.vy:97-140,357-368 | Reads token decimals live for each non-ETH conversion | Requires cached scale; zero or strict missing-scale revert | SOURCE-REACHABLE | R1:J-DESK-SCALE; R2:UC-J-01; R3:UC-J-02; R4:J-02; R5:J-01 | VERIFIED |
| BD-02 | J | NEW lifecycle | SwitchboardBravo.vy:733-752 | PriceDesk.vy:341-354; SwitchboardBravo.vy:804-829 | No cached-scale lifecycle or onboarding sync | New assets auto-sync; permitted actors can sync under stated gates | SOURCE-REACHABLE | R1:J-DESK-SCALE; R2:UC-J-01; R3:UC-J-05; R5:J-01 | VERIFIED |
| BD-03 | J | CHANGED failure policy | PriceDesk.vy:142-187 | PriceDesk.vy:158-202,208-257 | Typed uncapped call bubbles failure; price-without-feed can pass | 250k safe call rejects malformed pairs and continues | SOURCE-REACHABLE | R1:J-DESK-ISOLATE; R2:UC-J-02; R3:UC-J-03; R4:J-01; R5:J-02/J-03 | VERIFIED |
| BD-04 | J | CHANGED failure policy | PriceDesk.vy:220-232 | PriceDesk.vy:290-333 | One source failure reverts feed-existence probe | 75k safe probes ignore failure and malformed returns | SOURCE-REACHABLE | R1:J-DESK-ISOLATE; R2:UC-J-10; R3:UC-J-03; R4:J-03; R5:J-15 | VERIFIED |
| BD-05 | J | CHANGED failure policy | PriceDesk.vy:308-327 | PriceDesk.vy:444-485 | One snapshot call failure reverts entire fanout | 75k probes and 150k updates skip failures, preserve successes | SOURCE-REACHABLE | R1:J-DESK-ISOLATE; R2:UC-J-10; R3:UC-J-03; R4:J-03; R5:J-15 | VERIFIED |
| BD-06 | J | NEW integrator control | PriceDesk.vy:132-153 | PriceDesk.vy:148-176 | Only MissionControl bound reaches sources | Caller bound tightens MissionControl bound through public getPrice | SOURCE-REACHABLE | R1:J-STALE-MIN; R2:UC-J-03; R3:UC-J-01; R4:J-04; R5:J-16 | VERIFIED |
| BD-07 | J | CHANGED failure policy | RedStone.vy:29-30,172-178 | RedStone.vy:29-30,172-178 | Nested RedStone ETH lookup omits caller stale bound | Nested ETH lookup receives caller stale bound | CONFIGURATION-CONTINGENT | R1:J-STALE-MIN; R2:UC-J-03; R3:UC-J-01; R4:J-04; R5:J-16 | VERIFIED |
| BD-08 | J | CHANGED keeper API | PythPrices.vy:550-578 | PythPrices.vy:563-591 | Keeper submits one opaque Pyth payload | Keeper submits up to twenty opaque payloads | SOURCE-REACHABLE | R1:J-KEEPER-UPDATE; R3:UC-J-12; R4:J-14 | VERIFIED |
| BD-09 | J | CHANGED keeper API | StorkPrices.vy:486-514 | StorkPrices.vy:46-53,522-550 | Keeper submits one opaque Stork payload | Keeper submits up to twenty typed signed-value inputs | SOURCE-REACHABLE | R1:J-KEEPER-UPDATE; R3:UC-J-12; R4:J-14 | VERIFIED |
| BD-10 | J | CHANGED economics | CurvePrices.vy:969-1003 | CurvePrices.vy:1175-1242 | Balance-weights fresh ratios; stale fallback uses last ratio | Duration-weights minimum endpoints; invalid or stale history yields zero | SOURCE-REACHABLE | R1:J-CURVE-BORROW; R2:UC-J-07; R3:UC-J-15; R5:J-14 | VERIFIED |
| BD-11 | J | CHANGED economics/state | CurvePrices.vy:1018-1063 | CurvePrices.vy:1257-1368 | Any safe observation clears danger; danger pairs add elapsed blocks | Only danger pairs add; safe pairs recover; mixed pairs preserve | SOURCE-REACHABLE | R1:J-CURVE-BORROW; R2:UC-J-07; R3:UC-J-15; R5:J-14 | VERIFIED |
| BD-12 | J | CHANGED failure policy | CL:182-197; Pyth:150-165; RS:141-156; Stork:139-154 | CL:182-208,252-257; Pyth:150-165,255-260; RS:141-156,205-210; Stork:148-163,208-213 | Uses looser maximum of caller and feed freshness bounds | Uses tighter nonzero minimum of caller and feed bounds | CONFIGURATION-CONTINGENT | R1:J-STALE-MIN; R2:UC-J-03; R3:UC-J-10; R4:J-04; R5:J-04 | VERIFIED |
| BD-13 | J | CHANGED eligibility | CL:525-530; Pyth:438-450; RS:463-478 | CL:540-545; Pyth:450-463; RS:475-491 | Admission uses looser maximum freshness bound | Admission uses tighter nonzero minimum freshness bound | CONFIGURATION-CONTINGENT | R2:UC-J-03; R4:J-04 | VERIFIED |
| BD-14 | J | CHANGED failure policy | PythPrices.vy:188-198; StorkPrices.vy:159-171 | PythPrices.vy:188-200; StorkPrices.vy:168-183 | Future accepted at zero bound; nonzero subtraction can revert | Future timestamp returns zero before freshness subtraction | CONFIGURATION-CONTINGENT | R1:J-FUTURE-SOFT; R2:UC-J-04; R3:UC-J-09/11; R4:J-05; R5:J-06/J-07 | VERIFIED |
| BD-15 | J | CHANGED outcome | StorkPrices.vy:33-35,159-171 | StorkPrices.vy:42-44,168-183 | Decodes Stork value unsigned and rejects only zero | Decodes signed value and rejects nonpositive values | CONFIGURATION-CONTINGENT | R2:UC-J-04; R3:UC-J-09; R4:J-05; R5:J-06 | VERIFIED |
| BD-16 | J | CHANGED eligibility | StorkPrices.vy:381-386 | StorkPrices.vy:403-422 | Admission checks nonzero asset and timestamp only | Admission also requires positive, nonfuture, fresh observation | CONFIGURATION-CONTINGENT | R2:UC-J-04; R3:UC-J-09; R4:J-05 | VERIFIED |
| BD-17 | J | CHANGED failure policy | ChainlinkPrices.vy:202-223 | ChainlinkPrices.vy:200-225 | Conversion feed reuses main asset effective stale bound | Conversion feed resolves caller against its own configured bound | CONFIGURATION-CONTINGENT | R4:J-04; R5:J-05 | VERIFIED |
| BD-18 | J | CHANGED failure policy | ChainlinkPrices.vy:261-284 | ChainlinkPrices.vy:273-289 | Empty conversion-feed address is called and can revert | Empty conversion-feed address returns zero | CONFIGURATION-CONTINGENT | R2:UC-J-02; R5:J-05 | VERIFIED |
| BD-19 | J | CHANGED helper outcome | RedStone.vy:208-217 | RedStone.vy:218-229 | Direct helper calls an empty RedStone feed | Direct helper returns zero for empty feed | CONFIGURATION-CONTINGENT | R2:UC-J-02; R5:J-05 | VERIFIED |
| BD-20 | J | REMOVED pricing route | AeroRipePrices.vy:93-155 | AeroRipePrices.vy:69-113,187-202 | Aero returns a configured RIPE price and feed flag | Aero PriceSource surface is always zero and false | CONFIGURATION-CONTINGENT | R1:J-AERO-INERT; R2:UC-J-09; R3:UC-J-06; R4:J-11; R5:J-08 | VERIFIED |
| BD-21 | J | REMOVED/CHANGED admin | AeroRipePrices.vy:8-11,65-73,238-465 | AeroRipePrices.vy:187-303 | Aero exposes mutable pricing, governance, registry, and timelock administration | Most admin names disappear; retained compatibility actions are inert | CONFIGURATION-CONTINGENT | R2:UC-J-09; R3:UC-J-06 | VERIFIED |
| BD-22 | J | REMOVED pseudo-feeds | wsuperOETHbPrices.vy:49-102,171-177 | wsuperOETHbPrices.vy:47-82 | This source exposes MCBETH raw 1 and VVV 2.4e18 | This source prices only wrapped superOETHb | CONFIGURATION-CONTINGENT | R1:J-VVV-UNPRICED; R2:UC-J-08; R3:UC-J-08; R4:J-12; R5:J-10 | VERIFIED |
| BD-23 | J | CHANGED economics/failure | BlueChip:736-763; Undy:636-663 | BlueChip:796-877; Undy:676-757 | Supply-weights fresh samples; stale set falls back to last sample | Duration-weights chronological intervals; stale or invalid history returns zero | CONFIGURATION-CONTINGENT | R1:J-YIELD-TWAP; R2:UC-J-05; R3:UC-J-16/17; R4:J-06; R5:J-11 | VERIFIED |
| BD-24 | J | CHANGED failure policy | BlueChip:868-883,968-983; Undy:753-768 | BlueChip:1014-1046,1149-1176; Undy:852-868 | Zero live PPS falls back to historical price | Zero live PPS makes source quote zero | CONFIGURATION-CONTINGENT | R2:UC-J-05; R3:UC-J-16/17; R4:J-07; R5:J-11 | VERIFIED |
| BD-25 | J | CHANGED outcome | BlueChip:510-519,538-557; Undy:416-425,443-462 | BlueChip:532-541,560-588; Undy:422-431,449-474 | Confirmation restores proposal-time snapshot cursor before appending | Same capacity preserves current history; changed capacity resets ring | CONFIGURATION-CONTINGENT | R2:UC-J-05; R3:UC-J-16/17; R4:J-08 | VERIFIED |
| BD-26 | J | CHANGED keeper/activation failure | BlueChip:335-356,777-805; Undy:251-272,334-361,680-704 | BlueChip:345-369,762-781,891-925; Undy:253-273,335-367,643-661,774-800 | Periodic snapshots may store zero; BlueChip activates before seeding | Zero snapshots fail; snapshot-backed BlueChip activation requires nonzero seed | CONFIGURATION-CONTINGENT | R2:UC-J-05; R3:UC-J-16/17 | VERIFIED |
| BD-27 | J | NEW eligibility | BlueChipYieldPrices.vy:61-68,440-469 | BlueChipYieldPrices.vy:65-73,273-276,459-475,1080-1083 | No Morpho V2 protocol route | Validated Morpho V2 vaults use ERC-4626 pricing | CONFIGURATION-CONTINGENT | R1:J-BLUECHIP-M2; R2:UC-J-12; R3:UC-J-17; R4:J-09; R5:J-12 | VERIFIED |
| BD-28 | J | CHANGED failure policy | CurvePrices.vy:277-294,327-349 | CurvePrices.vy:286-305,338-385 | Residual oversized or recursive Curve configs proceed to pricing | Oversized returns feed-without-price; canonical self-reference returns zero | CONFIGURATION-CONTINGENT | R1:J-CURVE-LOOP; R2:UC-J-06; R3:UC-J-13; R4:J-10; R5:J-13 | VERIFIED |
| BD-29 | J | CHANGED eligibility | CurvePrices.vy:500-521,556-670 | CurvePrices.vy:529-559,594-605,640-668,703-766 | Membership and direct priceability can admit empty eco pools | Activation enforces structure, liquidity, and exact-source stipend qualification | CONFIGURATION-CONTINGENT | R1:J-CURVE-QUALIFY; R2:UC-J-06; R3:UC-J-04/14; R4:J-10; R5:J-13 | VERIFIED |
| BD-30 | J | NEW failure | PriceSourceData.vy:44-51 | PriceSourceData.vy:27,45-52 | A 51st asset can be stored despite bounded listing | A 51st asset registration reverts | CONFIGURATION-CONTINGENT | R1:J-SRC-CAP; R2:UC-J-11; R4:J-13; R5:UC-J-6 | VERIFIED |
| BD-31 | J | NEW monitoring-only source | A: UniswapV2Prices.vy absent | UniswapV2Prices.vy:69-120,165-286 | Source file absent | Monitoring views exist; every PriceSource and mutation path is inert | ROUTE NOT PROVEN | R1:J-UNI-MONITOR; R2:UC-J-09; R3:UC-J-07; R4:J-15; R5:J-09 | VERIFIED |
| UC-01 | J | SAME OUTCOME | PriceDesk.vy:150-172 | PriceDesk.vy:173-195 | Traverses priority IDs, then remaining registry IDs | Traverses priority IDs, then remaining registry IDs | SOURCE-REACHABLE | R5:UC-J-1 | VERIFIED |
| UC-02 | J | SAME OUTCOME | PriceDesk.vy:178,183-187 | PriceDesk.vy:198-200,210-216 | Empty slot or valid absent feed returns no-feed | Empty slot or valid absent feed returns no-feed | SOURCE-REACHABLE | R4:UC-J-01; R5:UC-J-2 | VERIFIED |
| UC-03 | J | SAME OUTCOME | PriceDesk.vy:198-214 | PriceDesk.vy:268-284 | ETH helpers use the same price and rounding formulas | ETH helpers use the same price and rounding formulas | SOURCE-REACHABLE | R1:UC-J-6; R5:UC-J-3 | VERIFIED |
| UC-04 | J | SAME OUTCOME | PriceDesk.vy:243-300 | PriceDesk.vy:379-436 | Registry add, update, disable, and cancel lifecycle remains | Registry add, update, disable, and cancel lifecycle remains | CONFIGURATION-CONTINGENT | R1:UC-J-1 | VERIFIED |
| UC-05 | J | SAME OUTCOME | CurvePrices.vy:277-294,357-466,1130-1132 | CurvePrices.vy:286-305,393-494,1441-1443 | Stable, crypto, single-token math and sGREEN conversion remain | Stable, crypto, single-token math and sGREEN conversion remain | CONFIGURATION-CONTINGENT | R1:UC-J-2; R5:UC-J-4 | VERIFIED |
| UC-06 | J | SAME OUTCOME | wsuperOETHbPrices.vy:107-117 | wsuperOETHbPrices.vy:87-97 | Wrapped price equals SUPER_OETH price times wrapper PPS | Wrapped price equals SUPER_OETH price times wrapper PPS | CONFIGURATION-CONTINGENT | R1:UC-J-3; R4:UC-J-02 | VERIFIED |
| UC-07 | J | SAME OUTCOME | PriceSourceData.vy:82-123 | PriceSourceData.vy:83-124 | Listing, pause, and recovery behavior remains | Listing, pause, and recovery behavior remains | CONFIGURATION-CONTINGENT | R1:UC-J-4 | VERIFIED |
| UC-08 | J | SAME OUTCOME | BlueChipYieldPrices.vy:256-258 | BlueChipYieldPrices.vy:266-268 | Aave and Compound return underlying-token price directly | Aave and Compound return underlying-token price directly | CONFIGURATION-CONTINGENT | R1:UC-J-5 | VERIFIED |
| UC-09 | J | SAME OUTCOME | BlueChip:241-254; Undy:177-192 | BlueChip:251-264; Undy:179-194 | Yield sources ignore PriceDesk caller stale parameter | Yield sources ignore PriceDesk caller stale parameter | CONFIGURATION-CONTINGENT | R4:UC-J-03 | VERIFIED |
| UC-10 | J | SAME OUTCOME | Pyth:550-578; Stork:486-514 | Pyth:563-591; Stork:522-550 | Fee payment and refund mechanics surround single payloads | Fee payment and refund mechanics surround batched payloads | SOURCE-REACHABLE | R2:unnumbered unchanged | VERIFIED |
| UC-11 | J | SAME OUTCOME | Chainlink:261-293; RedStone:216-248 | Chainlink:273-305; RedStone:226-259 | Nonempty oracle tuple decoding remains apart from cited guards | Nonempty oracle tuple decoding remains apart from cited guards | CONFIGURATION-CONTINGENT | R2:unnumbered unchanged | VERIFIED |

## Files

`CONFIRMED` here means at least one VERIFIED Ledger row cites the path, not that every line was walked.

| FOCUS path | final | ids | note |
|---|---|---|---|
| `contracts/registries/PriceDesk.vy` | CONFIRMED | BD-01–06; UC-01–04 | Valuation, traversal, isolation, snapshots, stale bound, scale lifecycle |
| `contracts/priceSources/AeroRipePrices.vy` | CONFIRMED | BD-20–21 | Pricing removed; monitoring/admin replacement |
| `contracts/priceSources/BlueChipYieldPrices.vy` | CONFIRMED | BD-23–27; UC-08–09 | Weighting, PPS failure, history, Morpho V2 |
| `contracts/priceSources/ChainlinkPrices.vy` | CONFIRMED | BD-12–13, BD-17–18; UC-11 | Freshness and conversion-leg behavior |
| `contracts/priceSources/CurvePrices.vy` | CONFIRMED | BD-10–11, BD-28–29; UC-05 | GREEN status, residual guards, admission |
| `contracts/priceSources/PythPrices.vy` | CONFIRMED | BD-08, BD-12–14; UC-10 | Batch ABI, freshness, future timestamps |
| `contracts/priceSources/RedStone.vy` | CONFIRMED | BD-07, BD-12–13, BD-19; UC-11 | Nested bound and helper behavior |
| `contracts/priceSources/StorkPrices.vy` | CONFIRMED | BD-09, BD-12, BD-14–16; UC-10 | Typed batch, signed values, admission |
| `contracts/priceSources/UndyVaultPrices.vy` | CONFIRMED | BD-23–26; UC-09 | Weighting, PPS failure, history |
| `contracts/priceSources/UniswapV2Prices.vy` | CONFIRMED | BD-31 | A on rh; monitoring-only |
| `contracts/priceSources/wsuperOETHbPrices.vy` | CONFIRMED | BD-22; UC-06 | Pseudo-feed removal; wrapper formula unchanged |
| `contracts/priceSources/modules/PriceSourceData.vy` | CONFIRMED | BD-30; UC-07 | Registration cap; other module behavior unchanged |

## API

The inventory was rebuilt from `@external`, `exports:`/`.__interface__`, and `public(...)` declarations. Events, constructors, internal functions, enums, and dependency-interface-only declarations are outside the requested API definition.

### PriceDesk

Added:

- `tokenScale(address) -> uint256`
- `syncTokenScale(address)`
- `qualifyCallerPriceSource(address,uint256=0) -> (uint256,uint256)`

Signature changed:

- master: `getPrice(address,bool=False) -> uint256`
- rh: `getPrice(address,bool=False,uint256=0) -> uint256`

The default-argument forms retain the shorter call variants. Exported `gov`, `registry`, `addys`, and `deptBasics` declarations are unchanged.

### AeroRipePrices

Added:

- `RIPE_HQ() -> address`
- `WETH_TOKEN() -> address`
- `RIPE_IS_TOKEN0() -> bool`
- `isMonitoringOnly() -> bool`
- `getRipePoolState() -> (uint256,uint256,uint256)`
- `getRipeWethMonitoringPrice() -> uint256`
- `getRipeUsdMonitoringPrice() -> uint256`

Removed host names:

- `priceConfigs`, `snapShots`, `pendingPriceConfigs`
- `updatePriceConfig`, `isValidPriceConfig`
- `getWeightedPrice`, `getLatestSnapshot`

Removed LocalGov export-derived names:

- `governance`, `pendingGov`, `numGovChanges`, `govChangeTimeLock`
- `getRipeHqFromGov`, `canGovern`, `getGovernors`, `hasPendingGovChange`
- `startGovernanceChange`, `confirmGovernanceChange`, `cancelGovernanceChange`
- `relinquishGov`, `setGovTimeLock`, `isValidGovTimeLock`
- `minGovChangeTimeLock`, `maxGovChangeTimeLock`, `finishRipeHqSetup`

Removed Addys/PriceSourceData export-derived names:

- `getAddys`, `getRipeHq`
- `assets`, `indexOfAsset`, `numAssets`

Removed TimeLock export-derived names:

- `pendingActions`, `actionId`, `expiration`
- `canConfirmAction`, `isExpired`
- `isValidActionTimeLock`, `minActionTimeLock`, `maxActionTimeLock`
- `setExpiration`

Retained but reimplemented as inert/monitoring-only:

- `getPricedAssets`
- `actionTimeLock`, `hasPendingAction`, `getActionConfirmationBlock`
- `setActionTimeLock`, `setActionTimeLockAfterSetup`
- `isPaused`, `pause`, `recoverFunds`, `recoverFundsMany`
- PriceSource/feed action names
- `getAeroRipePrice`

`getPrice` and `getPriceAndHasFeed` only rename their third source parameter from `_priceDesk` to `_oracleRegistry`; types, defaults, and return declarations are unchanged.

### BlueChipYieldPrices

Added:

- `MORPHO_V2_ADDR() -> address`

All direct external declarations and the four exported interfaces are otherwise unchanged.

### CurvePrices

Signature shape changed:

- master `getGreenStabilizerConfig()` returns seven components: `pool`, `lpToken`, `greenBalance`, `greenRatio`, `greenIndex`, `stabilizerAdjustWeight`, `stabilizerMaxPoolDebt`
- rh appends eighth component `altBalance`

`getCurvePoolData()` remains externally two-component on both pins. Only its internal helper changes to three components.

### PythPrices

Signatures changed:

- `updatePythPrice(Bytes[2048])` → `updatePythPrice(DynArray[Bytes[2048],20])`
- `updatePythPriceNoPay(Bytes[2048])` → `updatePythPriceNoPay(DynArray[Bytes[2048],20])`

### StorkPrices

Signatures changed:

- `updateStorkPrice(Bytes[2048])` → `updateStorkPrice(DynArray[TemporalNumericValueInput,20])`
- `updateStorkPriceNoPay(Bytes[2048])` → `updateStorkPriceNoPay(DynArray[TemporalNumericValueInput,20])`

### UniswapV2Prices

Entire API is added on rh.

Public getters:

- `RIPE_HQ`, `RIPE_WETH_POOL`, `RIPE_TOKEN`, `WETH_TOKEN`, `RIPE_IS_TOKEN0`

Monitoring externals:

- `isMonitoringOnly`
- `getRipePoolState`
- `getRipeWethMonitoringPrice`
- `getRipeUsdMonitoringPrice`

Inert PriceSource/admin externals:

- `getPrice`, `getPriceAndHasFeed`, `hasPriceFeed`, `hasPendingPriceFeedUpdate`
- `getPricedAssets`, `addPriceSnapshot`
- `confirmNewPriceFeed`, `cancelNewPendingPriceFeed`
- `confirmPriceFeedUpdate`, `cancelPriceFeedUpdate`
- `disablePriceFeed`, `confirmDisablePriceFeed`, `cancelDisablePriceFeed`
- `actionTimeLock`, `hasPendingAction`, `getActionConfirmationBlock`
- `setActionTimeLock`, `setActionTimeLockAfterSetup`
- `isPaused`, `pause`, `recoverFunds`, `recoverFundsMany`

It does not add Aero’s `getAeroRipePrice`.

### wsuperOETHbPrices

Removed:

- `vvvPrice() -> uint256`
- `resetVvvPrice()`

The public `MCBETH` and `VVV` address getters remain; removal concerns their pricing branches, not those getters.

### No requested API delta

- `ChainlinkPrices.vy`
- `RedStone.vy`
- `UndyVaultPrices.vy`
- `PriceSourceData.vy`

## Dropped / Open / referrals / SYNTH-CHECK

### Dropped — settled disagreements

- R1’s malformed-response wording was backwards. rh rejects positive price with false feed; `(0,true)` is a valid feed-without-price result.
- R2’s claim that failed **or empty** sources force strict raising was too broad. Empty registry slots and `(0,false)` remain status 0.
- “Scale is set once” was dropped: permissionless callers are one-shot, but governors and switchboards can overwrite.
- Blanket future-time claims were dropped. Master accepts future data when effective freshness is zero; otherwise subtraction may revert.
- R1/R3 source-reachable classifications for Aero, BlueChip/Undy, and Curve residual/admission behavior were dropped because runtime source identity/configuration is not statically bound.
- R1’s “still registered,” R2’s “no J consumer,” and R5’s “only Curve/no feed” RIPE claims were dropped as deployment-state assertions.
- MCBETH is raw price `1`, not `$1`. Neither MCBETH nor VVV was proven unpriced across every possible source.
- R3’s Stork update type was corrected: it is a typed input array, not a byte-payload array.
- R2/R3’s “every yield confirmation newly requires a live snapshot” was overbroad. Undy already required nonzero live PPS; same-capacity rh updates preserve history; direct-underlying BlueChip feeds clear without seeding.
- “Consecutive safety” was dropped as an exact rh danger rule: mixed intervals do not erase accumulated recovery.
- The RedStone empty-feed change applies to its direct helper; normal `getPrice` already exits empty on both pins.
- R3/R5’s “PriceSourceData same outcome” treatment was dropped because the 51st registration outcome changes.
- Events, constructors, internal helpers, enum values, and Curve dependency-interface declarations were dropped from API.
- `getCurvePoolData()` is not an external signature change; only the internal helper’s return expands.

### Open

- Exact PriceDesk ID→address mappings, per-asset source order, live feed configuration, and whether RIPE routes elsewhere are deployment/governance state.
- rh auto-syncs token scale on new non-NFT asset onboarding. No source path was found that automatically syncs assets already supported at migration.
- Whether nested sources remain below the new 250k runtime stipend as registry/configuration complexity changes requires execution evidence, which this source-only lane did not produce.

### Referrals

- **Borrow/health/liquidation:** rh’s quarantine treatment of positive balances with unusable prices changes downstream borrowing, liquidation, redemption, and health behavior; close in that behavior lane.
- **Governance/defaults:** priority source-ID lists and deployed mappings belong to Lane 3D.
- **Endaoment:** the added Curve `altBalance` output is consumed by changed Endaoment stabilizer paths.
- **Rewards:** RIPE valuation changes can flow into Lootbox USD-valued points.
- **Operations/governance:** existing-asset token-scale population remains an external migration/configuration question.

### SYNTH-CHECK

These were observed while opening cited source but were not promoted into Brief/Ledger because no R1–R5 item claimed them:

- **PriceDesk snapshot return value:** master sets aggregate `didUpdate=True` whenever a feed call returns, ignoring the source’s returned bool; rh sets it only for an exact returned word `1`. M `PriceDesk.vy:317-325`; R `:453-465,470-485`.
- **Exported LocalGov guard:** rh prevents `startGovernanceChange` while RIPE-HQ setup is unfinished and `numGovChanges==0`. M `LocalGov.vy:181-191`; R `:180-191`.
- **Exported TimeLock behavior:** rh adds confirmation/expiration overflow checks, requires action lock ≤ expiration, and caps expiration at `MAX_ACTION_TIMELOCK`. M `TimeLock.vy:65-74,204-207,249-254`; R `:65-75,205-208,250-255`.
- **Curve GREEN configuration confirmation:** rh revalidates pending parameters/current observation, validates `staleBlocks`, indices, decimals and current data, then requires a valid seed; master commits and ignores the seed call’s return. M `CurvePrices.vy:844-895`; R `:940-1018,1066-1116`.
- No unreported added API name was found in the twelve FOCUS files.

LANE SYNTHESIS COMPLETE — Lane 3B — 91eda49c vs 251ac9e2

<oai-mem-citation>
<citation_entries>
MEMORY.md:1609-1617|note=[prior PR67 contracts scope context]
</citation_entries>
<rollout_ids>
019fde5a-1ff3-7760-885a-d74acd76e57a
</rollout_ids>
</oai-mem-citation>
