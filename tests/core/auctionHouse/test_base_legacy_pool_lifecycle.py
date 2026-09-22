"""Multi-holder lifecycle and batch atomicity for authenticated retained Pool 1.

At unit prices each deposited dollar buys 10**8 shares. This independent
conservation model follows dollar entitlements and custody through operations;
it does not use the pool's conversion helpers to compute expected balances.
"""

from pathlib import Path

import boa
import pytest
from conf_legacy_pool import calls_to
from conf_utils import clear_transient_storage
from constants import EIGHTEEN_DECIMALS as WAD
from constants import MAX_UINT256


@pytest.mark.parametrize("sg_first", [False, True])
@pytest.mark.parametrize("reverse_users", [False, True])
@pytest.mark.parametrize("auto_deposit", [False, True])
def test_retained_multi_holder_lifecycle(
    legacy_env, setRipeRewardsConfig, sg_first, reverse_users, auto_deposit
):
    e = legacy_env
    second = e.token("Lifecycle second claim")
    e.configure(second, _vaultIds=[3], _debtTerms=e.terms(0, 0, 0, 0, 0, 0))
    e.prices.setPrice(second, WAD)
    e.configure(e.green, _vaultIds=[3], _debtTerms=e.terms(0, 0, 0, 0, 0, 0))
    cohorts = [e.lp, e.sg]
    if sg_first:
        cohorts.reverse()
    users = [e.bob, e.alice]
    if reverse_users:
        users.reverse()
    assets = [e.collateral, second, e.green]
    amounts = {
        e.lp.address: {e.bob: 120 * WAD, e.alice: 280 * WAD},
        e.sg.address: {e.bob: 180 * WAD, e.alice: 260 * WAD},
    }
    cash = {c.address: 0 for c in cohorts}
    claims = {(c.address, a.address): 0 for c in cohorts for a in assets}
    remaining = {(c.address, u): 0 for c in cohorts for u in users}
    delivered = {(a.address, u): a.balanceOf(u) for a in assets for u in users}
    initial_debt = {u: e.ledger.userDebt(u) for u in users}

    setRipeRewardsConfig(_ripePerBlock=0, _stabPoolRipePerDollarClaimed=2 * WAD)
    e.mc.setRipeGovVaultConfig(
        e.ripe, 100_00, False, (10, 1000, 100_00, False, 0), sender=e.alpha.address
    )
    e.configure(e.ripe, _vaultIds=[2])
    e.prices.setPrice(e.ripe, WAD)
    budget = 33 * WAD
    e.ledger.setRipeAvailForRewards(budget, sender=e.alpha.address)
    ripe_supply = e.ripe.totalSupply()
    rewards = {u: 0 for u in users}

    def check():
        clear_transient_storage()
        for c in cohorts:
            key = c.address
            assert c.balanceOf(e.pool) == cash[key]
            assert (
                e.pool.totalBalances(c) == sum(remaining[key, u] for u in users) * 10**8
            )
            assert cash[key] + sum(claims[key, a.address] for a in assets) == sum(
                remaining[key, u] for u in users
            )
            active = set()
            for a in assets:
                liability = claims[key, a.address]
                assert e.pool.claimableBalances(c, a) == liability
                index = e.pool.indexOfClaimableAsset(c, a)
                assert bool(index) == bool(liability)
                if liability:
                    assert e.pool.claimableAssets(c, index) == a.address
                    active.add(a.address)
            count = e.pool.numClaimableAssets(c)
            assert {e.pool.claimableAssets(c, i) for i in range(1, count)} == active
            for u in users:
                assert e.pool.userBalances(u, c) == remaining[key, u] * 10**8
                assert e.pool.getTotalUserValue(u, c) == remaining[key, u]
                index = e.pool.indexOfUserAsset(u, c)
                if index:
                    # Historical zero-balance entries can persist until the
                    # next Lootbox checkpoint; the balance marker is decisive.
                    assert e.pool.getUserAssetAtIndexAndHasBalance(u, index) == (
                        c.address,
                        bool(remaining[key, u]),
                    )
                else:
                    assert remaining[key, u] == 0
        for a in assets:
            liability = sum(claims[c.address, a.address] for c in cohorts)
            assert e.pool.totalClaimableBalances(a) == a.balanceOf(e.pool) == liability
            assert a.balanceOf(e.teller) == a.allowance(e.pool, e.teller) == 0
            for u in users:
                received = a.balanceOf(u) + e.ordinary.getTotalAmountForUser(u, a)
                assert received == delivered[a.address, u]
        assert e.ripe.totalSupply() == ripe_supply + sum(rewards.values())
        assert e.ledger.ripeAvailForRewards() == budget
        assert (
            e.ripe.allowance(e.pool, e.teller) == e.green.allowance(e.pool, e.sg) == 0
        )
        for u in users:
            assert e.ripe_gov.getTotalAmountForUser(u, e.ripe) == rewards[u]
            assert e.ledger.userDebt(u) == initial_debt[u]

    for c in cohorts:
        for u in users:
            amount = amounts[c.address][u]
            e.deposit(u, amount, c)
            cash[c.address] += amount
            remaining[c.address, u] += amount
            check()
    for c in cohorts:
        for a, amount in ((e.collateral, 40 * WAD), (second, 20 * WAD)):
            e.claim(a, amount, c, paid=amount)
            cash[c.address] -= amount
            claims[c.address, a.address] += amount
            check()

    # One shared claim becoming unpriceable blocks strict operations without
    # affecting balances; restoring its quote restores both cohort values.
    before = tuple(e.pool.userBalances(u, c) for c in cohorts for u in users)
    e.prices.setShouldRevert(second, True)
    clear_transient_storage()
    for c in cohorts:
        with boa.reverts("has price config, no price"):
            e.pool.getTotalUserValue(e.bob, c)
    assert tuple(e.pool.userBalances(u, c) for c in cohorts for u in users) == before
    e.prices.setShouldRevert(second, False)
    check()

    for u in users:
        entries = [
            (c.address, a.address, n * WAD)
            for c in cohorts
            for a, n in ((e.collateral, 7), (second, 3))
        ]
        clear_transient_storage()
        assert (
            e.teller.claimManyFromStabilityPool(1, entries, u, auto_deposit, sender=u)
            == 20 * WAD
        )
        reward = min(budget, 40 * WAD)
        budget -= reward
        rewards[u] += reward
        for c in cohorts:
            for a, n in ((e.collateral, 7), (second, 3)):
                claims[c.address, a.address] -= n * WAD
                remaining[c.address, u] -= n * WAD
                delivered[a.address, u] += n * WAD
        check()

    # Redeem all remaining collateral: LP receives backed GREEN claims while
    # sGREEN receives shares directly, without changing holder entitlements.
    payment = sum(claims[c.address, a.address] for c in cohorts for a in assets[:2])
    e.green.mint(e.sally, payment, sender=e.ah.address)
    e.green.approve(e.teller, payment, sender=e.sally)
    supply = e.green.totalSupply()
    clear_transient_storage()
    assert (
        e.teller.redeemManyFromStabilityPool(
            1,
            [(a.address, MAX_UINT256) for a in assets[:2]],
            payment,
            e.sally,
            False,
            False,
            False,
            sender=e.sally,
        )
        == payment
    )
    for c in cohorts:
        redeemed = sum(claims[c.address, a.address] for a in assets[:2])
        for a in assets[:2]:
            claims[c.address, a.address] = 0
        if c == e.sg:
            cash[c.address] += redeemed
        else:
            claims[c.address, e.green.address] += redeemed
    assert e.green.totalSupply() == supply
    check()

    # Fully deplete and re-register a claim after swap-and-pop removal.
    e.claim(second, 5 * WAD, e.sg, paid=5 * WAD)
    cash[e.sg.address] -= 5 * WAD
    claims[e.sg.address, second.address] = 5 * WAD
    check()
    clear_transient_storage()
    assert (
        e.teller.claimManyFromStabilityPool(
            1,
            [(e.sg.address, second.address, MAX_UINT256)],
            e.bob,
            auto_deposit,
            sender=e.bob,
        )
        == 5 * WAD
    )
    claims[e.sg.address, second.address] = 0
    remaining[e.sg.address, e.bob] -= 5 * WAD
    delivered[second.address, e.bob] += 5 * WAD
    check()

    green_claim = claims[e.lp.address, e.green.address]
    clear_transient_storage()
    assert (
        e.teller.claimManyFromStabilityPool(
            1,
            [(e.lp.address, e.green.address, MAX_UINT256)],
            e.bob,
            False,
            sender=e.bob,
        )
        == green_claim
    )
    claims[e.lp.address, e.green.address] = 0
    remaining[e.lp.address, e.bob] -= green_claim
    delivered[e.green.address, e.bob] += green_claim
    check()
    for u in users:
        for c in cohorts:
            expected = remaining[c.address, u]
            before_balance = c.balanceOf(u)
            clear_transient_storage()
            assert e.teller.withdraw(c, MAX_UINT256, u, e.pool, sender=u) == expected
            assert c.balanceOf(u) == before_balance + expected
            cash[c.address] -= expected
            remaining[c.address, u] = 0
            check()
    for c in reversed(cohorts):
        e.deposit(e.bob, 17 * WAD, c)
        cash[c.address] = remaining[c.address, e.bob] = 17 * WAD
        check()


