# PR #67 lane synthesis — Lane 1

Draft only. Not a source of truth. If this file and the contracts disagree,
the contracts win.

- master: 91eda49ccd34a25090582aff0695075c4c806011
- rh:     251ac9e228a8af80326e8fe30f607511c78fe820
- date:   2026-08-22

# PR #67 behavior delta — Lane 1 — 91eda49c vs 251ac9e2

## Brief

Source-only comparison at the exact pins:

- master: `91eda49ccd34a25090582aff0695075c4c806011`, tree `fbd958bec234081f70769045abd8f9bb638f6dd7`
- rh: `251ac9e228a8af80326e8fe30f607511c78fe820`, tree `204de8657d9cd2eded1212028b9b5ba8d87b6506`

`SR` means verified source-reachable. `CC` means verified but configuration or asset-behavior contingent. R1–R5 identify the five pasted reports in order.

### VERIFIED SOURCE-REACHABLE

`BD-01`, `BD-03`, `BD-05`, `BD-08`–`BD-12`, `BD-16`–`BD-18`, `BD-20`, `BD-21`, `BD-24`, `BD-27`, `BD-28`, `BD-32`.

### VERIFIED CONFIGURATION-CONTINGENT

`BD-07`, `BD-13`, `BD-15`, `BD-23`, `BD-25`, `BD-26`, `BD-29`.

## Catalog

### VERIFIED SOURCE-REACHABLE

- `BD-01` — R1:D-01; R2:UC-D-01; R3:D-1; R4:D-01; R5:L1-03. Debt-health quarantine, SR. Master skips zero amounts and can retain positive zero-valued collateral; rh flags unusable collateral, makes non-raising health checks fail, and lets AuctionHouse decline flagged terms. Borrowers, liquidators, and health UIs notice. Refs: CE M:726–756,938–959; R:722–754,941–969; AH M:302–323; R:303–324.

- `BD-03` — R1:D-04; R3:D-3; R4:E-09/E-11; R5:L1-11. Custody safety, SR. BasicVault master reports nominal balances; rh reports zero when custody is below aggregate nominal liability, feeding quarantine or liquidation-selection skips. Under-backed vault users and liquidators notice. Refs: BV M:116–148; R:140–185.

- `BD-05` — R4:D-04; R5:L1-12. Full repayment, SR. Master still traverses collateral after debt reaches zero; rh skips traversal, clears liquidation state, and emits empty term fields. Repayers with unusable collateral notice. Refs: CE M:542–578; R:537–580.

- `BD-08` — R1:D-03/E-01; R2:UC-D-02; R3:E-1; R4:D-05/E-01; R5:L1-01. Repeat liquidation, SR. Master’s `inLiquidation` state blocks another pass; rh permits retry once no stored auction remains. Keepers and still-unhealthy borrowers notice. Refs: AH M:312–314; R:310–315; CE M:949–951; R:952–969.

- `BD-09` — R1:E-07; R2:UC-E-06; R3:E-9; R4:E-02; R5:L1-02. Auction cleanup, SR. Rh adds permissionless removal of active expired auctions while unpaused; paused calls revert, and missing/inactive or unexpired auctions return false. Keepers and retrying liquidators notice. Ref: AH R:1003–1033.

- `BD-10` — R1:E-02; R2:UC-E-01/02; R3:E-2; R4:E-03; R5:L1-04. Liquidation fees, SR. Master’s sole admissible pass retains computed fees even if inert. Rh computes fees only before the first freeze, zeroes them for an inert first pass, and charges no retry fees. Borrowers, keepers, and accounting consumers notice. Refs: AH M:328–376; R:326–366.

- `BD-11` — R1:E-03; R2:UC-E-03; R3:E-2/E-3; R4:E-04; R5:L1-04. Stability Pool allocation, SR. Master’s spread covers base and keeper fees and its phase target is not pre-capped; rh’s spread covers base fee only, leaves keeper fee as debt, and caps the phase target. Pool depositors, keepers, and borrowers notice. Refs: AH M:328–376; R:326–366.

