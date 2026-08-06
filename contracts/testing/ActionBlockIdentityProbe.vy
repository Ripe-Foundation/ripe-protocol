# Ripe Protocol License: https://github.com/ripe-foundation/ripe-protocol/blob/master/LICENSE.md
# Ripe Foundation (C) 2026

# @version 0.4.3


interface ArbSys:
    def arbBlockNumber() -> uint256: view


event ActionBlockObserved:
    observationId: uint256
    caller: address
    nativeBlockNumber: uint256
    arbBlockNumber: uint256
    observedAt: uint256


ARB_SYS: constant(address) = 0x0000000000000000000000000000000000000064


@deploy
def __init__():
    # Deployment must fail if the expected precompile call or uint256 ABI decode fails.
    _: uint256 = staticcall ArbSys(ARB_SYS).arbBlockNumber()


@view
@external
def readActionBlocks() -> (uint256, uint256):
    return block.number, staticcall ArbSys(ARB_SYS).arbBlockNumber()


@external
def observe(_observationId: uint256) -> (uint256, uint256):
    nativeBlockNumber: uint256 = block.number
    arbBlockNumber: uint256 = staticcall ArbSys(ARB_SYS).arbBlockNumber()

    log ActionBlockObserved(
        observationId=_observationId,
        caller=msg.sender,
        nativeBlockNumber=nativeBlockNumber,
        arbBlockNumber=arbBlockNumber,
        observedAt=block.timestamp,
    )
    return nativeBlockNumber, arbBlockNumber
