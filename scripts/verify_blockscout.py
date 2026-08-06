"""Verify deployed Robinhood contracts on Blockscout.

scripts/verify.py only validates manifest assertions locally -- it has no
submission path -- so this does the actual explorer verification.

Uses `vyper -f solc_json` to produce the standard JSON input, which resolves
the module imports (addys, deptBasics, gov, timeLock, ...) that single-file
verification cannot. The compiler version is read from the local vyper so it
cannot silently disagree with what was deployed.

Usage:
    python scripts/verify_blockscout.py                    # all, skip verified
    python scripts/verify_blockscout.py --only RipeHq GreenToken
    python scripts/verify_blockscout.py --dry-run          # show, submit nothing
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(override=False)
except ImportError:
    pass

ROOT = Path(__file__).resolve().parent.parent
EXPLORER = "https://robinhoodchain.blockscout.com"
MANIFEST = ROOT / "migration_history/robinhood-mainnet/v1/current-manifest.json"


def compiler_version() -> str:
    """Read the local vyper version, formatted the way Blockscout lists it."""
    out = subprocess.run(
        ["vyper", "--version"], capture_output=True, text=True, check=True
    ).stdout.strip()
    return "v" + out.split()[0]


def standard_json(source_path: Path) -> dict:
    """Standard JSON input, with every imported module inlined."""
    out = subprocess.run(
        ["vyper", "-f", "solc_json", str(source_path)],
        capture_output=True, text=True, check=True, cwd=ROOT,
    ).stdout
    return json.loads(out)


def is_verified(address: str) -> bool | None:
    import requests

    try:
        r = requests.get(
            f"{EXPLORER}/api/v2/smart-contracts/{address}", timeout=20
        )
        if r.status_code != 200:
            return None
        return bool(r.json().get("is_verified"))
    except Exception:
        return None


def submit(address: str, source_path: Path, version: str) -> tuple[bool, str]:
    import requests

    payload = standard_json(source_path)
    files = {
        "files[0]": (
            "standard-input.json",
            json.dumps(payload).encode("utf-8"),
            "application/json",
        )
    }
    data = {"compiler_version": version, "license_type": "bsl_1_1"}
    # Optional: raises the rate limit and is required by some instances.
    api_key = os.environ.get("BLOCKSCOUT_API_KEY")
    if api_key:
        data["api_key"] = api_key
    r = requests.post(
        f"{EXPLORER}/api/v2/smart-contracts/{address}"
        "/verification/via/vyper-standard-input",
        data=data, files=files, timeout=120,
    )
    # This explorer queues the job, verifies it, and THEN answers 500 with an
    # HTML error page. The response says nothing useful either way, so the only
    # honest check is to ask whether the contract ended up verified.
    for _ in range(12):
        time.sleep(5)
        state = is_verified(address)
        if state:
            return True, f"verified (submit returned HTTP {r.status_code})"
    return False, f"not verified after 60s (submit returned HTTP {r.status_code})"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", nargs="*", help="Contract names to verify.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true",
                        help="Submit even if already verified.")
    args = parser.parse_args()

    contracts = json.loads(MANIFEST.read_text())["contracts"]
    sources = {p.stem: p for p in (ROOT / "contracts").rglob("*.vy")}
    version = compiler_version()
    print(f"compiler: {version}\nexplorer: {EXPLORER}\n")

    names = args.only or sorted(contracts)
    done = skipped = failed = 0
    for name in names:
        row = contracts.get(name)
        if not row or not row.get("address"):
            print(f"  {name:22} SKIP  not in manifest")
            skipped += 1
            continue
        address = row["address"]
        src = sources.get(name)
        if src is None:
            print(f"  {name:22} SKIP  no .vy source (blueprint or external)", flush=True)
            skipped += 1
            continue
        if not args.force and is_verified(address):
            print(f"  {name:22} ok    already verified", flush=True)
            skipped += 1
            continue
        if args.dry_run:
            print(f"  {name:22} would submit {src.relative_to(ROOT)} @ {address}")
            continue
        # Printed before the slow part so the run never looks hung: a submit
        # plus polling can take a minute per contract.
        print(f"  {name:22} submitting (up to 60s)...", flush=True)
        try:
            ok, detail = submit(address, src, version)
        except Exception as error:
            ok, detail = False, f"{type(error).__name__}: {error}"
        print(f"  {name:22} {'OK   ' if ok else 'FAIL '} {detail}", flush=True)
        done += ok
        failed += not ok

    print(f"\nsubmitted {done}, skipped {skipped}, failed {failed}")
    if done:
        print("Verification is asynchronous; re-run to see final status.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
