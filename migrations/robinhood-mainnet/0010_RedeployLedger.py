"""Static plan to promote 0009 and deploy the 0010 candidates.

Two things land together here.

FIRST -- deposits are currently reverting. 0009 replaced StabilityPool, RipeGov
and SimpleErc20 at their existing VaultBook ids. Ledger was deliberately left
alone -- it holds accounting nothing can rebuild -- but it also holds per-user
vault participation, and that kept pointing at ids whose vaults are now empty.

CreditEngine._getUserBorrowTerms runs on every deposit through housekeeping:

    numUserAssets = staticcall Vault(vaultAddr).numUserAssets(_user)
    for y: uint256 in range(1, numUserAssets, bound=max_value(uint256)):

Vyper reverts when stop < start, so a user Ledger says is in vault 2 whose
replacement reports zero assets makes range(1, 0) revert -- and every deposit
and withdrawal with it. The outer loop over vaults is guarded for zero
(CreditEngine.vy:699); this inner one is not, which is worth fixing separately.

A fresh Ledger clears participation, so it is rebuilt only as users deposit
into vaults that actually exist. Acceptable because the protocol is empty --
all three old vaults hold $0.00 -- and NOT a general answer. The right pattern
is to add a new vault id and migrate into it rather than replace a vault in
place, which keeps participation and balances consistent throughout.

SECOND -- Ledger, Teller, Lootbox and RipeGov all drifted again after 0009.
An intermediate generation added a dedicated
`removeVaultFromUserForMigration` Ledger selector. The final source removes
that special surface and routes migration cleanup through the ordinary
Lootbox/Ledger accounting path instead. The live records and final source are
therefore different generations even though that intermediate selector is not
part of the accepted current ABI. These four still move together because their
migration authority, lock preservation, reward cleanup and participation
semantics are interdependent.

ORDER MATTERS. RipeGov is replaced again here, which re-creates the same empty
vault at a live id. That is only safe because Ledger is wiped in the same
batch. If the Safe applies these separately, apply Ledger FIRST or together --
a new RipeGov against the old Ledger reproduces the revert this fixes.

Ledger keeps its ripeAvailFor*: DefaultsRobinhoodLive sources those from the
live Ledger, so the RIPE already emitted stays accounted for. It drops accrued
deposit and borrow points, unclaimed ripeRewards, and lastTouch.

The four new deployments use unique ``*Candidate0010`` manifest labels. This
migration emits actual Safe calldata but does not replace the canonical
manifest labels. The Safe must activate all four confirmations atomically; a
later readback-only migration promotes them after every slot matches.

The H-06 Robinhood runner keeps this legacy API fail-closed. Conversion to
typed ``MIGRATION_STAGE`` actions is required before production execution.
"""

from scripts.utils import log
from scripts.utils.migration import Migration, PromotionSpec

from config.robinhood_launch import (
    HR_MAX_TIMELOCK,
    HR_MIN_TIMELOCK,
    LEDGER_ACTION_BLOCK_SOURCE,
    LOOTBOX_DEPOSIT_REWARD,
    LOOTBOX_MIN_SEND_INTERVAL,
    LOOTBOX_SEND_INTERVAL,
    LOOTBOX_YIELD_BONUS,
    STALE_WINDOW_MAX,
    STALE_WINDOW_MIN,
    SWITCHBOARD_MAX_TIMELOCK,
    SWITCHBOARD_MIN_TIMELOCK,
    TELLER_SHOULD_PAUSE,
    ZERO_ADDRESS,
)

RIPE_HQ = "RipeHq"
VAULT_BOOK = "VaultBook"
CANDIDATE_SUFFIX = "Candidate0010"

ACTIVATED_0009 = (
    ("MissionControl", "MissionControlCandidate0009", RIPE_HQ, 5),
    ("AuctionHouse", "AuctionHouseCandidate0009", RIPE_HQ, 9),
    ("BondRoom", "BondRoomCandidate0009", RIPE_HQ, 12),
    ("CreditEngine", "CreditEngineCandidate0009", RIPE_HQ, 13),
    ("HumanResources", "HumanResourcesCandidate0009", RIPE_HQ, 15),
    ("Lootbox", "LootboxCandidate0009", RIPE_HQ, 16),
    ("Teller", "TellerCandidate0009", RIPE_HQ, 17),
    ("CreditRedeem", "CreditRedeemCandidate0009", RIPE_HQ, 19),
    ("TellerUtils", "TellerUtilsCandidate0009", RIPE_HQ, 20),
    ("StabilityPool", "StabilityPoolCandidate0009", VAULT_BOOK, 1),
    ("RipeGov", "RipeGovCandidate0009", VAULT_BOOK, 2),
    ("SimpleErc20", "SimpleErc20Candidate0009", VAULT_BOOK, 3),
    ("SwitchboardAlpha", "SwitchboardAlphaCandidate0009", "Switchboard", 1),
    ("SwitchboardBravo", "SwitchboardBravoCandidate0009", "Switchboard", 2),
    ("SwitchboardCharlie", "SwitchboardCharlieCandidate0009", "Switchboard", 3),
    ("SwitchboardEcho", "SwitchboardEchoCandidate0009", "Switchboard", 5),
)

