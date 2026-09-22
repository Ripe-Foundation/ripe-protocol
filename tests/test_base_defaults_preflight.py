"""Offline regressions for the mandatory, process-isolated Stage 2 preflight."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.utils import defaults_preflight as preflight


@pytest.fixture
def setup_preflight(tmp_path, monkeypatch):
    defaults = tmp_path / "Defaults.vy"
    defaults.write_text("reviewed source")
    monkeypatch.setattr(preflight, "artifact_hashes", lambda path: {str(path): path.read_text()})
    calls = []
    block = {"number": 123, "hash": bytes.fromhex("ab" * 32)}
    def get_block(tag):
        calls.append(tag)
        return block
    class FakeWeb3:
        HTTPProvider = staticmethod(lambda rpc: rpc)
        def __init__(self, provider):
            self.eth = SimpleNamespace(chain_id=8453, get_block=get_block)
    monkeypatch.setattr(preflight, "Web3", FakeWeb3)
    processes = []
    def run(command, **kwargs):
        processes.append((command, kwargs))
        return SimpleNamespace(returncode=0, stdout="verified", stderr="")
    monkeypatch.setattr(preflight.subprocess, "run", run)
    return defaults, calls, processes


def test_uses_same_rpc_fresh_finalized_and_subprocess(setup_preflight):
    defaults, calls, processes = setup_preflight
    checked = preflight.verify_before_deployment(defaults, "https://provider.invalid/secret")
    assert calls == ["finalized", 123]
    command, kwargs = processes[0]
    assert command[-4:] == ["--defaults", str(defaults), "--block-number", "123"]
    assert kwargs["env"]["BASE_MAINNET_RPC_URL"] == "https://provider.invalid/secret"
    assert kwargs["capture_output"] is True
    assert checked.block == 123
    checked.require_unchanged()
    defaults.write_text("unreviewed replacement")
    with pytest.raises(RuntimeError, match="ARTIFACT_CHANGED"):
        checked.require_unchanged()


def test_changed_during_verification_is_rejected(setup_preflight, monkeypatch):
    defaults, _, _ = setup_preflight
    def run(*args, **kwargs):
        defaults.write_text("changed during verification")
        return SimpleNamespace(returncode=0, stdout="", stderr="")
    monkeypatch.setattr(preflight.subprocess, "run", run)
    with pytest.raises(RuntimeError, match="ARTIFACT_CHANGED"):
        preflight.verify_before_deployment(defaults, "https://provider.invalid/secret")


def test_mc_only_scope_is_explicit_and_full_verification_remains_default(setup_preflight):
    defaults, _, processes = setup_preflight
    preflight.verify_before_deployment(defaults, "https://provider.invalid/secret")
    assert "--mission-control-only" not in processes[-1][0]
    preflight.verify_before_deployment(
        defaults, "https://provider.invalid/secret", mission_control_only=True
    )
    assert processes[-1][0][-1] == "--mission-control-only"


def test_failed_verification_redacts_provider(setup_preflight, monkeypatch):
    defaults, _, _ = setup_preflight
    rpc = "https://provider.invalid/SECRET_CREDENTIAL"
    monkeypatch.setattr(preflight.subprocess, "run", lambda *a, **kw:
                        SimpleNamespace(returncode=1, stdout="drift", stderr=rpc))
    with pytest.raises(RuntimeError, match="PREFLIGHT_FAILED") as exc:
        preflight.verify_before_deployment(defaults, rpc)
    assert "SECRET_CREDENTIAL" not in str(exc.value)


def test_historical_pin_only_for_rehearsal(setup_preflight):
    defaults, calls, _ = setup_preflight
    preflight.verify_before_deployment(defaults, "https://provider.invalid", rehearsal_block=123)
    assert calls == [123, 123]


def test_stage_two_preflight_failure_precedes_first_deployment():
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("stage2", root /
        "migrations/archive/base-mainnet/2026091401_StageBaseMissionControl.py")
    stage = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(stage)
    deployments = []
    def fail():
        raise RuntimeError("BASE_DEFAULTS_PREFLIGHT_FAILED")
    migration = SimpleNamespace(
        chain=lambda: "base-mainnet",
        get_contract=lambda *args: SimpleNamespace(getAddr=lambda slot: "0x" + "1" * 40),
        verify_base_defaults=fail,
        deploy=lambda *a, **kw: deployments.append(a),
        deploy_bp=lambda *a, **kw: deployments.append(a),
    )
    with pytest.raises(RuntimeError, match="PREFLIGHT_FAILED"):
        stage.migrate(migration)
    assert deployments == []
