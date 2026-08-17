# Contributor administrative-state live evidence

Local, uncommitted evidence captured on 2026-08-14 for the Contributor
administrative-state consistency task. This is not deployment authority, an
audit-guide update, or evidence that any corrective transaction executed.

## Bound scope

- Repository: `/Users/wigglez/dev/ripe-protocol-audit-remediation-contributor-admin-state-consistency`
- Git commit: `21f2433d27181583e7338b96e5431d243994ff05`
- Robinhood chain ID: `0x1237` (4663)
- RPC: `https://rpc.mainnet.chain.robinhood.com`
- RPC provenance: Robinhood's public mainnet endpoint documented at
  `https://docs.robinhood.com/chain/connecting/`
- All calls were read-only. No transaction was signed or broadcast.
- State calls used the `latest` tag because this public endpoint rejected an
  exact historical-state call with `metadata is not found`. The block anchors
  below bound the sampling period but are not claims that every `eth_call`
  executed against one exact state root.

## Launch-gating conclusions

1. `Ledger.numContributors()` is zero. No live Contributor instance is exposed.
2. All currently active Switchboard and price-source action timelocks queried
   are zero.
3. All four currently active registry-change timelocks are zero, including
   RipeHq. A Safe MultiSend can therefore place registry start and confirm
   calls in the same child transaction/block; there is no configured
   observation delay.
4. Active HumanResources also has a zero action timelock, so a Contributor can
   be initiated and confirmed without the intended HR delay.
5. `MissionControl.hrConfig().contribTemplate` points to a live blueprint whose
   bytecode is the 2025-06-24 Contributor generation. It is missing B-AUD-019,
   AUD-015, and later ownership hardening.
6. The zero HR delay and historical blueprint compose: the first Contributor
   can be created immediately from code that does not contain the pinned
   pending-state exclusion.

Do not create the first Contributor until the deployment-wide timelocks and
Contributor blueprint have been remediated and read back. The registry and
Switchboard findings are broader than this Contributor source task and should
be handled as a separate live-governance incident.

## Git-history reconciliation

The current migration text did not execute as written:

- `0007_FinishSetup.py` originally landed at
  `484dc1229c072ff76a6b006a25deb9e0a1330796` on 2026-08-05 with the action- and
  registry-timelock block commented out.
- The executable 0007 timelock setup landed later at
  `490565a061720c1f4c691d40cc868984e425e380` on 2026-08-06.
- `0009_RedeployStaleContracts.py` originated at
  `2e890188e03febdf3e4b44326e4f9c8df9815831` on 2026-08-06 without timelock
  handling.
- The current 0009/0010 pre-activation checks landed on 2026-08-11 at
  `e7421330e5e3c515714878f7a11a82b0d5d00660`, after the recorded deployments.

The live zero readbacks are consistent with the historical migration versions,
not with the later source safeguards.

## Snapshot anchors and action-block cadence

### Sample 1

- RPC method: `eth_getBlockByNumber("latest", false)`
- Child block `number`: `0x22d6ff6` (36,532,214)
- Block object's `l1BlockNumber`: `0x188ffd0` (25,755,600)
- Timestamp: `0x6a7f774b` (`2026-08-14T20:15:07Z`)
- Hash: `0xda372cebc1545ae5fc65de92d2c7d3368241af0c19d699933fe57aaff235b3ec`
- Contract-visible EVM `NUMBER`: `0x188ffd0`, obtained with creation-call
  bytecode `0x4360005260206000f3` (raw result:
  `0x000000000000000000000000000000000000000000000000000000000188ffd0`)
- `Ledger.getArbActionBlock()`: `0x22d6ff6` (raw result:
  `0x00000000000000000000000000000000000000000000000000000000022d6ff6`)

### Sample 2

- RPC method: `eth_getBlockByNumber("latest", false)`
- Child block `number`: `0x22d87b4` (36,538,292)
- Block object's `l1BlockNumber`: `0x1890002` (25,755,650)
- Timestamp: `0x6a7f79ad` (`2026-08-14T20:25:17Z`)
- Hash: `0x410fb8738f2dddf457c1954308f315002197f186291a83fc6669fd2f2e177081`
- Contract-visible EVM `NUMBER`: `0x1890002`, obtained with the same
  creation-call bytecode (raw result:
  `0x0000000000000000000000000000000000000000000000000000000001890002`)
