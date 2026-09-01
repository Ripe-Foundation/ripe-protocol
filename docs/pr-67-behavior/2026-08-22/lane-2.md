# PR #67 lane synthesis — Lane 2

Draft only. Not a source of truth. If this file and the contracts disagree,
the contracts win.

- master: 91eda49ccd34a25090582aff0695075c4c806011
- rh:     251ac9e228a8af80326e8fe30f607511c78fe820
- date:   2026-08-22

# PR #67 behavior delta — Lane 2 — 91eda49c vs 251ac9e2

Pins and trees verified:

- master `91eda49ccd34a25090582aff0695075c4c806011`, tree `fbd958bec234081f70769045abd8f9bb638f6dd7`
- rh `251ac9e228a8af80326e8fe30f607511c78fe820`, tree `204de8657d9cd2eded1212028b9b5ba8d87b6506`

All retained BD/UC rows are VERIFIED. No source row remains unresolved or unchecked.

## Brief

VERIFIED — SOURCE-REACHABLE

- `BD-A-01` — R1:BD-A-01; R2:A5; R3:UC-A-02; R4:BD-A-01; R5:BD-A-03 — Teller now requires exact token receipt and exact vault credit.
- `BD-A-03` — R1:BD-A-02; R2:A8; R3:UC-A-03; R4:BD-A-02 — Held-funds deposits must fit caps completely.
- `BD-A-04` — R1:BD-A-03; R2:A6; R3:UC-A-04; R4:BD-A-06; R5:BD-A-02 — Empty deposit/withdraw batches now revert.
- `BD-AC-01` — R1:BD-A-04; R2:A7; R3:UC-A-08; R4:BD-AC-01; R5:BD-A-04 — Third-party deposit, repay, and redemption preserve the beneficiary’s last-touch.
- `BD-A-05` — R1:BD-A-08; R2:A10; R3:UC-A-09; R4:BD-AC-02; R5:BD-A-01 — Omitted user-access flags now default to deny.
- `BD-A-06` — R1:BD-A-09; R2:A9; R3:UC-CROSS-01; R4:BD-A-09; R5:BD-A-08 — A Lego needs the user-specific grant to gov-deposit for another user.
- `BD-A-09` — R1:BD-A-05; R2:A1; R3:UC-A-01; R4:Brief; R5:BD-A-07 — BasicVault deposits require full backing.
- `BD-A-10` — R1:BD-A-05; R2:A2; R3:Brief; R4:BD-A-04; R5:BD-A-07 — BasicVault withdrawals require backing and exact outflow/delivery.
- `BD-ABCF-01` — R1:BD-A-05/BD-B-01; R2:B1; R3:UC-A-06; R4:BD-ABCF-01; R5:BD-A-07/BD-B-01 — Under-backed BasicVault positions expose zero usable balance.
- `BD-A-11` — R1:BD-A-06; R2:A4; R3:Files; R4:BD-A-03; R5:BD-A-05 — A deposit producing zero shares now reverts.
- `BD-A-12` — R1:BD-A-06; R2:A3; R3:UC-A-05; R4:BD-A-05; R5:BD-A-06 — SharesVault withdrawals credit measured delivery and burn measured outflow.
- `BD-A-13` — R4:BD-A-08 — Full-precision share conversion avoids intermediate-product overflow when the quotient fits.
- `BD-A-14` — R1:BD-A-07; R2:B3; R3:UC-B-04; R4:BD-A-07; R5:BD-A-11 — Max-withdraw retained collateral now rounds upward.
- `BD-B-01` — R1:BD-B-01; R2:B1; R3:UC-B-01; R4:BD-ABCF-01; R5:BD-B-01 — Quarantine blocks borrowing and makes max borrow zero.
- `BD-B-02` — R1:BD-B-02; R2:B2; R3:UC-B-03; R4:BD-B-01; R5:BD-B-02 — Configured Stability vaults no longer enter collateral terms.
- `BD-B-03` — R4:BD-BF-01(a) — Registered zero-amount assets retain weighted debt terms.
- `BD-BC-01` — R4:BD-BF-01(b) — Positive zero-capacity dust no longer sets `lowestLtv`.
- `BD-C-01` — R1:BD-C-02; R2:C1; R3:UC-C-02; R4:BD-C-01; R5:BD-C-02 — Repayment surplus now returns to the payer.
- `BD-C-02` — R4:BD-C-02(a); R5:BD-C-03(a) — Full payoff skips collateral repricing.
- `BD-C-03` — R4:BD-C-02(b); R5:BD-C-03(b) — Partial standard repayment values collateral non-strictly.
- `BD-C-04` — R2:B4; R4:BD-B-02; R5:BD-C-09 — Stored terms survive when no eligible collateral supplies replacement terms.
- `BD-C-05` — R1:BD-C-01; R2:C2; R3:UC-C-01; R4:BD-C-03; R5:BD-C-01 — Singular redemption is removed.
- `BD-C-06` — R1:BD-C-03; R2:C3/C4; R3:UC-C-03; R4:BD-ABCF-01; R5:BD-C-05/BD-C-08 — Redemption skips unusable targets and quarantined accounts.
- `BD-C-07` — R1:BD-C-03/BD-C-04; R2:C3; R3:UC-C-03; R4:BD-C-04; R5:BD-C-06 — Expected zero-credit redemption dust skips before mutation.
- `BD-C-08` — R1:BD-C-04; R2:C3; R3:UC-C-03; R4:BD-C-04; R5:BD-C-06 — Excess outflow or positive zero-credit under-send now reverts.
- `BD-C-09` — R2:A12; R4:BD-C-05; R5:BD-C-07 — In-vault share transfers round down and return realizable value or zero.
- `BD-F-01` — R1:BD-F-01; R2:F1; R3:UC-F-01; R4:BD-F-01; R5:BD-F-01 — Singular deleverage APIs are removed.
- `BD-F-02` — R1:BD-F-02; R2:F3; R3:UC-F-02; R4:BD-F-02; R5:BD-F-03 — Registered Underscore callers lose batch-wide trust.
- `BD-F-03` — R1:BD-F-02; R2:F4; R3:UC-F-02; R4:BD-F-02; R5:BD-F-04 — Other-user ordered deleverage requires `canBorrow`.
- `BD-F-05` — R1:BD-F-04; R2:F2; R3:UC-F-04; R4:BD-F-03; R5:BD-F-02 — Permissionless deleverage skips in-liquidation users.
- `BD-F-06` — R1:BD-F-03; R2:F8; R3:Brief-F; R4:BD-ABCF-01; R5:BD-F-06 — Quarantine zeroes debt-repayment deleverage paths and their max view.

VERIFIED — CONFIGURATION-CONTINGENT

