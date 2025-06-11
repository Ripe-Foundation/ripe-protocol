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


##################
# Reference Pool #
##################


@pytest.base
def test_reference_pool_basic(
    usdc_token, # load alt price
    deployed_green_pool,
    curve_prices,
    governance,
    addSeedGreenLiq,
):
    addSeedGreenLiq() # need to add liquidity to pool

    # setup
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 0, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock())
    assert curve_prices.confirmGreenRefPoolConfig(aid, sender=governance.address)

    # verify event
    log = filter_logs(curve_prices, "GreenRefPoolConfigUpdated")[0]
    assert log.pool == deployed_green_pool
    assert log.maxNumSnapshots == 10
    assert log.dangerTrigger == 60_00
    assert log.staleBlocks == 0

    # verify config
    config = curve_prices.greenRefPoolConfig()
    assert config.pool == deployed_green_pool
    assert config.greenIndex == 1
    assert config.altAsset == usdc_token.address
    assert config.altAssetDecimals == 6
    assert config.maxNumSnapshots == 10
    assert config.dangerTrigger == 60_00
    assert config.staleBlocks == 0

    # verify data
    data = curve_prices.greenRefPoolData()
    assert data.numBlocksInDanger == 0
    assert data.nextIndex == 1

    lastSnapshot = curve_prices.snapShots(0)
    assert data.lastSnapshot.greenBalance == 10_000 * EIGHTEEN_DECIMALS == lastSnapshot.greenBalance
    assert data.lastSnapshot.ratio == 50_00 == lastSnapshot.ratio
    assert data.lastSnapshot.update == boa.env.evm.patch.block_number == lastSnapshot.update
    assert data.lastSnapshot.inDanger == False == lastSnapshot.inDanger


# configuration tests


@pytest.base
def test_invalid_green_ref_pool_configs(
    deployed_green_pool,
    curve_prices,
    governance,
    addSeedGreenLiq,
):
    addSeedGreenLiq()

    # Test invalid maxNumSnapshots (0)
    with boa.reverts("invalid ref pool config"):
        curve_prices.setGreenRefPoolConfig(deployed_green_pool, 0, 60_00, 0, sender=governance.address)

    # Test invalid maxNumSnapshots (>100)
    with boa.reverts("invalid ref pool config"):
        curve_prices.setGreenRefPoolConfig(deployed_green_pool, 101, 60_00, 0, sender=governance.address)

    # Test invalid dangerTrigger (<50%)
    with boa.reverts("invalid ref pool config"):
        curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 49_99, 0, sender=governance.address)

    # Test invalid dangerTrigger (>100%)
    with boa.reverts("invalid ref pool config"):
        curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 100_01, 0, sender=governance.address)

    # Test valid edge cases
    aid1 = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 1, 50_00, 0, sender=governance.address)
    aid2 = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 100, 100_00, 0, sender=governance.address)
    
    # Should be able to set these
    assert aid1 != 0
    assert aid2 != 0


@pytest.base
def test_green_ref_pool_config_timelock(
    deployed_green_pool,
    curve_prices,
    governance,
    addSeedGreenLiq,
):
    addSeedGreenLiq()

    # Set config
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 0, sender=governance.address)
    
    # Verify pending config event
    log = filter_logs(curve_prices, "GreenRefPoolConfigPending")[0]
    assert log.pool == deployed_green_pool
    assert log.maxNumSnapshots == 10
    assert log.dangerTrigger == 60_00
    assert log.staleBlocks == 0
    assert log.actionId == aid

    # Try to confirm before timelock - should fail
    with boa.reverts("time lock not reached"):
        curve_prices.confirmGreenRefPoolConfig(aid, sender=governance.address)

    # Travel to just before timelock
    boa.env.time_travel(blocks=curve_prices.actionTimeLock() - 1)
    with boa.reverts("time lock not reached"):
        curve_prices.confirmGreenRefPoolConfig(aid, sender=governance.address)

    # Travel to exactly timelock block
    boa.env.time_travel(blocks=1)
    assert curve_prices.confirmGreenRefPoolConfig(aid, sender=governance.address)

    # Verify config is active
    config = curve_prices.greenRefPoolConfig()
    assert config.pool == deployed_green_pool
    assert config.maxNumSnapshots == 10


