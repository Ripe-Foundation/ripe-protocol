import pytest
import boa

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS
from config.BluePrint import CORE_TOKENS, CURVE_PARAMS, ADDYS, WHALES
from conf_utils import filter_logs
from utils.clock_profiles import clock_profile


# Module-scoped: every contract below is deployed by this fixture and none is
# registered in RipeHq or any shared registry, so building the set per test only
# re-paid the deployments. Titanoboa anchors every test call, so storage a test
# writes into them -- including the direct curve.eval() writes in the snapshot
# overflow tests -- still reverts before the next test runs.
#
# These objects are shared across the module. Boa reverts their EVM storage but
# not their Python-side state, so do not read filter_logs, get_logs or
# _computation from them.
@pytest.fixture(scope="module")
def local_curve_ref_system(governance, bob, sally, alice):
    green = boa.load(
        "contracts/mock/MockErc20.vy",
        governance.address,
        "GREEN",
        "GREEN",
        18,
        1,
    )
    alt = boa.load(
        "contracts/mock/MockErc20.vy",
        governance.address,
        "ALT",
        "ALT",
        18,
        1,
    )
    pool = boa.load("contracts/mock/MockCurveRefPool.vy")
    registry = boa.load(
        "contracts/mock/MockCurveRefPoolRegistry.vy",
        governance.address,
        green,
        sally,
        alice,
    )
    registry.setPool(pool, alt, green)
    registry.setValidRipeAddr(bob, True)
    curve = boa.load(
        "contracts/priceSources/CurvePrices.vy",
        registry,
        ZERO_ADDRESS,
        registry,
        green,
        sally,
        1,
        100,
    )
    assert curve.setActionTimeLockAfterSetup(sender=governance.address)
    pool.setBalances(10_000 * EIGHTEEN_DECIMALS, 10_000 * EIGHTEEN_DECIMALS)
    return curve, pool, registry, governance.address, bob


def _confirm_local_ref_config(
    curve,
    pool,
    governance,
    *,
    capacity=10,
    trigger=60_00,
    stale_blocks=0,
):
    aid = curve.setGreenRefPoolConfig(
        pool,
        capacity,
        trigger,
        stale_blocks,
        10_00,
        100_000 * EIGHTEEN_DECIMALS,
        sender=governance,
    )
    boa.env.time_travel(blocks=curve.actionTimeLock())
    assert curve.confirmGreenRefPoolConfig(aid, sender=governance)
    return aid


def _set_local_green_ratio(pool, green_percent):
    pool.setBalances(
        (100 - green_percent) * EIGHTEEN_DECIMALS,
        green_percent * EIGHTEEN_DECIMALS,
    )


def _establish_local_rolling_danger(
    curve,
    pool,
    governance,
    snapshotter,
    *,
    stale_blocks,
):
    _confirm_local_ref_config(
        curve,
        pool,
        governance,
        capacity=2,
        trigger=60_00,
        stale_blocks=stale_blocks,
    )
    _set_local_green_ratio(pool, 80)
    boa.env.time_travel(blocks=1)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    boa.env.time_travel(blocks=1)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    boa.env.time_travel(blocks=2)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    assert curve.greenRefPoolData().numBlocksInDanger == 2


@pytest.fixture(scope="module")
def usdc_token(fork, chainlink, governance):
    usdc = boa.from_etherscan(CORE_TOKENS[fork]["USDC"], name="usdc")
    if not chainlink.hasPriceFeed(usdc):
        # Use staleTime=0 for forked tests since historical Chainlink data may be stale
        assert chainlink.addNewPriceFeed(usdc, "0x7e860098F58bBFC8648a4311b374B1D669a2bc6B", 0, False, False, sender=governance.address)
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
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 0, 10_00, 100_000 * EIGHTEEN_DECIMALS, sender=governance.address)
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
    assert config.stabilizerAdjustWeight == 10_00
    assert config.stabilizerMaxPoolDebt == 100_000 * EIGHTEEN_DECIMALS

    # verify data
    data = curve_prices.greenRefPoolData()
    assert data.numBlocksInDanger == 0
    assert data.nextIndex == 1

    lastSnapshot = curve_prices.snapShots(0)
    assert data.lastSnapshot.greenBalance == 10_000 * EIGHTEEN_DECIMALS == lastSnapshot.greenBalance
    assert data.lastSnapshot.ratio == 50_00 == lastSnapshot.ratio
    assert data.lastSnapshot.update == boa.env.evm.patch.block_number == lastSnapshot.update
    assert data.lastSnapshot.inDanger is False == lastSnapshot.inDanger


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
        curve_prices.setGreenRefPoolConfig(deployed_green_pool, 0, 60_00, 0, 10_00, 100_000 * EIGHTEEN_DECIMALS, sender=governance.address)

    # Test invalid maxNumSnapshots (>100)
    with boa.reverts("invalid ref pool config"):
        curve_prices.setGreenRefPoolConfig(deployed_green_pool, 101, 60_00, 0, 10_00, 100_000 * EIGHTEEN_DECIMALS, sender=governance.address)

    # Test invalid dangerTrigger (<50%)
    with boa.reverts("invalid ref pool config"):
        curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 49_99, 0, 10_00, 100_000 * EIGHTEEN_DECIMALS, sender=governance.address)

    # Test invalid dangerTrigger (>=100%)
    with boa.reverts("invalid ref pool config"):
        curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 100_00, 0, 10_00, 100_000 * EIGHTEEN_DECIMALS, sender=governance.address)

    # Test invalid dangerTrigger (>100%)
    with boa.reverts("invalid ref pool config"):
        curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 100_01, 0, 10_00, 100_000 * EIGHTEEN_DECIMALS, sender=governance.address)

    # Test invalid stabilizerAdjustWeight (0)
    with boa.reverts("invalid ref pool config"):
        curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 0, 0, 100_000 * EIGHTEEN_DECIMALS, sender=governance.address)

    # Test invalid stabilizerAdjustWeight (>100%)
    with boa.reverts("invalid ref pool config"):
        curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 0, 100_01, 100_000 * EIGHTEEN_DECIMALS, sender=governance.address)

    # Test invalid stabilizerMaxPoolDebt (0)
    with boa.reverts("invalid ref pool config"):
        curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 0, 10_00, 0, sender=governance.address)

    # Test invalid stabilizerMaxPoolDebt (>25 million)
    with boa.reverts("invalid ref pool config"):
        curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 0, 10_00, 25_000_001 * EIGHTEEN_DECIMALS, sender=governance.address)

    # Test valid edge cases
    aid1 = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 1, 50_00, 0, 1, 1, sender=governance.address)  # Minimum valid values
    aid2 = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 100, 99_99, 0, 100_00, 25_000_000 * EIGHTEEN_DECIMALS, sender=governance.address)  # Maximum valid values
    
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
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 0, 10_00, 100_000 * EIGHTEEN_DECIMALS, sender=governance.address)
    
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
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 0, 10_00, 100_000 * EIGHTEEN_DECIMALS, sender=governance.address)
    
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
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 5, 60_00, 0, 10_00, 100_000 * EIGHTEEN_DECIMALS, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock())
    assert curve_prices.confirmGreenRefPoolConfig(aid, sender=governance.address)

    # Initial snapshot should be created during config confirmation
    data = curve_prices.greenRefPoolData()
    assert data.nextIndex == 1
    assert data.lastSnapshot.ratio == 50_00
    assert not data.lastSnapshot.inDanger

    # Add more snapshots in different blocks
    for i in range(4):
        boa.env.time_travel(blocks=1)
        assert curve_prices.addGreenRefPoolSnapshot(sender=teller.address)
        
        data = curve_prices.greenRefPoolData()
        assert data.nextIndex == (i + 2) % 5
        assert data.lastSnapshot.ratio == 50_00
        assert not data.lastSnapshot.inDanger

    # Verify all snapshots are saved
    for i in range(5):
        snapshot = curve_prices.snapShots(i)
        assert snapshot.greenBalance == 10_000 * EIGHTEEN_DECIMALS
        assert snapshot.ratio == 50_00
        assert not snapshot.inDanger


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
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 70_00, 0, 10_00, 100_000 * EIGHTEEN_DECIMALS, sender=governance.address)
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
    assert log.inDanger
    _test(75_00, log.greenRatio)

    # Verify snapshot shows danger
    data = curve_prices.greenRefPoolData()
    _test(75_00, data.lastSnapshot.ratio)
    assert data.lastSnapshot.inDanger
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
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 65_00, 0, 10_00, 100_000 * EIGHTEEN_DECIMALS, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock())
    assert curve_prices.confirmGreenRefPoolConfig(aid, sender=governance.address)

    # Create danger condition by adding GREEN to pool
    swap_amount = 5_000 * EIGHTEEN_DECIMALS
    swapGreenForUsdc(swap_amount)

    # Take first danger snapshot
    boa.env.time_travel(blocks=1)
    assert curve_prices.addGreenRefPoolSnapshot(sender=teller.address)
    data = curve_prices.greenRefPoolData()
    assert data.lastSnapshot.inDanger
    assert data.numBlocksInDanger == 0

    # Wait 5 blocks and take another danger snapshot. The rolling ratio enters
    # danger here, so this establishes the danger-duration anchor.
    boa.env.time_travel(blocks=5)
    assert curve_prices.addGreenRefPoolSnapshot(sender=teller.address)
    data = curve_prices.greenRefPoolData()
    assert data.lastSnapshot.inDanger
    assert data.numBlocksInDanger == 0

    # Wait 3 more blocks and take another danger snapshot
    boa.env.time_travel(blocks=3)
    assert curve_prices.addGreenRefPoolSnapshot(sender=teller.address)
    data = curve_prices.greenRefPoolData()
    assert data.lastSnapshot.inDanger
    assert data.numBlocksInDanger == 3

    # Rebalance pool to exit danger by removing GREEN from pool
    usdc_swap_amount = 5_000 * (10 ** usdc_token.decimals())
    swapUsdcForGreen(usdc_swap_amount)

    # One safe-looking spot observation cannot clear rolling danger history.
    boa.env.time_travel(blocks=2)
    assert curve_prices.addGreenRefPoolSnapshot(sender=teller.address)

    data = curve_prices.greenRefPoolData()
    assert not data.lastSnapshot.inDanger
    assert data.numBlocksInDanger >= 3


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
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 3, 60_00, 0, 10_00, 100_000 * EIGHTEEN_DECIMALS, sender=governance.address)
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
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 0, 10_00, 100_000 * EIGHTEEN_DECIMALS, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock())
    assert curve_prices.confirmGreenRefPoolConfig(aid, sender=governance.address)

    # Try to add another snapshot in the same block - should return False
    result = curve_prices.addGreenRefPoolSnapshot(sender=teller.address)
    assert not result

    # Move to next block - should work
    boa.env.time_travel(blocks=1)
    result = curve_prices.addGreenRefPoolSnapshot(sender=teller.address)
    assert result


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
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 0, 10_00, 100_000 * EIGHTEEN_DECIMALS, sender=governance.address)
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
    
    # Should be a duration-weighted average of the chronological observations.
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
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 10, 10_00, 100_000 * EIGHTEEN_DECIMALS, sender=governance.address)
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

    # The new observation has zero duration in its write block, so only the
    # balanced observation contributes until a later block.
    status = curve_prices.getCurrentGreenPoolStatus()
    assert status.weightedRatio == 50_00

    boa.env.time_travel(blocks=1)
    status = curve_prices.getCurrentGreenPoolStatus()
    imbalanced_ratio = status.weightedRatio
    assert imbalanced_ratio > 50_00

    # Travel 11 blocks (making first snapshot stale)
    boa.env.time_travel(blocks=11)
    
    # Should only use recent snapshot now (first snapshot is stale)
    status = curve_prices.getCurrentGreenPoolStatus()

    # Both observations are now stale; the fallback is age-bounded too.
    assert status.weightedRatio == 0


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
        curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 0, 10_00, 100_000 * EIGHTEEN_DECIMALS, sender=bob)

    # Setup valid config first
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 0, 10_00, 100_000 * EIGHTEEN_DECIMALS, sender=governance.address)
    
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
    # Proposal sees Curve's default 50% ratio, but confirmation must reject the
    # required nonzero seed and roll the pending confirmation back atomically.
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 0, 10_00, 100_000 * EIGHTEEN_DECIMALS, sender=governance.address)
    assert aid != 0

    boa.env.time_travel(blocks=curve_prices.actionTimeLock())
    with boa.reverts("invalid snapshot"):
        curve_prices.confirmGreenRefPoolConfig(aid, sender=governance.address)
    assert curve_prices.greenRefPoolConfig().pool == ZERO_ADDRESS
    assert curve_prices.pendingGreenRefPoolConfig(aid).pool == deployed_green_pool


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
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 100, 60_00, 0, 10_00, 100_000 * EIGHTEEN_DECIMALS, sender=governance.address)
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
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 0, 10_00, 100_000 * EIGHTEEN_DECIMALS, sender=governance.address)
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
def test_capacity_config_update_resets_ring(
    teller,
    deployed_green_pool,
    curve_prices,
    governance,
    addSeedGreenLiq,
):
    addSeedGreenLiq()

    # Setup initial config
    aid1 = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 5, 60_00, 0, 10_00, 100_000 * EIGHTEEN_DECIMALS, sender=governance.address)
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
    aid2 = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 8, 70_00, 5, 20_00, 200_000 * EIGHTEEN_DECIMALS, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock())
    assert curve_prices.confirmGreenRefPoolConfig(aid2, sender=governance.address)

    # Verify config updated
    config = curve_prices.greenRefPoolConfig()
    assert config.maxNumSnapshots == 8
    assert config.dangerTrigger == 70_00
    assert config.staleBlocks == 5
    assert config.stabilizerAdjustWeight == 20_00
    assert config.stabilizerMaxPoolDebt == 200_000 * EIGHTEEN_DECIMALS

    # Test that stabilizer config is also updated
    stabilizer_config = curve_prices.getGreenStabilizerConfig()
    assert stabilizer_config.pool == deployed_green_pool
    assert stabilizer_config.stabilizerAdjustWeight == 20_00
    assert stabilizer_config.stabilizerMaxPoolDebt == 200_000 * EIGHTEEN_DECIMALS

    # Capacity changes physically clear the ring and seed exactly one snapshot.
    data = curve_prices.greenRefPoolData()
    assert data.nextIndex == 1
    assert curve_prices.snapShots(0).update == data.lastSnapshot.update
    for index in range(1, 100):
        assert curve_prices.snapShots(index).update == 0


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
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 0, 10_00, 100_000 * EIGHTEEN_DECIMALS, sender=governance.address)
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
        curve_prices.setGreenRefPoolConfig(no_green_pool, 10, 60_00, 0, 10_00, 100_000 * EIGHTEEN_DECIMALS, sender=governance.address)


