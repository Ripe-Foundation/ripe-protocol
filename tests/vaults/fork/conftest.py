"""Collection guard for the session-owning SC-04 fork qualification."""

from pathlib import Path

import pytest


SC04_MODULE = Path(__file__).with_name(
    "test_shares_vault_exact_token_qualification.py"
).resolve()


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(items):
    """Reject mixed selected sessions before any expensive fixture deploys."""
    sc04_items = [item for item in items if Path(item.path).resolve() == SC04_MODULE]
    if not sc04_items:
        return

    foreign_items = sorted(
        {
            str(Path(item.path).resolve())
            for item in items
            if Path(item.path).resolve() != SC04_MODULE
        }
    )
    if foreign_items:
        raise pytest.UsageError(
            "SC-04 owns the session fork and must run alone; foreign selected "
            f"tests include {foreign_items[:3]}"
        )
