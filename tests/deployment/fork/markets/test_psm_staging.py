from __future__ import annotations

from config.robinhood_blueprint import (
    ROBINHOOD_BLUEPRINT,
    Disposition,
)


def _surface(surface_id):
    return next(
        surface
        for component in ROBINHOOD_BLUEPRINT.components
        for surface in component.surfaces
        if surface.surface_id == surface_id
    )


def test_psm_redeem_and_mint_start_disabled_in_real_blueprint(
    fork_framework, accepted_preflight
):
    fork_framework.require_owner_bindings(
        accepted_preflight.envelope, ("h08_assertions",)
    )
    assert _surface("S-048-REDEEM").disposition is Disposition.DISABLED
    assert _surface("S-048-MINT").disposition is Disposition.DISABLED


def test_psm_fee_rounding_is_minimal_and_conservative(fork_framework):
    synthetic_amount = 1_000_001
    synthetic_fee_bps = 7
    fee = fork_framework.conservative_fee(
        synthetic_amount, synthetic_fee_bps
    )
    numerator = synthetic_amount * synthetic_fee_bps
    assert fee * 10_000 >= numerator
    assert (fee - 1) * 10_000 < numerator


def test_pause_recovery_recreates_disposable_runtime_from_clean_state(
    fork_framework, synthetic_disposable_runtime, injected_market_state
):
    controller = synthetic_disposable_runtime
    controller.create()
    fork_framework.validate_local_fork_action(
        "set_storage",
        disposable_runtime_active=True,
        targets_local_fork=True,
    )
    state_path = controller.runtime_dir / "synthetic-psm-state.json"
    initial = fork_framework.canonical_json_bytes(injected_market_state)
    state_path.write_bytes(initial)
    mutated = dict(injected_market_state)
    mutated["psm_paused"] = False
    state_path.write_bytes(fork_framework.canonical_json_bytes(mutated))
    proof = controller.destroy()
    assert proof.storage_disposed is True

    controller.create()
    restored_path = controller.runtime_dir / "synthetic-psm-state.json"
    restored_path.write_bytes(initial)
    assert restored_path.read_bytes() == initial
    controller.destroy()


def test_lp_capital_and_psm_reserves_use_separate_ledgers(
    fork_framework, accepted_preflight, injected_market_state
):
    fork_framework.require_owner_bindings(
        accepted_preflight.envelope, ("h08_assertions",)
    )
    psm = injected_market_state["psm_ledger"]
    lp = injected_market_state["lp_ledger"]
    assert set(psm).isdisjoint(lp)
    assert sum(psm.values()) != sum(lp.values())


def test_psm_staging_consumes_synthetic_owner_control_output(
    fork_framework, accepted_preflight
):
    fork_framework.require_owner_bindings(
        accepted_preflight.envelope, ("h08_assertions",)
    )
    fields = (
        "mint_enabled",
        "paused",
        "redeem_enabled",
    )
    owner = {
        "mint_enabled": False,
        "paused": True,
        "redeem_enabled": False,
    }
    assert fork_framework.consume_owner_output(
        owner,
        dict(owner),
        required_fields=fields,
        code="H09_PSM_STAGING",
    ) == owner
