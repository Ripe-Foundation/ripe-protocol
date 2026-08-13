import pytest


@pytest.fixture(scope="session")
def ripe_hq() -> None:
    """Keep this focused subtree independent of the protocol bootstrap."""
