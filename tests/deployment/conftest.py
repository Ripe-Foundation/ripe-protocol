import pytest


@pytest.fixture(scope="session")
def ripe_hq() -> None:
    """Keep deployment evidence independent of the default protocol graph."""
