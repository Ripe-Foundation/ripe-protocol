from config.Ccip import CCIP
from scripts.utils import log, solidity
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    """
    Deploys RipeTokenPool - the CCIP burn/mint pool for RIPE - and gives it ripe minting
    rights in RipeHq.

    The stock `BurnMintTokenPool` chainlink deploys has no `canMintRipe()`, which RipeHq
    staticcalls on anything it grants minting rights to, so it can never mint RIPE
    through the token itself. RipeTokenPool is that same pool plus those answers.

    Wiring this pool to the remote chain and pointing CCIP at it happens in the next
    migration, once the pool on the other side of the lane exists.
    """
    chain = migration.chain()
    config = CCIP[chain]

    ripe_token = migration.get_address("RipeToken")
    hq = migration.get_contract("RipeHq")

    log.h1("Deploying RipeTokenPool")

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

    log.h1("Granting the pool ripe minting rights in RipeHq")

    migration.execute(hq.startAddNewAddressToRegistry, pool.address, "CCIP Ripe Pool")
    reg_id = int(migration.execute(hq.confirmNewAddressToRegistry, pool.address))
    log.info(f"RipeTokenPool registered in RipeHq with regId {reg_id}")

    # canMintGreen, canMintRipe, canSetTokenBlacklist
    migration.execute(hq.initiateHqConfigChange, reg_id, False, True, False)
    migration.execute(hq.confirmHqConfigChange, reg_id)

    assert hq.canMintRipe(pool.address), "RipeHq did not grant ripe minting to the pool"
