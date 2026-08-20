import pytest

from conf_utils import bind_token_scale, unbind_token_scale


@pytest.fixture(autouse=True)
def _bind_token_scale(price_desk, switchboard_bravo, governance):
    bind_token_scale(price_desk, switchboard_bravo.address, gov=governance.address)
    yield
    unbind_token_scale()
