# PR #67 lane synthesis — Lane 3A

Draft only. Not a source of truth. If this file and the contracts disagree,
the contracts win.

- master: 91eda49ccd34a25090582aff0695075c4c806011
- rh:     251ac9e228a8af80326e8fe30f607511c78fe820
- date:   2026-08-22

# PR #67 behavior delta — Lane 3A — 91eda49c vs 251ac9e2

Pinned commits and trees verified:

- master `91eda49ccd34a25090582aff0695075c4c806011`, tree `fbd958bec234081f70769045abd8f9bb638f6dd7`
- rh `251ac9e228a8af80326e8fe30f607511c78fe820`, tree `204de8657d9cd2eded1212028b9b5ba8d87b6506`

All five write-ups use the correct lane and pins; none was skipped wholesale.

## Brief

**VERIFIED SOURCE-REACHABLE**

- **BD-01–BD-04:** Lock top-ups use exact shares; adjust/release checkpoints now record the post-change balance; early-release fees target the live asset claim, require another holder, and make release higher-risk.
- **BD-05–BD-09:** Deposit reward categories settle atomically with full-precision ratios and dust retention; borrow-only users are minted; borrow rewards gain full precision; general-depositor funding tracks holder-represented underlying.
- **BD-10–BD-14:** Third-party loot/bond actions stop consuming the beneficiary’s last-touch slot; bond dust is refunded, preview matches execution, payment becomes explicit with min-out, and lock users may select historical RipeGov vault IDs.

**VERIFIED CONFIGURATION-CONTINGENT**

- **BD-15–BD-20:** Governance gains generic, current-RipeGov, and Base-legacy migration routes; only normal RipeGov export tombstones the source; point accrual can be irreversibly disabled; paused RipeGov vaults reject lock maintenance.
- **BD-21–BD-25:** Zero asset weight now means zero points; courtesy-unlock comparisons change; deposits and contributor transfers require lock terms; ordinary gov deposits follow the configured core vault.
- **BD-26–BD-31:** Loot and locked-bond routing follows configured RipeGov identity; historical IDs normalize correctly; registry retirement rechecks funds and stranded points; keeper per-asset claims respect `canClaimLoot`.
- **BD-32–BD-37:** Expired booster grants reset usage; invalid bond epochs fail earlier; Underscore cadence becomes deployment-bound and reserves capacity before callbacks; Boardroom and Stability-claim mint authorization tighten.

## Catalog

### SOURCE-REACHABLE

- **BD-01 — R1:H-8; R2:H-7; R4:I-03; R5:I-12 — CHANGED economics.** Master ignores sub-1e18 prior shares, normalizes weights, and caps prior duration. rh blends every nonzero prior share exactly without that cap. Who: lock user topping up. Refs: `RipeGov:696-721@91eda49c`; `1013-1040@251ac9e2`.

- **BD-02 — R1:I-8; R4:I-05; R5:I-07 — CHANGED economics.** Master checkpoints Lootbox before committing an adjusted unlock; rh commits first, so the new boost becomes the next accrual basis immediately. Who: lock-adjusting user. Refs: `RipeGov:518-548@91eda49c`; `796-826@251ac9e2`.

- **BD-03 — R1:H-9/I-8; R2:H-4; R3:UC-H-04; R4:I-06; R5:I-05/I-07 — CHANGED economics/failure.** Master burns a share percentage and checkpoints pre-burn while locked. rh targets the floored post-fee claim, requires another holder, and checkpoints post-burn with unlock zero. Who: exiting user and remaining holders. Refs: `RipeGov:551-593@91eda49c`; `829-901@251ac9e2`.

- **BD-04 — R1:H-9; R2:H-4; R4:I-06; R5:I-06 — CHANGED failure policy.** Master treats release as lower-risk housekeeping. rh requires a healthy debt update and applies configured action-slot enforcement. Who: indebted lock user. Refs: `Teller:791-804,985-1009@91eda49c`; `792-803,1004-1035@251ac9e2`.

- **BD-05 — R1:I-1; R2:I-1; R3:UC-I-02; R4:I-09; R5:I-02 — CHANGED outcome.** Master can consume the shared ticket when only one reward category pays. rh commits all attributable categories together or defers everything. Who: deposit-loot claimant. Refs: `Lootbox:405-455@91eda49c`; `422-528@251ac9e2`.

- **BD-06 — R1:I-1; R2:I-1/I-2; R3:UC-I-03; R4:I-09; R5:I-01 — CHANGED economics/failure.** Master quantizes entitlement to basis points and may flush tiny exited positions unpaid. rh uses raw ratios, defers live dust, forces terminal progress, and waits for zero points before cleanup. Who: small depositor. Refs: `Lootbox:428-494,513-547@91eda49c`; `314-322,440-528,592-635@251ac9e2`.

- **BD-07 — R1:I-2; R4:I-08 — CHANGED outcome.** Master consumes borrow rewards but returns before minting when the borrower has no registered vaults. rh continues to mint or stake. Who: borrow-only user. Refs: `Lootbox:277-320@91eda49c`; `287-334@251ac9e2`.

