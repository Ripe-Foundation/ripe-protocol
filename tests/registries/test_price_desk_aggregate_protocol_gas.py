from dataclasses import dataclass

import boa
import pytest

from conf_utils import advance_timelock_blocks, clear_transient_storage, filter_logs
from constants import (
    BLUE_CHIP_PROTOCOL_MORPHO_V2,
    EIGHTEEN_DECIMALS,
    ZERO_ADDRESS,
)
from registries.price_desk_aggregate_qualification import (
    NESTED_PRICE_SELECTOR,
    PRICE_SOURCE_SELECTOR,
    QUALIFIED_BORROWER_ASSET_COUNT,
    QUALIFIED_PRICE_DESK_SOURCE_COUNT,
    QUALIFIED_PRICE_SOURCE_PRICE_GAS_STIPEND,
    QUALIFIED_SATURATED_DELEVERAGE_BATCH_SIZE,
    QUALIFIED_SATURATED_LIQUIDATION_BATCH_SIZE,
    ROBINHOOD_MAX_TX_GAS,
    ROBINHOOD_PRICE_STALE_TIME,
)


MORPHO_V2_COLLATERAL_SOURCE = """# @version 0.4.3

event Transfer:
    sender: indexed(address)
    receiver: indexed(address)
    value: uint256

event Approval:
    owner: indexed(address)
    spender: indexed(address)
    value: uint256

asset: public(address)
decimals: public(uint8)
balanceOf: public(HashMap[address, uint256])
allowance: public(HashMap[address, HashMap[address, uint256]])
totalSupply: public(uint256)

@deploy
def __init__(_asset: address, _holder: address, _supply: uint256):
    self.asset = _asset
    self.decimals = 18
    self.balanceOf[_holder] = _supply
    self.totalSupply = _supply
    log Transfer(sender=empty(address), receiver=_holder, value=_supply)

@view
@external
def convertToAssets(_shares: uint256) -> uint256:
    return _shares

@external
def transfer(_receiver: address, _amount: uint256) -> bool:
    self.balanceOf[msg.sender] -= _amount
    self.balanceOf[_receiver] += _amount
    log Transfer(sender=msg.sender, receiver=_receiver, value=_amount)
    return True

@external
def transferFrom(_sender: address, _receiver: address, _amount: uint256) -> bool:
    self.allowance[_sender][msg.sender] -= _amount
    self.balanceOf[_sender] -= _amount
    self.balanceOf[_receiver] += _amount
    log Transfer(sender=_sender, receiver=_receiver, value=_amount)
    return True

@external
def approve(_spender: address, _amount: uint256) -> bool:
    self.allowance[msg.sender][_spender] = _amount
    log Approval(owner=msg.sender, spender=_spender, value=_amount)
    return True
"""


BOUNDED_PRICE_SOURCE = """# @version 0.4.3

BURN_ITERATIONS: constant(uint256) = 1_000_000

struct CurrentGreenPoolStatus:
    weightedRatio: uint256
    dangerTrigger: uint256
    numBlocksInDanger: uint256

shouldExhaust: public(bool)
healthyAsset: public(address)
healthyPrice: public(uint256)
workIterations: public(uint256)

@external
def configure(_shouldExhaust: bool, _healthyAsset: address, _healthyPrice: uint256):
    self.shouldExhaust = _shouldExhaust
    self.healthyAsset = _healthyAsset
    self.healthyPrice = _healthyPrice
    self.workIterations = BURN_ITERATIONS if _shouldExhaust else 0

@view
@internal
def _burn() -> uint256:
    checksum: uint256 = 0
    for i: uint256 in range(BURN_ITERATIONS):
        if i == self.workIterations:
            break
        checksum = unsafe_add(checksum, i)
    return checksum

@view
@external
def getPriceAndHasFeed(
    _asset: address,
    _staleTime: uint256,
    _priceDesk: address,
) -> (uint256, bool):
    checksum: uint256 = self._burn()
    if self.shouldExhaust:
        assert checksum == max_value(uint256)
    if self.healthyPrice != 0 and (
        self.healthyAsset == empty(address) or _asset == self.healthyAsset
    ):
        return self.healthyPrice, True
    return 0, False

@view
@external
def hasPriceFeed(_asset: address) -> bool:
    return self.healthyPrice != 0 and (
        self.healthyAsset == empty(address) or _asset == self.healthyAsset
    )

@external
def addPriceSnapshot(_asset: address) -> bool:
    return True

# Teller and CreditEngine resolve registry ID 2 as CurvePrices during account
# updates. This source preserves their required surfaces while saturating only
# PriceDesk's bounded price call.
@external
def addGreenRefPoolSnapshot() -> bool:
    return True

@view
@external
def getCurrentGreenPoolStatus() -> CurrentGreenPoolStatus:
    return CurrentGreenPoolStatus(
        weightedRatio=0,
        dangerTrigger=0,
        numBlocksInDanger=0,
    )
"""


