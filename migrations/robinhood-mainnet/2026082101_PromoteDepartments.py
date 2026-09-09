"""Authenticate and promote the complete 2026082100 fresh generation.

This migration sends no governance transaction.  It succeeds only after the
Safe has activated all 19 RipeHq candidates.  The fresh child registries then
witness their own vault, switchboard, and price-source candidates.  All source,
compiler, ABI, constructor, runtime, registry identity, and slot checks finish
before the canonical manifest is changed once.
"""

from scripts.utils import log
from scripts.utils.migration import Migration, PromotionSpec

from config.robinhood_launch import (
    BOND_BOOSTER_MAX_BOOST_RATIO,
    BOND_BOOSTER_MAX_UNITS,
    BOND_BOOSTER_MIN_LOCK_DURATION,
    DELEVERAGE_BUFFER,
    DELEVERAGE_COOLDOWN,
    DELEVERAGE_DUST_BPS,
    DELEVERAGE_DUST_THRESHOLD,
    DELEVERAGE_FULL_PAYOFF_BUFFER,
    DELEVERAGE_MIN_BPS,
    DELEVERAGE_OVERAGE_BPS,
    DELEVERAGE_UNDERSCORE_SPREAD,
    HR_MAX_TIMELOCK,
    HR_MIN_TIMELOCK,
    LEDGER_ACTION_BLOCK_SOURCE,
    LOCAL_GOV_MAX_TIMELOCK,
    LOCAL_GOV_MIN_TIMELOCK,
    LOOTBOX_DEPOSIT_REWARD,
    LOOTBOX_MIN_SEND_INTERVAL,
    LOOTBOX_SEND_INTERVAL,
    LOOTBOX_YIELD_BONUS,
    PRICE_CHANGE_MAX_TIMELOCK,
    PRICE_CHANGE_MIN_TIMELOCK,
    PRICE_MAX_TIMELOCK,
    PRICE_MIN_TIMELOCK,
    PSM_MAX_INTERVAL_MINT,
    PSM_MAX_INTERVAL_REDEEM,
    PSM_MINT_FEE,
    PSM_NUM_BLOCKS_PER_INTERVAL,
    PSM_REDEEM_FEE,
    PSM_YIELD_LEGO_ID,
    PSM_YIELD_VAULT_TOKEN,
    REGISTRY_MAX_DELAY,
    REGISTRY_MIN_DELAY,
    RIPE_WETH_POOL,
    STALE_WINDOW_DEFAULT,
    STALE_WINDOW_MAX,
    STALE_WINDOW_MIN,
    SWITCHBOARD_MAX_TIMELOCK,
    SWITCHBOARD_MIN_TIMELOCK,
    ZERO_ADDRESS,
)


RIPE_HQ = "RipeHq"
CANDIDATE_SUFFIX = "Candidate2026082100"
LIVE_CURVE_ADDRESS_PROVIDER = "0x4574921eb950d3Fd5B01562162EC566Cb8bc3648"

HQ_ACTIVATED = (
    ("Ledger", 4),
    ("MissionControl", 5),
    ("Switchboard", 6),
    ("PriceDesk", 7),
    ("VaultBook", 8),
    ("AuctionHouse", 9),
    ("AuctionHouseNFT", 10),
    ("Boardroom", 11),
    ("BondRoom", 12),
    ("CreditEngine", 13),
    ("Endaoment", 14),
    ("HumanResources", 15),
    ("Lootbox", 16),
    ("Teller", 17),
    ("Deleverage", 18),
    ("CreditRedeem", 19),
    ("TellerUtils", 20),
    ("EndaomentFunds", 21),
    ("EndaomentPSM", 22),
)
SWITCHBOARD_CHILDREN = (
    ("SwitchboardAlpha", 1),
    ("SwitchboardBravo", 2),
    ("SwitchboardCharlie", 3),
    ("SwitchboardDelta", 4),
    ("SwitchboardEcho", 5),
)
PRICE_SOURCE_CHILDREN = (
    ("ChainlinkPrices", 1),
    ("CurvePrices", 2),
    ("UniswapV2Prices", 3),
)
VAULT_CHILDREN = (
    ("StabilityPool", 1),
    ("RipeGov", 2),
    ("SimpleErc20", 3),
)

