# Track 8 M0: Stock Token launch evidence and product-freeze record

**Status:** Evidence collected; **M0 has not passed** because the exact
Robinhood runtime asset set, initial cross-chain graph, and day-one reward
policy are not frozen.

**Evidence date:** 24 July 2026

**Controlling integration commit:**
`2517eeb0013cdb277dc4815db4b524d7a090d682`

**Evidence branch:** `rh-track-8-m0-evidence`

**Scope:** Documentation and read-only evidence only. This record does not
approve M1, a production contract, a vault or VaultBook ID, an interface,
storage, ABI, default, migration, manifest, deployment, configuration, signed
message, or transaction.

## 1. Executive conclusion

M0 returns three hard stops and one incomplete fork-refresh item to the owner.
It does not widen the launch design.

1. **Robinhood asset-inventory stop.** The repository requires Stock Tokens at
   launch, but does not yet name every launch Stock Token or freeze every
   non-Stock asset and route in the Robinhood Teller graph. AAPL is the only
   exact Stock Token with a complete address and historical pinned-fork record.
   `RIPE`, `GREEN`, `sGREEN`, USDG, other Stock Tokens, and any other collateral
   remain included, omitted, disabled, or address-pending according to other
   open Robinhood decisions. Because `deposit`, `depositMany`, `rebalance`,
   `depositIntoGovVault`, Stability Pool auto-deposit, and trusted Deleverage
   can collectively reach any configured asset, an unfrozen configuration is
   an unfrozen compatibility matrix. This is an unknown Robinhood runtime-asset
   hard stop before M1.
2. **Cross-chain graph stop.** No Robinhood Ripe deployment, migration history,
   or final manifest exists at the controlling commit. Current production
   source contains no bridge or message implementation, so separate
   deployments can be state-independent if all cross-chain routes are omitted
   or inactive. The repository separately proposes GREEN/RIPE CCIP burn/mint
   transport, however. If active at initial launch, a Base-created GREEN supply
   or solvency failure can propagate economically into Robinhood token supply,
   liquidity, repayment, PSM, and accounting paths. The initial CCIP
   include/omit decision therefore must be frozen before state independence can
   pass.
3. **Reward-policy stop.** The current reward system has an account-wide
   borrower bucket and a global generic-depositor bucket. Per-asset Stock
   allocations of zero do not by themselves exclude a Stock-backed borrower or
   a Stock depositor from those global point classes. There is no approved
   Robinhood reward configuration. The owner must either disable rewards
   globally, set every Stock-capable global bucket to zero while setting Stock
   per-asset allocations to zero, or declare Stock-linked launch rewards
   required. The last option reopens the reward-loss scope and stops M1.
4. **Fork refresh incomplete, existing fork evidence intact.** The integrated
   Track 2 pinned AAPL fork remains reproducible in its committed input and
   records exact base-unit deposit and withdrawal. Fresh M0 live reads show the
   same proxy, beacon, implementation, and runtime hashes. A fresh execution of
   the historical fork did not complete because the two credential-free
   providers returned rate-limit or historical-metadata errors before local
   fork mutation. The owner or independent reviewer must decide whether the
   immutable integrated run plus current identity match is sufficient, or
   require a later credential-free/archive-capable rerun.

The refreshed Base snapshot does **not** trip Track 8's urgent-live criterion:
all nine custody-positive ID-3 assets had `C >= N`; WETH retained its known
one-unit surplus; no active fungible auction was enumerated; and no live
short-receipt path was reproduced. Base remains exposed to the three latent
legacy mechanisms identified in the controlling specification, but this
snapshot does not make a stateful Base core cutover a Robinhood launch
prerequisite.

## 2. Repository and source provenance

### 2.1 Worktree bootstrap

The worktree was created from the exact integrated commit:

```text
git worktree add -b rh-track-8-m0-evidence \
  /Users/wigglez/dev/ripe-protocol-track-8-m0-evidence \
  2517eeb0013cdb277dc4815db4b524d7a090d682
```

At creation:

- `HEAD`, local `rh`, and their merge base were
  `2517eeb0013cdb277dc4815db4b524d7a090d682`;
- the worktree was clean;
- the M0 branch and worktree path did not previously exist; and
- this file did not previously exist.

### 2.2 Controlling and load-bearing file hashes

All hashes are SHA-256 over the file at the controlling integration commit.

| File | SHA-256 |
| --- | --- |
| `docs/chains/rh/stock-token-vault-change-specification.md` | `71099e629734e7f001a8cbfa40792dfc2ab9fbc5490cd8b9c80a8431a994705c` |
| `docs/chains/rh/stock-token-vault-change-validation-plan.md` | `88edaf44fa375a7310cb73bec254d5801478e89479d51ded0c439f33a9a81bb1` |
| `docs/chains/rh/stock-token-transferability-evidence.md` | `01d7441e7338924316fcb14d159689625f83f0db35384a1c3d0ec56c27b22ba6` |
| `scripts/probes/aapl-robinhood-mainnet-fork.json` | `8193229d32a19e8ef3d4fb55d5dd4a54b00bda9e8257a1ba307603b9858a5f77` |
| `scripts/probes/stock_token_transfer_probe.py` | `5e72ceab7a37bac5a6ff2dc179a33dad9f5999c2d41adae966e4f90880416f1f` |
| `contracts/testing/StockTokenTransferProbe.vy` | `dcf632f75def3d55203731856e5c2813237235bf72c6b8586400c9f858c3046a` |
| `migration_history/base-mainnet/v1/current-manifest.json` | `06ac6dcf3d5c3d2366bd33118023fd6603fc4d759a7a5103901b29ae67007b00` |
| `contracts/core/Teller.vy` | `51cf13e3c9d58262ba446a462332d8f4f181c07ce689031b2398c20137f04198` |
| `contracts/core/CreditEngine.vy` | `23129f8f6e87805bc47712d06f7ddf6c0de920866ad36ca78ee96e9c57ef96d8` |
| `contracts/data/Ledger.vy` | `00d86847273621857b80701be5faf7ca88ff9505f68671d5b6ab3c8b4ec972e0` |
| `contracts/data/MissionControl.vy` | `5110d7ccea635b96fd88fe818afd97494cfe9d47648cd09f4632e8c68d0f19a1` |
| `contracts/core/Lootbox.vy` | `669c2857e2402ef0e8f9a508dd6f342426ffbd1affce11dd429e5b5b0129ae65` |
| `contracts/modules/Addys.vy` | `2a46a2fbb26fed9ed5d59414833fb6c2f85a7ddf72e82ffc2d6e122296e1d4e6` |
| `contracts/vaults/SimpleErc20.vy` | `6b6794f1e5aaef3b53c3e931eb8fe3596aa3d44dc5d4dcc17f487340f5c89c22` |
| `contracts/vaults/modules/BasicVault.vy` | `a21a33be9b805f5ce4fd42c66f976525032b92836149c74526be613dae79d89d` |
| `contracts/vaults/modules/VaultData.vy` | `d84d81ccf45405954404fa6af2c6651ed251efeca958242934eda8f032917e7f` |
| `contracts/config/DefaultsBase.vy` | `be475cce20fb66baf62fbdf3815a3e5afca1881fc5174484fd38cb508bf8e50b` |
| `docs/chains/rh-summary.md` | `8a44754bccfbc7698e71421b57fb2c591808a838fa91c7005223bfdff2ae97ea` |
| `docs/chains/rh/robinhood-deployment-support-specification.md` | `9a85d0a0307ce8fc6d268d6c48ab9a27bc60a75f8cbb655e88220020e7482698` |
| `docs/chains/rh/minimal-contract-change-reassessment.md` | `e29a1163b4cb1b4837ed8857775e9d1ea557bd3dc56213a594fa3fde0267987f` |

