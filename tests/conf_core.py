import pytest
import boa

from config.BluePrint import PARAMS, ADDYS
from constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS


###########
# Ripe HQ #
###########


@pytest.fixture(scope="session")
def ripe_hq_deploy(deploy3r, fork, green_token, savings_green, ripe_token):
    return boa.load(
        "contracts/registries/RipeHq.vy",
        green_token,
        savings_green,
        ripe_token,
        deploy3r,
        PARAMS[fork]["RIPE_HQ_MIN_GOV_TIMELOCK"],
        PARAMS[fork]["RIPE_HQ_MAX_GOV_TIMELOCK"],
        PARAMS[fork]["RIPE_HQ_MIN_REG_TIMELOCK"],
        PARAMS[fork]["RIPE_HQ_MAX_REG_TIMELOCK"],
        name="ripe_hq",
    )


@pytest.fixture(scope="session", autouse=True)
def ripe_hq(
    ripe_hq_deploy,
    green_token,
    savings_green,
    ripe_token,
    price_desk,
    vault_book,
    auction_house,
    auction_house_nft,
    bond_room,
    mission_control,
    switchboard,
    mainframe,
    credit_engine,
    endaoment,
    ledger,
    lootbox,
    teller,
    deploy3r,
    governance
):
    # finish token setup
    assert green_token.finishTokenSetup(ripe_hq_deploy, sender=deploy3r)
    assert savings_green.finishTokenSetup(ripe_hq_deploy, sender=deploy3r)
    assert ripe_token.finishTokenSetup(ripe_hq_deploy, sender=deploy3r)

    # config

    # 4
    assert ripe_hq_deploy.startAddNewAddressToRegistry(mission_control, "Mission Control", sender=deploy3r)
    assert ripe_hq_deploy.confirmNewAddressToRegistry(mission_control, sender=deploy3r) == 4

    # 5
    assert ripe_hq_deploy.startAddNewAddressToRegistry(switchboard, "Switchboard", sender=deploy3r)
    assert ripe_hq_deploy.confirmNewAddressToRegistry(switchboard, sender=deploy3r) == 5

    # 6
    assert ripe_hq_deploy.startAddNewAddressToRegistry(mainframe, "Mainframe", sender=deploy3r)
    assert ripe_hq_deploy.confirmNewAddressToRegistry(mainframe, sender=deploy3r) == 6

    # registries

    # 7
    assert ripe_hq_deploy.startAddNewAddressToRegistry(price_desk, "Price Desk", sender=deploy3r)
    assert ripe_hq_deploy.confirmNewAddressToRegistry(price_desk, sender=deploy3r) == 7

    # 8
    assert ripe_hq_deploy.startAddNewAddressToRegistry(vault_book, "Vault Book", sender=deploy3r)
    assert ripe_hq_deploy.confirmNewAddressToRegistry(vault_book, sender=deploy3r) == 8

    # departments

    # 9
    assert ripe_hq_deploy.startAddNewAddressToRegistry(auction_house, "Auction House", sender=deploy3r)
    assert ripe_hq_deploy.confirmNewAddressToRegistry(auction_house, sender=deploy3r) == 9

    # 10
    assert ripe_hq_deploy.startAddNewAddressToRegistry(auction_house_nft, "Auction House NFT", sender=deploy3r)
    assert ripe_hq_deploy.confirmNewAddressToRegistry(auction_house_nft, sender=deploy3r) == 10

    # 11
    assert ripe_hq_deploy.startAddNewAddressToRegistry(bond_room, "Bond Room", sender=deploy3r)
    assert ripe_hq_deploy.confirmNewAddressToRegistry(bond_room, sender=deploy3r) == 11


    # 12
    assert ripe_hq_deploy.startAddNewAddressToRegistry(credit_engine, "Credit Engine", sender=deploy3r)
    assert ripe_hq_deploy.confirmNewAddressToRegistry(credit_engine, sender=deploy3r) == 12

    # 13
    assert ripe_hq_deploy.startAddNewAddressToRegistry(endaoment, "Endaoment", sender=deploy3r)
    assert ripe_hq_deploy.confirmNewAddressToRegistry(endaoment, sender=deploy3r) == 13

    # 14
    assert ripe_hq_deploy.startAddNewAddressToRegistry(ledger, "Ledger", sender=deploy3r)
    assert ripe_hq_deploy.confirmNewAddressToRegistry(ledger, sender=deploy3r) == 14

    # 15
    assert ripe_hq_deploy.startAddNewAddressToRegistry(lootbox, "Lootbox", sender=deploy3r)
    assert ripe_hq_deploy.confirmNewAddressToRegistry(lootbox, sender=deploy3r) == 15

    # 16
    assert ripe_hq_deploy.startAddNewAddressToRegistry(teller, "Teller", sender=deploy3r)
    assert ripe_hq_deploy.confirmNewAddressToRegistry(teller, sender=deploy3r) == 16

    # set minting / blacklist capabilities

    # auction house can mint green
    ripe_hq_deploy.initiateHqConfigChange(9, True, False, False, False, sender=deploy3r)
    assert ripe_hq_deploy.confirmHqConfigChange(9, sender=deploy3r)

    # credit engine can mint green
    ripe_hq_deploy.initiateHqConfigChange(12, True, False, False, False, sender=deploy3r)
    assert ripe_hq_deploy.confirmHqConfigChange(12, sender=deploy3r)

    # lootbox can mint ripe
    ripe_hq_deploy.initiateHqConfigChange(15, False, True, False, False, sender=deploy3r)
    assert ripe_hq_deploy.confirmHqConfigChange(15, sender=deploy3r)

    # switchboard can set token blacklists and modify mission control
    ripe_hq_deploy.initiateHqConfigChange(5, False, False, True, True, sender=deploy3r)
    assert ripe_hq_deploy.confirmHqConfigChange(5, sender=deploy3r)

    # mainframe can modify mission control
    ripe_hq_deploy.initiateHqConfigChange(6, False, False, True, True, sender=deploy3r)
    assert ripe_hq_deploy.confirmHqConfigChange(6, sender=deploy3r)

    # finish ripe hq setup
    assert ripe_hq_deploy.setRegistryTimeLockAfterSetup(sender=deploy3r)
    assert ripe_hq_deploy.finishRipeHqSetup(governance, sender=deploy3r)

    return ripe_hq_deploy


