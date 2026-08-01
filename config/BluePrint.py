ADDYS = {
    "base": {
        "RIPE_WETH_POOL": "0x765824aD2eD0ECB70ECc25B0Cf285832b335d6A9",
        "RIPE_TOKEN": "0x2A0a59d6B975828e781EcaC125dBA40d7ee5dDC0",
        # underscore
        "UNDERSCORE_REGISTRY": "0x44Cf3c4f000DFD76a35d03298049D37bE688D6F9",
        # curve
        "CURVE_ADDRESS_PROVIDER": "0x5ffe7FB82894076ECB99A30D6A32e969e6e35E98",
        "CURVE_STABLE_FACTORY": "0xd2002373543Ce3527023C75e7518C274A51ce712",
        "CURVE_CRYPTO_FACTORY": "0xc9Fe0C63Af9A39402e8a5514f9c43Af0322b665F",
        # default chainlink feeds
        "CHAINLINK_ETH_USD": "0x71041dddad3595F9CEd3DcCFBe3D1F4b0a16Bb70",
        "CHAINLINK_BTC_USD": "0x64c911996D3c6aC71f9b455B1E8E7266BcbD848F",
        "CHAINLINK_USDC_USD": "0x7e860098F58bBFC8648a4311b374B1D669a2bc6B",
        "CHAINLINK_CBBTC_USD": "0x07DA0E54543a844a80ABE69c8A12F22B3aA59f9D",
        "CHAINLINK_DOGE_USD": "0x8422f3d3CAFf15Ca682939310d6A5e619AE08e57",
        "CHAINLINK_SOL_USD": "0x975043adBb80fc32276CbF9Bbcfd4A601a12462D",

        # important tokens / representations
        "WETH": "0x4200000000000000000000000000000000000006",
        "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        "BTC": "0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB",
        # morpho
        "MORPHO_FACTORY": "0xFf62A7c278C62eD665133147129245053Bbf5918",
        "MORPHO_FACTORY_LEGACY": "0xA9c3D3a366466Fa809d1Ae982Fb2c46E5fC41101",
        # euler
        "EULER_EVAULT_FACTORY": "0x7F321498A801A191a93C840750ed637149dDf8D0",
        "EULER_EARN_FACTORY": "0x72bbDB652F2AEC9056115644EfCcDd1986F51f15",
        # fluid
        "FLUID_RESOLVER": "0x3aF6FBEc4a2FE517F56E402C65e3f4c3e18C1D86",
        # compound v3
        "COMPOUND_V3_CONFIGURATOR": "0x45939657d1CA34A8FA39A924B71D28Fe8431e581",
        # moonwell
        "MOONWELL_COMPTROLLER": "0xfBb21d0380beE3312B33c4353c8936a0F13EF26C",
        # aave v3
        "AAVE_V3_ADDRESS_PROVIDER": "0xe20fCBdBfFC4Dd138cE8b2E6FBb6CB49777ad64D",
        # oracles
        "PYTH_NETWORK": "0x8250f4aF4B972684F7b336503E2D6dFeDeB1487a",
        "STORK_NETWORK": "0x647DFd812BC1e116c6992CB2bC353b2112176fD6",
        # governance
        "GOVERNANCE": "0xe488a42D33b3Af5d3E5Cd5680938d8369716D1bf",
    },
    "local": {
        # important tokens / representations
        "WETH": "0x4200000000000000000000000000000000000006",
        "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        "BTC": "0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB",
    },
}


PARAMS = {
    "base": {
        # ripe hq - gov changes (blocks)
        "RIPE_HQ_MIN_GOV_TIMELOCK": 43_200,  # 1 day on Base
        "RIPE_HQ_MAX_GOV_TIMELOCK": 302_400,  # 7 days on Base
        # ripe hq - registry changes (blocks)
        "RIPE_HQ_MIN_REG_TIMELOCK": 21_600,  # 12 hours on Base
        "RIPE_HQ_MAX_REG_TIMELOCK": 302_400,  # 7 days on Base
        # tokens (green / ripe)
        "MIN_HQ_CHANGE_TIMELOCK": 43_200,  # 1 day on Base
        "MAX_HQ_CHANGE_TIMELOCK": 302_400,  # 7 days on Base
        # switchboard (green / ripe)
        "MIN_SWITCHBOARD_CHANGE_TIMELOCK": 3_600,  # 2 hours on Base
        "MAX_SWITCHBOARD_CHANGE_TIMELOCK": 302_400,  # 7 days on Base
        # price desk (timestamps, not blocks!)
        "PRICE_DESK_MIN_STALE_TIME": 60 * 5,  # 5 mins
        "PRICE_DESK_MAX_STALE_TIME": 60 * 60 * 24 * 7,  # 7 days
        # price desk (blocks)
        "PRICE_DESK_MIN_REG_TIMELOCK": 3_600,  # 2 hours on Base
        "PRICE_DESK_MAX_REG_TIMELOCK": 302_400,  # 7 days on Base
        # vault book (blocks)
        "VAULT_BOOK_MIN_REG_TIMELOCK": 3_600,  # 12 hours on Base
        "VAULT_BOOK_MAX_REG_TIMELOCK": 302_400,  # 7 days on Base
    },
    "local": {
        # ripe hq - gov changes (blocks)
        "RIPE_HQ_MIN_GOV_TIMELOCK": 43_200,
        "RIPE_HQ_MAX_GOV_TIMELOCK": 302_400,
        # ripe hq - registry changes (blocks)
        "RIPE_HQ_MIN_REG_TIMELOCK": 21_600,
        "RIPE_HQ_MAX_REG_TIMELOCK": 302_400,
        # tokens (green / ripe)
        "MIN_HQ_CHANGE_TIMELOCK": 43_200,
        "MAX_HQ_CHANGE_TIMELOCK": 302_400,
        # price desk (timestamps, not blocks!)
        "PRICE_DESK_MIN_STALE_TIME": 60 * 5,
        "PRICE_DESK_MAX_STALE_TIME": 60 * 60 * 24 * 3,
        # price desk (blocks)
        "PRICE_DESK_MIN_REG_TIMELOCK": 21_600,
        "PRICE_DESK_MAX_REG_TIMELOCK": 302_400,
        # vault book (blocks)
        "VAULT_BOOK_MIN_REG_TIMELOCK": 21_600,
        "VAULT_BOOK_MAX_REG_TIMELOCK": 302_400,
    },
}