The controlling specification and validation plan were not edited during M0.

## 3. RPC, indexer, and fork evidence ledger

No endpoint below contains a credential. No request signed or broadcast a
transaction.

| Evidence ID | Chain and pin | Endpoint/provider class | Contracts and runtime identity | Retrieval result |
| --- | --- | --- | --- | --- |
| RH-M0-01 | Robinhood mainnet `4663`; block `18,538,327`; hash `0x1f3920aded6d22dd6afc0234d7b0088bdbdfcdc98bd40cddb8e6dbd8e8889eba`; `2026-07-24T23:18:57Z` | Official public Robinhood JSON-RPC, `https://rpc.mainnet.chain.robinhood.com`; credential-free, rate-limited | AAPL proxy, beacon/registry, implementation; exact hashes in Section 5 | Identity, pause, multiplier, supply, balance, and blocklist reads succeeded at `2026-07-24T23:18:59Z`. |
| RH-T2-01 | Robinhood mainnet `4663`; block `17,558,441`; hash `0x35e8e2a3803cb42c4553cb5f3528b187508c6cc200a8b761943374003b8f0243`; `2026-07-23T18:52:41Z` | Official public Robinhood JSON-RPC; local `boa` fork; integrated Track 2 record | Same three AAPL identities and hashes as RH-M0-01; probe hash `0xaa9b728174d048a5d65f49f5b4c851413008d6b89f315d36256191bd1a402949` | Integrated exact approve/deposit/withdraw/cleanup fork passed; no live transaction. |
| BASE-M0-01 | Base mainnet `8453`; block `49,072,790`; tag `0x2ecca96`; hash `0x40e350e456725c0e1801a32d8fd948f82b33a281365c826bd697f15d411db57b`; `2026-07-24T23:15:27Z` | PublicNode credential-free public RPC, `https://base-rpc.publicnode.com`, for the complete batched state snapshot, with the official Base public RPC `https://mainnet.base.org` used for exact-block runtime-hash and aggregate-debt confirmation | SimpleErc20 `0xf75b…ddfD`, hash `0x1d0ec5…34eb7`; MissionControl `0x559E…BC19`, hash `0x0428c8…90f5`; Ledger `0x3652…fA47`, hash `0xdcb945…1b7d`; all 27 token hashes in Section 6 | Complete 27-row custody/nominal/config snapshot, aggregate debt/reward state, and exact-block token runtime hashes. |
| BASE-M0-02 | Base mainnet `8453`; block `49,072,974`; hash `0x221cc559c736530bfd88bbd1864e557e2aa6ff8ca239e486f17bc98de2f1022d`; `2026-07-24T23:21:35Z` | PublicNode credential-free public RPC, `https://base-rpc.publicnode.com` | Twelve manifest-resolved Base core/token contracts; exact addresses and hashes in Section 7 | Companion live core-runtime inventory for the state-independence proof. |

The official Base RPC first returned block `49,072,665`,
`0xc5f0b240233c9bd26942bdd6b9fed0841d652ff3b2bfb46ee54c381995f81871`,
then rate-limited the first sequential bulk attempt with HTTP `429`. That
partial output was discarded. PublicNode completed BASE-M0-01 in batched
read-only calls; the official endpoint then independently confirmed the
exact-block runtime hashes and aggregate values.

The fresh historical AAPL fork attempt did not produce a new fork result:

- the official RPC first returned HTTP `429` during preflight;
- a paced retry later returned
  `metadata is not found, 17558444` while the approved pin was being prepared;
  and
- Blockscout's credential-free `/api/eth-rpc` endpoint returned HTTP `429`
  before `boa` initialized local fork state.

All failures occurred before local fork mutation. No failed or blank response
is used as token evidence. The exact prior fork result remains RH-T2-01, and
the current live identity comparison is RH-M0-01.

### 3.1 Reproducible request shapes

The state tables were decoded from these calls at the exact block tag shown
above. The batched request used the same calldata as the command shapes.

```text
cast block <block> --rpc-url <credential-free-endpoint> --json
cast code <contract> --block <block> --rpc-url <endpoint>
cast keccak <returned-runtime-code>

cast call <simple-vault> 'getNumVaultAssets()(uint256)' \
  --block <block> --rpc-url <endpoint>
cast call <simple-vault> 'vaultAssets(uint256)(address)' <index> \
  --block <block> --rpc-url <endpoint>
cast call <asset> 'balanceOf(address)(uint256)' <simple-vault> \
  --block <block> --rpc-url <endpoint>
cast call <simple-vault> 'totalBalances(address)(uint256)' <asset> \
  --block <block> --rpc-url <endpoint>
cast call <mission-control> \
  'getDebtTerms(address)((uint256,uint256,uint256,uint256,uint256,uint256))' \
  <asset> --block <block> --rpc-url <endpoint>
cast call <mission-control> \
  'getTellerDepositConfig(uint256,address,address)((bool,bool,bool,bool,uint256,uint256,uint256,uint256,bool,uint256))' \
  3 <asset> 0x0000000000000000000000000000000000000001 \
  --block <block> --rpc-url <endpoint>
cast call <mission-control> \
  'getAssetLiqConfig(address)((bool,bool,bool,bool,bool,(bool,uint256,uint256,uint256,uint256),(uint256,address,address)))' \
  <asset> --block <block> --rpc-url <endpoint>
cast call <mission-control> \
  'getDepositPointsConfig(address)((uint256,uint256,bool))' \
  <asset> --block <block> --rpc-url <endpoint>

cast call <ledger> 'getNumBorrowers()(uint256)' \
  --block <block> --rpc-url <endpoint>
cast call <ledger> 'totalDebt()(uint256)' \
  --block <block> --rpc-url <endpoint>
cast call <ledger> 'numFungLiqUsers()(uint256)' \
  --block <block> --rpc-url <endpoint>
cast call <ledger> 'badDebt()(uint256)' \
  --block <block> --rpc-url <endpoint>
cast call <ledger> 'unrealizedYield()(uint256)' \
  --block <block> --rpc-url <endpoint>
cast call <mission-control> \
  'getRewardsConfig()((bool,uint256,uint256,uint256,uint256,uint256,uint256,uint256))' \
  --block <block> --rpc-url <endpoint>
```

