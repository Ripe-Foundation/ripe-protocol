import pytest
import boa
from constants import HUNDRED_PERCENT, MAX_UINT256, ZERO_ADDRESS, EIGHTEEN_DECIMALS


def advance_timelock_blocks(blocks):
    """Advance governance block number without aging historical fork oracles."""
    boa.env.evm.patch.block_number += blocks


def ensure_token_scale(price_desk, asset, sender):
    """Synchronize PriceDesk scale when a priced asset has none cached yet."""
    if asset is None:
        return
    asset_addr = getattr(asset, "address", asset)
    if asset_addr in (ZERO_ADDRESS, price_desk.ETH()):
        return
    if price_desk.tokenScale(asset_addr) == 0:
        try:
            price_desk.syncTokenScale(asset_addr, sender=sender)
        except boa.BoaError:
            # EOAs and mocks without decimals() cannot be synchronized.
            # Production admission still requires a successful sync.
            return


_SCALE_BIND = {}


def bind_token_scale(price_desk, sender):
    _SCALE_BIND["desk"] = price_desk
    _SCALE_BIND["sender"] = sender


def unbind_token_scale():
    _SCALE_BIND.clear()


def sync_deployed_token(token):
    desk = _SCALE_BIND.get("desk")
    sender = _SCALE_BIND.get("sender")
    assert desk is not None, "PriceDesk token-scale bind is not active"
    assert sender is not None, "token-scale sender bind is not active"
    ensure_token_scale(desk, token, sender)


def clear_transient_storage():
    """Emulate a real EVM transaction boundary under titanoboa 0.2.7."""
    boa.env.evm.vm.state.clear_transient_storage()


def has_dev_reason(error, expected_reason):
    return any(
        not isinstance(frame, str)
        and getattr(frame, "dev_reason", None) is not None
        and frame.dev_reason.reason_str == expected_reason
        for frame in error.stack_trace
    )


def assert_reverted_call(error, expected_reason, contract):
    """Bind a nested dev reason to the exact failed outer computation.

    Outer Vyper extcalls can mask nested dev labels from ``boa.reverts``, so
    inspect the structured frames instead. ``_computation`` is intentionally
    coupled to the repository's pinned titanoboa 0.2.7 test API; py-evm drops
    all logs from an error computation by construction, so ``is_error`` also
    establishes that no transaction event can survive the revert.
    """
    assert has_dev_reason(error, expected_reason), str(error)
    computation = contract._computation
    assert computation is not None
    assert computation.is_error


def install_lootbox_user_checkpoint_trap(lootbox, ripe_hq, blocked_user):
    from pathlib import Path

    source = Path("contracts/core/Lootbox.vy").read_text()
    needle = """@external
def updateDepositPoints(
    _user: address,
    _vaultId: uint256,
    _vaultAddr: address,
    _asset: address,
    _a: addys.Addys = empty(addys.Addys),
):
    assert addys._isValidRipeAddr(msg.sender) # dev: no perms
    assert not deptBasics.isPaused # dev: contract paused
"""
    assert source.count(needle) == 1
    # Use a # dev: assert, not a string revert: a string payload makes the
    # Lootbox mutant exceed EIP-170. Teller-wrapped calls do not surface
    # the # dev: reason, so callers match with bare boa.reverts() plus
    # pre/post state.
    source = source.replace(
        needle,
        needle + f"    assert _user != {blocked_user} # dev: user checkpoint blocked\n",
        1,
    )
    mutant = boa.loads(
        source,
        ripe_hq.address,
        43_200,
        43_200,
        100 * EIGHTEEN_DECIMALS,
        100 * EIGHTEEN_DECIMALS,
        name="lootbox_user_checkpoint_trap",
    )
    boa.env.set_code(lootbox.address, bytes(boa.env.get_code(mutant.address)))