- `BD-A-02` — R2:A5; R3:UC-A-02; R4:BD-A-01; R5:BD-A-03 — A transient receipt window blocks overlapping deposit/housekeeping callbacks.
- `BD-A-07` — R1:BD-A-09; R2:A9; R4:BD-AB-CC-01 — Gov deposits use the configured nonzero core-gov vault ID.
- `BD-AB-01` — R1:BD-A-10; R2:C5; R3:UC-A-07; R4:BD-AB-CC-01; R5:BD-B-04 — Stability deposits use the configured nonzero preferred vault ID.
- `BD-A-08` — R1:BD-A-11; R2:A11; R3:UC-A-10; R4:BD-ABCF-CC-01; R5:BD-A-09 — Ledger can use ArbSys action blocks instead of `block.number`.
- `BD-A-15` — R1:BD-A-07/BD-B-01; R2:B1/B3; R3:UC-B-01; R4:BD-ABCF-01; R5:BD-B-01 — A detected quarantined sister asset zeroes max withdrawal.
- `BD-F-04` — R1:BD-F-05; R2:F5; R3:UC-F-03; R4:BD-F-02; R5:BD-F-05 — Other-user withdrawal deleverage requires `canBorrow`, then re-trusts the delegate.
- `BD-F-07` — R1:BD-F-01/API; R2:API; R3:UC-F-08; R4:BD-F-04; R5:BD-F-01/API — Nested retained deleverage mutations now revert.
- `BD-F-08` — R1:BD-F-06; R2:F6; R3:UC-F-05; R4:BD-F-04; R5:BD-F-08 — Settlement rereads debt and reverts if collateral interaction changed it.
- `BD-F-09` — R1:BD-F-07; R2:F7; R3:UC-F-06; R4:BD-F-CC-01; R5:BD-F-07 — Stability cohorts use fail-soft availability and skip ordinary priority processing.

## Catalog

- `BD-A-01` — R1:BD-A-01; R2:A5; R3:UC-A-02; R4:BD-A-01; R5:BD-A-03 — CHANGED failure policy; SOURCE-REACHABLE. Master trusts post-transfer vault credit. RH requires exact custody increase and full credit. Depositor/token integrator notices. Refs: `Teller.vy:294-304@91eda49c`, `312-328@251ac9e2`.

- `BD-A-03` — R1:BD-A-02; R2:A8; R3:UC-A-03; R4:BD-A-02 — CHANGED failure policy; SOURCE-REACHABLE. Master may cap held funds. RH requires the entire held amount to fit. Savings-GREEN converter notices. Refs: `TellerUtils.vy:152-165@91eda49c`, `153-169@251ac9e2`.

- `BD-A-04` — R1:BD-A-03; R2:A6; R3:UC-A-04; R4:BD-A-06; R5:BD-A-02 — CHANGED failure policy; SOURCE-REACHABLE. Empty batches returned zero after housekeeping; RH reverts first. Batch integrator notices. Refs: `Teller.vy:245-251,347-353@91eda49c`, `255-262,374-381@251ac9e2`.

- `BD-AC-01` — R1:BD-A-04; R2:A7; R3:UC-A-08; R4:BD-AC-01; R5:BD-A-04 — CHANGED eligibility; SOURCE-REACHABLE. Master always writes beneficiary last-touch. RH third-party deposit/repay/redemption only checks lock state. Beneficiary and third-party actor notice. Refs: `Teller.vy:313-315,486-540,986-997@91eda49c`, `340-342,577-606,1005-1023@251ac9e2`.

- `BD-A-05` — R1:BD-A-08; R2:A10; R3:UC-A-09; R4:BD-AC-02; R5:BD-A-01 — CHANGED eligibility; SOURCE-REACHABLE. Omitted deposit/repay/bond access flags defaulted true; RH defaults false. Caller relying on defaults notices. Refs: `Teller.vy:861-866@91eda49c`, `855-860@251ac9e2`.

- `BD-A-06` — R1:BD-A-09; R2:A9; R3:UC-CROSS-01; R4:BD-A-09; R5:BD-A-08 — CHANGED eligibility; SOURCE-REACHABLE. Any registered Lego could gov-deposit for a user. RH also requires wallet-specific access. Lego/user notices. Refs: `TellerUtils.vy:404-409@91eda49c`, `408-419@251ac9e2`.

- `BD-A-09` — R1:BD-A-05; R2:A1; R3:UC-A-01; R4:Brief; R5:BD-A-07 — CHANGED failure policy; SOURCE-REACHABLE. BasicVault credited the lesser of request and custody. RH requires custody covering liabilities plus deposit. Depositor notices. Refs: `BasicVault.vy:24-39@91eda49c`, `24-43@251ac9e2`.

- `BD-A-10` — R1:BD-A-05; R2:A2; R3:Brief; R4:BD-A-04; R5:BD-A-07 — CHANGED failure policy; SOURCE-REACHABLE. Master capped delivery to custody without measurement. RH requires backing and exact vault/recipient deltas. Withdrawer notices. Refs: `BasicVault.vy:43-65@91eda49c`, `47-80@251ac9e2`.

- `BD-ABCF-01` — R1:BD-A-05/BD-B-01; R2:B1; R3:UC-A-06; R4:BD-ABCF-01; R5:BD-A-07/BD-B-01 — CHANGED eligibility; SOURCE-REACHABLE. Master usable views exposed nominal balances despite deficit. RH returns zero while retaining identity. Withdrawer, borrower, redeemer, and keeper notice. Refs: `BasicVault.vy:116-148@91eda49c`, `140-185@251ac9e2`.

- `BD-A-11` — R1:BD-A-06; R2:A4; R3:Files; R4:BD-A-03; R5:BD-A-05 — CHANGED failure policy; SOURCE-REACHABLE. Master could transfer tokens while issuing zero shares. RH rejects zero-share deposits. Shares depositor notices. Refs: `SharesVault.vy:26-46@91eda49c`, `27-48@251ac9e2`.

- `BD-A-12` — R1:BD-A-06; R2:A3; R3:UC-A-05; R4:BD-A-05; R5:BD-A-06 — CHANGED outcome; SOURCE-REACHABLE. Master reports computed withdrawal. RH measures ±2 deltas, credits delivery, and burns outflow shares. Shares withdrawer notices. Refs: `SharesVault.vy:50-70@91eda49c`, `52-118@251ac9e2`.

- `BD-A-13` — R4:BD-A-08 — CHANGED failure policy; SOURCE-REACHABLE. Master’s checked product may overflow before division. RH full-precision division succeeds when the quotient fits. Quote caller notices. Refs: `SharesVault.vy:202-268@91eda49c`, `263-366@251ac9e2`.

- `BD-A-14` — R1:BD-A-07; R2:B3; R3:UC-B-04; R4:BD-A-07; R5:BD-A-11 — CHANGED economics; SOURCE-REACHABLE. Master floors retained collateral. RH rounds the remainder upward. Debted withdrawer notices. Refs: `CreditEngine.vy:1261-1286@91eda49c`, `1279-1309@251ac9e2`.

- `BD-B-01` — R1:BD-B-01; R2:B1; R3:UC-B-01; R4:BD-ABCF-01; R5:BD-B-01 — CHANGED eligibility; SOURCE-REACHABLE. Master may accept zero-valued live collateral without quarantine. RH blocks borrow and zeroes max borrow. Borrower notices. Refs: `CreditEngine.vy:232-245,726-769@91eda49c`, `235-250,395-401,722-779@251ac9e2`.

