"""Record the PR #208 contracts after the Safe activates them.

This step sends no transactions.  It reads the activated registry tree,
checks that it is the generation deployed by 2026082405, and promotes those
candidate records to their canonical manifest names.
"""

from scripts.utils import log
from scripts.utils.migration import Migration, PromotionSpec

from config.robinhood_launch import (
    CURVE_PRICES_ID,
    PRICE_CHANGE_MAX_TIMELOCK,
    PRICE_CHANGE_MIN_TIMELOCK,
    PRICE_MAX_TIMELOCK,
    PRICE_MIN_TIMELOCK,
    PYTH_PRICES_ID,
    REGISTRY_MAX_DELAY,
    REGISTRY_MIN_DELAY,
    STALE_WINDOW_INHERIT,
    STALE_WINDOW_MAX,
    STALE_WINDOW_MIN,
    SWITCHBOARD_MAX_TIMELOCK,
    SWITCHBOARD_MIN_TIMELOCK,
    TELLER_SHOULD_PAUSE,
    ZERO_ADDRESS,
    stale_time_override_for_asset,
)


CANDIDATE_SUFFIX = "Candidate2026082405"
LIVE_CURVE_ADDRESS_PROVIDER = "0x4574921eb950d3Fd5B01562162EC566Cb8bc3648"

# Retained generation used as the configuration source by 2026082405.
RIPE_HQ = "0xD4e82AE1De673bba3B53386A2D2C630AE6630940"
RETAINED_SWITCHBOARD = "0xA1872467AC4fb442aeA341163A65263915ce178a"
RETAINED_PRICE_DESK = "0x4EEc14F2905ec6bCfE9f399b90c1b92128B0AF8B"
RETAINED_CHAINLINK_PRICES = "0x599180f6cFCDa61FcFDC924c637b97d41c007E0F"
RETAINED_CURVE_PRICES = "0xC98e6c6CD0DDF20aA71413Ee12A1d169f58C418E"

SOURCE = {
    "SwitchboardAlpha": "contracts/config/SwitchboardAlpha.vy",
    "SwitchboardBravo": "contracts/config/SwitchboardBravo.vy",
    "SwitchboardCharlie": "contracts/config/SwitchboardCharlie.vy",
    "PriceDesk": "contracts/registries/PriceDesk.vy",
    "ChainlinkPrices": "contracts/priceSources/ChainlinkPrices.vy",
    "CurvePrices": "contracts/priceSources/CurvePrices.vy",
    "VaultBook": "contracts/registries/VaultBook.vy",
    "StabilityPool": "contracts/vaults/StabilityPool.vy",
    "CreditEngine": "contracts/core/CreditEngine.vy",
    "Endaoment": "contracts/core/Endaoment.vy",
    "Teller": "contracts/core/Teller.vy",
}


def candidate(name):
    return f"{name}{CANDIDATE_SUFFIX}"


