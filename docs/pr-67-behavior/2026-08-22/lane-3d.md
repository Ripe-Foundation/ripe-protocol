# PR #67 lane synthesis — Lane 3D

Draft only. Not a source of truth. If this file and the contracts disagree,
the contracts win.

- master: 91eda49ccd34a25090582aff0695075c4c806011
- rh:     251ac9e228a8af80326e8fe30f607511c78fe820
- date:   2026-08-22

# PR #67 behavior delta — Lane 3D — 91eda49c vs 251ac9e2

Local objects match the pinned commits and trees. All Ledger evidence was opened from both trees; no repository state was changed.

Abbreviations: `Alpha`–`Echo` = `SwitchboardAlpha.vy`–`SwitchboardEcho.vy`; `MC` = `MissionControl.vy`; `HR` = `HumanResources.vy`; `D(path/name)` = absent at that pin.

## Brief

### VERIFIED SOURCE-REACHABLE

- `BD-01` — Initial RipeHq governance must finish setup before starting a governance change. (`R1:L-GOV-HQSETUP; R2:UC-L-025; R3:L-22; R4:L-005; R5:L-01`)
- `BD-02` — TimeLock configuration now enforces `actionTimeLock ≤ expiration ≤ MAX_ACTION_TIMELOCK`. (`R1:L-TL-BOUNDS; R2:UC-L-026; R3:L-23; R4:L-006; R5:L-02`)
- `BD-04` — Echo gains timelocked global and per-user RipeGov-point disable actions. (`R1:L-ECHO-DISABLE; R2:UC-L-020; R3:L-02; R4:L-025; R5:L-04`)
- `BD-05` — Echo’s Endaoment-liquidity action requires and stores `_expectedLpToken`. (`R1:API/ref; R2:UC-L-021; R3:L-03; R4:API/ref; R5:L-05`)
- `BD-06` — Charlie gains a validated, timelocked core-RipeGov-vault setter. (`R1:L-MC-VAULT-PTRS; R2:UC-L-013/028; R3:L-04; R4:L-015; R5:L-06`)
- `BD-07` — Charlie gains a separately validated preferred-Stability-vault setter. (`R1:L-MC-VAULT-PTRS; R2:UC-L-014/028; R3:L-04; R4:L-015; R5:L-06`)
- `BD-08` — MC initializes core/preferred IDs to `2/1` and maintains monotonic vault-classification maps. (`R1:L-MC-VAULT-PTRS; R2:UC-L-028; R3:L-05; R4:L-015; R5:L-07`)
- `BD-09` — MC asset deregistration now rejects live voter or staker allocations. (`R1:L-MC-DEREG; R2:UC-L-027; R3:L-06; R4:L-016; R5:L-08`)
- `BD-10` — Charlie now asserts successful asset and vault-asset deregistration returns. (`R1:Brief; R2:UC-L-015; R3:L-06; R4:L-016; R5:L-08`)
- `BD-11` — Global minimum debt must not exceed the selected MC’s borrow-interval maximum. (`R1:L-ALPHA-DEBT-X; R2:UC-L-007; R3:L-10; R4:L-007; R5:L-11`)
- `BD-12` — Borrow-interval changes use the selected MC and are rechecked at execution. (`R2:UC-L-007; R3:L-10; R4:L-007; R5:L-11`)
- `BD-13` — Auction discount, delay, and duration bounds tighten. (`R1:L-ALPHA-AUCTION; R2:UC-L-006; R3:L-11; R4:L-008; R5:L-12`)
- `BD-14` — RipeGov configuration follows the selected MC core vault and rejects zero/unsafe lock maxima. (`R1:L-ALPHA-RIPEGOV; R2:UC-L-005; R3:L-12; R4:L-011; R5:L-13`)
- `BD-15` — Priority-liquidation vaults cannot be Stability or RipeGov vaults and are revalidated. (`R1:L-ALPHA-PRIVault; R2:UC-L-008; R3:L-08; R4:L-009; R5:L-09`)
- `BD-16` — Priority-Stability vaults must pass live StabilityPool checks at proposal and execution. (same aliases as `BD-15`)
- `BD-17` — Priority price-source sanitation moves from proposal to execution. (`R1:L-ALPHA-PRISRC; R2:UC-L-009; R3:L-09; R4:L-010; R5:L-10`)
- `BD-18` — Staker allocations follow core-RipeGov/Stability classification instead of literal IDs `2/1`. (`R1:L-BRAVO-STAKER; R3:Brief; R4:L-012; R5:L-15`)
- `BD-19` — Bravo adds instant-auction and special-Stability-pool constraints. (`R1:L-BRAVO-LIQ; R2:UC-L-010; R3:L-28; R4:L-012; R5:L-15`)
- `BD-20` — Debt-term rails expand beyond LTV and are rechecked against live terms. (`R1:L-BRAVO-STEP; R2:UC-L-011; R3:L-28; R4:L-013; R5:L-14`)
- `BD-21` — Pending asset additions reassert that the asset remains unsupported at execution. (`R3:L-28; R4:L-014; R5:L-15`)
- `BD-22` — Non-NFT asset addition initializes a missing PriceDesk token scale. (`R2:UC-L-012; R3:L-28; R4:L-014; R5:L-15`)
- `BD-23` — Underscore-registry validation gains contract and registry-topology probes. (`R1:L-DELTA-UNDY; R2:UC-L-017; R3:L-15; R4:L-022; R5:L-17`)
- `BD-24` — HR cliff/vesting configuration rejects infeasible combinations at execution. (`R2:UC-L-018; R3:L-14; R4:L-021; R5:L-18`)
- `BD-25` — Delta’s single-user `deleverageUser` route is removed. (`R1:API/ref; R2:UC-L-016; R3:L-13; R4:ref; R5:L-16`)
- `BD-26` — Contributor terms gain live lock, arithmetic, and timestamp bounds plus confirmation revalidation. (`R1:L-HR-TERMS-LOCK; R2:UC-L-022; R3:L-16; R4:L-017; R5:L-19`)
- `BD-27` — HR cash-checks use MC’s live core-RipeGov vault rather than literal vault `2`. (`R1:L-HR-VAULT-ROUTE; R2:UC-L-023; R3:L-20; R4:ref; R5:L-20`)
- `BD-28` — HR balance, transfer, and refund paths resolve explicit ID → legacy ID → core ID. (`R1:L-HR-VAULT-ROUTE; R2:UC-L-023; R3:L-17/L-18; R4:ref; R5:L-20`)
- `BD-29` — Switchboard or contributor owner/manager can set or clear a validated legacy vault. (`R1:L-HR-LEGACY; R2:UC-L-024; R3:L-19; R4:L-024; R5:L-21`)
- `BD-30` — Contributor transfer refreshes sender points and conditionally clears the legacy mapping. (`R1:L-HR-VAULT-ROUTE; R2:UC-L-023; R3:L-17; R4:ref; R5:L-22`)
- `BD-31` — Refund gains saturating credit, routed burn, point refresh, asserted burn, and housekeeping. (`R2:UC-L-023; R3:L-18; R4:ref; R5:L-22`)
- `BD-36` — Contributor-cancellation events preserve the actual confirmation block. (`R4:L-018`)
- `BD-37` — HR aggregate views saturate instead of reverting on addition overflow. (`R4:L-019`)

