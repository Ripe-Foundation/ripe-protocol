import boa
import pytest
from eth_utils import to_checksum_address

from constants import ZERO_ADDRESS


LEDGER_PATH = "contracts/data/Ledger.vy"
ARB_SYS = to_checksum_address("0x0000000000000000000000000000000000000064")


def _install_arb_sys(action_block=1):
    implementation = boa.loads(
        """# @version 0.4.3
actionBlock: uint256

@view
@external
def arbBlockNumber() -> uint256:
    return self.actionBlock
""",
        name="ledger_action_block_source",
    )
    boa.env.set_code(ARB_SYS, boa.env.get_code(implementation.address))
    boa.env.set_storage(ARB_SYS, 0, action_block)


def _set_arb_action_block(action_block):
    boa.env.set_storage(ARB_SYS, 0, action_block)


def _install_arb_sys_failure(kind):
    if kind == "missing":
        boa.env.set_code(ARB_SYS, b"")
    elif kind == "reverting":
        boa.env.set_code(ARB_SYS, bytes.fromhex("60006000fd"))
    elif kind in {
        "short_31",
        "oversized_33",
        "oversized_64",
        "oversized_gt_64",
    }:
        return_size = {
            "short_31": 31,
            "oversized_33": 33,
            "oversized_64": 64,
            "oversized_gt_64": 96,
        }[kind]
        # Return zero-initialized data of the requested exact size. Capturing
        # 65 bytes makes every oversized case observable as len != 32.
        boa.env.set_code(
            ARB_SYS,
            bytes([0x60, return_size, 0x60, 0x00, 0xF3]),
        )
    else:
        assert kind == "incompatible"
        implementation = boa.loads(
            """# @version 0.4.3
@view
@external
def wrongBlockNumber() -> uint256:
    return block.number
""",
            name="incompatible_ledger_action_block_source",
        )
        boa.env.set_code(ARB_SYS, boa.env.get_code(implementation.address))


def _deploy_ledger(ripe_hq_deploy, defaults, source, name="action_block_ledger"):
    return boa.load(
        LEDGER_PATH,
        ripe_hq_deploy,
        defaults,
        source,
        name=name,
    )


def test_native_source_getter_and_action_identity_match_block_number(
    ledger,
    teller,
    alice,
):
    assert ledger.ACTION_BLOCK_SOURCE() == ZERO_ADDRESS

    for increment in (0, 1, 2, 4, 60):
        if increment:
            boa.env.time_travel(blocks=increment)
        ledger.checkAndUpdateLastTouch(alice, True, sender=teller.address)
        assert ledger.lastTouch(alice) == boa.env.evm.patch.block_number


@pytest.mark.parametrize(
    "source",
    [
        to_checksum_address("0x0000000000000000000000000000000000000001"),
        to_checksum_address("0x0000000000000000000000000000000000000063"),
        to_checksum_address("0x0000000000000000000000000000000000000065"),
    ],
)
def test_constructor_rejects_every_nonzero_non_arb_sys_source(
    ripe_hq_deploy,
    defaults,
    source,
):
    with boa.reverts("invalid action block source"):
        _deploy_ledger(ripe_hq_deploy, defaults, source)


@pytest.mark.parametrize(
    "failure",
    [
        "missing",
        "reverting",
        "short_31",
        "oversized_33",
        "oversized_64",
        "oversized_gt_64",
        "incompatible",
    ],
)
def test_arb_sys_constructor_fails_closed_when_call_or_decode_is_invalid(
    ripe_hq_deploy,
    defaults,
    failure,
):
    _install_arb_sys_failure(failure)
    with boa.reverts():
        _deploy_ledger(ripe_hq_deploy, defaults, ARB_SYS)


def test_arb_sys_constructor_validates_call_and_exposes_immutable_source(
    ripe_hq_deploy,
    defaults,
):
    _install_arb_sys(700)
    ledger = _deploy_ledger(ripe_hq_deploy, defaults, ARB_SYS)
    assert ledger.ACTION_BLOCK_SOURCE() == ARB_SYS


