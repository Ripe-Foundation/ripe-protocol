# Chainlink technical question packet: GREEN/RIPE on Base <-> Robinhood Chain

Status: **REVISED DRAFT — NOT SENT — FRESH OWNER APPROVAL REQUIRED**

Revised: 2026-07-27

Recipient and channel: Pending owner selection

External actions taken: None

The 2026-07-23 approval applied to an older, materially different packet. This
shortened pure-Vyper version requires fresh approval of the exact text,
recipient, channel, and act of sending. It asks only questions that require
Chainlink's technical or operational knowledge.

## Proposed subject

Pure-Vyper custom CCT pool and assisted registration for GREEN/RIPE on Base and
Robinhood Chain

## Proposed message

Hello Chainlink team,

Ripe is evaluating a direct CCIP burn/mint bridge for GREEN and RIPE between
Base and Robinhood Chain. Nothing has been deployed or registered.

Existing Base deployments:

- GREEN: `0xd1Eac76497D06Cf15475A5e3984D5bC03de7C707`
- RIPE: `0x2A0a59d6B975828e781EcaC125dBA40d7ee5dDC0`
- RipeHq: `0x6162df1b329E157479F8f1407E888260E0EC3d2b`

Both tokens have 18 decimals and expose
`mint(address,uint256) returns (bool)`, `burn(uint256) returns (bool)`,
`balanceOf(address)`, and `decimals()`. They expose neither `owner()` nor
`getCCIPAdmin()`. The tokens are pausable and blacklistable.

The immutable Base token contracts must remain unchanged. The Robinhood token
contracts are not yet fixed and could add a supported Chainlink
admin-discovery interface before deployment if required. The selected pool
design is pure Vyper `0.4.3`, one GREEN pool implementation deployed on both
chains and one RIPE pool implementation deployed on both chains. Each pool
directly calls the token's `burn`/`mint`. Ripe-local authorization makes the
pool a registered minter, but does not change the CCIP ABI.

The reference pool mirrors contracts-CCIP v1.6.1's relevant surface, including:

- `IPoolV1`, `CCIP_POOL_V1`, and ERC-165;
- `applyChainUpdates(uint64[],ChainUpdate[])`;
- `addRemotePool(uint64,bytes)` and `removeRemotePool(uint64,bytes)`;
- singular/plural chain rate-limiter setters and current-state getters;
- enumerable supported chains and remote pools;
- deployment-time optional allowlist mode;
- Router, RMN proxy, decimal conversion, OnRamp/OffRamp, and source-pool
  validation;
- v1.6.1 event parameter types/indexing and security/rate-limit custom-error
  encodings; and
- state-preserving v1.6.1 rate-limit reconfiguration.

Its execution selectors are `lockOrBurn=0x9a4575b9` and
`releaseOrMint=0x39077537`; its administration selectors include
`applyChainUpdates=0xe8a1da17`,
`addRemotePool=0x62ddd3c4`,
`removeRemotePool=0xacfecf91`, and
`setChainRateLimiterConfig=0xcf7401f3`.

One source/documentation mismatch is explicit: the pinned v1.6.1
`RateLimiter.sol` rejects only `rate > capacity`, while the current v1.6.1 API
text says an enabled rate must be nonzero. The Vyper reference follows the
safer documented rule and rejects `rate == 0`; disabled limits use
`(false,0,0)`. The version-compatibility question below includes this mismatch.
The constructor also requires `token.decimals()` to succeed and match the
supplied value; GREEN and RIPE both satisfy that stricter check, while TokenPool
v1.6.1 permits a missing optional decimals method.

We have answered the Ripe-contract questions locally. We need Chainlink's help
only with the following:

1. **Custom-pool eligibility and tooling.** Is a non-Chainlink-derived,
   from-scratch pure-Vyper pool eligible for assisted registration, production
   lane enablement, CCIP Directory listing, monitoring, Token Manager/Expert,
   CCIP tools, and supported manual execution? Beyond `IPoolV1`, which exact
   ABI, event, error, `typeAndVersion`, audit, test, or security-review
   requirements are mandatory for testnet and mainnet?

