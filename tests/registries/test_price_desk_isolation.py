import boa
import pytest

from conf_utils import filter_logs, redeem_collateral
from constants import EIGHTEEN_DECIMALS


ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"
RAW_CANONICAL = 0
RAW_REVERT = 1
RAW_EMPTY = 2
RAW_SHORT = 3
RAW_OVERSIZED_ONE = 4
RAW_NONCANONICAL_BOOL = 5
RAW_OVERSIZED_96 = 6
RAW_SNAPSHOT_FALSE = 7


def _raw_source(
    price=0,
    has_feed=False,
    price_mode=0,
    has_feed_mode=0,
    snapshot_mode=0,
):
    source = boa.load(
        "contracts/mock/MockRawPriceSource.vy",
        name="raw_price_source",
    )
    source.configure(
        price,
        has_feed,
        price_mode,
        has_feed_mode,
        snapshot_mode,
    )
    return source


def _gas_source(
    price=0,
    has_feed=False,
    price_iterations=0,
    has_feed_iterations=0,
    snapshot_iterations=0,
    exhaust_price=False,
    exhaust_has_feed=False,
    exhaust_snapshot=False,
):
    source = boa.load(
        "contracts/mock/MockGasBurningPriceSource.vy",
        name="gas_burning_price_source",
    )
    source.configure(
        price,
        has_feed,
        price_iterations,
        has_feed_iterations,
        snapshot_iterations,
        exhaust_price,
        exhaust_has_feed,
        exhaust_snapshot,
    )
    return source


def _isolated_price_desk(ripe_hq, deploy3r, sources):
    desk = boa.load(
        "contracts/registries/PriceDesk.vy",
        ripe_hq,
        deploy3r,
        ETH,
        1,
        2,
        name="isolated_price_desk",
    )
    for index, source in enumerate(sources, start=1):
        assert desk.startAddNewAddressToRegistry(
            source,
            f"source {index}",
            sender=deploy3r,
        )
        assert desk.confirmNewAddressToRegistry(source, sender=deploy3r) == index
    return desk


def _set_priorities(mission_control, switchboard_alpha, source_ids):
    mission_control.setPriorityPriceSourceIds(
        source_ids,
        sender=switchboard_alpha.address,
    )


def _register_sources(price_desk, governance, sources):
    for index, source in enumerate(sources, start=1):
        assert price_desk.startAddNewAddressToRegistry(
            source,
            f"isolation {index}",
            sender=governance.address,
        )
    boa.env.time_travel(blocks=price_desk.registryChangeTimeLock() + 1)
    ids = []
    for source in sources:
        ids.append(
            price_desk.confirmNewAddressToRegistry(
                source,
                sender=governance.address,
            )
        )
    return ids


def _count_calls(computation, address, selector):
    expected = bytes.fromhex(str(address)[2:])
    return sum(
        child.msg.code_address == expected and bytes(child.msg.data[:4]) == selector
        for child in computation.children
    ) + sum(_count_calls(child, address, selector) for child in computation.children)


def test_reverting_priority_source_falls_through_to_healthy_source(
    ripe_hq,
    deploy3r,
    alpha_token,
    mission_control,
    switchboard_alpha,
):
    failed = _raw_source(price_mode=1)
    healthy = _raw_source(2 * EIGHTEEN_DECIMALS, True)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [failed, healthy])
    _set_priorities(mission_control, switchboard_alpha, [1, 2])

    assert desk.getPrice(alpha_token, True) == 2 * EIGHTEEN_DECIMALS


def test_reverting_non_priority_source_falls_through_to_healthy_source(
    ripe_hq,
    deploy3r,
    alpha_token,
    mission_control,
    switchboard_alpha,
):
    failed = _raw_source(price_mode=1)
    healthy = _raw_source(3 * EIGHTEEN_DECIMALS, True)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [failed, healthy])
    _set_priorities(mission_control, switchboard_alpha, [])

    assert desk.getPrice(alpha_token, True) == 3 * EIGHTEEN_DECIMALS


