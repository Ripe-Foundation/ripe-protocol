"""Ordinary, network-independent composition tests for retained Base Pool 1."""
import boa
import pytest

from constants import EIGHTEEN_DECIMALS as WAD, ZERO_ADDRESS
from conf_utils import filter_logs
from conf_legacy_pool import PROVENANCE, call_tree, calls_to, storage_write


def debt(e, user=None):
    return e.ce.getLatestUserDebtAndTerms(e.bob if user is None else user, False)[0].amount


def pool_state(e, user=None):
    user = e.bob if user is None else user
    return tuple((e.pool.userBalances(user, t), e.pool.totalBalances(t),
                  t.balanceOf(e.pool), e.pool.claimableBalances(t, e.green),
                  e.pool.claimableBalances(t, e.collateral)) for t in (e.lp, e.sg))


def mature(contract, action):
    confirmation = contract.getActionConfirmationBlock(action)
    if confirmation > boa.env.evm.patch.block_number:
        boa.env.time_travel(blocks=confirmation - boa.env.evm.patch.block_number)


def liquidatable(e):
    e.borrower(e.bob)
    e.prices.setPrice(e.collateral, WAD * 35 // 100)
    assert e.ce.canLiquidateUser(e.bob)


@pytest.mark.parametrize("kind", ["lp", "sg"])
def test_funded_legacy_swaps_through_auction_house(legacy_env, kind):
    e = legacy_env
    token = getattr(e, kind)
    e.deposit(e.alice, 600 * WAD, token)
    liquidatable(e)
    before = (token.balanceOf(e.pool), token.balanceOf(e.funds), e.green.totalSupply(),
              e.pool.userBalances(e.alice, token), debt(e))
    e.teller.liquidateUser(e.bob, False, sender=e.sally)
    swaps = filter_logs(e.teller, "CollateralSwappedWithStabPool")
    assert len(swaps) == 1
    swap = swaps[0]
    assert swap.stabVaultId == 1 and swap.stabAsset == token.address
    assert before[0] - token.balanceOf(e.pool) == swap.amountSwapped > 0
    assert e.pool.claimableBalances(token, e.collateral) == swap.collateralAmountOut
    assert e.pool.totalClaimableBalances(e.collateral) == swap.collateralAmountOut
    assert e.collateral.balanceOf(e.pool) == swap.collateralAmountOut
    assert debt(e) == before[4] - swap.valueSwapped
    assert e.pool.userBalances(e.alice, token) == before[3]
    if kind == "lp":
        assert token.balanceOf(e.funds) - before[1] == swap.amountSwapped
        assert e.green.totalSupply() == before[2]
    else:
        assert before[2] - e.green.totalSupply() == swap.valueSwapped
    calls = calls_to(e.teller._computation, e.pool.address,
                    "swapForLiquidatedCollateral(address,uint256,address,uint256,address,address,address)")
    assert len(calls) == 1
    assert calls[0].msg.sender == bytes.fromhex(e.ah.address[2:])


def test_backed_green_can_pay_with_zero_stabilization_custody(legacy_env):
    e = legacy_env
    e.deposit(e.alice, 600 * WAD)
    e.claim(e.green, 600 * WAD, paid=e.lp.balanceOf(e.pool))
    assert e.lp.balanceOf(e.pool) == 0 and e.ready()
    liquidatable(e)
    before = (e.green.totalSupply(), e.pool.claimableBalances(e.lp, e.green), debt(e))
    e.teller.liquidateUser(e.bob, False, sender=e.sally)
    swaps = filter_logs(e.teller, "CollateralSwappedWithStabPool")
    assert len(swaps) == 1 and swaps[0].assetSwapped == e.green.address
    paid = swaps[0].amountSwapped
    assert paid > 0
    assert e.green.totalSupply() == before[0] - paid
    assert e.pool.claimableBalances(e.lp, e.green) == before[1] - paid
    assert e.pool.totalClaimableBalances(e.green) == before[1] - paid
    assert debt(e) == before[2] - paid
    assert e.lp.balanceOf(e.pool) == 0


@pytest.mark.parametrize("custody", [99, 100, 199])
def test_aggregate_green_deficit_rejects_even_small_covered_swap(legacy_env, custody):
    e = legacy_env
    e.deposit(e.alice, 100 * WAD)
    e.deposit(e.alice, 100 * WAD, e.sg)
    e.claim(e.green, 100 * WAD, e.lp, paid=100 * WAD)
    e.claim(e.green, 100 * WAD, e.sg)
    e.green.transfer(e.whale, (200 - custody) * WAD, sender=e.pool.address)
    assert e.pool.claimableBalances(e.lp, e.green) == 100 * WAD
    assert e.pool.totalClaimableBalances(e.green) == 200 * WAD
    assert not e.ready(e.lp) and not e.ready(e.sg)
    liquidatable(e)
    before = pool_state(e, e.alice)
    e.teller.liquidateUser(e.bob, False, sender=e.sally)
    assert not filter_logs(e.teller, "CollateralSwappedWithStabPool")
    assert filter_logs(e.teller, "FungibleAuctionUpdated")
    assert pool_state(e, e.alice) == before


def test_green_backing_is_required_only_for_selected_cohort_and_spendable_price(legacy_env):
    e = legacy_env
    e.deposit(e.alice, 100 * WAD)
    e.deposit(e.alice, 100 * WAD, e.sg)
    e.claim(e.green, 100 * WAD, e.sg)
    e.green.transfer(e.whale, e.green.balanceOf(e.pool), sender=e.pool.address)
    assert e.ready(e.lp)
    assert not e.ready(e.sg)
    e.claim(e.green, 200 * WAD, e.lp)
    # Repair aggregate funding; LP still needs its price for a residual payment.
    e.green.mint(e.pool, 100 * WAD, sender=e.ah.address)
    assert e.ready(e.lp)
    e.prices.setPrice(e.lp, 0)
    assert not e.ready(e.lp)
    e.lp.transfer(e.whale, e.lp.balanceOf(e.pool), sender=e.pool.address)
    assert e.ready(e.lp)


@pytest.mark.parametrize("boundary", ["pause", "unregistered_stab", "zero_incoming", "deposit_incoming", "reservation", "empty"])
def test_legacy_readiness_boundaries_preserve_state(legacy_env, boundary):
    e = legacy_env
    e.deposit(e.alice, 100 * WAD)
    cohort, incoming = e.lp, e.collateral
    if boundary == "pause":
        e.pool.pause(True, sender=e.alpha.address)
    elif boundary == "unregistered_stab":
        cohort = e.sg
    elif boundary == "zero_incoming":
        incoming = ZERO_ADDRESS
    elif boundary == "deposit_incoming":
        incoming = e.lp
    elif boundary == "reservation":
        storage_write(e.pool, "stabVault", "totalClaimableBalances", [e.lp], 1)
    else:
        e.lp.transfer(e.whale, e.lp.balanceOf(e.pool), sender=e.pool.address)
    before = pool_state(e, e.alice)
    assert not e.ready(cohort, incoming)
    assert pool_state(e, e.alice) == before


def test_empty_cohort_becomes_ready_with_donated_spendable_custody(legacy_env):
    e = legacy_env
    e.deposit(e.alice, WAD)
    e.lp.transfer(e.whale, WAD, sender=e.pool.address)
    assert not e.ready()
    e.lp.mint(e.pool, 1, sender=e.gov.address)
    assert e.ready()


@pytest.mark.parametrize("next_pair", [False, True])
def test_zero_lp_price_falls_back_before_raising_quote(legacy_env, next_pair):
    e = legacy_env
    e.deposit(e.alice, 600 * WAD)
    if next_pair:
        e.deposit(e.alice, 600 * WAD, e.sg)
    liquidatable(e)
    e.prices.setPrice(e.lp, 0)
    assert not e.ready(e.lp)
    before = (e.lp.balanceOf(e.pool), e.pool.userBalances(e.alice, e.lp))
    e.teller.liquidateUser(e.bob, False, sender=e.sally)
    swaps = filter_logs(e.teller, "CollateralSwappedWithStabPool")
    if next_pair:
        assert len(swaps) == 1 and swaps[0].stabAsset == e.sg.address
    else:
        assert not swaps
        assert filter_logs(e.teller, "FungibleAuctionUpdated")
    assert (e.lp.balanceOf(e.pool), e.pool.userBalances(e.alice, e.lp)) == before


@pytest.mark.parametrize("kind", ["lp", "sg"])
@pytest.mark.parametrize("scenario", ["weighted", "liquidity_cap", "debt_cap"])
def test_ordinary_vault3_withdrawal_preparation_uses_real_legacy_nav(legacy_env, kind, scenario):
    e = legacy_env
    token = getattr(e, kind)
    ordinary_eligible = scenario != "liquidity_cap"
    e.configure(e.collateral, _vaultIds=[3], _debtTerms=e.terms(50_00, 60_00, 80_00, 0, 0, 0),
                _shouldTransferToEndaoment=ordinary_eligible)
    e.borrower(e.bob)
    initial = {"weighted": 200, "liquidity_cap": 50, "debt_cap": 800}[scenario] * WAD
    e.deposit(e.bob, initial, token)
    if scenario == "weighted":
        claim = e.token()
        e.prices.setPrice(claim, WAD)
        e.claim(claim, 100 * WAD, token, paid=20 * WAD)
    nav = e.pool.getTotalAmountForUser(e.bob, token)
    pool_value = e.pd.getUsdValue(token, nav, True)
    ordinary_value = 1000 * WAD if ordinary_eligible else 0
    maximum = pool_value + ordinary_value
    weighted_ltv = ordinary_value * 50_00 // maximum
    assert e.dl.getDeleverageInfo(e.bob) == (maximum, weighted_ltv)
    bt = e.ce.getUserBorrowTerms(e.bob, False)
    assert bt.collateralVal == 1000 * WAD and bt.totalMaxDebt == 500 * WAD
    amount = 200 * WAD if scenario == "weighted" else 1000 * WAD
    before_debt = debt(e)
    raw_target = before_debt * (amount * 50_00 // 100_00) // (
        bt.totalMaxDebt - before_debt * weighted_ltv // 100_00)
    target = min(maximum, before_debt, raw_target)
    if scenario == "liquidity_cap":
        assert target == maximum < raw_target
    elif scenario == "debt_cap":
        assert target == before_debt < raw_target
    else:
        assert raw_target * (bt.totalMaxDebt - before_debt * weighted_ltv // 100_00) <= before_debt * (amount // 2)
        assert (raw_target + 1) * (bt.totalMaxDebt - before_debt * weighted_ltv // 100_00) > before_debt * (amount // 2)
    requested_tokens = e.sg.convertToShares(target) if kind == "sg" else target
    shares_before = e.pool.userBalances(e.bob, token)
    expected_shares = min(shares_before, e.pool.valueToShares(token, target, True))
    supply_before = e.green.totalSupply()
    funds_before = token.balanceOf(e.funds)
    cash_before = token.balanceOf(e.pool)
    assert e.dl.deleverageForWithdrawal(e.bob, 3, e.collateral, amount, sender=e.teller.address)
    trace = e.dl._computation
    event = filter_logs(e.dl, "DeleverageUser")[0]
    assert event.targetRepayAmount == target
    assert debt(e) == before_debt - target
    assert cash_before - token.balanceOf(e.pool) == requested_tokens
    assert e.pool.userBalances(e.bob, token) == shares_before - expected_shares
    if kind == "lp":
        assert token.balanceOf(e.funds) - funds_before == requested_tokens
        assert e.green.totalSupply() == supply_before
    else:
        assert supply_before - e.green.totalSupply() == target
    withdrawals = calls_to(trace, e.pool.address, "withdrawTokensFromVault(address,address,uint256,address,(address,address,address,address,address,address,address,address,address,address,address,address,address,address,address,address,address,address))")
    assert len(withdrawals) == 1 and withdrawals[0].msg.sender == bytes.fromhex(e.ah.address[2:])
    if scenario != "liquidity_cap":
        collateral_before = e.collateral.balanceOf(e.bob)
        assert e.teller.withdraw(e.collateral, amount, e.bob, e.ordinary, sender=e.bob) == amount
        assert e.collateral.balanceOf(e.bob) - collateral_before == amount
    else:
        before_pool = pool_state(e)
        max_withdrawal = e.ce.getMaxWithdrawableForAsset(e.bob, 3, e.collateral)
        assert 0 < max_withdrawal < amount
        assert e.teller.withdraw(e.collateral, amount, e.bob, e.ordinary, sender=e.bob) == max_withdrawal
        assert pool_state(e) == before_pool and debt(e) == before_debt - target
        assert e.ce.getUserBorrowTerms(e.bob, False).totalMaxDebt >= debt(e)


@pytest.mark.parametrize("kind", ["lp", "sg"])
@pytest.mark.parametrize("vault_id", [0, 1])
def test_zero_ltv_pool_withdrawal_preparation_does_not_force_repayment(legacy_env, kind, vault_id):
    e = legacy_env
    token = getattr(e, kind)
    e.borrower(e.bob)
    e.deposit(e.bob, 100 * WAD, token)
    before = (debt(e), pool_state(e))
    assert not e.dl.deleverageForWithdrawal(e.bob, vault_id, token, 10 * WAD, sender=e.teller.address)
    assert (debt(e), pool_state(e)) == before
    if kind == "lp":
        e.prices.setPrice(token, 0)
        with boa.reverts("has price config, no price"):
            e.dl.deleverageForWithdrawal(e.bob, vault_id, token, 10 * WAD, sender=e.teller.address)
        assert (debt(e), pool_state(e)) == before


@pytest.mark.parametrize("condition", ["paused", "cash_empty"])
def test_broad_batch_skips_pool_and_continues_next_user(legacy_env, condition):
    e = legacy_env
    e.borrower(e.bob)
    e.borrower(e.alice)
    e.deposit(e.bob, 100 * WAD)
    claim = e.token()
    e.prices.setPrice(claim, WAD)
    e.claim(claim, 100 * WAD)
    ordinary_payment = e.token("Payment")
    e.configure(ordinary_payment, _vaultIds=[3], _debtTerms=e.terms(0, 0, 0, 0, 0, 0), _shouldTransferToEndaoment=True)
    e.prices.setPrice(ordinary_payment, WAD)
    ordinary_payment.mint(e.alice, 300 * WAD, sender=e.gov.address)
    ordinary_payment.approve(e.teller, 300 * WAD, sender=e.alice)
    e.teller.deposit(ordinary_payment, 300 * WAD, e.alice, e.ordinary, sender=e.alice)
    if condition == "paused":
        e.pool.pause(True, sender=e.alpha.address)
    else:
        e.lp.transfer(e.whale, e.lp.balanceOf(e.pool), sender=e.pool.address)
    before = pool_state(e)
    claims_before = e.pool.claimableBalances(e.lp, claim)
    assert e.dl.getDeleverageInfo(e.bob) == (0, 0)
    assert e.teller.deleverageManyUsers([(e.bob, 100 * WAD), (e.alice, 100 * WAD)], sender=e.alpha.address) == 100 * WAD
    trace = e.teller._computation
    assert debt(e) == 300 * WAD and debt(e, e.alice) == 200 * WAD
    assert ordinary_payment.balanceOf(e.funds) == 100 * WAD
    assert pool_state(e) == before and e.pool.claimableBalances(e.lp, claim) == claims_before
    assert not calls_to(trace, e.pool.address, "withdrawTokensFromVault(address,address,uint256,address,(address,address,address,address,address,address,address,address,address,address,address,address,address,address,address,address,address,address))")
    # Explicit asset selection bypasses broad traversal and retains the strict path.
    reason = "contract paused" if condition == "paused" else "no stab asset to withdraw"
    with boa.reverts(reason):
        e.teller.deleverageWithSpecificAssets([(1, e.lp.address, WAD)], e.bob, sender=e.bob)
    assert pool_state(e) == before and debt(e) == 300 * WAD
    assert e.pool.getTotalAmountForUser(e.bob, e.lp) > 0


def test_retained_configuration_leaves_pool_positions_for_deleverage(legacy_env):
    e = legacy_env
    e.borrower(e.bob)
    e.deposit(e.bob, 50 * WAD)
    e.deposit(e.bob, 50 * WAD, e.sg)
    assert e.mc.getAssetLiqConfig(e.lp).shouldTransferToEndaoment
    assert e.mc.getAssetLiqConfig(e.sg).shouldBurnAsPayment
    assert e.pool.getUserAssetAndAmountAtIndex(e.bob, 1) == (ZERO_ADDRESS, 0)
    before = pool_state(e)
    addys = e.ah.getAddys()
    for token in (e.lp, e.sg):
        assert e.ah.internal._handleSpecificLiqAsset(e.bob, 1, e.pool.address, token.address,
                    100 * WAD, 0, 0, [], addys) == (100 * WAD, 0)
    assert pool_state(e) == before
    assert e.teller.deleverageManyUsers([(e.bob, 100 * WAD)], sender=e.alpha.address) == 100 * WAD
    assert debt(e) == 200 * WAD
    assert e.lp.balanceOf(e.funds) == 50 * WAD
    assert e.pool.userBalances(e.bob, e.lp) == e.pool.userBalances(e.bob, e.sg) == 0


def test_value_moving_callers_stay_direct_and_authorized(legacy_env):
    e = legacy_env
    e.deposit(e.bob, 100 * WAD)
    before = pool_state(e)
    for caller in (e.book.address, e.dl.address, e.bob):
        with boa.reverts("not allowed"):
            e.pool.withdrawTokensFromVault(e.bob, e.lp, WAD, e.bob, sender=caller)
        with boa.reverts("only Teller allowed"):
            e.pool.depositTokensInVault(e.bob, e.lp, WAD, sender=caller)
        with boa.reverts("only AuctionHouse allowed"):
            e.pool.swapForLiquidatedCollateral(e.lp, WAD, e.collateral, WAD, e.whale,
                                               e.green, e.sg, sender=caller)
        with boa.reverts("only AuctionHouse allowed"):
            e.pool.swapWithClaimableGreen(e.lp, WAD, e.collateral, WAD, e.green, sender=caller)
    assert pool_state(e) == before
    assert e.teller.withdraw(e.lp, WAD, e.bob, e.pool, sender=e.bob) == WAD
    calls = calls_to(e.teller._computation, e.pool.address, "withdrawTokensFromVault(address,address,uint256,address,(address,address,address,address,address,address,address,address,address,address,address,address,address,address,address,address,address,address))")
    assert len(calls) == 1 and calls[0].msg.sender == bytes.fromhex(e.teller.address[2:])


@pytest.mark.parametrize("requested,paid,expected", [
    (0, 0, True), (1, 0, False), (99, 98, False), (99, 99, True),
    (100, 99, True), (100, 98, False), (100, 101, True), (100, 102, False),
    (199, 198, True), (199, 197, False), (200, 198, True), (200, 197, False),
])
def test_exact_one_percent_integer_boundary(auction_house, requested, paid, expected):
    assert auction_house.internal._isPaymentCloseEnough(requested, paid) is expected


@pytest.mark.parametrize("past_boundary", [False, True])
def test_real_legacy_partial_green_payment_settlement_and_rollback(legacy_env, past_boundary):
    e = legacy_env
    requested = 100 * WAD + 99
    paid = requested - requested // 100 - int(past_boundary)
    e.deposit(e.alice, 200 * WAD)
    e.claim(e.green, requested, paid=200 * WAD)
    e.green.transfer(e.whale, requested - paid, sender=e.pool.address)
    e.borrower(e.bob)
    assert not e.ready()  # aggregate backing policy excludes both cases publicly
    before = (pool_state(e, e.alice), e.green.totalSupply(), e.green.balanceOf(e.pool),
              e.ordinary.getTotalAmountForUser(e.bob, e.collateral), debt(e))
    # Exercise the unchanged settlement boundary independently of conservative
    # admission. The real pool pays min(requested, cohort claim, actual cash).
    args = (False, e.bob, 3, e.ordinary.address, e.collateral.address, 0,
            requested, requested, requested, 0, (1, e.pool.address, e.lp.address),
            ZERO_ADDRESS, e.ah.getAddys())
    if past_boundary:
        with boa.reverts("invalid stability pool swap"):
            e.ah.internal._swapAssetsWithStabPool(*args)
        assert (pool_state(e, e.alice), e.green.totalSupply(), e.green.balanceOf(e.pool),
                e.ordinary.getTotalAmountForUser(e.bob, e.collateral), debt(e)) == before
    else:
        result = e.ah.internal._swapAssetsWithStabPool(*args)
        assert result[0] == requested - paid and result[1] == requested
        assert e.green.totalSupply() == before[1] - paid
        assert e.pool.claimableBalances(e.lp, e.green) == requested - paid
        assert e.pool.totalClaimableBalances(e.green) == requested - paid
        assert e.pool.claimableBalances(e.lp, e.collateral) == requested
        assert e.collateral.balanceOf(e.pool) == requested
        # Internal swap accounting does not itself settle CreditEngine debt.
        assert debt(e) == before[4]


def seed_dust(e):
    assets = []
    for row in PROVENANCE["dust_claims"]:
        token = e.token(row["symbol"], row["decimals"])
        e.prices.setPrice(token, row["active_unit_price"])
        e.claim(token, row["cohort_balance"])
        e.lp.mint(e.pool, 1, sender=e.gov.address)
        assets.append(token)
    return assets


@pytest.mark.parametrize("health", ["healthy", "unpriceable", "under_backed"])
def test_eleven_saved_dust_claims_do_not_gate_liquidation(legacy_env, health):
    e = legacy_env
    e.deposit(e.alice, 600 * WAD)
    assets = seed_dust(e)
    quotes = []
    for token, row in zip(assets, PROVENANCE["dust_claims"]):
        quote = e.pd.getUsdValue(token, row["cohort_balance"], True)
        assert quote == row["active_usd_value"]
        quotes.append(quote)
        assert e.pool.claimableBalances(e.lp, token) == row["cohort_balance"]
        assert e.pool.totalClaimableBalances(token) == row["total_claimable_balance"]
    assert len(quotes) == 11 and sum(v == 1 for v in quotes) == 6
    assert sum(r["cohort_balance"] * r["active_unit_price"] // 10**r["decimals"] == 0
               for r in PROVENANCE["dust_claims"]) == 5
    assert e.pool.getTotalAmountForUser(e.alice, e.lp) == 600 * WAD + sum(quotes)
    if health == "unpriceable":
        e.prices.setPrice(assets[0], 0)
        with boa.reverts("has price config, no price"):
            e.pool.getTotalAmountForUser(e.alice, e.lp)
    elif health == "under_backed":
        assets[-1].transfer(e.whale, assets[-1].balanceOf(e.pool), sender=e.pool.address)
        # Historical NAV still values recorded claims. Readiness is selected
        # swap admission, not a certification of unrelated claim backing.
        assert e.pool.getTotalAmountForUser(e.alice, e.lp) == 600 * WAD + sum(quotes)
    assert e.ready()
    trace = list(call_tree(e.book._computation))
    assert not any(c.msg.code_address == bytes.fromhex(token.address[2:]) for c in trace for token in assets)
    for signature in ("claimableAssets(address,uint256)", "numClaimableAssets(address)", "getTotalValue(address)", "getTotalAmountForUser(address,address)"):
        assert not calls_to(e.book._computation, e.pool.address, signature)
    liquidatable(e)
    shares = e.pool.userBalances(e.alice, e.lp)
    e.teller.liquidateUser(e.bob, False, sender=e.sally)
    assert len(filter_logs(e.teller, "CollateralSwappedWithStabPool")) == 1
    assert e.pool.userBalances(e.alice, e.lp) == shares
    for token, row in zip(assets, PROVENANCE["dust_claims"]):
        assert e.pool.claimableBalances(e.lp, token) == row["cohort_balance"]
        assert e.pool.totalClaimableBalances(token) == row["total_claimable_balance"]


def test_readiness_cost_does_not_grow_with_unrelated_claim_count(legacy_env):
    e = legacy_env
    e.deposit(e.alice, 600 * WAD)
    measurements = []
    for count in (0, 11, 25):
        if count == 11:
            seed_dust(e)
        elif count == 25:
            for i in range(14):
                claim = e.token(f"Unpriced{i}")
                e.claim(claim, 1)
                e.lp.mint(e.pool, 1, sender=e.gov.address)
        assert e.lp.balanceOf(e.pool) == 600 * WAD
        assert e.pool.numClaimableAssets(e.lp) == (count + 1 if count else 0)
        with boa.env.anchor():
            assert e.ready()
            computation = e.book._computation
            calls = [(c.msg.code_address.hex(), bytes(c.msg.data).hex()) for c in call_tree(computation)][1:]
            measurements.append((count, computation.get_gas_used(), calls))
    assert measurements[0][1:] == measurements[1][1:] == measurements[2][1:]
    print("LOCAL_READINESS_COST", [(n, gas, len(calls)) for n, gas, calls in measurements])
    # This is a deterministic local comparison, not live oracle gas qualification.
    liquidatable(e)
    e.teller.liquidateUser(e.bob, False, sender=e.sally)
    assert len(filter_logs(e.teller, "CollateralSwappedWithStabPool")) == 1
    assert e.pool.numClaimableAssets(e.lp) == 27  # 25 unrelated plus incoming collateral


def test_pricedesk_failure_propagates_and_rolls_back(legacy_env):
    e = legacy_env
    e.deposit(e.alice, 600 * WAD)
    liquidatable(e)
    e.prices.setPrice(e.lp, 2**256 - 1)  # real PriceDesk multiplication must raise
    before = (pool_state(e, e.alice), debt(e), e.ordinary.getTotalAmountForUser(e.bob, e.collateral))
    with boa.reverts():
        e.ready()
    with boa.reverts():
        e.teller.liquidateUser(e.bob, False, sender=e.sally)
    assert (pool_state(e, e.alice), debt(e), e.ordinary.getTotalAmountForUser(e.bob, e.collateral)) == before


@pytest.mark.parametrize("board", ["alpha", "charlie"])
def test_empty_legacy_pool_proposal_and_execution(legacy_env, board):
    e = legacy_env
    contract = getattr(e, board)
    if board == "charlie":
        storage_write(e.mc, None, "preferredStabVaultId", [], 0)
    assert e.pool.vaultAssets(1) == ZERO_ADDRESS
    assert e.book.hasStabilityPoolInterface(e.pool, e.sg, ZERO_ADDRESS)
    assert not e.ready(e.sg)
    setter = contract.setPriorityStabVaults if board == "alpha" else contract.setPreferredStabVaultId
    value = [(1, e.sg.address)] if board == "alpha" else 1
    with boa.reverts("no perms"):
        setter(value, sender=e.bob)
    action = setter(value, sender=e.gov.address)
    assert contract.hasPendingAction(action)
    assert not contract.executePendingAction(action, sender=e.gov.address)
    mature(contract, action)
    assert contract.executePendingAction(action, sender=e.gov.address)
    assert not contract.hasPendingAction(action)
    if board == "charlie":
        assert e.mc.preferredStabVaultId() == 1
    else:
        assert e.mc.getPriorityStabVaults() == [(1, e.sg.address)]


@pytest.mark.parametrize("board", ["alpha", "charlie"])
@pytest.mark.parametrize("stage", ["proposal", "execution"])
@pytest.mark.parametrize("condition", ["paused", "unsupported", "invalid_row", "no_contract"])
def test_structural_probe_preserves_caller_policy(legacy_env, board, stage, condition):
    e = legacy_env
    contract = getattr(e, board)
    if board == "charlie":
        storage_write(e.mc, None, "preferredStabVaultId", [], 0)
    setter = contract.setPriorityStabVaults if board == "alpha" else contract.setPreferredStabVaultId
    value = [(1, e.sg.address)] if board == "alpha" else 1
    action = None
    if stage == "execution":
        action = setter(value, sender=e.gov.address)
        mature(contract, action)
    if condition == "paused":
        e.pool.pause(True, sender=e.alpha.address)
    elif condition == "unsupported":
        e.configure(e.sg, _vaultIds=[3], _debtTerms=e.terms(0, 0, 0, 0, 0, 0))
    elif condition == "invalid_row":
        storage_write(e.book, "registry", "numAddrs", [], 1)
    else:
        storage_write(e.book, "registry", "addrInfo", [1], e.bob)
    with boa.reverts():
        if stage == "proposal":
            setter(value, sender=e.gov.address)
        else:
            contract.executePendingAction(action, sender=e.gov.address)
    if action is not None:
        assert contract.hasPendingAction(action)


@pytest.mark.parametrize("stage", ["proposal", "execution"])
def test_charlie_still_rejects_reserved_sgreen(legacy_env, stage):
    e = legacy_env
    storage_write(e.mc, None, "preferredStabVaultId", [], 0)
    action = None
    if stage == "execution":
        action = e.charlie.setPreferredStabVaultId(1, sender=e.gov.address)
        mature(e.charlie, action)
    storage_write(e.pool, "stabVault", "totalClaimableBalances", [e.sg], 1)
    assert e.book.hasStabilityPoolInterface(e.pool, e.sg, e.sg)
    with boa.reverts("asset reserved for claims"):
        if action is None:
            e.charlie.setPreferredStabVaultId(1, sender=e.gov.address)
        else:
            e.charlie.executePendingAction(action, sender=e.gov.address)
    if action is not None:
        assert e.charlie.hasPendingAction(action)


def test_nav_larger_than_cash_sizes_target_but_only_delivered_tokens_repay(legacy_env):
    e = legacy_env
    e.borrower(e.bob)
    e.deposit(e.bob, 100 * WAD)
    claim = e.token()
    e.prices.setPrice(claim, WAD)
    e.claim(claim, 1000 * WAD, paid=90 * WAD)
    nav = 1010 * WAD
    assert e.nav() == (e.lp.address, nav)
    assert e.dl.getDeleverageInfo(e.bob) == (nav, 0)
    cash = e.lp.balanceOf(e.pool)
    assert cash == 10 * WAD
    shares = e.pool.userBalances(e.bob, e.lp)
    burned_shares = e.pool.valueToShares(e.lp, cash, True)
    assert e.dl.deleverageForWithdrawal(e.bob, 3, e.collateral, 500 * WAD, sender=e.teller.address)
    event = filter_logs(e.dl, "DeleverageUser")[0]
    assert event.targetRepayAmount == 150 * WAD
    assert event.collateralValueRepaid == event.debtToClear == cash
    assert debt(e) == 300 * WAD - cash
    assert e.lp.balanceOf(e.funds) == cash and e.lp.balanceOf(e.pool) == 0
    assert e.pool.userBalances(e.bob, e.lp) == shares - burned_shares > 0
    assert e.pool.claimableBalances(e.lp, claim) == 1000 * WAD
    assert e.nav() == (e.lp.address, 0)


@pytest.mark.parametrize("green_claim", [False, True])
def test_stabilization_reservation_blocks_both_payment_paths(legacy_env, green_claim):
    e = legacy_env
    e.deposit(e.alice, 600 * WAD)
    if green_claim:
        e.claim(e.green, 600 * WAD)
    assert e.ready()
    storage_write(e.pool, "stabVault", "totalClaimableBalances", [e.lp], 1)
    assert not e.ready()
    liquidatable(e)
    before = pool_state(e, e.alice)
    supply = e.green.totalSupply()
    e.teller.liquidateUser(e.bob, False, sender=e.sally)
    assert not filter_logs(e.teller, "CollateralSwappedWithStabPool")
    assert e.ledger.hasFungibleAuction(e.bob, 3, e.collateral)
    assert pool_state(e, e.alice) == before and e.green.totalSupply() == supply
