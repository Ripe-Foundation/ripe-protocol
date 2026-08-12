import json
import os
import re
import time
from pathlib import Path

import click

from scripts.migrate import param_prompt, CLICK_PROMPTS
from scripts.utils.verify_etherscan import CHAIN_SPECS, verify_from_manifest

MIGRATION_HISTORY_DIR = "./migration_history"

# scripts/verify_blockscout.py targets Robinhood mainnet only, so that is the
# one chain we can honestly redirect to it. Pointing anything else there --
# a typo, `local`, a retired network -- would be false advice.
BLOCKSCOUT_CHAINS = frozenset({"robinhood-mainnet"})

# One path segment: must start alphanumeric, and may then carry only
# alphanumerics, dot, dash or underscore. That admits `v1`, `v2` and
# `current`, and excludes separators, `.`, `..`, absolute paths and empties.
_SEGMENT_RE = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._-]*\Z")


def _canonical_segment(value, option):
    """Return `value` if it is a single safe path segment, else refuse.

    The rejected value is deliberately not echoed. It is caller-controlled,
    and repeating it back writes the attempted path into terminal scrollback
    and CI logs.
    """
    if not isinstance(value, str) or not _SEGMENT_RE.match(value):
        raise click.ClickException(
            f"--{option} must be a single path segment matching "
            "[A-Za-z0-9][A-Za-z0-9._-]* -- no separators, no '.' or '..', "
            "not absolute. The rejected value is not echoed."
        )
    return value


def _history_manifest_path(chain, environment, manifest):
    """Resolve the manifest path and prove it stays inside the history tree."""
    root = Path(MIGRATION_HISTORY_DIR).resolve()
    candidate = (
        root / chain / environment / f"{manifest}-manifest.json"
    ).resolve()
    # The segment rules already forbid traversal. Re-checking the *resolved*
    # path is what stops a symlink planted inside the tree from widening it,
    # and it is cheap next to submitting contract records with a live key.
    if not candidate.is_relative_to(root):
        raise click.ClickException(
            "Resolved manifest path escapes the migration history directory."
        )
    return candidate


def _migration_owners(chain, environment):
    """Map (contract, address) -> the migration timestamp that deployed it.

    Numbered step manifests record the address each migration deployed. Where
    that address is still the one in `current-manifest.json`, that migration
    deployed the live generation. Matching on the address rather than the name
    is what makes it exact: a redeployed contract appears in several steps, and
    only the one holding the live address is the current owner.

    Step manifests carry address and file only -- they are a record, not a
    payload -- so this reads them for attribution only. Everything submitted
    comes from the current manifest.
    """
    owners = {}
    history = _history_manifest_path(chain, environment, "current").parent
    steps = sorted(
        history.glob("[0-9]*-manifest.json"),
        key=lambda path: int(path.name.split("-", 1)[0]),
    )
    for path in steps:
        timestamp = path.name.split("-", 1)[0]
        try:
            contracts = json.loads(path.read_text()).get("contracts", {})
        except (OSError, json.JSONDecodeError):
            continue
        for name, record in contracts.items():
            address = record.get("address") if isinstance(record, dict) else None
            if address:
                owners.setdefault((name, address), timestamp)
    return owners


def _rows(contracts, owners):
    """One selectable row per contract, in manifest order."""
    rows = []
    for name, record in contracts.items():
        address = record.get("address", "") if isinstance(record, dict) else ""
        rows.append(
            {
                "name": name,
                "address": address,
                "migration": owners.get((name, address)),
                # deploy_solidity records an address only; Foundry artifacts
                # have no Vyper standard-JSON equivalent to submit.
                "verifiable": isinstance(record, dict)
                and isinstance(record.get("solc_json"), dict),
                "record": record,
            }
        )
    return rows


def _short(address):
    return f"{address[:8]}…{address[-4:]}" if len(address) > 14 else address


def _render(rows):
    width = max((len(r["name"]) for r in rows), default=8)
    lines = []
    for index, row in enumerate(rows, start=1):
        flag = " " if row["verifiable"] else "-"
        note = "" if row["verifiable"] else "  (no solc_json, cannot verify)"
        lines.append(
            f" {flag}{index:>3}  {row['name']:<{width}}  "
            f"{row['migration'] or '?':<12}  {_short(row['address'])}{note}"
        )
    return "\n".join(lines)