- **BD-08 — R1:I-6; R2:I-2; R4:I-08; R5:I-03 — CHANGED economics.** Master quantizes borrower share to basis points. rh allocates directly from capped raw points. Who: borrowers below 0.01% of global points. Refs: `Lootbox:1012-1037@91eda49c`; `1170-1194@251ac9e2`.

- **BD-09 — R1:I-4; R2:I-4; R4:I-10; R5:I-04 — CHANGED economics.** Master funds general-depositor rewards from full vault custody. rh funds non-RipeGov assets from checkpointed holder-represented underlying, capped and fail-closed; RipeGov still uses custody. Who: general-deposit reward earner. Refs: `Lootbox:785-833@91eda49c`; `859-987@251ac9e2`.

- **BD-10 — R1:Open; R2:I-9; R4:I-13; R5:I-08 — CHANGED failure policy.** Master makes third-party loot claims and bonds write the beneficiary’s last-touch marker. rh instead checks paused/locked state without consuming their slot. Who: claim or bond beneficiary. Refs: `Teller:735-740,814-826,985-997@91eda49c`; `736-741,813-827,1004-1023@251ac9e2`.

- **BD-11 — R1:I-9; R2:I-6; R3:UC-I-05; R4:I-14; R5:I-09 — CHANGED economics.** Master charges fractional payment-token dust that buys no RIPE. rh truncates accounting and transfer to whole units and refunds the remainder. Who: bond buyer. Refs: `BondRoom:156-166,202-232@91eda49c`; `156-166,203-235@251ac9e2`.

- **BD-12 — R1:I-9; R2:I-6; R3:UC-I-06; R4:I-15; R5:I-11 — CHANGED view outcome.** Master calculates preview lock bonus before a booster-enforced minimum lock. rh applies the booster first, matching execution. Who: boosted bond buyer. Refs: `BondRoom:275-325@91eda49c`; `278-334@251ac9e2`.

- **BD-13 — R1:I-10; R2:I-6; R3:UC-H-11; R4:I-14; R5:I-10 — CHANGED failure/API.** rh requires `_paymentAmount` and adds `_minRipePayout`; master permits a one-argument whole-balance call and has no min-out. Who: bond buyer or integrator. Refs: `Teller:812-826@91eda49c`; `811-827@251ac9e2`.

- **BD-14 — R1:H-10; R2:H-8; R3:UC-H-09; R4:H-03; R5:I-13 — CHANGED routing/API.** Master lock operations always target vault ID 2. rh accepts `_vaultId=0` for current core or an explicit classified historical RipeGov ID. Who: historical-vault holder or integrator. Refs: `Teller:775-804@91eda49c`; `777-803,974-986@251ac9e2`.

### CONFIGURATION-CONTINGENT

- **BD-15 — R1:H-1; R2:H-1; R3:UC-H-01; R4:H-01; R5:H-01 — NEW.** Governance can move exact amounts between live non-RipeGov vaults of the same Stability class while Teller is paused. Batch unsupported assets skip; explicit assets revert. Who: migrated depositor or governor. Refs: master A/D absence; `SwitchboardEcho:586-609`, `VaultMigrator:147-233,475-514,607-652`, `Teller:497-508@251ac9e2`.

- **BD-16 — R1:H-2; R2:H-1; R3:UC-H-01; R4:H-02; R5:H-02 — NEW.** Normal RipeGov migration requires Teller, source, and current-core target paused. It preserves amount, accrued points, unlock, and stored terms; target shares are freshly calculated. Who: RipeGov holder or governor. Refs: master A/D absence; `VaultMigrator:242-347,520-582,731-766`, `RipeGov:531-649@251ac9e2`.

- **BD-17 — R1:H-3; R2:H-1; R3:UC-H-01; R4:H-02; R5:H-02 — NEW.** Base-only legacy migration binds deploy-time vault ID 2, requires Teller/target paused and source live, snapshots pending state, ordinarily withdraws, then imports. It neither tombstones nor copies disables. Who: Base legacy holder or governor. Refs: master A/D absence; `VaultMigrator:353-464,658-688`, `Teller:535-547@251ac9e2`.

- **BD-18 — R1:H-4; R2:H-1/H-3; R3:UC-H-02; R4:H-02; R5:H-03 — CHANGED eligibility.** Normal export permanently blocks later deposit and incoming forced transfer for that source `(user,asset)`. Legacy migration does not. Who: normally migrated user or forced-transfer recipient. Refs: `RipeGov:156-179,343-365@91eda49c`; `203,427,531-571,596-612@251ac9e2`.

- **BD-19 — R1:H-12; R2:H-5; R3:UC-H-03; R4:I-01; R5:I-14 — NEW.** Timelocked governance can irreversibly disable accrual globally or per user. Partial exits preserve saved points, full exits clear them, Boardroom callbacks stop, and only per-user disable migrates. Who: targeted/all RipeGov holders. Refs: `RipeGov:268-299,355-365@91eda49c`; `314-352,437-446,484-521,737-752@251ac9e2`.