- `Ledger.getArbActionBlock()`: `0x22d87b4` (raw result:
  `0x00000000000000000000000000000000000000000000000000000000022d87b4`)

The samples are 610 seconds apart. The child-block delta is 6,078, while the
L1-block and contract-visible `block.number` delta is 50: 4.918 L1 blocks per
minute, or 12.2 seconds per L1 block over this interval. The administrative
time locks in `TimeLock.vy`, `AddressRegistry.vy`, and `Contributor.vy` use
`block.number`, so their units follow the observed L1 cadence rather than the
child-block cadence. At this sample rate, 600, 3,600, and 7,200 blocks are
approximately 2.03, 12.2, and 24.4 hours. `Ledger.getArbActionBlock()` is the
separate child-chain value used by Ledger's one-action-per-block protection.

## Active-address proof

Selector: `getAddr(uint256) = 0xd81f84b7`.

RipeHq `0xD4e82AE1De673bba3B53386A2D2C630AE6630940` returned:

| ID | Component | Returned active address |
|---:|---|---|
| 4 | Ledger | `0x7B2aeE8B6A4bdF0885dEF48CCda8453Fdc1Bba5d` |
| 5 | MissionControl | `0x5B8b85cD2f56D1a99691de784FB50c0bf2FA3baC` |
| 6 | Switchboard registry | `0x4A9B60633f65ba9Ae6faedD289A597D78347CFb4` |
| 7 | PriceDesk registry | `0x694a1F8525483cFf3142770395Ec310bf954b0C0` |
| 8 | VaultBook registry | `0x8DBd00caA2e13dC1A32aA2F726711b97A046e964` |
| 15 | HumanResources | `0xF17eF9744882cF9c00dC89Cfe6DB8E0b2D16bB4a` |

Switchboard registry `0x4A9B60633f65ba9Ae6faedD289A597D78347CFb4`
returned:

| ID | Component | Returned active address |
|---:|---|---|
| 1 | Alpha | `0xd02ff7F8202fae6890Fbf089B75A846743197E62` |
| 2 | Bravo | `0xacFcC76e4F40d56B52e51418B31e2091091520dE` |
| 3 | Charlie | `0xf9e3F5E80e7b23eE754727509FA82Ee8626ddB04` |
| 4 | Delta | `0x6C75717e34Dcc74DF0a3b03c2C98B9DBCba57756` |
| 5 | Echo | `0xC11b8Cf74607A5e4bA55Ff7806Ac29229f2481f3` |

PriceDesk `0x694a1F8525483cFf3142770395Ec310bf954b0C0`
returned:

| ID | Component | Returned active address |
|---:|---|---|
| 1 | ChainlinkPrices | `0xeAfE60Df55F4B1eDE8852C75Fe21c3224EEa4f24` |
| 2 | CurvePrices | `0x236Af2b8d0867f898FeD3fBFDfcDD131001135F3` |
| 3 | UniswapV2Prices | `0xfB2d96242769fCE0a3Cf75204B0553cE0E516545` |

The BlueChipYieldPrices address configured by historical 0007 is no longer an
active PriceDesk entry; current slot 3 resolves to UniswapV2Prices. The table
therefore covers all three active price-source action timelocks.

## Deployment-wide timelock readbacks

Action selectors:

- `actionTimeLock() = 0xc3901d01`
- `minActionTimeLock() = 0xee5e7179`
- `maxActionTimeLock() = 0x724bd531`

Every current raw word below was
`0x0000000000000000000000000000000000000000000000000000000000000000`.

