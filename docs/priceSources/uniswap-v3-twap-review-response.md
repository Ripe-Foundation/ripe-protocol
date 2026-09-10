# PR #229 reviewer follow-up

2026-09-09. Follow-up to the three reviews of `11d3bd30`. Owner decisions
D1–D20 remain unchanged. The original master merge and implementation commits
are preserved. This follow-up does not deploy or activate any feed.

## Disposition of all review items

| Feedback | Resolution |
| --- | --- |
| A1: null/malformed depth headers | Validate quantity types, encodings, hash type/length and block identity; 24 malformed-field CLI cases produce the normal error without a traceback. RPC response objects are also validated. |
| A2 / B3 / C8: temporary final-head JSON | Preserve the exact `11d3bd30` JSON in repository evidence and verify every recorded hash against that Git revision. The new final-head JSON is attached losslessly to the PR using the tested pack/unpack tool. |
| A3 / C7: depth coverage | Add 24 canonical swaps covering nonzero ticks, tiny liquidity and zero-liquidity gaps in both asset orders and four directions; unequal-decimal/nonzero-spot USD references; explicit negative bitmap boundaries; unavailable history/quote and RPC OLD failures. |
| B1: preceding quote read in governance batch | Add both add/update regressions: standalone rejects, a preceding quote read admits, then the cold route is unavailable. The runbook limits confirmation transactions to confirmation alone or a preceding scale sync for the same asset. |
| B2: unverifiable fixture hash | Replace the old replay fixture. Hash canonical LAB/vector content independently of its filename; bind 25 source, worker, helper, compiled-reference and transitive Vyper dependency files. Required tests reject changed identities. |
| B4 / C8: unused old-model fixture | Delete both superseded replay fixtures; retain only the current selected fixture in the replay directory. Historical reviewed-head evidence lives separately and is clearly labelled. |
| B5: gas output absent from CI | Add `-s` to snapshot-gas and a workflow guard requiring it. |
| B nits: wording and CI link | Correct `cardinality 1801`, identify the math module as already present before remediation, and link the original final-head 17-job CI run alongside the earlier merge run. |
| B nit: transaction gas | Runbook requires estimating the complete intended transaction with a generous buffer and explains EIP-150/inner-stipend starvation. |
| B nit: duplicate desk lookup | Pass the already authenticated canonical desk to the internal scale helper. No public/governance arguments changed. Saves 633 gas in the measured successful price paths; costs 48 runtime bytes. |
| C1: unlike gas meters | Report warm source child, full admission callback, and cold source child separately. Use the measured 18000 source-to-source delta for the conservative ceiling calculation. |
| C2: manually numbered feed slots | Derive base slots and member offsets from compiler storage layout and resolved struct types; continue checking the exact executed-read and address intersections. |
| C3: obsolete cardinality-knob test | Express the longer default window explicitly; assert that it raises the next proposal's requirement while the active feed retains its stored window. |
| C4: add recovery and unchanged identity | Add atomic add-path success and transient rollback. A hostile token lies only to the desk during permissionless first sync; source identity stays 18 decimals. An existing independent feed supplies the actual first-sync prerequisite. |
| C5: precision and extremes | Decimal logs only choose a candidate; exact rational inequalities prove its tick bracket. Bound rounding against an independent rational USD ideal to less than 1000 wei, and prove the old unscaled formula fails that bound. Cover both orders, explicit zero-quote proposal rejection, and scaled modular-accumulator references with a non-unit quote price. |
| C6: conflicting historical appendix | Keep the complete packet under D15, collapse it by default, and label every historical heading as superseded. |
| C8: missing initial header | Add a run-level test proving all 12 cases become unverified. This behavior already existed; no contract or classification change was needed. |
| C9: early identity cancellation | Put the before-unlock cancellation/consumption warning beside the batch instructions. |
| C10: unset scale conversions | Require immediate sync before conversion use; explicitly test price availability versus zero/reverting USD/asset conversions while scale is unset. |
| C11: actual registry qualification | Require cold qualification of the actual registry and every quote fallback before proposal and after registry/priority changes. D4 remains operator policy. |
| C12: checkpoint artifacts | Preserve the nine original Phase 1 logs with a checked SHA-256 manifest. Their limitation is disclosed below. |
| C12: brittle exception handling | Replace catch-and-rethrow with explicit expected admission/rejection cases using `boa.reverts` directly. |
| C12: test fixture clarity | Precision/domain tests create a fresh single graph with explicit quote decimals, price and order. |
| C12: tooling runtime directories | Use the same explicit pytest cache and basetemp paths as sibling jobs; extend the workflow guards. Full history is required for historical evidence hash checks. |

