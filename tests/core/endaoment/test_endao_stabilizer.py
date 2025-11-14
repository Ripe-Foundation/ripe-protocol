import pytest
import boa

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS
from config.BluePrint import CORE_TOKENS, CURVE_PARAMS, ADDYS, WHALES
from conf_utils import filter_logs


@pytest.fixture(scope="module")
def usdc_token(fork, chainlink, governance):
    usdc = boa.from_etherscan(CORE_TOKENS[fork]["USDC"], name="usdc")
    assert chainlink.addNewPriceFeed(usdc, "0x7e860098F58bBFC8648a4311b374B1D669a2bc6B", sender=governance.address)
    boa.env.time_travel(blocks=chainlink.actionTimeLock() + 1)
    assert chainlink.confirmNewPriceFeed(usdc, sender=governance.address)
    return usdc


@pytest.fixture(scope="module")
def deployed_green_pool(
    green_token,
    deploy3r,
    usdc_token,
    fork,
):
    factory = boa.from_etherscan(ADDYS[fork]["CURVE_STABLE_FACTORY"])

    implementation_idx = 0
    blueprint_address = factory.pool_implementations(implementation_idx)
    blueprint = boa.from_etherscan(blueprint_address, "green pool").deployer

    green_pool_deploy = factory.deploy_plain_pool(
        CURVE_PARAMS[fork]["GREEN_POOL_NAME"],
        CURVE_PARAMS[fork]["GREEN_POOL_SYMBOL"],
        [usdc_token, green_token],
        CURVE_PARAMS[fork]["GREEN_POOL_A"],
        CURVE_PARAMS[fork]["GREEN_POOL_FEE"],
        CURVE_PARAMS[fork]["GREEN_POOL_OFFPEG_MULTIPLIER"],
        CURVE_PARAMS[fork]["GREEN_POOL_MA_EXP_TIME"],
        implementation_idx,
        [0, 0],
        [b"", b""],
        [ZERO_ADDRESS, ZERO_ADDRESS],
        sender=deploy3r,
    )
    blueprint.at(green_pool_deploy) # register for later lookup_contract
    return green_pool_deploy


@pytest.fixture(scope="module")
def addSeedGreenLiq(
    green_token,
    deployed_green_pool,
    whale,
    fork,
    usdc_token,
    bob,
):
    def addSeedGreenLiq():
        green_pool = boa.env.lookup_contract(deployed_green_pool)

        # usdc
        usdc_amount = 10_000 * (10 ** usdc_token.decimals())
        usdc_token.transfer(bob, usdc_amount, sender=WHALES[fork]["usdc"])
        usdc_token.approve(green_pool, usdc_amount, sender=bob)

        # green
        green_amount = 10_000 * EIGHTEEN_DECIMALS
        green_token.transfer(bob, green_amount, sender=whale)
        green_token.approve(green_pool, green_amount, sender=bob)

        # add liquidity
        green_pool.add_liquidity([usdc_amount, green_amount], 0, bob, sender=bob)

    yield addSeedGreenLiq


@pytest.fixture(scope="module")
def swapGreenForUsdc(
    green_token,
    deployed_green_pool,
    whale,
    bob,
):
    def swapGreenForUsdc(_greenAmount):
        green_pool = boa.env.lookup_contract(deployed_green_pool)

        green_token.transfer(bob, _greenAmount, sender=whale)
        green_token.approve(green_pool, _greenAmount, sender=bob)
        received_usdc = green_pool.exchange(1, 0, _greenAmount, 0, bob, sender=bob)

        return received_usdc

    yield swapGreenForUsdc


@pytest.fixture(scope="module")
def swapUsdcForGreen(
    deployed_green_pool,
    fork,
    usdc_token,
    bob,
):
    def swapUsdcForGreen(_usdcAmount):
        green_pool = boa.env.lookup_contract(deployed_green_pool)

        usdc_token.transfer(bob, _usdcAmount, sender=WHALES[fork]["usdc"])
        usdc_token.approve(green_pool, _usdcAmount, sender=bob)
        received_green = green_pool.exchange(0, 1, _usdcAmount, 0, bob, sender=bob)

        return received_green

    yield swapUsdcForGreen


@pytest.fixture(scope="module")
def setGreenRefConfig(
    deployed_green_pool,
    curve_prices,
    governance,
):
    def setGreenRefConfig(
        _stabilizerAdjustWeight = 50_00,
        _stabilizerMaxPoolDebt = 1_000_000 * EIGHTEEN_DECIMALS,
    ):
        aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 50_00, 0, _stabilizerAdjustWeight, _stabilizerMaxPoolDebt, sender=governance.address)
        boa.env.time_travel(blocks=curve_prices.actionTimeLock())
        assert curve_prices.confirmGreenRefPoolConfig(aid, sender=governance.address)

    yield setGreenRefConfig


@pytest.fixture(scope="module", autouse=True)
def setup_mock_undy_v2(mock_undy_v2):
    # legacy curve underscore lego is 10
    mock_undy_v2.setUseThisLegoId(10)


####################
# Green Stabilizer #
####################


@pytest.base
def test_endao_stabilizer_add_green(
    setGreenRefConfig,
    endaoment,
    endaoment_funds,
    curve_prices,
    addSeedGreenLiq,
    swapUsdcForGreen,
    usdc_token,
    _test,
    switchboard_delta,
    deployed_green_pool,
    ledger,
):
    addSeedGreenLiq()
    setGreenRefConfig(_stabilizerAdjustWeight=100_00)
    green_pool = boa.env.lookup_contract(deployed_green_pool)

    # imablance pool, has more usdc
    large_usdc_swap = 5_000 * (10 ** usdc_token.decimals())
    swapUsdcForGreen(large_usdc_swap)

    # check the imbalanced pool state
    na, new_ratio = curve_prices.getCurvePoolData()
    _test(new_ratio, 25_00)

    # test expected green amount
    expected_green_amount = endaoment.getGreenAmountToAddInStabilizer()
    _test(expected_green_amount, 10_000 * EIGHTEEN_DECIMALS)

    # stabilize pool
    assert endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)

    log = filter_logs(endaoment, "StabilizerPoolLiqAdded")[0]
    assert log.pool == green_pool.address
    _test(log.greenAmountAdded, 10_000 * EIGHTEEN_DECIMALS) # 100% weight
    assert log.lpReceived != 0
    assert log.poolDebtAdded == log.greenAmountAdded

    # test ledger pool debt
    assert ledger.greenPoolDebt(green_pool) == log.poolDebtAdded

    # test lp balance
    assert green_pool.balanceOf(endaoment_funds) == log.lpReceived


@pytest.base
def test_endao_stabilizer_remove_green(
    setGreenRefConfig,
    endaoment,
    endaoment_funds,
    curve_prices,
    addSeedGreenLiq,
    swapGreenForUsdc,
    _test,
    switchboard_delta,
    green_token,
    deployed_green_pool,
    bob,
):
    addSeedGreenLiq()
    setGreenRefConfig(_stabilizerAdjustWeight=50_00)
    green_pool = boa.env.lookup_contract(deployed_green_pool)

    # move seed lp into endaoment_funds
    green_pool.transfer(endaoment_funds, green_pool.balanceOf(bob), sender=bob)
    pre_lp = green_pool.balanceOf(endaoment_funds)

    # imablance pool, has more green
    large_green_swap = 5_000 * EIGHTEEN_DECIMALS
    swapGreenForUsdc(large_green_swap)

    # check the imbalanced pool state
    na, new_ratio = curve_prices.getCurvePoolData()
    _test(new_ratio, 75_00)

    # test expected green amount
    expected_green_amount = endaoment.getGreenAmountToRemoveInStabilizer()
    _test(expected_green_amount, 5_000 * EIGHTEEN_DECIMALS) # 50% weight

    # stabilize pool
    assert endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)

    log = filter_logs(endaoment, "StabilizerPoolLiqRemoved")[0]
    assert log.pool == green_pool.address
    _test(log.greenAmountRemoved, 5_000 * EIGHTEEN_DECIMALS) # 50% weight
    assert log.lpBurned != 0
    assert log.debtRepaid == 0

    # test balances
    assert green_pool.balanceOf(endaoment_funds) == pre_lp - log.lpBurned
    assert green_token.balanceOf(endaoment_funds) == log.greenAmountRemoved


