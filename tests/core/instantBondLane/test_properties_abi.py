import re
from pathlib import Path

import boa
import pytest
from boa.contracts.event_decoder import RawLogEntry
from eth_utils import keccak
from hypothesis import HealthCheck, given, settings, strategies as st
from vyper.compiler.output import build_abi_output

from constants import ZERO_ADDRESS


EIP170_LIMIT = 24_576
LANE_RUNTIME_MAX = 11_000
FOXTROT_RUNTIME_MAX = 6_500
MAX_UINT256 = 2**256 - 1


def event_abi(contract_path, event_name):
    compiler_data = boa.load_partial(contract_path).compiler_data
    return next(
        item
        for item in build_abi_output(compiler_data)
        if item.get("type") == "event" and item.get("name") == event_name
    )


def indexed_fields(event):
    return [item["name"] for item in event["inputs"] if item["indexed"]]


def event_topic(contract_path, event_name):
    event = event_abi(contract_path, event_name)
    signature = f"{event_name}({','.join(item['type'] for item in event['inputs'])})"
    return int.from_bytes(keccak(text=signature), "big")


def reference_controller_rate(
    rate,
    accepted,
    cap,
    elapsed,
    config,
    weighted_lateness=0,
    timing_eligible=True,
):
    ceiling = config[4] * 10_000 // (10_000 + config[14])
    rate = min(rate, ceiling)
    utilization = accepted * 10_000 // cap

    if utilization >= config[6]:
        utilization_strength = (
            (utilization - config[6]) * 10_000 // (10_000 - config[6])
        )
        earliness = 0
        if timing_eligible:
            earliness = 10_000 - weighted_lateness // accepted
        demand_strength = utilization_strength * earliness // 10_000
        step = config[8] + (config[9] - config[8]) * demand_strength // 10_000
        rate = max(rate * 10_000 // (10_000 + step), 10_000)
    elif utilization <= config[7]:
        weakness = (config[7] - utilization) * 10_000 // config[7]
        step = config[10] + (config[11] - config[10]) * weakness // 10_000
        rate = min(rate * 10_000 // (10_000 - step), ceiling)

    decay_steps = min(elapsed - 1, config[13])
    for _ in range(decay_steps):
        rate = min(rate * 10_000 // (10_000 - config[12]), ceiling)
    return rate, utilization, decay_steps


def extract_struct(path, name):
    source = Path(path).read_text()
    match = re.search(rf"^struct {name}:\n(?P<body>(?:    .+\n)+)", source, re.MULTILINE)
    assert match is not None
    return match.group("body")


def test_runtime_sizes_have_large_eip170_headroom(lane_env, ripe_hq):
    foxtrot = boa.load(
        "contracts/config/SwitchboardFoxtrot.vy",
        ripe_hq,
        ZERO_ADDRESS,
        2,
        20,
        lane_env.lane,
    )
    lane_size = len(boa.env.get_code(lane_env.lane.address))
    foxtrot_size = len(boa.env.get_code(foxtrot.address))

    assert 0 < lane_size < EIP170_LIMIT
    assert 0 < foxtrot_size < EIP170_LIMIT
    size_report = f"deployed runtime sizes: lane={lane_size}, foxtrot={foxtrot_size}"
    assert lane_size <= LANE_RUNTIME_MAX, size_report
    assert foxtrot_size <= FOXTROT_RUNTIME_MAX, size_report


def test_event_abi_names_order_and_indexing():
    path = "contracts/core/InstantBondLane.vy"
    initialized = event_abi(path, "EpochInitialized")
    rolled = event_abi(path, "EpochRolled")
    purchased = event_abi(path, "InstantBondPurchased")

    assert [item["name"] for item in initialized["inputs"]] == [
        "epoch",
        "rate",
        "paymentCap",
        "minPaymentAmount",
        "maxLockBonus",
        "timingEligible",
        "pricingConfigVersion",
    ]
    assert indexed_fields(initialized) == ["epoch", "pricingConfigVersion"]

    assert [item["name"] for item in rolled["inputs"]] == [
        "fromEpoch",
        "toEpoch",
        "oldRate",
        "newRate",
        "newPaymentCap",
        "newMinPaymentAmount",
        "newMaxLockBonus",
        "previousAcceptedPayment",
        "previousPaymentCap",
        "previousWeightedLateness",
        "previousTimingEligible",
        "utilizationBps",
        "effectiveAdjustmentBps",
        "decaySteps",
        "controllerRate",
        "pricingConfigVersion",
    ]
    assert indexed_fields(rolled) == [
        "fromEpoch",
        "toEpoch",
        "pricingConfigVersion",
    ]

    assert [item["name"] for item in purchased["inputs"]] == [
        "buyer",
        "paymentAmount",
        "baseRipe",
        "bonusRipe",
        "bonusRatio",
        "actualLock",
        "totalRipe",
        "epochRate",
        "epoch",
        "pricingConfigVersion",
        "liveConfigVersion",
        "ripeGovVaultId",
    ]
    assert indexed_fields(purchased) == [
        "buyer",
        "epoch",
        "pricingConfigVersion",
    ]

    override_events = {
        name: event_abi(path, name)
        for name in (
            "RateOverrideInstalled",
            "RateOverrideApplied",
            "RateOverrideCancelled",
            "RateOverrideInvalidated",
        )
    }
    assert [item["name"] for item in override_events["RateOverrideInstalled"]["inputs"]] == [
        "newVersion",
        "targetRate",
        "boundConfigVersion",
    ]
    assert indexed_fields(override_events["RateOverrideInstalled"]) == [
        "newVersion",
        "boundConfigVersion",
    ]
    assert [item["name"] for item in override_events["RateOverrideApplied"]["inputs"]] == [
        "newVersion",
        "fromEpoch",
        "toEpoch",
        "targetRate",
        "controllerRate",
    ]
    assert indexed_fields(override_events["RateOverrideApplied"]) == [
        "newVersion",
        "fromEpoch",
        "toEpoch",
    ]
    assert [item["name"] for item in override_events["RateOverrideCancelled"]["inputs"]] == [
        "newVersion",
        "targetRate",
    ]
    assert indexed_fields(override_events["RateOverrideCancelled"]) == ["newVersion"]
    assert [item["name"] for item in override_events["RateOverrideInvalidated"]["inputs"]] == [
        "newVersion",
        "targetRate",
        "newConfigVersion",
    ]
    assert indexed_fields(override_events["RateOverrideInvalidated"]) == [
        "newVersion",
        "newConfigVersion",
    ]


def test_instant_bond_config_struct_bodies_are_byte_for_byte_identical():
    lane = extract_struct("contracts/core/InstantBondLane.vy", "InstantBondConfig")
    foxtrot = extract_struct(
        "contracts/config/SwitchboardFoxtrot.vy", "InstantBondConfig"
    )
    assert lane == foxtrot


def test_indexed_epoch_and_pricing_topics_filter_raw_runtime_logs(lane_env):
    path = "contracts/core/InstantBondLane.vy"
    initialized_topic = event_topic(path, "EpochInitialized")
    rolled_topic = event_topic(path, "EpochRolled")
    purchased_topic = event_topic(path, "InstantBondPurchased")
    buyer_topic = int(str(lane_env.bob), 16)

    lane_env.set_config(maxLockBonus=0)
    first = lane_env.quote(lane_env.scale)
    lane_env.buy(
        lane_env.scale,
        expected_epoch=first.epoch,
        min_ripe_out=first.totalRipe,
    )
    raw_logs = [
        RawLogEntry(*entry)
        for entry in lane_env.lane._computation.get_raw_log_entries()
    ]
    assert any(list(log.topics) == [initialized_topic, 0, 1] for log in raw_logs)
    assert any(
        list(log.topics) == [purchased_topic, buyer_topic, 0, 1]
        for log in raw_logs
    )

    lane_env.set_config(maxLockBonus=0)
    boa.env.time_travel(blocks=lane_env.epoch_length)
    second = lane_env.quote(lane_env.scale)
    lane_env.buy(
        lane_env.scale,
        expected_epoch=second.epoch,
        min_ripe_out=second.totalRipe,
    )
    raw_logs = [
        RawLogEntry(*entry)
        for entry in lane_env.lane._computation.get_raw_log_entries()
    ]
    assert any(list(log.topics) == [rolled_topic, 0, 1, 2] for log in raw_logs)
    assert any(
        list(log.topics) == [purchased_topic, buyer_topic, 1, 2]
        for log in raw_logs
    )


@given(
    data=st.data(),
    seed_rate=st.integers(min_value=10_000, max_value=10**24),
    ceiling_multiplier=st.integers(min_value=1, max_value=20),
    cap_units=st.integers(min_value=2, max_value=1_000),
    u_low=st.integers(min_value=1, max_value=4_999),
    min_up_bps=st.integers(min_value=2, max_value=10_000),
    elapsed=st.integers(min_value=1, max_value=1_000_000),
    max_decay=st.integers(min_value=1, max_value=32),
)
@settings(
    max_examples=250,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_randomized_controller_matches_contract(
    lane_env,
    data,
    seed_rate,
    ceiling_multiplier,
    cap_units,
    u_low,
    min_up_bps,
    elapsed,
    max_decay,
):
    u_high = data.draw(st.integers(min_value=u_low + 1, max_value=9_999))
    max_up_bps = data.draw(st.integers(min_value=min_up_bps, max_value=10_000))
    max_down_limit = min(
        min_up_bps - 1,
        10_000 * min_up_bps // (10_000 + min_up_bps),
    )
    max_down_bps = data.draw(st.integers(min_value=1, max_value=max_down_limit))
    min_down_bps = data.draw(st.integers(min_value=1, max_value=max_down_bps))
    decay_bps = data.draw(st.integers(min_value=max_down_bps, max_value=9_999))
    accepted_units = data.draw(st.integers(min_value=1, max_value=cap_units))

    with boa.env.anchor():
        cap = cap_units * lane_env.scale
        accepted = accepted_units * lane_env.scale
        config = lane_env.set_config(
            paymentCapPerEpoch=cap,
            minPaymentAmount=lane_env.scale,
            mintBudget=MAX_UINT256,
            maxEffectiveRate=seed_rate * ceiling_multiplier,
            seedRate=seed_rate,
            uHighBps=u_high,
            uLowBps=u_low,
            minUpBps=min_up_bps,
            maxUpBps=max_up_bps,
            minDownBps=min_down_bps,
            maxDownBps=max_down_bps,
            decayBps=decay_bps,
            maxDecayEpochs=max_decay,
            maxLockBonus=0,
        )
        lane_env.buy(accepted)
        boa.env.time_travel(blocks=elapsed * lane_env.epoch_length)

        quote = lane_env.quote(lane_env.scale)
        expected_rate, utilization, decay_steps = reference_controller_rate(
            seed_rate,
            accepted,
            cap,
            elapsed,
            config,
        )

        assert quote.epoch == elapsed
        assert quote.rate == expected_rate
        assert 0 <= utilization <= 10_000
        assert decay_steps <= 32


def test_worst_case_valid_config_payout_across_decimal_counts(
    ripe_hq,
    governance,
    switchboard_alpha,
    mission_control,
    ripe_token,
):
    with boa.env.anchor():
        mission_control.setRipeGovVaultConfig(
            ripe_token,
            10_000,
            False,
            (1, 2, 20_000, True, 0),
            sender=switchboard_alpha.address,
        )

        for decimals in (0, 1, 2, 6, 8, 18, 27, 73):
            token = boa.load(
                "contracts/mock/MockErc20.vy",
                governance,
                "Payment",
                "PAY",
                decimals,
                0,
            )
            scale = 10**decimals
            lane = boa.load(
                "contracts/core/InstantBondLane.vy",
                ripe_hq,
                token,
                boa.env.evm.patch.block_number,
                100,
            )
            lane.pause(False, sender=switchboard_alpha.address)

            if decimals == 73:
                # At 73 decimals, cap >= PAYMENT_SCALE leaves only ~15.79% rate
                # headroom above MIN_BASE_RATE. This deterministic preview keeps
                # the absolute decimal extreme at its minimum-rate boundary; the
                # executable test below covers the same decimal count with bonus.
                cap = scale
                max_bonus = 0
                max_effective = 10_000
                seed = 10_000
            else:
                cap = 1_000 * scale
                max_bonus = 100_000
                max_effective = 11 * 10**18
                seed = 10**18

            config = (
                True,
                cap,
                scale,
                MAX_UINT256,
                max_effective,
                seed,
                8_000,
                2_000,
                1_000,
                1_000,
                500,
                500,
                1_000,
                32,
                max_bonus,
            )
            assert lane.isValidConfig(config)
            lane.setConfig(config, 0, sender=switchboard_alpha.address)

            quote = lane.previewBuyNow(cap, 2)
            assert quote.baseRipe == cap * seed // scale
            assert quote.bonusRatio == max_bonus
            assert quote.totalRipe == quote.baseRipe + quote.bonusRipe
            assert quote.totalRipe * scale <= cap * max_effective


@pytest.mark.parametrize("decimals", [0, 6, 18, 27, 73])
def test_worst_case_valid_config_executes_purchase(
    lane_factory,
    charlie_token_whale,
    decimals,
):
    scale = 10**decimals
    cap = scale if decimals == 73 else 1_000 * scale
    supply = 1 if decimals == 73 else 1_000
    token = boa.load(
        "contracts/mock/MockErc20.vy",
        charlie_token_whale,
        "Payment",
        "PAY",
        decimals,
        supply,
    )
    ctx = lane_factory(
        payment_token=token,
        buyer_funding=cap,
    )
    ctx.setup_lock_terms(min_lock=1, max_lock=2)

    if decimals == 73:
        max_bonus = 1_000
        max_effective = 11_000
        seed = 10_000
    else:
        max_bonus = 100_000
        max_effective = 11 * 10**18
        seed = 10**18

    ctx.set_config(
        paymentCapPerEpoch=cap,
        minPaymentAmount=scale,
        mintBudget=MAX_UINT256,
        maxEffectiveRate=max_effective,
        seedRate=seed,
        maxDecayEpochs=32,
        maxLockBonus=max_bonus,
    )
    quote = ctx.quote(cap, 2)
    ripe_supply_before = ctx.ripe_token.totalSupply()
    payout = ctx.buy(
        cap,
        requested_lock=2,
        expected_epoch=quote.epoch,
        min_ripe_out=quote.totalRipe,
    )

    assert payout == quote.totalRipe
    assert quote.bonusRatio == max_bonus
    assert quote.totalRipe * scale <= cap * max_effective
    assert ctx.lane.cumulativeMinted() == payout
    assert ctx.ripe_token.totalSupply() == ripe_supply_before + payout
    assert ctx.payment_token.balanceOf(ctx.endaoment_funds) == cap


@given(
    decimals=st.sampled_from((0, 1, 2, 6, 8, 18, 27, 36, 54, 73)),
    cap_units=st.integers(min_value=1, max_value=1_000),
    max_bonus=st.integers(min_value=0, max_value=100_000),
    target_ceiling=st.integers(min_value=10_000, max_value=10**20),
)
@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_fuzz_valid_worst_case_payout_never_overflows_and_respects_floor(
    ripe_hq,
    governance,
    switchboard_alpha,
    mission_control,
    ripe_token,
    decimals,
    cap_units,
    max_bonus,
    target_ceiling,
):
    with boa.env.anchor():
        mission_control.setRipeGovVaultConfig(
            ripe_token,
            10_000,
            False,
            (1, 2, 20_000, True, 0),
            sender=switchboard_alpha.address,
        )
        token = boa.load(
            "contracts/mock/MockErc20.vy",
            governance,
            "Payment",
            "PAY",
            decimals,
            0,
        )
        scale = 10**decimals
        lane = boa.load(
            "contracts/core/InstantBondLane.vy",
            ripe_hq,
            token,
            boa.env.evm.patch.block_number,
            100,
        )

        if decimals == 73:
            # The randomized preview keeps this absolute scale at the conservative
            # zero-bonus boundary; the executable test above covers a nonzero bonus.
            cap = scale
            max_bonus = 0
            max_effective = 10_000
        else:
            units = 1 if decimals >= 54 else cap_units
            cap = units * scale
            max_effective = (
                target_ceiling * (10_000 + max_bonus) + 9_999
            ) // 10_000

        derived_ceiling = max_effective * 10_000 // (10_000 + max_bonus)
        config = (
            True,
            cap,
            scale,
            MAX_UINT256,
            max_effective,
            derived_ceiling,
            8_000,
            2_000,
            1_000,
            1_000,
            500,
            500,
            1_000,
            32,
            max_bonus,
        )
        assert lane.isValidConfig(config)
        lane.setConfig(config, 0, sender=switchboard_alpha.address)

        quote = lane.previewBuyNow(cap, 2)
        assert quote.rate == derived_ceiling
        assert quote.baseRipe == cap * derived_ceiling // scale
        assert quote.bonusRatio == max_bonus
        assert quote.bonusRipe == quote.baseRipe * max_bonus // 10_000
        assert quote.totalRipe == quote.baseRipe + quote.bonusRipe
        assert quote.totalRipe * scale <= cap * max_effective