### VERIFIED CONFIGURATION-CONTINGENT

- `BD-03` — Echo gains five immediate migration routes, contingent on HQ ID `25` resolving. (`R1:L-ECHO-MIGRATE; R2:UC-L-019; R3:L-01; R4:API/ref; R5:L-03`)
- `BD-32` — The configured Contributor blueprint gains selected-vault transfer plumbing. (`R1:L-CONTRIB-XFER; R2:API; R3:L-21; R4:API/ref; R5:L-23`)
- `BD-33` — That blueprint rejects self-ownership and ownership changes overlapping pending RIPE transfers. (`R1:L-CONTRIB-OWNER; R2:UC-L-029; R3:L-21; R4:L-023; R5:L-23`)
- `BD-34` — Successful ownership changes increment public `numOwnerChanges`. (`R1:API; R2:UC-L-029/API; R3:L-21; R4:L-023/API; R5:L-23/API`)
- `BD-35` — Vested-amount arithmetic preserves the floor result while avoiding some multiplication overflows. (`R2:file; R3:L-21; R4:L-020; R5:L-23`)
- `BD-38` — DefaultsBase drops priority price-source ID `9`. (`R1:L-DEF-BASE-PX; R2:UC-L-001; R3:L-27; R4:L-001; R5:L-24`)
- `BD-39` — `DefaultsBaseLive` becomes a selectable MC/Ledger Defaults profile. (`R1:L-DEF-BASELIVE; R2:UC-L-002; R3:L-24; R4:L-002; R5:L-25`)
- `BD-40` — `DefaultsRobinhood` becomes a selectable launch profile. (`R1:L-DEF-RH; R2:UC-L-003; R3:L-25; R4:L-003; R5:L-26`)
- `BD-41` — `DefaultsRobinhoodLive` becomes a distinct selectable live-replacement profile. (`R1:L-DEF-RHLIVE; R2:UC-L-004; R3:L-26; R4:L-004; R5:L-27`)
- `BD-42` — Addys assigns internal IDs `23/24/25` to two CCIP pools and VaultMigrator. (`R1:L-HQ-IDS; R2:file; R3:narrative; R4:ref; R5:L-03 support`)

Contributor rows are contingent because HR deploys the address supplied in `hrConfig.contribTemplate`; the pinned source does not prove that address is this `Contributor.vy` blueprint.

## Catalog

- **BD-01** — CHANGED eligibility; SOURCE-REACHABLE. Master lets initial RipeHq governance start before setup; rh blocks while top-level RipeHq has zero governance changes. Only RipeHq notices—local hosts initialize with a nonzero HQ. Refs: M `LocalGov:172-199; RipeHq:33-40,100-112`; R same paths `171-199; 33-40,100-112`.

- **BD-02** — CHANGED eligibility; SOURCE-REACHABLE. Existing no-change/min/max checks remain; rh additionally requires a new action timelock not exceed expiration and caps expiration at `MAX_ACTION_TIMELOCK`. TimeLock-host governance notices. Refs: M `TimeLock:179-207,230-254`; R `TimeLock:180-208,231-255`.

- **BD-03** — NEW; CONFIGURATION-CONTINGENT. Five governor-only immediate Echo calls forward to VaultMigrator at HQ ID `25`; successful use requires that ID to resolve. Migration mechanics are referred. Refs: M `D(names)`; R `Echo:538-539,562-619; Addys:64,485-497`.

- **BD-04** — NEW; SOURCE-REACHABLE. Echo adds timelocked global/user RipeGov-point disable actions, validating the registered target and current disable state at proposal and execution. It does not check pause state or explicit RipeGov classification. Refs: M `D(names)`; R `Echo:627-706,1388-1404`.

- **BD-05** — CHANGED ABI/outcome; SOURCE-REACHABLE. Endaoment partner-liquidity initiation now requires nonzero `_expectedLpToken`; the pending-action getter returns it and execution forwards it. Governance callers/getter consumers notice. Refs: M `Echo:107-114,418,757-783,1092-1095`; R `Echo:126-133,465,976-1004,1313-1316`.

- **BD-06** — NEW; SOURCE-REACHABLE. Charlie adds a timelocked core-vault route, validated twice for changed/registered contract ID, RIPE support, RipeGov interface compatibility, and unpaused state. It does not require positive `totalGovPoints`. Refs: M `D(names)`; R `Charlie:539-578,1188-1197; MC:414-420`.

- **BD-07** — NEW; SOURCE-REACHABLE. Charlie separately retargets the preferred Stability vault after registration, contract, SavingsGreen support, StabilityPool-interface, changed-ID, and pause checks at proposal and execution. Refs: M `D(names)`; R `Charlie:584-629,1199-1208; MC:426-431`.

- **BD-08** — NEW state/API; SOURCE-REACHABLE. MC initializes preferred/core IDs to `1/2`, exposes setters/getters, and marks Stability/RipeGov classifications monotonically; previous IDs remain marked after retargeting. Deployers, Switchboards, and readers notice. Refs: M `MC:195-213; D(names)`; R `MC:195-213,221-231,307-315,414-431,464-470`.

