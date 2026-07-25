# Track 8 M0 owner-decision packet

**Status:** Owner directions recorded on 24–25 July 2026. All documentable
pre-implementation M0 inputs are complete and ready for independent review.
**M0 remains open pending that review and owner closure; M1 remains
unauthorized.**

**Revision baseline:** current reviewed `rh`
`fc48ac45e5f6e8c698a6464a14289aad00e1f2d4`

During this unstaged revision, local `rh` advanced from
`185bd32004121bbb1c60748844c517ea8da0affb` to
`fc48ac45e5f6e8c698a6464a14289aad00e1f2d4`. The increment adds only
`docs/chains/rh/track-6-s6-track-7-h4-defaults-parameters.md`; it changes none
of the four Track 8 package files. On 25 July 2026 the Track 8 branch was
fast-forwarded to the exact `fc48ac45` commit. No rebase, merge commit, or
history rewrite occurred; the four-document unstaged delta was preserved.

**Scope:** Documentation-only decision reconciliation. This packet does not
authorize M1, production source or test changes, a vault or VaultBook ID, an
ABI, default, migration, manifest, deployment, configuration, signer,
transaction, live probe, bridge activation, reward distribution, or Base
cutover.

## 1. Provenance and controlling record

On **24 July 2026**, the owner stated that the fourteen decisions in this
packet were correct and approved. On **25 July 2026**, the owner approved the
partial-fill refinement in Section 6.1 exactly as written and accepted the
residual risk in Section 6.2. That later authorization permits documenting
the decision and completing the remaining pre-implementation M0 evidence
only. The owner expressly prohibited M1 and every production/test/interface/
ABI/default/migration/manifest/`rh-summary.md` change.

This revision must be independently reviewed with:

- [Track 8 M0 evidence](stock-token-m0-evidence.md), SHA-256
  `6da31ade6594b2988d06e896abd9e219a41780e0bb36bf9a0cbab479026e2fba`;
- [Track 8 M0 sanitized raw evidence](stock-token-m0-raw-evidence.json),
  immutable in this revision, SHA-256
  `9ea333b4e84330f56c3a3d70e68823cfdba9c37948508e692450e01b3e994cba`;
- [Track 8 minimum-change specification](stock-token-vault-change-specification.md),
  SHA-256
  `61173781b4a410efa693e24075955f1d40d5621758a9e078f42703f9053fa1a9`;
  and
- [Track 8 validation plan](stock-token-vault-change-validation-plan.md),
  SHA-256
  `c786ef7dd7ff925e1667f3aab90423aa51e30daeba325250e1ec939792fff5e6`.

The companion hashes above were computed after the complete unstaged revision;
the packet's own final hash is returned out of band because embedding it would
be self-referential. A checked decision below records owner policy; it does not
prove or close its evidence requirements.

## 2. Owner-approved launch graph

### 2.1 Stock Token set

- [x] **AAPL is the only initial Stock Token.**
- [x] Additional Stock Tokens should follow soon after launch, but each
  requires token-specific proxy/beacon/implementation identity, runtime
  hashes, transfer behavior, oracle, administrative controls, and complete
  ordinary/trusted route evidence before separate approval.

The initial AAPL proxy remains
`0xaF3D76f1834A1d425780943C99Ea8A608f8a93f9`. The accepted historical fork
does not waive final identity revalidation.

### 2.2 Cross-chain graph

- [x] GREEN and RIPE CCIP are launch targets for both tokens, but are not
  launch blockers.
- [x] Target a separately reviewed CCIP promotion within seven days after
  launch.
- [x] If any CCIP identity, route, authority, supply, accounting, monitoring,
  rollback, or state-independence gate is incomplete, launch with CCIP
  disabled.
- [x] sGREEN is chain-native and must never be CCIP-enabled.

Seven days is an operational target, not automatic authorization. An enabled
CCIP route requires a fresh promotion package with complete propagation,
security, authority, monitoring, and rollback evidence. Missing the target
leaves CCIP disabled. Disabled CCIP preserves the M0 state-independence
conclusion and does not block the chain-local launch.