def migrate(migration: Migration):
    # ---------------------------------------------------------------------
    # 1. Read the generation deployed by 2026082405.
    # ---------------------------------------------------------------------
    log.h1("1. Reading the activated PR #208 generation")

    hq = migration.get_contract("RipeHq", RIPE_HQ)
    switchboard = migration.get_contract("Switchboard", RETAINED_SWITCHBOARD)
    price_desk = migration.get_contract(candidate("PriceDesk"))
    vault_book = migration.get_contract(candidate("VaultBook"))
    deployer = migration.account()

    old_price_desk = migration.get_contract("PriceDesk", RETAINED_PRICE_DESK)
    old_chainlink = migration.get_contract(
        "ChainlinkPrices", RETAINED_CHAINLINK_PRICES
    )
    old_curve = migration.get_contract("CurvePrices", RETAINED_CURVE_PRICES)
    eth = old_price_desk.ETH()
    weth = old_chainlink.WETH()
    btc = old_chainlink.BTC()

    # ---------------------------------------------------------------------
    # 2. Confirm the Safe activated the complete tree.
    # ---------------------------------------------------------------------
    log.h1("2. Checking registry and oracle readbacks")

    require_tree(
        hq,
        (
            (7, price_desk),
            (8, vault_book),
            (13, migration.get_address(candidate("CreditEngine"))),
            (14, migration.get_address(candidate("Endaoment"))),
            (17, migration.get_address(candidate("Teller"))),
        ),
        require_local_governance=False,
    )
    require_tree(
        switchboard,
        (
            (1, migration.get_address(candidate("SwitchboardAlpha"))),
            (2, migration.get_address(candidate("SwitchboardBravo"))),
            (3, migration.get_address(candidate("SwitchboardCharlie"))),
        ),
        require_local_governance=False,
    )
    require_tree(
        price_desk,
        (
            (1, migration.get_address(candidate("ChainlinkPrices"))),
            (2, migration.get_address(candidate("CurvePrices"))),
            (3, migration.get_address("UniswapV2Prices")),
        ),
    )
    require_tree(
        vault_book,
        (
            (1, migration.get_address(candidate("StabilityPool"))),
            (2, migration.get_address("RipeGov")),
            (3, migration.get_address("SimpleErc20")),
        ),
    )

    for name in (
        "SwitchboardAlpha",
        "SwitchboardBravo",
        "SwitchboardCharlie",
        "ChainlinkPrices",
        "CurvePrices",
    ):
        require_relinquished(migration.get_contract(candidate(name)))

    assert not bool(migration.get_contract(candidate("Teller")).isPaused())
    require_oracles_copied(migration, old_chainlink, old_curve)
    require_token_scales_copied(
        migration,
        old_price_desk,
        price_desk,
        eth,
    )

    # ---------------------------------------------------------------------
    # 3. Authenticate constructor inputs and promote all eleven records.
    # ---------------------------------------------------------------------
    log.h1("3. Promoting the eleven deployment records")

    promotions = (
        promotion(
            "SwitchboardAlpha",
            "Switchboard",
            switchboard,
            1,
            (
                hq,
                deployer,
                STALE_WINDOW_MIN,
                STALE_WINDOW_MAX,
                SWITCHBOARD_MIN_TIMELOCK,
                SWITCHBOARD_MAX_TIMELOCK,
                PYTH_PRICES_ID,
            ),
        ),
        promotion(
            "SwitchboardBravo",
            "Switchboard",
            switchboard,
            2,
            (hq, deployer, SWITCHBOARD_MIN_TIMELOCK, SWITCHBOARD_MAX_TIMELOCK),
        ),
        promotion(
            "SwitchboardCharlie",
            "Switchboard",
            switchboard,
            3,
            (hq, deployer, SWITCHBOARD_MIN_TIMELOCK, SWITCHBOARD_MAX_TIMELOCK),
        ),
        promotion(
            "PriceDesk",
            "RipeHq",
            hq,
            7,
            (hq, deployer, eth, REGISTRY_MIN_DELAY, REGISTRY_MAX_DELAY),
        ),
        promotion(
            "ChainlinkPrices",
            candidate("PriceDesk"),
            price_desk,
            1,
            (
                hq,
                deployer,
                PRICE_MIN_TIMELOCK,
                PRICE_MAX_TIMELOCK,
                weth,
                eth,
                btc,
                old_chainlink.feedConfig(eth)[0],
                old_chainlink.feedConfig(btc)[0],
                STALE_WINDOW_INHERIT,
            ),
        ),
        promotion(
            "CurvePrices",
            candidate("PriceDesk"),
            price_desk,
            2,
            (
                hq,
                deployer,
                LIVE_CURVE_ADDRESS_PROVIDER,
                migration.get_address("GreenToken"),
                migration.get_address("SavingsGreen"),
                PRICE_CHANGE_MIN_TIMELOCK,
                PRICE_CHANGE_MAX_TIMELOCK,
            ),
        ),
        promotion(
            "VaultBook",
            "RipeHq",
            hq,
            8,
            (hq, deployer, REGISTRY_MIN_DELAY, REGISTRY_MAX_DELAY),
        ),
        promotion(
            "StabilityPool",
            candidate("VaultBook"),
            vault_book,
            1,
            (hq,),
        ),
        promotion("CreditEngine", "RipeHq", hq, 13, (hq, CURVE_PRICES_ID)),
        promotion(
            "Endaoment",
            "RipeHq",
            hq,
            14,
            (hq, weth, eth, CURVE_PRICES_ID),
        ),
        promotion(
            "Teller",
            "RipeHq",
            hq,
            17,
            (hq, TELLER_SHOULD_PAUSE, CURVE_PRICES_ID),
        ),
    )
    migration.promote_candidates(promotions)


