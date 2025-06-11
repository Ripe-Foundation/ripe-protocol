import pytest
from constants import HUNDRED_PERCENT, MAX_UINT256, ZERO_ADDRESS


def filter_logs(contract, event_name, _strict=False):
    return [e for e in contract.get_logs(strict=_strict) if type(e).__name__ == event_name]


@pytest.fixture(scope="session")
def _test():
    def _test(_expectedValue, _actualValue, _buffer=50):
        if _expectedValue == 0 or _actualValue == 0:
            assert _expectedValue == _actualValue
        else:
            buffer = _expectedValue * _buffer // HUNDRED_PERCENT
            assert _expectedValue + buffer >= _actualValue >= _expectedValue - buffer

    yield _test


@pytest.fixture(scope="session")
def performDeposit(teller, simple_erc20_vault, alpha_token, alpha_token_whale):
    def performDeposit(
        _user,
        _amount,
        _token = alpha_token,
        _tokenWhale = alpha_token_whale,
        _vault = simple_erc20_vault,
    ):
        _token.transfer(_user, _amount, sender=_tokenWhale)
        _token.approve(teller.address, _amount, sender=_user)
        teller.deposit(_token, _amount, _user, _vault, sender=_user)
    yield performDeposit


#################
# Global Config #
#################


@pytest.fixture(scope="session")
def setGeneralConfig(mission_control, switchboard_alpha):
    def setGeneralConfig(
        _perUserMaxVaults = 5,
        _perUserMaxAssetsPerVault = 10,
        _priceStaleTime = 0,
        _canDeposit = True,
        _canWithdraw = True,
        _canBorrow = True,
        _canRepay = True,
        _canClaimLoot = True,
        _canLiquidate = True,
        _canRedeemCollateral = True,
        _canRedeemInStabPool = True,
        _canBuyInAuction = True,
        _canClaimInStabPool = True,
    ):
        gen_config = (
            _perUserMaxVaults,
            _perUserMaxAssetsPerVault,
            _priceStaleTime,
            _canDeposit,
            _canWithdraw,
            _canBorrow,
            _canRepay,
            _canClaimLoot,
            _canLiquidate,
            _canRedeemCollateral,
            _canRedeemInStabPool,
            _canBuyInAuction,
            _canClaimInStabPool,
        )
        mission_control.setGeneralConfig(gen_config, sender=switchboard_alpha.address)
    yield setGeneralConfig


@pytest.fixture(scope="session")
def setGeneralDebtConfig(mission_control, switchboard_alpha, createAuctionParams):
    def setGeneralDebtConfig(
        _perUserDebtLimit = MAX_UINT256,
        _globalDebtLimit = MAX_UINT256,
        _minDebtAmount = 0,
        _numAllowedBorrowers = MAX_UINT256,
        _maxBorrowPerInterval = MAX_UINT256,
        _numBlocksPerInterval = 1000,
        _minDynamicRateBoost = 100_00,
        _maxDynamicRateBoost = 1000_00,
        _increasePerDangerBlock = 10,
        _maxBorrowRate = 100_00,
        _keeperFeeRatio = 0,
        _minKeeperFee = 0,
        _isDaowryEnabled = False,
        _ltvPaybackBuffer = 1_00,
        _genAuctionParams = createAuctionParams(),
    ):
        debt_config = (
            _perUserDebtLimit,
            _globalDebtLimit,
            _minDebtAmount,
            _numAllowedBorrowers,
            _maxBorrowPerInterval,
            _numBlocksPerInterval,
            _minDynamicRateBoost,
            _maxDynamicRateBoost,
            _increasePerDangerBlock,
            _maxBorrowRate,
            _keeperFeeRatio,
            _minKeeperFee,
            _isDaowryEnabled,
            _ltvPaybackBuffer,
            _genAuctionParams,
        )
        mission_control.setGeneralDebtConfig(debt_config, sender=switchboard_alpha.address)
    yield setGeneralDebtConfig


@pytest.fixture(scope="session")
def createAuctionParams():
    def createAuctionParams(
        _startDiscount = 0,
        _maxDiscount = 50_00,
        _delay = 0,
        _duration = 1000,
    ):
        return (
            True,
            _startDiscount,
            _maxDiscount,
            _delay,
            _duration,
        )
    yield createAuctionParams