CORE_TOKENS = {
    "base": {
        # stables
        "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "USDBC": "0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA",
        "USDS": "0x820C137fa70C8691f0e44Dc420a5e53c168921Dc",
        "DAI": "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb",
        "EURC": "0x60a3e35cc302bfa44cb288bc5a4f316fdb1adb42",
        "CRVUSD": "0x417ac0e078398c154edfadd9ef675d30be60af93",
        "GHO": "0x6Bb7a212910682DCFdbd5BCBb3e28FB4E8da10Ee",
        "SUSDS": "0x5875eEE11Cf8398102FdAd704C9E96607675467a",
        # eth
        "WETH": "0x4200000000000000000000000000000000000006",
        "WSTETH": "0xc1cba3fcea344f92d9239c08c0568f6f2f0ee452",
        "CBETH": "0x2ae3f1ec7f1f5012cfeab0185bfc7aa3cf0dec22",
        "WEETH": "0x04C0599Ae5A44757c0af6F9eC3b93da8976c150A",
        "EZETH": "0x2416092f143378750bb29b79eD961ab195CcEea5",
        "RETH": "0xB6fe221Fe9EeF5aBa221c348bA20A1Bf5e73624c",
        "WRSETH": "0xEDfa23602D0EC14714057867A78d01e94176BEA0",
        # btc
        "CBBTC": "0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf",
        "TBTC": "0x236aa50979d5f3de3bd1eeb40e81137f22ab794b",
        "LBTC": "0xecAc9C5F704e954931349Da37F60E39f515c11c1",
        # other
        "AERO": "0x940181a94a35a4569e4529a3cdfb74e38fd98631",
        "WELL": "0xA88594D404727625A9437C3f886C7643872296AE",
        "VIRTUAL": "0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b",
        "USOL": "0x9B8Df6E244526ab5F6e6400d331DB28C8fdDdb55",
        "CBDOGE": "0xcbD06E5A2B0C65597161de254AA074E489dEb510",
    },
}


CURVE_PARAMS = {
    "base": {
        # green pool parameters
        "GREEN_POOL_NAME": "GREEN/USDC Pool",
        "GREEN_POOL_SYMBOL": "GREEN/USDC",
        "GREEN_POOL_A": 100,
        "GREEN_POOL_FEE": 4000000,
        "GREEN_POOL_OFFPEG_MULTIPLIER": 20000000000,
        "GREEN_POOL_MA_EXP_TIME": 600,
        # ripe pool params
        "RIPE_POOL_NAME": "RIPE/WETH Pool",
        "RIPE_POOL_SYMBOL": "RIPE/WETH",
        "RIPE_POOL_A": 2700000,
        "RIPE_POOL_GAMMA": 1300000000000,
        "RIPE_POOL_MID_FEE": 2999999,
        "RIPE_POOL_OUT_FEE": 80000000,
        "RIPE_POOL_FEE_GAMMA": 350000000000000,
        "RIPE_POOL_EXTRA_PROFIT": 100000000000,
        "RIPE_POOL_ADJ_STEP": 100000000000,
        "RIPE_POOL_MA_EXP_TIME": 600,
        "RIPE_POOL_INIT_PRICE": 10 ** 13,
    },
}


WHALES = {
    "base": {
        "usdc": "0x0B0A5886664376F59C351ba3f598C8A8B4D0A6f3",
        "weth": "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb",
    },
}