@pytest.base
def test_endao_stabilizer_balanced_pool(
    setGreenRefConfig,
    endaoment,
    addSeedGreenLiq,
    switchboard_delta,
):
    # Balanced pool should not trigger stabilization
    addSeedGreenLiq()
    setGreenRefConfig(_stabilizerAdjustWeight=50_00)
    
    # Pool is already balanced (50/50), so stabilizer should return False
    result = endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)
    assert not result # No adjustment needed


@pytest.base
def test_endao_stabilizer_no_config(
    endaoment,
    switchboard_delta,
):
    # Should return False when no stabilizer config is set
    result = endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)
    assert not result


@pytest.base
def test_endao_stabilizer_different_weights(
    setGreenRefConfig,
    endaoment,
    addSeedGreenLiq,
    swapUsdcForGreen,
    usdc_token,
    _test,
    switchboard_delta,
):
    # Test with 25% weight
    addSeedGreenLiq()
    setGreenRefConfig(_stabilizerAdjustWeight=25_00)
    
    # Create imbalance
    large_usdc_swap = 5_000 * (10 ** usdc_token.decimals())
    swapUsdcForGreen(large_usdc_swap)
    
    # Test expected green amount with 25% weight
    expected_green_amount = endaoment.getGreenAmountToAddInStabilizer()
    _test(expected_green_amount, 2_500 * EIGHTEEN_DECIMALS) # 25% of 10k
    
    # Stabilize pool
    assert endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)
    
    log = filter_logs(endaoment, "StabilizerPoolLiqAdded")[0]
    _test(log.greenAmountAdded, 2_500 * EIGHTEEN_DECIMALS) # 25% weight


@pytest.base
def test_endao_stabilizer_max_debt_reached(
    setGreenRefConfig,
    endaoment,
    addSeedGreenLiq,
    swapUsdcForGreen,
    usdc_token,
    _test,
    switchboard_delta,
    ledger,
    deployed_green_pool,
):
    # Test when max pool debt is reached
    addSeedGreenLiq()
    max_debt = 5_000 * EIGHTEEN_DECIMALS  # Set low max debt
    setGreenRefConfig(_stabilizerAdjustWeight=100_00, _stabilizerMaxPoolDebt=max_debt)
    
    # Create imbalance
    large_usdc_swap = 6_000 * (10 ** usdc_token.decimals())
    swapUsdcForGreen(large_usdc_swap)
    
    # Expected green should be limited by max debt
    expected_green_amount = endaoment.getGreenAmountToAddInStabilizer()
    _test(expected_green_amount, max_debt) # Limited by max debt
    
    # Stabilize pool
    assert endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)
    
    log = filter_logs(endaoment, "StabilizerPoolLiqAdded")[0]
    _test(log.greenAmountAdded, max_debt)
    
    # Pool debt should equal max debt
    assert ledger.greenPoolDebt(deployed_green_pool) == max_debt


@pytest.base
def test_endao_stabilizer_with_leftover_green(
    setGreenRefConfig,
    endaoment,
    addSeedGreenLiq,
    swapUsdcForGreen,
    usdc_token,
    _test,
    switchboard_delta,
    green_token,
    whale,
    deployed_green_pool,
    ledger,
):
    # Test when endaoment already has green tokens
    addSeedGreenLiq()
    setGreenRefConfig(_stabilizerAdjustWeight=100_00)
    
    # Give endaoment some green tokens
    leftover_green = 3_000 * EIGHTEEN_DECIMALS
    green_token.transfer(endaoment, leftover_green, sender=whale)
    
    # Create imbalance
    large_usdc_swap = 5_000 * (10 ** usdc_token.decimals())
    swapUsdcForGreen(large_usdc_swap)
    
    # Stabilize pool
    assert endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)
    
    log = filter_logs(endaoment, "StabilizerPoolLiqAdded")[0]
    _test(log.greenAmountAdded, 10_000 * EIGHTEEN_DECIMALS)
    
    # Pool debt should only be the newly minted amount
    expected_new_debt = 10_000 * EIGHTEEN_DECIMALS - leftover_green
    _test(log.poolDebtAdded, expected_new_debt)
    assert ledger.greenPoolDebt(deployed_green_pool) == log.poolDebtAdded


@pytest.base
def test_endao_stabilizer_remove_with_debt_repayment(
    setGreenRefConfig,
    endaoment,
    addSeedGreenLiq,
    swapGreenForUsdc,
    swapUsdcForGreen,
    usdc_token,
    switchboard_delta,
    deployed_green_pool,
    bob,
    ledger,
):
    # First create some pool debt by adding liquidity
    addSeedGreenLiq()
    setGreenRefConfig(_stabilizerAdjustWeight=100_00)
    
    # Create imbalance and add liquidity to create debt
    large_usdc_swap = 5_000 * (10 ** usdc_token.decimals())
    swapUsdcForGreen(large_usdc_swap)
    assert endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)
    
    # Check debt was created
    pool_debt = ledger.greenPoolDebt(deployed_green_pool)
    assert pool_debt > 0
    
    # Move all LP tokens to endaoment
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    green_pool.transfer(endaoment, green_pool.balanceOf(bob), sender=bob)
    
    # Now create opposite imbalance (more green)
    large_green_swap = 8_000 * EIGHTEEN_DECIMALS
    swapGreenForUsdc(large_green_swap)
    
    # Set different weight for removal
    setGreenRefConfig(_stabilizerAdjustWeight=50_00)
    
    # Stabilize (should remove liquidity and repay debt)
    assert endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)
    
    log = filter_logs(endaoment, "StabilizerPoolLiqRemoved")[0]
    assert log.debtRepaid > 0
    assert log.greenAmountRemoved > 0
    
    # Pool debt should be reduced by exactly the amount repaid
    new_pool_debt = ledger.greenPoolDebt(deployed_green_pool)
    expected_new_debt = pool_debt - log.debtRepaid
    assert new_pool_debt == expected_new_debt
    assert new_pool_debt < pool_debt  # Additional safety check


@pytest.base
def test_endao_stabilizer_no_lp_tokens_to_remove(
    setGreenRefConfig,
    endaoment,
    addSeedGreenLiq,
    swapGreenForUsdc,
    switchboard_delta,
):
    # Test when endaoment has no LP tokens but pool needs rebalancing
    addSeedGreenLiq()
    setGreenRefConfig(_stabilizerAdjustWeight=50_00)
    
    # Create imbalance (more green)
    large_green_swap = 5_000 * EIGHTEEN_DECIMALS
    swapGreenForUsdc(large_green_swap)
    
    # Endaoment has no LP tokens, so should return False
    result = endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)
    assert not result


@pytest.base
def test_endao_stabilizer_view_functions(
    setGreenRefConfig,
    endaoment,
    endaoment_funds,
    addSeedGreenLiq,
    swapUsdcForGreen,
    swapGreenForUsdc,
    usdc_token,
    _test,
    deployed_green_pool,
    bob,
):
    addSeedGreenLiq()
    setGreenRefConfig(_stabilizerAdjustWeight=75_00)
    
    # Test add scenario
    large_usdc_swap = 5_000 * (10 ** usdc_token.decimals())
    swapUsdcForGreen(large_usdc_swap)
    
    add_amount = endaoment.getGreenAmountToAddInStabilizer()
    _test(add_amount, 7_500 * EIGHTEEN_DECIMALS) # 75% of 10k
    
    # Should return 0 for remove in this scenario
    remove_amount = endaoment.getGreenAmountToRemoveInStabilizer()
    assert remove_amount == 0
    
    # Now test remove scenario
    # First rebalance pool and give endaoment_funds LP tokens
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    green_pool.transfer(endaoment_funds, green_pool.balanceOf(bob), sender=bob)
    
    # Swap back to balance, then create opposite imbalance
    large_green_swap = 8_000 * EIGHTEEN_DECIMALS
    swapGreenForUsdc(large_green_swap)
    
    remove_amount = endaoment.getGreenAmountToRemoveInStabilizer()
    assert remove_amount > 0
    
    # Should return 0 for add in this scenario
    add_amount = endaoment.getGreenAmountToAddInStabilizer()
    assert add_amount == 0


@pytest.base
def test_endao_stabilizer_no_config_view_functions(
    endaoment,
):
    # View functions should return 0 when no config is set
    add_amount = endaoment.getGreenAmountToAddInStabilizer()
    assert add_amount == 0
    
    remove_amount = endaoment.getGreenAmountToRemoveInStabilizer()
    assert remove_amount == 0


