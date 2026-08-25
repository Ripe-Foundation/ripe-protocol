from __future__ import annotations

import copy
import json
from pathlib import Path, PurePosixPath
from types import SimpleNamespace

import boa
import pytest
import vyper
from eth_abi.abi import encode

import scripts.utils.migration as migration_module
from scripts.utils.migration import Migration, PromotionSpec
from scripts.utils.migration_helpers import (
    NO_OUTPUT_TRANSACTION_RESULT,
    TransactionExecutionError,
    execute_transaction,
)
from scripts.utils.migration_runner import MigrationRunner


def _args(*, ignore_logs: bool = False):
    return SimpleNamespace(
        ignore_logs=ignore_logs,
        rpc="redacted",
        sender=SimpleNamespace(address="0x" + "1" * 40),
        chain="robinhood-mainnet",
        blueprint=None,
    )


def _write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value))


def _source(constructor_inputs=()) -> str:
    parameters = ", ".join(
        f"_{name}: {abi_type}" for name, abi_type in constructor_inputs
    )
    constructor = ""
    if constructor_inputs:
        constructor = f"\n@deploy\ndef __init__({parameters}):\n    pass\n"
    return (
        "# pragma version ~=0.4.3\n"
        f"{constructor}\n"
        "@external\n"
        "@view\n"
        "def marker() -> uint256:\n"
        "    return 1\n"
    )


_DEPLOYED_CODE = {}


def _promotable_record(
    tmp_path: Path,
    source_path: str,
    address: str,
    *,
    constructor_inputs=(),
    constructor_values=(),
) -> dict:
    content = _source(constructor_inputs)
    local_source = tmp_path / source_path
    local_source.parent.mkdir(parents=True, exist_ok=True)
    local_source.write_text(content)
    compiled = vyper.compile_code(
        content,
        contract_path=PurePosixPath(source_path),
        output_formats=["integrity", "abi", "bytecode_runtime", "layout"],
    )
    input_types = [abi_type for _name, abi_type in constructor_inputs]
    record = {
        "address": address,
        "file": source_path,
        "abi": compiled["abi"],
        "args": encode(input_types, constructor_values).hex() if input_types else "",
        "solc_json": {
            "language": "Vyper",
            "sources": {source_path: {"content": content}},
            "settings": {
                "outputSelection": {source_path: ["*"]},
                "search_paths": ["."],
            },
            "compiler_version": f"v{vyper.__long_version__}",
            "integrity": compiled["integrity"],
        },
    }
    code_layout = compiled["layout"].get("code_layout", {})
    code_data_size = migration_module._code_data_size(code_layout)
    _DEPLOYED_CODE[address.lower()] = bytes.fromhex(
        compiled["bytecode_runtime"].removeprefix("0x")
    ) + bytes(code_data_size)
    return record


@pytest.fixture(autouse=True)
def _bind_promotable_sources_to_test_repository(tmp_path, monkeypatch):
    monkeypatch.setattr(migration_module, "_REPOSITORY_ROOT", tmp_path)
    _DEPLOYED_CODE.clear()


def _migration(
    tmp_path: Path,
    *,
    timestamp: str = "2",
    files=None,
) -> Migration:
    migration = Migration(
        _args(),
        files or {},
        timestamp,
        "1",
        str(tmp_path),
    )
    migration._get_deployed_code = lambda address: _DEPLOYED_CODE.get(
        str(address).lower(), b""
    )
    return migration


def _promotion(
    migration,
    canonical_name,
    candidate_label,
    registry,
    registry_id=7,
    *,
    registry_name="Registry",
    expected_constructor_args=(),
    activation_candidate_label=None,
    activation_dependency_arg_index=None,
    activation_expected_constructor_args=None,
):
    candidate = migration._previous_manifest["contracts"][candidate_label]
    migration._files.setdefault(canonical_name, candidate["file"])
    migration._previous_manifest["contracts"].setdefault(
        registry_name,
        {"address": registry.address},
    )
    return PromotionSpec(
        canonical_name=canonical_name,
        expected_source_path=candidate["file"],
        candidate_label=candidate_label,
        registry_name=registry_name,
        registry=registry,
        registry_id=registry_id,
        expected_constructor_args=expected_constructor_args,
        activation_candidate_label=activation_candidate_label,
        activation_dependency_arg_index=activation_dependency_arg_index,
        activation_expected_constructor_args=(activation_expected_constructor_args),
    )


class _AbiCallable:
    def __init__(self, outputs, result=None, error=None):
        self._abi = {
            "type": "function",
            "name": "synthetic",
            "inputs": [],
            "outputs": outputs,
        }
        self._result = result
        self._error = error
        self.calls = 0

    def __call__(self):
        self.calls += 1
        if self._error is not None:
            raise self._error
        return self._result


class _Registry:
    def __init__(self, address: str, registry_id: int = 7):
        self.address = address
        self.registry_id = registry_id

    def getAddr(self, registry_id: int) -> str:
        assert registry_id == self.registry_id
        return self.address


def test_vyper_zero_output_success_is_durably_logged_and_resumable(tmp_path):
    contract = boa.loads(
        """
stored: public(uint256)

@external
def set_stored(new_value: uint256):
    self.stored = new_value
"""
    )
    deploy_args = SimpleNamespace(
        ignore_logs=False,
        rpc="redacted",
        chain="robinhood-mainnet",
        sender=SimpleNamespace(address=boa.env.eoa),
    )

    migration = Migration(deploy_args, {}, "2", "1", str(tmp_path))
    result = migration.execute(contract.set_stored, 41)

    assert result == NO_OUTPUT_TRANSACTION_RESULT
    assert result
    assert contract.stored() == 41
    record = json.loads((tmp_path / "2-log.json").read_text())["transactions"][0]
    assert record == {
        **migration._transaction_intent(contract.set_stored, (41,), {}),
        "receipt": NO_OUTPUT_TRANSACTION_RESULT,
    }

    resumed = Migration(deploy_args, {}, "2", "1", str(tmp_path))
    assert resumed.execute(contract.set_stored, 41) == NO_OUTPUT_TRANSACTION_RESULT
    assert contract.stored() == 41

    changed = Migration(deploy_args, {}, "2", "1", str(tmp_path))
    with pytest.raises(
        RuntimeError,
        match="MIGRATION_TRANSACTION_CALLDATA_MISMATCH",
    ):
        changed.execute(contract.set_stored, 99)


