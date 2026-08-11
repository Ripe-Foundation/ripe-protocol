# PR 67 ABI, artifact, and deployment handoff

Status: implementation handoff for the integrated remediation candidate. This
document authorizes no deployment, registry action, manifest promotion, or
release.

Bound review range:

- base: `91eda49ccd34a25090582aff0695075c4c806011`
- reviewed PR head: `02468586d710e2cce2360c2bc07e94de6ebdab29`

Final ABI hashes and artifact identities are deliberately not recorded here.
The C1, C2, and C3 contract lanes change production source after the reviewed
head, so those generated values must be produced once from the final
integrated bytes.

## Accepted ABI removals

The owner accepted the removals below and did not request compatibility
wrappers. Vyper expands default arguments into multiple ABI entries, so four
conceptual Teller methods account for 22 removed selectors.

| Removed Teller family | Removed ABI overloads | Supported replacement |
| --- | ---: | --- |
| `buyFungibleAuction` | 6 | `buyManyFungibleAuctions(tuple[], ...)` |
| `redeemCollateral` | 6 | `redeemCollateralFromMany(tuple[], ...)` |
| `claimFromStabilityPool` | 4 | `claimManyFromStabilityPool(uint256, tuple[], ...)` |
| `redeemFromStabilityPool` | 6 | `redeemManyFromStabilityPool(uint256, tuple[], ...)` |

The exact removed Teller signatures are:

```text
buyFungibleAuction(address,uint256,address)
buyFungibleAuction(address,uint256,address,uint256)
buyFungibleAuction(address,uint256,address,uint256,bool)
buyFungibleAuction(address,uint256,address,uint256,bool,bool)
buyFungibleAuction(address,uint256,address,uint256,bool,bool,bool)
buyFungibleAuction(address,uint256,address,uint256,bool,bool,bool,address)
claimFromStabilityPool(uint256,address,address)
claimFromStabilityPool(uint256,address,address,uint256)
claimFromStabilityPool(uint256,address,address,uint256,address)
claimFromStabilityPool(uint256,address,address,uint256,address,bool)
redeemCollateral(address,uint256,address)
redeemCollateral(address,uint256,address,uint256)
redeemCollateral(address,uint256,address,uint256,bool)
redeemCollateral(address,uint256,address,uint256,bool,bool)
redeemCollateral(address,uint256,address,uint256,bool,bool,bool)
redeemCollateral(address,uint256,address,uint256,bool,bool,bool,address)
redeemFromStabilityPool(uint256,address)
redeemFromStabilityPool(uint256,address,uint256)
redeemFromStabilityPool(uint256,address,uint256,address)
redeemFromStabilityPool(uint256,address,uint256,address,bool)
redeemFromStabilityPool(uint256,address,uint256,address,bool,bool)
redeemFromStabilityPool(uint256,address,uint256,address,bool,bool,bool)
```

StabilityPool intentionally removes these public conversion views:

```text
sharesToValue(address,uint256,bool)
valueToShares(address,uint256,bool)
```

The internal module helpers remain implementation details. Consumers that
need protocol value should use the retained `getTotalValue` and
`getTotalUserValue` views; consumers that need shares must not reconstruct
state-changing share math off chain and present it as an execution quote.

StabilityPool also removes the no-longer-emitted event:

```text
VaultFundsRecovered(address,address,uint256)
```

It adds lifecycle events `ClaimAssetActivated`, `ClaimAssetDeactivated`, and
`ClaimAssetLeftDormant`. Indexers must treat that as an event-schema migration,
not as an event rename with equivalent semantics.

## Consumer inventory

The repository inventory at the reviewed head found:

- no production Vyper, migration, configuration, or parameter-script call to
  any removed Teller selector;
- retained direct calls to AuctionHouse, CreditRedeem, and StabilityPool's
  underlying single-item functions. Those are contract-to-contract surfaces,
  not calls to the removed Teller wrappers;
- retained StabilityPool module tests that exercise the underlying
  Teller-gated claim/redeem functions directly;
- explicit Teller tests asserting all four removed wrapper names are absent;
- deterministic `scripts/export_abis.py --check` coverage for the checked-in
  `scripts/abis/` directory; and
