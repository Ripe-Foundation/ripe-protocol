"""Wire the CCIP pools to the remote chain and hand them to the Safe.

Run only after CcipPools has run on every chain in REMOTE_CHAINS -- the remote
pool and token addresses are read from those chains' manifests.

Order is deliberate. The deployer owns the pools at this point, so it does the
lane wiring itself rather than routing a dozen config calls through the Safe.
Ownership moves to the Safe here, and mint rights are granted only AFTER that,
by the Safe. That way the deployer never owns a pool that can mint: while it
is owner the pool has no authority, and by the time it has authority the
deployer is no longer owner. Pool ownership is mint-critical -- the owner can
replace the router, and a hostile router can nominate ramps that reach the
pool's mint path -- so this ordering is what makes a deployer-run deployment
safe without deploying from the Safe itself.

Everything the Safe has to do is printed at the end as calldata.
"""

from config.Ccip import (
    CCIP,
    CCIP_POOL_HQ_IDS,
    CURRENT_RATE_LIMIT_ADMIN,
    NO_RATE_LIMIT,
    require_ccip_wiring_gates,
)
from scripts.utils import ccip, log
from scripts.utils.migration import Migration

SOURCE_FILE = "RipeCcipBurnMintTokenPools.sol"

# (label, contract, token, canMintGreen, canMintRipe). The contract name is
# also the manifest key -- one contract per token, so no aliasing needed.
POOLS = (
    ("RIPE", "RipeCcipBurnMintTokenPool", "RipeToken", False, True),
    ("GREEN", "GreenCcipBurnMintTokenPool", "GreenToken", True, False),
)


def _calldata(signature, types, values):
    from eth_abi.abi import encode
    from web3 import Web3

    return "0x" + (Web3.keccak(text=signature)[:4] + encode(types, values)).hex()


