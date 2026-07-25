from __future__ import annotations

import ast
import hashlib
import re
from importlib import metadata
from pathlib import Path

import cbor2
import idna
import pytest
import requests
from dotenv import dotenv_values, find_dotenv, load_dotenv
from requests.adapters import BaseAdapter, HTTPAdapter
from requests.exceptions import ConnectTimeout
from urllib3.util import Retry


ROOT = Path(__file__).resolve().parents[2]
DIRECT_INPUT = ROOT / "requirements.in"
LOCK = ROOT / "requirements.txt"
EVIDENCE = ROOT / "docs/chains/rh/evidence/dependency-security-gate.md"
S1 = ROOT / "tests/clock/test_clock_profiles.py"

APPROVED_HASHES = {
    DIRECT_INPUT: "2523c04409946a6625e30e5e4aa4f711663924f4a674f4cfd5fee5b7bbb3b80d",
    LOCK: "d2e12a6f0cfd128c3891634efafbba8305878bef7a7c5db33e25ebe93b0d2bce",
}
SELECTED = {
    "cbor2": "5.9.0",
    "idna": "3.15",
    "python-dotenv": "1.2.2",
    "requests": "2.33.0",
    "urllib3": "2.7.0",
    "wheel": "0.46.2",
}
HELD = {
    "click": "8.2.1",
    "pygments": "2.19.2",
    "pymdown-extensions": "10.16.1",
    "pytest": "8.4.2",
    "titanoboa": "0.2.7",
    "vyper": "0.4.3",
}
RESIDUAL_FINDINGS = {
    "PYSEC-2026-2132": "EX-H01-CLICK-01",
    "PYSEC-2026-1845": "EX-H01-PYTEST-01",
    "PYSEC-2026-2987": "EX-H01-PYGMENTS-01",
    "PYSEC-2026-2999": "EX-H01-PYMDOWN-SNIPPETS-01",
    "CVE-2026-61632": "EX-H01-PYMDOWN-B64-01",
    "PYSEC-2023-142": "authoritative range exclusion",
    "PYSEC-2025-33": "authoritative range exclusion",
}
EXCEPTION_IDS = {
    "EX-H01-CLICK-01",
    "EX-H01-PYTEST-01",
    "EX-H01-PYGMENTS-01",
    "EX-H01-PYMDOWN-SNIPPETS-01",
    "EX-H01-PYMDOWN-B64-01",
}
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
    Path("scripts/console.py"),
    Path("scripts/migrate.py"),
    Path("scripts/verify.py"),
}


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


def _exception_section(evidence: str, exception_id: str) -> str:
    match = re.search(
        rf"#### `{re.escape(exception_id)}`.*?(?=\n#### |\n### )",
        evidence,
        flags=re.DOTALL,
    )
    assert match is not None, f"missing exception section {exception_id}"
    return match.group(0)


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


def _python_reachability_violations(path: Path, root: Path) -> list[str]:
    relative = path.relative_to(root)
    try:
        tree = ast.parse(path.read_text(), filename=str(relative))
    except (SyntaxError, UnicodeDecodeError) as error:
        return [f"{relative}: cannot AST-scan Python source: {error}"]

    aliases: dict[str, str] = {}
    violations: list[str] = []
    for node in ast.walk(tree):
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
        if not resolved_call or not resolved_call.startswith("pygments."):
            continue
        if resolved_call.endswith(".get_lexer_by_name") and node.args:
            lexer_name = node.args[0]
            if isinstance(lexer_name, ast.Constant) and isinstance(
                lexer_name.value, str
            ):
                if lexer_name.value.lower() in {"adl", "archetype"}:
                    violations.append(
                        f"{relative}:{node.lineno}: selects Pygments "
                        f"{lexer_name.value!r} lexer"
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


def test_selected_and_held_versions_match_lock_and_runtime():
    pins = _pins(LOCK)
    expected = SELECTED | HELD
    for package, version in expected.items():
        assert pins[package] == version
        assert metadata.version(package) == version

    # These lower versions are the vulnerable frozen-lock values displaced by
    # Candidate A. Exact approved pins above make the range check fail closed.
    forbidden = {
        "cbor2": {"5.7.0"},
        "idna": {"3.10"},
        "python-dotenv": {"1.2.1"},
        "requests": {"2.32.5"},
        "urllib3": {"2.5.0", "2.6.0", "2.6.2", "2.6.3"},
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
    for package in SELECTED | HELD:
        assert metadata.distribution(package).read_text("direct_url.json") is None


def test_evidence_reconciles_every_selected_package_and_residual_finding():
    evidence = EVIDENCE.read_text()
    normalized = " ".join(evidence.split())
    for package in SELECTED | HELD:
        assert package in evidence.lower()
    for finding, disposition in RESIDUAL_FINDINGS.items():
        assert finding in evidence
        assert disposition in evidence

    assert "The two Vyper determinations are not exceptions" in normalized
    assert "no `--ignore-vuln` flags" in normalized
    assert "all five bounded exceptions" in normalized
    assert "both Vyper dispositions" in normalized


def test_bounded_exceptions_are_explicit_and_workflow_gated():
    evidence = EVIDENCE.read_text()
    normalized = " ".join(evidence.split())
    assert "Mick Hagen, H-01 owner" in evidence
    assert "15 August 2026" in evidence
    assert "2026-08-31T23:59:59Z" in evidence
    assert "An expired exception blocks deployment rehearsal and merge" in evidence

    for exception_id in EXCEPTION_IDS:
        section = _exception_section(evidence, exception_id)
        assert "**Threat model:**" in section
        assert "**Scope:**" in section
        assert "**Compensating controls:**" in section
        assert "**Re-review/invalidation triggers:**" in section

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


def test_dependency_gate_has_no_live_query_capability():
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
    assert imported_roots.isdisjoint(
        {"http", "socket", "subprocess", "urllib", "aiohttp"}
    )
    assert "gh " + "api" not in source
    assert "pip_" + "audit" not in source