### 2.3 Chain-native protocol routes

- [x] Chain-native sGREEN deposits and withdrawals must be active on launch
  day.
- [x] USDG/EndaomentPSM minting and redemption are launch targets.
- [x] Use canonical USDG and the approved USDG/USD feed.
- [x] Curve is not a PSM dependency.
- [x] Prove redemption first and grant GREEN mint authority last.
- [x] Enable the GREEN Stability Pool and RIPE governance vault at launch.
- [x] Stock Tokens remain excluded from Stability Pool custody and swaps.
- [x] GREEN/USDG LP and RIPE/WETH LP are launch deposit tokens with zero
  borrowing power.
- [x] USDG is used only by the PSM and GREEN/USDG liquidity pool, not as
  ordinary Teller collateral.
- [x] CreditRedeem Stock extraction remains disabled.
- [x] Underscore and other Base-only integrations remain omitted.

These are product directions, not deployment evidence. M0 freezes exact
identities and compatibility for every already-selected, already-existing
external dependency. An unselected factory/pool is not silently treated as an
M0 dependency; not-yet-built Ripe/LP artifacts instead require exact proposed
file/route/authority dispositions. Their eventual selection/creation inputs,
deployment addresses, runtime hashes, and composed route proof are post-M0
launch gates.

The existing external dependency freeze is:

- canonical Robinhood USDG
  `0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168`, exact six-decimal fee-free
  non-rebasing ordinary transfers under the integrated runtime, PSM/LP-only;
- approved USDG/USD feed
  `0x61B7e5650328764B076A108EFF5fa7282a1B9aD2`;
- chain-operator-listed Robinhood WETH
  `0x0Bd7D308f8E1639FAb988df18A8011f41EAcAD73`, constituent-only for the
  future RIPE/WETH LP; and
- AAPL plus its feed in Sections 2.1 and 4.

GREEN/USDG LP and RIPE/WETH LP are new launch artifacts, not existing external
contracts. M0 freezes their constituents, ordinary-only Teller disposition,
all trusted routes omitted, and `ltv=0`. DEX/factory/pool/oracle selection,
creation inputs, LP addresses/runtimes, and composed route proof remain later
launch-component gates; this packet does not invent or select them.

## 3. Rewards

- [x] Rewards begin globally disabled.
- [x] Target reward activation within seven days after launch, subject to
  validation.
- [x] AAPL depositors and AAPL-backed borrowers may participate after that
  validation.
- [x] Accept the risk that nominal/global reward accounting may briefly accrue
  rewards after an issuer/custody incident until the global switches are
  disabled.
- [x] Require live monitoring and a rehearsed
  `arePointsEnabled=false` / `ripePerBlock=0` kill-switch runbook.
- [x] Do not add Stock-specific reward-accounting contract changes by default.

This revision freezes the launch-disabled policy and returns its
monitoring/kill-switch runbook for independent review. Later launch-day
evidence must prove the
deployed global disabled state. Reward activation requires its own validation
and operations record; the seven-day target is not permission to distribute
rewards.

## 4. AAPL evidence and exposure

### 4.1 Fork and identity

- [x] Accept the existing successful integrated AAPL pinned-fork evidence plus
  the later matching proxy, beacon, implementation, and runtime identities.
- [x] Any proxy/beacon/implementation identity change requires complete
  revalidation before activation or continued use.

This accepts the documented archive-provider limitation. It does not approve a
live transfer or an unidentified future implementation.

### 4.2 Exposure and route constraints

- [x] Target **$5,000 per user** and **$25,000 globally**.
- [x] Convert both targets to fixed 18-decimal AAPL amounts using the approved
  AAPL/USD price at the final freeze.
- [x] Review whenever either stored cap's USD value rises more than 10% above
  its approved target and at least every seven days.
