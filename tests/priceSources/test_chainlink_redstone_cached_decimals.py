"""Regression coverage for proposal/confirmation feed-decimals snapshots.

ChainlinkPrices and RedStone intentionally read ``decimals()`` while a feed is
proposed and again when that proposal is confirmed. Once activated, reads use
the confirmed snapshot: admitted feed addresses are governed under the explicit
assumption that their decimals metadata does not subsequently change.
"""

import boa
import pytest

from config.BluePrint import ADDYS, PARAMS
from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS


ONE_DAY_IN_SECS = 60 * 60 * 24
SOURCE_KINDS = ("chainlink", "redstone")

REVERT = 1
EMPTY = 2
SHORT = 3
OVERSIZED = 4
OUT_OF_UINT8_RANGE = 5


RAW_METADATA_FEED = """
# @version 0.4.3

struct ChainlinkRound:
    roundId: uint80
    answer: int256
    startedAt: uint256
    updatedAt: uint256
    answeredInRound: uint80

_decimals: uint256
responseMode: public(uint256)
mockData: public(ChainlinkRound)

@deploy
def __init__(_decimalsValue: uint256):
    self._decimals = _decimalsValue

@external
def setDecimals(_decimalsValue: uint256):
    self._decimals = _decimalsValue

@external
def setResponseMode(_mode: uint256):
    self.responseMode = _mode

@external
def setMockData(
    _answer: int256,
    _roundId: uint80 = 1,
    _answeredInRound: uint80 = 1,
    _startedAt: uint256 = block.timestamp,
    _updatedAt: uint256 = block.timestamp,
):
    self.mockData = ChainlinkRound(
        roundId=_roundId,
        answer=_answer,
        startedAt=_startedAt,
        updatedAt=_updatedAt,
        answeredInRound=_answeredInRound,
    )

@view
@external
def latestRoundData() -> ChainlinkRound:
    return self.mockData

@view
@external
@raw_return
def decimals() -> Bytes[33]:
    mode: uint256 = self.responseMode
    if mode == 1:
        raise "decimals revert"
    if mode == 2:
        return b""
    if mode == 3:
        return slice(convert(self._decimals, bytes32), 0, 31)
    if mode == 4:
        return concat(convert(self._decimals, bytes32), b"x")
    if mode == 5:
        return slice(convert(max_value(uint256), bytes32), 0, 32)
    return slice(convert(self._decimals, bytes32), 0, 32)

@view
@external
def configuredDecimals() -> uint256:
    return self._decimals
"""


REVERTING_ROUND_FEED = """
# @version 0.4.3

@view
@external
def latestRoundData() -> (uint80, int256, uint256, uint256, uint80):
    raise "round revert"
"""


def _desk_params(fork):
    return (
        PARAMS[fork]["PRICE_DESK_MIN_REG_TIMELOCK"],
        PARAMS[fork]["PRICE_DESK_MAX_REG_TIMELOCK"],
    )


def _load_source(kind, ripe_hq, fork, *, eth_feed=ZERO_ADDRESS):
    min_tl, max_tl = _desk_params(fork)
    if kind == "chainlink":
        return boa.load(
            "contracts/priceSources/ChainlinkPrices.vy",
            ripe_hq,
            ZERO_ADDRESS,
            min_tl,
            max_tl,
            ADDYS[fork]["WETH"],
            ADDYS[fork]["ETH"],
            ADDYS[fork]["BTC"],
            eth_feed,
            ZERO_ADDRESS,
            ONE_DAY_IN_SECS,
            name="chainlink_confirmation_decimals",
        )
    return boa.load(
        "contracts/priceSources/RedStone.vy",
        ripe_hq,
        ZERO_ADDRESS,
        ADDYS[fork]["ETH"],
        min_tl,
        max_tl,
        name="redstone_confirmation_decimals",
    )


def _feed(decimals=8, answer=None):
    feed = boa.loads(RAW_METADATA_FEED, decimals, name="raw_metadata_feed")
    _fresh_round(feed, 10**decimals if answer is None else answer)
    return feed


