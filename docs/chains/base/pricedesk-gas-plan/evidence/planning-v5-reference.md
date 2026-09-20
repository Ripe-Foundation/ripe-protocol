# Execution reference

Use this with `updated-prompt.md`. It supplies setup, measurement, test and activation details; the current prompt and recorded owner decisions control. Archived prompts are evidence only.

## Source and workspace

Repository: `$RIPE_REPOSITORY`. Frozen implementation baseline: `bdf7f3da7113aabde60ab8eceab6a960a841bb88`, PR #231, branch `codex/base-upgrade-fork-rehearsal`. Master reference: `1ede38351e6da918806dff70d34b2066bf8cde8c`. Read the pinned tree's:

- `contracts/registries/PriceDesk.vy`, its registry/governance modules, relevant interfaces, `config/BluePrint.py` and constructor consumers.
- `docs/chains/base/staged-upgrade-deployment.md`, `docs/chains/base/review-231.md`, `migrations/base-mainnet/2026091403_StageBaseBridgePriceDesk.py`.
- `scripts/diagnose_base_undy_prices.py`, `scripts/base_full_update_fork.py::FullUpdate` and supporting rehearsal code before extending them.

Refresh PR state/head and record any delta; continue at the frozen SHA unless explicitly instructed otherwise. Use a new isolated checkout. Preserve other checkouts and untracked files. If linked-worktree administration is unavailable, use a permitted standalone `git clone --no-hardlinks --no-checkout` into an unused writable location, then check out the pin. If Git metadata writes are unavailable too, use a source archive and deliver patches with the limitation recorded. Do not bypass a denied permission. Copy only files listed in `packet-hashes.json` into the implementation checkout, preserving relative paths, plus that inventory itself. Exclude `.claude/` and any other unlisted session files. The packet is absent from the pinned commit. Do not delete another session's directories.

The diagnostic runner currently accepts only historical block **51,312,366**, contains expected outcomes specific to that block, and stages replacement sources. Its asset list contains only undyETH, undyEURC and undyUSDC. Extend reusable machinery explicitly for new pins, the full asset inventory and the bridge's retained sources. Do not merely remove its block guard or treat its fresh-source result as production-ring qualification. Respect its documented diagnostic exit/status semantics.

## Measurement details

Revision-5 topology evidence: at Base block **51,532,116**, hash `0x2d63b25e62be864d40eabbe4a08d536121d44c7ff6406b50550935c9d4a0890a`, HQ resolved the same desk/MC and MC returned priorities `[1,8,2,9,4,5]`. Later slot/asset enumeration was rate-limited, so that readback does not independently prove the reviewer's complete six-asset/fallback claim. A separate pinned read returned the active PriceDesk's source `registryChangeTimeLock == 0`. Do not confuse this with the historical HQ replacement delay of 21,600 blocks or infer the replacement's desired delay. Authenticate source builds/configuration and all retained dependencies before qualifying the lazy quote design.

The eager self-revisit contradiction is structural: a source entered with at most B has less than B after doing work/calling back; a nested eager request to supply B again cannot pass. The candidate remedy permits a low-gas **clean no-feed** visit, not an exemption for arbitrary source failure. Test Chainlink exhaustion with healthy underlying fallback and duplicate/revisited slots, using actual priorities. Review current source, historical deployed build, linked libraries/proxies and external vault/pool/oracle behavior for caught failures, default values and gas-dependent clean replies. The two current-source `raw_call(..., revert_on_failure=False)` sites are feed-decimals helpers; this is a useful lead, not a full deployed dependency audit.

Authenticate chain ID, header/hash/time, deployed code, constructor/configuration inputs, HQ departments and source state before comparing generations. Historical leads are approximate failure block **51,493,600** and earlier reported bridge parity at **51,491,284**; neither establishes causality. The reviewer's **1,719,201** measurement and undyAERO/undyUSD margin reports lack an accompanying trace in this packet. Obtain or reproduce frame-level provenance; do not relabel them independently verified.

Use a separate fresh finalized pin for final qualification, preserving historical evidence. Record fork advances, snapshot due-state changes and corrective fixtures. Trace every desk address: callbacks may use a passed desk or resolve HQ's canonical desk. Route through the replacement on the fork using recorded setup. Never repoint live HQ and send no third-party messages. A measurement that silently prices dependencies through the old desk does not qualify the replacement.

