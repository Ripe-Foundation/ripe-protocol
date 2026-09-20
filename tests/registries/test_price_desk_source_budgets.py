"""Source availability, permission checks and cold funding boundary cases."""
import boa
import pytest
from eth_abi import encode

from conf_utils import filter_logs
from registries.price_desk_gas_helpers import cold_trial, calls_to, CallGasMeter
from registries.price_desk_helpers import (
    ETH, ZERO_ADDRESS, _gas_source, _isolated_price_desk, _raw_source, _set_priorities,
)

DEFAULTS = (250_000, 150_000, 75_000)
MAXIMUM = 6_000_000
FUNDING_ERROR = b"insufficient source gas"


def static_price(desk, asset, strict, gas):
    return boa.env.execute_code(
        to_address=desk.address, data=desk.getPrice.prepare_calldata(asset, strict),
        gas=gas, is_modifying=False,
    )


def test_budget_permissions_paused_and_relinquished(
    ripe_hq, deploy3r, governance, switchboard_alpha, teller, bob,
):
    source = _raw_source()
    desk = _isolated_price_desk(ripe_hq, deploy3r, [])
    assert desk.getSourceGasBudgets(source) == DEFAULTS
    # Pre-registration governance config is allowed; membership alone is not.
    for caller in (switchboard_alpha.address, teller.address, bob):
        with boa.reverts("no perms"):
            desk.setSourceGasBudgets(source, 0, 0, 0, sender=caller)
    assert desk.setSourceGasBudgets(source, 300_000, 200_000, 90_000, sender=deploy3r)
    desk.pause(True, sender=switchboard_alpha.address)
    assert desk.setSourceGasBudgets(source, 400_000, 0, 0, sender=governance.address)
    desk.relinquishGov(sender=deploy3r)
    with boa.reverts("no perms"):
        desk.setSourceGasBudgets(source, 0, 0, 0, sender=deploy3r)
    assert desk.setSourceGasBudgets(source, 0, 0, 0, sender=governance.address)
    assert desk.getSourceGasBudgets(source) == DEFAULTS


@pytest.mark.parametrize("field", range(3), ids=("quote", "snapshot", "feed"))
def test_budget_floors_maximum_and_independent_reset(ripe_hq, deploy3r, field):
    source = _raw_source()
    desk = _isolated_price_desk(ripe_hq, deploy3r, [])
    for invalid in (1, DEFAULTS[field] - 1, MAXIMUM + 1, 2**256 - 1):
        budgets = [0, 0, 0]
        budgets[field] = invalid
        with boa.reverts():
            desk.setSourceGasBudgets(source, *budgets, sender=deploy3r)
        assert desk.getSourceGasBudgets(source) == DEFAULTS
    for valid in (DEFAULTS[field], MAXIMUM):
        budgets = [0, 0, 0]
        budgets[field] = valid
        assert desk.setSourceGasBudgets(source, *budgets, sender=deploy3r)
        expected = list(DEFAULTS)
        expected[field] = valid
        assert tuple(desk.getSourceGasBudgets(source)) == tuple(expected)
    desk.setSourceGasBudgets(source, *([MAXIMUM] * 3), sender=deploy3r)
    budgets = [MAXIMUM] * 3
    budgets[field] = 0
    desk.setSourceGasBudgets(source, *budgets, sender=deploy3r)
    expected = list(budgets)
    expected[field] = DEFAULTS[field]
    assert tuple(desk.getSourceGasBudgets(source)) == tuple(expected)


def test_budget_events_report_raw_overrides_and_address_lifecycle(ripe_hq, deploy3r):
    original, replacement = _raw_source(), _raw_source()
    desk = _isolated_price_desk(ripe_hq, deploy3r, [original])
    first = (300_000, 200_000, 90_000)
    desk.setSourceGasBudgets(original, *first, sender=deploy3r)
    event = filter_logs(desk, "SourceGasBudgetsUpdated")[0]
    assert event.source == original.address
    assert (event.oldQuoteGas, event.oldSnapshotGas, event.oldHasFeedGas) == (0, 0, 0)
    assert (event.newQuoteGas, event.newSnapshotGas, event.newHasFeedGas) == first
    entries = desk._computation.get_log_entries()
    assert len(entries[0][1]) == 2  # event signature plus indexed source
    assert entries[0][1][1] == int(str(original.address), 16)
    desk.startAddressDisableInRegistry(1, sender=deploy3r)
    desk.confirmAddressDisableInRegistry(1, sender=deploy3r)
    assert desk.getSourceGasBudgets(original) == first
    for source in (original, replacement, original):
        desk.startAddressUpdateToRegistry(1, source, sender=deploy3r)
        assert desk.confirmAddressUpdateToRegistry(1, sender=deploy3r)
        assert desk.getSourceGasBudgets(source) == (first if source == original else DEFAULTS)
    desk.setSourceGasBudgets(original, 0, 0, 0, sender=deploy3r)
    event = filter_logs(desk, "SourceGasBudgetsUpdated")[0]
    assert (event.oldQuoteGas, event.oldSnapshotGas, event.oldHasFeedGas) == first
    assert (event.newQuoteGas, event.newSnapshotGas, event.newHasFeedGas) == (0, 0, 0)
    assert desk.getSourceGasBudgets(original) == DEFAULTS