@pytest.mark.parametrize("explicit_amount", (False, True))
def test_vyper_default_argument_zero_output_is_logged_once_and_resumable(
    tmp_path,
    explicit_amount,
):
    contract = boa.loads(
        """
count: public(uint256)

@external
def bump(amount: uint256 = 1):
    self.count += amount
"""
    )
    deploy_args = SimpleNamespace(
        ignore_logs=False,
        rpc="redacted",
        chain="robinhood-mainnet",
        sender=SimpleNamespace(address=boa.env.eoa),
    )
    call_args = (7,) if explicit_amount else ()
    expected = 7 if explicit_amount else 1

    migration = Migration(deploy_args, {}, "2", "1", str(tmp_path))
    result = migration.execute(contract.bump, *call_args)

    assert result == NO_OUTPUT_TRANSACTION_RESULT
    assert contract.count() == expected
    record = json.loads((tmp_path / "2-log.json").read_text())["transactions"][0]
    assert record == {
        **migration._transaction_intent(contract.bump, call_args, {}),
        "receipt": NO_OUTPUT_TRANSACTION_RESULT,
    }

    resumed = Migration(deploy_args, {}, "2", "1", str(tmp_path))
    assert resumed.execute(contract.bump, *call_args) == NO_OUTPUT_TRANSACTION_RESULT
    assert contract.count() == expected


def test_abi_none_requires_explicit_zero_outputs():
    no_output_transaction = _AbiCallable([])
    assert (
        execute_transaction(no_output_transaction, no_retry=True)
        == NO_OUTPUT_TRANSACTION_RESULT
    )
    assert no_output_transaction.calls == 1

    transaction = _AbiCallable([{"name": "", "type": "uint256"}])

    with pytest.raises(
        TransactionExecutionError, match="MIGRATION_TRANSACTION_RESULT_MISSING"
    ):
        execute_transaction(transaction, max_attempts=20)

    assert transaction.calls == 1


def test_raised_zero_output_function_remains_fail_closed():
    transaction = _AbiCallable([], error=RuntimeError("synthetic failure"))

    with pytest.raises(TransactionExecutionError, match="MIGRATION_TRANSACTION_FAILED"):
        execute_transaction(transaction, no_retry=True)

    assert transaction.calls == 1


class _ReconciledCall:
    def __init__(self, callback):
        self.contract = SimpleNamespace(address="0x" + "2" * 40)
        self._callback = callback

    def prepare_calldata(self):
        return b"\x12\x34"

    def __call__(self, **_kwargs):
        return self._callback()


def test_execute_reconciled_records_only_a_proven_frontier_call(tmp_path):
    _write_json(tmp_path / "current-manifest.json", {"contracts": {}})
    migration = Migration(_args(), {}, "2", "1", str(tmp_path))
    calls = []
    transaction = _ReconciledCall(lambda: calls.append("broadcast"))

    result = migration.execute_reconciled(
        transaction,
        lambda: True,
    )

    assert result is True
    assert calls == []
    assert migration._count == 1
    expected = {
        **migration._transaction_intent(transaction, (), {}),
        "receipt": True,
    }
    assert migration._transactions == [expected]
    saved = json.loads((tmp_path / "2-log.json").read_text())
    assert saved == {"transactions": [expected]}


def test_execute_reconciled_recovers_mined_success_from_driver_error(tmp_path):
    _write_json(tmp_path / "current-manifest.json", {"contracts": {}})
    migration = Migration(_args(), {}, "2", "1", str(tmp_path))
    state = {"complete": False}

    def mined_then_driver_failed(**_kwargs):
        state["complete"] = True
        raise RuntimeError("synthetic post-receipt failure")

    transaction = _ReconciledCall(mined_then_driver_failed)
    assert migration.execute_reconciled(
        transaction,
        lambda: state["complete"],
    )
    assert migration._count == 1
    assert migration._transactions == [
        {
            **migration._transaction_intent(transaction, (), {}),
            "receipt": True,
        }
    ]


def test_execute_reconciled_keeps_real_failure_closed(tmp_path):
    _write_json(tmp_path / "current-manifest.json", {"contracts": {}})
    migration = Migration(_args(), {}, "2", "1", str(tmp_path))
    transaction = _ReconciledCall(
        lambda: (_ for _ in ()).throw(RuntimeError("real failure"))
    )

    with pytest.raises(TransactionExecutionError):
        migration.execute_reconciled(
            transaction,
            lambda: False,
        )

    assert migration._transactions == []


@pytest.mark.parametrize("deployment_kind", ("standard", "blueprint"))
def test_deployment_resume_preserves_recorded_manifest_metadata_byte_for_byte(
    tmp_path,
    monkeypatch,
    deployment_kind,
):
    address = "0x" + "2" * 40
    intended_owner = "0x" + "3" * 40
    if deployment_kind == "standard":
        name = "Service"
        label = "ServiceCandidate"
        source_path = "contracts/Service.vy"
        record = _promotable_record(
            tmp_path,
            source_path,
            address,
            constructor_inputs=(("owner", "address"),),
            constructor_values=(intended_owner,),
        )
        deploy_args = (intended_owner,)
    else:
        name = label = "Contributor"
        source_path = "contracts/modules/Contributor.vy"
        # Existing Contributor blueprints have a constructor-bearing ABI but
        # no constructor args because the record describes blueprint creation,
        # not an instance. Resume must preserve that historical record; the
        # stricter validator applies only to candidate promotion records.
        record = _promotable_record(
            tmp_path,
            source_path,
            address,
            constructor_inputs=(("owner", "address"),),
            constructor_values=(intended_owner,),
        )
        record["args"] = ""
        deploy_args = ()
    record["future_field"] = {"must": ["survive"]}

    current = {
        "contracts": {
            label: {
                "address": "0x" + "1" * 40,
                "stale_field": "must not return",
            }
        }
    }
    pending = {"contracts": {label: record}}
    _write_json(tmp_path / "current-manifest.json", current)
    _write_json(tmp_path / "2-pending-manifest.json", pending)
    _write_json(tmp_path / "2-log.json", {"transactions": [address]})
    pending_before = (tmp_path / "2-pending-manifest.json").read_bytes()
    current_before = (tmp_path / "current-manifest.json").read_bytes()

    migration = Migration(
        _args(),
        {name: source_path},
        "2",
        "1",
        str(tmp_path),
    )
    recorded = SimpleNamespace(address=address)
    monkeypatch.setattr(
        migration,
        "get_contract",
        lambda requested: recorded if requested == label else None,
    )
    if deployment_kind == "standard":
        resumed_code = _DEPLOYED_CODE[address.lower()]
    else:
        compiled = migration_module._compile_authenticated_record(
            record,
            expected_source_path=source_path,
        )
        creation_hex = compiled["evm"]["bytecode"]["object"]
        resumed_code = b"\xfe\x71\x00" + bytes.fromhex(creation_hex.removeprefix("0x"))
    monkeypatch.setattr(
        migration,
        "_get_deployed_code",
        lambda _address: resumed_code,
    )

    if deployment_kind == "standard":
        resumed = migration.deploy(
            name,
            *deploy_args,
            label=label,
        )
    else:
        resumed = migration.deploy_bp(name)

    assert resumed is recorded
    assert migration._count == 1
    assert migration._previous_manifest["contracts"][label] == record
    assert label not in migration._contract_files
    assert label not in migration._args
    assert (tmp_path / "2-pending-manifest.json").read_bytes() == pending_before
    assert (tmp_path / "current-manifest.json").read_bytes() == current_before


