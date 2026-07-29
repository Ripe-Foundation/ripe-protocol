# Chainlink CCIP infrastructure, per chain.
#
# Every value below was read straight off the chain it belongs to (router / rmn proxy
# from the `BurnMintTokenPool 1.5.1` pools deployed via the CCIP token manager UI, token
# admin registry from the OnRamp static config, registry module from the
# `RegistryModuleAdded` event on the token admin registry).

CCIP = {
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
