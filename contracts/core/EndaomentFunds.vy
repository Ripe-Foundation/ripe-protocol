#            ___          ___                       ___          ___          ___          ___          ___                 
#           /\__\        /\  \        _____        /\  \        /\  \        /\  \        /\__\        /\  \                
#          /:/ _/_       \:\  \      /::\  \      /::\  \      /::\  \      |::\  \      /:/ _/_       \:\  \       ___     
#         /:/ /\__\       \:\  \    /:/\:\  \    /:/\:\  \    /:/\:\  \     |:|:\  \    /:/ /\__\       \:\  \     /\__\    
#        /:/ /:/ _/_  _____\:\  \  /:/  \:\__\  /:/ /::\  \  /:/  \:\  \  __|:|\:\  \  /:/ /:/ _/_  _____\:\  \   /:/  /    
#       /:/_/:/ /\__\/::::::::\__\/:/__/ \:|__|/:/_/:/\:\__\/:/__/ \:\__\/::::|_\:\__\/:/_/:/ /\__\/::::::::\__\ /:/__/     
#       \:\/:/ /:/  /\:\~~\~~\/__/\:\  \ /:/  /\:\/:/  \/__/\:\  \ /:/  /\:\~~\  \/__/\:\/:/ /:/  /\:\~~\~~\/__//::\  \     
#        \::/_/:/  /  \:\  \       \:\  /:/  /  \::/__/      \:\  /:/  /  \:\  \       \::/_/:/  /  \:\  \     /:/\:\  \    
#         \:\/:/  /    \:\  \       \:\/:/  /    \:\  \       \:\/:/  /    \:\  \       \:\/:/  /    \:\  \    \/__\:\  \   
#          \::/  /      \:\__\       \::/  /      \:\__\       \::/  /      \:\__\       \::/  /      \:\__\        \:\__\  
#           \/__/        \/__/        \/__/        \/__/        \/__/        \/__/        \/__/        \/__/         \/__/  
#
#     ╔════════════════════════════════════════════════════╗
#     ║  ** Endaoment Funds **                             ║
#     ║  Secure vault for protocol-owned funds             ║
#     ╚════════════════════════════════════════════════════╝
#
#     Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
#     Ripe Foundation (C) 2025

# @version 0.4.3

exports: addys.__interface__
initializes: addys
import contracts.modules.Addys as addys

from ethereum.ercs import IERC20

event EndaomentFundsMoved:
    token: indexed(address)
    to: indexed(address)
    amount: uint256

API_VERSION: constant(String[28]) = "0.1.0"


@deploy
def __init__(_ripeHq: address):
    addys.__init__(_ripeHq)


@payable
@external
def __default__():
    pass


@view
@external
def hasBalance(_asset: address = empty(address)) -> bool:
    if _asset != empty(address):
        return staticcall IERC20(_asset).balanceOf(self) != 0
    else:
        return self.balance != 0


@external
def transfer(_asset: address = empty(address), _amount: uint256 = max_value(uint256)) -> uint256:
    endaoment: address = addys._getEndaomentAddr()
    assert msg.sender == endaoment # dev: not authorized

    actualAmount: uint256 = 0

    # erc20 transfer
    if _asset != empty(address):
        actualAmount = min(_amount, staticcall IERC20(_asset).balanceOf(self))
        assert actualAmount != 0 # dev: insufficient balance
        assert extcall IERC20(_asset).transfer(endaoment, actualAmount, default_return_value = True) # dev: transfer failed

    # eth transfer
    else:
        actualAmount = min(_amount, self.balance)
        assert actualAmount != 0 # dev: insufficient balance
        send(endaoment, actualAmount)

    log EndaomentFundsMoved(token=_asset, to=endaoment, amount=actualAmount)
    return actualAmount
