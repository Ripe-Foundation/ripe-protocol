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
    human_resources,
    mission_control,
    switchboard,
    credit_engine,
    endaoment,
    ledger,
    lootbox,
    teller,
    boardroom,
    deploy3r,
    governance
):
    # finish token setup
    assert green_token.finishTokenSetup(ripe_hq_deploy, sender=deploy3r)
    assert savings_green.finishTokenSetup(ripe_hq_deploy, sender=deploy3r)
    assert ripe_token.finishTokenSetup(ripe_hq_deploy, sender=deploy3r)

    # data

    # 4
    assert ripe_hq_deploy.startAddNewAddressToRegistry(ledger, "Ledger", sender=deploy3r)
    assert ripe_hq_deploy.confirmNewAddressToRegistry(ledger, sender=deploy3r) == 4

    # 5
    assert ripe_hq_deploy.startAddNewAddressToRegistry(mission_control, "Mission Control", sender=deploy3r)
    assert ripe_hq_deploy.confirmNewAddressToRegistry(mission_control, sender=deploy3r) == 5

    # registries

    # 6
    assert ripe_hq_deploy.startAddNewAddressToRegistry(switchboard, "Switchboard", sender=deploy3r)
    assert ripe_hq_deploy.confirmNewAddressToRegistry(switchboard, sender=deploy3r) == 6

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
    assert ripe_hq_deploy.startAddNewAddressToRegistry(boardroom, "Boardroom", sender=deploy3r)
    assert ripe_hq_deploy.confirmNewAddressToRegistry(boardroom, sender=deploy3r) == 11

    # 12
    assert ripe_hq_deploy.startAddNewAddressToRegistry(bond_room, "Bond Room", sender=deploy3r)
    assert ripe_hq_deploy.confirmNewAddressToRegistry(bond_room, sender=deploy3r) == 12

    # 13
    assert ripe_hq_deploy.startAddNewAddressToRegistry(credit_engine, "Credit Engine", sender=deploy3r)
    assert ripe_hq_deploy.confirmNewAddressToRegistry(credit_engine, sender=deploy3r) == 13

    # 14
    assert ripe_hq_deploy.startAddNewAddressToRegistry(endaoment, "Endaoment", sender=deploy3r)
    assert ripe_hq_deploy.confirmNewAddressToRegistry(endaoment, sender=deploy3r) == 14

    # 15
    assert ripe_hq_deploy.startAddNewAddressToRegistry(human_resources, "Human Resources", sender=deploy3r)
    assert ripe_hq_deploy.confirmNewAddressToRegistry(human_resources, sender=deploy3r) == 15

    # 16
    assert ripe_hq_deploy.startAddNewAddressToRegistry(lootbox, "Lootbox", sender=deploy3r)
    assert ripe_hq_deploy.confirmNewAddressToRegistry(lootbox, sender=deploy3r) == 16

    # 17
    assert ripe_hq_deploy.startAddNewAddressToRegistry(teller, "Teller", sender=deploy3r)
    assert ripe_hq_deploy.confirmNewAddressToRegistry(teller, sender=deploy3r) == 17

    # special permission setup

    # switchboard can set token blacklists
    ripe_hq_deploy.initiateHqConfigChange(6, False, False, True, sender=deploy3r)
    assert ripe_hq_deploy.confirmHqConfigChange(6, sender=deploy3r)

    # vault book can mint ripe
    ripe_hq_deploy.initiateHqConfigChange(8, False, True, False, sender=deploy3r)
    assert ripe_hq_deploy.confirmHqConfigChange(8, sender=deploy3r)

    # auction house can mint green
    ripe_hq_deploy.initiateHqConfigChange(9, True, False, False, sender=deploy3r)
    assert ripe_hq_deploy.confirmHqConfigChange(9, sender=deploy3r)

    # bond room can mint ripe
    ripe_hq_deploy.initiateHqConfigChange(12, False, True, False, sender=deploy3r)
    assert ripe_hq_deploy.confirmHqConfigChange(12, sender=deploy3r)

    # credit engine can mint green
    ripe_hq_deploy.initiateHqConfigChange(13, True, False, False, sender=deploy3r)
    assert ripe_hq_deploy.confirmHqConfigChange(13, sender=deploy3r)

    # endaoment can mint green
    ripe_hq_deploy.initiateHqConfigChange(14, True, False, False, sender=deploy3r)
    assert ripe_hq_deploy.confirmHqConfigChange(14, sender=deploy3r)

    # human resources can mint ripe
    ripe_hq_deploy.initiateHqConfigChange(15, False, True, False, sender=deploy3r)
    assert ripe_hq_deploy.confirmHqConfigChange(15, sender=deploy3r)

    # lootbox can mint ripe
    ripe_hq_deploy.initiateHqConfigChange(16, False, True, False, sender=deploy3r)
    assert ripe_hq_deploy.confirmHqConfigChange(16, sender=deploy3r)

    # finish ripe hq setup
    assert ripe_hq_deploy.setRegistryTimeLockAfterSetup(sender=deploy3r)
    assert ripe_hq_deploy.finishRipeHqSetup(governance, sender=deploy3r)

    return ripe_hq_deploy


