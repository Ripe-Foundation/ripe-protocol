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
import hashlib
import json
from pathlib import Path
import subprocess
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


@dataclass(frozen=True)
class RobinhoodStockInputQualification:
    path: str
    resolution: str
    candidate: Any
    constraints: tuple[str, ...]
    blocker_ids: tuple[str, ...]


@dataclass(frozen=True)
class RobinhoodHistoricalTrancheIdentity:
    integration_commit: str
    changed_paths: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class RobinhoodGitPathIdentity:
    path: str
    git_blob: str
    sha256: str


@dataclass(frozen=True)
class RobinhoodArtifactApplicabilityIdentity:
    contract: str
    source_path: str
    source_git_blob: str
    source_sha256: str
    creation_sha256: str
    runtime_template_sha256: str
    abi_canonical_sha256: str
    selectors_canonical_sha256: str


@dataclass(frozen=True)
class RobinhoodStockM4Binding:
    historical_tranche: RobinhoodHistoricalTrancheIdentity
    current_test_identities: tuple[RobinhoodGitPathIdentity, ...]
    current_artifact_identities: tuple[
        RobinhoodArtifactApplicabilityIdentity, ...
    ]


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
    RobinhoodComponentSelection("CM-017", "CurvePrices", "required", "selected"),
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
    RobinhoodRegistrySelection("price_desk", 2, "Curve", "source_hard_coded", "CM-017", "required", "selected"),
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
    "stock_enabled_vaults": ("GuardedErc20",),
    "stock_excluded_from_stability_pool": True,
    "profile_2_lp_ltv": 0,
}

# Stock/AAPL launch qualification. These records intentionally do not populate
# DefaultsRobinhood or make any Stock route reachable. They distinguish exact
# repository evidence and selected external candidates from the values that
# still require owner acceptance or current-chain verification. Every record is
# consumed as one atomic M5 packet; a partial record set is not deployable.
ROBINHOOD_INITIAL_STOCK_SYMBOLS = ("AAPL",)
ROBINHOOD_AAPL_TOKEN_CANDIDATE = "0xaF3D76f1834A1d425780943C99Ea8A608f8a93f9"
ROBINHOOD_AAPL_FEED_CANDIDATE = "0x6B22A786bAa607d76728168703a39Ea9C99f2cD0"

ROBINHOOD_STOCK_ACTIVATION_POLICY = (
    ("vault", "GuardedErc20"),
    ("exclusiveVaultAssignment", True),
    ("shouldSwapInStabPools", False),
    ("shouldTransferToEndaoment", False),
    ("shouldAuctionInstantly", True),
    ("canRedeemCollateral", False),
    ("unsupportedStockRoutes", "absent"),
    ("stockRewards", "disabled_recommendation_only"),
    ("defaultsPosture", "absent_until_atomic_packet_accepted"),
)

ROBINHOOD_STOCK_ARTIFACT_BINDING = (
    ("contract", "GuardedErc20"),
    ("sourcePath", "contracts/vaults/GuardedErc20.vy"),
    ("sourceGitBlob", "713dab98bb9a08585e0c1f937425e8142cd600ab"),
    (
        "sourceSha256",
        "0fcdb02a0b3adf56ef0fd04397c57ac40325a37c87a32f29979dadc5eaf353ed",
    ),
    (
        "creationSha256",
        "64e42e5402343c3ffc8ac67b3ab92d90c9d79447e3323660de09aee5c6d30805",
    ),
    (
        "runtimeTemplateSha256",
        "e3dae3cc8bc64712d9d95adb24674f3c363e0df43d8eb853c6b430907d544a14",
    ),
    (
        "abiCanonicalSha256",
        "453d702567897a4ec89f9ea25502deac64c0d86f9700c597140e5c044f51740a",
    ),
    (
        "selectorsCanonicalSha256",
        "884259b81c166e48aff3cf2d424dcddf7a64eba157a58987521206dc617b1c2b",
    ),
    ("selectorCount", 34),
    ("runtimeTemplateSize", 10_524),
)

