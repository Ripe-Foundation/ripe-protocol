"""Constructor allowances and the Teller reference-pool relay."""

import boa
import pytest

from conf_utils import filter_logs
from registries.test_price_desk_isolation import (
    ETH,
    _gas_source,
    _isolated_price_desk,
    _raw_source,
    _set_priorities,
)


SNAPSHOT_SOURCE = """# @version 0.4.3
work: uint256
count: public(uint256)
caller: public(address)

@external
def setWork(work: uint256):
    self.work = work

@view
@external
def hasPriceFeed(asset: address) -> bool:
    return True

@internal
def _snapshot() -> bool:
    checksum: uint256 = 0
    for i: uint256 in range(self.work, bound=100_000):
        checksum = unsafe_add(checksum, i)
    assert checksum != max_value(uint256)
    self.count += 1
    self.caller = msg.sender
    return True

@external
def addPriceSnapshot(asset: address) -> bool:
    return self._snapshot()

@external
def addGreenRefPoolSnapshot() -> bool:
    return self._snapshot()
"""


def _calls_to(computation, source):
    address = bytes.fromhex(str(source.address)[2:])
    return [child for child in computation.children if child.msg.code_address == address] + [
        call for child in computation.children for call in _calls_to(child, source)
    ]


def _activate(ripe_hq, governance, slot, replacement):
    ripe_hq.startAddressUpdateToRegistry(slot, replacement, sender=governance.address)
    boa.env.time_travel(blocks=ripe_hq.registryChangeTimeLock() + 1)
    assert ripe_hq.confirmAddressUpdateToRegistry(slot, sender=governance.address)


@pytest.mark.parametrize("quote,snapshot", [(0, 150_000), (250_000, 0), (0, 0)])
def test_zero_allowances_rejected(ripe_hq, deploy3r, quote, snapshot):
    with boa.reverts():
        _isolated_price_desk(ripe_hq, deploy3r, [], quote, snapshot)


def test_allowances_are_independent_and_readable(ripe_hq, deploy3r):
    desk = _isolated_price_desk(ripe_hq, deploy3r, [], 1_500_000, 900_000)
    assert desk.PRICE_SOURCE_PRICE_GAS() == 1_500_000
    assert desk.PRICE_SOURCE_SNAPSHOT_GAS() == 900_000


@pytest.mark.parametrize("strict", [False, True])
def test_larger_quote_allowance_recovers_expensive_source_and_keeps_fallback(
    ripe_hq, deploy3r, mission_control, switchboard_alpha, strict,
):
    source = _gas_source(price=123, has_feed=True, price_iterations=7_000)
    fallback = _raw_source(42, True)
    _set_priorities(mission_control, switchboard_alpha, [1, 2])
    small = _isolated_price_desk(ripe_hq, deploy3r, [source, fallback])
    larger = _isolated_price_desk(ripe_hq, deploy3r, [source, fallback], 1_500_000, 150_000)
    assert small.getPrice(ETH, strict, gas=3_000_000) == 42
    assert _calls_to(small._computation, source)[0].is_error
    assert larger.getPrice(ETH, strict, gas=3_000_000) == 123
    assert _calls_to(larger._computation, source)[0].msg.gas == 1_500_000
    assert not _calls_to(larger._computation, fallback)
    assert small.qualifyCallerPriceSource(ETH, sender=source.address) == (0, 2)
    assert larger.qualifyCallerPriceSource(ETH, sender=source.address) == (123, 1)

    source.configure(123, True, 100_000, 0, 0, True, False, False)
    assert larger.getPrice(ETH, strict, gas=3_000_000) == 42
    assert _calls_to(larger._computation, source)[0].is_error


def test_increased_quote_allowance_does_not_change_non_strict_underfunding(
    ripe_hq, deploy3r, mission_control, switchboard_alpha,
):
    source = _gas_source(price=123, has_feed=True, price_iterations=7_000)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [source], 1_500_000, 150_000)
    _set_priorities(mission_control, switchboard_alpha, [1])
    assert desk.getPrice(ETH, False, gas=100_000) == 0
    assert desk.getPrice(ETH, True, gas=3_000_000) == 123