@pytest.mark.parametrize("invalid", (ZERO_ADDRESS, ETH))
def test_budget_source_must_be_deployed(ripe_hq, deploy3r, invalid):
    desk = _isolated_price_desk(ripe_hq, deploy3r, [])
    with boa.reverts("invalid source"):
        desk.setSourceGasBudgets(invalid, 0, 0, 0, sender=deploy3r)


@pytest.mark.parametrize("budgets", (
    (250_000, 150_000, 0, MAXIMUM), (250_000, 150_000, 75_000, 0),
    (250_000, 150_000, 75_000, 249_999), (1, 150_000, 1, 149_999),
    (1, 1, 75_000, 74_999), (1, 1, 1, 2**256 - 1),
))
def test_constructor_rejects_invalid_budget_bounds(ripe_hq, deploy3r, budgets):
    with boa.reverts():
        boa.load("contracts/registries/PriceDesk.vy", ripe_hq, deploy3r, ETH, 1, 2, *budgets)


def test_constructor_accepts_overflow_safe_upper_boundary(ripe_hq, deploy3r):
    maximum = ((2**256 - 1 - 5_000) // 64) * 63
    desk = boa.load("contracts/registries/PriceDesk.vy", ripe_hq, deploy3r, ETH, 1, 2,
                    1, 1, 1, maximum)
    source = _raw_source()
    assert desk.setSourceGasBudgets(source, maximum, maximum, maximum, sender=deploy3r)
    # Exercise the actual compiled proof arithmetic at the upper boundary.
    desk.eval(f"self._requireSourceCallGas(max_value(uint256), {maximum})")
    with boa.reverts():
        boa.load("contracts/registries/PriceDesk.vy", ripe_hq, deploy3r, ETH, 1, 2,
                 1, 1, 1, maximum + 1)


@pytest.mark.parametrize("strict", (False, True))
@pytest.mark.parametrize("price,feed,mode", (
    (10**18, True, 0), (0, False, 0), (0, True, 0), (10**18, False, 0),
    *[(0, False, mode) for mode in range(1, 7)],
))
def test_static_quote_result_controls_funding_proof(
    ripe_hq, deploy3r, mission_control, switchboard_alpha, strict, price, feed, mode,
):
    source = _raw_source(price, feed, price_mode=mode)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [source])
    _set_priorities(mission_control, switchboard_alpha, [1])
    accepted = mode == 0 and ((price > 0 and feed) or (price == 0 and not feed))
    with cold_trial(desk, source):
        result = static_price(desk, ETH, strict, 100_000)
        assert result.msg.is_static
        source_calls = calls_to(result, source)
        assert len(source_calls) == 1 and source_calls[0].msg.gas < DEFAULTS[0]
        if accepted:
            assert not result.is_error
            assert int.from_bytes(result.output, "big") == price
        else:
            assert result.is_error and FUNDING_ERROR in result.output
    with cold_trial(desk, source):
        result = static_price(desk, ETH, strict, 500_000)
        assert calls_to(result, source)[0].msg.gas == DEFAULTS[0]
        assert result.is_error == (strict and not accepted)
        if result.is_error:
            assert b"has price config, no price" in result.output
        else:
            assert int.from_bytes(result.output, "big") == (price if accepted else 0)


def test_source_revert_bytes_never_classify_underfunding(
    ripe_hq, deploy3r, mission_control, switchboard_alpha,
):
    source = boa.loads('''# @version 0.4.3
@view
@external
def getPriceAndHasFeed(a: address, t: uint256, d: address) -> (uint256, bool):
    raise "insufficient source gas"
''')
    fallback = _raw_source(42, True)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [source, fallback])
    _set_priorities(mission_control, switchboard_alpha, [1, 2])
    with cold_trial(desk, source):
        assert desk.getPrice(ETH, True, gas=500_000) == 42
    with cold_trial(desk, source):
        with boa.reverts("insufficient source gas"):
            desk.getPrice(ETH, False, gas=100_000)


@pytest.mark.parametrize("operation", ("feed", "admission"))
@pytest.mark.parametrize("override", (False, True))
def test_feed_and_admission_require_eager_effective_budget(
    ripe_hq, deploy3r, operation, override,
):
    source = _raw_source(10**18, True)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [source])
    if override:
        desk.setSourceGasBudgets(source, 500_000, 0, 200_000, sender=deploy3r)
    with cold_trial(desk, source):
        with boa.reverts("insufficient source gas"):
            if operation == "feed":
                desk.hasPriceFeed(ETH, gas=50_000 if not override else 150_000)
            else:
                desk.qualifyCallerPriceSource(ETH, sender=source.address, gas=100_000 if not override else 400_000)
        assert not calls_to(desk._computation, source)
    with cold_trial(desk, source):
        if operation == "feed":
            assert desk.hasPriceFeed(ETH, gas=1_000_000)
        else:
            assert desk.qualifyCallerPriceSource(ETH, sender=source.address, gas=1_000_000) == (10**18, 1)
        assert calls_to(desk._computation, source)[0].msg.gas == (
            (200_000 if override else 75_000) if operation == "feed" else (500_000 if override else 250_000))


