from __future__ import annotations

from config.robinhood_blueprint import Disposition, get_component
from utils.blueprint_policy import blueprint_policy


def test_vault_book_ids_and_reserved_four_are_exact():
    """VaultBook's registry slots are exact and hard-coded, not derived.

    Migrations and address lookups rely on these IDs matching these
    components; a shift here would misroute a deposit/withdraw call to the
    wrong vault. ID 4 is reserved (not yet assigned a required component).
    """
    policy = blueprint_policy()
    assert {
        key: policy.canonical_registries[key]
        for key in policy.canonical_registries
        if key[0] == "vault_book"
    } == {
        ("vault_book", 1): "CM-022",
        ("vault_book", 2): "CM-023",
        ("vault_book", 3): "CM-024",
        ("vault_book", 4): "CM-025",
    }
    assert ("vault_book", 4) in policy.reserved_registries


def test_ripe_hq_id_four_is_reserved():
    """RipeHq registry ID 4 is bound to CM-008 but not yet required.

    A component landing on ID 4 without going through this reservation would
    be a silent registry-slot reuse.
    """
    policy = blueprint_policy()
    assert policy.canonical_registries[("ripe_hq", 4)] == "CM-008"
    assert ("ripe_hq", 4) in policy.reserved_registries


def test_profile1_bluechip_topology_is_selected_in_slot_three():
    """BlueChipYieldPrices is required at PriceDesk slot 3.

    Preserved from `tests/inventory/test_bluechip_yield_prices_artifacts.py`,
    which was deleted with the artifact-expectations pipeline. Every other test
    in that module compared compiler output against frozen hashes; this one
    asserts deployment policy, which no other test covers, so it moves here
    rather than dying with the artifact bindings.
    """
    component = get_component("CM-018")
    policy = blueprint_policy()

    assert component.name == "BlueChipYieldPrices"
    assert component.deployment is Disposition.REQUIRED
    assert len(component.registry_expectations) == 1
    row = component.registry_expectations[0]
    assert (row.domain.value, row.registry_id, row.semantic_name) == (
        "price_desk",
        3,
        "BlueChipYield",
    )
    assert row.disposition is Disposition.REQUIRED
    assert policy.canonical_registries[("price_desk", 3)] == "CM-018"
    assert ("price_desk", 3) not in policy.reserved_registries
    assert ("price_desk", 3) in policy.required_registries