YIELD_TOKENS = {
    "base": {
        # morpho
        "MORPHO_MOONWELL_WETH": "0xa0E430870c4604CcfC7B38Ca7845B1FF653D0ff1",  # moonwell
        "MORPHO_MOONWELL_USDC": "0xc1256Ae5FF1cf2719D4937adb3bbCCab2E00A2Ca",  # moonwell
        "MORPHO_MOONWELL_CBBTC": "0x543257eF2161176D7C8cD90BA65C2d4CaEF5a796",  # moonwell
        "MORPHO_MOONWELL_EURC": "0xf24608E0CCb972b0b0f4A6446a0BBf58c701a026",  # moonwell
        "MORPHO_SPARK_USDC": "0x7BfA7C4f149E7415b73bdeDfe609237e29CBF34A",  # spark
        "MORPHO_SEAMLESS_USDC": "0x616a4E1db48e22028f6bbf20444Cd3b8e3273738",  # seamless
        "MORPHO_SEAMLESS_WETH": "0x27D8c7273fd3fcC6956a0B370cE5Fd4A7fc65c18",  # seamless
        "MORPHO_SEAMLESS_CBBTC": "0x5a47C803488FE2BB0A0EAaf346b420e4dF22F3C7",  # seamless
        "MORPHO_GAUNTLET_WETH_CORE": "0x6b13c060F13Af1fdB319F52315BbbF3fb1D88844",  # gauntlet
        "MORPHO_GAUNTLET_CBBTC_CORE": "0x6770216aC60F634483Ec073cBABC4011c94307Cb",  # gauntlet
        "MORPHO_GAUNTLET_USDC_PRIME": "0xeE8F4eC5672F09119b96Ab6fB59C27E1b7e44b61",  # gauntlet
        "MORPHO_GAUNTLET_USDC_CORE": "0xc0c5689e6f4D256E861F65465b691aeEcC0dEb12",  # gauntlet
        "MORPHO_GAUNTLET_LBTC_CORE": "0x0D05e6ec0A10f9fFE9229EAA785c11606a1d13Fb",  # gauntlet
        "MORPHO_GAUNTLET_EURC_CORE": "0x1c155be6bC51F2c37d472d4C2Eba7a637806e122",  # gauntlet
        "MORPHO_STEAKHOUSE_USDC": "0xbeeF010f9cb27031ad51e3333f9aF9C6B1228183",  # steakhouse
        "MORPHO_STEAKHOUSE_EURC": "0xBeEF086b8807Dc5E5A1740C5E3a7C4c366eA6ab5",  # steakhouse
        "MORPHO_9SUMMITS_WETH": "0x5496b42ad0deCebFab0db944D83260e60D54f667",  # 9summits
        "MORPHO_RE7_WETH": "0xA2Cac0023a4797b4729Db94783405189a4203AFc",  # re7
        "MORPHO_RE7_USDC": "0x12AFDeFb2237a5963e7BAb3e2D46ad0eee70406e",  # re7
        "MORPHO_IONIC_WETH": "0x5A32099837D89E3a794a44fb131CBbAD41f87a8C",  # ionic
        "MORPHO_IONIC_USDC": "0x23479229e52Ab6aaD312D0B03DF9F33B46753B5e",  # ionic
        # euler (only dao-governed vaults)
        "EULER_USDC": "0x0A1a3b5f2041F33522C4efc754a7D096f880eE16",
        "EULER_USDS": "0x556d518FDFDCC4027A3A1388699c5E11AC201D8b",
        "EULER_WETH": "0x859160DB5841E5cfB8D3f144C6b3381A85A4b410",
        "EULER_WEETH": "0xd4A805261B28f375fc9c3d89EcD2C952Cd130d14",
        "EULER_CBBTC": "0x882018411Bc4A020A879CEE183441fC9fa5D7f8B",
        "EULER_EURC": "0x9ECD9fbbdA32b81dee51AdAed28c5C5039c87117",
        # fluid
        "FLUID_USDC": "0xf42f5795D9ac7e9D757dB633D693cD548Cfd9169",
        "FLUID_WETH": "0x9272D6153133175175Bc276512B2336BE3931CE9",
        "FLUID_WSTETH": "0x896E39f0E9af61ECA9dD2938E14543506ef2c2b5",
        "FLUID_EURC": "0x1943FA26360f038230442525Cf1B9125b5DCB401",
        "FLUID_SUSDS": "0xf62e339f21d8018940f188F6987Bcdf02A849619",
        # compound v3
        "COMPOUNDV3_USDC": "0xb125E6687d4313864e53df431d5425969c15Eb2F",
        "COMPOUNDV3_WETH": "0x46e6b214b524310239732D51387075E0e70970bf",
        # moonwell
        "MOONWELL_WETH": "0x628ff693426583D9a7FB391E54366292F509D457",
        "MOONWELL_USDC": "0xEdc817A28E8B93B03976FBd4a3dDBc9f7D176c22",
        "MOONWELL_CBBTC": "0xF877ACaFA28c19b96727966690b2f44d35aD5976",
        "MOONWELL_AERO": "0x73902f619CEB9B31FD8EFecf435CbDf89E369Ba6",
        "MOONWELL_WSTETH": "0x627Fe393Bc6EdDA28e99AE648fD6fF362514304b",
        "MOONWELL_CBETH": "0x3bf93770f2d4a794c3d9EBEfBAeBAE2a8f09A5E5",
        "MOONWELL_WEETH": "0xb8051464C8c92209C92F3a4CD9C73746C4c3CFb3",
        "MOONWELL_EURC": "0xb682c840B5F4FC58B20769E691A6fa1305A501a2",
        "MOONWELL_WELL": "0xdC7810B47eAAb250De623F0eE07764afa5F71ED1",
        "MOONWELL_RETH": "0xCB1DaCd30638ae38F2B94eA64F066045B7D45f44",
        "MOONWELL_LBTC": "0x10fF57877b79e9bd949B3815220eC87B9fc5D2ee",
        "MOONWELL_WRSETH": "0xfC41B49d064Ac646015b459C522820DB9472F4B5",
        "MOONWELL_VIRTUAL": "0xdE8Df9d942D78edE3Ca06e60712582F79CFfFC64",
        "MOONWELL_TBTC": "0x9A858ebfF1bEb0D3495BB0e2897c1528eD84A218",
        "MOONWELL_DAI": "0x73b06D8d18De422E269645eaCe15400DE7462417",
        "MOONWELL_USDS": "0xb6419c6C2e60c4025D6D06eE4F913ce89425a357",
        # aave v3 aTokens
        "AAVEV3_WETH": "0xD4a0e0b9149BCee3C920d2E00b5dE09138fd8bb7",
        "AAVEV3_CBETH": "0xcf3D55c10DB69f28fD1A75Bd73f3D8A2d9c595ad",
        "AAVEV3_USDBC": "0x0a1d576f3eFeF75b330424287a95A366e8281D54",
        "AAVEV3_WSTETH": "0x99CBC45ea5bb7eF3a5BC08FB1B7E56bB2442Ef0D",
        "AAVEV3_USDC": "0x4e65fE4DbA92790696d040ac24Aa414708F5c0AB",
        "AAVEV3_WEETH": "0x7C307e128efA31F540F2E2d976C995E0B65F51F6",
        "AAVEV3_CBBTC": "0xBdb9300b7CDE636d9cD4AFF00f6F009fFBBc8EE6",
        "AAVEV3_EZETH": "0xDD5745756C2de109183c6B5bB886F9207bEF114D",
        "AAVEV3_GHO": "0x067ae75628177FD257c2B1e500993e1a0baBcBd1",
        # super oethb
        "SUPER_OETH": "0xdbfefd2e8460a6ee4955a68582f85708baea60a3",
        "WRAPPED_SUPER_OETH": "0x7FcD174E80f264448ebeE8c88a7C4476AAF58Ea6",
        # underscore
        "UNDY_USD": "0xcF9F72237d4135a6D8b3ee717DC414Ae5b56E41e",
        "UNDY_ETH": "0x01ECc16CE82CCf7e6f734351d5d3AdCf2f8D3497",
        "UNDY_BTC": "0x4cD99832E44D1154bd7841f5E5E9ce66dA0437d4",
        "UNDY_AERO": "0xCaF73025d206AcC74736e1b54F92ee425694cF83",
        "UNDY_EURC": "0x04e77BC5885c82d68f523d1deE2e8b88c3036784",
        "UNDY_GHO": "0x78De8bd82035593e140e0f6567A019db3d716B74",
        "UNDY_CBETH": "0xe9EA27C1c67F12D04cb4694F8618AE8Bdb278E50",
        "UNDY_USDS": "0x04e77BC5885c82d68f523d1deE2e8b88c3036784",
    },
}


# Robinhood Profile 1 source authority
#
# Human-controlled addresses, topology, constructor inputs, clocks, and all
# non-Defaults deployment inputs live here. Defaults-interface values live only
# in contracts/config/DefaultsRobinhood.vy. The JSON ledger is derived evidence.

from dataclasses import dataclass
from typing import Any

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@dataclass(frozen=True)
class SymbolicBinding:
    semantic_name: str


@dataclass(frozen=True)
class SourceReference:
    path: str


@dataclass(frozen=True)
class RobinhoodInput:
    value: Any
    disposition: str


@dataclass(frozen=True)
class RobinhoodComponentSelection:
    component_id: str
    semantic_name: str
    deployment_disposition: str
    selection_state: str


@dataclass(frozen=True)
class RobinhoodRegistrySelection:
    domain: str
    registry_id: int
    semantic_name: str
    id_authority: str
    component_id: str
    disposition: str
    selection_state: str


# Selected external facts remain deployment-readiness blocked until their
# separately retained verification metadata is closed.
ROBINHOOD_USDG = "0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168"
ROBINHOOD_WETH = "0x0Bd7D308f8E1639FAb988df18A8011f41EAcAD73"
ROBINHOOD_STEAKHOUSE_USDG_VAULT = "0xBeEff033F34C046626B8D0A041844C5d1A5409dd"
ROBINHOOD_GOVERNANCE = "0xe488a42D33b3Af5d3E5Cd5680938d8369716D1bf"
ROBINHOOD_CHAINLINK_ETH_USD = "0x78F3556b67E17Df817D51Ef5a990cDaF09E8d3A9"
ROBINHOOD_CHAINLINK_BTC_USD = "0xa2c5184bF03d373Dc9dE4876eb4Bce595B460251"
ROBINHOOD_CHAINLINK_USDG_USD = "0x61B7e5650328764B076A108EFF5fa7282a1B9aD2"
ROBINHOOD_MORPHO_V2_FACTORY = "0x0FBad98595b0186dA120E41f77C102beb49f803c"
ROBINHOOD_NATIVE_ETH_SENTINEL = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"
ROBINHOOD_BTC_SENTINEL = "0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB"
ROBINHOOD_ARB_SYS = "0x0000000000000000000000000000000000000064"

