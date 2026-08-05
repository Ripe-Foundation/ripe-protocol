# Robinhood reassessment and qualification synthesis

**Synthesis date:** 1 August 2026

**Repository baseline:** `5f5d22b7ee78cbb904c4fe3c6e46599c330c4353`

**Repository tree:** `7454b5456ebb6cd02d716a64b408629ab501629e`

**Scope:** current program synthesis, including the bounded launch-pricing
Curve amendment

**Lifecycle effect:** repository configuration, validation, tests, and handoff
only; no deployment, migration execution, production configuration,
activation, release, RPC, account, signer, Sites, or external-state action

## 1. Purpose and authority

This document consolidates eight independently prepared reassessment and
qualification reports into one Robinhood program package. It does not create
eight implementation trains. The source reports remain complete, byte-identical
evidence; this synthesis reconciles their controlling owner dispositions,
separates lifecycle phases, and defines a small number of future packages.

The source reports are:

### Reassessment

- [Ledger chain-abstraction reassessment](reassessment/ledger-chain-abstraction.md)
- [Teller balance and receipt measurement reassessment](reassessment/teller-balance-measurement.md)
- [GuardedErc20 vault architecture reassessment](reassessment/guarded-erc20-vault-architecture.md)
- [Robinhood Uniswap price-source decision](reassessment/uniswap-price-source-decision.md)

### Qualification

- [Robinhood Curve and Profile 2 qualification](qualification/curve-profile2-qualification.md)
- [Robinhood PSM, reserve, and launch-liquidity activation proposal](qualification/psm-liquidity-activation.md)
- [Robinhood network, token, clock, and oracle qualification authority](qualification/network-token-oracle-authority.md)
- [Robinhood fork-suite coverage census and implementation design](qualification/fork-suite-coverage-census.md)

Subsequent decision/evidence record (does not rewrite the eight source reports):

- [Robinhood PSM lite-permission split decision and evidence](reassessment/psm-lite-permission-split.md)
- [Robinhood Curve launch activation](curve-launch-activation.md)

The Curve launch-activation record supersedes the earlier Profile 1/Profile 2
boundary only for the exact launch-pricing topology it names. The copied source
reports and hashes below remain historical evidence; their claims that
PriceDesk ID 2 is empty or that all Curve use belongs to Profile 2 are no
longer current.

**Fork-census provenance:** intermediate corrected-report revision
`cd13c3028315784b6a48de097b95529e18ee8d0695f7cd3eca5d6f6fcae6038c`
was a pre-disposition revision and was not durably archived. The owner has
re-attested option 1 against final durable artifact
`103850c1c434e7f5e1836b9340e21ab3dac07c1cf0861727cfb0e7e45222ecd9`,
which is the sole controlling census artifact. The historical v1 archive
remains preserved but is superseded and non-controlling.

Where a report's exploratory text differs from its later controlling owner
disposition, the controlling disposition governs. Where a report proposed a
future task that is explicitly deferred here, the deferral governs current
program sequencing without rewriting the report.

The copied-report byte identities are:

| Repository report | SHA-256 |
| --- | --- |
| `reassessment/ledger-chain-abstraction.md` | `7970f9bb2b921629a0b4dad1631f9ddcd4773ac362ec4974d10073420aec4361` |
| `reassessment/teller-balance-measurement.md` | `b8227f76644ac5b249d34e2ca4dd61c58d12b8f21b883411eea2c9ddcab5113d` |
| `reassessment/guarded-erc20-vault-architecture.md` | `a77cd01bbd6df2262469cbd8a093308cc294330bd0f94519c9be542402c19251` |
| `reassessment/uniswap-price-source-decision.md` | `d7057fb3c3e27d7b80d70850459b6ecafb5583447f0c12e1bf9d052a1467a622` |
| `qualification/curve-profile2-qualification.md` | `8d450a8a27618553f3dd3d5cdb10fa07bfc7fe6fe43414b77d4e1e867151f102` |
| `qualification/psm-liquidity-activation.md` | `98b8eace88c19fe6e5077bacb94ee96ad7157f6264b710c1bb4f2c81bfa799a4` |
| `qualification/network-token-oracle-authority.md` | `46e25a6d7f4ff289a8c3773f9533bc29a95472d84622342e1374b3f7e841ab84` |
| `qualification/fork-suite-coverage-census.md` | `103850c1c434e7f5e1836b9340e21ab3dac07c1cf0861727cfb0e7e45222ecd9` |

