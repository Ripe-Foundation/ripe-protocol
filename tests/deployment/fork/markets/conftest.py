from __future__ import annotations

import pytest


@pytest.fixture
def injected_market_state():
    return {
        "lp_ledger": {
            "green_liquidity": 31_415_926,
            "ripe_liquidity": 27_182_818,
        },
        "psm_ledger": {
            "green_reserve": 100_000_003,
            "usdg_reserve": 90_000_007,
        },
        "psm_paused": True,
    }