- **BD-20 — R2:H-3; R3:UC-H-08; R4:I-07; R5:H-04 — CHANGED failure policy.** Master allows lock adjustment, release, and public point refresh while the vault is paused. rh rejects them. Who: lock user or point updater during migration pause. Refs: `RipeGov:461-465,518-557@91eda49c`; `715-727,796-836@251ac9e2`.

- **BD-21 — R1:H-7; R2:H-6; R3:UC-H-05; R4:I-02; R5:I-15 — CHANGED economics.** Master skips multiplication for weight zero, making it behave as 100%. rh applies the multiplier unconditionally, producing zero points. Who: zero-weight asset depositor. Refs: `RipeGov:618-645@91eda49c`; `938-962@251ac9e2`.

- **BD-22 — R1:H-6; R2:H-7; R3:UC-H-06; R4:I-04; R5:I-16 — CHANGED eligibility/outcome.** Master courtesy-unlocks on lost exit, lower boost/minimum, or higher fee and clamps after shorter max. rh unlocks on specified adverse increases/losses and otherwise preserves the original block. Who: user touched after term changes. Refs: `RipeGov:735-771@91eda49c`; `1054-1068@251ac9e2`.

- **BD-23 — R1:H-5; R2:H-3; R3:UC-H-07; R5:I-17 — CHANGED failure policy.** Master accepts a gov deposit with zero maximum lock terms. rh reverts before depositing. Who: RipeGov depositor. Refs: `RipeGov:156-179@91eda49c`; `196-220@251ac9e2`.

- **BD-24 — R1:H-5; R2:H-3; R3:UC-H-07; R5:I-17 — CHANGED failure policy.** Master allows an HR contributor transfer with zero maximum lock terms. rh rejects it. Who: contributor or transfer beneficiary. Refs: `RipeGov:371-395@91eda49c`; `454-475@251ac9e2`.

- **BD-25 — R1:H-10; R2:H-8; R3:UC-H-09; R4:H-03; R5:I-20 — CHANGED routing.** Master `depositIntoGovVault` targets fixed ID 2. rh resolves and requires `coreRipeGovVaultId()`. Who: depositor after core-pointer rotation or misconfiguration. Refs: `Teller:761-772@91eda49c`; `762-774,964-969@251ac9e2`.

- **BD-26 — R1:I-3; R2:H-8/I-5; R4:I-11; R5:I-20 — CHANGED routing/failure.** Master can transfer ordinary loot without a configured core and stakes into ID 2. rh resolves a nonzero core for nonzero claims and stakes there. Who: loot claimant. Refs: `Lootbox:277-320,1128-1158@91eda49c`; `287-334,1289-1318@251ac9e2`.

- **BD-27 — R1:I-9; R2:H-8; R4:I-11; R5:I-20 — CHANGED routing/failure.** Master deposits locked bond payouts into ID 2. rh requires and uses the configured core RipeGov ID. Who: bond buyer choosing a lock. Refs: `BondRoom:219-224@91eda49c`; `220-227@251ac9e2`.

- **BD-28 — R1:I-5; R2:I-4; R4:I-11; R5:I-20 — CHANGED eligibility.** Master skips loot-share normalization only for ID 2. rh skips it for every classified historical RipeGov ID. Who: holder in a rotated historical vault. Refs: `Lootbox:785-818@91eda49c`; `859-913@251ac9e2`.

- **BD-29 — R1:H-11; R2:H-2; R3:UC-H-15; R4:H-05; R5:file observation — CHANGED failure policy.** Master checks vault funds only when update/disable starts. rh checks again at confirmation. Who: governor or depositor funded during the delay. Refs: `VaultBook:97-131@91eda49c`; `105-145@251ac9e2`.

- **BD-30 — same aliases as BD-29 — CHANGED eligibility.** Master’s funds predicate ignores stranded RipeGov points and imposes no replacement points interface. rh counts `totalGovPoints` and probes replacements. Who: governor or holder with stranded points. Refs: `VaultBook:143-147@91eda49c`; `157-180@251ac9e2`.

- **BD-31 — R1:I-7; R2:I-5; R3:UC-I-01; R4:I-12 — CHANGED failure policy.** Master’s department-only per-asset claim bypasses `canClaimLoot`. rh checks it; SwitchboardCharlie provides the keeper route. Who: keeper or beneficiary while claims are disabled. Refs: `Lootbox:364-374@91eda49c`; `Lootbox:380-392`, `SwitchboardCharlie:856-862@251ac9e2`.

- **BD-32 — R1:I-11; R2:I-7; R3:UC-I-04; R4:I-15; R5:I-18 — CHANGED eligibility/economics.** Master carries `unitsUsed` across an expired grant rewrite. rh resets it for absent/expired prior configuration while preserving usage on active replacement. Who: re-granted boosted bonder. Refs: `BondBooster:120-131@91eda49c`; `120-135@251ac9e2`.

