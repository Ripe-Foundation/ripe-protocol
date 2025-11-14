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
from ethereum.ercs import IERC721

event EndaomentFundsMoved:
    token: indexed(address)
    to: indexed(address)
    amount: uint256

event EndaomentNftMoved:
    nft: indexed(address)
    to: indexed(address)
    tokenId: uint256

API_VERSION: constant(String[28]) = "0.1.0"
ERC721_RECEIVE_DATA: constant(Bytes[1024]) = b"UE721"


@deploy
def __init__(_ripeHq: address):
    addys.__init__(_ripeHq)


@view
@external
def onERC721Received(_operator: address, _owner: address, _tokenId: uint256, _data: Bytes[1024]) -> bytes4:
    # must implement method for safe NFT transfers
    return method_id("onERC721Received(address,address,uint256,bytes)", output_type = bytes4)


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


@external
def transferNft(_nft: address, _tokenId: uint256):
    endaoment: address = addys._getEndaomentAddr()
    assert msg.sender == endaoment # dev: not authorized

    assert staticcall IERC721(_nft).ownerOf(_tokenId) == self # dev: not owner
    extcall IERC721(_nft).safeTransferFrom(self, endaoment, _tokenId, ERC721_RECEIVE_DATA)
    log EndaomentNftMoved(nft=_nft, to=endaoment, tokenId=_tokenId)
