# Shared Stock Token Vault-Change Specification

Status: **owner-checkpoint draft — Phases A–C complete; Phases D–K intentionally
not finalized**

Date: 2026-07-23 (America/Denver)

This document is the Track 8 working specification required by
`track-8-stock-token-vault-change.md`. It records the evidence reconciliation,
formal state and invariant model, architecture comparison, and mandatory early
owner checkpoint. It does not select a production vault, approve a
loss-allocation policy, authorize a Base migration, or authorize implementation.

Until the owner selects a direction, the operative conclusion is:

> **Do not list Stock Tokens under the current vault designs.**

## 1. Scope, branch, and starting state

- Integration repository: `/Users/wigglez/dev/ripe-protocol`
- Track worktree:
  `/Users/wigglez/dev/ripe-protocol-track-8-stock-token-vault-change`
- Branch: `rh-track-8-stock-token-vault-change`
- Starting branch: `rh`
- Starting commit:
  `be6a759e15e763b633feefdce91cf8f3ee31a10e`
  (`docs: add Robinhood vault change track brief`)
- Starting integration worktree: clean
- Track worktree at bootstrap: clean
- Current Track 5 decision:
  `conditional — shared vault change specification required`
- Production code, interfaces, tests, mocks, defaults, migrations, manifests,
  ABIs, dependencies, CI, generated artifacts, and `rh-summary.md`: unchanged by
  Track 8
- Push, merge, deployment, live configuration, and transaction actions: not
  performed

Parallel Track 6 S1, Track 6 S2, and Track 7 implementation outputs were not
integrated at the starting commit. After this worktree was created, integration
`rh` advanced to `ce3805d6079ee87d727486ea82b75cbddc12e46d`; that commit records
owner approval of the narrow S1/S2 kickoff choices, but does not integrate
their implementation outputs. Future implementation interfaces therefore
remain `pending`; no floating worktree or unmerged commit is treated as
authority.

### 1.1 Bootstrap command record

The following results were captured before creating the Track worktree:

```text
git -C /Users/wigglez/dev/ripe-protocol status --short --branch
=> ## rh...origin/rh

git -C /Users/wigglez/dev/ripe-protocol rev-parse rh
=> be6a759e15e763b633feefdce91cf8f3ee31a10e

git -C /Users/wigglez/dev/ripe-protocol show \
  rh:docs/chains/rh/track-8-stock-token-vault-change.md
=> present

git -C /Users/wigglez/dev/ripe-protocol show-ref --verify \
  refs/heads/rh-track-8-stock-token-vault-change
=> exit 1; branch absent

test -e /Users/wigglez/dev/ripe-protocol-track-8-stock-token-vault-change
=> exit 1; path absent
```

The contract-prescribed creation command and immediate verification were:

```text
git -C /Users/wigglez/dev/ripe-protocol worktree add \
  -b rh-track-8-stock-token-vault-change \
  /Users/wigglez/dev/ripe-protocol-track-8-stock-token-vault-change rh
=> worktree created at be6a759

git -C /Users/wigglez/dev/ripe-protocol-track-8-stock-token-vault-change \
  status --short --branch
=> ## rh-track-8-stock-token-vault-change
```

### 1.2 Documentation-only validation record

Before staging, each untracked deliverable was checked independently:

```text
git diff --no-index --check /dev/null \
  docs/chains/rh/stock-token-vault-change-specification.md
=> no whitespace diagnostics; exit 1 only because the new file differs from
   /dev/null

git diff --no-index --check /dev/null \
  docs/chains/rh/stock-token-vault-change-validation-plan.md
=> no whitespace diagnostics; exit 1 only because the new file differs from
   /dev/null

git status --short
=> ?? docs/chains/rh/stock-token-vault-change-specification.md
   ?? docs/chains/rh/stock-token-vault-change-validation-plan.md
```

The final staged-file scope and `git diff --cached --check` result are recorded
by the local checkpoint-draft commit; no non-document file is permitted in that
commit.

## 2. Evidence ledger

### 2.1 Primary evidence hashes

| Evidence | Commit provenance | SHA-256 at starting commit |
| --- | --- | --- |
| `docs/chains/rh/stock-token-vault-comparison.md` | `758f45f5455fd7c05b25533d2d748769bcfc49c2` | `2a1f01acc843f95fb94329f2451d18dd77db3142a5c9a1977b610ca2805c23da` |
| `docs/chains/rh/stock-token-vault-decision.md` | `758f45f5455fd7c05b25533d2d748769bcfc49c2` | `8dd7eee20dca17fcc367c3debf48ae0e2ce9598748c55ec2e7152beb89918629` |
| `docs/chains/rh/stock-token-vault-fix-recommendations.md` | `221122658f10b4241011e5e4e0d4faaa65ae7de1` | `c1ef4d58bce5b54f330d27228f5b583fe291661adb220cbcc5c0699b78d6b877` |
| `contracts/mock/MockStockTokenControls.vy` | `d8f11e9e3330e2c490ae5b14d5ef2bc186208dfc` | `5d1527262aad66642a6e0f6dfdaad03458abdc4085a0445ebff0af8969614ef7` |
| `tests/vaults/test_stock_token_vault_comparison.py` | `05940a5273cb7ff625ad0dc9bfb5ddc52c22844d` | `1f3723db14349f30a8b4990c8c993ef1a6add65c5b798871c86192aa7cd08c6c` |
| `docs/chains/rh/component-matrix.md` | `758f45f5455fd7c05b25533d2d748769bcfc49c2` | `9f4f33785d577461d17f89f0831e8e88b339e160509a4589e16bc5967364f2ec` |
| `docs/chains/rh/stock-token-transferability-evidence.md` | `72fbc300752e6f14db97ca16da7bbf75945eb3f8` | `01d7441e7338924316fcb14d159689625f83f0db35384a1c3d0ec56c27b22ba6` |
| `docs/chains/rh/block-number-inventory.md` | `4408aa2184cfa80e8f0fed5482397856a9aedfb7` | `3f111accff58e51b91986f134df6d15ed7401d692ef0cca28b2cafb1c89ad2d4` |
| `docs/chains/rh/shared-block-clock-specification.md` | `c3040041a1254a774e0a305060330d6ab9cc04ca` | `98a8afb992cedb749543d986544504c42c7e9b0d57ec2eb72154ea5dad95fb8d` |
| `docs/chains/rh/block-clock-validation-plan.md` | `fc3382c043e026a45eb411142ba6f4918d195aae` | `e3f5d73fa9588aba28ac8823b74c5d523d1e0e6451d29d47f352a87fe03371f2` |
| `migration_history/base-mainnet/v1/current-manifest.json` | `cbf7ea8264abbf81ea2becd616c8d79843a44b0f` | `06ac6dcf3d5c3d2366bd33118023fd6603fc4d759a7a5103901b29ae67007b00` |

### 2.2 Comparison-suite result

Commands were run unmodified from the Track worktree:

```text
PYTHONPATH=. pytest --collect-only -q \
  tests/vaults/test_stock_token_vault_comparison.py
=> 90 tests collected in 0.16s

PYTHONPATH=. pytest -q \
  tests/vaults/test_stock_token_vault_comparison.py
=> 90 passed in 51.98s
```

The actual integrated count is therefore 90, not an inherited point-in-time
count.

After incorporating checkpoint-review feedback, the same unchanged suite was
run again from the same pinned worktree:

