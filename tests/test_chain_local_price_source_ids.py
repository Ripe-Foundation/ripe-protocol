import boa

from conf_utils import filter_logs
from constants import ZERO_ADDRESS


PYTH_TARGET_SOURCE = """
# @version 0.4.3

maxConfidenceRatio: public(uint256)

@external
def setMaxConfidenceRatio(_ratio: uint256) -> bool:
    self.maxConfidenceRatio = _ratio
    return True
"""


CURVE_SNAPSHOT_TARGET_SOURCE = """
# @version 0.4.3

snapshotCalls: public(uint256)

@external
def addGreenRefPoolSnapshot() -> bool:
    self.snapshotCalls += 1
    return True
"""


REVERTING_CURVE_SNAPSHOT_TARGET_SOURCE = """
# @version 0.4.3

@external
def addGreenRefPoolSnapshot() -> bool:
    raise "snapshot failure"
"""


REVERTING_STABILIZER_SOURCE = """
# @version 0.4.3

struct StabilizerConfig:
    pool: address
    lpToken: address
    greenBalance: uint256
    greenRatio: uint256
    greenIndex: uint256
    stabilizerAdjustWeight: uint256
    stabilizerMaxPoolDebt: uint256
    altBalance: uint256

SHOULD_REVERT: immutable(bool)

@deploy
def __init__(_shouldRevert: bool):
    SHOULD_REVERT = _shouldRevert

@view
@external
def getGreenStabilizerConfig() -> StabilizerConfig:
    assert not SHOULD_REVERT # dev: selected curve id
    return empty(StabilizerConfig)
"""


def _register_price_source(price_desk, governance, source, description):
    assert price_desk.startAddNewAddressToRegistry(
        source,
        description,
        sender=governance.address,
    )
    boa.env.time_travel(blocks=price_desk.registryChangeTimeLock() + 1)
    source_id = price_desk.confirmNewAddressToRegistry(
        source,
        sender=governance.address,
    )
    assert source_id > 4
    return source_id


def test_switchboard_alpha_uses_constructor_pyth_id(
    ripe_hq,
    governance,
    price_desk,
    pyth_prices,
    switchboard_alpha,
):
    with boa.env.anchor():
        target = boa.loads(PYTH_TARGET_SOURCE, name="chain_local_pyth_target")
        source_id = _register_price_source(
            price_desk,
            governance,
            target,
            "Chain-local Pyth target",
        )
        candidate = boa.load(
            "contracts/config/SwitchboardAlpha.vy",
            ripe_hq,
            ZERO_ADDRESS,
            switchboard_alpha.MIN_STALE_TIME(),
            switchboard_alpha.MAX_STALE_TIME(),
            switchboard_alpha.minActionTimeLock(),
            switchboard_alpha.maxActionTimeLock(),
            source_id,
            name="switchboard_alpha_nondefault_pyth_id",
        )
        assert candidate.setActionTimeLockAfterSetup(sender=governance.address)

        original_ratio = pyth_prices.maxConfidenceRatio()
        action_id = candidate.setPythMaxConfidenceRatio(
            7_77,
            sender=governance.address,
        )
        boa.env.time_travel(blocks=candidate.actionTimeLock())
        assert candidate.executePendingAction(action_id, sender=governance.address)

        assert target.maxConfidenceRatio() == 7_77
        assert pyth_prices.maxConfidenceRatio() == original_ratio


def test_switchboard_alpha_zero_pyth_id_disables_without_consuming_action(
    ripe_hq,
    governance,
    switchboard_alpha,
):
    candidate = boa.load(
        "contracts/config/SwitchboardAlpha.vy",
        ripe_hq,
        ZERO_ADDRESS,
        switchboard_alpha.MIN_STALE_TIME(),
        switchboard_alpha.MAX_STALE_TIME(),
        switchboard_alpha.minActionTimeLock(),
        switchboard_alpha.maxActionTimeLock(),
        0,
        name="switchboard_alpha_pyth_disabled",
    )
    action_id_before = candidate.actionId()
    with boa.reverts("pyth disabled"):
        candidate.setPythMaxConfidenceRatio(5_00, sender=governance.address)
    assert candidate.actionId() == action_id_before


def test_credit_engine_uses_constructor_curve_id_and_zero_disables(
    ripe_hq,
    governance,
    price_desk,
    mock_curve_prices,
    setGeneralDebtConfig,
):
    with boa.env.anchor():
        source_id = _register_price_source(
            price_desk,
            governance,
            mock_curve_prices,
            "Chain-local Curve rate target",
        )
        mock_curve_prices.setMockGreenPoolData(70_00, 60_00, 10)
        setGeneralDebtConfig(
            _minDynamicRateBoost=100_00,
            _maxDynamicRateBoost=300_00,
            _increasePerDangerBlock=10,
            _maxBorrowRate=1_000_00,
        )

        candidate = boa.load(
            "contracts/core/CreditEngine.vy",
            ripe_hq,
            source_id,
            name="credit_engine_nondefault_curve_id",
        )
        disabled = boa.load(
            "contracts/core/CreditEngine.vy",
            ripe_hq,
            0,
            name="credit_engine_curve_disabled",
        )

        assert candidate.getDynamicBorrowRate(1_000) > 1_000
        assert disabled.getDynamicBorrowRate(1_000) == 1_000


