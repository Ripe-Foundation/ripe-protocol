from types import SimpleNamespace

import boa
import pytest

from constants import MAX_UINT256


HUNDRED_PERCENT = 10_000
DEFAULT_EPOCH_LENGTH = 100


def make_config(scale, **overrides):
    values = {
        "canBuyNow": True,
        "paymentCapPerEpoch": 1_000 * scale,
        "minPaymentAmount": scale,
        "mintBudget": 1_000_000 * 10**18,
        "maxEffectiveRate": 2 * 10**18,
        "seedRate": 10**18,
        "uHighBps": 8_000,
        "uLowBps": 2_000,
        "upBps": 1_000,
        "downBps": 500,
        "decayBps": 1_000,
        "maxDecayEpochs": 4,
        "maxLockBonus": 5_000,
    }
    values.update(overrides)
    return (
        values["canBuyNow"],
        values["paymentCapPerEpoch"],
        values["minPaymentAmount"],
        values["mintBudget"],
        values["maxEffectiveRate"],
        values["seedRate"],
        values["uHighBps"],
        values["uLowBps"],
        values["upBps"],
        values["downBps"],
        values["decayBps"],
        values["maxDecayEpochs"],
        values["maxLockBonus"],
    )


def config_dict(config):
    keys = (
        "canBuyNow",
        "paymentCapPerEpoch",
        "minPaymentAmount",
        "mintBudget",
        "maxEffectiveRate",
        "seedRate",
        "uHighBps",
        "uLowBps",
        "upBps",
        "downBps",
        "decayBps",
        "maxDecayEpochs",
        "maxLockBonus",
    )
    return dict(zip(keys, config))


def travel_blocks(blocks):
    if blocks > 0:
        boa.env.time_travel(blocks=blocks)


@pytest.fixture
def lane_factory(
    ripe_hq,
    switchboard,
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
    setUserConfig,
):
    with boa.env.anchor():
        def factory(
            payment_token=charlie_token,
            epoch_length=DEFAULT_EPOCH_LENGTH,
            start_at_genesis=True,
            register_lane=True,
            enable_mint=True,
            fund_buyer=True,
            buyer_funding=None,
            genesis_delay=5,
        ):
            registry_lock = ripe_hq.registryChangeTimeLock()
            setup_blocks = registry_lock * 2 if register_lane else 0
            genesis = boa.env.evm.patch.block_number + setup_blocks + genesis_delay

            lane = boa.load(
                "contracts/core/InstantBondLane.vy",
                ripe_hq,
                payment_token,
                genesis,
                epoch_length,
                name="instant_bond_lane",
            )

            reg_id = 0
            if register_lane:
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

            lane.pause(False, sender=switchboard_alpha.address)

            if start_at_genesis:
                travel_blocks(genesis - boa.env.evm.patch.block_number)

            scale = 10 ** payment_token.decimals()
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
                genesis=genesis,
                epoch_length=epoch_length,
                reg_id=reg_id,
                bob=bob,
                ripe_whale=whale,
                governance=governance,
                switchboard=switchboard_alpha,
                switchboard_registry=switchboard,
                ripe_hq=ripe_hq,
                mission_control=mission_control,
                ledger=ledger,
                ripe_token=ripe_token,
                teller=teller,
                ripe_gov_vault=ripe_gov_vault,
                endaoment_funds=endaoment_funds,
            )

            def set_config(expected_version=None, **overrides):
                if expected_version is None:
                    expected_version = lane.configVersion()
                config = make_config(scale, **overrides)
                lane.setConfig(config, expected_version, sender=switchboard_alpha.address)
                return config

            def setup_lock_terms(
                min_lock=100,
                max_lock=1_000,
                can_exit=True,
                exit_fee=500,
                freeze_on_bad_debt=False,
                can_deposit=True,
                asset_can_deposit=True,
                anyone_can_deposit=True,
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
                setAssetConfig(
                    ripe_token,
                    _vaultIds=[2],
                    _canDeposit=asset_can_deposit,
                )
                setUserConfig(
                    bob,
                    _canAnyoneDeposit=anyone_can_deposit,
                )
                return lock_terms

            def quote(payment_amount, requested_lock=0):
                return lane.previewBuyNow(payment_amount, requested_lock)

            def buy(
                payment_amount,
                requested_lock=0,
                expected_epoch=None,
                min_ripe_out=0,
                deadline=None,
                sender=bob,
            ):
                if expected_epoch is None:
                    expected_epoch = quote(payment_amount, requested_lock).epoch
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
            ctx.make_config = lambda **overrides: make_config(scale, **overrides)
            ctx.setup_lock_terms = setup_lock_terms
            ctx.quote = quote
            ctx.buy = buy
            return ctx

        yield factory


@pytest.fixture
def lane_env(lane_factory):
    return lane_factory()
