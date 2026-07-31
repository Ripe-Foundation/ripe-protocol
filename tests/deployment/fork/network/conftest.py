from __future__ import annotations

import pytest


@pytest.fixture
def observed_facts(fork_framework, parse_envelope):
    owner = parse_envelope().owner
    return fork_framework.ObservedForkFacts(
        chain_id=owner.expected_chain_id,
        block_number=owner.pin.number,
        block_hash=owner.pin.block_hash,
        parent_hash=owner.pin.parent_hash,
        state_root=owner.pin.state_root,
        timestamp=owner.pin.timestamp,
        endpoint_fingerprint_sha256=owner.endpoint.fingerprint_sha256,
    )


@pytest.fixture
def mutate_observation(observed_facts):
    def mutate(**overrides):
        values = {
            name: getattr(observed_facts, name)
            for name in observed_facts.__dataclass_fields__
        }
        values.update(overrides)
        return observed_facts.__class__(**values)

    return mutate
