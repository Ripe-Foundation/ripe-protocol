from pathlib import Path

import boa
import pytest

from constants import ZERO_ADDRESS


E18 = 10**18
PCT = 10_000
DAY_SECONDS = 86_400
WEEK_SECONDS = 604_800
MONTH_SECONDS = 2_592_000
YEAR_SECONDS = 31_536_000
HOUR_BLOCKS = 300
DAY_BLOCKS = 7_200
YEAR_BLOCKS = 2_628_000
DEFAULTS_DIR = Path(__file__).resolve().parents[2] / "contracts" / "config"


@pytest.fixture(scope="session")
def ripe_hq():
    """This runtime-defaults module does not need the protocol deployment graph."""


def _sentinels(prefix):
    names = ("ct", "tw", "ripe", "green", "sgreen", "usdg", "weth")
    values = tuple(boa.env.generate_address(f"rh-defaults-{prefix}-{name}") for name in names)
    assert len(set(values)) == len(values)
    assert ZERO_ADDRESS not in values
    return values


def _deploy(values):
    return boa.load("contracts/config/DefaultsRobinhood.vy", *values)


def _deploy_defaults_profile(path):
    deployer = boa.load_partial(str(path))
    init_function = deployer.compiler_data.global_ctx.init_function
    constructor_args = ()
    if init_function is not None:
        assert all(str(argument.typ) == "address" for argument in init_function.arguments)
        constructor_args = tuple(
            boa.env.generate_address(f"{path.stem}-{argument.name}")
            for argument in init_function.arguments
        )
    return deployer.deploy(*constructor_args)


def _has_ripe_bond_config(config):
    return any(
        (
            config.asset != ZERO_ADDRESS,
            config.amountPerEpoch != 0,
            config.canBond,
            config.minRipePerUnit != 0,
            config.maxRipePerUnit != 0,
            config.maxRipePerUnitLockBonus != 0,
            config.epochLength != 0,
            config.shouldAutoRestart,
            config.restartDelayBlocks != 0,
        )
    )


@pytest.fixture
def defaults_and_addresses():
    values = _sentinels("primary")
    return _deploy(values), values


def _assert_struct(actual, expected):
    """Assert every approved field explicitly, including nested structs."""
    assert tuple(actual._fields) == tuple(expected)
    for field, value in expected.items():
        observed = getattr(actual, field)
        if isinstance(value, dict):
            _assert_struct(observed, value)
        else:
            assert observed == value, field


GEN_CONFIG = {
    # D-01: approved Appendix A, Revision 6, pinned to RH 7d8c76e5.
    "perUserMaxVaults": 5,
    "perUserMaxAssetsPerVault": 15,
    "priceStaleTime": DAY_SECONDS,
    "canDeposit": True,
    "canWithdraw": True,
    "canBorrow": True,
    "canRepay": True,
    "canClaimLoot": True,
    "canLiquidate": True,
    "canRedeemCollateral": True,
    "canRedeemInStabPool": True,
    "canBuyInAuction": True,
    "canClaimInStabPool": True,
}

GEN_DEBT_CONFIG = {
    "perUserDebtLimit": 50 * E18,
    "globalDebtLimit": 500 * E18,
    "minDebtAmount": E18,
    "numAllowedBorrowers": 20,
    "maxBorrowPerInterval": 25 * E18,
    "numBlocksPerInterval": DAY_BLOCKS,
    "minDynamicRateBoost": PCT,
    "maxDynamicRateBoost": 5 * PCT,
    "increasePerDangerBlock": 60,
    "maxBorrowRate": PCT,
    "maxLtvDeviation": 10_00,
    "keeperFeeRatio": 1_00,
    "minKeeperFee": E18,
    "maxKeeperFee": 25_000 * E18,
    "isDaowryEnabled": True,
    "ltvPaybackBuffer": 10_00,
    "genAuctionParams": {
        "hasParams": True,
        "startDiscount": 1_00,
        "maxDiscount": 50_00,
        "delay": 0,
        "duration": DAY_BLOCKS,
    },
}

REWARDS_CONFIG = {
    "arePointsEnabled": True,
    "ripePerBlock": 9 * 10**15,
    "borrowersAlloc": 10_00,
    "stakersAlloc": 90_00,
    "votersAlloc": 0,
    "genDepositorsAlloc": 0,
    "autoStakeRatio": 75_00,
    "autoStakeDurationRatio": 33_00,
    "stabPoolRipePerDollarClaimed": E18,
}


def _auction_defaults():
    return {
        "hasParams": False,
        "startDiscount": 0,
        "maxDiscount": 0,
        "delay": 0,
        "duration": 0,
    }