def _fresh_round(feed, answer, round_id=1, answered_in_round=1, updated_at=None):
    ts = boa.env.timestamp if updated_at is None else updated_at
    feed.setMockData(answer, round_id, answered_in_round, ts, ts)


def _set_up_source(kind, ripe_hq, fork, governance):
    source = _load_source(kind, ripe_hq, fork)
    assert source.setActionTimeLockAfterSetup(sender=governance.address)
    return source


def _propose_new(source, asset, feed, governance):
    assert source.addNewPriceFeed(asset, feed, sender=governance.address)
    return source.pendingUpdates(asset).actionId


def _propose_update(source, asset, feed, governance):
    assert source.updatePriceFeed(asset, feed, sender=governance.address)
    return source.pendingUpdates(asset).actionId


def _advance(source):
    boa.env.time_travel(blocks=source.actionTimeLock() + 1)


def _refresh_round(feed):
    current = feed.mockData()
    _fresh_round(feed, current.answer, current.roundId, current.answeredInRound)


def _activate_initial(source, asset, feed, governance):
    action_id = _propose_new(source, asset, feed, governance)
    _advance(source)
    _refresh_round(feed)
    assert source.confirmNewPriceFeed(asset, sender=governance.address)
    assert not source.hasPendingAction(action_id)
    return source.feedConfig(asset)


@pytest.mark.parametrize("kind", SOURCE_KINDS)
def test_matching_decimals_activate_new_and_updated_feeds(
    kind,
    ripe_hq,
    governance,
    fork,
    charlie_token,
):
    source = _set_up_source(kind, ripe_hq, fork, governance)
    original = _feed(8)

    _activate_initial(source, charlie_token, original, governance)
    assert source.feedConfig(charlie_token).feed == original.address
    assert source.feedConfig(charlie_token).decimals == 8
    assert source.getPrice(charlie_token) == EIGHTEEN_DECIMALS

    replacement = _feed(6)
    action_id = _propose_update(source, charlie_token, replacement, governance)
    assert source.pendingUpdates(charlie_token).config.decimals == 6
    _advance(source)
    _fresh_round(replacement, 10**6)
    assert source.confirmPriceFeedUpdate(charlie_token, sender=governance.address)
    assert not source.hasPendingAction(action_id)
    assert source.pendingUpdates(charlie_token).actionId == 0
    assert source.feedConfig(charlie_token).feed == replacement.address
    assert source.feedConfig(charlie_token).decimals == 6
    assert source.getPrice(charlie_token) == EIGHTEEN_DECIMALS


@pytest.mark.parametrize("kind", SOURCE_KINDS)
def test_new_feed_decimals_mismatch_cancels_action_and_writes_no_state(
    kind,
    ripe_hq,
    governance,
    fork,
    charlie_token,
):
    source = _set_up_source(kind, ripe_hq, fork, governance)
    feed = _feed(8)
    action_id = _propose_new(source, charlie_token, feed, governance)
    assert source.pendingUpdates(charlie_token).config.decimals == 8

    feed.setDecimals(6)
    _advance(source)
    _fresh_round(feed, 10**6)
    assert not source.confirmNewPriceFeed(charlie_token, sender=governance.address)

    assert not source.hasPendingAction(action_id)
    assert not source.hasPendingPriceFeedUpdate(charlie_token)
    assert source.pendingUpdates(charlie_token).actionId == 0
    assert source.feedConfig(charlie_token).feed == ZERO_ADDRESS
    assert source.indexOfAsset(charlie_token) == 0
    assert not source.hasPriceFeed(charlie_token)
    assert source.getPriceAndHasFeed(charlie_token) == (0, False)


