import pytest
import boa

from constants import EIGHTEEN_DECIMALS


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
def sally(env):
    return env.generate_address("sally")


@pytest.fixture(scope="session")
def governance():
    # cannot be EOA
    return boa.load("contracts/mock/MockGov.vy", name="mock_gov")


##########
# Assets #
##########


# alpha token


@pytest.fixture(scope="session")
def alpha_token(governance):
    return boa.load("contracts/mock/MockErc20.vy", governance, "Alpha Token", "ALPHA", 18, 10_000_000, name="alpha_token")


@pytest.fixture(scope="session")
def alpha_token_whale(env, alpha_token, governance):
    whale = env.generate_address("alpha_token_whale")
    alpha_token.mint(whale, 1_000_000 * (10 ** alpha_token.decimals()), sender=governance)
    return whale


@pytest.fixture(scope="session")
def alpha_token_vault(alpha_token):
    return boa.load("contracts/mock/MockErc4626Vault.vy", alpha_token, name="alpha_erc4626_vault")


# bravo token


@pytest.fixture(scope="session")
def bravo_token(governance):
    return boa.load("contracts/mock/MockErc20.vy", governance, "Bravo Token", "BRAVO", 18, 10_000_000, name="bravo_token")


@pytest.fixture(scope="session")
def bravo_token_whale(env, bravo_token, governance):
    whale = env.generate_address("bravo_token_whale")
    bravo_token.mint(whale, 1_000_000 * (10 ** bravo_token.decimals()), sender=governance)
    return whale


@pytest.fixture(scope="session")
def bravo_token_vault(bravo_token):
    return boa.load("contracts/mock/MockErc4626Vault.vy", bravo_token, name="bravo_erc4626_vault")


# charlie token (6 decimals)


@pytest.fixture(scope="session")
def charlie_token(governance):
    return boa.load("contracts/mock/MockErc20.vy", governance, "Charlie Token", "CHARLIE", 6, 10_000_000, name="charlie_token")


@pytest.fixture(scope="session")
def charlie_token_whale(env, charlie_token, governance):
    whale = env.generate_address("charlie_token_whale")
    charlie_token.mint(whale, 1_000_000 * (10 ** charlie_token.decimals()), sender=governance)
    return whale


@pytest.fixture(scope="session")
def charlie_token_vault(charlie_token):
    return boa.load("contracts/mock/MockErc4626Vault.vy", charlie_token, name="charlie_erc4626_vault")


#################
# Price Sources #
#################


@pytest.fixture(scope="session")
def mock_price_source(ripe_hq_deploy, price_desk_deploy):
    return boa.load(
        "contracts/mock/MockPriceSource.vy",
        ripe_hq_deploy,
        price_desk_deploy,
        name="mock_price_source",
    )


@pytest.fixture(scope="session")
def mock_chainlink_feed_one():
    return boa.load(
        "contracts/mock/MockChainlinkFeed.vy",
        EIGHTEEN_DECIMALS, # $1
        name="mock_chainlink_feed_one",
    )


@pytest.fixture(scope="session")
def mock_chainlink_feed_two():
    return boa.load(
        "contracts/mock/MockChainlinkFeed.vy",
        EIGHTEEN_DECIMALS, # $1
        name="mock_chainlink_feed_two",
    )