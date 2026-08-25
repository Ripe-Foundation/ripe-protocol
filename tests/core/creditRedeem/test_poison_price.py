import boa
import pytest

from constants import EIGHTEEN_DECIMALS, MAX_UINT256, ZERO_ADDRESS
from conf_utils import filter_logs, redeem_collateral, sync_deployed_token


UNDER_SEND_VAULT_SOURCE = """
# @version 0.4.3

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

asset: public(address)
underSendAmount: public(uint256)
vaultAmount: public(uint256)
balances: public(HashMap[address, uint256])
priceSourceToZero: address

@external
def configure(_asset: address, _user: address, _amount: uint256, _underSendAmount: uint256, _priceSourceToZero: address):
    self.asset = _asset
    self.balances[_user] = _amount
    self.vaultAmount = _amount
    self.underSendAmount = _underSendAmount
    self.priceSourceToZero = _priceSourceToZero

@view
@external
def getTotalAmountForUser(_user: address, _asset: address) -> uint256:
    if _asset != self.asset:
        return 0
    return self.balances[_user]

@view
@external
def numUserAssets(_user: address) -> uint256:
    if self.balances[_user] == 0:
        return 0
    return 2

@view
@external
def getUserAssetAndAmountAtIndex(_user: address, _index: uint256) -> (address, uint256):
    if _index != 1 or self.balances[_user] == 0:
        return empty(address), 0
    return self.asset, self.balances[_user]

@view
@external
def doesUserHaveBalance(_user: address, _asset: address) -> bool:
    return _asset == self.asset and self.balances[_user] != 0

@view
@external
def getTotalAmountForVault(_asset: address) -> uint256:
    if _asset != self.asset:
        return 0
    return self.vaultAmount

@view
@external
def getUserLootBoxShare(_user: address, _asset: address) -> uint256:
    if _asset != self.asset:
        return 0
    return self.balances[_user]

@external
def transferBalanceWithinVault(
    _asset: address,
    _fromUser: address,
    _toUser: address,
    _transferAmount: uint256,
    _a: Addys = empty(Addys),
) -> (uint256, bool):
    sent: uint256 = self.underSendAmount
    self.balances[_fromUser] -= sent
    self.balances[_toUser] += sent
    if self.priceSourceToZero != empty(address):
        extcall MutablePriceSource(self.priceSourceToZero).setPrice(self.asset, 0)
    return sent, self.balances[_fromUser] == 0
"""


def _redeem_terms(createDebtTerms):
    return createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=70_00,
        _liqThreshold=80_00,
        _liqFee=10_00,
        _borrowRate=0,
        _daowry=0,
    )