Verify installed Vyper/Titanoboa and compiler settings; the inspected environment uses **0.4.3 / 0.2.7**. Configure task-local `RIPE_BOA_CACHE_DIR`, `PYTHONPYCACHEPREFIX`, `XDG_CACHE_HOME`, pytest cache/basetemp and Hypothesis storage. With a verified header, call `boa.fork(url, block_identifier=PIN_NUMBER)` using an integer keyword, then assert fork number/chain/time. Forking replaces the global environment; establish it before fixtures. Do not hide discarded fixtures with `allow_dirty=True`.

Restore identical production storage and prove actual transaction access-list resets for every boundary trial. `clear_transient_storage()` and RPC caches do not establish EIP-2929 coldness. Fresh source deployments do not reproduce mature rings. The inspected Boa backend supplies placeholder older BLOCKHASH values; use a compatible backend if a relevant route relies on them. Pass `BASE_MAINNET_RPC_URL` explicitly through an allowlisted environment. Do not load the whole `.env`, private-key/account configuration or production signers. Import only audited fork helpers; their existing CLI `load_dotenv` calls are not the new runner. Try an authenticated configured RPC or public `https://base-rpc.publicnode.com` / `https://mainnet.base.org` with bounded retries, matching chain/hash checks and no signer. Provider failures are environment evidence, not contract failures.

For each route, bracket/bisect the minimum caller limit producing the expected price or snapshot writes; inspect neighboring and higher limits. If behavior is non-monotonic, report success bands instead of a unique minimum. Distinguish consumed gas, requested/actually forwarded source gas, and minimum outer limit. Preserve provenance for each. Recheck at selected budgets because callbacks and guard thresholds can change the requirement.

Inventory actual deployed dependencies and all executable callers, including aliases, conversions, admission, source standalone validation, strictness and user consequences. Source-file counts are not route counts. Undy snapshot calculation invokes external vault `convertToAssets`; trace that external graph too. Test full rings, supported vault-state growth, nested callbacks, recursion/cycles and recovery. Preserve all existing price/freshness semantics, including rejection of the retired nonzero caller stale-time argument and ordinary strict/non-strict distinctions.

For D01, compare identical pre-state and environment at an `eth_estimateGas` result and a generous limit, with exactly the same sender, calldata, value and access list. Assert equal due snapshot transitions and surrounding user state, including relevant events; a successful receipt alone is insufficient. Test the actual submitted buffered limit too. Use a fork backend exposing real estimation, record client/version and estimation parameters, and do not replace this test with gas-used arithmetic. Apply the prompt's result-dependent quote checks and eager admission/feed/snapshot checks. Missing required funding proof reverts that desk frame; genuine fully funded source failures remain isolatable. Parents never classify failures from child-controlled revert bytes. Prove whole-operation rollback where propagated, including earlier snapshots and user writes. Teller's ignored boolean makes this state assertion necessary.

Apply the owner-selected fault model from the prompt; it supersedes the old all-sources-exhaust assumption. Nested execution consumes the parent's cap and must not be counted twice. Faults can change traversal and make additional healthy calls reachable. Test each eligible faulty identity separately, including every invocation through quote/feed/snapshot and nested paths. Also retain existing broader multiple-failure correctness tests; they do not imply those cases fit every production transaction limit.

Make the calculation auditable: first derive the normal bound with 1.5× measured consumption and any larger minimum outer limit imposed by forwarding guards. For each faulty identity, expand the reachable fault-path call tree, replace its disjoint call envelopes with their full configured allowances, and give the remaining healthy work 1.5× headroom, including newly reached fallback work. Recompute the outer funding requirement and take the maximum across normal and fault cases. A faulted descendant already enclosed by a fully counted parent is not added again. Reserve/call overhead and intrinsic gas must be included exactly once. This is fault tolerance with headroom, not the obsolete sum of every source's cap or one extra cap for an arbitrarily long transaction.

## Verification lanes

### Estimator backend preflight

Use Anvil with an explicitly supplied `BASE_MAINNET_RPC_URL`, fixed block and loopback binding. The installed planning environment is Anvil 1.3.5; verify its hardfork/transaction-cap semantics against the target Base execution rules, upgrading or selecting another compatible backend if necessary. Do not infer chain-faithful gas from its version or a higher local block gas limit.

Example launch shape, after selecting and recording `PIN_NUMBER` and a free `LOCAL_RPC_PORT`:

```sh
anvil --host 127.0.0.1 --port "$LOCAL_RPC_PORT" --accounts 0 \
  --fork-url "$BASE_MAINNET_RPC_URL" --fork-block-number "$PIN_NUMBER" --silent
```