- `BD-12` — R1:E-04/E-08/E-12; R3:E-4; R4:E-11/G-15; R5:L1-09/L1-11. Liquidation selection, SR. Master selects by nominal balance; rh selects by safe realizable amount. Healthy canonical Stability Pool collateral remains eligible, while under-backed, paused, or otherwise unusable cohorts can be skipped. Liquidators and borrowers notice. Refs: AH M:420–423,513–521,889–894; R:410–413,503–511,878–883; SV M:217–232; R:285–346.

- `BD-16` — R1:E-09; R2:UC-E-04; R3:E-8; R4:E-06; R5:L1-06. Auction pricing, SR. Master’s discrete curve can finish below maximum discount; rh reaches the terminal discount at `duration-1`, including duration one. Buyers and borrowers notice. Refs: AH M:1124–1126,1171–1178; R:1157–1166.

- `BD-17` — R1:E-09; R2:UC-E-05; R3:E-7; R4:E-07; R5:L1-05. Purchase conservation, SR. Master lacks a live-debt cap and tolerates minimum-plus-one-percent payment, allowing excess repayment to reach the borrower. Rh caps by live debt, requires its computed spend, and returns unused batch GREEN to the caller. Buyers and borrowers notice. Refs: AH M:1118–1150; R:1090–1107,1148–1189; CE M:484–502,574–576; R:493–499.

- `BD-18` — R1:E-10; R3:E-7; R4:E-08; R5:L1-07. Zero-credit purchases, SR. Master may move collateral before discovering zero credited value. Rh preflights zero-credit entries and makes a post-transfer zero payment revert the batch. Buyers and vault recipients notice. Refs: AH M:1225–1243; R:1123–1124,1181–1189,1256–1277; CE R:493–499.

- `BD-20` — R1:E-11/G-04; R2:UC-E-09/UC-G-07; R3:API; R4:E-13/G-01; R5:L1-17. Teller API, SR. Rh removes the three singular buy, claim, and redeem routes while retaining batch routes. Integrators using singular selectors notice. Refs: T M:580–702; R:643–723.

- `BD-21` — R1:G-04; R2:API; R3:API; R4:G-01; R5:L1-17. StabilityPool host API, SR. Rh stops exporting two conversion and two singular claim/redemption methods, although the StabVault module still defines them. Direct StabilityPool callers notice. Refs: SP M:21–23; R:43–60; SV M:366–411,589–606,765–790.

- `BD-24` — R1:G-01; R2:UC-G-04; R3:G-2; R4:G-03/G-04/G-05; R5:L1-13. Stability Pool deposits, SR. Master permits GREEN, reserved-asset, and zero-share deposits; rh rejects all three. Depositors notice. Refs: SV M:109–141; R:172–207.

- `BD-27` — R1:G-03; R2:UC-G-01; R3:G-3; R4:G-09; R5:L1-14. Claim-asset lifecycle, SR. Master activates immediately and delists below $0.10. Rh separates active and dormant cohorts, caps active assets at 20, and applies guarded activation and retention floors; dormant pairs remain explicitly claimable. Pool claimants and maintainers notice. Refs: SV M:1023–1075; R:118–140,1364–1465.

- `BD-28` — R1:G-07; R2:UC-G-01; R3:G-4; R4:G-10; R5:L1-16. Claim-asset maintenance, SR. Rh adds active-count/state/acceptance views and permissionless pruning; master has no equivalent surface. Maintainers and monitoring clients notice. Refs: SP R:55–59; SV R:1185–1224,1325–1327.

- `BD-32` — R1:G-06; R3:G-7; R4:G-13; R5:L1-20. Recovery authority, SR. Master’s inherited recovery selectors can move orphaned funds under Switchboard authority; rh retains the selectors but makes both always revert. Governance and incident responders notice. Refs: SP M:21–23; VD M:280–302; SP R:217–224.

### VERIFIED CONFIGURATION-CONTINGENT

- `BD-07` — R1:D-02 (extra IDs); R4:D-06; R5:L1-10. Stability-ID treatment, CC. Canonical Stability Pool collateral has no borrow power on either pin. Rh additionally excludes every MissionControl-configured Stability vault ID; master has no equivalent generic exclusion. Custom Stability-vault users notice. Refs: CE M:715–731; R:707–710; SV M:217–222.

