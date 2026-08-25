from types import SimpleNamespace

import boa
import pytest

from constants import (
    INSTANT_BOND_CLAIMS_HQ_ID,
    INSTANT_BOND_LANE_HQ_ID,
    MAX_UINT256,
)


HUNDRED_PERCENT = 10_000
DEFAULT_EPOCH_LENGTH = 100
DEFAULT_MIN_VESTING_LENGTH = 100
DEFAULT_MAX_VESTING_LENGTH = 1_000
DEFAULT_ALLOCATION_BUDGET = 1_000_000 * 10**18
MIN_BASE_PAYOUT_RATE = 10_000

CONFIG_KEYS = (
    "paymentCapPerEpoch",
    "minPaymentAmount",
    "maxAllInPayoutRate",
    "seedBasePayoutRate",
    "uHighBps",
    "uLowBps",
    "minUpBps",
    "maxUpBps",
    "minDownBps",
    "maxDownBps",
    "decayBps",
    "maxDecayEpochs",
    "maxVestingBonus",
    "minVestingLength",
    "maxVestingLength",
    "epochLength",
)


def make_config(scale, epoch_length=DEFAULT_EPOCH_LENGTH, **overrides):
    max_safe_scaled = MAX_UINT256 // HUNDRED_PERCENT
    cap = scale if 1_000 * scale > max_safe_scaled else 1_000 * scale
    max_safe_rate = MAX_UINT256 // max(cap, 1)
    values = {
        "paymentCapPerEpoch": cap,
        "minPaymentAmount": scale,
        "maxAllInPayoutRate": (
            2 * 10**18 if 2 * 10**18 <= max_safe_rate else 11_000
        ),
        "seedBasePayoutRate": (
            10**18 if 10**18 <= max_safe_rate else MIN_BASE_PAYOUT_RATE
        ),
        "uHighBps": 8_000,
        "uLowBps": 2_000,
        "minUpBps": 1_000,
        "maxUpBps": 1_000,
        "minDownBps": 500,
        "maxDownBps": 500,
        "decayBps": 900,
        "maxDecayEpochs": 4,
        "maxVestingBonus": 5_000 if 2 * 10**18 <= max_safe_rate else 0,
        "minVestingLength": DEFAULT_MIN_VESTING_LENGTH,
        "maxVestingLength": DEFAULT_MAX_VESTING_LENGTH,
        "epochLength": epoch_length,
    }
    values.update(overrides)
    return tuple(values[key] for key in CONFIG_KEYS)


def config_dict(config):
    return dict(zip(CONFIG_KEYS, config))


def replace_config(config, **overrides):
    values = config_dict(config)
    values.update(overrides)
    return tuple(values[key] for key in CONFIG_KEYS)


def travel_blocks(blocks):
    if blocks > 0:
        boa.env.time_travel(blocks=blocks)


def controller_rate(
    rate,
    accepted,
    cap,
    elapsed,
    config,
    weighted_lateness=0,
    timing_eligible=True,
):
    values = config_dict(config)
    ceiling = values["maxAllInPayoutRate"] * HUNDRED_PERCENT // (
        HUNDRED_PERCENT + values["maxVestingBonus"]
    )
    rate = min(rate, ceiling)
    utilization = 0
    adjustment = 0
    decay_steps = 0

    if accepted == 0:
        decay_steps = min(elapsed, values["maxDecayEpochs"])
    else:
        utilization = accepted * HUNDRED_PERCENT // cap
        if utilization >= values["uHighBps"]:
            strength = (
                (utilization - values["uHighBps"])
                * HUNDRED_PERCENT
                // (HUNDRED_PERCENT - values["uHighBps"])
            )
            earliness = 0
            if timing_eligible:
                earliness = HUNDRED_PERCENT - weighted_lateness // accepted
            demand = strength * earliness // HUNDRED_PERCENT
            adjustment = values["minUpBps"] + (
                values["maxUpBps"] - values["minUpBps"]
            ) * demand // HUNDRED_PERCENT
            rate = max(
                rate * HUNDRED_PERCENT // (HUNDRED_PERCENT + adjustment),
                MIN_BASE_PAYOUT_RATE,
            )
        elif utilization <= values["uLowBps"]:
            weakness = (
                (values["uLowBps"] - utilization)
                * HUNDRED_PERCENT
                // values["uLowBps"]
            )
            adjustment = values["minDownBps"] + (
                values["maxDownBps"] - values["minDownBps"]
            ) * weakness // HUNDRED_PERCENT
            rate = min(
                rate * HUNDRED_PERCENT // (HUNDRED_PERCENT - adjustment),
                ceiling,
            )
        decay_steps = min(elapsed - 1, values["maxDecayEpochs"])

    for _ in range(decay_steps):
        rate = min(
            rate * HUNDRED_PERCENT // (HUNDRED_PERCENT - values["decayBps"]),
            ceiling,
        )
    return rate, utilization, decay_steps, adjustment


