# PR #67 lane synthesis — Lane 3C

Draft only. Not a source of truth. If this file and the contracts disagree,
the contracts win.

- master: 91eda49ccd34a25090582aff0695075c4c806011
- rh:     251ac9e228a8af80326e8fe30f607511c78fe820
- date:   2026-08-22

# PR #67 behavior delta — Lane 3C — 91eda49c vs 251ac9e2

Pins verified locally:

- master tree `fbd958bec234081f70769045abd8f9bb638f6dd7`
- rh tree `204de8657d9cd2eded1212028b9b5ba8d87b6506`

All five write-ups use the correct lane and pins. All Ledger rows below are VERIFIED; none remain UNRESOLVED or UNCHECKED.

## Brief

SOURCE-REACHABLE

- **BD-01–BD-06:** Zero-value `approve`/`permit` and every `decreaseAllowance` can bypass pause/blacklist restrictions. sGREEN separately gains blacklisted-holder and backed-final-share burn guards; governance separately loses the ability to burn GREEN held by SavingsGreen or the final backed sGREEN supply.
- **BD-07–BD-10:** ERC-4626 maximum views become state- and owner-aware. sGREEN `redeem`/`withdraw` newly reject an sGREEN pause, a blacklisted owner, or a blacklisted delegated spender. GREEN-side transfer restrictions already existed.
- **BD-11–BD-12:** New-HQ validation now requires `savingsGreen()`. GREEN, RIPE, and sGREEN add `getCCIPAdmin()`, returning current HQ governance.
- **BD-13, BD-29–BD-30:** Dust-priced USDC capacity below `10^12` GREEN wei becomes zero. The switchboard’s mint-cap ceiling tightens, and extreme interval durations no longer make interval views/actions overflow.
- **BD-14–BD-20:** Stabilization now targets normalized `altBalance` versus GREEN, sizes removals against owned LP, rejects worsening deficits, soft-fails when CurvePrices is absent, and reports zero profit for an empty pool or zero LP.
- **BD-21–BD-27:** Partner liquidity gets a seven-argument ABI, expected-LP validation, per-action LP splitting, actual-receipt valuation, a GREEN partner-asset prohibition, custody/report reconciliation, and partial-fill cleanup that burns unused provisional GREEN and records only actual debt.
- **BD-28:** Ten Endaoment operator entry points gain the shared nonreentrant lock; ordinary authorized behavior remains unchanged.

CONFIGURATION-CONTINGENT

- **BD-31:** sGREEN deployment now requires zero initial shares.
- **BD-32–BD-34:** PSM construction now requires six-decimal USDC, rejects `numBlocksPerInterval == uint256.max`, and applies the safe mint-cap ceiling.
- **BD-35:** Dedicated GREEN-only and RIPE-only capability-response CCIP wrappers are added. Their constructors do not enforce token identity; correct token binding, Router/ramp/remote configuration, rate limits, and HQ authorization remain required.

## Catalog

- **BD-01 — VERIFIED / CHANGED eligibility / SOURCE-REACHABLE.** R-aliases: R1 `K-ERC20-REVOKE`; R2 `K-1`; R3 `UC-K-03`; R4 `K-01`; R5 `K-01`. Master always applies pause and owner/spender blacklist checks to `approve` and `permit`; rh applies only nonzero-spender validation when value is zero. Holders and permit integrators notice. Refs: `Erc20Token.vy:226-230,347-356@91eda49c`; `:227-234,379-391@251ac9e2`.

- **BD-02 — VERIFIED / CHANGED eligibility / SOURCE-REACHABLE.** R-aliases: R1 `K-ERC20-REVOKE`; R2 `K-1`; R3 `UC-K-03`; R4 `K-01`; R5 `K-02`. Master fully validates every allowance decrease; rh requires only a nonzero spender for every decrease, regardless of amount. Holders reducing allowances notice. Refs: `Erc20Token.vy:261-268@91eda49c`; `:265-272@251ac9e2`.

- **BD-03 — VERIFIED / CHANGED failure policy / SOURCE-REACHABLE.** R-aliases: R1 `K-ERC20-VAULT-BURN`; R2 `K-2`; R3 `UC-K-01`; R4 `K-03`; R5 `K-03`. Master lets an unpaused blacklisted sGREEN holder burn; rh blocks a blacklisted caller when the token exposes an underlying asset. Blacklisted sGREEN holders notice. Refs: `Erc20Token.vy:306-309@91eda49c`; `:316-336@251ac9e2`.

- **BD-04 — VERIFIED / CHANGED failure policy / SOURCE-REACHABLE.** Same aliases as BD-03. Master permits the holder of all sGREEN shares to burn them while GREEN remains; rh rejects a full-supply burn that would strand underlying assets. The sole sGREEN holder notices. Refs: `Erc20Token.vy:306-317@91eda49c`; `:337-349@251ac9e2`.

- **BD-05 — VERIFIED / CHANGED eligibility / SOURCE-REACHABLE.** R-aliases: R1 `K-ERC20-VAULT-BURN`; R2 `K-3`; R3 `UC-K-02`; R4 `K-03`; R5 `K-04`. Master lets governance burn blacklisted GREEN held by SavingsGreen; rh expressly forbids that target. Governance and sGREEN holders notice. Refs: `Erc20Token.vy:414-422@91eda49c`; `:450-457@251ac9e2`.

