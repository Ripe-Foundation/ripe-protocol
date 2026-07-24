
pytest_plugins = [
    "conf_core",
    "conf_mock",
    "conf_utils",
    "conf_env",
    # tests/utils is a namespace package; a root utils package would shadow it.
    "utils.clock_profiles",
]
