from __future__ import annotations

import copy
import json
import subprocess
import sys

import pytest

from scripts.utils.deployment_assertions import (
    DeploymentAssertionInputError,
    ObservationMode,
    assert_deployment,
    blueprint_policy,
    ccip_live_assertion_expectations,
    ccip_live_component_expectations,
)


COMPONENT = {
    "component_id": "CM-016",
    "address": "0x0000000000000000000000000000000000000016",
    "proxy_type": "transparent",
    "implementation": "0x0000000000000000000000000000000000001016",
    "runtime_sha256": "11" * 32,
    "constructor_sha256": "22" * 32,
    "artifact_sha256": "33" * 32,
}
CAPABILITY = {
    "component_id": "CM-016",
    "capability": "price_source",
    "enabled": True,
}
CCIP_CAPABILITIES, CCIP_EXTERNAL_FACTS = ccip_live_assertion_expectations()
CCIP_COMPONENTS = ccip_live_component_expectations()


def required_registries():
    policy = blueprint_policy()
    return [
        {
            "domain": domain,
            "registry_id": registry_id,
            "component_id": policy.canonical_registries[(domain, registry_id)],
        }
        for domain, registry_id in sorted(policy.required_registries)
    ]


def expectations():
    return {
        "schema_version": 1,
        "profile_id": "robinhood-mainnet",
        "profile_kind": "profile1",
        "chain_id": 4663,
        "components": [COMPONENT, *copy.deepcopy(CCIP_COMPONENTS)],
        "capabilities": [CAPABILITY, *copy.deepcopy(CCIP_CAPABILITIES)],
        "external_facts": copy.deepcopy(CCIP_EXTERNAL_FACTS),
        "forbidden_edges": [
            {"source": "CM-016", "target": "CM-017", "kind": "pricing"}
        ],
        "profile2_components": ["P2-CURVE"],
        "configuration_sources": {
            "Deleverage.fullPayoffBuffer": "robinhood-mainnet"
        },
    }


def observations(mode="synthetic"):
    return {
        "schema_version": 1,
        "mode": mode,
        "profile_id": "robinhood-mainnet",
        "chain_id": 4663,
        "registries": required_registries(),
        "components": [COMPONENT, *copy.deepcopy(CCIP_COMPONENTS)],
        "capabilities": [CAPABILITY, *copy.deepcopy(CCIP_CAPABILITIES)],
        "external_facts": copy.deepcopy(CCIP_EXTERNAL_FACTS),
        "configuration_sources": {
            "Deleverage.fullPayoffBuffer": "robinhood-mainnet"
        },
    }


def codes(report):
    return {failure.code for failure in report.failures}


@pytest.mark.parametrize("mode", [value.value for value in ObservationMode])
def test_synthetic_local_and_future_deployed_observation_interfaces(mode):
    report = assert_deployment(expectations(), observations(mode))
    assert report.ok
    assert report.mode.value == mode


@pytest.mark.parametrize(
    ("field", "replacement", "code"),
    [
        ("address", "0x0000000000000000000000000000000000009999", "ADDRESS_MISMATCH"),
        ("proxy_type", "beacon", "PROXY_TYPE_MISMATCH"),
        (
            "implementation",
            "0x0000000000000000000000000000000000009999",
            "IMPLEMENTATION_MISMATCH",
        ),
        ("runtime_sha256", "00" * 32, "RUNTIME_SHA256_MISMATCH"),
        ("constructor_sha256", "00" * 32, "CONSTRUCTOR_SHA256_MISMATCH"),
        ("artifact_sha256", "00" * 32, "ARTIFACT_SHA256_MISMATCH"),
    ],
)
def test_wrong_proxy_implementation_runtime_constructor_or_artifact_fails(
    field, replacement, code
):
    value = observations()
    value["components"] = [
        {**COMPONENT, field: replacement},
        *copy.deepcopy(CCIP_COMPONENTS),
    ]
    assert code in codes(assert_deployment(expectations(), value))