ROBINHOOD_ADDRESSES = {
    # Deployment-produced: symbolic until the deployment plan binds them.
    "CONTRIBUTOR_TEMPLATE": SymbolicBinding("CONTRIBUTOR_TEMPLATE"),
    "TRAINING_WHEELS": SymbolicBinding("TRAINING_WHEELS"),
    "RIPE_TOKEN": SymbolicBinding("RIPE_TOKEN"),
    "GREEN_TOKEN": SymbolicBinding("GREEN_TOKEN"),
    "SGREEN_TOKEN": SymbolicBinding("SGREEN_TOKEN"),
    # Defaults constructor external facts.
    "USDG": ROBINHOOD_USDG,
    "WETH": ROBINHOOD_WETH,
    "STEAKHOUSE_USDG_VAULT": ROBINHOOD_STEAKHOUSE_USDG_VAULT,
    # Governance, oracle, protocol, and chain identities.
    "GOVERNANCE": ROBINHOOD_GOVERNANCE,
    "SAFE": ROBINHOOD_GOVERNANCE,
    "GUARDIAN": SymbolicBinding("GUARDIAN"),
    "CHAINLINK_ETH_USD": ROBINHOOD_CHAINLINK_ETH_USD,
    "CHAINLINK_BTC_USD": ROBINHOOD_CHAINLINK_BTC_USD,
    "CHAINLINK_USDG_USD": ROBINHOOD_CHAINLINK_USDG_USD,
    "MORPHO_V2_FACTORY": ROBINHOOD_MORPHO_V2_FACTORY,
    "NATIVE_ETH_SENTINEL": ROBINHOOD_NATIVE_ETH_SENTINEL,
    "BTC_SENTINEL": ROBINHOOD_BTC_SENTINEL,
    "ARB_SYS": ROBINHOOD_ARB_SYS,
    # Intentionally absent Profile 1 integration.
    "UNDERSCORE_REGISTRY": ZERO_ADDRESS,
}

ROBINHOOD_ADDRESS_STATUS = {
    "CONTRIBUTOR_TEMPLATE": "deployment_produced_unresolved",
    "TRAINING_WHEELS": "deployment_produced_unresolved",
    "RIPE_TOKEN": "deployment_produced_unresolved",
    "GREEN_TOKEN": "deployment_produced_unresolved",
    "SGREEN_TOKEN": "deployment_produced_unresolved",
    "GUARDIAN": "deployment_produced_unresolved",
    "USDG": "selected_external_fact_unverified",
    "WETH": "selected_external_fact_unverified",
    "STEAKHOUSE_USDG_VAULT": "selected_external_fact_unverified",
    "GOVERNANCE": "selected_external_fact_unverified",
    "SAFE": "selected_external_fact_unverified",
    "CHAINLINK_ETH_USD": "selected_external_fact_unverified",
    "CHAINLINK_BTC_USD": "selected_external_fact_unverified",
    "CHAINLINK_USDG_USD": "selected_external_fact_unverified",
    "MORPHO_V2_FACTORY": "selected_external_fact_unverified",
    "NATIVE_ETH_SENTINEL": "selected_external_fact_unverified",
    "BTC_SENTINEL": "selected_external_fact_unverified",
    "ARB_SYS": "selected_external_fact_unverified",
    "UNDERSCORE_REGISTRY": "approved_semantic_absence",
}

ROBINHOOD_DEFAULTS_CONSTRUCTOR = (
    ("contributorTemplate", "CONTRIBUTOR_TEMPLATE"),
    ("trainingWheels", "TRAINING_WHEELS"),
    ("ripeToken", "RIPE_TOKEN"),
    ("greenToken", "GREEN_TOKEN"),
    ("sgreenToken", "SGREEN_TOKEN"),
    ("usdgToken", "USDG"),
    ("wethToken", "WETH"),
    ("steakhouseUsdgVault", "STEAKHOUSE_USDG_VAULT"),
)

ROBINHOOD_CHAIN = {
    "mainnet_chain_id": 4663,
    "testnet_chain_id": 46630,
    "evm_block_number_seconds": 12,
    "blocks_per_minute": 5,
    "action_block_source": SymbolicBinding("LEDGER_ACTION_BLOCK_SOURCE"),
}

ROBINHOOD_COMPONENT_DEPLOYMENT_STATES = frozenset(
    {"required", "omitted", "disabled", "deferred", "blocked"}
)
ROBINHOOD_SELECTION_STATES = frozenset(
    {"selected", "omitted", "disabled", "deferred", "blocked", "reserved"}
)

