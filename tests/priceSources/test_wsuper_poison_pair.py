import boa

from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS


MOCK_WRAPPED_SUPER = """
# @version 0.4.3

_asset: address

@deploy
def __init__(_asset: address):
    self._asset = _asset

@view
@external
def asset() -> address:
    return self._asset

@view
@external
def convertToAssets(_shares: uint256) -> uint256:
    return _shares
"""


def _load_wsuper(ripe_hq, mcbeth, super_oeth, wrapped, vvv):
    return boa.load(
        "contracts/priceSources/wsuperOETHbPrices.vy",
        ripe_hq,
        mcbeth,
        super_oeth,
        wrapped,
        vvv,
        1,
        100,
        name="wsuper_poison_source",
    )


def test_wsuper_mcbeth_and_vvv_are_not_priceable(
    ripe_hq,
    mock_yield_registry,
    alpha_token,
    bravo_token,
):
    src = _load_wsuper(
        ripe_hq,
        alpha_token.address,
        mock_yield_registry,
        mock_yield_registry,
        bravo_token.address,
    )
    assert src.getPrice(alpha_token) == 0
    assert src.getPriceAndHasFeed(alpha_token) == (0, False)
    assert src.hasPriceFeed(alpha_token) is False
    assert src.getPrice(bravo_token) == 0
    assert src.getPriceAndHasFeed(bravo_token) == (0, False)
    assert src.hasPriceFeed(bravo_token) is False
    priced = [str(a).lower() for a in src.getPricedAssets()]
    assert str(alpha_token.address).lower() not in priced
    assert str(bravo_token.address).lower() not in priced
    assert not hasattr(src, "resetVvvPrice")
    assert not hasattr(src, "vvvPrice")


def test_wsuper_wrapped_super_still_listed(
    ripe_hq,
    mock_yield_registry,
    mock_price_source,
    price_desk,
    switchboard_alpha,
    mission_control,
    alpha_token,
    bravo_token,
):
    with boa.env.anchor():
        super_oeth = alpha_token
        wrapped = boa.loads(MOCK_WRAPPED_SUPER, super_oeth.address)
        src = _load_wsuper(
            ripe_hq,
            bravo_token.address,
            super_oeth.address,
            wrapped.address,
            mock_yield_registry,
        )
        mock_price_source.setPrice(super_oeth, 3 * EIGHTEEN_DECIMALS)
        mission_control.setPriorityPriceSourceIds([6], sender=switchboard_alpha.address)
        assert src.hasPriceFeed(wrapped) is True
        priced = [str(a).lower() for a in src.getPricedAssets()]
        assert str(wrapped.address).lower() in priced
        assert src.getPrice(wrapped) == 3 * EIGHTEEN_DECIMALS
        assert src.getPriceAndHasFeed(wrapped) == (3 * EIGHTEEN_DECIMALS, True)
        assert price_desk.getPrice(super_oeth) == 3 * EIGHTEEN_DECIMALS


def test_later_source_can_still_price_mcbeth_and_vvv(
    ripe_hq,
    mock_yield_registry,
    mock_price_source,
    price_desk,
    switchboard_alpha,
    mission_control,
    governance,
    alpha_token,
    bravo_token,
):
    with boa.env.anchor():
        src = _load_wsuper(
            ripe_hq,
            alpha_token.address,
            mock_yield_registry,
            mock_yield_registry,
            bravo_token.address,
        )
        assert price_desk.startAddNewAddressToRegistry(
            src, "wsuper later source", sender=governance.address
        )
        boa.env.time_travel(blocks=price_desk.registryChangeTimeLock() + 1)
        wsuper_id = price_desk.confirmNewAddressToRegistry(src, sender=governance.address)

        mock_price_source.setPrice(alpha_token, 0)
        mock_price_source.setPrice(bravo_token, 0)
        mission_control.setPriorityPriceSourceIds(
            [wsuper_id, 6], sender=switchboard_alpha.address
        )
        assert src.getPriceAndHasFeed(alpha_token) == (0, False)
        assert src.getPriceAndHasFeed(bravo_token) == (0, False)
        assert price_desk.getPrice(alpha_token) == 0
        assert price_desk.getPrice(bravo_token) == 0

        mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
        mock_price_source.setPrice(bravo_token, 2 * EIGHTEEN_DECIMALS)
        assert price_desk.getPrice(alpha_token) == EIGHTEEN_DECIMALS
        assert price_desk.getPrice(bravo_token) == 2 * EIGHTEEN_DECIMALS
        assert src.getPrice(alpha_token) == 0
        assert src.getPrice(bravo_token) == 0
        assert src.MCBETH() != ZERO_ADDRESS
        assert src.VVV() != ZERO_ADDRESS
