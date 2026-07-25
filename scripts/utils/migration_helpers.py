import json
import os
import re
import time
import subprocess
from collections.abc import Mapping

from eth_abi.abi import encode
from eth_account import Account

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
        if private_key is not None or operation is not Operation.MIGRATION_FORK:
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
    max_attempts = 20
    if "max_attempts" in kwargs:
        max_attempts = kwargs["max_attempts"]
        kwargs.pop("max_attempts")
    if "no_retry" in kwargs:
        max_attempts = 1
        kwargs.pop("no_retry")

    while attempts < max_attempts:
        attempts += 1
        try:
            return transaction(*args, **kwargs)

        except Exception as exception:
            if "NoneType" in str(exception):
                return None

            log.info(
                "\tTransaction Failed "
                + str(attempts)
                + " time"
                + ("s" if attempts > 1 else "")
                + (" (Trying again in 3 seconds)")

            )
            log.error(f"\tException: {str(exception)}\n")
            if attempts == max_attempts:
                log.error(f"\tMax attempts reached. Exiting.\n")
                break

            time.sleep(3)


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

    # Get the input types from the constructor
    input_types = [input_['type'] for input_ in constructor['inputs']]

    # Convert objects with address attribute to their address
    processed_args = []
    for arg in args:
        if hasattr(arg, 'address'):
            processed_args.append(arg.address)
        else:
            processed_args.append(arg)

    # Encode the arguments
    encoded = encode(input_types, processed_args)
    return encoded.hex()


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
