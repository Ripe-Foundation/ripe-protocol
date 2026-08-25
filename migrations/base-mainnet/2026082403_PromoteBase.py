"""Authenticate the Base generation after the Safe activates it.

This migration sends no governance transaction.  It only reads the live
registries, checks the complete generation, and promotes the authenticated
candidates to their normal manifest names.
"""

from scripts.utils import log
from scripts.utils.migration import Migration, PromotionSpec


ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
CANDIDATE_SUFFIX = "Candidate2026082402"

# Retained live contracts.
RIPE_HQ = "0x6162df1b329E157479F8f1407E888260E0EC3d2b"
LEDGER = "0x365256e322a47Aa2015F6724783F326e9B24fA47"
GREEN = "0xd1Eac76497D06Cf15475A5e3984D5bC03de7C707"
SAVINGS_GREEN = "0xaa0f13488CE069A7B5a099457c753A7CFBE04d36"
RIPE = "0x2A0a59d6B975828e781EcaC125dBA40d7ee5dDC0"
GREEN_POOL = "0xd6c283655B42FA0eb2685F7AB819784F071459dc"
RIPE_WETH_POOL = "0x765824aD2eD0ECB70ECc25B0Cf285832b335d6A9"
RIPE_CCIP_POOL = "0x6E3f8465aF365a2C400C361783ea51ad44b3C836"
GREEN_CCIP_POOL = "0xEF56E5036728718Baa577257Ff4FA9259E9e895f"

ACTIVE_CHAINLINK = "0xD11B23b6391e294DF49961E64231bddDE5bB5E89"
ACTIVE_CURVE = "0x7B2aeE8B6A4bdF0885dEF48CCda8453Fdc1Bba5d"
ACTIVE_PYTH = "0x16371fAf6f603f8d8D6cef8C46253c80AdEe8b98"
ACTIVE_STORK = "0xceE8Ed804f72b6EcB6B2D679ca17B545bD654bF6"
ACTIVE_UNDY = "0x64D0F785c3D4bf4675f4b8432D765175F014A8Ac"
ACTIVE_REDSTONE = "0x9f20F25f037046721A292B19A486932ef390EAf9"

SOURCE_VAULTS = (
    (1, "0x2a157096af6337b2b4bd47de435520572ed5a439"),
    (2, "0xe42b3dC546527EB70D741B185Dc57226cA01839D"),
    (3, "0xf75b566eF80Fde0dEfcC045A4d57b540eb43ddfD"),
    (4, "0xce2E96C9F6806731914A7b4c3E4aC1F296d98597"),
    (5, "0x4549A368c00f803862d457C4C0c659a293F26C66"),
)

# Constructor inputs.  They intentionally match 2026082402 verbatim.
DEPLOYER = "0xEF3cB7750FF6158d9f9B27651BbBA2299096483B"
REGISTRY_MIN_DELAY = 3_600
REGISTRY_MAX_DELAY = 302_400
ACTION_MIN_DELAY = 3_600
ACTION_MAX_DELAY = 302_400
STALE_TIME_MIN = 5 * 60
STALE_TIME_MAX = 7 * 24 * 60 * 60
DEFAULT_STALE_TIME = 24 * 60 * 60
CURVE_PRICES_ID = 2
PYTH_PRICES_ID = 4

ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"
WETH = "0x4200000000000000000000000000000000000006"
BTC = "0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB"
ETH_USD_FEED = "0x71041dddad3595F9CEd3DcCFBe3D1F4b0a16Bb70"
BTC_USD_FEED = "0x64c911996D3c6aC71f9b455B1E8E7266BcbD848F"
PYTH = "0x8250f4aF4B972684F7b336503E2D6dFeDeB1487a"
STORK = "0x647DFd812BC1e116c6992CB2bC353b2112176fD6"
CURVE_ADDRESS_PROVIDER = "0x5ffe7FB82894076ECB99A30D6A32e969e6e35E98"

MCBETH = "0x3bf93770f2d4a794c3d9EBEfBAeBAE2a8f09A5E5"
SUPER_OETH = "0xDBFeFD2e8460a6Ee4955A68582F85708BAEA60A3"
WRAPPED_SUPER_OETH = "0x7FcD174E80f264448ebeE8c88a7C4476AAF58Ea6"
VVV = "0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf"

