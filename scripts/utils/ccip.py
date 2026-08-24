"""
Helpers for talking to the Chainlink CCIP contracts that Ripe does not deploy itself
(the token admin registry and the registry module used to claim a token's admin role).
"""

import hashlib
import json

import boa
from eth_abi.abi import encode

from config.Ccip import (
    CCIP,
    CCIP_POOL_HQ_IDS,
    ccip_revalidation_policy,
    require_ccip_hq_append_window,
    require_ccip_wiring_gates,
)
from scripts.utils import log

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
MAINNET_TOKEN_DECIMALS = 18

TOKEN_ADMIN_REGISTRY_ABI = [
    {
        "type": "function",
        "name": "getPool",
        "stateMutability": "view",
        "inputs": [{"name": "token", "type": "address"}],
        "outputs": [{"name": "", "type": "address"}],
    },
    {
        "type": "function",
        "name": "getTokenConfig",
        "stateMutability": "view",
        "inputs": [{"name": "token", "type": "address"}],
        "outputs": [
            {
                "name": "",
                "type": "tuple",
                "components": [
                    {"name": "administrator", "type": "address"},
                    {"name": "pendingAdministrator", "type": "address"},
                    {"name": "tokenPool", "type": "address"},
                ],
            }
        ],
    },
    {
        "type": "function",
        "name": "setPool",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "localToken", "type": "address"},
            {"name": "pool", "type": "address"},
        ],
        "outputs": [],
    },
    {
        "type": "function",
        "name": "acceptAdminRole",
        "stateMutability": "nonpayable",
        "inputs": [{"name": "localToken", "type": "address"}],
        "outputs": [],
    },
    {
        "type": "function",
        "name": "transferAdminRole",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "localToken", "type": "address"},
            {"name": "newAdmin", "type": "address"},
        ],
        "outputs": [],
    },
]

ROUTER_ABI = [
    {
        "type": "function",
        "name": "getFee",
        "stateMutability": "view",
        "inputs": [
            {"name": "destinationChainSelector", "type": "uint64"},
            {
                "name": "message",
                "type": "tuple",
                "components": [
                    {"name": "receiver", "type": "bytes"},
                    {"name": "data", "type": "bytes"},
                    {
                        "name": "tokenAmounts",
                        "type": "tuple[]",
                        "components": [
                            {"name": "token", "type": "address"},
                            {"name": "amount", "type": "uint256"},
                        ],
                    },
                    {"name": "feeToken", "type": "address"},
                    {"name": "extraArgs", "type": "bytes"},
                ],
            },
        ],
        "outputs": [{"name": "fee", "type": "uint256"}],
    },
    {
        "type": "function",
        "name": "ccipSend",
        "stateMutability": "payable",
        "inputs": [
            {"name": "destinationChainSelector", "type": "uint64"},
            {
                "name": "message",
                "type": "tuple",
                "components": [
                    {"name": "receiver", "type": "bytes"},
                    {"name": "data", "type": "bytes"},
                    {
                        "name": "tokenAmounts",
                        "type": "tuple[]",
                        "components": [
                            {"name": "token", "type": "address"},
                            {"name": "amount", "type": "uint256"},
                        ],
                    },
                    {"name": "feeToken", "type": "address"},
                    {"name": "extraArgs", "type": "bytes"},
                ],
            },
        ],
        "outputs": [{"name": "messageId", "type": "bytes32"}],
    },
    {
        "type": "function",
        "name": "isChainSupported",
        "stateMutability": "view",
        "inputs": [{"name": "destChainSelector", "type": "uint64"}],
        "outputs": [{"name": "supported", "type": "bool"}],
    },
]

REGISTRY_MODULE_OWNER_CUSTOM_ABI = [
    {
        "type": "function",
        "name": "registerAdminViaGetCCIPAdmin",
        "stateMutability": "nonpayable",
        "inputs": [{"name": "token", "type": "address"}],
        "outputs": [],
    },
    {
        "type": "function",
        "name": "registerAdminViaOwner",
        "stateMutability": "nonpayable",
        "inputs": [{"name": "token", "type": "address"}],
        "outputs": [],
    },
]


