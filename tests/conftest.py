
import os
import tempfile

import pytest
from boa.environment import Env
from boa.interpret import set_cache_dir


_coverage_cache_isolated = False


def _isolate_coverage_cache():
    global _coverage_cache_isolated
    if not _coverage_cache_isolated:
        cache_dir = tempfile.mkdtemp(
            prefix="instant-bond-coverage-boa.",
            dir="/private/tmp",
        )
        set_cache_dir(cache_dir)
        _coverage_cache_isolated = True


if Env._coverage_enabled:
    # Boa's disk cache stores compiler artifacts whose tracing state depends on
    # whether coverage was active. A unique empty cache preserves Boa source-map
    # materialization without reusing uninstrumented artifacts.
    _isolate_coverage_cache()
elif cache_dir := os.environ.get("RIPE_INSTANT_BOND_BOA_CACHE"):
    set_cache_dir(cache_dir)


@pytest.hookimpl(trylast=True)
def pytest_sessionstart(session):
    # pytest-cov activates coverage after this conftest is imported but before the
    # test session starts. Re-check here so a warm cache can never supply
    # uninstrumented compiler data to coverage-enabled fixture deployments.
    if Env._coverage_enabled:
        _isolate_coverage_cache()


pytest_plugins = [
    "conf_core",
    "conf_mock",
    "conf_utils",
    "conf_env",
]