- **BD-33 — R1:I-12; R2:I-8; R3/R5:file observation — CHANGED failure policy.** Master can write a zero-length/zero-amount epoch and fail later during refresh or purchase. rh rejects the invalid values at setup/refresh. Who: governor or bond caller. Refs: `BondRoom:360-439@91eda49c`; `369-440@251ac9e2`.

- **BD-34 — R1:I-13; R2:Brief; R3:UC-I-08; R4:I-16; R5:file observation — CHANGED eligibility/API.** Master fixes the minimum Underscore interval at 43,200 blocks. rh chooses a nonzero immutable floor at deployment and exposes it. Who: deployer or interval governor. Refs: `Lootbox:193,196-212,1294-1302@91eda49c`; `199,202-222,1508-1531@251ac9e2`.

- **BD-35 — R1:I-13; R2:UC-I-2; R3:UC-I-07; R4:I-17; R5:referral — CHANGED failure policy.** Master reserves reward capacity after mint and distributor interaction. rh reserves before either, so a reentrant callback cannot consume the same capacity. Who: configured distributor or concurrent claimant. Refs: `Lootbox:1200-1259@91eda49c`; `1422-1478@251ac9e2`.

- **BD-36 — R1:UC-I-4; R3:UC-H-17; R4:I-18; R5:I-19 — CHANGED authorization.** Master’s Boardroom callback succeeds for any caller. rh requires a registered, classified RipeGov vault. Who: misclassified vault or its user. Refs: `Boardroom:27-29@91eda49c`; `33-37@251ac9e2`.

- **BD-37 — R1:I-14; R2:I-3; R3:UC-H-16; R4:I-19; R5:UC-stabClaimMint — CHANGED authorization.** Master lets any registered address use caller-supplied RIPE/Ledger without a local cap. rh requires classified Stability caller, canonical addresses, and remaining reward capacity. Who: noncanonical or misconfigured caller. Refs: `VaultBook:158-163@91eda49c`; `192-208@251ac9e2`.

## Ledger