def test_role_and_capability_membership_is_exact():
    missing = observations()
    missing["capabilities"] = []
    assert "MISSING_CAPABILITY" in codes(assert_deployment(expectations(), missing))

    wrong = observations()
    wrong["capabilities"] = [{**CAPABILITY, "enabled": False}]
    assert "CAPABILITY_MEMBERSHIP_MISMATCH" in codes(
        assert_deployment(expectations(), wrong)
    )

    extra = observations()
    extra["capabilities"].append(
        {"component_id": "CM-016", "capability": "curve", "enabled": True}
    )
    assert "UNEXPECTED_CAPABILITY" in codes(
        assert_deployment(expectations(), extra)
    )

    invalid = observations()
    invalid["capabilities"] = [{**CAPABILITY, "enabled": 1}]
    with pytest.raises(DeploymentAssertionInputError, match="enabled must be boolean"):
        assert_deployment(expectations(), invalid)


def test_ccip_components_capabilities_and_external_facts_are_observation_bound():
    expected = expectations()
    observed = observations()
    assert assert_deployment(expected, observed).ok

    missing_component = copy.deepcopy(observed)
    missing_component["components"] = [
        row for row in missing_component["components"] if row["component_id"] != "CM-051"
    ]
    assert "MISSING_COMPONENT" in codes(
        assert_deployment(expected, missing_component)
    )

    missing_expected_component = expectations()
    missing_expected_component["components"] = [
        row
        for row in missing_expected_component["components"]
        if row["component_id"] != "CM-052"
    ]
    with pytest.raises(
        DeploymentAssertionInputError,
        match="exact authenticated live CCIP identity",
    ):
        assert_deployment(missing_expected_component, observed)

    missing_capability = copy.deepcopy(observed)
    missing_capability["capabilities"] = [
        row
        for row in missing_capability["capabilities"]
        if not (
            row["component_id"] == "CM-051"
            and row["capability"] == "canMintGreen"
        )
    ]
    assert "MISSING_CAPABILITY" in codes(
        assert_deployment(expected, missing_capability)
    )

    missing_registration = copy.deepcopy(observed)
    missing_registration["external_facts"] = missing_registration[
        "external_facts"
    ][1:]
    assert "MISSING_EXTERNAL_FACT" in codes(
        assert_deployment(expected, missing_registration)
    )

    wrong_toolchain = copy.deepcopy(observed)
    wrong_toolchain["external_facts"][1]["live_creation_identity_status"] = (
        "proven"
    )
    assert "EXTERNAL_FACT_MISMATCH" in codes(
        assert_deployment(expected, wrong_toolchain)
    )

    understated_expectations = expectations()
    understated_expectations["capabilities"] = [CAPABILITY]
    with pytest.raises(
        DeploymentAssertionInputError,
        match="must include exact live CCIP membership",
    ):
        assert_deployment(understated_expectations, observations())

    missing_fact_expectations = expectations()
    missing_fact_expectations["external_facts"] = missing_fact_expectations[
        "external_facts"
    ][1:]
    with pytest.raises(
        DeploymentAssertionInputError,
        match="must include exact live CCIP fact",
    ):
        assert_deployment(missing_fact_expectations, observations())


@pytest.mark.parametrize(
    ("component_id", "code"),
    [
        ("CM-005", "OMITTED_COMPONENT_PRESENT"),
        ("CM-008", "BLOCKED_COMPONENT_PRESENT"),
    ],
)
def test_unavailable_component_presence_fails_closed(component_id, code):
    value = observations()
    value["components"].append(
        {
            "component_id": component_id,
            "address": "0x0000000000000000000000000000000000000005",
        }
    )
    assert code in codes(assert_deployment(expectations(), value))


def test_disabled_and_profile2_reachability_fail_closed():
    disabled = observations()
    disabled["edges"] = [
        {"source": "CM-016", "target": "CM-017", "kind": "pricing"}
    ]
    disabled_codes = codes(assert_deployment(expectations(), disabled))
    assert "DISABLED_FUNCTIONALITY_REACHABLE" in disabled_codes
    assert "OMITTED_COMPONENT_REACHABLE" not in disabled_codes

    omitted = observations()
    omitted["edges"] = [
        {"source": "CM-016", "target": "CM-019", "kind": "pricing"}
    ]
    assert "OMITTED_COMPONENT_REACHABLE" in codes(
        assert_deployment(expectations(), omitted)
    )

    profile2 = observations()
    profile2["edges"] = [
        {"source": "CM-016", "target": "P2-CURVE", "kind": "pricing"}
    ]
    assert "PROFILE2_REACHABLE_FROM_PROFILE1" in codes(
        assert_deployment(expectations(), profile2)
    )


