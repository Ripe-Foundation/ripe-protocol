"""
Helpers for talking to the Chainlink CCIP contracts that Ripe does not deploy itself
(the token admin registry and the registry module used to claim a token's admin role).
"""

import json

import boa
from eth_abi.abi import encode

from config.Ccip import CCIP
from scripts.utils import log

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

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
    return boa.loads_abi(json.dumps(ROUTER_ABI), name="Router").at(CCIP[chain]["ROUTER"])


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


def assert_lane_configuration(
    pool,
    remote_selector,
    remote_pool,
    remote_token,
    expected_rate_limit,
    expected_rate_limit_admin,
):
    """Revalidate every security-relevant field of an existing CCIP lane.

    `isSupportedChain()` alone is not evidence that the lane points at the
    intended peer. A selector can be present with the wrong token, an old or
    additional pool, or an unexpected rate policy. Migration replays call this
    after both the add and already-present paths so neither path silently skips
    verification.
    """
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

    outbound = _rate_limit_config(
        pool.getCurrentOutboundRateLimiterState(remote_selector)
    )
    inbound = _rate_limit_config(
        pool.getCurrentInboundRateLimiterState(remote_selector)
    )
    assert outbound == expected_rate_limit, (
        f"CCIP selector {remote_selector} outbound rate policy {outbound} does "
        f"not match expected {expected_rate_limit}"
    )
    assert inbound == expected_rate_limit, (
        f"CCIP selector {remote_selector} inbound rate policy {inbound} does "
        f"not match expected {expected_rate_limit}"
    )

    rate_limit_admin = str(pool.getRateLimitAdmin())
    assert rate_limit_admin.lower() == expected_rate_limit_admin.lower(), (
        f"CCIP rateLimitAdmin {rate_limit_admin} does not match expected "
        f"{expected_rate_limit_admin}"
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


def claim_admin_role(migration, token):
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
        migration.execute(module.registerAdminViaGetCCIPAdmin, token)
        administrator, pending, _pool = registry.getTokenConfig(token)

    if _is(pending, deployer):
        log.info("accepting the pending CCIP administrator role")
        migration.execute(registry.acceptAdminRole, token)
        administrator = deployer

    return administrator


def set_pool(migration, token, pool):
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

    administrator = claim_admin_role(migration, token)
    if _is(administrator, migration.account().address):
        migration.execute(registry.setPool, token, pool)
        return True

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
