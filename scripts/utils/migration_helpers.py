import json
import os
import re
import time
import subprocess
from collections.abc import Mapping

from eth_abi.abi import encode
from eth_account import Account
from eth_utils.abi import function_abi_to_4byte_selector

from config.network_profiles import (
    get_profile,
    NetworkProfileError,
    Operation,
    VerifiedNetworkIdentity,
    validate_verified_identity,
)
from scripts.utils import log

# Define constants for directories
CONTRACTS_DIR = "./contracts"
INTERFACES_DIR = "./interfaces"


class TransactionExecutionError(RuntimeError):
    """A migration transaction never produced a confirmed result."""


NO_OUTPUT_TRANSACTION_RESULT = "MIGRATION_TRANSACTION_CONFIRMED_NO_OUTPUT"
_BOA_CALL_OPTION_NAMES = frozenset(("gas", "sender", "simulate", "value"))


def _transaction_abi_entry(transaction, args=(), kwargs=None):
    """Return explicit callable ABI metadata, or ``None`` if it is ambiguous."""
    direct_abi = getattr(transaction, "_abi", None)
    if isinstance(direct_abi, Mapping):
        return direct_abi

    # Boa's source-backed VyperFunction keeps the ABI on its contract and the
    # function name on its AST node. ABI-backed Boa functions take the direct
    # path above. A Vyper function with default arguments has one ABI entry for
    # every callable arity, so resolve that expansion from the exact arguments
    # that were accepted by the bound callable instead of treating it as an
    # unknown overload.
    function_ast = getattr(transaction, "fn_ast", None)
    function_name = getattr(function_ast, "name", None)
    contract = getattr(transaction, "contract", None)
    contract_abi = getattr(contract, "abi", None)
    if not isinstance(function_name, str) or not isinstance(contract_abi, list):
        return None

    matches = [
        entry
        for entry in contract_abi
        if isinstance(entry, Mapping)
        and entry.get("type") == "function"
        and entry.get("name") == function_name
    ]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        return None

    func_type = getattr(transaction, "func_t", None)
    args_abi_type = getattr(transaction, "args_abi_type", None)
    required_args = getattr(func_type, "n_positional_args", None)
    total_args = getattr(func_type, "n_total_args", None)
    if (
        not callable(args_abi_type)
        or isinstance(required_args, bool)
        or not isinstance(required_args, int)
        or isinstance(total_args, bool)
        or not isinstance(total_args, int)
    ):
        return None

    supplied_kwargs = kwargs or {}
    abi_kwarg_count = sum(
        key not in _BOA_CALL_OPTION_NAMES for key in supplied_kwargs
    )
    supplied_args = len(args) + abi_kwarg_count
    if not required_args <= supplied_args <= total_args:
        return None

    try:
        selector, _ = args_abi_type(supplied_args - required_args)
        selected = [
            entry
            for entry in matches
            if function_abi_to_4byte_selector(entry) == selector
        ]
    except Exception:
        return None
    if len(selected) != 1:
        return None
    return selected[0]


def _declares_zero_outputs(transaction, args=(), kwargs=None):
    abi_entry = _transaction_abi_entry(transaction, args, kwargs)
    return (
        abi_entry is not None
        and abi_entry.get("type") == "function"
        and abi_entry.get("outputs") == []
    )


def load_vyper_files(directories=[CONTRACTS_DIR, INTERFACES_DIR], excluded_dirs=("testing",)):
    """
    Load all Vyper files from the specified directories and their subdirectories.
    Returns relative paths from the project root.
    """
    vyper_files = {}

    for directory in directories:
        if not os.path.exists(directory):
            continue

        for root, _, files in os.walk(directory):
            if any(excluded in os.path.normpath(root).split(os.sep) for excluded in excluded_dirs):
                continue
            for file in files:
                if file.endswith('.vy'):
                    # Get the relative path from the current directory
                    rel_path = os.path.relpath(os.path.join(root, file))
                    # Remove .vy extension from the key
                    key = file[:-3] if file.endswith('.vy') else file
                    vyper_files[key] = rel_path

    return vyper_files


