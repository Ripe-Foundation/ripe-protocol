"""Retained Pool-1 composition regressions using authenticated historical bytecode."""

import boa
import pytest
from conf_utils import clear_transient_storage
from constants import EIGHTEEN_DECIMALS as WAD
from constants import MAX_UINT256
from core.auctionHouse.test_base_legacy_vault_compat import debt


@pytest.mark.parametrize("modern_first", [False, True])
@pytest.mark.parametrize(
    "condition",
    [
        "healthy",
        "legacy_paused",
        "legacy_price_unavailable",
        "legacy_depleted",
        "modern_depleted",
    ],
)
def test_retained_legacy_and_modern_pool_coexist(
    legacy_env, stability_pool, modern_first, condition
):
    e = legacy_env
    e.book.startAddNewAddressToRegistry(
        stability_pool, "Modern pool", sender=e.gov.address
    )
    boa.env.time_travel(blocks=e.book.registryChangeTimeLock())
    assert e.book.confirmNewAddressToRegistry(stability_pool, sender=e.gov.address) == 5
    e.configure(
        e.lp,
        _vaultIds=[1, 5],
        _debtTerms=e.terms(0, 0, 0, 0, 0, 0),
        _stakersPointsAlloc=0,
        _voterPointsAlloc=0,
        _shouldTransferToEndaoment=True,
    )
    priority = [(1, e.lp.address), (5, e.lp.address)]
    if modern_first:
        priority.reverse()
    e.mc.setPriorityStabVaults(priority, sender=e.alpha.address)
    e.borrower(e.bob)
    e.deposit(e.bob, 100 * WAD)
    e.lp.mint(e.bob, 100 * WAD, sender=e.gov.address)
    e.lp.approve(e.teller, 100 * WAD, sender=e.bob)
    e.teller.deposit(e.lp, 100 * WAD, e.bob, stability_pool, sender=e.bob)
    if condition in ("legacy_depleted", "modern_depleted"):
        vault = e.pool if condition == "legacy_depleted" else stability_pool
        clear_transient_storage()
        assert (
            e.teller.withdraw(e.lp, MAX_UINT256, e.bob, vault, sender=e.bob)
            == 100 * WAD
        )
    elif condition == "legacy_paused":
        e.pool.pause(True, sender=e.alpha.address)
    elif condition == "legacy_price_unavailable":
        claim = e.token()
        e.claim(claim, WAD, paid=1)
        e.prices.setShouldRevert(claim, True)
    clear_transient_storage()
    expected = (150 if condition == "healthy" else 100) * WAD
    assert (
        e.teller.deleverageManyUsers(
            [(e.bob, 150 * WAD)], sender=e.alpha.address, gas=40000000
        )
        == expected
    )
    assert debt(e) == 300 * WAD - expected
    assert e.lp.balanceOf(e.funds) == expected
    if condition in ("legacy_paused", "legacy_price_unavailable"):
        assert e.pool.userBalances(e.bob, e.lp) == 100 * WAD * 10**8
    clear_transient_storage()


@pytest.mark.parametrize("pay_sg", [False, True])
@pytest.mark.parametrize("auto_deposit", [False, True])
def test_retained_multi_cohort_redemption(legacy_env, pay_sg, auto_deposit):
    e = legacy_env
    claim = e.token("Second redemption claim")
    e.configure(claim, _vaultIds=[3], _debtTerms=e.terms(0, 0, 0, 0, 0, 0))
    e.prices.setPrice(claim, WAD)
    for cohort in (e.lp, e.sg):
        e.deposit(e.bob, 100 * WAD, cohort)
        e.claim(e.collateral, 20 * WAD, cohort, paid=20 * WAD)
        e.claim(claim, 10 * WAD, cohort, paid=10 * WAD)
    e.green.mint(e.alice, 80 * WAD, sender=e.ah.address)
    payment = 80 * WAD
    if pay_sg:
        e.green.approve(e.sg, payment, sender=e.alice)
        payment = e.sg.deposit(payment, e.alice, sender=e.alice)
    token = e.sg if pay_sg else e.green
    token.approve(e.teller, payment, sender=e.alice)
    clear_transient_storage()
    assert (
        e.teller.redeemManyFromStabilityPool(
            1,
            [(e.collateral.address, MAX_UINT256), (claim.address, MAX_UINT256)],
            payment,
            e.alice,
            auto_deposit,
            pay_sg,
            True,
            sender=e.alice,
        )
        == 60 * WAD
    )
    for asset, amount in ((e.collateral, 40 * WAD), (claim, 20 * WAD)):
        assert asset.balanceOf(e.pool) == e.pool.totalClaimableBalances(asset) == 0
        assert (
            e.pool.claimableBalances(e.lp, asset)
            == e.pool.claimableBalances(e.sg, asset)
            == 0
        )
        if auto_deposit:
            assert e.ordinary.getTotalAmountForUser(e.alice, asset) == amount
        else:
            assert asset.balanceOf(e.alice) == amount
        assert asset.balanceOf(e.teller) == 0
    assert (
        e.pool.claimableBalances(e.lp, e.green)
        == e.pool.totalClaimableBalances(e.green)
        == e.green.balanceOf(e.pool)
        == 30 * WAD
    )
    assert e.sg.balanceOf(e.pool) == 100 * WAD
    assert e.sg.convertToAssets(e.sg.balanceOf(e.alice)) == 20 * WAD
    assert e.green.balanceOf(e.teller) == 0
    assert e.green.allowance(e.pool, e.sg) == 0
    clear_transient_storage()


