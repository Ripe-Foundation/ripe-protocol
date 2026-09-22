"""Optional conversion/price outcomes and integer boundaries in the real helper."""

import boa
import pytest
from conf_legacy_pool import calls_to
from conf_utils import clear_transient_storage
from constants import EIGHTEEN_DECIMALS as WAD
from constants import MAX_UINT256


def install_pool_reads(e, token, value=WAD, nav=WAD):
    code = boa.loads(f"""
@external
@view
def isPaused() -> bool:
    return False
@external
@view
def totalClaimableBalances(a: address) -> uint256:
    return 0
@external
@view
def getUserAssetAtIndexAndHasBalance(u: address, i: uint256) -> (address, bool):
    return {token.address}, True
@external
@view
def getTotalAmountForUser(u: address, a: address) -> uint256:
    return {nav}
@external
@view
def getTotalUserValue(u: address, a: address) -> uint256:
    return {value}
""")
    boa.env.set_code(e.pool.address, boa.env.get_code(code.address))


def short_reply_with_valid_balance(custody):
    # Return one byte for the optional selector, but a valid uint256 for the
    # mandatory ERC20 balanceOf read preceding it. Labels are byte offsets.
    selector_check = bytes.fromhex("5f3560e01c6370a0823114")
    short = bytes.fromhex("60015f526001601ff3")
    destination = len(selector_check) + 3 + len(short)
    normal = b"\x5b\x7f" + custody.to_bytes(32, "big") + bytes.fromhex("5f5260205ff3")
    return selector_check + bytes([0x60, destination, 0x57]) + short + normal


@pytest.mark.parametrize("target", ["conversion", "price"])
@pytest.mark.parametrize(
    "response", ["valid", "revert", "empty", "short", "overlong", "zero", "exhausted"]
)
def test_final_optional_reads_preserve_fail_soft_contract(legacy_env, target, response):
    e = legacy_env
    token = e.sg if target == "conversion" else e.lp
    e.deposit(e.bob, WAD, token)
    install_pool_reads(e, token)
    address = e.sg.address if target == "conversion" else e.pd.address
    signature = (
        "convertToAssets(uint256)"
        if target == "conversion"
        else "getUsdValue(address,uint256)"
    )
    declaration = (
        "convertToAssets(n: uint256)"
        if target == "conversion"
        else "getUsdValue(a: address, n: uint256)"
    )
    if response == "short":
        runtime = short_reply_with_valid_balance(WAD)
    else:
        body = {
            "valid": f" -> uint256:\n    return {WAD}",
            "zero": " -> uint256:\n    return 0",
            "revert": " -> uint256:\n    raise",
            "empty": ":\n    pass",
            "overlong": " -> Bytes[32]:\n    return b'not a uint'",
            "exhausted": " -> uint256:\n    x: bytes32 = empty(bytes32)\n    for i: uint256 in range(1_000_000):\n        x = keccak256(x)\n    return convert(x, uint256)",
        }[response]
        source = f"@external\n@view\ndef {declaration}{body}\n"
        source += f"@external\n@view\ndef balanceOf(a: address) -> uint256:\n    return {WAD}\n"
        probe = boa.loads(source)
        runtime = boa.env.get_code(probe.address)
    boa.env.set_code(address, runtime)
    clear_transient_storage()
    assert e.book.getDeleverageTraversalAsset(
        e.bob, e.pool, 1, True, gas=20_000_000
    ) == (token.address, WAD if response == "valid" else 0)
    calls = calls_to(e.book._computation, address, signature)
    assert len(calls) == 1 and calls[0].msg.gas == 8_000_000
    if response == "exhausted":
        assert calls[0].is_error and calls[0].get_gas_remaining() == 0
    elif response == "short":
        assert not calls[0].is_error and bytes(calls[0].output) == b"\x01"
    elif response == "revert":
        assert calls[0].is_error


@pytest.mark.parametrize("delta", [-1, 0, 1])
def test_user_value_multiplication_boundary(legacy_env, delta):
    e = legacy_env
    e.deposit(e.bob, WAD)
    # Synthetic upper boundary only; no assertion that such values are realistic.
    value = MAX_UINT256 // WAD + delta
    install_pool_reads(e, e.lp, value=value, nav=123)
    clear_transient_storage()
    assert e.nav() == (e.lp.address, 0 if delta == 1 else 123)
    quotes = calls_to(e.book._computation, e.pd.address, "getUsdValue(address,uint256)")
    assert len(quotes) == (0 if delta == 1 else 1)


@pytest.mark.parametrize("custody_value", [WAD - 1, WAD, WAD + 1])
@pytest.mark.parametrize("user_value", [1, 2, 3])
def test_smallest_executable_payment_retains_full_nav(
    legacy_env, custody_value, user_value
):
    e = legacy_env
    e.deposit(e.bob, WAD)
    install_pool_reads(e, e.lp, value=user_value, nav=999)
    quote = boa.loads(f"""
@external
@view
def getUsdValue(a: address, n: uint256) -> uint256:
    return {custody_value}
""")
    boa.env.set_code(e.pd.address, boa.env.get_code(quote.address))
    # At a price just below one, value=1 has a one-unit payout worth zero;
    # just above one it has a zero-unit payout. Value>=2 clears both floors.
    eligible = custody_value == WAD or user_value >= 2
    clear_transient_storage()
    assert e.nav() == (e.lp.address, 999 if eligible else 0)
