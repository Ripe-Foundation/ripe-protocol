# Robinhood smart-contract change rationale

This directory is the contract-centric explanation of every Vyper and Solidity
contract-language source change represented by the current Robinhood (`rh`)
branch. It separates current `master..rh` production deltas from configuration,
non-admitted candidates, supporting/test-only sources, documentation examples, and
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

## Current review-candidate authority and ancestry

This uncommitted review candidate is based on the following independently
verified repository identities. Its Teller source and artifact rows include
the direct typed-balance candidate and therefore are not claims about the
unchanged `rh` ref.

| Ref or role | Commit | Tree | Meaning |
| --- | --- | --- | --- |
| Candidate base `rh` | `1ac64deb5f65fc39f4362f02ed86a118d7554deb` | `40fc7d00222659285b60fbde96155f255246c734` | Exact base for this uncommitted review candidate |
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

## Complete review-candidate production-source delta

The following feature-candidate production source paths include the current
Robinhood delta plus the BasicVault fail-closed changes in this worktree. The
shared ERC-20 modules alter their transitive compiled artifacts:

| Contract | Rationale | Git blob | SHA-256 | Source bytes | Current source disposition |
| --- | --- | --- | --- | ---: | --- |
| `contracts/core/Teller.vy` | [`teller.md`](teller.md) | `dea818cde0901b02248e3824158e5c422ed02a80` | `f2e01e1cc9cf4cdfca380f329836732fd2d6d0201565828093257a0df8451b9a` | 40,786 | Exact call-local receipt and vault-return policy with typed balance observations |
| `contracts/vaults/modules/BasicVault.vy` | [`basic-vault-fail-closed.md`](basic-vault-fail-closed.md) | `a5a51ee20c598e9bf40908fc6c38f1c0634bf665` | `6a6abdde4887fb5339125c7268e0258175e3b66c9f060b6ab6e8262f58269ea8` | 5,552 | Shared nominal-vault fail-closed backing and exact delivery |
| `contracts/vaults/modules/StabVault.vy` | [`basic-vault-fail-closed.md`](basic-vault-fail-closed.md) | `e9c0bb1e67bdcfa0df4c9116d5a6298446b9df68` | `b6b80e171eaced650b9ccc0583543f2a20dec471f43ff3231c0619d6c637549e` | 39,669 | Truthful indexed Stability Pool positions for non-borrow consumers |
| `contracts/core/AuctionHouse.vy` | [`auction-house.md`](auction-house.md) | `d0a2d45cae0128cbb6ed5508238c817dfd963482` | `3fe2ae20b013ce3493daa272270ebf65324656561a807ea8df878e1bc87dfad3` | 53,566 | Skips deficient collateral, preserves eligible Stability Pool auctions, and keeps empty liquidations retryable |
| `contracts/core/CreditRedeem.vy` | [`basic-vault-fail-closed.md`](basic-vault-fail-closed.md) | `447a945b7bb052837412fb15a7f22875f44b9ee9` | `62f6aa664becc2df31702dcb88c28f2a1bbf749a5f9d665a3ea3d7bf69283bdd` | 14,166 | Soft-skips deficient redemption entries so healthy batch entries can continue |
| `contracts/core/CreditEngine.vy` | [`credit-engine.md`](credit-engine.md) | `ef7724393d3b9f30f6e4281a1a465c5d2cc49895` | `05bb1157c6885fc734cc4831efa2fe6aa4c189d14a1bc22bb80472103de105bb` | 46,886 | Retains terms for zero amounts and explicitly excludes Stability Pool collateral |
| `contracts/data/Ledger.vy` | [`ledger.md`](ledger.md) | `590341e3f9091105036c1cc497bd862ea3769248` | `6bd731a6ce9084de213494ebad09f8e52c782153842708b78f90fa178c06e9e3` | 26,492 | Immutable native/ArbSys action-block selection |
| `contracts/core/Lootbox.vy` | [`lootbox.md`](lootbox.md) | `12d7b6afcc660bc502ad749b7d624fe8f38ab0cb` | `669c2857e2402ef0e8f9a508dd6f342426ffbd1affce11dd429e5b5b0129ae65` | 47,731 | Per-deployment immutable Underscore interval floor |
| `contracts/priceSources/BlueChipYieldPrices.vy` | [`blue-chip-yield-prices.md`](blue-chip-yield-prices.md) | `cafd177ef601186b0a6a30863ba5b8973d8dd92e` | `abe188bf7edd973f6d68e58e39767e948471542030f6c2447ab98616c303e8be` | 38,730 | Adds fail-closed Morpho V2 support while preserving existing yield protocols |
| `contracts/tokens/modules/Erc20Token.vy` | [`erc20-token.md`](erc20-token.md) | `e9ec81672ed5ea973487d3ae44a633c13b06b572` | `6593a28f791f9e6b3fdaf0ff14abd7379894833d62026a9092237de7033398c1` | 17,668 | Adds governance-backed `getCCIPAdmin()` discovery to GREEN, RIPE, and sGREEN compiler outputs; deterministic ABIs and direct behavior tests are current, while owner authorization, Base live-version policy, and the missing final LF remain unresolved |