- `BD-B-02` — R1:BD-B-02; R2:B2; R3:UC-B-03; R4:BD-B-01; R5:BD-B-02 — CHANGED eligibility; SOURCE-REACHABLE. Master lets every registered vault enter debt terms. RH skips configured Stability vaults before traversal. Stability depositor/borrower notices. Refs: `CreditEngine.vy:715-742@91eda49c`, `706-710@251ac9e2`.

- `BD-B-03` — R4:BD-BF-01(a) — CHANGED economics; SOURCE-REACHABLE. Master skips registered zero-amount assets. RH retains their configured terms in weighted debt terms. Borrower with a retained asset registration notices. Refs: `CreditEngine.vy:726-760@91eda49c`, `722-774@251ac9e2`.

- `BD-BC-01` — R4:BD-BF-01(b) — CHANGED economics; SOURCE-REACHABLE. Positive zero-capacity dust could set `lowestLtv`; RH excludes it. Borrower or residual-debt payer notices. Refs: `CreditEngine.vy:741-760@91eda49c`, `747-771@251ac9e2`.

- `BD-C-01` — R1:BD-C-02; R2:C1; R3:UC-C-02; R4:BD-C-01; R5:BD-C-02 — CHANGED outcome; SOURCE-REACHABLE. Master sends repayment surplus to the debtor. RH sends it to the payer. Third-party payer notices. Refs: `CreditEngine.vy:454-478,541-578@91eda49c`, `451-475,536-580@251ac9e2`.

- `BD-C-02` — R4:BD-C-02(a); R5:BD-C-03(a) — CHANGED failure policy; SOURCE-REACHABLE. Master strictly reprices collateral even at full payoff. RH bypasses repricing. Full-payoff payer notices during price failure. Refs: `CreditEngine.vy:541-579@91eda49c`, `536-581@251ac9e2`.

- `BD-C-03` — R4:BD-C-02(b); R5:BD-C-03(b) — CHANGED failure policy; SOURCE-REACHABLE. Master strictly reprices partial standard repayment. RH uses non-strict valuation. Partial payer notices during unusable pricing. Refs: `CreditEngine.vy:541-579@91eda49c`, `536-581,678-815@251ac9e2`.

- `BD-C-04` — R2:B4; R4:BD-B-02; R5:BD-C-09 — CHANGED economics; SOURCE-REACHABLE. Master overwrites stored terms when no eligible collateral contributes. RH preserves them. Residual-debt borrower notices through future accrual. Refs: `CreditEngine.vy:1122-1147@91eda49c`, `1126-1154@251ac9e2`.

- `BD-C-05` — R1:BD-C-01; R2:C2; R3:UC-C-01; R4:BD-C-03; R5:BD-C-01 — REMOVED; SOURCE-REACHABLE. Master offers singular and batch redemption. RH retains only batch redemption. Integrator/redeemer notices. Refs: `Teller.vy:502-540@91eda49c`; singular absent, batch `592-606@251ac9e2`.

- `BD-C-06` — R1:BD-C-03; R2:C3/C4; R3:UC-C-03; R4:BD-ABCF-01; R5:BD-C-05/BD-C-08 — CHANGED failure policy; SOURCE-REACHABLE. Master strict-prices targets and accounts. RH skips unusable targets and zeroes quarantined redeemability. Redeemer notices. Refs: `CreditRedeem.vy:206-241,303-326@91eda49c`, `208-250,319-342@251ac9e2`.

- `BD-C-07` — R1:BD-C-03/BD-C-04; R2:C3; R3:UC-C-03; R4:BD-C-04; R5:BD-C-06 — CHANGED outcome; SOURCE-REACHABLE. Master may transfer before discovering zero repayment. RH skips expected zero-credit dust first. Redeemer notices. Refs: `CreditRedeem.vy:231-249@91eda49c`, `234-263@251ac9e2`.

- `BD-C-08` — R1:BD-C-04; R2:C3; R3:UC-C-03; R4:BD-C-04; R5:BD-C-06 — CHANGED failure policy; SOURCE-REACHABLE. Master may accept unexpected zero-credit outflow. RH skips zero sends but rejects excessive outflow or positive zero-credit sends. Redeemer notices. Refs: `CreditRedeem.vy:243-261@91eda49c`, `252-275@251ac9e2`.

- `BD-C-09` — R2:A12; R4:BD-C-05; R5:BD-C-07 — CHANGED economics; SOURCE-REACHABLE. Master rounds internal share transfer upward. RH rounds down and returns realizable value or zero. Redemption balance-transfer caller notices. Refs: `SharesVault.vy:74-93,183-196@91eda49c`, `124-144,224-257@251ac9e2`.

- `BD-F-01` — R1:BD-F-01; R2:F1; R3:UC-F-01; R4:BD-F-01; R5:BD-F-01 — REMOVED; SOURCE-REACHABLE. Master has singular and batch deleverage. RH retains batch/specific forms only. Keeper/integrator notices. Refs: `Teller.vy:834-852`, `Deleverage.vy:262-304@91eda49c`; singulars absent, retained paths `Teller.vy:835-846`, `Deleverage.vy:280-305@251ac9e2`.

- `BD-F-02` — R1:BD-F-02; R2:F3; R3:UC-F-02; R4:BD-F-02; R5:BD-F-03 — CHANGED eligibility; SOURCE-REACHABLE. Master grants registered Underscore callers batch-wide trust. RH resolves trust per user. Underscore batch operator notices. Refs: `Deleverage.vy:281-304,682-715@91eda49c`, `283-305,697-735@251ac9e2`.

- `BD-F-03` — R1:BD-F-02; R2:F4; R3:UC-F-02; R4:BD-F-02; R5:BD-F-04 — CHANGED eligibility; SOURCE-REACHABLE. Master lets any registered Underscore caller order another user’s assets. RH requires `canBorrow`, then trusts the delegate. Ordered-asset integrator notices. Refs: `Deleverage.vy:310-329@91eda49c`, `311-329@251ac9e2`.

- `BD-F-05` — R1:BD-F-04; R2:F2; R3:UC-F-04; R4:BD-F-03; R5:BD-F-02 — CHANGED eligibility; SOURCE-REACHABLE. Master permissionless deleverage may process in-liquidation users. RH skips them. Permissionless keeper/borrower notices. Refs: `Deleverage.vy:689-715@91eda49c`, `707-735@251ac9e2`.

- `BD-F-06` — R1:BD-F-03; R2:F8; R3:Brief-F; R4:BD-ABCF-01; R5:BD-F-06 — CHANGED eligibility; SOURCE-REACHABLE. Master has no quarantine flag. RH zeroes debt-repayment deleverage routes and their max view. Keeper/borrower notices. Refs: `CreditEngine.vy:99-105,685-785`, `Deleverage.vy:331-1130@91eda49c`; corresponding RH paths `102-108,678-753`, `331-1187@251ac9e2`.

