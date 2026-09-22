"""Retained-pool repayment targets, enumeration order and nonzero policy."""

import boa
import pytest
from conf_legacy_pool import calls_to
from conf_utils import clear_transient_storage, filter_logs
from constants import EIGHTEEN_DECIMALS as WAD
from core.auctionHouse.test_base_legacy_vault_compat import ADDYS_ABI, debt, pool_state


@pytest.mark.parametrize("cross_cohort", [False, True])
@pytest.mark.parametrize("sg_first", [False, True])
@pytest.mark.parametrize("borrowed", [5 * WAD, 300 * WAD])
@pytest.mark.parametrize("target_delta", [-1, 0, 1])
def test_retained_payoff_targets_and_internal_cohort_order(
    legacy_env, setGeneralDebtConfig, sg_first, borrowed, target_delta, cross_cohort
):
    e = legacy_env
    setGeneralDebtConfig(
        _minDebtAmount=5 * WAD,
        _ltvPaybackBuffer=100,
        _keeperFeeRatio=100,
        _minKeeperFee=10**16,
    )
    e.borrower(e.bob, debt=borrowed)
    cohorts = [e.sg, e.lp] if sg_first else [e.lp, e.sg]
    first_amount = borrowed // 2 if cross_cohort else borrowed
    e.deposit(e.bob, first_amount, cohorts[0])
    e.deposit(e.bob, borrowed, cohorts[1])
    # Force ordinary vault enumeration instead of the configured priority list.
    e.mc.setPriorityStabVaults([], sender=e.alpha.address)
    before = {c.address: c.balanceOf(e.pool) for c in cohorts}
    clear_transient_storage()
    requested = borrowed + target_delta
    paid = e.teller.deleverageManyUsers(
        [(e.bob, requested)], sender=e.alpha.address, gas=40_000_000
    )
    trace = e.teller._computation
    expected = min(requested, borrowed)
    assert paid == expected and debt(e) == borrowed - expected
    event = filter_logs(e.teller, "DeleverageUser")[0]
    assert event.targetRepayAmount == event.debtToClear == expected
    assert event.collateralValueRepaid == expected
    first_paid = min(first_amount, expected)
    second_paid = expected - first_paid
    assert cohorts[0].balanceOf(e.pool) == before[cohorts[0].address] - first_paid
    assert cohorts[1].balanceOf(e.pool) == before[cohorts[1].address] - second_paid
    withdrawals = calls_to(
        trace,
        e.pool.address,
        f"withdrawTokensFromVault(address,address,uint256,address,{ADDYS_ABI})",
    )
    assert len(withdrawals) == (2 if cross_cohort else 1)
    # A trusted caller does not receive a keeper reward for this operation.
    assert e.green.balanceOf(e.alpha) == 0
    assert e.pool.userBalances(e.bob, cohorts[1]) == (borrowed - second_paid) * 10**8


@pytest.mark.parametrize("kind", ["lp", "sg"])
def test_retained_withdrawal_minimum_buffer_and_cooldown(legacy_env, kind):
    e = legacy_env
    c = getattr(e, kind)
    e.borrower(e.bob)
    e.deposit(e.bob, 600 * WAD, c)
    e.dl.setMinDeleverageBps(500, sender=e.alpha.address)
    e.dl.setDeleverageBuffer(100, sender=e.alpha.address)
    e.dl.setDeleverageCooldown(10, sender=e.alpha.address)
    before = debt(e), pool_state(e)
    clear_transient_storage()
    assert not e.dl.deleverageForWithdrawal(
        e.bob, 3, e.collateral, WAD, sender=e.teller.address
    )
    assert (debt(e), pool_state(e)) == before
    # 300 debt * 50 lost capacity / 500 capacity, then the configured 1%.
    expected = 303 * WAD // 10
    clear_transient_storage()
    assert e.dl.deleverageForWithdrawal(
        e.bob, 3, e.collateral, 100 * WAD, sender=e.teller.address
    )
    assert debt(e) == 300 * WAD - expected
    assert c.balanceOf(e.pool) == 600 * WAD - expected
    first_block = e.dl.lastDeleverageBlock(e.bob)
    boa.env.time_travel(blocks=1)
    before = debt(e), pool_state(e)
    clear_transient_storage()
    assert not e.dl.deleverageForWithdrawal(
        e.bob, 3, e.collateral, 100 * WAD, sender=e.teller.address
    )
    assert (debt(e), pool_state(e)) == before
    boa.env.time_travel(blocks=9)
    clear_transient_storage()
    assert e.dl.deleverageForWithdrawal(
        e.bob, 3, e.collateral, 100 * WAD, sender=e.teller.address
    )
    assert e.dl.lastDeleverageBlock(e.bob) == first_block + 10
    assert debt(e) < before[0]