@pytest.base
def test_decimal_handling_edge_cases(
    deployed_green_pool,
    curve_prices,
    governance,
    addSeedGreenLiq,
):
    addSeedGreenLiq()
    
    # Test with current setup (USDC = 6 decimals)
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 0, 10_00, 100_000 * EIGHTEEN_DECIMALS, sender=governance.address)
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
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 3, 10_00, 100_000 * EIGHTEEN_DECIMALS, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock())
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
    
    # Give the newest observation nonzero duration, then check both are valid.
    boa.env.time_travel(blocks=1)
    status = curve_prices.getCurrentGreenPoolStatus()
    weighted_ratio_before_stale = status.weightedRatio
    # Should be between the initial (50%) and imbalanced ratios
    assert initial_ratio < weighted_ratio_before_stale < imbalanced_ratio
    
    # Travel past stale threshold to make all snapshots stale
    # Snapshots become stale when: block.number > snapshot.update + staleBlocks
    boa.env.time_travel(blocks=5)
    
    # The last-snapshot fallback is also stale after the boundary.
    status = curve_prices.getCurrentGreenPoolStatus()
    data = curve_prices.greenRefPoolData()
    
    assert status.weightedRatio == 0
    assert data.lastSnapshot.ratio == imbalanced_ratio


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
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 3, 10_00, 100_000 * EIGHTEEN_DECIMALS, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock())
    assert curve_prices.confirmGreenRefPoolConfig(aid, sender=governance.address)
    
    # Record the initial snapshot block (created during config confirmation)
    data = curve_prices.greenRefPoolData()
    
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
    
    # Now both the ring and last-snapshot fallback are stale.
    status = curve_prices.getCurrentGreenPoolStatus()
    assert status.weightedRatio == 0


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
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 0, 10_00, 100_000 * EIGHTEEN_DECIMALS, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock())
    assert curve_prices.confirmGreenRefPoolConfig(aid, sender=governance.address)
    
    # Pause the contract
    curve_prices.pause(True, sender=switchboard_alpha.address)
    
    # All functions should be blocked when paused
    with boa.reverts("contract paused"):
        curve_prices.setGreenRefPoolConfig(deployed_green_pool, 5, 70_00, 0, 15_00, 150_000 * EIGHTEEN_DECIMALS, sender=governance.address)
    
    with boa.reverts("contract paused"):
        curve_prices.confirmGreenRefPoolConfig(123, sender=governance.address)
        
    with boa.reverts("contract paused"):
        curve_prices.cancelGreenRefPoolConfig(123, sender=governance.address)
    
    # fails gracefully if paused
    assert not curve_prices.addGreenRefPoolSnapshot(sender=teller.address)
    
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
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 0, 10_00, 100_000 * EIGHTEEN_DECIMALS, sender=governance.address)
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
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 0, 10_00, 100_000 * EIGHTEEN_DECIMALS, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock())
    assert curve_prices.confirmGreenRefPoolConfig(aid, sender=governance.address)
    
    # Create danger condition - need enough to exceed 60%
    swap_amount = 2_500 * EIGHTEEN_DECIMALS
    swapGreenForUsdc(swap_amount)
    
    boa.env.time_travel(blocks=1)
    assert curve_prices.addGreenRefPoolSnapshot(sender=teller.address)
    
    data = curve_prices.greenRefPoolData()
    assert data.lastSnapshot.inDanger
    assert data.numBlocksInDanger == 0
    
    # Exit danger immediately (within same block would be prevented)
    boa.env.time_travel(blocks=1)
    usdc_swap_amount = 2_000 * (10 ** usdc_token.decimals())
    swapUsdcForGreen(usdc_swap_amount)
    
    assert curve_prices.addGreenRefPoolSnapshot(sender=teller.address)
    
    data = curve_prices.greenRefPoolData()
    assert not data.lastSnapshot.inDanger
    assert data.numBlocksInDanger == 0  # Should reset to 0


