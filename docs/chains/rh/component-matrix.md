# Robinhood Phase-0 component matrix

**Status:** Complete analysis; recommendations and owner decisions remain unapproved

**Track branch:** `rh-track-3-phase-0-inventory`

**Pinned starting commit:** `51a7a3996f5fec40efd554d1b025aaa9c2ed4ea2` (`3 tracks`)

**Planning baseline:** `1bb8bd5b8837a06c818c3fb9e7b599b5dd29f2b1`

**Audit timestamp:** `2026-07-23T19:59:58Z`

**Revision history:** 2026-07-23 — initial authoring and reviewer follow-ups are
consolidated in this track commit. Corrections include the BN-012 trace, CAD-001,
setter/status/decision provenance, dependency, and parameter-reporting polish.

**Controlling architecture:** `/Users/wigglez/dev/hightop-notes/random/hood/hood-chain-executive-summary.md`

This matrix specifies the clean Robinhood deployment surface. It does not approve
owner decisions, prove current external addresses, or authorize deployment.

## Method and status rules

The matrix was derived from the pinned contracts, `config/BluePrint.py`,
`contracts/config/DefaultsBase.vy`, Base migration history, the 48-entry
`migration_history/base-mainnet/v1/current-manifest.json`, ABI/export and deployment
scripts, tests, [`block-number-inventory.md`](block-number-inventory.md), and the
controlling Hightop Notes executive summary.

The generated Base parameter snapshots used for configuration context are dated
**2025-12-02** at blocks `38,930,921..38,931,053`. They are nearly eight months
old at this audit and are not evidence of current live configuration or bytecode.
The general snapshot's `increasePerDangerBlock | 0.10%` display is also a
reporting defect: its generic formatter uses a `100_00` denominator, while the
runtime field uses `100_0000`; see CAD-001 in the inventory.

The repository diff from the planning baseline contains only the three Robinhood
track briefs; there is no production-code delta to reconcile.

The required statuses mean:

- **reused unchanged:** same canonical production source; parameters, addresses,
  permissions, or asset configuration may differ by chain;
- **modified:** the canonical shared source needs a chain-portable code change;
- **replaced:** Robinhood uses a different component for the same role;
- **disabled:** the source may remain canonical/Base-live, but Robinhood does not
  deploy or register the integration;
- **deferred:** architecture or owner/cross-track evidence is still required.

The taxonomy has no `new` status. A net-new component remains **deferred** while
its controlling cross-track facts, specification, and source are unfrozen. Once
frozen, its source/deployment status must be reclassified explicitly; adding a new
shared component does not by itself label existing core contracts `modified`.

A different address or parameter is not a contract fork. `DefaultsRobinhood` is
chain-specific configuration data and must not contain divergent protocol logic.
All external addresses in the existing manifest are point-in-time repository
evidence only; every launch address must be reverified from a dated primary source.

## Component and source matrix

