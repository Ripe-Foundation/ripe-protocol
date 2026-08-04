# Robinhood deployment-owner quick-start

This is the sole canonical human handoff for the Robinhood deployment owner and
the deployment owner's agents. It is operational guidance, not execution
authority. Nothing here authorizes RPC access, accounts, keys, signers,
transactions, migration execution, testnet work, production configuration,
activation, release, or Sites actions.

## Current baseline and lifecycle

Work from the current `rh` tip after confirming parity among local `rh`, cached
`origin/rh`, and credential-free live `rh`.

The transaction-executor candidate continues from the integrated shared-
migration commit `25c0d58e1243449276e4ac4cae8d7abb8272f376`, tree
`2dd9ddb30c1bc09cc82b8ed1ffd67949a20a4abf`. Treat that identity as the exact
candidate parent; do not infer currentness from ancestry or another branch tip.

The preserved predecessor candidate was frozen on commit
`5f5d22b7ee78cbb904c4fe3c6e46599c330c4353`, tree
`7454b5456ebb6cd02d716a64b408629ab501629e`. It is historical comparison
evidence only; it is not the parent or launch authority for this rebind.

Repository configuration is prepared and consistent; production/onchain
configuration has not occurred.

Ready to begin deployment preparation.

- Morpho V2 and BlueChipYield support are integrated.
- `BlueChipYieldPrices.vy` runtime is 22,054 bytes, leaving 2,522 bytes of
  EIP-170 headroom.
- `DefaultsRobinhood.vy` exists, compiles, and is source-authoritative.
- The derived parameter ledger is synchronized.
- The current H-04 register has 22 rows: 21 approved and operative, one
  retired and non-operative, and zero open. 28 canonical H-03 blockers remain
  open; the 14 approved Curve pool and funding inputs are now resolved
  repository facts, leaving 9 Curve-specific typed inputs.
- `configuration_consistent=true`; `deployment_ready=false`; the current
  readiness blocker count is 66: the remaining 57 non-Curve blockers plus 9
  typed Curve launch inputs.
- The executable migration graph is separately typed blocked by 86 keys:
  39 execution bindings (37 deployment-produced identities plus the distinct
  temporary local-governance authority, the zero local-governance authority,
  and the GREEN supply recipient), 9 Curve inputs, 5 external addresses,
  17 deployment inputs, 4 stage reservations, and 12 Stock inputs. This
  86-key plan census layers migration-specific bindings, reservations, and
  Stock inputs on top of the 66-key source/configuration readiness state;
  neither count replaces the other.
- DP15 and P-H04-399 are approved product/configuration decisions. The exact
  reward values remain points enabled, `0.009 RIPE/block`, 10% borrower / 90%
  staker allocation, 75% conditional auto-stake, 33% lock ratio, `1 RIPE/$`
  Stability rewards, and one shared `1,000 RIPE` budget. Stock rewards remain
  disabled. `B-REWARD-PROMOTION` stays open for operational prerequisites.
- The GREEN/USDG pool and bounded GREEN pricing route are selected launch work,
  but neither the GREEN/USDG nor RIPE/WETH LP token is admitted as a Ripe asset.
  RIPE/WETH remains only a separately authorized external canary possibility;
  PSM reserves cannot fund either venue.
- The shared `migrations/robinhood/` source exists as 17 ordered stages through
  `0900`; it contains 119 plan actions and 33 registrations. Stage `1000`
  remains deferred with no executable source file.
- H-05 deterministic offline planning now consumes that shared source for both
  Robinhood profiles; it does not authorize execution or deployment.
- External facts remain independently unverified and deployment-produced
  identities remain unresolved where the sources say so.
- No Robinhood deployment or migration has occurred. Nothing has been
  configured onchain, activated, or released.

[`status.yaml`](status.yaml) is the sole machine-readable current-status
authority. Use the [reassessment and qualification synthesis](reassessment-and-qualification-synthesis.md)
for accepted launch architecture and separately gated follow-on decisions. The
[Curve launch-activation record](curve-launch-activation.md) is controlling for
the bounded ID-2 route. The [reward qualification](reward-launch-qualification.md)
and [LP-admission qualification](qualification/lp-launch-admission.md) retain
their product and non-admission decisions without granting operational or
lifecycle authority.

