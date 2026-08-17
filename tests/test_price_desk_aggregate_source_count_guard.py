import re
from pathlib import Path

import boa
import pytest

from config.BluePrint import ROBINHOOD_REGISTRY_TOPOLOGY
from registries.price_desk_aggregate_qualification import (
    DELEVERAGE_MANY_API_MAX,
    LIQUIDATE_MANY_API_MAX,
    QUALIFIED_BORROWER_ASSET_COUNT,
    QUALIFIED_PRICE_DESK_SOURCE_COUNT,
    QUALIFIED_PRICE_SOURCE_PRICE_GAS_STIPEND,
    QUALIFIED_SATURATED_DELEVERAGE_BATCH_SIZE,
    QUALIFIED_SATURATED_LIQUIDATION_BATCH_SIZE,
    ROBINHOOD_LIVE_PRICE_DESK_SLOT_3,
    ROBINHOOD_LIVE_PRICE_DESK_SLOT_3_ADDRESS,
)


@pytest.fixture(scope="session")
def ripe_hq():
    """Keep these source/config-only guards out of the full core setup."""


def _source_uint_constant(path, name):
    source = Path(path).read_text()
    match = re.search(
        rf"^{name}: constant\(uint256\) = ([0-9_]+)$",
        source,
        flags=re.MULTILINE,
    )
    assert match is not None, f"cannot bind {name} for aggregate-gas guard"
    return int(match.group(1).replace("_", ""))


def _source_address_constant(path, name):
    source = Path(path).read_text()
    match = re.search(
        rf"^{name}: constant\(address\) = (0x[0-9A-Fa-f]{{40}})$",
        source,
        flags=re.MULTILINE,
    )
    assert match is not None, f"cannot bind {name} for aggregate-gas guard"
    return match.group(1).lower()


def _selected_price_sources():
    return tuple(
        row
        for row in ROBINHOOD_REGISTRY_TOPOLOGY
        if row.domain == "price_desk" and row.selection_state == "selected"
    )


def test_robinhood_price_desk_source_count_requires_gas_requalification_on_growth():
    selected_sources = _selected_price_sources()
    assert len(selected_sources) <= QUALIFIED_PRICE_DESK_SOURCE_COUNT, (
        "Robinhood PriceDesk source growth requires aggregate protocol-gas "
        "requalification before activation"
    )
    assert [row.registry_id for row in selected_sources] == [1, 2, 3], (
        "Robinhood PriceDesk registry ordering changed; aggregate protocol-gas "
        "requalification is required before activation"
    )
    assert [row.semantic_name for row in selected_sources] == [
        "Chainlink",
        "Curve",
        "BlueChipYield",
    ], (
        "Robinhood PriceDesk source composition changed; aggregate protocol-gas "
        "requalification is required before activation"
    )


def test_robinhood_enumerable_position_count_requires_gas_requalification_on_growth():
    defaults = boa.load(
        "contracts/config/DefaultsRobinhoodLive.vy",
        name="aggregate_gas_robinhood_live_defaults",
    )
    enumerable_non_stability_positions = tuple(
        (entry.asset, vault_id)
        for entry in defaults.assetConfigs()
        for vault_id in entry.config.vaultIds
        if vault_id != 1
    )
    assert len(enumerable_non_stability_positions) <= QUALIFIED_BORROWER_ASSET_COUNT, (
        "Robinhood enumerable non-stability position growth requires aggregate "
        "protocol-gas requalification before activation"
    )


def test_unqualified_price_assets_remain_zero_ltv():
    defaults_path = "contracts/config/DefaultsRobinhoodLive.vy"
    defaults = boa.load(
        defaults_path,
        name="aggregate_gas_robinhood_live_zero_ltv_defaults",
    )
    configs_by_asset = {
        str(entry.asset).lower(): entry.config
        for entry in defaults.assetConfigs()
    }
    for constant_name in ("RIPE_TOKEN", "RIPE_WETH_LP"):
        asset = _source_address_constant(defaults_path, constant_name)
        assert asset in configs_by_asset, (
            f"{constant_name} is missing from the zero-LTV aggregate-gas guard"
        )
        assert configs_by_asset[asset].debtTerms.ltv == 0, (
            f"{constant_name} received nonzero LTV; the nested or unavailable "
            "price path now reaches collateral-health checks and requires "
            "aggregate-gas requalification before activation"
        )


def test_batch_api_maxima_and_smaller_qualified_operator_limits_are_explicit():
    assert _source_uint_constant(
        "contracts/registries/PriceDesk.vy",
        "PRICE_SOURCE_PRICE_GAS",
    ) == QUALIFIED_PRICE_SOURCE_PRICE_GAS_STIPEND, (
        "PriceDesk price-source stipend changed; aggregate protocol-gas "
        "requalification is required"
    )
    assert _source_uint_constant(
        "contracts/core/Teller.vy",
        "MAX_LIQ_USERS",
    ) == LIQUIDATE_MANY_API_MAX, (
        "liquidation batch API maximum changed; aggregate protocol-gas "
        "requalification is required"
    )
    assert _source_uint_constant(
        "contracts/core/Deleverage.vy",
        "MAX_DELEVERAGE_USERS",
    ) == DELEVERAGE_MANY_API_MAX, (
        "Deleverage batch API maximum changed; aggregate protocol-gas "
        "requalification is required"
    )
    assert (
        QUALIFIED_SATURATED_LIQUIDATION_BATCH_SIZE < LIQUIDATE_MANY_API_MAX
        and QUALIFIED_SATURATED_DELEVERAGE_BATCH_SIZE < DELEVERAGE_MANY_API_MAX
    ), "qualified keeper batches must remain explicit and below ABI maxima"


def test_observed_live_slot_three_divergence_is_documented_for_manual_recheck():
    repository_slot_three = next(
        row for row in _selected_price_sources() if row.registry_id == 3
    )
    assert repository_slot_three.semantic_name == "BlueChipYield"
    assert len(ROBINHOOD_LIVE_PRICE_DESK_SLOT_3_ADDRESS) == 42
    assert int(ROBINHOOD_LIVE_PRICE_DESK_SLOT_3_ADDRESS, 16) != 0
    assert repository_slot_three.semantic_name != ROBINHOOD_LIVE_PRICE_DESK_SLOT_3, (
        "the documented slot-3 snapshot no longer differs from the repository; "
        "manually reread live state and update aggregate-gas qualification"
    )
