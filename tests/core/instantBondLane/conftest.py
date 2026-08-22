from types import SimpleNamespace

import boa
import pytest

from constants import MAX_UINT256


HUNDRED_PERCENT = 10_000
DEFAULT_EPOCH_LENGTH = 100
MIN_BASE_RATE = 10_000

CONFIG_KEYS = (
    "canBuyNow",
    "paymentCapPerEpoch",
    "minPaymentAmount",
    "mintBudget",
    "maxEffectiveRate",
    "seedRate",
    "uHighBps",
    "uLowBps",
    "minUpBps",
    "maxUpBps",
    "minDownBps",
    "maxDownBps",
    "decayBps",
    "maxDecayEpochs",
    "maxLockBonus",
    "minLockDuration",
    "epochLength",
)


def make_config(scale, epoch_length=DEFAULT_EPOCH_LENGTH, **overrides):
    max_safe_scaled = (2**256 - 1) // 10_000
    cap = scale if 1_000 * scale > max_safe_scaled else 1_000 * scale
    max_safe_rate = (2**256 - 1) // max(cap, 1)
    values = {
        "canBuyNow": True,
        "paymentCapPerEpoch": cap,
        "minPaymentAmount": scale,
        "mintBudget": 1_000_000 * 10**18,
        "maxEffectiveRate": 2 * 10**18 if 2 * 10**18 <= max_safe_rate else 11_000,
        "seedRate": 10**18 if 10**18 <= max_safe_rate else 10_000,
        "uHighBps": 8_000,
        "uLowBps": 2_000,
        "minUpBps": 1_000,
        "maxUpBps": 1_000,
        "minDownBps": 500,
        "maxDownBps": 500,
        "decayBps": 900,
        "maxDecayEpochs": 4,
        "maxLockBonus": 5_000 if 2 * 10**18 <= max_safe_rate else 0,
        "minLockDuration": 0,
        "epochLength": epoch_length,
    }
    values.update(overrides)
    return tuple(values[key] for key in CONFIG_KEYS)


def config_dict(config):
    return dict(zip(CONFIG_KEYS, config))


def travel_blocks(blocks):
    if blocks > 0:
        boa.env.time_travel(blocks=blocks)


def settlement_accounting(ctx):
    return (
        ctx.lane.epochState().rate,
        ctx.lane.epochState().acceptedPayment,
        ctx.lane.cumulativeMinted(),
        ctx.payment_token.balanceOf(ctx.bob),
        ctx.payment_token.balanceOf(ctx.endaoment_funds),
        ctx.ripe_token.balanceOf(ctx.lane),
        ctx.ripe_token.balanceOf(ctx.bob),
        ctx.ripe_gov_vault.getTotalAmountForUser(ctx.bob, ctx.ripe_token),
        ctx.ripe_token.allowance(ctx.lane, ctx.teller),
    )


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
    ceiling = values["maxEffectiveRate"] * HUNDRED_PERCENT // (
        HUNDRED_PERCENT + values["maxLockBonus"]
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
                MIN_BASE_RATE,
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
            enable_mint=True,
            fund_buyer=True,
            buyer_funding=None,
            unpause=True,
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

            reg_id = 0
            if register_lane:
                registry_lock = ripe_hq.registryChangeTimeLock()
                assert ripe_hq.startAddNewAddressToRegistry(
                    lane, "Instant Bond Lane", sender=governance.address
                )
                travel_blocks(registry_lock)
                reg_id = ripe_hq.confirmNewAddressToRegistry(
                    lane, sender=governance.address
                )
                ripe_hq.initiateHqConfigChange(
                    reg_id, False, enable_mint, False, sender=governance.address
                )
                travel_blocks(registry_lock)
                assert ripe_hq.confirmHqConfigChange(
                    reg_id, sender=governance.address
                )

            if unpause:
                lane.pause(False, sender=switchboard_alpha.address)

            started_genesis = 0
            if auto_start:
                lane.start(
                    genesis_block,
                    epoch_length,
                    sender=switchboard_alpha.address,
                )
                started_genesis = lane.genesisBlock()
                if started_genesis > boa.env.evm.patch.block_number:
                    travel_blocks(
                        started_genesis - boa.env.evm.patch.block_number
                    )

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
                payment_token=payment_token,
                scale=scale,
                genesis=started_genesis,
                epoch_length=epoch_length,
                config=config,
                reg_id=reg_id,
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
                next_config = make_config(
                    scale,
                    epoch_length=lane.epochLength(),
                    **overrides,
                )
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
                return ctx.genesis

            def stop():
                lane.stop(sender=switchboard_alpha.address)
                ctx.genesis = 0

            def set_rate_override(target_rate):
                return lane.setRateOverride(
                    target_rate, sender=switchboard_alpha.address
                )

            def cancel_rate_override():
                return lane.cancelRateOverride(sender=switchboard_alpha.address)

            def setup_lock_terms(
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
                core_vault_id = mission_control.coreRipeGovVaultId()
                assert core_vault_id != 0
                setAssetConfig(
                    ripe_token,
                    _vaultIds=[core_vault_id],
                    _canDeposit=asset_can_deposit,
                )
                return lock_terms

            def quote(payment_amount, requested_lock=0, sender=bob):
                return lane.previewBuyNow(
                    payment_amount,
                    requested_lock,
                    sender=sender,
                )

            def buy(
                payment_amount,
                requested_lock=0,
                expected_epoch=None,
                min_ripe_out=0,
                deadline=None,
                sender=bob,
            ):
                if expected_epoch is None:
                    expected_epoch = quote(
                        payment_amount,
                        requested_lock,
                        sender=sender,
                    ).epoch
                if deadline is None:
                    deadline = boa.env.evm.patch.block_number
                return lane.buyNow(
                    payment_amount,
                    requested_lock,
                    expected_epoch,
                    min_ripe_out,
                    deadline,
                    sender=sender,
                )

            ctx.set_config = set_config
            ctx.start = start
            ctx.stop = stop
            ctx.set_rate_override = set_rate_override
            ctx.cancel_rate_override = cancel_rate_override
            ctx.make_config = lambda **overrides: make_config(
                scale, epoch_length=lane.epochLength(), **overrides
            )
            ctx.setup_lock_terms = setup_lock_terms
            ctx.quote = quote
            ctx.buy = buy
            return ctx

        yield factory


@pytest.fixture
def lane_env(lane_factory):
    return lane_factory()
