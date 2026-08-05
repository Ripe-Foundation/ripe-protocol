# GuardedErc20 vault architecture reassessment

> **Superseded 4 August 2026.** This document is retained as historical
> decision evidence. The current feature-branch decision moves the fail-closed
> nominal protections into `BasicVault`, uses them through `SimpleErc20`, and
> removes the separate `GuardedErc20` source and artifact. See
> [`basic-vault-fail-closed.md`](../smart-contract-changes/basic-vault-fail-closed.md).

Frozen authority: `rh` commit
`0d5994aa78f9d6f35b59bd7a2bc70fa18706e693`, tree
`b68dffdddbdc7c5ae8423db049099c1632b478c9`. Review date: 30 July
2026. This is a repository-local, read-only architectural reassessment. It
does not authorize a contract, interface, ABI, configuration, registry,
migration, deployment, activation, or release change.

## 1. Executive recommendation

**Retain `GuardedErc20` as a separate specialized nominal vault. Do not
backport its whole behavior into `SimpleErc20`, `BasicVault`, `SharesVault`,
`RipeGov`, or `StabilityPool`.** The separate artifact is justified because it
isolates a materially stricter token-compatibility and failure policy while
preserving the established Base nominal and share-vault behaviors.

Guarded is not a new accounting model. It is the `SimpleErc20`/`BasicVault`
nominal model with custody-solvency, exact-delivery, strict-returndata, and
backing-aware-value containment around the same storage and canonical `Vault`
selectors. One non-guard getter detail differs: a depleted but still registered
position is `(asset,0)` in Simple and `(0,0)` in Guarded. That affects
CreditEngine term inclusion and must not be described as identical consumer
behavior. Git added the file in
`4f887207d344a1513d6c3a79d315c8315a10a9c8`; there is no recorded Git copy or
rename predecessor, but the declarations, constructor, nominal module, public
function set, and unchanged sections establish `SimpleErc20` as the direct
structural predecessor. It is not derived from `RebaseErc20` or
`SharesVault`.

The protections divide into three layers:

1. Teller must measure the call-local deposit receipt because Teller performs
   the inbound transfer. That shared protection already exists and should
   remain shared.
2. A nominal vault must enforce the relationship between its own custody and
   its own liabilities, and must prove its own outbound delivery. That is
   properly a vault responsibility.
3. Consumers must interpret a nonempty `(asset, 0)` as an existing but
   unusable position, retain terms, and assign zero capacity. They must not
   duplicate token observation or treat position existence as value.

A token adapter cannot replace these layers. An adapter can normalize a token
or express a share claim, but it either leaves the vault exposed to adapter
backing or moves the same solvency problem into the adapter.

For Robinhood:

- deploy `GuardedErc20` for every borrow-enabled nominal asset whose custody
  can be changed, frozen, taxed, rebased, seized, redeemed, or upgraded outside
  the vault, including the initial Stock asset;
- do not permit the same relevant asset in `SimpleErc20`;
- retain the dedicated `StabilityPool` and `RipeGov` roles;
- omit `RebaseErc20` at launch unless an asset explicitly requires approved
  share/yield semantics;
- use `SimpleErc20` only for a deliberately non-Stock, exact-transfer,
  non-rebasing, non-confiscatable nominal asset whose route does not need
  Guarded's Stock-specific Endaoment exclusion. For a fresh chain, prefer
  Guarded as the default borrow-enabled nominal generation so Simple becomes a
  constrained legacy/deposit-only choice rather than the default collateral
  choice.

For every Guarded Stock asset, activation must additionally bind the
auction-only liquidation tuple
`shouldSwapInStabPools=False`, `shouldTransferToEndaoment=False`, and
`shouldAuctionInstantly=True`. Without the first value, a funded Stability Pool
swap can reach Guarded withdrawal while custody is deficient and revert the
entire multi-vault liquidation; without the latter two, Stock can be skipped or
left without the intended per-asset auction path. The frozen Robinhood
parameters omit these AAPL fields rather than supplying values, so this is an
unmet activation invariant, not a description of current configuration.

This is stricter than saying “all ERC-20s use Guarded.” Fee-on-transfer,
reflection, dishonest-balance, and share/yield assets are not made safe by
putting them in either Simple or Guarded; they require a separately reviewed
abstraction or rejection.

No production backport is recommended now. The reusable pieces worth carrying
forward are policy and narrowly factored internal helpers: exact 32-byte
balance observation, strict optional-Boolean transfer handling, and
pre/post-delta assertions. Extract them only when a second production vault
needs exactly the same semantics. Vyper statically composes modules, so such an
extraction reduces source duplication but does not create a separately
upgradeable library or automatically reduce runtime size.

## 2. Contract-family genealogy

### 2.1 Family tree

```text
Vault.vyi (common external selectors)
|
+-- Addys + VaultData (address resolution; pause, nominal/share maps and indexes)
    |
    +-- BasicVault (nominal token-unit helpers)
    |   +-- SimpleErc20
    |   `-- GuardedErc20 (same nominal base, guarded wrapper)
    |
    +-- SharesVault (raw shares, virtual balance/share offsets)
    |   +-- RebaseErc20
    |   `-- RipeGov (+ governance lock and points state/logic)
    |
    `-- StabVault (USD-value shares plus claim/redemption state/logic)
        `-- StabilityPool
```