## Exactly two editable value authorities

| Team/owner-editable source | Exact ownership |
| --- | --- |
| [`config/BluePrint.py`](../../../config/BluePrint.py) | Every Defaults constructor argument and immutable identity; deployment-produced and external address bindings; chain identities and clocks; component and registry topology; governance/operator/role inputs; timelocks, stale windows, supplies, external-oracle inputs; and every other non-Defaults deployment input. Constructor/immutable ownership takes precedence even when a Defaults getter later returns the value. |
| [`contracts/config/DefaultsRobinhood.vy`](../../../contracts/config/DefaultsRobinhood.vy) | Product and configuration values encoded directly in the 17 Defaults getter bodies, excluding constructor-bound identities: global permissions, debt and auction risk, RIPE availability, bond and reward economics, governance-vault and HR configuration, Underscore and last-touch policy, asset-configuration fields, liquidation/stability/price ordering, and lite signers. |

The mechanical ownership precedence is controlling:

1. Defaults constructor arguments, immutable identities, deployment-produced
   addresses, and external address bindings are owned by `config/BluePrint.py`,
   even when a Defaults getter later returns them.
2. Product and configuration values encoded directly in Defaults getter bodies
   are owned by `contracts/config/DefaultsRobinhood.vy`.
3. All other non-Defaults deployment inputs are owned by `config/BluePrint.py`.

Apply this precedence field-by-field when one returned structure mixes an
immutable identity with directly encoded configuration fields.

Two adjacent files are not value authorities:

- [`config/robinhood-parameters.json`](../../../config/robinhood-parameters.json)
  is synchronized, derived evidence. Do not edit a ledger value to change the
  product configuration.
- [`config/robinhood_blueprint.py`](../../../config/robinhood_blueprint.py) is
  structural policy and validation: types, lifecycle, gates, relations,
  blockers, assertions, and address-literal prohibitions. It is not a third
  product-value surface.
- [`config/robinhood-reward-launch-plan.json`](../../../config/robinhood-reward-launch-plan.json)
  is deterministic derived evidence for the approved product decision. Its
  SHA-256 identity binds the exact decision bytes; it does not supersede
  Defaults or authorize execution, deployment, activation, or release.

## Temporary local-governance execution binding

`binding:temporary-local-governance` is an accepted execution-envelope field,
not a product/configuration value and not a third substitute for
`BluePrint.py` or `DefaultsRobinhood.vy`. A production-shaped plan remains
blocked until the deployment operator identity is explicitly approved and
bound. The value must be a nonzero address, must equal the executor's actual
deployment sender, and must differ from
`input:Deployment.DP-18.roles.governance`. Never infer it from an owner,
guardian, Safe, release signer, or another role. The deterministic local
fixture alone may bind it to its local deployment sender.

It deliberately does **not** differ from `RipeHq.governance()`: the deployer is
bound as RipeHq governance at construction and stays so until `0900` hands off
to the Safe. That is the restored Base lifecycle -- the deployer governs the
whole run, then relinquishes once -- and it is what makes the registration
calls work, since `RipeHq` registration asserts
`msg.sender == gov.governance` by strict equality rather than `_canGovern`.

The binding is constructor input only for this mechanically verified census:

- stage `0100`: RipeHq, GreenToken, RipeToken, and SavingsGreen.

The deployer is RipeHq governance for the whole run, so no department may also
take it as local governance: `LocalGov.__init__` asserts
`_initialGov != hqGov`. All 11 departments are therefore constructed with
`binding:no-local-governance`, which is the zero address:

- stage `0300`: Switchboard, SwitchboardAlpha, SwitchboardBravo,
  SwitchboardCharlie, SwitchboardDelta, and SwitchboardEcho;
- stage `0400`: PriceDesk, ChainlinkPrices, CurvePrices, and
  BlueChipYieldPrices; and
- stage `0500`: VaultBook.

Because those 11 never hold local governance, their `0900` relinquishment
receipts are vacuous by construction: each is recorded with no transaction
identity and mutates nothing. The proof obligation is unchanged -- local
`governance()` must be zero for all 11 -- but it is satisfied from
construction rather than by a state transition.

