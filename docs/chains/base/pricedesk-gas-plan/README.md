# PriceDesk gas-budget packet — current reading path

Start with [the implementation handoff](../pricedesk-gas-implementation.md) and
[PR #232 review closure](../pricedesk-gas-review-232.md) for current status,
validation, configuration boundaries and remaining work. The implementation is
published in [PR #232](https://github.com/Ripe-Foundation/ripe-protocol/pull/232)
on `codex/pricedesk-configurable-gas`, stacked on PR #231.

The original approved scope was contract implementation and affected tests,
using conditional ordinary quote checks, eager feed/snapshot/admission checks,
immutable defaults with source overrides, and the Teller-to-PriceDesk Curve relay.
Those design choices are settled. The later C01–C26 and R01–R16 handoffs additionally authorize
workflow coverage and complete applicable validation; their directions supersede
the original selected-tests-only limit. Base floors remain 1.5M/1.5M for the approved
implementation/rehearsal scope; production qualification and any lower-floor
owner decision remain separate.

[Deferred qualification](follow-up-qualification.md) and the
[Pool-1 supplement](legacy-pool-claim-qualification.md) preserve release requirements.
Production budgets, RPC-estimator D01, deployment and activation remain separately
authorized work. No document in this archive authorizes those operations now.

## Historical implementation directions and provenance

[Revision-7 prompt](updated-prompt.md), [setup reference](implementation-reference.md)
and [review resolutions](review-resolutions.md) preserve the original execution
scope and decisions. Earlier revisions under `evidence/` are historical background,
not instructions to rerun operations. This is the canonical tracked packet; any
older untracked checkout copy is superseded.

For portable historical commands, set `RIPE_REPOSITORY` to the original checkout,
`PRICEDESK_WORKTREE` to the designated PR worktree and `PRICEDESK_PYTHON` to the
pinned environment's Python executable. Optional integration references use
`RIPE_WEB_REPOSITORY` and `UNDERSCORE_REPOSITORY`. The archived Anvil probe uses
`ANVIL` or `anvil` on PATH and `PRICEDESK_REVIEW_OUTPUT` for its generated JSON.
The handoff defines that writable output directory for caches/logs/XML as well;
it contains generated outputs, not required plugin or report inputs. Verify the
worktree branch before running any command.

Published archival copies were edited on 2026-09-19 to sanitize local paths
and repair 24 links to the corresponding archived versions or shared supplements.
The 2026-09-20 follow-up quotes worktree paths, parameterizes the historical smoke
output, and clarifies revision-7 scope; current qualification material gains the
route-inventory and D01 templates.
They are not byte-for-byte originals. [Packet inventory](packet-hashes.json)
contains current published sizes/SHA-256 in `files` and the reviewed-head original
published inventory in `original_published_inventory`; upstream capture hashes
inside evidence describe those earlier captures. Copy the listed files plus the
inventory, preserving relative paths and excluding unlisted session files.