NESTED_SOURCE = '''# @version 0.4.3
vault: address
underlying: address
catchMode: uint256
repeats: uint256
@deploy
def __init__(vault: address, underlying: address, catchMode: uint256, repeats: uint256):
    self.vault = vault
    self.underlying = underlying
    self.catchMode = catchMode
    self.repeats = repeats
@view
@external
def getPriceAndHasFeed(asset: address, stale: uint256, desk: address) -> (uint256, bool):
    if asset != self.vault:
        return 0, False
    price: uint256 = 0
    for i: uint256 in range(self.repeats, bound=2):
        success: bool = False
        response: Bytes[256] = b""
        success, response = raw_call(desk, abi_encode(self.underlying, False, method_id=method_id("getPrice(address,bool)")), max_outsize=256, is_static_call=True, revert_on_failure=False)
        if not success:
            if self.catchMode == 1:
                return 0, True
            if self.catchMode == 2:
                return 7, True
            if self.catchMode == 3:
                return 0, False
            raw_revert(response)
        price = abi_decode(response, uint256)
    return price * 2, True
'''

ASSET_SOURCE = '''# @version 0.4.3
asset: address
price: uint256
@deploy
def __init__(asset: address, price: uint256):
    self.asset = asset
    self.price = price
@view
@external
def getPriceAndHasFeed(asset: address, stale: uint256, desk: address) -> (uint256, bool):
    if asset == self.asset:
        return self.price, True
    return 0, False
'''


def nested_desk(ripe_hq, deploy3r, mission_control, switchboard_alpha, catch=0, repeats=2):
    underlying = boa.env.generate_address()
    chainlink = _gas_source(price_iterations=1_000_000, exhaust_price=True)
    undy = boa.loads(NESTED_SOURCE, ETH, underlying, catch, repeats)
    healthy = boa.loads(ASSET_SOURCE, underlying, 100)
    sources = [chainlink, healthy, *[_raw_source() for _ in range(5)], undy, _raw_source(42, True)]
    desk = _isolated_price_desk(ripe_hq, deploy3r, sources)
    _set_priorities(mission_control, switchboard_alpha, [1, 8, 2, 9, 4, 5])
    return desk, sources, undy, chainlink


def test_nested_repeated_source_identity_and_undy_no_feed_revisit(
    ripe_hq, deploy3r, mission_control, switchboard_alpha,
):
    desk, sources, undy, chainlink = nested_desk(ripe_hq, deploy3r, mission_control, switchboard_alpha)
    desk.setSourceGasBudgets(undy, 2_000_000, 0, 0, sender=deploy3r)
    with cold_trial(desk, *sources):
        result = static_price(desk, ETH, True, 3_000_000)
        assert not result.is_error and int.from_bytes(result.output, "big") == 200
        exhausted = calls_to(result, chainlink)
        assert len(exhausted) == 3
        assert all(call.is_error and call.msg.gas == 250_000 for call in exhausted)
        revisits = calls_to(result, undy)
        assert len(revisits) == 3 and all(not call.is_error for call in revisits)
        assert all(call.msg.gas < 2_000_000 for call in revisits[1:])
        assert all(call.msg.is_static for source in sources for call in calls_to(result, source))
        direct_order = [sources.index(next(source for source in sources if bytes.fromhex(str(source.address)[2:]) == child.msg.code_address)) + 1
                        for child in result.children if any(bytes.fromhex(str(source.address)[2:]) == child.msg.code_address for source in sources)]
        assert direct_order == [1, 8]


@pytest.mark.parametrize("catch", (0, 1), ids=("propagated", "caught_zero_with_feed"))
def test_fully_funded_parent_isolates_inner_underfunding(
    ripe_hq, deploy3r, mission_control, switchboard_alpha, catch,
):
    desk, sources, undy, chainlink = nested_desk(ripe_hq, deploy3r, mission_control, switchboard_alpha, catch)
    with cold_trial(desk, *sources):
        result = static_price(desk, ETH, True, 1_000_000)
        assert not result.is_error and int.from_bytes(result.output, "big") == 42
        parent = calls_to(result, undy)[0]
        assert parent.msg.gas == 250_000
        assert any(FUNDING_ERROR in call.output for call in calls_to(parent, desk))
    with cold_trial(desk, *sources):
        result = static_price(desk, ETH, False, 480_000)
        assert result.is_error


@pytest.mark.parametrize("catch,expected", ((2, 7), (3, 42)))
def test_caught_inner_failure_with_canonical_reply_is_an_explicit_limit(
    ripe_hq, deploy3r, mission_control, switchboard_alpha, catch, expected,
):
    # A source that conceals an inner error as a canonical reply cannot be
    # distinguished at this interface. Preserve this focused reproduction.
    desk, sources, undy, chainlink = nested_desk(ripe_hq, deploy3r, mission_control, switchboard_alpha, catch)
    with cold_trial(desk, *sources):
        result = static_price(desk, ETH, False, 1_000_000)
        assert not result.is_error and int.from_bytes(result.output, "big") == expected
        assert any(FUNDING_ERROR in call.output for call in calls_to(calls_to(result, undy)[0], desk))