- `BD-A-02` — R2:A5; R3:UC-A-02; R4:BD-A-01; R5:BD-A-03 — CHANGED failure policy; CONFIGURATION-CONTINGENT. Master has no receipt window. RH blocks overlapping deposits and housekeeping while measuring receipt. Callback-capable token/actor notices. Refs: absence on master receipt path `Teller.vy:294-304`; `Teller.vy:213,308-331,1012@251ac9e2`.

- `BD-A-07` — R1:BD-A-09; R2:A9; R4:BD-AB-CC-01 — CHANGED outcome; CONFIGURATION-CONTINGENT. Master gov-deposits into vault 2. RH uses configured nonzero `coreRipeGovVaultId`, default 2. Gov depositor notices after configuration change. Refs: `Teller.vy:762-772@91eda49c`, `763-774,964-969@251ac9e2`.

- `BD-AB-01` — R1:BD-A-10; R2:C5; R3:UC-A-07; R4:BD-AB-CC-01; R5:BD-B-04 — CHANGED outcome; CONFIGURATION-CONTINGENT. Master conversion/borrow-to-stability uses vault 1. RH uses configured nonzero preferred ID, default 1. Stability depositor notices after configuration change. Refs: `Teller.vy:628-642`, `CreditEngine.vy:1182-1208@91eda49c`; `671-687`, `1197-1225@251ac9e2`.

- `BD-A-08` — R1:BD-A-11; R2:A11; R3:UC-A-10; R4:BD-ABCF-CC-01; R5:BD-A-09 — CHANGED failure policy; CONFIGURATION-CONTINGENT. Master last-touch uses `block.number`. RH deployment chooses `block.number` or ArbSys. Same-action-window user notices. Refs: `Ledger.vy:186-210@91eda49c`, `130-132,189-246@251ac9e2`.

- `BD-A-15` — R1:BD-A-07/BD-B-01; R2:B1/B3; R3:UC-B-01; R4:BD-ABCF-01; R5:BD-B-01 — CHANGED eligibility; CONFIGURATION-CONTINGENT. Master has no returned-quarantine gate. RH returns zero when traversal detects a quarantined sister asset. Debted withdrawer notices. Refs: `CreditEngine.vy:1257-1259,726-742@91eda49c`, `722-754,1274-1277@251ac9e2`.

- `BD-F-04` — R1:BD-F-05; R2:F5; R3:UC-F-03; R4:BD-F-02; R5:BD-F-05 — CHANGED eligibility; CONFIGURATION-CONTINGENT. Master trusts any registered Underscore withdrawal caller. RH requires `canBorrow`, then re-trusts it internally. Wallet/vault integration notices. Refs: `Deleverage.vy:557-563,655-687@91eda49c`, `566-578,668-705@251ac9e2`.

- `BD-F-07` — R1:BD-F-01/API; R2:API; R3:UC-F-08; R4:BD-F-04; R5:BD-F-01/API — CHANGED failure policy; CONFIGURATION-CONTINGENT. Master retained mutations lack a guard. RH Teller and Deleverage reject nesting. Callback-capable integration notices. Refs: `Teller.vy:841-852`, `Deleverage.vy:281-558@91eda49c`; corresponding RH decorators `835-846`, `283-568@251ac9e2`.

- `BD-F-08` — R1:BD-F-06; R2:F6; R3:UC-F-05; R4:BD-F-04; R5:BD-F-08 — CHANGED failure policy; CONFIGURATION-CONTINGENT. Master settles against snapshot debt. RH rereads debt and reverts on change. Callback-capable collateral user notices. Refs: `Deleverage.vy:385-392,458-463,735-743@91eda49c`, `383-394,461-470,753-797@251ac9e2`.

- `BD-F-09` — R1:BD-F-07; R2:F7; R3:UC-F-06; R4:BD-F-CC-01; R5:BD-F-07 — CHANGED failure policy; CONFIGURATION-CONTINGENT. Master treats Stability positions as ordinary traversal entries. RH uses fail-soft amounts and skips them in priority processing. Configured Stability cohort notices. Refs: `Deleverage.vy:802-916@91eda49c`, `834-973@251ac9e2`.

## Ledger

