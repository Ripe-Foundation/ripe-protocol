import boa
import pytest

from conf_utils import get_boa_dev_reasons
from constants import MAX_UINT256

from tests.core.instantBondLane.conftest import settlement_accounting


def _fund_alice(ctx, alice, charlie_token_whale):
    ctx.payment_token.transfer(alice, 100 * ctx.scale, sender=charlie_token_whale)
    ctx.payment_token.approve(ctx.lane, MAX_UINT256, sender=alice)


def test_unlocked_buy_still_works_when_protocol_deposits_are_disabled(lane_env):
    lane_env.setup_lock_terms(min_lock=100, max_lock=1_000, can_deposit=False)
    quote = lane_env.quote(lane_env.scale, 0)
    assert quote.available is True
    assert quote.actualLock == 0
    assert lane_env.buy(lane_env.scale) == quote.totalRipe


def test_locked_buy_reverts_atomically_when_protocol_deposits_are_disabled(lane_env):
    lane_env.setup_lock_terms(min_lock=100, max_lock=1_000, can_deposit=False)
    quote = lane_env.quote(lane_env.scale, 500)
    assert quote.available is True
    assert quote.actualLock == 500
    before = settlement_accounting(lane_env)
    with pytest.raises(boa.BoaError) as err:
        lane_env.buy(lane_env.scale, requested_lock=500)
    assert "protocol deposits disabled" in get_boa_dev_reasons(err.value)
    assert settlement_accounting(lane_env) == before


def test_locked_buy_reverts_atomically_when_ripe_deposits_are_disabled(lane_env):
    lane_env.setup_lock_terms(min_lock=100, max_lock=1_000, asset_can_deposit=False)
    quote = lane_env.quote(lane_env.scale, 500)
    assert quote.available is True
    before = settlement_accounting(lane_env)
    with pytest.raises(boa.BoaError) as err:
        lane_env.buy(lane_env.scale, requested_lock=500)
    assert "asset deposits disabled" in get_boa_dev_reasons(err.value)
    assert settlement_accounting(lane_env) == before


def test_preview_shows_zero_vault_id_but_buy_reverts_in_lootbox(lane_env):
    lane_env.setup_lock_terms(min_lock=100, max_lock=1_000)
    lane_env.mission_control.eval("self.coreRipeGovVaultId = 0")
    quote = lane_env.quote(lane_env.scale, 500)
    assert quote.available is True
    assert quote.ripeGovVaultId == 0
    before = settlement_accounting(lane_env)
    with pytest.raises(boa.BoaError) as err:
        lane_env.buy(lane_env.scale, requested_lock=500)
    assert "invalid vault id" in get_boa_dev_reasons(err.value)
    assert settlement_accounting(lane_env) == before


def test_locked_buy_reverts_atomically_when_core_vault_id_is_unknown(lane_env):
    lane_env.setup_lock_terms(min_lock=100, max_lock=1_000)
    lane_env.mission_control.setCoreRipeGovVaultId(
        999, sender=lane_env.switchboard.address
    )
    quote = lane_env.quote(lane_env.scale, 500)
    assert quote.available is True
    assert quote.ripeGovVaultId == 999
    before = settlement_accounting(lane_env)
    with pytest.raises(boa.BoaError) as err:
        lane_env.buy(lane_env.scale, requested_lock=500)
    assert "invalid vault id" in get_boa_dev_reasons(err.value)
    assert settlement_accounting(lane_env) == before


def test_locked_buy_reverts_atomically_when_position_has_migrated_out(lane_env):
    lane_env.setup_lock_terms(min_lock=100, max_lock=1_000)
    lane_env.ripe_gov_vault.eval(
        f"self.positionMigratedOut[{lane_env.bob}][{lane_env.ripe_token.address}] = True"
    )
    quote = lane_env.quote(lane_env.scale, 500)
    assert quote.available is True
    before = settlement_accounting(lane_env)
    with pytest.raises(boa.BoaError) as err:
        lane_env.buy(lane_env.scale, requested_lock=500)
    assert "position migrated" in get_boa_dev_reasons(err.value)
    assert settlement_accounting(lane_env) == before


def test_second_locked_buy_merges_into_a_weighted_vault_lock(lane_env):
    terms = lane_env.setup_lock_terms(min_lock=100, max_lock=1_000)
    lane_env.set_config(minLockDuration=0, maxLockBonus=0)
    first = lane_env.buy(lane_env.scale, requested_lock=100)
    first_data = lane_env.ripe_gov_vault.userGovData(
        lane_env.bob, lane_env.ripe_token
    )
    assert first_data.unlock == boa.env.evm.patch.block_number + 100

    second = lane_env.buy(2 * lane_env.scale, requested_lock=1_000)
    second_data = lane_env.ripe_gov_vault.userGovData(
        lane_env.bob, lane_env.ripe_token
    )
    expected_unlock = lane_env.ripe_gov_vault.getWeightedLockOnTokenDeposit(
        second_data.lastShares - first_data.lastShares,
        1_000,
        terms,
        first_data.lastShares,
        first_data.unlock,
    )
    assert second_data.unlock == expected_unlock
    assert second_data.unlock > first_data.unlock
    assert (
        lane_env.ripe_gov_vault.getTotalAmountForUser(
            lane_env.bob, lane_env.ripe_token
        )
        == first + second
    )


