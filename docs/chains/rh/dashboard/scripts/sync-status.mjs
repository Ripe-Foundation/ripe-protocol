import { createHash } from "node:crypto";
import { spawn } from "node:child_process";
import {
  mkdir,
  readFile,
  realpath,
  rename,
  writeFile,
} from "node:fs/promises";
import {
  basename,
  dirname,
  isAbsolute,
  relative,
  resolve,
  sep,
} from "node:path";
import { fileURLToPath } from "node:url";
import YAML from "yaml";

const here = dirname(fileURLToPath(import.meta.url));
const repositoryRoot = resolve(here, "../../../../..");
const sourcePath = resolve(here, "../../status.yaml");
const decisionRegisterPath = resolve(here, "../../decision-register.md");
const outputPath = resolve(here, "../app/status.generated.json");
const temporaryPath = `${outputPath}.tmp`;
const handoffRoutePath = resolve(here, "../app/handoff/[slug]");
const handoffOutputPath = resolve(handoffRoutePath, "handoff.generated.json");
const handoffTemporaryPath = `${handoffOutputPath}.tmp`;
const gitExecutable = "/usr/bin/git";
const exactCommitPattern = /^[a-f0-9]{40}$/;
const exactObjectPattern = /^[a-f0-9]{40}(?:[a-f0-9]{24})?$/;
const exactSha256Pattern = /^[a-f0-9]{64}$/;
const assumeUnchangedFlag = 0x8000n;
const skipWorktreeFlag = 0x40000000n;

function sanitizedGitEnvironment() {
  return {
    GIT_ASKPASS: "/usr/bin/false",
    GIT_CONFIG_GLOBAL: "/dev/null",
    GIT_CONFIG_NOSYSTEM: "1",
    GIT_CONFIG_SYSTEM: "/dev/null",
    GIT_OPTIONAL_LOCKS: "0",
    GIT_TERMINAL_PROMPT: "0",
    LANG: "C",
    LC_ALL: "C",
    PATH: "/usr/bin:/bin:/usr/sbin:/sbin",
  };
}

async function runGit(
  repository,
  arguments_,
  failureMessage,
  { allowedExitCodes = [0], input } = {},
) {
  return await new Promise((resolvePromise, rejectPromise) => {
    const child = spawn(
      gitExecutable,
      ["--no-optional-locks", "-C", repository, ...arguments_],
      {
        cwd: repository,
        env: sanitizedGitEnvironment(),
        stdio: ["pipe", "pipe", "pipe"],
      },
    );
    const stdout = [];
    const stderr = [];
    let settled = false;

    child.stdout.on("data", (chunk) => stdout.push(chunk));
    child.stderr.on("data", (chunk) => stderr.push(chunk));
    child.on("error", (error) => {
      if (!settled) {
        settled = true;
        rejectPromise(new Error(failureMessage, { cause: error }));
      }
    });
    child.on("close", (code, signal) => {
      if (settled) return;
      settled = true;
      const result = {
        code,
        signal,
        stderr: Buffer.concat(stderr),
        stdout: Buffer.concat(stdout),
      };
      if (!allowedExitCodes.includes(code)) {
        const detail = result.stderr.toString("utf8").trim();
        rejectPromise(
          new Error(
            detail.length > 0 ? `${failureMessage}: ${detail}` : failureMessage,
          ),
        );
        return;
      }
      resolvePromise(result);
    });

    child.stdin.end(input);
  });
}

async function gitOutput(repository, arguments_, failureMessage) {
  const { stdout } = await runGit(repository, arguments_, failureMessage);
  return stdout.toString("utf8").trim();
}