- `BD-13` — R1:E-05; R2:UC-E-07; R3:E-5; R4:E-10; R5:L1-08. Pool acceptance, CC. Master uses a same-vault-asset guard. Rh delegates to `canAcceptLiquidationAsset`, rejecting paused pools, new pairs at cap, reserved assets, deficient custody, and unpriceable assets. Liquidators and pool depositors notice when those states exist. Refs: AH M:650–669; R:640–642; SV R:1206–1224.

- `BD-15` — R1:E-06/E-10; R2:UC-G-03; R3:E-6/E-10/G-6; R4:E-09/G-08; R5:L1-07. Exact custody, CC. Rh adds backing checks and exact outflow, inflow, pool-receipt, and claim-receipt accounting where master can clamp values or trust boolean transfers. Fee-on-transfer, rebasing, or deficient-custody assets expose the difference. Refs: BV M:55–65; R:59–80; AH M:741–765; R:728–737; SV M:150–165,465–478,981–997,1023–1038; R:210–231,570–583,1132–1155,1364–1380.

- `BD-23` — R1:G-05; R2:UC-G-06; R3:Brief; R4:G-02; R5:Brief/UC-G-convert. Preferred Stability Pool, CC. Master targets fixed vault ID 1; rh uses a configured nonzero preferred ID. Deployments where the preferred ID differs notice. Refs: T M:628–642; R:671–687.

- `BD-25` — R1:G-02; R3:G-1; R4:G-06; R5:Brief. Pool principal, CC. Master treats raw custody as available principal; rh subtracts reserved balances before valuing or transferring principal. Pools with reservations notice. Refs: SV M:257–276,322–360,465; R:158–164,381–403,445–483,570.

- `BD-26` — R2:UC-G-02; R3:G-6; R4:G-07; R5:L1-15. Claim NAV, CC. Master silently skips zero-priced claim assets; rh’s active-claim valuation requires aggregate custody and nonzero price. Active pools containing deficient or unpriced claims notice. Refs: SV M:553–581; R:675–708.

- `BD-29` — R1:G-07; R2:UC-G-01; R3:G-4; R4:G-10; R5:L1-16. Cohort activation, CC. Rh adds a permissionless host activation call gated by contract pause state; internal activation also requires an empty active cohort and satisfies floor/cap rules. Maintainers notice when dormant assets qualify. Refs: SP R:55–59; SV R:1227–1243,1273–1302,1330–1333.

## Ledger