- **BD-09** — CHANGED failure policy; SOURCE-REACHABLE. Master allowed indexed-asset deregistration with live points allocations; rh rejects nonzero staker or voter allocation. Governance through Charlie notices. Refs: M `MC:317-340`; R `MC:332-357`.

- **BD-10** — CHANGED failure policy; SOURCE-REACHABLE. Charlie formerly logged successful asset/vault-asset deregistration even if MC returned false; rh asserts each return. Governance notices. Refs: M `Charlie:1041-1052`; R `Charlie:1210-1223`.

- **BD-11** — CHANGED eligibility; SOURCE-REACHABLE. Global minimum debt had no live interval relationship; rh resolves the selected MC, requires `minDebtAmount ≤ maxBorrowPerInterval`, and rechecks at execution. Refs: M `Alpha:688-707,1477-1485`; R `Alpha:690-712,1509-1518`.

- **BD-12** — CHANGED eligibility; SOURCE-REACHABLE. Master checked borrow interval against the current/default MC only at proposal. Rh checks the selected MC and revalidates against live minimum debt at execution. Refs: M `Alpha:713-731,1487-1493`; R `Alpha:718-736,1520-1527`.

- **BD-13** — CHANGED eligibility; SOURCE-REACHABLE. Auction bounds change from `maxDiscount≤100%` and loose sentinel exclusions to `<100%`, delay `≤2^32−1`, and duration `≤max_uint/10,000`. Governance and Bravo callers notice. Refs: M `Alpha:836-878`; R `Alpha:841-883`.

- **BD-14** — CHANGED eligibility; SOURCE-REACHABLE. RipeGov configuration changes from literal vault `2` to the selected MC core pointer; rh rejects zero core ID, zero max lock, and unsafe duration multiplication. Refs: M `Alpha:1358-1438,1593-1596`; R `Alpha:1386-1470,1630-1633`.

- **BD-15** — CHANGED eligibility; SOURCE-REACHABLE. Master sanitized liquidation-vault input and required no entries be lost. Rh uses the selected MC, rejects Stability/RipeGov classifications, and revalidates at execution. Refs: M `Alpha:1208-1268,1573-1576`; R `Alpha:1213-1230,1261-1293,1607-1611`.

- **BD-16** — CHANGED eligibility; SOURCE-REACHABLE. Priority-Stability input had generic registration/support checks only at proposal; rh requires live contract/interface/unpaused StabilityPool checks at proposal and execution. Refs: M `Alpha:1231-1268,1578-1581`; R `Alpha:1236-1255,1261-1293,1613-1617`.

- **BD-17** — CHANGED failure policy; SOURCE-REACHABLE. Master sanitized and rejected an empty price-source list at proposal. Rh queues nonempty raw IDs, filters invalid/duplicate/zero-address entries at execution, then rejects empty output. Refs: M `Alpha:1276-1307,1583-1586`; R `Alpha:1301-1335,1619-1623`.

- **BD-18** — CHANGED eligibility; SOURCE-REACHABLE. A nonzero staker allocation required literal vault `1` or `2`; rh requires the selected core-RipeGov ID or an ID marked Stability. Governance notices. Refs: M `Bravo:348-402`; R `Bravo:365-426`.

- **BD-19** — CHANGED eligibility; SOURCE-REACHABLE. Rh requires instant auction when swapping in Stability and structurally validates a special pool’s contract, interface, pause state, vault-asset uniqueness, and claim capacity where applicable. Refs: M `Bravo:410-484`; R `Bravo:434-539`.

- **BD-20** — CHANGED eligibility; SOURCE-REACHABLE. Proposal rails expand from LTV step-down alone to directional LTV/redemption/liquidation step-down and borrow-rate step-up limits, rechecked against live execution-time terms. Refs: M `Bravo:500-565,780-786`; R `Bravo:555-636,857-867`.

- **BD-21** — CHANGED failure policy; SOURCE-REACHABLE. Master could execute a pending asset-add after an intervening addition; rh reasserts that the asset is still unsupported before applying it. Refs: M `Bravo:222-320,748-752`; R `Bravo:238-337,819-823`.

- **BD-22** — CHANGED outcome; SOURCE-REACHABLE. After adding a non-NFT asset, rh requires PriceDesk and synchronizes token scale when its current value is zero. Governance and price integrations notice. Refs: M `Bravo:748-752`; R `Bravo:819-829`.

- **BD-23** — CHANGED eligibility; SOURCE-REACHABLE. A nonzero Underscore registry must now be a contract, report root `isValidAddr(0)=false`, and pass optional VaultRegistry/LegoBook sentinel probes. Governance notices. Refs: M `Delta:1133-1162`; R `Delta:1125-1173`.

- **BD-24** — CHANGED failure policy; SOURCE-REACHABLE. Master could execute infeasible HR cliff/vesting bounds; rh rejects `minCliffLength > min(nonzero maxVestingLength, 2^128)`. Governance notices. Refs: M `Delta:796-828,1372-1392`; R `Delta:788-820,1383-1411`.

- **BD-25** — REMOVED; SOURCE-REACHABLE. Delta no longer exposes the single-user `deleverageUser` governor/lite-signer route; batch and asset-specific routes remain. Replacement semantics are referred. Refs: M `Delta:516-523,580-595`; R `Delta:514-521,578-593; D(name)`.

- **BD-26** — CHANGED eligibility; SOURCE-REACHABLE. Rh requires a nonzero deposit lock within live RipeGov maximum, compensation `≤max_uint/2`, vesting `≤2^128`, and safe timestamps; confirmation revalidates and auto-cancels invalidated terms. Refs: M `HR:320-368`; R `HR:331-430`.

- **BD-27** — CHANGED outcome; SOURCE-REACHABLE. HR cash-checks previously used literal RipeGov vault `2`; rh reads MC’s live core-RipeGov pointer. HR callers and contributors notice after retargeting. Refs: M `HR:415-428`; R `HR:491-505`.

- **BD-28** — CHANGED outcome/signature; SOURCE-REACHABLE. HR balance, transfer, and refund calls gain optional vault ID and resolve nonzero explicit ID, otherwise contributor legacy mapping, otherwise core; explicit IDs require RipeGov classification. Refs: M `HR:387-409,435-451`; R `HR:449-485,512-538,592-617`.

