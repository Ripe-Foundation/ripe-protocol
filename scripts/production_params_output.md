================================================================================
# Ripe Protocol Production Parameters

**Generated:** 2025-12-01 02:28:42 UTC
**Block:** 38883364
**Network:** Base Mainnet

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [All Contract Addresses](#all-addresses)
3. [MissionControl Configuration](#mission-control)
   - [General Config](#general-config)
   - [Debt Config](#debt-config)
   - [Rewards Config](#rewards-config)
   - [Registered Assets](#registered-assets)
4. [RipeHQ Registry](#ripe-hq)
5. [Switchboard Registry](#switchboard)
6. [PriceDesk Oracles](#price-desk)
7. [VaultBook Registry](#vault-book)
8. [Ledger Statistics](#ledger)
9. [Endaoment PSM](#endaoment-psm)
10. [Core Lending Contracts](#core-lending)
    - [CreditEngine](#credit-engine)
    - [AuctionHouse](#auction-house)
    - [Teller](#teller)
    - [Deleverage](#deleverage)
    - [CreditRedeem](#credit-redeem)
    - [StabilityPool](#stability-pool)
11. [Treasury & Rewards Contracts](#treasury-rewards)
    - [Endaoment](#endaoment)
    - [BondBooster](#bond-booster)
    - [Lootbox](#lootbox)
    - [BondRoom](#bond-room)
    - [HumanResources](#human-resources)
12. [Governance Contracts](#governance)
    - [RipeGovVault](#ripe-gov-vault)
13. [Price Source Configurations](#price-sources)
14. [Token Statistics](#token-statistics)


<a id="executive-summary"></a>
## 📊 Executive Summary

| Metric | Value |
| --- | --- |
| **Total GREEN Supply** | 202.05K GREEN |
| **Total Debt Outstanding** | 74.39K GREEN |
| **Debt Utilization** | 37.19% of 200.00K GREEN limit |
| **Active Borrowers** | 78 |
| **Registered Assets** | 55 |
| **Bad Debt** | 0.00 GREEN |
| **RIPE Total Supply** | 10.32M RIPE |
| **sGREEN Exchange Rate** | 1.056821 GREEN per sGREEN (+5.6821% vs 1:1) |
| **Protocol Status** | ✅ Deposits / ✅ Borrowing / ✅ Liquidations |

<a id="all-addresses"></a>
## 📋 All Contract Addresses

*Complete list of all live protocol contract addresses*

### Core Protocol Contracts (RipeHQ Registry)
| ID | Contract | Address |
| --- | --- | --- |
| - | **RipeHQ** | `0x6162df1b329E157479F8f1407E888260E0EC3d2b` |
| 1 | Green Token | `0xd1Eac76497D06Cf15475A5e3984D5bC03de7C707` |
| 2 | Savings Green | `0xaa0f13488CE069A7B5a099457c753A7CFBE04d36` |
| 3 | Ripe Token | `0x2A0a59d6B975828e781EcaC125dBA40d7ee5dDC0` |
| 4 | Ledger | `0x365256e322a47Aa2015F6724783F326e9B24fA47` |
| 5 | Mission Control | `0xB59b84B526547b6dcb86CCF4004d48E619156CF3` |
| 6 | Switchboard | `0xc68A90A40B87ae1dABA93Da9c02642F8B74030F9` |
| 7 | Price Desk | `0x68564c6035e8Dc21F0Ce6CB9592dC47B59dE2Ff6` |
| 8 | Vault Book | `0xB758e30C14825519b895Fd9928d5d8748A71a944` |
| 9 | Auction House | `0x8a02aC4754b72aFBDa4f403ec5DA7C2950164084` |
| 10 | Auction House NFT | `0x504Fb3b94a9f4A238Ee3A16474B91F99A3f26F3A` |
| 11 | Boardroom | `0xb5cA6Ef866b510C3b85D4B0e3862061A569412D1` |
| 12 | Bond Room | `0x707f660A7834d00792DF9a28386Bb2cCC6446154` |
| 13 | Credit Engine | `0x30aa8eB041AcB3B22228516297C331B313b81462` |
| 14 | Endaoment | `0x70fA85Aa99a39161A2623627377F1c791fd091f6` |
| 15 | Human Resources | `0xF9aCDFd0d167b741f9144Ca01E52FcdE16BE108b` |
| 16 | Lootbox | `0x1f90ef42Da9B41502d2311300E13FAcf70c64be7` |
| 17 | Teller | `0xae87deB25Bc5030991Aa5E27Cbab38f37a112C13` |
| 18 | Deleverage | `0x75EeBb8c6f1A5727e7c0c1f9d64Ed07cd0966F27` |
| 19 | Credit Redeem | `0x3bfB0F72642aeFA2486da00Db855c5F0b787e3FB` |
| 20 | Teller Utils | `0x57f071AB96D1798C6bB3e314D2D283502DEDDcdD` |
| 21 | Endaoment Funds | `0x4Ce5FB8D572917Eb96724eA1866b505B2a6B0873` |
| 22 | Endaoment PSM | `0x2893d0dfa54571bDc7DE60F2d8a456d3377CcAA7` |

### Switchboard Registry
| ID | Contract | Address |
| --- | --- | --- |
| - | **Switchboard** | `0xc68A90A40B87ae1dABA93Da9c02642F8B74030F9` |
| 1 | Switchboard Alpha | `0x73Cd87A047eb16E22f8afA21e0980C07Bb26CA83` |
| 2 | Switchboard Bravo | `0xD18AC028cBe1AbebDb118E9C7A60018d58C846e7` |
| 3 | Switchboard Charlie | `0x6D798bD44b1591571c9d95b6D51c9c34a5534008` |
| 4 | Switchboard Delta | `0x50e815AC356798E42EB35De538a0376459ce11cb` |
| 5 | Switchboard Echo | `0xdF99a86e4450163e8DbA47C928131e75D2995dbb` |

### PriceDesk Registry (Oracle Sources)
| ID | Contract | Address |
| --- | --- | --- |
| - | **PriceDesk** | `0x68564c6035e8Dc21F0Ce6CB9592dC47B59dE2Ff6` |
| 1 | Chainlink | `0x253f55e455701fF0B835128f55668ed159aAB3D9` |
| 2 | Curve Prices | `0x7B2aeE8B6A4bdF0885dEF48CCda8453Fdc1Bba5d` |
| 3 | BlueChip Yield Prices | `0x90C70ACfF302c8a7f00574EC3547B0221f39cD28` |
| 4 | Pyth Prices | `0x89b6E13E4aD4036EAA586219DD73Ebb2b36d5968` |
| 5 | Stork Prices | `0xCa13ACFB607B842DF5c1D0657C0865cC47bEfe14` |
| 6 | Aero Ripe Prices | `0x5ce2BbD5eBe9f7d9322a8F56740F95b9576eE0A2` |
| 7 | wsuperOETHb Prices | `0x2606Ce36b62a77562DF664E7a0009805BB254F3f` |
| 8 | Undy Vault Prices | `0x2210a9b994CC0F13689043A34F2E11d17DB2099C` |

### VaultBook Registry
| ID | Contract | Address |
| --- | --- | --- |
| - | **VaultBook** | `0xB758e30C14825519b895Fd9928d5d8748A71a944` |
| 1 | Stability Pool | `0x2a157096af6337b2b4bd47de435520572ed5a439` |
| 2 | Ripe Gov Vault | `0xe42b3dC546527EB70D741B185Dc57226cA01839D` |
| 3 | Simple ERC20 Vault | `0xf75b566eF80Fde0dEfcC045A4d57b540eb43ddfD` |
| 4 | Rebase ERC20 Vault | `0xce2E96C9F6806731914A7b4c3E4aC1F296d98597` |
| 5 | Underscore Vault | `0x4549A368c00f803862d457C4C0c659a293F26C66` |

### Derived Contracts
| Contract | Source | Address |
| --- | --- | --- |
| BondBooster | BondRoom.bondBooster() | `0xA1872467AC4fb442aeA341163A65263915ce178a` |
| GREEN Pool | CurvePrices.greenRefPoolConfig() | `0xd6c283655B42FA0eb2685F7AB819784F071459dc` |

### Token Contracts
| Token | Address |
| --- | --- |
| GREEN | `0xd1Eac76497D06Cf15475A5e3984D5bC03de7C707` |
| sGREEN (Savings) | `0xaa0f13488CE069A7B5a099457c753A7CFBE04d36` |
| RIPE | `0x2A0a59d6B975828e781EcaC125dBA40d7ee5dDC0` |

---


================================================================================

<a id="mission-control"></a>
# MissionControl - Core Protocol Configuration
Address: 0xB59b84B526547b6dcb86CCF4004d48E619156CF3

## General Config
| Parameter | Value |
| --- | --- |
| perUserMaxVaults | 5 |
| perUserMaxAssetsPerVault | 15 |
| priceStaleTime | 0 seconds |
| canDeposit | True |
| canWithdraw | True |
| canBorrow | True |
| canRepay | True |
| canClaimLoot | True |
| canLiquidate | True |
| canRedeemCollateral | True |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |

## General Debt Config
| Parameter | Value |
| --- | --- |
| perUserDebtLimit | 20.00K GREEN |
| globalDebtLimit | 200.00K GREEN |
| minDebtAmount | 1.00 GREEN |
| numAllowedBorrowers | 1000 |
| maxBorrowPerInterval | 10.00K GREEN |
| numBlocksPerInterval | 43200 blocks (~1.0d) |
| minDynamicRateBoost | 100.00% |
| maxDynamicRateBoost | 500.00% |
| increasePerDangerBlock | 0.10% |
| maxBorrowRate | 100.00% |
| maxLtvDeviation | 10.00% |
| keeperFeeRatio | 1.00% |
| minKeeperFee | 1.00 GREEN |
| maxKeeperFee | 25.00K GREEN |
| isDaowryEnabled | True |
| ltvPaybackBuffer | 10.00% |

## General Auction Parameters
| Parameter | Value |
| --- | --- |
| hasParams | True |
| startDiscount | 1.00% |
| maxDiscount | 50.00% |
| delay | 0 blocks (~0s) |
| duration | 43200 blocks (~1.0d) |

## HR Config (Compensation)
| Parameter | Value |
| --- | --- |
| contribTemplate | `0x4965578D80E54b5EbE3BB5D7b1B3E0425559C1D1` |
| maxCompensation | 0.000000 RIPE |
| minCliffLength | 604800 blocks (~14.0d) |
| maxStartDelay | 7776000 blocks (~180.0d) |
| minVestingLength | 604800 blocks (~14.0d) |
| maxVestingLength | 315360000 blocks (~7300.0d) |

## RIPE Bond Config
| Parameter | Value |
| --- | --- |
| asset | USDC (`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`) |
| amountPerEpoch | 2,000.000000 (asset units) |
| canBond | False |
| minRipePerUnit | 0.000000 RIPE |
| maxRipePerUnit | 1.000000 RIPE |
| maxRipePerUnitLockBonus | 0.000000 RIPE |
| epochLength | 14400 blocks (~8.0h) |
| shouldAutoRestart | True |
| restartDelayBlocks | 0 blocks (~0s) |

## RIPE Rewards Config
| Parameter | Value |
| --- | --- |
| arePointsEnabled | True |
| ripePerBlock | 0.007500 RIPE |
| borrowersAlloc | 10.00% |
| stakersAlloc | 90.00% |
| votersAlloc | 0.00% |
| genDepositorsAlloc | 0.00% |
| autoStakeRatio | 75.00% |
| autoStakeDurationRatio | 33.00% |
| stabPoolRipePerDollarClaimed | 0.010000 RIPE |

## Total Points Allocations
| Parameter | Value |
| --- | --- |
| stakersPointsAllocTotal | 100.00% |
| voterPointsAllocTotal | 0.00% |

## RIPE Token Governance Vault Config
| Parameter | Value |
| --- | --- |
| minLockDuration | 43200 blocks (~1.0d) |
| maxLockDuration | 47304000 blocks (~1095.0d) |
| maxLockBoost | 200.00% |
| canExit | True |
| exitFee | 80.00% |
| assetWeight | 10000 |
| shouldFreezeWhenBadDebt | True |

## Other Settings
| Parameter | Value |
| --- | --- |
| underscoreRegistry | UNDERSCORE_REGISTRY (`0x44Cf3c4f000DFD76a35d03298049D37bE688D6F9`) |
| trainingWheels | `0x2255b0006A3DA38AA184E0F9d5e056C2d0448065` |
| shouldCheckLastTouch | True |

## Priority Price Source IDs
| Priority | Source ID |
| --- | --- |
| 0 | 1 |
| 1 | 3 |
| 2 | 4 |
| 3 | 5 |
| 4 | 2 |

## Priority Liquidation Asset Vaults
| Vault ID | Asset |
| --- | --- |
| 3 | USDC (`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`) |
| 3 | CBBTC (`0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf`) |
| 3 | WETH (`0x4200000000000000000000000000000000000006`) |
| 3 | USOL (`0x9B8Df6E244526ab5F6e6400d331DB28C8fdDdb55`) |
| 3 | CBDOGE (`0xcbD06E5A2B0C65597161de254AA074E489dEb510`) |

## Priority Stability Pool Vaults
| Vault ID | Asset |
| --- | --- |
| 1 | `0xd6c283655B42FA0eb2685F7AB819784F071459dc` |
| 1 | `0xaa0f13488CE069A7B5a099457c753A7CFBE04d36` |

## Registered Assets (55 total)
| Asset | Vault IDs | LTV | Liq Threshold | Borrow Rate | canDeposit | canBorrow |
| --- | --- | --- | --- | --- | --- | --- |
| USDC (`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`) | 3 | 80.00% | 90.00% | 5.00% | True | True |
| CBBTC (`0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf`) | 3 | 70.00% | 80.00% | 7.00% | True | True |
| WETH (`0x4200000000000000000000000000000000000006`) | 3 | 70.00% | 80.00% | 7.00% | True | True |
| `0xaa0f13488CE069A7B5a099457c753A7CFBE04d36` | 1 | 0.00% | 0.00% | 0.00% | True | False |
| `0xd6c283655B42FA0eb2685F7AB819784F071459dc` | 1 | 0.00% | 0.00% | 0.00% | True | False |
| RIPE_TOKEN (`0x2A0a59d6B975828e781EcaC125dBA40d7ee5dDC0`) | 2 | 0.00% | 0.00% | 0.00% | True | False |
| `0xF8D92a9531205AB2Dd0Bc623CDF4A6Ab4c3a2526` | 2 | 0.00% | 0.00% | 0.00% | False | False |
| CBDOGE (`0xcbD06E5A2B0C65597161de254AA074E489dEb510`) | 3 | 50.00% | 65.00% | 11.00% | True | True |
| USOL (`0x9B8Df6E244526ab5F6e6400d331DB28C8fdDdb55`) | 3 | 50.00% | 65.00% | 11.00% | True | True |
| RIPE_WETH_POOL (`0x765824aD2eD0ECB70ECc25B0Cf285832b335d6A9`) | 2 | 0.00% | 0.00% | 0.00% | True | False |
| MORPHO_SPARK_USDC (`0x7BfA7C4f149E7415b73bdeDfe609237e29CBF34A`) | 3 | 80.00% | 85.00% | 5.00% | True | True |
| AERO (`0x940181a94A35A4569E4529A3CDfB74e38FD98631`) | 3 | 50.00% | 65.00% | 8.00% | True | True |
| `0x784efeB622244d2348d4F2522f8860B96fbEcE89` | 4 | 50.00% | 65.00% | 8.00% | True | True |
| MOONWELL_AERO (`0x73902f619CEB9B31FD8EFecf435CbDf89E369Ba6`) | 3 | 50.00% | 65.00% | 8.00% | True | True |
| AAVEV3_USDC (`0x4e65fE4DbA92790696d040ac24Aa414708F5c0AB`) | 4 | 80.00% | 85.00% | 5.00% | True | True |
| AAVEV3_CBBTC (`0xBdb9300b7CDE636d9cD4AFF00f6F009fFBBc8EE6`) | 4 | 70.00% | 80.00% | 7.00% | True | True |
| AAVEV3_WETH (`0xD4a0e0b9149BCee3C920d2E00b5dE09138fd8bb7`) | 4 | 70.00% | 80.00% | 7.00% | True | True |
| VIRTUAL (`0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b`) | 3 | 50.00% | 65.00% | 11.00% | True | True |
| `0xcbADA732173e39521CDBE8bf59a6Dc85A9fc7b8c` | 3 | 50.00% | 65.00% | 11.00% | True | True |
| `0xcb585250f852C6c6bf90434AB21A00f02833a4af` | 3 | 50.00% | 65.00% | 11.00% | True | True |
| `0xcb17C9Db87B595717C857a08468793f5bAb6445F` | 3 | 50.00% | 65.00% | 11.00% | True | True |
| `0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf` | 3 | 40.00% | 50.00% | 13.00% | True | True |
| WELL (`0xA88594D404727625A9437C3f886C7643872296AE`) | 3 | 40.00% | 50.00% | 13.00% | True | True |
| `0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed` | 3 | 40.00% | 50.00% | 13.00% | True | True |
| COMPOUNDV3_WETH (`0x46e6b214b524310239732D51387075E0e70970bf`) | 4 | 70.00% | 80.00% | 7.00% | True | True |
| MORPHO_MOONWELL_WETH (`0xa0E430870c4604CcfC7B38Ca7845B1FF653D0ff1`) | 3 | 70.00% | 80.00% | 7.00% | True | True |
| MORPHO_SEAMLESS_WETH (`0x27D8c7273fd3fcC6956a0B370cE5Fd4A7fc65c18`) | 3 | 70.00% | 80.00% | 7.00% | True | True |
| EULER_WETH (`0x859160DB5841E5cfB8D3f144C6b3381A85A4b410`) | 3 | 70.00% | 80.00% | 7.00% | True | True |
| CBETH (`0x2Ae3F1Ec7F1F5012CFEab0185bfc7aa3cf0DEc22`) | 3 | 70.00% | 80.00% | 7.00% | True | True |
| MOONWELL_CBETH (`0x3bf93770f2d4a794c3d9EBEfBAeBAE2a8f09A5E5`) | 3 | 70.00% | 80.00% | 7.00% | True | True |
| COMPOUNDV3_USDC (`0xb125E6687d4313864e53df431d5425969c15Eb2F`) | 4 | 80.00% | 90.00% | 5.00% | True | True |
| MOONWELL_USDC (`0xEdc817A28E8B93B03976FBd4a3dDBc9f7D176c22`) | 3 | 80.00% | 90.00% | 5.00% | True | True |
| EULER_USDC (`0x0A1a3b5f2041F33522C4efc754a7D096f880eE16`) | 3 | 80.00% | 90.00% | 5.00% | True | True |
| FLUID_USDC (`0xf42f5795D9ac7e9D757dB633D693cD548Cfd9169`) | 3 | 80.00% | 90.00% | 5.00% | True | True |
| MORPHO_MOONWELL_USDC (`0xc1256Ae5FF1cf2719D4937adb3bbCCab2E00A2Ca`) | 3 | 80.00% | 90.00% | 5.00% | True | True |
| MORPHO_SEAMLESS_USDC (`0x616a4E1db48e22028f6bbf20444Cd3b8e3273738`) | 3 | 80.00% | 90.00% | 5.00% | True | True |
| EULER_CBBTC (`0x882018411Bc4A020A879CEE183441fC9fa5D7f8B`) | 3 | 70.00% | 80.00% | 7.00% | True | True |
| MOONWELL_CBBTC (`0xF877ACaFA28c19b96727966690b2f44d35aD5976`) | 3 | 70.00% | 80.00% | 7.00% | True | True |
| MORPHO_MOONWELL_CBBTC (`0x543257eF2161176D7C8cD90BA65C2d4CaEF5a796`) | 3 | 70.00% | 80.00% | 7.00% | True | True |
| `0x211Cc4DD073734dA055fbF44a2b4667d5E5fE5d2` | 3 | 80.00% | 90.00% | 5.00% | True | True |
| WRAPPED_SUPER_OETH (`0x7FcD174E80f264448ebeE8c88a7C4476AAF58Ea6`) | 3 | 70.00% | 80.00% | 7.00% | True | True |
| `0xd1Eac76497D06Cf15475A5e3984D5bC03de7C707` | None | 0.00% | 0.00% | 0.00% | False | False |
| UNDY_USD (`0xcF9F72237d4135a6D8b3ee717DC414Ae5b56E41e`) | 5 | 80.00% | 90.00% | 5.00% | False | True |
| UNDY_ETH (`0x01ECc16CE82CCf7e6f734351d5d3AdCf2f8D3497`) | 5 | 70.00% | 80.00% | 7.00% | False | True |
| UNDY_BTC (`0x4cD99832E44D1154bd7841f5E5E9ce66dA0437d4`) | 5 | 70.00% | 80.00% | 7.00% | False | True |
| `0xcdD894E6c11d6444e0c3d974928Dd71b28b09356` | 5 | 80.00% | 90.00% | 5.00% | False | True |
| `0x434696F22EF3862f14C6Abd008f18456418f7457` | 5 | 70.00% | 80.00% | 7.00% | False | True |
| `0x897b56836C79e68042EFc51be7ad652a4BBFb86b` | 5 | 70.00% | 80.00% | 7.00% | False | True |
| `0x9e629632c483235845E27840C304C11b59d2FEDa` | 5 | 50.00% | 65.00% | 8.00% | False | True |
| `0x4bCa2A052428D7b7D2E1Daf9e1af471EA4c2F7bf` | 5 | 80.00% | 90.00% | 5.00% | False | True |
| `0x02981DB1a99A14912b204437e7a2E02679B57668` | 5 | 70.00% | 80.00% | 7.00% | True | True |
| `0x3fb0fC9D3Ddd543AD1b748Ed2286a022f4638493` | 5 | 70.00% | 80.00% | 7.00% | True | True |
| `0xb33852cfd0c22647AAC501a6Af59Bc4210a686Bf` | 5 | 80.00% | 90.00% | 5.00% | True | True |
| `0x96F1a7ce331F40afe866F3b707c223e377661087` | 5 | 50.00% | 65.00% | 8.00% | True | True |
| `0x1cb8DAB80f19fC5Aca06C2552AECd79015008eA8` | 5 | 80.00% | 90.00% | 5.00% | True | True |

### Detailed Asset Configurations

#### USDC (0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913)

## USDC - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 100.000000 |
| globalDepositLimit | 1,000.000000 |
| minDepositBalance | 0.250000 |

## USDC - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 80.00% |
| redemptionThreshold | 85.00% |
| liqThreshold | 90.00% |
| liqFee | 5.00% |
| borrowRate | 5.00% |
| daowry | 0.25% |

## USDC - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

## USDC - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | False |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### CBBTC (0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf)

## CBBTC - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 2.500000 |
| globalDepositLimit | 25.000000 |
| minDepositBalance | 0.000025 |

## CBBTC - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

## CBBTC - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## CBBTC - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | True |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### WETH (0x4200000000000000000000000000000000000006)

## WETH - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 800,000,000,000.000000 |
| globalDepositLimit | 8,000,000,000,000.000000 |
| minDepositBalance | 80,000,000.000000 |

## WETH - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

## WETH - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## WETH - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | True |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### 0xaa0f13488CE069A7B5a099457c753A7CFBE04d36 (0xaa0f13488CE069A7B5a099457c753A7CFBE04d36)

## 0xaa0f13488CE069A7B5a099457c753A7CFBE04d36 - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 1 |
| stakersPointsAlloc | 15.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 100,000,000,000,000,000,000.000000 |
| globalDepositLimit | 1,000,000,000,000,000,000,000.000000 |
| minDepositBalance | 10,000,000,000.000000 |

## 0xaa0f13488CE069A7B5a099457c753A7CFBE04d36 - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 0.00% |
| redemptionThreshold | 0.00% |
| liqThreshold | 0.00% |
| liqFee | 0.00% |
| borrowRate | 0.00% |
| daowry | 0.00% |

## 0xaa0f13488CE069A7B5a099457c753A7CFBE04d36 - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | True |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

## 0xaa0f13488CE069A7B5a099457c753A7CFBE04d36 - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | False |
| canRedeemInStabPool | False |
| canBuyInAuction | False |
| canClaimInStabPool | False |
| whitelist | None |
| isNft | False |

#### 0xd6c283655B42FA0eb2685F7AB819784F071459dc (0xd6c283655B42FA0eb2685F7AB819784F071459dc)

## 0xd6c283655B42FA0eb2685F7AB819784F071459dc - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 1 |
| stakersPointsAlloc | 25.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 100,000,000,000,000,000,000.000000 |
| globalDepositLimit | 1,000,000,000,000,000,000,000.000000 |
| minDepositBalance | 10,000,000,000.000000 |

## 0xd6c283655B42FA0eb2685F7AB819784F071459dc - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 0.00% |
| redemptionThreshold | 0.00% |
| liqThreshold | 0.00% |
| liqFee | 0.00% |
| borrowRate | 0.00% |
| daowry | 0.00% |

## 0xd6c283655B42FA0eb2685F7AB819784F071459dc - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

## 0xd6c283655B42FA0eb2685F7AB819784F071459dc - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | False |
| canRedeemInStabPool | False |
| canBuyInAuction | False |
| canClaimInStabPool | False |
| whitelist | None |
| isNft | False |

#### RIPE_TOKEN (0x2A0a59d6B975828e781EcaC125dBA40d7ee5dDC0)

## RIPE_TOKEN - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 2 |
| stakersPointsAlloc | 15.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 100,000,000,000,000,000,000.000000 |
| globalDepositLimit | 1,000,000,000,000,000,000,000.000000 |
| minDepositBalance | 100,000,000.000000 |

## RIPE_TOKEN - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 0.00% |
| redemptionThreshold | 0.00% |
| liqThreshold | 0.00% |
| liqFee | 0.00% |
| borrowRate | 0.00% |
| daowry | 0.00% |

## RIPE_TOKEN - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

## RIPE_TOKEN - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | False |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### 0xF8D92a9531205AB2Dd0Bc623CDF4A6Ab4c3a2526 (0xF8D92a9531205AB2Dd0Bc623CDF4A6Ab4c3a2526)

## 0xF8D92a9531205AB2Dd0Bc623CDF4A6Ab4c3a2526 - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 2 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 100,000,000,000,000,000,000.000000 |
| globalDepositLimit | 1,000,000,000,000,000,000,000.000000 |
| minDepositBalance | 1,000,000,000.000000 |

## 0xF8D92a9531205AB2Dd0Bc623CDF4A6Ab4c3a2526 - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 0.00% |
| redemptionThreshold | 0.00% |
| liqThreshold | 0.00% |
| liqFee | 0.00% |
| borrowRate | 0.00% |
| daowry | 0.00% |

## 0xF8D92a9531205AB2Dd0Bc623CDF4A6Ab4c3a2526 - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

## 0xF8D92a9531205AB2Dd0Bc623CDF4A6Ab4c3a2526 - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | False |
| canWithdraw | False |
| canRedeemCollateral | False |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | `0x2255b0006A3DA38AA184E0F9d5e056C2d0448065` |
| isNft | False |

#### CBDOGE (0xcbD06E5A2B0C65597161de254AA074E489dEb510)

## CBDOGE - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 1,500,000.000000 |
| globalDepositLimit | 15,000,000.000000 |
| minDepositBalance | 150.000000 |

## CBDOGE - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 50.00% |
| redemptionThreshold | 60.00% |
| liqThreshold | 65.00% |
| liqFee | 12.00% |
| borrowRate | 11.00% |
| daowry | 0.25% |

## CBDOGE - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## CBDOGE - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | True |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### USOL (0x9B8Df6E244526ab5F6e6400d331DB28C8fdDdb55)

## USOL - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 15,000,000,000,000.000000 |
| globalDepositLimit | 150,000,000,000,000.000000 |
| minDepositBalance | 1,500,000,000.000000 |

## USOL - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 50.00% |
| redemptionThreshold | 60.00% |
| liqThreshold | 65.00% |
| liqFee | 12.00% |
| borrowRate | 11.00% |
| daowry | 0.25% |

## USOL - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## USOL - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | True |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### RIPE_WETH_POOL (0x765824aD2eD0ECB70ECc25B0Cf285832b335d6A9)

## RIPE_WETH_POOL - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 2 |
| stakersPointsAlloc | 45.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 100,000,000,000,000,000,000.000000 |
| globalDepositLimit | 1,000,000,000,000,000,000,000.000000 |
| minDepositBalance | 1,000,000,000.000000 |

## RIPE_WETH_POOL - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 0.00% |
| redemptionThreshold | 0.00% |
| liqThreshold | 0.00% |
| liqFee | 0.00% |
| borrowRate | 0.00% |
| daowry | 0.00% |

## RIPE_WETH_POOL - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

## RIPE_WETH_POOL - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | False |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### MORPHO_SPARK_USDC (0x7BfA7C4f149E7415b73bdeDfe609237e29CBF34A)

## MORPHO_SPARK_USDC - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 3,000,000,000,000,000.000000 |
| globalDepositLimit | 30,000,000,000,000,000.000000 |
| minDepositBalance | 300,000,000,000.000000 |

## MORPHO_SPARK_USDC - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 80.00% |
| redemptionThreshold | 82.00% |
| liqThreshold | 85.00% |
| liqFee | 5.00% |
| borrowRate | 5.00% |
| daowry | 0.25% |

## MORPHO_SPARK_USDC - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

## MORPHO_SPARK_USDC - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | False |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### AERO (0x940181a94A35A4569E4529A3CDfB74e38FD98631)

## AERO - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 3,000,000,000,000,000.000000 |
| globalDepositLimit | 30,000,000,000,000,000.000000 |
| minDepositBalance | 1,000,000,000,000.000000 |

## AERO - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 50.00% |
| redemptionThreshold | 60.00% |
| liqThreshold | 65.00% |
| liqFee | 10.00% |
| borrowRate | 8.00% |
| daowry | 0.25% |

## AERO - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## AERO - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | True |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### 0x784efeB622244d2348d4F2522f8860B96fbEcE89 (0x784efeB622244d2348d4F2522f8860B96fbEcE89)

## 0x784efeB622244d2348d4F2522f8860B96fbEcE89 - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 4 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 3,000,000,000,000,000.000000 |
| globalDepositLimit | 30,000,000,000,000,000.000000 |
| minDepositBalance | 1,000,000,000,000.000000 |

## 0x784efeB622244d2348d4F2522f8860B96fbEcE89 - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 50.00% |
| redemptionThreshold | 60.00% |
| liqThreshold | 65.00% |
| liqFee | 10.00% |
| borrowRate | 8.00% |
| daowry | 0.25% |

## 0x784efeB622244d2348d4F2522f8860B96fbEcE89 - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## 0x784efeB622244d2348d4F2522f8860B96fbEcE89 - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | True |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### MOONWELL_AERO (0x73902f619CEB9B31FD8EFecf435CbDf89E369Ba6)

## MOONWELL_AERO - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 13,000,000.000000 |
| globalDepositLimit | 130,000,000.000000 |
| minDepositBalance | 1,000.000000 |

## MOONWELL_AERO - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 50.00% |
| redemptionThreshold | 60.00% |
| liqThreshold | 65.00% |
| liqFee | 10.00% |
| borrowRate | 8.00% |
| daowry | 0.25% |

## MOONWELL_AERO - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## MOONWELL_AERO - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | True |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### AAVEV3_USDC (0x4e65fE4DbA92790696d040ac24Aa414708F5c0AB)

## AAVEV3_USDC - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 4 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 3,000.000000 |
| globalDepositLimit | 30,000.000000 |
| minDepositBalance | 1.000000 |

## AAVEV3_USDC - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 80.00% |
| redemptionThreshold | 82.00% |
| liqThreshold | 85.00% |
| liqFee | 5.00% |
| borrowRate | 5.00% |
| daowry | 0.25% |

## AAVEV3_USDC - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

## AAVEV3_USDC - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | False |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### AAVEV3_CBBTC (0xBdb9300b7CDE636d9cD4AFF00f6F009fFBBc8EE6)

## AAVEV3_CBBTC - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 4 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 2.500000 |
| globalDepositLimit | 25.000000 |
| minDepositBalance | 0.000025 |

## AAVEV3_CBBTC - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

## AAVEV3_CBBTC - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## AAVEV3_CBBTC - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | True |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### AAVEV3_WETH (0xD4a0e0b9149BCee3C920d2E00b5dE09138fd8bb7)

## AAVEV3_WETH - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 4 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 800,000,000,000.000000 |
| globalDepositLimit | 8,000,000,000,000.000000 |
| minDepositBalance | 80,000,000.000000 |

## AAVEV3_WETH - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

## AAVEV3_WETH - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## AAVEV3_WETH - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | True |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### VIRTUAL (0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b)

## VIRTUAL - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 2,000,000,000,000,000.000000 |
| globalDepositLimit | 20,000,000,000,000,000.000000 |
| minDepositBalance | 1,000,000,000,000.000000 |

## VIRTUAL - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 50.00% |
| redemptionThreshold | 60.00% |
| liqThreshold | 65.00% |
| liqFee | 12.00% |
| borrowRate | 11.00% |
| daowry | 0.25% |

## VIRTUAL - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## VIRTUAL - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | True |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### 0xcbADA732173e39521CDBE8bf59a6Dc85A9fc7b8c (0xcbADA732173e39521CDBE8bf59a6Dc85A9fc7b8c)

## 0xcbADA732173e39521CDBE8bf59a6Dc85A9fc7b8c - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 3,750.000000 |
| globalDepositLimit | 37,500.000000 |
| minDepositBalance | 1.000000 |

## 0xcbADA732173e39521CDBE8bf59a6Dc85A9fc7b8c - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 50.00% |
| redemptionThreshold | 60.00% |
| liqThreshold | 65.00% |
| liqFee | 12.00% |
| borrowRate | 11.00% |
| daowry | 0.25% |

## 0xcbADA732173e39521CDBE8bf59a6Dc85A9fc7b8c - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## 0xcbADA732173e39521CDBE8bf59a6Dc85A9fc7b8c - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | True |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### 0xcb585250f852C6c6bf90434AB21A00f02833a4af (0xcb585250f852C6c6bf90434AB21A00f02833a4af)

## 0xcb585250f852C6c6bf90434AB21A00f02833a4af - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 1,000.000000 |
| globalDepositLimit | 10,000.000000 |
| minDepositBalance | 0.333333 |

## 0xcb585250f852C6c6bf90434AB21A00f02833a4af - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 50.00% |
| redemptionThreshold | 60.00% |
| liqThreshold | 65.00% |
| liqFee | 12.00% |
| borrowRate | 11.00% |
| daowry | 0.25% |

## 0xcb585250f852C6c6bf90434AB21A00f02833a4af - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## 0xcb585250f852C6c6bf90434AB21A00f02833a4af - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | True |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### 0xcb17C9Db87B595717C857a08468793f5bAb6445F (0xcb17C9Db87B595717C857a08468793f5bAb6445F)

## 0xcb17C9Db87B595717C857a08468793f5bAb6445F - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 2,500.000000 |
| globalDepositLimit | 25,000.000000 |
| minDepositBalance | 0.800000 |

## 0xcb17C9Db87B595717C857a08468793f5bAb6445F - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 50.00% |
| redemptionThreshold | 60.00% |
| liqThreshold | 65.00% |
| liqFee | 12.00% |
| borrowRate | 11.00% |
| daowry | 0.25% |

## 0xcb17C9Db87B595717C857a08468793f5bAb6445F - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## 0xcb17C9Db87B595717C857a08468793f5bAb6445F - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | True |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### 0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf (0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf)

## 0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 1,100,000,000,000,000.000000 |
| globalDepositLimit | 11,000,000,000,000,000.000000 |
| minDepositBalance | 110,000,000,000.000000 |

## 0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 40.00% |
| redemptionThreshold | 45.00% |
| liqThreshold | 50.00% |
| liqFee | 15.00% |
| borrowRate | 13.00% |
| daowry | 0.25% |

## 0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## 0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | True |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### WELL (0xA88594D404727625A9437C3f886C7643872296AE)

## WELL - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 100,000,000,000,000,000.000000 |
| globalDepositLimit | 1,000,000,000,000,000,000.000000 |
| minDepositBalance | 10,000,000,000,000.000000 |

## WELL - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 40.00% |
| redemptionThreshold | 45.00% |
| liqThreshold | 50.00% |
| liqFee | 15.00% |
| borrowRate | 13.00% |
| daowry | 0.25% |

## WELL - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## WELL - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | True |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### 0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed (0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed)

## 0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 750,000,000,000,000,000.000000 |
| globalDepositLimit | 7,500,000,000,000,000,000.000000 |
| minDepositBalance | 75,000,000,000,000.000000 |

## 0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 40.00% |
| redemptionThreshold | 45.00% |
| liqThreshold | 50.00% |
| liqFee | 15.00% |
| borrowRate | 13.00% |
| daowry | 0.25% |

## 0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## 0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | True |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### COMPOUNDV3_WETH (0x46e6b214b524310239732D51387075E0e70970bf)

## COMPOUNDV3_WETH - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 4 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 800,000,000,000.000000 |
| globalDepositLimit | 8,000,000,000,000.000000 |
| minDepositBalance | 80,000,000.000000 |

## COMPOUNDV3_WETH - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

## COMPOUNDV3_WETH - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## COMPOUNDV3_WETH - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | True |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### MORPHO_MOONWELL_WETH (0xa0E430870c4604CcfC7B38Ca7845B1FF653D0ff1)

## MORPHO_MOONWELL_WETH - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 800,000,000,000.000000 |
| globalDepositLimit | 8,000,000,000,000.000000 |
| minDepositBalance | 80,000,000.000000 |

## MORPHO_MOONWELL_WETH - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

## MORPHO_MOONWELL_WETH - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## MORPHO_MOONWELL_WETH - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | True |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### MORPHO_SEAMLESS_WETH (0x27D8c7273fd3fcC6956a0B370cE5Fd4A7fc65c18)

## MORPHO_SEAMLESS_WETH - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 800,000,000,000.000000 |
| globalDepositLimit | 8,000,000,000,000.000000 |
| minDepositBalance | 80,000,000.000000 |

## MORPHO_SEAMLESS_WETH - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

## MORPHO_SEAMLESS_WETH - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## MORPHO_SEAMLESS_WETH - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | True |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### EULER_WETH (0x859160DB5841E5cfB8D3f144C6b3381A85A4b410)

## EULER_WETH - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 800,000,000,000.000000 |
| globalDepositLimit | 8,000,000,000,000.000000 |
| minDepositBalance | 80,000,000.000000 |

## EULER_WETH - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

## EULER_WETH - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## EULER_WETH - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | True |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### CBETH (0x2Ae3F1Ec7F1F5012CFEab0185bfc7aa3cf0DEc22)

## CBETH - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 800,000,000,000.000000 |
| globalDepositLimit | 8,000,000,000,000.000000 |
| minDepositBalance | 80,000,000.000000 |

## CBETH - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

## CBETH - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## CBETH - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | True |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### MOONWELL_CBETH (0x3bf93770f2d4a794c3d9EBEfBAeBAE2a8f09A5E5)

## MOONWELL_CBETH - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 3,300.000000 |
| globalDepositLimit | 33,000.000000 |
| minDepositBalance | 0.330000 |

## MOONWELL_CBETH - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

## MOONWELL_CBETH - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## MOONWELL_CBETH - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | True |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### COMPOUNDV3_USDC (0xb125E6687d4313864e53df431d5425969c15Eb2F)

## COMPOUNDV3_USDC - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 4 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 6,000.000000 |
| globalDepositLimit | 60,000.000000 |
| minDepositBalance | 0.010000 |

## COMPOUNDV3_USDC - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 80.00% |
| redemptionThreshold | 85.00% |
| liqThreshold | 90.00% |
| liqFee | 5.00% |
| borrowRate | 5.00% |
| daowry | 0.25% |

## COMPOUNDV3_USDC - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

## COMPOUNDV3_USDC - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | False |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### MOONWELL_USDC (0xEdc817A28E8B93B03976FBd4a3dDBc9f7D176c22)

## MOONWELL_USDC - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 27,500,000.000000 |
| globalDepositLimit | 275,000,000.000000 |
| minDepositBalance | 45.600000 |

## MOONWELL_USDC - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 80.00% |
| redemptionThreshold | 85.00% |
| liqThreshold | 90.00% |
| liqFee | 5.00% |
| borrowRate | 5.00% |
| daowry | 0.25% |

## MOONWELL_USDC - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

## MOONWELL_USDC - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | False |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### EULER_USDC (0x0A1a3b5f2041F33522C4efc754a7D096f880eE16)

## EULER_USDC - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 6,000.000000 |
| globalDepositLimit | 60,000.000000 |
| minDepositBalance | 0.010000 |

## EULER_USDC - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 80.00% |
| redemptionThreshold | 85.00% |
| liqThreshold | 90.00% |
| liqFee | 5.00% |
| borrowRate | 5.00% |
| daowry | 0.25% |

## EULER_USDC - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

## EULER_USDC - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | False |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### FLUID_USDC (0xf42f5795D9ac7e9D757dB633D693cD548Cfd9169)

## FLUID_USDC - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 6,000.000000 |
| globalDepositLimit | 60,000.000000 |
| minDepositBalance | 0.010000 |

## FLUID_USDC - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 80.00% |
| redemptionThreshold | 85.00% |
| liqThreshold | 90.00% |
| liqFee | 5.00% |
| borrowRate | 5.00% |
| daowry | 0.25% |

## FLUID_USDC - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

## FLUID_USDC - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | False |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### MORPHO_MOONWELL_USDC (0xc1256Ae5FF1cf2719D4937adb3bbCCab2E00A2Ca)

## MORPHO_MOONWELL_USDC - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 6,000,000,000,000,000.000000 |
| globalDepositLimit | 60,000,000,000,000,000.000000 |
| minDepositBalance | 10,000,000,000.000000 |

## MORPHO_MOONWELL_USDC - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 80.00% |
| redemptionThreshold | 85.00% |
| liqThreshold | 90.00% |
| liqFee | 5.00% |
| borrowRate | 5.00% |
| daowry | 0.25% |

## MORPHO_MOONWELL_USDC - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

## MORPHO_MOONWELL_USDC - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | False |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### MORPHO_SEAMLESS_USDC (0x616a4E1db48e22028f6bbf20444Cd3b8e3273738)

## MORPHO_SEAMLESS_USDC - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 6,000,000,000,000,000.000000 |
| globalDepositLimit | 60,000,000,000,000,000.000000 |
| minDepositBalance | 10,000,000,000.000000 |

## MORPHO_SEAMLESS_USDC - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 80.00% |
| redemptionThreshold | 85.00% |
| liqThreshold | 90.00% |
| liqFee | 5.00% |
| borrowRate | 5.00% |
| daowry | 0.25% |

## MORPHO_SEAMLESS_USDC - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

## MORPHO_SEAMLESS_USDC - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | False |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### EULER_CBBTC (0x882018411Bc4A020A879CEE183441fC9fa5D7f8B)

## EULER_CBBTC - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 5.000000 |
| globalDepositLimit | 50.000000 |
| minDepositBalance | 0.000025 |

## EULER_CBBTC - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

## EULER_CBBTC - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## EULER_CBBTC - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | True |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### MOONWELL_CBBTC (0xF877ACaFA28c19b96727966690b2f44d35aD5976)

## MOONWELL_CBBTC - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 266.000000 |
| globalDepositLimit | 2,660.000000 |
| minDepositBalance | 0.000443 |

## MOONWELL_CBBTC - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

## MOONWELL_CBBTC - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## MOONWELL_CBBTC - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | True |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### MORPHO_MOONWELL_CBBTC (0x543257eF2161176D7C8cD90BA65C2d4CaEF5a796)

## MORPHO_MOONWELL_CBBTC - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 50,000,000,000.000000 |
| globalDepositLimit | 500,000,000,000.000000 |
| minDepositBalance | 2,500,000.000000 |

## MORPHO_MOONWELL_CBBTC - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

## MORPHO_MOONWELL_CBBTC - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## MORPHO_MOONWELL_CBBTC - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | True |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### 0x211Cc4DD073734dA055fbF44a2b4667d5E5fE5d2 (0x211Cc4DD073734dA055fbF44a2b4667d5E5fE5d2)

## 0x211Cc4DD073734dA055fbF44a2b4667d5E5fE5d2 - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 6,000,000,000,000,000.000000 |
| globalDepositLimit | 60,000,000,000,000,000.000000 |
| minDepositBalance | 10,000,000,000.000000 |

## 0x211Cc4DD073734dA055fbF44a2b4667d5E5fE5d2 - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 80.00% |
| redemptionThreshold | 85.00% |
| liqThreshold | 90.00% |
| liqFee | 5.00% |
| borrowRate | 5.00% |
| daowry | 0.25% |

## 0x211Cc4DD073734dA055fbF44a2b4667d5E5fE5d2 - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

## 0x211Cc4DD073734dA055fbF44a2b4667d5E5fE5d2 - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | False |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### WRAPPED_SUPER_OETH (0x7FcD174E80f264448ebeE8c88a7C4476AAF58Ea6)

## WRAPPED_SUPER_OETH - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 1,600,000,000,000.000000 |
| globalDepositLimit | 16,000,000,000,000.000000 |
| minDepositBalance | 80,000,000.000000 |

## WRAPPED_SUPER_OETH - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

## WRAPPED_SUPER_OETH - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## WRAPPED_SUPER_OETH - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | True |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### 0xd1Eac76497D06Cf15475A5e3984D5bC03de7C707 (0xd1Eac76497D06Cf15475A5e3984D5bC03de7C707)

## 0xd1Eac76497D06Cf15475A5e3984D5bC03de7C707 - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | None |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 0.000001 |
| globalDepositLimit | 0.000002 |
| minDepositBalance | 0.000001 |

## 0xd1Eac76497D06Cf15475A5e3984D5bC03de7C707 - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 0.00% |
| redemptionThreshold | 0.00% |
| liqThreshold | 0.00% |
| liqFee | 0.00% |
| borrowRate | 0.00% |
| daowry | 0.00% |

## 0xd1Eac76497D06Cf15475A5e3984D5bC03de7C707 - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

## 0xd1Eac76497D06Cf15475A5e3984D5bC03de7C707 - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | False |
| canWithdraw | False |
| canRedeemCollateral | False |
| canRedeemInStabPool | False |
| canBuyInAuction | False |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### UNDY_USD (0xcF9F72237d4135a6D8b3ee717DC414Ae5b56E41e)

## UNDY_USD - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 5 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 100.000000 |
| globalDepositLimit | 1,000.000000 |
| minDepositBalance | 0.100000 |

## UNDY_USD - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 80.00% |
| redemptionThreshold | 85.00% |
| liqThreshold | 90.00% |
| liqFee | 5.00% |
| borrowRate | 5.00% |
| daowry | 0.25% |

## UNDY_USD - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

## UNDY_USD - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | False |
| canWithdraw | True |
| canRedeemCollateral | False |
| canRedeemInStabPool | False |
| canBuyInAuction | False |
| canClaimInStabPool | False |
| whitelist | None |
| isNft | False |

#### UNDY_ETH (0x01ECc16CE82CCf7e6f734351d5d3AdCf2f8D3497)

## UNDY_ETH - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 5 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 25,000,000,000.000000 |
| globalDepositLimit | 250,000,000,000.000000 |
| minDepositBalance | 25,000,000.000000 |

## UNDY_ETH - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

## UNDY_ETH - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## UNDY_ETH - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | False |
| canWithdraw | True |
| canRedeemCollateral | True |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### UNDY_BTC (0x4cD99832E44D1154bd7841f5E5E9ce66dA0437d4)

## UNDY_BTC - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 5 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 0.100000 |
| globalDepositLimit | 1.000000 |
| minDepositBalance | 0.000100 |

## UNDY_BTC - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

## UNDY_BTC - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## UNDY_BTC - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | False |
| canWithdraw | True |
| canRedeemCollateral | True |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### 0xcdD894E6c11d6444e0c3d974928Dd71b28b09356 (0xcdD894E6c11d6444e0c3d974928Dd71b28b09356)

## 0xcdD894E6c11d6444e0c3d974928Dd71b28b09356 - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 5 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 50,000.000000 |
| globalDepositLimit | 250,000.000000 |
| minDepositBalance | 0.100000 |

## 0xcdD894E6c11d6444e0c3d974928Dd71b28b09356 - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 80.00% |
| redemptionThreshold | 85.00% |
| liqThreshold | 90.00% |
| liqFee | 5.00% |
| borrowRate | 5.00% |
| daowry | 0.25% |

## 0xcdD894E6c11d6444e0c3d974928Dd71b28b09356 - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

## 0xcdD894E6c11d6444e0c3d974928Dd71b28b09356 - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | False |
| canWithdraw | True |
| canRedeemCollateral | False |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### 0x434696F22EF3862f14C6Abd008f18456418f7457 (0x434696F22EF3862f14C6Abd008f18456418f7457)

## 0x434696F22EF3862f14C6Abd008f18456418f7457 - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 5 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 250,000,000,000.000000 |
| globalDepositLimit | 2,500,000,000,000.000000 |
| minDepositBalance | 25,000,000.000000 |

## 0x434696F22EF3862f14C6Abd008f18456418f7457 - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

## 0x434696F22EF3862f14C6Abd008f18456418f7457 - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## 0x434696F22EF3862f14C6Abd008f18456418f7457 - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | False |
| canWithdraw | True |
| canRedeemCollateral | True |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### 0x897b56836C79e68042EFc51be7ad652a4BBFb86b (0x897b56836C79e68042EFc51be7ad652a4BBFb86b)

## 0x897b56836C79e68042EFc51be7ad652a4BBFb86b - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 5 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 1.000000 |
| globalDepositLimit | 10.000000 |
| minDepositBalance | 0.000100 |

## 0x897b56836C79e68042EFc51be7ad652a4BBFb86b - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

## 0x897b56836C79e68042EFc51be7ad652a4BBFb86b - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## 0x897b56836C79e68042EFc51be7ad652a4BBFb86b - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | False |
| canWithdraw | True |
| canRedeemCollateral | True |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### 0x9e629632c483235845E27840C304C11b59d2FEDa (0x9e629632c483235845E27840C304C11b59d2FEDa)

## 0x9e629632c483235845E27840C304C11b59d2FEDa - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 5 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 100,000,000,000,000.000000 |
| globalDepositLimit | 1,000,000,000,000,000.000000 |
| minDepositBalance | 100,000,000,000.000000 |

## 0x9e629632c483235845E27840C304C11b59d2FEDa - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 50.00% |
| redemptionThreshold | 60.00% |
| liqThreshold | 65.00% |
| liqFee | 12.00% |
| borrowRate | 8.00% |
| daowry | 0.25% |

## 0x9e629632c483235845E27840C304C11b59d2FEDa - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## 0x9e629632c483235845E27840C304C11b59d2FEDa - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | False |
| canWithdraw | True |
| canRedeemCollateral | True |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### 0x4bCa2A052428D7b7D2E1Daf9e1af471EA4c2F7bf (0x4bCa2A052428D7b7D2E1Daf9e1af471EA4c2F7bf)

## 0x4bCa2A052428D7b7D2E1Daf9e1af471EA4c2F7bf - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 5 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 100.000000 |
| globalDepositLimit | 1,000.000000 |
| minDepositBalance | 0.100000 |

## 0x4bCa2A052428D7b7D2E1Daf9e1af471EA4c2F7bf - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 80.00% |
| redemptionThreshold | 85.00% |
| liqThreshold | 90.00% |
| liqFee | 5.00% |
| borrowRate | 5.00% |
| daowry | 0.25% |

## 0x4bCa2A052428D7b7D2E1Daf9e1af471EA4c2F7bf - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

## 0x4bCa2A052428D7b7D2E1Daf9e1af471EA4c2F7bf - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | False |
| canWithdraw | True |
| canRedeemCollateral | False |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### 0x02981DB1a99A14912b204437e7a2E02679B57668 (0x02981DB1a99A14912b204437e7a2E02679B57668)

## 0x02981DB1a99A14912b204437e7a2E02679B57668 - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 5 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 250,000,000,000.000000 |
| globalDepositLimit | 2,500,000,000,000.000000 |
| minDepositBalance | 25,000,000.000000 |

## 0x02981DB1a99A14912b204437e7a2E02679B57668 - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

## 0x02981DB1a99A14912b204437e7a2E02679B57668 - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## 0x02981DB1a99A14912b204437e7a2E02679B57668 - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | True |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### 0x3fb0fC9D3Ddd543AD1b748Ed2286a022f4638493 (0x3fb0fC9D3Ddd543AD1b748Ed2286a022f4638493)

## 0x3fb0fC9D3Ddd543AD1b748Ed2286a022f4638493 - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 5 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 1.000000 |
| globalDepositLimit | 10.000000 |
| minDepositBalance | 0.000100 |

## 0x3fb0fC9D3Ddd543AD1b748Ed2286a022f4638493 - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

## 0x3fb0fC9D3Ddd543AD1b748Ed2286a022f4638493 - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## 0x3fb0fC9D3Ddd543AD1b748Ed2286a022f4638493 - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | True |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### 0xb33852cfd0c22647AAC501a6Af59Bc4210a686Bf (0xb33852cfd0c22647AAC501a6Af59Bc4210a686Bf)

## 0xb33852cfd0c22647AAC501a6Af59Bc4210a686Bf - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 5 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 50,000.000000 |
| globalDepositLimit | 250,000.000000 |
| minDepositBalance | 0.100000 |

## 0xb33852cfd0c22647AAC501a6Af59Bc4210a686Bf - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 80.00% |
| redemptionThreshold | 85.00% |
| liqThreshold | 90.00% |
| liqFee | 5.00% |
| borrowRate | 5.00% |
| daowry | 0.25% |

## 0xb33852cfd0c22647AAC501a6Af59Bc4210a686Bf - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

## 0xb33852cfd0c22647AAC501a6Af59Bc4210a686Bf - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | False |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### 0x96F1a7ce331F40afe866F3b707c223e377661087 (0x96F1a7ce331F40afe866F3b707c223e377661087)

## 0x96F1a7ce331F40afe866F3b707c223e377661087 - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 5 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 1,000,000,000,000,000.000000 |
| globalDepositLimit | 10,000,000,000,000,000.000000 |
| minDepositBalance | 100,000,000,000.000000 |

## 0x96F1a7ce331F40afe866F3b707c223e377661087 - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 50.00% |
| redemptionThreshold | 60.00% |
| liqThreshold | 65.00% |
| liqFee | 12.00% |
| borrowRate | 8.00% |
| daowry | 0.25% |

## 0x96F1a7ce331F40afe866F3b707c223e377661087 - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## 0x96F1a7ce331F40afe866F3b707c223e377661087 - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | True |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

#### 0x1cb8DAB80f19fC5Aca06C2552AECd79015008eA8 (0x1cb8DAB80f19fC5Aca06C2552AECd79015008eA8)

## 0x1cb8DAB80f19fC5Aca06C2552AECd79015008eA8 - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 5 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 1,000.000000 |
| globalDepositLimit | 10,000.000000 |
| minDepositBalance | 0.100000 |

## 0x1cb8DAB80f19fC5Aca06C2552AECd79015008eA8 - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 80.00% |
| redemptionThreshold | 85.00% |
| liqThreshold | 90.00% |
| liqFee | 5.00% |
| borrowRate | 5.00% |
| daowry | 0.25% |

## 0x1cb8DAB80f19fC5Aca06C2552AECd79015008eA8 - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

## 0x1cb8DAB80f19fC5Aca06C2552AECd79015008eA8 - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | True |
| canWithdraw | True |
| canRedeemCollateral | False |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | None |
| isNft | False |

================================================================================

<a id="ripe-hq"></a>
# RipeHQ - Main Registry & Minting Config
Address: 0x6162df1b329E157479F8f1407E888260E0EC3d2b

## Minting Circuit Breaker
| Parameter | Value |
| --- | --- |
| mintEnabled | True |

## Core Token Registry
| Token | Address |
| --- | --- |
| greenToken (ID 1) | `0xd1Eac76497D06Cf15475A5e3984D5bC03de7C707` |
| savingsGreen (ID 2) | `0xaa0f13488CE069A7B5a099457c753A7CFBE04d36` |
| ripeToken (ID 3) | RIPE_TOKEN (`0x2A0a59d6B975828e781EcaC125dBA40d7ee5dDC0`) |

## Registry Config
| Parameter | Value |
| --- | --- |
| numAddrs | 23 |
| registryChangeTimeLock | 21600 blocks (~12.0h) |

### All Registered Contracts
| ID | Description | Address | Mint GREEN | Mint RIPE | Blacklist | Paused |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Green Token | `0xd1Eac76497D06Cf15475A5e3984D5bC03de7C707` | - | - | - | False |
| 2 | Savings Green | `0xaa0f13488CE069A7B5a099457c753A7CFBE04d36` | - | - | - | False |
| 3 | Ripe Token | RIPE_TOKEN (`0x2A0a59d6B975828e781EcaC125dBA40d7ee5dDC0`) | - | - | - | False |
| 4 | Ledger | `0x365256e322a47Aa2015F6724783F326e9B24fA47` | - | - | - | False |
| 5 | Mission Control | `0xB59b84B526547b6dcb86CCF4004d48E619156CF3` | - | - | - | False |
| 6 | Switchboard | `0xc68A90A40B87ae1dABA93Da9c02642F8B74030F9` | - | - | ✓ | False |
| 7 | Price Desk | `0x68564c6035e8Dc21F0Ce6CB9592dC47B59dE2Ff6` | - | - | - | False |
| 8 | Vault Book | `0xB758e30C14825519b895Fd9928d5d8748A71a944` | - | ✓ | - | False |
| 9 | Auction House | `0x8a02aC4754b72aFBDa4f403ec5DA7C2950164084` | ✓ | - | - | False |
| 10 | Auction House NFT | `0x504Fb3b94a9f4A238Ee3A16474B91F99A3f26F3A` | - | - | - | False |
| 11 | Boardroom | `0xb5cA6Ef866b510C3b85D4B0e3862061A569412D1` | - | - | - | False |
| 12 | Bond Room | `0x707f660A7834d00792DF9a28386Bb2cCC6446154` | - | ✓ | - | False |
| 13 | Credit Engine | `0x30aa8eB041AcB3B22228516297C331B313b81462` | ✓ | - | - | False |
| 14 | Endaoment | `0x70fA85Aa99a39161A2623627377F1c791fd091f6` | ✓ | - | - | False |
| 15 | Human Resources | `0xF9aCDFd0d167b741f9144Ca01E52FcdE16BE108b` | - | ✓ | - | False |
| 16 | Lootbox | `0x1f90ef42Da9B41502d2311300E13FAcf70c64be7` | - | ✓ | - | False |
| 17 | Teller | `0xae87deB25Bc5030991Aa5E27Cbab38f37a112C13` | - | - | - | False |
| 18 | Deleverage | `0x75EeBb8c6f1A5727e7c0c1f9d64Ed07cd0966F27` | - | - | - | False |
| 19 | Credit Redeem | `0x3bfB0F72642aeFA2486da00Db855c5F0b787e3FB` | - | - | - | False |
| 20 | Teller Utils | `0x57f071AB96D1798C6bB3e314D2D283502DEDDcdD` | - | - | - | False |
| 21 | Endaoment Funds | `0x4Ce5FB8D572917Eb96724eA1866b505B2a6B0873` | - | - | - | - |
| 22 | Endaoment PSM | `0x2893d0dfa54571bDc7DE60F2d8a456d3377CcAA7` | - | - | - | False |

================================================================================

<a id="switchboard"></a>
# Switchboard - Configuration Contracts Registry
Address: 0xc68A90A40B87ae1dABA93Da9c02642F8B74030F9

## Registry Config
| Parameter | Value |
| --- | --- |
| numAddrs (switchboards) | 5 |
| registryChangeTimeLock | 21600 blocks (~12.0h) |

### Registered Switchboards
| ID | Description | Address | Paused |
| --- | --- | --- | --- |
| 1 | Switchboard Alpha | `0x73Cd87A047eb16E22f8afA21e0980C07Bb26CA83` | - |
| 2 | Switchboard Bravo | `0xD18AC028cBe1AbebDb118E9C7A60018d58C846e7` | - |
| 3 | Switchboard Charlie | `0x6D798bD44b1591571c9d95b6D51c9c34a5534008` | - |
| 4 | Switchboard Delta | `0x50e815AC356798E42EB35De538a0376459ce11cb` | - |
| 5 | Switchboard Echo | `0xdF99a86e4450163e8DbA47C928131e75D2995dbb` | - |

================================================================================

<a id="price-desk"></a>
# PriceDesk - Oracle Registry
Address: 0x68564c6035e8Dc21F0Ce6CB9592dC47B59dE2Ff6

## Constants
| Parameter | Value |
| --- | --- |
| ETH | ETH (`0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE`) |

## Registry Config
| Parameter | Value |
| --- | --- |
| numAddrs (price sources) | 8 |
| registryChangeTimeLock | 0 blocks (~0s) |

### Registered Price Sources
| Reg ID | Description | Address |
| --- | --- | --- |
| 1 | Chainlink | `0x253f55e455701fF0B835128f55668ed159aAB3D9` |
| 2 | Curve Prices | `0x7B2aeE8B6A4bdF0885dEF48CCda8453Fdc1Bba5d` |
| 3 | BlueChip Yield Prices | `0x90C70ACfF302c8a7f00574EC3547B0221f39cD28` |
| 4 | Pyth Prices | `0x89b6E13E4aD4036EAA586219DD73Ebb2b36d5968` |
| 5 | Stork Prices | `0xCa13ACFB607B842DF5c1D0657C0865cC47bEfe14` |
| 6 | Aero Ripe Prices | `0x5ce2BbD5eBe9f7d9322a8F56740F95b9576eE0A2` |
| 7 | wsuperOETHb Prices | `0x2606Ce36b62a77562DF664E7a0009805BB254F3f` |
| 8 | Undy Vault Prices | `0x2210a9b994CC0F13689043A34F2E11d17DB2099C` |

================================================================================

<a id="vault-book"></a>
# VaultBook - Vault Registry
Address: 0xB758e30C14825519b895Fd9928d5d8748A71a944

## Registry Config
| Parameter | Value |
| --- | --- |
| numAddrs (vaults) | 5 |
| registryChangeTimeLock | 21600 blocks (~12.0h) |

### Vault 1: Stability Pool
Address: 0x2a157096af6337b2b4bd47de435520572ed5a439

## Vault Status
| Parameter | Value |
| --- | --- |
| isPaused | False |
| numAssets | 2 |

**Assets in Vault (2):**
| Asset | Total Balance |
| --- | --- |
| 0xaa0f13488CE069A7B5a099457c753A7CFBE04d36 | Very High (5.41e+12 ) |
| 0xd6c283655B42FA0eb2685F7AB819784F071459dc | Very High (5.87e+12 ) |

### Vault 2: Ripe Gov Vault
Address: 0xe42b3dC546527EB70D741B185Dc57226cA01839D

## Vault Status
| Parameter | Value |
| --- | --- |
| isPaused | False |
| numAssets | 3 |

**Assets in Vault (3):**
| Asset | Total Balance |
| --- | --- |
| RIPE_TOKEN | Very High (1.99e+13 ) |
| 0xF8D92a9531205AB2Dd0Bc623CDF4A6Ab4c3a2526 | 0.00  |
| RIPE_WETH_POOL | 22.83B  |

### Vault 3: Simple ERC20 Vault
Address: 0xf75b566eF80Fde0dEfcC045A4d57b540eb43ddfD

## Vault Status
| Parameter | Value |
| --- | --- |
| isPaused | False |
| numAssets | 27 |

**Assets in Vault (27):**
| Asset | Total Balance |
| --- | --- |
| USDC | 762.51  |
| CBBTC | 0.02  |
| WETH | 1.57  |
| CBDOGE | 285.30  |
| USOL | 1.70  |
| MORPHO_SPARK_USDC | 7.14K  |
| AERO | 1.70K  |
| MOONWELL_AERO | 0.00  |
| 0xcb585250f852C6c6bf90434AB21A00f02833a4af | 0.00  |
| WELL | 11.99K  |
| VIRTUAL | 1.11K  |
| 0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf | 295.05  |
| 0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed | 145.66K  |
| MOONWELL_CBETH | 0.00  |
| CBETH | 0.80  |
| MOONWELL_USDC | 45.58  |
| MORPHO_MOONWELL_USDC | 0.00  |
| MORPHO_SEAMLESS_USDC | 5.83K  |
| FLUID_USDC | 5.88K  |
| EULER_USDC | 0.00  |
| MOONWELL_CBBTC | 0.00  |
| MORPHO_MOONWELL_WETH | 0.00  |
| MORPHO_SEAMLESS_WETH | 0.13  |
| EULER_WETH | 0.00  |
| MORPHO_MOONWELL_CBBTC | 0.00  |
| 0x211Cc4DD073734dA055fbF44a2b4667d5E5fE5d2 | 0.83  |
| WRAPPED_SUPER_OETH | 0.37  |

### Vault 4: Rebase ERC20 Vault
Address: 0xce2E96C9F6806731914A7b4c3E4aC1F296d98597

## Vault Status
| Parameter | Value |
| --- | --- |
| isPaused | False |
| numAssets | 6 |

**Assets in Vault (6):**
| Asset | Total Balance |
| --- | --- |
| 0x784efeB622244d2348d4F2522f8860B96fbEcE89 | 0.00  |
| AAVEV3_CBBTC | 452.60  |
| AAVEV3_USDC | 520.27B  |
| AAVEV3_WETH | 86.29M  |
| COMPOUNDV3_USDC | 0.00  |
| COMPOUNDV3_WETH | 0.00  |

### Vault 5: Underscore Vault
Address: 0x4549A368c00f803862d457C4C0c659a293F26C66

## Vault Status
| Parameter | Value |
| --- | --- |
| isPaused | False |
| numAssets | 8 |

**Assets in Vault (8):**
| Asset | Total Balance |
| --- | --- |
| UNDY_USD | 0.00  |
| UNDY_ETH | 0.00  |
| UNDY_BTC | 0.00  |
| 0xcdD894E6c11d6444e0c3d974928Dd71b28b09356 | 0.00  |
| 0xb33852cfd0c22647AAC501a6Af59Bc4210a686Bf | 103.07K  |
| 0x3fb0fC9D3Ddd543AD1b748Ed2286a022f4638493 | 0.00  |
| 0x02981DB1a99A14912b204437e7a2E02679B57668 | 0.01  |
| 0x96F1a7ce331F40afe866F3b707c223e377661087 | 16.66  |

================================================================================

<a id="ledger"></a>
# Ledger - Core Protocol Data
Address: 0x365256e322a47Aa2015F6724783F326e9B24fA47

## Debt Statistics
| Parameter | Value |
| --- | --- |
| totalDebt | 74.39K GREEN |
| numBorrowers | 78 |
| unrealizedYield | 0.27 GREEN |

## RIPE Rewards Pool
| Parameter | Value |
| --- | --- |
| borrowers allocation | 413.73 RIPE |
| stakers allocation | 6.02K RIPE |
| voters allocation | 0.00 RIPE |
| genDepositors allocation | 0.00 RIPE |
| newRipeRewards | 0.00 RIPE |
| lastUpdate (block) | 38879399 |
| ripeAvailForRewards | 12.94K RIPE |

## Global Deposit Points
| Parameter | Value |
| --- | --- |
| lastUsdValue | $0.15 |
| ripeStakerPoints | 14642957784 |
| ripeVotePoints | 0 |
| ripeGenPoints | 963753209294 |
| lastUpdate (block) | 38862405 |

## Global Borrow Points
| Parameter | Value |
| --- | --- |
| lastPrincipal | 0.00 GREEN |
| points | 91195132495 |
| lastUpdate (block) | 38879399 |

## Liquidation Statistics
| Parameter | Value |
| --- | --- |
| numFungLiqUsers (active liquidations) | 0 |

## Human Resources
| Parameter | Value |
| --- | --- |
| ripeAvailForHr | 800.00 RIPE |
| numContributors | 2 |

## Bond Epoch Data
| Parameter | Value |
| --- | --- |
| epochStart (block) | 34376384 |
| epochEnd (block) | 34390784 |
| badDebt | 0.00 GREEN |
| ripePaidOutForBadDebt | 0.00 RIPE |
| paymentAmountAvailInEpoch | 0.00 GREEN |
| ripeAvailForBonds | 288.56K RIPE |

## Endaoment Pool Debt
| Parameter | Value |
| --- | --- |
| greenPoolDebt (GREEN Pool) | 123.18K GREEN |

================================================================================

<a id="endaoment-psm"></a>
# Endaoment PSM - Peg Stability Module
Address: 0x2893d0dfa54571bDc7DE60F2d8a456d3377CcAA7

## PSM Mint Configuration
| Parameter | Value |
| --- | --- |
| canMint | ❌ Disabled |
| mintFee | 0.00% |
| maxIntervalMint | 100.00K GREEN |
| shouldEnforceMintAllowlist | False |

## PSM Redeem Configuration
| Parameter | Value |
| --- | --- |
| canRedeem | ❌ Disabled |
| redeemFee | 0.00% |
| maxIntervalRedeem | 100.00K GREEN |
| shouldEnforceRedeemAllowlist | False |

## PSM Interval & Yield Configuration
| Parameter | Value |
| --- | --- |
| numBlocksPerInterval | 43200 blocks (~1.0d) |
| shouldAutoDeposit | True |
| usdcYieldPosition.legoId | 13 |
| usdcYieldPosition.vaultToken | `0xb33852cfd0c22647AAC501a6Af59Bc4210a686Bf` |

## PSM Current Interval Stats
| Parameter | Value |
| --- | --- |
| Mint Interval Start | 0 |
| Mint Interval Amount | 0.00 GREEN |
| Redeem Interval Start | 0 |
| Redeem Interval Amount | 0.00 GREEN |

**USDC Address:** USDC (`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`)

================================================================================

<a id="core-lending"></a>
# Core Lending Contracts

================================================================================

<a id="credit-engine"></a>
# CreditEngine - Credit Configuration
Address: 0x30aa8eB041AcB3B22228516297C331B313b81462

## Credit Engine Config
| Parameter | Value |
| --- | --- |
| undyVaultDiscount | 50.00% |
| buybackRatio | 0.00% |

================================================================================

<a id="auction-house"></a>
# Auction House - Liquidation Auctions
Address: 0x8a02aC4754b72aFBDa4f403ec5DA7C2950164084

## Auction House Status
| Parameter | Value |
| --- | --- |
| isPaused | False |

================================================================================

<a id="teller"></a>
# Teller - User Interaction Gateway
Address: 0xae87deB25Bc5030991Aa5E27Cbab38f37a112C13

## Teller Status
| Parameter | Value |
| --- | --- |
| isPaused | False |

================================================================================

<a id="deleverage"></a>
# Deleverage - Deleverage Engine
Address: 0x75EeBb8c6f1A5727e7c0c1f9d64Ed07cd0966F27

## Deleverage Status
| Parameter | Value |
| --- | --- |
| isPaused | False |

================================================================================

<a id="credit-redeem"></a>
# Credit Redeem - Redemptions Engine
Address: 0x3bfB0F72642aeFA2486da00Db855c5F0b787e3FB

## Credit Redeem Status
| Parameter | Value |
| --- | --- |
| isPaused | False |

================================================================================

<a id="stability-pool"></a>
# Stability Pool - Liquidation Buffer
Address: 0x2a157096af6337b2b4bd47de435520572ed5a439

## Stability Pool Config
| Parameter | Value |
| --- | --- |
| isPaused | False |
| numAssets | 2 |

================================================================================

<a id="treasury-rewards"></a>
# Treasury & Rewards Contracts

================================================================================

<a id="endaoment"></a>
# Endaoment - Treasury & GREEN Stabilization
Address: 0x70fA85Aa99a39161A2623627377F1c791fd091f6

## Endaoment Status
| Parameter | Value |
| --- | --- |
| isPaused | False |
| WETH | WETH (`0x4200000000000000000000000000000000000006`) |

================================================================================

<a id="bond-booster"></a>
# BondBooster - Bond Boost Configuration
Address: 0xA1872467AC4fb442aeA341163A65263915ce178a

## Bond Booster Global Config
| Parameter | Value |
| --- | --- |
| maxBoostRatio | 200.00% |
| maxUnits | 25000 |
| minLockDuration | 7776000 blocks (~180.0d) |

================================================================================

<a id="lootbox"></a>
# Lootbox - RIPE Rewards & Underscore Config
Address: 0x1f90ef42Da9B41502d2311300E13FAcf70c64be7

## Underscore Rewards Config
| Parameter | Value |
| --- | --- |
| hasUnderscoreRewards | True |
| underscoreSendInterval | 43200 blocks (~1.0d) |
| lastUnderscoreSend (block) | 0 |
| undyDepositRewardsAmount | 100.00 RIPE |
| undyYieldBonusAmount | 100.00 RIPE |

================================================================================

<a id="bond-room"></a>
# BondRoom - Bond Purchase Configuration
Address: 0x707f660A7834d00792DF9a28386Bb2cCC6446154

## Bond Room Config
| Parameter | Value |
| --- | --- |
| isPaused | False |
| bondBooster | `0xA1872467AC4fb442aeA341163A65263915ce178a` |

================================================================================

<a id="human-resources"></a>
# Human Resources - Contributor Management
Address: 0xF9aCDFd0d167b741f9144Ca01E52FcdE16BE108b

## Human Resources Status
| Parameter | Value |
| --- | --- |
| isPaused | False |

*Note: numContributors is tracked in Ledger contract*

================================================================================

<a id="governance"></a>
# Governance Contracts

================================================================================

<a id="ripe-gov-vault"></a>
# Ripe Gov Vault - Governance Staking
Address: 0xe42b3dC546527EB70D741B185Dc57226cA01839D

## Governance Vault Stats
| Parameter | Value |
| --- | --- |
| isPaused | False |
| totalGovPoints | 102,522,757,469,984,937,255 |

================================================================================

<a id="price-sources"></a>
# Price Source Configurations

## Chainlink
Address: 0x253f55e455701fF0B835128f55668ed159aAB3D9

## Chainlink Global Config
| Parameter | Value |
| --- | --- |
| isPaused | False |
| numAssets | 23 |

### Chainlink - Registered Assets (23)
| Asset | Feed/Underlying | Config | StaleTime |
| --- | --- | --- | --- |
| ETH | CHAINLINK_ETH_USD (`0x71041dddad3595F9CEd3DcCFBe3D1F4b0a16Bb70`) | ETH:False, BTC:False | default |
| WETH | CHAINLINK_ETH_USD (`0x71041dddad3595F9CEd3DcCFBe3D1F4b0a16Bb70`) | ETH:False, BTC:False | default |
| BTC | CHAINLINK_BTC_USD (`0x64c911996D3c6aC71f9b455B1E8E7266BcbD848F`) | ETH:False, BTC:False | default |
| USDC | CHAINLINK_USDC_USD (`0x7e860098F58bBFC8648a4311b374B1D669a2bc6B`) | ETH:False, BTC:False | default |
| CBBTC | CHAINLINK_CBBTC_USD (`0x07DA0E54543a844a80ABE69c8A12F22B3aA59f9D`) | ETH:False, BTC:False | default |
| USOL | CHAINLINK_SOL_USD (`0x975043adBb80fc32276CbF9Bbcfd4A601a12462D`) | ETH:False, BTC:False | default |
| CBDOGE | CHAINLINK_DOGE_USD (`0x8422f3d3CAFf15Ca682939310d6A5e619AE08e57`) | ETH:False, BTC:False | default |
| AERO | `0x4EC5970fC728C5f65ba413992CD5fF6FD70fcfF0` | ETH:False, BTC:False | default |
| 0xcbADA732173e39521CDBE8bf59a6Dc85A9fc7b8c | `0x34cD971a092d5411bD69C10a5F0A7EEF72C69041` | ETH:False, BTC:False | default |
| 0xcb585250f852C6c6bf90434AB21A00f02833a4af | `0x9f0C1dD78C4CBdF5b9cf923a549A201EdC676D34` | ETH:False, BTC:False | default |
| 0xcb17C9Db87B595717C857a08468793f5bAb6445F | `0x206a34e47093125fbf4C75b7c7E88b84c6A77a69` | ETH:False, BTC:False | default |
| uAVAX | `0xE70f2D34Fd04046aaEC26a198A35dD8F2dF5cd92` | ETH:False, BTC:False | default |
| uSHIB | `0xC8D5D660bb585b68fa0263EeD7B4224a5FC99669` | ETH:False, BTC:False | default |
| CBETH | `0xd7818272B9e248357d13057AAb0B417aF31E817d` | ETH:False, BTC:False | default |
| 0x211Cc4DD073734dA055fbF44a2b4667d5E5fE5d2 | `0x79cf4a31B29D69191f0b6E97916eB93FEB81E533` | ETH:False, BTC:False | default |
| VIRTUAL | `0xEaf310161c9eF7c813A14f8FEF6Fb271434019F7` | ETH:False, BTC:False | default |
| 0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf | `0x8eC6a128a430f7A850165bcF18facc9520a9873F` | ETH:False, BTC:False | default |
| WELL | `0xc15d9944dAefE2dB03e53bef8DDA25a56832C5fe` | ETH:False, BTC:False | default |
| 0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed | `0xE62BcE5D7CB9d16AB8b4D622538bc0A50A5799c2` | ETH:False, BTC:False | default |
| EURC | `0xDAe398520e2B67cd3f27aeF9Cf14D93D927f8250` | ETH:False, BTC:False | default |
| GHO | `0x42868EFcee13C0E71af89c04fF7d96f5bec479b0` | ETH:False, BTC:False | default |
| USDS | `0x2330aaE3bca5F05169d5f4597964D44522F62930` | ETH:False, BTC:False | default |
| SUPER_OETH | `0x39C6E14CdE46D4FFD9F04Ff159e7ce8eC20E10B4` | ETH:True, BTC:False | default |

## Curve Prices
Address: 0x7B2aeE8B6A4bdF0885dEF48CCda8453Fdc1Bba5d

## Curve Prices Global Config
| Parameter | Value |
| --- | --- |
| isPaused | False |
| numAssets | 2 |

### Curve Prices - Registered Assets (2)
| Asset | Feed/Underlying | Config | StaleTime |
| --- | --- | --- | --- |
| 0xd1Eac76497D06Cf15475A5e3984D5bC03de7C707 | Curve Pool | - | - |
| 0xd6c283655B42FA0eb2685F7AB819784F071459dc | Curve Pool | - | - |

## BlueChip Yield Prices
Address: 0x90C70ACfF302c8a7f00574EC3547B0221f39cD28

## BlueChip Yield Prices Global Config
| Parameter | Value |
| --- | --- |
| isPaused | False |
| numAssets | 20 |

### BlueChip Yield Prices - Registered Assets (20)
| Asset | Feed/Underlying | Config | StaleTime |
| --- | --- | --- | --- |
| MORPHO_SPARK_USDC | USDC | Morpho, snaps:20 | default |
| AAVEV3_CBBTC | CBBTC | AaveV3, snaps:20 | default |
| MOONWELL_AERO | AERO | Moonwell, snaps:20 | default |
| 0x784efeB622244d2348d4F2522f8860B96fbEcE89 | AERO | CompoundV3, snaps:20 | default |
| AAVEV3_USDC | USDC | AaveV3, snaps:20 | default |
| AAVEV3_WETH | WETH | AaveV3, snaps:20 | default |
| COMPOUNDV3_WETH | WETH | CompoundV3, snaps:20 | default |
| MORPHO_MOONWELL_WETH | WETH | Morpho, snaps:20 | default |
| MORPHO_SEAMLESS_WETH | WETH | Morpho, snaps:20 | default |
| EULER_WETH | WETH | Euler, snaps:20 | default |
| MOONWELL_CBETH | CBETH | Moonwell, snaps:20 | default |
| COMPOUNDV3_USDC | USDC | CompoundV3, snaps:20 | default |
| MOONWELL_USDC | USDC | Moonwell, snaps:20 | default |
| EULER_USDC | USDC | Euler, snaps:20 | default |
| FLUID_USDC | USDC | Fluid, snaps:20 | default |
| MORPHO_MOONWELL_USDC | USDC | Morpho, snaps:20 | default |
| MORPHO_SEAMLESS_USDC | USDC | Morpho, snaps:20 | default |
| EULER_CBBTC | CBBTC | Euler, snaps:20 | default |
| MOONWELL_CBBTC | CBBTC | Moonwell, snaps:20 | default |
| MORPHO_MOONWELL_CBBTC | CBBTC | Morpho, snaps:20 | default |

## Pyth Prices
Address: 0x89b6E13E4aD4036EAA586219DD73Ebb2b36d5968

## Pyth Prices Global Config
| Parameter | Value |
| --- | --- |
| isPaused | False |
| maxConfidenceRatio | 3.00% |
| numAssets | 0 |

## Stork Prices
Address: 0xCa13ACFB607B842DF5c1D0657C0865cC47bEfe14

## Stork Prices Global Config
| Parameter | Value |
| --- | --- |
| isPaused | False |
| numAssets | 0 |

## Aero Ripe Prices
Address: 0x5ce2BbD5eBe9f7d9322a8F56740F95b9576eE0A2

## Aero Ripe Prices Global Config
| Parameter | Value |
| --- | --- |
| isPaused | False |
| numAssets | 1 |

## wsuperOETHb Prices
Address: 0x2606Ce36b62a77562DF664E7a0009805BB254F3f

## wsuperOETHb Prices Global Config
| Parameter | Value |
| --- | --- |
| isPaused | False |
| numAssets | 1 |

### wsuperOETHb Prices - Registered Assets (1)
| Asset | Feed/Underlying | Config | StaleTime |
| --- | --- | --- | --- |
| WRAPPED_SUPER_OETH | Configured | - | - |

## Undy Vault Prices
Address: 0x2210a9b994CC0F13689043A34F2E11d17DB2099C

## Undy Vault Prices Global Config
| Parameter | Value |
| --- | --- |
| isPaused | False |
| numAssets | 15 |

### Undy Vault Prices - Registered Assets (15)
| Asset | Feed/Underlying | Config | StaleTime |
| --- | --- | --- | --- |
| UNDY_USD | USDC | ID:0, snaps:20 | default |
| UNDY_ETH | WETH | ID:0, snaps:20 | default |
| UNDY_BTC | CBBTC | ID:0, snaps:20 | default |
| UNDY_AERO | AERO | ID:0, snaps:20 | default |
| UNDY_EURC | USDS | ID:0, snaps:20 | default |
| 0x4bCa2A052428D7b7D2E1Daf9e1af471EA4c2F7bf | EURC | ID:0, snaps:20 | default |
| 0x9e629632c483235845E27840C304C11b59d2FEDa | AERO | ID:0, snaps:20 | default |
| 0x897b56836C79e68042EFc51be7ad652a4BBFb86b | CBBTC | ID:0, snaps:20 | default |
| 0x434696F22EF3862f14C6Abd008f18456418f7457 | WETH | ID:0, snaps:20 | default |
| 0xcdD894E6c11d6444e0c3d974928Dd71b28b09356 | USDC | ID:0, snaps:20 | default |
| 0xb33852cfd0c22647AAC501a6Af59Bc4210a686Bf | USDC | ID:0, snaps:20 | default |
| 0x02981DB1a99A14912b204437e7a2E02679B57668 | WETH | ID:0, snaps:20 | default |
| 0x3fb0fC9D3Ddd543AD1b748Ed2286a022f4638493 | CBBTC | ID:0, snaps:20 | default |
| 0x96F1a7ce331F40afe866F3b707c223e377661087 | AERO | ID:0, snaps:20 | default |
| 0x1cb8DAB80f19fC5Aca06C2552AECd79015008eA8 | EURC | ID:0, snaps:20 | default |

================================================================================

<a id="token-statistics"></a>
# Token Statistics

## GREEN Token
| Parameter | Value |
| --- | --- |
| totalSupply | 202.05K GREEN |
| decimals | 18 |
| name | Green USD Stablecoin |
| symbol | GREEN |

## RIPE Token
| Parameter | Value |
| --- | --- |
| totalSupply | 10.32M RIPE |
| decimals | 18 |
| name | Ripe DAO Governance Token |
| symbol | RIPE |

## Savings GREEN (sGREEN)
| Parameter | Value |
| --- | --- |
| totalSupply (shares) | 55.83K GREEN |
| totalAssets (GREEN) | 59.00K GREEN |
| **Exchange Rate** | **1.056821 GREEN per sGREEN** |
| **Accumulated Yield** | **+5.6821%** above 1:1 |
| decimals | 18 |
| name | Savings Green USD |
| symbol | sGREEN |

*Example: 1,000 sGREEN = 1,056.8213 GREEN*

================================================================================

---
*Report generated at block 38883364 on 2025-12-01 02:32:28 UTC*
