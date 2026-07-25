# Track 8 M0 owner-decision packet

**Status:** Draft for owner and independent review. No decision in this file is
approved merely because it is recommended.

**Date:** 24 July 2026

**Planning baseline:** `26eb3a78668d623be40ed2b6e16f52c919906a12`

**Purpose:** Freeze the smallest initial Robinhood Stock Token product graph and
record the owner decisions returned by Track 8 M0. This packet may authorize
only a documentation-only M0 closure revision after all required evidence is
present. It does not authorize M1, production source or test changes, a vault
or VaultBook ID, a default, migration, manifest, deployment, configuration,
signer, transaction, live probe, bridge, reward distribution, or Base cutover.
Vault-implementation selection is deliberately outside M0: the fresh generic
external-only nominal vault is the reviewed minimum-design candidate, but its
source, final name, and VaultBook ID remain later M1 and Track 7 decisions.

## 1. Controlling evidence

This packet must be reviewed with:

- [Track 8 M0 evidence](stock-token-m0-evidence.md), SHA-256
  `a2d118b7729538f984435504412012a10710bb936d36304c774168614a3250fc`;
- [Track 8 M0 sanitized raw evidence](stock-token-m0-raw-evidence.json),
  SHA-256
  `9ea333b4e84330f56c3a3d70e68823cfdba9c37948508e692450e01b3e994cba`;
- [Track 8 minimum-change specification](stock-token-vault-change-specification.md),
  SHA-256
  `71099e629734e7f001a8cbfa40792dfc2ab9fbc5490cd8b9c80a8431a994705c`;
  and
- [Track 8 validation plan](stock-token-vault-change-validation-plan.md),
  SHA-256
  `88edaf44fa375a7310cb73bec254d5801478e89479d51ded0c439f33a9a81bb1`.

If any controlling file changes before approval, update these hashes and
re-review affected decisions. A checked owner decision does not close an
evidence requirement.

For this packet, the single source of truth is the four tracked Git objects at
the planning baseline above, not a historical Track 8 branch or worktree copy.
The pre-approval check must reproduce each hash from the baseline object (for
example, `git show <baseline>:<path>`) or prove that the reviewed working-tree
file is byte-identical to that object.

## 2. What M0 established

M0 established the following without authorizing implementation:

- the exact AAPL proxy passed the integrated pinned-fork transfer-in/out probe,
  and its later live proxy, beacon, implementation, and runtime identities
  remained consistent;
- no other launch Stock Token has an exact, complete repository evidence row;
- the refreshed Base snapshot did not demonstrate an urgent live deficit or
  another launch-blocking reason to migrate Base;
- the current Robinhood/Base state-independence conclusion depends on
  GREEN/RIPE CCIP and every other cross-chain propagation path remaining
  omitted or provably inactive; enabling one requires a new propagation
  analysis and invalidates the present conclusion;
- Stock-backed borrowers and Stock depositors can reach global reward buckets,
  so per-Stock-token zero allocations alone do not disable Stock-linked
  rewards; and
- M0 cannot pass while any enabled token, route, runtime identity, or
  exact-transfer result remains unknown.

## 3. Recommended minimum initial graph

The smallest graph supported by current evidence is an AAPL-first restricted
activation. It keeps every unproved token and optional route inactive rather
than extrapolating from AAPL.

### 3.1 Proposed asset and route freeze

`Pending exact identity` is not an M0 pass. An enabled row must receive its
exact address and required runtime/proxy identities in the M0 closure revision.

