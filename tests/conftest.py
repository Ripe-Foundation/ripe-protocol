
import os

import boa
import pytest

from boa.interpret import set_cache_dir


if boa_cache_dir := os.environ.get("RIPE_BOA_CACHE_DIR"):
    set_cache_dir(boa_cache_dir)


@pytest.fixture(autouse=True)
def isolate_boa_storage_diagnostics():
    """Clear diagnostic traces that Titanoboa does not anchor with EVM state."""

    assert isinstance(boa.env.sstore_trace, dict)
    assert isinstance(boa.env.sha3_trace, dict)
    boa.env.sstore_trace.clear()
    boa.env.sha3_trace.clear()
    yield
    boa.env.sstore_trace.clear()
    boa.env.sha3_trace.clear()


pytest_plugins = [
    "conf_core",
    "conf_mock",
    "conf_utils",
    "conf_env",
    # tests/utils is a namespace package; a root utils package would shadow it.
    "utils.clock_profiles",
]