| id | surface | class | master ref | rh ref | master ≤15w | rh ≤15w | reach | R-aliases | status |
|---|---|---|---|---|---|---|---|---|---|
| BD-01 | CE/AH quarantine | Debt | CE 726–756,938–959; AH 302–323 | CE 722–754,941–969; AH 303–324 | Zero amounts skip; positive zero-value collateral can retain weight. | Unusable collateral flags quarantine; health fails and auctions may decline. | SR | R1:D-01; R2:UC-D-01; R3:D-1; R4:D-01; R5:L1-03 | VERIFIED |
| BD-02 | CE zero slots | Debt | CE 726–731,758–764 | CE 722–774 | Zero balances are skipped entirely. | Registered zero slots can affect highest and lowest LTV. | SR | R1:D-05; R4:D-02 | VERIFIED |
| BD-03 | BasicVault safe amount | Custody | BV 116–148 | BV 140–185 | Reports nominal balance without aggregate-custody deficiency check. | Preserves asset identity but reports zero under deficient custody. | SR | R1:D-04; R3:D-3; R4:E-09/E-11; R5:L1-11 | VERIFIED |
| BD-04 | CE partial repayment | Debt | CE 542–564,1131–1142 | CE 537–563,1135–1147 | Empty traversal overwrites stored debt terms. | Empty traversal preserves stored debt terms. | SR | R4:D-03 | VERIFIED |
| BD-05 | CE full payoff | Debt | CE 542–578 | CE 537–580 | Full payoff still traverses collateral strictly. | Zero debt skips traversal and clears liquidation state. | SR | R4:D-04; R5:L1-12 | VERIFIED |
| BD-06 | `UserBorrowTerms` | ABI | CE 99–104,649–673,852–857 | CE 102–108,645–666,857–862 | Five-field struct returned by three external paths. | Struct adds `hasQuarantinedAsset`; all three return ABIs expand. | SR | R1:API; R3:API; R4:D-07; R5:API | VERIFIED |
| BD-07 | configured Stability IDs | Debt | CE 715–731; SV 217–222 | CE 707–710 | No generic exclusion for configured Stability IDs. | Every configured Stability ID is excluded from debt collateral. | CC | R1:D-02 (extra IDs); R4:D-06; R5:L1-10 | VERIFIED |
| BD-08 | repeat liquidation | Liquidation | AH 312–314; CE 949–951 | AH 310–315; CE 952–969 | `inLiquidation` blocks another liquidation pass. | Only outstanding stored auctions block a retry. | SR | R1:D-03/E-01; R2:UC-D-02; R3:E-1; R4:D-05/E-01; R5:L1-01 | VERIFIED |
| BD-09 | expired-auction cleanup | Liquidation | absent | AH 1003–1033 | No public expired-auction cleanup. | Permissionless when unpaused; paused reverts; invalid timing returns false. | SR | R1:E-07; R2:UC-E-06; R3:E-9; R4:E-02; R5:L1-02 | VERIFIED |
| BD-10 | liquidation fees | Economics | AH 328–376 | AH 326–366 | Sole admissible pass retains fees even when no auction starts. | First productive freeze charges; inert passes and retries charge zero. | SR | R1:E-02; R2:UC-E-01/02; R3:E-2; R4:E-03; R5:L1-04 | VERIFIED |
| BD-11 | SP fee allocation | Economics | AH 328–376 | AH 326–366 | Spread covers base plus keeper; phase target is not pre-capped. | Spread covers base; keeper stays debt; phase target is capped. | SR | R1:E-03; R2:UC-E-03; R3:E-2/E-3; R4:E-04; R5:L1-04 | VERIFIED |
| BD-12 | amount-safe selection | Liquidation | AH 420–423,513–521,889–894; SV 217–232 | AH 410–413,503–511,878–883; SV 285–346 | Nominal balance controls eligibility and manual starts. | Safe realizable amount controls eligibility and manual starts. | SR | R1:E-04/E-08/E-12; R3:E-4; R4:E-11/G-15; R5:L1-09/L1-11 | VERIFIED |
| BD-13 | SP acceptance | Liquidation | AH 650–669 | AH 640–642; SV 1206–1224 | Same-vault-asset guard controls routing. | Pool state, capacity, custody, reservation, and price gate routing. | CC | R1:E-05; R2:UC-E-07; R3:E-5; R4:E-10; R5:L1-08 | VERIFIED |
| BD-14 | SP gross-up | Arithmetic | AH 718–748 | AH 705–737 | Gross-up uses floor-style division. | Gross-up preserves ceiling requirements. | SR | R1:E-06; R2:UC-E-08; R3:E-6; R4:E-05 | VERIFIED |
| BD-15 | exact delivery/receipt | Custody | BV 55–65; AH 741–765; SV 150–165,465–478,981–997,1023–1038 | BV 59–80; AH 728–737; SV 210–231,570–583,1132–1155,1364–1380 | Clamps amounts or trusts boolean token transfers. | Requires backing and exact outgoing and incoming balance deltas. | CC | R1:E-06/E-10; R2:UC-G-03; R3:E-6/E-10/G-6; R4:E-09/G-08; R5:L1-07 | VERIFIED |
| BD-16 | discount curve | Economics | AH 1124–1126,1171–1178 | AH 1157–1166 | Final purchasable block can remain below maximum discount. | Final purchasable block reaches maximum discount. | SR | R1:E-09; R2:UC-E-04; R3:E-8; R4:E-06; R5:L1-06 | VERIFIED |
| BD-17 | purchase conservation | Economics | AH 1118–1150; CE 484–502,574–576 | AH 1090–1107,1148–1189; CE 493–499 | No live-debt cap; excess repayment can reach borrower. | Caps live debt; exact spend; unused batch GREEN returns caller. | SR | R1:E-09; R2:UC-E-05; R3:E-7; R4:E-07; R5:L1-05 | VERIFIED |
| BD-18 | zero-credit purchase | Liquidation | AH 1225–1243 | AH 1123–1124,1181–1189,1256–1277; CE 493–499 | Collateral movement can precede discovering zero credited value. | Preflight skips zero credit; post-transfer zero payment reverts batch. | SR | R1:E-10; R3:E-7; R4:E-08; R5:L1-07 | VERIFIED |
| BD-19 | retry calculator | View semantics | AH 1316–1359 | AH 1355–1381; execution 326–346 | Retry cannot execute under `inLiquidation`. | Calculator remains fee-bearing although executable retry fees are zero. | SR | R4:E-14 | VERIFIED |
| BD-20 | Teller singular routes | API | T 580–702 | T 643–723 | Three singular Teller routes exist. | Only batch counterparts remain. | SR | R1:E-11/G-04; R2:UC-E-09/UC-G-07; R3:API; R4:E-13/G-01; R5:L1-17 | VERIFIED |
| BD-21 | StabilityPool exports | API | SP 21–23; SV 366–411,589–606,765–790 | SP 43–60 | Host exports conversions plus singular claim and redeem. | Host omits those four names; module definitions remain. | SR | R1:G-04; R2:API; R3:API; R4:G-01; R5:L1-17 | VERIFIED |
| BD-22 | delegated `lastTouch` | Authorization | T 580–615,685–722,986–998 | T 643–657,706–723,1005–1023 | Buy and redeem always write recipient touch. | Delegated buy/redeem avoids touch if recipient is unlocked and unpaused. | SR | R2:UC-D-05 (narrowed); R3:D-5; R4:E-12; R5:L1-19 | VERIFIED |
| BD-23 | preferred SP target | Routing | T 628–642 | T 671–687 | Conversion targets fixed vault ID 1. | Conversion targets configured nonzero preferred Stability vault ID. | CC | R1:G-05; R2:UC-G-06; R3:Brief; R4:G-02; R5:Brief/UC-G-convert | VERIFIED |
| BD-24 | SP deposits | Validation | SV 109–141 | SV 172–207 | GREEN, reserved, and zero-share deposits can proceed. | Rejects GREEN, reserved assets, and zero-share deposits. | SR | R1:G-01; R2:UC-G-04; R3:G-2; R4:G-03/G-04/G-05; R5:L1-13 | VERIFIED |
| BD-25 | unreserved principal | Accounting | SV 257–276,322–360,465 | SV 158–164,381–403,445–483,570 | Raw custody represents available principal. | Available principal subtracts reserved balances. | CC | R1:G-02; R3:G-1; R4:G-06; R5:Brief | VERIFIED |
| BD-26 | active-claim NAV | Accounting | SV 553–581 | SV 675–708 | Zero-priced claim assets are skipped. | Active claims require aggregate custody and nonzero price. | CC | R2:UC-G-02; R3:G-6; R4:G-07; R5:L1-15 | VERIFIED |
| BD-27 | claim-asset lifecycle | Lifecycle | SV 1023–1075 | SV 118–140,1364–1465 | Immediate activation and $0.10 delisting. | Active/dormant cohorts with cap and guarded activation/retention floors. | SR | R1:G-03; R2:UC-G-01; R3:G-3; R4:G-09; R5:L1-14 | VERIFIED |
| BD-28 | maintenance views/pruning | Lifecycle | absent | SP 55–59; SV 1185–1224,1325–1327 | No equivalent maintenance surface. | Adds state views, acceptance view, and permissionless pruning. | SR | R1:G-07; R2:UC-G-01; R3:G-4; R4:G-10; R5:L1-16 | VERIFIED |
| BD-29 | claim activation | Lifecycle | absent | SP 55–59; SV 1227–1243,1273–1302,1330–1333 | No active-cohort maintenance activation surface. | Anyone may activate while paused, subject to internal cohort gates. | CC | R1:G-07; R2:UC-G-01; R3:G-4; R4:G-10; R5:L1-16 | VERIFIED |
| BD-30 | sGREEN redemption preview | Accounting | SV 910–945 | SV 1059–1096 | Claim state mutates before resulting zero-share deposit is known. | Zero-share preview skips before claim mutation. | SR | R2:UC-G-05; R3:G-6; R4:G-11; R5:L1-21 | VERIFIED |
| BD-31 | auto-deposit self ID | Routing | SV 981–1012 | SV 1132–1174 | Auto-deposit assumes Stability Pool vault ID 1. | Uses the actual current vault ID. | CC | R2:UC-G-10; R3:G-8; R4:G-12; R5:UC-G-autodeposit | VERIFIED |
| BD-32 | recovery selectors | Authority | SP 21–23; VD 280–302 | SP 217–224 | Inherited recovery paths can transfer orphaned funds. | Both retained recovery selectors always revert. | SR | R1:G-06; R3:G-7; R4:G-13; R5:L1-20 | VERIFIED |
| BD-33 | retirement/funds detection | Lifecycle | VD 175–222 | SV 1339–1358 | Retirement and funds tests consider shares only. | Claim-pair balances also block retirement and report funds. | SR | R1:G-08; R4:G-14 | VERIFIED |
| UC-01 | interest formula | Unchanged | CE 894–910 | CE 897–913 | Debt-interest arithmetic and elapsed-time treatment. | Debt-interest arithmetic and elapsed-time treatment. | SR | R1:UC-D-1; R4:UC-D-01 | VERIFIED |
| UC-02 | health/threshold math | Unchanged | CE 938–990 | CE 941–975 | Core health ratio, thresholds, and equality boundary. | Core health ratio, thresholds, and equality boundary. | SR | R1:UC-D-2/3; R3:UC-D-1; R4:UC-D-03/04; R5:UC-D-thresholds | VERIFIED |
| UC-03 | canonical SP borrow power | Unchanged | SV 217–222; CE 715–731 | CE 707–710 | Canonical Stability Pool supplies no borrow power. | Canonical Stability Pool supplies no borrow power. | SR | R4:UC-G-01 | VERIFIED |
| UC-04 | healthy SP liquidation collateral | Unchanged | SV 225–232; AH 513–521 | SV 333–346; AH 503–511 | Healthy canonical pool balances are liquidation collateral. | Healthy canonical pool balances are liquidation collateral. | SR | R4:UC-G-02 | VERIFIED |
| UC-05 | liquidation phases | Unchanged | AH 413–430 | AH 403–420 | Priority assets precede user-vault assets. | Priority assets precede user-vault assets. | SR | R1:UC-E-1; R4:UC-E-02; R5:UC-E-phases | VERIFIED |
| UC-06 | GREEN/sGREEN deferral | Unchanged | AH 560–566 | AH 550–556 | GREEN/sGREEN and Endaoment handling remains deferred. | GREEN/sGREEN and Endaoment handling remains deferred. | SR | R1:UC-E-2; R4:UC-E-03; R5:UC-E-phases | VERIFIED |
| UC-07 | liquidation freeze | Unchanged | CE 314–322,1242–1244 | CE 314–322,1259–1261 | `inLiquidation` blocks borrow and withdrawal. | `inLiquidation` blocks borrow and withdrawal. | SR | R1:UC-E-3; R4:UC-E-04; R5:UC-E-hold | VERIFIED |
| UC-08 | liquidation entrypoints | Unchanged | AH 237–285 | AH 242–286 | Single and batch liquidation entrypoints exist. | Single and batch liquidation entrypoints exist. | SR | R1:UC-E-4; R4:UC-E-11 | VERIFIED |
| UC-09 | manual auction authority | Unchanged | AH 820–894 | AH 809–883 | Manual auction start is Switchboard-only. | Manual auction start is Switchboard-only. | SR | R1:UC-E-5; R4:UC-E-07; R5:UC-E-manual-start | VERIFIED |
| UC-10 | purchase skips/refunds | Unchanged | AH 1061–1076,1096–1112 | AH 1090–1105,1126–1142 | Core skip cases and leftover caller refund remain. | Core skip cases and leftover caller refund remain. | SR | R1:UC-E-6; R4:UC-E-06/08; R5:UC-E-purchase-skips | VERIFIED |
| UC-11 | restored health | Unchanged | L 343–345 | L 384–386 | Restored health clears stored auctions. | Restored health clears stored auctions. | SR | R1:UC-E-7; R4:UC-E-09 | VERIFIED |
| UC-12 | earn-vault guard | Unchanged | AH 298–300 | AH 299–301 | Earn-vault accounts remain rejected. | Earn-vault accounts remain rejected. | SR | R1:UC-E-8; R4:UC-E-01 | VERIFIED |
| UC-13 | keeper fee formula | Unchanged | AH 333–351 | AH 1392–1411 | Keeper fee formula and caps remain. | Keeper fee formula and caps remain. | SR | R1:UC-E-9; R3:UC-E-3; R4:UC-E-10; R5:UC-E-fee-cap | VERIFIED |
| UC-14 | SP batch routes | Unchanged | T 668–722 | T 692–723 | `claimMany` and `redeemMany` remain. | `claimMany` and `redeemMany` remain. | SR | R1:UC-G-1 | VERIFIED |
| UC-15 | SP swap authority | Unchanged | SV 444–455 | SV 555–564,617–624 | Liquidation swaps remain AuctionHouse-only. | Liquidation swaps remain AuctionHouse-only. | SR | R1:UC-G-2 | VERIFIED |
| UC-16 | AuctionHouseNFT surface | Unchanged | AHN 8–24 | AHN 8–24 | No direct product methods; effective eight-name admin export surface. | No direct product methods; effective eight-name admin export surface. | SR | R1:UC-G-3; R4:UC-E-NFT-01 | VERIFIED |
| UC-17 | share conversion math | Unchanged | SV 366–436 | SV 489–546 | Core value/share conversion math remains. | Core value/share conversion math remains. | SR | R2:G; R3:UC-G-2 | VERIFIED |