For AAPL, RH-M0-01 used `eth_getStorageAt` at the EIP-1967 beacon slot
`0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50`,
`eth_getCode`, and `eth_call` for:

```text
name()
symbol()
decimals()
totalSupply()
uiMultiplier()
newUIMultiplier()
effectiveAt()
tokenPaused()
oraclePaused()
implementation()
paused()
isBlocked(address)
balanceOf(address)
```

### 3.2 Sanitized raw-evidence amendment

The machine-readable companion is
[`stock-token-m0-raw-evidence.json`](stock-token-m0-raw-evidence.json), SHA-256
`9ea333b4e84330f56c3a3d70e68823cfdba9c37948508e692450e01b3e994cba`.
It contains:

- the exact JSON-RPC requests, parsed raw responses, decoded values, targets,
  selectors, block numbers and hashes, block and retrieval timestamps, and
  classifications for a credential-free replay at the immutable RH-M0-01,
  BASE-M0-01, and BASE-M0-02 pins;
- `20` successful RH-M0-01 requests through
  `https://rpc.mainnet.chain.robinhood.com`;
- `228` successful BASE-M0-01 requests and `14` successful BASE-M0-02 requests
  through the credential-free archive replay endpoint
  `https://base-mainnet.public.blastapi.io`;
- the exact current PublicNode archive-replay rejection, the three retained
  fresh-fork failure classifications, and explicit `null` raw fields wherever
  a byte-exact request or response was not retained; and
- no credential, private information, signature, broadcast, state-changing RPC
  method, or transaction.

The original M0 session retained decoded results, exact endpoints, and exact
pins, but did not persist its raw JSON-RPC envelopes. This amendment does not
reconstruct or relabel them. BASE-M0-01 and BASE-M0-02 retain
`https://base-rpc.publicnode.com` as their original source; because that
endpoint now requires a personal token for these historical reads, the
companion replays the same immutable blocks through the separately named Blast
public endpoint. No credential was supplied.

RH-T2-01 remains **prior integrated evidence**, not a fresh M0 raw capture.
Its committed input and decoded execution record remain authoritative for the
historical fork. The companion deliberately leaves its raw requests and
responses `null`; none were fabricated. The fresh-fork limitation stated above
and in Section 5.3 remains unchanged.

## 4. Candidate Teller route and asset inventory

### 4.1 Complete current-source route inventory

| Route | Current caller/source | Asset domain that can reach Teller | Candidate-vault relevance |
| --- | --- | --- | --- |
| Ordinary `deposit` | `Teller.vy:229–240` | Any asset allowed by MissionControl and the selected vault | Direct |
| Ordinary `depositMany` | `Teller.vy:243–251` | Any configured asset in each action | Direct |
| `rebalance` deposit leg | `Teller.vy:401–426` | Any asset/vault pair allowed after the withdrawal leg | Direct |
| `depositFromTrusted` | `Teller.vy:254–265` | Any valid Ripe Department-supplied asset and vault ID that passes common configuration | Direct when the producer selects the launch vault |
| RipeGov deposit | `Teller.vy:762–772` | Any asset configured for RipeGov, not only RIPE | Separate vault, but the same forward Teller transfer boundary |
| GREEN conversion | `Teller.vy:628–642` | GREEN enters Teller; sGREEN enters the Stability Pool through `_deposit` | Separate vault; included if SavingsGreen is deployed |
| Stability auto-deposit | `StabVault.vy:979–995` | The arbitrary claim asset, sent to its first configured vault | Direct if a Stock/non-Stock asset is routed to the launch vault |
| Deleverage | `Deleverage.vy:442–456` | Governance/caller-supplied deposit asset and vault ID | Direct |
| Stability RIPE reward | `StabVault.vy:741–756` | RIPE into RipeGov | Same Teller boundary |
| Human Resources | `HumanResources.vy:416–426` | RIPE into RipeGov | Same Teller boundary |
| Lootbox auto-stake | `Lootbox.vy:1142–1160` | RIPE into RipeGov | Same Teller boundary |
| BondRoom | `BondRoom.vy:208–223` | RIPE into RipeGov | Same Teller boundary |
| CreditEngine surplus | `CreditEngine.vy:1192–1207` | sGREEN into Stability Pool | Same Teller boundary |
| CreditRedeem surplus | `CreditRedeem.vy:278–293` | sGREEN into Stability Pool | Same Teller boundary |

This inventory is configuration-complete but not asset-complete. Trusted caller
status narrows permissions, not the possible token type: Deleverage and
Stability auto-deposit retain arbitrary configured asset inputs.

### 4.2 Robinhood exact-transfer compatibility matrix

`Pass` below means exact base-unit transfer behavior is positively evidenced;
it does not mean approved for listing. `Unknown` is a hard stop for an enabled
Robinhood runtime row.

This is an M0 token-compatibility classification. The forward Teller and launch
vault do not exist yet, so it does not claim that an unimplemented M1 route has
run. M1 must compose each approved token with every ordinary and trusted route
and prove the same exact delta.

| Asset or asset class | Address/runtime | Ordinary routes | Trusted routes | Exact-transfer result | M0 disposition |
| --- | --- | --- | --- | --- | --- |
| AAPL Stock Token | Proxy `0xaF3D76f1834A1d425780943C99Ea8A608f8a93f9`; exact identities in Section 5 | Eligible only after future config | Deleverage/Stability auto-deposit could reach it after future config | **Pass at RH-T2-01**, conditional on unpaused/unblocked unchanged runtime; RH-M0-01 identity matches | Compatible candidate; not a vault/listing approval |
| Every other launch Stock Token | **No final addresses or count in the repository** | Potentially all generic routes | Potentially Deleverage/Stability auto-deposit | **Unknown** | **Hard stop** until every token proxy/control/runtime and exact route is pinned |
| RIPE | No Robinhood deployment address/runtime | RipeGov public route if included | StabVault, HR, Lootbox, BondRoom | **Unknown Robinhood runtime** | **Hard stop** if the route is enabled; otherwise manifest must prove omission/inactivity |
| sGREEN | Inclusion is owner-pending; no Robinhood deployment address/runtime | GREEN-conversion route deposits sGREEN | CreditEngine/CreditRedeem | **Unknown Robinhood runtime and inclusion** | **Hard stop** if included; otherwise prove every dependent path omitted/inactive |
| GREEN | No Robinhood deployment address/runtime | Enters Teller before optional ERC-4626 conversion; it is not the final `_deposit` asset in that route | None of the enumerated trusted `_deposit` calls use raw GREEN | **Unknown runtime; wrapper-input only** | Freeze inclusion and exact conversion behavior before enabling the route |
| USDG | Canonical asset direction exists, but final PSM/collateral inclusion and address manifest are absent | Could reach generic Teller only if configured as collateral/RipeGov asset | Could reach arbitrary trusted routes if configured | **Unknown route inclusion/runtime** | **Hard stop if enabled through Teller**; disabled/omitted PSM alone does not prove Teller omission |
| Any other Robinhood collateral, governance, reward, claim, or receipt token | No final asset/default/manifest inventory | Generic ordinary routes | Arbitrary configured trusted routes | **Unknown** | **Hard stop** |

