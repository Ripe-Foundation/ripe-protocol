import boa
import pytest
from boa.contracts.base_evm_contract import BoaError

from constants import EIGHTEEN_DECIMALS, MAX_UINT256
from conf_utils import filter_logs, redeem_from_stability_pool, sync_deployed_token


def _frame_reasons(frame):
    if isinstance(frame, str):
        return [frame]
    found = []
    detail = getattr(frame, "error_detail", None)
    if detail:
        found.append(detail)
    reason = getattr(getattr(frame, "dev_reason", None), "reason_str", None)
    if reason:
        found.append(reason)
    try:
        vm_reason = getattr(frame, "pretty_vm_reason", None)
    except Exception:
        vm_reason = None
    if vm_reason:
        found.append(str(vm_reason))
    return found


def _boa_error_has_reason(error, expected_reason):
    # Nested Teller → AuctionHouse → token/PriceDesk reverts lose the last-frame
    # # dev: label when titanoboa cannot format the trace. Walk every frame.
    return any(
        expected_reason == reason or expected_reason in reason
        for frame in error.stack_trace
        for reason in _frame_reasons(frame)
    )


def _boa_error_reasons(error):
    return [
        reason
        for frame in error.stack_trace
        for reason in _frame_reasons(frame)
    ]


def _auction_flags(createDebtTerms):
    return dict(
        _debtTerms=createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0),
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=True,
    )


