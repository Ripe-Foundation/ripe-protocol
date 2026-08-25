import copy
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import warnings
from typing import Any, Mapping

import boa.contracts
import boa.contracts.abi
from eth_abi.abi import decode, encode
from mergedeep import merge
import boa
import vyper
from vyper.cli.vyper_json import compile_json
from scripts.utils import log
from scripts.utils import json_file
from scripts.utils import solidity
from scripts.utils.deploy_args import DeployArgs
from scripts.utils.migration_helpers import (
    TransactionExecutionError,
    deployed_contracts_manifest,
    execute_transaction,
)



_PROMOTABLE_MANIFEST_FIELDS = frozenset({"address", "file", "abi", "solc_json", "args"})
_PROMOTABLE_SOLC_FIELDS = frozenset(
    {"language", "sources", "settings", "compiler_version", "integrity"}
)
_CANONICAL_HEX_RE = re.compile(r"(?:[0-9a-f]{2})*")
_INTEGRITY_RE = re.compile(r"[0-9a-f]{64}")
_COMPILER_VERSION_RE = re.compile(r"v?\d+\.\d+\.\d+(?:\+commit\.[0-9a-f]+)?")
_ADDRESS_RE = re.compile(r"0x[0-9a-fA-F]{40}")
_LEGACY_VYPER_DEPLOYMENT_RE = re.compile(
    r"^<[^>]+ at (0x[0-9a-fA-F]{40})(?:, compiled with [^>]+)?>"
)
_LEGACY_BLUEPRINT_LOG_RE = re.compile(
    r"^<boa\.contracts\.vyper\.vyper_contract\.VyperBlueprint "
    r"object at 0x[0-9a-fA-F]+>$"
)
_ABI_ENTRY_TYPES = frozenset({"constructor", "event", "fallback", "function"})
_TRANSACTION_LOG_VERSION = 2
_TRANSACTION_LOG_FIELDS = frozenset(
    {
        "version",
        "kind",
        "chain",
        "sender",
        "target",
        "calldata_sha256",
        "value",
        "receipt",
    }
)
_SOLIDITY_DEPLOYMENT_LOG_FIELDS = frozenset(
    {
        "version",
        "kind",
        "chain",
        "sender",
        "contract",
        "source_file",
        "artifact_sha256",
        "creation_sha256",
        "address",
        "runtime_sha256",
    }
)
_BOA_CALL_OPTION_NAMES = frozenset(("gas", "sender", "simulate", "value"))
_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_DISTINCT_ACTIVATION_POLICIES = frozenset(
    {
        (
            "DefaultsRobinhoodLive",
            "contracts/config/DefaultsRobinhoodLive.vy",
            "contracts/data/MissionControl.vy",
            "RipeHq",
            5,
            1,
        ),
        (
            "BondBooster",
            "contracts/config/BondBooster.vy",
            "contracts/core/BondRoom.vy",
            "RipeHq",
            12,
            1,
        ),
    }
)


def _validated_manifest(manifest, error):
    if (
        not isinstance(manifest, dict)
        or set(manifest) != {"contracts"}
        or not isinstance(manifest["contracts"], dict)
    ):
        raise RuntimeError(error)
    return manifest


@dataclass(frozen=True)
class PromotionSpec:
    """Complete, caller-owned intent for one manifest promotion.

    The manifest remains evidence of what was deployed; this specification is
    the independent statement of what the migration intended to deploy and
    which canonical registry must have activated it.
    """

    canonical_name: str
    expected_source_path: str
    candidate_label: str
    registry_name: str
    registry: Any
    registry_id: int
    expected_constructor_args: tuple
    activation_candidate_label: str | None = None
    activation_dependency_arg_index: int | None = None
    activation_expected_constructor_args: tuple | None = None


@dataclass(frozen=True)
class _ValidatedPromotableRecord:
    address: str
    encoded_args: bytes
    runtime_template: bytes
    deployed_runtime_size: int


def _iter_code_layout_entries(layout: Mapping[str, Any]):
    for value in layout.values():
        if isinstance(value, Mapping) and {"offset", "length", "type"} <= set(value):
            yield value
        elif isinstance(value, Mapping):
            yield from _iter_code_layout_entries(value)


def _code_data_size(layout):
    if not isinstance(layout, Mapping):
        raise RuntimeError("MIGRATION_CANDIDATE_RECORD_RUNTIME_INVALID")
    entries = sorted(
        (int(item["offset"]), int(item["length"]))
        for item in _iter_code_layout_entries(layout)
    )
    cursor = 0
    for offset, length in entries:
        if length <= 0 or offset != cursor:
            raise RuntimeError("MIGRATION_CANDIDATE_RECORD_RUNTIME_INVALID")
        cursor += length
    return cursor


def _canonical_address(value):
    if hasattr(value, "address"):
        value = value.address
    return value


def _encode_expected_constructor_args(abi, values, *, blueprint=False):
    if not isinstance(values, tuple):
        raise RuntimeError("MIGRATION_CONSTRUCTOR_INTENT_REQUIRED")
    constructors = [entry for entry in abi if entry["type"] == "constructor"]
    if len(constructors) > 1:
        raise RuntimeError("MIGRATION_CANDIDATE_RECORD_INVALID")
    if blueprint:
        if values:
            raise RuntimeError("MIGRATION_BLUEPRINT_CONSTRUCTOR_INTENT_INVALID")
        return b""
    if not constructors:
        if values:
            raise RuntimeError("MIGRATION_CONSTRUCTOR_INTENT_MISMATCH")
        return b""
    inputs = constructors[0].get("inputs")
    if not isinstance(inputs, list) or any(
        not isinstance(item, dict) or not isinstance(item.get("type"), str)
        for item in inputs
    ):
        raise RuntimeError("MIGRATION_CANDIDATE_RECORD_INVALID")
    try:
        return encode(
            [item["type"] for item in inputs],
            tuple(_canonical_address(value) for value in values),
        )
    except Exception:
        raise RuntimeError("MIGRATION_CONSTRUCTOR_INTENT_INVALID") from None