Within `0400`, register PriceDesk at RipeHq ID 7 after CurvePrices is admitted
at PriceDesk ID 2 and before adding the GREEN Curve feed. Production
`CurvePrices.addNewPriceFeed()` resolves PriceDesk through RipeHq, so this is a
runtime prerequisite, not an activation or authority shortcut.

`RipeHq` and the three token constructors keep the approved final-governance
lifecycle. HumanResources initializes local governance to zero and is not part
of the temporary-governance census. Do not use `startGovernanceChange()` as a
constructor workaround.

The last irreversible action in `0900` must first prove all setup, registry and
action timelocks, pending-action absence, post-deployment assertions, sender
identity, and distinct unchanged RipeHq governance. It then records one typed
`relinquishGov()` receipt for each of the 11 contracts and proves local
`governance()` is zero, the temporary sender has no remaining governance power,
and final RipeHq governance is the sole effective governor. An interrupted
handoff records the exact retained set, cannot promote current history, and may
resume only under the identical plan/source/profile/history binding. Previously
validated action and relinquishment receipts are restored; only remaining work
may execute.

## Exact input map

### Addresses and chain identity — `BluePrint.py`

| Input class | Exact source |
| --- | --- |
| Selected external addresses | `ROBINHOOD_USDG`, `ROBINHOOD_WETH`, `ROBINHOOD_STEAKHOUSE_USDG_VAULT`, `ROBINHOOD_GOVERNANCE`, three `ROBINHOOD_CHAINLINK_*` feeds, `ROBINHOOD_MORPHO_V2_FACTORY`, `ROBINHOOD_NATIVE_ETH_SENTINEL`, `ROBINHOOD_BTC_SENTINEL`, `ROBINHOOD_ARB_SYS`, and the five official Curve address-provider/registry/factory candidates; resolution state is in `ROBINHOOD_ADDRESS_STATUS`. |
| Deployment-produced addresses | Symbolic entries in `ROBINHOOD_ADDRESSES`: `CONTRIBUTOR_TEMPLATE`, `TRAINING_WHEELS`, `RIPE_TOKEN`, `GREEN_TOKEN`, `SGREEN_TOKEN`, `GUARDIAN`, and `GREEN_USDG_CURVE_POOL`. Leave them symbolic until a deterministic plan or authorized deployment binds them. |
| Defaults constructor identities | `CONTRIBUTOR_TEMPLATE` (ContributorTemplate), `TRAINING_WHEELS` (TrainingWheels), `RIPE_TOKEN` (RIPE), `GREEN_TOKEN` (GREEN), `SGREEN_TOKEN` (sGREEN), `ROBINHOOD_USDG` (USDG), `ROBINHOOD_WETH` (WETH), and `ROBINHOOD_STEAKHOUSE_USDG_VAULT` (SteakHouse USDG) are all `BluePrint.py`-owned constructor/immutable bindings, even where `hrConfig()`, `trainingWheels()`, `ripeBondConfig()`, `assetConfigs()`, or a priority getter returns them. |
| Chain identity and clocks | `ROBINHOOD_CHAIN`: mainnet chain ID `4663`, testnet chain ID `46630`, 12-second EVM `block.number` basis, five blocks per minute, and symbolic `action_block_source`. |
| Approved absence | `UNDERSCORE_REGISTRY=ZERO_ADDRESS`. Zero is valid only for this declared semantic absence, never as a substitute for an unresolved identity. |

Every selected external address is still `selected_external_fact_unverified`.
An address literal in the repository is not independent target-chain
verification.

### Components, registries, and constructors — `BluePrint.py`