ROBINHOOD_STOCK_M4_BINDING = RobinhoodStockM4Binding(
    historical_tranche=RobinhoodHistoricalTrancheIdentity(
        integration_commit="a2d6b940c9b90d9ff1c78560ad61b2dd546f1760",
        changed_paths=(
            ("M", "tests/core/auctionHouse/test_ah_auctions.py"),
            (
                "A",
                "tests/core/auctionHouse/test_auctionhouse_stock_delivery.py",
            ),
            (
                "A",
                "tests/core/deleverage/test_deleverage_stock_delivery.py",
            ),
            (
                "M",
                "tests/core/deleverage/test_deleverage_swap_collateral.py",
            ),
        ),
    ),
    current_test_identities=(
        RobinhoodGitPathIdentity(
            "tests/core/auctionHouse/test_ah_auctions.py",
            "d45629865f93e22dae240c319d393aed04ac8e82",
            "ecda7d232bf17da43a511f9ac88d3a7ef58f3e4356e9b97edf9af44ab8a71d9a",
        ),
        RobinhoodGitPathIdentity(
            "tests/core/auctionHouse/test_auctionhouse_stock_delivery.py",
            "f19d5dcb1fcf7a6a37132ee1a0b0e02b3b70c3e7",
            "2a0be15fe4241562bee5b3157a1f98d17ba9306c7403314c2a7e514df96a9546",
        ),
        RobinhoodGitPathIdentity(
            "tests/core/deleverage/test_deleverage_stock_delivery.py",
            "d8a0d95317b45ac7a20016945a05f14ae3eead6d",
            "c74b1b0d8b22e5a064109c6f811b98010d40aa979600683d57d3d67e5a385d54",
        ),
        RobinhoodGitPathIdentity(
            "tests/core/deleverage/test_deleverage_swap_collateral.py",
            "bb0560048f91a89b7c413ff177360bb4ae0a759f",
            "3b900a98eb348fa5db94a0090974bb47c7cab3e5e86d951569a978b8181632b9",
        ),
    ),
    current_artifact_identities=(
        RobinhoodArtifactApplicabilityIdentity(
            "AuctionHouse",
            "contracts/core/AuctionHouse.vy",
            "48cbbbca22c87e490ef0f88aae4f643ab5b87987",
            "e5a1603d27e22abc3fa0bf98971dbc16732afe8647b1fe323916216036998921",
            "55c73a3c9f4a03b8fc1feb405e002b36e00ec1186ffb08398fee78d029a71609",
            "f91c53f0fbfe66b2f9e07003ba712cb976d6941a3b98ec0891918faa0bf6eead",
            "4f855ff6ea205cab84e204f4fa09964bcac958c632112c021b2c996e1f40b387",
            "9c6a8928074ec7e92b0220afabd8c0776986042c35d6d3e5088dabd2ff7c1762",
        ),
        RobinhoodArtifactApplicabilityIdentity(
            "Deleverage",
            "contracts/core/Deleverage.vy",
            "b43d373039b352d6eab240be714134764901b947",
            "d64a08573d1af100a8d6ca9d72811a87414654107fd09fe105322dde53a9c138",
            "cf8462f9489fda051d7e55bb1c52be38984538818ffd0d96338e5a4fade9638b",
            "baa883c99f91d41f7b3091090b246b415c77f5d7ffffebfd5e3366ab15366d57",
            "61fefe1ba573787eb65ab293da64922278e09b01619b4fa244ba36e961b73752",
            "5c6b9eccf45ba0b4be2fcf2c141616f0a8fcab3811bf3a3423a7dfab77b33490",
        ),
        RobinhoodArtifactApplicabilityIdentity(
            "GuardedErc20",
            "contracts/vaults/GuardedErc20.vy",
            "713dab98bb9a08585e0c1f937425e8142cd600ab",
            "0fcdb02a0b3adf56ef0fd04397c57ac40325a37c87a32f29979dadc5eaf353ed",
            "64e42e5402343c3ffc8ac67b3ab92d90c9d79447e3323660de09aee5c6d30805",
            "e3dae3cc8bc64712d9d95adb24674f3c363e0df43d8eb853c6b430907d544a14",
            "453d702567897a4ec89f9ea25502deac64c0d86f9700c597140e5c044f51740a",
            "884259b81c166e48aff3cf2d424dcddf7a64eba157a58987521206dc617b1c2b",
        ),
    ),
)

ROBINHOOD_STOCK_INPUT_QUALIFICATIONS = (
    RobinhoodStockInputQualification(
        "Deployment.DP-10.aapl.identity",
        "selected_external_fact_pending_current_verification",
        ROBINHOOD_AAPL_TOKEN_CANDIDATE,
        (
            "AAPL is the sole initial Stock symbol",
            "revalidate proxy implementation runtime controls and multiplier at freeze",
        ),
        ("B-T8-FREEZE", "B-P1-EXTERNAL-VERIFY"),
    ),
    RobinhoodStockInputQualification(
        "Deployment.DP-10.aapl.feed",
        "historical_candidate_pending_current_verification",
        ROBINHOOD_AAPL_FEED_CANDIDATE,
        (
            "prove feed proxy implementation runtime decimals and answer semantics",
            "bind an accepted freeze-time round under the 86400-second ceiling",
        ),
        ("B-T8-FREEZE", "B-ORACLE-FREEZE"),
    ),
    RobinhoodStockInputQualification(
        "Deployment.DP-10.aapl.decimals",
        "selected_external_fact_pending_current_verification",
        18,
        ("revalidate token decimals against the accepted current AAPL identity",),
        ("B-T8-FREEZE", "B-P1-EXTERNAL-VERIFY"),
    ),
    RobinhoodStockInputQualification(
        "Deployment.DP-10.aapl.P8",
        "freeze_time_input_unresolved",
        None,
        ("positive 8-decimal feed answer from the accepted freeze-time round",),
        ("B-T8-FREEZE", "B-ORACLE-FREEZE"),
    ),
    RobinhoodStockInputQualification(
        "Deployment.DP-10.aapl.perUserCap",
        "derived_cap_unresolved",
        None,
        (
            "target exposure is 5000 USD",
            "floor(5000 * 10^(18+8) / P8)",
        ),
        ("B-T8-FREEZE", "B-H04-PARAMS"),
    ),
    RobinhoodStockInputQualification(
        "Deployment.DP-10.aapl.globalCap",
        "derived_cap_unresolved",
        None,
        (
            "target exposure is 25000 USD",
            "floor(25000 * 10^(18+8) / P8)",
        ),
        ("B-T8-FREEZE", "B-H04-PARAMS"),
    ),
    RobinhoodStockInputQualification(
        "Deployment.DP-10.aapl.vault",
        "deployment_identity_unresolved",
        None,
        (
            "fresh deployment of the exact GuardedErc20 artifact binding",
            "exclusive AAPL assignment",
        ),
        ("B-T8-FREEZE", "B-H05-PLAN", "B-T8-M5"),
    ),
    RobinhoodStockInputQualification(
        "Deployment.DP-10.aapl.risk",
        "owner_risk_tuple_unresolved",
        None,
        (
            "exact deposit minimum and debt terms required",
            "no CreditEngine zero-backing or settlement redesign",
        ),
        ("B-H04-PARAMS", "B-T8-M5"),
    ),
    RobinhoodStockInputQualification(
        "Deployment.DP-10.aapl.auction",
        "policy_constrained_exact_values_unresolved",
        None,
        (
            "shouldSwapInStabPools=false",
            "shouldTransferToEndaoment=false",
            "shouldAuctionInstantly=true",
            "exact custom auction parameter tuple required",
        ),
        ("B-H04-PARAMS", "B-T8-M5"),
    ),
    RobinhoodStockInputQualification(
        "Deployment.DP-10.aapl.route",
        "policy_constrained_exact_values_unresolved",
        None,
        (
            "auction-only liquidation",
            "canRedeemCollateral=false",
            "unsupported Stock routes absent",
            "Stock rewards disabled as a recommendation without DP-15 changes",
        ),
        ("B-H04-PARAMS", "B-T8-M5"),
    ),
    RobinhoodStockInputQualification(
        "Deployment.DP-11.stock.vaultArtifact",
        "repository_fact_integrated",
        ROBINHOOD_STOCK_ARTIFACT_BINDING,
        (
            "canonical selectors and persistent transient and immutable layouts match SimpleErc20",
        ),
        (),
    ),
    RobinhoodStockInputQualification(
        "Deployment.DP-11.stock.vaultSlot",
        "owner_slot_unresolved",
        None,
        ("exact fresh VaultBook id and semantic name required",),
        ("B-H05-PLAN", "B-T8-M5"),
    ),
    RobinhoodStockInputQualification(
        "Deployment.DP-11.stock.m2Movement",
        "repository_fact_integrated",
        (
            ("source", "contracts/vaults/GuardedErc20.vy"),
            ("gitBlob", "713dab98bb9a08585e0c1f937425e8142cd600ab"),
            ("integrationCommit", "4f887207d344a1513d6c3a79d315c8315a10a9c8"),
        ),
        ("preserve nominal internal movement and backing-aware external delivery",),
        (),
    ),
    RobinhoodStockInputQualification(
        "Deployment.DP-11.stock.m3CreditContainment",
        "repository_fact_integrated",
        (
            ("source", "contracts/core/CreditEngine.vy"),
            ("gitBlob", "a98d2522a16708e887a5a8aad78171843d413baf"),
            ("integrationCommit", "4c26d7d73bb02f7eae2e5df02314db77a426aced"),
        ),
        ("preserve represented zero-amount terms with zero capacity",),
        (),
    ),
    RobinhoodStockInputQualification(
        "Deployment.DP-11.stock.m4ComposedProof",
        "repository_fact_integrated",
        ROBINHOOD_STOCK_M4_BINDING,
        (
            "historical tranche identity is distinct from current applicability",
            "current applicability is pinned to exact test and production/artifact identities",
            "composed proof does not authorize configuration deployment or activation",
        ),
        (),
    ),
    RobinhoodStockInputQualification(
        "Deployment.DP-11.stock.m5ActivationBinding",
        "atomic_binding_unresolved",
        None,
        (
            "one reviewed packet must bind all 16 inputs and exact configuration bytes",
            "negative reachability must remain true before packet acceptance",
        ),
        ("B-T8-M5", "B-H08-PROOF", "B-H09-RELEASE"),
    ),
)