The implementation runner must validate these required inputs, redact RPC credentials from reports/process errors and stop its own node on exit. Allowlist environment variables rather than loading `.env`; the URL is network access, not signer authorization. Only impersonate/fund synthetic or governance identities on the verified local fork. Assert expected loopback endpoint, chain/header/state and client before any local mutation; upstream RPC remains read-only. PublicNode HTTP 403 and official-RPC HTTP 429 have both occurred; do not retry indefinitely or switch pins silently.

Planning evidence: `evidence/anvil-estimator-smoke-v5.json` records a synthetic local contract whose slot 0 changed identically with estimated gas 43,106 and a generous 100,000 limit. Default sandbox listener creation failed; a permitted loopback retry passed and shut down. This establishes local estimator/snapshot/revert mechanics only. The implementation must run `eth_estimateGas`, `evm_snapshot`/`evm_revert` and real state-equivalence cases on the final pinned Base fork; Boa's consumed-gas value is not an estimator. Advance timestamps/blocks identically and compare state/events from exactly restored pre-state.

Name the four regressions `test_d01_due_funded_writes`, `test_d01_due_underfunded_reverts_and_rolls_back`, `test_d01_not_due_is_valid_noop`, and `test_d01_genuine_failure_is_isolated`, parameterized or separately implemented for PriceDesk per-asset snapshots and Teller Green reference-pool snapshots. Add estimate/generous-limit equivalence and malformed/caught-failure cases. Record the owner policy, source/tree identity, each result and implementation-review disposition; no aggregate snapshot Boolean closes D01.

Teller's 500k call is a distinct path and initial allowance. Its existing `CurveSnapshotFailed` event concerns low-level call failure, not every Boolean False result. Preserve zero/unconfigured/disabled-route no-op and genuine configured-source failure behavior; add caller-funding protection without making all False returns fatal. Measure its own minimum and complete Teller runtime. If its cap itself is insufficient, supply evidence and a specific bounded-configuration proposal rather than quietly wiring it to a different snapshot function's budget.

Preserve and extend:

- `tests/registries/test_price_desk_isolation.py`, `test_price_desk_gas.py`, `test_price_desk_aggregate_protocol_gas.py`, `price_desk_aggregate_qualification.py`.
- `tests/test_price_desk_aggregate_source_count_guard.py`: preserve independent Robinhood source, topology, budget and batch assertions; adapt constructor inspection meaningfully when arguments change.
- `tests/priceSources/curve/test_robinhood_launch_route.py` and `tests/deployment/fork/markets/test_pricedesk_profiles.py`, with their actual prerequisites and ownership gates.
- `tests/deployment/test_price_desk_token_scale_bootstrap.py`, applicable source tests and constructor/migration consumers.

Run from the implementation checkout with its Python environment. Ordinary explicit gas/artifact lanes retain configured addopts:

```sh
python -m pytest -q -m gas tests/registries/test_price_desk_gas.py tests/registries/test_price_desk_aggregate_protocol_gas.py
python -m pytest -q -m artifact tests/test_current_manifest_consumers.py
```

Run isolation, governance/bounds/struct-member/reset, source-count and affected source tests explicitly as applicable. `gas`, `artifact` and `fork_qualification` already exist. Document the actual new Base module/runner command and require nonzero collection. Deployment tests are excluded by default: when removing that exclusion for an explicit lane, preserve `-p no:unraisableexception`, specify paths/markers and record collection. Missing external qualification inputs remain visible rather than being replaced with fabricated approval.

Measure complete deployed PriceDesk and Teller runtime including immutables; keep `test_price_desk_complete_deployed_runtime_is_below_eip170` and all touched deployables within repository limits. Historical master evidence was 17,742 bytes / 6,834 bytes headroom; the old deployed candidate was 17,898 bytes. Neither qualifies the new implementation. Report baseline failures, deselections and fixture repairs separately from final-stack acceptance.

## Activation reference and separate owner action

**Do not defer the queued-batch decision until implementation finishes.** Give the owner a current read-only assessment of the old slot-7 call immediately. Removing/replacing that proposal or holding its execution is an owner action; this task prepares instructions only. The 2026-09-19 21:22 UTC refresh at finalized Base block **51,531,230**, hash `0xcb7ef0979e164af8e5c6a2d6a11e79abe2d302ab9972225c15a80e01c0c42aed`, again found the old desk active, slot-7 pending empty and the same governance. A separately timed Safe-service request reported the same nonce-477 hash unexecuted. See `evidence/planning-v4-live-refresh.json`; this is a dated readback, not a monitor or full bytecode authentication. The fuller identity/delay record below remains historical.