async function resolveRepositoryContext(repository) {
  let intendedRoot;
  try {
    intendedRoot = await realpath(repository);
  } catch (error) {
    throw new Error("Could not resolve the intended repository root", {
      cause: error,
    });
  }

  const [reportedRoot, insideWorktree, bareRepository, gitDirectory, commonDirectory, indexPath] =
    await Promise.all([
      gitOutput(
        intendedRoot,
        ["rev-parse", "--path-format=absolute", "--show-toplevel"],
        "Git could not report the repository root",
      ),
      gitOutput(
        intendedRoot,
        ["rev-parse", "--is-inside-work-tree"],
        "Git could not confirm the intended worktree",
      ),
      gitOutput(
        intendedRoot,
        ["rev-parse", "--is-bare-repository"],
        "Git could not classify the intended repository",
      ),
      gitOutput(
        intendedRoot,
        ["rev-parse", "--path-format=absolute", "--git-dir"],
        "Git could not report the repository metadata directory",
      ),
      gitOutput(
        intendedRoot,
        ["rev-parse", "--path-format=absolute", "--git-common-dir"],
        "Git could not report the common repository metadata directory",
      ),
      gitOutput(
        intendedRoot,
        ["rev-parse", "--path-format=absolute", "--git-path", "index"],
        "Git could not report the intended repository index",
      ),
    ]);

  let reportedRootReal;
  let gitDirectoryReal;
  let commonDirectoryReal;
  let indexPathReal;
  try {
    [reportedRootReal, gitDirectoryReal, commonDirectoryReal, indexPathReal] =
      await Promise.all([
        realpath(reportedRoot),
        realpath(gitDirectory),
        realpath(commonDirectory),
        realpath(indexPath),
      ]);
  } catch (error) {
    throw new Error("Git reported an unresolved repository or index path", {
      cause: error,
    });
  }

  if (
    reportedRootReal !== intendedRoot ||
    insideWorktree !== "true" ||
    bareRepository !== "false"
  ) {
    throw new Error(
      "The intended repository root does not match Git's reported worktree",
    );
  }

  if (
    dirname(indexPathReal) !== gitDirectoryReal ||
    !(
      gitDirectoryReal === commonDirectoryReal ||
      gitDirectoryReal.startsWith(`${commonDirectoryReal}${sep}`)
    )
  ) {
    throw new Error("Git reported an alternate or inconsistent index");
  }

  return intendedRoot;
}

async function resolveStatusSource(repository, statusSourcePath) {
  let sourceRealPath;
  try {
    sourceRealPath = await realpath(statusSourcePath);
  } catch (error) {
    throw new Error("Could not resolve the exact status source path", {
      cause: error,
    });
  }
  const relativeSourcePath = relative(repository, sourceRealPath);

  if (
    relativeSourcePath.length === 0 ||
    isAbsolute(relativeSourcePath) ||
    relativeSourcePath === ".." ||
    relativeSourcePath.startsWith(`..${sep}`)
  ) {
    throw new Error("Status source must be inside the repository");
  }

  return { relativeSourcePath, sourceRealPath };
}

function parseIndexEntries(indexOutput, relativeSourcePath) {
  return indexOutput
    .toString("utf8")
    .split("\0")
    .filter((record) => record.length > 0)
    .map((record) => {
      const match = record.match(
        /^([0-7]{6}) ([a-f0-9]{40}(?:[a-f0-9]{24})?) ([0-3])\t([\s\S]+)$/,
      );
      if (!match || match[4] !== relativeSourcePath) {
        throw new Error("Git returned an inconsistent status source index entry");
      }
      return {
        mode: match[1],
        blob: match[2],
        stage: Number.parseInt(match[3], 10),
      };
    });
}

async function inspectStatusSourceIndex(repository, relativeSourcePath) {
  const [stageResult, tagResult, debugOutput] = await Promise.all([
    runGit(
      repository,
      ["ls-files", "--stage", "-z", "--", relativeSourcePath],
      "Git could not inspect the status source index entries",
    ),
    runGit(
      repository,
      ["ls-files", "-v", "-z", "--", relativeSourcePath],
      "Git could not inspect the status source index flags",
    ),
    gitOutput(
      repository,
      ["ls-files", "--debug", "--", relativeSourcePath],
      "Git could not inspect the status source index metadata",
    ),
  ]);
  const entries = parseIndexEntries(stageResult.stdout, relativeSourcePath);

  if (entries.some((entry) => entry.stage !== 0)) {
    throw new Error("Status source is involved in an unmerged state");
  }
  if (entries.length > 1) {
    throw new Error("Status source has multiple index entries");
  }

  const tagRecords = tagResult.stdout
    .toString("utf8")
    .split("\0")
    .filter((record) => record.length > 0);
  const flagMatches = [...debugOutput.matchAll(/flags: ([0-9a-fA-F]+)/g)];

  if (entries.length === 0) {
    if (tagRecords.length !== 0 || flagMatches.length !== 0) {
      throw new Error("Git returned an inconsistent untracked index state");
    }
    return null;
  }

  if (
    tagRecords.length !== 1 ||
    !tagRecords[0].endsWith(` ${relativeSourcePath}`) ||
    flagMatches.length !== 1
  ) {
    throw new Error("Git returned an inconsistent status source index state");
  }

  const tag = tagRecords[0][0];
  const flags = BigInt(`0x${flagMatches[0][1]}`);
  if (tag.toUpperCase() === "S" || (flags & skipWorktreeFlag) !== 0n) {
    throw new Error("Status source index entry has skip-worktree set");
  }
  if (tag === tag.toLowerCase() || (flags & assumeUnchangedFlag) !== 0n) {
    throw new Error("Status source index entry has assume-unchanged set");
  }
  if (tag !== "H") {
    throw new Error("Git returned an unsupported status source index state");
  }

  return entries[0];
}