- **BD-29** — NEW; SOURCE-REACHABLE. Switchboard or the registered contributor’s owner/manager may set/clear a legacy vault. Nonzero requires a marked RipeGov ID, nonempty vault, and contributor RIPE balance. Distinct non-core use needs another configured vault. Refs: M `D(name)`; R `HR:135-137,620-637`.

- **BD-30** — CHANGED outcome; SOURCE-REACHABLE. Transfer formerly updated only recipient Lootbox points. Rh updates sender and recipient and clears the legacy mapping whenever the HR call argument was zero, even if legacy resolution supplied the vault. Refs: M `HR:396-409`; R `HR:465-485`.

- **BD-31** — CHANGED outcome/failure policy; SOURCE-REACHABLE. Refund credit becomes `min(amount,max_uint-ripeAvailForHr)`—not available-budget capping—and routed burn gains point updates, asserted success, Teller housekeeping, and conditional legacy-map clearing. Refs: M `HR:434-451; Contributor:422-448`; R `HR:511-538; Contributor:437-463`.

- **BD-32** — CHANGED outcome/signature; CONFIGURATION-CONTINGENT. Contributor initiation resolves/stores one vault ID and confirmation passes it through. Default `0` calls public `getRipeGovVaultId(0)`, selecting core directly and bypassing legacy mapping. Refs: M `Contributor:211-275`; R `Contributor:213-285; HR:449-450,600-617`.

- **BD-33** — CHANGED eligibility; CONFIGURATION-CONTINGENT. Rh constructor rejects owner=self; ownership initiation rejects self and a pending RIPE transfer and guards block addition. Configured Contributor owners/new owners notice. Refs: M `Contributor:123-162,298-323`; R `Contributor:125-164,308-338`.

- **BD-34** — CHANGED outcome/API; CONFIGURATION-CONTINGENT. Successful ownership confirmation now safely increments public `numOwnerChanges`; master had no counter. Contributor integrators notice. Refs: M `Contributor:313-323; D(name)`; R `Contributor:326-338`.

- **BD-35** — CHANGED failure policy; CONFIGURATION-CONTINGENT. Master’s `compensation*elapsed` can overflow; rh uses an equivalent quotient/remainder floor calculation and asserts `vestingLength≤2^128`. Ordinary results are unchanged; extreme configured cases stop reverting. Refs: M `Contributor:479-492`; R `Contributor:494-520`.

- **BD-36** — CHANGED outcome; SOURCE-REACHABLE. Master cleared the TimeLock record before reading the confirmation block, so `NewContributorCancelled` reported zero; rh captures the real block first. Refs: M `HR:255-275; TimeLock:93-98,168-171`; R `HR:265-286`.

- **BD-37** — CHANGED failure policy; SOURCE-REACHABLE. HR’s public total-claimed and total-compensation views previously reverted on checked-addition overflow; rh returns `max_value(uint256)`. Dashboards and integrators notice. Refs: M `HR:459-494`; R `HR:546-587`.

- **BD-38** — CHANGED outcome; CONFIGURATION-CONTINGENT. DefaultsBase priority price-source IDs change from `[1,8,2,9,4,5]` to `[1,8,2,4,5]`; MC copies this only when the deployer supplies DefaultsBase. Refs: M `DefaultsBase:1262-1265; MC:217-248`; R `DefaultsBase:1262-1265; MC:221-259`.

- **BD-39** — NEW profile; CONFIGURATION-CONTINGENT. `DefaultsBaseLive` is a new generated Base live-replacement profile, consumed only if supplied to MC/Ledger. It is not field-compared to DefaultsBase. Refs: M `D(path)`; R `DefaultsBaseLive:1-47,84-86`.

- **BD-40** — NEW profile; CONFIGURATION-CONTINGENT. `DefaultsRobinhood` is a new constructor-bound Robinhood launch profile, selected by deployment configuration. Refs: M `D(path)`; R `DefaultsRobinhood:1-8,44-68`.

- **BD-41** — NEW profile; CONFIGURATION-CONTINGENT. `DefaultsRobinhoodLive` is a distinct generated Robinhood live-replacement profile, selected by deployment configuration. Refs: M `D(path)`; R `DefaultsRobinhoodLive:1-31,49-51`.

- **BD-42** — NEW internal wiring; CONFIGURATION-CONTINGENT. Addys assigns IDs `23/24/25` to RIPE CCIP pool, GREEN CCIP pool, and VaultMigrator; only ID `25` gains internal helpers. This does not itself register addresses or change Addys API. Refs: M `Addys:39-61`; R `Addys:39-64,485-497`.

## Ledger

