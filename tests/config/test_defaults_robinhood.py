from __future__ import annotations

import base64
from collections import Counter
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace

import pytest

from config import BluePrint as blueprint_source
from scripts.params import generate_robinhood_defaults as sync


pytestmark = pytest.mark.release


ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "config" / "robinhood-parameters.json"
DEFAULTS = ROOT / "contracts" / "config" / "DefaultsRobinhood.vy"
GENERATOR = ROOT / "scripts" / "params" / "generate_robinhood_defaults.py"
HISTORICAL_AUTHORITY = (
    ROOT
    / "tests"
    / "fixtures"
    / "robinhood"
    / "provenance"
    / "historical-authority-baselines.json"
)
HISTORICAL_AUTHORITY_SHA256 = (
    "516611b3125004ea002476505b16cb4ddf02579aec84dc9fb1d5c3a3c41ec6fa"
)
PR66 = "0f79b626c6ec4788ba43b3132ada9ebec6084f2a"
LAUNCH = "74c4120fbfa1ade859dc32f61acdf567c139fe02"
MORPHO = "33ad0f3c08bf6dc88f6569c622886d264d6e2868"


@pytest.fixture(scope="session")
def ripe_hq() -> None:
    """Override the repository autouse deployment fixture for source checks."""


def _ledger() -> dict:
    return json.loads(LEDGER.read_text())


def _records(ledger: dict | None = None) -> dict[str, dict]:
    selected = ledger or _ledger()
    return {
        record["destination"]["path"]: record
        for record in selected["parameters"]
    }


def _write_ledger(tmp_path: Path, ledger: dict) -> Path:
    path = tmp_path / "robinhood-parameters.json"
    path.write_bytes(sync.canonical_json(ledger))
    return path


def _mutated_defaults(tmp_path: Path, old: str, new: str) -> Path:
    source = DEFAULTS.read_text()
    assert source.count(old) >= 1
    path = tmp_path / "DefaultsRobinhood.vy"
    path.write_text(source.replace(old, new, 1), encoding="utf-8")
    return path


def _blueprint_proxy() -> SimpleNamespace:
    return SimpleNamespace(
        ZERO_ADDRESS=blueprint_source.ZERO_ADDRESS,
        ROBINHOOD_ADDRESSES=dict(blueprint_source.ROBINHOOD_ADDRESSES),
        ROBINHOOD_ADDRESS_STATUS=dict(blueprint_source.ROBINHOOD_ADDRESS_STATUS),
        ROBINHOOD_DEFAULTS_CONSTRUCTOR=tuple(
            blueprint_source.ROBINHOOD_DEFAULTS_CONSTRUCTOR
        ),
        ROBINHOOD_DEPLOYMENT_INPUTS=dict(
            blueprint_source.ROBINHOOD_DEPLOYMENT_INPUTS
        ),
        ROBINHOOD_CHAIN=dict(blueprint_source.ROBINHOOD_CHAIN),
        ROBINHOOD_ASSERTION_INVARIANTS=copy.deepcopy(
            blueprint_source.ROBINHOOD_ASSERTION_INVARIANTS
        ),
    )


def _semantic_raw(value: dict):
    if value["kind"] in {"typed_null", "symbolic_binding", "omitted"}:
        return None
    raw = value.get("raw")
    if isinstance(raw, str) and raw.isdigit():
        return int(raw)
    if isinstance(raw, str) and raw.startswith("["):
        return json.loads(raw)
    if isinstance(raw, str) and raw.startswith("0x"):
        return raw.lower()
    return raw


def _record_projection(record: dict) -> dict:
    return {
        "id": record["id"],
        "destination": record["destination"],
        "status": record["status"],
        "value": _semantic_raw(record["value"]),
    }