| Asset or class | Recommended initial disposition | Allowed initial role or route | Explicitly inactive or omitted | Evidence still required before M0 may close |
| --- | --- | --- | --- | --- |
| AAPL Stock Token — proxy `0xaF3D76f1834A1d425780943C99Ea8A608f8a93f9` | Candidate for initial restricted activation after M1–M5 | Ordinary user deposit/withdraw; collateral borrow/repay; externally delivered liquidation only after the complete containment group passes | CreditRedeem; Stability Pool swap/custody; Deleverage/Endaoment; RipeGov deposit; internal auction settlement; every unreviewed trusted deposit route | Reconfirm exact proxy/beacon/implementation and controls at freeze; compose the selected route with the future M1–M3 implementation; retain separate live-transfer gate |
| Every other Stock Token | Omitted from initial activation unless separately named below | None | Every ordinary and trusted Teller route | Exact proxy, beacon/implementation where applicable, control surface, runtime hashes, decimals, feed, exact-transfer evidence, and route composition |
| GREEN | Chain-local protocol token; not a Teller collateral/deposit asset in the minimum Stock activation graph | Borrow, repay, debt settlement, and other approved core GREEN accounting only | CCIP; unapproved wrapper/deposit conversion; PSM mint/redeem; any generic Teller listing | Final chain-local token identity, exact core route graph, and proof that no inactive route is reachable |
| RIPE | Chain-local governance token with launch rewards globally disabled | Only the governance/role behavior required by the final minimal deployment graph | CCIP; RIPE reward distribution; auto-stake; HR/BondRoom/Stability reward deposit routes unless separately proved necessary | Final token identity and final graph disposition for every RipeGov/Teller consumer |
| sGREEN / SavingsGreen | Omitted from value paths for the initial Stock activation unless H-03 proves an inert topology placeholder is required | None; an inert placeholder, if required, cannot accept value or imply feature enablement | GREEN conversion/deposit; Stability Pool; CreditEngine/CreditRedeem surplus routes; yield/reward paths | Owner selection of omitted versus inert staging, followed by topology and negative-reachability proof |
| USDG / EndaomentPSM | Inactive staging only if required by the final topology; no Stock Teller listing | Price registration or disabled scaffold only if separately approved | PSM mint, redeem, auto-deposit, yield, GREEN mint authority, and generic Teller collateral routes | Canonical USDG identity; final omit/stage choice; disabled-state and no-authority proof |
| Claim, receipt, reward, governance, or other collateral token | Omitted unless named in the final graph | None | Every ordinary and trusted route | Exact identity and full route/economic justification before inclusion |

### 3.2 Exact launch Stock Token set — owner input required

Select exactly one:

- [ ] **Option A — recommended minimum:** AAPL is the only Stock Token eligible
  for initial restricted activation. Every other Stock Token remains omitted
  until it completes a separate M0-compatible evidence row and later release
  approval.
- [ ] **Option B:** AAPL plus the following exact Stock Tokens are required for
  initial activation:

  | Token | Proxy address | Why required on day one | Evidence owner |
  | --- | --- | --- | --- |
  | `PENDING` | `PENDING` | `PENDING` | `PENDING` |

  Add one row for every additional token; the single placeholder row is not a
  one-token limit.

- [ ] **Option C:** Another explicitly bounded launch set:
  `PENDING OWNER TEXT`.

“All Stock Tokens,” a ticker-only list, a UI list, an issuer-level assumption,
or a future address is not a valid selection. Each additional enabled token is
a hard stop until its exact row is complete.

### 3.3 Non-Stock topology — owner input required

For each row, approve the recommended disposition or replace it with an exact
alternative:

| Item | Recommended owner disposition | Owner approval or replacement |
| --- | --- | --- |
| GREEN | Chain-local core token; no CCIP and no generic Teller asset route during initial Stock activation | `PENDING` |
| RIPE | Chain-local governance token; no CCIP and no reward distribution during initial Stock activation | `PENDING` |
| sGREEN / SavingsGreen | Omit value paths; permit only a separately proved inert topology placeholder if H-03 demonstrates it is necessary | `PENDING` |
| USDG / EndaomentPSM | Omit or deploy as a disabled, no-GREEN-authority scaffold; no mint/redeem/auto-deposit/yield/Teller route | `PENDING` |
| Stability Pool Stock custody | Disabled; `shouldSwapInStabPools=false` for every Stock Token | `PENDING` |
| CreditRedeem Stock extraction | Disabled; Stock collateral cannot be redeemed through CreditRedeem | `PENDING` |
| Underscore and Base-only integrations | Omitted | `PENDING` |
| Other token or route | None unless added here with exact disposition and evidence owner | `PENDING` |