| Active component | Address | Current | Immutable minimum | Immutable maximum |
|---|---|---:|---:|---:|
| SwitchboardAlpha | `0xd02ff7F8202fae6890Fbf089B75A846743197E62` | 0 | 600 (`0x258`) | 50,400 (`0xc4e0`) |
| SwitchboardBravo | `0xacFcC76e4F40d56B52e51418B31e2091091520dE` | 0 | 600 | 50,400 |
| SwitchboardCharlie | `0xf9e3F5E80e7b23eE754727509FA82Ee8626ddB04` | 0 | 600 | 50,400 |
| SwitchboardDelta | `0x6C75717e34Dcc74DF0a3b03c2C98B9DBCba57756` | 0 | 600 | 50,400 |
| SwitchboardEcho | `0xC11b8Cf74607A5e4bA55Ff7806Ac29229f2481f3` | 0 | 600 | 50,400 |
| HumanResources | `0xF17eF9744882cF9c00dC89Cfe6DB8E0b2D16bB4a` | 0 | 7,200 (`0x1c20`) | 50,400 |
| ChainlinkPrices | `0xeAfE60Df55F4B1eDE8852C75Fe21c3224EEa4f24` | 0 | 600 | 50,400 |
| CurvePrices | `0x236Af2b8d0867f898FeD3fBFDfcDD131001135F3` | 0 | 600 | 50,400 |
| UniswapV2Prices | `0xfB2d96242769fCE0a3Cf75204B0553cE0E516545` | 0 | 600 | 50,400 |

Registry selectors:

- `registryChangeTimeLock() = 0x06400479`
- `minRegistryTimeLock() = 0x6688f72a`
- `maxRegistryTimeLock() = 0xb9b5dbb6`

Every current raw word below was also zero.

| Active registry | Address | Current | Immutable minimum | Immutable maximum |
|---|---|---:|---:|---:|
| RipeHq | `0xD4e82AE1De673bba3B53386A2D2C630AE6630940` | 0 | 3,600 (`0xe10`) | 50,400 |
| Switchboard | `0x4A9B60633f65ba9Ae6faedD289A597D78347CFb4` | 0 | 7,200 (`0x1c20`) | 50,400 |
| PriceDesk | `0x694a1F8525483cFf3142770395Ec310bf954b0C0` | 0 | 3,600 | 50,400 |
| VaultBook | `0x8DBd00caA2e13dC1A32aA2F726711b97A046e964` | 0 | 3,600 | 50,400 |

These zero values are initialization gaps, not mutable choices that were set
and later lowered: both setup paths require the previous value to be zero, and
normal validation requires the immutable nonzero minimum.

## HumanResources and Contributor exposure

- `Ledger.numContributors() = 0x00`.
- Active HR `actionTimeLock() = 0x00`.
- `eth_getStorageAt(active_hr, 0x9, latest) = 0x00`, independently
  corroborating the getter.
- `eth_getLogs` for
  `ActionTimeLockSet(uint256,uint256)` topic
  `0x494182dce7963f8f20b15adc110fe2d6659b940b8a162088a01fba3fba125e04`
  returned `[]` for the active HR address.
- `MissionControl.hrConfig()` selector `0x0190dbb3` returned first word
  `0x2593d4eeeeab39eb5f86b76ae54c6f0f1a7cc567`, the live Contributor
  blueprint.

## Live Contributor blueprint identity

Address: `0x2593D4eeEeaB39Eb5F86B76AE54C6f0F1A7cC567`.

`eth_getCode` evidence:

- length: 5,128 bytes
- SHA-256: `839877de6fd2f8a62339a5745d22760120c51994c906ff7ed933fdda664e2e33`
- first 32 bytes:
  `fe71006112675150346101a25760206114055f395f518060a01c6101a2576040`
- last 32 bytes:
  `9dc347539875576edcdc081912278118541860a1657679706572830004030038`

A detached compilation of
`d0957e497261a52e7a7b460eb986a6e9fb27f051` (`2025-06-24`, Vyper 0.4.3)
as `0xfe7100 + compiler_data.bytecode` reproduced exactly the same length,
hash, and prefix. The manifest's Contributor source differs from that commit
only by a trailing newline and compiles identically.

Pinned source at `21f2433d` produces:

- ERC-5202 body length: 5,298 bytes
- SHA-256: `8969e101c3c259fab1d054554368d0b7bf47f503b940fc7bc33f7982408f4467`

