"""Stage the clean Robinhood generation built from PR #211.

Read ``migrate`` from top to bottom as the deployment checklist.  Nothing in
this migration changes a live registry.  It deploys the replacement contracts,
copies the live Chainlink routes, and prints the one Safe batch that activates
the reviewed generation.

Ledger and RipeGov are intentionally reset even though their runtimes did not
change.  The old RipeGov position cannot exit its lock because it is the only
holder; governance chose to compensate that user later.  Its exact holder,
shares, and underlying amount are pinned below.  Any additional old-vault
state makes this migration fail before deployment.
"""

from pathlib import Path

from scripts.utils import log
from scripts.utils.ledger_deployment import validate_ledger_action_block_source
from scripts.utils.migration import Migration

from config.robinhood_launch import (
    CURVE_PRICES_ID,
    HR_MAX_TIMELOCK,
    HR_MIN_TIMELOCK,
    LEDGER_ACTION_BLOCK_SOURCE,
    LOOTBOX_DEPOSIT_REWARD,
    LOOTBOX_MIN_SEND_INTERVAL,
    LOOTBOX_SEND_INTERVAL,
    LOOTBOX_YIELD_BONUS,
    PRICE_MAX_TIMELOCK,
    PRICE_MIN_TIMELOCK,
    PYTH_PRICES_ID,
    STALE_WINDOW_INHERIT,
    STALE_WINDOW_MAX,
    STALE_WINDOW_MIN,
    SWITCHBOARD_MAX_TIMELOCK,
    SWITCHBOARD_MIN_TIMELOCK,
    TELLER_SHOULD_PAUSE,
    ZERO_ADDRESS,
)


# This stays False while PR #211's Vyper files are still changing.  Final review
# must refresh the runtime inventory and Defaults snapshot before enabling it.
DEPLOYMENT_READY = False
PR211_REVIEW_HEAD = "63bc7e18722b5f423b39cf5b356de385382be6c8"
DEFAULTS_SNAPSHOT_BLOCK = 0
DEFAULTS_SNAPSHOT_BLOCK_HASH = ""
# Defaults cannot carry MissionControl.userConfig/userDelegation.  Final review
# must scan both Teller and SwitchboardCharlie events through the snapshot block.
USER_STATE_AUDIT_BLOCK = 0
USER_CONFIG_EVENT_COUNT = None
USER_DELEGATION_EVENT_COUNT = None

STAGED_SUFFIX = "Staged2026082600"

# Retained live generation.  Hardcoding makes reruns independent of accidental
# canonical-manifest edits and makes the review surface explicit.
RIPE_HQ = "0xD4e82AE1De673bba3B53386A2D2C630AE6630940"
LEDGER = "0xF1CD5BE4288b744913d33F55370793ca833D08d7"
MISSION_CONTROL = "0xD335373E59cA2F07FC3B779F2B456972C7EfDb29"
SWITCHBOARD = "0xA1872467AC4fb442aeA341163A65263915ce178a"
SWITCHBOARD_ALPHA = "0x5e7dE30B8636f6227f4C1fCA2d03FEcC7C2F286d"
SWITCHBOARD_BRAVO = "0x5281175B0f4a8ba4839d43d778434F7274Be52B8"
SWITCHBOARD_CHARLIE = "0x846176B2294a5168a04345087f0474738B569150"
SWITCHBOARD_DELTA = "0x2606Ce36b62a77562DF664E7a0009805BB254F3f"
PRICE_DESK = "0x56Db9c2322e009189049bC57385751fc7922AAb0"
CHAINLINK_PRICES = "0xf4AF744784fBdB5f251F95a789AC0f9aB702d310"
VAULT_BOOK = "0x9B37ea4E5b250Fef242fFC88364A143Fa39DF090"
STABILITY_POOL = "0x03b9d0C5f628671FC877f267cC706BEd91Cc42fB"
RIPE_GOV = "0x7Eb9E83c4F475B650Ad25E359532286E130DED7f"
SIMPLE_ERC20 = "0x4F89C94636995eF20d40d5592bA2585348bE6D53"
AUCTION_HOUSE = "0xA5801c426590F44Bc7d33551Caf7354488C8516C"
CREDIT_ENGINE = "0x16371fAf6f603f8d8D6cef8C46253c80AdEe8b98"
HUMAN_RESOURCES = "0xCd9F242a2B82387a3ED02cC4a8a0fF9a7EE8d8F5"
LOOTBOX = "0x64CC9916d6222baC56f9DA770F78A3d71b0cFc80"
TELLER = "0xceE8Ed804f72b6EcB6B2D679ca17B545bD654bF6"
DELEVERAGE = "0x781a37a5999760c73c52fcdE1a6A34668D8eA311"
CREDIT_REDEEM = "0x7aAB69c238EA051Fa9e8370559FD917a72dBe074"

