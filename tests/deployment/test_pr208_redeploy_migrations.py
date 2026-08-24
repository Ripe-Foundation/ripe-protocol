from __future__ import annotations

import importlib.util
from pathlib import Path

from config.robinhood_launch import (
    CURVE_PRICES_ID,
    PYTH_PRICES_ID,
    STALE_WINDOW_INHERIT,
    TELLER_SHOULD_PAUSE,
)


ROOT = Path(__file__).resolve().parents[2]


def _load(relative_path: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


DEPLOY = _load(
    "migrations/robinhood-mainnet/2026082405_RedeployPr208.py",
    "pr208_redeploy",
)
PROMOTE = _load(
    "migrations/robinhood-mainnet/2026082406_PromotePr208.py",
    "pr208_promote",
)


EXPECTED_REPLACEMENTS = {
    "SwitchboardAlpha",
    "SwitchboardBravo",
    "SwitchboardCharlie",
    "PriceDesk",
    "ChainlinkPrices",
    "CurvePrices",
    "VaultBook",
    "StabilityPool",
    "CreditEngine",
    "Endaoment",
    "Teller",
}


def test_pr208_redeploy_boundary_is_exactly_the_changed_live_generation():
    assert set(PROMOTE.CANONICAL_SOURCE_PATHS) == EXPECTED_REPLACEMENTS
    assert DEPLOY.HQ_REPLACEMENTS == (
        ("PriceDesk", 7),
        ("VaultBook", 8),
        ("CreditEngine", 13),
        ("Endaoment", 14),
        ("Teller", 17),
    )
    assert DEPLOY.SWITCHBOARD_REPLACEMENTS == (
        ("SwitchboardAlpha", 1),
        ("SwitchboardBravo", 2),
        ("SwitchboardCharlie", 3),
    )
    assert EXPECTED_REPLACEMENTS.isdisjoint(
        {
            "RipeHq",
            "GreenToken",
            "SavingsGreen",
            "RipeToken",
            "Ledger",
            "MissionControl",
            "UniswapV2Prices",
            "RipeGov",
            "SimpleErc20",
        }
    )


def test_pr208_plan_preserves_unchanged_children_and_uses_target_stale_policy():
    source = Path(DEPLOY.__file__).read_text()
    assert 'migration.get_contract("UniswapV2Prices")' in source
    assert 'migration.get_contract("RipeGov")' in source
    assert 'migration.get_contract("SimpleErc20")' in source
    assert "stale_time_override_for_asset(str(asset))" in source
    assert "STALE_WINDOW_INHERIT" in source
    assert "active_curve.getPricedAssets()" in source
    assert "active_curve.greenRefPoolConfig()" in source


def test_pr208_plan_is_readable_and_only_relinquishes_temporary_governance():
    source = Path(DEPLOY.__file__).read_text()
    assert "await c.Ripe_RH_RipeHq.startAddressUpdateToRegistry" in source
    assert "await c.Ripe_RH_Switchboard.startAddressUpdateToRegistry" in source
    assert "relinquishGov" in source
    assert "setActionTimeLockAfterSetup" not in source
    assert "setRegistryTimeLockAfterSetup" not in source
    assert "_calldata" not in source
    assert "eth_abi" not in source


def test_pr208_constructor_policy_is_explicit():
    assert CURVE_PRICES_ID == 2
    assert PYTH_PRICES_ID == 0
    assert STALE_WINDOW_INHERIT == 0
    assert TELLER_SHOULD_PAUSE is True
    source = Path(DEPLOY.__file__).read_text()
    assert "PYTH_PRICES_ID," in source
    assert "CURVE_PRICES_ID," in source
    assert "TELLER_SHOULD_PAUSE," in source
    assert 'charlie.pause(\"{teller.address}\", false)' in source


def test_pr208_promotion_is_one_eleven_candidate_batch():
    source = Path(PROMOTE.__file__).read_text()
    assert "len(promotions) == len(CANONICAL_SOURCE_PATHS) == 11" in source
    assert 'candidate_label("PriceDesk")' in source
    assert 'candidate_label("VaultBook")' in source
    assert "stale_time_override_for_asset(str(asset))" in source
    assert "migration.promote_candidates(promotions)" in source
