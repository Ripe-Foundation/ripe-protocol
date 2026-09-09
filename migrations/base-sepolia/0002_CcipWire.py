from config.Ccip import CCIP
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

    assert str(pool.getToken()).lower() == ripe_token.lower(), (
        "RIPE pool has wrong token"
    )
    assert str(pool.getRouter()).lower() == config["ROUTER"].lower(), (
        "RIPE pool has wrong router"
    )
    assert str(pool.getRmnProxy()).lower() == config["RMN_PROXY"].lower(), (
        "RIPE pool has wrong RMN proxy"
    )
    assert pool.typeAndVersion() == "BurnMintTokenPool 1.5.1", (
        "RIPE pool has wrong source version"
    )
    assert pool.canMintRipe() and not pool.canMintGreen(), (
        "RIPE pool has wrong mint capability"
    )

    governance = str(hq.governance())
    blueprint_governance = str(migration.blueprint().ADDYS["GOVERNANCE"])
    assert governance.lower() == blueprint_governance.lower(), (
        "RipeHq governance and blueprint governance must match before CCIP activation"
    )
    owner = str(pool.owner())
    configured_pool = str(ccip.token_admin_registry(chain).getPool(ripe_token))
    already_active = bool(hq.canMintRipe(pool.address)) or (
        configured_pool.lower() == str(pool.address).lower()
    )
    if owner.lower() != governance.lower() and already_active:
        raise RuntimeError(
            "CCIP_ACTIVE_POOL_NOT_GOVERNANCE_OWNED: disable routing/mint authority "
            "before recovering this legacy testnet state"
        )
    if owner.lower() != governance.lower():
        ccip.execute_activation_mutation(
            migration, "RIPE", pool.transferOwnership, governance
        )
        if governance.lower() == str(migration.account().address).lower():
            ccip.execute_activation_mutation(migration, "RIPE", pool.acceptOwnership)
        else:
            log.error(
                f"ACTION REQUIRED: governance {governance} must accept pool ownership; "
                "rerun as governance before any wiring, routing, or mint grant"
            )
            return
    assert str(pool.owner()).lower() == governance.lower(), (
        "governance must own the pool before wiring"
    )
    assert str(migration.account().address).lower() == governance.lower(), (
        "the governance owner must execute testnet wiring"
    )

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

        lane_is_configured = pool.isSupportedChain(remote_selector)
        if lane_is_configured:
            log.info(
                f"{remote_chain} ({remote_selector}) already configured; revalidating"
            )
            policy = ccip.lane_policy_for_revalidation(chain, remote_chain, "RIPE")
        else:
            policy = ccip.require_activation_policy(migration, "RIPE", remote_chain)
            log.info(f"{remote_chain}: pool {remote_pool}, token {remote_token}")
            chain_update = (
                remote_selector,
                [ccip.encode_address(remote_pool)],
                ccip.encode_address(remote_token),
                policy.outbound.as_tuple(),
                policy.inbound.as_tuple(),
            )
            ccip.execute_activation_mutation(
                migration,
                "RIPE",
                pool.applyChainUpdates,
                [],
                [chain_update],
                remote_chain=remote_chain,
            )

        outbound, inbound, rate_limit_admin = ccip.current_lane_policy_fields(
            pool, remote_selector
        )
        if (outbound, inbound) != (
            policy.outbound.as_tuple(),
            policy.inbound.as_tuple(),
        ):
            ccip.execute_activation_mutation(
                migration,
                "RIPE",
                pool.setChainRateLimiterConfig,
                remote_selector,
                policy.outbound.as_tuple(),
                policy.inbound.as_tuple(),
                remote_chain=remote_chain,
            )
        if rate_limit_admin.lower() != policy.rate_limit_admin.lower():
            ccip.execute_activation_mutation(
                migration,
                "RIPE",
                pool.setRateLimitAdmin,
                policy.rate_limit_admin,
                remote_chain=remote_chain,
            )

        ccip.assert_lane_configuration(
            pool,
            remote_selector,
            remote_pool,
            remote_token,
            policy.outbound.as_tuple(),
            policy.inbound.as_tuple(),
            policy.rate_limit_admin,
        )

    log.h1("Pointing CCIP at the new pool")

    if not ccip.set_pool(migration, ripe_token, pool.address, "RIPE"):
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
        ccip.execute_activation_mutation(
            migration,
            "RIPE",
            hq.initiateHqConfigChange,
            previous_reg_id,
            False,
            False,
            False,
        )
        ccip.execute_activation_mutation(
            migration, "RIPE", hq.confirmHqConfigChange, previous_reg_id
        )
        assert not hq.canMintRipe(previous_pool), "previous pool can still mint RIPE"

    log.h1("Granting the governance-owned, routed pool mint authority LAST")
    reg_id = int(hq.getRegId(pool.address))
    if reg_id == 0:
        ccip.execute_activation_mutation(
            migration,
            "RIPE",
            hq.startAddNewAddressToRegistry,
            pool.address,
            "CCIP Ripe Pool",
        )
        reg_id = int(
            ccip.execute_activation_mutation(
                migration, "RIPE", hq.confirmNewAddressToRegistry, pool.address
            )
        )
    hq_config = tuple(hq.hqConfig(reg_id))
    actual_capabilities = (bool(hq_config[1]), bool(hq_config[2]), bool(hq_config[3]))
    assert actual_capabilities in ((False, False, False), (False, True, False)), (
        f"RIPE pool has unexpected RipeHq capabilities {actual_capabilities}"
    )
    if actual_capabilities != (False, True, False):
        ccip.execute_activation_mutation(
            migration, "RIPE", hq.initiateHqConfigChange, reg_id, False, True, False
        )
        ccip.execute_activation_mutation(
            migration, "RIPE", hq.confirmHqConfigChange, reg_id
        )
    assert hq.canMintRipe(pool.address), "RipeHq did not grant RIPE mint authority"
