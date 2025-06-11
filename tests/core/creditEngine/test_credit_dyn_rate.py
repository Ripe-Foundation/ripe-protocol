import pytest
import boa


@pytest.fixture(scope="module")
def setupDynamicRate(
    price_desk,
    governance,
    mock_curve_prices,
    setGeneralDebtConfig,
):
    def setupDynamicRate(
        _minDynamicRateBoost = 10000,   # 100% (cleaner default)
        _maxDynamicRateBoost = 30000,   # 300% (cleaner default)
        _increasePerDangerBlock = 10,
        _maxBorrowRate = 100000,        # Very high default to prevent capping
        _weightedRatio = 5000,          # 50%
        _dangerTrigger = 6000,          # 60%
        _numBlocksInDanger = 0,
    ):
        # mock curve price
        if price_desk.getAddr(2) != mock_curve_prices.address:
            assert price_desk.startAddressUpdateToRegistry(2, mock_curve_prices, sender=governance.address)
            boa.env.time_travel(blocks=price_desk.registryChangeTimeLock() + 1)
            assert price_desk.confirmAddressUpdateToRegistry(2, sender=governance.address)

        # set mock data
        mock_curve_prices.setMockGreenPoolData(_weightedRatio, _dangerTrigger, _numBlocksInDanger)

        # set specific dynamic rate config
        setGeneralDebtConfig(
            _minDynamicRateBoost = _minDynamicRateBoost,
            _maxDynamicRateBoost = _maxDynamicRateBoost,
            _increasePerDangerBlock = _increasePerDangerBlock,
            _maxBorrowRate = _maxBorrowRate,
        )

    yield setupDynamicRate


##########################
# Early Exit Conditions #
##########################


def test_no_curve_prices_returns_base_rate(
    setupDynamicRate,
    credit_engine,
    price_desk,
    governance,
):
    """When curve prices contract is not available, return base rate"""
    setupDynamicRate()
    
    # Remove curve prices from registry
    assert price_desk.startAddressDisableInRegistry(2, sender=governance.address)
    boa.env.time_travel(blocks=price_desk.registryChangeTimeLock() + 1)
    assert price_desk.confirmAddressDisableInRegistry(2, sender=governance.address)
    
    # Must return base rate regardless of input
    assert credit_engine.getDynamicBorrowRate(1000) == 1000
    assert credit_engine.getDynamicBorrowRate(5000) == 5000


def test_zero_weighted_ratio_returns_base_rate(
    setupDynamicRate,
    credit_engine,
):
    """When weightedRatio is 0, return base rate"""
    setupDynamicRate(_weightedRatio=0, _dangerTrigger=6000, _numBlocksInDanger=100)
    
    # Must return base rate even with danger blocks present
    assert credit_engine.getDynamicBorrowRate(1500) == 1500


def test_below_danger_trigger_returns_base_rate(
    setupDynamicRate,
    credit_engine,
):
    """When weightedRatio < dangerTrigger, return base rate"""
    setupDynamicRate(_weightedRatio=5999, _dangerTrigger=6000, _numBlocksInDanger=500)
    
    # Must return base rate even with danger blocks present
    assert credit_engine.getDynamicBorrowRate(2000) == 2000


#############################
# Rate Boost Logic Paths   #
#############################


def test_max_dynamic_rate_boost_zero_skips_rate_boost(
    setupDynamicRate,
    credit_engine,
):
    """When maxDynamicRateBoost is 0, skip rate boost calculation"""
    setupDynamicRate(
        _minDynamicRateBoost=1000,  # Irrelevant when max is 0
        _maxDynamicRateBoost=0,
        _weightedRatio=8000,
        _dangerTrigger=6000,
        _numBlocksInDanger=100,
        _increasePerDangerBlock=50,
    )
    
    # Should only get danger boost: (50 * 100) * 10000 // 1000000 = 50
    assert credit_engine.getDynamicBorrowRate(1000) == 1050


def test_at_exact_trigger_gets_min_boost(
    setupDynamicRate,
    credit_engine,
):
    """At weightedRatio == dangerTrigger, get minDynamicRateBoost"""
    setupDynamicRate(
        _minDynamicRateBoost=15000,  # 150%
        _maxDynamicRateBoost=30000,  # 300%
        _weightedRatio=6000,
        _dangerTrigger=6000,
    )
    
    # dynamicRatio = 0, so rateMultiplier = minBoost = 15000
    # rateBoost = 1000 * 15000 // 10000 = 1500
    assert credit_engine.getDynamicBorrowRate(1000) == 2500


