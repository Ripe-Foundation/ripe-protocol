"""Launch values for Robinhood, in one place.

Every number and address the Robinhood migrations need, with the reason it has
that value. Approved values are read from `config/BluePrint.py` so there is one
source of truth; the rest are decisions recorded here with their rationale.

Lives in config/ because migration directories have hyphens in their names and
are therefore not importable packages -- the same reason Base's migrations
import their values from config/ and scripts/.
"""

import os

from config.BluePrint import ROBINHOOD_ADDRESSES, ROBINHOOD_GOVERNANCE

ZERO_ADDRESS = "0x" + "0" * 40


def address(key):
    """Read a verified external address from the blueprint."""
    return ROBINHOOD_ADDRESSES[key]


# --- block units ------------------------------------------------------------
# Same constants as contracts/config/DefaultsRobinhood.vy. BLOCKS_PER_MINUTE is
# 5 because on this Arbitrum L2 `block.number` is the L1 ancestor estimate,
# advancing about every 12 seconds -- not the child block height.
BLOCKS_PER_MINUTE = 5
HOUR_IN_BLOCKS = 60 * BLOCKS_PER_MINUTE
DAY_IN_BLOCKS = 24 * HOUR_IN_BLOCKS
WEEK_IN_BLOCKS = 7 * DAY_IN_BLOCKS

# --- timelocks (blocks) -----------------------------------------------------
TOKEN_HQ_MIN_TIMELOCK = DAY_IN_BLOCKS
TOKEN_HQ_MAX_TIMELOCK = WEEK_IN_BLOCKS
LOCAL_GOV_MIN_TIMELOCK = DAY_IN_BLOCKS
LOCAL_GOV_MAX_TIMELOCK = WEEK_IN_BLOCKS
RIPE_HQ_MIN_TIMELOCK = HOUR_IN_BLOCKS * 12
RIPE_HQ_MAX_TIMELOCK = WEEK_IN_BLOCKS
REGISTRY_MIN_DELAY = HOUR_IN_BLOCKS * 12
REGISTRY_MAX_DELAY = WEEK_IN_BLOCKS
PRICE_MIN_TIMELOCK = HOUR_IN_BLOCKS * 2
PRICE_MAX_TIMELOCK = WEEK_IN_BLOCKS
# All five switchboards share one band.
SWITCHBOARD_MIN_TIMELOCK = HOUR_IN_BLOCKS * 2
SWITCHBOARD_MAX_TIMELOCK = WEEK_IN_BLOCKS
HR_MIN_TIMELOCK = DAY_IN_BLOCKS
HR_MAX_TIMELOCK = WEEK_IN_BLOCKS

# --- stale windows (SECONDS, not blocks) ------------------------------------
# Deliberately plain integers: these are wall-clock seconds passed to price
# feeds. Writing DAY_IN_BLOCKS here would make every staleness check 12x tighter.
STALE_WINDOW_MIN = 300  # 5 minutes
STALE_WINDOW_MAX = 604_800  # 7 days
STALE_WINDOW_DEFAULT = 86_400  # 1 day
STALE_WINDOW_USDG = 86_400  # 1 day

# --- initial supply ---------------------------------------------------------
GREEN_INITIAL_SUPPLY = 100 * 10**18  # to the deployer, which seeds the pool
RIPE_INITIAL_SUPPLY = 100_000 * 10**18  # to the governance Safe
SGREEN_INITIAL_SUPPLY = 0

# --- misc -------------------------------------------------------------------
TELLER_SHOULD_PAUSE = True  # Teller launches paused
BOND_BOOSTER_MAX_BOOST_RATIO = 200_00  # 200%
BOND_BOOSTER_MAX_UNITS = 25_000  # a count, not a ratio
BOND_BOOSTER_MIN_LOCK_DURATION = DAY_IN_BLOCKS * 180


# --- governance -------------------------------------------------------------
# The multi-chain Safe, same address as Base. It receives governance at the end
# of the final migration; it never signs a deployment transaction.
GOVERNANCE = ROBINHOOD_GOVERNANCE
SAFE = ROBINHOOD_GOVERNANCE

# Evidentiary roles. No Robinhood contract reads a "guardian", and the Safe
# holds every power the role describes -- including the unpause that lite
# signers deliberately cannot perform.
GUARDIAN = ROBINHOOD_GOVERNANCE

# --- token supply -----------------------------------------------------------
# Base minted its RIPE supply to GOVERNANCE; Robinhood mints the approved
# 100,000 to the same Safe. GREEN goes to the deployer, which seeds the pool.
# sGREEN has a zero supply, and Erc20Token skips the credit entirely when the
# supply is zero, so a zero recipient makes the mint impossible rather than
# merely unused -- which is exactly what Base passed.
SGREEN_SUPPLY_RECIPIENT = ZERO_ADDRESS

# --- training wheels --------------------------------------------------------
# Empty at launch by owner decision. Base seeded four addresses here; Robinhood
# starts with none and adds them afterwards through the normal governed path.
TRAINING_WHEELS_ALLOWLIST = []