def token_admin_registry(chain):
    return boa.loads_abi(
        json.dumps(TOKEN_ADMIN_REGISTRY_ABI), name="TokenAdminRegistry"
    ).at(CCIP[chain]["TOKEN_ADMIN_REGISTRY"])


def registry_module_owner_custom(chain):
    return boa.loads_abi(
        json.dumps(REGISTRY_MODULE_OWNER_CUSTOM_ABI), name="RegistryModuleOwnerCustom"
    ).at(CCIP[chain]["REGISTRY_MODULE_OWNER_CUSTOM"])


def router(chain):
    return boa.loads_abi(json.dumps(ROUTER_ABI), name="Router").at(
        CCIP[chain]["ROUTER"]
    )


def encode_address(address):
    """
    CCIP stores remote pool / token addresses abi encoded, so they work for non evm chains.
    """
    return encode(["address"], [str(address)])


def _rate_limit_config(state):
    """Return only the policy fields from a TokenBucket getter result."""
    if all(hasattr(state, field) for field in ("isEnabled", "capacity", "rate")):
        return (bool(state.isEnabled), int(state.capacity), int(state.rate))

    values = tuple(state)
    if len(values) != 5:
        raise AssertionError(
            f"unexpected CCIP TokenBucket shape: expected 5 values, got {len(values)}"
        )
    # RateLimiter.TokenBucket(tokens, lastUpdated, isEnabled, capacity, rate)
    return (bool(values[2]), int(values[3]), int(values[4]))


def _normalized_bytes(value):
    if isinstance(value, str):
        if not value.startswith("0x") or len(value) % 2:
            raise AssertionError(f"unexpected CCIP bytes value {value!r}")
        try:
            return bytes.fromhex(value[2:])
        except ValueError:
            raise AssertionError(f"unexpected CCIP bytes value {value!r}") from None
    return bytes(value)


def current_lane_policy_fields(pool, remote_selector):
    """Read both directional policies and the pool-wide rate-limit admin."""
    outbound = _rate_limit_config(
        pool.getCurrentOutboundRateLimiterState(remote_selector)
    )
    inbound = _rate_limit_config(
        pool.getCurrentInboundRateLimiterState(remote_selector)
    )
    rate_limit_admin = str(pool.getRateLimitAdmin())
    return outbound, inbound, rate_limit_admin


def assert_lane_peer_configuration(pool, remote_selector, remote_pool, remote_token):
    """Revalidate selector, exact remote token, and the sole remote pool."""
    expected_pool = encode_address(remote_pool)
    expected_token = encode_address(remote_token)

    assert pool.isSupportedChain(remote_selector), (
        f"CCIP selector {remote_selector} is not configured"
    )

    actual_token = _normalized_bytes(pool.getRemoteToken(remote_selector))
    assert actual_token == expected_token, (
        f"CCIP selector {remote_selector} has remote token 0x{actual_token.hex()}, "
        f"expected 0x{expected_token.hex()}"
    )

    actual_pools = tuple(
        _normalized_bytes(value) for value in pool.getRemotePools(remote_selector)
    )
    assert actual_pools == (expected_pool,), (
        f"CCIP selector {remote_selector} has remote pools "
        f"{['0x' + value.hex() for value in actual_pools]}, expected only "
        f"0x{expected_pool.hex()}"
    )