ROBINHOOD_STOCK_LAUNCH_INPUT_PATHS = tuple(
    item.path for item in ROBINHOOD_STOCK_INPUT_QUALIFICATIONS
)
ROBINHOOD_STOCK_RESOLVED_REPOSITORY_FACT_PATHS = tuple(
    item.path
    for item in ROBINHOOD_STOCK_INPUT_QUALIFICATIONS
    if item.resolution == "repository_fact_integrated"
)
ROBINHOOD_STOCK_UNRESOLVED_INPUT_PATHS = tuple(
    item.path
    for item in ROBINHOOD_STOCK_INPUT_QUALIFICATIONS
    if item.resolution != "repository_fact_integrated"
)

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
    'Deployment.DP-15.rewards.promotion': RobinhoodInput('7395a0bff4abd75e11f832fbd0dee2f6569244dafa2ba52604d3f5989662acec', 'approved'),
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
    # 100 GREEN at construction, matching Base. The launch graph creates a
    # GREEN/USDG Curve pool and DefaultsRobinhood expects GREEN to resolve
    # through Curve at price-desk id 2, so the pool must be seedable -- and
    # GREEN cannot be minted any other way at deploy time, since minting needs
    # a department with canMintGreen and the deployer holds governance, not
    # mint capability. A zero here contradicts the pool actions in 0400.
    #
    # NOTE: this changes a value the H-04 register recorded as approved at zero.
    # It needs its own approval; the register entry should be updated alongside.
    'Deployment.DP-19.supply.GREEN.amount': RobinhoodInput(100 * 10**18, 'approved'),
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

@dataclass(frozen=True)
class RobinhoodCurveLaunchInput:
    input_id: str
    value: Any
    authority_class: str
    primary_owner: str
    provenance: str
    resolution_state: str


ROBINHOOD_CURVE_ADDRESS_PROVIDER = "0x4574921eb950d3Fd5B01562162EC566Cb8bc3648"
ROBINHOOD_CURVE_META_REGISTRY = "0xe6dA14500f0b5783E2325F9C5a7eE5d99DA0fB42"
ROBINHOOD_CURVE_TRICRYPTO_NG_FACTORY = "0x6E28493348446503db04A49621d8e6C9A40015FB"
ROBINHOOD_CURVE_STABLESWAP_NG_FACTORY = "0x8271e06E5887FE5ba05234f5315c19f3Ec90E8aD"
ROBINHOOD_CURVE_TWOCRYPTO_NG_FACTORY = "0xe7FBd704B938cB8fe26313C3464D4b7B7348c88C"

