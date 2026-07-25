# Track 8 M0: Stock Token launch evidence and product-freeze record

**Status:** Track 8 M0 was independently reviewed and owner-closed on 25 July
2026 at reviewed commit
`c5c8b699b229792dc61e66af35502684ea3c8155`. **M1 remains unauthorized.**

**Evidence acquisition date:** 24 July 2026

**Owner-decision completion date:** 25 July 2026

**Controlling integration commit:**
`2517eeb0013cdb277dc4815db4b524d7a090d682`

**Evidence branch:** `rh-track-8-m0-evidence`

**Owner-decision revision baseline:** current reviewed `rh`
`fc48ac45e5f6e8c698a6464a14289aad00e1f2d4`; prepared in
`rh-track-8-m0-owner-decisions`

**Scope:** Documentation and read-only evidence only. This record does not
approve M1, a production contract, a vault or VaultBook ID, an interface,
storage, ABI, default, migration, manifest, deployment, configuration, signed
message, or transaction.

The decision worktree was fast-forwarded on 25 July 2026 from
`185bd32004121bbb1c60748844c517ea8da0affb` to exact current `rh`
`fc48ac45e5f6e8c698a6464a14289aad00e1f2d4`, without rebase or history
rewrite. That increment adds only
`docs/chains/rh/track-6-s6-track-7-h4-defaults-parameters.md` and changes no
M0 evidence or Track 8 specification file. The original raw evidence remains
bound to its recorded acquisition pins.

On 25 July 2026, independent review confirmed that no M0 hard stop was
converted into an unsupported documentation assumption, and the owner
explicitly closed M0 at reviewed commit
`c5c8b699b229792dc61e66af35502684ea3c8155`. That closure does not authorize
M1 or any production/test change, vault or VaultBook ID selection, deployment,
configuration, signing, or transaction.

## 1. Executive conclusion

On 24 July 2026, the owner froze the product directions without closing the
evidence gates:

1. AAPL is the only initial Stock Token; every later Stock Token requires its
   own complete evidence.
2. GREEN/RIPE CCIP are nonblocking targets for separately reviewed promotion
   within seven days after launch. Seven days is not automatic authorization;
   incomplete or late evidence leaves CCIP disabled. sGREEN is chain-native
   and never CCIP-enabled.
3. Rewards launch globally disabled and target validated activation within
   seven days; AAPL depositors/borrowers may then participate under the
   accepted brief global-accounting incident window and kill-switch runbook.
4. The existing AAPL fork plus current matching identities is sufficient;
   implementation-identity change requires revalidation.
5. Base remains unchanged and separately gated.
6. sGREEN, PSM, Stability Pool, RipeGov, and the two named LP routes are
   launch targets under the exact restrictions in the owner packet.
7. AAPL uses fixed USD exposure targets, one enabled vault, and no
   trusted/Department deposit route.
8. The settlement candidate permits only vault-local guarded internal
   movement; external remains the frontend default. On 25 July 2026 the owner
   approved the exact partial-fill invariant in Section 12 and accepted its
   stated transfer-control residual risk.

This revision closes the remaining documentable pre-implementation inputs:
existing external-token identities and compatibility; the approved launch
graph and route dispositions; the file-exact proposed Robinhood/Base
state-independence graph; the AAPL/USD feed, price-pin procedure, cap
inputs/formula/rounding/review rules; CCIP complete-or-disabled policy and
promotion checklist; launch-disabled reward posture and incident runbook; the
exact proposed Teller/`GuardedErc20`/CreditEngine file boundary; source-traced
mechanism plausibility; the partial-fill decision; and the file-exact M1
authorization proposal in the owner packet. Implemented GuardedErc20
evidence, composed implementation tests, new Ripe deployment addresses/runtime
hashes, post-deployment route/configuration proof, exact freeze-time cap
integers, and final M1–M5 evidence are later gates, not M0 blockers.

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
it does not mean approved for listing. `Unknown` is an M0 hard stop for an
already-existing external token proposed for enablement. A new Ripe artifact
that does not yet exist receives a route/file disposition in M0 and runtime
evidence only after implementation.

This is an M0 token-compatibility classification. The forward Teller and launch
vault do not exist yet, so it does not claim that an unimplemented M1 route has
run. M1 must compose each approved token with every ordinary and trusted route
and prove the same exact delta.

