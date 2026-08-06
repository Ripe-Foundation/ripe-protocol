# Track 2: Stock Token Transferability Probe

**Status:** Draft for owner review

**Prepared:** 23 July 2026

**Planning baseline:** `1bb8bd5b8837a06c818c3fb9e7b599b5dd29f2b1`

## Fresh-agent instruction

Treat this document as the task contract. Build the smallest chain-agnostic probe that can behaviorally prove whether an exact Robinhood Stock Token can enter and leave a third-party smart contract.

Use a dedicated branch or worktree named `rh-track-2-stock-transfer`. Do not edit `docs/chains/rh-summary.md` or files owned by the other Robinhood tracks. Do not add the probe to production migrations or treat a successful transfer as approval to list the asset. Commit deliverables to the track branch with clear messages; never push directly to or merge into the shared `rh` or `master` branch. The owner reviews and integrates the work.

## Worktree bootstrap

The owner must commit the approved track briefs to the `rh` integration branch before kickoff. The fresh agent is responsible for creating its own worktree:

1. Start from `/Users/wigglez/dev/ripe-protocol`.
2. Verify that the integration worktree is clean, `rh` resolves to the approved integration commit, and this brief exists in that commit.
3. Confirm that branch `rh-track-2-stock-transfer` and path `/Users/wigglez/dev/ripe-protocol-track-2-stock-transfer` do not already exist. If either exists, stop and ask the owner; do not reuse, delete, reset, or overwrite it.
4. Create the isolated worktree from the committed `rh` baseline:

   ```bash
   git -C /Users/wigglez/dev/ripe-protocol worktree add \
     -b rh-track-2-stock-transfer \
     /Users/wigglez/dev/ripe-protocol-track-2-stock-transfer \
     rh
   ```

5. Verify the new worktree's branch, commit, and clean status. Record the full starting commit in the deliverables.
6. Run every subsequent command and make every edit inside `/Users/wigglez/dev/ripe-protocol-track-2-stock-transfer`.

Do not modify or commit from the integration worktree. Leave the track worktree and branch in place for owner review; do not remove or merge them yourself.

Never broadcast a transaction, use a signing key, move a token, or spend funds without explicit owner approval of the network, contracts, account, amount, and transaction sequence.

## Objective

Produce reproducible fork and live-chain evidence for this narrow question:

> Can the exact candidate Stock Token be transferred from an eligible holder into a newly deployed third-party contract and then transferred back out under its current implementation and administrative state?

The result is a technical transferability finding. It is not proof of legal eligibility, beneficial ownership, redemption rights, future transferability, liquidation liquidity, or protection from pause, blocklist, upgrade, forced transfer, or administrative burn.