SINGLE_USER_GAS_REGRESSION_BUDGETS = {
    ("intended_prompt", "valuation"): 250_000,
    ("prompt_reordered", "valuation"): 300_000,
    ("stipend_saturated", "valuation"): 6_000_000,
    ("intended_prompt", "liquidation"): 3_000_000,
    ("prompt_reordered", "liquidation"): 3_000_000,
    ("stipend_saturated", "liquidation"): 14_000_000,
    ("intended_prompt", "deleverage"): 1_000_000,
    ("prompt_reordered", "deleverage"): 1_000_000,
    ("stipend_saturated", "deleverage"): 12_000_000,
}

BATCH_GAS_REGRESSION_BUDGETS = {
    ("liquidation", QUALIFIED_SATURATED_LIQUIDATION_BATCH_SIZE): 28_000_000,
    ("deleverage", QUALIFIED_SATURATED_DELEVERAGE_BATCH_SIZE): 31_000_000,
}


@dataclass(frozen=True)
class AggregateScenario:
    desk: object
    assets: tuple
    sources: tuple
    source_names: tuple[str, ...]
    priority_source_ids: tuple[int, ...]
    borrowers: tuple
    final_position_asset: object
    has_nested_lookup: bool
    all_sources_per_lookup: bool


def _register_source(desk, source, deployer, description):
    assert desk.startAddNewAddressToRegistry(source, description, sender=deployer)
    return desk.confirmNewAddressToRegistry(source, sender=deployer)


def _count_calls(computation, address, selector):
    return len(_matching_calls(computation, address, selector))


def _matching_calls(computation, address, selector):
    expected = bytes.fromhex(str(address)[2:])
    direct_matches = tuple(
        child
        for child in computation.children
        if child.msg.code_address == expected
        and bytes(child.msg.data[:4]) == selector
    )
    return direct_matches + sum(
        (_matching_calls(child, address, selector)
        for child in computation.children),
        (),
    )


def _has_error_type(computation, error_type_name):
    # The pinned Boa/py-evm stack exposes the child error class through private
    # `_error`; this mirrors the documented coupling in assert_reverted_call.
    # Revisit this trace helper whenever the test toolchain changes.
    return (
        computation.is_error
        and type(computation._error).__name__ == error_type_name
    ) or any(
        _has_error_type(child, error_type_name)
        for child in computation.children
    )


def _assert_qualified_revert(callback, resolved_message):
    try:
        callback()
    except boa.BoaError:
        return
    pytest.fail(resolved_message)


def _price_calls_for_asset(computation, address, asset):
    expected_address = bytes.fromhex(str(address)[2:])
    asset_address = getattr(asset, "address", asset)
    expected_asset = bytes.fromhex(str(asset_address)[2:]).rjust(32, b"\0")
    direct_matches = tuple(
        child
        for child in computation.children
        if child.msg.code_address == expected_address
        and bytes(child.msg.data[:4]) == PRICE_SOURCE_SELECTOR
        and bytes(child.msg.data[4:36]) == expected_asset
    )
    return direct_matches + sum(
        (_price_calls_for_asset(child, address, asset)
        for child in computation.children),
        (),
    )


def _install_price_desk(
    ripe_hq,
    governance,
    deploy3r,
    sources,
    expected_source_count=QUALIFIED_PRICE_DESK_SOURCE_COUNT,
):
    desk = boa.load(
        "contracts/registries/PriceDesk.vy",
        ripe_hq,
        deploy3r,
        "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        1,
        2,
        name="aggregate_protocol_price_desk",
    )
    for index, (name, source) in enumerate(sources, start=1):
        assert _register_source(desk, source, deploy3r, name) == index

    assert ripe_hq.startAddressUpdateToRegistry(
        7,
        desk,
        sender=governance.address,
    )
    advance_timelock_blocks(ripe_hq.registryChangeTimeLock() + 1)
    assert ripe_hq.confirmAddressUpdateToRegistry(
        7,
        sender=governance.address,
    )
    assert ripe_hq.getAddr(7) == desk.address
    assert desk.numAddrs() - 1 == expected_source_count
    return desk


