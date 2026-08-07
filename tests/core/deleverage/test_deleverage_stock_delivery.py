"""Track 8 M4 composed stock delivery proof for unchanged Deleverage ordering."""

import boa

from conf_utils import filter_logs
from constants import EIGHTEEN_DECIMALS
from tests.vaults.test_basic_vault_safety import (
    _register_safe_nominal_vault,
    safe_simple_erc20_vault,
)


SHORT_ON_TELLER_TOKEN_SOURCE = """
# @version 0.4.3

balances: HashMap[address, uint256]
allowances: HashMap[address, HashMap[address, uint256]]
short_operator: public(address)

@external
def configure_short_operator(_operator: address):
    self.short_operator = _operator

@external
def mint(_to: address, _amount: uint256):
    self.balances[_to] += _amount

@view
@external
def balanceOf(_holder: address) -> uint256:
    return self.balances[_holder]

@view
@external
def decimals() -> uint8:
    return 18

@view
@external
def allowance(_owner: address, _spender: address) -> uint256:
    return self.allowances[_owner][_spender]

@external
def approve(_spender: address, _amount: uint256) -> bool:
    self.allowances[msg.sender][_spender] = _amount
    return True

@internal
def _move(_from: address, _to: address, _amount: uint256) -> bool:
    self.balances[_from] -= _amount
    received: uint256 = _amount
    if msg.sender == self.short_operator:
        received -= 1
    self.balances[_to] += received
    return True

@external
def transfer(_to: address, _amount: uint256) -> bool:
    return self._move(msg.sender, _to, _amount)

@external
def transferFrom(_from: address, _to: address, _amount: uint256) -> bool:
    allowed: uint256 = self.allowances[_from][msg.sender]
    self.allowances[_from][msg.sender] = allowed - _amount
    return self._move(_from, _to, _amount)
"""


def _configure_swap_assets(
    tokens,
    vault_id,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    mock_price_source,
    green_token,
):
    setGeneralConfig()
    setGeneralDebtConfig()
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=60_00,
        _liqThreshold=80_00,
        _liqFee=10_00,
        _borrowRate=0,
    )
    for token in tokens:
        setAssetConfig(
            token,
            _vaultIds=[vault_id],
            _debtTerms=debt_terms,
            _shouldBurnAsPayment=False,
            _shouldTransferToEndaoment=False,
            _shouldSwapInStabPools=False,
        )
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)
    return debt_terms


def _swap_state(
    vault,
    withdraw_token,
    deposit_token,
    deleverage,
    ledger,
    user,
    governance,
):
    debt = ledger.userDebt(user)
    return (
        withdraw_token.balanceOf(vault),
        withdraw_token.balanceOf(governance),
        withdraw_token.balanceOf(deleverage),
        deposit_token.balanceOf(vault),
        deposit_token.balanceOf(governance),
        deposit_token.balanceOf(deleverage),
        vault.userBalances(user, withdraw_token),
        vault.userBalances(user, deposit_token),
        vault.totalBalances(withdraw_token),
        vault.totalBalances(deposit_token),
        debt.amount,
        debt.inLiquidation,
        ledger.getNumUserVaults(user),
        ledger.lastTouch(user),
    )


def _credit_engine_recorder():
    return boa.loads(
        """# @version 0.4.3

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

count: public(uint256)
lastUser: public(address)
lastHq: public(address)

@external
def updateDebtForUser(_user: address, _a: Addys) -> bool:
    self.count += 1
    self.lastUser = _user
    self.lastHq = _a.hq
    return True
""",
        name="deleverage_housekeeping_credit_engine_recorder",
    )


