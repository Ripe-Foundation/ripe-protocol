# @version 0.4.1

implements: IERC20

exports: token.__interface__
initializes: token

from ethereum.ercs import IERC20
from contracts.modules import Erc20Token as token

interface RipeHq:
    def canMintRipe(_addr: address) -> bool: view
    
# token details
NAME: constant(String[25]) = "Ripe DAO Governance Token"
SYMBOL: constant(String[4]) = "RIPE"
DECIMALS: constant(uint8) = 18


@deploy
def __init__(
    _initialGov: address,
    _minHqTimeLock: uint256,
    _maxHqTimeLock: uint256,
    _initialSupply: uint256,
    _initialSupplyRecipient: address,
):
    token.__init__(NAME, _minHqTimeLock, _maxHqTimeLock, _initialGov, _initialSupply, _initialSupplyRecipient)


##########
# Basics #
##########


@pure
@external
def name() -> String[25]:
    return NAME


@pure
@external
def symbol() -> String[4]:
    return SYMBOL


@pure
@external
def decimals() -> uint8:
    return DECIMALS


###########
# Minting #
###########


@external
def mint(_recipient: address, _amount: uint256) -> bool:
    assert staticcall RipeHq(token.ripeHq).canMintRipe(msg.sender) # dev: cannot mint
    return token._mint(_recipient, _amount)
