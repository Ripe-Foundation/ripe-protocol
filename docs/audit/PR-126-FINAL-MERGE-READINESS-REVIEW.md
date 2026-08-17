# PR #126 — Final Smart-Contract Merge-Readiness Review

**Repository:** `Ripe-Foundation/ripe-protocol`

**Pull request:** `#126` (`rh-audit-remediation` → `rh`)

**Base:** `36ee0db42482c3e7d6c43d045fc02655b90bebf4`

**Reviewed remediation head:** `5f3848c051655e6b9b7e439fb6db13348d87ade3`

**Contract/test snapshot:** `c9ae47e1854e676b5846c98baa40f5d0fdfaf324`

**Reviewed:** 2026-08-17

## Purpose and authority

This document records the final contract-focused merge review and the owner
decisions made after discussing the review findings. It supersedes the merge
verdict in `PR-126-SMART-CONTRACT-FINDINGS.md` for the exact remediation head
identified above. The older document remains historical evidence of the defects
present at its earlier reviewed head.

This review answers whether the remediation source is suitable to merge into
`rh`. It is not deployment, configuration, activation, migration, or release
authorization.

## Final verdict

**APPROVE — merge-ready from a smart-contract perspective.**

No unresolved production-contract defect identified by this final review blocks
merging `rh-audit-remediation` into `rh`. The integrated implementation is high
quality, the material remediation findings are fixed or deliberately dispositioned,
and the active contract regression suite is green.

The operational and trust decisions below are intentional parts of this verdict.
They must not later be misrepresented as contract-enforced guarantees.

## Owner decisions and final dispositions

### 1. SavingsGreen first-depositor risk is operational

The owner does not authorize an on-chain virtual-share, dead-share, or other
contract-code remediation in this branch. The protocol intends to control the
first sGREEN deposit as an operational mitigation.

This decision makes the known first-depositor donation/inflation risk non-blocking
for the source merge. It does not establish that the operational action has already
occurred, and it does not convert the operational protection into a contract
invariant. Deployment operators remain responsible for transaction ordering and
for preserving the intended seed position.

### 2. Registered Ripe addresses have full protocol trust

The owner confirmed that an address recognized by the protocol as a valid Ripe
address is fully trusted. This includes the trust needed for Teller's external
`performHousekeeping` route.

That route can select a user, choose the risk/debt-refresh mode, supply an `Addys`
bundle, update `lastTouch`, refresh the Curve reference snapshot, and trigger debt
and reward-point updates. Its broad authorization is therefore consistent with the
owner's intended trust model, not a missing permission boundary.

The only direct production callers found in the reviewed source are Deleverage and
VaultMigrator. Both are trusted core contracts. DER-01 in
`PR-126-DERIVED-FOLLOW-UP-REGISTER.md` is closed by this owner decision for the
reviewed topology. Reopen the decision only if a future registered address is not
intended to receive full protocol trust.

### 3. CreditEngine auction repayment bound is optional defense in depth

AuctionHouse is the only authorized caller of
`CreditEngine.repayDuringAuctionPurchase`. The reviewed AuctionHouse implementation
rereads live debt and caps GREEN accepted, and therefore discounted collateral
transferred, before each auction-purchase iteration moves collateral.

The focused regressions cover oversized input, partial and exact payoff, accrued
interest, same-borrower batches, refunds, cleanup, and transaction rollback. An
additional CreditEngine-side upper-bound assertion would duplicate the current
canonical boundary. Issue `#153` is future defense in depth, not a current
production-contract defect or merge blocker. Reconsider it if AuctionHouse's bound
changes, a new repayment caller is introduced, or CreditEngine is otherwise changed.

### 4. Source hashes and consumer inventories are process evidence

The excluded artifact lane contains exact-file hashes and a line-oriented inventory
of selected Vault getter consumers. A hash is a fingerprint of exact file bytes; a
"rebind" updates the stored fingerprint after a reviewed source change.

