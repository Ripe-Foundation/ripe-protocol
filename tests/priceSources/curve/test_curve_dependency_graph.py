"""Adversarial regression tests for CurvePrices dependency-cycle admission."""

import boa

from constants import (
    CURVE_POOL_TYPE_METAPOOL,
    CURVE_POOL_TYPE_STABLESWAP_NG,
    CURVE_POOL_TYPE_TWO_CRYPTO_NG,
    EIGHTEEN_DECIMALS,
    ZERO_ADDRESS,
)
from priceSources.curve.test_curve_rejects_more_than_four_underlyings import (
    CURVE_MR,
    CURVE_POOL,
    CURVE_POOL_WITH_SUPPLY,
    _load_curve,
    _setup_system,
)


TYPED_CURVE_AP = """
# @version 0.4.3

mr: public(address)
selectedRegistryId: public(uint256)

@deploy
def __init__(_mr: address, _selectedRegistryId: uint256):
    self.mr = _mr
    self.selectedRegistryId = _selectedRegistryId

@view
@external
def get_address(_id: uint256) -> address:
    if _id == 7:
        return self.mr
    if _id == self.selectedRegistryId:
        return self
    return convert(1000 + _id, address)
"""


def _coins(first, second):
    return [first, second] + [ZERO_ADDRESS] * 6


def _curve_system(
    ripe_hq,
    governance,
    green_token,
    savings_green,
    alpha_token,
    bravo_token,
    charlie_token,
    delta_token,
    fork,
    first,
    second,
):
    mr, ap, pool, lp, _ = _setup_system(
        alpha_token,
        bravo_token,
        charlie_token,
        delta_token,
        2,
        coins8=_coins(first, second),
    )
    curve = _load_curve(ripe_hq, green_token, savings_green, fork, ap)
    assert curve.setActionTimeLockAfterSetup(sender=governance.address)
    return curve, mr, pool, lp


def _typed_lp_system(
    ripe_hq,
    governance,
    green_token,
    savings_green,
    fork,
    registry_id,
    underlyings,
):
    mr = boa.loads(CURVE_MR, name="typed_curve_meta_registry")
    ap = boa.loads(
        TYPED_CURVE_AP,
        mr.address,
        registry_id,
        name="typed_curve_address_provider",
    )
    pool = boa.loads(CURVE_POOL, name="typed_curve_pool")
    lp = boa.loads(CURVE_POOL_WITH_SUPPLY, name="typed_curve_lp")
    lp.setSupply(EIGHTEEN_DECIMALS)
    mr.setup(
        list(underlyings) + [ZERO_ADDRESS] * (8 - len(underlyings)),
        lp,
        ap.address,
        len(underlyings),
    )
    curve = _load_curve(ripe_hq, green_token, savings_green, fork, ap)
    assert curve.setActionTimeLockAfterSetup(sender=governance.address)
    return curve, pool, lp


def _inject_single_asset_route(curve, asset, dependency, label):
    pool = boa.env.generate_address(f"{label} pool")
    lp = boa.env.generate_address(f"{label} lp")
    curve.eval(
        f"self.curveConfig[{asset}] = CurvePriceConfig("
        f"pool={pool}, "
        f"lpToken={lp}, "
        "numUnderlying=2, "
        f"underlying=[{asset}, {dependency}, empty(address), empty(address)], "
        "poolType=PoolType.STABLESWAP_NG, "
        "hasEcoToken=False)"
    )
    curve.eval(f"priceData._addPricedAsset({asset})")
    return pool


def _advance(curve):
    boa.env.time_travel(blocks=curve.actionTimeLock() + 1)


def test_rejects_direct_single_asset_self_reference(
    ripe_hq,
    governance,
    green_token,
    savings_green,
    mock_price_source,
    alpha_token,
    bravo_token,
    charlie_token,
    delta_token,
    fork,
):
    curve, _, pool, _ = _curve_system(
        ripe_hq,
        governance,
        green_token,
        savings_green,
        alpha_token,
        bravo_token,
        charlie_token,
        delta_token,
        fork,
        alpha_token.address,
        alpha_token.address,
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)

    assert not curve.isValidNewFeed(alpha_token, pool)
    with boa.reverts("invalid pool"):
        curve.addNewPriceFeed(alpha_token, pool, sender=governance.address)
    assert curve.pendingUpdates(alpha_token).actionId == 0
    assert curve.curveConfig(alpha_token).pool == ZERO_ADDRESS


