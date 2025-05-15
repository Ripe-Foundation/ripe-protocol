import pytest
import boa

from config.BluePrint import PARAMS, ADDYS


###########
# Ripe HQ #
###########


@pytest.fixture(scope="session")
def ripe_hq_deploy(governor, fork):
    return boa.load(
        "contracts/registries/AddyRegistry.vy",
        governor,
        PARAMS[fork]["RIPE_HQ_MIN_GOV_CHANGE_DELAY"],
        PARAMS[fork]["RIPE_HQ_MAX_GOV_CHANGE_DELAY"],
        PARAMS[fork]["RIPE_HQ_MIN_CHANGE_DELAY"],
        PARAMS[fork]["RIPE_HQ_MAX_CHANGE_DELAY"],
        name="ripe_hq",
    )


@pytest.fixture(scope="session", autouse=True)
def ripe_hq(ripe_hq_deploy, price_desk, auction_house, vault_book, control_room, credit_engine, ledger, lootbox, teller, governor):
    delay = ripe_hq_deploy.addyChangeDelay()

    # 1
    assert ripe_hq_deploy.registerNewAddy(price_desk, "Price Desk", sender=governor)
    boa.env.time_travel(blocks=delay + 1)
    assert ripe_hq_deploy.confirmNewAddy(price_desk, sender=governor) == 1

    # 2
    assert ripe_hq_deploy.registerNewAddy(vault_book, "Vault Book", sender=governor)
    boa.env.time_travel(blocks=delay + 1)
    assert ripe_hq_deploy.confirmNewAddy(vault_book, sender=governor) == 2

    # 3
    assert ripe_hq_deploy.registerNewAddy(auction_house, "Auction House", sender=governor)
    boa.env.time_travel(blocks=delay + 1)
    assert ripe_hq_deploy.confirmNewAddy(auction_house, sender=governor) == 3

    # 4
    assert ripe_hq_deploy.registerNewAddy(control_room, "Control Room", sender=governor)
    boa.env.time_travel(blocks=delay + 1)
    assert ripe_hq_deploy.confirmNewAddy(control_room, sender=governor) == 4

    # 5
    assert ripe_hq_deploy.registerNewAddy(credit_engine, "Credit Engine", sender=governor)
    boa.env.time_travel(blocks=delay + 1)
    assert ripe_hq_deploy.confirmNewAddy(credit_engine, sender=governor) == 5

    # 6
    assert ripe_hq_deploy.registerNewAddy(ledger, "Ledger", sender=governor)
    boa.env.time_travel(blocks=delay + 1)
    assert ripe_hq_deploy.confirmNewAddy(ledger, sender=governor) == 6

    # 7
    assert ripe_hq_deploy.registerNewAddy(lootbox, "Lootbox", sender=governor)
    boa.env.time_travel(blocks=delay + 1)
    assert ripe_hq_deploy.confirmNewAddy(lootbox, sender=governor) == 7

    # 8
    assert ripe_hq_deploy.registerNewAddy(teller, "Teller", sender=governor)
    boa.env.time_travel(blocks=delay + 1)
    assert ripe_hq_deploy.confirmNewAddy(teller, sender=governor) == 8

    return ripe_hq_deploy


###############
# Departments #
###############


# price desk


@pytest.fixture(scope="session")
def price_desk(ripe_hq_deploy, fork):
    ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE" if fork == "local" else ADDYS[fork]["ETH"]
    return boa.load(
        "contracts/registries/PriceDesk.vy",
        ripe_hq_deploy,
        ETH,
        PARAMS[fork]["PRICE_DESK_MIN_STALE_TIME"],
        PARAMS[fork]["PRICE_DESK_MAX_STALE_TIME"],
        PARAMS[fork]["PRICE_DESK_MIN_CHANGE_DELAY"],
        PARAMS[fork]["PRICE_DESK_MAX_CHANGE_DELAY"],
        name="price_desk",
    )


# vault book


@pytest.fixture(scope="session")
def vault_book(ripe_hq_deploy, fork):
    return boa.load(
        "contracts/registries/VaultBook.vy",
        ripe_hq_deploy,
        PARAMS[fork]["VAULT_BOOK_MIN_CHANGE_DELAY"],
        PARAMS[fork]["VAULT_BOOK_MAX_CHANGE_DELAY"],
        name="vault_book",
    )


# auction house


@pytest.fixture(scope="session")
def auction_house(ripe_hq_deploy):
    return boa.load(
        "contracts/core/AuctionHouse.vy",
        ripe_hq_deploy,
        name="auction_house",
    )


# control room


@pytest.fixture(scope="session")
def control_room(ripe_hq_deploy):
    return boa.load(
        "contracts/core/ControlRoom.vy",
        ripe_hq_deploy,
        name="control_room",
    )


# credit engine


@pytest.fixture(scope="session")
def credit_engine(ripe_hq_deploy):
    return boa.load(
        "contracts/core/CreditEngine.vy",
        ripe_hq_deploy,
        name="credit_engine",
    )


# ledger


@pytest.fixture(scope="session")
def ledger(ripe_hq_deploy):
    return boa.load(
        "contracts/core/Ledger.vy",
        ripe_hq_deploy,
        name="ledger",
    )


# lootbox


@pytest.fixture(scope="session")
def lootbox(ripe_hq_deploy):
    return boa.load(
        "contracts/core/Lootbox.vy",
        ripe_hq_deploy,
        name="lootbox",
    )


# teller


@pytest.fixture(scope="session")
def teller(ripe_hq_deploy):
    return boa.load(
        "contracts/core/Teller.vy",
        ripe_hq_deploy,
        name="teller",
    )


##########
# Vaults #
##########


# simple erc20 vault


@pytest.fixture(scope="session")
def simple_erc20_vault(ripe_hq, vault_book, governor):
    vault = boa.load(
        "contracts/vaults/SimpleErc20.vy",
        ripe_hq,
        name="simple_erc20_vault",
    )

    # register with vault book
    assert vault_book.registerNewVault(vault.address, "Simple ERC20 Vault", sender=governor)
    boa.env.time_travel(blocks=vault_book.vaultChangeDelay() + 1)
    assert vault_book.confirmNewVaultRegistration(vault.address, sender=governor) != 0

    return vault


# rebase erc20 vault


@pytest.fixture(scope="session")
def rebase_erc20_vault(ripe_hq, vault_book, governor):
    vault = boa.load(
        "contracts/vaults/RebaseErc20.vy",
        ripe_hq,
        name="rebase_erc20_vault",
    )

    # register with vault book
    assert vault_book.registerNewVault(vault.address, "Rebase ERC20 Vault", sender=governor)
    boa.env.time_travel(blocks=vault_book.vaultChangeDelay() + 1)
    assert vault_book.confirmNewVaultRegistration(vault.address, sender=governor) != 0

    return vault


# stability pool vault


@pytest.fixture(scope="session")
def stability_pool(ripe_hq, vault_book, governor):
    vault = boa.load(
        "contracts/vaults/StabilityPool.vy",
        ripe_hq,
        name="stability_pool",
    )

    # register with vault book
    assert vault_book.registerNewVault(vault.address, "Stability Pool", sender=governor)
    boa.env.time_travel(blocks=vault_book.vaultChangeDelay() + 1)
    assert vault_book.confirmNewVaultRegistration(vault.address, sender=governor) != 0

    return vault