@pytest.mark.parametrize("deployment_kind", ("standard", "blueprint"))
def test_deployment_resume_rejects_missing_deployed_code(
    tmp_path,
    monkeypatch,
    deployment_kind,
):
    address = "0x" + "2" * 40
    if deployment_kind == "standard":
        name = "Service"
        label = "ServiceCandidate"
        source_path = "contracts/Service.vy"
    else:
        name = label = "Contributor"
        source_path = "contracts/modules/Contributor.vy"
    record = _promotable_record(tmp_path, source_path, address)
    _write_json(tmp_path / "current-manifest.json", {"contracts": {}})
    _write_json(
        tmp_path / "2-pending-manifest.json",
        {"contracts": {label: record}},
    )
    _write_json(tmp_path / "2-log.json", {"transactions": [address]})
    migration = Migration(
        _args(),
        {name: source_path},
        "2",
        "1",
        str(tmp_path),
    )
    monkeypatch.setattr(
        migration,
        "get_contract",
        lambda _label: SimpleNamespace(address=address),
    )
    monkeypatch.setattr(migration, "_get_deployed_code", lambda _address: b"")
    error = (
        "MIGRATION_CANDIDATE_DEPLOYED_CODE_MISSING"
        if deployment_kind == "standard"
        else "MIGRATION_RESUMED_BLUEPRINT_CODE_MISSING"
    )

    with pytest.raises(RuntimeError, match=error):
        if deployment_kind == "standard":
            migration.deploy(name, label=label)
        else:
            migration.deploy_bp(name)


def test_deployment_resume_rejects_log_manifest_address_mismatch(
    tmp_path,
    monkeypatch,
):
    recorded_address = "0x" + "2" * 40
    logged_address = "0x" + "4" * 40
    source_path = "contracts/Service.vy"
    owner = "0x" + "3" * 40
    record = _promotable_record(
        tmp_path,
        source_path,
        recorded_address,
        constructor_inputs=(("owner", "address"),),
        constructor_values=(owner,),
    )
    _write_json(tmp_path / "current-manifest.json", {"contracts": {}})
    _write_json(
        tmp_path / "2-pending-manifest.json",
        {"contracts": {"ServiceCandidate": record}},
    )
    _write_json(
        tmp_path / "2-log.json",
        {"transactions": [logged_address]},
    )
    migration = Migration(
        _args(),
        {"Service": source_path},
        "2",
        "1",
        str(tmp_path),
    )
    monkeypatch.setattr(
        migration,
        "get_contract",
        lambda _label: SimpleNamespace(address=recorded_address),
    )

    with pytest.raises(
        RuntimeError,
        match="MIGRATION_RESUMED_CONTRACT_LOG_ADDRESS_MISMATCH",
    ):
        migration.deploy("Service", owner, label="ServiceCandidate")


def test_deployment_resume_accepts_legacy_vyper_contract_log(
    tmp_path,
    monkeypatch,
):
    address = "0x" + "2" * 40
    source_path = "contracts/Service.vy"
    record = _promotable_record(tmp_path, source_path, address)
    _write_json(tmp_path / "current-manifest.json", {"contracts": {}})
    _write_json(
        tmp_path / "2-pending-manifest.json",
        {"contracts": {"ServiceCandidate": record}},
    )
    legacy = f"<contracts/Service.vy at {address}, compiled with vyper-0.4.3>"
    _write_json(tmp_path / "2-log.json", {"transactions": [legacy]})
    migration = Migration(
        _args(),
        {"Service": source_path},
        "2",
        "1",
        str(tmp_path),
    )
    attached = SimpleNamespace(address=address)
    monkeypatch.setattr(migration, "get_contract", lambda _label: attached)
    monkeypatch.setattr(
        migration,
        "_get_deployed_code",
        lambda _address: _DEPLOYED_CODE[address.lower()],
    )

    assert migration.deploy("Service", label="ServiceCandidate") is attached


def test_blueprint_resume_accepts_legacy_object_log_after_code_validation(
    tmp_path,
    monkeypatch,
):
    address = "0x" + "2" * 40
    name = "Contributor"
    source_path = "contracts/modules/Contributor.vy"
    record = _promotable_record(tmp_path, source_path, address)
    record["args"] = ""
    _write_json(tmp_path / "current-manifest.json", {"contracts": {}})
    _write_json(
        tmp_path / "2-pending-manifest.json",
        {"contracts": {name: record}},
    )
    legacy = (
        "<boa.contracts.vyper.vyper_contract.VyperBlueprint object at 0x125af33e0>"
    )
    _write_json(tmp_path / "2-log.json", {"transactions": [legacy]})
    migration = Migration(
        _args(),
        {name: source_path},
        "2",
        "1",
        str(tmp_path),
    )
    attached = SimpleNamespace(address=address)
    monkeypatch.setattr(migration, "get_contract", lambda _label: attached)
    compiled = migration_module._compile_authenticated_record(
        record,
        expected_source_path=source_path,
    )
    creation_hex = compiled["evm"]["bytecode"]["object"]
    expected_code = b"\xfe\x71\x00" + bytes.fromhex(creation_hex.removeprefix("0x"))
    monkeypatch.setattr(migration, "_get_deployed_code", lambda _address: expected_code)

    assert migration.deploy_bp(name) is attached


@pytest.mark.parametrize("drift", ("constructor", "source"))
def test_deployment_resume_rejects_current_intent_drift(
    tmp_path,
    monkeypatch,
    drift,
):
    address = "0x" + "2" * 40
    source_path = "contracts/Service.vy"
    owner = "0x" + "3" * 40
    record = _promotable_record(
        tmp_path,
        source_path,
        address,
        constructor_inputs=(("owner", "address"),),
        constructor_values=(owner,),
    )
    _write_json(tmp_path / "current-manifest.json", {"contracts": {}})
    _write_json(
        tmp_path / "2-pending-manifest.json",
        {"contracts": {"ServiceCandidate": record}},
    )
    _write_json(tmp_path / "2-log.json", {"transactions": [address]})
    if drift == "source":
        (tmp_path / source_path).write_text(
            _source((("owner", "address"),)) + "\n# drift\n"
        )
    migration = Migration(
        _args(),
        {"Service": source_path},
        "2",
        "1",
        str(tmp_path),
    )
    monkeypatch.setattr(
        migration,
        "get_contract",
        lambda _label: SimpleNamespace(address=address),
    )
    intended = "0x" + "5" * 40 if drift == "constructor" else owner
    error = "INTENT_MISMATCH" if drift == "constructor" else "SOURCE_MISMATCH"

    with pytest.raises(RuntimeError, match=error):
        migration.deploy("Service", intended, label="ServiceCandidate")