| id | surface | class | master ref | rh ref | master ≤15w | rh ≤15w | reach | R-aliases | status |
|---|---|---|---|---|---|---|---|---|---|
| BD-A-01 | A | CHANGED failure policy | `Teller.vy:294-304@91eda49c` | `Teller.vy:312-328@251ac9e2` | Transfer, then trust vault-reported credit | Require exact custody and vault credit | SOURCE-REACHABLE | R1:BD-A-01; R2:A5; R3:UC-A-02; R4:BD-A-01; R5:BD-A-03 | VERIFIED |
| BD-A-02 | A | CHANGED failure policy | A `receiptMeasurementActive`; receipt `Teller.vy:294-304@91eda49c` | `Teller.vy:213,308-331,1012@251ac9e2` | No receipt window blocks overlap | Transient window blocks deposit and housekeeping overlap | CONFIGURATION-CONTINGENT | R2:A5; R3:UC-A-02; R4:BD-A-01; R5:BD-A-03 | VERIFIED |
| BD-A-03 | A | CHANGED failure policy | `TellerUtils.vy:152-165@91eda49c` | `TellerUtils.vy:153-169@251ac9e2` | Held amount may shrink to caps | Entire held amount must fit | SOURCE-REACHABLE | R1:BD-A-02; R2:A8; R3:UC-A-03; R4:BD-A-02 | VERIFIED |
| BD-A-04 | A | CHANGED failure policy | `Teller.vy:245-251,347-353@91eda49c` | `Teller.vy:255-262,374-381@251ac9e2` | Empty batch returns zero | Empty batch reverts | SOURCE-REACHABLE | R1:BD-A-03; R2:A6; R3:UC-A-04; R4:BD-A-06; R5:BD-A-02 | VERIFIED |
| BD-AC-01 | A/C | CHANGED eligibility | `Teller.vy:313-315,486-540,986-997@91eda49c` | `Teller.vy:340-342,577-606,1005-1023@251ac9e2` | Every completed path writes beneficiary last-touch | Third-party path preserves last-touch | SOURCE-REACHABLE | R1:BD-A-04; R2:A7; R3:UC-A-08; R4:BD-AC-01; R5:BD-A-04 | VERIFIED |
| BD-A-05 | A/C | CHANGED eligibility | `Teller.vy:861-866@91eda49c` | `Teller.vy:855-860@251ac9e2` | Omitted access flags default true | Omitted access flags default false | SOURCE-REACHABLE | R1:BD-A-08; R2:A10; R3:UC-A-09; R4:BD-AC-02; R5:BD-A-01 | VERIFIED |
| BD-A-06 | A | CHANGED eligibility | `TellerUtils.vy:404-409@91eda49c` | `TellerUtils.vy:408-419@251ac9e2` | Any registered Lego may gov-deposit | Lego also needs user-specific access | SOURCE-REACHABLE | R1:BD-A-09; R2:A9; R3:UC-CROSS-01; R4:BD-A-09; R5:BD-A-08 | VERIFIED |
| BD-A-07 | A | CHANGED outcome | `Teller.vy:762-772@91eda49c` | `Teller.vy:763-774,964-969@251ac9e2` | Gov deposit targets vault 2 | Use configured nonzero core-gov vault | CONFIGURATION-CONTINGENT | R1:BD-A-09; R2:A9; R4:BD-AB-CC-01 | VERIFIED |
| BD-AB-01 | A/B | CHANGED outcome | `Teller.vy:628-642`; `CreditEngine.vy:1182-1208@91eda49c` | `Teller.vy:671-687`; `CreditEngine.vy:1197-1225@251ac9e2` | Stability deposit targets vault 1 | Use configured nonzero preferred vault | CONFIGURATION-CONTINGENT | R1:BD-A-10; R2:C5; R3:UC-A-07; R4:BD-AB-CC-01; R5:BD-B-04 | VERIFIED |
| BD-A-08 | A | CHANGED failure policy | `Ledger.vy:186-210@91eda49c` | `Ledger.vy:130-132,189-246@251ac9e2` | Last-touch uses block.number | Deployment chooses block.number or ArbSys | CONFIGURATION-CONTINGENT | R1:BD-A-11; R2:A11; R3:UC-A-10; R4:BD-ABCF-CC-01; R5:BD-A-09 | VERIFIED |
| BD-A-09 | A | CHANGED failure policy | `BasicVault.vy:24-39@91eda49c` | `BasicVault.vy:24-43@251ac9e2` | Credit minimum of request and custody | Require backing for liabilities plus deposit | SOURCE-REACHABLE | R1:BD-A-05; R2:A1; R3:UC-A-01; R4:Brief; R5:BD-A-07 | VERIFIED |
| BD-A-10 | A | CHANGED failure policy | `BasicVault.vy:43-65@91eda49c` | `BasicVault.vy:47-80@251ac9e2` | Cap withdrawal to available custody | Require backing and exact delivery | SOURCE-REACHABLE | R1:BD-A-05; R2:A2; R3:Brief; R4:BD-A-04; R5:BD-A-07 | VERIFIED |
| BD-ABCF-01 | A/B/C/F | CHANGED eligibility | `BasicVault.vy:116-148@91eda49c` | `BasicVault.vy:140-185@251ac9e2` | Usable views expose nominal balance | Under-backed usable views return zero | SOURCE-REACHABLE | R1:BD-A-05/BD-B-01; R2:B1; R3:UC-A-06; R4:BD-ABCF-01; R5:BD-A-07/BD-B-01 | VERIFIED |
| BD-A-11 | A | CHANGED failure policy | `SharesVault.vy:26-46@91eda49c` | `SharesVault.vy:27-48@251ac9e2` | Zero-share deposit can complete | Zero-share deposit reverts | SOURCE-REACHABLE | R1:BD-A-06; R2:A4; R3:Files; R4:BD-A-03; R5:BD-A-05 | VERIFIED |
| BD-A-12 | A | CHANGED outcome | `SharesVault.vy:50-70@91eda49c` | `SharesVault.vy:52-118@251ac9e2` | Burn and report computed amount | Measure delivery and outflow | SOURCE-REACHABLE | R1:BD-A-06; R2:A3; R3:UC-A-05; R4:BD-A-05; R5:BD-A-06 | VERIFIED |
| BD-A-13 | A | CHANGED failure policy | `SharesVault.vy:202-268@91eda49c` | `SharesVault.vy:263-366@251ac9e2` | Checked product may overflow first | Full-precision division succeeds if quotient fits | SOURCE-REACHABLE | R4:BD-A-08 | VERIFIED |
| BD-A-14 | A | CHANGED economics | `CreditEngine.vy:1261-1286@91eda49c` | `CreditEngine.vy:1279-1309@251ac9e2` | Floor retained collateral | Round retained collateral upward | SOURCE-REACHABLE | R1:BD-A-07; R2:B3; R3:UC-B-04; R4:BD-A-07; R5:BD-A-11 | VERIFIED |
| BD-A-15 | A/F | CHANGED eligibility | `CreditEngine.vy:1257-1259,726-742@91eda49c` | `CreditEngine.vy:722-754,1274-1277@251ac9e2` | No returned-quarantine withdrawal gate | Detected quarantine zeroes max withdrawal | CONFIGURATION-CONTINGENT | R1:BD-A-07/BD-B-01; R2:B1/B3; R3:UC-B-01; R4:BD-ABCF-01; R5:BD-B-01 | VERIFIED |
| BD-A-16 | A | CHANGED eligibility | `SharesVault.vy:57@91eda49c` | `SharesVault.vy:59-60@251ac9e2` | Vault-self withdrawal recipient allowed | Vault-self recipient reverts | ROUTE NOT PROVEN | R5:BD-A-06 | VERIFIED |
| BD-B-01 | B | CHANGED eligibility | `CreditEngine.vy:232-245,726-769@91eda49c` | `CreditEngine.vy:235-250,395-401,722-779@251ac9e2` | Zero-valued live collateral may avoid quarantine | Quarantine blocks and zeroes borrowing | SOURCE-REACHABLE | R1:BD-B-01; R2:B1; R3:UC-B-01; R4:BD-ABCF-01; R5:BD-B-01 | VERIFIED |
| BD-B-02 | B | CHANGED eligibility | `CreditEngine.vy:715-742@91eda49c` | `CreditEngine.vy:706-710@251ac9e2` | Every registered vault enters terms | Stability vaults are skipped | SOURCE-REACHABLE | R1:BD-B-02; R2:B2; R3:UC-B-03; R4:BD-B-01; R5:BD-B-02 | VERIFIED |
| BD-B-03 | B | CHANGED economics | `CreditEngine.vy:726-760@91eda49c` | `CreditEngine.vy:722-774@251ac9e2` | Skip zero-amount registered assets | Retain their weighted debt terms | SOURCE-REACHABLE | R4:BD-BF-01(a) | VERIFIED |
| BD-BC-01 | B/C | CHANGED economics | `CreditEngine.vy:741-760@91eda49c` | `CreditEngine.vy:747-771@251ac9e2` | Zero-capacity dust may set lowestLtv | Zero-capacity dust cannot set lowestLtv | SOURCE-REACHABLE | R4:BD-BF-01(b) | VERIFIED |
| BD-C-01 | C | CHANGED outcome | `CreditEngine.vy:454-478,541-578@91eda49c` | `CreditEngine.vy:451-475,536-580@251ac9e2` | Refund repayment surplus to debtor | Refund surplus to payer | SOURCE-REACHABLE | R1:BD-C-02; R2:C1; R3:UC-C-02; R4:BD-C-01; R5:BD-C-02 | VERIFIED |
| BD-C-02 | C | CHANGED failure policy | `CreditEngine.vy:541-579@91eda49c` | `CreditEngine.vy:536-581@251ac9e2` | Full payoff strictly reprices collateral | Full payoff skips repricing | SOURCE-REACHABLE | R4:BD-C-02(a); R5:BD-C-03(a) | VERIFIED |
| BD-C-03 | C | CHANGED failure policy | `CreditEngine.vy:541-579@91eda49c` | `CreditEngine.vy:536-581,678-815@251ac9e2` | Partial standard repay strictly reprices | It values collateral non-strictly | SOURCE-REACHABLE | R4:BD-C-02(b); R5:BD-C-03(b) | VERIFIED |
| BD-C-04 | C | CHANGED economics | `CreditEngine.vy:1122-1147@91eda49c` | `CreditEngine.vy:1126-1154@251ac9e2` | Empty terms overwrite stored terms | Preserve stored terms without replacements | SOURCE-REACHABLE | R2:B4; R4:BD-B-02; R5:BD-C-09 | VERIFIED |
| BD-C-05 | C | REMOVED | `Teller.vy:502-540@91eda49c` | D singular; batch `Teller.vy:592-606@251ac9e2` | Singular and batch redemption exist | Only batch redemption remains | SOURCE-REACHABLE | R1:BD-C-01; R2:C2; R3:UC-C-01; R4:BD-C-03; R5:BD-C-01 | VERIFIED |
| BD-C-06 | C | CHANGED failure policy | `CreditRedeem.vy:206-241,303-326@91eda49c` | `CreditRedeem.vy:208-250,319-342@251ac9e2` | Unusable pricing may revert batch | Skip unusable targets and quarantine | SOURCE-REACHABLE | R1:BD-C-03; R2:C3/C4; R3:UC-C-03; R4:BD-ABCF-01; R5:BD-C-05/BD-C-08 | VERIFIED |
| BD-C-07 | C | CHANGED outcome | `CreditRedeem.vy:231-249@91eda49c` | `CreditRedeem.vy:234-263@251ac9e2` | Zero credit may follow transfer | Expected zero-credit dust skips first | SOURCE-REACHABLE | R1:BD-C-03/BD-C-04; R2:C3; R3:UC-C-03; R4:BD-C-04; R5:BD-C-06 | VERIFIED |
| BD-C-08 | C | CHANGED failure policy | `CreditRedeem.vy:243-261@91eda49c` | `CreditRedeem.vy:252-275@251ac9e2` | Unexpected outflow may repay zero | Invalid positive outflow reverts | SOURCE-REACHABLE | R1:BD-C-04; R2:C3; R3:UC-C-03; R4:BD-C-04; R5:BD-C-06 | VERIFIED |
| BD-C-09 | C | CHANGED economics | `SharesVault.vy:74-93,183-196@91eda49c` | `SharesVault.vy:124-144,224-257@251ac9e2` | Internal transfer rounds shares upward | Round down; return realizable amount | SOURCE-REACHABLE | R2:A12; R4:BD-C-05; R5:BD-C-07 | VERIFIED |
| BD-C-10 | C | CHANGED failure policy | `BasicVault.vy:68-87@91eda49c` | `BasicVault.vy:83-104@251ac9e2` | Under-backed internal bookkeeping allowed | Internal transfer requires full backing | ROUTE NOT PROVEN | R1:BD-A-05; R2:A12; R4:BD-A-04; R5:BD-A-07 | VERIFIED |
| BD-C-11 | C | CHANGED eligibility | `BasicVault.vy:68-87@91eda49c` | `BasicVault.vy:83-104@251ac9e2` | Same-user internal transfer allowed | Same-user internal transfer reverts | ROUTE NOT PROVEN | R1:BD-A-05; R2:A12; R4:BD-A-04; R5:BD-A-07 | VERIFIED |
| BD-F-01 | F | REMOVED | `Teller.vy:834-852`; `Deleverage.vy:262-304@91eda49c` | D singulars; retained `835-846`, `280-305@251ac9e2` | Singular and batch deleverage exist | Only batch and specific forms remain | SOURCE-REACHABLE | R1:BD-F-01; R2:F1; R3:UC-F-01; R4:BD-F-01; R5:BD-F-01 | VERIFIED |
| BD-F-02 | F | CHANGED eligibility | `Deleverage.vy:281-304,682-715@91eda49c` | `Deleverage.vy:283-305,697-735@251ac9e2` | Registered Underscore gains batch-wide trust | Trust is resolved per user | SOURCE-REACHABLE | R1:BD-F-02; R2:F3; R3:UC-F-02; R4:BD-F-02; R5:BD-F-03 | VERIFIED |
| BD-F-03 | F | CHANGED eligibility | `Deleverage.vy:310-329@91eda49c` | `Deleverage.vy:311-329@251ac9e2` | Registered Underscore may order assets | Other-user ordering requires canBorrow | SOURCE-REACHABLE | R1:BD-F-02; R2:F4; R3:UC-F-02; R4:BD-F-02; R5:BD-F-04 | VERIFIED |
| BD-F-04 | F | CHANGED eligibility | `Deleverage.vy:557-563,655-687@91eda49c` | `Deleverage.vy:566-578,668-705@251ac9e2` | Registered Underscore is always trusted | Other-user caller needs canBorrow, then trusted | CONFIGURATION-CONTINGENT | R1:BD-F-05; R2:F5; R3:UC-F-03; R4:BD-F-02; R5:BD-F-05 | VERIFIED |
| BD-F-05 | F | CHANGED eligibility | `Deleverage.vy:689-715@91eda49c` | `Deleverage.vy:707-735@251ac9e2` | Permissionless path ignores liquidation state | It skips in-liquidation users | SOURCE-REACHABLE | R1:BD-F-04; R2:F2; R3:UC-F-04; R4:BD-F-03; R5:BD-F-02 | VERIFIED |
| BD-F-06 | F | CHANGED eligibility | `CreditEngine.vy:99-105,685-785`; `Deleverage.vy:331-1130@91eda49c` | `CreditEngine.vy:102-108,678-753`; `Deleverage.vy:331-1187@251ac9e2` | Deleverage has no quarantine flag | Quarantine zeroes repayment paths and max | SOURCE-REACHABLE | R1:BD-F-03; R2:F8; R3:Brief-F; R4:BD-ABCF-01; R5:BD-F-06 | VERIFIED |
| BD-F-07 | F | CHANGED failure policy | `Teller.vy:841-852`; `Deleverage.vy:281-558@91eda49c` | `Teller.vy:835-846`; `Deleverage.vy:283-568@251ac9e2` | Retained mutations lack reentrancy guards | Nested deleverage mutations revert | CONFIGURATION-CONTINGENT | R1:BD-F-01/API; R2:API; R3:UC-F-08; R4:BD-F-04; R5:BD-F-01/API | VERIFIED |
| BD-F-08 | F | CHANGED failure policy | `Deleverage.vy:385-392,458-463,735-743@91eda49c` | `Deleverage.vy:383-394,461-470,753-797@251ac9e2` | Settle using snapshot debt | Reread debt; changed amount reverts | CONFIGURATION-CONTINGENT | R1:BD-F-06; R2:F6; R3:UC-F-05; R4:BD-F-04; R5:BD-F-08 | VERIFIED |
| BD-F-09 | F | CHANGED failure policy | `Deleverage.vy:802-916@91eda49c` | `Deleverage.vy:834-973@251ac9e2` | Stability positions use ordinary traversal | Stability traversal is fail-soft and separated | CONFIGURATION-CONTINGENT | R1:BD-F-07; R2:F7; R3:UC-F-06; R4:BD-F-CC-01; R5:BD-F-07 | VERIFIED |
| UC-A-01 | A | UNCHANGED eligibility | `TellerUtils.vy:118-165@91eda49c` | `TellerUtils.vy:119-169@251ac9e2` | Ordinary deposit authorization and caps apply | Ordinary deposit authorization and caps apply | SOURCE-REACHABLE | R1:UC-A-01; R2:unchanged-A; R4:UC-A-01 | VERIFIED |
| UC-A-02 | A | UNCHANGED eligibility | `TellerUtils.vy:201-226@91eda49c` | `TellerUtils.vy:205-230@251ac9e2` | Withdrawal delegation and capping apply | Withdrawal delegation and capping apply | SOURCE-REACHABLE | R1:UC-A-02; R2:unchanged-A; R4:UC-A-02; R5:UC-A-01 | VERIFIED |
| UC-A-03 | A | UNCHANGED outcome | `Teller.vy:401-456@91eda49c` | `Teller.vy:429-484@251ac9e2` | Rebalance deposits, withdraws, then checks health | Same sequence remains | SOURCE-REACHABLE | R1:UC-A-04; R2:unchanged-A; R5:UC-A-03 | VERIFIED |
| UC-A-04 | A | UNCHANGED eligibility | `Teller.vy:899-915@91eda49c` | `Teller.vy:893-909@251ac9e2` | Delegation defaults and owner checks apply | Same delegation rules apply | SOURCE-REACHABLE | R1:UC-A-05; R2:unchanged-A; R5:UC-A-04 | VERIFIED |
| UC-A-05 | A | UNCHANGED eligibility | `Teller.vy:945-962@91eda49c` | `Teller.vy:939-956@251ac9e2` | setUndyLegoAccess writes all grants true | Same grant writes remain | SOURCE-REACHABLE | R1:UC-A-06; R2:unchanged-A; R5:UC-A-04 | VERIFIED |
| UC-A-06 | A | UNCHANGED eligibility | `Teller.vy:254-265@91eda49c` | `Teller.vy:265-276@251ac9e2` | depositFromTrusted permissions and signature remain | Same trusted-deposit behavior remains | SOURCE-REACHABLE | R2:unchanged-A; R5:UC-A-04 | VERIFIED |
| UC-B-01 | B | UNCHANGED eligibility | `CreditEngine.vy:235-245,312-365@91eda49c` | `CreditEngine.vy:239-250,312-365@251ac9e2` | Borrow-for-other permission and limits apply | Same permissions and limits apply | SOURCE-REACHABLE | R1:UC-B-01; R2:UC-B; R4:UC-B-01; R5:UC-B-01 | VERIFIED |
| UC-B-02 | B | UNCHANGED eligibility | `CreditEngine.vy:321@91eda49c` | `CreditEngine.vy:321@251ac9e2` | Borrow rejects in-liquidation accounts | Borrow still rejects them | SOURCE-REACHABLE | R1:UC-B-02; R4:UC-B-02; R5:UC-B-01 | VERIFIED |
| UC-B-03 | B | UNCHANGED economics | `CreditEngine.vy:301-303@91eda49c` | `CreditEngine.vy:301-303@251ac9e2` | Borrower receives borrow less daowry | Same GREEN or sGREEN proceeds remain | SOURCE-REACHABLE | R1:UC-B-03; R4/R5:broad-borrow-UC | VERIFIED |
| UC-C-01 | C | UNCHANGED eligibility | `CreditEngine.vy:585-622@91eda49c` | `CreditEngine.vy:587-619@251ac9e2` | Repay authorization and min sizing apply | Same authorization and sizing apply | SOURCE-REACHABLE | R1:UC-C-01; R2:UC-C; R4:UC-C-01; R5:UC-C-01 | VERIFIED |
| UC-C-02 | C | UNCHANGED outcome | `CreditRedeem.vy:153-156@91eda49c` | `CreditRedeem.vy:154-157@251ac9e2` | Leftover GREEN returns to caller | Leftover GREEN returns to caller | SOURCE-REACHABLE | R1:UC-C-02 | VERIFIED |
| UC-C-03 | C | UNCHANGED eligibility | `CreditRedeem.vy:176-182,206-223@91eda49c` | `CreditRedeem.vy:177-183,208-226@251ac9e2` | Self, debtless, liquidation targets skip | Same targets skip | SOURCE-REACHABLE | R1:UC-C-03; R4:UC-C-02; R5:UC-C-02 | VERIFIED |
| UC-C-04 | C | UNCHANGED economics | `CreditRedeem.vy:329-342@91eda49c` | `CreditRedeem.vy:345-357@251ac9e2` | Redemption payback calculation applies | Same calculation applies | SOURCE-REACHABLE | R2/R4/R5:redemption-math-UC | VERIFIED |
| UC-C-05 | C | UNCHANGED failure policy | `CreditRedeem.vy:140-157@91eda49c` | `CreditRedeem.vy:141-158@251ac9e2` | All-skipped batch reverts | All-skipped batch still reverts | SOURCE-REACHABLE | R1/R2/R4/R5:batch-UC | VERIFIED |
| UC-F-01 | F | UNCHANGED eligibility | `CreditEngine.vy:1238-1244@91eda49c` | `CreditEngine.vy:1255-1261@251ac9e2` | In-liquidation ordinary max withdrawal is zero | It remains zero | SOURCE-REACHABLE | R1:UC-A-03; R4:UC-A-03; R5:UC-A-02 | VERIFIED |
| UC-F-02 | F | UNCHANGED failure policy | `Deleverage.vy:592-603@91eda49c` | `Deleverage.vy:607-616@251ac9e2` | Same-block withdrawal deleverage remains allowed | Same strict-greater cooldown remains | SOURCE-REACHABLE | R1:UC-F-01; R2:unchanged-UC-F; R4:UC-F-02; R5:UC-F-01 | VERIFIED |
| UC-F-03 | F | UNCHANGED economics | `Deleverage.vy:717-783@91eda49c` | `Deleverage.vy:737-815@251ac9e2` | Full-payoff buffer and dust formulas apply | Same formulas apply | SOURCE-REACHABLE | R1:UC-F-02; R2:unchanged-UC-F; R4:UC-F-01; R5:UC-F-01 | VERIFIED |
| UC-F-04 | F | UNCHANGED eligibility | `Deleverage.vy:476-491@91eda49c` | `Deleverage.vy:483-499@251ac9e2` | Swap requires Ripe or governance | Same authorization remains | SOURCE-REACHABLE | R1:UC-F-03 | VERIFIED |

