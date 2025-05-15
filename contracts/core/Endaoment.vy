# @version 0.4.1

initializes: gov
exports: gov.__interface__
import contracts.modules.LocalGov as gov

from ethereum.ercs import IERC20

event TempEndaomentFundsRecovered:
    asset: indexed(address)
    recipient: indexed(address)
    balance: uint256

MAX_RECOVER_ASSETS: constant(uint256) = 20


@deploy
def __init__(_ripeHq: address):
    gov.__init__(empty(address), _ripeHq, 0, 0)

    # NOTE: This is a temporary Endaoment contract. Real one coming soon.


# recovery


@external
def recoverFunds(_recipient: address, _asset: address):
    assert gov._canGovern(msg.sender) # dev: no perms
    self._recoverFunds(_recipient, _asset)


@external
def recoverFundsMany(_recipient: address, _assets: DynArray[address, MAX_RECOVER_ASSETS]):
    assert gov._canGovern(msg.sender) # dev: no perms
    for a: address in _assets:
        self._recoverFunds(_recipient, a)


@internal
def _recoverFunds(_recipient: address, _asset: address):
    assert empty(address) not in [_recipient, _asset] # dev: invalid recipient or asset
    balance: uint256 = staticcall IERC20(_asset).balanceOf(self)
    assert balance != 0 # dev: nothing to recover

    assert extcall IERC20(_asset).transfer(_recipient, balance, default_return_value=True) # dev: recovery failed
    log TempEndaomentFundsRecovered(asset=_asset, recipient=_recipient, balance=balance)