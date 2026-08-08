# Robinhood Stock Token Transferability Evidence

**Track:** 2 — Stock Token Transferability Probe
**Status:** Fork validation passed; live conclusion inconclusive at approval gate
**Retrieval and fork execution date:** 23 July 2026
**Starting repository commit:** `51a7a3996f5fec40efd554d1b025aaa9c2ed4ea2`
**Track branch:** `rh-track-2-stock-transfer`

## Conclusion

**Inconclusive for final live transferability proof.**

At Robinhood Chain mainnet block `17,558,441`, the exact AAPL Stock Token
successfully completed the proposed `approve` → probe `deposit` → probe
`withdraw` → allowance cleanup sequence on a local fork. Exact balances
reconciled, the probe emitted the expected events, and the final probe balance
and allowance were zero.

This is positive technical fork evidence only. No signing credential was
accessed, no transaction was broadcast, no live Stock Token or native token was
moved, and no funds were spent. The holder was impersonated only in ephemeral
fork state. An owner-approved live round trip has not occurred, and the owner
and counsel have not supplied the required sender/recipient eligibility
determination or approved acquisition/provenance path.

The result does not establish legal eligibility, beneficial ownership,
redemption rights, future transferability, liquidation liquidity, or protection
from pause, blocklist, upgrade, multiplier changes, or administrative burn.

## Candidate and primary evidence

| Field | Verified value |
| --- | --- |
| Network | Robinhood Chain mainnet |
| Chain ID | `4663` |
| Token | Apple • Robinhood Token (`AAPL`) |
| Token proxy | `0xaF3D76f1834A1d425780943C99Ea8A608f8a93f9` |
| Decimals | `18` |
| Robinhood asset ID | `0x00000000000000000000000000000000c2425be3658540dd8e2424cbf3c5c649` |
| Registry status | `ASSET_STATUS_ACTIVE` |

The address was tied to the intended instrument through two current Robinhood
sources, rather than a ticker or UI lookup alone:

- Robinhood's live asset registry returned chain ID `4663`, symbol `AAPL`,
  name `Apple • Robinhood Token`, and the proxy address above.
- Robinhood's Apple final terms identify the same smart-contract address.

Sources retrieved 23 July 2026:

