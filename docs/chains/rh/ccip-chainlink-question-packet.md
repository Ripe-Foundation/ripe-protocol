# Chainlink question packet: Base <-> Robinhood Chain Ripe tokens

Status: **DRAFT — NOT SENT — OWNER APPROVAL REQUIRED**

Prepared: 2026-07-23

Recipient and channel: Pending owner selection

External actions taken: None

This is the proposed external question packet. Sending it, submitting a form,
contacting Chainlink, or accepting any terms requires separate explicit owner
authorization.

## Proposed subject

Confirming supported CCIP pool and registration path for GREEN/RIPE on Base and
Robinhood Chain

## Proposed message

Hello Chainlink team,

Ripe is evaluating a minimal CCIP burn/mint bridge for GREEN and RIPE between
Base and Robinhood Chain. We are still in technical confirmation and have not
deployed or registered pools.

The existing Base deployments are:

- GREEN: `0xd1Eac76497D06Cf15475A5e3984D5bC03de7C707`
- RIPE: `0x2A0a59d6B975828e781EcaC125dBA40d7ee5dDC0`
- RipeHq: `0x6162df1b329E157479F8f1407E888260E0EC3d2b`

We see direct Base <-> Robinhood Chain and Base Sepolia <-> Robinhood Chain
Testnet lanes in the CCIP directory, with the lane records reporting version
`1.6.0`. The current public EVM API reference labels contracts-CCIP `1.6.1` as
latest and pins commit
`bbab0601244ce58e2ffac0dbc178a80aab1fa4a3`.

Both Ripe tokens have 18 decimals and expose:

```solidity
function mint(address recipient, uint256 amount) external returns (bool);
function burn(uint256 amount) external returns (bool);
function balanceOf(address account) external view returns (uint256);
function decimals() external view returns (uint8);
```

They do not expose `burnFrom`, `owner`, or `getCCIPAdmin`.

They are pausable and blacklistable. While paused, transfer, mint, and burn
revert. Mint also reverts for a blacklisted receiver, while transfer rejects a
blacklisted sender or receiver. We therefore expect a paused destination token
or blacklisted destination receiver to make CCIP release/mint fail until the
condition is removed.

There is an additional authorization layer. GREEN minting calls
`RipeHq.canMintGreen(msg.sender)`, and RIPE minting calls
`RipeHq.canMintRipe(msg.sender)`. RipeHq first checks its global `mintEnabled`
circuit breaker, then requires the direct mint caller to be a registered
department, have only the corresponding mint permission enabled, and expose the
corresponding view:

```solidity
// GREEN pool only
function canMintGreen() external view returns (bool); // true

// RIPE pool only
function canMintRipe() external view returns (bool); // true
```

The CCIP pool must therefore remain the direct caller of `token.mint`; a
separate mint adapter is not viable. Our proposed shape is:

- one thin GREEN burn/mint pool implementation, deployed on both chains;
- one thin RIPE burn/mint pool implementation, deployed on both chains;
- the standard CCIP burn/mint path unchanged;
- only the appropriate Ripe capability view added to each implementation;
- each pool registered in RipeHq and enabled only for its corresponding token.

Illustrative compatibility layer, with constructor forwarding and the final
Chainlink base class omitted pending your answer:

```solidity
contract GreenTokenBurnMintPool is BurnMintTokenPool {
    function canMintGreen() external pure returns (bool) { return true; }
}

contract RipeTokenBurnMintPool is BurnMintTokenPool {
    function canMintRipe() external pure returns (bool) { return true; }
}
```

Each implementation deliberately omits the opposite mint capability.

Although the tokens lack Chainlink's self-service admin-discovery functions,
they are not ownerless. Each token exposes `ripeHq()`, that RipeHq exposes
`governance()`, and token `pause(bool)` accepts only that governance address.
Subject to owner approval, governance can provide a proof signature or a
non-disruptive demonstration transaction in whatever format your assisted
registration process requires.

Could you please confirm the following?

### Blocking compatibility and pool-design questions

1. Can you confirm that direct token transport is currently supported for both
   Base <-> Robinhood Chain mainnet and Base Sepolia <-> Robinhood Chain
   Testnet, rather than only independent support for each chain?
2. Which exact production and test Router, Token Admin Registry, chain
   selectors, OnRamps, OffRamps, RMN contracts, and other lane-specific
   addresses should we use?
3. Which exact contracts-CCIP release, repository tag or commit, Solidity
   version, and dependency set do you recommend for pools on the live
   Base <-> Robinhood Chain lane?
4. Is a contracts-CCIP `1.6.1` token pool compatible with the directory's
   `1.6.0` lane contracts on both chains?
5. For this minimal extension, do you prefer:
   - subclassing `BurnMintTokenPool` and adding only the corresponding
     capability view; or
   - inheriting `BurnMintTokenPoolAbstract`, retaining the standard direct
     `burn(amount)` and `mint(receiver, amount)` behavior, and declaring a
     custom type/version?
6. Will Chainlink review and support that thin custom pool for production? If
   yes, what review artifacts, test vectors, audit scope, and lead time are
   required?
7. Can the supported implementation remain the direct caller of
   `mint(address,uint256)` while preserving standard CCIP registration,
   monitoring, upgrade, and manual-execution tooling?
