"""Read-only monitoring and all-user receipt reconciliation, without RPC."""
import json
import sys

import boa
import pytest
from eth_abi import encode

from scripts import legacy_vault_preflight as monitor

WAD = 10**18
USER = "0x" + "11" * 20
OTHER = "0x" + "22" * 20
EMITTER = "0x" + "33" * 20


def ok(value):
    return {"status": "ok", "values": [value], "gas_used": 100}


@pytest.mark.parametrize("fault,expected", [
    ("none", "executable"), ("dust", "rounding_residue"), ("pause", "paused"),
    ("custody", "unavailable_custody"), ("price", "missing_price"),
    ("malformed", "malformed_response"), ("gas", "gas_exhaustion"),
    ("revert", "unexplained_read_failure"), ("mismatch", "unexplained_traversal_mismatch"),
    ("expensive", "expensive_read"), ("overflow", "arithmetic_overflow"),
])
def test_classifies_strict_and_traversal_results(fault, expected):
    nav, value = ok(100), ok(100)
    custody, reserved, cv, paused, prices = 100, 0, 100, False, []
    traversed = 100 if fault in ("none", "expensive") else 0
    if fault == "dust": value = ok(0)
    if fault == "pause": paused = True
    if fault == "custody": reserved = 100
    if fault == "price": prices = [OTHER]
    if fault in ("malformed", "gas", "revert"):
        nav = {"status": {"malformed": "malformed_response", "gas": "gas_exhaustion", "revert": "revert"}[fault]}
    if fault == "expensive": nav["gas_used"] = 6_400_001
    if fault == "overflow": value = ok(2**256-1)
    traversal = {"status": "ok", "values": [OTHER, traversed]}
    assert monitor.classify(nav, value, traversal, custody, reserved, cv, paused, prices) == expected


@pytest.mark.parametrize("kind", ["lp", "sg", "mixed"])
@pytest.mark.parametrize("fault", ["none", "pause", "price", "one_wei"])
def test_real_legacy_cohort_diagnostic(legacy_env, kind, fault):
    e = legacy_env
    for token in ([e.lp, e.sg] if kind == "mixed" else [getattr(e, kind)]):
        e.deposit(e.bob, 200 * WAD, token)
        if fault in ("price", "one_wei"):
            e.claim(e.collateral, WAD, token)
    if fault == "pause": e.pool.pause(True, sender=e.alpha.address)
    if fault in ("price", "one_wei"): e.prices.setPrice(e.collateral, 0 if fault == "price" else 1)
    records = {name: {"address": str(c.address), "abi": c.abi} for name, c in
               (("RipeHq", e.hq), ("StabilityPool", e.pool), ("PriceDesk", e.pd), ("MissionControl", e.mc), ("Teller", e.teller))}
    before = [e.pool.userBalances(e.bob, a) for a in (e.lp, e.sg)]
    report = monitor.diagnose(records, [e.bob], e.book.address)
    assert report["passed"] == (fault in ("none", "pause"))
    assert not report["keeper_ready"]
    assert [e.pool.userBalances(e.bob, a) for a in (e.lp, e.sg)] == before
    assert len(report["cohorts"]) == (2 if kind == "mixed" else 1)
    if fault == "none":
        assert all(p["classification"] == "executable" for c in report["cohorts"] for p in c["positions"])
        e.borrower(e.bob)
        monitor.dry_run(records, report, [{"user": str(e.bob), "target": WAD}], e.alpha.address)
        assert report["keeper_ready"] and len(report["reconciliation"]) == 1


def event(user=USER, credit=10, target=10, emitter=EMITTER):
    return {"address": emitter, "topics": [monitor.EVENT, int(user, 16).to_bytes(32, "big"), bytes(32)],
            "data": encode(["uint256"] * 4 + ["bool"], [target, target, credit, credit, True])}


@pytest.mark.parametrize("fault", ["missing", "duplicate", "wrong_emitter", "zero_credit", "partial_credit", "wrong_target", "unexpected", "duplicate_intent", "weakened_minimum"])
def test_receipt_rejects_incomplete_or_ambiguous_batches(fault):
    intended, logs = [{"user": USER, "target": 10}], [event()]
    if fault == "missing": logs = []
    if fault == "duplicate": logs.append(event())
    if fault == "wrong_emitter": logs = [event(emitter=OTHER)]
    if fault == "zero_credit": logs = [event(credit=0)]
    if fault == "partial_credit": logs = [event(credit=9)]
    if fault == "wrong_target": logs = [event(target=9)]
    if fault == "unexpected": logs.append(event(user=OTHER))
    if fault == "duplicate_intent": intended.append(intended[0])
    if fault == "weakened_minimum":
        intended[0]["minimum_credit"] = 1
        logs = [event(credit=1)]
    with pytest.raises(RuntimeError, match="KEEPER_"):
        monitor.reconcile(intended, EMITTER, logs)


