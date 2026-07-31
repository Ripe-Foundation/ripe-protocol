# Robinhood deployment-owner quickstart

This is the practical entry point for the engineer and agents assembling the
Robinhood deployment. It explains where configuration belongs, how the
generated defaults and deployment plan are produced, what the migration and
qualification tools prove, and which actions remain separately authorized.

This guide is not deployment authority. It does not authorize RPC access,
accounts, keys, signers, transactions, migration execution, configuration,
activation, testnet rehearsal, production release, or Sites changes.

> **Integration checkpoint:** before following a command, verify the named path
> exists on the current `rh` tip. The Profile 1 configuration, artifact/topology,
> and H-09 fork Wave 2 packages are being assembled as one qualification train.
> A reviewed local candidate is not controlling until its signed train is
> integrated and rebound to the final `rh` commit.

## The five-minute mental model

The old deployment style made the runtime blueprint, a handwritten defaults
contract, migration scripts, and a verification script act as independent
sources of truth. The new workflow is an authority pipeline:

```text
owner decisions + canonical external facts + repository-approved values
                              |
                              v
config/robinhood_blueprint.py + config/robinhood-parameters.json
                              |
                  fail-closed validation
                              |
             +----------------+----------------+
             |                                 |
             v                                 v
generated DefaultsRobinhood.vy       deterministic deployment plan
             |                                 |
             +----------------+----------------+
                              |
                              v
migrations/robinhood + artifact/topology expectations
                              |
                              v
local deployment -> pinned archive fork -> authorized testnet rehearsal
                              |
                              v
reviewed evidence and release packet -> separately authorized production run
```

The important rule is simple: **an output never becomes its own authority**.
Do not make a value true by typing it into `BluePrint.py`, a Vyper defaults
file, or a migration. Bind the value and its authority first; then generate or
derive the downstream artifacts.

## Source-of-truth map

| File or interface | What it owns | What it does not own |
| --- | --- | --- |
| [`status.yaml`](status.yaml) | Current program state, active/parked lanes, and lifecycle truth | Contract values, deployment addresses, or execution permission |
| [`current-owner-priorities.md`](current-owner-priorities.md) | Controlling priority and deferral overlay | Machine-readable configuration |
| [`config/robinhood_blueprint.py`](../../../config/robinhood_blueprint.py) | Desired Robinhood component graph, dispositions, symbolic bindings, authority classes, and Profile 1 exclusions | Runtime deployment addresses invented by a migration author |
| [`config/robinhood-parameters.json`](../../../config/robinhood-parameters.json) | Typed parameter, deployment-input, and assertion records with status and provenance | Permission to replace unresolved values with Base values, zeroes, or guesses |
| [`config/BluePrint.py`](../../../config/BluePrint.py) | Execution-facing runtime blueprint after inputs are accepted | The first or sole record of a product, risk, topology, or identity decision |
| [`scripts/params/generate_robinhood_defaults.py`](../../../scripts/params/generate_robinhood_defaults.py) | Deterministic validation and generation of the canonical defaults contract | Choosing values or curing blocked inputs |
| `contracts/config/DefaultsRobinhood.vy` | Generated, reviewable configuration artifact | A file to edit by hand; it remains absent while required inputs are unresolved |
| [`config/network_profiles.py`](../../../config/network_profiles.py) | Chain IDs, RPC environment-variable names, allowed operations, migration source, and history namespace | RPC secrets or deployment permission |
| `migrations/robinhood/` | One canonical ordered migration source shared by Robinhood testnet and mainnet | Environment-specific source forks or retroactive history changes |
| `migration_history/robinhood-{testnet,mainnet}/v1/` | Separate immutable evidence after authorized execution | Planning output or evidence that may be created during an offline/fork run |
| Artifact/topology expectation and observation envelopes | Exact expected artifacts, registries, reachability, identities, and observed results | Live RPC collection; the checker compares pre-collected facts |
| [`tests/deployment/fork/`](../../../tests/deployment/fork) | H-09 offline gates and explicit opt-in, read-only archive-fork qualification | Live testnet deployment; H-10 owns that lane |

## What the deployment owner actually produces

