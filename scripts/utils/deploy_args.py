from config.BluePrint import PARAMS, ADDYS


class BluePrint:
    def __init__(self, blueprint):
        self.blueprint = blueprint
        self.PARAMS = PARAMS[blueprint]
        self.ADDYS = ADDYS[blueprint]


class DeployArgs:
    def __init__(self, sender, chain, ignore_logs, blueprint):
        self.sender = sender
        self.chain = chain
        self.ignore_logs = ignore_logs
        self.blueprint = BluePrint(blueprint)


class LegoType:
    YIELD_OPP = 2**0  # 2 ** 0 = 1
    DEX = 2**1  # 2 ** 1 = 2