@pytest.mark.parametrize("low_price,low_feed,expected", ((7, True, 7), (0, False, 42)))
def test_gas_dependent_canonical_reply_cannot_be_authenticated(
    ripe_hq, deploy3r, mission_control, switchboard_alpha, low_price, low_feed, expected,
):
    source = boa.loads(f'''# @version 0.4.3
@view
@external
def getPriceAndHasFeed(a: address, t: uint256, d: address) -> (uint256, bool):
    if msg.gas < 150000:
        return {low_price}, {low_feed}
    return 100, True
''')
    desk = _isolated_price_desk(ripe_hq, deploy3r, [source, _raw_source(42, True)])
    _set_priorities(mission_control, switchboard_alpha, [1, 2])
    for gas, price in ((100_000, expected), (500_000, 100)):
        with cold_trial(desk, source):
            assert desk.getPrice(ETH, True, gas=gas) == price


SNAPSHOT_SOURCE = '''# @version 0.4.3
count: public(uint256)
last: public(uint256)
due: public(bool)
failure: uint256
event SnapshotWritten:
    count: uint256
@external
def configure(due: bool, failure: uint256):
    self.due = due
    self.failure = failure
@view
@external
def hasPriceFeed(asset: address) -> bool:
    return True
@external
def addPriceSnapshot(asset: address) -> bool:
    return self._snapshot()
@external
def addGreenRefPoolSnapshot() -> bool:
    return self._snapshot()
@internal
def _snapshot() -> bool:
    if not self.due or self.last == block.number:
        return False
    self.count += 1
    self.last = block.number
    if self.failure == 1:
        raise "source unavailable"
    if self.failure == 2:
        x: bytes32 = empty(bytes32)
        for i: uint256 in range(1000000):
            x = keccak256(x)
        assert x == empty(bytes32)
    log SnapshotWritten(count=self.count)
    return True
'''

SNAPSHOT_CALLER = '''# @version 0.4.3
interface Desk:
    def addPriceSnapshot(asset: address) -> bool: nonpayable
    def addGreenRefPoolSnapshot(id: uint256) -> bool: nonpayable
interface Source:
    def addPriceSnapshot(asset: address) -> bool: nonpayable
writes: public(uint256)
@external
def run(desk: address, source: address, relay: bool) -> bool:
    self.writes += 1
    extcall Source(source).addPriceSnapshot(self)
    if relay:
        return extcall Desk(desk).addGreenRefPoolSnapshot(1)
    return extcall Desk(desk).addPriceSnapshot(self)
'''


@pytest.fixture(params=(False, True), ids=("asset_snapshot", "green_ref_snapshot"))
def snapshot_case(request, ripe_hq, governance, deploy3r):
    prior, source = boa.loads(SNAPSHOT_SOURCE), boa.loads(SNAPSHOT_SOURCE)
    prior.configure(True, 0)
    source.configure(True, 0)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [source], price_gas=1_500_000, snapshot_gas=1_500_000)
    caller = boa.loads(SNAPSHOT_CALLER)
    ripe_hq.startAddressUpdateToRegistry(17, caller, sender=governance.address)
    boa.env.time_travel(blocks=ripe_hq.registryChangeTimeLock() + 1)
    assert ripe_hq.confirmAddressUpdateToRegistry(17, sender=governance.address)
    return desk, prior, source, caller, request.param


def snapshot_trial(case, gas):
    desk, prior, source, caller, relay = case
    with cold_trial(desk, prior, source, caller):
        result = boa.env.execute_code(to_address=caller.address,
            data=caller.run.prepare_calldata(desk, prior, relay), gas=gas)
        logs = result.get_log_entries()
        state = (caller.writes(), prior.count(), source.count(), source.last())
        if result.is_error:
            assert state == (0, 0, 0, 0)
            assert not logs
        return result, state, logs


def test_d01_due_funded_writes(snapshot_case):
    result, state, logs = snapshot_trial(snapshot_case, 3_000_000)
    assert not result.is_error and int.from_bytes(result.output, "big") == 1
    assert state[:3] == (1, 1, 1) and state[3] > 0
    assert len(logs) == 2


def test_d01_due_underfunded_reverts_and_rolls_back(snapshot_case):
    result, _, _ = snapshot_trial(snapshot_case, 500_000)
    assert result.is_error and FUNDING_ERROR in result.output
    assert calls_to(result, snapshot_case[1])  # earlier snapshot actually ran
    assert not [call for call in calls_to(result, snapshot_case[2]) if not call.msg.is_static]


def test_d01_not_due_is_valid_noop(snapshot_case):
    desk, prior, source, caller, relay = snapshot_case
    source.configure(False, 0)
    result, state, logs = snapshot_trial(snapshot_case, 3_000_000)
    assert not result.is_error and int.from_bytes(result.output, "big") == int(relay)
    assert state == (1, 1, 0, 0) and len(logs) == 1
    # Base eagerly needs its 1.5M snapshot allowance even for this cheap no-op.
    result, _, _ = snapshot_trial(snapshot_case, 500_000)
    assert result.is_error and FUNDING_ERROR in result.output


@pytest.mark.parametrize("failure", (1, 2), ids=("revert", "out_of_gas"))
def test_d01_genuine_failure_is_isolated(snapshot_case, failure):
    snapshot_case[2].configure(True, failure)
    result, state, logs = snapshot_trial(snapshot_case, 3_000_000)
    assert not result.is_error and int.from_bytes(result.output, "big") == 0
    assert state == (1, 1, 0, 0) and len(logs) == 1
    failed = [call for call in calls_to(result, snapshot_case[2]) if not call.msg.is_static]
    assert len(failed) == 1 and failed[0].is_error and failed[0].msg.gas == 1_500_000