All rows other than Teller record integrated source facts. The Teller row is
the uncommitted review candidate described above. No row proves that the
corresponding contract has been deployed, registered, configured, or activated
on Robinhood.

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

## Monitoring-only Uniswap V2 component

[`contracts/priceSources/UniswapV2Prices.vy`](../../../../contracts/priceSources/UniswapV2Prices.vy)
replaces the deleted cumulative-price research prototype. The owner approved
deployment for direct monitoring, not oracle admission. The replacement has
no local governance, timelock, configuration, or snapshot state.

The standard PriceSource entrypoints remain callable but are permanently
inert. They return no price or feed, even if the component is accidentally
registered. Only explicitly named RIPE/WETH monitoring views expose the
accepted spot-reserve manipulation and liquidity limitations documented in
[`uniswap-v2-prices.md`](uniswap-v2-prices.md). Deployment does not authorize
PriceDesk registration, collateral valuation, LP admission, or any other
value-bearing consumer. Exact source and artifact identities are generated
from the final integrated bytes, not copied from the superseded candidate row.

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

The repository-health remediation reran the complete central artifact checker.
These are the authoritative values in
[`contract-artifact-expectations.json`](../../../../config/contract-artifact-expectations.json):

| Contract | Template bytes | Template headroom | Deployed bytes | Deployed headroom | Runtime-template SHA-256 | Canonical ABI SHA-256 |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| AuctionHouse | 23,767 | 809 | 23,863 | 713 | `6cb605c161504d656256f6498f49167b82fec7ee1c3539903e965c7c6c35a1fa` | `4f855ff6ea205cab84e204f4fa09964bcac958c632112c021b2c996e1f40b387` |
| CreditEngine | 24,271 | 305 | 24,367 | 209 | `ad40bde63aee7e41933c2cbe6012de9940791a4f28a85328b8accdf3dabf635e` | `1b5616ca9b7df4dc88f013be7b0c69ec54006cf856e2e768a852d47b6d960e24` |
| DefaultsRobinhood | 2,474 | 22,102 | 2,698 | 21,878 | `b424af2dc57a90b7332aab302df9acfbb716f91e6a11f31446ea109f3ac075c9` | `6878e6b5bd5b34906a96ac60e03df7db322dc01d546de6385ec6a70fc9fae1a2` |
| Deleverage | 24,473 | 103 | 24,569 | 7 | `baa883c99f91d41f7b3091090b246b415c77f5d7ffffebfd5e3366ab15366d57` | `61fefe1ba573787eb65ab293da64922278e09b01619b4fa244ba36e961b73752` |
| Ledger | 13,264 | 11,312 | 13,392 | 11,184 | `fe65aaa826003b14518824bf6219b33cde311db63687a9b9c23baf7fb4708380` | `0a10ba343608af86094ef62417285e32e3abe6a976bdf63590706310e9771f34` |
| Lootbox | 21,995 | 2,581 | 22,123 | 2,453 | `1b1a969fedeaa4d430d4fa81bd6cde2bfb937239dde48ce39e7e24052d8884f4` | `e752a206ba5c78cb573c734c7bfd1c407f1cb98898d3d8e9d3513836c56f5fb2` |
| MissionControl | 15,902 | 8,674 | 15,998 | 8,578 | `d1fe5a9af241b8cfc601d5af8589c056d339283598005c92889954f0756897fb` | `fb07a0bb2b5fdcfdd5fcca7980f13d67ce7d37b26ecdffcd206c88ef12f4e9c3` |
| RipeGov | 24,480 | 96 | 24,512 | 64 | `8ab834360cec9d4d8e7d939fd624829eae83b8e1ee3dbfb99227d21f259b2f3e` | `9c54e3cec9e471e776e16f1f6454ec27c23d8b319281d8ee0b792931c4e22137` |
| SimpleErc20 | 9,368 | 15,208 | 9,400 | 15,176 | `750c6a05e9a400a54e25d5f1020d99a3d7ad1ef8372ee86583f79024e60674b6` | `cf0daef1095087a92ec3d0c327009d8a1d7ec6c3dc04b430debfd4bc25c88b57` |
| StabilityPool | 24,275 | 301 | 24,371 | 205 | `d47f9d2c92cbac07fb7ed6e86b4c55cfab09bc19d3de8bc717e5b99d58955361` | `8086009513c4557dc8a12fec7829c0f3782693001ebc7d21dddab2944084812a` |
| SwitchboardBravo | 22,922 | 1,654 | 23,082 | 1,494 | `d7af2f3f3adf8ddc1088f19bc7295e07b058eee18420eb6f227ce4912c1da65f` | `8a30c7b4483192513051c1162f235d02549e708aab4173d79597609ffab39202` |
| SwitchboardDelta | 23,102 | 1,474 | 23,262 | 1,314 | `77553ded4c1e8de0754b25e0dbb0fa18be25657b3134c90bc071a99306bfca61` | `6d2bb3cfa9244b49bc180351316dc5d9ca0265bebcba90a2c84fbf8e3ea7909f` |
| Teller | 24,151 | 425 | 24,247 | 329 | `21d15c2b77d9f513cb8a0957daa42910150ba5661883913ea8bbf4a9ec6343d1` | `9cca03351cd8ead87160401be263732376fb4ab7d4913b0d59ce6ad271e4dabb` |
| UniswapV2Prices | 3,621 | 20,955 | 3,781 | 20,795 | `88cbf9a963bf38bfcf83ea95317356bf44e50052973748968e1f8bf34574910f` | `787994c73fa92e072833734f3c079215eace4bc7159305bcd059989b62deef6f` |

