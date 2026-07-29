# CreditEngine zero-amount gas measurements

Status: **protocol frozen; local Boa measurements collected**.

This file is the C2 protocol and eventual result record for
`CreditEngine.getUserBorrowTerms`. The protocol is committed before any C2
measurement is collected. Results will be added in a later commit without
changing the protocol.

## Subject and question

The measured path is the loop in `_getUserBorrowTerms` that reads every user
position, retains a nonempty `(asset, 0)` position's debt configuration, and
skips PriceDesk only when its amount is zero
([CreditEngine source](../../../../contracts/core/CreditEngine.vy#L687)).
The comparison asks for the local marginal gas estimate as position count
grows for:

1. `priced`: every returned position is `(asset, 1e18)` and reaches
   `PriceDesk.getUsdValue`;
2. `zero-amount containment`: every returned position is `(asset, 0)`, still
   reaches `MissionControl.getDebtTerms`, and never reaches PriceDesk.

This measures the integrated behavior retained by the CreditEngine record; it
does not price a zero amount, restore the prohibited `(asset, 0)` skip, or add
a custody reader
([record](../smart-contract-changes/credit-engine.md#exact-source-delta-and-complete-execution-flow)).

## Frozen setup protocol

| Field | Frozen value and derivation |
| --- | --- |
| Repository baseline | `a86650b187c523f27c92f05bfe959d06840025a6` |
| CreditEngine source | `contracts/core/CreditEngine.vy`, SHA-256 `7de649cece6e076b75775bb4ff5f397bf5ffa0a50ccdc462a061ca047b888e3d` |
| Environment | exact-lock venv `/private/tmp/ripe-rh-final-gate2.uZCfBL/venv`; canonical environment manifest SHA-256 `f0393df6e4c1728b28d95e5034fee7b6ca4c5463df8fb387dbae839e15b87e4d` |
| Compiler | `Vyper 0.4.3+commit.bff19ea2`; CreditEngine source pragma governs `codesize`; no `-O` override |
| EVM harness | Titanoboa from the exact-lock environment; local ephemeral deployment only |
| Public subject | `credit_engine.getUserBorrowTerms(user, True)` |
| Position counts | `1, 2, 4, 8, 16, 50` |
| Largest-count derivation | fixture general configuration permits five user vaults and ten assets per vault, so `5 * 10 = 50` is the largest realistic configured per-user position count ([fixture](../../../../tests/conf_utils.py#L42)) |
| Vault shape | disposable synthetic read-only vaults, at most ten positions each; counts above ten are split `10 + ...` across at most five Ledger-registered vaults |
| Asset shape | one configured disposable asset identity reused in every synthetic row; this isolates loop/path cost rather than configuration diversity |
| Debt terms | one fixed nonzero-LTV debt configuration for that asset; identical in both comparison paths |
| Amounts | priced path `1e18` per row; containment path `0` per row with the same nonempty asset identity |
| Price | fixed `1e18` unit price for the priced path |
| Warm/cold policy | every recorded sample is a separate top-level Boa call, so EIP-2929 transaction-local address/storage warmth resets between samples; no intra-transaction warm wrapper is measured |
| Repetitions | one unrecorded warm-up call for Python/Boa dispatch, followed by seven recorded top-level calls per count and comparison path |
| Isolation | fresh pytest process and private mode-0700 Boa, XDG, Hypothesis, and pytest directories; ambient dotenv and every listed RPC/key variable unset |

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
  the configured nonzero terms;
- the guarded PriceDesk invocation counter is exactly the priced position
  count and zero for the containment path;
- all seven observations for a cell are positive;
- the frozen source hash, environment identity, counts, repetitions, and
  comparison labels match this document.

## Results

The protocol was committed first as `d44ab68`. The accepted run then completed
with `1 passed, 3 warnings in 106.94s`. All warnings were pytest
already-imported assertion-rewrite warnings for Hypothesis and Boa; no test was
skipped, xfailed, or deselected.

An initial collection attempt was rejected at the first priced cell because
the trace counter counted two frames sharing the PriceDesk code address. No
partial observation from that attempt is included. The accepted harness counts
only PriceDesk frames whose calldata selector is exactly
`getUsdValue(address,uint256,bool)`; the frozen protocol itself was unchanged.

### Raw observations

All values are local Boa gas estimates. Each bracket contains all seven
recorded top-level calls.

| Positions | Path | Seven observations | Median | PriceDesk calls per observation |
| ---: | --- | --- | ---: | ---: |
| 1 | priced | `[37637, 37637, 37637, 37637, 37637, 37637, 37637]` | 37,637 | 1 |
| 1 | zero-amount containment | `[21950, 21950, 21950, 21950, 21950, 21950, 21950]` | 21,950 | 0 |
| 2 | priced | `[56681, 56681, 56681, 56681, 56681, 56681, 56681]` | 56,681 | 2 |
| 2 | zero-amount containment | `[25411, 25411, 25411, 25411, 25411, 25411, 25411]` | 25,411 | 0 |
| 4 | priced | `[94769, 94769, 94769, 94769, 94769, 94769, 94769]` | 94,769 | 4 |
| 4 | zero-amount containment | `[32333, 32333, 32333, 32333, 32333, 32333, 32333]` | 32,333 | 0 |
| 8 | priced | `[170945, 170945, 170945, 170945, 170945, 170945, 170945]` | 170,945 | 8 |
| 8 | zero-amount containment | `[46177, 46177, 46177, 46177, 46177, 46177, 46177]` | 46,177 | 0 |
| 16 | priced | `[325068, 325068, 325068, 325068, 325068, 325068, 325068]` | 325,068 | 16 |
| 16 | zero-amount containment | `[75636, 75636, 75636, 75636, 75636, 75636, 75636]` | 75,636 | 0 |
| 50 | priced | `[977877, 977877, 977877, 977877, 977877, 977877, 977877]` | 977,877 | 50 |
| 50 | zero-amount containment | `[198623, 198623, 198623, 198623, 198623, 198623, 198623]` | 198,623 | 0 |

### Marginal calculations

| Positions | Priced median | Zero median | Priced minus zero | Added positions | Priced marginal | Priced per added position | Zero marginal | Zero per added position |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 37,637 | 21,950 | 15,687 | — | — | — | — | — |
| 2 | 56,681 | 25,411 | 31,270 | 1 | 19,044 | 19,044.000 | 3,461 | 3,461.000 |
| 4 | 94,769 | 32,333 | 62,436 | 2 | 38,088 | 19,044.000 | 6,922 | 3,461.000 |
| 8 | 170,945 | 46,177 | 124,768 | 4 | 76,176 | 19,044.000 | 13,844 | 3,461.000 |
| 16 | 325,068 | 75,636 | 249,432 | 8 | 154,123 | 19,265.375 | 29,459 | 3,682.375 |
| 50 | 977,877 | 198,623 | 779,254 | 34 | 652,809 | 19,200.265 | 122,987 | 3,617.265 |

The one-, two-, four-, and eight-position cells have exact marginal slopes of
19,044 gas per priced position and 3,461 per contained zero position in this
harness. The later cells cross synthetic-vault boundaries, so their marginal
figures also include additional Ledger/VaultBook/vault-call overhead. At the
fixture-derived 50-position ceiling, the containment path remains below the
priced comparator, but this is not a production gas limit or a release
approval.
