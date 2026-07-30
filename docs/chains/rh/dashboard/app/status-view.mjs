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