@pytest.base
def test_green_ref_pool_config_cancellation(
    deployed_green_pool,
    curve_prices,
    governance,
    addSeedGreenLiq,
):
    addSeedGreenLiq()

    # Set config
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 0, sender=governance.address)
    
    # Cancel before timelock
    assert curve_prices.cancelGreenRefPoolConfig(aid, sender=governance.address)
    
    # Verify cancellation event
    log = filter_logs(curve_prices, "GreenRefPoolConfigUpdateCancelled")[0]
    assert log.pool == deployed_green_pool
    assert log.maxNumSnapshots == 10
    assert log.dangerTrigger == 60_00

    # Try to confirm cancelled action - should fail
    boa.env.time_travel(blocks=curve_prices.actionTimeLock())
    with boa.reverts("no pending update"):
        curve_prices.confirmGreenRefPoolConfig(aid, sender=governance.address)


# snapshot tests


@pytest.base
def test_multiple_snapshots_balanced_pool(
    deployed_green_pool,
    curve_prices,
    governance,
    addSeedGreenLiq,
    teller,
):
    addSeedGreenLiq()

    # Setup config
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 5, 60_00, 0, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock())
    assert curve_prices.confirmGreenRefPoolConfig(aid, sender=governance.address)

    # Initial snapshot should be created during config confirmation
    data = curve_prices.greenRefPoolData()
    assert data.nextIndex == 1
    assert data.lastSnapshot.ratio == 50_00
    assert data.lastSnapshot.inDanger == False

    # Add more snapshots in different blocks
    for i in range(4):
        boa.env.time_travel(blocks=1)
        assert curve_prices.addGreenRefPoolSnapshot(sender=teller.address)
        
        data = curve_prices.greenRefPoolData()
        assert data.nextIndex == (i + 2) % 5
        assert data.lastSnapshot.ratio == 50_00
        assert data.lastSnapshot.inDanger == False

    # Verify all snapshots are saved
    for i in range(5):
        snapshot = curve_prices.snapShots(i)
        assert snapshot.greenBalance == 10_000 * EIGHTEEN_DECIMALS
        assert snapshot.ratio == 50_00
        assert snapshot.inDanger == False


@pytest.base
def test_snapshots_with_imbalanced_pool(
    deployed_green_pool,
    curve_prices,
    governance,
    addSeedGreenLiq,
    swapGreenForUsdc,
    teller,
    _test,
):
    addSeedGreenLiq()

    # Setup config with 70% danger trigger
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 70_00, 0, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock())
    assert curve_prices.confirmGreenRefPoolConfig(aid, sender=governance.address)

    # Create imbalance by swapping GREEN for USDC (increases GREEN ratio in pool)
    swap_amount = 5_000 * EIGHTEEN_DECIMALS
    swapGreenForUsdc(swap_amount)

    # Take snapshot
    boa.env.time_travel(blocks=1)
    assert curve_prices.addGreenRefPoolSnapshot(sender=teller.address)

    # Verify snapshot event
    log = filter_logs(curve_prices, "GreenRefPoolSnapshotAdded")[0]
    assert log.pool == deployed_green_pool
    assert log.inDanger == True
    _test(75_00, log.greenRatio)

    # Verify snapshot shows danger
    data = curve_prices.greenRefPoolData()
    _test(75_00, data.lastSnapshot.ratio)
    assert data.lastSnapshot.inDanger == True
    assert data.numBlocksInDanger == 0  # No elapsed blocks yet


