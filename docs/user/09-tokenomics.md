# RIPE Tokenomics: Where Early Believers Win Big

Every DeFi token promises "fair distribution." Then VCs dump on retail.

RIPE flips the script. Community gets tokens first. Team waits a year. Early backers paid 2 cents while builders self-funded development. Now 250 million RIPE flows to users who actually use the protocol.

One small seed round at $0.02 after 2+ years of building. Just builders who bet their own money and users who show up early.

> **📊 Tokenomics at a Glance**
>
> - **Fixed supply**: 1B RIPE (mint beyond cap only if RIPE Bonds are triggered to cover bad debt)
> - **Community first**: 25% of supply goes to user incentives; this is the only bucket that begins unlocking at TGE via block rewards & bonding
> - **All unlocks on-chain**: Immutable vesting contracts you can audit today

For a deep dive into how RIPE powers the protocol—including [staking rewards](06-ripe-rewards.md), protocol fees via [sGREEN](04-sgreen.md), [governance participation](08-governance.md), and treasury building through [bond sales](10-bonds.md)—explore these detailed guides. Full onchain governance will launch post-TGE once the community owns sufficient supply.

## Token Allocation: Community-First Distribution

The 1 billion RIPE supply is allocated across five key stakeholder groups, with the largest portion dedicated to community incentives:

