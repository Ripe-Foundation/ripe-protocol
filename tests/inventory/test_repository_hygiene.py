"""Repository hygiene checks for portable, reviewable tracked evidence."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TEXT_SUFFIXES = frozenset({".json", ".md", ".txt", ".xml", ".yaml", ".yml"})
FORBIDDEN_LOCAL_PROVENANCE = (
    "/" + "Users/",
    "Wig" + "glez-MacStudio",
    "<oai-" + "mem-citation>",
)


def test_docs_do_not_embed_local_user_or_host_provenance():
    offenders = []
    for path in (ROOT / "docs").rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text()
        for forbidden in FORBIDDEN_LOCAL_PROVENANCE:
            if forbidden in text:
                offenders.append((path.relative_to(ROOT).as_posix(), forbidden))

    assert offenders == []


def test_docs_do_not_track_podcast_audio():
    assert list((ROOT / "docs").rglob("*.m4a")) == []
