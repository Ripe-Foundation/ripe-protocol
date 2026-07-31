from scripts.utils import log
from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    blueprint = migration.blueprint()

    log.h1("Deploying Endaoment PSM")

    # Deployed DISABLED. The constructor hard-sets canMint = False and
    # canRedeem = False (P-H04-355/356); activation is a separate governed step
    # that is independently blocked.
    #
    # The fee and cap values are scaffolding, not approved policy -- B-H04-PSM
    # holds all of DP-08 blocked. They are non-zero only because the constructor
    # rejects a zero interval and a zero or max cap. They are inert while mint
    # and redeem are false.
    #
    # Yield position is disabled per P-H04-359/360: lego id 0 and a zero vault
    # token leave usdcYieldPosition unset.
    reserve_asset = blueprint.CORE_TOKENS["USDG"]
    assert reserve_asset != ZERO_ADDRESS  # dev: psm reserve asset unresolved

    endaoment_psm = migration.deploy(
        "EndaomentPSM",
        hq,
        blueprint.PARAMS["PSM_NUM_BLOCKS_PER_INTERVAL"],
        blueprint.PARAMS["PSM_MINT_FEE"],
        blueprint.PARAMS["PSM_MAX_INTERVAL_MINT"],
        blueprint.PARAMS["PSM_REDEEM_FEE"],
        blueprint.PARAMS["PSM_MAX_INTERVAL_REDEEM"],
        reserve_asset,
        blueprint.PARAMS["PSM_YIELD_LEGO_ID"],
        blueprint.PARAMS["PSM_YIELD_VAULT_TOKEN"],
    )

    migration.execute(hq.startAddNewAddressToRegistry, endaoment_psm, "Endaoment PSM")
    assert int(migration.execute(hq.confirmNewAddressToRegistry, endaoment_psm)) == 22

    # The contract declares canMintGreen in DeptBasics, but the HQ-level
    # capability stays withheld while the PSM is disabled. Granting it is part of
    # PSM activation, not deployment.
    assert not bool(migration.execute(endaoment_psm.canMint))
    assert not bool(migration.execute(endaoment_psm.canRedeem))
