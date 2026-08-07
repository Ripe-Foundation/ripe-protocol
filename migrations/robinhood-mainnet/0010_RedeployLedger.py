"""Redeploy Ledger, Teller, Lootbox and RipeGov.

Two things land together here.

FIRST -- deposits are currently reverting. 0009 replaced StabilityPool, RipeGov
and SimpleErc20 at their existing VaultBook ids. Ledger was deliberately left
alone -- it holds accounting nothing can rebuild -- but it also holds per-user
vault participation, and that kept pointing at ids whose vaults are now empty.

CreditEngine._getUserBorrowTerms runs on every deposit through housekeeping:

    numUserAssets = staticcall Vault(vaultAddr).numUserAssets(_user)
    for y: uint256 in range(1, numUserAssets, bound=max_value(uint256)):

Vyper reverts when stop < start, so a user Ledger says is in vault 2 whose
replacement reports zero assets makes range(1, 0) revert -- and every deposit
and withdrawal with it. The outer loop over vaults is guarded for zero
(CreditEngine.vy:699); this inner one is not, which is worth fixing separately.

A fresh Ledger clears participation, so it is rebuilt only as users deposit
into vaults that actually exist. Acceptable because the protocol is empty --
all three old vaults hold $0.00 -- and NOT a general answer. The right pattern
is to add a new vault id and migrate into it rather than replace a vault in
place, which keeps participation and balances consistent throughout.

SECOND -- Ledger, Teller, Lootbox and RipeGov all drifted again after 0009.
`removeVaultFromUserForMigration` was re-added to Ledger and RipeGov migration
cleanup routed back through it, and RipeGov lock-deposit and lock mutation were
restricted to Teller. The new Teller calls a Ledger function the deployed
Ledger does not have, so these four have to move together regardless.

ORDER MATTERS. RipeGov is replaced again here, which re-creates the same empty
vault at a live id. That is only safe because Ledger is wiped in the same
batch. If the Safe applies these separately, apply Ledger FIRST or together --
a new RipeGov against the old Ledger reproduces the revert this fixes.

Ledger keeps its ripeAvailFor*: DefaultsRobinhoodLive sources those from the
live Ledger, so the RIPE already emitted stays accounted for. It drops accrued
deposit and borrow points, unclaimed ripeRewards, and lastTouch.
"""

from scripts.utils import log
from scripts.utils.migration import Migration

from config.robinhood_launch import (
    LEDGER_ACTION_BLOCK_SOURCE,
    LOOTBOX_DEPOSIT_REWARD,
    LOOTBOX_MIN_SEND_INTERVAL,
    LOOTBOX_SEND_INTERVAL,
    LOOTBOX_YIELD_BONUS,
    TELLER_SHOULD_PAUSE,
)

RIPE_HQ = "RipeHq"
VAULT_BOOK = "VaultBook"


def _arb_action_block(migration, ledger_address):
    """Read getArbActionBlock() from the NODE, not from boa's local EVM.

    ArbSys is a node-implemented precompile: on chain it is a single 0xfe byte,
    so boa executes INVALID and any local read reverts even when the contract
    is correct. The constructor no longer probes it either -- that check was
    removed upstream -- so this is the only thing standing between a wrong
    action-block source and a Ledger whose one-action-per-block guard is broken.
    """
    from web3 import Web3

    rpc = migration.rpc()
    if not rpc or rpc == "boa":
        return None  # local run: nothing real to ask
    w3 = Web3(Web3.HTTPProvider(rpc))
    address = Web3.to_checksum_address(ledger_address)

    # On a fork the contract exists only in the local EVM, so the node has no
    # code at this address and would answer an empty word -- which reads as
    # zero and would fail the assertion below for the wrong reason.
    if len(w3.eth.get_code(address)) == 0:
        log.info("\tnot deployed on the node (fork run), skipping ArbSys readback")
        return None

    selector = Web3.keccak(text="getArbActionBlock()")[:4]
    result = w3.eth.call({"to": address, "data": selector})
    return int.from_bytes(result, "big")


def _update_calldata(reg_id, new_addr):
    """The two calls the Safe makes for one registry slot."""
    from eth_abi.abi import encode
    from web3 import Web3

    start = Web3.keccak(text="startAddressUpdateToRegistry(uint256,address)")[:4]
    start += encode(["uint256", "address"], [reg_id, new_addr])
    confirm = Web3.keccak(text="confirmAddressUpdateToRegistry(uint256)")[:4]
    confirm += encode(["uint256"], [reg_id])
    return start.hex(), confirm.hex()


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")

    # Already on chain from 0009, and its ripeAvailFor* still match the live
    # Ledger exactly, so the replacement inherits them unchanged.
    defaults = migration.get_address("DefaultsRobinhoodLive")

    updates = []

    def redeploy(name, registry, reg_id, *args):
        log.h2(f"Deploying {name}")
        contract = migration.deploy(name, *args)
        updates.append((name, registry, reg_id, contract.address))
        return contract

    log.h1("Redeploying")

    ledger = redeploy("Ledger", RIPE_HQ, 4, hq, defaults, LEDGER_ACTION_BLOCK_SOURCE)

    # Asked of the node, because boa cannot execute ArbSys. None on a fork.
    arb_block = _arb_action_block(migration, ledger.address)
    if arb_block is not None:
        assert arb_block != 0, "ArbSys action block reads zero"
        log.h2(f"ArbSys action block: {arb_block}")

    redeploy(
        "Lootbox", RIPE_HQ, 16, hq,
        LOOTBOX_MIN_SEND_INTERVAL,
        LOOTBOX_SEND_INTERVAL,
        LOOTBOX_DEPOSIT_REWARD,
        LOOTBOX_YIELD_BONUS,
    )
    redeploy("Teller", RIPE_HQ, 17, hq, TELLER_SHOULD_PAUSE)
    redeploy("RipeGov", VAULT_BOOK, 2, hq)

    log.h1("Registry updates for the Safe")

    for registry in (RIPE_HQ, VAULT_BOOK):
        rows = [u for u in updates if u[1] == registry]
        if not rows:
            continue
        log.h2(f"{registry} @ {migration.get_address(registry)}")
        for name, _, reg_id, addr in rows:
            start, confirm = _update_calldata(reg_id, addr)
            log.info(f"\t{name} -> id {reg_id} -> {addr}")
            log.info(f"\t  [1] 0x{start}")
            log.info(f"\t  [2] 0x{confirm}   (after timelock)")

    log.h2("Order and follow-ups")
    log.info("\tApply Ledger (id 4) FIRST or together with RipeGov (VaultBook")
    log.info("\tid 2). A new RipeGov against the old Ledger reproduces the")
    log.info("\trange(1, 0) revert that breaks deposits.")
    if TELLER_SHOULD_PAUSE:
        log.info("")
        log.info("\tTeller is deployed PAUSED (TELLER_SHOULD_PAUSE). It has to be")
        log.info("\tunpaused after the swap or deposits stay blocked.")
