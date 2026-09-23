"""Offline deployment of the actual compiled, separately licensed references."""
import json
from pathlib import Path
import boa
from boa.contracts.abi.abi_contract import ABIContractFactory

BASE = Path(__file__).resolve().parent / 'reference'


def artifact(version, name):
    return json.loads((BASE / version / 'artifacts.json').read_text())['contracts'][name]


def at(version, name, address):
    return ABIContractFactory(name, artifact(version, name)['abi']).at(address)


def deploy(version, name):
    raw = artifact(version, name)
    address, computation = boa.env.deploy(bytecode=bytes.fromhex(raw['bytecode']['object'].removeprefix('0x')))
    assert not computation.is_error, computation.error
    return at(version, name, address)