## 2. Consolidated disposition

### Accepted architecture

1. Preserve the current shared Ledger architecture and its exact-length
   `raw_call` boundary. Do not create `LedgerRh.vy`, add a runtime provider,
   add `chain.id` dispatch, or change the Ledger contract for launch.
2. Preserve Teller's current balance-measurement design:
   strict exactly-32-byte custody reads, the global transient
   `receiptMeasurementActive` mutex, exact destination-custody delta, and exact
   vault-return equality.
3. Keep `GuardedErc20` separate and Stock-specific. Do not backport its behavior
   into Simple, Basic, Shares, VaultData, RipeGov, StabilityPool, or `Vault.vyi`;
   do not add a mutable guarded mode or token adapter.
4. Preserve auction-only liquidation initiation for Guarded Stock, external
   delivery as the default settlement, exclusive Guarded assignment, and
   Stock rewards disabled.
5. Retain the owner-approved PR #66 general RIPE reward values and shared
   `1,000 RIPE` budget, including accepted Stability competition and zero
   theoretical minimum runway. DP15 and P-H04-399 are approved; checkpoints,
   identities, runbook operations, monitoring, H-05/H-06/H-08/H-09, rehearsal,
   deployment, activation, and release stay gated. Stock rewards remain
   disabled.
6. Use the bounded launch-pricing profile. PriceDesk ID 1 has Chainlink
   selected, ID 2 has unchanged `CurvePrices` selected, ID 3 has
   BlueChipYield selected, and IDs 4 and 5 are empty. Priority price-source
   IDs remain `[1, 3]`. ID 2 is used only for GREEN through the candidate
   GREEN/USDG pool; USDG has no Curve feed. Dynamic rates, Teller reference
   snapshots, and the Curve stabilizer remain inactive.
7. Keep Chainlink as the sole USDG and PSM price authority. The GREEN route is
   GREEN -> Curve GREEN/USDG -> PriceDesk -> Chainlink USDG, with no recursion.
   BlueChipYield remains the selected yield-token route. Uniswap is not a
   launch fallback.
8. Do not build or register a Uniswap price-source contract at launch.
9. RIPE/WETH V2 is at most an externally held launch-liquidity canary. It is
   not a protocol oracle and its LP token is not admitted at launch.
10. Do not create a launch GREEN/USDG Uniswap pool. A GREEN/USDG Curve pool is a
   bounded launch-pricing candidate whose production address, funding,
   custody, slippage, withdrawal, and operating controls remain blocked.
11. Neither the RIPE/WETH LP token nor the GREEN/USDG Curve LP token is
    admitted at launch. The pricing venue does not imply LP collateral,
    oracle, custody, or stability admission; both LP admissions require
    separate authority.
12. Preserve the shared `EndaomentPSM` architecture with canonical USDG as the
    sole reserve asset, no yield position, disabled user directions, no
    effective GREEN-mint authority, and a redemption-first canary sequence.
13. H-09 owns the opt-in read-only archive-fork qualification lane. Network is
    disabled by default. H-10 separately owns live testnet rehearsal and every
    real transaction, signer/account, persistent deployment, or operational
    action.

### Items requiring no contract change

| Area | Current disposition | Work that may still be required |
| --- | --- | --- |
| Ledger | Preserve current contract and ABI | Deployment/profile binding, immutable readback, negative tests, authentic clock/receipt qualification, replay, monitoring |
| Teller | Preserve current contract, strict read, mutex, and equality checks | Release-gate test matrix, current rationale update, exact token/proxy qualification |
| GuardedErc20 | Preserve separate specialized contract and existing ABI | VaultBook/asset binding, deployment policy, composed-route tests, monitoring and incident procedures |
| Uniswap launch oracle | No contract at launch | Off-chain monitoring and separately approved pool/custody operations only |
| Curve launch pricing | Unchanged `CurvePrices`, selected at ID 2 for GREEN only | Bind verified official identities and pool deployment/operations; prove exact route, fail-closed behavior, and inactive higher powers |
| PSM architecture | Reuse shared contract | Later configuration, funding, qualification, and activation work under separate authority |
| H-09 architecture | No production-contract change | Future test/evidence package after owner APIs and external inputs exist |

The absence of a contract change does not make the operational or evidence
gates optional.

