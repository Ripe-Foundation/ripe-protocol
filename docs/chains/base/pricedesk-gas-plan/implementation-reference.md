# Focused execution reference

The [implementation prompt](updated-prompt.md) controls. This reference adds test/setup commands only; run them as part of the uninterrupted implementation, not after an owner review. No RPC, live inventory, fork sweeps or operational tooling is required for the contract task.

Run from `/Users/wigglez/dev/ripe-protocol-pricedesk-gas`. Its checkout has no `.venv`; use the original repository’s interpreter. Confirm once that `config` and test imports resolve to this worktree (`pytest.ini` adds `.` and `tests`). Use writable task-local Boa/Python/pytest caches; `tests/conftest.py` supports `RIPE_BOA_CACHE_DIR`. Keep temporary caches separate from the persistent checkout.

```sh
/Users/wigglez/dev/ripe-protocol/.venv/bin/python -m pytest -q \
  tests/registries/test_price_desk_isolation.py \
  tests/registries/test_price_desk_token_decimals.py \
  tests/test_price_desk_aggregate_source_count_guard.py \
  tests/test_base_review_safety.py::test_staging_timing_and_price_constructor_bindings \
  tests/test_base_review_safety.py::test_price_desk_current_constructor_bindings \
  tests/priceSources/curve/test_green_ref_pool.py

/Users/wigglez/dev/ripe-protocol/.venv/bin/python -m pytest -q -m gas \
  tests/registries/test_price_desk_gas.py \
  tests/registries/test_price_desk_aggregate_protocol_gas.py
```

Add `test_price_desk_current_constructor_bindings` to exercise the current fixture’s constructor/default bindings before running the command; retain the existing historical test unchanged.

Retain configured addopts; explicit `-m gas` selects the otherwise excluded gas lane. Require nonzero collection. Add the new relay/runtime test module explicitly if tests are placed elsewhere; run directly affected Curve launch-route cases where their behavior changes. Extend `price_desk_aggregate_qualification.py` only as needed for fixture/constructor compatibility. **Do not run the full suite or deployment/fork/artifact-wide lanes.**

Keep `test_price_desk_complete_deployed_runtime_is_below_eip170`; add `test_teller_complete_deployed_runtime_is_below_eip170` to the gas lane. Use the installed repository compiler/build settings and count deployed immutables, not just the runtime template. Restore transaction access-list coldness as well as storage for boundary tests; storage anchors alone are not proof of coldness.

Preserve historical staging assertions; new constructor arguments need additional checks, not edits to executed migrations. Regenerate only affected ABI outputs, preserving unrelated artifacts. Record unrelated baseline failures separately. Fix failures caused by this change, then rerun the affected lane. Expand testing only for a demonstrated dependency impact; do not repeat successful unrelated checks or weaken source-count, budget or batch assertions.