| Input class | Exact source |
| --- | --- |
| Component selection | All 60 rows in `ROBINHOOD_COMPONENT_SELECTIONS`; preserve each `required`, `omitted`, `disabled`, `deferred`, or `blocked` disposition and selection state. |
| Registry topology | All 38 rows in `ROBINHOOD_REGISTRY_TOPOLOGY` across `ripe_hq`, `vault_book`, `price_desk`, and `switchboard`, including source-hard-coded IDs, registration-order IDs, and provisional reservations. |
| Defaults constructor | Ordered `ROBINHOOD_DEFAULTS_CONSTRUCTOR`: `contributorTemplate`, `trainingWheels`, `ripeToken`, `greenToken`, `sgreenToken`, `usdgToken`, `wethToken`, `steakhouseUsdgVault`. Do not reorder or fall back to the older five-argument shape. |
| Other constructors and deployment inputs | `ROBINHOOD_DEPLOYMENT_INPUTS` (`Deployment.DP-04` through `DP-23`) plus `ADDYS`, `PARAMS`, `CORE_TOKENS`, `CURVE_PARAMS`, and `YIELD_TOKENS` for profile `robinhood`. |

Bounded launch topology is exact:

| PriceDesk slot | State |
| --- | --- |
| 1 | Chainlink selected |
| 2 | Unchanged CurvePrices selected for GREEN only |
| 3 | BlueChipYield selected |
| 4 | Empty Pyth |
| 5 | Empty Stork |

Priority price-source IDs are `[1, 3]`. The exact GREEN route is GREEN ->
Curve GREEN/USDG -> PriceDesk -> Chainlink USDG. USDG has no Curve feed. Launch
asset tuples are GREEN, RIPE, sGREEN, WETH, and SteakHouse USDG. Neither the
GREEN/USDG LP nor RIPE/WETH LP is admitted.

`ROBINHOOD_CURVE_LAUNCH_INPUTS` and `CURVE_PARAMS["robinhood"]` in
`BluePrint.py` own the official identity candidates, constructor bindings,
pool candidates, typed owner choices, deployment-produced pool identity,
production observation, exact GREEN-only feed route, and explicit inactive
capabilities. `config/robinhood-parameters.json` contains no alternate Curve
value rows.

### Governance, roles, product, and risk values

| Values | Edit here |
| --- | --- |
| Governance, Safe, Guardian, TrainingWheels allowlist, supply recipients, Endaoment native metadata, external oracle/factory facts, operator/deployment bindings, PSM/stock/LP promotion bindings | `ROBINHOOD_ADDRESSES` and `ROBINHOOD_DEPLOYMENT_INPUTS` in `BluePrint.py`. Getter exposure does not override constructor, immutable, deployment-produced, or external-binding ownership. |
| ContributorTemplate, TrainingWheels, RIPE, GREEN, sGREEN, USDG, WETH, and SteakHouse USDG identities | Their ordered `ROBINHOOD_DEFAULTS_CONSTRUCTOR` bindings in `BluePrint.py`, including when a Defaults getter returns the immutable. |
| Global product permissions and general limits | `genConfig()` in `DefaultsRobinhood.vy`. |
| Debt caps, rates, LTV deviation, keeper fees, payback buffer, and general auction terms | `genDebtConfig()`. |
| RIPE rewards/HR/bond buckets | `ripeAvailForRewards()`, `ripeAvailForHr()`, `ripeAvailForBonds()`. |
| Bond, rewards, governance lock/boost, and HR economics, excluding constructor-bound asset and ContributorTemplate identities | `ripeBondConfig()`, `rewardsConfig()`, `ripeGovVaultConfigs()`, and `hrConfig()` in `DefaultsRobinhood.vy`. |
| Underscore semantic absence, last-touch policy, and lite-signer list | `underscoreRegistry()`, `shouldCheckLastTouch()`, and `liteSigners()` in `DefaultsRobinhood.vy`; the TrainingWheels identity returned by `trainingWheels()` remains constructor-bound in `BluePrint.py`. |
| Asset caps, vault IDs, debt/liquidation risk, auction behavior, and permissions | Directly encoded fields in `assetConfigs()` in `DefaultsRobinhood.vy`; each tuple's asset identity remains constructor-bound in `BluePrint.py`. |
| Liquidation, stability, and price-source ordering | Directly encoded ordering and vault-ID fields in `priorityLiqAssetVaults()`, `priorityStabVaults()`, and `priorityPriceSourceIds()` in `DefaultsRobinhood.vy`; returned asset identities remain constructor-bound in `BluePrint.py`. |

Do not open PSM activation, LP admission, any Curve feed or consumer beyond
GREEN, dynamic rates, Teller reference snapshots, Endaoment stabilization,
Uniswap prototype admission, Deleverage, CreditEngine zero-backing, CCIP, or
Sites work through an otherwise valid configuration edit.

