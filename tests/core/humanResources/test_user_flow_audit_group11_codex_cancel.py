"""Focused Group 11 cancellation proofs using Delta's production action path."""

import boa

from contracts.modules import Contributor


def _advance_to_block(block_number):
    current = boa.env.evm.patch.block_number
    if current < block_number:
        boa.env.time_travel(blocks=block_number - current)
    assert boa.env.evm.patch.block_number >= block_number


def _advance_to_timestamp(timestamp):
    current = boa.env.evm.patch.timestamp
    if current < timestamp:
        boa.env.time_travel(seconds=timestamp - current)
    assert boa.env.evm.patch.timestamp == timestamp


def _queue_cancel(switchboard_delta, governance, contributor):
    action = switchboard_delta.cancelPaycheckForContributor(
        contributor.address, sender=governance.address
    )
    _advance_to_block(switchboard_delta.getActionConfirmationBlock(action))
    return action


def test_g11_precliff_cancel_burns_all_clone_vault_residue_but_refunds_only_paycheck(
    deployedContributor,
    valid_contributor_terms,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    ripe_token,
    whale,
    teller,
    ledger,
    human_resources,
    switchboard_delta,
    governance,
    owner_address,
):
    """The pre-cliff burn pulls B + P even though the ledger refund is only C."""
    setupRipeGovVaultConfig()
    contributor = Contributor.at(deployedContributor(dict(valid_contributor_terms)))
    midpoint = contributor.startTime() + (
        contributor.cliffTime() - contributor.startTime()
    ) // 2
    _advance_to_timestamp(midpoint)
    paycheck = contributor.cashRipeCheck(sender=owner_address)
    assert paycheck > 0

    # This is a fixture/protocol-deposit route, not a claim that an ordinary
    # EOA can target a clone.  It intentionally puts residue B in the gov
    # vault (not as RIPE held by the clone) so HR's actual burn callee sees it.
    residue = 1_000 * 10**18
    ripe_token.transfer(ripe_gov_vault, residue, sender=whale)
    ripe_gov_vault.depositTokensInVault(
        contributor.address, ripe_token, residue, sender=teller.address
    )
    position_before = ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token)
    assert position_before == paycheck + residue
    supply_before = ripe_token.totalSupply()
    budget_before = ledger.ripeAvailForHr()
    original_compensation = contributor.compensation()
    assert boa.env.evm.patch.timestamp < contributor.cliffTime()

    action = _queue_cancel(switchboard_delta, governance, contributor)
    assert switchboard_delta.executePendingAction(action, sender=governance.address)
    assert contributor.compensation() == 0
    assert contributor.totalClaimed() == paycheck
    assert ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token) == 0
    assert ledger.ripeAvailForHr() == budget_before + original_compensation
    assert ripe_token.totalSupply() == supply_before - position_before
    assert ripe_token.balanceOf(human_resources) == 0


def test_g11_default_contributor_rejects_ordinary_third_party_residue_deposit(
    deployedContributor,
    valid_contributor_terms,
    setupRipeGovVaultConfig,
    ripe_token,
    ripe_gov_vault,
    whale,
    teller,
):
    """The residue proof's direct Teller impersonation is not an ordinary flow."""
    setupRipeGovVaultConfig()
    contributor = Contributor.at(deployedContributor(dict(valid_contributor_terms)))
    residue = 1_000 * 10**18
    assert ripe_token.approve(teller, residue, sender=whale)
    with boa.reverts("cannot deposit for user"):
        teller.deposit(
            ripe_token,
            residue,
            contributor.address,
            ripe_gov_vault.address,
            2,
            sender=whale,
        )


def test_g11_component_cancel_boundaries_classify_the_switchboard_address_spoof(
    deployedContributor,
    valid_contributor_terms,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    ripe_token,
    ledger,
    switchboard_alpha,
):
    """Exact timing needs a component spoof; production Delta proofs are above."""

    def run_prestart_or_precliff(target, expect_cash):
        with boa.env.anchor():
            setupRipeGovVaultConfig()
            contributor = Contributor.at(deployedContributor(dict(valid_contributor_terms)))
            _advance_to_timestamp(target(contributor))
            before_budget = ledger.ripeAvailForHr()
            before_supply = ripe_token.totalSupply()
            original = contributor.compensation()
            expected = contributor.getClaimable()
            contributor.cancelPaycheck(sender=switchboard_alpha.address)
            assert contributor.compensation() == (expected if expect_cash else 0)
            assert contributor.totalClaimed() == (expected if expect_cash else 0)
            assert ledger.ripeAvailForHr() == before_budget + (
                original - expected if expect_cash else original
            )
            assert ripe_token.totalSupply() == before_supply + (expected if expect_cash else 0)
            assert contributor.getTotalVested() == (expected if expect_cash else 0)
            assert contributor.getClaimable() == 0

    run_prestart_or_precliff(lambda c: c.startTime() - 1, False)
    run_prestart_or_precliff(lambda c: c.startTime() + 1, False)
    run_prestart_or_precliff(lambda c: c.cliffTime(), True)

    with boa.env.anchor():
        contributor = Contributor.at(deployedContributor(dict(valid_contributor_terms)))
        _advance_to_timestamp(contributor.endTime())
        with boa.reverts("cannot cancel"):
            contributor.cancelPaycheck(sender=switchboard_alpha.address)

    with boa.env.anchor():
        contributor = Contributor.at(deployedContributor(dict(valid_contributor_terms)))
        _advance_to_timestamp(contributor.startTime() - 1)
        contributor.cancelPaycheck(sender=switchboard_alpha.address)
        with boa.reverts("cannot cancel"):
            contributor.cancelPaycheck(sender=switchboard_alpha.address)


