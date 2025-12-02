================================================================================
# Ripe Protocol - Vault Configurations

**Generated:** 2025-12-02 04:55:34 UTC
**Block:** 38930978
**Network:** Base Mainnet

Detailed configuration for all vaults registered in VaultBook.


## Table of Contents

1. [VaultBook Overview](#vault-book-overview)
2. [Vault Configurations](#vault-configs)

   - [Stability Pool](#stability-pool)
   - [Ripe Gov Vault](#ripe-gov-vault)
   - [Simple ERC20 Vault](#simple-erc20-vault)
   - [Rebase ERC20 Vault](#rebase-erc20-vault)
   - [Underscore Vault](#underscore-vault)

<a id="vault-book-overview"></a>
## VaultBook Overview

Address: `0xB758e30C14825519b895Fd9928d5d8748A71a944`


### Registry Config (AddressRegistry Module)
| Parameter | Value |
| --- | --- |
| numAddrs (vaults) | 5 |
| registryChangeTimeLock | 21600 blocks (~12.0h) |

### Governance Settings (LocalGov Module)
| Parameter | Value |
| --- | --- |
| governance | None |
| govChangeTimeLock | 43200 blocks (~1.0d) |
| pendingGov | None |

### Registered Vaults

| Reg ID | Description | Address |
| --- | --- | --- |
| 1 | Stability Pool | `0x2a157096af6337b2b4bd47de435520572ed5a439` |
| 2 | Ripe Gov Vault | `0xe42b3dC546527EB70D741B185Dc57226cA01839D` |
| 3 | Simple ERC20 Vault | `0xf75b566eF80Fde0dEfcC045A4d57b540eb43ddfD` |
| 4 | Rebase ERC20 Vault | `0xce2E96C9F6806731914A7b4c3E4aC1F296d98597` |
| 5 | Underscore Vault | `0x4549A368c00f803862d457C4C0c659a293F26C66` |

<a id="vault-configs"></a>
## Vault Configurations

<a id="stability-pool"></a>
### Stability Pool
Address: `0x2a157096af6337b2b4bd47de435520572ed5a439`

#### Vault Status
| Parameter | Value |
| --- | --- |
| isPaused | False |
| numAssets | 2 |

#### Assets in Vault (2)
| Asset | Address | Total Balance |
| --- | --- | --- |
| sGREEN | `0xaa0f13488CE069A7B5a099457c753A7CFBE04d36` | 53.99K  |
| GREEN/USDC | `0xd6c283655B42FA0eb2685F7AB819784F071459dc` | 59.39K  |

#### Claimable Assets by Stability Pool Asset

**sGREEN** (`0xaa0f13488CE069A7B5a099457c753A7CFBE04d36`)
- No claimable assets

**GREEN/USDC** (`0xd6c283655B42FA0eb2685F7AB819784F071459dc`)
- Num Claimable Assets: 9
  - VVV: 0.000000000000000001 VVV
  - AERO: 0.000000000000000001 AERO
  - WETH: 0.000362059480465854 WETH
  - WRAPPED_SUPER_OETH: 0.000000000000000001 WRAPPED_SUPER_OETH
  - MOONWELL_CBETH: 0.00000001 MOONWELL_CBETH
  - WELL: 0.000000000000000056 WELL
  - CBDOGE: 0.00000001 CBDOGE
  - GREEN: 0.000000000000000001 GREEN
  - WELL: 0.000000000000000056 WELL

#### Total Claimable Balances (across all stability pools)
| Asset | Total Claimable Balance |
| --- | --- |
| MOONWELL_CBETH | 0.00000001 MOONWELL_CBETH |
| WETH | 0.000362059480465854 WETH |
| WRAPPED_SUPER_OETH | 0.000000000000000001 WRAPPED_SUPER_OETH |
| AERO | 0.000000000000000001 AERO |
| WELL | 0.000000000000000056 WELL |
| VVV | 0.000000000000000001 VVV |
| CBDOGE | 0.00000001 CBDOGE |
| GREEN | 0.000000000000000001 GREEN |

---

<a id="ripe-gov-vault"></a>
### Ripe Gov Vault
Address: `0xe42b3dC546527EB70D741B185Dc57226cA01839D`

#### Vault Status
| Parameter | Value |
| --- | --- |
| isPaused | False |
| numAssets | 3 |
| totalGovPoints | 104,140,151,492,233,437,230 |

#### Assets in Vault (3)
| Asset | Address | Total Balance |
| --- | --- | --- |
| RIPE_TOKEN | `0x2A0a59d6B975828e781EcaC125dBA40d7ee5dDC0` | 270.43K  |
| RIPE/WETH | `0xF8D92a9531205AB2Dd0Bc623CDF4A6Ab4c3a2526` | 0.00  |
| RIPE_WETH_POOL | `0x765824aD2eD0ECB70ECc25B0Cf285832b335d6A9` | 228.29  |

---

<a id="simple-erc20-vault"></a>
### Simple ERC20 Vault
Address: `0xf75b566eF80Fde0dEfcC045A4d57b540eb43ddfD`

#### Vault Status
| Parameter | Value |
| --- | --- |
| isPaused | False |
| numAssets | 27 |

#### Assets in Vault (27)
| Asset | Address | Total Balance |
| --- | --- | --- |
| USDC | `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` | 762.51  |
| CBBTC | `0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf` | 0.02  |
| WETH | `0x4200000000000000000000000000000000000006` | 1.57  |
| CBDOGE | `0xcbD06E5A2B0C65597161de254AA074E489dEb510` | 285.30  |
| USOL | `0x9B8Df6E244526ab5F6e6400d331DB28C8fdDdb55` | 1.70  |
| MORPHO_SPARK_USDC | `0x7BfA7C4f149E7415b73bdeDfe609237e29CBF34A` | 7.14K  |
| AERO | `0x940181a94A35A4569E4529A3CDfB74e38FD98631` | 1.30K  |
| MOONWELL_AERO | `0x73902f619CEB9B31FD8EFecf435CbDf89E369Ba6` | 0.00  |
| cbXRP | `0xcb585250f852C6c6bf90434AB21A00f02833a4af` | 0.00  |
| WELL | `0xA88594D404727625A9437C3f886C7643872296AE` | 11.99K  |
| VIRTUAL | `0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b` | 1.11K  |
| VVV | `0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf` | 295.05  |
| DEGEN | `0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed` | 145.66K  |
| MOONWELL_CBETH | `0x3bf93770f2d4a794c3d9EBEfBAeBAE2a8f09A5E5` | 0.00  |
| CBETH | `0x2Ae3F1Ec7F1F5012CFEab0185bfc7aa3cf0DEc22` | 0.80  |
| MOONWELL_USDC | `0xEdc817A28E8B93B03976FBd4a3dDBc9f7D176c22` | 45.58  |
| MORPHO_MOONWELL_USDC | `0xc1256Ae5FF1cf2719D4937adb3bbCCab2E00A2Ca` | 0.00  |
| MORPHO_SEAMLESS_USDC | `0x616a4E1db48e22028f6bbf20444Cd3b8e3273738` | 5.83K  |
| FLUID_USDC | `0xf42f5795D9ac7e9D757dB633D693cD548Cfd9169` | 5.88K  |
| EULER_USDC | `0x0A1a3b5f2041F33522C4efc754a7D096f880eE16` | 0.00  |
| MOONWELL_CBBTC | `0xF877ACaFA28c19b96727966690b2f44d35aD5976` | 0.00  |
| MORPHO_MOONWELL_WETH | `0xa0E430870c4604CcfC7B38Ca7845B1FF653D0ff1` | 0.00  |
| MORPHO_SEAMLESS_WETH | `0x27D8c7273fd3fcC6956a0B370cE5Fd4A7fc65c18` | 0.13  |
| EULER_WETH | `0x859160DB5841E5cfB8D3f144C6b3381A85A4b410` | 0.00  |
| MORPHO_MOONWELL_CBBTC | `0x543257eF2161176D7C8cD90BA65C2d4CaEF5a796` | 0.00  |
| sUSDe | `0x211Cc4DD073734dA055fbF44a2b4667d5E5fE5d2` | 0.83  |
| WRAPPED_SUPER_OETH | `0x7FcD174E80f264448ebeE8c88a7C4476AAF58Ea6` | 0.37  |

---

<a id="rebase-erc20-vault"></a>
### Rebase ERC20 Vault
Address: `0xce2E96C9F6806731914A7b4c3E4aC1F296d98597`

#### Vault Status
| Parameter | Value |
| --- | --- |
| isPaused | False |
| numAssets | 6 |

#### Assets in Vault (6)
| Asset | Address | Total Balance |
| --- | --- | --- |
| 0x784efeB622244d2348d4F2522f8860B96fbEcE89 | `0x784efeB622244d2348d4F2522f8860B96fbEcE89` | 0.00  |
| AAVEV3_CBBTC | `0xBdb9300b7CDE636d9cD4AFF00f6F009fFBBc8EE6` | 0.00  |
| AAVEV3_USDC | `0x4e65fE4DbA92790696d040ac24Aa414708F5c0AB` | 5.28K  |
| AAVEV3_WETH | `0xD4a0e0b9149BCee3C920d2E00b5dE09138fd8bb7` | 0.87  |
| COMPOUNDV3_USDC | `0xb125E6687d4313864e53df431d5425969c15Eb2F` | 0.00  |
| COMPOUNDV3_WETH | `0x46e6b214b524310239732D51387075E0e70970bf` | 0.00  |

---

<a id="underscore-vault"></a>
### Underscore Vault
Address: `0x4549A368c00f803862d457C4C0c659a293F26C66`

#### Vault Status
| Parameter | Value |
| --- | --- |
| isPaused | False |
| numAssets | 8 |

#### Assets in Vault (8)
| Asset | Address | Total Balance |
| --- | --- | --- |
| UNDY_USD | `0xcF9F72237d4135a6D8b3ee717DC414Ae5b56E41e` | 0.00  |
| UNDY_ETH | `0x01ECc16CE82CCf7e6f734351d5d3AdCf2f8D3497` | 0.00  |
| UNDY_BTC | `0x4cD99832E44D1154bd7841f5E5E9ce66dA0437d4` | 0.00  |
| undyUSD | `0xcdD894E6c11d6444e0c3d974928Dd71b28b09356` | 0.00  |
| undyUSD | `0xb33852cfd0c22647AAC501a6Af59Bc4210a686Bf` | 103.07K  |
| undyBTC | `0x3fb0fC9D3Ddd543AD1b748Ed2286a022f4638493` | 0.00  |
| undyETH | `0x02981DB1a99A14912b204437e7a2E02679B57668` | 0.01  |
| undyAERO | `0x96F1a7ce331F40afe866F3b707c223e377661087` | 16.66  |

---

================================================================================

---
*Report generated at block 38930978 on 2025-12-02 04:57:01 UTC*