## Files

| FOCUS path | final | ids | note |
|---|---|---|---|
| `contracts/core/AuctionHouse.vy` | CONFIRMED | BD-01, BD-08–BD-19; UC-04–UC-06, UC-08–UC-10, UC-12–UC-13 | Material liquidation, pricing, purchase, retry, cleanup, and API behavior deltas. |
| `contracts/core/AuctionHouseNFT.vy` | CNC | UC-16 | Modified header only; direct product surface remains empty and effective exports remain identical. |
| `contracts/vaults/StabilityPool.vy` | CONFIRMED | BD-21, BD-24, BD-27–BD-29, BD-32–BD-33; UC-15 | Export topology changes and recovery is explicitly disabled. |
| `contracts/vaults/modules/StabVault.vy` | CONFIRMED | BD-07, BD-12–BD-15, BD-21, BD-24–BD-31, BD-33; UC-03–UC-04, UC-15, UC-17 | Material accounting, custody, lifecycle, routing, and module-API deltas. |

Shared partial surfaces cited in the ledger—CreditEngine, Teller, Ledger, BasicVault, and VaultData—are intentionally excluded from this FOCUS-only table.

## API

Rebuilt from direct externals, public getters, and effective export lists at both pins.

### `AuctionHouse.vy`

Effective names: `20 → 21`.

