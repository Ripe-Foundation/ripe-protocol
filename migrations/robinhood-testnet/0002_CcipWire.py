from config.Ccip import CCIP, NO_RATE_LIMIT
from scripts.utils import ccip, log
from scripts.utils.migration import Migration


def migrate(migration: Migration):
    """
    Wires RipeTokenPool to the pools on the other side of each lane, points CCIP at it,
    and takes ripe minting rights away from the pool it replaces.

    Run this only after the CcipPool migration has run on every chain in REMOTE_CHAINS -
    the remote pool addresses are read from those chains' manifests.
    """
    chain = migration.chain()
    config = CCIP[chain]

    ripe_token = migration.get_address("RipeToken")
    hq = migration.get_contract("RipeHq")
    pool = migration.get_solidity_contract("RipeTokenPool")

    log.h1("Wiring RipeTokenPool to the remote chains")

    for remote_chain in config["REMOTE_CHAINS"]:
        remote_selector = CCIP[remote_chain]["CHAIN_SELECTOR"]
        try:
            remote_pool = migration.get_address_on_chain(remote_chain, "RipeTokenPool")
            remote_token = migration.get_address_on_chain(remote_chain, "RipeToken")
        except (FileNotFoundError, KeyError):
            raise Exception(
                f"no RipeTokenPool in the {remote_chain} manifest - run the CcipPool "
                f"migration on {remote_chain} before wiring {chain} to it"
            )

        if pool.isSupportedChain(remote_selector):
            log.info(f"{remote_chain} ({remote_selector}) already configured, skipping")
            continue

        log.info(f"{remote_chain}: pool {remote_pool}, token {remote_token}")
        chain_update = (
            remote_selector,
            [ccip.encode_address(remote_pool)],
            ccip.encode_address(remote_token),
            NO_RATE_LIMIT,  # outbound
            NO_RATE_LIMIT,  # inbound
        )
        migration.execute(pool.applyChainUpdates, [], [chain_update])

    log.h1("Pointing CCIP at the new pool")

    if not ccip.set_pool(migration, ripe_token, pool.address):
        log.error(
            "Stopping here: the pool this one replaces keeps its ripe minting rights "
            "until CCIP actually routes through the new pool. Re-run this migration "
            f"(--start-timestamp {migration.timestamp()} --end-timestamp {migration.timestamp()}) "
            "once that is done."
        )
        return

    log.h1("Retiring the previous CCIP pool")

    previous_pool = config["PREVIOUS_RIPE_POOL"]
    previous_reg_id = int(hq.getRegId(previous_pool))
    if previous_reg_id == 0:
        log.info(f"{previous_pool} is not in RipeHq, nothing to retire")
    else:
        migration.execute(hq.initiateHqConfigChange, previous_reg_id, False, False, False)
        migration.execute(hq.confirmHqConfigChange, previous_reg_id)
        assert not hq.canMintRipe(previous_pool), "previous pool can still mint RIPE"

    # last, since the pool owner is who sets rate limits, remote pools and the router
    hand_pool_to_governance(migration, pool, hq)


def hand_pool_to_governance(migration: Migration, pool, hq):
    """
    Moves pool ownership from the deployer to the blueprint's governance address.
    Ownership is two step: the deployer offers it, governance has to accept. When
    governance is the deployer itself, both happen here.
    """
    log.h1("Handing the pool over to governance")

    governance = str(migration.blueprint().ADDYS["GOVERNANCE"])
    owner = str(pool.owner())

    hq_governance = str(hq.governance())
    if hq_governance.lower() != governance.lower():
        log.info(
            f"note: the pool will be owned by the blueprint's governance ({governance}), "
            f"while its minting rights are governed by RipeHq's ({hq_governance})"
        )

    if owner.lower() == governance.lower():
        log.info(f"pool is already owned by governance ({governance})")
        return

    migration.execute(pool.transferOwnership, governance)

    if governance.lower() == str(migration.account().address).lower():
        migration.execute(pool.acceptOwnership)
        log.info(f"pool ownership moved to governance ({governance})")
        return

    log.error(
        f"ACTION REQUIRED: pool ownership was offered to governance ({governance}), which "
        f"has to accept it before it can change rate limits, remote pools or the router. "
        f"From governance run:\n"
        f"    cast send {pool.address} 'acceptOwnership()' \\\n"
        f"        --rpc-url $RPC_URL --account $GOVERNANCE_ACCOUNT\n"
        f"Until then the deployer ({migration.account().address}) stays the owner."
    )