def assert_lane_rate_policy(
    pool,
    remote_selector,
    expected_outbound_rate_limit,
    expected_inbound_rate_limit,
    expected_rate_limit_admin,
):
    """Revalidate both rate-limit directions and the pool-wide administrator."""

    outbound, inbound, rate_limit_admin = current_lane_policy_fields(
        pool, remote_selector
    )
    assert outbound == expected_outbound_rate_limit, (
        f"CCIP selector {remote_selector} outbound rate policy {outbound} does "
        f"not match expected {expected_outbound_rate_limit}"
    )
    assert inbound == expected_inbound_rate_limit, (
        f"CCIP selector {remote_selector} inbound rate policy {inbound} does "
        f"not match expected {expected_inbound_rate_limit}"
    )

    assert rate_limit_admin.lower() == expected_rate_limit_admin.lower(), (
        f"CCIP rateLimitAdmin {rate_limit_admin} does not match expected "
        f"{expected_rate_limit_admin}"
    )


def assert_lane_configuration(
    pool,
    remote_selector,
    remote_pool,
    remote_token,
    expected_outbound_rate_limit,
    expected_inbound_rate_limit,
    expected_rate_limit_admin,
):
    """Revalidate every security-relevant field of an existing CCIP lane.

    `isSupportedChain()` alone is not evidence that the lane points at the
    intended peer. A selector can be present with the wrong token, an old or
    additional pool, or an unexpected rate policy. Migration replays call this
    after both the add and already-present paths so neither path silently skips
    verification.
    """
    assert_lane_peer_configuration(pool, remote_selector, remote_pool, remote_token)
    assert_lane_rate_policy(
        pool,
        remote_selector,
        expected_outbound_rate_limit,
        expected_inbound_rate_limit,
        expected_rate_limit_admin,
    )


# Client.GENERIC_EXTRA_ARGS_V2_TAG
GENERIC_EXTRA_ARGS_V2_TAG = bytes.fromhex("181dcf10")


def extra_args(gas_limit=0, allow_out_of_order=True):
    """
    Client._argsToBytes(Client.GenericExtraArgsV2). Gas limit 0 is right for a plain token
    transfer to an EOA - there is no ccipReceive callback to pay for on the other side.
    """
    return GENERIC_EXTRA_ARGS_V2_TAG + encode(
        ["uint256", "bool"], [gas_limit, allow_out_of_order]
    )


def token_transfer_message(receiver, token, amount, fee_token=ZERO_ADDRESS):
    """
    Client.EVM2AnyMessage carrying tokens and nothing else. `fee_token` zero means the
    fee is paid in the source chain's native coin.
    """
    return (
        encode_address(receiver),
        b"",
        [(str(token), amount)],
        str(fee_token),
        extra_args(),
    )


def lane_policy_for_revalidation(local_chain, remote_chain, token_label):
    """Return a typed owner choice, or the exact observed no-op baseline."""
    return ccip_revalidation_policy(local_chain, remote_chain, token_label)


def require_activation_policy(migration, token_label, remote_chain=None):
    """Resolve the exact lane-bound policy required by a CCIP mutation."""
    chain = migration.chain()
    remotes = tuple(CCIP[chain]["REMOTE_CHAINS"])
    if remote_chain is None:
        if len(remotes) != 1:
            raise RuntimeError(
                f"CCIP_MUTATION_REMOTE_CHAIN_REQUIRED: {chain} has {len(remotes)} peers"
            )
        remote_chain = remotes[0]
    return require_ccip_wiring_gates(chain, remote_chain, token_label)


def execute_activation_mutation(
    migration, token_label, action, *args, remote_chain=None
):
    """Execute a CCIP activation mutation only after every policy gate closes.

    Existing lanes can be fully revalidated while owner/evidence decisions are
    unresolved. Any state-changing repair, role transition, routing update, or
    capability change must cross the same gate even when remote wiring already
    exists.
    """
    require_activation_policy(migration, token_label, remote_chain)
    return migration.execute(action, *args)


