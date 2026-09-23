"""Rebuild/check the pinned Solidity fixtures; ordinary tests only read JSON."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parent


def digest(data):
    return hashlib.sha256(data).hexdigest()


def source_hashes(version):
    directory = BASE / version
    return {
        str(p.relative_to(ROOT)): digest(p.read_bytes())
        for p in sorted(directory.rglob('*'))
        if p.is_file() and ('vendor' in p.parts or 'src' in p.parts or p.name == 'foundry.toml')
    }


def build(version, compiler):
    subprocess.run(['forge', 'build', '--root', str(BASE / version), '--use', compiler], check=True)
    contracts = ['Reference']
    if version == 'v3':
        contracts += ['UniswapV3Factory', 'UniswapV3Pool']
    result = {'compiler': compiler, 'sources': source_hashes(version), 'contracts': {}}
    for name in contracts:
        raw = json.loads((BASE / version / 'out' / f'{name}.sol' / f'{name}.json').read_text())
        assert len(raw['bytecode']['object']) > 20, name
        fields = {k: raw[k] for k in ['abi', 'bytecode', 'deployedBytecode', 'storageLayout'] if k in raw}
        # Source maps/build IDs belong in scratch Forge output. Keep executable
        # bytes and immutable offsets needed to validate the actual pool runtime.
        for k in ['bytecode', 'deployedBytecode']:
            fields[k] = {a: b for a, b in fields[k].items() if a in ('object', 'linkReferences', 'immutableReferences')}
            fields[k]['sha256'] = digest(bytes.fromhex(fields[k]['object'].removeprefix('0x')))
        fields['settings'] = raw['metadata']['settings'] if isinstance(raw['metadata'], dict) else json.loads(raw['metadata'])['settings']
        result['contracts'][name] = fields
    return (json.dumps(result, indent=2, sort_keys=True) + '\n').encode()


def verify_offline(version):
    value = json.loads((BASE / version / 'artifacts.json').read_text())
    assert value['sources'] == source_hashes(version), 'reference source/settings drift'
    for c in value['contracts'].values():
        for k in ['bytecode', 'deployedBytecode']:
            assert digest(bytes.fromhex(c[k]['object'].removeprefix('0x'))) == c[k]['sha256']
    return value


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--check', action='store_true', help='rebuild and compare exact checked fixtures')
    args = p.parse_args()
    for v, c in [('v3', '0.7.6'), ('v4', '0.8.26')]:
        data = build(v, c)
        path = BASE / v / 'artifacts.json'
        if args.check:
            assert path.read_bytes() == data, f'{v} artifacts differ'
        else:
            path.write_bytes(data)
        verify_offline(v)
        print(v, 'artifact_sha256=' + digest(data))