- old ABI entries inside Base and Robinhood `current-manifest.json` files.
  Those manifests describe the generation that was deployed when each record
  was produced. They are not the canonical SDK ABI inventory and must not be
  rewritten to pretend an old deployment had new bytecode.

The repository cannot prove the absence of off-repository consumers. Before
activating a replacement Teller or StabilityPool, the release owner must
inventory at least the web application, SDK/package releases, keeper and
liquidation bots, analytics/indexers, saved Safe transactions, monitoring
probes, and partner integrations. Every discovered consumer must move to the
batch ABI or explicitly attest that it never used the removed surface. An
unknown external inventory blocks activation; it is not a reason to restore
the wrappers without a demonstrated need.

## Deployment and manifest lifecycle

The corrected Robinhood forward sequence is deliberately multi-stage:

1. `0008_UniswapV2Prices.py` deploys Uniswap for direct monitoring, finalizes
   its timelock, relinquishes temporary local governance, and never registers
   it in PriceDesk.
2. `0009_RedeployStaleContracts.py` deploys 16 replacements under unique
   `*Candidate0009` labels, finalizes the four Switchboards under temporary
   local governance, and emits the HumanResources pre-activation setup call
   plus actual Safe start/confirm calldata. HumanResources timelock readback is
   required before its registry start. The prior canonical manifest records
   remain current.
3. After the Safe confirmations execute, `0010_RedeployLedger.py` reads every
   registry slot and all five replacement action timelocks, promotes the
   complete 0009 records, deploys four interlocked replacements under
   `*Candidate0010`, and emits their Safe calldata. Those four confirmations
   must execute atomically.
4. After that atomic activation, `0011_BlueChipYieldPricesCandidate.py` verifies
   and promotes 0010, deploys/finalizes a Morpho V2-capable BlueChip candidate,
   and emits the Safe calls that add PriceDesk slot 3.
5. `0012_PromoteBlueChipYieldPrices.py` advances the canonical BlueChip
   manifest record only after slot-3 readback equals the candidate.
6. `0013_VaultMigratorCandidate.py` requires RipeHq's next id to be exactly
   25, deploys an unpaused Robinhood candidate with a zero Base-legacy-vault
   binding, and emits the Safe calls that append it. It neither reserves nor
   changes the CCIP rows at ids 23 and 24.
7. `0014_PromoteVaultMigrator.py` creates the first canonical VaultMigrator
   manifest record only after RipeHq id 25 equals the candidate.

The promotion helper copies the candidate's complete record, including file,
ABI, compiler JSON, and constructor arguments. Copying only its address would
silently pair new code with the prior generation's metadata and is forbidden.
Candidate labels and prior timestamp manifests remain preserved as evidence.

`DefaultsRobinhoodLive` has an additional dependency witness. Its activation
witness is MissionControl at RipeHq id 5, so before either record is promoted
the plan decodes `MissionControlCandidate0009`'s manifest constructor arguments
and requires `(RipeHq, DefaultsRobinhoodLiveCandidate0009)` exactly. It also
reads MissionControl's immutable RipeHq back on chain. MissionControl copies
Defaults into storage and deliberately retains no public Defaults pointer, so
the typed execution envelope must bind the creation input and deployment
receipt; registry readback alone is not proof of the Defaults dependency.

The already-recorded Robinhood Uniswap deployment predates the corrected
temporary-governance flow. Rewriting `0008` is not on-chain remediation. Bind
the current address and full deployed runtime, read `governance()` and
`actionTimeLock()`, and if the timelock is still zero use the separately
authorized RipeHq governance path to finalize that existing monitoring
instance. A tempGov-zero instance is already locally relinquished and cannot
execute `relinquishGov()` because the stored local governor is zero.

PriceDesk's `numAddrs()` is the next registry id. With Chainlink and Curve in
slots 1 and 2, the BlueChip precondition is `numAddrs() == 3` and
`getAddr(3) == 0`. Keep an exclusive PriceDesk-add window through the
timelock, require the confirmation to return id 3, and read slot 3 back before
the first canonical `BlueChipYieldPrices` record is created. First promotion
must support an absent canonical label while retaining every candidate,
witness, nonzero-address, and registry-readback check.