@pytest.base
def test_endao_stabilizer_permissions(
    setGreenRefConfig,
    endaoment,
    addSeedGreenLiq,
    alice,
):
    # Test that only switchboard can call stabilizer
    addSeedGreenLiq()
    setGreenRefConfig()
    
    # Should revert when called by non-switchboard address
    with boa.reverts("no perms"):
        endaoment.stabilizeGreenRefPool(sender=alice)


@pytest.base
def test_endao_stabilizer_paused_contract(
    setGreenRefConfig,
    endaoment,
    addSeedGreenLiq,
    switchboard_delta,
):
    # Test that stabilizer respects contract pause
    addSeedGreenLiq()
    setGreenRefConfig()
    
    # Pause the contract
    endaoment.pause(True, sender=switchboard_delta.address)
    
    # Should revert when contract is paused
    with boa.reverts("contract paused"):
        endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)


#############
# Pool Debt #
#############


@pytest.base
def test_endao_repay_pool_debt_directly(
    setGreenRefConfig,
    endaoment,
    endaoment_funds,
    addSeedGreenLiq,
    swapUsdcForGreen,
    usdc_token,
    switchboard_delta,
    green_token,
    whale,
    deployed_green_pool,
    ledger,
    _test,
):
    # Test the repayPoolDebt function directly
    addSeedGreenLiq()
    setGreenRefConfig(_stabilizerAdjustWeight=100_00)
    
    # Create debt by stabilizing an imbalanced pool
    large_usdc_swap = 5_000 * (10 ** usdc_token.decimals())
    swapUsdcForGreen(large_usdc_swap)
    assert endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)
    
    # Check debt was created
    initial_debt = ledger.greenPoolDebt(deployed_green_pool)
    assert initial_debt > 0
    
    # Give endaoment_funds extra green for repayment
    extra_green = 5_000 * EIGHTEEN_DECIMALS  # Enough to cover any repayment
    green_token.transfer(endaoment_funds, extra_green, sender=whale)
    green_balance_before = green_token.balanceOf(endaoment_funds)
    
    # Repay partial debt (request more than we plan to actually repay)
    requested_repay = min(3_000 * EIGHTEEN_DECIMALS, initial_debt)
    assert endaoment.repayPoolDebt(deployed_green_pool, requested_repay, sender=switchboard_delta.address)

    # Check event was emitted
    log = filter_logs(endaoment, "PoolDebtRepaid")[0]
    assert log.pool == deployed_green_pool
    actual_repay_amount = log.amount  # This is what was actually repaid
    
    # The actual repay amount should be the minimum of requested, available green, and debt
    expected_repay = min(requested_repay, green_balance_before, initial_debt)
    _test(log.amount, expected_repay)

    # Check debt was reduced by exactly the actual repay amount
    final_debt = ledger.greenPoolDebt(deployed_green_pool)
    expected_debt = initial_debt - actual_repay_amount
    assert final_debt == expected_debt

    # Check green was burned (balance should decrease)
    green_balance_after = green_token.balanceOf(endaoment_funds)
    green_burned = green_balance_before - green_balance_after
    _test(green_burned, actual_repay_amount)


@pytest.base 
def test_endao_repay_pool_debt_max_amount(
    setGreenRefConfig,
    endaoment,
    addSeedGreenLiq,
    swapUsdcForGreen,
    usdc_token,
    switchboard_delta,
    green_token,
    whale,
    deployed_green_pool,
    ledger,
    _test,
):
    # Test repaying more than the debt (should only repay what's owed)
    addSeedGreenLiq()
    setGreenRefConfig(_stabilizerAdjustWeight=100_00)
    
    # Create debt
    large_usdc_swap = 3_000 * (10 ** usdc_token.decimals())
    swapUsdcForGreen(large_usdc_swap)
    assert endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)
    
    initial_debt = ledger.greenPoolDebt(deployed_green_pool)
    assert initial_debt > 0
    
    # Give endaoment way more green than needed
    excess_green = initial_debt + (5_000 * EIGHTEEN_DECIMALS)
    green_token.transfer(endaoment, excess_green, sender=whale)
    
    # Try to repay more than the debt
    huge_repay_amount = initial_debt * 2
    assert endaoment.repayPoolDebt(deployed_green_pool, huge_repay_amount, sender=switchboard_delta.address)

    # Check that only the actual debt amount was burned
    log = filter_logs(endaoment, "PoolDebtRepaid")[0]
    _test(log.amount, initial_debt)  # Should equal initial debt, not huge_repay_amount

    # Should only repay the actual debt amount
    final_debt = ledger.greenPoolDebt(deployed_green_pool)
    assert final_debt == 0  # All debt should be repaid


#####################
# Partner Liquidity #
#####################


def test_endao_mint_partner_liquidity_basic(
    endaoment,
    endaoment_funds,
    switchboard_delta,
    alpha_token,
    alpha_token_whale,
    green_token,
    mock_price_source,
    _test,
):
    # Test basic mintPartnerLiquidity functionality
    partner = alpha_token_whale
    asset = alpha_token
    amount = 1_000 * EIGHTEEN_DECIMALS
    mock_price_source.setPrice(alpha_token, 1 * EIGHTEEN_DECIMALS)

    # Approve endaoment to spend partner's tokens
    pre_bal = alpha_token.balanceOf(partner)
    alpha_token.approve(endaoment, amount, sender=partner)
    
    # Mint partner liquidity
    green_minted = endaoment.mintPartnerLiquidity(partner, asset, amount, sender=switchboard_delta.address)
    
    # Check event was emitted
    log = filter_logs(endaoment, "PartnerLiquidityMinted")[0]
    assert log.partner == partner
    assert log.asset == asset.address
    _test(log.partnerAmount, amount)
    _test(log.greenMinted, green_minted)
    _test(green_minted, amount)
    
    # Check balances
    assert alpha_token.balanceOf(endaoment_funds) == amount
    assert green_token.balanceOf(endaoment_funds) == green_minted
    assert alpha_token.balanceOf(partner) == pre_bal - amount


def test_endao_mint_partner_liquidity_max_amount(
    endaoment,
    endaoment_funds,
    switchboard_delta,
    alpha_token,
    alpha_token_whale,
    green_token,
    _test,
    mock_price_source,
):
    # Test mintPartnerLiquidity with max_value(uint256)
    partner = alpha_token_whale
    asset = alpha_token
    partner_balance = alpha_token.balanceOf(partner)
    mock_price_source.setPrice(alpha_token, 2 * EIGHTEEN_DECIMALS)

    # Approve endaoment to spend partner's tokens
    alpha_token.approve(endaoment, partner_balance, sender=partner)
    
    # Mint partner liquidity with max amount
    green_minted = endaoment.mintPartnerLiquidity(partner, asset, sender=switchboard_delta.address)
    
    # Check event was emitted
    log = filter_logs(endaoment, "PartnerLiquidityMinted")[0]
    _test(log.partnerAmount, partner_balance)
    _test(log.greenMinted, green_minted)
    _test(green_minted, partner_balance * 2)
    
    # Check balances
    assert alpha_token.balanceOf(endaoment_funds) == partner_balance
    assert green_token.balanceOf(endaoment_funds) == green_minted
    assert alpha_token.balanceOf(partner) == 0  # All transferred


def test_endao_mint_partner_liquidity_different_decimals(
    endaoment,
    endaoment_funds,
    switchboard_delta,
    charlie_token,  # 6 decimals
    charlie_token_whale,
    green_token,
    mock_price_source,
    _test,
):
    # Test mintPartnerLiquidity with tokens of different decimals
    partner = charlie_token_whale
    asset = charlie_token
    amount = 1_000 * (10 ** charlie_token.decimals())  # 1M tokens with 6 decimals
    mock_price_source.setPrice(charlie_token, 1 * EIGHTEEN_DECIMALS)

    # Approve endaoment to spend partner's tokens
    pre_bal = charlie_token.balanceOf(partner)
    charlie_token.approve(endaoment, amount, sender=partner)
    
    # Mint partner liquidity
    green_minted = endaoment.mintPartnerLiquidity(partner, asset, amount, sender=switchboard_delta.address)
    
    # Check event was emitted
    log = filter_logs(endaoment, "PartnerLiquidityMinted")[0]
    assert log.partner == partner
    assert log.asset == asset.address
    _test(log.partnerAmount, amount)
    _test(log.greenMinted, green_minted)
    _test(green_minted, 1000 * EIGHTEEN_DECIMALS)
    
    # Check balances
    assert charlie_token.balanceOf(endaoment_funds) == amount
    assert green_token.balanceOf(endaoment_funds) == green_minted
    assert charlie_token.balanceOf(partner) == pre_bal - amount


