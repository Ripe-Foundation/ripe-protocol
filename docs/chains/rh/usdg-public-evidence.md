# USDG public evidence for Robinhood Chain

**Status:** Complete technical evidence record; risk acceptance remains owner-gated

**Research date:** 23 July 2026

**Branch:** `rh-track-4-usdg-psm`

**Starting commit:** `d6efb34b5c28741fb25b053ea9b10af084fe7e53`

**Planning baseline:** `51a7a3996f5fec40efd554d1b025aaa9c2ed4ea2`

## Repository state

The starting commit differs from the planning baseline only by the addition of
`docs/chains/rh/track-4-usdg-psm-price-path.md`. There is no intervening
production-contract, defaults, migration, script, ABI, or test delta on which
this analysis depends.

The controlling architecture is
`${HOME}/dev/hightop-notes/random/hood/hood-chain-executive-summary.md`
at Hightop Notes commit
`a94decfd23e627e8079e7fcd6ce22b873f6371d0` (file blob
`a64a895e0542ed2482d7d5e857960d78eef1ffd8`) and
[`../rh-summary.md`](../rh-summary.md). The working copy of the architecture
file matched that committed blob during the follow-up review; unrelated dirty
media files in Hightop Notes were not used. This evidence record does not
modify either source.

## Intended environments

