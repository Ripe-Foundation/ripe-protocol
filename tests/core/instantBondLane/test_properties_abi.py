import json
import os
import re
from pathlib import Path

import boa
import pytest
from boa.contracts.event_decoder import RawLogEntry
from eth_utils import keccak
from hypothesis import HealthCheck, given, settings, strategies as st
from vyper.compiler.output import build_abi_output

from constants import MAX_UINT256, ZERO_ADDRESS
from tests.core.instantBondLane.conftest import config_dict, make_config


EIP170_LIMIT = 24_576
ENGINE_PATH = "contracts/core/RipeReserveEngine.vy"
VESTING_PATH = "contracts/core/RipeReserveVesting.vy"
FOXTROT_PATH = "contracts/config/SwitchboardFoxtrot.vy"


def contract_abi(contract_path):
    return build_abi_output(boa.load_partial(contract_path).compiler_data)


def event_abi(contract_path, event_name):
    return next(
        item
        for item in contract_abi(contract_path)
        if item.get("type") == "event" and item.get("name") == event_name
    )


def indexed_fields(event):
    return [item["name"] for item in event["inputs"] if item["indexed"]]


def event_topic(contract_path, event_name):
    event = event_abi(contract_path, event_name)
    signature = f"{event_name}({','.join(item['type'] for item in event['inputs'])})"
    return int.from_bytes(keccak(text=signature), "big")


def extract_struct(path, name):
    source = Path(path).read_text()
    match = re.search(rf"^struct {name}:\n(?P<body>(?:    .+\n)+)", source, re.MULTILINE)
    assert match is not None
    return match.group("body")


