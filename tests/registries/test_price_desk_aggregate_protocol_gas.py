from dataclasses import dataclass

import boa
import pytest

from conf_utils import clear_transient_storage, filter_logs
from constants import (
    BLUE_CHIP_PROTOCOL_MORPHO_V2,
    EIGHTEEN_DECIMALS,
    ZERO_ADDRESS,
)


ASSET_COUNT = 9
REGISTERED_SOURCE_COUNT = 3
ROBINHOOD_MAX_TX_GAS = 32_000_000
PRICE_SOURCE_SELECTOR = bytes.fromhex("abe4ffb4")


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


@dataclass(frozen=True)
class AggregateScenario:
    desk: object
    assets: tuple
    sources: tuple
    source_names: tuple[str, ...]
    priority_source_ids: tuple[int, ...]
    nested_source: object
    borrower: object


def _register_source(desk, source, deployer, description):
    assert desk.startAddNewAddressToRegistry(source, description, sender=deployer)
    return desk.confirmNewAddressToRegistry(source, sender=deployer)


def _count_calls(computation, address, selector):
    expected = bytes.fromhex(str(address)[2:])
    return sum(
        child.msg.code_address == expected and bytes(child.msg.data[:4]) == selector
        for child in computation.children
    ) + sum(
        _count_calls(child, address, selector) for child in computation.children
    )


def _install_price_desk(ripe_hq, governance, deploy3r, sources):
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
    boa.env.time_travel(blocks=ripe_hq.registryChangeTimeLock() + 1)
    assert ripe_hq.confirmAddressUpdateToRegistry(
        7,
        sender=governance.address,
    )
    assert ripe_hq.getAddr(7) == desk.address
    assert desk.numAddrs() - 1 == REGISTERED_SOURCE_COUNT
    return desk


def _configure_chainlink_feeds(
    chainlink,
    governance,
    feed,
    assets,
):
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
    boa.env.time_travel(blocks=chainlink.actionTimeLock() + 1)
    for asset in assets:
        assert chainlink.confirmNewPriceFeed(asset, sender=governance.address)


def _configure_bluechip_source(
    ripe_hq,
    deploy3r,
    teller,
    underlying,
    holder,
):
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


