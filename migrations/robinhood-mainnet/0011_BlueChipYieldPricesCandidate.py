"""Static plan to promote 0010 and prepare BlueChipYield slot 3.

The existing Robinhood deployment omitted BlueChipYieldPrices even though the
approved topology reserves PriceDesk slot 3 for it. This forward migration
does not rewrite historical deployment steps and does not mutate PriceDesk.
It deploys a fully finalized Morpho V2-capable candidate under a unique
manifest label and emits the exact Safe calldata for the timelocked add.
``0012`` performs registry readback before promoting the canonical manifest
label.

The H-06 runner that rejected this legacy deploy/send API has been removed.
What now gates execution is MigrationRunner: it refuses a history that already
holds a ``current-manifest.json`` unless an explicit ``--start-timestamp`` is
given.
"""

from scripts.utils import log
from scripts.utils.migration import Migration, PromotionSpec

from config.robinhood_launch import (
    BLUECHIP_AAVE_PROVIDER,
    BLUECHIP_COMPOUND_CONFIGURATOR,
    BLUECHIP_EULER_FACTORIES,
    BLUECHIP_FLUID_RESOLVER,
    BLUECHIP_MOONWELL_COMPTROLLER,
    BLUECHIP_MORPHO_FACTORIES,
    LEDGER_ACTION_BLOCK_SOURCE,
    LOOTBOX_DEPOSIT_REWARD,
    LOOTBOX_MIN_SEND_INTERVAL,
    LOOTBOX_SEND_INTERVAL,
    LOOTBOX_YIELD_BONUS,
    PRICE_CHANGE_MAX_TIMELOCK,
    PRICE_CHANGE_MIN_TIMELOCK,
    TELLER_SHOULD_PAUSE,
    ZERO_ADDRESS,
    address,
)


RIPE_HQ = "RipeHq"
VAULT_BOOK = "VaultBook"
BLUECHIP_CANDIDATE = "BlueChipYieldPricesCandidate0011"

ACTIVATED_0010 = (
    ("Ledger", "LedgerCandidate0010", RIPE_HQ, 4),
    ("Lootbox", "LootboxCandidate0010", RIPE_HQ, 16),
    ("Teller", "TellerCandidate0010", RIPE_HQ, 17),
    ("RipeGov", "RipeGovCandidate0010", VAULT_BOOK, 2),
)

CANONICAL_SOURCE_PATHS = {
    "Ledger": "contracts/data/Ledger.vy",
    "Lootbox": "contracts/core/Lootbox.vy",
    "Teller": "contracts/core/Teller.vy",
    "RipeGov": "contracts/vaults/RipeGov.vy",
}


def _add_calldata(new_addr, description):
    """The two Safe calls that append one PriceDesk registry slot."""
    from eth_abi.abi import encode
    from web3 import Web3

    start = Web3.keccak(text="startAddNewAddressToRegistry(address,string)")[:4]
    start += encode(["address", "string"], [new_addr, description])
    confirm = Web3.keccak(text="confirmNewAddressToRegistry(address)")[:4]
    confirm += encode(["address"], [new_addr])
    return start.hex(), confirm.hex()


def migrate(migration: Migration):
    hq = migration.get_contract(RIPE_HQ)
    registries = {
        RIPE_HQ: hq,
        VAULT_BOOK: migration.get_contract(VAULT_BOOK),
    }

    log.h1("Verifying and promoting activated 0010 candidates")
    expected_args = {
        "Ledger": (
            hq,
            migration.get_address("DefaultsRobinhoodLive"),
            LEDGER_ACTION_BLOCK_SOURCE,
        ),
        "Lootbox": (
            hq,
            LOOTBOX_MIN_SEND_INTERVAL,
            LOOTBOX_SEND_INTERVAL,
            LOOTBOX_DEPOSIT_REWARD,
            LOOTBOX_YIELD_BONUS,
        ),
        "Teller": (hq, TELLER_SHOULD_PAUSE),
        "RipeGov": (hq,),
    }
    migration.promote_candidates(
        [
            PromotionSpec(
                canonical_name=canonical,
                expected_source_path=CANONICAL_SOURCE_PATHS[canonical],
                candidate_label=candidate,
                registry_name=registry_name,
                registry=registries[registry_name],
                registry_id=reg_id,
                expected_constructor_args=expected_args[canonical],
            )
            for canonical, candidate, registry_name, reg_id in ACTIVATED_0010
        ]
    )

    price_desk = migration.get_contract("PriceDesk")
    # AddressRegistry.numAddrs is the next id, not the number of populated
    # rows. Chainlink and Curve occupy ids 1 and 2, so the required pre-state
    # is numAddrs == 3 with an empty readback at the next id.
    assert int(price_desk.numAddrs()) == 3, "PriceDesk next id is not slot 3"
    assert price_desk.getAddr(3) == ZERO_ADDRESS, "PriceDesk slot 3 is occupied"

    # This selected external fact is not established merely by appearing in
    # BluePrint. The typed conversion must bind chain id, deployed code, code
    # identity, and the Morpho V2 membership selector before authorizing a
    # deployment. Nonzero is only the static plan's minimum sanity check.
    morpho_v2_factory = address("MORPHO_V2_FACTORY")
    assert morpho_v2_factory != ZERO_ADDRESS

    log.h1("Deploying BlueChipYieldPrices Morpho V2 candidate")
    blue_chip = migration.deploy(
        "BlueChipYieldPrices",
        hq,
        migration.account(),
        PRICE_CHANGE_MIN_TIMELOCK,
        PRICE_CHANGE_MAX_TIMELOCK,
        BLUECHIP_MORPHO_FACTORIES,
        BLUECHIP_EULER_FACTORIES,
        BLUECHIP_FLUID_RESOLVER,
        BLUECHIP_COMPOUND_CONFIGURATOR,
        BLUECHIP_MOONWELL_COMPTROLLER,
        BLUECHIP_AAVE_PROVIDER,
        morpho_v2_factory,
        label=BLUECHIP_CANDIDATE,
    )

    assert int(blue_chip.actionTimeLock()) == 0
    selected = int(blue_chip.minActionTimeLock())
    assert selected == PRICE_CHANGE_MIN_TIMELOCK and selected != 0
    migration.execute(
        blue_chip.setActionTimeLockAfterSetup,
        selected,
    )
    assert int(blue_chip.actionTimeLock()) == selected
    migration.execute(blue_chip.relinquishGov)
    assert blue_chip.governance() == ZERO_ADDRESS

    start, confirm = _add_calldata(
        blue_chip.address,
        "BlueChipYieldPrices",
    )
    log.h1("PriceDesk slot 3 Safe actions")
    log.info(f"\tPriceDesk:  {price_desk.address}")
    log.info(f"\tcandidate:  {blue_chip.address} [{BLUECHIP_CANDIDATE}]")
    log.info(f"\t[1] 0x{start}")
    log.info(f"\t[2] 0x{confirm}   (after timelock)")
    log.info("\tKeep an exclusive PriceDesk-add window until confirmation.")
    log.info("\tThe typed executor must require confirm() to return id 3.")
