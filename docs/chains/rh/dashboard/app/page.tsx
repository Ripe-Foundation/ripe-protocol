import statusJson from "./status.generated.json";
import {
  deriveOriginDrift,
  derivePublicationLifecycle,
  deriveSourceSnapshotSeal,
} from "./status-view.mjs";

type MaturityState =
  | "complete"
  | "partial"
  | "gated"
  | "not_started"
  | "not_applicable";

type DocumentLink = {
  label: string;
  path: string;
  availability?: string;
};

type Workstream = {
  id: string;
  name: string;
  group: string;
  plain_language_scope: string;
  why_it_matters: string;
  current_phase: string;
  implementation_state: string;
  integration_state: string;
  review_state: string;
  owner_decision_state: string;
  remaining_blockers: string[];
  deployment_release_state: string;
  exact_next_action: string;
  authority: string;
  docs: DocumentLink[];
};

type Decision = {
  id: string;
  title: string;
  status: string;
  summary: string;
  source: string;
  source_availability?: "private_handoff";
  source_note?: string;
};

type Deadline = {
  id: string;
  label: string;
  due_at: string;
  kind: "scheduled_review" | "hard_expiry";
  plain_language_scope: string;
  why_it_matters: string;
  owner: string;
  consequence: string;
  source: string;
};

type HardGate = {
  id: string;
  label: string;
  plain_language_scope: string;
  why_it_matters: string;
  state: string;
  effect: string;
};

type CriticalStep = {
  order: number;
  label: string;
  internal_reference: string;
  plain_language_scope: string;
  why_it_matters: string;
  detail: string;
  state: MaturityState;
  owner_gate: string;
};

type H04Decision = {
  id: string;
  title: string;
  state: string;
};

type H03Blocker = {
  id: string;
  state: string;
  implementation_predicate: string;
  remaining: string;
};

type AcceptedResidual = {
  id: string;
  state: string;
  statement: string;
  release_condition?: string;
};

type DashboardGovernance = {
  authority_status: string;
  ratified_at: string;
  ratified_against_commit: string;
  repository_placement: string;
  placement_reason: string;
  dependency_scope: string;
  dependency_owner: string;
  dependency_policy: string;
  dependency_audit: {
    environment: {
      node: string;
      npm: string;
    };
    remediation: {
      direct_pins: string;
      lockfile_scope: string;
      result: string;
    };
    production_only: {
      observed_at: string;
      command: string;
      total: number;
      critical: number;
      high: number;
      moderate: number;
      low: number;
    };
    full_tree: {
      observed_at: string;
      command: string;
      input: string;
      observation_source: string;
      total: number;
      critical: number;
      high: number;
      moderate: number;
      low: number;
      scope_note: string;
    };
    interpretation: string;
    disposition: string;
    h01_effect: string;
  };
  ci_policy: string;
  ci_observation: {
    observed_at: string;
    source: string;
    enabled: boolean;
    allowed_actions: string;
    repository_requires_sha_pinning: boolean;
    interpretation: string;
  };
  hosting: {
    publisher: string;
    role: string;
    access_model: string;
    fallback: string;
    revisit_trigger: string;
  };
};

type OwnerPriorityLane = {
  id: string;
  subject: string;
  state: string;
  blocker_effect: string;
  instruction: string;
  reopen_condition: string;
};

type OwnerPriorityOverlay = {
  effective_at: string;
  authority: string;
  scope: string;
  active_focus: string;
  parked_lanes: OwnerPriorityLane[];
  preserved_boundaries: string[];
};

type DeploymentOwnerStep = {
  order: number;
  label: string;
  owns: string;
  output: string;
  boundary: string;
};

type DeploymentOwner = {
  readiness: string;
  authority_boundary: string;
  sequence: DeploymentOwnerStep[];
  parallel_inputs: Array<{
    name: string;
    start_effect: string;
    gate_effect: string;
  }>;
};