| ID | Component / deployable | Source | Base role | Intended Robinhood role | Status | Same shared source? | Reason for non-unchanged status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CM-001 | `GreenToken` | `contracts/tokens/GreenToken.vy` | Canonical GREEN token | Local GREEN, minted/burned by Ripe and CCIP capability paths | reused unchanged | Yes | —; changes only if Track 1 proves in-token `getCCIPAdmin()` is required |
| CM-002 | `RipeToken` | `contracts/tokens/RipeToken.vy` | RIPE token | Local RIPE plus CCIP burn/mint | reused unchanged | Yes | —; same Track 1 contingency as CM-001 |
| CM-003 | `SavingsGreen` | `contracts/tokens/SavingsGreen.vy` | sGREEN wrapper and protocol destination | Optional local sGREEN | deferred | Yes if included | Owner has not approved inclusion/omission; existing protocol paths assume an sGREEN address |
| CM-004 | `RipeHq` | `contracts/registries/RipeHq.vy` | Capability and Department registry | Local authority root, including `canMintGreen` for CCIP pool | reused unchanged | Yes | — |
| CM-005 | `Contributor` | `contracts/modules/Contributor.vy` | Contributor vesting/authority module | Local contributor module if HR enabled | reused unchanged | Yes | — |
| CM-006 | `TrainingWheels` | `contracts/config/TrainingWheels.vy` | Restricted launch safety controls | Same launch safety role | reused unchanged | Yes | — |
| CM-007 | `DefaultsBase` | `contracts/config/DefaultsBase.vy` | Base parameter source | Not deployed as RH defaults | replaced | Chain-specific data source | Replaced on RH by CM-049; no runtime logic fork |
| CM-008 | `Ledger` | `contracts/data/Ledger.vy` | Shared accounting and same-number action guard | Local accounting with RH-compatible guard policy | modified | Yes | BN-002 same-number guard can throttle many RH L2 transactions |
| CM-009 | `MissionControl` | `contracts/data/MissionControl.vy` | Governed protocol/asset parameters | Same local data contract with RH values | reused unchanged | Yes | — |
| CM-010 | `Switchboard` | `contracts/registries/Switchboard.vy` | Registry of configuration Departments | Same local registry | reused unchanged | Yes | — |
| CM-011 | `SwitchboardAlpha` | `contracts/config/SwitchboardAlpha.vy` | General debt, vault and price parameters | Same setters/validators with RH values | reused unchanged | Yes | — |
| CM-012 | `SwitchboardBravo` | `contracts/config/SwitchboardBravo.vy` | Auction parameters | Same with RH auction durations | reused unchanged | Yes | — |
| CM-013 | `SwitchboardCharlie` | `contracts/config/SwitchboardCharlie.vy` | Rewards/Lootbox parameters | Same with RH emission rate/interval values | reused unchanged | Yes | — |
| CM-014 | `SwitchboardDelta` | `contracts/config/SwitchboardDelta.vy` | Deleverage, bond and operational configuration | Same role with chain-portable cooldown validation | modified | Yes | Duplicates ambiguous `MAX_COOLDOWN_BLOCKS=7_200` with Deleverage; HR seconds bounds also fail to round-trip current defaults |
| CM-015 | `PriceDesk` | `contracts/registries/PriceDesk.vy` | Price-source routing | Local routing, initially Chainlink-focused | reused unchanged | Yes | — |
| CM-016 | `ChainlinkPrices` | `contracts/priceSources/ChainlinkPrices.vy` | Chainlink feed adapter | Official Stock Token feeds and any approved USDG feed | reused unchanged | Yes | — |
| CM-017 | `CurvePrices` | `contracts/priceSources/CurvePrices.vy` | Curve/Green reference pricing | No initial RH registration/deployment | disabled | Yes for Base | Curve is Base-only; block snapshot semantics are not suitable to enable accidentally |
| CM-018 | `BlueChipYieldPrices` | `contracts/priceSources/BlueChipYieldPrices.vy` | Yield-token price adapter | Omitted initially | disabled | Yes for Base | No approved RH yield integrations |
| CM-019 | `PythPrices` | `contracts/priceSources/PythPrices.vy` | Optional oracle adapter | Omitted initially | disabled | Yes for Base | Selected architecture uses official Chainlink Stock feeds |
| CM-020 | `StorkPrices` | `contracts/priceSources/StorkPrices.vy` | Optional oracle adapter | Omitted initially | disabled | Yes for Base | No approved RH use |
| CM-021 | `VaultBook` | `contracts/registries/VaultBook.vy` | Vault implementation registry | Local registry for approved vault implementation | reused unchanged | Yes | — |
| CM-022 | `StabilityPool` | `contracts/vaults/StabilityPool.vy` | GREEN stability/liquidation vault | Local insurance/liquidation component | reused unchanged | Yes | — |
| CM-023 | `RipeGov` | `contracts/vaults/RipeGov.vy` | RIPE governance/reward vault | Local governance/reward vault | reused unchanged | Yes | — |
| CM-024 | `SimpleErc20` | `contracts/vaults/SimpleErc20.vy` | ERC-20 collateral accounting option | Recommended provisional Stock Token vault only if owner accepts transfer/rebase failure behavior | deferred | Yes | Owner vault choice and Track 2 transferability evidence remain open |
| CM-025 | `RebaseErc20` / inherited `SharesVault` | `contracts/vaults/RebaseErc20.vy`, `contracts/vaults/modules/SharesVault.vy` | Share-accounted collateral option | Alternative Stock Token vault | deferred | Yes | Requires explicit behavior spec/tests; owner has not chosen it |
| CM-026 | `AuctionHouse` | `contracts/core/AuctionHouse.vy` | Liquidation auctions | Local liquidation auctions | reused unchanged | Yes | — |
| CM-027 | `AuctionHouseNFT` | `contracts/core/AuctionHouseNFT.vy` | NFT auction claims/receipts | Same if liquidation flow requires it | reused unchanged | Yes | — |
| CM-028 | `Boardroom` | `contracts/core/Boardroom.vy` | RIPE reward/boardroom accounting | Local rewards component | reused unchanged | Yes | — |
| CM-029 | `BondRoom` | `contracts/core/BondRoom.vy` | RIPE bond epochs | Local bond/rewards component with RH durations | reused unchanged | Yes | — |
| CM-030 | `CreditEngine` | `contracts/core/CreditEngine.vy` | Borrowing, debt and interest | Local GREEN credit engine | reused unchanged | Yes | — |
| CM-031 | `Endaoment` | `contracts/core/Endaoment.vy` | Protocol treasury/stabilizer actions | Local reserve coordinator with unsupported Base actions unconfigured | reused unchanged | Yes | — |
| CM-032 | `HumanResources` | `contracts/core/HumanResources.vy` | Contributor administration | Optional local HR administration | reused unchanged | Yes | — |
| CM-033 | `Lootbox` | `contracts/core/Lootbox.vy` | Points, RIPE rewards, Underscore distribution | Local points/rewards; Underscore path disabled | modified | Yes | `ONE_DAY=43_200 # on Base` is enforced in shared source |
| CM-034 | `Teller` | `contracts/core/Teller.vy` | User entry point/orchestrator | Same local entry point | reused unchanged | Yes | —; Ledger policy changes should preserve its interface if possible |
| CM-035 | `GreenPool` | `migrations/base-mainnet/2001_CurvePools.py`, current manifest | Base GREEN liquidity/reference pool | Omitted | disabled | N/A external | Base-only Curve liquidity |
| CM-036 | `RipePoolCurve` | `migrations/base-mainnet/2001_CurvePools.py`, current manifest | Base Curve RIPE liquidity | Omitted | disabled | N/A external | Unsupported Curve path |
| CM-037 | `RipePoolAero` | `migrations/base-mainnet/2025082000_AeroPrices.py`, current manifest | Base Aerodrome RIPE liquidity | Omitted | disabled | N/A external | Unsupported Aerodrome path |
| CM-038 | `BondBooster` | `contracts/config/BondBooster.vy` | Time-limited bond boost config | Same if bond program enabled | reused unchanged | Yes | — |
| CM-039 | `wsuperOETHbPrices` | `contracts/priceSources/wsuperOETHbPrices.vy` | Base-specific wrapped yield price | Omitted | disabled | Yes for Base | Base-only asset/yield dependency |
| CM-040 | `RedStone` | `contracts/priceSources/RedStone.vy` | Optional oracle adapter | Omitted initially | disabled | Yes for Base | No approved RH use |
| CM-041 | `UndyVaultPrices` | `contracts/priceSources/UndyVaultPrices.vy` | Underscore vault pricing | Omitted | disabled | Yes for Base | Underscore unsupported initially |
| CM-042 | `Underscore Vault` | `migrations/base-mainnet/2025102200_UnderscoreVault.py`, current manifest | Base Underscore integration | Omitted | disabled | N/A external | Unsupported integration |
| CM-043 | `CreditRedeem` | `contracts/core/CreditRedeem.vy` | Collateral redemption Department | May support other assets; Stock Token redemption flag must be false | reused unchanged | Yes | —; Stock Token disablement is asset configuration, not source modification |
| CM-044 | `Deleverage` | `contracts/core/Deleverage.vy` | Withdrawal deleveraging and cooldown | Same role with portable cooldown semantics | modified | Yes | BN-012 duplicate cap and repeated-number bypass |
| CM-045 | `TellerUtils` | `contracts/core/TellerUtils.vy` | Teller helper/view logic | Same local helper | reused unchanged | Yes | — |
| CM-046 | `SwitchboardEcho` | `contracts/config/SwitchboardEcho.vy` | Treasury, Endaoment, and PSM governance actions | Required and registered if PSM is deployed for later enable/tuning; configure no unsupported external paths | reused unchanged | Yes | — |
| CM-047 | `EndaomentFunds` | `contracts/core/EndaomentFunds.vy` | Treasury fund custody/routing | Local custody/routing with Base-specific targets disabled | reused unchanged | Yes | — |
| CM-048 | `EndaomentPSM` | `contracts/core/EndaomentPSM.vy` | USDG-style PSM/reserve conversion | Deploy disabled or omit activation until USDG price path is approved | deferred | Yes | USDG price path and PSM launch state remain owner decisions |
| CM-049 | `DefaultsRobinhood` | New chain-specific defaults artifact parallel to `DefaultsBase.vy` | N/A | RH constructor/default parameter source | replaced | Chain-specific data, common interfaces | Required replacement for CM-007; contains values only, never divergent protocol logic |
| CM-050 | `AeroRipePrices` | `contracts/priceSources/AeroRipePrices.vy` | Base Aerodrome snapshot pricing; absent from current manifest | Omitted | disabled | Yes for Base | Unsupported Aerodrome integration |
| CM-051 | GREEN CCIP BurnMint pool | Net-new shared Solidity integration, exact package pending Track 1 | N/A / counterpart required on Base | Burn/mint GREEN across Base and RH | deferred | Yes, same integration source both chains | No existing source to modify; package, interface, specification, and final decision remain pending Track 1 |
| CM-052 | RIPE CCIP BurnMint pool | Net-new shared Solidity integration, exact package pending Track 1 | N/A / counterpart required on Base | Burn/mint RIPE across Base and RH | deferred | Yes, same integration source both chains | Same net-new/pending status as CM-051 |
| CM-053 | CCIP token-admin registration | Chainlink registry/admin transaction sequence | Register Base pool/token | Register RH pool/token | deferred | Same operational pattern | Assisted registration vs token `getCCIPAdmin()` pending Track 1 and owner |
| CM-054 | GREEN/RIPE local price adapter | Not yet specified | Base uses existing liquidity/reference pricing | Price-dependent GREEN/RIPE features remain off | deferred | Yes if built | No approved local price source; do not use a fabricated peg |
| CM-055 | Deployment, migration, and parameter-report tooling | `config/BluePrint.py`, `scripts/migrate.py`, `scripts/params/**`, `migrations/base-mainnet/**` | Base/local deployment graph and parameter reports | Clean Robinhood graph, ordered migrations, and correctly scaled cadence-field reports | modified | Shared framework, chain-specific graph | Current CLI/blueprint has no RH target; the generic percent formatter overstates CAD-001's ideal runtime slope 100× |
| CM-056 | Manifests and migration history | `migration_history/base-mainnet/**`, migration utilities | Base address/ABI history | Independent RH history/manifest | modified | Shared schema/tooling | New chain namespace and no address reuse |
| CM-057 | ABI export and explorer verification | `scripts/export_abis.py`, `scripts/verify.py`, `scripts/utils/verify_etherscan.py` | Vyper ABI export and Etherscan/Basescan verification | Verify Vyper plus CCIP Solidity artifacts on RH explorer | modified | Shared tooling | Export currently scans Vyper; verification assumes Etherscan-style/Base paths |
| CM-058 | Solidity build/test/deploy toolchain | No committed canonical path for CCIP additions | Not required by current Vyper-only core | Build, test, deploy and verify CCIP pools | deferred | Yes | Toolchain boundary and dependency/version ownership unapproved |
| CM-059 | Base/RH test profiles | `tests/**`, `tests/conf_core.py`, `tests/conf_utils.py` | Ordinary monotonic local block behavior | Base plus repeated-number, +1 and multi-jump RH clock profiles | modified | Shared test suite | Current helpers do not prove the L1-derived repeat/jump behavior required by Track 3 |
| CM-060 | `DefaultsLocal` | `contracts/config/DefaultsLocal.vy` | Local-test parameter source | Not a Robinhood deployment artifact; remains usable by generic tests | disabled | Chain-specific test data | RH receives CM-049 instead; local defaults must not be copied as production configuration |

