import boa
import pytest

from config.BluePrint import PARAMS
from constants import ZERO_ADDRESS


TOKEN_FIXTURES = ("green_token", "savings_green", "ripe_token")


def _deploy_hq(green, savings, ripe, governance, fork):
    return boa.load(
        "contracts/registries/RipeHq.vy",
        green,
        savings,
        ripe,
        governance,
        PARAMS[fork]["RIPE_HQ_MIN_GOV_TIMELOCK"],
        PARAMS[fork]["RIPE_HQ_MAX_GOV_TIMELOCK"],
        PARAMS[fork]["RIPE_HQ_MIN_REG_TIMELOCK"],
        PARAMS[fork]["RIPE_HQ_MAX_REG_TIMELOCK"],
    )


def _suite(green_token, savings_green, ripe_token):
    return (green_token, savings_green, ripe_token)


@pytest.mark.parametrize("token_fixture", TOKEN_FIXTURES)
def test_same_suite_hq_migration_completes_for_every_protocol_token(
    request,
    token_fixture,
    green_token,
    savings_green,
    ripe_token,
    governance,
    fork,
):
    token = request.getfixturevalue(token_fixture)

    with boa.env.anchor():
        candidate = _deploy_hq(
            green_token,
            savings_green,
            ripe_token,
            governance,
            fork,
        )
        previous_hq = token.ripeHq()

        assert token.isValidNewRipeHq(candidate)
        token.initiateHqChange(candidate, sender=governance.address)
        assert token.hasPendingHqChange()
        assert token.ripeHq() == previous_hq

        with boa.reverts("time lock not reached"):
            token.confirmHqChange(sender=governance.address)

        boa.env.time_travel(blocks=token.hqChangeTimeLock())
        assert token.confirmHqChange(sender=governance.address)
        assert not token.hasPendingHqChange()
        assert token.ripeHq() == candidate.address


@pytest.mark.parametrize(
    "changed_role",
    ("green", "savings-green", "ripe"),
)
def test_foreign_token_suite_is_rejected_for_every_protocol_token(
    changed_role,
    green_token,
    savings_green,
    ripe_token,
    alpha_token,
    governance,
    fork,
):
    with boa.env.anchor():
        suite = list(_suite(green_token, savings_green, ripe_token))
        suite[("green", "savings-green", "ripe").index(changed_role)] = alpha_token
        candidate = _deploy_hq(*suite, governance, fork)

        for token in _suite(green_token, savings_green, ripe_token):
            assert not token.isValidNewRipeHq(candidate)
            assert not token.hasPendingHqChange()
            with boa.reverts("invalid new hq"):
                token.initiateHqChange(candidate, sender=governance.address)
            assert not token.hasPendingHqChange()


@pytest.mark.parametrize(
    "changed_role_id",
    (1, 2, 3),
    ids=("green", "savings-green", "ripe"),
)
def test_confirmation_cancels_candidate_whose_suite_changes_during_timelock(
    changed_role_id,
    green_token,
    savings_green,
    ripe_token,
    alpha_token,
    governance,
    fork,
):
    with boa.env.anchor():
        candidate = _deploy_hq(
            green_token,
            savings_green,
            ripe_token,
            governance,
            fork,
        )
        previous_hq = green_token.ripeHq()
        green_token.initiateHqChange(candidate, sender=governance.address)

        assert candidate.startAddressUpdateToRegistry(
            changed_role_id,
            alpha_token,
            sender=governance.address,
        )
        assert candidate.confirmAddressUpdateToRegistry(
            changed_role_id,
            sender=governance.address,
        )
        assert not green_token.isValidNewRipeHq(candidate)

        boa.env.time_travel(blocks=green_token.hqChangeTimeLock())
        assert not green_token.confirmHqChange(sender=governance.address)
        assert green_token.ripeHq() == previous_hq
        assert not green_token.hasPendingHqChange()


def test_initial_setup_rejects_hq_suite_that_omits_the_token(
    green_token,
    savings_green,
    ripe_token,
    deploy3r,
    governance,
    fork,
):
    with boa.env.anchor():
        orphan = boa.load(
            "contracts/tokens/GreenToken.vy",
            ZERO_ADDRESS,
            deploy3r,
            PARAMS[fork]["MIN_HQ_CHANGE_TIMELOCK"],
            PARAMS[fork]["MAX_HQ_CHANGE_TIMELOCK"],
            0,
            ZERO_ADDRESS,
        )
        current_hq = _deploy_hq(
            green_token,
            savings_green,
            ripe_token,
            governance,
            fork,
        )

        assert not orphan.isValidNewRipeHq(current_hq)
        with boa.reverts("invalid ripe hq"):
            orphan.finishTokenSetup(current_hq, sender=deploy3r)
        assert orphan.ripeHq() == ZERO_ADDRESS


def test_constructor_rejects_hq_suite_that_omits_the_token(
    green_token,
    savings_green,
    ripe_token,
    deploy3r,
    fork,
):
    with boa.env.anchor():
        hq = _deploy_hq(
            green_token,
            savings_green,
            ripe_token,
            deploy3r,
            fork,
        )
        with boa.reverts("invalid ripe hq"):
            boa.load(
                "contracts/tokens/GreenToken.vy",
                hq,
                ZERO_ADDRESS,
                PARAMS[fork]["MIN_HQ_CHANGE_TIMELOCK"],
                PARAMS[fork]["MAX_HQ_CHANGE_TIMELOCK"],
                0,
                ZERO_ADDRESS,
            )


def test_first_time_setup_still_accepts_the_newly_deployed_complete_suite(
    deploy3r,
    fork,
):
    with boa.env.anchor():
        token_args = (
            ZERO_ADDRESS,
            deploy3r,
            PARAMS[fork]["MIN_HQ_CHANGE_TIMELOCK"],
            PARAMS[fork]["MAX_HQ_CHANGE_TIMELOCK"],
            0,
            ZERO_ADDRESS,
        )
        green = boa.load("contracts/tokens/GreenToken.vy", *token_args)
        ripe = boa.load("contracts/tokens/RipeToken.vy", *token_args)
        savings = boa.load(
            "contracts/tokens/SavingsGreen.vy",
            green,
            *token_args,
        )
        hq = _deploy_hq(green, savings, ripe, deploy3r, fork)

        for token in (green, savings, ripe):
            assert token.finishTokenSetup(hq, sender=deploy3r)
            assert token.ripeHq() == hq.address
            assert token.getCCIPAdmin() == deploy3r