@pytest.base
def test_usdc_dominant_pool_scenarios(
    deployed_green_pool,
    curve_prices,
    governance,
    addSeedGreenLiq,
    swapUsdcForGreen,
    teller,
    usdc_token,
    _test,
):
    """Test scenarios where USDC dominates the pool (GREEN ratio < 50%)"""
    addSeedGreenLiq()  # Start with balanced pool (50/50)

    # Setup config with 50% danger trigger (minimum allowed)
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 50_00, 0, 10_00, 100_000 * EIGHTEEN_DECIMALS, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock())
    assert curve_prices.confirmGreenRefPoolConfig(aid, sender=governance.address)

    # Initial balanced state
    green_balance, ratio = curve_prices.getCurvePoolData()
    assert ratio == 50_00
    assert green_balance == 10_000 * EIGHTEEN_DECIMALS

    # Create USDC dominance by swapping large amount of USDC for GREEN
    # This removes GREEN from pool and adds USDC, decreasing GREEN ratio
    large_usdc_swap = 8_000 * (10 ** usdc_token.decimals())  # Large USDC amount
    swapUsdcForGreen(large_usdc_swap)

    # Check the imbalanced pool state
    new_green_balance, new_ratio = curve_prices.getCurvePoolData()
    assert new_green_balance < green_balance  # Less GREEN in pool
    assert new_ratio < 50_00  # GREEN ratio should be below 50%
    _test(10_70, new_ratio)  # Should be around 10.7% GREEN after large swap

    # Take snapshot of USDC-dominant pool
    boa.env.time_travel(blocks=1)
    assert curve_prices.addGreenRefPoolSnapshot(sender=teller.address)

    # The instantaneous snapshot is below the trigger, but it has zero duration
    # in its write block. The prior 50% observation therefore remains the
    # rolling classification and credits its one evidenced danger block.
    data = curve_prices.greenRefPoolData()
    assert data.lastSnapshot.ratio < 50_00
    assert not data.lastSnapshot.inDanger  # Below 50% trigger
    assert data.numBlocksInDanger == 1

    # Give the low-ratio observation duration before reading the rollup.
    boa.env.time_travel(blocks=1)
    status = curve_prices.getCurrentGreenPoolStatus()
    assert status.weightedRatio < 50_00
    assert status.dangerTrigger == 50_00

    # Create another USDC-dominant snapshot with different ratio
    moderate_usdc_swap = 2_000 * (10 ** usdc_token.decimals())
    swapUsdcForGreen(moderate_usdc_swap)
    
    boa.env.time_travel(blocks=1)
    assert curve_prices.addGreenRefPoolSnapshot(sender=teller.address)

    # Get final pool state
    final_green_balance, final_ratio = curve_prices.getCurvePoolData()
    assert final_green_balance < new_green_balance  # Even less GREEN
    assert final_ratio < new_ratio  # Even lower GREEN ratio
    _test(3_20, final_ratio)  # Should be around 3.2% GREEN after second swap

    # Verify weighted ratio uses all USDC-dominant snapshots
    status = curve_prices.getCurrentGreenPoolStatus()
    assert status.weightedRatio < 50_00
    # Should be a duration-weighted average including the initial balanced snapshot.


@pytest.base
def test_green_scarcity_recovery_scenarios(
    deployed_green_pool,
    curve_prices,
    governance,
    addSeedGreenLiq,
    swapUsdcForGreen,
    swapGreenForUsdc,
    teller,
    usdc_token,
):
    """Test recovery from GREEN scarcity (ratio < 50%) back to balance"""
    addSeedGreenLiq()

    # Setup config
    aid = curve_prices.setGreenRefPoolConfig(deployed_green_pool, 10, 60_00, 0, 10_00, 100_000 * EIGHTEEN_DECIMALS, sender=governance.address)
    boa.env.time_travel(blocks=curve_prices.actionTimeLock())
    assert curve_prices.confirmGreenRefPoolConfig(aid, sender=governance.address)

    # Create GREEN scarcity (ratio < 50%)
    large_usdc_swap = 6_000 * (10 ** usdc_token.decimals())
    swapUsdcForGreen(large_usdc_swap)
    
    boa.env.time_travel(blocks=1)
    assert curve_prices.addGreenRefPoolSnapshot(sender=teller.address)

    # Verify GREEN scarcity
    data = curve_prices.greenRefPoolData()
    scarcity_ratio = data.lastSnapshot.ratio
    assert scarcity_ratio < 50_00
    assert not data.lastSnapshot.inDanger  # Below 60% danger trigger

    # Begin recovery - add GREEN back to pool
    recovery_green_swap = 3_000 * EIGHTEEN_DECIMALS
    swapGreenForUsdc(recovery_green_swap)
    
    boa.env.time_travel(blocks=1)
    assert curve_prices.addGreenRefPoolSnapshot(sender=teller.address)

    # Check partial recovery
    data = curve_prices.greenRefPoolData()
    recovery_ratio = data.lastSnapshot.ratio
    assert recovery_ratio > scarcity_ratio  # Should be higher than scarcity
    assert recovery_ratio < 50_00 or recovery_ratio > 50_00  # Could be above or below 50%

    # Complete recovery to balance
    final_green_swap = 2_000 * EIGHTEEN_DECIMALS
    swapGreenForUsdc(final_green_swap)
    
    boa.env.time_travel(blocks=1)
    assert curve_prices.addGreenRefPoolSnapshot(sender=teller.address)

    # Verify recovery trend in weighted ratio
    status = curve_prices.getCurrentGreenPoolStatus()
    # Should reflect the progression from scarcity to recovery
    assert status.weightedRatio != scarcity_ratio  # Should be different from initial scarcity


############################
# SC-16 / SC-23 Remediation #
############################


@pytest.mark.fork("local", "base")
def test_sc16_single_safe_snapshot_preserves_danger_history(local_curve_ref_system):
    curve, pool, _, governance, snapshotter = local_curve_ref_system
    _confirm_local_ref_config(curve, pool, governance, capacity=2, trigger=60_00)

    _set_local_green_ratio(pool, 80)
    boa.env.time_travel(blocks=1)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    boa.env.time_travel(blocks=5)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    boa.env.time_travel(blocks=5)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    danger_blocks = curve.greenRefPoolData().numBlocksInDanger
    assert danger_blocks == 5

    _set_local_green_ratio(pool, 20)
    boa.env.time_travel(blocks=1)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    assert curve.greenRefPoolData().numBlocksInDanger >= danger_blocks


@pytest.mark.fork("local", "base")
def test_sc23_fully_stale_status_returns_zero(local_curve_ref_system):
    curve, pool, _, governance, _ = local_curve_ref_system
    _confirm_local_ref_config(curve, pool, governance, stale_blocks=3)
    boa.env.time_travel(blocks=4)
    assert curve.getCurrentGreenPoolStatus().weightedRatio == 0

    # Category C retains the ring, and an explicit zero restores deliberate
    # no-expiry behavior without adding a confirmation snapshot.
    _confirm_local_ref_config(curve, pool, governance, stale_blocks=0)
    seeded_update = curve.greenRefPoolData().lastSnapshot.update
    boa.env.time_travel(blocks=10_000)
    assert curve.getCurrentGreenPoolStatus().weightedRatio == 50_00
    assert curve.greenRefPoolData().lastSnapshot.update == seeded_update


@pytest.mark.fork("local", "base")
def test_capacity_regrowth_cannot_resurrect_discarded_slots(local_curve_ref_system):
    curve, pool, _, governance, snapshotter = local_curve_ref_system
    _confirm_local_ref_config(curve, pool, governance, capacity=4)

    for green_ratio in (60, 70, 80, 90):
        pool.setBalances((100 - green_ratio) * EIGHTEEN_DECIMALS, green_ratio * EIGHTEEN_DECIMALS)
        boa.env.time_travel(blocks=1)
        assert curve.addGreenRefPoolSnapshot(sender=snapshotter)

    _confirm_local_ref_config(curve, pool, governance, capacity=2)
    pool.setBalances(15 * EIGHTEEN_DECIMALS, 85 * EIGHTEEN_DECIMALS)
    boa.env.time_travel(blocks=1)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    _confirm_local_ref_config(curve, pool, governance, capacity=4)

    assert curve.greenRefPoolData().nextIndex == 1
    for index in range(1, 100):
        assert curve.snapShots(index).update == 0


@pytest.mark.fork("local", "base")
def test_extreme_stale_blocks_rejected_without_poisoning_view(local_curve_ref_system):
    curve, pool, _, governance, _ = local_curve_ref_system
    with boa.reverts("invalid ref pool config"):
        curve.setGreenRefPoolConfig(
            pool,
            10,
            60_00,
            2**256 - 1,
            10_00,
            100_000 * EIGHTEEN_DECIMALS,
            sender=governance,
        )


@pytest.mark.fork("local", "base")
def test_duration_weighting_is_exact_and_ignores_green_balance(local_curve_ref_system):
    curve, pool, _, governance, snapshotter = local_curve_ref_system
    _confirm_local_ref_config(curve, pool, governance, capacity=4)

    # The first observation is 50% at block B. Ratios observed at B+2 and B+5
    # weight the prior observations for 2 and 3 blocks respectively.
    pool.setBalances(1 * EIGHTEEN_DECIMALS, 4 * EIGHTEEN_DECIMALS)
    boa.env.time_travel(blocks=2)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    pool.setBalances(4 * EIGHTEEN_DECIMALS, 1 * EIGHTEEN_DECIMALS)
    boa.env.time_travel(blocks=3)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    assert curve.getCurrentGreenPoolStatus().weightedRatio == (50_00 * 2 + 80_00 * 3) // 5

    # The newest 20% observation then owns the next four blocks. Its tiny GREEN
    # balance is deliberately irrelevant to weighting.
    boa.env.time_travel(blocks=4)
    assert curve.getCurrentGreenPoolStatus().weightedRatio == (
        50_00 * 2 + 80_00 * 3 + 20_00 * 4
    ) // 9