### Inherited source modules

These sources are not independently deployed and therefore do not receive separate
deployment IDs. Their status follows the deployable rows shown here:

| Modules | Source paths | Parent rows and disposition |
| --- | --- | --- |
| Address/Department/governance/timelock modules | `contracts/modules/Addys.vy`, `contracts/modules/DeptBasics.vy`, `contracts/modules/LocalGov.vy`, `contracts/modules/TimeLock.vy`; `contracts/registries/modules/AddressRegistry.vy` | CM-004–006, CM-010–021 and Departments; reused unchanged, with per-chain block timelocks from BN-001/003/004/018–021 |
| Token modules | `contracts/tokens/modules/Erc20Token.vy`, `contracts/tokens/modules/Erc4626Token.vy` | CM-001–003; reused unchanged under the preferred assisted-admin path |
| Vault modules | `contracts/vaults/modules/BasicVault.vy`, `contracts/vaults/modules/SharesVault.vy`, `contracts/vaults/modules/StabVault.vy`, `contracts/vaults/modules/VaultData.vy` | CM-022–025; shared sources retained, while use of `SharesVault` is deferred with CM-025 |
| Price-source data module | `contracts/priceSources/modules/PriceSourceData.vy` | CM-015–020 and CM-039–041/050; shared module unchanged, with unsupported deployables disabled |