def _parse_selection(text, rows):
    """Turn `all` / `none` / `1,3,5-8` / `m:2026080700` into row indices."""
    text = (text or "").strip().lower()
    if text in ("", "none", "q", "quit"):
        return []
    if text == "all":
        return [i for i, r in enumerate(rows) if r["verifiable"]]

    chosen = set()
    for token in (piece.strip() for piece in text.split(",") if piece.strip()):
        if token.startswith(("m:", "migration:")):
            wanted = token.split(":", 1)[1].strip()
            hits = [i for i, r in enumerate(rows) if r["migration"] == wanted]
            if not hits:
                raise click.ClickException(
                    f"No contracts in this manifest were deployed by migration {wanted}."
                )
            chosen.update(hits)
            continue
        if "-" in token:
            start, _, end = token.partition("-")
            try:
                lo, hi = int(start), int(end)
            except ValueError:
                raise click.ClickException(f"Not a range: {token}")
            if lo > hi:
                lo, hi = hi, lo
            chosen.update(range(lo - 1, hi))
            continue
        try:
            chosen.add(int(token) - 1)
        except ValueError:
            raise click.ClickException(
                f"Not a number, range, or m:<migration>: {token}"
            )

    out_of_range = [i + 1 for i in chosen if not 0 <= i < len(rows)]
    if out_of_range:
        raise click.ClickException(
            f"Out of range (1-{len(rows)}): {', '.join(map(str, sorted(out_of_range)))}"
        )
    return sorted(chosen)