The canonical interface is
[`interfaces/Vault.vyi:5-192`](../../../../interfaces/Vault.vyi). Guarded and
Simple both implement it, export `Addys` and `VaultData`, initialize
`BasicVault`, and call `vaultData.__init__(False)`
([Guarded 6-18, 39-43](../../../../contracts/vaults/GuardedErc20.vy#L6);
[Simple 6-19, 40-44](../../../../contracts/vaults/SimpleErc20.vy#L6)).
Rebase initializes `SharesVault`
([Rebase 6-20, 44-48](../../../../contracts/vaults/RebaseErc20.vy#L6)).
RipeGov also uses `SharesVault` but adds governance-specific persistent state
([RipeGov 23-33, 57-124](../../../../contracts/vaults/RipeGov.vy#L23)).
StabilityPool initializes `StabVault`, which adds claimable-asset state and
price/settlement behavior
([StabilityPool 19-33, 57-61](../../../../contracts/vaults/StabilityPool.vy#L19);
[StabVault 73-100](../../../../contracts/vaults/modules/StabVault.vy#L73)).

### 2.2 Accounting genealogy

| Wrapper | Stored `userBalances` / `totalBalances` units | Economic amount source | Loss/surplus behavior |
| --- | --- | --- | --- |
| Simple | Nominal token units | Stored nominal amount | Loss does not reprice claims; surplus is not allocated |
| Guarded | Nominal token units | Nominal only while exact custody is known and `C >= N` | Deficit/unknown freezes mutations and zeroes two value getters; surplus stays unallocated |
| Rebase | Raw shares | `sharesToAmount` against live custody | Partial loss and surplus reprice pro rata; total-zero/post-zero rounding remains a policy boundary |
| RipeGov | Raw shares plus lock/points state | Shares plus governance terms | Yield/share behavior is coupled to governance locks and point updates |
| StabilityPool | USD-value shares plus claimable balances | PriceDesk and live/claimable assets | Liquidation, claim, redemption, and reward economics are specialized |

`SharesVault` uses `DECIMAL_OFFSET = 10**8` and virtual `+1` balance /
`+DECIMAL_OFFSET` shares
([SharesVault 12, 202-268](../../../../contracts/vaults/modules/SharesVault.vy#L12)).
Guarded imports none of this math.

Guarded does share one *getter outcome* with SharesVault: both return `(0,0)`
for a depleted registered position. That isolated zero-elision choice does not
make Guarded a share vault; its stored units, deposit credit, aggregate
liability, withdrawal amount, loss policy, and surplus policy remain Basic
nominal accounting.

### 2.3 Git genealogy

- `GuardedErc20.vy` was created, not renamed, at feature commit `4f887207…`,
  parent `e39815d…`.
- All 292 current production-source lines blame to that feature commit.
- The source and committed ABI are byte-identical to the feature snapshot at
  this frozen baseline. Later history added tests, artifact expectations,
  consumer inventory, and explanatory/deployment evidence without changing
  the contract.
- Source SHA-256 values are Guarded
  `0fcdb02a0b3adf56ef0fd04397c57ac40325a37c87a32f29979dadc5eaf353ed`,
  Simple
  `6b6794f1e5aaef3b53c3e931eb8fe3596aa3d44dc5d4dcc17f487340f5c89c22`,
  Rebase
  `14fe0db39f96ffebbb8fa4b28fc6fe6fb173ab51095c2853885f4c37c8c41b42`,
  Basic
  `a21a33be9b805f5ce4fd42c66f976525032b92836149c74526be613dae79d89d`,
  Shares
  `7a0ccbfc8c98f8274c3788ef577741053426b9a7ee6618cefb84768425989b3f`,
  and VaultData
  `d84d81ccf45405954404fa6af2c6651ed251efeca958242934eda8f032917e7f`.

## 3. Line-level delta matrix

### 3.1 Guarded versus Simple/Basic

The direct no-index source comparison is 153 inserted and 11 deleted lines
(Guarded is 292 lines versus Simple's 150); most unchanged behavior is inherited
through the same three modules rather than duplicated inside the wrapper.

| Surface | Simple/Basic source | Guarded source | Precise delta |
| --- | --- | --- | --- |
| Imports/composition | [Simple 6-19](../../../../contracts/vaults/SimpleErc20.vy#L6) | [Guarded 6-18](../../../../contracts/vaults/GuardedErc20.vy#L6) | Same `Vault`, `Addys`, `VaultData`, and `BasicVault`; Guarded drops the typed `IERC20` import because its new token calls are raw |
| Constructor | [Simple 40-44](../../../../contracts/vaults/SimpleErc20.vy#L40) | [Guarded 39-43](../../../../contracts/vaults/GuardedErc20.vy#L39) | Identical one-address constructor and initialization; no mode, policy, or guard state |
| Events | [Simple 21-38](../../../../contracts/vaults/SimpleErc20.vy#L21) | [Guarded 20-37](../../../../contracts/vaults/GuardedErc20.vy#L20) | Same fields and indexing; three names/topics change from `Simple...` to `Guarded...` |
| Deposit wrapper | [Simple 52-64](../../../../contracts/vaults/SimpleErc20.vy#L52); [Basic 23-39](../../../../contracts/vaults/modules/BasicVault.vy#L23) | [Guarded 51-79](../../../../contracts/vaults/GuardedErc20.vy#L51) | Before: exact-shape custody observation and `C >= N + Q`; Basic still performs its typed balance read and nominal credit; after: require returned `Q`, unchanged custody, and `N' = N + Q` |
| Withdrawal wrapper | [Simple 67-82](../../../../contracts/vaults/SimpleErc20.vy#L67); [Basic 42-65](../../../../contracts/vaults/modules/BasicVault.vy#L42) | [Guarded 82-137](../../../../contracts/vaults/GuardedErc20.vy#L82) | Bypasses Basic withdrawal; proves pre-solvency, rejects live Endaoment endpoints, observes recipient, reduces nominal, performs strict raw transfer, then proves exact vault outflow, exact recipient receipt, and post-solvency |
| Internal balance movement | [Simple 85-100](../../../../contracts/vaults/SimpleErc20.vy#L85); [Basic 68-87](../../../../contracts/vaults/modules/BasicVault.vy#L68) | [Guarded 140-182](../../../../contracts/vaults/GuardedErc20.vy#L140) | Reuses Basic mutation but surrounds it with pre/post custody, solvency, seller, buyer, and total-nominal invariants |
| Deposit metadata | [Simple 108-112](../../../../contracts/vaults/SimpleErc20.vy#L108) | [Guarded 190-194](../../../../contracts/vaults/GuardedErc20.vy#L190) | Same nominal pre-deposit metadata. Teller uses it for position/limit checks; the actual Guarded deposit and Teller receipt proof subsequently fail under deficit or nonreceipt, so this getter need not represent spendable collateral |
| Lootbox share | [Simple 115-119](../../../../contracts/vaults/SimpleErc20.vy#L115) | [Guarded 197-201](../../../../contracts/vaults/GuardedErc20.vy#L197) | Same nominal user reward weight. If rewards are enabled, a fully burned Stock position can continue accruing at full nominal weight without a time bound |
| Indexed user amount | [Simple 122-126](../../../../contracts/vaults/SimpleErc20.vy#L122); [Basic 114-121](../../../../contracts/vaults/modules/BasicVault.vy#L114) | [Guarded 204-218](../../../../contracts/vaults/GuardedErc20.vy#L204) | True empty is `(0,0)` in both. A depleted registered position remains `(asset,0)` in Simple but becomes `(0,0)` in Guarded, matching Shares' zero-elision; an unsafe nonzero Guarded position is `(asset,0)`. For configured nonzero-LTV terms, CreditEngine includes the Simple depleted asset with weight 1 but skips the Guarded depleted asset |
| Position discovery | [Simple 129-133](../../../../contracts/vaults/SimpleErc20.vy#L129) | [Guarded 221-225](../../../../contracts/vaults/GuardedErc20.vy#L221) | Same nominal, backing-unaware `(asset,hasBalance)`. This preserves loss identity for Lootbox/AuctionHouse, but also lets AuctionHouse enumerate a deficient asset; liquidation configuration must prevent an immediate Stability Pool withdrawal path |
| User total | [Simple 141-144](../../../../contracts/vaults/SimpleErc20.vy#L141) | [Guarded 233-239](../../../../contracts/vaults/GuardedErc20.vy#L233) | Guarded returns zero on unknown/deficit, nominal otherwise |
| Vault total | [Simple 147-150](../../../../contracts/vaults/SimpleErc20.vy#L147) | [Guarded 242-245](../../../../contracts/vaults/GuardedErc20.vy#L242) | Same nominal liability, not custody. Lootbox uses it for global asset USD value, so full custody loss does not zero that reward-side aggregate |
| Backing predicate | None | [Guarded 248-254](../../../../contracts/vaults/GuardedErc20.vy#L248) | Derived, unstored `known && custody >= totalBalances[asset]` |
| Outbound token call | [Basic 60-63](../../../../contracts/vaults/modules/BasicVault.vy#L60) | [Guarded 257-275](../../../../contracts/vaults/GuardedErc20.vy#L257) | Typed optional-Boolean transfer becomes raw call accepting only empty or exact 32-byte canonical `true` |
| Balance observation | Typed `IERC20.balanceOf` | [Guarded 278-292](../../../../contracts/vaults/GuardedErc20.vy#L278) | Static raw call with 33-byte sentinel; failure or length other than 32 is `unknown`. The bounded copy prevents a caller-side returndata-copy bomb, but the call has no explicit gas cap |
| Validation / revert order | Basic checks pause before nominal mutation | [Guarded 61-70, 93-118, 151-165](../../../../contracts/vaults/GuardedErc20.vy#L61) | Guarded performs custody/solvency observations before reaching the pause check. Outcome still reverts, but a paused deficient asset reports backing/observation failure rather than Simple's `contract paused` |
| Withdrawal clamp | [Basic 48-58](../../../../contracts/vaults/modules/BasicVault.vy#L48) | [Guarded 116-121](../../../../contracts/vaults/GuardedErc20.vy#L116) | `min(withdrawalAmount, vaultBefore)` is defensive but unreachable as a binding clamp under prior invariants: `vaultBefore >= nominalBefore` and `withdrawalAmount <= userBalance <= nominalBefore` |
| Pause/recovery/index administration | [VaultData 103-302](../../../../contracts/vaults/modules/VaultData.vy#L103) | Exported unchanged | Same roles, selectors, and maps. Recovery uses typed transfer and no recipient-delta proof; it also rejects every registered asset, so registered surplus is immovable until liabilities reach zero and the asset is deregistered, or a migration occurs |

### 3.2 Guarded versus share/specialized vaults

| Surface | Rebase / RipeGov / StabilityPool | Guarded consequence |
| --- | --- | --- |
| Stored unit | Shares, plus specialized state in RipeGov/StabilityPool | Nominal units only; same physical base slots as Simple/Rebase but different Rebase meaning |
| Deposit measurement | Live total used to mint shares/value shares | Credits exactly the Teller-confirmed nominal amount and refuses aggregate deficit |
| Withdrawal | Converts shares/value to live amount; typed transfer | Nominal reduction plus exact outflow and recipient receipt |
| Positive yield/donation | Reprices share holders | Never credited; remains surplus |
| Loss | Reprices shares or specialized pool value | Does not allocate; freezes on any aggregate deficit |
| Zero backing | Share conversion yields zero while raw shares remain | Value getters zero, all three Guarded mutations revert |
| Extra ABI | Rebase has `amountToShares`/`sharesToAmount`; RipeGov and StabilityPool add many role-specific methods/events | Guarded has exactly the same 34 function signatures/selectors as Simple |
| Callback surface | RipeGov and StabVault interact with Ledger, Lootbox, PriceDesk, Teller, pools, and token conversions | Guarded only calls token balance/transfer and shared address resolution; consumers call it through canonical Vault |

### 3.3 Reproduced compiler, ABI, and artifact matrix

Vyper `0.4.3`, repository import root, source-owned/default `gas`
optimization, and no experimental codegen produced:

| Wrapper | Creation bytes | Runtime-template bytes | EIP-170 headroom | ABI functions | ABI events | Persistent layout |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Guarded | 10,691 | 10,524 | 14,052 | 34 | 5 | VaultData slots 0-8 |
| Simple | 8,920 | 8,753 | 15,823 | 34 | 5 | Identical to Guarded |
| Rebase | 10,526 | 10,359 | 14,217 | 36 | 5 | Same physical slots 0-8, but balances mean shares |
| RipeGov | 21,185 | 21,018 | 3,558 | 56 | 9 | VaultData 0-8 plus governance state 9-11 |
| StabilityPool | 24,028 | 23,861 | 715 | 53 | 6 | VaultData 0-8 plus claimable state 9-13 |

Guarded is 1,771 runtime bytes larger than Simple and 165 bytes larger than
Rebase. Guarded and Simple have identical method-identifier maps, persistent
layout, transient nonreentrant layout, and Addys immutable layout. Guarded's
three wrapper events replace Simple's three topics; both also expose the same
two inherited events. Rebase adds only `amountToShares` and `sharesToAmount`
to the canonical function set, but its three wrapper events also add share
fields. RipeGov and StabilityPool have materially broader role-specific ABIs.

The frozen Guarded artifact checker reproduced creation SHA-256
`64e42e5402343c3ffc8ac67b3ab92d90c9d79447e3323660de09aee5c6d30805`,
runtime-template SHA-256
`e3dae3cc8bc64712d9d95adb24674f3c363e0df43d8eb853c6b430907d544a14`,
34-selector canonical hash
`884259b81c166e48aff3cf2d424dcddf7a64eba157a58987521206dc617b1c2b`,
and committed ABI file SHA-256
`1477d537e71863a7da8c727791cdbf3e745cc31b81889a00615296148d9dafb0`.
These are constructor-bound runtime templates, not deployed runtime identities;
the immutable `_ripeHq` value must be bound before a deployed-code hash exists.

## 4. Behavioral and threat-model differences

Let `C` be an exact 32-byte observed vault custody balance and `N` the stored
aggregate nominal liability.

| State | Guarded value | Deposit | Withdrawal | Internal movement |
| --- | ---: | --- | --- | --- |
| Known `C == N` | Nominal | Exact only | Exact only | Solvent/custody-neutral only |
| Known `C > N` | Nominal | Requires `C >= N + Q`; surplus is not credited | Preserves the surplus | Does not allocate the surplus |
| Known `C < N` | Zero through two amount getters | Revert | Revert | Revert |
| Failed/malformed observation | Zero through two amount getters | Revert | Revert | Revert |

### Balance and receipt measurement

Guarded does not replace Teller's call-local receipt proof. A pre-existing
surplus can satisfy `C >= N + Q` after a short receipt, so Teller's
`C1 - C0 == Q` remains decisive. Contract-locally, a Guarded deposit performs
two new raw reads plus Basic's existing typed read; Simple performs only the
Basic typed read. A Guarded withdrawal performs four raw reads (vault and
recipient before and after) versus Simple's one typed vault-balance clamp.
Guarded internal movement performs two raw custody reads versus Simple's zero
token reads.

Positive surplus is structurally unallocated and, while the asset remains
registered, unrecoverable. `VaultData._recoverFunds` requires both
`indexOfAsset[asset] == 0` and `totalBalances[asset] == 0`
([VaultData 277-303](../../../../contracts/vaults/modules/VaultData.vy#L277)).
The normal exit is therefore to drain all nominal liabilities, deregister the
vault asset, and then recover the residue; otherwise recovery requires a
separately approved migration. This is not merely an undecided allocation
policy—the current contract has no live surplus sweep.

### Transferability assumptions

An external withdrawal supports canonical `true` and legacy empty transfer
returns, but requires exact vault decrease and recipient increase. It
intentionally rejects fees, recipient burns/taxes, reflection/excess receipt,
false, malformed/oversized returndata, and reverting transfers.

Internal movement performs no token transfer. Therefore token pause,
sender/recipient/operator blocklists, and current delivery eligibility are not
consulted. Solvency makes the acquired claim backed; it does not make it
immediately transferable. For administratively restricted Stock assets,
external delivery should be the default settlement policy unless the owner
explicitly accepts “backed claim now, delivery later” semantics.

### Liquidation composition and the auction-only invariant

Guarded's `getUserAssetAtIndexAndHasBalance` deliberately delegates to Basic,
so a deficient nonzero position is still enumerated by AuctionHouse
([Guarded 221-225](../../../../contracts/vaults/GuardedErc20.vy#L221);
[AuctionHouse 455-521](../../../../contracts/core/AuctionHouse.vy#L455)).
During `liquidateUser`, AuctionHouse iterates all user vaults and assets. If
`shouldSwapInStabPools=True` and a funded applicable Stability Pool route
reaches `_transferCollateral`
([AuctionHouse 549-577, 589-677](../../../../contracts/core/AuctionHouse.vy#L549)),
AuctionHouse calls Guarded withdrawal; the pre-solvency assertion then reverts
([Guarded 93-99](../../../../contracts/vaults/GuardedErc20.vy#L93)). Vyper has
no local try/catch, so this can
roll back the whole liquidation transaction, including work on otherwise
healthy collateral. Whether it is reached depends on vault/asset order,
remaining debt, and available pool liquidity, so a deficit does not make every
possible liquidation fail—but it creates a cross-vault bad-debt/liveness path.

Robinhood must remove that path by binding Guarded Stock to
`shouldSwapInStabPools=False`, `shouldTransferToEndaoment=False`, and
`shouldAuctionInstantly=True`. The first value prevents liquidation-time
withdrawal; the second prevents Stock from being skipped as an Endaoment asset;
the third saves Stock for an isolated auction. A later auction purchase can
still revert on deficient delivery, but that failure is buyer/asset scoped
rather than rolling back liquidation initiation. Current comparison tests
assume `shouldSwapInStabPools=False`, while frozen AAPL parameter records are
omitted/typed-null and do not enforce the full tuple.

### Guard state, zero receipt, and zero backing

There is no persistent guard enum, latch, deficit amount, or event. Guard
state is recomputed on each call. Restoring `C >= N` mechanically restores
value and liveness; that is not an allocation or recapitalization approval.
Zero requested deposit/withdraw/internal amounts reject. A true empty indexed
position remains `(0,0)`; an existing *nonzero* unsafe position becomes
`(asset,0)`, which lets CreditEngine retain configuration/terms while setting
capacity to zero.

A depleted but still registered position is different: Basic/Simple returns
`(asset,0)`, while Guarded returns `(0,0)`. CreditEngine skips Guarded's result
entirely, whereas, for configured nonzero-LTV terms, Simple fetches the asset's
debt terms, gives them weight 1, and includes them in the weighted terms and
lowest/highest LTV
([CreditEngine 726-764](../../../../contracts/core/CreditEngine.vy#L726)). This
reachable, non-guard delta matches SharesVault's zero-elision and needs a
separate compatibility decision; the current Guarded test pins its getter
result but no composed test compares the resulting Simple/Guarded borrow terms.
Guarded does not settle loss, forgive debt, apportion remaining custody, or
define permanent-total-loss handling.

The getter split is intentional but asymmetric:

- `getUserAssetAndAmountAtIndex` and `getTotalAmountForUser` are
  backing-aware because CreditEngine treats them as collateral value;
- `getVaultDataOnDeposit` remains nominal because Teller uses it for
  pre-deposit position/limit metadata, while the later Guarded mutation and
  Teller exact-receipt proof reject an unsafe deposit;
- `getUserAssetAtIndexAndHasBalance` remains nominal to preserve position
  discovery for Lootbox and AuctionHouse, which makes the auction-only
  liquidation tuple load-bearing; and
- `getTotalAmountForVault` remains nominal for aggregate liability/reward
  accounting, not spendable custody.

### Reentrancy and callbacks

All three external mutation entry points participate in Vyper's shared
transient nonreentrant lock. A token can callback during outbound transfer, but
an authorized nested Guarded mutation reverts and the outer transaction rolls
back. Static balance observations cannot mutate Guarded state. This is the same
wrapper-level mutex posture as the existing vault family, but Guarded's
adversarial callback test proves the authorization check does not mask the
mutex.

### Access control and events

Deposit is Teller-only. Withdrawal accepts Teller, AuctionHouse, or
CreditEngine. Internal movement accepts AuctionHouse or CreditEngine. Pause,
recovery, and asset deregistration remain Switchboard-controlled; user-asset
deregistration remains Lootbox-only. These are the same effective roles as
Simple. Guarded adds no authority.

The three wrapper event schemas match Simple, but their names/topics differ.
The inherited `VaultPauseModified` and `VaultFundsRecovered` events match.
Indexers and deployment tooling must bind the Guarded topics explicitly.

Guarded's pre-observations precede its pause assertions, unlike Basic. A call
against a paused and deficient/malformed asset can therefore emit
`unknown/insufficient ... backing` rather than `contract paused`. Monitoring
must classify the call and on-chain state, not key incident routing solely on
Simple's revert reason.

### Last-touch and last-balance behavior

Guarded has neither `lastTouch` nor `lastBalance` storage and never reads a
block number. Teller updates Ledger `lastTouch` in housekeeping after Teller
flows; generic AuctionHouse/CreditEngine/Deleverage composition retains its
own housekeeping order. Selecting Guarded therefore does not itself change the
Track 6 one-action-per-action-block rule.

Lootbox `lastBalance` is different: Guarded deliberately returns the nominal
`getUserLootBoxShare` and nominal `getTotalAmountForVault`. A custody loss
zeroes credit-facing amounts but does not zero reward weight or global nominal
amount. If rewards were enabled, a fully burned Stock position could continue
accruing at its full nominal user and asset weight indefinitely, until
configuration or position state changes
([Lootbox 808-833](../../../../contracts/core/Lootbox.vy#L808)). This is safe
only while Stock rewards remain disabled or a separately approved loss-aware
reward policy exists.
Backing containment must not be misrepresented as reward-interval correction.

### Unsupported and dishonest tokens

Fail-closed unsupported behavior is a security property and an availability
cost. A reverting or malformed `balanceOf` does not itself revert Guarded's two
backing-aware views: `_observeExactBalance(..., revert_on_failure=False)`
returns unknown and those views return zero so CreditEngine can continue
iterating. The same unknown result makes all three mutations revert. A
reverting/malformed transfer also reverts the withdrawal. `max_outsize=33`
bounds caller-side returndata copying, so oversized returndata is rejected
without a return-copy bomb; the remaining gas risk is callee execution because
the raw calls have no explicit gas cap. A consistently dishonest exact 32-byte
`balanceOf` can fake custody and recipient deltas; no generic vault can prove a
token's internal truth. Admission must therefore bind the exact proxy/
implementation/admin/pause/blocklist/burn/redemption model, not merely an
ERC-20 interface.

## 5. Why-new-contract analysis

A new artifact was not required by Vyper or the EVM. The guards could be
placed in Simple or Basic without adding persistent storage, and the canonical
function selectors could stay stable. The new contract was created for
semantic and operational isolation:

1. **Compatibility isolation.** Existing Simple behavior accepts a wider set
   of token responses and does not freeze all users on a one-unit deficit.
   Replacing that behavior would change established integrations and liveness.
2. **Accounting isolation.** Rebase/Shares would choose pro-rata
   loss/surplus/yield economics. Guarded intentionally chooses containment
   without allocation.
3. **Deployment clarity.** A distinct VaultBook artifact makes the asset's
   safety policy visible and reviewable. A same-name Simple runtime or mode
   makes policy depend on history/configuration.
4. **Migration isolation.** A fresh Robinhood vault starts empty. Existing
   funded Base Simple deployments remain byte-for-byte untouched; moving them
   is correctly recognized as a state migration, not a source patch.
5. **Audit isolation.** The guarded delta is reviewed against a small nominal
   predecessor. Editing Basic or Shares would recompile multiple wrappers and
   reopen their specialized semantics.
6. **Rollback isolation.** Before funding, omit/unregister the Guarded
   artifact. After positions exist, rollback is honestly treated as a
   migration rather than a mutable flag flip.

The cost is source duplication and one more artifact/slot/policy assignment.
That cost is material but smaller than the compatibility and audit blast
radius of changing the shared primitive. The depleted-index `(0,0)` behavior
is an additional compatibility delta, not part of custody containment; it
should be pinned and reviewed rather than used as evidence that Guarded is a
different accounting family.

## 6. Reusable versus specialized protections

| Protection | Reusable? | Recommended home | Backport conclusion |
| --- | --- | --- | --- |
| Teller call-local exact receipt | Yes, every inbound ERC-20 route | Teller, which performs the transfer | Already shared; retain and test, no vault backport |
| Shared nonreentrancy on mutation entry points | Yes | Each deployable wrapper / compiler shared lock | Already present across the family |
| Exact 32-byte `balanceOf` observation helper | Yes for strict assets | Internal source module when a second identical consumer exists | Reuse in future generation; do not recompile legacy vaults solely for refactoring |
| Strict empty-or-true transfer return | Broadly desirable | Outbound-custody component | Future-generation/recovery hardening candidate; compatibility-test per asset |
| Exact vault outflow and recipient receipt | Broadly desirable for external delivery | Custody-owning vault or adapter that actually transfers | Future specialized wrappers; not a blanket share/specialized backport |
| `C >= N` nominal-solvency guard | Yes for nominal liabilities | Nominal vault | Guarded/default future nominal generation, not Shares/Stab/RipeGov |
| Backing-aware credit amount | Yes where raw accounting can outlive custody | Vault getter plus consumer zero semantics | Guarded and consumer policy; share vault already reports live amounts |
| Freeze every mutation on any deficit | Policy-specific | Specialized nominal vault | Appropriate for Guarded; not universal |
| Endaoment Funds/PSM recipient rejection | Robinhood/Stock route-specific | Guarded or explicit settlement policy | Do not put in Basic/Simple/shared token helper |
| Nominal Lootbox reward share | Existing behavior, not a protection | Vault/reward policy | Do not generalize; Stock rewards should remain disabled until resolved |
| Recovery strict recipient delta | Desirable defense-in-depth | Future shared recovery helper | Current inherited recovery is narrower but not exact; no current-source change recommended |

Backporting the complete Guarded behavior would change Base behavior even if
ABI and storage stayed identical: new reverts, stricter token acceptance,
different deficit and depleted-index values, different weighted debt terms,
different gas, a global-per-asset freeze, and new event identities or
same-name semantic divergence. Existing immutable deployments would not change
until migrated, but all future compilations and integrations using the edited
source would.

## 7. Deployment policy recommendation

### Robinhood

1. Deploy a distinct Guarded artifact and bind a reviewed VaultBook slot; the
   current repository has source, ABI, and artifact expectations but no final
   Stock asset value or Guarded slot in Robinhood defaults/blueprint.
2. Assign every initial Stock/issuer-controlled borrow-enabled nominal asset
   only to Guarded. Do not make the same asset simultaneously valid in Simple,
   Rebase, StabilityPool, Endaoment, or an unreviewed adapter.
3. Keep external delivery as the default auction/deleverage settlement for an
   asset with pause/blocklist controls. If internal settlement remains enabled,
   label it as backed-claim settlement, not delivery.
4. Deploy StabilityPool for its GREEN role and RipeGov for RIPE governance.
   Keep Stock out of both.
5. Omit Rebase at launch unless a concrete asset has approved positive
   rebase/yield/share semantics and its zero-backing policy is separately
   accepted.
6. Simple may be deployed for explicitly non-borrowing ordinary LP/deposit
   routes or exact non-confiscatable nominal assets, but it must not be the
   fallback for a failed Guarded compatibility test.
7. Bind each Guarded Stock asset to
   `shouldSwapInStabPools=False`,
   `shouldTransferToEndaoment=False`, and
   `shouldAuctionInstantly=True`. Treat any drift or omitted value as an
   activation stop. This auction-only tuple prevents deficit-triggered
   Stability Pool withdrawal from rolling back the user's whole multi-vault
   liquidation while still preserving an asset-scoped auction path.
8. Before activation, bind exact token implementation/admin behavior,
   exact-return compatibility, raw balance truth/liveness, events/indexing,
   VaultBook ID, route exclusions, the liquidation tuple, rewards-disabled
   posture, monitoring, and rollback stage.

### Current deployment/configuration surface

| Surface | Frozen-baseline fact | Consequence |
| --- | --- | --- |
| Base repository migrations and test deployment | Base migration [`2025071504_VaultBook.py:19-34`](../../../../migrations/base-mainnet/2025071504_VaultBook.py#L19), legacy migration [`1008_VaultBook.py:19-48`](../../../../migrations/base-mainnet/1008_VaultBook.py#L19), and the test fixture [`conf_core.py:669-685`](../../../../tests/conf_core.py#L669) register StabilityPool, RipeGov, Simple, and Rebase as IDs 1-4 | This is repository migration evidence, not current live-chain RPC verification. Guarded is not retrofitted into those migrations, and this reassessment made no live-deployment claim |
| Base defaults | Many ordinary assets refer to nominal vault ID 3; some yield-vault tokens appear as assets routed to other registered vault IDs | A token being yield-bearing does not make the Ripe deposit wrapper share-based; assignment and underlying-token semantics must both be reviewed |
| Robinhood blueprint | StabilityPool 1 and RipeGov 2 are required; Simple 3 is the documented ordinary role; Rebase 4 is omitted; Guarded Stock placement is a separate blocked/unbound slot | Source integration is not registry/deployment completion |
| Robinhood defaults | AAPL/Stock identity, vault IDs, risk, and routes are launch omissions, not zero values or future bindings | No report may infer an active Guarded asset from source/artifact presence |
| Robinhood liquidation fields | AAPL `shouldTransferToEndaoment`, `shouldSwapInStabPools`, and `shouldAuctionInstantly` are omitted/typed-null in `robinhood-parameters.json`; comparison tests set swap false and normally auction true, but no final configuration enforces the tuple | Guarded Stock activation remains blocked until the exact auction-only tuple is bound and checked atomically |
| ABI export | `scripts/abis/GuardedErc20.json` exists and matches the frozen compiler output | Tooling can bind the artifact, but an ABI file is not a deployment |
| Artifact expectations | Guarded source, compiler inputs, constructor, ABI, selectors, events, layouts, creation/runtime hashes, and size are fail-closed expectations | Any source/module/compiler refactor requires regeneration and review |
| Consumer inventory | Six core sources and all current Vault getter call sites are source-hash bound and classified | New files/interfaces or indirect wrappers need inventory extension, not an assumption of coverage |

### Future chains and deployments

Use an asset-capability decision, not a chain-name decision:

| Asset capability | Default vault policy |
| --- | --- |
| Fixed nominal unit; exact transfer; custody can change externally | Guarded nominal |
| Fixed nominal unit; custody cannot change externally; no borrow or only constrained deposit route | Guarded preferred; Simple allowed only by explicit compatibility/risk record |
| Positive rebase/yield where holders should share gains/losses | Share vault after explicit zero/post-zero/reward policy |
| Stability/claim/redemption role | Dedicated StabilityPool generation |
| RIPE governance/locks/points | Dedicated RipeGov generation |
| Fee/reflection/nonexact delivery | Reject or design a separate measured adapter/vault; never silently fall back to Simple |
| Dishonest/unbounded balance observation or unacceptable admin power | Reject |

Every future borrow-enabled Guarded collateral deployment also inherits the
auction-only liquidation rule unless a later architecture review proves another
route cannot synchronously call a Guarded mutation during multi-asset
liquidation. Asset admission and liquidation-route admission are one atomic
policy decision.

Legacy deployed vaults remain legacy. Do not redefine their source name and
call that migration. Review live exposure asset by asset, then migrate only
through separately approved custody, position, debt, auction, configuration,
index, event/indexer, and rollback procedures.

## 8. Alternative architecture comparison

| Alternative | Security | Compatibility | Migration needs | ABI / storage | Gas / bytecode | Code reuse | Audit surface | Consumer blast radius | Deployment policy | Rollback |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Retain separate Guarded (recommended)** | Strong containment for exact nominal assets; assignment, auction-route, and fail-closed liveness risk remain | Additive for fresh assets; canonical calls remain compatible, with distinct events and stricter zero/revert semantics | None for fresh Robinhood assets; funded Simple positions need full custody/debt/index migration | Same 34 selectors and persistent/transient/immutable layouts as Simple; three event topics differ | Creation 10,691; runtime 10,524; +1,771 runtime bytes. Adds observations to every mutation | Duplicates some wrapper logic; future helper extraction remains possible | Smallest source delta and isolated artifact/asset policy review | Assigned assets only; generic consumers must tolerate zero/revert and depleted-index semantics | Explicit VaultBook slot, exclusive asset assignment, exact token admission, and auction-only liquidation tuple | Omit before funding; after positions, pause and perform an approved stateful migration |
| **Modify Simple and migrate all consumers** | Makes nominal guards default, but universal deficit freeze and strict-token policy create broad DoS/config risk | Breaks established token/liveness, depleted-index, gas, monitoring, and possibly event expectations | Redeploy and migrate every funded Simple position; immutable deployed Base code cannot change | Selectors/layout could remain; same-name events would conceal runtime/semantic divergence | Guarded-size overhead applies to all Simple operations/assets | Highest source reuse; one nominal implementation | Reopens every Simple asset, consumer, token variant, and Base regression | Every Simple user, asset, consumer, operator, and indexer | Replace default generation and atomically rebind all assets/configuration | No safe flag rollback; funded rollback is another full migration |
| **Extract shared guarded module** | Sound only for consumers with identical invariants; a generic helper can leak nominal assumptions into share/special vaults | Guarded-only extraction is behavior-compatible if bytecode proves equal; importing elsewhere recompiles those wrappers | No state migration for a Guarded-only refactor, but every changed wrapper needs redeployment to use it | Storage-free internal module can preserve ABI/layout; compiler-input and artifact hashes change | Static composition keeps runtime calls/code near current size; no deployed library dedup | Best source-level reuse after a second identical production use | Adds dependency and cross-artifact review; today broader than the direct wrapper delta | Guarded-only is narrow; Basic/Shares/Stab adoption is family-wide | Version and deploy each consuming artifact; never silently replace legacy source identities | Choose prior artifact before funding; migrate any funded changed wrapper |
| **Opt-in mode in existing vaults** | Mode/config transitions can disable safety; two semantic modes multiply invariant combinations | Existing deployments cannot gain an immutable mode; mutable mode changes trust and observability | Immutable mode requires redeploy/migration; mutable mode also needs authority/storage transition policy | Constructor/code layout changes if immutable; persistent slot/getter/authority/event impact if mutable | Branch and guard calls increase code/gas even when off; both modes need full tests | High apparent reuse in one wrapper | Largest state-space per artifact plus governance/config audit | All instances, defaults, builders, migrations, indexers, and operators | Every deployment must bind, monitor, and lock mode plus token/route policy | Flag rollback is unsafe because it disables containment; immutable rollback requires migration |
| **Token adapter** | Can normalize calls or express shares, but cannot prove dishonest underlying backing; adds custody, allowance, oracle, callback, and upgrade risks | Introduces a new asset identity and may change price, reward, liquidation, and UI assumptions | Deploy adapter; migrate positions/config/oracles/routes; provision unwrap liquidity and authority | New adapter ABI/storage; vault may hold receipts rather than underlying | Extra calls and usually more aggregate bytecode/deployment/transaction gas | Reuses an adapter across assets only if semantics truly match | Moves rather than removes audit work; adds adapter-underlying composition | Teller, PriceDesk, MissionControl, VaultBook, liquidation, rewards, and indexers | Admit both adapter and underlying, cap/monitor backing, and bind unwind route | Requires unwrapping plus state/config migration; adapter failure may obstruct exit |
| **Broader new vault generation; preserve legacy** | Best long-term separation if nominal/share/transfer/loss policies are explicit; overdesign remains a risk | Additive and legacy-preserving; each new asset opts into a version | No legacy migration unless voluntarily adopted; each funded adoption is stateful | Canonical Vault can remain; new policy may require new ABI/storage/artifact identity | Likely larger initially; compile-time specialization can avoid inactive branches | Can consolidate proven helpers and policy components | Full new-generation audit rather than Guarded delta review | New assets initially; broader only by explicit later adoption | Versioned artifact/capability matrix with no in-place semantic replacement | Select old/new artifact before funding; funded rollback follows explicit migration stage |

The practical sequencing is: retain Guarded now; use it as the default
borrow-enabled nominal generation on new chains; extract only proven-identical
helpers later; design a broader generation only when a second accounting
policy requires more than Guarded can express.

## 9. Current tests and exact missing tests

### Current evidence

The focused selection collected 212 cases across:

- `tests/vaults/test_guarded_erc20.py`;
- `tests/vaults/test_guarded_consumer_inventory.py`;
- `tests/vaults/test_stock_token_vault_comparison.py`;
- `tests/core/creditEngine/test_stock_backing.py`;
- `tests/core/auctionHouse/test_auctionhouse_stock_delivery.py`;
- `tests/core/deleverage/test_deleverage_stock_delivery.py`; and
- `tests/inventory/test_contract_artifacts.py`.

The first run was blocked before test bodies because the process sandbox
denied the local Anvil fixture's loopback bind. The unchanged rerun with
loopback permission and all RPC/private-key variables unset produced:
`212 passed, 3 warnings in 337.89s`. The interpreter was
`/Users/wigglez/dev/ripe-protocol-validation-envs/rh-wave2-py312/bin/python`;
its installed-package manifest SHA-256 was the test-pinned
`9d1b066c4d8c96bff1c97cdcd243905b8c02324b434c962553a1f1b58886df92`.
An earlier ambient-`ripe-lite` attempt produced 211 behavioral/artifact passes
and only the intended package-manifest mismatch; it is not the controlling
result.

A reviewer-followup selection reran the exact depleted-index, registered
recovery, mixed-collateral health, deficit-auction rollback, Stock-swap
omission, and test-harness asset-policy evidence in the same frozen
interpreter: `8 passed, 3 warnings in 107.66s`. It confirms the cited current
behavior; it does not substitute for the new composed/configuration tests
listed below.

The Guarded suite covers exact deposits at 6/18 decimals, surplus, one-unit
deficit, malformed/failed observations, empty versus unsafe positions,
partial/full/over-request internal moves, transfer-control independence,
post-read rollback, external outflow/delivery, return-data variants, fee/burn/
reflection behavior, authorized callback reentrancy, seven guard mutations,
real Teller batches and later-row rollback, Endaoment exclusions, roles/pause,
and inherited recovery boundaries. Consumer suites cover CreditEngine value,
AuctionHouse internal/external/batch settlement, Deleverage swaps, and a
source-hash-bound getter inventory. The artifact checker reproduces the frozen
compiler, ABI, selector, event, layout, bytecode, and integrity facts. The
selection does **not** compose a deficient Guarded asset with other healthy
collateral during liquidation initiation, compare depleted registered
Simple/Guarded debt terms, or bind the complete auction-only Stock
configuration tuple.

### Exact missing tests

These are missing evidence, not findings that current source is defective:

1. `test_guarded_and_simple_canonical_function_selectors_and_layout_match`:
   checked-in direct equality for all function selectors, persistent layout,
   transient lock, immutable layout, and constructor, rather than relying on
   separate frozen facts.
2. `test_guarded_event_topics_are_intentionally_distinct_and_indexer_bound`:
   exact topic hashes and an indexer/deployment consumer that selects Guarded
   topics.
3. `test_guarded_operation_gas_delta_against_simple_at_fixed_token`:
   reproducible deposit, withdrawal, internal movement, backing-aware view, and
   revert-path gas, including cold/warm observations.
4. `test_guarded_balance_call_gas_grief_fails_atomically`:
   a balance/transfer implementation that consumes near-all forwarded gas and
   proof of complete rollback/operational classification.
5. `test_exact_but_dishonest_balance_observer_documents_trust_boundary`:
   show that self-consistent false 32-byte balances can defeat observation,
   preventing reviewers from overstating the guard.
6. `test_guarded_internal_settlement_during_pause_is_backed_but_not_delivered`:
   composed AuctionHouse evidence that explicitly separates accounting safety
   from transferability and verifies the selected external/internal policy.
7. `test_guarded_loss_does_not_zero_lootbox_last_balance`:
   pin that a fully burned position continues accruing indefinitely at nominal
   user/global weight if enabled, prove Stock reward configuration stays
   disabled, and add the corresponding activation-negative test.
8. `test_guarded_restoration_resumes_mechanically_but_configuration_stays_disabled`:
   reduce custody below nominal, restore it, verify claims are not repriced,
   and prove operations cannot resume through deployment configuration without
   the separately authorized enablement.
9. `test_endpoint_rotation_updates_guard_without_stale_recipient`:
   change the RipeHq-resolved Endaoment address in the local harness and prove
   the old/current recipient consequences and configuration stop.
10. `test_every_value_consumer_uses_backing_aware_amount_after_source_change`:
    extend the inventory gate to fail on new interfaces, aliases, indirect
    wrappers, or new production files, not only the current regex getter scope.
11. `test_guarded_deficit_does_not_block_liquidation_of_other_collateral`:
    build a user with healthy ordinary collateral and deficient Guarded Stock;
    with the auction-only tuple, prove liquidation initiation succeeds,
    preserves healthy-route work, and saves Stock for auction without calling
    Guarded mutation. Add a negative variant with a funded applicable Stability
    Pool and `shouldSwapInStabPools=True` that proves the whole transaction
    reverts, making the configuration dependency mutation-sensitive.
12. `test_guarded_stock_liquidation_and_assignment_config_invariant`:
    final deployment-plan/default assertion that every Guarded Stock asset has
    `shouldSwapInStabPools=False`,
    `shouldTransferToEndaoment=False`,
    `shouldAuctionInstantly=True`, is absent from Simple/specialized vaults, and
    fails closed on omission or any one-field mutation.
13. `test_depleted_registered_position_term_semantics_guarded_vs_simple`:
    fully withdraw without Lootbox deregistration, prove Simple returns
    `(asset,0)` and contributes weight-1 debt terms/lowest/highest LTV, prove
    Guarded returns `(0,0)` and is skipped, and freeze the intended compatibility
    policy.
14. `test_registered_guarded_surplus_is_unrecoverable_until_cleanup`:
    prove donated surplus cannot be recovered while registered, then drain
    nominal claims, deregister, recover, and verify exact residue and event.
15. Exact-token proxy/implementation tests for raw response length,
    truthful balances, pause/blocklists, admin burn/force transfer/redemption,
    upgrade behavior, and repeated-read liveness. These require a later exact
    token and deployment freeze; mocks are not sufficient.

## 10. Recommended implementation scope, if any

No contract implementation is recommended by this reassessment.

The owner will combine the release-gate tests with Teller, Ledger,
external-integration, and fork-suite findings in one larger, separately
authorized implementation wave. Within that future wave, the Guarded lane
should remain limited to deployment/configuration evidence and the missing
tests above:

- bind the existing Guarded source/ABI/artifact to an explicit VaultBook slot;
- bind relevant assets only after exact-token qualification;
- enforce mutually exclusive vault assignment and the exact auction-only
  liquidation tuple;
- keep Stock rewards disabled;
- add the missing liquidation-composition, depleted-index, surplus-recovery,
  static equality, gas, reward, transferability, restoration, and
  deployment-policy tests;
- update only the deployment/default/manifest/inventory and test surfaces
  expressly authorized for that phase; consume the existing ABI without
  changing it.

Do not edit Guarded, Simple, Basic, Shares, VaultData, RipeGov, StabilityPool,
or Vault.vyi merely to reduce duplication. If a second production wrapper
later needs strict balance/transfer helpers, propose a storage-free internal
module with compiled before/after artifact and mutation evidence for every
consumer. Do not combine that refactor with asset activation.

For Base, first inventory exact live assets and controls. Conventional assets
without an external custody-reduction path do not acquire the Stock threat
merely because repository Simple has weaker invariants. Migrate only assets
whose evidence justifies the operational risk.

## 11. Owner decisions

Appendix A records the controlling owner disposition. The following are the
remaining execution-specific choices or evidence bindings; none may silently
override that disposition:

1. the deployment owner must choose and record the exact distinct Guarded
   VaultBook ID/name rather than infer it from Base;
2. every non-Stock asset proposed for Simple needs an explicit ordinary-asset
   classification and approval;
3. final token/proxy/implementation/admin identities and the complete transfer,
   pause, blocklist, burn/force-transfer, upgrade, exact-return, and liveness
   qualification record;
4. monitoring thresholds, pause authority, incident response, restoration
   approval, rollback procedures, and classification that does not rely solely
   on Simple's revert reasons;
5. any future proposal for backed-internal auction settlement, Stock rewards,
   Rebase/share-yield deployment, or a non-auction-only liquidation route must
   enter the separate review required by Appendix A;
6. any later funded Base migration must begin from independently verified live
   deployment facts, not repository migrations or fixtures; and
7. any future shared-module extraction or broader vault generation remains a
   separate architecture/audit decision after a second proven production use.

Permanent-loss, recapitalization, bad-debt, user-allocation, and alternative
surplus policy are expressly not reopened by this task. None of the remaining
choices authorizes modification of the current Guarded or legacy vault source.
Unbound exact slot/token/configuration/procedure evidence is an activation
stop, not an architecture defect.

## 12. Residual risks and non-actions

### Residual risks

- exact-shape observations can still be dishonest;
- raw token calls have no explicit gas cap and callee execution can deny
  service, although the 33-byte output bound prevents a caller-side
  returndata-copy bomb;
- a one-unit deficit freezes every user's mutation for that asset and, if a
  funded Stability Pool route is mistakenly enabled, can revert the entire
  multi-vault liquidation transaction and obstruct healthy-collateral
  processing;
- restoration automatically restores contract liveness even though operational
  approval may still be required;
- internal settlement proves backing, not current token deliverability;
- a depleted registered position is skipped by Guarded/CreditEngine but
  contributes weight-1 debt terms in Simple/CreditEngine;
- nominal reward weight can remain fully active indefinitely after total
  custody loss if Stock rewards are enabled;
- registered surplus has no live recovery path until nominal liabilities are
  drained and the asset is deregistered, or a migration is approved;
- loss, debt, auction completion, surplus allocation, and bad-debt policy
  remain outside Guarded;
- inherited recovery uses typed transfer behavior and does not prove recipient
  delta;
- a distinct artifact introduces VaultBook assignment and indexer/event
  configuration risk;
- strict behavior intentionally excludes some ERC-20 variants; weakening it
  to admit them would remove the safety property;
- existing Base deployments are not changed or remediated by repository source
  or this report.

### Non-actions

This reassessment:

- used no RPC, account, key, signer, transaction, deployment, or external
  state;
- changed no contract, module, interface, ABI, configuration, builder,
  inventory, migration, existing document, or Git ref after the explicitly
  requested worktree branch was created;
- did not stage, commit, push, deploy, activate, or release;
- does not approve a token, VaultBook slot, migration, or Robinhood launch;
- does not recommend changing `SimpleErc20` in place;
- does not recommend a mutable guarded mode or a token adapter as a substitute
  for vault solvency;
- does not recommend refactoring solely to reduce line duplication; and
- creates only the now-explicitly-authorized byte-identical durable archive
  copy outside Git worktrees; that preservation copy is the sole external
  filesystem write and does not authorize deployment/configuration state; and
- does not claim that passing local tests resolves the exact-token or
  deployment-policy gates.

## Appendix A. Controlling owner disposition

This owner disposition controls the GuardedErc20 reassessment wherever an
earlier recommendation, open decision, or implementation sequence could be
read differently:

1. Preserve `GuardedErc20` as a separate specialized vault.
2. Do not modify `SimpleErc20`, `BasicVault`, `SharesVault`, `VaultData`,
   `RipeGov`, `StabilityPool`, or `Vault.vyi` to backport Guarded behavior.
3. Do not introduce a mutable guarded mode or token adapter as a substitute.
4. Deploy Guarded for every Robinhood Stock or issuer-controlled,
   borrow-enabled nominal asset.
5. Assign each such asset exclusively to Guarded. It must not simultaneously
   be valid in Simple, Rebase, StabilityPool, Endaoment, or an unreviewed
   adapter.
6. Bind a distinct reviewed Guarded VaultBook slot during deployment
   preparation. The deployment owner must choose and record the exact ID/name;
   it must not be inferred from Base.
7. Simple may be used only for explicitly classified ordinary assets whose
   custody, transfer, loss, and borrowing behavior has been separately
   approved. It must never be a fallback after a Guarded compatibility failure.
8. Omit Rebase/share-yield vaults at launch unless a concrete asset has
   approved positive-rebase/share economics and a separate zero/post-zero
   policy.
9. Preserve the required atomic liquidation-initiation tuple for every Guarded
   Stock asset:

   - `shouldSwapInStabPools = False`
   - `shouldTransferToEndaoment = False`
   - `shouldAuctionInstantly = True`

10. Treat omission, null, default inference, or mutation of any one tuple field
    as an activation stop.
11. Keep external delivery as the default auction-purchase settlement for
    paused or blocklisted Stock assets.
12. If backed internal settlement is ever enabled, describe it as backed-claim
    settlement rather than token delivery and require separate review.
13. Keep Stock out of StabilityPool, Endaoment, RipeGov, and other synchronous
    liquidation routes unless a later composed-route review proves safety.
14. Keep Stock rewards disabled. A fully burned Guarded position can otherwise
    continue contributing nominal Lootbox weight indefinitely.
15. Any future Stock reward activation requires a separate reward/loss policy
    and explicit activation-negative tests.
16. Preserve current surplus behavior: registered surplus remains unallocated
    and unrecoverable until nominal liabilities reach zero and the asset is
    deregistered, unless a separately approved migration creates another path.
17. Do not reopen permanent-loss, recapitalization, bad-debt, or
    user-allocation policy in this task.
18. Require exact token, proxy, implementation, admin, pause, blocklist,
    burn/force-transfer, upgrade, exact-return, and repeated-read-liveness
    qualification before activating any Guarded asset.
19. Require monitoring, pause authority, restoration approval, incident
    response, and rollback procedures before activation.
20. Do not infer live Base deployment facts from repository migrations or test
    fixtures.

### Release-gate tests

The following missing evidence is a release gate, not optional follow-up:

- cross-vault liquidation succeeds with the approved auction-only tuple;
- the negative StabilityPool/swap variant proves the complete transaction
  reverts, pinning the denial-of-service hazard;
- every Guarded Stock assignment and all three tuple fields are machine-bound
  and fail closed on omission or mutation;
- Guarded/Simple selector, layout, constructor, and event-topic comparison;
- deficient, depleted, restored, and surplus-bearing position behavior;
- Lootbox loss behavior and Stock-rewards-disabled activation checks;
- external versus backed-internal auction settlement;
- endpoint rotation;
- balance-call gas grief and dishonest balance observations;
- every value consumer remains backing-aware; and
- final token/proxy/implementation behavior after identities are frozen.

No Guarded, Simple, module, interface, ABI, or storage change is authorized.
No release-gate test is implemented by this reassessment. These test
requirements will be combined with Teller, Ledger, external-integration, and
fork-suite findings into one larger, separately authorized implementation
wave.