## Configuration, divergence, specification, and test matrix

“Dated manifest” below means the pinned repository manifest; it is not a claim
about current live Base bytecode or current external state.

| ID | Base configuration | Robinhood configuration / omission | External dependencies; clock | Live Base vs proposed canonical / divergence | Unresolved decision; required specification and tests | Evidence / confidence |
| --- | --- | --- | --- | --- | --- | --- |
| CM-001–002 | Dated manifest token addresses; RipeHq permissions | New local addresses; local minters/burners; CCIP pool capability | RipeHq, pools, Token Admin Registry; BN-001 HQ change | Preferred canonical token source unchanged, so no source divergence. If admin getter is added, Base upgrade policy applies | Track 1 registration facts; specify pool caps/roles and test mint/burn authority, supply conservation, remote mapping | Source + executive summary; high, Track 1 pending |
| CM-003 | Dated sGREEN deployment and integrations | New local sGREEN or explicit omitted-address behavior | GREEN, AuctionHouse, StabilityPool; timestamp ERC-4626 behavior | Omission is configuration only if every consumer supports it; otherwise shared spec/change is needed | Owner include/omit decision; test liquidation, Stability Pool, address registry, wants-sGREEN branches, zero/absent address | Source and migrations; high on dependency, decision open |
| CM-004 | Dated HQ; Base registry delay about 12h | New HQ; RH-equivalent registry delay; grant CCIP `canMintGreen` only if approved | Governance and all Departments; BN-018 | Source unchanged | Capability/CCIP authority spec and negative permission tests | Source/tests; high |
| CM-005 | Dated contributor config; block action delay plus timestamp vesting | RH block delay; seconds vesting unchanged | HR/RIPE; BN-005/006 + TS-002 | Source unchanged | Confirm HR included and mixed-unit runbook; repeat/jump/vesting tests | Source/generated snapshot; high |
| CM-006 | Base launch restrictions | RH launch restrictions | Governance/operator addresses; inherited timelocks | Source unchanged | Owner provides roles and exit criteria; permission tests | Source/migrations; high |
| CM-007, CM-049 | Base values remain in `DefaultsBase`, including raw `increasePerDangerBlock=10` | `DefaultsRobinhood` supplies RH cadence, bounds, integrations, and addresses; CAD-001 must be explicit/inactive while Curve is omitted | No external runtime dependency; all BN config plus CAD-001 | Live Base can retain Base defaults; canonical interfaces remain common | Shared block-clock spec must enumerate values and forbid logic/`chain.id` branches; generated-default parity tests must reject silent Base-cadence copies | Defaults/blueprint; high |
| CM-008 | `shouldCheckLastTouch=True` in Base defaults | Owner-approved portable guard or explicit false only after security acceptance | Teller/MissionControl; BN-002 | Modification creates temporary live Base divergence until upgraded; permanent divergence not recommended | Define threat and replacement semantics; same-number multi-transaction, liquidation and borrow abuse tests | Source/tests; high mechanics, policy open |
| CM-009 | 2025-12-02 general/asset/vault parameters; `increasePerDangerBlock=10` in current defaults; snapshot displays the latter as `0.10%` using the wrong denominator | RH-specific durations/rates/assets; same schema; explicitly mark CAD-001 inactive while Curve is unregistered | All protocol components; many BN IDs plus CAD-001 | Source unchanged; values differ by configuration | Full parameter manifest; Base/RH generated defaults and bounds tests; no silent cadence-field copy; distinguish raw, displayed, and runtime-effective danger rates | Source/defaults/scripts; high |
| CM-010–013 | 2025-12-02 registered Switchboards and action delays | New local addresses; RH action delays and values; Alpha owns CAD-001's governed setter | HQ/MissionControl; BN-004, domain clocks, CAD-001 | Sources unchanged | Migration ordering, permissions, action-expiration jump tests, per-domain setter tests including nonzero danger-rate validation | Source/migrations/tests; high |
| CM-014 | `Deleverage.deleverageCooldown` storage initializes to `0`; no repository snapshot proves current live state; duplicated max `7,200`; Base bond terms | RH owner-selected cooldown max and RH bond durations | MissionControl, Deleverage, BondRoom/BondBooster, Ledger, HumanResources/Contributor; BN-002/012/013/016/017/032 + TS-002 | Shared modification; Base may remain older only temporarily with tracked upgrade | Cooldown intent and one shared validation source; tests for same-number exception, bounds, epoch starts; reconcile HR bound drift | Source/tests; high mechanics |
| CM-015 | Dated registered Base price sources | Register only approved RH sources | Feed adapters and MissionControl stale seconds; timestamp context | Source unchanged | RH registration allowlist/omission spec; negative unsupported-source tests | Source/migrations; high |
| CM-016 | Existing Base feed configs; exact values must be live-checked | Official Chainlink Stock Token feed(s), no duplicate multiplier; USDG only if approved | Chainlink feeds/sequencer requirements pending Track 1; timestamp staleness | Source unchanged | Track 1 current facts; feed decimals, quote, heartbeat, stale time, sequencer policy; fork/integration tests | Source + executive summary; high architecture, external facts pending |
| CM-017 | Base Curve config, pools, `staleBlocks=43,200` migration; danger blocks feed CAD-001 | Do not deploy/register, leaving CAD-001 inert | Curve pools; BN-010/011 and CAD-001 | Base-only live source can remain; omission is not a fork | Negative registration/no-address tests and proof CreditEngine returns base rate without Curve | Source/migration/CreditEngine; high |
| CM-018–020 | Optional Base price adapters/configs | Do not deploy/register initially | External protocols/oracles; timestamp stale/snapshot clocks | Base can remain live; no RH divergence | Omission allowlist and negative routing tests | Source/selected architecture; high |
| CM-021 | Dated vault implementations and registry delay | Register only owner-approved Stock vault plus core vaults; RH delay | HQ/vault implementations; AddressRegistry clock | Source unchanged | Vault registration order and capability tests | Source/migrations; high |
| CM-022–023 | Dated core vault config; RipeGov Base lock terms | Local config; RipeGov terms scaled for RH wall time | GREEN/RIPE, liquidation/rewards; BN-007–009 | Sources unchanged | sGREEN consequence, RipeGov coarse clock acceptance; repeat/jump and liquidation tests | Source/tests; high |
| CM-024–025 | Both implementations exist in Base manifest | Exactly one selected for Stock Token, unless owner specifies multiple asset-specific registrations | Stock Token transfer/rebase behavior pending Track 2 | Source can remain common whichever is chosen; selection is not a fork | Owner choice after Track 2. Compare phantom collateral, rebase/share accounting, transfer-from-vault, first-withdrawer and total-supply invariants | Source + executive summary; high on code, behavior pending Track 2 |
| CM-026–027 | Base auction delay/duration and local dependencies | RH auction values, same roles | MissionControl, CreditEngine, vaults; BN-030/031 | Sources unchanged | Auction duration/jump profile and sGREEN output path; repeated/jump price, skipped-window and NFT claim tests | Source/tests; high |
| CM-028 | Base rewards config | RH local rewards config | RIPE/Lootbox/BondRoom; indirect BN clocks | Source unchanged | Reward-role and accounting integration tests | Source/migrations; high |
| CM-029 | Base epoch `14,400`, restart `0` | Provisionally `2,400` for 8h, restart owner-set | RIPE/RipeGov/BondBooster; BN-014–017 | Source unchanged | Epoch/jump spec; repeat, +1 and multi-epoch jump tests | Source/defaults/tests; high |
| CM-030 | Borrow interval `43,200`; seconds interest; Curve danger boost consumes CAD-001 | Provisionally `7,200` for one day; seconds interest unchanged; base-rate fallback while Curve is absent | Oracles/vaults; BN-029, TS-010, CAD-001 | Source unchanged | Debt/rate parameters; repeat/jump capacity with timestamp interest tests; unregistered-Curve fallback and future danger-rate calibration tests | Source/defaults/tests; high |
| CM-031 | Base Curve/liquidity/yield treasury actions configured as applicable | Local reserve role; leave unsupported partner-liquidity, Curve and yield actions unconfigured | EndaomentFunds/PSM/external protocols; inherited timelocks | Source unchanged if omission is fully supported | Explicit action/permission allowlist and negative tests; no silent zero-address calls | Source/migrations/executive summary; medium-high |
| CM-032 | Dated HR deployment | Deploy only if contributors are required at launch | Contributor/RIPE/governance; mixed clocks | Source unchanged | Inclusion/roles; reconcile existing defaults/setter mismatch (1-week/10-year defaults versus >1-month/≤5-year governed vesting bounds); contributor lifecycle and permission tests | Source/defaults/Switchboard/tests; high |
| CM-033 | `ripePerBlock=0.0075`; Underscore interval/min `43,200` | Tokenomics-approved per-increment rate (about `0.045` preserves time-rate); Underscore disabled; portable minimum | RIPE, vaults, Underscore; BN-022–026 | Shared modification; Base live divergence until upgrade if new minimum source changes bytecode | Rewards owner approves time-rate/coarse accrual; parameterize minimum; dual profile accounting tests | Source/defaults/tests; high mechanics |
| CM-034 | Ledger guard requested under configured conditions | Same entry point with approved Ledger behavior | Every user-facing Department; BN-002 via Ledger | Teller source unchanged if Ledger interface stays stable | End-to-end guard and permission regression suite | Source/tests; high |
| CM-035–037 | Dated external pool manifest entries | No addresses, registration or permissions | Curve/Aerodrome | Base-only external state remains | Negative deployment/config assertions; no current-address claims | Manifest/migrations; high |
| CM-038 | Base absolute expiry and lock terms | Chain-native absolute expiry and RH lock terms | BondRoom/RipeGov; BN-032 | Source unchanged | Operational absolute-number specification; expiry/repeat/jump tests | Source/generated snapshot; high |
| CM-039–042, CM-050 | Base-specific yield, Aero and Underscore components | Omitted and unregistered | Base external protocols; timestamp snapshot clocks where applicable | Base remains independent; omission is not bytecode divergence | Negative routing/zero-address tests and deployment-manifest absence | Source/manifest/architecture; high |
| CM-043 | Per-asset `canRedeemCollateral` may be enabled for Base assets | `canRedeemCollateral=false` for Stock Token; other assets separately approved | CreditEngine/PriceDesk/assets; no direct clock | Source unchanged | Stock asset config invariant and failed redemption test | Source/executive summary; high |
| CM-044 | Contract-local cooldown storage initializes to `0`; current live value is not in repository snapshots; max duplicated at `7,200` | Owner-approved portable cooldown and max | SwitchboardDelta/Teller; BN-012 | Shared modified canonical; Base upgrade/divergence plan required | Same specification/tests as CM-014 plus withdrawal multi-asset semantics | Source/tests; high mechanics |
| CM-045 | Dated helper deployment | New local helper address | Teller and registries; no direct clock | Source unchanged | ABI/address wiring regression tests | Source/manifest; high |
| CM-046 | Base Endaoment/PSM governance actions, including timelocked interval updates | Deploy/register whenever CM-048 is deployed, even disabled, so later PSM enable/tuning has a governance path; configure only supported local operations | Endaoment, EndaomentPSM, external destinations; BN-004 and BN-027/028 | Source unchanged | Explicit allowlist; `setPsmNumBlocksPerInterval` execution; disabled-to-enabled governance; no-unsupported-operation tests | Source/migrations/`test_switchboard_echo.py`; high |
| CM-047 | Base treasury destinations | RH local custody; external/yield destinations unset unless approved | Endaoment/PSM/governance; inherited timelocks | Source unchanged | Custody/withdrawal authority and zero-address behavior specification/tests | Source/migrations; high |
| CM-048 | Base PSM interval `43,200`, 2025-12-02 snapshot/deployment context; yield position must be checked | Disabled or inactive until USDG price source approved; if enabled interval provisionally `7,200`; yield position `(0, zero address)`; CM-046 still required if deployed for later activation | USDG token/feed, Endaoment, SwitchboardEcho; BN-027/028 | Source unchanged; activation/config differs | Owner selects existing approved price source, new separately reviewed adapter, or disabled. Mint/redeem cap, peg, reserve, governance enablement, disabled and no-yield tests | Source/migrations/executive summary; high mechanics, decision open |
| CM-051–052 | No existing deployment; Base counterpart pools are required if approved | Proposed RH pools; only GREEN/RIPE bridged | Chainlink CCIP Router, RMN, Token Admin Registry; no protocol block clock assumed | Deferred net-new shared Solidity source; once frozen, identical pool implementations deploy on Base/RH while core Vyper remains common | Pending Track 1 exact interfaces/versions. Specify owner/admin, rate limits, remote pools, RipeHq capability and emergency controls; unit/integration/fork tests | Executive summary; external facts pending Track 1 |
| CM-053 | Base registration transaction sequence | RH registration transaction sequence | Chainlink registries/admin accounts | Operational state, not a fork | Owner chooses assisted registration unless Track 1 demonstrates need for `getCCIPAdmin()`. Test/verify registered admins and pool mappings on both chains | Executive summary; pending Track 1 |
| CM-054 | Base GREEN/RIPE pricing exists through liquidity integrations | No fabricated local price; dependent features disabled | Future approved oracle/adapter | Deferral is launch configuration | Separate oracle spec, manipulation/staleness review and tests before enablement | Executive summary; high |
| CM-055 | Migration CLI exposes local/Base/ETH flows and generated Base parameter reports; CAD-001 is displayed with a generic `100_00` percent denominator | Explicit RH target, chain IDs/config, graph, idempotence and dry-run; cadence reports must use field-specific denominators | RPC, deployer/safe, explorer; all clocks as constructor args | Tooling modification; no protocol fork | Deployment runbook/spec; clean-chain dry run, resume/idempotence and failure recovery tests; raw/formatted/runtime regression for CAD-001 before DefaultsRobinhood parity reports | Scripts/migrations; high |
| CM-056 | 48-entry dated Base manifest/history | Separate RH manifest/history with provenance | Deployment outputs | Schema shared; state separate by chain | Manifest schema, commit/RPC/time metadata, uniqueness and completeness validation | Manifest/utilities; high |
| CM-057 | Vyper ABI exporter and Etherscan/Basescan assumptions | Export Vyper + Solidity ABIs; verify RH explorer using supported API | Explorer and compiler metadata | Shared tooling modified | Tool version pinning, flattened/standard JSON inputs, verification smoke tests | Scripts/ABIs; high |
| CM-058 | Current production build is Vyper-centric | Owner-approved Solidity package manager/compiler/test/deployer for CCIP | Chainlink Solidity packages | New tool boundary; must not create a second deployment truth source | Owner chooses Foundry or other boundary, locks dependency/compiler versions and CI; unit/fuzz/integration tests | Repository/tooling audit; high on gap |
| CM-059 | Existing tests advance blocks monotonically | Add Base cadence plus RH repeat, +1 and multi-jump profiles | Local EVM must emulate observed number semantics | Test-only shared change | Clock fixture spec and coverage gate for every BN ID; matrix omission/config tests | Tests + block inventory; high |
| CM-060 | Local-only generated values | Omit from RH manifests; retain only for generic local tests | None at launch | Omission is expected, not live-version divergence | Assert RH migrations select `DefaultsRobinhood`, never `DefaultsLocal`; keep generic local tests passing | Source/deployment scripts; high |