ROBINHOOD_ADDRESSES.update(
    {
        # Official repository candidates; live identities remain blockers.
        "CURVE_ADDRESS_PROVIDER": ROBINHOOD_CURVE_ADDRESS_PROVIDER,
        "CURVE_META_REGISTRY": ROBINHOOD_CURVE_META_REGISTRY,
        "CURVE_TRICRYPTO_NG_FACTORY": ROBINHOOD_CURVE_TRICRYPTO_NG_FACTORY,
        "CURVE_STABLESWAP_NG_FACTORY": ROBINHOOD_CURVE_STABLESWAP_NG_FACTORY,
        "CURVE_TWOCRYPTO_NG_FACTORY": ROBINHOOD_CURVE_TWOCRYPTO_NG_FACTORY,
        # CREATE output: observed during deployment, never precomputed.
        "GREEN_USDG_CURVE_POOL": SymbolicBinding("GREEN_USDG_CURVE_POOL"),
    }
)
ROBINHOOD_ADDRESS_STATUS.update(
    {
        "CURVE_ADDRESS_PROVIDER": "selected_external_fact_unverified",
        "CURVE_META_REGISTRY": "selected_external_fact_unverified",
        "CURVE_TRICRYPTO_NG_FACTORY": "selected_external_fact_unverified",
        "CURVE_STABLESWAP_NG_FACTORY": "selected_external_fact_unverified",
        "CURVE_TWOCRYPTO_NG_FACTORY": "selected_external_fact_unverified",
        "GREEN_USDG_CURVE_POOL": "deployment_produced_unresolved",
    }
)
ROBINHOOD_COMPONENTS["curve_launch"] = {
    "component_id": "CM-017",
    "registry_id": 2,
    "configured_assets": ("GREEN",),
    "priority_ids": (1, 3),
}

# Bounded Curve launch authority. Every row is either an approved repository
# invariant, an independently checked official-repository candidate that still
# needs a live identity observation, an owner decision, or a deployment output.
# No row below authorizes deployment, pool funding, or any higher Curve power.
ROBINHOOD_CURVE_OFFICIAL_PROVENANCE = (
    "curvefi/curve-core@6222dda9959091db94d61f6d6378234a624cdd66:"
    "deployments/prod/robinhood.yaml"
)
ROBINHOOD_CURVE_LITE_PROVENANCE = (
    "curvefi/curve-lite@5a9e1ab34c1319de69b987900d859ad2e965d0e2:"
    "contracts/amm/stableswap/factory/factory_v_100.vy"
)
# Owner-selected, mirroring Base's "GREEN/USDC Pool" / "GREEN/USDC". These are
# written into the deployed Curve pool and cannot be changed afterwards.
ROBINHOOD_CURVE_POOL_NAME = "GREEN/USDG Pool"
ROBINHOOD_CURVE_POOL_SYMBOL = "GREEN/USDG"

