# @version 0.4.3

ripeAvailForRewards: public(uint256)
numCalls: public(uint256)
lastAmount: public(uint256)


@deploy
def __init__(_ripeAvailForRewards: uint256):
    self.ripeAvailForRewards = _ripeAvailForRewards


@external
def didGetRewardsFromStabClaims(_amount: uint256):
    self.numCalls += 1
    self.lastAmount = _amount
    self.ripeAvailForRewards -= _amount