| id | surface | class | master ref | rh ref | master ≤15w | rh ≤15w | reach | R-aliases | status |
|---|---|---|---|---|---|---|---|---|---|
| BD-01 | L | CHANGED eligibility | LocalGov:172-199; RipeHq:33-40,100-112 | LocalGov:171-199; RipeHq:33-40,100-112 | HQ governance may start before setup | Initial RipeHq governance waits for setup | SOURCE-REACHABLE | R1:L-GOV-HQSETUP; R2:UC-L-025; R3:L-22; R4:L-005; R5:L-01 | VERIFIED |
| BD-02 | L | CHANGED eligibility | TimeLock:179-207,230-254 | TimeLock:180-208,231-255 | Timelock and expiration independently bounded | Timelock cannot exceed bounded expiration | SOURCE-REACHABLE | R1:L-TL-BOUNDS; R2:UC-L-026; R3:L-23; R4:L-006; R5:L-02 | VERIFIED |
| BD-03 | L | NEW | D(names) | Echo:538-539,562-619; Addys:64,485-497 | No migration API | Five calls target HQ ID 25 | CONFIGURATION-CONTINGENT | R1:L-ECHO-MIGRATE; R2:UC-L-019; R3:L-01; R4:API/ref; R5:L-03 | VERIFIED |
| BD-04 | L | NEW | D(names) | Echo:627-706,1388-1404 | No point-disable route | Timelocked global and user disable routes | SOURCE-REACHABLE | R1:L-ECHO-DISABLE; R2:UC-L-020; R3:L-02; R4:L-025; R5:L-04 | VERIFIED |
| BD-05 | L | CHANGED ABI/outcome | Echo:107-114,418,757-783,1092-1095 | Echo:126-133,465,976-1004,1313-1316 | No expected LP token | Required token stored and forwarded | SOURCE-REACHABLE | R1:API/ref; R2:UC-L-021; R3:L-03; R4:API/ref; R5:L-05 | VERIFIED |
| BD-06 | L | NEW | D(names) | Charlie:539-578,1188-1197; MC:414-420 | No core-pointer action | Validated timelocked core retarget | SOURCE-REACHABLE | R1:L-MC-VAULT-PTRS; R2:UC-L-013/028; R3:L-04; R4:L-015; R5:L-06 | VERIFIED |
| BD-07 | L | NEW | D(names) | Charlie:584-629,1199-1208; MC:426-431 | No preferred-vault action | Validated timelocked Stability retarget | SOURCE-REACHABLE | R1:L-MC-VAULT-PTRS; R2:UC-L-014/028; R3:L-04; R4:L-015; R5:L-06 | VERIFIED |
| BD-08 | L | NEW state/API | MC:195-213; D(names) | MC:195-213,221-231,307-315,414-431,464-470 | Hardcoded identities, no pointers | Defaults 2/1; monotonic classification maps | SOURCE-REACHABLE | R1:L-MC-VAULT-PTRS; R2:UC-L-028; R3:L-05; R4:L-015; R5:L-07 | VERIFIED |
| BD-09 | L | CHANGED failure policy | MC:317-340 | MC:332-357 | Live points do not block deregistration | Live allocations revert deregistration | SOURCE-REACHABLE | R1:L-MC-DEREG; R2:UC-L-027; R3:L-06; R4:L-016; R5:L-08 | VERIFIED |
| BD-10 | L | CHANGED failure policy | Charlie:1041-1052 | Charlie:1210-1223 | False deregistration returns ignored | Both returns asserted | SOURCE-REACHABLE | R1:Brief; R2:UC-L-015; R3:L-06; R4:L-016; R5:L-08 | VERIFIED |
| BD-11 | L | CHANGED eligibility | Alpha:688-707,1477-1485 | Alpha:690-712,1509-1518 | No interval cross-check | Minimum debt cannot exceed interval maximum | SOURCE-REACHABLE | R1:L-ALPHA-DEBT-X; R2:UC-L-007; R3:L-10; R4:L-007; R5:L-11 | VERIFIED |
| BD-12 | L | CHANGED eligibility | Alpha:713-731,1487-1493 | Alpha:718-736,1520-1527 | Current MC checked only at proposal | Selected MC checked again at execution | SOURCE-REACHABLE | R2:UC-L-007; R3:L-10; R4:L-007; R5:L-11 | VERIFIED |
| BD-13 | L | CHANGED eligibility | Alpha:836-878 | Alpha:841-883 | Discount permits 100%; loose bounds | Discount below 100%; arithmetic-safe bounds | SOURCE-REACHABLE | R1:L-ALPHA-AUCTION; R2:UC-L-006; R3:L-11; R4:L-008; R5:L-12 | VERIFIED |
| BD-14 | L | CHANGED eligibility | Alpha:1358-1438,1593-1596 | Alpha:1386-1470,1630-1633 | Literal vault 2; zero max allowed | Selected nonzero core; safe nonzero max | SOURCE-REACHABLE | R1:L-ALPHA-RIPEGOV; R2:UC-L-005; R3:L-12; R4:L-011; R5:L-13 | VERIFIED |
| BD-15 | L | CHANGED eligibility | Alpha:1208-1268,1573-1576 | Alpha:1213-1230,1261-1293,1607-1611 | Generic sanitation; no type split | Reject Stability/RipeGov; revalidate | SOURCE-REACHABLE | R1:L-ALPHA-PRIVault; R2:UC-L-008; R3:L-08; R4:L-009; R5:L-09 | VERIFIED |
| BD-16 | L | CHANGED eligibility | Alpha:1231-1268,1578-1581 | Alpha:1236-1255,1261-1293,1613-1617 | Generic proposal checks | Live StabilityPool checks twice | SOURCE-REACHABLE | R1:L-ALPHA-PRIVault; R2:UC-L-008; R3:L-08; R4:L-009; R5:L-09 | VERIFIED |
| BD-17 | L | CHANGED failure policy | Alpha:1276-1307,1583-1586 | Alpha:1301-1335,1619-1623 | Sanitize and reject empty at proposal | Sanitize and reject empty at execution | SOURCE-REACHABLE | R1:L-ALPHA-PRISRC; R2:UC-L-009; R3:L-09; R4:L-010; R5:L-10 | VERIFIED |
| BD-18 | L | CHANGED eligibility | Bravo:348-402 | Bravo:365-426 | Staker allocation requires ID 1 or 2 | Requires core-RipeGov or Stability classification | SOURCE-REACHABLE | R1:L-BRAVO-STAKER; R3:Brief; R4:L-012; R5:L-15 | VERIFIED |
| BD-19 | L | CHANGED eligibility | Bravo:410-484 | Bravo:434-539 | Light special-pool validation | Instant-auction and structural pool checks | SOURCE-REACHABLE | R1:L-BRAVO-LIQ; R2:UC-L-010; R3:L-28; R4:L-012; R5:L-15 | VERIFIED |
| BD-20 | L | CHANGED eligibility | Bravo:500-565,780-786 | Bravo:555-636,857-867 | LTV proposal rail only | Four directional rails; execution recheck | SOURCE-REACHABLE | R1:L-BRAVO-STEP; R2:UC-L-011; R3:L-28; R4:L-013; R5:L-14 | VERIFIED |
| BD-21 | L | CHANGED failure policy | Bravo:222-320,748-752 | Bravo:238-337,819-823 | Intervening asset addition may be overwritten | Asset must remain unsupported | SOURCE-REACHABLE | R3:L-28; R4:L-014; R5:L-15 | VERIFIED |
| BD-22 | L | CHANGED outcome | Bravo:748-752 | Bravo:819-829 | No token-scale initialization | Missing non-NFT scale synchronized | SOURCE-REACHABLE | R2:UC-L-012; R3:L-28; R4:L-014; R5:L-15 | VERIFIED |
| BD-23 | L | CHANGED eligibility | Delta:1133-1162 | Delta:1125-1173 | Ledger/sentinel probe only | Contract plus topology probes | SOURCE-REACHABLE | R1:L-DELTA-UNDY; R2:UC-L-017; R3:L-15; R4:L-022; R5:L-17 | VERIFIED |
| BD-24 | L | CHANGED failure policy | Delta:796-828,1372-1392 | Delta:788-820,1383-1411 | Infeasible HR bounds may execute | Cliff/vesting feasibility enforced | SOURCE-REACHABLE | R2:UC-L-018; R3:L-14; R4:L-021; R5:L-18 | VERIFIED |
| BD-25 | L | REMOVED | Delta:516-523,580-595 | Delta:514-521,578-593; D(name) | Single-user deleverage route exists | Route removed | SOURCE-REACHABLE | R1:API/ref; R2:UC-L-016; R3:L-13; R4:ref; R5:L-16 | VERIFIED |
| BD-26 | L | CHANGED eligibility | HR:320-368 | HR:331-430 | Lock and arithmetic bounds incomplete | Live lock and overflow bounds; revalidate | SOURCE-REACHABLE | R1:L-HR-TERMS-LOCK; R2:UC-L-022; R3:L-16; R4:L-017; R5:L-19 | VERIFIED |
| BD-27 | L | CHANGED outcome | HR:415-428 | HR:491-505 | Cash-check uses vault 2 | Cash-check uses live core | SOURCE-REACHABLE | R1:L-HR-VAULT-ROUTE; R2:UC-L-023; R3:L-20; R4:ref; R5:L-20 | VERIFIED |
| BD-28 | L | CHANGED outcome/signature | HR:387-409,435-451 | HR:449-485,512-538,592-617 | HR I/O uses vault 2 | Explicit, legacy, then core resolution | SOURCE-REACHABLE | R1:L-HR-VAULT-ROUTE; R2:UC-L-023; R3:L-17/L-18; R4:ref; R5:L-20 | VERIFIED |
| BD-29 | L | NEW | D(name) | HR:135-137,620-637 | No legacy-vault setter | Authorized validated set or clear | SOURCE-REACHABLE | R1:L-HR-LEGACY; R2:UC-L-024; R3:L-19; R4:L-024; R5:L-21 | VERIFIED |
| BD-30 | L | CHANGED outcome | HR:396-409 | HR:465-485 | Recipient points refreshed | Sender and recipient refreshed; mapping may clear | SOURCE-REACHABLE | R1:L-HR-VAULT-ROUTE; R2:UC-L-023; R3:L-17; R4:ref; R5:L-22 | VERIFIED |
| BD-31 | L | CHANGED outcome/failure policy | HR:434-451; Contributor:422-448 | HR:511-538; Contributor:437-463 | Full credit; fixed optional burn | Headroom cap; routed asserted burn; housekeeping | SOURCE-REACHABLE | R2:UC-L-023; R3:L-18; R4:ref; R5:L-22 | VERIFIED |
| BD-32 | L | CHANGED outcome/signature | Contributor:211-275 | Contributor:213-285; HR:449-450,600-617 | Transfer fixed to vault 2 | Selected vault stored and forwarded | CONFIGURATION-CONTINGENT | R1:L-CONTRIB-XFER; R2:API; R3:L-21; R4:API/ref; R5:L-23 | VERIFIED |
| BD-33 | L | CHANGED eligibility | Contributor:123-162,298-323 | Contributor:125-164,308-338 | Self/overlapping ownership cases accepted | Self and pending-transfer cases rejected | CONFIGURATION-CONTINGENT | R1:L-CONTRIB-OWNER; R2:UC-L-029; R3:L-21; R4:L-023; R5:L-23 | VERIFIED |
| BD-34 | L | CHANGED outcome/API | Contributor:313-323; D(name) | Contributor:326-338 | No owner-change counter | Safe public counter increment | CONFIGURATION-CONTINGENT | R1:API; R2:UC-L-029/API; R3:L-21; R4:L-023/API; R5:L-23/API | VERIFIED |
| BD-35 | L | CHANGED failure policy | Contributor:479-492 | Contributor:494-520 | Multiplication may overflow | Equivalent quotient/remainder calculation | CONFIGURATION-CONTINGENT | R2:file; R3:L-21; R4:L-020; R5:L-23 | VERIFIED |
| BD-36 | L | CHANGED outcome | HR:255-275; TimeLock:93-98,168-171 | HR:265-286 | Cancellation event reports block zero | Event preserves confirmation block | SOURCE-REACHABLE | R4:L-018 | VERIFIED |
| BD-37 | L | CHANGED failure policy | HR:459-494 | HR:546-587 | Aggregate addition may revert | Aggregate saturates at uint256 maximum | SOURCE-REACHABLE | R4:L-019 | VERIFIED |
| BD-38 | L | CHANGED outcome | DefaultsBase:1262-1265; MC:217-248 | DefaultsBase:1262-1265; MC:221-259 | Priority IDs include 9 | ID 9 omitted | CONFIGURATION-CONTINGENT | R1:L-DEF-BASE-PX; R2:UC-L-001; R3:L-27; R4:L-001; R5:L-24 | VERIFIED |
| BD-39 | L | NEW profile | D(path) | DefaultsBaseLive:1-47,84-86 | Profile absent | Selectable Base live profile | CONFIGURATION-CONTINGENT | R1:L-DEF-BASELIVE; R2:UC-L-002; R3:L-24; R4:L-002; R5:L-25 | VERIFIED |
| BD-40 | L | NEW profile | D(path) | DefaultsRobinhood:1-8,44-68 | Profile absent | Selectable Robinhood launch profile | CONFIGURATION-CONTINGENT | R1:L-DEF-RH; R2:UC-L-003; R3:L-25; R4:L-003; R5:L-26 | VERIFIED |
| BD-41 | L | NEW profile | D(path) | DefaultsRobinhoodLive:1-31,49-51 | Profile absent | Selectable Robinhood live profile | CONFIGURATION-CONTINGENT | R1:L-DEF-RHLIVE; R2:UC-L-004; R3:L-26; R4:L-004; R5:L-27 | VERIFIED |
| BD-42 | L | NEW internal wiring | Addys:39-61 | Addys:39-64,485-497 | IDs end at 22 | Constants 23/24/25; ID-25 helpers | CONFIGURATION-CONTINGENT | R1:L-HQ-IDS; R2:file; R3:narrative; R4:ref; R5:L-03 support | VERIFIED |
| UC-01 | L | UNCHANGED outcome | DefaultsLocal:1-156 | DefaultsLocal:1-156 | DefaultsLocal snapshot | Same except copyright year | N/A — UC | R1:UC-L-LOCAL; R2:file; R3:UC broad; R4:UC-L-001; R5:UC-L-03 | VERIFIED |
| UC-02 | L | UNCHANGED outcome | TrainingWheels:42-57 | TrainingWheels:42-57 | Allowlist authority and outcome | Same | N/A — UC | R1:UC-L-TW; R2:file; R3:UC broad; R4:UC-L-002; R5:UC-L-03 | VERIFIED |
| UC-03 | L | UNCHANGED outcome | DeptBasics:43-94 | DeptBasics:43-94 | Pause, recovery, mint flags | Same | N/A — UC | R1:UC-L-DEPT; R2:file; R3:UC broad; R4:UC-L-003; R5:UC-L-03 | VERIFIED |
| UC-04 | L | UNCHANGED local body | RipeHq:215-229,376-399 | RipeHq:215-229,376-399 | Registry/HQ-config/mint bodies | Same | N/A — UC | R1:UC-L-HQ; R2:file; R3:UC broad; R4:UC-L-004; R5:UC-L-02 | VERIFIED |
| UC-05 | L | UNCHANGED outcome | Switchboard:53-150 | Switchboard:53-150 | Registry and blacklist routes | Same | N/A — UC | R1:UC-L-SB; R2:file; R3:UC broad; R4:UC-L-005; R5:UC-L-02 | VERIFIED |
| UC-06 | L | UNCHANGED outcome | AddressRegistry:409-420 | AddressRegistry:409-420 | Timelocked registry write | Same | N/A — UC | R1:UC-L-AR; R2:file; R3:UC broad; R4:UC-L-006; R5:UC-L-02 | VERIFIED |
| UC-07 | L | UNCHANGED API/outcome | Addys:16-34,75-78,146-149 | Addys:16-34,78-81,149-152 | getAddys/getRipeHq struct and fields | Same | N/A — UC | R1:UC-L-ADDYS; R2:file; R3:narrative; R4:UC-L-007; R5:file | VERIFIED |
| UC-08 | L | UNCHANGED outcome | Charlie:584-604 | Charlie:731-751 | Existing debt-update routes | Same | N/A — UC | R1:UC-L-CHARLIE-REST; R3:narrative; R5:file | VERIFIED |
| UC-09 | L | UNCHANGED outcome | Delta:899-924,1235-1243 | Delta:891-916,1246-1254 | Paycheck cancellation and BondBooster writes | Same | N/A — UC | R3:narrative; R5:file | VERIFIED |
| UC-10 | L | UNCHANGED authority | LocalGov:118-158 | LocalGov:117-157 | Governor enumeration and access checks | Same | N/A — UC | R5:UC-L-01; other reports implicit | VERIFIED |