def test_disabled_middle_slot_falls_through_across_all_traversal_channels(
    ripe_hq,
    deploy3r,
    alpha_token,
    mission_control,
    switchboard_alpha,
    teller,
):
    first = _raw_source(0, False)
    disabled = _raw_source(99 * EIGHTEEN_DECIMALS, True)
    healthy = _raw_source(12 * EIGHTEEN_DECIMALS, True)
    desk = _isolated_price_desk(
        ripe_hq,
        deploy3r,
        [first, disabled, healthy],
    )
    assert desk.startAddressDisableInRegistry(2, sender=deploy3r)
    assert desk.confirmAddressDisableInRegistry(2, sender=deploy3r)
    assert desk.getAddr(2) == "0x" + "0" * 40
    _set_priorities(mission_control, switchboard_alpha, [1, 2])

    assert desk.getPrice(alpha_token, False) == 12 * EIGHTEEN_DECIMALS
    assert desk.getPrice(alpha_token, True) == 12 * EIGHTEEN_DECIMALS
    assert desk.hasPriceFeed(alpha_token)
    assert desk.addPriceSnapshot(alpha_token, sender=teller.address)
    assert first.snapshotCount() == 0
    assert disabled.snapshotCount() == 0
    assert healthy.snapshotCount() == 1


def test_priority_source_is_not_repeated_in_general_registry_traversal(
    ripe_hq,
    deploy3r,
    alpha_token,
    mission_control,
    switchboard_alpha,
):
    priority_no_feed = _raw_source(0, False)
    healthy = _raw_source(13 * EIGHTEEN_DECIMALS, True)
    desk = _isolated_price_desk(
        ripe_hq,
        deploy3r,
        [priority_no_feed, healthy],
    )
    _set_priorities(mission_control, switchboard_alpha, [1])

    assert desk.getPrice(alpha_token, True) == 13 * EIGHTEEN_DECIMALS
    selector = bytes(
        priority_no_feed.getPriceAndHasFeed.prepare_calldata(
            alpha_token,
            0,
            desk,
        )[:4]
    )
    assert (
        _count_calls(
            desk._computation,
            priority_no_feed.address,
            selector,
        )
        == 1
    )


@pytest.mark.parametrize(
    "mode",
    (
        RAW_EMPTY,
        RAW_SHORT,
        RAW_OVERSIZED_ONE,
        RAW_NONCANONICAL_BOOL,
        RAW_OVERSIZED_96,
    ),
    ids=("empty", "short", "oversized_65", "noncanonical_bool", "oversized_96"),
)
def test_malformed_price_response_falls_through_to_healthy_source(
    mode,
    ripe_hq,
    deploy3r,
    alpha_token,
    mission_control,
    switchboard_alpha,
):
    malformed = _raw_source(99 * EIGHTEEN_DECIMALS, True, price_mode=mode)
    healthy = _raw_source(4 * EIGHTEEN_DECIMALS, True)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [malformed, healthy])
    _set_priorities(mission_control, switchboard_alpha, [1, 2])

    assert desk.getPrice(alpha_token, True) == 4 * EIGHTEEN_DECIMALS


def test_exact_canonical_response_and_primary_price_still_win(
    ripe_hq,
    deploy3r,
    alpha_token,
    mission_control,
    switchboard_alpha,
):
    primary = _raw_source(5 * EIGHTEEN_DECIMALS, True)
    fallback = _raw_source(6 * EIGHTEEN_DECIMALS, True)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [primary, fallback])
    _set_priorities(mission_control, switchboard_alpha, [1, 2])

    assert desk.getPrice(alpha_token, True) == 5 * EIGHTEEN_DECIMALS


def test_valid_zero_configured_feed_falls_through_to_healthy_source(
    ripe_hq,
    deploy3r,
    alpha_token,
    mission_control,
    switchboard_alpha,
):
    zero_feed = _raw_source(0, True)
    healthy = _raw_source(7 * EIGHTEEN_DECIMALS, True)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [zero_feed, healthy])
    _set_priorities(mission_control, switchboard_alpha, [1, 2])

    assert desk.getPrice(alpha_token, True) == 7 * EIGHTEEN_DECIMALS