# Complete Profile 1 component selection authority. Lifecycle, owner, gate,
# relation, blocker, and evidence metadata remain in robinhood_blueprint.py.
ROBINHOOD_COMPONENT_SELECTIONS = (
    RobinhoodComponentSelection("CM-001", "GreenToken", "required", "selected"),
    RobinhoodComponentSelection("CM-002", "RipeToken", "required", "selected"),
    RobinhoodComponentSelection("CM-003", "SavingsGreen", "required", "selected"),
    RobinhoodComponentSelection("CM-004", "RipeHq", "required", "selected"),
    RobinhoodComponentSelection("CM-005", "Contributor", "omitted", "omitted"),
    RobinhoodComponentSelection("CM-006", "TrainingWheels", "required", "selected"),
    RobinhoodComponentSelection("CM-007", "DefaultsBase", "omitted", "omitted"),
    RobinhoodComponentSelection("CM-008", "Ledger", "blocked", "blocked"),
    RobinhoodComponentSelection("CM-009", "MissionControl", "required", "selected"),
    RobinhoodComponentSelection("CM-010", "Switchboard", "required", "selected"),
    RobinhoodComponentSelection("CM-011", "SwitchboardAlpha", "required", "selected"),
    RobinhoodComponentSelection("CM-012", "SwitchboardBravo", "required", "selected"),
    RobinhoodComponentSelection("CM-013", "SwitchboardCharlie", "required", "selected"),
    RobinhoodComponentSelection("CM-014", "SwitchboardDelta", "required", "selected"),
    RobinhoodComponentSelection("CM-015", "PriceDesk", "required", "selected"),
    RobinhoodComponentSelection("CM-016", "ChainlinkPrices", "required", "selected"),
    RobinhoodComponentSelection("CM-017", "CurvePrices", "omitted", "omitted"),
    RobinhoodComponentSelection("CM-018", "BlueChipYieldPrices", "required", "selected"),
    RobinhoodComponentSelection("CM-019", "PythPrices", "omitted", "omitted"),
    RobinhoodComponentSelection("CM-020", "StorkPrices", "omitted", "omitted"),
    RobinhoodComponentSelection("CM-021", "VaultBook", "required", "selected"),
    RobinhoodComponentSelection("CM-022", "StabilityPool", "required", "selected"),
    RobinhoodComponentSelection("CM-023", "RipeGov", "required", "selected"),
    RobinhoodComponentSelection("CM-024", "SimpleErc20", "required", "selected"),
    RobinhoodComponentSelection(
        "CM-025", "RebaseErc20 / inherited SharesVault", "omitted", "omitted"
    ),
    RobinhoodComponentSelection("CM-026", "AuctionHouse", "required", "selected"),
    RobinhoodComponentSelection("CM-027", "AuctionHouseNFT", "required", "selected"),
    RobinhoodComponentSelection("CM-028", "Boardroom", "required", "selected"),
    RobinhoodComponentSelection("CM-029", "BondRoom", "required", "selected"),
    RobinhoodComponentSelection("CM-030", "CreditEngine", "required", "selected"),
    RobinhoodComponentSelection("CM-031", "Endaoment", "required", "selected"),
    RobinhoodComponentSelection("CM-032", "HumanResources", "required", "selected"),
    RobinhoodComponentSelection("CM-033", "Lootbox", "required", "selected"),
    RobinhoodComponentSelection("CM-034", "Teller", "required", "selected"),
    RobinhoodComponentSelection("CM-035", "GreenPool", "omitted", "omitted"),
    RobinhoodComponentSelection("CM-036", "RipePoolCurve", "omitted", "omitted"),
    RobinhoodComponentSelection("CM-037", "RipePoolAero", "omitted", "omitted"),
    RobinhoodComponentSelection("CM-038", "BondBooster", "required", "selected"),
    RobinhoodComponentSelection("CM-039", "wsuperOETHbPrices", "omitted", "omitted"),
    RobinhoodComponentSelection("CM-040", "RedStone", "omitted", "omitted"),
    RobinhoodComponentSelection("CM-041", "UndyVaultPrices", "omitted", "omitted"),
    RobinhoodComponentSelection("CM-042", "Underscore Vault", "omitted", "omitted"),
    RobinhoodComponentSelection("CM-043", "CreditRedeem", "required", "selected"),
    RobinhoodComponentSelection("CM-044", "Deleverage", "required", "selected"),
    RobinhoodComponentSelection("CM-045", "TellerUtils", "required", "selected"),
    RobinhoodComponentSelection("CM-046", "SwitchboardEcho", "required", "selected"),
    RobinhoodComponentSelection("CM-047", "EndaomentFunds", "required", "selected"),
    RobinhoodComponentSelection("CM-048", "EndaomentPSM", "required", "selected"),
    RobinhoodComponentSelection("CM-049", "DefaultsRobinhood", "required", "selected"),
    RobinhoodComponentSelection("CM-050", "AeroRipePrices", "omitted", "omitted"),
    RobinhoodComponentSelection(
        "CM-051", "GREEN CCIP BurnMint pool", "deferred", "deferred"
    ),
    RobinhoodComponentSelection(
        "CM-052", "RIPE CCIP BurnMint pool", "deferred", "deferred"
    ),
    RobinhoodComponentSelection(
        "CM-053", "CCIP token-admin registration", "deferred", "deferred"
    ),
    RobinhoodComponentSelection(
        "CM-054", "GREEN/RIPE local price adapter", "deferred", "deferred"
    ),
    RobinhoodComponentSelection(
        "CM-055",
        "Deployment, migration, and parameter-report tooling",
        "required",
        "selected",
    ),
    RobinhoodComponentSelection(
        "CM-056", "Manifests and migration history", "required", "selected"
    ),
    RobinhoodComponentSelection(
        "CM-057", "ABI export and explorer verification", "required", "selected"
    ),
    RobinhoodComponentSelection(
        "CM-058", "Solidity build/test/deploy toolchain", "deferred", "deferred"
    ),
    RobinhoodComponentSelection("CM-059", "Base/RH test profiles", "required", "selected"),
    RobinhoodComponentSelection("CM-060", "DefaultsLocal", "omitted", "omitted"),
)

ROBINHOOD_REGISTRY_DOMAINS = ("ripe_hq", "vault_book", "price_desk", "switchboard")
ROBINHOOD_REGISTRY_ID_AUTHORITIES = (
    "source_hard_coded",
    "registration_order",
    "provisional_reservation",
)

# Complete 38-row registry authority. A reserved row is deliberately unselected;
# its deployment disposition still records whether it is omitted or deferred.
ROBINHOOD_REGISTRY_TOPOLOGY = (
    RobinhoodRegistrySelection("ripe_hq", 1, "Green Token", "source_hard_coded", "CM-001", "required", "selected"),
    RobinhoodRegistrySelection("ripe_hq", 2, "Savings Green", "source_hard_coded", "CM-003", "required", "selected"),
    RobinhoodRegistrySelection("ripe_hq", 3, "Ripe Token", "source_hard_coded", "CM-002", "required", "selected"),
    RobinhoodRegistrySelection("ripe_hq", 4, "Ledger", "source_hard_coded", "CM-008", "blocked", "blocked"),
    RobinhoodRegistrySelection("ripe_hq", 5, "Mission Control", "source_hard_coded", "CM-009", "required", "selected"),
    RobinhoodRegistrySelection("ripe_hq", 6, "Switchboard", "source_hard_coded", "CM-010", "required", "selected"),
    RobinhoodRegistrySelection("ripe_hq", 7, "Price Desk", "source_hard_coded", "CM-015", "required", "selected"),
    RobinhoodRegistrySelection("ripe_hq", 8, "Vault Book", "source_hard_coded", "CM-021", "required", "selected"),
    RobinhoodRegistrySelection("ripe_hq", 9, "Auction House", "source_hard_coded", "CM-026", "required", "selected"),
    RobinhoodRegistrySelection("ripe_hq", 10, "Auction House NFT", "source_hard_coded", "CM-027", "required", "selected"),
    RobinhoodRegistrySelection("ripe_hq", 11, "Boardroom", "source_hard_coded", "CM-028", "required", "selected"),
    RobinhoodRegistrySelection("ripe_hq", 12, "Bond Room", "source_hard_coded", "CM-029", "required", "selected"),
    RobinhoodRegistrySelection("ripe_hq", 13, "Credit Engine", "source_hard_coded", "CM-030", "required", "selected"),
    RobinhoodRegistrySelection("ripe_hq", 14, "Endaoment", "source_hard_coded", "CM-031", "required", "selected"),
    RobinhoodRegistrySelection("ripe_hq", 15, "Human Resources", "source_hard_coded", "CM-032", "required", "selected"),
    RobinhoodRegistrySelection("ripe_hq", 16, "Lootbox", "source_hard_coded", "CM-033", "required", "selected"),
    RobinhoodRegistrySelection("ripe_hq", 17, "Teller", "source_hard_coded", "CM-034", "required", "selected"),
    RobinhoodRegistrySelection("ripe_hq", 18, "Deleverage", "source_hard_coded", "CM-044", "required", "selected"),
    RobinhoodRegistrySelection("ripe_hq", 19, "Credit Redeem", "source_hard_coded", "CM-043", "required", "selected"),
    RobinhoodRegistrySelection("ripe_hq", 20, "Teller Utils", "source_hard_coded", "CM-045", "required", "selected"),
    RobinhoodRegistrySelection("ripe_hq", 21, "Endaoment Funds", "source_hard_coded", "CM-047", "required", "selected"),
    RobinhoodRegistrySelection("ripe_hq", 22, "Endaoment PSM", "source_hard_coded", "CM-048", "required", "selected"),
    RobinhoodRegistrySelection("ripe_hq", 23, "GREEN CCIP BurnMint pool", "provisional_reservation", "CM-051", "deferred", "reserved"),
    RobinhoodRegistrySelection("ripe_hq", 24, "RIPE CCIP BurnMint pool", "provisional_reservation", "CM-052", "deferred", "reserved"),
    RobinhoodRegistrySelection("vault_book", 1, "Stability Pool", "source_hard_coded", "CM-022", "required", "selected"),
    RobinhoodRegistrySelection("vault_book", 2, "Ripe Gov Vault", "source_hard_coded", "CM-023", "required", "selected"),
    RobinhoodRegistrySelection("vault_book", 3, "Simple ERC20 Vault", "registration_order", "CM-024", "required", "selected"),
    RobinhoodRegistrySelection("vault_book", 4, "Rebase ERC20 Vault", "registration_order", "CM-025", "omitted", "omitted"),
    RobinhoodRegistrySelection("price_desk", 1, "Chainlink", "registration_order", "CM-016", "required", "selected"),
    RobinhoodRegistrySelection("price_desk", 2, "Curve", "source_hard_coded", "CM-017", "omitted", "reserved"),
    RobinhoodRegistrySelection("price_desk", 3, "BlueChipYield", "registration_order", "CM-018", "required", "selected"),
    RobinhoodRegistrySelection("price_desk", 4, "Pyth", "source_hard_coded", "CM-019", "omitted", "omitted"),
    RobinhoodRegistrySelection("price_desk", 5, "Stork", "registration_order", "CM-020", "omitted", "omitted"),
    RobinhoodRegistrySelection("switchboard", 1, "Switchboard Alpha", "source_hard_coded", "CM-011", "required", "selected"),
    RobinhoodRegistrySelection("switchboard", 2, "Switchboard Bravo", "registration_order", "CM-012", "required", "selected"),
    RobinhoodRegistrySelection("switchboard", 3, "Switchboard Charlie", "registration_order", "CM-013", "required", "selected"),
    RobinhoodRegistrySelection("switchboard", 4, "Switchboard Delta", "registration_order", "CM-014", "required", "selected"),
    RobinhoodRegistrySelection("switchboard", 5, "Switchboard Echo", "registration_order", "CM-046", "required", "selected"),
)