The repository evidence for the unknown set is explicit:

- `docs/chains/rh-summary.md` requires “each launch Stock Token” but names only
  “one candidate Stock Token” in the testnet checklist;
- the SavingsGreen decision remains open;
- initial GREEN/RIPE bridging remains open;
- PSM activation remains open even though the USDG price path is selected; and
- Robinhood migration trees, manifests, and final address/parameter inventory
  do not yet exist.

Therefore AAPL evidence cannot be extrapolated by ticker, issuer, beacon, or
shared implementation to an unnamed token. Every enabled proxy remains a
separate matrix row even if its bytecode later matches AAPL.

## 5. Exact AAPL identity, controls, and pinned-fork behavior

### 5.1 Fresh live identity

RH-M0-01 decoded:

| Field | Result |
| --- | --- |
| Chain ID | `4663` |
| Block | `18,538,327` / `0x11adf57` |
| Block hash | `0x1f3920aded6d22dd6afc0234d7b0088bdbdfcdc98bd40cddb8e6dbd8e8889eba` |
| Timestamp | `2026-07-24T23:18:57Z` |
| Proxy | `0xaF3D76f1834A1d425780943C99Ea8A608f8a93f9` |
| Proxy runtime hash | `0x6c1fdd40002dcb440c7fff6a84171404d279ccb057803b65826f7546acd65630` |
| Name / symbol / decimals | `Apple • Robinhood Token` / `AAPL` / `18` |
| Robinhood asset ID / integrated registry status | `0x00000000000000000000000000000000c2425be3658540dd8e2424cbf3c5c649` / `ASSET_STATUS_ACTIVE` in the integrated Track 2 indexer record |
| Total supply | `3381949000000000000000` |
| EIP-1967 beacon / access registry | `0xe10b6f6B275de231345c20D14Ab812db62151b00` |
| Beacon runtime hash | `0x8b465c0b53a2ba499566e9b4ca67d8c90ed6131743df806a570d156956a7e90e` |
| Implementation | `0xb35490d6f9163DE4F80d88dc75c3516eb64C5aE2` |
| Implementation runtime hash | `0xdc07e86ee482f99641bdafb9a0d772846b167401e094d90a666b94dbdcd1eec7` |
| Global / token / oracle pause | `false / false / false` |
| Current / new UI multiplier | `1000000000000000000 / 1000000000000000000` |
| Multiplier effective time | `0` |
| Fork sender blocked | `false` |
| Predicted probe blocked | `false` |
| Fork sender live balance | `716665481191064488488` |

The proxy, beacon, implementation, and all three hashes are unchanged from the
RH-T2-01 approved input. Supply and the public holder balance changed, as
expected for dynamic state; neither value is used as code identity.

### 5.2 Transfer-relevant controls

The integrated verified source/ABI and current reads establish:

- global registry pause;
- per-token pause and oracle pause;
- sender and recipient blocklist checks;
- an additional operator blocklist check on `transferFrom`;
- beacon implementation upgrades controlled through registry roles;
- privileged mint, burn, administrative burn, blocklist, pause, oracle, and
  multiplier-management surfaces; and
- no current transfer fee or receiver hook in the inspected implementation.

These controls do not make the token incompatible with exact-transfer
accounting. They make compatibility conditional and justify fail-closed vault
behavior: a blocked, paused, confiscated, or newly incompatible implementation
must revert or produce unsafe backing, never nominal credit.

### 5.3 Pinned fork

RH-T2-01 is fixed by the committed input:

| Field | Pinned value |
| --- | --- |
| Block / hash | `17,558,441` / `0x35e8e2a3803cb42c4553cb5f3528b187508c6cc200a8b761943374003b8f0243` |
| Timestamp | `2026-07-23T18:52:41Z` |
| Sender/owner/recipient | `0x9f736F87E6293AC1Bd9142E257dbfAC8b7AcF1ae` |
| Amount | `1000000000000000` base units (`0.001 AAPL`) |
| Probe | `0xdC40b17919c0a684Cf553C22B394fD44Dd7a712F` |
| Probe runtime hash | `0xaa9b728174d048a5d65f49f5b4c851413008d6b89f315d36256191bd1a402949` |
| Input scope | `fork-only`; `broadcast_allowed=false` |

The integrated execution observed:

| Step | Sender | Probe | Allowance |
| --- | ---: | ---: | ---: |
| Before | `390389871775472346454` | `0` | `0` |
| Exact approval | unchanged | `0` | `1000000000000000` |
| Deposit | `390388871775472346454` | `1000000000000000` | `0` |
| Withdrawal | `390389871775472346454` | `0` | `0` |
| Cleanup | `390389871775472346454` | `0` | `0` |

The deposit receipt and withdrawal delivery were exact in base units. The
round trip restored balances and left no allowance. No credential, signature,
live token, native token, or transaction was used.

The M0 rerun limitation in Section 3 remains explicit. Current identity parity
substantially reduces implementation-drift risk but is not a substitute for a
fresh historical fork if the independent reviewer requires one.

## 6. Base ID-3 forward-source and live-risk classification

### 6.1 Decode legend

At BASE-M0-01:

- `C` is live token `balanceOf(SimpleErc20)`;
- `N` is `SimpleErc20.totalBalances(asset)`;
- `dep/sup` is current `canDepositAsset / doesVaultSupportAsset` from
  `getTellerDepositConfig(3, asset, 0x1)`; general deposits were enabled;
- `LTV` is `DebtTerms.ltv` in basis points;
- `swap` means `shouldSwapInStabPools=true` and
  `shouldAuctionInstantly=true`;
- `Endaoment` means `shouldTransferToEndaoment=true`;
- all 27 per-asset `stakersPointsAlloc / voterPointsAlloc` reads were `0 / 0`;
  and
- `conditional exact` means the current inspected token class has no known
  transfer fee or balance rebase on ordinary transfer, but its per-route
  pinned-fork proof is not complete. It is not approval for a Base cutover.

### 6.2 All 27 rows

