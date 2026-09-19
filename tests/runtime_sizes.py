"""Shared complete deployed-runtime pins; not a collected test module."""

EIP170_LIMIT = 24_576

# Exact deployed runtimes at this head (boa, including immutables).
# These are a drift tripwire: an unintended size change fails as a
# dict diff instead of waiting for the EIP-170 cliff. Update the pin
# when a size change is intentional. vyper==0.4.3 / titanoboa==0.2.7
# are load-bearing for these numbers — bumping either is a deploy event.
# Tight EIP-170 headrooms vs 24,576: AuctionHouse 12, Deleverage 17,
# Teller 88, CreditEngine 33, Lootbox 165, Alpha 614, Golf 3,644.
# Charlie is 22,317 / 2,259 free. MissionControl is 18,948. Ledger is
# 13,306 and must stay unchanged. Do not add nits to AuctionHouse or
# Deleverage without remeasuring.
# Lootbox `# pragma optimize codesize` (no CLI -O override) is load-bearing.
# Bravo: a dead current VaultBook row fail-closes; restore the book, then Bravo.
# Alpha always settles ripePerBlock / split writes, including setRipePerBlock(0).
# Any edit to a pinned contract must recompile and remeasure.
EXPECTED_RUNTIME_BYTES = {
    "MissionControl": 18948,
    "DefaultsLocal": 1200,
    "SwitchboardAlpha": 23962,
    "SwitchboardBravo": 16423,
    "SwitchboardCharlie": 22317,
    "SwitchboardEcho": 23930,
    "SwitchboardFoxtrot": 18278,
    "SwitchboardGolf": 20932,
    "VaultMigrator": 15626,
    "VaultBook": 14410,
    "Teller": 24488,
    "TellerUtils": 9113,
    "BondRoom": 10927,
    "Ledger": 13306,
    "Lootbox": 24411,
    "GreenToken": 8760,
    "SavingsGreen": 13166,
    "RipeToken": 8760,
    "RebaseErc20": 11602,
    "RipeGov": 24116,
    "HumanResources": 14932,
    "AuctionHouse": 24564,
    "CreditEngine": 24543,
    "CreditRedeem": 8504,
    "Endaoment": 23386,
    "PriceDesk": 19541,
    "Deleverage": 24559,
    "StabilityPool": 24332,
    "BlueChipYieldPrices": 20857,
    "ChainlinkPrices": 16988,
    "CurvePrices": 23406,
    "PythPrices": 16055,
    "RedStone": 15325,
    "StorkPrices": 15067,
    "UndyVaultPrices": 18306,
    "wsuperOETHbPrices": 8336,
}
