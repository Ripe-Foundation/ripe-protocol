# @version 0.4.3
# Canonical-binding fault fixture. Authentic gas tests use compiled V3Factory.
pools: HashMap[address, HashMap[address, HashMap[uint24, address]]]
@external
def setPool(asset: address, weth: address, fee: uint24, pool: address):
    self.pools[asset][weth][fee] = pool
    self.pools[weth][asset][fee] = pool
@view
@external
def getPool(asset: address, weth: address, fee: uint24) -> address:
    return self.pools[asset][weth][fee]
