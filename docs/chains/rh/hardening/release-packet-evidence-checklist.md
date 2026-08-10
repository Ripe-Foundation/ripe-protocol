# RH release-packet evidence checklist

> **31 July 2026 currentness:** Ready to begin deployment preparation. Any
> future packet must bind current configuration-source baseline
> `e4473ce6485888f1b747761a5ee8693443108877`, tree
> `33b705690007bda9b11900b5775bd9230e79f09e`, the documentation authority
> derived from its committed bytes, H-04 source authority,
> H-05 deterministic planning reports, and the final H-06 operator
> machine/volume. Historical checkpoints are not present branch authority.
> `DefaultsRobinhood.vy` exists and compiles; the packet must fail closed while
> deployment readiness is false or while `fullPayoffBuffer`, `overageBps`,
> `dustThreshold`, and `dustBps` lack
> machine-facing Robinhood parameter/planning representation. All four values
> remain zero and deferred. No Robinhood migration, deployment, production
> configuration, activation, RPC, account, key, signer, or release action has
> occurred. Repository configuration is prepared and consistent;
> production/onchain configuration has not occurred. Use this checklist only
> after reaching the release-evidence phase in the canonical
> [`../deployment-owner-quickstart.md`](../deployment-owner-quickstart.md).

> **DRAFT — reusable offline checklist.** Completing this file does not approve,
> sign, publish, deploy, configure, activate, or release anything. Adoption into
> the actual release process is **UNRESOLVED — owner decision**.

## 1. Snapshot identity

- [ ] Record the exact 40-hex baseline commit, release commit/tree, branch,
  worktree, and clean status; the hardening baseline demonstrates the required
  identity fields
  ([BASELINE.md](BASELINE.md)).
- [ ] Record every source/artifact path and SHA-256 used by the packet; the S1
  expectation file separates per-contract source, optimization mode,
  creation/runtime artifacts, layout, and integrity
  ([contract-artifact-expectations.json](../../../../config/contract-artifact-expectations.json)).
- [ ] Record the exact interpreter, Vyper version, dependency manifest/hash,
  compiler command, environment variables, and cache isolation; the hardening
  baseline pins the environment and the S1 checker pins source-governed
  compilation
  ([BASELINE.md](BASELINE.md),
  [check_contract_artifacts.py](../../../../scripts/check_contract_artifacts.py)).
- [ ] Pin every command exactly, including selection paths, plugins/options,
  environment unsets, temporary directories, and working directory; the
  mutation protocol requires same-process isolated execution for mutation
  claims
  ([mutation-evidence-protocol.md](mutation-evidence-protocol.md)).

## 2. Snapshot-specific counts and labels