@pytest.mark.fork("local", "base")
def test_wrapped_ring_traversal_remains_chronological(local_curve_ref_system):
    curve, pool, _, governance, snapshotter = local_curve_ref_system
    _confirm_local_ref_config(curve, pool, governance, capacity=3)

    for blocks, ratio in ((1, 60), (2, 70), (3, 80)):
        _set_local_green_ratio(pool, ratio)
        boa.env.time_travel(blocks=blocks)
        assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    assert curve.greenRefPoolData().nextIndex == 1

    boa.env.time_travel(blocks=2)
    # Live wrapped chronology is 60% for 2 blocks, 70% for 3, then 80% for 2.
    assert curve.getCurrentGreenPoolStatus().weightedRatio == (
        60_00 * 2 + 70_00 * 3 + 80_00 * 2
    ) // 7


@pytest.mark.fork("local", "base")
def test_zero_stale_blocks_still_requires_a_later_safe_block(local_curve_ref_system):
    curve, pool, _, governance, snapshotter = local_curve_ref_system
    _establish_local_rolling_danger(
        curve,
        pool,
        governance,
        snapshotter,
        stale_blocks=0,
    )

    _set_local_green_ratio(pool, 20)
    boa.env.time_travel(blocks=1)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    boa.env.time_travel(blocks=1)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    danger_blocks = curve.greenRefPoolData().numBlocksInDanger
    assert danger_blocks > 0
    assert not curve.addGreenRefPoolSnapshot(sender=snapshotter)
    assert curve.greenRefPoolData().numBlocksInDanger == danger_blocks

    boa.env.time_travel(blocks=1)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    assert curve.greenRefPoolData().numBlocksInDanger == 0


@pytest.mark.fork("local", "base")
def test_sparse_recovery_exact_boundary_and_stale_gap_restart(local_curve_ref_system):
    curve, pool, _, governance, snapshotter = local_curve_ref_system
    _establish_local_rolling_danger(
        curve,
        pool,
        governance,
        snapshotter,
        stale_blocks=3,
    )
    _set_local_green_ratio(pool, 20)
    boa.env.time_travel(blocks=1)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    boa.env.time_travel(blocks=1)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    recovery_start = boa.env.evm.patch.block_number
    danger_blocks = curve.greenRefPoolData().numBlocksInDanger

    with boa.env.anchor():
        boa.env.time_travel(blocks=3)
        assert boa.env.evm.patch.block_number == recovery_start + 3
        assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
        assert curve.greenRefPoolData().numBlocksInDanger == 0

    boa.env.time_travel(blocks=4)
    status = curve.getCurrentGreenPoolStatus()
    assert status.weightedRatio == 0
    assert status.numBlocksInDanger == danger_blocks

    # One block past freshness cannot bridge recovery. The new safe observation
    # restarts recovery and only a later exact-boundary observation clears it.
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    restarted_at = boa.env.evm.patch.block_number
    assert curve.greenRefPoolData().numBlocksInDanger == danger_blocks
    boa.env.time_travel(blocks=2)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    assert curve.greenRefPoolData().numBlocksInDanger == danger_blocks
    boa.env.time_travel(blocks=1)
    assert boa.env.evm.patch.block_number == restarted_at + 3
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    assert curve.greenRefPoolData().numBlocksInDanger == 0


@pytest.mark.fork("local", "base")
def test_danger_returns_after_unavailable_gap_from_preserved_history(local_curve_ref_system):
    curve, pool, _, governance, snapshotter = local_curve_ref_system
    _establish_local_rolling_danger(
        curve,
        pool,
        governance,
        snapshotter,
        stale_blocks=3,
    )
    preserved = curve.greenRefPoolData().numBlocksInDanger
    boa.env.time_travel(blocks=4)
    assert curve.getCurrentGreenPoolStatus().weightedRatio == 0
    assert curve.greenRefPoolData().numBlocksInDanger == preserved

    _set_local_green_ratio(pool, 80)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    status = curve.getCurrentGreenPoolStatus()
    assert status.weightedRatio >= status.dangerTrigger
    assert status.numBlocksInDanger == preserved
    boa.env.time_travel(blocks=1)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    assert curve.greenRefPoolData().numBlocksInDanger == preserved + 1


@pytest.mark.fork("local", "base")
def test_spot_only_danger_restarts_recovery_without_rate_signal(
    local_curve_ref_system,
    price_desk,
    credit_engine,
    governance,
):
    curve, pool, _, local_governance, snapshotter = local_curve_ref_system
    _establish_local_rolling_danger(
        curve,
        pool,
        local_governance,
        snapshotter,
        stale_blocks=10,
    )
    preserved = curve.greenRefPoolData().numBlocksInDanger
    _set_local_green_ratio(pool, 20)

    # Capacity reset preserves the counter and seeds a safe recovery anchor.
    _confirm_local_ref_config(
        curve,
        pool,
        local_governance,
        capacity=5,
        trigger=60_00,
        stale_blocks=10,
    )
    assert curve.greenRefPoolData().numBlocksInDanger == preserved
    boa.env.time_travel(blocks=9)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)

    for _ in range(2):
        _set_local_green_ratio(pool, 80)
        boa.env.time_travel(blocks=1)
        assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
        status = curve.getCurrentGreenPoolStatus()
        assert status.weightedRatio < status.dangerTrigger
        assert status.numBlocksInDanger == preserved

    assert price_desk.startAddressUpdateToRegistry(2, curve, sender=governance.address)
    boa.env.time_travel(blocks=price_desk.registryChangeTimeLock() + 1)
    assert price_desk.confirmAddressUpdateToRegistry(2, sender=governance.address)
    assert curve.getCurrentGreenPoolStatus().weightedRatio < 60_00
    assert credit_engine.getDynamicBorrowRate(1_000) == 1_000


@pytest.mark.fork("local", "base")
def test_future_and_non_monotonic_snapshot_updates_fail_safe(local_curve_ref_system):
    curve, pool, _, governance, snapshotter = local_curve_ref_system
    _confirm_local_ref_config(curve, pool, governance, capacity=3)
    boa.env.time_travel(blocks=1)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)

    current = boa.env.evm.patch.block_number
    curve.eval(f"self.snapShots[0].update = {current + 1}")
    assert curve.getCurrentGreenPoolStatus().weightedRatio == 0

    curve.eval(f"self.snapShots[0].update = {current}")
    curve.eval(f"self.snapShots[1].update = {current}")
    assert curve.getCurrentGreenPoolStatus().weightedRatio == 0


@pytest.mark.fork("local", "base")
def test_weighted_ratio_product_overflow_returns_unavailable(local_curve_ref_system):
    curve, pool, _, governance, _ = local_curve_ref_system
    _confirm_local_ref_config(curve, pool, governance, capacity=3)

    # Corrupt the otherwise valid seed ratio to exercise the defensive checked
    # multiplication branch without changing production validation bounds.
    curve.eval(f"self.snapShots[0].ratio = {2**256 - 1}")
    boa.env.time_travel(blocks=2)

    assert curve.getCurrentGreenPoolStatus().weightedRatio == 0


@pytest.mark.fork("local", "base")
def test_weighted_ratio_sum_overflow_returns_unavailable(local_curve_ref_system):
    curve, pool, _, governance, snapshotter = local_curve_ref_system
    _confirm_local_ref_config(curve, pool, governance, capacity=3)

    # Each interval product fits independently: (MAX // 2) * 2 == MAX - 1,
    # then 2 * 1 == 2. Their numerator sum does not fit and must fail closed.
    boa.env.time_travel(blocks=2)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    curve.eval(f"self.snapShots[0].ratio = {(2**256 - 1) // 2}")
    curve.eval("self.snapShots[1].ratio = 2")
    boa.env.time_travel(blocks=1)

    assert curve.getCurrentGreenPoolStatus().weightedRatio == 0


@pytest.mark.fork("local", "base")
def test_danger_counter_overflow_guard_preserves_state(local_curve_ref_system):
    curve, pool, _, governance, snapshotter = local_curve_ref_system
    _confirm_local_ref_config(curve, pool, governance, capacity=2)
    _set_local_green_ratio(pool, 80)
    boa.env.time_travel(blocks=1)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)

    current = boa.env.evm.patch.block_number
    preserved = 2**256 - 2
    curve.eval(f"self.greenRefPoolData.numBlocksInDanger = {preserved}")
    curve.eval(f"self.greenDangerLastBlock = {current}")
    boa.env.time_travel(blocks=2)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)

    data = curve.greenRefPoolData()
    assert data.numBlocksInDanger == preserved
    assert data.lastSnapshot.update == current + 2


@pytest.mark.fork("local", "base")
def test_capacity_reset_preserves_counter_restarts_recovery_and_seeds_once(local_curve_ref_system):
    curve, pool, _, governance, snapshotter = local_curve_ref_system
    _establish_local_rolling_danger(
        curve,
        pool,
        governance,
        snapshotter,
        stale_blocks=3,
    )
    preserved = curve.greenRefPoolData().numBlocksInDanger
    _set_local_green_ratio(pool, 20)

    aid = curve.setGreenRefPoolConfig(
        pool,
        5,
        60_00,
        3,
        10_00,
        100_000 * EIGHTEEN_DECIMALS,
        sender=governance,
    )
    boa.env.time_travel(blocks=curve.actionTimeLock())
    # An ordinary same-block observation must not suppress the post-reset seed.
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    preserved = curve.greenRefPoolData().numBlocksInDanger
    assert curve.confirmGreenRefPoolConfig(aid, sender=governance)
    data = curve.greenRefPoolData()
    assert data.numBlocksInDanger == preserved
    assert data.nextIndex == 1
    assert data.lastSnapshot.update == boa.env.evm.patch.block_number
    assert curve.snapShots(0).update == data.lastSnapshot.update
    for index in range(1, 100):
        assert curve.snapShots(index).update == 0

    # The capacity reset starts a fresh three-block recovery window.
    boa.env.time_travel(blocks=2)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    assert curve.greenRefPoolData().numBlocksInDanger == preserved
    boa.env.time_travel(blocks=1)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    assert curve.greenRefPoolData().numBlocksInDanger == 0