def _set_priority_sources(mission_control, switchboard_alpha, priorities):
    mission_control.setPriorityPriceSourceIds(
        priorities,
        sender=switchboard_alpha.address,
    )
    assert tuple(mission_control.getPriorityPriceSourceIds()) == tuple(priorities)


def _configure_chainlink_feeds(chainlink, governance, feed, assets):
    feed.setMockData(10**8)
    for asset in assets:
        assert chainlink.addNewPriceFeed(
            asset,
            feed,
            0,
            False,
            False,
            sender=governance.address,
        )
    advance_timelock_blocks(chainlink.actionTimeLock() + 1)
    for asset in assets:
        assert chainlink.confirmNewPriceFeed(asset, sender=governance.address)
    feed.setMockData(10**8)


def _configure_bluechip_source(ripe_hq, deploy3r, underlying, holder):
    factory = boa.load(
        "contracts/mock/MockMorphoV2Factory.vy",
        name="aggregate_protocol_morpho_v2_factory",
    )
    vault = boa.loads(
        MORPHO_V2_COLLATERAL_SOURCE,
        underlying,
        holder,
        10_000 * EIGHTEEN_DECIMALS,
        name="aggregate_protocol_morpho_v2_collateral",
    )
    factory.setVault(vault, True)
    bluechip = boa.load(
        "contracts/priceSources/BlueChipYieldPrices.vy",
        ripe_hq,
        deploy3r,
        1,
        2,
        [ZERO_ADDRESS, ZERO_ADDRESS],
        [ZERO_ADDRESS, ZERO_ADDRESS],
        ZERO_ADDRESS,
        ZERO_ADDRESS,
        ZERO_ADDRESS,
        ZERO_ADDRESS,
        factory,
        name="aggregate_protocol_bluechip_morpho_v2",
    )
    return bluechip, vault


def _fill_bluechip_ring(bluechip, vault, deploy3r, teller):
    assert bluechip.addNewPriceFeed(
        vault,
        BLUE_CHIP_PROTOCOL_MORPHO_V2,
        0,
        25,
        0,
        0,
        sender=deploy3r,
    )
    assert bluechip.confirmNewPriceFeed(vault, sender=deploy3r)
    for _ in range(24):
        boa.env.time_travel(seconds=1)
        assert bluechip.addPriceSnapshot(vault, sender=teller.address)
    config = bluechip.priceConfigs(vault)
    assert config.protocol == BLUE_CHIP_PROTOCOL_MORPHO_V2
    assert config.maxNumSnapshots == 25
    assert config.nextIndex == 0


def _bounded_source(
    name,
    should_exhaust,
    healthy_asset=ZERO_ADDRESS,
    healthy_price=None,
):
    source = boa.loads(BOUNDED_PRICE_SOURCE, name=name)
    if healthy_price is None:
        healthy_price = (
            EIGHTEEN_DECIMALS if healthy_asset != ZERO_ADDRESS else 0
        )
    source.configure(should_exhaust, healthy_asset, healthy_price)
    return source


def _deploy_direct_assets(whale, count):
    return tuple(
        boa.load(
            "contracts/mock/MockErc20.vy",
            whale,
            f"Aggregate Asset {index}",
            f"AGG{index}",
            18,
            10_000,
            name=f"aggregate_protocol_asset_{index}",
        )
        for index in range(1, count + 1)
    )


def _configure_protocol_assets(
    operation,
    assets,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
):
    setGeneralConfig(
        _perUserMaxVaults=5,
        _perUserMaxAssetsPerVault=15,
        _priceStaleTime=ROBINHOOD_PRICE_STALE_TIME,
    )
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=70_00,
        _liqThreshold=80_00,
        _liqFee=0,
        _borrowRate=0,
    )
    for asset in assets:
        setAssetConfig(
            asset,
            _vaultIds=[3],
            _debtTerms=debt_terms,
            _shouldBurnAsPayment=False,
            _shouldTransferToEndaoment=operation == "deleverage",
            _shouldSwapInStabPools=False,
            _shouldAuctionInstantly=operation == "liquidation",
        )