@pytest.base
def test_danger_block_counting(
    usdc_token,
    deployed_green_pool,
    curve_prices,
    governance,
    addSeedGreenLiq,
    swapUsdcForGreen,
    swapGreenForUsdc,
    teller,
):
    addSeedGreenLiq()

    # Setup config
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 65_00, 0, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock())
    assert curve_prices.confirmGreenRefPoolConfig(aid, sender=governance.address)

    # Create danger condition by adding GREEN to pool
    swap_amount = 5_000 * EIGHTEEN_DECIMALS
    swapGreenForUsdc(swap_amount)

    # Take first danger snapshot
    boa.env.time_travel(blocks=1)
    assert curve_prices.addGreenRefPoolSnapshot(sender=teller.address)
    data = curve_prices.greenRefPoolData()
    assert data.lastSnapshot.inDanger == True
    assert data.numBlocksInDanger == 0

    # Wait 5 blocks and take another danger snapshot
    boa.env.time_travel(blocks=5)
    assert curve_prices.addGreenRefPoolSnapshot(sender=teller.address)
    data = curve_prices.greenRefPoolData()
    assert data.lastSnapshot.inDanger == True
    assert data.numBlocksInDanger == 5

    # Wait 3 more blocks and take another danger snapshot
    boa.env.time_travel(blocks=3)
    assert curve_prices.addGreenRefPoolSnapshot(sender=teller.address)
    data = curve_prices.greenRefPoolData()
    assert data.lastSnapshot.inDanger == True
    assert data.numBlocksInDanger == 8

    # Rebalance pool to exit danger by removing GREEN from pool
    usdc_swap_amount = 5_000 * (10 ** usdc_token.decimals())
    swapUsdcForGreen(usdc_swap_amount)

    # Take snapshot - should reset danger blocks
    boa.env.time_travel(blocks=2)
    assert curve_prices.addGreenRefPoolSnapshot(sender=teller.address)

    data = curve_prices.greenRefPoolData()
    assert data.lastSnapshot.inDanger == False
    assert data.numBlocksInDanger == 0


@pytest.base
def test_snapshot_index_wrapping(
    deployed_green_pool,
    curve_prices,
    governance,
    addSeedGreenLiq,
    teller,
):
    addSeedGreenLiq()

    # Setup config with only 3 max snapshots
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 3, 60_00, 0, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock())
    assert curve_prices.confirmGreenRefPoolConfig(aid, sender=governance.address)

    # Initial index should be 1 after config confirmation
    data = curve_prices.greenRefPoolData()
    assert data.nextIndex == 1

    # Add snapshots until we wrap around
    for i in range(5):
        boa.env.time_travel(blocks=1)
        assert curve_prices.addGreenRefPoolSnapshot(sender=teller.address)
        
        data = curve_prices.greenRefPoolData()
        expected_index = (i + 2) % 3
        assert data.nextIndex == expected_index

    # Verify only the last 3 snapshots are kept
    # Indexes 0, 1, 2 should all have data, but older ones overwritten
    for i in range(3):
        snapshot = curve_prices.snapShots(i)
        assert snapshot.greenBalance > 0
        assert snapshot.ratio > 0


@pytest.base
def test_same_block_snapshot_prevention(
    teller,
    deployed_green_pool,
    curve_prices,
    governance,
    addSeedGreenLiq,
):
    addSeedGreenLiq()

    # Setup config
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 0, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock())
    assert curve_prices.confirmGreenRefPoolConfig(aid, sender=governance.address)

    # Try to add another snapshot in the same block - should return False
    result = curve_prices.addGreenRefPoolSnapshot(sender=teller.address)
    assert result == False

    # Move to next block - should work
    boa.env.time_travel(blocks=1)
    result = curve_prices.addGreenRefPoolSnapshot(sender=teller.address)
    assert result == True


# weighted ratio tests


