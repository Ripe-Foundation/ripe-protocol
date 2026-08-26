"""Verify the activated PR #211 generation and publish canonical records.

This migration sends no transaction.  It checks every authoritative registry,
constructor input, copied Chainlink route, pause state, and retained parameter
before replacing the staged manifest labels atomically.
"""

from scripts.utils import log
from scripts.utils.migration import Migration, PromotionSpec

from config.robinhood_launch import (
    CURVE_PRICES_ID,
    HR_MAX_TIMELOCK,
    HR_MIN_TIMELOCK,
    PRICE_MAX_TIMELOCK,
    PRICE_MIN_TIMELOCK,
    STALE_WINDOW_INHERIT,
    SWITCHBOARD_MAX_TIMELOCK,
    SWITCHBOARD_MIN_TIMELOCK,
    TELLER_SHOULD_PAUSE,
    ZERO_ADDRESS,
)


STAGED_SUFFIX = "Staged2026082600"

RIPE_HQ = "0xD4e82AE1De673bba3B53386A2D2C630AE6630940"
SWITCHBOARD = "0xA1872467AC4fb442aeA341163A65263915ce178a"
PRICE_DESK = "0x56Db9c2322e009189049bC57385751fc7922AAb0"
VAULT_BOOK = "0x9B37ea4E5b250Fef242fFC88364A143Fa39DF090"

OLD_CHAINLINK_PRICES = "0xf4AF744784fBdB5f251F95a789AC0f9aB702d310"
OLD_STABILITY_POOL = "0x03b9d0C5f628671FC877f267cC706BEd91Cc42fB"
OLD_DELEVERAGE = "0x781a37a5999760c73c52fcdE1a6A34668D8eA311"

SOURCE = {
    "DefaultsRobinhoodLive": "contracts/config/DefaultsRobinhoodLive.vy",
    "MissionControl": "contracts/data/MissionControl.vy",
    "SwitchboardBravo": "contracts/config/SwitchboardBravo.vy",
    "ChainlinkPrices": "contracts/priceSources/ChainlinkPrices.vy",
    "StabilityPool": "contracts/vaults/StabilityPool.vy",
    "AuctionHouse": "contracts/core/AuctionHouse.vy",
    "CreditEngine": "contracts/core/CreditEngine.vy",
    "HumanResources": "contracts/core/HumanResources.vy",
    "Teller": "contracts/core/Teller.vy",
    "Deleverage": "contracts/core/Deleverage.vy",
    "CreditRedeem": "contracts/core/CreditRedeem.vy",
}


def staged(name):
    return f"{name}{STAGED_SUFFIX}"


