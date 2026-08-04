"""Build the production execution envelope and plan for a Robinhood deployment.

`migrate.py --live` needs two files: a plan and the envelope bound into it. The
only envelope that existed was a TEST fixture that fabricates placeholder
addresses, which is fine for proving mechanics and unusable for a real launch.
This produces the real one.

The envelope is an ACCEPTANCE record, not a discovery mechanism. Most of the
values already exist in `config/BluePrint.py` -- verified external addresses,
approved parameters, owner decisions. What the envelope adds is an explicit,
hash-stamped record that the deployment owner accepts each one. So this script
SOURCES values and refuses to invent them: every reference it cannot justify
from the blueprint or a recorded decision is reported and the run fails, rather
than being filled with a plausible-looking default.

Usage:
    python scripts/build_execution_envelope.py --deployer 0xYourLedgerAddress

Writes, under migration_history/<profile>/v1/pending/ by default:
    execution-envelope.json   the accepted values
    execution-plan.json       the plan those values bind

Review both before passing them to migrate.py. Nothing here touches a chain.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ZERO = "0x" + "0" * 40
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")


def _typed(reference: str, type_name: str, value, authority: str):
    """Stamp one accepted value with the authority that justifies it."""
    return {
        "type": type_name,
        "value": value,
        "authority_ref": authority,
        "evidence_sha256": hashlib.sha256(
            f"{authority}:{reference}:{value!r}".encode("utf-8")
        ).hexdigest(),
    }


class Unjustified(Exception):
    """Raised when a reference has no value this script may legitimately set."""


def _resolve(reference, blueprint, deployer, curve_rows, stock_rows):
    """Return (type, value, authority) for one blocked reference.

    Raises Unjustified when the value is a genuine owner decision that has not
    been recorded anywhere. That is the point: an envelope built from guesses
    would deploy a protocol nobody approved.
    """
    namespace, key = reference.split(":", 1)
    lowered = key.casefold()

    if namespace == "address":
        value = blueprint.ROBINHOOD_ADDRESSES.get(key)
        if isinstance(value, str) and ADDRESS_RE.match(value):
            return "address", value, "BluePrint.ROBINHOOD_ADDRESSES (verified on-chain)"
        raise Unjustified("no verified address in ROBINHOOD_ADDRESSES")

    if namespace == "input":
        row = blueprint.ROBINHOOD_DEPLOYMENT_INPUTS[key]
        if row.disposition == "external_fact":
            return "address", row.value, "BluePrint external_fact (verified on-chain)"
        if key == "Deployment.DP-19.supply.RIPE.recipient":
            return (
                "address",
                blueprint.ROBINHOOD_GOVERNANCE,
                "owner decision: 100k RIPE to the governance Safe, as Base minted to GOVERNANCE",
            )
        if key == "Deployment.DP-19.supply.SGREEN.recipient":
            return (
                "address", ZERO,
                "supply is 0 and Erc20Token skips a zero-supply credit; Base passed ZERO_ADDRESS",
            )
        if key == "Deployment.DP-18.roles.trainingWheelsAllowlist":
            return "address-array", [], "owner decision: empty allowlist at launch"
        if lowered.endswith(".guardian"):
            return (
                "address",
                blueprint.ROBINHOOD_GOVERNANCE,
                "owner decision: evidentiary role, the Safe holds the powers it names",
            )
        if lowered.endswith("nativesymbol"):
            return "string", "ETH", "Robinhood native currency"
        if lowered.endswith("nativename"):
            return "string", "Ether", "Robinhood native currency"
        if lowered.endswith("nativedecimals"):
            return "uint256", 18, "Robinhood native currency"
        if key.startswith("Deployment.DP-08.psm."):
            # Stage 0800 deploys the PSM disabled. Zero fees and zero caps mean
            # that even if it were enabled by mistake, nothing can be minted or
            # redeemed through it. numBlocksPerInterval must be nonzero to
            # avoid a division-by-zero shape in interval maths.
            if key.endswith("numBlocksPerInterval"):
                return "uint256", 1, "PSM disabled at launch; nonzero interval only"
            return "uint256", 0, "PSM disabled at launch; zero fees and caps"
        if isinstance(row.value, bool):
            return "boolean", row.value, "BluePrint approved value"
        if isinstance(row.value, int):
            return "uint256", row.value, "BluePrint approved value"
        raise Unjustified(f"unresolved deployment input ({row.disposition})")

    if namespace == "binding":
        if key == "temporary-local-governance":
            return "address", deployer, "owner decision: the Ledger deploys and governs until handoff"
        if key == "green-supply-recipient":
            return "address", deployer, "the deployer seeds the GREEN/USDG pool in 0600"
        if key in {"no-local-governance", "initial-ripe-hq"}:
            return "address", ZERO, "LocalGov asserts _initialGov != hqGov; departments hold none"
        if key == "reward-qualified-lite-signer-identity-if-used":
            return "address", ZERO, "not used; psm-lite-signer-posture-zero is asserted alongside"
        if key in {"operator-identity", "release-signer-identity", "reward-governance-identity"}:
            return (
                "address",
                blueprint.ROBINHOOD_GOVERNANCE,
                "owner decision: evidentiary role, the Safe holds the powers it names",
            )
        if key.startswith("bluechip-"):
            # Only Morpho V2 exists on Robinhood, and it is bound separately as
            # a DP-23 external fact. A zero registry fails closed: Vyper checks
            # extcodesize, so registering an asset against one reverts.
            array = key.endswith("-factories")
            return (
                ("address-array", [ZERO, ZERO]) if array else ("address", ZERO)
            ) + ("owner decision: protocol absent on Robinhood; zero fails closed",)
        raise Unjustified("owner parameter or acceptance record")

    if namespace == "curve":
        row = curve_rows[key]
        if key == "pool.address":
            return "address", ZERO, "create path: no GREEN/USDG pool can pre-exist"
        if "address_provider_binding_" in key:
            return "json", list(row.value), "BluePrint curve authority (verified on-chain)"
        if key == "curve.address_provider":
            return "address", row.value, "BluePrint curve authority (verified on-chain)"
        raise Unjustified("owner curve decision")

    if namespace == "stock":
        raise Unjustified("AAPL stock lane is deferred and not part of this launch")

    raise Unjustified(f"unknown namespace {namespace}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default="robinhood-mainnet")
    parser.add_argument(
        "--deployer",
        required=True,
        help="The Ledger address that deploys and holds governance until 0900.",
    )
    parser.add_argument("--out", default=None, help="Output directory.")
    args = parser.parse_args()

    if not ADDRESS_RE.match(args.deployer):
        raise SystemExit(f"--deployer must be an address, got {args.deployer!r}")

    from config import BluePrint as blueprint
    from scripts.utils.migration_runner import build_robinhood_plan

    plan = build_robinhood_plan(args.profile, repository_root=ROOT)
    curve_rows = {r.input_id: r for r in blueprint.ROBINHOOD_CURVE_LAUNCH_INPUTS}
    stock_rows = {r.path: r for r in blueprint.ROBINHOOD_STOCK_INPUT_QUALIFICATIONS}

    references = sorted(
        {
            ref
            for detail in plan["blocker_details"]
            for ref in detail["references"]
            if not ref.startswith("reservation:")
        }
    )

    values, unjustified = {}, []
    for reference in references:
        try:
            type_name, value, authority = _resolve(
                reference, blueprint, args.deployer, curve_rows, stock_rows
            )
        except Unjustified as reason:
            unjustified.append((reference, str(reason)))
            continue
        values[reference] = _typed(reference, type_name, value, authority)

    print(f"references needing a value : {len(references)}")
    print(f"  sourced from authority   : {len(values)}")
    print(f"  needing an owner decision: {len(unjustified)}")

    if unjustified:
        print(
            "\nThese have no recorded authority. Each is a real decision, not a\n"
            "gap this script may fill -- an envelope built from guesses would\n"
            "deploy a protocol nobody approved.\n"
        )
        for reference, reason in unjustified:
            print(f"  {reference:64} {reason}")
        print(
            f"\nRecord these in config/BluePrint.py (or as an owner decision here),\n"
            "then re-run. No files were written."
        )
        return 1

    out = Path(args.out) if args.out else (
        ROOT / "migration_history" / args.profile / "v1" / "pending"
    )
    out.mkdir(parents=True, exist_ok=True)
    envelope = {
        "schema": "ripe.robinhood.execution-envelope.v1",
        "profile_id": args.profile,
        "values": values,
    }
    bound = build_robinhood_plan(
        args.profile, repository_root=ROOT, execution_envelope=envelope
    )
    (out / "execution-envelope.json").write_text(
        json.dumps(envelope, indent=2, sort_keys=True) + "\n"
    )
    (out / "execution-plan.json").write_text(
        json.dumps(bound, indent=2, sort_keys=True) + "\n"
    )
    print(f"\nplan status: {bound['status']}")
    print(f"wrote {out}/execution-envelope.json")
    print(f"wrote {out}/execution-plan.json")
    print("\nReview both before passing them to migrate.py. Nothing touched a chain.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
