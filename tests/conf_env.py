import pytest
import contextlib
import boa
import subprocess
import time
import requests
import sys
import socket

from boa.environment import Env
import os


FORKS = {
    "mainnet": {
        "rpc_url": f"https://eth-mainnet.g.alchemy.com/v2/{os.environ.get('WEB3_ALCHEMY_API_KEY')}",
        "etherscan_url": "https://api.etherscan.io/api",
        "etherscan_api_key": os.environ["ETHERSCAN_API_KEY"],
        "block": 21552600,
        "anvil": True,
    },
    "base": {
        "rpc_url": f"https://base-mainnet.g.alchemy.com/v2/{os.environ.get('WEB3_ALCHEMY_API_KEY')}",
        "block": 26828421,
        "etherscan_url": "https://api.basescan.org/api",
        "etherscan_api_key": os.environ["BASESCAN_API_KEY"],
        "anvil": True,
    }
}


def pytest_configure(config):
    # Add fork marker
    config.addinivalue_line(
        "markers",
        "fork(name): mark test to run only on specific fork"
    )

    pytest.always = pytest.mark.fork("always")
    pytest.local = pytest.mark.fork("local")
    # Register shorthand markers
    for key in FORKS.keys():
        setattr(pytest, key, pytest.mark.fork(key))


def pytest_collection_modifyitems(config, items):
    fork = config.getoption("--fork")

    selected = []
    deselected = []

    for item in items:
        markers = [marker for marker in item.iter_markers(name="fork")]
        # Always run tests marked with "always"
        if any("always" in marker.args for marker in markers):
            selected.append(item)
            continue

        if fork == "local":
            # For local, select tests with no fork marker OR local marker
            if not markers or any("local" in marker.args for marker in markers):
                selected.append(item)
            else:
                deselected.append(item)
        else:
            # For mainnet/base, only select tests marked for that fork
            if any(fork in marker.args for marker in markers):
                selected.append(item)
            else:
                deselected.append(item)

    items[:] = selected
    if deselected:
        config.hook.pytest_deselected(items=deselected)


def pytest_addoption(parser):
    parser.addoption(
        "--fork",
        action="store",
        default="local",
        choices=["local", "mainnet", "base"],
        help="Specify the fork to run tests against"
    )
    parser.addoption(
        "--rpc",
        action="store",
        default=None,
        help="Override RPC URL for the selected fork or local testing"
    )
    parser.addoption(
        "--anvil",
        action="store_true",
        default=False,
        help="Force using Anvil"
    )


@pytest.fixture(scope="session")
def fork(pytestconfig):
    return pytestconfig.getoption("fork")


@pytest.fixture(scope="session")
def set_etherscan(fork):
    config = FORKS[fork] if fork in FORKS else FORKS["mainnet"]
    api_key = config["etherscan_api_key"]
    uri = config["etherscan_url"]

    boa.set_etherscan(api_key=api_key, uri=uri)


@pytest.fixture(scope="session")
def free_port():
    """Find a free port to use for anvil"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


@pytest.fixture(scope="session")
def anvil(free_port):
    @contextlib.contextmanager
    def anvil(fork_url=None, block_number=None):
        anvil_args = [
            "anvil",
            "--port", str(free_port),
        ]

        # Only add fork-url if provided
        if fork_url:
            anvil_args.extend(["--fork-url", fork_url, "--no-rate-limit"])

        # Add block number if provided
        if block_number:
            anvil_args.extend(["--fork-block-number", str(block_number)])

        # TODO: checked=True
        anvil_process = subprocess.Popen(
            anvil_args,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )

        anvil_uri = f"http://localhost:{free_port}"
        try:
            # Wait for anvil to come up
            while True:
                try:
                    requests.head(anvil_uri)
                    break
                except requests.exceptions.ConnectionError:
                    time.sleep(1)

            fork_kwargs = {"block_identifier": block_number} if block_number else {}
            with boa.fork(anvil_uri, **fork_kwargs) as env:
                yield env
        finally:
            # Clean up anvil process
            anvil_process.terminate()
            try:
                anvil_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                anvil_process.kill()
                anvil_process.wait(timeout=1)
    return anvil


@pytest.fixture(scope="session")
def env(fork, pytestconfig, anvil, set_etherscan):
    # Get optional settings
    rpc_override = pytestconfig.getoption("rpc")
    force_anvil = pytestconfig.getoption("anvil")
    is_forked = fork in FORKS

    # Enable prefetch state for all forked environments
    boa.env.evm._fork_try_prefetch_state = is_forked

    # Handle RPC override first
    if rpc_override:
        if fork in FORKS:
            block_number = FORKS[fork].get("block")
        with boa.fork(rpc_override, block_identifier=block_number) as env:
            yield env
        return

    # Handle local testing
    if not is_forked:
        if force_anvil:
            with anvil() as env:
                yield env
        else:
            with boa.set_env(Env()) as env:
                boa.env.enable_fast_mode()
                yield env
        return

    # Handle forked testing
    fork_config = FORKS[fork]
    block_number = fork_config.get("block")
    use_anvil = force_anvil or fork_config.get("anvil", False)

    if use_anvil:
        with anvil(fork_config["rpc_url"], block_number) as env:
            yield env
    else:
        fork_kwargs = {"block_identifier": block_number} if block_number else {}
        with boa.fork(fork_config["rpc_url"], **fork_kwargs) as env:
            yield env