@pytest.base
def test_weighted_ratio_calculation(
    teller,
    deployed_green_pool,
    curve_prices,
    governance,
    addSeedGreenLiq,
    swapGreenForUsdc,
):
    addSeedGreenLiq()

    # Setup config
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 0, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock())
    assert curve_prices.confirmGreenRefPoolConfig(aid, sender=governance.address)

    # Get initial status
    status = curve_prices.getCurrentGreenPoolStatus()
    assert status.weightedRatio == 50_00
    assert status.dangerTrigger == 60_00
    assert status.numBlocksInDanger == 0

    # Create different balance scenarios by adding GREEN to pool
    # Small swap - should increase GREEN ratio slightly
    small_swap = 1_000 * EIGHTEEN_DECIMALS
    swapGreenForUsdc(small_swap)
    
    boa.env.time_travel(blocks=1)
    assert curve_prices.addGreenRefPoolSnapshot(sender=teller.address)

    # Large swap - should increase GREEN ratio more
    large_swap = 2_000 * EIGHTEEN_DECIMALS
    swapGreenForUsdc(large_swap)
    
    boa.env.time_travel(blocks=1)
    assert curve_prices.addGreenRefPoolSnapshot(sender=teller.address)

    # Get weighted ratio
    status = curve_prices.getCurrentGreenPoolStatus()
    
    # Should be weighted average based on green balances
    # The snapshot with more green tokens should have more weight
    assert status.weightedRatio > 50_00
    assert status.weightedRatio < 70_00  # Should be somewhere in between


@pytest.base
def test_stale_snapshots_excluded(
    teller,
    deployed_green_pool,
    curve_prices,
    governance,
    addSeedGreenLiq,
    swapGreenForUsdc,
):
    addSeedGreenLiq()

    # Setup config with stale blocks = 10
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 10, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock())
    assert curve_prices.confirmGreenRefPoolConfig(aid, sender=governance.address)

    # Initial balanced snapshot at block X
    initial_status = curve_prices.getCurrentGreenPoolStatus()
    assert initial_status.weightedRatio == 50_00

    # Create imbalance by adding GREEN to pool
    swap_amount = 2_000 * EIGHTEEN_DECIMALS
    swapGreenForUsdc(swap_amount)
    boa.env.time_travel(blocks=1)
    assert curve_prices.addGreenRefPoolSnapshot(sender=teller.address)

    # Should include both snapshots
    status = curve_prices.getCurrentGreenPoolStatus()
    imbalanced_ratio = status.weightedRatio
    assert imbalanced_ratio > 50_00

    # Travel 11 blocks (making first snapshot stale)
    boa.env.time_travel(blocks=11)
    
    # Should only use recent snapshot now (first snapshot is stale)
    status = curve_prices.getCurrentGreenPoolStatus()
    data = curve_prices.greenRefPoolData()

    # With first snapshot stale, weighted ratio should equal the last snapshot ratio
    assert status.weightedRatio == data.lastSnapshot.ratio


# edge cases and permissions


@pytest.base
def test_permission_checks(
    deployed_green_pool,
    curve_prices,
    governance,
    addSeedGreenLiq,
    bob,
):
    addSeedGreenLiq()

    # Test non-governance cannot set config
    with boa.reverts("no perms"):
        curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 0, sender=bob)

    # Setup valid config first
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 0, sender=governance.address)
    
    # Test non-governance cannot confirm
    boa.env.time_travel(blocks=curve_prices.actionTimeLock())
    with boa.reverts("no perms"):
        curve_prices.confirmGreenRefPoolConfig(aid, sender=bob)

    # Test non-governance cannot cancel
    with boa.reverts("no perms"):
        curve_prices.cancelGreenRefPoolConfig(aid, sender=bob)

    # Governance should work
    assert curve_prices.confirmGreenRefPoolConfig(aid, sender=governance.address)

    # For addGreenRefPoolSnapshot, test that only valid ripe addresses can call
    # (The contract checks addys._isValidRipeAddr(msg.sender))
    with boa.reverts("no perms"):
        curve_prices.addGreenRefPoolSnapshot(sender=bob)


@pytest.base
def test_no_config_scenarios(
    curve_prices,
):
    # Test getCurrentGreenPoolStatus with no config
    status = curve_prices.getCurrentGreenPoolStatus()
    assert status.weightedRatio == 0
    assert status.dangerTrigger == 0
    assert status.numBlocksInDanger == 0

    # Test getCurvePoolData with no config - should fail gracefully
    # Since there's no pool address configured, calling pool functions should revert
    with boa.reverts():
        curve_prices.getCurvePoolData()


