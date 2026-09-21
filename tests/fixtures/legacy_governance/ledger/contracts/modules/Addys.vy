# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2025

# @version 0.4.3

interface RipeHq:
    def isValidAddr(_addr: address) -> bool: view
    def getAddr(_regId: uint256) -> address: view

interface Switchboard:
    def isSwitchboardAddr(_addr: address) -> bool: view

interface VaultBook:
    def isVaultBookAddr(_addr: address) -> bool: view

struct Addys:
    hq: address
    greenToken: address
    savingsGreen: address
    ripeToken: address
    ledger: address
    missionControl: address
    switchboard: address
    priceDesk: address
    vaultBook: address
    auctionHouse: address
    auctionHouseNft: address
    boardroom: address
    bondRoom: address
    creditEngine: address
    endaoment: address
    humanResources: address
    lootbox: address
    teller: address

# hq
RIPE_HQ_FOR_ADDYS: immutable(address)

# core addys
GREEN_TOKEN_ID: constant(uint256) = 1
SAVINGS_GREEN_ID: constant(uint256) = 2
RIPE_TOKEN_ID: constant(uint256) = 3
LEDGER_ID: constant(uint256) = 4
MISSION_CONTROL_ID: constant(uint256) = 5
SWITCHBOARD_ID: constant(uint256) = 6
PRICE_DESK_ID: constant(uint256) = 7
VAULT_BOOK_ID: constant(uint256) = 8
AUCTION_HOUSE_ID: constant(uint256) = 9
AUCTION_HOUSE_NFT_ID: constant(uint256) = 10
BOARDROOM_ID: constant(uint256) = 11
BOND_ROOM_ID: constant(uint256) = 12
CREDIT_ENGINE_ID: constant(uint256) = 13
ENDAOMENT_ID: constant(uint256) = 14
HUMAN_RESOURCES_ID: constant(uint256) = 15
LOOTBOX_ID: constant(uint256) = 16
TELLER_ID: constant(uint256) = 17


@deploy
def __init__(_ripeHq: address):
    assert _ripeHq != empty(address) # dev: invalid ripe hq
    RIPE_HQ_FOR_ADDYS = _ripeHq


########
# Core #
########


@view
@external
def getAddys() -> Addys:
    return self._generateAddys()


@view
@internal
def _getAddys(_addys: Addys = empty(Addys)) -> Addys:
    if _addys.hq != empty(address):
        return _addys
    return self._generateAddys()


@view
@internal
def _generateAddys() -> Addys:
    hq: address = RIPE_HQ_FOR_ADDYS
    return Addys(
        hq=hq,
        greenToken=staticcall RipeHq(hq).getAddr(GREEN_TOKEN_ID),
        savingsGreen=staticcall RipeHq(hq).getAddr(SAVINGS_GREEN_ID),
        ripeToken=staticcall RipeHq(hq).getAddr(RIPE_TOKEN_ID),
        ledger=staticcall RipeHq(hq).getAddr(LEDGER_ID),
        missionControl=staticcall RipeHq(hq).getAddr(MISSION_CONTROL_ID),
        switchboard=staticcall RipeHq(hq).getAddr(SWITCHBOARD_ID),
        priceDesk=staticcall RipeHq(hq).getAddr(PRICE_DESK_ID),
        vaultBook=staticcall RipeHq(hq).getAddr(VAULT_BOOK_ID),
        auctionHouse=staticcall RipeHq(hq).getAddr(AUCTION_HOUSE_ID),
        auctionHouseNft=staticcall RipeHq(hq).getAddr(AUCTION_HOUSE_NFT_ID),
        boardroom=staticcall RipeHq(hq).getAddr(BOARDROOM_ID),
        bondRoom=staticcall RipeHq(hq).getAddr(BOND_ROOM_ID),
        creditEngine=staticcall RipeHq(hq).getAddr(CREDIT_ENGINE_ID),
        endaoment=staticcall RipeHq(hq).getAddr(ENDAOMENT_ID),
        humanResources=staticcall RipeHq(hq).getAddr(HUMAN_RESOURCES_ID),
        lootbox=staticcall RipeHq(hq).getAddr(LOOTBOX_ID),
        teller=staticcall RipeHq(hq).getAddr(TELLER_ID),
    )


##########
# Tokens #
##########


@view
@internal
def _getGreenToken() -> address:
    return staticcall RipeHq(RIPE_HQ_FOR_ADDYS).getAddr(GREEN_TOKEN_ID)


@view
@internal
def _getSavingsGreen() -> address:
    return staticcall RipeHq(RIPE_HQ_FOR_ADDYS).getAddr(SAVINGS_GREEN_ID)


@view
@internal
def _getRipeToken() -> address:
    return staticcall RipeHq(RIPE_HQ_FOR_ADDYS).getAddr(RIPE_TOKEN_ID)


###########
# Helpers #
###########


# ripe hq


@view
@external
def getRipeHq() -> address:
    return self._getRipeHq()


@view
@internal
def _getRipeHq() -> address:
    return RIPE_HQ_FOR_ADDYS


# utils