| # | Asset and address | `C / N` | `dep/sup`; LTV; liq | Runtime hash at BASE-M0-01 | Forward-source classification |
| ---: | --- | ---: | --- | --- | --- |
| 1 | USDC `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` | `0 / 0` | `false/false`; `8000`; none | `0xa6705a10bb756b5dea144591118be77d7af0c3eee3bf2dfe2583dcb0364fefab` | Conditional exact controlled proxy; currently inactive for ID 3; route proof pending |
| 2 | cbBTC `0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf` | `1356929 / 1356929` | `true/true`; `7000`; swap | `0x91149353e08445ba77a52bf7e4cef919054027f4ad42812b4314bbaf2abd8b71` | Conditional exact controlled proxy; **funded**; route proof pending |
| 3 | WETH `0x4200000000000000000000000000000000000006` | `1149627914921567448 / 1149627914921567447` | `true/true`; `7000`; swap | `0x8a3a1f6a9f9dce633117adee5b458245835a8645a8c8726a26382a4622508b1c` | Fixed exact WETH units; **funded; one-unit surplus**; route proof pending |
| 4 | cbDOGE `0xcbD06E5A2B0C65597161de254AA074E489dEb510` | `14500000000 / 14500000000` | `true/true`; `5000`; swap | `0xf16c0bc993ad17b0763080df1733af8a7faf532253b96e9c8e82862203144721` | Conditional exact controlled proxy; **funded**; route proof pending |
| 5 | uSOL `0x9B8Df6E244526ab5F6e6400d331DB28C8fdDdb55` | `823425136048272240 / 823425136048272240` | `true/true`; `5000`; swap | `0x177179d65f16894b8a71e2206b9570ecb7224b67a6923519e966f8d1de649026` | Conditional exact beacon proxy; **funded**; route proof pending |
| 6 | Morpho Spark USDC `0x7BfA7C4f149E7415b73bdeDfe609237e29CBF34A` | `0 / 0` | `false/false`; `0`; none | `0x84ca9fa073d8b84cc3f911eb7116b4f311e8326ab1d8b5f5d6ef9d0f7913bdfa` | Exact share units under current runtime; underlying value can change; route proof pending |
| 7 | AERO `0x940181a94A35A4569E4529A3CDfB74e38FD98631` | `91859213070865428334 / 91859213070865428334` | `true/true`; `5000`; swap | `0x6e2d6a09208d3bbad8885809c4db6a91be93d78c0cabc06ded4dc6fa38a1b458` | Fixed exact units with minter; **funded**; route proof pending |
| 8 | Moonwell AERO `0x73902f619CEB9B31FD8EFecf435CbDf89E369Ba6` | `0 / 0` | `false/false`; `0`; none | `0xec9af364cc1bb9f6c2dac4f79c5250503d4ff7514ced4670a402b6f287721616` | Exact cToken units under current runtime; upgrade/seize/value risk; route proof pending |
| 9 | cbXRP `0xcb585250f852C6c6bf90434AB21A00f02833a4af` | `0 / 0` | `true/true`; `5000`; swap | `0xf16c0bc993ad17b0763080df1733af8a7faf532253b96e9c8e82862203144721` | Conditional exact controlled proxy; route proof pending |
| 10 | WELL `0xA88594D404727625A9437C3f886C7643872296AE` | `11986269878969919127060 / 11986269878969919127060` | `true/true`; `4000`; swap | `0x229ea3687ae24e2e77ea3fa5a97affd10d2500be2699bfad47d4aa6e40717091` | Conditional exact upgradeable token; **funded**; route proof pending |
| 11 | VIRTUAL `0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b` | `1054012762792834343376 / 1054012762792834343376` | `true/true`; `5000`; swap | `0x2a9e5cdaeba01009afa309c7e6236caad9fda314f1088da2c486d4a6df2ecec7` | Conditional exact bridge token; **funded**; route proof pending |
| 12 | VVV `0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf` | `0 / 0` | `false/false`; `4000`; none | `0x67f0ec6b769503efc2611b3566ffae158a1a9fd8ba3dc30ccf320436d8c5745d` | Fixed exact units with mint control; currently inactive; route proof pending |
| 13 | DEGEN `0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed` | `0 / 0` | `true/true`; `4000`; swap | `0x0fc7067f83de437662a064d75d34700c97224082189a9ef1ccd5ed5a7dd601f6` | Exact current units with pause/self-burn; route proof pending |
| 14 | Moonwell cbETH `0x3bf93770f2d4a794c3d9EBEfBAeBAE2a8f09A5E5` | `0 / 0` | `false/false`; `0`; none | `0x041dbd5067f87816c0c8d6af9992f04e71aa99c87d1a8e9fb1d27e3e7ed99985` | Exact cToken units under current runtime; upgrade/seize/value risk; route proof pending |
| 15 | cbETH `0x2Ae3F1Ec7F1F5012CFEab0185bfc7aa3cf0DEc22` | `800000000000000000 / 800000000000000000` | `true/true`; `7000`; swap | `0x8cd2f08c7ee9e6ab6e0180e8d6cb0613bbd54d2c4ae2ecdcaddfcdd9a226215b` | Conditional exact bridge proxy; **funded**; route proof pending |
| 16 | Moonwell USDC `0xEdc817A28E8B93B03976FBd4a3dDBc9f7D176c22` | `0 / 0` | `false/false`; `0`; none | `0xcd7e22e6eef009b831781d4de03f20777094f437a9719c597c45cf9725a7dca9` | Exact cToken units under current runtime; upgrade/seize/value risk; route proof pending |
| 17 | Morpho Moonwell USDC `0xc1256Ae5FF1cf2719D4937adb3bbCCab2E00A2Ca` | `0 / 0` | `false/false`; `0`; none | `0xca56bf34ea3b781d633c62274f5ad1bb2e987d82eb0c6fc038febde1f0e7cfb1` | Exact share units under current runtime; underlying value can change; route proof pending |
| 18 | Morpho Seamless USDC `0x616a4E1db48e22028f6bbf20444Cd3b8e3273738` | `0 / 0` | `false/false`; `0`; none | `0xf4f6a3e473c76700c0afce3dde29d313f368212a50e7ef968c3b8c7dcaefd667` | Exact share units under current runtime; underlying value can change; route proof pending |
| 19 | Fluid USDC `0xf42f5795D9ac7e9D757dB633D693cD548Cfd9169` | `0 / 0` | `false/false`; `0`; none | `0x7bb1bad9cc6f098488c71a052e917f646cb335cf64c64d244e6d14ee57b7c743` | Exact fToken units under current runtime; share value can change; route proof pending |
| 20 | Euler USDC `0x0A1a3b5f2041F33522C4efc754a7D096f880eE16` | `0 / 0` | `false/false`; `0`; none | `0x62b853b99162e9e09c5f3b09d9aa16144fd9491022773342a613a814febea2b1` | Exact share units under current runtime; beacon/value risk; route proof pending |
| 21 | Moonwell cbBTC `0xF877ACaFA28c19b96727966690b2f44d35aD5976` | `0 / 0` | `false/false`; `0`; none | `0x12217819851fedb91f4d45a29ce418f9546b8f426782f94cfa24f703382bc1de` | Exact cToken units under current runtime; upgrade/seize/value risk; route proof pending |
| 22 | Morpho Moonwell WETH `0xa0E430870c4604CcfC7B38Ca7845B1FF653D0ff1` | `0 / 0` | `false/false`; `0`; none | `0x07e97040484bcc9c5134e6291e9009845725d7d329c6a5bd682f1fa9fb02fdf8` | Exact share units under current runtime; underlying value can change; route proof pending |
| 23 | Morpho Seamless WETH `0x27D8c7273fd3fcC6956a0B370cE5Fd4A7fc65c18` | `0 / 0` | `false/false`; `0`; none | `0x8da64fe9566e4f9596f225f4d602da45c65de99806a1503c94505c3c19922bb2` | Exact share units under current runtime; underlying value can change; route proof pending |
| 24 | Euler WETH `0x859160DB5841E5cfB8D3f144C6b3381A85A4b410` | `0 / 0` | `false/false`; `0`; none | `0x91b8f22d54c61b6f1d54d24f2623e4e5a9d552acbd5a16c39d1c154758410fbb` | Exact share units under current runtime; beacon/value risk; route proof pending |
| 25 | Morpho Moonwell cbBTC `0x543257eF2161176D7C8cD90BA65C2d4CaEF5a796` | `0 / 0` | `false/false`; `0`; none | `0x51f0bce7a86c43504e1383fd06f4e61e6a2528886d24d15e954159c823d99842` | Exact share units under current runtime; underlying value can change; route proof pending |
| 26 | sUSDe `0x211Cc4DD073734dA055fbF44a2b4667d5E5fE5d2` | `830694343423510974 / 830694343423510974` | `true/true`; `8000`; Endaoment | `0x15fbd16726e8f991d745fa094f3c934164c353010f40abd453aa80d395108df1` | Conditional exact transfer; blacklist redistribution can independently create a deficit; **funded**; route proof pending |
| 27 | wrapped superOETH `0x7FcD174E80f264448ebeE8c88a7C4476AAF58Ea6` | `0 / 0` | `false/true`; `7000`; swap | `0x7bcae86aa09a8e427693277c4ef8a659538e3e5aa85fef8bd8f55da5e55954c1` | Exact wrapped-share units under current runtime; upgrade/value risk; deposit currently disabled; route proof pending |