def test_deployment_stays_pending_until_migration_end(tmp_path, monkeypatch):
    active = {"contracts": {"Service": {"address": "0x" + "1" * 40, "file": "old.vy"}}}
    _write_json(tmp_path / "current-manifest.json", active)
    _write_json(tmp_path / "1-manifest.json", active)

    def manifest(contracts, contract_files, args, files):
        return {
            "contracts": {
                name: {"address": value, "file": "new.vy"}
                for name, value in contracts.items()
            }
        }

    monkeypatch.setattr(migration_module, "deployed_contracts_manifest", manifest)
    migration = _migration(tmp_path)
    migration._contracts["Service"] = "0x" + "2" * 40
    migration._append_manifest("Service")

    assert json.loads((tmp_path / "current-manifest.json").read_text()) == active
    assert not (tmp_path / "2-manifest.json").exists()
    pending = json.loads((tmp_path / "2-pending-manifest.json").read_text())
    assert pending["contracts"]["Service"]["address"] == "0x" + "2" * 40

    migration.end()

    assert not (tmp_path / "2-pending-manifest.json").exists()
    assert json.loads((tmp_path / "2-manifest.json").read_text()) == pending
    assert json.loads((tmp_path / "current-manifest.json").read_text()) == pending


def test_candidate_promotion_copies_complete_record_after_registry_readback(
    tmp_path,
):
    old = {
        "address": "0x" + "1" * 40,
        "file": "old.vy",
        "abi": [{"name": "old"}],
        "args": ["stale"],
        "old_only": True,
    }
    candidate = _promotable_record(
        tmp_path,
        "Service.vy",
        "0x" + "2" * 40,
    )
    candidate["future_field"] = {"preserve": [1, 2, 3]}
    active = {
        "contracts": {
            "Service": old,
            "ServiceCandidate": candidate,
            "OldCandidate2026082100": {
                "address": "0x" + "9" * 40,
                "file": "historical.vy",
            },
        }
    }
    _write_json(tmp_path / "current-manifest.json", active)
    _write_json(tmp_path / "1-manifest.json", active)

    migration = _migration(tmp_path)
    registry = _Registry(candidate["address"])
    migration._files["Service"] = candidate["file"]
    migration._previous_manifest["contracts"]["Registry"] = {
        "address": registry.address
    }
    promoted = migration.promote_candidate(
        "Service",
        "ServiceCandidate",
        registry,
        7,
        expected_source_path="Service.vy",
        registry_name="Registry",
        expected_constructor_args=(),
    )

    assert promoted == candidate["address"]
    pending = json.loads((tmp_path / "2-pending-manifest.json").read_text())
    assert pending["contracts"]["Service"] == candidate
    assert "ServiceCandidate" not in pending["contracts"]
    assert "OldCandidate2026082100" not in pending["contracts"]
    assert "old_only" not in pending["contracts"]["Service"]
    assert json.loads((tmp_path / "current-manifest.json").read_text()) == active

    migration.end()
    assert json.loads((tmp_path / "current-manifest.json").read_text()) == pending
    assert json.loads((tmp_path / "1-manifest.json").read_text()) == active
    # The step manifest attributes only what this migration promoted -
    # "Service" (this step's canonical name) - not "ServiceCandidate", which
    # was already deployed and recorded in an earlier step. And per the
    # step-manifest schema, only address/file survive: not abi/args/
    # old_only/future_field.
    step = json.loads((tmp_path / "2-manifest.json").read_text())
    assert step == {
        "contracts": {
            "Service": {
                "address": candidate["address"],
                "file": candidate["file"],
            }
        }
    }


def test_candidate_promotion_mismatch_is_write_free(tmp_path):
    candidate = _promotable_record(
        tmp_path,
        "Service.vy",
        "0x" + "2" * 40,
    )
    active = {
        "contracts": {
            "Service": {
                "address": "0x" + "1" * 40,
                "file": "old.vy",
            },
            "ServiceCandidate": candidate,
        }
    }
    _write_json(tmp_path / "current-manifest.json", active)
    _write_json(tmp_path / "1-manifest.json", active)
    _write_json(tmp_path / "2-manifest.json", {"sentinel": True})
    current_before = (tmp_path / "current-manifest.json").read_bytes()
    timestamp_before = (tmp_path / "2-manifest.json").read_bytes()

    migration = _migration(tmp_path)
    registry = _Registry("0x" + "3" * 40)
    spec = _promotion(
        migration,
        "Service",
        "ServiceCandidate",
        registry,
    )
    with pytest.raises(RuntimeError, match="MIGRATION_CANDIDATE_REGISTRY_MISMATCH"):
        migration.promote_candidates([spec])

    assert (tmp_path / "current-manifest.json").read_bytes() == current_before
    assert (tmp_path / "2-manifest.json").read_bytes() == timestamp_before
    assert not (tmp_path / "2-pending-manifest.json").exists()


def test_candidate_promotion_rejects_incomplete_record_before_readback(
    tmp_path,
):
    active = {
        "contracts": {
            "ServiceCandidate": {
                "address": "0x" + "2" * 40,
                "file": "Service.vy",
                "abi": [{"type": "function", "name": "new"}],
                # Missing the compiler record and encoded constructor args.
            }
        }
    }
    _write_json(tmp_path / "current-manifest.json", active)
    _write_json(tmp_path / "1-manifest.json", active)
    migration = _migration(tmp_path)
    registry = _Registry("0x" + "2" * 40)
    migration._files["Service"] = "Service.vy"
    migration._previous_manifest["contracts"]["Registry"] = {
        "address": registry.address
    }

    with pytest.raises(RuntimeError, match="MIGRATION_CANDIDATE_RECORD_INCOMPLETE"):
        migration.promote_candidate(
            "Service",
            "ServiceCandidate",
            registry,
            7,
            expected_source_path="Service.vy",
            registry_name="Registry",
            expected_constructor_args=(),
        )

    assert not (tmp_path / "2-pending-manifest.json").exists()


def test_candidate_promotion_accepts_distinct_activation_witness(tmp_path):
    defaults = _promotable_record(
        tmp_path,
        "contracts/config/DefaultsRobinhoodLive.vy",
        "0x" + "2" * 40,
    )
    hq = "0x" + "4" * 40
    mission_control = _promotable_record(
        tmp_path,
        "contracts/data/MissionControl.vy",
        "0x" + "3" * 40,
        constructor_inputs=(
            ("ripeHq", "address"),
            ("defaults", "address"),
        ),
        constructor_values=(hq, defaults["address"]),
    )
    active = {
        "contracts": {
            "DefaultsRobinhoodLive": {
                "address": "0x" + "1" * 40,
                "file": "old.vy",
            },
            "DefaultsCandidate": defaults,
            "MissionControlCandidate": mission_control,
        }
    }
    _write_json(tmp_path / "current-manifest.json", active)
    _write_json(tmp_path / "1-manifest.json", active)

    migration = _migration(tmp_path)
    registry = _Registry(mission_control["address"], 5)
    migration._files["DefaultsRobinhoodLive"] = defaults["file"]
    migration._previous_manifest["contracts"]["RipeHq"] = {"address": registry.address}
    migration.promote_candidate(
        "DefaultsRobinhoodLive",
        "DefaultsCandidate",
        registry,
        5,
        expected_source_path=defaults["file"],
        registry_name="RipeHq",
        expected_constructor_args=(),
        activation_candidate_label="MissionControlCandidate",
        activation_dependency_arg_index=1,
        activation_expected_constructor_args=(hq, defaults["address"]),
    )

    pending = json.loads((tmp_path / "2-pending-manifest.json").read_text())
    assert pending["contracts"]["DefaultsRobinhoodLive"] == defaults
    assert "DefaultsCandidate" not in pending["contracts"]
    assert "MissionControlCandidate" not in pending["contracts"]