- **BD-06 — VERIFIED / CHANGED eligibility / SOURCE-REACHABLE.** Same aliases as BD-05. Master lets governance burn an asset-bearing token’s entire blacklisted supply while underlying remains; rh rejects that final backed burn. Governance and remaining vault claimants notice. Refs: `Erc20Token.vy:414-422@91eda49c`; `:458-462@251ac9e2`.

- **BD-07 — VERIFIED / CHANGED outcome / SOURCE-REACHABLE.** R-aliases: R1 `K-ERC4626-CAPS`; R2 `K-5`; R3 `UC-K-05`; R4 `K-04`; R5 `K-06`. Master `maxDeposit`/`maxMint` always return `uint256.max`; rh returns zero for an invalid/blacklisted receiver, sGREEN pause, GREEN blocking the vault, or zero backing with nonzero supply. Deposit/mint apps notice. Refs: `Erc4626Token.vy:54-57,83-86@91eda49c`; `:58-63,89-94,323-332@251ac9e2`.

- **BD-08 — VERIFIED / CHANGED outcome / SOURCE-REACHABLE.** Same aliases as BD-07. Master `maxWithdraw` returns the vault’s entire GREEN balance; rh returns zero under blocking states, otherwise the owner’s shares converted to GREEN. Owners and ERC-4626 apps notice. Refs: `Erc4626Token.vy:127-130@91eda49c`; `:135-140,323-332@251ac9e2`.

- **BD-09 — VERIFIED / CHANGED outcome / SOURCE-REACHABLE.** Same aliases as BD-07. Master `maxRedeem` returns owner shares without state checks; rh returns zero under sGREEN pause, owner blacklist, GREEN blocking, or zero backing. Owners and ERC-4626 apps notice. Refs: `Erc4626Token.vy:150-153@91eda49c`; `:160-165,323-332@251ac9e2`.

- **BD-10 — VERIFIED / CHANGED failure policy / SOURCE-REACHABLE.** R-aliases: R1 `K-ERC4626-EXIT`; R2 `K-4`; R3 `UC-K-06`; R4 `K-02`; R5 `K-05`. Master redemption checks amounts, recipient, balance, and allowance; rh additionally rejects sGREEN pause, blacklisted owner, and blacklisted delegated sender. sGREEN owners/operators notice. Refs: `Erc4626Token.vy:177-202@91eda49c`; `:189-217@251ac9e2`.

- **BD-11 — VERIFIED / CHANGED eligibility / SOURCE-REACHABLE.** R-aliases: R1 `K-ERC20-HQ-SGREEN`; R2 `K-14`; R3 file note; R4 referral; R5 `K-15`. Master new-HQ validation requires GREEN and RIPE addresses; rh also requires SavingsGreen. Validation callers and governance notice. Refs: `Erc20Token.vy:503-526@91eda49c`; `:543-566@251ac9e2`.

- **BD-12 — VERIFIED / NEW / SOURCE-REACHABLE.** R-aliases: R1 `K-ERC20-GETCCIPADMIN`; R2 `K-6`; R3 `UC-K-14`; R4 `K-06`; R5 `K-07`. Master lacks the name; rh adds `getCCIPAdmin() -> address`, returning HQ governance through all three token exports. Direct API callers notice. Refs: `D Erc20Token.getCCIPAdmin@91eda49c`; `Erc20Token.vy:674-677@251ac9e2`.

- **BD-13 — VERIFIED / CHANGED economics / SOURCE-REACHABLE.** R-aliases: R1 `K-PSM-REDEEM-DUST`; R2 `K-7`; R3 `UC-K-11`; R4 `K-08`; R5 `K-11`. Master preserves any nonzero priced USDC capacity; rh zeroes values below one USDC base unit at 1:1. PSM users and max-view callers notice. Refs: `EndaomentPSM.vy:450-476,484-495@91eda49c`; `:464-493,501-512@251ac9e2`.

- **BD-14 — VERIFIED / CHANGED economics / SOURCE-REACHABLE.** R-aliases: R1 `K-ENDAO-STAB`; R2 `K-11`; R3 `UC-K-09`; R4 `K-11`; R5 `K-09`. Master skips zero-GREEN pools and targets `greenRatio` versus 50%; rh compares normalized `altBalance` directly with GREEN and adjusts their weighted difference. Keeper and amount-view callers notice. Refs: `Endaoment.vy:743-769,819-854,891-910@91eda49c`; `:785-815,873-902,943-962@251ac9e2`.

- **BD-15 — VERIFIED / CHANGED outcome / SOURCE-REACHABLE.** R-aliases: R1 `K-ENDAO-STAB`; R2 `K-11`; R3 `UC-K-09`; R4 `K-12`; R5 `K-09`. Master executes removal with an unlimited LP maximum; rh validates pool/index/LP, quotes cost, binary-searches the largest affordable amount, and passes `lpQuote + 1`. Keeper and removal-view callers notice. Refs: `Endaoment.vy:861-922@91eda49c`; `:909-1002@251ac9e2`.

