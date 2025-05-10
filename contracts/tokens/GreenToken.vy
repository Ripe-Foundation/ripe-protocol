# @version 0.4.1

implements: IERC20
from ethereum.ercs import IERC20

initializes: token
exports: token.__interface__
from contracts.modules import Erc20Token as token

interface RipeHq:
    def canSetTokenBlacklist(_addr: address) -> bool: view
    def canMintGreen(_addr: address) -> bool: view

# ripe protocol
ripeHq: public(address)

# token details
NAME: constant(String[25]) = "Green USD Stablecoin"
SYMBOL: constant(String[5]) = "GREEN"
DECIMALS: constant(uint8) = 18


@deploy
def __init__(
    _ripeHq: address,
    _initialSupply: uint256,
    _initialSupplyRecipient: address,
):
    assert _ripeHq != empty(address) and _ripeHq.is_contract # dev: cannot be 0x0
    self.ripeHq = _ripeHq

    # initialize erc20 token module
    token.__init__(NAME, _initialSupply, _initialSupplyRecipient)


##########
# Basics #
##########


@pure
@external
def name() -> String[25]:
    return NAME


@pure
@external
def symbol() -> String[5]:
    return SYMBOL


@pure
@external
def decimals() -> uint8:
    return DECIMALS


##################
# Require Access #
##################


@external
def mint(_recipient: address, _amount: uint256) -> bool:
    assert staticcall RipeHq(self.ripeHq).canMintGreen(msg.sender) # dev: cannot mint
    return token._mint(_recipient, _amount)


@external
def setBlacklist(_addr: address, _shouldBlacklist: bool) -> bool:
    assert staticcall RipeHq(self.ripeHq).canSetTokenBlacklist(msg.sender) # dev: no perms
    return token._setBlacklist(_addr, _shouldBlacklist)
