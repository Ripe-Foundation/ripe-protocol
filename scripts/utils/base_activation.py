"""Shared dependency validation for current-source Base replacements."""


def department_confirmation_order(replacements):
    """Validate dependencies before proposing any department changes."""
    if len(replacements) != len(set(replacements)):
        raise RuntimeError("BASE_ACTIVATION_DUPLICATE_SLOT")
    required = (6, 8, 5, 7, 17)
    for slot in required:
        if slot not in replacements:
            raise RuntimeError(f"BASE_ACTIVATION_REQUIRED_SLOT_MISSING:{slot}")
    # The relay Teller needs the compatible PriceDesk already active.
    return [6, 8, 5, 7] + [slot for slot in replacements if slot not in (6, 8, 5, 7)]
