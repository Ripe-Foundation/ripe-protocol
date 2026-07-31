from __future__ import annotations

import pytest


@pytest.fixture
def offline_mode() -> str:
    return "disabled"
