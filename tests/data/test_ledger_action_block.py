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