def _seed_borrowers(
    borrowers,
    assets,
    whale,
    teller,
    simple_erc20_vault,
    performDeposit,
):
    for borrower in borrowers:
        for asset in assets:
            performDeposit(
                borrower,
                100 * EIGHTEEN_DECIMALS,
                asset,
                whale,
                simple_erc20_vault,
            )
        assert (
            simple_erc20_vault.numUserAssets(borrower) - 1
            == QUALIFIED_BORROWER_ASSET_COUNT
        )
        teller.borrow(400 * EIGHTEEN_DECIMALS, borrower, False, sender=borrower)


def _build_scenario(
    topology,
    operation,
    user_count,
    ripe_hq,
    governance,
    deploy3r,
    whale,
    bob,
    teller,
    simple_erc20_vault,
    chainlink,
    curve_prices,
    mission_control,
    switchboard_alpha,
    mock_chainlink_feed_one,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    performDeposit,
):
    # Feed admission happens before the broader protocol configuration below.
    # Bind the production global policy first so stored zero means inheritance
    # throughout setup as well as on the measured aggregate path.
    setGeneralConfig(_priceStaleTime=ROBINHOOD_PRICE_STALE_TIME)

    borrowers = (bob,) + tuple(
        boa.env.generate_address() for _ in range(user_count - 1)
    )

    if topology == "stipend_saturated":
        assets = _deploy_direct_assets(whale, QUALIFIED_BORROWER_ASSET_COUNT)
        first_bounded = _bounded_source(
            "aggregate_protocol_bounded_source_1",
            False,
        )
        curve_compatible_bounded = _bounded_source(
            "aggregate_protocol_bounded_curve_source_2",
            False,
        )
        healthy_all_asset_fallback = _bounded_source(
            "aggregate_protocol_healthy_all_asset_source_3",
            False,
            healthy_price=EIGHTEEN_DECIMALS,
        )
        source_rows = (
            ("BoundedExhaustingSource", first_bounded),
            ("BoundedExhaustingCurveCompatible", curve_compatible_bounded),
            ("HealthyAllAssetFallback", healthy_all_asset_fallback),
        )
        priorities = [1, 2]
        final_position_asset = assets[0]
        has_nested_lookup = False
        all_sources_per_lookup = True
    else:
        direct_assets = _deploy_direct_assets(
            whale,
            QUALIFIED_BORROWER_ASSET_COUNT - 1,
        )
        bluechip, nested_asset = _configure_bluechip_source(
            ripe_hq,
            deploy3r,
            direct_assets[0],
            whale,
        )
        assets = (*direct_assets, nested_asset)
        source_rows = (
            ("ChainlinkPrices", chainlink),
            ("CurvePrices", curve_prices),
            ("BlueChipYieldPrices", bluechip),
        )
        priorities = [1, 2] if topology == "intended_prompt" else [2, 1]
        final_position_asset = nested_asset
        has_nested_lookup = True
        all_sources_per_lookup = False
        _configure_chainlink_feeds(
            chainlink,
            governance,
            mock_chainlink_feed_one,
            direct_assets,
        )

    desk = _install_price_desk(
        ripe_hq,
        governance,
        deploy3r,
        source_rows,
    )
    for asset in assets:
        desk.syncTokenScale(asset, sender=deploy3r)
    _set_priority_sources(mission_control, switchboard_alpha, priorities)

    if topology != "stipend_saturated":
        _fill_bluechip_ring(bluechip, nested_asset, deploy3r, teller)
        assert desk.getPrice(nested_asset, True) == EIGHTEEN_DECIMALS

    _configure_protocol_assets(
        operation,
        assets,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
    )
    # Registry and BlueChip setup advance time past the one-day stale window.
    # Refresh the mock observation after setup so the measured path exercises
    # staleness checks with a valid Robinhood-style timestamp.
    if topology != "stipend_saturated":
        mock_chainlink_feed_one.setMockData(10**8)
    else:
        for asset in assets:
            assert healthy_all_asset_fallback.getPriceAndHasFeed(
                asset,
                ROBINHOOD_PRICE_STALE_TIME,
                desk,
            ) == (EIGHTEEN_DECIMALS, True)
            assert desk.getPrice(asset, True) == EIGHTEEN_DECIMALS
    _seed_borrowers(
        borrowers,
        assets,
        whale,
        teller,
        simple_erc20_vault,
        performDeposit,
    )
    if topology == "stipend_saturated":
        # Seed through the healthy registry, then saturate only the measured
        # operation. Setup transactions are not part of the qualified path.
        first_bounded.configure(True, ZERO_ADDRESS, 0)
        curve_compatible_bounded.configure(True, ZERO_ADDRESS, 0)
    return AggregateScenario(
        desk=desk,
        assets=assets,
        sources=tuple(source for _, source in source_rows),
        source_names=tuple(name for name, _ in source_rows),
        priority_source_ids=tuple(priorities),
        borrowers=borrowers,
        final_position_asset=final_position_asset,
        has_nested_lookup=has_nested_lookup,
        all_sources_per_lookup=all_sources_per_lookup,
    )


