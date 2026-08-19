import boa

from constants import EIGHTEEN_DECIMALS


MUTABLE_VAULT = """
# @version 0.4.3

_asset: address
_decimals: public(uint8)
should_revert_asset: public(bool)
should_revert_decimals: public(bool)
should_oog_asset: public(bool)
should_oog_decimals: public(bool)
dirty_asset: public(bool)
dirty_decimals: public(bool)
share_price: public(uint256)

@deploy
def __init__(_asset: address):
    self._asset = _asset
    self._decimals = 18
    self.share_price = 10 ** 18

@external
def setAsset(_asset: address):
    self._asset = _asset

@external
def setDecimals(_decimals: uint8):
    self._decimals = _decimals

@external
def setShouldRevertAsset(_v: bool):
    self.should_revert_asset = _v

@external
def setShouldRevertDecimals(_v: bool):
    self.should_revert_decimals = _v

@external
def setShouldOogAsset(_v: bool):
    self.should_oog_asset = _v

@external
def setShouldOogDecimals(_v: bool):
    self.should_oog_decimals = _v

@external
def setDirtyAsset(_v: bool):
    self.dirty_asset = _v

@external
def setDirtyDecimals(_v: bool):
    self.dirty_decimals = _v

@external
def setSharePrice(_price: uint256):
    self.share_price = _price

@view
@external
def asset() -> uint256:
    if self.should_revert_asset:
        raise "asset revert"
    if self.should_oog_asset:
        s: uint256 = 0
        for i: uint256 in range(10_000):
            s += i
        return convert(self._asset, uint256)
    if self.dirty_asset:
        return max_value(uint256)
    return convert(self._asset, uint256)

@view
@external
def decimals() -> uint256:
    if self.should_revert_decimals:
        raise "decimals revert"
    if self.should_oog_decimals:
        s: uint256 = 0
        for i: uint256 in range(10_000):
            s += i
        return convert(self._decimals, uint256)
    if self.dirty_decimals:
        return max_value(uint256)
    return convert(self._decimals, uint256)

@view
@external
def convertToAssets(_shares: uint256) -> uint256:
    return self.share_price * _shares // (10 ** 18)

@view
@external
def totalSupply() -> uint256:
    return 10 ** 18
"""

MUTABLE_UNDERLYING = """
# @version 0.4.3

_decimals: public(uint8)
should_revert: public(bool)
oog: public(bool)

@deploy
def __init__():
    self._decimals = 18

@external
def setDecimals(_decimals: uint8):
    self._decimals = _decimals

@external
def setShouldRevert(_v: bool):
    self.should_revert = _v

@external
def setOog(_v: bool):
    self.oog = _v

@view
@external
def decimals() -> uint256:
    if self.should_revert:
        raise "decimals revert"
    if self.oog:
        s: uint256 = 0
        for i: uint256 in range(10_000):
            s += i
        return convert(self._decimals, uint256)
    return convert(self._decimals, uint256)
"""

RET_31_CODE = bytes.fromhex("601f6000f3")
RET_33_CODE = bytes.fromhex("60216000f3")

SWITCHABLE_VAULT_DECIMALS = """
# @version 0.4.3

_asset: address
_decimals: public(uint256)
decimals_len: public(uint256)
dirty: public(bool)

@deploy
def __init__(_asset: address):
    self._asset = _asset
    self._decimals = 18
    self.decimals_len = 32

@external
def setDecimalsLen(_n: uint256):
    self.decimals_len = _n

@external
def setDirty(_v: bool):
    self.dirty = _v

@view
@external
def asset() -> address:
    return self._asset

@raw_return
@view
@external
def decimals() -> Bytes[33]:
    word: bytes32 = convert(self._decimals, bytes32)
    if self.dirty:
        word = convert(max_value(uint256), bytes32)
    if self.decimals_len == 31:
        return slice(word, 0, 31)
    if self.decimals_len == 33:
        return concat(word, b"x")
    return slice(word, 0, 32)

@view
@external
def convertToAssets(_shares: uint256) -> uint256:
    return _shares

@view
@external
def totalSupply() -> uint256:
    return 10 ** 18
"""


