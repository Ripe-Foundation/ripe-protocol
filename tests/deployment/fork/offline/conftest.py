from __future__ import annotations

import pytest


@pytest.fixture
def offline_mode() -> str:
    return "disabled"


@pytest.fixture
def safe_default_deselection_reason(fork_framework) -> str:
    return fork_framework.SAFE_DEFAULT_DESELECTION_REASON