RIPE_TOKEN = "0x4D3f37a965b21aB4122e92Dd41D2693E742c883b"
SAVINGS_GREEN = "0x290a52380A88f743813B8C3e9F6B0e61DB5FDF73"
GREEN_USDG_POOL = "0x2fD13b49F970e8C6D89283056C1c6281214b7EB6"
RIPE_WETH_POOL = "0xba6F6CBa1a4104000847d4fdccB676E99166CEcE"

# Explicitly accepted legacy state.  These are exact values, not allowances.
# A deposit, withdrawal, transfer, or reward-induced share change requires a
# new team review and a new snapshot before deployment can proceed.
ACKNOWLEDGED_RIPE_HOLDER = "0x31a3bcdBcC9234de33cf51507D2FDA69B02c34BC"
ACKNOWLEDGED_RIPE_SHARES = 2_419_789_616_525_529_173_200_000_000
ACKNOWLEDGED_RIPE_AMOUNT = 24_197_896_165_255_291_732
ACKNOWLEDGED_SGREEN_DUST = 1

HQ_UPDATES = (
    ("Ledger", 4),
    ("MissionControl", 5),
    ("AuctionHouse", 9),
    ("CreditEngine", 13),
    ("HumanResources", 15),
    ("Lootbox", 16),
    ("Teller", 17),
    ("Deleverage", 18),
    ("CreditRedeem", 19),
)

SWITCHBOARD_UPDATES = (
    ("SwitchboardAlpha", 1),
    ("SwitchboardBravo", 2),
    ("SwitchboardCharlie", 3),
    ("SwitchboardDelta", 4),
)


def staged(name):
    return f"{name}{STAGED_SUFFIX}"


