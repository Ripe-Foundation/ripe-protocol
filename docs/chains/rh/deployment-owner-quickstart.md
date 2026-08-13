# Robinhood deployment-owner quick-start

> **11 August 2026 removal overlay:** The unused deployment tooling this
> quick-start drives has been removed: `scripts/check_deployment.py` and
> `scripts/utils/deployment_assertions.py`, which step 5 invokes, and
> `scripts/utils/manifest_schema.py` with the H-06 manifest-v2 writer and
> promotion gate that step 6 binds. The migrations themselves are unchanged and
> still deploy through `scripts/migrate.py`. Steps 5 and 6 no longer describe
> anything that runs; they are retained as the record of the intended method.
> Removed sources are recoverable from git history.

This is the sole canonical human handoff for the Robinhood deployment owner and
the deployment owner's agents. It is operational guidance, not execution
authority. Nothing here authorizes RPC access, accounts, keys, signers,
transactions, migration execution, testnet work, production configuration,
activation, release, or Sites actions.

## Current baseline and candidate

The exact live `rh` parent reviewed for this candidate is commit
`0372d48680c281ddaafe2f1982f0bcfa851071c9`, tree
`79fdc69de22eb8cfa2be3a2067c596d5fed92963`.

Draft PR #73 contains the production-remediation source candidate commit
`e12b1abe26218acb804d84670099c41169e5f515`, tree
`b680f0016f29f9a217054db9f80c0bbf9f0b9916`, on branch
`codex/rh-production-vyper-remediation-integration`, followed only by this
status-authority reconciliation. Rebind the production-source identity after
any production/configuration change. A PR, merge, or passing suite still does
not authorize deployment, configuration, activation, or release.

Repository configuration is prepared and consistent; production/onchain
configuration has not occurred.

Ready to begin deployment preparation.

- `DefaultsRobinhood.vy` exists, compiles, and is source-authoritative.
- The derived parameter ledger is synchronized.
- The H-04 register has 22 rows: 21 approved and operative, one retired and
  non-operative, and zero open.
- All 28 canonical H-03 blockers remain open, including nine Curve-specific
  blockers.
- `configuration_consistent=true`; `deployment_ready=false`; 64 unresolved or
  unverified bindings currently prevent deployment readiness.
- The current candidate uses eight imperative migration files,
  `migrations/robinhood-mainnet/0000_TokensAndHq.py` through
  `0007_FinishSetup.py`.
- No executable migration plan is authorized or currently censused. The former
  17-stage declarative plan, runner, transaction executor, action census, and
  86-key plan census are retired historical evidence.
- No non-CCIP Robinhood launch deployment or migration has occurred. Separately,
  GREEN/RIPE CCIP topology and token-specific capabilities are confirmed live;
  that external fact authorizes no further transaction or release. Nothing else
  in the launch candidate has been configured onchain, activated, or released.

[`status.yaml`](status.yaml) is the sole machine-readable current-status
authority. The [production-remediation correction](rh-production-vyper-remediation.md)
records the current candidate deltas. Earlier reassessment, Curve, reward, and
transaction-executor records remain historical design or risk evidence where
they conflict with current source and status.

## Current launch projection

The selected asset tuples are WETH, RIPE, sGREEN, and GREEN. SteakHouse USDG
is not a current Defaults constructor binding or selected asset.

| PriceDesk slot | Current state |
| --- | --- |
| 1 | Chainlink selected |
| 2 | Unchanged CurvePrices selected for GREEN only |
| 3 | BlueChipYield structurally selected in the blueprint, but not deployed or finalized by the current migration candidate |
| 4 | Empty Pyth |
| 5 | Empty Stork |

Priority price-source IDs are `[1, 2]`. The configured GREEN route is GREEN ->
Curve GREEN/USDG -> PriceDesk -> Chainlink USDG. USDG has no Curve feed. No
Uniswap price source is admitted or deployed, and neither GREEN/USDG nor
RIPE/WETH LP is admitted as a Ripe asset.

Current source assigns `1,000,000e18` RIPE to rewards, zero to HR, and
`1,000,000e18` RIPE to bonds. `rewardsConfig()` enables points at
`0.009 RIPE/block`, assigns 10% to borrowers and 90% to stakers, assigns zero
to voters and general depositors, uses a 75% conditional auto-stake ratio and
33% duration ratio, and pays `1 RIPE/$` Stability claims. Stock rewards remain
disabled. Operational reward promotion remains blocked.

## Exactly two editable value authorities

