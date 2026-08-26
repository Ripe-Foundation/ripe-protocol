from scripts import verify_blockscout


def test_candidate_source_comes_from_manifest_file(tmp_path, monkeypatch):
    source = tmp_path / "contracts/core/RipeReserveEngine.vy"
    source.parent.mkdir(parents=True)
    source.write_text("# candidate source\n")
    monkeypatch.setattr(verify_blockscout, "ROOT", tmp_path)

    resolved = verify_blockscout.source_for_record(
        "RipeReserveEngineCandidate2026082500",
        {"file": "contracts/core/RipeReserveEngine.vy"},
        {},
    )

    assert resolved == source


def test_candidate_source_cannot_escape_contracts(tmp_path, monkeypatch):
    source = tmp_path / "outside.vy"
    source.write_text("# not a contract source\n")
    monkeypatch.setattr(verify_blockscout, "ROOT", tmp_path)

    resolved = verify_blockscout.source_for_record(
        "Candidate",
        {"file": "outside.vy"},
        {},
    )

    assert resolved is None