ROBINHOOD_CURVE_LAUNCH_INPUTS = (
    RobinhoodCurveLaunchInput(
        "launch.chain_id", 4663, "repository_approved", "protocol_owner",
        "config/network_profiles.py", "resolved_repository_fact",
    ),
    RobinhoodCurveLaunchInput(
        "launch.component", "CM-017:CurvePrices", "repository_approved", "oracle_owner",
        "ROBINHOOD_COMPONENT_SELECTIONS", "selected_launch",
    ),
    RobinhoodCurveLaunchInput(
        "launch.price_desk_registration_order",
        ((1, "ChainlinkPrices"), (2, "CurvePrices"), (3, "BlueChipYieldPrices")),
        "repository_approved", "migration_owner", "ROBINHOOD_REGISTRY_TOPOLOGY",
        "selected_launch",
    ),
    RobinhoodCurveLaunchInput(
        "launch.priority_price_source_ids", (1, 3), "repository_approved", "oracle_owner",
        "contracts/config/DefaultsRobinhood.vy", "resolved_repository_fact",
    ),
    RobinhoodCurveLaunchInput(
        "curve.address_provider", ROBINHOOD_ADDRESSES["CURVE_ADDRESS_PROVIDER"],
        "externally_verifiable_canonical_fact", "oracle_owner",
        ROBINHOOD_CURVE_OFFICIAL_PROVENANCE, "selected_external_fact_unverified",
    ),
    RobinhoodCurveLaunchInput(
        "curve.address_provider_binding_7",
        (7, "MetaRegistry", ROBINHOOD_ADDRESSES["CURVE_META_REGISTRY"]),
        "externally_verifiable_canonical_fact", "oracle_owner",
        ROBINHOOD_CURVE_OFFICIAL_PROVENANCE, "selected_external_fact_unverified",
    ),
    RobinhoodCurveLaunchInput(
        "curve.address_provider_binding_11",
        (11, "TricryptoNG", ROBINHOOD_ADDRESSES["CURVE_TRICRYPTO_NG_FACTORY"]),
        "externally_verifiable_canonical_fact", "oracle_owner",
        ROBINHOOD_CURVE_OFFICIAL_PROVENANCE, "selected_external_fact_unverified",
    ),
    RobinhoodCurveLaunchInput(
        "curve.address_provider_binding_12",
        (12, "StableSwapNG", ROBINHOOD_ADDRESSES["CURVE_STABLESWAP_NG_FACTORY"]),
        "externally_verifiable_canonical_fact", "oracle_owner",
        ROBINHOOD_CURVE_OFFICIAL_PROVENANCE, "selected_external_fact_unverified",
    ),
    RobinhoodCurveLaunchInput(
        "curve.address_provider_binding_13",
        (13, "TwoCryptoNG", ROBINHOOD_ADDRESSES["CURVE_TWOCRYPTO_NG_FACTORY"]),
        "externally_verifiable_canonical_fact", "oracle_owner",
        ROBINHOOD_CURVE_OFFICIAL_PROVENANCE, "selected_external_fact_unverified",
    ),
    RobinhoodCurveLaunchInput(
        "curve.constructor_bindings",
        (
            ("_ripeHq", "deployment:RIPE_HQ"),
            ("_tempGov", "owner:GOVERNANCE"),
            ("_curveAddressProvider", "CURVE_ADDRESS_PROVIDER"),
            ("_green", "GREEN_TOKEN"),
            ("_savingsGreen", "SGREEN_TOKEN"),
            ("_minPriceChangeTimeLock", "Defaults:price source minimum"),
            ("_maxPriceChangeTimeLock", "Defaults:price source maximum"),
        ),
        "repository_approved", "migration_owner", "contracts/priceSources/CurvePrices.vy",
        "resolved_repository_fact",
    ),
    RobinhoodCurveLaunchInput(
        "pool.factory", ROBINHOOD_ADDRESSES["CURVE_STABLESWAP_NG_FACTORY"],
        "externally_verifiable_canonical_fact", "oracle_owner",
        ROBINHOOD_CURVE_OFFICIAL_PROVENANCE, "resolved_reference_to_unverified_binding",
    ),
    RobinhoodCurveLaunchInput(
        "pool.factory_method", "deploy_plain_pool/create_from_blueprint/CREATE",
        "repository_approved", "migration_owner", ROBINHOOD_CURVE_LITE_PROVENANCE,
        "resolved_repository_fact",
    ),
    RobinhoodCurveLaunchInput(
        "pool.name", ROBINHOOD_CURVE_POOL_NAME, "owner_selected", "protocol_owner",
        "matches approved Base GREEN pool deployment (CURVE_PARAMS[base])", "resolved_repository_fact",
    ),
    RobinhoodCurveLaunchInput(
        "pool.symbol", ROBINHOOD_CURVE_POOL_SYMBOL, "owner_selected", "protocol_owner",
        "matches approved Base GREEN pool deployment (CURVE_PARAMS[base])", "resolved_repository_fact",
    ),
    RobinhoodCurveLaunchInput(
        "pool.coin_order", ("USDG", "GREEN"), "owner_selected", "oracle_owner",
        "matches approved Base GREEN pool deployment (CURVE_PARAMS[base])", "resolved_repository_fact",
    ),
    RobinhoodCurveLaunchInput(
        "pool.coin_decimals", (6, 18), "owner_selected", "oracle_owner",
        "matches approved Base GREEN pool deployment (CURVE_PARAMS[base])",
        "resolved_repository_fact",
    ),
    RobinhoodCurveLaunchInput(
        "pool.A", 100, "owner_selected", "liquidity_owner",
        "matches approved Base GREEN pool deployment (CURVE_PARAMS[base])", "resolved_repository_fact",
    ),
    RobinhoodCurveLaunchInput(
        "pool.fee", 4_000_000, "owner_selected", "liquidity_owner",
        "matches approved Base GREEN pool deployment (CURVE_PARAMS[base])", "resolved_repository_fact",
    ),
    RobinhoodCurveLaunchInput(
        "pool.offpeg_fee_multiplier", 20_000_000_000, "owner_selected", "liquidity_owner",
        "matches approved Base GREEN pool deployment (CURVE_PARAMS[base])", "resolved_repository_fact",
    ),
    RobinhoodCurveLaunchInput(
        "pool.ma_exp_time", 600, "owner_selected", "liquidity_owner",
        "matches approved Base GREEN pool deployment (CURVE_PARAMS[base])", "resolved_repository_fact",
    ),
    RobinhoodCurveLaunchInput(
        "pool.ma_exp_time_alternative_test_vector", 866, "repository_approved", "oracle_owner",
        ROBINHOOD_CURVE_LITE_PROVENANCE, "test_vector_only",
    ),
    RobinhoodCurveLaunchInput(
        "pool.address", ROBINHOOD_ADDRESSES["GREEN_USDG_CURVE_POOL"],
        "deployment_produced", "migration_owner", ROBINHOOD_CURVE_LITE_PROVENANCE,
        "deployment_produced_unresolved",
    ),
    RobinhoodCurveLaunchInput(
        "pool.factory_nonce_or_order", "not_precomputed; record returned deployment address",
        "deployment_produced", "migration_owner", ROBINHOOD_CURVE_LITE_PROVENANCE,
        "resolved_no_predeployment_value",
    ),
    RobinhoodCurveLaunchInput(
        # (USDG, GREEN) in the pool coin order. 100 USDG at 6 decimals and 100
        # GREEN at 18, the same seed Base used.
        "pool.production_liquidity_amount", (100 * 10**6, 100 * 10**18),
        "owner_selected", "liquidity_owner", "mirrors Base 2001_CurvePools.py seed", "resolved_repository_fact",
    ),
    RobinhoodCurveLaunchInput(
        # The deployer, which must already hold the USDG. GREEN comes from the
        # 100 minted to it at construction (DP-19).
        "pool.funding_source", "temporary-local-governance",
        "owner_selected", "liquidity_owner", "mirrors Base 2001_CurvePools.py seed", "resolved_repository_fact",
    ),
    RobinhoodCurveLaunchInput(
        # EndaomentFunds holds the LP. Base sent it to the Endaoment, but
        # local custody moved to the dedicated EndaomentFunds department
        # (RipeHq id 21) since then.
        "pool.custodian", "ENDAOMENT_FUNDS",
        "owner_selected", "security_owner", "mirrors Base 2001_CurvePools.py seed", "resolved_repository_fact",
    ),
    RobinhoodCurveLaunchInput(
        "pool.approving_account", "temporary-local-governance",
        "owner_selected", "security_owner", "mirrors Base 2001_CurvePools.py seed", "resolved_repository_fact",
    ),
    RobinhoodCurveLaunchInput(
        # Seeding 100 USDG (6dp) + 100 GREEN (18dp) into an empty StableSwap-NG
        # pool mints LP equal to the invariant D, so ~200e18 at a 1:1 peg. 199e18
        # is a ~0.5% floor: enough to absorb rounding and a small peg deviation,
        # tight enough to abort if the pool is not what we think it is.
        # Base passed 0; this is deliberately stricter.
        "pool.minimum_minted_lp", 199 * 10**18,
        "owner_selected", "liquidity_owner", "mirrors Base 2001_CurvePools.py seed", "resolved_repository_fact",
    ),
    RobinhoodCurveLaunchInput(
        "pool.slippage_limit", SymbolicBinding("GREEN_USDG_SLIPPAGE_LIMIT"),
        "owner_selected", "liquidity_owner", "owner launch input", "owner_choice_unresolved",
    ),
    RobinhoodCurveLaunchInput(
        "pool.withdrawal_authority", SymbolicBinding("GREEN_USDG_WITHDRAWAL_AUTHORITY"),
        "owner_selected", "security_owner", "owner launch input", "owner_choice_unresolved",
    ),
    RobinhoodCurveLaunchInput(
        "pool.minimum_retained_liquidity", SymbolicBinding("GREEN_USDG_MIN_RETAINED_LIQUIDITY"),
        "owner_selected", "liquidity_owner", "owner launch input", "owner_choice_unresolved",
    ),
    RobinhoodCurveLaunchInput(
        "pool.production_observation", SymbolicBinding("GREEN_USDG_PRODUCTION_OBSERVATION"),
        "externally_verifiable_canonical_fact", "oracle_owner", "post-deployment observation",
        "external_observation_unverified",
    ),
    RobinhoodCurveLaunchInput(
        "feed.route", ("GREEN", "Curve:GREEN/USDG", "PriceDesk", "Chainlink:USDG/USD"),
        "repository_approved", "oracle_owner", "bounded launch architecture", "selected_launch",
    ),
    RobinhoodCurveLaunchInput(
        "feed.curve_assets", ("GREEN",), "repository_approved", "oracle_owner",
        "bounded launch architecture", "selected_launch",
    ),
    RobinhoodCurveLaunchInput(
        "feed.usdg_curve_feed", False, "repository_approved", "oracle_owner",
        "anti-recursion invariant", "explicitly_inactive",
    ),
    RobinhoodCurveLaunchInput(
        "feed.usdg_authority", "ChainlinkPrices only", "repository_approved", "oracle_owner",
        "anti-recursion invariant", "selected_launch",
    ),
    RobinhoodCurveLaunchInput(
        "inactive.capabilities",
        (
            "GREEN_USDG_LP_COLLATERAL", "RIPE_WETH_LP_COLLATERAL", "CURVE_LP_VALUATION",
            "PSM_CURVE_AUTHORITY", "CURVE_DYNAMIC_RATES", "GREEN_REFERENCE_SNAPSHOTS",
            "ENDAOMENT_CURVE_STABILIZATION", "STOCK_PRICING", "UNISWAP_ACCOUNTING",
        ),
        "repository_approved", "protocol_owner", "bounded launch architecture", "explicitly_inactive",
    ),
    RobinhoodCurveLaunchInput(
        "artifact.curve_prices_source_sha256",
        "f6e8234be8e433ed344f6f61d9cf04d20a4327c773759bb6aced44b9f65ebd0c",
        "repository_approved", "oracle_owner", "contracts/priceSources/CurvePrices.vy",
        "source_frozen",
    ),
    RobinhoodCurveLaunchInput(
        "artifact.curve_prices_abi_sha256",
        "3f06fa5c83f4404bfb97da689ea3b4611e94c60a504174001210033c7c429772",
        "repository_approved", "oracle_owner", "scripts/abis/CurvePrices.json", "source_frozen",
    ),
)

