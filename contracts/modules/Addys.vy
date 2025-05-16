# @version 0.4.1

interface RipeHq:
    def isValidAddr(_addr: address) -> bool: view
    def getAddr(_regId: uint256) -> address: view

struct Addys:
    hq: address
    greenToken: address
    ripeToken: address
    priceDesk: address
    vaultBook: address
    auctionHouse: address
    auctionHouseNft: address
    bondRoom: address
    controlRoom: address
    creditEngine: address
    endaoment: address
    ledger: address
    lootbox: address
    teller: address

# hq
RIPE_HQ_FOR_ADDYS: immutable(address)

# core addys
GREEN_TOKEN_ID: constant(uint256) = 1
RIPE_TOKEN_ID: constant(uint256) = 2
PRICE_DESK_ID: constant(uint256) = 3
VAULT_BOOK_ID: constant(uint256) = 4
AUCTION_HOUSE_ID: constant(uint256) = 5
AUCTION_HOUSE_NFT_ID: constant(uint256) = 6
BOND_ROOM_ID: constant(uint256) = 7
CONTROL_ROOM_ID: constant(uint256) = 8
CREDIT_ENGINE_ID: constant(uint256) = 9
ENDAOMENT_ID: constant(uint256) = 10
LEDGER_ID: constant(uint256) = 11
LOOTBOX_ID: constant(uint256) = 12
TELLER_ID: constant(uint256) = 13


@deploy
def __init__(_ripeHq: address):
    assert _ripeHq != empty(address) # dev: invalid ripe hq
    RIPE_HQ_FOR_ADDYS = _ripeHq


########
# Core #
########


@view
@internal
def _getAddys(_addys: Addys = empty(Addys)) -> Addys:
    if _addys.hq != empty(address):
        return _addys
    return self._generateAddys()


@view
@external
def getAddys() -> Addys:
    return self._generateAddys()


@view
@internal
def _generateAddys() -> Addys:
    hq: address = RIPE_HQ_FOR_ADDYS
    return Addys(
        hq=hq,
        greenToken=staticcall RipeHq(hq).getAddr(GREEN_TOKEN_ID),
        ripeToken=staticcall RipeHq(hq).getAddr(RIPE_TOKEN_ID),
        priceDesk=staticcall RipeHq(hq).getAddr(PRICE_DESK_ID),
        vaultBook=staticcall RipeHq(hq).getAddr(VAULT_BOOK_ID),
        auctionHouse=staticcall RipeHq(hq).getAddr(AUCTION_HOUSE_ID),
        auctionHouseNft=staticcall RipeHq(hq).getAddr(AUCTION_HOUSE_NFT_ID),
        bondRoom=staticcall RipeHq(hq).getAddr(BOND_ROOM_ID),
        controlRoom=staticcall RipeHq(hq).getAddr(CONTROL_ROOM_ID),
        creditEngine=staticcall RipeHq(hq).getAddr(CREDIT_ENGINE_ID),
        endaoment=staticcall RipeHq(hq).getAddr(ENDAOMENT_ID),
        ledger=staticcall RipeHq(hq).getAddr(LEDGER_ID),
        lootbox=staticcall RipeHq(hq).getAddr(LOOTBOX_ID),
        teller=staticcall RipeHq(hq).getAddr(TELLER_ID),
    )


###########
# Helpers #
###########


@view
@internal
def _getRipeHq() -> address:
    return RIPE_HQ_FOR_ADDYS


@view
@internal
def _isValidRipeHqAddr(_addr: address) -> bool:
    return staticcall RipeHq(RIPE_HQ_FOR_ADDYS).isValidAddr(_addr)


# tokens


@view
@internal
def _getGreenToken() -> address:
    return staticcall RipeHq(RIPE_HQ_FOR_ADDYS).getAddr(GREEN_TOKEN_ID)


@view
@internal
def _getRipeToken() -> address:
    return staticcall RipeHq(RIPE_HQ_FOR_ADDYS).getAddr(RIPE_TOKEN_ID)


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


# bond room


@view
@internal
def _getBondRoomId() -> uint256:
    return BOND_ROOM_ID


@view
@internal
def _getBondRoomAddr() -> address:
    return staticcall RipeHq(RIPE_HQ_FOR_ADDYS).getAddr(BOND_ROOM_ID)


# control room


@view
@internal
def _getControlRoomId() -> uint256:
    return CONTROL_ROOM_ID


@view
@internal
def _getControlRoomAddr() -> address:
    return staticcall RipeHq(RIPE_HQ_FOR_ADDYS).getAddr(CONTROL_ROOM_ID)


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


# ledger


@view
@internal
def _getLedgerId() -> uint256:
    return LEDGER_ID


@view
@internal
def _getLedgerAddr() -> address:
    return staticcall RipeHq(RIPE_HQ_FOR_ADDYS).getAddr(LEDGER_ID)


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