```text
PYTHONPATH=. pytest -q \
  tests/vaults/test_stock_token_vault_comparison.py
=> 90 passed in 53.85s
```

### 2.3 Claim labels

- **Tested:** directly asserted by the 90-case integrated Track 5 suite.
- **Source-traced:** follows from current source and caller/callee ordering.
- **Live-verified:** read from the committed Base manifest plus read-only Base
  RPC at a pinned block.
- **Derived:** a consequence of tested/source/live facts, but not itself an
  executed test.
- **Pending:** requires owner policy, unintegrated S1/S2/Track 7 work, audit, or
  future implementation evidence.

## 3. Evidence and source delta report

### 3.1 Track 5 evidence to starting commit

The source delta from the integrated test-evidence commit
`05940a5273cb7ff625ad0dc9bfb5ddc52c22844d` to the Track 8 starting commit adds
Track 2 probe contracts/tests/scripts, Track 3/6/7/8 documents, and two probe or
migration-tool helpers. It also refines the Track 5 evidence documents.

No production vault, common Vault interface, Teller, CreditEngine,
AuctionHouse, Deleverage, Lootbox, Ledger, MissionControl, VaultBook,
Switchboard, or deployed-default source changed in that range. In particular,
all of the following behavioral inputs are unchanged:

- `BasicVault`, `SharesVault`, `SimpleErc20`, `RebaseErc20`, `StabVault`,
  `VaultData`, `StabilityPool`, and `RipeGov`;
- `Vault.vyi` and `ConfigStructs.vyi`;
- `Teller`, `TellerUtils`, `CreditEngine`, `AuctionHouse`,
  `AuctionHouseNFT`, `Deleverage`, `Lootbox`, and `CreditRedeem`;
- `Ledger`, `MissionControl`, `VaultBook`, and `RipeHq`;
- Switchboards Alpha, Bravo, Charlie, and Delta; and
- `DefaultsBase`.

Disposition: **no invalidating production-source delta**. The Track 5 suite was
nevertheless rerun rather than assumed.

### 3.2 Current behavior reconciliation

| Claim | Classification | Current result |
| --- | --- | --- |
| Simple total issuer burn leaves nominal user balances and borrowing amount | Tested | Reproduced by the suite; custody can be zero while nominal collateral remains positive. |
| Simple internal auction after total burn can charge GREEN and move a nominal buyer claim | Tested | Reproduced; the token never leaves the vault because the settlement mode only changes nominal ownership. |
| Rebase partial loss reprices live claims pro rata | Tested and source-traced | Current share conversion follows live `balanceOf(vault)`. |
| Rebase total loss with nonzero shares blocks withdrawal/internal transfer | Tested and source-traced | `_calcWithdrawalSharesAndAmount` asserts live balance is nonzero. Safety may hold by revert, but debt-resolution liveness is absent. |
| Rebase fresh deposit after zero custody with old shares is unsafe | Tested and source-traced | For an ordinary fully received deposit `R` after `C=0`, current code observes `totalAssetBalance=R`, sets `depositAmount=R`, and derives `prevTotalBalance=R-R=0`. `_amountToShares` then divides by the `+1` virtual balance and mints approximately `R × (old S + 10^8)` shares, heavily diluting the old shares without an approved recapitalization policy. |
| Later short-received deposit is reported/credited as requested in both paths | Tested and source-traced | Teller transfers the requested amount, then the vault infers receipt from total balance rather than measuring the call delta. |
| External auction transfer failure is atomic | Tested and source-traced | Vault transfer reverts before `_buyFungibleAuction` sends GREEN or calls debt repayment. |
| Paused internal settlement can still charge GREEN | Tested | Internal balance transfer does not exercise token transferability. |
| Total loss has no automatic exactly-once user-debt-to-bad-debt transition | Source-traced | Ledger exposes a Switchboard `setBadDebt` overwrite, but no current loss path atomically removes the same liability from user debt and increments protocol bad debt. |
| Per-asset collateral-use safety flag exists | Source-traced | False. `AssetConfig` has deposit, withdrawal, redemption, and auction flags plus LTV; borrowing is controlled globally. |

The evidence does not prove that every ordinary ERC-20 can spontaneously lose
vault custody. It proves what happens if custody falls independently of Ripe
accounting and that current deposit accounting can itself create an accounted
deficit after a short receipt.

### 3.3 Post-bootstrap integration delta

During Track 8 work, integration `rh` advanced from the mandated starting commit
`be6a759` to `ce3805d`. The later commit changes only:

- `docs/chains/rh-summary.md`; and
- `docs/chains/rh/shared-block-clock-specification.md`.

It records owner-approved checklist reconciliation and S1/S2 kickoff decisions.
It does not change any vault/protocol source, Track 5 comparison test or mock,
Base manifest, or Track 8 production assumption. The deployable Stock Token
vault path remains unchecked. The Track 8 worktree intentionally remains pinned
to `be6a759`; it was not rebased or moved after the checkpoint contract was
started.

## 4. Current consumer and ordering trace

### 4.1 Deposit

1. `Teller._deposit` resolves the vault and calls
   `TellerUtils.validateOnDeposit`.
2. Validation reads `getVaultDataOnDeposit` before transfer and applies user and
   global limits to the requested/available amount.
3. Teller executes `transfer` or `transferFrom` to the vault.
4. Teller calls the selected vault's deposit function with the pre-transfer
   amount.
5. The vault returns an amount; Teller then registers vault participation,
   updates Lootbox points, optionally performs housekeeping, records a price
   snapshot, emits `TellerDeposit`, and returns that vault-returned amount.

`BasicVault` sets
`depositAmount = min(passedAmount, IERC20(asset).balanceOf(vault))` and credits
that amount. The clamp is against aggregate post-transfer custody, not the
current call's delta, so prior custody can make a short-received call appear
fully received.
`SharesVault` observes the entire post-transfer balance and computes
`prevTotalBalance = totalAssetBalance - depositAmount`, where
`depositAmount = min(requested, totalAssetBalance)`. A prior donation can affect
the conversion base, and a later short receipt remains indistinguishable from
the requested amount. The same Teller entry point is also used for trusted
Stability Pool and RipeGov flows, so a future measurement boundary must
disposition those semantics explicitly. Selecting that boundary is Phase D and
is not done at this checkpoint.

### 4.2 Credit and debt health

`CreditEngine._getUserBorrowTerms` enumerates Ledger user vaults, then each
vault's user assets. It skips an entry when the returned asset is zero **or the
returned amount is zero**. It fetches debt terms, skips zero-LTV assets, values
the amount, and constructs weighted terms using max-debt weight.

Consequences:

- Simple returns nominal amounts even during an aggregate custody deficit, so
  missing custody can support borrowing.
- Merely changing the Simple amount view to zero is not sufficient. The zero
  entry is skipped, which can remove its liquidation threshold and borrow-rate
  weight. Existing debt may then appear healthy, have zero liquidation
  threshold, or become non-progressing unless a separate deficit signal is
  propagated.
- `canBorrow` is global. LTV is an economic parameter, not an immediate,
  custody-independent, per-asset safety switch.
- Debt is account-level; current storage does not attribute an exact slice of
  user debt to a particular collateral asset.

Repayment remains separately callable and must remain available while a
deficit or resolution freeze exists.

### 4.3 Auction settlement

`AuctionHouse._buyFungibleAuction` calculates a maximum collateral value and
calls `_transferCollateral` before taking payment:

- internal mode calls `Vault.transferBalanceWithinVault`, adds the buyer's vault
  participation, and updates buyer rewards; or
- external mode calls `Vault.withdrawTokensFromVault` to deliver the token to
  the recipient.

Only after a nonzero amount and USD value return does AuctionHouse transfer
GREEN to CreditEngine and call `repayDuringAuctionPurchase`. Therefore an
external token-transfer revert rolls back settlement. The unsafe case is the
internal mode: Simple can return a positive nominal amount without proving
custody is live or externally deliverable.

Active auction state is stored in Ledger and is removed when a position reports
depletion. No reservation ledger prevents two nominal claims from referring to
the same remaining aggregate custody after a loss.

### 4.4 Deleverage

The applicable path is external delivery through
`AuctionHouse.withdrawTokensFromVault`. It calculates credited USD value from
the amount the vault reports delivered. This is atomic if the token transfer
reverts. At total live-custody loss, however, the path returns or reverts
without creating repayment value. That preserves payment safety but is a debt
resolution dead end; it is not an exactly-once bad-debt transition.

### 4.5 Rewards and monitoring units

- `Lootbox.updateDepositPoints` reads raw share weight through
  `getUserLootBoxShare`; `SharesVault` returns raw shares divided by
  `DECIMAL_OFFSET`.
- Global asset value reads `getTotalAmountForVault`; `SharesVault` returns live
  custody, while Simple returns nominal total accounting.

Raw shares, token-denominated live claim, and global live value are distinct
units. Any permanent share path must keep those units explicit rather than
silently using one as another.

### 4.6 Registry, deregistration, and recovery

- `VaultBook.startAddressUpdateToRegistry` and
  `startAddressDisableInRegistry` reject a vault whose
  `doesVaultHaveAnyFunds()` returns true.
- `VaultData.deregisterVaultAsset` refuses while its persisted aggregate
  balance is nonzero.
- Vault recovery requires the asset to be unregistered and persisted total
  accounting to be zero.

Therefore a funded Base vault cannot be casually replaced in the registry.
Loss can also leave persisted nominal/share state that blocks deregistration
and recovery even when live custody is zero.

### 4.7 Standing Stock Token configuration constraints

These constraints carry forward unchanged into every architecture outcome and
future implementation/validation phase:

- Stock Token deposits, borrowing, and auction purchases remain disabled until
  the selected shared behavior, exact-token tests, live transferability gate,
  migration, and owner approvals close.
- `AssetConfig.canRedeemCollateral` remains `false`; the resulting
  `MissionControl.getRedeemCollateralConfig()` view must also report the asset
  disabled so CreditRedeem cannot extract Stock Tokens.
- `shouldSwapInStabPools` remains `false` unless governance separately and
  explicitly accepts Stability Pool custody of issuer-controlled collateral.
- Stock Tokens do not route through Base treasury, Endaoment partner liquidity,
  Curve, Aerodrome, Underscore, yield, or any unsupported integration.
- Issuer-controlled treatment remains generic and per-asset; no token-name,
  issuer-name, Robinhood-only, or `chain.id` behavior branch is permitted.

These are standing constraints, not open architecture conveniences. A future
proposal that changes one must return to the owner rather than silently
expanding scope.

### 4.8 AuctionHouseNFT disposition

`AuctionHouseNFT` (`CM-027`) is a temporary Department stub with no fungible or
NFT settlement functions and no calls to the common Vault interface. It does
not consume deposit, amount, internal-transfer, or withdrawal behavior traced
for fungible Stock Tokens. It is therefore **reused unchanged / inapplicable**
to the Track 8 fungible path unless a future NFT implementation introduces a
common Vault consumer; that would require a fresh disposition.

## 5. Live Base exposure

### 5.1 Verification boundary

Committed manifest addresses:

- `VaultBook`: `0xB758e30C14825519b895Fd9928d5d8748A71a944`
- `SimpleErc20`: `0xf75b566eF80Fde0dEfcC045A4d57b540eb43ddfD`
- `RebaseErc20`: `0xce2E96C9F6806731914A7b4c3E4aC1F296d98597`

Read-only Base RPC was pinned to:

- block: `49,036,674`
- block hash:
  `0x030f624ed01a4d2f6eca29774fca774570c2ff0eae80c9ecbaff0cf3381c86e0`
- timestamp: `2026-07-24T03:11:35Z`
- `VaultBook.getAddr(3)`: the manifested `SimpleErc20`
- `VaultBook.getRegId(SimpleErc20)`: `3`
- `VaultBook.getRegId(RebaseErc20)`: `4`
- Simple runtime code hash:
  `0x1d0ec56e109e264dad4435b772deec0026167d96acdb036c51e8b88909b34eb7`
- Rebase runtime code hash:
  `0x21f30af51f5b541329d1e82429851c237a379c07750389810676cccc3f79bef4`
- `SimpleErc20.getNumVaultAssets()`: `27`
- `SimpleErc20.doesVaultHaveAnyFunds()`: `true`
- `RebaseErc20.getNumVaultAssets()`: `6`
- `RebaseErc20.doesVaultHaveAnyFunds()`: `false`

The control-surface assessment also used verified Base Blockscout source/ABI
metadata retrieved on 2026-07-23 America/Denver. Explorer metadata is dated
public evidence, not a historical proof of every role holder or every possible
future implementation.

### 5.2 Registered assets and custody

`C` is live token `balanceOf(SimpleErc20)` and `N` is
`SimpleErc20.totalBalances(asset)`, both in raw token units at the pinned block.

