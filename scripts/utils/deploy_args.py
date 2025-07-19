from config.BluePrint import PARAMS, ADDYS, CURVE_PARAMS, CORE_TOKENS, YIELD_TOKENS


class BluePrint:
    def __init__(self, blueprint):
        self.blueprint = blueprint
        self.PARAMS = PARAMS[blueprint]
        self.ADDYS = ADDYS[blueprint]
        self.CURVE_PARAMS = CURVE_PARAMS[blueprint]
        self.CORE_TOKENS = CORE_TOKENS[blueprint]
        self.YIELD_TOKENS = YIELD_TOKENS[blueprint]


class DeployArgs:
    def __init__(self, sender, chain, ignore_logs, blueprint, rpc):
        self.sender = sender
        self.chain = chain
        self.ignore_logs = ignore_logs
        self.blueprint = BluePrint(blueprint)
        self.rpc = rpc


class LegoType:
    YIELD_OPP = 2**0  # 2 ** 0 = 1
    DEX = 2**1  # 2 ** 1 = 2


DEFAULT_AUCTION_PARAMS = (
    False,
    0,
    0,
    0,
    0,
)