@pytest.mark.parametrize(
    ("dependency_index", "dependency_address", "error"),
    [
        (None, "0x" + "2" * 40, "DEPENDENCY_REQUIRED"),
        (1, "0x" + "5" * 40, "DEPENDENCY_MISMATCH"),
    ],
)
def test_distinct_activation_witness_requires_matching_constructor_dependency(
    tmp_path,
    dependency_index,
    dependency_address,
    error,
):
    candidate_address = "0x" + "2" * 40
    witness_address = "0x" + "3" * 40
    hq = "0x" + "4" * 40
    candidate = _promotable_record(
        tmp_path,
        "contracts/config/DefaultsRobinhoodLive.vy",
        candidate_address,
    )
    witness = _promotable_record(
        tmp_path,
        "contracts/data/MissionControl.vy",
        witness_address,
        constructor_inputs=(
            ("hq", "address"),
            ("candidate", "address"),
        ),
        constructor_values=(hq, dependency_address),
    )
    active = {
        "contracts": {
            "Candidate": candidate,
            "Witness": witness,
        }
    }
    _write_json(tmp_path / "current-manifest.json", active)
    _write_json(tmp_path / "1-manifest.json", active)
    before = (tmp_path / "current-manifest.json").read_bytes()

    migration = _migration(tmp_path)
    registry = _Registry(witness_address, 5)
    migration._files["DefaultsRobinhoodLive"] = candidate["file"]
    migration._previous_manifest["contracts"]["RipeHq"] = {"address": registry.address}
    with pytest.raises(RuntimeError, match=error):
        migration.promote_candidate(
            "DefaultsRobinhoodLive",
            "Candidate",
            registry,
            5,
            expected_source_path=candidate["file"],
            registry_name="RipeHq",
            expected_constructor_args=(),
            activation_candidate_label="Witness",
            activation_dependency_arg_index=dependency_index,
            activation_expected_constructor_args=(hq, dependency_address),
        )

    assert (tmp_path / "current-manifest.json").read_bytes() == before
    assert not (tmp_path / "2-pending-manifest.json").exists()


@pytest.mark.parametrize(
    ("case", "error"),
    [
        ("fabricated_source", "SOURCE_MISMATCH"),
        ("noncompilable_source", "COMPILE_FAILED"),
        ("integrity", "INTEGRITY_MISMATCH"),
        ("abi", "ABI_MISMATCH"),
        ("compiler", "COMPILER_MISMATCH"),
    ],
)
def test_candidate_promotion_authenticates_source_compiler_integrity_and_abi(
    tmp_path,
    case,
    error,
):
    source_path = "contracts/Canonical.vy"
    candidate = _promotable_record(
        tmp_path,
        source_path,
        "0x" + "2" * 40,
    )
    if case == "fabricated_source":
        candidate["solc_json"]["sources"][source_path]["content"] += (
            "\n# not present in the repository"
        )
    elif case == "noncompilable_source":
        invalid_source = "# pragma version ~=0.4.3\nthis is not vyper\n"
        candidate["solc_json"]["sources"][source_path]["content"] = invalid_source
        (tmp_path / source_path).write_text(invalid_source)
    elif case == "integrity":
        candidate["solc_json"]["integrity"] = "ab" * 32
    elif case == "abi":
        candidate["abi"][0]["name"] = "forgedMarker"
    elif case == "compiler":
        candidate["solc_json"]["compiler_version"] = "v0.4.2"

    active = {"contracts": {"Candidate": candidate}}
    _write_json(tmp_path / "current-manifest.json", active)
    _write_json(tmp_path / "1-manifest.json", active)

    migration = _migration(tmp_path)
    registry = _Registry("0x" + "2" * 40)
    migration._files["Canonical"] = source_path
    migration._previous_manifest["contracts"]["Registry"] = {
        "address": registry.address
    }
    with pytest.raises(RuntimeError, match=f"MIGRATION_CANDIDATE_RECORD_{error}"):
        migration.promote_candidate(
            "Canonical",
            "Candidate",
            registry,
            7,
            expected_source_path=source_path,
            registry_name="Registry",
            expected_constructor_args=(),
        )

    assert not (tmp_path / "2-pending-manifest.json").exists()


def test_candidate_promotion_rejects_valid_wrong_source_for_canonical_label(
    tmp_path,
):
    candidate = _promotable_record(
        tmp_path,
        "contracts/data/MissionControl.vy",
        "0x" + "2" * 40,
    )
    expected_source = "contracts/data/Ledger.vy"
    expected_file = tmp_path / expected_source
    expected_file.parent.mkdir(parents=True, exist_ok=True)
    expected_file.write_text(_source())
    active = {"contracts": {"LedgerCandidate": candidate}}
    _write_json(tmp_path / "current-manifest.json", active)
    _write_json(tmp_path / "1-manifest.json", active)
    migration = _migration(tmp_path, files={"Ledger": expected_source})
    registry = _Registry(candidate["address"])
    migration._previous_manifest["contracts"]["RipeHq"] = {"address": registry.address}

    with pytest.raises(
        RuntimeError,
        match="MIGRATION_CANDIDATE_RECORD_SOURCE_MISMATCH",
    ):
        migration.promote_candidate(
            "Ledger",
            "LedgerCandidate",
            registry,
            4,
            expected_source_path=expected_source,
            registry_name="RipeHq",
            expected_constructor_args=(),
        )


def test_candidate_promotion_rejects_wrong_source_even_when_mapping_agrees(
    tmp_path,
):
    candidate = _promotable_record(
        tmp_path,
        "contracts/data/MissionControl.vy",
        "0x" + "2" * 40,
    )
    active = {"contracts": {"LedgerCandidate": candidate}}
    _write_json(tmp_path / "current-manifest.json", active)
    _write_json(tmp_path / "1-manifest.json", active)
    migration = _migration(
        tmp_path,
        files={"Ledger": candidate["file"]},
    )
    registry = _Registry(candidate["address"])
    migration._previous_manifest["contracts"]["RipeHq"] = {"address": registry.address}

    with pytest.raises(
        RuntimeError,
        match="MIGRATION_CANONICAL_SOURCE_INVALID",
    ):
        migration.promote_candidate(
            "Ledger",
            "LedgerCandidate",
            registry,
            4,
            expected_source_path=candidate["file"],
            registry_name="RipeHq",
            expected_constructor_args=(),
        )


