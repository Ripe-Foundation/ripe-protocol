# @version 0.4.1

implements: IERC20
implements: IERC4626

exports: token.__interface__
exports: erc4626.__interface__

initializes: token
initializes: erc4626[token := token]

from contracts.modules import Erc20Token as token
import contracts.modules.Erc4626Token as erc4626

from ethereum.ercs import IERC20
from ethereum.ercs import IERC4626
from ethereum.ercs import IERC20Detailed

# erc20 token details
NAME: constant(String[25]) = "Savings Green USD"
SYMBOL: constant(String[6]) = "sGREEN"
DECIMALS: immutable(uint8)


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
    token.__init__(NAME, _ripeHq, _initialGov, _minHqTimeLock, _maxHqTimeLock, _initialSupply, _initialSupplyRecipient)
    erc4626.__init__(_asset)

    DECIMALS = staticcall IERC20Detailed(_asset).decimals()


##############
# Token Info #
##############


@pure
@external
def name() -> String[25]:
    return NAME


@pure
@external
def symbol() -> String[6]:
    return SYMBOL


@view
@external
def decimals() -> uint8:
    return DECIMALS