CANONICAL_SOURCE_PATHS = {
    "MissionControl": "contracts/data/MissionControl.vy",
    "AuctionHouse": "contracts/core/AuctionHouse.vy",
    "BondRoom": "contracts/core/BondRoom.vy",
    "CreditEngine": "contracts/core/CreditEngine.vy",
    "HumanResources": "contracts/core/HumanResources.vy",
    "Lootbox": "contracts/core/Lootbox.vy",
    "Teller": "contracts/core/Teller.vy",
    "CreditRedeem": "contracts/core/CreditRedeem.vy",
    "TellerUtils": "contracts/core/TellerUtils.vy",
    "StabilityPool": "contracts/vaults/StabilityPool.vy",
    "RipeGov": "contracts/vaults/RipeGov.vy",
    "SimpleErc20": "contracts/vaults/SimpleErc20.vy",
    "SwitchboardAlpha": "contracts/config/SwitchboardAlpha.vy",
    "SwitchboardBravo": "contracts/config/SwitchboardBravo.vy",
    "SwitchboardCharlie": "contracts/config/SwitchboardCharlie.vy",
    "SwitchboardEcho": "contracts/config/SwitchboardEcho.vy",
    "DefaultsRobinhoodLive": "contracts/config/DefaultsRobinhoodLive.vy",
}

FINALIZED_0009 = (
    ("HumanResourcesCandidate0009", HR_MIN_TIMELOCK),
    ("SwitchboardAlphaCandidate0009", SWITCHBOARD_MIN_TIMELOCK),
    ("SwitchboardBravoCandidate0009", SWITCHBOARD_MIN_TIMELOCK),
    ("SwitchboardCharlieCandidate0009", SWITCHBOARD_MIN_TIMELOCK),
    ("SwitchboardEchoCandidate0009", SWITCHBOARD_MIN_TIMELOCK),
)


def _arb_action_block(migration, ledger_address):
    """Read getArbActionBlock() from the NODE, not from boa's local EVM.

    ArbSys is a node-implemented precompile: on chain it is a single 0xfe byte,
    so boa executes INVALID and any local read reverts even when the contract
    is correct. The constructor no longer probes it either -- that check was
    removed upstream -- so this is the only thing standing between a wrong
    action-block source and a Ledger whose one-action-per-block guard is broken.
    """
    from web3 import Web3

    rpc = migration.rpc()
    if not rpc or rpc == "boa":
        return None  # local run: nothing real to ask
    w3 = Web3(Web3.HTTPProvider(rpc))
    address = Web3.to_checksum_address(ledger_address)

    # On a fork the contract exists only in the local EVM, so the node has no
    # code at this address and would answer an empty word -- which reads as
    # zero and would fail the assertion below for the wrong reason.
    if len(w3.eth.get_code(address)) == 0:
        log.info("\tnot deployed on the node (fork run), skipping ArbSys readback")
        return None

    selector = Web3.keccak(text="getArbActionBlock()")[:4]
    result = w3.eth.call({"to": address, "data": selector})
    return int.from_bytes(result, "big")


def _update_calldata(reg_id, new_addr):
    """The two calls the Safe makes for one registry slot."""
    from eth_abi.abi import encode
    from web3 import Web3

    start = Web3.keccak(text="startAddressUpdateToRegistry(uint256,address)")[:4]
    start += encode(["uint256", "address"], [reg_id, new_addr])
    confirm = Web3.keccak(text="confirmAddressUpdateToRegistry(uint256)")[:4]
    confirm += encode(["uint256"], [reg_id])
    return start.hex(), confirm.hex()