def get_account(
    account_name: str,
    identity: VerifiedNetworkIdentity,
    operation: Operation,
    *,
    environ: Mapping[str, str] | None = None,
    private_key: str | None = None,
    local_test_only: bool = False,
):
    """Load an account only after an explicit, verified operation context."""
    if not isinstance(identity, VerifiedNetworkIdentity):
        raise NetworkProfileError(
            "H02_CHAIN_ID_MISMATCH", operation=operation
        )
    profile = get_profile(identity.profile_id)
    validate_verified_identity(
        profile,
        operation,
        identity,
        require_account=True,
    )
    if not re.fullmatch(r"[A-Z][A-Z0-9_]*", account_name):
        raise NetworkProfileError(
            "H02_ACCOUNT_BACKEND_UNAPPROVED",
            profile_id=profile.identity.profile_id,
            operation=operation,
        )

    if local_test_only:
        if (
            identity.profile_id != "local"
            or operation is not Operation.LOCAL_RUNTIME
            or private_key is None
        ):
            raise NetworkProfileError(
                "H02_ACCOUNT_BACKEND_UNAPPROVED",
                profile_id=profile.identity.profile_id,
                operation=operation,
            )
        account_key = private_key
    else:
        if private_key is not None or operation not in (
            Operation.MIGRATION_FORK,
            Operation.MIGRATION_LIVE,
        ):
            raise NetworkProfileError(
                "H02_ACCOUNT_BACKEND_UNAPPROVED",
                profile_id=profile.identity.profile_id,
                operation=operation,
            )
        env_name = f"{account_name}_PRIVATE_KEY"
        values = os.environ if environ is None else environ
        try:
            account_key = values[env_name]
        except KeyError:
            raise NetworkProfileError(
                "H02_PRIVATE_KEY_MISSING",
                profile_id=profile.identity.profile_id,
                operation=operation,
                env_name=env_name,
            ) from None
        if not account_key:
            raise NetworkProfileError(
                "H02_PRIVATE_KEY_MISSING",
                profile_id=profile.identity.profile_id,
                operation=operation,
                env_name=env_name,
            )

    log.h1(f"Connecting to deployer account {account_name}")
    try:
        account = Account.from_key(account_key)
    except Exception:
        raise NetworkProfileError(
            "H02_PRIVATE_KEY_INVALID",
            profile_id=profile.identity.profile_id,
            operation=operation,
        ) from None
    log.h2(f"Deployer account {account_name} connected")
    return account


def execute_transaction(transaction, *args, **kwargs):
    attempts = 0
    # State-changing exceptions are not safely retryable by default: an RPC
    # provider can raise after broadcast but before returning a receipt.  A
    # caller may opt into a larger budget only for an operation it has already
    # established is idempotent or receipt-reconciled.
    max_attempts = 1
    if "max_attempts" in kwargs:
        max_attempts = kwargs["max_attempts"]
        kwargs.pop("max_attempts")
    if "no_retry" in kwargs:
        max_attempts = 1
        kwargs.pop("no_retry")

    if isinstance(max_attempts, bool) or not isinstance(max_attempts, int):
        raise TransactionExecutionError("MIGRATION_ATTEMPTS_INVALID")
    if max_attempts <= 0:
        raise TransactionExecutionError("MIGRATION_ATTEMPTS_INVALID")

    while attempts < max_attempts:
        attempts += 1
        try:
            result = transaction(*args, **kwargs)
        except Exception as exception:
            log.info(
                "\tTransaction Failed "
                + str(attempts)
                + " time"
                + ("s" if attempts > 1 else "")
                + (
                    " (Trying again in 3 seconds)"
                    if attempts < max_attempts
                    else ""
                )

            )
            # Exception text is NOT logged by default: it can carry provider
            # URLs, keys, or calldata, and what a driver puts in a message
            # cannot be enumerated in advance. Retrying twenty times on a
            # deterministic revert with only a code is painful to debug, so
            # RIPE_MIGRATE_TRACE=1 opts in to the cause, with complete URLs
            # stripped. Preserving the authority is unsafe because an RPC URL
            # may carry HTTP basic-auth credentials as userinfo.
            if os.environ.get("RIPE_MIGRATE_TRACE"):
                detail = re.sub(
                    r"(?i)\b(?:https?|wss?)://[^\s\"'<>]+",
                    "<redacted-url>",
                    f"{type(exception).__name__}: {exception}",
                )
                log.error(f"\tH02_TRANSACTION_FAILED {detail}\n")
            else:
                log.error("\tH02_TRANSACTION_FAILED\n")
            if attempts == max_attempts:
                log.error("\tMax attempts reached. Failing closed.\n")
                raise TransactionExecutionError(
                    "MIGRATION_TRANSACTION_FAILED"
                ) from None

            time.sleep(3)
            continue

        # A call can commit onchain and still surface Python ``None``.  That is
        # a post-call reconciliation failure, not a transient pre-submission
        # exception: retrying it could repeat a non-idempotent transaction.
        if result is None:
            if _declares_zero_outputs(transaction, args, kwargs):
                return NO_OUTPUT_TRANSACTION_RESULT
            log.error("\tH02_TRANSACTION_RESULT_MISSING\n")
            raise TransactionExecutionError(
                "MIGRATION_TRANSACTION_RESULT_MISSING"
            )
        return result