def test_zero_without_feed_remains_valid_no_feed(
    ripe_hq,
    deploy3r,
    alpha_token,
    mission_control,
    switchboard_alpha,
):
    no_feed = _raw_source(0, False)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [no_feed])
    _set_priorities(mission_control, switchboard_alpha, [1])

    assert desk.getPrice(alpha_token, False) == 0
    assert desk.getPrice(alpha_token, True) == 0


def test_positive_price_without_feed_is_malformed_and_falls_through(
    ripe_hq,
    deploy3r,
    alpha_token,
    mission_control,
    switchboard_alpha,
):
    contradictory = _raw_source(99 * EIGHTEEN_DECIMALS, False)
    healthy = _raw_source(8 * EIGHTEEN_DECIMALS, True)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [contradictory, healthy])
    _set_priorities(mission_control, switchboard_alpha, [1, 2])

    assert desk.getPrice(alpha_token, True) == 8 * EIGHTEEN_DECIMALS


def test_gas_burning_priority_source_falls_through_to_healthy_source(
    ripe_hq,
    deploy3r,
    alpha_token,
    mission_control,
    switchboard_alpha,
):
    burner = _gas_source(
        price_iterations=1_000_000,
        exhaust_price=True,
    )
    healthy = _gas_source(
        9 * EIGHTEEN_DECIMALS,
        True,
        price_iterations=2_000,
    )
    desk = _isolated_price_desk(ripe_hq, deploy3r, [burner, healthy])
    _set_priorities(mission_control, switchboard_alpha, [1, 2])

    assert desk.getPrice(alpha_token, True, gas=2_000_000) == 9 * EIGHTEEN_DECIMALS


def test_gas_burning_non_priority_source_falls_through_to_healthy_source(
    ripe_hq,
    deploy3r,
    alpha_token,
    mission_control,
    switchboard_alpha,
):
    burner = _gas_source(
        price_iterations=1_000_000,
        exhaust_price=True,
    )
    healthy = _raw_source(10 * EIGHTEEN_DECIMALS, True)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [burner, healthy])
    _set_priorities(mission_control, switchboard_alpha, [])

    assert desk.getPrice(alpha_token, True, gas=1_000_000) == 10 * EIGHTEEN_DECIMALS


def test_final_source_wins_in_three_source_selected_topology(
    ripe_hq,
    deploy3r,
    alpha_token,
    mission_control,
    switchboard_alpha,
):
    burners = [
        _gas_source(
            price_iterations=1_000_000,
            exhaust_price=True,
        )
        for _ in range(2)
    ]
    healthy = _gas_source(
        11 * EIGHTEEN_DECIMALS,
        True,
        price_iterations=2_000,
    )
    desk = _isolated_price_desk(ripe_hq, deploy3r, [*burners, healthy])
    _set_priorities(mission_control, switchboard_alpha, [1, 2])

    assert desk.numAddrs() - 1 == 3
    assert desk.getPrice(alpha_token, True, gas=2_000_000) == 11 * EIGHTEEN_DECIMALS
    gas_used = desk._computation.get_gas_used()
    print(
        "PRICEDESK_SELECTED_BOUNDARY",
        f"three_source_final_position={gas_used}",
        "source_slots=3",
        "outer_limit=2000000",
    )
    assert gas_used < 2_000_000