## 3. Launch requirements

Launch remains gated. None of the requirements below has been satisfied merely
by accepting this synthesis.

### Profile and market topology

- Bounded launch-pricing profile only.
- PriceDesk ID 1 has Chainlink selected.
- PriceDesk ID 2 has unchanged `CurvePrices` selected.
- PriceDesk ID 3 has BlueChipYield selected.
- PriceDesk IDs 4 and 5 are empty.
- Priority price-source IDs are `[1, 3]`.
- Chainlink remains the sole USDG and PSM authority. GREEN alone uses
  GREEN -> Curve GREEN/USDG -> PriceDesk -> Chainlink USDG. USDG has no Curve
  feed, so the route cannot recurse. BlueChipYield provides the selected
  yield-token route.
- Deploy/register `CurvePrices` at ID 2 only after the typed address,
  constructor, pool, artifact, and operating blockers close.
- No Uniswap price-source deployment or registration.
- The GREEN/USDG Curve venue is pricing-only. Its LP token is not admitted and
  its deployment, funding, custody, slippage, withdrawal, observation, and
  incident inputs remain blocked.
- Any RIPE/WETH V2 canary remains externally held, operationally monitored,
  separately funded, and outside Ripe custody and valuation.
- Neither LP token is admitted.
- Any later LP admission retains `SimpleErc20`, `ltv=0`, no PriceDesk feed, and
  complete negative reachability until separately activated.

### Chainlink and external identity

- Freeze exact chain/profile, feed proxy/aggregator, token, decimals, heartbeat,
  stale-time, round, implementation, and admin identities.
- Use a nonzero stale policy with an accepted operating margin. The
  `86,400`-second USDG value is a ceiling/candidate, not accepted production
  policy because it currently has no publisher-lateness margin.
- Bind a truthful Robinhood sequencer/finality outage policy. Prefer an
  official accepted Chainlink sequencer feed if one exists; otherwise require
  an explicitly approved operational gate. Do not invent an address.
- Keep Stock/equity oracle activation outside the initial packet unless Stock
  is explicitly reopened with its separate 24/5, multiplier, corporate-action,
  token, and accepted-round evidence.

### Ledger, Teller, and Guarded evidence

- Bind Ledger's exact `0x64` Robinhood source through a mandatory
  deployment/profile gate and immutable readback.
- Under separately authorized read-only fork execution, prove authentic
  ArbSys/receipt clock behavior and the required child/L1/EVM/timestamp
  relationships.
- Close Teller's controlling release-gate matrix without changing Teller:
  vault authorization, legacy-clamp closure, callback/reentrancy cross-product,
  withdrawal responsibility, balance-return policy, and nested rejection.
- Bind Guarded to a distinct approved VaultBook slot and exact qualified Stock
  asset; prove exclusive assignment, auction-only configuration, rewards-off
  posture, composed liquidation, loss/restoration/surplus behavior, and
  monitoring/incident controls.

### PSM disabled/canary-first posture

- Deployment and registration, if later authorized, begin fully disabled.
- Chainlink is the sole USDG price authority. ID 2 may price GREEN through the
  GREEN/USDG pool, but USDG itself has no Curve feed.
- Yield remains `(0, zero)`, auto-deposit is disabled, and Underscore remains
  zero.
- Both user directions and effective GREEN mint authority remain disabled
  through preparation.
- Qualification candidates such as `100,000 USDG`, `10/0` bps fees,
  `25,000/50,000 GREEN` interval caps, `7,200` blocks, enforced allowlists, and
  operational per-actor limits are not frozen production values.
- Prove pre-production redemption before any mint authority, disable redemption
  again, then require separate production-activation authority.
- In production activation, prove redemption first; mutate the PSM HQ tuple
  last among capability rows and global minting last overall.
- PSM reserve stays inside the PSM and is never launch-liquidity capital.
- Public access requires a separate decision after at least seven completed
  use-anchored intervals and the full reconciliation, reserve, incident,
  oracle, and circulating-GREEN evidence gate.

### Operational readiness

- Finalize immutable manifests, exact artifacts, constructor packets, role
  maps, monitoring, pause/recovery procedures, custody, and signer ceremony.
- Close the H-07 artifact interface and H-08 topology/assertion interface before
  H-09 implementation.
- Complete an H-09 safe-default/offline package before any opt-in archive-fork
  qualification.