- [x] Permit exactly one enabled AAPL vault.
- [x] Disable every AAPL trusted/Department deposit route.

This revision freezes these pre-implementation inputs:

| Field | M0 freeze / later evidence |
| --- | --- |
| Approved AAPL/USD feed | Integrated proxy and aggregator identity, source, decimals, heartbeat, and failure rules; current runtime hashes/owner are re-pinned at the later final freeze |
| Freeze procedure | Exact formula, approved feed, target values, rounding rule, required block/hash/timestamp provenance, and responsible reviewer |
| Cap inputs | `$5,000`, `$25,000`, AAPL 18-decimal units, 10% upward-drift trigger, and seven-day review interval |
| Vault cardinality | One-enabled-vault product/configuration rule and no-alternate-route plan; the actual future vault address/ID is post-M0 |
| Trusted routes | Complete current-source ordinary/trusted caller inventory and the approved rule that every AAPL Department bypass is disabled |

The actual freeze price, resulting base-unit integers, new Ripe vault address,
and post-deployment configuration proof are later M1–M5 outputs and cannot
block M0.

The frozen feed is proxy
`0x6B22A786bAa607d76728168703a39Ea9C99f2cD0`, eight decimals, with a
published `86,400`-second heartbeat. For USD target `D` and positive
eight-decimal answer `P8`:

```text
capAtomic = floor(D * 10^(18 + 8) / P8)
```

Use `D=5,000` and `D=25,000`, round down, pin one final
block/hash/timestamp plus current proxy/aggregator runtime identities and
round-quality fields, and require two-person arithmetic review and
configuration readback. The actual market answer and cap integers remain
post-M0.

## 5. Base posture

- [x] Leave current Base deployments unchanged.
- [x] Accept that refreshed M0 evidence did not demonstrate an urgent live
  Base vulnerability.
- [x] Require a separate proposal, fresh evidence, per-asset compatibility,
  migration design, security review, and owner authorization before any future
  Base cutover.

This accepts the documented latent Base receipt, backing/health, and legacy
internal-settlement mechanisms. It does not authorize migration or state
change.

## 6. Initial AAPL settlement

### 6.1 Selected direction and approved partial-fill invariant

- [x] External settlement remains the frontend default.
- [x] Internal movement is permitted only through the candidate launch vault
  when revert-safe reads prove known `C>=N` before and after.
- [x] Aggregate nominal accounting must remain unchanged and live custody must
  remain unchanged during the internal accounting move.
- [x] An unknown read, pre/post deficit, nominal mismatch, total-accounting
  change, or custody change reverts before GREEN payment or debt reduction.
- [x] Existing auction-disable controls, live monitoring, conservative caps,
  and incident response remain mandatory.
- [x] Do not add AuctionHouse changes, persistent settlement-mode
  configuration, canonical-interface changes, Ledger changes, or
  chain-specific logic unless independent review proves the vault-local
  mechanism insufficient.
- [x] **Owner-approved on 25 July 2026:** permit legitimate partial fills
  under the exact invariant below, with payment and debt reduction based only
  on `W`.

Notation:

```text
C0 = vault custody before internal move
C1 = vault custody after internal move
N  = aggregate nominal accounting, unchanged by an internal user-to-user move
Q  = maximum requested nominal settlement amount
W  = vault-reported nominal amount moved

success only if:
known(C0,C1) and C0 >= N and C1 >= N
and 0 < W <= Q
and sellerNominalDecrease == W
and buyerNominalIncrease == W
and aggregateNominalAfter == N
and C1 == C0
and payment/debt reduction are based only on W
```

Current AuctionHouse ordering calls the vault before charging GREEN or
reducing debt. The fresh vault owns custody reads, nominal totals,
`transferBalanceWithinVault`, and the nonreentrancy boundary. Subject to
composed validation, the design remains within the same three-contract
production surface: Teller, the fresh generic vault, and CreditEngine.
AuctionHouse and Deleverage remain negative-diff requirements.