def _compile_authenticated_record(
    record,
    *,
    expected_source_path,
    activation=False,
):
    kind = "ACTIVATION_CANDIDATE" if activation else "CANDIDATE"
    if not isinstance(record, dict):
        raise RuntimeError(f"MIGRATION_{kind}_RECORD_INVALID")
    if not _PROMOTABLE_MANIFEST_FIELDS.issubset(record):
        raise RuntimeError(f"MIGRATION_{kind}_RECORD_INCOMPLETE")
    source_path = record["file"]
    if (
        not isinstance(expected_source_path, str)
        or not expected_source_path
        or not isinstance(source_path, str)
        or not source_path
    ):
        raise RuntimeError(f"MIGRATION_{kind}_RECORD_INVALID")
    normalized_path = PurePosixPath(source_path.replace("\\", "/"))
    if (
        normalized_path.is_absolute()
        or ".." in normalized_path.parts
        or normalized_path.suffix != ".vy"
        or source_path != normalized_path.as_posix()
        or source_path != expected_source_path
    ):
        raise RuntimeError(f"MIGRATION_{kind}_RECORD_SOURCE_MISMATCH")
    abi = record["abi"]
    if (
        not isinstance(abi, list)
        or not abi
        or any(
            not isinstance(entry, dict)
            or not isinstance(entry.get("type"), str)
            or entry["type"] not in _ABI_ENTRY_TYPES
            for entry in abi
        )
    ):
        raise RuntimeError(f"MIGRATION_{kind}_RECORD_INVALID")
    solc_json = record["solc_json"]
    expected_settings = {
        "outputSelection": {source_path: ["*"]},
        "search_paths": ["."],
    }
    if (
        not isinstance(solc_json, dict)
        or set(solc_json) != _PROMOTABLE_SOLC_FIELDS
        or solc_json.get("language") != "Vyper"
        or not isinstance(solc_json.get("sources"), dict)
        or not solc_json["sources"]
        or not isinstance(solc_json.get("compiler_version"), str)
        or _COMPILER_VERSION_RE.fullmatch(solc_json["compiler_version"]) is None
        or not isinstance(solc_json.get("integrity"), str)
        or _INTEGRITY_RE.fullmatch(solc_json["integrity"]) is None
        or source_path not in solc_json["sources"]
        or not isinstance(solc_json["sources"][source_path], dict)
        or not isinstance(solc_json["sources"][source_path].get("content"), str)
        or not solc_json["sources"][source_path]["content"]
    ):
        raise RuntimeError(f"MIGRATION_{kind}_RECORD_INVALID")
    if solc_json["settings"] != expected_settings:
        raise RuntimeError(f"MIGRATION_{kind}_RECORD_SETTINGS_MISMATCH")
    for compiler_source, payload in solc_json["sources"].items():
        compiler_path = PurePosixPath(str(compiler_source).replace("\\", "/"))
        if (
            not isinstance(compiler_source, str)
            or not compiler_source
            or compiler_path.is_absolute()
            or ".." in compiler_path.parts
            or compiler_path.suffix not in {".vy", ".vyi"}
            or compiler_source != compiler_path.as_posix()
            or not isinstance(payload, dict)
            or not {"content"} <= set(payload) <= {"content", "sha256sum"}
            or not isinstance(payload.get("content"), str)
            or not payload["content"]
        ):
            raise RuntimeError(f"MIGRATION_{kind}_RECORD_INVALID")
        repository_root = _REPOSITORY_ROOT.resolve()
        local_source = (_REPOSITORY_ROOT / compiler_path).resolve()
        try:
            local_source.relative_to(repository_root)
        except ValueError:
            raise RuntimeError(f"MIGRATION_{kind}_RECORD_SOURCE_MISMATCH") from None
        try:
            recorded_source = payload["content"].encode("utf-8")
        except UnicodeEncodeError:
            raise RuntimeError(f"MIGRATION_{kind}_RECORD_SOURCE_MISMATCH") from None
        recorded_sha256 = payload.get("sha256sum")
        if recorded_sha256 is not None and (
            not isinstance(recorded_sha256, str)
            or _INTEGRITY_RE.fullmatch(recorded_sha256) is None
            or hashlib.sha256(recorded_source).hexdigest() != recorded_sha256
        ):
            raise RuntimeError(f"MIGRATION_{kind}_RECORD_SOURCE_MISMATCH")
        if not local_source.is_file() or _normalized_vyper_source(
            local_source.read_bytes()
        ) != _normalized_vyper_source(recorded_source):
            raise RuntimeError(f"MIGRATION_{kind}_RECORD_SOURCE_MISMATCH")

    expected_compiler = f"v{vyper.__long_version__}"
    if solc_json["compiler_version"] != expected_compiler:
        raise RuntimeError(f"MIGRATION_{kind}_RECORD_COMPILER_MISMATCH")
    try:
        compiled = compile_json(copy.deepcopy(solc_json))
    except Exception:
        raise RuntimeError(f"MIGRATION_{kind}_RECORD_COMPILE_FAILED") from None
    compiler_messages = compiled.get("errors") or []
    if any(
        "Mismatched integrity sum!" in str(message.get("message", ""))
        for message in compiler_messages
        if isinstance(message, dict)
    ):
        raise RuntimeError(f"MIGRATION_{kind}_RECORD_INTEGRITY_MISMATCH")
    if compiler_messages:
        raise RuntimeError(f"MIGRATION_{kind}_RECORD_COMPILE_FAILED")
    source_outputs = compiled.get("contracts", {}).get(source_path)
    if not isinstance(source_outputs, dict) or len(source_outputs) != 1:
        raise RuntimeError(f"MIGRATION_{kind}_RECORD_COMPILE_FAILED")
    compiled_contract = next(iter(source_outputs.values()))
    compiled_abi = compiled_contract.get("abi")
    if json.dumps(compiled_abi, sort_keys=True, separators=(",", ":")) != json.dumps(
        abi, sort_keys=True, separators=(",", ":")
    ):
        raise RuntimeError(f"MIGRATION_{kind}_RECORD_ABI_MISMATCH")
    return compiled_contract