@pytest.mark.fork("local", "base")
def test_meaning_change_clears_ring_and_danger_state(local_curve_ref_system):
    curve, pool, registry, governance, snapshotter = local_curve_ref_system
    _establish_local_rolling_danger(
        curve,
        pool,
        governance,
        snapshotter,
        stale_blocks=3,
    )
    alt = boa.load(
        "contracts/mock/MockErc20.vy",
        governance,
        "ALT2",
        "ALT2",
        18,
        1,
    )
    new_pool = boa.load("contracts/mock/MockCurveRefPool.vy")
    registry.setPool(new_pool, alt, registry.green())
    new_pool.setBalances(80 * EIGHTEEN_DECIMALS, 20 * EIGHTEEN_DECIMALS)

    _confirm_local_ref_config(
        curve,
        new_pool,
        governance,
        capacity=2,
        trigger=60_00,
        stale_blocks=3,
    )
    data = curve.greenRefPoolData()
    assert data.numBlocksInDanger == 0
    assert data.nextIndex == 1
    assert data.lastSnapshot.ratio == 20_00
    for index in range(1, 100):
        assert curve.snapShots(index).update == 0


@pytest.mark.fork("local", "base")
def test_category_c_and_d_updates_preserve_live_ring_and_counter(local_curve_ref_system):
    curve, pool, _, governance, snapshotter = local_curve_ref_system
    _set_local_green_ratio(pool, 55)
    _confirm_local_ref_config(
        curve,
        pool,
        governance,
        capacity=4,
        trigger=50_00,
        stale_blocks=0,
    )
    boa.env.time_travel(blocks=3)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    assert curve.greenRefPoolData().numBlocksInDanger == 3

    # Propose a threshold/freshness/stabilizer update, then add an observation
    # while it is pending. Confirmation must retain that live observation and
    # must not add a duplicate confirmation snapshot.
    aid = curve.setGreenRefPoolConfig(
        pool,
        4,
        70_00,
        1,
        20_00,
        200_000 * EIGHTEEN_DECIMALS,
        sender=governance,
    )
    boa.env.time_travel(blocks=curve.actionTimeLock())
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    before = curve.greenRefPoolData()
    assert curve.confirmGreenRefPoolConfig(aid, sender=governance)
    after = curve.greenRefPoolData()
    assert after.nextIndex == before.nextIndex
    assert after.lastSnapshot.update == before.lastSnapshot.update
    assert after.numBlocksInDanger == before.numBlocksInDanger

    # Confirmation classifies the retained ring with the new trigger, not the
    # snapshots' historical inDanger flags. One continuously safe block then
    # completes the new one-block recovery window without crediting old time.
    boa.env.time_travel(blocks=1)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    status = curve.getCurrentGreenPoolStatus()
    assert status.weightedRatio == 55_00
    assert status.dangerTrigger == 70_00
    assert status.numBlocksInDanger == 0

    # A subsequent stabilizer-only update is Category D: it retains the ring,
    # cursor, counter, recovery state, and an observation added while pending.
    aid = curve.setGreenRefPoolConfig(
        pool,
        4,
        70_00,
        1,
        30_00,
        300_000 * EIGHTEEN_DECIMALS,
        sender=governance,
    )
    boa.env.time_travel(blocks=curve.actionTimeLock())
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    before = curve.greenRefPoolData()
    assert curve.confirmGreenRefPoolConfig(aid, sender=governance)
    after = curve.greenRefPoolData()
    assert after == before


@pytest.mark.fork("local", "base")
def test_reset_seed_failure_reverts_confirmation_atomically(local_curve_ref_system):
    curve, pool, _, governance, snapshotter = local_curve_ref_system
    _confirm_local_ref_config(curve, pool, governance, capacity=3)
    boa.env.time_travel(blocks=1)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    before_config = curve.greenRefPoolConfig()
    before_data = curve.greenRefPoolData()
    before_slots = [curve.snapShots(i) for i in range(3)]

    aid = curve.setGreenRefPoolConfig(
        pool,
        4,
        60_00,
        0,
        10_00,
        100_000 * EIGHTEEN_DECIMALS,
        sender=governance,
    )
    pool.setBalances(0, 0)  # validation ratio is 50%, but seed balance is invalid
    boa.env.time_travel(blocks=curve.actionTimeLock())
    with boa.reverts("invalid snapshot"):
        curve.confirmGreenRefPoolConfig(aid, sender=governance)

    assert curve.greenRefPoolConfig() == before_config
    assert curve.greenRefPoolData() == before_data
    assert [curve.snapShots(i) for i in range(3)] == before_slots
    assert curve.pendingGreenRefPoolConfig(aid).pool == pool.address
    assert curve.hasPendingAction(aid)


@pytest.mark.fork("local", "base")
def test_confirmation_revalidates_pending_pool(local_curve_ref_system):
    curve, pool, registry, governance, _ = local_curve_ref_system
    _confirm_local_ref_config(curve, pool, governance, capacity=3)
    aid = curve.setGreenRefPoolConfig(
        pool,
        4,
        60_00,
        0,
        10_00,
        100_000 * EIGHTEEN_DECIMALS,
        sender=governance,
    )
    registry.setPoolRegistered(pool, False)
    boa.env.time_travel(blocks=curve.actionTimeLock())
    with boa.reverts("invalid ref pool config"):
        curve.confirmGreenRefPoolConfig(aid, sender=governance)
    assert curve.greenRefPoolConfig().maxNumSnapshots == 3
    assert curve.pendingGreenRefPoolConfig(aid).pool == pool.address


@pytest.mark.fork("local", "base")
def test_credit_engine_fail_soft_and_danger_reactivation(
    local_curve_ref_system,
    price_desk,
    credit_engine,
    governance,
    setGeneralDebtConfig,
):
    curve, pool, _, local_governance, snapshotter = local_curve_ref_system
    _establish_local_rolling_danger(
        curve,
        pool,
        local_governance,
        snapshotter,
        stale_blocks=3,
    )
    preserved = curve.greenRefPoolData().numBlocksInDanger

    assert price_desk.startAddressUpdateToRegistry(2, curve, sender=governance.address)
    boa.env.time_travel(blocks=price_desk.registryChangeTimeLock() + 1)
    assert price_desk.confirmAddressUpdateToRegistry(2, sender=governance.address)
    setGeneralDebtConfig(
        _minDynamicRateBoost=100_00,
        _maxDynamicRateBoost=200_00,
        _increasePerDangerBlock=10,
        _maxBorrowRate=100_00,
    )

    status = curve.getCurrentGreenPoolStatus()
    assert status.weightedRatio == 0
    assert status.numBlocksInDanger == preserved
    assert credit_engine.getDynamicBorrowRate(1_000) == 1_000

    _set_local_green_ratio(pool, 80)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    status = curve.getCurrentGreenPoolStatus()
    assert status.weightedRatio >= status.dangerTrigger
    assert status.numBlocksInDanger == preserved
    assert credit_engine.getDynamicBorrowRate(1_000) > 1_000


@pytest.mark.fork("local", "base")
def test_teller_housekeeping_is_the_production_green_ring_writer(
    local_curve_ref_system,
    teller,
    price_desk,
    governance,
    deleverage,
    alice,
):
    curve, pool, registry, local_governance, _ = local_curve_ref_system
    _confirm_local_ref_config(
        curve,
        pool,
        local_governance,
        capacity=4,
        trigger=60_00,
        stale_blocks=10,
    )
    registry.setValidRipeAddr(teller, True)

    assert price_desk.startAddressUpdateToRegistry(
        2,
        curve,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=price_desk.registryChangeTimeLock() + 1)
    assert price_desk.confirmAddressUpdateToRegistry(
        2,
        sender=governance.address,
    )

    before = curve.greenRefPoolData()
    boa.env.time_travel(blocks=1)
    teller.performHousekeeping(
        False,
        alice,
        False,
        sender=deleverage.address,
    )
    after = curve.greenRefPoolData()

    assert after.nextIndex == before.nextIndex + 1
    assert after.lastSnapshot.update == boa.env.evm.patch.block_number
    # A second write in the same block is suppressed even from Teller itself.
    assert not curve.addGreenRefPoolSnapshot(sender=teller.address)


@pytest.mark.fork("local", "base")
def test_rolling_danger_interrupts_recovery_and_resumes_history(local_curve_ref_system):
    curve, pool, _, governance, snapshotter = local_curve_ref_system
    _confirm_local_ref_config(
        curve,
        pool,
        governance,
        capacity=2,
        trigger=60_00,
        stale_blocks=10,
    )

    _set_local_green_ratio(pool, 80)
    for blocks in (1, 2, 3):
        boa.env.time_travel(blocks=blocks)
        assert curve.addGreenRefPoolSnapshot(sender=snapshotter)

    _set_local_green_ratio(pool, 20)
    for blocks in (1, 1):
        boa.env.time_travel(blocks=blocks)
        assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    assert curve.getCurrentGreenPoolStatus().weightedRatio < 60_00
    preserved = curve.greenRefPoolData().numBlocksInDanger

    boa.env.time_travel(blocks=4)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    assert curve.greenRefPoolData().numBlocksInDanger == preserved

    _set_local_green_ratio(pool, 95)
    for blocks in (2, 3):
        boa.env.time_travel(blocks=blocks)
        assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    status = curve.getCurrentGreenPoolStatus()
    assert status.weightedRatio >= status.dangerTrigger
    at_interrupt = status.numBlocksInDanger
    assert at_interrupt >= preserved

    boa.env.time_travel(blocks=5)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    assert curve.greenRefPoolData().numBlocksInDanger == at_interrupt + 5


