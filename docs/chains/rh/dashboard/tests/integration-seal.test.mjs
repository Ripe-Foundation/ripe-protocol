import assert from "node:assert/strict";
import test from "node:test";

import {
  deriveOriginDrift,
  derivePublicationLifecycle,
  deriveSourceSnapshotSeal,
} from "../app/status-view.mjs";

test("source snapshot seal is verified only when every ledger check is true", () => {
  const verified = deriveSourceSnapshotSeal({
    subject_in_origin_history: true,
    build_worktree_clean: true,
  });

  assert.equal(verified.verified, true);
  assert.equal(verified.label, "Verified");
  assert.deepEqual(
    verified.checks.map((check) => check.verified),
    [true, true],
  );
});

test("source snapshot seal renders a deliberately unverified ledger fixture honestly", () => {
  const unverified = deriveSourceSnapshotSeal({
    subject_in_origin_history: false,
    build_worktree_clean: true,
  });

  assert.equal(unverified.verified, false);
  assert.equal(unverified.label, "Unverified");
  assert.equal(unverified.checks[0].verified, false);
  assert.match(unverified.checks[0].detail, /not verified/i);
  assert.equal(unverified.checks[1].verified, true);
});

test("origin drift reports a current subject only at zero integrated changes", () => {
  const current = deriveOriginDrift({
    subject_in_origin_history: true,
    origin_commits_after_subject: 0,
  });

  assert.equal(current.current, true);
  assert.equal(current.count, 0);
  assert.match(current.label, /^0 integrated changes/);
  assert.match(current.detail, /current with the cached origin\/rh/i);
});

test("origin drift warns on a deliberately stale fixture", () => {
  const stale = deriveOriginDrift({
    subject_in_origin_history: true,
    origin_commits_after_subject: 2,
  });

  assert.equal(stale.current, false);
  assert.equal(stale.count, 2);
  assert.match(stale.label, /^2 integrated changes/);
  assert.match(stale.detail, /reconcile status\.yaml before trusting/i);
});

test("origin drift refuses a count without verified ancestry", () => {
  const unknown = deriveOriginDrift({
    subject_in_origin_history: false,
    origin_commits_after_subject: null,
  });

  assert.equal(unknown.current, false);
  assert.equal(unknown.count, null);
  assert.equal(unknown.label, "Freshness unverified");
});

test("publication lifecycle renders all four authority states truthfully", () => {
  const fixtures = [
    ["candidate", "Uncommitted candidate", null],
    ["committed_feature", "Committed feature", null],
    ["integrated_rh", "Integrated into rh", 0],
    ["later_descendant", "Later rh descendant", 2],
  ];

  for (const [source_lifecycle, label, origin_commits_after_authority] of fixtures) {
    const result = derivePublicationLifecycle({
      source_lifecycle,
      origin_commits_after_authority,
    });
    assert.equal(result.state, source_lifecycle);
    assert.equal(result.label, label);
  }
});