- Execute H-10 live rehearsal only under fresh exact authority naming network,
  plan, endpoint, accounts, signers, funds, commands, evidence, and stops.
- Deployment, configuration, activation, release, and role transfer each remain
  separate later approvals.

## 4. Post-launch Curve higher powers and LP requirements

The bounded GREEN pricing route is part of launch. Every other Curve power and
every LP admission is a separately promoted follow-on.

| Stage | Capability | Required boundary |
| --- | --- | --- |
| P2-A | Production observation and bounded launch-route qualification | Exact ID-2 GREEN route only; no dynamic rate, Teller snapshot, Endaoment, PSM, LP, or broader feed authority |
| P2-B | Later additional Curve feeds or consumers | Separate per-asset and per-consumer approval; USDG remains Chainlink-only unless explicitly changed |
| P2-C | Promote optional snapshot or reference consumers | Exact clock, staleness, incident-disable, and consumer-specific approval |
| P2-D | Enable dynamic-rate parameters | Accepted P2-C soak, risk parameters, caps, repeated/jump clock tests, emergency disable |
| P2-E | Enable Endaoment stabilization | Exact roles, GREEN cap, liquidity/custody, profit/slippage, pool-admin, pause and recovery evidence |

The launch pool research candidates are
`ma_exp_time=600`, `stabilizerAdjustWeight=5_000`, and
`staleBlocks=7_200`. Required alternative fork vectors are
`ma_exp_time=866` and `stabilizerAdjustWeight=7_500`. These are qualification
candidates, not deployed configuration. `staleBlocks=0` and copied Base
`43_200` are rejected.

The follow-on lane owns:

- any GREEN/USDG use beyond the bounded launch-pricing route, plus broader
  liquidity/custody and staged protocol use;
- both LP-token admissions, each with `ltv=0`, no PriceDesk feed, complete
  valuation-negative proof, and separate activation;
- unchanged `CurvePrices` using the deliberately accepted L1-derived EVM
  `NUMBER` semantics, subject to full repeated-number and jump qualification;
- any Teller snapshots, dynamic-rate production, or Endaoment stabilization;
  and
- promotion beyond the launch route after the launch incident-disable, repair,
  and guarded re-enable runbook has been qualified.

Failure at any stage leaves or returns the system to the last accepted stage.
Passing fork tests does not deploy, register, configure, activate, or release
any launch or follow-on capability.

## 5. Explicitly deferred work

The following work is outside the current queue and is nonblocking unless an
owner explicitly reopens it:

1. **CreditEngine zero-backing reassessment.** Preserve integrated behavior and
   historical evidence. Do not design, remediate, review, or schedule new
   zero-backing policy.
2. **Every Deleverage task.** This includes contract work, parameter/control
   representation, configuration, tests, fork scenarios, documentation
   refreshes, bytecode size or EIP-170 headroom work, deployment planning, and
   operational work. Preserve current zero values and historical evidence.
3. **Uniswap V2 candidate admission.** The old cumulative-price design and
   implementation are deleted. The smaller `UniswapV2Prices` spot/snapshot
   candidate exists under separate owner instruction, but no PriceDesk row,
   deployment, or security-relevant DEX price belongs in launch.
4. **CCIP.** Keep disabled and preserve historical evidence without new
   research, implementation, testing, packaging, testnet, or production work.
5. **Sites recovery and dashboard publication.** Preserve provenance; do not
   recover access, create a replacement project, save/deploy a version, publish,
   or change access.
6. **Live deployment.** No testnet or production deployment, configuration,
   migration execution, funding, registration, activation, role transfer,
   signing, broadcast, or release is authorized.

The fork census's provisional 33-path ceiling includes
`tests/deployment/fork/lifecycle/test_deleverage.py`. That report also states
that the ceiling is planning-only and must be sealed by H-09. Because every
Deleverage task is now deferred, the future H-09 ledger must be resealed before
implementation and must not implement or execute the Deleverage lane unless an
explicit owner reopening changes this disposition.

## 6. Future implementation packages

Future work should be reviewed as several large packages, not split into one
micro-task per report or finding.

### Package A — shared-contract release-gate evidence

One test-and-documentation wave for unchanged Ledger, Teller, and GuardedErc20:
deployment/profile negatives, authentic-clock hooks, critical-route rollback,
Teller vault/callback/return matrices, Guarded deployment/topology/loss
matrices, artifact ceilings, and current rationale links. It must not edit
production contracts, interfaces, ABIs, migrations, or configuration.

