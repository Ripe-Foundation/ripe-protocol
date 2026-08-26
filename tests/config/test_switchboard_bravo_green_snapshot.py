import json
import re
from pathlib import Path

import boa
import pytest
from eth_hash.auto import keccak

from conf_utils import filter_logs
from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS


ROOT = Path(__file__).resolve().parents[2]
PRICE_SOURCE_DIR = ROOT / "contracts" / "priceSources"
ABI_DIR = ROOT / "scripts" / "abis"
SPECIALIZED_SELECTOR = keccak(b"addGreenRefPoolSnapshot()")[:4]
WRAPPER_SELECTOR = keccak(b"addGreenRefPoolSnapshot(uint256)")[:4]
GET_ADDR_SELECTOR = keccak(b"getAddr(uint256)")[:4]
CAN_PERFORM_LITE_SELECTOR = keccak(b"canPerformLiteAction(address)")[:4]
SPECIALIZED_SELECTOR_HEX = "0x" + SPECIALIZED_SELECTOR.hex()
WRAPPER_SELECTOR_HEX = "0x" + WRAPPER_SELECTOR.hex()

COUNTING_SNAPSHOT_SOURCE = """
# @version 0.4.3

snapshotCalls: public(uint256)

@external
def addGreenRefPoolSnapshot() -> bool:
    self.snapshotCalls += 1
    return True
"""

REVERTING_SNAPSHOT_SOURCE = """
# @version 0.4.3

@external
def addGreenRefPoolSnapshot() -> bool:
    raise "snapshot failure"
"""

# Serves only MissionControl (RipeHq ID 5) and PriceDesk (ID 7). Every other
# getAddr id returns empty(address) on purpose.
MOCK_HQ_SOURCE = """
# @version 0.4.3

governance: public(address)
priceDesk: public(address)
missionControl: public(address)

@deploy
def __init__(_gov: address, _desk: address, _mc: address):
    self.governance = _gov
    self.priceDesk = _desk
    self.missionControl = _mc

@external
def setPriceDesk(_desk: address):
    self.priceDesk = _desk

@external
def setMissionControl(_mc: address):
    self.missionControl = _mc

@view
@external
def minGovChangeTimeLock() -> uint256:
    return 1

@view
@external
def maxGovChangeTimeLock() -> uint256:
    return 100

@view
@external
def getAddr(_regId: uint256) -> address:
    if _regId == 5:
        return self.missionControl
    if _regId == 7:
        return self.priceDesk
    return empty(address)
"""

MOCK_MISSION_CONTROL_SOURCE = """
# @version 0.4.3

allowed: public(HashMap[address, bool])

@external
def setCanPerformLiteAction(_user: address, _canDo: bool):
    self.allowed[_user] = _canDo

@view
@external
def canPerformLiteAction(_user: address) -> bool:
    return self.allowed[_user]
"""


def _canonical_abi_type(item):
    typ = item["type"]
    if typ == "tuple" or typ.startswith("tuple["):
        inner = ",".join(_canonical_abi_type(component) for component in item["components"])
        return f"({inner}){typ[5:]}"
    return typ


def _fn_selector(fn):
    types = ",".join(_canonical_abi_type(item) for item in fn.get("inputs", []))
    return keccak(f"{fn['name']}({types})".encode())[:4]


def _event_named(abi, name):
    return next(
        item
        for item in abi
        if item.get("type") == "event" and item.get("name") == name
    )


# Child-call traces use titanoboa 0.2.7 private internals
# (`contract._computation`, `computation.children`, `child.msg.code_address`,
# `child.msg.data`). They are not public boa API. A boa bump that changes
# those attributes will break the no-write / pointer-rotation proofs first.
def _walk_children(computation):
    for child in computation.children:
        yield child
        yield from _walk_children(child)


def _count_calls(computation, address, selector):
    expected = bytes.fromhex(str(address)[2:])
    return sum(
        child.msg.code_address == expected and bytes(child.msg.data[:4]) == selector
        for child in _walk_children(computation)
    )