The nine custody-positive rows are 2, 3, 4, 5, 7, 10, 11, 15, and 26.
Every one is nominally solvent. WETH is the only mismatch and is solvent by one
raw unit.

### 6.3 Debt, auctions, rewards, and urgent-live criteria

At BASE-M0-01:

| Field | Decoded result |
| --- | ---: |
| Actual borrowers (`getNumBorrowers`) | `61` |
| Stored total debt, raw 18-decimal GREEN units | `23129931081907483392420` |
| Unrealized yield, raw 18-decimal GREEN units | `16042224245768543113` |
| Raw `numFungLiqUsers` sentinel count | `1` |
| Actual active fungible liquidation users | `0` |
| Ledger bad debt | `0` |
| Reward points enabled | `true` |
| RIPE per block | `7500000000000000` |
| Borrower / staker / voter / generic-depositor allocation | `1000 / 9000 / 0 / 0` |
| Total staker / voter points allocation | `10000 / 0` |

Ledger uses index zero as a sentinel. A raw `numFungLiqUsers == 1` means there
are zero enumerated active liquidation users. A stale storage row at index one
is not active: its user's `numFungibleAuctions` is zero and debt is zero.

Debt is stored per user, not attributed to one collateral asset. Because no
ID-3 row has `C < N`, the directly evidenced debt exposed to an observed
nominal deficit is zero. The aggregate debt remains relevant exposure if a
funded asset later loses custody.

Urgent criteria:

| Criterion | Result |
| --- | --- |
| Borrow-enabled `C < N` | **Not observed** |
| Debt or active auction exposed to an observed deficit | **Not observed** |
| Live short-receipt reproduction | **Not performed and not observed** |
| Credible current immediately exploitable custody mismatch | **Not observed**; WETH is `C=N+1`, not a deficit |
| Issuer/bridge/upgrade control alone | Present on several funded rows; latent under the controlling specification, not by itself urgent |

**Conclusion:** no refreshed urgent-live Base vulnerability is demonstrated.
This is not a safety warranty. Base ID 3 still uses the legacy nominal path,
and every per-token route fork remains required before a future forward-source
Base cutover. That later Base cutover is blocked by incomplete route evidence,
but the incompleteness does not itself block Robinhood while Base remains on
its current runtimes.

## 7. Robinhood/Base state-independence proof

### 7.1 Current Base deployment identity

BASE-M0-02 resolved these addresses from the committed Base manifest and
hashed live runtime code:

| Contract | Base address | Runtime hash |
| --- | --- | --- |
| GreenToken | `0xd1Eac76497D06Cf15475A5e3984D5bC03de7C707` | `0x7ccdbcccfb53bb7888a3f2c178720208c82b631eb7d816d58ca1f5ab8a786eca` |
| RipeToken | `0x2A0a59d6B975828e781EcaC125dBA40d7ee5dDC0` | `0x0da1178ba4b030fb92d5aaae3128d29bb02a5959c6fd1a1774ad91c232ff717c` |
| SavingsGreen | `0xaa0f13488CE069A7B5a099457c753A7CFBE04d36` | `0x13568815b8854708f7002369c12704f3a83b2cf829b2669f6c1b1928e9fa97c6` |
| RipeHq | `0x6162df1b329E157479F8f1407E888260E0EC3d2b` | `0xe33d1686ee691b8a37872d35e2bafbb2cc0102d66a123072c4377fa5ecd190fa` |
| Ledger | `0x365256e322a47Aa2015F6724783F326e9B24fA47` | `0xdcb94574dd9e625451c96086c7a03c2516457e7ced0b9d3545bab4a005921b7d` |
| MissionControl | `0x559E53F42b68b4995732Dba4aF300796761DBC19` | `0x0428c8dd05faed65d02bf4742635ed19170de66ecc7954580fcedbe6a95590f5` |
| VaultBook | `0xB758e30C14825519b895Fd9928d5d8748A71a944` | `0x01aa4ad4bebce4f28a50b7a1da386afde39d7de5558351e393fd9a71e3d71758` |
| SimpleErc20 | `0xf75b566eF80Fde0dEfcC045A4d57b540eb43ddfD` | `0x1d0ec56e109e264dad4435b772deec0026167d96acdb036c51e8b88909b34eb7` |
| AuctionHouse | `0x8a02aC4754b72aFBDa4f403ec5DA7C2950164084` | `0xc385d07ca6040ae6738c5cef2bea14bc0e4a4cc8893c0adc40a60f62c49ac9d4` |
| CreditEngine | `0xEdd0563D06CC52fb5F264A2366A31d9776f6dcC7` | `0x651f0cf6c3ece5427d54a0c3ee83136cab2a9c502835d08e32d4ad496889612f` |
| Lootbox | `0x1f90ef42Da9B41502d2311300E13FAcf70c64be7` | `0xb3a2f6516aab23a9842e504b8cc8140167369b84d4f1f4fe787d76078019c6eb` |
| Teller | `0xae87deB25Bc5030991Aa5E27Cbab38f37a112C13` | `0x016ec2406e181fb30cb94f7d8e49d12bf138ffedacc10356c2618947217e8c44` |