@pytest.mark.gas
def test_d01_cold_boundary_neighbors_match_generous_state_and_events(snapshot_case, request):
    generous, expected_state, expected_logs = snapshot_trial(snapshot_case, 3_000_000)
    assert not generous.is_error
    low, high = 100_000, 3_000_000
    while high - low > 1:
        mid = (low + high) // 2
        result, _, _ = snapshot_trial(snapshot_case, mid)
        if result.is_error:
            low = mid
        else:
            high = mid
    limits = sorted(set(range(100_000, 3_000_001, 100_000)) | {
        high + offset for offset in (-128, -32, -2, -1, 0, 1, 2, 32, 128)})
    observations = []
    for limit in limits:
        result, state, logs = snapshot_trial(snapshot_case, limit)
        observations.append((limit, not result.is_error))
        if not result.is_error:
            assert state == expected_state and logs == expected_logs
        assert (not result.is_error) == (limit >= high)
    request.node.user_properties.extend((('minimum_cold_execution_gas', high), ('non_monotonic_bands', 'none observed')))
    print(f"D01_COLD_BOUNDARY relay={snapshot_case[-1]} minimum={high} non_monotonic_bands=none_observed trials={len(limits)}")




@pytest.mark.gas
@pytest.mark.parametrize("operation", ("quote", "admission", "feed", "snapshot", "relay"))
@pytest.mark.parametrize("override", (False, True))
def test_compiled_call_overhead_and_full_allowance(
    ripe_hq, deploy3r, teller, mission_control, switchboard_alpha, operation, override,
):
    source = boa.loads(SNAPSHOT_SOURCE) if operation in ("snapshot", "relay") else _raw_source(1, True)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [source])
    _set_priorities(mission_control, switchboard_alpha, [1])
    budgets = (MAXIMUM,) * 3 if override else DEFAULTS
    if override:
        desk.setSourceGasBudgets(source, *budgets, sender=deploy3r)
    index = 0 if operation in ("quote", "admission") else (2 if operation == "feed" else 1)
    budget = budgets[index]
    with cold_trial(desk, source), boa.env.gas_meter_class(CallGasMeter):
        if operation == "quote":
            desk.getPrice(ETH, True, gas=10_000_000)
        elif operation == "admission":
            desk.qualifyCallerPriceSource(ETH, sender=source.address, gas=10_000_000)
        elif operation == "feed":
            desk.hasPriceFeed(ETH, gas=10_000_000)
        elif operation == "snapshot":
            desk.addPriceSnapshot(ETH, sender=teller.address, gas=10_000_000)
        else:
            desk.addGreenRefPoolSnapshot(1, sender=teller.address, gas=10_000_000)
        computation = desk._computation
        events = computation._gas_meter.events
        code = bytes(boa.env.get_code(desk.address))
        target = calls_to(computation, source)[-1]
        assert target.msg.gas == budget
        # Debit for forwarding occurs after memory expansion and cold access.
        forwarding = [i for i, event in enumerate(events) if event[3] in ("CALL", "STATICCALL") and event[2] == budget][-1]
        sample = [i for i in range(forwarding) if code[events[i][0]] == 0x5A][-1]
        available = events[sample][1] - events[sample][2]
        overhead = available - events[forwarding][1]
        assert 0 < overhead <= desk.eval("SOURCE_CALL_GAS_OVERHEAD")
        if operation != "snapshot":
            assert any(event[2] == 2_600 and event[0] == events[forwarding][0] for event in events[sample:forwarding])
        print(f"SOURCE_CALL_OVERHEAD operation={operation} override={override} gas={overhead}")


def install_curve_route(price_desk, governance, source):
    price_desk.startAddressUpdateToRegistry(2, source, sender=governance.address)
    boa.env.time_travel(blocks=price_desk.registryChangeTimeLock() + 1)
    assert price_desk.confirmAddressUpdateToRegistry(2, sender=governance.address)


@pytest.mark.parametrize("mode", ("absent", "disabled", "false", "empty", "malformed", "revert", "out_of_gas"))
def test_teller_relay_preserves_low_level_success_and_event(
    price_desk, teller, governance, deleverage, alice, mode,
):
    if mode in ("absent", "disabled"):
        price_desk.startAddressDisableInRegistry(2, sender=governance.address)
        boa.env.time_travel(blocks=price_desk.registryChangeTimeLock() + 1)
        price_desk.confirmAddressDisableInRegistry(2, sender=governance.address)
        if mode == "absent":
            assert price_desk.addGreenRefPoolSnapshot(1234, sender=teller.address, gas=40_000)
    elif mode in ("false", "revert", "out_of_gas"):
        source = boa.loads(SNAPSHOT_SOURCE)
        source.configure(mode != "false", {"false": 0, "revert": 1, "out_of_gas": 2}[mode])
        install_curve_route(price_desk, governance, source)
    else:
        source = boa.loads('''# @version 0.4.3
@external
@raw_return
def addGreenRefPoolSnapshot() -> Bytes[1]:
    return ''' + ('b""' if mode == "empty" else 'b"x"') + '\n')
        install_curve_route(price_desk, governance, source)
    with cold_trial(price_desk, teller):
        teller.performHousekeeping(False, alice, False, sender=deleverage.address, gas=1_000_000)
        logs = filter_logs(teller, "CurveSnapshotFailed")
        assert len(logs) == int(mode in ("revert", "out_of_gas"))
        if mode not in ("absent", "disabled"):
            source_call = calls_to(teller._computation, source)[0]
            assert source_call.msg.gas == 150_000  # shares snapshot budget; old cap was 500k
            assert source_call.msg.sender == bytes.fromhex(str(price_desk.address)[2:])


