import pytest
from eth_hash.auto import keccak
from boa.contracts.base_evm_contract import BoaError

import boa

from constants import EIGHTEEN_DECIMALS
from conf_utils import filter_logs


OFFICIAL_TUPLE = "((uint64,int192),bytes32,bytes32,bytes32,bytes32,bytes32,uint8)[]"
OFFICIAL_FEE_SEL = "b2255ba3"
OFFICIAL_UPDATE_SEL = "41bd64ba"
OLD_FEE_SEL = "73854e60"
OLD_UPDATE_SEL = "c52be1c7"

BYTES_CALLER = """
# @version 0.4.3

interface RipeStorkBytes:
    def getUpdateFeeV1(_payload: Bytes[2048]) -> uint256: view
    def updateTemporalNumericValuesV1(_payload: Bytes[2048]): payable

interface RipeStorkAdapterBytes:
    def updateStorkPrice(_payload: Bytes[2048]) -> bool: payable
    def updateStorkPriceNoPay(_payload: Bytes[2048]) -> bool: nonpayable

@external
@view
def ripeFee(_target: address, _payload: Bytes[2048]) -> uint256:
    return staticcall RipeStorkBytes(_target).getUpdateFeeV1(_payload)

@external
def ripeUpdate(_target: address, _payload: Bytes[2048]):
    extcall RipeStorkBytes(_target).updateTemporalNumericValuesV1(_payload)

@external
def ripeAdapterUpdate(_target: address, _payload: Bytes[2048]):
    extcall RipeStorkAdapterBytes(_target).updateStorkPrice(_payload)

@external
def ripeAdapterUpdateNoPay(_target: address, _payload: Bytes[2048]):
    extcall RipeStorkAdapterBytes(_target).updateStorkPriceNoPay(_payload)
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


def _payload(mock_stork, n=1):
    feed_id = bytes.fromhex(f"{n:064x}")
    return mock_stork.createPriceFeedUpdateData(
        feed_id,
        EIGHTEEN_DECIMALS,
        boa.env.evm.patch.timestamp,
    )


def test_stork_official_tuple_array_selectors():
    assert _selector(f"getUpdateFeeV1({OFFICIAL_TUPLE})") == OFFICIAL_FEE_SEL
    assert _selector(f"updateTemporalNumericValuesV1({OFFICIAL_TUPLE})") == OFFICIAL_UPDATE_SEL
    assert _selector("getUpdateFeeV1(bytes)") == OLD_FEE_SEL
    assert _selector("updateTemporalNumericValuesV1(bytes)") == OLD_UPDATE_SEL


def test_stork_update_empty_one_twenty_and_reject_twenty_one(
    stork_prices,
    mock_stork,
    authorized_caller,
):
    one = _payload(mock_stork, 1)
    assert mock_stork.getUpdateFeeV1([]) == 0
    assert mock_stork.getUpdateFeeV1([one]) == 1
    twenty = [_payload(mock_stork, i + 1) for i in range(20)]
    assert mock_stork.getUpdateFeeV1(twenty) == 20
    with pytest.raises((ValueError, OverflowError, BoaError)):
        mock_stork.getUpdateFeeV1(twenty + [_payload(mock_stork, 21)])

    boa.env.set_balance(authorized_caller, 100)
    assert stork_prices.updateStorkPrice([], sender=authorized_caller, value=1)
    log = filter_logs(stork_prices, "StorkPriceUpdated")[0]
    assert list(log.payload) == []
    assert log.feeAmount == 0

    assert stork_prices.updateStorkPrice([one], sender=authorized_caller, value=10)
    log = filter_logs(stork_prices, "StorkPriceUpdated")[0]
    assert list(log.payload) == [one]
    assert log.feeAmount == 1
    assert log.caller == authorized_caller

    boa.env.set_balance(authorized_caller, 100)
    assert stork_prices.updateStorkPrice(twenty, sender=authorized_caller, value=40)
    log = filter_logs(stork_prices, "StorkPriceUpdated")[0]
    assert len(log.payload) == 20
    assert log.feeAmount == 20

    with pytest.raises((ValueError, OverflowError, BoaError)):
        stork_prices.updateStorkPrice(twenty + [one], sender=authorized_caller, value=40)


def test_stork_paid_nopay_refund_and_old_bytes_revert(
    stork_prices,
    mock_stork,
    authorized_caller,
):
    payload = _payload(mock_stork, 7)
    boa.env.set_balance(authorized_caller, EIGHTEEN_DECIMALS)
    pre = boa.env.get_balance(authorized_caller)
    mock_before = boa.env.get_balance(mock_stork.address)

    assert stork_prices.updateStorkPrice([payload], sender=authorized_caller, value=EIGHTEEN_DECIMALS)
    assert boa.env.get_balance(mock_stork.address) == mock_before + 1
    assert boa.env.get_balance(authorized_caller) == pre - 1

    boa.env.set_balance(stork_prices.address, 5)
    pre_contract = boa.env.get_balance(stork_prices.address)
    assert stork_prices.updateStorkPriceNoPay([payload], sender=authorized_caller)
    assert boa.env.get_balance(stork_prices.address) == pre_contract - 1

    caller = boa.loads(BYTES_CALLER)
    with boa.reverts():
        caller.ripeFee(mock_stork.address, b"\x00" * 32)
    with boa.reverts():
        caller.ripeUpdate(mock_stork.address, b"\x00" * 32)
    with boa.reverts():
        caller.ripeFee(stork_prices.address, b"\x00" * 32)
    with boa.reverts():
        caller.ripeAdapterUpdate(stork_prices.address, b"\x00" * 32)
    with boa.reverts():
        caller.ripeAdapterUpdateNoPay(stork_prices.address, b"\x00" * 32)