Deleverage-specific work is excluded while deferred. Existing composed evidence
may be cited, but no new Deleverage test, size, parameter, or documentation task
is part of this package.

### Package B — immutable external-input and artifact closure

One owner-bound H-07/H-08 package for network pins, archive-provider receipt,
fork-engine clock capability, canonical WETH/USDG, GREEN/RIPE/sGREEN artifacts,
Chainlink/sequencer packets, Curve graph, pool/custody identities, PSM
parameters/roles, topology assertions, allowed state deltas, and failure codes.
It is offline preparation and must fail closed on every missing owner field.

### Package C — H-09 safe-default and archive-fork qualification

One H-09-owned package under `tests/deployment/fork/**` after Packages A and B
and all owner APIs exist. Ordinary collection is network-disabled. Archive-fork
mode is affirmative opt-in, read-only against Robinhood, uses no real signer,
permits mutation only inside a disposable local fork, writes reproducible
evidence outside the repository, and proves destruction plus replay.

The provisional 33-path decomposition is a ceiling candidate, not an
implementation grant. H-09 must reseal its final paths, nodes, stop codes, and
verdict vocabulary, with Deleverage excluded unless reopened. The maximum
result remains non-authoritative `LOCAL_FORK_QUALIFIED`.

### Package D — launch deployment-preparation and PSM canary

One later configuration/operations package for exact launch bindings,
Chainlink USDG authority, the bounded GREEN Curve route, the selected BlueChipYield route, disabled
PSM preparation, reserve/custody decisions, redemption-first qualification,
monitoring, incident controls, and a restricted activation packet. It begins
only after exact machine, manifest, role, feed, token, and operator inputs exist.
It does not combine preparation, qualification, and production activation into
one authority.

### Package E — post-launch Curve higher powers and LP integration

One staged package for capabilities excluded from the bounded launch route. It
covers additional Curve feeds or consumers, optional dynamic rates, optional
Teller snapshots, optional stabilizer use, and later LP admissions. No stage is
implied by acceptance of the previous stage.

UniswapV2Prices hardening, admission, and deployment remain excluded while
deferred.

### Package F — H-10 live rehearsal and operational release

One separately authorized live-rehearsal package for testnet transactions,
external signers/accounts, persistent rehearsal artifacts, operator runbooks,
monitoring, failure/rollback evidence, and later restricted-release
preparation. It consumes H-09 evidence but does not inherit H-09 authority.
Production deployment and activation remain later exact approvals.

## 7. Resolved owner decisions

The consolidated owner decisions no longer open for this program slice are:

- preserve current Ledger architecture and raw-call boundary;
- preserve current Teller strict balance-measurement design and global mutex;
- preserve GuardedErc20 as a separate Stock-specific vault;
- use the bounded Curve pricing topology at launch and stage every higher power
  and LP admission as follow-on;
- keep Chainlink as sole USDG and PSM authority, with PriceDesk ID 1 selected;
- select BlueChipYield at PriceDesk ID 3 for the yield-token pricing route,
  select unchanged `CurvePrices` at ID 2 for GREEN only, keep IDs 4 and 5
  empty, and use priority price-source IDs `[1, 3]`;
- deploy no Uniswap price-source contract at launch;
- treat RIPE/WETH V2 only as an optional externally held liquidity canary;
- create no launch GREEN/USDG Uniswap venue;
- keep both LP admissions outside launch and separately gated;
- keep `CurvePrices` unchanged;
- use a disabled, allowlisted, redemption-first PSM canary posture;
- keep PSM reserve separate from DEX liquidity;
- keep H-09 network-disabled by default with explicit opt-in read-only archive
  qualification; and
- keep H-10 as the separate live-rehearsal owner; and
- use the exact PR #66 initial-launch reward values with one shared 1,000-RIPE
  Lootbox/Stability budget; accept an approximately 15.432-day emission-only
  runway, Stability claims shortening it, and a zero theoretical minimum; and
  select no Stability reserve, separate budget, redesign, or launch disablement.

Reopening one of these decisions requires an explicit owner action and does not
by itself authorize implementation or a later lifecycle phase.