async function gitBlobForBytes(repository, sourceBytes) {
  const { stdout } = await runGit(
    repository,
    ["hash-object", "--stdin"],
    "Git could not hash the exact status source bytes",
    { input: sourceBytes },
  );
  const blob = stdout.toString("utf8").trim();
  if (!exactObjectPattern.test(blob)) {
    throw new Error("Git returned an invalid status source blob");
  }
  return blob;
}

async function proveProposedAuthorityCommit(
  repository,
  relativeSourcePath,
  sourceBytes,
  proposedAuthorityCommit,
) {
  if (!exactCommitPattern.test(proposedAuthorityCommit)) {
    throw new Error(
      "Committed status source lacks an exact status authority commit",
    );
  }

  const resolvedCommit = await gitOutput(
    repository,
    ["rev-parse", "--verify", `${proposedAuthorityCommit}^{commit}`],
    "Could not verify the proposed status authority commit",
  );
  if (resolvedCommit !== proposedAuthorityCommit) {
    throw new Error("Status authority commit resolution is ambiguous");
  }

  const [sourceBlob, authorityBlob] = await Promise.all([
    gitBlobForBytes(repository, sourceBytes),
    gitOutput(
      repository,
      ["rev-parse", "--verify", `${proposedAuthorityCommit}:${relativeSourcePath}`],
      "Could not resolve the status source in the authority commit",
    ),
  ]);
  if (!exactObjectPattern.test(authorityBlob) || authorityBlob !== sourceBlob) {
    throw new Error(
      "Proposed status authority commit does not contain the exact source bytes",
    );
  }

  return { authorityBlob, sourceBlob };
}

export async function verifyProposedStatusAuthority(
  repository,
  statusSourcePath,
  sourceBytes,
  proposedAuthorityCommit,
) {
  const intendedRoot = await resolveRepositoryContext(repository);
  const { relativeSourcePath } = await resolveStatusSource(
    intendedRoot,
    statusSourcePath,
  );
  return await proveProposedAuthorityCommit(
    intendedRoot,
    relativeSourcePath,
    sourceBytes,
    proposedAuthorityCommit,
  );
}