[Robinhood's current public disclosure](https://robinhood.com/rhj/stocktokens/) describes Stock Tokens as Jersey-issued debt instruments that may not be offered, sold, or delivered to or for U.S. persons and that are restricted in additional jurisdictions. Whether a sender, recipient, entity, acquisition path, or transaction is eligible is an owner-and-counsel determination. The agent must never make, imply, or certify that determination and must re-check the current disclosure during Phase A.

## Controlling constraints

- Follow [`../rh-summary.md`](../rh-summary.md) and the selected Hightop Notes architecture.
- Use the exact proposed launch token contract, not a generic mock, wrapper, ticker match, or UI identifier.
- Verify proxy, implementation, decimals, administrative controls, and current pause/blocklist behavior from primary sources and onchain state.
- The probe must be generic and reusable for other ERC-20 candidates.
- Keep the deployed amount deliberately minimal.
- Leave no probe-held token balance or unnecessary allowance after the successful round trip.
- A failed transaction is evidence only after configuration, balances, approvals, revert data, and the correct token address are verified.

## Required inputs

Before live execution, the owner must approve:

- the target network;
- the canonical Stock Token address;
- the amount to test;
- a funded sender whose legal and contractual eligibility has been determined outside this track by the owner and counsel;
- the approved recipient, including any owner/counsel eligibility determination that applies;
- how that sender obtained or will obtain the test amount;
- the signing/broadcast mechanism; and
- the maximum acceptable gas spend.

The agent must not advise on, recommend, broker, or arrange acquisition of a Stock Token. The owner must approve whether the test amount already exists in the sender wallet, is withdrawn through an authorized Robinhood flow, or is acquired through an approved onchain path.

If any input is missing, the agent may research technical candidates but must stop before live deployment, acquisition, or transfer. Treat sender eligibility and the approved acquisition path as likely Phase-D blockers and surface them in the Phase-A preflight report.

## Required repository reading

Read and verify:

- `docs/chains/rh-summary.md`
- `contracts/vaults/SimpleErc20.vy`
- `contracts/vaults/RebaseErc20.vy`
- `contracts/vaults/modules/BasicVault.vy`
- `contracts/vaults/modules/SharesVault.vy`
- `contracts/mock/MockBlacklistErc20.vy`
- relevant vault and ERC-20 tests under `tests/vaults/` and `tests/tokens/`
- `scripts/migrate.py` and repository deployment helpers
- the Stock Token sections of `/Users/wigglez/dev/hightop-notes/random/hood/hood-chain-executive-summary.md`

If the local Hightop Notes checkout is unavailable, use the [GitHub copy](https://github.com/mickhagen/hightop-notes/blob/main/random/hood/hood-chain-executive-summary.md). If neither source is accessible, stop rather than silently skipping the required architecture.

Record the actual starting commit. If relevant repository conventions changed after the planning baseline, adapt the file locations without broadening the probe.

## Phase A: Select and verify the target

- [ ] Identify one candidate Stock Token from current official Robinhood sources.
- [ ] Record the network, canonical proxy address, current implementation address, symbol, name, decimals, and code hash.
- [ ] Identify the official evidence tying the address to the intended Stock Token.
- [ ] Read current pause, blocklist/denylist, upgrade, forced-transfer, forced-redemption, and administrative-burn controls where observable.
- [ ] Confirm that the proposed sender has enough token and native gas balance without exposing private credentials.
- [ ] Record whether the owner and counsel have supplied an eligibility determination and whether the owner has approved the acquisition/provenance path. Do not assess either question yourself.
- [ ] Confirm whether the sender, probe address, recipient, or operator is blocked where a public view is available.
- [ ] Confirm whether the token uses nonstandard return values, fees, hooks, rebasing, or transfer restrictions relevant to the probe.

Write the preflight record to:

`docs/chains/rh/stock-token-transferability-evidence.md`

Do not rely on an address copied only from the July 2026 research snapshot.

### Approval gate

Present the verified target, sender/recipient requirements, eligibility and acquisition-path status, amount, expected transactions, and gas estimate to the owner. Stop until the exact live test is approved.

## Phase B: Implement the reusable probe

Add a small test-only Vyper contract under:

`contracts/testing/StockTokenTransferProbe.vy`

The repository currently places non-production contracts under `contracts/mock/`, but this probe is intentionally separated because it may be deployed on a live network. Confirm that ABI export, explorer verification, packaging, and production migration tooling do not automatically sweep `contracts/testing/` into production artifacts.

The contract should:

- be explicitly controlled by a configured owner;
- bind one configured token address at deployment so it cannot be redirected to an unapproved test target;
- accept a token deposit through `transferFrom`;
- verify the received balance delta;
- transfer an exact token amount back to an approved recipient;
- expose no arbitrary external-call surface;
- emit events sufficient to reconstruct the round trip; and
- provide a safe recovery path limited to the owner for accidentally retained ERC-20 balances.

Do not add pausing, upgradeability, protocol roles, vault accounting, pricing, borrowing, or liquidation behavior.

Add:

- focused local tests under `tests/probes/`;
- a narrowly scoped deployment/execution script under `scripts/probes/`; and
- operator-facing dry-run output showing the target, sender, amount, expected balance changes, network, and whether broadcasting is disabled.

The script must fail closed when the chain ID, target token, sender, amount, or expected probe bytecode does not match its approved input.

## Phase C: Validate locally and on a fork

Test at minimum:

- successful `approve` → `deposit` → `withdraw`;
- exact balance reconciliation for sender, probe, and recipient;
- owner-only withdrawal and recovery;
- zero amount;
- insufficient allowance;
- insufficient balance;
- wrong token;
- unauthorized withdrawal;
- token returning false or reverting;
- paused-token and blocked-address behavior with mocks; and
- post-run zero probe balance and cleared/reduced allowance.

Then run the exact transaction sequence against a fork at a pinned block using the canonical token. Record any fork limitations, including holder impersonation or state mutation that cannot be reproduced live.

Passing mocks or a fork is not the final transferability proof.

## Phase D: Execute the approved live probe

Before every broadcast:

- print and verify chain ID, RPC target, token, probe bytecode hash, sender, recipient, amount, nonce, and maximum fee;
- simulate or estimate the transaction;
- obtain explicit owner approval for the final transaction set; and
- ensure logs do not expose secrets.

Execute:

1. deploy the probe;
2. approve only the minimal amount;
3. deposit the candidate token into the probe;
4. verify the exact probe balance;
5. withdraw the exact amount to the approved recipient;
6. verify final balances;
7. clear any remaining allowance where possible; and
8. confirm that the probe holds no token balance.

Stop immediately on an unexpected address, chain ID, balance delta, revert, proxy change, pause, blocklist result, or fee estimate.

## Evidence requirements

Update `docs/chains/rh/stock-token-transferability-evidence.md` with:

- retrieval and execution dates;
- pinned repository commit;
- network and chain ID;
- token proxy and implementation addresses;
- probe address and deployed bytecode hash;
- sender and recipient public addresses;
- amount and decimals;
- fork block and results;
- live transaction hashes and block numbers;
- pre- and post-balances;
- approval/allowance cleanup;
- decoded events and revert data, if any;
- current administrative-control observations;
- limitations of the result; and
- a clear `passed`, `failed`, or `inconclusive` conclusion.

Do not record private keys, seed phrases, API secrets, or sensitive identity/KYC material.

## Stop conditions

Stop and involve the owner if:

- the canonical token address is ambiguous;
- the token or network changes between preflight and execution;
- the owner and counsel have not determined sender/recipient eligibility or the owner has not approved how the test amount is obtained;
- no approved funded holder is available;
- live execution requires a new legal, KYC, custody, or counterparty decision;
- the probe or sender is blocklisted;
- the token is paused or upgraded unexpectedly;
- a transaction would move more than the approved amount;
- testing would require privileged issuer actions;
- a failure cannot be distinguished from RPC, funding, allowance, or configuration error; or
- the proposed work expands into vault selection, collateral listing, oracle configuration, borrowing, or liquidation.

## Completion criteria

This track is complete only when:

- the probe and its tests are reusable and narrowly scoped;
- the exact candidate token and administrative state are documented;
- the fork sequence is reproducible;
- an owner-approved live round trip has a complete evidence record, or the precise blocker is documented;
- no funds or allowances are unintentionally left behind; and
- the conclusion states exactly what the result proves and does not prove.

Do not mark any checkbox in `rh-summary.md` yourself. In the completion report, identify the exact checklist items that are eligible for owner review and closure.
