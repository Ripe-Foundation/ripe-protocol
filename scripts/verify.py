import json
import os
import time

import click

from scripts.migrate import param_prompt, CLICK_PROMPTS
from scripts.utils.verify_etherscan import verify_from_manifest

MIGRATION_HISTORY_DIR = "./migration_history"


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
    manifest_path = f"{MIGRATION_HISTORY_DIR}/{chain}/{environment}/{manifest}-manifest.json"
    print(f"Verifying contracts from chain `{chain}`, manifest `{manifest_path}`")

    if not os.path.exists(manifest_path):
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