CANONICAL_SOURCE_PATHS = {
    "DefaultsRobinhoodLive": "contracts/config/DefaultsRobinhoodLive.vy",
    "Ledger": "contracts/data/Ledger.vy",
    "MissionControl": "contracts/data/MissionControl.vy",
    "Switchboard": "contracts/registries/Switchboard.vy",
    "SwitchboardAlpha": "contracts/config/SwitchboardAlpha.vy",
    "SwitchboardBravo": "contracts/config/SwitchboardBravo.vy",
    "SwitchboardCharlie": "contracts/config/SwitchboardCharlie.vy",
    "SwitchboardDelta": "contracts/config/SwitchboardDelta.vy",
    "SwitchboardEcho": "contracts/config/SwitchboardEcho.vy",
    "PriceDesk": "contracts/registries/PriceDesk.vy",
    "ChainlinkPrices": "contracts/priceSources/ChainlinkPrices.vy",
    "CurvePrices": "contracts/priceSources/CurvePrices.vy",
    "UniswapV2Prices": "contracts/priceSources/UniswapV2Prices.vy",
    "VaultBook": "contracts/registries/VaultBook.vy",
    "StabilityPool": "contracts/vaults/StabilityPool.vy",
    "RipeGov": "contracts/vaults/RipeGov.vy",
    "SimpleErc20": "contracts/vaults/SimpleErc20.vy",
    "AuctionHouse": "contracts/core/AuctionHouse.vy",
    "AuctionHouseNFT": "contracts/core/AuctionHouseNFT.vy",
    "Boardroom": "contracts/core/Boardroom.vy",
    "BondBooster": "contracts/config/BondBooster.vy",
    "BondRoom": "contracts/core/BondRoom.vy",
    "CreditEngine": "contracts/core/CreditEngine.vy",
    "Endaoment": "contracts/core/Endaoment.vy",
    "HumanResources": "contracts/core/HumanResources.vy",
    "Lootbox": "contracts/core/Lootbox.vy",
    "Teller": "contracts/core/Teller.vy",
    "Deleverage": "contracts/core/Deleverage.vy",
    "CreditRedeem": "contracts/core/CreditRedeem.vy",
    "TellerUtils": "contracts/core/TellerUtils.vy",
    "EndaomentFunds": "contracts/core/EndaomentFunds.vy",
    "EndaomentPSM": "contracts/core/EndaomentPSM.vy",
}


def candidate_label(name):
    return f"{name}{CANDIDATE_SUFFIX}"


def _as_address(value):
    return str(getattr(value, "address", value)).lower()


def _assert_finalized_tree(migration, root_name, children):
    root = migration.get_contract(candidate_label(root_name))
    for name, reg_id in children:
        expected = migration.get_address(candidate_label(name))
        assert _as_address(root.getAddr(reg_id)) == _as_address(expected)
    assert int(root.registryChangeTimeLock()) == 0
    assert _as_address(root.governance()) == ZERO_ADDRESS
    return root


def _normalized(value):
    if isinstance(value, str) and value.startswith("0x") and len(value) == 42:
        return value.lower()
    if isinstance(value, (tuple, list)):
        return tuple(_normalized(item) for item in value)
    return value


def _assert_price_state_cloned(migration):
    active_chainlink = migration.get_contract("ChainlinkPrices")
    fresh_chainlink = migration.get_contract(candidate_label("ChainlinkPrices"))
    active_chainlink_assets = tuple(active_chainlink.getPricedAssets())
    fresh_chainlink_assets = tuple(fresh_chainlink.getPricedAssets())
    assert tuple(map(_as_address, fresh_chainlink_assets)) == tuple(
        map(_as_address, active_chainlink_assets)
    )
    for asset in active_chainlink_assets:
        assert _normalized(fresh_chainlink.feedConfig(asset)) == _normalized(
            active_chainlink.feedConfig(asset)
        )

    active_curve = migration.get_contract("CurvePrices")
    fresh_curve = migration.get_contract(candidate_label("CurvePrices"))
    active_curve_assets = tuple(active_curve.getPricedAssets())
    fresh_curve_assets = tuple(fresh_curve.getPricedAssets())
    assert tuple(map(_as_address, fresh_curve_assets)) == tuple(
        map(_as_address, active_curve_assets)
    )
    for asset in active_curve_assets:
        assert _normalized(fresh_curve.curveConfig(asset)) == _normalized(
            active_curve.curveConfig(asset)
        )
    assert _normalized(fresh_curve.greenRefPoolConfig()) == _normalized(
        active_curve.greenRefPoolConfig()
    )