Those checks became stale after legitimate final changes to AuctionHouse,
CreditEngine, Deleverage, and Lootbox. The observed failures did not establish an
ABI mismatch or a runtime defect. ABI-currentness tests passed. Manual review of the
changed Lootbox consumers found backing-aware reward valuation that caps eligible
underlying by usable vault custody, with extensive behavioral regressions.

The owner does not require hash or line-number rebind work for this merge. These
process checks are non-blocking and may be retired or simplified separately in favor
of behavioral tests.

### 5. Deployment and CI-administration concerns are outside this verdict

Known deployment-test deselections, comprehensive-lane hygiene, and aggregation of
the unchanged Solidity job are outside the requested smart-contract merge decision.
They do not change this approval. The reviewed exact head's Solidity job passed, and
the remediation branch does not change the owned Solidity contracts.

## Contract behavior reviewed

The final review affirmatively checked the integrated production delta, material
value and authority flows, and the principal composed paths. Strong remediation and
regression coverage was confirmed for:

- Stability Pool liquidation and keeper-fee conservation;
- fungible-auction live-debt capping before collateral delivery;
- Deleverage callback/reentrancy debt refresh and atomic rollback;
- PriceDesk bounded-gas source isolation and malformed-response rejection;
- BasicVault backing-deficit handling and consumer behavior;
- SharesVault measured withdrawal delivery and bounded rounding behavior;
- oracle staleness, future-timestamp, and delayed-configuration handling;
- reward accounting, sender/recipient checkpoints, dust handling, and rollback;
- governance proposal/execution validation and lifecycle boundaries; and
- asset, vault, debt-limit, liquidation, and registry edge conditions.

No additional current Critical or High production-contract exploit was established
by the final review. The known sGREEN risk is retained under the explicit operational
decision above.

## Validation evidence

- `origin/rh-audit-remediation` is a direct 172-commit descendant of `origin/rh` at
  the reviewed refs, with no base-only commits and no merge conflict.
- `git diff --check` passed for the full base-to-remediation delta.
- The exact-head required GitHub workflow completed successfully, including eleven
  Python shards, deployment controls, snapshot gas, and the Solidity build/focused
  tests.
- A clean serial run of the active contract suite completed with **4,680 passed**,
  **266 deselected**, and **1 expected xfail**.
- The broader gas selection completed with **43 passed** and one process-only failure
  caused by an older CreditEngine source fingerprint; no gas measurement failed.
- The release/artifact/fuzz selection completed with **80 passed** and four
  process-only source-hash/inventory failures described above.
- Exported ABI-currentness checks passed.
- All measured reviewed runtimes fit EIP-170 under the pinned Vyper/Titanoboa
  toolchain. The smallest recorded margins include AuctionHouse at 8 bytes, Teller
  at 20 bytes, SwitchboardAlpha at 70 bytes, Lootbox at 132 bytes, Deleverage at
  152 bytes, and CreditEngine at 194 bytes.

The thin runtime margins are a constraint on later contract changes, not a failure
of this exact source.

## Non-merge activation and operational boundaries

The following retained items do not block the source merge but remain relevant only
when their associated features or live configuration are activated:

- protocol-controlled sGREEN first-depositor handling;
- nested BlueChip/PriceDesk gas composition;
- Comet-style multi-holder full-exit rounding;
- the AuctionHouse retry monitor tracked by issue `#160`;
- deployment/configuration verification for the remediated Underscore boundary;
- the specialized BlueChip/Undy stale-time policy decision;
- fresh live feed, PriceDesk, and Stock configuration reads; and
- dormant non-RH fallback integrations if they are ever enabled.

None of these items is deployment or activation authority, and none changes the
contract-focused approval recorded here.

## Final handoff

For the exact base and remediation head recorded above, the smart-contract review
conclusion is **approve and merge**. Any later production-contract change requires a
new delta review and proportional regression/runtime validation.
