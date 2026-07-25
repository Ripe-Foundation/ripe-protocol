"""
Interactive IPython console for an explicitly selected, verified fork.

Usage:
    python -m scripts.console [OPTIONS]

Examples:
    python -m scripts.console --profile base-mainnet
    python -m scripts.console --chain base-sepolia
    python -m scripts.console --account 0x1234...  # Impersonate specific address
"""

import os
from contextlib import ExitStack
from pathlib import Path

import click
import boa
from boa.rpc import EthereumRPC

from config.network_profiles import (
    NETWORK_PROFILE_IDS,
    NetworkProfileError,
    Operation,
    get_profile,
    repository_paths,
    require_operation,
    resolve_rpc_reference,
    validate_fork_request,
    verify_chain_identity,
)
from scripts.utils import json_file, log
from scripts.utils.migration_helpers import load_vyper_files

ROOT = Path(__file__).resolve().parents[1]


class ContractNameCompleter:
    """
    Callable that provides autocomplete for contract names.

    Usage:
        c.Contract.Teller("0x...")  # Load Teller ABI at custom address
    """

    def __init__(self, console: "Console"):
        self._console = console

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)

        def load_at_address(address: str):
            return self._console.get_contract(name, address)

        return load_at_address

    def __dir__(self):
        return list(self._console._manifest.get("contracts", {}).keys())

    def __repr__(self):
        return "<ContractNameCompleter - use c.Contract.Name('0x...') to load at custom address>"


class ContractAccessor:
    """
    Provides attribute-style access to contracts with autocomplete.

    Usage:
        c.Teller                    # Returns the Teller contract at manifest address
        c.Contract.Teller("0x...")  # Returns Teller ABI at custom address
    """

    def __init__(self, console: "Console"):
        self._console = console
        self._cache = {}
        self.Contract = ContractNameCompleter(console)

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)

        if name in self._cache:
            return self._cache[name]

        contract = self._console.get_contract(name)
        self._cache[name] = contract
        return contract

    def __dir__(self):
        # This enables autocomplete in IPython
        return list(self._console._manifest.get("contracts", {}).keys()) + ["Contract"]

    def __repr__(self):
        return f"<ContractAccessor with {len(self._console._manifest.get('contracts', {}))} contracts - use Tab for autocomplete>"