def test_endao_mint_partner_liquidity_permissions(
    endaoment,
    alpha_token,
    alpha_token_whale,
    alice,
):
    # Test that only switchboard can call mintPartnerLiquidity
    partner = alpha_token_whale
    asset = alpha_token
    amount = 1_000 * (10 ** alpha_token.decimals())
    
    # Approve endaoment to spend partner's tokens
    alpha_token.approve(endaoment, amount, sender=partner)
    
    # Should revert when called by non-switchboard address
    with boa.reverts("no perms"):
        endaoment.mintPartnerLiquidity(partner, asset, amount, sender=alice)


def test_endao_mint_partner_liquidity_paused_contract(
    endaoment,
    switchboard_delta,
    alpha_token,
    alpha_token_whale,
):
    # Test that mintPartnerLiquidity respects contract pause
    partner = alpha_token_whale
    asset = alpha_token
    amount = 1_000 * (10 ** alpha_token.decimals())
    
    # Approve endaoment to spend partner's tokens
    alpha_token.approve(endaoment, amount, sender=partner)
    
    # Pause the contract
    endaoment.pause(True, sender=switchboard_delta.address)
    
    # Should revert when contract is paused
    with boa.reverts("contract paused"):
        endaoment.mintPartnerLiquidity(partner, asset, amount, sender=switchboard_delta.address)


def test_endao_mint_partner_liquidity_no_approval(
    endaoment,
    switchboard_delta,
    alpha_token,
    alpha_token_whale,
):
    # Test mintPartnerLiquidity without approval
    partner = alpha_token_whale
    asset = alpha_token
    amount = 1_000 * (10 ** alpha_token.decimals())
    
    # No approval given - should revert
    with boa.reverts("transfer failed"):
        endaoment.mintPartnerLiquidity(partner, asset, amount, sender=switchboard_delta.address)


def test_endao_mint_partner_liquidity_insufficient_approval(
    endaoment,
    switchboard_delta,
    alpha_token,
    alpha_token_whale,
):
    # Test mintPartnerLiquidity with insufficient approval
    partner = alpha_token_whale
    asset = alpha_token
    amount = 1_000 * (10 ** alpha_token.decimals())
    insufficient_approval = amount // 2
    
    # Approve less than requested amount
    alpha_token.approve(endaoment, insufficient_approval, sender=partner)
    
    # Should revert due to insufficient approval
    with boa.reverts("transfer failed"):
        endaoment.mintPartnerLiquidity(partner, asset, amount, sender=switchboard_delta.address)


def test_endao_mint_partner_liquidity_zero_balance(
    endaoment,
    switchboard_delta,
    alpha_token,
    alice,  # alice has no alpha tokens
):
    # Test mintPartnerLiquidity with partner having zero balance
    partner = alice
    asset = alpha_token
    amount = 1_000 * (10 ** alpha_token.decimals())
    
    # Approve endaoment to spend partner's tokens
    alpha_token.approve(endaoment, amount, sender=partner)
    
    # Should revert due to zero balance
    with boa.reverts("no asset to add"):
        endaoment.mintPartnerLiquidity(partner, asset, amount, sender=switchboard_delta.address)


def test_endao_mint_partner_liquidity_usd_value_calculation(
    endaoment,
    switchboard_delta,
    alpha_token,
    alpha_token_whale,
    price_desk,
    mock_price_source,
    _test,
):
    # Test that the USD value calculation is correct
    partner = alpha_token_whale
    asset = alpha_token
    amount = 1_000 * (10 ** alpha_token.decimals())
    
    # Set a price for the asset
    price_per_token = 2 * EIGHTEEN_DECIMALS  # $2 per token
    mock_price_source.setPrice(alpha_token, price_per_token)
    
    # Get expected USD value from price desk
    expected_usd_value = price_desk.getUsdValue(asset, amount, True)
    assert expected_usd_value > 0
    
    # Approve endaoment to spend partner's tokens
    alpha_token.approve(endaoment, amount, sender=partner)
    
    # Mint partner liquidity
    green_minted = endaoment.mintPartnerLiquidity(partner, asset, amount, sender=switchboard_delta.address)

    # Check event
    log = filter_logs(endaoment, "PartnerLiquidityMinted")[0]
    _test(log.greenMinted, expected_usd_value)

    # Check that green minted equals USD value
    _test(green_minted, expected_usd_value)


@pytest.base
def test_endao_add_partner_liquidity_basic(
    endaoment,
    endaoment_funds,
    deployed_green_pool,
    switchboard_delta,
    green_token,
    _test,
    fork,
    alice,
    usdc_token,
    ledger,
):
    green_pool = boa.env.lookup_contract(deployed_green_pool)

    # usdc
    usdc_whale = WHALES[fork]["usdc"]
    usdc_amount = 10_000 * (10 ** usdc_token.decimals())
    usdc_token.transfer(alice, usdc_amount, sender=usdc_whale)

    # setup
    partner = alice
    asset = usdc_token
    amount = 1_000 * (10 ** usdc_token.decimals())

    # Approve endaoment to spend partner's tokens
    usdc_token.approve(endaoment, amount, sender=partner)

    # Mint partner liquidity
    liquidityAdded, liqAmountA, liqAmountB = endaoment.addPartnerLiquidity(10, green_pool, partner, asset, amount, 0, sender=switchboard_delta.address)
    
    # Check event was emitted
    log = filter_logs(endaoment, "PartnerLiquidityAdded")[0]
    assert log.partner == partner
    assert log.asset == asset.address
    assert log.lpBalance == liquidityAdded

    _test(log.partnerAmount, liqAmountA)
    _test(liqAmountA, amount)
    _test(log.greenAmount, liqAmountB)
    _test(liqAmountB, 1_000 * EIGHTEEN_DECIMALS)
    
    # Check balances
    assert usdc_token.balanceOf(endaoment) == 0
    assert green_token.balanceOf(endaoment) == 0

    _test(log.lpBalance // 2, green_pool.balanceOf(partner))
    _test(log.lpBalance // 2, green_pool.balanceOf(endaoment_funds))

    _test(ledger.greenPoolDebt(green_pool), 1_000 * EIGHTEEN_DECIMALS)


@pytest.base
def test_endao_add_partner_liquidity_permissions(
    endaoment,
    deployed_green_pool,
    alice,
    bob,
    usdc_token,
    fork,
):
    # Test that only switchboard can call addPartnerLiquidity
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]
    amount = 1_000 * (10 ** usdc_token.decimals())
    
    # Setup partner with tokens
    usdc_token.transfer(alice, amount, sender=usdc_whale)
    usdc_token.approve(endaoment, amount, sender=alice)
    
    # Should revert when called by non-switchboard address
    with boa.reverts("no perms"):
        endaoment.addPartnerLiquidity(10, green_pool, alice, usdc_token, amount, 0, sender=bob)


@pytest.base
def test_endao_add_partner_liquidity_paused_contract(
    endaoment,
    deployed_green_pool,
    switchboard_delta,
    alice,
    usdc_token,
    fork,
):
    # Test that addPartnerLiquidity respects contract pause
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]
    amount = 1_000 * (10 ** usdc_token.decimals())
    
    # Setup partner with tokens
    usdc_token.transfer(alice, amount, sender=usdc_whale)
    usdc_token.approve(endaoment, amount, sender=alice)
    
    # Pause the contract
    endaoment.pause(True, sender=switchboard_delta.address)
    
    # Should revert when contract is paused
    with boa.reverts("contract paused"):
        endaoment.addPartnerLiquidity(10, green_pool, alice, usdc_token, amount, 0, sender=switchboard_delta.address)