@click.command()
@click.option(
    "--environment",
    default=CLICK_PROMPTS["environment"]["default"],
    help=CLICK_PROMPTS["environment"]["help"],
    callback=param_prompt,
)
@click.option(
    "--chain",
    default=CLICK_PROMPTS["chain"]["default"],
    help=CLICK_PROMPTS["chain"]["help"],
    callback=param_prompt,
)
@click.option(
    "--manifest",
    default=CLICK_PROMPTS["manifest"]["default"],
    help=CLICK_PROMPTS["manifest"]["help"],
    callback=param_prompt,
)
@click.option(
    "--contracts",
    default="",
    help="Comma-separated contract names to verify. Skips the checklist.",
)
@click.option(
    "--migration",
    default="",
    help=(
        "Verify the contracts whose live deployment came from this migration "
        "timestamp, e.g. 2026080700. Skips the checklist."
    ),
)
@click.option(
    "--all",
    "verify_all",
    is_flag=True,
    default=False,
    help="Verify every verifiable contract in the manifest. Skips the checklist.",
)
def cli(
    environment,
    chain,
    manifest,
    # Defaulted so `cli.callback(environment, chain, manifest)` keeps working:
    # the secret-handling and profile-regression suites call it that way to
    # assert the chain guard runs before the explorer key is read.
    contracts="",
    migration="",
    verify_all=False,
):
    """Verify contracts on Etherscan/Basescan.

    Reads the manifest (`current` by default) and offers a checklist so a run
    can submit one migration's contracts rather than all of them. Verification
    is deliberately separate from deployment: submitting is its own failure
    surface and does not belong in the middle of a migration.

    Robinhood chains have no Etherscan-family explorer -- see
    `scripts/verify_blockscout.py` for those.
    """
    # Validate every input before constructing -- let alone printing -- a path.
    # An unknown chain and a known chain without a verifier are different
    # failures and get different advice; conflating them tells someone with a
    # typo to go use the Robinhood Blockscout script.
    spec = CHAIN_SPECS.get(chain) if isinstance(chain, str) else None
    if spec is None:
        raise click.ClickException(
            "Unknown chain. Supported chains: "
            + ", ".join(sorted(CHAIN_SPECS))
            + "."
        )
    if spec.provider is None:
        # Safe to echo now: `chain` is a canonical key, not free text.
        hint = (
            " Use `python -m scripts.verify_blockscout` for that chain."
            if chain in BLOCKSCOUT_CHAINS
            else ""
        )
        raise click.ClickException(
            f"Chain `{chain}` has no Etherscan-family verifier configured."
            + hint
        )

    environment = _canonical_segment(environment, "environment")
    manifest = _canonical_segment(manifest, "manifest")
    manifest_path = _history_manifest_path(chain, environment, manifest)

    print(f"Verifying contracts from chain `{chain}`, manifest `{manifest_path}`")

    if not manifest_path.exists():
        raise click.ClickException(f"No manifest found at {manifest_path}")

    # Either spelling is accepted: `migrate` reads BASESCAN_API_KEY for the
    # Base chains, while CI and older docs use ETHERSCAN_API_KEY.
    api_key = os.getenv("ETHERSCAN_API_KEY") or os.getenv("BASESCAN_API_KEY")
    if not api_key:
        raise click.ClickException(
            "Neither ETHERSCAN_API_KEY nor BASESCAN_API_KEY is set."
        )

    with open(manifest_path, "r") as f:
        manifest_data = json.load(f)

    rows = _rows(
        manifest_data["contracts"], _migration_owners(chain, environment)
    )
    if not rows:
        raise click.ClickException(f"No contracts in {manifest_path}.")

    # A numbered step manifest is a record of what a migration deployed --
    # address, file, args -- and deliberately carries no solc_json, which is
    # what verification submits. Only current-manifest.json has it. Say so
    # once, up front, rather than listing every row as unverifiable.
    if manifest.isdigit() and not any(row["verifiable"] for row in rows):
        raise click.ClickException(
            f"{manifest_path.name} is a step manifest: it records which "
            f"contracts migration {manifest} deployed and where, but carries "
            "no compiler output to submit. To verify what that migration "
            f"deployed, use the current manifest: --migration {manifest}"
        )

    if sum(bool(flag) for flag in (contracts, migration, verify_all)) > 1:
        raise click.ClickException(
            "Use only one of --contracts, --migration, --all."
        )

    if contracts:
        wanted = [name.strip() for name in contracts.split(",") if name.strip()]
        by_name = {row["name"]: index for index, row in enumerate(rows)}
        unknown = [name for name in wanted if name not in by_name]
        if unknown:
            raise click.ClickException(
                f"Not in this manifest: {', '.join(unknown)}"
            )
        selected = sorted(by_name[name] for name in wanted)
    elif migration:
        selected = _parse_selection(f"m:{migration}", rows)
    elif verify_all:
        selected = _parse_selection("all", rows)
    else:
        click.echo(f"\n{len(rows)} contracts in {manifest_path.name}:\n")
        click.echo(_render(rows))
        click.echo(
            "\nSelect: all | none | 1,3,5-8 | m:<migration>   "
            "(rows marked '-' have no solc_json and are skipped by 'all')"
        )
        selected = _parse_selection(click.prompt("Verify", default="none"), rows)

    skipped = [rows[i]["name"] for i in selected if not rows[i]["verifiable"]]
    if skipped:
        raise click.ClickException(
            "These have no solc_json and cannot be submitted: "
            + ", ".join(skipped)
        )
    if not selected:
        click.echo("Nothing selected.")
        return

    chosen = [rows[i] for i in selected]
    click.echo(f"\nSubmitting {len(chosen)} of {len(rows)}:")
    for row in chosen:
        click.echo(f"  {row['name']}  ({row['migration'] or '?'})")
    if not verify_all and not contracts and not migration:
        click.confirm("\nProceed", abort=True)

    failed = []
    for position, row in enumerate(chosen, start=1):
        name = row["name"]
        click.echo(f"\n[{position}/{len(chosen)}] Verifying {name}...")
        success = verify_from_manifest(
            api_key=api_key,
            contract_name=name,
            manifest_data=row["record"],
            chain=chain,
        )
        if success:
            click.echo(f"✅ {name} verified successfully")
        else:
            failed.append(name)
            click.echo(f"❌ {name} verification failed")

        # Stay under the explorer's rate limit between submissions.
        if position < len(chosen):
            time.sleep(1)

    click.echo(f"\nVerified {len(chosen) - len(failed)}/{len(chosen)} contracts.")
    if failed:
        # Exit non-zero so a CI or scripted run does not read as success.
        raise click.ClickException(f"Verification failed for: {', '.join(failed)}")


if __name__ == "__main__":
    cli()