| Asset or asset class | Address/runtime | Ordinary routes | Trusted routes | Exact-transfer result | M0 disposition |
| --- | --- | --- | --- | --- | --- |
| AAPL Stock Token | Proxy `0xaF3D76f1834A1d425780943C99Ea8A608f8a93f9`; exact identities in Section 5 | Future ordinary deposit only, through exactly one enabled vault | **Prohibited:** every Department/trusted route, including Deleverage and Stability auto-deposit, must remain disabled/unreachable | **Pass at RH-T2-01**, conditional on unpaused/unblocked unchanged runtime; RH-M0-01 identity matches | Compatible candidate; not a vault/listing approval |
| Every other Stock Token | No initial-launch row required | None at initial launch | None at initial launch | Not applicable while omitted | Owner-omitted; each later token requires a complete independent row |
| RIPE | New Ripe artifact; no Robinhood deployment exists | RipeGov public route required at launch | Only the named RIPE producers StabVault, HumanResources, Lootbox, and BondRoom may use their existing RipeGov route; no arbitrary asset substitution | **Not runtime-classifiable in M0** | M0 freezes this exact file/route disposition; source/compiler/runtime and composed route proof are post-M0 |
| sGREEN | New Ripe artifact; no Robinhood deployment exists | GREEN-conversion deposit/withdraw required | Only the named CreditEngine/CreditRedeem surplus-to-Stability routes; Stock extraction through CreditRedeem remains disabled | **Not runtime-classifiable in M0** | M0 freezes the chain-native file/route disposition; source/compiler/runtime and composed route proof are post-M0; CCIP must never exist |
| GREEN | New Ripe artifact; no Robinhood deployment exists | Enters Teller only as the input to the sGREEN conversion; core debt/settlement token | No raw-GREEN trusted `_deposit` route in the inventory | **Not runtime-classifiable in M0; wrapper-input only** | M0 freezes core/sGREEN/CCIP file and route dispositions; runtime/composition proof is post-M0 |
| USDG | Canonical Robinhood mainnet proxy `0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168`; implementation `0x68184C449E1a8f34fA18d289737129FD27B66f8F`; proxy/implementation hashes `0x864cc9ad53b338b82da1f7cab85ab0b3d5c8861acb422b6fec63cf36234f36a6` / `0x3a551ac5c744af57e68a1d1431ac403c0f516ffd7d224a75746aee11fc4f3baf` at block `17,572,269` | **Must not be ordinary Teller collateral; PSM and future GREEN/USDG LP only** | Every arbitrary trusted route omitted | **Pass for exact ordinary ERC-20 transfer under the pinned six-decimal, fee-free, non-rebasing runtime** | Existing identity/compatibility frozen from `usdg-public-evidence.md`; future PSM/LP composition and runtimes are post-M0 |
| GREEN/USDG LP | New launch artifact; canonical USDG above is the existing external constituent; GREEN is a new Ripe artifact | Future ordinary deposit token only, `ltv=0` | Every trusted route omitted | **Not runtime-classifiable in M0 because the pool/token does not yet exist** | M0 freezes constituents, ordinary-only route, and zero-LTV policy; exact DEX/factory/pool implementation/oracle creation inputs, LP address/runtime, and composed proof are post-M0 launch gates, not fabricated M0 identities |
| RIPE/WETH LP | New launch artifact; Robinhood WETH `0x0Bd7D308f8E1639FAb988df18A8011f41EAcAD73` is the existing external constituent documented by the [chain operator](https://docs.robinhood.com/chain/contracts/); RIPE is a new Ripe artifact | Future ordinary deposit token only, `ltv=0` | Every trusted route omitted | **Not runtime-classifiable in M0 because the pool/token does not yet exist** | M0 freezes constituents, ordinary-only route, and zero-LTV policy; exact DEX/factory/pool implementation/oracle creation inputs, LP address/runtime, and composed proof are post-M0 launch gates |
| Any other Robinhood collateral, governance, reward, claim, or receipt token | Not approved in the M0 launch graph | No route permitted | No route permitted | Not applicable while omitted | M0 freezes omission; later inclusion requires a complete independent row |

The repository evidence for the unknown set is explicit:

- `docs/chains/rh-summary.md` requires “each launch Stock Token” but names only
  “one candidate Stock Token” in the testnet checklist;
- SavingsGreen is owner-required, but M0 can freeze its proposed file and route
  disposition without fabricating a future deployment identity.
- GREEN/RIPE CCIP targets a separately reviewed promotion within seven days
  after launch and remains disabled if incomplete or late.
- PSM activation is owner-required; M0 freezes the existing canonical
  USDG/feed identities plus proposed authority/route ordering.
- Robinhood migration trees, manifests, new Ripe contract addresses, and final
  deployed runtime inventory do not yet exist and are post-M0 evidence.

The LP pool/factory/implementation/oracle cannot be pinned as an already
existing external dependency because no approved pool selection or deployed
LP exists in the reviewed repository. That absence is a later launch-component
gate, not an M0 evidence hole: neither LP can reach Teller until it exists and
is separately configured. It remains a hard launch stop, and M0 does not
select a DEX or pool.

The Robinhood operator token-contract directory was retrieved on 25 July 2026
and lists the WETH and USDG addresses used above. This was a documentation
read, not an RPC/indexer/fork result; it does not supply a WETH runtime or
approve a future LP.

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

### 5.4 Approved AAPL/USD feed and cap-freeze procedure

The integrated `stock-token-transferability-evidence.md` pins the approved
Robinhood Chainlink AAPL/USD feed:

| Field | Frozen M0 input |
| --- | --- |
| Feed proxy | `0x6B22A786bAa607d76728168703a39Ea9C99f2cD0` |
| Aggregator at the integrated pin | `0xBb11A21267cFDb63d4935d99a499133DD1744ACb` |
| Decimals | `8` |
| Published heartbeat | `86,400` seconds |
| Integrated reference answer | `32079999999` |
| Integrated update time | `2026-07-23T15:07:00Z` |

The final activation freeze must re-read the proxy and
`latestRoundData()` at one recorded block number/hash/timestamp, record proxy
and then-current aggregator runtime hashes, and require: positive answer,
eight decimals, nonzero/not-future `updatedAt`,
`answeredInRound >= roundId`, and age no greater than the approved nonzero
effective stale ceiling. An identity or interface change triggers full
revalidation.

For target USD value `D`, AAPL decimals `18`, and positive eight-decimal answer
`P8`, the fixed AAPL atomic cap is:

```text
capAtomic = floor(D * 10^(18 + 8) / P8)
```

Apply it independently with `D=5,000` and `D=25,000`. Rounding down ensures a
stored cap never exceeds its USD target at the freeze price. The activation
record must include both inputs, formula evaluation, two-person arithmetic
review, and exact configuration readback. Re-review is required at least every
seven days and whenever the current approved-feed valuation of either fixed
cap exceeds `110%` of its target. The freeze-time price and resulting integers
are post-M0 activation evidence; M0 freezes the procedure and inputs, not
future market data.

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

The proposed chain-local boundary is file-exact:

| Source file | State/authority that must be a distinct Robinhood instance | Prohibited Base edge |
| --- | --- | --- |
| `contracts/registries/RipeHq.vy`; `contracts/modules/Addys.vy` | Root address registry and every resolved Department/token address | No Base RipeHq or Base Department address may be registered or used as fallback |
| `contracts/registries/VaultBook.vy`; proposed `contracts/vaults/GuardedErc20.vy` | Vault registry, AAPL nominal accounting, and AAPL custody | No shared vault, custody address, VaultBook ID meaning, or token balance |
| `contracts/data/Ledger.vy`; `contracts/core/CreditEngine.vy` | User/global debt, participation, bad debt, and collateral evaluation | No remote debt read/write, shared debt store, or cross-chain credit |
| `contracts/data/MissionControl.vy` | Asset, route, debt-term, reward, permission, and pause configuration | No remote config read/write or Base default fallback |
| `contracts/core/AuctionHouse.vy`; `contracts/core/Teller.vy` | Auction state, settlement, deposits, and withdrawals | No remote auction/settlement call or Base vault consumer |
| `contracts/core/Lootbox.vy` | Points and RIPE reward accounting | No shared reward accumulator or cross-chain claim |
| `contracts/tokens/GreenToken.vy`; `contracts/tokens/RipeToken.vy`; `contracts/tokens/SavingsGreen.vy` | Chain-local GREEN, RIPE, and sGREEN supply/balances/roles | No mint/burn/message authority connecting Base during launch; later GREEN/RIPE CCIP is a separately reviewed intentional economic edge; sGREEN never has one |

The later deployment proof must resolve every row to a Robinhood address and
runtime hash and show that no address equals a Base deployment. M0 freezes that
graph and the exact source boundary; it cannot fabricate the future addresses.

### 7.3 Propagation-path matrix

| Possible path | Current repository/deployment evidence | Can Base failure alter Robinhood protocol state? | M0 disposition |
| --- | --- | --- | --- |
| Shared vault custody | Base vault address is chain-local; no RH Ripe vault exists | No current path | M0 freezes a distinct-chain deployment requirement; later deployment proof must reject every Base address |
| Shared Ledger/credit/debt | Base Ledger is manifest-pinned; Addys resolves local HQ | No current path | M0 freezes local-HQ resolution; later deployment proof must show distinct RH HQ/Ledger and state roots |
| Shared AuctionHouse/settlement | Base AuctionHouse is manifest-pinned; no remote call source exists | No current path | M0 freezes the local AuctionHouse/GREEN graph; distinct deployed addresses are post-M0 proof |
| Shared MissionControl/config | Local HQ resolution only | No current path | M0 freezes local-only resolution; distinct RH MissionControl/default manifest is post-M0 proof |
| Stock-token authority | AAPL beacon/registry exists on Robinhood; no repository or deployment evidence inspected in M0 identifies a Base Ripe address as privileged in that graph | No Base-to-RH protocol-state path observed from the available evidence | Enumerate exact launch-token roles at freeze; an unknown role is a stop |
| Shared offchain operator/governance person | Possible operationally, but not an automatic state edge | No by itself | Role errors remain operational risk, not state propagation |
| GREEN/RIPE CCIP burn/mint pools | Owner-selected post-launch target; no complete production source/deployment evidence yet | **Yes if activated:** Base-originated excess/unsafe GREEN can be burned/minted into RH supply and affect liquidity, repayment, PSM, or accounting; token/pool authority is a direct edge | Target a separately reviewed promotion within seven days after launch; this is not automatic authorization, incomplete or late evidence leaves CCIP disabled, and sGREEN has no route |
| USDG/PSM or other external bridge | PSM is a launch target, but no cross-chain USDG route is approved by this record | Unknown if a remote edge is introduced | PSM must be chain-local under the current independence proof; any remote custody/message/token-authority edge is a hard stop |

### 7.4 Independence conclusion

The file-level architecture supports independence. M0 can close its
**file-exact proposed deployment-graph proof** without a not-yet-created
Robinhood manifest if both requirements are frozen:

1. every Robinhood Ripe contract, registry, custody address, debt store,
   auction store, configuration store, and token authority is a distinct
   chain-local instance; and
2. GREEN/RIPE CCIP and every other cross-chain state/economic route is either
   omitted/provably inactive or fully enumerated with a revised propagation
   and security conclusion.

Actual new Robinhood addresses, runtime hashes, manifest, and post-deployment
state-root checks are later gates. CCIP is a nonblocking target for a fresh,
separately reviewed promotion within seven days after launch. Seven days is
not automatic authorization; incomplete or late evidence leaves CCIP
disabled. If it enables later, the promotion package must describe the
intentional economic edge rather than claim strict state independence.
sGREEN must remain chain-native with no CCIP path in every case.

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

### 8.2 Owner-approved reward lifecycle

The owner selected:

1. launch with `arePointsEnabled=false`, `ripePerBlock=0`, and no live reward
   distribution;
2. target activation within seven days after launch, subject to validation;
3. permit AAPL depositors and AAPL-backed borrowers to participate after that
   validation;
4. accept that nominal/global accounting can briefly accrue rewards after an
   issuer/custody incident until the global switches are disabled; and
5. require live monitoring and a rehearsed
   `arePointsEnabled`/`ripePerBlock` kill-switch runbook.

No reward-accounting contract change is required by default. M0 closed after
independent review, and the pre-implementation runbook is exact. The seven-day
target is not permission to distribute rewards.

### 8.3 Source-exact incident runbook

The two controls have different authority and timing:

| Control | Current source path | Authority/timing | Required use |
| --- | --- | --- | --- |
| Stop new point accrual | `SwitchboardAlpha.setRewardsPointsEnabled(false)` -> `MissionControl.setRipeRewardsConfig` | Governance, or a configured MissionControl lite actor when disabling; immediate | Must already be `false` at launch. After a later reward promotion, the incident operator disables it in the first response transaction and verifies `MissionControl.getRewardsConfig().arePointsEnabled == false` plus `RewardsPointsEnabledModified(false, caller)`. |
| Stop the RIPE-per-block schedule | `SwitchboardAlpha.setRipePerBlock(0)` -> pending `RIPE_REWARDS_BLOCK` action -> `executePendingAction` | Governance-only initiation and execution after the configured timelock | Must already be `0` at launch. After a later reward promotion, governance immediately initiates zero, records action ID/confirmation block, and executes at the first eligible block; readback must prove `ripePerBlock == 0` and the `RipeRewardsPerBlockSet(0)` event. |

Monitoring must alert on AAPL proxy/beacon/implementation change, pause or
blocklist control use, unknown backing read, `C<N`, failed external delivery,
and any mismatch between the two launch-disabled readbacks and expected
configuration. On an incident:

1. disable AAPL deposits and auction purchases through existing fast-disable
   controls, preserve `canRepay=true`, and use the global borrow stop if new
   borrowing must halt before a custody deficit is observable;
2. execute the immediate points disable and initiate the timelocked
   `ripePerBlock=0` action;
3. record chain, block/hash/timestamp, callers, action ID, events, and
   MissionControl readbacks;
4. verify no further point accrual after the disable block and quantify any
   distribution/claim exposure that remains during the emission timelock; and
5. keep the affected Stock path and reward promotion disabled until an
   independently reviewed recovery package proves backing, token identity,
   configuration, and reward state.

The owner accepts the brief nominal/global accounting window, but the
timelocked emission change means “two-switch kill” is not two simultaneous
fast stops. Failure to provision a live lite actor, governance execution path,
monitor, or confirmation-block runbook is a post-M0 launch/promotion stop.

## 9. Incompatibilities, unknowns, and accepted residual risk

### 9.1 Incompatibilities found

- No current incompatibility was found in the exact AAPL proxy at RH-M0-01 or
  RH-T2-01.
- No Base row was shown to take a transfer fee or rebase balance units on
  ordinary transfer under the current inspected source class.
- Per-route fork execution is incomplete for all 27 Base rows, so none is
  approved for a forward-source Base cutover by this file.

### 9.2 True M0 hard stops

Any of the following would stop M0 before a later M1 authorization could be
approved. Independent review confirmed that the present package closes each
at the pre-implementation level:

- An already-existing external token proposed for a Robinhood route is not
  explicitly named by address and identity, or remains fee-taking,
  short-receipt, rebasing-on-transfer, malformed-read, or unknown.
- The approved launch graph or any route disposition remains ambiguous,
  including existing AAPL/USDG/WETH identities and the proposed file/route
  disposition for sGREEN, PSM, Stability Pool, RipeGov, or either future LP.
- The file-exact proposed deployment graph exposes an unclassified bridge,
  message, shared custody, credit, debt, settlement, accounting, or
  token-authority path capable of propagating a Base failure into Robinhood.
- The CCIP complete-or-disabled policy, separate seven-day promotion target,
  fresh-promotion-package requirement, or permanent sGREEN exclusion is not
  frozen.
- The launch-disabled reward posture or the
  `arePointsEnabled`/`ripePerBlock` incident runbook is incomplete.
- A refreshed Base `C<N` row has borrow capacity, exposed debt or auction,
  live short receipt, or another immediately exploitable mismatch.
- The AAPL implementation identity changes without revalidation, or the
  approved AAPL/USD feed, price-pin procedure, cap inputs/formula/rounding, or
  review cadence remains incomplete.
- The exact proposed Teller/`GuardedErc20`/CreditEngine file boundary or
  unchanged AuctionHouse/Deleverage/interface/storage/Ledger boundary remains
  ambiguous.
- Source tracing cannot make guarded internal settlement plausible without
  zero-backed payment, first-withdrawer allocation, or production-surface
  expansion.
- The owner has not confirmed or rejected the exact partial-fill invariant.
- A file-exact M1 authorization proposal is not ready.

Implemented GuardedErc20 source/compiler/storage/ABI/runtime evidence,
composed implementation tests, actual new Ripe addresses/runtime hashes,
post-deployment route/configuration proof, exact freeze-time cap integers, and
final M1–M5 integration/activation evidence do not exist yet by design and are
not M0 hard stops.

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
- Disabled CCIP preserves state independence but creates chain-local
  GREEN/RIPE liquidity and supply until the separately gated target enables.
- After reward activation, a global/nominal accrual window may persist between
  an issuer incident and operation of the two global kill switches.
- Guarded internal settlement does not exercise AAPL transfer, blocklist, or
  recipient-eligibility controls; the buyer's nominal claim may later freeze
  or become undeliverable.

### 9.4 Pre-implementation closure manifest

| M0 input | Closing evidence | Result |
| --- | --- | --- |
| Existing external tokens | Section 4.2 plus Sections 5 and 6; integrated `usdg-public-evidence.md`; operator token-contract directory | AAPL exact-transfer candidate; USDG exact-transfer but PSM/LP-only; WETH constituent-only; every other external asset omitted |
| Launch graph/routes | Sections 4.1–4.2 and owner-packet Sections 2 and 4 | AAPL-only Stock; one-vault intent; every AAPL trusted/Department route disabled; all unsupported Stock routes omitted |
| AAPL feed/caps | Section 5.4 | Proxy, decimals, heartbeat, round-quality rules, floor formula, two USD targets, review triggers, and final-freeze evidence shape frozen |
| Robinhood/Base independence | Section 7 | Distinct local RipeHq graph and disabled-at-launch CCIP; no observed current propagation path; actual new addresses/runtimes remain post-M0 |
| CCIP | Sections 7.3–7.4 and owner packet 2.2 | GREEN/RIPE disabled at launch unless later separately promoted; seven-day target is non-authorizing; sGREEN never CCIP |
| Rewards | Sections 8.1–8.3 | Both launch values zero; points fast-disable and timelocked emission-zero procedure distinguished; monitoring/evidence/runbook frozen |
| Three-file boundary | Specification Sections 23.2–23.4 and owner-packet Section 7 | `Teller.vy`, proposed `GuardedErc20.vy`, and `CreditEngine.vy`; AuctionHouse/Deleverage/interfaces/Ledger negative-diff boundary |
| Mechanism plausibility | Specification Sections 23.3 A–D, current-source caller matrix in Section 4.1, and owner-approved invariant in Section 12 | ML-01–ML-07 are source-plausible within the three-production-contract boundary; composed implementation proof remains mandatory post-M0 |
| M1 proposal | Owner-packet Section 10 and specification Section 23.9.1 | Teller-only production slice, exact later baseline placeholder, allowed existing tests, excluded files, reviewers, stop conditions, and exit evidence fixed |

This manifest does not claim that future Ripe contracts, LPs, DEX/pool
selection, deployed runtimes, routes, or configuration exist. Those artifacts
cannot be M0 evidence. It confirms only that no remaining unknown
already-existing external asset can reach the proposed Teller under the frozen
graph.

## 10. Historical post-M0 decision return

This section records the questions returned before the 24–25 July 2026 owner
decision revisions. Section 12 is controlling. The owner has now selected the
policy directions, including the partial-fill invariant. Independent review
confirmed the pre-implementation identity, compatibility,
parameter-procedure, route-disposition, runbook, source-plausibility,
decision, and M1-proposal evidence.

### D-M0-01 — Freeze the complete Robinhood Teller asset graph

Provide one exhaustive table containing:

- every launch Stock Token proxy address;
- every already-existing external non-Stock token address, including canonical
  USDG and the external constituents/dependencies of the launch LPs;
- proposed file and route dispositions for new Ripe artifacts such as RIPE,
  GREEN, and sGREEN, without fabricating future deployment addresses;
- ordinary/trusted route availability;
- target vault class, without selecting the production launch vault or ID in
  this M0 record;
- enabled, disabled, omitted, or inactive-staging disposition; and
- code/proxy/beacon/implementation identity for every already-existing
  external token proposed for enablement.

The owner selected AAPL as the only initial Stock Token and named the non-Stock
launch targets. Section 4.2 now freezes every existing external identity that
can reach Teller and the complete route/file disposition. New Ripe deployment
addresses, pool/factory selection, runtimes, and composed route tests are later
launch gates.

### D-M0-02 — Initial cross-chain posture

Resolved direction: launch does not depend on CCIP. GREEN and RIPE target a
fresh, separately reviewed promotion within seven days after launch. Seven
days is a target, not automatic authorization; any incomplete or late package
leaves CCIP disabled. sGREEN never has a CCIP route. The promotion package,
deployed route identities, authorities, monitoring, rollback, and propagation
evidence are post-M0.

### D-M0-03 — Day-one rewards

Resolved by Section 8.2: global disable at launch, then a validated target
activation within seven days that may include AAPL positions.

### D-M0-04 — AAPL fork-refresh sufficiency

Historical alternatives:

- accept the integrated immutable RH-T2-01 exact fork plus RH-M0-01's current
  identity match for M0; or
- require a fresh rerun through an approved archive-capable provider. Any
  credential must remain outside the repository and logs.

This decision does not approve a live AAPL transfer.

### D-M0-05 — Base sequencing and residual risk

Historical confirmation request:

- BASE-M0-01 does not demonstrate an urgent live Base vulnerability;
- Robinhood-first may continue after the other M0 stops close;
- current Base runtimes remain unchanged; and
- the three legacy Base mechanisms and future per-asset fork gap are accepted
  until a separate Base hardening/migration decision.

Rejecting this statement returns Base sequencing to owner/security review; it
does not authorize a migration.

### D-M0-06 — Future Base cutover

The owner confirmed that this file does **not** approve a Base cutover. All 27
rows require route-exact fork/equivalent evidence, implementation/control
refresh, borrower position enumeration, auction enumeration, and separate
migration approval before any forward-source Base deployment.

### D-M0-07 — Next authorization boundary

The pre-implementation package in Section 9.2 was independently reviewed, and
the owner explicitly closed M0 on 25 July 2026. The owner used the first of
the following two separate authorization paths:

- this documentation-only M0 closure revision; or
- a later file-exact M1 implementation slice, which remains unauthorized.

Nothing in this file authorizes M1. No production vault or VaultBook ID is
selected. The three-contract direction is documented but remains unimplemented
and evidence-dependent.

## 11. M0 checklist

- [x] Fresh worktree and branch created from exact integrated commit.
- [x] Original M0 evidence acquisition changed only this file and its sanitized
  raw companion.
- [x] The later 24–25 July owner-decision revisions update this file, the
  packet, specification, and validation plan only; the raw companion remains
  immutable.
- [x] Exact original Base RPC URL, raw replay provenance, companion SHA-256,
  and unavailable-response classifications recorded without credentials.
- [x] Current-source ordinary and trusted Teller caller inventory complete.
- [x] M0 Robinhood asset matrix complete — **AAPL, canonical USDG, and WETH
  constituent identities plus all route/file dispositions are frozen; new
  Ripe/LP runtimes are post-M0**.
- [x] Exact AAPL proxy/beacon/implementation and live hashes refreshed.
- [x] Integrated exact AAPL fork behavior preserved with immutable provenance.
- [x] Fresh AAPL fork rerun not required for M0 — **owner accepted integrated
  fork plus current identity; identity change requires revalidation**.
- [x] All 27 Base ID-3 assets refreshed for `C/N`, deposit support, LTV,
  liquidation route, points allocation, and exact-block runtime hash.
- [x] Nine funded Base rows and WETH one-unit surplus confirmed.
- [x] Base aggregate debt, borrower count, auction sentinel, bad debt, yield,
  and rewards recorded.
- [x] No urgent-live Base criterion observed.
- [x] Robinhood/Base file-exact proposed state-independence proof complete —
  **CCIP is disabled at launch and separately promoted; actual new
  addresses/runtime hashes are post-M0**.
- [x] Every Stock-capable reward bucket identified.
- [x] Day-one reward policy frozen — **global disable, later validated target
  activation**.
- [x] AAPL feed, price-pin procedure, cap inputs/formula/rounding, and review
  cadence frozen — **actual freeze-time cap integers are post-M0**.
- [x] Exact proposed three-contract/file and unchanged-consumer boundary plus
  source-traced mechanism plausibility complete.
- [x] Exact partial-fill invariant owner-confirmed on 25 July 2026.
- [x] File-exact M1 authorization proposal ready in the owner packet without
  beginning M1.
- [x] Independent reviewer confirmed no M0 hard stop was converted into an
  unsupported documentation assumption.
- [x] Owner closed M0 at reviewed commit
  `c5c8b699b229792dc61e66af35502684ea3c8155` on 25 July 2026.
- [x] No state-changing transaction, signing, deployment, configuration,
  migration, or live transfer performed.
- [x] No secret or credential recorded.
- [x] M1 not begun.

## 12. Controlling owner-decision revision — 24–25 July 2026

The complete owner record is
`track-8-m0-owner-decision-packet.md`. The evidence effect is:

| Direction | Evidence consequence |
| --- | --- |
| AAPL only | Other Stock Tokens no longer block initial launch, but cannot be enabled without a complete token-specific row. |
| CCIP target, nonblocking | Target a fresh, separately reviewed promotion within seven days after launch. Seven days is not automatic authorization; incomplete or late evidence leaves CCIP disabled. sGREEN has no CCIP path. |
| Rewards disabled then target activation | Prove launch disable, live monitoring, and both global kill switches; later AAPL reward participation remains validation-gated. |
| Existing AAPL fork accepted | No new historical fork is required unless identity changes; the prior provider limitation remains disclosed. |
| Base unchanged | No cutover evidence is needed for Robinhood launch beyond current-state risk and independence; every later cutover is separate. |
| sGREEN, PSM, Stability, RipeGov, LP launch targets | M0 freezes existing external dependencies and proposed route/file dispositions; new Ripe identities, runtime hashes, and composed route evidence are later gates. |
| AAPL USD targets/cardinality | M0 records the approved feed, pin procedure, cap formula/inputs/rounding/review cadence, one-vault policy, and trusted-route-disable policy. The actual freeze price, 18-decimal cap integers, new vault address, and post-deployment configuration proof are later gates. |
| Guarded internal settlement | Owner-selected vault-local direction with the exact partial-fill invariant owner-approved on 25 July 2026. M0 source tracing establishes plausibility; composed implementation evidence is post-M0. |
| Unacceptable boundary | Phantom collateral, first-withdrawer allocation, and zero-backed payment/debt reduction remain hard stops. |

The owner approved the exact internal-settlement partial-fill invariant on
25 July 2026:

```text
0 < W <= Q
sellerNominalDecrease == W
buyerNominalIncrease == W
aggregateNominalAfter == N
known(C0,C1)
C0 >= N
C1 >= N
C1 == C0
payment and debt reduction are based only on W
```

Here `Q` is the AuctionHouse maximum request and `W` is the amount actually
moved. The rule permits a safe partial fill when the seller's remaining
nominal balance is smaller than `Q`. Later composed validation must cover full
fill, partial fill, seller depletion, batch auctions, over-request, and
failure atomicity. External settlement remains governed independently by
exact delivery and `E=min(Q,W,R)`.

The guarded internal direction does not require a larger production surface on
the current source evidence. Teller remains necessary for exact call-local
deposit receipt, the fresh vault owns both external and internal settlement
proofs, CreditEngine preserves unsafe-position terms, and AuctionHouse already
commits payment/debt only after the vault returns. An AuctionHouse change,
persistent mode field, canonical-interface change, Ledger change, or
chain-specific branch is a stop-and-return unless independent composed review
proves it necessary.

The owner also expressly accepted that a successful internal accounting move
does not exercise AAPL transfer, blocklist, or recipient-eligibility controls
and that the buyer's resulting claim can later become frozen or
undeliverable.

All documentable pre-implementation M0 inputs are complete. Independent review
confirmed that no M0 hard stop was converted into an unsupported documentation
assumption, and the owner closed M0 at reviewed commit
`c5c8b699b229792dc61e66af35502684ea3c8155` on 25 July 2026. M1 remains
unauthorized.