## Files

| FOCUS path | final | ids | note |
|---|---|---|---|
| `contracts/core/TellerUtils.vy` | CONFIRMED | BD-A-03, BD-A-06, UC-A-01, UC-A-02 | Held-funds and gov-Lego behavior verified. |
| `contracts/core/CreditRedeem.vy` | CONFIRMED | BD-C-06–BD-C-08, UC-C-02–UC-C-05 | Redemption eligibility, dust, and transfer guards verified. |
| `contracts/core/Deleverage.vy` | CONFIRMED | BD-F-01–BD-F-09, UC-F-02–UC-F-04 | Assigned deleverage entry and settlement paths verified. |
| `contracts/vaults/modules/BasicVault.vy` | CONFIRMED | BD-A-09, BD-A-10, BD-ABCF-01, BD-C-10, BD-C-11 | Deposit, withdrawal, usable-view, and internal-transfer deltas verified. |
| `contracts/vaults/modules/SharesVault.vy` | CONFIRMED | BD-A-11–BD-A-13, BD-A-16, BD-C-09 | Deposit, withdrawal, conversion, and internal-transfer deltas verified. |
| `contracts/vaults/modules/VaultData.vy` | INSPECTED same outcome | — | `_deregisterVaultAsset` extraction preserves the relevant behavior: `175-201@91eda49c`, `175-206@251ac9e2`. |
| `contracts/data/Ledger.vy` | CONFIRMED | BD-A-08 | Action-block selection and generated getter verified. |
| `contracts/core/Teller.vy` | PARTIAL | BD-A-01, BD-A-02, BD-A-04–BD-A-07, BD-AB-01, BD-AC-01, BD-C-05, BD-F-01, BD-F-07 | Only the assigned shared-selector ceiling was inspected. |
| `contracts/core/CreditEngine.vy` | PARTIAL | BD-A-14, BD-A-15, BD-B-01–BD-B-03, BD-BC-01, BD-C-01–BD-C-04, BD-F-06 | Only the assigned shared-selector ceiling was inspected. |