- **BD-16 — VERIFIED / CHANGED failure policy / SOURCE-REACHABLE.** R-aliases: R1 `K-ENDAO-STAB`; R2 `K-11`; R3 `UC-K-09`; R4 `K-13`; R5 `K-09`. Master clamps deep deficits to zero, allowing a worsening `0 >= 0`; rh preserves deficit magnitude and rejects a larger deficit. The keeper notices. Refs: `Endaoment.vy:758-776,943-967@91eda49c`; `:802-830,1033-1048@251ac9e2`.

- **BD-17 — VERIFIED / CHANGED failure policy / SOURCE-REACHABLE.** R-alias: R4 `K-14`. With no CurvePrices registry address, master’s keeper action hard-calls the empty address and reverts; rh’s helper returns an empty config and the action returns false. Refs: `Endaoment.vy:749-752@91eda49c`; `:791-793,1008-1014@251ac9e2`.

- **BD-18 — VERIFIED / CHANGED failure policy / SOURCE-REACHABLE.** R-aliases: R4 `K-14`; R5 `K-10`. With no CurvePrices registry address, master’s three stabilizer views can revert; rh returns zero. Monitoring and amount-view callers notice. Refs: `Endaoment.vy:848-854,916-938@91eda49c`; `:896-902,996-1028@251ac9e2`.

- **BD-19 — VERIFIED / CHANGED failure policy / SOURCE-REACHABLE.** R-aliases: R4 `K-14`; R5 `K-10`. If CurvePrices exists but returns an empty pool, master already soft-fails action and amount views, but `calcProfitForStabilizer` can revert; rh returns zero. Profit-view callers notice. Refs: `Endaoment.vy:930-938@91eda49c`; `:1019-1028@251ac9e2`.

- **BD-20 — VERIFIED / CHANGED outcome / SOURCE-REACHABLE.** R-alias: R4 `K-14`. With a valid pool but zero LP, master can report positive leftover-GREEN profit; rh explicitly reports zero. Profit-view callers notice. Refs: `Endaoment.vy:943-967@91eda49c`; `:1053-1066@251ac9e2`.

- **BD-21 — VERIFIED / CHANGED signature / SOURCE-REACHABLE.** R-aliases: R1 `K-ENDAO-PARTNER`; R2 `K-9`; R3 `UC-K-08`; R4 `K-15`; R5 `K-08`. Master exposes 4/5/6-argument default-generated `addPartnerLiquidity` selectors; rh exposes one required seven-argument selector. ABI callers notice. Refs: `Endaoment.vy:988-996@91eda49c`; `:1088-1098@251ac9e2`.

- **BD-22 — VERIFIED / CHANGED eligibility / SOURCE-REACHABLE.** Same aliases as BD-21. Master has no expected-LP input or identity policy; rh requires a nonzero expected token and requires the lego’s returned LP token to match. Switchboard operators notice. Refs: `Endaoment.vy:988-1014@91eda49c`; `:1090-1121@251ac9e2`.

- **BD-23 — VERIFIED / CHANGED economics / SOURCE-REACHABLE.** Same aliases as BD-21. Master pulls and splits the entire custody balance of the returned LP token; rh verifies and splits only this action’s received LP, and the event field follows that amount. Partner, treasury, and event consumers notice. Refs: `Endaoment.vy:1016-1035@91eda49c`; `:1113-1124,1153-1169@251ac9e2`.

- **BD-24 — VERIFIED / CHANGED economics / SOURCE-REACHABLE.** R-aliases: R1 `K-ENDAO-PARTNER`; R2 `K-10`; R4 `K-16`; R5 `K-08`. Master values the nominal minimum of request and partner balance; for an external partner, rh values the positive EndaomentFunds receipt delta. Fee-on-transfer partners/operators notice. Refs: `Endaoment.vy:1051-1058@91eda49c`; `:1192-1203@251ac9e2`.

- **BD-25 — VERIFIED / CHANGED eligibility / SOURCE-REACHABLE.** Same aliases as BD-24. Master permits GREEN as the partner asset; rh rejects it. Partners and operators notice. Refs: `Endaoment.vy:1043-1058@91eda49c`; `:1183-1193@251ac9e2`.

- **BD-26 — VERIFIED / CHANGED failure policy / SOURCE-REACHABLE.** R-aliases: R2 `K-9`; R4 `K-16`; R5 `K-08`. Master trusts the lego’s reported contributions; rh requires bounded partner/GREEN reports to match combined-custody decreases. Operators notice mismatches, fees, or unrelated top-ups. Refs: `Endaoment.vy:1008-1014@91eda49c`; `:1126-1133@251ac9e2`.

- **BD-27 — VERIFIED / CHANGED economics / SOURCE-REACHABLE.** R-aliases: R1 `K-ENDAO-PARTNER`; R2 `K-9`; R3 `UC-K-08`; R4 `K-16`; R5 `K-08`. Master retains and books every provisional GREEN mint; rh burns the unused portion and records/events only actual GREEN contribution and final minted debt. Accounting consumers notice. Refs: `Endaoment.vy:1002-1035@91eda49c`; `:1135-1151,1165-1169@251ac9e2`.

