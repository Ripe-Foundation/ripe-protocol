# @version 0.4.1

interface RipeHq:
    def isValidAddyAddr(_addr: address) -> bool: view
    def getAddy(_addyId: uint256) -> address: view
    def governance() -> address: view
    def greenToken() -> address: view
    def ripeToken() -> address: view

interface VaultBook:
    def getStakedGreenData() -> (uint256, address): view
    def getStakedRipeData() -> (uint256, address): view

struct Addys:
    hq: address
    governance: address
    greenToken: address
    ripeToken: address
    priceDesk: address
    vaultBook: address
    auctionHouse: address
    controlRoom: address
    creditEngine: address
    ledger: address
    lootbox: address
    teller: address
    sGreenVaultAddr: address
    sGreenVaultId: uint256
    sRipeVaultAddr: address
    sRipeVaultId: uint256

# hq
RIPE_HQ: immutable(address)

# core addys
PRICE_DESK_ID: constant(uint256) = 1
VAULT_BOOK_ID: constant(uint256) = 2
AUCTION_HOUSE_ID: constant(uint256) = 3
CONTROL_ROOM_ID: constant(uint256) = 4
CREDIT_ENGINE_ID: constant(uint256) = 5
LEDGER_ID: constant(uint256) = 6
LOOTBOX_ID: constant(uint256) = 7
TELLER_ID: constant(uint256) = 8


@deploy
def __init__(_ripeHq: address):
    assert _ripeHq != empty(address) # dev: invalid ripe hq
    RIPE_HQ = _ripeHq


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
    hq: address = RIPE_HQ
    vaultBook: address = staticcall RipeHq(hq).getAddy(VAULT_BOOK_ID)

    # staked green
    sGreenVaultId: uint256 = 0
    sGreenVaultAddr: address = empty(address)
    sGreenVaultId, sGreenVaultAddr = staticcall VaultBook(vaultBook).getStakedGreenData()

    # staked ripe
    sRipeVaultId: uint256 = 0
    sRipeVaultAddr: address = empty(address)
    sRipeVaultId, sRipeVaultAddr = staticcall VaultBook(vaultBook).getStakedRipeData()

    return Addys(
        hq=hq,
        governance=staticcall RipeHq(hq).governance(),
        greenToken=staticcall RipeHq(hq).greenToken(),
        ripeToken=staticcall RipeHq(hq).ripeToken(),
        priceDesk=staticcall RipeHq(hq).getAddy(PRICE_DESK_ID),
        vaultBook=vaultBook,
        auctionHouse=staticcall RipeHq(hq).getAddy(AUCTION_HOUSE_ID),
        controlRoom=staticcall RipeHq(hq).getAddy(CONTROL_ROOM_ID),
        creditEngine=staticcall RipeHq(hq).getAddy(CREDIT_ENGINE_ID),
        ledger=staticcall RipeHq(hq).getAddy(LEDGER_ID),
        lootbox=staticcall RipeHq(hq).getAddy(LOOTBOX_ID),
        teller=staticcall RipeHq(hq).getAddy(TELLER_ID),
        sGreenVaultAddr=sGreenVaultAddr,
        sGreenVaultId=sGreenVaultId,
        sRipeVaultAddr=sRipeVaultAddr,
        sRipeVaultId=sRipeVaultId,
    )


###########
# Helpers #
###########


@view
@internal
def _getRipeHq() -> address:
    return RIPE_HQ


@view
@internal
def _isValidRipeHqAddy(_addr: address) -> bool:
    return staticcall RipeHq(RIPE_HQ).isValidAddyAddr(_addr)


@view
@internal
def _getGovernance() -> address:
    return staticcall RipeHq(RIPE_HQ).governance()


# tokens


@view
@internal
def _getGreenToken() -> address:
    return staticcall RipeHq(RIPE_HQ).greenToken()


@view
@internal
def _getRipeToken() -> address:
    return staticcall RipeHq(RIPE_HQ).ripeToken()


# price desk


@view
@internal
def _getPriceDeskId() -> uint256:
    return PRICE_DESK_ID


@view
@internal
def _getPriceDeskAddr() -> address:
    return staticcall RipeHq(RIPE_HQ).getAddy(PRICE_DESK_ID)


# vault book


@view
@internal
def _getVaultBookId() -> uint256:
    return VAULT_BOOK_ID


@view
@internal
def _getVaultBookAddr() -> address:
    return staticcall RipeHq(RIPE_HQ).getAddy(VAULT_BOOK_ID)


# auction house


@view
@internal
def _getAuctionHouseId() -> uint256:
    return AUCTION_HOUSE_ID


@view
@internal
def _getAuctionHouseAddr() -> address:
    return staticcall RipeHq(RIPE_HQ).getAddy(AUCTION_HOUSE_ID)


# control room


@view
@internal
def _getControlRoomId() -> uint256:
    return CONTROL_ROOM_ID


@view
@internal
def _getControlRoomAddr() -> address:
    return staticcall RipeHq(RIPE_HQ).getAddy(CONTROL_ROOM_ID)


# credit engine


@view
@internal
def _getCreditEngineId() -> uint256:
    return CREDIT_ENGINE_ID


@view
@internal
def _getCreditEngineAddr() -> address:
    return staticcall RipeHq(RIPE_HQ).getAddy(CREDIT_ENGINE_ID)


# ledger


@view
@internal
def _getLedgerId() -> uint256:
    return LEDGER_ID


@view
@internal
def _getLedgerAddr() -> address:
    return staticcall RipeHq(RIPE_HQ).getAddy(LEDGER_ID)


# lootbox


@view
@internal
def _getLootboxId() -> uint256:
    return LOOTBOX_ID


@view
@internal
def _getLootboxAddr() -> address:
    return staticcall RipeHq(RIPE_HQ).getAddy(LOOTBOX_ID)


# teller


@view
@internal
def _getTellerId() -> uint256:
    return TELLER_ID


@view
@internal
def _getTellerAddr() -> address:
    return staticcall RipeHq(RIPE_HQ).getAddy(TELLER_ID)