def test_at_100_percent_ratio_gets_max_boost(
    setupDynamicRate,
    credit_engine,
):
    """At weightedRatio == 100%, get maxDynamicRateBoost"""
    setupDynamicRate(
        _minDynamicRateBoost=20000,  # 200%
        _maxDynamicRateBoost=50000,  # 500%
        _weightedRatio=10000,
        _dangerTrigger=6000,
    )
    
    # dynamicRatio = (10000-6000)*10000//(10000-6000) = 10000 (100%)
    # rateMultiplier = 20000 + 10000*30000//10000 = 20000 + 30000 = 50000
    # rateBoost = 1200 * 50000 // 10000 = 6000
    assert credit_engine.getDynamicBorrowRate(1200) == 7200


def test_min_boost_equals_max_boost_returns_min(
    setupDynamicRate,
    credit_engine,
):
    """When minBoost == maxBoost, always return minBoost"""
    setupDynamicRate(
        _minDynamicRateBoost=25000,  # 250%
        _maxDynamicRateBoost=25000,  # Same as min
        _weightedRatio=8500,
        _dangerTrigger=7000,
    )
    
    # Should get minBoost regardless of ratio
    # rateBoost = 800 * 25000 // 10000 = 2000
    assert credit_engine.getDynamicBorrowRate(800) == 2800


def test_mid_range_ratio_interpolates_correctly(
    setupDynamicRate,
    credit_engine,
):
    """Mid-range weightedRatio interpolates between min and max boost"""
    setupDynamicRate(
        _minDynamicRateBoost=10000,  # 100%
        _maxDynamicRateBoost=30000,  # 300%
        _weightedRatio=8000,         # 80%
        _dangerTrigger=6000,         # 60%
    )
    
    # Clean calculation: dynamicRatio = (8000-6000)*10000//(10000-6000) = 5000 (50%)
    # rateMultiplier = 10000 + 5000*20000//10000 = 10000 + 10000 = 20000 (200%)
    # rateBoost = 1000 * 20000 // 10000 = 2000
    # Total: 1000 + 2000 = 3000
    assert credit_engine.getDynamicBorrowRate(1000) == 3000


def test_above_100_percent_ratio_uncapped_multiplier(
    setupDynamicRate,
    credit_engine,
    mock_curve_prices,
    _test,
):
    """weightedRatio > 100% can produce multipliers above maxDynamicRateBoost"""
    setupDynamicRate(
        _minDynamicRateBoost=10000,  # 100%
        _maxDynamicRateBoost=20000,  # 200%
        _dangerTrigger=6000,         # 60%
    )
    
    # Set 130% ratio (above 100%)
    mock_curve_prices.setMockGreenPoolData(13000, 6000, 0)
    
    # dynamicRatio = (13000-6000)*10000//(10000-6000) = 17500 (175%)
    # The contract doesn't cap this, so uncapped multiplier calculation:
    # rateMultiplier = 10000 + 17500*10000//10000 = 10000 + 17500 = 27500 (275%)
    # rateBoost = 1000 * 27500 // 10000 = 2750
    # Expected total: 1000 + 2750 = 3750
    _test(3750, credit_engine.getDynamicBorrowRate(1000))


#############################
# Danger Boost Logic Paths #
#############################


def test_zero_blocks_in_danger_no_danger_boost(
    setupDynamicRate,
    credit_engine,
):
    """When numBlocksInDanger is 0, no danger boost applied"""
    setupDynamicRate(
        _weightedRatio=8000,
        _dangerTrigger=6000,
        _numBlocksInDanger=0,
        _increasePerDangerBlock=100,
        _minDynamicRateBoost=0,  # Isolate danger boost
        _maxDynamicRateBoost=0,
    )
    
    # Only get base rate (no boosts)
    assert credit_engine.getDynamicBorrowRate(1500) == 1500


