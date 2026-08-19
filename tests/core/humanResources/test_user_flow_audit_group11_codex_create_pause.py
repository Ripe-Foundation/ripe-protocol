"""Group 11 official HR/Ledger pause rollback proofs for contributor creation."""

import boa


def _advance_to_block(block_number):
    current = boa.env.evm.patch.block_number
    if current < block_number:
        boa.env.time_travel(blocks=block_number - current)
    assert boa.env.evm.patch.block_number >= block_number


def _initiate(human_resources, governance, terms):
    return human_resources.initiateNewContributor(
        terms["owner"],
        terms["manager"],
        terms["compensation"],
        terms["startDelay"],
        terms["vestingLength"],
        terms["cliffLength"],
        terms["unlockLength"],
        terms["depositLockDuration"],
        sender=governance.address,
    )


def test_g11_charlie_hr_pause_blocks_create_confirm_and_cancel_then_unpause_retries(
    human_resources,
    switchboard_charlie,
    governance,
    setupHrConfig,
    setupLedgerBalance,
    valid_contributor_terms,
):
    """Charlie is the official department-pause writer, not a spoofed HR call."""
    terms = dict(valid_contributor_terms)
    setupHrConfig()
    setupLedgerBalance(terms["compensation"])
    assert switchboard_charlie.pause(
        human_resources.address, True, sender=governance.address
    )
    with boa.reverts("contract paused"):
        _initiate(human_resources, governance, terms)
    assert switchboard_charlie.pause(
        human_resources.address, False, sender=governance.address
    )

    action = _initiate(human_resources, governance, terms)
    _advance_to_block(human_resources.getActionConfirmationBlock(action))
    assert switchboard_charlie.pause(
        human_resources.address, True, sender=governance.address
    )
    with boa.reverts("contract paused"):
        human_resources.confirmNewContributor(action, sender=governance.address)
    with boa.reverts("contract paused"):
        human_resources.cancelNewContributor(action, sender=governance.address)
    assert human_resources.pendingContributor(action).owner == terms["owner"]
    assert switchboard_charlie.pause(
        human_resources.address, False, sender=governance.address
    )
    assert human_resources.confirmNewContributor(action, sender=governance.address)


def test_g11_charlie_ledger_pause_reverts_after_blueprint_creation_without_orphan(
    human_resources,
    ledger,
    switchboard_charlie,
    governance,
    setupHrConfig,
    setupLedgerBalance,
    valid_contributor_terms,
):
    """Ledger's addHrContributor failure rolls the whole confirm transaction back."""
    terms = dict(valid_contributor_terms)
    setupHrConfig()
    setupLedgerBalance(terms["compensation"])
    action = _initiate(human_resources, governance, terms)
    _advance_to_block(human_resources.getActionConfirmationBlock(action))
    before_budget = ledger.ripeAvailForHr()
    before_count = ledger.numContributors()

    assert switchboard_charlie.pause(ledger.address, True, sender=governance.address)
    with boa.reverts():
        human_resources.confirmNewContributor(action, sender=governance.address)
    assert human_resources.pendingContributor(action).owner == terms["owner"]
    assert ledger.numContributors() == before_count
    assert ledger.ripeAvailForHr() == before_budget

    assert switchboard_charlie.pause(ledger.address, False, sender=governance.address)
    assert human_resources.confirmNewContributor(action, sender=governance.address)
    assert ledger.numContributors() == before_count + (2 if before_count == 0 else 1)
    assert ledger.ripeAvailForHr() == before_budget - terms["compensation"]
