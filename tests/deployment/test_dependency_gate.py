from __future__ import annotations

import ast
import base64
import hashlib
import io
import json
import re
import socket
import stat
from importlib import metadata
from pathlib import Path

import cbor2
import idna
import markdown
import pytest
import requests
from _pytest._io.terminalwriter import TerminalWriter
from dotenv import dotenv_values, find_dotenv, load_dotenv
from pygments import highlight, lex
from pygments.formatters import HtmlFormatter, TerminalFormatter
from pygments.lexers import PythonLexer
from pymdownx.snippets import SnippetMissingError
from requests.adapters import BaseAdapter, HTTPAdapter
from requests.exceptions import ConnectTimeout
from rich.console import Console
from rich.syntax import Syntax
from urllib3.util import Retry


ROOT = Path(__file__).resolve().parents[2]
DIRECT_INPUT = ROOT / "requirements.in"
LOCK = ROOT / "requirements.txt"
EVIDENCE = ROOT / "docs/chains/rh/evidence/dependency-security-gate.md"
S1 = ROOT / "tests/clock/test_clock_profiles.py"

APPROVED_HASHES = {
    DIRECT_INPUT: "77768a6e25a4eac86afa88492c5e21d8609c3c5aee469846067e5c8c2b896e72",
    LOCK: "3a75970898ff917f508c8ac40046d41eee91646bc83af8bb87d0fd7217e3e569",
}
SELECTED = {
    "cbor2": "5.9.0",
    "click": "8.3.3",
    "idna": "3.15",
    "pygments": "2.20.0",
    "pymdown-extensions": "10.21.3",
    "python-dotenv": "1.2.2",
    "requests": "2.33.0",
    "urllib3": "2.7.0",
    "web3": "7.16.0",
    "wheel": "0.46.2",
}
WEB3_CLOSURE = {
    "aiohappyeyeballs": "2.7.1",
    "aiohttp": "3.14.3",
    "aiosignal": "1.4.0",
    "frozenlist": "1.8.0",
    "multidict": "6.7.1",
    "propcache": "0.5.2",
    "pyunormalize": "17.0.0",
    "types-requests": "2.33.0.20260712",
    "web3": "7.16.0",
    "websockets": "15.0.1",
    "yarl": "1.24.5",
}
HELD = {
    "pytest": "8.4.2",
    "titanoboa": "0.2.7",
    "vyper": "0.4.3",
}
RETIRED_REMEDIATED_FINDINGS = {
    "PYSEC-2026-2132": "EX-H01-CLICK-01",
    "PYSEC-2026-2987": "EX-H01-PYGMENTS-01",
    "PYSEC-2026-2999": "EX-H01-PYMDOWN-SNIPPETS-01",
}
RESIDUAL_FINDINGS = {
    "PYSEC-2026-1845": "EX-H01-PYTEST-01",
    "CVE-2026-61632": "EX-H01-PYMDOWN-B64-01",
    "PYSEC-2023-142": "authoritative range exclusion",
    "PYSEC-2025-33": "authoritative range exclusion",
}
CURRENT_REVIEW_BLOCKERS = {
    "PYSEC-2026-3654": "separate H-01 review blocker",
}
RETIRED_EXCEPTION_IDS = {
    "EX-H01-CLICK-01",
    "EX-H01-PYGMENTS-01",
    "EX-H01-PYMDOWN-SNIPPETS-01",
}
RETAINED_EXCEPTION_IDS = {
    "EX-H01-PYTEST-01",
    "EX-H01-PYMDOWN-B64-01",
}
OPERATIVE_EXCEPTION_IDS = RETAINED_EXCEPTION_IDS
KNOWN_EXCEPTION_IDS = {
    *RETIRED_EXCEPTION_IDS,
    *RETAINED_EXCEPTION_IDS,
}
TRANSITION_MARKER = "## H-01 three-exception retirement transition"
RETAINED_TERMS_MARKER = "### Operative retained exception terms"
RETAINED_REVIEW_FIELD = "scheduled security review on **15 August 2026**"
RETAINED_EXPIRY_FIELD = "hard expiry at **2026-08-31T23:59:59Z**"
RETAINED_STATUS = "**Status:** Retained—operative."
RETIRED_STATUS = "**Status:** Retired—historical and non-operative."
EXPECTED_HEADER = (
    "#    pip-compile --cert=None --client-cert=None "
    "--index-url=https://pypi.org/simple --no-emit-index-url "
    "--output-file=requirements.txt --pip-args=None requirements.in"
)
REACHABILITY_SUFFIXES = {
    ".cfg",
    ".ini",
    ".json",
    ".py",
    ".toml",
    ".yaml",
    ".yml",
}
REACHABILITY_EXCLUDED_DIRS = {
    ".cache",
    ".direnv",
    ".git",
    ".hg",
    ".mypy_cache",
    ".nox",
    ".pytest_cache",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".venv",
    "__pycache__",
    "artifacts",
    "build",
    "dist",
    "env",
    "generated",
    "htmlcov",
    "node_modules",
    "private",
    "private-evidence",
    "site",
    "site-packages",
    "venv",
    "vendor",
}
APPROVED_CLICK_SURFACES = {
    Path("scripts/ccip_send.py"),
    Path("scripts/console.py"),
    Path("scripts/migrate.py"),
    Path("scripts/verify.py"),
}
CURRENT_SUPPORTED_WEB3_IMPORT_PATHS = {
    Path("migrations/base-mainnet/2025071801_LootBoxPointsRefresh.py"),
    Path("migrations/base-mainnet/2026080701_CcipWire.py"),
    Path("migrations/robinhood-mainnet/0001_Registries.py"),
    Path("migrations/robinhood-mainnet/0009_RedeployStaleContracts.py"),
    Path("migrations/robinhood-mainnet/0010_RedeployLedger.py"),
    Path("migrations/robinhood-mainnet/2026080701_CcipWire.py"),
    Path("scripts/ledger_signing_smoke.py"),
    Path("scripts/prepare_defaults.py"),
    Path("scripts/utils/ledger_account.py"),
    Path("scripts/utils/safe_account.py"),
}
DEPENDENCY_BEHAVIOR_TEST = Path("tests/deployment/test_dependency_gate.py")
PYMDOWN_EXTENSION_NAMES = {"pymdownx.b64", "pymdownx.snippets"}