def test_final_source_wins_behind_nine_allowance_exhausting_sources(
    ripe_hq,
    deploy3r,
    alpha_token,
    mission_control,
    switchboard_alpha,
):
    burners = [
        _gas_source(
            price_iterations=1_000_000,
            exhaust_price=True,
        )
        for _ in range(9)
    ]
    healthy = _gas_source(
        11 * EIGHTEEN_DECIMALS,
        True,
        price_iterations=2_000,
    )
    desk = _isolated_price_desk(ripe_hq, deploy3r, [*burners, healthy])
    _set_priorities(mission_control, switchboard_alpha, [1, 2, 3])

    assert desk.numAddrs() - 1 == 10
    assert desk.getPrice(alpha_token, True, gas=6_000_000) == 11 * EIGHTEEN_DECIMALS
    gas_used = desk._computation.get_gas_used()
    print(
        "PRICEDESK_STRESS_BOUNDARY",
        f"ten_source_final_position={gas_used}",
        "priority_sources=3",
        "fallback_sources=7",
        "outer_limit=6000000",
    )
    assert gas_used < 6_000_000


def test_all_sources_failed_preserves_strict_and_non_strict_intent(
    ripe_hq,
    deploy3r,
    alpha_token,
    mission_control,
    switchboard_alpha,
):
    reverted = _raw_source(price_mode=1)
    malformed = _raw_source(price_mode=5)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [reverted, malformed])
    _set_priorities(mission_control, switchboard_alpha, [1, 2])

    assert desk.getPrice(alpha_token, False) == 0
    with boa.reverts("has price config, no price"):
        desk.getPrice(alpha_token, True)


@pytest.mark.parametrize(
    "mode",
    (
        RAW_REVERT,
        RAW_EMPTY,
        RAW_SHORT,
        RAW_OVERSIZED_ONE,
        RAW_NONCANONICAL_BOOL,
        RAW_OVERSIZED_96,
    ),
    ids=("revert", "empty", "short", "oversized_33", "noncanonical_bool", "oversized_96"),
)
def test_malformed_has_price_feed_falls_through_to_healthy_source(
    mode,
    ripe_hq,
    deploy3r,
    alpha_token,
):
    failed = _raw_source(has_feed=True, has_feed_mode=mode)
    healthy = _raw_source(has_feed=True)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [failed, healthy])

    assert desk.hasPriceFeed(alpha_token)


@pytest.mark.parametrize(
    "mode",
    (
        RAW_REVERT,
        RAW_EMPTY,
        RAW_SHORT,
        RAW_OVERSIZED_ONE,
        RAW_NONCANONICAL_BOOL,
        RAW_OVERSIZED_96,
    ),
    ids=("revert", "empty", "short", "oversized_33", "noncanonical_bool", "oversized_96"),
)
def test_all_failed_has_price_feed_queries_return_false(
    mode,
    ripe_hq,
    deploy3r,
    alpha_token,
):
    failed = _raw_source(has_feed=True, has_feed_mode=mode)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [failed])

    assert not desk.hasPriceFeed(alpha_token)


@pytest.mark.parametrize("has_feed", (False, True), ids=("false", "true"))
def test_canonical_has_price_feed_response_is_preserved(
    has_feed,
    ripe_hq,
    deploy3r,
    alpha_token,
):
    source = _raw_source(has_feed=has_feed)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [source])

    assert desk.hasPriceFeed(alpha_token) is has_feed


def test_gas_burning_has_feed_query_falls_through_to_healthy_source(
    ripe_hq,
    deploy3r,
    alpha_token,
):
    burner = _gas_source(
        has_feed=True,
        has_feed_iterations=1_000_000,
        exhaust_has_feed=True,
    )
    healthy = _raw_source(has_feed=True)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [burner, healthy])

    assert desk.hasPriceFeed(alpha_token, gas=500_000)


def test_all_gas_burning_has_feed_queries_return_false(
    ripe_hq,
    deploy3r,
    alpha_token,
):
    burner = _gas_source(
        has_feed=True,
        has_feed_iterations=1_000_000,
        exhaust_has_feed=True,
    )
    desk = _isolated_price_desk(ripe_hq, deploy3r, [burner])

    assert not desk.hasPriceFeed(alpha_token, gas=250_000)


