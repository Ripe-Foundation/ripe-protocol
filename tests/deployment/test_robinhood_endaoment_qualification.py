from __future__ import annotations

import pytest

from config.BluePrint import (
    ROBINHOOD_ADDRESSES,
    ROBINHOOD_ADDRESS_STATUS,
    ROBINHOOD_ENDAOMENT_QUALIFICATION,
    ZERO_ADDRESS,
)
from config.robinhood_launch import validate_endaoment_qualification


def test_robinhood_endaoment_deployment_and_configuration_fail_closed():
    gate = ROBINHOOD_ENDAOMENT_QUALIFICATION

    assert gate["deployment_allowed"] is False
    assert gate["partner_liquidity_configuration_allowed"] is False
    assert gate["qualified_legos"] == ()
    assert gate["qualified_partner_assets"] == ()
    assert ROBINHOOD_ADDRESS_STATUS["WETH"] == (
        "selected_external_fact_unverified"
    )
    assert ROBINHOOD_ADDRESSES["UNDERSCORE_REGISTRY"] == ZERO_ADDRESS

    with pytest.raises(ValueError, match="RH_ENDAOMENT_QUALIFICATION_BLOCKED"):
        validate_endaoment_qualification()