@pytest.fixture
def registerVault(vault_book, governance):
    def registerVault(vault, description):
        assert vault_book.startAddNewAddressToRegistry(
            vault.address,
            description,
            sender=governance.address,
        )
        boa.env.time_travel(blocks=vault_book.registryChangeTimeLock())
        return vault_book.confirmNewAddressToRegistry(vault.address, sender=governance.address)

    yield registerVault


@pytest.fixture
def cleanCoreRipeGovFixture(
    ripe_hq,
    ripe_token,
    vault_book,
    mission_control,
    switchboard_bravo,
    switchboard_charlie,
    governance,
):
    """Build and select one clean RipeGov vault through all delayed paths.

    RIPE must have finite nonzero deposit caps before this builder runs because
    SwitchboardBravo deliberately rejects max_value(uint256) caps.
    """

    def _advance_to(block_number):
        current = boa.env.evm.patch.block_number
        if current < block_number:
            boa.env.time_travel(blocks=block_number - current)
        assert boa.env.evm.patch.block_number >= block_number

    def build():
        clean_vault = boa.load(
            "contracts/vaults/RipeGov.vy",
            ripe_hq,
            name="aud_024_clean_core_ripe_gov_vault",
        )
        assert boa.env.get_code(clean_vault.address) != b""
        assert clean_vault.totalGovPoints() == 0
        assert not clean_vault.isPaused()
        assert clean_vault.totalBalances(ripe_token) == 0

        previous_core_id = mission_control.coreRipeGovVaultId()
        assert vault_book.startAddNewAddressToRegistry(
            clean_vault,
            "AUD-024 clean RipeGov",
            sender=governance.address,
        )
        registration = vault_book.pendingNewAddr(clean_vault)
        assert registration.initiatedBlock != 0
        assert registration.confirmBlock > registration.initiatedBlock
        _advance_to(registration.confirmBlock)
        new_id = vault_book.confirmNewAddressToRegistry(
            clean_vault,
            sender=governance.address,
        )
        assert vault_book.isValidRegId(new_id)
        assert vault_book.getAddr(new_id) == clean_vault.address
        assert new_id != previous_core_id

        asset_config_before = mission_control.assetConfig(ripe_token)
        lock_config_before = mission_control.ripeGovVaultConfig(ripe_token)
        existing_vault_ids = list(asset_config_before.vaultIds)
        assert new_id not in existing_vault_ids
        assert len(existing_vault_ids) < 10
        assert 0 < asset_config_before.perUserDepositLimit < MAX_UINT256
        assert 0 < asset_config_before.globalDepositLimit < MAX_UINT256
        new_vault_ids = existing_vault_ids + [new_id]

        # Omit the optional MissionControl argument intentionally. Both
        # switchboards resolve empty(address) to the current MissionControl and
        # reject its explicit address with "use empty for current mission control".
        support_action = switchboard_bravo.setAssetDepositParams(
            ripe_token,
            new_vault_ids,
            asset_config_before.stakersPointsAlloc,
            asset_config_before.voterPointsAlloc,
            asset_config_before.perUserDepositLimit,
            asset_config_before.globalDepositLimit,
            asset_config_before.minDepositBalance,
            sender=governance.address,
        )
        support_confirmation = switchboard_bravo.getActionConfirmationBlock(
            support_action
        )
        assert support_confirmation > boa.env.evm.patch.block_number
        _advance_to(support_confirmation)
        assert switchboard_bravo.executePendingAction(
            support_action,
            sender=governance.address,
        )

        asset_config_after = mission_control.assetConfig(ripe_token)
        assert mission_control.isSupportedAssetInVault(new_id, ripe_token)
        assert list(asset_config_after.vaultIds) == new_vault_ids
        for field in (
            "stakersPointsAlloc",
            "voterPointsAlloc",
            "perUserDepositLimit",
            "globalDepositLimit",
            "minDepositBalance",
        ):
            assert getattr(asset_config_after, field) == getattr(
                asset_config_before, field
            )
        for field in asset_config_before._fields:
            if field not in (
                "vaultIds",
                "stakersPointsAlloc",
                "voterPointsAlloc",
                "perUserDepositLimit",
                "globalDepositLimit",
                "minDepositBalance",
            ):
                assert getattr(asset_config_after, field) == getattr(
                    asset_config_before, field
                )
        assert mission_control.ripeGovVaultConfig(ripe_token) == lock_config_before

        assert vault_book.isValidRegId(new_id)
        assert vault_book.getAddr(new_id) == clean_vault.address
        assert new_id != previous_core_id
        assert mission_control.isSupportedAssetInVault(new_id, ripe_token)
        assert clean_vault.totalGovPoints() == 0
        assert not clean_vault.isPaused()
        assert clean_vault.totalBalances(ripe_token) == 0

        pointer_action = switchboard_charlie.setCoreRipeGovVaultId(
            new_id,
            sender=governance.address,
        )
        pointer_confirmation = switchboard_charlie.getActionConfirmationBlock(
            pointer_action
        )
        assert pointer_confirmation > boa.env.evm.patch.block_number
        _advance_to(pointer_confirmation)
        assert switchboard_charlie.executePendingAction(
            pointer_action,
            sender=governance.address,
        )

        assert mission_control.coreRipeGovVaultId() == new_id
        assert mission_control.isRipeGovVaultId(new_id)
        assert mission_control.isRipeGovVaultId(previous_core_id)
        assert vault_book.getAddr(new_id) == clean_vault.address
        assert not clean_vault.isPaused()
        assert clean_vault.totalBalances(ripe_token) == 0

        return {
            "vault": clean_vault,
            "vault_id": new_id,
            "previous_vault_id": previous_core_id,
            "existing_vault_ids": existing_vault_ids,
            "new_vault_ids": new_vault_ids,
            "registration_confirmation": registration.confirmBlock,
            "support_action": support_action,
            "support_confirmation": support_confirmation,
            "pointer_action": pointer_action,
            "pointer_confirmation": pointer_confirmation,
            "asset_config_before": asset_config_before,
            "asset_config_after": asset_config_after,
            "lock_config_before": lock_config_before,
        }

    return build