| Team/owner-editable source | Exact ownership |
| --- | --- |
| [`config/BluePrint.py`](../../../config/BluePrint.py) | Every Defaults constructor argument and immutable identity; deployment-produced and external address bindings; chain identities and clocks; component and registry topology; governance/operator/role inputs; and every other non-Defaults deployment input. |
| [`contracts/config/DefaultsRobinhood.vy`](../../../contracts/config/DefaultsRobinhood.vy) | Product and configuration values encoded directly in Defaults getter bodies, excluding constructor-bound identities. |

The mechanical ownership precedence is controlling:

1. Defaults constructor arguments, immutable identities, deployment-produced
   addresses, and external address bindings are owned by `config/BluePrint.py`,
   even when a Defaults getter later returns them.
2. Product and configuration values encoded directly in Defaults getter bodies
   are owned by `contracts/config/DefaultsRobinhood.vy`.
3. All other non-Defaults deployment inputs are owned by `config/BluePrint.py`.

The current ordered Defaults constructor identities are ContributorTemplate,
TrainingWheels, RIPE, GREEN, sGREEN, USDG, and WETH. Preserve their order and
ownership. Do not restore the historical SteakHouse USDG constructor input.

Two adjacent files are not value authorities:

- [`config/robinhood-parameters.json`](../../../config/robinhood-parameters.json)
  is synchronized, derived evidence. Never hand edit it to change a value.
- [`config/robinhood_blueprint.py`](../../../config/robinhood_blueprint.py) is
  structural policy and validation, not a third product-value surface.

## Synchronize and check

After editing either value authority, synchronize the derived ledger:

```sh
python scripts/params/generate_robinhood_defaults.py
```

Review the `config/robinhood-parameters.json` diff, then run the read-only
check:

```sh
python scripts/params/generate_robinhood_defaults.py --check
```

The current healthy result is:

```text
configuration_consistent=true deployment_ready=false blockers=64
```

List every unresolved or unverified deployment blocker without using RPC:

```sh
python -c 'from scripts.params.generate_robinhood_defaults import deployment_readiness; ready, blockers = deployment_readiness(); print(f"deployment_ready={str(ready).lower()} blockers={len(blockers)}"); print(*blockers, sep="\n")'
```

Configuration consistency proves that the two sources reconstruct the derived
ledger. Deployment readiness additionally requires external verification and
resolution of deployment-produced and owner bindings. Never collapse those
gates.

## Deployment-owner sequence

### 1. Freeze the exact repository candidate

Confirm clean-worktree status and parity among local `rh`, cached `origin/rh`,
and credential-free live `rh`. Bind the exact parent commit/tree, candidate
commit/tree, source diff, artifact expectations, and validation evidence. Stop
on drift.

### 2. Close the 64 readiness bindings

Classify every unresolved binding by its named owner. The nine Curve items are
the official AddressProvider plus IDs 7, 11, 12, and 13; the deployment-produced
pool address; the slippage limit; minimum retained liquidity; and production
observation. Preserve every unresolved value as blocked. Do not use RPC merely
because an address literal exists in source.

### 3. Synchronize source authority

Edit only the two value authorities, regenerate the ledger, review its complete
diff, and require the read-only check to remain byte-consistent. A healthy
result remains `deployment_ready=false` until all deployment bindings close.

### 4. Review the imperative migration candidate

Review the eight current `migrations/robinhood-mainnet/` files in order. Confirm
component omissions, constructor inputs, registrations, configuration, final
assertions, and governance transfer behavior against the two source
authorities. Do not restore or invoke the retired declarative runner or
transaction executor. H-05 remains deterministic repository review; no
executable plan or migration history is authorized.

### 5. Freeze offline artifacts and expectations

Compile in clean isolated environments and freeze source, compiler, ABI,
creation/runtime bytecode, constructors, storage layout, registries, topology,
and omission identities. The checker consumes pre-collected observations and
does not authorize live collection:

```sh
python scripts/check_deployment.py --print-template expectations
python scripts/check_deployment.py --print-template local_deployment
python scripts/check_deployment.py --print-template deployed_observation
```

### 6. Bind H-06 to the intended operator environment

H-06 qualifies a macOS/APFS operator/storage class only. Bind the frozen
candidate to the intended operator, machine, and mode-0700 local APFS volume.
Candidate-class qualification is not final operational, history-publication,
deployment, or release authority. Follow the
[manifest operator runbook](robinhood-manifest-operator-runbook.md).

### 7. Complete local and fork qualification

First prove static, unit, clean-local, negative, artifact, topology, omission,
and reproducibility gates with networking disabled. Use a pinned read-only
archive fork only after a separate H-09 authorization names the exact pin,
provider, identities, commands, evidence, and stop rules. Fork qualification is
not deployment authority.

### 8. Rehearse only under an exact testnet authorization

A later instruction must name the exact candidate, network, provider,
account/signer, funding, allowed actions, abort rules, and evidence outputs.
Offline and fork results do not grant this authority.

