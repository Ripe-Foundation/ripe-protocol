import boa
import pytest

from constants import EIGHTEEN_DECIMALS


@pytest.fixture(scope="module")
def addStorkFeed(stork_prices, governance):
    def addStorkFeed(_asset, _feed_id, _stale_time=0):
        if stork_prices.hasPriceFeed(_asset):
            return
        assert stork_prices.addNewPriceFeed(_asset, _feed_id, _stale_time, sender=governance.address)
        boa.env.time_travel(blocks=stork_prices.actionTimeLock() + 1)
        assert stork_prices.confirmNewPriceFeed(_asset, sender=governance.address)
    yield addStorkFeed


def _feed_id(n=1):
    return bytes.fromhex(f"{n:064x}")


def _write_feed(mock_stork, feed_id, price, publish_time):
    payload = mock_stork.createPriceFeedUpdateData(feed_id, price, publish_time)
    boa.env.set_balance(boa.env.eoa, EIGHTEEN_DECIMALS)
    mock_stork.updateTemporalNumericValuesV1([payload], value=1)


def test_stork_rejects_negative_int192(
    stork_prices,
    mock_stork,
    alpha_token,
    addStorkFeed,
):
    feed_id = bytes.fromhex("7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c")
    addStorkFeed(alpha_token, feed_id)
    assert stork_prices.getPrice(alpha_token) != 0
    _write_feed(mock_stork, feed_id, -1, boa.env.evm.patch.timestamp)
    assert mock_stork.priceFeeds(feed_id).quantizedValue == -1
    assert stork_prices.getPrice(alpha_token) == 0
    assert stork_prices.getPriceAndHasFeed(alpha_token) == (0, True)


def test_stork_official_1e18_as_is(
    stork_prices,
    mock_stork,
    alpha_token,
    addStorkFeed,
):
    feed_id = bytes.fromhex("7416a56f222e196d0487dce8a1a8003936862e7a15092a91898d69fa8bce290c")
    addStorkFeed(alpha_token, feed_id)
    _write_feed(mock_stork, feed_id, EIGHTEEN_DECIMALS, boa.env.evm.patch.timestamp)
    assert stork_prices.getPrice(alpha_token) == EIGHTEEN_DECIMALS


def test_stork_admission_rejects_zero_future_and_stale(
    stork_prices,
    mock_stork,
    alpha_token,
    bravo_token,
    charlie_token,
    governance,
):
    now = boa.env.evm.patch.timestamp
    zero_id = _feed_id(2)
    future_id = _feed_id(3)
    stale_id = _feed_id(4)

    _write_feed(mock_stork, zero_id, 0, now)
    with boa.reverts("invalid feed"):
        stork_prices.addNewPriceFeed(alpha_token, zero_id, 3600, sender=governance.address)

    _write_feed(mock_stork, future_id, EIGHTEEN_DECIMALS, now + 3600)
    with boa.reverts("invalid feed"):
        stork_prices.addNewPriceFeed(bravo_token, future_id, 3600, sender=governance.address)

    _write_feed(mock_stork, stale_id, EIGHTEEN_DECIMALS, now - 10_000)
    with boa.reverts("invalid feed"):
        stork_prices.addNewPriceFeed(charlie_token, stale_id, 3600, sender=governance.address)


def test_stork_failed_revalidation_cancels_pending(
    stork_prices,
    mock_stork,
    alpha_token,
    governance,
):
    feed_id = _feed_id(5)
    _write_feed(mock_stork, feed_id, EIGHTEEN_DECIMALS, boa.env.evm.patch.timestamp)
    assert stork_prices.addNewPriceFeed(alpha_token, feed_id, 3600, sender=governance.address)
    boa.env.time_travel(blocks=stork_prices.actionTimeLock() + 1)
    _write_feed(mock_stork, feed_id, -1, boa.env.evm.patch.timestamp)
    assert not stork_prices.confirmNewPriceFeed(alpha_token, sender=governance.address)
    assert not stork_prices.hasPriceFeed(alpha_token)
    assert not stork_prices.hasPendingPriceFeedUpdate(alpha_token)


