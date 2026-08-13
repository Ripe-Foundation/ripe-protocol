from types import SimpleNamespace

import boa
import pytest

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS
from conf_utils import filter_logs


LEGO_SOURCE = """
# @version 0.4.3

from ethereum.ercs import IERC20

interface Mintable:
    def mint(_to: address, _amount: uint256): nonpayable

LP_TOKEN: immutable(address)

returnedLpToken: public(address)
actualLpAmount: public(uint256)
reportedLpAmount: public(uint256)
lastRecipient: public(address)
deliverLpByTransfer: public(bool)

@deploy
def __init__(_lpToken: address):
    LP_TOKEN = _lpToken
    self.returnedLpToken = _lpToken
    self.actualLpAmount = 2
    self.reportedLpAmount = 2

@external
def configure(_returnedLpToken: address, _actualLpAmount: uint256, _reportedLpAmount: uint256):
    self.returnedLpToken = _returnedLpToken
    self.actualLpAmount = _actualLpAmount
    self.reportedLpAmount = _reportedLpAmount

@external
def setDeliverLpByTransfer(_shouldTransfer: bool):
    self.deliverLpByTransfer = _shouldTransfer

@view
@external
def getAddr(_id: uint256) -> address:
    return self

@view
@external
def isValidAddr(_addr: address) -> bool:
    return True

@external
def addLiquidity(
    _pool: address,
    _tokenA: address,
    _tokenB: address,
    _amountA: uint256,
    _amountB: uint256,
    _minAmountA: uint256,
    _minAmountB: uint256,
    _minLpAmount: uint256,
    _extraData: bytes32,
    _recipient: address,
) -> (address, uint256, uint256, uint256, uint256):
    assert extcall IERC20(_tokenA).transferFrom(msg.sender, self, _amountA)
    assert extcall IERC20(_tokenB).transferFrom(msg.sender, self, _amountB)
    assert self.reportedLpAmount >= _minLpAmount  # dev: insufficient lp amount

    self.lastRecipient = _recipient
    if self.actualLpAmount != 0:
        if self.deliverLpByTransfer:
            assert extcall IERC20(LP_TOKEN).transfer(_recipient, self.actualLpAmount)
        else:
            extcall Mintable(LP_TOKEN).mint(_recipient, self.actualLpAmount)

    return self.returnedLpToken, self.reportedLpAmount, _amountA, _amountB, 0
"""


ONE_ASSET = 10**6
ONE_GREEN = EIGHTEEN_DECIMALS
LEGO_ID = 1