def test_arb_sys_identity_not_native_block_controls_equality(
    ripe_hq_deploy,
    defaults,
    teller,
    alice,
):
    _install_arb_sys(700)
    ledger = _deploy_ledger(ripe_hq_deploy, defaults, ARB_SYS)

    ledger.checkAndUpdateLastTouch(alice, True, sender=teller.address)
    assert ledger.lastTouch(alice) == 700

    # Native block advancement cannot clear an unchanged child action block.
    boa.env.time_travel(blocks=60)
    with boa.reverts("one action per block"):
        ledger.checkAndUpdateLastTouch(alice, True, sender=teller.address)
    assert ledger.lastTouch(alice) == 700

    # Explicit child action-block advancement clears the equality guard.
    _set_arb_action_block(701)
    ledger.checkAndUpdateLastTouch(alice, True, sender=teller.address)
    assert ledger.lastTouch(alice) == 701


def test_arb_sys_preserves_equality_only_without_monotonicity_assertion(
    ripe_hq_deploy,
    defaults,
    teller,
    alice,
):
    _install_arb_sys(750)
    ledger = _deploy_ledger(ripe_hq_deploy, defaults, ARB_SYS)

    ledger.checkAndUpdateLastTouch(alice, True, sender=teller.address)
    _set_arb_action_block(749)
    ledger.checkAndUpdateLastTouch(alice, True, sender=teller.address)
    assert ledger.lastTouch(alice) == 749


def test_arb_sys_preserves_low_high_and_high_low_high_ordering(
    ripe_hq_deploy,
    defaults,
    teller,
    alice,
):
    _install_arb_sys(800)
    ledger = _deploy_ledger(ripe_hq_deploy, defaults, ARB_SYS)

    # Low-risk touches arm a later checked action.
    ledger.checkAndUpdateLastTouch(alice, False, sender=teller.address)
    with boa.reverts("one action per block"):
        ledger.checkAndUpdateLastTouch(alice, True, sender=teller.address)

    _set_arb_action_block(801)
    ledger.checkAndUpdateLastTouch(alice, True, sender=teller.address)
    ledger.checkAndUpdateLastTouch(alice, False, sender=teller.address)
    with boa.reverts("one action per block"):
        ledger.checkAndUpdateLastTouch(alice, True, sender=teller.address)


def test_arb_sys_keeps_users_isolated_within_one_action_block(
    ripe_hq_deploy,
    defaults,
    teller,
    alice,
    bob,
):
    _install_arb_sys(900)
    ledger = _deploy_ledger(ripe_hq_deploy, defaults, ARB_SYS)

    ledger.checkAndUpdateLastTouch(alice, True, sender=teller.address)
    ledger.checkAndUpdateLastTouch(bob, True, sender=teller.address)
    assert ledger.lastTouch(alice) == ledger.lastTouch(bob) == 900

    with boa.reverts("one action per block"):
        ledger.checkAndUpdateLastTouch(alice, True, sender=teller.address)
    with boa.reverts("one action per block"):
        ledger.checkAndUpdateLastTouch(bob, True, sender=teller.address)


@pytest.mark.parametrize(
    "failure",
    [
        "missing",
        "reverting",
        "short_31",
        "oversized_33",
        "oversized_64",
        "oversized_gt_64",
        "incompatible",
    ],
)
def test_arb_sys_runtime_failure_reverts_without_fallback_or_partial_write(
    ripe_hq_deploy,
    defaults,
    teller,
    alice,
    failure,
):
    _install_arb_sys(1_000)
    ledger = _deploy_ledger(ripe_hq_deploy, defaults, ARB_SYS)
    ledger.checkAndUpdateLastTouch(alice, False, sender=teller.address)

    native_block = boa.env.evm.patch.block_number
    _install_arb_sys_failure(failure)
    boa.env.time_travel(blocks=1)

    with boa.reverts():
        ledger.checkAndUpdateLastTouch(alice, False, sender=teller.address)
    assert ledger.lastTouch(alice) == 1_000
    assert ledger.lastTouch(alice) != native_block + 1