##########
# Tokens #
##########


@pytest.fixture(scope="session")
def green_token(deploy3r, fork, whale):
    return boa.load(
        "contracts/tokens/GreenToken.vy",
        ZERO_ADDRESS,
        deploy3r,
        PARAMS[fork]["MIN_HQ_CHANGE_TIMELOCK"],
        PARAMS[fork]["MAX_HQ_CHANGE_TIMELOCK"],
        1_000_000 * EIGHTEEN_DECIMALS,
        whale,
        name="green_token",
    )


@pytest.fixture(scope="session")
def ripe_token(deploy3r, fork, whale):
    return boa.load(
        "contracts/tokens/RipeToken.vy",
        ZERO_ADDRESS,
        deploy3r,
        PARAMS[fork]["MIN_HQ_CHANGE_TIMELOCK"],
        PARAMS[fork]["MAX_HQ_CHANGE_TIMELOCK"],
        1_000_000 * EIGHTEEN_DECIMALS,
        whale,
        name="ripe_token",
    )


@pytest.fixture(scope="session")
def savings_green(fork, green_token, deploy3r):
    return boa.load(
        "contracts/tokens/SavingsGreen.vy",
        green_token,
        ZERO_ADDRESS,
        deploy3r,
        PARAMS[fork]["MIN_HQ_CHANGE_TIMELOCK"],
        PARAMS[fork]["MAX_HQ_CHANGE_TIMELOCK"],
        0,
        ZERO_ADDRESS,
        name="savings_green",
    )


##########
# Config #
##########


# mission control