def test_g11_frozen_after_cliff_cancel_forfeits_vested_uncashed_ripe_by_design(
    deployedContributor,
    valid_contributor_terms,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    ripe_token,
    ledger,
    switchboard_delta,
    governance,
):
    """Compare identical Delta cancels with and without the authorized freeze."""

    def run_case(frozen):
        with boa.env.anchor():
            setupRipeGovVaultConfig()
            contributor = Contributor.at(deployedContributor(dict(valid_contributor_terms)))
            _advance_to_timestamp(contributor.cliffTime() + 1)
            compensation = contributor.compensation()
            supply_before = ripe_token.totalSupply()
            position_before = ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token)
            budget_before = ledger.ripeAvailForHr()
            if frozen:
                assert switchboard_delta.freezeContributor(
                    contributor.address, True, sender=governance.address
                )
            action = _queue_cancel(switchboard_delta, governance, contributor)
            assert switchboard_delta.executePendingAction(action, sender=governance.address)
            return {
                "claimed": contributor.totalClaimed(),
                "compensation": compensation,
                "supply_delta": ripe_token.totalSupply() - supply_before,
                "position_delta": ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token)
                - position_before,
                "budget_delta": ledger.ripeAvailForHr() - budget_before,
            }

    unfrozen = run_case(False)
    frozen = run_case(True)
    assert unfrozen["claimed"] > 0
    assert unfrozen["supply_delta"] == unfrozen["claimed"]
    assert unfrozen["position_delta"] == unfrozen["claimed"]
    assert unfrozen["budget_delta"] == unfrozen["compensation"] - unfrozen["claimed"]
    assert frozen["claimed"] == 0
    assert frozen["supply_delta"] == 0
    assert frozen["position_delta"] == 0
    assert frozen["budget_delta"] == frozen["compensation"]
    assert frozen["budget_delta"] > unfrozen["budget_delta"]


def test_g11_hr_pause_rolls_back_mature_delta_cancel_and_terminal_clone_can_exit(
    deployedContributor,
    valid_contributor_terms,
    setupRipeGovVaultConfig,
    ripe_gov_vault,
    ripe_token,
    ledger,
    human_resources,
    switchboard_charlie,
    switchboard_delta,
    governance,
    owner_address,
):
    """Pause rolls back the official cancel and retry retains its original action."""
    setupRipeGovVaultConfig()
    contributor = Contributor.at(deployedContributor(dict(valid_contributor_terms)))
    _advance_to_timestamp(contributor.cliffTime() + 1)
    original_unlock = contributor.unlockTime()
    action = _queue_cancel(switchboard_delta, governance, contributor)
    before = (
        contributor.compensation(),
        contributor.endTime(),
        contributor.totalClaimed(),
        ledger.ripeAvailForHr(),
        ripe_token.totalSupply(),
        ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token),
    )

    assert switchboard_charlie.pause(
        human_resources.address, True, sender=governance.address
    )
    with boa.reverts():
        switchboard_delta.executePendingAction(action, sender=governance.address)
    assert switchboard_delta.hasPendingAction(action)
    assert (
        contributor.compensation(),
        contributor.endTime(),
        contributor.totalClaimed(),
        ledger.ripeAvailForHr(),
        ripe_token.totalSupply(),
        ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token),
    ) == before

    assert switchboard_charlie.pause(
        human_resources.address, False, sender=governance.address
    )
    assert switchboard_delta.executePendingAction(action, sender=governance.address)
    assert contributor.unlockTime() == original_unlock
    assert contributor.compensation() == contributor.totalClaimed()
    position = ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token)
    assert position > 0

    # An after-cliff cancellation is terminal for vesting, not custody: once
    # the unchanged original unlock is strictly past, ordinary two-step
    # transfer exits the clone.
    _advance_to_timestamp(original_unlock + 1)
    contributor.initiateRipeTransfer(False, sender=owner_address)
    pending = contributor.pendingRipeTransfer()
    _advance_to_block(pending.confirmBlock)
    owner_before = ripe_gov_vault.getTotalAmountForUser(owner_address, ripe_token)
    contributor.confirmRipeTransfer(False, sender=owner_address)
    assert ripe_gov_vault.getTotalAmountForUser(contributor, ripe_token) == 0
    assert (
        ripe_gov_vault.getTotalAmountForUser(owner_address, ripe_token)
        == owner_before + position
    )