def test_standard_swap_delivers_withdrawal_and_exact_teller_deposit(
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    green_token,
    bob,
    teller,
    deleverage,
    mock_price_source,
    ledger,
    safe_simple_erc20_vault,
    vault_book,
    governance,
):
    vault_id = _register_safe_nominal_vault(
        vault_book,
        governance,
        safe_simple_erc20_vault,
    )
    _configure_swap_assets(
        (alpha_token, bravo_token),
        vault_id,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
        mock_price_source,
        green_token,
    )
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    debt_amount = 25 * EIGHTEEN_DECIMALS
    swap_amount = 40 * EIGHTEEN_DECIMALS
    performDeposit(
        bob,
        deposit_amount,
        alpha_token,
        alpha_token_whale,
        safe_simple_erc20_vault,
    )
    teller.borrow(debt_amount, bob, False, sender=bob)
    bravo_token.transfer(
        governance,
        swap_amount,
        sender=bravo_token_whale,
    )
    bravo_token.approve(
        deleverage,
        swap_amount,
        sender=governance.address,
    )

    governance_alpha_before = alpha_token.balanceOf(governance)
    governance_bravo_before = bravo_token.balanceOf(governance)
    custody_alpha_before = alpha_token.balanceOf(safe_simple_erc20_vault)
    custody_bravo_before = bravo_token.balanceOf(safe_simple_erc20_vault)
    touch_before = ledger.lastTouch(bob)
    boa.env.time_travel(blocks=1)

    withdrawn, deposited = deleverage.swapCollateral(
        bob,
        vault_id,
        alpha_token,
        vault_id,
        bravo_token,
        swap_amount,
        sender=governance.address,
    )

    assert withdrawn == deposited == swap_amount
    assert alpha_token.balanceOf(governance) - governance_alpha_before == withdrawn
    assert governance_bravo_before - bravo_token.balanceOf(governance) == deposited
    assert custody_alpha_before - alpha_token.balanceOf(
        safe_simple_erc20_vault
    ) == withdrawn
    assert bravo_token.balanceOf(
        safe_simple_erc20_vault
    ) - custody_bravo_before == deposited
    assert safe_simple_erc20_vault.userBalances(
        bob,
        alpha_token,
    ) == deposit_amount - withdrawn
    assert safe_simple_erc20_vault.userBalances(bob, bravo_token) == deposited
    assert ledger.userDebt(bob).amount == debt_amount
    assert ledger.lastTouch(bob) > touch_before

    teller_deposits = filter_logs(deleverage, "TellerDeposit")
    withdrawals = filter_logs(
        deleverage,
        "SimpleErc20VaultWithdrawal",
    )
    standard_deposits = filter_logs(
        deleverage,
        "SimpleErc20VaultDeposit",
    )
    swaps = filter_logs(deleverage, "CollateralSwapped")
    assert len(teller_deposits) == len(withdrawals) == len(standard_deposits) == 1
    assert len(swaps) == 1
    assert teller_deposits[0].amount == deposited
    assert teller_deposits[0].vaultAddr == safe_simple_erc20_vault.address
    assert teller_deposits[0].vaultId == vault_id
    assert withdrawals[0].amount == withdrawn
    assert standard_deposits[0].amount == deposited
    assert swaps[0].withdrawAmount == withdrawn
    assert swaps[0].depositAmount == deposited