def test_zero_increase_per_danger_block_no_danger_boost(
    setupDynamicRate,
    credit_engine,
):
    """When increasePerDangerBlock is 0, no danger boost applied"""
    setupDynamicRate(
        _weightedRatio=8000,
        _dangerTrigger=6000,
        _numBlocksInDanger=1000,
        _increasePerDangerBlock=0,
        _minDynamicRateBoost=0,  # Isolate danger boost
        _maxDynamicRateBoost=0,
    )
    
    # Only get base rate (no boosts)
    assert credit_engine.getDynamicBorrowRate(1200) == 1200


def test_danger_boost_precise_calculation(
    setupDynamicRate,
    credit_engine,
):
    """Danger boost calculation with specific values"""
    setupDynamicRate(
        _weightedRatio=6000,  # At trigger for minimal rate boost
        _dangerTrigger=6000,
        _numBlocksInDanger=250,
        _increasePerDangerBlock=40,
        _minDynamicRateBoost=0,  # Isolate danger boost
        _maxDynamicRateBoost=0,
    )
    
    # dangerBoost = (40 * 250) * 10000 // 1000000 = 100
    assert credit_engine.getDynamicBorrowRate(1000) == 1100


def test_large_danger_boost_calculation(
    setupDynamicRate,
    credit_engine,
):
    """Large danger boost with high block count"""
    setupDynamicRate(
        _weightedRatio=6000,  # At trigger for minimal rate boost
        _dangerTrigger=6000,
        _numBlocksInDanger=2000,
        _increasePerDangerBlock=150,
        _minDynamicRateBoost=0,  # Isolate danger boost
        _maxDynamicRateBoost=0,
    )
    
    # dangerBoost = (150 * 2000) * 10000 // 1000000 = 3000
    assert credit_engine.getDynamicBorrowRate(500) == 3500


def test_danger_boost_only_with_blocks_below_trigger_impossible(
    setupDynamicRate,
    credit_engine,
):
    """Danger boost cannot apply when below trigger, even with blocks in danger"""
    setupDynamicRate(
        _weightedRatio=5999,  # Below trigger
        _dangerTrigger=6000,
        _numBlocksInDanger=5000,
        _increasePerDangerBlock=200,
    )
    
    # No boost possible when below trigger
    assert credit_engine.getDynamicBorrowRate(2000) == 2000


##########################
# Combined Boost Logic  #
##########################


def test_combined_rate_and_danger_boost_exact_calculation(
    setupDynamicRate,
    credit_engine,
    _test,
):
    """Both rate boost and danger boost active with exact calculation"""
    setupDynamicRate(
        _minDynamicRateBoost=10000,  # 100%
        _maxDynamicRateBoost=30000,  # 300%
        _weightedRatio=8000,         # 80%
        _dangerTrigger=6000,         # 60%
        _numBlocksInDanger=100,      # Round number
        _increasePerDangerBlock=100, # Clean calculation
    )
    
    # Clean calculation:
    # dynamicRatio = (8000-6000)*10000//(10000-6000) = 5000 (50%)
    # rateMultiplier = 10000 + 5000*20000//10000 = 10000 + 10000 = 20000 (200%)
    # rateBoost = 2000 * 20000 // 10000 = 4000
    # dangerBoost = (100 * 100) * 10000 // 1000000 = 100
    # Expected total: 2000 + 4000 + 100 = 6100
    _test(6100, credit_engine.getDynamicBorrowRate(2000))


#######################
# Rate Capping Logic #
#######################


def test_combined_boosts_below_max_borrow_rate_not_capped(
    setupDynamicRate,
    credit_engine,
):
    """Combined boosts below maxBorrowRate are not capped"""
    setupDynamicRate(
        _minDynamicRateBoost=40000,  # 400%
        _maxDynamicRateBoost=40000,  # Same (constant high boost)
        _maxBorrowRate=6000,         # Higher than calculated rate
        _weightedRatio=8000,
        _dangerTrigger=6000,
        _numBlocksInDanger=1000,
        _increasePerDangerBlock=50,
    )
    
    # Calculated rate: 1000 + 4000 + 500 = 5500 (below cap of 6000)
    assert credit_engine.getDynamicBorrowRate(1000) == 5500