@pytest.mark.parametrize("sg_first", [False, True])
@pytest.mark.parametrize(
    "minimum,maximum,fee",
    [
        (WAD, 100 * WAD, 6 * WAD),
        (10 * WAD, 100 * WAD, 10 * WAD),
        (WAD, 3 * WAD, 3 * WAD),
    ],
)
def test_actual_liquidation_preserves_unequal_holders_with_nonzero_fees(
    legacy_env, setGeneralDebtConfig, sg_first, minimum, maximum, fee
):
    e = legacy_env
    setGeneralDebtConfig(
        _ltvPaybackBuffer=100,
        _keeperFeeRatio=200,
        _minKeeperFee=minimum,
        _maxKeeperFee=maximum,
    )
    e.configure(
        e.collateral, _vaultIds=[3], _debtTerms=e.terms(5000, 6000, 8000, 500, 0, 0)
    )
    cohorts = [e.sg, e.lp] if sg_first else [e.lp, e.sg]
    e.mc.setPriorityStabVaults(
        [(1, c.address) for c in cohorts], sender=e.alpha.address
    )
    starting = {}
    shares = {}
    for c, amount in zip(cohorts, (100 * WAD, 400 * WAD)):
        starting[c.address] = amount
        for u, fraction in ((e.alice, 2), (e.sally, 3)):
            e.deposit(u, amount * fraction // 5, c)
            shares[c.address, u] = amount * fraction // 5 * 10**8
    e.borrower(e.bob)
    e.prices.setPrice(e.collateral, 35 * WAD // 100)
    keeper_before, supply_before = e.green.balanceOf(e.whale), e.green.totalSupply()
    clear_transient_storage()
    assert e.teller.liquidateUser(e.bob, False, sender=e.whale) == fee
    swaps = filter_logs(e.teller, "CollateralSwappedWithStabPool")
    event = filter_logs(e.teller, "LiquidateUser")[0]
    assert [s.stabAsset for s in swaps] == [c.address for c in cohorts]
    assert event.keeperFee == fee and event.totalLiqFees == 15 * WAD + fee
    repaid = sum(s.valueSwapped for s in swaps)
    collateral_value = sum(s.collateralValueOut for s in swaps)
    unpaid_base = 15 * WAD - min(15 * WAD, max(0, collateral_value - repaid))
    assert debt(e) == 300 * WAD + unpaid_base + fee - repaid
    assert e.green.balanceOf(e.whale) == keeper_before + fee
    sg_burn = 0
    for c, swap in zip(cohorts, swaps):
        cash = starting[c.address] - swap.amountSwapped
        assert c.balanceOf(e.pool) == cash
        assert e.pool.claimableBalances(c, e.collateral) == swap.collateralAmountOut
        value = cash + swap.collateralAmountOut * 35 // 100
        for u in (e.alice, e.sally):
            expected = (
                shares[c.address, u]
                * (value + 1)
                // (starting[c.address] * 10**8 + 10**8)
            )
            assert e.pool.userBalances(u, c) == shares[c.address, u]
            assert e.pool.getTotalUserValue(u, c) == expected
        if c == e.sg:
            sg_burn = swap.valueSwapped
        else:
            assert e.lp.balanceOf(e.funds) == swap.amountSwapped
    assert (
        e.collateral.balanceOf(e.pool)
        == e.pool.totalClaimableBalances(e.collateral)
        == sum(s.collateralAmountOut for s in swaps)
    )
    assert e.green.totalSupply() == supply_before + fee - sg_burn