@pytest.mark.parametrize("kind", SOURCE_KINDS)
def test_update_decimals_mismatch_cancels_and_preserves_active_config(
    kind,
    ripe_hq,
    governance,
    fork,
    charlie_token,
):
    source = _set_up_source(kind, ripe_hq, fork, governance)
    original = _feed(8)
    previous = _activate_initial(source, charlie_token, original, governance)
    previous_index = source.indexOfAsset(charlie_token)

    replacement = _feed(8, 2 * 10**8)
    action_id = _propose_update(source, charlie_token, replacement, governance)
    replacement.setDecimals(6)
    _advance(source)
    _fresh_round(replacement, 2 * 10**6)
    assert not source.confirmPriceFeedUpdate(
        charlie_token, sender=governance.address
    )

    assert not source.hasPendingAction(action_id)
    assert source.pendingUpdates(charlie_token).actionId == 0
    assert source.feedConfig(charlie_token) == previous
    assert source.indexOfAsset(charlie_token) == previous_index
    _refresh_round(original)
    assert source.getPrice(charlie_token) == EIGHTEEN_DECIMALS


@pytest.mark.parametrize("kind", SOURCE_KINDS)
def test_transient_decimals_drift_restored_before_confirmation_is_accepted(
    kind,
    ripe_hq,
    governance,
    fork,
    charlie_token,
):
    source = _set_up_source(kind, ripe_hq, fork, governance)
    feed = _feed(8)
    action_id = _propose_new(source, charlie_token, feed, governance)

    # Confirmation-only checking intentionally has no continuous-monitoring
    # requirement: the metadata must match at proposal and confirmation.
    feed.setDecimals(6)
    feed.setDecimals(8)
    _advance(source)
    _fresh_round(feed, 10**8)
    assert source.confirmNewPriceFeed(charlie_token, sender=governance.address)
    assert not source.hasPendingAction(action_id)
    assert source.feedConfig(charlie_token).decimals == 8


@pytest.mark.parametrize("kind", SOURCE_KINDS)
@pytest.mark.parametrize(
    "response_mode",
    (REVERT, EMPTY, SHORT, OVERSIZED, OUT_OF_UINT8_RANGE),
    ids=("revert", "empty", "short", "oversized", "out-of-uint8-range"),
)
def test_reverting_or_malformed_decimals_is_rejected_at_proposal_without_state(
    kind,
    response_mode,
    ripe_hq,
    governance,
    fork,
    charlie_token,
):
    source = _set_up_source(kind, ripe_hq, fork, governance)
    feed = _feed(8)
    feed.setResponseMode(response_mode)
    next_action_id = source.actionId()

    with boa.reverts("invalid feed"):
        source.addNewPriceFeed(charlie_token, feed, sender=governance.address)

    assert source.actionId() == next_action_id
    assert source.pendingUpdates(charlie_token).actionId == 0
    assert source.feedConfig(charlie_token).feed == ZERO_ADDRESS
    assert source.indexOfAsset(charlie_token) == 0


@pytest.mark.parametrize("kind", SOURCE_KINDS)
@pytest.mark.parametrize("operation", ("new", "update"))
@pytest.mark.parametrize(
    "response_mode",
    (REVERT, EMPTY, SHORT, OVERSIZED, OUT_OF_UINT8_RANGE),
    ids=("revert", "empty", "short", "oversized", "out-of-uint8-range"),
)
def test_reverting_or_malformed_decimals_at_confirmation_cancels_atomically(
    kind,
    operation,
    response_mode,
    ripe_hq,
    governance,
    fork,
    charlie_token,
):
    source = _set_up_source(kind, ripe_hq, fork, governance)
    previous = source.feedConfig(charlie_token)
    previous_index = 0
    if operation == "update":
        previous = _activate_initial(
            source, charlie_token, _feed(8), governance
        )
        previous_index = source.indexOfAsset(charlie_token)

    candidate = _feed(8, 2 * 10**8)
    if operation == "new":
        action_id = _propose_new(source, charlie_token, candidate, governance)
    else:
        action_id = _propose_update(source, charlie_token, candidate, governance)

    candidate.setResponseMode(response_mode)
    _advance(source)
    _fresh_round(candidate, 2 * 10**8)
    if operation == "new":
        assert not source.confirmNewPriceFeed(
            charlie_token, sender=governance.address
        )
    else:
        assert not source.confirmPriceFeedUpdate(
            charlie_token, sender=governance.address
        )

    assert not source.hasPendingAction(action_id)
    assert source.pendingUpdates(charlie_token).actionId == 0
    assert source.feedConfig(charlie_token) == previous
    assert source.indexOfAsset(charlie_token) == previous_index