At Base block **51,524,517**, hash `0x37ebbf61930e433ee35894adda51ab9054cff823e5febe9c6ef32c589606f10b`, read on 2026-09-19:

| Identity | Historical value |
| --- | --- |
| RipeHq | `0x6162df1b329E157479F8f1407E888260E0EC3d2b` |
| Governance Safe | `0xe488a42D33b3Af5d3E5Cd5680938d8369716D1bf` |
| Active PriceDesk | `0x2F7901BE53cC94AEF174f1a0764430840360Ef53` |
| Unqualified 1.5M/1.5M candidate | `0xad70893e2f51076b0e9ba18fc593e924593a073f` |
| Slot-7 pending update | Empty |
| Registry delay | 21,600 blocks |
| Unexecuted Safe batch | Nonce 477, 22 calls |
| Safe transaction hash | `0x6422e6d187b9f0abfe3b11a51fadb828f57207c0b9e53f260e0992df5746636e` |

The batch contains `startAddressUpdateToRegistry(7, candidate)`, which proposes rather than confirms. Refresh HQ code, active/pending desk, governance/delay, Safe nonce and relevant service proposals at entry and handoff; service queue observations are time-stamped separately from block-pinned chain state. Record material drift in the decision log and current task update. The inspected HQ confirmation wrapper is governance-only; bind deployed behavior before relying on it. Proposal execution alone does not activate the candidate. Explicitly reconcile later confirm-all batches: they must not confirm the superseded candidate after its delay matures.

Immediate owner handoff: hold execution of the recorded nonce-477 payload until its slot-7 action is reconciled. The identified call is **third in the batch (zero-based index 2)**, target HQ above, operation CALL/value zero, `startAddressUpdateToRegistry(7, 0xad70893e2f51076b0e9ba18fc593e924593a073f)`. Omitting this call and proceeding is not a default recommendation: the new departments may require the replacement desk. First prove the full dependency/activation graph is compatible; otherwise hold the dependent cutover together. Any reviewed omission produces new calldata/signatures, and does not itself establish readiness of remaining calls. If waiting for the replacement, use its authenticated deployed address only after setup/qualification. In either case, re-read nonce/chain/service state, simulate the entire revised batch, obtain the required new signatures and arrange owner-approved supersession of the old proposal. Neither this note nor deleting a service entry revokes already collected signatures. No replacement payload has been submitted or approved by this planning task.

Reconstruct source IDs/order/disabled state and all settings through registry methods. Historical `numAddrs == 10` is exclusive: `range(1, numAddrs)` visits 1–9, including disabled slot 3 and retained legacy Aero at 6, for eight enabled addresses. Assert every slot and the last enabled source. Do not manually repair the counter.

Bootstrap scales for the union of current collateral, retained vault holdings, source assets and nested dependencies, independently of an incoming empty MissionControl. Use existing authorized setup paths and verify `10**decimals` plus conversions. ETH is implicit 1e18 and rejects `syncTokenScale(ETH)`; exclude zero/BTC reference sentinels and classify NFTs/non-ERC-20 assets. Permissionless sync traverses feeds and fills only unset scales; governance/switchboard bypasses those checks. Missing scales yield non-strict zero or strict reversion even when quotes work.

Resolve departments from authenticated HQ. Historical MissionControl `0x559E53F42b68b4995732Dba4aF300796761DBC19` matched the manifest and had code; no blanket dead-address claim is supported. Maintain candidate labels until separately authorized activation, then promote canonical active manifests with readbacks/consumer tests. Keep existing Stage 2 recovery/empty-MissionControl and Stage 3 gates distinct from this desk change.

Deployment/setup/readbacks precede proposal: a proposed address must contain valid code. A valid on-chain re-proposal overwrites pending state and restarts delay; cancellation is not mechanically required first. This differs from replacing a Safe-service proposal. Changed calldata creates a new Safe hash and requires fresh appropriate signatures; signed transactions are not editable. If nonce 477 already executed, derive the action from current nonce/pending/active state. Do not assume removal from a service invalidates signatures or on-chain pending state. Use actual `confirmBlock`; 21,600 blocks is only approximately twelve hours. Other batch calls remain untouched and unreviewed here.

