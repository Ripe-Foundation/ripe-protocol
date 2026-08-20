import pytest
from eth_hash.auto import keccak
from boa.contracts.base_evm_contract import BoaError

import boa

from constants import EIGHTEEN_DECIMALS
from conf_utils import filter_logs


OFFICIAL_FEE_SEL = "d47eed45"
OFFICIAL_UPDATE_SEL = "ef9e5e28"
OLD_FEE_SEL = "238e0a8a"
OLD_UPDATE_SEL = "c51be003"

BYTES_CALLER = """
# @version 0.4.3

interface RipePythBytes:
    def getUpdateFee(_payload: Bytes[2048]) -> uint256: view
    def updatePriceFeeds(_payload: Bytes[2048]): payable

interface RipePythAdapterBytes:
    def updatePythPrice(_payload: Bytes[2048]) -> bool: payable
    def updatePythPriceNoPay(_payload: Bytes[2048]) -> bool: nonpayable

@external
@view
def ripeFee(_target: address, _payload: Bytes[2048]) -> uint256:
    return staticcall RipePythBytes(_target).getUpdateFee(_payload)

@external
def ripeUpdate(_target: address, _payload: Bytes[2048]):
    extcall RipePythBytes(_target).updatePriceFeeds(_payload)

@external
def ripeAdapterUpdate(_target: address, _payload: Bytes[2048]):
    extcall RipePythAdapterBytes(_target).updatePythPrice(_payload)

@external
def ripeAdapterUpdateNoPay(_target: address, _payload: Bytes[2048]):
    extcall RipePythAdapterBytes(_target).updatePythPriceNoPay(_payload)
"""


def _selector(sig):
    return keccak(sig.encode()).hex()[:8]


@pytest.fixture(scope="module")
def authorized_caller(switchboard_alpha, mission_control, governance, bob):
    action_id = switchboard_alpha.setCanPerformLiteAction(bob, True, sender=governance.address)
    boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock())
    switchboard_alpha.executePendingAction(action_id, sender=governance.address)
    assert mission_control.canPerformLiteAction(bob)
    return bob


def _payload(mock_pyth, n=1):
    feed_id = bytes.fromhex(f"{n:064x}")
    return mock_pyth.createPriceFeedUpdateData(
        feed_id,
        98000000,
        50000,
        -8,
        boa.env.evm.patch.timestamp,
    )


def test_pyth_official_bytes_array_selectors():
    assert _selector("getUpdateFee(bytes[])") == OFFICIAL_FEE_SEL
    assert _selector("updatePriceFeeds(bytes[])") == OFFICIAL_UPDATE_SEL
    assert _selector("getUpdateFee(bytes)") == OLD_FEE_SEL
    assert _selector("updatePriceFeeds(bytes)") == OLD_UPDATE_SEL


def test_pyth_update_empty_one_twenty_and_reject_twenty_one(
    pyth_prices,
    mock_pyth,
    authorized_caller,
):
    one = _payload(mock_pyth, 1)
    assert mock_pyth.getUpdateFee([]) == 0
    assert mock_pyth.getUpdateFee([one]) == 1
    twenty = [_payload(mock_pyth, i + 1) for i in range(20)]
    assert mock_pyth.getUpdateFee(twenty) == 20
    with pytest.raises((ValueError, OverflowError, BoaError)):
        mock_pyth.getUpdateFee(twenty + [_payload(mock_pyth, 21)])

    boa.env.set_balance(authorized_caller, 100)
    assert pyth_prices.updatePythPrice([], sender=authorized_caller, value=1)
    log = filter_logs(pyth_prices, "PythPriceUpdated")[0]
    assert list(log.payload) == []
    assert log.feeAmount == 0

    assert pyth_prices.updatePythPrice([one], sender=authorized_caller, value=10)
    log = filter_logs(pyth_prices, "PythPriceUpdated")[0]
    assert list(log.payload) == [one]
    assert log.feeAmount == 1
    assert log.caller == authorized_caller

    boa.env.set_balance(authorized_caller, 100)
    assert pyth_prices.updatePythPrice(twenty, sender=authorized_caller, value=40)
    log = filter_logs(pyth_prices, "PythPriceUpdated")[0]
    assert len(log.payload) == 20
    assert log.feeAmount == 20

    with pytest.raises((ValueError, OverflowError, BoaError)):
        pyth_prices.updatePythPrice(twenty + [one], sender=authorized_caller, value=40)


def test_pyth_paid_nopay_refund_and_old_bytes_revert(
    pyth_prices,
    mock_pyth,
    authorized_caller,
):
    payload = _payload(mock_pyth, 7)
    boa.env.set_balance(authorized_caller, EIGHTEEN_DECIMALS)
    pre = boa.env.get_balance(authorized_caller)
    mock_before = boa.env.get_balance(mock_pyth.address)

    assert pyth_prices.updatePythPrice([payload], sender=authorized_caller, value=EIGHTEEN_DECIMALS)
    assert boa.env.get_balance(mock_pyth.address) == mock_before + 1
    assert boa.env.get_balance(authorized_caller) == pre - 1

    boa.env.set_balance(pyth_prices.address, 5)
    pre_contract = boa.env.get_balance(pyth_prices.address)
    assert pyth_prices.updatePythPriceNoPay([payload], sender=authorized_caller)
    assert boa.env.get_balance(pyth_prices.address) == pre_contract - 1

    caller = boa.loads(BYTES_CALLER)
    with boa.reverts():
        caller.ripeFee(mock_pyth.address, b"\x00" * 32)
    with boa.reverts():
        caller.ripeUpdate(mock_pyth.address, b"\x00" * 32)
    with boa.reverts():
        caller.ripeFee(pyth_prices.address, b"\x00" * 32)
    with boa.reverts():
        caller.ripeAdapterUpdate(pyth_prices.address, b"\x00" * 32)
    with boa.reverts():
        caller.ripeAdapterUpdateNoPay(pyth_prices.address, b"\x00" * 32)