def filter_logs(contract, event_name, _strict=False):
    return [e for e in contract.get_logs(strict=_strict) if type(e).__name__ == event_name]


def get_boa_dev_reasons(error):
    return {
        frame.dev_reason.reason_str
        for frame in error.stack_trace
        if getattr(frame, "dev_reason", None) is not None
    }


def redeem_collateral(
    teller,
    user,
    vault_id,
    asset,
    payment_amount=MAX_UINT256,
    is_payment_savings_green=False,
    should_transfer_balance=False,
    should_refund_savings_green=True,
    recipient=None,
    *,
    sender,
):
    """Execute the removed single-redemption API through its one-item batch equivalent."""
    if recipient is None:
        recipient = sender
    redemption = (user, vault_id, asset, MAX_UINT256)
    return teller.redeemCollateralFromMany(
        [redemption],
        payment_amount,
        is_payment_savings_green,
        should_transfer_balance,
        should_refund_savings_green,
        recipient,
        sender=sender,
    )


def buy_fungible_auction(
    teller,
    liq_user,
    vault_id,
    asset,
    payment_amount=MAX_UINT256,
    is_payment_savings_green=False,
    should_transfer_balance=False,
    should_refund_savings_green=True,
    recipient=None,
    *,
    sender,
):
    """Execute the removed single-auction API through its one-item batch equivalent."""
    if recipient is None:
        recipient = sender
    purchase = (liq_user, vault_id, asset, MAX_UINT256)
    return teller.buyManyFungibleAuctions(
        [purchase],
        payment_amount,
        is_payment_savings_green,
        should_transfer_balance,
        should_refund_savings_green,
        recipient,
        sender=sender,
    )


