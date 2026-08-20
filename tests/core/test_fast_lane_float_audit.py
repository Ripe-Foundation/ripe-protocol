import boa
import pytest
from eth_account import Account

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS

MAX_FILL = 1_000 * EIGHTEEN_DECIMALS
MAX_EXPOSURE = 5_000 * EIGHTEEN_DECIMALS
MAX_ENTRIES = 5
MAX_AGE = 3_600
FLOOR = 1_000 * EIGHTEEN_DECIMALS
FLOAT = 100_000 * EIGHTEEN_DECIMALS

ACTION_SET_SOLVER = 1
ACTION_UNPAUSE = 3
ACTION_WITHDRAW = 4


@pytest.fixture(scope="module")
def solver():
    return Account.create()


@pytest.fixture(scope="module")
def float_recipient(env):
    return env.generate_address("float_recipient")


@pytest.fixture
def flf(ripe_hq_deploy, ripe_token, float_recipient, charlie, whale, solver):
    c = boa.load(
        "contracts/core/FastLaneFloat.vy",
        ripe_hq_deploy.address, ripe_token.address, float_recipient, charlie,
        10, 1_000, MAX_FILL, MAX_EXPOSURE, MAX_ENTRIES, MAX_AGE, FLOOR,
        name="fast_lane_float",
    )
    ripe_token.transfer(c.address, FLOAT, sender=whale)
    aid = c.initiateChange(ACTION_SET_SOLVER, solver.address, 0, sender=charlie)
    boa.env.time_travel(blocks=11)
    c.confirmChange(aid, sender=charlie)
    aid = c.initiateChange(ACTION_UNPAUSE, ZERO_ADDRESS, 0, sender=charlie)
    boa.env.time_travel(blocks=11)
    c.confirmChange(aid, sender=charlie)
    c.setQuoteThreshold(MAX_EXPOSURE, sender=charlie)
    return c


def _order(recipient, amount, out=None, origin=8453, deadline=None, salt=None):
    return (recipient, amount, out if out is not None else amount, origin,
            deadline if deadline is not None else boa.env.timestamp + 3600,
            salt or boa.env.timestamp.to_bytes(32, "big"))


def _sign(flf, solver, order):
    return bytes(Account._sign_hash(flf.getDigest(order), solver.key).signature)


def _fill(flf, solver, order):
    return flf.fill(order, _sign(flf, solver, order), sender=solver.address)


# ---------- F-1: a matured UNPAUSE outlives and instantly defeats a guardian pause ----------

def test_poc_f1_stale_unpause_defeats_guardian_pause(flf, solver, bob, alice, charlie):
    flf.setGuardian(alice, True, sender=charlie)

    # routine ops: governance stages an unpause and lets it mature. Lane is not
    # even paused right now, so nothing looks wrong.
    stale = flf.initiateChange(ACTION_UNPAUSE, ZERO_ADDRESS, 0, sender=charlie)
    boa.env.time_travel(blocks=11)

    # incident: guardian halts the lane
    flf.pauseLane(sender=alice)
    assert flf.lanePaused()
    with boa.reverts():
        _fill(flf, solver, _order(bob, 10 * EIGHTEEN_DECIMALS))

    # the halt lasts exactly one transaction: the pre-staged action is still live
    assert flf.canConfirmAction(stale)
    flf.confirmChange(stale, sender=charlie)
    assert not flf.lanePaused()
    _fill(flf, solver, _order(bob, 10 * EIGHTEEN_DECIMALS, salt=b"\x01" * 32))


# ---------- F-2: a matured SET_SOLVER + no order invalidation revives a pre-signed backlog ----------