def reference_controller_rate(
    rate,
    accepted,
    cap,
    elapsed,
    config,
    weighted_lateness=0,
    timing_eligible=True,
):
    values = config_dict(config)
    ceiling = values["maxAllInPayoutRate"] * 10_000 // (
        10_000 + values["maxVestingBonus"]
    )
    rate = min(rate, ceiling)
    utilization = accepted * 10_000 // cap

    if utilization >= values["uHighBps"]:
        strength = (
            (utilization - values["uHighBps"])
            * 10_000
            // (10_000 - values["uHighBps"])
        )
        earliness = 0
        if timing_eligible:
            earliness = 10_000 - weighted_lateness // accepted
        demand = strength * earliness // 10_000
        step = values["minUpBps"] + (
            values["maxUpBps"] - values["minUpBps"]
        ) * demand // 10_000
        rate = max(rate * 10_000 // (10_000 + step), 10_000)
    elif utilization <= values["uLowBps"]:
        weakness = (
            (values["uLowBps"] - utilization)
            * 10_000
            // values["uLowBps"]
        )
        step = values["minDownBps"] + (
            values["maxDownBps"] - values["minDownBps"]
        ) * weakness // 10_000
        rate = min(rate * 10_000 // (10_000 - step), ceiling)

    decay_steps = min(elapsed - 1, values["maxDecayEpochs"])
    for _ in range(decay_steps):
        rate = min(
            rate * 10_000 // (10_000 - values["decayBps"]),
            ceiling,
        )
    return rate, utilization, decay_steps


@pytest.mark.artifact
def test_runtime_sizes_have_eip170_headroom(lane_env, ripe_hq):
    foxtrot = boa.load(FOXTROT_PATH, ripe_hq, ZERO_ADDRESS, 2, 20)
    sizes = {
        "ripe_reserve_engine": len(boa.env.get_code(lane_env.lane.address)),
        "ripe_reserve_vesting": len(boa.env.get_code(lane_env.claims.address)),
        "switchboard_foxtrot": len(boa.env.get_code(foxtrot.address)),
    }
    assert all(0 < size < EIP170_LIMIT for size in sizes.values()), sizes
    print("deployed runtime sizes: " + json.dumps(sizes, sort_keys=True))

    report_path = os.environ.get("INSTANT_BOND_SIZE_REPORT")
    if report_path:
        payload = {**sizes, "eip170_ceiling": EIP170_LIMIT}
        Path(report_path).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


@pytest.mark.artifact
def test_purchase_and_claim_gas_benchmarks_are_reported(lane_env):
    lane_env.set_config(
        maxVestingBonus=0,
        minVestingLength=1,
        maxVestingLength=1,
    )
    gas = {}
    lane_env.buy(lane_env.scale)
    gas["purchase_initialize"] = lane_env.lane._computation.get_gas_used()
    lane_env.buy(lane_env.scale)
    gas["purchase_same_epoch"] = lane_env.lane._computation.get_gas_used()
    boa.env.time_travel(blocks=lane_env.epoch_length)
    lane_env.buy(lane_env.scale)
    gas["purchase_rollover"] = lane_env.lane._computation.get_gas_used()
    lane_env.set_rate_override(9 * 10**17, 0)
    boa.env.time_travel(blocks=lane_env.epoch_length)
    lane_env.buy(lane_env.scale)
    gas["purchase_override"] = lane_env.lane._computation.get_gas_used()
    boa.env.time_travel(blocks=1)
    lane_env.claim(1)
    gas["claim_direct"] = lane_env.lane._computation.get_gas_used()

    assert all(value > 0 for value in gas.values())
    print("ripe reserve engine gas: " + json.dumps(gas, sort_keys=True))
    report_path = os.environ.get("INSTANT_BOND_GAS_REPORT")
    if report_path:
        Path(report_path).write_text(json.dumps(gas, indent=2, sort_keys=True) + "\n")


@pytest.mark.artifact
def test_engine_event_abi_names_order_and_indexing():
    expected = {
        "EpochInitialized": (
            [
                "epoch",
                "controllerBasePayoutRate",
                "basePayoutRate",
                "rateSource",
                "paymentCap",
                "minPaymentAmount",
                "maxVestingBonus",
                "minVestingLength",
                "maxVestingLength",
                "timingEligible",
            ],
            ["epoch"],
        ),
        "EpochRolled": (
            [
                "fromEpoch",
                "toEpoch",
                "oldBasePayoutRate",
                "controllerBasePayoutRate",
                "newBasePayoutRate",
                "rateSource",
                "newPaymentCap",
                "newMinPaymentAmount",
                "newMaxVestingBonus",
                "newMinVestingLength",
                "newMaxVestingLength",
                "previousAcceptedPayment",
                "previousPaymentCap",
                "previousWeightedLateness",
                "previousTimingEligible",
                "utilizationBps",
                "effectiveAdjustmentBps",
                "decaySteps",
            ],
            ["fromEpoch", "toEpoch"],
        ),
        "RipeAllocated": (
            [
                "acquirer",
                "positionId",
                "paymentAmount",
                "baseRipe",
                "bonusRipe",
                "bonusRatio",
                "vestingLength",
                "creationBlock",
                "claimStartBlock",
                "maturityBlock",
                "totalRipe",
                "controllerBasePayoutRate",
                "basePayoutRate",
                "rateSource",
                "epoch",
            ],
            ["acquirer", "positionId", "epoch"],
        ),
        "VestedRipeClaimed": (
            [
                "beneficiary",
                "positionId",
                "amountClaimed",
                "totalClaimedForPosition",
                "ripeAllocation",
                "autoDeposited",
                "lockDuration",
            ],
            ["beneficiary", "positionId"],
        ),
        "RateOverrideInstalled": (
            ["targetEpoch", "targetBasePayoutRate"],
            ["targetEpoch"],
        ),
        "RateOverrideApplied": (
            [
                "fromEpoch",
                "toEpoch",
                "targetBasePayoutRate",
                "controllerBasePayoutRate",
            ],
            ["fromEpoch", "toEpoch"],
        ),
        "RateOverrideMissed": (
            [
                "targetEpoch",
                "committedEpoch",
                "targetBasePayoutRate",
                "controllerBasePayoutRate",
            ],
            ["targetEpoch", "committedEpoch"],
        ),
        "RateOverrideCancelled": (
            ["targetEpoch", "targetBasePayoutRate"],
            ["targetEpoch"],
        ),
        "RateOverrideInvalidated": (
            ["targetEpoch", "targetBasePayoutRate"],
            ["targetEpoch"],
        ),
    }
    for event_name, (names, indexed) in expected.items():
        event = event_abi(ENGINE_PATH, event_name)
        assert [item["name"] for item in event["inputs"]] == names
        assert indexed_fields(event) == indexed


@pytest.mark.artifact
def test_vesting_event_abi_names_order_and_indexing():
    expected = {
        "VestingPositionCreated": (
            [
                "user",
                "positionId",
                "sourceEngine",
                "ripeAllocation",
                "creationBlock",
                "claimStartBlock",
                "maturityBlock",
            ],
            ["user", "positionId", "sourceEngine"],
        ),
        "ClaimRecorded": (
            [
                "user",
                "positionId",
                "amountClaimed",
                "totalClaimedForPosition",
                "ripeAllocation",
                "fullyClaimed",
            ],
            ["user", "positionId"],
        ),
        "RemainingAllocationBudgetSet": (["amount"], []),
    }
    for event_name, (names, indexed) in expected.items():
        event = event_abi(VESTING_PATH, event_name)
        assert [item["name"] for item in event["inputs"]] == names
        assert indexed_fields(event) == indexed


@pytest.mark.artifact
def test_engine_and_vesting_function_abi_is_explicit():
    lane_abi = contract_abi(ENGINE_PATH)
    functions = {
        item["name"]: item
        for item in lane_abi
        if item.get("type") == "function"
    }
    assert [item["name"] for item in functions["acquireRipe"]["inputs"]] == [
        "_paymentAmount",
        "_requestedVestingLength",
        "_expectedVestingLength",
        "_expectedEpoch",
        "_minRipeOut",
        "_deadlineBlock",
    ]
    assert [item["name"] for item in functions["setRateOverride"]["inputs"]] == [
        "_targetBasePayoutRate",
        "_targetEpoch",
    ]
    assert [item["name"] for item in functions["claimVestedRipe"]["inputs"]] == [
        "_positionId",
        "_autoDeposit",
        "_lockDuration",
    ]
    assert [item["name"] for item in functions["claimVestedRipeMany"]["inputs"]] == [
        "_positionIds",
        "_autoDeposit",
        "_lockDuration",
    ]
    assert "paymentDecimals" not in functions
    assert "cumulativeMinted" not in functions
    assert "setCumulativeMinted" not in functions

    quote_components = functions["previewAcquireRipe"]["outputs"][0]["components"]
    assert [component["name"] for component in quote_components] == [
        "available",
        "epoch",
        "controllerBasePayoutRate",
        "basePayoutRate",
        "rateSource",
        "remainingPayment",
        "minPaymentAmount",
        "budgetRemaining",
        "baseRipe",
        "bonusRatio",
        "bonusRipe",
        "vestingLength",
        "creationBlock",
        "claimStartBlock",
        "maturityBlock",
        "totalRipe",
    ]

    claims_abi = contract_abi(VESTING_PATH)
    claim_functions = {
        item["name"]: item
        for item in claims_abi
        if item.get("type") == "function"
    }
    assert [item["name"] for item in claim_functions["createVestingPosition"]["inputs"]] == [
        "_user",
        "_ripeAllocation",
        "_vestingLength",
        "_minVestingLength",
    ]
    assert [item["name"] for item in claim_functions["recordClaim"]["inputs"]] == [
        "_user",
        "_positionId",
    ]


@pytest.mark.artifact
def test_reserve_engine_config_structs_are_identical():
    assert extract_struct(ENGINE_PATH, "ReserveEngineConfig") == extract_struct(
        FOXTROT_PATH,
        "ReserveEngineConfig",
    )


@pytest.mark.artifact
def test_indexed_epoch_and_position_topics_filter_raw_logs(lane_env):
    initialized_topic = event_topic(ENGINE_PATH, "EpochInitialized")
    rolled_topic = event_topic(ENGINE_PATH, "EpochRolled")
    purchased_topic = event_topic(ENGINE_PATH, "RipeAllocated")
    buyer_topic = int(str(lane_env.bob), 16)

    lane_env.buy(lane_env.scale)
    raw_logs = [
        RawLogEntry(*entry)
        for entry in lane_env.lane._computation.get_raw_log_entries()
    ]
    assert any(list(log.topics) == [initialized_topic, 0] for log in raw_logs)
    assert any(
        list(log.topics) == [purchased_topic, buyer_topic, 1, 0]
        for log in raw_logs
    )

    boa.env.time_travel(blocks=lane_env.epoch_length)
    lane_env.buy(lane_env.scale)
    raw_logs = [
        RawLogEntry(*entry)
        for entry in lane_env.lane._computation.get_raw_log_entries()
    ]
    assert any(list(log.topics) == [rolled_topic, 0, 1] for log in raw_logs)
    assert any(
        list(log.topics) == [purchased_topic, buyer_topic, 2, 1]
        for log in raw_logs
    )


@given(
    data=st.data(),
    seed_rate=st.integers(min_value=10_000, max_value=10**24),
    ceiling_multiplier=st.integers(min_value=1, max_value=20),
    cap_units=st.integers(min_value=2, max_value=1_000),
    u_low=st.integers(min_value=1, max_value=4_999),
    min_up_bps=st.integers(min_value=2, max_value=10_000),
    elapsed=st.integers(min_value=1, max_value=1_000),
    max_decay=st.integers(min_value=1, max_value=32),
)
@settings(
    max_examples=75,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@pytest.mark.fuzz
def test_randomized_controller_matches_reference(
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
    decay_bps = data.draw(
        st.integers(min_value=max_down_bps, max_value=max_down_limit)
    )
    accepted_units = data.draw(st.integers(min_value=1, max_value=cap_units))

    with boa.env.anchor():
        cap = cap_units * lane_env.scale
        accepted = accepted_units * lane_env.scale
        lane_env.set_budget(MAX_UINT256)
        config = lane_env.set_config(
            paymentCapPerEpoch=cap,
            minPaymentAmount=lane_env.scale,
            maxAllInPayoutRate=seed_rate * ceiling_multiplier,
            seedBasePayoutRate=seed_rate,
            uHighBps=u_high,
            uLowBps=u_low,
            minUpBps=min_up_bps,
            maxUpBps=max_up_bps,
            minDownBps=min_down_bps,
            maxDownBps=max_down_bps,
            decayBps=decay_bps,
            maxDecayEpochs=max_decay,
            maxVestingBonus=0,
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
        assert quote.basePayoutRate == expected_rate
        assert 0 <= utilization <= 10_000
        assert decay_steps <= 32


@pytest.mark.parametrize("decimals", [0, 6, 18, 27, 73])
def test_worst_case_valid_config_executes_purchase_without_overflow(
    lane_factory,
    charlie_token_whale,
    decimals,
):
    scale = 10**decimals
    cap = scale if decimals == 73 else 1_000 * scale
    token = boa.load(
        "contracts/mock/MockErc20.vy",
        charlie_token_whale,
        "Payment",
        "PAY",
        decimals,
        1_000,
    )
    ctx = lane_factory(
        payment_token=token,
        buyer_funding=cap,
        allocation_budget=MAX_UINT256,
    )
    if decimals == 73:
        max_bonus = 1_000
        max_all_in = 11_000
        seed = 10_000
    else:
        max_bonus = 100_000
        max_all_in = 11 * 10**18
        seed = 10**18
    max_vesting_length = max_bonus // 10_000 + 2
    ctx.set_config(
        paymentCapPerEpoch=cap,
        minPaymentAmount=scale,
        maxAllInPayoutRate=max_all_in,
        seedBasePayoutRate=seed,
        maxDecayEpochs=32,
        maxVestingBonus=max_bonus,
        minVestingLength=1,
        maxVestingLength=max_vesting_length,
    )
    quote = ctx.quote(cap, max_vesting_length)
    ripe_supply_before = ctx.ripe_token.totalSupply()
    payout = ctx.buy(
        cap,
        requested_vesting=max_vesting_length,
        min_ripe_out=quote.totalRipe,
    )
    assert payout == quote.totalRipe
    assert quote.bonusRatio == max_bonus
    assert quote.totalRipe * scale <= cap * max_all_in
    assert ctx.claims.totalAllocatedRipe() == payout
    assert ctx.ripe_token.totalSupply() == ripe_supply_before
    assert ctx.payment_token.balanceOf(ctx.endaoment_funds) == cap


@given(
    decimals=st.sampled_from((0, 1, 2, 6, 8, 18, 27, 36, 54, 73)),
    cap_units=st.integers(min_value=1, max_value=1_000),
    max_bonus=st.integers(min_value=0, max_value=100_000),
    target_ceiling=st.integers(min_value=10_000, max_value=10**20),
)
@settings(max_examples=40, deadline=None)
@pytest.mark.fuzz
def test_fuzz_payout_respects_all_in_ceiling(
    ripe_hq,
    governance,
    switchboard_alpha,
    decimals,
    cap_units,
    max_bonus,
    target_ceiling,
):
    with boa.env.anchor():
        token = boa.load(
            "contracts/mock/MockErc20.vy",
            governance,
            "Payment",
            "PAY",
            decimals,
            0,
        )
        scale = 10**decimals
        if decimals == 73:
            cap = scale
            max_bonus = 0
            max_all_in = 10_000
        else:
            units = 1 if decimals >= 54 else cap_units
            cap = units * scale
            max_all_in = (
                target_ceiling * (10_000 + max_bonus) + 9_999
            ) // 10_000
        derived_ceiling = max_all_in * 10_000 // (10_000 + max_bonus)
        max_vesting_length = max_bonus // 10_000 + 2
        config = make_config(
            scale,
            paymentCapPerEpoch=cap,
            minPaymentAmount=scale,
            maxAllInPayoutRate=max_all_in,
            seedBasePayoutRate=derived_ceiling,
            maxDecayEpochs=32,
            maxVestingBonus=max_bonus,
            minVestingLength=1,
            maxVestingLength=max_vesting_length,
        )
        lane = boa.load(ENGINE_PATH, ripe_hq, token, config)
        lane.start(0, config[-1], sender=switchboard_alpha.address)
        quote = lane.previewAcquireRipe(cap, max_vesting_length)
        assert quote.basePayoutRate == derived_ceiling
        assert quote.baseRipe == cap * derived_ceiling // scale
        assert quote.bonusRatio == max_bonus
        assert quote.bonusRipe == quote.baseRipe * max_bonus // 10_000
        assert quote.totalRipe * scale <= cap * max_all_in