def _asset_config(
    *,
    vault_ids,
    stakers_alloc,
    per_user_limit,
    global_limit,
    min_balance,
    debt_terms,
    burn=False,
    swap=False,
    auction=False,
    deposit=True,
    withdraw=True,
    redeem_collateral=False,
    redeem_stab=False,
    buy_auction=False,
    claim_stab=False,
):
    return {
        "vaultIds": vault_ids,
        "stakersPointsAlloc": stakers_alloc,
        "voterPointsAlloc": 0,
        "perUserDepositLimit": per_user_limit,
        "globalDepositLimit": global_limit,
        "minDepositBalance": min_balance,
        "debtTerms": debt_terms,
        "shouldBurnAsPayment": burn,
        "shouldTransferToEndaoment": False,
        "shouldSwapInStabPools": swap,
        "shouldAuctionInstantly": auction,
        "canDeposit": deposit,
        "canWithdraw": withdraw,
        "canRedeemCollateral": redeem_collateral,
        "canRedeemInStabPool": redeem_stab,
        "canBuyInAuction": buy_auction,
        "canClaimInStabPool": claim_stab,
        "specialStabPoolId": 0,
        "customAuctionParams": _auction_defaults(),
        "whitelist": ZERO_ADDRESS,
        "isNft": False,
    }


ZERO_DEBT_TERMS = {
    "ltv": 0,
    "redemptionThreshold": 0,
    "liqThreshold": 0,
    "liqFee": 0,
    "borrowRate": 0,
    "daowry": 0,
}


def _approved_asset_rows(addresses):
    _, _, ripe, green, sgreen, _, weth = addresses
    return (
        {
            "asset": weth,
            "config": _asset_config(
                vault_ids=[3],
                stakers_alloc=0,
                per_user_limit=25 * 10**17,
                global_limit=5 * E18,
                min_balance=5 * 10**14,
                debt_terms={
                    "ltv": 70_00,
                    "redemptionThreshold": 77_00,
                    "liqThreshold": 80_00,
                    "liqFee": 10_00,
                    "borrowRate": 7_00,
                    "daowry": 25,
                },
                swap=True,
                auction=True,
                redeem_collateral=True,
                redeem_stab=True,
                buy_auction=True,
                claim_stab=True,
            ),
        },
        {
            "asset": ripe,
            "config": _asset_config(
                vault_ids=[2],
                stakers_alloc=15_00,
                per_user_limit=100_000_000 * E18,
                global_limit=1_000_000_000 * E18,
                min_balance=10**14,
                debt_terms=ZERO_DEBT_TERMS,
                redeem_stab=True,
                buy_auction=True,
                claim_stab=True,
            ),
        },
        {
            "asset": sgreen,
            "config": _asset_config(
                vault_ids=[1],
                stakers_alloc=15_00,
                per_user_limit=100_000_000 * E18,
                global_limit=1_000_000_000 * E18,
                min_balance=10**16,
                debt_terms=ZERO_DEBT_TERMS,
                burn=True,
            ),
        },
        {
            "asset": green,
            "config": _asset_config(
                vault_ids=[],
                stakers_alloc=0,
                per_user_limit=1,
                global_limit=2,
                min_balance=1,
                debt_terms=ZERO_DEBT_TERMS,
                deposit=False,
                withdraw=False,
                claim_stab=True,
            ),
        },
    )


def test_constructor_bound_addresses_round_trip_through_runtime_getters():
    first = _sentinels("first")
    second = _sentinels("second")
    assert set(first).isdisjoint(second)

    for values in (first, second):
        defaults = _deploy(values)
        ct, tw, ripe, green, sgreen, usdg, weth = values
        assert defaults.hrConfig().contribTemplate == ct
        assert defaults.trainingWheels() == tw
        assert defaults.ripeBondConfig().asset == usdg
        assert [row.asset for row in defaults.ripeGovVaultConfigs()] == [ripe]
        assert [row.asset for row in defaults.assetConfigs()] == [weth, ripe, sgreen, green]
        assert [(row.vaultId, row.asset) for row in defaults.priorityLiqAssetVaults()] == [(3, weth)]
        assert [(row.vaultId, row.asset) for row in defaults.priorityStabVaults()] == [(1, sgreen)]


def test_every_configured_defaults_profile_has_nonzero_bond_epoch_length():
    configured_profiles = []
    for path in sorted(DEFAULTS_DIR.glob("Defaults*.vy")):
        config = _deploy_defaults_profile(path).ripeBondConfig()
        if not _has_ripe_bond_config(config):
            continue

        configured_profiles.append(path.name)
        # Bonding may be disabled through canBond; zero is never an epoch sentinel.
        assert config.epochLength != 0, path.name

    assert set(configured_profiles) == {
        "DefaultsBase.vy",
        "DefaultsBaseLive.vy",
        "DefaultsRobinhood.vy",
        "DefaultsRobinhoodLive.vy",
    }