# --- Ledger action-block source ---------------------------------------------
# ArbSys is the production answer: Robinhood is an Arbitrum L2 where
# `block.number` is the L1 ancestor estimate and REPEATS across child blocks, so
# native mode lets the Ledger's one-action-per-block guard treat several child
# blocks as one. `arbBlockNumber()` is the true child height.
#
# It CANNOT be exercised on a titanoboa fork. ArbSys is a node-implemented
# precompile, not bytecode: `boa.env.get_code(0x64)` returns 1 byte and the call
# reverts, so the Ledger constructor -- which deliberately refuses to deploy
# unless it can read the block number -- fails on any local fork.
#
# Set RIPE_LEDGER_BLOCK_SOURCE=native to fork-test the REST of the deployment.
# That run does not validate this choice, and must not be read as proving it.
_NATIVE_BLOCK_SOURCE = ZERO_ADDRESS
LEDGER_ACTION_BLOCK_SOURCE = (
    _NATIVE_BLOCK_SOURCE
    if os.environ.get("RIPE_LEDGER_BLOCK_SOURCE") == "native"
    else ROBINHOOD_ADDRESSES["ARB_SYS"]
)

# --- blue chip yield --------------------------------------------------------
# Only Morpho V2 exists on Robinhood. The other six registries are zero, which
# fails CLOSED: Vyper checks extcodesize, so registering an asset against a zero
# registry reverts rather than silently mispricing it.
BLUECHIP_MORPHO_FACTORIES = [ZERO_ADDRESS, ZERO_ADDRESS]
BLUECHIP_EULER_FACTORIES = [ZERO_ADDRESS, ZERO_ADDRESS]
BLUECHIP_FLUID_RESOLVER = ZERO_ADDRESS
BLUECHIP_COMPOUND_CONFIGURATOR = ZERO_ADDRESS
BLUECHIP_MOONWELL_COMPTROLLER = ZERO_ADDRESS
BLUECHIP_AAVE_PROVIDER = ZERO_ADDRESS

# --- lootbox ----------------------------------------------------------------
# Every Lootbox parameter is an Underscore reward, and Underscore is
# intentionally absent on Robinhood. The floor must still be nonzero: the
# constructor asserts it is neither 0 nor max_value.
LOOTBOX_MIN_SEND_INTERVAL = 1
LOOTBOX_SEND_INTERVAL = 0
LOOTBOX_DEPOSIT_REWARD = 0
LOOTBOX_YIELD_BONUS = 0

# --- deleverage -------------------------------------------------------------
# Fresh-deployment values from docs/chains/rh/deleverage-cooldown-security-
# decision.md, plus the literals Base passed in 2026072800.
DELEVERAGE_MIN_BPS = 0
DELEVERAGE_BUFFER = 0
DELEVERAGE_COOLDOWN = 0
DELEVERAGE_UNDERSCORE_SPREAD = 1_00  # 1%
DELEVERAGE_FULL_PAYOFF_BUFFER = 10**15
DELEVERAGE_OVERAGE_BPS = 1_00  # 1%
DELEVERAGE_DUST_THRESHOLD = 0  # disabled pending governance policy approval
DELEVERAGE_DUST_BPS = 0  # disabled pending governance policy approval

# --- endaoment PSM ----------------------------------------------------------
# Deployed DISABLED: the constructor hard-sets canMint and canRedeem to False,
# and activation is a separate governed step. These fees and caps are
# scaffolding, not approved policy -- they are nonzero only because the
# constructor rejects a zero interval and a zero or max cap, and they are inert
# while mint and redeem are false. Values from the rh-deploy branch.
PSM_NUM_BLOCKS_PER_INTERVAL = 7_200  # 1 day on Robinhood
PSM_MINT_FEE = 0
PSM_MAX_INTERVAL_MINT = 100_000 * 10**18
PSM_REDEEM_FEE = 0
PSM_MAX_INTERVAL_REDEEM = 100_000 * 10**18
# Yield position disabled: lego id 0 and a zero vault token leave it unset.
PSM_YIELD_LEGO_ID = 0
PSM_YIELD_VAULT_TOKEN = ZERO_ADDRESS

# --- price sources ----------------------------------------------------------
# CurvePrices takes a price-change timelock band. Robinhood has no separate
# PRICE_DESK_*_REG_TIMELOCK, so all three price sources share the approved
# Chainlink band.
PRICE_CHANGE_MIN_TIMELOCK = PRICE_MIN_TIMELOCK
PRICE_CHANGE_MAX_TIMELOCK = PRICE_MAX_TIMELOCK

# --- curve pool -------------------------------------------------------------
# 100 USDG (6dp) + 100 GREEN (18dp), matching Base's GREEN pool seed.
POOL_SEED_USDG = 100 * 10**6
POOL_SEED_GREEN = 100 * 10**18
# Seeding an empty StableSwap-NG pool mints LP equal to the invariant D, so
# ~200e18 at a 1:1 peg. Base passed 0; this is a ~0.5% floor -- tight enough to
# abort if the pool is not what we think it is, loose enough for rounding.
POOL_MIN_MINTED_LP = 199 * 10**18