def _count_selector_calls(computation, selector):
    return sum(
        bytes(child.msg.data[:4]) == selector
        for child in _walk_children(computation)
    )


def _price_source_vy_files():
    return sorted(PRICE_SOURCE_DIR.glob("*.vy"))


def _price_source_abi_paths():
    paths = []
    for source in _price_source_vy_files():
        path = ABI_DIR / f"{source.stem}.json"
        assert path.exists(), f"missing exported ABI for {source.stem}"
        paths.append(path)
    return paths


def _register_price_source(price_desk, governance, source, description):
    assert price_desk.startAddNewAddressToRegistry(
        source,
        description,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=price_desk.registryChangeTimeLock() + 1)
    source_id = price_desk.confirmNewAddressToRegistry(
        source,
        sender=governance.address,
    )
    assert source_id != 0
    assert source_id != 2
    assert price_desk.getAddr(source_id) == source.address
    return source_id


def _enable_lite_signer(switchboard_alpha, mission_control, governance, user):
    action_id = switchboard_alpha.setCanPerformLiteAction(
        user,
        True,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    assert switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    assert mission_control.canPerformLiteAction(user)
    return user


def _configure_green_ref_pool(curve, pool, governance):
    assert curve.setActionTimeLockAfterSetup(sender=governance.address)
    pool.setBalances(10_000 * EIGHTEEN_DECIMALS, 10_000 * EIGHTEEN_DECIMALS)
    action_id = curve.setGreenRefPoolConfig(
        pool,
        10,
        60_00,
        100,
        10_00,
        100_000 * EIGHTEEN_DECIMALS,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=curve.actionTimeLock())
    assert curve.confirmGreenRefPoolConfig(action_id, sender=governance.address)


def _ring_state(curve):
    data = curve.greenRefPoolData()
    last = data.lastSnapshot
    capacity = curve.greenRefPoolConfig().maxNumSnapshots
    slots = tuple(tuple(curve.snapShots(index)) for index in range(capacity))
    return (
        (last.greenBalance, last.ratio, last.update, last.inDanger),
        data.numBlocksInDanger,
        data.nextIndex,
        slots,
    )


def _logs_from_wrapper(switchboard_bravo, event_name, computation=None):
    # Child logs live on the wrapper computation. Later Curve view calls
    # replace curve.get_logs(), so read them from Bravo immediately.
    # Bravo events use boa's default strict=True. The Alpha regression below
    # still uses filter_logs(..., _strict=False), the repo helper.
    entries = switchboard_bravo.get_logs(strict=True, computation=computation)
    return [entry for entry in entries if type(entry).__name__ == event_name]


def _assert_bravo_event(switchboard_bravo, caller, source_id, source_addr, did_update):
    logs = _logs_from_wrapper(switchboard_bravo, "GreenRefPoolSnapshotAttempted")
    assert len(logs) == 1
    log = logs[0]
    assert log.caller == caller
    assert log.priceSourceId == source_id
    assert log.priceSourceAddr == source_addr
    assert log.didUpdate is did_update


def _assert_curve_snapshot_added(switchboard_bravo, pool, green_balance=None):
    logs = _logs_from_wrapper(switchboard_bravo, "GreenRefPoolSnapshotAdded")
    assert len(logs) == 1
    assert logs[0].pool == pool
    if green_balance is not None:
        assert logs[0].greenBalance == green_balance


def _load_candidate_bravo(mock_hq, temp_gov, name):
    return boa.load(
        "contracts/config/SwitchboardBravo.vy",
        mock_hq,
        temp_gov,
        1,
        100,
        name=name,
    )


def _load_isolated_desk(mock_hq, name):
    return boa.load(
        "contracts/registries/PriceDesk.vy",
        mock_hq,
        ZERO_ADDRESS,
        "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        1,
        100,
        name=name,
    )


# Titanoboa 0.2.7 wraps each test in boa.env.anchor() via its pytest plugin,
# so module-scoped Curve storage mutations (pause, snapshots) do not leak.
# These tests rely on that plugin isolation rather than local unpause/reset.
# Child-call traces additionally depend on the private computation attributes
# documented on `_walk_children`.


@pytest.fixture(scope="module")
def local_green_ref_curve(ripe_hq, green_token, savings_green, ripe_token, governance):
    alt = boa.load(
        "contracts/mock/MockErc20.vy",
        governance.address,
        "ALT",
        "ALT",
        18,
        1,
        name="bravo_green_ref_alt",
    )
    pool = boa.load(
        "contracts/mock/MockCurveRefPool.vy",
        name="bravo_green_ref_pool",
    )
    registry = boa.load(
        "contracts/mock/MockCurveRefPoolRegistry.vy",
        governance.address,
        green_token,
        savings_green,
        ripe_token,
        name="bravo_green_ref_registry",
    )
    registry.setPool(pool, alt, green_token)
    curve = boa.load(
        "contracts/priceSources/CurvePrices.vy",
        ripe_hq,
        ZERO_ADDRESS,
        registry,
        green_token,
        savings_green,
        1,
        100,
        name="bravo_green_ref_curve_prices",
    )
    return {
        "alt": alt,
        "pool": pool,
        "registry": registry,
        "curve": curve,
    }


@pytest.fixture
def configured_green_ref(local_green_ref_curve, price_desk, governance, green_token):
    curve = local_green_ref_curve["curve"]
    pool = local_green_ref_curve["pool"]
    _configure_green_ref_pool(curve, pool, governance)
    source_id = _register_price_source(
        price_desk,
        governance,
        curve,
        "Bravo GREEN ref CurvePrices",
    )
    return {
        **local_green_ref_curve,
        "source_id": source_id,
        "green": green_token,
    }


def test_governance_can_call_specialized_wrapper(
    configured_green_ref,
    switchboard_bravo,
    governance,
):
    curve = configured_green_ref["curve"]
    source_id = configured_green_ref["source_id"]
    before = _ring_state(curve)

    assert switchboard_bravo.addGreenRefPoolSnapshot(
        source_id,
        sender=governance.address,
    )
    _assert_curve_snapshot_added(
        switchboard_bravo,
        configured_green_ref["pool"].address,
    )
    _assert_bravo_event(
        switchboard_bravo,
        governance.address,
        source_id,
        curve.address,
        True,
    )

    after = _ring_state(curve)
    assert after[0][2] > before[0][2]
    assert after[2] == before[2] + 1
    assert after != before


def test_lite_signer_can_call_wrapper_but_not_curve_directly(
    configured_green_ref,
    switchboard_bravo,
    switchboard_alpha,
    mission_control,
    governance,
    bob,
):
    curve = configured_green_ref["curve"]
    source_id = configured_green_ref["source_id"]
    lite_signer = _enable_lite_signer(
        switchboard_alpha,
        mission_control,
        governance,
        bob,
    )

    with boa.reverts("no perms"):
        curve.addGreenRefPoolSnapshot(sender=lite_signer)

    before = _ring_state(curve)
    assert switchboard_bravo.addGreenRefPoolSnapshot(source_id, sender=lite_signer)
    after = _ring_state(curve)
    assert after[0][2] > before[0][2]
    assert after[2] == before[2] + 1
    _assert_bravo_event(
        switchboard_bravo,
        lite_signer,
        source_id,
        curve.address,
        True,
    )


def test_lite_signer_revocation_is_honored_immediately(
    configured_green_ref,
    switchboard_bravo,
    switchboard_alpha,
    mission_control,
    governance,
    bob,
):
    source_id = configured_green_ref["source_id"]
    _enable_lite_signer(switchboard_alpha, mission_control, governance, bob)
    assert switchboard_bravo.addGreenRefPoolSnapshot(source_id, sender=bob)

    switchboard_alpha.setCanPerformLiteAction(bob, False, sender=governance.address)
    assert not mission_control.canPerformLiteAction(bob)
    with boa.reverts("no perms"):
        switchboard_bravo.addGreenRefPoolSnapshot(source_id, sender=bob)


def test_unauthorized_eoa_reverts_no_perms(configured_green_ref, switchboard_bravo, alice):
    with boa.reverts("no perms"):
        switchboard_bravo.addGreenRefPoolSnapshot(
            configured_green_ref["source_id"],
            sender=alice,
        )


def test_invalid_and_disabled_ids_revert_before_external_write(
    configured_green_ref,
    switchboard_bravo,
    price_desk,
    governance,
):
    curve = configured_green_ref["curve"]
    before = _ring_state(curve)
    counter = boa.loads(COUNTING_SNAPSHOT_SOURCE, name="bravo_green_ref_counter")
    counter_id = _register_price_source(
        price_desk,
        governance,
        counter,
        "Counting GREEN snapshot target",
    )

    for invalid_id in (0, 999, 2_000):
        with boa.reverts("invalid price source id"):
            switchboard_bravo.addGreenRefPoolSnapshot(
                invalid_id,
                sender=governance.address,
            )
        failed = switchboard_bravo._computation
        assert _count_selector_calls(failed, SPECIALIZED_SELECTOR) == 0
        assert _count_calls(failed, counter.address, SPECIALIZED_SELECTOR) == 0
        assert _count_calls(failed, curve.address, SPECIALIZED_SELECTOR) == 0
        assert _count_calls(failed, price_desk.address, GET_ADDR_SELECTOR) == 1
        assert counter.snapshotCalls() == 0
        assert _ring_state(curve) == before

    assert price_desk.startAddressDisableInRegistry(
        counter_id,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=price_desk.registryChangeTimeLock() + 1)
    assert price_desk.confirmAddressDisableInRegistry(
        counter_id,
        sender=governance.address,
    )
    assert price_desk.getAddr(counter_id) == ZERO_ADDRESS

    with boa.reverts("invalid price source id"):
        switchboard_bravo.addGreenRefPoolSnapshot(
            counter_id,
            sender=governance.address,
        )
    failed = switchboard_bravo._computation
    assert _count_selector_calls(failed, SPECIALIZED_SELECTOR) == 0
    assert _count_calls(failed, counter.address, SPECIALIZED_SELECTOR) == 0
    assert _count_calls(failed, price_desk.address, GET_ADDR_SELECTOR) == 1
    assert counter.snapshotCalls() == 0
    assert _ring_state(curve) == before


def test_successful_specialized_call_updates_ring_and_emits(
    configured_green_ref,
    switchboard_bravo,
    governance,
):
    curve = configured_green_ref["curve"]
    source_id = configured_green_ref["source_id"]
    before = _ring_state(curve)

    did_update = switchboard_bravo.addGreenRefPoolSnapshot(
        source_id,
        sender=governance.address,
    )
    assert did_update is True
    _assert_curve_snapshot_added(
        switchboard_bravo,
        configured_green_ref["pool"].address,
        10_000 * EIGHTEEN_DECIMALS,
    )
    _assert_bravo_event(
        switchboard_bravo,
        governance.address,
        source_id,
        curve.address,
        True,
    )

    after = _ring_state(curve)
    assert after[0][0] == 10_000 * EIGHTEEN_DECIMALS
    assert after[0][2] > before[0][2]
    assert after[2] == before[2] + 1
    assert after[3][before[2]][2] == after[0][2]
    assert after != before


def test_alpha_generic_snapshot_leaves_green_ring_for_bravo(
    configured_green_ref,
    switchboard_alpha,
    switchboard_bravo,
    governance,
    green_token,
):
    curve = configured_green_ref["curve"]
    source_id = configured_green_ref["source_id"]
    before = _ring_state(curve)

    assert not switchboard_alpha.addPriceSnapshot(
        green_token,
        source_id,
        sender=governance.address,
    )
    assert _ring_state(curve) == before
    alpha_logs = filter_logs(switchboard_alpha, "PriceSnapshotAdded")
    assert len(alpha_logs) == 1
    assert alpha_logs[0].didUpdate is False

    assert switchboard_bravo.addGreenRefPoolSnapshot(
        source_id,
        sender=governance.address,
    )
    after = _ring_state(curve)
    assert after[0][2] > before[0][2]
    assert after[2] == before[2] + 1
    assert after != before
    _assert_bravo_event(
        switchboard_bravo,
        governance.address,
        source_id,
        curve.address,
        True,
    )


def test_same_block_duplicate_returns_false_without_state_change(
    configured_green_ref,
    switchboard_bravo,
    governance,
):
    curve = configured_green_ref["curve"]
    source_id = configured_green_ref["source_id"]

    assert switchboard_bravo.addGreenRefPoolSnapshot(
        source_id,
        sender=governance.address,
    )
    after_first = _ring_state(curve)

    did_update = switchboard_bravo.addGreenRefPoolSnapshot(
        source_id,
        sender=governance.address,
    )
    assert did_update is False
    assert _ring_state(curve) == after_first
    _assert_bravo_event(
        switchboard_bravo,
        governance.address,
        source_id,
        curve.address,
        False,
    )
    assert _logs_from_wrapper(switchboard_bravo, "GreenRefPoolSnapshotAdded") == []


def test_paused_curve_returns_false_and_logs_no_update(
    configured_green_ref,
    switchboard_bravo,
    switchboard_alpha,
    governance,
):
    curve = configured_green_ref["curve"]
    source_id = configured_green_ref["source_id"]
    before = _ring_state(curve)

    curve.pause(True, sender=switchboard_alpha.address)
    did_update = switchboard_bravo.addGreenRefPoolSnapshot(
        source_id,
        sender=governance.address,
    )
    assert did_update is False
    assert _ring_state(curve) == before
    _assert_bravo_event(
        switchboard_bravo,
        governance.address,
        source_id,
        curve.address,
        False,
    )
    assert _logs_from_wrapper(switchboard_bravo, "GreenRefPoolSnapshotAdded") == []


def test_reverting_registered_target_reverts_wrapper_without_event(
    configured_green_ref,
    price_desk,
    switchboard_bravo,
    governance,
):
    curve = configured_green_ref["curve"]
    good_id = configured_green_ref["source_id"]
    assert switchboard_bravo.addGreenRefPoolSnapshot(
        good_id,
        sender=governance.address,
    )
    successful_logs = _logs_from_wrapper(
        switchboard_bravo,
        "GreenRefPoolSnapshotAttempted",
    )
    assert len(successful_logs) == 1
    after_success = _ring_state(curve)

    target = boa.loads(
        REVERTING_SNAPSHOT_SOURCE,
        name="bravo_green_ref_reverting_target",
    )
    source_id = _register_price_source(
        price_desk,
        governance,
        target,
        "Reverting GREEN snapshot target",
    )

    with boa.reverts("snapshot failure"):
        switchboard_bravo.addGreenRefPoolSnapshot(
            source_id,
            sender=governance.address,
        )
    failed = switchboard_bravo._computation
    assert _count_calls(failed, target.address, SPECIALIZED_SELECTOR) == 1
    assert _logs_from_wrapper(
        switchboard_bravo,
        "GreenRefPoolSnapshotAttempted",
        computation=failed,
    ) == []
    assert _ring_state(curve) == after_success


def test_missing_price_desk_reverts_without_specialized_call(alice, bob):
    mock_hq = boa.loads(
        MOCK_HQ_SOURCE,
        bob,
        ZERO_ADDRESS,
        ZERO_ADDRESS,
        name="bravo_green_ref_missing_desk_hq",
    )
    candidate = _load_candidate_bravo(mock_hq, alice, "candidate_bravo_missing_desk")
    counter = boa.loads(COUNTING_SNAPSHOT_SOURCE, name="bravo_green_ref_unused_counter")

    with boa.reverts("missing price desk"):
        candidate.addGreenRefPoolSnapshot(2, sender=alice)
    failed = candidate._computation
    assert _count_selector_calls(failed, SPECIALIZED_SELECTOR) == 0
    assert _count_calls(failed, counter.address, SPECIALIZED_SELECTOR) == 0
    assert _count_calls(failed, mock_hq.address, GET_ADDR_SELECTOR) == 1


def test_wrapper_reads_current_price_desk_and_mission_control(alice, bob, sally):
    mock_hq = boa.loads(
        MOCK_HQ_SOURCE,
        bob,
        ZERO_ADDRESS,
        ZERO_ADDRESS,
        name="bravo_green_ref_pointer_hq",
    )
    first_mc = boa.loads(
        MOCK_MISSION_CONTROL_SOURCE,
        name="bravo_green_ref_pointer_mc_a",
    )
    second_mc = boa.loads(
        MOCK_MISSION_CONTROL_SOURCE,
        name="bravo_green_ref_pointer_mc_b",
    )
    mock_hq.setMissionControl(first_mc)
    candidate = _load_candidate_bravo(
        mock_hq,
        alice,
        "candidate_bravo_pointer",
    )

    first_desk = _load_isolated_desk(mock_hq, "candidate_bravo_price_desk_a")
    first_counter = boa.loads(COUNTING_SNAPSHOT_SOURCE, name="bravo_green_ref_desk_a")
    assert first_desk.startAddNewAddressToRegistry(
        first_counter,
        "Desk A counter",
        sender=bob,
    )
    # Isolated desks start with registryChangeTimeLock == 0, so same-block
    # confirm currently works. Travel anyway so this does not depend on that
    # initial lock or on boa incrementing the block per transaction.
    boa.env.time_travel(blocks=first_desk.registryChangeTimeLock() + 1)
    first_id = first_desk.confirmNewAddressToRegistry(first_counter, sender=bob)
    assert first_id == 1

    second_desk = _load_isolated_desk(mock_hq, "candidate_bravo_price_desk_b")
    second_counter = boa.loads(COUNTING_SNAPSHOT_SOURCE, name="bravo_green_ref_desk_b")
    assert second_desk.startAddNewAddressToRegistry(
        second_counter,
        "Desk B counter",
        sender=bob,
    )
    boa.env.time_travel(blocks=second_desk.registryChangeTimeLock() + 1)
    second_id = second_desk.confirmNewAddressToRegistry(second_counter, sender=bob)
    assert second_id == 1

    mock_hq.setPriceDesk(first_desk)
    assert candidate.addGreenRefPoolSnapshot(first_id, sender=alice)
    assert first_counter.snapshotCalls() == 1
    assert second_counter.snapshotCalls() == 0

    mock_hq.setPriceDesk(second_desk)
    first_mc.setCanPerformLiteAction(sally, True)
    second_mc.setCanPerformLiteAction(sally, False)
    assert candidate.addGreenRefPoolSnapshot(second_id, sender=sally)
    assert first_counter.snapshotCalls() == 1
    assert second_counter.snapshotCalls() == 1
    assert _count_calls(candidate._computation, first_mc.address, CAN_PERFORM_LITE_SELECTOR) == 1
    assert _count_calls(candidate._computation, second_mc.address, CAN_PERFORM_LITE_SELECTOR) == 0
    assert _count_calls(candidate._computation, second_desk.address, GET_ADDR_SELECTOR) == 1
    assert _count_calls(candidate._computation, first_desk.address, GET_ADDR_SELECTOR) == 0

    mock_hq.setMissionControl(second_mc)
    with boa.reverts("no perms"):
        candidate.addGreenRefPoolSnapshot(second_id, sender=sally)
    failed = candidate._computation
    assert _count_calls(failed, second_mc.address, CAN_PERFORM_LITE_SELECTOR) == 1
    assert _count_calls(failed, first_mc.address, CAN_PERFORM_LITE_SELECTOR) == 0

    second_mc.setCanPerformLiteAction(sally, True)
    assert candidate.addGreenRefPoolSnapshot(second_id, sender=sally)
    assert first_counter.snapshotCalls() == 1
    assert second_counter.snapshotCalls() == 2
    assert _count_calls(candidate._computation, second_mc.address, CAN_PERFORM_LITE_SELECTOR) == 1
    assert _count_calls(candidate._computation, first_mc.address, CAN_PERFORM_LITE_SELECTOR) == 0
    assert _count_calls(candidate._computation, second_desk.address, GET_ADDR_SELECTOR) == 1
    assert _count_calls(candidate._computation, first_desk.address, GET_ADDR_SELECTOR) == 0


def test_only_curve_prices_exposes_specialized_green_snapshot(switchboard_bravo):
    assert SPECIALIZED_SELECTOR_HEX == "0x7cdb0a4d"
    assert WRAPPER_SELECTOR_HEX == "0xd9948a29"

    source_hits = sorted(
        path.name
        for path in _price_source_vy_files()
        if re.search(r"def\s+addGreenRefPoolSnapshot\s*\(", path.read_text())
    )
    assert source_hits == ["CurvePrices.vy"]

    default_hits = sorted(
        path.name
        for path in _price_source_vy_files()
        if re.search(r"def\s+__default__\s*\(", path.read_text())
    )
    assert default_hits == []

    specialized_hits = []
    wrapper_hits = []
    for path in _price_source_abi_paths():
        abi = json.loads(path.read_text())
        for fn in abi:
            if fn.get("type") != "function":
                continue
            selector = _fn_selector(fn)
            if selector == SPECIALIZED_SELECTOR:
                specialized_hits.append((path.name, fn))
            if selector == WRAPPER_SELECTOR:
                wrapper_hits.append((path.name, fn))

    assert [name for name, _ in specialized_hits] == ["CurvePrices.json"]
    assert specialized_hits[0][1]["inputs"] == []
    assert [output["type"] for output in specialized_hits[0][1]["outputs"]] == ["bool"]
    assert wrapper_hits == []

    bravo_fns = [
        item
        for item in switchboard_bravo.abi
        if item.get("type") == "function"
    ]
    bravo_selectors = {_fn_selector(fn): fn for fn in bravo_fns}
    assert len(bravo_selectors) == len(bravo_fns)
    assert SPECIALIZED_SELECTOR not in bravo_selectors
    wrapper = bravo_selectors[WRAPPER_SELECTOR]
    assert wrapper["name"] == "addGreenRefPoolSnapshot"
    assert [item["type"] for item in wrapper["inputs"]] == ["uint256"]
    assert [item["type"] for item in wrapper["outputs"]] == ["bool"]

    exported = json.loads((ABI_DIR / "SwitchboardBravo.json").read_text())
    exported_wrapper = next(
        item
        for item in exported
        if item.get("type") == "function"
        and item.get("name") == "addGreenRefPoolSnapshot"
    )
    assert _fn_selector(exported_wrapper) == WRAPPER_SELECTOR
    event = _event_named(exported, "GreenRefPoolSnapshotAttempted")
    live_event = _event_named(switchboard_bravo.abi, "GreenRefPoolSnapshotAttempted")
    for candidate in (event, live_event):
        assert [
            (item["name"], item["type"], item["indexed"])
            for item in candidate["inputs"]
        ] == [
            ("caller", "address", True),
            ("priceSourceId", "uint256", True),
            ("priceSourceAddr", "address", True),
            ("didUpdate", "bool", False),
        ]
