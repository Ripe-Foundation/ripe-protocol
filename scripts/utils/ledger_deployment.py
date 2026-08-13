"""Node-backed deployment validation for Ledger action-block sources.

ArbSys is a node-implemented precompile. On chain it appears as a single
``0xfe`` byte and the Arbitrum node intercepts calls to it. Boa's local EVM
instead executes that byte as ``INVALID``, so a local Boa call can revert even
when the live-chain configuration is correct.

The Ledger constructor no longer probes the action-block source; that check
was removed upstream. Node-backed deployment validation is therefore the
control that prevents activation of a Ledger with a wrong or nonfunctional
action-block source. This helper deliberately bypasses Boa and must not be
replaced with a constructor probe.
"""

from scripts.utils import log


MAX_ADDRESS = 2**160 - 1


def _load_web3():
    from web3 import Web3

    return Web3


def _normalize_expected_source(expected_source):
    if isinstance(expected_source, bool) or not isinstance(
        expected_source,
        (int, str),
    ):
        raise TypeError(
            "expected_source must be an integer or 0x-prefixed hex string"
        )

    if isinstance(expected_source, str):
        digits = expected_source[2:] if expected_source.startswith("0x") else ""
        if not digits or any(
            character not in "0123456789abcdefABCDEF" for character in digits
        ):
            raise ValueError(
                "expected_source must be a valid 0x-prefixed hex string"
            )
        normalized = int(digits, 16)
    else:
        normalized = expected_source

    if normalized < 0:
        raise ValueError("expected_source must not be negative")
    if normalized > MAX_ADDRESS:
        raise ValueError("expected_source exceeds the 160-bit address range")
    return normalized


def _read_word(w3, contract_address, signature):
    selector = w3.keccak(text=signature)[:4]
    result = w3.eth.call({"to": contract_address, "data": selector})
    assert len(result) == 32, f"malformed {signature} readback"
    return int.from_bytes(result, "big")


def validate_ledger_action_block_source(
    migration,
    ledger_address,
    expected_source,
    *,
    allow_local_preview=False,
):
    """Validate Ledger's stored source and live action-block behavior via RPC.

    Returns ``None`` only when a local/fork preview skip is explicitly allowed.
    Completed validation returns ``(actual_source, action_block)``; a validated
    zero source returns ``(0, None)`` without calling ``getArbActionBlock()``.
    """
    normalized_source = _normalize_expected_source(expected_source)
    rpc = migration.rpc()
    if not rpc or rpc == "boa":
        if allow_local_preview:
            log.info(
                "\tNode-backed Ledger validation skipped: local/fork preview "
                "has no real RPC."
            )
            return None
        raise AssertionError("production Ledger requires a real RPC node")

    Web3 = _load_web3()
    try:
        w3 = Web3(Web3.HTTPProvider(rpc))
        connected = w3.is_connected()
    except Exception as exc:
        raise AssertionError("production Ledger RPC is unavailable") from exc
    assert connected, "production Ledger RPC is unavailable"

    address = w3.to_checksum_address(ledger_address)
    code = w3.eth.get_code(address)
    if len(code) == 0:
        if allow_local_preview:
            log.info(
                "\tNode-backed Ledger validation skipped: candidate exists "
                "only in the local/fork EVM."
            )
            return None
        raise AssertionError("Ledger is not deployed on the configured RPC")

    actual_source = _read_word(w3, address, "ACTION_BLOCK_SOURCE()")
    assert actual_source == normalized_source, "Ledger action-block source mismatch"

    if normalized_source == 0:
        return 0, None

    action_block = _read_word(w3, address, "getArbActionBlock()")
    assert action_block != 0, "ArbSys action block reads zero"
    return actual_source, action_block
