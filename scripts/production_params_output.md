Connecting to Base mainnet via Alchemy...
Connected. Block: 38663660

Loading contracts from Etherscan...
Fetching configuration data...

================================================================================
# Ripe Protocol Production Parameters

**Generated:** 2025-11-26 00:25:14 UTC
**Block:** 38663660
**Network:** Base Mainnet

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [MissionControl Configuration](#mission-control)
   - [General Config](#general-config)
   - [Debt Config](#debt-config)
   - [Rewards Config](#rewards-config)
   - [Registered Assets](#registered-assets)
3. [RipeHQ Registry](#ripe-hq)
4. [Switchboard Registry](#switchboard)
5. [PriceDesk Oracles](#price-desk)
6. [VaultBook Registry](#vault-book)
7. [Ledger Statistics](#ledger)
8. [Endaoment PSM](#endaoment-psm)
9. [Other Contracts](#other-contracts)
   - [CreditEngine](#credit-engine)
   - [BondBooster](#bond-booster)
   - [Lootbox](#lootbox)
   - [BondRoom](#bond-room)
   - [RipeGovVault](#ripe-gov-vault)
   - [StabilityPool](#stability-pool)
10. [Price Source Configurations](#price-sources)
11. [Token Statistics](#token-statistics)


<a id="executive-summary"></a>
## 📊 Executive Summary

| Metric | Value |
| --- | --- |
| **Total GREEN Supply** | 202.46K GREEN |
| **Total Debt Outstanding** | 74.80K GREEN |
| **Debt Utilization** | 37.40% of 200.00K GREEN limit |
| **Active Borrowers** | 79 |
| **Registered Assets** | 55 |
| **Bad Debt** | 0.00 GREEN |
| **RIPE Total Supply** | 10.32M RIPE |
| **sGREEN Exchange Rate** | 1.055864 GREEN per sGREEN (+5.5864% vs 1:1) |
| **Protocol Status** | ✅ Deposits / ✅ Borrowing / ✅ Liquidations |

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
| contribTemplate | 0x4965...C1D1 |
| maxCompensation | 0.000000 RIPE |
| minCliffLength | 604800 blocks (~14.0d) |
| maxStartDelay | 7776000 blocks (~180.0d) |
| minVestingLength | 604800 blocks (~14.0d) |
| maxVestingLength | 315360000 blocks (~7300.0d) |

## RIPE Bond Config
| Parameter | Value |
| --- | --- |
| asset | USDC (0x8335...2913) |
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
| underscoreRegistry | UNDERSCORE_REGISTRY (0x44Cf...D6F9) |
| trainingWheels | 0x2255...8065 |
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
| 3 | USDC (0x8335...2913) |
| 3 | CBBTC (0xcbB7...33Bf) |
| 3 | WETH (0x4200...0006) |
| 3 | USOL (0x9B8D...db55) |
| 3 | CBDOGE (0xcbD0...b510) |

## Priority Stability Pool Vaults
| Vault ID | Asset |
| --- | --- |
| 1 | GREEN/USDC (0xd6c2...59dc) |
| 1 | sGREEN (0xaa0f...4d36) |

## Registered Assets (55 total)
| Asset | Vault IDs | LTV | Liq Threshold | Borrow Rate | canDeposit | canBorrow |
| --- | --- | --- | --- | --- | --- | --- |
| USDC (0x8335...2913) | 3 | 80.00% | 90.00% | 5.00% | True | True |
| CBBTC (0xcbB7...33Bf) | 3 | 70.00% | 80.00% | 7.00% | True | True |
| WETH (0x4200...0006) | 3 | 70.00% | 80.00% | 7.00% | True | True |
| sGREEN (0xaa0f...4d36) | 1 | 0.00% | 0.00% | 0.00% | True | False |
| GREEN/USDC (0xd6c2...59dc) | 1 | 0.00% | 0.00% | 0.00% | True | False |
| RIPE_TOKEN (0x2A0a...dDC0) | 2 | 0.00% | 0.00% | 0.00% | True | False |
| RIPE/WETH (0xF8D9...2526) | 2 | 0.00% | 0.00% | 0.00% | False | False |
| CBDOGE (0xcbD0...b510) | 3 | 50.00% | 65.00% | 11.00% | True | True |
| USOL (0x9B8D...db55) | 3 | 50.00% | 65.00% | 11.00% | True | True |
| RIPE_WETH_POOL (0x7658...d6A9) | 2 | 0.00% | 0.00% | 0.00% | True | False |
| MORPHO_SPARK_USDC (0x7BfA...F34A) | 3 | 80.00% | 85.00% | 5.00% | True | True |
| AERO (0x9401...8631) | 3 | 50.00% | 65.00% | 8.00% | True | True |
| 0x784e...cE89 | 4 | 50.00% | 65.00% | 8.00% | True | True |
| MOONWELL_AERO (0x7390...9Ba6) | 3 | 50.00% | 65.00% | 8.00% | True | True |
| AAVEV3_USDC (0x4e65...c0AB) | 4 | 80.00% | 85.00% | 5.00% | True | True |
| AAVEV3_CBBTC (0xBdb9...8EE6) | 4 | 70.00% | 80.00% | 7.00% | True | True |
| AAVEV3_WETH (0xD4a0...8bb7) | 4 | 70.00% | 80.00% | 7.00% | True | True |
| VIRTUAL (0x0b3e...7E1b) | 3 | 50.00% | 65.00% | 11.00% | True | True |
| cbADA (0xcbAD...7b8c) | 3 | 50.00% | 65.00% | 11.00% | True | True |
| cbXRP (0xcb58...a4af) | 3 | 50.00% | 65.00% | 11.00% | True | True |
| cbLTC (0xcb17...445F) | 3 | 50.00% | 65.00% | 11.00% | True | True |
| VVV (0xacfE...21bf) | 3 | 40.00% | 50.00% | 13.00% | True | True |
| WELL (0xA885...96AE) | 3 | 40.00% | 50.00% | 13.00% | True | True |
| DEGEN (0x4ed4...efed) | 3 | 40.00% | 50.00% | 13.00% | True | True |
| COMPOUNDV3_WETH (0x46e6...70bf) | 4 | 70.00% | 80.00% | 7.00% | True | True |
| MORPHO_MOONWELL_WETH (0xa0E4...0ff1) | 3 | 70.00% | 80.00% | 7.00% | True | True |
| MORPHO_SEAMLESS_WETH (0x27D8...5c18) | 3 | 70.00% | 80.00% | 7.00% | True | True |
| EULER_WETH (0x8591...b410) | 3 | 70.00% | 80.00% | 7.00% | True | True |
| CBETH (0x2Ae3...Ec22) | 3 | 70.00% | 80.00% | 7.00% | True | True |
| MOONWELL_CBETH (0x3bf9...A5E5) | 3 | 70.00% | 80.00% | 7.00% | True | True |
| COMPOUNDV3_USDC (0xb125...Eb2F) | 4 | 80.00% | 90.00% | 5.00% | True | True |
| MOONWELL_USDC (0xEdc8...6c22) | 3 | 80.00% | 90.00% | 5.00% | True | True |
| EULER_USDC (0x0A1a...eE16) | 3 | 80.00% | 90.00% | 5.00% | True | True |
| FLUID_USDC (0xf42f...9169) | 3 | 80.00% | 90.00% | 5.00% | True | True |
| MORPHO_MOONWELL_USDC (0xc125...A2Ca) | 3 | 80.00% | 90.00% | 5.00% | True | True |
| MORPHO_SEAMLESS_USDC (0x616a...3738) | 3 | 80.00% | 90.00% | 5.00% | True | True |
| EULER_CBBTC (0x8820...7f8B) | 3 | 70.00% | 80.00% | 7.00% | True | True |
| MOONWELL_CBBTC (0xF877...5976) | 3 | 70.00% | 80.00% | 7.00% | True | True |
| MORPHO_MOONWELL_CBBTC (0x5432...a796) | 3 | 70.00% | 80.00% | 7.00% | True | True |
| sUSDe (0x211C...E5d2) | 3 | 80.00% | 90.00% | 5.00% | True | True |
| WRAPPED_SUPER_OETH (0x7FcD...8Ea6) | 3 | 70.00% | 80.00% | 7.00% | True | True |
| GREEN (0xd1Ea...C707) | None | 0.00% | 0.00% | 0.00% | False | False |
| UNDY_USD (0xcF9F...E41e) | 5 | 80.00% | 90.00% | 5.00% | False | True |
| UNDY_ETH (0x01EC...3497) | 5 | 70.00% | 80.00% | 7.00% | False | True |
| UNDY_BTC (0x4cD9...37d4) | 5 | 70.00% | 80.00% | 7.00% | False | True |
| undyUSD (0xcdD8...9356) | 5 | 80.00% | 90.00% | 5.00% | False | True |
| undyETH (0x4346...7457) | 5 | 70.00% | 80.00% | 7.00% | False | True |
| undyBTC (0x897b...b86b) | 5 | 70.00% | 80.00% | 7.00% | False | True |
| undyAERO (0x9e62...FEDa) | 5 | 50.00% | 65.00% | 8.00% | False | True |
| undyEURC (0x4bCa...F7bf) | 5 | 80.00% | 90.00% | 5.00% | False | True |
| undyETH (0x0298...7668) | 5 | 70.00% | 80.00% | 7.00% | True | True |
| undyBTC (0x3fb0...8493) | 5 | 70.00% | 80.00% | 7.00% | True | True |
| undyUSD (0xb338...86Bf) | 5 | 80.00% | 90.00% | 5.00% | True | True |
| undyAERO (0x96F1...1087) | 5 | 50.00% | 65.00% | 8.00% | True | True |
| undyEURC (0x1cb8...8eA8) | 5 | 80.00% | 90.00% | 5.00% | True | True |

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

#### sGREEN (0xaa0f13488CE069A7B5a099457c753A7CFBE04d36)

## sGREEN - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 1 |
| stakersPointsAlloc | 15.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 100,000,000,000,000,000,000.000000 |
| globalDepositLimit | 1,000,000,000,000,000,000,000.000000 |
| minDepositBalance | 10,000,000,000.000000 |

## sGREEN - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 0.00% |
| redemptionThreshold | 0.00% |
| liqThreshold | 0.00% |
| liqFee | 0.00% |
| borrowRate | 0.00% |
| daowry | 0.00% |

## sGREEN - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | True |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

## sGREEN - Action Flags
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

#### GREEN/USDC (0xd6c283655B42FA0eb2685F7AB819784F071459dc)

## GREEN/USDC - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 1 |
| stakersPointsAlloc | 25.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 100,000,000,000,000,000,000.000000 |
| globalDepositLimit | 1,000,000,000,000,000,000,000.000000 |
| minDepositBalance | 10,000,000,000.000000 |

## GREEN/USDC - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 0.00% |
| redemptionThreshold | 0.00% |
| liqThreshold | 0.00% |
| liqFee | 0.00% |
| borrowRate | 0.00% |
| daowry | 0.00% |

## GREEN/USDC - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

## GREEN/USDC - Action Flags
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

#### RIPE/WETH (0xF8D92a9531205AB2Dd0Bc623CDF4A6Ab4c3a2526)

## RIPE/WETH - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 2 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 100,000,000,000,000,000,000.000000 |
| globalDepositLimit | 1,000,000,000,000,000,000,000.000000 |
| minDepositBalance | 1,000,000,000.000000 |

## RIPE/WETH - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 0.00% |
| redemptionThreshold | 0.00% |
| liqThreshold | 0.00% |
| liqFee | 0.00% |
| borrowRate | 0.00% |
| daowry | 0.00% |

## RIPE/WETH - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

## RIPE/WETH - Action Flags
| Parameter | Value |
| --- | --- |
| canDeposit | False |
| canWithdraw | False |
| canRedeemCollateral | False |
| canRedeemInStabPool | True |
| canBuyInAuction | True |
| canClaimInStabPool | True |
| whitelist | 0x2255...8065 |
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

#### 0x784e...cE89 (0x784efeB622244d2348d4F2522f8860B96fbEcE89)

## 0x784e...cE89 - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 4 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 3,000,000,000,000,000.000000 |
| globalDepositLimit | 30,000,000,000,000,000.000000 |
| minDepositBalance | 1,000,000,000,000.000000 |

## 0x784e...cE89 - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 50.00% |
| redemptionThreshold | 60.00% |
| liqThreshold | 65.00% |
| liqFee | 10.00% |
| borrowRate | 8.00% |
| daowry | 0.25% |

## 0x784e...cE89 - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## 0x784e...cE89 - Action Flags
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

#### cbADA (0xcbADA732173e39521CDBE8bf59a6Dc85A9fc7b8c)

## cbADA - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 3,750.000000 |
| globalDepositLimit | 37,500.000000 |
| minDepositBalance | 1.000000 |

## cbADA - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 50.00% |
| redemptionThreshold | 60.00% |
| liqThreshold | 65.00% |
| liqFee | 12.00% |
| borrowRate | 11.00% |
| daowry | 0.25% |

## cbADA - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## cbADA - Action Flags
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

#### cbXRP (0xcb585250f852C6c6bf90434AB21A00f02833a4af)

## cbXRP - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 1,000.000000 |
| globalDepositLimit | 10,000.000000 |
| minDepositBalance | 0.333333 |

## cbXRP - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 50.00% |
| redemptionThreshold | 60.00% |
| liqThreshold | 65.00% |
| liqFee | 12.00% |
| borrowRate | 11.00% |
| daowry | 0.25% |

## cbXRP - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## cbXRP - Action Flags
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

#### cbLTC (0xcb17C9Db87B595717C857a08468793f5bAb6445F)

## cbLTC - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 2,500.000000 |
| globalDepositLimit | 25,000.000000 |
| minDepositBalance | 0.800000 |

## cbLTC - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 50.00% |
| redemptionThreshold | 60.00% |
| liqThreshold | 65.00% |
| liqFee | 12.00% |
| borrowRate | 11.00% |
| daowry | 0.25% |

## cbLTC - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## cbLTC - Action Flags
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

#### VVV (0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf)

## VVV - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 1,100,000,000,000,000.000000 |
| globalDepositLimit | 11,000,000,000,000,000.000000 |
| minDepositBalance | 110,000,000,000.000000 |

## VVV - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 40.00% |
| redemptionThreshold | 45.00% |
| liqThreshold | 50.00% |
| liqFee | 15.00% |
| borrowRate | 13.00% |
| daowry | 0.25% |

## VVV - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## VVV - Action Flags
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

#### DEGEN (0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed)

## DEGEN - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 750,000,000,000,000,000.000000 |
| globalDepositLimit | 7,500,000,000,000,000,000.000000 |
| minDepositBalance | 75,000,000,000,000.000000 |

## DEGEN - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 40.00% |
| redemptionThreshold | 45.00% |
| liqThreshold | 50.00% |
| liqFee | 15.00% |
| borrowRate | 13.00% |
| daowry | 0.25% |

## DEGEN - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## DEGEN - Action Flags
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

#### sUSDe (0x211Cc4DD073734dA055fbF44a2b4667d5E5fE5d2)

## sUSDe - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 6,000,000,000,000,000.000000 |
| globalDepositLimit | 60,000,000,000,000,000.000000 |
| minDepositBalance | 10,000,000,000.000000 |

## sUSDe - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 80.00% |
| redemptionThreshold | 85.00% |
| liqThreshold | 90.00% |
| liqFee | 5.00% |
| borrowRate | 5.00% |
| daowry | 0.25% |

## sUSDe - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

## sUSDe - Action Flags
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

#### GREEN (0xd1Eac76497D06Cf15475A5e3984D5bC03de7C707)

## GREEN - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | None |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 0.000001 |
| globalDepositLimit | 0.000002 |
| minDepositBalance | 0.000001 |

## GREEN - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 0.00% |
| redemptionThreshold | 0.00% |
| liqThreshold | 0.00% |
| liqFee | 0.00% |
| borrowRate | 0.00% |
| daowry | 0.00% |

## GREEN - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

## GREEN - Action Flags
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

#### undyUSD (0xcdD894E6c11d6444e0c3d974928Dd71b28b09356)

## undyUSD - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 5 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 50,000.000000 |
| globalDepositLimit | 250,000.000000 |
| minDepositBalance | 0.100000 |

## undyUSD - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 80.00% |
| redemptionThreshold | 85.00% |
| liqThreshold | 90.00% |
| liqFee | 5.00% |
| borrowRate | 5.00% |
| daowry | 0.25% |

## undyUSD - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

## undyUSD - Action Flags
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

#### undyETH (0x434696F22EF3862f14C6Abd008f18456418f7457)

## undyETH - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 5 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 250,000,000,000.000000 |
| globalDepositLimit | 2,500,000,000,000.000000 |
| minDepositBalance | 25,000,000.000000 |

## undyETH - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

## undyETH - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## undyETH - Action Flags
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

#### undyBTC (0x897b56836C79e68042EFc51be7ad652a4BBFb86b)

## undyBTC - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 5 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 1.000000 |
| globalDepositLimit | 10.000000 |
| minDepositBalance | 0.000100 |

## undyBTC - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

## undyBTC - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## undyBTC - Action Flags
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

#### undyAERO (0x9e629632c483235845E27840C304C11b59d2FEDa)

## undyAERO - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 5 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 100,000,000,000,000.000000 |
| globalDepositLimit | 1,000,000,000,000,000.000000 |
| minDepositBalance | 100,000,000,000.000000 |

## undyAERO - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 50.00% |
| redemptionThreshold | 60.00% |
| liqThreshold | 65.00% |
| liqFee | 12.00% |
| borrowRate | 8.00% |
| daowry | 0.25% |

## undyAERO - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## undyAERO - Action Flags
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

#### undyEURC (0x4bCa2A052428D7b7D2E1Daf9e1af471EA4c2F7bf)

## undyEURC - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 5 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 100.000000 |
| globalDepositLimit | 1,000.000000 |
| minDepositBalance | 0.100000 |

## undyEURC - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 80.00% |
| redemptionThreshold | 85.00% |
| liqThreshold | 90.00% |
| liqFee | 5.00% |
| borrowRate | 5.00% |
| daowry | 0.25% |

## undyEURC - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

## undyEURC - Action Flags
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

#### undyETH (0x02981DB1a99A14912b204437e7a2E02679B57668)

## undyETH - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 5 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 250,000,000,000.000000 |
| globalDepositLimit | 2,500,000,000,000.000000 |
| minDepositBalance | 25,000,000.000000 |

## undyETH - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

## undyETH - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## undyETH - Action Flags
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

#### undyBTC (0x3fb0fC9D3Ddd543AD1b748Ed2286a022f4638493)

## undyBTC - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 5 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 1.000000 |
| globalDepositLimit | 10.000000 |
| minDepositBalance | 0.000100 |

## undyBTC - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

## undyBTC - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## undyBTC - Action Flags
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

#### undyUSD (0xb33852cfd0c22647AAC501a6Af59Bc4210a686Bf)

## undyUSD - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 5 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 50,000.000000 |
| globalDepositLimit | 250,000.000000 |
| minDepositBalance | 0.100000 |

## undyUSD - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 80.00% |
| redemptionThreshold | 85.00% |
| liqThreshold | 90.00% |
| liqFee | 5.00% |
| borrowRate | 5.00% |
| daowry | 0.25% |

## undyUSD - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

## undyUSD - Action Flags
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

#### undyAERO (0x96F1a7ce331F40afe866F3b707c223e377661087)

## undyAERO - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 5 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 1,000,000,000,000,000.000000 |
| globalDepositLimit | 10,000,000,000,000,000.000000 |
| minDepositBalance | 100,000,000,000.000000 |

## undyAERO - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 50.00% |
| redemptionThreshold | 60.00% |
| liqThreshold | 65.00% |
| liqFee | 12.00% |
| borrowRate | 8.00% |
| daowry | 0.25% |

## undyAERO - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

## undyAERO - Action Flags
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

#### undyEURC (0x1cb8DAB80f19fC5Aca06C2552AECd79015008eA8)

## undyEURC - Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 5 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 1,000.000000 |
| globalDepositLimit | 10,000.000000 |
| minDepositBalance | 0.100000 |

## undyEURC - Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 80.00% |
| redemptionThreshold | 85.00% |
| liqThreshold | 90.00% |
| liqFee | 5.00% |
| borrowRate | 5.00% |
| daowry | 0.25% |

## undyEURC - Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

## undyEURC - Action Flags
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
| greenToken (ID 1) | GREEN (0xd1Ea...C707) |
| savingsGreen (ID 2) | sGREEN (0xaa0f...4d36) |
| ripeToken (ID 3) | RIPE_TOKEN (0x2A0a...dDC0) |

## Registry Config
| Parameter | Value |
| --- | --- |
| numAddrs | 21 |
| registryChangeTimeLock | 21600 blocks (~12.0h) |

### All Registered Contracts
| ID | Description | Address | Mint GREEN | Mint RIPE | Blacklist | Paused |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Green Token | GREEN (0xd1Ea...C707) | - | - | - | False |
| 2 | Savings Green | sGREEN (0xaa0f...4d36) | - | - | - | False |
| 3 | Ripe Token | RIPE_TOKEN (0x2A0a...dDC0) | - | - | - | False |
| 4 | Ledger | 0x3652...fA47 | - | - | - | False |
| 5 | Mission Control | MissionControl (0xB59b...6CF3) | - | - | - | False |
| 6 | Switchboard | 0xc68A...30F9 | - | - | ✓ | False |
| 7 | Price Desk | 0x6856...2Ff6 | - | - | - | False |
| 8 | Vault Book | 0xB758...a944 | - | ✓ | - | False |
| 9 | Auction House | 0x38FB...7312 | ✓ | - | - | False |
| 10 | Auction House NFT | 0x504F...6F3A | - | - | - | False |
| 11 | Boardroom | 0xb5cA...12D1 | - | - | - | False |
| 12 | Bond Room | 0xe2E1...84A6 | - | ✓ | - | False |
| 13 | Credit Engine | 0xf911...DA6a | ✓ | - | - | False |
| 14 | Endaoment | Endaoment (0x14F4...E40d) | ✓ | - | - | False |
| 15 | Human Resources | 0xF9aC...108b | - | ✓ | - | False |
| 16 | Lootbox | 0xef52...2515 | - | ✓ | - | False |
| 17 | Teller | 0xae87...2C13 | - | - | - | False |
| 18 | Deleverage | 0x9cE3...6F61 | - | - | - | False |
| 19 | Credit Redeem | 0x3bfB...e3FB | - | - | - | False |
| 20 | Teller Utils | 0x57f0...DcdD | - | - | - | False |

================================================================================

<a id="switchboard"></a>
# Switchboard - Configuration Contracts Registry
Address: 0xc68A90A40B87ae1dABA93Da9c02642F8B74030F9

## Registry Config
| Parameter | Value |
| --- | --- |
| numAddrs (switchboards) | 4 |
| registryChangeTimeLock | 21600 blocks (~12.0h) |

### Registered Switchboards
| ID | Description | Address | Paused |
| --- | --- | --- | --- |
| 1 | Switchboard Alpha | 0x4EEc...AF8B | - |
| 2 | Switchboard Bravo | 0xD18A...46e7 | - |
| 3 | Switchboard Charlie | 0xaEb3...403b | - |
| 4 | Switchboard Delta | 0x50e8...11cb | - |

================================================================================

<a id="price-desk"></a>
# PriceDesk - Oracle Registry
Address: 0xDFe8D79bc05420a3fFa14824135016a738eE8299

## Constants
| Parameter | Value |
| --- | --- |
| ETH | ETH (0xEeee...EEeE) |

## Registry Config
| Parameter | Value |
| --- | --- |
| numAddrs (price sources) | 8 |
| registryChangeTimeLock | 21600 blocks (~12.0h) |

### Registered Price Sources
| Reg ID | Description | Address |
| --- | --- | --- |
| 1 | Chainlink | 0x253f...B3D9 |
| 2 | Curve Prices | 0x7B2a...ba5d |
| 3 | BlueChip Yield Prices | 0x90C7...cD28 |
| 4 | Pyth Prices | 0x4dfb...b9c0 |
| 5 | Stork Prices | 0xd831...e774 |
| 6 | Aero Ripe Prices | 0x5ce2...E0A2 |
| 7 | wsuperOETHb Prices | 0x2606...4F3f |
| 8 | Undy Vault Prices | 0x2210...099C |

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
| sGREEN | Very High (5.44e+12 ) |
| GREEN/USDC | Very High (5.87e+12 ) |

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
| RIPE/WETH | 0.00  |
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
| USDC | 764.26  |
| CBBTC | 0.02  |
| WETH | 1.57  |
| CBDOGE | 285.30  |
| USOL | 1.70  |
| MORPHO_SPARK_USDC | 7.14K  |
| AERO | 1.81K  |
| MOONWELL_AERO | 0.00  |
| cbXRP | 0.00  |
| WELL | 11.99K  |
| VIRTUAL | 1.11K  |
| VVV | 295.05  |
| DEGEN | 145.66K  |
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
| sUSDe | 0.83  |
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
| 0x784e...cE89 | 0.00  |
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
| undyUSD | 0.00  |
| undyUSD | 103.47K  |
| undyBTC | 0.00  |
| undyETH | 0.01  |
| undyAERO | 16.66  |

================================================================================

<a id="ledger"></a>
# Ledger - Core Protocol Data
Address: 0x365256e322a47Aa2015F6724783F326e9B24fA47

## Debt Statistics
| Parameter | Value |
| --- | --- |
| totalDebt | 74.80K GREEN |
| numBorrowers | 79 |
| unrealizedYield | 0.29 GREEN |

## RIPE Rewards Pool
| Parameter | Value |
| --- | --- |
| borrowers allocation | 314.65 RIPE |
| stakers allocation | 4.67K RIPE |
| voters allocation | 0.00 RIPE |
| genDepositors allocation | 0.00 RIPE |
| newRipeRewards | 51.43 RIPE |
| lastUpdate (block) | 38662972 |
| ripeAvailForRewards | 14.60K RIPE |

## Global Deposit Points
| Parameter | Value |
| --- | --- |
| lastUsdValue | $0.15 |
| ripeStakerPoints | 12944718095 |
| ripeVotePoints | 0 |
| ripeGenPoints | 933932358244 |
| lastUpdate (block) | 38662972 |

## Global Borrow Points
| Parameter | Value |
| --- | --- |
| lastPrincipal | 0.00 GREEN |
| points | 89970245938 |
| lastUpdate (block) | 38653959 |

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
Address: 0x14F4f1CD5F4197DB7cB536B282fe6c59eACfE40d

================================================================================

<a id="other-contracts"></a>
# Other Contract Configurations

================================================================================

<a id="credit-engine"></a>
# CreditEngine - Credit Configuration
Address: 0xf9111dFcAbf2538D6ED9057C07e18bc14AC8DA6a

## Credit Engine Config
| Parameter | Value |
| --- | --- |
| undyVaultDiscount | 50.00% |

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
Address: 0xef52d8a4732b96b98A0Bd47a69beFb40CdCF2515
*No underscore config deployed yet*

================================================================================

<a id="bond-room"></a>
# BondRoom - Bond Purchase Configuration
Address: 0xe2E1a03b95B8E8EFEB6eFbAD52172488FF8C84A6

## Bond Room Config
| Parameter | Value |
| --- | --- |
| bondBooster | 0xA187...178a |

================================================================================

<a id="ripe-gov-vault"></a>
# Ripe Gov Vault - Governance Staking
Address: 0xe42b3dC546527EB70D741B185Dc57226cA01839D

## Governance Vault Stats
| Parameter | Value |
| --- | --- |
| totalGovPoints | 101,065,513,109,068,698,931 |
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
| ETH | CHAINLINK_ETH_USD (0x7104...Bb70) | ETH:False, BTC:False | default |
| WETH | CHAINLINK_ETH_USD (0x7104...Bb70) | ETH:False, BTC:False | default |
| BTC | CHAINLINK_BTC_USD (0x64c9...848F) | ETH:False, BTC:False | default |
| USDC | CHAINLINK_USDC_USD (0x7e86...bc6B) | ETH:False, BTC:False | default |
| CBBTC | CHAINLINK_CBBTC_USD (0x07DA...9f9D) | ETH:False, BTC:False | default |
| USOL | CHAINLINK_SOL_USD (0x9750...462D) | ETH:False, BTC:False | default |
| CBDOGE | CHAINLINK_DOGE_USD (0x8422...8e57) | ETH:False, BTC:False | default |
| AERO | 0x4EC5...cfF0 | ETH:False, BTC:False | default |
| cbADA | 0x34cD...9041 | ETH:False, BTC:False | default |
| cbXRP | 0x9f0C...6D34 | ETH:False, BTC:False | default |
| cbLTC | 0x206a...7a69 | ETH:False, BTC:False | default |
| uAVAX | 0xE70f...cd92 | ETH:False, BTC:False | default |
| uSHIB | 0xC8D5...9669 | ETH:False, BTC:False | default |
| CBETH | 0xd781...817d | ETH:False, BTC:False | default |
| sUSDe | 0x79cf...E533 | ETH:False, BTC:False | default |
| VIRTUAL | 0xEaf3...19F7 | ETH:False, BTC:False | default |
| VVV | 0x8eC6...873F | ETH:False, BTC:False | default |
| WELL | 0xc15d...C5fe | ETH:False, BTC:False | default |
| DEGEN | 0xE62B...99c2 | ETH:False, BTC:False | default |
| EURC | 0xDAe3...8250 | ETH:False, BTC:False | default |
| GHO | 0x4286...79b0 | ETH:False, BTC:False | default |
| USDS | 0x2330...2930 | ETH:False, BTC:False | default |
| SUPER_OETH | 0x39C6...10B4 | ETH:True, BTC:False | default |

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
| GREEN | Curve Pool | - | - |
| GREEN/USDC | Curve Pool | - | - |

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
| 0x784e...cE89 | AERO | CompoundV3, snaps:20 | default |
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
Address: 0x4dfbFaC4592699A84377C7E8d6Be8d0fEDb4b9c0

## Pyth Prices Global Config
| Parameter | Value |
| --- | --- |
| isPaused | False |
| numAssets | 5 |

### Pyth Prices - Registered Assets (5)
| Asset | Feed/Underlying | Config | StaleTime |
| --- | --- | --- | --- |
| COOKIE | 0xa73331cc...9a7a0191 | - | default |
| KAITO | 0x7302dee6...692b7e59 | - | default |
| AIXBT | 0x0fc54579...b638a5a7 | - | default |
| KTA | 0x61fb0189...34c74084 | - | default |
| ZORA | 0x93eacee7...3f5666b1 | - | default |

## Stork Prices
Address: 0xd83187f7484FE9b92334d2a5bbCC6dDdA3E4e774

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
| undyEURC | EURC | ID:0, snaps:20 | default |
| undyAERO | AERO | ID:0, snaps:20 | default |
| undyBTC | CBBTC | ID:0, snaps:20 | default |
| undyETH | WETH | ID:0, snaps:20 | default |
| undyUSD | USDC | ID:0, snaps:20 | default |
| undyUSD | USDC | ID:0, snaps:20 | default |
| undyETH | WETH | ID:0, snaps:20 | default |
| undyBTC | CBBTC | ID:0, snaps:20 | default |
| undyAERO | AERO | ID:0, snaps:20 | default |
| undyEURC | EURC | ID:0, snaps:20 | default |

================================================================================

<a id="token-statistics"></a>
# Token Statistics

## GREEN Token
| Parameter | Value |
| --- | --- |
| totalSupply | 202.46K GREEN |
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
| totalSupply (shares) | 56.25K GREEN |
| totalAssets (GREEN) | 59.40K GREEN |
| **Exchange Rate** | **1.055864 GREEN per sGREEN** |
| **Accumulated Yield** | **+5.5864%** above 1:1 |
| decimals | 18 |
| name | Savings Green USD |
| symbol | sGREEN |

*Example: 1,000 sGREEN = 1,055.8639 GREEN*

================================================================================

---
*Report generated at block 38663660 on 2025-11-26 00:29:37 UTC*