@view
@internal
def _isValidRipeAddr(_addr: address) -> bool:
    hq: address = RIPE_HQ_FOR_ADDYS
    
    # core departments
    if staticcall RipeHq(hq).isValidAddr(_addr):
        return True

    # vault book
    vaultBook: address = staticcall RipeHq(hq).getAddr(VAULT_BOOK_ID)
    if vaultBook != empty(address) and staticcall VaultBook(vaultBook).isVaultBookAddr(_addr):
        return True

    # switchboard config
    switchboard: address = staticcall RipeHq(hq).getAddr(SWITCHBOARD_ID)
    if switchboard != empty(address) and staticcall Switchboard(switchboard).isSwitchboardAddr(_addr):
        return True

    return False


@view
@internal
def _isSwitchboardAddr(_addr: address) -> bool:
    switchboard: address = staticcall RipeHq(RIPE_HQ_FOR_ADDYS).getAddr(SWITCHBOARD_ID)
    if switchboard == empty(address):
        return False
    return staticcall Switchboard(switchboard).isSwitchboardAddr(_addr)


###############
# Departments #
###############


# ledger


@view
@internal
def _getLedgerId() -> uint256:
    return LEDGER_ID


@view
@internal
def _getLedgerAddr() -> address:
    return staticcall RipeHq(RIPE_HQ_FOR_ADDYS).getAddr(LEDGER_ID)


# mission control


@view
@internal
def _getMissionControlId() -> uint256:
    return MISSION_CONTROL_ID


@view
@internal
def _getMissionControlAddr() -> address:
    return staticcall RipeHq(RIPE_HQ_FOR_ADDYS).getAddr(MISSION_CONTROL_ID)


# switchboard


@view
@internal
def _getSwitchboardId() -> uint256:
    return SWITCHBOARD_ID


@view
@internal
def _getSwitchboardAddr() -> address:
    return staticcall RipeHq(RIPE_HQ_FOR_ADDYS).getAddr(SWITCHBOARD_ID)


# price desk


@view
@internal
def _getPriceDeskId() -> uint256:
    return PRICE_DESK_ID


@view
@internal
def _getPriceDeskAddr() -> address:
    return staticcall RipeHq(RIPE_HQ_FOR_ADDYS).getAddr(PRICE_DESK_ID)


# vault book


@view
@internal
def _getVaultBookId() -> uint256:
    return VAULT_BOOK_ID


@view
@internal
def _getVaultBookAddr() -> address:
    return staticcall RipeHq(RIPE_HQ_FOR_ADDYS).getAddr(VAULT_BOOK_ID)


# auction house


@view
@internal
def _getAuctionHouseId() -> uint256:
    return AUCTION_HOUSE_ID


@view
@internal
def _getAuctionHouseAddr() -> address:
    return staticcall RipeHq(RIPE_HQ_FOR_ADDYS).getAddr(AUCTION_HOUSE_ID)


# auction house nft


@view
@internal
def _getAuctionHouseNftId() -> uint256:
    return AUCTION_HOUSE_NFT_ID


@view
@internal
def _getAuctionHouseNftAddr() -> address:
    return staticcall RipeHq(RIPE_HQ_FOR_ADDYS).getAddr(AUCTION_HOUSE_NFT_ID)


# boardroom


@view
@internal
def _getBoardroomId() -> uint256:
    return BOARDROOM_ID


@view
@internal
def _getBoardroomAddr() -> address:
    return staticcall RipeHq(RIPE_HQ_FOR_ADDYS).getAddr(BOARDROOM_ID)


# bond room


@view
@internal
def _getBondRoomId() -> uint256:
    return BOND_ROOM_ID


@view
@internal
def _getBondRoomAddr() -> address:
    return staticcall RipeHq(RIPE_HQ_FOR_ADDYS).getAddr(BOND_ROOM_ID)


# credit engine


@view
@internal
def _getCreditEngineId() -> uint256:
    return CREDIT_ENGINE_ID


@view
@internal
def _getCreditEngineAddr() -> address:
    return staticcall RipeHq(RIPE_HQ_FOR_ADDYS).getAddr(CREDIT_ENGINE_ID)


# endaoment


@view
@internal
def _getEndaomentId() -> uint256:
    return ENDAOMENT_ID


@view
@internal
def _getEndaomentAddr() -> address:
    return staticcall RipeHq(RIPE_HQ_FOR_ADDYS).getAddr(ENDAOMENT_ID)


# human resources


@view
@internal
def _getHumanResourcesId() -> uint256:
    return HUMAN_RESOURCES_ID


@view
@internal
def _getHumanResourcesAddr() -> address:
    return staticcall RipeHq(RIPE_HQ_FOR_ADDYS).getAddr(HUMAN_RESOURCES_ID)


# lootbox


@view
@internal
def _getLootboxId() -> uint256:
    return LOOTBOX_ID


@view
@internal
def _getLootboxAddr() -> address:
    return staticcall RipeHq(RIPE_HQ_FOR_ADDYS).getAddr(LOOTBOX_ID)


# teller


@view
@internal
def _getTellerId() -> uint256:
    return TELLER_ID


@view
@internal
def _getTellerAddr() -> address:
    return staticcall RipeHq(RIPE_HQ_FOR_ADDYS).getAddr(TELLER_ID)