8. Please confirm which burn function the recommended pool calls. Is its
   direct `burn(uint256)` call compatible with the tokens' self-burn behavior
   without changing GREEN or RIPE?
9. Ripe's broader Department convention includes `isPaused()`, `pause(bool)`,
   and fund-recovery methods, although RipeHq validates only the enabled mint
   capability. Should this pool implement a Chainlink-approved lifecycle/pause
   surface, or should it remain capability-only and rely on standard CCIP rate
   controls plus Ripe's token and global mint circuit breakers?
10. Are there any Robinhood-specific Router, RMN, pool factory, allowlist,
   decimal, gas, or remote-pool constraints not represented in the public
   directory and EVM pool documentation?

### Registration and administration questions

11. Because the immutable Base tokens expose neither `owner()` nor
    `getCCIPAdmin()`, is assisted/manual Token Admin Registry registration the
    correct path? Is the onchain `token.ripeHq() -> RipeHq.governance()`
    authority chain sufficient, and what additional signature or
    demonstration transaction, contracts, contacts, and review steps are
    required?
12. For newly deployed Robinhood GREEN and RIPE, is self-service registration
    preferred? If so, is `getCCIPAdmin()` required, or can the same portable
    token source use assisted registration on both sides? We do not want a
    Robinhood-only token variant.
13. Ripe must deploy the pool before starting its two-step, block-timelocked
    address registration, then complete a second timelocked Hq-config change
    that rechecks the pool's capability at confirmation. Around that fixed
    Ripe-side sequence, what is Chainlink's required ordering for:

    - establishing token administrators;
    - associating local tokens and pools;
    - applying remote-chain and remote-pool configuration;
    - configuring rate limits; and
    - activating production transfers?
14. Do you support separate multisigs for pool ownership, Token Admin Registry
   administration, and the `rateLimitAdmin` incident role? Are there prescribed
   role-transition or two-step ownership procedures?

### Operations, security, and commercial questions

15. Ripe governance can immediately call `RipeHq.setMintingEnabled(false)`,
    which hard-stops inbound GREEN and RIPE minting on that chain but does not
    stop outbound burns. Token pause is broader and stops transfers, burns, and
    mints. What initial per-token inbound/outbound capacities and refill rates
    do you recommend, and how should those controls be coordinated for a
    guarded launch and emergency response? If an in-flight message fails
    because `mintEnabled` is false, the token is paused, or the receiver is
    blacklisted, what state does it enter and what is the supported retry or
    manual-execution procedure after re-enable?
16. What monitoring, alerting, manual-execution coverage, upgrade coordination,
    incident-response, and support responsibilities should Ripe plan to own?
17. Where is the 90,000 combined token-pool execution gas allowance enforced,
    what measurements and margin should accompany review, and what supported
    configuration or assistance path applies if the RipeHq authorization path
    cannot be kept below it?
18. Beyond public per-message CCIP billing, are there onboarding fees,
    liquidity or volume requirements, recurring fees, support commitments,
    SLAs, audits, security-review requirements, program/deprecation conditions,
    or external terms that apply to this integration?
19. Is there a recommended testnet acceptance checklist before requesting
    mainnet registration?

For an actionable response, it would help if you could identify each answer as
one of:

- confirmed from current production support;
- recommended but optional;
- required before testnet registration;
- required before mainnet registration; or
- subject to a separate commercial/security review.

Thank you.

## Answer-to-decision map

| Answer area | If confirmed / supported | If rejected / required otherwise |
| --- | --- | --- |
| Direct lanes and addresses | Freeze the verified test and production network matrix | Block Track 1; do not infer a multi-hop route |
| Exact release and lane compatibility | Lock the named commit, compiler, and dependency graph | Replace the provisional `1.6.1` candidate before implementation |
| Standard-pool subclass | Add only the appropriate Ripe capability view | Use the accepted abstract/custom form without changing the direct caller |
| Thin pool review/support | Proceed to an implementation and review specification | Block and escalate; do not add an adapter or token fork |
| Direct mint and self-burn compatibility | Keep GREEN, RIPE, and RipeHq unchanged | Block and escalate any required token migration or nonstandard mint authority |
| Department lifecycle surface | Implement only the approved pause/recovery shape | Keep the pool capability-only and document the Switchboard limitation |
| Assisted Base registration | Write the authority-evidence and registration runbook | Block if immutable Base tokens cannot be registered |
| Portable Robinhood registration | Deploy the same canonical token source on both chains | Escalate before any `getCCIPAdmin()` or Robinhood-only source change |
| Configuration order and roles | Freeze the governance transaction and signer matrix | Revise the matrix before preparing transactions |
| Token restrictions and emergency controls | Define rate limits, circuit-breaker order, and in-flight recovery | Keep activation blocked until retry behavior is accepted |
| Gas expectations | Adopt the confirmed measured acceptance threshold | Redesign only within the direct-pool constraint or block |
| Commercial/security requirements | Add the stated budget, review, agreements, and gates | Keep launch blocked until requirements are known |

## Approval gate

Before this packet can leave the repository, the owner must explicitly approve:

1. the exact message text;
2. the named recipient or form;
3. the delivery channel; and
4. the act of sending.

Approval to send this question packet would not authorize accepting terms,
installing dependencies, deploying contracts, changing roles, signing
transactions, or broadcasting transactions.