def test_deleverage_swap_housekeeping_uses_user_low_risk_and_updates_debt(
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    green_token,
    bob,
    alice,
    teller,
    deleverage,
    mock_price_source,
    ledger,
    safe_simple_erc20_vault,
    vault_book,
    governance,
    ripe_hq,
):
    vault_id = _register_safe_nominal_vault(
        vault_book,
        governance,
        safe_simple_erc20_vault,
    )
    _configure_swap_assets(
        (alpha_token, bravo_token),
        vault_id,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
        mock_price_source,
        green_token,
    )
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    debt_amount = 25 * EIGHTEEN_DECIMALS
    swap_amount = 10 * EIGHTEEN_DECIMALS
    performDeposit(
        bob,
        deposit_amount,
        alpha_token,
        alpha_token_whale,
        safe_simple_erc20_vault,
    )
    teller.borrow(debt_amount, bob, False, sender=bob)
    bravo_token.transfer(governance, 2 * swap_amount, sender=bravo_token_whale)
    bravo_token.approve(deleverage, 2 * swap_amount, sender=governance.address)
    recorder = _credit_engine_recorder()
    ripe_hq.startAddressUpdateToRegistry(13, recorder, sender=governance.address)
    boa.env.time_travel(blocks=ripe_hq.registryChangeTimeLock())
    assert ripe_hq.confirmAddressUpdateToRegistry(13, sender=governance.address)
    decoy_touch = ledger.lastTouch(alice)

    first = deleverage.swapCollateral(
        bob,
        vault_id,
        alpha_token,
        vault_id,
        bravo_token,
        swap_amount,
        sender=governance.address,
    )
    action_block = ledger.lastTouch(bob)
    assert first == (swap_amount, swap_amount)
    assert action_block == boa.env.evm.patch.block_number
    assert recorder.count() == 1
    assert recorder.lastUser() == bob
    assert recorder.lastHq() == ripe_hq.address
    assert ledger.lastTouch(alice) == decoy_touch

    second = deleverage.swapCollateral(
        bob,
        vault_id,
        alpha_token,
        vault_id,
        bravo_token,
        swap_amount,
        sender=governance.address,
    )
    assert second == (swap_amount, swap_amount)
    assert ledger.lastTouch(bob) == action_block
    assert ledger.lastTouch(alice) == decoy_touch
    assert recorder.count() == 2
    assert recorder.lastUser() == bob