- Added: `removeExpiredFungibleAuction`
- Removed: none
- Signature-changed: none

### `AuctionHouseNFT.vy`

Effective names: `8 → 8`.

- Added: none
- Removed: none
- Signature-changed: none
- No direct external product methods exist on either pin.

### `StabilityPool.vy`

Effective names: `46 → 47` (`42` common).

- Added:
  - `getNumActiveClaimAssets`
  - `getClaimAssetState`
  - `canAcceptLiquidationAsset`
  - `pruneClaimableAssets`
  - `activateClaimAssets`

- Removed from the host surface:
  - `valueToShares`
  - `sharesToValue`
  - `claimFromStabilityPool`
  - `redeemFromStabilityPool`

- Signature-changed: none

`recoverFunds`, `recoverFundsMany`, `deregisterVaultAsset`, `doesVaultHaveAnyFunds`, and `pause` are retained names, not additions. The recovery implementations change as recorded in `BD-32`.

### `StabVault.vy`

Declared external names: `15 → 23`.

- Added:
  - `getNumActiveClaimAssets`
  - `getClaimAssetState`
  - `canAcceptLiquidationAsset`
  - `canActivateClaimAsset`
  - `pruneClaimableAssets`
  - `activateClaimAssets`
  - `deregisterVaultAsset`
  - `doesVaultHaveAnyFunds`