@pytest.fixture
def partner_liquidity_env(
    endaoment,
    endaoment_funds,
    mission_control,
    switchboard_alpha,
    switchboard_delta,
    switchboard_echo,
    charlie_token,
    green_token,
    mock_price_source,
    ledger,
    governance,
    mock_registry,
    ripe_hq_deploy,
):
    lp_token = boa.load(
        "contracts/mock/MockErc20.vy",
        governance.address,
        "Partner LP",
        "PLP",
        18,
        0,
    )
    wrong_lp_token = boa.load(
        "contracts/mock/MockErc20.vy",
        governance.address,
        "Wrong LP",
        "WLP",
        18,
        0,
    )
    lego = boa.loads(LEGO_SOURCE, lp_token.address)
    lp_token.setMinter(lego.address, True, sender=governance.address)

    # Use distinct registry, Lego book, and admitted Lego layers without
    # changing the intentionally empty Robinhood production default.
    lego_book = boa.load(
        "contracts/mock/MockRegistry.vy",
        ripe_hq_deploy,
        mock_registry.registryChangeTimeLock(),
        mock_registry.minRegistryTimeLock(),
        mock_registry.maxRegistryTimeLock(),
        name="partner_liquidity_lego_book",
    )
    lego_book.startAddNewAddressToRegistry(
        lego.address,
        "Partner liquidity Lego",
        sender=governance.address,
    )
    boa.env.time_travel(blocks=lego_book.registryChangeTimeLock())
    assert lego_book.confirmNewAddressToRegistry(
        lego.address,
        sender=governance.address,
    ) == LEGO_ID

    # The top-level Underscore registry resolves the Lego book at registry ID 3.
    for target, description in (
        (lp_token.address, "Test registry placeholder one"),
        (wrong_lp_token.address, "Test registry placeholder two"),
        (lego_book.address, "Lego book"),
    ):
        mock_registry.startAddNewAddressToRegistry(
            target,
            description,
            sender=governance.address,
        )
    boa.env.time_travel(blocks=mock_registry.registryChangeTimeLock())
    assert mock_registry.confirmNewAddressToRegistry(
        lp_token.address,
        sender=governance.address,
    ) == 1
    assert mock_registry.confirmNewAddressToRegistry(
        wrong_lp_token.address,
        sender=governance.address,
    ) == 2
    assert mock_registry.confirmNewAddressToRegistry(
        lego_book.address,
        sender=governance.address,
    ) == 3
    assert mock_registry.getAddr(3) == lego_book.address
    assert lego_book.getAddr(LEGO_ID) == lego.address
    assert lego_book.isValidAddr(lego.address)

    mission_control.setUnderscoreRegistry(
        mock_registry.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(charlie_token.address, ONE_GREEN)

    return SimpleNamespace(
        endaoment=endaoment,
        endaoment_funds=endaoment_funds,
        switchboard_delta=switchboard_delta,
        switchboard_echo=switchboard_echo,
        asset=charlie_token,
        green=green_token,
        lp=lp_token,
        wrong_lp=wrong_lp_token,
        lego=lego,
        lego_book=lego_book,
        ledger=ledger,
        governance=governance,
    )


def _fund_partner(ctx, partner, amount=ONE_ASSET):
    ctx.asset.mint(partner, amount, sender=ctx.governance.address)
    ctx.asset.approve(ctx.endaoment.address, amount, sender=partner)


def _add_partner_liquidity(ctx, partner, amount=ONE_ASSET):
    return ctx.endaoment.addPartnerLiquidity(
        LEGO_ID,
        ctx.lp.address,
        partner,
        ctx.asset.address,
        amount,
        0,
        ctx.lp.address,
        sender=ctx.switchboard_delta.address,
    )


def test_partner_receives_only_current_action_share(
    partner_liquidity_env,
    alice,
):
    ctx = partner_liquidity_env
    ctx.lp.mint(ctx.endaoment_funds.address, 1_000, sender=ctx.governance.address)
    _fund_partner(ctx, alice)

    lp_received, _, _ = _add_partner_liquidity(ctx, alice)

    # The read-only pre-fix audit proof executes this same 1,000-plus-two setup
    # against the base contract and observes 501 LP paid to the partner. This
    # fixed-contract regression asserts the corrected side of that comparison.
    assert lp_received == 2
    assert ctx.lp.balanceOf(alice) == 1
    assert ctx.lp.balanceOf(ctx.endaoment_funds.address) == 1_001
    assert ctx.lp.balanceOf(ctx.endaoment.address) == 0
    assert filter_logs(ctx.endaoment, "PartnerLiquidityAdded")[0].lpBalance == 2


def test_sequential_partner_actions_do_not_redistribute_reserves(
    partner_liquidity_env,
    alice,
    bob,
):
    ctx = partner_liquidity_env
    ctx.lp.mint(ctx.endaoment_funds.address, 1_000, sender=ctx.governance.address)
    _fund_partner(ctx, alice)
    _fund_partner(ctx, bob)

    _add_partner_liquidity(ctx, alice)
    alice_after_first = ctx.lp.balanceOf(alice)
    _add_partner_liquidity(ctx, bob)

    assert alice_after_first == 1
    assert ctx.lp.balanceOf(alice) == alice_after_first
    assert ctx.lp.balanceOf(bob) == 1
    assert ctx.lp.balanceOf(ctx.endaoment_funds.address) == 1_002


def test_unsolicited_endaoment_lp_is_not_split_or_swept(
    partner_liquidity_env,
    alice,
):
    ctx = partner_liquidity_env
    ctx.lp.mint(ctx.endaoment.address, 73, sender=ctx.governance.address)
    ctx.lp.mint(ctx.endaoment_funds.address, 1_000, sender=ctx.governance.address)
    _fund_partner(ctx, alice)

    _add_partner_liquidity(ctx, alice)

    assert ctx.lp.balanceOf(ctx.endaoment.address) == 73
    assert ctx.lp.balanceOf(alice) == 1
    assert ctx.lp.balanceOf(ctx.endaoment_funds.address) == 1_001


def test_incorrect_returned_lp_token_reverts(
    partner_liquidity_env,
    alice,
):
    ctx = partner_liquidity_env
    ctx.lego.configure(ctx.wrong_lp.address, 2, 2)
    _fund_partner(ctx, alice)

    with boa.reverts("unexpected lp token"):
        _add_partner_liquidity(ctx, alice)


@pytest.mark.parametrize(
    ("actual_lp", "reported_lp"),
    [(2, 3), (3, 2)],
    ids=["over-reported", "under-reported-external-lp"],
)
def test_reported_lp_amount_must_match_exact_external_call_delta(
    partner_liquidity_env,
    alice,
    actual_lp,
    reported_lp,
):
    ctx = partner_liquidity_env
    ctx.lego.configure(ctx.lp.address, actual_lp, reported_lp)
    _fund_partner(ctx, alice)

    with boa.reverts("lp amount mismatch"):
        _add_partner_liquidity(ctx, alice)


def test_rebase_like_lp_balance_change_during_external_call_reverts(
    partner_liquidity_env,
    alice,
):
    """A balance increase beyond the Lego report cannot join this cohort."""
    ctx = partner_liquidity_env
    ctx.lp.mint(ctx.endaoment.address, 20, sender=ctx.governance.address)
    ctx.lego.configure(ctx.lp.address, 4, 2)
    _fund_partner(ctx, alice)

    with boa.reverts("lp amount mismatch"):
        _add_partner_liquidity(ctx, alice)

    assert ctx.lp.balanceOf(ctx.endaoment.address) == 20


def test_fee_on_transfer_lp_short_receipt_reverts_atomically(
    partner_liquidity_env,
    alice,
):
    ctx = partner_liquidity_env
    fee_lp = boa.load(
        "contracts/mock/MockFeeOnTransferErc20.vy",
        ctx.governance.address,
        5_000,  # 50% makes a two-unit transfer deliver exactly one unit.
        name="partner_fee_lp",
    )
    fee_lego = boa.loads(LEGO_SOURCE, fee_lp.address)
    fee_lego.setDeliverLpByTransfer(True)
    fee_lp.transfer(fee_lego.address, 10, sender=ctx.governance.address)

    ctx.lego_book.startAddressUpdateToRegistry(
        LEGO_ID,
        fee_lego.address,
        sender=ctx.governance.address,
    )
    boa.env.time_travel(blocks=ctx.lego_book.registryChangeTimeLock())
    assert ctx.lego_book.confirmAddressUpdateToRegistry(
        LEGO_ID,
        sender=ctx.governance.address,
    )
    _fund_partner(ctx, alice)

    balances_before = (
        fee_lp.balanceOf(fee_lego.address),
        fee_lp.balanceOf(ctx.endaoment.address),
        fee_lp.balanceOf(ctx.endaoment_funds.address),
        ctx.asset.balanceOf(alice),
        ctx.green.totalSupply(),
        ctx.ledger.greenPoolDebt(fee_lp.address),
    )
    with boa.reverts("lp amount mismatch"):
        ctx.endaoment.addPartnerLiquidity(
            LEGO_ID,
            fee_lp.address,
            alice,
            ctx.asset.address,
            ONE_ASSET,
            0,
            fee_lp.address,
            sender=ctx.switchboard_delta.address,
        )
    balances_after = (
        fee_lp.balanceOf(fee_lego.address),
        fee_lp.balanceOf(ctx.endaoment.address),
        fee_lp.balanceOf(ctx.endaoment_funds.address),
        ctx.asset.balanceOf(alice),
        ctx.green.totalSupply(),
        ctx.ledger.greenPoolDebt(fee_lp.address),
    )
    assert balances_after == balances_before


def test_minimum_lp_failure_reverts_atomically(
    partner_liquidity_env,
    alice,
):
    ctx = partner_liquidity_env
    _fund_partner(ctx, alice)
    balances_before = (
        ctx.asset.balanceOf(alice),
        ctx.asset.balanceOf(ctx.endaoment_funds.address),
        ctx.green.totalSupply(),
        ctx.ledger.greenPoolDebt(ctx.lp.address),
    )

    with boa.reverts("insufficient lp amount"):
        ctx.endaoment.addPartnerLiquidity(
            LEGO_ID,
            ctx.lp.address,
            alice,
            ctx.asset.address,
            ONE_ASSET,
            3,
            ctx.lp.address,
            sender=ctx.switchboard_delta.address,
        )

    balances_after = (
        ctx.asset.balanceOf(alice),
        ctx.asset.balanceOf(ctx.endaoment_funds.address),
        ctx.green.totalSupply(),
        ctx.ledger.greenPoolDebt(ctx.lp.address),
    )
    assert balances_after == balances_before


def test_zero_reported_lp_amount_reverts_cleanly(
    partner_liquidity_env,
    alice,
):
    ctx = partner_liquidity_env
    ctx.lego.configure(ctx.lp.address, 0, 0)
    _fund_partner(ctx, alice)

    with boa.reverts("no liquidity added"):
        _add_partner_liquidity(ctx, alice)


def test_odd_lp_output_favors_endaoment_funds(
    partner_liquidity_env,
    alice,
):
    ctx = partner_liquidity_env
    ctx.lego.configure(ctx.lp.address, 3, 3)
    _fund_partner(ctx, alice)

    _add_partner_liquidity(ctx, alice)

    assert ctx.lp.balanceOf(alice) == 1
    assert ctx.lp.balanceOf(ctx.endaoment_funds.address) == 2


def test_one_unit_lp_output_goes_entirely_to_endaoment_funds(
    partner_liquidity_env,
    alice,
):
    ctx = partner_liquidity_env
    ctx.lego.configure(ctx.lp.address, 1, 1)
    _fund_partner(ctx, alice)

    _add_partner_liquidity(ctx, alice)

    assert ctx.lp.balanceOf(alice) == 0
    assert ctx.lp.balanceOf(ctx.endaoment_funds.address) == 1


def test_endaoment_partner_returns_all_current_lp_to_funds(
    partner_liquidity_env,
):
    ctx = partner_liquidity_env
    ctx.asset.mint(
        ctx.endaoment.address,
        ONE_ASSET,
        sender=ctx.governance.address,
    )

    _add_partner_liquidity(ctx, ctx.endaoment.address)

    assert ctx.lp.balanceOf(ctx.endaoment.address) == 0
    assert ctx.lp.balanceOf(ctx.endaoment_funds.address) == 2


def test_validation_failure_rolls_back_all_accounting(
    partner_liquidity_env,
    alice,
):
    ctx = partner_liquidity_env
    ctx.lp.mint(ctx.endaoment.address, 13, sender=ctx.governance.address)
    ctx.lp.mint(ctx.endaoment_funds.address, 1_000, sender=ctx.governance.address)
    ctx.lego.configure(ctx.lp.address, 3, 2)
    _fund_partner(ctx, alice)

    balances_before = (
        ctx.asset.balanceOf(alice),
        ctx.asset.balanceOf(ctx.endaoment.address),
        ctx.asset.balanceOf(ctx.endaoment_funds.address),
        ctx.green.balanceOf(ctx.endaoment.address),
        ctx.green.balanceOf(ctx.endaoment_funds.address),
        ctx.lp.balanceOf(alice),
        ctx.lp.balanceOf(ctx.endaoment.address),
        ctx.lp.balanceOf(ctx.endaoment_funds.address),
        ctx.green.totalSupply(),
        ctx.ledger.greenPoolDebt(ctx.lp.address),
    )

    with boa.reverts("lp amount mismatch"):
        _add_partner_liquidity(ctx, alice)

    balances_after = (
        ctx.asset.balanceOf(alice),
        ctx.asset.balanceOf(ctx.endaoment.address),
        ctx.asset.balanceOf(ctx.endaoment_funds.address),
        ctx.green.balanceOf(ctx.endaoment.address),
        ctx.green.balanceOf(ctx.endaoment_funds.address),
        ctx.lp.balanceOf(alice),
        ctx.lp.balanceOf(ctx.endaoment.address),
        ctx.lp.balanceOf(ctx.endaoment_funds.address),
        ctx.green.totalSupply(),
        ctx.ledger.greenPoolDebt(ctx.lp.address),
    )
    assert balances_after == balances_before


def test_successful_pool_debt_equals_green_minted_for_current_action(
    partner_liquidity_env,
    alice,
):
    ctx = partner_liquidity_env
    _fund_partner(ctx, alice)
    supply_before = ctx.green.totalSupply()
    debt_before = ctx.ledger.greenPoolDebt(ctx.lp.address)

    _add_partner_liquidity(ctx, alice)

    green_minted = ctx.green.totalSupply() - supply_before
    debt_added = ctx.ledger.greenPoolDebt(ctx.lp.address) - debt_before
    assert green_minted == ONE_GREEN
    assert debt_added == green_minted


def test_ordinary_add_liquidity_still_sends_lp_to_endaoment_funds(
    partner_liquidity_env,
    whale,
):
    ctx = partner_liquidity_env
    ctx.asset.mint(
        ctx.endaoment_funds.address,
        ONE_ASSET,
        sender=ctx.governance.address,
    )
    ctx.green.transfer(
        ctx.endaoment_funds.address,
        ONE_GREEN,
        sender=whale,
    )

    lp_received, _, _, _ = ctx.endaoment.addLiquidity(
        LEGO_ID,
        ctx.lp.address,
        ctx.asset.address,
        ctx.green.address,
        ONE_ASSET,
        ONE_GREEN,
        0,
        0,
        0,
        sender=ctx.switchboard_delta.address,
    )

    assert lp_received == 2
    assert ctx.lego.lastRecipient() == ctx.endaoment_funds.address
    assert ctx.lp.balanceOf(ctx.endaoment_funds.address) == 2
    assert ctx.lp.balanceOf(ctx.endaoment.address) == 0


def test_endaoment_rejects_zero_expected_lp_token(
    partner_liquidity_env,
    alice,
):
    ctx = partner_liquidity_env
    with boa.reverts("invalid lp token"):
        ctx.endaoment.addPartnerLiquidity(
            LEGO_ID,
            ctx.lp.address,
            alice,
            ctx.asset.address,
            ONE_ASSET,
            0,
            ZERO_ADDRESS,
            sender=ctx.switchboard_delta.address,
        )


def test_paused_endaoment_blocks_partner_liquidity_locally(
    partner_liquidity_env,
    alice,
):
    ctx = partner_liquidity_env
    _fund_partner(ctx, alice)
    ctx.endaoment.pause(True, sender=ctx.switchboard_delta.address)

    with boa.reverts("contract paused"):
        _add_partner_liquidity(ctx, alice)


def test_switchboard_echo_stores_and_passes_expected_lp_token(
    partner_liquidity_env,
    governance,
    alice,
):
    ctx = partner_liquidity_env
    _fund_partner(ctx, alice)

    aid = ctx.switchboard_echo.addPartnerLiquidityInEndaoment(
        LEGO_ID,
        ctx.lp.address,
        alice,
        ctx.asset.address,
        ONE_ASSET,
        0,
        ctx.lp.address,
        sender=governance.address,
    )
    assert ctx.switchboard_echo.pendingEndaoPartnerPoolActions(aid) == (
        LEGO_ID,
        ctx.lp.address,
        alice,
        ctx.asset.address,
        ONE_ASSET,
        0,
        ctx.lp.address,
    )

    boa.env.time_travel(blocks=ctx.switchboard_echo.actionTimeLock())
    assert ctx.switchboard_echo.executePendingAction(
        aid,
        sender=governance.address,
    )
    assert ctx.lp.balanceOf(alice) == 1
    assert ctx.lp.balanceOf(ctx.endaoment_funds.address) == 1
