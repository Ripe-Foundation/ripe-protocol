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


def test_native_action_block_mode_does_not_call_arb_sys(
    ledger,
    teller,
    alice,
):
    assert ledger.ACTION_BLOCK_SOURCE() == ZERO_ADDRESS
    _install_arb_sys_failure("reverting")

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
def test_arb_sys_constructor_defers_validation_to_first_runtime_read(
    ripe_hq_deploy,
    defaults,
    teller,
    alice,
    failure,
):
    _install_arb_sys_failure(failure)
    ledger = _deploy_ledger(ripe_hq_deploy, defaults, ARB_SYS)

    assert ledger.ACTION_BLOCK_SOURCE() == ARB_SYS
    assert ledger.lastTouch(alice) == 0
    assert ledger.getNumUserVaults(alice) == 0
    with boa.reverts():
        ledger.getArbActionBlock()
    with boa.reverts():
        ledger.checkAndUpdateLastTouch(alice, False, sender=teller.address)
    assert ledger.lastTouch(alice) == 0
    assert ledger.getNumUserVaults(alice) == 0


def test_get_arb_action_block_returns_exact_identity_word(
    ripe_hq_deploy,
    defaults,
    teller,
    alice,
):
    _install_arb_sys(700)
    ledger = _deploy_ledger(ripe_hq_deploy, defaults, ARB_SYS)
    assert ledger.ACTION_BLOCK_SOURCE() == ARB_SYS
    assert ledger.getArbActionBlock() == 700
    ledger.checkAndUpdateLastTouch(alice, False, sender=teller.address)
    assert ledger.lastTouch(alice) == 700


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
def test_get_arb_action_block_rejects_invalid_returndata_without_fallback(
    ripe_hq_deploy,
    defaults,
    teller,
    alice,
    bob,
    failure,
):
    _install_arb_sys(1_000)
    ledger = _deploy_ledger(ripe_hq_deploy, defaults, ARB_SYS)
    ledger.checkAndUpdateLastTouch(alice, False, sender=teller.address)

    native_block = boa.env.evm.patch.block_number
    _install_arb_sys_failure(failure)
    boa.env.time_travel(blocks=1)

    with boa.reverts():
        ledger.getArbActionBlock()
    with boa.reverts():
        ledger.checkAndUpdateLastTouch(bob, False, sender=teller.address)
    assert ledger.lastTouch(alice) == 1_000
    assert ledger.lastTouch(bob) == 0
    assert ledger.getNumUserVaults(bob) == 0
    assert ledger.numBorrowers() == 0
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


# Substrings that may legitimately appear in a line changed by each L3a mutant.
# Stated here independently of _l3a_mutant_source so the two must agree: if the
# generator grows an extra edit, or a mutant picks up an unrelated change, the
# changed line will not match any marker and the test fails.
L3A_EXPECTED_EDIT_MARKERS = {
    "typed_call": (
        "interface MutantArbSys:",
        "def arbBlockNumber() -> uint256: view",
        "staticcall MutantArbSys(ARB_SYS).arbBlockNumber()",
        "response: Bytes[65] = raw_call(",
        "ARB_SYS,",
        'method_id("arbBlockNumber()", output_type=Bytes[4]),',
        "max_outsize=65,",
        "is_static_call=True,",
        "revert_on_failure=True,",
        ")",
        "assert len(response) == 32",
        "return abi_decode(response, uint256)",
    ),
    "truncation": (
        "response: Bytes[65] = raw_call(",
        "response: Bytes[32] = raw_call(",
        "max_outsize=65,",
        "max_outsize=32,",
    ),
    "native_fallback": (
        "success: bool = False",
        'response: Bytes[65] = b""',
        "success, response = raw_call(",
        "response: Bytes[65] = raw_call(",
        "ARB_SYS,",
        'method_id("arbBlockNumber()", output_type=Bytes[4]),',
        "max_outsize=65,",
        "is_static_call=True,",
        "revert_on_failure=False,",
        "revert_on_failure=True,",
        ")",
        "if not success or len(response) != 32:",
        "return block.number",
        "assert len(response) == 32",
        "return abi_decode(response, uint256)",
    ),
    "monotonic": (
        "assert self.lastTouch[_user] != actionBlock",
        "assert self.lastTouch[_user] < actionBlock",
    ),
}


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
        "test_l3a_typed_call_mutant_accepts_every_oversized_runtime_case"
    ),
    "truncation": (
        "test_l3a_truncation_mutant_accepts_oversized_runtime_case"
    ),
    "native_fallback": (
        "test_get_arb_action_block_rejects_invalid_returndata_without_fallback"
    ),
    "monotonic": (
        "test_arb_sys_preserves_equality_only_without_monotonicity_assertion"
    ),
}