def test_poc_f2_stale_set_solver_revives_presigned_orders(flf, solver, bob, alice, charlie):
    flf.setGuardian(alice, True, sender=charlie)

    # attacker (or a solver that later gets rotated out) pre-signs a backlog.
    # These are never filled, so `isFilled` never records them.
    backlog = [_order(bob, MAX_FILL, salt=bytes([i]) * 32, deadline=boa.env.timestamp + 10**9)
               for i in range(3)]
    sigs = [_sign(flf, solver, o) for o in backlog]

    # routine ops: a solver rotation is staged and matures
    stale = flf.initiateChange(ACTION_SET_SOLVER, solver.address, 0, sender=charlie)
    boa.env.time_travel(blocks=11)

    # incident: guardian burns the solver key
    flf.clearSolverSigner(sender=alice)
    assert flf.solverSigner() == ZERO_ADDRESS
    with boa.reverts():
        flf.fill(backlog[0], sigs[0], sender=solver.address)

    # one transaction reinstates it, and every pre-signed order is live again
    flf.confirmChange(stale, sender=charlie)
    assert flf.solverSigner() == solver.address
    before = flf.outstandingNotional()
    for o, s in zip(backlog, sigs):
        flf.fill(o, s, sender=solver.address)
    assert flf.outstandingNotional() == before + 3 * MAX_FILL


# ---------- F-3: pauseLane does not block confirmChange; WITHDRAW ignores the drain floor ----------

def test_poc_f3_paused_lane_still_confirms_full_withdrawal_below_floor(
    flf, ripe_token, float_recipient, alice, charlie
):
    flf.setGuardian(alice, True, sender=charlie)
    assert flf.minFloatBalance() == FLOOR

    aid = flf.initiateChange(ACTION_WITHDRAW, ZERO_ADDRESS, FLOAT, sender=charlie)
    boa.env.time_travel(blocks=11)

    # guardian halts the lane; the pause is meant to stop value leaving
    flf.pauseLane(sender=alice)
    assert flf.lanePaused()

    # it does not stop this
    flf.confirmChange(aid, sender=charlie)
    assert ripe_token.balanceOf(flf.address) == 0        # floor was 1_000e18
    assert ripe_token.balanceOf(float_recipient) == FLOAT


# ---------- F-4: the drain floor can be deployed inert, and lowered to zero ----------

def test_poc_f4_floor_can_be_zero_at_deploy(ripe_hq_deploy, ripe_token, float_recipient, charlie):
    c = boa.load(
        "contracts/core/FastLaneFloat.vy",
        ripe_hq_deploy.address, ripe_token.address, float_recipient, charlie,
        10, 1_000, MAX_FILL, MAX_EXPOSURE, MAX_ENTRIES, MAX_AGE,
        0,  # every other cap is asserted non-zero; this one is not
        name="flf_no_floor",
    )
    assert c.minFloatBalance() == 0


def test_poc_f4_floor_can_be_lowered_to_zero(flf, charlie):
    aid = flf.initiateChange(5, ZERO_ADDRESS, 0, sender=charlie)  # ACTION_LOWER_FLOOR to 0
    boa.env.time_travel(blocks=11)
    flf.confirmChange(aid, sender=charlie)
    assert flf.minFloatBalance() == 0


# ---------- F-1c: a matured cap raise undoes an emergency lowerCaps in one tx ----------

def test_poc_f1c_stale_cap_raise_undoes_emergency_lower_caps(flf, charlie):
    stale = flf.initiateCapRaise(MAX_FILL * 2, MAX_EXPOSURE * 2, MAX_ENTRIES, MAX_AGE, sender=charlie)
    boa.env.time_travel(blocks=11)

    # incident: governance slams the caps down. This is the only immediate
    # lever that tightens the loss bound.
    flf.lowerCaps(1 * EIGHTEEN_DECIMALS, 1 * EIGHTEEN_DECIMALS, 1, 60, sender=charlie)
    assert flf.maxAggregateExposure() == 1 * EIGHTEEN_DECIMALS

    # and it is reverted, with no re-validation against current state
    flf.confirmChange(stale, sender=charlie)
    assert flf.maxFillAmount() == MAX_FILL * 2
    assert flf.maxAggregateExposure() == MAX_EXPOSURE * 2
    assert flf.maxEntryAge() == MAX_AGE
