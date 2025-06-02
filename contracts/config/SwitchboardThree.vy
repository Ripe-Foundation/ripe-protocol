# @version 0.4.1


exports: addys.__interface__

initializes: addys

import contracts.modules.Addys as addys


@deploy
def __init__(_ripeHq: address):
    addys.__init__(_ripeHq)

    # NOTE: This is a temporary Switchboard contract.
