================================================================================
# Ripe Protocol - General Parameters

**Generated:** 2025-12-02 04:57:28 UTC
**Block:** 38931025
**Network:** Base Mainnet

General protocol configuration, statistics, and contract status.


## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Token Statistics](#token-statistics)
3. [MissionControl Configuration](#mission-control)
   - [General Config](#general-config)
   - [Debt Config](#debt-config)
   - [Rewards Config](#rewards-config)
   - [Priority Lists](#priority-lists)
4. [RipeHQ Registry](#ripe-hq)
5. [Switchboard Registry](#switchboard)
   - [Individual Switchboard Configurations](#individual-switchboard-configurations)
6. [Endaoment Contracts](#endaoment)
7. [Departments](#departments)

*Note: Live protocol data (debt, rewards, points, contributors) is in `ledger_output.md`*


<a id="executive-summary"></a>
## Executive Summary

| Metric | Value |
| --- | --- |
| **Total GREEN Supply** | 202.00K GREEN |
| **Total Debt Outstanding** | 74.34K GREEN |
| **Debt Utilization** | 37.17% of 200.00K GREEN limit |
| **Active Borrowers** | 78 |
| **Registered Assets** | 55 |
| **Bad Debt** | 0.00 GREEN |
| **RIPE Total Supply** | 10.32M RIPE |
| **sGREEN Exchange Rate** | 1.056821 GREEN per sGREEN (+5.6821% vs 1:1) |
| **Protocol Status** | Deposits ON / Borrowing ON / Liquidations ON |

================================================================================

<a id="token-statistics"></a>
## Token Statistics

### GREEN Token
| Parameter | Value |
| --- | --- |
| totalSupply | 202.00K GREEN |
| decimals | 18 |
| name | Green USD Stablecoin |
| symbol | GREEN |

### RIPE Token
| Parameter | Value |
| --- | --- |
| totalSupply | 10.32M RIPE |
| decimals | 18 |
| name | Ripe DAO Governance Token |
| symbol | RIPE |

### Savings GREEN (sGREEN)
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

<a id="mission-control"></a>
## MissionControl - Core Protocol Configuration
Address: `0xB59b84B526547b6dcb86CCF4004d48E619156CF3`

<a id="general-config"></a>

### General Config
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

<a id="debt-config"></a>

### General Debt Config
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

### General Auction Parameters
| Parameter | Value |
| --- | --- |
| hasParams | True |
| startDiscount | 1.00% |
| maxDiscount | 50.00% |
| delay | 0 blocks (~0s) |
| duration | 43200 blocks (~1.0d) |

### HR Config (Compensation)
| Parameter | Value |
| --- | --- |
| contribTemplate | `0x4965578D80E54b5EbE3BB5D7b1B3E0425559C1D1` |
| maxCompensation | No Limit |
| minCliffLength | 604800 blocks (~14.0d) |
| maxStartDelay | 7776000 blocks (~180.0d) |
| minVestingLength | 604800 blocks (~14.0d) |
| maxVestingLength | 315360000 blocks (~7300.0d) |

### RIPE Bond Config
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

<a id="rewards-config"></a>

### RIPE Rewards Config
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
| **autoStakeLockDuration (derived)** | **15596064 blocks (~361.0d)** |
| stabPoolRipePerDollarClaimed | 0.010000 RIPE |

### Total Points Allocations
| Parameter | Value |
| --- | --- |
| stakersPointsAllocTotal | 100.00% |
| voterPointsAllocTotal | 0.00% |

### RIPE Token Governance Vault Config
| Parameter | Value |
| --- | --- |
| minLockDuration | 43200 blocks (~1.0d) |
| maxLockDuration | 47304000 blocks (~1095.0d) |
| maxLockBoost | 200.00% |
| canExit | True |
| exitFee | 80.00% |
| assetWeight | 10000 |
| shouldFreezeWhenBadDebt | True |

### Other Settings
| Parameter | Value |
| --- | --- |
| underscoreRegistry | UNDERSCORE_REGISTRY (`0x44Cf3c4f000DFD76a35d03298049D37bE688D6F9`) |
| trainingWheels | `0x2255b0006A3DA38AA184E0F9d5e056C2d0448065` |
| shouldCheckLastTouch | True |

<a id="priority-lists"></a>
### Priority Lists

#### Priority Price Source IDs
| Priority | Source ID | Name |
| --- | --- | --- |
| 0 | 1 | Chainlink |
| 1 | 3 | BlueChip Yield Prices |
| 2 | 4 | Pyth Prices |
| 3 | 5 | Stork Prices |
| 4 | 2 | Curve Prices |

#### Priority Liquidation Asset Vaults
| Priority | Vault ID | Vault Name | Asset |
| --- | --- | --- | --- |
| 0 | 3 | Simple ERC20 Vault | USDC (`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`) |
| 1 | 3 | Simple ERC20 Vault | CBBTC (`0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf`) |
| 2 | 3 | Simple ERC20 Vault | WETH (`0x4200000000000000000000000000000000000006`) |
| 3 | 3 | Simple ERC20 Vault | USOL (`0x9B8Df6E244526ab5F6e6400d331DB28C8fdDdb55`) |
| 4 | 3 | Simple ERC20 Vault | CBDOGE (`0xcbD06E5A2B0C65597161de254AA074E489dEb510`) |

#### Priority Stability Pool Vaults
| Priority | Vault ID | Vault Name | Asset |
| --- | --- | --- | --- |
| 0 | 1 | Stability Pool | `0xd6c283655B42FA0eb2685F7AB819784F071459dc` |
| 1 | 1 | Stability Pool | `0xaa0f13488CE069A7B5a099457c753A7CFBE04d36` |

================================================================================

<a id="ripe-hq"></a>
## RipeHQ - Main Registry & Minting Config
Address: `0x6162df1b329E157479F8f1407E888260E0EC3d2b`

### Minting Circuit Breaker
| Parameter | Value |
| --- | --- |
| mintEnabled | True |

### Registry Config (AddressRegistry Module)
| Parameter | Value |
| --- | --- |
| numAddrs (contracts) | 22 |
| registryChangeTimeLock | 21600 blocks (~12.0h) |

### Governance Settings (LocalGov Module)
| Parameter | Value |
| --- | --- |
| governance | GOVERNANCE (`0xe488a42D33b3Af5d3E5Cd5680938d8369716D1bf`) |
| govChangeTimeLock | 43200 blocks (~1.0d) |
| pendingGov | None |

### Registered Contracts & Permissions

| ID | Description | Address | Mint GREEN | Mint RIPE | Blacklist | Paused |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Green Token | `0xd1Eac76497D06Cf15475A5e3984D5bC03de7C707` | - | - | - | False |
| 2 | Savings Green | `0xaa0f13488CE069A7B5a099457c753A7CFBE04d36` | - | - | - | False |
| 3 | Ripe Token | `0x2A0a59d6B975828e781EcaC125dBA40d7ee5dDC0` | - | - | - | False |
| 4 | Ledger | `0x365256e322a47Aa2015F6724783F326e9B24fA47` | - | - | - | False |
| 5 | Mission Control | `0xB59b84B526547b6dcb86CCF4004d48E619156CF3` | - | - | - | False |
| 6 | Switchboard | `0xc68A90A40B87ae1dABA93Da9c02642F8B74030F9` | - | - | Yes | False |
| 7 | Price Desk | `0x68564c6035e8Dc21F0Ce6CB9592dC47B59dE2Ff6` | - | - | - | False |
| 8 | Vault Book | `0xB758e30C14825519b895Fd9928d5d8748A71a944` | - | Yes | - | False |
| 9 | Auction House | `0x8a02aC4754b72aFBDa4f403ec5DA7C2950164084` | Yes | - | - | False |
| 10 | Auction House NFT | `0x504Fb3b94a9f4A238Ee3A16474B91F99A3f26F3A` | - | - | - | False |
| 11 | Boardroom | `0xb5cA6Ef866b510C3b85D4B0e3862061A569412D1` | - | - | - | False |
| 12 | Bond Room | `0x707f660A7834d00792DF9a28386Bb2cCC6446154` | - | Yes | - | False |
| 13 | Credit Engine | `0x30aa8eB041AcB3B22228516297C331B313b81462` | Yes | - | - | False |
| 14 | Endaoment | `0x70fA85Aa99a39161A2623627377F1c791fd091f6` | Yes | - | - | False |
| 15 | Human Resources | `0xF9aCDFd0d167b741f9144Ca01E52FcdE16BE108b` | - | Yes | - | False |
| 16 | Lootbox | `0x1f90ef42Da9B41502d2311300E13FAcf70c64be7` | - | Yes | - | False |
| 17 | Teller | `0xae87deB25Bc5030991Aa5E27Cbab38f37a112C13` | - | - | - | False |
| 18 | Deleverage | `0x75EeBb8c6f1A5727e7c0c1f9d64Ed07cd0966F27` | - | - | - | False |
| 19 | Credit Redeem | `0x3bfB0F72642aeFA2486da00Db855c5F0b787e3FB` | - | - | - | False |
| 20 | Teller Utils | `0x57f071AB96D1798C6bB3e314D2D283502DEDDcdD` | - | - | - | False |
| 21 | Endaoment Funds | `0x4Ce5FB8D572917Eb96724eA1866b505B2a6B0873` | - | - | - | - |
| 22 | Endaoment PSM | `0x2893d0dfa54571bDc7DE60F2d8a456d3377CcAA7` | - | - | - | False |

================================================================================

<a id="switchboard"></a>
## Switchboard - Configuration Contracts Registry
Address: `0xc68A90A40B87ae1dABA93Da9c02642F8B74030F9`

### Registry Config (AddressRegistry Module)
| Parameter | Value |
| --- | --- |
| numAddrs (switchboards) | 5 |
| registryChangeTimeLock | 21600 blocks (~12.0h) |

### Governance Settings (LocalGov Module)
| Parameter | Value |
| --- | --- |
| governance | None |
| govChangeTimeLock | 43200 blocks (~1.0d) |
| pendingGov | None |

### Registered Switchboards

| Reg ID | Description | Address |
| --- | --- | --- |
| 1 | Switchboard Alpha | `0x73Cd87A047eb16E22f8afA21e0980C07Bb26CA83` |
| 2 | Switchboard Bravo | `0xD18AC028cBe1AbebDb118E9C7A60018d58C846e7` |
| 3 | Switchboard Charlie | `0x6D798bD44b1591571c9d95b6D51c9c34a5534008` |
| 4 | Switchboard Delta | `0x50e815AC356798E42EB35De538a0376459ce11cb` |
| 5 | Switchboard Echo | `0xdF99a86e4450163e8DbA47C928131e75D2995dbb` |

### Individual Switchboard Configurations

#### Switchboard Alpha
Address: `0x73Cd87A047eb16E22f8afA21e0980C07Bb26CA83`

##### Governance Settings (LocalGov Module)
| Parameter | Value |
| --- | --- |
| governance | None |
| govChangeTimeLock | 43200 blocks (~1.0d) |
| pendingGov | None |

##### Timelock Settings (TimeLock Module)
| Parameter | Value |
| --- | --- |
| minActionTimeLock | 3600 blocks (~2.0h) |
| maxActionTimeLock | 302400 blocks (~7.0d) |
| actionTimeLock | 0 blocks (~0s) |
| expiration | 302400 blocks (~7.0d) |

#### Switchboard Bravo
Address: `0xD18AC028cBe1AbebDb118E9C7A60018d58C846e7`

##### Governance Settings (LocalGov Module)
| Parameter | Value |
| --- | --- |
| governance | None |
| govChangeTimeLock | 43200 blocks (~1.0d) |
| pendingGov | None |

##### Timelock Settings (TimeLock Module)
| Parameter | Value |
| --- | --- |
| minActionTimeLock | 14400 blocks (~8.0h) |
| maxActionTimeLock | 302400 blocks (~7.0d) |
| actionTimeLock | 14400 blocks (~8.0h) |
| expiration | 302400 blocks (~7.0d) |

#### Switchboard Charlie
Address: `0x6D798bD44b1591571c9d95b6D51c9c34a5534008`

##### Governance Settings (LocalGov Module)
| Parameter | Value |
| --- | --- |
| governance | None |
| govChangeTimeLock | 43200 blocks (~1.0d) |
| pendingGov | None |

##### Timelock Settings (TimeLock Module)
| Parameter | Value |
| --- | --- |
| minActionTimeLock | 3600 blocks (~2.0h) |
| maxActionTimeLock | 302400 blocks (~7.0d) |
| actionTimeLock | 0 blocks (~0s) |
| expiration | 302400 blocks (~7.0d) |

#### Switchboard Delta
Address: `0x50e815AC356798E42EB35De538a0376459ce11cb`

##### Governance Settings (LocalGov Module)
| Parameter | Value |
| --- | --- |
| governance | None |
| govChangeTimeLock | 43200 blocks (~1.0d) |
| pendingGov | None |

##### Timelock Settings (TimeLock Module)
| Parameter | Value |
| --- | --- |
| minActionTimeLock | 3600 blocks (~2.0h) |
| maxActionTimeLock | 302400 blocks (~7.0d) |
| actionTimeLock | 3600 blocks (~2.0h) |
| expiration | 302400 blocks (~7.0d) |

#### Switchboard Echo
Address: `0xdF99a86e4450163e8DbA47C928131e75D2995dbb`

##### Governance Settings (LocalGov Module)
| Parameter | Value |
| --- | --- |
| governance | None |
| govChangeTimeLock | 43200 blocks (~1.0d) |
| pendingGov | None |

##### Timelock Settings (TimeLock Module)
| Parameter | Value |
| --- | --- |
| minActionTimeLock | 3600 blocks (~2.0h) |
| maxActionTimeLock | 302400 blocks (~7.0d) |
| actionTimeLock | 0 blocks (~0s) |
| expiration | 302400 blocks (~7.0d) |

================================================================================

<a id="endaoment"></a>
## Endaoment Contracts

### Endaoment
Address: `0x70fA85Aa99a39161A2623627377F1c791fd091f6`

#### Status
| Parameter | Value |
| --- | --- |
| isPaused | False |
| WETH | WETH (`0x4200000000000000000000000000000000000006`) |

### Endaoment PSM - Peg Stability Module
Address: `0x2893d0dfa54571bDc7DE60F2d8a456d3377CcAA7`

### PSM Mint Configuration
| Parameter | Value |
| --- | --- |
| canMint | Disabled |
| mintFee | 0.00% |
| maxIntervalMint | 100.00K GREEN |
| shouldEnforceMintAllowlist | False |

### PSM Redeem Configuration
| Parameter | Value |
| --- | --- |
| canRedeem | Disabled |
| redeemFee | 0.00% |
| maxIntervalRedeem | 100.00K GREEN |
| shouldEnforceRedeemAllowlist | False |

### PSM Interval & Yield Configuration
| Parameter | Value |
| --- | --- |
| numBlocksPerInterval | 43200 blocks (~1.0d) |
| shouldAutoDeposit | True |
| usdcYieldPosition.legoId | 13 |
| usdcYieldPosition.vaultToken | `0xb33852cfd0c22647AAC501a6Af59Bc4210a686Bf` |

### PSM Current Interval Stats
| Parameter | Value |
| --- | --- |
| Mint Interval Start | 0 |
| Mint Interval Amount | 0.00 GREEN |
| Redeem Interval Start | 0 |
| Redeem Interval Amount | 0.00 GREEN |

**USDC Address:** USDC (`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`)

### EndaomentFunds
Address: `0x4Ce5FB8D572917Eb96724eA1866b505B2a6B0873`

================================================================================

<a id="departments"></a>
## Departments

### CreditEngine
Address: `0x30aa8eB041AcB3B22228516297C331B313b81462`

#### Config
| Parameter | Value |
| --- | --- |
| undyVaultDiscount | 50.00% |
| buybackRatio | 0.00% |

### BondBooster
Address: `0xA1872467AC4fb442aeA341163A65263915ce178a`

#### Config
| Parameter | Value |
| --- | --- |
| maxBoostRatio | 200.00% |
| maxUnits | 25000 |
| minLockDuration | 7776000 blocks (~180.0d) |

### Lootbox
Address: `0x1f90ef42Da9B41502d2311300E13FAcf70c64be7`

#### Underscore Rewards Config
| Parameter | Value |
| --- | --- |
| hasUnderscoreRewards | True |
| underscoreSendInterval | 43200 blocks (~1.0d) |
| lastUnderscoreSend (block) | 0 |
| undyDepositRewardsAmount | 100.00 RIPE |
| undyYieldBonusAmount | 100.00 RIPE |

### HumanResources
Address: `0xF9aCDFd0d167b741f9144Ca01E52FcdE16BE108b`

#### Status
| Parameter | Value |
| --- | --- |
| isPaused | False |

#### Governance Settings (LocalGov Module)
| Parameter | Value |
| --- | --- |
| governance | None |
| govChangeTimeLock | 43200 blocks (~1.0d) |
| pendingGov | None |

#### Timelock Settings (TimeLock Module)
| Parameter | Value |
| --- | --- |
| minActionTimeLock | 43200 blocks (~1.0d) |
| maxActionTimeLock | 302400 blocks (~7.0d) |
| actionTimeLock | 43200 blocks (~1.0d) |
| expiration | 302400 blocks (~7.0d) |
*Note: numContributors is tracked in Ledger contract*

### StabilityPool
Address: `0x2a157096af6337b2b4bd47de435520572ed5a439`

#### Status
| Parameter | Value |
| --- | --- |
| isPaused | False |
| numAssets | 2 |

---

### BondRoom
Address: `0x707f660A7834d00792DF9a28386Bb2cCC6446154`

#### Status
| Parameter | Value |
| --- | --- |
| isPaused | False |
| bondBooster | `0xA1872467AC4fb442aeA341163A65263915ce178a` |

### RipeGovVault
Address: `0xe42b3dC546527EB70D741B185Dc57226cA01839D`

#### Status
| Parameter | Value |
| --- | --- |
| isPaused | False |
| totalGovPoints | 104,140,151,492,233,437,230 |

### AuctionHouse
Address: `0x8a02aC4754b72aFBDa4f403ec5DA7C2950164084`

#### Status
| Parameter | Value |
| --- | --- |
| isPaused | False |

### Teller
Address: `0xae87deB25Bc5030991Aa5E27Cbab38f37a112C13`

#### Status
| Parameter | Value |
| --- | --- |
| isPaused | False |

### Deleverage
Address: `0x75EeBb8c6f1A5727e7c0c1f9d64Ed07cd0966F27`

#### Status
| Parameter | Value |
| --- | --- |
| isPaused | False |

### CreditRedeem
Address: `0x3bfB0F72642aeFA2486da00Db855c5F0b787e3FB`

#### Status
| Parameter | Value |
| --- | --- |
| isPaused | False |

================================================================================

---
*Report generated at block 38931025 on 2025-12-02 04:58:10 UTC*