Runtime templates with constructor-bound immutables are compiler artifacts,
not final deployed-runtime identities.

The tightest EIP-170 margins are therefore the constructor-bound deployed
values: Deleverage has 7 bytes, AuctionHouse 20, RipeGov 64, and CreditEngine
184 under its exact owner-granted waiver. The corresponding 103-, 116-, 96-,
and 280-byte values are runtime-template margins and must not be described as
the final deployed headroom.

The health remediation also regenerated all 53 committed ABI outputs. The
repository-wide deterministic ABI export check now covers the token artifacts,
including `getCCIPAdmin()`.

## Supporting and test-only Vyper delta

Every remaining Vyper path in `master..rh` is explicitly classified below.
None is a production component, documentation example, or launch authority.

| Path | Classification | Git blob | SHA-256 | Source bytes |
| --- | --- | --- | --- | ---: |
| `contracts/mock/MockMorphoV2Factory.vy` | Morpho V2 factory test double | `725a6f623705e223b891953208be952b77ca5242` | `d4afb38408b542ef123ba5df453de8ed8a871116e85f916be983c934a0f4da60` | 902 |
| `contracts/mock/MockMorphoV2Vault.vy` | Morpho V2 vault/malformed-return test double | `3f41b99d9ec9ec98dc9484eecf7d0ae9095eb69d` | `d5c84d5c58f996b5cad7db1928de3fc8b144fd6322beccaad86396ab3cab5dac` | 2,735 |
| `contracts/mock/MockYieldRegistry.vy` | Existing yield-registry test double extended for Morpho V2 | `29c23b8042e2271539a87d191a3c561b6c101e42` | `b645e1bc1f9fdb036da47a508f54dac43e000b362463e095ddb434b358de7c5d` | 1,070 |
| `contracts/mock/MockUniswapV2Pair.vy` | Uniswap pair/cumulative-price test double | `30a75af4cab8e62de5ecf2caa8a8bdecf1c1ffc2` | `7c6bc92970be39fa8118c4000379b722bcb87592779c6cb3b45df1f5cab76350` | 7,683 |
| `contracts/mock/MockUniswapV2Token.vy` | Uniswap token test double | `141137a97d6576d679314ff6366bd1a1659fb04d` | `0e109020f202db31e7a09c6e473b95aad39901f98acbf439fa11aeecacf0b588` | 604 |
| `contracts/mock/MockUniswapV2QuotePriceDesk.vy` | Quote-source/recursive-call test double | `7ec9e348d2b01d86e715549a90c7d48c08cb734b` | `7b84dfaafb51e51b07dc725b739e422421bc419c56b51804164aeab231c6fdf5` | 1,634 |
| `contracts/mock/MockUniswapV2RipeHq.vy` | Minimal RipeHq/governance test double | `003f80140e6f5cb1ee43bf4ef731d7af96fe3e07` | `4a696548ef6f130d227133d70b3b6ee93558d78a18cf253e4364a9c63af85d4d` | 1,162 |
| `contracts/mock/MockProbeErc20.vy` | Stock-token transferability probe double | `a367fbd89f3fc7d5dbafa3a5c118cabbc70e696b` | `7d84c3f995c7f06588cabda1c8a12d8376217c653a9c4371a69ac8e559bf6a48` | 3,069 |
| `contracts/mock/MockStockTokenControls.vy` | Stock-control adversarial double | `b9ed997df86bffe529b93bf9b6b00a5d0a9ca331` | `5d1527262aad66642a6e0f6dfdaad03458abdc4085a0445ebff0af8969614ef7` | 4,971 |
| `contracts/mock/MockRobinhoodCurveSystem.vy` | Test-only Curve address-provider, registry, factory, and pool double for launch-route assertions | `1420dbf2999405783726d64c64eb3c5007b95e37` | `6d180087f56b68ed7387cce91f391fddf6ae9845a1ab78fef095423d0f4279ea` | 2,666 |
| ~~`contracts/testing/ActionBlockIdentityProbe.vy`~~ **(removed)** | Test-only action-block probe | `82a56a6770d07b6330ca19d55df10f05bef5e105` | `95716e4e2b383f2a07826be94d9ee402d263eec522bb4f77efd72a5e5f6eafe5` | 1,203 |
| ~~`contracts/testing/StockTokenTransferProbe.vy`~~ **(removed)** | Test-only Stock transfer probe | `1460f97591ac2a98e244f37fd66ce540d3408391` | `dcf632f75def3d55203731856e5c2813237235bf72c6b8586400c9f858c3046a` | 4,602 |