| # | Asset | `C / N` | Dated control-surface assessment |
| ---: | --- | ---: | --- |
| 1 | USDC `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` | `0 / 0` | Verified `FiatTokenProxy`; upgrade, pause, blacklist, mint, and burn surfaces. Current burn semantics are not proof of arbitrary vault burn, but upgrade/freeze/short-receipt risk is present. |
| 2 | cbBTC `0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf` | `1,356,929 / 1,356,929` | Verified `FiatTokenProxy`; same controlled/upgradeable surface. Funded. |
| 3 | WETH `0x4200000000000000000000000000000000000006` | `1,149,627,914,921,567,448 / 1,149,627,914,921,567,447` | Verified fixed `WETH9`; no issuer burn, rebase, fee, or upgrade control found. One raw-unit donation/surplus, not a deficit. |
| 4 | cbDOGE `0xcbD06E5A2B0C65597161de254AA074E489dEb510` | `14,500,000,000 / 14,500,000,000` | Verified `FiatTokenProxy`; controlled/upgradeable. Funded. |
| 5 | uSOL `0x9B8Df6E244526ab5F6e6400d331DB28C8fdDdb55` | `823,425,136,048,272,240 / 823,425,136,048,272,240` | Verified beacon proxy with upgrade, blacklist, mint, and burn surfaces. Funded. |
| 6 | Morpho Spark USDC `0x7BfA7C4f149E7415b73bdeDfe609237e29CBF34A` | `0 / 0` | Verified non-proxy MetaMorpho vault. Owner fee/skim controls and underlying loss can reduce share value; no direct holder-share confiscation was established. |
| 7 | AERO `0x940181a94A35A4569E4529A3CDfB74e38FD98631` | `91,859,213,070,865,428,334 / 91,859,213,070,865,428,334` | Verified fixed token with minter surface; no holder-balance burn, rebase, fee, or upgrade control found. Funded. |
| 8 | Moonwell AERO `0x73902f619CEB9B31FD8EFecf435CbDf89E369Ba6` | `0 / 0` | Verified delegator/implementation architecture with admin implementation change and seize surface. Share value can change; upgrade risk exists. |
| 9 | cbXRP `0xcb585250f852C6c6bf90434AB21A00f02833a4af` | `0 / 0` | Verified `FiatTokenProxy`; controlled/upgradeable. |
| 10 | WELL `0xA88594D404727625A9437C3f886C7643872296AE` | `11,986,269,878,969,919,127,060 / 11,986,269,878,969,919,127,060` | Verified transparent proxy with upgrade, pause, mint, and burn surfaces. Funded. |
| 11 | VIRTUAL `0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b` | `1,054,012,762,792,834,343,376 / 1,054,012,762,792,834,343,376` | Verified Optimism mintable bridge token with privileged mint/burn surface. Funded. |
| 12 | VVV `0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf` | `0 / 0` | Verified fixed token with owner/mint surface; no holder-balance burn, rebase, fee, or upgrade control found. |
| 13 | DEGEN `0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed` | `0 / 0` | Verified fixed token with pause and self/allowance burn surfaces; no arbitrary holder-balance reduction established. |
| 14 | Moonwell cbETH `0x3bf93770f2d4a794c3d9EBEfBAeBAE2a8f09A5E5` | `0 / 0` | Verified delegator/implementation architecture; upgrade and seize surfaces; share-value loss remains possible. |
| 15 | cbETH `0x2Ae3F1Ec7F1F5012CFEab0185bfc7aa3cf0DEc22` | `800,000,000,000,000,000 / 800,000,000,000,000,000` | Verified upgradeable bridge-token proxy with privileged mint/burn surface. Funded. |
| 16 | Moonwell USDC `0xEdc817A28E8B93B03976FBd4a3dDBc9f7D176c22` | `0 / 0` | Verified delegator/implementation architecture; upgrade and seize surfaces. |
| 17 | Morpho Moonwell USDC `0xc1256Ae5FF1cf2719D4937adb3bbCCab2E00A2Ca` | `0 / 0` | Verified non-proxy MetaMorpho vault; share value can fall through underlying loss; owner fee/skim surfaces do not by themselves prove holder-share confiscation. |
| 18 | Morpho Seamless USDC `0x616a4E1db48e22028f6bbf20444Cd3b8e3273738` | `0 / 0` | Same class as other MetaMorpho shares. |
| 19 | Fluid USDC `0xf42f5795D9ac7e9D757dB633D693cD548Cfd9169` | `0 / 0` | Verified `fToken`; share value can change. No direct holder-unit confiscation, rebase, transfer fee, or proxy was established from the dated ABI. |
| 20 | Euler USDC `0x0A1a3b5f2041F33522C4efc754a7D096f880eE16` | `0 / 0` | Verified beacon-proxy EVault; upgrade and share-value loss risk. |
| 21 | Moonwell cbBTC `0xF877ACaFA28c19b96727966690b2f44d35aD5976` | `0 / 0` | Verified delegator/implementation architecture; upgrade and seize surfaces. |
| 22 | Morpho Moonwell WETH `0xa0E430870c4604CcfC7B38Ca7845B1FF653D0ff1` | `0 / 0` | Verified non-proxy MetaMorpho vault; share-value loss risk. |
| 23 | Morpho Seamless WETH `0x27D8c7273fd3fcC6956a0B370cE5Fd4A7fc65c18` | `0 / 0` | Verified non-proxy MetaMorpho vault; share-value loss risk. |
| 24 | Euler WETH `0x859160DB5841E5cfB8D3f144C6b3381A85A4b410` | `0 / 0` | Verified beacon-proxy EVault; upgrade and share-value loss risk. |
| 25 | Morpho Moonwell cbBTC `0x543257eF2161176D7C8cD90BA65C2d4CaEF5a796` | `0 / 0` | Verified non-proxy MetaMorpho vault; share-value loss risk. |
| 26 | sUSDe `0x211Cc4DD073734dA055fbF44a2b4667d5E5fE5d2` | `830,694,343,423,510,974 / 830,694,343,423,510,974` | Verified `StakedUSDeOFT` exposes blacklist and `redistributeBlackListedFunds`. This is an explicit mechanism capable of moving a blacklisted holder's funds independently of Ripe accounting. Funded. |
| 27 | wrapped superOETH `0x7FcD174E80f264448ebeE8c88a7C4476AAF58Ea6` | `0 / 0` | Verified upgradeable proxy; underlying/share-value loss and upgrade risk. |

At the pinned block, all funded assets were solvent in nominal accounting; WETH
had a one-unit surplus. This snapshot does not prove future safety.

### 5.3 Base urgency conclusion

**Recommendation, not approval:** Release 1 is an urgent live Base hardening
requirement, even if Robinhood ultimately uses the permanent share path.

Reasoning:

1. Base currently routes vault ID 3 to the unsafe nominal Simple path.
2. Nine registered assets had positive custody at the pinned block.
3. Funded `sUSDe` exposes an explicit blacklist-funds redistribution surface.
4. Funded cbBTC, cbDOGE, uSOL, WELL, VIRTUAL, and cbETH have issuer, bridge,
   proxy, beacon, pause, blacklist, burn, or upgrade controls.
5. The current deposit path can create a deficit through short receipt even
   without issuer confiscation.

The current no-deficit snapshot reduces immediate incident evidence; it does
not remove the reachable invariant failure. Any Base change still requires the
owner to approve the live-version and custody-bearing migration posture.

### 5.4 Reproducibility appendix

#### Endpoints and retrieval times

- Pinned JSON-RPC endpoint:
  `https://mainnet.base.org`
- Verified-source metadata endpoint template:
  `https://base.blockscout.com/api/v2/smart-contracts/{address}`
- Initial RPC/source retrieval:
  2026-07-23 America/Denver
- Review repeat for registry and funded-status reads:
  `2026-07-24T03:46:40Z`

No secret, authenticated endpoint, write method, signing operation, or broadcast
was used.

#### RPC method transcript

The address table above is the decoded result of indices `1..27`; `C / N` is
the decoded pair from the last two calls for each address.

```text
cast block 49036674 --json --rpc-url https://mainnet.base.org

cast call 0xB758e30C14825519b895Fd9928d5d8748A71a944 \
  'getAddr(uint256)(address)' 3 \
  --block 49036674 --rpc-url https://mainnet.base.org

cast call 0xB758e30C14825519b895Fd9928d5d8748A71a944 \
  'getRegId(address)(uint256)' \
  0xf75b566eF80Fde0dEfcC045A4d57b540eb43ddfD \
  --block 49036674 --rpc-url https://mainnet.base.org

cast call 0xB758e30C14825519b895Fd9928d5d8748A71a944 \
  'getRegId(address)(uint256)' \
  0xce2E96C9F6806731914A7b4c3E4aC1F296d98597 \
  --block 49036674 --rpc-url https://mainnet.base.org

cast call 0xf75b566eF80Fde0dEfcC045A4d57b540eb43ddfD \
  'getNumVaultAssets()(uint256)' \
  --block 49036674 --rpc-url https://mainnet.base.org

cast call 0xf75b566eF80Fde0dEfcC045A4d57b540eb43ddfD \
  'vaultAssets(uint256)(address)' <index> \
  --block 49036674 --rpc-url https://mainnet.base.org

cast call <asset> 'balanceOf(address)(uint256)' \
  0xf75b566eF80Fde0dEfcC045A4d57b540eb43ddfD \
  --block 49036674 --rpc-url https://mainnet.base.org

cast call 0xf75b566eF80Fde0dEfcC045A4d57b540eb43ddfD \
  'totalBalances(address)(uint256)' <asset> \
  --block 49036674 --rpc-url https://mainnet.base.org

cast call <vault> 'doesVaultHaveAnyFunds()(bool)' \
  --block 49036674 --rpc-url https://mainnet.base.org

cast codehash <vault> \
  --block 49036674 --rpc-url https://mainnet.base.org
```

