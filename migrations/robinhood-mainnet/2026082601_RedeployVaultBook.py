"""Deploy the fresh VaultBook required by the clean PR #211 generation.

The PR #211 contracts were already deployed by migration 2026082600. The old
RipeGov still has funds and governance points, so its VaultBook correctly
refuses an in-place replacement. This migration leaves that state untouched:
it builds a fresh VaultBook, registers the staged vaults, and prints the
revised Safe activation batch.
"""

from scripts.utils import log
from scripts.utils.migration import Migration

from config.robinhood_launch import (
    REGISTRY_MAX_DELAY,
    REGISTRY_MIN_DELAY,
    ZERO_ADDRESS,
)


RIPE_HQ = "0xD4e82AE1De673bba3B53386A2D2C630AE6630940"
SWITCHBOARD = "0xA1872467AC4fb442aeA341163A65263915ce178a"
PRICE_DESK = "0x56Db9c2322e009189049bC57385751fc7922AAb0"
SIMPLE_ERC20 = "0x4F89C94636995eF20d40d5592bA2585348bE6D53"

PR211_SUFFIX = "Staged2026082600"
VAULT_BOOK_LABEL = "VaultBookStaged2026082601"

HQ_UPDATES = (
    ("Ledger", 4),
    ("MissionControl", 5),
    ("VaultBook", 8),
    ("AuctionHouse", 9),
    ("CreditEngine", 13),
    ("HumanResources", 15),
    ("Lootbox", 16),
    ("Teller", 17),
    ("Deleverage", 18),
    ("CreditRedeem", 19),
)

SWITCHBOARD_UPDATES = (
    ("SwitchboardAlpha", 1),
    ("SwitchboardBravo", 2),
    ("SwitchboardCharlie", 3),
    ("SwitchboardDelta", 4),
)


def staged(name):
    return f"{name}{PR211_SUFFIX}"


def migrate(migration: Migration):
    # ------------------------------------------------------------------
    # 1. Read the contracts already deployed by 2026082600.
    # ------------------------------------------------------------------
    log.h1("1. Reading the staged PR #211 generation")

    hq = migration.get_contract("RipeHq", RIPE_HQ)
    switchboard = migration.get_contract("Switchboard", SWITCHBOARD)
    price_desk = migration.get_contract("PriceDesk", PRICE_DESK)
    simple_erc20 = migration.get_contract("SimpleErc20", SIMPLE_ERC20)

    fresh = {
        name: migration.get_contract(staged(name))
        for name, _reg_id in HQ_UPDATES + SWITCHBOARD_UPDATES
        if name != "VaultBook"
    }
    fresh["ChainlinkPrices"] = migration.get_contract(
        staged("ChainlinkPrices")
    )
    stability_pool = migration.get_contract(staged("StabilityPool"))
    ripe_gov = migration.get_contract(staged("RipeGov"))

    # ------------------------------------------------------------------
    # 2. Build the fresh VaultBook tree before governance activation.
    # ------------------------------------------------------------------
    log.h1("2. Deploying and populating the fresh VaultBook")

    vault_book = migration.deploy(
        "VaultBook",
        hq,
        migration.account(),
        REGISTRY_MIN_DELAY,
        REGISTRY_MAX_DELAY,
        label=VAULT_BOOK_LABEL,
    )
    register(migration, vault_book, stability_pool, "StabilityPool", 1)
    register(migration, vault_book, ripe_gov, "RipeGov", 2)
    register(migration, vault_book, simple_erc20, "SimpleErc20", 3)
    relinquish_governance(migration, vault_book)

    fresh["VaultBook"] = vault_book
    assert as_address(vault_book.getAddr(1)) == as_address(stability_pool)
    assert as_address(vault_book.getAddr(2)) == as_address(ripe_gov)
    assert as_address(vault_book.getAddr(3)) == as_address(simple_erc20)

    # ------------------------------------------------------------------
    # 3. Print the complete replacement batch; the 2026082600 batch is stale.
    # ------------------------------------------------------------------
    log.h1("3. Revised Safe activation batch")
    print_safe_batch(hq, switchboard, price_desk, fresh)


def register(migration, registry, contract, description, expected_id):
    def registration_started():
        if int(registry.getRegId(contract)) == expected_id:
            return True
        pending = registry.pendingNewAddr(contract)
        return str(pending[0]) == description and int(pending[2]) != 0

    assert migration.execute_reconciled(
        registry.startAddNewAddressToRegistry,
        registration_started,
        contract,
        description,
    )
    assert migration.execute_reconciled(
        registry.confirmNewAddressToRegistry,
        lambda: int(registry.getRegId(contract)) == expected_id,
        contract,
    )
    assert int(registry.getRegId(contract)) == expected_id


def relinquish_governance(migration, contract):
    assert as_address(contract.governance()) in (
        as_address(migration.account()),
        ZERO_ADDRESS,
    )
    assert migration.execute_reconciled(
        contract.relinquishGov,
        lambda: as_address(contract.governance()) == ZERO_ADDRESS,
    )
    assert as_address(contract.governance()) == ZERO_ADDRESS


def print_safe_batch(hq, switchboard, price_desk, fresh):
    log.info(f'const hq = c.Ripe_RH_RipeHq.at("{hq.address}")')
    log.info(
        f'const switchboard = c.Ripe_RH_Switchboard.at("{switchboard.address}")'
    )
    log.info(
        f'const priceDesk = c.Ripe_RH_PriceDesk.at("{price_desk.address}")'
    )
    log.info("")

    log.info("// Start the ten RipeHq replacements")
    for name, reg_id in HQ_UPDATES:
        log.info(
            f"await hq.startAddressUpdateToRegistry("
            f'{reg_id}n, "{fresh[name].address}")  // {name}'
        )

    log.info("// Start the four Switchboard replacements")
    for name, reg_id in SWITCHBOARD_UPDATES:
        log.info(
            f"await switchboard.startAddressUpdateToRegistry("
            f'{reg_id}n, "{fresh[name].address}")  // {name}'
        )

    chainlink = fresh["ChainlinkPrices"]
    log.info("// Start the Chainlink price source replacement")
    log.info(
        "await priceDesk.startAddressUpdateToRegistry("
        f'1n, "{chainlink.address}")  // ChainlinkPrices'
    )
    log.info("")

    log.info("// Confirm every replacement in dependency order")
    for name, reg_id in HQ_UPDATES:
        log.info(
            f"await hq.confirmAddressUpdateToRegistry({reg_id}n)  // {name}"
        )
    for name, reg_id in SWITCHBOARD_UPDATES:
        log.info(
            "await switchboard.confirmAddressUpdateToRegistry("
            f"{reg_id}n)  // {name}"
        )
    log.info(
        "await priceDesk.confirmAddressUpdateToRegistry(1n)  // ChainlinkPrices"
    )
    log.info("")

    charlie = fresh["SwitchboardCharlie"]
    teller = fresh["Teller"]
    log.info("// Teller was deployed paused; reopen it after activation")
    log.info(
        f'const charlie = c.Ripe_RH_SwitchboardCharlie.at("{charlie.address}")'
    )
    log.info(f'await charlie.pause("{teller.address}", false)')
    log.info("")
    log.info("// Then run migration 2026082602 to verify and publish.")


def as_address(value):
    return str(getattr(value, "address", value)).lower()