## API

Added:

- `Ledger.getArbActionBlock() -> uint256`
- Generated `Ledger.ACTION_BLOCK_SOURCE() -> address` from `ACTION_BLOCK_SOURCE: public(immutable(address))`

Removed:

- `Teller.redeemCollateral(address,uint256,address,uint256,bool,bool,bool,address) -> uint256`
- `Teller.deleverageUser(address = msg.sender,uint256 = max_value(uint256)) -> uint256`
- `Deleverage.deleverageUser(address,address,uint256,Addys = empty(Addys)) -> uint256`

Declaration/signature changes:

- `Ledger.__init__(_ripeHq: address, _defaults: address)` becomes `Ledger.__init__(_ripeHq: address, _defaults: address, _actionBlockSource: address)`.
- `Teller.setUserConfig` keeps its parameter and return types, but the three Boolean defaults change from `True` to `False`. This changes the full declaration, not its ABI selector.
- `CreditEngine.UserBorrowTerms` appends `hasQuarantinedAsset: bool`. Tuple decoding changes for:
  - `getUserBorrowTerms`
  - `getUserBorrowTermsWithNumVaults`
  - `getLatestUserDebtAndTerms`

No rebuilt-name change:

- `TellerUtils`: exports and all nine external declarations are unchanged.
- `CreditRedeem`: `redeemCollateralFromMany`, `getMaxRedeemValue`, and its exports are unchanged.
- `Deleverage`: retained external declarations, exports, and public getters are unchanged; `@nonreentrant` is runtime behavior, not ABI.
- `BasicVault`: no standalone `@external`, export, or public-getter names.
- `SharesVault`: `amountToShares(address,uint256,bool)` and `sharesToAmount(address,uint256,bool)` are unchanged.
- `VaultData`: public getters and eleven external declarations are unchanged.
- `CreditEngine` scalar returns such as `getMaxBorrowAmount`, `getMaxRedeemValue`, and `getMaxDeleverageAmount` do not gain tuple-shape ABI changes.
- Supporting `SwitchboardDelta.deleverageUser` is also removed, but it is outside the rebuilt FOCUS/shared inventory.

