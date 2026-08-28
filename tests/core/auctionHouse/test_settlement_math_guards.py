import boa
import pytest

from constants import EIGHTEEN_DECIMALS, HUNDRED_PERCENT, MAX_UINT256
from conf_utils import filter_logs
from tests.core.auctionHouse.test_ah_poison_price import (
    _fund_alice,
    _register_vault,
)


PRICE_BUMP_VAULT_SOURCE = """
# @version 0.4.3

from ethereum.ercs import IERC20

interface MutablePriceSource:
    def setPrice(_asset: address, _price: uint256): nonpayable

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

struct VaultDataOnDeposit:
    hasPosition: bool
    numAssets: uint256
    userBalance: uint256
    totalBalance: uint256

userBalances: HashMap[address, HashMap[address, uint256]]
totalBalances: HashMap[address, uint256]
userAssets: HashMap[address, HashMap[uint256, address]]
indexOfUserAsset: HashMap[address, HashMap[address, uint256]]
numUserAssets: public(HashMap[address, uint256])
priceSource: address
bumpPrice: uint256

@external
def setPriceBump(_priceSource: address, _bumpPrice: uint256):
    self.priceSource = _priceSource
    self.bumpPrice = _bumpPrice

@internal
def _register(_user: address, _asset: address):
    if self.indexOfUserAsset[_user][_asset] != 0:
        return
    aid: uint256 = self.numUserAssets[_user]
    if aid == 0:
        aid = 1
    self.userAssets[_user][aid] = _asset
    self.indexOfUserAsset[_user][_asset] = aid
    self.numUserAssets[_user] = aid + 1

@external
def depositTokensInVault(
    _user: address,
    _asset: address,
    _amount: uint256,
    _a: Addys = empty(Addys),
) -> uint256:
    self._register(_user, _asset)
    self.userBalances[_user][_asset] += _amount
    self.totalBalances[_asset] += _amount
    return _amount

@internal
def _outflow(_user: address, _asset: address, _amount: uint256) -> (uint256, bool):
    available: uint256 = self.userBalances[_user][_asset]
    sendAmount: uint256 = min(_amount, available)
    if sendAmount == 0:
        return 0, available == 0
    self.userBalances[_user][_asset] = available - sendAmount
    self.totalBalances[_asset] -= sendAmount
    return sendAmount, self.userBalances[_user][_asset] == 0

@internal
def _bump(_asset: address):
    if self.priceSource != empty(address):
        extcall MutablePriceSource(self.priceSource).setPrice(_asset, self.bumpPrice)

@external
def withdrawTokensFromVault(
    _user: address,
    _asset: address,
    _amount: uint256,
    _recipient: address,
    _a: Addys = empty(Addys),
) -> (uint256, bool):
    sendAmount: uint256 = 0
    depleted: bool = False
    sendAmount, depleted = self._outflow(_user, _asset, _amount)
    if sendAmount != 0:
        assert extcall IERC20(_asset).transfer(_recipient, sendAmount, default_return_value=True)
        self._bump(_asset)
    return sendAmount, depleted

@external
def transferBalanceWithinVault(
    _asset: address,
    _fromUser: address,
    _toUser: address,
    _transferAmount: uint256,
    _a: Addys = empty(Addys),
) -> (uint256, bool):
    sendAmount: uint256 = 0
    depleted: bool = False
    sendAmount, depleted = self._outflow(_fromUser, _asset, _transferAmount)
    if sendAmount != 0:
        self.userBalances[_toUser][_asset] += sendAmount
        self.totalBalances[_asset] += sendAmount
        self._register(_toUser, _asset)
        self._bump(_asset)
    return sendAmount, depleted

@view
@external
def getVaultDataOnDeposit(_user: address, _asset: address) -> VaultDataOnDeposit:
    n: uint256 = self.numUserAssets[_user]
    count: uint256 = 0
    if n != 0:
        count = n - 1
    return VaultDataOnDeposit(
        hasPosition=self.indexOfUserAsset[_user][_asset] != 0,
        numAssets=count,
        userBalance=self.userBalances[_user][_asset],
        totalBalance=self.totalBalances[_asset],
    )

@view
@external
def getUserLootBoxShare(_user: address, _asset: address) -> uint256:
    return self.userBalances[_user][_asset]

@view
@external
def getUserAssetAndAmountAtIndex(_user: address, _index: uint256) -> (address, uint256):
    asset: address = self.userAssets[_user][_index]
    return asset, self.userBalances[_user][asset]

@view
@external
def getUserAssetAtIndexAndHasBalance(_user: address, _index: uint256) -> (address, bool):
    asset: address = self.userAssets[_user][_index]
    return asset, self.userBalances[_user][asset] != 0

@view
@external
def getTotalAmountForUser(_user: address, _asset: address) -> uint256:
    return self.userBalances[_user][_asset]

@view
@external
def getTotalAmountForVault(_asset: address) -> uint256:
    return self.totalBalances[_asset]

@view
@external
def isPaused() -> bool:
    return False
"""


def _old_target_repay(debt_amount, collateral_value, target_ltv):
    collateral_adjusted = collateral_value * target_ltv // HUNDRED_PERCENT
    if debt_amount <= collateral_adjusted:
        return debt_amount
    return min(
        (debt_amount - collateral_adjusted)
        * HUNDRED_PERCENT
        // (HUNDRED_PERCENT - target_ltv),
        debt_amount,
    )


