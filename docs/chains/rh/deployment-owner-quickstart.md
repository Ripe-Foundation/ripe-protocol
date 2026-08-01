# Robinhood configuration owner quick-start

This page describes the Robinhood Profile 1 configuration-authoring workflow. It does not authorize or perform deployment, migration, activation, registration, configuration, RPC access, or signer use.

## Two editable value authorities

There are exactly two team/owner-editable configuration sources:

| Source | Owns |
|---|---|
| `config/BluePrint.py` | Addresses, chain identities and clocks, external oracle/feed/factory/protocol identities, governance/operator inputs, component and registry topology, constructor inputs, switchboard inputs, and every approved deployable value outside the Defaults interface |
| `contracts/config/DefaultsRobinhood.vy` | Every product, risk, permission, liquidation, priority, asset, reward, bond, HR, signer, and other value returned by the 17 getters in `interfaces/Defaults.vyi` |

The ownership tiebreaker is mechanical: if a value is returned by a Defaults getter, edit it in `DefaultsRobinhood.vy`; otherwise edit it in `BluePrint.py`.

`config/robinhood-parameters.json` is derived evidence. It retains owner/governance/provenance metadata, but its value-bearing fields are reconstructed from the two sources above. Do not edit a ledger value to change the product configuration.

`config/robinhood_blueprint.py` remains the structural policy model for types, lifecycle and gate metadata, relations, blockers, assertions, and the address-literal prohibition. It consumes or cross-checks source values; it is not a third value authority.

## Address ownership and constructor binding

Every nonzero chain-specific address literal lives only in `BluePrint.py`. Defaults receives its eight named identities through constructor arguments and immutables:

| Defaults constructor argument | Blueprint input | State |
|---|---|---|
| `contributorTemplate` | `CONTRIBUTOR_TEMPLATE` | deployment-produced, unresolved |
| `trainingWheels` | `TRAINING_WHEELS` | deployment-produced, unresolved |
| `ripeToken` | `RIPE_TOKEN` | deployment-produced, unresolved |
| `greenToken` | `GREEN_TOKEN` | deployment-produced, unresolved |
| `sgreenToken` | `SGREEN_TOKEN` | deployment-produced, unresolved |
| `usdgToken` | `USDG` | selected external fact, unverified |
| `wethToken` | `WETH` | selected external fact, unverified |
| `steakhouseUsdgVault` | `STEAKHOUSE_USDG_VAULT` | selected external fact, unverified |

This eight-argument ABI intentionally differs from PR #66's five-argument authoring precedent. PR #66 embedded three external-fact addresses; the canonical source lifts those values into Blueprint and passes them as `usdgToken`, `wethToken`, and `steakhouseUsdgVault`. Any future deployment migration must bind all eight arguments in the order above. This candidate creates no migration history and executes no migration.

`ZERO_ADDRESS` means an approved semantic absence. It must not stand in for an unresolved identity. Deployment-produced identities stay as explicit symbolic bindings until their own authority track resolves them.

## Profile 1 topology

The PriceDesk registry selection is:

| Slot | Selection |
|---|---|
| 1 | Chainlink |
| 2 | Empty; reserved for Profile 2 Curve |
| 3 | BlueChipYield |
| 4 | Empty Pyth slot |
| 5 | Empty Stork slot |

BlueChipYield slot 3 is selected. Commit `33ad0f3c08bf6dc88f6569c622886d264d6e2868` provides the integrated Morpho V2 production-source, ABI, artifact, and test compatibility. The selected Morpho factory and vault facts still require independent verification; source compatibility does not make deployment ready.

Profile 1 includes GREEN, RIPE, sGREEN, WETH, and SteakHouse USDG asset tuples. GREEN/USDG LP and RIPE/WETH LP remain omitted. Priority price-source IDs are `[1, 3]`, and sGREEN remains the priority stability asset.

## Owner workflow

1. Edit addresses, bindings, clocks, topology, and non-Defaults deployment inputs in `config/BluePrint.py`.
2. Edit Defaults-interface values directly in `contracts/config/DefaultsRobinhood.vy`.
3. Compile and synchronize the derived ledger:

```sh
python scripts/params/generate_robinhood_defaults.py
```

4. Review the resulting `config/robinhood-parameters.json` diff. Value changes must be traceable to Blueprint or Defaults; retained metadata must remain owner-maintained evidence.
5. Run the read-only consistency check:

```sh
python scripts/params/generate_robinhood_defaults.py --check
```

A healthy result reports `configuration_consistent=true`. Check mode compiles Defaults, reconstructs the ledger, compares canonical bytes, and performs no repository writes.

Both commands are local authoring operations. Neither command deploys, migrates, activates, registers, configures production, contacts an RPC endpoint, or uses an account or signer.

## Inspect unresolved readiness blockers

The synchronization check reports the blocker count without converting it into configuration drift. To list the exact unresolved or unverified bindings locally:

```sh
python -c 'from scripts.params.generate_robinhood_defaults import deployment_readiness; ready, blockers = deployment_readiness(); print(f"deployment_ready={str(ready).lower()} blockers={len(blockers)}"); print(*blockers, sep="\n")'
```

The current source-authority candidate is expected to be configuration-consistent while deployment readiness remains false. Typical blockers include:

- deployment-produced Contributor, TrainingWheels, RIPE, GREEN, and sGREEN identities;
- selected but independently unverified USDG, WETH, SteakHouse USDG vault, Chainlink feed, Morpho factory, governance, Safe, and sentinel facts;
- explicitly unresolved PSM, stock, LP, role, supply-recipient, promotion, and native-token inputs.

Resolve those only through their named owner and verification gates. Never fabricate a Robinhood address, copy a Base address, or query a live chain from this workflow.

## Fail-closed behavior

The check fails when:

- either canonical source is missing or Defaults does not compile with repository-default Vyper 0.4.3 settings;
- a Blueprint or Defaults value differs from the derived ledger;
- a ledger-only value edit attempts to override a source;
- an unknown ledger key, placeholder, or sensitive value appears;
- ownership is duplicate or missing;
- the canonical Defaults filename or casing is not unique;
- the launch partition, omissions, topology, or artifact/inventory bindings drift.

Configuration consistency is not deployment readiness. A green synchronization check grants no authority for deployment, migration execution, configuration activation, registration, release, RPC access, or signer use.