@pytest.base
def test_empty_pool_scenarios(
    deployed_green_pool,
    curve_prices,
    governance,
):
    # Try to setup config on empty pool (no liquidity)
    # This should actually succeed because empty pools return 50% ratio by default
    # The contract considers this valid since ratio != 0
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 0, sender=governance.address)
    assert aid != 0
    
    # Should be able to confirm it too
    boa.env.time_travel(blocks=curve_prices.actionTimeLock())
    assert curve_prices.confirmGreenRefPoolConfig(aid, sender=governance.address)
    
    # Verify the empty pool data
    green_balance, ratio = curve_prices.getCurvePoolData()
    assert green_balance == 0  # No GREEN tokens
    assert ratio == 50_00  # Default ratio for empty pools


@pytest.base
def test_maximum_snapshots_config(
    teller,
    deployed_green_pool,
    curve_prices,
    governance,
    addSeedGreenLiq,
):
    addSeedGreenLiq()

    # Test that maximum allowed maxNumSnapshots (100) can be configured and used
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 100, 60_00, 0, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock())
    assert curve_prices.confirmGreenRefPoolConfig(aid, sender=governance.address)

    # Verify config was set with maximum value
    config = curve_prices.greenRefPoolConfig()
    assert config.maxNumSnapshots == 100

    # Verify system works with maximum config
    data = curve_prices.greenRefPoolData()
    assert data.nextIndex == 1

    # Add several snapshots to verify functionality
    for i in range(5):
        boa.env.time_travel(blocks=1)
        assert curve_prices.addGreenRefPoolSnapshot(sender=teller.address)
        
        data = curve_prices.greenRefPoolData()
        expected_index = (i + 2) % 100  # Should wrap at 100, not smaller values
        assert data.nextIndex == expected_index

    # Verify snapshots are properly stored
    for i in range(6):  # Initial + 5 added
        snapshot = curve_prices.snapShots(i)
        assert snapshot.greenBalance == 10_000 * EIGHTEEN_DECIMALS
        assert snapshot.ratio == 50_00
        assert snapshot.update > 0


@pytest.base
def test_curve_pool_data_accuracy(
    deployed_green_pool,
    curve_prices,
    governance,
    addSeedGreenLiq,
    swapGreenForUsdc,
):
    addSeedGreenLiq()

    # Setup config to enable getCurvePoolData
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 0, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock())
    assert curve_prices.confirmGreenRefPoolConfig(aid, sender=governance.address)

    # Test balanced pool
    green_balance, ratio = curve_prices.getCurvePoolData()
    assert green_balance == 10_000 * EIGHTEEN_DECIMALS
    assert ratio == 50_00

    # Create imbalance by adding GREEN to pool
    swap_amount = 2_000 * EIGHTEEN_DECIMALS
    swapGreenForUsdc(swap_amount)

    # Test imbalanced pool
    new_green_balance, new_ratio = curve_prices.getCurvePoolData()
    assert new_green_balance > green_balance  # More green tokens
    assert new_ratio > 50_00  # Higher green ratio

    # Verify the pool actually has these balances
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    actual_green_balance = green_pool.balances(1)  # Green is index 1
    assert new_green_balance == actual_green_balance