def test_endaoment_uses_constructor_curve_id_and_zero_disables(
    ripe_hq,
    governance,
    price_desk,
    endaoment,
):
    with boa.env.anchor():
        target = boa.loads(
            REVERTING_STABILIZER_SOURCE,
            True,
            name="chain_local_endaoment_curve_target",
        )
        source_id = _register_price_source(
            price_desk,
            governance,
            target,
            "Chain-local Curve stabilizer target",
        )
        candidate = boa.load(
            "contracts/core/Endaoment.vy",
            ripe_hq,
            endaoment.WETH(),
            endaoment.ETH(),
            source_id,
            name="endaoment_nondefault_curve_id",
        )
        disabled = boa.load(
            "contracts/core/Endaoment.vy",
            ripe_hq,
            endaoment.WETH(),
            endaoment.ETH(),
            0,
            name="endaoment_curve_disabled",
        )

        with boa.reverts("selected curve id"):
            candidate.getGreenAmountToAddInStabilizer()
        assert disabled.getGreenAmountToAddInStabilizer() == 0
        assert disabled.getGreenAmountToRemoveInStabilizer() == 0
        assert disabled.calcProfitForStabilizer() == 0


def test_teller_uses_constructor_curve_id_and_zero_disables(
    ripe_hq,
    governance,
    price_desk,
    credit_engine,
    bob,
    alice,
):
    with boa.env.anchor():
        target = boa.loads(
            CURVE_SNAPSHOT_TARGET_SOURCE,
            name="chain_local_teller_curve_target",
        )
        source_id = _register_price_source(
            price_desk,
            governance,
            target,
            "Chain-local Curve snapshot target",
        )
        candidate = boa.load(
            "contracts/core/Teller.vy",
            ripe_hq,
            False,
            source_id,
            name="teller_nondefault_curve_id",
        )
        disabled = boa.load(
            "contracts/core/Teller.vy",
            ripe_hq,
            False,
            0,
            name="teller_curve_disabled",
        )

        assert ripe_hq.startAddressUpdateToRegistry(
            17,
            disabled,
            sender=governance.address,
        )
        boa.env.time_travel(blocks=ripe_hq.registryChangeTimeLock() + 1)
        assert ripe_hq.confirmAddressUpdateToRegistry(17, sender=governance.address)
        disabled.performHousekeeping(
            False,
            alice,
            False,
            sender=credit_engine.address,
        )
        assert target.snapshotCalls() == 0

        assert ripe_hq.startAddressUpdateToRegistry(
            17,
            candidate,
            sender=governance.address,
        )
        boa.env.time_travel(blocks=ripe_hq.registryChangeTimeLock() + 1)
        assert ripe_hq.confirmAddressUpdateToRegistry(17, sender=governance.address)
        candidate.performHousekeeping(
            False,
            bob,
            False,
            sender=credit_engine.address,
        )
        assert target.snapshotCalls() == 1
        assert filter_logs(candidate, "CurveSnapshotFailed") == []


def test_teller_curve_snapshot_is_bounded_best_effort_housekeeping(
    ripe_hq,
    governance,
    price_desk,
    credit_engine,
    ledger,
    alice,
):
    with boa.env.anchor():
        target = boa.loads(
            REVERTING_CURVE_SNAPSHOT_TARGET_SOURCE,
            name="reverting_chain_local_teller_curve_target",
        )
        source_id = _register_price_source(
            price_desk,
            governance,
            target,
            "Reverting chain-local Curve snapshot target",
        )
        candidate = boa.load(
            "contracts/core/Teller.vy",
            ripe_hq,
            False,
            source_id,
            name="teller_bounded_curve_snapshot",
        )

        assert ripe_hq.startAddressUpdateToRegistry(
            17,
            candidate,
            sender=governance.address,
        )
        boa.env.time_travel(blocks=ripe_hq.registryChangeTimeLock() + 1)
        assert ripe_hq.confirmAddressUpdateToRegistry(17, sender=governance.address)

        # Optional snapshot failure is isolated, while required Ledger
        # housekeeping still completes normally.
        candidate.performHousekeeping(
            False,
            alice,
            False,
            sender=credit_engine.address,
            gas=1_500_000,
        )
        assert ledger.lastTouch(alice) == boa.env.evm.patch.block_number
        logs = filter_logs(candidate, "CurveSnapshotFailed")
        assert len(logs) == 1