@pytest.mark.parametrize("source", [ZERO_ADDRESS, ARB_SYS])
@pytest.mark.parametrize("should_check", [False, True])
def test_lock_enforcement_remains_after_write_in_both_source_modes(
    ripe_hq_deploy,
    defaults,
    teller,
    switchboard_alpha,
    alice,
    source,
    should_check,
):
    if source == ARB_SYS:
        _install_arb_sys(1_100)
    ledger = _deploy_ledger(
        ripe_hq_deploy,
        defaults,
        source,
        name=f"locked_action_block_ledger_{source}",
    )
    ledger.setLockedAccount(alice, True, sender=switchboard_alpha.address)

    with boa.reverts("account locked"):
        ledger.checkAndUpdateLastTouch(
            alice,
            should_check,
            sender=teller.address,
        )
    assert ledger.lastTouch(alice) == 0


@pytest.mark.parametrize("source", [ZERO_ADDRESS, ARB_SYS])
@pytest.mark.parametrize("should_check", [False, True])
def test_pause_and_teller_authority_remain_fail_closed_in_both_source_modes(
    ripe_hq_deploy,
    defaults,
    teller,
    switchboard_alpha,
    alice,
    source,
    should_check,
):
    if source == ARB_SYS:
        _install_arb_sys(1_200)
    ledger = _deploy_ledger(
        ripe_hq_deploy,
        defaults,
        source,
        name=f"paused_action_block_ledger_{source}",
    )

    with boa.reverts("only Teller allowed"):
        ledger.checkAndUpdateLastTouch(
            alice,
            should_check,
            sender=alice,
        )

    ledger.pause(True, sender=switchboard_alpha.address)
    with boa.reverts("not activated"):
        ledger.checkAndUpdateLastTouch(
            alice,
            should_check,
            sender=teller.address,
        )
    assert ledger.lastTouch(alice) == 0


@pytest.mark.parametrize("source", [ZERO_ADDRESS, ARB_SYS])
def test_zero_address_identity_behavior_is_preserved_in_both_source_modes(
    ripe_hq_deploy,
    defaults,
    teller,
    source,
):
    action_block = 1_300
    if source == ARB_SYS:
        _install_arb_sys(action_block)
    ledger = _deploy_ledger(
        ripe_hq_deploy,
        defaults,
        source,
        name=f"zero_user_action_block_ledger_{source}",
    )

    ledger.checkAndUpdateLastTouch(ZERO_ADDRESS, True, sender=teller.address)
    expected = (
        boa.env.evm.patch.block_number if source == ZERO_ADDRESS else action_block
    )
    assert ledger.lastTouch(ZERO_ADDRESS) == expected


def _deploy_ledger_source(
    source,
    ripe_hq_deploy,
    defaults,
    action_block_source,
    name,
):
    return boa.loads(
        source,
        ripe_hq_deploy,
        defaults,
        action_block_source,
        name=name,
        override_address=boa.env.generate_address(),
    )


def _replace_once(source, old, new):
    assert source.count(old) == 1
    return source.replace(old, new)