def _validated_promotable_record(
    record,
    *,
    expected_source_path,
    expected_constructor_args,
    activation=False,
):
    kind = "ACTIVATION_CANDIDATE" if activation else "CANDIDATE"
    compiled_contract = _compile_authenticated_record(
        record,
        expected_source_path=expected_source_path,
        activation=activation,
    )
    abi = record["abi"]
    args = record["args"]
    if not isinstance(args, str) or _CANONICAL_HEX_RE.fullmatch(args) is None:
        raise RuntimeError(f"MIGRATION_{kind}_RECORD_INVALID")
    constructors = [entry for entry in abi if entry["type"] == "constructor"]
    if len(constructors) > 1:
        raise RuntimeError(f"MIGRATION_{kind}_RECORD_INVALID")
    if not constructors:
        if args:
            raise RuntimeError(f"MIGRATION_{kind}_RECORD_INVALID")
    else:
        inputs = constructors[0].get("inputs")
        if not isinstance(inputs, list) or any(
            not isinstance(item, dict) or not isinstance(item.get("type"), str)
            for item in inputs
        ):
            raise RuntimeError(f"MIGRATION_{kind}_RECORD_INVALID")
        try:
            input_types = [item["type"] for item in inputs]
            encoded_args = bytes.fromhex(args)
            decoded_args = decode(input_types, encoded_args)
            if encode(input_types, decoded_args) != encoded_args:
                raise ValueError("non-canonical constructor encoding")
        except Exception:
            raise RuntimeError(f"MIGRATION_{kind}_RECORD_INVALID") from None

    expected_encoded_args = _encode_expected_constructor_args(
        abi,
        expected_constructor_args,
    )
    if expected_encoded_args != bytes.fromhex(args):
        raise RuntimeError(f"MIGRATION_{kind}_CONSTRUCTOR_INTENT_MISMATCH")

    address = record["address"]
    if (
        not isinstance(address, str)
        or len(address) != 42
        or not address.startswith("0x")
    ):
        raise RuntimeError(f"MIGRATION_{kind}_ADDRESS_INVALID")
    try:
        address_value = int(address[2:], 16)
    except ValueError:
        raise RuntimeError(f"MIGRATION_{kind}_ADDRESS_INVALID") from None
    if address_value == 0:
        raise RuntimeError(f"MIGRATION_{kind}_ADDRESS_INVALID")
    try:
        runtime_hex = compiled_contract["evm"]["deployedBytecode"]["object"]
        if isinstance(runtime_hex, str) and runtime_hex.startswith("0x"):
            runtime_hex = runtime_hex[2:]
        if (
            not isinstance(runtime_hex, str)
            or _CANONICAL_HEX_RE.fullmatch(runtime_hex) is None
            or not runtime_hex
        ):
            raise ValueError
        runtime_template = bytes.fromhex(runtime_hex)
        code_layout = compiled_contract["layout"].get("code_layout", {})
        deployed_runtime_size = len(runtime_template) + _code_data_size(code_layout)
    except (KeyError, TypeError, ValueError):
        raise RuntimeError(f"MIGRATION_{kind}_RECORD_RUNTIME_INVALID") from None
    return _ValidatedPromotableRecord(
        address=address,
        encoded_args=bytes.fromhex(args),
        runtime_template=runtime_template,
        deployed_runtime_size=deployed_runtime_size,
    )


def _validate_activation_dependency(
    activation_record,
    candidate_address,
    constructor_arg_index,
):
    if not isinstance(constructor_arg_index, int) or constructor_arg_index < 0:
        raise RuntimeError("MIGRATION_ACTIVATION_DEPENDENCY_INVALID")
    constructors = [
        entry for entry in activation_record["abi"] if entry["type"] == "constructor"
    ]
    if len(constructors) != 1:
        raise RuntimeError("MIGRATION_ACTIVATION_DEPENDENCY_INVALID")
    inputs = constructors[0].get("inputs")
    if not isinstance(inputs, list) or constructor_arg_index >= len(inputs):
        raise RuntimeError("MIGRATION_ACTIVATION_DEPENDENCY_INVALID")
    if any(
        not isinstance(item, dict) or not isinstance(item.get("type"), str)
        for item in inputs
    ):
        raise RuntimeError("MIGRATION_ACTIVATION_DEPENDENCY_INVALID")
    if inputs[constructor_arg_index]["type"] != "address":
        raise RuntimeError("MIGRATION_ACTIVATION_DEPENDENCY_INVALID")
    try:
        input_types = [item["type"] for item in inputs]
        encoded_args = bytes.fromhex(activation_record["args"])
        values = decode(input_types, encoded_args)
        if encode(input_types, values) != encoded_args:
            raise ValueError("non-canonical constructor encoding")
    except Exception:
        raise RuntimeError("MIGRATION_ACTIVATION_DEPENDENCY_INVALID") from None
    if str(values[constructor_arg_index]).lower() != candidate_address.lower():
        raise RuntimeError("MIGRATION_ACTIVATION_DEPENDENCY_MISMATCH")


# A history that already holds a current-manifest.json has been deployed.
# `_append_manifest` writes it on the first successful step, so its presence is
# the surviving evidence that migrations have run here -- the numbered step
# manifests are pruned as a matter of policy (see docs/simplification), and the
# transaction log is deleted by `end()` on success, so neither can be used.
#
# Running against such a history is allowed, but not by accident:
# `--start-timestamp` defaults to "0", which selects every migration from the
# first one, so a bare run is a full redeploy rather than a resume.
# MigrationRunner decides; anything constructing a Migration directly fails
# closed.
CURRENT_MANIFEST = "current-manifest.json"


class MigrationHistoryError(Exception):
    """Raised when a migration would execute against a deployed history."""


def _deployment_address_from_log(value):
    """Read a chain address from current or legacy deployment journal data."""
    if not isinstance(value, str):
        return None
    if _ADDRESS_RE.fullmatch(value):
        return value
    match = _LEGACY_VYPER_DEPLOYMENT_RE.match(value)
    return match.group(1) if match else None


def _normalized_vyper_source(source):
    """Match Vyper's compiler JSON normalization of whitespace-only lines."""
    return re.sub(rb"(?m)^[ \t]+(?=\r?$)", b"", source)


def history_has_deployment(history_path):
    """True if `history_path` already holds a deployed current manifest."""
    return os.path.exists(os.path.join(str(history_path), CURRENT_MANIFEST))


_STEP_MANIFEST_FIELDS = frozenset({"address", "file"})


