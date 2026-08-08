# Chainlink CCIP infrastructure, per chain.
#
# The mainnet entries were derived on chain, not from a directory: the router
# and RMN proxy were read off the BurnMintTokenPools already deployed on each
# chain (13 of 15 agree on Base, 7 of 8 on Robinhood -- the outliers are pools
# still pointing at a superseded router), the chain selector off an OffRamp's
# static config, and every address was then confirmed by its typeAndVersion().
# LINK is omitted rather than guessed: nothing in these migrations reads it,
# and both explorers list several name-squatting "ChainLink Token" entries.
#
# Every value below was read straight off the chain it belongs to (router / rmn proxy
# from the `BurnMintTokenPool 1.5.1` pools deployed via the CCIP token manager UI, token
# admin registry from the OnRamp static config, registry module from the
# `RegistryModuleAdded` event on the token admin registry).

CCIP = {
    "base-mainnet": {
        "CHAIN_SELECTOR": 15971525489660198786,
        "ROUTER": "0x881e3A65B4d4a04dD529061dd0071cf975F58bCD",
        "RMN_PROXY": "0xC842c69d54F83170C42C4d556B4F6B2ca53Dd3E8",
        "TOKEN_ADMIN_REGISTRY": "0x6f6C373d09C07425BaAE72317863d7F6bb731e37",
        "REGISTRY_MODULE_OWNER_CUSTOM": "0x1A5f2d0c090dDB7ee437051DA5e6f03b6bAE1A77",
        # No pool to retire: nothing CCIP-shaped is registered in RipeHq here.
        "PREVIOUS_RIPE_POOL": None,
        "REMOTE_CHAINS": ["robinhood-mainnet"],
    },
    "robinhood-mainnet": {
        "CHAIN_SELECTOR": 6180753054346818345,
        "ROUTER": "0x06fC836cf9839B1cd891C440A0a45242DA6Ae1c9",
        "RMN_PROXY": "0xe8464c353210Cc398A45dB2454FBc5BCd25fFf20",
        "TOKEN_ADMIN_REGISTRY": "0x1912C3cFafE8A76A32a92861d815aC2837F237Ca",
        "REGISTRY_MODULE_OWNER_CUSTOM": "0x3237c0D7B58BEc8Dc17F00103B784Bd6678f789E",
        "PREVIOUS_RIPE_POOL": None,
        "REMOTE_CHAINS": ["base-mainnet"],
    },
    "base-sepolia": {
        "CHAIN_SELECTOR": 10344971235874465080,
        "ROUTER": "0xD3b06cEbF099CE7DA4AcCf578aaebFDBd6e88a93",
        "RMN_PROXY": "0x99360767a4705f68CcCb9533195B761648d6d807",
        "TOKEN_ADMIN_REGISTRY": "0x736D0bBb318c1B27Ff686cd19804094E66250e17",
        "REGISTRY_MODULE_OWNER_CUSTOM": "0x176ae8C6C11DD2c031B924CE1A0A43188035f3f6",
        # fee tokens the FeeQuoter accepts, besides the native coin
        "LINK": "0xE4aB69C077896252FAFBD49EFD26B5D171A32410",
        # the stock chainlink pool the ripe pool replaces (no `canMintRipe()`)
        "PREVIOUS_RIPE_POOL": "0x4DFd9eBB670F22b0cf53A53088E38636855CC600",
        "REMOTE_CHAINS": ["robinhood-testnet"],
    },
    "robinhood-testnet": {
        "CHAIN_SELECTOR": 2032988798112970440,
        "ROUTER": "0x30D197C6F5bE050D5525dD94d01760FaCdB67e7C",
        "RMN_PROXY": "0x934c1B8f6913070528CC24081E0b78d57D3A97A3",
        "TOKEN_ADMIN_REGISTRY": "0xad4c7a1430D140Fc5121C0697B2f7Efc655c0070",
        "REGISTRY_MODULE_OWNER_CUSTOM": "0x00094197A82faDE614C214CFE27719dEDa898686",
        "LINK": "0xD610B8f58689de7755947C05342A2DFaC30ebD57",
        "PREVIOUS_RIPE_POOL": "0x8BcA5FC8933e19aa99cf95E0BaDE1aAB5309Be3d",
        "REMOTE_CHAINS": ["base-sepolia"],
    },
}


# rate limits, `RateLimiter.Config(isEnabled, capacity, rate)` - disabled, which is what
# the pools deployed by the CCIP token manager UI use today
NO_RATE_LIMIT = (False, 0, 0)