The owner approved this exact refinement on 25 July 2026. It replaces
full-request equality because AuctionHouse supplies a maximum request and
BasicVault may safely return the seller's smaller remaining balance. The
approval includes seller depletion, per-row batch accounting, over-request
handling, and failure atomicity. For external delivery, the earlier Phase F
bound remains `E=min(Q,W,R)`, and payment/debt remain bounded by `E`. This
decision does not authorize M1 or select a vault, VaultBook ID, implementation
artifact, deployment, or configuration.

### 6.2 Accepted residual risk

- [x] A guarded internal settlement does not exercise issuer transfer,
  blocklist, pause, or recipient-eligibility controls.
- [x] A buyer's nominal claim can later become frozen or undeliverable.
- [x] The owner accepts that residual risk under conservative caps, external
  frontend default, monitoring, auction disablement, and incident response.

### 6.3 Unacceptable boundary

- [x] Phantom collateral is not accepted.
- [x] First-withdrawer loss allocation is not accepted.
- [x] Zero-backed settlement that charges GREEN or reduces debt is not
  accepted.

If the vault-local proof cannot preserve those boundaries without an
AuctionHouse, canonical-interface, persistent-state, or Ledger change, M0
returns to the owner. It does not silently widen M1.

## 7. M0 pre-implementation closure record

The four-document package now completes every input that can exist before
implementation:

1. every already-existing external token that can reach the proposed Teller
   has frozen identity and exact-transfer compatibility: AAPL is the only
   ordinary Stock collateral; canonical USDG is PSM/LP-only and exact-transfer
   compatible; WETH is only a future LP constituent whose operator identity is
   pinned; all other external assets and routes are omitted;
2. the current-source ordinary/trusted caller and route-disposition matrix is
   complete, including one-vault AAPL intent, every AAPL Department route
   disabled, USDG excluded from ordinary Teller collateral, and Stock excluded
   from CreditRedeem, Stability custody/swaps, and Base-only integrations;
3. the file-exact proposed Robinhood/Base state-independence proof classifies
   every bridge, message, shared custody, credit, debt, settlement, accounting,
   and token-authority edge; distinct chain-local RipeHq resolution and
   disabled launch CCIP are mandatory;
4. the approved AAPL/USD proxy, decimals, heartbeat, price-pin procedure, cap
   formula, rounding, 10% upward-drift trigger, and seven-day review procedure
   are frozen;
5. the CCIP-complete-or-disabled policy, seven-day promotion target, fresh
   promotion-package requirement, and permanent no-sGREEN-CCIP rule are
   frozen;
6. launch-disabled rewards and the source-exact monitoring/kill procedure are
   frozen: `setRewardsPointsEnabled(false)` is a fast disable available to
   governance or a configured lite actor; `setRipePerBlock(0)` is a governed,
   timelocked action and must already be zero at launch and be initiated
   immediately after any later incident;
7. the exact proposed Teller/`GuardedErc20`/CreditEngine production-file
   boundary, unchanged AuctionHouse/Deleverage boundary, and proposed
   test/file inventory are frozen;
8. source traces establish that exact deposit measurement, guarded
   partial-fill settlement, unsafe-position evaluation, repayment liveness,
   and payment/debt ordering are plausible without a larger production
   change;
9. the owner approved the exact partial-fill invariant in Section 6.1; and
10. the file-exact M1 authorization proposal in Section 10 is complete without
    beginning M1.

M0 nevertheless remains open until this package receives independent review
and the owner explicitly closes M0. No unresolved pre-implementation evidence
item is converted into an implementation or deployment assertion.

### 7.1 Post-M0 evidence gates

The following are required later but cannot block M0 because they depend on
authorized implementation or deployment:

- implemented `GuardedErc20` source, compiler, storage, ABI, bytecode, runtime,
  and nonreentrancy evidence;
- composed implementation tests for partial fills, exact external delivery,
  credit/health, repayment, AuctionHouse, and Deleverage;