Retrieved 23 July 2026 from Robinhood's
[connection guide](https://docs.robinhood.com/chain/connecting/) and
[contract-address guide](https://docs.robinhood.com/chain/contracts/).

| Environment | Chain ID | Public RPC | Explorer |
| --- | ---: | --- | --- |
| Robinhood Chain mainnet | `4663` | `https://rpc.mainnet.chain.robinhood.com` | [Robinhood mainnet Blockscout](https://robinhoodchain.blockscout.com/) |
| Robinhood Chain testnet | `46630` | `https://rpc.testnet.chain.robinhood.com` | [Robinhood testnet Blockscout](https://explorer.testnet.chain.robinhood.com/) |

These are public endpoints. No private RPC, API key, signing key, or
transaction was used.

## Canonical USDG identity

### Mainnet

Robinhood and Paxos independently publish the same canonical mainnet address:

- Robinhood's current [contract list](https://docs.robinhood.com/chain/contracts/)
  identifies USDG as `0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168`.
- Paxos's current [USDG mainnet deployment guide](https://docs.paxos.com/guides/stablecoin/usdg/mainnet)
  identifies that token on chain ID `4663`, and identifies supply control
  `0xdf5FfF9cb88B3cAb50572FAE73E2EB08599D25D4`.
- The address is an ERC-1967 proxy. Its EIP-1967 implementation slot at the
  pinned block resolves to
  `0x68184C449E1a8f34fA18d289737129FD27B66f8F`.

Read-only state was pinned at block `17,572,269`, hash
`0x99c4f46a3a8f3bcd567ffaebf1e77502081e010943cfcc4bb706dfaf615fd3e9`,
timestamp `2026-07-23T20:24:04Z`.

| Fact | Pinned value |
| --- | --- |
| Proxy | [`0x5fc5…d168`](https://robinhoodchain.blockscout.com/address/0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168) |
| Implementation | [`0x6818…f8F`](https://robinhoodchain.blockscout.com/address/0x68184C449E1a8f34fA18d289737129FD27B66f8F) |
| Deployment type | OpenZeppelin ERC-1967 proxy with UUPS implementation |
| Proxy runtime-code hash | `0x864cc9ad53b338b82da1f7cab85ab0b3d5c8861acb422b6fec63cf36234f36a6` |
| Implementation runtime-code hash | `0x3a551ac5c744af57e68a1d1431ac403c0f516ffd7d224a75746aee11fc4f3baf` |
| Name / symbol | `Global Dollar` / `USDG` |
| Decimals | `6` |
| Total supply | `299100471343563` atomic = `299,100,471.343563 USDG` |
| Supply control | `0xdf5FfF9cb88B3cAb50572FAE73E2EB08599D25D4` |
| Default admin | `0xcFA0388f5ddf905FdC08c45c716C15Dc10A14C6F` |
| Default-admin delay | `10,800` seconds |
| Paused | `false` |

### Testnet

Paxos's current [USDG testnet deployment guide](https://docs.sandbox.paxos.com/guides/stablecoin/usdg/testnet)
identifies the canonical Robinhood testnet token as
`0x7E955252E15c84f5768B83c41a71F9eba181802F` and supply control as
`0x4549bb98c667aAb626627C118102c28065E8f54C`.

Read-only state was pinned at block `92,773,516`, hash
`0x569b2031b7aab3921ec575cf179604ef9560546e6af3ec5c1071835901b326dd`,
timestamp `2026-07-23T20:25:18Z`.

| Fact | Pinned value |
| --- | --- |
| Proxy | [`0x7E95…802F`](https://explorer.testnet.chain.robinhood.com/address/0x7E955252E15c84f5768B83c41a71F9eba181802F) |
| Implementation | [`0xF086…78DF`](https://explorer.testnet.chain.robinhood.com/address/0xF0863D7A29a55d0c4263c11bFac754312ff078DF) |
| Deployment type | ERC-1967 proxy; implementation is verified as `USDG` |
| Proxy runtime-code hash | `0x864cc9ad53b338b82da1f7cab85ab0b3d5c8861acb422b6fec63cf36234f36a6` |
| Implementation runtime-code hash | `0x72f197ff5ab8dcedf1244113dd91f245af65ae2c3354456d8bbfb6a3939ecd18` |
| Name / symbol | `Global Dollar` / `USDG` |
| Decimals | `6` |
| Total supply | `11001240000000` atomic = `11,001,240 USDG` |
| Supply control | `0x4549bb98c667aAb626627C118102c28065E8f54C` |
| Default admin | `0x3a5B30D74e90E08F0E576CF9f6F2457E44AF38B3` |
| Default-admin delay | `300` seconds |
| Paused | `false` |

A real canonical test USDG therefore exists; a mock reserve token is not
required. A mock price feed is still required for deterministic testnet
price-failure scenarios because no official testnet USDG feed was found below.

## Token mechanics relevant to the PSM

The verified mainnet implementation source agrees with Paxos's public
[`usdg-contract` repository](https://github.com/paxosglobal/usdg-contract):

- standard ERC-20 `transfer` and `transferFrom` return `bool` and move the exact
  requested atomic amount;
- balances do not rebase and transfers do not charge a token fee;
- there are no ERC-777-style receiver hooks in the transfer path;
- `balanceOf` and `totalSupply` exclude unclaimed claimable rewards; claiming
  transfers existing tokens from the configured claim source rather than
  rebasing every holder;
- EIP-2612 and EIP-3009 authorization methods add signing-based transfer
  methods but do not alter ordinary ERC-20 transfer accounting.

That behavior is compatible with `EndaomentPSM`'s exact-balance reserve model
and its `default_return_value=True` calls. The PSM hardcodes six reserve
decimals (`ONE_USDC = 10**6`), so the live `decimals() == 6` result is a
necessary compatibility condition, not merely a label match.

### Observable issuer and administrator controls

The current implementation exposes materially centralized controls:

- global transfer pause;
- per-address freeze/blocklist behavior;
- wipe of a frozen address, which burns that address's balance;
- supply-controller mint and burn;
- payout-group and reward administration;
- delayed default-admin transfer; and
- UUPS implementation upgrade authorization.

The current verified ABI/source showed no forced-transfer method and no
forced-redemption method. Administrative wipe is a clawback-like burn, not a
transfer to the issuer. This is a statement about the implementation observed
at the pinned block, not a promise about future upgrades.

No claim is made here that those controls are acceptable for launch. Their
acceptance is an explicit owner/risk/governance gate.

## Current USDG/USD feed on Robinhood mainnet

Robinhood directs builders to Chainlink for standard price feeds. Chainlink's
current official
[Robinhood feed directory](https://docs.chain.link/data-feeds/price-feeds/addresses?network=robinhood)
and its underlying
[Robinhood mainnet reference-data directory](https://reference-data-directory.vercel.app/feeds-robinhood-mainnet.json)
list a feed for the exact pair and network:

| Feed fact | Current value retrieved 23 July 2026 |
| --- | --- |
| Pair | `USDG / USD` |
| Standard proxy | `0x61B7e5650328764B076A108EFF5fa7282a1B9aD2` |
| Current aggregator | `0x8bEeE3503F6860D5dac4cE26b5eEe92982951c2e` |
| Product | `USDG/USD-RefPrice-DF-Robinhood-001` |
| Answer decimals | `8` |
| Heartbeat | `86,400` seconds |
| Deviation threshold | `0.5%` |
| Delivery / interface | Data Feed, standard `AggregatorV3Interface`; not Data Streams |

At mainnet block `17,572,269`:

| Read-only check | Result |
| --- | --- |
| Proxy description | `USDG / USD` |
| Proxy decimals / version | `8` / `6` |
| Proxy aggregator | `0x8bEeE3503F6860D5dac4cE26b5eEe92982951c2e` |
| Proposed aggregator | zero address |
| Proxy access controller | zero address |
| Proxy / aggregator owner | `0xeE27D5Ae494300902D90454e8630A3F1C68c9C52` |
| Aggregator type | `DualAggregator 1.0.0` |
| Latest round | `18446744073709551665` |
| Answer | `100004104` = `$1.00004104` |
| `startedAt` | `2026-07-23T15:15:49Z` |
| `updatedAt` | `2026-07-23T15:16:02Z` |
| `answeredInRound` | equal to `roundId` |
| Proxy runtime-code hash | `0xbd6f524cdc4268b6bd1bb6f77a8821faeea9c52ee9e0afa0b6d948ce82c966c2` |
| Aggregator runtime-code hash | `0x206a881c94ecf09d4b9e94ce7d859d6b0acdec074f05f9917072d8da659b6764` |

The answer was positive, round-complete, not future-dated, and about five hours
old at the pinned block, within the published heartbeat. The proxy was
publicly readable. These facts establish current operational compatibility,
not future uptime.

The current Robinhood RDD contains no entry labeled as a sequencer-uptime feed,
and Ripe's `ChainlinkPrices` has no separate sequencer-uptime check. This is a
monitoring/restart-policy input for owner review, not evidence against the
USDG/USD proxy's AggregatorV3 compatibility.

### Compatibility with Ripe

`contracts/priceSources/ChainlinkPrices.vy:306-335` reads `decimals()` and
records it in the pending timelocked config when a governed feed is proposed;
`:342-362` revalidates and copies that config into live `feedConfig` only on
confirmation. The runtime path at `:182-197,261-293` uses the live stored
decimals and calls `latestRoundData()` on the configured standard proxy. It
rejects nonpositive answers, feed decimals above 18, future timestamps, zero
or incomplete rounds, and answers older than a nonzero effective stale time,
then normalizes to 18 decimals. The Robinhood feed meets that interface
without a new adapter.

The effective stale time is
`max(MissionControl.priceStaleTime, feedConfig.staleTime)`. Therefore a
feed-specific value cannot tighten a larger global value. The stale-round
check is conditional on this effective value being nonzero: if both settings
are zero, otherwise-valid answers of any age pass. Robinhood manifest and
smoke validation must therefore require
`0 < max(globalStaleTime, feedStaleTime) <= approvedCeiling`; at least one
setting must be positive and neither may exceed the ceiling.
`PriceSourceData.pause` blocks configuration changes but is not consulted by
`getPrice`; feed/source disablement and PSM pause are the actual runtime stop
paths.

### Testnet feed evidence

The official Chainlink directory currently exposes Robinhood mainnet, not a
Robinhood testnet USDG entry. The natural official RDD testnet filenames
checked on 23 July 2026 returned no document. This is evidence that no public
official testnet listing was found, not proof that no unpublished feed exists.

The implementation plan should use:

1. canonical Paxos testnet USDG for token behavior;
2. the repository's clearly labeled `MockChainlinkFeed.vy` for deterministic
   unit and testnet failure cases; and
3. a pinned Robinhood-mainnet fork or read-only integration check against the
   real proxy before production configuration.

No nonpublic Chainlink answer or Track 1 outreach is required for this
decision.

## Existing Ripe adapter inventory

All current sources implement the shared `PriceSource` interface, but interface
compatibility alone is not semantic reuse. The exact common read interface is
`getPrice(asset, staleTime, priceDesk)`, `getPriceAndHasFeed(...)`,
`hasPriceFeed(asset)`, and `addPriceSnapshot(asset)`. Mutable source
configuration is source-specific and, where present, follows the repository's
`LocalGov` plus `TimeLock` initiation/confirmation pattern.

| Source | Price premise / update path | Failure behavior relevant here | USDG disposition |
| --- | --- | --- | --- |
| `ChainlinkPrices` | Governed, timelocked standard Aggregator feed config | Invalid round returns zero; stale round returns zero only under a nonzero effective threshold; proxy revert propagates | **Usable existing path with nonzero stale-time invariant** |
| `RedStone` | Chainlink-like RedStone aggregator endpoints | Endpoint-specific freshness and feed assumptions | Reject label-level reuse; exact Robinhood USDG product is Chainlink |
| `PythPrices` | Pyth network and feed ID | Requires Pyth product/config and update semantics | No current exact-network USDG evidence |
| `StorkPrices` | Stork network and feed ID | Requires Stork product/config | No current exact-network USDG evidence |
| `AeroRipePrices` | Aerodrome pool observations | Depends on a matching liquid local pool | Semantically inapplicable |
| `CurvePrices` | Curve pool/registry state | Depends on matching pool and liquidity assumptions | Semantically inapplicable |
| `BlueChipYieldPrices` | Underlying plus supported yield-token conversion | Wrapper/vault-specific failure surface | Semantically inapplicable |
| `UndyVaultPrices` | Underscore vault share conversion | Requires Underscore registry and vault | Forbidden Base-only dependency |
| `wsuperOETHbPrices` | Specific SuperOETH wrapper conversion | Asset-specific | Semantically inapplicable |

The repository contains Base deployment history for several sources, but no
repository evidence makes a non-Chainlink source a reviewed USDG path on
Robinhood. A semantic change to any of them would be a new adapter and require
its own specification. No audit report or third-party security attestation for
these adapters is present in this repository; this record therefore does not
promote repository deployment history into an audit claim.

## Reproducible read-only calls

These calls reproduce the critical identity and feed facts. Hex code output is
hashed locally with `cast keccak`.

```bash
MAINNET_RPC=https://rpc.mainnet.chain.robinhood.com
TESTNET_RPC=https://rpc.testnet.chain.robinhood.com
MAINNET_BLOCK=17572269
TESTNET_BLOCK=92773516
USDG=0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168
TEST_USDG=0x7E955252E15c84f5768B83c41a71F9eba181802F
MAINNET_IMPL=0x68184C449E1a8f34fA18d289737129FD27B66f8F
TESTNET_IMPL=0xF0863D7A29a55d0c4263c11bFac754312ff078DF
FEED=0x61B7e5650328764B076A108EFF5fa7282a1B9aD2
AGGREGATOR=0x8bEeE3503F6860D5dac4cE26b5eEe92982951c2e
IMPLEMENTATION_SLOT=0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc

cast chain-id --rpc-url "$MAINNET_RPC"
cast block "$MAINNET_BLOCK" --rpc-url "$MAINNET_RPC" --json
cast call "$USDG" 'name()(string)' --block "$MAINNET_BLOCK" --rpc-url "$MAINNET_RPC"
cast call "$USDG" 'symbol()(string)' --block "$MAINNET_BLOCK" --rpc-url "$MAINNET_RPC"
cast call "$USDG" 'decimals()(uint8)' --block "$MAINNET_BLOCK" --rpc-url "$MAINNET_RPC"
cast call "$USDG" 'totalSupply()(uint256)' --block "$MAINNET_BLOCK" --rpc-url "$MAINNET_RPC"
cast call "$USDG" 'paused()(bool)' --block "$MAINNET_BLOCK" --rpc-url "$MAINNET_RPC"
cast call "$USDG" 'defaultAdmin()(address)' --block "$MAINNET_BLOCK" --rpc-url "$MAINNET_RPC"
cast call "$USDG" 'defaultAdminDelay()(uint48)' --block "$MAINNET_BLOCK" --rpc-url "$MAINNET_RPC"
cast storage "$USDG" "$IMPLEMENTATION_SLOT" --block "$MAINNET_BLOCK" --rpc-url "$MAINNET_RPC"
cast keccak "$(cast code "$USDG" --block "$MAINNET_BLOCK" --rpc-url "$MAINNET_RPC")"
cast keccak "$(cast code "$MAINNET_IMPL" --block "$MAINNET_BLOCK" --rpc-url "$MAINNET_RPC")"

cast call "$FEED" 'description()(string)' --block "$MAINNET_BLOCK" --rpc-url "$MAINNET_RPC"
cast call "$FEED" 'decimals()(uint8)' --block "$MAINNET_BLOCK" --rpc-url "$MAINNET_RPC"
cast call "$FEED" 'version()(uint256)' --block "$MAINNET_BLOCK" --rpc-url "$MAINNET_RPC"
cast call "$FEED" 'owner()(address)' --block "$MAINNET_BLOCK" --rpc-url "$MAINNET_RPC"
cast call "$FEED" 'aggregator()(address)' --block "$MAINNET_BLOCK" --rpc-url "$MAINNET_RPC"
cast call "$FEED" 'proposedAggregator()(address)' --block "$MAINNET_BLOCK" --rpc-url "$MAINNET_RPC"
cast call "$FEED" 'accessController()(address)' --block "$MAINNET_BLOCK" --rpc-url "$MAINNET_RPC"
cast call "$FEED" 'latestRoundData()(uint80,int256,uint256,uint256,uint80)' \
  --block "$MAINNET_BLOCK" --rpc-url "$MAINNET_RPC"
cast call "$AGGREGATOR" 'owner()(address)' --block "$MAINNET_BLOCK" --rpc-url "$MAINNET_RPC"
cast call "$AGGREGATOR" 'typeAndVersion()(string)' --block "$MAINNET_BLOCK" --rpc-url "$MAINNET_RPC"
cast keccak "$(cast code "$FEED" --block "$MAINNET_BLOCK" --rpc-url "$MAINNET_RPC")"
cast keccak "$(cast code "$AGGREGATOR" --block "$MAINNET_BLOCK" --rpc-url "$MAINNET_RPC")"

cast chain-id --rpc-url "$TESTNET_RPC"
cast block "$TESTNET_BLOCK" --rpc-url "$TESTNET_RPC" --json
cast call "$TEST_USDG" 'name()(string)' --block "$TESTNET_BLOCK" --rpc-url "$TESTNET_RPC"
cast call "$TEST_USDG" 'symbol()(string)' --block "$TESTNET_BLOCK" --rpc-url "$TESTNET_RPC"
cast call "$TEST_USDG" 'decimals()(uint8)' --block "$TESTNET_BLOCK" --rpc-url "$TESTNET_RPC"
cast call "$TEST_USDG" 'totalSupply()(uint256)' --block "$TESTNET_BLOCK" --rpc-url "$TESTNET_RPC"
cast call "$TEST_USDG" 'paused()(bool)' --block "$TESTNET_BLOCK" --rpc-url "$TESTNET_RPC"
cast call "$TEST_USDG" 'defaultAdmin()(address)' --block "$TESTNET_BLOCK" --rpc-url "$TESTNET_RPC"
cast call "$TEST_USDG" 'defaultAdminDelay()(uint48)' --block "$TESTNET_BLOCK" --rpc-url "$TESTNET_RPC"
cast storage "$TEST_USDG" "$IMPLEMENTATION_SLOT" --block "$TESTNET_BLOCK" --rpc-url "$TESTNET_RPC"
cast keccak "$(cast code "$TEST_USDG" --block "$TESTNET_BLOCK" --rpc-url "$TESTNET_RPC")"
cast keccak "$(cast code "$TESTNET_IMPL" --block "$TESTNET_BLOCK" --rpc-url "$TESTNET_RPC")"
```

Pinned calls require an archive-capable endpoint. On a follow-up check later on
23 July 2026, Robinhood's public testnet RPC returned `missing trie node` for
the pinned historical state while unpinned current calls still returned the
same identity, controls, implementation, and code hashes. Use an archival
endpoint or explorer evidence to reproduce the exact pinned block; omit
`--block` only for a current drift check and do not present that result as the
pinned observation.

## Contradictions, inferences, and unresolved facts

- Any earlier assumption that Robinhood lacked an official USDG/USD standard
  feed is superseded by the current exact-network Chainlink RDD entry and
  onchain proxy state.
- The absence of a public testnet catalog entry is an inference from the
  current official directory, not a statement about nonpublic services.
- No sequencer-uptime entry was found in the same current public RDD; no claim
  is made about a nonpublic product.
- Code-hash and implementation facts are point-in-time because USDG is
  upgradeable.
- The role addresses above do not enumerate every facet-specific reward,
  freeze, pause, or upgrade administrator. A deployment smoke script must
  snapshot all relevant live roles/owners immediately before any launch
  approval.
- This evidence does not establish oracle uptime, USDG solvency or redemption
  rights, legal treatment, custody suitability, or acceptance of issuer/admin
  controls.

## What this evidence establishes

As of the pinned 23 July 2026 observations, canonical six-decimal USDG exists
on both intended Robinhood environments, its ordinary ERC-20 accounting is
compatible with the existing PSM reserve interface, and an official
AggregatorV3-compatible USDG/USD feed exists on Robinhood mainnet through the
existing Ripe `ChainlinkPrices` path. It does not authorize deploying,
registering, funding, or enabling a PSM.
