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
        ripe_hq_deploy.address,
        ripe_token.address,
        float_recipient,
        charlie,  # local gov, must differ from RipeHq gov
        10,       # min timelock (blocks)
        1_000,    # max timelock
        MAX_FILL,
        MAX_EXPOSURE,
        MAX_ENTRIES,
        MAX_AGE,
        FLOOR,
        name="fast_lane_float",
    )
    ripe_token.approve(c.address, FLOAT, sender=whale)
    c.fundFloat(FLOAT, sender=whale)
    # charlie is local governance for this contract
    aid = c.initiateChange(1, solver.address, 0, sender=charlie)
    boa.env.time_travel(blocks=11)
    c.confirmChange(aid, sender=charlie)
    aid = c.initiateChange(3, ZERO_ADDRESS, 0, sender=charlie)  # unpause
    boa.env.time_travel(blocks=11)
    c.confirmChange(aid, sender=charlie)
    c.setQuoteThreshold(MAX_EXPOSURE, sender=charlie)
    return c


def _order(recipient, amount, out=None, origin=8453, deadline=None, salt=None):
    return (
        recipient,
        amount,
        out if out is not None else amount,
        origin,
        deadline if deadline is not None else boa.env.timestamp + 600,
        salt or boa.env.timestamp.to_bytes(32, "big"),
    )


def _sign(flf, solver, order):
    digest = flf.getDigest(order)
    sig = Account._sign_hash(digest, solver.key)
    return bytes(sig.signature)


def _restore(flf, token, whale, ids, amount, gov_sender):
    """Restoration requires real tokens to arrive, not a governance assertion."""
    token.transfer(flf.address, amount, sender=whale)
    return flf.recordRestored(ids, amount, sender=gov_sender)


def _fill(flf, solver, order):
    return flf.fill(order, _sign(flf, solver, order), sender=solver.address)


# ---------- happy path ----------


def test_fill_pays_recipient_and_records_exposure(flf, solver, bob, ripe_token):
    order = _order(bob, 100 * EIGHTEEN_DECIMALS)
    before = ripe_token.balanceOf(bob)
    order_id = _fill(flf, solver, order)

    assert ripe_token.balanceOf(bob) == before + 100 * EIGHTEEN_DECIMALS
    assert flf.isFilled(order_id)
    assert flf.outstandingNotional() == 100 * EIGHTEEN_DECIMALS
    assert flf.outstandingEntries() == 1
    assert flf.stageANotional() == 100 * EIGHTEEN_DECIMALS
    assert flf.oldestEntry() == order_id
    assert flf.isHealthy()


# ---------- authority ----------


def test_non_solver_caller_cannot_fill(flf, solver, bob, alice):
    """The solver signature is visible at quote time; without the caller gate a
    user holding a quote could claim the payout before ever depositing."""
    order = _order(bob, 100 * EIGHTEEN_DECIMALS)
    sig = _sign(flf, solver, order)
    with boa.reverts("not solver"):
        flf.fill(order, sig, sender=alice)


def test_wrong_signer_rejected(flf, bob):
    rogue = Account.create()
    order = _order(bob, 100 * EIGHTEEN_DECIMALS)
    digest = flf.getDigest(order)
    sig = bytes(Account._sign_hash(digest, rogue.key).signature)
    with boa.reverts("not solver"):
        flf.fill(order, sig, sender=rogue.address)


def test_signature_from_another_instance_is_rejected(flf, solver, bob, ripe_hq_deploy, ripe_token, float_recipient, charlie):
    """Domain separator binds address(this). A sibling deployment's signature
    must not be replayable here."""
    other = boa.load(
        "contracts/core/FastLaneFloat.vy",
        ripe_hq_deploy.address, ripe_token.address, float_recipient, charlie,
        10, 1_000, MAX_FILL, MAX_EXPOSURE, MAX_ENTRIES, MAX_AGE, FLOOR, name="flf_other",
    )
    order = _order(bob, 100 * EIGHTEEN_DECIMALS)
    foreign_sig = bytes(Account._sign_hash(other.getDigest(order), solver.key).signature)
    assert other.getDigest(order) != flf.getDigest(order)
    with boa.reverts("invalid signature"):
        flf.fill(order, foreign_sig, sender=solver.address)