def _measurement_metadata(scenario, computation):
    source_calls = tuple(
        _count_calls(computation, source.address, PRICE_SOURCE_SELECTOR)
        for source in scenario.sources
    )
    per_asset_source_computations = tuple(
        tuple(
            _price_calls_for_asset(computation, source.address, asset)
            for source in scenario.sources
        )
        for asset in scenario.assets
    )
    per_asset_source_calls = tuple(
        tuple(len(calls) for calls in asset_calls)
        for asset_calls in per_asset_source_computations
    )
    sources_reached = sum(count != 0 for count in source_calls)
    nested_calls = _count_calls(
        computation,
        scenario.desk.address,
        NESTED_PRICE_SELECTOR,
    )

    assert sources_reached == len(scenario.sources)
    saturated_oog_calls = 0
    if scenario.all_sources_per_lookup:
        assert all(
            all(count > 0 for count in asset_calls)
            for asset_calls in per_asset_source_calls
        )
        for asset_calls in per_asset_source_computations:
            for exhausting_source_calls in asset_calls[:2]:
                assert all(
                    call.msg.gas == QUALIFIED_PRICE_SOURCE_PRICE_GAS_STIPEND
                    and call.is_error
                    and _has_error_type(call, "OutOfGas")
                    for call in exhausting_source_calls
                )
                saturated_oog_calls += len(exhausting_source_calls)
            assert all(not call.is_error for call in asset_calls[2])
    else:
        final_asset_calls = per_asset_source_calls[
            scenario.assets.index(scenario.final_position_asset)
        ]
        assert all(count > 0 for count in final_asset_calls)
    if scenario.has_nested_lookup:
        assert nested_calls > 0
    else:
        assert nested_calls == 0
    return (
        source_calls,
        per_asset_source_calls,
        nested_calls,
        sources_reached,
        saturated_oog_calls,
    )


def _record_properties(request, **properties):
    request.node.user_properties.extend(properties.items())