def migrate(migration: Migration):
    chain = migration.chain()
    config = CCIP[chain]
    hq = migration.get_contract("RipeHq")
    governance = str(hq.governance())
    token_admin_registry = ccip.token_admin_registry(chain)

    safe_steps = []
    admin_steps = []
    mint_rights_needed = []

    for label, contract_name, token_name, can_green, can_ripe in POOLS:
        token = migration.get_address(token_name)
        pool = migration.get_solidity_contract(contract_name, source_file=SOURCE_FILE)

        token_config = tuple(token_admin_registry.getTokenConfig(token))
        administrator = str(token_config[0])
        pending_administrator = str(token_config[1])
        if administrator.lower() == governance.lower():
            assert pending_administrator.lower() == ccip.ZERO_ADDRESS, (
                f"{label} has unexpected pending CCIP administrator "
                f"{pending_administrator}"
            )
            log.info(f"\t{label} TokenAdminRegistry administrator revalidated")
        else:
            assert administrator.lower() == ccip.ZERO_ADDRESS, (
                f"{label} has unexpected CCIP administrator {administrator}"
            )
            assert pending_administrator.lower() in (
                ccip.ZERO_ADDRESS,
                governance.lower(),
            ), f"{label} has unexpected pending CCIP administrator {pending_administrator}"
            admin_steps.append((label, token, pending_administrator))

        assert str(pool.getToken()).lower() == token.lower(), f"{label} pool has wrong token"
        assert str(pool.getRouter()).lower() == config["ROUTER"].lower(), f"{label} pool has wrong router"
        assert str(pool.getRmnProxy()).lower() == config["RMN_PROXY"].lower(), f"{label} pool has wrong RMN proxy"
        assert pool.typeAndVersion() == "BurnMintTokenPool 1.5.1", f"{label} pool has wrong source version"
        assert bool(pool.canMintGreen()) is can_green, f"{label} pool has wrong GREEN capability"
        assert bool(pool.canMintRipe()) is can_ripe, f"{label} pool has wrong RIPE capability"

        log.h1(f"Wiring the {label} pool")

        for remote_chain in config["REMOTE_CHAINS"]:
            remote_selector = CCIP[remote_chain]["CHAIN_SELECTOR"]
            try:
                remote_pool = migration.get_address_on_chain(remote_chain, contract_name)
                remote_token = migration.get_address_on_chain(remote_chain, token_name)
            except (FileNotFoundError, KeyError):
                raise Exception(
                    f"no {contract_name} in the {remote_chain} manifest - run the "
                    f"CcipPools migration on {remote_chain} before wiring {chain}"
                )

            if pool.isSupportedChain(remote_selector):
                log.info(f"\t{remote_chain} ({remote_selector}) already wired; revalidating")
            else:
                require_ccip_wiring_gates()
                log.info(f"\t{remote_chain}: pool {remote_pool}, token {remote_token}")
                chain_update = (
                    remote_selector,
                    [ccip.encode_address(remote_pool)],
                    ccip.encode_address(remote_token),
                    NO_RATE_LIMIT,  # outbound; unresolved owner disposition
                    NO_RATE_LIMIT,  # inbound; unresolved owner disposition
                )
                migration.execute(pool.applyChainUpdates, [], [chain_update])

            ccip.assert_lane_configuration(
                pool,
                remote_selector,
                remote_pool,
                remote_token,
                NO_RATE_LIMIT,
                CURRENT_RATE_LIMIT_ADMIN,
            )

        log.h2(f"Handing the {label} pool to governance")

        owner = str(pool.owner())
        if owner.lower() == governance.lower():
            log.info(f"\talready owned by governance ({governance})")
        else:
            # Two step: the deployer offers, governance accepts. The Safe is
            # not the deployer, so it never completes here.
            migration.execute(pool.transferOwnership, governance)
            log.info(f"\townership offered to {governance}")
            safe_steps.append((
                f"{label} pool: accept ownership",
                pool.address,
                _calldata("acceptOwnership()", [], []),
            ))

        reg_id = int(hq.getRegId(pool.address))
        if reg_id == 0:
            mint_rights_needed.append((label, can_green, can_ripe))
            safe_steps.append((
                f"{label} pool: register in RipeHq",
                hq.address,
                _calldata("startAddNewAddressToRegistry(address,string)",
                          ["address", "string"], [pool.address, f"CCIP {label} Pool"]),
            ))
            safe_steps.append((
                f"{label} pool: confirm registration -> gives it a regId",
                hq.address,
                _calldata("confirmNewAddressToRegistry(address)", ["address"], [pool.address]),
            ))
        else:
            assert reg_id == CCIP_POOL_HQ_IDS[label], (
                f"{label} pool has RipeHq id {reg_id}, expected {CCIP_POOL_HQ_IDS[label]}"
            )
            hq_config = tuple(hq.hqConfig(reg_id))
            actual_capabilities = (
                bool(hq_config[1]), bool(hq_config[2]), bool(hq_config[3])
            )
            expected_capabilities = (can_green, can_ripe, False)
            assert actual_capabilities in ((False, False, False), expected_capabilities), (
                f"{label} RipeHq capabilities {actual_capabilities} are unexpected"
            )
            if actual_capabilities == expected_capabilities:
                log.info(f"\tRipeHq id {reg_id} and capabilities revalidated")
            else:
                mint_rights_needed.append((label, can_green, can_ripe))

        configured_pool = str(token_admin_registry.getPool(token))
        if configured_pool.lower() == ccip.ZERO_ADDRESS:
            safe_steps.append((
                f"{label} pool: point CCIP at it (admin must be accepted first)",
                config["TOKEN_ADMIN_REGISTRY"],
                _calldata("setPool(address,address)", ["address", "address"],
                          [token, pool.address]),
            ))
        else:
            assert configured_pool.lower() == str(pool.address).lower(), (
                f"{label} TokenAdminRegistry pool {configured_pool} does not match {pool.address}"
            )
            log.info("\tTokenAdminRegistry pool assignment revalidated")

    log.h1("What the Safe has to run")

    log.h2("1. Claim the CCIP admin role, once per token")
    if admin_steps:
        log.info(f"\tRegistryModuleOwnerCustom {config['REGISTRY_MODULE_OWNER_CUSTOM']}")
        for label, token, pending_administrator in admin_steps:
            if pending_administrator.lower() != governance.lower():
                log.info(f"\t  {label} registerAdminViaGetCCIPAdmin(address)")
                log.info(f"\t    {_calldata('registerAdminViaGetCCIPAdmin(address)', ['address'], [token])}")
            log.info(f"\t  {label} acceptAdminRole(address) on {config['TOKEN_ADMIN_REGISTRY']}")
            log.info(f"\t    {_calldata('acceptAdminRole(address)', ['address'], [token])}")
        log.info("")
        log.info("\tThe token's getCCIPAdmin() returns RipeHq governance, so the")
        log.info("\tSafe is the address proposed and the Safe is who accepts.")
    else:
        log.info("\tgovernance is already administrator for both tokens")

    log.h2("2. Ownership, registration and routing")
    for description, target, data in safe_steps:
        log.info(f"\t{description}")
        log.info(f"\t  to:   {target}")
        log.info(f"\t  data: {data}")

    log.h2("3. Mint rights -- LAST, after ownership has moved")
    if mint_rights_needed:
        log.info(f"\tRipeHq {hq.address}, once each pool has a regId from step 2.")
        log.info("\t  initiateHqConfigChange(regId, canMintGreen, canMintRipe, false)")
        log.info("\t  confirmHqConfigChange(regId)")
        for label, can_green, can_ripe in mint_rights_needed:
            log.info(f"\t  {label} pool -> canMintGreen={can_green}, canMintRipe={can_ripe}")
        log.info("")
        log.info("\tGranting before ownership moves would leave the deployer owning")
        log.info("\ta pool that can mint. Do not reorder.")
    else:
        log.info("\tRipeHq ids and token-specific mint capabilities already revalidated")