def test_candidate_promotion_binds_approved_compiler_settings(tmp_path):
    candidate = _promotable_record(
        tmp_path,
        "contracts/Canonical.vy",
        "0x" + "2" * 40,
    )
    candidate["solc_json"]["settings"]["optimize"] = "gas"
    active = {"contracts": {"Candidate": candidate}}
    _write_json(tmp_path / "current-manifest.json", active)
    _write_json(tmp_path / "1-manifest.json", active)
    migration = _migration(tmp_path)
    spec = _promotion(
        migration,
        "Canonical",
        "Candidate",
        _Registry(candidate["address"]),
    )

    with pytest.raises(
        RuntimeError,
        match="MIGRATION_CANDIDATE_RECORD_SETTINGS_MISMATCH",
    ):
        migration.promote_candidates([spec])


def test_candidate_promotion_binds_intended_constructor_values(tmp_path):
    recorded_owner = "0x" + "3" * 40
    candidate = _promotable_record(
        tmp_path,
        "contracts/Canonical.vy",
        "0x" + "2" * 40,
        constructor_inputs=(("owner", "address"),),
        constructor_values=(recorded_owner,),
    )
    active = {"contracts": {"Candidate": candidate}}
    _write_json(tmp_path / "current-manifest.json", active)
    _write_json(tmp_path / "1-manifest.json", active)
    migration = _migration(tmp_path)
    spec = _promotion(
        migration,
        "Canonical",
        "Candidate",
        _Registry(candidate["address"]),
        expected_constructor_args=("0x" + "4" * 40,),
    )

    with pytest.raises(
        RuntimeError,
        match="MIGRATION_CANDIDATE_CONSTRUCTOR_INTENT_MISMATCH",
    ):
        migration.promote_candidates([spec])


@pytest.mark.parametrize(
    ("code_case", "error"),
    [
        ("missing", "DEPLOYED_CODE_MISSING"),
        ("prefix", "DEPLOYED_CODE_PREFIX_MISMATCH"),
        ("length", "DEPLOYED_CODE_LENGTH_MISMATCH"),
    ],
)
def test_candidate_promotion_binds_deployed_runtime_template_and_length(
    tmp_path,
    code_case,
    error,
):
    candidate = _promotable_record(
        tmp_path,
        "contracts/Canonical.vy",
        "0x" + "2" * 40,
    )
    active = {"contracts": {"Candidate": candidate}}
    _write_json(tmp_path / "current-manifest.json", active)
    _write_json(tmp_path / "1-manifest.json", active)
    migration = _migration(tmp_path)
    spec = _promotion(
        migration,
        "Canonical",
        "Candidate",
        _Registry(candidate["address"]),
    )
    good_code = _DEPLOYED_CODE[candidate["address"].lower()]
    if code_case == "missing":
        bad_code = b""
    elif code_case == "prefix":
        bad_code = bytes([good_code[0] ^ 1]) + good_code[1:]
    else:
        bad_code = good_code + b"\x00"
    migration._get_deployed_code = lambda _address: bad_code

    with pytest.raises(RuntimeError, match=f"MIGRATION_CANDIDATE_{error}"):
        migration.promote_candidates([spec])


def test_candidate_promotion_uses_exact_utf8_source_bytes(tmp_path):
    source_path = "contracts/Canonical.vy"
    candidate = _promotable_record(
        tmp_path,
        source_path,
        "0x" + "2" * 40,
    )
    local_source = tmp_path / source_path
    local_source.write_bytes(local_source.read_bytes().replace(b"\n", b"\r\n"))
    active = {"contracts": {"Candidate": candidate}}
    _write_json(tmp_path / "current-manifest.json", active)
    _write_json(tmp_path / "1-manifest.json", active)
    migration = _migration(tmp_path)
    spec = _promotion(
        migration,
        "Canonical",
        "Candidate",
        _Registry(candidate["address"]),
    )

    with pytest.raises(
        RuntimeError,
        match="MIGRATION_CANDIDATE_RECORD_SOURCE_MISMATCH",
    ):
        migration.promote_candidates([spec])


def test_candidate_source_match_ignores_spaces_on_blank_lines_only():
    normalize = migration_module._normalized_vyper_source

    assert normalize(b"first\n   \nsecond\n") == normalize(b"first\n\nsecond\n")
    assert normalize(b"first  \n\n") != normalize(b"first\n\n")
    assert normalize(b"first\r\n\r\n") != normalize(b"first\n\n")


def test_candidate_promotion_accepts_real_manifest_source_hash_fields(
    tmp_path,
):
    candidate = _promotable_record(
        tmp_path,
        "contracts/Canonical.vy",
        "0x" + "2" * 40,
    )
    for payload in candidate["solc_json"]["sources"].values():
        payload["sha256sum"] = migration_module.hashlib.sha256(
            payload["content"].encode("utf-8")
        ).hexdigest()
    active = {"contracts": {"Candidate": candidate}}
    _write_json(tmp_path / "current-manifest.json", active)
    _write_json(tmp_path / "1-manifest.json", active)
    migration = _migration(tmp_path)
    spec = _promotion(
        migration,
        "Canonical",
        "Candidate",
        _Registry(candidate["address"]),
    )

    assert migration.promote_candidates([spec]) == (candidate["address"],)


def test_candidate_promotion_rejects_invalid_manifest_source_hash(tmp_path):
    candidate = _promotable_record(
        tmp_path,
        "contracts/Canonical.vy",
        "0x" + "2" * 40,
    )
    source = candidate["solc_json"]["sources"][candidate["file"]]
    source["sha256sum"] = "00" * 32
    active = {"contracts": {"Candidate": candidate}}
    _write_json(tmp_path / "current-manifest.json", active)
    _write_json(tmp_path / "1-manifest.json", active)
    migration = _migration(tmp_path)
    spec = _promotion(
        migration,
        "Canonical",
        "Candidate",
        _Registry(candidate["address"]),
    )

    with pytest.raises(
        RuntimeError,
        match="MIGRATION_CANDIDATE_RECORD_SOURCE_MISMATCH",
    ):
        migration.promote_candidates([spec])


