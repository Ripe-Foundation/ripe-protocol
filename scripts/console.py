"""
Interactive IPython console for debugging with forked mainnet.

Usage:
    python -m scripts.console [OPTIONS]

Examples:
    python -m scripts.console                    # Default: base-mainnet fork
    python -m scripts.console --chain base-sepolia
    python -m scripts.console --account 0x1234...  # Impersonate specific address
"""

import os
import click
import boa
import dotenv

from scripts.utils import json_file, log
from scripts.utils.migration_helpers import load_vyper_files
from scripts.utils.deploy_args import DeployArgs
from scripts.utils.mock_account import MockAccount

dotenv.load_dotenv()

MIGRATION_HISTORY_DIR = "./migration_history"


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

    def __init__(self, chain: str, environment: str, blueprint: str, rpc: str):
        self._chain = chain
        self._environment = environment
        self._blueprint = blueprint
        self._rpc = rpc
        self._manifest = {}
        self._contracts = {}
        self._files = load_vyper_files()
        self._load_manifest()
        self.c = ContractAccessor(self)

    def _load_manifest(self):
        """Load the current manifest file."""
        manifest_path = os.path.join(
            MIGRATION_HISTORY_DIR,
            self._chain,
            self._environment,
            "current-manifest.json"
        )
        try:
            self._manifest = json_file.load(manifest_path)
            log.h3(f"Loaded manifest from {manifest_path}")
        except Exception as e:
            log.error(f"Failed to load manifest: {e}")
            self._manifest = {"contracts": {}}

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
        return f"<Console chain={self._chain} contracts={len(self._manifest.get('contracts', {}))}>"


def create_console_banner(console: Console) -> str:
    """Create the IPython startup banner."""
    return f"""
╔══════════════════════════════════════════════════════════════╗
║                    Ripe Protocol Console                     ║
╠══════════════════════════════════════════════════════════════╣
║  Chain: {console._chain:<52} ║
║  Environment: {console._environment:<46} ║
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


@click.command()
@click.option(
    "--chain", "-c",
    default="base-mainnet",
    help="Chain to fork (default: base-mainnet)",
    type=click.Choice(["base-mainnet", "base-sepolia", "eth-mainnet", "eth-sepolia"], case_sensitive=False),
)
@click.option(
    "--environment", "-e",
    default="v1",
    help="Environment/manifest directory (default: v1)",
)
@click.option(
    "--blueprint", "-b",
    default="base",
    help="Blueprint configuration (default: base)",
)
@click.option(
    "--rpc",
    default="",
    help="Custom RPC URL (default: uses Alchemy)",
)
@click.option(
    "--account", "-a",
    default="",
    help="Address to impersonate as the default sender",
)
def main(chain, environment, blueprint, rpc, account):
    """
    Start an interactive IPython console with forked mainnet.

    The console provides access to all deployed contracts from the manifest
    and allows impersonating any address for testing.
    """
    # Determine RPC URL
    final_rpc = rpc if rpc else f"https://{chain}.g.alchemy.com/v2/{os.environ.get('WEB3_ALCHEMY_API_KEY')}"

    log.h1("Starting Ripe Protocol Console")
    log.info(f"Forking {chain} via {final_rpc[:50]}...")

    # Create console instance
    console = Console(chain, environment, blueprint, final_rpc)

    # Start fork environment
    with boa.fork(final_rpc, allow_dirty=True) as env:
        # Set up impersonation if specified
        if account:
            env.eoa = account
            try:
                env.set_balance(account, 10 * 10**18)
                log.info(f"Impersonating {account} (funded with 10 ETH)")
            except:
                log.info(f"Impersonating {account}")

        # Try to import IPython
        try:
            from IPython import embed
            from traitlets.config import Config

            # Configure IPython
            config = Config()
            config.InteractiveShellEmbed.colors = "Linux"
            config.InteractiveShell.autocall = 0

            # Create namespace with useful objects
            namespace = {
                "c": console.c,
                "console": console,
                "boa": boa,
                "env": env,
            }

            banner = create_console_banner(console)

            # Start IPython
            embed(
                config=config,
                banner1=banner,
                user_ns=namespace,
                colors="Linux",
            )

        except ImportError:
            log.error("IPython is not installed. Install it with: pip install ipython")
            log.info("Falling back to standard Python REPL...")

            import code
            namespace = {
                "c": console.c,
                "console": console,
                "boa": boa,
                "env": env,
            }

            banner = create_console_banner(console)
            code.interact(banner=banner, local=namespace)


if __name__ == "__main__":
    main()
