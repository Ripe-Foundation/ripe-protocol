"""Static plan to prepare VaultMigrator as RipeHq registry id 25.

RipeHq ids 23 and 24 belong to the two CCIP pools. AddressRegistry assigns the
current ``numAddrs`` value to the next confirmed append, so this plan aborts
unless those rows already exist and the next id is exactly 25. It deploys an
unpaused Robinhood candidate with no Base legacy-vault binding, then emits the
exact Safe calldata for the timelocked append. ``0014`` performs registry
readback before creating the first canonical manifest record.

The H-06 Robinhood runner intentionally rejects this legacy deploy/send API.
This plan requires a typed ``MIGRATION_STAGE`` conversion before execution.
"""

from scripts.utils import log
from scripts.utils.migration import Migration

from config.robinhood_launch import (
    VAULT_MIGRATOR_SHOULD_PAUSE,
    ZERO_ADDRESS,
)


VAULT_MIGRATOR_ID = 25
VAULT_MIGRATOR_CANDIDATE = "VaultMigratorCandidate0013"
PRIOR_CCIP_POOL_IDS = (23, 24)


def _add_calldata(new_addr, description):
    """The two Safe calls that append one RipeHq registry slot."""
    from eth_abi.abi import encode
    from web3 import Web3

    start = Web3.keccak(
        text="startAddNewAddressToRegistry(address,string)"
    )[:4]
    start += encode(["address", "string"], [new_addr, description])
    confirm = Web3.keccak(
        text="confirmNewAddressToRegistry(address)"
    )[:4]
    confirm += encode(["address"], [new_addr])
    return start.hex(), confirm.hex()


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")

    # numAddrs is the next id, not a populated-row count. Require both prior
    # CCIP rows to remain active without reserving, replacing or otherwise
    # touching their ids. The typed conversion additionally binds their exact
    # approved addresses and runtime identities.
    assert int(hq.numAddrs()) == VAULT_MIGRATOR_ID, (
        "RipeHq next id is not VaultMigrator slot 25"
    )
    for reg_id in PRIOR_CCIP_POOL_IDS:
        assert hq.getAddr(reg_id) != ZERO_ADDRESS, (
            f"RipeHq CCIP pool slot {reg_id} is not active"
        )
    assert hq.getAddr(VAULT_MIGRATOR_ID) == ZERO_ADDRESS, (
        "RipeHq slot 25 is already occupied"
    )

    log.h1("Deploying VaultMigrator candidate")
    vault_migrator = migration.deploy(
        "VaultMigrator",
        hq,
        VAULT_MIGRATOR_SHOULD_PAUSE,
        ZERO_ADDRESS,
        label=VAULT_MIGRATOR_CANDIDATE,
    )
    assert bool(vault_migrator.isPaused()) is VAULT_MIGRATOR_SHOULD_PAUSE

    start, confirm = _add_calldata(
        vault_migrator.address,
        "VaultMigrator",
    )
    log.h1("RipeHq slot 25 Safe actions")
    log.info(f"\tRipeHq:    {hq.address}")
    log.info(
        f"\tcandidate: {vault_migrator.address} "
        f"[{VAULT_MIGRATOR_CANDIDATE}]"
    )
    log.info(f"\t[1] 0x{start}")
    log.info(f"\t[2] 0x{confirm}   (after timelock)")
    log.info("\tKeep an exclusive RipeHq-add window until confirmation.")
    log.info("\tThe typed executor must require confirm() to return id 25.")
    log.info("\tAfter confirmation, read getAddr(25) before promotion.")
