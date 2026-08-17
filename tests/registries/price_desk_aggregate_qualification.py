"""Durable inputs shared by the Robinhood aggregate-gas qualification tests."""

from eth_utils import keccak


QUALIFIED_BORROWER_ASSET_COUNT = 9
QUALIFIED_PRICE_DESK_SOURCE_COUNT = 3
QUALIFIED_PRICE_SOURCE_PRICE_GAS_STIPEND = 250_000

# Read-only Robinhood mainnet observation at eth_blockNumber 38,402,845 on
# 2026-08-16: ArbGasInfo(0x000000000000000000000000000000000000006c)
# getMaxTxGasLimit() returned 32,000,000. Requalify if this chain input changes.
ROBINHOOD_MAX_TX_GAS = 32_000_000
ROBINHOOD_GAS_LIMIT_OBSERVED_BLOCK = 38_402_845

# DefaultsRobinhood uses this value. Keeping staleness enabled makes the gas
# measurements cover the configured timestamp checks rather than a zero-window
# gas-only shortcut.
ROBINHOOD_PRICE_STALE_TIME = 86_400

# These ABI maxima are not themselves safe batch sizes. The focused gas suite
# measures smaller keeper/operator limits, and larger batches remain a manual
# operations gate because the repository has no keeper batch-size config.
LIQUIDATE_MANY_API_MAX = 50
DELEVERAGE_MANY_API_MAX = 25
QUALIFIED_SATURATED_LIQUIDATION_BATCH_SIZE = 2
QUALIFIED_SATURATED_DELEVERAGE_BATCH_SIZE = 3

# Snapshot of a read-only live registry check at the gas-limit observation
# block. Repository slot 3 is BlueChipYieldPrices, while live slot 3 was still
# Uniswap V2 Prices. Reconciliation is a manual pre-activation gate; this
# source-only test package must not silently treat the two compositions as one.
ROBINHOOD_LIVE_PRICE_DESK_SLOT_3 = "Uniswap V2 Prices"
ROBINHOOD_LIVE_PRICE_DESK_SLOT_3_ADDRESS = (
    "0xfB2d96242769fCE0a3Cf75204B0553cE0E516545"
)

PRICE_SOURCE_SELECTOR = keccak(
    text="getPriceAndHasFeed(address,uint256,address)"
)[:4]
NESTED_PRICE_SELECTOR = keccak(text="getPrice(address,bool)")[:4]