export async function deriveStatusAuthority(repository, statusSourcePath) {
  const intendedRoot = await resolveRepositoryContext(repository);
  const { relativeSourcePath, sourceRealPath } = await resolveStatusSource(
    intendedRoot,
    statusSourcePath,
  );

  let sourceBytes;
  try {
    sourceBytes = await readFile(sourceRealPath);
  } catch (error) {
    throw new Error("Could not read the exact status source bytes", {
      cause: error,
    });
  }

  const statusFileSha256 = createHash("sha256")
    .update(sourceBytes)
    .digest("hex");
  if (!exactSha256Pattern.test(statusFileSha256)) {
    throw new Error("Could not derive the exact status source SHA-256");
  }

  const buildSourceCommit = await gitOutput(
    intendedRoot,
    ["rev-parse", "--verify", "HEAD^{commit}"],
    "Could not resolve HEAD",
  );
  if (!exactCommitPattern.test(buildSourceCommit)) {
    throw new Error("Could not derive the exact build source commit");
  }

  const originCommit = await gitOutput(
    intendedRoot,
    ["rev-parse", "--verify", "refs/remotes/origin/rh^{commit}"],
    "Could not resolve cached origin/rh",
  );
  if (!exactCommitPattern.test(originCommit)) {
    throw new Error("Could not derive cached origin/rh");
  }

  const [worktreeStatus, sourceStatus, indexEntry, sourceBlob] =
    await Promise.all([
      runGit(
        intendedRoot,
        ["status", "--porcelain=v2", "-z", "--untracked-files=all"],
        "Git could not classify the repository worktree",
      ),
      runGit(
        intendedRoot,
        [
          "status",
          "--porcelain=v2",
          "-z",
          "--untracked-files=all",
          "--",
          relativeSourcePath,
        ],
        "Git could not classify the status source",
      ),
      inspectStatusSourceIndex(intendedRoot, relativeSourcePath),
      gitBlobForBytes(intendedRoot, sourceBytes),
    ]);

  const worktreeClean = worktreeStatus.stdout.length === 0;
  const sourceChanged = sourceStatus.stdout.length > 0;
  const sourceTracked = indexEntry !== null;

  if (sourceTracked && !sourceChanged && worktreeClean) {
    if (sourceBlob !== indexEntry.blob) {
      throw new Error(
        "Exact status source bytes do not match the stage-zero index blob",
      );
    }

    const headBlob = await gitOutput(
      intendedRoot,
      ["rev-parse", "--verify", `HEAD:${relativeSourcePath}`],
      "Committed status source lacks a matching HEAD blob",
    );
    if (!exactObjectPattern.test(headBlob) || headBlob !== indexEntry.blob) {
      throw new Error(
        "Status source stage-zero index blob does not match HEAD",
      );
    }

    const statusAuthorityCommit = await gitOutput(
      intendedRoot,
      ["log", "-1", "--format=%H", "--follow", "--", relativeSourcePath],
      "Could not derive the status authority commit",
    );
    if (!exactCommitPattern.test(statusAuthorityCommit)) {
      throw new Error(
        "Committed status source lacks an exact status authority commit",
      );
    }
    const { authorityBlob } = await proveProposedAuthorityCommit(
      intendedRoot,
      relativeSourcePath,
      sourceBytes,
      statusAuthorityCommit,
    );
    if (
      authorityBlob !== indexEntry.blob ||
      authorityBlob !== headBlob ||
      authorityBlob !== sourceBlob
    ) {
      throw new Error(
        "Committed status source authority blobs are internally inconsistent",
      );
    }

    return {
      state: "committed",
      statusAuthorityCommit,
      statusAuthorityBaseCommit: null,
      statusFileSha256,
      buildSourceCommit,
      originCommit,
      buildWorktreeClean: true,
    };
  }

  if (sourceChanged && !worktreeClean) {
    if (!exactCommitPattern.test(buildSourceCommit)) {
      throw new Error(
        "Uncommitted status candidate lacks an exact base commit",
      );
    }
    if (!exactSha256Pattern.test(statusFileSha256)) {
      throw new Error("Uncommitted status candidate lacks an exact source hash");
    }

    return {
      state: "uncommitted_candidate",
      statusAuthorityCommit: null,
      statusAuthorityBaseCommit: buildSourceCommit,
      statusFileSha256,
      buildSourceCommit,
      originCommit,
      buildWorktreeClean: false,
    };
  }

  throw new Error(
    "Git could not unambiguously classify the status source authority state",
  );
}