def execute_vyper_json_command(file_path, command):
    cmd = f"vyper {file_path} -f {command}"
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            shell=True
        )
        if result.returncode == 0:
            # Parse the JSON output immediately
            return json.loads(result.stdout)
        else:
            raise Exception(f"Vyper compilation failed: {result.stderr}")
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse JSON output from vyper: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to execute vyper command: {str(e)}")


def get_vyper_abi(file_path):
    return execute_vyper_json_command(file_path, "abi")


def get_contract_abi(contract_name, contract, files):
    if (contract != '' and contract.abi):
        return contract.abi
    return get_vyper_abi(files[contract_name])


def write_contract_abi(abis_dir, contract_name):
    """
    Write an ABI file for the specified `contract_name` to `abis_dir`.
    Returns the ABI JSON as string.
    """
    # create the directory if it doesn't already exist
    os.makedirs(abis_dir, exist_ok=True)

    contract_abis = get_contract_abi(contract_name)
    filename = os.path.join(abis_dir, f"{contract_name}.json")
    with open(filename, "w") as outfile:
        json.dump(contract_abis, outfile, indent=2)

    return json.dumps(contract_abis)


def canonical_abi_input_type(input_: Mapping) -> str:
    """Return the canonical eth-abi type for one JSON ABI input."""
    abi_type = input_.get("type")
    if not isinstance(abi_type, str):
        raise ValueError("invalid ABI input type")
    if not abi_type.startswith("tuple"):
        return abi_type

    components = input_.get("components")
    if not isinstance(components, list):
        raise ValueError("tuple ABI input has no components")
    suffix = abi_type[len("tuple") :]
    return (
        "("
        + ",".join(canonical_abi_input_type(component) for component in components)
        + ")"
        + suffix
    )


def normalize_abi_argument(value):
    """Replace Boa contract objects with addresses, including inside structs."""
    if hasattr(value, "address"):
        return value.address
    if isinstance(value, (tuple, list)):
        return tuple(normalize_abi_argument(item) for item in value)
    return value


def encode_abi_inputs(inputs: list, args) -> bytes:
    """Encode values against JSON ABI inputs, including nested Vyper structs."""
    return encode(
        [canonical_abi_input_type(input_) for input_ in inputs],
        [normalize_abi_argument(arg) for arg in args],
    )


def encode_constructor_args(abi: list, args: list) -> str:
    """
    Encode constructor arguments based on the contract's ABI
    Returns hex string without '0x' prefix
    """
    # Find the constructor in the ABI
    constructor = next(
        (item for item in abi if item.get('type') == 'constructor'), None)
    if not constructor or not args:
        return ""

    return encode_abi_inputs(constructor["inputs"], args).hex()


def deployed_contracts_manifest(contracts: dict, contract_files: dict, args: dict, files: dict):
    """
    Generate manifest file that maps each deployed contract to its address.
    """
    manifest = {}

    for contract_name in contracts.keys():
        if not hasattr(contracts[contract_name], "address"):
            manifest[contract_name] = {
                "address": contracts[contract_name],
            }
        else:
            manifest[contract_name] = {
                "address": contracts[contract_name].address,
                "abi": get_vyper_abi(files[contract_files[contract_name]]),
                "solc_json": contracts[contract_name].deployer.solc_json,
                "args": encode_constructor_args(get_vyper_abi(files[contract_files[contract_name]]), args[contract_name]),
                "file": files[contract_files[contract_name]]
            }

    return {"contracts": manifest}