There is no `migration_history/robinhood-*` tree, Robinhood migration tree, or
Robinhood Ripe manifest at the controlling commit. Accordingly there are no
Robinhood Ripe contract addresses or hashes to place opposite the Base rows.
That is an explicit deployment-evidence gap, not evidence of shared state.

### 7.2 File-exact mechanism

`contracts/modules/Addys.vy` stores one immutable local `RipeHq` address and
resolves Ledger, MissionControl, VaultBook, AuctionHouse, CreditEngine, Lootbox,
Teller, GREEN, RIPE, and sGREEN from that local registry. It has no chain ID,
remote registry, bridge, or message fallback. A repository search over
`contracts/`, `interfaces/`, and `migrations/` found no production CCIP pool,
bridge, cross-chain message sender/receiver, remote Ledger, or remote vault
implementation.

Thus a clean Robinhood deployment with a distinct RipeHq and distinct
registered addresses has separate custody, nominal balances, debt, auctions,
configuration, rewards, and permissions by construction. Shared source,
governance personnel, monitoring, or release tooling is not shared onchain
state.

### 7.3 Propagation-path matrix

| Possible path | Current repository/deployment evidence | Can Base failure alter Robinhood protocol state? | M0 disposition |
| --- | --- | --- | --- |
| Shared vault custody | Base vault address is chain-local; no RH Ripe vault exists | No current path | Require distinct RH manifest address and reject every Base address |
| Shared Ledger/credit/debt | Base Ledger is manifest-pinned; Addys resolves local HQ | No current path | Require distinct RH HQ/Ledger and state-root checks |
| Shared AuctionHouse/settlement | Base AuctionHouse is manifest-pinned; no remote call source exists | No current path | Require distinct RH AuctionHouse and GREEN path |
| Shared MissionControl/config | Local HQ resolution only | No current path | Require distinct RH MissionControl/default manifest |
| Stock-token authority | AAPL beacon/registry exists on Robinhood; no repository or deployment evidence inspected in M0 identifies a Base Ripe address as privileged in that graph | No Base-to-RH protocol-state path observed from the available evidence | Enumerate exact launch-token roles at freeze; an unknown role is a stop |
| Shared offchain operator/governance person | Possible operationally, but not an automatic state edge | No by itself | Role errors remain operational risk, not state propagation |
| GREEN/RIPE CCIP burn/mint pools | Proposed in docs; no production source/deployment yet; initial-launch requirement open | **Yes if activated:** Base-originated excess/unsafe GREEN can be burned/minted into RH supply and affect liquidity, repayment, PSM, or accounting; token/pool authority is a direct edge | **Hard stop until omitted/inactive or separately security-approved with a revised independence claim** |
| USDG/PSM or other external bridge | Inclusion and final graph are not frozen | Unknown | Hard stop if any remote custody/message/token-authority edge is included |

### 7.4 Independence conclusion

The file-level architecture supports independence, but a
**deployment-exact proof cannot pass without the final Robinhood manifest and
feature graph**. It passes provisionally only under both conditions:

1. every Robinhood Ripe contract, registry, custody address, debt store,
   auction store, configuration store, and token authority is a distinct
   chain-local instance; and
2. GREEN/RIPE CCIP and every other cross-chain state/economic route is omitted
   or provably inactive during Stock activation.

If initial launch requires the proposed CCIP bridge, M0 must return to
owner/security review. It cannot describe Robinhood-first as independent while
the bridge intentionally joins token supply and economic state.

## 8. Day-one depositor and borrower reward posture

### 8.1 Exact reward buckets

The current source has four global RIPE reward buckets:

| Bucket | Point source | Can a Stock position participate? |
| --- | --- | --- |
| `borrowers` | Account-level debt principal in `Lootbox._getLatestBorrowPoints`; no collateral-asset attribution | **Yes.** A borrower using Stock collateral cannot be excluded per asset. |
| `stakers` | Per-asset `stakersPointsAlloc` and user vault balance/share | Only if the Stock asset receives nonzero staker allocation |
| `voters` | Per-asset `voterPointsAlloc` and vote-related points | Only if the Stock asset receives nonzero voter allocation |
| `genDepositors` | USD value for assets whose `stakersPointsAlloc == 0` | **Yes.** Setting Stock staker allocation to zero routes its deposit value into this generic point class; it does not exclude it. |

`arePointsEnabled=false` stops new point accrual. `_getLatestGlobalRipeRewards`
separately allocates available RIPE according to `ripePerBlock` and the four
global allocation fields. A robust “globally inactive” launch posture therefore
must freeze both point accrual and reward distribution/mint availability; it
should not rely on one boolean while leaving a positive distribution schedule
ambiguous.

Base's current values in Section 6 are evidence of current Base only:
points enabled, `0.0075 RIPE` per block, `10%` borrowers, `90%` stakers, and
zero voter/generic-depositor distribution. They are not approved Robinhood
defaults. In particular, blindly copying them would make every Robinhood
borrower eligible for the global borrower bucket.

### 8.2 Required owner decision

The owner must select one posture before M0 can pass:

1. **Global launch disable — recommended minimum-risk posture.**
   `arePointsEnabled=false`, `ripePerBlock=0`, and no funded/mintable launch
   reward distribution. Stock and non-Stock positions accrue no launch points
   or RIPE until a later approved enablement.
2. **Non-Stock rewards only.** Points may be enabled, but
   `borrowersAlloc=0`, `genDepositorsAlloc=0`, and every launch Stock Token has
   `stakersPointsAlloc=0` and `voterPointsAlloc=0`. Any retained staker/voter
   bucket must prove that only named non-Stock assets have nonzero per-asset
   allocation. This sacrifices borrower rewards globally because the current
   schema cannot distinguish debt by collateral.
3. **Stock-linked launch rewards required.** This is a **hard stop**. Reopen
   reward-loss attribution and incident behavior before M1; do not silently
   accept pre-loss points or payouts after custody loss.

No option is selected by this evidence file.

## 9. Incompatibilities, unknowns, and accepted residual risk

