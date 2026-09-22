"""Compiler bundle paths and caller state survive detached fork rehearsals."""
import boa
import boa.interpret as interpreter
import pytest
from vyper.exceptions import CompilerPanic

from scripts.base_legacy_compat_fork import isolated_compiler_cache


@pytest.fixture(scope="session")
def ripe_hq():
    """These compiler-only tests require no protocol fixture."""


@pytest.mark.parametrize("fail", [False, True])
def test_rehearsal_cache_isolated_across_paths_and_restored(tmp_path, monkeypatch, fail):
    original = interpreter._disk_cache
    first, second = tmp_path / "first", tmp_path / "second"
    for root in (first, second):
        root.mkdir()
        (root / "Probe.vy").write_text("@external\n@view\ndef value() -> uint256:\n    return 1\n")
    with isolated_compiler_cache():
        shared = interpreter._disk_cache
        monkeypatch.chdir(first)
        before = boa.load_partial("Probe.vy")
        assert before.solc_json["settings"]["search_paths"] == ["."]
        monkeypatch.chdir(second)
        # Reproduce the cross-checkout poisoned bundle without changing source.
        try:
            reused = boa.load_partial("Probe.vy").solc_json
        except CompilerPanic as error:
            assert "Invalid path" in str(error) and str(first) in str(error)
        else:
            assert "Probe.vy" not in reused["sources"]
        try:
            with isolated_compiler_cache():
                fresh = boa.load_partial("Probe.vy")
                assert set(fresh.solc_json["sources"]) == {"Probe.vy"}
                assert fresh.solc_json["settings"] == {"outputSelection": {"Probe.vy": ["*"]}, "search_paths": ["."]}
                assert fresh.compiler_data.bytecode_runtime == before.compiler_data.bytecode_runtime
                if fail:
                    raise RuntimeError("injected exit")
        except RuntimeError as error:
            assert fail and str(error) == "injected exit"
        assert interpreter._disk_cache is shared
    assert interpreter._disk_cache is original