def migrate(migration: Migration):
    # ------------------------------------------------------------------
    # 1. Bind the retained live generation and the final review inputs.
    # ------------------------------------------------------------------
    log.h1("1. PR #211 deployment preflight")
    require_release_inputs()

    hq = migration.get_contract("RipeHq", RIPE_HQ)
    old_ledger = migration.get_contract("Ledger", LEDGER)
    old_mc = migration.get_contract("MissionControl", MISSION_CONTROL)
    switchboard = migration.get_contract("Switchboard", SWITCHBOARD)
    old_alpha = migration.get_contract("SwitchboardAlpha", SWITCHBOARD_ALPHA)
    old_bravo = migration.get_contract("SwitchboardBravo", SWITCHBOARD_BRAVO)
    old_charlie = migration.get_contract("SwitchboardCharlie", SWITCHBOARD_CHARLIE)
    old_delta = migration.get_contract("SwitchboardDelta", SWITCHBOARD_DELTA)
    price_desk = migration.get_contract("PriceDesk", PRICE_DESK)
    old_chainlink = migration.get_contract("ChainlinkPrices", CHAINLINK_PRICES)
    vault_book = migration.get_contract("VaultBook", VAULT_BOOK)
    old_pool = migration.get_contract("StabilityPool", STABILITY_POOL)
    old_ripe_gov = migration.get_contract("RipeGov", RIPE_GOV)
    simple_erc20 = migration.get_contract("SimpleErc20", SIMPLE_ERC20)
    ripe_token = migration.get_contract("RipeToken", RIPE_TOKEN)
    savings_green = migration.get_contract("SavingsGreen", SAVINGS_GREEN)
    old_credit = migration.get_contract("CreditEngine", CREDIT_ENGINE)
    old_hr = migration.get_contract("HumanResources", HUMAN_RESOURCES)
    old_deleverage = migration.get_contract("Deleverage", DELEVERAGE)

    require_slot(hq, 4, old_ledger)
    require_slot(hq, 5, old_mc)
    require_slot(hq, 9, AUCTION_HOUSE)
    require_slot(hq, 13, old_credit)
    require_slot(hq, 15, old_hr)
    require_slot(hq, 16, LOOTBOX)
    require_slot(hq, 17, TELLER)
    require_slot(hq, 18, old_deleverage)
    require_slot(hq, 19, CREDIT_REDEEM)
    require_slot(switchboard, 1, old_alpha)
    require_slot(switchboard, 2, old_bravo)
    require_slot(switchboard, 3, old_charlie)
    require_slot(switchboard, 4, old_delta)
    require_slot(price_desk, 1, old_chainlink)
    require_slot(vault_book, 1, old_pool)
    require_slot(vault_book, 2, old_ripe_gov)
    require_slot(vault_book, 3, simple_erc20)

    assert int(hq.registryChangeTimeLock()) == 0
    assert int(switchboard.registryChangeTimeLock()) == 0
    assert int(price_desk.registryChangeTimeLock()) == 0
    assert int(vault_book.registryChangeTimeLock()) == 0
    assert int(old_credit.undyVaulDiscount()) == 5_000
    assert int(old_credit.buybackRatio()) == 0
    require_clean_ledger(old_ledger)
    require_acknowledged_old_stability_pool(old_pool, savings_green)
    require_acknowledged_old_ripe_gov(
        old_ripe_gov,
        ripe_token,
    )
    require_economically_empty_vault(simple_erc20)

    # ------------------------------------------------------------------
    # 2. Deploy fresh live defaults and the changed PR #211 runtimes.
    # ------------------------------------------------------------------
    log.h1("2. Deploying the staged PR #211 generation")

    # Contributor is a blueprint rather than a registry member.  The fresh
    # Defaults contract binds it into MissionControl.hrConfig.
    contributor = migration.deploy_bp("Contributor")
    defaults = migration.deploy(
        "DefaultsRobinhoodLive",
        contributor,
        label=staged("DefaultsRobinhoodLive"),
    )

    ledger = migration.deploy(
        "Ledger",
        hq,
        defaults,
        LEDGER_ACTION_BLOCK_SOURCE,
        label=staged("Ledger"),
    )
    validation = validate_ledger_action_block_source(
        migration,
        ledger.address,
        LEDGER_ACTION_BLOCK_SOURCE,
        allow_local_preview=True,
    )
    if validation is not None:
        source, action_block = validation
        log.info(
            f"Ledger action source: 0x{source:040x}; " f"ArbSys block: {action_block}"
        )
    require_clean_ledger(ledger)

    mission_control = migration.deploy(
        "MissionControl",
        hq,
        defaults,
        label=staged("MissionControl"),
    )
    assert equivalent_global_config(old_mc, mission_control)
    assert as_address(mission_control.hrConfig()[0]) == as_address(contributor)

    alpha = deploy_switchboard(migration, hq, "SwitchboardAlpha")
    bravo = deploy_switchboard(migration, hq, "SwitchboardBravo")
    charlie = deploy_switchboard(migration, hq, "SwitchboardCharlie")
    delta = deploy_switchboard(migration, hq, "SwitchboardDelta")

    chainlink = deploy_chainlink_copy(migration, hq, old_chainlink)

    stability_pool = migration.deploy(
        "StabilityPool",
        hq,
        label=staged("StabilityPool"),
    )
    require_empty_stability_pool(stability_pool)
    ripe_gov = migration.deploy("RipeGov", hq, label=staged("RipeGov"))
    require_empty_vault(ripe_gov, "PR211_FRESH_RIPE_GOV_NOT_EMPTY")

    auction_house = migration.deploy("AuctionHouse", hq, label=staged("AuctionHouse"))
    credit_engine = migration.deploy(
        "CreditEngine",
        hq,
        CURVE_PRICES_ID,
        label=staged("CreditEngine"),
    )
    human_resources = migration.deploy(
        "HumanResources",
        hq,
        HR_MIN_TIMELOCK,
        HR_MAX_TIMELOCK,
        label=staged("HumanResources"),
    )
    lootbox = migration.deploy(
        "Lootbox",
        hq,
        LOOTBOX_MIN_SEND_INTERVAL,
        LOOTBOX_SEND_INTERVAL,
        LOOTBOX_DEPOSIT_REWARD,
        LOOTBOX_YIELD_BONUS,
        label=staged("Lootbox"),
    )
    teller = migration.deploy(
        "Teller",
        hq,
        TELLER_SHOULD_PAUSE,
        CURVE_PRICES_ID,
        label=staged("Teller"),
    )
    deleverage = migration.deploy(
        "Deleverage",
        hq,
        *deleverage_config(old_deleverage),
        label=staged("Deleverage"),
    )
    credit_redeem = migration.deploy("CreditRedeem", hq, label=staged("CreditRedeem"))

    assert int(credit_engine.undyVaulDiscount()) == int(old_credit.undyVaulDiscount())
    assert int(credit_engine.buybackRatio()) == int(old_credit.buybackRatio())
    assert as_address(human_resources.governance()) == ZERO_ADDRESS
    assert int(human_resources.actionTimeLock()) == 0
    assert bool(teller.isPaused()) is TELLER_SHOULD_PAUSE

    # ------------------------------------------------------------------
    # 3. Print the atomic Safe activation for team review.
    # ------------------------------------------------------------------
    log.h1("3. Safe activation batch")
    print_safe_batch(
        ledger=ledger,
        mission_control=mission_control,
        auction_house=auction_house,
        credit_engine=credit_engine,
        human_resources=human_resources,
        lootbox=lootbox,
        teller=teller,
        deleverage=deleverage,
        credit_redeem=credit_redeem,
        alpha=alpha,
        bravo=bravo,
        charlie=charlie,
        delta=delta,
        chainlink=chainlink,
        stability_pool=stability_pool,
        ripe_gov=ripe_gov,
    )


