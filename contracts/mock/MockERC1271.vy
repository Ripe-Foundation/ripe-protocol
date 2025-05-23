# @version 0.4.1

"""
@title Mock ERC1271 Contract
@notice A mock contract implementing ERC1271 for testing signature validation
@dev This contract will always return a valid signature for testing purposes
"""

# Magic value that indicates a valid signature
MAGIC_VALUE: constant(bytes32) = 0x1626ba7e00000000000000000000000000000000000000000000000000000000

@external
def isValidSignature(_hash: bytes32, _signature: Bytes[65]) -> bytes32:
    """
    @notice Always returns the magic value to indicate a valid signature
    @param _hash The hash of the data to be signed
    @param _signature The signature to be validated
    @return The magic value indicating a valid signature
    """
    return MAGIC_VALUE 