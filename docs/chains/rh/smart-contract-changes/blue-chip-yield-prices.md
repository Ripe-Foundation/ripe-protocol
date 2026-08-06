# BlueChipYieldPrices: Morpho V2 compatibility rationale

## Current `rh` rebind

This rationale is bound to current `rh` commit
`0642f086d19e3cc62faaf67da096b6511e405320`, tree
`d869d4149380b368f9678ed03efc0b59a6c804e2`.

| Identity | Current value |
| --- | --- |
| Production source | [`contracts/priceSources/BlueChipYieldPrices.vy`](../../../../contracts/priceSources/BlueChipYieldPrices.vy) |
| Git blob | `cafd177ef601186b0a6a30863ba5b8973d8dd92e` |
| Source SHA-256 | `abe188bf7edd973f6d68e58e39767e948471542030f6c2447ab98616c303e8be` |
| Source size | 38,730 bytes |
| Creation artifact | 23,627 bytes; SHA-256 `725ed0aee23fdf31d51fa720ecc1806976f1dff127d2c2c78ea3ce1d28f5ab6d` |
| Runtime template | 22,054 bytes; SHA-256 `84e004bf72ed7a699c7b7c52d849674517f82581cd4f49b73a06f1721e6cf578` |
| EIP-170 headroom | 2,522 bytes |
| Compiler integrity | `a7bd19991381dd4d3f1d6863e3b2291823a092c130402e62a18159f21bbeeff5` |
| Canonical ABI SHA-256 | `d1a7f8491d5b1ba59da03ef3e0920a6bbf7682dfc2f0b471d4a5a8a1cb8f5c73` |
| Committed ABI file SHA-256 | `b4c17cf9a87cd3325fba306cc9e4a9595c2e0689c18fb4fc2da2aed5622e91f7` |

The artifact values above were freshly compiled and hashed with Vyper
`0.4.3+commit.bff19ea2`; they are current compiler artifacts, not deployed
runtime evidence.

## Why the source changed

Morpho Vaults V2 use a different factory membership selector and must be read
defensively across external factory, vault, and underlying-token boundaries.
The existing `MORPHO` lane is MetaMorpho-specific, so treating V2 as ordinary
Morpho would either reject an intended V2 vault or blur two distinct admission
contracts.

The change therefore appends `MORPHO_V2` to the existing `Protocol` flag,
adds one immutable V2 factory address, validates membership through
`isVaultV2(address)`, and performs strict one-word reads for V2 asset,
decimals, supply, and `convertToAssets` observations.

Appending the flag matters: existing stored protocol-bit meanings for Morpho,
Euler, Moonwell, Sky, Fluid, Aave V3, and Compound V3 remain unchanged.

## Compatibility and fail-closed behavior

### Existing Morpho, Euler, and Fluid

The existing MetaMorpho, Euler, and Fluid branches remain selected by their
original protocol flags and registry rules. Their ERC-4626 pricing behavior is
preserved. The integrated regression test also exercises existing ERC-4626
protocols after the V2 addition, while the existing dedicated Morpho, Euler,
and Fluid suites remain current source paths.

The change adds checked decimal scaling and checked multiplication/addition
around common price and snapshot arithmetic. Compatible existing observations
continue to price; an overflow or invalid decimal scale now returns zero rather
than allowing an unsafe calculation.

### Morpho V2 validation

A V2 feed is valid only when all of the following are usable and compatible:

- the immutable factory is the selected factory and returns exactly one ABI
  word whose value is Boolean `1` for the vault;
- the vault returns one valid nonzero underlying address;
- underlying and vault decimals return one word within the safe exponent
  bound;
- `totalSupply()` returns one word and is nonzero after normalization;
- `convertToAssets(scale)` returns one word; and
- supply-times-price and underlying-price-times-price calculations fit.

Reverting, empty, short, oversized, invalid-address, invalid-Boolean, or
otherwise malformed returns fail closed. At registration they make the feed
invalid. After registration, an unusable V2 observation produces zero price or
a zero snapshot rather than retaining a newly computed positive value.

