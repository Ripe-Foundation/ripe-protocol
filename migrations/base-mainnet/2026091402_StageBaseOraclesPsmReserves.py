"""Deploy the remaining Base oracle and treasury candidates; no activation."""

import boa
from boa.contracts.abi.abi_contract import ABIContractFactory
from scripts.utils import log
from scripts.utils.migration import Migration

ZERO = "0x" + "00" * 20
SUFFIX = "BaseUpgradeCandidate20260914"
USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

# Constructor-only placeholder. Sales stay PAUSED, with no allocation or mint
# permission. These are NOT approved launch economics; configure before launch.
DORMANT_RESERVE_CONFIG = (
    1_000_000, 1_000_000, 10**18, 10**18,
    6000, 4000, 1000, 3000, 300, 800, 800, 4,
    0, 43_200, 1_296_000, 43_200,
)


def migrate(migration: Migration):
    log.h1("1. Read Base's existing price sources and PSM")
    if migration.chain() != "base-mainnet":
        raise RuntimeError("BASE_UPGRADE_WRONG_PROFILE")
    hq = migration.get_contract("RipeHq")
    old_desk = migration.get_contract("PriceDesk", hq.getAddr(7))
    psm = migration.get_contract("EndaomentPSM", hq.getAddr(22))
    assert str(psm.USDC()).lower() == USDC.lower()
    params = migration.blueprint().PARAMS
    min_lock = params["MIN_SWITCHBOARD_CHANGE_TIMELOCK"]
    max_lock = params["MAX_SWITCHBOARD_CHANGE_TIMELOCK"]
    old = {}
    for name in ("ChainlinkPrices", "CurvePrices", "BlueChipYieldPrices",
                 "PythPrices", "StorkPrices", "wsuperOETHbPrices", "RedStone", "UndyVaultPrices"):
        source = migration.get_contract(name)
        if name == "BlueChipYieldPrices":
            # Slot 3 is intentionally disabled on live Base. Deploy its new
            # code, but do not re-enable the source when preparing PriceDesk.
            assert str(old_desk.getAddr(3)).lower() == ZERO
        else:
            assert int(old_desk.getRegId(source.address)) != 0, f"inactive source: {name}"
        old[name] = source
    chainlink = old["ChainlinkPrices"]
    eth, btc = chainlink.ETH(), chainlink.BTC()
    eth_config, btc_config = chainlink.feedConfig(eth), chainlink.feedConfig(btc)
    assert not eth_config[2] and not eth_config[3]
    assert not btc_config[2] and not btc_config[3]
    blue = old["BlueChipYieldPrices"]
    # The deployed generation exposes indexed array getters; today's source
    # returns whole arrays. Use the legacy ABI for these two reads only.
    blue_arrays = ABIContractFactory("LegacyBlueChipFactories", [
        {"type": "function", "name": name, "stateMutability": "view",
         "inputs": [{"name": "index", "type": "uint256"}],
         "outputs": [{"name": "", "type": "address"}]}
        for name in ("MORPHO_ADDRS", "EULER_ADDRS")
    ]).at(blue.address)
    morpho_factories = [blue_arrays.MORPHO_ADDRS(0), blue_arrays.MORPHO_ADDRS(1)]
    euler_factories = [blue_arrays.EULER_ADDRS(0), blue_arrays.EULER_ADDRS(1)]
    wrapped = old["wsuperOETHbPrices"]
    yield_position = psm.usdcYieldPosition()

    log.h1("2. Deploy the replacement PriceDesk and all existing source types")
    candidates = {}
    candidates["PriceDesk"] = migration.deploy(
        "PriceDesk", hq.address, ZERO, eth,
        params["PRICE_DESK_MIN_REG_TIMELOCK"], params["PRICE_DESK_MAX_REG_TIMELOCK"],
        1_500_000,  # immutable per-source price-call budget; Base vault quotes exceed 250k
        label=f"PriceDesk{SUFFIX}",
    )
    assert candidates["PriceDesk"].PRICE_SOURCE_PRICE_GAS() == 1_500_000
    candidates["ChainlinkPrices"] = migration.deploy(
        "ChainlinkPrices", hq.address, ZERO, min_lock, max_lock,
        chainlink.WETH(), eth, btc, eth_config[0], btc_config[0], eth_config[4],
        label=f"ChainlinkPrices{SUFFIX}",
    )
    candidates["CurvePrices"] = migration.deploy(
        "CurvePrices", hq.address, ZERO,
        migration.blueprint().ADDYS["CURVE_ADDRESS_PROVIDER"],
        hq.getAddr(1), hq.getAddr(2), min_lock, max_lock,
        label=f"CurvePrices{SUFFIX}",
    )
    candidates["BlueChipYieldPrices"] = migration.deploy(
        "BlueChipYieldPrices", hq.address, ZERO, min_lock, max_lock,
        morpho_factories, euler_factories, blue.FLUID_ADDR(),
        blue.COMPOUND_V3_ADDR(), blue.MOONWELL_ADDR(), blue.AAVE_V3_ADDR(),
        ZERO,  # no new Morpho V2 factory enabled without an authenticated Base binding
        label=f"BlueChipYieldPrices{SUFFIX}",
    )
    candidates["PythPrices"] = migration.deploy(
        "PythPrices", hq.address, ZERO, old["PythPrices"].PYTH(), min_lock, max_lock,
        label=f"PythPrices{SUFFIX}",
    )
    candidates["StorkPrices"] = migration.deploy(
        "StorkPrices", hq.address, ZERO, old["StorkPrices"].STORK(), min_lock, max_lock,
        label=f"StorkPrices{SUFFIX}",
    )
    candidates["wsuperOETHbPrices"] = migration.deploy(
        "wsuperOETHbPrices", hq.address, wrapped.MCBETH(), wrapped.SUPER_OETH(),
        wrapped.WRAPPED_SUPER_OETH(), wrapped.VVV(), min_lock, max_lock,
        label=f"wsuperOETHbPrices{SUFFIX}",
    )
    candidates["RedStone"] = migration.deploy(
        "RedStone", hq.address, ZERO, eth, min_lock, max_lock,
        label=f"RedStone{SUFFIX}",
    )
    candidates["UndyVaultPrices"] = migration.deploy(
        "UndyVaultPrices", hq.address, ZERO, min_lock, max_lock,
        label=f"UndyVaultPrices{SUFFIX}",
    )
    # The current Aero contract is monitoring-only, not a collateral oracle.
    # Never register it as a replacement for the legacy live slot-6 source.
    candidates["AeroRipePrices"] = migration.deploy(
        "AeroRipePrices", hq.address, migration.blueprint().ADDYS["RIPE_WETH_POOL"],
        hq.getAddr(3), chainlink.WETH(), label=f"AeroRipePrices{SUFFIX}",
    )
    assert candidates["AeroRipePrices"].isMonitoringOnly()

    log.h1("3. Deploy PSM with the live USDC limits and yield destination")
    candidates["EndaomentPSM"] = migration.deploy(
        "EndaomentPSM", hq.address, psm.numBlocksPerInterval(),
        psm.mintFee(), psm.maxIntervalMint(), psm.redeemFee(), psm.maxIntervalRedeem(),
        USDC, yield_position[0], yield_position[1], label=f"EndaomentPSM{SUFFIX}",
    )
    assert not candidates["EndaomentPSM"].canMint()
    assert not candidates["EndaomentPSM"].canRedeem()

    log.h1("4. Deploy USDC reserves, paused and with sales disabled")
    candidates["RipeReserveEngine"] = migration.deploy(
        "RipeReserveEngine", hq.address, USDC, DORMANT_RESERVE_CONFIG,
        label=f"RipeReserveEngine{SUFFIX}",
    )
    candidates["RipeReserveVesting"] = migration.deploy(
        "RipeReserveVesting", hq.address, label=f"RipeReserveVesting{SUFFIX}",
    )
    assert candidates["RipeReserveEngine"].isPaused()
    assert not candidates["RipeReserveEngine"].isRunning()
    assert not candidates["RipeReserveEngine"].canAcquireRipe()
    assert candidates["RipeReserveVesting"].isPaused()

    for name, candidate in candidates.items():
        assert 0 < len(boa.env.get_code(candidate.address)) <= 24576, name
        log.info(f"STAGED ONLY {name}: {candidate.address}")
    assert str(hq.getAddr(7)).lower() == str(old_desk.address).lower()
    assert str(hq.getAddr(22)).lower() == str(psm.address).lower()
    log.info("No activation, oracle config replay, or custody transfers performed here.")
