import boa
from hypothesis import settings, strategies as st
from hypothesis.stateful import (
    RuleBasedStateMachine,
    invariant,
    precondition,
    rule,
    run_state_machine_as_test,
)


HUNDRED_PERCENT = 10_000

CONFIG_KEYS = (
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


def as_config_dict(config):
    return dict(zip(CONFIG_KEYS, config))


def settlement_snapshot(ctx):
    return (
        ctx.lane.configVersion(),
        ctx.lane.isInitialized(),
        ctx.lane.currentEpoch(),
        ctx.lane.epochRate(),
        ctx.lane.epochPaymentCap(),
        ctx.lane.epochMinPaymentAmount(),
        ctx.lane.epochMaxLockBonus(),
        ctx.lane.epochPricingVersion(),
        ctx.lane.epochAcceptedPayment(),
        ctx.lane.cumulativeMinted(),
        ctx.payment_token.balanceOf(ctx.bob),
        ctx.payment_token.balanceOf(ctx.endaoment_funds),
        ctx.payment_token.balanceOf(ctx.lane),
        ctx.ripe_token.totalSupply(),
        ctx.ripe_token.balanceOf(ctx.bob),
        ctx.ripe_token.balanceOf(ctx.lane),
        ctx.ripe_token.balanceOf(ctx.ripe_gov_vault),
        ctx.ripe_token.allowance(ctx.lane, ctx.teller),
        ctx.ripe_gov_vault.getTotalAmountForUser(ctx.bob, ctx.ripe_token),
    )


def test_stateful_lifecycle_differential_fuzz(lane_env):
    class InstantBondLaneStateMachine(RuleBasedStateMachine):
        def __init__(self):
            super().__init__()
            self._anchor = boa.env.anchor()
            self._anchor.__enter__()
            self.ctx = lane_env

            self.paused = False
            self.mint_enabled = True
            self.lock_terms = self.ctx.setup_lock_terms(
                min_lock=100,
                max_lock=1_000,
                can_exit=True,
                exit_fee=500,
            )
            self.freeze_on_bad_debt = False

            initial = self.ctx.set_config(
                paymentCapPerEpoch=20 * self.ctx.scale,
                minPaymentAmount=self.ctx.scale,
                mintBudget=10_000_000 * 10**18,
                maxEffectiveRate=2 * 10**18,
                seedRate=10**18,
                maxLockBonus=5_000,
            )
            self.config_version = 1
            self.live_config = as_config_dict(initial)
            self.config_history = {self.config_version: self.live_config.copy()}

            self.initialized = False
            self.stored_pricing = None
            self.cumulative_minted = 0
            self.total_payment = 0
            self.destination_balance_start = self.ctx.payment_token.balanceOf(
                self.ctx.endaoment_funds
            )
            self.ripe_supply_start = self.ctx.ripe_token.totalSupply()

        def teardown(self):
            self._anchor.__exit__(None, None, None)

        def _lane_epoch(self):
            return (
                boa.env.evm.patch.block_number - self.ctx.genesis
            ) // self.ctx.epoch_length

        def _expected_pricing(self):
            epoch = self._lane_epoch()
            config = self.live_config

            if not self.initialized:
                return {
                    "epoch": epoch,
                    "rate": config["seedRate"],
                    "cap": config["paymentCapPerEpoch"],
                    "minimum": config["minPaymentAmount"],
                    "max_bonus": config["maxLockBonus"],
                    "version": self.config_version,
                    "accepted": 0,
                }

            pricing = self.stored_pricing.copy()
            if epoch <= pricing["epoch"]:
                return pricing

            elapsed = epoch - pricing["epoch"]
            ceiling = (
                config["maxEffectiveRate"]
                * HUNDRED_PERCENT
                // (HUNDRED_PERCENT + config["maxLockBonus"])
            )
            rate = min(pricing["rate"], ceiling)
            utilization = pricing["accepted"] * HUNDRED_PERCENT // pricing["cap"]

            if utilization >= config["uHighBps"]:
                rate = max(
                    rate
                    * HUNDRED_PERCENT
                    // (HUNDRED_PERCENT + config["upBps"]),
                    HUNDRED_PERCENT,
                )
            elif utilization <= config["uLowBps"]:
                rate = min(
                    rate
                    * HUNDRED_PERCENT
                    // (HUNDRED_PERCENT - config["downBps"]),
                    ceiling,
                )

            decay_steps = min(elapsed - 1, config["maxDecayEpochs"])
            for _ in range(decay_steps):
                rate = min(
                    rate
                    * HUNDRED_PERCENT
                    // (HUNDRED_PERCENT - config["decayBps"]),
                    ceiling,
                )

            return {
                "epoch": epoch,
                "rate": rate,
                "cap": config["paymentCapPerEpoch"],
                "minimum": config["minPaymentAmount"],
                "max_bonus": config["maxLockBonus"],
                "version": self.config_version,
                "accepted": 0,
            }

        def _expected_payout(self, pricing, payment_amount, requested_lock):
            min_lock, max_lock, _, can_exit, exit_fee = self.lock_terms
            actual_lock = 0
            bonus_ratio = 0

            if (
                max_lock != 0
                and max_lock >= min_lock
                and requested_lock >= min_lock
            ):
                actual_lock = min(requested_lock, max_lock)
                if max_lock == min_lock:
                    bonus_ratio = pricing["max_bonus"]
                else:
                    bonus_ratio = (
                        pricing["max_bonus"]
                        * (actual_lock - min_lock)
                        // (max_lock - min_lock)
                    )

            base_ripe = payment_amount * pricing["rate"] // self.ctx.scale
            bonus_ripe = base_ripe * bonus_ratio // HUNDRED_PERCENT
            return {
                "actual_lock": actual_lock,
                "bonus_ratio": bonus_ratio,
                "base_ripe": base_ripe,
                "bonus_ripe": bonus_ripe,
                "total_ripe": base_ripe + bonus_ripe,
                "can_exit": can_exit if actual_lock != 0 else False,
                "exit_fee": exit_fee if actual_lock != 0 else 0,
            }

        def _operational(self):
            return (
                not self.paused
                and self.live_config["canBuyNow"]
                and self.mint_enabled
            )

        def _minimum_purchase_available(self):
            pricing = self._expected_pricing()
            remaining = pricing["cap"] - pricing["accepted"]
            if not self._operational() or remaining < pricing["minimum"]:
                return False

            payout = self._expected_payout(pricing, pricing["minimum"], 0)
            budget_remaining = (
                self.live_config["mintBudget"] - self.cumulative_minted
            )
            return (
                payout["base_ripe"] != 0
                and payout["total_ripe"] <= budget_remaining
            )

        def _assert_quote(self, payment_amount, requested_lock):
            pricing = self._expected_pricing()
            quote = self.ctx.quote(payment_amount, requested_lock)
            remaining = pricing["cap"] - pricing["accepted"]
            budget_remaining = (
                self.live_config["mintBudget"] - self.cumulative_minted
            )

            assert quote.epoch == pricing["epoch"]
            assert quote.pricingConfigVersion == pricing["version"]
            assert quote.liveConfigVersion == self.config_version
            assert quote.rate == pricing["rate"]
            assert quote.remainingPayment == remaining
            assert quote.minPaymentAmount == pricing["minimum"]
            assert quote.budgetRemaining == budget_remaining

            valid_amount = pricing["minimum"] <= payment_amount <= remaining
            if not valid_amount:
                assert quote.baseRipe == 0
                assert quote.bonusRipe == 0
                assert quote.totalRipe == 0
                assert not quote.available
                return quote, pricing, None

            payout = self._expected_payout(pricing, payment_amount, requested_lock)
            assert quote.baseRipe == payout["base_ripe"]
            assert quote.bonusRatio == payout["bonus_ratio"]
            assert quote.bonusRipe == payout["bonus_ripe"]
            assert quote.actualLock == payout["actual_lock"]
            assert quote.totalRipe == payout["total_ripe"]
            assert quote.canExitEarly == payout["can_exit"]
            assert quote.exitFee == payout["exit_fee"]
            assert not quote.isExitFrozen

            expected_available = (
                self._operational()
                and payout["base_ripe"] != 0
                and payout["total_ripe"] <= budget_remaining
            )
            assert quote.available == expected_available
            assert (
                quote.totalRipe * self.ctx.scale
                <= payment_amount
                * self.config_history[pricing["version"]]["maxEffectiveRate"]
            )
            return quote, pricing, payout

        def _commit_purchase(self, pricing, payment_amount, payout):
            self.initialized = True
            self.stored_pricing = pricing.copy()
            self.stored_pricing["accepted"] += payment_amount
            self.cumulative_minted += payout["total_ripe"]
            self.total_payment += payment_amount

        @rule(blocks=st.integers(min_value=1, max_value=4_100))
        def advance_blocks(self, blocks):
            boa.env.time_travel(blocks=blocks)

        @rule(
            data=st.data(),
            can_buy_now=st.booleans(),
            cap_units=st.integers(min_value=1, max_value=50),
            minimum_selector=st.integers(min_value=0, max_value=1_000),
            seed_rate=st.sampled_from((10_000, 10**6, 10**12, 10**18)),
            ceiling_multiplier=st.integers(min_value=1, max_value=5),
            max_bonus=st.sampled_from((0, 1, 5_000, 100_000)),
            max_decay=st.integers(min_value=1, max_value=32),
            budget_fraction=st.integers(min_value=0, max_value=6),
        )
        def install_valid_config(
            self,
            data,
            can_buy_now,
            cap_units,
            minimum_selector,
            seed_rate,
            ceiling_multiplier,
            max_bonus,
            max_decay,
            budget_fraction,
        ):
            minimum_units = 1 + minimum_selector % cap_units
            u_low = data.draw(st.integers(min_value=0, max_value=9_999))
            u_high = data.draw(
                st.integers(min_value=u_low + 1, max_value=10_000)
            )
            up_bps = data.draw(st.integers(min_value=2, max_value=10_000))
            down_bps = data.draw(st.integers(min_value=1, max_value=up_bps - 1))
            decay_bps = data.draw(
                st.integers(min_value=down_bps, max_value=9_999)
            )

            cap = cap_units * self.ctx.scale
            target_ceiling = seed_rate * ceiling_multiplier
            max_effective_rate = (
                target_ceiling * (HUNDRED_PERCENT + max_bonus)
                + HUNDRED_PERCENT
                - 1
            ) // HUNDRED_PERCENT
            max_base_ripe = cap * target_ceiling // self.ctx.scale
            max_epoch_payout = (
                max_base_ripe
                + max_base_ripe * max_bonus // HUNDRED_PERCENT
            )
            headroom = max_epoch_payout * budget_fraction // 3

            config = self.ctx.make_config(
                canBuyNow=can_buy_now,
                paymentCapPerEpoch=cap,
                minPaymentAmount=minimum_units * self.ctx.scale,
                mintBudget=self.cumulative_minted + headroom,
                maxEffectiveRate=max_effective_rate,
                seedRate=seed_rate,
                uHighBps=u_high,
                uLowBps=u_low,
                upBps=up_bps,
                downBps=down_bps,
                decayBps=decay_bps,
                maxDecayEpochs=max_decay,
                maxLockBonus=max_bonus,
            )
            assert self.ctx.lane.isValidConfig(config)
            self.ctx.lane.setConfig(
                config,
                self.config_version,
                sender=self.ctx.switchboard.address,
            )

            self.config_version += 1
            self.live_config = as_config_dict(config)
            self.config_history[self.config_version] = self.live_config.copy()

        @rule(
            min_lock=st.integers(min_value=0, max_value=300),
            max_lock=st.integers(min_value=0, max_value=500),
            can_exit=st.booleans(),
            exit_fee=st.integers(min_value=0, max_value=10_000),
            freeze_on_bad_debt=st.booleans(),
        )
        def update_lock_terms(
            self,
            min_lock,
            max_lock,
            can_exit,
            exit_fee,
            freeze_on_bad_debt,
        ):
            self.lock_terms = self.ctx.setup_lock_terms(
                min_lock=min_lock,
                max_lock=max_lock,
                can_exit=can_exit,
                exit_fee=exit_fee,
                freeze_on_bad_debt=freeze_on_bad_debt,
            )
            self.freeze_on_bad_debt = freeze_on_bad_debt

        @rule()
        def toggle_pause(self):
            self.paused = not self.paused
            self.ctx.lane.pause(self.paused, sender=self.ctx.switchboard.address)

        @rule()
        def toggle_global_minting(self):
            self.mint_enabled = not self.mint_enabled
            self.ctx.ripe_hq.setMintingEnabled(
                self.mint_enabled,
                sender=self.ctx.governance.address,
            )

        @rule(
            amount_selector=st.integers(min_value=0, max_value=10**9),
            requested_lock=st.integers(min_value=0, max_value=2_000),
        )
        def purchase_or_prove_rollback(self, amount_selector, requested_lock):
            pricing = self._expected_pricing()
            remaining = pricing["cap"] - pricing["accepted"]
            if remaining >= pricing["minimum"]:
                payment_amount = pricing["minimum"] + amount_selector % (
                    remaining - pricing["minimum"] + 1
                )
            else:
                payment_amount = pricing["minimum"]

            quote, pricing, payout = self._assert_quote(
                payment_amount,
                requested_lock,
            )
            before = settlement_snapshot(self.ctx)

            if quote.available:
                result = self.ctx.buy(
                    payment_amount,
                    requested_lock=requested_lock,
                    expected_epoch=quote.epoch,
                    min_ripe_out=quote.totalRipe,
                )
                assert result == quote.totalRipe
                purchase_logs = [
                    log
                    for log in self.ctx.lane.get_logs()
                    if type(log).__name__ == "InstantBondPurchased"
                ]
                assert len(purchase_logs) == 1
                purchase = purchase_logs[0]
                assert purchase.buyer == self.ctx.bob
                assert purchase.paymentAmount == payment_amount
                assert purchase.baseRipe == payout["base_ripe"]
                assert purchase.bonusRipe == payout["bonus_ripe"]
                assert purchase.bonusRatio == payout["bonus_ratio"]
                assert purchase.actualLock == payout["actual_lock"]
                assert purchase.totalRipe == payout["total_ripe"]
                assert purchase.epochRate == pricing["rate"]
                assert purchase.epoch == pricing["epoch"]
                assert purchase.pricingConfigVersion == pricing["version"]
                assert purchase.liveConfigVersion == self.config_version
                assert purchase.ripeGovVaultId == (
                    self.ctx.mission_control.coreRipeGovVaultId()
                    if payout["actual_lock"]
                    else 0
                )
                self._commit_purchase(pricing, payment_amount, payout)
                return

            if self.paused:
                reason = "paused"
            elif not self.live_config["canBuyNow"]:
                reason = "disabled"
            elif not self.mint_enabled:
                reason = "mint unavailable"
            elif payment_amount > remaining:
                reason = "exceeds epoch cap"
            else:
                reason = "mint budget"

            with boa.reverts(reason):
                self.ctx.buy(
                    payment_amount,
                    requested_lock=requested_lock,
                    expected_epoch=quote.epoch,
                    min_ripe_out=quote.totalRipe,
                )
            assert settlement_snapshot(self.ctx) == before

        @precondition(lambda self: self._operational())
        @rule(kind=st.sampled_from(("below minimum", "above cap")))
        def invalid_amount_rolls_back(self, kind):
            pricing = self._expected_pricing()
            remaining = pricing["cap"] - pricing["accepted"]
            if kind == "below minimum":
                payment_amount = pricing["minimum"] - 1
                reason = "below minimum payment"
            else:
                payment_amount = max(remaining + 1, pricing["minimum"])
                reason = "exceeds epoch cap"

            quote, _, _ = self._assert_quote(payment_amount, 0)
            before = settlement_snapshot(self.ctx)
            with boa.reverts(reason):
                self.ctx.buy(
                    payment_amount,
                    expected_epoch=quote.epoch,
                    min_ripe_out=0,
                )
            assert settlement_snapshot(self.ctx) == before

        @precondition(lambda self: self._operational())
        @rule()
        def stale_epoch_rolls_back_lazy_rollover(self):
            pricing = self._expected_pricing()
            payment_amount = pricing["minimum"]
            stale_epoch = pricing["epoch"]
            boa.env.time_travel(blocks=self.ctx.epoch_length)
            before = settlement_snapshot(self.ctx)

            with boa.reverts("epoch moved"):
                self.ctx.buy(
                    payment_amount,
                    expected_epoch=stale_epoch,
                    min_ripe_out=0,
                )
            assert settlement_snapshot(self.ctx) == before

        @precondition(lambda self: self._minimum_purchase_available())
        @rule(requested_lock=st.integers(min_value=0, max_value=2_000))
        def slippage_rolls_back(self, requested_lock):
            pricing = self._expected_pricing()
            payment_amount = pricing["minimum"]
            quote, _, _ = self._assert_quote(payment_amount, requested_lock)
            if not quote.available:
                requested_lock = 0
                quote, _, _ = self._assert_quote(payment_amount, requested_lock)
            assert quote.available

            before = settlement_snapshot(self.ctx)
            with boa.reverts("slippage"):
                self.ctx.buy(
                    payment_amount,
                    requested_lock=requested_lock,
                    expected_epoch=quote.epoch,
                    min_ripe_out=quote.totalRipe + 1,
                )
            assert settlement_snapshot(self.ctx) == before

        @precondition(lambda self: self._operational())
        @rule()
        def expired_deadline_rolls_back(self):
            pricing = self._expected_pricing()
            before = settlement_snapshot(self.ctx)
            with boa.reverts("expired"):
                self.ctx.buy(
                    pricing["minimum"],
                    expected_epoch=pricing["epoch"],
                    deadline=boa.env.evm.patch.block_number - 1,
                )
            assert settlement_snapshot(self.ctx) == before

        @rule()
        def stale_config_version_rolls_back(self):
            config = tuple(self.live_config[key] for key in CONFIG_KEYS)
            before = settlement_snapshot(self.ctx)
            with boa.reverts("stale config version"):
                self.ctx.lane.setConfig(
                    config,
                    self.config_version - 1,
                    sender=self.ctx.switchboard.address,
                )
            assert settlement_snapshot(self.ctx) == before

        @invariant()
        def model_and_accounting_invariants_hold(self):
            assert self.ctx.lane.configVersion() == self.config_version
            assert self.ctx.lane.cumulativeMinted() == self.cumulative_minted
            assert self.cumulative_minted <= self.live_config["mintBudget"]
            assert (
                self.ctx.payment_token.balanceOf(self.ctx.endaoment_funds)
                == self.destination_balance_start + self.total_payment
            )
            assert (
                self.ctx.ripe_token.totalSupply()
                == self.ripe_supply_start + self.cumulative_minted
            )
            assert self.ctx.payment_token.balanceOf(self.ctx.lane) == 0
            assert self.ctx.ripe_token.balanceOf(self.ctx.lane) == 0
            assert self.ctx.ripe_token.allowance(self.ctx.lane, self.ctx.teller) == 0

            assert self.ctx.lane.isInitialized() == self.initialized
            if self.initialized:
                assert self.stored_pricing["accepted"] > 0
                assert self.ctx.lane.currentEpoch() == self.stored_pricing["epoch"]
                assert self.ctx.lane.epochRate() == self.stored_pricing["rate"]
                assert self.ctx.lane.epochPaymentCap() == self.stored_pricing["cap"]
                assert (
                    self.ctx.lane.epochMinPaymentAmount()
                    == self.stored_pricing["minimum"]
                )
                assert (
                    self.ctx.lane.epochMaxLockBonus()
                    == self.stored_pricing["max_bonus"]
                )
                assert (
                    self.ctx.lane.epochPricingVersion()
                    == self.stored_pricing["version"]
                )
                assert (
                    self.ctx.lane.epochAcceptedPayment()
                    == self.stored_pricing["accepted"]
                )
                assert self.stored_pricing["accepted"] <= self.stored_pricing["cap"]
                assert self.stored_pricing["epoch"] <= self._lane_epoch()

            pricing = self._expected_pricing()
            self._assert_quote(pricing["minimum"], self.lock_terms[1])

    run_state_machine_as_test(
        InstantBondLaneStateMachine,
        settings=settings(
            max_examples=50,
            stateful_step_count=20,
            deadline=None,
        ),
    )