# Assertion-class records are computed evidence, not ledger-owned values.
ROBINHOOD_ASSERTION_INVARIANTS = {
    "deleverage_launch_cooldown": 0,
    "timelock_base_headroom_blocks": 366,
    "base_blocks_per_robinhood_block": 6,
    "psm_activation_sequence": (
        "redemption",
        "auto_deposit_off",
        "reserve_funding",
        "configuration",
        "allowlists",
        "green_mint",
    ),
    "aapl_cap_formula": "floor(D * 10^(18+8) / P8)",
    "aapl_cap_inputs": ("D target", "P8 freeze price"),
    "stock_enabled_vaults": ("SimpleErc20",),
    "stock_excluded_from_stability_pool": False,
    "profile_2_lp_ltv": 0,
}

ROBINHOOD_COMPONENTS = {
    "price_desk_registry": {
        row.registry_id: row.semantic_name if row.selection_state == "selected" else None
        for row in ROBINHOOD_REGISTRY_TOPOLOGY
        if row.domain == "price_desk"
    },
    "blue_chip_yield": {
        "protocol": "MorphoV2",
        "compatibility": "resolved_by_33ad0f3c08bf6dc88f6569c622886d264d6e2868",
    },
    "profile_1_omissions": ("GREEN_USDG_LP", "RIPE_WETH_LP"),
}