def test_solver_cannot_free_capacity(flf, solver, bob):
    """A key that can clear the cap can drain the float regardless of its size."""
    order = _order(bob, 100 * EIGHTEEN_DECIMALS)
    order_id = _fill(flf, solver, order)
    with boa.reverts("no perms"):
        flf.recordWithdrawn([order_id], sender=solver.address)
    with boa.reverts("no perms"):
        flf.recordRestored([order_id], 1, sender=solver.address)


# ---------- H-6: the mintEnabled coupling ----------


def test_mint_disabled_blocks_fill_and_reenabling_restores_it(flf, solver, bob, ripe_hq_deploy, governance):
    """H-6. The fill is a plain transfer that never consults mintEnabled, while
    the CCIP refill leg is blocked by it. Without this coupling, disabling
    minting stops the float being replenished while it keeps draining."""
    ripe_hq_deploy.setMintingEnabled(False, sender=governance.address)
    order = _order(bob, 100 * EIGHTEEN_DECIMALS)
    with boa.reverts("minting disabled"):
        _fill(flf, solver, order)

    # paired assertion: the mint gate is the ONLY thing that closed it
    ripe_hq_deploy.setMintingEnabled(True, sender=governance.address)
    assert _fill(flf, solver, order) == flf.getOrderId(order)


# ---------- order terms ----------


def test_replay_rejected(flf, solver, bob):
    order = _order(bob, 100 * EIGHTEEN_DECIMALS)
    _fill(flf, solver, order)
    with boa.reverts("already filled"):
        _fill(flf, solver, order)


def test_expired_order_rejected(flf, solver, bob):
    order = _order(bob, 100 * EIGHTEEN_DECIMALS, deadline=boa.env.timestamp - 1)
    with boa.reverts("order expired"):
        _fill(flf, solver, order)


def test_overpay_rejected(flf, solver, bob):
    amt = 100 * EIGHTEEN_DECIMALS
    order = _order(bob, amt, out=amt + 1)
    with boa.reverts("overpay"):
        _fill(flf, solver, order)


def test_same_chain_order_rejected(flf, solver, bob):
    order = _order(bob, 100 * EIGHTEEN_DECIMALS, origin=boa.env.evm.patch.chain_id)
    with boa.reverts("same chain"):
        _fill(flf, solver, order)


def test_blacklisted_recipient_rejected(flf, solver, bob, ripe_token, switchboard):
    ripe_token.setBlacklist(bob, True, sender=switchboard.address)
    order = _order(bob, 100 * EIGHTEEN_DECIMALS)
    with boa.reverts("blacklisted recipient"):
        _fill(flf, solver, order)


def test_zero_output_rejected(flf, solver, bob):
    order = _order(bob, 100 * EIGHTEEN_DECIMALS, out=0)
    with boa.reverts("zero output"):
        _fill(flf, solver, order)


# ---------- caps: the security boundary ----------


def test_per_fill_cap_boundary(flf, solver, bob):
    ok = _order(bob, MAX_FILL, salt=b"\x01" * 32)
    _fill(flf, solver, ok)
    over = _order(bob, MAX_FILL + 1, salt=b"\x02" * 32)
    with boa.reverts("fill too large"):
        _fill(flf, solver, over)