## Current-manifest coverage

The pinned Base manifest contains **48** names. Each appears exactly once below and
maps to one component row; proposed Robinhood additions, tooling, and explicitly
omitted local-test defaults are CM-049–060.

| Manifest name | Matrix ID | Manifest name | Matrix ID |
| --- | --- | --- | --- |
| `AuctionHouse` | CM-026 | `AuctionHouseNFT` | CM-027 |
| `BlueChipYieldPrices` | CM-018 | `Boardroom` | CM-028 |
| `BondBooster` | CM-038 | `BondRoom` | CM-029 |
| `ChainlinkPrices` | CM-016 | `Contributor` | CM-005 |
| `CreditEngine` | CM-030 | `CreditRedeem` | CM-043 |
| `CurvePrices` | CM-017 | `DefaultsBase` | CM-007 |
| `Deleverage` | CM-044 | `Endaoment` | CM-031 |
| `EndaomentFunds` | CM-047 | `EndaomentPSM` | CM-048 |
| `GreenPool` | CM-035 | `GreenToken` | CM-001 |
| `HumanResources` | CM-032 | `Ledger` | CM-008 |
| `Lootbox` | CM-033 | `MissionControl` | CM-009 |
| `PriceDesk` | CM-015 | `PythPrices` | CM-019 |
| `RebaseErc20` | CM-025 | `RedStone` | CM-040 |
| `RipeGov` | CM-023 | `RipeHq` | CM-004 |
| `RipePoolAero` | CM-037 | `RipePoolCurve` | CM-036 |
| `RipeToken` | CM-002 | `SavingsGreen` | CM-003 |
| `SimpleErc20` | CM-024 | `StabilityPool` | CM-022 |
| `StorkPrices` | CM-020 | `Switchboard` | CM-010 |
| `SwitchboardAlpha` | CM-011 | `SwitchboardBravo` | CM-012 |
| `SwitchboardCharlie` | CM-013 | `SwitchboardDelta` | CM-014 |
| `SwitchboardEcho` | CM-046 | `Teller` | CM-034 |
| `TellerUtils` | CM-045 | `TrainingWheels` | CM-006 |
| `Underscore Vault` | CM-042 | `UndyVaultPrices` | CM-041 |
| `VaultBook` | CM-021 | `wsuperOETHbPrices` | CM-039 |

