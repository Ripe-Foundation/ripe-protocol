"""Fail-closed G4 inventory for Vault getter consumers."""

import hashlib
import json
import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
INVENTORY_PATH = (
    ROOT / "docs/chains/rh/hardening/basic-vault-consumer-inventory.md"
)
BEGIN = "<!-- BASIC_VAULT_CONSUMER_INVENTORY_BEGIN -->"
END = "<!-- BASIC_VAULT_CONSUMER_INVENTORY_END -->"
FUNCTION_RE = re.compile(r"^def ([A-Za-z_][A-Za-z0-9_]*)\(", re.MULTILINE)

BACKING_AWARE_GETTERS = {
    "getTotalAmountForUser",
    "getUserAssetAndAmountAtIndex",
}
POSITION_DISCOVERY_GETTERS = {
    "doesUserHaveBalance",
    "getUserAssetAtIndexAndHasBalance",
    "numUserAssets",
    "userAssets",
}
QUARANTINE_STATUS_GETTERS = {"getTotalAmountForVault"}
REWARD_GETTERS = {"getTotalAmountForVault", "getUserLootBoxShare"}
CAPABILITY_GETTERS = {"isSupportedVaultAsset"}


@pytest.fixture(scope="session")
def ripe_hq() -> None:
    """Keep source inventory checks independent of protocol deployment."""


def _load_inventory():
    text = INVENTORY_PATH.read_text()
    assert text.count(BEGIN) == 1
    assert text.count(END) == 1
    payload = text.split(BEGIN, 1)[1].split(END, 1)[0].strip()
    assert payload.startswith("```json\n")
    assert payload.endswith("\n```")
    return json.loads(payload.removeprefix("```json\n").removesuffix("\n```"))


def _function_at(source, offset):
    functions = [
        (match.start(), match.group(1))
        for match in FUNCTION_RE.finditer(source)
        if match.start() < offset
    ]
    assert functions
    return functions[-1][1]


def _scan_calls(path, getters):
    source = path.read_text()
    getter_pattern = "|".join(re.escape(getter) for getter in sorted(getters))
    call_re = re.compile(
        rf"\bVault\([^)\n]+\)\.(?P<getter>{getter_pattern})\("
    )
    return [
        {
            "path": str(path.relative_to(ROOT)),
            "line": source.count("\n", 0, match.start()) + 1,
            "function": _function_at(source, match.start()),
            "getter": match.group("getter"),
        }
        for match in call_re.finditer(source)
    ]


def test_basic_vault_consumer_inventory_matches_reviewed_sources():
    inventory = _load_inventory()
    assert inventory["schema"] == 1
    assert inventory["baseline"] == "1e36c0c3dd168dbf292456eb5760b02d1f1e4a80"

    actual_rows = []
    actual_sources = {}
    for path in sorted((ROOT / "contracts").rglob("*.vy")):
        rows = _scan_calls(path, inventory["getter_scope"])
        if not rows:
            continue
        relative_path = str(path.relative_to(ROOT))
        actual_sources[relative_path] = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        actual_rows.extend(rows)

    # Discover callers across the complete production-contract tree first;
    # a new consumer cannot evade review merely by living outside a frozen
    # source allowlist.
    assert actual_sources == inventory["sources"]

    expected_rows = [
        {
            "path": row["path"],
            "line": row["line"],
            "function": row["function"],
            "getter": row["getter"],
        }
        for row in inventory["rows"]
    ]
    assert actual_rows == expected_rows
    assert len({row["id"] for row in inventory["rows"]}) == len(
        inventory["rows"]
    )
    assert {row["path"] for row in inventory["rows"]} == set(
        inventory["sources"]
    )


def test_auction_house_basic_vault_consumer_rows_are_current():
    """Enforce the changed consumer independently of unrelated inventory drift."""
    inventory = _load_inventory()
    relative_path = "contracts/core/AuctionHouse.vy"
    path = ROOT / relative_path

    assert hashlib.sha256(path.read_bytes()).hexdigest() == (
        inventory["sources"][relative_path]
    )
    actual_rows = _scan_calls(path, inventory["getter_scope"])
    expected_rows = [
        {
            "path": row["path"],
            "line": row["line"],
            "function": row["function"],
            "getter": row["getter"],
        }
        for row in inventory["rows"]
        if row["path"] == relative_path
    ]
    assert actual_rows == expected_rows


def test_basic_vault_consumer_inventory_enforces_amount_policy():
    inventory = _load_inventory()
    category_getters = {
        "value_backing_required": BACKING_AWARE_GETTERS,
        "position_discovery_nominal_allowed": POSITION_DISCOVERY_GETTERS,
        "quarantine_status_backing_required": QUARANTINE_STATUS_GETTERS,
        "reward_accounting_backing_aware": REWARD_GETTERS,
        "capability_discovery_nominal_allowed": CAPABILITY_GETTERS,
    }
    assert set(inventory["getter_scope"]) == set().union(
        *category_getters.values()
    )

    for row in inventory["rows"]:
        assert row["classification"] in category_getters
        assert row["getter"] in category_getters[row["classification"]]
        assert row["reason"].strip()
        assert row["evidence_test"].startswith("test_")

    test_sources = [
        path.read_text()
        for path in (ROOT / "tests").rglob("*.py")
    ]
    for evidence_test in {row["evidence_test"] for row in inventory["rows"]}:
        assert any(
            f"def {evidence_test}(" in source
            for source in test_sources
        )

    backing_aware_paths = {
        (row["path"], row["line"])
        for row in inventory["rows"]
        if row["classification"]
        in {"value_backing_required", "quarantine_status_backing_required"}
    }
    assert backing_aware_paths == {
        ("contracts/core/AuctionHouse.vy", 439),
        ("contracts/core/AuctionHouse.vy", 535),
        ("contracts/core/AuctionHouse.vy", 913),
        ("contracts/core/AuctionHouse.vy", 1265),
        ("contracts/core/AuctionHouse.vy", 1293),
        ("contracts/core/CreditEngine.vy", 736),
        ("contracts/core/CreditEngine.vy", 753),
        ("contracts/core/CreditEngine.vy", 1256),
        ("contracts/core/CreditRedeem.vy", 191),
        ("contracts/core/Deleverage.vy", 563),
        ("contracts/core/Deleverage.vy", 1070),
        ("contracts/core/Teller.vy", 410),
        ("contracts/core/VaultMigrator.vy", 472),
        ("contracts/core/VaultMigrator.vy", 523),
    }