## Synchronize and check

After editing either value authority, synchronize the derived ledger:

```sh
python scripts/params/generate_robinhood_defaults.py
```

Review the `config/robinhood-parameters.json` diff. Every derived value change
must trace to one of the two authorities. Then run the read-only check:

```sh
python scripts/params/generate_robinhood_defaults.py --check
```

The current healthy result is:

```text
configuration_consistent=true deployment_ready=false blockers=66
```

List every unresolved or unverified deployment blocker without using RPC:

```sh
python -c 'from scripts.params.generate_robinhood_defaults import deployment_readiness; ready, blockers = deployment_readiness(); print(f"deployment_ready={str(ready).lower()} blockers={len(blockers)}"); print(*blockers, sep="\n")'
```

Configuration consistency means the two sources compile and reconstruct the
derived ledger byte-for-byte. Deployment readiness additionally requires all
external facts to be independently verified and every deployment-produced or
owner binding to be resolved. Never collapse those gates.

## Deployment-owner sequence

### 1. Close inputs and authorities

Bind the exact baseline, preserve a clean isolated worktree, classify each of
the 66 readiness blockers, and obtain its named external verification,
deployment-produced identity, or owner decision. Freeze governance, Safe,
Guardian, TrainingWheels, lite signers, operators, emergency roles, and signer
policy as reviewed inputs. Separately bind `temporary-local-governance` to the
approved actual deployment sender; zero, final governance, and role inference
are invalid. A missing value remains symbolic and blocked.

### 2. Synchronize configuration

Edit only the two value authorities, regenerate the ledger, and require the
read-only check to remain byte-consistent. `deployment_ready=false` is the
correct result until all deployment bindings are closed.

### 3. Produce offline artifacts and expectations

Compile in clean isolated environments and freeze source, compiler, ABI,
creation/runtime bytecode, constructor, storage-layout, registry, topology,
and omission identities. Generate assertion-envelope templates locally:

```sh
python scripts/check_deployment.py --print-template expectations
python scripts/check_deployment.py --print-template local_deployment
python scripts/check_deployment.py --print-template deployed_observation
```

The checker consumes pre-collected observations; it does not authorize or
perform live collection. Follow the detailed [deployment validation plan](robinhood-deployment-validation-plan.md)
only when this phase begins.

### 4. Produce deterministic plans

Review component selection, omission, deferral, and registry topology in
`config/BluePrint.py`. While this candidate is uncommitted, review the exact
stage/action sequence in explicit preview output from the shared
`migrations/robinhood/` source:

```sh
python -m scripts.migrate --profile robinhood-testnet --plan --preview
python -m scripts.migrate --profile robinhood-mainnet --plan --preview
```

Preview output is bound to the complete prospective working tree and is
intrinsically non-production, non-executable, and ineligible for history. Once
the same bytes are reviewed and committed in a clean worktree, omit
`--preview` to produce a production-bound plan; production planning rejects
dirty, untracked, missing, symlinked, or non-HEAD planning inputs. Both
profiles use the same source without RPC, an account, key, signer, or history
creation. Typed-blocked output with `plan_hash=null` is correct while
external facts, deployment-produced identities, AAPL inputs, Curve inputs,
reward operational gates, owners, operators, or release inputs remain
unresolved. These blockers are configuration and operational inputs, not a
missing migration implementation.

Generate the matching pre-collected assertion envelope without live RPC:

```sh
python scripts/check_deployment.py --print-plan-expectations robinhood-testnet --preview
python scripts/check_deployment.py --print-plan-expectations robinhood-mainnet --preview
```

Do not create history, execute a plan, add a custom runner, or copy Base
migrations to make planning appear ready. No plan, synthetic fixture, fork
result, or passing test authorizes deployment.

### 5. Qualify locally and on a pinned archive fork

First prove static, unit, clean-local, negative, artifact, topology, omission,
and reproducibility gates with networking disabled. Then, only under a separate
H-09 authorization, use the exact accepted chain/block pin, identity manifest,
provider alias, process-isolation rules, and read-only archive-fork command in
the [deployment validation plan](robinhood-deployment-validation-plan.md).
Fork qualification may mutate only the disposable local fork; it does not
deploy or configure Robinhood.