def _register_hq_address(ripe_hq, governance, address, description, expected_id):
    lock = ripe_hq.registryChangeTimeLock()
    assert ripe_hq.startAddNewAddressToRegistry(
        address,
        description,
        sender=governance.address,
    )
    travel_blocks(lock)
    reg_id = ripe_hq.confirmNewAddressToRegistry(
        address,
        sender=governance.address,
    )
    assert reg_id == expected_id
    return reg_id


@pytest.fixture
def lane_factory(
    ripe_hq,
    switchboard_alpha,
    governance,
    charlie_token,
    charlie_token_whale,
    whale,
    bob,
    mission_control,
    ledger,
    ripe_token,
    teller,
    ripe_gov_vault,
    endaoment_funds,
    setGeneralConfig,
    setAssetConfig,
):
    with boa.env.anchor():

        def factory(
            payment_token=charlie_token,
            epoch_length=DEFAULT_EPOCH_LENGTH,
            auto_start=True,
            genesis_block=0,
            register_lane=True,
            register_claims=True,
            enable_mint=True,
            fund_buyer=True,
            buyer_funding=None,
            unpause_lane=True,
            unpause_claims=True,
            can_buy=True,
            allocation_budget=DEFAULT_ALLOCATION_BUDGET,
            config_overrides=None,
        ):
            scale = 10 ** payment_token.decimals()
            config = make_config(
                scale,
                epoch_length=epoch_length,
                **(config_overrides or {}),
            )
            lane = boa.load(
                "contracts/core/InstantBondLane.vy",
                ripe_hq,
                payment_token,
                config,
                name="instant_bond_lane",
            )
            claims = boa.load(
                "contracts/core/InstantBondClaims.vy",
                ripe_hq,
                name="instant_bond_claims",
            )

            lane_reg_id = 0
            if register_lane:
                lane_reg_id = _register_hq_address(
                    ripe_hq,
                    governance,
                    lane,
                    "Instant Bond Lane",
                    INSTANT_BOND_LANE_HQ_ID,
                )
                ripe_hq.initiateHqConfigChange(
                    lane_reg_id,
                    False,
                    enable_mint,
                    False,
                    sender=governance.address,
                )
                travel_blocks(ripe_hq.registryChangeTimeLock())
                assert ripe_hq.confirmHqConfigChange(
                    lane_reg_id,
                    sender=governance.address,
                )

            claims_reg_id = 0
            if register_claims:
                claims_reg_id = _register_hq_address(
                    ripe_hq,
                    governance,
                    claims,
                    "Instant Bond Claims",
                    INSTANT_BOND_CLAIMS_HQ_ID,
                )

            if unpause_lane:
                lane.pause(False, sender=switchboard_alpha.address)
            if unpause_claims:
                claims.pause(False, sender=switchboard_alpha.address)
            claims.setRemainingAllocationBudget(
                allocation_budget,
                sender=switchboard_alpha.address,
            )
            if can_buy:
                lane.setCanBuyNow(True, sender=switchboard_alpha.address)

            started_genesis = 0
            if auto_start:
                lane.start(
                    genesis_block,
                    epoch_length,
                    sender=switchboard_alpha.address,
                )
                started_genesis = lane.genesisBlock()
                if started_genesis > boa.env.evm.patch.block_number:
                    travel_blocks(started_genesis - boa.env.evm.patch.block_number)

            if fund_buyer:
                funding = (
                    10_000_000 * scale
                    if buyer_funding is None
                    else buyer_funding
                )
                payment_token.transfer(
                    bob,
                    funding,
                    sender=charlie_token_whale,
                )
                payment_token.approve(lane, MAX_UINT256, sender=bob)

            ctx = SimpleNamespace(
                lane=lane,
                claims=claims,
                payment_token=payment_token,
                scale=scale,
                genesis=started_genesis,
                epoch_length=epoch_length,
                config=config,
                lane_reg_id=lane_reg_id,
                claims_reg_id=claims_reg_id,
                bob=bob,
                ripe_whale=whale,
                governance=governance,
                switchboard=switchboard_alpha,
                ripe_hq=ripe_hq,
                mission_control=mission_control,
                ledger=ledger,
                ripe_token=ripe_token,
                teller=teller,
                ripe_gov_vault=ripe_gov_vault,
                endaoment_funds=endaoment_funds,
            )

            def set_config(**overrides):
                next_config = replace_config(ctx.config, **overrides)
                lane.setConfig(next_config, sender=switchboard_alpha.address)
                ctx.config = next_config
                return next_config

            def start(genesis=0, length=None):
                length = epoch_length if length is None else length
                resolved = (
                    boa.env.evm.patch.block_number if genesis == 0 else genesis
                )
                lane.start(genesis, length, sender=switchboard_alpha.address)
                ctx.genesis = resolved
                ctx.epoch_length = length
                ctx.config = replace_config(ctx.config, epochLength=length)
                return ctx.genesis

            def stop():
                lane.stop(sender=switchboard_alpha.address)
                ctx.genesis = 0

            def set_rate_override(target_rate, target_epoch=0):
                return lane.setRateOverride(
                    target_rate,
                    target_epoch,
                    sender=switchboard_alpha.address,
                )

            def cancel_rate_override():
                return lane.cancelRateOverride(sender=switchboard_alpha.address)

            def set_budget(amount):
                claims.setRemainingAllocationBudget(
                    amount,
                    sender=switchboard_alpha.address,
                )

            def setup_ripe_vault(
                min_lock=100,
                max_lock=1_000,
                can_exit=True,
                exit_fee=500,
                freeze_on_bad_debt=False,
                can_deposit=True,
                asset_can_deposit=True,
            ):
                setGeneralConfig(_canDeposit=can_deposit)
                lock_terms = (
                    min_lock,
                    max_lock,
                    20_000,
                    can_exit,
                    exit_fee,
                )
                mission_control.setRipeGovVaultConfig(
                    ripe_token,
                    HUNDRED_PERCENT,
                    freeze_on_bad_debt,
                    lock_terms,
                    sender=switchboard_alpha.address,
                )
                vault_id = mission_control.coreRipeGovVaultId()
                assert vault_id != 0
                setAssetConfig(
                    ripe_token,
                    _vaultIds=[vault_id],
                    _canDeposit=asset_can_deposit,
                )
                return lock_terms

            def quote(payment_amount, requested_vesting=0, sender=bob):
                return lane.previewBuyNow(
                    payment_amount,
                    requested_vesting,
                    sender=sender,
                )

            def buy(
                payment_amount,
                requested_vesting=0,
                expected_vesting=None,
                expected_epoch=None,
                min_ripe_out=0,
                deadline=None,
                sender=bob,
            ):
                preview = quote(
                    payment_amount,
                    requested_vesting,
                    sender=sender,
                )
                if expected_vesting is None:
                    expected_vesting = preview.vestingLength
                if expected_epoch is None:
                    expected_epoch = preview.epoch
                if deadline is None:
                    deadline = boa.env.evm.patch.block_number
                return lane.buyNow(
                    payment_amount,
                    requested_vesting,
                    expected_vesting,
                    expected_epoch,
                    min_ripe_out,
                    deadline,
                    sender=sender,
                )

            def claim(position_id, auto_deposit=False, lock_duration=0, sender=bob):
                return lane.claimVestedRipe(
                    position_id,
                    auto_deposit,
                    lock_duration,
                    sender=sender,
                )

            ctx.set_config = set_config
            ctx.start = start
            ctx.stop = stop
            ctx.set_rate_override = set_rate_override
            ctx.cancel_rate_override = cancel_rate_override
            ctx.set_budget = set_budget
            ctx.make_config = lambda **overrides: replace_config(
                ctx.config,
                **overrides,
            )
            ctx.setup_ripe_vault = setup_ripe_vault
            ctx.quote = quote
            ctx.buy = buy
            ctx.claim = claim
            return ctx

        yield factory


@pytest.fixture
def lane_env(lane_factory):
    return lane_factory()