@pytest.mark.parametrize(
    "kind",
    ["typed_call", "truncation", "native_fallback", "monotonic"],
)
def test_l3a_mutant_source_is_exactly_the_intended_edit(kind):
    # This used to pin a sha256 of the whole mutant source.
    #
    # An earlier revision of this comment blamed those constants on a
    # macOS-arm64 versus Linux-x86_64 difference. That was wrong. A sha256 of
    # source text cannot depend on the CPU when the bytes are identical; the
    # constants were stale because rh commit 3a5f840 changed Ledger.vy, and the
    # comparison that suggested otherwise was a local run against a CI run of the
    # pull_request *merge* ref, which already contained the newer contract.
    #
    # A whole-file hash is still the wrong assertion: it has to be regenerated on
    # every legitimate Ledger change, which is what let it go stale unnoticed.
    # What it was actually guarding is that the mutant differs from the baseline
    # by the intended edit and nothing else — a mutant carrying a second,
    # unrelated change would still have satisfied a hash refreshed without
    # reading it, and would silently weaken the mutation test that consumes it.
    # That property is asserted directly here, and it is source-drift immune.
    import difflib
    from pathlib import Path

    baseline = Path(LEDGER_PATH).read_text()
    mutant = _l3a_mutant_source(kind)

    assert L3A_KILLING_TESTS[kind] in globals()
    assert mutant != baseline

    # Every changed line, in either direction, must belong to the intended edit.
    # Anything else is an unrelated mutation riding along.
    allowed = L3A_EXPECTED_EDIT_MARKERS[kind]
    changed = [
        line[1:].strip()
        for line in difflib.unified_diff(
            baseline.splitlines(), mutant.splitlines(), n=0, lineterm=""
        )
        if line[:1] in "+-" and not line.startswith(("---", "+++"))
    ]
    assert changed, "no lines changed"

    unexpected = [
        line
        for line in changed
        if line and not any(marker in line for marker in allowed)
    ]
    assert not unexpected, (
        f"{kind} mutant changes lines outside the intended edit: {unexpected}"
    )


@pytest.mark.parametrize(
    "failure",
    ("oversized_33", "oversized_64", "oversized_gt_64"),
)
def test_l3a_typed_call_mutant_accepts_every_oversized_runtime_case(
    ripe_hq_deploy,
    defaults,
    failure,
):
    _install_arb_sys_failure(failure)
    mutant = _deploy_ledger_source(
        _l3a_mutant_source("typed_call"),
        ripe_hq_deploy,
        defaults,
        ARB_SYS,
        f"l3a_typed_call_ledger_{failure}",
    )
    assert mutant.ACTION_BLOCK_SOURCE() == ARB_SYS
    assert mutant.getArbActionBlock() == 0


@pytest.mark.parametrize(
    ("action_block", "should_check", "should_succeed"),
    (
        pytest.param(0, False, True, id="zero-low-risk-writes-zero"),
        pytest.param(0, True, False, id="zero-high-risk-equals-empty-state"),
        pytest.param(
            2**256 - 1,
            True,
            True,
            id="max-word-is-a-valid-identity",
        ),
    ),
)
def test_exact_but_false_words_define_identity_not_chain_truth(
    ripe_hq_deploy,
    defaults,
    teller,
    alice,
    action_block,
    should_check,
    should_succeed,
):
    _install_arb_sys(action_block)
    ledger = _deploy_ledger(
        ripe_hq_deploy,
        defaults,
        ARB_SYS,
        name=f"false_word_ledger_{action_block}_{should_check}",
    )

    if should_succeed:
        ledger.checkAndUpdateLastTouch(
            alice,
            should_check,
            sender=teller.address,
        )
        assert ledger.lastTouch(alice) == action_block
    else:
        with boa.reverts():
            ledger.checkAndUpdateLastTouch(
                alice,
                should_check,
                sender=teller.address,
            )
        assert ledger.lastTouch(alice) == 0


def test_l3a_truncation_mutant_accepts_oversized_runtime_case(
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
    assert mutant.getArbActionBlock() == 0


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


@pytest.fixture(autouse=True)
def isolate_boa_storage_diagnostics():
    """Avoid Boa repr crashes from stale address/type trace metadata."""

    # Keep this below all tests: earlier placement moves cadence-sensitive line
    # numbers pinned by test_block_clock_inventory.py. A shared root fixture
    # would be preferable but tests/conftest.py is outside this candidate's
    # explicit authorization.
    assert isinstance(boa.env.sstore_trace, dict)
    assert isinstance(boa.env.sha3_trace, dict)
    boa.env.sstore_trace.clear()
    boa.env.sha3_trace.clear()
    yield
    boa.env.sstore_trace.clear()
    boa.env.sha3_trace.clear()