def _projection_sha256(records: list[dict]) -> str:
    payload = json.dumps(
        records,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def _historical_authority() -> dict:
    payload = HISTORICAL_AUTHORITY.read_bytes()
    assert hashlib.sha256(payload).hexdigest() == (
        HISTORICAL_AUTHORITY_SHA256
    )
    fixture = json.loads(payload)
    assert fixture["schema_version"] == (
        "rh-historical-authority-baselines-v1"
    )
    assert fixture["projection_semantics"] == {
        "canonical_json": (
            "sort_keys=true,separators=(',',':'),ensure_ascii=false"
        ),
        "fields": ["id", "destination", "status", "value"],
    }
    return fixture


def test_canonical_sources_exist_and_filename_casing_is_unique():
    names = [
        path.name
        for path in DEFAULTS.parent.iterdir()
        if path.name.lower() == "defaultsrobinhood.vy"
    ]
    assert names == ["DefaultsRobinhood.vy"]
    assert DEFAULTS.is_file()
    assert (ROOT / "config" / "BluePrint.py").is_file()


def test_defaults_implements_all_seventeen_interface_getters():
    assert sync.default_selectors() == (
        "genConfig",
        "genDebtConfig",
        "ripeAvailForRewards",
        "ripeAvailForHr",
        "ripeAvailForBonds",
        "ripeBondConfig",
        "rewardsConfig",
        "ripeGovVaultConfigs",
        "hrConfig",
        "underscoreRegistry",
        "trainingWheels",
        "shouldCheckLastTouch",
        "assetConfigs",
        "priorityLiqAssetVaults",
        "priorityStabVaults",
        "priorityPriceSourceIds",
        "liteSigners",
    )
    source = DEFAULTS.read_text()
    interface = (ROOT / "interfaces" / "Defaults.vyi").read_text()
    source_getters = set(re.findall(r"^def (\w+)\(", source, re.MULTILINE))
    source_getters.remove("__init__")
    assert source_getters == set(
        re.findall(r"^def (\w+)\(", interface, re.MULTILINE)
    )


def test_constructor_has_seven_named_blueprint_bindings_and_no_address_literals():
    values = sync.extract_defaults_values()
    assert tuple(blueprint_source.ROBINHOOD_DEFAULTS_CONSTRUCTOR) == (
        ("contributorTemplate", "CONTRIBUTOR_TEMPLATE"),
        ("trainingWheels", "TRAINING_WHEELS"),
        ("ripeToken", "RIPE_TOKEN"),
        ("greenToken", "GREEN_TOKEN"),
        ("sgreenToken", "SGREEN_TOKEN"),
        ("usdgToken", "USDG"),
        ("wethToken", "WETH"),
    )
    assert values["Defaults.hrConfig.contribTemplate"] == {
        "kind": "symbolic_binding",
        "name": "CONTRIBUTOR_TEMPLATE",
    }
    assert values["Defaults.trainingWheels"] == {
        "kind": "symbolic_binding",
        "name": "TRAINING_WHEELS",
    }
    assert values["Defaults.ripeBondConfig.asset"] == {
        "kind": "external_fact",
        "raw": blueprint_source.ROBINHOOD_ADDRESSES["USDG"],
    }
    assert not re.findall(r"0x[0-9A-Fa-f]{40}", DEFAULTS.read_text())


def test_constructor_abi_intentionally_extends_pr66_to_seven_arguments():
    abi = json.loads((ROOT / "scripts" / "abis" / "DefaultsRobinhood.json").read_text())
    constructor = next(entry for entry in abi if entry["type"] == "constructor")
    assert [item["name"] for item in constructor["inputs"]] == list(
        sync.CONSTRUCTOR_ABI_NAMES
    )
    baseline = _historical_authority()["pr66_defaults"]
    assert baseline == {
        "blob_oid": "e22bf986a4a1e01a33712ff7e82c5dcab33a04f8",
        "commit": PR66,
        "encoding": "base64",
        "path": "contracts/config/DefaultsRobinHood.vy",
        "sha256": (
            "4d2093f917c881181f8dc8ccd07f92e6bfd8c542476a84c06b15608d0bb89ca8"
        ),
        "snapshot_path": (
            "tests/fixtures/robinhood/provenance/"
            "defaults-robinhood-pr66.vy.snapshot.base64"
        ),
        "tree": "d198a3e70b420a5d1de1f272f9c785506d91da4d",
    }
    precedent_path = ROOT / baseline["snapshot_path"]
    encoded_lines = precedent_path.read_text(encoding="ascii").splitlines()
    assert encoded_lines
    assert all(len(line) == 76 for line in encoded_lines[:-1])
    assert 1 <= len(encoded_lines[-1]) <= 76
    precedent_bytes = base64.b64decode(
        "".join(encoded_lines),
        validate=True,
    )
    assert hashlib.sha256(precedent_bytes).hexdigest() == baseline["sha256"]
    precedent = precedent_bytes.decode()
    assert precedent.count("immutable(address)") == 5
    assert "_usdgToken" not in precedent
    assert "_wethToken" not in precedent
    assert "_steakhouseUsdgVault" not in precedent


def test_manifest_partition_statuses_assets_and_omissions_are_exact():
    ledger = _ledger()
    records = ledger["parameters"]
    assert ledger["schema_version"] == sync.SCHEMA_VERSION
    assert len(records) == 403
    assert Counter(r["destination"]["kind"] for r in records) == Counter(
        defaults_field=272,
        deployment_input=119,
        assertion=12,
    )
    defaults = [r for r in records if r["destination"]["kind"] == "defaults_field"]
    assert Counter(r["status"] for r in defaults) == Counter(
        approved=192,
        external_fact=3,
        blocked=7,
        omitted=70,
    )
    asset_records = [
        r
        for r in defaults
        if r["destination"]["path"].startswith("Defaults.assetConfigs[")
        and r["status"] != "omitted"
    ]
    assert len(asset_records) == 124
    assert {
        r["destination"]["path"].split("[", 1)[1].split("]", 1)[0]
        for r in asset_records
    } == {"GREEN", "RIPE", "SGREEN", "WETH"}
    omitted = [r for r in defaults if r["status"] == "omitted"]
    assert len(omitted) == 70
    assert all(r["value"] == {"kind": "omitted", "profile": "Profile 2"} for r in omitted)


def test_priority_and_profile1_values_normalize_from_defaults():
    values = sync.extract_defaults_values()
    assert values["Defaults.priorityLiqAssetVaults[0].vaultId"]["raw"] == 3
    assert values["Defaults.priorityLiqAssetVaults[0].asset"]["raw"] == (
        blueprint_source.ROBINHOOD_ADDRESSES["WETH"]
    )
    assert values["Defaults.priorityStabVaults[0].vaultId"]["raw"] == 1
    assert values["Defaults.priorityStabVaults[0].asset"] == {
        "kind": "symbolic_binding",
        "name": "SGREEN_TOKEN",
    }
    assert values["Defaults.priorityPriceSourceIds"] == {
        "kind": "concrete",
        "raw": [1, 2],
    }


def test_launch_stability_pool_routing_is_bounded_and_excludes_green():
    values = sync.extract_defaults_values()

    def raw(row, field):
        return values[f"Defaults.assetConfigs[{row}].config.{field}"]["raw"]

    assert raw("GREEN", "vaultIds") == []
    assert raw("GREEN", "shouldSwapInStabPools") is False
    assert raw("SGREEN", "vaultIds") == [1]
    assert values["Defaults.priorityStabVaults[0].asset"] == {
        "kind": "symbolic_binding",
        "name": "SGREEN_TOKEN",
    }

    routed = {
        row
        for row in sync.ACTIVE_ASSET_ROWS
        if raw(row, "shouldSwapInStabPools")
    }
    assert routed == {"WETH"}
    assert len(routed) <= 11


def test_every_value_has_one_source_owner_and_full_coverage():
    ledger = _ledger()
    defaults = sync.extract_defaults_values()
    deployment = sync.extract_deployment_values(defaults)
    assertions = sync.derive_assertion_values(defaults)
    destinations = [r["destination"]["path"] for r in ledger["parameters"]]
    assert len(destinations) == len(set(destinations)) == 403
    assert set(defaults) == {
        r["destination"]["path"]
        for r in ledger["parameters"]
        if r["destination"]["kind"] == "defaults_field"
    }
    assert set(deployment) == {
        r["destination"]["path"]
        for r in ledger["parameters"]
        if r["destination"]["kind"] == "deployment_input"
    }
    assert set(assertions) == {
        r["destination"]["path"]
        for r in ledger["parameters"]
        if r["destination"]["kind"] == "assertion"
    }
    assert not (set(defaults) & set(deployment))
    assert not (set(defaults) & set(assertions))
    assert not (set(deployment) & set(assertions))


def test_assertion_path_census_and_p_h04_306_are_source_derived():
    ledger = _ledger()
    assertion_records = [
        record
        for record in ledger["parameters"]
        if record["destination"]["kind"] == "assertion"
    ]
    assert tuple(
        record["destination"]["path"] for record in assertion_records
    ) == sync.ASSERTION_DESTINATION_PATHS
    defaults = sync.extract_defaults_values()
    assertions = sync.derive_assertion_values(defaults)
    assert assertions["Deployment.DP-01.lootbox.minUnderscoreSendInterval"] == {
        "kind": "concrete",
        "raw": blueprint_source.ROBINHOOD_CHAIN["blocks_per_minute"] * 60 * 24,
    }


@pytest.mark.parametrize("mutation", ["missing", "extra", "duplicate", "unknown"])
def test_assertion_missing_extra_duplicate_and_unknown_paths_fail_closed(
    tmp_path, mutation
):
    ledger = _ledger()
    assertions = [
        record
        for record in ledger["parameters"]
        if record["destination"]["kind"] == "assertion"
    ]
    if mutation == "missing":
        assertions[0]["destination"]["kind"] = "deployment_input"
    elif mutation == "extra":
        next(
            record
            for record in ledger["parameters"]
            if record["destination"]["kind"] == "deployment_input"
        )["destination"]["kind"] = "assertion"
    elif mutation == "duplicate":
        assertions[1]["destination"]["path"] = assertions[0]["destination"]["path"]
    else:
        assertions[1]["destination"]["path"] = "Deployment.UNKNOWN.assertion"
    path = _write_ledger(tmp_path, ledger)
    with pytest.raises(sync.ManifestError, match="H04_ASSERTION_PATH_CENSUS"):
        sync.check_ledger(path)


def test_assertion_only_ledger_drift_and_p_h04_306_mutation_fail_check(tmp_path):
    ledger = _ledger()
    record = next(item for item in ledger["parameters"] if item["id"] == "P-H04-306")
    record["value"] = {"kind": "concrete", "raw": 7_201}
    path = _write_ledger(tmp_path, ledger)
    with pytest.raises(sync.ManifestError, match="H04_LEDGER_DRIFT"):
        sync.check_ledger(path)


def test_defaults_extraction_preserves_boa_environment_and_cache_on_all_paths(
    tmp_path,
):
    import boa
    import boa.interpret as boa_interpret

    marker = boa.loads(
        """# @version 0.4.3
@external
@view
def marker() -> uint256:
    return 73
""",
        name="source_authority_environment_marker",
    )
    original_env = boa.env
    original_cache = boa_interpret._disk_cache
    original_cache_config = (
        getattr(original_cache, "cache_dir", None),
        getattr(original_cache, "version_salt", None),
    )

    values = sync.extract_defaults_values()
    assert len(values) == 272
    assert boa.env is original_env
    assert boa_interpret._disk_cache is original_cache
    assert (
        getattr(boa_interpret._disk_cache, "cache_dir", None),
        getattr(boa_interpret._disk_cache, "version_salt", None),
    ) == original_cache_config
    assert marker.marker() == 73

    broken = tmp_path / "DefaultsRobinhood.vy"
    broken.write_text(DEFAULTS.read_text() + "\nthis is not vyper\n")
    with pytest.raises(sync.ManifestError, match="H04_DEFAULTS_COMPILE"):
        sync.extract_defaults_values(broken)
    assert boa.env is original_env
    assert boa_interpret._disk_cache is original_cache
    assert (
        getattr(boa_interpret._disk_cache, "cache_dir", None),
        getattr(boa_interpret._disk_cache, "version_salt", None),
    ) == original_cache_config
    assert marker.marker() == 73


@pytest.mark.parametrize("mutation", ["missing", "extra"])
def test_missing_or_duplicate_blueprint_ownership_fails_closed(mutation):
    proxy = _blueprint_proxy()
    if mutation == "missing":
        proxy.ROBINHOOD_DEPLOYMENT_INPUTS.pop(next(iter(proxy.ROBINHOOD_DEPLOYMENT_INPUTS)))
    else:
        proxy.ROBINHOOD_DEPLOYMENT_INPUTS["Deployment.EXTRA"] = (
            blueprint_source.RobinhoodInput(1, "approved")
        )
    with pytest.raises(sync.ManifestError, match="H04_BLUEPRINT_DEPLOYMENT_INPUT_CENSUS"):
        sync.derive_ledger(_ledger(), blueprint=proxy)


def test_derived_ledger_matches_both_sources_and_check_mode():
    tracked = sync.load_ledger()
    assert sync.derive_ledger(tracked) == tracked
    identity = sync.check_ledger()
    assert identity == sync.ledger_sha256(tracked)


def test_manual_ledger_value_edit_and_metadata_override_fail(tmp_path):
    ledger = _ledger()
    record = _records(ledger)["Defaults.genConfig.perUserMaxVaults"]
    record["value"] = {"kind": "concrete", "raw": 999}
    record["source"] = {
        "citation": "owner metadata cannot override source",
        "commit": "0" * 40,
    }
    path = _write_ledger(tmp_path, ledger)
    with pytest.raises(sync.ManifestError, match="H04_LEDGER_DRIFT"):
        sync.check_ledger(path)


def test_unknown_ledger_keys_fail_closed(tmp_path):
    ledger = _ledger()
    ledger["parameters"][0]["unknown_value_authority"] = 7
    path = _write_ledger(tmp_path, ledger)
    with pytest.raises(sync.ManifestError, match="H04_RECORD_KEYS"):
        sync.check_ledger(path)


def test_blueprint_address_mutation_fails_ledger_check():
    proxy = _blueprint_proxy()
    proxy.ROBINHOOD_ADDRESSES["USDG"] = "0x1111111111111111111111111111111111111111"
    with pytest.raises(sync.ManifestError, match="H04_LEDGER_DRIFT"):
        sync.check_ledger(blueprint=proxy)


@pytest.mark.parametrize(
    ("old", "new"),
    (
        ("perUserMaxVaults = 5", "perUserMaxVaults = 6"),
        ("canDeposit = True", "canDeposit = False"),
        ("return [1, 2]", "return [1]"),
        ("vaultIds=[3]", "vaultIds=[2]"),
    ),
)
def test_defaults_numeric_boolean_list_and_asset_tuple_mutations_fail(tmp_path, old, new):
    mutated = _mutated_defaults(tmp_path, old, new)
    with pytest.raises(sync.ManifestError, match="H04_LEDGER_DRIFT"):
        sync.check_ledger(defaults_path=mutated)


def test_missing_and_uncompilable_defaults_fail_closed(tmp_path):
    with pytest.raises(sync.ManifestError, match="H04_DEFAULTS_MISSING"):
        sync.extract_defaults_values(tmp_path / "DefaultsRobinhood.vy")
    broken = tmp_path / "DefaultsRobinhood.vy"
    broken.write_text(DEFAULTS.read_text() + "\nthis is not vyper\n")
    with pytest.raises(sync.ManifestError, match="H04_DEFAULTS_COMPILE"):
        sync.extract_defaults_values(broken)


def test_sensitive_and_placeholder_rejection_remains_fail_closed():
    proxy = _blueprint_proxy()
    path = "Deployment.DP-05.timelocks.TokenHq.actionTimeLock"
    proxy.ROBINHOOD_DEPLOYMENT_INPUTS[path] = blueprint_source.RobinhoodInput(
        "placeholder-secret",
        "approved",
    )
    defaults = sync.extract_defaults_values(blueprint=proxy)
    with pytest.raises(sync.ManifestError, match="H04_FORBIDDEN_TEXT"):
        sync.extract_deployment_values(defaults, blueprint=proxy)


def test_source_reference_is_limited_to_defaults_and_allowlisted_live_evidence():
    defaults = sync.extract_defaults_values()
    values = sync.extract_deployment_values(defaults)
    assert values["Deployment.DP-16.ccip.promotion"] == {
        "kind": "external_fact",
        "raw": sync.CCIP_LIVE_EVIDENCE_PATH,
    }

    proxy = _blueprint_proxy()
    path = "Deployment.DP-16.ccip.promotion"
    proxy.ROBINHOOD_DEPLOYMENT_INPUTS[path] = blueprint_source.RobinhoodInput(
        blueprint_source.SourceReference("docs/chains/rh/evidence/not-allowlisted.json"),
        "external_fact",
    )
    with pytest.raises(sync.ManifestError, match="H04_SOURCE_REFERENCE"):
        sync.extract_deployment_values(defaults, blueprint=proxy)


def test_ccip_source_reference_rejects_same_path_byte_replacement(
    tmp_path, monkeypatch
):
    evidence_path = tmp_path / sync.CCIP_LIVE_EVIDENCE_PATH
    evidence_path.parent.mkdir(parents=True)
    payload = (ROOT / sync.CCIP_LIVE_EVIDENCE_PATH).read_bytes()
    evidence_path.write_bytes(payload + b"\n")
    monkeypatch.setattr(sync, "ROOT", tmp_path)
    with pytest.raises(sync.ManifestError, match="H04_CCIP_EVIDENCE_DIGEST"):
        sync._validated_ccip_live_evidence()


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        (lambda value: value.__setitem__("schema_version", 2), "SCHEMA"),
        (
            lambda value: value["chains"]["robinhood-mainnet"].__setitem__(
                "chain_id", 999
            ),
            "TOPOLOGY",
        ),
        (
            lambda value: value["chains"]["robinhood-mainnet"]["pools"][
                "RIPE"
            ].__setitem__("can_mint_ripe", False),
            "CAPABILITY",
        ),
    ],
)
def test_ccip_source_reference_validates_schema_topology_and_capabilities(
    tmp_path, monkeypatch, mutation, code
):
    evidence_path = tmp_path / sync.CCIP_LIVE_EVIDENCE_PATH
    evidence_path.parent.mkdir(parents=True)
    value = json.loads((ROOT / sync.CCIP_LIVE_EVIDENCE_PATH).read_bytes())
    mutation(value)
    payload = json.dumps(value, sort_keys=True).encode()
    evidence_path.write_bytes(payload)
    monkeypatch.setattr(sync, "ROOT", tmp_path)
    monkeypatch.setattr(
        sync, "CCIP_LIVE_EVIDENCE_SHA256", hashlib.sha256(payload).hexdigest()
    )
    with pytest.raises(sync.ManifestError, match=f"H04_CCIP_EVIDENCE_{code}"):
        sync._validated_ccip_live_evidence()


