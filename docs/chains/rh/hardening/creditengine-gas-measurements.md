# CreditEngine zero-amount gas measurements

Status: **protocol frozen; local Boa measurements collected**.

This file is the C2 protocol and result record for
`CreditEngine.getUserBorrowTerms`. The original counts, repetitions, and
comparison semantics remain frozen; the environment attestation and results
below bind the current reviewed implementation.

## Subject and question

The measured path is the loop in `_getUserBorrowTerms` that reads every user
position, retains a nominally nonempty `(asset, 0)` position's debt
configuration, checks its vault-wide usability and global support, marks it
quarantined when no usable vault balance remains, and skips PriceDesk only
when its amount is zero
([CreditEngine source](../../../../contracts/core/CreditEngine.vy#L687)).
The comparison asks for the local marginal gas estimate as position count
grows for:

1. `priced`: every returned position is `(asset, 1e18)` and reaches
   `PriceDesk.getUsdValue`;
2. `zero-amount containment`: every returned position is `(asset, 0)`, reports
   a nominal balance with zero vault-wide usable amount, reaches both the debt
   terms and global-support checks, is marked quarantined, and never reaches
   PriceDesk.

This measures the integrated behavior retained by the CreditEngine record. It
does not price a zero amount or restore the prohibited `(asset, 0)` skip
([record](../smart-contract-changes/credit-engine.md#exact-source-delta-and-complete-execution-flow)).

## Frozen setup protocol

| Field | Frozen value and derivation |
| --- | --- |
| Reviewed candidate | PR #211 head `5a623218e6d39b6f1a4799db586160411fc255f9` plus the source-hash-bound remediation below |
| CreditEngine source | `contracts/core/CreditEngine.vy`, SHA-256 `f0811ea1d20d8c68853608bc2fbef03168c6c3e23228d84c9304b6bb0f1b8688` |
| Environment | repository-local `<repo root>/.venv/bin/python`, selected through `RIPE_C2_MEASUREMENT_INTERPRETER` and resolving to the attested Python 3.12 interpreter; installed-distribution manifest SHA-256 `5df5fbc4e94b394f4fbc26a7b2877c731ee33fe7db267a734010c6039ac61138`; interpreter SHA-256 `e2605291e058fdbe3102e8185d0ac5fe0e063398de617010a6af3a42a78f05e3`; `requirements.txt` SHA-256 `4f0097670e618e8210fc7d961d851df643332b3b52d156a0a0b9171e86d1906f` |
| Compiler | `Vyper 0.4.3+commit.bff19ea2`; CreditEngine source pragma governs `codesize`; no `-O` override |
| EVM harness | Titanoboa from the repository `.venv` above; local ephemeral deployment only |
| Public subject | `credit_engine.getUserBorrowTerms(user, True)` |
| Position counts | `1, 2, 4, 8, 16, 50` |
| Largest-count derivation | fixture general configuration permits five user vaults and ten assets per vault, so `5 * 10 = 50` is the largest realistic configured per-user position count ([fixture](../../../../tests/conf_utils.py#L42)) |
| Vault shape | disposable synthetic read-only vaults, at most ten positions each; counts above ten are split `10 + ...` across at most five Ledger-registered vaults |
| Asset shape | one configured disposable asset identity reused in every synthetic row; this isolates loop/path cost rather than configuration diversity |
| Debt terms | one fixed nonzero-LTV debt configuration for that asset; identical in both comparison paths |
| Amounts | priced path `1e18` per row; containment path returns `0` per row for the same nonempty asset identity while `doesUserHaveBalance` returns true and `getTotalAmountForVault` returns zero |
| Price | fixed `1e18` unit price for the priced path |
| Warm/cold policy | every recorded sample is a separate top-level Boa call, so EIP-2929 transaction-local address/storage warmth resets between samples; no intra-transaction warm wrapper is measured |
| Repetitions | one unrecorded warm-up call for Python/Boa dispatch, followed by seven recorded top-level calls per count and comparison path |
| Isolation | fresh pytest process and private mode-0700 Boa, XDG, Hypothesis, and pytest directories; ambient RPC/private-key variables unset; `ETHERSCAN_API_KEY=local-placeholder` prevents live key discovery |

The synthetic vault count convention matches CreditEngine's reviewed loop:
`numUserAssets(user)` returns the exclusive upper bound, and the engine
iterates indices starting at one
([CreditEngine source](../../../../contracts/core/CreditEngine.vy#L716)).
Ledger user-vault registration is performed through the existing test-only
authorized route; no production contract or configuration source is changed.

## Collection and calculations

For each count, the test constructs the same vault partition for the priced and
zero-amount variants. Each sample records:

```python
before = boa.env.get_gas_used()
credit_engine.getUserBorrowTerms(user, True)
sample = boa.env.get_gas_used() - before
```

The committed result table will report all seven raw observations plus:

- median gas for each path and count;
- `priced - zero` median delta at the same count;
- marginal median gas from the preceding count;
- marginal-per-added-position, computed as the marginal median divided by the
  number of added positions.

No pass/fail production gas threshold is inferred. Results are labeled local
Boa estimates, not live-network gas, block-budget approval, deployment
evidence, or release evidence.

## Validation gates

The measurement test must also assert:

- the returned collateral value and total maximum debt equal the priced
  position count times their per-position values;
- the zero path returns zero collateral and zero maximum debt while retaining
  the configured nonzero terms and setting `hasQuarantinedAsset`; the priced
  path must leave `hasQuarantinedAsset` clear;
- the guarded PriceDesk invocation counter is exactly the priced position
  count and zero for the containment path;
- all seven observations for a cell are positive;
- the frozen source hash, environment identity, counts, repetitions, and
  comparison labels match this document.

## Results

The original measurement protocol was committed as `d44ab68`. The current
reviewer-fix revision adds global-support work for every real debt-bearing
position and nominal-balance/quarantine work for a zero-amount containment
row. The synthetic vault was extended only with the two current Vault reader
methods needed to preserve that comparison. The previous external validation
environment was no longer present, so the repository `.venv` was freshly
attested with the hashes above before collection. The accepted run completed
with `1 passed, 3 warnings in 107.83s`. All warnings were pytest
already-imported assertion-rewrite warnings for Hypothesis and Boa; no test was
skipped, xfailed, or deselected.
The accepted harness counts only PriceDesk frames whose calldata selector is
exactly `getUsdValue(address,uint256,bool)`.

### Raw observations

All values are local Boa gas estimates. Each bracket contains all seven
recorded top-level calls.

| Positions | Path | Seven observations | Median | PriceDesk calls per observation |
| ---: | --- | --- | ---: | ---: |
| 1 | priced | `[42985, 42985, 42985, 42985, 42985, 42985, 42985]` | 42,985 | 1 |
| 1 | zero-amount containment | `[25097, 25097, 25097, 25097, 25097, 25097, 25097]` | 25,097 | 0 |
| 2 | priced | `[65945, 65945, 65945, 65945, 65945, 65945, 65945]` | 65,945 | 2 |
| 2 | zero-amount containment | `[30265, 30265, 30265, 30265, 30265, 30265, 30265]` | 30,265 | 0 |
| 4 | priced | `[111865, 111865, 111865, 111865, 111865, 111865, 111865]` | 111,865 | 4 |
| 4 | zero-amount containment | `[40601, 40601, 40601, 40601, 40601, 40601, 40601]` | 40,601 | 0 |
| 8 | priced | `[203705, 203705, 203705, 203705, 203705, 203705, 203705]` | 203,705 | 8 |
| 8 | zero-amount containment | `[61273, 61273, 61273, 61273, 61273, 61273, 61273]` | 61,273 | 0 |
| 16 | priced | `[389931, 389931, 389931, 389931, 389931, 389931, 389931]` | 389,931 | 16 |
| 16 | zero-amount containment | `[105163, 105163, 105163, 105163, 105163, 105163, 105163]` | 105,163 | 0 |
| 50 | priced | `[1178209, 1178209, 1178209, 1178209, 1178209, 1178209, 1178209]` | 1,178,209 | 50 |
| 50 | zero-amount containment | `[288513, 288513, 288513, 288513, 288513, 288513, 288513]` | 288,513 | 0 |

### Marginal calculations

| Positions | Priced median | Zero median | Priced minus zero | Added positions | Priced marginal | Priced per added position | Zero marginal | Zero per added position |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 42,985 | 25,097 | 17,888 | — | — | — | — | — |
| 2 | 65,945 | 30,265 | 35,680 | 1 | 22,960 | 22,960.000 | 5,168 | 5,168.000 |
| 4 | 111,865 | 40,601 | 71,264 | 2 | 45,920 | 22,960.000 | 10,336 | 5,168.000 |
| 8 | 203,705 | 61,273 | 142,432 | 4 | 91,840 | 22,960.000 | 20,672 | 5,168.000 |
| 16 | 389,931 | 105,163 | 284,768 | 8 | 186,226 | 23,278.250 | 43,890 | 5,486.250 |
| 50 | 1,178,209 | 288,513 | 889,696 | 34 | 788,278 | 23,184.647 | 183,350 | 5,392.647 |

The one-, two-, four-, and eight-position cells have exact marginal slopes of
22,960 gas per priced position and 5,168 per contained zero position in this
harness. The later cells cross synthetic-vault boundaries, so their marginal
figures also include additional Ledger/VaultBook/vault-call overhead. At the
fixture-derived 50-position ceiling, the containment path remains below the
priced comparator, but this is not a production gas limit or a release
approval.
