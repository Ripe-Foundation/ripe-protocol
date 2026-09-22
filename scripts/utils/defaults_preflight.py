"""Read-only subprocess verification: never replaces the runner's Boa environment."""

import hashlib
import os
from pathlib import Path
import subprocess
import sys

from web3 import Web3

from scripts.utils.fork_reports import sanitize

ROOT = Path(__file__).resolve().parents[2]


def artifact_hashes(defaults_path):
    # Bind compiler inputs AND verifier logic, not just the generated file.
    paths = {Path(defaults_path).resolve()}
    for directory, suffix in (("contracts", "*.vy"), ("interfaces", "*.vyi"),
                              ("scripts", "*.py"), ("config", "*.py")):
        paths.update((ROOT / directory).rglob(suffix))
    paths.add(ROOT / "migration_history/base-mainnet/v1/current-manifest.json")
    paths.update((ROOT / "migrations/base-mainnet").glob("*.py"))
    paths.update((ROOT / "migrations/archive/base-mainnet").glob("*.py"))
    return {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(paths)}


class VerifiedDefaults:
    def __init__(self, path, hashes, block, block_hash):
        self.path, self.hashes = path, hashes
        self.block, self.block_hash = block, block_hash

    def require_unchanged(self):
        if artifact_hashes(self.path) != self.hashes:
            raise RuntimeError("BASE_DEFAULTS_PREFLIGHT_ARTIFACT_CHANGED")


def verify_before_deployment(path, rpc, *, rehearsal_block=None):
    """Production always selects finalized now; only the fork adapter supplies a pin."""
    if not __debug__:
        raise RuntimeError("BASE_DEFAULTS_PREFLIGHT_OPTIMIZED_PYTHON")
    path = Path(path).resolve()
    hashes = artifact_hashes(path)
    w3 = Web3(Web3.HTTPProvider(rpc))
    try:
        if w3.eth.chain_id != 8453:
            raise RuntimeError("BASE_DEFAULTS_PREFLIGHT_WRONG_CHAIN")
        block = w3.eth.get_block("finalized" if rehearsal_block is None else rehearsal_block)
        number, block_hash = int(block["number"]), block["hash"].hex()
        env = os.environ.copy()
        env["BASE_MAINNET_RPC_URL"] = rpc
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/verify_defaults.py"),
             "--network", "base-mainnet", "--defaults", str(path),
             "--block-number", str(number)],
            cwd=ROOT, env=env, capture_output=True, text=True, timeout=600,
        )
        if result.returncode != 0:
            detail = sanitize(result.stdout + result.stderr, rpc, ROOT)
            raise RuntimeError("BASE_DEFAULTS_PREFLIGHT_FAILED:\n" + detail[-6000:])
        if w3.eth.get_block(number)["hash"].hex() != block_hash:
            raise RuntimeError("BASE_DEFAULTS_PREFLIGHT_BLOCK_CHANGED")
    except Exception as exc:
        # Provider errors can include authentication-bearing URLs.
        raise RuntimeError(sanitize(str(exc), rpc, ROOT)) from None
    verified = VerifiedDefaults(path, hashes, number, block_hash)
    verified.require_unchanged()
    return verified