@pytest.mark.parametrize(
    ("record_update", "error"),
    [
        ({"abi": []}, "RECORD_INVALID"),
        ({"args": "00 00"}, "RECORD_INVALID"),
        ({"file": "../Candidate.vy"}, "RECORD_SOURCE_MISMATCH"),
    ],
)
def test_candidate_promotion_rejects_noncanonical_manifest_records(
    tmp_path,
    record_update,
    error,
):
    candidate = _promotable_record(
        tmp_path,
        "Canonical.vy",
        "0x" + "2" * 40,
    )
    candidate.update(record_update)
    active = {"contracts": {"Candidate": candidate}}
    _write_json(tmp_path / "current-manifest.json", active)
    _write_json(tmp_path / "1-manifest.json", active)

    migration = _migration(tmp_path)
    registry = _Registry("0x" + "2" * 40)
    migration._files["Canonical"] = "Canonical.vy"
    migration._previous_manifest["contracts"]["Registry"] = {
        "address": registry.address
    }
    with pytest.raises(RuntimeError, match=f"MIGRATION_CANDIDATE_{error}"):
        migration.promote_candidate(
            "Canonical",
            "Candidate",
            registry,
            7,
            expected_source_path="Canonical.vy",
            registry_name="Registry",
            expected_constructor_args=(),
        )

    assert not (tmp_path / "2-pending-manifest.json").exists()


def test_candidate_promotion_rejects_constructor_trailing_bytes(tmp_path):
    candidate = _promotable_record(
        tmp_path,
        "Canonical.vy",
        "0x" + "2" * 40,
        constructor_inputs=(("hq", "address"),),
        constructor_values=("0x" + "3" * 40,),
    )
    candidate["args"] += "00" * 32
    active = {"contracts": {"Candidate": candidate}}
    _write_json(tmp_path / "current-manifest.json", active)
    _write_json(tmp_path / "1-manifest.json", active)

    migration = _migration(tmp_path)
    registry = _Registry(candidate["address"])
    migration._files["Canonical"] = candidate["file"]
    migration._previous_manifest["contracts"]["Registry"] = {
        "address": registry.address
    }
    with pytest.raises(RuntimeError, match="MIGRATION_CANDIDATE_RECORD_INVALID"):
        migration.promote_candidate(
            "Canonical",
            "Candidate",
            registry,
            7,
            expected_source_path=candidate["file"],
            registry_name="Registry",
            expected_constructor_args=("0x" + "3" * 40,),
        )

    assert not (tmp_path / "2-pending-manifest.json").exists()


def test_distinct_activation_witness_rejects_unapproved_policy(tmp_path):
    candidate = _promotable_record(
        tmp_path,
        "contracts/config/DefaultsRobinhoodLive.vy",
        "0x" + "2" * 40,
    )
    witness = _promotable_record(
        tmp_path,
        "contracts/data/MissionControl.vy",
        "0x" + "3" * 40,
        constructor_inputs=(("candidate", "address"),),
        constructor_values=(candidate["address"],),
    )
    active = {"contracts": {"Candidate": candidate, "Witness": witness}}
    _write_json(tmp_path / "current-manifest.json", active)
    _write_json(tmp_path / "1-manifest.json", active)

    migration = _migration(tmp_path)
    registry = _Registry(witness["address"], 5)
    migration._files["DefaultsRobinhoodLive"] = candidate["file"]
    migration._previous_manifest["contracts"]["RipeHq"] = {"address": registry.address}
    with pytest.raises(
        RuntimeError,
        match="MIGRATION_ACTIVATION_DEPENDENCY_UNSUPPORTED",
    ):
        migration.promote_candidate(
            "DefaultsRobinhoodLive",
            "Candidate",
            registry,
            5,
            expected_source_path=candidate["file"],
            registry_name="RipeHq",
            expected_constructor_args=(),
            activation_candidate_label="Witness",
            activation_dependency_arg_index=0,
            activation_expected_constructor_args=(candidate["address"],),
        )

    assert not (tmp_path / "2-pending-manifest.json").exists()


def test_distinct_activation_witness_requires_canonical_ripe_hq_registry(
    tmp_path,
):
    defaults = _promotable_record(
        tmp_path,
        "contracts/config/DefaultsRobinhoodLive.vy",
        "0x" + "2" * 40,
    )
    hq = "0x" + "4" * 40
    witness = _promotable_record(
        tmp_path,
        "contracts/data/MissionControl.vy",
        "0x" + "3" * 40,
        constructor_inputs=(("hq", "address"), ("defaults", "address")),
        constructor_values=(hq, defaults["address"]),
    )
    active = {"contracts": {"Candidate": defaults, "Witness": witness}}
    _write_json(tmp_path / "current-manifest.json", active)
    _write_json(tmp_path / "1-manifest.json", active)
    migration = _migration(tmp_path)
    registry = _Registry(witness["address"], 5)
    migration._files["DefaultsRobinhoodLive"] = defaults["file"]
    migration._previous_manifest["contracts"]["FakeRegistry"] = {
        "address": registry.address
    }

    with pytest.raises(
        RuntimeError,
        match="MIGRATION_ACTIVATION_DEPENDENCY_UNSUPPORTED",
    ):
        migration.promote_candidate(
            "DefaultsRobinhoodLive",
            "Candidate",
            registry,
            5,
            expected_source_path=defaults["file"],
            registry_name="FakeRegistry",
            expected_constructor_args=(),
            activation_candidate_label="Witness",
            activation_dependency_arg_index=1,
            activation_expected_constructor_args=(hq, defaults["address"]),
        )


def test_candidate_promotion_can_create_first_canonical_label(tmp_path):
    candidate = _promotable_record(
        tmp_path,
        "BlueChipYieldPrices.vy",
        "0x" + "2" * 40,
        constructor_inputs=(("hq", "address"),),
        constructor_values=("0x" + "3" * 40,),
    )
    candidate["future_field"] = {"preserve": True}
    active = {
        "contracts": {
            "BlueChipYieldPricesCandidate": candidate,
        }
    }
    _write_json(tmp_path / "current-manifest.json", active)
    _write_json(tmp_path / "1-manifest.json", active)

    migration = _migration(tmp_path)
    registry = _Registry(candidate["address"])
    migration._files["BlueChipYieldPrices"] = candidate["file"]
    migration._previous_manifest["contracts"]["Registry"] = {
        "address": registry.address
    }
    migration.promote_candidate(
        "BlueChipYieldPrices",
        "BlueChipYieldPricesCandidate",
        registry,
        7,
        expected_source_path=candidate["file"],
        registry_name="Registry",
        expected_constructor_args=("0x" + "3" * 40,),
    )

    pending = json.loads((tmp_path / "2-pending-manifest.json").read_text())
    assert pending["contracts"]["BlueChipYieldPrices"] == candidate
    assert "BlueChipYieldPricesCandidate" not in pending["contracts"]
    assert "BlueChipYieldPrices" not in active["contracts"]


