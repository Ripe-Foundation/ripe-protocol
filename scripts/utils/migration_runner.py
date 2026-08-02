from __future__ import annotations

import ast
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import types
from typing import Any, Mapping, Sequence, TYPE_CHECKING

from scripts.utils import log

if TYPE_CHECKING:
    from scripts.utils.deploy_args import DeployArgs


class MigrationPlanError(ValueError):
    """Stable, sanitized H-05 discovery or planning failure."""

    def __init__(self, code: str):
        if re.fullmatch(r"H05_[A-Z0-9_]+", code) is None:
            raise ValueError("invalid H-05 error code")
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class MigrationReservation:
    migration_id: str
    filename: str
    semantic_id: str
    disposition: str
    local_blockers: tuple[str, ...] = ()
    input_bindings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SourceExpectation:
    migration_id: str
    filename: str
    semantic_id: str
    sha256: str | None = None


@dataclass(frozen=True, slots=True)
class DiscoveredSource:
    migration_id: str
    filename: str
    semantic_id: str
    sha256: str


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    members: tuple[DiscoveredSource, ...]
    source_digest: str


ROBINHOOD_RESERVATIONS: tuple[MigrationReservation, ...] = (
    MigrationReservation(
        "0010",
        "0010_Track6S3LootboxFloor.py",
        "track6-s3-lootbox-floor",
        "assertion",
    ),
    MigrationReservation(
        "0020",
        "0020_Track6S4DeleverageCooldown.py",
        "track6-s4-deleverage-cooldown",
        "omitted",
    ),
    MigrationReservation(
        "0030",
        "0030_Track6S5LedgerGuard.py",
        "track6-s5-ledger-guard",
        "assertion",
    ),
    MigrationReservation(
        "0040",
        "0040_Track6S6DefaultsAndParameters.py",
        "track6-s6-defaults-and-parameters",
        "assertion",
    ),
    MigrationReservation(
        "0050",
        "0050_Track6S7TimelockRegistryValidation.py",
        "track6-s7-timelock-registry-validation",
        "assertion",
    ),
    MigrationReservation(
        "0060",
        "0060_Track6S8LifecycleCapacity.py",
        "track6-s8-lifecycle-capacity",
        "assertion",
    ),
    MigrationReservation(
        "0070",
        "0070_Track6S9DisabledIntegrationAssertions.py",
        "track6-s9-disabled-integration-assertions",
        "assertion",
    ),
    MigrationReservation(
        "0080",
        "0080_Track6S10CadReportAssertion.py",
        "track6-s10-cad-report-assertion",
        "tooling_only",
    ),
    MigrationReservation(
        "0100",
        "0100_TokensAndRipeHq.py",
        "tokens-and-ripe-hq",
        "blocked",
    ),
    MigrationReservation(
        "0200",
        "0200_DataAndConfigRegistries.py",
        "data-and-config-registries",
        "blocked",
    ),
    MigrationReservation(
        "0300",
        "0300_Switchboards.py",
        "switchboards",
        "blocked",
    ),
    MigrationReservation(
        "0400",
        "0400_PriceSources.py",
        "price-sources",
        "blocked",
    ),
    MigrationReservation(
        "0500",
        "0500_VaultsAndAssets.py",
        "vaults-and-assets",
        "blocked",
        ("B-T8-FREEZE", "B-T8-M5"),
        (
            "Deployment.DP-10.aapl.identity",
            "Deployment.DP-10.aapl.feed",
            "Deployment.DP-10.aapl.decimals",
            "Deployment.DP-10.aapl.P8",
            "Deployment.DP-10.aapl.perUserCap",
            "Deployment.DP-10.aapl.globalCap",
            "Deployment.DP-10.aapl.vault",
            "Deployment.DP-10.aapl.risk",
            "Deployment.DP-10.aapl.auction",
            "Deployment.DP-10.aapl.route",
            "Deployment.DP-11.stock.vaultArtifact",
            "Deployment.DP-11.stock.vaultSlot",
            "Deployment.DP-11.stock.m2Movement",
            "Deployment.DP-11.stock.m3CreditContainment",
            "Deployment.DP-11.stock.m4ComposedProof",
            "Deployment.DP-11.stock.m5ActivationBinding",
        ),
    ),
    MigrationReservation(
        "0600",
        "0600_CoreDepartments.py",
        "core-departments",
        "blocked",
        ("B-REWARD-PROMOTION",),
    ),
    MigrationReservation(
        "0700",
        "0700_SavingsGreenPath.py",
        "savings-green-path",
        "blocked",
    ),
    MigrationReservation(
        "0800",
        "0800_EndaomentPsmDisabled.py",
        "endaoment-psm-disabled",
        "blocked",
        ("B-PSM-SEQUENCE",),
    ),
    MigrationReservation(
        "0900",
        "0900_CapabilitiesRolesAndHandoff.py",
        "capabilities-roles-and-handoff",
        "blocked",
    ),
    MigrationReservation(
        "1000",
        "1000_CcipPoolsAndRegistration.py",
        "ccip-pools-and-registration",
        "deferred",
        ("B-T1-CCIP", "B-T1-TOOLCHAIN"),
    ),
)

_REPORT_SCHEMA = "ripe.robinhood.migration-plan.v3"
_PRODUCTION_ARTIFACT_DOMAIN = b"ripe-robinhood-production-artifact-v1"
_PRODUCTION_PLAN_DOMAIN = b"ripe-robinhood-production-plan-v1"
_PREVIEW_ARTIFACT_DOMAIN = b"ripe-robinhood-preview-artifact-v1"
_SYNTHETIC_PROOF_DOMAIN = b"ripe-robinhood-synthetic-proof-v1"
_ARTIFACT_KINDS = {
    "production-plan",
    "preview-plan",
    "synthetic-proof",
}
_CANONICAL_FILENAME = re.compile(
    r"(?P<migration_id>[0-9]{4})_"
    r"(?P<semantic_name>[A-Za-z][A-Za-z0-9]*)\.py",
    re.ASCII,
)
_HEX64 = re.compile(r"[0-9a-f]{64}", re.ASCII)
_GIT = "/usr/bin/git"
_GIT_ENV = {"LANG": "C", "LC_ALL": "C"}

_SOURCE_RESERVATIONS = tuple(
    reservation
    for reservation in ROBINHOOD_RESERVATIONS
    if reservation.migration_id != "1000"
)
_STAGE_KINDS = {"assertion", "tooling-only", "deployment", "configuration", "handoff"}
_ACTION_KINDS = {
    "assertion",
    "omission",
    "deferred",
    "tooling-only",
    "deployment",
    "configuration",
    "registration",
    "blocked",
    "recovery",
    "handoff",
}
_NON_LAUNCH_ACTION_KINDS = {"omission", "deferred", "tooling-only", "blocked", "recovery"}
_ACTION_FIELDS = {
    "semantic_action_id",
    "kind",
    "operation",
    "component_id",
    "selection_state",
    "feature_families",
    "artifact",
    "constructor",
    "requires",
    "provides",
    "registry_ref",
    "postconditions",
    "abort_if",
    "when",
}
_SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*", re.ASCII)

_FIXED_PLANNING_INPUTS = (
    "config/BluePrint.py",
    "config/contract-artifact-expectations.json",
    "config/network_profiles.py",
    "config/robinhood-parameters.json",
    "config/robinhood_blueprint.py",
    "config/robinhood-reward-launch-plan.json",
    "contracts/config/DefaultsRobinhood.vy",
    "scripts/migrate.py",
    "scripts/utils/deployment_assertions.py",
    "scripts/utils/migration.py",
    "scripts/utils/migration_runner.py",
)


def robinhood_source_expectations() -> tuple[SourceExpectation, ...]:
    """Return the executable shared-source set; deferred 1000 has no file."""

    return tuple(
        SourceExpectation(
            reservation.migration_id,
            reservation.filename,
            reservation.semantic_id,
        )
        for reservation in _SOURCE_RESERVATIONS
    )