- **BD-28 — VERIFIED / CHANGED failure policy / SOURCE-REACHABLE.** R-aliases: R2 `K-13`; R4 `K-10`; R5 `K-13`; R1/R3 file notes. Master leaves ten listed operator entries outside the shared lock; rh makes them nonreentrant. Reentrant callbacks notice; ordinary calls do not. Refs: `DeptBasics.vy:63-84`, `Endaoment.vy:176,204,245,742,975,988,1074@91eda49c`; `Endaoment.vy:172-190,213-215,242-244,284-286,783-785,1074-1090,1219-1221@251ac9e2`.

- **BD-29 — VERIFIED / CHANGED eligibility / SOURCE-REACHABLE.** R-aliases: R1 `K-PSM-CTOR`; R2 `K-8`; R3 `UC-K-13`; R4 `K-07`; R5 `K-12`. Master’s setter accepts any nonzero cap except `uint256.max`; rh requires `<= uint256.max / 10^10`. The registered switchboard notices. Refs: `EndaomentPSM.vy:785-792@91eda49c`; `:162-164,802-809@251ac9e2`.

- **BD-30 — VERIFIED / CHANGED failure policy / SOURCE-REACHABLE.** R-aliases: R2 `K-8`; R4 `K-09`; opposed by R3/R5 same-outcome notes. Master’s checked `start + duration` can overflow for still-accepted near-max durations; rh uses subtraction. Users and interval-view callers notice after such configuration. Refs: `EndaomentPSM.vy:337-361,509-533,909-916@91eda49c`; `:341-375,526-550,926-933@251ac9e2`.

- **BD-31 — VERIFIED / CHANGED eligibility / CONFIGURATION-CONTINGENT.** R-aliases: R1 `K-SGREEN-NOSUPPLY`; R2 `K-15`; R3 `UC-K-07`; R4 `K-05`; R5 file note. Master can mint initial sGREEN; rh rejects every nonzero initial supply. Deployer/initial recipient notice. Refs: `SavingsGreen.vy:31-42`, `Erc20Token.vy:139-143@91eda49c`; `SavingsGreen.vy:31-44`, `Erc20Token.vy:140-144@251ac9e2`.

- **BD-32 — VERIFIED / CHANGED eligibility / CONFIGURATION-CONTINGENT.** R-aliases: R1 `K-PSM-CTOR`; R2 `K-8`; R3 `UC-K-12`; R4 `K-07`; R5 file note. Master requires only nonzero USDC; rh additionally requires `decimals() == 6`. The deployer notices. Refs: `EndaomentPSM.vy:201-202@91eda49c`; `:204-206@251ac9e2`.

- **BD-33 — VERIFIED / CHANGED eligibility / CONFIGURATION-CONTINGENT.** R-aliases: R1 `K-PSM-CTOR`; R2 `K-8`; R3 `UC-K-13`; R4 `K-07`; R5 file note. Master construction accepts every nonzero interval duration; rh also rejects `uint256.max`. The deployer notices. Refs: `EndaomentPSM.vy:181-182@91eda49c`; `:184-185@251ac9e2`.

- **BD-34 — VERIFIED / CHANGED eligibility / CONFIGURATION-CONTINGENT.** R-aliases: R1 `K-PSM-CTOR`; R2 `K-8`; R3 `UC-K-13`; R4 `K-07`; R5 `K-12`. Master construction accepts any nonzero mint cap except `uint256.max`; rh applies the `uint256.max / 10^10` ceiling. The deployer notices. Refs: `EndaomentPSM.vy:189-190@91eda49c`; `:162-164,192-193@251ac9e2`.

- **BD-35 — VERIFIED / NEW / CONFIGURATION-CONTINGENT.** R-aliases: R1 `K-CCIP-POOLS`; R2 `K-12` part; R3 `UC-K-15` part; R4 `K-17`; R5 `K-14` part. rh adds fixed GREEN-only and RIPE-only capability-response wrappers over `BurnMintTokenPool 1.5.1`; constructors accept arbitrary burn/mint tokens. Cross-chain integrators notice only after correct binding and CCIP/HQ configuration. Refs: `A@91eda49c`; `RipeCcipBurnMintTokenPools.sol:19-22,34-73@251ac9e2`.

## Ledger

