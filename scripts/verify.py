import click
import json
import os
from scripts.migrate import param_prompt, CLICK_PROMPTS
from scripts.utils.verify_etherscan import verify_from_manifest
import time

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
def cli(environment, chain):
    """Verify contracts on Etherscan/Basescan"""
    print(f"Verifying contracts from environment: {environment}")

    # Load manifest
    manifest_path = f"{MIGRATION_HISTORY_DIR}/{environment}/current-manifest.json"
    if not os.path.exists(manifest_path):
        print(f"No manifest found at {manifest_path}")
        return

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    # Get API key based on chain
    if "base" in chain:
        api_key = os.getenv("BASESCAN_API_KEY")
        if not api_key:
            print("BASESCAN_API_KEY environment variable not set")
            return
    else:
        api_key = os.getenv("ETHERSCAN_API_KEY")
        if not api_key:
            print("ETHERSCAN_API_KEY environment variable not set")
            return

    # Verify each contract
    for contract_name, contract_data in manifest["contracts"].items():
        print(f"\nVerifying {contract_name}...")
        success = verify_from_manifest(
            api_key=api_key,
            contract_name=contract_name,
            manifest_data=contract_data,
            chain=chain
        )
        if success:
            print(f"✅ {contract_name} verified successfully")
        else:
            print(f"❌ {contract_name} verification failed")

        # Add delay between verifications to avoid rate limits
        time.sleep(1)  # Wait 1 second between contracts


if __name__ == "__main__":
    cli()