- new Ripe contract, vault, token, CCIP-pool, PSM, Stability, RipeGov, and
  deployment addresses/runtime hashes that do not yet exist;
- actual freeze price and resulting fixed AAPL cap integers;
- post-deployment route, role, configuration, negative-reachability, and
  runtime proof; and
- final M1–M5 integration, audit, deployment, promotion, and activation
  evidence.

## 8. Complete owner-decision mapping

| Owner decision | Controlling packet section | Specification | Validation section / named tests |
| --- | --- | --- | --- |
| 1. AAPL only | 2.1 | 3.22; 23.6.1; 23.7–23.11 | 20.6–20.10; `check_m0_aapl_only_scope_and_later_token_evidence_rule`; later route-enable and added-token tests |
| 2. GREEN/RIPE CCIP target; sGREEN never CCIP | 2.2 | 3.22; 23.6–23.6.1; 23.9 | 20.6–20.10; four `check_m0_ccip_*` policy checks; later disabled-at-launch and promoted-route proofs |
| 3. Rewards disabled then validated activation | 3 | 3.22; 23.3.E; 23.7–23.11 | 20.6; 20.9–20.10; `check_m0_launch_disabled_reward_policy_and_runbook`; later deployed-disable and incident-response tests |
| 4. AAPL fork accepted; identity-change revalidation | 4.1 | 3.22; 23.8–23.9 | 20.6–20.7; pinned AAPL identity/lifecycle suite; later AAPL-only route-enable test |
| 5. Base unchanged | 5 | 3.22; 23.6; 23.9 | 20.7–20.10; T3/T7 unchanged-runtime and state-independence proofs |
| 6. sGREEN day-one | 2.3 | 3.22; 23.6.1; 23.9 | 20.6–20.7; M0 chain-native/no-CCIP disposition checks; later deployed deposit/withdraw tests |
| 7. USDG/PSM target and sequencing | 2.3 | 3.22; 23.6.1; 23.9 | 20.6–20.7; M0 canonical-identity and ordering checks; later redemption-first/mint-last tests |
| 8. Stability Pool and RipeGov | 2.3 | 3.22; 23.6.1; 23.9 | 20.6–20.7; M0 route-disposition/Stock-exclusion check; later deployed activation tests |
| 9. Launch LP tokens at zero LTV | 2.3 | 3.22; 23.6.1; 23.9 | 20.6–20.7; M0 external-dependency/route/zero-LTV checks; later exact deployed LP tests |
| 10. USDG route restriction | 2.3 | 3.22; 23.6.1; 23.9 | 20.6–20.7; `check_m0_usdg_not_ordinary_teller_collateral`; later deployed negative-route test |
| 11. CreditRedeem/Underscore exclusions | 2.3 | 3.22; 23.3.E; 23.6.1 | 20.6; M0 negative-route disposition checks; later deployed negative-reachability tests |
| 12. AAPL caps/cardinality/trusted routes | 4.2 | 3.22; 23.7–23.9 | 20.6–20.10; M0 feed/procedure/input/policy checks; later freeze-integer, drift, one-vault, and trusted-route tests |
| 13. Guarded internal settlement | 6 | revised I-04/I-11; 23.1–23.5; 23.7–23.11 | revised I-04/I-11; 20.2–20.5; owner-approved partial-fill, seller-depletion, batch, over-request, failure-atomicity, and unchanged-consumer tests |
| 14. Unacceptable-risk boundary | 6.3 | I-01–I-07; 23.2; 23.7–23.9 | 20.2–20.4; 20.8–20.10; receipt/deficit/payment state-root failure assertions |

## 9. Review checklist and authorization boundary

- [x] All fourteen owner decisions recorded with 24–25 July 2026 provenance.
- [x] AAPL-only Stock set selected.
- [x] Cross-chain, reward, fork, Base, route, cap-target, and settlement
  directions selected.