## Dropped / Open / referrals / SYNTH-CHECK

Dropped:

- R3’s “borrow no longer clears `inLiquidation`” is same outcome. Both trees first reject an in-liquidation borrow at `CreditEngine.vy:321`; the removed write was unreachable.
- R2:F5, R3:UC-F-03, and R5:BD-F-05 incorrectly say an authorized withdrawal delegate remains untrusted/capped. RH re-trusts a `canBorrow` delegate at `Deleverage.vy:702-705`.
- “All deleverage entries are quarantine-gated” is too broad. `swapCollateral` is not; BD-F-06 is limited to debt-repayment paths and `getMaxDeleverageAmount`.
- R5’s full-precision “same outcome” claim holds only where the master intermediate multiplication does not overflow. R4’s behavioral delta wins.
- R2’s scalar-getter ABI claim does not match the declarations. Only the three `UserBorrowTerms`-returning functions change tuple decoding.
- R3’s internal-helper additions are not API names.
- CreditRedeem’s configured-Stability branch is not promoted: its current caller passes `_shouldEnterStabPool=False` on both pins.
- R3’s “delegated withdraw skips last-touch” does not match RH: ordinary withdraw paths still request a last-touch write.
- R3’s held-funds attribution to `depositFromTrusted` does not match the route; that entry uses ordinary transferred-funds mode.
- “All BasicVault getters return zero while under-backed” is overbroad. Nominal inventory helpers remain nominal.
- `TellerUtils.isUnderscoreAddr` changes which MissionControl address it dereferences, but no assigned Lane 2 caller was established; it is not promoted to product behavior.

Open:

- No UNRESOLVED or UNCHECKED source row.
- Actual post-deployment `coreRipeGovVaultId`, `preferredStabVaultId`, Stability-ID sets, and priority arrays were not established.
- The deployed Ledger `ACTION_BLOCK_SOURCE` was not established. Source proves only that `0` and `0x64` are accepted.
- Actual callback-capable collateral/token configurations and callback permissions were not established.
- `BD-A-16`, `BD-C-10`, and `BD-C-11` are source-verified but remain ROUTE NOT PROVEN for an assigned Lane 2 user path.

Referrals:

- Re-liquidation of an already-liquidating user with no open auction belongs to the liquidation lane.
- Price-source production and strict-versus-zero price semantics belong to the price-source lane; this report records only Lane 2 consumers.
- Lootbox deposit-point checkpoints belong to the rewards lane.
- Migration/export-import paths, auction/Stability singulars, bond operations, and other removed Teller selectors belong to their respective lanes.
- Auction use of BasicVault internal balance transfer remains an auction-lane concern.

SYNTH-CHECK:

- RH full payoff leaves the local borrow-terms bundle empty, so repayment event collateral fields become zero; the drafts did not isolate this consequence.
- RH adds a second `AddressRegistry.isValidAddr(vaultAddr)` assertion in Teller’s receipt path. TellerUtils already resolves a registered vault, so product significance was not promoted.
- No in-repo production caller of `deleverageForWithdrawal` was found at either pin; its third-party integration remains configuration-contingent.
- `getMaxDeleverageAmount` already returned zero for `inLiquidation` on master and still does on RH; that view gate is not new.
- The rebuilt FOCUS/shared API inventory found no additional unreported Lane 2 name change.

LANE SYNTHESIS COMPLETE — Lane 2 — 91eda49c vs 251ac9e2