### 9. Assemble the release packet

Bind configuration, closed blockers, artifacts, constructors, qualification,
rehearsal receipts, verification, operators, signers, monitoring, pause/abort
rules, rollback truth, and residual risk in the
[release-packet checklist](hardening/release-packet-evidence-checklist.md).
Packet completeness is not production authority.

### 10. Deploy, configure, activate, or release only under new authority

Each external-state phase requires a fresh exact authorization naming the
commit/tree, artifacts, target profile, account/signer, operator, commands,
permitted actions, stop rules, and evidence destination. Treat deployment,
migration execution, production configuration, activation, and release as
separate lifecycle events.

## Conditional post-deployment asset retirement

This procedure applies only after a separately reviewed MissionControl runtime
containing the `active points alloc` guard and a hardened SwitchboardCharlie
runtime that checks MissionControl's boolean return have both been deployed and
made authoritative. A source merge, passing suite, or artifact update does not
change either deployed runtime or authorize either transition.

The rollout therefore contains two contract deployments. Bind and review each
runtime and deployed address separately. For SwitchboardCharlie, also verify
its Switchboard registration, governance permission, and action-timelock
wiring before relying on the execution-time revert behavior. Do not infer that
deploying or activating the guarded MissionControl also activates the hardened
Charlie behavior. The reviewed Charlie candidate has 703 bytes of EIP-170
deployed-runtime headroom; recompile and recheck that gate after every further
Charlie change rather than carrying this measurement forward by assumption.

Asset retirement is then two governed timelock actions, not one:

1. Read the complete live `AssetConfig`. Through
   `SwitchboardBravo.setAssetDepositParams`, preserve the live vault IDs and
   deposit limits while setting both fixed reward allocations to zero.
2. Execute the Bravo action and verify both fields are zero and the global
   staker/voter totals decreased by exactly the former allocations.
3. Execute the existing `SwitchboardCharlie.deregisterAsset` action and verify
   the asset is unsupported and the totals did not decrease a second time.

Do not reconstruct the deposit tuple from defaults. If Bravo rejects the live
sibling fields because a limit is now invalid or a retained VaultBook ID is no
longer valid, stop and deliberately repair or replace only the offending field
in the same reviewed deposit-configuration action; record the deviation and
its evidence rather than guessing a value.

Once the hardened SwitchboardCharlie runtime is live, Charlie execution
requires MissionControl to return `True`. If a concurrent or duplicate action
already removed the asset, execution reverts `invalid asset`, does not emit a
second `AssetDeregistered`, and leaves the action available for normal
cancellation or expiry. Before execution, recheck that the asset is supported,
and after execution verify final MissionControl state as well as the event.

The hardened Charlie applies the same success requirement to
`deregisterVaultAsset`. If the vault still has a nonzero `totalBalances` value
for the asset, or the asset is already unregistered from that vault, execution
reverts `invalid vault asset`, emits no `VaultAssetDeregistered`, and leaves the
action available for retry, cancellation, or expiry. Verify the vault balance
is zero immediately before execution and verify vault support state afterward.

## Historical inputs

PR #66, the former `migrations/robinhood/` declarative package, its custom
runner, the transaction-executor candidate, the 17-stage and action censuses,
the 86-key plan census, the shared 1,000-RIPE analysis, and priority IDs
`[1, 3]` remain historical inputs. Do not rebase, merge, execute, or use them as
current configuration or migration authority.

The current candidate intentionally omits BlueChipYield deployment even though
the structural blueprint retains ID 3. Do not infer deployed topology from the
blueprint and do not invent an alternate registration merely to reconcile the
two. Resolve that boundary through a separately reviewed production change if
the owner later wants BlueChipYield deployed.

## Stop conditions and prohibited substitutions

Stop immediately if:

- local, cached, or live `rh`, the expected tree, source/artifact bytes, or a
  frozen candidate identity drifts;
- a clean-input gate finds a dirty repository;
- the generator is not byte-consistent or the exact blocker set changes
  without reviewed source changes;
- an external fact lacks independent target-chain evidence or a
  deployment-produced identity lacks deterministic provenance;
- an owner, operator, signer, machine, volume, provider, pin, or authority is
  missing or differs from the reviewed packet; or
- a command would require RPC, an account, key, signer, transaction, migration
  execution, history creation or promotion, testnet action, or production
  action not named in a fresh exact authorization.

Never substitute a Base value, zero address, placeholder, stale PR value,
latest fork block, alternate endpoint, different signer, hand-edited ledger,
hand-edited generated JSON, retired migration runner, or historical evidence
for a current binding. Never infer deployment readiness from configuration
consistency, compilation, a green suite, fork qualification, packet
completeness, integration, or an earlier lifecycle gate.
