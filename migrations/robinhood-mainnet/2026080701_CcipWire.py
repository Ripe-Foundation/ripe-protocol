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


def _hq_append_plan(migration, hq, missing_labels):
    """Build the exact four-stage Safe packet protected by the append window."""

    steps = []
    for label, contract_name, _token_name, can_green, can_ripe in POOLS:
        if label not in missing_labels:
            continue
        pool = migration.get_solidity_contract(contract_name, source_file=SOURCE_FILE)
        reg_id = CCIP_POOL_HQ_IDS[label]
        steps.extend(
            (
                {
                    "phase": 1,
                    "label": label,
                    "description": f"{label} pool: start RipeHq registration",
                    "target": str(hq.address),
                    "data": _calldata(
                        "startAddNewAddressToRegistry(address,string)",
                        ["address", "string"],
                        [pool.address, f"CCIP {label} Pool"],
                    ),
                },
                {
                    "phase": 2,
                    "label": label,
                    "description": f"{label} pool: confirm registration as exact id {reg_id}",
                    "target": str(hq.address),
                    "data": _calldata(
                        "confirmNewAddressToRegistry(address)",
                        ["address"],
                        [pool.address],
                    ),
                },
                {
                    "phase": 3,
                    "label": label,
                    "description": f"{label} pool: initiate token-specific mint rights",
                    "target": str(hq.address),
                    "data": _calldata(
                        "initiateHqConfigChange(uint256,bool,bool,bool)",
                        ["uint256", "bool", "bool", "bool"],
                        [reg_id, can_green, can_ripe, False],
                    ),
                },
                {
                    "phase": 4,
                    "label": label,
                    "description": f"{label} pool: confirm token-specific mint rights LAST",
                    "target": str(hq.address),
                    "data": _calldata(
                        "confirmHqConfigChange(uint256)", ["uint256"], [reg_id]
                    ),
                },
            )
        )
    return tuple(steps)