@pytest.mark.fork("local", "base")
def test_category_c_old_dangerous_new_dangerous_reanchors_at_confirmation(local_curve_ref_system):
    curve, pool, _, governance, snapshotter = local_curve_ref_system
    _confirm_local_ref_config(
        curve,
        pool,
        governance,
        capacity=2,
        trigger=60_00,
        stale_blocks=0,
    )
    _set_local_green_ratio(pool, 80)
    for blocks in (1, 2, 3):
        boa.env.time_travel(blocks=blocks)
        assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    before = curve.greenRefPoolData().numBlocksInDanger

    aid = curve.setGreenRefPoolConfig(
        pool,
        2,
        65_00,
        0,
        10_00,
        100_000 * EIGHTEEN_DECIMALS,
        sender=governance,
    )
    boa.env.time_travel(blocks=curve.actionTimeLock())
    assert curve.confirmGreenRefPoolConfig(aid, sender=governance)

    boa.env.time_travel(blocks=7)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    assert curve.greenRefPoolData().numBlocksInDanger == before + 7
    boa.env.time_travel(blocks=4)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    assert curve.greenRefPoolData().numBlocksInDanger == before + 11


@pytest.mark.fork("local", "base")
def test_category_c_old_dangerous_new_safe_starts_recovery_at_confirmation(local_curve_ref_system):
    curve, pool, _, governance, snapshotter = local_curve_ref_system
    _establish_local_rolling_danger(
        curve,
        pool,
        governance,
        snapshotter,
        stale_blocks=0,
    )
    before = curve.greenRefPoolData().numBlocksInDanger

    aid = curve.setGreenRefPoolConfig(
        pool,
        2,
        90_00,
        0,
        10_00,
        100_000 * EIGHTEEN_DECIMALS,
        sender=governance,
    )
    boa.env.time_travel(blocks=curve.actionTimeLock())
    assert curve.confirmGreenRefPoolConfig(aid, sender=governance)

    # Recovery begins at confirmation, not at an anchor from the old trigger.
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    assert curve.greenRefPoolData().numBlocksInDanger == before
    boa.env.time_travel(blocks=1)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    assert curve.greenRefPoolData().numBlocksInDanger == 0


@pytest.mark.fork("local", "base")
def test_category_c_old_safe_new_dangerous_reanchors_at_confirmation(local_curve_ref_system):
    curve, pool, _, governance, snapshotter = local_curve_ref_system
    _confirm_local_ref_config(
        curve,
        pool,
        governance,
        capacity=2,
        trigger=60_00,
        stale_blocks=0,
    )
    _set_local_green_ratio(pool, 55)
    for blocks in (1, 1):
        boa.env.time_travel(blocks=blocks)
        assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    assert curve.getCurrentGreenPoolStatus().weightedRatio == 55_00

    aid = curve.setGreenRefPoolConfig(
        pool,
        2,
        50_00,
        0,
        10_00,
        100_000 * EIGHTEEN_DECIMALS,
        sender=governance,
    )
    boa.env.time_travel(blocks=curve.actionTimeLock())
    assert curve.confirmGreenRefPoolConfig(aid, sender=governance)

    boa.env.time_travel(blocks=5)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    assert curve.greenRefPoolData().numBlocksInDanger == 5


@pytest.mark.fork("local", "base")
def test_category_c_stale_expansion_does_not_bridge_expired_danger(local_curve_ref_system):
    curve, pool, _, governance, snapshotter = local_curve_ref_system
    _establish_local_rolling_danger(
        curve,
        pool,
        governance,
        snapshotter,
        stale_blocks=3,
    )
    before = curve.greenRefPoolData().numBlocksInDanger
    boa.env.time_travel(blocks=4)
    assert curve.getCurrentGreenPoolStatus().weightedRatio == 0

    aid = curve.setGreenRefPoolConfig(
        pool,
        2,
        60_00,
        100,
        10_00,
        100_000 * EIGHTEEN_DECIMALS,
        sender=governance,
    )
    boa.env.time_travel(blocks=curve.actionTimeLock())
    assert curve.confirmGreenRefPoolConfig(aid, sender=governance)

    boa.env.time_travel(blocks=2)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    assert curve.greenRefPoolData().numBlocksInDanger == before + 2


@pytest.mark.fork("local", "base")
def test_category_c_zero_staleness_does_not_bridge_expired_recovery(local_curve_ref_system):
    curve, pool, _, governance, snapshotter = local_curve_ref_system
    _establish_local_rolling_danger(
        curve,
        pool,
        governance,
        snapshotter,
        stale_blocks=3,
    )
    _set_local_green_ratio(pool, 20)
    for blocks in (1, 1):
        boa.env.time_travel(blocks=blocks)
        assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    before = curve.greenRefPoolData().numBlocksInDanger
    assert before != 0

    boa.env.time_travel(blocks=4)
    assert curve.getCurrentGreenPoolStatus().weightedRatio == 0
    aid = curve.setGreenRefPoolConfig(
        pool,
        2,
        60_00,
        0,
        10_00,
        100_000 * EIGHTEEN_DECIMALS,
        sender=governance,
    )
    boa.env.time_travel(blocks=curve.actionTimeLock())
    assert curve.confirmGreenRefPoolConfig(aid, sender=governance)

    # The first safe write cannot reuse a pre-gap recovery anchor.
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    assert curve.greenRefPoolData().numBlocksInDanger == before
    boa.env.time_travel(blocks=1)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    assert curve.greenRefPoolData().numBlocksInDanger == 0


@pytest.mark.fork("local", "base")
def test_category_c_simultaneous_trigger_and_freshness_change_reanchors(local_curve_ref_system):
    curve, pool, _, governance, snapshotter = local_curve_ref_system
    _confirm_local_ref_config(
        curve,
        pool,
        governance,
        capacity=2,
        trigger=60_00,
        stale_blocks=3,
    )
    _set_local_green_ratio(pool, 55)
    for blocks in (1, 1):
        boa.env.time_travel(blocks=blocks)
        assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    assert curve.getCurrentGreenPoolStatus().weightedRatio == 55_00
    boa.env.time_travel(blocks=4)
    assert curve.getCurrentGreenPoolStatus().weightedRatio == 0

    aid = curve.setGreenRefPoolConfig(
        pool,
        2,
        50_00,
        100,
        10_00,
        100_000 * EIGHTEEN_DECIMALS,
        sender=governance,
    )
    boa.env.time_travel(blocks=curve.actionTimeLock())
    assert curve.confirmGreenRefPoolConfig(aid, sender=governance)

    boa.env.time_travel(blocks=2)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    assert curve.greenRefPoolData().numBlocksInDanger == 2


@pytest.mark.fork("local", "base")
def test_category_c_unavailable_history_leaves_continuity_cleared(local_curve_ref_system):
    curve, pool, _, governance, snapshotter = local_curve_ref_system
    _establish_local_rolling_danger(
        curve,
        pool,
        governance,
        snapshotter,
        stale_blocks=3,
    )
    _set_local_green_ratio(pool, 20)
    for blocks in (1, 1):
        boa.env.time_travel(blocks=blocks)
        assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    before = curve.greenRefPoolData().numBlocksInDanger

    boa.env.time_travel(blocks=4)
    assert curve.getCurrentGreenPoolStatus().weightedRatio == 0
    aid = curve.setGreenRefPoolConfig(
        pool,
        2,
        70_00,
        3,
        10_00,
        100_000 * EIGHTEEN_DECIMALS,
        sender=governance,
    )
    boa.env.time_travel(blocks=curve.actionTimeLock())
    assert curve.confirmGreenRefPoolConfig(aid, sender=governance)

    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    assert curve.greenRefPoolData().numBlocksInDanger == before
    boa.env.time_travel(blocks=2)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    assert curve.greenRefPoolData().numBlocksInDanger == before
    boa.env.time_travel(blocks=1)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    assert curve.greenRefPoolData().numBlocksInDanger == 0


@pytest.mark.fork("local", "base")
def test_danger_gap_does_not_credit_stale_elapsed_blocks(local_curve_ref_system):
    curve, pool, _, governance, snapshotter = local_curve_ref_system
    _confirm_local_ref_config(
        curve,
        pool,
        governance,
        capacity=2,
        trigger=60_00,
        stale_blocks=3,
    )
    _set_local_green_ratio(pool, 80)
    for blocks in (1, 2, 3):
        boa.env.time_travel(blocks=blocks)
        assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    before = curve.greenRefPoolData().numBlocksInDanger

    boa.env.time_travel(blocks=10)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    assert curve.greenRefPoolData().numBlocksInDanger == before
    boa.env.time_travel(blocks=2)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    assert curve.greenRefPoolData().numBlocksInDanger == before + 2