@pytest.fixture(scope="session")
def ripe_hq():
    """Keep this dependency-only gate out of the protocol autouse setup graph."""
    yield None


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _pins(path: Path) -> dict[str, str]:
    pins: dict[str, str] = {}
    for line in path.read_text().splitlines():
        match = re.fullmatch(r"([A-Za-z0-9][A-Za-z0-9_.-]*)==([^\s;]+)", line)
        if match:
            pins[_canonical_name(match.group(1))] = match.group(2)
    return pins


def _distribution_direct_url(package: str) -> str | None:
    return metadata.distribution(package).read_text("direct_url.json")


def _assert_web3_closure(
    lock: Path,
    *,
    version_reader=metadata.version,
    direct_url_reader=_distribution_direct_url,
) -> None:
    pins = _pins(lock)
    for package, expected_version in WEB3_CLOSURE.items():
        assert pins.get(package) == expected_version, (
            f"{package} lock version must be {expected_version}"
        )
        assert version_reader(package) == expected_version, (
            f"{package} runtime version must be {expected_version}"
        )
        assert direct_url_reader(package) is None, (
            f"{package} must not have direct URL installation metadata"
        )


def _supported_literal_import_target(
    node: ast.AST,
    importlib_aliases: set[str],
    import_module_aliases: set[str],
) -> str | None:
    if not isinstance(node, ast.Call):
        return None
    target = (
        node.args[0]
        if node.args
        else next(
            (keyword.value for keyword in node.keywords if keyword.arg == "name"),
            None,
        )
    )
    if not isinstance(target, ast.Constant) or not isinstance(target.value, str):
        return None

    if isinstance(node.func, ast.Name):
        if node.func.id == "__import__" or node.func.id in import_module_aliases:
            return target.value
        return None
    if (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "import_module"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id in importlib_aliases
    ):
        return target.value
    return None


def _supported_web3_import_paths(root: Path) -> set[Path]:
    paths: set[Path] = set()
    for source_root in (root / "migrations", root / "scripts"):
        try:
            source_root_mode = source_root.lstat().st_mode
        except FileNotFoundError:
            continue
        assert stat.S_ISDIR(source_root_mode), (
            f"{source_root.relative_to(root)} must be a real directory"
        )
        for path in sorted(source_root.rglob("*")):
            relative = path.relative_to(root)
            mode = path.lstat().st_mode
            assert not stat.S_ISLNK(mode), (
                f"{relative}: symlink entries are not allowed in Web3 inventory roots"
            )
            if path.suffix != ".py":
                continue
            assert stat.S_ISREG(mode), (
                f"{relative}: Python source must be a regular file"
            )
            tree = ast.parse(path.read_text(), filename=str(relative))
            # Deliberately syntax-limited: callable assignment, builtins aliases,
            # and dataflow-derived targets remain explicit code-review triggers.
            importlib_aliases: set[str] = set()
            import_module_aliases: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for imported in node.names:
                        if imported.name == "importlib":
                            importlib_aliases.add(imported.asname or "importlib")
                elif isinstance(node, ast.ImportFrom) and node.module == "importlib":
                    for imported in node.names:
                        if imported.name == "import_module":
                            import_module_aliases.add(
                                imported.asname or "import_module"
                            )
            imports_web3 = any(
                (
                    isinstance(node, ast.Import)
                    and any(
                        imported.name == "web3"
                        or imported.name.startswith("web3.")
                        for imported in node.names
                    )
                )
                or (
                    isinstance(node, ast.ImportFrom)
                    and node.module is not None
                    and (
                        node.module == "web3"
                        or node.module.startswith("web3.")
                    )
                )
                or (
                    (
                        dynamic_target := _supported_literal_import_target(
                            node,
                            importlib_aliases,
                            import_module_aliases,
                        )
                    )
                    is not None
                    and (dynamic_target == "web3" or dynamic_target.startswith("web3."))
                )
                for node in ast.walk(tree)
            )
            if imports_web3:
                paths.add(relative)
    return paths


def _exception_section(evidence: str, exception_id: str) -> str:
    matches = list(
        re.finditer(
            rf"#### `{re.escape(exception_id)}`.*?(?=\n#### |\n### )",
            evidence,
            flags=re.DOTALL,
        )
    )
    assert matches, f"missing exception section {exception_id}"
    return matches[-1].group(0)


def _latest_transition_section(evidence: str) -> str:
    assert (
        TRANSITION_MARKER in evidence
    ), "missing H-01 retirement transition section"
    return TRANSITION_MARKER + evidence.rsplit(
        TRANSITION_MARKER, maxsplit=1
    )[1]


def _exception_heading_sections(
    evidence: str, exception_id: str
) -> list[tuple[int, str]]:
    headings = list(
        re.finditer(
            rf"^(?P<level>#{{1,6}})\s+[^\n]*"
            rf"{re.escape(exception_id)}[^\n]*$",
            evidence,
            flags=re.MULTILINE,
        )
    )
    sections: list[tuple[int, str]] = []
    for heading in headings:
        level = len(heading.group("level"))
        tail = evidence[heading.end() :]
        boundary = re.search(
            rf"^#{{1,{level}}}\s+",
            tail,
            flags=re.MULTILINE,
        )
        end = heading.end() + boundary.start() if boundary else len(evidence)
        sections.append((heading.start(), evidence[heading.start() : end]))
    return sections


def _retained_exception_control(evidence: str, exception_id: str) -> str:
    transition = _latest_transition_section(evidence)
    assert (
        transition.count(RETAINED_TERMS_MARKER) == 1
    ), "retained terms must have exactly one controlling section"
    terms_tail = transition.split(RETAINED_TERMS_MARKER, maxsplit=1)[1]
    first_exception = re.search(r"^####\s+", terms_tail, flags=re.MULTILINE)
    assert first_exception is not None, "missing retained exception sections"
    common_terms = (
        RETAINED_TERMS_MARKER + terms_tail[: first_exception.start()]
    )
    sections = [
        section
        for _, section in _exception_heading_sections(
            transition, exception_id
        )
    ]
    assert (
        len(sections) == 1
    ), f"expected one controlling section for {exception_id}"
    return common_terms + sections[0]


def _assert_retained_exception_control(
    control: str, exception_id: str
) -> None:
    normalized = " ".join(control.split())
    assert exception_id in normalized
    assert RETAINED_STATUS in normalized
    assert normalized.count(RETAINED_REVIEW_FIELD) == 1
    assert normalized.count(RETAINED_EXPIRY_FIELD) == 1
    assert "**Threat model:**" in normalized
    assert "**Scope:**" in normalized
    assert "**Compensating controls:**" in normalized
    assert "**Re-review/invalidation triggers:**" in normalized