The owner exercised that reopening authority for both LP launch admissions on
1 August 2026. The independent qualification in
[`qualification/lp-launch-admission.md`](qualification/lp-launch-admission.md)
reaffirmed no LP-token protocol admission on fresh source-path evidence: the
GREEN/USDG pool and bounded GREEN pricing route are selected launch work, but
its LP token remains excluded; RIPE/WETH remains only a conditional externally
held V2 canary. This is a new qualification decision, not reliance on the
earlier no-admission conclusion. It changes no Defaults LP row, PSM,
Deleverage, Uniswap-accounting, deployment, or activation state. The negative
LP-admission result follows from missing verified facts, owner controls, and
shared-path safety properties. No LP token is configured, registered, held as
a Ripe asset, admitted, or active, and the selected GREEN/USDG pool remains
undeployed and unfunded. Owner, external, implementation, fork, and security
work may explicitly reopen a future result without authorizing it.

## 8. Remaining external inputs and residual decisions

### Network and fork

- final signed per-profile packet and owner identities;
- exact mainnet/testnet block, hash, parent, state root, timestamp, finality,
  L1, adjacent-header, and representative receipt evidence;
- approved archive-provider identity/fingerprint and read-only capability
  receipt, with secrets external;
- exact fork engine/version and proof of child/L1/EVM/NodeInterface/ArbSys
  clock fidelity; and
- final H-07, H-08, and H-09 APIs, schemas, path/node ceilings, evidence
  destination, stop codes, and verdict vocabulary.

### Tokens and artifacts

- pinned WETH and USDG proxy/implementation/admin/runtime/source/layout and
  behavior evidence;
- compiler-derived USDG slot/getter proof, exact positive overlay `Q`,
  deterministic actor, two-write set, unchanged set, and destruction rollback;
- final GREEN, RIPE, and sGREEN constructors, supplies, recipients, artifacts,
  deterministic addresses, and direct-deployment proof; and
- exact Guarded VaultBook ID/name and final Stock token/control identities.

### Oracle and sequencer

- exact Chainlink constructor packet, feed proxies/aggregators, accepted rounds,
  decimals, BTC disposition, timelocks, and nonzero stale values;
- a stale policy with accepted publisher-lateness margin;
- accepted Robinhood sequencer signal or explicit combined operational policy;
  and
- monitoring, pause, escalation, grace, fresh-round, and recovery authority.

### Liquidity, Curve, and follow-on powers

- final Curve source/artifact graph and current onchain graph at an approved
  pin;
- exact GREEN/USDG pool identity or creation route, coin order, parameters,
  implementation, LP identity, admin, funding, custody, slippage, withdrawal,
  and monitoring;
- RIPE/WETH canary factory/router/pair, initialization, budget, custody,
  approvals, retained reserves, trade/slippage limits, unwind, and incident
  owners if the optional pool proceeds; and
- closure of every typed launch-pool blocker before the bounded route is
  deployment-ready, plus separate owner approvals for each later feed,
  consumer, P2-C, P2-D, P2-E, and LP-admission promotion.

### PSM and operations

- accepted production reserve, fees, caps, interval, actor, allowlist,
  circulating-GREEN, and reserve-coverage values;
- governance, treasury, recovery, liquidity, monitoring, response-time, and
  incident identities;
- final SavingsGreen availability/omission binding;
- final token/oracle/sequencer evidence and pre-production redemption proof;
  and
- separate exact testnet, production, configuration, funding, activation, and
  release authorities.

No public candidate, report literal, Base value, symbol, placeholder, current
chain tip, or mock result may fill one of these inputs by inference.

## 9. Current lifecycle statement

This package records accepted architecture, requirements, deferrals, and future
program shape. It copies no report conclusion into contract, interface, ABI,
migration, configuration, generator, test, Sites, or external state.

At this synthesis baseline:

- no Robinhood deployment has occurred;
- no Robinhood migration has been executed;
- no production configuration or registration has occurred;
- no pool has been created or funded by this program;
- no PSM reserve has been funded;
- no Curve launch-pricing or follow-on capability has been deployed or
  activated;
- no testnet or production rehearsal has occurred;
- no account, key, signer, Safe, RPC endpoint, or transaction was used; and
- no production activation or release has occurred.

Passing documentation, local tests, or a future H-09 archive-fork suite can at
most provide evidence for the next owner gate. It cannot authorize deployment,
configuration, activation, migration execution, or release.