export async function generateDashboard() {

const [source, decisionRegister] = await Promise.all([
  readFile(sourcePath, "utf8"),
  readFile(decisionRegisterPath, "utf8"),
]);
const parsed = YAML.parse(source);

if (
  !parsed?.snapshot?.program_subject_commit ||
  !Array.isArray(parsed?.workstreams)
) {
  throw new Error("status.yaml is missing its snapshot or workstream inventory");
}

const ids = parsed.workstreams.map((workstream) => workstream.id);
if (new Set(ids).size !== ids.length) {
  throw new Error("status.yaml contains duplicate workstream IDs");
}

const audienceCollections = [
  ["workstream", parsed.workstreams],
  ["critical-path step", parsed.critical_path],
  ["hard gate", parsed.hard_gates],
];

for (const [kind, entries] of audienceCollections) {
  for (const entry of entries) {
    for (const field of ["plain_language_scope", "why_it_matters"]) {
      if (typeof entry[field] !== "string" || entry[field].trim().length < 40) {
        throw new Error(
          `${kind} ${entry.id ?? entry.order} requires a substantive ${field}`,
        );
      }
    }
  }
}

for (const step of parsed.critical_path) {
  if (
    typeof step.internal_reference !== "string" ||
    step.internal_reference.trim().length === 0
  ) {
    throw new Error(
      `critical-path step ${step.order} requires an internal_reference`,
    );
  }
}

if (
  !Array.isArray(parsed.glossary) ||
  parsed.glossary.length === 0 ||
  parsed.glossary.some(
    (entry) =>
      typeof entry.term !== "string" ||
      typeof entry.meaning !== "string" ||
      entry.meaning.trim().length < 30,
  )
) {
  throw new Error("status.yaml requires a substantive audience glossary");
}

const canonicalDecisions = [...decisionRegister.matchAll(/^### (RH-D\d{3}) — (.+)$/gm)]
  .map((match) => ({ id: match[1], title: match[2].trim() }));
const mirroredDecisions = parsed.decisions.map(({ id, title }) => ({ id, title }));

if (
  canonicalDecisions.length === 0 ||
  JSON.stringify(canonicalDecisions) !== JSON.stringify(mirroredDecisions)
) {
  throw new Error(
    "status.yaml decisions must exactly mirror the canonical decision register IDs and titles",
  );
}

const subjectCommit = parsed.snapshot.program_subject_commit;

if (
  parsed.snapshot.subject_in_origin_history !== "build_derived" ||
  parsed.snapshot.origin_commits_after_subject !== "build_derived" ||
  parsed.snapshot.build_worktree_clean !== "build_derived" ||
  parsed.publication.status_authority_state !== "build_derived" ||
  parsed.publication.status_authority_commit !== "build_derived" ||
  parsed.publication.status_authority_base_commit !== "build_derived" ||
  parsed.publication.status_file_sha256 !== "build_derived"
) {
  throw new Error(
    "snapshot trust and status authority fields must be declared build_derived, never hand-authored",
  );
}

const statusAuthority = await deriveStatusAuthority(repositoryRoot, sourcePath);
const {
  buildSourceCommit,
  buildWorktreeClean,
  originCommit,
  state: statusAuthorityState,
  statusAuthorityBaseCommit,
  statusAuthorityCommit,
  statusFileSha256: sourceHash,
} = statusAuthority;

const ancestryResult = await runGit(
  repositoryRoot,
  ["merge-base", "--is-ancestor", subjectCommit, originCommit],
  "Could not verify whether the program subject is in origin/rh history",
  { allowedExitCodes: [0, 1] },
);
const subjectInOriginHistory = ancestryResult.code === 0;

let originCommitsAfterSubject = null;
if (subjectInOriginHistory) {
  const driftCountOutput = await gitOutput(
    repositoryRoot,
    ["rev-list", "--count", `${subjectCommit}..${originCommit}`],
    "Could not derive origin/rh commits after the program subject",
  );
  originCommitsAfterSubject = Number.parseInt(driftCountOutput, 10);

  if (
    !Number.isInteger(originCommitsAfterSubject) ||
    originCommitsAfterSubject < 0
  ) {
    throw new Error(
      "Could not derive origin/rh commits after the program subject",
    );
  }
}

const generated = {
  ...parsed,
  snapshot: {
    ...parsed.snapshot,
    subject_in_origin_history: subjectInOriginHistory,
    origin_commits_after_subject: originCommitsAfterSubject,
    build_worktree_clean: buildWorktreeClean,
  },
  publication: {
    ...parsed.publication,
    build_source_commit: buildSourceCommit,
    status_authority_state: statusAuthorityState,
    status_authority_commit: statusAuthorityCommit,
    status_authority_base_commit: statusAuthorityBaseCommit,
    status_file_sha256: sourceHash,
  },
  _generated: {
    source: "../status.yaml",
    source_sha256: sourceHash,
    build_source_commit: buildSourceCommit,
    status_authority_state: statusAuthorityState,
    status_authority_commit: statusAuthorityCommit,
    status_authority_base_commit: statusAuthorityBaseCommit,
    origin_rh_commit: originCommit,
    subject_in_origin_history: subjectInOriginHistory,
    origin_commits_after_subject: originCommitsAfterSubject,
    build_worktree_clean: buildWorktreeClean,
  },
};

await writeFile(temporaryPath, `${JSON.stringify(generated, null, 2)}\n`);
await rename(temporaryPath, outputPath);

const readingDocuments = Object.values(parsed.reading_paths)
  .flat()
  .filter((value) => typeof value === "string" && value.startsWith("docs/"));
const publishedDocuments = new Map();

await mkdir(handoffRoutePath, { recursive: true });

for (const documentPath of readingDocuments) {
  const publishedName = basename(documentPath);
  const prior = publishedDocuments.get(publishedName);
  const priorPath = prior?.source;
  if (priorPath && priorPath !== documentPath) {
    throw new Error(
      `Reading-path basename collision: ${priorPath} and ${documentPath}`,
    );
  }
  if (!prior) {
    publishedDocuments.set(publishedName, {
      source: documentPath,
      content: await readFile(resolve(repositoryRoot, documentPath), "utf8"),
    });
  }
}

await writeFile(
  handoffTemporaryPath,
  `${JSON.stringify(Object.fromEntries(publishedDocuments), null, 2)}\n`,
);
await rename(handoffTemporaryPath, handoffOutputPath);

console.log(
  `Synced ${parsed.workstreams.length} workstreams, ${parsed.decisions.length} decisions, and ${publishedDocuments.size} handoff documents (${sourceHash.slice(0, 12)}).`,
);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await generateDashboard();
}
