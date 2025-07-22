# Ripe Protocol Technical Documentation

## Overview  

Ripe Protocol is an onchain credit layer that turns **any tokenized asset—crypto‑native *or* real‑world**—into both a yield source *and* instant liquidity.  

Users deposit assets that keep earning through external strategies **plus** Ripe’s Endaoment, then draw a **single GREEN loan** against their diversified portfolio—no order books, no counterparties, predictable rates. Governance, driven by RIPE tokens and dynamic committee voting, steers risk, monetary policy and treasury allocations, giving the community full ownership of the protocol’s economics.

### Key Features  

| Feature | Why it matters |
|---------|----------------|
| **Earn Yield on Anything** | The Endaoment reinvests all protocol revenues and Bonding proceeds, distributing sustainable yield (and RIPE incentives) even to idle NFTs or tokenized RWAs. |
| **One‑Loan‑for‑All Collateral** | Aggregate every deposit—stablecoins, LP tokens, NFTs, houses—to back a *single* GREEN debt position, slashing liquidation risk and UX friction. |
| **GREEN Stablecoin & Multi‑Layer Peg Defense** | Dynamic interest, Stability Pool absorption, Endaoment redemptions and protocol‑owned liquidity keep GREEN fully‑backed and on‑peg. |
| **Compliance‑Ready RWA Support** | Whitelists and transfer‑restricted liquidation paths let regulated or permissioned assets participate safely. |
| **Counterparty‑Free, Predictable Borrowing** | Smart contracts mint GREEN directly—no lenders, no funding gaps, transparent terms. |
| **Resilient Liquidations** | Cascade of Stability Pool swaps + fungible/NFT auctions minimizes bad debt while rewarding backstops. |
| **Dynamic, Onchain Governance** | Continuous “Dynamic Voting,” elected committees and **Juice Score** incentives align risk, rewards and protocol evolution with token‑holder skin‑in‑the‑game. |

### Protocol Components

The protocol consists of several interconnected systems:
- **Core Contracts**: Handle lending, liquidations, rewards, and treasury management
- **Vaults**: Manage user deposits with varying complexity from simple storage to yield-bearing positions
- **Registries**: Coordinate protocol components and maintain authoritative records
- **Configuration**: Store and manage all protocol parameters and permissions
- **Price Oracles**: Integrate multiple price sources for accurate asset valuations
- **Tokens**: GREEN (stablecoin), RIPE (governance), and sGREEN (yield-bearing GREEN)

## Core Contracts

Essential protocol functionality for lending, liquidations, and rewards.

| Contract | Description |
|----------|-------------|
| [AuctionHouse.vy](core/AuctionHouse.md) | Liquidation engine executing multi-phase strategies to recover value from under-collateralized positions |
| [BondRoom.vy](core/BondRoom.md) | Decentralized bond marketplace for GREEN/RIPE exchanges with dynamic pricing based on treasury needs |
| [CreditEngine.vy](core/CreditEngine.md) | Lending powerhouse managing collateralized borrowing, interest accrual, and debt repayment |
| [Endaoment.vy](core/Endaoment.md) | Treasury and liquidity hub deploying funds across DeFi strategies while maintaining GREEN stability |
| [HumanResources.vy](core/HumanResources.md) | On-chain payroll system managing contributor vesting schedules and token compensation |
| [Lootbox.vy](core/Lootbox.md) | Rewards distribution engine calculating time-weighted points for RIPE token allocation |
| [Teller.vy](core/Teller.md) | Primary user interface for deposits, withdrawals, borrowing, and account management |

## Vaults

Modular vault implementations for different asset management strategies.

| Contract | Description |
|----------|-------------|
| [RebaseErc20.vy](vaults/RebaseErc20.md) | Yield-optimized vault for rebase tokens like stETH with automatic compounding |
| [RipeGov.vy](vaults/RipeGov.md) | Governance vault where users lock RIPE tokens for voting power with time-based bonuses |
| [SimpleErc20.vy](vaults/SimpleErc20.md) | Basic vault with direct 1:1 balance tracking for standard ERC20 collateral |
| [StabilityPool.vy](vaults/StabilityPool.md) | Insurance fund where stablecoin deposits earn discounted liquidated collateral |

### Vault Modules

Reusable components that power vault functionality.

| Module | Description |
|--------|-------------|
| [BasicVault.vy](vaults/modules/BasicVault.md) | Foundational vault operations for deposits, withdrawals, and transfers |
| [SharesVault.vy](vaults/modules/SharesVault.md) | Share-based accounting for yield distribution and proportional ownership |
| [StabVault.vy](vaults/modules/StabVault.md) | Stability pool mechanics for liquidation absorption and reward distribution |
| [VaultData.vy](vaults/modules/VaultData.md) | Universal database layer for balance tracking and state management |

## Registries