def test_actual_rate_capping_demonstration(
    setupDynamicRate,
    credit_engine,
    _test,
):
    """Demonstrate actual rate capping with very low max rate"""
    setupDynamicRate(
        _minDynamicRateBoost=20000,  # 200%
        _maxDynamicRateBoost=20000,  # Same (constant high boost)
        _maxBorrowRate=3000,         # Very low cap
        _weightedRatio=8000,         # 80%
        _dangerTrigger=6000,         # 60%
        _numBlocksInDanger=100,      # Round number
        _increasePerDangerBlock=100, # Clean calculation
    )
    
    # Calculated rate would be: 1000 + 2000 + 100 = 3100
    # But capped at 3000
    assert credit_engine.getDynamicBorrowRate(1000) == 3000


def test_base_rate_above_max_borrow_rate_gets_capped(
    setupDynamicRate,
    credit_engine,
):
    """Base rate above maxBorrowRate gets capped"""
    setupDynamicRate(
        _maxBorrowRate=5000,
        _weightedRatio=8000,
        _dangerTrigger=6000,
    )
    
    # Base rate exceeds max, should be capped
    assert credit_engine.getDynamicBorrowRate(8000) == 5000


def test_danger_boost_alone_triggers_capping(
    setupDynamicRate,
    credit_engine,
):
    """Large danger boost alone can trigger rate capping"""
    setupDynamicRate(
        _minDynamicRateBoost=0,      # No rate boost
        _maxDynamicRateBoost=0,
        _maxBorrowRate=2000,         # Low cap
        _weightedRatio=6000,         # At trigger
        _dangerTrigger=6000,
        _numBlocksInDanger=5000,     # Large number
        _increasePerDangerBlock=100, # High increase
    )
    
    # dangerBoost = (100 * 5000) * 10000 // 1000000 = 5000
    # totalRate = 1000 + 0 + 5000 = 6000, capped at 2000
    assert credit_engine.getDynamicBorrowRate(1000) == 2000


############################
# Edge Cases & Boundaries #
############################


def test_division_by_zero_when_danger_trigger_is_max_impossible(
    setupDynamicRate,
    credit_engine,
):
    """Setting dangerTrigger to 100% would cause division by zero, but is prevented by validation"""
    # This test documents that dangerTrigger=10000 would cause division by zero
    # The SwitchboardAlpha contract should prevent this configuration
    setupDynamicRate(
        _weightedRatio=9900,   # Close to but not at 100%
        _dangerTrigger=9900,   # Close to but not at 100%
    )
    
    # At trigger exactly, dynamicRatio = 0, gets minBoost
    assert credit_engine.getDynamicBorrowRate(1000) == 2000  # 1000 + 1000 (100% boost)


def test_zero_base_rate_with_boosts(
    setupDynamicRate,
    credit_engine,
):
    """Zero base rate with boosts applied"""
    setupDynamicRate(
        _minDynamicRateBoost=20000,  # 200%
        _maxDynamicRateBoost=20000,
        _weightedRatio=8000,
        _dangerTrigger=6000,
        _numBlocksInDanger=100,
        _increasePerDangerBlock=50,
    )
    
    # Rate boost: 0 * 20000 // 10000 = 0
    # Danger boost: (50 * 100) * 10000 // 1000000 = 50
    # Total: 0 + 0 + 50 = 50
    assert credit_engine.getDynamicBorrowRate(0) == 50


def test_calc_dynamic_rate_boost_with_zero_ratio(
    setupDynamicRate,
    credit_engine,
):
    """_calcDynamicRateBoost with _ratio == 0 returns _minBoost"""
    setupDynamicRate(
        _minDynamicRateBoost=12000,  # 120%
        _maxDynamicRateBoost=50000,  # 500%
        _weightedRatio=6000,         # Exactly at trigger
        _dangerTrigger=6000,
    )
    
    # At exact trigger, dynamicRatio = 0, should return minBoost
    # rateBoost = 1500 * 12000 // 10000 = 1800
    assert credit_engine.getDynamicBorrowRate(1500) == 3300


def test_precision_with_small_values(
    setupDynamicRate,
    credit_engine,
):
    """Small precision values that might round to zero"""
    setupDynamicRate(
        _weightedRatio=6000,
        _dangerTrigger=6000,
        _numBlocksInDanger=1,
        _increasePerDangerBlock=1,
        _minDynamicRateBoost=0,
        _maxDynamicRateBoost=0,
    )
    
    # dangerBoost = (1 * 1) * 10000 // 1000000 = 0 (rounds down)
    assert credit_engine.getDynamicBorrowRate(1000) == 1000