class Console:
    """
    Interactive console helper with access to deployed contracts.

    Attributes:
        c: ContractAccessor with autocomplete (c.Teller, c.CreditEngine, etc.)
        contracts: Dict of contract name -> contract instance (cached)
        addresses: Dict of contract name -> address string
        boa: The boa module for direct access
    """

    def __init__(
        self,
        profile_id: str,
        operation: Operation,
        mode: str,
        manifest_path: Path | None,
    ):
        self._profile_id = profile_id
        self._operation = operation
        self._mode = mode
        self._manifest_path = manifest_path
        self._manifest = {}
        self._contracts = {}
        self._files = load_vyper_files()
        self._load_manifest()
        self.c = ContractAccessor(self)

    def _load_manifest(self):
        """Load the current manifest file."""
        if self._manifest_path is None:
            self._manifest = {"contracts": {}}
            log.h3("No repository manifest is available for this profile.")
            return
        try:
            self._manifest = json_file.load(str(self._manifest_path))
            log.h3(
                "Loaded profile-owned manifest "
                f"{self._manifest_path.relative_to(ROOT)}"
            )
        except Exception:
            raise NetworkProfileError(
                "H02_REPOSITORY_UNAVAILABLE",
                profile_id=self._profile_id,
                operation=self._operation,
            ) from None

    def get_address(self, name: str) -> str:
        """Get the address of a deployed contract by name."""
        return self._manifest["contracts"][name]["address"]

    def get_contract(self, name: str, address: str = None):
        """
        Get a contract instance by name.

        Args:
            name: Contract name as it appears in the manifest
            address: Optional address override

        Returns:
            Contract instance with ABI loaded
        """
        if name in self._contracts and address is None:
            return self._contracts[name]

        contract_info = self._manifest["contracts"][name]
        file_path = contract_info["file"]
        addr = address or contract_info["address"]

        contract = boa.load_partial(file_path).at(addr)

        if address is None:
            self._contracts[name] = contract

        return contract

    def load_abi(self, name: str, address: str):
        """
        Load a contract at a specific address using the ABI from a known contract.

        Args:
            name: Contract name to use as ABI source
            address: Address to load the contract at

        Returns:
            Contract instance
        """
        contract_info = self._manifest["contracts"][name]
        file_path = contract_info["file"]
        return boa.load_partial(file_path).at(address)

    def impersonate(self, address: str):
        """
        Set the sender to impersonate a specific address.

        Args:
            address: Address to impersonate
        """
        boa.env.eoa = address
        log.info(f"Now impersonating: {address}")

    def fund(self, address: str, amount_eth: float = 10.0):
        """
        Fund an address with ETH (only works in fork mode).

        Args:
            address: Address to fund
            amount_eth: Amount of ETH to send (default: 10)
        """
        boa.env.set_balance(address, int(amount_eth * 10**18))
        log.info(f"Funded {address} with {amount_eth} ETH")

    @property
    def contracts(self) -> dict:
        """Dict of all loaded contract instances."""
        return self._contracts

    @property
    def addresses(self) -> dict:
        """Dict of contract name -> address for all contracts in manifest."""
        return {
            name: info["address"]
            for name, info in self._manifest["contracts"].items()
        }

    def list_contracts(self):
        """Print all available contracts from the manifest."""
        log.h2("Available Contracts:")
        for name, info in self._manifest["contracts"].items():
            addr = info.get("address", "N/A")
            print(f"  {name}: {addr}")

    def __repr__(self):
        return (
            f"<Console profile={self._profile_id} mode={self._mode} "
            f"contracts={len(self._manifest.get('contracts', {}))}>"
        )


def create_console_banner(console: Console) -> str:
    """Create the IPython startup banner."""
    return f"""
╔══════════════════════════════════════════════════════════════╗
║                    Ripe Protocol Console                     ║
╠══════════════════════════════════════════════════════════════╣
║  Profile: {console._profile_id:<50} ║
║  Mode: {console._mode:<53} ║
╠══════════════════════════════════════════════════════════════╣
║  Available objects:                                          ║
║    c          - Contract accessor with autocomplete          ║
║                 (c.Teller, c.CreditEngine, c.<Tab>)          ║
║    console    - Console helper                               ║
║    boa        - Boa module for direct blockchain interaction ║
║                                                              ║
║  Quick commands:                                             ║
║    c.Teller                      - Get Teller contract       ║
║    c.<Tab>                       - Autocomplete contracts    ║
║    console.impersonate("0x...")  - Impersonate address       ║
║    console.fund("0x...", 10)     - Fund address with ETH     ║
║    console.list_contracts()      - List all contracts        ║
╚══════════════════════════════════════════════════════════════╝
"""


def read_chain_id(rpc_url: str) -> int | str:
    return EthereumRPC(rpc_url).fetch("eth_chainId", [])


def _validate_static_assertions(profile, operation, environment, blueprint):
    repository = profile.repository
    if environment is not None:
        if (
            repository.history_dir is None
            or environment != repository.history_dir.name
        ):
            raise NetworkProfileError(
                "H02_HISTORY_ALIAS",
                profile_id=profile.identity.profile_id,
                operation=operation,
            )
    if blueprint is not None and blueprint != repository.blueprint_id:
        raise NetworkProfileError(
            "H02_PROFILE_INVALID",
            profile_id=profile.identity.profile_id,
            operation=operation,
        )


