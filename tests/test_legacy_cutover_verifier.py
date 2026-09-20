"""Ordinary composition tests: no network, no bypass of runtime/manifest checks."""
import copy
import hashlib
import json
from functools import lru_cache

import boa
import pytest

from conf_legacy_pool import storage_write
from test_base_review_safety import legacy_compat_staging
from scripts import verify_legacy_vault_cutover as verifier
from scripts.capture_legacy_vault_baseline import capture
from scripts.utils import migration as migration_tools
from scripts.utils.legacy_vault_compat import PREVIOUS_SUFFIX, HQ_SLOTS, ZERO


@pytest.fixture(scope="module", autouse=True)
def cache_pure_compilation():
    # Cache only deterministic compiler output, never address/runtime/state or
    # expected-argument validation. Every authentication check still executes.
    original = migration_tools.compile_json
    @lru_cache(maxsize=64)
    def cached(encoded):
        return original(json.loads(encoded))
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(migration_tools, "compile_json", lambda obj: copy.deepcopy(cached(json.dumps(obj, sort_keys=True))))
        yield


@pytest.fixture
def staged(legacy_compat_staging, monkeypatch):
    module, migration, e = legacy_compat_staging
    monkeypatch.setattr(verifier, "HQ", str(e.hq.address).lower())
    monkeypatch.setattr(verifier, "POOL", str(e.pool.address).lower())
    records = migration.records
    for name, contract in {"RipeHq": e.hq, "VaultBook": e.book, "StabilityPool": e.pool,
                           "RipeGov": e.ripe_gov, "SimpleErc20": e.ordinary, "MissionControl": e.mc,
                           "Deleverage": e.dl, "AuctionHouse": e.ah,
                           "Switchboard": migration.get_contract("SwitchboardPopulated" + module.PREVIOUS_SUFFIX)}.items():
        records[name] = {"address": str(contract.address), "abi": contract.abi}
    for name, row, source in (("RebaseErc20", 4, "RebaseErc20"), ("Underscore Vault", 5, "SimpleErc20")):
        contract = boa.load_partial(f"contracts/vaults/{source}.vy").at(e.book.getAddr(row))
        records[name] = {"address": str(contract.address), "abi": contract.abi}
    baseline = capture(records)
    module.migrate(migration)
    return records, baseline, migration, e


def check(staged):
    records, baseline, migration, e = staged
    return verifier.verify_candidates(records, str(e.bob), baseline, "staged")


def test_staged_verifier_composition(staged):
    result = check(staged)
    assert result["passed"] and result["expected_phase"] == "staged"
    assert result["active_retained_rows"] == result["candidate_retained_rows"]
    assert not any(result["active_candidate_slots"].values())
    assert result["foxtrot_setup"]["initStep"] == 1


@pytest.mark.parametrize("slot", [6, 8, 9, 18])
@pytest.mark.parametrize("kind", ["partial", "unrelated"])
def test_verifier_rejects_lifecycle_mismatch(staged, slot, kind):
    _, _, migration, e = staged
    roles = {6: "Switchboard", 8: "VaultBook", 9: "AuctionHouse", 18: "Deleverage"}
    target = migration.deployed[roles[slot]].address if kind == "partial" else e.ripe_gov.address
    storage_write(e.hq, "registry", "addrInfo", [slot], target)
    with pytest.raises(RuntimeError, match=f"PHASE_STAGED_SLOT:{slot}"):
        check(staged)


@pytest.mark.parametrize("which", ["active", "candidate"])
@pytest.mark.parametrize("field", ["forward", "reverse", "valid"])
def test_verifier_rejects_vault_row_drift(staged, which, field):
    _, _, migration, e = staged
    book = e.book if which == "active" else migration.deployed["VaultBook"]
    if field == "forward":
        storage_write(book, "registry", "addrInfo", [3], e.dl.address)
    elif field == "reverse":
        storage_write(book, "registry", "addrToRegId", [book.getAddr(3)], 4)
    else:
        storage_write(book, "registry", "numAddrs", [], 4)
    with pytest.raises(RuntimeError, match="BASE_LEGACY_COMPAT_"):
        check(staged)