| id | surface | class | master ref | rh ref | master ≤15w | rh ≤15w | reach | R-aliases | status |
|---|---|---|---|---|---|---|---|---|---|
| BD-01 | K allowance | CHANGED eligibility | Erc20Token:226-230,347-356 | Erc20Token:227-234,379-391 | All approve/permit values require pause and blacklist validation. | Zero value requires only a nonzero spender. | SOURCE-REACHABLE | R1 REVOKE; R2 K-1; R3 03; R4 K-01; R5 K-01 | VERIFIED |
| BD-02 | K allowance | CHANGED eligibility | Erc20Token:261-268 | Erc20Token:265-272 | Every decrease requires pause and blacklist validation. | Every decrease requires only a nonzero spender. | SOURCE-REACHABLE | R1 REVOKE; R2 K-1; R3 03; R4 K-01; R5 K-02 | VERIFIED |
| BD-03 | K holder burn | CHANGED failure policy | Erc20Token:306-309 | Erc20Token:316-336 | Blacklisted sGREEN holder may burn while unpaused. | Blacklisted asset-bearing-token holder may not burn. | SOURCE-REACHABLE | R1 VAULT-BURN; R2 K-2; R3 01; R4 K-03; R5 K-03 | VERIFIED |
| BD-04 | K holder burn | CHANGED failure policy | Erc20Token:306-317 | Erc20Token:337-349 | Final vault shares may burn while backed. | Final shares require zero underlying backing. | SOURCE-REACHABLE | same as BD-03 | VERIFIED |
| BD-05 | K gov burn | CHANGED eligibility | Erc20Token:414-422 | Erc20Token:450-457 | Governance may burn blacklisted GREEN at SavingsGreen. | SavingsGreen backing is excluded. | SOURCE-REACHABLE | R1 VAULT-BURN; R2 K-3; R3 02; R4 K-03; R5 K-04 | VERIFIED |
| BD-06 | K gov burn | CHANGED eligibility | Erc20Token:414-422 | Erc20Token:458-462 | Governance may burn final backed vault supply. | Final backed vault supply cannot burn. | SOURCE-REACHABLE | same as BD-05 | VERIFIED |
| BD-07 | K maxDeposit/maxMint | CHANGED outcome | Erc4626:54-57,83-86 | Erc4626:58-63,89-94,323-332 | Both always return uint256.max. | Blocked/invalid/unbacked state returns zero. | SOURCE-REACHABLE | R1 CAPS; R2 K-5; R3 05; R4 K-04; R5 K-06 | VERIFIED |
| BD-08 | K maxWithdraw | CHANGED outcome | Erc4626:127-130 | Erc4626:135-140,323-332 | Returns the vault’s whole GREEN balance. | Returns zero or owner-convertible GREEN. | SOURCE-REACHABLE | same as BD-07 | VERIFIED |
| BD-09 | K maxRedeem | CHANGED outcome | Erc4626:150-153 | Erc4626:160-165,323-332 | Returns owner shares without state checks. | Returns zero under blocking states. | SOURCE-REACHABLE | same as BD-07 | VERIFIED |
| BD-10 | K sGREEN exit | CHANGED failure policy | Erc4626:177-202 | Erc4626:189-217 | Exit ignores sGREEN pause and blacklist. | Exit rejects pause, owner blacklist, delegated-spender blacklist. | SOURCE-REACHABLE | R1 EXIT; R2 K-4; R3 06; R4 K-02; R5 K-05 | VERIFIED |
| BD-11 | K HQ validity | CHANGED eligibility | Erc20Token:503-526 | Erc20Token:543-566 | New HQ needs GREEN and RIPE. | New HQ also needs SavingsGreen. | SOURCE-REACHABLE | R1 HQ-SGREEN; R2 K-14; R3 file; R4 referral; R5 K-15 | VERIFIED |
| BD-12 | K token API | NEW | D getCCIPAdmin | Erc20Token:674-677 | No CCIP-admin view. | View returns HQ governance. | SOURCE-REACHABLE | R1 GETCCIPADMIN; R2 K-6; R3 14; R4 K-06; R5 K-07 | VERIFIED |
| BD-13 | K PSM redeem | CHANGED economics | PSM:450-476,484-495 | PSM:464-493,501-512 | Any nonzero priced capacity remains. | Sub-USDC-base-unit capacity becomes zero. | SOURCE-REACHABLE | R1 DUST; R2 K-7; R3 11; R4 K-08; R5 K-11 | VERIFIED |
| BD-14 | K stabilizer target | CHANGED economics | Endaoment:743-769,819-854,891-910 | Endaoment:785-815,873-902,943-962 | Ratio versus 50% drives adjustment. | Normalized alt versus GREEN drives adjustment. | SOURCE-REACHABLE | R1 STAB; R2 K-11; R3 09; R4 K-11; R5 K-09 | VERIFIED |
| BD-15 | K stabilizer remove | CHANGED outcome | Endaoment:861-922 | Endaoment:909-1002 | Removal uses unlimited LP maximum. | Quote and owned LP bound removal. | SOURCE-REACHABLE | R1 STAB; R2 K-11; R3 09; R4 K-12; R5 K-09 | VERIFIED |
| BD-16 | K stabilizer guard | CHANGED failure policy | Endaoment:758-776,943-967 | Endaoment:802-830,1033-1048 | Deep deficits clamp to zero. | Deficit sign and magnitude are preserved. | SOURCE-REACHABLE | R1 STAB; R2 K-11; R3 09; R4 K-13; R5 K-09 | VERIFIED |
| BD-17 | K stabilize action | CHANGED failure policy | Endaoment:749-752 | Endaoment:791-793,1008-1014 | Missing CurvePrices may revert. | Missing CurvePrices returns false. | SOURCE-REACHABLE | R4 K-14 | VERIFIED |
| BD-18 | K stabilize views | CHANGED failure policy | Endaoment:848-854,916-938 | Endaoment:896-902,996-1028 | Missing CurvePrices may revert. | Missing CurvePrices returns zero. | SOURCE-REACHABLE | R4 K-14; R5 K-10 | VERIFIED |
| BD-19 | K profit view | CHANGED failure policy | Endaoment:930-938 | Endaoment:1019-1028 | Empty pool may revert. | Empty pool returns zero. | SOURCE-REACHABLE | R4 K-14; R5 K-10 | VERIFIED |
| BD-20 | K profit view | CHANGED outcome | Endaoment:943-967 | Endaoment:1053-1066 | Zero LP can report positive leftover-GREEN profit. | Zero LP reports zero. | SOURCE-REACHABLE | R4 K-14 | VERIFIED |
| BD-21 | K partner ABI | CHANGED signature | Endaoment:988-996 | Endaoment:1088-1098 | Three default-generated call shapes exist. | One seven-argument call shape exists. | SOURCE-REACHABLE | R1 PARTNER; R2 K-9; R3 08; R4 K-15; R5 K-08 | VERIFIED |
| BD-22 | K partner LP identity | CHANGED eligibility | Endaoment:988-1014 | Endaoment:1090-1121 | No expected-LP identity policy. | Expected LP must be nonzero and match. | SOURCE-REACHABLE | same as BD-21 | VERIFIED |
| BD-23 | K partner LP split | CHANGED economics | Endaoment:1016-1035 | Endaoment:1113-1124,1153-1169 | Splits all custody LP. | Splits verified current-action LP. | SOURCE-REACHABLE | same as BD-21 | VERIFIED |
| BD-24 | K partner receipt | CHANGED economics | Endaoment:1051-1058 | Endaoment:1192-1203 | Values nominal partner amount. | Values external partner’s actual receipt. | SOURCE-REACHABLE | R1 PARTNER; R2 K-10; R4 K-16; R5 K-08 | VERIFIED |
| BD-25 | K partner asset | CHANGED eligibility | Endaoment:1043-1058 | Endaoment:1183-1193 | GREEN may be partner asset. | GREEN partner asset reverts. | SOURCE-REACHABLE | same as BD-24 | VERIFIED |
| BD-26 | K partner custody | CHANGED failure policy | Endaoment:1008-1014 | Endaoment:1126-1133 | Venue reports are trusted. | Reports must match bounded custody decreases. | SOURCE-REACHABLE | R2 K-9; R4 K-16; R5 K-08 | VERIFIED |
| BD-27 | K partner accounting | CHANGED economics | Endaoment:1002-1035 | Endaoment:1135-1151,1165-1169 | All provisional mint remains debt. | Unused mint burns; debt uses actual contribution. | SOURCE-REACHABLE | R1 PARTNER; R2 K-9; R3 08; R4 K-16; R5 K-08 | VERIFIED |
| BD-28 | K Endaoment lock | CHANGED failure policy | DeptBasics:63-84; Endaoment:176,204,245,742,975,988,1074 | Endaoment:172-190,213-215,242-244,284-286,783-785,1074-1090,1219-1221 | Ten entries permit shared-lock reentry. | Ten entries are nonreentrant. | SOURCE-REACHABLE | R2 K-13; R4 K-10; R5 K-13; R1/R3 files | VERIFIED |
| BD-29 | K PSM cap setter | CHANGED eligibility | PSM:785-792 | PSM:162-164,802-809 | Any nonzero non-max cap accepted. | Cap cannot exceed safe ceiling. | SOURCE-REACHABLE | R1 CTOR; R2 K-8; R3 13; R4 K-07; R5 K-12 | VERIFIED |
| BD-30 | K PSM interval | CHANGED failure policy | PSM:337-361,509-533,909-916 | PSM:341-375,526-550,926-933 | Checked addition can overflow. | Subtraction avoids duration overflow. | SOURCE-REACHABLE | R2 K-8; R4 K-09; R3/R5 disputed UC | VERIFIED |
| BD-31 | K sGREEN deploy | CHANGED eligibility | SavingsGreen:31-42; Erc20Token:139-143 | SavingsGreen:31-44; Erc20Token:140-144 | Constructor may mint initial shares. | Initial supply must be zero. | CONFIGURATION-CONTINGENT | R1 NOSUPPLY; R2 K-15; R3 07; R4 K-05; R5 file | VERIFIED |
| BD-32 | K PSM deploy | CHANGED eligibility | PSM:201-202 | PSM:204-206 | Any nonzero payment-token address accepted. | Payment token must report six decimals. | CONFIGURATION-CONTINGENT | R1 CTOR; R2 K-8; R3 12; R4 K-07; R5 file | VERIFIED |
| BD-33 | K PSM deploy | CHANGED eligibility | PSM:181-182 | PSM:184-185 | Any nonzero interval accepted. | uint256.max interval rejected. | CONFIGURATION-CONTINGENT | R1 CTOR; R2 K-8; R3 13; R4 K-07; R5 file | VERIFIED |
| BD-34 | K PSM deploy | CHANGED eligibility | PSM:189-190 | PSM:162-164,192-193 | Any nonzero non-max cap accepted. | Cap cannot exceed safe ceiling. | CONFIGURATION-CONTINGENT | R1 CTOR; R2 K-8; R3 13; R4 K-07; R5 K-12 | VERIFIED |
| BD-35 | K dedicated CCIP | NEW | A RipeCcipBurnMintTokenPools.sol | RipeCcipBurnMintTokenPools:19-22,34-73 | No dedicated wrapper source. | Fixed GREEN-only and RIPE-only capability responses. | CONFIGURATION-CONTINGENT | R1 POOLS; R2 K-12; R3 15; R4 K-17; R5 K-14 | VERIFIED |
| BD-36 | K legacy CCIP | NEW | A RipeTokenPool.sol | RipeTokenPool:7-49 | No legacy wrapper source. | Constructor selects either capability independently. | ROUTE NOT PROVEN | R1 LEGACY; R2 K-12; R3 15; R4 K-18; R5 K-14 | VERIFIED |
| UC-01 | K GREEN/RIPE mint | UNCHANGED | GreenToken/RipeToken:61-64 | GreenToken/RipeToken:61-64 | Matching HQ capability required. | Matching HQ capability required. | SOURCE-REACHABLE | all mint UCs | VERIFIED |
| UC-02 | K HQ mint gate | UNCHANGED | RipeHq:378-399 | RipeHq:378-399 | Enablement, registration, HQ bit, target response required. | Same four gates required. | SOURCE-REACHABLE | R1 HQ-CANMINT; R3 HQ-MINT; R4/R5 refs | VERIFIED |
| UC-03 | K token transfer | UNCHANGED | Erc20Token:187-215 | Erc20Token:188-216 | Pause, recipient, blacklist, balance, allowance rules apply. | Same rules apply. | SOURCE-REACHABLE | R1/R2 TRANSFER; R4 02; R5 2 | VERIFIED |
| UC-04 | K sGREEN deposit | UNCHANGED | Erc4626:66-119 | Erc4626:72-127 | Deposit/mint use transfer then token mint checks. | Same behavior. | SOURCE-REACHABLE | R2 SGREEN-DEPOSIT | VERIFIED |
| UC-05 | K GREEN/RIPE burn | UNCHANGED | D asset() in hosts; Erc20Token:306-317 | D asset() in hosts; Erc20Token:316-349 | Unpaused holders may burn despite blacklist. | Same for non-vault GREEN/RIPE. | SOURCE-REACHABLE | R1 VAULT-BURN; R2 K-2; R5 K-03 | VERIFIED |
| UC-06 | K PSM core | UNCHANGED | PSM:219-277,374-442 | PSM:223-281,388-456 | Core fees, allowlists, rates, and routing apply. | Same, apart from listed helper edges. | SOURCE-REACHABLE | R1 PSM-SWAP; R2 CORE; R3 mint/redeem; R4 03; R5 3 | VERIFIED |
| UC-07 | K EndaomentFunds | UNCHANGED | EndaomentFunds:48-76 | EndaomentFunds:46-74 | Same balance and Endaoment-only transfer behavior. | Same behavior. | SOURCE-REACHABLE | R1/R2/R4/R5 FUNDS; R3 file | VERIFIED |
| UC-08 | K Endaoment controls | UNCHANGED ordinary outcome | Endaoment:27; DeptBasics:22,63-84 | Endaoment:27-30,172-199 | Exported controls use switchboard and module state. | Hosted controls use same permission and state. | SOURCE-REACHABLE | R1 CTRL; R3 10; R5 7 | VERIFIED |
| UC-09 | K permit length | UNCHANGED acceptance | Erc20Token:347-373 | Erc20Token:379-409 | Short EOA signature reverts during slicing. | Short EOA signature reverts at length check. | SOURCE-REACHABLE | R3 04 losing BD; R5 UC-4 | VERIFIED |