# ----------------------------------------------------------------------
# Repetitive readback and copy mechanics
# ----------------------------------------------------------------------


def as_address(value):
    return str(getattr(value, "address", value)).lower()


def require_release_inputs():
    if not DEPLOYMENT_READY:
        raise RuntimeError("PR211_DEPLOYMENT_NOT_FINAL")
    if DEFAULTS_SNAPSHOT_BLOCK == 0 or not DEFAULTS_SNAPSHOT_BLOCK_HASH:
        raise RuntimeError("PR211_DEFAULTS_SNAPSHOT_NOT_PINNED")
    if USER_STATE_AUDIT_BLOCK != DEFAULTS_SNAPSHOT_BLOCK:
        raise RuntimeError("PR211_USER_STATE_AUDIT_NOT_PINNED")
    if USER_CONFIG_EVENT_COUNT != 0 or USER_DELEGATION_EVENT_COUNT != 0:
        raise RuntimeError("PR211_MISSION_CONTROL_USER_STATE_NOT_EMPTY")

    source = (
        Path(__file__).resolve().parents[2]
        / "contracts/config/DefaultsRobinhoodLive.vy"
    ).read_text()
    required = (
        f"#   snapshot block: {DEFAULTS_SNAPSHOT_BLOCK}",
        f"#   snapshot block hash: {DEFAULTS_SNAPSHOT_BLOCK_HASH}",
        "#   snapshot finality: verified against the provider finalized tag",
        "CONTRIB_TEMPLATE: immutable(address)",
    )
    if any(marker not in source for marker in required):
        raise RuntimeError("PR211_DEFAULTS_SNAPSHOT_MISMATCH")


