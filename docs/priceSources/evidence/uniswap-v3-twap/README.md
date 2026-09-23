# Preserved implementation evidence

`fresh-11d3bd30.json` is the unchanged final-head capture reviewed by agents A,
B and C: block 58915768, 10 qualified / 2 expected rejected / 0 unverified /
0 failed. Required tests compare its four recorded hashes to Git revision
`11d3bd30d6a51d98c0d8eb5052a672c8c5a8aa51`; this is historical evidence, not the
active replay fixture.

The nine Phase 1 logs preserve the original codesize baseline and each §3.1–3.8
20-case measurement. `sha256.json` binds the bytes of all archived files. The
intermediate source trees were not committed separately, so these logs do
not make each intermediate checkpoint independently rebuildable. No source
snapshots were reconstructed or represented as contemporaneous artifacts.
The final Phase 1 tree remains reproducible from commit `8a9b90ec`.

See the [review response](../../uniswap-v3-twap-review-response.md) for subsequent
source changes, current gas evidence and the durable final-head PR attachment.

`reviewed-source-delta.log` measures the unchanged `11d3bd30` contract with the
new separate callback/source meters. `followup-gas.log` is the complete
67-case required snapshot-gas lane after desk reuse, with all 46 V3 gas cases.
`followup-gas-model.json` identifies its source/model content and environment.
Both source-child delta measurements are 18000; the callback-denominated delta
is separately 9115.

The archive check reads commit `11d3bd30` with `git show`. PR #229 must be
merged with a merge commit, never squashed or rebased, or the required
`twap-tooling` job fails on master; the test names this condition when it fails.