MORPHO_FACTORIES = (
    "0xFf62A7c278C62eD665133147129245053Bbf5918",
    "0xA9c3D3a366466Fa809d1Ae982Fb2c46E5fC41101",
)
EULER_FACTORIES = (
    "0x7F321498A801A191a93C840750ed637149dDf8D0",
    "0x72bbDB652F2AEC9056115644EfCcDd1986F51f15",
)
FLUID_RESOLVER = "0x3aF6FBEc4a2FE517F56E402C65e3f4c3e18C1D86"
COMPOUND_V3_CONFIGURATOR = "0x45939657d1CA34A8FA39A924B71D28Fe8431e581"
MOONWELL_COMPTROLLER = "0xfBb21d0380beE3312B33c4353c8936a0F13EF26C"
AAVE_V3_ADDRESS_PROVIDER = "0xe20fCBdBfFC4Dd138cE8b2E6FBb6CB49777ad64D"

BOND_BOOSTER_ARGS = (20_000, 25_000, 7_776_000)
LOOTBOX_ARGS = (43_200, 43_200, 25 * 10**18, 150 * 10**18)
DELEVERAGE_ARGS = (0, 0, 0, 100, 10**15, 100, 0, 0)
PSM_ARGS = (
    43_200,
    0,
    20_000 * 10**18,
    0,
    100_000 * 10**18,
    "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    13,
    "0x99e65176F7FA8743E3fbaEF277d1Da448e361367",
)


