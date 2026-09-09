import pytest


@pytest.fixture(scope="session")
def ripe_hq() -> None:
    """Keep pure clock-model tests independent of protocol deployment."""
