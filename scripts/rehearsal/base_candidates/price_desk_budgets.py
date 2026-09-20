"""Shared readbacks for provisional PriceDesk rehearsal candidates."""


BUDGET_GETTERS = (
    "PRICE_SOURCE_PRICE_GAS", "PRICE_SOURCE_SNAPSHOT_GAS", "PRICE_SOURCE_HAS_FEED_GAS",
    "MAX_SOURCE_GAS",
)
BUDGET_KEYS = (
    "PRICE_DESK_PRICE_SOURCE_GAS", "PRICE_DESK_SNAPSHOT_SOURCE_GAS",
    "PRICE_DESK_HAS_FEED_SOURCE_GAS", "PRICE_DESK_MAX_SOURCE_GAS",
)


def verify_price_desk_defaults(desk, params):
    values = tuple(int(getattr(desk, getter)()) for getter in BUDGET_GETTERS)
    expected = tuple(params[key] for key in BUDGET_KEYS)
    if values != expected:
        raise RuntimeError("PRICEDESK_CONSTRUCTOR_BUDGET_MISMATCH")
    return values


def apply_source_gas_budgets(migration, desk, sources):
    """Apply every profile entry to the exact registered address, then read back.

    Sources maps semantic names to (registry ID, address). Journalled execution
    makes replay safe even after local governance has been relinquished; the
    readbacks still run and reject altered settings or address bindings.
    """
    blueprint = migration.blueprint()
    defaults = verify_price_desk_defaults(desk, blueprint.PARAMS)
    overrides = blueprint.PRICE_DESK_SOURCE_GAS_OVERRIDES
    if not overrides or set(sources) != set(overrides):
        raise RuntimeError("PRICEDESK_OVERRIDE_SOURCE_SET_MISMATCH")
    entries = []
    for name, raw in overrides.items():
        slot, address = sources[name]
        if (int(desk.getRegId(address)) != slot
                or str(desk.getAddr(slot)).lower() != str(address).lower()):
            raise RuntimeError(f"PRICEDESK_OVERRIDE_SOURCE_MISMATCH:{name}")
        if len(raw) != 3 or any(type(value) is not int or value < 0 for value in raw):
            raise RuntimeError(f"PRICEDESK_OVERRIDE_INVALID:{name}")
        effective = tuple(value or floor for value, floor in zip(raw, defaults[:3]))
        if any(value < floor or value > defaults[3]
               for value, floor in zip(effective, defaults[:3])):
            raise RuntimeError(f"PRICEDESK_OVERRIDE_BOUNDS:{name}")
        entries.append((name, address, raw, effective))
    for name, address, raw, effective in entries:
        migration.execute(desk.setSourceGasBudgets, address, *raw)
        if tuple(desk.getSourceGasBudgets(address)) != effective:
            raise RuntimeError(f"PRICEDESK_OVERRIDE_READBACK_MISMATCH:{name}")