## Clarifications and retained requirements

The old 9115 value was cold source cost minus the **full callback**, whose
cost includes the source and wrapper. It was a valid scoped bound for a
callback-denominated admission ceiling, but it was imprecisely labelled as a
source warm-to-cold delta. The stronger like-for-like measurement is 18000;
the unchanged ceiling is conservative under either calculation.

Stable, caller-independent token metadata cannot itself poison a first sync.
The new hostile-sync regression states its nonstandard metadata behavior and
existing-feed prerequisite explicitly. A pending V3 add alone does not grant
permissionless first-sync eligibility. No production token assumption or
PriceDesk policy was changed.

Unset scale produces unavailable conversions (zero, or `missing token scale`
when requested), rather than an incorrect nonzero USD value. Price reads may
still succeed under the locked zero-scale rule.

The historical appendix remains complete because D15 requires preserving it.
The original per-checkpoint source trees were not committed separately; the
archived logs cannot make those intermediate states independently rebuildable.
No retrospective source snapshot is presented as contemporaneous evidence.
The final Phase 1 commit remains reproducible.

No coauthor identities were supplied, and there was one implementing agent.
The reviews are credited as A/B/C here; no identities or `Co-Authored-By`
trailers were invented and the existing history was not rewritten.

The 3601-write organic ring regression remains in the default suite because
it is required evidence. Test durations and the existing 30-minute CI bounds
remain visible; no required coverage was moved out of the default lane.

## Size and gas

Python 3.12.0, Vyper 0.4.3, Titanoboa 0.2.7, codesize, arm64. These are named
fixture measurements, not a universal bound on arbitrary quote routes.

| Measurement | Reviewed `11d3bd30` | Follow-up |
| --- | ---: | ---: |
| Deployed runtime bytes | 20650 | 20698 |
| Original 20-case matrix: successful forwarded peak | 165782 | 165149 |
| Same matrix: bounded late-failure peak | 174984 | 174351 |
| Same matrix: hostile stipend burn (unsupported route) | 248173 | 248163 |
| Same matrix: direct successful peak | 185738 | 185105 |
| Expanded suite: successful forwarded peak (fat registry, source last) | 183235 | 182602 |
| Source-child warm-to-cold delta | 18000 (newly measured on old source) | 18000 |
| Full callback overhead in standard T11 cases | 8885 | 8885 |
| Admission ceiling | 170000 | 170000 |
| Conservative ceiling plus source delta | 188000 | 188000 |

Targets remain 22500 runtime bytes and 210000 forwarded gas. Hard limits
remain 24576 and 250000. The original per-§3 table remains in the
[test README](../../tests/priceSources/uniswap_v3/README.md).

The enumerated intersection contains source, pool, canonical PriceDesk and
RipeHq addresses; the ten staged feed fields (pool, fee, quoteAsset,
assetIsToken0, assetDecimals, quoteDecimals, baseLiquidity, twapWindow,
maxObservationAge, minLiquidity); PriceDesk.tokenScale[asset]; and
RipeHq.addrInfo[7].addr. Concrete addresses/slots are printed in gas evidence.

Both forbidden quote-preflight batches measured callback 44838 and then an
unavailable cold route consuming 246714 source gas. This lies outside the
standard touch set and remains a documented operator limitation under D20.

## Validation and fresh evidence

Validation results and the final pushed head are recorded in the PR report.
The default TWAP suite passed **434 tests** in 7m39s. Required tooling passed
**49 tests**. Compatibility passed **1436 tests** on the full pre-staging run;
its sole failure was a repository hygiene check opening a deleted fixture
still in the old Git index. After staging the intended deletions, both hygiene
tests passed without a code change, covering all **1437 unique compatibility
tests**. The full command is repeated on the clean final head for the PR report.
The required 3601-write organic ring case took 100.38s locally; it remains in
the default lane and the existing 30-minute CI bounds are retained.

