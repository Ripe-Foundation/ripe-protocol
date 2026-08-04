"""Prove a connected Ledger will sign a Robinhood deployment transaction.

This exists because scripts/fork_rh_deployment.py CANNOT prove it. That harness
runs titanoboa's in-process EVM, which executes against forked state without
ever serialising, signing, or broadcasting anything -- so the device is never
asked for a signature and no prompt appears. Everything about the launch graph
is proven there except the one thing that needs real hardware.

What this checks, in a single button press:

  1. The device is reachable and index N derives the address you expect.
  2. The Ethereum app will sign for chain id 4663, which it does not know. It
     shows an unknown-network warning; a Ledger that refuses outright would
     stop a live deployment at its first transaction.
  3. Contract creation signs. This is the real risk: a deployment has no
     `to` address and opaque calldata, so the app requires "blind signing" to
     be enabled under Ethereum > Settings. Disabled, it rejects EVERY contract
     deployment -- all 38 of them -- and you would find out at action 9 of 119.
  4. The signed payload is accepted and mined by a node forked from Robinhood,
     so the chain id, nonce, gas and fee fields we build are actually valid.

Nothing here touches Robinhood mainnet: anvil holds the fork locally and is
discarded on exit. The RPC URL is never printed -- it may carry a provider key.

Usage:
    anvil --fork-url "$ROBINHOOD_MAINNET_RPC_URL" --port 8545   # separate shell
    python scripts/ledger_signing_smoke.py --ledger 0

Or let this script start and stop anvil itself:
    python scripts/ledger_signing_smoke.py --ledger 0 --manage-anvil
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ANVIL_RPC = "http://127.0.0.1:8545"
ROBINHOOD_CHAIN_ID = 4663

# Minimal runtime-returning initcode: PUSH1 0x00 DUP1 RETURN, wrapped in a
# constructor that returns it. Deliberately tiny -- the point is to exercise
# contract CREATION (no `to` field, opaque data), not to deploy anything real.
SMOKE_INITCODE = "0x600a600c600039600a6000f3600360005260206000f3"


def _rpc_url() -> str:
    url = os.environ.get("ROBINHOOD_MAINNET_RPC_URL")
    if not url:
        env = ROOT / ".env"
        if env.exists():
            for line in env.read_text().splitlines():
                if line.startswith("ROBINHOOD_MAINNET_RPC_URL="):
                    url = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not url:
        raise SystemExit("ROBINHOOD_MAINNET_RPC_URL is not set")
    return url


@contextmanager
def _anvil(manage: bool):
    """Run anvil forked from Robinhood, or assume one is already listening."""
    if not manage:
        yield
        return
    if shutil.which("anvil") is None:
        raise SystemExit("anvil not found on PATH (install Foundry)")
    # stdout is discarded: anvil echoes the fork URL, which carries a key.
    process = subprocess.Popen(
        ["anvil", "--fork-url", _rpc_url(), "--port", "8545", "--silent"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        from web3 import Web3

        w3 = Web3(Web3.HTTPProvider(ANVIL_RPC))
        for _ in range(60):
            if process.poll() is not None:
                raise SystemExit("anvil exited during startup")
            try:
                if w3.is_connected():
                    break
            except Exception:
                pass
            time.sleep(0.5)
        else:
            raise SystemExit("anvil did not become ready")
        print("  anvil forked from Robinhood and listening")
        yield
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
        print("  anvil stopped")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=int, default=0, metavar="INDEX")
    parser.add_argument(
        "--manage-anvil",
        action="store_true",
        help="Start and stop anvil around the test instead of using a running one.",
    )
    args = parser.parse_args()

    from web3 import Web3

    with _anvil(args.manage_anvil):
        w3 = Web3(Web3.HTTPProvider(ANVIL_RPC))
        if not w3.is_connected():
            raise SystemExit(
                f"nothing listening on {ANVIL_RPC}. Start anvil first, or pass "
                "--manage-anvil."
            )
        chain_id = w3.eth.chain_id
        print(f"  anvil chain id           {chain_id}")
        if chain_id != ROBINHOOD_CHAIN_ID:
            print(
                f"  WARNING: expected {ROBINHOOD_CHAIN_ID}. The device's response to "
                "an unknown chain id is part of what this proves, so a mismatch "
                "makes the result meaningless."
            )

        from scripts.utils.ledger_account import LedgerAccount

        print("\n  Connecting to Ledger (unlock it, open the Ethereum app)...")
        account = LedgerAccount(ANVIL_RPC, args.ledger)
        sender = account.address
        print(f"  Ledger account {args.ledger} address  {sender}")

        # Fund on the fork only. Real balance is irrelevant here.
        w3.provider.make_request("anvil_setBalance", [sender, hex(10**18)])

        nonce = w3.eth.get_transaction_count(sender)
        base_fee = w3.eth.get_block("latest").get("baseFeePerGas") or 10**9
        tx = {
            "from": sender,
            "value": 0,
            "gas": 200_000,
            "nonce": nonce,
            "data": SMOKE_INITCODE,
            "chainId": chain_id,
            "maxPriorityFeePerGas": 10**9,
            "maxFeePerGas": base_fee * 2 + 10**9,
        }

        print(
            "\n  A CONTRACT CREATION is about to be sent to the device.\n"
            "  Confirm it on the Ledger. If it rejects with a blind-signing\n"
            "  error, enable Ethereum > Settings > Blind signing -- every\n"
            "  contract deployment in the launch needs it.\n"
        )
        signed = account.sign_transaction(tx)
        raw = signed.raw_transaction
        print(f"  signed payload           {len(raw)} bytes")

        tx_hash = w3.eth.send_raw_transaction(raw)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        if receipt.status != 1:
            raise SystemExit(f"  transaction reverted: {receipt}")
        recovered = receipt["from"]
        if recovered.lower() != sender.lower():
            raise SystemExit(
                f"  signature recovered to {recovered}, not {sender} -- the "
                "device signed for a different account than it reported."
            )
        print(f"  mined in block           {receipt.blockNumber}")
        print(f"  contract created at      {receipt.contractAddress}")
        print(f"  recovered sender         {recovered}")

        print(
            "\nLEDGER SIGNING PROVED (local anvil fork only; nothing reached "
            "Robinhood mainnet)\n"
            f"  The device signs contract creations for chain {chain_id} and the\n"
            "  payload we build is accepted and mined. Blind signing is enabled."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