## Architecture constraints captured

- Robinhood runs a local full Ripe protocol. It is not a federated satellite.
- Only GREEN and RIPE bridge through two minimal Base ↔ Robinhood CCIP BurnMint
  pools; collateral and positions do not bridge.
- Official Chainlink Stock Token feeds route through the existing adapter, with feed
  decimals/quote verified and no multiplier applied twice.
- Stock Token `CreditRedeem` is disabled by asset configuration.
- USDG PSM activation requires an approved price path; otherwise it stays disabled.
- Any PSM yield position is `(0, zero address)` unless separately approved.
- Curve, Aerodrome, Underscore, Base treasury/yield, and unsupported partner
  integrations are absent/unregistered on Robinhood.
- GREEN/RIPE local price-dependent functionality remains off until a reviewed price
  source exists.
- Base and Robinhood use one canonical production source except intentionally
  chain-specific defaults/configuration. No `chain.id` protocol branches are
  recommended.

## Decision register

Recommendations are not approvals.

| Decision | Available options | Evidence | Recommendation | Affected components | Owner / approver | Needed by | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Live Base parity | Upgrade Base first/together; allow time-bounded divergence; accept justified permanent exception | CM-008/014/033/044 require shared bytecode changes; CM-051/052 are deferred net-new sources rather than modifications to existing core | Use one canonical target and documented Base upgrade plan; permit temporary drift only with compatibility/security evidence and an expiry | CM-008, CM-014, CM-033, CM-044; future CM-051/052 counterparts | Protocol/deployment owner | Implementation release plan | Open |
| Shared clock posture | Retain/configure sound block clocks; convert all to timestamps; redesign semantic failures | Inventory maps 100 literals plus indirect CAD-001; only BN-002/012/025 show shared-source semantic/configuration failures | Retain/configure most sites; modify Ledger, Deleverage and Lootbox hard floor; make CAD-001 explicit/inactive | CM-008, CM-009, CM-011–014, CM-017, CM-029–030, CM-033, CM-038, CM-044, CM-049, CM-059 | Protocol/security owner | Block-clock specification | Open |
| Cooldown maximum intent | Preserve Base numeric `7,200` (~4h); preserve “one day” comment intent; choose another bound | The cap exists independently in Deleverage and SwitchboardDelta; cooldown is contract-local, not Mission Control/defaults | Decide in wall time, centralize the bound, then derive Base/RH values | CM-014, CM-044 | Security/protocol owner | Deleverage specification | Open |
| Ledger same-number guard | Portable replacement; explicit RH disable; accept RH throttling | BN-002 traces the guard and governed flag path through SwitchboardDelta/MissionControl | Portable shared replacement; disable only with explicit security acceptance | CM-008, CM-034 | Security owner | Ledger specification and RH config | Open |
| SavingsGreen deployment | Include local sGREEN; omit and specify all dependent behavior | Existing liquidation, Stability Pool, address, and lifecycle paths reference it | Include provisionally unless the owner approves and specifies omission changes | CM-003, CM-022, CM-026 | Protocol/product owner | Frozen deployment graph | Open |
| Stock Token vault | `SimpleErc20`; `RebaseErc20`/`SharesVault`; another approved shared implementation | Both sources exist; launch-token behavior remains pending Track 2 | Use Simple only if Track 2 and owner accept phantom-balance/first-withdrawer behavior; otherwise specify SharesVault invariants | CM-021, CM-024, CM-025 | Protocol/risk owner | After Track 2, before asset migration | Pending Track 2 and owner |
| USDG price path / PSM | Existing reviewed Chainlink feed/adapter; separately specified fixed/capped adapter; no PSM | No approved USDG source exists; PSM interval governance requires CM-046 when CM-048 is deployed for later enablement | Prefer an existing reviewed source; otherwise launch disabled, with Echo deployed if later activation is intended | CM-015, CM-016, CM-046, CM-048 | Risk/oracle owner | Before PSM activation | Open |
| CCIP registration/admin | Assisted Token Admin Registry; shared token `getCCIPAdmin()` revision if required | Existing token source remains unchanged under assisted registration; package/admin facts and net-new pools remain pending Track 1 | Prefer assisted registration; any token revision must be shared and carry an explicit Base policy | CM-001, CM-002, CM-051–053 | Security/deployment owner | After Track 1, before pool implementation | Pending Track 1 and owner |
| Solidity toolchain boundary | Foundry; another pinned repo-native toolchain; external untracked build process | Repository build/export/verification is Vyper-centric while proposed CCIP pools are Solidity | Commit one pinned repo-native toolchain, CI, ABI export and verification path; avoid an untracked parallel process | CM-051–053, CM-057–059 | Engineering/deployment owner | Before CCIP code | Open |