@pytest.mark.gas
@pytest.mark.parametrize(
    "topology",
    ("intended_prompt", "prompt_reordered", "stipend_saturated"),
)
@pytest.mark.parametrize("operation", ("valuation", "liquidation", "deleverage"))
def test_aggregate_protocol_gas(
    topology,
    operation,
    request,
    ripe_hq,
    governance,
    deploy3r,
    whale,
    bob,
    sally,
    teller,
    ledger,
    credit_engine,
    endaoment_funds,
    simple_erc20_vault,
    chainlink,
    curve_prices,
    mission_control,
    switchboard_alpha,
    mock_chainlink_feed_one,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    performDeposit,
):
    scenario = _build_scenario(
        topology,
        operation,
        1,
        ripe_hq,
        governance,
        deploy3r,
        whale,
        bob,
        teller,
        simple_erc20_vault,
        chainlink,
        curve_prices,
        mission_control,
        switchboard_alpha,
        mock_chainlink_feed_one,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
        performDeposit,
    )

    borrower = scenario.borrowers[0]
    expected_collateral = (
        QUALIFIED_BORROWER_ASSET_COUNT * 100 * EIGHTEEN_DECIMALS
    )
    clear_transient_storage()
    if operation == "valuation":
        terms = credit_engine.getUserBorrowTerms(
            borrower,
            True,
            gas=ROBINHOOD_MAX_TX_GAS,
        )
        computation = credit_engine._computation
        assert terms.collateralVal == expected_collateral
        assert terms.totalMaxDebt == expected_collateral // 2
    elif operation == "liquidation":
        if topology == "stipend_saturated":
            scenario.sources[2].configure(
                False,
                ZERO_ADDRESS,
                40 * EIGHTEEN_DECIMALS // 100,
            )
        else:
            mock_chainlink_feed_one.setMockData(40_000_000)
        assert credit_engine.canLiquidateUser(borrower)
        clear_transient_storage()
        teller.liquidateUser(
            borrower,
            False,
            sender=sally,
            gas=ROBINHOOD_MAX_TX_GAS,
        )
        computation = teller._computation
        liquidation_logs = filter_logs(teller, "LiquidateUser")
        auction_logs = filter_logs(teller, "FungibleAuctionUpdated")
        assert len(liquidation_logs) == 1
        assert liquidation_logs[0].numAuctionsStarted == QUALIFIED_BORROWER_ASSET_COUNT
        assert len(auction_logs) == QUALIFIED_BORROWER_ASSET_COUNT
        assert ledger.userDebt(borrower).inLiquidation
        assert ledger.hasFungibleAuctions(borrower)
    else:
        debt_before = ledger.userDebt(borrower).amount
        balances_before = tuple(
            asset.balanceOf(endaoment_funds) for asset in scenario.assets
        )
        repaid = teller.deleverageManyUsers(
            [(borrower, 0)],
            sender=switchboard_alpha.address,
            gas=ROBINHOOD_MAX_TX_GAS,
        )
        computation = teller._computation
        balances_after = tuple(
            asset.balanceOf(endaoment_funds) for asset in scenario.assets
        )
        assert repaid == debt_before > 0
        assert ledger.userDebt(borrower).amount == 0
        assert any(
            after > before
            for before, after in zip(balances_before, balances_after)
        )
        assert filter_logs(teller, "EndaomentTransferDuringDeleverage")
        assert len(filter_logs(teller, "DeleverageUser")) == 1

    gas_used = computation.get_gas_used()
    (
        source_calls,
        per_asset_calls,
        nested_calls,
        sources_reached,
        saturated_oog_calls,
    ) = (
        _measurement_metadata(scenario, computation)
    )
    regression_budget = SINGLE_USER_GAS_REGRESSION_BUDGETS[(topology, operation)]
    assert 0 < gas_used <= regression_budget < ROBINHOOD_MAX_TX_GAS
    _record_properties(
        request,
        gas_used=gas_used,
        gas_regression_budget=regression_budget,
        borrower_assets=QUALIFIED_BORROWER_ASSET_COUNT,
        registered_sources=QUALIFIED_PRICE_DESK_SOURCE_COUNT,
        nested_calls=nested_calls,
        saturated_oog_calls=saturated_oog_calls,
    )
    print(
        "DER_T01_GAS",
        f"topology={topology}",
        f"operation={operation}",
        f"gas={gas_used}",
        f"gas_regression_budget={regression_budget}",
        f"assets={QUALIFIED_BORROWER_ASSET_COUNT}",
        f"registered_sources={QUALIFIED_PRICE_DESK_SOURCE_COUNT}",
        f"sources_reached_in_transaction={sources_reached}",
        f"all_sources_per_lookup={scenario.all_sources_per_lookup}",
        f"source_order={scenario.source_names}",
        f"priority_source_ids={scenario.priority_source_ids}",
        f"source_calls={source_calls}",
        f"first_asset_source_calls={per_asset_calls[0]}",
        f"price_calls={sum(source_calls)}",
        f"nested_calls={nested_calls}",
        f"saturated_oog_calls={saturated_oog_calls}",
        f"stale_time={ROBINHOOD_PRICE_STALE_TIME}",
        f"outer_budget={ROBINHOOD_MAX_TX_GAS}",
        f"margin={ROBINHOOD_MAX_TX_GAS - gas_used}",
        "transient_storage_cleared=true",
    )


