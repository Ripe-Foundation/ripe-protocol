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
    assert green_pool.balanceOf(endaoment) == log.lpReceived


@pytest.base
def test_endao_stabilizer_remove_green(
    setGreenRefConfig,
    endaoment,
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

    # move seed lp into endaoment
    green_pool.transfer(endaoment, green_pool.balanceOf(bob), sender=bob)
    pre_lp = green_pool.balanceOf(endaoment)

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
    assert green_pool.balanceOf(endaoment) == pre_lp - log.lpBurned
    assert green_token.balanceOf(endaoment) == log.greenAmountRemoved


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
    # First rebalance pool and give endaoment LP tokens
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    green_pool.transfer(endaoment, green_pool.balanceOf(bob), sender=bob)
    
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
    
    # Give endaoment extra green for repayment
    extra_green = 5_000 * EIGHTEEN_DECIMALS  # Enough to cover any repayment
    green_token.transfer(endaoment, extra_green, sender=whale)
    green_balance_before = green_token.balanceOf(endaoment)
    
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
    green_balance_after = green_token.balanceOf(endaoment)
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
    assert alpha_token.balanceOf(endaoment) == amount
    assert green_token.balanceOf(endaoment) == green_minted
    assert alpha_token.balanceOf(partner) == pre_bal - amount


def test_endao_mint_partner_liquidity_max_amount(
    endaoment,
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
    assert alpha_token.balanceOf(endaoment) == partner_balance
    assert green_token.balanceOf(endaoment) == green_minted
    assert alpha_token.balanceOf(partner) == 0  # All transferred


def test_endao_mint_partner_liquidity_different_decimals(
    endaoment,
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
    assert charlie_token.balanceOf(endaoment) == amount
    assert green_token.balanceOf(endaoment) == green_minted
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
    deployed_green_pool,
    switchboard_delta,
    green_token,
    _test,
    fork,
    alice,
    usdc_token,
    mock_undy_v2,
    ledger,
):
    green_pool = boa.env.lookup_contract(deployed_green_pool)

    # usdc
    usdc_whale = WHALES[fork]["usdc"]
    usdc_amount = 10_000 * (10 ** usdc_token.decimals())
    usdc_token.transfer(alice, usdc_amount, sender=usdc_whale)
    usdc_token.approve(green_pool, usdc_amount, sender=alice)

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
    _test(log.lpBalance // 2, green_pool.balanceOf(endaoment))

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
    endaoment,
    deployed_green_pool,
    switchboard_delta,
    alice,
    usdc_token,
    fork,
    _test,
):
    # Test that LP tokens are properly shared between partner and endaoment
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]
    amount = 2_000 * (10 ** usdc_token.decimals())
    
    # Record initial LP balances
    initial_partner_lp = green_pool.balanceOf(alice)
    initial_endaoment_lp = green_pool.balanceOf(endaoment)
    
    # Give partner tokens
    usdc_token.transfer(alice, amount, sender=usdc_whale)
    usdc_token.approve(endaoment, amount, sender=alice)
    
    # Add partner liquidity
    liquidityAdded, liqAmountA, liqAmountB = endaoment.addPartnerLiquidity(10, green_pool, alice, usdc_token, amount, 0, sender=switchboard_delta.address)
    
    # Check LP tokens were shared 50/50
    log = filter_logs(endaoment, "PartnerLiquidityAdded")[0]
    total_lp_received = log.lpBalance
    
    partner_lp_received = green_pool.balanceOf(alice) - initial_partner_lp
    endaoment_lp_received = green_pool.balanceOf(endaoment) - initial_endaoment_lp
    
    # Each should get half of the LP tokens
    _test(partner_lp_received, total_lp_received // 2)
    _test(endaoment_lp_received, total_lp_received // 2)
    
    # Total should add up (accounting for potential rounding)
    assert partner_lp_received + endaoment_lp_received >= total_lp_received - 1
    assert partner_lp_received + endaoment_lp_received <= total_lp_received


@pytest.base
def test_endao_add_partner_liquidity_multiple_partners(
    endaoment,
    deployed_green_pool,
    switchboard_delta,
    green_token,
    alice,
    bob,
    usdc_token,
    fork,
    ledger,
    _test,
):
    # Test multiple partners adding liquidity sequentially
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


# TEMPORARILY COMMENTING THIS OUT UNTIL WE GET RID OF MOCK_UNDY_V2


# @pytest.base
# def test_endao_add_partner_liquidity_invalid_lego_id(
#     endaoment,
#     deployed_green_pool,
#     switchboard_delta,
#     alice,
#     usdc_token,
#     fork,
# ):
#     # Test addPartnerLiquidity with invalid lego ID
#     green_pool = boa.env.lookup_contract(deployed_green_pool)
#     usdc_whale = WHALES[fork]["usdc"]
#     amount = 1_000 * (10 ** usdc_token.decimals())
    
#     # Give partner tokens
#     usdc_token.transfer(alice, amount, sender=usdc_whale)
#     usdc_token.approve(endaoment, amount, sender=alice)
    
#     # Use invalid lego ID (999)
#     with boa.reverts("invalid lego"):
#         endaoment.addPartnerLiquidity(999, green_pool, alice, usdc_token, amount, 0, sender=switchboard_delta.address)


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
    pre_green_balance = green_token.balanceOf(endaoment)
    
    # Mint partner liquidity with endaoment as partner
    green_minted = endaoment.mintPartnerLiquidity(endaoment, usdc_token, amount, sender=switchboard_delta.address)
    
    # Check event was emitted
    log = filter_logs(endaoment, "PartnerLiquidityMinted")[0]
    assert log.partner == endaoment.address
    assert log.asset == usdc_token.address
    _test(log.partnerAmount, amount)
    _test(log.greenMinted, green_minted)
    _test(green_minted, amount * EIGHTEEN_DECIMALS // (10 ** usdc_token.decimals()))
    
    # Check balances - USDC stays in endaoment, green is minted
    assert usdc_token.balanceOf(endaoment) == pre_usdc_balance  # No transfer needed
    assert green_token.balanceOf(endaoment) == pre_green_balance + green_minted


@pytest.base
def test_endao_mint_partner_liquidity_self_max_amount(
    endaoment,
    switchboard_delta,
    usdc_token,
    green_token,
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
    endaoment,
    deployed_green_pool,
    switchboard_delta,
    green_token,
    usdc_token,
    fork,
    ledger,
    _test,
):
    # Test addPartnerLiquidity where partner is Endaoment itself
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]
    amount = 1_000 * (10 ** usdc_token.decimals())

    # Transfer funds into Endaoment before calling it
    usdc_token.transfer(endaoment, amount, sender=usdc_whale)
    
    pre_endaoment_lp = green_pool.balanceOf(endaoment)
    
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
    
    # Check balances - all assets should be consumed, all LP should go to endaoment
    assert usdc_token.balanceOf(endaoment) == 0
    assert green_token.balanceOf(endaoment) == 0
    
    # Endaoment should get ALL the LP tokens (not split)
    total_lp_received = green_pool.balanceOf(endaoment) - pre_endaoment_lp
    _test(total_lp_received, liquidityAdded)
    
    # Check pool debt was added
    _test(ledger.greenPoolDebt(green_pool), 1_000 * EIGHTEEN_DECIMALS)


@pytest.base
def test_endao_add_partner_liquidity_self_max_amount(
    endaoment,
    deployed_green_pool,
    switchboard_delta,
    green_token,
    usdc_token,
    fork,
    ledger,
    _test,
):
    # Test addPartnerLiquidity with max amount where partner is Endaoment itself
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]
    amount = 3_000 * (10 ** usdc_token.decimals())

    # Transfer funds into Endaoment
    usdc_token.transfer(endaoment, amount, sender=usdc_whale)
    endaoment_balance = usdc_token.balanceOf(endaoment)
    
    pre_endaoment_lp = green_pool.balanceOf(endaoment)
    
    # Add partner liquidity with max amount
    liquidityAdded, liqAmountA, liqAmountB = endaoment.addPartnerLiquidity(
        10, green_pool, endaoment, usdc_token, sender=switchboard_delta.address
    )
    
    # Check event
    log = filter_logs(endaoment, "PartnerLiquidityAdded")[0]
    _test(log.partnerAmount, endaoment_balance)
    _test(log.greenAmount, 3_000 * EIGHTEEN_DECIMALS)
    
    # All LP tokens should go to endaoment
    total_lp_received = green_pool.balanceOf(endaoment) - pre_endaoment_lp
    _test(total_lp_received, liquidityAdded)
    
    # Check pool debt
    _test(ledger.greenPoolDebt(green_pool), 3_000 * EIGHTEEN_DECIMALS)


@pytest.base
def test_endao_add_partner_liquidity_self_with_existing_green(
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
    # Test addPartnerLiquidity where Endaoment already has green tokens
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    usdc_whale = WHALES[fork]["usdc"]
    usdc_amount = 1_000 * (10 ** usdc_token.decimals())
    green_amount = 500 * EIGHTEEN_DECIMALS

    # Transfer both USDC and existing Green into Endaoment
    usdc_token.transfer(endaoment, usdc_amount, sender=usdc_whale)
    green_token.transfer(endaoment, green_amount, sender=whale)
    
    pre_endaoment_lp = green_pool.balanceOf(endaoment)
    
    # Add partner liquidity with endaoment as partner
    liquidityAdded, liqAmountA, liqAmountB = endaoment.addPartnerLiquidity(
        10, green_pool, endaoment, usdc_token, usdc_amount, 0, sender=switchboard_delta.address
    )
    
    # Check event
    log = filter_logs(endaoment, "PartnerLiquidityAdded")[0]
    _test(log.partnerAmount, usdc_amount)
    _test(log.greenAmount, 1_000 * EIGHTEEN_DECIMALS)  # Full amount minted
    
    # Check balances
    assert usdc_token.balanceOf(endaoment) == 0
    assert green_token.balanceOf(endaoment) == 0  # Both existing and new green used
    
    # All LP tokens should go to endaoment
    total_lp_received = green_pool.balanceOf(endaoment) - pre_endaoment_lp
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