def test_final_feed_wins_behind_nine_has_feed_allowance_exhausting_sources(
    ripe_hq,
    deploy3r,
    alpha_token,
):
    burners = [
        _gas_source(
            has_feed=True,
            has_feed_iterations=1_000_000,
            exhaust_has_feed=True,
        )
        for _ in range(9)
    ]
    healthy = _raw_source(has_feed=True)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [*burners, healthy])

    assert desk.numAddrs() - 1 == 10
    assert desk.hasPriceFeed(alpha_token, gas=2_000_000)
    gas_used = desk._computation.get_gas_used()
    print(
        "PRICEDESK_HAS_FEED_STRESS_BOUNDARY",
        f"ten_source_final_position={gas_used}",
        "outer_limit=2000000",
    )
    assert gas_used > 9 * 75_000
    assert gas_used < 2_000_000


@pytest.mark.parametrize(
    "mode",
    (
        RAW_REVERT,
        RAW_EMPTY,
        RAW_SHORT,
        RAW_OVERSIZED_ONE,
        RAW_NONCANONICAL_BOOL,
        RAW_OVERSIZED_96,
    ),
    ids=(
        "revert",
        "empty",
        "short",
        "oversized_33",
        "noncanonical_bool",
        "oversized_96",
    ),
)
def test_failed_snapshot_source_does_not_block_later_healthy_source(
    mode,
    ripe_hq,
    deploy3r,
    alpha_token,
    teller,
):
    failed = _raw_source(
        EIGHTEEN_DECIMALS,
        has_feed=True,
        snapshot_mode=mode,
    )
    healthy = _raw_source(EIGHTEEN_DECIMALS, has_feed=True)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [failed, healthy])

    assert desk.addPriceSnapshot(alpha_token, sender=teller.address)
    # A revert rolls back the failing source's own write. Malformed returndata
    # is observed only after a successful source call, so its write remains.
    assert failed.snapshotCount() == (0 if mode == 1 else 1)
    assert healthy.snapshotCount() == 1


def test_earlier_successful_snapshot_remains_when_later_source_fails(
    ripe_hq,
    deploy3r,
    alpha_token,
    teller,
):
    healthy = _raw_source(has_feed=True)
    failed = _raw_source(has_feed=True, snapshot_mode=1)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [healthy, failed])

    assert desk.addPriceSnapshot(alpha_token, sender=teller.address)
    assert healthy.snapshotCount() == 1
    assert failed.snapshotCount() == 0


def test_canonical_false_snapshot_does_not_report_an_update(
    ripe_hq,
    deploy3r,
    alpha_token,
    teller,
):
    false_only = _raw_source(
        EIGHTEEN_DECIMALS,
        has_feed=True,
        snapshot_mode=RAW_SNAPSHOT_FALSE,
    )
    desk = _isolated_price_desk(ripe_hq, deploy3r, [false_only])

    assert not desk.addPriceSnapshot(alpha_token, sender=teller.address)
    assert false_only.snapshotCount() == 1


def test_canonical_false_snapshot_does_not_mask_later_true_update(
    ripe_hq,
    deploy3r,
    alpha_token,
    teller,
):
    false_source = _raw_source(
        EIGHTEEN_DECIMALS,
        has_feed=True,
        snapshot_mode=RAW_SNAPSHOT_FALSE,
    )
    true_source = _raw_source(EIGHTEEN_DECIMALS, has_feed=True)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [false_source, true_source])

    assert desk.addPriceSnapshot(alpha_token, sender=teller.address)
    assert false_source.snapshotCount() == 1
    assert true_source.snapshotCount() == 1


def test_gas_burning_snapshot_update_does_not_block_later_true_update(
    ripe_hq,
    deploy3r,
    alpha_token,
    teller,
):
    burner = _gas_source(
        has_feed=True,
        has_feed_iterations=500,
        snapshot_iterations=1_000_000,
        exhaust_snapshot=True,
    )
    healthy = _raw_source(EIGHTEEN_DECIMALS, has_feed=True)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [burner, healthy])

    assert desk.addPriceSnapshot(
        alpha_token,
        sender=teller.address,
        gas=1_000_000,
    )
    assert healthy.snapshotCount() == 1