def migrate(migration: Migration):
    chain = migration.chain()
    config = CCIP[chain]
    hq = migration.get_contract("RipeHq")
    governance = str(hq.governance())
    token_admin_registry = ccip.token_admin_registry(chain)

    safe_steps = []
    registration_confirm_steps = []
    hq_initiate_steps = []
    hq_confirm_steps = []
    admin_steps = []
    mint_rights_needed = []

    # This is deliberately a complete read-only preflight before any lane or
    # ownership mutation. confirmNewAddressToRegistry(address) cannot encode an
    # expected id, so a missing pool is supported only from the exact empty
    # 23/24 state under an explicitly reserved exclusive governance window.
    missing_hq_labels = []
    for label, contract_name, _token_name, _can_green, _can_ripe in POOLS:
        pool = migration.get_solidity_contract(contract_name, source_file=SOURCE_FILE)
        reg_id = int(hq.getRegId(pool.address))
        if reg_id == 0:
            missing_hq_labels.append(label)
        else:
            assert reg_id == CCIP_POOL_HQ_IDS[label], (
                f"{label} pool has RipeHq id {reg_id}, expected "
                f"{CCIP_POOL_HQ_IDS[label]}"
            )
    hq_append_plan = _hq_append_plan(migration, hq, missing_hq_labels)
    hq_append_plan_sha256 = (
        ccip.safe_plan_sha256(hq_append_plan) if hq_append_plan else None
    )
    ccip.require_mainnet_hq_append_preflight(
        chain,
        hq,
        missing_hq_labels,
        expected_plan_sha256=hq_append_plan_sha256,
    )
    for step in hq_append_plan:
        target = (
            safe_steps
            if step["phase"] == 1
            else registration_confirm_steps
            if step["phase"] == 2
            else hq_initiate_steps
            if step["phase"] == 3
            else hq_confirm_steps
        )
        target.append((step["description"], step["target"], step["data"]))
    for label in missing_hq_labels:
        ccip.require_activation_policy(migration, label)

    # Validate the complete RIPE+GREEN package before either token can mutate.
    # The execution loop below still re-reads its local state, but a late GREEN,
    # RipeHq, routing, ownership, or peer failure cannot follow a RIPE broadcast.
    ccip.complete_mainnet_activation_preflight(
        migration,
        POOLS,
        SOURCE_FILE,
        hq,
        token_admin_registry,
        governance,
    )

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
            ), (
                f"{label} has unexpected pending CCIP administrator {pending_administrator}"
            )
            ccip.require_activation_policy(migration, label)
            admin_steps.append((label, token, pending_administrator))

        assert str(pool.getToken()).lower() == token.lower(), (
            f"{label} pool has wrong token"
        )
        assert str(pool.getRouter()).lower() == config["ROUTER"].lower(), (
            f"{label} pool has wrong router"
        )
        assert str(pool.getRmnProxy()).lower() == config["RMN_PROXY"].lower(), (
            f"{label} pool has wrong RMN proxy"
        )
        assert pool.typeAndVersion() == "BurnMintTokenPool 1.5.1", (
            f"{label} pool has wrong source version"
        )
        assert bool(pool.canMintGreen()) is can_green, (
            f"{label} pool has wrong GREEN capability"
        )
        assert bool(pool.canMintRipe()) is can_ripe, (
            f"{label} pool has wrong RIPE capability"
        )
        owner = str(pool.owner())
        governance_owns_pool = owner.lower() == governance.lower()

        log.h1(f"Wiring the {label} pool")

        for remote_chain in config["REMOTE_CHAINS"]:
            remote_selector = CCIP[remote_chain]["CHAIN_SELECTOR"]
            try:
                remote_pool = migration.get_address_on_chain(
                    remote_chain, contract_name
                )
                remote_token = migration.get_address_on_chain(remote_chain, token_name)
            except (FileNotFoundError, KeyError):
                raise Exception(
                    f"no {contract_name} in the {remote_chain} manifest - run the "
                    f"CcipPools migration on {remote_chain} before wiring {chain}"
                )

            lane_is_configured = pool.isSupportedChain(remote_selector)
            lane_policy_pending = False
            if lane_is_configured:
                log.info(
                    f"\t{remote_chain} ({remote_selector}) already wired; revalidating"
                )
                policy = ccip.lane_policy_for_revalidation(chain, remote_chain, label)
            else:
                policy = ccip.require_activation_policy(migration, label, remote_chain)
                log.info(f"\t{remote_chain}: pool {remote_pool}, token {remote_token}")
                chain_update = (
                    remote_selector,
                    [ccip.encode_address(remote_pool)],
                    ccip.encode_address(remote_token),
                    policy.outbound.as_tuple(),
                    policy.inbound.as_tuple(),
                )
                if governance_owns_pool:
                    safe_steps.append(
                        (
                            f"{label} pool: add the {remote_chain} lane with the "
                            "owner-selected directional rate policy",
                            pool.address,
                            _calldata(
                                "applyChainUpdates(uint64[],(uint64,bytes[],bytes,"
                                "(bool,uint128,uint128),(bool,uint128,uint128))[])",
                                [
                                    "uint64[]",
                                    "(uint64,bytes[],bytes,(bool,uint128,uint128),"
                                    "(bool,uint128,uint128))[]",
                                ],
                                [[], [chain_update]],
                            ),
                        )
                    )
                    lane_policy_pending = True
                else:
                    ccip.execute_activation_mutation(
                        migration,
                        label,
                        pool.applyChainUpdates,
                        [],
                        [chain_update],
                        remote_chain=remote_chain,
                    )

            if lane_is_configured:
                outbound, inbound, rate_limit_admin = ccip.current_lane_policy_fields(
                    pool, remote_selector
                )
                if (outbound, inbound) != (
                    policy.outbound.as_tuple(),
                    policy.inbound.as_tuple(),
                ):
                    if governance_owns_pool:
                        ccip.require_activation_policy(migration, label, remote_chain)
                        safe_steps.append(
                            (
                                f"{label} pool: apply the owner-selected "
                                f"{remote_chain} directional rate policy",
                                pool.address,
                                _calldata(
                                    "setChainRateLimiterConfig(uint64,"
                                    "(bool,uint128,uint128),(bool,uint128,uint128))",
                                    [
                                        "uint64",
                                        "(bool,uint128,uint128)",
                                        "(bool,uint128,uint128)",
                                    ],
                                    [
                                        remote_selector,
                                        policy.outbound.as_tuple(),
                                        policy.inbound.as_tuple(),
                                    ],
                                ),
                            )
                        )
                        lane_policy_pending = True
                    else:
                        ccip.execute_activation_mutation(
                            migration,
                            label,
                            pool.setChainRateLimiterConfig,
                            remote_selector,
                            policy.outbound.as_tuple(),
                            policy.inbound.as_tuple(),
                            remote_chain=remote_chain,
                        )
            else:
                rate_limit_admin = str(pool.getRateLimitAdmin())

            if rate_limit_admin.lower() != policy.rate_limit_admin.lower():
                if governance_owns_pool:
                    ccip.require_activation_policy(migration, label, remote_chain)
                    safe_steps.append(
                        (
                            f"{label} pool: set the owner-selected rate-limit admin",
                            pool.address,
                            _calldata(
                                "setRateLimitAdmin(address)",
                                ["address"],
                                [policy.rate_limit_admin],
                            ),
                        )
                    )
                    lane_policy_pending = True
                else:
                    ccip.execute_activation_mutation(
                        migration,
                        label,
                        pool.setRateLimitAdmin,
                        policy.rate_limit_admin,
                        remote_chain=remote_chain,
                    )

            if lane_policy_pending:
                if lane_is_configured:
                    ccip.assert_lane_peer_configuration(
                        pool, remote_selector, remote_pool, remote_token
                    )
                log.info(
                    f"\t{remote_chain} rate/lane mutation is Safe-pending; "
                    "rerun for full revalidation after execution"
                )
            else:
                ccip.assert_lane_configuration(
                    pool,
                    remote_selector,
                    remote_pool,
                    remote_token,
                    policy.outbound.as_tuple(),
                    policy.inbound.as_tuple(),
                    policy.rate_limit_admin,
                )

        log.h2(f"Handing the {label} pool to governance")

        if governance_owns_pool:
            log.info(f"\talready owned by governance ({governance})")
        else:
            # Two step: the deployer offers, governance accepts. The Safe is
            # not the deployer, so it never completes here.
            ccip.execute_activation_mutation(
                migration, label, pool.transferOwnership, governance
            )
            log.info(f"\townership offered to {governance}")
            safe_steps.append(
                (
                    f"{label} pool: accept ownership",
                    pool.address,
                    _calldata("acceptOwnership()", [], []),
                )
            )

        reg_id = int(hq.getRegId(pool.address))
        if reg_id == 0:
            expected_reg_id = CCIP_POOL_HQ_IDS[label]
            ccip.require_activation_policy(migration, label)
            mint_rights_needed.append(
                (label, expected_reg_id, can_green, can_ripe)
            )
        else:
            assert reg_id == CCIP_POOL_HQ_IDS[label], (
                f"{label} pool has RipeHq id {reg_id}, expected {CCIP_POOL_HQ_IDS[label]}"
            )
            hq_config = tuple(hq.hqConfig(reg_id))
            actual_capabilities = (
                bool(hq_config[1]),
                bool(hq_config[2]),
                bool(hq_config[3]),
            )
            expected_capabilities = (can_green, can_ripe, False)
            assert actual_capabilities in (
                (False, False, False),
                expected_capabilities,
            ), f"{label} RipeHq capabilities {actual_capabilities} are unexpected"
            if actual_capabilities == expected_capabilities:
                log.info(f"\tRipeHq id {reg_id} and capabilities revalidated")
            else:
                ccip.require_activation_policy(migration, label)
                mint_rights_needed.append((label, reg_id, can_green, can_ripe))
                hq_initiate_steps.append(
                    (
                        f"{label} pool: initiate token-specific mint rights",
                        hq.address,
                        _calldata(
                            "initiateHqConfigChange(uint256,bool,bool,bool)",
                            ["uint256", "bool", "bool", "bool"],
                            [reg_id, can_green, can_ripe, False],
                        ),
                    )
                )
                hq_confirm_steps.append(
                    (
                        f"{label} pool: confirm token-specific mint rights LAST",
                        hq.address,
                        _calldata(
                            "confirmHqConfigChange(uint256)", ["uint256"], [reg_id]
                        ),
                    )
                )

        configured_pool = str(token_admin_registry.getPool(token))
        if configured_pool.lower() == ccip.ZERO_ADDRESS:
            ccip.require_activation_policy(migration, label)
            safe_steps.append(
                (
                    f"{label} pool: point CCIP at it (admin must be accepted first)",
                    config["TOKEN_ADMIN_REGISTRY"],
                    _calldata(
                        "setPool(address,address)",
                        ["address", "address"],
                        [token, pool.address],
                    ),
                )
            )
        else:
            assert configured_pool.lower() == str(pool.address).lower(), (
                f"{label} TokenAdminRegistry pool {configured_pool} does not match {pool.address}"
            )
            log.info("\tTokenAdminRegistry pool assignment revalidated")

    log.h1("What the Safe has to run")

    log.h2("1. Claim the CCIP admin role, once per token")
    if admin_steps:
        log.info(
            f"\tRegistryModuleOwnerCustom {config['REGISTRY_MODULE_OWNER_CUSTOM']}"
        )
        for label, token, pending_administrator in admin_steps:
            if pending_administrator.lower() != governance.lower():
                log.info(f"\t  {label} registerAdminViaGetCCIPAdmin(address)")
                log.info(f"\t    to:   {config['REGISTRY_MODULE_OWNER_CUSTOM']}")
                log.info(
                    f"\t    data: {_calldata('registerAdminViaGetCCIPAdmin(address)', ['address'], [token])}"
                )
            log.info(
                f"\t  {label} acceptAdminRole(address) on {config['TOKEN_ADMIN_REGISTRY']}"
            )
            log.info(f"\t    to:   {config['TOKEN_ADMIN_REGISTRY']}")
            log.info(
                f"\t    data: {_calldata('acceptAdminRole(address)', ['address'], [token])}"
            )
        log.info("")
        log.info("\tThe token's getCCIPAdmin() returns RipeHq governance, so the")
        log.info("\tSafe is the address proposed and the Safe is who accepts.")
    else:
        log.info("\tgovernance is already administrator for both tokens")

    log.h2("2. Immediate ownership, lane, routing, and registration-start calls")
    for description, target, data in safe_steps:
        log.info(f"\t{description}")
        log.info(f"\t  to:   {target}")
        log.info(f"\t  data: {data}")

    log.h2("3. AFTER registryChangeTimeLock: confirm exact registration ids")
    for description, target, data in registration_confirm_steps:
        log.info(f"\t{description}")
        log.info(f"\t  to:   {target}")
        log.info(f"\t  data: {data}")

    log.h2("4. Initiate token-specific RipeHq mint rights")
    for description, target, data in hq_initiate_steps:
        log.info(f"\t{description}")
        log.info(f"\t  to:   {target}")
        log.info(f"\t  data: {data}")

    log.h2("5. AFTER a second registryChangeTimeLock: confirm mint rights LAST")
    if mint_rights_needed:
        for description, target, data in hq_confirm_steps:
            log.info(f"\t{description}")
            log.info(f"\t  to:   {target}")
            log.info(f"\t  data: {data}")
        log.info("")
        log.info("\tGranting before ownership moves would leave the deployer owning")
        log.info("\ta pool that can mint. Do not reorder.")
    else:
        log.info(
            "\tRipeHq ids and token-specific mint capabilities already revalidated"
        )
    if hq_append_plan_sha256 is not None:
        log.info(f"\tApproved HQ append plan SHA-256: {hq_append_plan_sha256}")
