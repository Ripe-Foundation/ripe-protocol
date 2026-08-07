
import os

from boa.interpret import set_cache_dir


if boa_cache_dir := os.environ.get("RIPE_BOA_CACHE_DIR"):
    set_cache_dir(boa_cache_dir)


pytest_plugins = [
    "conf_core",
    "conf_mock",
    "conf_utils",
    "conf_env",
    # tests/utils is a namespace package; a root utils package would shadow it.
    "utils.clock_profiles",
]
