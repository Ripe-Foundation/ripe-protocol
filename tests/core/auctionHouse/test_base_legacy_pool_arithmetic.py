"""Retained Pool-1 arithmetic regressions using authenticated historical bytecode."""

import boa
import pytest
from conf_utils import clear_transient_storage
from constants import EIGHTEEN_DECIMALS as WAD
from core.auctionHouse.test_base_legacy_vault_compat import (
    debt,
    fund_healthy_batch_user,
)


@pytest.mark.parametrize("quote", [1007, 1500])
@pytest.mark.parametrize("healthy_first", [False, True])
def test_retained_sgreen_growth_after_partial_repayment(
    legacy_env, quote, healthy_first
):
    e = legacy_env
    e.borrower(e.bob)
    fund_healthy_batch_user(e)
    e.deposit(e.sally, 600 * WAD, e.sg)
    e.deposit(e.bob, 100 * WAD, e.sg)
    clear_transient_storage()
    assert (
        e.teller.deleverageWithSpecificAssets(
            [(1, e.sg.address, 100 * WAD - 1)], e.bob, sender=e.bob
        )
        == 100 * WAD - 1
    )
    assert e.pool.getTotalAmountForUser(e.bob, e.sg) == 1
    assert e.pool.getTotalUserValue(e.bob, e.sg) == 1
    e.green.mint(e.sg, e.sg.totalAssets() * (quote - 1000) // 1000, sender=e.ah.address)
    e.prices.setPrice(e.sg, e.sg.convertToAssets(WAD))
    clear_transient_storage()
    assert e.pool.getTotalAmountForUser(e.bob, e.sg) == 1
    assert e.pool.getTotalUserValue(e.bob, e.sg) == 1
    assert e.nav() == (e.sg.address, 0)
    users = [(e.bob, WAD), (e.alice, 100 * WAD)]
    if healthy_first:
        users.reverse()
    clear_transient_storage()
    assert (
        e.teller.deleverageManyUsers(users, sender=e.alpha.address, gas=40000000)
        == 100 * WAD
    )
    assert debt(e, e.alice) == 200 * WAD
    assert debt(e, e.bob) == 200 * WAD + 1
    clear_transient_storage()


@pytest.mark.parametrize("kind", ["lp", "sg"])
@pytest.mark.parametrize("quote", [400, 999, 1001, 1007, 1100, 1500])
def test_retained_residual_amount_matrix(legacy_env, kind, quote):
    e = legacy_env
    e.borrower(e.bob)
    fund_healthy_batch_user(e)
    token = getattr(e, kind)
    e.configure(
        token,
        _vaultIds=[1],
        _minDepositBalance=10**16,
        _debtTerms=e.terms(0, 0, 0, 0, 0, 0),
        _shouldTransferToEndaoment=kind == "lp",
        _shouldBurnAsPayment=kind == "sg",
        _shouldSwapInStabPools=False,
        _shouldAuctionInstantly=False,
    )
    if kind == "lp":
        e.prices.setPrice(token, quote * WAD // 1000)
    e.deposit(e.sally, 600 * WAD, token)
    e.deposit(e.bob, 100 * WAD, token)
    if kind == "sg":
        assets = e.sg.totalAssets()
        desired = assets * quote // 1000
        if desired > assets:
            e.green.mint(e.sg, desired - assets, sender=e.ah.address)
        elif desired < assets:
            e.green.transfer(e.whale, assets - desired, sender=e.sg.address)
        e.prices.setPrice(e.sg, e.sg.convertToAssets(WAD))
    value = e.pool.getTotalUserValue(e.bob, token)
    for offset in (1, 2, 3, 5, 10, 100, 1000):
        for healthy_first in (False, True):
            with boa.env.anchor():
                clear_transient_storage()
                target = value - offset
                paid = e.teller.deleverageWithSpecificAssets(
                    [(1, token.address, target)], e.bob, sender=e.bob
                )
                assert 0 < paid <= target
                clear_transient_storage()
                _, nav = e.nav()
                users = [(e.bob, WAD), (e.alice, 100 * WAD)]
                if healthy_first:
                    users.reverse()
                try:
                    e.teller.deleverageManyUsers(
                        users, sender=e.alpha.address, gas=40000000
                    )
                except boa.BoaError as err:
                    pytest.fail(
                        f"kind={kind!r} quote={quote!r} offset={offset!r} healthy_first={healthy_first!r} nav={nav!r}\n{err}"
                    )
                assert debt(e, e.alice) == 200 * WAD
    clear_transient_storage()
