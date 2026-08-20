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
    ripe_token.approve(c.address, FLOAT, sender=whale)
    c.fundFloat(FLOAT, sender=whale)
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


# These began as proof-of-concept exploits against the pre-fix contract. The
# attack narratives are kept verbatim because they are the clearest statement of
# what each control exists to stop; each now asserts the exploit is blocked.


# ---------- F-1: a matured UNPAUSE must not outlive a guardian pause ----------

def test_f1_stale_unpause_cannot_defeat_guardian_pause(flf, solver, bob, alice, charlie):
    flf.setGuardian(alice, True, sender=charlie)

    # an unpause can no longer even be staged while the lane is running, which
    # removes the pre-matured action the attack depended on
    with boa.reverts("not paused"):
        flf.initiateChange(ACTION_UNPAUSE, ZERO_ADDRESS, 0, sender=charlie)

    # and one staged during a real pause dies if anything is tightened after it
    flf.pauseLane(sender=alice)
    stale = flf.initiateChange(ACTION_UNPAUSE, ZERO_ADDRESS, 0, sender=charlie)
    boa.env.time_travel(blocks=11)
    flf.clearSolverSigner(sender=alice)
    with boa.reverts("stale action"):
        flf.confirmChange(stale, sender=charlie)
    assert flf.lanePaused()


# ---------- F-2: a matured SET_SOLVER must not revive a pre-signed backlog ----------

def test_f2_stale_set_solver_cannot_revive_presigned_orders(flf, solver, bob, alice, charlie):
    flf.setGuardian(alice, True, sender=charlie)

    backlog = [_order(bob, MAX_FILL, salt=bytes([i]) * 32, deadline=boa.env.timestamp + 10**9)
               for i in range(3)]
    sigs = [_sign(flf, solver, o) for o in backlog]

    stale = flf.initiateChange(ACTION_SET_SOLVER, solver.address, 0, sender=charlie)
    boa.env.time_travel(blocks=11)

    # incident: guardian burns the solver key
    flf.clearSolverSigner(sender=alice)
    assert flf.solverSigner() == ZERO_ADDRESS
    with boa.reverts("not solver"):
        flf.fill(backlog[0], sigs[0], sender=solver.address)

    # the staged rotation is void. Note what this does and does not prove: the
    # *stale* path is closed, not the backlog. See
    # test_h8_reinstating_a_burned_signer_revives_the_backlog for the rest.
    with boa.reverts("stale action"):
        flf.confirmChange(stale, sender=charlie)
    assert flf.solverSigner() == ZERO_ADDRESS
    with boa.reverts("not solver"):
        flf.fill(backlog[0], sigs[0], sender=solver.address)


# ---------- F-3: value must not leave a live or paused instance ----------

def test_f3_withdrawal_cannot_drain_a_live_or_paused_instance(
    flf, ripe_token, float_recipient, alice, charlie
):
    flf.setGuardian(alice, True, sender=charlie)
    assert flf.minFloatBalance() == FLOOR

    # a withdrawal cannot even be staged against a live instance
    with boa.reverts("not retired"):
        flf.initiateChange(ACTION_WITHDRAW, ZERO_ADDRESS, FLOAT, sender=charlie)

    # nor against a merely paused one: pausing is reversible, retirement is not
    flf.pauseLane(sender=alice)
    with boa.reverts("not retired"):
        flf.initiateChange(ACTION_WITHDRAW, ZERO_ADDRESS, FLOAT, sender=charlie)
    assert ripe_token.balanceOf(flf.address) == FLOAT


# ---------- F-4: the drain floor must not be deployable inert or zeroable ----------

def test_f4_floor_cannot_be_zero_at_deploy(ripe_hq_deploy, ripe_token, float_recipient, charlie):
    with boa.reverts("invalid floor"):
        boa.load(
            "contracts/core/FastLaneFloat.vy",
            ripe_hq_deploy.address, ripe_token.address, float_recipient, charlie,
            10, 1_000, MAX_FILL, MAX_EXPOSURE, MAX_ENTRIES, MAX_AGE,
            0,
            name="flf_no_floor",
        )