def test_general_and_debt_defaults_match_approved_values(defaults_and_addresses):
    defaults, _ = defaults_and_addresses
    _assert_struct(defaults.genConfig(), GEN_CONFIG)
    _assert_struct(defaults.genDebtConfig(), GEN_DEBT_CONFIG)


def test_ripe_allocations_and_rewards_defaults_match_approved_values(defaults_and_addresses):
    defaults, _ = defaults_and_addresses
    assert defaults.ripeAvailForRewards() == 1_000_000 * E18
    assert defaults.ripeAvailForHr() == 0
    assert defaults.ripeAvailForBonds() == 1_000_000 * E18
    rewards = defaults.rewardsConfig()
    _assert_struct(rewards, REWARDS_CONFIG)
    assert sum((rewards.borrowersAlloc, rewards.stakersAlloc, rewards.votersAlloc, rewards.genDepositorsAlloc)) == PCT


def test_bond_hr_and_governance_defaults_match_approved_values(defaults_and_addresses):
    defaults, addresses = defaults_and_addresses
    ct, tw, ripe, _, _, usdg, _ = addresses
    _assert_struct(
        defaults.ripeBondConfig(),
        {
            "asset": usdg,
            "amountPerEpoch": 100 * 10**6,
            "canBond": False,
            "minRipePerUnit": 0,
            "maxRipePerUnit": 50 * E18,
            "maxRipePerUnitLockBonus": 2 * PCT,
            "epochLength": 8 * HOUR_BLOCKS,
            "shouldAutoRestart": True,
            "restartDelayBlocks": 2 * HOUR_BLOCKS,
        },
    )
    gov_rows = defaults.ripeGovVaultConfigs()
    assert len(gov_rows) == 1
    _assert_struct(
        gov_rows[0],
        {
            "asset": ripe,
            "config": {
                "lockTerms": {
                    "minLockDuration": DAY_BLOCKS,
                    "maxLockDuration": 3 * YEAR_BLOCKS,
                    "maxLockBoost": 2 * PCT,
                    "canExit": True,
                    "exitFee": 80_00,
                },
                "assetWeight": PCT,
                "shouldFreezeWhenBadDebt": True,
            },
        },
    )
    _assert_struct(
        defaults.hrConfig(),
        {
            "contribTemplate": ct,
            "maxCompensation": 0,
            "minCliffLength": WEEK_SECONDS,
            "maxStartDelay": 3 * MONTH_SECONDS,
            "minVestingLength": WEEK_SECONDS,
            "maxVestingLength": 10 * YEAR_SECONDS,
        },
    )
    assert defaults.underscoreRegistry() == ZERO_ADDRESS
    assert defaults.trainingWheels() == tw
    assert defaults.shouldCheckLastTouch() is True


def test_asset_configs_match_approved_rows_order_and_values(defaults_and_addresses):
    defaults, addresses = defaults_and_addresses
    actual = defaults.assetConfigs()
    expected = _approved_asset_rows(addresses)
    assert len(actual) == len(expected) == 4
    for row, expected_row in zip(actual, expected, strict=True):
        _assert_struct(row, expected_row)


def test_priority_defaults_and_lite_signers_match_approved_values(defaults_and_addresses):
    defaults, addresses = defaults_and_addresses
    _, _, _, _, sgreen, _, weth = addresses
    assert [(row.vaultId, row.asset) for row in defaults.priorityLiqAssetVaults()] == [(3, weth)]
    assert [(row.vaultId, row.asset) for row in defaults.priorityStabVaults()] == [(1, sgreen)]
    assert defaults.priorityPriceSourceIds() == [1, 2]
    assert defaults.liteSigners() == []


def test_defaults_cross_field_invariants_hold_at_runtime(defaults_and_addresses):
    defaults, addresses = defaults_and_addresses
    debt = defaults.genDebtConfig()
    assert debt.perUserDebtLimit <= debt.globalDebtLimit
    assert debt.minDynamicRateBoost <= debt.maxDynamicRateBoost
    assert debt.minKeeperFee <= debt.maxKeeperFee
    assert debt.genAuctionParams.startDiscount <= debt.genAuctionParams.maxDiscount

    rewards = defaults.rewardsConfig()
    assert sum((rewards.borrowersAlloc, rewards.stakersAlloc, rewards.votersAlloc, rewards.genDepositorsAlloc)) == PCT

    rows = defaults.assetConfigs()
    assert [row.config.vaultIds for row in rows] == [[3], [2], [1], []]
    for row in rows:
        terms = row.config.debtTerms
        assert terms.ltv <= terms.redemptionThreshold <= terms.liqThreshold
        auction = row.config.customAuctionParams
        assert auction.startDiscount <= auction.maxDiscount

    assert all(address != ZERO_ADDRESS for address in addresses)