def _register(undy, governance, vault, stale=0):
    assert undy.addNewPriceFeed(vault, 0, 10, 0, stale, sender=governance.address)
    boa.env.time_travel(blocks=undy.actionTimeLock() + 1)
    assert undy.confirmNewPriceFeed(vault, sender=governance.address)


def test_undy_update_does_not_rebind_asset(
    ripe_hq,
    governance,
    switchboard_alpha,
    mission_control,
    mock_undy_v2,
    mock_price_source,
    alpha_token,
    bravo_token,
    undy_vault_prices,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 100 * EIGHTEEN_DECIMALS)

    vault = boa.loads(MUTABLE_VAULT, alpha_token.address)
    _register(undy_vault_prices, governance, vault)
    assert undy_vault_prices.priceConfigs(vault).underlyingAsset == alpha_token.address
    assert undy_vault_prices.getPrice(vault) == EIGHTEEN_DECIMALS
    assert undy_vault_prices.hasPriceFeed(vault) is True

    vault.setAsset(bravo_token.address)
    assert vault.asset() == int(bravo_token.address, 16)
    assert undy_vault_prices.priceConfigs(vault).underlyingAsset == alpha_token.address
    assert undy_vault_prices.getPrice(vault) == 0
    assert undy_vault_prices.getPriceAndHasFeed(vault) == (0, True)
    assert undy_vault_prices.hasPriceFeed(vault) is True
    with boa.reverts("invalid config"):
        undy_vault_prices.updatePriceConfig(vault, 0, 10, 0, 0, sender=governance.address)

    vault.setAsset(alpha_token.address)
    assert undy_vault_prices.updatePriceConfig(vault, 0, 10, 0, 0, sender=governance.address)
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    assert undy_vault_prices.confirmPriceFeedUpdate(vault, sender=governance.address)
    assert undy_vault_prices.priceConfigs(vault).underlyingAsset == alpha_token.address
    vault.setAsset(bravo_token.address)
    assert undy_vault_prices.getPrice(vault) == 0
    assert undy_vault_prices.getPrice(vault) != 100 * EIGHTEEN_DECIMALS


