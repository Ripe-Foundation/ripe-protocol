"""
Assert the end state of a Robinhood migration run.

Import-and-call from run_rh_migrations.py, or run standalone against a manifest.
This checks the things the migration asserts cannot check on their own: that the
final registry layout, capability grants and governance handoff are what the
minimum configuration is supposed to produce.
"""

from __future__ import annotations

# RipeHq registry ids, from contracts/modules/Addys.vy
HQ_IDS = {
    1: "Green Token",
    2: "Savings Green",
    3: "Ripe Token",
    4: "Ledger",
    5: "Mission Control",
    6: "Switchboard",
    7: "Price Desk",
    8: "Vault Book",
    9: "Auction House",
    10: "Auction House NFT",
    11: "Boardroom",
    12: "Bond Room",
    13: "Credit Engine",
    14: "Endaoment",
    15: "Human Resources",
    16: "Lootbox",
    17: "Teller",
    18: "Deleverage",
    19: "Credit Redeem",
    20: "Teller Utils",
    21: "Endaoment Funds",
    22: "Endaoment PSM",
}

# (canMintGreen, canMintRipe) expected at launch
EXPECTED_CAPABILITIES = {
    8: (False, True),    # Vault Book  -- ripe rewards
    9: (True, False),    # Auction House -- keeper rewards
    12: (False, True),   # Bond Room
    13: (True, False),   # Credit Engine
    14: (True, False),   # Endaoment
    15: (False, False),  # Human Resources -- inactive, no ripe mint
    16: (False, True),   # Lootbox
    22: (False, False),  # Endaoment PSM -- deployed disabled
}

NO_CAPABILITY = (18, 19, 20, 21)


def verify(migration, blueprint, deployer, log) -> list[str]:
    """Return a list of failures; empty means the end state is as intended."""
    failures: list[str] = []

    def check(condition, message):
        if condition:
            log.info(f"  ok   {message}")
        else:
            log.info(f"  FAIL {message}")
            failures.append(message)

    hq = migration.get_contract("RipeHq")

    log.h2("RipeHq registry")
    for reg_id, description in HQ_IDS.items():
        addr = hq.getAddr(reg_id)
        check(
            addr not in (None, "0x" + "0" * 40),
            f"id {reg_id:>2} {description} registered ({addr})",
        )

    check(hq.getAddr(23) == "0x" + "0" * 40, "id 23 unused (CCIP is deferred)")

    log.h2("Mint capabilities")
    for reg_id, (green, ripe) in EXPECTED_CAPABILITIES.items():
        config = hq.hqConfig(reg_id)
        check(
            config[1] == green and config[2] == ripe,
            f"id {reg_id:>2} {HQ_IDS[reg_id]:<18} canMintGreen={config[1]} canMintRipe={config[2]}",
        )
    for reg_id in NO_CAPABILITY:
        config = hq.hqConfig(reg_id)
        check(
            not config[1] and not config[2],
            f"id {reg_id:>2} {HQ_IDS[reg_id]:<18} holds no mint capability",
        )

    log.h2("Vault book")
    vault_book = migration.get_contract("VaultBook")
    for vault_id, name in ((1, "StabilityPool"), (2, "RipeGov"), (3, "SimpleErc20")):
        expected = migration.get_address(name)
        check(vault_book.getAddr(vault_id) == expected, f"vault id {vault_id} is {name}")

    log.h2("Price desk")
    price_desk = migration.get_contract("PriceDesk")
    for source_id, name in ((1, "ChainlinkPrices"), (2, "BlueChipYieldPrices")):
        expected = migration.get_address(name)
        check(price_desk.getAddr(source_id) == expected, f"price source id {source_id} is {name}")

    usdg = blueprint.CORE_TOKENS["USDG"]
    check(price_desk.getPrice(usdg, False) != 0, "USDG has a price")
    steakhouse = blueprint.YIELD_TOKENS["MORPHO_STEAKHOUSE_USDG"]
    check(price_desk.getPrice(steakhouse, False) != 0, "SteakHouse USDG vault has a price")

    log.h2("Switchboard")
    switchboard = migration.get_contract("Switchboard")
    for sb_id, name in (
        (1, "SwitchboardAlpha"),
        (2, "SwitchboardBravo"),
        (3, "SwitchboardCharlie"),
        (4, "SwitchboardDelta"),
        (5, "SwitchboardEcho"),
    ):
        check(switchboard.getAddr(sb_id) == migration.get_address(name), f"switchboard id {sb_id} is {name}")

    log.h2("Launch posture")
    teller = migration.get_contract("Teller")
    check(teller.isPaused(), "Teller launches paused (P-H04-421)")

    psm = migration.get_contract("EndaomentPSM")
    check(not psm.canMint(), "PSM mint disabled (P-H04-355)")
    check(not psm.canRedeem(), "PSM redeem disabled (P-H04-356)")

    deleverage = migration.get_contract("Deleverage")
    check(deleverage.deleverageCooldown() == 0, "deleverage cooldown zero (P-H04-308)")
    for name, getter in (
        ("full payoff buffer", deleverage.deleverageFullPayoffBuffer),
        ("overage bps", deleverage.deleverageOverageBps),
        ("dust threshold", deleverage.deleverageDustThreshold),
        ("dust bps", deleverage.deleverageDustBps),
    ):
        check(getter() == 0, f"deleverage {name} deferred at zero")

    log.h2("Governance handoff")
    governance = blueprint.ADDYS["GOVERNANCE"]
    check(hq.governance() == governance, f"RipeHq governance is {governance}")
    check(hq.governance() != deployer, "deployer no longer governs RipeHq")

    # Every department was deployed with no local gov, so RipeHq is the only
    # governor. Confirm nothing kept a local governance address behind.
    for name in (
        "SwitchboardAlpha",
        "SwitchboardBravo",
        "SwitchboardCharlie",
        "SwitchboardDelta",
        "SwitchboardEcho",
        "Switchboard",
        "PriceDesk",
        "VaultBook",
        "ChainlinkPrices",
        "BlueChipYieldPrices",
        "HumanResources",
    ):
        contract = migration.get_contract(name)
        check(contract.governance() == "0x" + "0" * 40, f"{name} has no local governance")

    return failures