def test_relay_only_current_teller_and_own_registry_route(
    ripe_hq, price_desk, governance, deploy3r, teller, deleverage, bob,
):
    source = boa.loads(SNAPSHOT_SOURCE)
    source.configure(True, 0)
    own_desk = _isolated_price_desk(ripe_hq, deploy3r, [source])
    for caller in (bob, deploy3r, governance.address, deleverage.address):
        with boa.reverts("no perms"):
            own_desk.addGreenRefPoolSnapshot(1, sender=caller)
    assert own_desk.addGreenRefPoolSnapshot(1, sender=teller.address)
    assert source.count() == 1
    replacement = boa.load("contracts/core/Teller.vy", ripe_hq, False, 1)
    ripe_hq.startAddressUpdateToRegistry(17, replacement, sender=governance.address)
    boa.env.time_travel(blocks=ripe_hq.registryChangeTimeLock() + 1)
    assert ripe_hq.confirmAddressUpdateToRegistry(17, sender=governance.address)
    with boa.reverts("no perms"):
        own_desk.addGreenRefPoolSnapshot(1, sender=teller.address)
    assert own_desk.addGreenRefPoolSnapshot(1, sender=replacement.address)
    assert source.count() == 2


def test_teller_relay_underfunding_rolls_back_last_touch(
    price_desk, teller, governance, deleverage, alice, ledger,
):
    source = boa.loads(SNAPSHOT_SOURCE)
    source.configure(True, 0)
    install_curve_route(price_desk, governance, source)
    price_desk.setSourceGasBudgets(source, 0, 1_500_000, 0, sender=governance.address)
    before = ledger.lastTouch(alice)
    with cold_trial(teller, source):
        with boa.reverts("insufficient source gas"):
            teller.performHousekeeping(False, alice, False, sender=deleverage.address, gas=500_000)
        result = teller._computation
        assert calls_to(result, ledger)
        assert not result.get_log_entries()
        assert ledger.lastTouch(alice) == before and source.count() == 0
    with cold_trial(teller, source):
        teller.performHousekeeping(False, alice, False, sender=deleverage.address, gas=2_000_000)
        assert not filter_logs(teller, "CurveSnapshotFailed")
        assert ledger.lastTouch(alice) == boa.env.evm.patch.block_number
        assert source.count() == 1


def test_teller_deposit_snapshot_underfunding_rolls_back_user_and_prior_snapshot(
    price_desk, governance, alpha_token, alpha_token_whale, bob, simple_erc20_vault,
    teller, ledger, setGeneralConfig, setAssetConfig, mock_price_source,
):
    prior, source = boa.loads(SNAPSHOT_SOURCE), boa.loads(SNAPSHOT_SOURCE)
    prior.configure(True, 0)
    source.configure(True, 0)
    for item in (prior, source):
        price_desk.startAddNewAddressToRegistry(item, "snapshot boundary", sender=governance.address)
    boa.env.time_travel(blocks=price_desk.registryChangeTimeLock() + 1)
    for item in (prior, source):
        price_desk.confirmNewAddressToRegistry(item, sender=governance.address)
    price_desk.setSourceGasBudgets(source, 0, 1_500_000, 0, sender=governance.address)
    setGeneralConfig()
    setAssetConfig(alpha_token)
    mock_price_source.setPrice(alpha_token, 10**18)
    amount = 10 * 10**18
    alpha_token.transfer(bob, amount, sender=alpha_token_whale)
    alpha_token.approve(teller, amount, sender=bob)
    before = (alpha_token.balanceOf(bob), alpha_token.balanceOf(simple_erc20_vault),
              simple_erc20_vault.getTotalAmountForUser(bob, alpha_token), ledger.lastTouch(bob))
    with cold_trial(teller, prior, source):
        with boa.reverts("insufficient source gas"):
            teller.deposit(alpha_token, amount, bob, simple_erc20_vault, sender=bob, gas=1_200_000)
        result = teller._computation
        assert calls_to(result, prior)
        assert not result.get_log_entries()
        assert (alpha_token.balanceOf(bob), alpha_token.balanceOf(simple_erc20_vault),
                simple_erc20_vault.getTotalAmountForUser(bob, alpha_token), ledger.lastTouch(bob)) == before
        assert prior.count() == source.count() == 0
    with cold_trial(teller, prior, source):
        result = boa.env.execute_code(to_address=teller.address, sender=bob,
            data=teller.deposit.prepare_calldata(alpha_token, amount, bob, simple_erc20_vault), gas=6_000_000)
        assert not result.is_error, result.output[68:].decode(errors="replace")
        assert int.from_bytes(result.output, "big") == amount
        assert prior.count() == source.count() == 1
        assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == before[2] + amount