The live generation predates and lacks:

- B-AUD-019 at `72e3c5591821775182a16aa296ad5d53678126c7`:
  `changeOwnership` does not reject a pending RIPE transfer;
- AUD-015 at `e56c42fe9790ccd08237f46fb1455f2f56608caf`:
  terminal zero-compensation vesting views are not guarded;
- `numOwnerChanges`, its overflow guard, and its storage slot;
- ownership confirmation-block overflow protection; and
- constructor/new-owner self-address rejection.

The live blueprint therefore has a different runtime and storage layout from
the pinned source. The pinned-source runtime, ABI, and storage-layout hashes do
not describe the live blueprint.

## Lite-action and Safe authority

RipeHq `governance()` returned Safe
`0xe488a42D33b3Af5d3E5Cd5680938d8369716D1bf`.

- Safe threshold: 2
- Safe owners:
  - `0x55f56f74e006496e23aec96b3f72cadee805a1d8`
  - `0x8d85be8b51d1da224fce440950f76a1a0d7c88cc`
  - `0xb7827a593b0bafceefae1f318768b3bfe279ec71`

Confirmed `CanPerformLiteAction(address,bool)` events on launch Alpha
`0xfa48AF6AE4C4a4E29E8c148518854Ff36023f0E9` occurred in transaction
`0x370e315345fa5f6ddc34ffa584e6ff825e4475a9f717fe317ab8d05a86f27f67`
at child block `0x1c5b85a` for:

- `0xeab5190bdb0cd9a01520e628b0205ed75a77e466`
- `0xb7827a593b0bafceefae1f318768b3bfe279ec71`
- `0x55f56f74e006496e23aec96b3f72cadee805a1d8`

Current `MissionControl.canPerformLiteAction(address)` returned raw word `0x01`
for all three. The current Alpha emitted no later grant event. Two lite signers
are also current Safe owners; only `0xeab5...e466` is independent of the current
Safe owner set. A lite signer may freeze and cancel a pending ownership change,
but cannot unfreeze; unfreeze is governance-only.

## Hash recipes

For `c = boa.load_partial("contracts/modules/Contributor.vy").compiler_data`:

- runtime hash:
  `sha256(bytes(c.bytecode_runtime))`
- canonical ABI hash:
  `sha256(json.dumps(build_abi_output(c), sort_keys=True, separators=(",", ":")).encode())`
- canonical storage-layout hash:
  `sha256(json.dumps(c.storage_layout["storage_layout"], sort_keys=True, separators=(",", ":"), default=str).encode())`
- local ERC-5202 blueprint-body hash:
  `sha256(b"\xfe\x71\x00" + bytes(c.bytecode))`
- live blueprint hash:
  `sha256(bytes.fromhex(eth_getCode_result.removeprefix("0x")))`

Pinned-source results:

- runtime template: 4,800 bytes
- deployed runtime: 4,896 bytes
- runtime SHA-256:
  `5f71721538b0a1edfe7025f92154177ffa7aecb151c6e797564a32986c7832d9`
- ABI SHA-256:
  `b1aa1322548b6dde9950e31bdfe8c844f17e97501e30941c16e6cf39edacc121`
- storage-layout-section SHA-256:
  `1981bdd9f1fc56b111654054e589cf4e03ce8af0fdda90bc303112a9e641d9c1`

## Separate owner policy decision

Freezing before governed `cancelPaycheck` currently forfeits
vested-but-unclaimed compensation because the frozen cash step returns zero and
does not advance `totalClaimed`. Whether freeze should imply that clawback is an
owner compensation-policy decision. No production change for that behavior was
made in this task.

## Merge sequencing

This task intentionally moves shared Contributor fixtures into
`tests/core/humanResources/conftest.py` and shared state builders into
`contributor_test_utils.py`. It therefore modifies the tracked B-AUD-019 file
`test_contributor_pending_state_exclusion.py` without changing its test bodies
or node IDs. Sequence this task with any concurrent B-AUD-019 test changes to
avoid a mechanical merge conflict.
