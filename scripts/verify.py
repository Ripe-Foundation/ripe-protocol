import json
import os
import re
import time
from pathlib import Path

import click

from scripts.migrate import param_prompt, CLICK_PROMPTS
from scripts.utils.verify_etherscan import CHAIN_SPECS, verify_from_manifest

MIGRATION_HISTORY_DIR = "./migration_history"

# scripts/verify_blockscout.py targets Robinhood mainnet only, so that is the
# one chain we can honestly redirect to it. Pointing anything else there --
# a typo, `local`, a retired network -- would be false advice.
BLOCKSCOUT_CHAINS = frozenset({"robinhood-mainnet"})

# One path segment: must start alphanumeric, and may then carry only
# alphanumerics, dot, dash or underscore. That admits `v1`, `v2` and
# `current`, and excludes separators, `.`, `..`, absolute paths and empties.
_SEGMENT_RE = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._-]*\Z")


def _canonical_segment(value, option):
    """Return `value` if it is a single safe path segment, else refuse.

    The rejected value is deliberately not echoed. It is caller-controlled,
    and repeating it back writes the attempted path into terminal scrollback
    and CI logs.
    """
    if not isinstance(value, str) or not _SEGMENT_RE.match(value):
        raise click.ClickException(
            f"--{option} must be a single path segment matching "
            "[A-Za-z0-9][A-Za-z0-9._-]* -- no separators, no '.' or '..', "
            "not absolute. The rejected value is not echoed."
        )
    return value


def _history_manifest_path(chain, environment, manifest):
    """Resolve the manifest path and prove it stays inside the history tree."""
    root = Path(MIGRATION_HISTORY_DIR).resolve()
    candidate = (
        root / chain / environment / f"{manifest}-manifest.json"
    ).resolve()
    # The segment rules already forbid traversal. Re-checking the *resolved*
    # path is what stops a symlink planted inside the tree from widening it,
    # and it is cheap next to submitting contract records with a live key.
    if not candidate.is_relative_to(root):
        raise click.ClickException(
            "Resolved manifest path escapes the migration history directory."
        )
    return candidate


@click.command()
@click.option(
    "--environment",
    default=CLICK_PROMPTS["environment"]["default"],
    help=CLICK_PROMPTS["environment"]["help"],
    callback=param_prompt,
)
@click.option(
    "--chain",
    default=CLICK_PROMPTS["chain"]["default"],
    help=CLICK_PROMPTS["chain"]["help"],
    callback=param_prompt,
)
@click.option(
    "--manifest",
    default=CLICK_PROMPTS["manifest"]["default"],
    help=CLICK_PROMPTS["manifest"]["help"],
    callback=param_prompt,
)
def cli(environment, chain, manifest):
    """Verify contracts on Etherscan/Basescan.

    Robinhood chains have no Etherscan-family explorer -- see
    `scripts/verify_blockscout.py` for those.
    """
    # Validate every input before constructing -- let alone printing -- a path.
    # An unknown chain and a known chain without a verifier are different
    # failures and get different advice; conflating them tells someone with a
    # typo to go use the Robinhood Blockscout script.
    spec = CHAIN_SPECS.get(chain) if isinstance(chain, str) else None
    if spec is None:
        raise click.ClickException(
            "Unknown chain. Supported chains: "
            + ", ".join(sorted(CHAIN_SPECS))
            + "."
        )
    if spec.provider is None:
        # Safe to echo now: `chain` is a canonical key, not free text.
        hint = (
            " Use `python -m scripts.verify_blockscout` for that chain."
            if chain in BLOCKSCOUT_CHAINS
            else ""
        )
        raise click.ClickException(
            f"Chain `{chain}` has no Etherscan-family verifier configured."
            + hint
        )

    environment = _canonical_segment(environment, "environment")
    manifest = _canonical_segment(manifest, "manifest")
    manifest_path = _history_manifest_path(chain, environment, manifest)

    print(f"Verifying contracts from chain `{chain}`, manifest `{manifest_path}`")

    if not manifest_path.exists():
        raise click.ClickException(f"No manifest found at {manifest_path}")

    # Either spelling is accepted: `migrate` reads BASESCAN_API_KEY for the
    # Base chains, while CI and older docs use ETHERSCAN_API_KEY.
    api_key = os.getenv("ETHERSCAN_API_KEY") or os.getenv("BASESCAN_API_KEY")
    if not api_key:
        raise click.ClickException(
            "Neither ETHERSCAN_API_KEY nor BASESCAN_API_KEY is set."
        )

    with open(manifest_path, "r") as f:
        manifest_data = json.load(f)

    contracts = manifest_data["contracts"]
    failed = []
    for contract_name, contract_data in contracts.items():
        print(f"\nVerifying {contract_name}...")
        success = verify_from_manifest(
            api_key=api_key,
            contract_name=contract_name,
            manifest_data=contract_data,
            chain=chain,
        )
        if success:
            print(f"✅ {contract_name} verified successfully")
        else:
            failed.append(contract_name)
            print(f"❌ {contract_name} verification failed")

        # Stay under the explorer's rate limit between submissions.
        time.sleep(1)

    print(f"\nVerified {len(contracts) - len(failed)}/{len(contracts)} contracts.")
    if failed:
        # Exit non-zero so a CI or scripted run does not read as success.
        raise click.ClickException(f"Verification failed for: {', '.join(failed)}")


if __name__ == "__main__":
    cli()