No Ledger row is `UNRESOLVED` or `UNCHECKED`.

## Files

| FOCUS path | final | ids | note |
|---|---|---|---|
| `contracts/config/DefaultsBase.vy` | CONFIRMED | BD-38 | Existing profile drops ID 9; CC reach |
| `contracts/config/DefaultsBaseLive.vy` | CONFIRMED | BD-39 | Added on rh; CC reach |
| `contracts/config/DefaultsLocal.vy` | INSPECTED same outcome | UC-01 | Copyright year only |
| `contracts/config/DefaultsRobinhood.vy` | CONFIRMED | BD-40 | Added on rh; CC reach |
| `contracts/config/DefaultsRobinhoodLive.vy` | CONFIRMED | BD-41 | Added on rh; CC reach |
| `contracts/config/SwitchboardAlpha.vy` | CONFIRMED | BD-11–BD-17 | Debt, auction, RipeGov, and priority validation |
| `contracts/config/SwitchboardBravo.vy` | CONFIRMED | BD-18–BD-22 | Staker, liquidation, debt rails, asset execution |
| `contracts/config/SwitchboardCharlie.vy` | CONFIRMED | BD-06, BD-07, BD-10, UC-08 | Pointer routes and deregistration returns |
| `contracts/config/SwitchboardDelta.vy` | CONFIRMED | BD-23–BD-25, UC-09 | Underscore, HR feasibility, removed route |
| `contracts/config/SwitchboardEcho.vy` | CONFIRMED | BD-03–BD-05 | Migration, disable, expected-LP action |
| `contracts/config/TrainingWheels.vy` | INSPECTED same outcome | UC-02 | Copyright year only |
| `contracts/data/MissionControl.vy` | CONFIRMED | BD-08, BD-09, BD-38 | Pointer state/classification and deregistration |
| `contracts/core/HumanResources.vy` | CONFIRMED | BD-26–BD-31, BD-36, BD-37 | Terms, vault routing, refund, event, aggregates |
| `contracts/modules/Addys.vy` | CONFIRMED | BD-42, UC-07 | Internal IDs changed; external API unchanged |
| `contracts/modules/Contributor.vy` | CONFIRMED | BD-32–BD-35 | All behavior rows are CC |
| `contracts/modules/DeptBasics.vy` | INSPECTED same outcome | UC-03 | Copyright year only |
| `contracts/modules/LocalGov.vy` | CONFIRMED | BD-01, UC-10 | New gate fires only on top-level RipeHq |
| `contracts/modules/TimeLock.vy` | CONFIRMED | BD-02, BD-36 | Configuration bounds; event-path support |
| `contracts/registries/RipeHq.vy` | CONFIRMED | BD-01, UC-04 | Exported bootstrap gate; own body otherwise same |
| `contracts/registries/Switchboard.vy` | INSPECTED same outcome | UC-05 | LocalGov initialized with nonzero HQ |
| `contracts/registries/modules/AddressRegistry.vy` | INSPECTED same outcome | UC-06 | Copyright year only |