- [x] Existing raw evidence preserved unchanged.
- [x] M0 remains open.
- [x] M1 remains unauthorized.
- [x] Every already-existing external token that can reach the proposed Teller
  has exact identity and compatibility evidence; future Ripe/LP runtime
  identities are post-M0.
- [x] AAPL feed, price-pin procedure, cap inputs/formula, and review rules are
  frozen; actual pin and cap integers are post-M0.
- [x] CCIP complete-or-disabled policy and seven-day separate-promotion target
  are frozen; sGREEN no-CCIP rule is explicit.
- [x] sGREEN, PSM, Stability, RipeGov, and both LP route dispositions and
  existing external dependencies are frozen.
- [x] File-exact proposed Robinhood/Base state-independence graph is complete;
  actual new deployment addresses/runtime hashes remain post-M0.
- [x] Launch reward disable and incident runbook are review-complete.
- [x] Exact three-contract/file boundary and source-traced plausibility are
  review-complete.
- [x] Partial-fill invariant is owner-confirmed.
- [x] File-exact M1 authorization proposal is ready without beginning M1.
- [ ] Independent reviewer confirms no hard stop was converted into a
  documentation assumption.
- [ ] Owner separately authorizes any exact M1 files after M0 closure.

This packet does not close M0. It does not authorize M1 or any production/live
action.

## 10. File-exact M1 authorization proposal

This is a proposal for a later owner message, not an authorization.

| Field | Exact proposed value |
| --- | --- |
| Slice | `M1 — Teller exact-receipt boundary` |
| Proposed branch/worktree | Fresh `rh-track-8-m1-exact-receipt` worktree |
| Required baseline | The exact reviewed `rh` commit that contains the final integrated M0 package; the owner must insert and approve the full 40-character commit before work starts |
| Only production file | `contracts/core/Teller.vy` |
| Existing tests allowed | `tests/core/teller/test_teller_deposit.py`; `tests/core/teller/test_teller_rebalance.py`; `tests/vaults/test_stock_token_vault_comparison.py` |
| Other test files | None. If the three existing files cannot carry the required cases cleanly, stop and return a revised exact file list before creating a file. |
| Explicitly excluded | Every vault source, `CreditEngine`, `AuctionHouse`, `Deleverage`, interfaces, storage-layout declarations, ABI artifacts, defaults, migrations, manifests, dependencies, CI, and `rh-summary.md` |
| Required reviewers | Protocol accounting, security/reentrancy, Base-compatibility, and independent source/test review |

M1 may implement only ML-01's Teller-side exact receipt proof:

```text
C0 = exact-length pre-transfer custody
C1 = exact-length post-transfer custody
R  = C1 - C0
require Q > 0 and R == Q
require vault result == Q
```

The proposed slice must cover ordinary `deposit`, `depositMany`,
`depositFromTrusted`, `rebalance`, the Teller-held sGREEN route, and
`depositIntoGovVault`; preserve the legitimate Stability Pool trusted
callback; and use a contract-local transient measurement mutex with no public
selector or persistent-storage change.

Stop and return before editing outside the authorized files if the exact
baseline is absent or has drifted; a deposit caller is unenumerated; any
authorized exact-transfer route needs `R!=Q`; the mutex breaks the legitimate
trusted callback; a storage, selector, event, canonical-interface, ABI,
default, migration, manifest, dependency, or Base live-cutover change appears
necessary; a production file other than `Teller.vy` would change; or any
mandatory targeted/full-suite test fails.

M1 exit evidence must include the donation-masking counterexample; zero,
short, fee, excess, reverting, empty, and malformed balance-read atomic
failures; exact receipts on every authorized route; nested-deposit rejection;
trusted-callback liveness; unchanged selector/event/storage/ABI proofs; all
downstream caller regressions; and a clean one-production-file diff. It may not
deploy, configure, activate, or claim the three-contract group is complete.
The owner must separately authorize this exact proposal after M0 closes and
the final M0 integration commit exists.