| id | surface | class | master ref | rh ref | master ≤15w | rh ≤15w | reach | R-aliases | status |
|---|---|---|---|---|---|---|---|---|---|
| BD-01 | H | CHANGED economics | RipeGov:696-721 | RipeGov:1013-1040 | Coarse blend ignores dust and caps duration. | Exact shares; prior duration uncapped. | SOURCE-REACHABLE | R1:H-8; R2:H-7; R4:I-03; R5:I-12 | VERIFIED |
| BD-02 | I | CHANGED economics | RipeGov:518-548 | RipeGov:796-826 | Checkpoint precedes new unlock. | New unlock precedes checkpoint. | SOURCE-REACHABLE | R1:I-8; R4:I-05; R5:I-07 | VERIFIED |
| BD-03 | I | CHANGED economics/failure | RipeGov:551-593 | RipeGov:829-901 | Share-percent burn; pre-burn locked checkpoint. | Claim-target burn; holder required; post-burn unlocked checkpoint. | SOURCE-REACHABLE | R1:H-9/I-8; R2:H-4; R3:UC-H-04; R4:I-06; R5:I-05/I-07 | VERIFIED |
| BD-04 | I | CHANGED failure | Teller:791-804,985-1009 | Teller:792-803,1004-1035 | Release is lower-risk housekeeping. | Release requires healthy higher-risk housekeeping. | SOURCE-REACHABLE | R1:H-9; R2:H-4; R4:I-06; R5:I-06 | VERIFIED |
| BD-05 | I | CHANGED outcome | Lootbox:405-455 | Lootbox:422-528 | One paying bucket can consume ticket. | All attributable buckets settle together or defer. | SOURCE-REACHABLE | R1:I-1; R2:I-1; R3:UC-I-02; R4:I-09; R5:I-02 | VERIFIED |
| BD-06 | I | CHANGED economics/failure | Lootbox:428-494,513-547 | Lootbox:314-322,440-528,592-635 | Basis-point dust may flush unpaid. | Raw ratios; live dust waits; terminal dust progresses. | SOURCE-REACHABLE | R1:I-1; R2:I-1/I-2; R3:UC-I-03; R4:I-09; R5:I-01 | VERIFIED |
| BD-07 | I | CHANGED outcome | Lootbox:277-320 | Lootbox:287-334 | Borrow-only rewards consumed but not minted. | Borrow-only rewards reach mint. | SOURCE-REACHABLE | R1:I-2; R4:I-08 | VERIFIED |
| BD-08 | I | CHANGED economics | Lootbox:1012-1037 | Lootbox:1170-1194 | Borrow share quantized to basis points. | Borrow share uses full-precision points. | SOURCE-REACHABLE | R1:I-6; R2:I-2; R4:I-08; R5:I-03 | VERIFIED |
| BD-09 | I | CHANGED economics | Lootbox:785-833 | Lootbox:859-987 | General rewards use total custody. | Non-gov rewards use holder-represented underlying. | SOURCE-REACHABLE | R1:I-4; R2:I-4; R4:I-10; R5:I-04 | VERIFIED |
| BD-10 | I | CHANGED failure | Teller:735-740,814-826,985-997 | Teller:736-741,813-827,1004-1023 | Third-party benefit writes beneficiary last-touch. | Beneficiary checked without writing last-touch. | SOURCE-REACHABLE | R1:Open; R2:I-9; R4:I-13; R5:I-08 | VERIFIED |
| BD-11 | I | CHANGED economics | BondRoom:156-166,202-232 | BondRoom:156-166,203-235 | Fractional payment charged without payout. | Fractional payment refunded. | SOURCE-REACHABLE | R1:I-9; R2:I-6; R3:UC-I-05; R4:I-14; R5:I-09 | VERIFIED |
| BD-12 | I | CHANGED view | BondRoom:275-325 | BondRoom:278-334 | Preview applies lock bonus before booster. | Preview applies booster before lock bonus. | SOURCE-REACHABLE | R1:I-9; R2:I-6; R3:UC-I-06; R4:I-15; R5:I-11 | VERIFIED |
| BD-13 | I | CHANGED failure/API | Teller:812-826 | Teller:811-827 | Payment may default to whole balance. | Payment required; minimum payout supported. | SOURCE-REACHABLE | R1:I-10; R2:I-6; R3:UC-H-11; R4:I-14; R5:I-10 | VERIFIED |
| BD-14 | H | CHANGED routing/API | Teller:775-804 | Teller:777-803,974-986 | Lock actions always use vault ID 2. | Caller may select historical RipeGov ID. | SOURCE-REACHABLE | R1:H-10; R2:H-8; R3:UC-H-09; R4:H-03; R5:I-13 | VERIFIED |
| BD-15 | H | NEW | A/D VaultMigrator | VaultMigrator:147-233,475-514 | No canonical generic migration. | Governor moves exact amounts between eligible vaults. | CONFIGURATION-CONTINGENT | R1:H-1; R2:H-1; R3:UC-H-01; R4:H-01; R5:H-01 | VERIFIED |
| BD-16 | H | NEW | A/D VaultMigrator | VaultMigrator:242-347,520-582,731-766 | No RipeGov transplant. | Amount and gov state move; shares reminted. | CONFIGURATION-CONTINGENT | R1:H-2; R2:H-1; R3:UC-H-01; R4:H-02; R5:H-02 | VERIFIED |
| BD-17 | H | NEW | A/D VaultMigrator | VaultMigrator:353-464,658-688 | No legacy migration route. | Base ID-2 snapshot, ordinary withdrawal, import. | CONFIGURATION-CONTINGENT | R1:H-3; R2:H-1; R3:UC-H-01; R4:H-02; R5:H-02 | VERIFIED |
| BD-18 | H | CHANGED eligibility | RipeGov:156-179,343-365 | RipeGov:203,427,531-571,596-612 | Emptied position may re-enter. | Normal-exported position is permanently tombstoned. | CONFIGURATION-CONTINGENT | R1:H-4; R2:H-1/H-3; R3:UC-H-02; R4:H-02; R5:H-03 | VERIFIED |
| BD-19 | I | NEW | RipeGov:268-299,355-365 | RipeGov:314-352,437-446,484-521 | Accrual always updates on touch. | Governor can irreversibly stop global/user accrual. | CONFIGURATION-CONTINGENT | R1:H-12; R2:H-5; R3:UC-H-03; R4:I-01; R5:I-14 | VERIFIED |
| BD-20 | H | CHANGED failure | RipeGov:461-465,518-557 | RipeGov:715-727,796-836 | Pause does not block lock maintenance. | Paused vault blocks lock maintenance and refresh. | CONFIGURATION-CONTINGENT | R2:H-3; R3:UC-H-08; R4:I-07; R5:H-04 | VERIFIED |
| BD-21 | I | CHANGED economics | RipeGov:618-645 | RipeGov:938-962 | Weight zero behaves as 100%. | Weight zero earns zero points. | CONFIGURATION-CONTINGENT | R1:H-7; R2:H-6; R3:UC-H-05; R4:I-02; R5:I-15 | VERIFIED |
| BD-22 | H | CHANGED eligibility | RipeGov:735-771 | RipeGov:1054-1068 | Old comparisons zero and down-clamp unlock. | Adverse comparisons zero; otherwise unlock persists. | CONFIGURATION-CONTINGENT | R1:H-6; R2:H-7; R3:UC-H-06; R4:I-04; R5:I-16 | VERIFIED |
| BD-23 | H | CHANGED failure | RipeGov:156-179 | RipeGov:196-220 | Deposit accepts missing lock terms. | Deposit rejects missing lock terms. | CONFIGURATION-CONTINGENT | R1:H-5; R2:H-3; R3:UC-H-07; R5:I-17 | VERIFIED |
| BD-24 | H | CHANGED failure | RipeGov:371-395 | RipeGov:454-475 | Contributor transfer accepts missing terms. | Contributor transfer rejects missing terms. | CONFIGURATION-CONTINGENT | R1:H-5; R2:H-3; R3:UC-H-07; R5:I-17 | VERIFIED |
| BD-25 | H | CHANGED routing | Teller:761-772 | Teller:762-774,964-969 | Gov deposit targets ID 2. | Gov deposit targets configured core. | CONFIGURATION-CONTINGENT | R1:H-10; R2:H-8; R3:UC-H-09; R4:H-03; R5:I-20 | VERIFIED |
| BD-26 | I | CHANGED routing/failure | Lootbox:277-320,1128-1158 | Lootbox:287-334,1289-1318 | Claims need no core; stakes use ID 2. | Claims resolve core; stakes use it. | CONFIGURATION-CONTINGENT | R1:I-3; R2:H-8/I-5; R4:I-11; R5:I-20 | VERIFIED |
| BD-27 | I | CHANGED routing/failure | BondRoom:219-224 | BondRoom:220-227 | Locked bond uses ID 2. | Locked bond requires configured core. | CONFIGURATION-CONTINGENT | R1:I-9; R2:H-8; R4:I-11; R5:I-20 | VERIFIED |
| BD-28 | I | CHANGED eligibility | Lootbox:785-818 | Lootbox:859-913 | Only ID 2 skips normalization. | Every classified RipeGov ID skips normalization. | CONFIGURATION-CONTINGENT | R1:I-5; R2:I-4; R4:I-11; R5:I-20 | VERIFIED |
| BD-29 | H | CHANGED failure | VaultBook:97-131 | VaultBook:105-145 | Funds checked only at initiation. | Funds rechecked at confirmation. | CONFIGURATION-CONTINGENT | R1:H-11; R2:H-2; R3:UC-H-15; R4:H-05; R5:file | VERIFIED |
| BD-30 | H | CHANGED eligibility | VaultBook:143-147 | VaultBook:157-180 | Funds ignore points; replacement unprobed. | Points count; replacement exposes totalGovPoints. | CONFIGURATION-CONTINGENT | same as BD-29 | VERIFIED |
| BD-31 | I | CHANGED failure | Lootbox:364-374 | Lootbox:380-392; Charlie:856-862 | Per-asset helper bypasses claim-disable. | Keeper route respects claim-disable. | CONFIGURATION-CONTINGENT | R1:I-7; R2:I-5; R3:UC-I-01; R4:I-12 | VERIFIED |
| BD-32 | I | CHANGED eligibility/economics | BondBooster:120-131 | BondBooster:120-135 | Expired grant retains used units. | Expired grant resets used units. | CONFIGURATION-CONTINGENT | R1:I-11; R2:I-7; R3:UC-I-04; R4:I-15; R5:I-18 | VERIFIED |
| BD-33 | I | CHANGED failure | BondRoom:360-439 | BondRoom:369-440 | Invalid epoch may be written then fail later. | Invalid epoch rejected immediately. | CONFIGURATION-CONTINGENT | R1:I-12; R2:I-8; R3/R5:file | VERIFIED |
| BD-34 | I | CHANGED eligibility/API | Lootbox:193,196-212,1294-1302 | Lootbox:199,202-222,1508-1531 | Minimum interval fixed at 43,200. | Deployment chooses immutable nonzero floor. | CONFIGURATION-CONTINGENT | R1:I-13; R2:Brief; R3:UC-I-08; R4:I-16; R5:file | VERIFIED |
| BD-35 | I | CHANGED failure | Lootbox:1200-1259 | Lootbox:1422-1478 | Capacity reserved after external interaction. | Capacity reserved before mint and callbacks. | CONFIGURATION-CONTINGENT | R1:I-13; R2:UC-I-2; R3:UC-I-07; R4:I-17; R5:referral | VERIFIED |
| BD-36 | I | CHANGED authorization | Boardroom:27-29 | Boardroom:33-37 | Any caller reaches no-op. | Only classified RipeGov vault succeeds. | CONFIGURATION-CONTINGENT | R1:UC-I-4; R3:UC-H-17; R4:I-18; R5:I-19 | VERIFIED |
| BD-37 | I | CHANGED authorization | VaultBook:158-163 | VaultBook:192-208 | Any registered caller; supplied addresses; uncapped. | Stability-only, canonical addresses, rewards-capped. | CONFIGURATION-CONTINGENT | R1:I-14; R2:I-3; R3:UC-H-16; R4:I-19; R5:UC-stab | VERIFIED |
| BD-38 | I | CHANGED failure | Lootbox:984-993 | Lootbox:1138-1149 | Direct borrow helper bypasses claim-disable. | Direct borrow helper respects claim-disable. | ROUTE NOT PROVEN | R1:I-7; R2:I-5; R3:UC-I-01; R4:Open | VERIFIED |
| UC-01 | H | UNCHANGED | SimpleErc20:8-9,40-150 | SimpleErc20:8-9,39-149 | Host deposit/withdraw/transfer/getters unchanged. | Host deposit/withdraw/transfer/getters unchanged. | SOURCE-REACHABLE | R1:UC-H-1; R2:UC-H-1; R3/R4/R5:Files | VERIFIED |
| UC-02 | H | UNCHANGED | RebaseErc20:8-10,44-158 | RebaseErc20:8-10,43-157 | Host declarations and bodies unchanged. | Host declarations and bodies unchanged. | SOURCE-REACHABLE | R1:UC-H-2; R2:UC-H-1; R3/R4/R5:Files | VERIFIED |
| UC-03 | I | UNCHANGED | RipeGov:412-422,651-676 | RipeGov:665-676,968-993 | Loot share and standalone bonus formulas unchanged. | Loot share and standalone bonus formulas unchanged. | SOURCE-REACHABLE | R1:UC-H-3; R4:UC-I-02 | VERIFIED |
| UC-04 | I | UNCHANGED API | Teller:733-753 | Teller:734-754 | Claim names and declarations unchanged. | Claim names and declarations unchanged. | SOURCE-REACHABLE | R1:UC-I-1; R5:UC-claimLoot | VERIFIED |
| UC-05 | I | UNCHANGED API/outcome | Lootbox:500-547 | Lootbox:574-635 | External calc uses basis-point-facing rule. | Wrapper preserves basis-point-facing rule. | SOURCE-REACHABLE | R1/R2/R4/R5:API | VERIFIED |
| UC-06 | I | UNCHANGED | Lootbox:1087-1120 | Lootbox:1244-1277 | Global reward drip math unchanged. | Global reward drip math unchanged. | SOURCE-REACHABLE | R1:UC-I-2; R2:UC-I-1 | VERIFIED |
| UC-07 | I | UNCHANGED | BondRoom:137-151,172-200 | BondRoom:137-151,173-201 | Whitelist, window, canBond, purchase booster unchanged. | Same rules remain. | SOURCE-REACHABLE | R1:UC-I-3 | VERIFIED |
| UC-08 | I | UNCHANGED canonical outcome | Boardroom:28-29 | Boardroom:34-37 | Valid RipeGov callback stores nothing. | Valid classified callback stores nothing. | CONFIGURATION-CONTINGENT | R1:UC-I-4 | VERIFIED |
| UC-09 | I | UNCHANGED canonical outcome | StabVault:735-756 | StabVault:881-905 | Canonical caller already caps and passes canonical addresses. | Canonical caller still does so. | SOURCE-REACHABLE | R5:UC-stabClaimMint | VERIFIED |