- Removed: none
- Signature-changed: none
- Five public getters remain unchanged.
- `canActivateClaimAsset` is module-external but is not exported by the StabilityPool host.
- Singular claim/redemption methods remain module-external despite disappearing from the host API.

### Reached shared APIs

- Teller removes `buyFungibleAuction`, `claimFromSP`, and `redeemFromSP`; batch counterparts remain.
- CreditEngine’s external name set is unchanged.
- `UserBorrowTerms` adds `hasQuarantinedAsset`, expanding the return ABI of:
  - `getUserBorrowTerms`
  - `getUserBorrowTermsWithNumVaults`
  - `getLatestUserDebtAndTerms`
- `getUserDebtAmount` exists at both pins; it is not an addition.

## Dropped / Open / referrals / SYNTH-CHECK

### Dropped or corrected during reconciliation

- Dropped R1:D-02’s claim that master Stability Pool collateral supplied borrow power. The canonical pool supplies none on both pins; only rh’s generic configured-ID exclusion is new.
- Dropped R2:UC-D-03’s claim that healthy Stability Pool positions become newly liquidatable. They are liquidation collateral on both pins.
- Dropped R3:D-2’s “borrow clears liquidation freeze” path. Both pins reject borrowing while `inLiquidation` before master’s later assignment can execute.
- Corrected R4:E-02: expired-auction cleanup does not return false while paused; it reverts at the pause assertion.
- Dropped R2’s governance-only characterization of `activateClaimAssets`. The external call has no caller-role check; it requires paused state, with internal cohort gates.
- Dropped R2’s claim that `canActivateClaimAsset` is host-exported.
- Dropped R2’s claim that `getUserDebtAmount` is new.
- Corrected R3’s dormant-asset claim: dormant pairs leave the active iterator/NAV but remain explicitly claimable and redeemable.
- Narrowed R3/R5 delegated-touch claims to `buyMany` and `redeemMany` recipients. `claimMany` still touches the claimer. The consequence concerns the same action-block slot, not the next block.
- Dropped R5’s claim that both pins’ singular purchase entrypoint wraps the batch path; that wrapper shape is rh-only.

