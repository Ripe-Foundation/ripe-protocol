from config.Ccip import CCIP
from scripts.utils import ccip, log, solidity
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    """
    Deploys an inert RipeTokenPool. Ownership, wiring, routing, and RipeHq mint
    rights are handled in the next migration, with mint authority granted last.

    The stock `BurnMintTokenPool` chainlink deploys has no `canMintRipe()`, which RipeHq
    staticcalls on anything it grants minting rights to, so it can never mint RIPE
    through the token itself. RipeTokenPool is that same pool plus those answers.

    Wiring this pool to the remote chain and pointing CCIP at it happens in the next
    migration, once the pool on the other side of the lane exists.
    """
    chain = migration.chain()
    config = CCIP[chain]

    ripe_token = migration.get_address("RipeToken")

    log.h1("Deploying RipeTokenPool")
    ccip.require_activation_policy(migration, "RIPE")

    pool_args = (
        ripe_token,
        18,
        [],  # no allowlist, same as the pool it replaces
        config["RMN_PROXY"],
        config["ROUTER"],
        False,  # canMintGreen
        True,  # canMintRipe
    )
    pool = migration.deploy_solidity("RipeTokenPool", *pool_args)

    # what RipeHq staticcalls before granting mint rights, and on every mint after that
    assert pool.canMintRipe(), "pool was not deployed as a ripe minter"
    assert not pool.canMintGreen()

    solidity.log_verify_command(migration, "RipeTokenPool", *pool_args)

    log.info("RipeTokenPool is inert: it has no RipeHq mint authority or CCIP routing")