@pytest.mark.fork("local", "base")
def test_same_block_non_observational_confirmation_preserves_state(local_curve_ref_system):
    curve, pool, _, governance, snapshotter = local_curve_ref_system
    _confirm_local_ref_config(
        curve,
        pool,
        governance,
        capacity=2,
        trigger=60_00,
        stale_blocks=3,
    )
    _set_local_green_ratio(pool, 80)
    for blocks in (1, 2, 2):
        boa.env.time_travel(blocks=blocks)
        assert curve.addGreenRefPoolSnapshot(sender=snapshotter)

    aid = curve.setGreenRefPoolConfig(
        pool,
        2,
        60_00,
        3,
        10_00,
        100_000 * EIGHTEEN_DECIMALS,
        sender=governance,
    )
    boa.env.time_travel(blocks=curve.actionTimeLock())
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    before = curve.greenRefPoolData()
    assert curve.confirmGreenRefPoolConfig(aid, sender=governance)
    assert curve.greenRefPoolData() == before


@pytest.mark.fork("local", "base")
def test_repeated_spot_only_interruptions_preserve_counter_and_safe_rollup(local_curve_ref_system):
    curve, pool, _, governance, snapshotter = local_curve_ref_system
    _establish_local_rolling_danger(
        curve,
        pool,
        governance,
        snapshotter,
        stale_blocks=20,
    )
    _set_local_green_ratio(pool, 20)

    # Reset to a larger ring with a safe seed. The historical counter remains,
    # while the seed and following safe interval establish a healthy rollup.
    _confirm_local_ref_config(
        curve,
        pool,
        governance,
        capacity=10,
        trigger=60_00,
        stale_blocks=20,
    )
    boa.env.time_travel(blocks=10)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    assert curve.getCurrentGreenPoolStatus().weightedRatio < 60_00
    preserved = curve.greenRefPoolData().numBlocksInDanger

    for _ in range(3):
        _set_local_green_ratio(pool, 90)
        boa.env.time_travel(blocks=1)
        assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
        assert curve.getCurrentGreenPoolStatus().weightedRatio < 60_00
        _set_local_green_ratio(pool, 20)
        boa.env.time_travel(blocks=1)
        assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
        assert curve.getCurrentGreenPoolStatus().weightedRatio < 60_00
        boa.env.time_travel(blocks=3)
        assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
        assert curve.getCurrentGreenPoolStatus().weightedRatio < 60_00

    assert curve.greenRefPoolData().numBlocksInDanger == preserved
    assert curve.getCurrentGreenPoolStatus().weightedRatio < 60_00


@pytest.mark.fork("local", "base")
def test_sc23_exact_freshness_boundary_is_inclusive(local_curve_ref_system):
    curve, pool, _, governance, _ = local_curve_ref_system
    _confirm_local_ref_config(curve, pool, governance, stale_blocks=3)

    boa.env.time_travel(blocks=3)
    assert curve.getCurrentGreenPoolStatus().weightedRatio == 50_00
    boa.env.time_travel(blocks=1)
    assert curve.getCurrentGreenPoolStatus().weightedRatio == 0


@pytest.mark.fork("local", "base")
def test_mixed_stale_and_fresh_intervals_have_exact_weight(local_curve_ref_system):
    curve, pool, _, governance, snapshotter = local_curve_ref_system
    _confirm_local_ref_config(
        curve,
        pool,
        governance,
        capacity=4,
        trigger=60_00,
        stale_blocks=5,
    )

    _set_local_green_ratio(pool, 80)
    boa.env.time_travel(blocks=4)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    _set_local_green_ratio(pool, 20)
    boa.env.time_travel(blocks=2)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    boa.env.time_travel(blocks=1)

    # The 50% seed is stale. The fresh intervals are 80% for two blocks and
    # 20% for one block, so the exact duration-weighted result is 60%.
    assert curve.getCurrentGreenPoolStatus().weightedRatio == 60_00


@pytest.mark.fork("local", "base")
def test_capacity_change_with_counter_and_dangerous_seed_reanchors_exactly(
    local_curve_ref_system,
):
    curve, pool, _, governance, snapshotter = local_curve_ref_system
    _establish_local_rolling_danger(
        curve,
        pool,
        governance,
        snapshotter,
        stale_blocks=0,
    )
    preserved = curve.greenRefPoolData().numBlocksInDanger
    assert preserved == 2

    aid = curve.setGreenRefPoolConfig(
        pool,
        4,
        60_00,
        0,
        10_00,
        100_000 * EIGHTEEN_DECIMALS,
        sender=governance,
    )
    boa.env.time_travel(blocks=curve.actionTimeLock())
    confirmation_block = boa.env.evm.patch.block_number
    assert curve.confirmGreenRefPoolConfig(aid, sender=governance)

    seeded = curve.greenRefPoolData()
    assert seeded.numBlocksInDanger == preserved
    assert seeded.nextIndex == 1
    assert seeded.lastSnapshot.update == confirmation_block
    assert curve.snapShots(0) == seeded.lastSnapshot
    assert [curve.snapShots(index).update for index in range(1, 4)] == [0, 0, 0]

    boa.env.time_travel(blocks=7)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    accrued = curve.greenRefPoolData()
    assert accrued.numBlocksInDanger == preserved + 7
    assert accrued.nextIndex == 2
    assert accrued.lastSnapshot.update == confirmation_block + 7
    assert [curve.snapShots(index).update for index in range(4)] == [
        confirmation_block,
        confirmation_block + 7,
        0,
        0,
    ]


@pytest.mark.fork("local", "base")
def test_capacity_and_classification_change_with_dangerous_seed_reanchors_exactly(
    local_curve_ref_system,
):
    curve, pool, _, governance, snapshotter = local_curve_ref_system
    _establish_local_rolling_danger(
        curve,
        pool,
        governance,
        snapshotter,
        stale_blocks=0,
    )
    preserved = curve.greenRefPoolData().numBlocksInDanger

    aid = curve.setGreenRefPoolConfig(
        pool,
        5,
        70_00,
        20,
        20_00,
        200_000 * EIGHTEEN_DECIMALS,
        sender=governance,
    )
    boa.env.time_travel(blocks=curve.actionTimeLock())
    confirmation_block = boa.env.evm.patch.block_number
    assert curve.confirmGreenRefPoolConfig(aid, sender=governance)
    seeded = curve.greenRefPoolData()
    assert seeded.numBlocksInDanger == preserved
    assert seeded.nextIndex == 1
    assert seeded.lastSnapshot.ratio == 80_00
    assert seeded.lastSnapshot.update == confirmation_block
    assert [curve.snapShots(index).update for index in range(5)] == [
        confirmation_block,
        0,
        0,
        0,
        0,
    ]

    boa.env.time_travel(blocks=4)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    after = curve.greenRefPoolData()
    assert after.numBlocksInDanger == preserved + 4
    assert after.nextIndex == 2
    assert after.lastSnapshot.update == confirmation_block + 4


@pytest.mark.fork("local", "base")
def test_capacity_and_classification_change_with_safe_seed_restarts_recovery(
    local_curve_ref_system,
):
    curve, pool, _, governance, snapshotter = local_curve_ref_system
    _establish_local_rolling_danger(
        curve,
        pool,
        governance,
        snapshotter,
        stale_blocks=3,
    )
    preserved = curve.greenRefPoolData().numBlocksInDanger
    _set_local_green_ratio(pool, 20)

    aid = curve.setGreenRefPoolConfig(
        pool,
        4,
        70_00,
        3,
        20_00,
        200_000 * EIGHTEEN_DECIMALS,
        sender=governance,
    )
    boa.env.time_travel(blocks=curve.actionTimeLock())
    confirmation_block = boa.env.evm.patch.block_number
    assert curve.confirmGreenRefPoolConfig(aid, sender=governance)
    seeded = curve.greenRefPoolData()
    assert seeded.numBlocksInDanger == preserved
    assert seeded.nextIndex == 1
    assert seeded.lastSnapshot.ratio == 20_00
    assert seeded.lastSnapshot.update == confirmation_block

    boa.env.time_travel(blocks=2)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    partial = curve.greenRefPoolData()
    assert partial.numBlocksInDanger == preserved
    assert partial.nextIndex == 2
    assert partial.lastSnapshot.update == confirmation_block + 2

    boa.env.time_travel(blocks=1)
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    complete = curve.greenRefPoolData()
    assert complete.numBlocksInDanger == 0
    assert complete.nextIndex == 3
    assert complete.lastSnapshot.update == confirmation_block + 3
    assert [curve.snapShots(index).update for index in range(4)] == [
        confirmation_block,
        confirmation_block + 2,
        confirmation_block + 3,
        0,
    ]


@pytest.mark.fork("local", "base")
@pytest.mark.parametrize("transition", ("noop", "stabilizer"))
def test_nonclassification_confirmation_preserves_active_danger_anchor(
    local_curve_ref_system,
    transition,
):
    curve, pool, _, governance, snapshotter = local_curve_ref_system
    _establish_local_rolling_danger(
        curve,
        pool,
        governance,
        snapshotter,
        stale_blocks=0,
    )
    before = curve.greenRefPoolData()
    anchor_block = before.lastSnapshot.update
    adjust = 10_00 if transition == "noop" else 30_00
    maximum = (
        100_000 * EIGHTEEN_DECIMALS
        if transition == "noop"
        else 300_000 * EIGHTEEN_DECIMALS
    )
    aid = curve.setGreenRefPoolConfig(
        pool,
        2,
        60_00,
        0,
        adjust,
        maximum,
        sender=governance,
    )
    boa.env.time_travel(blocks=curve.actionTimeLock())
    assert curve.confirmGreenRefPoolConfig(aid, sender=governance)
    assert curve.greenRefPoolData() == before

    boa.env.time_travel(blocks=4)
    write_block = boa.env.evm.patch.block_number
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    after = curve.greenRefPoolData()
    assert after.numBlocksInDanger == before.numBlocksInDanger + (
        write_block - anchor_block
    )
    assert after.nextIndex == (before.nextIndex + 1) % 2
    assert after.lastSnapshot.update == write_block
    assert sorted(
        snapshot.update for snapshot in (curve.snapShots(0), curve.snapShots(1))
    ) == sorted((anchor_block, write_block))


