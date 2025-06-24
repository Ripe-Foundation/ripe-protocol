# @version 0.4.3

allowed: public(HashMap[address, HashMap[address, bool]]) # user -> asset -> allowed


@deploy
def __init__():
    pass


@external
def setAllowed(_user: address, _asset: address, _allowed: bool):
    self.allowed[_user][_asset] = _allowed


@view
@external
def isUserAllowed(_user: address, _asset: address) -> bool:
    return self.allowed[_user][_asset]