All refs above use `@91eda49c` for the master column and `@251ac9e2` for the rh column.

## Files

| FOCUS path | final | ids | note |
|---|---|---|---|
| `contracts/core/VaultMigrator.vy` | CONFIRMED | BD-15–BD-17 | Added on rh; governance-only migration implementation. |
| `contracts/core/Lootbox.vy` | CONFIRMED | BD-05–BD-09, BD-26, BD-28, BD-31, BD-34, BD-35, BD-38; UC-05–UC-06 | Direct borrow-helper route remains unproven. |
| `contracts/core/BondRoom.vy` | CONFIRMED | BD-11, BD-12, BD-27, BD-33; UC-07 | Runtime API names unchanged. |
| `contracts/core/Boardroom.vy` | CONFIRMED | BD-36; UC-08 | Valid-caller outcome unchanged; authorization differs. |
| `contracts/config/BondBooster.vy` | CONFIRMED | BD-32 | Expired/absent grant reset verified. |
| `contracts/vaults/RipeGov.vy` | CONFIRMED | BD-01–BD-03, BD-16, BD-18–BD-24; UC-03 | Direct Lane 3A behavior confirmed; SharesVault internals referred. |
| `contracts/vaults/SimpleErc20.vy` | CONFIRMED | UC-01 | Same host-owned outcome; shared BasicVault behavior referred. |
| `contracts/vaults/RebaseErc20.vy` | PARTIAL | UC-02 | Host body verified; exported SharesVault signatures checked, module semantics remain Lane 2. |
| `contracts/registries/VaultBook.vy` | CONFIRMED | BD-29, BD-30, BD-37 | Canonical Stability payout remains UC-09. |