def test_locked_position_cannot_be_withdrawn_before_unlock(lane_env):
    lane_env.setup_lock_terms(min_lock=100, max_lock=1_000)
    payout = lane_env.buy(lane_env.scale, requested_lock=500)
    vault_id = lane_env.mission_control.coreRipeGovVaultId()
    with pytest.raises(boa.BoaError) as err:
        lane_env.teller.withdraw(
            lane_env.ripe_token,
            payout,
            lane_env.bob,
            lane_env.ripe_gov_vault,
            vault_id,
            sender=lane_env.bob,
        )
    assert "not reached unlock" in get_boa_dev_reasons(err.value)


def test_locked_position_can_be_withdrawn_after_unlock(lane_env):
    lane_env.setup_lock_terms(min_lock=100, max_lock=1_000)
    payout = lane_env.buy(lane_env.scale, requested_lock=500)
    unlock = lane_env.ripe_gov_vault.userGovData(
        lane_env.bob, lane_env.ripe_token
    ).unlock
    boa.env.time_travel(blocks=unlock - boa.env.evm.patch.block_number + 1)
    ripe_before = lane_env.ripe_token.balanceOf(lane_env.bob)
    vault_id = lane_env.mission_control.coreRipeGovVaultId()
    withdrawn = lane_env.teller.withdraw(
        lane_env.ripe_token,
        payout,
        lane_env.bob,
        lane_env.ripe_gov_vault,
        vault_id,
        sender=lane_env.bob,
    )
    assert withdrawn == payout
    assert lane_env.ripe_token.balanceOf(lane_env.bob) == ripe_before + payout
    assert (
        lane_env.ripe_gov_vault.getTotalAmountForUser(
            lane_env.bob, lane_env.ripe_token
        )
        == 0
    )


def test_bad_debt_freeze_blocks_withdraw_after_unlock(lane_env):
    lane_env.setup_lock_terms(
        min_lock=100,
        max_lock=1_000,
        freeze_on_bad_debt=True,
    )
    payout = lane_env.buy(lane_env.scale, requested_lock=500)
    unlock = lane_env.ripe_gov_vault.userGovData(
        lane_env.bob, lane_env.ripe_token
    ).unlock
    boa.env.time_travel(blocks=unlock - boa.env.evm.patch.block_number + 1)
    lane_env.ledger.setBadDebt(1, sender=lane_env.switchboard.address)
    vault_id = lane_env.mission_control.coreRipeGovVaultId()
    with pytest.raises(boa.BoaError) as err:
        lane_env.teller.withdraw(
            lane_env.ripe_token,
            payout,
            lane_env.bob,
            lane_env.ripe_gov_vault,
            vault_id,
            sender=lane_env.bob,
        )
    assert "cannot withdraw when bad debt" in get_boa_dev_reasons(err.value)

    lane_env.ledger.setBadDebt(0, sender=lane_env.switchboard.address)
    withdrawn = lane_env.teller.withdraw(
        lane_env.ripe_token,
        payout,
        lane_env.bob,
        lane_env.ripe_gov_vault,
        vault_id,
        sender=lane_env.bob,
    )
    assert withdrawn == payout


def test_early_exit_reverts_when_buyer_is_the_only_holder(lane_env):
    lane_env.setup_lock_terms(
        min_lock=100,
        max_lock=1_000,
        can_exit=True,
        exit_fee=500,
    )
    lane_env.buy(lane_env.scale, requested_lock=1_000)
    with pytest.raises(boa.BoaError) as err:
        lane_env.teller.releaseLock(lane_env.ripe_token, sender=lane_env.bob)
    assert "no remaining holders" in get_boa_dev_reasons(err.value)


def test_early_exit_then_withdraw_requires_another_holder(
    lane_env, alice, charlie_token_whale
):
    lane_env.setup_lock_terms(
        min_lock=100,
        max_lock=1_000,
        can_exit=True,
        exit_fee=500,
    )
    _fund_alice(lane_env, alice, charlie_token_whale)
    lane_env.buy(lane_env.scale, requested_lock=1_000, sender=alice)
    bob_payout = lane_env.buy(lane_env.scale, requested_lock=1_000)
    assert (
        lane_env.ripe_gov_vault.userGovData(
            lane_env.bob, lane_env.ripe_token
        ).unlock
        > boa.env.evm.patch.block_number
    )

    lane_env.teller.releaseLock(lane_env.ripe_token, sender=lane_env.bob)
    assert (
        lane_env.ripe_gov_vault.userGovData(
            lane_env.bob, lane_env.ripe_token
        ).unlock
        == 0
    )
    remaining = lane_env.ripe_gov_vault.getTotalAmountForUser(
        lane_env.bob, lane_env.ripe_token
    )
    assert 0 < remaining < bob_payout

    vault_id = lane_env.mission_control.coreRipeGovVaultId()
    withdrawn = lane_env.teller.withdraw(
        lane_env.ripe_token,
        remaining,
        lane_env.bob,
        lane_env.ripe_gov_vault,
        vault_id,
        sender=lane_env.bob,
    )
    assert withdrawn == remaining
    assert (
        lane_env.ripe_gov_vault.getTotalAmountForUser(
            lane_env.bob, lane_env.ripe_token
        )
        == 0
    )