def _spec(name, registry_name, registry, reg_id, expected_args):
    return PromotionSpec(
        canonical_name=name,
        expected_source_path=CANONICAL_SOURCE_PATHS[name],
        candidate_label=candidate_label(name),
        registry_name=registry_name,
        registry=registry,
        registry_id=reg_id,
        expected_constructor_args=expected_args,
    )


def migrate(migration: Migration):
    hq = migration.get_contract(RIPE_HQ)
    deployer = migration.account()
    contributor = migration.get_address("Contributor")
    defaults = migration.get_address(candidate_label("DefaultsRobinhoodLive"))
    bond_booster = migration.get_address(candidate_label("BondBooster"))
    active_price_desk = migration.get_contract("PriceDesk")
    active_chainlink = migration.get_contract("ChainlinkPrices")
    eth = active_price_desk.ETH()
    weth = active_chainlink.WETH()
    btc = active_chainlink.BTC()
    eth_feed = active_chainlink.feedConfig(eth)[0]
    btc_feed = active_chainlink.feedConfig(btc)[0]

    switchboard = _assert_finalized_tree(
        migration,
        "Switchboard",
        SWITCHBOARD_CHILDREN,
    )
    price_desk = _assert_finalized_tree(
        migration,
        "PriceDesk",
        PRICE_SOURCE_CHILDREN,
    )
    vault_book = _assert_finalized_tree(
        migration,
        "VaultBook",
        VAULT_CHILDREN,
    )

    for name in (
        *(item[0] for item in SWITCHBOARD_CHILDREN),
        "ChainlinkPrices",
        "CurvePrices",
    ):
        source = migration.get_contract(candidate_label(name))
        assert int(source.actionTimeLock()) == 0
        assert _as_address(source.governance()) == ZERO_ADDRESS

    human_resources = migration.get_contract(candidate_label("HumanResources"))
    assert int(human_resources.actionTimeLock()) == 0
    assert _as_address(human_resources.governance()) == ZERO_ADDRESS

    mission_control = migration.get_contract(candidate_label("MissionControl"))
    assert _as_address(mission_control.hrConfig()[0]) == _as_address(contributor)
    _assert_price_state_cloned(migration)

    active_psm = migration.get_contract("EndaomentPSM")
    expected_hq_args = {
        "Ledger": (hq, defaults, LEDGER_ACTION_BLOCK_SOURCE),
        "MissionControl": (hq, defaults),
        "Switchboard": (
            hq,
            deployer,
            LOCAL_GOV_MIN_TIMELOCK,
            LOCAL_GOV_MAX_TIMELOCK,
        ),
        "PriceDesk": (
            hq,
            deployer,
            eth,
            REGISTRY_MIN_DELAY,
            REGISTRY_MAX_DELAY,
        ),
        "VaultBook": (
            hq,
            deployer,
            REGISTRY_MIN_DELAY,
            REGISTRY_MAX_DELAY,
        ),
        "AuctionHouse": (hq,),
        "AuctionHouseNFT": (hq,),
        "Boardroom": (hq,),
        "BondRoom": (hq, bond_booster),
        "CreditEngine": (hq,),
        "Endaoment": (hq, weth, eth),
        "HumanResources": (hq, HR_MIN_TIMELOCK, HR_MAX_TIMELOCK),
        "Lootbox": (
            hq,
            LOOTBOX_MIN_SEND_INTERVAL,
            LOOTBOX_SEND_INTERVAL,
            LOOTBOX_DEPOSIT_REWARD,
            LOOTBOX_YIELD_BONUS,
        ),
        "Teller": (hq, False),
        "Deleverage": (
            hq,
            DELEVERAGE_MIN_BPS,
            DELEVERAGE_BUFFER,
            DELEVERAGE_COOLDOWN,
            DELEVERAGE_UNDERSCORE_SPREAD,
            DELEVERAGE_FULL_PAYOFF_BUFFER,
            DELEVERAGE_OVERAGE_BPS,
            DELEVERAGE_DUST_THRESHOLD,
            DELEVERAGE_DUST_BPS,
        ),
        "CreditRedeem": (hq,),
        "TellerUtils": (hq,),
        "EndaomentFunds": (hq,),
        "EndaomentPSM": (
            hq,
            PSM_NUM_BLOCKS_PER_INTERVAL,
            PSM_MINT_FEE,
            PSM_MAX_INTERVAL_MINT,
            PSM_REDEEM_FEE,
            PSM_MAX_INTERVAL_REDEEM,
            active_psm.USDC(),
            PSM_YIELD_LEGO_ID,
            PSM_YIELD_VAULT_TOKEN,
        ),
    }

    log.h1("Authenticating and promoting the complete fresh generation")
    promotions = [
        _spec(name, RIPE_HQ, hq, reg_id, expected_hq_args[name])
        for name, reg_id in HQ_ACTIVATED
    ]

    switchboard_args = {
        "SwitchboardAlpha": (
            hq,
            deployer,
            STALE_WINDOW_MIN,
            STALE_WINDOW_MAX,
            SWITCHBOARD_MIN_TIMELOCK,
            SWITCHBOARD_MAX_TIMELOCK,
        ),
        **{
            name: (
                hq,
                deployer,
                SWITCHBOARD_MIN_TIMELOCK,
                SWITCHBOARD_MAX_TIMELOCK,
            )
            for name in (
                "SwitchboardBravo",
                "SwitchboardCharlie",
                "SwitchboardDelta",
                "SwitchboardEcho",
            )
        },
    }
    promotions.extend(
        _spec(
            name,
            candidate_label("Switchboard"),
            switchboard,
            reg_id,
            switchboard_args[name],
        )
        for name, reg_id in SWITCHBOARD_CHILDREN
    )

    price_args = {
        "ChainlinkPrices": (
            hq,
            deployer,
            PRICE_MIN_TIMELOCK,
            PRICE_MAX_TIMELOCK,
            weth,
            eth,
            btc,
            eth_feed,
            btc_feed,
            STALE_WINDOW_DEFAULT,
        ),
        "CurvePrices": (
            hq,
            deployer,
            LIVE_CURVE_ADDRESS_PROVIDER,
            migration.get_address("GreenToken"),
            migration.get_address("SavingsGreen"),
            PRICE_CHANGE_MIN_TIMELOCK,
            PRICE_CHANGE_MAX_TIMELOCK,
        ),
        "UniswapV2Prices": (
            hq,
            RIPE_WETH_POOL,
            migration.get_address("RipeToken"),
            weth,
        ),
    }
    promotions.extend(
        _spec(
            name,
            candidate_label("PriceDesk"),
            price_desk,
            reg_id,
            price_args[name],
        )
        for name, reg_id in PRICE_SOURCE_CHILDREN
    )
    promotions.extend(
        _spec(
            name,
            candidate_label("VaultBook"),
            vault_book,
            reg_id,
            (hq,),
        )
        for name, reg_id in VAULT_CHILDREN
    )

    # Defaults and BondBooster have no direct slot. Their activated consumers
    # are the independently authenticated registry witnesses.
    promotions.append(
        PromotionSpec(
            canonical_name="DefaultsRobinhoodLive",
            expected_source_path=CANONICAL_SOURCE_PATHS["DefaultsRobinhoodLive"],
            candidate_label=candidate_label("DefaultsRobinhoodLive"),
            registry_name=RIPE_HQ,
            registry=hq,
            registry_id=5,
            expected_constructor_args=(contributor,),
            activation_candidate_label=candidate_label("MissionControl"),
            activation_dependency_arg_index=1,
            activation_expected_constructor_args=(hq, defaults),
        )
    )
    promotions.append(
        PromotionSpec(
            canonical_name="BondBooster",
            expected_source_path=CANONICAL_SOURCE_PATHS["BondBooster"],
            candidate_label=candidate_label("BondBooster"),
            registry_name=RIPE_HQ,
            registry=hq,
            registry_id=12,
            expected_constructor_args=(
                hq,
                BOND_BOOSTER_MAX_BOOST_RATIO,
                BOND_BOOSTER_MAX_UNITS,
                BOND_BOOSTER_MIN_LOCK_DURATION,
            ),
            activation_candidate_label=candidate_label("BondRoom"),
            activation_dependency_arg_index=1,
            activation_expected_constructor_args=(hq, bond_booster),
        )
    )

    assert len(promotions) == len(CANONICAL_SOURCE_PATHS) == 32
    migration.promote_candidates(promotions)