@pytest.mark.gas
@pytest.mark.parametrize(
    ("operation", "user_count", "should_succeed"),
    (
        (
            "liquidation",
            QUALIFIED_SATURATED_LIQUIDATION_BATCH_SIZE,
            True,
        ),
        (
            "liquidation",
            QUALIFIED_SATURATED_LIQUIDATION_BATCH_SIZE + 1,
            False,
        ),
        (
            "deleverage",
            QUALIFIED_SATURATED_DELEVERAGE_BATCH_SIZE,
            True,
        ),
        (
            "deleverage",
            QUALIFIED_SATURATED_DELEVERAGE_BATCH_SIZE + 1,
            False,
        ),
    ),
)
def test_stipend_saturated_batch_envelope(
    operation,
    user_count,
    should_succeed,
    request,
    ripe_hq,
    governance,
    deploy3r,
    whale,
    bob,
    sally,
    teller,
    ledger,
    simple_erc20_vault,
    chainlink,
    curve_prices,
    mission_control,
    switchboard_alpha,
    mock_chainlink_feed_one,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    performDeposit,
):
    scenario = _build_scenario(
        "stipend_saturated",
        operation,
        user_count,
        ripe_hq,
        governance,
        deploy3r,
        whale,
        bob,
        teller,
        simple_erc20_vault,
        chainlink,
        curve_prices,
        mission_control,
        switchboard_alpha,
        mock_chainlink_feed_one,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
        performDeposit,
    )
    debts_before = tuple(
        ledger.userDebt(borrower).amount for borrower in scenario.borrowers
    )
    assert all(debt == 400 * EIGHTEEN_DECIMALS for debt in debts_before)

    if operation == "liquidation":
        scenario.sources[2].configure(
            False,
            ZERO_ADDRESS,
            40 * EIGHTEEN_DECIMALS // 100,
        )
        assert all(
            ledger.userDebt(borrower).amount > 0 for borrower in scenario.borrowers
        )

    clear_transient_storage()
    if should_succeed:
        if operation == "liquidation":
            teller.liquidateManyUsers(
                list(scenario.borrowers),
                False,
                sender=sally,
                gas=ROBINHOOD_MAX_TX_GAS,
            )
        else:
            teller.deleverageManyUsers(
                [(borrower, 0) for borrower in scenario.borrowers],
                sender=switchboard_alpha.address,
                gas=ROBINHOOD_MAX_TX_GAS,
            )
        computation = teller._computation
        gas_used = computation.get_gas_used()
        regression_budget = BATCH_GAS_REGRESSION_BUDGETS[(operation, user_count)]
        assert 0 < gas_used <= regression_budget < ROBINHOOD_MAX_TX_GAS
        _measurement_metadata(scenario, computation)

        if operation == "liquidation":
            assert len(filter_logs(teller, "LiquidateUser")) == user_count
            assert len(filter_logs(teller, "FungibleAuctionUpdated")) == (
                user_count * QUALIFIED_BORROWER_ASSET_COUNT
            )
            assert all(
                ledger.userDebt(borrower).inLiquidation
                for borrower in scenario.borrowers
            )
        else:
            assert len(filter_logs(teller, "DeleverageUser")) == user_count
            assert all(
                ledger.userDebt(borrower).amount == 0
                for borrower in scenario.borrowers
            )
        status = "success"
    else:
        if operation == "liquidation":
            _assert_qualified_revert(
                lambda: teller.liquidateManyUsers(
                    list(scenario.borrowers),
                    False,
                    sender=sally,
                    gas=ROBINHOOD_MAX_TX_GAS,
                ),
                "saturated liquidation batch boundary moved; rerun aggregate "
                "gas qualification before changing the operator limit",
            )
        else:
            _assert_qualified_revert(
                lambda: teller.deleverageManyUsers(
                    [(borrower, 0) for borrower in scenario.borrowers],
                    sender=switchboard_alpha.address,
                    gas=ROBINHOOD_MAX_TX_GAS,
                ),
                "saturated Deleverage batch boundary moved; rerun aggregate "
                "gas qualification before changing the operator limit",
            )
        computation = teller._computation
        gas_used = computation.get_gas_used()
        regression_budget = ROBINHOOD_MAX_TX_GAS
        # The OOG descendant is the primary boundary proof. This looser outer
        # floor only rejects unrelated early failures without coupling the test
        # to the current ~98.2% EIP-150 top-level gas report.
        assert _has_error_type(computation, "OutOfGas")
        assert gas_used >= ROBINHOOD_MAX_TX_GAS * 95 // 100
        assert tuple(
            ledger.userDebt(borrower).amount for borrower in scenario.borrowers
        ) == debts_before
        status = "outer_gas_limit_exceeded"

    _record_properties(
        request,
        gas_used=gas_used,
        batch_users=user_count,
        borrower_assets=QUALIFIED_BORROWER_ASSET_COUNT,
        registered_sources=QUALIFIED_PRICE_DESK_SOURCE_COUNT,
        status=status,
    )
    print(
        "DER_T01_BATCH_GAS",
        f"operation={operation}",
        f"users={user_count}",
        f"assets_per_user={QUALIFIED_BORROWER_ASSET_COUNT}",
        f"registered_sources={QUALIFIED_PRICE_DESK_SOURCE_COUNT}",
        "saturated_sources=2",
        f"gas={gas_used}",
        f"gas_regression_budget={regression_budget}",
        f"status={status}",
        f"outer_budget={ROBINHOOD_MAX_TX_GAS}",
        "transient_storage_cleared=true",
    )


