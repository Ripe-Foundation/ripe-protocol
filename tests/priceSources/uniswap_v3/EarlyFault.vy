# @version 0.4.3
# Fault injection only; preserves PriceDesk's upstream MC read to reach source.
DESK: immutable(address)
MC: immutable(address)

@deploy
def __init__(desk: address, mc: address):
    DESK=desk
    MC=mc

@pure
@internal
def _burn() -> uint256:
    value: uint256=0
    for i: uint256 in range(100000):
        value=unsafe_add(value,i)
    return value

@view
@external
def getAddr(regId: uint256) -> address:
    if regId==5:
        return MC
    return convert(self._burn(),address)

@view
@external
def getPriceStaleTime() -> uint256:
    if msg.sender==DESK:
        return 0
    return self._burn()

struct PriceConfig:
    staleTime: uint256
    priorityPriceSourceIds: DynArray[uint256, 20]

@view
@external
def getPriceConfig() -> PriceConfig:
    return PriceConfig(staleTime=0,priorityPriceSourceIds=[])