def test_dp16_ledger_records_current_live_fact_and_preserves_no_action_boundary():
    ledger = sync.derive_ledger(_ledger())
    records = _records(ledger)
    expected = {
        "Deployment.DP-16.ccip.greenEnabled": ("CM-051", True),
        "Deployment.DP-16.ccip.ripeEnabled": ("CM-052", True),
    }
    for path, (h03_ref, value) in expected.items():
        record = records[path]
        assert record["h03_ref"] == h03_ref
        assert record["status"] == "external_fact"
        assert record["value"] == {"kind": "external_fact", "raw": value}
        assert record["source"] == {
            "citation": sync.CCIP_LIVE_EVIDENCE_PATH,
            "capture_commit": sync.CCIP_LIVE_EVIDENCE_CAPTURE_COMMIT,
            "sha256": sync.CCIP_LIVE_EVIDENCE_SHA256,
        }
        assert record["approval"]["status"] == "confirmed_existing_state"
        assert record["blockers"] == ["B-T1-CCIP", "B-T1-TOOLCHAIN"]
        assert "no mutation authorized" in record["approval"]["provenance"]

    sgreen = records["Deployment.DP-16.ccip.sgreenEnabled"]
    assert sgreen["status"] == "disabled"
    assert sgreen["value"] == {"kind": "concrete", "raw": False}
    assert sgreen["source"]["citation"] == (
        "review-archives/h04/h04-group2-proposal-R2.md"
    )

    promotion = records["Deployment.DP-16.ccip.promotion"]
    assert promotion["h03_ref"] == "CM-053"
    assert promotion["status"] == "external_fact"
    assert promotion["value"] == {
        "kind": "external_fact",
        "raw": sync.CCIP_LIVE_EVIDENCE_PATH,
    }
    assert promotion["approval"]["schedule_id"] == "BS-H04-CCIP-PARKED"
    assert "no further transaction" in promotion["launch_phase"]

    schedule = next(
        item
        for item in ledger["binding_schedules"]
        if item["id"] == "BS-H04-CCIP-PARKED"
    )
    assert schedule["records"] == ["P-H04-403"]
    assert schedule["classification"] == (
        "confirmed_existing_state_with_operational_gates"
    )
    assert "separate transaction and release authority" in schedule[
        "closure_artifacts"
    ]