################
# Asset Config #
################


@pytest.fixture(scope="session")
def setAssetConfig(mission_control, switchboard_bravo, createDebtTerms):
    def setAssetConfig(
        _asset,
        _vaultIds = [3], # default simple erc20 vault
        _stakersPointsAlloc = 10,
        _voterPointsAlloc = 10,
        _perUserDepositLimit = MAX_UINT256,
        _globalDepositLimit = MAX_UINT256,
        _debtTerms = createDebtTerms(),
        _shouldBurnAsPayment = False,
        _shouldTransferToEndaoment = False,
        _shouldSwapInStabPools = True,
        _shouldAuctionInstantly = True,
        _canDeposit = True,
        _canWithdraw = True,
        _canRedeemCollateral = True,
        _canRedeemInStabPool = True,
        _canBuyInAuction = True,
        _canClaimInStabPool = True,
        _specialStabPoolId = 0,
        _customAuctionParams = (False, 0, 0, 0, 0),
        _whitelist = ZERO_ADDRESS,
        _isNft = False,
    ):
        asset_config = (
            _vaultIds,
            _stakersPointsAlloc,
            _voterPointsAlloc,
            _perUserDepositLimit,
            _globalDepositLimit,
            _debtTerms,
            _shouldBurnAsPayment,
            _shouldTransferToEndaoment,
            _shouldSwapInStabPools,
            _shouldAuctionInstantly,
            _canDeposit,
            _canWithdraw,
            _canRedeemCollateral,
            _canRedeemInStabPool,
            _canBuyInAuction,
            _canClaimInStabPool,
            _specialStabPoolId,
            _customAuctionParams,
            _whitelist,
            _isNft,
        )
        mission_control.setAssetConfig(_asset, asset_config, sender=switchboard_bravo.address)
    yield setAssetConfig


@pytest.fixture(scope="session")
def createDebtTerms():
    def createDebtTerms(
        _ltv = 50_00,
        _redemptionThreshold = 60_00,
        _liqThreshold = 70_00,
        _liqFee = 10_00,
        _borrowRate = 5_00,
        _daowry = 0,
    ):
        return (
            _ltv,
            _redemptionThreshold,
            _liqThreshold,
            _liqFee,
            _borrowRate,
            _daowry,
        )
    yield createDebtTerms


####################
# Rewards / Points #
####################


@pytest.fixture(scope="session")
def setRipeRewardsConfig(mission_control, switchboard_alpha):
    def setRipeRewardsConfig(
        _arePointsEnabled = True,
        _ripePerBlock = 10,
        _borrowersAlloc = 25_00,
        _stakersAlloc = 25_00,
        _votersAlloc = 25_00,
        _genDepositorsAlloc = 25_00,
        _autoStakeRatio = 0,
        _autoStakeDurationRatio = 0,
    ):
        config = (
            _arePointsEnabled,
            _ripePerBlock,
            _borrowersAlloc,
            _stakersAlloc,
            _votersAlloc,
            _genDepositorsAlloc,
            _autoStakeRatio,
            _autoStakeDurationRatio,
        )
        mission_control.setRipeRewardsConfig(config, sender=switchboard_alpha.address)
    yield setRipeRewardsConfig


###############
# User Config #
###############


@pytest.fixture(scope="session")
def setUserConfig(mission_control):
    def setUserConfig(
        _user,
        _canAnyoneDeposit = True,
        _canAnyoneRepayDebt = True,
        _canAnyoneBondForUser = False,
    ):
        mission_control.setUserConfig(_canAnyoneDeposit, _canAnyoneRepayDebt, _canAnyoneBondForUser, sender=_user)
    yield setUserConfig


@pytest.fixture(scope="session")
def setUserDelegation(mission_control):
    def setUserDelegation(
        _user,
        _delegate,
        _canWithdraw = True,
        _canBorrow = True,
        _canClaimFromStabPool = True,
        _canClaimLoot = True,
    ):
        mission_control.setUserDelegation(_delegate, _canWithdraw, _canBorrow, _canClaimFromStabPool, _canClaimLoot, sender=_user)
    yield setUserDelegation