def test_gas_burning_has_feed_check_skips_snapshot_and_reaches_later_update(
    ripe_hq,
    deploy3r,
    alpha_token,
    teller,
):
    burner = _gas_source(
        has_feed=True,
        has_feed_iterations=1_000_000,
        exhaust_has_feed=True,
    )
    healthy = _raw_source(EIGHTEEN_DECIMALS, has_feed=True)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [burner, healthy])

    assert desk.addPriceSnapshot(
        alpha_token,
        sender=teller.address,
        gas=700_000,
    )
    assert healthy.snapshotCount() == 1


def test_final_snapshot_wins_behind_nine_snapshot_allowance_exhausting_sources(
    ripe_hq,
    deploy3r,
    alpha_token,
    teller,
):
    burners = [
        _gas_source(
            has_feed=True,
            has_feed_iterations=500,
            snapshot_iterations=1_000_000,
            exhaust_snapshot=True,
        )
        for _ in range(9)
    ]
    healthy = _raw_source(EIGHTEEN_DECIMALS, has_feed=True)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [*burners, healthy])

    assert desk.numAddrs() - 1 == 10
    assert desk.addPriceSnapshot(
        alpha_token,
        sender=teller.address,
        gas=3_000_000,
    )
    gas_used = desk._computation.get_gas_used()
    print(
        "PRICEDESK_SNAPSHOT_STRESS_BOUNDARY",
        f"ten_source_final_position={gas_used}",
        "outer_limit=3000000",
    )
    assert gas_used > 9 * 150_000
    assert gas_used < 3_000_000
    assert healthy.snapshotCount() == 1


@pytest.mark.parametrize("mode", (1, 5), ids=("revert", "noncanonical_bool"))
def test_snapshot_skips_failed_has_feed_query_and_reaches_healthy_source(
    mode,
    ripe_hq,
    deploy3r,
    alpha_token,
    teller,
):
    failed = _raw_source(has_feed=True, has_feed_mode=mode)
    healthy = _raw_source(has_feed=True)
    desk = _isolated_price_desk(ripe_hq, deploy3r, [failed, healthy])

    assert desk.addPriceSnapshot(alpha_token, sender=teller.address)
    assert failed.snapshotCount() == 0
    assert healthy.snapshotCount() == 1


def test_failed_snapshot_source_no_longer_blocks_teller_deposit(
    price_desk,
    governance,
    alpha_token,
    alpha_token_whale,
    bob,
    simple_erc20_vault,
    teller,
    setGeneralConfig,
    setAssetConfig,
):
    failed = _raw_source(
        EIGHTEEN_DECIMALS,
        has_feed=True,
        snapshot_mode=1,
    )
    healthy = _raw_source(EIGHTEEN_DECIMALS, has_feed=True)
    _register_sources(price_desk, governance, [failed, healthy])

    setGeneralConfig()
    setAssetConfig(alpha_token)
    amount = 10 * EIGHTEEN_DECIMALS
    alpha_token.transfer(bob, amount, sender=alpha_token_whale)
    alpha_token.approve(teller, amount, sender=bob)

    assert teller.deposit(
        alpha_token,
        amount,
        bob,
        simple_erc20_vault,
        sender=bob,
    ) == amount
    assert failed.snapshotCount() == 0
    assert healthy.snapshotCount() == 1


def test_healthy_fallback_restores_strict_credit_engine_repay(
    price_desk,
    governance,
    alpha_token,
    alpha_token_whale,
    bob,
    mission_control,
    switchboard_alpha,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    performDeposit,
    mock_price_source,
    teller,
    green_token,
    ledger,
):
    failed = _raw_source(has_feed=True, price_mode=1)
    failed_id = _register_sources(price_desk, governance, [failed])[0]
    healthy_id = price_desk.getRegId(mock_price_source)
    assert healthy_id != 0
    _set_priorities(mission_control, switchboard_alpha, [failed_id, healthy_id])

    setGeneralConfig()
    setAssetConfig(alpha_token)
    setGeneralDebtConfig()
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    performDeposit(
        bob,
        100 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
    )
    borrowed = teller.borrow(40 * EIGHTEEN_DECIMALS, bob, False, sender=bob)

    repay_amount = 10 * EIGHTEEN_DECIMALS
    green_token.approve(teller, repay_amount, sender=bob)
    assert teller.repay(repay_amount, bob, False, False, sender=bob)
    assert ledger.userDebt(bob).amount == borrowed - repay_amount


