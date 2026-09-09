from pathlib import Path

from scripts import migrate


def test_migration_compiler_cache_is_repository_owned(monkeypatch, tmp_path):
    observed = []
    monkeypatch.setattr(migrate, "ROOT", tmp_path)
    monkeypatch.setattr(migrate, "set_cache_dir", observed.append)
    monkeypatch.delenv("RIPE_MIGRATION_BOA_CACHE_DIR", raising=False)

    cache_dir = migrate._configure_compiler_cache()

    assert cache_dir == tmp_path / "cache" / "migrations" / "boa"
    assert cache_dir.is_dir()
    assert observed == [cache_dir]


def test_migration_compiler_cache_allows_an_explicit_override(
    monkeypatch, tmp_path
):
    cache_dir = tmp_path / "migration-cache"
    observed = []
    monkeypatch.setattr(migrate, "set_cache_dir", observed.append)
    monkeypatch.setenv("RIPE_MIGRATION_BOA_CACHE_DIR", str(cache_dir))

    assert migrate._configure_compiler_cache() == Path(cache_dir)
    assert cache_dir.is_dir()
    assert observed == [cache_dir]
