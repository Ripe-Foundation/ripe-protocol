# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2026

# @version 0.4.3


interface Registry:
    def getAddr(_regId: uint256) -> address: view


@view
@external
def assertConfirmed(_registry: address, _regId: uint256, _expected: address):
    """Revert unless a preceding registry confirmation installed _expected."""
    assert _registry.is_contract # dev: invalid registry
    assert staticcall Registry(_registry).getAddr(_regId) == _expected # dev: registry update failed
