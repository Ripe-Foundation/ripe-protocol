# PR 67 ABI, artifact, and deployment handoff

Status: implementation handoff for the integrated remediation candidate. This
document authorizes no deployment, registry action, manifest promotion, or
release.

> **Retired tooling (16 August 2026):** the commands and file references below
> that use `scripts/check_contract_artifacts.py`,
> `scripts/update_contract_artifact_expectations.py`, or
> `config/contract-artifact-expectations.json` are **not runnable**. That
> pipeline was deleted with the descoped Robinhood stock M4 launch binding.
> This page is retained as a dated record of the PR-67 handoff; do not execute
> its artifact commands. Measure the release tree directly instead.

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

1. `0008_UniswapV2Prices.py` deploys the stateless RIPE/WETH monitor, verifies
   its immutable identities and permanent no-feed interface, and never
   registers it in PriceDesk. It has no local governance or timelock to
   finalize.
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
4. Robinhood's CCIP lanes and RipeHq rows at ids 23 and 24 are already active,
   so this deployment does not rewire or redeploy either token pool.
   VaultMigrator registration and the BlueChip topology decision are deferred;
   no id 25 registry row is added by this release.
5. `2026082405_RedeployPr208.py` is the next Robinhood migration. It redeploys
   the PR #208 Switchboards, price infrastructure, vault infrastructure, and
   affected departments while retaining RipeHq, tokens, CCIP pools, Ledger,
   MissionControl, and the existing PriceDesk slot 3 monitor.
6. `2026082406_PromotePr208.py` promotes the authenticated candidates only after
   the Safe registry confirmations and required post-activation readbacks pass.

The promotion helper copies the candidate's complete record, including file,
ABI, compiler JSON, and canonical ABI-encoded constructor arguments. Every
caller supplies a reviewed literal source path. The helper requires that path
to equal the repository's canonical-name lookup and requires the filename stem
to equal the canonical contract name; an authenticated MissionControl record
cannot therefore be promoted as Ledger by changing the local lookup. It rejects
absolute/traversing/non-Vyper paths, empty or malformed ABI/compiler records,
and compiler records that do not contain the named source. The approved
compiler settings are exactly the primary source's full output selection and a
repository-root search path. Every compiler source is compared as exact UTF-8
bytes to its repository file, and a Vyper `sha256sum` field is verified when
present.

The manifest's exact pinned Vyper version must equal the installed build. The
helper recompiles the recorded standard JSON, rejects compile diagnostics or
an integrity mismatch, and requires the recompiled ABI to equal the recorded
ABI. Constructor bytes must decode and re-encode identically, which rejects
trailing bytes, and must equal the independent constructor values supplied by
the migration caller. The activated registry object must itself equal the
canonical manifest record for the named registry. Finally, the candidate
address must contain code whose length is exactly compiler-template length plus
Vyper code-layout length and whose prefix equals the complete compiled runtime
template. This is full runtime equality for contracts without code-data; for
immutable-bearing contracts it deliberately does **not** authenticate the
immutable suffix. The typed execution envelope must still bind the exact
creation input, receipt/address, and full deployed runtime before production
execution. Copying only an address would silently pair new code with the prior
generation's metadata and is forbidden. Candidate labels and prior timestamp
manifests remain preserved as evidence.

The 17 promotions in `0010` use one batch helper call. Every candidate,
source/compiler/runtime identity,
constructor, dependency, registry identity, and registry readback is
preflighted before any checkpoint write. The transaction log is then persisted
before the pending manifest, making a pure-promotion checkpoint immediately
resumable; the in-memory manifest advances only after the pending save
succeeds. JSON checkpoints use a same-directory temporary file, complete write,
file `fsync`, atomic replace, and directory `fsync`, so an interrupted partial
write cannot replace the prior JSON target. Resume loads that complete pending
snapshot as authoritative rather than recursively merging it with `current`, so
removed stale fields cannot reappear. A late batch mismatch cannot leave an
earlier canonical label promoted, while a failed pending save may retain its
intentional log journal but cannot advance the manifest or memory.

Resuming a logged `deploy` or `deploy_bp` requires the logged address to equal
both the pending record and returned contract. It recompiles the current exact
source/compiler/ABI record, binds the newly supplied constructor arguments, and
validates the recorded address's deployed code before reusing the pending entry
without regenerating it, preserving all metadata byte-for-byte. Standard
deployments use the same runtime-template/length check described above.
Blueprint resume is explicit: blueprint creation has empty arguments even when
the instance ABI declares a constructor, and the deployed code must exactly
equal the ERC-5202 `fe7100` preamble plus the recompiled creation bytecode. The
promotion validator remains stricter than that blueprint exception.