@pytest.base
def test_config_update_overwrites_data(
    teller,
    deployed_green_pool,
    curve_prices,
    governance,
    addSeedGreenLiq,
):
    addSeedGreenLiq()

    # Setup initial config
    aid1 = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 5, 60_00, 0, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock())
    assert curve_prices.confirmGreenRefPoolConfig(aid1, sender=governance.address)

    # Add some snapshots
    for i in range(3):
        boa.env.time_travel(blocks=1)
        assert curve_prices.addGreenRefPoolSnapshot(sender=teller.address)

    # Check state before config update
    data = curve_prices.greenRefPoolData()
    assert data.nextIndex == 4  # Should be 4 after adding 3 snapshots (started at 1)

    # Update config with different parameters
    aid2 = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 8, 70_00, 5, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock())
    assert curve_prices.confirmGreenRefPoolConfig(aid2, sender=governance.address)

    # Verify config updated
    config = curve_prices.greenRefPoolConfig()
    assert config.maxNumSnapshots == 8
    assert config.dangerTrigger == 70_00
    assert config.staleBlocks == 5

    # Verify new snapshot was added during confirmation and nextIndex continues
    data = curve_prices.greenRefPoolData()
    assert data.nextIndex == 5  # Should be 5 (snapshot added at index 4, then incremented)


@pytest.base
def test_green_token_index_detection(
    deployed_green_pool,
    curve_prices,
    governance,
    addSeedGreenLiq,
    usdc_token,
):
    addSeedGreenLiq()
    
    # Test current setup (GREEN at index 1)
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 0, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock())
    assert curve_prices.confirmGreenRefPoolConfig(aid, sender=governance.address)
    
    config = curve_prices.greenRefPoolConfig()
    assert config.greenIndex == 1  # GREEN should be at index 1
    assert config.altAsset == usdc_token.address


@pytest.base 
def test_invalid_pool_no_green_token(
    curve_prices,
    governance,
    usdc_token,
    fork,
    deploy3r,
):
    # Create a pool without GREEN token (USDC/WETH for example)
    factory = boa.from_etherscan(ADDYS[fork]["CURVE_STABLE_FACTORY"])
    weth = boa.from_etherscan(CORE_TOKENS[fork]["WETH"], name="weth")
    
    implementation_idx = 0
    no_green_pool = factory.deploy_plain_pool(
        "USDC/WETH Pool",
        "USDC/WETH", 
        [usdc_token, weth],
        100,
        4000000,
        20000000000,
        600,
        implementation_idx,
        [0, 0],
        [b"", b""],
        [ZERO_ADDRESS, ZERO_ADDRESS],
        sender=deploy3r,
    )
    
    # Should fail because GREEN token not in pool
    with boa.reverts("invalid ref pool config"):
        curve_prices.setGreenRefPoolConfig(no_green_pool, 10, 60_00, 0, sender=governance.address)


@pytest.base
def test_decimal_handling_edge_cases(
    deployed_green_pool,
    curve_prices,
    governance,
    addSeedGreenLiq,
):
    addSeedGreenLiq()
    
    # Test with current setup (USDC = 6 decimals)
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 0, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock())
    assert curve_prices.confirmGreenRefPoolConfig(aid, sender=governance.address)
    
    config = curve_prices.greenRefPoolConfig()
    assert config.altAssetDecimals == 6
    
    # Verify normalization works correctly
    green_balance, ratio = curve_prices.getCurvePoolData()
    assert green_balance > 0
    assert ratio == 50_00


@pytest.base
def test_weighted_ratio_edge_cases(
    deployed_green_pool,
    curve_prices,
    governance,
    addSeedGreenLiq,
    swapGreenForUsdc,
    teller,
):
    addSeedGreenLiq()
    
    # Setup config with stale blocks = 3
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 3, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock())
    initial_block = boa.env.evm.patch.block_number
    assert curve_prices.confirmGreenRefPoolConfig(aid, sender=governance.address)
    
    # Initial snapshot created during config confirmation - should be balanced (50%)
    data = curve_prices.greenRefPoolData()
    initial_ratio = data.lastSnapshot.ratio
    assert initial_ratio == 50_00
    
    # Add an imbalanced snapshot
    swap_amount = 1_000 * EIGHTEEN_DECIMALS
    swapGreenForUsdc(swap_amount)
    boa.env.time_travel(blocks=1)
    assert curve_prices.addGreenRefPoolSnapshot(sender=teller.address)
    
    # Get the imbalanced snapshot data
    data = curve_prices.greenRefPoolData()
    imbalanced_ratio = data.lastSnapshot.ratio
    assert imbalanced_ratio > 50_00  # Should be higher due to imbalance
    
    # Check weighted ratio with both snapshots valid
    status = curve_prices.getCurrentGreenPoolStatus()
    weighted_ratio_before_stale = status.weightedRatio
    # Should be between the initial (50%) and imbalanced ratios
    assert initial_ratio < weighted_ratio_before_stale < imbalanced_ratio
    
    # Travel past stale threshold to make all snapshots stale
    # Snapshots become stale when: block.number > snapshot.update + staleBlocks
    boa.env.time_travel(blocks=5)
    
    # Test fallback to lastSnapshot.ratio when no valid snapshots
    status = curve_prices.getCurrentGreenPoolStatus()
    data = curve_prices.greenRefPoolData()
    
    # Should fall back to lastSnapshot.ratio since all snapshots are stale
    assert status.weightedRatio == data.lastSnapshot.ratio
    # The lastSnapshot should be the imbalanced one (most recent)
    assert data.lastSnapshot.ratio == imbalanced_ratio
    assert status.weightedRatio == imbalanced_ratio