def test_candidate_promotion_batch_late_failure_is_write_free(tmp_path):
    first = _promotable_record(
        tmp_path,
        "contracts/First.vy",
        "0x" + "2" * 40,
    )
    second = _promotable_record(
        tmp_path,
        "contracts/Second.vy",
        "0x" + "3" * 40,
    )
    active = {"contracts": {"FirstCandidate": first, "SecondCandidate": second}}
    _write_json(tmp_path / "current-manifest.json", active)
    _write_json(tmp_path / "1-manifest.json", active)
    current_before = (tmp_path / "current-manifest.json").read_bytes()

    migration = _migration(tmp_path)
    first_registry = _Registry(first["address"])
    second_registry = _Registry("0x" + "4" * 40)
    first_spec = _promotion(
        migration,
        "First",
        "FirstCandidate",
        first_registry,
        registry_name="FirstRegistry",
    )
    second_spec = _promotion(
        migration,
        "Second",
        "SecondCandidate",
        second_registry,
        registry_name="SecondRegistry",
    )
    memory_before = copy.deepcopy(migration._previous_manifest)
    with pytest.raises(
        RuntimeError,
        match="MIGRATION_CANDIDATE_REGISTRY_MISMATCH",
    ):
        migration.promote_candidates([first_spec, second_spec])

    assert migration._previous_manifest == memory_before
    assert (tmp_path / "current-manifest.json").read_bytes() == current_before
    assert not (tmp_path / "2-pending-manifest.json").exists()


def test_candidate_promotion_save_failure_does_not_advance_memory(
    tmp_path,
    monkeypatch,
):
    candidate = _promotable_record(
        tmp_path,
        "contracts/Canonical.vy",
        "0x" + "2" * 40,
    )
    active = {"contracts": {"Candidate": candidate}}
    _write_json(tmp_path / "current-manifest.json", active)
    _write_json(tmp_path / "1-manifest.json", active)
    migration = _migration(tmp_path)
    spec = _promotion(
        migration,
        "Canonical",
        "Candidate",
        _Registry(candidate["address"]),
    )
    memory_before = copy.deepcopy(migration._previous_manifest)

    original_save = migration_module.json_file.save

    def fail_save(filename, manifest):
        if filename.endswith("-pending-manifest.json"):
            raise OSError("synthetic save failure")
        return original_save(filename, manifest)

    monkeypatch.setattr(migration_module.json_file, "save", fail_save)
    with pytest.raises(OSError, match="synthetic save failure"):
        migration.promote_candidates([spec])

    assert migration._previous_manifest == memory_before
    assert "Canonical" not in migration._previous_manifest["contracts"]
    assert not (tmp_path / "2-pending-manifest.json").exists()


def test_successful_promotion_checkpoint_is_immediately_resumable(tmp_path):
    candidate = _promotable_record(
        tmp_path,
        "contracts/Canonical.vy",
        "0x" + "2" * 40,
    )
    active = {
        "contracts": {
            "Candidate": candidate,
            "Canonical": {
                "address": "0x" + "1" * 40,
                "stale_field": "must not return",
            },
        }
    }
    _write_json(tmp_path / "current-manifest.json", active)
    _write_json(tmp_path / "1-manifest.json", active)
    migration = _migration(tmp_path)
    spec = _promotion(
        migration,
        "Canonical",
        "Candidate",
        _Registry(candidate["address"]),
    )

    migration.promote_candidates([spec])

    assert json.loads((tmp_path / "2-log.json").read_text()) == {"transactions": []}
    resumed = _migration(
        tmp_path,
        files={"Canonical": candidate["file"]},
    )
    assert resumed._previous_manifest["contracts"]["Canonical"] == candidate


def test_atomic_json_save_preserves_old_target_after_partial_write(
    tmp_path,
    monkeypatch,
):
    target = tmp_path / "manifest.json"
    original = b'{"old": true}'
    target.write_bytes(original)
    real_write = migration_module.json_file.os.write

    def partial_then_fail(fd, data):
        real_write(fd, data[: max(1, len(data) // 2)])
        raise OSError("synthetic partial write")

    monkeypatch.setattr(
        migration_module.json_file,
        "write_all",
        partial_then_fail,
    )
    with pytest.raises(OSError, match="synthetic partial write"):
        migration_module.json_file.save(target, {"new": list(range(50))})

    assert target.read_bytes() == original
    assert list(tmp_path.glob(".manifest.json.*.tmp")) == []


def test_atomic_json_save_replaces_with_complete_utf8_json(tmp_path):
    target = tmp_path / "manifest.json"
    target.write_text('{"old": true}')
    value = {"message": "Ripe ✓", "rows": [1, 2, 3]}

    migration_module.json_file.save(target, value)

    assert json.loads(target.read_text(encoding="utf-8")) == value


def test_pending_manifest_without_transaction_log_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(
        migration_module,
        "deployed_contracts_manifest",
        lambda contracts, *args: {
            "contracts": {
                name: {"address": value, "file": "new.vy"}
                for name, value in contracts.items()
            }
        },
    )
    first = _migration(tmp_path)
    first._contracts["Service"] = "0x" + "2" * 40
    first._append_manifest("Service")

    with pytest.raises(RuntimeError, match="MIGRATION_RESUME_STATE_INCOMPLETE"):
        _migration(tmp_path)


def test_force_replay_refuses_an_existing_pending_journal(tmp_path):
    _write_json(tmp_path / "2-pending-manifest.json", {"contracts": {}})
    _write_json(tmp_path / "2-log.json", {"transactions": ["0xabc"]})

    with pytest.raises(RuntimeError, match="MIGRATION_FORCE_REPLAY_PENDING"):
        Migration(_args(ignore_logs=True), {}, "2", "1", str(tmp_path))


def _migration_source(path: Path, name: str) -> None:
    path.joinpath(name).write_text("def migrate(migration):\n    return None\n")


def test_auto_resume_requires_a_numeric_completion_checkpoint(tmp_path):
    source = tmp_path / "source"
    history = tmp_path / "history"
    source.mkdir()
    history.mkdir()
    _migration_source(source, "001_first.py")
    _migration_source(source, "002_second.py")
    _write_json(history / "current-manifest.json", {"contracts": {}})

    runner = MigrationRunner(str(source), str(history), {})
    with pytest.raises(RuntimeError, match="MIGRATION_RESUME_CHECKPOINT_REQUIRED"):
        list(runner._migrations())

    # An explicit start remains an intentional operator override.
    assert [row[1] for row in runner._migrations("0")] == ["001", "002"]


def test_auto_resume_uses_only_finalized_numeric_manifests(tmp_path):
    source = tmp_path / "source"
    history = tmp_path / "history"
    source.mkdir()
    history.mkdir()
    _migration_source(source, "001_first.py")
    _migration_source(source, "002_second.py")
    _write_json(history / "current-manifest.json", {"contracts": {}})
    _write_json(history / "001-manifest.json", {"contracts": {}})
    _write_json(history / "999-pending-manifest.json", {"contracts": {}})

    runner = MigrationRunner(str(source), str(history), {})
    assert [row[1] for row in runner._migrations()] == ["002"]


def test_empty_history_starts_from_first_migration(tmp_path):
    source = tmp_path / "source"
    history = tmp_path / "history"
    source.mkdir()
    history.mkdir()
    _migration_source(source, "001_first.py")

    runner = MigrationRunner(str(source), str(history), {})
    assert [row[1] for row in runner._migrations()] == ["001"]