@pytest.mark.parametrize(
    "debt,collateral,target_ltv,expected",
    [
        (
            100 * EIGHTEEN_DECIMALS,
            140 * EIGHTEEN_DECIMALS,
            50_00,
            60 * EIGHTEEN_DECIMALS,
        ),
        # This supplied 99.99% vector reaches the existing collateral branch.
        (
            100 * EIGHTEEN_DECIMALS,
            140 * EIGHTEEN_DECIMALS,
            99_99,
            100 * EIGHTEEN_DECIMALS,
        ),
        (
            100 * EIGHTEEN_DECIMALS,
            140 * EIGHTEEN_DECIMALS,
            100_00,
            100 * EIGHTEEN_DECIMALS,
        ),
        (
            100 * EIGHTEEN_DECIMALS,
            140 * EIGHTEEN_DECIMALS,
            100_01,
            100 * EIGHTEEN_DECIMALS,
        ),
        (
            100 * EIGHTEEN_DECIMALS,
            50 * EIGHTEEN_DECIMALS,
            100_00,
            100 * EIGHTEEN_DECIMALS,
        ),
        (
            100 * EIGHTEEN_DECIMALS,
            200 * EIGHTEEN_DECIMALS,
            100_00,
            100 * EIGHTEEN_DECIMALS,
        ),
        (0, 100 * EIGHTEEN_DECIMALS, 100_00, 0),
    ],
)
def test_c11_calc_target_repay_amount_boundaries(
    auction_house,
    debt,
    collateral,
    target_ltv,
    expected,
):
    assert auction_house.calcTargetRepayAmount(
        debt,
        collateral,
        target_ltv,
    ) == expected


def test_c11_9999_target_still_uses_existing_formula(auction_house):
    debt = 100 * EIGHTEEN_DECIMALS
    collateral = debt + EIGHTEEN_DECIMALS // 10_000
    expected = _old_target_repay(debt, collateral, 99_99)
    assert expected < debt
    assert auction_house.calcTargetRepayAmount(debt, collateral, 99_99) == expected


def test_c12_auction_forward_overshoot_settles_at_target_cap(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    mock_price_source,
    teller,
    credit_engine,
    green_token,
    whale,
    vault_book,
    governance,
    price_desk,
):
    with boa.env.anchor():
        vault = boa.loads(PRICE_BUMP_VAULT_SOURCE, name="price_bump_vault")
        vault_id = _register_vault(vault_book, governance, vault, "price bump vault")
        token = boa.load(
            "contracts/mock/MockErc20.vy",
            governance,
            "Forward Overshoot",
            "FOVR",
            18,
            1_000_000_000,
            name="forward_overshoot_token",
        )
        borrower = boa.env.generate_address("overshoot-borrower")
        buyer = boa.env.generate_address("overshoot-buyer")
        keeper = boa.env.generate_address("overshoot-keeper")

        setGeneralConfig(_perUserMaxVaults=20)
        setGeneralDebtConfig(_ltvPaybackBuffer=0)
        setAssetConfig(
            token,
            _vaultIds=[vault_id],
            _debtTerms=createDebtTerms(
                _liqThreshold=80_00,
                _liqFee=0,
                _ltv=50_00,
                _borrowRate=0,
            ),
            _shouldBurnAsPayment=False,
            _shouldTransferToEndaoment=False,
            _shouldSwapInStabPools=False,
            _shouldAuctionInstantly=True,
        )
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
        mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)

        collateral = 200 * EIGHTEEN_DECIMALS
        debt = 100 * EIGHTEEN_DECIMALS
        token.mint(borrower, collateral, sender=governance.address)
        token.approve(teller, collateral, sender=borrower)
        teller.deposit(token, collateral, borrower, vault, sender=borrower)
        teller.borrow(debt, borrower, False, sender=borrower)

        mock_price_source.setPrice(token, 12 * EIGHTEEN_DECIMALS // 100)
        assert credit_engine.canLiquidateUser(borrower)
        teller.liquidateUser(borrower, False, sender=keeper)

        target = debt
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
        max_asset_amount = price_desk.getAssetAmount(token, target, True)
        assert max_asset_amount == target
        vault.setPriceBump(mock_price_source, 2 * EIGHTEEN_DECIMALS)

        buyer_green_before = _fund_alice(
            green_token,
            whale,
            teller,
            buyer,
            target,
        )
        buyer_token_before = token.balanceOf(buyer)
        borrower_debt_before = credit_engine.getUserDebtAmount(borrower)
        borrower_collateral_before = vault.getTotalAmountForUser(borrower, token)

        green_spent = teller.buyManyFungibleAuctions(
            [(borrower, vault_id, token.address, MAX_UINT256)],
            target,
            False,
            False,
            False,
            buyer,
            sender=buyer,
        )

        log = filter_logs(teller, "FungAuctionPurchased")[0]
        raw_forward_value = price_desk.getUsdValue(
            token,
            log.collateralAmountSent,
            True,
        )
        assert raw_forward_value > target + 1
        assert log.collateralAmountSent == max_asset_amount
        assert log.collateralUsdValueSent == target
        assert log.greenSpent == target
        assert green_spent == target
        assert token.balanceOf(buyer) == buyer_token_before + max_asset_amount
        assert green_token.balanceOf(buyer) == buyer_green_before - target
        assert credit_engine.getUserDebtAmount(borrower) == (
            borrower_debt_before - green_spent
        )
        assert vault.getTotalAmountForUser(borrower, token) == (
            borrower_collateral_before - max_asset_amount
        )