@pytest.mark.parametrize("slot", HQ_SLOTS)
@pytest.mark.parametrize("kind", ["pendingAddrUpdate", "pendingAddrDisable"])
def test_verifier_rejects_each_hq_pending_action(staged, slot, kind):
    _, _, _, e = staged
    storage_write(e.hq, "registry", kind, [slot], e.dl.address if kind == "pendingAddrUpdate" else 1)
    with pytest.raises(RuntimeError, match=f"HQ_PENDING_DRIFT:{slot}"):
        check(staged)


@pytest.mark.parametrize("registry", ["VaultBook", "Switchboard"])
@pytest.mark.parametrize("kind", ["pendingAddrUpdate", "pendingAddrDisable"])
def test_verifier_rejects_candidate_pending_actions(staged, registry, kind):
    _, _, migration, e = staged
    storage_write(migration.deployed[registry], "registry", kind, [1], e.dl.address if kind == "pendingAddrUpdate" else 1)
    with pytest.raises(RuntimeError, match="REGISTRY_PENDING:1"):
        check(staged)


@pytest.mark.parametrize("field,value", [("missionControl", 1), ("defaults", 1), ("initStep", 2), ("nextAssetIndex", 1), ("rewardsInitialized", 1)])
def test_verifier_rejects_every_foxtrot_field(staged, field, value):
    _, _, migration, _ = staged
    storage_write(migration.controllers[6], None, field, [], value)
    with pytest.raises(RuntimeError, match="FOXTROT_SETUP:" + field):
        check(staged)


def test_verifier_rejects_inherited_deleverage_drift(staged):
    _, _, _, e = staged
    e.dl.setMinDeleverageBps(100, sender=e.alpha.address)
    with pytest.raises(RuntimeError, match="ACTIVE_DELEVERAGE_DRIFT"):
        check(staged)


def test_candidate_manifest_cannot_redefine_baseline(staged):
    records, _, _, e = staged
    records["SimpleErc20"]["address"] = str(e.dl.address)
    with pytest.raises(RuntimeError, match="RECORDED_ADDRESS:SimpleErc20"):
        check(staged)


@pytest.mark.parametrize("fault", ["same_path", "symlink", "hardlink", "hash"])
def test_baseline_inputs_and_failure_reports(tmp_path, fault):
    baseline = tmp_path / "before.json"
    candidate = tmp_path / "after.json"
    baseline.write_text('{"schema":"legacy-vault-pre-stage-v1"}')
    digest = hashlib.sha256(baseline.read_bytes()).hexdigest()
    reason = "BASELINE_SAME_FILE"
    if fault == "same_path":
        candidate = baseline
    elif fault == "symlink":
        candidate.symlink_to(baseline)
    elif fault == "hardlink":
        candidate.hardlink_to(baseline)
    else:
        candidate.write_text('{"contracts":{}}')
        digest = "0" * 64
        reason = "BASELINE_HASH"
    output = tmp_path / "failure.json"
    with pytest.raises(RuntimeError, match=reason):
        verifier.run_verification(candidate, baseline, digest, ZERO, "staged", 1, "https://unused.invalid", output)
    report = json.loads(output.read_text())
    assert report["passed"] is False and report["error"] == "BASE_LEGACY_COMPAT_" + reason


def test_independent_baseline_hash_is_checked(tmp_path):
    baseline, candidate = tmp_path / "before.json", tmp_path / "after.json"
    baseline.write_text('{"schema":"legacy-vault-pre-stage-v1"}')
    candidate.write_text('{"contracts":{"candidate":"first"}}')
    digest = hashlib.sha256(baseline.read_bytes()).hexdigest()
    before, _, evidence = verifier.load_inputs(baseline, digest, candidate)
    candidate.write_text('{"contracts":{"candidate":"changed"}}')
    after, records, changed = verifier.load_inputs(baseline, digest, candidate)
    assert before == after and records["candidate"] == "changed"
    assert evidence["baseline_sha256"] == changed["baseline_sha256"]
    assert evidence["candidate_manifest_sha256"] != changed["candidate_manifest_sha256"]