# Immutable metadata projection used by the structural validator. The rows
# above remain the sole value/metadata authority; this snapshot lets validators
# reject in-memory provenance, owner, authority-class, or state substitution
# without duplicating those values in another module.
ROBINHOOD_CURVE_LAUNCH_METADATA = tuple(
    (
        row.input_id,
        row.authority_class,
        row.primary_owner,
        row.provenance,
        row.resolution_state,
    )
    for row in ROBINHOOD_CURVE_LAUNCH_INPUTS
)

ROBINHOOD_CURVE_AUTHORITY_CLASSES = frozenset(
    {"repository_approved", "externally_verifiable_canonical_fact", "owner_selected", "deployment_produced"}
)
ROBINHOOD_CURVE_RESOLUTION_STATES = frozenset(
    {
        "resolved_repository_fact", "selected_launch", "selected_external_fact_unverified",
        "research_candidate_owner_approval_unresolved", "test_vector_only",
        "deployment_produced_unresolved", "resolved_no_predeployment_value",
        "resolved_reference_to_unverified_binding",
        "owner_choice_unresolved", "external_observation_unverified", "explicitly_inactive",
        "source_frozen",
    }
)
ROBINHOOD_CURVE_BLOCKING_STATES = frozenset(
    {
        "selected_external_fact_unverified", "research_candidate_owner_approval_unresolved",
        "deployment_produced_unresolved", "owner_choice_unresolved",
        "external_observation_unverified",
    }
)