@pytest.mark.gas
def test_nested_bluechip_is_starved_by_preceding_all_asset_stipend_exhaustion(
    request,
    ripe_hq,
    governance,
    deploy3r,
    whale,
    teller,
    mission_control,
    switchboard_alpha,
):
    underlying = _deploy_direct_assets(whale, 1)[0]
    bluechip, nested_asset = _configure_bluechip_source(
        ripe_hq,
        deploy3r,
        underlying,
        whale,
    )
    preceding_source = _bounded_source(
        "nested_preceding_source",
        False,
    )
    healthy_curve_compatible = _bounded_source(
        "nested_healthy_curve_fallback",
        False,
        underlying,
    )
    source_rows = (
        ("PrecedingBoundedSource", preceding_source),
        ("HealthyCurveCompatibleFallback", healthy_curve_compatible),
        ("BlueChipYieldPrices", bluechip),
    )
    desk = _install_price_desk(
        ripe_hq,
        governance,
        deploy3r,
        source_rows,
    )
    _set_priority_sources(mission_control, switchboard_alpha, [1, 2])
    _fill_bluechip_ring(bluechip, nested_asset, deploy3r, teller)
    assert desk.getPrice(underlying, True) == EIGHTEEN_DECIMALS
    assert desk.getPrice(nested_asset, True) == EIGHTEEN_DECIMALS

    preceding_source.configure(True, ZERO_ADDRESS, 0)
    assert desk.getPrice(underlying, True, gas=3_000_000) == EIGHTEEN_DECIMALS

    clear_transient_storage()
    nested_price = desk.getPrice(nested_asset, False, gas=3_000_000)
    assert nested_price == 0, (
        "nested BlueChip stop condition changed or was resolved; rerun aggregate "
        "gas qualification and recalibrate the listing invariant"
    )
    computation = desk._computation
    gas_used = computation.get_gas_used()
    preceding_calls = _count_calls(
        computation,
        preceding_source.address,
        PRICE_SOURCE_SELECTOR,
    )
    bluechip_calls = _count_calls(
        computation,
        bluechip.address,
        PRICE_SOURCE_SELECTOR,
    )
    bluechip_computations = _matching_calls(
        computation,
        bluechip.address,
        PRICE_SOURCE_SELECTOR,
    )
    nested_calls = _count_calls(
        computation,
        desk.address,
        NESTED_PRICE_SELECTOR,
    )
    healthy_underlying_computations = _price_calls_for_asset(
        computation,
        healthy_curve_compatible.address,
        underlying,
    )
    healthy_underlying_calls = len(healthy_underlying_computations)
    healthy_underlying_successes = sum(
        not call.is_error for call in healthy_underlying_computations
    )
    assert preceding_calls == 2
    assert bluechip_calls == 1
    assert len(bluechip_computations) == 1
    assert bluechip_computations[0].is_error
    assert nested_calls == 1
    assert healthy_underlying_calls == 1
    assert healthy_underlying_successes == 1
    # If this exact fail-closed reason changes, the nested stop condition moved
    # or was resolved and aggregate-gas qualification must be rerun.
    with boa.reverts("has price config, no price"):
        desk.getPrice(nested_asset, True, gas=3_000_000)

    _record_properties(
        request,
        gas_used=gas_used,
        nested_price=0,
        preceding_saturated_calls=preceding_calls,
        nested_calls=nested_calls,
    )
    print(
        "DER_T01_NESTED_STOP_CONDITION",
        f"gas={gas_used}",
        "registered_sources=3",
        "preceding_saturated_sources=1",
        f"preceding_calls={preceding_calls}",
        f"bluechip_calls={bluechip_calls}",
        f"nested_calls={nested_calls}",
        f"healthy_underlying_calls={healthy_underlying_calls}",
        f"healthy_underlying_successes={healthy_underlying_successes}",
        "nested_price=0",
        "strict_price_reverts=true",
        "transient_storage_cleared=true",
    )