@pytest.mark.parametrize("kind", SOURCE_KINDS)
def test_latest_proposal_snapshot_replaces_prior_candidate(
    kind,
    ripe_hq,
    governance,
    fork,
    charlie_token,
):
    source = _set_up_source(kind, ripe_hq, fork, governance)
    first = _feed(8)
    second = _feed(6)

    first_action = _propose_new(source, charlie_token, first, governance)
    second_action = _propose_new(source, charlie_token, second, governance)
    assert second_action != first_action
    assert source.hasPendingAction(first_action)
    assert source.hasPendingAction(second_action)
    pending = source.pendingUpdates(charlie_token)
    assert pending.actionId == second_action
    assert pending.config.feed == second.address
    assert pending.config.decimals == 6

    # Only the latest proposal is validated and activated.
    first.setResponseMode(REVERT)
    _advance(source)
    _fresh_round(second, 10**6)
    assert source.confirmNewPriceFeed(charlie_token, sender=governance.address)
    assert source.feedConfig(charlie_token).feed == second.address
    assert source.feedConfig(charlie_token).decimals == 6
    assert source.getPrice(charlie_token) == EIGHTEEN_DECIMALS
    assert not source.hasPendingAction(second_action)
    # Replacing a proposal does not cancel its TimeLock record. It remains
    # confirmable in isolation but is inert because pendingUpdates references
    # only the latest proposal and is cleared when that proposal activates.
    assert source.hasPendingAction(first_action)
    assert source.canConfirmAction(first_action)
    assert source.pendingUpdates(charlie_token).actionId == 0
    with boa.reverts("no pending new feed"):
        source.confirmNewPriceFeed(charlie_token, sender=governance.address)


@pytest.mark.parametrize("kind", SOURCE_KINDS)
def test_latest_update_snapshot_replaces_prior_candidate(
    kind,
    ripe_hq,
    governance,
    fork,
    charlie_token,
):
    source = _set_up_source(kind, ripe_hq, fork, governance)
    _activate_initial(source, charlie_token, _feed(8), governance)
    first = _feed(8, 2 * 10**8)
    second = _feed(6, 3 * 10**6)

    first_action = _propose_update(source, charlie_token, first, governance)
    second_action = _propose_update(source, charlie_token, second, governance)
    assert second_action != first_action
    assert source.hasPendingAction(first_action)
    assert source.hasPendingAction(second_action)
    pending = source.pendingUpdates(charlie_token)
    assert pending.actionId == second_action
    assert pending.config.feed == second.address
    assert pending.config.decimals == 6

    first.setResponseMode(REVERT)
    _advance(source)
    _fresh_round(second, 3 * 10**6)
    assert source.confirmPriceFeedUpdate(charlie_token, sender=governance.address)
    assert source.feedConfig(charlie_token).feed == second.address
    assert source.feedConfig(charlie_token).decimals == 6
    assert source.getPrice(charlie_token) == 3 * EIGHTEEN_DECIMALS
    assert not source.hasPendingAction(second_action)
    assert source.hasPendingAction(first_action)
    assert source.canConfirmAction(first_action)
    assert source.pendingUpdates(charlie_token).actionId == 0
    with boa.reverts("no pending update feed"):
        source.confirmPriceFeedUpdate(charlie_token, sender=governance.address)


@pytest.mark.parametrize("kind", SOURCE_KINDS)
def test_active_reads_ignore_valid_live_decimals_change_after_confirmation(
    kind,
    ripe_hq,
    governance,
    fork,
    charlie_token,
):
    source = _set_up_source(kind, ripe_hq, fork, governance)
    feed = _feed(8)
    _activate_initial(source, charlie_token, feed, governance)

    # decimals() still returns a canonical 32-byte word, but active reads do
    # not invoke it. Keeping the 1e8 answer distinguishes cached-8 pricing
    # (1e18) from an incorrect live-6 normalization (100e18).
    feed.setDecimals(6)
    assert feed.responseMode() == 0
    assert feed.configuredDecimals() == 6
    _fresh_round(feed, 10**8)

    assert source.feedConfig(charlie_token).decimals == 8
    assert source.getPrice(charlie_token) == EIGHTEEN_DECIMALS
    assert source.getPriceAndHasFeed(charlie_token) == (
        EIGHTEEN_DECIMALS,
        True,
    )