## API

### Added

- `SwitchboardCharlie`
  - `setCoreRipeGovVaultId`
  - `setPreferredStabVaultId`
  - `pendingCoreRipeGovVaultId`
  - `pendingPreferredStabVaultId`

- `MissionControl`
  - `setCoreRipeGovVaultId`
  - `setPreferredStabVaultId`
  - `coreRipeGovVaultId`
  - `preferredStabVaultId`
  - `isStabVaultId`
  - `isRipeGovVaultId`

- `SwitchboardEcho`
  - `migrateRipeGovPositions`
  - `migrateRipeGovPositionsForUserByAssets`
  - `migrateVaultPositions`
  - `migrateVaultPositionsForUserByAssets`
  - `migrateLegacyRipeGovPositions`
  - `isValidRipeGovPointAccrualDisable`
  - `disableRipeGovPointAccrualGlobally`
  - `disableRipeGovPointAccrualForUser`
  - `pendingRipeGovPointAccrualDisableActions`

- `HumanResources`
  - `getRipeGovVaultId`
  - `setLegacyContributorRipeGovVaultId`
  - `legacyContributorRipeGovVaultId`

- `Contributor`
  - `numOwnerChanges`
  - `pendingRipeTransferVaultId`

- Each new Defaults contract—`DefaultsBaseLive`, `DefaultsRobinhood`, and `DefaultsRobinhoodLive`—adds the existing 17-name Defaults surface:
  - `assetConfigs`
  - `genConfig`
  - `genDebtConfig`
  - `hrConfig`
  - `liteSigners`
  - `priorityLiqAssetVaults`
  - `priorityPriceSourceIds`
  - `priorityStabVaults`
  - `rewardsConfig`
  - `ripeAvailForBonds`
  - `ripeAvailForHr`
  - `ripeAvailForRewards`
  - `ripeBondConfig`
  - `ripeGovVaultConfigs`
  - `shouldCheckLastTouch`
  - `trainingWheels`
  - `underscoreRegistry`

