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
    assert result == False # No adjustment needed


@pytest.base
def test_endao_stabilizer_no_config(
    endaoment,
    switchboard_delta,
):
    # Should return False when no stabilizer config is set
    result = endaoment.stabilizeGreenRefPool(sender=switchboard_delta.address)
    assert result == False


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
    
    # Pool debt should be reduced
    new_pool_debt = ledger.greenPoolDebt(deployed_green_pool)
    assert new_pool_debt < pool_debt


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
    assert result == False


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