@pytest.mark.parametrize("sg_first", [False, True])
@pytest.mark.parametrize("payment", [15, 45, 65])
def test_retained_partial_redemption_follows_cohort_order(
    legacy_env, sg_first, payment
):
    e = legacy_env
    second = e.token("Partial redemption")
    e.configure(second, _vaultIds=[3], _debtTerms=e.terms(0, 0, 0, 0, 0, 0))
    e.prices.setPrice(second, WAD)
    cohorts = [e.sg, e.lp] if sg_first else [e.lp, e.sg]
    assets = [e.collateral, second]
    claims = {}
    green_claims = {c.address: 0 for c in cohorts}
    custody = {c.address: 70 * WAD for c in cohorts}
    for c in cohorts:
        e.deposit(e.bob, 100 * WAD, c)
        for a, amount in zip(assets, (20 * WAD, 10 * WAD)):
            e.claim(a, amount, c, paid=amount)
            claims[c.address, a.address] = amount
    e.green.mint(e.alice, payment * WAD, sender=e.ah.address)
    e.green.approve(e.teller, payment * WAD, sender=e.alice)
    remaining = payment * WAD
    received = {a.address: 0 for a in assets}
    # First asset is capped at 25 GREEN. The second uses the remaining budget;
    # unused payment must return to the caller after both items are processed.
    for a, cap in zip(assets, (25 * WAD, MAX_UINT256)):
        budget = min(remaining, cap)
        for c in cohorts:
            amount = min(claims[c.address, a.address], budget)
            claims[c.address, a.address] -= amount
            received[a.address] += amount
            if c == e.sg:
                custody[c.address] += amount
            else:
                green_claims[c.address] += amount
            budget -= amount
            remaining -= amount
    clear_transient_storage()
    assert (
        e.teller.redeemManyFromStabilityPool(
            1,
            [(assets[0].address, 25 * WAD), (assets[1].address, MAX_UINT256)],
            payment * WAD,
            e.alice,
            False,
            False,
            False,
            sender=e.alice,
        )
        == payment * WAD - remaining
    )
    for a in assets:
        assert a.balanceOf(e.alice) == received[a.address]
        assert (
            e.pool.totalClaimableBalances(a)
            == a.balanceOf(e.pool)
            == sum(claims[c.address, a.address] for c in cohorts)
        )
        for c in cohorts:
            assert e.pool.claimableBalances(c, a) == claims[c.address, a.address]
    for c in cohorts:
        assert c.balanceOf(e.pool) == custody[c.address]
        assert e.pool.claimableBalances(c, e.green) == green_claims[c.address]
        assert e.pool.getTotalUserValue(e.bob, c) == 100 * WAD
        assert e.pool.userBalances(e.bob, c) == 100 * WAD * 10**8
    assert e.green.balanceOf(e.alice) == remaining
    assert (
        e.green.balanceOf(e.pool)
        == e.pool.totalClaimableBalances(e.green)
        == sum(green_claims.values())
    )
    assert e.green.balanceOf(e.teller) == e.green.allowance(e.pool, e.sg) == 0