def _l3a_mutant_source(kind):
    from pathlib import Path

    source = Path(LEDGER_PATH).read_text()
    helper = """@view
@internal
def _getArbActionBlock() -> uint256:
    response: Bytes[65] = raw_call(
        ARB_SYS,
        method_id("arbBlockNumber()", output_type=Bytes[4]),
        max_outsize=65,
        is_static_call=True,
        revert_on_failure=True,
    )
    assert len(response) == 32 # dev: invalid action block response
    return abi_decode(response, uint256)
"""
    if kind == "typed_call":
        source = _replace_once(
            source,
            "from interfaces import Defaults\n",
            """from interfaces import Defaults

interface MutantArbSys:
    def arbBlockNumber() -> uint256: view
""",
        )
        return _replace_once(
            source,
            helper,
            """@view
@internal
def _getArbActionBlock() -> uint256:
    return staticcall MutantArbSys(ARB_SYS).arbBlockNumber()
""",
        )
    if kind == "truncation":
        source = _replace_once(
            source,
            "response: Bytes[65] = raw_call(",
            "response: Bytes[32] = raw_call(",
        )
        return _replace_once(
            source,
            "        max_outsize=65,",
            "        max_outsize=32,",
        )
    if kind == "no_constructor_probe":
        return _replace_once(
            source,
            """    if _actionBlockSource == ARB_SYS:
        _: uint256 = self._getArbActionBlock()

""",
            "",
        )
    if kind == "native_fallback":
        mutant_helper = """@view
@internal
def _getArbActionBlock() -> uint256:
    success: bool = False
    response: Bytes[65] = b""
    success, response = raw_call(
        ARB_SYS,
        method_id("arbBlockNumber()", output_type=Bytes[4]),
        max_outsize=65,
        is_static_call=True,
        revert_on_failure=False,
    )
    if not success or len(response) != 32:
        return __NATIVE_BLOCK__
    return abi_decode(response, uint256)
""".replace("__NATIVE_BLOCK__", "block" + ".number")
        return _replace_once(source, helper, mutant_helper)
    if kind == "monotonic":
        return _replace_once(
            source,
            "assert self.lastTouch[_user] != actionBlock",
            "assert self.lastTouch[_user] < actionBlock",
        )
    raise AssertionError(f"unknown L3a mutant: {kind}")


def test_l2_both_check_and_update_last_touch_selectors_share_teller_gated_body(
    ledger,
    teller,
    alice,
    bob,
):
    from eth_utils import keccak

    assert keccak(text="checkAndUpdateLastTouch(address,bool)")[:4].hex() == (
        "222a390e"
    )
    assert keccak(
        text="checkAndUpdateLastTouch(address,bool,address)"
    )[:4].hex() == "ec74f007"

    with boa.reverts("only Teller allowed"):
        ledger.checkAndUpdateLastTouch(alice, False, sender=alice)
    with boa.reverts("only Teller allowed"):
        ledger.checkAndUpdateLastTouch(alice, False, bob, sender=alice)

    ledger.checkAndUpdateLastTouch(alice, False, sender=teller.address)
    first_identity = boa.env.evm.patch.block_number
    assert ledger.lastTouch(alice) == first_identity

    boa.env.time_travel(blocks=1)
    ledger.checkAndUpdateLastTouch(
        bob,
        False,
        alice,
        sender=teller.address,
    )
    assert ledger.lastTouch(bob) == first_identity + 1


L3A_KILLING_TESTS = {
    "typed_call": (
        "test_arb_sys_constructor_fails_closed_when_call_or_decode_is_invalid"
    ),
    "truncation": (
        "test_arb_sys_constructor_fails_closed_when_call_or_decode_is_invalid"
    ),
    "no_constructor_probe": (
        "test_arb_sys_constructor_fails_closed_when_call_or_decode_is_invalid"
    ),
    "native_fallback": (
        "test_arb_sys_runtime_failure_reverts_without_fallback_or_partial_write"
    ),
    "monotonic": (
        "test_arb_sys_preserves_equality_only_without_monotonicity_assertion"
    ),
}


