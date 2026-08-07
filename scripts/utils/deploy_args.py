from config.BluePrint import (
    ADDYS,
    CORE_TOKENS,
    CURVE_PARAMS,
    PARAMS,
    ROBINHOOD_ADDRESS_STATUS,
    ROBINHOOD_DEFAULTS_CONSTRUCTOR,
    SymbolicBinding,
    YIELD_TOKENS,
)


class BluePrint:
    def __init__(self, blueprint):
        self.blueprint = blueprint
        self.PARAMS = PARAMS[blueprint]
        self.ADDYS = ADDYS[blueprint]
        self.CURVE_PARAMS = CURVE_PARAMS[blueprint]
        self.CORE_TOKENS = CORE_TOKENS[blueprint]
        self.YIELD_TOKENS = YIELD_TOKENS[blueprint]

    def defaults_robinhood_constructor_args(self):
        """Return the seven ordered inputs, failing on unresolved identities."""
        if self.blueprint != "robinhood":
            raise ValueError("DefaultsRobinhood constructor is Robinhood-only")
        values = []
        for semantic_name, key in ROBINHOOD_DEFAULTS_CONSTRUCTOR:
            value = self.ADDYS[key]
            status = ROBINHOOD_ADDRESS_STATUS[key]
            if isinstance(value, SymbolicBinding):
                raise ValueError(
                    f"RH_DEPLOYMENT_BINDING_UNRESOLVED:{semantic_name}:{key}"
                )
            if status.endswith("unverified"):
                raise ValueError(
                    f"RH_EXTERNAL_FACT_UNVERIFIED:{semantic_name}:{key}"
                )
            values.append(value)
        return tuple(values)


class DeployArgs:
    def __init__(self, sender, chain, ignore_logs, blueprint, rpc):
        self.sender = sender
        self.chain = chain
        self.ignore_logs = ignore_logs
        self.blueprint = BluePrint(blueprint)
        self.rpc = rpc
        # Installed only by the post-gate Robinhood execution branch.
        self.robinhood_execution_plan = None
        self.robinhood_repository_root = None
        self.robinhood_stage_executor = None


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