def _build_scenario(
    topology,
    operation,
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
    switchboard_bravo,
    mock_chainlink_feed_one,
    setGeneralConfig,
    setGeneralDebtConfig,
    setAssetConfig,
    createDebtTerms,
    performDeposit,
):
    direct_assets = tuple(
        boa.load(
            "contracts/mock/MockErc20.vy",
            whale,
            f"Aggregate Asset {index}",
            f"AGG{index}",
            18,
            10_000,
            name=f"aggregate_protocol_asset_{index}",
        )
        for index in range(1, ASSET_COUNT)
    )
    bluechip, nested_asset = _configure_bluechip_source(
        ripe_hq,
        deploy3r,
        teller,
        direct_assets[0],
        whale,
    )

    source_rows = (
        ("ChainlinkPrices", chainlink),
        ("CurvePrices", curve_prices),
        ("BlueChipYieldPrices", bluechip),
    )
    if topology == "intended":
        priorities = [1, 2]
    else:
        priorities = [2, 1]

    desk = _install_price_desk(
        ripe_hq,
        governance,
        deploy3r,
        source_rows,
    )
    mission_control.setPriorityPriceSourceIds(
        priorities,
        sender=switchboard_alpha.address,
    )
    assert tuple(mission_control.getPriorityPriceSourceIds()) == tuple(priorities)

    _configure_chainlink_feeds(
        chainlink,
        governance,
        mock_chainlink_feed_one,
        direct_assets,
    )
    _fill_bluechip_ring(bluechip, nested_asset, deploy3r, teller)
    assert desk.getPrice(nested_asset, True) == EIGHTEEN_DECIMALS

    setGeneralConfig(
        _perUserMaxVaults=5,
        _perUserMaxAssetsPerVault=15,
        _priceStaleTime=0,
    )
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=70_00,
        _liqThreshold=80_00,
        _liqFee=0,
        _borrowRate=0,
    )
    assets = (*direct_assets, nested_asset)
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
        performDeposit(
            bob,
            100 * EIGHTEEN_DECIMALS,
            asset,
            whale,
            simple_erc20_vault,
        )

    assert simple_erc20_vault.numUserAssets(bob) - 1 == ASSET_COUNT
    teller.borrow(400 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    return AggregateScenario(
        desk=desk,
        assets=assets,
        sources=tuple(source for _, source in source_rows),
        source_names=tuple(name for name, _ in source_rows),
        priority_source_ids=tuple(priorities),
        nested_source=bluechip,
        borrower=bob,
    )


def _measurement_metadata(scenario, computation):
    source_calls = tuple(
        _count_calls(computation, source.address, PRICE_SOURCE_SELECTOR)
        for source in scenario.sources
    )
    nested_selector = bytes(
        scenario.desk.getPrice.prepare_calldata(scenario.assets[0], True)[:4]
    )
    nested_calls = _count_calls(
        computation,
        scenario.desk.address,
        nested_selector,
    )
    traversed_sources = sum(count != 0 for count in source_calls)
    assert traversed_sources > 1
    assert source_calls[-1] > 0
    assert nested_calls > 0
    return source_calls, nested_calls, traversed_sources


@pytest.mark.gas
@pytest.mark.parametrize("topology", ("intended", "conservative"))
@pytest.mark.parametrize("operation", ("valuation", "liquidation", "deleverage"))
def test_aggregate_protocol_gas(
    topology,
    operation,
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
    switchboard_bravo,
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
        switchboard_bravo,
        mock_chainlink_feed_one,
        setGeneralConfig,
        setGeneralDebtConfig,
        setAssetConfig,
        createDebtTerms,
        performDeposit,
    )

    expected_collateral = ASSET_COUNT * 100 * EIGHTEEN_DECIMALS
    clear_transient_storage()
    if operation == "valuation":
        terms = credit_engine.getUserBorrowTerms(
            scenario.borrower,
            True,
            gas=ROBINHOOD_MAX_TX_GAS,
        )
        computation = credit_engine._computation
        assert terms.collateralVal == expected_collateral
        assert terms.totalMaxDebt == expected_collateral // 2
    elif operation == "liquidation":
        mock_chainlink_feed_one.setMockData(40_000_000)
        assert credit_engine.canLiquidateUser(scenario.borrower)
        clear_transient_storage()
        teller.liquidateUser(
            scenario.borrower,
            False,
            sender=sally,
            gas=ROBINHOOD_MAX_TX_GAS,
        )
        computation = teller._computation
        liquidation_logs = filter_logs(teller, "LiquidateUser")
        auction_logs = filter_logs(teller, "FungibleAuctionUpdated")
        assert len(liquidation_logs) == 1
        assert liquidation_logs[0].numAuctionsStarted == ASSET_COUNT
        assert len(auction_logs) == ASSET_COUNT
        assert ledger.userDebt(scenario.borrower).inLiquidation
        assert ledger.hasFungibleAuctions(scenario.borrower)
    else:
        debt_before = ledger.userDebt(scenario.borrower).amount
        balances_before = tuple(
            asset.balanceOf(endaoment_funds) for asset in scenario.assets
        )
        repaid = teller.deleverageManyUsers(
            [(scenario.borrower, 0)],
            sender=switchboard_alpha.address,
            gas=ROBINHOOD_MAX_TX_GAS,
        )
        computation = teller._computation
        balances_after = tuple(
            asset.balanceOf(endaoment_funds) for asset in scenario.assets
        )
        assert repaid == debt_before > 0
        assert ledger.userDebt(scenario.borrower).amount == 0
        assert any(after > before for before, after in zip(balances_before, balances_after))
        assert filter_logs(teller, "EndaomentTransferDuringDeleverage")
        assert len(filter_logs(teller, "DeleverageUser")) == 1

    gas_used = computation.get_gas_used()
    source_calls, nested_calls, traversed_sources = _measurement_metadata(
        scenario,
        computation,
    )
    assert 0 < gas_used < ROBINHOOD_MAX_TX_GAS
    print(
        "DER_T01_GAS",
        f"topology={topology}",
        f"operation={operation}",
        f"gas={gas_used}",
        f"assets={ASSET_COUNT}",
        f"registered_sources={REGISTERED_SOURCE_COUNT}",
        f"traversed_sources={traversed_sources}",
        f"source_order={scenario.source_names}",
        f"priority_source_ids={scenario.priority_source_ids}",
        f"source_calls={source_calls}",
        f"price_calls={sum(source_calls)}",
        f"nested_calls={nested_calls}",
        f"outer_budget={ROBINHOOD_MAX_TX_GAS}",
        f"margin={ROBINHOOD_MAX_TX_GAS - gas_used}",
        "transient_storage_cleared=true",
    )