type StatusData = {
  counts: {
    workstreams: number;
    rh_d_decisions: number;
    h03_blockers: number;
    h04_rows: number;
    h04_approved_operative: number;
    h04_retired_non_operative: number;
    h04_open: number;
    binding_schedules: number;
    hard_gates: number;
    handoff_documents: number;
    parked_lanes: number;
    live_actions: number;
  };
  snapshot: {
    title: string;
    as_of: string;
    timezone: string;
    branch: string;
    program_subject_commit: string;
    program_subject_tree: string;
    subject_in_origin_history: boolean;
    origin_commits_after_subject: number | null;
    build_worktree_clean: boolean;
    posture: string;
    hero_lead: string;
    hero_emphasis: string;
    launch_readiness: string;
    live_actions_completed: number;
  };
  publication: {
    dashboard_url: string;
    access_boundary: string;
    refresh_state: string;
    live_currentness: string;
    last_observed_access: string;
    last_observed_live_version: number;
    last_observed_at: string;
    build_source_commit: string;
    status_authority_state: "committed" | "uncommitted_candidate";
    status_authority_commit: string | null;
    status_authority_base_commit: string | null;
    status_file_sha256: string;
    source_lifecycle:
      | "candidate"
      | "committed_feature"
      | "integrated_rh"
      | "later_descendant";
    authority_in_origin_history: boolean | null;
    origin_commits_after_authority: number | null;
  };
  dashboard_governance: DashboardGovernance;
  owner_priority_overlay: OwnerPriorityOverlay;
  deployment_owner: DeploymentOwner;
  overall: {
    bottom_line: string;
    architecture: { status: MaturityState; note: string };
    engineering_foundation: { status: MaturityState; note: string };
    launch_implementation: { status: MaturityState; note: string };
    testnet: { status: MaturityState; note: string };
    production: { status: MaturityState; note: string };
  };
  glossary: Array<{ term: string; meaning: string }>;
  authorization_boundaries: string[];
  accepted_residuals: AcceptedResidual[];
  h04_decisions: {
    schema_v2_integrated: boolean;
    defaults_render_ready: boolean;
    approved_ids: string[];
    open_ids: string[];
    retired_ids: string[];
    unresolved_binding_classes: string[];
    binding_schedule_count: number;
    implementation_file_surface: string[];
    rows: H04Decision[];
  };
  h03_blockers: H03Blocker[];
  critical_path: CriticalStep[];
  workstreams: Workstream[];
  decisions: Decision[];
  deadlines: Deadline[];
  hard_gates: HardGate[];
  reading_paths: {
    human_10_minute: string[];
    human_45_minute: string[];
    agent_bootstrap: string[];
  };
  _generated: {
    source: string;
    source_sha256: string;
    build_source_commit: string;
    status_authority_state: "committed" | "uncommitted_candidate";
    status_authority_commit: string | null;
    status_authority_base_commit: string | null;
    source_lifecycle: string;
    authority_in_origin_history: boolean | null;
    origin_commits_after_authority: number | null;
  };
};

const status = statusJson as StatusData;

const stateLabels: Record<MaturityState, string> = {
  complete: "Complete",
  partial: "Partial",
  gated: "Gated",
  not_started: "Not started",
  not_applicable: "N/A",
};

const stateSymbols: Record<MaturityState, string> = {
  complete: "●",
  partial: "◐",
  gated: "◆",
  not_started: "○",
  not_applicable: "—",
};

const githubRoot =
  "https://github.com/Ripe-Foundation/ripe-protocol/blob/rh/";