The complete snapshot-gas lane passed **67 tests** (46 V3), with 85 deselected;
the two fuzz campaigns passed **4096 generated cases**; ABI export and check
both matched all **60 artifacts**, and exporter tests passed **9/9**.
The [full gas log](evidence/uniswap-v3-twap/followup-gas.log) and its source/model
identity are preserved with the historical checkpoint logs.
The committed active fixture is `fresh-58962463.json`, block hash
`0x92b524383f45e20ec17338166a3aa665ebd427661514b0319402188b22be7aa6`:
10 qualified, 2 expected rejected, 0 unverified, 0 failed; maximum source gas
160632. Its capture records `11d3bd30` plus a dirty worktree, and its content
hashes match the complete follow-up laboratory. The fixture filename is
excluded from the canonical model hash so committing it does not invalidate
its own provenance. The required artifact tests verify this match.

Fresh inputs use the [official public Robinhood mainnet RPC](https://docs.robinhood.com/chain/add-network-to-wallet/).
This is a fixed-WETH laboratory with local protocol contracts, not production
route qualification. Expected outcomes derive from pinned raw inputs.

After the follow-up commit, repeat the fresh run against that clean final head.
Its complete raw JSON is attached to the PR outside the commit it qualifies,
avoiding a self-referential Git hash. Extract and verify its original bytes:

```sh
gh pr view 229 --repo Ripe-Foundation/ripe-protocol --json body --jq .body > /tmp/twap-pr-report.md
"$RIPE_TWAP_PYTHON" scripts/twap_fork_evidence.py unpack /tmp/twap-pr-report.md --output /tmp/twap-final-head.json
```

The attachment binds the raw JSON SHA-256 and exact Git revision. The original
reviewed-head raw JSON and Phase 1 logs are also preserved under
[evidence/uniswap-v3-twap](evidence/uniswap-v3-twap/README.md).
The owner-required three-reviewer pass must target the same new head.

## Second-round dispositions (reviews of `c17fb8f3`)

The contract is byte-identical to `c17fb8f3`; every §3 measurement, the
committed fixture identity and the PR-attached final-head evidence for that
contract remain valid.

| Feedback | Resolution |
| --- | --- |
| A: brief and follow-up complete; process and deployment obligations restated | No code change. Three-reviewer sign-off on the final head, D4 as operator procedure, real-registry cold T11/T22, D11, D12, D18, the unset 2% depth value and registration remain owner work. |
| A5: no empty-desk short-circuit in `_hasCompatibleScale` | Not changed. A typed staticcall to an empty desk reverts, PriceDesk isolates that as status 2, and an empty desk entry means RipeHq itself is broken. Editing the contract would invalidate the size/gas table and restart review for a fail-closed corner. |
| B P3: null, empty, odd-length or short `eth_call` results escaped the depth CLI's error handling | `decode_result` validates the payload as non-empty even-length hex and translates ABI decoding failures into the normal `No verified depth snapshot` error; twelve CLI cases and a unit test cover it. |
| C1: `git show 11d3bd30` in the archive test breaks under a squash or rebase merge | The test now fails with an explicit message naming the merge-commit requirement; README and evidence README state it. Merge PR #229 with a merge commit. |
| C2: the 18000 delta is a desk-routed net, not the touch set's cost | T11 now also measures a cold call made directly into the source (delta 37956, route-invariant) and asserts ceiling + direct delta <= 210000 on every route; README and spec state both figures and that neither may raise the ceiling. |
| C3: the 59-admit / 60-reject boundary is hardcoded | Retained deliberately: a future PriceDesk or source gas change must re-measure and re-derive, not edit the expectation. |

Validation on this tree (Python 3.12.0, Vyper 0.4.3, Titanoboa 0.2.7, arm64):
default TWAP suite 446 passed; snapshot-gas V3 lane 46 passed with the
direct-call reading asserted on all eight T11 delta samples (direct delta
37956, ceiling + direct delta 207956); required tooling 49 passed; ABI export
tests and shard coverage 35 passed; fuzz 2 passed; `export_abis.py --check`
matched all 60 artifacts. A fresh fixed-WETH run on the committed clean head
is attached to the PR report with the same pack/unpack tool.