Central coordination points for protocol components and permissions.

| Contract | Description |
|----------|-------------|
| [PriceDesk.vy](registries/PriceDesk.md) | Oracle aggregator routing price requests through prioritized sources |
| [RipeHq.vy](registries/RipeHq.md) | Master registry and governance hub controlling token minting permissions |
| [Switchboard.vy](registries/Switchboard.md) | Authorization gateway for all protocol configuration changes |
| [VaultBook.vy](registries/VaultBook.md) | Central registry of approved vaults with safety checks and RIPE reward distribution |

## Configuration & Data

Protocol parameters and state management contracts.

| Contract | Description |
|----------|-------------|
| [BondBooster.vy](config/BondBooster.md) | Dynamic discount mechanism for GREEN-to-RIPE bond conversions |
| [SwitchboardAlpha.vy](config/SwitchboardAlpha.md) | Asset and vault configuration including collateral parameters |
| [SwitchboardBravo.vy](config/SwitchboardBravo.md) | Reward distribution and points system configuration |
| [SwitchboardCharlie.vy](config/SwitchboardCharlie.md) | Protocol operations including deposits, withdrawals, and liquidations |
| [SwitchboardDelta.vy](config/SwitchboardDelta.md) | HR, contributor management, and auxiliary feature configuration |
| [Ledger.vy](data/Ledger.md) | Comprehensive data storage for user positions, debt, and protocol metrics |
| [MissionControl.vy](data/MissionControl.md) | Central configuration hub storing all operational parameters |

## Price Sources

Oracle integrations for reliable asset pricing.

| Contract | Description |
|----------|-------------|
| [BlueChipYieldPrices.vy](priceSources/BlueChipYieldPrices.md) | Specialized pricing for yield-bearing vault tokens with snapshot system |
| [ChainlinkPrices.vy](priceSources/ChainlinkPrices.md) | Integration with Chainlink's decentralized oracle network |
| [CurvePrices.vy](priceSources/CurvePrices.md) | Curve LP token pricing and GREEN stabilizer monitoring |
| [PythPrices.vy](priceSources/PythPrices.md) | High-frequency pricing with Pyth Network's pull-based oracles |
| [StorkPrices.vy](priceSources/StorkPrices.md) | Stork Network integration with nanosecond-precision timestamps |

### Price Source Modules

| Module | Description |
|--------|-------------|
| [PriceSourceData.vy](priceSources/modules/PriceSourceData.md) | Base module defining standard interface for all price sources |

## Tokens

Protocol tokens for value transfer and governance.

| Contract | Description |
|----------|-------------|
| [GreenToken.vy](tokens/GreenToken.md) | USD-pegged stablecoin minted through overcollateralized positions |
| [RipeToken.vy](tokens/RipeToken.md) | Governance token for voting on protocol parameters and treasury |
| [SavingsGreen.vy](tokens/SavingsGreen.md) | Yield-bearing GREEN vault implementing ERC4626 standard |

### Token Modules

| Module | Description |
|--------|-------------|
| [Erc20Token.vy](tokens/modules/Erc20Token.md) | Enhanced ERC20 with blacklisting, pausability, and governance integration |
| [Erc4626Token.vy](tokens/modules/Erc4626Token.md) | Tokenized vault standard for yield-bearing tokens |

## Common Modules

Shared functionality used across multiple contracts.

| Module | Description |
|--------|-------------|
| [AddressRegistry.vy](modules/AddressRegistry.md) | Flexible registry for managing protocol addresses with time-locks |
| [Addys.vy](modules/Addys.md) | Centralized address resolution providing validated protocol addresses |
| [Contributor.vy](modules/Contributor.md) | Individual vesting contracts for contributor token compensation |
| [DeptBasics.vy](modules/DeptBasics.md) | Base functionality for protocol departments including pause controls |
| [LocalGov.vy](modules/LocalGov.md) | Two-tier governance system for contract-specific operations |
| [TimeLock.vy](modules/TimeLock.md) | Time-delay mechanism for critical configuration changes |

---

## Getting Started

1. **New Users**: Start with [Teller.vy](core/Teller.md) to understand user interactions
2. **Developers**: Review [RipeHq.vy](registries/RipeHq.md) for protocol architecture
3. **Governance**: Explore [RipeToken.vy](tokens/RipeToken.md) and [RipeGov.vy](vaults/RipeGov.md)
4. **Integrators**: Check [PriceDesk.vy](registries/PriceDesk.md) and vault interfaces

## Architecture Principles

- **Modular Design**: Reusable modules reduce code duplication and audit surface
- **Registry Pattern**: Central registries coordinate decentralized components
- **Time-Locked Changes**: Critical updates require delays to prevent rushed decisions
- **Multi-Oracle Support**: No single point of failure for price feeds
- **Layered Security**: Multiple validation layers from modules to registries to core contracts