import pytest

from conf_utils import bind_token_scale, unbind_token_scale


@pytest.fixture(autouse=True)
def _bind_token_scale(price_desk, switchboard_bravo):
    bind_token_scale(price_desk, switchboard_bravo.address)
    yield
    unbind_token_scale()