def batch_snapshot(e, assets):
    users = (e.bob, e.alice)
    return (
        tuple(
            (
                a.totalSupply(),
                tuple(
                    a.balanceOf(x) for x in (*users, e.pool, e.teller, e.ordinary, e.sg)
                ),
                a.allowance(e.pool, e.teller),
                a.allowance(e.pool, e.sg),
            )
            for a in assets
        ),
        tuple(
            (
                e.pool.totalBalances(c),
                e.pool.numClaimableAssets(c),
                tuple(
                    (
                        e.pool.claimableBalances(c, a),
                        e.pool.indexOfClaimableAsset(c, a),
                        e.pool.totalClaimableBalances(a),
                    )
                    for a in assets
                ),
                tuple(
                    (e.pool.userBalances(u, c), e.pool.indexOfUserAsset(u, c))
                    for u in users
                ),
            )
            for c in (e.lp, e.sg)
        ),
        tuple(
            (
                e.ledger.userDebt(u),
                e.ledger.getDepositLedgerData(u, 1),
                e.ledger.lastTouch(u),
                e.ripe_gov.userBalances(u, e.ripe),
            )
            for u in users
        ),
        e.ledger.ripeAvailForRewards(),
        e.ledger.ripeRewards(),
    )


@pytest.mark.parametrize("operation", ["claim", "redeem"])
@pytest.mark.parametrize("auto_deposit", [False, True])
def test_later_item_failure_restores_entire_retained_batch(
    legacy_env, operation, auto_deposit
):
    e = legacy_env
    second = e.token("Later batch item")
    e.configure(second, _vaultIds=[3], _debtTerms=e.terms(0, 0, 0, 0, 0, 0))
    e.prices.setPrice(second, WAD)
    e.deposit(e.bob, 100 * WAD)
    for a in (e.collateral, second):
        e.claim(a, 20 * WAD, paid=20 * WAD)
    e.green.mint(e.alice, 50 * WAD, sender=e.ah.address)
    e.green.approve(e.teller, 50 * WAD, sender=e.alice)
    original = boa.env.get_code(second.address)
    source = Path("contracts/mock/MockErc20.vy").read_text()
    needle = "    self.balanceOf[msg.sender] -= _value"
    assert source.count(needle) == 1
    source = source.replace(
        "    self.balanceOf[_from] -= _value",
        '    assert False, "later item unavailable"\n    self.balanceOf[_from] -= _value',
    )
    blocked = boa.loads(
        source.replace(needle, '    assert False, "later item unavailable"\n' + needle),
        e.gov,
        "Later batch item",
        "LBI",
        18,
        0,
    )
    boa.env.set_code(second.address, boa.env.get_code(blocked.address))

    def perform():
        clear_transient_storage()
        if operation == "claim":
            return e.teller.claimManyFromStabilityPool(
                1,
                [(e.lp.address, a.address, 10 * WAD) for a in (e.collateral, second)],
                e.bob,
                auto_deposit,
                sender=e.bob,
            )
        return e.teller.redeemManyFromStabilityPool(
            1,
            [(a.address, MAX_UINT256) for a in (e.collateral, second)],
            50 * WAD,
            e.alice,
            auto_deposit,
            False,
            True,
            sender=e.alice,
        )

    before = batch_snapshot(e, (e.lp, e.sg, e.collateral, second, e.green, e.ripe))
    with boa.reverts():
        perform()
    trace = e.teller._computation
    signature = (
        "transferFrom(address,address,uint256)"
        if auto_deposit
        else "transfer(address,uint256)"
    )
    first = calls_to(trace, e.collateral.address, signature)
    later = calls_to(trace, second.address, signature)
    assert first and all(not c.is_error for c in first)
    assert later and later[-1].is_error
    assert (
        batch_snapshot(e, (e.lp, e.sg, e.collateral, second, e.green, e.ripe)) == before
    )
    boa.env.set_code(second.address, original)
    assert perform() == (20 if operation == "claim" else 40) * WAD