def _assert_no_retired_exception_shadow(
    evidence: str, exception_id: str
) -> None:
    transition_start = evidence.rfind(TRANSITION_MARKER)
    assert transition_start >= 0
    transition = evidence[transition_start:]
    normalized_transition = " ".join(transition.split())
    assert (
        "The historical `PROPOSED_RETIREMENTS` state is superseded only when "
        "the effectivity boundary above is satisfied."
    ) in normalized_transition
    assert (
        "The three retired records remain preserved for audit chronology"
    ) in normalized_transition

    sections = _exception_heading_sections(evidence, exception_id)
    assert any(
        start < transition_start for start, _ in sections
    ), f"missing preserved historical section for {exception_id}"
    for start, section in sections:
        if start < transition_start:
            continue
        assert (
            RETIRED_STATUS in section
        ), f"later shadow section for {exception_id} is not explicitly retired"
        assert (
            RETAINED_STATUS not in section
        ), f"later operative shadow section for retired {exception_id}"


def _dotted_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _dotted_name(node.value)
        return f"{parent}.{node.attr}" if parent else None
    return None


def _resolved_name(node: ast.expr, aliases: dict[str, str]) -> str | None:
    dotted = _dotted_name(node)
    if dotted is None:
        return None
    head, *tail = dotted.split(".")
    resolved = aliases.get(head, head)
    return ".".join((resolved, *tail))


def _literal_string(
    node: ast.expr, string_literals: dict[str, str]
) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        return string_literals.get(node.id)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _literal_string(node.left, string_literals)
        right = _literal_string(node.right, string_literals)
        if left is not None and right is not None:
            return left + right
    return None


def _statically_resolved_string_elements(
    node: ast.expr,
    string_literals: dict[str, str],
    sequence_literals: dict[str, tuple[str, ...]],
) -> tuple[str, ...]:
    if isinstance(node, ast.Name) and node.id in sequence_literals:
        return sequence_literals[node.id]
    value = _literal_string(node, string_literals)
    if value is not None:
        return (value,)
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return tuple(
            value
            for item in node.elts
            for value in _statically_resolved_string_elements(
                item, string_literals, sequence_literals
            )
        )
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _statically_resolved_string_elements(
            node.left, string_literals, sequence_literals
        ) + _statically_resolved_string_elements(
            node.right, string_literals, sequence_literals
        )
    return ()


def _literal_keyword_mapping(
    node: ast.expr,
    keyword_mappings: dict[str, dict[str, ast.expr]],
) -> dict[str, ast.expr]:
    if isinstance(node, ast.Name):
        return keyword_mappings.get(node.id, {})
    if not isinstance(node, ast.Dict):
        return {}
    return {
        key.value: value
        for key, value in zip(node.keys, node.values, strict=True)
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    }


def _call_keyword_values(
    node: ast.Call,
    keyword: str,
    keyword_mappings: dict[str, dict[str, ast.expr]],
) -> tuple[ast.expr, ...]:
    values: list[ast.expr] = []
    for item in node.keywords:
        if item.arg == keyword:
            values.append(item.value)
        elif item.arg is None:
            mapping = _literal_keyword_mapping(item.value, keyword_mappings)
            if keyword in mapping:
                values.append(mapping[keyword])
    return tuple(values)


def _python_reachability_violations(path: Path, root: Path) -> list[str]:
    relative = path.relative_to(root)
    try:
        tree = ast.parse(path.read_text(), filename=str(relative))
    except (SyntaxError, UnicodeDecodeError) as error:
        return [f"{relative}: cannot AST-scan Python source: {error}"]

    aliases: dict[str, str] = {}
    string_literals: dict[str, str] = {}
    sequence_literals: dict[str, tuple[str, ...]] = {}
    keyword_mappings: dict[str, dict[str, ast.expr]] = {}
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = _literal_string(node.value, string_literals)
            sequence = _statically_resolved_string_elements(
                node.value, string_literals, sequence_literals
            )
            keyword_mapping = _literal_keyword_mapping(
                node.value, keyword_mappings
            )
            resolved_alias = _resolved_name(node.value, aliases)
            targets = (
                node.targets if isinstance(node, ast.Assign) else [node.target]
            )
            for target in targets:
                if isinstance(target, ast.Name):
                    if value is not None:
                        string_literals[target.id] = value
                    if sequence:
                        sequence_literals[target.id] = sequence
                    if keyword_mapping:
                        keyword_mappings[target.id] = keyword_mapping
                    if resolved_alias and (
                        resolved_alias == "markdown"
                        or resolved_alias.startswith("markdown.")
                    ):
                        aliases[target.id] = resolved_alias
        if isinstance(node, ast.Import):
            for imported in node.names:
                bound = imported.asname or imported.name.split(".", 1)[0]
                aliases[bound] = imported.name if imported.asname else bound
                if imported.name == "click" or imported.name.startswith("click."):
                    if relative not in APPROVED_CLICK_SURFACES:
                        violations.append(
                            f"{relative}:{node.lineno}: adds a new Click "
                            "import surface"
                        )
                if (
                    imported.name == "pymdownx"
                    or imported.name.startswith("pymdownx.")
                ) and relative != DEPENDENCY_BEHAVIOR_TEST:
                    violations.append(
                        f"{relative}:{node.lineno}: adds a Pymdown "
                        "programmatic activation surface"
                    )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for imported in node.names:
                target = f"{module}.{imported.name}" if module else imported.name
                aliases[imported.asname or imported.name] = target
                if module == "click" or module.startswith("click."):
                    if relative not in APPROVED_CLICK_SURFACES:
                        violations.append(
                            f"{relative}:{node.lineno}: adds a new Click "
                            "import surface"
                        )
                    if imported.name in {"*", "edit"}:
                        violations.append(
                            f"{relative}:{node.lineno}: imports Click edit surface"
                        )
                if module == "pygments" or module.startswith("pygments."):
                    lowered = imported.name.lower()
                    if "adllexer" in lowered or "archetype" in lowered:
                        violations.append(
                            f"{relative}:{node.lineno}: imports Pygments "
                            "Archetype/AdlLexer surface"
                        )
                if (
                    module == "pymdownx" or module.startswith("pymdownx.")
                ) and relative != DEPENDENCY_BEHAVIOR_TEST:
                    violations.append(
                        f"{relative}:{node.lineno}: adds a Pymdown "
                        "programmatic activation surface"
                    )

    for node in ast.walk(tree):
        if isinstance(node, (ast.Attribute, ast.Name)):
            resolved = _resolved_name(node, aliases)
            if resolved and resolved.startswith("click.") and resolved.endswith(
                ".edit"
            ):
                violations.append(
                    f"{relative}:{node.lineno}: references {resolved}"
                )
            if resolved and resolved.startswith("pygments."):
                lowered = resolved.lower()
                if "adllexer" in lowered or "archetype" in lowered:
                    violations.append(
                        f"{relative}:{node.lineno}: references Pygments "
                        "Archetype/AdlLexer surface"
                    )
        if not isinstance(node, ast.Call):
            continue
        resolved_call = _resolved_name(node.func, aliases)
        if (
            resolved_call
            in {
                "markdown.Markdown",
                "markdown.markdown",
                "markdown.markdownFromFile",
            }
            and relative != DEPENDENCY_BEHAVIOR_TEST
        ):
            for extensions in _call_keyword_values(
                node, "extensions", keyword_mappings
            ):
                literal_extensions = _statically_resolved_string_elements(
                    extensions, string_literals, sequence_literals
                )
                for extension in literal_extensions:
                    if extension.lower() in PYMDOWN_EXTENSION_NAMES:
                        violations.append(
                            f"{relative}:{node.lineno}: activates "
                            f"{extension!r} through {resolved_call}"
                        )
        if not resolved_call or not resolved_call.startswith("pygments."):
            continue
        if resolved_call.endswith(".get_lexer_by_name") and node.args:
            lexer_name = _literal_string(node.args[0], string_literals)
            if lexer_name and lexer_name.lower() in {"adl", "archetype"}:
                violations.append(
                    f"{relative}:{node.lineno}: selects Pygments "
                    f"{lexer_name!r} lexer"
                )

    return violations