def test_production_wrapped_source_propagates_gas_dependent_canonical_dependency(
    ripe_hq, deploy3r, mission_control, switchboard_alpha,
):
    # Local production source, synthetic ERC-4626 dependency. A canonical
    # convertToAssets reply does not attest that the dependency had enough gas.
    underlying = boa.env.generate_address()
    vault = boa.loads('''# @version 0.4.3
@view
@external
def convertToAssets(amount: uint256) -> uint256:
    return amount * 7 // 10 if msg.gas < 150000 else amount
''')
    wrapped = boa.load("contracts/priceSources/wsuperOETHbPrices.vy", ripe_hq,
                       ZERO_ADDRESS, underlying, vault, ZERO_ADDRESS, 1, 2)
    healthy = boa.loads(ASSET_SOURCE, underlying, 10**18)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [healthy, wrapped])
    _set_priorities(mission_control, switchboard_alpha, [1, 2])
    for limit, price in ((150_000, 7 * 10**17), (500_000, 10**18)):
        with cold_trial(desk, vault, wrapped, healthy):
            assert desk.getPrice(vault, True, gas=limit) == price
            reply = calls_to(desk._computation, wrapped)[0]
            assert not reply.is_error
            assert (reply.msg.gas < 250_000) == (limit == 150_000)


@pytest.mark.parametrize("override", (False, True))
def test_asset_snapshot_underfunded_feed_check_never_calls_source(
    ripe_hq, deploy3r, teller, override,
):
    source = boa.loads(SNAPSHOT_SOURCE)
    source.configure(True, 0)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [source])
    if override:
        desk.setSourceGasBudgets(source, 0, 0, 200_000, sender=deploy3r)
    with cold_trial(desk, source):
        with boa.reverts("insufficient source gas"):
            desk.addPriceSnapshot(ETH, sender=teller.address, gas=150_000 if override else 50_000)
        assert not calls_to(desk._computation, source)
        assert source.count() == 0
        assert not desk._computation.get_log_entries()
    with cold_trial(desk, source):
        assert desk.addPriceSnapshot(ETH, sender=teller.address, gas=1_000_000)
        source_calls = calls_to(desk._computation, source)
        assert len(source_calls) == 2
        assert source_calls[0].msg.is_static
        assert source_calls[0].msg.gas == (200_000 if override else 75_000)
        assert source_calls[1].msg.gas == 150_000
        assert source.count() == 1


def test_asset_snapshot_underfunded_later_feed_check_rolls_back_prior_snapshot(
    ripe_hq, deploy3r, teller,
):
    prior, source = boa.loads(SNAPSHOT_SOURCE), boa.loads(SNAPSHOT_SOURCE)
    for item in (prior, source):
        item.configure(True, 0)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [prior, source])
    desk.setSourceGasBudgets(source, 0, 0, 1_000_000, sender=deploy3r)
    with cold_trial(desk, prior, source):
        with boa.reverts("insufficient source gas"):
            desk.addPriceSnapshot(ETH, sender=teller.address, gas=500_000)
        result = desk._computation
        assert any(not call.msg.is_static for call in calls_to(result, prior))
        assert not calls_to(result, source)
        assert prior.count() == source.count() == 0
        assert not result.get_log_entries()
    with cold_trial(desk, prior, source):
        assert desk.addPriceSnapshot(ETH, sender=teller.address, gas=2_000_000)
        assert prior.count() == source.count() == 1


@pytest.mark.parametrize("override", (False, True))
def test_permissionless_sync_token_scale_requires_effective_feed_budget(
    ripe_hq, deploy3r, bob, alpha_token, override,
):
    source = _raw_source(10**18, True)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [source])
    if override:
        desk.setSourceGasBudgets(source, 0, 0, 200_000, sender=deploy3r)
    with cold_trial(desk, source, alpha_token):
        with boa.reverts("insufficient source gas"):
            desk.syncTokenScale(alpha_token, sender=bob, gas=150_000 if override else 50_000)
        result = desk._computation
        assert not calls_to(result, source) and not calls_to(result, alpha_token)
        assert not result.get_log_entries()
        assert desk.tokenScale(alpha_token) == 0
    with cold_trial(desk, source, alpha_token):
        desk.syncTokenScale(alpha_token, sender=bob, gas=1_000_000)
        assert calls_to(desk._computation, source)[0].msg.gas == (200_000 if override else 75_000)
        assert len(filter_logs(desk, "TokenScaleSet")) == 1
        assert desk.tokenScale(alpha_token) == 10 ** alpha_token.decimals()
        with boa.reverts("already set"):
            desk.syncTokenScale(alpha_token, sender=bob, gas=1_000_000)


