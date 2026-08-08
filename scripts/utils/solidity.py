"""
Compile and deploy the Solidity contracts that live in `solidity/`.

Vyper contracts are deployed by boa straight from source. Solidity contracts are built
with foundry (`forge build`, settings in `solidity/foundry.toml`) and deployed from the
resulting artifact, so they go through the exact same migration bookkeeping.
"""

import json
import os
import subprocess

import boa
from eth_abi.abi import encode

from scripts.utils import log

SOLIDITY_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "solidity",
)


_built = False


def build(force=False):
    """
    Compiles `solidity/` with foundry, once per run.
    """
    global _built
    if _built and not force:
        return

    try:
        subprocess.run(
            ["forge", "build", "--root", SOLIDITY_DIR],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        raise Exception(
            "`forge` not found. Install foundry (https://getfoundry.sh) to build the "
            "Solidity contracts in solidity/"
        )
    except subprocess.CalledProcessError as exception:
        raise Exception(f"forge build failed:\n{exception.stdout}\n{exception.stderr}")

    _built = True


def artifact(name, source_file=None):
    """
    Returns the foundry artifact (abi + bytecode) for the contract named `name`.
    """
    build()
    filename = os.path.join(SOLIDITY_DIR, "out", source_file or f"{name}.sol", f"{name}.json")
    if not os.path.exists(filename):
        raise Exception(f"No foundry artifact for {name} (looked in {filename})")

    return json.load(open(filename))


def abi(name, source_file=None):
    return artifact(name, source_file)["abi"]


def at(name, address, source_file=None):
    """
    Returns a contract object for an already deployed Solidity contract.
    """
    contract_abi = abi(name, source_file)
    return boa.loads_abi(json.dumps(contract_abi), name=name).at(address)


def deploy(name, *args, sender=None, source_file=None):
    """
    Deploys a Solidity contract with the given constructor args.
    Returns the deployed contract.
    """
    contract_artifact = artifact(name, source_file)
    bytecode = bytes.fromhex(_strip_hex(contract_artifact["bytecode"]["object"]))

    constructor = next(
        (item for item in contract_artifact["abi"] if item.get("type") == "constructor"),
        None,
    )
    if constructor is not None and constructor["inputs"]:
        types = [_abi_type(item) for item in constructor["inputs"]]
        bytecode += encode(types, [_arg(arg) for arg in args])

    address, computation = boa.env.deploy(sender=sender, bytecode=bytecode)
    if computation.is_error:
        raise computation.error

    return at(name, address, source_file)


def constructor_args(name, *args, source_file=None):
    """
    Abi encoded constructor args, as `forge verify-contract --constructor-args` wants them.
    """
    constructor = next(
        (item for item in abi(name, source_file) if item.get("type") == "constructor"),
        None,
    )
    if constructor is None or not constructor["inputs"]:
        return ""

    types = [_abi_type(item) for item in constructor["inputs"]]
    return "0x" + encode(types, [_arg(arg) for arg in args]).hex()


# forge rejects our internal chain names and needs the EVM chain id, and it needs
# to be told when an explorer is Blockscout rather than Etherscan. Keyed by the
# chain names `scripts/migrate.py --chain` accepts.
VERIFY_TARGETS = {
    # Etherscan's V2 API is multichain off a single key, which is why both
    # Base networks read ETHERSCAN_API_KEY rather than a Basescan-specific one.
    # Note migrate.py's boa integration uses BASESCAN_API_KEY separately -- two
    # tools, two keys.
    "base-mainnet": {
        "chain_id": 8453,
        "verifier": None,  # etherscan, forge's default
        "verifier_url": None,
        "key_env": "ETHERSCAN_API_KEY",
    },
    "base-sepolia": {
        "chain_id": 84532,
        "verifier": None,
        "verifier_url": None,
        "key_env": "ETHERSCAN_API_KEY",
    },
    "robinhood-mainnet": {
        "chain_id": 4663,
        "verifier": "blockscout",
        "verifier_url": "https://robinhoodchain.blockscout.com/api",
        "key_env": "BLOCKSCOUT_API_KEY",
    },
}


def verify_command(migration, name, *args, source_file=None, label=None):
    """
    The `forge verify-contract` command for a deployed Solidity contract, as a
    string - boa's etherscan verification only knows how to bundle Vyper sources.

    `label` is the manifest key, which differs from `name` when the same contract is
    deployed more than once. `source_file` is the file name within `src/`, needed
    when it does not match the contract name - two pools share one file here.
    """
    chain = migration.chain()
    address = migration.get_address(label or name)
    target = VERIFY_TARGETS.get(chain)

    # forge resolves the contract path relative to the foundry root, so it always
    # needs the `src/` prefix -- passing a bare file name fails to resolve.
    path = f"src/{source_file or f'{name}.sol'}:{name}"

    if target is None:
        return f"# no verifier configured for {chain}; {name} is at {address}"

    lines = [
        f"forge verify-contract --root solidity --chain {target['chain_id']} \\",
        f"    --constructor-args {constructor_args(name, *args, source_file=source_file)} \\",
    ]
    if target["verifier"]:
        lines.append(f"    --verifier {target['verifier']} \\")
        lines.append(f"    --verifier-url {target['verifier_url']} \\")
    lines.append(f"    --etherscan-api-key ${target['key_env']} \\")
    lines.append(f"    {address} {path}")
    return "\n".join(lines)


def log_verify_command(migration, name, *args, source_file=None, label=None):
    """Logs the `forge verify-contract` command for a deployed Solidity contract."""
    command = verify_command(
        migration, name, *args, source_file=source_file, label=label
    )
    log.info(f"To verify {name}, run:\n    " + command.replace("\n", "\n    "))


def _abi_type(item):
    # tuples carry their component types in `components`, everything else is flat
    if item["type"].startswith("tuple"):
        components = ",".join(_abi_type(component) for component in item["components"])
        return f"({components}){item['type'][len('tuple'):]}"
    return item["type"]


def _arg(arg):
    # accept deployed contracts / accounts wherever an address is expected
    if hasattr(arg, "address"):
        return str(arg.address)
    if isinstance(arg, (list, tuple)):
        return type(arg)(_arg(item) for item in arg)
    return arg


def _strip_hex(value):
    return value[2:] if value.startswith("0x") else value