def _configuration_reachability_violations(path: Path, root: Path) -> list[str]:
    relative = path.relative_to(root)
    source = path.read_text(errors="ignore").lower()
    violations = []
    for extension in ("pymdownx.snippets", "pymdownx.b64"):
        if extension in source:
            violations.append(f"{relative}: enables {extension}")
    if "adllexer" in source or "archetypelexer" in source:
        violations.append(f"{relative}: selects Pygments Archetype/AdlLexer")
    elif "pygments" in source and "archetype" in source:
        violations.append(f"{relative}: selects Pygments Archetype lexer")
    return violations


def _exception_reachability_violations(root: Path) -> list[str]:
    violations: list[str] = []
    for directory, dirnames, filenames in root.walk():
        dirnames[:] = [
            name
            for name in dirnames
            if name not in REACHABILITY_EXCLUDED_DIRS
            and not name.endswith((".egg-info", ".dist-info"))
        ]
        for filename in filenames:
            path = directory / filename
            if (
                path.is_symlink()
                or path.suffix.lower() not in REACHABILITY_SUFFIXES
            ):
                continue
            if path.suffix.lower() == ".py":
                violations.extend(_python_reachability_violations(path, root))
            else:
                violations.extend(
                    _configuration_reachability_violations(path, root)
                )
    return sorted(set(violations))


def _assert_exception_reachability_controls(root: Path) -> None:
    violations = _exception_reachability_violations(root)
    assert not violations, "bounded-exception reachability changed:\n" + "\n".join(
        violations
    )


def test_approved_inputs_and_generated_lock_are_exact():
    for path, expected_hash in APPROVED_HASHES.items():
        assert _sha256(path) == expected_hash

    lock = LOCK.read_text()
    evidence = EVIDENCE.read_text()
    assert "# This file is autogenerated by pip-compile with Python 3.12" in lock
    assert EXPECTED_HEADER in lock
    assert lock.count("https://pypi.org/simple") == 1
    assert "    #   -r requirements.in" in lock
    for expected_hash in APPROVED_HASHES.values():
        assert expected_hash in evidence


def test_web3_direct_dependency_and_supported_current_tree_inventory():
    assert _pins(DIRECT_INPUT)["web3"] == "7.16.0"
    assert _pins(LOCK)["web3"] == "7.16.0"
    # Equality is a drift check only for the explicitly supported syntax below;
    # it is not whole-program Python import reachability.
    assert _supported_web3_import_paths(ROOT) == CURRENT_SUPPORTED_WEB3_IMPORT_PATHS
    evidence = EVIDENCE.read_text()
    normalized_evidence = " ".join(evidence.split())
    assert "GHSA-5hr4-253g-cpx2" in evidence
    assert "`web3==7.12.0` is rejected" in evidence
    assert "not whole-program Python import reachability" in normalized_evidence
    assert "code-review trigger" in evidence


@pytest.mark.parametrize(
    "source",
    (
        "import web3\n",
        "from web3 import Web3\n",
        "__import__('web3')\n",
        "import importlib\nimportlib.import_module('web3')\n",
        "import importlib as loader\nloader.import_module('web3.eth')\n",
        "import importlib as loader\nloader.import_module(name='web3')\n",
        "from importlib import import_module\nimport_module('web3')\n",
        ("from importlib import import_module as load_module\nload_module('web3')\n"),
    ),
)
def test_web3_supported_inventory_detects_listed_syntax(tmp_path, source):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    candidate = scripts / "candidate.py"
    candidate.write_text(source)
    assert _supported_web3_import_paths(tmp_path) == {Path("scripts/candidate.py")}


def test_web3_inventory_rejects_symlink_entries(tmp_path):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    target = tmp_path / "target.py"
    target.write_text("import web3\n")
    (scripts / "candidate.py").symlink_to(target)

    with pytest.raises(AssertionError, match="symlink entries are not allowed"):
        _supported_web3_import_paths(tmp_path)


def test_web3_inventory_rejects_nonregular_python_sources(tmp_path):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "candidate.py").mkdir()

    with pytest.raises(AssertionError, match="Python source must be a regular"):
        _supported_web3_import_paths(tmp_path)


@pytest.mark.parametrize(
    "source",
    (
        (
            "from importlib import import_module\n"
            "assigned_callable = import_module\n"
            "assigned_callable('web3')\n"
        ),
        (
            "import builtins as python_builtins\n"
            "python_builtins.__import__('web3')\n"
        ),
        (
            "import importlib\n"
            "module_alias = 'web3'\n"
            "importlib.import_module(module_alias)\n"
        ),
    ),
)
def test_web3_inventory_leaves_callable_builtins_and_dataflow_aliases_to_review(
    tmp_path, source
):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "candidate.py").write_text(source)
    assert _supported_web3_import_paths(tmp_path) == set()