@pytest.base
def test_endao_add_partner_liquidity_no_approval(
    endaoment,
    deployed_green_pool,
    switchboard_delta,
    alice,
    usdc_token,
    fork,
):
    # Test addPartnerLiquidity without token approval
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]
    amount = 1_000 * (10 ** usdc_token.decimals())
    
    # Give partner tokens but no approval
    usdc_token.transfer(alice, amount, sender=usdc_whale)
    
    # Should revert due to no approval
    with boa.reverts("transfer failed"):
        endaoment.addPartnerLiquidity(10, green_pool, alice, usdc_token, amount, 0, sender=switchboard_delta.address)


@pytest.base
def test_endao_add_partner_liquidity_insufficient_balance(
    endaoment,
    deployed_green_pool,
    switchboard_delta,
    alice,
    usdc_token,
):
    # Test addPartnerLiquidity when partner has insufficient balance
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    amount = 1_000 * (10 ** usdc_token.decimals())
    
    # Partner has no tokens but gives approval
    usdc_token.approve(endaoment, amount, sender=alice)
    
    # Should revert due to no asset to add
    with boa.reverts("no asset to add"):
        endaoment.addPartnerLiquidity(10, green_pool, alice, usdc_token, amount, 0, sender=switchboard_delta.address)


@pytest.base
def test_endao_add_partner_liquidity_max_amount(
    addSeedGreenLiq,
    endaoment,
    deployed_green_pool,
    switchboard_delta,
    alice,
    usdc_token,
    fork,
    ledger,
    _test,
):
    # Test addPartnerLiquidity with max_value(uint256)
    addSeedGreenLiq()
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]
    partner_balance = 5_000 * (10 ** usdc_token.decimals())
    
    # Give partner tokens
    usdc_token.transfer(alice, partner_balance, sender=usdc_whale)
    usdc_token.approve(endaoment, partner_balance, sender=alice)
    
    # Add partner liquidity with max amount (should use all partner's balance)
    liquidityAdded, liqAmountA, liqAmountB = endaoment.addPartnerLiquidity(10, green_pool, alice, usdc_token, sender=switchboard_delta.address)
    
    # Check event was emitted
    log = filter_logs(endaoment, "PartnerLiquidityAdded")[0]
    _test(log.partnerAmount, partner_balance)
    _test(log.greenAmount, 5_000 * EIGHTEEN_DECIMALS)
    
    # Check partner has no tokens left
    assert usdc_token.balanceOf(alice) == 0
    
    # Check pool debt was added
    _test(ledger.greenPoolDebt(green_pool), 5_000 * EIGHTEEN_DECIMALS)


@pytest.base
def test_endao_add_partner_liquidity_min_lp_amount(
    endaoment,
    deployed_green_pool,
    switchboard_delta,
    alice,
    usdc_token,
    fork,
):
    # Test addPartnerLiquidity with minimum LP amount requirement
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]
    amount = 1_000 * (10 ** usdc_token.decimals())
    
    # Give partner tokens
    usdc_token.transfer(alice, amount, sender=usdc_whale)
    usdc_token.approve(endaoment, amount, sender=alice)
    
    # Set unrealistically high minimum LP amount (should fail)
    unrealistic_min_lp = 1_000_000 * EIGHTEEN_DECIMALS
    
    # Should revert due to insufficient LP amount received
    with boa.reverts():  # The exact error depends on the lego implementation
        endaoment.addPartnerLiquidity(10, green_pool, alice, usdc_token, amount, unrealistic_min_lp, sender=switchboard_delta.address)