def test_f4_floor_cannot_be_lowered_to_zero(flf, charlie):
    with boa.reverts("zero floor"):
        flf.initiateChange(5, ZERO_ADDRESS, 0, sender=charlie)


# ---------- F-1c: a matured cap raise must not undo an emergency lowerCaps ----------

def test_f1c_stale_cap_raise_cannot_undo_emergency_lower_caps(flf, charlie):
    stale = flf.initiateCapRaise(MAX_FILL * 2, MAX_EXPOSURE * 2, MAX_ENTRIES, MAX_AGE, sender=charlie)
    boa.env.time_travel(blocks=11)

    flf.lowerCaps(1 * EIGHTEEN_DECIMALS, 1 * EIGHTEEN_DECIMALS, 1, 60, sender=charlie)
    assert flf.maxAggregateExposure() == 1 * EIGHTEEN_DECIMALS

    # the tightening bumped the epoch, so the staged raise is void
    with boa.reverts("stale action"):
        flf.confirmChange(stale, sender=charlie)
    assert flf.maxAggregateExposure() == 1 * EIGHTEEN_DECIMALS
    assert flf.maxFillAmount() == 1 * EIGHTEEN_DECIMALS


# ---------- H-8 residual: what configEpoch does not reach ----------


def test_h8_reinstating_a_burned_signer_revives_the_backlog(flf, solver, bob, alice, charlie):
    """A *fresh* rotation back to a burned address - no stale action, full
    timelock served, configEpoch current - revives every unfilled order that key
    ever signed. `configEpoch` guards pending actions, not signed orders.

    Bounded in practice by `fill`'s `msg.sender == solverSigner` gate: an
    attacker who cannot submit as the solver cannot use the backlog, and one who
    can does not need it. Recorded because the contract keeps no durable mark
    that an address was ever burned, so reinstating one is indistinguishable
    from any other rotation.
    """
    flf.setGuardian(alice, True, sender=charlie)

    backlog = [_order(bob, MAX_FILL, salt=bytes([i]) * 32, deadline=boa.env.timestamp + 10**9)
               for i in range(3)]
    sigs = [_sign(flf, solver, o) for o in backlog]

    flf.clearSolverSigner(sender=alice)
    epoch_after_clear = flf.configEpoch()
    with boa.reverts("not solver"):
        flf.fill(backlog[0], sigs[0], sender=solver.address)

    aid = flf.initiateChange(ACTION_SET_SOLVER, solver.address, 0, sender=charlie)
    boa.env.time_travel(blocks=11)
    flf.confirmChange(aid, sender=charlie)          # not stale: queued after the clear
    assert flf.configEpoch() == epoch_after_clear   # nothing invalidated the orders
    assert flf.solverSigner() == solver.address

    before = flf.outstandingNotional()
    for o, s in zip(backlog, sigs):
        flf.fill(o, s, sender=solver.address)
    assert flf.outstandingNotional() == before + 3 * MAX_FILL


def test_h8_deadline_is_unbounded_so_a_stale_order_still_fills(flf, solver, bob):
    """`deadline` is checked but not bounded, so the contract accepts an order
    whose terms were priced arbitrarily long ago. A fast lane quotes in seconds;
    this one fills a century later. The stated purpose of
    `outputAmount <= inputAmount` is to catch a *buggy* solver overpaying against
    a real deposit, and a dropped-then-replayed order is exactly that bug.
    """
    o = _order(bob, MAX_FILL, deadline=2**255, salt=b"\xaa" * 32)
    sig = _sign(flf, solver, o)

    boa.env.time_travel(seconds=100 * 365 * 24 * 3600)
    flf.fill(o, sig, sender=solver.address)
    assert flf.outstandingNotional() == MAX_FILL