def test_receipt_reconciles_both_users_independent_of_order():
    intended = [{"user": USER, "target": 10}, {"user": OTHER, "target": 20, "minimum_credit": 21}]
    result = monitor.reconcile(intended, EMITTER, [event(OTHER, 21, 20), event()])
    assert set(result) == {USER, OTHER}


@pytest.mark.parametrize("kind", ["revert", "malformed", "gas"])
def test_strict_probe_distinguishes_failed_reads(kind):
    source = {"revert": "@external\n@view\ndef value() -> uint256:\n    raise \"unavailable\"\n",
              "malformed": "@external\ndef __default__():\n    pass\n",
              "gas": "@external\n@view\ndef value() -> uint256:\n    x: bytes32 = empty(bytes32)\n    for i: uint256 in range(10000):\n        x = keccak256(x)\n    return convert(x, uint256)\n"}[kind]
    contract = boa.loads(source)
    result = monitor.probe(contract.address, "value()", [], [], gas=20_000)
    assert result["status"] == {"revert": "revert", "malformed": "malformed_response", "gas": "gas_exhaustion"}[kind]


def test_cli_failure_is_durable_and_nonzero(tmp_path, monkeypatch):
    output = tmp_path / "failure.json"
    monkeypatch.delenv("UNSET_TEST_RPC", raising=False)
    monkeypatch.setattr(sys, "argv", ["monitor", "--rpc-env", "UNSET_TEST_RPC", "--output", str(output)])
    with pytest.raises(SystemExit) as error:
        monitor.main()
    assert error.value.code == 1
    assert json.loads(output.read_text()) == {"passed": False, "keeper_ready": False, "live_transactions_sent": 0, "error": "BASE_LEGACY_COMPAT_RPC_ENV_REQUIRED"}

@pytest.mark.parametrize("fault", ["none", "unfinalized", "caller", "calldata", "omitted", "wrong_chain"])
def test_receipt_cli_binds_finalized_transaction_to_saved_intent(tmp_path, monkeypatch, fault):
    from types import SimpleNamespace
    import hashlib
    calldata = b"exact batch calldata"
    previous = {"keeper_ready": True, "keeper": USER, "teller": OTHER, "deleverage": EMITTER,
                "block": 100, "calldata_sha256": hashlib.sha256(calldata).hexdigest(),
                "intended": [{"user": USER, "target": 10}]}
    preflight, output = tmp_path / "preflight.json", tmp_path / "receipt.json"
    preflight.write_text(json.dumps(previous))
    receipt = SimpleNamespace(status=1, to=OTHER, blockNumber=101, logs=[] if fault == "omitted" else [event()])
    eth = SimpleNamespace(chain_id=1 if fault == "wrong_chain" else 8453,
        get_transaction_receipt=lambda _: receipt,
        get_block=lambda _: SimpleNamespace(number=100 if fault == "unfinalized" else 101),
        get_transaction=lambda _: {"from": OTHER if fault == "caller" else USER,
                                    "input": b"changed" if fault == "calldata" else calldata})
    factory = lambda _: SimpleNamespace(eth=eth)
    factory.HTTPProvider = lambda _: None
    monkeypatch.setattr(monitor, "Web3", factory)
    monkeypatch.setenv("TEST_RPC", "https://unused.invalid")
    monkeypatch.setattr(sys, "argv", ["monitor", "--rpc-env", "TEST_RPC", "--preflight", str(preflight),
                                      "--receipt-tx-hash", "0x1234", "--output", str(output)])
    if fault == "none":
        monitor.main()
        assert json.loads(output.read_text())["passed"]
    else:
        with pytest.raises(SystemExit): monitor.main()
        result = json.loads(output.read_text())
        assert result["passed"] is False and result["keeper_ready"] is False and result["error"]


def test_malformed_revert_reason_stays_a_failed_probe():
    assert monitor.revert_reason(bytes.fromhex("08c379a0"), "raw revert") == "raw revert"