| Work unit | Human-owned input | Tool-produced or checked output |
| --- | --- | --- |
| Canonical input package | Approved addresses, parameters, roles, topology choices, provenance, and unresolved dispositions | Updated typed blueprint/parameter records and a blocker report for anything incomplete |
| Profile 1 defaults | Complete approved `defaults_field` rows | Generated `contracts/config/DefaultsRobinhood.vy` plus source/artifact identities |
| Runtime blueprint | Accepted deployment inputs and deterministic future/deployed addresses | A `config/BluePrint.py` mapping that reconciles exactly to the canonical authorities |
| Deterministic plan | Selected Profile 1 graph, ordered steps, dependencies, and approved inputs | Stable plan/report bytes, plan hash, source set, preconditions, postconditions, and stop reasons |
| Migration package | Reviewed implementation of each assigned migration step | Canonical files under `migrations/robinhood/`; no history until an authorized execution |
| Artifact freeze | Reviewed source, compiler, constructor, registry, and topology expectations | Deterministic artifacts, ABIs, expectation envelope, and offline comparison results |
| Fork qualification | Accepted chain/block pin, identities, sequencer policy, archive endpoint alias, and owner manifests | Classification artifact, observations, replay/evidence hashes, and deterministic teardown proof |
| Testnet rehearsal | Separately authorized operator, signer, provider, plan, and funds | Isolated testnet history, receipts, assertions, verification, reconciliation, and incident evidence |
| Release packet | Owner/security/operations approvals and accepted testnet evidence | One indexed evidence bundle for the final production decision; still not execution authority |

The engineer owns truthful inputs, migration logic, and interpretation of
failures. The tools own deterministic rendering, ordering, hashing,
classification, and fail-closed enforcement. Neither the engineer nor an agent
should edit a downstream output to make a failing upstream input appear valid.

## The three kinds of configuration record

`config/robinhood-parameters.json` uses typed destinations. The distinction
prevents values from leaking into the wrong artifact.

| Destination | Meaning | Output |
| --- | --- | --- |
| `defaults_field` | A value encoded in the generated defaults contract | Rendered into `DefaultsRobinhood.vy` only when approved and complete |
| `deployment_input` | A constructor, address, role, operator, or plan input | Consumed by the deterministic deployment plan or runtime blueprint; not automatically rendered into defaults |
| `assertion` | A required invariant, omission, identity, or postcondition | Checked before/after deployment; never rendered as configuration |

The Profile 1 configuration train also classifies all required blueprint
bindings by **where authority comes from**:

| Authority class | Required treatment |
| --- | --- |
| `repository_approved` | Reuse the exact integrated repository decision or value. Do not reinterpret it. |
| `externally_verifiable_canonical_fact` | Supply the fact plus evidence such as chain, address, proxy/implementation, code hash, token metadata, block, source, and revalidation date. Do not label it verified before verification. |
| `owner_selected` | Obtain and record the explicit owner choice and approval reference. |
| `deployment_produced` | Leave unresolved until a deterministic plan derives it or a deployment produces it; bind the resulting identity and evidence afterward. Do not guess it. |

An input package is therefore not just a Markdown list of addresses. At minimum,
each input needs an identifier, typed value, authority class, resolution state,
source or approval, responsible owner, and—where applicable—chain/block,
proxy/implementation, code hash, decimals, observation time, and revalidation
policy.

## Controlling launch posture

Profile 1 is intentionally smaller than the eventual system:

- Chainlink is the primary launch price authority at PriceDesk ID 1.
- Curve remains reserved and empty at PriceDesk ID 2.
- BlueChipYield is the selected launch adapter for the SteakHouse USDG vault
  at PriceDesk ID 3, subject to the separately reviewed Morpho Vault V2
  production-contract prerequisite and final canonical-identity binding.
- Pyth and Stork remain empty at PriceDesk IDs 4 and 5.
- Curve is not deployed or registered in Profile 1.
- No Uniswap price-source contract is deployed or registered at launch.
- RIPE/WETH V2 may be considered only as an externally held liquidity canary;
  it is not protocol oracle authority and its LP token is not admitted.
- GREEN/USDG and both LP-token admissions belong to Profile 2.
- The PSM remains disabled and requires separate funding, qualification, and
  activation authority.