The review repeat returned:

```text
RebaseErc20.getNumVaultAssets()      => 6
RebaseErc20.doesVaultHaveAnyFunds() => false
SimpleErc20.doesVaultHaveAnyFunds() => true
```

For control classification, each full asset address was fetched through the
Blockscout endpoint above. The recorded fields were verified contract name,
proxy type, implementation address/name when present, verification status, and
ABI function names matching upgrade, implementation, admin, owner, pause,
blacklist, burn, mint, seize, skim, fee, or redistribution behavior. The most
consequential direct-custody evidence is reproducible at:

```text
https://base.blockscout.com/api/v2/smart-contracts/0x211Cc4DD073734dA055fbF44a2b4667d5E5fE5d2
```

That verified ABI includes `blackList`, `updateBlackList`, and
`redistributeBlackListedFunds`. Classification still does not claim that every
listed method is exercisable by every role or that latest explorer metadata is
historical proof at the pinned block; unknown authority/role state remains
unknown.

## 6. Formal state model

For each vault `v`, asset `a`, user `u`, and state/time `t`:

| Symbol | Definition |
| --- | --- |
| `C_t` | Actual live ERC-20 custody: `IERC20(a).balanceOf(v)` at `t`. |
| `q` | Requested transfer amount for the current call. |
| `C^-`, `C^+` | Custody immediately before and after the call's token-transfer boundary. |
| `R` | Actual per-call receipt. When `C^+ >= C^-`, `R = C^+ - C^-`; a negative or unclassifiable delta must not create credit. |
| `N_u`, `N` | Raw nominal user balance and aggregate nominal balance, with `N = ΣN_u`, for a nominal vault. |
| `s_u`, `S` | Raw user shares and aggregate raw share supply, with `S = Σs_u`, for a share vault. |
| `L_u(C,S)` | User's token-denominated live claim under the approved conversion/rounding formula. The current formula is approximately `floor(s_u × (C + 1) / (S + 10^8))`; its final status is Phase G. |
| `K` | Aggregate allocable live claims, `K = ΣL_u`, including defined rounding bounds. |
| `B_u` | Token amount exposed by this asset to CreditEngine for borrowing and debt health. |
| `D_u` | Amount currently and safely deliverable to or for `u`, after backing, allocation, settlement-policy, pause, and blocklist checks. |
| `δ` | Nominal deficit: `max(N - C, 0)`. `deficit := δ > 0`. |
| `Z` | Share total-loss state: `S > 0 ∧ C = 0`. |
| `P/BL/U` | Observable pause, relevant sender/recipient/operator blocklist, and implementation/beacon identity or change state. Unknown is not equivalent to safe. |
| `E_u` | User debt for an account that includes this asset. Current storage is account-level; no exact asset-attributed debt split exists. |
| `X` | Active auction claims/targets for `(v,a)` and their settlement state. |
| `BD` | Protocol bad debt recorded in Ledger. |

For a nominal path, token-denominated persisted accounting is `N`. For a share
path, persisted accounting is `S`, not token units; `L_u`, `K`, and `C` must be
reported separately.

## 7. Formal invariants

The identifiers below are shared with the validation-plan draft.

### I-01 — exact receipt and donation isolation

For each deposit call:

```text
credited_token_amount = R
0 <= R <= q unless an explicit excess-receipt policy is owner-approved
prior custody not received by this call cannot be credited to this depositor
```

Any unexpected negative delta, callback ambiguity, or implementation change
must revert or otherwise commit zero credit.

### I-02 — aggregate borrowing conservation

```text
Σ B_u(v,a) <= C(v,a)
```

No user or combination of users may borrow against the same custody twice.

### I-03 — claim and settlement conservation

```text
Σ live claims allocated or settled from (v,a) <= C(v,a)
```

Rounding dust must have an explicit bound and owner-approved disposition.

### I-04 — pay only for delivered collateral

For every auction, redemption, deleverage, or other collateral settlement:

```text
GREEN paid or debt reduced
    <= price(value of collateral actually and safely delivered)
```

An internal ledger move is not "safely delivered" for an issuer-controlled
asset unless the owner explicitly rejects the external-only policy and the
design separately proves live backing and later deliverability.

### I-05 — failed-delivery atomicity

Failed or false-returning token delivery, pause, blocklist, deficit guard, or
behavior switch cannot commit any of:

- GREEN payment;
- debt reduction;
- buyer claim;
- internal user-balance transfer;
- auction progress/removal; or
- reward/participation state derived from settlement.

### I-06 — deficit visibility

Fail-closed zero borrowing value must not erase the fact that existing debt is
unsafe. A deficit signal must remain visible to previews, borrow validation,
account health, liquidation/resolution eligibility, events, and monitoring even
when `B_u = 0`.

### I-07 — no new debt under an unsafe asset

If the asset collateral-use flag is disabled, `δ > 0`, `Z`, or the backing
check is unknown/failing:

```text
new borrowing capacity contributed by (v,a) = 0
```

Unrelated solvent collateral retains its correct capacity.

### I-08 — liability conservation and exactly once

At an approved bad-debt transition of amount `x`:

```text
user debt after = user debt before - x
protocol bad debt after = protocol bad debt before + x
```

The transition must be marked so it cannot repeat. The same `x` cannot remain
both as user debt and Ledger bad debt, and it cannot disappear from both.
Interest and repayments before the transition must use one pinned debt state.

### I-09 — repayment liveness

Repayment remains available before a bad-debt transition even when deposits,
borrowing, internal settlement, new auctions, or withdrawals are frozen.

### I-10 — post-zero non-interference

When `Z` holds, a new depositor cannot recapitalize old claims, erase them, or
capture later restoration by accident. New deposits remain frozen unless an
explicit owner-approved recapitalization/allocation procedure proves otherwise.

### I-11 — issuer-controlled external settlement

Under the recommended policy, issuer-controlled collateral is always settled
externally. Buyer-selected internal settlement is unavailable.

### I-12 — custody control is price-independent

Custody backing and per-asset collateral-use checks do not depend on a valid,
nonzero oracle price. Missing price may independently block valuation; it must
not hide or clear a custody deficit.

## 8. Required state behavior