def candidate(name):
    return f"{name}{CANDIDATE_SUFFIX}"


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq", RIPE_HQ)
    deployer = migration.account()
    assert _address(deployer) == _address(DEPLOYER)

    # ------------------------------------------------------------------
    # 1. Prove that only the intended RipeHq generation changed.
    # ------------------------------------------------------------------
    log.h1("1. Reading the activated Base generation")
    for registry_id, retained in (
        (1, GREEN),
        (2, SAVINGS_GREEN),
        (3, RIPE),
        (4, LEDGER),
        (23, RIPE_CCIP_POOL),
        (24, GREEN_CCIP_POOL),
    ):
        assert _address(hq.getAddr(registry_id)) == _address(retained)

    hq_components = (
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
        ("VaultMigrator", 25),
    )
    for name, registry_id in hq_components:
        assert _address(hq.getAddr(registry_id)) == _address(
            migration.get_address(candidate(name))
        )

    # ------------------------------------------------------------------
    # 2. Prove the child registry topology, including both vault generations.
    # ------------------------------------------------------------------
    log.h1("2. Reading Switchboard, PriceDesk, and VaultBook")
    switchboard = _finalized_registry(
        migration,
        "Switchboard",
        (
            (1, candidate("SwitchboardAlpha")),
            (2, candidate("SwitchboardBravo")),
            (3, candidate("SwitchboardCharlie")),
            (4, candidate("SwitchboardDelta")),
            (5, candidate("SwitchboardEcho")),
        ),
        expected_num_addrs=6,
    )
    price_desk = _finalized_registry(
        migration,
        "PriceDesk",
        (
            (1, candidate("ChainlinkPrices")),
            (2, candidate("CurvePrices")),
            (3, None),
            (4, candidate("PythPrices")),
            (5, candidate("StorkPrices")),
            (6, candidate("AeroRipePrices")),
            (7, candidate("wsuperOETHbPrices")),
            (8, candidate("UndyVaultPrices")),
            (9, candidate("RedStone")),
        ),
        expected_num_addrs=10,
    )
    vault_book = _finalized_registry(
        migration,
        "VaultBook",
        (
            *SOURCE_VAULTS,
            (6, candidate("StabilityPool")),
            (7, candidate("RipeGov")),
            (8, candidate("SimpleErc20")),
            (9, candidate("RebaseErc20")),
            (10, candidate("UnderscoreVault")),
        ),
        expected_num_addrs=11,
    )

    # Local deployer governance is gone.  HQ governance remains authoritative,
    # and setup timelocks deliberately remain zero as requested.
    for name in (
        "SwitchboardAlpha",
        "SwitchboardBravo",
        "SwitchboardCharlie",
        "SwitchboardDelta",
        "SwitchboardEcho",
        "ChainlinkPrices",
        "CurvePrices",
        "BlueChipYieldPrices",
        "PythPrices",
        "StorkPrices",
        "wsuperOETHbPrices",
        "UndyVaultPrices",
        "RedStone",
    ):
        contract = migration.get_contract(candidate(name))
        assert _address(contract.governance()) == ZERO_ADDRESS
        assert int(contract.actionTimeLock()) == 0

    human_resources = migration.get_contract(candidate("HumanResources"))
    assert _address(human_resources.governance()) == ZERO_ADDRESS
    assert int(human_resources.actionTimeLock()) == 0

    teller = migration.get_contract(candidate("Teller"))
    vault_migrator = migration.get_contract(candidate("VaultMigrator"))
    assert teller.isPaused()
    assert not vault_migrator.isPaused()

    # ------------------------------------------------------------------
    # 3. Prove that the mutable price routes were copied before promotion.
    # ------------------------------------------------------------------
    log.h1("3. Comparing the live and replacement price routes")
    _same_feed_state(
        migration.get_contract("ChainlinkPrices", ACTIVE_CHAINLINK),
        migration.get_contract(candidate("ChainlinkPrices")),
        "feedConfig",
    )
    _same_feed_state(
        migration.get_contract("CurvePrices", ACTIVE_CURVE),
        migration.get_contract(candidate("CurvePrices")),
        "curveConfig",
    )
    old_curve = migration.get_contract("CurvePrices", ACTIVE_CURVE)
    new_curve = migration.get_contract(candidate("CurvePrices"))
    assert _normalized(old_curve.greenRefPoolConfig()) == _normalized(
        new_curve.greenRefPoolConfig()
    )
    for old_name, old_address, getter in (
        ("PythPrices", ACTIVE_PYTH, "feedConfig"),
        ("StorkPrices", ACTIVE_STORK, "feedConfig"),
        ("RedStone", ACTIVE_REDSTONE, "feedConfig"),
    ):
        _same_feed_state(
            migration.get_contract(old_name, old_address),
            migration.get_contract(candidate(old_name)),
            getter,
        )
    _same_undy_feed_policy(
        migration.get_contract("UndyVaultPrices", ACTIVE_UNDY),
        migration.get_contract(candidate("UndyVaultPrices")),
    )

    # ------------------------------------------------------------------
    # 4. Authenticate code, constructors, dependencies, and registry slots.
    # ------------------------------------------------------------------
    log.h1("4. Promoting the authenticated generation")
    defaults = migration.get_address(candidate("DefaultsBaseLive"))
    contributor = migration.get_address("Contributor")
    bond_booster = migration.get_address(candidate("BondBooster"))

    hq_args = {
        "MissionControl": (hq, defaults),
        "Switchboard": (
            hq, deployer, REGISTRY_MIN_DELAY, REGISTRY_MAX_DELAY,
        ),
        "PriceDesk": (
            hq, deployer, ETH, REGISTRY_MIN_DELAY, REGISTRY_MAX_DELAY,
        ),
        "VaultBook": (
            hq, deployer, REGISTRY_MIN_DELAY, REGISTRY_MAX_DELAY,
        ),
        "AuctionHouse": (hq,),
        "AuctionHouseNFT": (hq,),
        "Boardroom": (hq,),
        "BondRoom": (hq, bond_booster),
        "CreditEngine": (hq, CURVE_PRICES_ID),
        "Endaoment": (hq, WETH, ETH, CURVE_PRICES_ID),
        "HumanResources": (hq, ACTION_MIN_DELAY, ACTION_MAX_DELAY),
        "Lootbox": (hq, *LOOTBOX_ARGS),
        "Teller": (hq, True, CURVE_PRICES_ID),
        "Deleverage": (hq, *DELEVERAGE_ARGS),
        "CreditRedeem": (hq,),
        "TellerUtils": (hq,),
        "EndaomentFunds": (hq,),
        "EndaomentPSM": (hq, *PSM_ARGS),
        "VaultMigrator": (hq, False, SOURCE_VAULTS[1][1]),
    }
    hq_paths = {
        "MissionControl": "contracts/data/MissionControl.vy",
        "Switchboard": "contracts/registries/Switchboard.vy",
        "PriceDesk": "contracts/registries/PriceDesk.vy",
        "VaultBook": "contracts/registries/VaultBook.vy",
        "AuctionHouse": "contracts/core/AuctionHouse.vy",
        "AuctionHouseNFT": "contracts/core/AuctionHouseNFT.vy",
        "Boardroom": "contracts/core/Boardroom.vy",
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
        "VaultMigrator": "contracts/core/VaultMigrator.vy",
    }
    promotions = [
        _spec(name, hq_paths[name], "RipeHq", hq, registry_id, hq_args[name])
        for name, registry_id in hq_components
    ]

    switchboard_args = {
        "SwitchboardAlpha": (
            hq, deployer, STALE_TIME_MIN, STALE_TIME_MAX,
            ACTION_MIN_DELAY, ACTION_MAX_DELAY, PYTH_PRICES_ID,
        ),
        **{
            name: (hq, deployer, ACTION_MIN_DELAY, ACTION_MAX_DELAY)
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
            f"contracts/config/{name}.vy",
            candidate("Switchboard"),
            switchboard,
            registry_id,
            switchboard_args[name],
        )
        for name, registry_id in (
            ("SwitchboardAlpha", 1),
            ("SwitchboardBravo", 2),
            ("SwitchboardCharlie", 3),
            ("SwitchboardDelta", 4),
            ("SwitchboardEcho", 5),
        )
    )

    price_specs = (
        (
            "ChainlinkPrices", 1, "contracts/priceSources/ChainlinkPrices.vy",
            (
                hq, deployer, REGISTRY_MIN_DELAY, REGISTRY_MAX_DELAY,
                WETH, ETH, BTC, ETH_USD_FEED, BTC_USD_FEED,
                DEFAULT_STALE_TIME,
            ),
        ),
        (
            "CurvePrices", 2, "contracts/priceSources/CurvePrices.vy",
            (
                hq, deployer, CURVE_ADDRESS_PROVIDER, GREEN, SAVINGS_GREEN,
                REGISTRY_MIN_DELAY, REGISTRY_MAX_DELAY,
            ),
        ),
        (
            "PythPrices", 4, "contracts/priceSources/PythPrices.vy",
            (
                hq, deployer, PYTH, REGISTRY_MIN_DELAY, REGISTRY_MAX_DELAY,
            ),
        ),
        (
            "StorkPrices", 5, "contracts/priceSources/StorkPrices.vy",
            (
                hq, deployer, STORK, REGISTRY_MIN_DELAY, REGISTRY_MAX_DELAY,
            ),
        ),
        (
            "AeroRipePrices", 6, "contracts/priceSources/AeroRipePrices.vy",
            (hq, RIPE_WETH_POOL, RIPE, WETH),
        ),
        (
            "wsuperOETHbPrices", 7,
            "contracts/priceSources/wsuperOETHbPrices.vy",
            (
                hq, MCBETH, SUPER_OETH, WRAPPED_SUPER_OETH, VVV,
                REGISTRY_MIN_DELAY, REGISTRY_MAX_DELAY,
            ),
        ),
        (
            "UndyVaultPrices", 8,
            "contracts/priceSources/UndyVaultPrices.vy",
            (hq, deployer, REGISTRY_MIN_DELAY, REGISTRY_MAX_DELAY),
        ),
        (
            "RedStone", 9, "contracts/priceSources/RedStone.vy",
            (hq, deployer, ETH, REGISTRY_MIN_DELAY, REGISTRY_MAX_DELAY),
        ),
    )
    promotions.extend(
        _spec(
            name, path, candidate("PriceDesk"), price_desk,
            registry_id, args,
        )
        for name, registry_id, path, args in price_specs
    )

    vault_specs = (
        ("StabilityPool", "StabilityPool", 6, "contracts/vaults/StabilityPool.vy"),
        ("RipeGov", "RipeGov", 7, "contracts/vaults/RipeGov.vy"),
        ("SimpleErc20", "SimpleErc20", 8, "contracts/vaults/SimpleErc20.vy"),
        ("RebaseErc20", "RebaseErc20", 9, "contracts/vaults/RebaseErc20.vy"),
        (
            "Underscore Vault", "UnderscoreVault", 10,
            "contracts/vaults/SimpleErc20.vy",
        ),
    )
    promotions.extend(
        _spec(
            canonical_name,
            path,
            candidate("VaultBook"),
            vault_book,
            registry_id,
            (hq,),
            candidate_name=candidate_name,
            source_contract_name=(
                "SimpleErc20" if canonical_name == "Underscore Vault" else None
            ),
        )
        for canonical_name, candidate_name, registry_id, path in vault_specs
    )

    # Defaults and BondBooster have no direct slot.  Their independently
    # authenticated consumers are the registry witnesses.
    promotions.extend(
        (
            PromotionSpec(
                canonical_name="DefaultsBaseLive",
                expected_source_path="contracts/config/DefaultsBaseLive.vy",
                candidate_label=candidate("DefaultsBaseLive"),
                registry_name="RipeHq",
                registry=hq,
                registry_id=5,
                expected_constructor_args=(contributor,),
                activation_candidate_label=candidate("MissionControl"),
                activation_dependency_arg_index=1,
                activation_expected_constructor_args=(hq, defaults),
            ),
            PromotionSpec(
                canonical_name="BondBooster",
                expected_source_path="contracts/config/BondBooster.vy",
                candidate_label=candidate("BondBooster"),
                registry_name="RipeHq",
                registry=hq,
                registry_id=12,
                expected_constructor_args=(hq, *BOND_BOOSTER_ARGS),
                activation_candidate_label=candidate("BondRoom"),
                activation_dependency_arg_index=1,
                activation_expected_constructor_args=(hq, bond_booster),
            ),
        )
    )

    assert len(promotions) == 39
    migration.promote_candidates(promotions)

    # ------------------------------------------------------------------
    # 5. Leave the position-moving phase as a short, visible handoff.
    # ------------------------------------------------------------------
    log.h1("5. Vault migration handoff")
    log.info("The deployment is authenticated; Teller is still paused.")
    log.info("First add target ids 6-10 to the matching asset deposit routes.")
    log.info("Then set preferredStabVaultId=6 and coreRipeGovVaultId=7.")
    log.info("1 -> 6  StabilityPool: echo.migrateVaultPositions(users, 1n, 6n)")
    log.info("2 -> 7  Legacy RipeGov: echo.migrateLegacyRipeGovPositions(users)")
    log.info("3 -> 8  SimpleErc20: echo.migrateVaultPositions(users, 3n, 8n)")
    log.info("4 -> 9  RebaseErc20: echo.migrateVaultPositions(users, 4n, 9n)")
    log.info("5 -> 10 Underscore: echo.migrateVaultPositions(users, 5n, 10n)")
    log.info("Keep Teller and target RipeGov paused during the legacy route.")