## Cross-track update path

- **Track 1:** replace `pending Track 1` in CM-001/002/016/051–053 with dated
  Chainlink facts, exact package/interface versions, registration requirements,
  supported chain selectors, and the approved admin path. If token source must
  change, update CM-001/002 to `modified` and add the Base upgrade decision.
- **Track 2:** attach its behavioral evidence to CM-024/025, then record the owner
  vault decision and asset invariants. Do not infer transferability from token
  branding or an interface alone.
- Any update should preserve CM IDs so implementation specifications and tests can
  cite stable rows.

## Validation and review eligibility

Completed against the pinned commit:

- all 48 current-manifest entries map exactly once to CM-001–048;
- contracts, inherited vault modules, non-contract external pools, disabled
  integrations, new CCIP additions, deployment tooling, ABI/verification tooling,
  manifests, and test infrastructure are represented;
- every `modified`, `replaced`, `disabled`, and `deferred` row states a reason;
- source status is separated from chain configuration and live Base bytecode;
- current external addresses are not asserted; the manifest is explicitly dated
  repository evidence requiring launch revalidation;
- 2025-12-02 generated parameter snapshots are dated explicitly rather than
  described as current live truth;
- indirect cadence field CAD-001 and its disabled-at-launch Curve dependency map to
  CM-007/009/011/017/030/049;