def test_web3_closure_matches_lock_runtime_and_install_metadata():
    _assert_web3_closure(LOCK)


@pytest.mark.parametrize(("package", "version"), WEB3_CLOSURE.items())
def test_web3_closure_rejects_lock_version_mutation(tmp_path, package, version):
    mutated = LOCK.read_text().replace(f"{package}=={version}", f"{package}==0", 1)
    assert mutated != LOCK.read_text()
    lock = tmp_path / "requirements.txt"
    lock.write_text(mutated)

    with pytest.raises(AssertionError, match=rf"{re.escape(package)} lock"):
        _assert_web3_closure(lock)


@pytest.mark.parametrize("package", WEB3_CLOSURE)
def test_web3_closure_rejects_runtime_version_mutation(package):
    actual_version = metadata.version

    def mutated_version(name):
        return "0" if name == package else actual_version(name)

    with pytest.raises(AssertionError, match=rf"{re.escape(package)} runtime"):
        _assert_web3_closure(LOCK, version_reader=mutated_version)


@pytest.mark.parametrize("package", WEB3_CLOSURE)
def test_web3_closure_rejects_direct_url_metadata(package):
    def mutated_direct_url(name):
        if name == package:
            return '{"url": "https://example.invalid/package.whl"}'
        return _distribution_direct_url(name)

    with pytest.raises(AssertionError, match=rf"{re.escape(package)} must not"):
        _assert_web3_closure(LOCK, direct_url_reader=mutated_direct_url)


def test_web3_checksum_and_keccak_make_no_network_attempt(monkeypatch):
    from web3 import Web3

    attempts: list[str] = []

    def deny(operation):
        def denied(*args, **kwargs):
            attempts.append(operation)
            raise AssertionError(f"network attempt through {operation}")

        return denied

    for operation in (
        "socket",
        "create_connection",
        "getaddrinfo",
        "gethostbyaddr",
        "gethostbyname",
        "gethostbyname_ex",
    ):
        monkeypatch.setattr(socket, operation, deny(f"socket.{operation}"))

    assert (
        Web3.to_checksum_address("0x52908400098527886e0f7030069857d2e4169ee7")
        == "0x52908400098527886E0F7030069857D2E4169EE7"
    )
    assert Web3.keccak(text="ripe-web3-offline-gate").hex() == (
        "1d17285abbb738ef53dadaa05ee534ef754ed12345f9c7c31b08c1819d611824"
    )
    assert attempts == []


def test_selected_and_held_versions_match_lock_and_runtime():
    pins = _pins(LOCK)
    expected = SELECTED | HELD
    for package, version in expected.items():
        assert pins[package] == version
        assert metadata.version(package) == version

    # These reviewed lower versions are displaced or explicitly rejected.
    # Exact approved pins above make the range check fail closed.
    forbidden = {
        "cbor2": {"5.7.0"},
        "click": {"8.2.1"},
        "idna": {"3.10"},
        "pygments": {"2.19.2"},
        "pymdown-extensions": {"10.16.1"},
        "python-dotenv": {"1.2.1"},
        "requests": {"2.32.5"},
        "urllib3": {"2.5.0", "2.6.0", "2.6.2", "2.6.3"},
        "web3": {"7.12.0"},
        "wheel": {"0.45.1"},
    }
    for package, versions in forbidden.items():
        assert pins[package] not in versions