Rehearse final deployment, setup, governance proposal/confirmation, overwrite/delay-reset, and readbacks on a fork using the intended full stack. Later integration/deployment must freeze the actual reconciled commit/tree, build and constructor/configuration manifest, refresh affected qualification, verify the eventual live replacement address, simulate final Safe calldata and validate activation. Source qualification does not authorize these live actions.

## Consumer compatibility and recovery

Inventory actual transaction construction and `eth_call` policies in the frontend, wallets, keepers, direct integrations and external contracts; include buffers, fixed caps, estimation failures and non-strict calls that now can revert. Starting pointers are `$RIPE_WEB_REPOSITORY` and `$UNDERSCORE_REPOSITORY/contracts/core/Appraiser.vy`: the latter contains direct `getPrice(..., False)`, conversions and `addPriceSnapshot` calls, while PriceDesk expressly authorizes the configured Underscore Appraiser. Bind the actual deployed generation; local sources alone are not proof of production caller behavior. Document unowned/unreadable integrations explicitly and prepare required client patches as proposals outside this implementation's file scope.

Every row of `caller-gas-matrix.csv` identifies endpoint, caller/application version, chain, input/state envelope, call multiplicity, normal and each supported fault-case minimum gas, estimator result, submitted limit/buffer, transaction ceiling and readiness. Include maximum supported keeper batches and indivisible multi-asset positions, not merely one-token happy paths. A smaller operator batch cannot repair an indivisible position that needs an unsupported number of quotes/snapshots.

Prepare the following **owner-operated** recovery playbook with actual setter names, measured values and simulation commands after implementation. These are instructions, not authorization for live action.

| Symptom | Diagnosis and bounded response |
| --- | --- |
| Caller-underfunding revert, healthy source calls | Check submitted limit and estimator/state pin first. Correct caller buffers or supported batch size; raising a source allowance can worsen the minimum caller requirement. Simulate before submitting. |
| Source near 70% / 85% usage, or exhausting a fully supplied budget | Identify call kind/source/dependency and distinguish staleness/no feed from gas exhaustion. Measure a candidate override and recheck normal/fault/nested fit for all affected routes; then governance may raise within bounds with readbacks and verification. Do not blindly raise all allowances. |
| Regression after an override change | Compare prior qualified configuration, current state and effective getters. Revert the setting only if the prior value still covers current requirements and floors; requalify before relying on it. Reset-to-default is not automatically safe. |
| No safe configuration fits the chain limit | Keep affected cutover/operations closed using only verified existing controls and owner authority. Deliver a narrowed scope/design/position-handling decision. Do not rely on the old desk without proving compatibility with the department stack. |
| Persistent due snapshot skips | Check both PriceDesk and Teller paths, due-state truth, source failure events, effective allowance and estimator limit. Do not mark a receipt or unrelated successful snapshot as repair. |
| Replacement required | Deploy/configure/verify the candidate under separate authority, reconcile Safe/pending state and use actual HQ delay/confirmBlock. Fast setters cannot replace this lifecycle. |

Requalification triggers: source addition/replacement/code or proxy-implementation change; priority/order/disabled-state change; override/default/configuration change; Underscore vault/strategy or other transitive dependency change; relevant asset/ring/batch growth; Base gas repricing/transaction-cap or client estimator change; compiler/optimization/EVM-target change; and tree-changing integration. Monitor nested fit each run, explicitly reporting missing fault/state coverage. Keep 70% warning and 85% critical; at exactly 1.5× headroom warning follows approximately 5% drift, which is intentional early notice rather than evidence that failure is imminent.

Budget floors and governance scope are separate from liveness: a constructor floor is not a time-evolving per-source qualified minimum, and immediate setters can still affect oracle availability. Upper bounds keep failure-path full-funding proofs and eager feed/snapshot calls reachable within the transaction envelope. With lazy quotes, a huge budget does **not** necessarily brick every clean quote, so do not repeat that blanket claim. No arbitrary near-uint256 maxima or overflow-prone inequality arithmetic are acceptable.

If Stage 2 cannot access a suitable RPC, finish feasible offline code/tests and the monitor/runner interface. Deliver exact attempted pin/hash/provider class and sanitized errors, cached-evidence provenance, rows marked unqualified, local artifacts/commits and the exact resume command with explicit RPC input. Distinguish implemented/locally tested from Base-qualified; missing fork/estimator evidence keeps dependent D01/deployment gates open. Do not manufacture a current snapshot or claim completion from a different historical pin.