### 3.4 Conditional dispositions and M0 closure

No conditional row counts as closed merely because a later track owns it. At
M0 closure:

- every enabled value path must have an unconditional disposition, exact
  address/runtime identity, exact route, and required compatibility evidence;
- an omitted row may close without a deployed address only after the final
  graph proves that no ordinary or trusted route can reach it;
- an inactive-staging row may close only with an exact artifact/address,
  explicit disabled flags and authority, and negative reachability proof; and
- `if H-03 requires it`, `address pending`, `inactive unless needed`, or another
  unresolved condition remains an open M0 stop.

Accordingly, the sGREEN and USDG/PSM rows in Section 3.3 must become
unconditional `omitted` rows with negative proof or exact `inactive staging`
rows with the evidence above. H-03 may supply that evidence after H-02, but M0
cannot claim closure while awaiting it.

### 3.5 AAPL launch exposure caps — owner input required

The initial AAPL route must have exact, finite `perUserDepositLimit` and
`globalDepositLimit` values. These are existing `AssetConfig` fields; this
decision requires configuration and tests, not a new production-contract
surface.

Current source enforces both limits for ordinary non-Department deposits in
`TellerUtils.validateOnDeposit` using the selected vault's reported nominal
`userBalance` and `totalBalance`. A valid Ripe Department depositor returns
before these checks and therefore bypasses both caps. The cap is a meaningful
bound only while every AAPL trusted-deposit route remains disabled or is
separately proved to enforce an equal or tighter bound. M1 must prove that the
selected launch vault's deposit-data getter preserves this ordinary-route
enforcement.

`globalDepositLimit` is compared with the selected vault's `totalBalance`; it
does not sum AAPL across multiple vaults. It is a launch-wide AAPL bound only
if AAPL is registered to exactly one enabled vault. The final configuration
must therefore prove one AAPL vault ID and reject every additional AAPL vault
route, or return a separately aggregated cap design for review.

The stored limits are AAPL base-unit amounts, not USD limits. An initial USD
target is converted using a separately approved price source and pinned price,
but the base-unit cap does not auto-adjust. Its USD-equivalent exposure grows
above the target as AAPL's price rises until a governed configuration change.

### Recommendation

Use a conservative first-release target of **$5,000 equivalent per user** and
**$25,000 equivalent globally**, converted to exact 18-decimal AAPL base units
at the final approved price pin. These targets follow the lower existing Base
configuration pattern; they are proposals, not approved values.

Require an operational review:

- before activation and after any AAPL proxy/beacon/implementation, decimals,
  or price-feed identity change;
- whenever the feed-derived USD value of either stored cap exceeds its
  approved target by more than the owner-selected tolerance; and
- at the owner-selected recurring interval while AAPL remains enabled.

Any cap increase requires a separately reviewed governed configuration change.
An urgent risk response may reduce the caps or disable deposits through the
existing controls, subject to the final governance/runbook evidence.

### Owner decision

| Field | Recommended decision | Owner-approved exact value |
| --- | --- | --- |
| Per-user target at freeze | `$5,000` equivalent | `PENDING` |
| Global target at freeze | `$25,000` equivalent | `PENDING` |
| Approved AAPL price source and pin | Official approved AAPL/USD path at final freeze | `PENDING` |
| Exact `perUserDepositLimit` in 18-decimal AAPL base units | Derived from the approved target and price pin | `PENDING` |
| Exact `globalDepositLimit` in 18-decimal AAPL base units | Derived from the approved target and price pin | `PENDING` |
| USD-drift review tolerance | `10%` | `PENDING` |
| Recurring review interval | `7 days` | `PENDING` |
| AAPL vault cardinality | Exactly one enabled launch vault | `PENDING` |
| Trusted-deposit posture | Every AAPL trusted-deposit route disabled; no cap bypass reachable | `PENDING` |