def test_stork_admission_resolves_global_and_feed_stale_bounds(
    stork_prices,
    mock_stork,
    alpha_token,
    bravo_token,
    charlie_token,
    governance,
    setGeneralConfig,
):
    with boa.env.anchor():
        now = boa.env.evm.patch.timestamp
        global_tight = _feed_id(20)
        feed_tight = _feed_id(21)
        both_ok = _feed_id(22)

        _write_feed(mock_stork, global_tight, EIGHTEEN_DECIMALS, now - 50)
        setGeneralConfig(_priceStaleTime=10)
        with boa.reverts("invalid feed"):
            stork_prices.addNewPriceFeed(alpha_token, global_tight, 1000, sender=governance.address)

        _write_feed(mock_stork, feed_tight, EIGHTEEN_DECIMALS, now - 50)
        setGeneralConfig(_priceStaleTime=1000)
        with boa.reverts("invalid feed"):
            stork_prices.addNewPriceFeed(bravo_token, feed_tight, 10, sender=governance.address)

        _write_feed(mock_stork, both_ok, EIGHTEEN_DECIMALS, now - 50)
        setGeneralConfig(_priceStaleTime=1000)
        assert stork_prices.addNewPriceFeed(charlie_token, both_ok, 1000, sender=governance.address)
        boa.env.time_travel(blocks=stork_prices.actionTimeLock() + 1)
        _write_feed(mock_stork, both_ok, EIGHTEEN_DECIMALS, boa.env.evm.patch.timestamp - 50)
        assert stork_prices.confirmNewPriceFeed(charlie_token, sender=governance.address)
        assert stork_prices.hasPriceFeed(charlie_token)


def test_stork_update_confirm_cancels_when_revalidation_fails(
    stork_prices,
    mock_stork,
    alpha_token,
    governance,
    setGeneralConfig,
):
    with boa.env.anchor():
        setGeneralConfig(_priceStaleTime=0)
        old_id = _feed_id(30)
        new_id = _feed_id(31)
        _write_feed(mock_stork, old_id, EIGHTEEN_DECIMALS, boa.env.evm.patch.timestamp)
        assert stork_prices.addNewPriceFeed(alpha_token, old_id, 3600, sender=governance.address)
        boa.env.time_travel(blocks=stork_prices.actionTimeLock() + 1)
        _write_feed(mock_stork, old_id, EIGHTEEN_DECIMALS, boa.env.evm.patch.timestamp)
        assert stork_prices.confirmNewPriceFeed(alpha_token, sender=governance.address)

        _write_feed(mock_stork, new_id, EIGHTEEN_DECIMALS, boa.env.evm.patch.timestamp)
        assert stork_prices.updatePriceFeed(alpha_token, new_id, 3600, sender=governance.address)
        boa.env.time_travel(blocks=stork_prices.actionTimeLock() + 1)
        _write_feed(mock_stork, new_id, -1, boa.env.evm.patch.timestamp)
        assert not stork_prices.confirmPriceFeedUpdate(alpha_token, sender=governance.address)
        assert stork_prices.feedConfig(alpha_token).feedId == old_id
        assert not stork_prices.hasPendingPriceFeedUpdate(alpha_token)


def test_stork_update_confirm_cancels_when_globally_stale(
    stork_prices,
    mock_stork,
    alpha_token,
    governance,
    setGeneralConfig,
):
    with boa.env.anchor():
        setGeneralConfig(_priceStaleTime=0)
        old_id = _feed_id(32)
        new_id = _feed_id(33)
        _write_feed(mock_stork, old_id, EIGHTEEN_DECIMALS, boa.env.evm.patch.timestamp)
        assert stork_prices.addNewPriceFeed(alpha_token, old_id, 1000, sender=governance.address)
        boa.env.time_travel(blocks=stork_prices.actionTimeLock() + 1)
        _write_feed(mock_stork, old_id, EIGHTEEN_DECIMALS, boa.env.evm.patch.timestamp)
        assert stork_prices.confirmNewPriceFeed(alpha_token, sender=governance.address)

        _write_feed(mock_stork, new_id, EIGHTEEN_DECIMALS, boa.env.evm.patch.timestamp)
        assert stork_prices.updatePriceFeed(alpha_token, new_id, 1000, sender=governance.address)
        boa.env.time_travel(blocks=stork_prices.actionTimeLock() + 1)
        setGeneralConfig(_priceStaleTime=10)
        _write_feed(mock_stork, new_id, EIGHTEEN_DECIMALS, boa.env.evm.patch.timestamp - 50)
        assert not stork_prices.confirmPriceFeedUpdate(alpha_token, sender=governance.address)
        assert stork_prices.feedConfig(alpha_token).feedId == old_id
