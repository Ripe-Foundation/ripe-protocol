from __future__ import annotations

from collections import Counter
import copy
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


ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "config" / "robinhood-parameters.json"
DEFAULTS = ROOT / "contracts" / "config" / "DefaultsRobinhood.vy"
GENERATOR = ROOT / "scripts" / "params" / "generate_robinhood_defaults.py"
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


def test_constructor_has_eight_named_blueprint_bindings_and_no_address_literals():
    values = sync.extract_defaults_values()
    assert tuple(blueprint_source.ROBINHOOD_DEFAULTS_CONSTRUCTOR) == (
        ("contributorTemplate", "CONTRIBUTOR_TEMPLATE"),
        ("trainingWheels", "TRAINING_WHEELS"),
        ("ripeToken", "RIPE_TOKEN"),
        ("greenToken", "GREEN_TOKEN"),
        ("sgreenToken", "SGREEN_TOKEN"),
        ("usdgToken", "USDG"),
        ("wethToken", "WETH"),
        ("steakhouseUsdgVault", "STEAKHOUSE_USDG_VAULT"),
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


def test_constructor_abi_intentionally_extends_pr66_five_arguments():
    abi = json.loads((ROOT / "scripts" / "abis" / "DefaultsRobinhood.json").read_text())
    constructor = next(entry for entry in abi if entry["type"] == "constructor")
    assert [item["name"] for item in constructor["inputs"]] == list(
        sync.CONSTRUCTOR_ABI_NAMES
    )
    tree_paths = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", PR66],
        cwd=ROOT,
        text=True,
    )
    precedent_path = next(
        path
        for path in tree_paths.splitlines()
        if path.lower() == "contracts/config/defaultsrobinhood.vy"
    )
    precedent = subprocess.check_output(
        ["git", "show", f"{PR66}:{precedent_path}"],
        cwd=ROOT,
        text=True,
    )
    assert precedent.count("immutable(address)") == 5
    assert "_usdgToken" not in precedent
    assert "_wethToken" not in precedent
    assert "_steakhouseUsdgVault" not in precedent


def test_manifest_partition_statuses_assets_and_omissions_are_exact():
    ledger = _ledger()
    records = ledger["parameters"]
    assert ledger["schema_version"] == sync.SCHEMA_VERSION
    assert len(records) == 436
    assert Counter(r["destination"]["kind"] for r in records) == Counter(
        defaults_field=305,
        deployment_input=119,
        assertion=12,
    )
    defaults = [r for r in records if r["destination"]["kind"] == "defaults_field"]
    assert Counter(r["status"] for r in defaults) == Counter(
        approved=223,
        external_fact=5,
        blocked=7,
        omitted=70,
    )
    asset_records = [
        r
        for r in defaults
        if r["destination"]["path"].startswith("Defaults.assetConfigs[")
        and r["status"] != "omitted"
    ]
    assert len(asset_records) == 155
    assert {
        r["destination"]["path"].split("[", 1)[1].split("]", 1)[0]
        for r in asset_records
    } == {"GREEN", "RIPE", "SGREEN", "WETH", "STEAKHOUSE_USDG"}
    omitted = [r for r in defaults if r["status"] == "omitted"]
    assert len(omitted) == 70
    assert all(r["value"] == {"kind": "omitted", "profile": "Profile 2"} for r in omitted)


def test_priority_and_profile1_values_normalize_from_defaults():
    values = sync.extract_defaults_values()
    assert values["Defaults.priorityLiqAssetVaults[0].vaultId"]["raw"] == 3
    assert values["Defaults.priorityLiqAssetVaults[0].asset"]["raw"] == (
        blueprint_source.ROBINHOOD_ADDRESSES["STEAKHOUSE_USDG_VAULT"]
    )
    assert values["Defaults.priorityLiqAssetVaults[1].vaultId"]["raw"] == 3
    assert values["Defaults.priorityLiqAssetVaults[1].asset"]["raw"] == (
        blueprint_source.ROBINHOOD_ADDRESSES["WETH"]
    )
    assert values["Defaults.priorityStabVaults[0].vaultId"]["raw"] == 1
    assert values["Defaults.priorityStabVaults[0].asset"] == {
        "kind": "symbolic_binding",
        "name": "SGREEN_TOKEN",
    }
    assert values["Defaults.priorityPriceSourceIds"] == {
        "kind": "concrete",
        "raw": [1, 3],
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
    assert len(destinations) == len(set(destinations)) == 436
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
    assert len(values) == 305
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
        ("return [1, 3]", "return [1]"),
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
    assert len(blockers) == 80
    assert not any("Deployment.DP-15.rewards.promotion" in item for item in blockers)
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
    assert params["GREEN_POOL_MA_EXP_TIME"] == 600
    assert params["GREEN_POOL_MA_EXP_TIME_ALTERNATIVE_TEST_VECTOR"] == 866
    assert type(params["GREEN_POOL_ADDRESS"]).__name__ == "SymbolicBinding"
    destinations = {
        record["destination"]["path"] for record in _ledger()["parameters"]
    }
    assert not any("curve" in destination.lower() for destination in destinations)


def test_launch_authority_semantics_are_preserved_except_resolved_morpho_gate():
    launch = json.loads(
        subprocess.check_output(
            ["git", "show", f"{LAUNCH}:config/robinhood-parameters.json"],
            cwd=ROOT,
            text=True,
        )
    )
    current = _ledger()
    old_by_id = {record["id"]: record for record in launch["parameters"]}
    new_by_id = {record["id"]: record for record in current["parameters"]}
    assert set(old_by_id) == set(new_by_id)
    for record_id, old in old_by_id.items():
        new = new_by_id[record_id]
        assert new["destination"] == old["destination"]
        if record_id in {"P-H04-399", "P-H04-436"}:
            assert old["status"] == "blocked"
            assert new["status"] == "approved"
            continue
        if record_id == "P-H04-391":
            assert old["value"] == {"kind": "concrete", "raw": False}
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
        if old["status"] in {"approved", "disabled", "external_fact", "derived"}:
            assert _semantic_raw(new["value"]) == _semantic_raw(old["value"])


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
