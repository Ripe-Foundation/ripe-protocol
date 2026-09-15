"""Safety and provenance for diagnostics; never changes the Boa environment."""

import hashlib
from importlib.metadata import version
from pathlib import Path
import subprocess
from urllib.parse import parse_qsl, quote, unquote, urlsplit

SANITIZER_VERSION = "fork-report-v2"


def require_unoptimized():
    if not __debug__:
        raise RuntimeError("FORK_DIAGNOSTIC_OPTIMIZED_PYTHON_UNSUPPORTED")


def require_new_report(path, overwrite=False):
    if Path(path).exists() and not overwrite:
        raise RuntimeError("REPORT_EXISTS: choose a fresh path or pass --overwrite")


def sanitize(value, rpc, root):
    """Redact full URLs and split provider errors, including nested trace data."""
    parts = urlsplit(rpc)
    secrets = {rpc, unquote(rpc), parts.netloc, parts.hostname or "",
               parts.path, unquote(parts.path), parts.username or "", parts.password or ""}
    secrets.update(v for _, v in parse_qsl(parts.query) if v)
    # Providers commonly embed credentials in a path segment, not a query.
    secrets.update(segment for segment in unquote(parts.path).split("/") if len(segment) >= 8)
    secrets.discard("")
    secrets.discard("/")
    secrets |= {quote(s, safe="") for s in tuple(secrets)}

    def clean(v):
        if isinstance(v, str):
            for secret in sorted(secrets, key=len, reverse=True):
                v = v.replace(secret, "<RPC>")
            v = v.replace(str(root) + "/", "")
            v = v.replace(str(Path.home()) + "/", "<user>/")
            return v
        if isinstance(v, dict):
            return {clean(k): clean(x) for k, x in v.items()}
        if isinstance(v, (list, tuple)):
            return [clean(x) for x in v]
        return v
    return clean(value)


def fingerprint(root, extra_paths=()):
    """Conservative superset of project inputs; excludes environment/key files."""
    paths = set()
    for directory, suffixes in (
        ("contracts", {".vy", ".vyi", ".json"}),
        ("interfaces", {".vy", ".vyi", ".json"}),
        ("scripts", {".py"}), ("config", {".py", ".json"}),
        ("migrations/base-mainnet", {".py"}),
    ):
        paths.update(p for p in (root / directory).rglob("*") if p.suffix in suffixes)
    paths.update(Path(p).resolve() for p in extra_paths)
    paths.update([root / "requirements.txt", root / "migration_history/base-mainnet/v1/current-manifest.json"])
    return {
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
        "dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True).strip()),
        "scope": "conservative project-input superset, including selected Defaults and manifest",
        "sha256": {str(p.relative_to(root)) if p.is_relative_to(root) else p.name:
                   hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)},
        "tools": {name: version(name) for name in ("titanoboa", "vyper", "web3")},
    }
