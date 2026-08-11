# Robinhood Chain CCIP public-evidence record

Status: Public-evidence baseline complete; external confirmation remains required

Evidence retrieved: 2026-07-23; directory/API facts and thin-subclass build
evidence rechecked 2026-07-27

Track branch: `rh-track-1-chainlink-ccip`

Track start commit: `51a7a3996f5fec40efd554d1b025aaa9c2ed4ea2`

Planning baseline: `1bb8bd5b8837a06c818c3fb9e7b599b5dd29f2b1`

## Outcome

The public record supports a direct Base <-> Robinhood Chain GREEN and RIPE
bridge built on Chainlink CCIP:

- Chainlink's current directory lists direct Base <-> Robinhood Chain lanes on
  mainnet and direct Base Sepolia <-> Robinhood Chain Testnet lanes on testnet.
  All four lane entries report CCIP version `1.6.0`.
- Ripe's token interfaces match CCIP's burn/mint mechanics: the token pool can
  burn tokens it holds with `burn(uint256)` and mint to a receiver with
  `mint(address,uint256)`.
- The selected design keeps each token pool as the direct caller of
  `GREEN.mint` or `RIPE.mint`. A separately registered adapter could
  technically become that direct caller, but is rejected because it adds a
  mint-critical contract and trust boundary without solving a token-interface
  problem.
- The owner selected one thin Solidity GREEN subclass and one thin Solidity
  RIPE subclass of Chainlink's concrete v1.6.1 `BurnMintTokenPool`, each used
  on both chains. Local compilation and the exact-hash Round-3 independent
  review prove the subclasses add only the two Ripe capability selectors and
  no storage or bridge override.
- The immutable Base token deployments expose neither `owner()` nor
  `getCCIPAdmin()`. Public Chainlink documentation therefore points to assisted
  registration rather than self-service registration for Base. An unchanged
  token deployment on Robinhood Chain would have the same constraint.

This evidence is sufficient to prepare the technical question packet and a
conditional integration decision. It is not sufficient to choose the final
pool/API reference version, establish that Chainlink will support the thin
subclass on the target lanes, clear the full destination-gas budget, or
authorize deployment.

## Research boundaries and reproducibility

The repository sources named in the Track 1 contract were read in full. There
are no changes to the required token, registry, test, or migration files between
the planning baseline and the track start commit. The deployed Base token
source embedded in `migration_history/base-mainnet/v1/current-manifest.json`
also matches the current token source semantically; the diff is only a trailing
blank line.

Read-only `eth_call` checks were made against Base mainnet on 2026-07-23. No
transaction was signed or broadcast. No Chainlink form was submitted, no
message was sent, and no terms were accepted.

Useful reproduction commands:

```bash
git diff --stat \
  1bb8bd5b8837a06c818c3fb9e7b599b5dd29f2b1..51a7a3996f5fec40efd554d1b025aaa9c2ed4ea2 \
  -- contracts/registries/RipeHq.vy \
     contracts/registries/modules/AddressRegistry.vy \
     contracts/tokens/GreenToken.vy \
     contracts/tokens/RipeToken.vy \
     contracts/tokens/modules/Erc20Token.vy \
     contracts/mock/MockDepartment.vy \
     tests/registries/test_ripe_hq.py \
     tests/tokens/test_erc20.py \
     scripts/migrate.py \
     scripts/utils/migration.py \
     scripts/utils/migration_runner.py

cast call 0xd1Eac76497D06Cf15475A5e3984D5bC03de7C707 \
  'decimals()(uint8)' --rpc-url "$BASE_RPC_URL"
cast call 0xd1Eac76497D06Cf15475A5e3984D5bC03de7C707 \
  'ripeHq()(address)' --rpc-url "$BASE_RPC_URL"
cast call 0x2A0a59d6B975828e781EcaC125dBA40d7ee5dDC0 \
  'decimals()(uint8)' --rpc-url "$BASE_RPC_URL"
cast call 0x2A0a59d6B975828e781EcaC125dBA40d7ee5dDC0 \
  'ripeHq()(address)' --rpc-url "$BASE_RPC_URL"
```

Calling `owner()` and `getCCIPAdmin()` on both Base tokens reverted, consistent
with the deployed ABI and source. The RPC URL is deliberately not recorded.