def test_sync_is_deterministic_and_writes_only_the_ledger(tmp_path):
    path = _write_ledger(tmp_path, _ledger())
    first_identity = sync.sync_ledger(path)
    first = path.read_bytes()
    second_identity = sync.sync_ledger(path)
    assert path.read_bytes() == first
    assert first_identity == second_identity == sync.ledger_sha256(json.loads(first))


def test_check_mode_performs_no_repository_writes(tmp_path):
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).split(b"\0")
    before = {
        path: (ROOT / path.decode()).read_bytes()
        for path in tracked
        if path and (ROOT / path.decode()).is_file()
    }
    environment = os.environ.copy()
    environment.update(
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONPYCACHEPREFIX=str(tmp_path / "pycache"),
        XDG_CACHE_HOME=str(tmp_path / "xdg"),
        ETHERSCAN_API_KEY="local-placeholder",
    )
    result = subprocess.run(
        [sys.executable, str(GENERATOR), "--check"],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    after = {
        path: (ROOT / path.decode()).read_bytes()
        for path in tracked
        if path and (ROOT / path.decode()).is_file()
    }
    assert after == before


def test_generator_has_no_defaults_render_or_write_path():
    source = GENERATOR.read_text()
    assert "render_defaults" not in source
    assert "atomic_replace_output" not in source
    assert "Generated only from" not in source
    assert "atomic_write_ledger" in source
    assert "DefaultsRobinhood.vy" in source
    assert "write_text" not in source


def test_bluechip_morpho_compatibility_is_resolved_but_readiness_is_not():
    records = _records()
    compatibility = records["Deployment.DP-23.blueChipYield.morphoV2Support"]
    assert compatibility["status"] == "approved"
    assert compatibility["value"] == {"kind": "concrete", "raw": True}
    assert compatibility["source"]["commit"] == MORPHO
    assert compatibility["blockers"] == []
    assert blueprint_source.ROBINHOOD_COMPONENTS["price_desk_registry"] == {
        1: "Chainlink",
        2: "Curve",
        3: "BlueChipYield",
        4: None,
        5: None,
    }
    ready, blockers = sync.deployment_readiness()
    assert ready is False
    assert len(blockers) == 65
    assert not any("Deployment.DP-15.rewards.promotion" in item for item in blockers)
    assert not any("Deployment.DP-16.ccip.promotion" in item for item in blockers)
    assert any(item.endswith(":unresolved") for item in blockers)
    assert any(item.endswith(":unverified") for item in blockers)
    assert any(item.startswith("curve:owner_selected:") for item in blockers)
    assert any(item.startswith("curve:deployment_produced:") for item in blockers)


def test_curve_launch_values_are_blueprint_owned_and_not_derived_json_values():
    params = blueprint_source.CURVE_PARAMS["robinhood"]
    assert params["GREEN_POOL_COINS"] == (
        blueprint_source.ROBINHOOD_ADDRESSES["USDG"],
        blueprint_source.ROBINHOOD_ADDRESSES["GREEN_TOKEN"],
    )
    assert params["GREEN_POOL_COIN_DECIMALS"] == (6, 18)
    assert params["GREEN_POOL_A"] == 100
    assert params["GREEN_POOL_FEE"] == 4_000_000
    assert params["GREEN_POOL_OFFPEG_MULTIPLIER"] == 20_000_000_000
    assert params["GREEN_POOL_MA_EXP_TIME"] == 866
    assert params["GREEN_POOL_MA_EXP_TIME_ALTERNATIVE_TEST_VECTOR"] == 866
    assert type(params["GREEN_POOL_ADDRESS"]).__name__ == "SymbolicBinding"
    destinations = {
        record["destination"]["path"] for record in _ledger()["parameters"]
    }
    assert not any("curve" in destination.lower() for destination in destinations)


def test_launch_authority_semantics_preserve_stable_ids_and_selected_reconciliations():
    baseline = _historical_authority()["launch_parameters"]
    assert {
        key: baseline[key]
        for key in ("blob_oid", "commit", "path", "sha256", "tree")
    } == {
        "blob_oid": "d0d367fb68f374b39e9540e1209051c913e05fe3",
        "commit": LAUNCH,
        "path": "config/robinhood-parameters.json",
        "sha256": (
            "1895fff3751fe6bc6f0d437cef78b757687fe519c0dd4ba2ce6a5c6baf3112bf"
        ),
        "tree": "296e1dcaf5e5c81f67b876cdfc9f78e3abd92f7a",
    }
    assert baseline["old_record_count"] == 436
    assert baseline["current_record_count"] == 403
    assert baseline["removed_record_count"] == 33
    assert baseline["reconciled_record_count"] == 16
    assert baseline["stable_record_count"] == 387
    assert baseline["stable_projection_sha256"] == (
        "f6570a4b8d0d198d7ee2d078497e47173303948b0a5a70c6af8864175b52ca50"
    )

    current = _ledger()
    new_by_id = {record["id"]: record for record in current["parameters"]}
    assert len(new_by_id) == baseline["current_record_count"]
    removed = baseline["removed"]
    removed_by_id = {record["id"]: record for record in removed}
    assert len(removed_by_id) == baseline["removed_record_count"]
    assert set(new_by_id).isdisjoint(removed_by_id)
    assert len(new_by_id) + len(removed_by_id) == baseline["old_record_count"]
    assert all(
        "STEAKHOUSE" in record["destination"]["path"]
        or record["destination"]["path"].startswith(
            "Defaults.priorityLiqAssetVaults[1]."
        )
        for record in removed
    )
    reconciled = baseline["reconciled"]
    reconciled_ids = set(reconciled)
    assert len(reconciled_ids) == baseline["reconciled_record_count"]
    stable_ids = sorted(set(new_by_id) - reconciled_ids)
    # Preserve the immutable launch-baseline proof while explicitly normalizing
    # the later dated CCIP live-state reconciliation back to its historical
    # projection. The generated ledger tests below assert the current facts.
    pre_live_ccip_projection = {
        "P-H04-400": ("disabled", False),
        "P-H04-401": ("disabled", False),
        "P-H04-403": ("blocked", None),
    }
    stable_projection = []
    for record_id in stable_ids:
        projection = _record_projection(new_by_id[record_id])
        if record_id in pre_live_ccip_projection:
            projection["status"], projection["value"] = (
                pre_live_ccip_projection[record_id]
            )
        stable_projection.append(projection)
    assert len(stable_projection) == baseline["stable_record_count"]
    assert _projection_sha256(stable_projection) == (
        baseline["stable_projection_sha256"]
    )
    semantic_changes = {
        record_id for record_id, old in reconciled.items()
        if new_by_id[record_id]["status"] != old["status"]
        or _semantic_raw(new_by_id[record_id]["value"]) != old["value"]
    }
    assert semantic_changes == reconciled_ids
    for record_id, old in reconciled.items():
        new = new_by_id[record_id]
        assert new["destination"] == old["destination"]
        if record_id in {"P-H04-399", "P-H04-436"}:
            assert old["status"] == "blocked"
            assert new["status"] == "approved"
            continue
        if record_id == "P-H04-391":
            assert old["value"] is False
            assert new["value"] == {"kind": "concrete", "raw": True}
            assert new["zero_semantics"] == {
                "kind": "not_zero",
                "explanation": (
                    "Approved explicit Stock exclusion; false, absence, "
                    "and omission are distinct."
                ),
            }
            continue
        assert new["status"] == old["status"]


def test_base_and_local_blueprint_values_are_byte_semantically_unchanged():
    baseline_source = subprocess.check_output(
        ["git", "show", f"{MORPHO}:config/BluePrint.py"],
        cwd=ROOT,
        text=True,
    )
    baseline: dict = {}
    exec(compile(baseline_source, "BluePrint-baseline.py", "exec"), baseline)
    for name in ("ADDYS", "PARAMS", "CURVE_PARAMS", "CORE_TOKENS", "YIELD_TOKENS"):
        current = getattr(blueprint_source, name)
        for profile, values in baseline[name].items():
            assert current[profile] == values
