"""Safety and provenance for diagnostics; never changes the Boa environment."""

import hashlib
import re
from importlib.metadata import version
from pathlib import Path
import subprocess
from urllib.parse import parse_qsl, quote, unquote, urlsplit

SANITIZER_VERSION = "fork-report-v3"


def require_unoptimized():
    if not __debug__:
        raise RuntimeError("FORK_DIAGNOSTIC_OPTIMIZED_PYTHON_UNSUPPORTED")


def require_new_report(path, overwrite=False):
    if Path(path).exists() and not overwrite:
        raise RuntimeError("REPORT_EXISTS: choose a fresh path or pass --overwrite")


def sanitize(value, rpc, root, credential_query_keys=()):
    """Redact full URLs and split provider errors, including nested trace data."""
    parts = urlsplit(rpc)
    secrets = {rpc, unquote(rpc), parts.netloc, parts.username or "", parts.password or ""}
    credential_keys = {"key", "apikey", "api_key", "token", "secret", "auth",
                       "access_token", "password", *credential_query_keys}
    secrets.update(v for k, v in parse_qsl(parts.query) if k.lower() in credential_keys and v)
    # Conventional endpoint segments are not credentials. Other segments may be
    # short provider keys; do not substitute generic words like rpc or base.
    public_segments = {"rpc", "v1", "v2", "v3", "api", "eth", "http", "https",
                       "base", "mainnet", "base-mainnet", "ethereum", "public"}
    secrets.update(s for s in unquote(parts.path).split("/") if s and s.lower() not in public_segments)
    secrets |= {unquote(s) for s in tuple(secrets)}
    secrets.discard("")
    secrets.discard("/")
    secrets |= {quote(s, safe="") for s in tuple(secrets)}

    def clean(v):
        if isinstance(v, str):
            for secret in sorted(secrets, key=len, reverse=True):
                v = v.replace(secret, "<RPC>")
            if parts.hostname:
                v = re.sub(re.escape(parts.hostname), "<RPC>", v, flags=re.IGNORECASE)
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
        ("migration_history/base-mainnet/v1", {".json"}),
        ("tests/fixtures/legacy_pool", {".vy", ".vyi", ".json"}),
    ):
        paths.update(p for p in (root / directory).rglob("*") if p.suffix in suffixes)
    paths.update(p for p in (root / "docs/chains/base/fork-rehearsal/full-update-final.json",
                             root / "docs/chains/base/legacy-vault-rehearsal/review-qualification.json") if p.exists())
    paths.update(Path(p).resolve() for p in extra_paths)
    paths.update([root / "requirements.txt", root / "migration_history/base-mainnet/v1/current-manifest.json"])
    return {
        "source_tree": subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=root, text=True).strip(),
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
        "dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True).strip()),
        "scope": "conservative project-input superset, including selected Defaults and manifest",
        "sha256": {str(p.relative_to(root)) if p.is_relative_to(root) else p.name:
                   hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)},
        "tools": {name: version(name) for name in ("titanoboa", "vyper", "web3")},
    }