def test_teller_exact_receipt_is_decisive_after_standard_withdrawal(
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    green_token,
    bob,
    teller,
    deleverage,
    mock_price_source,
    ledger,
    safe_simple_erc20_vault,
    simple_erc20_vault,
    vault_book,
    governance,
):
    short_token = boa.loads(
        SHORT_ON_TELLER_TOKEN_SOURCE,
        name="m4_short_on_teller_token",
        override_address=boa.env.generate_address(),
    )
    short_token.configure_short_operator(teller)
    vault_id = _register_safe_nominal_vault(
        vault_book,
        governance,
        safe_simple_erc20_vault,
    )
    simple_vault_id = vault_book.getRegId(simple_erc20_vault)
    setGeneralConfig()
    setGeneralDebtConfig()
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=60_00,
        _liqThreshold=80_00,
        _liqFee=10_00,
        _borrowRate=0,
    )
    setAssetConfig(
        alpha_token,
        _vaultIds=[vault_id],
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=False,
    )
    setAssetConfig(
        short_token,
        _vaultIds=[simple_vault_id],
        _debtTerms=debt_terms,
        _shouldBurnAsPayment=False,
        _shouldTransferToEndaoment=False,
        _shouldSwapInStabPools=False,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(short_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(green_token, EIGHTEEN_DECIMALS)
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    debt_amount = 25 * EIGHTEEN_DECIMALS
    swap_amount = 40 * EIGHTEEN_DECIMALS
    performDeposit(
        bob,
        deposit_amount,
        alpha_token,
        alpha_token_whale,
        safe_simple_erc20_vault,
    )
    teller.borrow(debt_amount, bob, False, sender=bob)
    short_token.mint(simple_erc20_vault, 1)
    short_token.mint(governance, swap_amount)
    short_token.approve(
        deleverage,
        swap_amount,
        sender=governance.address,
    )
    debt = ledger.userDebt(bob)
    before = (
        alpha_token.balanceOf(safe_simple_erc20_vault),
        alpha_token.balanceOf(governance),
        alpha_token.balanceOf(deleverage),
        short_token.balanceOf(simple_erc20_vault),
        short_token.balanceOf(governance),
        short_token.balanceOf(deleverage),
        safe_simple_erc20_vault.userBalances(bob, alpha_token),
        safe_simple_erc20_vault.totalBalances(alpha_token),
        simple_erc20_vault.userBalances(bob, short_token),
        simple_erc20_vault.totalBalances(short_token),
        debt.amount,
        debt.inLiquidation,
        ledger.getNumUserVaults(bob),
        ledger.isParticipatingInVault(bob, vault_id),
        ledger.isParticipatingInVault(bob, simple_vault_id),
        ledger.lastTouch(bob),
    )

    with boa.reverts():
        deleverage.swapCollateral(
            bob,
            vault_id,
            alpha_token,
            simple_vault_id,
            short_token,
            swap_amount,
            sender=governance.address,
        )

    debt = ledger.userDebt(bob)
    assert (
        alpha_token.balanceOf(safe_simple_erc20_vault),
        alpha_token.balanceOf(governance),
        alpha_token.balanceOf(deleverage),
        short_token.balanceOf(simple_erc20_vault),
        short_token.balanceOf(governance),
        short_token.balanceOf(deleverage),
        safe_simple_erc20_vault.userBalances(bob, alpha_token),
        safe_simple_erc20_vault.totalBalances(alpha_token),
        simple_erc20_vault.userBalances(bob, short_token),
        simple_erc20_vault.totalBalances(short_token),
        debt.amount,
        debt.inLiquidation,
        ledger.getNumUserVaults(bob),
        ledger.isParticipatingInVault(bob, vault_id),
        ledger.isParticipatingInVault(bob, simple_vault_id),
        ledger.lastTouch(bob),
    ) == before


def test_standard_destination_deficit_rolls_back_both_swap_legs(
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    green_token,
    bob,
    alice,
    teller,
    deleverage,
    credit_engine,
    mock_price_source,
    ledger,
    safe_simple_erc20_vault,
    vault_book,
    governance,
):
    vault_id = _register_safe_nominal_vault(
        vault_book,
        governance,
        safe_simple_erc20_vault,
    )
    debt_terms = _configure_swap_assets(
        (alpha_token, bravo_token),
        vault_id,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
        mock_price_source,
        green_token,
    )
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    debt_amount = 25 * EIGHTEEN_DECIMALS
    swap_amount = 40 * EIGHTEEN_DECIMALS
    performDeposit(
        bob,
        deposit_amount,
        alpha_token,
        alpha_token_whale,
        safe_simple_erc20_vault,
    )
    performDeposit(
        alice,
        20 * EIGHTEEN_DECIMALS,
        bravo_token,
        bravo_token_whale,
        safe_simple_erc20_vault,
    )
    teller.borrow(debt_amount, bob, False, sender=bob)
    bravo_token.burn(1, sender=safe_simple_erc20_vault.address)
    assert safe_simple_erc20_vault.getUserAssetAndAmountAtIndex(alice, 1) == (
        bravo_token.address,
        0,
    )
    alice_terms = credit_engine.getUserBorrowTerms(alice, True)
    assert alice_terms.collateralVal == 0
    assert alice_terms.totalMaxDebt == 0
    assert alice_terms.debtTerms.ltv == debt_terms[0]
    assert alice_terms.debtTerms.liqThreshold == debt_terms[2]

    bravo_token.transfer(
        governance,
        swap_amount,
        sender=bravo_token_whale,
    )
    bravo_token.approve(
        deleverage,
        swap_amount,
        sender=governance.address,
    )
    before = _swap_state(
        safe_simple_erc20_vault,
        alpha_token,
        bravo_token,
        deleverage,
        ledger,
        bob,
        governance,
    ) + (
        safe_simple_erc20_vault.userBalances(alice, bravo_token),
    )

    with boa.reverts():
        deleverage.swapCollateral(
            bob,
            vault_id,
            alpha_token,
            vault_id,
            bravo_token,
            swap_amount,
            sender=governance.address,
        )

    after = _swap_state(
        safe_simple_erc20_vault,
        alpha_token,
        bravo_token,
        deleverage,
        ledger,
        bob,
        governance,
    ) + (
        safe_simple_erc20_vault.userBalances(alice, bravo_token),
    )
    assert after == before
    assert ledger.userDebt(bob).amount == debt_amount


def test_safe_nominal_volatile_deleverage_can_deliver_to_endaoment_funds(
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    green_token,
    bob,
    teller,
    deleverage,
    credit_engine,
    switchboard_alpha,
    mock_price_source,
    ledger,
    safe_simple_erc20_vault,
    vault_book,
    governance,
    endaoment_funds,
):
    vault_id = _register_safe_nominal_vault(
        vault_book,
        governance,
        safe_simple_erc20_vault,
    )
    _configure_swap_assets(
        (alpha_token,),
        vault_id,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
        mock_price_source,
        green_token,
    )
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    debt_amount = 25 * EIGHTEEN_DECIMALS
    performDeposit(
        bob,
        deposit_amount,
        alpha_token,
        alpha_token_whale,
        safe_simple_erc20_vault,
    )
    teller.borrow(debt_amount, bob, False, sender=bob)
    transfer_amount = 10 * EIGHTEEN_DECIMALS
    funds_before = alpha_token.balanceOf(endaoment_funds)
    assert deleverage.deleverageWithVolAssets(
        bob,
        [(vault_id, alpha_token, transfer_amount)],
        sender=switchboard_alpha.address,
    ) == transfer_amount

    assert alpha_token.balanceOf(safe_simple_erc20_vault) == (
        deposit_amount - transfer_amount
    )
    assert alpha_token.balanceOf(endaoment_funds) == funds_before + transfer_amount
    assert safe_simple_erc20_vault.userBalances(bob, alpha_token) == (
        deposit_amount - transfer_amount
    )
    assert safe_simple_erc20_vault.totalBalances(alpha_token) == (
        deposit_amount - transfer_amount
    )
    assert credit_engine.getUserDebtAmount(bob) == debt_amount - transfer_amount
    assert not ledger.userDebt(bob).inLiquidation
    assert deleverage.lastDeleverageBlock(bob) == 0


def test_safe_nominal_volatile_deleverage_skips_deficit_and_continues(
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    performDeposit,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    green_token,
    bob,
    teller,
    deleverage,
    credit_engine,
    switchboard_alpha,
    mock_price_source,
    ledger,
    safe_simple_erc20_vault,
    vault_book,
    governance,
    endaoment_funds,
):
    vault_id = _register_safe_nominal_vault(
        vault_book,
        governance,
        safe_simple_erc20_vault,
    )
    _configure_swap_assets(
        (alpha_token, bravo_token),
        vault_id,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
        mock_price_source,
        green_token,
    )
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    debt_amount = 50 * EIGHTEEN_DECIMALS
    for token, whale_addr in (
        (alpha_token, alpha_token_whale),
        (bravo_token, bravo_token_whale),
    ):
        performDeposit(
            bob,
            deposit_amount,
            token,
            whale_addr,
            safe_simple_erc20_vault,
        )
    teller.borrow(debt_amount, bob, False, sender=bob)

    alpha_token.burn(1, sender=safe_simple_erc20_vault.address)
    target = 10 * EIGHTEEN_DECIMALS
    funds_before = bravo_token.balanceOf(endaoment_funds)

    repaid = deleverage.deleverageWithVolAssets(
        bob,
        [
            (vault_id, alpha_token.address, target),
            (vault_id, bravo_token.address, target),
        ],
        sender=switchboard_alpha.address,
    )

    assert repaid == target
    assert credit_engine.getUserDebtAmount(bob) == debt_amount - target
    assert safe_simple_erc20_vault.getTotalAmountForUser(bob, alpha_token) == 0
    assert safe_simple_erc20_vault.userBalances(bob, alpha_token) == deposit_amount
    assert alpha_token.balanceOf(safe_simple_erc20_vault) == deposit_amount - 1
    assert safe_simple_erc20_vault.userBalances(bob, bravo_token) == (
        deposit_amount - target
    )
    assert bravo_token.balanceOf(safe_simple_erc20_vault) == (
        deposit_amount - target
    )
    assert bravo_token.balanceOf(endaoment_funds) == funds_before + target
    assert not ledger.userDebt(bob).inLiquidation

    transfers = filter_logs(deleverage, "EndaomentTransferDuringDeleverage")
    withdrawals = filter_logs(deleverage, "SimpleErc20VaultWithdrawal")
    assert len(transfers) == len(withdrawals) == 1
    assert transfers[0].asset == bravo_token.address
    assert transfers[0].amountSent == target
    assert withdrawals[0].asset == bravo_token.address
    assert withdrawals[0].amount == target