@pytest.base
def test_endao_add_partner_liquidity_lp_sharing(
    addSeedGreenLiq,
    endaoment,
    endaoment_funds,
    deployed_green_pool,
    switchboard_delta,
    alice,
    usdc_token,
    fork,
    _test,
):
    # Test that LP tokens are properly shared between partner and endaoment_funds
    addSeedGreenLiq()
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]
    amount = 2_000 * (10 ** usdc_token.decimals())

    # Record initial LP balances
    initial_partner_lp = green_pool.balanceOf(alice)
    initial_endaoment_funds_lp = green_pool.balanceOf(endaoment_funds)
    
    # Give partner tokens
    usdc_token.transfer(alice, amount, sender=usdc_whale)
    usdc_token.approve(endaoment, amount, sender=alice)
    
    # Add partner liquidity
    liquidityAdded, liqAmountA, liqAmountB = endaoment.addPartnerLiquidity(10, green_pool, alice, usdc_token, amount, 0, sender=switchboard_delta.address)
    
    # Check LP tokens were shared 50/50
    log = filter_logs(endaoment, "PartnerLiquidityAdded")[0]
    total_lp_received = log.lpBalance

    partner_lp_received = green_pool.balanceOf(alice) - initial_partner_lp
    endaoment_funds_lp_received = green_pool.balanceOf(endaoment_funds) - initial_endaoment_funds_lp

    # Each should get half of the LP tokens
    _test(partner_lp_received, total_lp_received // 2)
    _test(endaoment_funds_lp_received, total_lp_received // 2)

    # Total should add up (accounting for potential rounding)
    assert partner_lp_received + endaoment_funds_lp_received >= total_lp_received - 1
    assert partner_lp_received + endaoment_funds_lp_received <= total_lp_received


@pytest.base
def test_endao_add_partner_liquidity_multiple_partners(
    addSeedGreenLiq,
    endaoment,
    deployed_green_pool,
    switchboard_delta,
    alice,
    bob,
    usdc_token,
    fork,
    ledger,
    _test,
):
    # Test multiple partners adding liquidity sequentially
    addSeedGreenLiq()
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]
    amount1 = 1_000 * (10 ** usdc_token.decimals())
    amount2 = 1_500 * (10 ** usdc_token.decimals())
    
    # First partner
    usdc_token.transfer(alice, amount1, sender=usdc_whale)
    usdc_token.approve(endaoment, amount1, sender=alice)
    
    liquidityAdded1, liqAmountA1, liqAmountB1 = endaoment.addPartnerLiquidity(10, green_pool, alice, usdc_token, amount1, 0, sender=switchboard_delta.address)
    
    # Second partner
    usdc_token.transfer(bob, amount2, sender=usdc_whale)
    usdc_token.approve(endaoment, amount2, sender=bob)
    
    liquidityAdded2, liqAmountA2, liqAmountB2 = endaoment.addPartnerLiquidity(10, green_pool, bob, usdc_token, amount2, 0, sender=switchboard_delta.address)
    
    # Verify both operations succeeded by checking that they returned valid results
    assert liquidityAdded1 > 0
    assert liquidityAdded2 > 0
    assert liqAmountA1 == amount1
    assert liqAmountA2 == amount2
    assert liqAmountB1 > 0  # Green tokens minted
    assert liqAmountB2 > 0  # Green tokens minted
    
    # Check total pool debt
    total_expected_debt = 1_000 * EIGHTEEN_DECIMALS + 1_500 * EIGHTEEN_DECIMALS
    _test(ledger.greenPoolDebt(green_pool), total_expected_debt)
    
    # Check both partners received LP tokens
    assert green_pool.balanceOf(alice) > 0
    assert green_pool.balanceOf(bob) > 0


@pytest.base
def test_endao_add_partner_liquidity_asset_price_validation(
    endaoment,
    deployed_green_pool,
    switchboard_delta,
    alice,
    alpha_token,  # Use alpha_token which doesn't have a price by default
    alpha_token_whale,
):
    # Test that addPartnerLiquidity validates asset has a price
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    amount = 1_000 * (10 ** alpha_token.decimals())
    
    # Give partner tokens but don't set price (getUsdValue will return 0)
    alpha_token.transfer(alice, amount, sender=alpha_token_whale)
    alpha_token.approve(endaoment, amount, sender=alice)
    
    # Should revert due to invalid asset (no USD value)
    with boa.reverts("invalid asset"):
        endaoment.addPartnerLiquidity(10, green_pool, alice, alpha_token, amount, 0, sender=switchboard_delta.address)


##################################
# Partner Liquidity - Self Tests #
##################################


@pytest.base
def test_endao_mint_partner_liquidity_self_as_partner(
    endaoment,
    endaoment_funds,
    switchboard_delta,
    usdc_token,
    green_token,
    fork,
    mock_price_source,
    _test,
):
    # Test mintPartnerLiquidity where partner is Endaoment itself
    usdc_whale = WHALES[fork]["usdc"]
    amount = 1_000 * (10 ** usdc_token.decimals())
    mock_price_source.setPrice(usdc_token, 1 * EIGHTEEN_DECIMALS)

    # Transfer funds into Endaoment before calling it
    usdc_token.transfer(endaoment, amount, sender=usdc_whale)

    pre_usdc_balance = usdc_token.balanceOf(endaoment)
    pre_green_balance = green_token.balanceOf(endaoment_funds)

    # Mint partner liquidity with endaoment as partner
    green_minted = endaoment.mintPartnerLiquidity(endaoment, usdc_token, amount, sender=switchboard_delta.address)

    # Check event was emitted
    log = filter_logs(endaoment, "PartnerLiquidityMinted")[0]
    assert log.partner == endaoment.address
    assert log.asset == usdc_token.address
    _test(log.partnerAmount, amount)
    _test(log.greenMinted, green_minted)
    _test(green_minted, amount * EIGHTEEN_DECIMALS // (10 ** usdc_token.decimals()))

    # Check balances - USDC stays in endaoment, green goes to endaoment_funds
    assert usdc_token.balanceOf(endaoment) == pre_usdc_balance  # No transfer needed
    assert green_token.balanceOf(endaoment_funds) == pre_green_balance + green_minted


@pytest.base
def test_endao_mint_partner_liquidity_self_max_amount(
    endaoment,
    switchboard_delta,
    usdc_token,
    fork,
    mock_price_source,
    _test,
):
    # Test mintPartnerLiquidity with max amount where partner is Endaoment itself
    usdc_whale = WHALES[fork]["usdc"]
    amount = 2_500 * (10 ** usdc_token.decimals())
    mock_price_source.setPrice(usdc_token, 1 * EIGHTEEN_DECIMALS)

    # Transfer funds into Endaoment
    usdc_token.transfer(endaoment, amount, sender=usdc_whale)
    endaoment_balance = usdc_token.balanceOf(endaoment)
    
    # Mint partner liquidity with max amount
    green_minted = endaoment.mintPartnerLiquidity(endaoment, usdc_token, sender=switchboard_delta.address)
    
    # Check event
    log = filter_logs(endaoment, "PartnerLiquidityMinted")[0]
    _test(log.partnerAmount, endaoment_balance)
    _test(log.greenMinted, green_minted)
    
    # Check all USDC balance was used
    expected_green = endaoment_balance * EIGHTEEN_DECIMALS // (10 ** usdc_token.decimals())
    _test(green_minted, expected_green)


@pytest.base
def test_endao_mint_partner_liquidity_self_insufficient_balance(
    endaoment,
    switchboard_delta,
    usdc_token,
):
    # Test mintPartnerLiquidity where Endaoment has insufficient balance
    amount = 1_000 * (10 ** usdc_token.decimals())
    
    # Don't transfer any funds to Endaoment
    assert usdc_token.balanceOf(endaoment) == 0
    
    # Should revert due to no asset to add
    with boa.reverts("no asset to add"):
        endaoment.mintPartnerLiquidity(endaoment, usdc_token, amount, sender=switchboard_delta.address)


@pytest.base
def test_endao_add_partner_liquidity_self_as_partner(
    addSeedGreenLiq,
    endaoment,
    endaoment_funds,
    deployed_green_pool,
    switchboard_delta,
    green_token,
    usdc_token,
    fork,
    ledger,
    _test,
):
    # Test addPartnerLiquidity where partner is Endaoment itself
    addSeedGreenLiq()
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]
    amount = 1_000 * (10 ** usdc_token.decimals())

    # Transfer funds into Endaoment before calling it
    usdc_token.transfer(endaoment, amount, sender=usdc_whale)

    pre_endaoment_funds_lp = green_pool.balanceOf(endaoment_funds)
    
    # Add partner liquidity with endaoment as partner
    liquidityAdded, liqAmountA, liqAmountB = endaoment.addPartnerLiquidity(
        10, green_pool, endaoment, usdc_token, amount, 0, sender=switchboard_delta.address
    )
    
    # Check event was emitted
    log = filter_logs(endaoment, "PartnerLiquidityAdded")[0]
    assert log.partner == endaoment.address
    assert log.asset == usdc_token.address
    assert log.lpBalance == liquidityAdded
    _test(log.partnerAmount, amount)
    _test(log.greenAmount, 1_000 * EIGHTEEN_DECIMALS)
    
    # Check balances - all assets should be consumed, all LP should go to endaoment_funds
    assert usdc_token.balanceOf(endaoment) == 0
    assert green_token.balanceOf(endaoment) == 0

    # Endaoment_funds should get ALL the LP tokens (not split since partner is self)
    total_lp_received = green_pool.balanceOf(endaoment_funds) - pre_endaoment_funds_lp
    _test(total_lp_received, liquidityAdded)

    # Check pool debt was added
    _test(ledger.greenPoolDebt(green_pool), 1_000 * EIGHTEEN_DECIMALS)


@pytest.base
def test_endao_add_partner_liquidity_self_max_amount(
    addSeedGreenLiq,
    endaoment,
    endaoment_funds,
    deployed_green_pool,
    switchboard_delta,
    usdc_token,
    fork,
    ledger,
    _test,
):
    # Test addPartnerLiquidity with max amount where partner is Endaoment itself
    addSeedGreenLiq()
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]
    amount = 3_000 * (10 ** usdc_token.decimals())

    # Transfer funds into Endaoment
    usdc_token.transfer(endaoment, amount, sender=usdc_whale)
    endaoment_balance = usdc_token.balanceOf(endaoment)

    pre_endaoment_funds_lp = green_pool.balanceOf(endaoment_funds)
    
    # Add partner liquidity with max amount
    liquidityAdded, liqAmountA, liqAmountB = endaoment.addPartnerLiquidity(
        10, green_pool, endaoment, usdc_token, sender=switchboard_delta.address
    )
    
    # Check event
    log = filter_logs(endaoment, "PartnerLiquidityAdded")[0]
    _test(log.partnerAmount, endaoment_balance)
    _test(log.greenAmount, 3_000 * EIGHTEEN_DECIMALS)

    # All LP tokens should go to endaoment_funds
    total_lp_received = green_pool.balanceOf(endaoment_funds) - pre_endaoment_funds_lp
    _test(total_lp_received, liquidityAdded)

    # Check pool debt
    _test(ledger.greenPoolDebt(green_pool), 3_000 * EIGHTEEN_DECIMALS)


@pytest.base
def test_endao_add_partner_liquidity_self_with_existing_green(
    addSeedGreenLiq,
    endaoment,
    endaoment_funds,
    deployed_green_pool,
    switchboard_delta,
    green_token,
    usdc_token,
    fork,
    whale,
    ledger,
    _test,
):
    # Test addPartnerLiquidity where EndaomentFunds already has green tokens
    addSeedGreenLiq()
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]
    usdc_amount = 1_000 * (10 ** usdc_token.decimals())
    green_amount = 500 * EIGHTEEN_DECIMALS

    # Transfer USDC to Endaoment and existing Green to EndaomentFunds
    usdc_token.transfer(endaoment, usdc_amount, sender=usdc_whale)
    green_token.transfer(endaoment_funds, green_amount, sender=whale)

    pre_endaoment_funds_lp = green_pool.balanceOf(endaoment_funds)
    
    # Add partner liquidity with endaoment as partner
    liquidityAdded, liqAmountA, liqAmountB = endaoment.addPartnerLiquidity(
        10, green_pool, endaoment, usdc_token, usdc_amount, 0, sender=switchboard_delta.address
    )
    
    # Check event
    log = filter_logs(endaoment, "PartnerLiquidityAdded")[0]
    _test(log.partnerAmount, usdc_amount)
    _test(log.greenAmount, 1_000 * EIGHTEEN_DECIMALS)  # Full amount needed

    # Check balances
    assert usdc_token.balanceOf(endaoment) == 0
    assert green_token.balanceOf(endaoment) == 0

    # All LP tokens should go to endaoment_funds
    total_lp_received = green_pool.balanceOf(endaoment_funds) - pre_endaoment_funds_lp
    _test(total_lp_received, liquidityAdded)

    # Pool debt should only be for newly minted green (1000 - 500 = 500)
    expected_new_debt = 1_000 * EIGHTEEN_DECIMALS - green_amount
    _test(ledger.greenPoolDebt(green_pool), expected_new_debt)


