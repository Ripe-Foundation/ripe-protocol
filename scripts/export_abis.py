"""
Export ABIs for all Vyper contracts (excluding mock contracts).

Usage:
    python scripts/export_abis.py
    python scripts/export_abis.py --output-dir ./my-abis
"""

import argparse
import json
from pathlib import Path

from vyper.compiler import compile_code


def export_abis(contracts_dir: Path, output_dir: Path, exclude_dirs: list[str] = None):
    exclude_dirs = exclude_dirs or ["mock"]
    output_dir.mkdir(parents=True, exist_ok=True)

    contract_files = list(contracts_dir.rglob("*.vy"))
    exported = 0
    skipped = 0

    for vy_file in sorted(contract_files):
        # Skip excluded directories
        if any(excluded in vy_file.parts for excluded in exclude_dirs):
            skipped += 1
            continue

        try:
            with open(vy_file) as f:
                code = f.read()

            result = compile_code(code, output_formats=["abi"])
            abi = result["abi"]

            output_file = output_dir / f"{vy_file.stem}.json"
            with open(output_file, "w") as f:
                json.dump(abi, f, indent=2)

            print(f"✓ {vy_file.stem}")
            exported += 1

        except Exception as e:
            print(f"✗ {vy_file.stem}: {e}")

    print(f"\nExported {exported} ABIs to {output_dir}")
    print(f"Skipped {skipped} mock contracts")


def main():
    parser = argparse.ArgumentParser(description="Export ABIs for Vyper contracts")
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=Path("scripts/abis"),
        help="Output directory for ABI files (default: scripts/abis)",
    )
    parser.add_argument(
        "--contracts-dir",
        "-c",
        type=Path,
        default=Path("contracts"),
        help="Contracts directory (default: contracts)",
    )
    args = parser.parse_args()

    export_abis(args.contracts_dir, args.output_dir)


if __name__ == "__main__":
    main()
