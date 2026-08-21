"""Group 11 exact constructor-addition boundary proof for maxStartDelay = 0."""

import boa

from conf_utils import filter_logs
from constants import ZERO_ADDRESS


UINT256_MAX = 2**256 - 1


def _advance_to_block(block_number):
    current = boa.env.evm.patch.block_number
    if current < block_number:
        boa.env.time_travel(blocks=block_number - current)
    assert boa.env.evm.patch.block_number >= block_number


def _valid(human_resources, terms):
    return human_resources.areValidContributorTerms(
        terms["owner"],
        terms["manager"],
        terms["compensation"],
        terms["startDelay"],
        terms["vestingLength"],
        terms["cliffLength"],
        terms["unlockLength"],
        terms["depositLockDuration"],
    )


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


def test_g11_zero_start_cap_exact_constructor_timestamp_boundary(
    human_resources,
    switchboard_delta,
    governance,
    setupHrConfig,
    setupLedgerBalance,
    valid_contributor_terms,
):
    """The largest representable start delay creates; boundary + 1 reverts."""
    terms = dict(valid_contributor_terms)
    setupHrConfig(_maxStartDelay=1)
    setupLedgerBalance(terms["compensation"])
    zero_cap = switchboard_delta.setMaxStartDelay(0, sender=governance.address)
    _advance_to_block(switchboard_delta.getActionConfirmationBlock(zero_cap))
    assert switchboard_delta.executePendingAction(zero_cap, sender=governance.address)

    # Predict the confirm-time timestamp by replaying the same HR action in an
    # anchor.  The real action below has identical initiation/confirmation
    # timing but a different immutable start delay.
    with boa.env.anchor():
        probe = _initiate(human_resources, governance, terms)
        _advance_to_block(human_resources.getActionConfirmationBlock(probe))
        confirm_timestamp = boa.env.evm.patch.timestamp

    largest = UINT256_MAX - confirm_timestamp - terms["vestingLength"]
    safe = dict(terms)
    safe["startDelay"] = largest
    overflowing = dict(safe)
    overflowing["startDelay"] = largest + 1
    enormous = dict(safe)
    enormous["startDelay"] = largest - 1_000_000

    assert _valid(human_resources, safe)
    assert _valid(human_resources, overflowing)
    assert _valid(human_resources, enormous)
    max_value_terms = dict(terms)
    max_value_terms["startDelay"] = UINT256_MAX
    assert not _valid(human_resources, max_value_terms)
    with boa.reverts("invalid terms"):
        _initiate(human_resources, governance, max_value_terms)

    with boa.env.anchor():
        action = _initiate(human_resources, governance, safe)
        _advance_to_block(human_resources.getActionConfirmationBlock(action))
        assert boa.env.evm.patch.timestamp == confirm_timestamp
        assert human_resources.confirmNewContributor(action, sender=governance.address)

    with boa.env.anchor():
        action = _initiate(human_resources, governance, enormous)
        _advance_to_block(human_resources.getActionConfirmationBlock(action))
        assert human_resources.confirmNewContributor(action, sender=governance.address)

    action = _initiate(human_resources, governance, overflowing)
    _advance_to_block(human_resources.getActionConfirmationBlock(action))
    assert human_resources.confirmNewContributor(action, sender=governance.address) is False
    assert human_resources.pendingContributor(action).owner == ZERO_ADDRESS
    assert not filter_logs(human_resources, "NewContributorConfirmed")
    assert not filter_logs(human_resources, "NewContributorCancelled")
