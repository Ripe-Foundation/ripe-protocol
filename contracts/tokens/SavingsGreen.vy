# @version 0.4.1

exports: token.__interface__
exports: erc4626.__interface__

initializes: token
initializes: erc4626[token := token]

from contracts.tokens.modules import Erc20Token as token
import contracts.tokens.modules.Erc4626Token as erc4626

from ethereum.ercs import IERC20Detailed


@deploy
def __init__(
    _asset: address,
    _ripeHq: address,
    _initialGov: address,
    _minHqTimeLock: uint256,
    _maxHqTimeLock: uint256,
    _initialSupply: uint256,
    _initialSupplyRecipient: address,
):
    token.__init__("Savings Green USD", "sGREEN", staticcall IERC20Detailed(_asset).decimals(), _ripeHq, _initialGov, _minHqTimeLock, _maxHqTimeLock, _initialSupply, _initialSupplyRecipient)
    erc4626.__init__(_asset)