def test_rejects_two_node_cross_pool_cycle_but_accepts_acyclic_route(
    ripe_hq,
    governance,
    green_token,
    savings_green,
    mock_price_source,
    alpha_token,
    bravo_token,
    charlie_token,
    delta_token,
    fork,
):
    curve, _, pool, _ = _curve_system(
        ripe_hq,
        governance,
        green_token,
        savings_green,
        alpha_token,
        bravo_token,
        charlie_token,
        delta_token,
        fork,
        alpha_token.address,
        bravo_token.address,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)

    _inject_single_asset_route(
        curve, bravo_token.address, charlie_token.address, "bravo acyclic"
    )
    assert curve.isValidNewFeed(alpha_token, pool)

    curve.eval(
        f"self.curveConfig[{bravo_token.address}].underlying[1] = "
        f"{alpha_token.address}"
    )
    assert not curve.isValidNewFeed(alpha_token, pool)
    with boa.reverts("invalid pool"):
        curve.addNewPriceFeed(alpha_token, pool, sender=governance.address)


def test_rejects_transitive_cross_pool_cycle_and_accepts_open_chain(
    ripe_hq,
    governance,
    green_token,
    savings_green,
    mock_price_source,
    alpha_token,
    bravo_token,
    charlie_token,
    delta_token,
    fork,
):
    curve, _, pool, _ = _curve_system(
        ripe_hq,
        governance,
        green_token,
        savings_green,
        alpha_token,
        bravo_token,
        charlie_token,
        delta_token,
        fork,
        alpha_token.address,
        bravo_token.address,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    tail = boa.env.generate_address("external graph tail")

    _inject_single_asset_route(
        curve, bravo_token.address, charlie_token.address, "bravo to charlie"
    )
    _inject_single_asset_route(
        curve, charlie_token.address, delta_token.address, "charlie to delta"
    )
    _inject_single_asset_route(curve, delta_token.address, tail, "delta to tail")
    assert curve.isValidNewFeed(alpha_token, pool)

    curve.eval(
        f"self.curveConfig[{delta_token.address}].underlying[1] = "
        f"{alpha_token.address}"
    )
    assert not curve.isValidNewFeed(alpha_token, pool)
    with boa.reverts("invalid pool"):
        curve.addNewPriceFeed(alpha_token, pool, sender=governance.address)


def test_sgreen_dependency_canonicalizes_to_green_for_cycle_detection(
    ripe_hq,
    governance,
    green_token,
    savings_green,
    mock_price_source,
    alpha_token,
    bravo_token,
    charlie_token,
    delta_token,
    fork,
):
    curve, _, pool, _ = _curve_system(
        ripe_hq,
        governance,
        green_token,
        savings_green,
        alpha_token,
        bravo_token,
        charlie_token,
        delta_token,
        fork,
        alpha_token.address,
        savings_green.address,
    )
    mock_price_source.setPrice(savings_green, EIGHTEEN_DECIMALS)
    _inject_single_asset_route(
        curve, green_token.address, alpha_token.address, "green to alpha"
    )

    assert not curve.isValidNewFeed(alpha_token, pool)
    with boa.reverts("invalid pool"):
        curve.addNewPriceFeed(alpha_token, pool, sender=governance.address)


def test_stable_lp_checks_index_three_when_earlier_underlyings_are_open(
    ripe_hq,
    governance,
    green_token,
    savings_green,
    mock_price_source,
    alpha_token,
    bravo_token,
    charlie_token,
    delta_token,
    fork,
):
    _, ap, pool, lp, _ = _setup_system(
        alpha_token, bravo_token, charlie_token, delta_token, 4
    )
    curve = _load_curve(ripe_hq, green_token, savings_green, fork, ap)
    assert curve.setActionTimeLockAfterSetup(sender=governance.address)
    tokens = (alpha_token, bravo_token, charlie_token, delta_token)
    for token in tokens:
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)

    config = curve.getCurvePoolConfig(pool)
    assert config.poolType == CURVE_POOL_TYPE_STABLESWAP_NG
    assert list(config.underlying) == [token.address for token in tokens]
    assert curve.isValidNewFeed(lp, pool)

    # Keep indices zero through two open. The only path back to the candidate
    # LP starts at index three, proving the full stable underlying set is read.
    for token in tokens[:3]:
        assert curve.curveConfig(token).pool == ZERO_ADDRESS
        assert curve.indexOfAsset(token) == 0
    _inject_single_asset_route(
        curve, delta_token.address, lp.address, "stable index three backedge"
    )
    for token in tokens[:3]:
        assert curve.curveConfig(token).pool == ZERO_ADDRESS
        assert curve.indexOfAsset(token) == 0
    assert not curve.isValidNewFeed(lp, pool)
    with boa.reverts("invalid pool"):
        curve.addNewPriceFeed(lp, pool, sender=governance.address)