@pytest.mark.parametrize("method", ("getUsdValue", "getAssetAmount", "getEthUsdValue", "getEthAmount"))
@pytest.mark.parametrize("failure", ("zero_with_feed", "invalid_reply", "revert", "out_of_gas"))
def test_non_strict_conversion_helpers_propagate_stable_funding_error(
    ripe_hq, deploy3r, mission_control, switchboard_alpha, alpha_token, method, failure,
):
    if failure == "out_of_gas":
        source = _gas_source(price_iterations=1_000_000, exhaust_price=True)
    elif failure == "revert":
        source = _raw_source(price_mode=1)
    else:
        source = _raw_source(0, True) if failure == "zero_with_feed" else _raw_source(1, False)
    fallback = _raw_source(10**18, True)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [source, fallback])
    _set_priorities(mission_control, switchboard_alpha, [1, 2])
    desk.syncTokenScale(alpha_token, sender=deploy3r)
    token_unit = 10 ** alpha_token.decimals()
    args, expected = {
        "getUsdValue": ((alpha_token, token_unit), 10**18),
        "getAssetAmount": ((alpha_token, 10**18), token_unit),
        "getEthUsdValue": ((10**18,), 10**18),
        "getEthAmount": ((10**18,), 10**18),
    }[method]
    # The default selector is non-strict. Pin the complete external Error(string)
    # encoding so callers can depend on this error across every helper path.
    data = getattr(desk, method).prepare_calldata(*args)
    for gas in (100_000, 1_000_000):
        with cold_trial(desk, source, fallback):
            result = boa.env.execute_code(to_address=desk.address, data=data, gas=gas, is_modifying=False)
            source_call = calls_to(result, source)[0]
            if gas == 100_000:
                assert result.is_error
                assert result.output == bytes.fromhex("08c379a0") + encode(["string"], [FUNDING_ERROR.decode()])
                assert source_call.msg.gas < DEFAULTS[0]
                assert not calls_to(result, fallback)
            else:
                assert not result.is_error and int.from_bytes(result.output, "big") == expected
                assert source_call.msg.gas == DEFAULTS[0]
                assert len(calls_to(result, fallback)) == 1


LEGACY_DESK_WITHOUT_RELAY = '''# @version 0.4.3
@view
@external
def getAddr(id: uint256) -> address:
    return empty(address)
@external
def addPriceSnapshot(asset: address) -> bool:
    return False
'''


def test_new_teller_requires_price_desk_relay_before_activation(
    ripe_hq, price_desk, teller, governance, deleverage, alice, ledger,
):
    legacy = boa.loads(LEGACY_DESK_WITHOUT_RELAY)
    ripe_hq.startAddressUpdateToRegistry(7, legacy, sender=governance.address)
    boa.env.time_travel(blocks=ripe_hq.registryChangeTimeLock() + 1)
    assert ripe_hq.confirmAddressUpdateToRegistry(7, sender=governance.address)
    before = ledger.lastTouch(alice)
    with cold_trial(teller, legacy):
        with boa.reverts():
            teller.performHousekeeping(False, alice, False, sender=deleverage.address, gas=2_000_000)
        result = teller._computation
        relay_calls = calls_to(result, legacy)
        assert len(relay_calls) == 1 and relay_calls[0].is_error
        assert relay_calls[0].msg.data[:4] == price_desk.addGreenRefPoolSnapshot.prepare_calldata(2)[:4]
        assert not result.get_log_entries()
        assert ledger.lastTouch(alice) == before
    # Confirm the compatible desk while user operations remain closed. Only
    # after slot 7 is compatible may the new Teller be activated/opened.
    ripe_hq.startAddressUpdateToRegistry(7, price_desk, sender=governance.address)
    boa.env.time_travel(blocks=ripe_hq.registryChangeTimeLock() + 1)
    assert ripe_hq.confirmAddressUpdateToRegistry(7, sender=governance.address)
    with cold_trial(teller, price_desk):
        teller.performHousekeeping(False, alice, False, sender=deleverage.address, gas=2_000_000)
        assert not filter_logs(teller, "CurveSnapshotFailed")
        assert ledger.lastTouch(alice) == boa.env.evm.patch.block_number


@pytest.mark.gas
@pytest.mark.parametrize("quote_floor,undy_budget,repeats,expected", (
    (1_500_000, 0, 1, 42),
    (1_500_000, 3_000_000, 1, 200),
    (1_500_000, 3_000_000, 2, 42),
    (1_500_000, 3_500_000, 2, 200),
    (1_500_000, 6_000_000, 2, 200),
    (250_000, 2_000_000, 2, 200),
))
def test_base_floor_nested_fault_comparison(
    ripe_hq, deploy3r, mission_control, switchboard_alpha,
    quote_floor, undy_budget, repeats, expected,
):
    # Preserve the review's configuration experiment separately from acceptance
    # of any production budget. The route is synthetic; 42 is the outer fallback,
    # while 200 means the nested Undy route survived repeated Chainlink exhaustion.
    _, sources, undy, chainlink = nested_desk(
        ripe_hq, deploy3r, mission_control, switchboard_alpha, repeats=repeats,
    )
    desk = _isolated_price_desk(ripe_hq, deploy3r, sources, price_gas=quote_floor)
    if undy_budget:
        desk.setSourceGasBudgets(undy, undy_budget, 0, 0, sender=deploy3r)
    with cold_trial(desk, *sources):
        result = static_price(desk, ETH, True, 10_000_000)
        assert not result.is_error and int.from_bytes(result.output, "big") == expected
        assert calls_to(result, chainlink)[0].msg.gas == quote_floor
        assert calls_to(result, undy)[0].msg.gas == (undy_budget or quote_floor)
        if expected == 200:
            exhausted = calls_to(result, chainlink)
            assert len(exhausted) == repeats + 1
            assert all(call.is_error and call.msg.gas == quote_floor for call in exhausted)
        print(f"BASE_NESTED_FAULT floor={quote_floor} undy={undy_budget or quote_floor} "
              f"repeats={repeats} price={expected} execution_gas={result.get_gas_used()}")