def _slim_step_manifest(manifest, contract_names):
    """Reduce a full manifest to a step manifest: this step's attribution only.

    current-manifest.json is the cumulative, verifiable record (abi, solc_json,
    args, address, file, for every contract deployed to date); a numbered step
    manifest exists only so a migration ID can be resolved back to the
    addresses *it* deployed (`verify --migration <timestamp>`, history
    readers). `manifest` here is the post-merge cumulative record, so this
    both narrows to `contract_names` -- what this migration actually touched,
    tracked in `self._contracts` -- and drops every field but address/file.
    An execute-only migration that deploys nothing correctly gets an empty
    step manifest rather than a copy of everything deployed before it.
    """
    contracts = manifest.get("contracts", {})
    return {
        "contracts": {
            name: {
                key: value
                for key, value in contracts[name].items()
                if key in _STEP_MANIFEST_FIELDS
            }
            for name in contract_names
            if name in contracts
        }
    }


class Migration:
    def __init__(
        self,
        deploy_args: DeployArgs,
        files,
        timestamp,
        previous_timestamp,
        history_path,
    ):
        self._hq = None
        self._files = files
        self._timestamp = timestamp
        self._previous_timestamp = previous_timestamp
        self._history_path = history_path
        self._deploy_args = deploy_args
        self._count = 0
        self._transactions = []
        self._contracts = {}
        self._contract_files = {}
        self._args = {}
        self._last_run_was_resume = False
        self._last_resumed_transaction = None
        self._last_resumed_transaction_raw = None
        self.gas = 0

        try:
            filename = self._manifest_filename("current")
            log.h3(f"Loading previous manifest {filename}")
            self._previous_manifest = json_file.load(filename)
        except FileNotFoundError:
            self._previous_manifest = {}
        except Exception:
            raise RuntimeError("MIGRATION_CURRENT_MANIFEST_INVALID") from None
        else:
            self._previous_manifest = _validated_manifest(
                self._previous_manifest,
                "MIGRATION_CURRENT_MANIFEST_INVALID",
            )

        pending_filename = self._pending_manifest_filename()
        has_pending_manifest = os.path.exists(pending_filename)
        if has_pending_manifest:
            if self._deploy_args.ignore_logs:
                raise RuntimeError("MIGRATION_FORCE_REPLAY_PENDING")
            try:
                pending_manifest = json_file.load(pending_filename)
            except Exception:
                raise RuntimeError("MIGRATION_PENDING_MANIFEST_INVALID") from None
            pending_manifest = _validated_manifest(
                pending_manifest,
                "MIGRATION_PENDING_MANIFEST_INVALID",
            )
            # Pending manifests are complete snapshots, not deltas. Treat the
            # checkpoint as authoritative so recursive merging cannot revive
            # stale fields from the prior canonical contract record.
            self._previous_manifest = pending_manifest

        loaded_log = False
        if self._deploy_args.ignore_logs:
            log.h3(f"Ignoring previous log file: {self._log_filename()}")
        else:
            try:
                self._load_log_file()
                loaded_log = True
                log.h3(f"Log file {self._log_filename()} loaded")
            except FileNotFoundError:
                log.h3(f"No previous log file: {self._log_filename()}")
            except Exception:
                raise RuntimeError("MIGRATION_TRANSACTION_LOG_INVALID") from None
        if has_pending_manifest and not loaded_log:
            raise RuntimeError("MIGRATION_RESUME_STATE_INCOMPLETE")

    def rpc(self):
        return self._deploy_args.rpc

    def is_local_preview(self):
        """Whether the CLI selected a verified local/fork execution path."""
        return getattr(self._deploy_args, "local_preview", False) is True

    def execute(self, transaction, *args, **kwargs):
        """
        Executes a transaction or skips if already executed.
        Returns the transaction receipt.
        """
        tx = self._run("", transaction, *args, **kwargs)
        self._save_log_file()

        return tx

    def execute_reconciled(self, transaction, postcondition, *args, **kwargs):
        """Record a call already proven complete after a receipt-side failure."""
        if self._curr_transaction() is not None:
            return self.execute(transaction, *args, **kwargs)
        if postcondition():
            return self._record_reconciled_transaction(
                transaction,
                args,
                kwargs,
            )
        try:
            return self.execute(transaction, *args, **kwargs)
        except TransactionExecutionError:
            if not postcondition():
                raise
            return self._record_reconciled_transaction(
                transaction,
                args,
                kwargs,
            )

    def _record_reconciled_transaction(self, transaction, args, kwargs):
        assert self._curr_transaction() is None
        next_transaction = self._count + 1
        log.h2(f"Transaction {next_transaction} — reconciled on-chain state")
        intent = self._transaction_intent(transaction, args, kwargs)
        self._transactions.append(self._transaction_record(intent, True))
        self._count += 1
        self._save_log_file()
        return True

    def _expected_source_path(
        self,
        canonical_name,
        required_source_path=None,
    ):
        source_path = self._files.get(canonical_name)
        if not isinstance(source_path, str) or not source_path:
            raise RuntimeError("MIGRATION_CANONICAL_SOURCE_MISSING")
        normalized = PurePosixPath(source_path.replace("\\", "/"))
        if (
            normalized.is_absolute()
            or ".." in normalized.parts
            or normalized.suffix != ".vy"
            or normalized.as_posix() != source_path
            or normalized.stem != canonical_name
        ):
            raise RuntimeError("MIGRATION_CANONICAL_SOURCE_INVALID")
        if required_source_path is not None:
            if (
                not isinstance(required_source_path, str)
                or required_source_path != source_path
            ):
                raise RuntimeError("MIGRATION_CANONICAL_SOURCE_MISMATCH")
        return source_path

    def _validate_resumed_deployment_record(
        self,
        name,
        record,
        args,
        *,
        blueprint,
    ):
        expected_source_path = self._expected_source_path(name)
        if not blueprint:
            validated = _validated_promotable_record(
                record,
                expected_source_path=expected_source_path,
                expected_constructor_args=tuple(args),
            )
            self._validate_deployed_code(validated)
            return

        compiled_contract = _compile_authenticated_record(
            record,
            expected_source_path=expected_source_path,
        )
        recorded_args = record.get("args")
        if (
            not isinstance(recorded_args, str)
            or _CANONICAL_HEX_RE.fullmatch(recorded_args) is None
        ):
            raise RuntimeError("MIGRATION_RESUMED_CONTRACT_RECORD_INVALID")
        expected_args = _encode_expected_constructor_args(
            record["abi"],
            tuple(args),
            blueprint=blueprint,
        )
        if bytes.fromhex(recorded_args) != expected_args:
            raise RuntimeError("MIGRATION_RESUMED_CONTRACT_INTENT_MISMATCH")
        try:
            creation_hex = compiled_contract["evm"]["bytecode"]["object"]
            if isinstance(creation_hex, str) and creation_hex.startswith("0x"):
                creation_hex = creation_hex[2:]
            if (
                not isinstance(creation_hex, str)
                or _CANONICAL_HEX_RE.fullmatch(creation_hex) is None
                or not creation_hex
            ):
                raise ValueError
            expected_code = b"\xfe\x71\x00" + bytes.fromhex(creation_hex)
        except (KeyError, TypeError, ValueError):
            raise RuntimeError("MIGRATION_RESUMED_BLUEPRINT_RECORD_INVALID") from None
        deployed_code = self._get_deployed_code(record.get("address"))
        if not deployed_code:
            raise RuntimeError("MIGRATION_RESUMED_BLUEPRINT_CODE_MISSING")
        if deployed_code != expected_code:
            raise RuntimeError("MIGRATION_RESUMED_BLUEPRINT_CODE_MISMATCH")

    def _register_contract(
        self,
        name,
        label,
        contract,
        args,
        *,
        blueprint=False,
    ):
        if self._last_run_was_resume:
            record = self._previous_manifest.get("contracts", {}).get(label)
            if not isinstance(record, dict):
                raise RuntimeError("MIGRATION_RESUMED_CONTRACT_RECORD_MISSING")
            logged_address = self._last_resumed_transaction
            raw_log_entry = self._last_resumed_transaction_raw
            recorded_address = record.get("address")
            legacy_blueprint = (
                blueprint
                and isinstance(raw_log_entry, str)
                and _LEGACY_BLUEPRINT_LOG_RE.fullmatch(raw_log_entry) is not None
            )
            if not isinstance(recorded_address, str) or (
                not legacy_blueprint
                and (
                    not isinstance(logged_address, str)
                    or logged_address.lower() != recorded_address.lower()
                )
            ):
                raise RuntimeError("MIGRATION_RESUMED_CONTRACT_LOG_ADDRESS_MISMATCH")
            if str(contract.address).lower() != recorded_address.lower():
                raise RuntimeError("MIGRATION_RESUMED_CONTRACT_ADDRESS_MISMATCH")
            self._validate_resumed_deployment_record(
                name,
                record,
                args,
                blueprint=blueprint,
            )
            self._contracts[label] = contract
            return contract
        self._contract_files[label] = name
        self._contracts[label] = contract
        self._args[label] = args
        self._append_manifest(label)
        self._save_log_file()
        return contract

    def deploy_bp(self, name):
        """
        Deploys contract with given name as blueprint or skips if already deployed
        Returns the deployed contract.
        """
        args = []
        kwargs = {}

        def deploy_bp_wrapper(*args, **kwargs):
            c = boa.load_partial(self._files[name]).deploy_as_blueprint()
            return c

        # ``name`` is also the manifest label needed by ``_run`` when a
        # durable deployment log is resumed.  The wrapper deliberately
        # accepts and ignores it on a fresh deployment.
        contract = self._run(
            name,
            deploy_bp_wrapper,
            *args,
            name=name,
            **kwargs,
        )
        return self._register_contract(
            name,
            name,
            contract,
            args,
            blueprint=True,
        )

    def deploy(self, name, *args, **kwargs):
        """
        Deploys contract with given name and args or skips if already deployed
        Returns the deployed contract.
        """
        label = kwargs.get("label", name)
        # remove label from kwargs
        kwargs.pop("label", None)

        contract = self._run(
            name, boa.load, self._files[name], *args, name=label, **kwargs
        )
        return self._register_contract(name, label, contract, args)

    def deploy_solidity(self, name, *args, **kwargs):
        """
        Deploys the Solidity contract with given name and args (built from `solidity/`
        with foundry) or skips if already deployed.
        Returns the deployed contract.
        """
        label = kwargs.pop("label", name)
        source_file = kwargs.pop("source_file", None)
        intent = solidity.deployment_intent(
            name,
            *args,
            sender=self._deploy_args.sender.address,
            chain=self._deploy_args.chain,
            source_file=source_file,
        )

        next_transaction = self._count + 1
        log.h2(
            f"Transaction {next_transaction} — Deploying {name}"
        )

        recorded = self._curr_transaction()
        if recorded is not None:
            if (
                not isinstance(recorded, dict)
                or set(recorded) != _SOLIDITY_DEPLOYMENT_LOG_FIELDS
                or any(recorded.get(key) != value for key, value in intent.items())
            ):
                raise RuntimeError("MIGRATION_SOLIDITY_DEPLOYMENT_INTENT_MISMATCH")
            address = recorded.get("address")
            if (
                not isinstance(address, str)
                or re.fullmatch(r"0x[0-9a-fA-F]{40}", address) is None
                or str(self.get_address(label)).lower() != address.lower()
            ):
                raise RuntimeError("MIGRATION_SOLIDITY_DEPLOYMENT_ADDRESS_MISMATCH")
            runtime = bytes(boa.env.get_code(address))
            if (
                not runtime
                or hashlib.sha256(runtime).hexdigest()
                != recorded.get("runtime_sha256")
            ):
                raise RuntimeError("MIGRATION_SOLIDITY_DEPLOYMENT_RUNTIME_MISMATCH")
            log.h3(f"Skipping transaction {next_transaction}")
            self._count += 1
            return solidity.at(name, address, source_file)

        contract = solidity.deploy(
            name,
            *args,
            sender=self._deploy_args.sender.address,
            source_file=source_file,
        )
        log.h3(f"Contract {name} deployed at {contract.address}")

        runtime = bytes(boa.env.get_code(contract.address))
        if not runtime:
            raise RuntimeError("MIGRATION_SOLIDITY_DEPLOYMENT_RUNTIME_MISSING")
        self._transactions.append(
            {
                **intent,
                "address": str(contract.address),
                "runtime_sha256": hashlib.sha256(runtime).hexdigest(),
            }
        )
        self._count += 1

        # The current manifest remains the canonical address index; the
        # transaction journal authenticates the Foundry artifact, constructor
        # payload, execution domain, address, and deployed runtime for resume.
        self.include_contract(label, str(contract.address))
        self._save_log_file()

        return contract

    def get_solidity_contract(self, name, address=None, source_file=None, label=None):
        """
        Returns a previously deployed Solidity contract, with the ABI from
        `solidity/`.
        """
        address = address or self.get_address(label or name)
        return solidity.at(name, address, source_file)

    def get_address_on_chain(self, chain, name):
        """
        Address of a contract deployed by another chain's migrations in the
        same environment.
        """
        filename = self._manifest_filename("current").replace(
            os.path.join("", self.chain(), ""), os.path.join("", chain, "")
        )
        return json_file.load(filename)["contracts"][name]["address"]

    def soft_deploy(self, name, *args, **kwargs):
        """
        Deploys contract with given name and args or skips if already deployed
        Returns the deployed contract.
        """
        contract = self._run(
            name, boa.load, self._files[name], *args, name=name, **kwargs
        )
        return self._register_contract(name, name, contract, args)

    def get_address(self, name):
        return self._previous_manifest["contracts"][name]["address"]

    def get_contract(self, name, address=None):
        file = self._previous_manifest["contracts"][name]["file"]
        address = address or self.get_address(name)
        # Attaching current source to an older deployed generation is expected
        # during replacement migrations. Boa's warning includes a full storage
        # dump (potentially thousands of lines), obscuring the actual operator
        # plan. Keep every other warning visible and suppress only this known
        # attachment warning in this narrow scope.
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=r"casted bytecode does not match compiled bytecode at ",
                category=UserWarning,
            )
            return boa.load_partial(file).at(address)

    def end(self):
        """
        Ends the migration and saves the manifest file
        """
        if self._count != len(self._transactions):
            raise RuntimeError("MIGRATION_TRANSACTION_LOG_UNCONSUMED")

        # A numbered manifest is a completed-migration checkpoint. During the
        # migration, deployments live only in a timestamp-scoped pending file;
        # neither a partial step nor a failed retry may become `current`.
        pending_filename = self._pending_manifest_filename()
        final_manifest = self._previous_manifest or {"contracts": {}}
        if os.path.exists(pending_filename):
            try:
                final_manifest = json_file.load(pending_filename)
            except Exception:
                raise RuntimeError("MIGRATION_PENDING_MANIFEST_INVALID") from None
        final_manifest = _validated_manifest(
            final_manifest,
            "MIGRATION_PENDING_MANIFEST_INVALID",
        )
        # Publish current first and the numeric completion marker last. If the
        # process dies between them, auto-resume selects this same migration
        # and its log/pending journal completes the checkpoint; it never skips
        # ahead with an old current manifest.
        json_file.save(self._manifest_filename("current"), final_manifest)
        json_file.save(
            self._manifest_filename(self._timestamp),
            _slim_step_manifest(final_manifest, self._contracts),
        )

        if os.path.exists(pending_filename):
            os.remove(pending_filename)
        if os.path.exists(self._log_filename()):
            os.remove(self._log_filename())

        log.info(f"Gas spent for migration: {self.gas}")

        return self.gas

    def account(self):
        return self._deploy_args.sender

    def chain(self):
        return self._deploy_args.chain

    def timestamp(self):
        return self._timestamp

    def previous_timestamp(self):
        return self._previous_timestamp

    def blueprint(self):
        return self._deploy_args.blueprint

    def include_contract(self, name, address):
        self._contracts[name] = address
        self._append_manifest(name)

    def promote_candidate(
        self,
        canonical_name,
        candidate_label,
        registry,
        registry_id,
        *,
        expected_source_path,
        registry_name,
        expected_constructor_args,
        activation_candidate_label=None,
        activation_dependency_arg_index=None,
        activation_expected_constructor_args=None,
    ):
        """Promote one authenticated candidate after authoritative readback."""
        return self.promote_candidates(
            [
                PromotionSpec(
                    canonical_name=canonical_name,
                    expected_source_path=expected_source_path,
                    candidate_label=candidate_label,
                    registry_name=registry_name,
                    registry=registry,
                    registry_id=registry_id,
                    expected_constructor_args=expected_constructor_args,
                    activation_candidate_label=activation_candidate_label,
                    activation_dependency_arg_index=(activation_dependency_arg_index),
                    activation_expected_constructor_args=(
                        activation_expected_constructor_args
                    ),
                )
            ]
        )[0]

    def _get_deployed_code(self, address):
        try:
            return bytes(boa.env.get_code(address))
        except Exception:
            raise RuntimeError("MIGRATION_CANDIDATE_CODE_READ_FAILED") from None

    def _validate_deployed_code(self, record, *, activation=False):
        kind = "ACTIVATION_CANDIDATE" if activation else "CANDIDATE"
        deployed_code = self._get_deployed_code(record.address)
        if not deployed_code:
            raise RuntimeError(f"MIGRATION_{kind}_DEPLOYED_CODE_MISSING")
        if len(deployed_code) != record.deployed_runtime_size:
            raise RuntimeError(f"MIGRATION_{kind}_DEPLOYED_CODE_LENGTH_MISMATCH")
        if not deployed_code.startswith(record.runtime_template):
            raise RuntimeError(f"MIGRATION_{kind}_DEPLOYED_CODE_PREFIX_MISMATCH")

    @staticmethod
    def _validate_registry_identity(contracts, spec):
        registry_record = contracts.get(spec.registry_name)
        if not isinstance(registry_record, dict):
            raise RuntimeError("MIGRATION_PROMOTION_REGISTRY_RECORD_MISSING")
        recorded_address = registry_record.get("address")
        registry_address = getattr(spec.registry, "address", None)
        if (
            not isinstance(recorded_address, str)
            or registry_address is None
            or recorded_address.lower() != str(registry_address).lower()
        ):
            raise RuntimeError("MIGRATION_PROMOTION_REGISTRY_IDENTITY_MISMATCH")

    def promote_candidates(self, promotions):
        """Atomically promote a preflighted set of authenticated candidates.

        Deployment and registry activation are intentionally separate steps.
        Every source/compiler/ABI/constructor/dependency/registry condition is
        validated before the pending manifest is written once. Candidate
        records are copied whole so stale metadata cannot survive promotion.
        """
        if not isinstance(promotions, (list, tuple)) or not promotions:
            raise RuntimeError("MIGRATION_PROMOTION_BATCH_INVALID")

        contracts = self._previous_manifest.get("contracts")
        if not isinstance(contracts, dict):
            raise RuntimeError("MIGRATION_MANIFEST_CONTRACTS_MISSING")
        validated = []
        canonical_names = set()
        for spec in promotions:
            if not isinstance(spec, PromotionSpec):
                raise RuntimeError("MIGRATION_PROMOTION_BATCH_INVALID")
            canonical_name = spec.canonical_name
            candidate_label = spec.candidate_label
            registry_id = spec.registry_id
            if canonical_name in canonical_names:
                raise RuntimeError("MIGRATION_PROMOTION_CANONICAL_DUPLICATE")
            canonical_names.add(canonical_name)
            if candidate_label not in contracts:
                raise RuntimeError("MIGRATION_CANDIDATE_CONTRACT_MISSING")
            self._validate_registry_identity(contracts, spec)

            activation_label = spec.activation_candidate_label or candidate_label
            if activation_label not in contracts:
                raise RuntimeError("MIGRATION_ACTIVATION_CANDIDATE_CONTRACT_MISSING")

            candidate = contracts[candidate_label]
            expected_source_path = self._expected_source_path(
                canonical_name,
                spec.expected_source_path,
            )
            validated_candidate = _validated_promotable_record(
                candidate,
                expected_source_path=expected_source_path,
                expected_constructor_args=spec.expected_constructor_args,
            )
            candidate_address = validated_candidate.address
            self._validate_deployed_code(validated_candidate)
            activation_candidate = contracts[activation_label]
            if activation_label == candidate_label:
                activation_address = candidate_address
                if (
                    spec.activation_dependency_arg_index is not None
                    or spec.activation_expected_constructor_args is not None
                ):
                    raise RuntimeError("MIGRATION_ACTIVATION_DEPENDENCY_INVALID")
            else:
                if spec.activation_dependency_arg_index is None:
                    raise RuntimeError("MIGRATION_ACTIVATION_DEPENDENCY_REQUIRED")
                if spec.activation_expected_constructor_args is None:
                    raise RuntimeError(
                        "MIGRATION_ACTIVATION_CONSTRUCTOR_INTENT_REQUIRED"
                    )
                matching_policies = [
                    policy
                    for policy in _DISTINCT_ACTIVATION_POLICIES
                    if policy[0] == canonical_name
                    and policy[1] == expected_source_path
                    and policy[3] == spec.registry_name
                    and policy[4] == registry_id
                    and policy[5] == spec.activation_dependency_arg_index
                ]
                if len(matching_policies) != 1:
                    raise RuntimeError("MIGRATION_ACTIVATION_DEPENDENCY_UNSUPPORTED")
                activation_source_path = matching_policies[0][2]
                validated_activation = _validated_promotable_record(
                    activation_candidate,
                    expected_source_path=activation_source_path,
                    expected_constructor_args=(
                        spec.activation_expected_constructor_args
                    ),
                    activation=True,
                )
                activation_address = validated_activation.address
                self._validate_deployed_code(
                    validated_activation,
                    activation=True,
                )
                _validate_activation_dependency(
                    activation_candidate,
                    candidate_address,
                    spec.activation_dependency_arg_index,
                )

            registry_address = str(spec.registry.getAddr(registry_id))
            if registry_address.lower() != activation_address.lower():
                raise RuntimeError("MIGRATION_CANDIDATE_REGISTRY_MISMATCH")
            validated.append(
                (
                    canonical_name,
                    candidate_label,
                    activation_label,
                    candidate,
                    candidate_address,
                )
            )

        # A canonical label may be absent when this is the first deployment of
        # a new component.  The candidate and its activation witness still
        # have to be complete, nonzero manifest records and the authoritative
        # registry readback above must prove the activation before the label is
        # created.  Existing canonicals follow this exact same replacement
        # path, so no stale metadata can leak into either case.
        promoted_manifest = copy.deepcopy(self._previous_manifest)
        for (
            canonical_name,
            _label,
            _activation,
            candidate,
            address,
        ) in validated:
            promoted_manifest["contracts"][canonical_name] = copy.deepcopy(candidate)
            # Promotion bypasses `_register_contract`, which is the usual
            # place `self._contracts` gets a new key. `end()` slims the step
            # manifest to exactly the names in `self._contracts`, so without
            # this a promoted contract would be silently absent from its own
            # step manifest's attribution.
            self._contracts[canonical_name] = address
        # A pending manifest is resumable only when its timestamp log exists.
        # Persist the (possibly empty) transaction list first. A crash after the
        # subsequent manifest save can then reload this same local checkpoint.
        self._save_log_file()
        json_file.save(self._pending_manifest_filename(), promoted_manifest)
        self._previous_manifest = promoted_manifest
        for (
            canonical_name,
            candidate_label,
            activation_label,
            _candidate,
            _address,
        ) in validated:
            log.h3(
                f"{candidate_label} promoted to {canonical_name} in pending "
                f"manifest after {activation_label} registry readback"
            )
        return tuple(item[4] for item in validated)

    def include_abis(self, contracts):
        keys = self._contracts.keys()
        for contract in contracts:
            if not contract in keys:
                self._contracts[contract] = ""
            self._append_manifest(contract)

    def _curr_transaction(self):
        """
        Returns the current transaction if it's been already executed.
        """
        if self._count == len(self._transactions):
            return None
        return self._transactions[self._count]

    def _transaction_intent(self, transaction, args, kwargs):
        """Bind a resumable call to its execution domain and exact EVM intent."""
        contract = getattr(transaction, "contract", None)
        target = getattr(contract, "address", None)
        prepare_calldata = getattr(transaction, "prepare_calldata", None)
        target_text = str(target).lower() if target is not None else ""
        if (
            re.fullmatch(r"0x[0-9a-f]{40}", target_text) is None
            or not callable(prepare_calldata)
        ):
            raise RuntimeError("MIGRATION_TRANSACTION_INTENT_UNAVAILABLE")

        call_kwargs = {
            name: value
            for name, value in kwargs.items()
            if name not in _BOA_CALL_OPTION_NAMES
        }
        try:
            calldata = prepare_calldata(*args, **call_kwargs)
            calldata = bytes(calldata)
        except Exception:
            raise RuntimeError("MIGRATION_TRANSACTION_CALLDATA_INVALID") from None

        sender = str(self._deploy_args.sender.address).lower()
        chain = str(self._deploy_args.chain)
        value = kwargs.get("value", 0)
        if (
            re.fullmatch(r"0x[0-9a-f]{40}", sender) is None
            or not chain
            or isinstance(value, bool)
            or not isinstance(value, int)
            or value < 0
        ):
            raise RuntimeError("MIGRATION_TRANSACTION_INTENT_UNAVAILABLE")

        return {
            "version": _TRANSACTION_LOG_VERSION,
            "kind": "call",
            "chain": chain,
            "sender": sender,
            "target": target_text,
            "calldata_sha256": hashlib.sha256(calldata).hexdigest(),
            "value": value,
        }

    @staticmethod
    def _resume_transaction(record, intent):
        if not isinstance(record, dict) or set(record) != _TRANSACTION_LOG_FIELDS:
            raise RuntimeError("MIGRATION_TRANSACTION_LOG_UNAUTHENTICATED")
        if (
            record.get("version") != _TRANSACTION_LOG_VERSION
            or record.get("kind") != "call"
        ):
            raise RuntimeError("MIGRATION_TRANSACTION_LOG_UNAUTHENTICATED")
        if record.get("chain") != intent["chain"]:
            raise RuntimeError("MIGRATION_TRANSACTION_CHAIN_MISMATCH")
        if record.get("sender") != intent["sender"]:
            raise RuntimeError("MIGRATION_TRANSACTION_SENDER_MISMATCH")
        if record.get("target") != intent["target"]:
            raise RuntimeError("MIGRATION_TRANSACTION_TARGET_MISMATCH")
        if record.get("calldata_sha256") != intent["calldata_sha256"]:
            raise RuntimeError("MIGRATION_TRANSACTION_CALLDATA_MISMATCH")
        if record.get("value") != intent["value"]:
            raise RuntimeError("MIGRATION_TRANSACTION_VALUE_MISMATCH")
        receipt = record.get("receipt")
        if not isinstance(receipt, (str, int, bool)) or receipt == "":
            raise RuntimeError("MIGRATION_TRANSACTION_RECEIPT_INVALID")
        return receipt

    @staticmethod
    def _transaction_record(intent, receipt):
        if not isinstance(receipt, (str, int, bool)):
            receipt = str(receipt)
        return {**intent, "receipt": receipt}

    def _clean_message(self, message, contract_name, *args):
        if contract_name != "":
            return f"Deploying {contract_name}"

        if "ABI " in message:
            try:
                abi_part = message.split("ABI ")[1]
                parts = abi_part.split(".vy.")
                contract_name = parts[0].split("/")[-1]
                return f"{contract_name}.{parts[1]} - {args}"
            except:
                return message

        return message

    def _run(self, contract_name, transaction, *args, **kwargs):
        """
        Executes a transaction or skips if already executed.
        Returns the transaction receipt as string.
        """
        self._last_run_was_resume = False
        self._last_resumed_transaction = None
        self._last_resumed_transaction_raw = None
        next_transaction = self._count + 1
        message = self._clean_message(str(transaction), contract_name, *args)
        intent = None
        if contract_name == "":
            intent = self._transaction_intent(transaction, args, kwargs)

        log.h2(
            f"Transaction {next_transaction} — {message}"
        )

        recorded = self._curr_transaction()

        if recorded is None:
            # Only include sender in kwargs if contract_name is empty
            if contract_name == "":
                kwargs["sender"] = self._deploy_args.sender.address

            tx = execute_transaction(transaction, *args, **kwargs)
            if tx is None:
                raise RuntimeError("MIGRATION_TRANSACTION_RESULT_MISSING")
            self._transactions.append(
                self._transaction_record(intent, tx)
                if contract_name == ""
                # Deployment objects stringify to verbose representations,
                # and a VyperBlueprint string contains only a Python memory
                # address. Persist the actual chain address so a restart can
                # authenticate the journal against the pending manifest.
                else str(tx.address)
            )
            gas = 0
            if contract_name != "":
                if hasattr(tx, "_computation") and tx._computation is not None:
                    gas = tx._computation.get_gas_used()
                log.h3(f"Contract {contract_name} deployed at {tx.address}")
            else:
                log.h3(f"Transaction confirmed")
                try:
                    contract_name = message.split(".")[0]
                    contract = self._contracts[contract_name]
                    gas = contract._computation.get_gas_used()
                except:
                    pass
            self.gas += gas

        else:
            log.h3(f"Skipping transaction {next_transaction}")
            self._last_run_was_resume = True
            if contract_name == "":
                tx = self._resume_transaction(recorded, intent)
                self._last_resumed_transaction = str(tx)
            else:
                self._last_resumed_transaction_raw = str(recorded)
                self._last_resumed_transaction = _deployment_address_from_log(
                    str(recorded)
                )
                tx = recorded
            if contract_name != "":
                self._count += 1
                return self.get_contract(kwargs["name"])

        self._count += 1
        return tx

    def _log_filename(self):
        return os.path.join(self._history_path, f"{self._timestamp}-log.json")

    def _manifest_filename(self, name):
        return os.path.join(self._history_path, f"{name}-manifest.json")

    def _pending_manifest_filename(self):
        return os.path.join(
            self._history_path, f"{self._timestamp}-pending-manifest.json"
        )

    def _append_manifest(self, contract_name):
        contract = self._contracts[contract_name]
        contracts = {contract_name: contract}

        manifest = deployed_contracts_manifest(
            contracts, self._contract_files, self._args, self._files
        )
        merged_manifest = merge({}, self._previous_manifest, manifest)
        self._previous_manifest = merged_manifest

        json_file.save(self._pending_manifest_filename(), merged_manifest)

        log.detail(f"{contract_name} added to pending manifest")
        return merged_manifest

    def _load_log_file(self):
        logs = json_file.load(self._log_filename())
        if (
            not isinstance(logs, dict)
            or set(logs) != {"transactions"}
            or not isinstance(logs["transactions"], list)
        ):
            raise RuntimeError("MIGRATION_TRANSACTION_LOG_INVALID")
        self._transactions = logs["transactions"]

    def _save_log_file(self):
        def serializable(value):
            if isinstance(value, dict):
                return copy.deepcopy(value)
            return str(value)

        json_file.save(
            self._log_filename(),
            {
                "transactions": [serializable(tx) for tx in self._transactions],
            },
        )

    def getArgument(self, name):
        return self._deploy_args[name]