- CAD-001's generic parameter-report formatting defect is assigned to CM-055,
  with a raw/formatted/runtime regression requirement before RH parity reporting;
- PSM interval governance is traced through CM-046 SwitchboardEcho to CM-048;
- Stock Token facts and CCIP facts retain their Track 2/Track 1 pending labels;
- selected local-full-protocol architecture is used; no federated design is mixed in.

Reproducible structural checks:

```bash
# Expected: 48 manifest entries and 60 component rows
jq '.contracts | length' \
  migration_history/base-mainnet/v1/current-manifest.json
sed -n '/^## Component and source matrix/,/^### Inherited source modules/p' \
  docs/chains/rh/component-matrix.md | rg '^\| CM-' | wc -l

# Every status must be one of the five contract values
awk -F'|' '
  /^## Component and source matrix/{on=1; next}
  /^### Inherited source modules/{on=0}
  on && $2 ~ /CM-[0-9][0-9][0-9]/ {
    value=$7; gsub(/^ +| +$/, "", value); print value
  }
' docs/chains/rh/component-matrix.md | sort | uniq -c

# Each manifest name must occur once in the coverage section
jq -r '.contracts | keys[]' \
  migration_history/base-mainnet/v1/current-manifest.json |
while IFS= read -r name; do
  count=$(sed -n '/^## Current-manifest coverage/,/^## Architecture/p' \
    docs/chains/rh/component-matrix.md | rg -F -c "\`$name\`" || printf '0')
  if [ "${count:-0}" -ne 1 ]; then
    printf '%s count=%s\n' "$name" "${count:-0}"
  fi
done

# Every production Vyper source path must appear in this matrix
while IFS= read -r contract_file; do
  rg -F -q "\`$contract_file\`" docs/chains/rh/component-matrix.md ||
    printf 'missing %s\n' "$contract_file"
done < <(find contracts -type f -name '*.vy' \
  ! -path 'contracts/mock/*' | sort)

git diff --check
git show --check --oneline HEAD
```

The following exact `docs/chains/rh-summary.md` checkboxes have evidence complete
enough for owner review and possible closure:

- “Pin the exact release commit and regenerate the `block.number` inventory from
  that commit.” The pinned Track 3 release input is recorded; the owner should
  confirm that this integration commit is the intended release pin.
- “Create a Base-versus-Robinhood component matrix using the definitions above:
  `reused unchanged`, `modified`, `replaced`, `disabled`, or `deferred`.”
- “Classify every retained `block.number` use as: configurable economic duration;
  hardcoded economic duration; per-number rate or reward accrual; true same-number
  guard; or telemetry only.”
- “Review repeated and jumping numbers across:” the seven listed surfaces
  (timelocks, borrow/PSM intervals, auctions, deleverage, RipeGov, Lootbox, and
  retained price snapshots).

The following exact checkboxes are now decision-ready, but **not** eligible for
closure without owner or cross-track approval:

- “Commit to one canonical contract source and release line for Base and
  Robinhood; separate chain configuration and migration directories must not
  become separate protocol branches.”
- “Freeze the contracts that will be deployed on Robinhood and the Base-only
  contracts that will be omitted.”
- “Approve the live-version policy for every `modified` or `replaced` component
  while retaining one canonical source:”
- “Approve the shared clock posture: retain `block.number` where its semantics are
  acceptable on both chains, move cadence assumptions into per-chain parameters,
  and change hardcoded or same-number behavior in the canonical shared contracts.”
- “Resolve the deployable Stock Token vault path:” (pending Track 2).
- “Decide whether to deploy SavingsGreen/sGREEN on Robinhood; if it is omitted,
  identify the resulting Stability Pool, insurance, rewards, and lifecycle-test
  changes in the component matrix.”
- “Resolve the USDG price path:”
- “Pin the supported CCIP contracts release and decide how its Solidity contracts
  and artifacts will be built, tested, and deployed from this currently
  Vyper-focused repository.” (release facts pending Track 1; tooling decision is
  ready).
- “Prefer Chainlink-assisted registration so Robinhood can deploy the same existing
  GREEN and RIPE token implementations without adding a Robinhood-only
  `getCCIPAdmin()` change.” (pending Track 1 confirmation).
- “Define Base and Robinhood values for all block-denominated defaults, including
  governance and registry timelocks, borrow/PSM intervals, auctions, locks,
  rewards, cooldowns, and price snapshots.” Provisional conversions are inventoried;
  approval and final values remain open.
- “Recalculate per-number rates, especially RIPE rewards, so each chain preserves
  the intended time-based economics through configuration.” The approximately
  `0.045 RIPE` RH candidate requires tokenomics approval.
- “Replace the duplicated `7_200` maximum deleverage cooldown constants in
  `Deleverage` and `SwitchboardDelta` with one consistent configurable design.”
- “Resolve `Ledger`'s one-action-per-`block.number` rule as a chain-portable
  security policy.”
