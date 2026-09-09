import boa

from constants import EIGHTEEN_DECIMALS


TRANSFER_AMOUNT = 1_000 * EIGHTEEN_DECIMALS


def prepare_transferable_position(
    contributor,
    setup_ripe_gov_vault_config,
    ripe_gov_vault,
    ripe_token,
    whale,
    teller,
    contributor_terms,
):
    """Fund a Contributor position and move past its unlock timestamp."""
    setup_ripe_gov_vault_config()
    ripe_token.transfer(ripe_gov_vault, TRANSFER_AMOUNT, sender=whale)
    ripe_gov_vault.depositTokensInVault(
        contributor.address,
        ripe_token,
        TRANSFER_AMOUNT,
        sender=teller.address,
    )
    boa.env.time_travel(
        seconds=contributor_terms["startDelay"] + contributor_terms["unlockLength"] + 1
    )


def initiate_transfer(
    contributor,
    setup_ripe_gov_vault_config,
    ripe_gov_vault,
    ripe_token,
    whale,
    teller,
    owner,
    contributor_terms,
):
    """Prepare and initiate a RIPE-position transfer to the current owner."""
    prepare_transferable_position(
        contributor,
        setup_ripe_gov_vault_config,
        ripe_gov_vault,
        ripe_token,
        whale,
        teller,
        contributor_terms,
    )
    contributor.initiateRipeTransfer(sender=owner)
