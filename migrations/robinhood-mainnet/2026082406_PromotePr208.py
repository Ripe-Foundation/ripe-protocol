"""Authenticate and promote the eleven activated PR-208 replacements."""

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

CANONICAL_SOURCE_PATHS = {
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


def candidate_label(name):
    return f"{name}{CANDIDATE_SUFFIX}"


def _as_address(value):
    return str(getattr(value, "address", value)).lower()


def _normalized(value):
    if isinstance(value, str) and value.startswith("0x") and len(value) == 42:
        return value.lower()
    if isinstance(value, (tuple, list)):
        return tuple(_normalized(item) for item in value)
    return value


def _assert_tree(root, expected):
    for reg_id, address in expected:
        assert _as_address(root.getAddr(reg_id)) == _as_address(address)
    assert int(root.registryChangeTimeLock()) == 0
    assert _as_address(root.governance()) == ZERO_ADDRESS


def _assert_oracles_cloned(migration):
    active_chainlink = migration.get_contract("ChainlinkPrices")
    fresh_chainlink = migration.get_contract(candidate_label("ChainlinkPrices"))
    active_assets = tuple(active_chainlink.getPricedAssets())
    fresh_assets = tuple(fresh_chainlink.getPricedAssets())
    assert tuple(map(_as_address, fresh_assets)) == tuple(map(_as_address, active_assets))
    for asset in active_assets:
        active = active_chainlink.feedConfig(asset)
        fresh = fresh_chainlink.feedConfig(asset)
        assert _as_address(fresh[0]) == _as_address(active[0])
        assert int(fresh[1]) == int(active[1])
        assert bool(fresh[2]) == bool(active[2])
        assert bool(fresh[3]) == bool(active[3])
        assert int(fresh[4]) == stale_time_override_for_asset(str(asset))

    active_curve = migration.get_contract("CurvePrices")
    fresh_curve = migration.get_contract(candidate_label("CurvePrices"))
    active_assets = tuple(active_curve.getPricedAssets())
    fresh_assets = tuple(fresh_curve.getPricedAssets())
    assert tuple(map(_as_address, fresh_assets)) == tuple(map(_as_address, active_assets))
    for asset in active_assets:
        assert _normalized(fresh_curve.curveConfig(asset)) == _normalized(
            active_curve.curveConfig(asset)
        )
    assert _normalized(fresh_curve.greenRefPoolConfig()) == _normalized(
        active_curve.greenRefPoolConfig()
    )


def _is_nft(config):
    return bool(config.isNft) if hasattr(config, "isNft") else bool(config[-1])


def _assert_token_scales_cloned(migration, fresh_price_desk, eth):
    active_price_desk = migration.get_contract("PriceDesk")
    mission_control = migration.get_contract("MissionControl")
    assets = [
        mission_control.assets(index)
        for index in range(1, int(mission_control.numAssets()))
    ]
    assets.append(migration.get_contract("EndaomentPSM").USDC())
    checked = set()
    for asset in assets:
        normalized = _as_address(asset)
        if normalized in checked or normalized in (ZERO_ADDRESS, _as_address(eth)):
            continue
        if _is_nft(mission_control.assetConfig(asset)):
            continue
        checked.add(normalized)
        active_scale = int(active_price_desk.tokenScale(asset))
        assert active_scale != 0
        assert int(fresh_price_desk.tokenScale(asset)) == active_scale


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
    hq = migration.get_contract("RipeHq")
    switchboard = migration.get_contract("Switchboard")
    price_desk = migration.get_contract(candidate_label("PriceDesk"))
    vault_book = migration.get_contract(candidate_label("VaultBook"))
    deployer = migration.account()

    active_price_desk = migration.get_contract("PriceDesk")
    active_chainlink = migration.get_contract("ChainlinkPrices")
    eth = active_price_desk.ETH()
    weth = active_chainlink.WETH()
    btc = active_chainlink.BTC()
    eth_feed = active_chainlink.feedConfig(eth)[0]
    btc_feed = active_chainlink.feedConfig(btc)[0]

    _assert_tree(
        price_desk,
        (
            (1, migration.get_address(candidate_label("ChainlinkPrices"))),
            (2, migration.get_address(candidate_label("CurvePrices"))),
            (3, migration.get_address("UniswapV2Prices")),
        ),
    )
    _assert_tree(
        vault_book,
        (
            (1, migration.get_address(candidate_label("StabilityPool"))),
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
        contract = migration.get_contract(candidate_label(name))
        assert int(contract.actionTimeLock()) == 0
        assert _as_address(contract.governance()) == ZERO_ADDRESS
    assert not bool(migration.get_contract(candidate_label("Teller")).isPaused())
    assert not bool(
        migration.get_contract(candidate_label("StabilityPool")).doesVaultHaveAnyFunds()
    )
    _assert_oracles_cloned(migration)
    _assert_token_scales_cloned(migration, price_desk, eth)

    switchboard_args = {
        "SwitchboardAlpha": (
            hq,
            deployer,
            STALE_WINDOW_MIN,
            STALE_WINDOW_MAX,
            SWITCHBOARD_MIN_TIMELOCK,
            SWITCHBOARD_MAX_TIMELOCK,
            PYTH_PRICES_ID,
        ),
        "SwitchboardBravo": (
            hq,
            deployer,
            SWITCHBOARD_MIN_TIMELOCK,
            SWITCHBOARD_MAX_TIMELOCK,
        ),
        "SwitchboardCharlie": (
            hq,
            deployer,
            SWITCHBOARD_MIN_TIMELOCK,
            SWITCHBOARD_MAX_TIMELOCK,
        ),
    }
    promotions = [
        _spec(name, "Switchboard", switchboard, reg_id, switchboard_args[name])
        for name, reg_id in (
            ("SwitchboardAlpha", 1),
            ("SwitchboardBravo", 2),
            ("SwitchboardCharlie", 3),
        )
    ]
    promotions.extend(
        (
            _spec(
                "PriceDesk",
                "RipeHq",
                hq,
                7,
                (hq, deployer, eth, REGISTRY_MIN_DELAY, REGISTRY_MAX_DELAY),
            ),
            _spec(
                "ChainlinkPrices",
                candidate_label("PriceDesk"),
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
                    eth_feed,
                    btc_feed,
                    STALE_WINDOW_INHERIT,
                ),
            ),
            _spec(
                "CurvePrices",
                candidate_label("PriceDesk"),
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
            _spec(
                "VaultBook",
                "RipeHq",
                hq,
                8,
                (hq, deployer, REGISTRY_MIN_DELAY, REGISTRY_MAX_DELAY),
            ),
            _spec(
                "StabilityPool",
                candidate_label("VaultBook"),
                vault_book,
                1,
                (hq,),
            ),
            _spec("CreditEngine", "RipeHq", hq, 13, (hq, CURVE_PRICES_ID)),
            _spec(
                "Endaoment",
                "RipeHq",
                hq,
                14,
                (hq, weth, eth, CURVE_PRICES_ID),
            ),
            _spec(
                "Teller",
                "RipeHq",
                hq,
                17,
                (hq, TELLER_SHOULD_PAUSE, CURVE_PRICES_ID),
            ),
        )
    )

    assert len(promotions) == len(CANONICAL_SOURCE_PATHS) == 11
    log.h1("Authenticating and promoting the eleven PR-208 replacements")
    migration.promote_candidates(promotions)