@pytest.base
def test_endao_add_partner_liquidity_self_insufficient_balance(
    endaoment,
    deployed_green_pool,
    switchboard_delta,
    usdc_token,
):
    # Test addPartnerLiquidity where Endaoment has insufficient balance
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    amount = 1_000 * (10 ** usdc_token.decimals())

    # Don't transfer any funds to Endaoment
    assert usdc_token.balanceOf(endaoment) == 0

    # Should revert due to no asset to add
    with boa.reverts("no asset to add"):
        endaoment.addPartnerLiquidity(10, green_pool, endaoment, usdc_token, amount, 0, sender=switchboard_delta.address)


###################################
# Profit Invariant Tests          #
###################################


@pytest.base
def test_green_stabilizer_profit_never_decreases_on_add(
    setGreenRefConfig,
    endaoment,
    endaoment_funds,
    deployed_green_pool,
    switchboard_delta,
    green_token,
    usdc_token,
    fork,
    ledger,
    addSeedGreenLiq,
):
    """Test that profit never decreases when adding green liquidity

    This test verifies a critical invariant: when the stabilizer adds green liquidity
    to rebalance the pool, the net profit position should never decrease.

    Profit is calculated as: (LP balance - LP debt equivalent) + net green balance
    Where LP debt is derived from (pool debt - green balance) / virtual price
    """
    addSeedGreenLiq()
    setGreenRefConfig(_stabilizerAdjustWeight=100_00)
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]

    # Create imbalance by adding USDC to pool (pool will have more USDC than green)
    usdc_add_amount = 50_000 * (10 ** usdc_token.decimals())
    usdc_token.transfer(endaoment, usdc_add_amount, sender=usdc_whale)
    usdc_token.approve(green_pool.address, usdc_add_amount, sender=endaoment.address)

    amounts = [usdc_add_amount, 0]
    green_pool.add_liquidity(amounts, 0, sender=endaoment.address)

    # Calculate initial profit using the new view function
    initial_profit = endaoment.calcProfitForStabilizer()
    initial_lp = green_pool.balanceOf(endaoment_funds)
    initial_green = green_token.balanceOf(endaoment_funds)
    initial_debt = ledger.greenPoolDebt(green_pool)

    # Run stabilizer to add green
    endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)

    # Calculate new profit
    new_profit = endaoment.calcProfitForStabilizer()
    new_lp = green_pool.balanceOf(endaoment_funds)
    new_green = green_token.balanceOf(endaoment_funds)
    new_debt = ledger.greenPoolDebt(green_pool)

    # CRITICAL INVARIANT: Profit should never decrease when stabilizing
    assert new_profit >= initial_profit, \
        f"Profit decreased! Initial: {initial_profit}, New: {new_profit}, " \
        f"LP change: {new_lp - initial_lp}, Green change: {new_green - initial_green}, " \
        f"Debt change: {new_debt - initial_debt}"


@pytest.base
def test_green_stabilizer_profit_never_decreases_on_remove(
    setGreenRefConfig,
    endaoment,
    endaoment_funds,
    deployed_green_pool,
    switchboard_delta,
    green_token,
    usdc_token,
    fork,
    whale,
    ledger,
    addSeedGreenLiq,
):
    """Test that profit never decreases when removing green liquidity

    This test verifies that when the stabilizer removes green liquidity (and potentially
    repays debt), the net profit position should never decrease. This is important because
    removing liquidity can repay debt, which should improve or maintain the profit position.
    """
    addSeedGreenLiq()
    setGreenRefConfig(_stabilizerAdjustWeight=100_00)
    green_pool = boa.env.lookup_contract(deployed_green_pool)

    # First create pool debt by adding partner liquidity
    usdc_whale = WHALES[fork]["usdc"]
    usdc_amount = 10_000 * (10 ** usdc_token.decimals())
    partner = boa.env.generate_address()

    # Transfer to partner and approve endaoment
    usdc_token.transfer(partner, usdc_amount, sender=usdc_whale)
    usdc_token.approve(endaoment, usdc_amount, sender=partner)

    endaoment.addPartnerLiquidity(10, green_pool, partner, usdc_token, usdc_amount, 0, sender=switchboard_delta.address)

    # Create imbalance by adding green to pool (pool will have more green than USDC)
    green_add_amount = 50_000 * EIGHTEEN_DECIMALS
    green_token.transfer(endaoment, green_add_amount, sender=whale)
    green_token.approve(green_pool.address, green_add_amount, sender=endaoment.address)

    amounts = [0, green_add_amount]
    green_pool.add_liquidity(amounts, 0, sender=endaoment.address)

    # Calculate initial profit
    initial_profit = endaoment.calcProfitForStabilizer()
    initial_lp = green_pool.balanceOf(endaoment_funds)
    initial_green = green_token.balanceOf(endaoment_funds)
    initial_debt = ledger.greenPoolDebt(green_pool)

    # Run stabilizer to remove green (and potentially repay debt)
    endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)

    # Calculate new profit
    new_profit = endaoment.calcProfitForStabilizer()
    new_lp = green_pool.balanceOf(endaoment_funds)
    new_green = green_token.balanceOf(endaoment_funds)
    new_debt = ledger.greenPoolDebt(green_pool)

    # CRITICAL INVARIANT: Profit should never decrease, especially when repaying debt
    assert new_profit >= initial_profit, \
        f"Profit decreased! Initial: {initial_profit}, New: {new_profit}, " \
        f"LP change: {new_lp - initial_lp}, Green change: {new_green - initial_green}, " \
        f"Debt change: {new_debt - initial_debt}"


@pytest.base
def test_green_stabilizer_profit_with_extreme_imbalance(
    setGreenRefConfig,
    endaoment,
    deployed_green_pool,
    switchboard_delta,
    usdc_token,
    fork,
    addSeedGreenLiq,
):
    """Test profit invariant with extreme pool imbalance (>80% one side)

    This is a stress test to ensure the profit invariant holds even when the pool
    is severely imbalanced. In extreme conditions, slippage and price impact are high,
    but the stabilizer should still maintain or improve the profit position.
    """
    addSeedGreenLiq()
    setGreenRefConfig(_stabilizerAdjustWeight=100_00)
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]

    # Create extreme imbalance
    extreme_amount = 500_000 * (10 ** usdc_token.decimals())
    usdc_token.transfer(endaoment, extreme_amount, sender=usdc_whale)
    usdc_token.approve(green_pool.address, extreme_amount, sender=endaoment.address)

    amounts = [extreme_amount, 0]
    green_pool.add_liquidity(amounts, 0, sender=endaoment.address)

    # Check pool ratio (index 0 is USDC, index 1 is GREEN in amounts array)
    # But get_balances() might return them differently, so let's calculate correctly
    balances = green_pool.get_balances()
    # Normalize to 18 decimals for comparison
    usdc_normalized = balances[0] * EIGHTEEN_DECIMALS // (10 ** usdc_token.decimals())
    green_normalized = balances[1]
    total = usdc_normalized + green_normalized
    usdc_percentage = (usdc_normalized * 100) // total if total > 0 else 0

    # Verify we have extreme imbalance
    assert usdc_percentage > 80, f"Not extreme enough: {usdc_percentage}% USDC (balances: {balances[0]} USDC, {balances[1]} GREEN)"

    # Calculate initial profit
    initial_profit = endaoment.calcProfitForStabilizer()

    # Run stabilizer on extremely imbalanced pool
    endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)

    # Calculate new profit
    new_profit = endaoment.calcProfitForStabilizer()

    # Even with extreme imbalance and high slippage, profit should not decrease
    assert new_profit >= initial_profit, \
        f"Profit decreased with extreme imbalance! Initial: {initial_profit}, New: {new_profit}, " \
        f"Pool imbalance: {usdc_percentage}% USDC"


###################################
# Pool Debt Integrity Tests       #
###################################


@pytest.base
def test_pool_debt_multiple_operations(
    endaoment,
    deployed_green_pool,
    switchboard_delta,
    usdc_token,
    fork,
    ledger,
    _test,
):
    """Test pool debt tracking across multiple add/remove operations"""
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]

    # Add partner liquidity 3 times
    for i in range(3):
        usdc_amount = 5_000 * (10 ** usdc_token.decimals())
        partner = boa.env.generate_address()

        # Transfer to partner and approve endaoment
        usdc_token.transfer(partner, usdc_amount, sender=usdc_whale)
        usdc_token.approve(endaoment, usdc_amount, sender=partner)

        endaoment.addPartnerLiquidity(10, green_pool, partner, usdc_token, usdc_amount, 0, sender=switchboard_delta.address)

    # Total debt should be ~3 * 5000 GREEN (in 18 decimals)
    total_debt = ledger.greenPoolDebt(green_pool)
    expected_debt = 3 * 5_000 * EIGHTEEN_DECIMALS

    # Allow 1% tolerance for curve pool pricing
    _test(total_debt, expected_debt, 100)  # 1% tolerance

    # Debt should never be negative
    assert total_debt >= 0


