import pytest
import boa

from config.BluePrint import PARAMS, ADDYS
from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS


############
# Accounts #
############


@pytest.fixture(scope="session")
def deploy3r(env):
    return env.eoa


@pytest.fixture(scope="session")
def sally(env):
    return env.generate_address("sally")


@pytest.fixture(scope="session")
def bob(env):
    return env.generate_address("bob")


@pytest.fixture(scope="session")
def alice(env):
    return env.generate_address("alice")


@pytest.fixture(scope="session")
def charlie(env):
    return env.generate_address("charlie")


@pytest.fixture(scope="session")
def governance():
    # cannot be EOA
    return boa.load("contracts/mock/MockRando.vy", name="mock_gov")


@pytest.fixture(scope="session")
def whale(env):
    return env.generate_address("whale")


##########
# Assets #
##########


# alpha token


@pytest.fixture(scope="session")
def alpha_token(governance):
    return boa.load("contracts/mock/MockErc20.vy", governance, "Alpha Token", "ALPHA", 18, 1_000_000_000, name="alpha_token")


@pytest.fixture(scope="session")
def alpha_token_whale(env, alpha_token, governance):
    whale = env.generate_address("alpha_token_whale")
    alpha_token.mint(whale, 100_000_000 * (10 ** alpha_token.decimals()), sender=governance.address)
    return whale


@pytest.fixture(scope="session")
def alpha_token_vault(alpha_token):
    return boa.load("contracts/mock/MockErc4626Vault.vy", alpha_token, name="alpha_erc4626_vault")


# bravo token


@pytest.fixture(scope="session")
def bravo_token(governance):
    return boa.load("contracts/mock/MockErc20.vy", governance, "Bravo Token", "BRAVO", 18, 1_000_000_000, name="bravo_token")


@pytest.fixture(scope="session")
def bravo_token_whale(env, bravo_token, governance):
    whale = env.generate_address("bravo_token_whale")
    bravo_token.mint(whale, 100_000_000 * (10 ** bravo_token.decimals()), sender=governance.address)
    return whale


@pytest.fixture(scope="session")
def bravo_token_vault(bravo_token):
    return boa.load("contracts/mock/MockErc4626Vault.vy", bravo_token, name="bravo_erc4626_vault")


# charlie token (6 decimals)


@pytest.fixture(scope="session")
def charlie_token(governance):
    return boa.load("contracts/mock/MockErc20.vy", governance, "Charlie Token", "CHARLIE", 6, 1_000_000_000, name="charlie_token")


@pytest.fixture(scope="session")
def charlie_token_whale(env, charlie_token, governance):
    whale = env.generate_address("charlie_token_whale")
    charlie_token.mint(whale, 100_000_000 * (10 ** charlie_token.decimals()), sender=governance.address)
    return whale


@pytest.fixture(scope="session")
def charlie_token_vault(charlie_token):
    return boa.load("contracts/mock/MockErc4626Vault.vy", charlie_token, name="charlie_erc4626_vault")


# delta token (8 decimals)


@pytest.fixture(scope="session")
def delta_token(governance):
    return boa.load("contracts/mock/MockErc20.vy", governance, "Delta Token", "DELTA", 8, 1_000_000_000, name="delta_token")


@pytest.fixture(scope="session")
def delta_token_whale(env, delta_token, governance):
    whale = env.generate_address("delta_token_whale")
    delta_token.mint(whale, 100_000_000 * (10 ** delta_token.decimals()), sender=governance.address)
    return whale


@pytest.fixture(scope="session")
def delta_token_vault(delta_token):
    return boa.load("contracts/mock/MockErc4626Vault.vy", delta_token, name="delta_erc4626_vault")


#################
# Price Sources #
#################


@pytest.fixture(scope="session")
def mock_price_source(ripe_hq_deploy, fork):
    return boa.load(
        "contracts/mock/MockPriceSource.vy",
        ripe_hq_deploy,
        PARAMS[fork]["PRICE_DESK_MIN_REG_TIMELOCK"],
        PARAMS[fork]["PRICE_DESK_MAX_REG_TIMELOCK"],
        name="mock_price_source",
    )


@pytest.fixture(scope="session")
def mock_curve_prices(ripe_hq_deploy, fork):
    return boa.load(
        "contracts/mock/MockCurvePrices.vy",
        ripe_hq_deploy,
        PARAMS[fork]["PRICE_DESK_MIN_REG_TIMELOCK"],
        PARAMS[fork]["PRICE_DESK_MAX_REG_TIMELOCK"],
        name="mock_curve_prices",
    )


@pytest.fixture(scope="session")
def mock_chainlink_feed_one():
    return boa.load(
        "contracts/mock/MockChainlinkFeed.vy",
        EIGHTEEN_DECIMALS,  # $1
        name="mock_chainlink_feed_one",
    )


@pytest.fixture(scope="session")
def mock_chainlink_feed_two():
    return boa.load(
        "contracts/mock/MockChainlinkFeed.vy",
        EIGHTEEN_DECIMALS,  # $1
        name="mock_chainlink_feed_two",
    )


###############
# Other Mocks #
###############


@pytest.fixture(scope="session")
def mock_rando_contract():
    return boa.load("contracts/mock/MockRando.vy", name="rando_contract")


@pytest.fixture(scope="session")
def mock_whitelist():
    return boa.load("contracts/mock/MockWhitelist.vy", name="mock_whitelist")


@pytest.fixture(scope="session")
def mock_registry(ripe_hq_deploy, fork):
    return boa.load(
        "contracts/mock/MockRegistry.vy",
        ripe_hq_deploy,
        PARAMS[fork]["MIN_HQ_CHANGE_TIMELOCK"],  # initial time lock
        PARAMS[fork]["MIN_HQ_CHANGE_TIMELOCK"],
        PARAMS[fork]["MAX_HQ_CHANGE_TIMELOCK"],
        name="mock_registry",
    )


@pytest.fixture(scope="session")
def mock_dept_can_mint_green(ripe_hq_deploy):
    return boa.load("contracts/mock/MockDepartment.vy", ripe_hq_deploy, True, False, name="mock_dept_can_mint_green")


@pytest.fixture(scope="session")
def mock_dept_can_mint_ripe(ripe_hq_deploy):
    return boa.load("contracts/mock/MockDepartment.vy", ripe_hq_deploy, False, True, name="mock_dept_can_mint_ripe")


@pytest.fixture(scope="session")
def mock_yield_registry(alpha_token_vault, bravo_token_vault, charlie_token_vault, delta_token_vault):
    return boa.load("contracts/mock/MockYieldRegistry.vy", [alpha_token_vault, bravo_token_vault, charlie_token_vault, delta_token_vault], name="mock_yield_registry")


@pytest.fixture(scope="session")
def mock_pyth():
    return boa.load("contracts/mock/MockPyth.vy", name="mock_pyth")


@pytest.fixture(scope="session")
def mock_stork():
    return boa.load("contracts/mock/MockStork.vy", name="mock_stork")


@pytest.fixture(scope="session")
def mock_undy_v2(fork):
    underscore_registry = ADDYS[fork]["UNDERSCORE_REGISTRY"] if fork != "local" else ZERO_ADDRESS
    return boa.load("contracts/mock/MockUndyV2.vy", underscore_registry, name="mock_undy_v2")