@pytest.mark.parametrize(
    ("component_id", "code"),
    [
        ("CM-008", "BLOCKED_COMPONENT_REACHABLE"),
    ],
)
def test_blocked_and_deferred_edges_fail_closed(component_id, code):
    value = observations()
    value["edges"] = [
        {"source": "CM-016", "target": component_id, "kind": "dependency"}
    ]
    assert code in codes(assert_deployment(expectations(), value))


def test_base_deleverage_configuration_provenance_cannot_be_reused():
    value = observations()
    value["configuration_sources"] = {
        "Deleverage.fullPayoffBuffer": "base-mainnet"
    }
    result_codes = codes(assert_deployment(expectations(), value))
    assert "CONFIGURATION_SOURCE_MISMATCH" in result_codes
    assert "DELEVERAGE_BASE_CONFIG_REUSE" in result_codes

    injected = observations()
    injected["configuration_sources"]["Deleverage.injected"] = "base-mainnet"
    injected_codes = codes(assert_deployment(expectations(), injected))
    assert "UNEXPECTED_CONFIGURATION_SOURCE" in injected_codes
    assert "DELEVERAGE_BASE_CONFIG_REUSE" in injected_codes


@pytest.mark.parametrize("envelope", ["expectations", "observations"])
def test_required_chain_identity_and_mandatory_blueprint_enforcement(envelope):
    expected = expectations()
    observed = observations()
    (expected if envelope == "expectations" else observed).pop("chain_id")
    with pytest.raises(DeploymentAssertionInputError, match="chain_id"):
        assert_deployment(expected, observed)

    disabled_policy = expectations()
    disabled_policy["enforce_blueprint_registry"] = False
    with pytest.raises(
        DeploymentAssertionInputError,
        match="registry enforcement is mandatory",
    ):
        assert_deployment(disabled_policy, observations())


def test_deployed_modes_require_complete_component_identity():
    value = observations("deployed_observation")
    value["components"] = [
        {key: item for key, item in COMPONENT.items() if key != "runtime_sha256"},
        *copy.deepcopy(CCIP_COMPONENTS),
    ]
    with pytest.raises(
        DeploymentAssertionInputError,
        match="missing deployed identity field",
    ):
        assert_deployment(expectations(), value)


@pytest.mark.parametrize("envelope", ["expectations", "observations"])
def test_topology_edges_require_nonempty_source_target_and_kind(envelope):
    expected = expectations()
    observed = observations()
    if envelope == "expectations":
        expected["forbidden_edges"] = [{"source": "CM-016", "target": "CM-017"}]
    else:
        observed["edges"] = [{"source": "CM-016", "target": "CM-017"}]
    with pytest.raises(DeploymentAssertionInputError, match="kind"):
        assert_deployment(expected, observed)


def test_cli_consumes_precollected_observations_without_deployed_claim(
    tmp_path,
):
    expected_path = tmp_path / "expected.json"
    observed_path = tmp_path / "observed.json"
    expected_path.write_text(json.dumps(expectations()))
    observed_path.write_text(json.dumps(observations("deployed_observation")))

    result = subprocess.run(
        [
            sys.executable,
            "scripts/check_deployment.py",
            "--expectations",
            str(expected_path),
            "--observations",
            str(observed_path),
        ],
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    report = json.loads(lines[0])
    assert report["mode"] == "deployed_observation"
    assert report["ok"] is True
    assert lines[-1] == (
        "DEPLOYMENT_ASSERTIONS_OK "
        "mode=deployed_observation source=precollected-observations"
    )


def test_cli_exposes_versioned_envelope_templates():
    for template in ("expectations", "synthetic", "deployed_observation"):
        result = subprocess.run(
            [
                sys.executable,
                "scripts/check_deployment.py",
                "--print-template",
                template,
            ],
            check=False,
            text=True,
            capture_output=True,
        )
        assert result.returncode == 0, result.stderr
        value = json.loads(result.stdout)
        assert value["schema_version"] == 1
        assert "chain_id" in value
        if template == "expectations":
            assert value["profile_kind"] == "profile1"
        else:
            assert value["mode"] == template