- [Robinhood Stock Token API](https://docs.robinhood.com/chain/stock-token-apis/)
- [Robinhood token contracts](https://docs.robinhood.com/chain/contracts/)
- [Apple final terms](https://cdn.robinhood.com/assets/robinhood/legal/rhj_final_terms_for_tokenised_debt_securities_linked_to_apple.pdf)
- [Robinhood Stock Tokens disclosure](https://robinhood.com/rhj/stocktokens/)
- [Robinhood Chain connection details](https://docs.robinhood.com/chain/connecting/)

The official public RPC used for state reads and the fork was
`https://rpc.mainnet.chain.robinhood.com`.

## Pinned onchain identity and state

| Field | Value at pinned block |
| --- | --- |
| Block number | `17,558,441` |
| Block hash | `0x35e8e2a3803cb42c4553cb5f3528b187508c6cc200a8b761943374003b8f0243` |
| Block timestamp | `2026-07-23T18:52:41Z` |
| Proxy code hash | `0x6c1fdd40002dcb440c7fff6a84171404d279ccb057803b65826f7546acd65630` |
| EIP-1967 beacon / access-control registry | `0xe10b6f6B275de231345c20D14Ab812db62151b00` |
| Beacon code hash | `0x8b465c0b53a2ba499566e9b4ca67d8c90ed6131743df806a570d156956a7e90e` |
| Implementation | `0xb35490d6f9163DE4F80d88dc75c3516eb64C5aE2` |
| Implementation code hash | `0xdc07e86ee482f99641bdafb9a0d772846b167401e094d90a666b94dbdcd1eec7` |
| Total supply | `3304177000000000000000` base units |
| Global pause | `false` |
| Token pause | `false` |
| Oracle pause | `false` |
| UI multiplier | `1000000000000000000` |
| New UI multiplier | `1000000000000000000` |
| Pending multiplier | none; effective time `0` |

The proxy, implementation, and registry were also inspected through verified
Blockscout source:

- [AAPL proxy](https://robinhoodchain.blockscout.com/address/0xaF3D76f1834A1d425780943C99Ea8A608f8a93f9)
- [Stock implementation](https://robinhoodchain.blockscout.com/address/0xb35490d6f9163DE4F80d88dc75c3516eb64C5aE2)
- [Access-control registry and beacon](https://robinhoodchain.blockscout.com/address/0xe10b6f6b275de231345c20d14ab812db62151b00)

### Administrative and transfer controls observed

- Transfers fail when the token or global registry is paused.
- The verified transfer path checks sender and recipient blocklist state.
  `transferFrom` also checks the operator, which is the probe for deposits.
- The registry controls the beacon implementation through an upgrader role.
- The implementation exposes privileged mint, burn, administrative burn,
  token-pause, oracle-pause, blocklist, and multiplier-management paths.
- No forced-transfer or forced-redemption entry point was observed in the
  verified ABI/source. This is not proof that such behavior can never be added
  through a beacon upgrade or exercised outside the inspected interface.
- No transfer fee or receiver hook was observed. The token does use scaled-UI
  multiplier accounting. Its multiplier was exactly `1e18` at the pinned block,
  `newUIMultiplier()` also returned `1e18`, and `effectiveAt()` returned `0`.
  The preflight now rejects any future-effective multiplier before execution,
  and the fork verified exact base-unit balance deltas.
- Standard ERC-20 calls returned successfully in the fork. The token emitted
  standard and issuer-specific logs; probe event validation did not depend on
  decoding the issuer-specific event.

For architecture cross-checking only, Robinhood's documented Chainlink AAPL/USD
feed was also inspected:

| Field | Value |
| --- | --- |
| Feed proxy | `0x6B22A786bAa607d76728168703a39Ea9C99f2cD0` |
| Aggregator | `0xBb11A21267cFDb63d4935d99a499133DD1744ACb` |
| Decimals | `8` |
| Heartbeat | `86,400` seconds |
| Latest answer at pinned block | `32079999999` |
| Latest update at pinned block | `2026-07-23T15:07:00Z` |

Source: [Robinhood oracle documentation](https://docs.robinhood.com/chain/oracles-and-price-feeds/).
No oracle or collateral configuration was performed in this track.

## Fork-only holder and approved-input record

| Field | Fork-only value |
| --- | --- |
| Sender | `0x9f736F87E6293AC1Bd9142E257dbfAC8b7AcF1ae` |
| Probe owner | `0x9f736F87E6293AC1Bd9142E257dbfAC8b7AcF1ae` |
| Recipient | `0x9f736F87E6293AC1Bd9142E257dbfAC8b7AcF1ae` |
| AAPL balance at pinned block | `390389871775472346454` base units |
| Native balance at pinned block | `50250706837858000` wei |
| Sender nonce at pinned block | `83` |
| Test amount | `1000000000000000` base units (`0.001 AAPL`) |
| Predicted fork probe | `0xdC40b17919c0a684Cf553C22B394fD44Dd7a712F` |
| Probe runtime code hash | `0xaa9b728174d048a5d65f49f5b4c851413008d6b89f315d36256191bd1a402949` |

The sender was selected from public explorer state solely to make the fork
reproducible. No private key was used or sought, and this address is not
proposed or approved for live use. Its legal or contractual eligibility was not
assessed.

At the pinned block, public `isBlocked(address)` reads were `false` for the
sender, owner, recipient, and predicted probe. Because the three account roles
used the same fork-only EOA, the round trip restored that EOA to its exact
starting balance.

The fail-closed input file is
`scripts/probes/aapl-robinhood-mainnet-fork.json`. It permits `fork-only` scope
and explicitly sets `broadcast_allowed` to `false`. Approval schema version `2`
requires the exact current, new, and effective-at multiplier fields; version
`1` inputs are rejected rather than silently defaulted.

## Fork execution evidence

The fork runner revalidated chain ID, block hash, token code hash, beacon,
implementation, implementation code hash, name, symbol, decimals, pause state,
UI multiplier, new UI multiplier, multiplier effective time, blocklist state,
sender balances, sender nonce, predicted probe address, and compiled runtime
bytecode hash before modifying local fork state.

Sequence and observed balances:

| Checkpoint | Sender / recipient | Probe | Allowance |
| --- | ---: | ---: | ---: |
| Before | `390389871775472346454` | `0` | `0` |
| After exact approval | unchanged | `0` | `1000000000000000` |
| After deposit | `390388871775472346454` | `1000000000000000` | `0` |
| After withdrawal | `390389871775472346454` | `0` | `0` |
| After cleanup | `390389871775472346454` | `0` | `0` |

Decoded probe events:

| Event | Token | Amount |
| --- | --- | ---: |
| `TokenDeposited` | `0xaF3D76f1834A1d425780943C99Ea8A608f8a93f9` | `1000000000000000` |
| `TokenWithdrawn` | `0xaF3D76f1834A1d425780943C99Ea8A608f8a93f9` | `1000000000000000` |

Fork-measured EVM execution gas:

| Step | Gas used |
| --- | ---: |
| Deploy | `363,991` |
| Approve | `30,893` |
| Deposit | `50,320` |
| Withdraw | `22,136` |
| Allowance cleanup | `6,993` |
| Total | `474,333` |

Deposit execution gas decreased from `52,783` to `50,320` after the owner-only
check was added, while deployment increased as expected. Repeated pinned-fork
runs reproduced both figures and the `474,333` total. The decrease is a
deterministic result consistent with compiler code-layout/dispatch changes from
recompiling the contract, not measurement drift.

These figures are fork execution gas, not a live fee quote or an approved
maximum. A live estimate must be regenerated against the owner-approved sender,
nonce, fee conditions, and final transaction set immediately before any
broadcast.

No fork transfer reverted. Local negative tests captured expected failures for
zero amount, insufficient allowance, insufficient balance, wrong token,
unauthorized deposit/withdrawal/recovery, over-balance withdrawal/recovery,
false-returning and reverting tokens, paused transfers, blocked
sender/probe/recipient, and an independently isolated blocked `transferFrom`
operator.

Fork limitations:

- Holder impersonation was required; no signature was produced.
- All deployments and transactions existed only in the local fork process.
- The predicted probe address depends on the sender nonce at the pinned block.
- Sender and recipient were the same address; local tests separately cover a
  distinct configured recipient.
- Fork preflight requires only a nonzero native balance. Phase D must instead
  prove that the approved sender covers the owner-approved maximum gas spend.
- Mainnet state, proxy implementation, administrative flags, blocklists,
  multiplier, nonce, balances, gas price, and legal restrictions can change.
- A fresh Phase D preflight must repeat the multiplier check immediately before
  every proposed broadcast; the pinned fork cannot rule out later scheduling.
- Fork success is not final live transferability proof.

## Reusable probe and tooling isolation

`contracts/testing/StockTokenTransferProbe.vy`:

- binds immutable owner, token, and recipient addresses;
- rejects a zero address or configured token address without deployed code;
- allows only the configured owner to initiate a deposit;
- pulls only the configured token through `transferFrom`;
- requires exact probe balance deltas;
- allows only the owner to withdraw to the configured recipient;
- has no arbitrary external-call surface;
- emits deposit, withdrawal, and recovery evidence; and
- provides owner-only ERC-20 recovery to the configured recipient.

All three state-changing probe entry points use Vyper's `@nonreentrant`
protection. No adversarial callback mock was added because the verified AAPL
target has no receiver-hook path and this track does not generalize the runner
to hook-bearing assets. A candidate with hooks or callbacks would require
candidate-specific reentrancy coverage before use.

Recovery deliberately retains the same exact-delta invariant as the transfer
probe. A fee-on-transfer token, false-returning token, token that blocklists the
configured recipient, or otherwise nonconforming junk token can therefore
remain unrecoverable. Relaxing the recipient-delta check would make recovery
appear successful while delivering less than the requested amount, so this
throwaway per-run probe fails closed instead. A focused test records the
false-returning-token case, and a fee-on-transfer test demonstrates both failed
deposit and deliberately unrecoverable retained-token behavior.

The four Phase-B tooling surfaces were audited:

- **ABI export:** default export excludes both `contracts/mock/` and
  `contracts/testing/`; a focused test verifies the behavior.
- **Production migration:** `load_vyper_files()` excludes
  `contracts/testing/`, and a focused test verifies the probe is absent.
- **Explorer verification:** `scripts/verify.py` iterates only contracts already
  present in a selected migration manifest; it does not glob contract source.
  Because production migration discovery excludes the probe, it is not swept
  into a production verification manifest. The console's source catalog uses
  the same excluded `load_vyper_files()` path.
- **Packaging:** no `pyproject.toml`, `setup.py`, `setup.cfg`, `MANIFEST.in`,
  `package.json`, Dockerfile, or other repository packaging configuration was
  present to sweep `contracts/testing/`.

The Vyper probe is generic for ERC-20 candidates. The Python runner is
intentionally Robinhood-Stock-Token-specific: it requires the current
beacon/registry, pause, blocklist, and scaled-UI multiplier interfaces. A
non-Robinhood candidate needs an adapted preflight, not changes to the probe.

Integration note: Track 5 should reuse or extend
`contracts/mock/MockProbeErc20.vy` for overlapping pause, blocklist,
false-return, and revert behavior rather than introduce a redundant test
double. Until this Track 2 branch is integrated, other branches cut from an
older baseline do not inherit the `contracts/testing/` migration and ABI-export
exclusions.

Reproduction commands:

```bash
python -m pytest tests/probes -q

python scripts/probes/stock_token_transfer_probe.py \
  --approval-file scripts/probes/aapl-robinhood-mainnet-fork.json \
  --rpc-url https://rpc.mainnet.chain.robinhood.com

python scripts/probes/stock_token_transfer_probe.py \
  --approval-file scripts/probes/aapl-robinhood-mainnet-fork.json \
  --rpc-url https://rpc.mainnet.chain.robinhood.com \
  --fork
```

The first runner command is read-only dry-run output. The second modifies only
ephemeral local fork state. Supplying `--broadcast` always raises an error; the
CLI prints a concise error without a traceback, and the runner contains no
signing or broadcast implementation. The CLI formats expected `ApprovalError`
stops; unexpected transport or runtime failures deliberately retain tracebacks
so infrastructure faults are not mistaken for transferability findings.

### Validation results after reviewer hardening

- `python -m pytest tests/probes -q`: **40 passed**.
- Combined `tests/probes`, BasicVault, SharesVault, and ERC-20 selection:
  **75 passed** (`40` Track 2 tests plus `35` existing regression tests).
- Scoped `ruff check` over the runner and two probe test files: passed.
- Repository-wide Ruff was not used as an acceptance claim: the repository has
  no Ruff configuration and reports `445` pre-existing errors. The `F541` in
  touched `scripts/utils/migration_helpers.py` exists unchanged at the recorded
  starting commit.
- Python syntax compilation, Vyper compilation for the probe and mock, and
  `git diff --check`: passed.
- Read-only dry-run and the pinned fork sequence: passed with the exact state,
  balances, events, runtime hash, and gas figures recorded above.

## Live approval gate and blockers

No live transaction may proceed until the owner explicitly approves all of the
following after a fresh preflight:

1. Robinhood Chain mainnet, chain ID `4663`.
2. The canonical AAPL proxy, then-current beacon and implementation, and exact
   runtime code hashes.
3. A live test amount. The fork used `0.001 AAPL`; that value is a proposal, not
   live approval.
4. A funded sender who will also deploy and own the probe: the live sender,
   deployer, and immutable `OWNER` must be the same public address. That
   address's legal and contractual eligibility must be determined outside this
   track by the owner and counsel.
5. The recipient and any owner/counsel eligibility determination that applies.
6. The approved acquisition/provenance path for the test amount.
7. The signing and broadcast mechanism.
8. The maximum acceptable gas spend and final fee fields.
9. The final sequence: deploy; approve only the exact amount; deposit; verify;
   withdraw to the approved recipient; verify; clear allowance; verify zero
   probe balance and allowance.

Current blockers:

- No owner/counsel sender or recipient eligibility determination was supplied.
- No acquisition/provenance path was approved.
- No funded live sender or approved live recipient was supplied.
- No signing/broadcast mechanism was approved.
- No maximum gas spend or final live transaction set was approved.

Live probe address, transaction hashes, block numbers, live balances, and live
event records are therefore **not applicable / not yet produced**.

## Checklist items eligible for owner review

The implementation and fork evidence are ready for owner review against
`docs/chains/rh-summary.md` section 4:

> Add a reusable transferability probe for each candidate Stock Token and run
> it against the exact launch contract.

The reusable-probe portion and exact-contract fork run are reviewable. The item
is not yet eligible for closure because the Track 2 contract states that mocks
and fork success are not final proof.

The Phase-0 claim that:

> a Stock Token can transfer into and back out of a third-party test contract

is also supported on a pinned fork but is not eligible for closure until the
owner authorizes and reviews a compliant live round trip, or accepts the
documented live blocker as the track outcome.