function prettyState(value: string) {
  return value
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function shortSha(value: string) {
  return value.slice(0, 8);
}

function compactDate(value: string) {
  const [year, month, day] = value.split("-");

  if (!year || !month || !day) {
    return value;
  }

  return `${day}·${month}·${year.slice(-2)}`;
}

function sourceHref(document: DocumentLink) {
  if (document.availability === "feature_worktree_only") {
    return null;
  }

  return `${githubRoot}${document.path}`;
}

function decisionHref(decision: Decision) {
  if (decision.source_availability === "private_handoff") {
    return handoffHref(decision.source);
  }

  return `${githubRoot}${decision.source}`;
}

const readingLabels: Record<string, string> = {
  "AGENT-HANDOFF.md": "Open the agent bootstrap",
  "START-HERE.md": "Open START-HERE",
  "decision-register.md": "Open the decision register",
  "minimal-contract-change-reassessment.md": "Read minimum-change reassessment",
  "rh-summary.md": "Read the architecture summary",
  "robinhood-deployment-support-specification.md":
    "Read the deployment specification",
  "robinhood-deployment-validation-plan.md": "Read the validation plan",
  "status.yaml": "Inspect the status ledger",
};

function handoffHref(path: string) {
  const filename = path.split("/").at(-1);
  return filename ? `/handoff/${encodeURIComponent(filename)}` : null;
}

function readingLabel(path: string) {
  const filename = path.split("/").at(-1);
  return (filename && readingLabels[filename]) || path;
}

function ReadingPath({ paths }: { paths: string[] }) {
  return (
    <ol>
      {paths.map((path) => {
        const href = path.startsWith("docs/") ? handoffHref(path) : null;

        return (
          <li key={path}>
            {href ? (
              <a href={href} target="_blank" rel="noreferrer">
                {readingLabel(path)} <span aria-hidden="true">↗</span>
              </a>
            ) : (
              <span>{path}</span>
            )}
          </li>
        );
      })}
    </ol>
  );
}

function MaturityPill({
  value,
  compact = false,
}: {
  value: MaturityState;
  compact?: boolean;
}) {
  return (
    <span
      className={`maturity maturity--${value}${compact ? " maturity--compact" : ""}`}
      title={stateLabels[value]}
      aria-label={stateLabels[value]}
    >
      <span aria-hidden="true">{stateSymbols[value]}</span>
      {!compact && <span>{stateLabels[value]}</span>}
    </span>
  );
}

function SectionHeading({
  eyebrow,
  title,
  copy,
}: {
  eyebrow: string;
  title: string;
  copy: string;
}) {
  return (
    <div className="section-heading">
      <p className="eyebrow">{eyebrow}</p>
      <h2>{title}</h2>
      <p>{copy}</p>
    </div>
  );
}

export default function Home() {
  const h04OpenDecisionCount = status.h04_decisions.rows.filter(
    (decision) => decision.state === "open",
  ).length;
  const h04ApprovedDecisionCount = status.h04_decisions.rows.filter(
    (decision) => decision.state === "approved",
  ).length;
  const h04RetiredDecisionCount = status.h04_decisions.rows.filter(
    (decision) => decision.state === "retired_non_operative",
  ).length;
  const h03OpenBlockerCount = status.h03_blockers.filter(
    (blocker) => blocker.state === "open",
  ).length;
  const sourceSnapshotSeal = deriveSourceSnapshotSeal(status.snapshot);
  const originDrift = deriveOriginDrift(status.snapshot);
  const publicationLifecycle = derivePublicationLifecycle(status.publication);
  const statusIsCandidate =
    status.publication.status_authority_state === "uncommitted_candidate";

  return (
    <main>
      <header className="topbar">
        <a className="brand" href="#top" aria-label="Ripe Robinhood dashboard">
          <span className="brand-mark" aria-hidden="true">
            R
          </span>
          <span>
            <strong>Ripe × Robinhood</strong>
            <small>Deployment operating picture</small>
          </span>
        </a>
        <nav aria-label="Dashboard sections">
          <a href="#glossary">Terms</a>
          <a href="#maturity">Maturity</a>
          <a href="#ownership">Ownership</a>
          <a href="#priorities">Priorities</a>
          <a href="#path">Critical path</a>
          <a href="#deadlines">Deadlines</a>
          <a href="#governance">Governance</a>
          <a href="#workstreams">Workstreams</a>
          <a href="#decisions">Decisions</a>
          <a href="#onboarding">Ramp up</a>
        </nav>
        <a className="topbar-cta" href="#onboarding">
          Start here <span aria-hidden="true">↘</span>
        </a>
      </header>

      <section className="hero" id="top">
        <div className="hero-grid" aria-hidden="true" />
        <div className="hero-orb hero-orb--one" aria-hidden="true" />
        <div className="hero-orb hero-orb--two" aria-hidden="true" />

        <div className="hero-content">
          <div className="hero-kicker">
            <span className="live-dot" />
            Reconciled operating picture
            <time className="hero-date" dateTime={status.snapshot.as_of}>
              {compactDate(status.snapshot.as_of)}
            </time>
          </div>
          <h1>
            {status.snapshot.hero_lead}
            <span>{status.snapshot.hero_emphasis}</span>
          </h1>
          <p className="hero-copy">{status.overall.bottom_line}</p>
          <div className="hero-actions">
            <a className="button button--primary" href="#path">
              See the critical path <span aria-hidden="true">↓</span>
            </a>
            <a className="button button--ghost" href="#onboarding">
              New here? Ramp up in 10 minutes
            </a>
          </div>
        </div>

        <aside
          className={`seal-card seal-card--${sourceSnapshotSeal.verified ? "verified" : "unverified"}`}
          aria-label="Reviewed source snapshot verification"
        >
          <div className="seal-card__header">
            <span>Reviewed source snapshot</span>
            <span
              className={`seal-state seal-state--${sourceSnapshotSeal.verified ? "verified" : "unverified"}`}
            >
              {sourceSnapshotSeal.label}
            </span>
          </div>
          <p className="seal-limitation">
            Verifies that the reviewed program subject remains in published
            rh history and that this exact dashboard build used a clean
            checkout. It does not mean all workstreams are integrated,
            Robinhood is deployed, or the program is launch-ready.
          </p>
          <div className="seal-branch">
            <span>Branch</span>
            <strong>{status.snapshot.branch}</strong>
          </div>
          <div className="seal-sha">
            <span>Program subject</span>
            <code>{shortSha(status.snapshot.program_subject_commit)}</code>
          </div>
          <div
            className={`drift-state drift-state--${originDrift.current ? "current" : "stale"}`}
            aria-label="Integrated source drift"
          >
            <strong>{originDrift.label}</strong>
            <small>{originDrift.detail}</small>
          </div>
          <div className="seal-checks">
            {sourceSnapshotSeal.checks.map((check) => (
              <div key={check.key}>
                <span
                  className={`check check--${check.verified ? "verified" : "unverified"}`}
                  aria-hidden="true"
                >
                  {check.verified ? "✓" : "!"}
                </span>
                <span>
                  <strong>{check.label}</strong>
                  <small>{check.detail}</small>
                </span>
              </div>
            ))}
          </div>
          <dl className="seal-provenance">
            <div>
              <dt>Build source</dt>
              <dd>{shortSha(status.publication.build_source_commit)}</dd>
            </div>
            <div>
              <dt>Lifecycle</dt>
              <dd>{publicationLifecycle.label}</dd>
            </div>
            <div>
              <dt>Status authority</dt>
              <dd>
                {statusIsCandidate
                  ? "Uncommitted candidate"
                  : status.publication.status_authority_commit}
              </dd>
            </div>
            {statusIsCandidate && (
              <div>
                <dt>Base commit</dt>
                <dd style={{ overflowWrap: "anywhere", textAlign: "right" }}>
                  {status.publication.status_authority_base_commit}
                </dd>
              </div>
            )}
            <div>
              <dt>Status SHA-256</dt>
              <dd style={{ overflowWrap: "anywhere", textAlign: "right" }}>
                {status.publication.status_file_sha256}
              </dd>
            </div>
          </dl>
        </aside>
      </section>

      <section className="metrics" aria-label="Program snapshot">
        <article>
          <span className="metric-value">{status.counts.workstreams}</span>
          <span className="metric-label">mapped workstreams</span>
          <small>each with a named next gate</small>
        </article>
        <article>
          <span className="metric-value">{status.counts.rh_d_decisions}</span>
          <span className="metric-label">RH-D decisions</span>
          <small>one canonical namespace</small>
        </article>
        <article>
          <span className="metric-value">{status.counts.hard_gates}</span>
          <span className="metric-label">hard gates</span>
          <small>each blocks a named downstream action</small>
        </article>
        <article className="metric-alert">
          <span className="metric-value">
            {status.counts.live_actions}
          </span>
          <span className="metric-label">live deployment actions</span>
          <small>testnet and production remain unopened</small>
        </article>
      </section>

      <section className="section path-section" id="ownership">
        <SectionHeading
          eyebrow="Deployment-owner handoff"
          title={status.deployment_owner.readiness}
          copy={status.deployment_owner.authority_boundary}
        />

        <ol className="critical-path owner-sequence">
          {status.deployment_owner.sequence.map((step, index) => (
            <li key={step.order}>
              <div className="path-index">
                <span>{String(step.order).padStart(2, "0")}</span>
                {index < status.deployment_owner.sequence.length - 1 && (
                  <span className="path-line" aria-hidden="true" />
                )}
              </div>
              <article>
                <div className="path-card__top">
                  <div>
                    <h3>{step.label}</h3>
                    <span className="internal-reference">Deployment owner</span>
                  </div>
                </div>
                <p className="path-scope">{step.owns}</p>
                <p className="path-impact">
                  <strong>Required output:</strong> {step.output}
                </p>
                <p className="path-detail">
                  <strong>Boundary:</strong> {step.boundary}
                </p>
              </article>
            </li>
          ))}
        </ol>

        <div className="governance-grid">
          {status.deployment_owner.parallel_inputs.map((input) => (
            <article key={input.name}>
              <span className="governance-index">PARALLEL INPUT</span>
              <h3>{input.name}</h3>
              <p>{prettyState(input.start_effect)}</p>
              <small>{input.gate_effect}</small>
            </article>
          ))}
        </div>
      </section>

      <section className="section governance-section" id="priorities">
        <SectionHeading
          eyebrow="Current owner priorities"
          title={`${status.owner_priority_overlay.parked_lanes.length} lanes are parked and nonblocking.`}
          copy={status.owner_priority_overlay.scope}
        />
        <div className="governance-grid">
          <article>
            <span className="governance-index">ACTIVE FOCUS</span>
            <h3>Advance the non-parked path</h3>
            <p>{status.owner_priority_overlay.active_focus}</p>
          </article>
          <article>
            <span className="governance-index">PRESERVED BOUNDARIES</span>
            <h3>Parking is not technical closure</h3>
            <ul>
              {status.owner_priority_overlay.preserved_boundaries.map(
                (boundary) => <li key={boundary}>{boundary}</li>,
              )}
            </ul>
          </article>
        </div>
        <div className="governance-grid">
          {status.owner_priority_overlay.parked_lanes.map((lane) => (
            <article key={lane.id}>
              <span className="governance-index">
                {lane.id} · {lane.state}
              </span>
              <h3>{lane.subject}</h3>
              <p>{lane.instruction}</p>
              <small>
                <strong>Blocker effect:</strong> {lane.blocker_effect}
                {" · "}
                <strong>Reopen:</strong> {lane.reopen_condition}
              </small>
            </article>
          ))}
        </div>
      </section>

      <section className="section governance-section" id="boundaries">
        <SectionHeading
          eyebrow="Current authority boundary"
          title="Preparation is authorized; deployment is not."
          copy={status.snapshot.launch_readiness}
        />
        <div className="governance-grid">
          <article>
            <span className="governance-index">NO LIVE ACTION</span>
            <h3>What this refresh does not authorize</h3>
            <ul>
              {status.authorization_boundaries.map((boundary) => (
                <li key={boundary}>{boundary}</li>
              ))}
            </ul>
          </article>
          <article>
            <span className="governance-index">ACCEPTED RESIDUALS</span>
            <h3>Known limits remain visible</h3>
            <ul>
              {status.accepted_residuals.map((residual) => (
                <li key={residual.id}>
                  <strong>{residual.id}</strong> · {residual.statement}
                  {residual.release_condition && (
                    <> {residual.release_condition}</>
                  )}
                </li>
              ))}
            </ul>
          </article>
        </div>
      </section>

      <section className="section deadlines-section" id="deadlines">
        <SectionHeading
          eyebrow="Time-bound security gates"
          title="Two dates cannot drift into the background."
          copy="These are controlling H-01 obligations, not project estimates. Each date has a named owner and a concrete stop condition."
        />
        <div className="deadline-grid">
          {status.deadlines.map((deadline) => (
            <article key={deadline.id}>
              <div className="deadline-topline">
                <time dateTime={deadline.due_at}>{deadline.due_at}</time>
                <span>{prettyState(deadline.kind)}</span>
              </div>
              <h3>{deadline.label}</h3>
              <p>{deadline.plain_language_scope}</p>
              <p className="deadline-impact">
                <strong>Why it matters:</strong> {deadline.why_it_matters}
              </p>
              <dl>
                <div>
                  <dt>Owner</dt>
                  <dd>{deadline.owner}</dd>
                </div>
                <div>
                  <dt>If missed</dt>
                  <dd>{deadline.consequence}</dd>
                </div>
              </dl>
              <a
                href={`${githubRoot}${deadline.source}`}
                target="_blank"
                rel="noreferrer"
              >
                Controlling evidence <span aria-hidden="true">↗</span>
              </a>
            </article>
          ))}
        </div>
      </section>

      <section className="section governance-section" id="governance">
        <SectionHeading
          eyebrow="Handoff governance"
          title="Useful now, without becoming protocol authority."
          copy={`The dashboard stays close to its source of truth while its dependency and hosting boundaries remain explicit. Policy status: ${prettyState(status.dashboard_governance.authority_status)} on ${status.dashboard_governance.ratified_at}, against ${shortSha(status.dashboard_governance.ratified_against_commit)}.`}
        />
        <div className="governance-grid">
          <article>
            <span className="governance-index">RH-D018</span>
            <h3>One repository, separate dependency scope</h3>
            <p>{status.dashboard_governance.placement_reason}</p>
            <dl>
              <div>
                <dt>Application path</dt>
                <dd>
                  <code>
                    {status.dashboard_governance.repository_placement}
                  </code>
                </dd>
              </div>
              <div>
                <dt>Dependency owner</dt>
                <dd>{status.dashboard_governance.dependency_owner}</dd>
              </div>
              <div>
                <dt>CI observed</dt>
                <dd>
                  {status.dashboard_governance.ci_observation.enabled
                    ? "Enabled"
                    : "Disabled"}{" "}
                  · {status.dashboard_governance.ci_observation.allowed_actions}
                  {" "}actions allowed
                </dd>
              </div>
            </dl>
            <p className="governance-rule">
              {status.dashboard_governance.dependency_policy}
            </p>
            <p className="governance-warning">
              <strong>Dashboard dependency review remains open.</strong>{" "}
              {
                status.dashboard_governance.dependency_audit.remediation
                  .direct_pins
              }{" "}
              Production-only audit:{" "}
              {status.dashboard_governance.dependency_audit.production_only.total}{" "}
              total,{" "}
              {status.dashboard_governance.dependency_audit.production_only.high}{" "}
              high. Full tooling-inclusive tree:{" "}
              {status.dashboard_governance.dependency_audit.full_tree.total}{" "}
              total (
              {status.dashboard_governance.dependency_audit.full_tree.high} high,{" "}
              {status.dashboard_governance.dependency_audit.full_tree.moderate}{" "}
              moderate,{" "}
              {status.dashboard_governance.dependency_audit.full_tree.low} low,{" "}
              {status.dashboard_governance.dependency_audit.full_tree.critical}{" "}
              critical), using{" "}
              {status.dashboard_governance.dependency_audit.environment.node}{" "}
              and npm{" "}
              {status.dashboard_governance.dependency_audit.environment.npm}.{" "}
              {status.dashboard_governance.dependency_audit.interpretation}
            </p>
            <small>{status.dashboard_governance.ci_policy}</small>
            <small>
              {status.dashboard_governance.ci_observation.interpretation}{" "}
              Observed {status.dashboard_governance.ci_observation.observed_at}.
            </small>
          </article>
          <article>
            <span className="governance-index">RH-D019</span>
            <h3>Temporary private mirror, complete repository fallback</h3>
            <p>{status.dashboard_governance.hosting.role}</p>
            <dl>
              <div>
                <dt>Publisher</dt>
                <dd>{status.dashboard_governance.hosting.publisher}</dd>
              </div>
              <div>
                <dt>Access</dt>
                <dd>{status.dashboard_governance.hosting.access_model}</dd>
              </div>
            </dl>
            <p className="governance-rule">
              {status.dashboard_governance.hosting.fallback}
            </p>
            <small>{status.dashboard_governance.hosting.revisit_trigger}</small>
          </article>
        </div>
      </section>

      <section className="section glossary-section" id="glossary">
        <SectionHeading
          eyebrow="00 · Decode the workflow"
          title="Meaning first. Internal reference second."
          copy="These terms connect the dashboard to engineering briefs and review records. The explanations below control how a new reader should interpret them."
        />
        <dl className="glossary-grid">
          {status.glossary.map((entry) => (
            <div key={entry.term}>
              <dt>{entry.term}</dt>
              <dd>{entry.meaning}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section className="section maturity-section" id="maturity">
        <SectionHeading
          eyebrow="01 · Read progress correctly"
          title="One program. Six explicit lifecycle fields."
          copy="Implementation, integration, review, owner decision, and deployment or release are deliberately separate. No row is allowed to collapse them into one completion claim."
        />

        <div className="maturity-table-wrap">
          <table className="maturity-table">
            <thead>
              <tr>
                <th scope="col">Workstream</th>
                <th scope="col">Phase</th>
                <th scope="col">Implementation</th>
                <th scope="col">Integration</th>
                <th scope="col">Review</th>
                <th scope="col">Owner decision</th>
                <th scope="col">Deployment / release</th>
              </tr>
            </thead>
            <tbody>
              {status.workstreams.map((workstream) => (
                <tr key={workstream.id}>
                  <th scope="row">
                    <strong>{workstream.plain_language_scope}</strong>
                    <span>
                      {workstream.id} · {workstream.name}
                    </span>
                    <small className="workstream-impact">
                      <b>Why it matters:</b> {workstream.why_it_matters}
                    </small>
                  </th>
                  <td><small>{workstream.current_phase}</small></td>
                  <td><small>{workstream.implementation_state}</small></td>
                  <td><small>{workstream.integration_state}</small></td>
                  <td><small>{workstream.review_state}</small></td>
                  <td><small>{workstream.owner_decision_state}</small></td>
                  <td><small>{workstream.deployment_release_state}</small></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="truth-strip">
          <span className="truth-strip__mark" aria-hidden="true">
            !
          </span>
          <p>
            <strong>Do not turn this into one percentage.</strong> A reviewed
            Phase A evidence package and an authorized production deployment are
            not comparable units. The matrix is the progress model.
          </p>
        </div>
      </section>

      <section className="section path-section" id="path">
        <SectionHeading
          eyebrow="02 · The critical path"
          title="What has to happen next"
          copy="This is the shortest honest route from the current branch to an authorized release. Each handoff names the gate that controls it."
        />

        <ol className="critical-path">
          {status.critical_path.map((step, index) => (
            <li key={step.order}>
              <div className="path-index">
                <span>{String(step.order).padStart(2, "0")}</span>
                {index < status.critical_path.length - 1 && (
                  <span className="path-line" aria-hidden="true" />
                )}
              </div>
              <article>
                <div className="path-card__top">
                  <div>
                    <h3>{step.label}</h3>
                    <span className="internal-reference">
                      {step.internal_reference}
                    </span>
                  </div>
                  <MaturityPill value={step.state} />
                </div>
                <p className="path-scope">{step.plain_language_scope}</p>
                <p className="path-impact">
                  <strong>Why it matters:</strong> {step.why_it_matters}
                </p>
                <p className="path-detail">
                  <strong>Current gate:</strong> {step.detail}
                </p>
                <small>
                  <span>Gate owner</span>
                  {step.owner_gate}
                </small>
              </article>
            </li>
          ))}
        </ol>
      </section>

      <section className="section workstreams-section" id="workstreams">
        <SectionHeading
          eyebrow="03 · Workstream radar"
          title="What is true, what is moving, and what is blocked"
          copy="Open any card for the exact authority boundary, blockers, safe next action, and controlling documents."
        />

        <div className="workstream-grid">
          {status.workstreams.map((workstream) => (
            <details className="workstream-card" key={workstream.id}>
              <summary>
                <h3>{workstream.plain_language_scope}</h3>
                <div className="card-id">
                  <small>{workstream.group}</small>
                  <span>{workstream.id}</span>
                </div>
                <p className="card-internal-name">{workstream.name}</p>
                <p className="card-impact">
                  <strong>Why it matters:</strong> {workstream.why_it_matters}
                </p>
                <p>{workstream.exact_next_action}</p>
                <div className="card-footer">
                  <span className="posture">
                    {workstream.current_phase}
                  </span>
                  <span className="expand-label">
                    Full detail <span aria-hidden="true">＋</span>
                  </span>
                </div>
              </summary>
              <div className="workstream-detail">
                <div className="detail-block detail-block--result">
                  <span>Exact next action</span>
                  <p>{workstream.exact_next_action}</p>
                </div>
                <div className="detail-columns">
                  <div className="detail-block">
                    <span>Authority</span>
                    <p>{workstream.authority}</p>
                  </div>
                  <div className="detail-block">
                    <span>Implementation / integration</span>
                    <p>
                      {workstream.implementation_state} ·{" "}
                      {workstream.integration_state}
                    </p>
                  </div>
                </div>
                <div className="detail-block detail-block--gate">
                  <span>Review / owner decision / deployment</span>
                  <p>
                    {workstream.review_state} · {workstream.owner_decision_state}
                    {" "}· {workstream.deployment_release_state}
                  </p>
                </div>
                <div className="detail-columns">
                  <div className="detail-block">
                    <span>Blockers</span>
                    <ul>
                      {workstream.remaining_blockers.map((blocker) => (
                        <li key={blocker}>{blocker}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="detail-block">
                    <span>Current phase</span>
                    <p>{workstream.current_phase}</p>
                  </div>
                </div>
                <div className="source-links">
                  {workstream.docs.map((document) => {
                    const href = sourceHref(document);
                    return href ? (
                      <a
                        href={href}
                        key={document.path}
                        target="_blank"
                        rel="noreferrer"
                      >
                        {document.label} <span aria-hidden="true">↗</span>
                      </a>
                    ) : (
                      <span key={document.path}>
                        {document.label} · worktree only
                      </span>
                    );
                  })}
                </div>
              </div>
            </details>
          ))}
        </div>
      </section>

      <section className="section decisions-section" id="owner-surface">
        <SectionHeading
          eyebrow="04 · Current owner surface"
          title={`${status.h04_decisions.rows.length} H-04 rows: ${h04ApprovedDecisionCount} approved, ${h04RetiredDecisionCount} retired, ${h04OpenDecisionCount} open.`}
          copy="Schema v2 is integrated, but unresolved machine bindings, Defaults rendering, configuration readiness, and downstream release gates remain explicit."
        />
        <div className="decision-layout">
          <div>
            <div className="truth-strip">
              <span className="truth-strip__mark" aria-hidden="true">!</span>
              <p>
                <strong>H-04 schema v2 is integrated; Defaults rendering is not ready.</strong>{" "}
                Approved operative decisions: {status.h04_decisions.approved_ids.join(", ")}.
                Retired non-operative IDs: {status.h04_decisions.retired_ids.join(", ")}.
                Unresolved binding classes:{" "}
                {status.h04_decisions.unresolved_binding_classes.join(", ")}.
              </p>
            </div>
            <div className="decision-list">
              {status.h04_decisions.rows.map((decision) => (
                <article key={decision.id}>
                  <div>
                    <span>{decision.id}</span>
                    <span className="decision-status">
                      {prettyState(decision.state)}
                    </span>
                  </div>
                  <h3>{decision.title}</h3>
                </article>
              ))}
            </div>
            <div className="detail-block detail-block--gate">
              <span>Integrated implementation file surface</span>
              <ul>
                {status.h04_decisions.implementation_file_surface.map((path) => (
                  <li key={path}><code>{path}</code></li>
                ))}
              </ul>
            </div>
          </div>

          <aside className="gate-panel">
            <div className="gate-panel__heading">
              <p className="eyebrow">H-03 typed blocker ledger</p>
              <h2>{h03OpenBlockerCount} blockers remain open</h2>
              <p>Implementation predicates can be satisfied while the blocker remains open.</p>
            </div>
            <div className="gate-list">
              {status.h03_blockers.map((blocker, index) => (
                <article key={blocker.id}>
                  <span className="gate-number">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <div>
                    <h3>{blocker.id}</h3>
                    <span>
                      Implementation predicate:{" "}
                      {prettyState(blocker.implementation_predicate)}
                    </span>
                    <p>{blocker.remaining}</p>
                  </div>
                  <span className="gate-open">{blocker.state}</span>
                </article>
              ))}
            </div>
          </aside>
        </div>
      </section>

      <section className="section decisions-section" id="decisions">
        <div className="decision-layout">
          <div>
            <SectionHeading
              eyebrow="05 · Program decisions"
              title="One canonical decision namespace"
              copy="Every RH-D identifier and title mirrors the canonical decision register. Source records still control scope, and an approved direction does not open the next phase."
            />
            <div className="decision-list">
              {status.decisions.map((decision) => (
                <article key={decision.id}>
                  <div>
                    <span>{decision.id}</span>
                    <span className="decision-status">
                      {prettyState(decision.status)}
                    </span>
                  </div>
                  <h3>{decision.title}</h3>
                  <p>{decision.summary}</p>
                  <a
                    href={decisionHref(decision) ?? undefined}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Controlling record <span aria-hidden="true">↗</span>
                  </a>
                  {decision.source_note && (
                    <small className="decision-source-note">
                      {decision.source_note}
                    </small>
                  )}
                </article>
              ))}
            </div>
          </div>

          <aside className="gate-panel">
            <div className="gate-panel__heading">
              <p className="eyebrow">Hard stops</p>
              <h2>Open gates</h2>
              <p>
                These are not backlog suggestions. Each one blocks a named
                downstream action.
              </p>
            </div>
            <div className="gate-list">
              {status.hard_gates.map((gate, index) => (
                <article key={gate.id}>
                  <span className="gate-number">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <div>
                    <h3>{gate.label}</h3>
                    <span>{gate.id}</span>
                    <p>{gate.plain_language_scope}</p>
                    <p className="gate-impact">
                      <strong>Why it matters:</strong> {gate.why_it_matters}
                    </p>
                    <p className="gate-effect">{gate.effect}</p>
                  </div>
                  <span className="gate-open">{gate.state}</span>
                </article>
              ))}
            </div>
          </aside>
        </div>
      </section>

      <section className="section onboarding-section" id="onboarding">
        <SectionHeading
          eyebrow="06 · Fast onboarding"
          title="Choose the depth you need"
          copy="Humans and agents start from the same status authority, then branch into the amount of context their assignment requires."
        />

        <div className="reading-grid">
          <article className="reading-card reading-card--accent">
            <span className="reading-time">10 min</span>
            <p className="eyebrow">Human orientation</p>
            <h3>Get the operating picture</h3>
            <ReadingPath paths={status.reading_paths.human_10_minute} />
            <p>
              Enough to understand what is integrated, what is blocked, and why
              “done” is not one state.
            </p>
          </article>

          <article className="reading-card">
            <span className="reading-time">45 min</span>
            <p className="eyebrow">Engineering context</p>
            <h3>Understand the full plan</h3>
            <ReadingPath paths={status.reading_paths.human_45_minute} />
            <p>
              Enough to discuss architecture, sequencing, and review boundaries.
            </p>
          </article>

          <article className="reading-card">
            <span className="reading-time">Agent</span>
            <p className="eyebrow">Cold bootstrap</p>
            <h3>Seal authority before acting</h3>
            <ReadingPath paths={status.reading_paths.agent_bootstrap} />
            <p>
              The agent must distinguish integrated truth from mutable worktree
              observations before editing.
            </p>
          </article>
        </div>

        <div className="handoff-contract">
          <div>
            <p className="eyebrow">The handoff contract</p>
            <h3>Every new assignment should answer seven questions first.</h3>
          </div>
          <ol>
            <li>
              <span>01</span>What exact integration commit controls?
            </li>
            <li>
              <span>02</span>Which document is current authority?
            </li>
            <li>
              <span>03</span>What is integrated versus feature-only?
            </li>
            <li>
              <span>04</span>What exact phase is authorized?
            </li>
            <li>
              <span>05</span>Which files are owned?
            </li>
            <li>
              <span>06</span>What is the next safe action?
            </li>
            <li>
              <span>07</span>What condition forces a stop?
            </li>
          </ol>
        </div>
      </section>

      <footer>
        <div className="footer-brand">
          <span className="brand-mark" aria-hidden="true">
            R
          </span>
          <span>
            <strong>Robinhood deployment operating picture</strong>
            <small>Generated from docs/chains/rh/status.yaml</small>
          </span>
        </div>
        <p>
          Subject {shortSha(status.snapshot.program_subject_commit)} · build{" "}
          {shortSha(status.publication.build_source_commit)} · status authority{" "}
          {statusIsCandidate
            ? "uncommitted candidate"
            : status.publication.status_authority_commit}
          {statusIsCandidate && (
            <> · base {status.publication.status_authority_base_commit}</>
          )}{" "}
          · lifecycle {publicationLifecycle.label}{" "}
          · status {status._generated.source_sha256}
        </p>
        <a href="#top">
          Back to top <span aria-hidden="true">↑</span>
        </a>
      </footer>
    </main>
  );
}