def _make_bob_redeemable_on_poisoned_bravo(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    bob,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    bravo_amount,
    vault=None,
    vault_ids=None,
):
    setGeneralConfig()
    debt_terms = _redeem_terms(createDebtTerms)
    extra = {} if vault_ids is None else {"_vaultIds": vault_ids}
    setAssetConfig(alpha_token, _debtTerms=debt_terms, **extra)
    setAssetConfig(bravo_token, _debtTerms=debt_terms, **extra)
    setGeneralDebtConfig()

    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)

    if vault is None:
        performDeposit(bob, 200 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
        performDeposit(bob, bravo_amount, bravo_token, bravo_token_whale)
    else:
        performDeposit(bob, 200 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale, vault)
        performDeposit(bob, bravo_amount, bravo_token, bravo_token_whale, vault)
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    mock_price_source.setPrice(alpha_token, 70 * EIGHTEEN_DECIMALS // 100)
    mock_price_source.setPrice(bravo_token, 1)
    assert credit_engine.canRedeemUserCollateral(bob)
    assert not credit_engine.getLatestUserDebtAndTerms(bob, False)[0].inLiquidation


def _fund_alice(green_token, whale, teller, alice, amount):
    green_token.transfer(alice, amount, sender=whale)
    green_token.approve(teller, amount, sender=alice)
    return green_token.balanceOf(alice)


def _snapshot_dust_state(
    credit_engine,
    green_token,
    credit_redeem,
    teller,
    bravo_token,
    vault,
    lootbox,
    vault_id,
    bob,
    alice,
):
    debt, _, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    return {
        "debt": debt.amount,
        "principal": debt.principal,
        "alice_green": green_token.balanceOf(alice),
        "alice_allowance": green_token.allowance(alice, teller),
        "credit_redeem_green": green_token.balanceOf(credit_redeem),
        "alice_bravo": bravo_token.balanceOf(alice),
        "bob_bravo": vault.getTotalAmountForUser(bob, bravo_token),
        "points": lootbox.getLatestDepositPoints(bob, vault_id, bravo_token),
    }


def test_credit_redeem_price_one_takes_full_token_burns_one_wei(
    ripe_hq,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    bob,
    alice,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    green_token,
    whale,
    credit_engine,
    simple_erc20_vault,
    vault_book,
    createDebtTerms,
    price_desk,
):
    bravo_amount = 1 * EIGHTEEN_DECIMALS
    _make_bob_redeemable_on_poisoned_bravo(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        credit_engine,
        bob,
        alpha_token,
        alpha_token_whale,
        bravo_token,
        bravo_token_whale,
        bravo_amount,
    )

    assert price_desk.getPrice(bravo_token) == 1
    assert price_desk.getAssetAmount(bravo_token, 60 * EIGHTEEN_DECIMALS, False) == 60 * 10**36

    green_budget = 100 * EIGHTEEN_DECIMALS
    alice_green_before = _fund_alice(green_token, whale, teller, alice, green_budget)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    green_spent = redeem_collateral(
        teller,
        bob,
        vault_id,
        bravo_token,
        green_budget,
        should_refund_savings_green=False,
        sender=alice,
    )

    assert green_spent == 1
    logs = filter_logs(teller, "CollateralRedeemed")
    assert len(logs) == 1
    log = logs[0]
    assert log.amount == bravo_amount
    assert log.repayValue == 1
    assert log.user == bob
    assert log.recipient == alice

    assert bravo_token.balanceOf(alice) == bravo_amount
    assert simple_erc20_vault.getTotalAmountForUser(bob, bravo_token) == 0
    assert green_token.balanceOf(alice) == alice_green_before - 1

    user_debt, _, _ = credit_engine.getLatestUserDebtAndTerms(bob, False)
    assert user_debt.amount == 100 * EIGHTEEN_DECIMALS - 1


def test_credit_redeem_credits_forward_value_of_zero_decimal_delivery(
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
    _make_bob_redeemable_on_poisoned_bravo(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        credit_engine,
        bob,
        alpha_token,
        alpha_token_whale,
        coarse_token,
        governance.address,
        1,
    )
    mock_price_source.setPrice(alpha_token, 62 * EIGHTEEN_DECIMALS // 100)
    mock_price_source.setPrice(coarse_token, 3 * EIGHTEEN_DECIMALS)
    assert credit_engine.canRedeemUserCollateral(bob)

    _fund_alice(green_token, whale, teller, alice, 5 * EIGHTEEN_DECIMALS)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    green_spent = redeem_collateral(
        teller,
        bob,
        vault_id,
        coarse_token,
        5 * EIGHTEEN_DECIMALS,
        should_refund_savings_green=False,
        sender=alice,
    )

    assert green_spent == 3 * EIGHTEEN_DECIMALS
    log = filter_logs(teller, "CollateralRedeemed")[0]
    assert log.amount == 1
    assert log.repayValue == 3 * EIGHTEEN_DECIMALS
    assert coarse_token.balanceOf(alice) == 1


def test_credit_redeem_multi_token_payment_scales_by_whole_tokens(
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
    _make_bob_redeemable_on_poisoned_bravo(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        credit_engine,
        bob,
        alpha_token,
        alpha_token_whale,
        bravo_token,
        bravo_token_whale,
        bravo_amount,
    )
    green_budget = 100 * EIGHTEEN_DECIMALS
    alice_green_before = _fund_alice(green_token, whale, teller, alice, green_budget)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    green_spent = redeem_collateral(
        teller,
        bob,
        vault_id,
        bravo_token,
        green_budget,
        should_refund_savings_green=False,
        sender=alice,
    )
    assert green_spent == 100
    logs = filter_logs(teller, "CollateralRedeemed")
    assert len(logs) == 1
    assert logs[0].amount == bravo_amount
    assert logs[0].repayValue == 100
    assert bravo_token.balanceOf(alice) == bravo_amount
    assert simple_erc20_vault.getTotalAmountForUser(bob, bravo_token) == 0
    assert green_token.balanceOf(alice) == alice_green_before - 100


def test_credit_redeem_one_wei_takes_one_token_from_multi_token_balance(
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
    _make_bob_redeemable_on_poisoned_bravo(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        credit_engine,
        bob,
        alpha_token,
        alpha_token_whale,
        bravo_token,
        bravo_token_whale,
        bravo_amount,
    )
    alice_green_before = _fund_alice(green_token, whale, teller, alice, 1)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    green_spent = redeem_collateral(
        teller,
        bob,
        vault_id,
        bravo_token,
        1,
        should_refund_savings_green=False,
        sender=alice,
    )
    assert green_spent == 1
    logs = filter_logs(teller, "CollateralRedeemed")
    assert logs[0].amount == EIGHTEEN_DECIMALS
    assert logs[0].repayValue == 1
    assert bravo_token.balanceOf(alice) == EIGHTEEN_DECIMALS
    assert simple_erc20_vault.getTotalAmountForUser(bob, bravo_token) == 99 * EIGHTEEN_DECIMALS
    assert green_token.balanceOf(alice) == alice_green_before - 1


def test_credit_redeem_sub_token_reverts_whole_tx(
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    credit_redeem,
    bob,
    alice,
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
    _make_bob_redeemable_on_poisoned_bravo(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        credit_engine,
        bob,
        alpha_token,
        alpha_token_whale,
        bravo_token,
        bravo_token_whale,
        bravo_amount,
    )
    _fund_alice(green_token, whale, teller, alice, 100 * EIGHTEEN_DECIMALS)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    before = _snapshot_dust_state(
        credit_engine,
        green_token,
        credit_redeem,
        teller,
        bravo_token,
        simple_erc20_vault,
        lootbox,
        vault_id,
        bob,
        alice,
    )
    with boa.reverts("no redemptions occurred"):
        redeem_collateral(
            teller,
            bob,
            vault_id,
            bravo_token,
            100 * EIGHTEEN_DECIMALS,
            should_refund_savings_green=False,
            sender=alice,
        )
    after = _snapshot_dust_state(
        credit_engine,
        green_token,
        credit_redeem,
        teller,
        bravo_token,
        simple_erc20_vault,
        lootbox,
        vault_id,
        bob,
        alice,
    )
    assert after == before
    assert after["credit_redeem_green"] == 0
    assert filter_logs(teller, "CollateralRedeemed") == []


@pytest.mark.parametrize("dust_first", [True, False], ids=["dust-first", "dust-last"])
@pytest.mark.parametrize(
    "should_transfer_balance",
    [False, True],
    ids=["withdraw", "transfer"],
)
def test_credit_redeem_mixed_batch_skips_dust_keeps_healthy(
    dust_first,
    should_transfer_balance,
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
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    green_token,
    whale,
    simple_erc20_vault,
    vault_book,
    lootbox,
    price_desk,
):
    dust_amount = EIGHTEEN_DECIMALS // 2
    _make_bob_redeemable_on_poisoned_bravo(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        credit_engine,
        bob,
        alpha_token,
        alpha_token_whale,
        bravo_token,
        bravo_token_whale,
        dust_amount,
    )
    vault = simple_erc20_vault
    vault_id = vault_book.getRegId(vault)
    healthy_repayment = 10 * EIGHTEEN_DECIMALS
    total_budget = 100 * EIGHTEEN_DECIMALS
    expected_alpha = price_desk.getAssetAmount(alpha_token, healthy_repayment, False)
    alice_green_before = _fund_alice(green_token, whale, teller, alice, total_budget)

    before = {
        "debt": credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount,
        "green_supply": green_token.totalSupply(),
        "bob_alpha": vault.getTotalAmountForUser(bob, alpha_token),
        "bob_bravo": vault.getTotalAmountForUser(bob, bravo_token),
        "bob_has_bravo": vault.doesUserHaveBalance(bob, bravo_token),
        "bob_num_assets": vault.getNumUserAssets(bob),
        "alice_alpha_ext": alpha_token.balanceOf(alice),
        "alice_bravo_ext": bravo_token.balanceOf(alice),
        "bob_alpha_internal": vault.userBalances(bob, alpha_token),
        "bob_bravo_internal": vault.userBalances(bob, bravo_token),
        "alice_alpha_internal": vault.userBalances(alice, alpha_token),
        "alice_bravo_internal": vault.userBalances(alice, bravo_token),
        "vault_alpha_tokens": alpha_token.balanceOf(vault),
        "vault_bravo_tokens": bravo_token.balanceOf(vault),
        "bob_bravo_points": lootbox.getLatestDepositPoints(bob, vault_id, bravo_token),
        "alice_bravo_points": lootbox.getLatestDepositPoints(alice, vault_id, bravo_token),
        "bob_alpha_points": lootbox.getLatestDepositPoints(bob, vault_id, alpha_token),
        "alice_alpha_points": lootbox.getLatestDepositPoints(alice, vault_id, alpha_token),
    }

    dust_entry = (bob, vault_id, bravo_token.address, MAX_UINT256)
    healthy_entry = (bob, vault_id, alpha_token.address, healthy_repayment)
    redemptions = [dust_entry, healthy_entry] if dust_first else [healthy_entry, dust_entry]

    spent = teller.redeemCollateralFromMany(
        redemptions,
        total_budget,
        False,
        should_transfer_balance,
        False,
        alice,
        sender=alice,
    )

    assert spent == healthy_repayment
    assert spent < total_budget
    assert credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount == before["debt"] - spent
    assert green_token.balanceOf(alice) == alice_green_before - spent
    assert green_token.totalSupply() == before["green_supply"] - spent

    assert vault.getTotalAmountForUser(bob, bravo_token) == before["bob_bravo"] == dust_amount
    assert vault.doesUserHaveBalance(bob, bravo_token) == before["bob_has_bravo"]
    assert vault.getNumUserAssets(bob) == before["bob_num_assets"]
    assert vault.userBalances(bob, bravo_token) == before["bob_bravo_internal"]
    assert bravo_token.balanceOf(vault) == before["vault_bravo_tokens"]
    assert bravo_token.balanceOf(alice) == before["alice_bravo_ext"]
    assert lootbox.getLatestDepositPoints(bob, vault_id, bravo_token) == before["bob_bravo_points"]
    assert lootbox.getLatestDepositPoints(alice, vault_id, bravo_token) == before["alice_bravo_points"]

    logs = filter_logs(teller, "CollateralRedeemed")
    assert [lg.asset for lg in logs] == [alpha_token.address]
    assert logs[0].amount == expected_alpha
    assert logs[0].repayValue == spent
    assert logs[0].user == bob
    assert logs[0].recipient == alice

    assert vault.getTotalAmountForUser(bob, alpha_token) == before["bob_alpha"] - expected_alpha
    if should_transfer_balance:
        assert alpha_token.balanceOf(alice) == before["alice_alpha_ext"]
        assert alpha_token.balanceOf(vault) == before["vault_alpha_tokens"]
        assert vault.userBalances(bob, alpha_token) == before["bob_alpha_internal"] - expected_alpha
        assert vault.userBalances(alice, alpha_token) == before["alice_alpha_internal"] + expected_alpha
        assert vault.userBalances(alice, bravo_token) == before["alice_bravo_internal"]
        assert lootbox.getLatestDepositPoints(bob, vault_id, alpha_token) != before["bob_alpha_points"]
        assert lootbox.getLatestDepositPoints(alice, vault_id, alpha_token) != before["alice_alpha_points"]
    else:
        assert alpha_token.balanceOf(alice) == before["alice_alpha_ext"] + expected_alpha
        assert alpha_token.balanceOf(vault) == before["vault_alpha_tokens"] - expected_alpha
        assert vault.userBalances(alice, alpha_token) == before["alice_alpha_internal"]


def test_credit_redeem_rebase_vault_preview_skips_zero_credit(
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
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    green_token,
    whale,
    rebase_erc20_vault,
    vault_book,
    price_desk,
):
    vault = rebase_erc20_vault
    vault_id = vault_book.getRegId(vault)
    dust_amount = EIGHTEEN_DECIMALS // 2
    _make_bob_redeemable_on_poisoned_bravo(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        credit_engine,
        bob,
        alpha_token,
        alpha_token_whale,
        bravo_token,
        bravo_token_whale,
        dust_amount,
        vault=vault,
        vault_ids=[vault_id],
    )

    assert vault.getTotalAmountForUser(bob, bravo_token) == dust_amount
    dust_shares = vault.userBalances(bob, bravo_token)
    dust_vault_tokens = bravo_token.balanceOf(vault)
    healthy_repayment = 10 * EIGHTEEN_DECIMALS
    total_budget = 100 * EIGHTEEN_DECIMALS
    expected_alpha = price_desk.getAssetAmount(alpha_token, healthy_repayment, False)
    alice_green_before = _fund_alice(green_token, whale, teller, alice, total_budget)
    green_supply_before = green_token.totalSupply()
    debt_before = credit_engine.getUserDebtAmount(bob)
    vault_alpha_before = alpha_token.balanceOf(vault)
    alice_alpha_before = alpha_token.balanceOf(alice)

    spent = teller.redeemCollateralFromMany(
        [
            (bob, vault_id, bravo_token.address, MAX_UINT256),
            (bob, vault_id, alpha_token.address, healthy_repayment),
        ],
        total_budget,
        False,
        False,
        False,
        alice,
        sender=alice,
    )

    assert spent == healthy_repayment
    assert vault.getTotalAmountForUser(bob, bravo_token) == dust_amount
    assert vault.userBalances(bob, bravo_token) == dust_shares
    assert bravo_token.balanceOf(vault) == dust_vault_tokens
    assert green_token.balanceOf(alice) == alice_green_before - spent
    assert green_token.totalSupply() == green_supply_before - spent
    assert credit_engine.getUserDebtAmount(bob) == debt_before - spent

    logs = filter_logs(teller, "CollateralRedeemed")
    assert [lg.asset for lg in logs] == [alpha_token.address]
    assert logs[0].amount == expected_alpha
    assert logs[0].repayValue == spent
    assert alpha_token.balanceOf(alice) == alice_alpha_before + expected_alpha
    assert alpha_token.balanceOf(vault) == vault_alpha_before - expected_alpha
    assert bravo_token.balanceOf(alice) == 0


@pytest.mark.parametrize(
    "price,under_send,payment_amount,zero_forward_price",
    [
        (1, EIGHTEEN_DECIMALS // 2, 100 * EIGHTEEN_DECIMALS, False),
        # The vault changes the source after the inverse quote. With a one-wei
        # target, zero must be rejected before target-1 normalization.
        (EIGHTEEN_DECIMALS, 1, 1, True),
    ],
)
def test_credit_redeem_registered_under_send_reverts_atomically(
    price,
    under_send,
    payment_amount,
    zero_forward_price,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    credit_redeem,
    ledger,
    lootbox,
    vault_book,
    governance,
    bob,
    alice,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    green_token,
    whale,
    price_desk,
):
    setGeneralConfig()
    debt_terms = _redeem_terms(createDebtTerms)
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()

    mock = boa.loads(UNDER_SEND_VAULT_SOURCE, name="cr_under_send_vault")
    assert vault_book.startAddNewAddressToRegistry(
        mock, "cr under-send vault", sender=governance.address
    )
    boa.env.time_travel(blocks=vault_book.registryChangeTimeLock() + 1)
    mock_vault_id = vault_book.confirmNewAddressToRegistry(mock, sender=governance.address)
    assert vault_book.getAddr(mock_vault_id) == mock.address
    setAssetConfig(bravo_token, _debtTerms=debt_terms, _vaultIds=[mock_vault_id])

    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    performDeposit(bob, 200 * EIGHTEEN_DECIMALS, alpha_token, alpha_token_whale)
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    mock_price_source.setPrice(alpha_token, 70 * EIGHTEEN_DECIMALS // 100)
    mock_price_source.setPrice(bravo_token, price)

    reported = EIGHTEEN_DECIMALS
    source_to_zero = mock_price_source.address if zero_forward_price else ZERO_ADDRESS
    mock.configure(bravo_token.address, bob, reported, under_send, source_to_zero)
    # The raw value is below one USD wei, while PriceDesk deliberately returns
    # one; the amount-domain guard must still reject the vault under-send.
    assert price_desk.getUsdValue(bravo_token, under_send, True) == 1
    ledger.addVaultToUser(bob, mock_vault_id, sender=teller.address)
    assert credit_engine.canRedeemUserCollateral(bob)
    assert mock.getTotalAmountForUser(bob, bravo_token) == reported

    _fund_alice(green_token, whale, teller, alice, 100 * EIGHTEEN_DECIMALS)
    before = {
        "debt": credit_engine.getLatestUserDebtAndTerms(bob, False)[0].amount,
        "principal": credit_engine.getLatestUserDebtAndTerms(bob, False)[0].principal,
        "alice_green": green_token.balanceOf(alice),
        "alice_allowance": green_token.allowance(alice, teller),
        "credit_redeem_green": green_token.balanceOf(credit_redeem),
        "green_supply": green_token.totalSupply(),
        "bob_mock": mock.balances(bob),
        "alice_mock": mock.balances(alice),
        "bob_points": lootbox.getLatestDepositPoints(bob, mock_vault_id, bravo_token),
        "alice_points": lootbox.getLatestDepositPoints(alice, mock_vault_id, bravo_token),
    }

    with boa.reverts("zero repayment value (vault under-send)"):
        teller.redeemCollateralFromMany(
            [(bob, mock_vault_id, bravo_token.address, MAX_UINT256)],
            payment_amount,
            False,
            True,
            False,
            alice,
            sender=alice,
        )

    after_debt = credit_engine.getLatestUserDebtAndTerms(bob, False)[0]
    assert after_debt.amount == before["debt"]
    assert after_debt.principal == before["principal"]
    assert green_token.balanceOf(alice) == before["alice_green"]
    assert green_token.allowance(alice, teller) == before["alice_allowance"]
    assert green_token.balanceOf(credit_redeem) == before["credit_redeem_green"] == 0
    assert green_token.totalSupply() == before["green_supply"]
    assert mock.balances(bob) == before["bob_mock"] == reported
    assert mock.balances(alice) == before["alice_mock"] == 0
    assert lootbox.getLatestDepositPoints(bob, mock_vault_id, bravo_token) == before["bob_points"]
    assert lootbox.getLatestDepositPoints(alice, mock_vault_id, bravo_token) == before["alice_points"]
    assert filter_logs(teller, "CollateralRedeemed") == []


def test_wsuper_price_desk_credit_redeem_tx(
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
        name="wsuper_cr_e2e",
    )
    assert price_desk.startAddNewAddressToRegistry(src, "wsuper e2e", sender=governance.address)
    boa.env.time_travel(blocks=price_desk.registryChangeTimeLock() + 1)
    wsuper_id = price_desk.confirmNewAddressToRegistry(src, sender=governance.address)
    mock_price_source.setPrice(bravo_token, 0)
    mission_control.setPriorityPriceSourceIds([wsuper_id], sender=switchboard_alpha.address)
    assert src.getPriceAndHasFeed(bravo_token) == (0, False)
    assert price_desk.getPrice(bravo_token) == 0

    _make_bob_redeemable_on_poisoned_bravo(
        setGeneralConfig,
        setAssetConfig,
        setGeneralDebtConfig,
        createDebtTerms,
        performDeposit,
        mock_price_source,
        teller,
        credit_engine,
        bob,
        alpha_token,
        alpha_token_whale,
        bravo_token,
        bravo_token_whale,
        EIGHTEEN_DECIMALS,
    )
    mock_price_source.setPrice(bravo_token, 0)
    mission_control.setPriorityPriceSourceIds([wsuper_id], sender=switchboard_alpha.address)
    assert price_desk.getPrice(bravo_token) == 0
    _fund_alice(green_token, whale, teller, alice, 100 * EIGHTEEN_DECIMALS)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    with boa.reverts("no redemptions occurred"):
        redeem_collateral(
            teller,
            bob,
            vault_id,
            bravo_token,
            100 * EIGHTEEN_DECIMALS,
            should_refund_savings_green=False,
            sender=alice,
        )
    assert simple_erc20_vault.getTotalAmountForUser(bob, bravo_token) == EIGHTEEN_DECIMALS
    assert bravo_token.balanceOf(alice) == 0

    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    mission_control.setPriorityPriceSourceIds([6], sender=switchboard_alpha.address)
    assert price_desk.getPrice(bravo_token) == EIGHTEEN_DECIMALS
