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
def __init__(_ripeHq: address):
    addys.__init__(_ripeHq)
    deptBasics.__init__(False, False, False) # no minting

    # NOTE: This is a temporary BondRoom contract. Real one coming soon.