def migrate(migration: Migration):
    # ------------------------------------------------------------------
    # 1. Read the exact staged contracts and retained roots.
    # ------------------------------------------------------------------
    log.h1("1. Reading the activated PR #211 generation")

    hq = migration.get_contract("RipeHq", RIPE_HQ)
    switchboard = migration.get_contract("Switchboard", SWITCHBOARD)
    price_desk = migration.get_contract("PriceDesk", PRICE_DESK)
    vault_book = migration.get_contract("VaultBook", VAULT_BOOK)

    mission_control = migration.get_contract(staged("MissionControl"))
    bravo = migration.get_contract(staged("SwitchboardBravo"))
    chainlink = migration.get_contract(staged("ChainlinkPrices"))
    stability_pool = migration.get_contract(staged("StabilityPool"))
    auction_house = migration.get_contract(staged("AuctionHouse"))
    credit_engine = migration.get_contract(staged("CreditEngine"))
    human_resources = migration.get_contract(staged("HumanResources"))
    teller = migration.get_contract(staged("Teller"))
    deleverage = migration.get_contract(staged("Deleverage"))
    credit_redeem = migration.get_contract(staged("CreditRedeem"))
    defaults = migration.get_contract(staged("DefaultsRobinhoodLive"))
    contributor = migration.get_contract("Contributor")

    # ------------------------------------------------------------------
    # 2. Prove Safe activation and copied state before touching manifests.
    # ------------------------------------------------------------------
    log.h1("2. Checking registry and state readbacks")

    require_slot(hq, 5, mission_control)
    require_slot(hq, 9, auction_house)
    require_slot(hq, 13, credit_engine)
    require_slot(hq, 15, human_resources)
    require_slot(hq, 17, teller)
    require_slot(hq, 18, deleverage)
    require_slot(hq, 19, credit_redeem)
    require_slot(switchboard, 2, bravo)
    require_slot(price_desk, 1, chainlink)
    require_slot(vault_book, 1, stability_pool)

    assert as_address(mission_control.hrConfig()[0]) == as_address(contributor)
    assert as_address(bravo.governance()) == ZERO_ADDRESS
    assert int(bravo.actionTimeLock()) == 0
    assert as_address(chainlink.governance()) == ZERO_ADDRESS
    assert int(chainlink.actionTimeLock()) == 0
    assert as_address(human_resources.governance()) == ZERO_ADDRESS
    assert int(human_resources.actionTimeLock()) == 0
    assert not bool(teller.isPaused())
    assert int(credit_engine.undyVaulDiscount()) == 5_000
    assert int(credit_engine.buybackRatio()) == 0

    old_chainlink = migration.get_contract(
        "ChainlinkPrices", OLD_CHAINLINK_PRICES
    )
    require_chainlink_copy(old_chainlink, chainlink)
    old_pool = migration.get_contract("StabilityPool", OLD_STABILITY_POOL)
    require_empty_stability_pool(old_pool)
    old_deleverage = migration.get_contract("Deleverage", OLD_DELEVERAGE)
    assert deleverage_config(deleverage) == deleverage_config(old_deleverage)

    # ------------------------------------------------------------------
    # 3. Authenticate constructors and atomically publish canonical names.
    # ------------------------------------------------------------------
    log.h1("3. Publishing the PR #211 canonical manifest records")

    deployer = migration.account()
    eth = old_chainlink.ETH()
    weth = old_chainlink.WETH()
    btc = old_chainlink.BTC()
    promotions = (
        PromotionSpec(
            canonical_name="DefaultsRobinhoodLive",
            expected_source_path=SOURCE["DefaultsRobinhoodLive"],
            candidate_label=staged("DefaultsRobinhoodLive"),
            registry_name="RipeHq",
            registry=hq,
            registry_id=5,
            expected_constructor_args=(contributor,),
            activation_candidate_label=staged("MissionControl"),
            activation_dependency_arg_index=1,
            activation_expected_constructor_args=(hq, defaults),
        ),
        promotion("MissionControl", "RipeHq", hq, 5, (hq, defaults)),
        promotion(
            "SwitchboardBravo",
            "Switchboard",
            switchboard,
            2,
            (hq, deployer, SWITCHBOARD_MIN_TIMELOCK, SWITCHBOARD_MAX_TIMELOCK),
        ),
        promotion(
            "ChainlinkPrices",
            "PriceDesk",
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
        promotion("StabilityPool", "VaultBook", vault_book, 1, (hq,)),
        promotion("AuctionHouse", "RipeHq", hq, 9, (hq,)),
        promotion(
            "CreditEngine", "RipeHq", hq, 13, (hq, CURVE_PRICES_ID)
        ),
        promotion(
            "HumanResources",
            "RipeHq",
            hq,
            15,
            (hq, HR_MIN_TIMELOCK, HR_MAX_TIMELOCK),
        ),
        promotion(
            "Teller",
            "RipeHq",
            hq,
            17,
            (hq, TELLER_SHOULD_PAUSE, CURVE_PRICES_ID),
        ),
        promotion(
            "Deleverage",
            "RipeHq",
            hq,
            18,
            (hq, *deleverage_config(old_deleverage)),
        ),
        promotion("CreditRedeem", "RipeHq", hq, 19, (hq,)),
    )
    migration.promote_candidates(promotions)


def as_address(value):
    return str(getattr(value, "address", value)).lower()


def require_slot(registry, reg_id, expected):
    assert as_address(registry.getAddr(reg_id)) == as_address(expected)


def promotion(name, registry_name, registry, reg_id, constructor_args):
    return PromotionSpec(
        canonical_name=name,
        expected_source_path=SOURCE[name],
        candidate_label=staged(name),
        registry_name=registry_name,
        registry=registry,
        registry_id=reg_id,
        expected_constructor_args=constructor_args,
    )


def normalized(value):
    if isinstance(value, str) and value.startswith("0x") and len(value) == 42:
        return value.lower()
    if isinstance(value, (tuple, list)):
        return tuple(normalized(item) for item in value)
    return value


def require_chainlink_copy(old, fresh):
    old_assets = tuple(old.getPricedAssets())
    fresh_assets = tuple(fresh.getPricedAssets())
    assert tuple(map(as_address, fresh_assets)) == tuple(map(as_address, old_assets))
    for asset in old_assets:
        assert normalized(fresh.feedConfig(asset)) == normalized(old.feedConfig(asset))


def require_empty_stability_pool(pool):
    for index in range(1, int(pool.numAssets())):
        asset = pool.vaultAssets(index)
        assert int(pool.totalBalances(asset)) == 0
        assert int(pool.getTotalAmountForVault(asset)) == 0
        assert int(pool.getNumActiveClaimAssets(asset)) == 0
        for claim_index in range(1, int(pool.numClaimableAssets(asset))):
            claim_asset = pool.claimableAssets(asset, claim_index)
            assert int(pool.totalClaimableBalances(claim_asset)) == 0


def deleverage_config(contract):
    return (
        int(contract.minDeleverageBps()),
        int(contract.deleverageBuffer()),
        int(contract.deleverageCooldown()),
        int(contract.underscoreSafeSpreadBps()),
        int(contract.deleverageFullPayoffBuffer()),
        int(contract.deleverageOverageBps()),
        int(contract.deleverageDustThreshold()),
        int(contract.deleverageDustBps()),
    )
