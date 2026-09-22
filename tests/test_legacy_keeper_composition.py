"""Actual local Teller execution through the keeper preflight and reconciliation."""

import pytest
from conf_utils import clear_transient_storage
from constants import EIGHTEEN_DECIMALS as WAD
from core.auctionHouse.test_base_legacy_vault_compat import debt, pool_state

from scripts import legacy_vault_preflight as monitor


@pytest.mark.parametrize(
    "changed",
    [
        "none",
        "paused",
        "price",
        "caller",
        "partial",
        "unprobed",
        "duplicate",
        "gas",
        "inactive",
    ],
)
def test_preflight_rechecks_changed_batch_and_clears_previous_success(
    legacy_env, changed
):
    e = legacy_env
    e.borrower(e.bob)
    e.deposit(e.bob, 100 * WAD, e.sg)
    records = {
        name: {"address": str(c.address), "abi": c.abi}
        for name, c in (
            ("RipeHq", e.hq),
            ("StabilityPool", e.pool),
            ("PriceDesk", e.pd),
            ("MissionControl", e.mc),
            ("Teller", e.teller),
        )
    }
    report = monitor.diagnose(records, [e.bob], e.book.address)
    intended = [{"user": str(e.bob), "target": WAD}]
    before = debt(e), pool_state(e), e.green.totalSupply()
    clear_transient_storage()
    monitor.dry_run(records, report, intended, e.alpha.address)
    assert report["keeper_ready"]
    assert (debt(e), pool_state(e), e.green.totalSupply()) == before
    keeper, limit = e.alpha.address, monitor.BATCH_GAS
    if changed == "paused":
        e.pool.pause(True, sender=e.alpha.address)
    elif changed == "price":
        claim = e.token()
        e.claim(claim, WAD, e.sg)
        e.prices.setShouldRevert(claim, True)
    elif changed == "caller":
        keeper = e.sally
    elif changed == "partial":
        intended = [{"user": str(e.bob), "target": 150 * WAD}]
    elif changed == "unprobed":
        intended = [{"user": str(e.alice), "target": WAD}]
    elif changed == "duplicate":
        intended = intended * 2
    elif changed == "gas":
        limit += 1
    elif changed == "inactive":
        report["active_book"] = str(e.lp.address)
    clear_transient_storage()
    before = debt(e), pool_state(e), e.green.totalSupply()
    if changed != "none":
        # Boa 0.2.7 can itself raise while formatting nested ABI-only errors;
        # every failed retry must invalidate readiness regardless of exception.
        with pytest.raises(Exception):
            monitor.dry_run(records, report, intended, keeper, limit)
        assert report["keeper_ready"] is False
        assert all(
            k not in report
            for k in (
                "reconciliation",
                "simulation",
                "intended",
                "keeper",
                "calldata_sha256",
            )
        )
    else:
        monitor.dry_run(records, report, intended, keeper, limit)
        assert report["keeper_ready"]
        clear_transient_storage()
        assert (
            e.teller.deleverageManyUsers([(e.bob, WAD)], sender=keeper, gas=limit)
            == WAD
        )
        computation = e.teller._computation
        logs = [
            {
                "address": "0x" + a.hex(),
                "topics": [t.to_bytes(32, "big") for t in topics],
                "data": data,
            }
            for a, topics, data in computation.get_log_entries()
        ]
        assert (
            monitor.reconcile(intended, report["deleverage"], logs)
            == report["reconciliation"]
        )
        assert debt(e) == before[0] - WAD
        return
    assert (debt(e), pool_state(e), e.green.totalSupply()) == before
