# @version 0.4.1

initializes: addys
exports: addys.__interface__
import contracts.modules.Addys as addys


@deploy
def __init__(_ripeHq: address):
    addys.__init__(_ripeHq)

    # Just filling up a spot in Ripe HQ for now.
    # Nothing here. Coming soon.