@pytest.mark.parametrize(
    "primary_failure",
    (
        pytest.param("zero", id="zero-primary"),
        pytest.param("revert", id="reverting-primary"),
    ),
)
def test_healthy_fallback_permits_complete_credit_redemption_terms(
    primary_failure,
    price_desk,
    governance,
    alpha_token,
    alpha_token_whale,
    bob,
    alice,
    mission_control,
    switchboard_alpha,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    green_token,
    whale,
    credit_engine,
    ledger,
    simple_erc20_vault,
    vault_book,
):
    """A healthy fallback keeps the non-strict preflight complete."""
    if primary_failure == "zero":
        failed = _raw_source(has_feed=True)
    else:
        failed = _raw_source(has_feed=True, price_mode=1)
    failed_id = _register_sources(price_desk, governance, [failed])[0]
    healthy_id = price_desk.getRegId(mock_price_source)
    assert healthy_id != 0
    _set_priorities(mission_control, switchboard_alpha, [failed_id, healthy_id])

    setGeneralConfig()
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=70_00,
        _liqThreshold=80_00,
        _borrowRate=0,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    performDeposit(
        bob,
        200 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
    )
    debt = teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    mock_price_source.setPrice(alpha_token, 70 * EIGHTEEN_DECIMALS // 100)

    borrower_terms = credit_engine.getUserBorrowTermsWithNumVaults(
        bob,
        ledger.numUserVaults(bob),
        False,
    )
    assert borrower_terms.collateralVal == 140 * EIGHTEEN_DECIMALS
    assert not borrower_terms.hasQuarantinedAsset
    assert credit_engine.canRedeemUserCollateral(bob)

    payment = 30 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, payment, sender=whale)
    green_token.approve(teller, payment, sender=alice)
    vault_id = vault_book.getRegId(simple_erc20_vault)

    spent = redeem_collateral(
        teller,
        bob,
        vault_id,
        alpha_token,
        payment,
        sender=alice,
    )

    assert spent == payment
    assert credit_engine.getUserDebtAmount(bob) == debt - payment
    logs = filter_logs(teller, "CollateralRedeemed")
    assert len(logs) == 1
    assert logs[0].user == bob
    assert logs[0].asset == alpha_token.address
    assert logs[0].repayValue == payment


# These two cross-module characterizations stay beside the PriceDesk isolation
# matrix because source-failure policy is their trigger. CreditEngine and
# CreditRedeem modules retain their ordinary health/redemption coverage.
def test_full_source_outage_marks_terms_unsafe_and_execution_fails_closed(
    price_desk,
    alpha_token,
    alpha_token_whale,
    bob,
    sally,
    mission_control,
    switchboard_alpha,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    ledger,
):
    """An outage is quarantined in views while strict liquidation fails closed."""
    source_id = price_desk.getRegId(mock_price_source)
    assert source_id != 0
    _set_priorities(mission_control, switchboard_alpha, [source_id])

    setGeneralConfig()
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=70_00,
        _liqThreshold=80_00,
        _borrowRate=0,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setGeneralDebtConfig()
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    performDeposit(
        bob,
        200 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
    )
    teller.borrow(100 * EIGHTEEN_DECIMALS, bob, False, sender=bob)
    assert not credit_engine.canLiquidateUser(bob)

    debt_before = ledger.userDebt(bob)
    mock_price_source.setShouldRevert(alpha_token, True)
    terms = credit_engine.getUserBorrowTerms(bob, False)
    assert terms.hasQuarantinedAsset
    assert not credit_engine.canLiquidateUser(bob)
    with boa.reverts("has price config, no price"):
        teller.liquidateUser(bob, False, sender=sally)
    assert ledger.userDebt(bob) == debt_before