@pytest.mark.parametrize(
    ("kind", "expected_sha256"),
    [
        (
            "typed_call",
            "0357682c8018c9cec062179f1d2020109000d890950590b2b5d2f8c590f9e6b4",
        ),
        (
            "truncation",
            "3012fdbc09bf750980dae1e08da48b014c846345b16dd3ca0e8ee8eaf8043865",
        ),
        (
            "no_constructor_probe",
            "d847811d29fb7eede2c6be62938703cd508d4196ab47e543fb206d42d3a6c073",
        ),
        (
            "native_fallback",
            "1379dd6a5e67703db3e1a3c00fa0063be4e993540117ebc624657ca4510ac25d",
        ),
        (
            "monotonic",
            "94bc87b5d2549444b3ed3fe9f01d90275643e92697716899ea3f99307780abdb",
        ),
    ],
)
def test_l3a_mutant_source_identities_are_frozen(kind, expected_sha256):
    import hashlib

    assert L3A_KILLING_TESTS[kind] in globals()
    assert hashlib.sha256(_l3a_mutant_source(kind).encode()).hexdigest() == (
        expected_sha256
    )


def test_l3a_typed_call_mutant_fails_oversized_constructor_case(
    ripe_hq_deploy,
    defaults,
):
    _install_arb_sys_failure("oversized_64")
    mutant = _deploy_ledger_source(
        _l3a_mutant_source("typed_call"),
        ripe_hq_deploy,
        defaults,
        ARB_SYS,
        "l3a_typed_call_ledger",
    )
    assert mutant.ACTION_BLOCK_SOURCE() == ARB_SYS


def test_l3a_truncation_mutant_fails_oversized_constructor_case(
    ripe_hq_deploy,
    defaults,
):
    _install_arb_sys_failure("oversized_64")
    mutant = _deploy_ledger_source(
        _l3a_mutant_source("truncation"),
        ripe_hq_deploy,
        defaults,
        ARB_SYS,
        "l3a_truncated_return_ledger",
    )
    assert mutant.ACTION_BLOCK_SOURCE() == ARB_SYS


def test_l3a_removed_probe_mutant_fails_missing_constructor_case(
    ripe_hq_deploy,
    defaults,
):
    _install_arb_sys_failure("missing")
    mutant = _deploy_ledger_source(
        _l3a_mutant_source("no_constructor_probe"),
        ripe_hq_deploy,
        defaults,
        ARB_SYS,
        "l3a_no_constructor_probe_ledger",
    )
    assert mutant.ACTION_BLOCK_SOURCE() == ARB_SYS


def test_l3a_native_fallback_mutant_fails_runtime_source_failure_case(
    ripe_hq_deploy,
    defaults,
    teller,
    alice,
):
    _install_arb_sys(1_400)
    mutant = _deploy_ledger_source(
        _l3a_mutant_source("native_fallback"),
        ripe_hq_deploy,
        defaults,
        ARB_SYS,
        "l3a_native_fallback_ledger",
    )
    mutant.checkAndUpdateLastTouch(
        alice,
        False,
        sender=teller.address,
    )
    _install_arb_sys_failure("missing")
    boa.env.time_travel(blocks=1)
    mutant.checkAndUpdateLastTouch(
        alice,
        False,
        sender=teller.address,
    )
    assert mutant.lastTouch(alice) == boa.env.evm.patch.block_number
    assert mutant.lastTouch(alice) != 1_400


def test_l3a_monotonic_mutant_fails_equality_only_regression_case(
    ripe_hq_deploy,
    defaults,
    teller,
    alice,
):
    _install_arb_sys(1_500)
    mutant = _deploy_ledger_source(
        _l3a_mutant_source("monotonic"),
        ripe_hq_deploy,
        defaults,
        ARB_SYS,
        "l3a_monotonic_ledger",
    )
    mutant.checkAndUpdateLastTouch(
        alice,
        True,
        sender=teller.address,
    )
    _set_arb_action_block(1_499)
    with boa.reverts():
        mutant.checkAndUpdateLastTouch(
            alice,
            True,
            sender=teller.address,
        )
    assert mutant.lastTouch(alice) == 1_500