@pytest.base
def test_stale_blocks_exact_threshold(
    deployed_green_pool,
    curve_prices,
    governance,
    addSeedGreenLiq,
    swapGreenForUsdc,
    teller,
):
    addSeedGreenLiq()
    
    # Setup config with stale blocks = 3 (shorter for clearer testing)
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 3, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock())
    assert curve_prices.confirmGreenRefPoolConfig(aid, sender=governance.address)
    
    # Record the initial snapshot block (created during config confirmation)
    data = curve_prices.greenRefPoolData()
    initial_snapshot_block = data.lastSnapshot.update
    
    # Add imbalanced snapshot 1 block later
    swap_amount = 2_000 * EIGHTEEN_DECIMALS
    swapGreenForUsdc(swap_amount)
    boa.env.time_travel(blocks=1)
    test_snapshot_block = boa.env.evm.patch.block_number
    assert curve_prices.addGreenRefPoolSnapshot(sender=teller.address)
    
    # Get the test snapshot data
    data = curve_prices.greenRefPoolData()
    test_snapshot_ratio = data.lastSnapshot.ratio
    
    # Travel to exactly the stale threshold for our test snapshot
    # Snapshot becomes stale when: block.number > snapshot.update + staleBlocks
    # So at snapshot.update + staleBlocks, it should still be valid
    blocks_to_travel = test_snapshot_block + 3 - boa.env.evm.patch.block_number
    boa.env.time_travel(blocks=blocks_to_travel)
    
    # At exactly threshold, test snapshot should still be valid
    current_block = boa.env.evm.patch.block_number
    assert current_block == test_snapshot_block + 3  # Verify we're at the threshold
    
    status = curve_prices.getCurrentGreenPoolStatus()
    # Should use lastSnapshot since initial snapshot is now stale, but test snapshot is still valid
    assert status.weightedRatio == test_snapshot_ratio
    
    # Travel 1 more block (beyond threshold)
    boa.env.time_travel(blocks=1)
    final_block = boa.env.evm.patch.block_number
    assert final_block > test_snapshot_block + 3  # Beyond threshold
    
    # Now both snapshots should be stale - should fall back to lastSnapshot
    status = curve_prices.getCurrentGreenPoolStatus()
    data = curve_prices.greenRefPoolData()
    assert status.weightedRatio == data.lastSnapshot.ratio