def test_partial_source_outage_marks_terms_unsafe_and_empty_batch_rolls_back(
    price_desk,
    alpha_token,
    alpha_token_whale,
    bravo_token,
    bravo_token_whale,
    bob,
    alice,
    mission_control,
    switchboard_alpha,
    setGeneralConfig,
    setAssetConfig,
    setGeneralDebtConfig,
    createDebtTerms,
    performDeposit,
    mock_price_source,
    teller,
    credit_engine,
    credit_redeem,
    green_token,
    whale,
    simple_erc20_vault,
    vault_book,
):
    """A partial outage is quarantined; redemption skips and rolls back."""
    source_id = price_desk.getRegId(mock_price_source)
    assert source_id != 0
    _set_priorities(mission_control, switchboard_alpha, [source_id])

    setGeneralConfig()
    debt_terms = createDebtTerms(
        _ltv=50_00,
        _redemptionThreshold=70_00,
        _liqThreshold=80_00,
        _borrowRate=0,
    )
    setAssetConfig(alpha_token, _debtTerms=debt_terms)
    setAssetConfig(bravo_token, _debtTerms=debt_terms)
    setGeneralDebtConfig(_ltvPaybackBuffer=0)
    mock_price_source.setPrice(alpha_token, EIGHTEEN_DECIMALS)
    mock_price_source.setPrice(bravo_token, EIGHTEEN_DECIMALS)
    performDeposit(
        bob,
        100 * EIGHTEEN_DECIMALS,
        alpha_token,
        alpha_token_whale,
    )
    performDeposit(
        bob,
        100 * EIGHTEEN_DECIMALS,
        bravo_token,
        bravo_token_whale,
    )
    debt_before = teller.borrow(
        100 * EIGHTEEN_DECIMALS,
        bob,
        False,
        sender=bob,
    )
    assert not credit_engine.canRedeemUserCollateral(bob)

    mock_price_source.setShouldRevert(bravo_token, True)
    terms = credit_engine.getUserBorrowTerms(bob, False)
    assert terms.collateralVal == 100 * EIGHTEEN_DECIMALS
    assert terms.hasQuarantinedAsset
    assert not credit_engine.canRedeemUserCollateral(bob)
    assert credit_redeem.getMaxRedeemValue(bob) == 0

    payment = 30 * EIGHTEEN_DECIMALS
    green_token.transfer(alice, payment, sender=whale)
    green_token.approve(teller, payment, sender=alice)
    vault_id = vault_book.getRegId(simple_erc20_vault)
    before = (
        green_token.balanceOf(alice),
        green_token.allowance(alice, teller),
        green_token.balanceOf(credit_redeem),
        credit_engine.getUserDebtAmount(bob),
        alpha_token.balanceOf(alice),
        simple_erc20_vault.getTotalAmountForUser(bob, alpha_token),
        bravo_token.balanceOf(alice),
        simple_erc20_vault.getTotalAmountForUser(bob, bravo_token),
    )
    assert filter_logs(teller, "CollateralRedeemed") == []
    with boa.reverts("no redemptions occurred"):
        redeem_collateral(
            teller,
            bob,
            vault_id,
            alpha_token,
            payment,
            sender=alice,
        )
    assert (
        green_token.balanceOf(alice),
        green_token.allowance(alice, teller),
        green_token.balanceOf(credit_redeem),
        credit_engine.getUserDebtAmount(bob),
        alpha_token.balanceOf(alice),
        simple_erc20_vault.getTotalAmountForUser(bob, alpha_token),
        bravo_token.balanceOf(alice),
        simple_erc20_vault.getTotalAmountForUser(bob, bravo_token),
    ) == before
    assert filter_logs(teller, "CollateralRedeemed") == []
