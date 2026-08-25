"""Repository hygiene checks for portable, reviewable tracked evidence."""

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN_LOCAL_PROVENANCE = (
    "/" + "Users/",
    "Wig" + "glez-MacStudio",
    "<oai-" + "mem-citation>",
)


def _tracked_paths():
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
    )
    return tuple(
        ROOT / os.fsdecode(raw_path)
        for raw_path in result.stdout.split(b"\0")
        if raw_path
    )


def test_repository_text_does_not_embed_local_user_or_host_provenance():
    offenders = []
    for path in _tracked_paths():
        contents = path.read_bytes()
        for forbidden in FORBIDDEN_LOCAL_PROVENANCE:
            if forbidden.encode() in contents:
                offenders.append((path.relative_to(ROOT).as_posix(), forbidden))

    assert offenders == []


def test_repository_does_not_track_podcast_audio():
    assert [path for path in _tracked_paths() if path.suffix.lower() == ".m4a"] == []