## Chain and lane evidence

As retrieved on 2026-07-23, [Robinhood's connecting
documentation](https://docs.robinhood.com/chain/connecting/) describes Robinhood
Chain as an Arbitrum L2 using ETH for gas and identifies production and test
chain IDs `4663` and `46630`. [Robinhood's bridge
documentation](https://docs.robinhood.com/chain/bridging/) separately lists
Chainlink CCIP/Transporter as a supported cross-chain route.

### Mainnet

Source, retrieved 2026-07-23: current Chainlink directory entries for
[Base](https://docs.chain.link/ccip/directory/mainnet/chain/ethereum-mainnet-base-1)
and [Robinhood
Chain](https://docs.chain.link/ccip/directory/mainnet/chain/robinhood-mainnet).

| Field | Base | Robinhood Chain |
| --- | --- | --- |
| Chain selector | `15971525489660198786` | `6180753054346818345` |
| Router | `0x881e3A65B4d4a04dD529061dd0071cf975F58bCD` | `0x06fC836cf9839B1cd891C440A0a45242DA6Ae1c9` |
| Directory-listed RMN proxy | `0xC842c69d54F83170C42C4d556B4F6B2ca53Dd3E8` | `0xe8464c353210Cc398A45dB2454FBc5BCd25fFf20` |
| Token Admin Registry | `0x6f6C373d09C07425BaAE72317863d7F6bb731e37` | `0x1912C3cFafE8A76A32a92861d815aC2837F237Ca` |
| RegistryModuleOwnerCustom | `0xAFEd606Bd2CAb6983fC6F10167c98aaC2173D77f` | `0x3237c0D7B58BEc8Dc17F00103B784Bd6678f789E` |
| Token pool factory | `0xcD66e8e103D05BC3a5059746283949A45C594D16` | `0x913814782144864e523C3FdB78E3ca25D2c2aeCa` |
| Local OnRamp for peer lane | `0xee85aEfb15b9489563A6a29891ebe0750AA1A7Ae` | `0xe72d25aDd538E8ef9CeF85622eA8912a6CB98Be6` |
| Local OffRamp for peer lane | `0xf09AFe78d3c7d359b334d7cB88995751F7eC5E13` | `0xcDca5D374e46A6DDDab50bD2D9acB8c796eC35C3` |
| Directory lane version | `1.6.0` | `1.6.0` |

### Testnet

Source, retrieved 2026-07-23: current Chainlink directory entries for [Base
Sepolia](https://docs.chain.link/ccip/directory/testnet/chain/ethereum-testnet-sepolia-base-1)
and [Robinhood Chain
Testnet](https://docs.chain.link/ccip/directory/testnet/chain/robinhood-testnet).

| Field | Base Sepolia | Robinhood Chain Testnet |
| --- | --- | --- |
| Chain selector | `10344971235874465080` | `2032988798112970440` |
| Router | `0xD3b06cEbF099CE7DA4AcCf578aaebFDBd6e88a93` | `0x30D197C6F5bE050D5525dD94d01760FaCdB67e7C` |
| Directory-listed RMN proxy | `0x99360767a4705f68CcCb9533195B761648d6d807` | `0x934c1B8f6913070528CC24081E0b78d57D3A97A3` |
| Token Admin Registry | `0x736D0bBb318c1B27Ff686cd19804094E66250e17` | `0xad4c7a1430D140Fc5121C0697B2f7Efc655c0070` |
| RegistryModuleOwnerCustom | `0x176ae8C6C11DD2c031B924CE1A0A43188035f3f6` | `0x00094197A82faDE614C214CFE27719dEDa898686` |
| Token pool factory | `0x29014dCC16CD6543F5c09623FD9c325902076caD` | `0x9A60462e4CA802E3E945663930Be0d162e662091` |
| Local OnRamp for peer lane | `0x28A025d34c830BF212f5D2357C8DcAB32dD92A20` | `0xEC7088f7952ba58f268E25AC3868DF92bF462AEf` |
| Local OffRamp for peer lane | `0xF4EbCC2c077d3939434C7Ab0572660c5A45e4df5` | `0x7A635FdfDC70469B6e8796Bd7dEeB3f24fd4f949` |
| Directory lane version | `1.6.0` | `1.6.0` |

The OnRamp and OffRamp values above are the local-chain addresses in the
directory's structured record for the peer lane. They are not pool constructor
values. The selected subclasses retain Chainlink TokenPool v1.6.1's five
arguments: local token, decimals, allowlist, directory-listed RMN proxy, and
Router. The deployer is the initial owner through inherited ownership logic,
and remote-chain configuration is applied separately. The Base mainnet
explorer identifies its directory-listed address as the proxy contract
(`ARMProxy`, the predecessor name); confirmation that every current directory
`RMN` field is the intended v1.6.1 constructor proxy remains in the external
packet.

### Existing token-transfer configuration

The [Robinhood mainnet
directory](https://docs.chain.link/ccip/directory/mainnet/chain/robinhood-mainnet)
structured data, retrieved 2026-07-23, lists `BWLK`, `SDM`, and `VIRTUAL` as
supported tokens in both directions on the Base <-> Robinhood Chain lane. This
is stronger evidence than the existence of lane contracts alone: the lane is
configured for third-party cross-chain token transfers. It is not, by itself,
proof of a recent successful transfer or a commitment to support Ripe's custom
pool.

## Release and source evidence

As retrieved on 2026-07-23, Chainlink's current [EVM API
reference](https://docs.chain.link/ccip/api-reference/evm/v1.6.1/) labels
contracts-CCIP `1.6.1` as the latest documented release. Its installation page
pins:

- npm package: `@chainlink/contracts-ccip@1.6.1`
- Foundry source commit:
  `smartcontractkit/chainlink-ccip@bbab0601244ce58e2ffac0dbc178a80aab1fa4a3`
- shared Chainlink EVM dependency:
  `smartcontractkit/chainlink-evm@e06cc226086ad91cfede63e96c63e5b3440c9801`
- documented Solidity pragma for `BurnMintTokenPool.sol`: `^0.8.24`

The [pinned `BurnMintTokenPool`
source](https://github.com/smartcontractkit/chainlink-ccip/blob/contracts-ccip-v1.6.1/chains/evm/contracts/pools/BurnMintTokenPool.sol)
shows `_lockOrBurn` calling
`IBurnMintERC20(address(i_token)).burn(amount)`. The [abstract pool API
reference](https://docs.chain.link/ccip/api-reference/evm/v1.6.1/burn-mint-token-pool-abstract)
shows the release/mint path calling `mint(receiver, amount)`. Those are direct
token calls.

There is a version boundary that must be confirmed: the live lane directory
reports core lane version `1.6.0`, while the current documented token-pool API is
`1.6.1`. Repository branches and package registries may expose newer artifacts,
but that is not evidence that a newer pool is audited and supported for this
lane. The provisional implementation pin is therefore the exact documented
`1.6.1` commit, subject to Chainlink confirmation of lane compatibility and the
recommended production version.

### Thin Solidity inheritance evidence

The selected
[`examples/RipeCcipBurnMintTokenPools.sol`](examples/RipeCcipBurnMintTokenPools.sol)
contains one GREEN and one RIPE subclass of the concrete v1.6.1
`BurnMintTokenPool`. It is an independently reviewed reference, not production
deployment source. The review is bound to source SHA-256
`28fea3591caf8955a4c1f47d34f5abfe249564001578687525f94fddf5cfac77`;
see the
Round-3 review record.

Each subclass:

- uses the standard five-argument constructor;
- adds `canMintGreen()` and `canMintRipe()`;
- adds no storage; and
- does not override any inherited function.

The 2026-07-27 reference build used
`@chainlink/contracts-ccip@1.6.1`,
`@chainlink/contracts@1.4.0`, Solidity `0.8.26`, EVM `paris`, via-IR,
optimizer `80_000`, and no metadata hash. Those are the upstream v1.6.1
Foundry settings. The npm tarball shasums and published SRI integrity values
observed in that build were:

- contracts-CCIP shasum:
  `9b0f5665634110bfa1d249eb58c141e358e05945`; integrity:
  `sha512-2ainz7DhzSPyUTD01e0roRHQ4V895peJ6rlu+GgxOYCZVFVtuwXEbT27ByyaJSFsB9ZubAtu1zhAijuL0OwPzw==`;
- shared contracts shasum:
  `e976e012fe9104067e9f00ef397de6d48a7d1593`; integrity:
  `sha512-SpNCJ0TPOI6pa2l702Wk4WIP8ccw5ARcRP1E/ZTqaFffXNoZeF03WhsVL8f3l3OTRFA9Z40O5KcZzmJmZQkoFA==`.

Compile comparison:

| Property | Standard pool | Ripe subclass |
| --- | ---: | ---: |
| Runtime bytecode | 17,334 bytes | 17,472 bytes |
| EIP-170 margin | 7,242 bytes | 7,104 bytes |
| External methods | 30 | 32 |
| Storage entries | 8 | 8 |

After removing the compiler's contract-name annotation, the base and derived
storage layouts were identical. The only added selectors were
`canMintGreen() = 0x40fd6f94` and
`canMintRipe() = 0x3b6fccc0`.

The initial implementation harness ran two isolated Foundry tests: one GREEN
capability/burn/mint path and one RIPE capability/mint path. The token mock
deliberately returned `bool` from `mint` and `burn`; the inherited void-return
calls accepted the extra return data.

The independent reviewer then ran 28 passing integration scenarios with the
compiled pools and the real Vyper GREEN, RIPE, and RipeHq contracts. Those
scenarios covered both capability truth tables, the direct RipeHq authorization
path, real mint/burn balance and supply changes, and the relevant inherited
ramp, peer, RMN, decimal, rate-limit, allowlist, pause/blacklist, and ownership
behavior. The isolated harness remains review evidence rather than a committed
repository test package.

The mock gas report measured `releaseOrMint` at 78,813 gas after a preceding
call warmed relevant state and 95,902 gas on a colder path. The harness did not
include the real RipeHq registry/config reads or the OffRamp's before/after
`balanceOf` calls. The cold pool-call figure exceeds the documented 90,000
combined default by 5,902 gas before that omitted work. Automatic execution may
therefore fail with the default configuration; manual execution with a token
gas override is recovery, not acceptable normal service. These figures do not
clear the required Base-fork/testnet full-path and FeeQuoter-configuration
gates.

The pinned Chainlink
[`v1.6 Additional Use Grant`](https://github.com/smartcontractkit/chainlink-ccip/blob/bbab0601244ce58e2ffac0dbc178a80aab1fa4a3/chains/evm/contracts/v1.6-CCIP-License-grants.md)
permits developing, deploying, and operating the token-pool contracts solely
for CCIP integration and use. The `1.6.1` npm tarball includes a BUSL-1.1
`contracts/LICENSE.md` that refers to that grant, but omits the referenced
grant file. Production packaging must retain both files from the exact pinned
source and complete internal license review before deployment.

The earlier
[`examples/ExampleGreenCcipBurnMintPool.vy`](examples/ExampleGreenCcipBurnMintPool.vy)
is retained only as a superseded comparison. The Round-2-reviewed historical
artifact is commit `8147784`, SHA-256
`7f3b46af23b9456869b0a72578d3ae295cbfb8ff112d0f7bddd1d66a4afb1e18`.
The superseded file is frozen byte-for-byte at that artifact and is not
maintained alongside the active design. Its finite ABI/collection bounds,
sixth constructor argument, enabled-zero-rate policy choice, and post-2106
timestamp conversion are not properties of the selected inherited design.

## Ripe token and authorization evidence

### Deployed Base contracts

| Contract | Address | Read-only observations |
| --- | --- | --- |
| GREEN | `0xd1Eac76497D06Cf15475A5e3984D5bC03de7C707` | symbol `GREEN`; 18 decimals; `ripeHq()` returns the address below |
| RIPE | `0x2A0a59d6B975828e781EcaC125dBA40d7ee5dDC0` | symbol `RIPE`; 18 decimals; `ripeHq()` returns the address below |
| RipeHq | `0x6162df1b329E157479F8f1407E888260E0EC3d2b` | registry and token-mint authorization authority |

Both tokens implement standard `transfer` and `transferFrom`. Their burn
function burns the caller's balance; neither token implements `burnFrom`.
Both tokens are also pausable and blacklistable:

- token pause makes `transfer`, `transferFrom`, `mint`, and `burn` revert;
- transfer rejects a blacklisted sender or recipient, and `transferFrom` also
  rejects a blacklisted spender; and
- mint rejects a blacklisted receiver.

Therefore an outbound CCIP transfer fails while its source token is paused, and
an inbound release/mint fails while its destination token is paused or its
receiver is blacklisted. A failed inbound message requires recovery after the
blocking condition is removed; the exact CCIP retry/manual-execution behavior
is included in the question packet for confirmation.

### Direct-caller requirement

The GREEN mint path is:

1. `GreenToken.mint(recipient, amount)` calls
   `RipeHq.canMintGreen(msg.sender)`.
2. `RipeHq.canMintGreen(pool)` first requires the global `mintEnabled` circuit
   breaker to be true.
3. It then requires a nonzero pool address, a registered department, a
   registered configuration that enables GREEN minting, and the pool itself to
   return true from `canMintGreen()`.
4. Only after those checks does the token credit the receiver.

RIPE uses the same path through `RipeHq.canMintRipe` and `canMintRipe()`.
Registration-time validation also calls the configured capability view.
Governance can change `mintEnabled` immediately through
`setMintingEnabled(bool)`; that action has no RipeHq timelock.

Consequences:

- The CCIP token pool must be `msg.sender` in the token's `mint` call.
- A separate mint adapter registered with the corresponding capability could
  technically be authorized by RipeHq because it would become `msg.sender` to
  the token. It is not required and is rejected for this design because it
  adds another mint-critical call and governance surface.
- The GREEN pool must implement `canMintGreen() -> true`; the RIPE pool must
  implement `canMintRipe() -> true`. The implementations should not claim the
  other token capability.
- Functional prerequisite: each deployed pool must be registered in RipeHq and
  have its matching mint permission enabled before CCIP minting can work.
- Ripe policy additionally requires the other token's mint permission to remain
  disabled.
- `setMintingEnabled(false)` is a true chain-local stop for every GREEN and RIPE
  mint authorized by that RipeHq, not only CCIP inbound minting. It also halts
  protocol-native issuance but does not stop outbound burns.

### Interface comparison

| Requirement | Ripe token | Standard Chainlink behavior | Result |
| --- | --- | --- | --- |
| `mint(address,uint256)` | Present; RipeHq-gated; returns `bool` | Called directly on release/mint through a void-return interface | Selector-compatible; the inherited-pool mock test accepted the extra return data |
| `burn(uint256)` | Present; burns caller balance; returns `bool` | Called directly after tokens reach the pool through a void-return interface | Selector-compatible; the inherited-pool mock test accepted the extra return data |
| `burnFrom(address,uint256)` | Absent | Required by `BurnFromMintTokenPool`, not by `BurnMintTokenPool` | Use burn/mint, not burn-from/mint |
| `decimals()` | Present; 18 | Used for remote decimal handling | Compatible |
| `balanceOf(address)` | Present | Used by pool accounting | Compatible |
| `owner()` | Absent | One self-service admin-discovery path | Assisted registration required |
| `getCCIPAdmin()` | Absent | Another self-service admin-discovery path | Assisted registration required |
| Ripe capability view | Token does not supply it; department must | Not present in standard pool | Thin token-specific subclass adds only the two views |
| Global mint circuit breaker | `RipeHq.setMintingEnabled(false)` immediately makes both mint checks return false | Destination release/mint reverts when token mint reverts | Protocol-wide issuance stop for every RipeHq-authorized minter; in-flight recovery must be confirmed and tested |
| Token pause | Transfer, mint, and burn revert while paused | Source transfer/burn or destination mint can fail | True token-wide stop with broader protocol impact |
| Token blacklist | Transfer rejects blacklisted parties; mint rejects blacklisted receiver | Destination mint can fail for a particular receiver | Disclose and test failed-message recovery |

Local source anchors at the recorded track start commit:

- `contracts/tokens/GreenToken.vy:61-64` and
  `contracts/tokens/RipeToken.vy:61-64`: token-to-RipeHq mint checks;
- `contracts/registries/RipeHq.vy:378-424`: mint authorization and immediate
  global circuit breaker;
- `contracts/registries/RipeHq.vy:215-277` and `318-344`: timelocked Hq config
  plus capability revalidation;
- `contracts/registries/modules/AddressRegistry.vy:156-198`: timelocked
  contract-address registration;
- `contracts/tokens/modules/Erc20Token.vy:187-215`, `291-317`, `404-421`, and
  `587-592`: transfer, mint/burn, blacklist, and governance pause behavior;
- `contracts/core/CreditEngine.vy:271-274`,
  `contracts/core/EndaomentPSM.vy:260-270`, and
  `contracts/core/Lootbox.vy:1139-1145`: representative protocol-native GREEN
  and RIPE mint paths affected by the global circuit breaker;
- `interfaces/Department.vyi:9-44`: Ripe's full Department convention; and
- `contracts/config/SwitchboardCharlie.vy:490-496`: generic targeted pause
  action.

As retrieved on 2026-07-23, Chainlink's [token-pool
documentation](https://docs.chain.link/ccip/concepts/cross-chain-token/evm/token-pools)
describes the standard burn/mint pool as fully audited. For custom burn/mint
behavior it recommends inheriting `BurnMintTokenPoolAbstract`. Ripe does not
need different burn/mint behavior, so it now subclasses the concrete standard
`BurnMintTokenPool` and adds only unrelated capability views. This maximizes
code reuse, but the public audit statement does not automatically cover Ripe's
subclass, RipeHq callback, build pin, deployment configuration, or operational
assumptions. Public documentation also does not explicitly establish whether
Chainlink will register, list, monitor, or support this exact thin subclass;
that remains an external question.

## Registration and administration

As retrieved on 2026-07-23, Chainlink's [registration and administration
documentation](https://docs.chain.link/ccip/concepts/cross-chain-token/evm/registration-administration)
says self-service token-admin registration relies on a supported discoverable
administrator exposed through `owner()` or `getCCIPAdmin()`. If the token does
not expose either function, Chainlink directs the developer to its
assisted/manual registration process.

| Chain/token state | Publicly supported path | Remaining confirmation |
| --- | --- | --- |
| Existing immutable Base GREEN and RIPE | Assisted/manual registration | Required evidence, expected reviewer, timing, and any prerequisite agreements |
| Robinhood tokens deployed from unchanged current source | Assisted/manual registration | Whether Chainlink prefers this symmetry or a discovery hook on only the new deployments |
| Robinhood tokens modified to add `getCCIPAdmin()` | Potential self-service on Robinhood only | Whether asymmetric token bytecode is acceptable and who should hold the role |

Adding a discovery hook only to the future Robinhood deployments would create
source and bytecode divergence from the immutable Base tokens. No such token
change is recommended without an explicit decision.

The existing contracts provide an onchain authority chain even though they do
not provide Chainlink's self-service discovery functions:

1. each token exposes `ripeHq()`;
2. that address exposes `governance()`; and
3. the token's `pause(bool)` function accepts only that governance address.

This is candidate proof for assisted registration. If Chainlink requires an
active proof, Ripe governance can provide an owner-approved signature or
non-disruptive demonstration transaction in the form Chainlink specifies. No
such signature or transaction has been produced.

After an administrator is established, public documentation describes these
separate actions:

1. the token administrator accepts the registry admin role;
2. the token administrator associates the local token with its pool;
3. the pool owner applies remote-chain and remote-pool configuration;
4. token permissions allow the pool to burn and mint; for Ripe, this means
   RipeHq department registration and the single corresponding mint flag.

Ripe's own ordering adds two sequential, block-denominated timelocks:

1. the pool must already be deployed with its capability view callable;
2. governance starts and later confirms its addition to the RipeHq address
   registry;
3. only after the registry assigns a valid ID can governance initiate the
   matching Hq config; and
4. governance later confirms that config, at which time RipeHq staticcalls the
   capability view again and cancels an invalid pending config.

Both waits use `registryChangeTimeLock` measured in `block.number`. Robinhood's
documented L2 block-number semantics therefore require a chain-specific timing
test and approved value before pool registration. Chainlink cannot determine
this Ripe-side schedule.

No action above was performed.

## Operational controls and limits

The Chainlink-specific statements below were retrieved from its current public
documentation on 2026-07-23, with the relevant primary page linked in each
item. Ripe-specific controls come from the local source anchors above.

- [CCIP rate
  limits](https://docs.chain.link/ccip/concepts/rate-limit-management/overview)
  are independent token buckets for each pool and lane direction. Changes take
  effect immediately.
- The documented emergency procedure approximates a halt with capacity `1` and
  rate `1` in both directions. It is not a true zero-rate pause, and a minimal
  transfer can still succeed. See [emergency
  actions](https://docs.chain.link/ccip/concepts/rate-limit-management/emergency-actions).
- Ripe has two stronger but broader controls. Governance can immediately call
  `RipeHq.setMintingEnabled(false)` to stop every GREEN and RIPE mint authorized
  by that RipeHq—including CreditEngine borrowing, EndaomentPSM issuance,
  Lootbox rewards, CCIP inbound minting, and other registered minters—while
  pausing a token stops its transfers, burns, and mints on that chain. The
  incident playbook should coordinate these controls with CCIP rate limits and
  explicitly handle in-flight messages.
- Pool ownership controls remote-chain updates and can add a replacement remote
  pool. Current contracts support overlapping old and new pools for in-flight
  upgrades; Chainlink recommends testnet validation and coordinated multi-chain
  upgrades. See [token
  pools](https://docs.chain.link/ccip/concepts/cross-chain-token/evm/token-pools).
- Chainlink v1.6.1's `applyChainUpdates` can completely remove a chain and its
  remote-pool approvals. Its rate-limiter reconfiguration first refills at the
  old rate and then clamps to the new capacity, so an administrator cannot
  restore consumed capacity merely by reapplying a config. The selected
  subclasses inherit both behaviors directly.
- Token-pool execution receives a combined default gas allowance of `90,000`.
  It covers the pre-mint `balanceOf` check, `releaseOrMint`, and the post-mint
  `balanceOf` check. Exceeding it makes destination execution fail; the public
  guidance recommends optimization, permits a one-off manual gas override, and
  directs consistently higher requirements to Chainlink. The custom capability
  check plus RipeHq authorization must fit within a measured budget with margin.
  See [EVM service limits](https://docs.chain.link/ccip/service-limits/evm) and
  [manual execution](https://docs.chain.link/ccip/concepts/manual-execution).
  The inherited-pool mock measured 78,813 gas after warming and 95,902 gas on a
  colder `releaseOrMint` path. It omits the real RipeHq reads and OffRamp
  balance checks, so it is not accepted proof. The cold pool call alone exceeds
  the combined default by 5,902 gas; automatic execution may fail before the
  real path's additional work is counted. Mainnet remains blocked on a Base
  fork measurement through the real OffRamp, Router, RMN proxy, token, and
  RipeHq, followed by testnet evidence and a supported FeeQuoter token overhead
  with margin. The production compiler/EVM settings must remain identical
  across both chains unless a separately approved and reviewed compatibility
  exception is unavoidable.
- If automatic execution fails, any externally owned account can manually
  execute after the documented smart-execution window by supplying gas.
  See [manual execution](https://docs.chain.link/ccip/concepts/manual-execution).
- A CCIP message currently supports one distinct token and up to 30 KB of data,
  with a maximum receiver execution gas limit of 3,000,000. GREEN and RIPE
  transfers should therefore be treated as separate token messages. See [EVM
  service limits](https://docs.chain.link/ccip/service-limits/evm).
- A source-chain CCIP fee combines blockchain and network fees. Unused execution
  gas is not refunded. See [CCIP billing](https://docs.chain.link/ccip/billing).

The recommended administrative split is:

- two-step multisig ownership for each pool;
- a token-admin multisig for Token Admin Registry actions;
- a narrowly scoped incident multisig as `rateLimitAdmin`;
- existing Ripe governance for RipeHq registration and mint enablement;
- no long-lived externally owned account as a production administrator.

The pool owner is an unlimited mint-critical authority in practice. It can
replace the Router, and a malicious Router can designate attacker-controlled
ramps that reach the pool's RipeHq mint permission. Pool ownership therefore
requires at least RipeHq-governance-quality controls. The repository does not
currently establish Safe support on Robinhood; use only an owner-approved
production multisig backend whose deployment and transaction flow have been
proven on that chain.

The repository's `Department.vyi` convention also declares `isPaused()`,
`pause(bool)`, and fund-recovery functions. RipeHq registration does not
runtime-check that full interface; it checks only the enabled mint capability.
The selected subclasses intentionally add only the two required views.
Therefore `SwitchboardCharlie.pause(address,bool)` will revert if aimed at a
pool, and operations must use inherited CCIP controls, RipeHq `mintEnabled`,
or token pause according to the incident scope. Production security review
must accept that minimum-change lifecycle and the global circuit breaker's
wider blast radius.

The exact multisig setup, role-transition sequence, emergency playbook,
monitoring, and manual-execution responsibilities require confirmation.

## Publicly unresolved questions

1. Is a direct subclass of `BurnMintTokenPool` that only adds two pure
   capability views supported for registration, production lanes,
   Directory/monitoring, Token Manager/Expert, and manual execution? Which
   pool/API version should target the `1.6.0` lanes, and are the directory
   `RMN` entries the intended constructor proxies?
2. What assisted-registration evidence, initiator, and sequence apply to
   unchanged Base and Robinhood tokens that expose neither `owner()` nor
   `getCCIPAdmin()`?
3. What destination token-gas overhead is configured, what measurement margin
   is required, and how is a custom
   `TokenTransferFeeConfig.destGasOverhead` approved and applied in FeeQuoter
   configuration if needed?
4. What exact message retry/manual-execution and remote-pool retirement
   procedures apply to Ripe's failure and upgrade cases?

These questions are formatted for external review in
`ccip-chainlink-question-packet.md`. That packet has not been sent.

## Sources

- [Robinhood Chain: Connecting](https://docs.robinhood.com/chain/connecting/)
- [Robinhood Chain: Bridging](https://docs.robinhood.com/chain/bridging/)
- [CCIP directory: Robinhood Chain mainnet](https://docs.chain.link/ccip/directory/mainnet/chain/robinhood-mainnet)
- [CCIP directory: Base mainnet](https://docs.chain.link/ccip/directory/mainnet/chain/ethereum-mainnet-base-1)
- [CCIP directory: Robinhood Chain testnet](https://docs.chain.link/ccip/directory/testnet/chain/robinhood-testnet)
- [CCIP directory: Base Sepolia](https://docs.chain.link/ccip/directory/testnet/chain/ethereum-testnet-sepolia-base-1)
- [CCIP EVM API reference](https://docs.chain.link/ccip/api-reference/evm/v1.6.1/)
- [BurnMintTokenPool API](https://docs.chain.link/ccip/api-reference/evm/v1.6.1/burn-mint-token-pool)
- [BurnMintTokenPool v1.6.1 source](https://github.com/smartcontractkit/chainlink-ccip/blob/contracts-ccip-v1.6.1/chains/evm/contracts/pools/BurnMintTokenPool.sol)
- [CCIP-compatible EVM tokens](https://docs.chain.link/ccip/concepts/cross-chain-token/evm/tokens)
- [EVM token pools](https://docs.chain.link/ccip/concepts/cross-chain-token/evm/token-pools)
- [Registration and administration](https://docs.chain.link/ccip/concepts/cross-chain-token/evm/registration-administration)
- [CCIP Token Manager](https://docs.chain.link/ccip/tools-resources/token-manager)
- [Rate-limit management](https://docs.chain.link/ccip/concepts/rate-limit-management/overview)
- [Emergency actions](https://docs.chain.link/ccip/concepts/rate-limit-management/emergency-actions)
- [Manual execution](https://docs.chain.link/ccip/concepts/manual-execution)
- [EVM service limits](https://docs.chain.link/ccip/service-limits/evm)
- [CCIP billing](https://docs.chain.link/ccip/billing)
- [Service responsibility](https://docs.chain.link/ccip/service-responsibility)
- [Base GREEN contract](https://basescan.org/address/0xd1eac76497D06Cf15475A5e3984D5bC03de7C707)
- [Base RIPE contract](https://basescan.org/address/0x2A0a59d6B975828e781EcaC125dBA40d7ee5dDC0)
- [Base RipeHq contract](https://basescan.org/address/0x6162df1b329E157479F8f1407E888260E0EC3d2b)