### 6. Bind the operator and manifest environment

H-06 qualifies an operator/storage class only. Bind the frozen candidate to the
intended operator, machine, and mode-0700
local APFS volume. Candidate-class qualification is not a final binding. At
this phase use the [manifest operator runbook](robinhood-manifest-operator-runbook.md);
do not create or promote Robinhood history without exact later authority.

### 7. Rehearse on testnet

Obtain a new instruction naming the exact testnet plan, chain, account/signer,
provider, funding, allowed actions, abort rules, and evidence outputs. Rebuild
from frozen inputs, execute the authorized rehearsal, reconcile receipts and
post-state, exercise pause/abort/incident paths, and complete the required soak.
Offline and fork results do not grant this authority.

### 8. Assemble and review release evidence

Bind configuration, blockers closed, deterministic plans, artifacts,
constructors, manifests, qualification, testnet receipts, verification,
operators, signers, monitoring, pause/abort rules, rollback truth, and residual
risk in the [release-packet checklist](hardening/release-packet-evidence-checklist.md).
Packet completeness is not production authority.

### 9. Release only under a new exact authorization

An eventual production instruction must name the final commit/tree, plan and
artifact hashes, target profile, account/signer backend, operator, permitted
commands/actions, stop rules, and evidence destination. Deployment, migration,
role transfer, production/onchain configuration, activation, and release stay
separate lifecycle events and must be reported separately.

## What to do with draft PR #66

Do not rebase, merge, cherry-pick, or continue implementation directly from
PR #66 or `rh-deploy`. It remains useful as historical deployment-design input,
not current implementation authority; its configuration and Morpho changes are
already superseded by stronger implementations on current `rh`.

Its incompatible assumptions include `DefaultsRobinHood.vy` instead of the
authoritative `DefaultsRobinhood.vy`, five Defaults constructor arguments
instead of the current eight bindings, BlueChipYield in PriceDesk slot 2 and
priority IDs `[1,2,3]` instead of exact ID-1 Chainlink, ID-2 GREEN-only Curve,
ID-3 BlueChipYield with priorities `[1,3]`, an obsolete
Robinhood-mainnet-only migration namespace/order, a custom runner and history
workflow that bypass the deterministic planner, unresolved identities treated
as usable,
and currently deferred or excluded Deleverage, Curve higher-power/LP, PSM
activation, and CCIP work.

Deployment agents must consume current `config/BluePrint.py` and
`contracts/config/DefaultsRobinhood.vy` through the shared
`migrations/robinhood/` package and `python -m scripts.migrate`. PR #66 remains
historical input and must not be rebased, merged, or used as migration source.

Until required bindings close, deterministic typed-blocked plans are correct.
Do not create migration history, use the old custom runner, access RPC or
signers, or substitute placeholders merely to make a blocked plan executable.
The shared source follows the exact order and abort rules in the
[Curve launch migration handoff](curve-launch-migration-handoff.md). Its
presence and deterministic output do not authorize migration execution.

## Stop conditions and prohibited substitutions

Stop immediately if any of the following is true:

- local, cached, or live `rh`, the expected tree, source/artifact bytes, or a
  frozen plan identity drifts;
- the repository is not clean where a clean-input gate is required;
- the generator does not report `configuration_consistent=true`, the derived
  ledger differs, or the exact blocker set changes without reviewed source
  changes;
- an external fact lacks independent target-chain evidence or a
  deployment-produced identity lacks deterministic provenance;
- an owner, operator, signer, machine, volume, provider, pin, or authority is
  missing or differs from the reviewed packet;
- a command would require RPC, an account, key, signer, transaction, migration
  execution, history promotion, testnet action, or production action not named
  in a fresh exact authorization.

Never substitute a Base value, zero address, placeholder, stale PR value,
latest fork block, alternate endpoint, different signer, hand-edited ledger,
hand-edited generated JSON, custom migration runner, or historical evidence
for a required current binding. Never infer deployment readiness from
configuration consistency, compilation, a green test, fork qualification,
packet completeness, integration, or an earlier gate.
