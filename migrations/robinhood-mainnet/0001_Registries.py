from scripts.utils import log
from scripts.utils.migration import Migration

from config.robinhood_launch import LEDGER_ACTION_BLOCK_SOURCE


def _arb_action_block(migration, ledger_address):
    """Read getArbActionBlock() from the NODE, not from boa's local EVM.

    Arbitrum marks its precompiles with a single 0xfe byte on chain. The node
    intercepts calls to them, but titanoboa mirrors chain state into a local
    EVM and executes that byte, which is INVALID -- so ANY boa-side read that
    touches ArbSys reverts even when the contract is perfectly correct. The
    deployment itself works because the node executes the constructor.
    """
    from web3 import Web3

    rpc = migration.rpc()
    if not rpc or rpc == "boa":
        return None  # local/boa run: nothing real to ask
    w3 = Web3(Web3.HTTPProvider(rpc))
    selector = Web3.keccak(text="getArbActionBlock()")[:4]
    result = w3.eth.call({"to": Web3.to_checksum_address(ledger_address),
                          "data": selector})
    return int.from_bytes(result, "big")


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    defaults = migration.get_contract("DefaultsRobinhood")

    log.h1("Deploying Ledger")

    # LEDGER_ACTION_BLOCK_SOURCE is ArbSys: on this L2 `block.number` is the L1
    # ancestor estimate and repeats across child blocks. The constructor calls
    # arbBlockNumber() and reverts if it cannot decode the result, so a wrong
    # value fails here rather than silently weakening the one-action-per-block
    # guard.
    ledger = migration.deploy(
        "Ledger",
        hq,
        defaults,
        LEDGER_ACTION_BLOCK_SOURCE,
    )
    # Asked of the node, because boa cannot execute ArbSys. None on a local run.
    arb_block = _arb_action_block(migration, ledger.address)
    if arb_block is not None:
        assert arb_block != 0, "ArbSys action block reads zero"
        log.h2(f"ArbSys action block: {arb_block}")

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