def _make_bob_auctionable_on_bravo(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    bob,
    sally,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    green_token,
    bravo_amount,
    alpha_crash,
    gen_auction_params=None,
    extra_asset_flags=None,
):
    setGeneralConfig()
    if gen_auction_params is None:
        setGeneralDebtConfig(_ltvPaybackBuffer=0)
    else:
        setGeneralDebtConfig(_ltvPaybackBuffer=0, _genAuctionParams=gen_auction_params)
    flags = _auction_flags(createDebtTerms)
    if extra_asset_flags:
        flags.update(extra_asset_flags)
    setAssetConfig(alpha_token, **flags)
    setAssetConfig(bravo_token, **flags)

    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)

    performDeposit(bob, 200 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    performDeposit(bob, bravo_amount, bravo_token, bravo_token_whale)
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    mock_price_source.setPrice(alpha_token, alpha_crash)
    assert credit_engine.canLiquidateUser(bob)
    teller.liquidateUser(bob, False, sender=sally)
    mock_price_source.setPrice(bravo_token, 1)


def _fund_alice(green_token, whale, teller, alice, amount):
    green_token.transfer(alice, amount, sender=whale)
    green_token.approve(teller, amount, sender=alice)
    return green_token.balanceOf(alice)


def _snapshot_ah(
    credit_engine,
    ledger,
    green_token,
    bravo_token,
    simple_erc20_vault,
    lootbox,
    vault_id,
    bob,
    alice,
):
    return {
        "debt": credit_engine.getUserDebtAmount(bob),
        "alice_green": green_token.balanceOf(alice),
        "alice_bravo": bravo_token.balanceOf(alice),
        "bob_bravo": simple_erc20_vault.getTotalAmountForUser(bob, bravo_token),
        "has_auc": ledger.hasFungibleAuction(bob, vault_id, bravo_token),
        "points": lootbox.getLatestDepositPoints(bob, vault_id, bravo_token),
    }


def _user_assets(vault, user):
    return [
        vault.getUserAssetAndAmountAtIndex(user, i)
        for i in range(1, vault.numUserAssets(user))
    ]


def _register_vault(vault_book, governance, vault, description):
    assert vault_book.startAddNewAddressToRegistry(
        vault, description, sender=governance.address
    )
    boa.env.time_travel(blocks=vault_book.registryChangeTimeLock() + 1)
    vault_id = vault_book.confirmNewAddressToRegistry(vault, sender=governance.address)
    assert vault_id != 0
    return vault_id


UNDERSEND_VAULT_SOURCE = """
# @version 0.4.3

from ethereum.ercs import IERC20

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
underSendAmount: public(uint256)

@external
def setUnderSendAmount(_amount: uint256):
    self.underSendAmount = _amount

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
    if self.underSendAmount != 0:
        sendAmount = min(sendAmount, self.underSendAmount)
    if sendAmount == 0:
        return 0, available == 0
    self.userBalances[_user][_asset] = available - sendAmount
    if self.totalBalances[_asset] < sendAmount:
        self.totalBalances[_asset] = 0
    else:
        self.totalBalances[_asset] -= sendAmount
    return sendAmount, self.userBalances[_user][_asset] == 0

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


def test_auction_house_multi_token_payment_scales_by_whole_tokens(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    bob,
    alice,
    sally,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    green_token,
    whale,
    simple_erc20_vault,
    vault_book,
):
    bravo_amount = 100 * EIGHTEEN_DECIMALS
    _make_bob_auctionable_on_bravo(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        credit_engine,
        bob,
        sally,
        alpha_token,
        alpha_token_whale,
        bravo_token,
        bravo_token_whale,
        green_token,
        bravo_amount,
        12 * EIGHTEEN_DECIMALS // 100,
    )
    green_budget = 100 * EIGHTEEN_DECIMALS
    alice_green_before = _fund_alice(green_token, whale, teller, alice, green_budget)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    green_spent = teller.buyManyFungibleAuctions(
        [(bob, vault_id, bravo_token, MAX_UINT256)],
        green_budget,
        False,
        False,
        False,
        alice,
        sender=alice,
    )
    assert green_spent == 100
    logs = filter_logs(teller, "FungAuctionPurchased")
    bravo_logs = [lg for lg in logs if lg.liqAsset == bravo_token.address]
    assert len(bravo_logs) == 1
    assert bravo_logs[0].collateralAmountSent == bravo_amount
    assert bravo_logs[0].collateralUsdValueSent == 100
    assert bravo_logs[0].greenSpent == 100
    assert bravo_token.balanceOf(alice) == bravo_amount
    assert simple_erc20_vault.getTotalAmountForUser(bob, bravo_token) == 0
    assert green_token.balanceOf(alice) == alice_green_before - 100


def test_auction_house_one_wei_takes_one_token_from_multi_token_balance(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    bob,
    alice,
    sally,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    green_token,
    whale,
    simple_erc20_vault,
    vault_book,
):
    bravo_amount = 100 * EIGHTEEN_DECIMALS
    _make_bob_auctionable_on_bravo(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        credit_engine,
        bob,
        sally,
        alpha_token,
        alpha_token_whale,
        bravo_token,
        bravo_token_whale,
        green_token,
        bravo_amount,
        12 * EIGHTEEN_DECIMALS // 100,
    )
    alice_green_before = _fund_alice(green_token, whale, teller, alice, 1)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    green_spent = teller.buyManyFungibleAuctions(
        [(bob, vault_id, bravo_token, MAX_UINT256)],
        1,
        False,
        False,
        False,
        alice,
        sender=alice,
    )
    assert green_spent == 1
    logs = filter_logs(teller, "FungAuctionPurchased")
    assert logs[0].collateralAmountSent == EIGHTEEN_DECIMALS
    assert logs[0].greenSpent == 1
    assert bravo_token.balanceOf(alice) == EIGHTEEN_DECIMALS
    assert simple_erc20_vault.getTotalAmountForUser(bob, bravo_token) == 99 * EIGHTEEN_DECIMALS
    assert green_token.balanceOf(alice) == alice_green_before - 1


def test_auction_house_credits_forward_value_of_zero_decimal_delivery(
    governance,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    bob,
    alice,
    sally,
    alpha_token,
    alpha_token_whale,
    green_token,
    whale,
    simple_erc20_vault,
    vault_book,
):
    coarse_token = boa.load(
        "contracts/mock/MockErc20.vy",
        governance,
        "Coarse Token",
        "COARSE",
        0,
        10,
    )
    sync_deployed_token(coarse_token)
    _make_bob_auctionable_on_bravo(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        credit_engine,
        bob,
        sally,
        alpha_token,
        alpha_token_whale,
        coarse_token,
        governance.address,
        green_token,
        10,
        12 * EIGHTEEN_DECIMALS // 100,
    )
    mock_price_source.setPrice(coarse_token, 3 * EIGHTEEN_DECIMALS)

    _fund_alice(green_token, whale, teller, alice, 5 * EIGHTEEN_DECIMALS)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    green_spent = teller.buyManyFungibleAuctions(
        [(bob, vault_id, coarse_token, MAX_UINT256)],
        5 * EIGHTEEN_DECIMALS,
        False,
        False,
        False,
        alice,
        sender=alice,
    )

    assert green_spent == 3 * EIGHTEEN_DECIMALS
    log = filter_logs(teller, "FungAuctionPurchased")[0]
    assert log.collateralAmountSent == 1
    assert log.collateralUsdValueSent == 3 * EIGHTEEN_DECIMALS
    assert coarse_token.balanceOf(alice) == 1


def test_auction_house_dust_only_purchase_reverts_no_green_spent(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    ledger,
    bob,
    alice,
    sally,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    green_token,
    whale,
    simple_erc20_vault,
    vault_book,
    lootbox,
):
    bravo_amount = EIGHTEEN_DECIMALS // 2
    _make_bob_auctionable_on_bravo(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        credit_engine,
        bob,
        sally,
        alpha_token,
        alpha_token_whale,
        bravo_token,
        bravo_token_whale,
        green_token,
        bravo_amount,
        60 * EIGHTEEN_DECIMALS // 100,
    )
    _fund_alice(green_token, whale, teller, alice, 100 * EIGHTEEN_DECIMALS)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    before = _snapshot_ah(
        credit_engine, ledger, green_token, bravo_token, simple_erc20_vault, lootbox, vault_id, bob, alice
    )
    with boa.reverts("no green spent"):
        teller.buyManyFungibleAuctions(
            [(bob, vault_id, bravo_token, MAX_UINT256)],
            100 * EIGHTEEN_DECIMALS,
            False,
            False,
            False,
            alice,
            sender=alice,
        )
    after = _snapshot_ah(
        credit_engine, ledger, green_token, bravo_token, simple_erc20_vault, lootbox, vault_id, bob, alice
    )
    assert after == before
    assert filter_logs(teller, "FungAuctionPurchased") == []
    assert simple_erc20_vault.getTotalAmountForUser(bob, bravo_token) == bravo_amount
    assert ledger.hasFungibleAuction(bob, vault_id, bravo_token)


@pytest.mark.parametrize("dust_first", [True, False])
def test_auction_house_mixed_batch_skips_zero_credit_entry(
    dust_first,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    ledger,
    bob,
    alice,
    sally,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    green_token,
    whale,
    simple_erc20_vault,
    vault_book,
    lootbox,
):
    bravo_amount = EIGHTEEN_DECIMALS // 2
    _make_bob_auctionable_on_bravo(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        credit_engine,
        bob,
        sally,
        alpha_token,
        alpha_token_whale,
        bravo_token,
        bravo_token_whale,
        green_token,
        bravo_amount,
        60 * EIGHTEEN_DECIMALS // 100,
    )
    green_budget = 100 * EIGHTEEN_DECIMALS
    alice_green_before = _fund_alice(green_token, whale, teller, alice, green_budget)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    bob_bravo_before = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    bob_alpha_before = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    dust_entry = (bob, vault_id, bravo_token, MAX_UINT256)
    healthy_entry = (bob, vault_id, alpha_token, 10 * EIGHTEEN_DECIMALS)
    entries = [dust_entry, healthy_entry] if dust_first else [healthy_entry, dust_entry]
    green_spent = teller.buyManyFungibleAuctions(
        entries,
        green_budget,
        False,
        False,
        False,
        alice,
        sender=alice,
    )
    assert green_spent == 10 * EIGHTEEN_DECIMALS
    assert green_token.balanceOf(alice) == alice_green_before - green_spent
    assert simple_erc20_vault.getTotalAmountForUser(bob, bravo_token) == bob_bravo_before
    assert bravo_token.balanceOf(alice) == 0
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) < bob_alpha_before
    assert alpha_token.balanceOf(alice) > 0
    logs = filter_logs(teller, "FungAuctionPurchased")
    assert [lg.liqAsset for lg in logs] == [alpha_token.address]
    assert logs[0].greenSpent == green_spent
    assert ledger.hasFungibleAuction(bob, vault_id, bravo_token)


def test_auction_house_discounted_one_token_reverts_on_zero_green_transfer(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    createAuctionParams,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    ledger,
    bob,
    alice,
    sally,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    green_token,
    whale,
    simple_erc20_vault,
    vault_book,
    price_desk,
):
    bravo_amount = 1 * EIGHTEEN_DECIMALS
    _make_bob_auctionable_on_bravo(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        credit_engine,
        bob,
        sally,
        alpha_token,
        alpha_token_whale,
        bravo_token,
        bravo_token_whale,
        green_token,
        bravo_amount,
        60 * EIGHTEEN_DECIMALS // 100,
        gen_auction_params=createAuctionParams(_startDiscount=1, _maxDiscount=50_00),
    )
    vault_id = vault_book.getRegId(simple_erc20_vault)
    auc = ledger.getFungibleAuctionDuringPurchase(bob, vault_id, bravo_token)
    assert auc.isActive
    assert auc.startDiscount == 1
    collateral_usd = price_desk.getUsdValue(bravo_token, bravo_amount)
    assert collateral_usd == 1
    assert collateral_usd * 9999 // 10000 == 0
    _fund_alice(green_token, whale, teller, alice, 100 * EIGHTEEN_DECIMALS)
    with pytest.raises(BoaError) as exc_info:
        teller.buyManyFungibleAuctions(
            [(bob, vault_id, bravo_token, MAX_UINT256)],
            100 * EIGHTEEN_DECIMALS,
            False,
            False,
            False,
            alice,
            sender=alice,
        )
    # Requested CreditEngine "cannot repay with 0 green" is not reached:
    # greenSpent floors to 0 and Erc20Token rejects the zero transfer first.
    assert _boa_error_has_reason(exc_info.value, "cannot transfer 0 amount"), (
        _boa_error_reasons(exc_info.value)
    )
    assert simple_erc20_vault.getTotalAmountForUser(bob, bravo_token) == bravo_amount
    assert bravo_token.balanceOf(alice) == 0


def test_auction_house_stab_swap_skips_zero_credit_dust(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    ledger,
    bob,
    sally,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    green_token,
    savings_green,
    whale,
    simple_erc20_vault,
    stability_pool,
    vault_book,
    mission_control,
    switchboard_alpha,
):
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    simple_id = vault_book.getRegId(simple_erc20_vault)
    stab_id = vault_book.getRegId(stability_pool)
    setAssetConfig(
        alpha_token,
        _vaultIds=[simple_id],
        _debtTerms=terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=True,
        _shouldAuctionInstantly=True,
    )
    setAssetConfig(
        bravo_token,
        _vaultIds=[simple_id],
        _debtTerms=terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=True,
        _shouldAuctionInstantly=True,
    )
    setAssetConfig(
        savings_green,
        _vaultIds=[stab_id],
        _debtTerms=createDebtTerms(0, 0, 0, 0, 0, 0),
        _shouldBurnAsPayment=True,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)
    mission_control.setPriorityStabVaults(
        [(stab_id, savings_green)], sender=switchboard_alpha.address
    )

    bravo_amount = EIGHTEEN_DECIMALS // 2
    performDeposit(bob, 200 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    performDeposit(bob, bravo_amount, bravo_token, bravo_token_whale)
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    pool_amount = 100 * EIGHTEEN_DECIMALS
    green_token.transfer(sally, pool_amount, sender=whale)
    green_token.approve(savings_green, pool_amount, sender=sally)
    pool_shares = savings_green.deposit(pool_amount, sally, sender=sally)
    savings_green.approve(teller, pool_shares, sender=sally)
    teller.deposit(savings_green, pool_shares, sally, stability_pool, sender=sally)

    mock_price_source.setPrice(alpha_token, 12 * EIGHTEEN_DECIMALS // 100)
    mock_price_source.setPrice(bravo_token, 1)
    assert credit_engine.canLiquidateUser(bob)
    bob_bravo = simple_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    bob_assets = _user_assets(simple_erc20_vault, bob)
    debt_before = credit_engine.getUserDebtAmount(bob)
    teller.liquidateUser(bob, False, sender=sally)
    swaps = filter_logs(teller, "CollateralSwappedWithStabPool")
    assert [lg.liqAsset for lg in swaps] == [alpha_token.address]
    assert simple_erc20_vault.getTotalAmountForUser(bob, bravo_token) == bob_bravo == bravo_amount
    assert bravo_token.balanceOf(stability_pool) == 0
    assert (bravo_token.address, bravo_amount) in _user_assets(simple_erc20_vault, bob)
    assert _user_assets(simple_erc20_vault, bob)[-1] == (bravo_token.address, bravo_amount)
    repay = sum(lg.valueSwapped for lg in swaps)
    assert repay > 0
    liq = filter_logs(teller, "LiquidateUser")
    assert len(liq) == 1
    assert liq[0].repayAmount == repay
    assert credit_engine.getUserDebtAmount(bob) == debt_before + liq[0].liqFeesUnpaid - repay
    assert ledger.hasFungibleAuction(bob, simple_id, bravo_token)
    assert bob_assets[1] == (bravo_token.address, bravo_amount)


def test_wsuper_price_desk_auction_house_tx(
    ripe_hq,
    mock_yield_registry,
    mock_price_source,
    price_desk,
    switchboard_alpha,
    mission_control,
    governance,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    teller,
    credit_engine,
    bob,
    alice,
    sally,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    green_token,
    whale,
    simple_erc20_vault,
    vault_book,
):
    src = boa.load(
        "contracts/priceSources/wsuperOETHbPrices.vy",
        ripe_hq,
        bravo_token.address,
        mock_yield_registry,
        mock_yield_registry,
        alpha_token.address,
        1,
        100,
        name="wsuper_ah_e2e",
    )
    assert price_desk.startAddNewAddressToRegistry(src, "wsuper ah e2e", sender=governance.address)
    boa.env.time_travel(blocks=price_desk.registryChangeTimeLock() + 1)
    wsuper_id = price_desk.confirmNewAddressToRegistry(src, sender=governance.address)

    _make_bob_auctionable_on_bravo(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        credit_engine,
        bob,
        sally,
        alpha_token,
        alpha_token_whale,
        bravo_token,
        bravo_token_whale,
        green_token,
        EIGHTEEN_DECIMALS,
        12 * EIGHTEEN_DECIMALS // 100,
    )
    mock_price_source.setPrice(bravo_token, 0)
    mission_control.setPriorityPriceSourceIds([wsuper_id], sender=switchboard_alpha.address)
    assert src.getPriceAndHasFeed(bravo_token) == (0, False)
    assert price_desk.getPrice(bravo_token) == 0
    _fund_alice(green_token, whale, teller, alice, 100 * EIGHTEEN_DECIMALS)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    with pytest.raises(BoaError) as exc_info:
        teller.buyManyFungibleAuctions(
            [(bob, vault_id, bravo_token, MAX_UINT256)],
            100 * EIGHTEEN_DECIMALS,
            False,
            False,
            False,
            alice,
            sender=alice,
        )
    # Requested AuctionHouse "no green spent" is not reached: getAssetAmount
    # is fail-closed, so PriceDesk raises before the no-progress assert.
    assert _boa_error_has_reason(exc_info.value, "has price config, no price"), (
        _boa_error_reasons(exc_info.value)
    )
    assert simple_erc20_vault.getTotalAmountForUser(bob, bravo_token) == EIGHTEEN_DECIMALS
    assert bravo_token.balanceOf(alice) == 0

    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    mission_control.setPriorityPriceSourceIds([6], sender=switchboard_alpha.address)
    assert price_desk.getPrice(bravo_token) == EIGHTEEN_DECIMALS


def test_auction_house_undersend_vault_hits_zero_usd_backstop(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    mock_price_source,
    teller,
    credit_engine,
    ledger,
    green_token,
    whale,
    vault_book,
    governance,
    lootbox,
):
    with boa.env.anchor():
        vault = boa.loads(UNDERSEND_VAULT_SOURCE, name="undersend_vault")
        vault_id = _register_vault(vault_book, governance, vault, "undersend vault")
        token = boa.load(
            "contracts/mock/MockErc20.vy",
            governance,
            "Undersend",
            "UNDS",
            18,
            1_000_000_000,
            name="undersend_token",
        )
        borrower = boa.env.generate_address("undersend-borrower")
        buyer = boa.env.generate_address("undersend-buyer")
        keeper = boa.env.generate_address("undersend-keeper")
        setGeneralConfig(_perUserMaxVaults=20)
        setGeneralDebtConfig(_ltvPaybackBuffer=0)
        setAssetConfig(
            token,
            _vaultIds=[vault_id],
            _debtTerms=createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0),
            _shouldBurnAsPayment=False,
            _shouldTransferToEndaoment=False,
            _shouldSwapInStabPools=False,
            _shouldAuctionInstantly=True,
        )
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
        mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)
        amount = 200 * EIGHTEEN_DECIMALS
        token.mint(borrower, amount, sender=governance.address)
        token.approve(teller, amount, sender=borrower)
        teller.deposit(token, amount, borrower, vault, sender=borrower)
        teller.borrow(100 * EIGHTEEN_DECIMALS, borrower, False, sender=borrower)
        mock_price_source.setPrice(token, 12 * EIGHTEEN_DECIMALS // 100)
        assert credit_engine.canLiquidateUser(borrower)
        teller.liquidateUser(borrower, False, sender=keeper)
        mock_price_source.setPrice(token, 1)
        vault.setUnderSendAmount(1)
        _fund_alice(green_token, whale, teller, buyer, 100 * EIGHTEEN_DECIMALS)
        before = {
            "debt": credit_engine.getUserDebtAmount(borrower),
            "buyer_green": green_token.balanceOf(buyer),
            "buyer_token": token.balanceOf(buyer),
            "borrower_token": vault.getTotalAmountForUser(borrower, token),
            "vault_token": token.balanceOf(vault),
            "has_auc": ledger.hasFungibleAuction(borrower, vault_id, token),
            "points": lootbox.getLatestDepositPoints(borrower, vault_id, token),
        }
        with boa.reverts("amounts do not match up"):
            teller.buyManyFungibleAuctions(
                [(borrower, vault_id, token.address, MAX_UINT256)],
                100 * EIGHTEEN_DECIMALS,
                False,
                False,
                False,
                buyer,
                sender=buyer,
            )
        assert {
            "debt": credit_engine.getUserDebtAmount(borrower),
            "buyer_green": green_token.balanceOf(buyer),
            "buyer_token": token.balanceOf(buyer),
            "borrower_token": vault.getTotalAmountForUser(borrower, token),
            "vault_token": token.balanceOf(vault),
            "has_auc": ledger.hasFungibleAuction(borrower, vault_id, token),
            "points": lootbox.getLatestDepositPoints(borrower, vault_id, token),
        } == before


def test_auction_house_shares_vault_dust_preview_is_skipped(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    ledger,
    bob,
    alice,
    sally,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    green_token,
    whale,
    rebase_erc20_vault,
    simple_erc20_vault,
    vault_book,
):
    rebase_id = vault_book.getRegId(rebase_erc20_vault)
    simple_id = vault_book.getRegId(simple_erc20_vault)
    flags = _auction_flags(createDebtTerms)
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    setAssetConfig(alpha_token, _vaultIds=[simple_id], **flags)
    setAssetConfig(bravo_token, _vaultIds=[rebase_id], **flags)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)
    dust = EIGHTEEN_DECIMALS // 2
    performDeposit(bob, 200 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale, simple_erc20_vault)
    performDeposit(bob, dust, bravo_token, bravo_token_whale, rebase_erc20_vault)
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    mock_price_source.setPrice(alpha_token, 60 * EIGHTEEN_DECIMALS // 100)
    assert credit_engine.canLiquidateUser(bob)
    teller.liquidateUser(bob, False, sender=sally)
    preview = rebase_erc20_vault.getTotalAmountForUser(bob, bravo_token)
    mock_price_source.setPrice(bravo_token, 1)
    assert preview * 1 // EIGHTEEN_DECIMALS == 0
    _fund_alice(green_token, whale, teller, alice, 100 * EIGHTEEN_DECIMALS)
    with boa.reverts("no green spent"):
        teller.buyManyFungibleAuctions(
            [(bob, rebase_id, bravo_token, MAX_UINT256)],
            100 * EIGHTEEN_DECIMALS,
            False,
            False,
            False,
            alice,
            sender=alice,
        )
    assert rebase_erc20_vault.getTotalAmountForUser(bob, bravo_token) == preview
    assert ledger.hasFungibleAuction(bob, rebase_id, bravo_token)
    assert bravo_token.balanceOf(alice) == 0


def test_auction_house_ordinary_stab_swap_still_pays(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    bob,
    sally,
    alpha_token,
    alpha_token_whale,
    green_token,
    savings_green,
    whale,
    simple_erc20_vault,
    stability_pool,
    vault_book,
    mission_control,
    switchboard_alpha,
):
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    simple_id = vault_book.getRegId(simple_erc20_vault)
    stab_id = vault_book.getRegId(stability_pool)
    setAssetConfig(
        alpha_token,
        _vaultIds=[simple_id],
        _debtTerms=terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=True,
        _shouldAuctionInstantly=False,
    )
    setAssetConfig(
        savings_green,
        _vaultIds=[stab_id],
        _debtTerms=createDebtTerms(0, 0, 0, 0, 0, 0),
        _shouldBurnAsPayment=True,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)
    mission_control.setPriorityStabVaults(
        [(stab_id, savings_green)], sender=switchboard_alpha.address
    )
    performDeposit(bob, 200 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    pool_amount = 100 * EIGHTEEN_DECIMALS
    green_token.transfer(sally, pool_amount, sender=whale)
    green_token.approve(savings_green, pool_amount, sender=sally)
    pool_shares = savings_green.deposit(pool_amount, sally, sender=sally)
    savings_green.approve(teller, pool_shares, sender=sally)
    teller.deposit(savings_green, pool_shares, sally, stability_pool, sender=sally)
    mock_price_source.setPrice(alpha_token, 40 * EIGHTEEN_DECIMALS // 100)
    debt_before = credit_engine.getUserDebtAmount(bob)
    teller.liquidateUser(bob, False, sender=sally)
    swaps = filter_logs(teller, "CollateralSwappedWithStabPool")
    assert len(swaps) == 1
    assert swaps[0].liqAsset == alpha_token.address
    assert swaps[0].valueSwapped > 0
    assert alpha_token.balanceOf(stability_pool) == swaps[0].collateralAmountOut
    assert credit_engine.getUserDebtAmount(bob) < debt_before


def test_auction_house_claimable_green_skips_zero_credit_dust(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    ledger,
    auction_house,
    bob,
    alice,
    sally,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    charlie_token,
    charlie_token_whale,
    green_token,
    whale,
    simple_erc20_vault,
    stability_pool,
    vault_book,
    mission_control,
    switchboard_alpha,
):
    setGeneralConfig()
    setGeneralDebtConfig(_ltvPaybackBuffer=0, _keeperFeeRatio=0, _minKeeperFee=0)
    terms = createDebtTerms(_liqThreshold=80_00, _liqFee=10_00, _ltv=50_00, _borrowRate=0)
    simple_id = vault_book.getRegId(simple_erc20_vault)
    stab_id = vault_book.getRegId(stability_pool)
    setAssetConfig(
        alpha_token,
        _vaultIds=[simple_id],
        _debtTerms=terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=True,
        _shouldAuctionInstantly=True,
    )
    setAssetConfig(
        bravo_token,
        _vaultIds=[simple_id, stab_id],
        _debtTerms=terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=True,
    )
    setAssetConfig(charlie_token, _vaultIds=[stab_id])
    setAssetConfig(green_token, _vaultIds=[stab_id], _debtTerms=createDebtTerms(0, 0, 0, 0, 0, 0), _shouldBurnAsPayment=True)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)
    mission_control.setPriorityStabVaults(
        [(stab_id, bravo_token)], sender=switchboard_alpha.address
    )
    bravo_deposit = 200 * EIGHTEEN_DECIMALS
    bravo_token.transfer(sally, bravo_deposit, sender=bravo_token_whale)
    bravo_token.approve(teller, bravo_deposit, sender=sally)
    teller.deposit(bravo_token, bravo_deposit, sally, stability_pool, 0, sender=sally)
    claimable_charlie = 200 * (10 ** charlie_token.decimals())
    charlie_token.transfer(stability_pool, claimable_charlie, sender=charlie_token_whale)
    stability_pool.swapForLiquidatedCollateral(
        bravo_token,
        100 * EIGHTEEN_DECIMALS,
        charlie_token,
        claimable_charlie,
        whale,
        green_token,
        whale,
        sender=auction_house.address,
    )
    redeem_amount = 50 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, redeem_amount, sender=whale)
    green_token.approve(teller, redeem_amount, sender=alice)
    redeem_from_stability_pool(teller, stab_id, charlie_token, redeem_amount, sender=alice)
    claimable_before = stability_pool.claimableBalances(bravo_token, green_token)
    assert claimable_before == redeem_amount
    performDeposit(bob, EIGHTEEN_DECIMALS // 2, alpha_token, alpha_token_whale)
    performDeposit(bob, 200 * EIGHTEEN_DECIMALS, bravo_token, bravo_token_whale, simple_erc20_vault)
    teller.borrow(80 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    mock_price_source.setPrice(bravo_token, 40 * EIGHTEEN_DECIMALS // 100)
    mock_price_source.setPrice(alpha_token, 1)
    assert credit_engine.canLiquidateUser(bob)
    alpha_before = simple_erc20_vault.getTotalAmountForUser(bob, alpha_token)
    teller.liquidateUser(bob, False, sender=sally)
    swaps = filter_logs(teller, "CollateralSwappedWithStabPool")
    assert alpha_token.address not in [lg.liqAsset for lg in swaps]
    assert simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == alpha_before
    assert alpha_token.balanceOf(stability_pool) == 0
    assert stability_pool.claimableBalances(bravo_token, green_token) == claimable_before
    assert ledger.hasFungibleAuction(bob, simple_id, alpha_token)


def test_auction_house_dust_auction_removed_after_expiry(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    createAuctionParams,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    ledger,
    auction_house,
    bob,
    alice,
    sally,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    green_token,
    simple_erc20_vault,
    vault_book,
):
    bravo_amount = EIGHTEEN_DECIMALS // 2
    _make_bob_auctionable_on_bravo(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        credit_engine,
        bob,
        sally,
        alpha_token,
        alpha_token_whale,
        bravo_token,
        bravo_token_whale,
        green_token,
        bravo_amount,
        60 * EIGHTEEN_DECIMALS // 100,
        gen_auction_params=createAuctionParams(_delay=0, _duration=10),
    )
    vault_id = vault_book.getRegId(simple_erc20_vault)
    auc = ledger.getFungibleAuctionDuringPurchase(bob, vault_id, bravo_token)
    assert auc.isActive
    blocks = auc.endBlock - boa.env.evm.patch.block_number
    if blocks:
        boa.env.time_travel(blocks=blocks)
    assert auction_house.removeExpiredFungibleAuction(bob, vault_id, bravo_token, sender=alice)
    assert not ledger.hasFungibleAuction(bob, vault_id, bravo_token)
    assert simple_erc20_vault.getTotalAmountForUser(bob, bravo_token) == bravo_amount


def test_auction_house_dust_auction_purchasable_after_price_recovery(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    ledger,
    bob,
    alice,
    sally,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    green_token,
    whale,
    simple_erc20_vault,
    vault_book,
):
    bravo_amount = EIGHTEEN_DECIMALS // 2
    _make_bob_auctionable_on_bravo(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        credit_engine,
        bob,
        sally,
        alpha_token,
        alpha_token_whale,
        bravo_token,
        bravo_token_whale,
        green_token,
        bravo_amount,
        60 * EIGHTEEN_DECIMALS // 100,
    )
    vault_id = vault_book.getRegId(simple_erc20_vault)
    assert ledger.hasFungibleAuction(bob, vault_id, bravo_token)
    alice_green = _fund_alice(green_token, whale, teller, alice, 100 * EIGHTEEN_DECIMALS)
    with boa.reverts("no green spent"):
        teller.buyManyFungibleAuctions(
            [(bob, vault_id, bravo_token, MAX_UINT256)],
            100 * EIGHTEEN_DECIMALS,
            False,
            False,
            False,
            alice,
            sender=alice,
        )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    green_spent = teller.buyManyFungibleAuctions(
        [(bob, vault_id, bravo_token, MAX_UINT256)],
        100 * EIGHTEEN_DECIMALS,
        False,
        False,
        False,
        alice,
        sender=alice,
    )
    assert green_spent == bravo_amount
    assert bravo_token.balanceOf(alice) == bravo_amount
    assert simple_erc20_vault.getTotalAmountForUser(bob, bravo_token) == 0
    assert green_token.balanceOf(alice) == alice_green - green_spent
    assert not ledger.hasFungibleAuction(bob, vault_id, bravo_token)
