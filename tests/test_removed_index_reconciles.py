"""`docs/simplification/REMOVED.md` must agree with itself and with the tree.

This exists because the same class of defect appeared three times across two
independent reviews, and each time it was found by a person reading rather than
by anything running:

- the index header said 171 removed paths while the section counts summed to 172;
- a section header declared a count that did not match the bullets beneath it;
- the index listed `contracts/mock/MockSGreenPrice.vy` as removed while a
  separate document argued for retaining it, and later while it was in fact
  restored to the tree.

None of those is a runtime defect. They matter because this branch removes ~3M
lines and asks to be merged on the strength of documented evidence; an index that
contradicts itself devalues every other count in the package.

Three properties, all cheap and offline:

1. every `## Section (N)` header's N equals the number of bulleted paths
   under it;
2. the `**N files removed.**` header equals the sum of those sections;
3. **every listed path is actually absent from the working tree.** This is the
   one that catches a restore: putting a file back without delisting it fails
   here, which is exactly what happened with `MockSGreenPrice.vy`.

What this deliberately does not check is the reverse direction — that everything
absent is listed. The branch removes far more than it enumerates individually
(79 deployment manifests are listed, but the removed step-manifest corpus is
described in prose), and a total-coverage assertion would be a census of the kind
this branch exists to remove.
"""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REMOVED_MD = ROOT / "docs" / "simplification" / "REMOVED.md"

SECTION_RE = re.compile(r"^## (?P<name>.+?) \((?P<count>\d+)\)\s*$")
BULLET_RE = re.compile(r"^- `(?P<path>[^`]+)`")
TOTAL_RE = re.compile(r"\*\*(?P<total>[\d,]+) files removed\.\*\*")


def _sections():
    """[(name, declared_count, [paths])] for each counted section, in order."""
    out = []
    current = None
    for line in REMOVED_MD.read_text().splitlines():
        header = SECTION_RE.match(line)
        if header:
            current = (header["name"], int(header["count"]), [])
            out.append(current)
            continue
        if current is None:
            continue
        bullet = BULLET_RE.match(line)
        if bullet:
            current[2].append(bullet["path"])
    return out


def test_every_section_count_matches_its_own_bullets():
    mismatches = [
        f"{name}: header says {declared}, {len(paths)} bullets"
        for name, declared, paths in _sections()
        if declared != len(paths)
    ]
    assert not mismatches, "REMOVED.md section counts disagree: " + "; ".join(
        mismatches
    )


def test_declared_total_matches_the_sum_of_sections():
    sections = _sections()
    assert sections, "REMOVED.md has no counted sections; the format changed"

    match = TOTAL_RE.search(REMOVED_MD.read_text())
    assert match, "REMOVED.md has no '**N files removed.**' total"

    declared_total = int(match["total"].replace(",", ""))
    summed = sum(len(paths) for _, _, paths in sections)
    assert declared_total == summed, (
        f"REMOVED.md says {declared_total} files removed, but its "
        f"{len(sections)} sections list {summed}"
    )


def test_every_listed_path_is_absent_from_the_tree():
    still_here = sorted(
        path
        for _, _, paths in _sections()
        for path in paths
        if (ROOT / path).exists()
    )
    assert not still_here, (
        "REMOVED.md lists paths that are present in the tree: "
        f"{still_here}. Either the file was restored and this index was not "
        "updated, or it was never removed."
    )