@pytest.fixture(scope="session")
def mission_control(ripe_hq_deploy):
    return boa.load(
        "contracts/config/MissionControl.vy",
        ripe_hq_deploy,
        name="mission_control",
    )


# switchboard


@pytest.fixture(scope="session")
def switchboard(ripe_hq_deploy, fork):
    return boa.load(
        "contracts/config/Switchboard.vy",
        ripe_hq_deploy,
        PARAMS[fork]["PRICE_DESK_MIN_STALE_TIME"],
        PARAMS[fork]["PRICE_DESK_MAX_STALE_TIME"],
        PARAMS[fork]["MIN_HQ_CHANGE_TIMELOCK"],
        PARAMS[fork]["MAX_HQ_CHANGE_TIMELOCK"],
        name="switchboard",
    )


# mainframe


@pytest.fixture(scope="session")
def mainframe(ripe_hq_deploy, fork):
    return boa.load(
        "contracts/config/Mainframe.vy",
        ripe_hq_deploy,
        PARAMS[fork]["MIN_HQ_CHANGE_TIMELOCK"],
        PARAMS[fork]["MAX_HQ_CHANGE_TIMELOCK"],
        name="mainframe",
    )


###############
# Departments #
###############


# auction house


@pytest.fixture(scope="session")
def auction_house(ripe_hq_deploy):
    return boa.load(
        "contracts/core/AuctionHouse.vy",
        ripe_hq_deploy,
        name="auction_house",
    )


# auction house nft


@pytest.fixture(scope="session")
def auction_house_nft(ripe_hq_deploy):
    return boa.load(
        "contracts/core/AuctionHouseNFT.vy",
        ripe_hq_deploy,
        name="auction_house_nft",
    )


# bond room


@pytest.fixture(scope="session")
def bond_room(ripe_hq_deploy):
    return boa.load(
        "contracts/core/BondRoom.vy",
        ripe_hq_deploy,
        name="bond_room",
    )


# credit engine


@pytest.fixture(scope="session")
def credit_engine(ripe_hq_deploy):
    return boa.load(
        "contracts/core/CreditEngine.vy",
        ripe_hq_deploy,
        name="credit_engine",
    )


# endaoment


@pytest.fixture(scope="session")
def endaoment(ripe_hq_deploy):
    return boa.load(
        "contracts/core/Endaoment.vy",
        ripe_hq_deploy,
        name="endaoment",
    )


# ledger


