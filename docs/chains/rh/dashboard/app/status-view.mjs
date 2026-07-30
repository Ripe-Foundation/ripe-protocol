const integrationChecks = [
  {
    key: "subject_in_origin_history",
    label: "Reviewed subject is published",
    verifiedDetail: "program subject is in cached origin/rh history",
    unverifiedDetail:
      "not verified: program subject is absent from cached origin/rh history",
  },
  {
    key: "build_worktree_clean",
    label: "Clean build checkout",
    verifiedDetail: "no tracked or untracked edits at exact build time",
    unverifiedDetail: "not verified: exact build checkout contained local edits",
  },
];

export function deriveSourceSnapshotSeal(snapshot) {
  const checks = integrationChecks.map((check) => {
    const verified = snapshot?.[check.key] === true;

    return {
      key: check.key,
      label: check.label,
      verified,
      detail: verified ? check.verifiedDetail : check.unverifiedDetail,
    };
  });

  const verified = checks.every((check) => check.verified);

  return {
    verified,
    label: verified ? "Verified" : "Unverified",
    checks,
  };
}

export function deriveOriginDrift(snapshot) {
  const count = snapshot?.origin_commits_after_subject;
  const hasVerifiedAncestry = snapshot?.subject_in_origin_history === true;
  const hasValidCount = Number.isInteger(count) && count >= 0;
  const current = hasVerifiedAncestry && hasValidCount && count === 0;

  if (!hasVerifiedAncestry || !hasValidCount) {
    return {
      current: false,
      count: null,
      label: "Freshness unverified",
      detail:
        "The program subject is not verified in cached origin/rh history, so integrated drift cannot be counted.",
    };
  }

  if (current) {
    return {
      current: true,
      count,
      label: "0 integrated changes after subject",
      detail:
        "The operating picture is current with the cached origin/rh integration tip.",
    };
  }

  return {
    current: false,
    count,
    label: `${count} integrated ${count === 1 ? "change" : "changes"} after subject`,
    detail:
      "This operating picture predates integrated changes. Reconcile status.yaml before trusting its workstream rows.",
  };
}

export function derivePublicationLifecycle(publication) {
  const state = publication?.source_lifecycle;

  if (state === "candidate") {
    return {
      state,
      label: "Uncommitted candidate",
      detail:
        "The status bytes are a local candidate based on the recorded base commit.",
    };
  }

  if (state === "committed_feature") {
    return {
      state,
      label: "Committed feature",
      detail:
        "The status bytes have a commit authority, but that commit is not integrated into cached origin/rh.",
    };
  }

  if (state === "integrated_rh") {
    return {
      state,
      label: "Integrated into rh",
      detail:
        "The status authority is the exact cached origin/rh integration tip.",
    };
  }

  if (state === "later_descendant") {
    const count = publication?.origin_commits_after_authority;
    return {
      state,
      label: "Later rh descendant",
      detail: `${count} integrated ${
        count === 1 ? "commit exists" : "commits exist"
      } after the status authority; reconcile current claims before use.`,
    };
  }

  return {
    state: "unknown",
    label: "Lifecycle unverified",
    detail:
      "The generated status does not provide a recognized publication lifecycle.",
  };
}