Shared Teller slice: **PARTIAL**, limited to migration functions, `depositIntoGovVault`, `adjustLock`, `releaseLock`, `claimLoot*`, and `purchaseRipeBond` (BD-04, BD-10, BD-13–BD-17, BD-25).

## API

### Added

- New `VaultMigrator` deployment:
  - `__init__(_ripeHq: address, _shouldPause: bool, _legacyRipeGovVault: address)`
  - `migrateVaultPositions(...) -> uint256`
  - `migrateVaultPositionsForUserByAssets(...) -> uint256`
  - `migrateRipeGovPositions(...) -> uint256`
  - `migrateRipeGovPositionsForUserByAssets(...) -> uint256`
  - `migrateLegacyRipeGovPositions(...) -> uint256`

- Teller migration surface:
  - `withdrawOnVaultMigration(...) -> (uint256, bool)`
  - `depositOnVaultMigration(...) -> uint256`
  - `exportPositionForMigration(...) -> RipeGovMigrationData`
  - `importPositionForMigration(...) -> uint256`
  - `exportPositionForLegacyRipeGovMigration(...) -> uint256`

- RipeGov:
  - `disableGovPointAccrualGlobally()`
  - `disableGovPointAccrualForUser(address)`
  - `inheritUserGovPointAccrualDisableForMigration(address,uint256) -> bool`
  - `exportPositionForMigration(...) -> RipeGovMigrationData`
  - `importPositionForMigration(...) -> uint256`
  - `govPointAccrualDisabledBlock() -> uint256`
  - `userGovPointAccrualDisabledBlock(address) -> uint256`
  - `positionMigratedOut(address,address) -> bool`