@pytest.fixture(scope="session")
def ledger(ripe_hq_deploy):
    return boa.load(
        "contracts/core/Ledger.vy",
        ripe_hq_deploy,
        100 * (1_000_000 * EIGHTEEN_DECIMALS), # 100 million
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


# vault book


@pytest.fixture(scope="session")
def vault_book_deploy(ripe_hq_deploy, fork):
    return boa.load(
        "contracts/registries/VaultBook.vy",
        ripe_hq_deploy,
        PARAMS[fork]["VAULT_BOOK_MIN_REG_TIMELOCK"],
        PARAMS[fork]["VAULT_BOOK_MAX_REG_TIMELOCK"],
        name="vault_book",
    )


@pytest.fixture(scope="session")
def vault_book(vault_book_deploy, deploy3r, stability_pool, simple_erc20_vault, rebase_erc20_vault):

    # register stability pool
    assert vault_book_deploy.startAddNewAddressToRegistry(stability_pool, "Stability Pool", sender=deploy3r)
    assert vault_book_deploy.confirmNewAddressToRegistry(stability_pool, sender=deploy3r) == 1

    # register simple erc20 vault
    assert vault_book_deploy.startAddNewAddressToRegistry(simple_erc20_vault, "Simple ERC20 Vault", sender=deploy3r)
    assert vault_book_deploy.confirmNewAddressToRegistry(simple_erc20_vault, sender=deploy3r) == 2

    # register rebase erc20 vault
    assert vault_book_deploy.startAddNewAddressToRegistry(rebase_erc20_vault, "Rebase ERC20 Vault", sender=deploy3r)
    assert vault_book_deploy.confirmNewAddressToRegistry(rebase_erc20_vault, sender=deploy3r) == 3

    # finish registry setup
    assert vault_book_deploy.setRegistryTimeLockAfterSetup(sender=deploy3r)

    return vault_book_deploy


# simple erc20 vault


@pytest.fixture(scope="session")
def simple_erc20_vault(ripe_hq_deploy):
    return boa.load(
        "contracts/vaults/SimpleErc20.vy",
        ripe_hq_deploy,
        name="simple_erc20_vault",
    )


# rebase erc20 vault


@pytest.fixture(scope="session")
def rebase_erc20_vault(ripe_hq_deploy):
    return boa.load(
        "contracts/vaults/RebaseErc20.vy",
        ripe_hq_deploy,
        name="rebase_erc20_vault",
    )


# stability pool vault


@pytest.fixture(scope="session")
def stability_pool(ripe_hq_deploy):
    return boa.load(
        "contracts/vaults/StabilityPool.vy",
        ripe_hq_deploy,
        name="stability_pool",
    )


#################
# Price Sources #
#################


# price desk


@pytest.fixture(scope="session")
def price_desk_deploy(ripe_hq_deploy, fork):
    ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE" if fork == "local" else ADDYS[fork]["ETH"]
    return boa.load(
        "contracts/registries/PriceDesk.vy",
        ripe_hq_deploy,
        ETH,
        PARAMS[fork]["PRICE_DESK_MIN_REG_TIMELOCK"],
        PARAMS[fork]["PRICE_DESK_MAX_REG_TIMELOCK"],
        name="price_desk",
    )


@pytest.fixture(scope="session")
def price_desk(price_desk_deploy, deploy3r, chainlink, mock_price_source):

    # register chainlink
    assert price_desk_deploy.startAddNewAddressToRegistry(chainlink, "Chainlink", sender=deploy3r)
    assert price_desk_deploy.confirmNewAddressToRegistry(chainlink, sender=deploy3r) == 1

    # register mock price source
    assert price_desk_deploy.startAddNewAddressToRegistry(mock_price_source, "Mock Price Source", sender=deploy3r)
    assert price_desk_deploy.confirmNewAddressToRegistry(mock_price_source, sender=deploy3r) == 2

    # finish registry setup
    assert price_desk_deploy.setRegistryTimeLockAfterSetup(sender=deploy3r)

    return price_desk_deploy


# chainlink


@pytest.fixture(scope="session")
def chainlink(ripe_hq_deploy, fork, sally, bob, deploy3r, mock_chainlink_feed_one, mock_chainlink_feed_two):
    CHAINLINK_ETH_USD = ZERO_ADDRESS if fork == "local" else ADDYS[fork]["CHAINLINK_ETH_USD"]
    CHAINLINK_BTC_USD = ZERO_ADDRESS if fork == "local" else ADDYS[fork]["CHAINLINK_BTC_USD"]

    c = boa.load(
        "contracts/priceSources/Chainlink.vy",
        ripe_hq_deploy,
        PARAMS[fork]["PRICE_DESK_MIN_REG_TIMELOCK"],
        PARAMS[fork]["PRICE_DESK_MAX_REG_TIMELOCK"],
        ADDYS[fork]["WETH"],
        ADDYS[fork]["ETH"],
        ADDYS[fork]["BTC"],
        CHAINLINK_ETH_USD,
        CHAINLINK_BTC_USD,
        name="chainlink",
    )

    # testing setup with mock feeds (using sally/bob as fake assets here)
    assert c.addNewPriceFeed(sally, mock_chainlink_feed_one, sender=deploy3r)
    assert c.confirmNewPriceFeed(sally, sender=deploy3r)

    assert c.addNewPriceFeed(bob, mock_chainlink_feed_two, sender=deploy3r)
    assert c.confirmNewPriceFeed(bob, sender=deploy3r)

    # finish setup
    assert c.setActionTimeLockAfterSetup(sender=deploy3r)

    return c