def require_slot(registry, reg_id, expected):
    if as_address(registry.getAddr(reg_id)) != as_address(expected):
        raise RuntimeError(f"PR211_ACTIVE_SLOT_MISMATCH:{reg_id}")


def require_clean_ledger(ledger):
    if int(ledger.totalDebt()) != 0:
        raise RuntimeError("PR211_LEDGER_DEBT_REMAINS")
    if int(ledger.getNumBorrowers()) != 0:
        raise RuntimeError("PR211_LEDGER_BORROWERS_REMAIN")
    if int(ledger.numContributors()) != 0:
        raise RuntimeError("PR211_LEDGER_CONTRIBUTORS_REMAIN")
    if int(ledger.badDebt()) != 0:
        raise RuntimeError("PR211_LEDGER_BAD_DEBT_REMAINS")


def require_empty_vault(vault, error):
    if int(vault.getNumVaultAssets()) != 0:
        raise RuntimeError(error)
    if bool(vault.doesVaultHaveAnyFunds()):
        raise RuntimeError(error)


def require_economically_empty_vault(vault):
    if bool(vault.doesVaultHaveAnyFunds()):
        raise RuntimeError("PR211_RETAINED_VAULT_FUNDS_REMAIN")
    for index in range(1, int(vault.numAssets())):
        asset = vault.vaultAssets(index)
        if int(vault.totalBalances(asset)) != 0:
            raise RuntimeError(f"PR211_RETAINED_VAULT_SHARES_REMAIN:{asset}")
        if int(vault.getTotalAmountForVault(asset)) != 0:
            raise RuntimeError(f"PR211_RETAINED_VAULT_FUNDS_REMAIN:{asset}")


def require_acknowledged_old_stability_pool(pool, savings_green):
    expected_assets = (SAVINGS_GREEN, GREEN_USDG_POOL)
    if int(pool.getNumVaultAssets()) != len(expected_assets):
        raise RuntimeError("PR211_OLD_STABILITY_POOL_ASSET_SET_CHANGED")

    for index, expected_asset in enumerate(expected_assets, start=1):
        asset = pool.vaultAssets(index)
        if as_address(asset) != as_address(expected_asset):
            raise RuntimeError("PR211_OLD_STABILITY_POOL_ASSET_SET_CHANGED")
        if int(pool.totalBalances(asset)) != 0:
            raise RuntimeError(f"PR211_STABILITY_POOL_SHARES_REMAIN:{asset}")
        if int(pool.getNumActiveClaimAssets(asset)) != 0:
            raise RuntimeError(f"PR211_STABILITY_POOL_ACTIVE_CLAIMS:{asset}")
        if int(pool.numClaimableAssets(asset)) != 0:
            raise RuntimeError(f"PR211_STABILITY_POOL_CLAIM_ASSETS_REMAIN:{asset}")

    if bool(pool.doesVaultHaveAnyFunds()):
        raise RuntimeError("PR211_STABILITY_POOL_SHARES_REMAIN")
    if int(pool.getTotalAmountForVault(SAVINGS_GREEN)) != ACKNOWLEDGED_SGREEN_DUST:
        raise RuntimeError("PR211_STABILITY_POOL_DUST_CHANGED")
    if int(savings_green.balanceOf(pool)) != ACKNOWLEDGED_SGREEN_DUST:
        raise RuntimeError("PR211_STABILITY_POOL_DUST_CHANGED")
    if int(pool.getTotalAmountForVault(GREEN_USDG_POOL)) != 0:
        raise RuntimeError("PR211_STABILITY_POOL_FUNDS_REMAIN")


