from itertools import combinations

import boa
import pytest

from constants import ZERO_ADDRESS


ROLE_NAMES = (
    "contrib_template",
    "training_wheels",
    "ripe_token",
    "green_token",
    "savings_green",
    "usdg_token",
    "weth_token",
)


@pytest.fixture(scope="session")
def ripe_hq():
    """Constructor-only tests do not need the protocol deployment graph."""


def _roles(label):
    values = tuple(
        boa.env.generate_address(f"defaults-robinhood-{label}-{role}")
        for role in ROLE_NAMES
    )
    assert ZERO_ADDRESS not in values
    assert len(set(values)) == len(ROLE_NAMES)
    return values


def _deploy(values):
    return boa.load("contracts/config/DefaultsRobinhood.vy", *values)


def test_constructor_accepts_seven_nonzero_distinct_roles():
    values = _roles("valid")
    defaults = _deploy(values)

    contrib, training_wheels, ripe, green, savings_green, usdg, weth = values
    assert defaults.hrConfig().contribTemplate == contrib
    assert defaults.trainingWheels() == training_wheels
    assert [row.asset for row in defaults.ripeGovVaultConfigs()] == [ripe]
    assert [row.asset for row in defaults.assetConfigs()] == [
        weth,
        ripe,
        savings_green,
        green,
    ]
    assert defaults.ripeBondConfig().asset == usdg


@pytest.mark.parametrize(
    "zero_index",
    range(len(ROLE_NAMES)),
    ids=ROLE_NAMES,
)
def test_constructor_rejects_zero_for_every_role(zero_index):
    values = list(_roles(f"zero-{ROLE_NAMES[zero_index]}"))
    values[zero_index] = ZERO_ADDRESS

    with boa.reverts("invalid defaults address"):
        _deploy(values)


ROLE_PAIRS = tuple(combinations(range(len(ROLE_NAMES)), 2))


@pytest.mark.parametrize(
    ("first_index", "second_index"),
    ROLE_PAIRS,
    ids=(
        f"{ROLE_NAMES[first]}-equals-{ROLE_NAMES[second]}"
        for first, second in ROLE_PAIRS
    ),
)
def test_constructor_rejects_every_pairwise_duplicate(first_index, second_index):
    values = list(
        _roles(
            f"duplicate-{ROLE_NAMES[first_index]}-{ROLE_NAMES[second_index]}"
        )
    )
    values[second_index] = values[first_index]

    with boa.reverts("duplicate defaults address"):
        _deploy(values)