| State | Safety behavior | Liveness result | Allocation/policy | Operator evidence |
| --- | --- | --- | --- | --- |
| 1. Solvent ordinary operation | Credit exactly `R`; `ΣB`, `K`, and settlement remain bounded by `C`. | Deposits, borrow, repay, withdrawal, and approved settlement can progress. | Normal rounding/dust policy pending Phase D/G. | Live/accounted/claim getters and normal events. |
| 2. Pre-existing donation | The donation is not the next depositor's `R`. | Deposit may proceed only if measurement is call-local. | Surplus ownership/recovery remains owner policy. | Expose `C` separately from persisted accounting. |
| 3. Donation between deposits | Later depositor cannot capture the donation through receipt inference. | Existing users may benefit only under an approved share/surplus policy. | Owner must decide who owns the donation. | Record first divergence and resulting surplus. |
| 4. Short receipt / fee on transfer | Credit `R`, not `q`; zero receipt commits no credit. | Call succeeds only if `R` satisfies minimums, or reverts atomically. | Excess/fee treatment pending. | Requested, received, credited, and event amounts must reconcile. |
| 5. Partial issuer reduction | Nominal path sets deficit and disables new borrowing/internal settlement; corrected share path reprices pro rata. | Repay and safely allocable external delivery remain possible. | Nominal partial-loss allocation is not selected. | Expose `C`, `N` or `S`, claims, `δ`, flags, and affected auctions. |
| 6. Aggregate nominal deficit | `B=0` for affected asset while explicit deficit keeps existing debt unsafe/visible. | Repay remains open; loss settlement freezes absent policy. | No silent `min(userNominal,C)` or pro rata. | Emit/return deficit independently of price. |
| 7. Total custody loss with claims | No paid auction or collateral settlement for missing tokens. | Repay remains open; position becomes resolution-eligible. | Owner must approve exactly-once bad-debt transition. | `C=0`, claims/accounting positive, debt and transition state observable. |
| 8. Zero custody, nonzero shares | Withdrawal/internal transfer cannot invent value; new deposits frozen. | User exit is blocked until repayment, restoration policy, or bad-debt resolution. | Old shares remain explicit; no automatic erasure. | `Z` getter/event and raw-share reporting. |
| 9. Donation/restoration after zero | No automatic reassignment or re-enable. | Progress only through approved restoration/recapitalization procedure. | Owner chooses old users, donor return, protocol, or another explicit allocation. | Amount, source, approval, and allocation event. |
| 10. Attempted new deposit after zero | Revert before credit/share mint while `Z`. | Deposit intentionally unavailable. | Alternative requires owner-approved recapitalization proof. | Clear post-zero freeze reason. |
| 11. Paused transfer | External delivery/deposit reverts; no downstream payment or accounting commits. | Retryable after unpause; repayment remains independent. | Internal settlement disabled for issuer-controlled assets. | Observable pause where supported; otherwise failure diagnostics. |
| 12. Sender/recipient/operator blocklist | Relevant transfer reverts atomically. | Retry with an eligible endpoint only where policy permits. | No bypass via internal claim for issuer-controlled assets. | Report which role failed when observable. |
| 13. Active auction before issuer action | Recheck backing/deliverability at purchase; do not rely on creation-time amount. | Auction may pause/fail without charging buyer. | Remaining custody cannot be allocated twice. | Auction state, custody-change point, and zero committed progress. |
| 14. Liquidation after issuer action | Do not manufacture a zero-backed auction; preserve deficit in health/resolution state. | Repay or approved resolution can progress. | Owner chooses total-loss transition. | Distinguish liquidation eligibility from auction eligibility. |
| 15. Implementation/beacon change | Re-evaluate receipt and delivery behavior; unsafe/unknown state fails closed. | Resume only after approved verification/re-enable. | Re-enable authority must be stronger than emergency disable. | Implementation/beacon/code identity and change evidence. |
| 16. Recovery/migration with users/debt | Disable old deposits; reconcile users, custody, debt, auctions, and raw accounting before movement/retirement. | Abort/rollback must preserve one authoritative state. | Owner approves migration and partial-failure policy. | Before/after manifest, registry, balances, debt, auction, and reconciliation record. |

The table intentionally separates safety from liveness. A revert can prevent
theft while still leaving debt permanently unresolved.

## 9. Architecture comparison

### 9.1 Summary

| Outcome | Full invariant coverage | Robinhood Stock Token technical eligibility | Recommendation |
| --- | --- | --- | --- |
| 1. Do not list Stock Tokens | Vacuous for Stock Tokens; existing Base defects remain | No | Safe default if no direction is approved |
| 2. Minimum shared containment | I-01, I-02, I-05–I-07, I-09, I-12; partial I-03/I-04 | No for issuer-controlled collateral under the complete invariant set; containment freezes unresolved loss cases | Ship as urgent Base hardening if owner approves the full atomic release and migration |
| 3. Corrected shared share path | Can cover I-01–I-12 after policy, implementation, migration, audit, and exact-token validation | Yes, but only after every gate is complete | Permanent direction |
| 4. Another generic design | Not needed at this checkpoint | No current basis | Do not open unless later interface proof shows the shared corrected design cannot meet an invariant |

### 9.2 Outcome 1 — do not list

- **Invariant coverage:** prevents Stock Token custody exposure by absence.
- **Unresolved choices:** Base hardening remains; Robinhood product scope
  excludes Stock Token collateral.
- **Affected surfaces:** configuration and deployment inventory only; no Stock
  Token deposits, borrowing, auctions, or vault migration.
- **Base behavior:** unchanged and still exposed to shared nominal-vault defects.
- **Custody risk:** no new Robinhood Stock Token custody; current Base risk
  remains.
- **Scope/audit/testing:** lowest Robinhood contract scope; Base follow-up still
  requires review.
- **Rollback:** operationally simple before listing.
- **Operational burden:** enforce unsupported status and prevent accidental
  configuration.
- **Eligibility:** no.

### 9.3 Outcome 2 — minimum shared containment

One atomic deployable safety group:

- exact call-local received amount;
- fail-closed Simple borrowing value during aggregate deficit;
- explicit deficit signal through debt health;
- no zero-threshold false health or non-liquidatable disappearance;
- internal-transfer deficit guard;
- generic per-asset collateral-use safety flag;
- repayment preserved; and
- no zero-backed auction manufactured.

Changing only the amount view is unsafe because CreditEngine skips zero amounts
before weighted terms are constructed.

- **Invariant coverage:** stops new phantom-backed debt and unsafe nominal
  internal settlement; preserves delivery atomicity and repayment.
- **Unresolved choices:** partial-loss allocation, total-loss bad-debt
  transition, post-zero restoration, and permanent issuer settlement remain
  unresolved/frozen.
- **Affected components:** at least `CM-024`, `CM-026`, `CM-030`, `CM-034`,
  `CM-045`, `CM-009`, `CM-011`–`CM-013`, `CM-021`, `CM-033`, `CM-044`, and
  common config/interfaces; exact changes are Phase I.
- **Base behavior/migration:** canonical shared source changes; funded vault ID
  3 means an owner-approved Base migration/version policy is mandatory.
- **Custody risk:** contains overcredit/new borrowing; does not allocate an
  existing loss or complete debt resolution.
- **Scope/audit:** cross-contract atomic safety review across deposit, credit,
  settlement, and governance.
- **Rollback:** deployment rollback is not a substitute for custody rollback;
  any moved positions need reconciled reverse migration.
- **Testing:** all affected Simple/Base regressions plus mixed collateral and
  existing debt.
- **Operations:** monitor deficits, disable quickly, keep repay open, do not
  auto-re-enable.
- **Eligibility:** not sufficient for full issuer-controlled collateral
  listing under I-08 and I-10.

### 9.4 Outcome 3 — corrected shared share-based permanent path

Required properties:

- pro-rata live claims after partial loss;
- exact call-local receipt;
- live claims, never raw shares, used for credit and settlement;
- explicit total-loss debt resolution;
- post-zero deposit freeze;
- owner-approved donation/restoration allocation;
- external-only issuer-controlled settlement;
- bounded rounding/dust;
- explicit reward and monitoring units; and
- migration from any custody-bearing prior vault version.