## Files

| FOCUS path | final | ids | note |
|---|---|---|---|
| `contracts/tokens/GreenToken.vy` | CONFIRMED | BD-12, UC-01, UC-05 | Token export gains `getCCIPAdmin`; local mint unchanged. |
| `contracts/tokens/RipeToken.vy` | CONFIRMED | BD-12, UC-01, UC-05 | Token export gains `getCCIPAdmin`; local mint unchanged. |
| `contracts/tokens/SavingsGreen.vy` | CONFIRMED | BD-31, BD-12 | Zero-supply construction plus changed exported token surface. |
| `contracts/tokens/modules/Erc20Token.vy` | CONFIRMED | BD-01–BD-06, BD-11–BD-12; UC-03, UC-05, UC-09 | Allowance, burn, HQ, and API rules verified. |
| `contracts/tokens/modules/Erc4626Token.vy` | CONFIRMED | BD-07–BD-10; UC-04 | Limit and exit rules verified. |
| `contracts/core/Endaoment.vy` | CONFIRMED | BD-14–BD-28; UC-08 | Stabilizer, partner, lock, and effective-control surface verified. |
| `contracts/core/EndaomentFunds.vy` | CONFIRMED | UC-07 | External behavior unchanged; removed constant was not public. |
| `contracts/core/EndaomentPSM.vy` | CONFIRMED | BD-13, BD-29–BD-34; UC-06 | Dust, constructor/config bounds, and interval arithmetic verified. |
| `solidity/src/RipeCcipBurnMintTokenPools.sol` | CONFIRMED | BD-35 | Added on rh; configuration-contingent runtime. |
| `solidity/src/RipeTokenPool.sol` | CONFIRMED | BD-36 | Added on rh; legacy route not proven. |