@click.command()
@click.option(
    "--profile",
    "--chain",
    "profile_id",
    required=True,
    type=click.Choice(NETWORK_PROFILE_IDS, case_sensitive=False),
    help=(
        "Required canonical network profile. `--chain` is a deprecated "
        "equivalent spelling. Availability is operation-specific; `local` "
        "is reserved for an embedded local runtime."
    ),
)
@click.option(
    "--environment",
    "-e",
    default=None,
    help=(
        "Optional compatibility assertion; it must match the profile-owned "
        "history namespace."
    ),
)
@click.option(
    "--blueprint",
    "-b",
    default=None,
    help=(
        "Optional compatibility assertion; it must match the profile-owned "
        "blueprint."
    ),
)
@click.option(
    "--rpc",
    default=None,
    help=(
        "Sensitive full RPC URL override. If omitted, the selected profile's "
        "named RPC_URL environment variable is used. The value is never logged."
    ),
)
@click.option(
    "--account",
    "-a",
    default="",
    help="Address to impersonate only after fork identity is verified.",
)
@click.option(
    "--block",
    type=click.IntRange(min=1),
    default=None,
    help="Exact source block. Required for evidence mode.",
)
@click.option(
    "--evidence",
    is_flag=True,
    default=False,
    help="Require a pinned, clean fork suitable for reproducible evidence.",
)
def main(
    profile_id,
    environment,
    blueprint,
    rpc,
    account,
    block,
    evidence,
):
    """Start an explicit exploration or reproducible-evidence fork console."""
    operation = (
        Operation.CONSOLE_EVIDENCE
        if evidence
        else Operation.CONSOLE_EXPLORATION
    )
    try:
        profile = get_profile(profile_id)
        policy = require_operation(profile, operation)
        _validate_static_assertions(
            profile, operation, environment, blueprint
        )
        validate_fork_request(
            profile,
            operation,
            evidence_mode=evidence,
            block_number=block,
            allow_dirty=not evidence,
        )
        redacted_rpc = resolve_rpc_reference(
            profile, operation, os.environ, rpc
        )
        identity = verify_chain_identity(
            profile, operation, redacted_rpc, read_chain_id
        )

        manifest = None
        if policy.requires_repository:
            paths = repository_paths(
                profile, operation, root=ROOT, identity=identity
            )
            manifest = paths.history_dir / "current-manifest.json"
    except NetworkProfileError as error:
        raise click.ClickException(str(error)) from None

    mode = "reproducible pinned evidence" if evidence else "local exploration"
    log.h1("Starting Ripe Protocol Console")
    log.info(
        "RPC configured: "
        f"profile={profile.identity.profile_id} "
        f"reference={redacted_rpc.reference} value=<redacted>."
    )
    log.info(f"Mode: {mode}. Source-RPC submission is disabled.")

    try:
        console = Console(
            profile.identity.profile_id, operation, mode, manifest
        )
    except NetworkProfileError as error:
        raise click.ClickException(str(error)) from None
    kwargs = {"allow_dirty": not evidence}
    if block is not None:
        kwargs["block_identifier"] = block

    with ExitStack() as fork_stack:
        try:
            env = fork_stack.enter_context(
                boa.fork(redacted_rpc.value, **kwargs)
            )
        except Exception:
            raise click.ClickException(
                "H02_RPC_CONNECT_FAILED "
                f"profile={profile.identity.profile_id} "
                f"operation={operation.value} env={redacted_rpc.reference}"
            ) from None

        if account:
            env.eoa = account
            try:
                env.set_balance(account, 10 * 10**18)
                log.info(
                    "Configured explicit fork-only impersonation account."
                )
            except Exception:
                log.info(
                    "Configured explicit fork-only impersonation account "
                    "without funding."
                )

        try:
            from IPython import embed
            from traitlets.config import Config

            config = Config()
            config.InteractiveShellEmbed.colors = "Linux"
            config.InteractiveShell.autocall = 0
            namespace = {
                "c": console.c,
                "console": console,
                "boa": boa,
                "env": env,
            }
            embed(
                config=config,
                banner1=create_console_banner(console),
                user_ns=namespace,
                colors="Linux",
            )
        except ImportError:
            log.error(
                "IPython is not installed. Falling back to the standard "
                "Python REPL."
            )
            import code

            namespace = {
                "c": console.c,
                "console": console,
                "boa": boa,
                "env": env,
            }
            code.interact(
                banner=create_console_banner(console), local=namespace
            )


if __name__ == "__main__":
    main()
