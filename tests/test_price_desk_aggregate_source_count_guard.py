import pytest

from config.BluePrint import ROBINHOOD_REGISTRY_TOPOLOGY


QUALIFIED_PRICE_DESK_SOURCE_COUNT = 3


@pytest.fixture(scope="session")
def ripe_hq():
    """Keep this source-only launch-topology assertion out of core setup."""


def test_robinhood_price_desk_source_count_requires_gas_requalification_on_growth():
    selected_sources = tuple(
        row
        for row in ROBINHOOD_REGISTRY_TOPOLOGY
        if row.domain == "price_desk" and row.selection_state == "selected"
    )
    assert [row.registry_id for row in selected_sources] == [1, 2, 3]
    assert len(selected_sources) <= QUALIFIED_PRICE_DESK_SOURCE_COUNT, (
        "Robinhood PriceDesk source growth requires aggregate protocol-gas "
        "requalification before activation"
    )
