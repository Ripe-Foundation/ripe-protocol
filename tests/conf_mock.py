import pytest
import boa


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
def governor(env):
    return env.generate_address("governor")


##########
# Assets #
##########


# alpha token


@pytest.fixture(scope="session")
def alpha_token(governor):
    return boa.load("contracts/mock/MockErc20.vy", governor, "Alpha Token", "ALPHA", 18, 10_000_000, name="alpha_token")


@pytest.fixture(scope="session")
def alpha_token_whale(env, alpha_token, governor):
    whale = env.generate_address("alpha_token_whale")
    alpha_token.mint(whale, 1_000_000 * (10 ** alpha_token.decimals()), sender=governor)
    return whale


@pytest.fixture(scope="session")
def alpha_token_vault(alpha_token):
    return boa.load("contracts/mock/MockErc4626Vault.vy", alpha_token, name="alpha_erc4626_vault")


# bravo token


@pytest.fixture(scope="session")
def bravo_token(governor):
    return boa.load("contracts/mock/MockErc20.vy", governor, "Bravo Token", "BRAVO", 18, 10_000_000, name="bravo_token")


@pytest.fixture(scope="session")
def bravo_token_whale(env, bravo_token, governor):
    whale = env.generate_address("bravo_token_whale")
    bravo_token.mint(whale, 1_000_000 * (10 ** bravo_token.decimals()), sender=governor)
    return whale


@pytest.fixture(scope="session")
def bravo_token_vault(bravo_token):
    return boa.load("contracts/mock/MockErc4626Vault.vy", bravo_token, name="bravo_erc4626_vault")


# charlie token (6 decimals)


@pytest.fixture(scope="session")
def charlie_token(governor):
    return boa.load("contracts/mock/MockErc20.vy", governor, "Charlie Token", "CHARLIE", 6, 10_000_000, name="charlie_token")


@pytest.fixture(scope="session")
def charlie_token_whale(env, charlie_token, governor):
    whale = env.generate_address("charlie_token_whale")
    charlie_token.mint(whale, 1_000_000 * (10 ** charlie_token.decimals()), sender=governor)
    return whale


@pytest.fixture(scope="session")
def charlie_token_vault(charlie_token):
    return boa.load("contracts/mock/MockErc4626Vault.vy", charlie_token, name="charlie_erc4626_vault")


#################
# Price Sources #
#################


@pytest.fixture(scope="session")
def mock_price_source(price_desk, governor):
    mock_price_source = boa.load(
        "contracts/mock/MockPriceSource.vy",
        name="mock_price_source",
    )

    # register with price desk
    assert price_desk.registerNewPriceSource(mock_price_source.address, "Mock Price Source", sender=governor)
    boa.env.time_travel(blocks=price_desk.priceSourceChangeDelay() + 1)
    assert price_desk.confirmNewPriceSourceRegistration(mock_price_source.address, sender=governor) != 0

    return mock_price_source