- **Invariant coverage:** capable of full I-01–I-12 coverage.
- **Unresolved choices:** loss allocation acceptance, total-loss transition,
  restoration/recapitalization, reward units, rounding bounds, migration, and
  external-only policy approval.
- **Affected components:** `CM-025` plus the containment consumers above,
  common interfaces/config, VaultBook, defaults/migrations/manifests, and
  post-deployment verification.
- **Base behavior/migration:** one canonical source. Owner must choose parity,
  bounded temporary drift with convergence, or a justified live-version
  exception; no policy is selected here.
- **Custody risk:** live pro-rata claims remove nominal phantom collateral, but
  transfer controls and total loss still require explicit resolution.
- **Scope/audit:** larger math, storage/interface, settlement, bad-debt, reward,
  and migration boundary.
- **Rollback:** live share migration is stateful and not trivially reversible.
- **Testing:** highest burden, including property math, exact AAPL fork,
  dual-clock profiles, Base regression, and migration.
- **Operations:** explicit raw-share/live-claim/deficit/version evidence and
  stronger re-enable process.
- **Eligibility:** technically eligible only after owner selection and all
  implementation, audit, exact-token, migration, and production-behavior gates.

This is an architecture recommendation, not a selection of the current
`RebaseErc20` deployment or any other production vault.

### 9.5 Outcome 4 — another generic shared design

Not admitted at this checkpoint. The required invariants appear achievable
through generic changes to the shared vault/config/credit/settlement
architecture plus a corrected share path. Existing interfaces are insufficient
unchanged, especially for deficit propagation, per-asset collateral use, and
exactly-once bad debt, but they can be extended without an issuer-branded or
Robinhood-only vault.

Reopen this outcome only if Phase D–I analysis, security review, or a proof
shows the shared corrected design cannot express an invariant.

## 10. Rejected shortcuts

| Shortcut | Disposition |
| --- | --- |
| Change only the Simple amount view to zero | Rejected: zero is skipped by CreditEngine and can erase weighted debt terms without resolving existing debt. |
| `min(userNominal, liveTotal)` | Rejected: multiple users can each claim the same aggregate custody. |
| Silent nominal pro rata or balance rewrite | Rejected absent owner-approved loss allocation/property-rights policy. |
| LTV set to zero as custody switch | Rejected: not an immediate backing control and does not make settlement honest. |
| Oracle price removal/zero as kill switch | Rejected: price and custody are independent; zero price can block health/liquidation. |
| Monitoring and operator response only | Rejected: onchain borrow and settlement must fail closed. |
| Disable deposits only | Rejected: existing borrowing, debt health, internal settlement, auctions, and loss resolution remain unsafe. |
| Treat internal balance movement as delivery | Rejected for issuer-controlled assets; token pause/blocklist/custody is not exercised. |
| Manufacture a zero-backed auction for progress | Rejected: violates payment/delivery conservation. |
| Treat later donation/restoration as automatic recovery | Rejected: ownership/allocation is ambiguous. |
| Permit fresh deposit at zero custody with old shares | Rejected absent explicit recapitalization; it can transfer value between old and new users. |
| Use current SharesVault unchanged | Rejected: short-receipt measurement, total-loss liveness, post-zero allocation, and migration are unresolved. |
| Use current SimpleErc20 unchanged | Rejected for Stock Token collateral: nominal phantom backing and first-withdrawer/internal-settlement failures persist. |
| Replace vault ID 3 directly in VaultBook | Rejected: live-funds checks and persisted user/asset state prevent casual replacement. |
| Disable repayment during freeze | Rejected: violates repayment liveness and worsens loss. |
| Robinhood-only/issuer-branded vault or `chain.id` branch | Rejected: violates the canonical shared-source constraint. |
| New insurer, Stability Pool custody route, or recovery token | Out of scope and rejected for Track 8. |

## 11. Recommendation

Recommend that the owner select checkpoint option **4: containment followed by
the corrected share path**, with these boundaries:

1. Treat the full Release 1 containment group as urgent Base hardening, not as a
   sufficient Robinhood Stock Token listing release.
2. Keep Robinhood Stock Token deposits, borrowing, and auctions disabled until
   the permanent path satisfies all invariants and gates.
3. Use a corrected generic share-based architecture as the permanent direction,
   without selecting a production vault at this checkpoint.
4. Require external-only settlement for issuer-controlled collateral.
5. Freeze post-zero deposits by default.
6. Do not begin implementation until the owner approves the decision set below.

This recommendation is not production-vault selection, implementation
authorization, Base migration approval, or acceptance of a loss-allocation
policy.

### 11.1 Track 5 recommendation disposition

| Track 5 recommendation | Track 8 disposition at checkpoint |
| --- | --- |
| Continuous live/accounted solvency monitoring | **Accepted as an operational and future getter/event requirement**, but not as an onchain fix. Hosted monitoring is outside this repository track. |
| Rehearsed global-borrow, per-asset-deposit, and per-asset-auction response | **Accepted as Release 0 preparation**. Any production flag change requires fresh owner approval. |
| Keep Stock Tokens disabled until behavior is approved | **Accepted**. This is the current safe state. |
| Fail-closed Simple borrowing amount under deficit | **Accepted into the containment recommendation**, conditional on explicit deficit propagation; exact interface is deferred to Phase E. |
| Deficit-aware existing-debt health | **Accepted into the atomic containment group**; no amount-view-only patch is acceptable. |
| Reject Simple internal transfer while underbacked | **Accepted into the atomic containment group**; exact guard/result behavior is deferred. |
| Add generic per-asset collateral-use flag | **Returned for owner approval in principle**, with a positive recommendation. |
| Exact per-call deposit delta in the same release | **Accepted as invariant I-01**; Teller-versus-vault boundary remains a Phase D owner-directed design decision. |
| External-only issuer-controlled settlement | **Returned for owner approval**, with a positive recommendation. |
| Keep generic backing checks even with external-only settlement | **Accepted as invariants I-02, I-06, and I-07**. |
| Define deficit and total-loss debt progress | **Partially accepted**: containment freezes unsafe progress and keeps repayment open; final exactly-once transition is returned for owner/accounting/security decision. |
| Corrected share-based permanent behavior | **Accepted as the recommended permanent architecture**, not selected as a production vault. |
| Freeze post-zero deposits | **Returned for owner approval**, with a positive default recommendation. |
| Do not auto-allocate later donations/restoration | **Accepted as a prohibition**; positive allocation remains an owner/counsel/risk decision. |
| Base canonical shared-version hardening and migration | **Recommended as urgent**, pending owner live-version and migration approval. |
| Fifteen acceptance-test outcomes | **Carried into the validation-plan scaffold** with invariant IDs and named future tests. |
| Release 0/1/2 sequencing | **Accepted as release framing**; no implementation or deployment gate is opened. |
| `min(user nominal, live)`, silent rewrite, oracle kill switch, monitoring-only, and LTV-only shortcuts | **Rejected**, as detailed in Section 10. |

Every Track 5 fix recommendation is therefore accepted, rejected, deferred, or
returned for an explicit owner decision. None is treated as implementation
authorization.

## 12. Mandatory owner checkpoint

### 12.1 Direction required

The owner must select one:

1. no Stock Token listing;
2. containment release only;
3. corrected share-based permanent path;
4. containment followed by corrected share path; or
5. another explicitly approved generic design.