`DefaultsRobinhoodLive` has an additional dependency witness. Its activation
witness is MissionControl at RipeHq id 5, so before either record is promoted
the plan decodes `MissionControlCandidate0009`'s manifest constructor arguments
and requires `(RipeHq, DefaultsRobinhoodLiveCandidate0009)` exactly. It also
reads MissionControl's immutable RipeHq back on chain. MissionControl copies
Defaults into storage and deliberately retains no public Defaults pointer. The
generic helper therefore permits exactly this
`DefaultsRobinhoodLive`/`MissionControl`/RipeHq-id-5 policy, requires constructor
argument index 1, and decodes that address from the witness's recorded
constructor bytes before promotion. Other distinct-witness combinations fail
closed. The typed execution envelope must still bind the creation input and
deployment receipt; registry readback alone is not proof of the Defaults
dependency.

The already-recorded Robinhood Uniswap deployment predates the stripped
stateless monitor. Rewriting `0008` is not on-chain remediation. Bind and
classify the current address and runtime independently. Replacing it requires
a separately authorized deployment, exact constructor/runtime binding,
consumer update, and manifest transition; the old instance cannot be converted
in place by governance or a timelock action.

PriceDesk's `numAddrs()` is the next registry id. Before PR #206, live slot 3 is
the legacy functional UniswapV2Prices generation; priority IDs `[1, 2]` do not
exclude it from PriceDesk's fallback scan. PR #206's required `2026082100/01`
history replaces the complete PriceDesk tree and promotes the authenticated
inert monitoring-only UniswapV2Prices generation in slot 3, with cursor `4`.
BlueChip remains unassigned at chain-local ID `0`; this does not make slot 3
empty. Any future BlueChip proposal must bind the then-live cursor and choose a
chain-local ID in a separately reviewed migration rather than assuming `3` or
`4`. First promotion must support an absent canonical label while retaining
every candidate, witness, nonzero-address, and registry-readback check.

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

The forward stages are numbered after the independently recorded `2026082101`
Robinhood frontier. The first stage machine-checks that `2026082101` is its
immediate predecessor, so this branch cannot execute it while PR #206's history
is absent. They depend on integrating PR #206's executed-history and
current-manifest update at commit `452053044de5fafa09e2c8acb9638cb61bdbce28`
before execution; PR 67's older manifest is not live authority.
They use the canonical `migration.deploy`/`migration.execute` API and are
reachable only through an explicit `--start-timestamp` after the integrated
frontier. The
transaction journal binds calls to chain, sender, target, value, and calldata;
Solidity deployment resume additionally binds Foundry artifact, creation input,
address, and live runtime. Preserve the candidate-before-activation and
readback-before-promotion order above.

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
immutable-bearing contract. After source freeze and one clean 18-contract Boa
capture, the exact final regeneration sequence is:

```bash
PR67_RUNTIME_DIR=/private/tmp/pr67-final-runtime-capture
python scripts/capture_contract_runtimes.py \
  --output-dir "$PR67_RUNTIME_DIR"

python scripts/export_abis.py

python scripts/update_contract_artifact_expectations.py \
  --capture-manifest "$PR67_RUNTIME_DIR/capture-manifest.json" \
  --deployed-runtime AuctionHouse="$PR67_RUNTIME_DIR/AuctionHouse.runtime" \
  --deployed-runtime BlueChipYieldPrices="$PR67_RUNTIME_DIR/BlueChipYieldPrices.runtime" \
  --deployed-runtime CreditEngine="$PR67_RUNTIME_DIR/CreditEngine.runtime" \
  --deployed-runtime DefaultsRobinhood="$PR67_RUNTIME_DIR/DefaultsRobinhood.runtime" \
  --deployed-runtime Deleverage="$PR67_RUNTIME_DIR/Deleverage.runtime" \
  --deployed-runtime Ledger="$PR67_RUNTIME_DIR/Ledger.runtime" \
  --deployed-runtime Lootbox="$PR67_RUNTIME_DIR/Lootbox.runtime" \
  --deployed-runtime MissionControl="$PR67_RUNTIME_DIR/MissionControl.runtime" \
  --deployed-runtime RipeGov="$PR67_RUNTIME_DIR/RipeGov.runtime" \
  --deployed-runtime SimpleErc20="$PR67_RUNTIME_DIR/SimpleErc20.runtime" \
  --deployed-runtime StabilityPool="$PR67_RUNTIME_DIR/StabilityPool.runtime" \
  --deployed-runtime SwitchboardAlpha="$PR67_RUNTIME_DIR/SwitchboardAlpha.runtime" \
  --deployed-runtime SwitchboardBravo="$PR67_RUNTIME_DIR/SwitchboardBravo.runtime" \
  --deployed-runtime SwitchboardCharlie="$PR67_RUNTIME_DIR/SwitchboardCharlie.runtime" \
  --deployed-runtime SwitchboardDelta="$PR67_RUNTIME_DIR/SwitchboardDelta.runtime" \
  --deployed-runtime Teller="$PR67_RUNTIME_DIR/Teller.runtime" \
  --deployed-runtime UniswapV2Prices="$PR67_RUNTIME_DIR/UniswapV2Prices.runtime" \
  --deployed-runtime VaultMigrator="$PR67_RUNTIME_DIR/VaultMigrator.runtime" \
  --require-deployed-runtime-bindings

python scripts/export_abis.py --check
python scripts/check_contract_artifacts.py \
  --require-deployed-runtime-bindings
```

No positional contract filter is allowed in this final sequence: strict mode
rejects filters, requires the exact 18 runtime inputs plus their completed
capture manifest, and rebuilds the exact 19-record governed set. The capture
command must run from the repository root after `contracts/` and `interfaces/`
are clean in Git, and its output path must not already exist. It writes into a
private sibling staging directory, records the exact repository HEAD/tree,
capture-script hash, toolchain, source hashes, constructor inputs, prospective
state/readback obligations, and runtime hashes, writes the completion manifest
last, then atomically publishes the directory. The updater rejects a mixed,
stale, incomplete, foreign-worktree, or differently configured generation.

The generated
`DefaultsRobinhoodLive` has no immutable code-data suffix, so its compiler
runtime template is already its full deployed-runtime identity and it is the
sole governed record that does not need a capture file.

ABI export compiles and preflights the complete inventory before mutation,
atomically replaces each generated ABI, and publishes
`scripts/abis/.abi-export-complete` only after the whole output set succeeds.
`--check` requires that seal to match every generated ABI hash, so an interrupted
or mixed generation cannot report current. The expectations JSON is likewise
written through a same-directory temporary file, `fsync`, and atomic replace.

For each measured runtime, the updater requires:

- exact total length equal to template length plus code-layout length;
- the complete compiler runtime template as the deployed-code prefix;
- exact immutable suffix bytes and SHA-256; and
- exact full deployed-runtime SHA-256 and EIP-170 headroom.

Final integration must deploy every governed immutable-bearing contract with
the exact approved constructor arguments in one clean Boa graph, capture the
raw `env.get_code` bytes outside the repository, refresh the final source and
ABI records, then run the strict checker. The runtime identity proves code plus
immutable code data. It does **not** prove storage-only constructor effects or
post-deployment state: Teller's pause bit, MissionControl's Defaults-derived
configuration, Deleverage's stored policy, temporary-governance relinquishment,
and action-timelock setup still require the typed execution receipt and named
readbacks recorded in the capture manifest. Do not derive a deployed-runtime
hash from the template or refresh hashes merely to make the gate pass.

The updater's final governed set contains 19 records and adds
`BlueChipYieldPrices`, the generated `DefaultsRobinhoodLive`, integrated
`SwitchboardAlpha`, and integrated `SwitchboardCharlie` to the prior 15-record
ledger. BlueChip must replace its standalone template-only frozen facts with a
constructor-bound runtime record; Defaults must bind the exact generated source
that the typed execution envelope supplies to MissionControl and Ledger; Alpha
and Charlie must bind their final integrated capability-check sources and
immutable code data, while their storage/post-setup state remains a separate
readback gate. Update the inventory
test's exact required-name set in the same final expectation refresh. The
integrated `VaultMigrator` source also changed after the reviewed PR head and
must be measured from those final bytes.

`config/contract-artifact-expectations.json`, the ABI completion seal, and the
18-runtime capture remain deliberately ungenerated until the final production
sources are frozen and clean. Do not commit a partial generation.