### Removed

- `SwitchboardDelta.deleverageUser`
  - Both default-argument ABI call shapes disappear.

### Signature/return-shape changed

- `SwitchboardEcho.addPartnerLiquidityInEndaoment` adds required `_expectedLpToken`.
- `SwitchboardEcho.pendingEndaoPartnerPoolActions` returns the added `expectedLpToken` field.
- `HumanResources.hasRipeBalance` adds optional `_vaultId: uint256 = 0`.
- `HumanResources.transferContributorRipeTokens` adds optional `_vaultId: uint256 = 0`.
- `HumanResources.refundAfterCancelPaycheck` adds optional `_vaultId: uint256 = 0`.
- `Contributor.initiateRipeTransfer` adds optional `_vaultId: uint256 = 0`.

The old shorter HR/Contributor call shapes remain available through Vyper default arguments; the longer shapes are added.

No export-name changes were found. Addys constants/helpers, embedded interface declarations, events, structs, and removed `HumanResources.RIPE_GOV_VAULT_ID` are not rebuilt external API names.

## Dropped / Open / referrals / SYNTH-CHECK

**Dropped or corrected**

- The TimeLock block-arithmetic guards were not retained as a separate product-behavior row: their only distinction requires astronomically unreachable block values.
- R2’s claim that master silently shortened invalid priority-vault lists loses. Master sanitized and then asserted equal length.
- R2’s claim that master could store an empty sanitized priority-source list loses. Master rejected it at proposal.
- R2’s proposed core-vault requirement `totalGovPoints > 0` loses. Charlie only interface-probes that function.
- R3’s point-disable pause and explicit `isRipeGovVaultId` requirements lose; neither exists.
- Broad “all LocalGov hosts notice” claims lose. Only top-level RipeHq satisfies the new predicate.
- Source-reachable classifications for Echo migration, Contributor behavior, DefaultsBase, and new Defaults profiles lose to the CC classifications above.
- R5’s CC classification for the legacy-vault setter loses for the call itself; the setter is directly reachable. A distinct alternate-vault effect remains configuration-dependent.
- “Refund capped to available HR budget” loses. The cap is remaining uint256 headroom above `ripeAvailForHr`.
- “Legacy mapping clears after a default-vault transfer” is narrowed: it clears when HR receives argument `0`, even if that resolves through legacy.
- “HQ IDs 23–25 are reserved/registered” is narrowed to internal constants and ID-25 helpers; registration is not proven.
- R2’s API removals for MC `underscoreRegistry`/`shouldCheckLastTouch`, `PendingCancelPaycheck`, interface declarations, constants, and events are excluded. The actual getters remain or the items are not API under the requested rebuild.
- Contributor vesting produces the same ordinary floor result; `BD-35` retains only the verified extreme-input failure-policy distinction.
- R3’s “22 lane files” loses to the actual 21-entry FOCUS list.
- R2’s attempted closure of the Lane 3C RipeHq mint/burn referral is rejected by the lane instruction.

**Open**

- None. All source disagreements relevant to this lane were settled.
- `SYNTH-CHECK: none.` The rebuilt API contained no unreported name delta.

**Referrals kept open**

- **Lane 3C:** RipeHq mint/burn allowance.
- **Vault:** Echo migration mechanics; downstream point-disable effects; HR/Contributor transfer and refund effects.
- **Treasury/PSM/Endaoment:** downstream meaning of `_expectedLpToken`.
- **Liquidation/deleverage:** MC `getGenLiqConfig` zero-address filtering; replacement semantics for removed `deleverageUser`; Bravo downstream liquidation effects.
- **Price:** Defaults ID `9` identity/effect, execution-time price-source sanitation, and PriceDesk token-scale consequences.
- **Rewards/borrow:** Lootbox point and Teller-housekeeping consequences.
- **Token/CCIP:** consumers and registration of Addys IDs `23/24`.
- **Other lane/scope:** Ledger `_actionBlockSource` and BondBooster behavior.

LANE SYNTHESIS COMPLETE — Lane 3D — 91eda49c vs 251ac9e2
