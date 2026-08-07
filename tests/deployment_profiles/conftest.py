import pytest


@pytest.fixture(scope="session")
def ripe_hq() -> None:
    """Keep deployment-profile evidence independent of protocol deployment."""