@pytest.base
def test_contract_pause_blocks_functions(
    deployed_green_pool,
    curve_prices,
    governance,
    addSeedGreenLiq,
    teller,
    switchboard_alpha,
):
    addSeedGreenLiq()
    
    # Setup config first
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 0, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock())
    assert curve_prices.confirmGreenRefPoolConfig(aid, sender=governance.address)
    
    # Pause the contract
    curve_prices.pause(True, sender=switchboard_alpha.address)
    
    # All functions should be blocked when paused
    with boa.reverts("contract paused"):
        curve_prices.setGreenRefPoolConfig(deployed_green_pool, 5, 70_00, 0, sender=governance.address)
    
    with boa.reverts("contract paused"):
        curve_prices.confirmGreenRefPoolConfig(123, sender=governance.address)
        
    with boa.reverts("contract paused"):
        curve_prices.cancelGreenRefPoolConfig(123, sender=governance.address)
        
    with boa.reverts("contract paused"):
        curve_prices.addGreenRefPoolSnapshot(sender=teller.address)
    
    # View functions should still work when paused
    status = curve_prices.getCurrentGreenPoolStatus()
    assert status.weightedRatio > 0
    
    balance, ratio = curve_prices.getCurvePoolData()
    assert balance > 0


@pytest.base
def test_snapshot_with_zero_balance_edge_case(
    deployed_green_pool,
    curve_prices,
    governance,
    green_token,
    usdc_token,
    bob,
    whale,
    fork,
):
    # Create a scenario where the pool might have zero GREEN balance
    # This is hard to achieve with normal swaps, so we'll test the validation
    
    # Add initial liquidity
    green_pool = boa.env.lookup_contract(deployed_green_pool)
    
    # Add only USDC to pool (if possible) or test validation logic
    usdc_amount = 1000 * (10 ** usdc_token.decimals())
    usdc_token.transfer(bob, usdc_amount, sender=WHALES[fork]["usdc"])
    usdc_token.approve(green_pool, usdc_amount, sender=bob)
    
    # Add minimal GREEN
    green_amount = 1 * EIGHTEEN_DECIMALS
    green_token.transfer(bob, green_amount, sender=whale)
    green_token.approve(green_pool, green_amount, sender=bob)
    
    green_pool.add_liquidity([usdc_amount, green_amount], 0, bob, sender=bob)
    
    # Setup config
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 0, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock())
    assert curve_prices.confirmGreenRefPoolConfig(aid, sender=governance.address)
    
    # The snapshot should be created successfully even with very low GREEN balance
    data = curve_prices.greenRefPoolData()
    assert data.lastSnapshot.greenBalance > 0
    assert data.lastSnapshot.ratio < 50_00  # Should be much less than 50%



@pytest.base
def test_invalid_action_id_scenarios(
    curve_prices,
    governance,
    addSeedGreenLiq,
):
    addSeedGreenLiq()
    
    # Try to confirm non-existent action ID
    with boa.reverts("no pending update"):
        curve_prices.confirmGreenRefPoolConfig(99999, sender=governance.address)
    
    # Try to cancel non-existent action ID  
    with boa.reverts("no pending update"):
        curve_prices.cancelGreenRefPoolConfig(99999, sender=governance.address)


@pytest.base
def test_danger_transition_edge_cases(
    deployed_green_pool,
    curve_prices,
    governance,
    addSeedGreenLiq,
    swapGreenForUsdc,
    swapUsdcForGreen,
    usdc_token,
    teller,
):
    addSeedGreenLiq()
    
    # Setup config with 60% danger trigger
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 0, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock())
    assert curve_prices.confirmGreenRefPoolConfig(aid, sender=governance.address)
    
    # Create danger condition - need enough to exceed 60%
    swap_amount = 2_500 * EIGHTEEN_DECIMALS
    swapGreenForUsdc(swap_amount)
    
    boa.env.time_travel(blocks=1)
    assert curve_prices.addGreenRefPoolSnapshot(sender=teller.address)
    
    data = curve_prices.greenRefPoolData()
    assert data.lastSnapshot.inDanger == True
    assert data.numBlocksInDanger == 0
    
    # Exit danger immediately (within same block would be prevented)
    boa.env.time_travel(blocks=1)
    usdc_swap_amount = 2_000 * (10 ** usdc_token.decimals())
    swapUsdcForGreen(usdc_swap_amount)
    
    assert curve_prices.addGreenRefPoolSnapshot(sender=teller.address)
    
    data = curve_prices.greenRefPoolData()
    assert data.lastSnapshot.inDanger == False
    assert data.numBlocksInDanger == 0  # Should reset to 0