@pytest.base
def test_pool_debt_repayment_reduces_debt(
    endaoment,
    deployed_green_pool,
    switchboard_delta,
    green_token,
    usdc_token,
    fork,
    whale,
    ledger,
    _test,
):
    """Test that repaying pool debt correctly reduces the debt"""
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]

    # Create initial debt
    usdc_amount = 10_000 * (10 ** usdc_token.decimals())
    partner = boa.env.generate_address()

    # Transfer to partner and approve endaoment
    usdc_token.transfer(partner, usdc_amount, sender=usdc_whale)
    usdc_token.approve(endaoment, usdc_amount, sender=partner)

    endaoment.addPartnerLiquidity(10, green_pool, partner, usdc_token, usdc_amount, 0, sender=switchboard_delta.address)

    initial_debt = ledger.greenPoolDebt(green_pool)
    assert initial_debt > 0

    # Transfer green to endaoment for repayment
    repay_amount = 5_000 * EIGHTEEN_DECIMALS
    green_token.transfer(endaoment, repay_amount, sender=whale)

    # Repay debt
    endaoment.repayPoolDebt(green_pool, repay_amount, sender=switchboard_delta.address)

    # Debt should have decreased
    new_debt = ledger.greenPoolDebt(green_pool)
    debt_reduction = initial_debt - new_debt

    # Debt reduction should equal repay amount
    _test(debt_reduction, repay_amount)

    # New debt should be initial - repay
    assert new_debt == initial_debt - repay_amount


@pytest.base
def test_pool_debt_cannot_over_repay(
    endaoment,
    endaoment_funds,
    deployed_green_pool,
    switchboard_delta,
    green_token,
    usdc_token,
    fork,
    whale,
    ledger,
    _test,
):
    """Test that repaying more than debt only reduces debt to zero

    repayPoolDebt() pulls green from endaoment_funds, burns only up to the debt amount,
    and returns any leftover green back to endaoment_funds.
    """
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]

    # Create debt
    usdc_amount = 5_000 * (10 ** usdc_token.decimals())
    partner = boa.env.generate_address()

    # Transfer to partner and approve endaoment
    usdc_token.transfer(partner, usdc_amount, sender=usdc_whale)
    usdc_token.approve(endaoment, usdc_amount, sender=partner)

    endaoment.addPartnerLiquidity(10, green_pool, partner, usdc_token, usdc_amount, 0, sender=switchboard_delta.address)

    debt = ledger.greenPoolDebt(green_pool)
    assert debt > 0

    # Try to repay more than debt - transfer to endaoment_funds (where assets are stored)
    excessive_repay = debt * 2
    green_token.transfer(endaoment_funds, excessive_repay, sender=whale)

    initial_green_balance = green_token.balanceOf(endaoment_funds)

    # Repay excessive amount - contract will only burn up to debt amount
    success = endaoment.repayPoolDebt(green_pool, excessive_repay, sender=switchboard_delta.address)

    # Should succeed
    assert success

    # Debt should be zero
    assert ledger.greenPoolDebt(green_pool) == 0

    # Only the actual debt should have been burned, rest should remain in endaoment_funds
    final_green_balance = green_token.balanceOf(endaoment_funds)
    green_burned = initial_green_balance - final_green_balance
    _test(debt, green_burned)


@pytest.base
def test_pool_debt_integrity_during_stabilizer_remove(
    setGreenRefConfig,
    endaoment,
    deployed_green_pool,
    switchboard_delta,
    green_token,
    usdc_token,
    fork,
    whale,
    ledger,
    addSeedGreenLiq,
):
    """Test that debt is properly repaid during green removal"""
    addSeedGreenLiq()
    setGreenRefConfig(_stabilizerAdjustWeight=100_00)
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]

    # Create debt via partner liquidity
    usdc_amount = 10_000 * (10 ** usdc_token.decimals())
    partner = boa.env.generate_address()

    # Transfer to partner and approve endaoment
    usdc_token.transfer(partner, usdc_amount, sender=usdc_whale)
    usdc_token.approve(endaoment, usdc_amount, sender=partner)

    endaoment.addPartnerLiquidity(10, green_pool, partner, usdc_token, usdc_amount, 0, sender=switchboard_delta.address)

    initial_debt = ledger.greenPoolDebt(green_pool)
    assert initial_debt > 0

    # Create imbalance (more green in pool)
    green_add_amount = 50_000 * EIGHTEEN_DECIMALS
    green_token.transfer(endaoment, green_add_amount, sender=whale)
    green_token.approve(green_pool.address, green_add_amount, sender=endaoment.address)

    amounts = [0, green_add_amount]
    green_pool.add_liquidity(amounts, 0, sender=endaoment.address)

    # Run stabilizer to remove green (which should repay debt)
    endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)

    # Debt should have decreased or stayed same (never increase)
    new_debt = ledger.greenPoolDebt(green_pool)
    assert new_debt <= initial_debt


###################################
# State Consistency Tests         #
###################################


@pytest.base
def test_stabilizer_add_then_remove_sequence(
    setGreenRefConfig,
    endaoment,
    deployed_green_pool,
    switchboard_delta,
    green_token,
    usdc_token,
    fork,
    whale,
    ledger,
    addSeedGreenLiq,
):
    """Test stabilizer operation sequence: add → remove

    This test verifies that profit never decreases through a full sequence of stabilizer
    operations: adding green to rebalance, then removing green to rebalance in the opposite
    direction. This tests the cumulative effect of multiple stabilizer actions.
    """
    addSeedGreenLiq()
    setGreenRefConfig(_stabilizerAdjustWeight=100_00)
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]

    # First create pool debt
    usdc_amount = 10_000 * (10 ** usdc_token.decimals())
    partner = boa.env.generate_address()

    # Transfer to partner and approve endaoment
    usdc_token.transfer(partner, usdc_amount, sender=usdc_whale)
    usdc_token.approve(endaoment, usdc_amount, sender=partner)

    endaoment.addPartnerLiquidity(10, green_pool, partner, usdc_token, usdc_amount, 0, sender=switchboard_delta.address)

    # Record initial state
    initial_profit = endaoment.calcProfitForStabilizer()
    initial_debt = ledger.greenPoolDebt(green_pool)

    # Step 1: Create imbalance (more USDC) and add green
    usdc_add_amount = 30_000 * (10 ** usdc_token.decimals())
    usdc_token.transfer(endaoment, usdc_add_amount, sender=usdc_whale)
    usdc_token.approve(green_pool.address, usdc_add_amount, sender=endaoment.address)
    amounts = [usdc_add_amount, 0]
    green_pool.add_liquidity(amounts, 0, sender=endaoment.address)

    endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)

    # Check profit and debt after adding
    after_add_profit = endaoment.calcProfitForStabilizer()
    after_add_debt = ledger.greenPoolDebt(green_pool)

    # Step 2: Create opposite imbalance (more green) and remove
    green_add_amount = 40_000 * EIGHTEEN_DECIMALS
    green_token.transfer(endaoment, green_add_amount, sender=whale)
    green_token.approve(green_pool.address, green_add_amount, sender=endaoment.address)
    amounts2 = [0, green_add_amount]
    green_pool.add_liquidity(amounts2, 0, sender=endaoment.address)

    endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)

    # Check final profit and debt after removing
    final_profit = endaoment.calcProfitForStabilizer()
    final_debt = ledger.greenPoolDebt(green_pool)

    # Verify profit invariants throughout the sequence
    assert after_add_profit >= initial_profit, \
        f"Profit decreased after adding! Initial: {initial_profit}, After add: {after_add_profit}"
    assert final_profit >= after_add_profit, \
        f"Profit decreased after removing! After add: {after_add_profit}, Final: {final_profit}"

    # Verify debt behavior
    assert after_add_debt >= initial_debt, "Adding green should increase debt"
    assert final_debt <= after_add_debt, "Removing green should repay debt"