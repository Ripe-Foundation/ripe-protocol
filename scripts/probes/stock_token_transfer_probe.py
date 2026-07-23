#!/usr/bin/env python3
"""Fail-closed Robinhood Stock Token runner for StockTokenTransferProbe.

This script never signs or broadcasts. The only state-changing mode executes
against a pinned local fork using an impersonated public address. The probe
contract is generic ERC-20 infrastructure; this runner intentionally validates
Robinhood Stock Token proxy, pause, blocklist, and multiplier interfaces.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import boa
import requests
import rlp
from boa.environment import Env
from boa.interpret import set_cache_dir
from eth_abi import decode, encode
from eth_utils import keccak, to_checksum_address


REPO_ROOT = Path(__file__).resolve().parents[2]
PROBE_CONTRACT = REPO_ROOT / "contracts/testing/StockTokenTransferProbe.vy"
BOA_CACHE_ROOT = Path(tempfile.gettempdir()) / "ripe-stock-token-probe-cache"
BEACON_SLOT = "0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50"
HASH_RE = re.compile(r"^0x[0-9a-fA-F]{64}$")

set_cache_dir(BOA_CACHE_ROOT / "compiler")

TOKEN_ABI = [
    {
        "type": "function",
        "name": "approve",
        "stateMutability": "nonpayable",
        "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
        "outputs": [{"name": "", "type": "bool"}],
    },
    {
        "type": "function",
        "name": "balanceOf",
        "stateMutability": "view",
        "inputs": [{"name": "account", "type": "address"}],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "type": "function",
        "name": "allowance",
        "stateMutability": "view",
        "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}],
        "outputs": [{"name": "", "type": "uint256"}],
    },
]

REGISTRY_ABI = [
    {
        "type": "function",
        "name": "isBlocked",
        "stateMutability": "view",
        "inputs": [{"name": "account", "type": "address"}],
        "outputs": [{"name": "", "type": "bool"}],
    },
    {
        "type": "function",
        "name": "paused",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "bool"}],
    },
]


class ApprovalError(RuntimeError):
    """Approved input or observed state did not match."""


@dataclass(frozen=True)
class ApprovedRun:
    network: str
    chain_id: int
    pinned_block: int
    pinned_block_hash: str
    token: str
    token_name: str
    token_symbol: str
    token_decimals: int
    token_code_hash: str
    ui_multiplier: int
    new_ui_multiplier: int
    multiplier_effective_at: int
    beacon: str
    implementation: str
    implementation_code_hash: str
    registry: str
    sender: str
    owner: str
    recipient: str
    amount: int
    expected_probe_address: str
    expected_probe_runtime_code_hash: str


def _required(data: dict[str, Any], key: str) -> Any:
    if key not in data:
        raise ApprovalError(f"missing approved input: {key}")
    return data[key]


def _address(value: Any, field: str) -> str:
    try:
        address = to_checksum_address(value)
    except Exception as exc:
        raise ApprovalError(f"invalid approved address: {field}") from exc
    if int(address, 16) == 0:
        raise ApprovalError(f"zero approved address: {field}")
    return address


def _hash(value: Any, field: str) -> str:
    if not isinstance(value, str) or not HASH_RE.fullmatch(value):
        raise ApprovalError(f"invalid approved hash: {field}")
    return value.lower()


def parse_approval(data: dict[str, Any]) -> ApprovedRun:
    if _required(data, "schema_version") != 1:
        raise ApprovalError("unsupported approval schema")
    if _required(data, "scope") != "fork-only":
        raise ApprovalError("approval scope must be fork-only")
    if _required(data, "broadcast_allowed") is not False:
        raise ApprovalError("broadcast must be disabled")

    token = _required(data, "token")
    probe = _required(data, "probe")
    amount = int(_required(data, "amount"))
    if amount <= 0:
        raise ApprovalError("approved amount must be positive")

    sender = _address(_required(data, "sender"), "sender")
    owner = _address(_required(data, "owner"), "owner")
    if sender != owner:
        raise ApprovalError("approved sender must equal probe owner")

    ui_multiplier = int(_required(token, "ui_multiplier"))
    new_ui_multiplier = int(_required(token, "new_ui_multiplier"))
    multiplier_effective_at = int(_required(token, "multiplier_effective_at"))
    if ui_multiplier <= 0 or new_ui_multiplier <= 0 or multiplier_effective_at < 0:
        raise ApprovalError("invalid approved multiplier state")

    return ApprovedRun(
        network=str(_required(data, "network")),
        chain_id=int(_required(data, "chain_id")),
        pinned_block=int(_required(data, "pinned_block")),
        pinned_block_hash=_hash(_required(data, "pinned_block_hash"), "pinned_block_hash"),
        token=_address(_required(token, "address"), "token.address"),
        token_name=str(_required(token, "name")),
        token_symbol=str(_required(token, "symbol")),
        token_decimals=int(_required(token, "decimals")),
        token_code_hash=_hash(_required(token, "code_hash"), "token.code_hash"),
        ui_multiplier=ui_multiplier,
        new_ui_multiplier=new_ui_multiplier,
        multiplier_effective_at=multiplier_effective_at,
        beacon=_address(_required(token, "beacon"), "token.beacon"),
        implementation=_address(_required(token, "implementation"), "token.implementation"),
        implementation_code_hash=_hash(
            _required(token, "implementation_code_hash"),
            "token.implementation_code_hash",
        ),
        registry=_address(_required(token, "registry"), "token.registry"),
        sender=sender,
        owner=owner,
        recipient=_address(_required(data, "recipient"), "recipient"),
        amount=amount,
        expected_probe_address=_address(
            _required(probe, "expected_address"),
            "probe.expected_address",
        ),
        expected_probe_runtime_code_hash=_hash(
            _required(probe, "runtime_code_hash"),
            "probe.runtime_code_hash",
        ),
    )


def load_approval(path: Path) -> ApprovedRun:
    with path.open() as approval_file:
        return parse_approval(json.load(approval_file))


def _assert_equal(field: str, observed: Any, expected: Any):
    if observed != expected:
        raise ApprovalError(f"{field} mismatch: observed {observed!r}, approved {expected!r}")


def _rpc(rpc_url: str, method: str, params: list[Any]) -> Any:
    response = requests.post(
        rpc_url,
        json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if "error" in payload:
        raise ApprovalError(f"RPC {method} failed: {payload['error']}")
    return payload["result"]


def _block_tag(block_number: int) -> str:
    return hex(block_number)


def _rpc_call(
    rpc_url: str,
    block_number: int,
    contract: str,
    signature: str,
    output_types: list[str],
    input_types: list[str] | None = None,
    args: list[Any] | None = None,
) -> tuple[Any, ...]:
    input_types = input_types or []
    args = args or []
    calldata = keccak(text=signature)[:4] + encode(input_types, args)
    raw = _rpc(
        rpc_url,
        "eth_call",
        [{"to": contract, "data": "0x" + calldata.hex()}, _block_tag(block_number)],
    )
    return decode(output_types, bytes.fromhex(raw[2:]))


def _code_hash(code_hex: str) -> str:
    return "0x" + keccak(bytes.fromhex(code_hex[2:])).hex()


def _predict_create_address(sender: str, nonce: int) -> str:
    encoded = rlp.encode([bytes.fromhex(sender[2:]), nonce])
    return to_checksum_address(keccak(encoded)[-20:])


def _format_token_amount(amount: int, decimals: int) -> str:
    if decimals == 0:
        return str(amount)
    whole, fractional = divmod(amount, 10**decimals)
    if fractional == 0:
        return str(whole)
    return f"{whole}.{fractional:0{decimals}d}".rstrip("0")


def _validate_multiplier_state(
    approved: ApprovedRun,
    ui_multiplier: int,
    new_ui_multiplier: int,
    effective_at: int,
    block_timestamp: int,
):
    _assert_equal("ui_multiplier", ui_multiplier, approved.ui_multiplier)
    _assert_equal("new_ui_multiplier", new_ui_multiplier, approved.new_ui_multiplier)
    _assert_equal(
        "multiplier_effective_at",
        effective_at,
        approved.multiplier_effective_at,
    )
    if effective_at > block_timestamp:
        raise ApprovalError(
            f"pending UI multiplier becomes effective at {effective_at}, "
            f"after pinned block timestamp {block_timestamp}"
        )
    if ui_multiplier != new_ui_multiplier:
        raise ApprovalError("current and scheduled UI multipliers do not reconcile")


def compile_probe_runtime_code_hash(approved: ApprovedRun) -> str:
    with boa.set_env(Env()):
        # Satisfy the constructor's code-presence check in this isolated local
        # environment while preserving the exact approved token address in the
        # immutable runtime configuration.
        boa.env.set_code(approved.token, b"\x00")
        probe = boa.load(
            str(PROBE_CONTRACT),
            approved.owner,
            approved.token,
            approved.recipient,
            name="stock_token_transfer_probe_hash",
        )
        return "0x" + keccak(boa.env.get_code(probe.address)).hex()


def preflight(approved: ApprovedRun, rpc_url: str) -> dict[str, Any]:
    chain_id = int(_rpc(rpc_url, "eth_chainId", []), 16)
    _assert_equal("chain_id", chain_id, approved.chain_id)

    block_tag = _block_tag(approved.pinned_block)
    block = _rpc(rpc_url, "eth_getBlockByNumber", [block_tag, False])
    if block is None:
        raise ApprovalError("approved pinned block is unavailable")
    _assert_equal("pinned_block_hash", block["hash"].lower(), approved.pinned_block_hash)
    block_timestamp = int(block["timestamp"], 16)

    token_code = _rpc(rpc_url, "eth_getCode", [approved.token, block_tag])
    if token_code == "0x":
        raise ApprovalError("approved token has no code")
    _assert_equal("token_code_hash", _code_hash(token_code), approved.token_code_hash)

    name = _rpc_call(rpc_url, approved.pinned_block, approved.token, "name()", ["string"])[0]
    symbol = _rpc_call(rpc_url, approved.pinned_block, approved.token, "symbol()", ["string"])[0]
    decimals = _rpc_call(rpc_url, approved.pinned_block, approved.token, "decimals()", ["uint8"])[0]
    _assert_equal("token_name", name, approved.token_name)
    _assert_equal("token_symbol", symbol, approved.token_symbol)
    _assert_equal("token_decimals", decimals, approved.token_decimals)

    ui_multiplier = _rpc_call(
        rpc_url,
        approved.pinned_block,
        approved.token,
        "uiMultiplier()",
        ["uint256"],
    )[0]
    new_ui_multiplier = _rpc_call(
        rpc_url,
        approved.pinned_block,
        approved.token,
        "newUIMultiplier()",
        ["uint256"],
    )[0]
    multiplier_effective_at = _rpc_call(
        rpc_url,
        approved.pinned_block,
        approved.token,
        "effectiveAt()",
        ["uint256"],
    )[0]
    _validate_multiplier_state(
        approved,
        ui_multiplier,
        new_ui_multiplier,
        multiplier_effective_at,
        block_timestamp,
    )

    beacon_word = _rpc(
        rpc_url,
        "eth_getStorageAt",
        [approved.token, BEACON_SLOT, block_tag],
    )
    beacon = to_checksum_address("0x" + beacon_word[-40:])
    _assert_equal("token_beacon", beacon, approved.beacon)
    _assert_equal("token_registry", beacon, approved.registry)

    implementation = _rpc_call(
        rpc_url,
        approved.pinned_block,
        approved.beacon,
        "implementation()",
        ["address"],
    )[0]
    implementation = to_checksum_address(implementation)
    _assert_equal("token_implementation", implementation, approved.implementation)
    implementation_code = _rpc(rpc_url, "eth_getCode", [implementation, block_tag])
    _assert_equal(
        "implementation_code_hash",
        _code_hash(implementation_code),
        approved.implementation_code_hash,
    )

    global_paused = _rpc_call(
        rpc_url,
        approved.pinned_block,
        approved.registry,
        "paused()",
        ["bool"],
    )[0]
    token_paused = _rpc_call(
        rpc_url,
        approved.pinned_block,
        approved.token,
        "tokenPaused()",
        ["bool"],
    )[0]
    oracle_paused = _rpc_call(
        rpc_url,
        approved.pinned_block,
        approved.token,
        "oraclePaused()",
        ["bool"],
    )[0]
    if global_paused or token_paused or oracle_paused:
        raise ApprovalError("token or oracle is paused at the pinned block")

    sender_balance = _rpc_call(
        rpc_url,
        approved.pinned_block,
        approved.token,
        "balanceOf(address)",
        ["uint256"],
        ["address"],
        [approved.sender],
    )[0]
    recipient_balance = _rpc_call(
        rpc_url,
        approved.pinned_block,
        approved.token,
        "balanceOf(address)",
        ["uint256"],
        ["address"],
        [approved.recipient],
    )[0]
    native_balance = int(
        _rpc(rpc_url, "eth_getBalance", [approved.sender, block_tag]),
        16,
    )
    if sender_balance < approved.amount:
        raise ApprovalError("approved sender has insufficient token balance")
    if native_balance == 0:
        raise ApprovalError("approved sender has no native gas balance")

    nonce = int(
        _rpc(rpc_url, "eth_getTransactionCount", [approved.sender, block_tag]),
        16,
    )
    predicted_probe = _predict_create_address(approved.sender, nonce)
    _assert_equal("probe_address", predicted_probe, approved.expected_probe_address)

    blocked: dict[str, bool] = {}
    for label, address in {
        "sender": approved.sender,
        "owner": approved.owner,
        "recipient": approved.recipient,
        "probe": predicted_probe,
    }.items():
        blocked[label] = _rpc_call(
            rpc_url,
            approved.pinned_block,
            approved.registry,
            "isBlocked(address)",
            ["bool"],
            ["address"],
            [address],
        )[0]
        if blocked[label]:
            raise ApprovalError(f"approved {label} is blocked")

    compiled_hash = compile_probe_runtime_code_hash(approved)
    _assert_equal(
        "probe_runtime_code_hash",
        compiled_hash,
        approved.expected_probe_runtime_code_hash,
    )

    sender_after_deposit = sender_balance - approved.amount
    recipient_after_withdraw = recipient_balance + approved.amount
    if approved.sender == approved.recipient:
        sender_after_withdraw = sender_balance
        recipient_after_withdraw = sender_balance
    else:
        sender_after_withdraw = sender_after_deposit

    return {
        "mode": "dry-run",
        "broadcast_enabled": False,
        "network": approved.network,
        "chain_id": approved.chain_id,
        "pinned_block": approved.pinned_block,
        "pinned_block_hash": approved.pinned_block_hash,
        "pinned_block_timestamp": block_timestamp,
        "token": approved.token,
        "token_symbol": approved.token_symbol,
        "sender": approved.sender,
        "owner": approved.owner,
        "recipient": approved.recipient,
        "amount": str(approved.amount),
        "amount_formatted": _format_token_amount(approved.amount, approved.token_decimals),
        "predicted_probe": predicted_probe,
        "probe_runtime_code_hash": compiled_hash,
        "multiplier_state": {
            "ui_multiplier": str(ui_multiplier),
            "new_ui_multiplier": str(new_ui_multiplier),
            "effective_at": str(multiplier_effective_at),
            "pending": False,
        },
        "blocked": blocked,
        "expected_balance_changes": {
            "sender_before": str(sender_balance),
            "sender_after_deposit": str(sender_after_deposit),
            "sender_after_withdraw": str(sender_after_withdraw),
            "recipient_before": str(recipient_balance),
            "recipient_after_withdraw": str(recipient_after_withdraw),
            "probe_before": "0",
            "probe_after_deposit": str(approved.amount),
            "probe_after_withdraw": "0",
            "allowance_after_approve": str(approved.amount),
            "allowance_after_deposit": "0",
            "allowance_after_cleanup": "0",
        },
        "sender_native_balance": str(native_balance),
        "sender_native_balance_check": "nonzero-fork-only",
        "transaction_sequence": [
            "deploy StockTokenTransferProbe",
            "approve exact amount",
            "deposit exact amount",
            "verify exact probe balance",
            "withdraw exact amount to configured recipient",
            "clear allowance to zero",
            "verify final balances and events",
        ],
    }


def execute_fork(approved: ApprovedRun, rpc_url: str) -> dict[str, Any]:
    report = preflight(approved, rpc_url)

    with boa.fork(
        rpc_url,
        block_identifier=approved.pinned_block,
        allow_dirty=True,
        cache_dir=str(BOA_CACHE_ROOT / "fork"),
    ):
        _assert_equal("fork_chain_id", boa.env.evm.patch.chain_id, approved.chain_id)
        token = boa.loads_abi(json.dumps(TOKEN_ABI), name="approved_stock_token").at(approved.token)
        registry = boa.loads_abi(json.dumps(REGISTRY_ABI), name="stock_token_registry").at(approved.registry)

        sender_before = token.balanceOf(approved.sender)
        recipient_before = token.balanceOf(approved.recipient)
        allowance_before = token.allowance(approved.sender, approved.expected_probe_address)
        if allowance_before != 0:
            raise ApprovalError("predicted probe already has a nonzero allowance")

        with boa.env.prank(approved.sender):
            probe = boa.load(
                str(PROBE_CONTRACT),
                approved.owner,
                approved.token,
                approved.recipient,
                name="stock_token_transfer_probe_fork",
            )
        deploy_gas_used = probe._computation.get_gas_used()
        _assert_equal("deployed_probe_address", probe.address, approved.expected_probe_address)
        deployed_hash = "0x" + keccak(boa.env.get_code(probe.address)).hex()
        _assert_equal(
            "deployed_probe_runtime_code_hash",
            deployed_hash,
            approved.expected_probe_runtime_code_hash,
        )
        if registry.isBlocked(probe.address):
            raise ApprovalError("deployed probe is blocked")

        approval_succeeded = token.approve(
            probe.address,
            approved.amount,
            sender=approved.sender,
        )
        if not approval_succeeded:
            raise ApprovalError("exact token approval returned false")
        approve_gas_used = token._computation.get_gas_used()
        _assert_equal(
            "allowance_after_approve",
            token.allowance(approved.sender, probe.address),
            approved.amount,
        )

        probe.deposit(approved.amount, sender=approved.sender)
        deposit_gas_used = probe._computation.get_gas_used()
        deposit_events = [
            event
            for event in probe.get_logs(strict=False)
            if type(event).__name__ == "TokenDeposited"
        ]
        if len(deposit_events) != 1:
            raise ApprovalError("expected exactly one TokenDeposited event")
        _assert_equal(
            "sender_after_deposit",
            token.balanceOf(approved.sender),
            sender_before - approved.amount,
        )
        _assert_equal("probe_after_deposit", token.balanceOf(probe.address), approved.amount)
        _assert_equal(
            "allowance_after_deposit",
            token.allowance(approved.sender, probe.address),
            0,
        )

        probe.withdraw(approved.amount, sender=approved.owner)
        withdraw_gas_used = probe._computation.get_gas_used()
        withdrawal_events = [
            event
            for event in probe.get_logs(strict=False)
            if type(event).__name__ == "TokenWithdrawn"
        ]
        if len(withdrawal_events) != 1:
            raise ApprovalError("expected exactly one TokenWithdrawn event")
        _assert_equal("probe_after_withdraw", token.balanceOf(probe.address), 0)
        expected_recipient_final = (
            recipient_before
            if approved.sender == approved.recipient
            else recipient_before + approved.amount
        )
        _assert_equal(
            "recipient_after_withdraw",
            token.balanceOf(approved.recipient),
            expected_recipient_final,
        )

        cleanup_succeeded = token.approve(probe.address, 0, sender=approved.sender)
        if not cleanup_succeeded:
            raise ApprovalError("allowance cleanup returned false")
        cleanup_gas_used = token._computation.get_gas_used()
        _assert_equal(
            "allowance_after_cleanup",
            token.allowance(approved.sender, probe.address),
            0,
        )

        events = [
            {
                "event": type(event).__name__,
                "amount": str(event.amount),
                "token": str(event.token),
            }
            for event in deposit_events + withdrawal_events
        ]

        report.update(
            {
                "mode": "fork",
                "broadcast_enabled": False,
                "probe_address": probe.address,
                "deployed_probe_runtime_code_hash": deployed_hash,
                "fork_results": {
                    "sender_before": str(sender_before),
                    "sender_final": str(token.balanceOf(approved.sender)),
                    "recipient_before": str(recipient_before),
                    "recipient_final": str(token.balanceOf(approved.recipient)),
                    "probe_final": str(token.balanceOf(probe.address)),
                    "allowance_final": str(token.allowance(approved.sender, probe.address)),
                    "events": events,
                    "evm_gas_used": {
                        "deploy": deploy_gas_used,
                        "approve": approve_gas_used,
                        "deposit": deposit_gas_used,
                        "withdraw": withdraw_gas_used,
                        "allowance_cleanup": cleanup_gas_used,
                        "total": (
                            deploy_gas_used
                            + approve_gas_used
                            + deposit_gas_used
                            + withdraw_gas_used
                            + cleanup_gas_used
                        ),
                    },
                },
                "fork_limitations": [
                    "The sender was impersonated; no private key or signature was used.",
                    "Transactions modified only local fork state and were not broadcast.",
                    "The probe deployment address depends on the pinned sender nonce.",
                    "Reported EVM gas is fork-measured execution gas, not a live fee quote or approved maximum.",
                    "Fork success does not establish legal eligibility or future transferability.",
                ],
            }
        )
        return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approval-file", type=Path, required=True)
    parser.add_argument("--rpc-url", required=True)
    parser.add_argument("--fork", action="store_true", help="Execute on local pinned fork state")
    parser.add_argument("--broadcast", action="store_true", help="Rejected; broadcasting is not implemented")
    args = parser.parse_args()

    if args.broadcast:
        raise ApprovalError("broadcast is disabled; Phase D approval and implementation are required")

    approved = load_approval(args.approval_file)
    report = execute_fork(approved, args.rpc_url) if args.fork else preflight(approved, args.rpc_url)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def cli() -> int:
    try:
        return main()
    except ApprovalError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(cli())