def _spec(
    canonical_name,
    path,
    registry_name,
    registry,
    registry_id,
    args,
    *,
    candidate_name=None,
    source_contract_name=None,
):
    return PromotionSpec(
        canonical_name=canonical_name,
        expected_source_path=path,
        candidate_label=candidate(candidate_name or canonical_name),
        registry_name=registry_name,
        registry=registry,
        registry_id=registry_id,
        expected_constructor_args=args,
        source_contract_name=source_contract_name,
    )


def _finalized_registry(
    migration,
    root_name,
    expected_slots,
    *,
    expected_num_addrs,
):
    root = migration.get_contract(candidate(root_name))
    assert int(root.numAddrs()) == expected_num_addrs
    for registry_id, expected in expected_slots:
        expected_address = (
            ZERO_ADDRESS
            if expected is None
            else migration.get_address(expected)
            if isinstance(expected, str) and expected.endswith(CANDIDATE_SUFFIX)
            else expected
        )
        assert _address(root.getAddr(registry_id)) == _address(expected_address)
    assert int(root.registryChangeTimeLock()) == 0
    assert _address(root.governance()) == ZERO_ADDRESS
    return root


def _same_feed_state(old, new, getter_name):
    old_assets = tuple(old.getPricedAssets())
    new_assets = tuple(new.getPricedAssets())
    assert tuple(map(_address, old_assets)) == tuple(map(_address, new_assets))
    old_getter = getattr(old, getter_name)
    new_getter = getattr(new, getter_name)
    for asset in old_assets:
        assert _normalized(old_getter(asset)) == _normalized(new_getter(asset))


def _same_undy_feed_policy(old, new):
    """Compare immutable feed policy, not the intentionally fresh snapshots."""
    old_assets = tuple(old.getPricedAssets())
    new_assets = tuple(new.getPricedAssets())
    assert tuple(map(_address, old_assets)) == tuple(map(_address, new_assets))
    for asset in old_assets:
        old_config = tuple(old.priceConfigs(asset))
        new_config = tuple(new.priceConfigs(asset))
        assert _normalized(old_config[:7]) == _normalized(new_config[:7])
        assert int(new.getPrice(asset)) != 0


def _normalized(value):
    if isinstance(value, str) and value.startswith("0x"):
        return value.lower()
    if isinstance(value, (tuple, list)):
        return tuple(_normalized(item) for item in value)
    return value


def _address(value):
    return str(getattr(value, "address", value)).lower()
