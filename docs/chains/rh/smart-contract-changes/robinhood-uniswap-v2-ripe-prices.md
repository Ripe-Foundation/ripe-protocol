# RobinhoodUniswapV2RipePrices: archival monitoring prototype

## Current classification and identity

This rationale is bound to current `rh` commit
`5f5d22b7ee78cbb904c4fe3c6e46599c330c4353`, tree
`7454b5456ebb6cd02d716a64b408629ab501629e`.

[`RobinhoodUniswapV2RipePrices.vy`](../../../../contracts/priceSources/RobinhoodUniswapV2RipePrices.vy)
is an archival research and monitoring prototype. It is not a launch price
source or an admitted protocol component.

| Identity | Current value |
| --- | --- |
| Git blob | `11fb790f04f782d7c3e7abcc66f78077c13434d9` |
| Source SHA-256 | `56a6685442d8730922205f8fcd2893b542e12b7d5d0e1384bcc2f065b945b485` |
| Source size | 42,036 bytes |
| Creation artifact | 24,787 bytes; SHA-256 `77c7e0b1c3b67717fa02c82af58640c9bce482dd55ab50c5329731b7aec9f8d6` |
| Runtime template | 20,556 bytes; SHA-256 `d36fe90fb011e2fbed546c5a0c576c7e5346e90ec34947c7be079884b2ca9c58` |
| EIP-170 headroom | 4,020 bytes |
| Compiler integrity | `775273ac8f544330c38d84458813d30d947c3f76dd174290a90bc93ca2b7842a` |
| Canonical ABI SHA-256 | `3dc0dcfe1a130a5911f2b97f106c963ebe9dca17efdad943a0a9c9609bcc837e` |
| Committed ABI file SHA-256 | `6c6c98d5db355bdda398e956aa197b1f3a420d1342b5bfbbc3e2d706d8f1ce08` |

The compiler identities prove current local artifacts only. They are not a
deployment or registration record.

## Structurally PriceDesk-inert

The prototype intentionally implements the PriceSource-facing surface as a
permanent no-feed boundary:

```text
getPrice(...)                 -> 0
getPriceAndHasFeed(...)       -> (0, false)
hasPriceFeed(...)             -> false
addPriceSnapshot(...)         -> false
```

Those results do not depend on its internal monitoring configuration,
activation flag, checkpoints, reserves, cumulative prices, or TWAP state. Even
accidental insertion into PriceDesk cannot supply a usable feed or price. The
integrated tests exercise a real PriceDesk and prove that an accidentally
registered monitor remains inert and does not interfere with later
authoritative price sources.

The internal `feedPending` and lifecycle getters are diagnostic state. They do
not make `hasPriceFeed` true and must not be interpreted as PriceDesk admission.

## Direct monitoring and update surfaces

The source retains direct research/monitoring functionality:

- permissionless `update()` observes validated pair cumulatives and advances a
  direct checkpoint/average when time and safety bounds pass;
- direct getters expose reserve, average, checkpoint, price, age, and update-due
  diagnostics;
- timelocked local configuration and activation/disable actions exercise the
  prototype lifecycle; and
- pause, sequencer-health, factory/pair/token identity, reserve-floor,
  deviation, stale-time, and malformed-return checks fail closed.

These direct surfaces are useful for local research and an optional externally
held liquidity canary. They do not make the contract authoritative for Ripe
accounting. A monitor can calculate a direct diagnostic value while still
returning zero/no-feed through every PriceDesk-facing method.

## Current repository and approved-launch disposition

At the current baseline, the repository and approved launch authorities record
the prototype as:

- unregistered;
- unconfigured for production;
- non-admitted by the launch Blueprint;
- having no deployment record and therefore classified as undeployed;
- having no activation record; and
- unavailable for collateral, debt, liquidation, redemption, or any other
  protocol accounting.

The launch Blueprint selects PriceDesk source IDs `[1, 3]` for Chainlink and
BlueChipYield. It contains no `RobinhoodUniswapV2RipePrices` component. No
launch Uniswap oracle authority was approved, and no pool address, liquidity
amount, checkpoint service, funding/custody authority, migration, deployment
dependency, registration, admission, configuration, or activation follows
from this source's presence.

No RPC or live-chain discovery was performed for this documentation refresh;
the disposition above is deliberately limited to repository and approved
launch authority.

## Current tests and supporting artifacts

| Path | Git blob | SHA-256 | Responsibility |
| --- | --- | --- | --- |
| [`tests/priceSources/uniswap/test_correctness.py`](../../../../tests/priceSources/uniswap/test_correctness.py) | `99bd415b531a0a4adf094edd06edb2cb9c446f18` | `d7a794a65dc3fe1a3923bd12bb4d06b14b589c1dd2b40b79803a98ad85ecd584` | Direct TWAP/checkpoint correctness, orientation, decimals, boundaries, pair operations |
| [`tests/priceSources/uniswap/test_adversarial.py`](../../../../tests/priceSources/uniswap/test_adversarial.py) | `bd79fc8e6dafcd19ca891da9897af6d6f5af38e7` | `3c7fc02b70fec1eb7a74abb54efb0187571bd94cc7ed181a760665b2846dae1f` | Manipulation, stale, reserve, malformed-return, recursive, pause, and recovery cases |
| [`tests/priceSources/uniswap/test_governance_economics.py`](../../../../tests/priceSources/uniswap/test_governance_economics.py) | `b86162bba37c2370305426157934806234a65cf3` | `e4240ea6c8af3c3f46c52ca46c2eff26a518da52e0d4b5d011b1d9f90ff5d02b` | Timelocks, lifecycle, reserve/economic bounds, real PriceDesk inertness, and Blueprint non-admission |
| [`tests/inventory/test_block_clock_inventory.py`](../../../../tests/inventory/test_block_clock_inventory.py) | `8a4f7af0e3f4b8c18c01196edde27f8967228284` | `313acf48eca4694cbc7e577eb51fde49ede81232bf2bd1c91027f26857fcf798` | Timestamp/block inventory classification |
| [`tests/deployment/test_abi_export.py`](../../../../tests/deployment/test_abi_export.py) | `a7187f7020273207a7b9643fbe70c83c708d6364` | `dfd904fb2bac83771999c0547216388b28b78659980beff7a22481de1371759f` | Committed ABI export inventory |

The Uniswap V2 Vyper mocks are
[`MockUniswapV2Factory.vy`](../../../../contracts/mock/MockUniswapV2Factory.vy),
[`MockUniswapV2Pair.vy`](../../../../contracts/mock/MockUniswapV2Pair.vy),
[`MockUniswapV2Token.vy`](../../../../contracts/mock/MockUniswapV2Token.vy),
[`MockUniswapV2FlashBorrower.vy`](../../../../contracts/mock/MockUniswapV2FlashBorrower.vy),
and
[`MockUniswapV2QuotePriceDesk.vy`](../../../../contracts/mock/MockUniswapV2QuotePriceDesk.vy).
They are local test infrastructure, not selected external contracts or launch
artifacts.

## What this rationale does not authorize

No source, mock, ABI, or test result authorizes deployment or any step that
could make the prototype authoritative. Work beyond archival prototype
maintenance requires a separately approved security-relevant consumer and
separate owner, risk, security, custody, exposure, configuration, deployment,
registration, activation, and release decisions.