def validate_robinhood_stock_launch_qualification(
    qualifications: tuple[RobinhoodStockInputQualification, ...] = (
        ROBINHOOD_STOCK_INPUT_QUALIFICATIONS
    ),
) -> None:
    expected_paths = (
        "Deployment.DP-10.aapl.identity",
        "Deployment.DP-10.aapl.feed",
        "Deployment.DP-10.aapl.decimals",
        "Deployment.DP-10.aapl.P8",
        "Deployment.DP-10.aapl.perUserCap",
        "Deployment.DP-10.aapl.globalCap",
        "Deployment.DP-10.aapl.vault",
        "Deployment.DP-10.aapl.risk",
        "Deployment.DP-10.aapl.auction",
        "Deployment.DP-10.aapl.route",
        "Deployment.DP-11.stock.vaultArtifact",
        "Deployment.DP-11.stock.vaultSlot",
        "Deployment.DP-11.stock.m2Movement",
        "Deployment.DP-11.stock.m3CreditContainment",
        "Deployment.DP-11.stock.m4ComposedProof",
        "Deployment.DP-11.stock.m5ActivationBinding",
    )
    paths = tuple(item.path for item in qualifications)
    if paths != expected_paths or len(paths) != len(set(paths)):
        raise ValueError("RH_STOCK_INPUT_CENSUS")
    if any(path not in ROBINHOOD_DEPLOYMENT_INPUTS for path in paths):
        raise ValueError("RH_STOCK_INPUT_AUTHORITY")
    if any(
        not isinstance(ROBINHOOD_DEPLOYMENT_INPUTS[path].value, SymbolicBinding)
        or ROBINHOOD_DEPLOYMENT_INPUTS[path].disposition != "blocked"
        for path in paths
    ):
        raise ValueError("RH_STOCK_PREMATURE_BINDING")
    if ROBINHOOD_INITIAL_STOCK_SYMBOLS != ("AAPL",):
        raise ValueError("RH_STOCK_SYMBOL_SCOPE")
    if dict(ROBINHOOD_STOCK_ACTIVATION_POLICY) != {
        "vault": "GuardedErc20",
        "exclusiveVaultAssignment": True,
        "shouldSwapInStabPools": False,
        "shouldTransferToEndaoment": False,
        "shouldAuctionInstantly": True,
        "canRedeemCollateral": False,
        "unsupportedStockRoutes": "absent",
        "stockRewards": "disabled_recommendation_only",
        "defaultsPosture": "absent_until_atomic_packet_accepted",
    }:
        raise ValueError("RH_STOCK_POLICY")
    if ROBINHOOD_ASSERTION_INVARIANTS["stock_enabled_vaults"] != (
        "GuardedErc20",
    ):
        raise ValueError("RH_STOCK_VAULT_SELECTION")
    if ROBINHOOD_ASSERTION_INVARIANTS[
        "stock_excluded_from_stability_pool"
    ] is not True:
        raise ValueError("RH_STOCK_STABILITY_EXCLUSION")
    if tuple(
        item.path
        for item in qualifications
        if item.resolution == "repository_fact_integrated"
    ) != (
        "Deployment.DP-11.stock.vaultArtifact",
        "Deployment.DP-11.stock.m2Movement",
        "Deployment.DP-11.stock.m3CreditContainment",
        "Deployment.DP-11.stock.m4ComposedProof",
    ):
        raise ValueError("RH_STOCK_REPOSITORY_FACT_SET")
    if any(
        item.resolution != "repository_fact_integrated"
        and not item.blocker_ids
        for item in qualifications
    ):
        raise ValueError("RH_STOCK_UNTYPED_BLOCKER")
    if any(
        item.resolution == "repository_fact_integrated" and item.blocker_ids
        for item in qualifications
    ):
        raise ValueError("RH_STOCK_RESOLVED_BLOCKER")
    m4_candidate = next(
        item.candidate
        for item in qualifications
        if item.path == "Deployment.DP-11.stock.m4ComposedProof"
    )
    if not isinstance(m4_candidate, RobinhoodStockM4Binding):
        raise ValueError("RH_STOCK_M4_BINDING_SHAPE")