def require_acknowledged_old_ripe_gov(vault, ripe_token):
    expected_assets = (RIPE_TOKEN, RIPE_WETH_POOL)
    if int(vault.getNumVaultAssets()) != len(expected_assets):
        raise RuntimeError("PR211_OLD_RIPE_GOV_ASSET_SET_CHANGED")
    for index, expected_asset in enumerate(expected_assets, start=1):
        if as_address(vault.vaultAssets(index)) != as_address(expected_asset):
            raise RuntimeError("PR211_OLD_RIPE_GOV_ASSET_SET_CHANGED")

    if not bool(vault.doesVaultHaveAnyFunds()):
        raise RuntimeError("PR211_ACKNOWLEDGED_RIPE_POSITION_CHANGED")
    if int(vault.getNumUserAssets(ACKNOWLEDGED_RIPE_HOLDER)) != 1:
        raise RuntimeError("PR211_ACKNOWLEDGED_RIPE_POSITION_CHANGED")
    if as_address(vault.userAssets(ACKNOWLEDGED_RIPE_HOLDER, 1)) != as_address(
        RIPE_TOKEN
    ):
        raise RuntimeError("PR211_ACKNOWLEDGED_RIPE_POSITION_CHANGED")

    total_shares = int(vault.totalBalances(RIPE_TOKEN))
    user_shares = int(vault.userBalances(ACKNOWLEDGED_RIPE_HOLDER, RIPE_TOKEN))
    if total_shares != ACKNOWLEDGED_RIPE_SHARES or user_shares != total_shares:
        raise RuntimeError("PR211_ACKNOWLEDGED_RIPE_SHARES_CHANGED")

    total_amount = int(vault.getTotalAmountForVault(RIPE_TOKEN))
    user_amount = int(vault.getTotalAmountForUser(ACKNOWLEDGED_RIPE_HOLDER, RIPE_TOKEN))
    token_balance = int(ripe_token.balanceOf(vault))
    if (
        total_amount != ACKNOWLEDGED_RIPE_AMOUNT
        or user_amount != total_amount
        or token_balance != total_amount
    ):
        raise RuntimeError("PR211_ACKNOWLEDGED_RIPE_AMOUNT_CHANGED")

    if int(vault.totalBalances(RIPE_WETH_POOL)) != 0:
        raise RuntimeError("PR211_OLD_RIPE_GOV_LP_SHARES_REMAIN")
    if int(vault.getTotalAmountForVault(RIPE_WETH_POOL)) != 0:
        raise RuntimeError("PR211_OLD_RIPE_GOV_LP_FUNDS_REMAIN")

    log.info(
        "Acknowledged legacy RipeGov state: "
        f"{ACKNOWLEDGED_RIPE_AMOUNT / 10**18:.6f} RIPE locked."
    )


def require_empty_stability_pool(pool):
    if int(pool.getNumVaultAssets()) != 0:
        raise RuntimeError("PR211_FRESH_STABILITY_POOL_NOT_EMPTY")
    if bool(pool.doesVaultHaveAnyFunds()):
        raise RuntimeError("PR211_FRESH_STABILITY_POOL_NOT_EMPTY")
    for index in range(1, int(pool.numAssets())):
        asset = pool.vaultAssets(index)
        if int(pool.totalBalances(asset)) != 0:
            raise RuntimeError(f"PR211_STABILITY_POOL_SHARES_REMAIN:{asset}")
        if int(pool.getTotalAmountForVault(asset)) != 0:
            raise RuntimeError(f"PR211_STABILITY_POOL_FUNDS_REMAIN:{asset}")
        if int(pool.getNumActiveClaimAssets(asset)) != 0:
            raise RuntimeError(f"PR211_STABILITY_POOL_ACTIVE_CLAIMS:{asset}")
        for claim_index in range(1, int(pool.numClaimableAssets(asset))):
            claim_asset = pool.claimableAssets(asset, claim_index)
            if int(pool.totalClaimableBalances(claim_asset)) != 0:
                raise RuntimeError(
                    f"PR211_STABILITY_POOL_CLAIM_LIABILITY:{claim_asset}"
                )


def deploy_switchboard(migration, hq, name):
    args = [hq, migration.account()]
    if name == "SwitchboardAlpha":
        args.extend((STALE_WINDOW_MIN, STALE_WINDOW_MAX))
    args.extend((SWITCHBOARD_MIN_TIMELOCK, SWITCHBOARD_MAX_TIMELOCK))
    if name == "SwitchboardAlpha":
        args.append(PYTH_PRICES_ID)

    board = migration.deploy(name, *args, label=staged(name))
    relinquish_governance(migration, board)
    return board


