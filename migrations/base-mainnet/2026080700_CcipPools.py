"""Deploy the CCIP burn/mint pools for RIPE and GREEN.

One contract per token. The mint capability is compiled in as a `pure` view
rather than taken as a constructor argument, so a pool cannot be deployed
claiming to be for a token it is not -- the capability is a property of the
bytecode, visible in the verified source, and there are no flags to pass in
the wrong order.

Deployment only. The pools are inert until two things happen, both of them
Safe transactions: RipeHq grants mint rights, and the TokenAdminRegistry
points CCIP at them. Wiring the lanes and handing ownership over comes in the
next migration, once the pools on the other side of each lane exist.

The stock BurnMintTokenPool Chainlink deploys has no canMintGreen() /
canMintRipe(), which RipeHq staticcalls on anything holding mint rights AND on
every mint. These are that same pool plus those two answers.
"""

from config.Ccip import CCIP
from scripts.utils import log, solidity
from scripts.utils.migration import Migration

SOURCE_FILE = "RipeCcipBurnMintTokenPools.sol"

# CCIP encodes amounts against the pool's declared decimals; both tokens are
# 18 on both chains, checked on chain.
TOKEN_DECIMALS = 18

# No allowlist, matching the pools already deployed on this chain. An empty
# allowlist means the pool does not restrict who may send through it -- access
# is controlled by the router and the ramps instead.
ALLOWLIST = []


def migrate(migration: Migration):
    config = CCIP[migration.chain()]

    ripe_token = migration.get_address("RipeToken")
    green_token = migration.get_address("GreenToken")

    log.h1("Deploying the RIPE pool")

    ripe_args = (
        ripe_token,
        TOKEN_DECIMALS,
        ALLOWLIST,
        config["RMN_PROXY"],
        config["ROUTER"],
    )
    ripe_pool = migration.deploy_solidity(
        "RipeCcipBurnMintTokenPool", *ripe_args, source_file=SOURCE_FILE
    )
    # What RipeHq staticcalls before granting mint rights, and on every mint.
    assert ripe_pool.canMintRipe(), "ripe pool cannot mint ripe"
    assert not ripe_pool.canMintGreen(), "ripe pool must not mint green"
    assert str(ripe_pool.getToken()).lower() == ripe_token.lower(), "wrong token"
    solidity.log_verify_command(
        migration, "RipeCcipBurnMintTokenPool", *ripe_args, source_file=SOURCE_FILE
    )

    log.h1("Deploying the GREEN pool")

    green_args = (
        green_token,
        TOKEN_DECIMALS,
        ALLOWLIST,
        config["RMN_PROXY"],
        config["ROUTER"],
    )
    green_pool = migration.deploy_solidity(
        "GreenCcipBurnMintTokenPool", *green_args, source_file=SOURCE_FILE
    )
    assert green_pool.canMintGreen(), "green pool cannot mint green"
    assert not green_pool.canMintRipe(), "green pool must not mint ripe"
    assert str(green_pool.getToken()).lower() == green_token.lower(), "wrong token"
    solidity.log_verify_command(
        migration, "GreenCcipBurnMintTokenPool", *green_args, source_file=SOURCE_FILE
    )

    log.h1("Deployed")

    log.info(f"\tRIPE  pool {ripe_pool.address}  token {ripe_token}")
    log.info(f"\tGREEN pool {green_pool.address}  token {green_token}")
    log.info("")
    log.info("\tBoth are inert: no mint rights, and CCIP does not route through")
    log.info("\tthem yet. Run the CcipPools migration on every chain in")
    log.info(f"\tREMOTE_CHAINS ({', '.join(config['REMOTE_CHAINS'])}) before wiring.")
