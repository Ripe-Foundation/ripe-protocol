"""Redeploy the 15 contracts whose bytecode no longer matches source.

Deployment only. Governance moved to the Safe in 0007, so the deployer can no
longer touch a registry: every one of these has to be pointed at through
startAddressUpdateToRegistry + confirmAddressUpdateToRegistry, under timelock,
by the Safe. This migration deploys and then prints that calldata.

Each contract is recorded in the manifest under a "<Name>V2" label so the
existing entries keep describing what RipeHq, VaultBook and Switchboard
actually point at. Nothing here changes the live wiring.
"""

from scripts.utils import log
from scripts.utils.migration import Migration

from config.robinhood_launch import (
    HR_MAX_TIMELOCK,
    HR_MIN_TIMELOCK,
    LOOTBOX_DEPOSIT_REWARD,
    LOOTBOX_MIN_SEND_INTERVAL,
    LOOTBOX_SEND_INTERVAL,
    LOOTBOX_YIELD_BONUS,
    STALE_WINDOW_MAX,
    STALE_WINDOW_MIN,
    SWITCHBOARD_MAX_TIMELOCK,
    SWITCHBOARD_MIN_TIMELOCK,
    TELLER_SHOULD_PAUSE,
    ZERO_ADDRESS,
)

# (contract, registry, regId). The ids were read off chain and are the slots
# the Safe has to update -- they are NOT deployment order.
TARGETS = (
    ("MissionControl", "RipeHq", 5),
    ("AuctionHouse", "RipeHq", 9),
    ("BondRoom", "RipeHq", 12),
    ("CreditEngine", "RipeHq", 13),
    ("HumanResources", "RipeHq", 15),
    ("Lootbox", "RipeHq", 16),
    ("Teller", "RipeHq", 17),
    ("CreditRedeem", "RipeHq", 19),
    ("StabilityPool", "VaultBook", 1),
    ("RipeGov", "VaultBook", 2),
    ("SimpleErc20", "VaultBook", 3),
    ("SwitchboardAlpha", "Switchboard", 1),
    ("SwitchboardBravo", "Switchboard", 2),
    ("SwitchboardCharlie", "Switchboard", 3),
    ("SwitchboardEcho", "Switchboard", 5),
)


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

    # Unchanged since launch, so the replacement takes the address already on
    # chain rather than getting a fresh copy.
    bond_booster = migration.get_contract("BondBooster")

    log.h1("Deploying DefaultsFromMissionControl")

    # MissionControl copies its defaults into storage at construction. Built
    # against DefaultsRobinhood it would come up holding LAUNCH values and
    # forget everything governance changed since -- eight registered assets, a
    # 10x lower ripePerBlock, an extra stability-vault route, three lite
    # signers. This mirror reads all of it back off the live MissionControl
    # instead, so the copy is exact whenever this actually runs.
    defaults = migration.deploy(
        "DefaultsFromMissionControl",
        migration.get_address("MissionControl"),
        migration.get_address("Ledger"),
    )

    # Constructor arguments, identical to the originals in 0001/0002/0004/0005.
    # The 08-05 changes ("stability vault id classifier", "governance and
    # stability vault pointers") altered internals only -- every signature here
    # was re-checked against the compiled ABI and none of them moved.
    args = {
        "MissionControl": (hq, defaults),
        "AuctionHouse": (hq,),
        "BondRoom": (hq, bond_booster),
        "CreditEngine": (hq,),
        "HumanResources": (hq, HR_MIN_TIMELOCK, HR_MAX_TIMELOCK),
        "Lootbox": (
            hq,
            LOOTBOX_MIN_SEND_INTERVAL,
            LOOTBOX_SEND_INTERVAL,
            LOOTBOX_DEPOSIT_REWARD,
            LOOTBOX_YIELD_BONUS,
        ),
        "Teller": (hq, TELLER_SHOULD_PAUSE),
        "CreditRedeem": (hq,),
        "StabilityPool": (hq,),
        "RipeGov": (hq,),
        "SimpleErc20": (hq,),
        # Alpha alone takes the stale-window band before its timelocks.
        "SwitchboardAlpha": (
            hq,
            ZERO_ADDRESS,
            STALE_WINDOW_MIN,
            STALE_WINDOW_MAX,
            SWITCHBOARD_MIN_TIMELOCK,
            SWITCHBOARD_MAX_TIMELOCK,
        ),
        "SwitchboardBravo": (
            hq, ZERO_ADDRESS, SWITCHBOARD_MIN_TIMELOCK, SWITCHBOARD_MAX_TIMELOCK
        ),
        "SwitchboardCharlie": (
            hq, ZERO_ADDRESS, SWITCHBOARD_MIN_TIMELOCK, SWITCHBOARD_MAX_TIMELOCK
        ),
        "SwitchboardEcho": (
            hq, ZERO_ADDRESS, SWITCHBOARD_MIN_TIMELOCK, SWITCHBOARD_MAX_TIMELOCK
        ),
    }

    log.h1("Redeploying stale contracts")

    deployed = []
    for name, registry, reg_id in TARGETS:
        log.h2(f"Deploying {name}")
        contract = migration.deploy(name, *args[name], label=f"{name}V2")
        deployed.append((name, registry, reg_id, contract.address))

    log.h1("Registry updates for the Safe")

    # Grouped by registry because that is how they get batched, and ordered so
    # MissionControl and the switchboards -- which the rest read their config
    # through -- land before the departments that depend on them.
    registries = {
        "RipeHq": hq.address,
        "VaultBook": migration.get_address("VaultBook"),
        "Switchboard": migration.get_address("Switchboard"),
    }
    for reg_name, reg_addr in registries.items():
        rows = [d for d in deployed if d[1] == reg_name]
        if not rows:
            continue
        log.h2(f"{reg_name} @ {reg_addr}")
        for name, _, reg_id, addr in rows:
            start, confirm = _update_calldata(reg_id, addr)
            log.info(f"\t{name} -> id {reg_id} -> {addr}")
            log.info(f"\t  [1] 0x{start}")
            log.info(f"\t  [2] 0x{confirm}   (after timelock)")

    # Neither of these is reachable from a Defaults contract: both are
    # switchboard-only setters that the MissionControl constructor never
    # touches, so the replacement comes up holding zero for both no matter
    # what the mirror returns. They have to be set explicitly afterwards.
    log.h2("Still required after MissionControl is registered")
    log.info("\tSwitchboardCharlie.setCoreRipeGovVaultId(2)    # RipeGov")
    log.info("\tSwitchboardCharlie.setPreferredStabVaultId(1)  # StabilityPool")
