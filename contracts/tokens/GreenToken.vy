# @version 0.4.1

exports: token.__interface__
initializes: token

from contracts.modules import Erc20Token as token

interface RipeHq:
    def canMintGreen(_addr: address) -> bool: view


@deploy
def __init__(
    _ripeHq: address,
    _initialGov: address,
    _minHqTimeLock: uint256,
    _maxHqTimeLock: uint256,
    _initialSupply: uint256,
    _initialSupplyRecipient: address,
):
    token.__init__("Green USD Stablecoin", "GREEN", 18, _ripeHq, _initialGov, _minHqTimeLock, _maxHqTimeLock, _initialSupply, _initialSupplyRecipient)


###########
# Minting #
###########


@external
def mint(_recipient: address, _amount: uint256) -> bool:
    assert staticcall RipeHq(token.ripeHq).canMintGreen(msg.sender) # dev: cannot mint
    return token._mint(_recipient, _amount)