2. **Pool/lane version compatibility.** For Base <-> Robinhood mainnet and Base
   Sepolia <-> Robinhood testnet, which pool/API release should we target when
   the public directory lane records report core `1.6.0` but the current
   documented pool API is contracts-CCIP `1.6.1`? We have already recorded the
   public selectors, Routers, Token Admin Registries, and directory-listed RMN
   addresses. Please confirm that the directory's `RMN` field is the proxy
   address intended for the v1.6.1 `TokenPool` constructor, and identify any
   non-public lane-specific pool constraints. Please also confirm whether the
   pinned source or current API text controls enabled zero-rate validation.

3. **Assisted Token Admin Registry process.** For the immutable Base tokens,
   which expose neither `owner()` nor `getCCIPAdmin()`, what exact assisted
   `proposeAdministrator` process, proof of authority, initiator, and ordering
   should we use? Can the same assisted path be used for the new Robinhood
   deployments; if not, which exact admin-discovery interface should those
   tokens implement? The onchain authority chain is
   `token.ripeHq() -> RipeHq.governance()`.

4. **Destination token gas.** What `destGasAmount`/token transfer overhead is
   configured for these lanes, and what measurement margin do you require for
   the full OffRamp `balanceOf` + `releaseOrMint` + `balanceOf` path? If the
   measured RipeHq-authorized mint path is too close to or above the default,
   what is the supported process for a custom `destGasOverhead`?

5. **Failure and upgrade operations.** When destination minting reverts because
   RipeHq minting is disabled, the token is paused, or the receiver is
   blacklisted, what exact CCIP message state and retry/manual-execution
   procedure applies after recovery? For remote-pool upgrades/removal, which
   monitoring or waiting procedure establishes that no in-flight message will
   be stranded?

For each answer, please identify whether it is:

- required before testnet;
- required before mainnet;
- recommended but optional; or
- unsupported.

Thank you.

## Why no other questions are included

Ripe can answer these items locally and should not ask Chainlink to reverse
engineer them:

- how `RipeHq.canMintGreen/canMintRipe` works;
- whether the pool is the direct token mint caller;
- whether a separately registered mint adapter could technically work;
- how RipeHq's two timelocks and capability checks operate;
- which Vyper bounds, allowlist policy, Department lifecycle surface, or
  governance roles Ripe chooses; and
- whether GREEN/RIPE need token-contract changes. They do not under the
  assisted-registration design.

## Answer-to-decision map

| Chainlink answer | Ripe consequence |
| --- | --- |
| Pure-Vyper custom pool supported with stated requirements | Freeze the mandatory surface and write the production implementation/audit specification |
| Pure-Vyper pool unsupported | Stop and return to the owner; do not add an adapter or change token contracts implicitly |
| `1.6.1` pool/API compatible with the live lanes | Freeze the exact source/API reference and differential-test oracle |
| Different release required | Rebase the reference and repeat selector/event/error/runtime review |
| Assisted registration available on both chains | Keep Base and Robinhood token bytecode source-equivalent |
| Token admin hook required on Robinhood | Stop for an owner decision between the smallest pre-deployment Robinhood change and the existing shared-source policy; do not alter or migrate Base implicitly |
| Token admin hook required on Base | Stop; any Base migration or live-version divergence requires a separate owner decision |
| Current gas overhead has adequate measured margin | Keep the standard lane configuration |
| Custom overhead required or unavailable | Obtain the supported configuration or redesign/block before activation |
| Retry/upgrade procedure confirmed | Encode it in testnet acceptance and the incident runbook |

## Approval gate

Do not send this packet, select a recipient on the owner's behalf, submit a
form, accept terms, deploy, register, or broadcast a transaction without fresh
explicit authorization.
