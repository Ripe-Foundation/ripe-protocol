"""Record CCIP activation only after complete, read-only on-chain readback."""

from scripts.utils import ccip
from scripts.utils.migration import Migration

SOURCE_FILE = "RipeCcipBurnMintTokenPools.sol"
POOLS = (
    ("RIPE", "RipeCcipBurnMintTokenPool", "RipeToken", False, True),
    ("GREEN", "GreenCcipBurnMintTokenPool", "GreenToken", True, False),
)


def migrate(migration: Migration):
    ccip.require_mainnet_activation_finalized(migration, POOLS, SOURCE_FILE)
