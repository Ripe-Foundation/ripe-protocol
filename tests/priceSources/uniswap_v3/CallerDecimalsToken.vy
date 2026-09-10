# @version 0.4.3
# Test-only caller-dependent metadata; never a production token assumption.
DESK: immutable(address)
spoofDesk: bool
@deploy
def __init__(_desk: address):
    DESK = _desk
@external
def setDeskSpoof(_spoof: bool):
    self.spoofDesk = _spoof
@external
@view
def decimals() -> uint256:
    return 6 if self.spoofDesk and msg.sender == DESK else 18
