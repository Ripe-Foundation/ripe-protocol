from __future__ import annotations

import re

import pytest

from config import robinhood_launch
from scripts import ledger_signing_smoke, prepare_defaults


@pytest.mark.parametrize("observed", (1, 8453, 46630, 0))
def test_ledger_smoke_rejects_every_non_robinhood_mainnet_chain(observed):
    with pytest.raises(SystemExit, match="LEDGER_SMOKE_CHAIN_MISMATCH"):
        ledger_signing_smoke._require_robinhood_chain_id(observed)


def test_ledger_smoke_accepts_robinhood_mainnet_chain():
    ledger_signing_smoke._require_robinhood_chain_id(4663)


@pytest.mark.parametrize("observed", (1, 8453, 46630, 0))
def test_defaults_snapshot_rejects_every_non_robinhood_mainnet_chain(
    observed,
):
    with pytest.raises(RuntimeError, match="DEFAULTS_CHAIN_MISMATCH"):
        prepare_defaults._require_robinhood_chain_id(observed)


def test_defaults_snapshot_accepts_robinhood_mainnet_chain():
    prepare_defaults._require_robinhood_chain_id(4663)


def test_defaults_snapshot_sanitizes_untrusted_token_metadata():
    malicious = "7\n@external\ndef steal():\n    pass\N{SNOWMAN}"

    identifier = prepare_defaults._safe_constant_name(malicious)
    comment = prepare_defaults._safe_asset_comment(malicious, "fallback")

    assert re.fullmatch(r"[A-Z][A-Z0-9_]*", identifier)
    assert identifier.startswith("ASSET_7_")
    assert "\n" not in comment and "\r" not in comment
    assert "\N{SNOWMAN}" not in comment
    assert len(comment) <= 80


def test_defaults_snapshot_preserves_safe_existing_labels():
    assert prepare_defaults._safe_constant_name("GreenUsdgPool") == (
        "GREEN_USDG_POOL"
    )
    assert prepare_defaults._safe_constant_name("SPCX") == "SPCX"
    assert prepare_defaults._safe_asset_comment("UNI-V2", "fallback") == (
        "UNI-V2"
    )


@pytest.mark.parametrize(
    "key",
    (
        "USDG",
        "WETH",
        "GOVERNANCE",
        "CHAINLINK_ETH_USD",
        "MORPHO_V2_FACTORY",
        "ARB_SYS",
        "CURVE_ADDRESS_PROVIDER",
    ),
)
def test_imperative_launch_address_rejects_unverified_external_facts(key):
    with pytest.raises(ValueError, match=f"RH_EXTERNAL_FACT_UNVERIFIED:{key}"):
        robinhood_launch.address(key)


def test_imperative_launch_address_allows_explicit_semantic_absence():
    assert robinhood_launch.address("UNDERSCORE_REGISTRY") == "0x" + "0" * 40


def test_robinhood_deployment_preflight_rejects_unverified_fact_set():
    unresolved = robinhood_launch.unresolved_external_address_keys()
    assert "USDG" in unresolved
    assert "GOVERNANCE" in unresolved
    assert "CURVE_ADDRESS_PROVIDER" in unresolved
    with pytest.raises(ValueError, match="RH_EXTERNAL_FACTS_UNVERIFIED"):
        robinhood_launch.validate_deployment_external_facts()