The Morpho V2 address remains a selected external fact until the execution
envelope binds the target chain, code-bearing address, runtime identity, and
expected membership selector. A nonzero configuration string is not that
evidence.

RipeHq also uses next-id semantics. Before the VaultMigrator append, bind and
read back the approved RIPE and GREEN CCIP pools at ids 23 and 24, require
`numAddrs() == 25`, and require `getAddr(25) == 0`. Keep an exclusive RipeHq
append window until confirmation and require `confirmNewAddressToRegistry` to
return 25. A next id of 23 or 24 blocks this plan; filling those rows with
sentinels or registering VaultMigrator under another id would break the
hardcoded Addys/Teller authority path. The candidate must report unpaused, and
its full deployed runtime must bind constructor arguments `(RipeHq, false,
zero-address)` on Robinhood before activation.

### Static-plan boundary

`migrations/robinhood-mainnet/0008_*.py` through `0014_*.py` use the legacy
`migration.deploy`/`migration.execute` API. The H-06 Robinhood runner
intentionally marks this history profile as manifest v2 and rejects those
methods. The files and fake-migration tests therefore establish the intended
constructor arguments, candidate labels, calldata, ordering, and readback
postconditions, but they are not executable through the canonical production
CLI.

Before any Robinhood action, the sequence must be converted into reserved,
typed `MIGRATION_STAGE` actions, bound to the accepted execution envelope and
source identities, and handed to the separately authorized H-06 executor.
That conversion must preserve the candidate-before-activation and
readback-before-promotion semantics above. Do not weaken `_manifest_v2`, route
around the executor, or describe these static modules as deployment-ready.

The historical Base PriceDesk callers now supply both constructor additions:
the temporary-governance position and an explicit zero Morpho V2 address.
Base does not silently inherit the Robinhood factory.

## Full deployed-runtime binding

Vyper's `bytecode_runtime` output is a template when a contract has immutable
code data. Template length plus `code_layout` length proves only a size; it
does not identify the constructor-bound deployed bytes. The artifact checker
now supports exact immutable-suffix and full-runtime bindings and provides a
strict gate:

```text
python scripts/check_contract_artifacts.py \
  --require-deployed-runtime-bindings
```

The updater accepts raw deployed bytecode captured from
`env.get_code(contract.address)`. When existing expectations are still
unbound, the strict refresh must supply a runtime for every governed
immutable-bearing contract, not only the example contracts below:

```text
python scripts/update_contract_artifact_expectations.py \
  --deployed-runtime ContractA=/private/path/ContractA.runtime \
  --deployed-runtime ContractB=/private/path/ContractB.runtime \
  --require-deployed-runtime-bindings \
  ContractA ContractB ...
```

For each measured runtime, the updater requires:

- exact total length equal to template length plus code-layout length;
- the complete compiler runtime template as the deployed-code prefix;
- exact immutable suffix bytes and SHA-256; and
- exact full deployed-runtime SHA-256 and EIP-170 headroom.

Final integration must deploy every governed immutable-bearing contract with
the exact approved constructor arguments in one clean Boa graph, capture the
raw `env.get_code` bytes outside the repository, refresh the final source and
ABI records, then run the strict checker. Do not derive a deployed-runtime hash
from the template or refresh hashes merely to make the gate pass.

The updater's final governed set adds `BlueChipYieldPrices`, the generated
`DefaultsRobinhoodLive`, and the integrated `SwitchboardAlpha` to the existing
ledger. BlueChip must replace its standalone template-only frozen facts with a
constructor-bound runtime record; Defaults must bind the exact generated
source used by MissionControl and Ledger; Alpha must bind the final integrated
capability-check source and constructor. Update the inventory test's exact
required-name set in the same final expectation refresh. The integrated
`VaultMigrator` source also changed after the reviewed PR head and must be
measured from those final bytes.

`config/contract-artifact-expectations.json` is intentionally not regenerated
in this lane because the final C1/C2/C3 production bytes are not yet integrated.
