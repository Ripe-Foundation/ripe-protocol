================================================================================
# Ripe Protocol - Price Source Configurations

**Generated:** 2025-12-02 04:53:56 UTC
**Block:** 38930921
**Network:** Base Mainnet

Detailed configuration for all price sources registered in PriceDesk.


## Table of Contents

1. [PriceDesk Overview](#price-desk-overview)
2. [Price Source Configurations](#price-source-configs)

   - [Chainlink](#chainlink)
   - [Curve Prices](#curve-prices)
   - [BlueChip Yield Prices](#bluechip-yield-prices)
   - [Pyth Prices](#pyth-prices)
   - [Stork Prices](#stork-prices)
   - [Aero Ripe Prices](#aero-ripe-prices)
   - [wsuperOETHb Prices](#wsuperoethb-prices)
   - [Undy Vault Prices](#undy-vault-prices)

<a id="price-desk-overview"></a>
## PriceDesk Overview

Address: `0x68564c6035e8Dc21F0Ce6CB9592dC47B59dE2Ff6`


### Constants
| Parameter | Value |
| --- | --- |
| ETH | ETH (`0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE`) |

### Registry Config (AddressRegistry Module)
| Parameter | Value |
| --- | --- |
| numAddrs (price sources) | 8 |
| registryChangeTimeLock | 0 blocks (~0s) |

### Governance Settings (LocalGov Module)
| Parameter | Value |
| --- | --- |
| governance | None |
| govChangeTimeLock | 43200 blocks (~1.0d) |
| pendingGov | None |

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

<a id="price-source-configs"></a>
## Price Source Configurations

<a id="chainlink"></a>
### Chainlink
Address: `0x253f55e455701fF0B835128f55668ed159aAB3D9`

#### Global Config
| Parameter | Value |
| --- | --- |
| isPaused | False |
| numAssets | 23 |

#### Governance Settings (LocalGov Module)
| Parameter | Value |
| --- | --- |
| governance | None |
| govChangeTimeLock | 43200 blocks (~1.0d) |
| pendingGov | None |

#### Timelock Settings (TimeLock Module)
| Parameter | Value |
| --- | --- |
| minActionTimeLock | 21600 blocks (~12.0h) |
| maxActionTimeLock | 302400 blocks (~7.0d) |
| actionTimeLock | 21600 blocks (~12.0h) |
| expiration | 302400 blocks (~7.0d) |

#### Registered Assets (23)
| Asset | Feed/Underlying | Config | StaleTime |
| --- | --- | --- | --- |
| ETH | CHAINLINK_ETH_USD (`0x71041dddad3595F9CEd3DcCFBe3D1F4b0a16Bb70`) | ETH:False, BTC:False | 0s |
| WETH | CHAINLINK_ETH_USD (`0x71041dddad3595F9CEd3DcCFBe3D1F4b0a16Bb70`) | ETH:False, BTC:False | 0s |
| BTC | CHAINLINK_BTC_USD (`0x64c911996D3c6aC71f9b455B1E8E7266BcbD848F`) | ETH:False, BTC:False | 0s |
| USDC | CHAINLINK_USDC_USD (`0x7e860098F58bBFC8648a4311b374B1D669a2bc6B`) | ETH:False, BTC:False | 0s |
| CBBTC | CHAINLINK_CBBTC_USD (`0x07DA0E54543a844a80ABE69c8A12F22B3aA59f9D`) | ETH:False, BTC:False | 0s |
| USOL | CHAINLINK_SOL_USD (`0x975043adBb80fc32276CbF9Bbcfd4A601a12462D`) | ETH:False, BTC:False | 0s |
| CBDOGE | CHAINLINK_DOGE_USD (`0x8422f3d3CAFf15Ca682939310d6A5e619AE08e57`) | ETH:False, BTC:False | 0s |
| AERO | `0x4EC5970fC728C5f65ba413992CD5fF6FD70fcfF0` | ETH:False, BTC:False | 0s |
| cbADA | `0x34cD971a092d5411bD69C10a5F0A7EEF72C69041` | ETH:False, BTC:False | 0s |
| cbXRP | `0x9f0C1dD78C4CBdF5b9cf923a549A201EdC676D34` | ETH:False, BTC:False | 0s |
| cbLTC | `0x206a34e47093125fbf4C75b7c7E88b84c6A77a69` | ETH:False, BTC:False | 0s |
| uAVAX | `0xE70f2D34Fd04046aaEC26a198A35dD8F2dF5cd92` | ETH:False, BTC:False | 0s |
| uSHIB | `0xC8D5D660bb585b68fa0263EeD7B4224a5FC99669` | ETH:False, BTC:False | 0s |
| CBETH | `0xd7818272B9e248357d13057AAb0B417aF31E817d` | ETH:False, BTC:False | 0s |
| sUSDe | `0x79cf4a31B29D69191f0b6E97916eB93FEB81E533` | ETH:False, BTC:False | 0s |
| VIRTUAL | `0xEaf310161c9eF7c813A14f8FEF6Fb271434019F7` | ETH:False, BTC:False | 0s |
| VVV | `0x8eC6a128a430f7A850165bcF18facc9520a9873F` | ETH:False, BTC:False | 0s |
| WELL | `0xc15d9944dAefE2dB03e53bef8DDA25a56832C5fe` | ETH:False, BTC:False | 0s |
| DEGEN | `0xE62BcE5D7CB9d16AB8b4D622538bc0A50A5799c2` | ETH:False, BTC:False | 0s |
| EURC | `0xDAe398520e2B67cd3f27aeF9Cf14D93D927f8250` | ETH:False, BTC:False | 0s |
| GHO | `0x42868EFcee13C0E71af89c04fF7d96f5bec479b0` | ETH:False, BTC:False | 0s |
| USDS | `0x2330aaE3bca5F05169d5f4597964D44522F62930` | ETH:False, BTC:False | 0s |
| SUPER_OETH | `0x39C6E14CdE46D4FFD9F04Ff159e7ce8eC20E10B4` | ETH:True, BTC:False | 0s |

---

<a id="curve-prices"></a>
### Curve Prices
Address: `0x7B2aeE8B6A4bdF0885dEF48CCda8453Fdc1Bba5d`

#### Global Config
| Parameter | Value |
| --- | --- |
| isPaused | False |
| numAssets | 2 |

#### Governance Settings (LocalGov Module)
| Parameter | Value |
| --- | --- |
| governance | None |
| govChangeTimeLock | 43200 blocks (~1.0d) |
| pendingGov | None |

#### Timelock Settings (TimeLock Module)
| Parameter | Value |
| --- | --- |
| minActionTimeLock | 14400 blocks (~8.0h) |
| maxActionTimeLock | 302400 blocks (~7.0d) |
| actionTimeLock | 14400 blocks (~8.0h) |
| expiration | 302400 blocks (~7.0d) |

#### Curve Pool Configs (2)

**GREEN**
- Pool: `0xd6c283655B42FA0eb2685F7AB819784F071459dc`
- Type: STABLESWAP_NG
- Underlying (2): USDC, GREEN
- LP Token: `0xd6c283655B42FA0eb2685F7AB819784F071459dc`
- Has Eco Token: True

**GREEN/USDC**
- Pool: `0xd6c283655B42FA0eb2685F7AB819784F071459dc`
- Type: STABLESWAP_NG
- Underlying (2): USDC, GREEN
- LP Token: `0xd6c283655B42FA0eb2685F7AB819784F071459dc`
- Has Eco Token: True

#### GREEN Reference Pool Configuration

**Pool Config**
- Pool: `0xd6c283655B42FA0eb2685F7AB819784F071459dc`
- LP Token: `0xd6c283655B42FA0eb2685F7AB819784F071459dc`
- GREEN Index: 1
- Alt Asset: USDC (`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`)
- Alt Asset Decimals: 6
- Max Num Snapshots: 10
- Danger Trigger: 60.00%
- Stale Blocks: 43200 blocks (~1.0d)
- Stabilizer Adjust Weight: 7500
- Stabilizer Max Pool Debt: 5,000,000.00 GREEN

**Current Status**
- Num Blocks In Danger: 0
- Next Index: 8
- Last Snapshot:
  - GREEN Balance: 116,310.95 GREEN
  - Ratio: 0.000000
  - In Danger: False
  - Update: 38927434 (~19973.7d ago)

---

<a id="bluechip-yield-prices"></a>
### BlueChip Yield Prices
Address: `0x90C70ACfF302c8a7f00574EC3547B0221f39cD28`

#### Global Config
| Parameter | Value |
| --- | --- |
| isPaused | False |
| numAssets | 20 |

#### Governance Settings (LocalGov Module)
| Parameter | Value |
| --- | --- |
| governance | None |
| govChangeTimeLock | 43200 blocks (~1.0d) |
| pendingGov | None |

#### Timelock Settings (TimeLock Module)
| Parameter | Value |
| --- | --- |
| minActionTimeLock | 21600 blocks (~12.0h) |
| maxActionTimeLock | 302400 blocks (~7.0d) |
| actionTimeLock | 21600 blocks (~12.0h) |
| expiration | 302400 blocks (~7.0d) |

#### Yield Token Configs (20)

**MORPHO_SPARK_USDC**
- Protocol: Morpho
- Underlying: USDC (`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`)
- Underlying Decimals: 6
- Vault Token Decimals: 18
- Min Snapshot Delay: 300 blocks (~10.0m)
- Max Snapshots: 20
- Max Upside Deviation: 10.00%
- Stale Time: 0s
- Next Index: 14
- Last Snapshot: supply=510933041, pps=1042841, block=1762542797 (~24.4d ago)

**AAVEV3_CBBTC**
- Protocol: AaveV3
- Underlying: CBBTC (`0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf`)
- Underlying Decimals: 8
- Vault Token Decimals: 8
- Min Snapshot Delay: 300 blocks (~10.0m)
- Max Snapshots: 20
- Max Upside Deviation: 10.00%
- Stale Time: 0s
- Next Index: 0

**MOONWELL_AERO**
- Protocol: Moonwell
- Underlying: AERO (`0x940181a94A35A4569E4529A3CDfB74e38FD98631`)
- Underlying Decimals: 18
- Vault Token Decimals: 8
- Min Snapshot Delay: 300 blocks (~10.0m)
- Max Snapshots: 20
- Max Upside Deviation: 10.00%
- Stale Time: 0s
- Next Index: 3
- Last Snapshot: supply=760123595, pps=23123299207694812, block=1762530403 (~24.5d ago)

**0x784efeB622244d2348d4F2522f8860B96fbEcE89**
- Protocol: CompoundV3
- Underlying: AERO (`0x940181a94A35A4569E4529A3CDfB74e38FD98631`)
- Underlying Decimals: 18
- Vault Token Decimals: 18
- Min Snapshot Delay: 300 blocks (~10.0m)
- Max Snapshots: 20
- Max Upside Deviation: 10.00%
- Stale Time: 0s
- Next Index: 0

**AAVEV3_USDC**
- Protocol: AaveV3
- Underlying: USDC (`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`)
- Underlying Decimals: 6
- Vault Token Decimals: 6
- Min Snapshot Delay: 300 blocks (~10.0m)
- Max Snapshots: 20
- Max Upside Deviation: 10.00%
- Stale Time: 0s
- Next Index: 0

**AAVEV3_WETH**
- Protocol: AaveV3
- Underlying: WETH (`0x4200000000000000000000000000000000000006`)
- Underlying Decimals: 18
- Vault Token Decimals: 18
- Min Snapshot Delay: 300 blocks (~10.0m)
- Max Snapshots: 20
- Max Upside Deviation: 10.00%
- Stale Time: 0s
- Next Index: 0

**COMPOUNDV3_WETH**
- Protocol: CompoundV3
- Underlying: WETH (`0x4200000000000000000000000000000000000006`)
- Underlying Decimals: 18
- Vault Token Decimals: 18
- Min Snapshot Delay: 300 blocks (~10.0m)
- Max Snapshots: 20
- Max Upside Deviation: 10.00%
- Stale Time: 0s
- Next Index: 0

**MORPHO_MOONWELL_WETH**
- Protocol: Morpho
- Underlying: WETH (`0x4200000000000000000000000000000000000006`)
- Underlying Decimals: 18
- Vault Token Decimals: 18
- Min Snapshot Delay: 300 blocks (~10.0m)
- Max Snapshots: 20
- Max Upside Deviation: 10.00%
- Stale Time: 0s
- Next Index: 2
- Last Snapshot: supply=8568, pps=1019220963758932247, block=1762541703 (~24.4d ago)

**MORPHO_SEAMLESS_WETH**
- Protocol: Morpho
- Underlying: WETH (`0x4200000000000000000000000000000000000006`)
- Underlying Decimals: 18
- Vault Token Decimals: 18
- Min Snapshot Delay: 300 blocks (~10.0m)
- Max Snapshots: 20
- Max Upside Deviation: 10.00%
- Stale Time: 0s
- Next Index: 8
- Last Snapshot: supply=6097, pps=1016271256024327301, block=1762541707 (~24.4d ago)

**EULER_WETH**
- Protocol: Euler
- Underlying: WETH (`0x4200000000000000000000000000000000000006`)
- Underlying Decimals: 18
- Vault Token Decimals: 18
- Min Snapshot Delay: 300 blocks (~10.0m)
- Max Snapshots: 20
- Max Upside Deviation: 10.00%
- Stale Time: 0s
- Next Index: 13
- Last Snapshot: supply=645, pps=1021273135484338417, block=1761085961 (~41.3d ago)

**MOONWELL_CBETH**
- Protocol: Moonwell
- Underlying: CBETH (`0x2Ae3F1Ec7F1F5012CFEab0185bfc7aa3cf0DEc22`)
- Underlying Decimals: 18
- Vault Token Decimals: 8
- Min Snapshot Delay: 300 blocks (~10.0m)
- Max Snapshots: 20
- Max Upside Deviation: 10.00%
- Stale Time: 0s
- Next Index: 2
- Last Snapshot: supply=118488, pps=20085960594168379, block=1755635135 (~104.4d ago)

**COMPOUNDV3_USDC**
- Protocol: CompoundV3
- Underlying: USDC (`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`)
- Underlying Decimals: 6
- Vault Token Decimals: 6
- Min Snapshot Delay: 300 blocks (~10.0m)
- Max Snapshots: 20
- Max Upside Deviation: 10.00%
- Stale Time: 0s
- Next Index: 0

**MOONWELL_USDC**
- Protocol: Moonwell
- Underlying: USDC (`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`)
- Underlying Decimals: 6
- Vault Token Decimals: 8
- Min Snapshot Delay: 300 blocks (~10.0m)
- Max Snapshots: 20
- Max Upside Deviation: 10.00%
- Stale Time: 0s
- Next Index: 10
- Last Snapshot: supply=1736185541, pps=22304, block=1762542793 (~24.4d ago)

**EULER_USDC**
- Protocol: Euler
- Underlying: USDC (`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`)
- Underlying Decimals: 6
- Vault Token Decimals: 6
- Min Snapshot Delay: 300 blocks (~10.0m)
- Max Snapshots: 20
- Max Upside Deviation: 10.00%
- Stale Time: 0s
- Next Index: 6
- Last Snapshot: supply=1684359, pps=1039446, block=1762541115 (~24.4d ago)

**FLUID_USDC**
- Protocol: Fluid
- Underlying: USDC (`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`)
- Underlying Decimals: 6
- Vault Token Decimals: 6
- Min Snapshot Delay: 300 blocks (~10.0m)
- Max Snapshots: 20
- Max Upside Deviation: 10.00%
- Stale Time: 0s
- Next Index: 13
- Last Snapshot: supply=26453635, pps=1094779, block=1762542637 (~24.4d ago)

**MORPHO_MOONWELL_USDC**
- Protocol: Morpho
- Underlying: USDC (`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`)
- Underlying Decimals: 6
- Vault Token Decimals: 18
- Min Snapshot Delay: 300 blocks (~10.0m)
- Max Snapshots: 20
- Max Upside Deviation: 10.00%
- Stale Time: 0s
- Next Index: 14
- Last Snapshot: supply=31224454, pps=1053453, block=1762542827 (~24.4d ago)

**MORPHO_SEAMLESS_USDC**
- Protocol: Morpho
- Underlying: USDC (`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`)
- Underlying Decimals: 6
- Vault Token Decimals: 18
- Min Snapshot Delay: 300 blocks (~10.0m)
- Max Snapshots: 20
- Max Upside Deviation: 10.00%
- Stale Time: 0s
- Next Index: 16
- Last Snapshot: supply=36507597, pps=1039983, block=1762542667 (~24.4d ago)

**EULER_CBBTC**
- Protocol: Euler
- Underlying: CBBTC (`0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf`)
- Underlying Decimals: 8
- Vault Token Decimals: 8
- Min Snapshot Delay: 300 blocks (~10.0m)
- Max Snapshots: 20
- Max Upside Deviation: 10.00%
- Stale Time: 0s
- Next Index: 5
- Last Snapshot: supply=7, pps=100064064, block=1761085221 (~41.3d ago)

**MOONWELL_CBBTC**
- Protocol: Moonwell
- Underlying: CBBTC (`0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf`)
- Underlying Decimals: 8
- Vault Token Decimals: 8
- Min Snapshot Delay: 300 blocks (~10.0m)
- Max Snapshots: 20
- Max Upside Deviation: 10.00%
- Stale Time: 0s
- Next Index: 10
- Last Snapshot: supply=28138, pps=2005521, block=1761085221 (~41.3d ago)

**MORPHO_MOONWELL_CBBTC**
- Protocol: Morpho
- Underlying: CBBTC (`0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf`)
- Underlying Decimals: 8
- Vault Token Decimals: 18
- Min Snapshot Delay: 300 blocks (~10.0m)
- Max Snapshots: 20
- Max Upside Deviation: 10.00%
- Stale Time: 0s
- Next Index: 18
- Last Snapshot: supply=67, pps=120726604, block=1762541711 (~24.4d ago)

---

<a id="pyth-prices"></a>
### Pyth Prices
Address: `0x89b6E13E4aD4036EAA586219DD73Ebb2b36d5968`

#### Global Config
| Parameter | Value |
| --- | --- |
| isPaused | False |
| maxConfidenceRatio | 3.00% |
| numAssets | 0 |

#### Governance Settings (LocalGov Module)
| Parameter | Value |
| --- | --- |
| governance | `0xEF3cB7750FF6158d9f9B27651BbBA2299096483B` |
| govChangeTimeLock | 43200 blocks (~1.0d) |
| pendingGov | None |

#### Timelock Settings (TimeLock Module)
| Parameter | Value |
| --- | --- |
| minActionTimeLock | 3600 blocks (~2.0h) |
| maxActionTimeLock | 302400 blocks (~7.0d) |
| actionTimeLock | 0 blocks (~0s) |
| expiration | 302400 blocks (~7.0d) |

---

<a id="stork-prices"></a>
### Stork Prices
Address: `0xCa13ACFB607B842DF5c1D0657C0865cC47bEfe14`

#### Global Config
| Parameter | Value |
| --- | --- |
| isPaused | False |
| numAssets | 0 |

#### Governance Settings (LocalGov Module)
| Parameter | Value |
| --- | --- |
| governance | `0xEF3cB7750FF6158d9f9B27651BbBA2299096483B` |
| govChangeTimeLock | 43200 blocks (~1.0d) |
| pendingGov | None |

#### Timelock Settings (TimeLock Module)
| Parameter | Value |
| --- | --- |
| minActionTimeLock | 3600 blocks (~2.0h) |
| maxActionTimeLock | 302400 blocks (~7.0d) |
| actionTimeLock | 0 blocks (~0s) |
| expiration | 302400 blocks (~7.0d) |

---

<a id="aero-ripe-prices"></a>
### Aero Ripe Prices
Address: `0x5ce2BbD5eBe9f7d9322a8F56740F95b9576eE0A2`

#### Global Config
| Parameter | Value |
| --- | --- |
| isPaused | False |
| numAssets | 1 |

#### Governance Settings (LocalGov Module)
| Parameter | Value |
| --- | --- |
| governance | None |
| govChangeTimeLock | 43200 blocks (~1.0d) |
| pendingGov | None |

#### Timelock Settings (TimeLock Module)
| Parameter | Value |
| --- | --- |
| minActionTimeLock | 14400 blocks (~8.0h) |
| maxActionTimeLock | 302400 blocks (~7.0d) |
| actionTimeLock | 14400 blocks (~8.0h) |
| expiration | 302400 blocks (~7.0d) |

#### RIPE Price Configs (1)

**RIPE_TOKEN**
- Asset Address: `0x2A0a59d6B975828e781EcaC125dBA40d7ee5dDC0`
- Min Snapshot Delay: 300 blocks (~10.0m)
- Max Snapshots: 20
- Max Upside Deviation: 10.00%
- Stale Time: 0s
- Next Index: 8
- Last Snapshot: price=1014877852446038841, block=1764641493 (~2.7h ago)

---

<a id="wsuperoethb-prices"></a>
### wsuperOETHb Prices
Address: `0x2606Ce36b62a77562DF664E7a0009805BB254F3f`

#### Global Config
| Parameter | Value |
| --- | --- |
| isPaused | False |
| numAssets | 1 |

#### Governance Settings (LocalGov Module)
| Parameter | Value |
| --- | --- |
| governance | None |
| govChangeTimeLock | 43200 blocks (~1.0d) |
| pendingGov | None |

#### Timelock Settings (TimeLock Module)
| Parameter | Value |
| --- | --- |
| minActionTimeLock | 14400 blocks (~8.0h) |
| maxActionTimeLock | 302400 blocks (~7.0d) |
| actionTimeLock | 0 blocks (~0s) |
| expiration | 302400 blocks (~7.0d) |

#### Registered Assets (1)
| Asset | Feed/Underlying | Config | StaleTime |
| --- | --- | --- | --- |
| WRAPPED_SUPER_OETH | Configured | - | - |

---

<a id="undy-vault-prices"></a>
### Undy Vault Prices
Address: `0x2210a9b994CC0F13689043A34F2E11d17DB2099C`

#### Global Config
| Parameter | Value |
| --- | --- |
| isPaused | False |
| numAssets | 15 |

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

#### Yield Token Configs (15)

**UNDY_USD**
- Protocol: ID:0
- Underlying: USDC (`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`)
- Underlying Decimals: 6
- Vault Token Decimals: 6
- Min Snapshot Delay: 300 blocks (~10.0m)
- Max Snapshots: 20
- Max Upside Deviation: 10.00%
- Stale Time: 0s
- Next Index: 7
- Last Snapshot: supply=86009, pps=1000310, block=1761860707 (~32.3d ago)

**UNDY_ETH**
- Protocol: ID:0
- Underlying: WETH (`0x4200000000000000000000000000000000000006`)
- Underlying Decimals: 18
- Vault Token Decimals: 18
- Min Snapshot Delay: 300 blocks (~10.0m)
- Max Snapshots: 20
- Max Upside Deviation: 10.00%
- Stale Time: 0s
- Next Index: 3
- Last Snapshot: supply=3, pps=1000318417364708282, block=1761860609 (~32.3d ago)

**UNDY_BTC**
- Protocol: ID:0
- Underlying: CBBTC (`0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf`)
- Underlying Decimals: 8
- Vault Token Decimals: 8
- Min Snapshot Delay: 300 blocks (~10.0m)
- Max Snapshots: 20
- Max Upside Deviation: 10.00%
- Stale Time: 0s
- Next Index: 3
- Last Snapshot: supply=0, pps=99981530, block=1761860849 (~32.3d ago)

**UNDY_AERO**
- Protocol: ID:0
- Underlying: AERO (`0x940181a94A35A4569E4529A3CDfB74e38FD98631`)
- Underlying Decimals: 18
- Vault Token Decimals: 18
- Min Snapshot Delay: 300 blocks (~10.0m)
- Max Snapshots: 20
- Max Upside Deviation: 10.00%
- Stale Time: 0s
- Next Index: 1
- Last Snapshot: supply=193, pps=1000166052825937495, block=1761611401 (~35.2d ago)

**UNDY_USDS**
- Protocol: ID:0
- Underlying: USDS (`0x820C137fa70C8691f0e44Dc420a5e53c168921Dc`)
- Underlying Decimals: 18
- Vault Token Decimals: 18
- Min Snapshot Delay: 300 blocks (~10.0m)
- Max Snapshots: 20
- Max Upside Deviation: 10.00%
- Stale Time: 0s
- Next Index: 1
- Last Snapshot: supply=0, pps=1000000000000000000, block=1761611417 (~35.2d ago)

**undyEURC**
- Protocol: ID:0
- Underlying: EURC (`0x60a3E35Cc302bFA44Cb288Bc5a4F316Fdb1adb42`)
- Underlying Decimals: 6
- Vault Token Decimals: 6
- Min Snapshot Delay: 300 blocks (~10.0m)
- Max Snapshots: 20
- Max Upside Deviation: 10.00%
- Stale Time: 0s
- Next Index: 1
- Last Snapshot: supply=178, pps=1000016, block=1762311651 (~27.1d ago)

**undyAERO**
- Protocol: ID:0
- Underlying: AERO (`0x940181a94A35A4569E4529A3CDfB74e38FD98631`)
- Underlying Decimals: 18
- Vault Token Decimals: 18
- Min Snapshot Delay: 300 blocks (~10.0m)
- Max Snapshots: 20
- Max Upside Deviation: 10.00%
- Stale Time: 0s
- Next Index: 1
- Last Snapshot: supply=816, pps=1000049126945571857, block=1762311651 (~27.1d ago)

**undyBTC**
- Protocol: ID:0
- Underlying: CBBTC (`0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf`)
- Underlying Decimals: 8
- Vault Token Decimals: 8
- Min Snapshot Delay: 300 blocks (~10.0m)
- Max Snapshots: 20
- Max Upside Deviation: 10.00%
- Stale Time: 0s
- Next Index: 1
- Last Snapshot: supply=0, pps=99998394, block=1762311651 (~27.1d ago)

**undyETH**
- Protocol: ID:0
- Underlying: WETH (`0x4200000000000000000000000000000000000006`)
- Underlying Decimals: 18
- Vault Token Decimals: 18
- Min Snapshot Delay: 300 blocks (~10.0m)
- Max Snapshots: 20
- Max Upside Deviation: 10.00%
- Stale Time: 0s
- Next Index: 1
- Last Snapshot: supply=0, pps=1000794097486393393, block=1762311651 (~27.1d ago)

**undyUSD**
- Protocol: ID:0
- Underlying: USDC (`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`)
- Underlying Decimals: 6
- Vault Token Decimals: 6
- Min Snapshot Delay: 300 blocks (~10.0m)
- Max Snapshots: 20
- Max Upside Deviation: 10.00%
- Stale Time: 0s
- Next Index: 14
- Last Snapshot: supply=5, pps=1002130, block=1763082811 (~18.2d ago)

**undyUSD**
- Protocol: ID:0
- Underlying: USDC (`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`)
- Underlying Decimals: 6
- Vault Token Decimals: 6
- Min Snapshot Delay: 300 blocks (~10.0m)
- Max Snapshots: 20
- Max Upside Deviation: 10.00%
- Stale Time: 0s
- Next Index: 12
- Last Snapshot: supply=299431, pps=1003016, block=1764449449 (~2.3d ago)

**undyETH**
- Protocol: ID:0
- Underlying: WETH (`0x4200000000000000000000000000000000000006`)
- Underlying Decimals: 18
- Vault Token Decimals: 18
- Min Snapshot Delay: 300 blocks (~10.0m)
- Max Snapshots: 20
- Max Upside Deviation: 10.00%
- Stale Time: 0s
- Next Index: 3
- Last Snapshot: supply=3, pps=1000570201122465354, block=1764359975 (~3.4d ago)

**undyBTC**
- Protocol: ID:0
- Underlying: CBBTC (`0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf`)
- Underlying Decimals: 8
- Vault Token Decimals: 8
- Min Snapshot Delay: 300 blocks (~10.0m)
- Max Snapshots: 20
- Max Upside Deviation: 10.00%
- Stale Time: 0s
- Next Index: 2
- Last Snapshot: supply=0, pps=99999000, block=1763140237 (~17.5d ago)

**undyAERO**
- Protocol: ID:0
- Underlying: AERO (`0x940181a94A35A4569E4529A3CDfB74e38FD98631`)
- Underlying Decimals: 18
- Vault Token Decimals: 18
- Min Snapshot Delay: 300 blocks (~10.0m)
- Max Snapshots: 20
- Max Upside Deviation: 10.00%
- Stale Time: 0s
- Next Index: 6
- Last Snapshot: supply=5181, pps=1000829663389601775, block=1764428329 (~2.6d ago)

**undyEURC**
- Protocol: ID:0
- Underlying: EURC (`0x60a3E35Cc302bFA44Cb288Bc5a4F316Fdb1adb42`)
- Underlying Decimals: 6
- Vault Token Decimals: 6
- Min Snapshot Delay: 300 blocks (~10.0m)
- Max Snapshots: 20
- Max Upside Deviation: 10.00%
- Stale Time: 0s
- Next Index: 2
- Last Snapshot: supply=177, pps=1000907, block=1764394783 (~3.0d ago)

---

================================================================================

---
*Report generated at block 38930921 on 2025-12-02 04:55:27 UTC*