def safe_plan_sha256(steps):
    """Return a deterministic digest for ordered Safe target/calldata stages."""

    payload = json.dumps(
        list(steps), ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def require_mainnet_hq_append_preflight(
    chain, hq, missing_labels, *, expected_plan_sha256=None
):
    """Fail before mutation unless the exact empty 23/24 window is reserved.

    RipeHq's confirm call does not accept an expected registry id, so calldata
    cannot enforce ids 23 and 24. Static Safe planning supports only the clean
    two-row case and requires an explicit exclusive governance append window;
    partial registration is intentionally a manual recovery case.
    """
    missing_labels = tuple(missing_labels)
    if not missing_labels:
        return None
    expected_labels = tuple(CCIP_POOL_HQ_IDS)
    if missing_labels != expected_labels:
        raise RuntimeError(
            "CCIP_HQ_APPEND_WINDOW_PARTIAL_STATE: expected both RIPE and GREEN "
            f"to be absent in order, got {missing_labels!r}"
        )
    next_id = int(hq.numAddrs())
    if next_id != CCIP_POOL_HQ_IDS["RIPE"]:
        raise RuntimeError(
            "CCIP_HQ_APPEND_CURSOR_MISMATCH: RipeHq append cursor must be "
            f"exactly 23, got {next_id}"
        )
    for label, expected_id in CCIP_POOL_HQ_IDS.items():
        actual = hq.getAddr(expected_id)
        if not _is(actual, ZERO_ADDRESS):
            raise RuntimeError(
                f"CCIP_HQ_APPEND_SLOT_OCCUPIED: RipeHq slot {expected_id} "
                f"for {label} must be empty, got {actual}"
            )
    return require_ccip_hq_append_window(
        chain, expected_plan_sha256=expected_plan_sha256
    )


def complete_mainnet_activation_preflight(
    migration,
    pools,
    source_file,
    hq,
    token_admin_registry_contract,
    governance,
):
    """Validate both token packages completely before the first mutation.

    Mainnet activation is a two-token package. A RIPE repair must not be sent and
    only then discover invalid GREEN, RipeHq, or TokenAdminRegistry state. This
    function is intentionally read-only and is called before either migration
    enters its mutation loop.
    """

    chain = migration.chain()
    config = CCIP[chain]
    governance = str(governance)
    for label, contract_name, token_name, can_green, can_ripe in pools:
        token = migration.get_address(token_name)
        pool = migration.get_solidity_contract(
            contract_name, source_file=source_file
        )
        token_config = tuple(token_admin_registry_contract.getTokenConfig(token))
        administrator = str(token_config[0])
        pending_administrator = str(token_config[1])
        if administrator.lower() == governance.lower():
            assert _is(pending_administrator, ZERO_ADDRESS), (
                f"{label} has unexpected pending CCIP administrator "
                f"{pending_administrator}"
            )
        else:
            assert _is(administrator, ZERO_ADDRESS), (
                f"{label} has unexpected CCIP administrator {administrator}"
            )
            assert pending_administrator.lower() in (
                ZERO_ADDRESS.lower(),
                governance.lower(),
            ), f"{label} has unexpected pending CCIP administrator {pending_administrator}"
            require_activation_policy(migration, label)

        assert _is(pool.getToken(), token), f"{label} pool has wrong token"
        assert _is(pool.getRouter(), config["ROUTER"]), f"{label} pool has wrong router"
        assert _is(pool.getRmnProxy(), config["RMN_PROXY"]), (
            f"{label} pool has wrong RMN proxy"
        )
        assert int(pool.getTokenDecimals()) == MAINNET_TOKEN_DECIMALS, (
            f"{label} pool has wrong token decimals"
        )
        assert (
            not bool(pool.getAllowListEnabled())
            and tuple(pool.getAllowList()) == ()
        ), f"{label} pool has an unexpected allowlist"
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
        lane_mutation_needed = False
        for remote_chain in config["REMOTE_CHAINS"]:
            remote_selector = CCIP[remote_chain]["CHAIN_SELECTOR"]
            try:
                remote_pool = migration.get_address_on_chain(
                    remote_chain, contract_name
                )
                remote_token = migration.get_address_on_chain(
                    remote_chain, token_name
                )
            except (FileNotFoundError, KeyError) as exc:
                raise RuntimeError(
                    f"no {contract_name} in the {remote_chain} manifest - run the "
                    f"CcipPools migration on {remote_chain} before wiring {chain}"
                ) from exc

            if pool.isSupportedChain(remote_selector):
                assert_lane_peer_configuration(
                    pool, remote_selector, remote_pool, remote_token
                )
                policy = lane_policy_for_revalidation(chain, remote_chain, label)
                outbound, inbound, rate_limit_admin = current_lane_policy_fields(
                    pool, remote_selector
                )
                if (outbound, inbound, rate_limit_admin.lower()) != (
                    policy.outbound.as_tuple(),
                    policy.inbound.as_tuple(),
                    policy.rate_limit_admin.lower(),
                ):
                    selected = require_activation_policy(
                        migration, label, remote_chain
                    )
                    assert selected == policy, (
                        f"{label} selected policy changed during preflight"
                    )
                    lane_mutation_needed = True
            else:
                require_activation_policy(migration, label, remote_chain)
                lane_mutation_needed = True

        reg_id = int(hq.getRegId(pool.address))
        hq_is_active = False
        hq_mutation_needed = False
        if reg_id == 0:
            hq_mutation_needed = True
        else:
            assert reg_id == CCIP_POOL_HQ_IDS[label], (
                f"{label} pool has RipeHq id {reg_id}, expected "
                f"{CCIP_POOL_HQ_IDS[label]}"
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
            hq_is_active = actual_capabilities == expected_capabilities
            hq_mutation_needed = not hq_is_active

        configured_pool = str(token_admin_registry_contract.getPool(token))
        if not _is(configured_pool, ZERO_ADDRESS):
            assert _is(configured_pool, pool.address), (
                f"{label} TokenAdminRegistry pool {configured_pool} does not match "
                f"{pool.address}"
            )
        routing_is_active = _is(configured_pool, pool.address)
        routing_mutation_needed = not routing_is_active

        # Once either mint authority or CCIP routing is active, an operational
        # owner other than governance violates the migration's core invariant.
        if not governance_owns_pool and (hq_is_active or routing_is_active):
            raise RuntimeError(
                f"CCIP_ACTIVE_POOL_NOT_GOVERNANCE_OWNED: {label} owner {owner}"
            )

        if (
            not governance_owns_pool
            or lane_mutation_needed
            or hq_mutation_needed
            or routing_mutation_needed
        ):
            require_activation_policy(migration, label)


def require_mainnet_activation_finalized(migration, pools, source_file):
    """Read back the complete mainnet activation before recording completion.

    The wiring stage may legitimately stop with governance/Safe work pending.
    This function is deliberately read-only and uses explicit exceptions so a
    completion marker cannot be produced under ``python -O`` from partial state.
    """

    chain = migration.chain()
    config = CCIP[chain]
    hq = migration.get_contract("RipeHq")
    governance = str(hq.governance())
    registry = token_admin_registry(chain)

    expected_cursor = max(CCIP_POOL_HQ_IDS.values()) + 1
    if int(hq.numAddrs()) != expected_cursor:
        raise RuntimeError(
            "CCIP_FINALIZATION_HQ_CURSOR_MISMATCH: expected next RipeHq id "
            f"{expected_cursor}, got {int(hq.numAddrs())}"
        )

    for label, contract_name, token_name, can_green, can_ripe in pools:
        token = migration.get_address(token_name)
        pool = migration.get_solidity_contract(
            contract_name, source_file=source_file
        )
        administrator, pending_administrator, configured_pool = tuple(
            registry.getTokenConfig(token)
        )
        if not _is(administrator, governance) or not _is(
            pending_administrator, ZERO_ADDRESS
        ):
            raise RuntimeError(
                f"CCIP_FINALIZATION_ADMIN_PENDING: {label} administrator state "
                f"is ({administrator}, {pending_administrator})"
            )
        if not _is(configured_pool, pool.address) or not _is(
            registry.getPool(token), pool.address
        ):
            raise RuntimeError(
                f"CCIP_FINALIZATION_POOL_ROUTE_MISMATCH: {label} is not routed "
                f"through {pool.address}"
            )
        expected_static = (
            (pool.getToken(), token, "token"),
            (pool.getRouter(), config["ROUTER"], "router"),
            (pool.getRmnProxy(), config["RMN_PROXY"], "RMN proxy"),
            (pool.owner(), governance, "owner"),
        )
        for actual, expected, field in expected_static:
            if not _is(actual, expected):
                raise RuntimeError(
                    f"CCIP_FINALIZATION_POOL_{field.upper().replace(' ', '_')}_MISMATCH: "
                    f"{label} has {actual}, expected {expected}"
                )
        if int(pool.getTokenDecimals()) != MAINNET_TOKEN_DECIMALS:
            raise RuntimeError(
                f"CCIP_FINALIZATION_POOL_TOKEN_DECIMALS_MISMATCH: {label}"
            )
        if bool(pool.getAllowListEnabled()) or tuple(pool.getAllowList()) != ():
            raise RuntimeError(
                f"CCIP_FINALIZATION_POOL_ALLOWLIST_MISMATCH: {label}"
            )
        if pool.typeAndVersion() != "BurnMintTokenPool 1.5.1":
            raise RuntimeError(
                f"CCIP_FINALIZATION_POOL_VERSION_MISMATCH: {label}"
            )
        if bool(pool.canMintGreen()) is not can_green or bool(
            pool.canMintRipe()
        ) is not can_ripe:
            raise RuntimeError(
                f"CCIP_FINALIZATION_POOL_CAPABILITY_MISMATCH: {label}"
            )

        expected_selectors = tuple(
            sorted(
                int(CCIP[remote_chain]["CHAIN_SELECTOR"])
                for remote_chain in config["REMOTE_CHAINS"]
            )
        )
        actual_selectors = tuple(
            sorted(int(selector) for selector in pool.getSupportedChains())
        )
        if actual_selectors != expected_selectors:
            raise RuntimeError(
                "CCIP_FINALIZATION_LANE_SET_MISMATCH: "
                f"{label} has selectors {actual_selectors}, expected "
                f"{expected_selectors}"
            )

        for remote_chain in config["REMOTE_CHAINS"]:
            selector = CCIP[remote_chain]["CHAIN_SELECTOR"]
            if not pool.isSupportedChain(selector):
                raise RuntimeError(
                    f"CCIP_FINALIZATION_LANE_MISSING: {label} to {remote_chain}"
                )
            remote_pool = migration.get_address_on_chain(
                remote_chain, contract_name
            )
            remote_token = migration.get_address_on_chain(remote_chain, token_name)
            actual_pools = tuple(pool.getRemotePools(selector))
            expected_pool = encode_address(remote_pool)
            if tuple(actual_pools) != (expected_pool,):
                raise RuntimeError(
                    f"CCIP_FINALIZATION_REMOTE_POOL_MISMATCH: {label} to {remote_chain}"
                )
            if bytes(pool.getRemoteToken(selector)) != encode_address(remote_token):
                raise RuntimeError(
                    f"CCIP_FINALIZATION_REMOTE_TOKEN_MISMATCH: {label} to {remote_chain}"
                )
            policy = lane_policy_for_revalidation(chain, remote_chain, label)
            outbound, inbound, rate_limit_admin = current_lane_policy_fields(
                pool, selector
            )
            expected_policy = (
                policy.outbound.as_tuple(),
                policy.inbound.as_tuple(),
                policy.rate_limit_admin.lower(),
            )
            if (outbound, inbound, rate_limit_admin.lower()) != expected_policy:
                raise RuntimeError(
                    f"CCIP_FINALIZATION_RATE_POLICY_MISMATCH: {label} to {remote_chain}"
                )

        reg_id = CCIP_POOL_HQ_IDS[label]
        if int(hq.getRegId(pool.address)) != reg_id or not _is(
            hq.getAddr(reg_id), pool.address
        ):
            raise RuntimeError(
                f"CCIP_FINALIZATION_HQ_ID_MISMATCH: {label} must be id {reg_id}"
            )
        hq_config = tuple(hq.hqConfig(reg_id))
        if tuple(bool(value) for value in hq_config[1:4]) != (
            can_green,
            can_ripe,
            False,
        ):
            raise RuntimeError(
                f"CCIP_FINALIZATION_HQ_CAPABILITY_MISMATCH: {label}"
            )
        if bool(hq.hasPendingHqConfigChange(reg_id)):
            raise RuntimeError(
                f"CCIP_FINALIZATION_HQ_CONFIG_PENDING: {label}"
            )
        if int(tuple(hq.pendingNewAddr(pool.address))[2]) != 0:
            raise RuntimeError(
                f"CCIP_FINALIZATION_HQ_REGISTRATION_PENDING: {label}"
            )
        if int(tuple(hq.pendingAddrUpdate(reg_id))[2]) != 0 or int(
            tuple(hq.pendingAddrDisable(reg_id))[1]
        ) != 0:
            raise RuntimeError(
                f"CCIP_FINALIZATION_HQ_ADDRESS_CHANGE_PENDING: {label}"
            )

    log.h1("CCIP mainnet activation fully revalidated")


def claim_admin_role(migration, token, token_label):
    """
    Makes the deployer the CCIP administrator of `token` when it is allowed to become it:
    claims an unclaimed token via its `getCCIPAdmin()`, and accepts a role already
    pending for the deployer.
    Returns whoever the administrator is once that is done.
    """
    chain = migration.chain()
    deployer = migration.account().address
    registry = token_admin_registry(chain)

    administrator, pending, _pool = registry.getTokenConfig(token)

    if _is(administrator, ZERO_ADDRESS) and _is(pending, ZERO_ADDRESS):
        log.info("token has no CCIP administrator, claiming it via `getCCIPAdmin()`")
        module = registry_module_owner_custom(chain)
        execute_activation_mutation(
            migration, token_label, module.registerAdminViaGetCCIPAdmin, token
        )
        administrator, pending, _pool = registry.getTokenConfig(token)

    if _is(pending, deployer):
        log.info("accepting the pending CCIP administrator role")
        execute_activation_mutation(
            migration, token_label, registry.acceptAdminRole, token
        )
        administrator = deployer

    return administrator


def set_pool(migration, token, pool, token_label):
    """
    Points CCIP at `pool` for `token`. Only the token's CCIP administrator can do that,
    so when the deployer does not hold that role this logs the call whoever does needs
    to make, and returns False.
    """
    chain = migration.chain()
    registry = token_admin_registry(chain)

    if _is(registry.getPool(token), pool):
        log.info(f"CCIP already routes {token} through {pool}")
        return True

    administrator = claim_admin_role(migration, token, token_label)
    if _is(administrator, migration.account().address):
        execute_activation_mutation(
            migration, token_label, registry.setPool, token, pool
        )
        return True

    # The fallback is actionable manual transaction guidance, so do not emit
    # it while the same owner/evidence decisions that guard execution are open.
    require_activation_policy(migration, token_label)
    log.error(
        f"ACTION REQUIRED: the CCIP administrator for this token is {administrator}, not the deployer, so it "
        f"has to be the one pointing CCIP at the new pool. Either do it from the CCIP "
        f"token manager UI, or from that wallet run:\n"
        f"    cast send {CCIP[chain]['TOKEN_ADMIN_REGISTRY']} \\\n"
        f"        'setPool(address,address)' {token} {pool} \\\n"
        f"        --rpc-url $RPC_URL --account $ADMIN_ACCOUNT\n"
        f"Alternatively hand the role over to the deployer ({migration.account().address}), "
        f"with `transferAdminRole(address,address)` on the same contract, and this "
        f"migration will do it on the next run."
    )
    return False


def _is(address, other):
    return str(address).lower() == str(other).lower()