- Lootbox:
  - `minUnderscoreSendInterval() -> uint256`

### Removed

- `RipeGov.areKeyTermsSame(cs.LockTerms,cs.LockTerms) -> bool`

### Signature-changed

- `Teller.adjustLock` appends `_vaultId: uint256 = 0`.
  - Generated arities: `2,3` → `2,3,4`.

- `Teller.releaseLock` appends `_vaultId: uint256 = 0`.
  - Generated arities: `1,2` → `1,2,3`.

- `Teller.purchaseRipeBond` makes `_paymentAmount` required and appends `_minRipePayout: uint256 = 0`.
  - Generated arities: `1,2,3,4` → `2,3,4,5`.

- Lootbox constructor inserts `_minUnderscoreSendInterval` as the second argument.

The arity consequences are inferred from Vyper default arguments; no compiler was run.

### Unchanged reconstructed surfaces

- No direct name or full-declaration change in BondRoom, Boardroom, BondBooster, VaultBook, SimpleErc20, or RebaseErc20.
- SharesVault exports on RipeGov/Rebase retain:
  - `amountToShares(address,uint256,bool) -> uint256`
  - `sharesToAmount(address,uint256,bool) -> uint256`
- Teller `depositIntoGovVault`, `claimLoot`, and `claimLootForManyUsers` declarations remain unchanged.

## Dropped / Open / referrals / SYNTH-CHECK

### Dropped

- **R3 Teller removals and unrelated API:** `redeemCollateral`, `buyFungibleAuction`, Stability convenience functions, `deleverageUser`, `setUserConfig`, preferred Stability routing, custody measurement, and deleverage annotations are outside the permitted Teller slice.
- **R4 SharesVault `_mulDiv` behavior:** module semantics are Lane 2. Only the exported names/signatures on RipeGov and Rebase were retained here.
- **R5 third-party deposit last-touch facet:** outside the named Teller slice; only loot and bond facets remain in BD-10.
- **“RipeGov shares are preserved”:** source disproves this. Amount and gov metadata are preserved; target shares are recalculated.
- **Legacy tombstone/disable inheritance:** source disproves both. Legacy uses ordinary withdrawal.
- **“All RipeGov deposits changed from any Ripe caller”:** `depositTokensInVault` was already Teller-only. Repository source shows Teller as the sole caller of the narrowed lock-duration/lock-operation functions on both pins.
- **SOURCE-REACHABLE labels for migration, point-disable, and VaultBook governance:** dropped in favor of CONFIGURATION-CONTINGENT.
- **“Zero epoch assertions are same-outcome”:** dropped. Master can accept/write invalid setup before later failure; rh rejects earlier.
- **VaultBook empty-slot helper:** changed internally, but the registry still rejects the invalid update/disable; no distinct product outcome was retained.

### Open

- **BD-38:** direct `Lootbox.claimBorrowLoot` now checks `canClaimLoot`, but no in-repository caller route was found.
- R2’s inconsistent-state subclaim—raw user points above asset totals can revert rather than cap—is source-implied, but no path creating that state was proven.

### Referrals

- SharesVault, BasicVault, StabVault, and other shared-module semantics → Lane 2.
- Teller ordinary deposit/withdraw/debt/liquidation/Stability changes → Lane 2 or Lane 3B.
- Live MissionControl classification and deployed core-vault identity → governance/configuration evidence, not this source lane.

### SYNTH-CHECK

The new VaultMigrator exports `addys.__interface__` and `deptBasics.__interface__`. Drafts mentioned these generically but did not name eight generated/exported members, so they are API + Open only—not Brief:

- `getAddys() -> Addys`
- `getRipeHq() -> address`
- `isPaused() -> bool`
- `canMintGreen() -> bool`
- `canMintRipe() -> bool`
- `pause(bool)`
- `recoverFunds(address,address)`
- `recoverFundsMany(address,DynArray[address,20])`

No other unreported API names were found.

**LANE SYNTHESIS COMPLETE — Lane 3A — 91eda49c vs 251ac9e2**
