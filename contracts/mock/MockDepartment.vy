# @version 0.4.1

implements: Department

exports: addys.__interface__
exports: deptBasics.__interface__

initializes: addys
initializes: deptBasics[addys := addys]

import contracts.modules.Addys as addys
import contracts.modules.DeptBasics as deptBasics
from interfaces import Department


@deploy
def __init__(_ripeHq: address, _canMintGreen: bool, _canMintRipe: bool):
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, _canMintGreen, _canMintRipe)

    # NOTE: Mock department contract