def test_stable_lp_handles_merged_dependency_branches(
    ripe_hq,
    governance,
    green_token,
    savings_green,
    mock_price_source,
    alpha_token,
    bravo_token,
    charlie_token,
    delta_token,
    fork,
):
    mr, ap, pool, lp, _ = _setup_system(
        alpha_token, bravo_token, charlie_token, delta_token, 4
    )
    curve = _load_curve(ripe_hq, green_token, savings_green, fork, ap)
    assert curve.setActionTimeLockAfterSetup(sender=governance.address)
    for token in (alpha_token, bravo_token, charlie_token, delta_token):
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)

    shared = boa.env.generate_address("shared graph node")
    tail = boa.env.generate_address("shared graph tail")
    _inject_single_asset_route(curve, alpha_token.address, shared, "alpha branch")
    _inject_single_asset_route(curve, bravo_token.address, shared, "bravo branch")
    _inject_single_asset_route(curve, shared, tail, "shared branch")
    assert curve.isValidNewFeed(lp, pool)

    # A cycle reachable through either merged branch must reject the LP route.
    curve.eval(
        f"self.curveConfig[{shared}].underlying[1] = {lp.address}"
    )
    assert not curve.isValidNewFeed(lp, pool)


def test_crypto_lp_index_zero_cycle_is_rejected(
    ripe_hq,
    governance,
    green_token,
    savings_green,
    mock_price_source,
    alpha_token,
    bravo_token,
    fork,
):
    curve, pool, lp = _typed_lp_system(
        ripe_hq,
        governance,
        green_token,
        savings_green,
        fork,
        13,
        (alpha_token.address, bravo_token.address),
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    config = curve.getCurvePoolConfig(pool)
    assert config.poolType == CURVE_POOL_TYPE_TWO_CRYPTO_NG
    assert curve.isValidNewFeed(lp, pool)

    _inject_single_asset_route(
        curve, alpha_token.address, lp.address, "crypto priced backedge"
    )
    assert not curve.isValidNewFeed(lp, pool)
    with boa.reverts("invalid pool"):
        curve.addNewPriceFeed(lp, pool, sender=governance.address)


def test_crypto_lp_nonpriced_index_one_backedge_is_not_over_rejected(
    ripe_hq,
    governance,
    green_token,
    savings_green,
    mock_price_source,
    alpha_token,
    bravo_token,
    fork,
):
    curve, pool, lp = _typed_lp_system(
        ripe_hq,
        governance,
        green_token,
        savings_green,
        fork,
        13,
        (alpha_token.address, bravo_token.address),
    )
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    config = curve.getCurvePoolConfig(pool)
    assert config.poolType == CURVE_POOL_TYPE_TWO_CRYPTO_NG

    # Crypto LP pricing queries only index zero. A Curve route from index one
    # back to the LP therefore is not an executable price dependency cycle.
    _inject_single_asset_route(
        curve, bravo_token.address, lp.address, "crypto nonpriced backedge"
    )
    assert curve.curveConfig(alpha_token).pool == ZERO_ADDRESS
    assert curve.indexOfAsset(alpha_token) == 0
    assert curve.isValidNewFeed(lp, pool)
    assert curve.addNewPriceFeed(lp, pool, sender=governance.address)
    pending = curve.pendingUpdates(lp)
    assert pending.config.pool == pool.address
    assert pending.config.poolType == CURVE_POOL_TYPE_TWO_CRYPTO_NG


def test_metapool_checks_index_three_when_earlier_underlyings_are_open(
    ripe_hq,
    governance,
    green_token,
    savings_green,
    mock_price_source,
    alpha_token,
    bravo_token,
    charlie_token,
    delta_token,
    fork,
):
    tokens = (alpha_token, bravo_token, charlie_token, delta_token)
    curve, pool, lp = _typed_lp_system(
        ripe_hq,
        governance,
        green_token,
        savings_green,
        fork,
        3,
        tuple(token.address for token in tokens),
    )
    for token in tokens:
        mock_price_source.setPrice(token, EIGHTEEN_DECIMALS)
    config = curve.getCurvePoolConfig(pool)
    assert config.poolType == CURVE_POOL_TYPE_METAPOOL
    assert list(config.underlying) == [token.address for token in tokens]
    assert curve.isValidNewFeed(lp, pool)

    for token in tokens[:3]:
        assert curve.curveConfig(token).pool == ZERO_ADDRESS
        assert curve.indexOfAsset(token) == 0
    _inject_single_asset_route(
        curve, delta_token.address, lp.address, "metapool index three backedge"
    )
    assert not curve.isValidNewFeed(lp, pool)
    with boa.reverts("invalid pool"):
        curve.addNewPriceFeed(lp, pool, sender=governance.address)


def test_new_confirmation_cancels_when_graph_becomes_cyclic_during_timelock(
    ripe_hq,
    governance,
    green_token,
    savings_green,
    mock_price_source,
    alpha_token,
    bravo_token,
    charlie_token,
    delta_token,
    fork,
):
    curve, _, pool, _ = _curve_system(
        ripe_hq,
        governance,
        green_token,
        savings_green,
        alpha_token,
        bravo_token,
        charlie_token,
        delta_token,
        fork,
        alpha_token.address,
        bravo_token.address,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    assert curve.addNewPriceFeed(alpha_token, pool, sender=governance.address)
    action_id = curve.pendingUpdates(alpha_token).actionId

    _inject_single_asset_route(
        curve, bravo_token.address, alpha_token.address, "late bravo cycle"
    )
    _advance(curve)
    assert not curve.confirmNewPriceFeed(alpha_token, sender=governance.address)

    assert not curve.hasPendingAction(action_id)
    assert curve.pendingUpdates(alpha_token).actionId == 0
    assert curve.curveConfig(alpha_token).pool == ZERO_ADDRESS
    assert curve.indexOfAsset(alpha_token) == 0
    assert curve.curveConfig(bravo_token).pool != ZERO_ADDRESS


def test_update_confirmation_cancels_cycle_and_preserves_active_route(
    ripe_hq,
    governance,
    green_token,
    savings_green,
    mock_price_source,
    alpha_token,
    bravo_token,
    charlie_token,
    delta_token,
    fork,
):
    curve, mr, old_pool, _ = _curve_system(
        ripe_hq,
        governance,
        green_token,
        savings_green,
        alpha_token,
        bravo_token,
        charlie_token,
        delta_token,
        fork,
        alpha_token.address,
        delta_token.address,
    )
    mock_price_source.setPrice(delta_token, EIGHTEEN_DECIMALS)
    assert curve.addNewPriceFeed(alpha_token, old_pool, sender=governance.address)
    _advance(curve)
    assert curve.confirmNewPriceFeed(alpha_token, sender=governance.address)
    previous = curve.curveConfig(alpha_token)
    previous_index = curve.indexOfAsset(alpha_token)

    new_pool = boa.loads(CURVE_POOL, name="curve_cycle_update_pool")
    mr.setCoins(_coins(alpha_token.address, bravo_token.address))
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    assert curve.updatePriceFeed(alpha_token, new_pool, sender=governance.address)
    action_id = curve.pendingUpdates(alpha_token).actionId

    _inject_single_asset_route(
        curve, bravo_token.address, alpha_token.address, "late update cycle"
    )
    _advance(curve)
    assert not curve.confirmPriceFeedUpdate(alpha_token, sender=governance.address)

    assert not curve.hasPendingAction(action_id)
    assert curve.pendingUpdates(alpha_token).actionId == 0
    assert curve.curveConfig(alpha_token) == previous
    assert curve.indexOfAsset(alpha_token) == previous_index


def test_latest_curve_proposal_snapshot_replaces_prior_candidate(
    ripe_hq,
    governance,
    green_token,
    savings_green,
    mock_price_source,
    alpha_token,
    bravo_token,
    charlie_token,
    delta_token,
    fork,
):
    curve, mr, first_pool, _ = _curve_system(
        ripe_hq,
        governance,
        green_token,
        savings_green,
        alpha_token,
        bravo_token,
        charlie_token,
        delta_token,
        fork,
        alpha_token.address,
        bravo_token.address,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(charlie_token, EIGHTEEN_DECIMALS)
    assert curve.addNewPriceFeed(alpha_token, first_pool, sender=governance.address)
    first_action = curve.pendingUpdates(alpha_token).actionId

    second_pool = boa.loads(CURVE_POOL, name="replacement_curve_pool")
    mr.setCoins(_coins(alpha_token.address, charlie_token.address))
    assert curve.addNewPriceFeed(alpha_token, second_pool, sender=governance.address)
    pending = curve.pendingUpdates(alpha_token)
    second_action = pending.actionId
    assert second_action != first_action
    assert curve.hasPendingAction(first_action)
    assert curve.hasPendingAction(second_action)
    assert pending.config.pool == second_pool.address
    assert pending.config.underlying[1] == charlie_token.address

    # A cycle involving only the superseded candidate must not poison the latest.
    _inject_single_asset_route(
        curve, bravo_token.address, alpha_token.address, "superseded cycle"
    )
    _advance(curve)
    assert curve.confirmNewPriceFeed(alpha_token, sender=governance.address)
    assert curve.curveConfig(alpha_token).pool == second_pool.address
    assert not curve.hasPendingAction(second_action)
    # The superseded TimeLock record remains confirmable in isolation, but it
    # is inert because only the latest proposal occupies pendingUpdates and
    # successful activation clears that endpoint state.
    assert curve.hasPendingAction(first_action)
    assert curve.canConfirmAction(first_action)
    assert curve.pendingUpdates(alpha_token).actionId == 0
    with boa.reverts("no pending new feed"):
        curve.confirmNewPriceFeed(alpha_token, sender=governance.address)


def test_inconsistent_active_dependency_without_index_fails_closed(
    ripe_hq,
    governance,
    green_token,
    savings_green,
    mock_price_source,
    alpha_token,
    bravo_token,
    charlie_token,
    delta_token,
    fork,
):
    curve, _, pool, _ = _curve_system(
        ripe_hq,
        governance,
        green_token,
        savings_green,
        alpha_token,
        bravo_token,
        charlie_token,
        delta_token,
        fork,
        alpha_token.address,
        bravo_token.address,
    )
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    orphan_pool = boa.env.generate_address("orphan active pool")
    orphan_lp = boa.env.generate_address("orphan active lp")
    curve.eval(
        f"self.curveConfig[{bravo_token.address}] = CurvePriceConfig("
        f"pool={orphan_pool}, "
        f"lpToken={orphan_lp}, "
        "numUnderlying=2, "
        f"underlying=[{bravo_token.address}, {charlie_token.address}, empty(address), empty(address)], "
        "poolType=PoolType.STABLESWAP_NG, "
        "hasEcoToken=False)"
    )
    assert curve.indexOfAsset(bravo_token) == 0
    assert not curve.isValidNewFeed(alpha_token, pool)


def test_full_fifty_asset_depth_is_bounded_and_detects_tail_cycle(
    ripe_hq,
    governance,
    green_token,
    savings_green,
    mock_price_source,
    alpha_token,
    bravo_token,
    charlie_token,
    delta_token,
    fork,
):
    first_node = "0x0000000000000000000000000000000000001001"
    curve, _, pool, _ = _curve_system(
        ripe_hq,
        governance,
        green_token,
        savings_green,
        alpha_token,
        bravo_token,
        charlie_token,
        delta_token,
        fork,
        alpha_token.address,
        first_node,
    )
    mock_price_source.setPrice(first_node, EIGHTEEN_DECIMALS)

    # Build all 50 normally representable active nodes in one evaluated helper.
    curve.eval(
        "for i: uint256 in range(50):\n"
        "                node: address = convert(4097 + i, address)\n"
        "                dependency: address = convert(4098 + i, address)\n"
        "                self.curveConfig[node] = CurvePriceConfig(\n"
        "                    pool=convert(12289 + i, address),\n"
        "                    lpToken=convert(20481 + i, address),\n"
        "                    numUnderlying=2,\n"
        "                    underlying=[node, dependency, empty(address), empty(address)],\n"
        "                    poolType=PoolType.STABLESWAP_NG,\n"
        "                    hasEcoToken=False,\n"
        "                )\n"
        "                priceData._addPricedAsset(node)"
    )
    assert curve.numAssets() == 51
    assert curve.indexOfAsset("0x0000000000000000000000000000000000001032") == 50

    assert curve.isValidNewFeed(alpha_token, pool, gas=5_000_000)
    acyclic_gas = curve._computation.get_gas_used()
    print(f"CURVE_50_ASSET_ACYCLIC_VALIDATION_GAS={acyclic_gas}")
    assert acyclic_gas < 2_000_000

    curve.eval(
        f"self.curveConfig[0x0000000000000000000000000000000000001032].underlying[1] = "
        f"{alpha_token.address}"
    )
    assert not curve.isValidNewFeed(alpha_token, pool, gas=5_000_000)
    cyclic_gas = curve._computation.get_gas_used()
    print(f"CURVE_50_ASSET_CYCLIC_VALIDATION_GAS={cyclic_gas}")
    assert cyclic_gas < 2_000_000