Zero supply is explicitly incompatible for Morpho V2: it rejects new-feed
validation, and a later transition to zero produces a snapshot with
`totalSupply = 0` and `pricePerShare = 0`. Recovery requires later compatible
observations; the source does not invent supply or price.

## Interface and artifact effects

The semantic interface effects are narrow but real:

- the constructor gains final argument `_morphoV2Addr: address`;
- immutable getter `MORPHO_V2_ADDR()` is added;
- the `Protocol` flag gains an append-only `MORPHO_V2` value;
- the committed ABI changes accordingly; and
- source, creation bytes, runtime bytes, code layout, selector identity, and
  compiler-input identity all change.

The contract has 84 method identifiers and 20 events at the current snapshot.
The runtime is 22,054 bytes, leaving 2,522 bytes under EIP-170. That is useful
headroom, not permission for another contract change; any later edit requires a
fresh exact compiler and size rebind.

## PriceDesk slot-3 selection

Readable repository configuration selects `BlueChipYieldPrices` component
`CM-018` and semantic `BlueChipYield` at PriceDesk slot 3. The selection and
required-registry assertion are current source facts.

Selection is not deployment. It also is not registration, feed configuration,
live price availability, activation, or release. The Morpho V2 factory is an
external-fact input that must be independently verified before deployment and
registration. Current repository readiness remains fail-closed on unresolved
inputs.

## Current tests and supporting artifacts

| Path | Git blob | SHA-256 | Responsibility |
| --- | --- | --- | --- |
| [`tests/priceSources/blueChip/test_bluechip_morpho_v2.py`](../../../../tests/priceSources/blueChip/test_bluechip_morpho_v2.py) | `f3d0e492412bbea4f99b7f2d5aa3a00a653f80e7` | `ad5062ee4fa86cf8ad4a10b6440bd3606541544b84aad7f96b29e89bbb82e853` | Membership, malformed returns, zero supply, arithmetic bounds, recovery, and legacy ERC-4626 compatibility |
| [`tests/inventory/test_bluechip_yield_prices_artifacts.py`](../../../../tests/inventory/test_bluechip_yield_prices_artifacts.py) | `e950a93d34b1452f30a70e64084396756af5bf09` | `349c986da1086d679afef909af78f859ae273e7bc4cc52206bce382813177823` | Exact source/compiler/artifact/ABI/layout identity and slot-3 topology, including current fork-package references |
| [`tests/priceSources/blueChip/test_bluechip_morpho.py`](../../../../tests/priceSources/blueChip/test_bluechip_morpho.py) | `9d4e531b995b3011a7dcf8fcda5a5f3bbaf5c75a` | `f6a3040b46742f60f1ab74fbfb19cbcbc50fbda335520ba231130b6f7b9fd71e` | Existing Morpho lane |
| [`tests/priceSources/blueChip/test_bluechip_euler.py`](../../../../tests/priceSources/blueChip/test_bluechip_euler.py) | `582b104ec49501bae40698303bff1b2db28d4f2a` | `1540596cf13bc5861203034fa89f176b754871ca2fb3c1928989eb99c47e0cc9` | Existing Euler lane |
| [`tests/priceSources/blueChip/test_bluechip_fluid.py`](../../../../tests/priceSources/blueChip/test_bluechip_fluid.py) | `adbb2334092bd2d9a38697613beadad1ca08c33f` | `d1d04e81c6bc89edc6f224fb8f51417a1812a9b1d2d7b78da5acdf3497b9b074` | Existing Fluid lane |

The Vyper supporting artifacts are
[`MockMorphoV2Factory.vy`](../../../../contracts/mock/MockMorphoV2Factory.vy),
[`MockMorphoV2Vault.vy`](../../../../contracts/mock/MockMorphoV2Vault.vy), and
the extended
[`MockYieldRegistry.vy`](../../../../contracts/mock/MockYieldRegistry.vy).
They are test doubles, not deployment candidates or external-fact proof.

## Deployment and release boundary

Before any live use, a separately authorized process must verify the factory
and intended vaults, bind exact constructor values and artifacts, deploy,
read back immutables, register slot 3, configure individual feeds through the
governed path, validate live returns and monitoring, and obtain activation and
release approval. This rationale performs and authorizes none of those steps.
