import pytest


@pytest.fixture(scope="session")
def ripe_hq() -> None:
    """Keep inventory evidence independent of protocol deployment."""