def test_aggregate_exposure_cap(flf, solver, bob):
    for i in range(MAX_EXPOSURE // MAX_FILL):
        _fill(flf, solver, _order(bob, MAX_FILL, salt=bytes([i + 1]) * 32))
    assert flf.outstandingNotional() == MAX_EXPOSURE
    with boa.reverts("exposure cap"):
        _fill(flf, solver, _order(bob, 1 * EIGHTEEN_DECIMALS, salt=b"\xff" * 32))


def test_entry_count_cap(flf, solver, bob, charlie):
    flf.lowerCaps(MAX_FILL, MAX_EXPOSURE, 3, MAX_AGE, sender=charlie)
    for i in range(3):
        _fill(flf, solver, _order(bob, 1 * EIGHTEEN_DECIMALS, salt=bytes([i + 1]) * 32))
    with boa.reverts("entry cap"):
        _fill(flf, solver, _order(bob, 1 * EIGHTEEN_DECIMALS, salt=b"\xfe" * 32))


def test_age_cap_halts_new_fills(flf, solver, bob):
    _fill(flf, solver, _order(bob, 1 * EIGHTEEN_DECIMALS, salt=b"\x01" * 32))
    boa.env.time_travel(seconds=MAX_AGE + 1)
    with boa.reverts("exposure too old"):
        _fill(flf, solver, _order(bob, 1 * EIGHTEEN_DECIMALS, salt=b"\x02" * 32))
    assert not flf.isHealthy()


def test_valid_signature_without_a_real_deposit_is_bounded_by_caps(flf, solver, bob, ripe_token):
    """The contract cannot verify the origin deposit. If the solver key is
    compromised, this is the attack -- and the caps are what bound it."""
    start = ripe_token.balanceOf(flf.address)
    drained = 0
    for i in range(MAX_ENTRIES + 5):
        try:
            _fill(flf, solver, _order(bob, MAX_FILL, salt=bytes([i + 1]) * 32))
            drained += MAX_FILL
        except Exception:
            break
    assert drained <= MAX_EXPOSURE
    assert start - ripe_token.balanceOf(flf.address) <= MAX_EXPOSURE


# ---------- ledger ----------


def test_transition_does_not_free_aggregate_capacity(flf, solver, bob, charlie):
    order = _order(bob, 100 * EIGHTEEN_DECIMALS)
    order_id = _fill(flf, solver, order)
    before = flf.outstandingNotional()
    flf.recordWithdrawn([order_id], sender=charlie)
    assert flf.outstandingNotional() == before
    assert flf.outstandingEntries() == 1
    assert flf.stageANotional() == 0
    assert flf.stageBNotional() == before


def test_restoration_requires_real_tokens_not_a_governance_assertion(flf, solver, bob, charlie, ripe_token, whale):
    order_id = _fill(flf, solver, _order(bob, 100 * EIGHTEEN_DECIMALS))
    flf.recordWithdrawn([order_id], sender=charlie)
    _restore(flf, ripe_token, whale, [order_id], 100 * EIGHTEEN_DECIMALS, charlie)
    assert flf.outstandingNotional() == 0
    assert flf.outstandingEntries() == 0
    assert flf.oldestEntry() == b"\x00" * 32
    assert flf.isHealthy()


def test_out_of_order_restoration_keeps_oldest_correct(flf, solver, bob, charlie, ripe_token, whale):
    """Entries may settle in any order; the age clock must still track the true
    oldest outstanding entry."""
    ids = []
    for i in range(3):
        ids.append(_fill(flf, solver, _order(bob, 1 * EIGHTEEN_DECIMALS, salt=bytes([i + 1]) * 32)))
        boa.env.time_travel(seconds=10)
    assert flf.oldestEntry() == ids[0]
    # settle the middle one first
    flf.recordWithdrawn([ids[1]], sender=charlie)
    _restore(flf, ripe_token, whale, [ids[1]], 1 * EIGHTEEN_DECIMALS, charlie)
    assert flf.oldestEntry() == ids[0]
    # now settle the oldest
    flf.recordWithdrawn([ids[0]], sender=charlie)
    _restore(flf, ripe_token, whale, [ids[0]], 1 * EIGHTEEN_DECIMALS, charlie)
    assert flf.oldestEntry() == ids[2]
    assert flf.outstandingEntries() == 1


# ---------- levers ----------


def test_guardian_pauses_immediately_but_cannot_unpause(flf, solver, bob, alice, charlie):
    flf.setGuardian(alice, True, sender=charlie)
    flf.pauseLane(sender=alice)
    assert flf.lanePaused()
    with boa.reverts("lane paused"):
        _fill(flf, solver, _order(bob, 1 * EIGHTEEN_DECIMALS))
    with boa.reverts():
        flf.initiateChange(3, ZERO_ADDRESS, 0, sender=alice)


def test_unpause_requires_the_timelock(flf, charlie, alice):
    flf.setGuardian(alice, True, sender=charlie)
    flf.pauseLane(sender=alice)
    aid = flf.initiateChange(3, ZERO_ADDRESS, 0, sender=charlie)
    with boa.reverts("time lock not reached"):
        flf.confirmChange(aid, sender=charlie)
    boa.env.time_travel(blocks=11)
    flf.confirmChange(aid, sender=charlie)
    assert not flf.lanePaused()


def test_guardian_can_clear_solver_immediately(flf, solver, bob, alice, charlie):
    flf.setGuardian(alice, True, sender=charlie)
    flf.clearSolverSigner(sender=alice)
    assert flf.solverSigner() == ZERO_ADDRESS
    with boa.reverts("not solver"):
        _fill(flf, solver, _order(bob, 1 * EIGHTEEN_DECIMALS))


def test_caps_cannot_be_lowered_below_live_exposure(flf, solver, bob, charlie):
    """Bricking recordRestored would strand entries the contract must reconcile."""
    _fill(flf, solver, _order(bob, 500 * EIGHTEEN_DECIMALS))
    with boa.reverts("below live exposure"):
        flf.lowerCaps(MAX_FILL, 100 * EIGHTEEN_DECIMALS, MAX_ENTRIES, MAX_AGE, sender=charlie)


def test_caps_can_only_be_raised_through_the_timelock(flf, charlie):
    with boa.reverts("not a reduction"):
        flf.lowerCaps(MAX_FILL, MAX_EXPOSURE * 2, MAX_ENTRIES, MAX_AGE, sender=charlie)
    aid = flf.initiateCapRaise(MAX_FILL * 2, MAX_EXPOSURE * 2, MAX_ENTRIES, MAX_AGE, sender=charlie)
    with boa.reverts("time lock not reached"):
        flf.confirmChange(aid, sender=charlie)
    boa.env.time_travel(blocks=11)
    flf.confirmChange(aid, sender=charlie)
    assert flf.maxAggregateExposure() == MAX_EXPOSURE * 2
    assert flf.maxFillAmount() == MAX_FILL * 2


def test_every_cap_is_recoverable_after_being_lowered(flf, charlie):
    """A mis-set cap must not require a redeploy -- but must not be quick either."""
    flf.lowerCaps(1, 1, 1, 1, sender=charlie)
    with boa.reverts("not a raise"):
        flf.initiateCapRaise(1, 1, 1, 0, sender=charlie)
    aid = flf.initiateCapRaise(MAX_FILL, MAX_EXPOSURE, MAX_ENTRIES, MAX_AGE, sender=charlie)
    boa.env.time_travel(blocks=11)
    flf.confirmChange(aid, sender=charlie)
    assert flf.maxEntryAge() == MAX_AGE
    assert flf.maxOutstandingEntries() == MAX_ENTRIES


def test_lowering_exposure_clamps_the_advisory_threshold(flf, charlie):
    """The quote threshold must never advertise headroom the hard cap refuses."""
    assert flf.quoteThreshold() == MAX_EXPOSURE
    flf.lowerCaps(MAX_FILL, MAX_FILL, MAX_ENTRIES, MAX_AGE, sender=charlie)
    assert flf.quoteThreshold() == MAX_FILL


def test_solver_must_be_an_eoa(flf, charlie, governance):
    with boa.reverts("solver must be eoa"):
        flf.initiateChange(1, governance.address, 0, sender=charlie)


def test_live_float_cannot_be_swept(flf, solver, bob, charlie):
    """Sweeping a live instance would strand every outstanding entry."""
    _fill(flf, solver, _order(bob, 100 * EIGHTEEN_DECIMALS))
    with boa.reverts("not retired"):
        flf.initiateChange(4, ZERO_ADDRESS, 10 * EIGHTEEN_DECIMALS, sender=charlie)


def test_withdraw_requires_retirement_delay_and_quiescence(flf, solver, bob, charlie, float_recipient, ripe_token, whale):
    order_id = _fill(flf, solver, _order(bob, 100 * EIGHTEEN_DECIMALS))
    flf.retire(sender=charlie)
    assert flf.isRetired() and flf.lanePaused() and flf.solverSigner() == ZERO_ADDRESS

    with boa.reverts("retirement delay"):
        flf.initiateChange(4, ZERO_ADDRESS, 10 * EIGHTEEN_DECIMALS, sender=charlie)

    boa.env.time_travel(seconds=7 * 24 * 3600 + 1)
    with boa.reverts("live exposure"):
        flf.initiateChange(4, ZERO_ADDRESS, 10 * EIGHTEEN_DECIMALS, sender=charlie)

    flf.recordWithdrawn([order_id], sender=charlie)
    _restore(flf, ripe_token, whale, [order_id], 100 * EIGHTEEN_DECIMALS, charlie)
    aid = flf.initiateChange(4, ZERO_ADDRESS, 10 * EIGHTEEN_DECIMALS, sender=charlie)
    boa.env.time_travel(blocks=11)
    before = ripe_token.balanceOf(float_recipient)
    flf.confirmChange(aid, sender=charlie)
    assert ripe_token.balanceOf(float_recipient) == before + 10 * EIGHTEEN_DECIMALS


def test_retirement_is_one_way(flf, charlie, solver):
    flf.retire(sender=charlie)
    with boa.reverts("retired"):
        flf.initiateChange(3, ZERO_ADDRESS, 0, sender=charlie)
    with boa.reverts("retired"):
        flf.initiateChange(1, solver.address, 0, sender=charlie)
    with boa.reverts("retired"):
        flf.initiateCapRaise(MAX_FILL, MAX_EXPOSURE, MAX_ENTRIES, MAX_AGE, sender=charlie)


def test_instance_halts_when_the_token_hq_is_not_its_own(
    solver, bob, ripe_hq_deploy, ripe_token, green_token, savings_green,
    float_recipient, charlie, whale, deploy3r, fork,
):
    """The token's HQ is mutable. An instance whose immutable RIPE_HQ no longer
    matches the token's live HQ must refuse to fill: the old HQ can still report
    mint-enabled while this instance's refill authority is obsolete."""
    from config.BluePrint import PARAMS

    # a token whose HQ is a different deployment than the float is bound to
    other_hq = boa.load(
        "contracts/registries/RipeHq.vy",
        green_token.address, savings_green.address, ripe_token.address, deploy3r,
        PARAMS[fork]["RIPE_HQ_MIN_GOV_TIMELOCK"], PARAMS[fork]["RIPE_HQ_MAX_GOV_TIMELOCK"],
        PARAMS[fork]["RIPE_HQ_MIN_REG_TIMELOCK"], PARAMS[fork]["RIPE_HQ_MAX_REG_TIMELOCK"],
        name="other_hq",
    )
    stale = boa.load(
        "contracts/core/FastLaneFloat.vy",
        other_hq.address,           # this instance believes the token's HQ is other_hq
        ripe_token.address,         # but the token actually points at ripe_hq_deploy
        float_recipient, charlie, 10, 1_000,
        MAX_FILL, MAX_EXPOSURE, MAX_ENTRIES, MAX_AGE, FLOOR, name="flf_stale",
    )
    assert ripe_token.ripeHq() != other_hq.address
    assert other_hq.mintEnabled()      # the stale HQ still reports enabled
    assert not stale.canFill(1 * EIGHTEEN_DECIMALS)

    aid = stale.initiateChange(1, solver.address, 0, sender=charlie)
    boa.env.time_travel(blocks=11)
    stale.confirmChange(aid, sender=charlie)
    ripe_token.approve(stale.address, FLOAT, sender=whale)
    stale.fundFloat(FLOAT, sender=whale)
    aid = stale.initiateChange(3, ZERO_ADDRESS, 0, sender=charlie)
    boa.env.time_travel(blocks=11)
    stale.confirmChange(aid, sender=charlie)

    order = _order(bob, 1 * EIGHTEEN_DECIMALS)
    sig = bytes(Account._sign_hash(stale.getDigest(order), solver.key).signature)
    with boa.reverts("hq migrated"):
        stale.fill(order, sig, sender=solver.address)


def test_matured_unpause_cannot_undo_a_later_guardian_pause(flf, charlie, alice):
    """A matured action must not survive an emergency response taken after it
    was queued."""
    flf.setGuardian(alice, True, sender=charlie)
    with boa.reverts("not paused"):
        flf.initiateChange(3, ZERO_ADDRESS, 0, sender=charlie)

    flf.pauseLane(sender=alice)
    aid = flf.initiateChange(3, ZERO_ADDRESS, 0, sender=charlie)
    boa.env.time_travel(blocks=11)
    flf.clearSolverSigner(sender=alice)   # a later emergency action
    with boa.reverts("stale action"):
        flf.confirmChange(aid, sender=charlie)


# ---------- M-4: liveness ----------


def test_fill_gas_is_bounded_independent_of_entry_count(flf, solver, bob, charlie):
    """M-4. The age cap must not be enforced by scanning: a compromised key that
    cannot exceed the notional cap could otherwise raise fill cost without bound."""
    flf.lowerCaps(MAX_FILL, MAX_EXPOSURE, MAX_ENTRIES, MAX_AGE, sender=charlie)
    _fill(flf, solver, _order(bob, 1 * EIGHTEEN_DECIMALS, salt=b"\x01" * 32))
    first = flf._computation.get_gas_used()
    for i in range(2, MAX_ENTRIES + 1):
        _fill(flf, solver, _order(bob, 1 * EIGHTEEN_DECIMALS, salt=bytes([i]) * 32))
    last = flf._computation.get_gas_used()
    assert last <= first + 5_000, f"fill gas grew with entry count: {first} -> {last}"


def test_no_arbitrary_call_surface(flf):
    """No execute(to, data) escape hatch -- the pattern that makes Relay's own
    Depository a single-key total-loss risk. The only dynamic bytes this
    contract accepts anywhere is the solver signature on `fill`."""
    fns = [e for e in flf.abi if e.get("type") == "function"]
    assert fns, "no functions found in abi"
    for fn in fns:
        assert not fn.get("payable"), f"{fn['name']} is payable"
        for inp in fn.get("inputs", []):
            assert inp["type"] != "bytes" or fn["name"] == "fill", (
                f"{fn['name']} accepts arbitrary bytes"
            )


# ---------- the drain floor: cause-agnostic ----------


def test_aggregate_cap_is_what_stops_a_stalled_refill(flf, solver, bob, ripe_token):
    """Under normal configuration the AGGREGATE ledger closes admission when
    replenishment stalls -- not the floor. Exposure cannot clear without real
    tokens returning, so outstandingNotional climbs to the cap."""
    for i in range(1, MAX_ENTRIES + 1):
        try:
            _fill(flf, solver, _order(bob, MAX_FILL, salt=bytes([i]) * 32))
        except Exception:
            break
    assert flf.outstandingNotional() == MAX_EXPOSURE
    with boa.reverts("exposure cap"):
        _fill(flf, solver, _order(bob, 1 * EIGHTEEN_DECIMALS, salt=b"\xee" * 32))
    # the floor never came near binding: it is not the control that fired
    assert ripe_token.balanceOf(flf.address) > flf.minFloatBalance() * 90


def test_floor_binds_only_when_tighter_than_remaining_aggregate_capacity(flf, solver, bob, charlie, ripe_token):
    """The floor is a reserve invariant, not a refill-failure detector. It fires
    only where `balance - floor` is tighter than the remaining exposure room."""
    aid = flf.initiateCapRaise(MAX_FILL, MAX_EXPOSURE * 100, MAX_ENTRIES, MAX_AGE, sender=charlie)
    boa.env.time_travel(blocks=11)
    flf.confirmChange(aid, sender=charlie)
    flf.raiseFloatFloor(FLOAT - MAX_FILL, sender=charlie)

    _fill(flf, solver, _order(bob, MAX_FILL, salt=b"\x01" * 32))
    with boa.reverts("float floor"):
        _fill(flf, solver, _order(bob, MAX_FILL, salt=b"\x02" * 32))
    assert flf.outstandingNotional() < flf.maxAggregateExposure()


def test_floor_holds_even_if_the_exposure_ledger_is_wrong(flf, solver, bob, charlie, ripe_token, whale):
    """The floor's reason to exist: every other cap reads counters this contract
    maintains, so they fail together if that accounting is wrong. The floor reads
    balanceOf, so it still reserves inventory."""
    aid = flf.initiateCapRaise(MAX_FILL, MAX_EXPOSURE * 100, MAX_ENTRIES, MAX_AGE, sender=charlie)
    boa.env.time_travel(blocks=11)
    flf.confirmChange(aid, sender=charlie)
    flf.raiseFloatFloor(FLOAT - (2 * MAX_FILL), sender=charlie)

    ids = []
    for i in range(1, 3):
        ids.append(_fill(flf, solver, _order(bob, MAX_FILL, salt=bytes([i]) * 32)))

    # simulate the ledger being cleared without inventory returning, by funding
    # the restoration from elsewhere: the exposure counters go to zero...
    flf.recordWithdrawn(ids, sender=charlie)
    _restore(flf, ripe_token, whale, ids, 2 * MAX_FILL, charlie)
    assert flf.outstandingNotional() == 0

    # ...and the floor still refuses once the balance is spent down to it
    _fill(flf, solver, _order(bob, MAX_FILL, salt=b"\x0a" * 32))
    _fill(flf, solver, _order(bob, MAX_FILL, salt=b"\x0b" * 32))
    with boa.reverts("float floor"):
        _fill(flf, solver, _order(bob, MAX_FILL, salt=b"\x0c" * 32))


def test_floor_raises_immediately_but_lowers_only_through_the_timelock(flf, charlie):
    flf.raiseFloatFloor(FLOOR * 2, sender=charlie)
    assert flf.minFloatBalance() == FLOOR * 2
    with boa.reverts("not a raise"):
        flf.raiseFloatFloor(FLOOR, sender=charlie)
    aid = flf.initiateChange(5, ZERO_ADDRESS, FLOOR, sender=charlie)
    with boa.reverts("time lock not reached"):
        flf.confirmChange(aid, sender=charlie)
    boa.env.time_travel(blocks=11)
    flf.confirmChange(aid, sender=charlie)
    assert flf.minFloatBalance() == FLOOR


def test_can_fill_reflects_the_floor(flf, charlie):
    assert flf.canFill(10 * EIGHTEEN_DECIMALS)
    flf.raiseFloatFloor(FLOAT, sender=charlie)
    assert not flf.canFill(10 * EIGHTEEN_DECIMALS)


# ---------- M-8: order staleness and burned signers ----------


def test_order_priced_arbitrarily_long_ago_is_refused(flf, solver, bob):
    """An unbounded deadline admits an order whose pricing no longer corresponds
    to anything. This is the contract's own stated threat model -- a buggy solver
    overpaying against a real deposit -- not the key-compromise one."""
    with boa.reverts("deadline too far"):
        _fill(flf, solver, _order(bob, 1 * EIGHTEEN_DECIMALS, deadline=boa.env.timestamp + 100 * 365 * 24 * 3600))

    # and one signed inside the horizon does not survive past it
    order = _order(bob, 1 * EIGHTEEN_DECIMALS, deadline=boa.env.timestamp + 14 * 60)
    boa.env.time_travel(seconds=15 * 60)
    with boa.reverts("order expired"):
        _fill(flf, solver, order)


def test_burned_signer_cannot_be_reinstated_so_the_backlog_is_dead(flf, solver, bob, alice, charlie):
    """Rotating back to a burned address serves a full timelock and carries a
    current epoch, so without this the whole pre-signed backlog revives."""
    flf.setGuardian(alice, True, sender=charlie)
    order = _order(bob, MAX_FILL, deadline=boa.env.timestamp + 10 * 60)
    sig = _sign(flf, solver, order)

    flf.clearSolverSigner(sender=alice)
    assert flf.isBurnedSigner(solver.address)

    with boa.reverts("signer burned"):
        flf.initiateChange(1, solver.address, 0, sender=charlie)

    # a genuinely new key is still fine, and cannot verify the old signature
    fresh = Account.create()
    aid = flf.initiateChange(1, fresh.address, 0, sender=charlie)
    boa.env.time_travel(blocks=11)
    flf.confirmChange(aid, sender=charlie)
    with boa.reverts("not solver"):
        flf.fill(order, sig, sender=solver.address)