- GuardedErc20 remains separate and Stock-specific, with Stock admission and
  its auction-only liquidation tuple still requiring exact binding.
- Ledger and Teller retain their integrated contract designs.

The selected launch asset set is SteakHouse USDG, WETH, RIPE, sGREEN, and
GREEN. SteakHouse USDG and WETH are the priority liquidation assets; sGREEN is
the priority stability asset. The normalized priority price-source list is
`[1, 3]`: Chainlink first and BlueChipYield second. Do not copy the older
`[1, 2, 3]` list from PR #66. That list reflects sequential registration in the
old deployment branch, while the canonical registry reserves semantic ID 2 for
Curve even when Curve is absent.

The Profile 1 generator must exclude all deferred LP/stability paths from
selection and rendering while preserving them in the canonical manifest for a
later Profile 2 package.

Current owner priorities also park all Deleverage work. Do not add machine
records for `fullPayoffBuffer`, `overageBps`, `dustThreshold`, or `dustBps`, and
do not reopen the zero-cooldown decision through a deployment PR.

Also parked: CCIP, CreditEngine zero-backing policy, Uniswap TWAP
implementation, Sites recovery, and dashboard deployment.

### Owner-selected launch inputs from PR #66

The team has selected the launch asset and economic inputs represented by
[PR #66](https://github.com/Ripe-Foundation/ripe-protocol/pull/66). They must be
reconciled into the typed input pipeline; the PR's handwritten blueprint,
defaults contract, migration runner, and migration namespace are not
authoritative artifacts.

External identities to bind and independently verify on Robinhood Chain:

| Input | Selected value | Treatment |
| --- | --- | --- |
| WETH | `0x0Bd7D308f8E1639FAb988df18A8011f41EAcAD73` | Canonical external fact; verify code and token metadata |
| USDG | `0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168` | Canonical external fact; verify proxy, implementation, storage, and metadata |
| SteakHouse USDG vault | `0xBeEff033F34C046626B8D0A041844C5d1A5409dd` | Canonical external fact and selected launch asset |
| Chainlink ETH/USD | `0x78F3556b67E17Df817D51Ef5a990cDaF09E8d3A9` | Canonical external fact; bind feed policy and decimals |
| Chainlink BTC/USD | `0xa2c5184bF03d373Dc9dE4876eb4Bce595B460251` | Canonical external fact; not automatically an admitted launch asset |
| Chainlink USDG/USD | `0x61B7e5650328764B076A108EFF5fa7282a1B9aD2` | Canonical external fact; bind heartbeat and stale policy |
| Morpho Vault V2 factory | `0x0FBad98595b0186dA120E41f77C102beb49f803c` | Canonical external fact and BlueChipYield prerequisite |
| Governance | `0xe488a42D33b3Af5d3E5Cd5680938d8369716D1bf` | Owner-selected role; bind authority and signer evidence separately |
| ArbSys | `0x0000000000000000000000000000000000000064` | Canonical chain fact; bind code identity at the accepted pin |

Selected launch economics include:

| Area | Selected launch values |
| --- | --- |
| Debt envelope | per-user `50e18`; global `500e18`; minimum `1e18`; 20 borrowers; `50e18` per 7,200-block interval; danger-block increase 60 |
| RIPE availability | `1,000e18` each for rewards, HR, and bonds |
| Rewards | points enabled; `9e15` RIPE/block; allocations borrowers/stakers/voters/general depositors `1000/9000/0/0`; auto-stake `7500`; duration ratio `3300`; stability reward `1e18` per dollar claimed |
| Bond | USDG; `2,000e6` per epoch; bonding initially disabled; maximum RIPE/unit `1e18`; maximum lock bonus `20,000`; epoch 2,400 blocks; auto-restart enabled |
| RIPE and sGREEN points | staker allocations `1500` each; voter allocations zero |

The complete asset tuples—including caps, LTVs, liquidation settings,
permissions, vault IDs, and priority ordering—belong in the machine-readable
launch-input reconciliation package and its exact tests. The generated defaults
file remains absent until that package and every required deployment-produced
identity are complete.

The PR also contains values that remain deliberately excluded: PSM capacity,
Deleverage scaffolding, CCIP token changes, Curve/LP activation, and its custom
runner and old migration namespace. Do not pull those into Profile 1 as a side
effect of accepting the asset and economic selections.

## End-to-end workflow

### 1. Rebind to the final integrated `rh`

Start in an isolated worktree and record the exact commit and tree. Confirm
local, cached, and live `rh` parity before editing. If a package was prepared
against an older baseline, rebase or reconstruct it and rerun the affected
bindings; do not carry hashes forward by assertion.

The configuration, artifact/topology, fork, and migration packages must all be
tested together after assembly because they consume one another's identities.

### 2. Assemble the canonical input package

Work from the unresolved bindings in `config/robinhood_blueprint.py` and
`config/robinhood-parameters.json`. For each row:

1. identify its authority class;
2. obtain the required repository decision, external proof, owner selection,
   or deterministic deployment output;
3. update the typed value and resolution state;
4. attach the exact provenance or approval;
5. preserve blocked, disabled, deferred, and omitted dispositions honestly;
6. run the focused configuration tests.

Do not paste a convenient address from an old deployment branch. Token,
oracle, factory, router, pool, proxy, implementation, governance, operator,
and sanctions-list identities all require the authority specified for their
row.

### 3. Validate and generate `DefaultsRobinhood.vy`

Safe validation writes nothing:

```sh
python scripts/params/generate_robinhood_defaults.py --check
```

While required inputs remain unresolved, the correct result is a stable
`H04_BLOCKED` response and no output file. Do not work around that response.

After every required defaults field is approved and bound, generation is:

```sh
python scripts/params/generate_robinhood_defaults.py
```

The generator atomically writes the exact canonical path:

```text
contracts/config/DefaultsRobinhood.vy
```

The spelling and capitalization are controlling. Never create
`DefaultsRobinHood.vy`, copy `DefaultsBase.vy`, or edit the generated file by
hand. Review the generated diff and bind its source and artifact hashes.

Focused checks:

```sh
pytest -q tests/config/test_defaults_robinhood.py
pytest -q tests/deployment/test_robinhood_blueprint.py
pytest -q tests/deployment/test_network_profiles.py
python scripts/check_block_clock_inventory.py --check
pytest -q tests/inventory/test_block_clock_inventory.py
```

### 4. Populate the runtime blueprint

Only after an input is accepted should it reach `config/BluePrint.py`.
Treat the runtime blueprint as a consumer of the canonical authority files,
not as an informal scratchpad.

Every runtime mapping must reconcile to:

- the selected component and disposition in `robinhood_blueprint.py`;
- the accepted parameter/deployment-input record;
- the expected registry ID and dependency edge;
- the generated defaults identity where applicable; and
- the deterministic plan that deploys or observes the address.

If a runtime value cannot be traced backward through that chain, stop and bind
the missing authority rather than adding the value directly.

### 5. Produce deterministic migration plans

Both Robinhood environments consume one source directory:

```text
migrations/robinhood/
```

Their histories are isolated:

```text
migration_history/robinhood-testnet/v1/
migration_history/robinhood-mainnet/v1/
```

The safe plan interface uses no RPC, account, signer, simulation, transaction,
or repository write:

```sh
python scripts/migrate.py --profile robinhood-testnet --plan
python scripts/migrate.py --profile robinhood-mainnet --plan
```

A blocked report is correct while source steps or required bindings are not
ready. Do not introduce a custom runner to bypass the profile, plan, account,
or history controls.

Initial migration IDs have fixed ownership:

| Range / ID | Purpose |
| --- | --- |
| `0010`–`0080` | Predeployment artifact, defaults, registry, omission, and tooling assertions |
| `0100` | Tokens, RipeHq, TrainingWheels, and initial authority foundations |
| `0200` | Ledger, MissionControl, and data/config registries |
| `0300` | Switchboards |
| `0400` | Chainlink price source and reserved-empty unsupported slots |
| `0500` | Vaults and selected assets |
| `0600` | Core departments and BondBooster |
| `0700` | Optional SavingsGreen disposition |
| `0800` | Disabled PSM posture |
| `0900` | Capabilities, roles, timelocks, and governance handoff |
| `1000` | Deferred CCIP record; never part of the initial graph while parked |

Do not create separate `migrations/robinhood-mainnet/` and
`migrations/robinhood-testnet/` source trees. Never edit Base migration
history to make Robinhood appear complete.

### 6. Freeze artifacts and topology expectations

After the artifact/topology package is integrated, use its templates instead
of writing a one-off verification script:

```sh
python scripts/check_deployment.py --print-template expectations
python scripts/check_deployment.py --print-template synthetic
python scripts/check_deployment.py --print-template local_deployment
python scripts/check_deployment.py --print-template deployed_observation
```

Then compare pre-collected observations with reviewed expectations:

```sh
python scripts/check_deployment.py \
  --expectations /absolute/path/to/expectations.json \
  --observations /absolute/path/to/observations.json
```

This interface must prove, as applicable:

- creation artifact and compiler-integrity bindings;
- ABI, selector, event, constructor, and layout identities;
- blueprint registry IDs and collision freedom;
- complete component dispositions, including absence and unreachability of
  blocked, deferred, disabled, and omitted components;
- dependency edges and configuration-source completeness;
- chain, proxy, implementation, code, and deployed-address identities; and
- truthful verifier-provider and submission-state classification.

The checker validates supplied evidence. It does not authorize RPC access or
collect live facts on its own.

### 7. Validate locally, then qualify a pinned archive fork

Run the offline fork framework first; network access is disabled by default:

```sh
pytest -q tests/deployment/fork
```

After H-09 Wave 2 is integrated, archive-fork qualification is explicit opt-in
and requires complete owner input and identity manifests, an accepted immutable
pin, an accepted sequencer policy, a clean repository, and an allowlisted
endpoint alias. The shape is:

```sh
RIPE_RH_FORK_MODE=read-only-archive-fork \
RIPE_RH_FORK_MANIFEST=/absolute/path/to/fork-envelope.json \
RIPE_RH_FORK_IDENTITY_MANIFEST=/absolute/path/to/identity-manifest.json \
OWNER_RH_ARCHIVE_PROVIDER='https://redacted-owner-endpoint' \
pytest -q tests/deployment/fork \
  --rh-classification-out=/absolute/path/to/classification.json
```

Use the exact endpoint alias declared by the envelope. Never commit or print
the endpoint value. Impersonation and state mutation are allowed only inside
the disposable local fork, which must be destroyed and deterministically
replayable. H-09 evidence is qualification, not a persistent deployment.

### 8. Rehearse on testnet only under a new authorization

H-10 owns live testnet work. Before any live command, freeze:

- final source commit/tree and clean-tree proof;
- exact plan and artifact hashes;
- selected operator, machine, volume, and H-06 qualification;
- RPC provider and secret-handling procedure;
- account/signer and funding authority;
- abort, pause, retry, finality, reconciliation, and evidence rules; and
- the exact permitted command and target profile.

No offline, local, or archive-fork result grants this authority.

### 9. Assemble release evidence; authorize production separately

The release packet is not random documentation. It is the evidence index that
binds the reviewed configuration, generated defaults, deployment plan,
artifacts, topology, fork/testnet results, operators, signers, abort rules,
receipts, verification, monitoring, and handoff. It makes a production decision
reviewable; it does not make the decision automatically.

Production deployment requires a separate instruction naming the final plan,
network, signer/backend, and allowed actions.

## Translating an older deployment PR

[PR #66](https://github.com/Ripe-Foundation/ripe-protocol/pull/66) is useful
engineering research, but it follows the older direct-authoring model. Preserve
its chain-specific discoveries, ordering logic, mocks, and semantic assertions;
translate the implementation as follows:

| Older pattern | New destination |
| --- | --- |
| Put addresses and decisions directly in `config/BluePrint.py` | Bind them first in `config/robinhood_blueprint.py` and `config/robinhood-parameters.json`; let the runtime blueprint consume accepted values |
| Handwrite `DefaultsRobinHood.vy` | Resolve typed manifest rows, run the generator, and review `DefaultsRobinhood.vy` |
| Maintain a `migrations/robinhood-mainnet/v1/` source tree | Use shared ordered source `migrations/robinhood/` and isolated environment histories |
| Use a custom runner with an arbitrary `--rpc` | Use `config/network_profiles.py` and `scripts/migrate.py`; keep plan, fork, testnet, and live operations separate |
| Use a handwritten postdeployment verifier | Produce observations and evaluate them through the artifact/topology assertion interface |
| Mix a prerequisite production-contract change into the deployment PR | Move it to a separate contract PR with its own review, artifact rebind, and tests |

PR #66's asset and economic choices are now owner-selected launch inputs, but
they still must be translated rather than copied. Normalize the PriceDesk IDs,
independently verify external identities, keep deployment-produced identities
unresolved until derived, and exclude parked PSM, Deleverage, CCIP, Curve/LP,
and custom-runner scope.

The SteakHouse USDG selection also opens one separately reviewed contract
prerequisite: `BlueChipYieldPrices.vy` must support the selected Morpho Vault V2
shape, followed by ABI/artifact rebind and focused tests. Do not hide that
production change inside a configuration or migration commit.

## Recommended PR shape

A deployment-preparation branch can remain one coherent review unit while
using logical commits:

1. `config(rh): bind canonical Profile 1 inputs`
2. `config(rh): generate Robinhood defaults`
3. `feat(rh): add deterministic deployment plan and migrations`
4. `test(rh): bind artifacts topology and qualification evidence`

Keep production-contract prerequisites in separate PRs. Keep Profile 2,
parked integrations, testnet execution, and production execution out of the
Profile 1 preparation PR.

## First-hour checklist

1. Read this guide and [`deployment-owner-readiness.md`](deployment-owner-readiness.md).
2. Read the current [`status.yaml`](status.yaml) and
   [`current-owner-priorities.md`](current-owner-priorities.md).
3. Verify the exact `rh` commit/tree and confirm the qualification train is
   integrated before relying on its commands or classifications.
4. Run the defaults generator in `--check` mode and record the stable blockers.
5. Run both migration `--plan` commands and record the blocked plan output.
6. Build a binding register for unresolved addresses, roles, parameters, and
   deployment-produced identities.
7. Classify each row by authority source; assign an owner and evidence target.
8. Do not access RPC, accounts, keys, or signers during this inventory pass.

## Contract for deployment agents

Every agent working in this lane should receive these constraints:

- bind work to the exact current `rh` commit and tree in an isolated worktree;
- inspect current authority files before changing runtime outputs;
- do not invent, infer, or substitute unresolved values;
- do not hand-edit generated files;
- keep Profile 1 and Profile 2 separate;
- preserve parked lanes and negative topology assertions;
- use no RPC unless the exact H-09 or H-10 authority is supplied;
- never expose endpoint, account, key, or signer material;
- do not stage, commit, push, deploy, migrate, configure, or activate unless
  that lifecycle action is explicitly authorized;
- report exact changed paths, tests, hashes, generated outputs, unresolved
  blockers, and final worktree hygiene.

## Stop conditions

Stop rather than improvise if any of these occurs:

- local/cached/live `rh` identity drift;
- a required value has no approved authority or evidence;
- the generator is blocked or produces a noncanonical path;
- a Profile 2 or parked item appears in Profile 1 output;
- a migration ID, registry ID, dependency edge, artifact, or source hash
  conflicts with the reviewed plan;
- a checker requires bypassing a fail-closed gate;
- an RPC URL, credential, account, or signer would be accessed outside the
  named authorization;
- a plan or fork run would create persistent migration history;
- a production-contract change is discovered inside deployment work; or
- an observed deployed topology differs from expectations.

## Detailed references

Use this page for navigation; use the following documents for the full
contracts and evidence rules:

- [Deployment-owner readiness](deployment-owner-readiness.md)
- [Deployment support specification](robinhood-deployment-support-specification.md)
- [Deployment validation plan](robinhood-deployment-validation-plan.md)
- [Manifest operator runbook](robinhood-manifest-operator-runbook.md)
- [Release-packet evidence checklist](hardening/release-packet-evidence-checklist.md)
- [Reassessment and qualification synthesis](reassessment-and-qualification-synthesis.md)
- [Network, token, and oracle authority](qualification/network-token-oracle-authority.md)
- [Fork-suite coverage and architecture](qualification/fork-suite-coverage-census.md)

If these references disagree, use the current machine authority and owner
priority overlay, preserve the disagreement, and request a bounded
reconciliation. Do not silently choose whichever value makes generation or
deployment easiest.