No selection has been made. If no direction is approved, Track 8 stops with
`do not list Stock Tokens under the current vault designs`.

### 12.2 Checkpoint decisions and their actual gates

Only the product/architecture direction is required to begin Phase D. The
checkpoint requests the remaining eight decisions now so the owner can resolve
them early, but they gate the later phases shown below and need not delay Phase
D if the owner prefers staged decisions.

| Decision | Options | Evidence and recommendation | Owner | Affected components | Prerequisite / milestone | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Product outcome | Five checkpoint options above | Recommend staged containment then corrected share path | Product + protocol owner | Whole track | Before Phase D | **Required now** |
| Per-asset collateral use | Approve generic flag / reject | Current config lacks it; recommend approve in principle | Protocol owner + security | `CM-009`, `CM-011`–`013`, `CM-030`, config/interfaces | Before Phase E | Requested at checkpoint; gates Phase E |
| Issuer-controlled settlement | Always external / permit bounded internal | Current internal mode can charge for undeliverable nominal claims; recommend external-only | Protocol owner + risk/security | `CM-026`, `CM-030`, `CM-043`, `CM-044`, Vault interface | Before Phase F | Requested at checkpoint; gates Phase F |
| Total-loss transition | Approved user-debt→Ledger-bad-debt design / another existing-accounting design / no listing | Current system has no atomic exactly-once path; recommend a separate shared transition specification within the selected release | Protocol owner + accounting/security | `CM-026`, `CM-030`, Ledger, interfaces | Before Phase F | Requested at checkpoint; gates Phase F |
| Post-zero state | Freeze / explicit recapitalization | Recommend freeze by default | Protocol owner + risk | `CM-025`, deposit callers, controls | Before Phase G | Requested at checkpoint; gates Phase G |
| Later donation/restoration | Old holders / donor return / protocol / explicit recapitalization allocation | No automatic inference is safe; owner must select only with legal/risk review | Protocol owner + counsel/risk | Share math, recovery, migration | Before Phase G | Requested at checkpoint; gates Phase G |
| Reward attribution | Raw shares / live claims / hybrid explicit units | Current Lootbox uses raw shares and global live value; recommend explicit units, final choice pending S3 coordination | Protocol owner + economics | `CM-033`, `CM-025` | Before Phase G/H | Requested at checkpoint; gates Phase G/H |
| Base live-version posture | Migrate before RH / bounded temporary drift / justified permanent exception | Funded ID 3 and live controlled assets make this material; recommend Release 1 Base migration subject to plan | Protocol owner + security/operations | Base vault consumers, VaultBook, manifests | Before Phase I/release | Requested at checkpoint; gates Phase I/release |
| Release 1 Base priority | Hardening requirement / RH prerequisite only / no release | Recommend urgent Base hardening | Protocol owner + security | Containment atomic group | Before implementation track | Requested at checkpoint; gates implementation split |

### 12.3 Decisions explicitly deferred but registered

These must not be treated as approved by the checkpoint recommendation:

| Decision area | Options/recommendation | Needed before | Status |
| --- | --- | --- | --- |
| Deposit measurement boundary | Teller or inside each vault; select only after Phase D caller/failure analysis | Phase D completion | Deferred |
| Requested/received/excess semantics | Revert excess, cap, or explicit credit rule; exact `R` required | Phase D completion | Deferred |
| Nominal partial loss | Freeze unresolved or owner-approved allocation; never silent pro rata | Phase E/F | Deferred |
| Rounding | Offset, directions, minimum, dust bound | Phase G | Deferred |
| Emergency disable/re-enable | Fast disable and stronger/timelocked re-enable recommended | Phase H | Deferred |
| Vault selection | No production vault selected | Phase I owner gate | Deferred |
| Migration atomicity/rollback | Explicit live users/funds/debt/auctions plan | Phase I | Pending Track 7 |
| Exact-token evidence | Pinned AAPL fork plus behavior-switch/loss tests | Phase J | Pending implementation |
| S1/S2 identical artifacts | Base/RH profiles and checked inventory | Phase J | Pending integrated S1/S2 |
| Audit/release | Atomic group, reviewers, testnet, smoke, soak | Phase K | Deferred |

## 13. Affected component map at checkpoint

This is a Phase C impact boundary, not the finalized Phase I change table.

| Stable ID / surface | Why affected |
| --- | --- |
| `CM-021` VaultBook | Funded-vault replacement, disablement, migration, and retirement checks |
| `CM-024` Basic/Simple vault path | Nominal accounting, deficit, internal transfer, receipt |
| `CM-025` Rebase/Shares path | Live claim, post-zero, restoration, rounding |
| `CM-026` AuctionHouse | Settlement policy, delivery/payment ordering, active auctions |
| `CM-027` AuctionHouseNFT | Current temporary stub has no common Vault consumer; reused unchanged/inapplicable unless later implemented |
| `CM-030` CreditEngine | Borrow amount, deficit propagation, health, resolution |
| `CM-043` CreditRedeem | Transfer/withdraw settlement consumer and unsupported Stock Token posture |
| `CM-033` Lootbox | Raw shares versus live-value reward units |
| `CM-034` Teller | Transfer/credit/event/limit/housekeeping ordering |
| `CM-044` Deleverage | Delivered amount and zero-custody progress |
| `CM-045` TellerUtils | Deposit limit inputs and pre-transfer vault views |
| `CM-007`–`CM-013`, `CM-049` | Defaults, MissionControl, Switchboards, per-asset controls, Robinhood configuration |
| Ledger | User debt, auctions, and exactly-once protocol bad debt |
| `ConfigStructs` and `Vault` interfaces | Missing flags/status/results; caller compatibility |
| StabilityPool, RipeGov, StabVault | Shared Teller deposit boundary must preserve semantics |
| Base/RH migration and manifests | Same canonical source, live-version policy, custody migration, verification |

Track 7 owns exact Robinhood migration IDs/namespaces/tooling. Track 8 will not
reserve or invent them.

## 14. Phases D–K hold

The following are deliberately **not finalized**:

- exact deposit measurement boundary and ABI/event behavior;
- final backing/config storage and governance interface;
- total-loss bad-debt transition mechanics;
- corrected share formulas and post-zero allocation;
- control roles and clock behavior;
- exact source/storage/interface/migration table;
- final validation plan;
- implementation PR split and atomic deployable groups; and
- exact `rh-summary.md` handoff.

Work must not continue into those phases until the owner resolves Section 12.

## 15. Checklist handoff at this checkpoint

No `rh-summary.md` checkbox is edited or closed.

Eligible for owner review:

- Phase 0, **resolve the deployable Stock Token vault path** (line 85 at the
  `be6a759` reconciliation baseline) — the decision packet is now ready, but no
  path is selected. The item remains unchecked in post-bootstrap `ce3805d`.
- Section 4, **finish the Simple versus Rebase comparison** (line 186 at the
  baseline) — Track 5 evidence is hash-verified, source-reconciled, and rerun.
- Section 4, **write a separate vault-change specification if current behavior
  is unacceptable** (line 190 at the baseline) — Phases A–C and the owner
  checkpoint are ready for review, but the item is not eligible for closure
  until Phases D–K are owner-directed and completed.

Not eligible for closure:

- chosen-vault behavior testing (line 189);
- vault/feed/config/risk-parameter selection;
- issuer-failure implementation evidence;
- the Section 4 exit condition; or
- any technical launch gate that requires a selected vault, production code,
  migration, audit, exact-token lifecycle, or owner approval.
