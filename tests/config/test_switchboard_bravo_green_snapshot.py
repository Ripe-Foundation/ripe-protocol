import json
from pathlib import Path

import boa
import pytest

from conf_utils import filter_logs
from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS


ROOT = Path(__file__).resolve().parents[2]
PRICE_SOURCE_DIR = ROOT / "contracts" / "priceSources"
ABI_DIR = ROOT / "scripts" / "abis"
PRICE_DESK_SOURCE_ABIS = (
    "BlueChipYieldPrices.json",
    "ChainlinkPrices.json",
    "CurvePrices.json",
    "PythPrices.json",
    "RedStone.json",
    "StorkPrices.json",
    "UndyVaultPrices.json",
    "UniswapV2Prices.json",
    "wsuperOETHbPrices.json",
    "AeroRipePrices.json",
)

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


def _snapshot_state(curve):
    data = curve.greenRefPoolData()
    return (data.lastSnapshot.update, data.nextIndex, data.lastSnapshot.greenBalance)


def _logs_from_wrapper(switchboard_bravo, event_name):
    # Child logs are on the wrapper computation. Later Curve view calls
    # replace curve.get_logs(), so read them from Bravo immediately.
    return filter_logs(switchboard_bravo, event_name)


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
    return logs[0]


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
def configured_green_ref(
    ripe_hq,
    local_green_ref_curve,
    price_desk,
    governance,
    green_token,
):
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
    ripe_hq,
    configured_green_ref,
    switchboard_bravo,
    governance,
):
    curve = configured_green_ref["curve"]
    source_id = configured_green_ref["source_id"]
    before = _snapshot_state(curve)

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

    after = _snapshot_state(curve)
    assert after[0] > before[0]
    assert after[1] == before[1] + 1


def test_lite_signer_can_call_wrapper_but_not_curve_directly(
    ripe_hq,
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

    before = _snapshot_state(curve)
    assert switchboard_bravo.addGreenRefPoolSnapshot(source_id, sender=lite_signer)
    after = _snapshot_state(curve)
    assert after[0] > before[0]
    assert after[1] == before[1] + 1
    _assert_bravo_event(
        switchboard_bravo,
        lite_signer,
        source_id,
        curve.address,
        True,
    )


def test_unauthorized_eoa_reverts_no_perms(
    ripe_hq,
    configured_green_ref,
    switchboard_bravo,
    alice,
):
    with boa.reverts("no perms"):
        switchboard_bravo.addGreenRefPoolSnapshot(
            configured_green_ref["source_id"],
            sender=alice,
        )


def test_invalid_and_disabled_ids_revert_before_external_write(
    ripe_hq,
    configured_green_ref,
    switchboard_bravo,
    price_desk,
    governance,
):
    curve = configured_green_ref["curve"]
    before = _snapshot_state(curve)
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
        assert counter.snapshotCalls() == 0
        assert _snapshot_state(curve) == before

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
    assert counter.snapshotCalls() == 0
    assert _snapshot_state(curve) == before


def test_successful_specialized_call_updates_ring_and_emits(
    ripe_hq,
    configured_green_ref,
    switchboard_bravo,
    governance,
):
    curve = configured_green_ref["curve"]
    source_id = configured_green_ref["source_id"]
    before = curve.greenRefPoolData()

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

    after = curve.greenRefPoolData()
    assert after.lastSnapshot.update > before.lastSnapshot.update
    assert after.nextIndex == before.nextIndex + 1
    assert after.lastSnapshot.greenBalance == 10_000 * EIGHTEEN_DECIMALS


def test_alpha_generic_snapshot_leaves_green_ring_for_bravo(
    ripe_hq,
    configured_green_ref,
    switchboard_alpha,
    switchboard_bravo,
    governance,
    green_token,
):
    curve = configured_green_ref["curve"]
    source_id = configured_green_ref["source_id"]
    before = _snapshot_state(curve)

    assert not switchboard_alpha.addPriceSnapshot(
        green_token,
        source_id,
        sender=governance.address,
    )
    assert _snapshot_state(curve) == before
    alpha_logs = filter_logs(switchboard_alpha, "PriceSnapshotAdded")
    assert len(alpha_logs) == 1
    assert alpha_logs[0].didUpdate is False

    assert switchboard_bravo.addGreenRefPoolSnapshot(
        source_id,
        sender=governance.address,
    )
    after = _snapshot_state(curve)
    assert after[0] > before[0]
    assert after[1] == before[1] + 1
    _assert_bravo_event(
        switchboard_bravo,
        governance.address,
        source_id,
        curve.address,
        True,
    )


def test_same_block_duplicate_returns_false_without_state_change(
    ripe_hq,
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
    after_first = _snapshot_state(curve)

    did_update = switchboard_bravo.addGreenRefPoolSnapshot(
        source_id,
        sender=governance.address,
    )
    assert did_update is False
    assert _snapshot_state(curve) == after_first
    _assert_bravo_event(
        switchboard_bravo,
        governance.address,
        source_id,
        curve.address,
        False,
    )
    assert _logs_from_wrapper(switchboard_bravo, "GreenRefPoolSnapshotAdded") == []


def test_paused_curve_returns_false_and_logs_no_update(
    ripe_hq,
    configured_green_ref,
    switchboard_bravo,
    switchboard_alpha,
    governance,
):
    curve = configured_green_ref["curve"]
    source_id = configured_green_ref["source_id"]
    before = _snapshot_state(curve)

    curve.pause(True, sender=switchboard_alpha.address)
    did_update = switchboard_bravo.addGreenRefPoolSnapshot(
        source_id,
        sender=governance.address,
    )
    assert did_update is False
    assert _snapshot_state(curve) == before
    _assert_bravo_event(
        switchboard_bravo,
        governance.address,
        source_id,
        curve.address,
        False,
    )
    assert _logs_from_wrapper(switchboard_bravo, "GreenRefPoolSnapshotAdded") == []


def test_reverting_registered_target_reverts_wrapper_without_event(
    ripe_hq,
    price_desk,
    switchboard_bravo,
    governance,
):
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
    assert _logs_from_wrapper(switchboard_bravo, "GreenRefPoolSnapshotAttempted") == []


def test_only_curve_prices_exposes_specialized_green_snapshot(switchboard_bravo):
    source_hits = sorted(
        path.name
        for path in PRICE_SOURCE_DIR.glob("*.vy")
        if "def addGreenRefPoolSnapshot(" in path.read_text()
    )
    assert source_hits == ["CurvePrices.vy"]

    abi_hits = []
    for name in PRICE_DESK_SOURCE_ABIS:
        abi = json.loads((ABI_DIR / name).read_text())
        functions = [
            item
            for item in abi
            if item.get("type") == "function"
            and item.get("name") == "addGreenRefPoolSnapshot"
        ]
        if functions:
            abi_hits.append((name, functions))
    assert [name for name, _ in abi_hits] == ["CurvePrices.json"]
    curve_fn = abi_hits[0][1]
    assert len(curve_fn) == 1
    assert curve_fn[0]["inputs"] == []
    assert [output["type"] for output in curve_fn[0]["outputs"]] == ["bool"]

    bravo_fns = [
        item
        for item in switchboard_bravo.abi
        if item.get("type") == "function"
        and item.get("name") == "addGreenRefPoolSnapshot"
    ]
    assert len(bravo_fns) == 1
    assert [item["type"] for item in bravo_fns[0]["inputs"]] == ["uint256"]
    assert [item["type"] for item in bravo_fns[0]["outputs"]] == ["bool"]
