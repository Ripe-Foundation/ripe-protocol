#                _____                    _____                    _____                    _____          
#               /\    \                  /\    \                  /\    \                  /\    \         
#              /::\    \                /::\    \                /::\    \                /::\    \        
#             /::::\    \               \:::\    \              /::::\    \              /::::\    \       
#            /::::::\    \               \:::\    \            /::::::\    \            /::::::\    \      
#           /:::/\:::\    \               \:::\    \          /:::/\:::\    \          /:::/\:::\    \     
#          /:::/__\:::\    \               \:::\    \        /:::/__\:::\    \        /:::/__\:::\    \    
#         /::::\   \:::\    \              /::::\    \      /::::\   \:::\    \      /::::\   \:::\    \   
#        /::::::\   \:::\    \    ____    /::::::\    \    /::::::\   \:::\    \    /::::::\   \:::\    \  
#       /:::/\:::\   \:::\____\  /\   \  /:::/\:::\    \  /:::/\:::\   \:::\____\  /:::/\:::\   \:::\    \ 
#      /:::/  \:::\   \:::|    |/::\   \/:::/  \:::\____\/:::/  \:::\   \:::|    |/:::/__\:::\   \:::\____\
#      \::/   |::::\  /:::|____|\:::\  /:::/    \::/    /\::/    \:::\  /:::|____|\:::\   \:::\   \::/    /
#       \/____|:::::\/:::/    /  \:::\/:::/    / \/____/  \/_____/\:::\/:::/    /  \:::\   \:::\   \/____/ 
#             |:::::::::/    /    \::::::/    /                    \::::::/    /    \:::\   \:::\    \     
#             |::|\::::/    /      \::::/____/                      \::::/    /      \:::\   \:::\____\    
#             |::| \::/____/        \:::\    \                       \::/____/        \:::\   \::/    /    
#             |::|  ~|               \:::\    \                       ~~               \:::\   \/____/     
#             |::|   |                \:::\    \                                        \:::\    \         
#             \::|   |                 \:::\____\                                        \:::\____\        
#              \:|   |                  \::/    /                                         \::/    /        
#               \|___|                   \/____/                                           \/____/         
#                                                       ╔╦╗╔═╗╦╔═╔═╗╔╗╔
#                                                        ║ ║ ║╠╩╗║╣ ║║║
#                                                        ╩ ╚═╝╩ ╩╚═╝╝╚╝
#     ╔════════════════════════════════════════════════════════╗
#     ║  ** Ripe Token **                                      ║
#     ║  Erc20 Token contract for Ripe DAO's governance token  ║
#     ╚════════════════════════════════════════════════════════╝
#
#     Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
#     Ripe Foundation (C) 2025

# @version 0.4.3

exports: token.__interface__
initializes: token

from contracts.tokens.modules import Erc20Token as token

interface RipeHq:
    def canMintRipe(_addr: address) -> bool: view


@deploy
def __init__(
    _ripeHq: address,
    _initialGov: address,
    _minHqTimeLock: uint256,
    _maxHqTimeLock: uint256,
    _initialSupply: uint256,
    _initialSupplyRecipient: address,
):
    token.__init__("Ripe DAO Governance Token", "RIPE", 18, _ripeHq, _initialGov, _minHqTimeLock, _maxHqTimeLock, _initialSupply, _initialSupplyRecipient)


###########
# Minting #
###########


@external
def mint(_recipient: address, _amount: uint256) -> bool:
    assert staticcall RipeHq(token.ripeHq).canMintRipe(msg.sender) # dev: cannot mint
    return token._mint(_recipient, _amount)
