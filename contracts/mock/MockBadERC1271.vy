# @version 0.4.3

"""
@title Mock Bad ERC1271 Contract
@notice A mock contract implementing ERC1271 for testing invalid signature validation
@dev This contract always returns an invalid magic value for isValidSignature
"""

@external
def isValidSignature(_hash: bytes32, _signature: Bytes[65]) -> bytes32:
    # Return an invalid value (not 0x1626ba7e...)
    return 0xdeadbeef00000000000000000000000000000000000000000000000000000000 