def test_dependency_sources_are_public_pypi_only():
    direct_lines = [
        line.strip()
        for line in DIRECT_INPUT.read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    lock_lines = [
        line.strip()
        for line in LOCK.read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    for line in direct_lines + lock_lines:
        assert "://" not in line
        assert " @ " not in line
        assert not line.startswith(("-e", "--editable", ".", "/", "~"))
        assert not any(
            marker in line.lower()
            for marker in ("git+", "hg+", "svn+", "bzr+", "file:")
        )

    combined = DIRECT_INPUT.read_text() + LOCK.read_text()
    assert "--extra-index-url" not in combined
    assert "--find-links" not in combined
    assert "private-index" not in combined.lower()
    for package in SELECTED | HELD | WEB3_CLOSURE:
        assert metadata.distribution(package).read_text("direct_url.json") is None


def test_evidence_reconciles_every_selected_package_and_residual_finding():
    evidence = EVIDENCE.read_text()
    normalized = " ".join(evidence.split())
    transition = _latest_transition_section(evidence)
    normalized_transition = " ".join(transition.split())
    for package in SELECTED | HELD | WEB3_CLOSURE:
        assert package in evidence.lower()
    for finding, disposition in RESIDUAL_FINDINGS.items():
        assert finding in evidence
        assert disposition in evidence
    for finding, disposition in CURRENT_REVIEW_BLOCKERS.items():
        assert finding in evidence
        assert disposition in evidence
    for finding, disposition in RETIRED_REMEDIATED_FINDINGS.items():
        assert finding in evidence
        assert disposition in transition

    assert "The two Vyper determinations are not exceptions" in normalized
    assert "no `--ignore-vuln` flags" in normalized
    assert "both Vyper dispositions" in normalized
    assert (
        "Package remediation and repository exception retirement are distinct "
        "from GitHub/Dependabot alert closure."
    ) in normalized_transition
    assert (
        "No authenticated alert-state query was required or performed."
    ) in normalized_transition


def test_bounded_exceptions_are_explicit_and_workflow_gated():
    evidence = EVIDENCE.read_text()
    normalized = " ".join(evidence.split())
    transition = _latest_transition_section(evidence)
    normalized_transition = " ".join(transition.split())
    assert "Mick Hagen, H-01 owner" in transition
    assert (
        "An expired exception blocks deployment rehearsal and merge"
        in normalized_transition
    )

    assert RETIRED_EXCEPTION_IDS == {
        "EX-H01-CLICK-01",
        "EX-H01-PYGMENTS-01",
        "EX-H01-PYMDOWN-SNIPPETS-01",
    }
    assert OPERATIVE_EXCEPTION_IDS == {
        "EX-H01-PYTEST-01",
        "EX-H01-PYMDOWN-B64-01",
    }
    assert RETIRED_EXCEPTION_IDS.isdisjoint(OPERATIVE_EXCEPTION_IDS)
    assert RETIRED_EXCEPTION_IDS | OPERATIVE_EXCEPTION_IDS == KNOWN_EXCEPTION_IDS

    for exception_id in RETIRED_EXCEPTION_IDS:
        assert (
            f"| `{exception_id}` | **Retired—historical and non-operative.**"
            in transition
        )
        _assert_no_retired_exception_shadow(evidence, exception_id)
        operative_shadow = (
            f"\n\n#### `{exception_id}` — appended operative shadow\n\n"
            f"- {RETAINED_STATUS}\n"
            "- **Threat model:** shadow\n"
            "- **Scope:** shadow\n"
            "- **Compensating controls:** shadow\n"
            "- **Re-review/invalidation triggers:** shadow\n"
        )
        with pytest.raises(
            AssertionError,
            match="later (?:shadow|operative shadow) section",
        ):
            _assert_no_retired_exception_shadow(
                evidence + operative_shadow, exception_id
            )

    for exception_id in OPERATIVE_EXCEPTION_IDS:
        control = _retained_exception_control(evidence, exception_id)
        _assert_retained_exception_control(control, exception_id)
        normalized_control = " ".join(control.split())
        assert normalized_control.count("15 August 2026") == 1
        assert normalized_control.count("2026-08-31T23:59:59Z") == 1

        mutations = (
            normalized_control.replace(
                "15 August 2026", "16 August 2026", 1
            ),
            normalized_control.replace(
                "2026-08-31T23:59:59Z", "2026-09-01T00:00:00Z", 1
            ),
            normalized_control.replace(RETAINED_REVIEW_FIELD, "", 1),
            normalized_control.replace(RETAINED_EXPIRY_FIELD, "", 1),
        )
        for mutated_control in mutations:
            with pytest.raises(AssertionError):
                _assert_retained_exception_control(
                    mutated_control, exception_id
                )

    assert "There is no general wall-clock freshness window." in normalized
    assert "Evidence becomes stale on any of these events:" in normalized
    assert "immediately before the Stage B reviewer gate" in normalized
    assert "Stale evidence blocks submission to the Stage B reviewer gate" in normalized


def test_exception_reachability_controls_remain_true():
    _assert_exception_reachability_controls(ROOT)


@pytest.mark.parametrize("extension", ("pymdownx.snippets", "pymdownx.b64"))
def test_reachability_gate_rejects_root_mkdocs_extension(tmp_path, extension):
    (tmp_path / "mkdocs.yml").write_text(
        f"markdown_extensions:\n  - {extension}\n"
    )

    with pytest.raises(AssertionError, match=rf"enables {re.escape(extension)}"):
        _assert_exception_reachability_controls(tmp_path)


def test_reachability_gate_rejects_aliased_click_edit_import(tmp_path):
    tooling = tmp_path / "tooling"
    tooling.mkdir()
    (tooling / "editor.py").write_text(
        "from click import edit as launch_editor\n"
        "launch_editor('trusted initial text')\n"
    )

    with pytest.raises(
        AssertionError,
        match="(adds a new Click import surface|imports Click edit surface)",
    ):
        _assert_exception_reachability_controls(tmp_path)


def test_reachability_gate_rejects_direct_adllexer_import(tmp_path):
    tooling = tmp_path / "tooling"
    tooling.mkdir()
    (tooling / "highlight.py").write_text(
        "from pygments.lexers.algebra import AdlLexer as SelectedLexer\n"
    )

    with pytest.raises(
        AssertionError, match="imports Pygments Archetype/AdlLexer surface"
    ):
        _assert_exception_reachability_controls(tmp_path)


def test_reachability_gate_rejects_dynamic_literal_adl_selection(tmp_path):
    tooling = tmp_path / "tooling"
    tooling.mkdir()
    (tooling / "highlight.py").write_text(
        "from pygments.lexers import get_lexer_by_name as select_lexer\n"
        "lexer_name = 'ad' + 'l'\n"
        "select_lexer(lexer_name)\n"
    )

    with pytest.raises(
        AssertionError, match="selects Pygments 'adl' lexer"
    ):
        _assert_exception_reachability_controls(tmp_path)


def test_reachability_gate_rejects_programmatic_pymdown_import(tmp_path):
    tooling = tmp_path / "tooling"
    tooling.mkdir()
    (tooling / "render.py").write_text(
        "from pymdownx import snippets\n"
    )

    with pytest.raises(
        AssertionError, match="adds a Pymdown programmatic activation surface"
    ):
        _assert_exception_reachability_controls(tmp_path)


@pytest.mark.parametrize(
    ("source", "extension"),
    (
        (
            "import markdown\n"
            "markdown.markdown(text, extensions=['pymdownx.b64'])\n",
            "pymdownx.b64",
        ),
        (
            "from markdown import markdown as render\n"
            "render(text, extensions=['pymdownx.snippets'])\n",
            "pymdownx.snippets",
        ),
        (
            "import markdown as md\n"
            "extension = 'pymdownx.' + 'b64'\n"
            "md.markdown(text, extensions=[extension])\n",
            "pymdownx.b64",
        ),
        (
            "import markdown\n"
            "selected = ['pymdownx.' + 'snippets']\n"
            "extensions = selected + ['tables']\n"
            "markdown.markdown(text, extensions=extensions)\n",
            "pymdownx.snippets",
        ),
        (
            "import markdown\n"
            "markdown.markdown(\n"
            "    text,\n"
            "    extensions=['pymdownx.b64', pick_extra()],\n"
            ")\n",
            "pymdownx.b64",
        ),
        (
            "from markdown import markdown as render\n"
            "render(\n"
            "    text,\n"
            "    extensions=[pick_extra(), 'pymdownx.snippets'],\n"
            ")\n",
            "pymdownx.snippets",
        ),
        (
            "import markdown\n"
            "markdown.Markdown(extensions=['pymdownx.b64'])\n",
            "pymdownx.b64",
        ),
        (
            "from markdown import Markdown\n"
            "Markdown(extensions=['pymdownx.snippets'])\n",
            "pymdownx.snippets",
        ),
        (
            "from markdown import Markdown as Renderer\n"
            "extension = 'pymdownx.' + 'b64'\n"
            "Renderer(extensions=[extension])\n",
            "pymdownx.b64",
        ),
        (
            "import markdown as md\n"
            "md.Markdown(extensions=['pymdownx.snippets'])\n",
            "pymdownx.snippets",
        ),
        (
            "import markdown\n"
            "Renderer = markdown.Markdown\n"
            "Renderer(extensions=['pymdownx.b64'])\n",
            "pymdownx.b64",
        ),
        (
            "import markdown\n"
            "markdown.markdownFromFile(\n"
            "    input='input.md',\n"
            "    extensions=['pymdownx.b64'],\n"
            ")\n",
            "pymdownx.b64",
        ),
        (
            "from markdown import markdownFromFile\n"
            "markdownFromFile(\n"
            "    input='input.md',\n"
            "    extensions=['pymdownx.snippets'],\n"
            ")\n",
            "pymdownx.snippets",
        ),
        (
            "from markdown import markdownFromFile as render_file\n"
            "render_file(\n"
            "    input='input.md',\n"
            "    extensions=['pymdownx.' + 'b64'],\n"
            ")\n",
            "pymdownx.b64",
        ),
        (
            "import markdown as md\n"
            "render_file = md.markdownFromFile\n"
            "render_file(\n"
            "    input='input.md',\n"
            "    extensions=['pymdownx.snippets'],\n"
            ")\n",
            "pymdownx.snippets",
        ),
        (
            "import markdown\n"
            "options = {\n"
            "    'extensions': ['pymdownx.b64', pick_extra()],\n"
            "}\n"
            "markdown.Markdown(**options)\n",
            "pymdownx.b64",
        ),
    ),
)
def test_reachability_gate_rejects_literal_pymdown_activation(
    tmp_path, source, extension
):
    tooling = tmp_path / "tooling"
    tooling.mkdir()
    (tooling / "render.py").write_text(source)

    with pytest.raises(
        AssertionError,
        match=rf"activates {re.escape(repr(extension))}",
    ):
        _assert_exception_reachability_controls(tmp_path)


@pytest.mark.parametrize(
    "source",
    (
        (
            "import markdown\n"
            "markdown.markdown(text, extensions=['tables', 'toc'])\n"
        ),
        (
            "import markdown\n"
            "extension = select_extension_at_runtime()\n"
            "markdown.markdown(text, extensions=[extension])\n"
        ),
        (
            "import markdown\n"
            "markdown.Markdown(\n"
            "    extensions=['tables', select_extension_at_runtime()],\n"
            ")\n"
        ),
        (
            "import markdown as md\n"
            "md.markdownFromFile(\n"
            "    input='input.md',\n"
            "    extensions=[select_extension_at_runtime(), 'toc'],\n"
            ")\n"
        ),
        (
            "from markdown import Markdown as Renderer\n"
            "options = {\n"
            "    'extensions': ['tables', select_extension_at_runtime()],\n"
            "}\n"
            "Renderer(**options)\n"
        ),
    ),
)
def test_reachability_gate_allows_safe_or_runtime_markdown_selection(
    tmp_path, source
):
    tooling = tmp_path / "tooling"
    tooling.mkdir()
    (tooling / "render.py").write_text(source)

    _assert_exception_reachability_controls(tmp_path)


def test_click_editor_patch_uses_argv_without_shell_execution():
    source = (
        metadata.distribution("click")
        .locate_file("click/_termui_impl.py")
        .read_text()
    )
    edit_files = re.search(
        r"    def edit_files\(.*?(?=\n    def |\Z)",
        source,
        flags=re.DOTALL,
    )
    assert edit_files is not None
    assert "shlex.split(editor) + list(filenames)" in edit_files.group(0)
    assert "shell=True" not in edit_files.group(0)


def test_pygments_lexer_and_ipython_rich_pytest_rendering_are_exact():
    from IPython.lib.lexers import IPython3Lexer

    source = (
        "def greet(name: str) -> str:\n"
        '    return f"hello {name}"\n'
    )
    lexer = PythonLexer()
    token_rows = [(str(token), value) for token, value in lex(source, lexer)]
    outputs = {
        "tokens": hashlib.sha256(
            json.dumps(token_rows, separators=(",", ":")).encode()
        ).hexdigest(),
        "html": hashlib.sha256(
            highlight(source, lexer, HtmlFormatter(nowrap=True)).encode()
        ).hexdigest(),
        "terminal": hashlib.sha256(
            highlight(source, lexer, TerminalFormatter(bg="dark")).encode()
        ).hexdigest(),
        "ipython_terminal": hashlib.sha256(
            highlight(
                source,
                IPython3Lexer(),
                TerminalFormatter(bg="dark"),
            ).encode()
        ).hexdigest(),
    }
    pytest_writer = TerminalWriter(file=io.StringIO())
    pytest_writer.hasmarkup = True
    pytest_writer.code_highlight = True
    outputs["pytest_terminal"] = hashlib.sha256(
        pytest_writer._highlight(source).encode()
    ).hexdigest()
    rich_console = Console(
        file=io.StringIO(),
        force_terminal=True,
        color_system="standard",
        no_color=False,
        width=80,
    )
    rich_console.print(Syntax(source, "python", theme="ansi_dark"))
    rich_output = rich_console.file.getvalue()
    assert "\x1b[" in rich_output
    outputs["rich_terminal"] = hashlib.sha256(
        rich_output.encode()
    ).hexdigest()
    assert outputs == {
        "tokens": "48953b4016ec793c0e8e23c9baaa7afe2ef8cc40b9605187666490c0071e5f35",
        "html": "c3e57a4263eb74006e0988b6dea2d398bbcabeb4e1b0119bd4fd8dbac899f48c",
        "terminal": "37ebe32a865ffdd7ecd4a5d097375ac299210fc8c16eeb6b9866682e0e0cb401",
        "ipython_terminal": (
            "37ebe32a865ffdd7ecd4a5d097375ac299210fc8c16eeb6b9866682e0e0cb401"
        ),
        "pytest_terminal": (
            "b1c489802e2e3adbbf152619aee2bf48c29798c933a67066cdb53f9d478cf6f4"
        ),
        "rich_terminal": (
            "4a98e8fea362182468a3d6c34cc22bdbc6efb5c4a293833960a382bdaf9afdd5"
        ),
    }


@pytest.mark.parametrize("escape_shape", ("shared-prefix", "parent", "absolute"))
def test_pymdown_snippets_blocks_outside_base_paths(tmp_path, escape_shape):
    base = tmp_path / "docs"
    sibling = tmp_path / "docs-private"
    base.mkdir()
    sibling.mkdir()
    (base / "inside.md").write_text("SAFE_SNIPPET")
    (sibling / "secret.md").write_text("SYNTHETIC_SECRET")
    (tmp_path / "outside.md").write_text("SYNTHETIC_OUTSIDE")

    config = {
        "pymdownx.snippets": {
            "base_path": [str(base)],
            "restrict_base_path": True,
            "check_paths": True,
        }
    }
    safe = markdown.markdown(
        '--8<-- "inside.md"',
        extensions=["pymdownx.snippets"],
        extension_configs=config,
    )
    assert "SAFE_SNIPPET" in safe

    target = {
        "shared-prefix": "../docs-private/secret.md",
        "parent": "../outside.md",
        "absolute": str(sibling / "secret.md"),
    }[escape_shape]
    with pytest.raises(SnippetMissingError, match="could not be found"):
        markdown.markdown(
            f'--8<-- "{target}"',
            extensions=["pymdownx.snippets"],
            extension_configs=config,
        )


def test_pymdown_b64_remains_affected_and_exception_governed(tmp_path):
    base = tmp_path / "docs"
    outside = tmp_path / "outside"
    base.mkdir()
    outside.mkdir()
    image = outside / "synthetic.png"
    payload = b"synthetic-h01-b64-fixture"
    image.write_bytes(payload)

    rendered = markdown.markdown(
        f"![fixture]({image})",
        extensions=["pymdownx.b64"],
        extension_configs={"pymdownx.b64": {"base_path": str(base)}},
    )
    assert base64.b64encode(payload).decode() in rendered

    evidence = EVIDENCE.read_text()
    section = _exception_section(evidence, "EX-H01-PYMDOWN-B64-01")
    assert "CVE-2026-61632" in evidence
    assert "11.0.0" in evidence
    assert "**Compensating controls:**" in section
    assert "EX-H01-PYMDOWN-B64-01" in RETAINED_EXCEPTION_IDS


def test_s1_exact_runtime_profile_matches_the_approved_lock():
    pins = _pins(LOCK)
    s1 = S1.read_text()
    assert pins["titanoboa"] == "0.2.7"
    assert pins["pytest"] == "8.4.2"
    assert '{"titanoboa": "0.2.7", "pytest": "8.4.2"}' in s1
    assert 'version("titanoboa") == "0.2.7"' in s1
    assert 'version("pytest") == "8.4.2"' in s1

    evidence = EVIDENCE.read_text()
    normalized = " ".join(evidence.split())
    assert "### pytest, Titanoboa, and Vyper" in evidence
    assert "Vyper 0.4.3 requires" in normalized
    assert "pytest `8.4.2` is the exact S1-reviewed runtime" in normalized


class _RecordingAdapter(BaseAdapter):
    def __init__(self, error: Exception | None = None):
        self.error = error
        self.request = None
        self.kwargs = None

    def send(self, request, **kwargs):
        self.request = request
        self.kwargs = kwargs
        if self.error is not None:
            raise self.error
        response = requests.Response()
        response.status_code = 200
        response.url = request.url
        response.request = request
        response._content = b"ok"
        return response

    def close(self):
        return None


def test_requests_transport_configuration_is_preserved_without_network():
    session = requests.Session()
    adapter = _RecordingAdapter()
    session.mount("https://", adapter)
    response = session.get(
        "https://example.test/path",
        timeout=(1.0, 2.0),
        verify="/tmp/h01-ca.pem",
        proxies={"https": "http://proxy.invalid:8080"},
    )
    assert response.content == b"ok"
    assert adapter.request.url == "https://example.test/path"
    assert adapter.kwargs["timeout"] == (1.0, 2.0)
    assert adapter.kwargs["verify"] == "/tmp/h01-ca.pem"
    assert adapter.kwargs["proxies"]["https"] == "http://proxy.invalid:8080"

    retry_adapter = HTTPAdapter(
        max_retries=Retry(total=2, status_forcelist={429, 503})
    )
    assert retry_adapter.max_retries.total == 2
    assert retry_adapter.max_retries.status_forcelist == {429, 503}

    redirect = requests.Response()
    redirect.status_code = 302
    redirect.headers["location"] = "/next"
    assert session.get_redirect_target(redirect) == "/next"

    failing = requests.Session()
    failing.mount("https://", _RecordingAdapter(ConnectTimeout("offline")))
    with pytest.raises(ConnectTimeout, match="offline"):
        failing.get("https://example.test/path", timeout=0.01)


def test_idna_normalization_and_rejection_are_preserved():
    prepared = requests.PreparedRequest()
    prepared.prepare_url("https://bücher.example/path", None)
    assert prepared.url == "https://xn--bcher-kva.example/path"
    assert idna.decode(idna.encode("bücher.example")) == "bücher.example"
    with pytest.raises(idna.IDNAError):
        idna.encode("\u200d.example")


def test_dotenv_search_interpolation_and_precedence(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "BASE=base\nCOMPOSED=${BASE}-suffix\nH01_PRECEDENCE=file\n"
    )
    parsed = dotenv_values(env_file)
    assert parsed == {
        "BASE": "base",
        "COMPOSED": "base-suffix",
        "H01_PRECEDENCE": "file",
    }

    monkeypatch.chdir(tmp_path)
    assert find_dotenv(usecwd=True) == str(env_file)
    monkeypatch.setenv("H01_PRECEDENCE", "environment")
    assert load_dotenv(env_file, override=False)
    assert __import__("os").environ["H01_PRECEDENCE"] == "environment"
    assert load_dotenv(env_file, override=True)
    assert __import__("os").environ["H01_PRECEDENCE"] == "file"


def test_cbor_and_wheel_metadata_are_stable():
    encoded = cbor2.dumps({"b": 2, "a": 1}, canonical=True)
    assert encoded.hex() == "a2616101616202"
    assert cbor2.loads(encoded) == {"a": 1, "b": 2}

    wheel_metadata = metadata.distribution("wheel").read_text("WHEEL")
    assert wheel_metadata is not None
    assert "Wheel-Version: 1.0" in wheel_metadata


def test_dependency_gate_has_no_external_query_or_process_runner():
    source = Path(__file__).read_text()
    tree = ast.parse(source)
    imported_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_roots |= {
        node.module.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert imported_roots.isdisjoint({"http", "subprocess", "urllib", "aiohttp"})
    assert "gh " + "api" not in source
    assert "pip_" + "audit" not in source
