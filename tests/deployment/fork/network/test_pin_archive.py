from __future__ import annotations

import copy

import pytest


@pytest.mark.parametrize(
    ("profile", "chain_id"),
    (
        ("robinhood-mainnet", 4663),
        ("robinhood-testnet", 46630),
    ),
)
def test_robinhood_profile_chain_binding(
    fork_framework, envelope_value, profile, chain_id
):
    candidate = copy.deepcopy(envelope_value)
    candidate["owner_inputs"]["profile"] = profile
    candidate["owner_inputs"]["expected_chain_id"] = chain_id
    data = fork_framework.canonical_json_bytes(candidate)
    parsed = fork_framework.parse_input_envelope(
        data,
        now=__import__("datetime").datetime(
            2029, 1, 1, tzinfo=__import__("datetime").timezone.utc
        ),
    )
    assert parsed.owner.profile == profile
    assert parsed.owner.expected_chain_id == chain_id


def test_base_profile_is_rejected(
    fork_framework, envelope_value, parse_envelope
):
    candidate = copy.deepcopy(envelope_value)
    candidate["owner_inputs"]["profile"] = "base-mainnet"
    candidate["owner_inputs"]["expected_chain_id"] = 8453
    with pytest.raises(
        fork_framework.ForkFrameworkError, match="H09_PROFILE"
    ):
        parse_envelope(candidate)


def test_exact_pin_and_endpoint_observation_bind(
    fork_framework, parse_envelope, observed_facts
):
    bound = fork_framework.bind_observed_facts(
        parse_envelope(), observed_facts
    )
    assert bound.owner.pin.number == observed_facts.block_number
    assert bound.owner.pin.block_hash == observed_facts.block_hash


@pytest.mark.parametrize(
    ("field", "value", "code"),
    (
        ("chain_id", 1, "H09_CHAIN_ID_MISMATCH"),
        ("block_number", 124, "H09_BLOCK_NUMBER_MISMATCH"),
        ("block_hash", "0x" + "91" * 32, "H09_BLOCK_HASH_MISMATCH"),
        ("parent_hash", "0x" + "92" * 32, "H09_PARENT_HASH_MISMATCH"),
        ("state_root", "0x" + "93" * 32, "H09_STATE_ROOT_MISMATCH"),
        ("timestamp", 1_800_000_001, "H09_TIMESTAMP_MISMATCH"),
        (
            "endpoint_fingerprint_sha256",
            "94" * 32,
            "H09_ENDPOINT_FINGERPRINT_MISMATCH",
        ),
    ),
)
def test_every_observed_pin_mismatch_fails_closed(
    fork_framework,
    parse_envelope,
    mutate_observation,
    field,
    value,
    code,
):
    with pytest.raises(fork_framework.ForkFrameworkError, match=code):
        fork_framework.bind_observed_facts(
            parse_envelope(), mutate_observation(**{field: value})
        )


def test_partial_pin_is_rejected(
    fork_framework, envelope_value, parse_envelope
):
    candidate = copy.deepcopy(envelope_value)
    del candidate["owner_inputs"]["pin"]["state_root"]
    with pytest.raises(
        fork_framework.ForkFrameworkError, match="H09_PIN_KEYS"
    ):
        parse_envelope(candidate)


def test_contradictory_parent_and_block_hash_are_rejected(
    fork_framework, envelope_value, parse_envelope
):
    candidate = copy.deepcopy(envelope_value)
    candidate["owner_inputs"]["pin"]["parent_hash"] = candidate[
        "owner_inputs"
    ]["pin"]["block_hash"]
    with pytest.raises(
        fork_framework.ForkFrameworkError, match="H09_PIN_CONTRADICTION"
    ):
        parse_envelope(candidate)