def test_very_high_weighted_ratio_calculation(
    setupDynamicRate,
    credit_engine,
    mock_curve_prices,
    _test,
):
    """Very high weightedRatio (150%) produces extreme multipliers"""
    setupDynamicRate(
        _minDynamicRateBoost=10000,  # 100%
        _maxDynamicRateBoost=20000,  # 200%
        _dangerTrigger=6000,         # 60%
    )
    
    # Set 150% ratio (above 100%)
    mock_curve_prices.setMockGreenPoolData(15000, 6000, 0)
    
    # dynamicRatio = (15000-6000)*10000//(10000-6000) = 22500 (225%)
    # The contract doesn't cap this, so extreme multipliers are possible
    # rateMultiplier = 10000 + 22500*10000//10000 = 10000 + 22500 = 32500 (325%)
    # rateBoost = 1000 * 32500 // 10000 = 3250
    # Expected total: 1000 + 3250 = 4250
    _test(4250, credit_engine.getDynamicBorrowRate(1000))


#########################
# Realistic Scenarios  #
#########################


def test_healthy_pool_no_boost(
    setupDynamicRate,
    credit_engine,
):
    """Healthy pool below danger trigger gets no boost"""
    setupDynamicRate(
        _weightedRatio=4000,   # 40% - healthy
        _dangerTrigger=7000,   # 70% danger trigger
        _numBlocksInDanger=0,
    )
    
    assert credit_engine.getDynamicBorrowRate(500) == 500


def test_moderate_stress_moderate_boost(
    setupDynamicRate,
    credit_engine,
    _test,
):
    """Moderate pool stress gets moderate boost"""
    setupDynamicRate(
        _minDynamicRateBoost=10000,  # 100%
        _maxDynamicRateBoost=20000,  # 200%
        _weightedRatio=8000,         # 80%
        _dangerTrigger=6000,         # 60%
        _numBlocksInDanger=100,      # Round number
        _increasePerDangerBlock=50,  # Clean calculation
    )
    
    # Clean calculation:
    # dynamicRatio = (8000-6000)*10000//(10000-6000) = 5000 (50%)
    # rateMultiplier = 10000 + 5000*10000//10000 = 10000 + 5000 = 15000 (150%)
    # rateBoost = 1000 * 15000 // 10000 = 1500
    # dangerBoost = (50 * 100) * 10000 // 1000000 = 50
    # Expected total: 1000 + 1500 + 50 = 2550
    _test(2550, credit_engine.getDynamicBorrowRate(1000))


def test_severe_stress_high_boost_with_capping(
    setupDynamicRate,
    credit_engine,
):
    """Severe pool stress gets high boost but is capped"""
    setupDynamicRate(
        _minDynamicRateBoost=30000,  # 300%
        _maxDynamicRateBoost=50000,  # 500%
        _maxBorrowRate=8000,         # Cap at 80%
        _weightedRatio=9000,         # 90% - severe stress
        _dangerTrigger=6000,         # 60% trigger
        _numBlocksInDanger=500,      # Round number
        _increasePerDangerBlock=200, # High increase
    )
    
    # This would produce very high rates but gets capped at 8000
    # dynamicRatio = (9000-6000)*10000//(10000-6000) = 7500 (75%)
    # rateMultiplier = 30000 + 7500*20000//10000 = 30000 + 15000 = 45000 (450%)
    # rateBoost = 1000 * 45000 // 10000 = 4500
    # dangerBoost = (200 * 500) * 10000 // 1000000 = 1000
    # totalRate = 1000 + 4500 + 1000 = 6500, but capped at 8000
    # Since 6500 < 8000, no capping occurs - let me fix this
    
    # To ensure capping, let me set a very low cap:
    setupDynamicRate(
        _minDynamicRateBoost=30000,  # 300%
        _maxDynamicRateBoost=50000,  # 500%
        _maxBorrowRate=5000,         # Very low cap
        _weightedRatio=9000,         # 90%
        _dangerTrigger=6000,         # 60%
        _numBlocksInDanger=500,      # Round number
        _increasePerDangerBlock=200, # High increase
    )
    
    # Calculated rate would be 6500 but capped at 5000
    assert credit_engine.getDynamicBorrowRate(1000) == 5000
