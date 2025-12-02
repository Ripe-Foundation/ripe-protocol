================================================================================
# Ripe Protocol - Asset Configurations

**Generated:** 2025-12-02 04:53:28 UTC
**Block:** 38930870
**Network:** Base Mainnet

Detailed configuration for all registered assets in MissionControl.


## Table of Contents

1. [Registered Assets Overview](#assets-overview)
2. [Per-Asset Configurations](#per-asset-configs)

   - [USDC](#usdc)
   - [CBBTC](#cbbtc)
   - [WETH](#weth)
   - [sGREEN](#sgreen)
   - [GREEN/USDC](#green/usdc)
   - [RIPE_TOKEN](#ripe_token)
   - [RIPE/WETH](#ripe/weth)
   - [CBDOGE](#cbdoge)
   - [USOL](#usol)
   - [RIPE_WETH_POOL](#ripe_weth_pool)
   - [MORPHO_SPARK_USDC](#morpho_spark_usdc)
   - [AERO](#aero)
   - [0x784efeB622244d2348d4F2522f8860B96fbEcE89](#0x784efeb622244d2348d4f2522f8860b96fbece89)
   - [MOONWELL_AERO](#moonwell_aero)
   - [AAVEV3_USDC](#aavev3_usdc)
   - [AAVEV3_CBBTC](#aavev3_cbbtc)
   - [AAVEV3_WETH](#aavev3_weth)
   - [VIRTUAL](#virtual)
   - [cbADA](#cbada)
   - [cbXRP](#cbxrp)
   - [cbLTC](#cbltc)
   - [VVV](#vvv)
   - [WELL](#well)
   - [DEGEN](#degen)
   - [COMPOUNDV3_WETH](#compoundv3_weth)
   - [MORPHO_MOONWELL_WETH](#morpho_moonwell_weth)
   - [MORPHO_SEAMLESS_WETH](#morpho_seamless_weth)
   - [EULER_WETH](#euler_weth)
   - [CBETH](#cbeth)
   - [MOONWELL_CBETH](#moonwell_cbeth)
   - [COMPOUNDV3_USDC](#compoundv3_usdc)
   - [MOONWELL_USDC](#moonwell_usdc)
   - [EULER_USDC](#euler_usdc)
   - [FLUID_USDC](#fluid_usdc)
   - [MORPHO_MOONWELL_USDC](#morpho_moonwell_usdc)
   - [MORPHO_SEAMLESS_USDC](#morpho_seamless_usdc)
   - [EULER_CBBTC](#euler_cbbtc)
   - [MOONWELL_CBBTC](#moonwell_cbbtc)
   - [MORPHO_MOONWELL_CBBTC](#morpho_moonwell_cbbtc)
   - [sUSDe](#susde)
   - [WRAPPED_SUPER_OETH](#wrapped_super_oeth)
   - [GREEN](#green)
   - [UNDY_USD](#undy_usd)
   - [UNDY_ETH](#undy_eth)
   - [UNDY_BTC](#undy_btc)
   - [undyUSD](#undyusd)
   - [undyETH](#undyeth)
   - [undyBTC](#undybtc)
   - [undyAERO](#undyaero)
   - [undyEURC](#undyeurc)
   - [undyETH](#undyeth)
   - [undyBTC](#undybtc)
   - [undyUSD](#undyusd)
   - [undyAERO](#undyaero)
   - [undyEURC](#undyeurc)

<a id="assets-overview"></a>
## Registered Assets Overview

*55 total registered assets*

| Asset | Vault IDs | LTV | Liq Threshold | Borrow Rate | canDeposit | canBorrow |
| --- | --- | --- | --- | --- | --- | --- |
| USDC (`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`) | 3 | 80.00% | 90.00% | 5.00% | True | True |
| CBBTC (`0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf`) | 3 | 70.00% | 80.00% | 7.00% | True | True |
| WETH (`0x4200000000000000000000000000000000000006`) | 3 | 70.00% | 80.00% | 7.00% | True | True |
| sGREEN (`0xaa0f13488CE069A7B5a099457c753A7CFBE04d36`) | 1 | 0.00% | 0.00% | 0.00% | True | False |
| GREEN/USDC (`0xd6c283655B42FA0eb2685F7AB819784F071459dc`) | 1 | 0.00% | 0.00% | 0.00% | True | False |
| RIPE_TOKEN (`0x2A0a59d6B975828e781EcaC125dBA40d7ee5dDC0`) | 2 | 0.00% | 0.00% | 0.00% | True | False |
| RIPE/WETH (`0xF8D92a9531205AB2Dd0Bc623CDF4A6Ab4c3a2526`) | 2 | 0.00% | 0.00% | 0.00% | False | False |
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
| cbADA (`0xcbADA732173e39521CDBE8bf59a6Dc85A9fc7b8c`) | 3 | 50.00% | 65.00% | 11.00% | True | True |
| cbXRP (`0xcb585250f852C6c6bf90434AB21A00f02833a4af`) | 3 | 50.00% | 65.00% | 11.00% | True | True |
| cbLTC (`0xcb17C9Db87B595717C857a08468793f5bAb6445F`) | 3 | 50.00% | 65.00% | 11.00% | True | True |
| VVV (`0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf`) | 3 | 40.00% | 50.00% | 13.00% | True | True |
| WELL (`0xA88594D404727625A9437C3f886C7643872296AE`) | 3 | 40.00% | 50.00% | 13.00% | True | True |
| DEGEN (`0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed`) | 3 | 40.00% | 50.00% | 13.00% | True | True |
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
| sUSDe (`0x211Cc4DD073734dA055fbF44a2b4667d5E5fE5d2`) | 3 | 80.00% | 90.00% | 5.00% | True | True |
| WRAPPED_SUPER_OETH (`0x7FcD174E80f264448ebeE8c88a7C4476AAF58Ea6`) | 3 | 70.00% | 80.00% | 7.00% | True | True |
| GREEN (`0xd1Eac76497D06Cf15475A5e3984D5bC03de7C707`) | None | 0.00% | 0.00% | 0.00% | False | False |
| UNDY_USD (`0xcF9F72237d4135a6D8b3ee717DC414Ae5b56E41e`) | 5 | 80.00% | 90.00% | 5.00% | False | True |
| UNDY_ETH (`0x01ECc16CE82CCf7e6f734351d5d3AdCf2f8D3497`) | 5 | 70.00% | 80.00% | 7.00% | False | True |
| UNDY_BTC (`0x4cD99832E44D1154bd7841f5E5E9ce66dA0437d4`) | 5 | 70.00% | 80.00% | 7.00% | False | True |
| undyUSD (`0xcdD894E6c11d6444e0c3d974928Dd71b28b09356`) | 5 | 80.00% | 90.00% | 5.00% | False | True |
| undyETH (`0x434696F22EF3862f14C6Abd008f18456418f7457`) | 5 | 70.00% | 80.00% | 7.00% | False | True |
| undyBTC (`0x897b56836C79e68042EFc51be7ad652a4BBFb86b`) | 5 | 70.00% | 80.00% | 7.00% | False | True |
| undyAERO (`0x9e629632c483235845E27840C304C11b59d2FEDa`) | 5 | 50.00% | 65.00% | 8.00% | False | True |
| undyEURC (`0x4bCa2A052428D7b7D2E1Daf9e1af471EA4c2F7bf`) | 5 | 80.00% | 90.00% | 5.00% | False | True |
| undyETH (`0x02981DB1a99A14912b204437e7a2E02679B57668`) | 5 | 70.00% | 80.00% | 7.00% | True | True |
| undyBTC (`0x3fb0fC9D3Ddd543AD1b748Ed2286a022f4638493`) | 5 | 70.00% | 80.00% | 7.00% | True | True |
| undyUSD (`0xb33852cfd0c22647AAC501a6Af59Bc4210a686Bf`) | 5 | 80.00% | 90.00% | 5.00% | True | True |
| undyAERO (`0x96F1a7ce331F40afe866F3b707c223e377661087`) | 5 | 50.00% | 65.00% | 8.00% | True | True |
| undyEURC (`0x1cb8DAB80f19fC5Aca06C2552AECd79015008eA8`) | 5 | 80.00% | 90.00% | 5.00% | True | True |

<a id="per-asset-configs"></a>
## Per-Asset Configurations

<a id="usdc"></a>
### USDC
Address: `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 100.000000 |
| globalDepositLimit | 1,000.000000 |
| minDepositBalance | 0.250000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 80.00% |
| redemptionThreshold | 85.00% |
| liqThreshold | 90.00% |
| liqFee | 5.00% |
| borrowRate | 5.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="cbbtc"></a>
### CBBTC
Address: `0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 2.500000 |
| globalDepositLimit | 25.000000 |
| minDepositBalance | 0.000025 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="weth"></a>
### WETH
Address: `0x4200000000000000000000000000000000000006`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 800,000,000,000.000000 |
| globalDepositLimit | 8,000,000,000,000.000000 |
| minDepositBalance | 80,000,000.000000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="sgreen"></a>
### sGREEN
Address: `0xaa0f13488CE069A7B5a099457c753A7CFBE04d36`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 1 |
| stakersPointsAlloc | 15.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 100,000,000,000,000,000,000.000000 |
| globalDepositLimit | 1,000,000,000,000,000,000,000.000000 |
| minDepositBalance | 10,000,000,000.000000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 0.00% |
| redemptionThreshold | 0.00% |
| liqThreshold | 0.00% |
| liqFee | 0.00% |
| borrowRate | 0.00% |
| daowry | 0.00% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | True |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="green/usdc"></a>
### GREEN/USDC
Address: `0xd6c283655B42FA0eb2685F7AB819784F071459dc`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 1 |
| stakersPointsAlloc | 25.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 100,000,000,000,000,000,000.000000 |
| globalDepositLimit | 1,000,000,000,000,000,000,000.000000 |
| minDepositBalance | 10,000,000,000.000000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 0.00% |
| redemptionThreshold | 0.00% |
| liqThreshold | 0.00% |
| liqFee | 0.00% |
| borrowRate | 0.00% |
| daowry | 0.00% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="ripe_token"></a>
### RIPE_TOKEN
Address: `0x2A0a59d6B975828e781EcaC125dBA40d7ee5dDC0`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 2 |
| stakersPointsAlloc | 15.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 100,000,000,000,000,000,000.000000 |
| globalDepositLimit | 1,000,000,000,000,000,000,000.000000 |
| minDepositBalance | 100,000,000.000000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 0.00% |
| redemptionThreshold | 0.00% |
| liqThreshold | 0.00% |
| liqFee | 0.00% |
| borrowRate | 0.00% |
| daowry | 0.00% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="ripe/weth"></a>
### RIPE/WETH
Address: `0xF8D92a9531205AB2Dd0Bc623CDF4A6Ab4c3a2526`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 2 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 100,000,000,000,000,000,000.000000 |
| globalDepositLimit | 1,000,000,000,000,000,000,000.000000 |
| minDepositBalance | 1,000,000,000.000000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 0.00% |
| redemptionThreshold | 0.00% |
| liqThreshold | 0.00% |
| liqFee | 0.00% |
| borrowRate | 0.00% |
| daowry | 0.00% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="cbdoge"></a>
### CBDOGE
Address: `0xcbD06E5A2B0C65597161de254AA074E489dEb510`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 1,500,000.000000 |
| globalDepositLimit | 15,000,000.000000 |
| minDepositBalance | 150.000000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 50.00% |
| redemptionThreshold | 60.00% |
| liqThreshold | 65.00% |
| liqFee | 12.00% |
| borrowRate | 11.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="usol"></a>
### USOL
Address: `0x9B8Df6E244526ab5F6e6400d331DB28C8fdDdb55`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 15,000,000,000,000.000000 |
| globalDepositLimit | 150,000,000,000,000.000000 |
| minDepositBalance | 1,500,000,000.000000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 50.00% |
| redemptionThreshold | 60.00% |
| liqThreshold | 65.00% |
| liqFee | 12.00% |
| borrowRate | 11.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="ripe_weth_pool"></a>
### RIPE_WETH_POOL
Address: `0x765824aD2eD0ECB70ECc25B0Cf285832b335d6A9`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 2 |
| stakersPointsAlloc | 45.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 100,000,000,000,000,000,000.000000 |
| globalDepositLimit | 1,000,000,000,000,000,000,000.000000 |
| minDepositBalance | 1,000,000,000.000000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 0.00% |
| redemptionThreshold | 0.00% |
| liqThreshold | 0.00% |
| liqFee | 0.00% |
| borrowRate | 0.00% |
| daowry | 0.00% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="morpho_spark_usdc"></a>
### MORPHO_SPARK_USDC
Address: `0x7BfA7C4f149E7415b73bdeDfe609237e29CBF34A`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 3,000,000,000,000,000.000000 |
| globalDepositLimit | 30,000,000,000,000,000.000000 |
| minDepositBalance | 300,000,000,000.000000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 80.00% |
| redemptionThreshold | 82.00% |
| liqThreshold | 85.00% |
| liqFee | 5.00% |
| borrowRate | 5.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="aero"></a>
### AERO
Address: `0x940181a94A35A4569E4529A3CDfB74e38FD98631`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 3,000,000,000,000,000.000000 |
| globalDepositLimit | 30,000,000,000,000,000.000000 |
| minDepositBalance | 1,000,000,000,000.000000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 50.00% |
| redemptionThreshold | 60.00% |
| liqThreshold | 65.00% |
| liqFee | 10.00% |
| borrowRate | 8.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="0x784efeb622244d2348d4f2522f8860b96fbece89"></a>
### 0x784efeB622244d2348d4F2522f8860B96fbEcE89
Address: `0x784efeB622244d2348d4F2522f8860B96fbEcE89`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 4 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 3,000,000,000,000,000.000000 |
| globalDepositLimit | 30,000,000,000,000,000.000000 |
| minDepositBalance | 1,000,000,000,000.000000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 50.00% |
| redemptionThreshold | 60.00% |
| liqThreshold | 65.00% |
| liqFee | 10.00% |
| borrowRate | 8.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="moonwell_aero"></a>
### MOONWELL_AERO
Address: `0x73902f619CEB9B31FD8EFecf435CbDf89E369Ba6`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 13,000,000.000000 |
| globalDepositLimit | 130,000,000.000000 |
| minDepositBalance | 1,000.000000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 50.00% |
| redemptionThreshold | 60.00% |
| liqThreshold | 65.00% |
| liqFee | 10.00% |
| borrowRate | 8.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="aavev3_usdc"></a>
### AAVEV3_USDC
Address: `0x4e65fE4DbA92790696d040ac24Aa414708F5c0AB`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 4 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 3,000.000000 |
| globalDepositLimit | 30,000.000000 |
| minDepositBalance | 1.000000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 80.00% |
| redemptionThreshold | 82.00% |
| liqThreshold | 85.00% |
| liqFee | 5.00% |
| borrowRate | 5.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="aavev3_cbbtc"></a>
### AAVEV3_CBBTC
Address: `0xBdb9300b7CDE636d9cD4AFF00f6F009fFBBc8EE6`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 4 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 2.500000 |
| globalDepositLimit | 25.000000 |
| minDepositBalance | 0.000025 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="aavev3_weth"></a>
### AAVEV3_WETH
Address: `0xD4a0e0b9149BCee3C920d2E00b5dE09138fd8bb7`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 4 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 800,000,000,000.000000 |
| globalDepositLimit | 8,000,000,000,000.000000 |
| minDepositBalance | 80,000,000.000000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="virtual"></a>
### VIRTUAL
Address: `0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 2,000,000,000,000,000.000000 |
| globalDepositLimit | 20,000,000,000,000,000.000000 |
| minDepositBalance | 1,000,000,000,000.000000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 50.00% |
| redemptionThreshold | 60.00% |
| liqThreshold | 65.00% |
| liqFee | 12.00% |
| borrowRate | 11.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="cbada"></a>
### cbADA
Address: `0xcbADA732173e39521CDBE8bf59a6Dc85A9fc7b8c`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 3,750.000000 |
| globalDepositLimit | 37,500.000000 |
| minDepositBalance | 1.000000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 50.00% |
| redemptionThreshold | 60.00% |
| liqThreshold | 65.00% |
| liqFee | 12.00% |
| borrowRate | 11.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="cbxrp"></a>
### cbXRP
Address: `0xcb585250f852C6c6bf90434AB21A00f02833a4af`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 1,000.000000 |
| globalDepositLimit | 10,000.000000 |
| minDepositBalance | 0.333333 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 50.00% |
| redemptionThreshold | 60.00% |
| liqThreshold | 65.00% |
| liqFee | 12.00% |
| borrowRate | 11.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="cbltc"></a>
### cbLTC
Address: `0xcb17C9Db87B595717C857a08468793f5bAb6445F`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 2,500.000000 |
| globalDepositLimit | 25,000.000000 |
| minDepositBalance | 0.800000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 50.00% |
| redemptionThreshold | 60.00% |
| liqThreshold | 65.00% |
| liqFee | 12.00% |
| borrowRate | 11.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="vvv"></a>
### VVV
Address: `0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 1,100,000,000,000,000.000000 |
| globalDepositLimit | 11,000,000,000,000,000.000000 |
| minDepositBalance | 110,000,000,000.000000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 40.00% |
| redemptionThreshold | 45.00% |
| liqThreshold | 50.00% |
| liqFee | 15.00% |
| borrowRate | 13.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="well"></a>
### WELL
Address: `0xA88594D404727625A9437C3f886C7643872296AE`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 100,000,000,000,000,000.000000 |
| globalDepositLimit | 1,000,000,000,000,000,000.000000 |
| minDepositBalance | 10,000,000,000,000.000000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 40.00% |
| redemptionThreshold | 45.00% |
| liqThreshold | 50.00% |
| liqFee | 15.00% |
| borrowRate | 13.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="degen"></a>
### DEGEN
Address: `0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 750,000,000,000,000,000.000000 |
| globalDepositLimit | 7,500,000,000,000,000,000.000000 |
| minDepositBalance | 75,000,000,000,000.000000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 40.00% |
| redemptionThreshold | 45.00% |
| liqThreshold | 50.00% |
| liqFee | 15.00% |
| borrowRate | 13.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="compoundv3_weth"></a>
### COMPOUNDV3_WETH
Address: `0x46e6b214b524310239732D51387075E0e70970bf`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 4 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 800,000,000,000.000000 |
| globalDepositLimit | 8,000,000,000,000.000000 |
| minDepositBalance | 80,000,000.000000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="morpho_moonwell_weth"></a>
### MORPHO_MOONWELL_WETH
Address: `0xa0E430870c4604CcfC7B38Ca7845B1FF653D0ff1`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 800,000,000,000.000000 |
| globalDepositLimit | 8,000,000,000,000.000000 |
| minDepositBalance | 80,000,000.000000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="morpho_seamless_weth"></a>
### MORPHO_SEAMLESS_WETH
Address: `0x27D8c7273fd3fcC6956a0B370cE5Fd4A7fc65c18`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 800,000,000,000.000000 |
| globalDepositLimit | 8,000,000,000,000.000000 |
| minDepositBalance | 80,000,000.000000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="euler_weth"></a>
### EULER_WETH
Address: `0x859160DB5841E5cfB8D3f144C6b3381A85A4b410`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 800,000,000,000.000000 |
| globalDepositLimit | 8,000,000,000,000.000000 |
| minDepositBalance | 80,000,000.000000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="cbeth"></a>
### CBETH
Address: `0x2Ae3F1Ec7F1F5012CFEab0185bfc7aa3cf0DEc22`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 800,000,000,000.000000 |
| globalDepositLimit | 8,000,000,000,000.000000 |
| minDepositBalance | 80,000,000.000000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="moonwell_cbeth"></a>
### MOONWELL_CBETH
Address: `0x3bf93770f2d4a794c3d9EBEfBAeBAE2a8f09A5E5`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 3,300.000000 |
| globalDepositLimit | 33,000.000000 |
| minDepositBalance | 0.330000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="compoundv3_usdc"></a>
### COMPOUNDV3_USDC
Address: `0xb125E6687d4313864e53df431d5425969c15Eb2F`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 4 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 6,000.000000 |
| globalDepositLimit | 60,000.000000 |
| minDepositBalance | 0.010000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 80.00% |
| redemptionThreshold | 85.00% |
| liqThreshold | 90.00% |
| liqFee | 5.00% |
| borrowRate | 5.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="moonwell_usdc"></a>
### MOONWELL_USDC
Address: `0xEdc817A28E8B93B03976FBd4a3dDBc9f7D176c22`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 27,500,000.000000 |
| globalDepositLimit | 275,000,000.000000 |
| minDepositBalance | 45.600000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 80.00% |
| redemptionThreshold | 85.00% |
| liqThreshold | 90.00% |
| liqFee | 5.00% |
| borrowRate | 5.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="euler_usdc"></a>
### EULER_USDC
Address: `0x0A1a3b5f2041F33522C4efc754a7D096f880eE16`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 6,000.000000 |
| globalDepositLimit | 60,000.000000 |
| minDepositBalance | 0.010000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 80.00% |
| redemptionThreshold | 85.00% |
| liqThreshold | 90.00% |
| liqFee | 5.00% |
| borrowRate | 5.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="fluid_usdc"></a>
### FLUID_USDC
Address: `0xf42f5795D9ac7e9D757dB633D693cD548Cfd9169`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 6,000.000000 |
| globalDepositLimit | 60,000.000000 |
| minDepositBalance | 0.010000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 80.00% |
| redemptionThreshold | 85.00% |
| liqThreshold | 90.00% |
| liqFee | 5.00% |
| borrowRate | 5.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="morpho_moonwell_usdc"></a>
### MORPHO_MOONWELL_USDC
Address: `0xc1256Ae5FF1cf2719D4937adb3bbCCab2E00A2Ca`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 6,000,000,000,000,000.000000 |
| globalDepositLimit | 60,000,000,000,000,000.000000 |
| minDepositBalance | 10,000,000,000.000000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 80.00% |
| redemptionThreshold | 85.00% |
| liqThreshold | 90.00% |
| liqFee | 5.00% |
| borrowRate | 5.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="morpho_seamless_usdc"></a>
### MORPHO_SEAMLESS_USDC
Address: `0x616a4E1db48e22028f6bbf20444Cd3b8e3273738`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 6,000,000,000,000,000.000000 |
| globalDepositLimit | 60,000,000,000,000,000.000000 |
| minDepositBalance | 10,000,000,000.000000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 80.00% |
| redemptionThreshold | 85.00% |
| liqThreshold | 90.00% |
| liqFee | 5.00% |
| borrowRate | 5.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="euler_cbbtc"></a>
### EULER_CBBTC
Address: `0x882018411Bc4A020A879CEE183441fC9fa5D7f8B`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 5.000000 |
| globalDepositLimit | 50.000000 |
| minDepositBalance | 0.000025 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="moonwell_cbbtc"></a>
### MOONWELL_CBBTC
Address: `0xF877ACaFA28c19b96727966690b2f44d35aD5976`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 266.000000 |
| globalDepositLimit | 2,660.000000 |
| minDepositBalance | 0.000443 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="morpho_moonwell_cbbtc"></a>
### MORPHO_MOONWELL_CBBTC
Address: `0x543257eF2161176D7C8cD90BA65C2d4CaEF5a796`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 50,000,000,000.000000 |
| globalDepositLimit | 500,000,000,000.000000 |
| minDepositBalance | 2,500,000.000000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="susde"></a>
### sUSDe
Address: `0x211Cc4DD073734dA055fbF44a2b4667d5E5fE5d2`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 6,000,000,000,000,000.000000 |
| globalDepositLimit | 60,000,000,000,000,000.000000 |
| minDepositBalance | 10,000,000,000.000000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 80.00% |
| redemptionThreshold | 85.00% |
| liqThreshold | 90.00% |
| liqFee | 5.00% |
| borrowRate | 5.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="wrapped_super_oeth"></a>
### WRAPPED_SUPER_OETH
Address: `0x7FcD174E80f264448ebeE8c88a7C4476AAF58Ea6`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 3 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 1,600,000,000,000.000000 |
| globalDepositLimit | 16,000,000,000,000.000000 |
| minDepositBalance | 80,000,000.000000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="green"></a>
### GREEN
Address: `0xd1Eac76497D06Cf15475A5e3984D5bC03de7C707`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | None |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 0.000001 |
| globalDepositLimit | 0.000002 |
| minDepositBalance | 0.000001 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 0.00% |
| redemptionThreshold | 0.00% |
| liqThreshold | 0.00% |
| liqFee | 0.00% |
| borrowRate | 0.00% |
| daowry | 0.00% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="undy_usd"></a>
### UNDY_USD
Address: `0xcF9F72237d4135a6D8b3ee717DC414Ae5b56E41e`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 5 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 100.000000 |
| globalDepositLimit | 1,000.000000 |
| minDepositBalance | 0.100000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 80.00% |
| redemptionThreshold | 85.00% |
| liqThreshold | 90.00% |
| liqFee | 5.00% |
| borrowRate | 5.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="undy_eth"></a>
### UNDY_ETH
Address: `0x01ECc16CE82CCf7e6f734351d5d3AdCf2f8D3497`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 5 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 25,000,000,000.000000 |
| globalDepositLimit | 250,000,000,000.000000 |
| minDepositBalance | 25,000,000.000000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="undy_btc"></a>
### UNDY_BTC
Address: `0x4cD99832E44D1154bd7841f5E5E9ce66dA0437d4`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 5 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 0.100000 |
| globalDepositLimit | 1.000000 |
| minDepositBalance | 0.000100 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="undyusd"></a>
### undyUSD
Address: `0xcdD894E6c11d6444e0c3d974928Dd71b28b09356`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 5 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 50,000.000000 |
| globalDepositLimit | 250,000.000000 |
| minDepositBalance | 0.100000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 80.00% |
| redemptionThreshold | 85.00% |
| liqThreshold | 90.00% |
| liqFee | 5.00% |
| borrowRate | 5.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="undyeth"></a>
### undyETH
Address: `0x434696F22EF3862f14C6Abd008f18456418f7457`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 5 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 250,000,000,000.000000 |
| globalDepositLimit | 2,500,000,000,000.000000 |
| minDepositBalance | 25,000,000.000000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="undybtc"></a>
### undyBTC
Address: `0x897b56836C79e68042EFc51be7ad652a4BBFb86b`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 5 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 1.000000 |
| globalDepositLimit | 10.000000 |
| minDepositBalance | 0.000100 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="undyaero"></a>
### undyAERO
Address: `0x9e629632c483235845E27840C304C11b59d2FEDa`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 5 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 100,000,000,000,000.000000 |
| globalDepositLimit | 1,000,000,000,000,000.000000 |
| minDepositBalance | 100,000,000,000.000000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 50.00% |
| redemptionThreshold | 60.00% |
| liqThreshold | 65.00% |
| liqFee | 12.00% |
| borrowRate | 8.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="undyeurc"></a>
### undyEURC
Address: `0x4bCa2A052428D7b7D2E1Daf9e1af471EA4c2F7bf`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 5 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 100.000000 |
| globalDepositLimit | 1,000.000000 |
| minDepositBalance | 0.100000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 80.00% |
| redemptionThreshold | 85.00% |
| liqThreshold | 90.00% |
| liqFee | 5.00% |
| borrowRate | 5.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="undyeth"></a>
### undyETH
Address: `0x02981DB1a99A14912b204437e7a2E02679B57668`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 5 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 250,000,000,000.000000 |
| globalDepositLimit | 2,500,000,000,000.000000 |
| minDepositBalance | 25,000,000.000000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="undybtc"></a>
### undyBTC
Address: `0x3fb0fC9D3Ddd543AD1b748Ed2286a022f4638493`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 5 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 1.000000 |
| globalDepositLimit | 10.000000 |
| minDepositBalance | 0.000100 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 70.00% |
| redemptionThreshold | 77.00% |
| liqThreshold | 80.00% |
| liqFee | 10.00% |
| borrowRate | 7.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="undyusd"></a>
### undyUSD
Address: `0xb33852cfd0c22647AAC501a6Af59Bc4210a686Bf`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 5 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 50,000.000000 |
| globalDepositLimit | 250,000.000000 |
| minDepositBalance | 0.100000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 80.00% |
| redemptionThreshold | 85.00% |
| liqThreshold | 90.00% |
| liqFee | 5.00% |
| borrowRate | 5.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="undyaero"></a>
### undyAERO
Address: `0x96F1a7ce331F40afe866F3b707c223e377661087`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 5 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 1,000,000,000,000,000.000000 |
| globalDepositLimit | 10,000,000,000,000,000.000000 |
| minDepositBalance | 100,000,000,000.000000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 50.00% |
| redemptionThreshold | 60.00% |
| liqThreshold | 65.00% |
| liqFee | 12.00% |
| borrowRate | 8.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | False |
| shouldSwapInStabPools | True |
| shouldAuctionInstantly | True |
| specialStabPoolId | None |

#### Action Flags
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

---

<a id="undyeurc"></a>
### undyEURC
Address: `0x1cb8DAB80f19fC5Aca06C2552AECd79015008eA8`

#### Deposit Settings
| Parameter | Value |
| --- | --- |
| vaultIds | 5 |
| stakersPointsAlloc | 0.00% |
| voterPointsAlloc | 0.00% |
| perUserDepositLimit | 1,000.000000 |
| globalDepositLimit | 10,000.000000 |
| minDepositBalance | 0.100000 |

#### Debt Terms
| Parameter | Value |
| --- | --- |
| ltv | 80.00% |
| redemptionThreshold | 85.00% |
| liqThreshold | 90.00% |
| liqFee | 5.00% |
| borrowRate | 5.00% |
| daowry | 0.25% |

#### Liquidation Settings
| Parameter | Value |
| --- | --- |
| shouldBurnAsPayment | False |
| shouldTransferToEndaoment | True |
| shouldSwapInStabPools | False |
| shouldAuctionInstantly | False |
| specialStabPoolId | None |

#### Action Flags
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

---

================================================================================

---
*Report generated at block 38930870 on 2025-12-02 04:53:45 UTC*