ROBINHOOD_DEPLOYMENT_INPUTS = {
    # DP-04
    'Deployment.DP-04.ledger.actionBlockSourceBinding': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_04_LEDGER_ACTIONBLOCKSOURCEBINDING'), 'blocked'),
    # DP-05
    'Deployment.DP-05.timelocks.TokenHq.actionTimeLock': RobinhoodInput(7200, 'approved'),
    'Deployment.DP-05.timelocks.TokenHq.minTimeLock': RobinhoodInput(7200, 'approved'),
    'Deployment.DP-05.timelocks.TokenHq.maxTimeLock': RobinhoodInput(50400, 'approved'),
    'Deployment.DP-05.timelocks.LocalGov.actionTimeLock': RobinhoodInput(7200, 'approved'),
    'Deployment.DP-05.timelocks.LocalGov.minTimeLock': RobinhoodInput(7200, 'approved'),
    'Deployment.DP-05.timelocks.LocalGov.maxTimeLock': RobinhoodInput(50400, 'approved'),
    'Deployment.DP-05.timelocks.RipeHq.actionTimeLock': RobinhoodInput(3600, 'approved'),
    'Deployment.DP-05.timelocks.RipeHq.minTimeLock': RobinhoodInput(3600, 'approved'),
    'Deployment.DP-05.timelocks.RipeHq.maxTimeLock': RobinhoodInput(50400, 'approved'),
    'Deployment.DP-05.timelocks.SwitchboardAlpha.actionTimeLock': RobinhoodInput(0, 'approved'),
    'Deployment.DP-05.timelocks.SwitchboardAlpha.minTimeLock': RobinhoodInput(600, 'approved'),
    'Deployment.DP-05.timelocks.SwitchboardAlpha.maxTimeLock': RobinhoodInput(50400, 'approved'),
    'Deployment.DP-05.timelocks.SwitchboardAlpha.expiration': RobinhoodInput(50400, 'approved'),
    'Deployment.DP-05.timelocks.SwitchboardBravo.actionTimeLock': RobinhoodInput(0, 'approved'),
    'Deployment.DP-05.timelocks.SwitchboardBravo.minTimeLock': RobinhoodInput(600, 'approved'),
    'Deployment.DP-05.timelocks.SwitchboardBravo.maxTimeLock': RobinhoodInput(50400, 'approved'),
    'Deployment.DP-05.timelocks.SwitchboardBravo.expiration': RobinhoodInput(50400, 'approved'),
    'Deployment.DP-05.timelocks.SwitchboardCharlie.actionTimeLock': RobinhoodInput(0, 'approved'),
    'Deployment.DP-05.timelocks.SwitchboardCharlie.minTimeLock': RobinhoodInput(600, 'approved'),
    'Deployment.DP-05.timelocks.SwitchboardCharlie.maxTimeLock': RobinhoodInput(50400, 'approved'),
    'Deployment.DP-05.timelocks.SwitchboardCharlie.expiration': RobinhoodInput(50400, 'approved'),
    'Deployment.DP-05.timelocks.SwitchboardDelta.actionTimeLock': RobinhoodInput(0, 'approved'),
    'Deployment.DP-05.timelocks.SwitchboardDelta.minTimeLock': RobinhoodInput(600, 'approved'),
    'Deployment.DP-05.timelocks.SwitchboardDelta.maxTimeLock': RobinhoodInput(50400, 'approved'),
    'Deployment.DP-05.timelocks.SwitchboardDelta.expiration': RobinhoodInput(50400, 'approved'),
    'Deployment.DP-05.timelocks.SwitchboardEcho.actionTimeLock': RobinhoodInput(0, 'approved'),
    'Deployment.DP-05.timelocks.SwitchboardEcho.minTimeLock': RobinhoodInput(600, 'approved'),
    'Deployment.DP-05.timelocks.SwitchboardEcho.maxTimeLock': RobinhoodInput(50400, 'approved'),
    'Deployment.DP-05.timelocks.SwitchboardEcho.expiration': RobinhoodInput(50400, 'approved'),
    'Deployment.DP-05.timelocks.Chainlink.actionTimeLock': RobinhoodInput(0, 'approved'),
    'Deployment.DP-05.timelocks.Chainlink.minTimeLock': RobinhoodInput(600, 'approved'),
    'Deployment.DP-05.timelocks.Chainlink.maxTimeLock': RobinhoodInput(50400, 'approved'),
    'Deployment.DP-05.timelocks.Chainlink.expiration': RobinhoodInput(50400, 'approved'),
    'Deployment.DP-05.timelocks.HumanResources.actionTimeLock': RobinhoodInput(7200, 'approved'),
    'Deployment.DP-05.timelocks.HumanResources.minTimeLock': RobinhoodInput(7200, 'approved'),
    'Deployment.DP-05.timelocks.HumanResources.maxTimeLock': RobinhoodInput(50400, 'approved'),
    'Deployment.DP-05.timelocks.HumanResources.expiration': RobinhoodInput(50400, 'approved'),
    'Deployment.DP-05.timelocks.Contributor.delay': RobinhoodInput(7200, 'approved'),
    'Deployment.DP-05.timelocks.AddressRegistry.addDelay': RobinhoodInput(3600, 'approved'),
    'Deployment.DP-05.timelocks.AddressRegistry.updateDelay': RobinhoodInput(3600, 'approved'),
    'Deployment.DP-05.timelocks.AddressRegistry.disableDelay': RobinhoodInput(3600, 'approved'),
    'Deployment.DP-05.timelocks.AddressRegistry.minDelay': RobinhoodInput(3600, 'approved'),
    'Deployment.DP-05.timelocks.AddressRegistry.maxDelay': RobinhoodInput(50400, 'approved'),
    # DP-07
    'Deployment.DP-07.psm.constructor.canMint': RobinhoodInput(False, 'disabled'),
    'Deployment.DP-07.psm.constructor.canRedeem': RobinhoodInput(False, 'disabled'),
    'Deployment.DP-07.psm.constructor.shouldAutoDeposit': RobinhoodInput(True, 'approved'),
    'Deployment.DP-07.psm.preActivation.shouldAutoDeposit': RobinhoodInput(False, 'disabled'),
    'Deployment.DP-07.psm.yield.amount': RobinhoodInput(0, 'disabled'),
    'Deployment.DP-07.psm.yield.asset': RobinhoodInput(ZERO_ADDRESS, 'disabled'),
    # DP-08
    'Deployment.DP-08.psm.mintFee': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_08_PSM_MINTFEE'), 'blocked'),
    'Deployment.DP-08.psm.redeemFee': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_08_PSM_REDEEMFEE'), 'blocked'),
    'Deployment.DP-08.psm.maxMintPerInterval': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_08_PSM_MAXMINTPERINTERVAL'), 'blocked'),
    'Deployment.DP-08.psm.maxRedeemPerInterval': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_08_PSM_MAXREDEEMPERINTERVAL'), 'blocked'),
    'Deployment.DP-08.psm.numBlocksPerInterval': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_08_PSM_NUMBLOCKSPERINTERVAL'), 'blocked'),
    'Deployment.DP-08.psm.allowlists': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_08_PSM_ALLOWLISTS'), 'blocked'),
    'Deployment.DP-08.psm.reserveFunding': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_08_PSM_RESERVEFUNDING'), 'blocked'),
    # DP-09
    'Deployment.DP-09.psm.executionBinding': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_09_PSM_EXECUTIONBINDING'), 'blocked'),
    # DP-10
    'Deployment.DP-10.aapl.identity': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_10_AAPL_IDENTITY'), 'blocked'),
    'Deployment.DP-10.aapl.feed': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_10_AAPL_FEED'), 'blocked'),
    'Deployment.DP-10.aapl.decimals': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_10_AAPL_DECIMALS'), 'blocked'),
    'Deployment.DP-10.aapl.P8': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_10_AAPL_P8'), 'blocked'),
    'Deployment.DP-10.aapl.perUserCap': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_10_AAPL_PERUSERCAP'), 'blocked'),
    'Deployment.DP-10.aapl.globalCap': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_10_AAPL_GLOBALCAP'), 'blocked'),
    'Deployment.DP-10.aapl.vault': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_10_AAPL_VAULT'), 'blocked'),
    'Deployment.DP-10.aapl.risk': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_10_AAPL_RISK'), 'blocked'),
    'Deployment.DP-10.aapl.auction': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_10_AAPL_AUCTION'), 'blocked'),
    'Deployment.DP-10.aapl.route': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_10_AAPL_ROUTE'), 'blocked'),
    # DP-11
    'Deployment.DP-11.stock.vaultArtifact': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_11_STOCK_VAULTARTIFACT'), 'blocked'),
    'Deployment.DP-11.stock.vaultSlot': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_11_STOCK_VAULTSLOT'), 'blocked'),
    'Deployment.DP-11.stock.m2Movement': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_11_STOCK_M2MOVEMENT'), 'blocked'),
    'Deployment.DP-11.stock.m3CreditContainment': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_11_STOCK_M3CREDITCONTAINMENT'), 'blocked'),
    'Deployment.DP-11.stock.m4ComposedProof': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_11_STOCK_M4COMPOSEDPROOF'), 'blocked'),
    'Deployment.DP-11.stock.m5ActivationBinding': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_11_STOCK_M5ACTIVATIONBINDING'), 'blocked'),
    # DP-13
    'Deployment.DP-13.stability.specialStabPoolId': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_13_STABILITY_SPECIALSTABPOOLID'), 'blocked'),
    # DP-14
    'Deployment.DP-14.lp.identities': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_14_LP_IDENTITIES'), 'blocked'),
    'Deployment.DP-14.lp.decimals': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_14_LP_DECIMALS'), 'blocked'),
    'Deployment.DP-14.lp.depositLimits': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_14_LP_DEPOSITLIMITS'), 'blocked'),
    'Deployment.DP-14.lp.oracleArtifacts': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_14_LP_ORACLEARTIFACTS'), 'blocked'),
    # DP-15
    'Deployment.DP-15.rewards.arePointsEnabled': RobinhoodInput(SourceReference('Defaults.rewardsConfig.arePointsEnabled'), 'approved'),
    'Deployment.DP-15.rewards.ripePerBlock': RobinhoodInput(SourceReference('Defaults.rewardsConfig.ripePerBlock'), 'approved'),
    'Deployment.DP-15.rewards.promotion': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_15_REWARDS_PROMOTION'), 'blocked'),
    # DP-16
    'Deployment.DP-16.ccip.greenEnabled': RobinhoodInput(False, 'disabled'),
    'Deployment.DP-16.ccip.ripeEnabled': RobinhoodInput(False, 'disabled'),
    'Deployment.DP-16.ccip.sgreenEnabled': RobinhoodInput(False, 'disabled'),
    'Deployment.DP-16.ccip.promotion': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_16_CCIP_PROMOTION'), 'blocked'),
    # DP-17
    'Deployment.DP-17.staleWindows.alphaMinimum': RobinhoodInput(300, 'approved'),
    'Deployment.DP-17.staleWindows.alphaMaximum': RobinhoodInput(604800, 'approved'),
    'Deployment.DP-17.staleWindows.chainlinkDefault': RobinhoodInput(86400, 'approved'),
    'Deployment.DP-17.staleWindows.aaplCeiling': RobinhoodInput(86400, 'approved'),
    'Deployment.DP-17.staleWindows.usdgCeiling': RobinhoodInput(86400, 'approved'),
    # DP-18
    'Deployment.DP-18.roles.governance': RobinhoodInput(ROBINHOOD_ADDRESSES["GOVERNANCE"], 'external_fact'),
    'Deployment.DP-18.roles.safe': RobinhoodInput(ROBINHOOD_ADDRESSES["SAFE"], 'external_fact'),
    'Deployment.DP-18.roles.guardian': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_18_ROLES_GUARDIAN'), 'blocked'),
    'Deployment.DP-18.roles.liteSigners': RobinhoodInput(SourceReference('Defaults.liteSigners[0]'), 'approved'),
    'Deployment.DP-18.roles.trainingWheels': RobinhoodInput(SourceReference('Defaults.trainingWheels'), 'blocked'),
    'Deployment.DP-18.roles.trainingWheelsAllowlist': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_18_ROLES_TRAININGWHEELSALLOWLIST'), 'blocked'),
    # DP-19
    'Deployment.DP-19.supply.GREEN.amount': RobinhoodInput(0, 'approved'),
    'Deployment.DP-19.supply.GREEN.recipient': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_19_SUPPLY_GREEN_RECIPIENT'), 'blocked'),
    'Deployment.DP-19.supply.RIPE.amount': RobinhoodInput(0, 'approved'),
    'Deployment.DP-19.supply.RIPE.recipient': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_19_SUPPLY_RIPE_RECIPIENT'), 'blocked'),
    'Deployment.DP-19.supply.SGREEN.amount': RobinhoodInput(0, 'approved'),
    'Deployment.DP-19.supply.SGREEN.recipient': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_19_SUPPLY_SGREEN_RECIPIENT'), 'blocked'),
    # DP-20
    'Deployment.DP-20.teller.shouldPause': RobinhoodInput(True, 'approved'),
    # DP-21
    'Deployment.DP-21.endaoment.wethIdentity': RobinhoodInput(ROBINHOOD_ADDRESSES["WETH"], 'external_fact'),
    'Deployment.DP-21.endaoment.nativeSymbol': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_21_ENDAOMENT_NATIVESYMBOL'), 'blocked'),
    'Deployment.DP-21.endaoment.nativeName': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_21_ENDAOMENT_NATIVENAME'), 'blocked'),
    'Deployment.DP-21.endaoment.nativeDecimals': RobinhoodInput(SymbolicBinding('DEPLOYMENT_DP_21_ENDAOMENT_NATIVEDECIMALS'), 'blocked'),
    # DP-22
    'Deployment.DP-22.bondBooster.maxBoostRatio': RobinhoodInput(20000, 'approved'),
    'Deployment.DP-22.bondBooster.maxUnits': RobinhoodInput(25000, 'approved'),
    'Deployment.DP-22.bondBooster.minLockDuration': RobinhoodInput(1296000, 'approved'),
    # DP-23
    'Deployment.DP-23.external.chainlink.ethUsdFeed': RobinhoodInput(ROBINHOOD_ADDRESSES["CHAINLINK_ETH_USD"], 'external_fact'),
    'Deployment.DP-23.external.chainlink.btcUsdFeed': RobinhoodInput(ROBINHOOD_ADDRESSES["CHAINLINK_BTC_USD"], 'external_fact'),
    'Deployment.DP-23.external.chainlink.usdgUsdFeed': RobinhoodInput(ROBINHOOD_ADDRESSES["CHAINLINK_USDG_USD"], 'external_fact'),
    'Deployment.DP-23.external.blueChipYield.morphoV2Factory': RobinhoodInput(ROBINHOOD_ADDRESSES["MORPHO_V2_FACTORY"], 'external_fact'),
    'Deployment.DP-23.external.nativeEthSentinel': RobinhoodInput(ROBINHOOD_ADDRESSES["NATIVE_ETH_SENTINEL"], 'external_fact'),
    'Deployment.DP-23.external.btcSentinel': RobinhoodInput(ROBINHOOD_ADDRESSES["BTC_SENTINEL"], 'external_fact'),
    'Deployment.DP-23.external.arbSys': RobinhoodInput(ROBINHOOD_ADDRESSES["ARB_SYS"], 'external_fact'),
    'Deployment.DP-23.blueChipYield.morphoV2Support': RobinhoodInput(True, 'approved'),
}