Both `contracts/testing/` probes were removed along with `tests/probes/` and the
block-clock inventory that pinned their paths. Neither was ever deployed —
neither appears in any manifest under `migration_history/` — and no migration,
script, or config referenced them. Their rows are struck through rather than
deleted so the recorded hashes stay auditable; the sources remain in git history.

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
[`python-tests.yml`](../../../../.github/workflows/python-tests.yml). Pull
requests, plus pushes to `master` or `rh`, run both lean and comprehensive
pytest lanes on exact Python 3.12.0; manual dispatch can select either lane.
Checkout is full-history because release, M4, and manifest gates bind historical
commits. Superseded runs are cancelled by pull-request number or branch ref,
while manual lane selections remain separate. Jobs use task-private
pytest/cache roots, verify the resolved environment with `pip check`, and
preserve deterministic hashing. The comprehensive lane has a 180-minute limit
and collects the repository's artifact, release, fuzz, gas, and offline fork
gates in addition to the default suite.

The Ubuntu comprehensive job intentionally skips the macOS/APFS-only H-06
publication tests. A separate `manifest-promotion-macos` job runs
`tests/deployment/test_current_manifest_promotion.py` on `macos-latest`,
including both multiprocessing cleanup regressions. Local macOS comprehensive
totals and Ubuntu CI totals are therefore platform-specific and must not be
presented as identical expected counts.