## API

Added Vyper name:

- GREEN, RIPE, and sGREEN: `getCCIPAdmin() -> address` (`view`).

Signature-changed Vyper name:

- `Endaoment.addPartnerLiquidity`

  - Removed default-generated selectors:
    - `addPartnerLiquidity(uint256,address,address,address)`
    - `addPartnerLiquidity(uint256,address,address,address,uint256)`
    - `addPartnerLiquidity(uint256,address,address,address,uint256,uint256)`
  - Added:
    - `addPartnerLiquidity(uint256,address,address,address,uint256,uint256,address) -> (uint256,uint256,uint256)`

Endaoment’s `pause`, `recoverFunds`, `recoverFundsMany`, and `isPaused` move from a full module export to host declarations, but their effective names, parameters, returns, mutability, and permissions remain unchanged. No PSM or EndaomentFunds API name changes were found. Removed `API_VERSION`, `FIFTY_PERCENT`, and interface-only declarations were not user-visible.

Added Solidity wrapper-local names:

- `GreenCcipBurnMintTokenPool` and `RipeCcipBurnMintTokenPool`:
  - `canMintGreen() external pure returns (bool)`
  - `canMintRipe() external pure returns (bool)`
- `RipeTokenPool`:
  - `canMintGreen() external view returns (bool)`
  - `canMintRipe() external view returns (bool)`

