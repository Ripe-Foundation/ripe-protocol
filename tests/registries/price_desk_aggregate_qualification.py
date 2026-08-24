"""Durable inputs shared by the Robinhood aggregate-gas qualification tests."""

from eth_utils import keccak

from config.robinhood_launch import STALE_WINDOW_GLOBAL


QUALIFIED_BORROWER_ASSET_COUNT = 9
QUALIFIED_PRICE_DESK_SOURCE_COUNT = 3
QUALIFIED_PRICE_SOURCE_PRICE_GAS_STIPEND = 250_000

# Exact DefaultsRobinhoodLive addresses qualified as nonzero-LTV, direct-priced
# collateral. Do not derive these from the defaults source: this guard must also
# catch address rebinding under an existing semantic constant name.
QUALIFIED_DIRECT_PRICE_LTV_ASSET_ADDRESSES = frozenset(
    (
        "0x0bd7d308f8e1639fab988df18a8011f41eacad73",  # WETH
        "0x4a0e65a3eccec6dbe60ae065f2e7bb85fae35eea",  # SPCX
        "0xd0601ce157db5bdc3162bbac2a2c8af5320d9eec",  # NVDA
        "0x322f0929c4625ed5bad873c95208d54e1c003b2d",  # TSLA
        "0xaf3d76f1834a1d425780943c99ea8a608f8a93f9",  # AAPL
        "0x2e0847e8910a9732eb3fb1bb4b70a580adad4fe3",  # GOOGL
        "0x1b0e319c6a659f002271b69db8a7df2f911c153e",  # GME
    )
)

# Read-only Robinhood mainnet observation at eth_blockNumber 38,402,845 on
# 2026-08-16: ArbGasInfo(0x000000000000000000000000000000000000006c)
# getMaxTxGasLimit() returned 32,000,000. Requalify if this chain input changes.
ROBINHOOD_MAX_TX_GAS = 32_000_000
ROBINHOOD_GAS_LIMIT_OBSERVED_BLOCK = 38_402_845

# Independent qualification literal: changing the production configuration must
# fail collection until the PriceDesk gas profile has been rerun and this value
# is deliberately updated.
QUALIFIED_ROBINHOOD_PRICE_STALE_TIME = 86_400
if STALE_WINDOW_GLOBAL != QUALIFIED_ROBINHOOD_PRICE_STALE_TIME:
    raise RuntimeError(
        "Robinhood global stale-time policy changed; rerun aggregate PriceDesk "
        "gas qualification before updating QUALIFIED_ROBINHOOD_PRICE_STALE_TIME"
    )

# The prompt-faithful Chainlink lanes consume the production value after the
# independent literal above proves that this is still the qualified profile.
# The synthetic saturated source accepts the ABI argument but intentionally
# isolates stipend exhaustion from oracle-freshness behavior.
ROBINHOOD_PRICE_STALE_TIME = STALE_WINDOW_GLOBAL

# These ABI maxima are not themselves safe batch sizes. The focused gas suite
# measures smaller keeper/operator limits, and larger batches remain a manual
# operations gate because the repository has no keeper batch-size config.
LIQUIDATE_MANY_API_MAX = 50
DELEVERAGE_MANY_API_MAX = 25
QUALIFIED_SATURATED_LIQUIDATION_BATCH_SIZE = 2
QUALIFIED_SATURATED_DELEVERAGE_BATCH_SIZE = 3
# Each value is proven by a successful N-user transaction and an OOG at N+1.
# Raising either input without expanding the measured envelope fails loudly.

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