@pytest.mark.parametrize("relay", [False, True], ids=["asset", "green_reference"])
def test_larger_snapshot_allowance_recovers_real_writes(ripe_hq, deploy3r, teller, relay):
    source = boa.loads(SNAPSHOT_SOURCE)
    source.setWork(7_000)
    small = _isolated_price_desk(ripe_hq, deploy3r, [source], 250_000, 150_000)
    larger = _isolated_price_desk(ripe_hq, deploy3r, [source], 250_000, 1_500_000)
    def take(desk, gas):
        if relay:
            return desk.addGreenRefPoolSnapshot(1, sender=teller.address, gas=gas)
        return desk.addPriceSnapshot(ETH, sender=teller.address, gas=gas)

    assert not take(small, 3_000_000)
    assert source.count() == 0
    assert take(larger, 3_000_000)
    assert source.count() == 1 and source.caller() == larger.address
    calls = _calls_to(larger._computation, source)
    assert calls[-1].msg.gas == 1_500_000
    # Increasing the cap does not guarantee a caller funds it: preserve the
    # existing fail-soft behavior and explicitly expose the skipped write.
    assert not take(larger, 100_000)
    assert source.count() == 1


def test_relay_authenticates_current_teller_and_uses_own_registry(
    ripe_hq, governance, deploy3r, teller, bob,
):
    source = boa.loads(SNAPSHOT_SOURCE)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [source])
    for caller in (bob, deploy3r, governance.address):
        with boa.reverts("no perms"):
            desk.addGreenRefPoolSnapshot(1, sender=caller)
    assert desk.addGreenRefPoolSnapshot(1, sender=teller.address)
    assert source.count() == 1
    replacement = boa.load("contracts/core/Teller.vy", ripe_hq, False, 1)
    _activate(ripe_hq, governance, 17, replacement)
    with boa.reverts("no perms"):
        desk.addGreenRefPoolSnapshot(1, sender=teller.address)
    assert desk.addGreenRefPoolSnapshot(1, sender=replacement.address)
    assert source.count() == 2


@pytest.mark.parametrize("mode", ["absent", "disabled", "false", "empty", "malformed", "revert", "out_of_gas"])
def test_teller_relay_preserves_success_and_failure_event(
    ripe_hq, governance, deploy3r, teller, deleverage, alice, mode,
):
    body = {
        "false": 'return b"' + r"\x00" * 32 + '"',
        "empty": 'return b""',
        "malformed": 'return b"x"',
        "revert": "raise",
        "out_of_gas": "for i: uint256 in range(100_000):\n        assert msg.gas > 1\n    return b\"\"",
    }.get(mode, 'return b""')
    source = boa.loads(f'''# @version 0.4.3
@external
@raw_return
def addGreenRefPoolSnapshot() -> Bytes[32]:
    {body}
''')
    desk = _isolated_price_desk(ripe_hq, deploy3r, [_raw_source(), source])
    if mode in ("absent", "disabled"):
        desk.startAddressDisableInRegistry(2, sender=deploy3r)
        assert desk.confirmAddressDisableInRegistry(2, sender=deploy3r)
        if mode == "absent":
            assert desk.addGreenRefPoolSnapshot(1234, sender=teller.address)
    _activate(ripe_hq, governance, 7, desk)
    teller.performHousekeeping(False, alice, False, sender=deleverage.address, gas=2_000_000)
    assert len(filter_logs(teller, "CurveSnapshotFailed")) == int(mode in ("revert", "out_of_gas"))
    if mode not in ("absent", "disabled"):
        call = _calls_to(teller._computation, source)[0]
        assert call.msg.sender == bytes.fromhex(str(desk.address)[2:])
        assert call.msg.gas == desk.PRICE_SOURCE_SNAPSHOT_GAS()


def test_teller_uses_larger_snapshot_allowance(ripe_hq, governance, deploy3r, teller, deleverage, alice):
    source = boa.loads(SNAPSHOT_SOURCE)
    source.setWork(10_000)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [_raw_source(), source], 250_000, 1_500_000)
    _activate(ripe_hq, governance, 7, desk)
    teller.performHousekeeping(False, alice, False, sender=deleverage.address, gas=3_000_000)
    assert source.count() == 1 and source.caller() == desk.address
    assert not filter_logs(teller, "CurveSnapshotFailed")
    call = _calls_to(teller._computation, source)[0]
    assert call.msg.gas == 1_500_000
    assert call.get_gas_used() > 500_000  # exceeded the old Teller-specific cap


def test_relay_teller_requires_compatible_desk_and_rolls_back_last_touch(
    ripe_hq, governance, price_desk, teller, deleverage, alice, ledger,
):
    old_interface = boa.loads('''# @version 0.4.3
@view
@external
def getAddr(id: uint256) -> address:
    return empty(address)
''')
    _activate(ripe_hq, governance, 7, old_interface)
    before = ledger.lastTouch(alice)
    with boa.reverts():
        teller.performHousekeeping(False, alice, False, sender=deleverage.address)
    assert ledger.lastTouch(alice) == before
    _activate(ripe_hq, governance, 7, price_desk)
    teller.performHousekeeping(False, alice, False, sender=deleverage.address)
    assert ledger.lastTouch(alice) == boa.env.evm.patch.block_number