This makes repository CI execution automatic, but GitHub branch-protection and
required-check policy remain external controls and must be configured on the
repository. No workflow run proves a deployment, live-chain binding, Solidity
production package, or owner release decision.

The former `rh-handoff-dashboard.yml` workflow and the dashboard application it
built were extracted from the active tree; both remain recoverable from
`610b43f4508e85628a1362532a79d68d71ea902c` (see
[`extracted-files.tsv`](../../../simplification/extracted-files.tsv)).

## Complete rationale page inventory

- [`defaults-robinhood.md`](defaults-robinhood.md) — configuration values and
  the two-source authority model;
- [`teller.md`](teller.md) — exact deposit receipt, mutex, and return policy;
- [`basic-vault-fail-closed.md`](basic-vault-fail-closed.md) — shared nominal
  backing and exact-delivery containment;
- [`credit-engine.md`](credit-engine.md) — zero-backing debt-term containment;
- [`ledger.md`](ledger.md) — portable action-block identity;
- [`lootbox.md`](lootbox.md) — per-deployment reward interval floor;
- [`ripe-gov.md`](ripe-gov.md) — SC-12 early-release accounting,
  governance-point lifecycle, address-level redistribution limitation, and
  cross-lane rollout consequences;
- [`blue-chip-yield-prices.md`](blue-chip-yield-prices.md) — Morpho V2 yield
  pricing and compatibility;
- [`erc20-token.md`](erc20-token.md) — shared `getCCIPAdmin()` source change,
  transitive token artifacts, and current ABI/test discrepancy;
- [`ccip-burn-mint-token-pools.md`](ccip-burn-mint-token-pools.md) — changed
  GREEN/RIPE thin-Solidity reference subclasses and their production-package
  boundary;
- [`uniswap-v2-prices.md`](uniswap-v2-prices.md) — RIPE/WETH-only stateless
  monitoring component and its prohibited value-bearing
  admission boundary;
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
are integrated repository facts. Those facts alone do not prove any later
lifecycle state, and unresolved bindings keep the remaining deployment plan
non-executable. The separately owner-confirmed Uniswap monitoring deployment
is an explicit exception; it does not establish PriceDesk registration,
value-bearing activation, or release.

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

That frozen historical range yields 24 contract-language paths: 23 Vyper and
one Solidity, with no changed `.vyi` path. The current candidate branch deletes
the range's archival Uniswap prototype and two old-only mocks, and adds the
smaller `UniswapV2Prices` candidate plus one replacement test mock. The three
historical/shared rationale sources have identical `master` and `rh` Git blobs
and therefore do not appear in that frozen delta.

Future reviews must first re-enumerate the repository's contract-language
extensions and then update this command if a new language appears; extension-
specific discovery must not be assumed complete by convention.