def normalized(value):
    if isinstance(value, str) and value.startswith("0x") and len(value) == 42:
        return value.lower()
    if isinstance(value, (tuple, list)):
        return tuple(normalized(item) for item in value)
    return value


def equivalent_global_config(old, fresh):
    scalar_getters = (
        "genConfig",
        "genDebtConfig",
        "hrConfig",
        "ripeBondConfig",
        "rewardsConfig",
        "getPriorityLiqAssetVaults",
        "getPriorityStabVaults",
        "getPriorityPriceSourceIds",
        "underscoreRegistry",
        "trainingWheels",
        "shouldCheckLastTouch",
        "coreRipeGovVaultId",
        "preferredStabVaultId",
        "totalPointsAllocs",
    )
    if any(
        normalized(getattr(old, name)()) != normalized(getattr(fresh, name)())
        for name in scalar_getters
        if name != "hrConfig"
    ):
        return False

    # hrConfig differs only in the intentionally replaced Contributor template.
    if normalized(old.hrConfig()[1:]) != normalized(fresh.hrConfig()[1:]):
        return False

    old_assets = tuple(old.assets(i) for i in range(1, int(old.numAssets())))
    fresh_assets = tuple(fresh.assets(i) for i in range(1, int(fresh.numAssets())))
    if tuple(map(as_address, old_assets)) != tuple(map(as_address, fresh_assets)):
        return False
    for asset in old_assets:
        if normalized(old.assetConfig(asset)) != normalized(fresh.assetConfig(asset)):
            return False
        if normalized(old.ripeGovVaultConfig(asset)) != normalized(
            fresh.ripeGovVaultConfig(asset)
        ):
            return False

    old_signers = tuple(
        old.liteSigners(index) for index in range(1, int(old.numLiteSigners()))
    )
    fresh_signers = tuple(
        fresh.liteSigners(index) for index in range(1, int(fresh.numLiteSigners()))
    )
    if tuple(map(as_address, old_signers)) != tuple(map(as_address, fresh_signers)):
        return False

    # RH currently has three registered vault rows; both historical classifiers
    # must survive the MissionControl replacement exactly.
    for vault_id in range(1, 4):
        if bool(old.isStabVaultId(vault_id)) != bool(fresh.isStabVaultId(vault_id)):
            return False
        if bool(old.isRipeGovVaultId(vault_id)) != bool(
            fresh.isRipeGovVaultId(vault_id)
        ):
            return False
    return True


def chainlink_config(value):
    return (
        as_address(value[0]),
        int(value[1]),
        bool(value[2]),
        bool(value[3]),
        int(value[4]),
    )


def deploy_chainlink_copy(migration, hq, old):
    eth = old.ETH()
    weth = old.WETH()
    btc = old.BTC()
    fresh = migration.deploy(
        "ChainlinkPrices",
        hq,
        migration.account(),
        PRICE_MIN_TIMELOCK,
        PRICE_MAX_TIMELOCK,
        weth,
        eth,
        btc,
        old.feedConfig(eth)[0],
        old.feedConfig(btc)[0],
        STALE_WINDOW_INHERIT,
        label=staged("ChainlinkPrices"),
    )

    core = {as_address(asset) for asset in (eth, weth, btc)}
    for asset in old.getPricedAssets():
        expected = chainlink_config(old.feedConfig(asset))
        if as_address(asset) in core:
            assert chainlink_config(fresh.feedConfig(asset)) == expected
            continue

        assert migration.execute_reconciled(
            fresh.addNewPriceFeed,
            lambda asset=asset, expected=expected: (
                int(fresh.pendingUpdates(asset)[0]) != 0
                or chainlink_config(fresh.feedConfig(asset)) == expected
            ),
            asset,
            expected[0],
            expected[4],
            expected[2],
            expected[3],
        )
        assert migration.execute_reconciled(
            fresh.confirmNewPriceFeed,
            lambda asset=asset, expected=expected: (
                chainlink_config(fresh.feedConfig(asset)) == expected
            ),
            asset,
        )

    assert tuple(map(as_address, fresh.getPricedAssets())) == tuple(
        map(as_address, old.getPricedAssets())
    )
    relinquish_governance(migration, fresh)
    return fresh