# DeployArgs indexes all five legacy dictionaries. Robinhood deliberately has
# no Curve or generic yield-token surface in Profile 1 beyond the selected
# SteakHouse USDG vault. Values below are references to the authorities above.
ADDYS["robinhood"] = ROBINHOOD_ADDRESSES
PARAMS["robinhood"] = {
    "DEPLOYMENT_INPUTS": ROBINHOOD_DEPLOYMENT_INPUTS,
    "CHAIN": ROBINHOOD_CHAIN,
    "COMPONENTS": ROBINHOOD_COMPONENTS,
}
CURVE_PARAMS["robinhood"] = {}
CORE_TOKENS["robinhood"] = {
    "USDG": ROBINHOOD_ADDRESSES["USDG"],
    "WETH": ROBINHOOD_ADDRESSES["WETH"],
    "GREEN": ROBINHOOD_ADDRESSES["GREEN_TOKEN"],
    "RIPE": ROBINHOOD_ADDRESSES["RIPE_TOKEN"],
    "SGREEN": ROBINHOOD_ADDRESSES["SGREEN_TOKEN"],
}
YIELD_TOKENS["robinhood"] = {
    "STEAKHOUSE_USDG": ROBINHOOD_ADDRESSES["STEAKHOUSE_USDG_VAULT"],
}