# -------------------------------------------------------------------------
# Readback and manifest mechanics
# -------------------------------------------------------------------------


def address(value):
    return str(getattr(value, "address", value)).lower()


def normalized(value):
    if isinstance(value, str) and value.startswith("0x") and len(value) == 42:
        return value.lower()
    if isinstance(value, (tuple, list)):
        return tuple(normalized(item) for item in value)
    return value


def require_tree(root, expected, *, require_local_governance=True):
    for reg_id, expected_address in expected:
        assert address(root.getAddr(reg_id)) == address(expected_address)
    assert int(root.registryChangeTimeLock()) == 0
    if require_local_governance:
        assert address(root.governance()) == ZERO_ADDRESS


def require_relinquished(contract):
    assert int(contract.actionTimeLock()) == 0
    assert address(contract.governance()) == ZERO_ADDRESS


def require_oracles_copied(migration, old_chainlink, old_curve):
    new_chainlink = migration.get_contract(candidate("ChainlinkPrices"))
    old_assets = tuple(old_chainlink.getPricedAssets())
    new_assets = tuple(new_chainlink.getPricedAssets())
    assert tuple(map(address, new_assets)) == tuple(map(address, old_assets))
    for asset in old_assets:
        old = old_chainlink.feedConfig(asset)
        new = new_chainlink.feedConfig(asset)
        assert address(new[0]) == address(old[0])
        assert int(new[1]) == int(old[1])
        assert bool(new[2]) == bool(old[2])
        assert bool(new[3]) == bool(old[3])
        assert int(new[4]) == stale_time_override_for_asset(str(asset))

    new_curve = migration.get_contract(candidate("CurvePrices"))
    old_assets = tuple(old_curve.getPricedAssets())
    new_assets = tuple(new_curve.getPricedAssets())
    assert tuple(map(address, new_assets)) == tuple(map(address, old_assets))
    for asset in old_assets:
        assert normalized(new_curve.curveConfig(asset)) == normalized(
            old_curve.curveConfig(asset)
        )
    assert normalized(new_curve.greenRefPoolConfig()) == normalized(
        old_curve.greenRefPoolConfig()
    )


def is_nft(config):
    return bool(config.isNft) if hasattr(config, "isNft") else bool(config[-1])


def require_token_scales_copied(
    migration,
    old_price_desk,
    new_price_desk,
    eth,
):
    mission_control = migration.get_contract("MissionControl")
    assets = [
        mission_control.assets(index)
        for index in range(1, int(mission_control.numAssets()))
    ]
    assets.append(migration.get_contract("EndaomentPSM").USDC())

    checked = set()
    for asset in assets:
        key = address(asset)
        if key in checked or key in (ZERO_ADDRESS, address(eth)):
            continue
        if is_nft(mission_control.assetConfig(asset)):
            continue
        checked.add(key)
        old_scale = int(old_price_desk.tokenScale(asset))
        assert old_scale != 0
        assert int(new_price_desk.tokenScale(asset)) == old_scale


def promotion(name, registry_name, registry, reg_id, constructor_args):
    return PromotionSpec(
        canonical_name=name,
        expected_source_path=SOURCE[name],
        candidate_label=candidate(name),
        registry_name=registry_name,
        registry=registry,
        registry_id=reg_id,
        expected_constructor_args=constructor_args,
    )