def validate_robinhood_stock_m4_binding(
    repository_root: Path | str,
    binding: RobinhoodStockM4Binding = ROBINHOOD_STOCK_M4_BINDING,
) -> None:
    """Validate historical M4 identity and its separate current applicability."""

    if not isinstance(binding, RobinhoodStockM4Binding):
        raise ValueError("RH_STOCK_M4_BINDING_SHAPE")

    root = Path(repository_root).resolve()

    def git(*args: str) -> bytes:
        result = subprocess.run(
            ["/usr/bin/git", "-C", str(root), *args],
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise ValueError("RH_STOCK_M4_GIT")
        return result.stdout

    expected_commit = "a2d6b940c9b90d9ff1c78560ad61b2dd546f1760"
    expected_changed_paths = (
        ("M", "tests/core/auctionHouse/test_ah_auctions.py"),
        (
            "A",
            "tests/core/auctionHouse/test_auctionhouse_stock_delivery.py",
        ),
        (
            "A",
            "tests/core/deleverage/test_deleverage_stock_delivery.py",
        ),
        (
            "M",
            "tests/core/deleverage/test_deleverage_swap_collateral.py",
        ),
    )
    historical = binding.historical_tranche
    if historical.integration_commit != expected_commit:
        raise ValueError("RH_STOCK_M4_COMMIT")

    ancestry = subprocess.run(
        [
            "/usr/bin/git",
            "-C",
            str(root),
            "merge-base",
            "--is-ancestor",
            expected_commit,
            "HEAD",
        ],
        capture_output=True,
        check=False,
    )
    if ancestry.returncode != 0:
        raise ValueError("RH_STOCK_M4_NON_ANCESTOR")

    commit_with_parents = git(
        "rev-list", "--parents", "-n", "1", expected_commit
    ).decode().split()
    if len(commit_with_parents) != 2:
        raise ValueError("RH_STOCK_M4_PARENT_CENSUS")
    parent = commit_with_parents[1]
    changed_path_lines = git(
        "diff-tree",
        "--no-commit-id",
        "--name-status",
        "-r",
        "--no-renames",
        parent,
        expected_commit,
        "--",
    ).decode().splitlines()
    try:
        derived_changed_paths = tuple(
            tuple(line.split("\t", 1)) for line in changed_path_lines
        )
    except ValueError as error:
        raise ValueError("RH_STOCK_M4_HISTORICAL_PATH_CENSUS") from error
    if any(len(item) != 2 for item in derived_changed_paths):
        raise ValueError("RH_STOCK_M4_HISTORICAL_PATH_CENSUS")
    if (
        historical.changed_paths != expected_changed_paths
        or derived_changed_paths != expected_changed_paths
        or historical.changed_paths != derived_changed_paths
    ):
        raise ValueError("RH_STOCK_M4_HISTORICAL_PATH_CENSUS")

    expected_test_paths = tuple(path for _, path in expected_changed_paths)
    test_identities = binding.current_test_identities
    if tuple(item.path for item in test_identities) != expected_test_paths:
        raise ValueError("RH_STOCK_M4_TEST_IDENTITY_CENSUS")
    for identity in test_identities:
        baseline_bytes = git("cat-file", "blob", f"HEAD:{identity.path}")
        baseline_blob = git("rev-parse", f"HEAD:{identity.path}").decode().strip()
        if identity.git_blob != baseline_blob:
            raise ValueError("RH_STOCK_M4_TEST_BLOB")
        if identity.sha256 != hashlib.sha256(baseline_bytes).hexdigest():
            raise ValueError("RH_STOCK_M4_TEST_SHA256")
        try:
            working_bytes = (root / identity.path).read_bytes()
        except OSError as error:
            raise ValueError("RH_STOCK_M4_TEST_WORKTREE_DRIFT") from error
        if working_bytes != baseline_bytes:
            raise ValueError("RH_STOCK_M4_TEST_WORKTREE_DRIFT")

    expected_artifacts = (
        ("AuctionHouse", "contracts/core/AuctionHouse.vy"),
        ("Deleverage", "contracts/core/Deleverage.vy"),
        ("GuardedErc20", "contracts/vaults/GuardedErc20.vy"),
    )
    artifact_identities = binding.current_artifact_identities
    if tuple(
        (item.contract, item.source_path) for item in artifact_identities
    ) != expected_artifacts:
        raise ValueError("RH_STOCK_M4_ARTIFACT_IDENTITY_CENSUS")

    expectations_path = "config/contract-artifact-expectations.json"
    expectations_bytes = git("cat-file", "blob", f"HEAD:{expectations_path}")
    try:
        if (root / expectations_path).read_bytes() != expectations_bytes:
            raise ValueError("RH_STOCK_M4_ARTIFACT_FILE_DRIFT")
        expectations = json.loads(expectations_bytes)["contracts"]
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise ValueError("RH_STOCK_M4_ARTIFACT_FILE_DRIFT") from error

    for identity in artifact_identities:
        baseline_bytes = git("cat-file", "blob", f"HEAD:{identity.source_path}")
        baseline_blob = git(
            "rev-parse", f"HEAD:{identity.source_path}"
        ).decode().strip()
        if identity.source_git_blob != baseline_blob:
            raise ValueError("RH_STOCK_M4_SOURCE_BLOB")
        if identity.source_sha256 != hashlib.sha256(baseline_bytes).hexdigest():
            raise ValueError("RH_STOCK_M4_SOURCE_SHA256")
        try:
            working_bytes = (root / identity.source_path).read_bytes()
        except OSError as error:
            raise ValueError("RH_STOCK_M4_SOURCE_WORKTREE_DRIFT") from error
        if working_bytes != baseline_bytes:
            raise ValueError("RH_STOCK_M4_SOURCE_WORKTREE_DRIFT")

        try:
            canonical = expectations[identity.contract]
            canonical_identity = (
                canonical["source_path"],
                canonical["source_git_blob"],
                canonical["source_sha256"],
                canonical["artifacts"]["creation_sha256"],
                canonical["artifacts"]["runtime_template_sha256"],
                canonical["abi"]["canonical_sha256"],
                canonical["selectors"]["canonical_sha256"],
            )
        except (KeyError, TypeError) as error:
            raise ValueError("RH_STOCK_M4_ARTIFACT_EXPECTATION") from error
        bound_identity = (
            identity.source_path,
            identity.source_git_blob,
            identity.source_sha256,
            identity.creation_sha256,
            identity.runtime_template_sha256,
            identity.abi_canonical_sha256,
            identity.selectors_canonical_sha256,
        )
        if bound_identity != canonical_identity:
            raise ValueError("RH_STOCK_M4_ARTIFACT_EXPECTATION")


def robinhood_stock_launch_readiness() -> tuple[bool, tuple[str, ...]]:
    validate_robinhood_stock_launch_qualification()
    blockers = tuple(
        f"input:{item.path}:{item.resolution}"
        for item in ROBINHOOD_STOCK_INPUT_QUALIFICATIONS
        if item.resolution != "repository_fact_integrated"
    )
    return False, (*blockers, "activation:atomic_packet_unaccepted")


validate_robinhood_stock_launch_qualification()

# DeployArgs indexes all five legacy dictionaries. Robinhood exposes only the
# bounded GREEN/USDG Curve candidate here; unresolved owner choices and the
# deployment-produced pool address remain fail-closed in the authority rows.
ADDYS["robinhood"] = ROBINHOOD_ADDRESSES
PARAMS["robinhood"] = {
    "DEPLOYMENT_INPUTS": ROBINHOOD_DEPLOYMENT_INPUTS,
    "CHAIN": ROBINHOOD_CHAIN,
    "COMPONENTS": ROBINHOOD_COMPONENTS,
}
_ROBINHOOD_CURVE_VALUES = {
    row.input_id: row.value for row in ROBINHOOD_CURVE_LAUNCH_INPUTS
}
CURVE_PARAMS["robinhood"] = {
    "GREEN_POOL_NAME": _ROBINHOOD_CURVE_VALUES["pool.name"],
    "GREEN_POOL_SYMBOL": _ROBINHOOD_CURVE_VALUES["pool.symbol"],
    "GREEN_POOL_COINS": (
        ROBINHOOD_ADDRESSES["USDG"],
        ROBINHOOD_ADDRESSES["GREEN_TOKEN"],
    ),
    "GREEN_POOL_COIN_DECIMALS": _ROBINHOOD_CURVE_VALUES["pool.coin_decimals"],
    "GREEN_POOL_A": _ROBINHOOD_CURVE_VALUES["pool.A"],
    "GREEN_POOL_FEE": _ROBINHOOD_CURVE_VALUES["pool.fee"],
    "GREEN_POOL_OFFPEG_MULTIPLIER": _ROBINHOOD_CURVE_VALUES[
        "pool.offpeg_fee_multiplier"
    ],
    "GREEN_POOL_MA_EXP_TIME": _ROBINHOOD_CURVE_VALUES["pool.ma_exp_time"],
    "GREEN_POOL_MA_EXP_TIME_ALTERNATIVE_TEST_VECTOR": _ROBINHOOD_CURVE_VALUES[
        "pool.ma_exp_time_alternative_test_vector"
    ],
    "GREEN_POOL_ADDRESS": _ROBINHOOD_CURVE_VALUES["pool.address"],
}
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