def claim_from_stability_pool(
    teller,
    vault_id,
    stab_asset,
    claim_asset,
    max_usd_value=MAX_UINT256,
    user=None,
    should_auto_deposit=False,
    *,
    sender,
):
    """Execute the removed single-claim API through its one-item batch equivalent."""
    if user is None:
        user = sender
    claim = (stab_asset, claim_asset, max_usd_value)
    return teller.claimManyFromStabilityPool(
        vault_id,
        [claim],
        user,
        should_auto_deposit,
        sender=sender,
    )


def redeem_from_stability_pool(
    teller,
    vault_id,
    claim_asset,
    payment_amount=MAX_UINT256,
    recipient=None,
    should_auto_deposit=False,
    is_payment_savings_green=False,
    should_refund_savings_green=True,
    *,
    sender,
):
    """Execute the removed single-pool redemption through its one-item batch equivalent."""
    if recipient is None:
        recipient = sender
    redemption = (claim_asset, MAX_UINT256)
    return teller.redeemManyFromStabilityPool(
        vault_id,
        [redemption],
        payment_amount,
        recipient,
        should_auto_deposit,
        is_payment_savings_green,
        should_refund_savings_green,
        sender=sender,
    )


def set_full_payoff_params(
    deleverage,
    switchboard_alpha,
    buffer_amount=0,
    overage_bps=0,
    dust_threshold=0,
    dust_bps=0,
):
    deleverage.setDeleverageFullPayoffParam(1, buffer_amount, sender=switchboard_alpha.address)
    deleverage.setDeleverageFullPayoffParam(2, overage_bps, sender=switchboard_alpha.address)
    deleverage.setDeleverageFullPayoffParam(3, dust_threshold, sender=switchboard_alpha.address)
    deleverage.setDeleverageFullPayoffParam(4, dust_bps, sender=switchboard_alpha.address)


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
        _maxLtvDeviation = 10_00,
        _keeperFeeRatio = 0,
        _minKeeperFee = 0,
        _maxKeeperFee = MAX_UINT256,
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
            _maxLtvDeviation,
            _keeperFeeRatio,
            _minKeeperFee,
            _maxKeeperFee,
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
def setAssetConfig(mission_control, switchboard_bravo, createDebtTerms, price_desk):
    def setAssetConfig(
        _asset,
        _vaultIds = [3], # default simple erc20 vault
        _stakersPointsAlloc = 10,
        _voterPointsAlloc = 10,
        _perUserDepositLimit = MAX_UINT256,
        _globalDepositLimit = MAX_UINT256,
        _minDepositBalance = 0,
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
            _minDepositBalance,
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
        if not _isNft:
            ensure_token_scale(price_desk, _asset, switchboard_bravo.address)
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
        _stabPoolRipePerDollarClaimed = 0,
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
            _stabPoolRipePerDollarClaimed,
        )
        mission_control.setRipeRewardsConfig(config, sender=switchboard_alpha.address)
    yield setRipeRewardsConfig


###############
# User Config #
###############


@pytest.fixture(scope="session")
def setUserConfig(mission_control, teller):
    def setUserConfig(
        _user,
        _canAnyoneDeposit = True,
        _canAnyoneRepayDebt = True,
        _canAnyoneBondForUser = False,
    ):
        config = (
            _canAnyoneDeposit,
            _canAnyoneRepayDebt,
            _canAnyoneBondForUser,
        )
        mission_control.setUserConfig(_user, config, sender=teller.address)
    yield setUserConfig


@pytest.fixture(scope="session")
def setUserDelegation(mission_control, teller):
    def setUserDelegation(
        _user,
        _delegate,
        _canWithdraw = True,
        _canBorrow = True,
        _canClaimFromStabPool = True,
        _canClaimLoot = True,
    ):
        config = (
            _canWithdraw,
            _canBorrow,
            _canClaimFromStabPool,
            _canClaimLoot,
        )
        mission_control.setUserDelegation(_user, _delegate, config, sender=teller.address)
    yield setUserDelegation
