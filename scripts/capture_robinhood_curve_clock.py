#!/usr/bin/env python3
"""Capture a secret-free Robinhood Curve clock-domain evidence packet."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlparse
from urllib.request import Request, urlopen


ROBINHOOD_CHAIN_ID = 4663
MULTICALL3 = "0xcA11bde05977b3631167028862bE2a173976CA11"
ARB_SYS = "0x0000000000000000000000000000000000000064"
GET_BLOCK_NUMBER = "0x42cbb15c"
ARB_BLOCK_NUMBER = "0xa3b1b31d"


def _rpc(url: str, calls: list[dict]) -> dict[int, dict]:
    request = Request(
        url,
        data=json.dumps(calls).encode(),
        headers={
            "content-type": "application/json",
            "user-agent": "ripe-protocol-clock-evidence/1",
        },
        method="POST",
    )
    with urlopen(request, timeout=60) as response:  # noqa: S310 - operator RPC
        payload = json.load(response)
    if not isinstance(payload, list):
        payload = [payload]
    by_id = {item["id"]: item for item in payload}
    for call in calls:
        result = by_id.get(call["id"])
        if result is None or "error" in result or "result" not in result:
            raise RuntimeError(f"RPC call {call['id']} failed")
    return by_id


def _quantity(value: str) -> int:
    return int(value, 16)


def capture(url: str, sample_size: int, end_block: int | None) -> dict:
    identity_calls = [
        {"jsonrpc": "2.0", "id": 1, "method": "eth_chainId", "params": []},
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "eth_getBlockByNumber",
            "params": [hex(end_block) if end_block is not None else "latest", False],
        },
    ]
    identity = _rpc(url, identity_calls)
    chain_id = _quantity(identity[1]["result"])
    if chain_id != ROBINHOOD_CHAIN_ID:
        raise RuntimeError(
            f"wrong chain id: expected {ROBINHOOD_CHAIN_ID}, observed {chain_id}"
        )
    pinned_end = _quantity(identity[2]["result"]["number"])
    start = pinned_end - sample_size + 1
    if start < 0:
        raise ValueError("sample starts before genesis")

    block_calls = [
        {
            "jsonrpc": "2.0",
            "id": index + 1,
            "method": "eth_getBlockByNumber",
            "params": [hex(number), False],
        }
        for index, number in enumerate(range(start, pinned_end + 1))
    ]
    blocks = _rpc(url, block_calls)

    clock_calls = []
    for index, number in enumerate(range(start, pinned_end + 1)):
        tag = hex(number)
        clock_calls.extend(
            [
                {
                    "jsonrpc": "2.0",
                    "id": (index * 2) + 1,
                    "method": "eth_call",
                    "params": [
                        {"to": MULTICALL3, "data": GET_BLOCK_NUMBER},
                        tag,
                    ],
                },
                {
                    "jsonrpc": "2.0",
                    "id": (index * 2) + 2,
                    "method": "eth_call",
                    "params": [
                        {"to": ARB_SYS, "data": ARB_BLOCK_NUMBER},
                        tag,
                    ],
                },
            ]
        )
    clocks = _rpc(url, clock_calls)

    samples = []
    for index, expected_child in enumerate(range(start, pinned_end + 1)):
        block = blocks[index + 1]["result"]
        rpc_child = _quantity(block["number"])
        l1_number = _quantity(block["l1BlockNumber"])
        contract_number = _quantity(clocks[(index * 2) + 1]["result"])
        arb_number = _quantity(clocks[(index * 2) + 2]["result"])
        if rpc_child != expected_child or arb_number != rpc_child:
            raise RuntimeError("child-block or ArbSys identity mismatch")
        samples.append(
            {
                "rpc_child_block": rpc_child,
                "block_hash": block["hash"],
                "l1BlockNumber": l1_number,
                "contract_visible_NUMBER": contract_number,
                "arbSys_arbBlockNumber": arb_number,
                "timestamp": _quantity(block["timestamp"]),
            }
        )

    endpoint = urlparse(url)
    endpoint_label = (
        endpoint.hostname
        if endpoint.hostname == "rpc.mainnet.chain.robinhood.com"
        else "<redacted-provider>"
    )
    unique_numbers = sorted({row["contract_visible_NUMBER"] for row in samples})
    return {
        "schema_version": 1,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "network": "robinhood-mainnet",
        "chain_id": chain_id,
        "rpc_endpoint": endpoint_label,
        "sample_size": sample_size,
        "pinned_child_range": [start, pinned_end],
        "contracts": {
            "multicall3": MULTICALL3,
            "arbSys": ARB_SYS,
            "multicall3_getBlockNumber_selector": GET_BLOCK_NUMBER,
            "arbSys_arbBlockNumber_selector": ARB_BLOCK_NUMBER,
        },
        "summary": {
            "distinct_contract_NUMBER_values": len(unique_numbers),
            "contract_NUMBER_values": unique_numbers,
            "all_l1_numbers_match_contract_NUMBER": all(
                row["l1BlockNumber"] == row["contract_visible_NUMBER"]
                for row in samples
            ),
            "all_arbSys_values_match_rpc_child": all(
                row["arbSys_arbBlockNumber"] == row["rpc_child_block"]
                for row in samples
            ),
        },
        "samples": samples,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rpc-url", default=os.environ.get("ROBINHOOD_MAINNET_RPC_URL"))
    parser.add_argument("--sample-size", type=int, default=16)
    parser.add_argument("--end-block", type=int)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.rpc_url:
        parser.error("--rpc-url or ROBINHOOD_MAINNET_RPC_URL is required")
    if args.sample_size < 2 or args.sample_size > 128:
        parser.error("--sample-size must be between 2 and 128")

    rendered = json.dumps(
        capture(args.rpc_url, args.sample_size, args.end_block),
        indent=2,
        sort_keys=True,
    ) + "\n"
    if args.output:
        args.output.write_text(rendered)
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