### Open

- For positive-balance, zero-priced collateral, strict state-liquidation behavior remains PriceDesk-path dependent: it may revert before CreditEngine can return the quarantine flag. Non-raising health behavior and the under-backed BasicVault path are verified.
- Priority phase one can still call strict Stability Pool total-value logic; only the later safe iterator/acceptance path is fail-soft. Whether deployed priority configuration can expose this requires live configuration evidence.
- No scoped host route to module-only `canActivateClaimAsset` was established.
- `buyFungibleAuction` remains Teller-authorized in AuctionHouse, but Teller’s singular wrapper is removed; no alternative scoped rh caller route was established.
- Rh’s retry calculator is a hypothetical calculation, not an executable fee quote.

### Referrals

- R3:D-4 maximum-withdraw rounding belongs to the broader CreditEngine lane.
- Lootbox checkpointing, `coreRipeGovVaultId`, and other rewards changes belong to the rewards lane.
- `setUserConfig`, account locks, bond handling, migrations, and Ledger action-block changes belong to their owning lanes.
- `redeemCollateral` and deleverage route removals belong to the Deleverage/API lane.
- Generic Teller deposit custody and CreditRedeem changes are outside this exact BasicVault/AuctionHouse/StabVault behavior lane.
- Positive unpriced-asset strict behavior requires PriceDesk review.
- Preferred Stability IDs, priority assets, and other deployed values require MissionControl/live-configuration review.

### SYNTH-CHECK

- Exact commit and tree pins matched.
- All four FOCUS files were inspected and accounted for.
- Shared partials appear only as supporting references, not in the Files table.
- No duplicated BD/UC row remains.
- No rebuilt FOCUS API name or signature delta lacked an R1–R5 mention.
- No tests, compilers, repository scripts, fetches, branch changes, worktrees, or file edits were used.

LANE SYNTHESIS COMPLETE — Lane 1 — 91eda49c vs 251ac9e2
