from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
from typing import Any, Mapping

import pytest

from config import BluePrint as source_blueprint
from scripts.utils.migration_runner import build_robinhood_plan
from scripts.utils.manifest_schema import validate_execution_handoff


OWNER = "0x" + "1" * 40
TEMPORARY_GOVERNANCE = "0x" + "2" * 40
ZERO = "0x" + "0" * 40
ACCEPTED_RESERVATION_BLOCKERS = [
    "B-PSM-SEQUENCE",
    "B-REWARD-PROMOTION",
    "B-T8-FREEZE",
    "B-T8-M5",
]


def _identity(root: Path) -> tuple[str, str]:
    values = []
    for revision in ("HEAD", "HEAD^{tree}"):
        values.append(
            subprocess.run(
                ["/usr/bin/git", "rev-parse", revision],
                cwd=root,
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
        )
    return values[0], values[1]


def _typed(reference: str, type_name: str, value: Any) -> Mapping[str, Any]:
    evidence = hashlib.sha256(
        f"test-owner-acceptance:{reference}:{value!r}".encode("utf-8")
    ).hexdigest()
    return {
        "type": type_name,
        "value": value,
        "authority_ref": "tests/deployment/fully-bound-local-fixture",
        "evidence_sha256": evidence,
    }


def _blocked_references(root: Path, profile_id: str) -> set[str]:
    plan = build_robinhood_plan(profile_id, repository_root=root)
    return {
        reference
        for detail in plan["blocker_details"]
        for reference in detail["references"]
        if not reference.startswith("reservation:")
    }


def build_fully_bound_envelope(
    root: Path,
    profile_id: str,
    *,
    overrides: Mapping[str, tuple[str, Any]] | None = None,
) -> Mapping[str, Any]:
    chain_id = 4663 if profile_id == "robinhood-mainnet" else 46630
    commit, tree = _identity(root)
    override_values = dict(overrides or {})
    values: dict[str, Mapping[str, Any]] = {}
    curve_rows = {
        row.input_id: row for row in source_blueprint.ROBINHOOD_CURVE_LAUNCH_INPUTS
    }
    stock_rows = {
        row.path: row for row in source_blueprint.ROBINHOOD_STOCK_INPUT_QUALIFICATIONS
    }
    for reference in sorted(_blocked_references(root, profile_id)):
        if reference in override_values:
            type_name, value = override_values[reference]
            values[reference] = _typed(reference, type_name, value)
            continue
        namespace, key = reference.split(":", 1)
        if namespace == "address":
            value = source_blueprint.ROBINHOOD_ADDRESSES.get(key, OWNER)
            if not isinstance(value, str):
                value = OWNER
            values[reference] = _typed(reference, "address", value)
        elif namespace == "input":
            row = source_blueprint.ROBINHOOD_DEPLOYMENT_INPUTS[key]
            lowered = key.casefold()
            if row.disposition == "external_fact":
                values[reference] = _typed(reference, "address", row.value)
            elif "sourcebinding" in lowered:
                values[reference] = _typed(reference, "address", ZERO)
            elif key == "Deployment.DP-19.supply.RIPE.recipient":
                # Base minted RIPE to the governance Safe; Robinhood mints the
                # approved 100,000 to the same multi-chain Safe.
                values[reference] = _typed(
                    reference,
                    "address",
                    source_blueprint.ROBINHOOD_GOVERNANCE,
                )
            elif key == "Deployment.DP-19.supply.SGREEN.recipient":
                # Supply is 0 and Erc20Token skips the credit entirely when the
                # supply is zero, so zero here makes the mint impossible rather
                # than merely unused. Base passed the same.
                values[reference] = _typed(reference, "address", ZERO)
            elif lowered.endswith(".guardian"):
                # Evidentiary: no contract reads a guardian, and the Safe holds
                # every power the role describes -- including the unpause that
                # lite signers deliberately cannot do.
                values[reference] = _typed(
                    reference, "address", source_blueprint.ROBINHOOD_GOVERNANCE
                )
            elif any(marker in lowered for marker in (".guardian", ".recipient")):
                values[reference] = _typed(reference, "address", OWNER)
            elif key == "Deployment.DP-18.roles.trainingWheelsAllowlist":
                # Empty at launch by owner decision. Base seeded four addresses
                # here; Robinhood starts with none and adds them afterwards
                # through the normal governed path.
                values[reference] = _typed(reference, "address-array", [])
            elif "allowlist" in lowered or lowered.endswith("litesigners"):
                values[reference] = _typed(reference, "address-array", [OWNER])
            elif key in {
                "Deployment.DP-08.psm.numBlocksPerInterval",
                "Deployment.DP-08.psm.mintFee",
                "Deployment.DP-08.psm.maxMintPerInterval",
                "Deployment.DP-08.psm.redeemFee",
                "Deployment.DP-08.psm.maxRedeemPerInterval",
            }:
                values[reference] = _typed(reference, "uint256", 1)
            elif lowered.endswith("nativesymbol"):
                values[reference] = _typed(reference, "string", "ETH")
            elif lowered.endswith("nativename"):
                values[reference] = _typed(reference, "string", "Ether")
            elif isinstance(row.value, bool):
                values[reference] = _typed(reference, "boolean", row.value)
            elif isinstance(row.value, int):
                values[reference] = _typed(reference, "uint256", row.value)
            elif lowered.endswith("nativedecimals"):
                values[reference] = _typed(reference, "uint256", 18)
            else:
                values[reference] = _typed(reference, "json", {"accepted": True})
        elif namespace == "binding":
            if key == "initial-ripe-hq":
                values[reference] = _typed(reference, "address", ZERO)
            elif key == "temporary-local-governance":
                values[reference] = _typed(
                    reference, "address", TEMPORARY_GOVERNANCE
                )
            elif key == "green-supply-recipient":
                # Receives the initial GREEN supply, so it must be an address --
                # and it must be the DEPLOYER, because the deployer is what
                # seeds the pool later in 0600. Binding this to any other
                # account mints the GREEN somewhere the seed cannot spend it.
                values[reference] = _typed(
                    reference, "address", TEMPORARY_GOVERNANCE
                )
            elif key == "reward-qualified-lite-signer-identity-if-used":
                # "if used" -- and the same action asserts
                # psm-lite-signer-posture-zero, so it is not.
                values[reference] = _typed(reference, "address", ZERO)
            elif key in {
                "operator-identity",
                "release-signer-identity",
                "reward-governance-identity",
            }:
                # Evidentiary records, not on-chain grants: their actions have
                # no `provides`, so nothing is written. The Safe is the
                # authority that actually holds these powers.
                values[reference] = _typed(
                    reference, "address", source_blueprint.ROBINHOOD_GOVERNANCE
                )
            elif key == "contributor-template" or "identity" in key:
                values[reference] = _typed(reference, "address", OWNER)
            elif key == "approved-capability-set":
                values[reference] = _typed(reference, "json", [])
            elif key in {
                "bluechip-morpho-factories",
                "bluechip-euler-factories",
            }:
                values[reference] = _typed(
                    reference, "address-array", [OWNER, OWNER]
                )
            elif key in {
                "bluechip-fluid-resolver",
                "bluechip-compound-configurator",
                "bluechip-moonwell-comptroller",
                "bluechip-aave-provider",
            }:
                values[reference] = _typed(reference, "address", OWNER)
            elif key.startswith("lootbox-"):
                values[reference] = _typed(
                    reference,
                    "uint256",
                    1 if key == "lootbox-min-send-interval" else 0,
                )
            elif key.startswith("deleverage-"):
                values[reference] = _typed(reference, "uint256", 0)
            else:
                values[reference] = _typed(reference, "boolean", True)
        elif namespace == "curve":
            row = curve_rows[key]
            if "address_provider_binding_" in key:
                values[reference] = _typed(reference, "json", list(row.value))
            elif key in {"curve.address_provider", "pool.address", "pool.factory"} or any(
                marker in key
                for marker in (
                    "funding_source", "custodian", "approving_account", "withdrawal_authority"
                )
            ):
                value = row.value if isinstance(row.value, str) else OWNER
                values[reference] = _typed(reference, "address", value)
            elif isinstance(row.value, bool):
                values[reference] = _typed(reference, "boolean", row.value)
            elif isinstance(row.value, int):
                values[reference] = _typed(reference, "uint256", row.value)
            elif isinstance(row.value, str):
                values[reference] = _typed(reference, "string", row.value)
            elif isinstance(row.value, (tuple, list)):
                values[reference] = _typed(reference, "json", list(row.value))
            elif any(
                marker in key
                for marker in (
                    "liquidity_amount", "minimum_minted_lp", "slippage_limit", "minimum_retained_liquidity"
                )
            ):
                values[reference] = _typed(reference, "uint256", 0)
            else:
                values[reference] = _typed(reference, "boolean", True)
        elif namespace == "stock":
            row = stock_rows[key]
            candidate = row.candidate
            if isinstance(candidate, str) and candidate.startswith("0x") and len(candidate) == 42:
                values[reference] = _typed(reference, "address", candidate)
            elif isinstance(candidate, int):
                values[reference] = _typed(reference, "uint256", candidate)
            else:
                values[reference] = _typed(reference, "boolean", True)
        else:
            raise AssertionError(reference)
    return {
        "schema": "ripe.robinhood.execution-envelope.v1",
        "profile_id": profile_id,
        "expected_chain_id": chain_id,
        "source_commit": commit,
        "source_tree": tree,
        "values": values,
        "accepted_blockers": ACCEPTED_RESERVATION_BLOCKERS,
        "authorization": {
            "execution_approved": True,
            "history_approved": True,
        },
    }


def build_bound_plan(
    root: Path,
    profile_id: str = "robinhood-mainnet",
    *,
    overrides: Mapping[str, tuple[str, Any]] | None = None,
) -> Mapping[str, Any]:
    envelope = build_fully_bound_envelope(
        root, profile_id, overrides=overrides
    )
    return build_robinhood_plan(
        profile_id,
        repository_root=root,
        execution_envelope=envelope,
    )


class MigrationHandoff:
    def __init__(self) -> None:
        self.results = {}

    def handoff_manifest_v2_action_result(self, semantic_plan, result):
        validated = validate_execution_handoff(semantic_plan, result)
        if validated["action_id"] in self.results:
            raise AssertionError("duplicate handoff")
        self.results[validated["action_id"]] = validated
        return validated


@pytest.fixture(scope="session")
def committed_execution_root(tmp_path_factory) -> Path:
    from tests.deployment.test_robinhood_migration_source import (
        _clean_committed_fixture,
    )

    return _clean_committed_fixture(
        tmp_path_factory.mktemp("robinhood-execution-source")
    )


@pytest.fixture(scope="session")
def bound_mainnet_plan(committed_execution_root):
    return build_bound_plan(committed_execution_root)