### 9.1 Incompatibilities found

- No current incompatibility was found in the exact AAPL proxy at RH-M0-01 or
  RH-T2-01.
- No Base row was shown to take a transfer fee or rebase balance units on
  ordinary transfer under the current inspected source class.
- Per-route fork execution is incomplete for all 27 Base rows, so none is
  approved for a forward-source Base cutover by this file.

### 9.2 Hard stops

The following stop before M1:

- any enabled Robinhood Stock or non-Stock asset not explicitly named by
  address, runtime identity, route, and exact-transfer result;
- any fee, short-receipt, rebasing-on-transfer, malformed-read, or unknown
  Robinhood runtime;
- an active GREEN/RIPE or other cross-chain propagation path during Stock
  activation without a revised owner/security decision;
- a day-one requirement to pay Stock-linked depositor or borrower rewards;
- a refreshed Base `C<N` row with borrow capacity, exposed debt/auction, live
  short receipt, or another immediately exploitable mismatch;
- inability to obtain the exact Robinhood deployment graph and prove every
  state-owning address distinct; or
- independent-review rejection of the carried-forward AAPL fork without an
  archive-capable rerun.

### 9.3 Residual risks if the stops are closed

- AAPL and other Stock Tokens retain issuer pause, blocklist, burn, multiplier,
  and upgrade risk.
- Exact-transfer compatibility at one pin is not future compatibility after a
  beacon implementation change.
- An issuer loss can freeze the affected Stock asset, withdrawals, and
  liquidation while debt and interest remain.
- Base remains on legacy Teller, SimpleErc20, CreditEngine, and internal
  settlement behavior. Its WETH surplus remains a donation-masking
  precondition even though no deficit exists now.
- Base aggregate debt is not attributable to one collateral asset in Ledger;
  an incident snapshot must enumerate each indebted user's vault positions.
- Public credential-free RPCs are not production-grade evidence backends. The
  AAPL historical fork refresh demonstrated rate/archive limitations.
- Omitting CCIP preserves state independence but creates chain-local GREEN/RIPE
  liquidity and supply. That product consequence must be accepted explicitly.
- Disabling borrower rewards to exclude Stock-backed debt also disables
  borrower rewards for non-Stock borrowers under the current global schema.

## 10. Complete post-M0 owner-decision package

M0 requires decisions, not implementation authorization.

The owner supplied the following **preliminary recommendations** with the raw
provenance amendment: keep CCIP inactive during initial Stock activation;
disable rewards globally at launch; accept RH-T2-01 plus the current AAPL
identity match; leave Base unchanged; and require separate evidence and
approval before any future Base cutover. These recommendations align with
D-M0-02 through D-M0-06 but do not close them in this evidence amendment. The
complete Robinhood launch-token and route table in D-M0-01 remains the
load-bearing owner input and the principal M0 stop.

### D-M0-01 — Freeze the complete Robinhood Teller asset graph

Provide one exhaustive table containing:

- every launch Stock Token proxy address;
- every non-Stock token address, including RIPE, GREEN, sGREEN, USDG, reward,
  governance, claim, and receipt tokens;
- ordinary/trusted route availability;
- target vault class, without selecting the production launch vault or ID in
  this M0 record;
- enabled, disabled, omitted, or inactive-staging disposition; and
- code/proxy/beacon/implementation identity for every enabled token.

Until this table exists, M0 remains stopped.

### D-M0-02 — Initial cross-chain posture

Choose:

- **omit or keep all GREEN/RIPE CCIP and other cross-chain routes inactive
  through Stock activation** — recommended for the minimum independent launch;
  or
- require a cross-chain route, which returns the propagation path to
  owner/security review and prevents the current independence proof from
  passing.

### D-M0-03 — Day-one rewards

Choose reward option 1, 2, or 3 from Section 8.2. Option 3 is a stop and reopens
reward-loss scope.

### D-M0-04 — AAPL fork-refresh sufficiency

Choose:

- accept the integrated immutable RH-T2-01 exact fork plus RH-M0-01's current
  identity match for M0; or
- require a fresh rerun through an approved archive-capable provider. Any
  credential must remain outside the repository and logs.

This decision does not approve a live AAPL transfer.

### D-M0-05 — Base sequencing and residual risk

Confirm or reject:

- BASE-M0-01 does not demonstrate an urgent live Base vulnerability;
- Robinhood-first may continue after the other M0 stops close;
- current Base runtimes remain unchanged; and
- the three legacy Base mechanisms and future per-asset fork gap are accepted
  until a separate Base hardening/migration decision.

Rejecting this statement returns Base sequencing to owner/security review; it
does not authorize a migration.

### D-M0-06 — Future Base cutover

Confirm that this file does **not** approve a Base cutover. All 27 rows require
route-exact fork/equivalent evidence, implementation/control refresh, borrower
position enumeration, auction enumeration, and separate migration approval
before any forward-source Base deployment.

### D-M0-07 — Next authorization boundary

After D-M0-01 through D-M0-06 are resolved and this file is independently
reviewed, the owner may authorize either:

- a documentation-only M0 closure revision; or
- a later file-exact M1 implementation slice.

Nothing in this file authorizes M1. No production vault or VaultBook ID is
selected, and the three-contract mechanism remains unapproved.

## 11. M0 checklist

- [x] Fresh worktree and branch created from exact integrated commit.
- [x] Only this M0 file and its sanitized raw-evidence companion are authorized
  repository deltas.
- [x] Controlling Track 8 specification and validation plan unchanged.
- [x] Exact original Base RPC URL, raw replay provenance, companion SHA-256,
  and unavailable-response classifications recorded without credentials.
- [x] Current-source ordinary and trusted Teller caller inventory complete.
- [ ] Exact Robinhood asset matrix complete — **blocked on D-M0-01**.
- [x] Exact AAPL proxy/beacon/implementation and live hashes refreshed.
- [x] Integrated exact AAPL fork behavior preserved with immutable provenance.
- [ ] Fresh AAPL fork rerun — **provider-limited; D-M0-04 returned**.
- [x] All 27 Base ID-3 assets refreshed for `C/N`, deposit support, LTV,
  liquidation route, points allocation, and exact-block runtime hash.
- [x] Nine funded Base rows and WETH one-unit surplus confirmed.
- [x] Base aggregate debt, borrower count, auction sentinel, bad debt, yield,
  and rewards recorded.
- [x] No urgent-live Base criterion observed.
- [ ] Robinhood/Base deployment-exact independence complete — **blocked on
  final Robinhood graph and D-M0-02**.
- [x] Every Stock-capable reward bucket identified.
- [ ] Day-one reward policy frozen — **blocked on D-M0-03**.
- [x] No state-changing transaction, signing, deployment, configuration,
  migration, or live transfer performed.
- [x] No secret or credential recorded.
- [x] M1 not begun.