The legacy capability flags are internal immutables and create no public getters.

Inherited user-visible names added on all three wrappers:

| group | names |
|---|---|
| Runtime | `lockOrBurn`, `releaseOrMint` |
| Views/getters | `typeAndVersion`, `owner`, `isSupportedToken`, `getToken`, `getRmnProxy`, `getRouter`, `supportsInterface`, `getTokenDecimals`, `getRemotePools`, `isRemotePool`, `getRemoteToken`, `isSupportedChain`, `getSupportedChains`, `getRateLimitAdmin`, `getCurrentOutboundRateLimiterState`, `getCurrentInboundRateLimiterState`, `getAllowListEnabled`, `getAllowList` |
| Administration | `setRouter`, `addRemotePool`, `removeRemotePool`, `applyChainUpdates`, `setRateLimitAdmin`, `setChainRateLimiterConfigs`, `setChainRateLimiterConfig`, `applyAllowListUpdates`, `transferOwnership`, `acceptOwnership` |

## Dropped / Open / referrals / SYNTH-CHECK

Dropped or corrected:

- R3 `UC-K-04` is not a behavior delta: short EOA signatures already revert on master during fixed slicing. It is retained as UC-09.
- R3’s internal helpers and removed internal constants/interface declarations are not API names.
- R2/R3’s “new direct Endaoment control APIs” are dropped: the selectors already existed through `deptBasics.__interface__`. Only BD-28’s lock behavior changes.
- R2’s new-exit wording is corrected from “GREEN paused” to **sGREEN paused**. GREEN’s transfer-side pause/blacklist rules already applied.
- R3’s “underlying asset blacklisted” wording is narrowed: GREEN is queried for whether it blacklisted the SavingsGreen vault.
- R2’s PSM “silent cap bypass” mechanism is wrong: master’s checked addition reverts. R3/R5’s same-outcome conclusion is also wrong because both setters still accept near-max durations. BD-30 records the verified rule.
- R2’s unqualified “a pool can never mint the other token” applies only to correctly bound dedicated wrappers. Legacy `RipeTokenPool` accepts any flag pair, including both true.
- R5’s “permissionless burn route” is narrowed: token `burn()` has no HQ authorization, but bridge `lockOrBurn()` is Router/configured-onRamp gated.
- Constructor-only changes are CONFIGURATION-CONTINGENT. Dedicated pools are also configuration-contingent; legacy `RipeTokenPool` remains ROUTE NOT PROVEN.

Open/referrals:

- **Lane 3D:** actual CCIP deployment and token binding, TokenAdminRegistry/admin ownership, Router ramps, remote pools, rate limits, HQ registry ID/config flags, `mintEnabled`, and active pool selection.
- **Price-source lane:** production, normalization, and live configuration of `StabilizerConfig.altBalance`.
- Live Base/Robinhood pool creation provenance is not proven by the added Solidity source.

SYNTH-CHECK:

- `_isValidNewRipeHq` also gates constructor initialization and `finishTokenSetup`, not only later migration: `Erc20Token.vy:134-136,600-608@91eda49c`; `:135-137,640-648@251ac9e2`.
- When `_partner == self`, master computes a half share but does not transfer it, leaving that half on Endaoment; rh leaves `partnerShare` at zero and sends all current-action LP to EndaomentFunds: `Endaoment.vy:1021-1029@91eda49c`; `:1153-1163@251ac9e2`.
- The unchanged downstream token mint restrictions were omitted by all drafts: recipient cannot be token/self or zero, cannot be blacklisted, and the token cannot be paused: `Erc20Token.vy:291-300@91eda49c`; `:301-310@251ac9e2`.

LANE SYNTHESIS COMPLETE — Lane 3C — 91eda49c vs 251ac9e2
