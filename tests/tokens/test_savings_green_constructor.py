import boa

from config.BluePrint import PARAMS
from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS


def _deploy_savings_green(
    green_token,
    deploy3r,
    fork,
    initial_supply,
    initial_supply_recipient,
):
    return boa.load(
        "contracts/tokens/SavingsGreen.vy",
        green_token,
        ZERO_ADDRESS,
        deploy3r,
        PARAMS[fork]["MIN_HQ_CHANGE_TIMELOCK"],
        PARAMS[fork]["MAX_HQ_CHANGE_TIMELOCK"],
        initial_supply,
        initial_supply_recipient,
    )


def test_zero_initial_supply_deploys_successfully(
    green_token,
    deploy3r,
    fork,
):
    savings_green = _deploy_savings_green(
        green_token,
        deploy3r,
        fork,
        0,
        ZERO_ADDRESS,
    )

    assert savings_green.name() == "Savings Green USD"
    assert savings_green.symbol() == "sGREEN"
    assert savings_green.decimals() == green_token.decimals()
    assert savings_green.asset() == green_token.address
    assert savings_green.totalSupply() == 0
    assert savings_green.totalAssets() == 0


def test_zero_initial_supply_with_nonzero_recipient_mints_no_shares(
    green_token,
    deploy3r,
    fork,
    bob,
):
    savings_green = _deploy_savings_green(
        green_token,
        deploy3r,
        fork,
        0,
        bob,
    )

    assert savings_green.totalSupply() == 0
    assert savings_green.totalAssets() == 0
    assert savings_green.balanceOf(bob) == 0


def test_nonzero_initial_supply_with_valid_recipient_reverts(
    green_token,
    deploy3r,
    fork,
    bob,
):
    with boa.reverts("invalid initial supply"):
        _deploy_savings_green(
            green_token,
            deploy3r,
            fork,
            EIGHTEEN_DECIMALS,
            bob,
        )


def test_nonzero_initial_supply_with_zero_address_reverts(
    green_token,
    deploy3r,
    fork,
):
    with boa.reverts("invalid initial supply"):
        _deploy_savings_green(
            green_token,
            deploy3r,
            fork,
            EIGHTEEN_DECIMALS,
            ZERO_ADDRESS,
        )


def test_zero_initial_supply_accepts_green_deposit_one_to_one(
    green_token,
    deploy3r,
    fork,
    whale,
    bob,
):
    savings_green = _deploy_savings_green(
        green_token,
        deploy3r,
        fork,
        0,
        ZERO_ADDRESS,
    )
    deposit_amount = 100 * EIGHTEEN_DECIMALS
    green_token.approve(savings_green, deposit_amount, sender=whale)

    shares = savings_green.deposit(deposit_amount, bob, sender=whale)

    assert shares == deposit_amount
    assert savings_green.balanceOf(bob) == deposit_amount
    assert savings_green.totalSupply() == deposit_amount
    assert savings_green.totalAssets() == deposit_amount