@pytest.mark.parametrize("kind", SOURCE_KINDS)
@pytest.mark.parametrize(
    "post_confirmation_mode",
    (REVERT, SHORT, OVERSIZED),
    ids=("revert", "short", "oversized"),
)
def test_active_reads_trust_confirmed_snapshot_and_do_not_recheck_decimals(
    kind,
    post_confirmation_mode,
    ripe_hq,
    governance,
    fork,
    charlie_token,
):
    source = _set_up_source(kind, ripe_hq, fork, governance)
    feed = _feed(8)
    _activate_initial(source, charlie_token, feed, governance)

    feed.setDecimals(6)
    feed.setResponseMode(post_confirmation_mode)
    _fresh_round(feed, 10**8)

    # The cached 8-decimal snapshot is the explicit post-confirmation policy.
    assert source.feedConfig(charlie_token).decimals == 8
    assert source.getPrice(charlie_token) == EIGHTEEN_DECIMALS
    assert source.getPriceAndHasFeed(charlie_token) == (
        EIGHTEEN_DECIMALS,
        True,
    )


@pytest.mark.parametrize("kind", SOURCE_KINDS)
def test_cached_decimals_preserve_round_and_staleness_validation(
    kind,
    ripe_hq,
    governance,
    fork,
    charlie_token,
):
    source = _set_up_source(kind, ripe_hq, fork, governance)
    feed = _feed(8)
    _activate_initial(source, charlie_token, feed, governance)
    feed.setResponseMode(REVERT)

    _fresh_round(feed, 10**8, round_id=0, answered_in_round=0)
    assert source.getPrice(charlie_token) == 0

    _fresh_round(feed, 10**8, round_id=2, answered_in_round=1)
    assert source.getPrice(charlie_token) == 0

    _fresh_round(feed, 10**8)
    boa.env.time_travel(seconds=ONE_DAY_IN_SECS + 1)
    assert source.getPrice(charlie_token) == 0

    future = boa.env.timestamp + 100
    feed.setMockData(10**8, 1, 1, future, future)
    assert source.getPrice(charlie_token) == 0

    _fresh_round(feed, 0)
    assert source.getPrice(charlie_token) == 0

    _fresh_round(feed, -1)
    assert source.getPrice(charlie_token) == 0

    _fresh_round(feed, 10**8)
    assert source.getPrice(charlie_token) == EIGHTEEN_DECIMALS


@pytest.mark.parametrize("response_mode", (REVERT, SHORT, OVERSIZED))
def test_chainlink_constructor_rejects_unreadable_default_feed_metadata(
    response_mode,
    ripe_hq,
    fork,
):
    feed = _feed(8)
    feed.setResponseMode(response_mode)
    with boa.reverts("invalid feed"):
        _load_source("chainlink", ripe_hq, fork, eth_feed=feed.address)


def test_chainlink_constructor_caches_matching_default_feed_decimals(
    ripe_hq,
    fork,
):
    feed = _feed(8)
    source = _load_source("chainlink", ripe_hq, fork, eth_feed=feed.address)
    assert source.feedConfig(source.ETH()).feed == feed.address
    assert source.feedConfig(source.ETH()).decimals == 8
    assert source.feedConfig(source.WETH()).feed == feed.address
    assert source.feedConfig(source.WETH()).decimals == 8


@pytest.mark.parametrize("kind", SOURCE_KINDS)
def test_invalid_explicit_decimals_short_circuits_round_call(kind, ripe_hq, fork):
    source = _load_source(kind, ripe_hq, fork)
    reverting_round = boa.loads(REVERTING_ROUND_FEED, name="reverting_round_feed")
    if kind == "chainlink":
        assert source.getChainlinkData(reverting_round, 19) == 0
    else:
        assert source.getRedStoneData(reverting_round, 19) == 0