@pytest.fixture(scope="session")
def contributor_template():
    return boa.load_partial("contracts/modules/Contributor.vy").deploy_as_blueprint()


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
        10_000_000 * EIGHTEEN_DECIMALS,
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
        1_000_000_000 * EIGHTEEN_DECIMALS,
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


########
# Data #
########


# ledger


@pytest.fixture(scope="session")
def ledger(ripe_hq_deploy, defaults):
    return boa.load(
        "contracts/data/Ledger.vy",
        ripe_hq_deploy,
        defaults,
        name="ledger",
    )


# mission control


@pytest.fixture(scope="session")
def mission_control(ripe_hq_deploy, defaults):
    return boa.load(
        "contracts/data/MissionControl.vy",
        ripe_hq_deploy,
        defaults,
        name="mission_control",
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


# boardroom


@pytest.fixture(scope="session")
def boardroom(ripe_hq_deploy):
    return boa.load(
        "contracts/core/Boardroom.vy",
        ripe_hq_deploy,
        name="boardroom",
    )


# bond room


@pytest.fixture(scope="session")
def bond_room(ripe_hq_deploy, bond_booster):
    return boa.load(
        "contracts/core/BondRoom.vy",
        ripe_hq_deploy,
        bond_booster,
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
def endaoment(ripe_hq_deploy, fork):
    return boa.load(
        "contracts/core/Endaoment.vy",
        ripe_hq_deploy,
        ADDYS[fork]["WETH"],
        ADDYS[fork]["ETH"],
        name="endaoment",
    )


# human resources


@pytest.fixture(scope="session")
def human_resources(ripe_hq_deploy, fork, deploy3r):
    hr = boa.load(
        "contracts/core/HumanResources.vy",
        ripe_hq_deploy,
        PARAMS[fork]["MIN_HQ_CHANGE_TIMELOCK"],
        PARAMS[fork]["MAX_HQ_CHANGE_TIMELOCK"],
        name="human_resources",
    )
    assert hr.setActionTimeLockAfterSetup(sender=deploy3r)
    return hr

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
        False,
        name="teller",
    )


######################
# Switchboard Config #
######################


@pytest.fixture(scope="session")
def switchboard_deploy(ripe_hq_deploy, fork):
    return boa.load(
        "contracts/registries/Switchboard.vy",
        ripe_hq_deploy,
        PARAMS[fork]["MIN_HQ_CHANGE_TIMELOCK"],
        PARAMS[fork]["MAX_HQ_CHANGE_TIMELOCK"],
        name="switchboard",
    )


@pytest.fixture(scope="session")
def switchboard(switchboard_deploy, deploy3r, switchboard_alpha, switchboard_bravo, switchboard_charlie, switchboard_delta):

    # alpha
    assert switchboard_deploy.startAddNewAddressToRegistry(switchboard_alpha, "Alpha", sender=deploy3r)
    assert switchboard_deploy.confirmNewAddressToRegistry(switchboard_alpha, sender=deploy3r) == 1

    # bravo
    assert switchboard_deploy.startAddNewAddressToRegistry(switchboard_bravo, "Bravo", sender=deploy3r)
    assert switchboard_deploy.confirmNewAddressToRegistry(switchboard_bravo, sender=deploy3r) == 2

    # charlie
    assert switchboard_deploy.startAddNewAddressToRegistry(switchboard_charlie, "Charlie", sender=deploy3r)
    assert switchboard_deploy.confirmNewAddressToRegistry(switchboard_charlie, sender=deploy3r) == 3

    # delta
    assert switchboard_deploy.startAddNewAddressToRegistry(switchboard_delta, "Delta", sender=deploy3r)
    assert switchboard_deploy.confirmNewAddressToRegistry(switchboard_delta, sender=deploy3r) == 4

    # finish setup
    assert switchboard_deploy.setRegistryTimeLockAfterSetup(sender=deploy3r)

    # finish setup on switchboard config contracts
    assert switchboard_alpha.setActionTimeLockAfterSetup(sender=deploy3r)
    assert switchboard_bravo.setActionTimeLockAfterSetup(sender=deploy3r)
    assert switchboard_charlie.setActionTimeLockAfterSetup(sender=deploy3r)
    assert switchboard_delta.setActionTimeLockAfterSetup(sender=deploy3r)

    return switchboard_deploy


# switchboard alpha


@pytest.fixture(scope="session")
def switchboard_alpha(ripe_hq_deploy, fork):
    return boa.load(
        "contracts/config/SwitchboardAlpha.vy",
        ripe_hq_deploy,
        ZERO_ADDRESS,
        PARAMS[fork]["PRICE_DESK_MIN_STALE_TIME"],
        PARAMS[fork]["PRICE_DESK_MAX_STALE_TIME"],
        PARAMS[fork]["MIN_HQ_CHANGE_TIMELOCK"],
        PARAMS[fork]["MAX_HQ_CHANGE_TIMELOCK"],
        name="switchboard_alpha",
    )


# switchboard bravo


@pytest.fixture(scope="session")
def switchboard_bravo(ripe_hq_deploy, fork):
    return boa.load(
        "contracts/config/SwitchboardBravo.vy",
        ripe_hq_deploy,
        ZERO_ADDRESS,
        PARAMS[fork]["MIN_HQ_CHANGE_TIMELOCK"],
        PARAMS[fork]["MAX_HQ_CHANGE_TIMELOCK"],
        name="switchboard_bravo",
    )


# switchboard charlie


@pytest.fixture(scope="session")
def switchboard_charlie(ripe_hq_deploy, fork):
    return boa.load(
        "contracts/config/SwitchboardCharlie.vy",
        ripe_hq_deploy,
        ZERO_ADDRESS,
        PARAMS[fork]["MIN_HQ_CHANGE_TIMELOCK"],
        PARAMS[fork]["MAX_HQ_CHANGE_TIMELOCK"],
        name="switchboard_charlie",
    )


# switchboard delta


@pytest.fixture(scope="session")
def switchboard_delta(ripe_hq_deploy, fork):
    return boa.load(
        "contracts/config/SwitchboardDelta.vy",
        ripe_hq_deploy,
        ZERO_ADDRESS,
        PARAMS[fork]["MIN_HQ_CHANGE_TIMELOCK"],
        PARAMS[fork]["MAX_HQ_CHANGE_TIMELOCK"],
        name="switchboard_delta",
    )


# defaults


@pytest.fixture(scope="session")
def defaults(fork, contributor_template, training_wheels, mock_undy_v2):
    d = ZERO_ADDRESS
    if fork == "local":
        d = boa.load("contracts/config/DefaultsLocal.vy")
    elif fork == "base":
        d = boa.load("contracts/config/DefaultsBase.vy", contributor_template, training_wheels, mock_undy_v2)
    return d


# training wheels


@pytest.fixture(scope="session")
def training_wheels(ripe_hq_deploy):
    return boa.load(
        "contracts/config/TrainingWheels.vy",
        ripe_hq_deploy,
        [],
        name="training_wheels",
    )


# bond booster


@pytest.fixture(scope="session")
def bond_booster(ripe_hq_deploy):
    return boa.load(
        "contracts/config/BondBooster.vy",
        ripe_hq_deploy,
        1000 * EIGHTEEN_DECIMALS,  # _maxBoost
        100,                        # _maxUnits
        [],                         # _initialBoosts
        name="bond_booster",
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
def vault_book(vault_book_deploy, deploy3r, stability_pool, ripe_gov_vault, simple_erc20_vault, rebase_erc20_vault):

    # register stability pool
    assert vault_book_deploy.startAddNewAddressToRegistry(stability_pool, "Stability Pool", sender=deploy3r)
    assert vault_book_deploy.confirmNewAddressToRegistry(stability_pool, sender=deploy3r) == 1

    # register ripe gov vault
    assert vault_book_deploy.startAddNewAddressToRegistry(ripe_gov_vault, "Ripe Gov Vault", sender=deploy3r)
    assert vault_book_deploy.confirmNewAddressToRegistry(ripe_gov_vault, sender=deploy3r) == 2

    # register simple erc20 vault
    assert vault_book_deploy.startAddNewAddressToRegistry(simple_erc20_vault, "Simple ERC20 Vault", sender=deploy3r)
    assert vault_book_deploy.confirmNewAddressToRegistry(simple_erc20_vault, sender=deploy3r) == 3

    # register rebase erc20 vault
    assert vault_book_deploy.startAddNewAddressToRegistry(rebase_erc20_vault, "Rebase ERC20 Vault", sender=deploy3r)
    assert vault_book_deploy.confirmNewAddressToRegistry(rebase_erc20_vault, sender=deploy3r) == 4

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


# ripe gov vault


@pytest.fixture(scope="session")
def ripe_gov_vault(ripe_hq_deploy):
    return boa.load(
        "contracts/vaults/RipeGov.vy",
        ripe_hq_deploy,
        name="ripe_gov_vault",
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
def price_desk(price_desk_deploy, deploy3r, chainlink, mock_price_source, curve_prices, blue_chip_prices, pyth_prices, stork_prices):

    # register chainlink
    assert price_desk_deploy.startAddNewAddressToRegistry(chainlink, "Chainlink", sender=deploy3r)
    assert price_desk_deploy.confirmNewAddressToRegistry(chainlink, sender=deploy3r) == 1

    # register curve prices
    assert price_desk_deploy.startAddNewAddressToRegistry(curve_prices, "Curve Prices", sender=deploy3r)
    assert price_desk_deploy.confirmNewAddressToRegistry(curve_prices, sender=deploy3r) == 2

    # register blue chip prices
    assert price_desk_deploy.startAddNewAddressToRegistry(blue_chip_prices, "Blue Chip Prices", sender=deploy3r)
    assert price_desk_deploy.confirmNewAddressToRegistry(blue_chip_prices, sender=deploy3r) == 3

    # register pyth prices
    assert price_desk_deploy.startAddNewAddressToRegistry(pyth_prices, "Pyth Prices", sender=deploy3r)
    assert price_desk_deploy.confirmNewAddressToRegistry(pyth_prices, sender=deploy3r) == 4

    # register stork prices
    assert price_desk_deploy.startAddNewAddressToRegistry(stork_prices, "Stork Prices", sender=deploy3r)
    assert price_desk_deploy.confirmNewAddressToRegistry(stork_prices, sender=deploy3r) == 5

    # register mock price source
    assert price_desk_deploy.startAddNewAddressToRegistry(mock_price_source, "Mock Price Source", sender=deploy3r)
    assert price_desk_deploy.confirmNewAddressToRegistry(mock_price_source, sender=deploy3r) == 6

    # finish registry setup
    assert price_desk_deploy.setRegistryTimeLockAfterSetup(sender=deploy3r)

    return price_desk_deploy


# chainlink


@pytest.fixture(scope="session")
def chainlink(ripe_hq_deploy, fork, sally, bob, deploy3r, mock_chainlink_feed_one, mock_chainlink_feed_two):
    CHAINLINK_ETH_USD = ZERO_ADDRESS if fork == "local" else ADDYS[fork]["CHAINLINK_ETH_USD"]
    CHAINLINK_BTC_USD = ZERO_ADDRESS if fork == "local" else ADDYS[fork]["CHAINLINK_BTC_USD"]

    c = boa.load(
        "contracts/priceSources/ChainlinkPrices.vy",
        ripe_hq_deploy,
        ZERO_ADDRESS,
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


# curve prices


@pytest.fixture(scope="session")
def curve_prices(ripe_hq_deploy, fork, deploy3r, green_token, savings_green):
    curve_address_provider = ZERO_ADDRESS if fork == "local" else ADDYS[fork]["CURVE_ADDRESS_PROVIDER"]

    c = boa.load(
        "contracts/priceSources/CurvePrices.vy",
        ripe_hq_deploy,
        ZERO_ADDRESS,
        curve_address_provider,
        green_token,
        savings_green,
        PARAMS[fork]["PRICE_DESK_MIN_REG_TIMELOCK"],
        PARAMS[fork]["PRICE_DESK_MAX_REG_TIMELOCK"],
        name="curve_prices",
    )
    assert c.setActionTimeLockAfterSetup(sender=deploy3r)
    return c


# blue chip vault token prices


@pytest.fixture(scope="session")
def blue_chip_prices(ripe_hq_deploy, fork, deploy3r, mock_yield_registry):
    MORPHO_A = mock_yield_registry if fork == "local" else ADDYS[fork]["MORPHO_FACTORY"]
    MORPHO_B = mock_yield_registry if fork == "local" else ADDYS[fork]["MORPHO_FACTORY_LEGACY"]
    EULER_A = mock_yield_registry if fork == "local" else ADDYS[fork]["EULER_EVAULT_FACTORY"]
    EULER_B = mock_yield_registry if fork == "local" else ADDYS[fork]["EULER_EARN_FACTORY"]
    FLUID = mock_yield_registry if fork == "local" else ADDYS[fork]["FLUID_RESOLVER"]
    COMPOUND_V3 = mock_yield_registry if fork == "local" else ADDYS[fork]["COMPOUND_V3_CONFIGURATOR"]
    MOONWELL = mock_yield_registry if fork == "local" else ADDYS[fork]["MOONWELL_COMPTROLLER"]
    AAVE_V3 = mock_yield_registry if fork == "local" else ADDYS[fork]["AAVE_V3_ADDRESS_PROVIDER"]

    c = boa.load(
        "contracts/priceSources/BlueChipYieldPrices.vy",
        ripe_hq_deploy,
        ZERO_ADDRESS,
        PARAMS[fork]["PRICE_DESK_MIN_REG_TIMELOCK"],
        PARAMS[fork]["PRICE_DESK_MAX_REG_TIMELOCK"],
        [MORPHO_A, MORPHO_B],
        [EULER_A, EULER_B],
        FLUID,
        COMPOUND_V3,
        MOONWELL,
        AAVE_V3,
        name="blue_chip_prices",
    )
    assert c.setActionTimeLockAfterSetup(sender=deploy3r)
    return c


# pyth prices


@pytest.fixture(scope="session")
def pyth_prices(ripe_hq_deploy, fork, deploy3r, mock_pyth):
    pyth_network = mock_pyth if fork == "local" else ADDYS[fork]["PYTH_NETWORK"]

    c = boa.load(
        "contracts/priceSources/PythPrices.vy",
        ripe_hq_deploy,
        ZERO_ADDRESS,
        pyth_network,
        PARAMS[fork]["PRICE_DESK_MIN_REG_TIMELOCK"],
        PARAMS[fork]["PRICE_DESK_MAX_REG_TIMELOCK"],
        name="pyth_prices",
    )
    assert c.setActionTimeLockAfterSetup(sender=deploy3r)
    return c


# stork prices


@pytest.fixture(scope="session")
def stork_prices(ripe_hq_deploy, fork, deploy3r, mock_stork):
    stork_network = mock_stork if fork == "local" else ADDYS[fork]["STORK_NETWORK"]

    c = boa.load(
        "contracts/priceSources/StorkPrices.vy",
        ripe_hq_deploy,
        ZERO_ADDRESS,
        stork_network,
        PARAMS[fork]["PRICE_DESK_MIN_REG_TIMELOCK"],
        PARAMS[fork]["PRICE_DESK_MAX_REG_TIMELOCK"],
        name="stork_prices",
    )
    assert c.setActionTimeLockAfterSetup(sender=deploy3r)
    return c