@pytest.mark.fork("local", "base")
@pytest.mark.parametrize("transition", ("noop", "stabilizer"))
def test_nonclassification_confirmation_preserves_active_recovery_window(
    local_curve_ref_system,
    transition,
):
    curve, pool, _, governance, snapshotter = local_curve_ref_system
    _establish_local_rolling_danger(
        curve,
        pool,
        governance,
        snapshotter,
        stale_blocks=3,
    )
    preserved = curve.greenRefPoolData().numBlocksInDanger

    # Category C first establishes a fresh, observable recovery anchor.
    aid = curve.setGreenRefPoolConfig(
        pool,
        2,
        90_00,
        3,
        10_00,
        100_000 * EIGHTEEN_DECIMALS,
        sender=governance,
    )
    boa.env.time_travel(blocks=curve.actionTimeLock())
    recovery_start = boa.env.evm.patch.block_number
    assert curve.confirmGreenRefPoolConfig(aid, sender=governance)

    adjust = 10_00 if transition == "noop" else 30_00
    maximum = (
        100_000 * EIGHTEEN_DECIMALS
        if transition == "noop"
        else 300_000 * EIGHTEEN_DECIMALS
    )
    aid = curve.setGreenRefPoolConfig(
        pool,
        2,
        90_00,
        3,
        adjust,
        maximum,
        sender=governance,
    )
    boa.env.time_travel(blocks=curve.actionTimeLock())
    before = curve.greenRefPoolData()
    assert curve.confirmGreenRefPoolConfig(aid, sender=governance)
    assert curve.greenRefPoolData() == before

    # The original Category-C recovery start remains controlling. If this
    # confirmation reset it, the exact recovery boundary below would not clear.
    assert boa.env.evm.patch.block_number < recovery_start + 3
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    assert curve.greenRefPoolData().numBlocksInDanger == preserved
    assert curve.greenRefPoolData().nextIndex == (before.nextIndex + 1) % 2
    boa.env.time_travel(
        blocks=recovery_start + 3 - boa.env.evm.patch.block_number
    )
    assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    after = curve.greenRefPoolData()
    assert after.numBlocksInDanger == 0
    assert after.lastSnapshot.update == recovery_start + 3
    assert after.nextIndex == before.nextIndex


@pytest.mark.fork("local", "base")
def test_robinhood_repeated_number_suppresses_every_green_ring_write(
    local_curve_ref_system,
    clock_controller,
):
    curve, pool, _, governance, snapshotter = local_curve_ref_system
    _confirm_local_ref_config(curve, pool, governance, stale_blocks=10)
    before = curve.greenRefPoolData()
    current = clock_controller.current
    profile = clock_profile(
        "R-REP128",
        number=current.number,
        timestamp=current.timestamp,
    )

    with clock_controller.scenario(profile, "robinhood_candidate"):
        for step in range(len(profile.points)):
            clock_controller.apply(profile, step)
            assert not curve.addGreenRefPoolSnapshot(sender=snapshotter)
        assert curve.greenRefPoolData() == before


@pytest.mark.fork("local", "base")
def test_robinhood_plus_one_and_jump_profiles_drive_exact_curve_durations(
    local_curve_ref_system,
    clock_controller,
):
    curve, pool, _, governance, snapshotter = local_curve_ref_system
    _confirm_local_ref_config(
        curve,
        pool,
        governance,
        capacity=5,
        trigger=60_00,
        stale_blocks=100,
    )
    _set_local_green_ratio(pool, 80)
    start = curve.greenRefPoolData().lastSnapshot.update
    timestamp = clock_controller.current.timestamp

    plus_one = clock_profile("R-PLUS1", number=start, timestamp=timestamp)
    with clock_controller.scenario(plus_one, "robinhood_candidate"):
        for step, expected_write in enumerate((False, False, True, False)):
            clock_controller.apply(plus_one, step)
            assert (
                curve.addGreenRefPoolSnapshot(sender=snapshotter)
                is expected_write
            )
        data = curve.greenRefPoolData()
        assert data.nextIndex == 2
        assert data.lastSnapshot.update == start + 1

    jumps = clock_profile("R-J2-J4", number=start, timestamp=timestamp)
    with clock_controller.scenario(jumps, "robinhood_candidate"):
        for step, expected_write in enumerate((False, False, True, False, True)):
            clock_controller.apply(jumps, step)
            assert (
                curve.addGreenRefPoolSnapshot(sender=snapshotter)
                is expected_write
            )
        status = curve.getCurrentGreenPoolStatus()
        assert status.weightedRatio == (50_00 * 2 + 80_00 * 2) // 4
        assert status.numBlocksInDanger == 0


@pytest.mark.fork("local", "base")
def test_robinhood_stress_jump_credits_exact_fresh_danger_duration(
    local_curve_ref_system,
    clock_controller,
):
    curve, pool, _, governance, snapshotter = local_curve_ref_system
    _establish_local_rolling_danger(
        curve,
        pool,
        governance,
        snapshotter,
        stale_blocks=100,
    )
    before = curve.greenRefPoolData()
    start = before.lastSnapshot.update
    profile = clock_profile(
        "R-STRESS60",
        number=start,
        timestamp=clock_controller.current.timestamp,
    )
    with clock_controller.scenario(profile, "robinhood_candidate"):
        clock_controller.apply(profile, 0)
        assert not curve.addGreenRefPoolSnapshot(sender=snapshotter)
        clock_controller.apply(profile, 1)
        assert not curve.addGreenRefPoolSnapshot(sender=snapshotter)
        clock_controller.apply(profile, 2)
        assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
        after = curve.greenRefPoolData()
        assert after.numBlocksInDanger == before.numBlocksInDanger + 60
        assert after.lastSnapshot.update == start + 60
        assert after.nextIndex == (before.nextIndex + 1) % 2


@pytest.mark.fork("local", "base")
def test_robinhood_jump_crosses_inclusive_freshness_boundary(
    local_curve_ref_system,
    clock_controller,
):
    curve, pool, _, governance, _ = local_curve_ref_system
    _confirm_local_ref_config(curve, pool, governance, stale_blocks=3)
    seeded = curve.greenRefPoolData().lastSnapshot.update
    profile = clock_profile(
        "BOUNDARY-OPEN",
        boundary=seeded + 3,
        timestamp=clock_controller.current.timestamp,
    )
    with clock_controller.scenario(profile, "robinhood_candidate"):
        clock_controller.apply(profile, 0)
        assert curve.getCurrentGreenPoolStatus().weightedRatio == 50_00
        clock_controller.apply(profile, 1)
        assert curve.getCurrentGreenPoolStatus().weightedRatio == 0


@pytest.mark.fork("local", "base")
def test_robinhood_jump_over_recovery_window_restarts_without_clearing(
    local_curve_ref_system,
    clock_controller,
):
    curve, pool, _, governance, snapshotter = local_curve_ref_system
    _establish_local_rolling_danger(
        curve,
        pool,
        governance,
        snapshotter,
        stale_blocks=3,
    )
    _set_local_green_ratio(pool, 20)
    for _ in range(2):
        boa.env.time_travel(blocks=1)
        assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
    preserved = curve.greenRefPoolData().numBlocksInDanger
    recovery_start = curve.greenRefPoolData().lastSnapshot.update
    assert preserved != 0

    profile = clock_profile(
        "BOUNDARY-WINDOW",
        start=recovery_start + 1,
        end=recovery_start + 3,
        timestamp=clock_controller.current.timestamp,
    )
    with clock_controller.scenario(profile, "robinhood_candidate"):
        clock_controller.apply(profile, 0)
        assert not curve.addGreenRefPoolSnapshot(sender=snapshotter)
        clock_controller.apply(profile, 1)
        assert curve.addGreenRefPoolSnapshot(sender=snapshotter)
        after = curve.greenRefPoolData()
        assert after.numBlocksInDanger == preserved
        assert after.lastSnapshot.update == recovery_start + 4


@pytest.mark.fork("local", "base")
def test_teller_housekeeping_repeated_robinhood_number_writes_once_per_number(
    local_curve_ref_system,
    clock_controller,
    teller,
    price_desk,
    governance,
    deleverage,
    alice,
):
    curve, pool, registry, local_governance, _ = local_curve_ref_system
    _confirm_local_ref_config(
        curve,
        pool,
        local_governance,
        capacity=4,
        trigger=60_00,
        stale_blocks=10,
    )
    registry.setValidRipeAddr(teller, True)
    assert price_desk.startAddressUpdateToRegistry(
        2,
        curve,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=price_desk.registryChangeTimeLock() + 1)
    assert price_desk.confirmAddressUpdateToRegistry(
        2,
        sender=governance.address,
    )

    start = boa.env.evm.patch.block_number
    profile = clock_profile(
        "R-PLUS1",
        number=start,
        timestamp=clock_controller.current.timestamp,
    )
    before = curve.greenRefPoolData()
    with clock_controller.scenario(profile, "robinhood_candidate"):
        for step in range(len(profile.points)):
            clock_controller.apply(profile, step)
            teller.performHousekeeping(
                False,
                alice,
                False,
                sender=deleverage.address,
            )
        after = curve.greenRefPoolData()
        assert after.nextIndex == (before.nextIndex + 2) % 4
        assert after.lastSnapshot.update == start + 1
        assert [curve.snapShots(index).update for index in range(3)] == [
            before.lastSnapshot.update,
            start,
            start + 1,
        ]
