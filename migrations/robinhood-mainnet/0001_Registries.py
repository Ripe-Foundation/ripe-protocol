from scripts.utils import log
from scripts.utils.migration import Migration

from config.robinhood_launch import LEDGER_ACTION_BLOCK_SOURCE


def _node_read_word(migration, contract_address, signature):
    """Read one exact ABI word from the configured Robinhood node.

    Arbitrum marks its precompiles with a single 0xfe byte on chain. The node
    intercepts calls to them, but titanoboa mirrors chain state into a local
    EVM and executes that byte, which is INVALID. Production evidence must
    therefore come from the real RPC, never Boa's local EVM.
    """
    rpc = migration.rpc()
    assert rpc and rpc != "boa", "production Ledger requires a real RPC node"

    from web3 import Web3

    w3 = Web3(Web3.HTTPProvider(rpc))
    assert w3.is_connected(), "production Ledger RPC is unavailable"
    selector = Web3.keccak(text=signature)[:4]
    result = w3.eth.call(
        {
            "to": Web3.to_checksum_address(contract_address),
            "data": selector,
        }
    )
    assert len(result) == 32, f"malformed {signature} readback"
    return int.from_bytes(result, "big")


def _validate_ledger_profile(migration, ledger_address):
    expected_source = int(LEDGER_ACTION_BLOCK_SOURCE, 16)
    assert expected_source == 0x64, "production action-block source must be ArbSys"

    actual_source = _node_read_word(
        migration,
        ledger_address,
        "ACTION_BLOCK_SOURCE()",
    )
    assert actual_source == expected_source, "Ledger action-block source mismatch"

    action_block = _node_read_word(
        migration,
        ledger_address,
        "getArbActionBlock()",
    )
    assert action_block != 0, "ArbSys action block reads zero"
    return actual_source, action_block


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    defaults = migration.get_contract("DefaultsRobinhood")

    log.h1("Deploying Ledger")

    # The constructor stores and allowlists the source. The node-backed checks
    # below prove both the exact stored source and its live runtime behavior.
    ledger = migration.deploy(
        "Ledger",
        hq,
        defaults,
        LEDGER_ACTION_BLOCK_SOURCE,
    )
    action_source, action_block = _validate_ledger_profile(
        migration,
        ledger.address,
    )
    log.h2(f"Ledger ACTION_BLOCK_SOURCE: 0x{action_source:040x}")
    log.h2(f"ArbSys action block: {action_block}")

    migration.execute(hq.startAddNewAddressToRegistry, ledger, "Ledger")
    assert int(migration.execute(hq.confirmNewAddressToRegistry, ledger)) == 4

    log.h1("Deploying MissionControl")

    mission_control = migration.deploy(
        "MissionControl",
        hq,
        defaults,
    )
    migration.execute(
        hq.startAddNewAddressToRegistry, mission_control, "MissionControl"
    )
    assert int(
        migration.execute(hq.confirmNewAddressToRegistry, mission_control)
    ) == 5