def test_undy_live_decimals_mismatch_and_timelock_identity(
    governance,
    switchboard_alpha,
    mission_control,
    mock_undy_v2,
    mock_price_source,
    alpha_token,
    undy_vault_prices,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    vault = boa.loads(MUTABLE_VAULT, alpha_token.address)
    assert undy_vault_prices.addNewPriceFeed(vault, 0, 10, 0, 0, sender=governance.address)
    vault.setDecimals(6)
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    assert not undy_vault_prices.confirmNewPriceFeed(vault, sender=governance.address)
    assert not undy_vault_prices.hasPriceFeed(vault)
    assert not undy_vault_prices.hasPendingPriceFeedUpdate(vault)

    vault.setDecimals(18)
    _register(undy_vault_prices, governance, vault)
    assert undy_vault_prices.getPrice(vault) == EIGHTEEN_DECIMALS
    vault.setDecimals(8)
    assert undy_vault_prices.getPriceAndHasFeed(vault) == (0, True)


def test_undy_underlying_decimals_mismatch(
    governance,
    switchboard_alpha,
    mission_control,
    mock_undy_v2,
    mock_price_source,
    undy_vault_prices,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    underlying = boa.loads(MUTABLE_UNDERLYING)
    mock_price_source.setPrice(underlying, EIGHTEEN_DECIMALS)
    vault = boa.loads(MUTABLE_VAULT, underlying.address)
    _register(undy_vault_prices, governance, vault)
    assert undy_vault_prices.getPrice(vault) == EIGHTEEN_DECIMALS
    underlying.setDecimals(6)
    assert undy_vault_prices.getPriceAndHasFeed(vault) == (0, True)
    assert undy_vault_prices.hasPriceFeed(vault) is True


def test_undy_asset_and_decimals_call_failures(
    governance,
    switchboard_alpha,
    mission_control,
    mock_undy_v2,
    mock_price_source,
    alpha_token,
    undy_vault_prices,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    vault = boa.loads(MUTABLE_VAULT, alpha_token.address)
    _register(undy_vault_prices, governance, vault)

    vault.setShouldRevertAsset(True)
    assert undy_vault_prices.getPriceAndHasFeed(vault) == (0, True)

    vault.setShouldRevertAsset(False)
    vault.setShouldRevertDecimals(True)
    assert undy_vault_prices.getPriceAndHasFeed(vault) == (0, True)


def test_undy_disable_readd_seeds_fresh_snapshot(
    governance,
    switchboard_alpha,
    mission_control,
    mock_undy_v2,
    mock_price_source,
    alpha_token,
    bravo_token,
    undy_vault_prices,
    teller,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, 100 * EIGHTEEN_DECIMALS)
    vault = boa.loads(MUTABLE_VAULT, alpha_token.address)
    _register(undy_vault_prices, governance, vault)
    first_snap = undy_vault_prices.priceConfigs(vault).lastSnapshot
    assert first_snap.pricePerShare != 0
    boa.env.time_travel(seconds=1)
    assert undy_vault_prices.addPriceSnapshot(vault, sender=teller.address)
    boa.env.time_travel(seconds=1)
    assert undy_vault_prices.addPriceSnapshot(vault, sender=teller.address)
    old_one = undy_vault_prices.snapShots(vault, 1)
    old_two = undy_vault_prices.snapShots(vault, 2)
    assert old_one.pricePerShare != 0
    assert old_two.pricePerShare != 0

    assert undy_vault_prices.disablePriceFeed(vault, sender=governance.address)
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    assert undy_vault_prices.confirmDisablePriceFeed(vault, sender=governance.address)
    assert undy_vault_prices.hasPriceFeed(vault) is False

    vault.setAsset(bravo_token.address)
    _register(undy_vault_prices, governance, vault)
    cfg = undy_vault_prices.priceConfigs(vault)
    assert cfg.underlyingAsset == bravo_token.address
    assert cfg.lastSnapshot.lastUpdate != first_snap.lastUpdate or cfg.lastSnapshot.pricePerShare != first_snap.pricePerShare
    assert cfg.nextIndex == 1
    assert undy_vault_prices.snapShots(vault, 1).pricePerShare == 0
    assert undy_vault_prices.snapShots(vault, 2).pricePerShare == 0
    assert undy_vault_prices.getPrice(vault) == 100 * EIGHTEEN_DECIMALS


def test_undy_identity_failures_are_soft_for_each_getter(
    governance,
    switchboard_alpha,
    mission_control,
    mock_undy_v2,
    mock_price_source,
    alpha_token,
    undy_vault_prices,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    vault = boa.loads(MUTABLE_VAULT, alpha_token.address)
    _register(undy_vault_prices, governance, vault)
    assert undy_vault_prices.getPrice(vault) == EIGHTEEN_DECIMALS

    vault.setShouldRevertAsset(True)
    assert undy_vault_prices.getPrice(vault) == 0
    assert undy_vault_prices.getPriceAndHasFeed(vault) == (0, True)
    assert undy_vault_prices.hasPriceFeed(vault) is True
    vault.setShouldRevertAsset(False)

    vault.setShouldOogAsset(True)
    assert undy_vault_prices.getPrice(vault) == 0
    assert undy_vault_prices.getPriceAndHasFeed(vault) == (0, True)
    assert undy_vault_prices.hasPriceFeed(vault) is True
    vault.setShouldOogAsset(False)

    vault.setDirtyAsset(True)
    assert undy_vault_prices.getPrice(vault) == 0
    assert undy_vault_prices.getPriceAndHasFeed(vault) == (0, True)
    assert undy_vault_prices.hasPriceFeed(vault) is True
    vault.setDirtyAsset(False)
    assert undy_vault_prices.getPrice(vault) == EIGHTEEN_DECIMALS

    vault.setShouldRevertDecimals(True)
    assert undy_vault_prices.getPrice(vault) == 0
    assert undy_vault_prices.getPriceAndHasFeed(vault) == (0, True)
    vault.setShouldRevertDecimals(False)

    vault.setShouldOogDecimals(True)
    assert undy_vault_prices.getPrice(vault) == 0
    assert undy_vault_prices.getPriceAndHasFeed(vault) == (0, True)
    vault.setShouldOogDecimals(False)

    underlying = boa.loads(MUTABLE_UNDERLYING)
    mock_price_source.setPrice(underlying, EIGHTEEN_DECIMALS)
    vault_u = boa.loads(MUTABLE_VAULT, underlying.address)
    _register(undy_vault_prices, governance, vault_u)
    assert undy_vault_prices.getPrice(vault_u) == EIGHTEEN_DECIMALS
    underlying.setShouldRevert(True)
    assert undy_vault_prices.getPrice(vault_u) == 0
    assert undy_vault_prices.getPriceAndHasFeed(vault_u) == (0, True)
    underlying.setShouldRevert(False)
    underlying.setOog(True)
    assert undy_vault_prices.getPrice(vault_u) == 0
    assert undy_vault_prices.getPriceAndHasFeed(vault_u) == (0, True)
    assert undy_vault_prices.hasPriceFeed(vault_u) is True
    underlying.setOog(False)

    boa.env.set_code(underlying.address, RET_31_CODE)
    assert undy_vault_prices.getPriceAndHasFeed(vault_u) == (0, True)

    vault_mal = boa.loads(MUTABLE_VAULT, alpha_token.address)
    _register(undy_vault_prices, governance, vault_mal)
    boa.env.set_code(vault_mal.address, RET_31_CODE)
    assert undy_vault_prices.getPriceAndHasFeed(vault_mal) == (0, True)

    vault2 = boa.loads(MUTABLE_VAULT, alpha_token.address)
    _register(undy_vault_prices, governance, vault2)
    boa.env.set_code(vault2.address, RET_33_CODE)
    assert undy_vault_prices.getPriceAndHasFeed(vault2) == (0, True)

    vault.setDirtyDecimals(True)
    assert undy_vault_prices.getPriceAndHasFeed(vault) == (0, True)
    vault.setDirtyDecimals(False)
    assert undy_vault_prices.getPrice(vault) == EIGHTEEN_DECIMALS

    vault_dec = boa.loads(SWITCHABLE_VAULT_DECIMALS, alpha_token.address)
    _register(undy_vault_prices, governance, vault_dec)
    assert undy_vault_prices.getPrice(vault_dec) == EIGHTEEN_DECIMALS
    vault_dec.setDecimalsLen(31)
    assert undy_vault_prices.getPriceAndHasFeed(vault_dec) == (0, True)
    vault_dec.setDecimalsLen(32)
    assert undy_vault_prices.getPrice(vault_dec) == EIGHTEEN_DECIMALS
    vault_dec.setDecimalsLen(33)
    assert undy_vault_prices.getPriceAndHasFeed(vault_dec) == (0, True)
    vault_dec.setDecimalsLen(32)
    vault_dec.setDirty(True)
    assert undy_vault_prices.getPriceAndHasFeed(vault_dec) == (0, True)


def test_undy_confirm_cancels_rebind_and_does_not_serve_foreign_price(
    governance,
    switchboard_alpha,
    mission_control,
    mock_undy_v2,
    mock_price_source,
    alpha_token,
    bravo_token,
    undy_vault_prices,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    vault = boa.loads(MUTABLE_VAULT, alpha_token.address)
    assert undy_vault_prices.addNewPriceFeed(vault, 0, 10, 0, 0, sender=governance.address)
    vault.setSharePrice(10 ** 16)
    vault.setAsset(bravo_token.address)
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    assert not undy_vault_prices.confirmNewPriceFeed(vault, sender=governance.address)
    assert not undy_vault_prices.hasPriceFeed(vault)
    vault.setSharePrice(EIGHTEEN_DECIMALS)
    vault.setAsset(alpha_token.address)
    assert undy_vault_prices.getPrice(vault) == 0
    assert undy_vault_prices.getPriceAndHasFeed(vault) == (0, False)


def test_undy_add_snapshot_refuses_rebind_and_restore_keeps_original_price(
    governance,
    switchboard_alpha,
    mission_control,
    mock_undy_v2,
    mock_price_source,
    alpha_token,
    bravo_token,
    undy_vault_prices,
    teller,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    vault = boa.loads(MUTABLE_VAULT, alpha_token.address)
    _register(undy_vault_prices, governance, vault)
    first = undy_vault_prices.priceConfigs(vault).lastSnapshot
    assert first.pricePerShare == EIGHTEEN_DECIMALS
    vault.setSharePrice(10 ** 16)
    vault.setAsset(bravo_token.address)
    boa.env.time_travel(seconds=1)
    assert not undy_vault_prices.addPriceSnapshot(vault, sender=teller.address)
    assert undy_vault_prices.snapShots(vault, 1).pricePerShare == 0
    assert undy_vault_prices.priceConfigs(vault).lastSnapshot.pricePerShare == first.pricePerShare
    vault.setSharePrice(EIGHTEEN_DECIMALS)
    vault.setAsset(alpha_token.address)
    assert undy_vault_prices.getPrice(vault) == EIGHTEEN_DECIMALS
    assert undy_vault_prices.getPrice(vault) != 10 ** 16


def test_undy_get_latest_snapshot_empty_on_absent_or_rebind(
    governance,
    switchboard_alpha,
    mission_control,
    mock_undy_v2,
    mock_price_source,
    alpha_token,
    bravo_token,
    undy_vault_prices,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    vault = boa.loads(MUTABLE_VAULT, alpha_token.address)
    empty = undy_vault_prices.getLatestSnapshot(vault)
    assert empty.pricePerShare == 0
    assert empty.totalSupply == 0
    _register(undy_vault_prices, governance, vault)
    live = undy_vault_prices.getLatestSnapshot(vault)
    assert live.pricePerShare == EIGHTEEN_DECIMALS
    vault.setSharePrice(10 ** 16)
    vault.setAsset(bravo_token.address)
    rebound = undy_vault_prices.getLatestSnapshot(vault)
    assert rebound.pricePerShare == 0
    assert rebound.totalSupply == 0
    assert undy_vault_prices.getPrice(vault) == 0
    vault.setSharePrice(EIGHTEEN_DECIMALS)
    vault.setAsset(alpha_token.address)
    restored = undy_vault_prices.getLatestSnapshot(vault)
    assert restored.pricePerShare == EIGHTEEN_DECIMALS


def test_undy_capacity_update_cancels_if_rebound_during_timelock(
    governance,
    switchboard_alpha,
    mission_control,
    mock_undy_v2,
    mock_price_source,
    alpha_token,
    bravo_token,
    undy_vault_prices,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    vault = boa.loads(MUTABLE_VAULT, alpha_token.address)
    _register(undy_vault_prices, governance, vault)
    assert undy_vault_prices.updatePriceConfig(vault, 0, 5, 0, 0, sender=governance.address)
    vault.setSharePrice(10 ** 16)
    vault.setAsset(bravo_token.address)
    boa.env.time_travel(blocks=undy_vault_prices.actionTimeLock() + 1)
    assert not undy_vault_prices.confirmPriceFeedUpdate(vault, sender=governance.address)
    assert not undy_vault_prices.hasPendingPriceFeedUpdate(vault)
    assert undy_vault_prices.priceConfigs(vault).maxNumSnapshots == 10
    vault.setSharePrice(EIGHTEEN_DECIMALS)
    vault.setAsset(alpha_token.address)
    assert undy_vault_prices.getPrice(vault) == EIGHTEEN_DECIMALS
    assert undy_vault_prices.getPrice(vault) != 10 ** 16


def test_undy_rejects_decimals_above_77(
    governance,
    switchboard_alpha,
    mission_control,
    mock_undy_v2,
    mock_price_source,
    alpha_token,
    undy_vault_prices,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    vault = boa.loads(MUTABLE_VAULT, alpha_token.address)
    vault.setDecimals(78)
    with boa.reverts("invalid feed"):
        undy_vault_prices.addNewPriceFeed(vault, 0, 10, 0, 0, sender=governance.address)


def test_undy_rejects_underlying_decimals_above_77(
    governance,
    switchboard_alpha,
    mission_control,
    mock_undy_v2,
    mock_price_source,
    undy_vault_prices,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    underlying = boa.loads(MUTABLE_UNDERLYING)
    underlying.setDecimals(78)
    mock_price_source.setPrice(underlying, EIGHTEEN_DECIMALS)
    vault = boa.loads(MUTABLE_VAULT, underlying.address)
    with boa.reverts("invalid feed"):
        undy_vault_prices.addNewPriceFeed(vault, 0, 10, 0, 0, sender=governance.address)
