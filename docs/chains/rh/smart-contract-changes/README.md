# Robinhood smart-contract change rationale

This directory is the contract-centric explanation of every Vyper and Solidity
contract-language source change represented by the current Robinhood (`rh`)
branch. It separates current `master..rh` production deltas from configuration,
archival prototypes, supporting/test-only sources, documentation examples, and
historical changes whose source bytes are now shared by `master` and `rh`.

> [!IMPORTANT]
> Source integration, selected repository configuration, deployment,
> registration, activation, and release are separate lifecycle states. Nothing
> in this directory authorizes an RPC call, signer, deployment, migration,
> onchain configuration, registration, activation, or release.

## Documentation standard

Each page distinguishes current integrated facts from dated historical
validation, current local artifact evidence, unresolved risks, and later
deployment or release gates. Historical commits, counts, and hashes remain
dated evidence; a current rebind is added rather than rewriting their original
meaning. Source rationale does not expand owner authority.

## Current authority and ancestry

This refresh is bound to the following independently verified identities on
3 August 2026:

| Ref or role | Commit | Tree | Meaning |
| --- | --- | --- | --- |
| Current local/cached/live `rh` | `0642f086d19e3cc62faaf67da096b6511e405320` | `d869d4149380b368f9678ed03efc0b59a6c804e2` | Authority for every current claim in this directory |
| Current local/cached/live `master` | `91eda49ccd34a25090582aff0695075c4c806011` | `fbd958bec234081f70769045abd8f9bb638f6dd7` | Comparison point and merge base for `master..rh` |
| Configuration-source ancestor | `e4473ce6485888f1b747761a5ee8693443108877` | `33b705690007bda9b11900b5775bd9230e79f09e` | Ancestor that last changed `DefaultsRobinhood.vy`; not the current `rh` tip |
| Shared-source import ancestor | `ad831669943ccfe7b9ed57454995dfce51630a66` | `3467f4a75aa37203d615407d5baf9c5fc9035639` | Historical `rh` import of corrected Deleverage work |

### Related authority drift outside this directory