- [ ] Regenerate counts from the release snapshot; never copy a prior count
  into a current label. The historical S5 result is **69 tests**, while the
  reviewed current Ledger record labels **95 tests**; the record explicitly
  prohibits rewriting 69 as 95
  ([ledger.md, recommended hardening](../smart-contract-changes/ledger.md#recommended-hardening),
  [ledger.md, independently reproduced audit evidence](../smart-contract-changes/ledger.md#independently-reproduced-audit-evidence)).
- [ ] Label the current block-clock inventory independently. At the present
  hardening snapshot the checker/test requires `vyper_paths=95`; the inventory
  document separately reports 95 matching production lines, 100 occurrences,
  and 17 files for its dated snapshot
  (`test_block_clock_inventory.py:124`,
  [block-number-inventory.md, exact occurrence coverage](../block-number-inventory.md#exact-occurrence-coverage-ledger)).
- [ ] For every pytest invocation record passed, failed, skipped, xfailed,
  xpassed, warnings, errors, and deselected counts exactly as emitted; do not
  infer absent categories from a green exit code.
- [ ] Assign an independent reviewer to spot-audit every value that exists only
  in the narrative report. Resolve each claimed commit with
  `git rev-parse --verify <hash>^{commit}` and reproduce sampled counts,
  medians, and digests from the preserved command output or source recipe
  before accepting the packet.
- [ ] Record the configured deselection list/version and compare actual
  deselections item-by-item; any unconfigured deselection is an anomaly
  requiring the aggregate-failure protocol.
- [ ] Label every result `historical`, `current release snapshot`, `local
  reproduction`, `fork`, or `live`; the Ledger artifact generator explicitly
  labels its output local reproduction rather than deployment evidence
  ([build_ledger_artifact_bundle.py:1-7](../../../../scripts/proposals/build_ledger_artifact_bundle.py#L1)).

## 3. Scope and lifecycle

- [ ] Attach the approved path matrix and compare it mechanically in both
  directions against `git diff --name-only <BASE> HEAD`; the hardening baseline
  is the controlling path ceiling
  ([BASELINE.md, path matrix](BASELINE.md#approved-work-item-path-matrix)).
- [ ] Prove protected production contracts, interfaces, committed ABIs, and
  migrations are unchanged when the release scope requires no change; source
  identities are pinned in the baseline
  ([BASELINE.md, baseline identity](BASELINE.md#baseline-identity-verification)).
- [ ] Classify each item exactly as prohibited, owner-parked, live-gated,
  conditional, locally implementable draft support, or owner-decision-needed;
  do not convert validation necessity into authority.
- [ ] State separately whether evidence supports implementation,
  publication, integration, deployment, activation, monitoring, and release;
  the component records explicitly distinguish source integration from
  deployment/activation
  ([guarded-erc20.md, reviewed snapshot](../smart-contract-changes/guarded-erc20.md#reviewed-implementation-snapshot),
  [credit-engine.md, reviewed snapshot](../smart-contract-changes/credit-engine.md#reviewed-implementation-snapshot)).

## 4. Tests, mutations, and anomalies

- [ ] Run every focused family, static checker, created test, and the full
  serial repository suite in the exact environment; record each exact command
  and result.
- [ ] For every S2/S3 claim record subject path, one replacement, mutant
  SHA-256, baseline pass, named mutant rejection, intended invariant, and
  criteria result
  ([mutation-evidence-protocol.md](mutation-evidence-protocol.md)).
- [ ] Record every failed attempt or anomalous run, its root cause, whether the
  aggregate-failure protocol ran, and which later evidence supersedes it; never
  erase an inconvenient result from the packet.
- [ ] Re-run the frozen artifact checker and negative self-tests; the checker
  controls source-governed optimization, raw-byte hashing, layouts, integrity,
  and runtime-template labeling
  ([check_contract_artifacts.py](../../../../scripts/check_contract_artifacts.py),
  [test_contract_artifacts.py](../../../../tests/inventory/test_contract_artifacts.py)).
- [ ] Re-run the complete block-clock inventory and its tests; the checker
  fails closed on unclassified production, test, mock, testing, cadence, and
  timestamp drift
  (`check_block_clock_inventory.py`,
  `test_block_clock_inventory.py`).

## 5. Deployment/profile evidence

- [ ] Bind constructor ABI arity/order, decoded arguments, source creation
  bytecode, runtime template, immutable-bound runtime, code hashes, and every
  post-deploy readback; the Ledger artifact bundle/test demonstrates those
  distinctions
  ([ledger-local-artifact-bundle.json](ledger-local-artifact-bundle.json),
  [test_ledger_artifact_bundle.py](../../../../tests/deployment_profiles/test_ledger_artifact_bundle.py)).
- [ ] Label deterministic placeholder inputs as placeholders and local Boa
  results as local reproduction, never live deployment evidence
  ([ledger_robinhood_profile.py:1-9](../../../../scripts/proposals/ledger_robinhood_profile.py#L1),
  [lootbox_deployment_profiles.py:1-9](../../../../scripts/proposals/lootbox_deployment_profiles.py#L1)).
- [ ] For Lootbox, use the single canonical manifest and identify which future
  deployment paths actually exist; the current tests pin four historical Base
  call sites as arity-incompatible rather than treating them as runnable
  current paths
  ([test_lootbox_deployment_profiles.py:83-172](../../../../tests/deployment_profiles/test_lootbox_deployment_profiles.py#L83)).
- [ ] For Ledger, bind historical Base replay to the original two-argument
  artifact, require a new explicit-zero migration for future native
  deployments, and keep exact-`0x64` RH deployment separately controlled
  ([ledger-replay-policy.md](ledger-replay-policy.md)).

## 6. Operations and ownership

- [ ] Attach completed asset-admission, backing, Ledger, and Lootbox runbooks;
  unresolved thresholds and authorities must remain literally marked
  `UNRESOLVED — owner decision`
  ([asset-admission-assumptions.md](asset-admission-assumptions.md),
  [stock-backing-monitoring-runbook.md](stock-backing-monitoring-runbook.md),
  [ledger-monitoring-runbook.md](ledger-monitoring-runbook.md),
  [lootbox-distribution-monitoring.md](lootbox-distribution-monitoring.md)).
- [ ] Obtain consumer-owner sign-off that `lastTouch` is a
  deployment-selected identity and not universally EVM `NUMBER`; the semantic
  contract and unresolved gate are recorded separately
  ([last-touch-consumer-semantics.md](last-touch-consumer-semantics.md)).
- [ ] Record owner decisions for every unresolved authority, escalation route,
  paging threshold, re-enable criterion, retention rule, and Lootbox sane upper
  interval bound; absence remains a release residual, not an agent-selected
  default.
- [ ] Record live-gated evidence as not attempted unless a later instruction
  explicitly authorized network reads or transactions; local source/profile
  results do not satisfy live qualification.

## 7. Packet sign-off

| Field | Required value |
| --- | --- |
| Packet ID and release snapshot | **UNRESOLVED — owner/release process** |
| Evidence preparer and independent reviewer | **UNRESOLVED — owner/release process** |
| Security, protocol, operations, and consumer approvals | **UNRESOLVED — owner/release process** |
| Exact unresolved residuals accepted/rejected | **UNRESOLVED — owner/release process** |
| Deployment/activation/release authority reference | **UNRESOLVED — owner/release process** |
| Retention location and policy | **UNRESOLVED — owner/release process** |

Checklist completion is evidence assembly only. Actual adoption, sign-off,
deployment, activation, and release remain owner decisions.