def relinquish_governance(migration, contract):
    assert as_address(contract.governance()) in (
        as_address(migration.account()),
        ZERO_ADDRESS,
    )
    assert migration.execute_reconciled(
        contract.relinquishGov,
        lambda: as_address(contract.governance()) == ZERO_ADDRESS,
    )
    assert as_address(contract.governance()) == ZERO_ADDRESS


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


def print_safe_batch(**fresh):
    log.info(f'const hq = c.Ripe_RH_RipeHq.at("{RIPE_HQ}")')
    log.info(f'const switchboard = c.Ripe_RH_Switchboard.at("{SWITCHBOARD}")')
    log.info(f'const priceDesk = c.Ripe_RH_PriceDesk.at("{PRICE_DESK}")')
    log.info(f'const vaultBook = c.Ripe_RH_VaultBook.at("{VAULT_BOOK}")')
    log.info("")

    log.info("// Start the nine RipeHq replacements")
    for name, reg_id in HQ_UPDATES:
        contract = fresh[camel_to_key(name)]
        log.info(
            f"await hq.startAddressUpdateToRegistry({reg_id}n, "
            f'"{contract.address}")  // {name}'
        )

    log.info("// Start the six child-registry replacements")
    for name, reg_id in SWITCHBOARD_UPDATES:
        board = fresh[camel_to_key(name)]
        log.info(
            f"await switchboard.startAddressUpdateToRegistry({reg_id}n, "
            f'"{board.address}")  // {name}'
        )
    log.info(
        "await priceDesk.startAddressUpdateToRegistry(1n, "
        f'"{fresh["chainlink"].address}")  // ChainlinkPrices'
    )
    log.info(
        "await vaultBook.startAddressUpdateToRegistry(1n, "
        f'"{fresh["stability_pool"].address}")  // StabilityPool'
    )
    log.info(
        "await vaultBook.startAddressUpdateToRegistry(2n, "
        f'"{fresh["ripe_gov"].address}")  // RipeGov'
    )
    log.info("")

    log.info("// Confirm every staged contract in dependency order")
    for name, reg_id in HQ_UPDATES:
        log.info(f"await hq.confirmAddressUpdateToRegistry({reg_id}n)  // {name}")
    for name, reg_id in SWITCHBOARD_UPDATES:
        log.info(
            f"await switchboard.confirmAddressUpdateToRegistry({reg_id}n)  "
            f"// {name}"
        )
    log.info("await priceDesk.confirmAddressUpdateToRegistry(1n)  // ChainlinkPrices")
    log.info("await vaultBook.confirmAddressUpdateToRegistry(1n)  // StabilityPool")
    log.info("await vaultBook.confirmAddressUpdateToRegistry(2n)  // RipeGov")
    log.info("")

    log.info("// Teller was deployed paused; reopen it only after activation")
    log.info(
        f'const charlie = c.Ripe_RH_SwitchboardCharlie.at("{fresh["charlie"].address}")'
    )
    log.info(f'await charlie.pause("{fresh["teller"].address}", false)')
    log.info("")
    log.info(
        "// Old Ledger and old RipeGov are intentionally left behind; "
        "governance will compensate the acknowledged holder later."
    )
    log.info("// Then run migration 2026082601 to authenticate and promote.")


def camel_to_key(name):
    return {
        "Ledger": "ledger",
        "MissionControl": "mission_control",
        "AuctionHouse": "auction_house",
        "CreditEngine": "credit_engine",
        "HumanResources": "human_resources",
        "Lootbox": "lootbox",
        "Teller": "teller",
        "Deleverage": "deleverage",
        "CreditRedeem": "credit_redeem",
        "SwitchboardAlpha": "alpha",
        "SwitchboardBravo": "bravo",
        "SwitchboardCharlie": "charlie",
        "SwitchboardDelta": "delta",
    }[name]