def _require_defaults_constructor_dependency(
    migration,
    hq,
    mission_control,
):
    """Bind the promoted Defaults record to activated MissionControl initcode.

    MissionControl copies Defaults into storage and does not retain a public
    Defaults pointer, so registry readback alone cannot prove this dependency.
    The deployment manifest's ABI-encoded constructor arguments are the exact
    local witness; the typed conversion must bind the same creation input and
    transaction receipt.
    """
    from eth_abi.abi import decode

    manifest = getattr(migration, "_previous_manifest", None)
    contracts = manifest.get("contracts") if isinstance(manifest, dict) else None
    if not isinstance(contracts, dict):
        raise RuntimeError("DEFAULTS_DEPENDENCY_MANIFEST_MISSING")

    mission_record = contracts.get("MissionControlCandidate0009")
    defaults_record = contracts.get("DefaultsRobinhoodLiveCandidate0009")
    if not isinstance(mission_record, dict) or not isinstance(
        defaults_record,
        dict,
    ):
        raise RuntimeError("DEFAULTS_DEPENDENCY_CANDIDATE_RECORD_MISSING")

    encoded_args = mission_record.get("args")
    defaults_address = defaults_record.get("address")
    if (
        not isinstance(encoded_args, str)
        or len(encoded_args) != 128
        or not isinstance(defaults_address, str)
        or len(defaults_address) != 42
        or not defaults_address.startswith("0x")
    ):
        raise RuntimeError("DEFAULTS_DEPENDENCY_CONSTRUCTOR_ARGS_INVALID")
    try:
        if int(defaults_address[2:], 16) == 0:
            raise ValueError
        constructor_hq, constructor_defaults = decode(
            ["address", "address"],
            bytes.fromhex(encoded_args),
        )
    except (ValueError, TypeError):
        raise RuntimeError("DEFAULTS_DEPENDENCY_CONSTRUCTOR_ARGS_INVALID") from None

    expected_hq = str(hq.address).lower()
    expected_defaults = defaults_address.lower()
    if (
        constructor_hq.lower() != expected_hq
        or constructor_defaults.lower() != expected_defaults
    ):
        raise RuntimeError("DEFAULTS_DEPENDENCY_CONSTRUCTOR_MISMATCH")

    # The RipeHq immutable is directly readable on chain. There is no
    # corresponding Defaults pointer: MissionControl deliberately copies the
    # defaults and discards the constructor-only address.
    if str(mission_control.getRipeHq()).lower() != expected_hq:
        raise RuntimeError("DEFAULTS_DEPENDENCY_RIPE_HQ_READBACK_MISMATCH")


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")

    log.h1("Verifying and promoting activated 0009 candidates")
    registries = {
        name: migration.get_contract(name)
        for name in (RIPE_HQ, VAULT_BOOK, "Switchboard")
    }

    # Do this before the first manifest promotion. The activation witness for
    # Defaults is MissionControl's registry slot, but that is sufficient only
    # if the activated MissionControl was constructed from this exact Defaults
    # candidate.
    _require_defaults_constructor_dependency(
        migration,
        hq,
        migration.get_contract("MissionControlCandidate0009"),
    )

    # Validate all replacement action timelocks before the first pending
    # manifest promotion. A missed pre-activation setup must not leave even a
    # partial local promotion sequence behind.
    for candidate, expected_minimum in FINALIZED_0009:
        component = migration.get_contract(candidate)
        selected = int(component.minActionTimeLock())
        assert selected == expected_minimum and selected != 0
        assert int(component.actionTimeLock()) == selected
        assert component.governance() == ZERO_ADDRESS

    defaults_candidate = migration.get_address("DefaultsRobinhoodLiveCandidate0009")
    expected_args = {
        "MissionControl": (hq, defaults_candidate),
        "AuctionHouse": (hq,),
        "BondRoom": (hq, migration.get_contract("BondBooster")),
        "CreditEngine": (hq,),
        "HumanResources": (hq, HR_MIN_TIMELOCK, HR_MAX_TIMELOCK),
        "Lootbox": (
            hq,
            LOOTBOX_MIN_SEND_INTERVAL,
            LOOTBOX_SEND_INTERVAL,
            LOOTBOX_DEPOSIT_REWARD,
            LOOTBOX_YIELD_BONUS,
        ),
        "Teller": (hq, TELLER_SHOULD_PAUSE),
        "CreditRedeem": (hq,),
        "TellerUtils": (hq,),
        "StabilityPool": (hq,),
        "RipeGov": (hq,),
        "SimpleErc20": (hq,),
        "SwitchboardAlpha": (
            hq,
            migration.account(),
            STALE_WINDOW_MIN,
            STALE_WINDOW_MAX,
            SWITCHBOARD_MIN_TIMELOCK,
            SWITCHBOARD_MAX_TIMELOCK,
        ),
        "SwitchboardBravo": (
            hq,
            migration.account(),
            SWITCHBOARD_MIN_TIMELOCK,
            SWITCHBOARD_MAX_TIMELOCK,
        ),
        "SwitchboardCharlie": (
            hq,
            migration.account(),
            SWITCHBOARD_MIN_TIMELOCK,
            SWITCHBOARD_MAX_TIMELOCK,
        ),
        "SwitchboardEcho": (
            hq,
            migration.account(),
            SWITCHBOARD_MIN_TIMELOCK,
            SWITCHBOARD_MAX_TIMELOCK,
        ),
    }
    promotions = [
        PromotionSpec(
            canonical_name=canonical,
            expected_source_path=CANONICAL_SOURCE_PATHS[canonical],
            candidate_label=candidate,
            registry_name=registry_name,
            registry=registries[registry_name],
            registry_id=reg_id,
            expected_constructor_args=expected_args[canonical],
        )
        for canonical, candidate, registry_name, reg_id in ACTIVATED_0009
    ]
    promotions.append(
        PromotionSpec(
            canonical_name="DefaultsRobinhoodLive",
            expected_source_path=CANONICAL_SOURCE_PATHS["DefaultsRobinhoodLive"],
            candidate_label="DefaultsRobinhoodLiveCandidate0009",
            registry_name=RIPE_HQ,
            registry=registries[RIPE_HQ],
            registry_id=5,
            expected_constructor_args=(),
            activation_candidate_label="MissionControlCandidate0009",
            # MissionControl's constructor is (RipeHq, Defaults). The helper
            # independently decodes argument 1 and requires this exact
            # candidate before accepting the sole distinct-witness policy.
            activation_dependency_arg_index=1,
            activation_expected_constructor_args=(hq, defaults_candidate),
        )
    )
    # All 17 records, compiler/source identities, dependencies, and registry
    # readbacks pass before one pending-manifest write. A late mismatch cannot
    # leave an earlier canonical label promoted.
    migration.promote_candidates(promotions)

    # The now-promoted 0009 defaults retain the live Ledger's ripeAvailFor*
    # values, so the replacement inherits them unchanged.
    defaults = migration.get_address("DefaultsRobinhoodLive")

    updates = []

    def redeploy(name, registry, reg_id, *args):
        log.h2(f"Deploying {name}")
        label = f"{name}{CANDIDATE_SUFFIX}"
        contract = migration.deploy(name, *args, label=label)
        updates.append((name, label, registry, reg_id, contract.address))
        return contract

    log.h1("Redeploying")

    ledger = redeploy("Ledger", RIPE_HQ, 4, hq, defaults, LEDGER_ACTION_BLOCK_SOURCE)

    # Asked of the node, because boa cannot execute ArbSys. None on a fork.
    arb_block = _arb_action_block(migration, ledger.address)
    if arb_block is not None:
        assert arb_block != 0, "ArbSys action block reads zero"
        log.h2(f"ArbSys action block: {arb_block}")

    redeploy(
        "Lootbox",
        RIPE_HQ,
        16,
        hq,
        LOOTBOX_MIN_SEND_INTERVAL,
        LOOTBOX_SEND_INTERVAL,
        LOOTBOX_DEPOSIT_REWARD,
        LOOTBOX_YIELD_BONUS,
    )
    redeploy("Teller", RIPE_HQ, 17, hq, TELLER_SHOULD_PAUSE)
    redeploy("RipeGov", VAULT_BOOK, 2, hq)

    log.h1("Registry updates for the Safe")

    for registry in (RIPE_HQ, VAULT_BOOK):
        rows = [u for u in updates if u[2] == registry]
        if not rows:
            continue
        registry_contract = registries[registry]
        log.h2(f"{registry} @ {registry_contract.address}")
        for name, label, _, reg_id, addr in rows:
            active = registry_contract.getAddr(reg_id)
            assert active != addr, f"{name} candidate is already active"
            start, confirm = _update_calldata(reg_id, addr)
            log.info(f"\t{name} [{label}] -> id {reg_id}")
            log.info(f"\t  active:    {active}")
            log.info(f"\t  candidate: {addr}")
            log.info(f"\t  [1] 0x{start}")
            log.info(f"\t  [2] 0x{confirm}   (after timelock)")

    log.h2("Order and follow-ups")
    log.info("\tBundle every 0010 confirmation into one atomic Safe action.")
    log.info("\tA partial activation is unsupported and must revert as a unit.")
    if TELLER_SHOULD_PAUSE:
        log.info("")
        log.info("\tTeller is deployed PAUSED (TELLER_SHOULD_PAUSE). It has to be")
        log.info("\tunpaused after the swap or deposits stay blocked.")