M0 may record the target, source, tolerance, and interval as owner decisions,
but it cannot pass until the exact activation base-unit values and route
enforcement evidence are present.

## 4. D-M0-02 — initial cross-chain posture

### Recommendation

Keep GREEN/RIPE CCIP and every other cross-chain token, custody, or message route
omitted or provably inactive through initial Stock activation.

### Consequence

This preserves chain-state independence and avoids making the Stock launch
depend on the unresolved Chainlink/CCIP work. GREEN and RIPE supply and
liquidity remain chain-local, so users cannot bridge them at initial
activation. Selecting this posture removes CCIP from the Stock-launch critical
path; CCIP remains a separately gated later release.

### Owner decision

- [ ] **Approve the recommendation.**
- [ ] Require an initial cross-chain route and return M0 to owner/security
  review. Exact route: `PENDING`.

## 5. D-M0-03 — day-one rewards

### Recommendation

Use global launch disablement:

- `arePointsEnabled=false`;
- `ripePerBlock=0`; and
- no funded or mintable launch reward distribution.

Do not rely only on per-Stock-token allocations. Under current source, a
Stock-backed borrower can reach the global borrower bucket, and a Stock
depositor with zero staker allocation can reach the generic-depositor bucket.

### Consequence

No Stock or non-Stock user earns launch points or RIPE until a later,
separately approved reward release. This sacrifices early incentives in return
for avoiding untracked Stock-linked rewards during issuer loss or custody
failure.

### Owner decision

- [ ] **Approve global launch disablement.**
- [ ] Require non-Stock-only rewards and return an exact allocation table for
  review.
- [ ] Require Stock-linked rewards, which stops M0 and reopens reward-loss
  attribution and incident behavior.

## 6. D-M0-04 — AAPL fork-refresh sufficiency

### Recommendation

Accept the integrated immutable RH-T2-01 AAPL fork result together with
RH-M0-01's later matching identity evidence for M0. Preserve the failed fresh
archive-provider attempt as an explicit limitation.

### Consequence

This avoids delaying M0 for another archive provider, but it accepts that the
historical behavior was not freshly rerun during M0. It does not approve a live
AAPL transfer, future implementation behavior, or activation after an
implementation/beacon change.

### Owner decision

- [ ] **Accept the existing fork plus current identity match for M0.**
- [ ] Require a fresh archive-capable rerun before M0 closure.

## 7. D-M0-05 — Base sequencing and residual risk

### Recommendation

Approve Robinhood-first sequencing and leave current Base runtimes unchanged.
Accept that the M0 snapshot did not demonstrate an urgent live Base
vulnerability while preserving the known legacy risks:

- legacy receipt accounting;
- custody-backed credit/health behavior;
- internal settlement behavior; and
- incomplete per-asset forward-cutover fork evidence.

### Consequence

This avoids a risky stateful Base migration as a Robinhood-launch dependency.
Base does not receive the future Robinhood containment changes and retains
those latent mechanisms. Any new Base deficit, short receipt, exposed
debt/auction, or exploitable mismatch must reopen this decision.

### Owner decision

- [ ] **Approve Robinhood-first and unchanged Base with the stated residual
  risks.**
- [ ] Reject and return Base sequencing to owner/security review. This does not
  authorize a Base migration.

## 8. D-M0-06 — future Base cutover

### Recommendation

Confirm that neither M0 nor the Robinhood launch approves a future Base
cutover. Any Base proposal requires separate per-asset route evidence,
implementation/control refresh, borrower and auction enumeration, migration
design, security review, and owner authorization.

### Owner decision

- [ ] **Approve the recommendation.**
- [ ] Alternative: `PENDING OWNER TEXT`.

## 9. D-M0-07 — next authorization boundary

After Sections 3–8 are resolved, exact enabled-token identities and route
evidence are complete, and an independent reviewer approves the revised
evidence, the next permitted action is only:

1. update the M0 evidence with the exact owner decisions and final matrix;
2. identify any remaining evidence hard stop;
3. mark M0 passed only if every hard stop is actually closed; and
4. return a separate, file-exact M1 proposal for owner and security review.

### Owner decision

- [ ] Authorize a **documentation-only M0 closure revision** after independent
  review confirms the final matrix and evidence.
- [ ] Do not authorize any revision yet.

This decision does not authorize M1. If M0 passes, the owner must separately
decide the six mechanism/risk items in Track 8 specification Section 23.11 and
then separately authorize exact M1 files.

## 10. Consolidated residual-risk acceptance

Approving the recommendations means the owner understands and accepts:

- AAPL retains issuer pause, blocklist, administrative burn, multiplier, and
  upgrade risk;
- exact-transfer behavior at one pinned identity is not a guarantee after an
  issuer implementation change;
- issuer loss can freeze an affected Stock asset and strand debt while
  repayment must remain available;
- the initial product is deliberately narrow and excludes unproved Stock
  Tokens and optional routes;
- CCIP inactivity causes chain-local GREEN/RIPE supply and liquidity;
- global reward disablement removes incentives for all launch users, not only
  Stock users;
- unchanged Base retains the explicitly documented legacy mechanisms; and
- M0 evidence cannot substitute for M1–M5 implementation, audit, testnet,
  migration, configuration, or activation gates.

The owner is **not** accepting phantom collateral after custody loss,
first-withdrawer capture, or zero-backed internal settlement that charges
GREEN and reduces debt as launch behavior. Those are protocol-side defects
that the complete M1–M3 containment group must close before AAPL activation.
If the implementation or validation cannot prove those closures, AAPL remains
disabled.

## 11. Approval form

The owner should not sign this form until every selected option and every
`PENDING` field in the approved graph is resolved.

> I approve the Track 8 M0 product-freeze decisions recorded in
> `docs/chains/rh/track-8-m0-owner-decision-packet.md` at its reviewed SHA-256.
> I select launch Stock Token option `[A/B/C]` and approve the completed asset
> and route table, including exact AAPL activation caps, review triggers, and
> disabled trusted-deposit routes. I approve `[inactive/required]` initial cross-chain routes,
> reward option `[1/2/3]`, AAPL evidence option `[accept/rerun]`,
> `[Robinhood-first/Base-review]` sequencing, and the separately gated future
> Base-cutover policy. I accept the residual risks in Section 10. After
> independent review and completion of every exact identity/evidence field, I
> authorize only a documentation-only M0 closure revision. I do not authorize
> M1, a production contract or test change, a vault or registry ID, a default,
> migration, manifest, deployment, configuration, signer, transaction, live
> probe, bridge, reward distribution, or Base cutover.

## 12. Review and completion checklist

- [ ] Exact launch Stock Token set selected.
- [ ] Every enabled token has an exact address and required runtime identities.
- [ ] Every enabled token has route-exact transfer compatibility evidence.
- [ ] Every non-Stock token and route has an explicit disposition.
- [ ] No enabled or inactive-staging row remains conditionally specified.
- [ ] Exact AAPL activation caps, price pin, review triggers, and ordinary-route
  enforcement are approved and evidenced.
- [ ] AAPL is registered to exactly one enabled launch vault, or a separately
  approved aggregate-cap mechanism exists.
- [ ] Every AAPL trusted-deposit route is proved disabled or separately bounded.
- [ ] Cross-chain posture approved.
- [ ] Reward posture approved.
- [ ] AAPL evidence sufficiency approved.
- [ ] Base sequencing and residual risks approved.
- [ ] Future Base cutover remains separately gated.
- [ ] Independent reviewer confirms no hard stop was converted into a
  documentation assumption.
- [ ] Owner approval cites the reviewed packet hash.
- [ ] Only a documentation-only M0 closure revision is authorized.
- [ ] M1 and all production/live actions remain unauthorized.
