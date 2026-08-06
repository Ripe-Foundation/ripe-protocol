
import os
from pathlib import Path
import tempfile

import pytest
from boa.environment import Env
from boa.interpret import set_cache_dir


_INSTANT_BOND_COVERAGE_CONFIG = ".coveragerc-instant-bond"
_coverage_cache_tempdir = None


def _isolate_coverage_cache():
    global _coverage_cache_tempdir
    if _coverage_cache_tempdir is None:
        _coverage_cache_tempdir = tempfile.TemporaryDirectory(
            prefix="ripe-boa-coverage.",
        )
        set_cache_dir(_coverage_cache_tempdir.name)


if cache_dir := os.environ.get("RIPE_BOA_CACHE_DIR"):
    set_cache_dir(cache_dir)


@pytest.hookimpl(trylast=True)
def pytest_sessionstart(session):
    # pytest-cov activates coverage after this conftest is imported. Isolate only
    # the dedicated Instant Bond Lane coverage gate so unrelated coverage runs keep
    # their normal cache behavior and configuration.
    cov_config_option = session.config.getoption("cov_config", default=None)
    if cov_config_option is None:
        return

    cov_config = Path(cov_config_option).resolve()
    expected_config = Path(session.config.rootpath, _INSTANT_BOND_COVERAGE_CONFIG)
    if (
        cov_config == expected_config
        and getattr(Env, "_coverage_enabled", False)
    ):
        _isolate_coverage_cache()


pytest_plugins = [
    "conf_core",
    "conf_mock",
    "conf_utils",
    "conf_env",
    # tests/utils is a namespace package; a root utils package would shadow it.
    "utils.clock_profiles",
]
