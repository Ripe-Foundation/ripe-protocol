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
| Reviewed implementation parent | `fdf19226f0d8f4b42741f2ce324f8ccb9ba20336`; the source hash below binds the subsequent reviewer-fix revision |
| CreditEngine source | `contracts/core/CreditEngine.vy`, SHA-256 `05bb1157c6885fc734cc4831efa2fe6aa4c189d14a1bc22bb80472103de105bb` |
| Environment | validation venv `${HOME}/dev/ripe-protocol-validation-envs/rh-wave2-py312`; installed-distribution manifest SHA-256 `9d1b066c4d8c96bff1c97cdcd243905b8c02324b434c962553a1f1b58886df92`; interpreter SHA-256 `d23fa2c326127c9590d097603f105d69e68774968f46246fc7a8a80103600765`; `requirements.txt` SHA-256 `214f6c32c628df1eb2bbb1979b3bae8147ceaf338e68959dd58d82394b9be010` |
| Compiler | `Vyper 0.4.3+commit.bff19ea2`; CreditEngine source pragma governs `codesize`; no `-O` override |
| EVM harness | Titanoboa from the validation environment above; local ephemeral deployment only |
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

The original measurement protocol was committed as `d44ab68`. After the
reviewer-fix revision added an explicit Stability Pool exclusion, the same
protocol was rerun against the source hash above. That accepted follow-up run
completed with `1 passed, 3 warnings in 114.40s`. All warnings were pytest
already-imported assertion-rewrite warnings for Hypothesis and Boa; no test was
skipped, xfailed, or deselected.
The accepted harness counts only PriceDesk frames whose calldata selector is
exactly `getUsdValue(address,uint256,bool)`.

### Raw observations

All values are local Boa gas estimates. Each bracket contains all seven
recorded top-level calls.

| Positions | Path | Seven observations | Median | PriceDesk calls per observation |
| ---: | --- | --- | ---: | ---: |
| 1 | priced | `[37782, 37782, 37782, 37782, 37782, 37782, 37782]` | 37,782 | 1 |
| 1 | zero-amount containment | `[21977, 21977, 21977, 21977, 21977, 21977, 21977]` | 21,977 | 0 |
| 2 | priced | `[56944, 56944, 56944, 56944, 56944, 56944, 56944]` | 56,944 | 2 |
| 2 | zero-amount containment | `[25438, 25438, 25438, 25438, 25438, 25438, 25438]` | 25,438 | 0 |
| 4 | priced | `[95268, 95268, 95268, 95268, 95268, 95268, 95268]` | 95,268 | 4 |
| 4 | zero-amount containment | `[32360, 32360, 32360, 32360, 32360, 32360, 32360]` | 32,360 | 0 |
| 8 | priced | `[171916, 171916, 171916, 171916, 171916, 171916, 171916]` | 171,916 | 8 |
| 8 | zero-amount containment | `[46204, 46204, 46204, 46204, 46204, 46204, 46204]` | 46,204 | 0 |
| 16 | priced | `[327010, 327010, 327010, 327010, 327010, 327010, 327010]` | 327,010 | 16 |
| 16 | zero-amount containment | `[75690, 75690, 75690, 75690, 75690, 75690, 75690]` | 75,690 | 0 |
| 50 | priced | `[983912, 983912, 983912, 983912, 983912, 983912, 983912]` | 983,912 | 50 |
| 50 | zero-amount containment | `[198758, 198758, 198758, 198758, 198758, 198758, 198758]` | 198,758 | 0 |

### Marginal calculations

| Positions | Priced median | Zero median | Priced minus zero | Added positions | Priced marginal | Priced per added position | Zero marginal | Zero per added position |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 37,782 | 21,977 | 15,805 | — | — | — | — | — |
| 2 | 56,944 | 25,438 | 31,506 | 1 | 19,162 | 19,162.000 | 3,461 | 3,461.000 |
| 4 | 95,268 | 32,360 | 62,908 | 2 | 38,324 | 19,162.000 | 6,922 | 3,461.000 |
| 8 | 171,916 | 46,204 | 125,712 | 4 | 76,648 | 19,162.000 | 13,844 | 3,461.000 |
| 16 | 327,010 | 75,690 | 251,320 | 8 | 155,094 | 19,386.750 | 29,486 | 3,685.750 |
| 50 | 983,912 | 198,758 | 785,154 | 34 | 656,902 | 19,320.647 | 123,068 | 3,619.647 |

The one-, two-, four-, and eight-position cells have exact marginal slopes of
19,162 gas per priced position and 3,461 per contained zero position in this
harness. The later cells cross synthetic-vault boundaries, so their marginal
figures also include additional Ledger/VaultBook/vault-call overhead. At the
fixture-derived 50-position ceiling, the containment path remains below the
priced comparator, but this is not a production gas limit or a release
approval.