def _plain(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    if isinstance(value, list):
        return [_plain(item) for item in value]
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    return value


def _load_repository_module(root: Path, relative: str, label: str) -> Any:
    """Load one authority from ``root`` without consulting process imports."""

    path = root / relative
    name = f"_ripe_robinhood_{label}_{hashlib.sha256(str(path).encode()).hexdigest()}"
    module = types.ModuleType(name)
    module.__file__ = str(path)
    module.__package__ = ""
    sys.modules[name] = module
    try:
        source = _regular_input_bytes(root, relative)
        code = compile(source, str(path), "exec", dont_inherit=True)
        exec(code, module.__dict__)
    except MigrationPlanError:
        raise
    except Exception as error:
        raise MigrationPlanError("H05_PLANNING_INPUT_IMPORT") from error
    finally:
        sys.modules.pop(name, None)
    return module


def _load_blueprint(root: Path) -> Any:
    return _load_repository_module(root, "config/BluePrint.py", "blueprint")


def _load_network_profiles(root: Path) -> Any:
    return _load_repository_module(
        root, "config/network_profiles.py", "network_profiles"
    )


def _run_git(root: Path, arguments: Sequence[str], code: str) -> bytes:
    result = subprocess.run(
        [_GIT, *arguments],
        cwd=root,
        env=_GIT_ENV,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise MigrationPlanError(code)
    return result.stdout


def _require_index_head_parity(root: Path) -> None:
    result = subprocess.run(
        [_GIT, "diff", "--cached", "--quiet", "HEAD", "--"],
        cwd=root,
        env=_GIT_ENV,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise MigrationPlanError("H05_INDEX_NOT_HEAD")


def _require_clean_repository(root: Path) -> None:
    _require_index_head_parity(root)
    if _run_git(
        root,
        ["status", "--porcelain=v1", "-z", "--untracked-files=all"],
        "H05_REPOSITORY_STATUS",
    ):
        raise MigrationPlanError("H05_PRODUCTION_REPOSITORY_DIRTY")


def _git_object_id(kind: bytes, payload: bytes) -> bytes:
    header = kind + b" " + str(len(payload)).encode("ascii") + b"\0"
    return hashlib.sha1(header + payload).digest()


def _prospective_tree(root: Path) -> str:
    """Hash HEAD-index plus all non-ignored working bytes without writing Git."""

    _require_index_head_parity(root)
    paths = {
        item.decode("utf-8")
        for item in _run_git(
            root, ["ls-files", "-z"], "H05_SOURCE_GIT_IDENTITY"
        ).split(b"\0")
        if item
    }
    paths.update(
        item.decode("utf-8")
        for item in _run_git(
            root,
            ["ls-files", "--others", "--exclude-standard", "-z"],
            "H05_SOURCE_GIT_IDENTITY",
        ).split(b"\0")
        if item
    )
    root_node: dict[str, Any] = {}
    for relative in sorted(paths):
        path = root / relative
        try:
            details = path.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(details.st_mode):
            mode = "120000"
            payload = os.readlink(path).encode("utf-8")
        elif stat.S_ISREG(details.st_mode):
            mode = "100755" if details.st_mode & stat.S_IXUSR else "100644"
            payload = path.read_bytes()
        else:
            raise MigrationPlanError("H05_PROSPECTIVE_TREE_ENTRY")
        node = root_node
        parts = PurePosixPath(relative).parts
        for part in parts[:-1]:
            child = node.setdefault(part, {})
            if not isinstance(child, dict):
                raise MigrationPlanError("H05_PROSPECTIVE_TREE_ENTRY")
            node = child
        node[parts[-1]] = (mode, _git_object_id(b"blob", payload))

    def tree_oid(node: Mapping[str, Any]) -> bytes:
        records = []
        for name in sorted(
            node,
            key=lambda item: item.encode("utf-8")
            + (b"/" if isinstance(node[item], dict) else b""),
        ):
            value = node[name]
            if isinstance(value, dict):
                mode, oid = "40000", tree_oid(value)
            else:
                mode, oid = value
            records.append(
                mode.encode("ascii")
                + b" "
                + name.encode("utf-8")
                + b"\0"
                + oid
            )
        return _git_object_id(b"tree", b"".join(records))

    return tree_oid(root_node).hex()


def _regular_input_bytes(root: Path, relative: str) -> bytes:
    path = root / relative
    try:
        details = path.lstat()
    except FileNotFoundError as error:
        raise MigrationPlanError("H05_PLANNING_INPUT_MISSING") from error
    if stat.S_ISLNK(details.st_mode):
        raise MigrationPlanError("H05_PLANNING_INPUT_SYMLINK")
    if not stat.S_ISREG(details.st_mode):
        raise MigrationPlanError("H05_PLANNING_INPUT_INVALID")
    try:
        return path.read_bytes()
    except OSError as error:
        raise MigrationPlanError("H05_PLANNING_INPUT_UNREADABLE") from error


def _artifact_source_paths(
    root: Path, stages: Sequence[Mapping[str, Any]]
) -> tuple[str, ...]:
    paths = []
    for stage in stages:
        for action in stage["actions"]:
            if action["kind"] != "deployment":
                continue
            artifact = action.get("artifact")
            matches = tuple((root / "contracts").rglob(f"{artifact}.vy"))
            if len(matches) != 1:
                raise MigrationPlanError("H05_ARTIFACT_SOURCE_IDENTITY")
            paths.append(matches[0].relative_to(root).as_posix())
    return tuple(sorted(set(paths)))


def _planning_input_manifest(
    root: Path,
    stages: Sequence[Mapping[str, Any]],
    *,
    require_head: bool,
) -> list[dict[str, str]]:
    paths = set(_FIXED_PLANNING_INPUTS)
    paths.update(
        f"migrations/robinhood/{item.filename}"
        for item in robinhood_source_expectations()
    )
    paths.update(_artifact_source_paths(root, stages))
    records = []
    for relative in sorted(paths):
        payload = _regular_input_bytes(root, relative)
        if require_head:
            try:
                head_payload = _git_blob(root, relative)
            except MigrationPlanError as error:
                raise MigrationPlanError("H05_PLANNING_INPUT_NOT_HEAD") from error
            if payload != head_payload:
                raise MigrationPlanError("H05_PLANNING_INPUT_NOT_HEAD")
        records.append(
            {"path": relative, "sha256": hashlib.sha256(payload).hexdigest()}
        )
    return records


def _domain_hash(domain: bytes, value: Mapping[str, Any]) -> str:
    return hashlib.sha256(domain + b"\0" + canonical_jcs_bytes(value)).hexdigest()


def _stage_literal(path: Path) -> dict[str, Any]:
    try:
        tree = ast.parse(path.read_bytes(), filename=path.name)
    except (OSError, SyntaxError, UnicodeDecodeError) as error:
        raise MigrationPlanError("H05_SOURCE_SYNTAX") from error
    assignments = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "MIGRATION_STAGE"
    ]
    if len(assignments) != 1:
        raise MigrationPlanError("H05_STAGE_LITERAL_REQUIRED")
    try:
        stage = ast.literal_eval(assignments[0].value)
    except (ValueError, TypeError, SyntaxError) as error:
        raise MigrationPlanError("H05_STAGE_LITERAL_REQUIRED") from error
    if not isinstance(stage, dict):
        raise MigrationPlanError("H05_STAGE_SCHEMA")

    functions = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    if len(functions) != 1 or functions[0].name != "migrate":
        raise MigrationPlanError("H05_EXECUTION_BRIDGE_REQUIRED")
    calls = [node for node in ast.walk(functions[0]) if isinstance(node, ast.Call)]
    if len(calls) != 1:
        raise MigrationPlanError("H05_EXECUTION_BRIDGE_REQUIRED")
    call = calls[0]
    if not (
        isinstance(call.func, ast.Attribute)
        and isinstance(call.func.value, ast.Name)
        and call.func.value.id == "migration"
        and call.func.attr == "apply_robinhood_stage"
        and len(call.args) == 1
        and isinstance(call.args[0], ast.Name)
        and call.args[0].id == "MIGRATION_STAGE"
        and not call.keywords
    ):
        raise MigrationPlanError("H05_EXECUTION_BRIDGE_REQUIRED")
    return _plain(stage)


def _validate_stage(
    stage: Mapping[str, Any], expectation: SourceExpectation
) -> dict[str, Any]:
    if set(stage) != {"migration_id", "semantic_id", "stage_kind", "actions"}:
        raise MigrationPlanError("H05_STAGE_SCHEMA")
    if stage.get("migration_id") != expectation.migration_id:
        raise MigrationPlanError("H05_STAGE_ID_MISMATCH")
    if stage.get("semantic_id") != expectation.semantic_id:
        raise MigrationPlanError("H05_STAGE_SEMANTIC_MISMATCH")
    if stage.get("stage_kind") not in _STAGE_KINDS:
        raise MigrationPlanError("H05_STAGE_KIND")
    actions = stage.get("actions")
    if not isinstance(actions, list) or not actions:
        raise MigrationPlanError("H05_STAGE_ACTIONS_REQUIRED")
    seen: set[str] = set()
    for action in actions:
        if isinstance(action, dict) and "registry_id" in action:
            raise MigrationPlanError("H05_REGISTRY_ID_LOCAL_AUTHORITY")
        if not isinstance(action, dict) or not set(action).issubset(_ACTION_FIELDS):
            raise MigrationPlanError("H05_ACTION_SCHEMA")
        required = {"semantic_action_id", "kind", "operation", "postconditions"}
        if not required.issubset(action):
            raise MigrationPlanError("H05_ACTION_SCHEMA")
        action_id = action["semantic_action_id"]
        if not isinstance(action_id, str) or _SLUG.fullmatch(action_id) is None:
            raise MigrationPlanError("H05_ACTION_ID")
        if action_id in seen:
            raise MigrationPlanError("H05_ACTION_DUPLICATE")
        seen.add(action_id)
        if action["kind"] not in _ACTION_KINDS:
            raise MigrationPlanError("H05_ACTION_KIND")
        postconditions = action["postconditions"]
        if not isinstance(postconditions, list) or not postconditions:
            raise MigrationPlanError("H05_ACTION_POSTCONDITION")
        for field in ("constructor", "requires", "provides", "postconditions", "abort_if", "feature_families"):
            if field in action and (
                not isinstance(action[field], list)
                or not all(isinstance(item, str) and item for item in action[field])
            ):
                raise MigrationPlanError("H05_ACTION_SCHEMA")
            if field in action and len(action[field]) != len(set(action[field])):
                raise MigrationPlanError("H05_ACTION_LIST_DUPLICATE")
        rendered = canonical_jcs_bytes(action).decode("utf-8")
        if "0x" in rendered or "base-mainnet" in rendered or "pr-66" in rendered:
            raise MigrationPlanError("H05_LOCAL_VALUE_FORBIDDEN")
    return dict(stage)


def load_robinhood_stages(
    repository_root: str | os.PathLike[str],
    discovery: DiscoveryResult | None = None,
) -> tuple[dict[str, Any], ...]:
    """Load validated literal stages without importing migration modules."""

    root = _absolute_repository_root(repository_root)
    expectations = robinhood_source_expectations()
    if discovery is None:
        discovery = discover_migration_sources(
            root,
            PurePosixPath("migrations/robinhood"),
            expectations,
            require_tracked=False,
            forbid_base_blobs=True,
        )
    if [member.migration_id for member in discovery.members] != [
        item.migration_id for item in expectations
    ]:
        raise MigrationPlanError("H05_SOURCE_ORDER")
    stages = []
    all_action_ids: set[str] = set()
    for expectation in expectations:
        path = root / "migrations/robinhood" / expectation.filename
        stage = _validate_stage(_stage_literal(path), expectation)
        for action in stage["actions"]:
            action_id = action["semantic_action_id"]
            for reference in action.get("requires", []):
                if reference.startswith("action:") and reference[7:] not in all_action_ids:
                    raise MigrationPlanError("H05_ACTION_ORDER")
            all_action_ids.add(action_id)
        stages.append(stage)
    return tuple(stages)


def _blocker_code(prefix: str, reference: str) -> str:
    suffix = re.sub(r"[^A-Za-z0-9]+", "_", reference).strip("_").upper()
    return f"H05_{prefix}_{suffix}_PENDING"


def _defaults_contract_checks(root: Path, blueprint: Any, stages: Sequence[Mapping[str, Any]]) -> None:
    source = (root / "contracts/config/DefaultsRobinhood.vy").read_text(encoding="utf-8")
    if re.search(r"def priorityPriceSourceIds\(\).*?return \[1, 3\]", source, re.S) is None:
        raise MigrationPlanError("H05_DEFAULTS_PRIORITY_MISMATCH")
    defaults_action = next(
        action
        for stage in stages
        for action in stage["actions"]
        if action["semantic_action_id"] == "deploy-defaults-robinhood"
    )
    expected = [
        f"address:{authority_key}"
        for _, authority_key in blueprint.ROBINHOOD_DEFAULTS_CONSTRUCTOR
    ]
    if defaults_action.get("constructor") != expected:
        raise MigrationPlanError("H05_DEFAULTS_CONSTRUCTOR_MISMATCH")


def _constructor_argument_count(source: str) -> int:
    match = re.search(r"@deploy\s+def __init__\((.*?)\)\s*:", source, re.S)
    if match is None:
        return 0
    return len(re.findall(r"(?:^|,)\s*_[A-Za-z][A-Za-z0-9_]*\s*:", match.group(1)))


def _constructor_shape_checks(root: Path, stages: Sequence[Mapping[str, Any]]) -> None:
    for stage in stages:
        for action in stage["actions"]:
            if action["kind"] != "deployment":
                continue
            artifact = action.get("artifact")
            matches = tuple((root / "contracts").rglob(f"{artifact}.vy"))
            if len(matches) != 1:
                raise MigrationPlanError("H05_ARTIFACT_SOURCE_IDENTITY")
            expected_count = _constructor_argument_count(
                matches[0].read_text(encoding="utf-8")
            )
            if len(action.get("constructor", [])) != expected_count:
                raise MigrationPlanError("H05_CONSTRUCTOR_ARGUMENT_COUNT")


def _validate_curve_authority(blueprint: Any) -> None:
    component = next(
        (
            row
            for row in blueprint.ROBINHOOD_COMPONENT_SELECTIONS
            if row.component_id == "CM-017"
        ),
        None,
    )
    registry = next(
        (
            row
            for row in blueprint.ROBINHOOD_REGISTRY_TOPOLOGY
            if row.domain == "price_desk"
            and row.component_id == "CM-017"
            and row.registry_id == 2
        ),
        None,
    )
    launch_rows = _curve_input_rows(blueprint)
    required_launch_ids = {
        "launch.chain_id",
        "launch.component",
        "launch.price_desk_registration_order",
        "launch.priority_price_source_ids",
    }
    if not required_launch_ids.issubset(launch_rows):
        raise MigrationPlanError("H05_CURVE_AUTHORITY_MISMATCH")
    expected_order = (
        (1, "ChainlinkPrices"),
        (2, "CurvePrices"),
        (3, "BlueChipYieldPrices"),
    )
    if not (
        component is not None
        and component.deployment_disposition == "required"
        and component.selection_state == "selected"
        and registry is not None
        and registry.disposition == "required"
        and registry.selection_state == "selected"
        and launch_rows["launch.chain_id"].value
        == blueprint.ROBINHOOD_CHAIN["mainnet_chain_id"]
        == 4663
        and launch_rows["launch.component"].value == "CM-017:CurvePrices"
        and launch_rows["launch.price_desk_registration_order"].value
        == expected_order
        and launch_rows["launch.priority_price_source_ids"].value == (1, 3)
        and blueprint.ROBINHOOD_COMPONENTS.get("curve_launch")
        == {
            "component_id": "CM-017",
            "registry_id": 2,
            "configured_assets": ("GREEN",),
            "priority_ids": (1, 3),
        }
    ):
        raise MigrationPlanError("H05_CURVE_AUTHORITY_MISMATCH")


def _curve_input_rows(blueprint: Any) -> dict[str, Any]:
    rows = tuple(getattr(blueprint, "ROBINHOOD_CURVE_LAUNCH_INPUTS", ()))
    result = {row.input_id: row for row in rows}
    if len(result) != len(rows):
        raise MigrationPlanError("H05_CURVE_INPUT_DUPLICATE")
    return result


def _stock_input_rows(blueprint: Any) -> dict[str, Any]:
    rows = tuple(
        getattr(blueprint, "ROBINHOOD_STOCK_INPUT_QUALIFICATIONS", ())
    )
    result = {row.path: row for row in rows}
    if len(result) != len(rows):
        raise MigrationPlanError("H05_STOCK_INPUT_DUPLICATE")
    return result


def _validate_stock_authority(blueprint: Any) -> None:
    rows = _stock_input_rows(blueprint)
    reservation = next(
        item for item in ROBINHOOD_RESERVATIONS if item.migration_id == "0500"
    )
    resolved = {
        path
        for path, row in rows.items()
        if row.resolution == "repository_fact_integrated"
    }
    if not (
        tuple(rows) == reservation.input_bindings
        and len(rows) == 16
        and len(resolved) == 4
        and len(rows) - len(resolved) == 12
        and blueprint.ROBINHOOD_INITIAL_STOCK_SYMBOLS == ("AAPL",)
        and tuple(blueprint.ROBINHOOD_STOCK_UNRESOLVED_INPUT_PATHS)
        == tuple(path for path in rows if path not in resolved)
    ):
        raise MigrationPlanError("H05_STOCK_AUTHORITY_MISMATCH")


def _validate_authority_reference_coverage(
    stages: Sequence[Mapping[str, Any]], blueprint: Any
) -> None:
    references = [
        reference
        for stage in stages
        for action in stage["actions"]
        for reference in action.get("constructor", [])
        + action.get("requires", [])
    ]
    curve_references = {
        reference[6:]
        for reference in references
        if reference.startswith("curve:")
    }
    if curve_references != set(_curve_input_rows(blueprint)):
        raise MigrationPlanError("H05_CURVE_INPUT_COVERAGE")
    stock_references = tuple(
        reference[6:]
        for reference in references
        if reference.startswith("stock:")
    )
    if stock_references != tuple(_stock_input_rows(blueprint)):
        raise MigrationPlanError("H05_STOCK_INPUT_COVERAGE")


def _registry_authority(blueprint: Any) -> dict[tuple[str, str], Any]:
    result = {}
    for row in blueprint.ROBINHOOD_REGISTRY_TOPOLOGY:
        key = (row.domain, row.component_id)
        if key in result:
            raise MigrationPlanError("H05_REGISTRY_COMPONENT_DUPLICATE")
        result[key] = row
    return result


def _resolve_reference(
    reference: str,
    *,
    blueprint: Any,
    produced: set[str],
    prior_actions: set[str],
) -> str | None:
    if reference.startswith("action:"):
        return None if reference[7:] in prior_actions else "H05_ACTION_ORDER"
    if reference.startswith("address:"):
        key = reference[8:]
        if reference in produced:
            return None
        status = blueprint.ROBINHOOD_ADDRESS_STATUS.get(key)
        if status == "approved_semantic_absence":
            return None
        if status is None:
            return _blocker_code("ADDRESS", key)
        if status == "deployment_produced_unresolved":
            return _blocker_code("DEPLOYMENT_OUTPUT", key)
        return _blocker_code("EXTERNAL", key)
    if reference.startswith("input-prefix:"):
        prefix = reference[13:]
        rows = [
            row
            for key, row in blueprint.ROBINHOOD_DEPLOYMENT_INPUTS.items()
            if key.startswith(prefix)
        ]
        if not rows:
            return "H05_INPUT_PREFIX_UNKNOWN"
        return None if all(row.disposition in {"approved", "disabled"} for row in rows) else _blocker_code("INPUT_PREFIX", prefix)
    if reference.startswith("input:"):
        key = reference[6:]
        row = blueprint.ROBINHOOD_DEPLOYMENT_INPUTS.get(key)
        if row is None:
            return _blocker_code("INPUT_AUTHORITY", key)
        if row.disposition in {"approved", "disabled"}:
            return None
        return _blocker_code("INPUT", key)
    if reference.startswith("curve:"):
        input_id = reference[6:]
        row = _curve_input_rows(blueprint).get(input_id)
        if row is None:
            raise MigrationPlanError("H05_CURVE_INPUT_UNKNOWN")
        if row.resolution_state in blueprint.ROBINHOOD_CURVE_BLOCKING_STATES:
            return _blocker_code("CURVE", input_id)
        return None
    if reference.startswith("curve-binding:"):
        argument = reference[14:]
        row = _curve_input_rows(blueprint).get("curve.constructor_bindings")
        if row is None:
            raise MigrationPlanError("H05_CURVE_AUTHORITY_MISMATCH")
        try:
            bindings = dict(row.value)
        except (TypeError, ValueError):
            raise MigrationPlanError(
                "H05_CURVE_AUTHORITY_MISMATCH"
            ) from None
        if argument not in bindings:
            raise MigrationPlanError(
                "H05_CURVE_CONSTRUCTOR_BINDING_UNKNOWN"
            )
        return None
    if reference.startswith("stock:"):
        input_path = reference[6:]
        row = _stock_input_rows(blueprint).get(input_path)
        if row is None:
            raise MigrationPlanError("H05_STOCK_INPUT_UNKNOWN")
        if row.resolution != "repository_fact_integrated":
            return _blocker_code("STOCK", input_path)
        return None
    if reference.startswith("binding:"):
        return _blocker_code("BINDING", reference[8:])
    if reference.startswith("defaults:"):
        return None
    if reference.startswith("blueprint:"):
        return None
    return "H05_REFERENCE_UNKNOWN"


def build_robinhood_plan(
    profile_id: str,
    *,
    repository_root: str | os.PathLike[str],
    synthetic_bindings: Mapping[str, Any] | None = None,
    synthetic_bind_all: bool = False,
    preview: bool = False,
) -> dict[str, Any]:
    """Construct the complete offline plan from shared source and authority."""

    root = _absolute_repository_root(repository_root)
    if synthetic_bindings is not None and not synthetic_bind_all:
        raise MigrationPlanError("H05_SYNTHETIC_BIND_ALL_REQUIRED")
    synthetic = synthetic_bind_all or synthetic_bindings is not None
    if preview and synthetic:
        raise MigrationPlanError("H05_PLAN_MODE_CONFLICT")
    artifact_kind = (
        "synthetic-proof"
        if synthetic
        else "preview-plan"
        if preview
        else "production-plan"
    )
    if artifact_kind == "production-plan":
        _require_clean_repository(root)
        commit, tree = _git_identity(root)
    else:
        commit, base_tree = _git_identity(root)
        tree = _prospective_tree(root)

    profiles = _load_network_profiles(root)
    profile = profiles.get_profile(profile_id)
    if profile.identity.chain_id is None:
        raise MigrationPlanError("H05_PLAN_UNSUPPORTED")
    expectations = robinhood_source_expectations()
    discovery = discover_migration_sources(
        root,
        PurePosixPath("migrations/robinhood"),
        expectations,
        require_tracked=artifact_kind == "production-plan",
        forbid_base_blobs=True,
    )
    stages = load_robinhood_stages(root, discovery)
    input_manifest = _planning_input_manifest(
        root,
        stages,
        require_head=artifact_kind == "production-plan",
    )
    blueprint = _load_blueprint(root)
    _defaults_contract_checks(root, blueprint, stages)
    _constructor_shape_checks(root, stages)
    _validate_curve_authority(blueprint)
    _validate_stock_authority(blueprint)
    _validate_authority_reference_coverage(stages, blueprint)
    registry = _registry_authority(blueprint)
    component_rows = {
        row.component_id: row for row in blueprint.ROBINHOOD_COMPONENT_SELECTIONS
    }
    produced: set[str] = set()
    prior_actions: set[str] = set()
    blockers: set[str] = set()
    blocker_references: dict[str, set[str]] = {}
    deployment_counts: dict[str, int] = {}
    registration_counts: dict[tuple[str, str], int] = {}
    price_registration_sequence: list[tuple[str, int]] = []
    represented_components: set[str] = set()
    planned_stages = []

    for stage_ordinal, stage in enumerate(stages):
        reservation = _SOURCE_RESERVATIONS[stage_ordinal]
        if reservation.migration_id != stage["migration_id"]:
            raise MigrationPlanError("H05_RESERVATION_MISMATCH")
        stage_blockers = set(reservation.local_blockers)
        blockers.update(stage_blockers)
        for blocker in stage_blockers:
            blocker_references.setdefault(blocker, set()).add(
                f"reservation:{reservation.migration_id}"
            )
        planned_actions = []
        for action_ordinal, raw_action in enumerate(stage["actions"]):
            action = dict(raw_action)
            component_id = action.get("component_id")
            if component_id is not None:
                if component_id not in component_rows:
                    raise MigrationPlanError("H05_COMPONENT_UNKNOWN")
                if "selection_state" in action:
                    raise MigrationPlanError(
                        "H05_SELECTION_STATE_LOCAL_AUTHORITY"
                    )
                represented_components.add(component_id)
            if action["kind"] == "deployment":
                if action.get("artifact") != component_rows[
                    component_id
                ].semantic_name:
                    raise MigrationPlanError(
                        "H05_COMPONENT_ARTIFACT_MISMATCH"
                    )
                deployment_counts[component_id] = deployment_counts.get(component_id, 0) + 1
                if component_rows[component_id].selection_state in {"omitted", "deferred"}:
                    raise MigrationPlanError("H05_UNAVAILABLE_COMPONENT_DEPLOYED")
            registry_data = None
            registry_ref = action.get("registry_ref")
            if registry_ref is not None:
                match = re.fullmatch(r"registry:([a-z_]+):(CM-[0-9]{3})", registry_ref)
                if match is None:
                    raise MigrationPlanError("H05_REGISTRY_REFERENCE")
                key = (match.group(1), match.group(2))
                row = registry.get(key)
                if row is None:
                    raise MigrationPlanError("H05_REGISTRY_REFERENCE")
                registry_data = {
                    "domain": row.domain,
                    "registry_id": row.registry_id,
                    "semantic_name": row.semantic_name,
                    "component_id": row.component_id,
                    "disposition": row.disposition,
                    "selection_state": row.selection_state,
                }
                if action["kind"] == "registration":
                    registration_counts[key] = registration_counts.get(key, 0) + 1
                    if row.domain == "price_desk":
                        price_registration_sequence.append(
                            (row.component_id, row.registry_id)
                        )
                    if row.selection_state not in {"selected", "blocked"}:
                        raise MigrationPlanError("H05_RESERVED_REGISTRY_REUSED")

            action_blockers: set[str] = set()
            references = list(action.get("constructor", [])) + list(action.get("requires", []))
            should_resolve = action["kind"] not in _NON_LAUNCH_ACTION_KINDS or any(
                reference.startswith(("stock:", "binding:reward-"))
                for reference in references
            )
            if should_resolve:
                for reference in references:
                    blocker = _resolve_reference(
                        reference,
                        blueprint=blueprint,
                        produced=produced,
                        prior_actions=prior_actions,
                    )
                    if blocker is not None:
                        action_blockers.add(blocker)
                        blockers.add(blocker)
                        blocker_references.setdefault(blocker, set()).add(reference)
            for provided in action.get("provides", []):
                if provided in produced:
                    raise MigrationPlanError("H05_OUTPUT_DUPLICATE")
                produced.add(provided)
            prior_actions.add(action["semantic_action_id"])
            planned = dict(action)
            planned["action_id"] = f"{stage['migration_id']}:{action_ordinal:06d}:{action['semantic_action_id']}"
            planned["ordinal"] = action_ordinal
            planned["component_authority"] = (
                {
                    "deployment_disposition": component_rows[
                        component_id
                    ].deployment_disposition,
                    "selection_state": component_rows[
                        component_id
                    ].selection_state,
                }
                if component_id is not None
                else None
            )
            planned["registry"] = registry_data
            planned["blockers"] = sorted(action_blockers)
            planned["status"] = (
                "proof-overridden"
                if synthetic and action_blockers
                else "blocked"
                if action_blockers
                else "planned"
            )
            planned_actions.append(planned)
        planned_stages.append(
            {
                "migration_id": stage["migration_id"],
                "semantic_id": stage["semantic_id"],
                "stage_kind": stage["stage_kind"],
                "reservation_disposition": reservation.disposition,
                "input_bindings": list(reservation.input_bindings),
                "ordinal": stage_ordinal,
                "status": (
                    "proof-overridden"
                    if synthetic
                    and (
                        stage_blockers
                        or any(action["blockers"] for action in planned_actions)
                    )
                    else "blocked"
                    if stage_blockers
                    or any(action["blockers"] for action in planned_actions)
                    else "planned"
                ),
                "blockers": sorted(stage_blockers),
                "action_count": len(planned_actions),
                "actions": planned_actions,
            }
        )

    duplicate_deployments = sorted(
        component for component, count in deployment_counts.items() if count != 1
    )
    if duplicate_deployments:
        raise MigrationPlanError("H05_COMPONENT_DEPLOYMENT_DUPLICATE")

    target_selected = {
        row.component_id
        for row in blueprint.ROBINHOOD_COMPONENT_SELECTIONS
        if row.selection_state == "selected"
    }
    target_blocked = {
        row.component_id
        for row in blueprint.ROBINHOOD_COMPONENT_SELECTIONS
        if row.selection_state == "blocked"
    }
    target_planned = target_selected | target_blocked
    missing_components = target_planned - represented_components
    if missing_components:
        raise MigrationPlanError("H05_SELECTED_COMPONENT_MISSING")
    contract_artifacts = {
        path.stem for path in (root / "contracts").rglob("*.vy")
    }
    deployable_components = {
        row.component_id
        for row in blueprint.ROBINHOOD_COMPONENT_SELECTIONS
        if row.component_id in target_planned
        and row.semantic_name in contract_artifacts
    }
    if set(deployment_counts) != deployable_components:
        raise MigrationPlanError("H05_COMPONENT_DEPLOYMENT_COVERAGE")

    target_registrations = {
        (row.domain, row.component_id)
        for row in blueprint.ROBINHOOD_REGISTRY_TOPOLOGY
        if row.selection_state in {"selected", "blocked"}
    }
    if set(registration_counts) != target_registrations or any(
        count != 1 for count in registration_counts.values()
    ):
        raise MigrationPlanError("H05_REGISTRY_COVERAGE")
    if price_registration_sequence != [
        ("CM-016", 1),
        ("CM-017", 2),
        ("CM-018", 3),
    ]:
        raise MigrationPlanError("H05_PRICE_REGISTRY_ORDER")

    all_actions = [
        action for stage in planned_stages for action in stage["actions"]
    ]
    deployment_action_ids = [
        action["action_id"]
        for action in all_actions
        if action["kind"] == "deployment"
    ]
    registration_action_ids = [
        action["action_id"]
        for action in all_actions
        if action["kind"] == "registration"
    ]
    action_census = {
        "total": len(all_actions),
        "deployments": len(deployment_action_ids),
        "registrations": len(registration_action_ids),
        "all_action_ids": [action["action_id"] for action in all_actions],
        "deployment_action_ids": deployment_action_ids,
        "registration_action_ids": registration_action_ids,
    }
    if action_census["total"] != 117:
        raise MigrationPlanError("H05_ACTION_CENSUS")
    if action_census["deployments"] != 37:
        raise MigrationPlanError("H05_DEPLOYMENT_CENSUS")
    if action_census["registrations"] != 33:
        raise MigrationPlanError("H05_REGISTRATION_CENSUS")

    blocker_details = [
        {"key": key, "references": sorted(blocker_references.get(key, set()))}
        for key in sorted(blockers)
    ]
    source = {
        "commit": commit if artifact_kind == "production-plan" else None,
        "tree": tree,
        "source_digest": discovery.source_digest,
        "members": [
            {
                "migration_id": member.migration_id,
                "filename": member.filename,
                "semantic_id": member.semantic_id,
                "sha256": member.sha256,
            }
            for member in discovery.members
        ],
        "planning_inputs": input_manifest,
    }
    if artifact_kind != "production-plan":
        source["base_commit"] = commit
        source["base_tree"] = base_tree

    plan_core = {
        "artifact": {
            "kind": artifact_kind,
            "profile_kind": (
                "synthetic-proof"
                if synthetic
                else "robinhood-network-preview"
                if preview
                else "robinhood-network-production"
            ),
            "production": artifact_kind == "production-plan",
            "executable": artifact_kind == "production-plan" and not blockers,
            "history_eligible": artifact_kind == "production-plan" and not blockers,
            "identity_domain": (
                _SYNTHETIC_PROOF_DOMAIN.decode("ascii")
                if synthetic
                else _PREVIEW_ARTIFACT_DOMAIN.decode("ascii")
                if preview
                else _PRODUCTION_ARTIFACT_DOMAIN.decode("ascii")
            ),
        },
        "profile": {
            "profile_id": (
                "robinhood-synthetic-proof" if synthetic else profile_id
            ),
            "base_profile_id": profile_id if synthetic else None,
            "expected_chain_id": profile.identity.chain_id,
        },
        "source": source,
        "stages": planned_stages,
        "deferred_stages": [
            {
                "migration_id": "1000",
                "semantic_id": "ccip-pools-and-registration",
                "reason": "ccip-deferred-outside-launch-graph",
            }
        ],
        "component_coverage": {
            "selected": sorted(target_selected),
            "blocked": sorted(target_blocked),
            "represented": sorted(represented_components & target_planned),
            "omitted": sorted(
                row.component_id for row in blueprint.ROBINHOOD_COMPONENT_SELECTIONS if row.selection_state == "omitted"
            ),
            "deferred": sorted(
                row.component_id for row in blueprint.ROBINHOOD_COMPONENT_SELECTIONS if row.selection_state == "deferred"
            ),
        },
        "registry_coverage": [
            {
                "domain": domain,
                "component_id": component,
                "count": registration_counts[(domain, component)],
            }
            for domain, component in sorted(registration_counts)
        ],
        "action_census": action_census,
        "blocker_details": blocker_details,
        "blockers": sorted(blockers),
        "synthetic_authority_overrides": (
            [
                {
                    "key": detail["key"],
                    "real_disposition": "blocked",
                    "references": detail["references"],
                    "scope": "synthetic-proof-only",
                }
                for detail in blocker_details
            ]
            if synthetic
            else []
        ),
    }
    expectation_digest = hashlib.sha256(
        canonical_jcs_bytes(
            {
                "action_census": action_census,
                "actions": [
                    {
                        "action_id": action["action_id"],
                        "postconditions": action["postconditions"],
                        "registry": action["registry"],
                    }
                    for action in all_actions
                ],
            }
        )
    ).hexdigest()
    result = dict(plan_core)
    result["status"] = (
        "proof-complete"
        if synthetic_bind_all
        else "blocked"
        if blockers
        else "complete"
    )
    result["expectation_digest"] = expectation_digest
    result["plan_hash"] = None
    result["proof_hash"] = None
    result["preview_hash"] = None
    result["artifact_hash"] = _domain_hash(
        _SYNTHETIC_PROOF_DOMAIN
        if synthetic
        else _PREVIEW_ARTIFACT_DOMAIN
        if preview
        else _PRODUCTION_ARTIFACT_DOMAIN,
        _plan_identity_payload(result),
    )
    if synthetic:
        result["proof_hash"] = result["artifact_hash"]
    elif preview:
        result["preview_hash"] = result["artifact_hash"]
    elif not blockers:
        result["plan_hash"] = _domain_hash(
            _PRODUCTION_PLAN_DOMAIN, _plan_identity_payload(result)
        )

    final_manifest = _planning_input_manifest(
        root,
        stages,
        require_head=artifact_kind == "production-plan",
    )
    if final_manifest != input_manifest:
        raise MigrationPlanError("H05_PLANNING_INPUT_DRIFT")
    if artifact_kind == "production-plan":
        _require_clean_repository(root)
        if _git_identity(root) != (commit, tree):
            raise MigrationPlanError("H05_REPOSITORY_IDENTITY_DRIFT")
    elif _prospective_tree(root) != tree:
        raise MigrationPlanError("H05_PROSPECTIVE_TREE_DRIFT")
    return result


def _validate_unicode_string(value: str) -> None:
    try:
        value.encode("utf-8", "strict")
        value.encode("utf-16-be", "strict")
    except UnicodeEncodeError as error:
        raise MigrationPlanError("H05_JCS_UNICODE") from error


def _jcs_string(value: str) -> str:
    _validate_unicode_string(value)
    pieces = ['"']
    short_escapes = {
        "\b": "\\b",
        "\t": "\\t",
        "\n": "\\n",
        "\f": "\\f",
        "\r": "\\r",
        '"': '\\"',
        "\\": "\\\\",
    }
    for character in value:
        if character in short_escapes:
            pieces.append(short_escapes[character])
        elif ord(character) < 0x20:
            pieces.append(f"\\u{ord(character):04x}")
        else:
            pieces.append(character)
    pieces.append('"')
    return "".join(pieces)


def _jcs_text(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        raise MigrationPlanError("H05_JCS_FLOAT_FORBIDDEN")
    if isinstance(value, str):
        return _jcs_string(value)
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(_jcs_text(item) for item in value) + "]"
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise MigrationPlanError("H05_JCS_KEY_TYPE")
        for key in value:
            _validate_unicode_string(key)
        keys = sorted(value, key=lambda key: key.encode("utf-16-be"))
        return (
            "{"
            + ",".join(
                f"{_jcs_string(key)}:{_jcs_text(value[key])}"
                for key in keys
            )
            + "}"
        )
    raise MigrationPlanError("H05_JCS_TYPE")


def canonical_jcs_bytes(value: Any) -> bytes:
    """Canonicalize the integer-only H-05 JSON domain without a final LF."""

    return _jcs_text(value).encode("utf-8")


def _plan_identity_payload(plan: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(plan)
    for field in ("artifact_hash", "plan_hash", "preview_hash", "proof_hash"):
        payload.pop(field, None)
    return payload


def _validate_artifact_action_census(plan: Mapping[str, Any]) -> None:
    stages = plan.get("stages")
    census = plan.get("action_census")
    if not isinstance(stages, list) or not isinstance(census, Mapping):
        raise MigrationPlanError("H05_ACTION_CENSUS")
    try:
        actions = [
            action
            for stage in stages
            for action in stage["actions"]
        ]
        action_ids = [action["action_id"] for action in actions]
        deployment_ids = [
            action["action_id"]
            for action in actions
            if action["kind"] == "deployment"
        ]
        registration_ids = [
            action["action_id"]
            for action in actions
            if action["kind"] == "registration"
        ]
    except (KeyError, TypeError):
        raise MigrationPlanError("H05_ACTION_CENSUS") from None
    expected = {
        "total": 117,
        "deployments": 37,
        "registrations": 33,
        "all_action_ids": action_ids,
        "deployment_action_ids": deployment_ids,
        "registration_action_ids": registration_ids,
    }
    if dict(census) != expected:
        raise MigrationPlanError("H05_ACTION_CENSUS")


def report_bytes(report: Mapping[str, Any]) -> bytes:
    """Seal a report with its H-05 self-hash and one terminal LF."""

    unsigned = dict(report)
    unsigned.pop("report_sha256", None)
    digest = hashlib.sha256(canonical_jcs_bytes(unsigned)).hexdigest()
    sealed = dict(unsigned)
    sealed["report_sha256"] = digest
    return canonical_jcs_bytes(sealed) + b"\n"


def report_sha256(report: Mapping[str, Any]) -> str:
    """Return the report self-hash without confusing it with H-06 plan_sha256."""

    unsigned = dict(report)
    unsigned.pop("report_sha256", None)
    return hashlib.sha256(canonical_jcs_bytes(unsigned)).hexdigest()


def _reservation_records() -> list[dict[str, Any]]:
    return [
        {
            "migration_id": item.migration_id,
            "filename": item.filename,
            "semantic_id": item.semantic_id,
            "disposition": item.disposition,
            "blockers": list(item.local_blockers),
            "input_bindings": list(item.input_bindings),
        }
        for item in ROBINHOOD_RESERVATIONS
    ]


RESERVATION_DIGEST = hashlib.sha256(
    canonical_jcs_bytes(_reservation_records())
).hexdigest()


def _safe_repository_path(value: PurePosixPath | str) -> PurePosixPath:
    raw = str(value)
    if (
        not raw
        or "\\" in raw
        or raw.startswith("/")
        or "://" in raw
    ):
        raise MigrationPlanError("H05_PATH_INVALID")
    normalized = PurePosixPath(raw)
    if (
        raw != normalized.as_posix()
        or normalized.is_absolute()
        or any(
        part in {"", ".", ".."} for part in normalized.parts
        )
    ):
        raise MigrationPlanError("H05_PATH_INVALID")
    return normalized


def _absolute_repository_root(value: str | os.PathLike[str]) -> Path:
    root = Path(value)
    if not root.is_absolute():
        raise MigrationPlanError("H05_REPOSITORY_ROOT_INVALID")
    try:
        details = root.lstat()
    except OSError as error:
        raise MigrationPlanError("H05_REPOSITORY_ROOT_INVALID") from error
    if stat.S_ISLNK(details.st_mode) or not stat.S_ISDIR(details.st_mode):
        raise MigrationPlanError("H05_REPOSITORY_ROOT_INVALID")
    return root


def _join_repository_path(root: Path, relative: PurePosixPath | str) -> Path:
    path = _safe_repository_path(relative)
    selected = root.joinpath(*path.parts)
    try:
        selected.relative_to(root)
    except ValueError as error:
        raise MigrationPlanError("H05_PATH_ESCAPE") from error
    return selected


def _validate_expectations(
    expectations: Sequence[SourceExpectation],
) -> tuple[SourceExpectation, ...]:
    items = tuple(expectations)
    ids = [item.migration_id for item in items]
    semantics = [item.semantic_id for item in items]
    if any(
        re.fullmatch(r"[0-9]{4}", migration_id, re.ASCII) is None
        for migration_id in ids
    ):
        raise MigrationPlanError("H05_RESERVATION_ID")
    if len(ids) != len(set(ids)):
        raise MigrationPlanError("H05_DUPLICATE_NUMERIC_ID")
    if len(semantics) != len(set(semantics)):
        raise MigrationPlanError("H05_DUPLICATE_SEMANTIC_ID")
    if ids != sorted(ids, key=int):
        raise MigrationPlanError("H05_RESERVATION_ORDER")
    for item in items:
        match = _CANONICAL_FILENAME.fullmatch(item.filename)
        if match is None or match.group("migration_id") != item.migration_id:
            raise MigrationPlanError("H05_RESERVATION_MISMATCH")
        if item.sha256 is not None and _HEX64.fullmatch(item.sha256) is None:
            raise MigrationPlanError("H05_SOURCE_HASH_INVALID")
    return items


def _git_blob(root: Path, relative_path: str) -> bytes:
    tracked = subprocess.run(
        [_GIT, "ls-files", "--error-unmatch", "--", relative_path],
        cwd=root,
        env=_GIT_ENV,
        capture_output=True,
        check=False,
    )
    if tracked.returncode != 0:
        raise MigrationPlanError("H05_SOURCE_UNTRACKED")
    blob = subprocess.run(
        [_GIT, "cat-file", "blob", f"HEAD:{relative_path}"],
        cwd=root,
        env=_GIT_ENV,
        capture_output=True,
        check=False,
    )
    if blob.returncode != 0:
        raise MigrationPlanError("H05_SOURCE_UNTRACKED")
    return blob.stdout


def _base_source_digests(root: Path) -> frozenset[str]:
    base_root = root / "migrations/base-mainnet"
    try:
        details = base_root.lstat()
    except FileNotFoundError:
        return frozenset()
    if stat.S_ISLNK(details.st_mode) or not stat.S_ISDIR(details.st_mode):
        raise MigrationPlanError("H05_BASE_NAMESPACE_INVALID")
    digests = set()
    with os.scandir(base_root) as entries:
        for entry in entries:
            if entry.is_symlink():
                raise MigrationPlanError("H05_BASE_NAMESPACE_INVALID")
            if entry.is_file(follow_symlinks=False) and entry.name.endswith(
                ".py"
            ):
                digests.add(
                    hashlib.sha256(Path(entry.path).read_bytes()).hexdigest()
                )
    return frozenset(digests)


def discover_migration_sources(
    repository_root: str | os.PathLike[str],
    source_root: PurePosixPath | str,
    expectations: Sequence[SourceExpectation],
    *,
    require_tracked: bool = True,
    forbid_base_blobs: bool = True,
) -> DiscoveryResult:
    """Discover one exact, flat migration set without importing any module."""

    root = _absolute_repository_root(repository_root)
    source_relative = _safe_repository_path(source_root)
    if source_relative.parts[:2] == ("migrations", "base-mainnet"):
        raise MigrationPlanError("H05_BASE_NAMESPACE_FORBIDDEN")
    source = _join_repository_path(root, source_relative)
    expected = _validate_expectations(expectations)
    expected_by_name = {item.filename: item for item in expected}
    try:
        root_details = source.lstat()
    except FileNotFoundError as error:
        raise MigrationPlanError("H05_SOURCE_ABSENT") from error
    if stat.S_ISLNK(root_details.st_mode) or not stat.S_ISDIR(
        root_details.st_mode
    ):
        raise MigrationPlanError("H05_SOURCE_ROOT_INVALID")

    observed: list[tuple[str, str, str, bytes]] = []
    with os.scandir(source) as entries:
        for entry in entries:
            if entry.is_symlink():
                raise MigrationPlanError("H05_SOURCE_SYMLINK")
            if not entry.is_file(follow_symlinks=False):
                raise MigrationPlanError("H05_RECURSIVE_SOURCE_FORBIDDEN")
            match = _CANONICAL_FILENAME.fullmatch(entry.name)
            if match is None:
                raise MigrationPlanError("H05_FILENAME_NONCANONICAL")
            payload = Path(entry.path).read_bytes()
            try:
                ast.parse(payload, filename=entry.name)
            except (SyntaxError, UnicodeDecodeError) as error:
                raise MigrationPlanError("H05_SOURCE_SYNTAX") from error
            observed.append(
                (
                    entry.name,
                    match.group("migration_id"),
                    match.group("semantic_name"),
                    payload,
                )
            )

    numeric_ids = [item[1] for item in observed]
    semantic_names = [item[2] for item in observed]
    if len(numeric_ids) != len(set(numeric_ids)):
        raise MigrationPlanError("H05_DUPLICATE_NUMERIC_ID")
    if len(semantic_names) != len(set(semantic_names)):
        raise MigrationPlanError("H05_DUPLICATE_SEMANTIC_ID")
    if set(name for name, *_ in observed) != set(expected_by_name):
        raise MigrationPlanError("H05_SOURCE_SET_MISMATCH")

    base_digests = (
        _base_source_digests(root) if forbid_base_blobs else frozenset()
    )
    observed_by_name = {item[0]: item for item in observed}
    discovered: list[DiscoveredSource] = []
    for expectation in expected:
        name, migration_id, semantic_name, payload = observed_by_name[
            expectation.filename
        ]
        if migration_id != expectation.migration_id:
            raise MigrationPlanError("H05_RESERVATION_MISMATCH")
        if semantic_name.casefold() == "ledger":
            raise MigrationPlanError("H05_BASE_SEMANTIC_FORBIDDEN")
        digest = hashlib.sha256(payload).hexdigest()
        if digest in base_digests:
            raise MigrationPlanError("H05_BASE_BLOB_FORBIDDEN")
        relative_path = (
            source_relative / expectation.filename
        ).as_posix()
        if require_tracked and _git_blob(root, relative_path) != payload:
            raise MigrationPlanError("H05_SOURCE_BYTE_MISMATCH")
        if expectation.sha256 is not None and digest != expectation.sha256:
            raise MigrationPlanError("H05_SOURCE_BYTE_MISMATCH")
        discovered.append(
            DiscoveredSource(
                expectation.migration_id,
                name,
                expectation.semantic_id,
                digest,
            )
        )

    records = [
        {
            "migration_id": item.migration_id,
            "filename": item.filename,
            "semantic_id": item.semantic_id,
            "sha256": item.sha256,
        }
        for item in discovered
    ]
    return DiscoveryResult(
        tuple(discovered),
        hashlib.sha256(canonical_jcs_bytes(records)).hexdigest(),
    )


def _git_identity(root: Path) -> tuple[str, str]:
    commit = subprocess.run(
        [_GIT, "rev-parse", "--verify", "HEAD^{commit}"],
        cwd=root,
        env=_GIT_ENV,
        capture_output=True,
        text=True,
        check=False,
    )
    tree = subprocess.run(
        [_GIT, "rev-parse", "HEAD^{tree}"],
        cwd=root,
        env=_GIT_ENV,
        capture_output=True,
        text=True,
        check=False,
    )
    if (
        commit.returncode != 0
        or tree.returncode != 0
        or re.fullmatch(r"[0-9a-f]{40}", commit.stdout.strip()) is None
        or re.fullmatch(r"[0-9a-f]{40}", tree.stdout.strip()) is None
    ):
        raise MigrationPlanError("H05_SOURCE_GIT_IDENTITY")
    return commit.stdout.strip(), tree.stdout.strip()


def validate_plan_artifact(
    plan_value: Mapping[str, Any],
    *,
    repository_root: str | os.PathLike[str],
) -> Mapping[str, Any]:
    """Rebind a plan artifact to the repository bytes it claims to describe."""

    if not isinstance(plan_value, Mapping):
        raise MigrationPlanError("H05_PLAN_ARTIFACT_INVALID")
    plan = dict(plan_value)
    artifact = plan.get("artifact")
    source = plan.get("source")
    if not isinstance(artifact, Mapping) or not isinstance(source, Mapping):
        raise MigrationPlanError("H05_PLAN_ARTIFACT_INVALID")
    _validate_artifact_action_census(plan)
    kind = artifact.get("kind")
    if kind not in _ARTIFACT_KINDS:
        raise MigrationPlanError("H05_PLAN_ARTIFACT_KIND")
    expected_flags = {
        "production": kind == "production-plan",
        "executable": (
            kind == "production-plan"
            and plan.get("status") == "complete"
            and not plan.get("blockers")
        ),
        "history_eligible": (
            kind == "production-plan"
            and plan.get("status") == "complete"
            and not plan.get("blockers")
        ),
    }
    if any(artifact.get(field) is not value for field, value in expected_flags.items()):
        raise MigrationPlanError("H05_PLAN_ARTIFACT_FLAGS")

    root = _absolute_repository_root(repository_root)
    current_commit, current_tree = _git_identity(root)
    if kind == "production-plan":
        _require_clean_repository(root)
        if source.get("commit") != current_commit or source.get("tree") != current_tree:
            raise MigrationPlanError("H05_PLAN_SOURCE_DRIFT")
        domain = _PRODUCTION_ARTIFACT_DOMAIN
    else:
        if source.get("commit") is not None:
            raise MigrationPlanError("H05_PLAN_SOURCE_IDENTITY")
        if (
            source.get("base_commit") != current_commit
            or source.get("base_tree") != current_tree
            or source.get("tree") != _prospective_tree(root)
        ):
            raise MigrationPlanError("H05_PLAN_SOURCE_DRIFT")
        domain = (
            _SYNTHETIC_PROOF_DOMAIN
            if kind == "synthetic-proof"
            else _PREVIEW_ARTIFACT_DOMAIN
        )

    discovery = discover_migration_sources(
        root,
        PurePosixPath("migrations/robinhood"),
        robinhood_source_expectations(),
        require_tracked=kind == "production-plan",
        forbid_base_blobs=True,
    )
    stages = load_robinhood_stages(root, discovery)
    expected_inputs = _planning_input_manifest(
        root, stages, require_head=kind == "production-plan"
    )
    if source.get("planning_inputs") != expected_inputs:
        raise MigrationPlanError("H05_PLANNING_INPUT_DRIFT")
    expected_artifact_hash = _domain_hash(domain, _plan_identity_payload(plan))
    if plan.get("artifact_hash") != expected_artifact_hash:
        raise MigrationPlanError("H05_PLAN_ARTIFACT_HASH")
    if kind == "synthetic-proof":
        if plan.get("proof_hash") != expected_artifact_hash or plan.get("plan_hash") is not None:
            raise MigrationPlanError("H05_SYNTHETIC_PROOF_IDENTITY")
    elif kind == "preview-plan":
        if plan.get("preview_hash") != expected_artifact_hash or plan.get("plan_hash") is not None:
            raise MigrationPlanError("H05_PREVIEW_IDENTITY")
    elif plan.get("status") == "complete":
        expected_plan_hash = _domain_hash(
            _PRODUCTION_PLAN_DOMAIN, _plan_identity_payload(plan)
        )
        if plan.get("plan_hash") != expected_plan_hash:
            raise MigrationPlanError("H05_PRODUCTION_PLAN_IDENTITY")
    return plan


def validate_execution_plan_artifact(
    plan_value: Mapping[str, Any],
    *,
    repository_root: str | os.PathLike[str],
) -> Mapping[str, Any]:
    """Accept only a complete clean-tree production artifact for execution."""

    artifact = (
        plan_value.get("artifact") if isinstance(plan_value, Mapping) else None
    )
    if not isinstance(artifact, Mapping) or artifact.get("kind") != "production-plan":
        raise MigrationPlanError("H05_EXECUTION_PRODUCTION_PLAN_REQUIRED")
    validated = validate_plan_artifact(
        plan_value, repository_root=repository_root
    )
    if (
        validated.get("status") != "complete"
        or validated.get("plan_hash") is None
        or validated.get("blockers")
        or artifact.get("executable") is not True
    ):
        raise MigrationPlanError("H05_EXECUTION_PLAN_INELIGIBLE")
    profile = validated.get("profile")
    profile_id = profile.get("profile_id") if isinstance(profile, Mapping) else None
    if not isinstance(profile_id, str):
        raise MigrationPlanError("H05_PLAN_PROFILE_MISMATCH")
    expected = build_robinhood_plan(
        profile_id, repository_root=repository_root
    )
    if expected != validated:
        raise MigrationPlanError("H05_EXECUTION_PLAN_DRIFT")
    return validated


def read_bound_h06_history(
    semantic_plan: Mapping[str, Any],
    *,
    profile_id: str,
    expected_chain_id: int,
    source_commit: str,
    source_tree: str,
    history_root: str | os.PathLike[str],
):
    """Use only the H-06 public semantic-plan hash and reader APIs."""

    artifact = (
        semantic_plan.get("artifact")
        if isinstance(semantic_plan, Mapping)
        else None
    )
    if artifact is not None:
        kind = artifact.get("kind") if isinstance(artifact, Mapping) else None
        if kind != "production-plan":
            raise MigrationPlanError("H05_HISTORY_PRODUCTION_PLAN_REQUIRED")
        raise MigrationPlanError("H05_HISTORY_H06_SEMANTIC_PLAN_REQUIRED")

    from scripts.utils.manifest_schema import (
        plan_sha256,
        read_history,
        validate_semantic_plan,
    )

    validated = validate_semantic_plan(semantic_plan)
    if validated["profile"] != {
        "profile_id": profile_id,
        "expected_chain_id": expected_chain_id,
    }:
        raise MigrationPlanError("H05_PLAN_PROFILE_MISMATCH")
    if (
        validated["source"]["commit"] != source_commit
        or validated["source"]["tree"] != source_tree
    ):
        raise MigrationPlanError("H05_PLAN_SOURCE_MISMATCH")
    digest = plan_sha256(validated)
    return digest, read_history(
        profile_id,
        expected_chain_id,
        digest,
        source_commit,
        source_tree,
        history_root,
    )


def _path_presence(path: Path) -> bool:
    try:
        details = path.lstat()
    except FileNotFoundError:
        return False
    except OSError as error:
        raise MigrationPlanError("H05_PATH_UNVERIFIABLE") from error
    if stat.S_ISLNK(details.st_mode):
        raise MigrationPlanError("H05_PATH_SYMLINK")
    return True


def build_blocked_migration_report(
    profile_id: str,
    *,
    repository_root: str | os.PathLike[str],
    semantic_plan: Mapping[str, Any] | None = None,
    expectations: Sequence[SourceExpectation] = (),
    preview: bool = False,
) -> dict[str, Any]:
    """Build the deterministic, non-executing Robinhood source-plan report."""

    root = _absolute_repository_root(repository_root)
    profiles = _load_network_profiles(root)
    profile = profiles.get_profile(profile_id)
    if profile.identity.profile_id != profile_id:
        raise MigrationPlanError("H05_PROFILE_ALIAS_FORBIDDEN")
    decision = profiles.operation_decision(
        profile, profiles.Operation.MIGRATION_PLAN
    )
    if decision.outcome is not profiles.OperationOutcome.SUPPORTED:
        raise MigrationPlanError("H05_PLAN_UNSUPPORTED")
    if any(
        (
            decision.requires_rpc,
            decision.requires_identity,
            decision.requires_repository,
            decision.requires_account,
            decision.requires_verifier,
        )
    ):
        raise MigrationPlanError("H05_PLAN_RUNTIME_DEPENDENCY")
    repository = profile.repository
    if (
        repository.migration_dir is None
        or repository.history_dir is None
        or profile.identity.chain_id is None
    ):
        raise MigrationPlanError("H05_PLAN_UNSUPPORTED")
    source_relative = _safe_repository_path(repository.migration_dir)
    history_relative = _safe_repository_path(repository.history_dir)
    if source_relative == history_relative:
        raise MigrationPlanError("H05_SOURCE_HISTORY_COLLISION")
    if source_relative.parts[:2] == ("migrations", "base-mainnet"):
        raise MigrationPlanError("H05_BASE_NAMESPACE_FORBIDDEN")
    if history_relative.parts[:2] == (
        "migration_history",
        "base-mainnet",
    ):
        raise MigrationPlanError("H05_BASE_HISTORY_FORBIDDEN")

    del semantic_plan, expectations
    source_path = _join_repository_path(root, source_relative)
    history_path = _join_repository_path(root, history_relative)
    if not _path_presence(source_path):
        raise MigrationPlanError("H05_SOURCE_ABSENT")
    if _path_presence(history_path):
        raise MigrationPlanError("H05_HISTORY_PRESENT_DURING_PLAN")

    plan = build_robinhood_plan(
        profile_id,
        repository_root=root,
        preview=preview,
    )
    report = {
        "schema": _REPORT_SCHEMA,
        "mode": "preview-plan" if preview else "production-plan",
        "artifact": plan["artifact"],
        "status": plan["status"],
        "profile_id": profile_id,
        "expected_chain_id": profile.identity.chain_id,
        "source_root": source_relative.as_posix(),
        "history_root": history_relative.as_posix(),
        "source_commit": plan["source"]["commit"],
        "source_tree": plan["source"]["tree"],
        "source_digest": plan["source"]["source_digest"],
        "source_base_commit": plan["source"].get("base_commit"),
        "source_base_tree": plan["source"].get("base_tree"),
        "planning_inputs": plan["source"]["planning_inputs"],
        "reservation_digest": RESERVATION_DIGEST,
        "prior_history_digest": None,
        "source_members": plan["source"]["members"],
        "steps": plan["stages"],
        "deferred_steps": plan["deferred_stages"],
        "component_coverage": plan["component_coverage"],
        "registry_coverage": plan["registry_coverage"],
        "action_census": plan["action_census"],
        "blocker_details": plan["blocker_details"],
        "blockers": plan["blockers"],
        "plan_hash": plan["plan_hash"],
        "preview_hash": plan["preview_hash"],
        "proof_hash": plan["proof_hash"],
        "artifact_hash": plan["artifact_hash"],
        "expectation_digest": plan["expectation_digest"],
    }
    report["report_sha256"] = report_sha256(report)
    return report


class MigrationError(Exception):
    """
    Error representing an exception that occurs while executing a migration.
    Provides a `failure_timestamp` to identify the migration in which the
    failure occurred, which can be used to resume execution later on.
    """

    def __init__(
        self, failure_timestamp, message="An error occurred while executing migration"
    ):
        self.failure_timestamp = failure_timestamp
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message}. Timestamp of failed migration script: {self.failure_timestamp}"


class MigrationRunner:
    """
    Facilitates the execution of migration scripts.
    """

    def __init__(self, migrations_dir, history_dir, files):
        self.migrations_dir = migrations_dir
        self.history_dir = history_dir
        self.files = files
        self.gas = 0

    def run(self, deploy_args: DeployArgs, start_timestamp=None, end_timestamp=None, continue_running=True):
        """
        Run migrations starting at `start_timestamp`. If no start timestamp is provided,
        the history directory is checked for existing timestamps, and migrations will
        start after the latest recorded manifest timestamp.

        The `migrate` function of each migration is called with the manifest generated
        by the previous migration. Manifests returned by each migration are stored in
        the history directory. For shared deployments, they should be included in version
        control.

        To make it easy for other utilities to obtain the current manifest, a manifest
        named `current-manifest.json` will be also be saved in the history directory,
        duplicating the manifest of the latest migration.
        """
        from scripts.utils.migration import Migration

        for migrate, timestamp, prev_timestamp in self._migrations(start_timestamp, end_timestamp):
            log.h1(f"Running migration with timestamp {timestamp}...")
            try:
                migration = Migration(
                    deploy_args, self.files, timestamp, prev_timestamp, self.history_dir
                )
                migrate(migration)
                self.gas += migration.end()

                if not continue_running:
                    break
            except Exception as exception:
                raise MigrationError(timestamp) from exception
        return self.gas

    def _migrations(self, start_timestamp=None, end_timestamp=None):
        # Generator that returns a `(migration, timestamp, prev_timestamp)` tuple for
        # each migration script, starting ON OR AFTER `start_timestamp`.
        #
        # If no start timestamp is provided, the history directory is checked for existing
        # timestamps, and migrations will start after the latest recorded manifest timestamp.

        migrations = []
        if start_timestamp == None:
            start_timestamp = self._latest_manifest_timestamp()
            migrations = self._filtered_migration_filenames(
                start_timestamp, end_timestamp, inclusive=False
            )
        else:
            migrations = self._filtered_migration_filenames(
                start_timestamp, end_timestamp)

        for filename, timestamp, prev_timestamp in migrations:
            migration = importlib.util.spec_from_file_location('migration', filename)
            module = importlib.util.module_from_spec(migration)
            migration.loader.exec_module(module)
            yield module.migrate, timestamp, prev_timestamp

    def _filtered_migration_filenames(self, start_timestamp, end_timestamp, inclusive=True):
        # Get a list of migration scripts having timestamps greater than or equal
        # to the value of `start_timestamp`.
        #
        # If `inclusive` == False, only timestamps AFTER the start timestamp will be
        # included.
        #
        # Returns a list of `(filename, timestamp, prev_timestamp)` tuples.
        # `prev_timestamp` is included so that the manifest from the previous
        # migration can be retrieved and passed to the next migration.

        timestamped_migrations = []
        for file in os.listdir(self.migrations_dir):
            # timestamp of the filename is the initial string of numbers,
            # up to the first non-digit character
            match = re.fullmatch(r"(\d+).*\.py$", file)
            if match:
                timestamp = match.group(1)
                filename = os.path.join(self.migrations_dir, file)
                timestamped_migrations.append((filename, timestamp))

        # sort order of `os.listdir` is not guaranteed, so we sort on timestamp
        # Convert timestamps to integers for proper numerical sorting
        timestamped_migrations = sorted(
            timestamped_migrations, key=lambda x: int(x[1]))

        # include previous timestamp in migration tuples
        migrations = []
        prev_timestamp = None
        for filename, timestamp in timestamped_migrations:
            # Convert timestamps to integers for proper numerical comparison
            timestamp_int = int(timestamp)
            end_timestamp_int = int(end_timestamp) if end_timestamp and end_timestamp != '0' else None
            start_timestamp_int = int(start_timestamp) if start_timestamp else None

            if end_timestamp_int is not None and timestamp_int > end_timestamp_int:
                break
            if start_timestamp_int is None or timestamp_int >= start_timestamp_int:
                migrations.append((filename, timestamp, prev_timestamp))
            prev_timestamp = timestamp

        return migrations

    def _latest_manifest_timestamp(self):
        # get the timestamp of the most recently executed migration
        # (returns None if no migrations have been run)

        latest_timestamp = None

        # create the history directory if it doesn't already exist
        os.makedirs(self.history_dir, exist_ok=True)

        # scan each file to get the latest timestamp
        for file in os.listdir(self.history_dir):
            match = re.fullmatch(r"(.*)\-manifest\.json$", file)
            if match:
                timestamp = match.group(1)
                # Convert timestamps to integers for proper numerical comparison
                if latest_timestamp == None or int(timestamp) > int(latest_timestamp):
                    latest_timestamp = timestamp

        return latest_timestamp
