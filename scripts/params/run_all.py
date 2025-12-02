#!/usr/bin/env python3
"""
Run All Params Scripts for Ripe Protocol

Generates all parameter output files by running each params script sequentially.

Output files generated:
- deployments_output.md  - All contract addresses
- assets_output.md       - Per-asset configurations
- prices_output.md       - Price source configurations
- vaults_output.md       - Vault configurations
- general_output.md      - General protocol settings
- ledger_output.md       - Live protocol data (debt, rewards, contributors)

Usage:
    python scripts/params/run_all.py
"""

import os
import sys
import subprocess
import time

# Scripts to run in order
SCRIPTS = [
    ("deployments.py", "Contract Addresses"),
    ("assets.py", "Asset Configurations"),
    ("prices.py", "Price Source Configurations"),
    ("vaults.py", "Vault Configurations"),
    ("general.py", "General Protocol Settings"),
    ("ledger.py", "Live Protocol Data"),
]


def main():
    """Run all params scripts sequentially."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    start_time = time.time()

    print("=" * 80)
    print("Ripe Protocol - Generate All Parameter Reports")
    print("=" * 80)
    print()

    total = len(SCRIPTS)
    failed = []

    for i, (script_name, description) in enumerate(SCRIPTS, 1):
        script_path = os.path.join(script_dir, script_name)

        print(f"[{i}/{total}] Generating {description}...")
        print(f"     Running: {script_name}")

        try:
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                cwd=script_dir,
            )

            if result.returncode != 0:
                print(f"     ERROR: Script failed with return code {result.returncode}")
                if result.stderr:
                    print(f"     {result.stderr[:200]}...")
                failed.append(script_name)
            else:
                print(f"     Done!")

        except Exception as e:
            print(f"     ERROR: {e}")
            failed.append(script_name)

        print()

    # Summary
    elapsed = time.time() - start_time
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"Total time: {elapsed:.1f} seconds")
    print(f"Scripts run: {total}")
    print(f"Successful: {total - len(failed)}")

    if failed:
        print(f"Failed: {len(failed)}")
        for name in failed:
            print(f"  - {name}")
        print()
        print("Output files generated (check for any missing):")
    else:
        print()
        print("All output files generated successfully:")

    # List output files
    output_files = [
        "deployments_output.md",
        "assets_output.md",
        "prices_output.md",
        "vaults_output.md",
        "general_output.md",
        "ledger_output.md",
    ]

    for output_file in output_files:
        output_path = os.path.join(script_dir, output_file)
        if os.path.exists(output_path):
            size = os.path.getsize(output_path)
            print(f"  - {output_file} ({size:,} bytes)")
        else:
            print(f"  - {output_file} (NOT FOUND)")

    print()

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
