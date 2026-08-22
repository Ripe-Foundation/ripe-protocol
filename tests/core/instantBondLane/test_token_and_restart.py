import boa
import pytest

from conf_utils import get_boa_dev_reasons
from constants import MAX_UINT256

from tests.core.instantBondLane.conftest import make_config, settlement_accounting


def test_stop_then_new_seed_then_start_uses_the_new_seed(lane_env):
    first = lane_env.buy(lane_env.scale)
    assert lane_env.lane.epochState().rate == 10**18
    lane_env.stop()
    lane_env.set_config(seedRate=11 * 10**17)
    lane_env.start(0)
    assert lane_env.lane.epochState().rate == 0
    quote = lane_env.quote(lane_env.scale)
    assert quote.rate == 11 * 10**17
    payout = lane_env.buy(lane_env.scale)
    assert payout != first
    assert lane_env.lane.epochState().rate == 11 * 10**17
    assert lane_env.lane.epochState().epoch == 0


def test_token_swap_without_matching_config_empties_preview_and_blocks_start(
    lane_env, governance
):
    other = boa.load(
        "contracts/mock/MockErc20.vy",
        governance,
        "Other",
        "OTH",
        8,
        1_000_000,
    )
    old_funds = lane_env.payment_token.balanceOf(lane_env.endaoment_funds)
    lane_env.stop()
    lane_env.lane.setPaymentToken(other.address, sender=lane_env.switchboard.address)

    empty = lane_env.quote(lane_env.scale)
    assert empty.available is False
    assert empty.rate == 0
    assert empty.totalRipe == 0

    with pytest.raises(boa.BoaError) as err:
        lane_env.start(0)
    assert "not configured" in get_boa_dev_reasons(err.value)

    new_scale = 10**8
    lane_env.lane.setConfig(
        make_config(new_scale, epoch_length=lane_env.lane.epochLength()),
        sender=lane_env.switchboard.address,
    )
    lane_env.start(0)
    other.transfer(lane_env.bob, 100 * new_scale, sender=governance.address)
    other.approve(lane_env.lane, MAX_UINT256, sender=lane_env.bob)

    quote = lane_env.lane.previewBuyNow(new_scale, 0, sender=lane_env.bob)
    assert quote.available is True
    payout = lane_env.lane.buyNow(
        new_scale,
        0,
        quote.epoch,
        quote.totalRipe,
        boa.env.evm.patch.block_number,
        sender=lane_env.bob,
    )
    assert payout == quote.totalRipe
    assert other.balanceOf(lane_env.endaoment_funds) == new_scale
    assert lane_env.payment_token.balanceOf(lane_env.endaoment_funds) == old_funds


def test_ripe_pause_keeps_preview_available_but_blocks_mint(lane_env):
    quote = lane_env.quote(lane_env.scale)
    assert quote.available is True
    lane_env.ripe_token.pause(True, sender=lane_env.governance.address)
    still = lane_env.quote(lane_env.scale)
    assert still.available is True
    assert still.totalRipe == quote.totalRipe
    before = settlement_accounting(lane_env)
    with pytest.raises(boa.BoaError) as err:
        lane_env.buy(lane_env.scale)
    assert "token paused" in get_boa_dev_reasons(err.value)
    assert settlement_accounting(lane_env) == before


def test_blacklisted_buyer_blocks_unlocked_mint_only(lane_env, switchboard):
    lane_env.setup_lock_terms(min_lock=100, max_lock=1_000)
    lane_env.ripe_token.setBlacklist(lane_env.bob, True, sender=switchboard.address)
    unlocked = lane_env.quote(lane_env.scale, 0)
    assert unlocked.available is True
    before = settlement_accounting(lane_env)
    with pytest.raises(boa.BoaError) as err:
        lane_env.buy(lane_env.scale, requested_lock=0)
    assert "blacklisted" in get_boa_dev_reasons(err.value)
    assert settlement_accounting(lane_env) == before

    locked = lane_env.quote(lane_env.scale, 500)
    assert locked.available is True
    payout = lane_env.buy(lane_env.scale, requested_lock=500)
    assert payout == locked.totalRipe
    assert lane_env.ripe_token.balanceOf(lane_env.bob) == before[6]
    assert (
        lane_env.ripe_gov_vault.getTotalAmountForUser(
            lane_env.bob, lane_env.ripe_token
        )
        == payout
    )


def test_blacklisted_lane_blocks_locked_mint(lane_env, switchboard):
    lane_env.setup_lock_terms(min_lock=100, max_lock=1_000)
    lane_env.ripe_token.setBlacklist(lane_env.lane, True, sender=switchboard.address)
    quote = lane_env.quote(lane_env.scale, 500)
    assert quote.available is True
    before = settlement_accounting(lane_env)
    with pytest.raises(boa.BoaError) as err:
        lane_env.buy(lane_env.scale, requested_lock=500)
    assert "blacklisted" in get_boa_dev_reasons(err.value)
    assert settlement_accounting(lane_env) == before