![RIPE Token Allocation](https://miro.medium.com/v2/format:webp/1*2OWDZIl3gjqJl_B6JXyyaw.png)

### Community Incentives (25% - 250M RIPE)

Block rewards, bonding discounts, and LP rewards that directly incentivize protocol usage and growth. This is the only allocation that begins distributing at TGE.

### Ripe Foundation Treasury (22.2% - 222M RIPE)

Long-term liquidity provisions, strategic partnerships, ecosystem grants, and marketing initiatives to ensure protocol sustainability.

### Core Contributors (20.6% - 206M RIPE)

Compensation for 2.5 years of full-time protocol development already completed, plus ongoing development through the 4-year vesting period, ensuring the team remains committed to building and improving the protocol.

### Distribution Partner - Hightop (15% - 150M RIPE)

Strategic partner providing mobile on-ramps and fiat bridges to bring Ripe Protocol to mainstream users beyond crypto natives.

### Early Backers (17.2% - 172M RIPE)

Seed investors who provided capital and strategic guidance during testnet development, helping accelerate the path to mainnet launch.

## Emission Schedule: Sustainable Token Release

![RIPE Emission Schedule](https://miro.medium.com/v2/format:webp/1*_cx_OWu-kZAygnVZeLI5Cw.png)

### Hard Cap with Emergency Provision

The RIPE supply is strictly capped at 1 billion tokens with one carefully designed exception: if the protocol ever needs to cover bad debt that exceeds treasury reserves, it can auction [RIPE Bonds](10-bonds.md) to raise funds. These emergency tokens would be minted beyond the cap, transparently diluting all holders to socialize losses fairly.

### Vesting Schedules by Category

Community Incentives stand alone as the only allocation unlocking from day one, ensuring immediate protocol activity:

**Community Incentives (Unlocking Now)**

- **First Unlock**: Immediate at TGE
- **Release Length**: 5+ years
- **Pattern**: Dynamic distribution via block rewards, bonding discounts, and governance

**Core Contributors (Locked First Year)**

- **First Unlock**: 12 months from TGE
- **Total Length**: 4 years
- **Release Pattern**: 25% unlocked at month 12, then linear vesting over 36 months
- **Example**: A contributor with 1M RIPE allocation receives 250K at month 12, then ~694 RIPE per day

**Ripe Foundation, Distribution Partner & Early Backers (Aligned Schedules)**

- **First Unlock**: 12 months from TGE
- **Total Length**: 3 years
- **Release Pattern**: 33% unlocked at month 12, then linear vesting over 24 months
- **Example**: An early backer with 1M RIPE receives 330K at month 12, then ~931 RIPE per day

## Early Backers: Bootstrap to Launch

### Capital Efficiency Through Self-Funding

Ripe Protocol represents a new model for DeFi development—bootstrapped primarily by its builders. Since committing [full-time](https://medium.com/hightop/hightop-sunset-ripe-sunrise-b2559ff9a7e4) to the protocol, the team has deployed $1.87M in capital:

**Core Contributor Funding**: $1.32M

- Self-funded by the founding team
- Covered operational expenses, legal structure, and security audits
- Demonstrates deep personal commitment to the protocol's success

**Seed Round**: $550K (February 2025)

- Raised via Ripe Foundation at $0.02 per RIPE
- Implied fully diluted valuation: $20M
- First external capital after 2+ years of development
- Funds ongoing operational expenses and launch preparation

### Strategic Seed Investors

The seed round brought together a carefully selected group of strategic partners who share the vision for sustainable DeFi:

**Institutional Partners**

- **[OrangeDAO](https://www.orangedao.xyz/)**: YCombinator alumni network (also advisor allocation)
- **[Big Brain](https://www.bigbrain.holdings/)**: Crypto-Native VC
- **[Tetranode](https://x.com/Tetranode)**: Prominent DeFi investor/whale

**Individual Strategic Investors**

- **Sid Krommenhoek**: Partner at [Album VC](https://www.album.vc/)
- **Stephen McKeon**: Partner at [Collab+Currency](https://www.collabcurrency.com/)
- **Trevor Koverko**: Founder of [Sapien](https://www.sapien.io/)
- **Doug Leonard**: Founder of [HiFi Finance](https://hifi.finance/)
- **AJ Taylor**: Founder of [Etherfuse](https://www.etherfuse.com/)

These early supporters bring diverse perspectives from across DeFi, helping guide the protocol's development while sharing in its long-term success through aligned vesting schedules.

## How Vesting Works: Immutable Smart Contracts

### Smart Contract Automation

Unlike traditional vesting that relies on lawyers and spreadsheets, Ripe Protocol enforces all token distributions entirely onchain. Each contributor, foundation member, and investor receives a personalized smart contract that:

- **Automatically calculates** vested tokens using linear formulas
- **Enables claiming** anytime after cliff periods pass
- **Locks tokens** in governance vault for continued participation
- **Enforces terms** immutably without any manual intervention

### The Vesting Process

**1. Token Release**

```
Vested Amount = Total Allocation × (Time Elapsed / Vesting Duration)
```

Tokens vest continuously—every block brings contributors closer to their full allocation.

**2. Claiming Tokens**

- Contributors can claim vested RIPE anytime (daily, monthly, or in bulk)
- Claimed tokens are minted and deposited into the [Governance Vault](08-governance.md)
- Tokens remain locked but gain full voting power immediately

**3. Unlocking for Transfer**

- After the unlock period (varies by group), tokens become transferable
- Two-phase security process: initiate → wait → confirm
- Protects against compromised accounts and hasty decisions

### Transparency & Security

Every vesting contract is visible onchain, allowing anyone to verify:

- Total allocation and vesting schedule
- Tokens claimed vs. remaining
- Exact unlock dates
- No hidden terms or backdoors

The protocol can freeze contracts in emergencies but cannot steal vested tokens. If someone leaves early, unvested tokens return to treasury while vested amounts remain claimable—ensuring fairness for all parties.

_For deep technical details on the vesting system, see the [Contributor contract documentation](../technical/modules/Contributor.md)._

## The Bottom Line: Own the Future, Not the Hype

RIPE isn't another VC exit scam dressed up as "community ownership."

Founders self-funded for 2.5 years. Locked for another year after launch. Early backers paid real money at a fair price. Every token unlock happens on-chain where you can audit it.

But here's what matters: 250 million RIPE goes to users. Not eventually. Now. Through [block rewards](06-ripe-rewards.md) that started at TGE. Through [bonds](10-bonds.md) that let you buy at discounts. Through actual usage, not Twitter campaigns.

The protocol that wins is the one that survives. The one that survives is the one people own.

Your move.