[`status.yaml`](../status.yaml#L6-L15) remains dated 1 August and binds its
program subject to `5f5d22b7…`. Later edits updated its candidate metadata, but
its H-05 workstream still labels the transaction executor
[`candidate_not_integrated`](../status.yaml#L778-L789), even though
`27f21ccc…` is now an ancestor of current `rh`. The file remains consistent on
the controlling lifecycle boundary—80 source/configuration blockers, 100
executable-plan blockers, and no deployment, migration execution,
configuration, activation, or release—but it is not current for post-snapshot
source/integration identity. This directory therefore binds current source
claims directly to the verified Git identities above. Reconciliation of the
separate dashboard authority is outside this folder refresh.

The live ref checks establish repository identity only. They do not establish a
Robinhood deployment or live protocol state.

## Complete current production-source delta

The following feature-candidate production source paths include the current
Robinhood delta plus the BasicVault fail-closed changes in this worktree. The
shared ERC-20 modules alter their transitive compiled artifacts:

| Contract | Rationale | Git blob | SHA-256 | Source bytes | Current source disposition |
| --- | --- | --- | --- | ---: | --- |
| `contracts/core/Teller.vy` | [`teller.md`](teller.md) | `7019b6c47dde03151acc1952944dd19301c83328` | `4afc6ce1ccf21cb65e04ce3c56fedcf60bb79cba8e7dc51fd855a1f1f82bd909` | 41,106 | Exact call-local receipt and vault-return policy |
| `contracts/vaults/modules/BasicVault.vy` | [`basic-vault-fail-closed.md`](basic-vault-fail-closed.md) | `9c8299accd5a65cbfbc96c4cdc1849bb125523b8` | `0b13c91ef72cfc139de1d4c036e01e3d371349ba549b144d1aa0ff47cc855044` | 5,597 | Shared nominal-vault fail-closed backing and exact delivery |
| `contracts/core/AuctionHouse.vy` | [`auction-house.md`](auction-house.md) | `ffd98c032171dfd8b4ef357aab57bae82fce5ca7` | `2f6d9cfe42ef61be8d8448222ef5cf835ae8933bc580081cfc8368cd7e8ecd3c` | 53,377 | Skips deficient collateral at liquidation, auction, purchase, and deleverage boundaries |
| `contracts/core/CreditRedeem.vy` | [`basic-vault-fail-closed.md`](basic-vault-fail-closed.md) | `447a945b7bb052837412fb15a7f22875f44b9ee9` | `62f6aa664becc2df31702dcb88c28f2a1bbf749a5f9d665a3ea3d7bf69283bdd` | 14,166 | Soft-skips deficient redemption entries so healthy batch entries can continue |
| `contracts/core/CreditEngine.vy` | [`credit-engine.md`](credit-engine.md) | `a98d2522a16708e887a5a8aad78171843d413baf` | `7de649cece6e076b75775bb4ff5f397bf5ffa0a50ccdc462a061ca047b888e3d` | 46,812 | Retains terms for nonempty zero-backed positions without pricing zero |
| `contracts/data/Ledger.vy` | [`ledger.md`](ledger.md) | `590341e3f9091105036c1cc497bd862ea3769248` | `6bd731a6ce9084de213494ebad09f8e52c782153842708b78f90fa178c06e9e3` | 26,492 | Immutable native/ArbSys action-block selection |
| `contracts/core/Lootbox.vy` | [`lootbox.md`](lootbox.md) | `12d7b6afcc660bc502ad749b7d624fe8f38ab0cb` | `669c2857e2402ef0e8f9a508dd6f342426ffbd1affce11dd429e5b5b0129ae65` | 47,731 | Per-deployment immutable Underscore interval floor |
| `contracts/priceSources/BlueChipYieldPrices.vy` | [`blue-chip-yield-prices.md`](blue-chip-yield-prices.md) | `cafd177ef601186b0a6a30863ba5b8973d8dd92e` | `abe188bf7edd973f6d68e58e39767e948471542030f6c2447ab98616c303e8be` | 38,730 | Adds fail-closed Morpho V2 support while preserving existing yield protocols |
| `contracts/tokens/modules/Erc20Token.vy` | [`erc20-token.md`](erc20-token.md) | `f00e5655567612e3f8c95182de75701424eeea2b` | `54ffb5d2dcdf5dd2c5990e0bcd3a67b0ebcbae32b8dc3ef6c00d2e84ea447af7` | 17,435 | Adds governance-backed `getCCIPAdmin()` discovery to GREEN, RIPE, and sGREEN compiler outputs; owner authorization is unresolved, committed ABIs are stale, direct tests are missing, and the final LF was removed |

These are integrated source facts. None proves that the corresponding contract
has been deployed, registered, configured, or activated on Robinhood.

## Configuration contract

[`contracts/config/DefaultsRobinhood.vy`](../../../../contracts/config/DefaultsRobinhood.vy) is
a production-intended configuration contract, but its values and mere presence
in source are not deployment or onchain configuration:

| Rationale | Git blob | SHA-256 | Source bytes | Current disposition |
| --- | --- | --- | ---: | --- |
| [`defaults-robinhood.md`](defaults-robinhood.md) | `c63009f9e03044616da2562767f129d91e0843aa` | `4f89a970c19a7fc5a3d6f05035cd252d660ac6c1696ccddb4bd76c6751f356f8` | 13,617 | Integrated source; repository configuration consistent; deployment readiness fail-closed with unresolved inputs |

`DefaultsRobinhood.vy` and [`config/BluePrint.py`](../../../../config/BluePrint.py)
are the two human-edited value authorities. The
[`robinhood-parameters.json`](../../../../config/robinhood-parameters.json)
ledger is derived evidence, not a third value authority.

## Archival, non-admitted prototype

[`contracts/priceSources/RobinhoodUniswapV2RipePrices.vy`](../../../../contracts/priceSources/RobinhoodUniswapV2RipePrices.vy)
is present in `master..rh`, but it is not an admitted production price source:

| Rationale | Git blob | SHA-256 | Source bytes | Current disposition |
| --- | --- | --- | ---: | --- |
| [`robinhood-uniswap-v2-ripe-prices.md`](robinhood-uniswap-v2-ripe-prices.md) | `11fb790f04f782d7c3e7abcc66f78077c13434d9` | `56a6685442d8730922205f8fcd2893b542e12b7d5d0e1384bcc2f065b945b485` | 42,036 | Archival monitoring prototype; PriceDesk-inert, unregistered, unconfigured, non-admitted, without a repository deployment record, and unavailable for protocol accounting |

No launch Uniswap oracle authority was approved. Its direct monitoring and
update surfaces do not change its PriceDesk-facing zero/no-feed behavior.

## Historical/shared-source rationale inventory

The corrected Deleverage changes entered `rh` through `ad831669…`. Current
`master` and current `rh` contain identical production blobs for the two
unchanged sources below, so they remain historical/shared-source rationales:

| Contract | Rationale | Shared Git blob | Current SHA-256 | Source bytes |
| --- | --- | --- | --- | ---: |
| `Deleverage.vy` | [`deleverage.md`](deleverage.md) | `b43d373039b352d6eab240be714134764901b947` | `d64a08573d1af100a8d6ca9d72811a87414654107fd09fe105322dde53a9c138` | 56,068 |
| `SwitchboardDelta.vy` | [`switchboard-delta.md`](switchboard-delta.md) | `4e234df7626eb332836aceb5cbca2daaef2a0390` | `12604c00353b2b4e7519ffd316883e1e64394af53dd79f2c9866765d7385eb79` | 53,713 |

Their integration history and current shared bytes are established. Robinhood
deployment, parameter selection, timelock action, configuration, activation,
and release remain separate.

## Relevant current artifact identities

The central nine-contract artifact checker was rerun against the current bytes.
BlueChip, the archival Uniswap prototype, the changed token module, and its
three transitive token consumers were also freshly compiled with Vyper
`0.4.3+commit.bff19ea2` and their outputs hashed.

| Contract | Runtime-template bytes | EIP-170 headroom | Runtime SHA-256 | Canonical ABI SHA-256 |
| --- | ---: | ---: | --- | --- |
| AuctionHouse | 24,432 | 144 | `687bb68c747d5ec802db1333a8cbb8f842b4423e90dbdc01277699aaf1e4dfc8` | `4f855ff6ea205cab84e204f4fa09964bcac958c632112c021b2c996e1f40b387` |
| CreditEngine | 24,132 | 444 | `764512326594fe5b0dc49fa3afc8528b02fa717f685beea4249629d22e0fc1de` | `1b5616ca9b7df4dc88f013be7b0c69ec54006cf856e2e768a852d47b6d960e24` |
| Deleverage | 24,473 | 103 | `baa883c99f91d41f7b3091090b246b415c77f5d7ffffebfd5e3366ab15366d57` | `61fefe1ba573787eb65ab293da64922278e09b01619b4fa244ba36e961b73752` |
| DefaultsRobinhood | 2,687 | 21,889 | `aede1fc73290eeb071e1b67a7c7b367dbec0536e406391a03f12275663370d99` | `a2b3232606060b9b296666a2cfbc6a328c2b92897ac6e1dcf9f82920a449bddb` |
| SimpleErc20 | 9,390 | 15,186 | `3e21a9c930c878bb84883f66fab1f3cff0a9abf173034d927d3d660b020f0da1` | `cf0daef1095087a92ec3d0c327009d8a1d7ec6c3dc04b430debfd4bc25c88b57` |
| Ledger | 13,125 | 11,451 | `8fbc85b5bac4586fdb4fc432284f9c38d12ed3966b2de5630f9d4c80973dcce7` | `69f5e1c1cccf0f8bfbfa0cae30879635bca241d40af1e95615026b264658fb32` |
| Lootbox | 21,569 | 3,007 | `db9c2b91497a6e11191a181c9cbe1776e96532e50ff3e60e17f0bd447354e097` | `e752a206ba5c78cb573c734c7bfd1c407f1cb98898d3d8e9d3513836c56f5fb2` |
| SwitchboardDelta | 23,102 | 1,474 | `77553ded4c1e8de0754b25e0dbb0fa18be25657b3134c90bc071a99306bfca61` | `6d2bb3cfa9244b49bc180351316dc5d9ca0265bebcba90a2c84fbf8e3ea7909f` |
| Teller | 24,152 | 424 | `39ffa8d3274b74c91896a36c4d2ce9d6df5c197758a89fbfd1589b394dad5b81` | `319169528ec22722c7f912a0f93d3a0560feb17c2d6349770c17a643e1f00e20` |
| BlueChipYieldPrices | 22,054 | 2,522 | `84e004bf72ed7a699c7b7c52d849674517f82581cd4f49b73a06f1721e6cf578` | `d1a7f8491d5b1ba59da03ef3e0920a6bbf7682dfc2f0b471d4a5a8a1cb8f5c73` |
| RobinhoodUniswapV2RipePrices | 20,556 | 4,020 | `d36fe90fb011e2fbed546c5a0c576c7e5346e90ec34947c7be079884b2ca9c58` | `3dc0dcfe1a130a5911f2b97f106c963ebe9dca17efdad943a0a9c9609bcc837e` |
| Erc20Token module | 6,767 | 17,809 | `d13a59c2961a981a444ce6defd59a2d4c4d0a0b079f5cb322dc2c4fc2715c7fb` | `49c87121ab8eec9d6472e7e7401e54d78bf47022d54346ae1020dce01f546f39` |
| GreenToken | 7,085 | 17,491 | `74f3f1c818d951f6c5c2e755e0b1667f3f1b13f91cc483da7923809bb7038f16` | `5b399bea8005b337b822e7d7b00b165650d6b4e9af1d170b29878870d0a152e2` |
| RipeToken | 7,085 | 17,491 | `0338e28a3787286430139234127c9953945bca3fd7d4084cbd19fdfc62943962` | `5b399bea8005b337b822e7d7b00b165650d6b4e9af1d170b29878870d0a152e2` |
| SavingsGreen | 10,602 | 13,974 | `214218d00cc1cce8fa32160769e73c686c532bc13790f42ad4a4f83c14e6fc92` | `9234529ab0fc8a20a1b78ff1c1609a43629f5f6fd756debbe89b6606031f19cd` |

Runtime templates with constructor-bound immutables are compiler artifacts,
not final deployed-runtime identities.

The repository-wide deterministic ABI export check is not green: the committed
`Erc20Token.json`, `GreenToken.json`, `RipeToken.json`, and `SavingsGreen.json`
files omit `getCCIPAdmin()`. The source commit added no direct test for the new
selector. The green central artifact gate does not cover those token artifacts;
see [`erc20-token.md`](erc20-token.md) for exact expected and committed hashes.

## Supporting and test-only Vyper delta

Every remaining Vyper path in `master..rh` is explicitly classified below.
None is a production component, documentation example, or launch authority.

| Path | Classification | Git blob | SHA-256 | Source bytes |
| --- | --- | --- | --- | ---: |
| `contracts/mock/MockMorphoV2Factory.vy` | Morpho V2 factory test double | `725a6f623705e223b891953208be952b77ca5242` | `d4afb38408b542ef123ba5df453de8ed8a871116e85f916be983c934a0f4da60` | 902 |
| `contracts/mock/MockMorphoV2Vault.vy` | Morpho V2 vault/malformed-return test double | `3f41b99d9ec9ec98dc9484eecf7d0ae9095eb69d` | `d5c84d5c58f996b5cad7db1928de3fc8b144fd6322beccaad86396ab3cab5dac` | 2,735 |
| `contracts/mock/MockYieldRegistry.vy` | Existing yield-registry test double extended for Morpho V2 | `29c23b8042e2271539a87d191a3c561b6c101e42` | `b645e1bc1f9fdb036da47a508f54dac43e000b362463e095ddb434b358de7c5d` | 1,070 |
| `contracts/mock/MockUniswapV2Factory.vy` | Uniswap factory test double | `ea97d1930b72c41a99b909a2331a8fbd8d51c16e` | `ff4ba203e8e18d11a5738ef68a7f8fa9d677c2817e0f06a683c10c05e0ef83c5` | 828 |
| `contracts/mock/MockUniswapV2Pair.vy` | Uniswap pair/cumulative-price test double | `30a75af4cab8e62de5ecf2caa8a8bdecf1c1ffc2` | `7c6bc92970be39fa8118c4000379b722bcb87592779c6cb3b45df1f5cab76350` | 7,683 |
| `contracts/mock/MockUniswapV2Token.vy` | Uniswap token test double | `141137a97d6576d679314ff6366bd1a1659fb04d` | `0e109020f202db31e7a09c6e473b95aad39901f98acbf439fa11aeecacf0b588` | 604 |
| `contracts/mock/MockUniswapV2FlashBorrower.vy` | Flash-swap test borrower | `812ece36f706b7177a34e0561799dd001b2db54b` | `39b2e4b0e8eebe55175d71465ba33d8430528f0fa221c0b27c3b0f44012d6d84` | 973 |
| `contracts/mock/MockUniswapV2QuotePriceDesk.vy` | Quote-source/recursive-call test double | `978000acc79cfd1a7c12547896232602f35233f2` | `12d2046240189462486f7b2925228b31f369f83c7f4827faf4857b3de59a4d1f` | 1,540 |
| `contracts/mock/MockProbeErc20.vy` | Stock-token transferability probe double | `a367fbd89f3fc7d5dbafa3a5c118cabbc70e696b` | `7d84c3f995c7f06588cabda1c8a12d8376217c653a9c4371a69ac8e559bf6a48` | 3,069 |
| `contracts/mock/MockStockTokenControls.vy` | Stock-control adversarial double | `b9ed997df86bffe529b93bf9b6b00a5d0a9ca331` | `5d1527262aad66642a6e0f6dfdaad03458abdc4085a0445ebff0af8969614ef7` | 4,971 |
| `contracts/mock/MockRobinhoodCurveSystem.vy` | Test-only Curve address-provider, registry, factory, and pool double for launch-route assertions | `1420dbf2999405783726d64c64eb3c5007b95e37` | `6d180087f56b68ed7387cce91f391fddf6ae9845a1ab78fef095423d0f4279ea` | 2,666 |
| `contracts/testing/ActionBlockIdentityProbe.vy` | Test-only action-block probe | `82a56a6770d07b6330ca19d55df10f05bef5e105` | `95716e4e2b383f2a07826be94d9ee402d263eec522bb4f77efd72a5e5f6eafe5` | 1,203 |
| `contracts/testing/StockTokenTransferProbe.vy` | Test-only Stock transfer probe | `1460f97591ac2a98e244f37fd66ce540d3408391` | `dcf632f75def3d55203731856e5c2813237235bf72c6b8586400c9f858c3046a` | 4,602 |

The committed ABI files and Python tests are supporting artifacts rather than
additional Vyper production deltas. Their current paths are linked from the
individual rationale pages.

## Documentation-example contract delta

These two changed contract-language files are review references, not admitted
production components. The Solidity file contains the active thin-inheritance
reference; the Vyper file is its frozen superseded comparison.

| Path | Rationale | Language / disposition | Git blob | SHA-256 | Source bytes |
| --- | --- | --- | --- | --- | ---: |
| `docs/chains/rh/examples/RipeCcipBurnMintTokenPools.sol` | [`ccip-burn-mint-token-pools.md`](ccip-burn-mint-token-pools.md) | Solidity; exact-hash reviewed GREEN and RIPE reference subclasses, not production-ready or deployment-authorized | `9914be95aab65e48438b5be9e3e7defa221696b7` | `28fea3591caf8955a4c1f47d34f5abfe249564001578687525f94fddf5cfac77` | 1,784 |
| `docs/chains/rh/examples/ExampleGreenCcipBurnMintPool.vy` | [`ccip-burn-mint-token-pools.md`](ccip-burn-mint-token-pools.md) | Vyper; frozen superseded comparison, not the selected architecture | `742f8ce4c41ed18a7fabcd51fa42864433355880` | `7f3b46af23b9456869b0a72578d3ae295cbfb8ff112d0f7bddd1d66a4afb1e18` | 34,600 |

The 27 July Round-3 review reproduced the Solidity reference's pinned compiler,
dependency, runtime, layout, ABI-delta, and isolated integration evidence. That
environment is not a committed repository build package, so the results remain
dated exact-hash review evidence rather than a fresh current compilation.

## Automated enforcement boundary

The repository currently contains one GitHub Actions workflow:
[`rh-handoff-dashboard.yml`](../../../../.github/workflows/rh-handoff-dashboard.yml).
It builds, tests, and lints the Robinhood dashboard only. It does not run the
Python/Vyper contract suites, central artifact checker, block-clock inventory,
Defaults generator, deterministic ABI export check, or any Solidity build/test
package. The red four-file token ABI discrepancy and the Solidity reference
gaps therefore have no repository CI enforcement. Every validation result in
this directory is explicit audit evidence, not a continuously enforced gate.

## Complete rationale page inventory

- [`defaults-robinhood.md`](defaults-robinhood.md) — configuration values and
  the two-source authority model;
- [`teller.md`](teller.md) — exact deposit receipt, mutex, and return policy;
- [`basic-vault-fail-closed.md`](basic-vault-fail-closed.md) — shared nominal
  backing and exact-delivery containment;
- [`credit-engine.md`](credit-engine.md) — zero-backing debt-term containment;
- [`ledger.md`](ledger.md) — portable action-block identity;
- [`lootbox.md`](lootbox.md) — per-deployment reward interval floor;
- [`blue-chip-yield-prices.md`](blue-chip-yield-prices.md) — Morpho V2 yield
  pricing and compatibility;
- [`erc20-token.md`](erc20-token.md) — shared `getCCIPAdmin()` source change,
  transitive token artifacts, and current ABI/test discrepancy;
- [`ccip-burn-mint-token-pools.md`](ccip-burn-mint-token-pools.md) — changed
  GREEN/RIPE thin-Solidity reference subclasses and their production-package
  boundary;
- [`robinhood-uniswap-v2-ripe-prices.md`](robinhood-uniswap-v2-ripe-prices.md)
  — archival, PriceDesk-inert monitoring prototype;
- [`deleverage.md`](deleverage.md) — historical/shared full-payoff and dust
  rationale;
- [`auction-house.md`](auction-house.md) — historical/shared safe conversion,
  Stock delivery, and liquidation composition; and
- [`switchboard-delta.md`](switchboard-delta.md) — historical/shared bounded
  governance actions.

## Lifecycle boundary

The current repository state can be read in this order:

1. **Integrated source:** the bytes exist in current `rh`.
2. **Selected configuration:** readable repository authorities select some
   components and values while unresolved inputs remain fail-closed.
3. **Deployment:** creation bytecode is executed with exact approved inputs.
4. **Registration:** the deployed address is entered in the approved registry
   slot or topology.
5. **Activation:** governed feature/configuration switches make the component
   live for intended protocol paths.
6. **Release:** independent evidence and owner authority approve production use.

No later state follows automatically from an earlier one. In particular,
PriceDesk slot-3 selection for BlueChipYield is not deployment or registration,
and source-level Defaults values are not onchain configuration.

At this exact baseline, the AAPL launch-input authority, qualified non-admission
of launch LP tokens, owner-approved reward product packet, bounded Curve launch
topology, deterministic Robinhood migration sources, and transaction executor
are integrated repository facts. Their unresolved bindings keep the deployment
plan non-executable; there is no migration history, execution, deployment,
onchain configuration, registration, activation, or release.

The shared `Erc20Token.getCCIPAdmin()` hook is also integrated. It does not
establish CCIP registration, pools, remotes, rate limits, or mint/burn
capabilities. The recorded Track-1 precondition and owner decision remain
unresolved, its four transitive committed ABI files are stale, and direct tests
are missing. Nine CCIP planning documents outside this directory contain a mix
of still-current Base facts, governing conditions, neutral inventory, and
stale Robinhood source premises; [`erc20-token.md`](erc20-token.md) records the
complete disposition map. Ratification and reversion are both separately
controlled source decisions; this folder selects neither.

## Mechanical coverage rule

The repository's current contract-language inventory contains `.vy`, `.vyi`,
and `.sol` files. The discovery set checks all three extensions and is
reproducible with:

```text
git diff --name-status \
  91eda49ccd34a25090582aff0695075c4c806011..\
  0642f086d19e3cc62faaf67da096b6511e405320 -- \
  '*.vy' '*.vyi' '*.sol'
```

It yields 24 contract-language paths: 23 Vyper and one Solidity, with no changed
`.vyi` path. They classify as seven current production source paths, one
configuration contract, one archival prototype, thirteen supporting/test-only
Vyper paths, and two documentation examples. The three historical/shared
rationale sources have identical `master` and `rh` Git blobs and therefore do
not appear in that delta.

Future reviews must first re-enumerate the repository's contract-language
extensions and then update this command if a new language appears; extension-
specific discovery must not be assumed complete by convention.
