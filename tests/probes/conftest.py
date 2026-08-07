import pytest


@pytest.fixture(scope="session")
def ripe_hq() -> None:
    """Keep probe-tooling tests independent of protocol deployment."""
