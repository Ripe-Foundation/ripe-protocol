import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


def _load(relative_path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VAULTS = _load(
    "migrations/robinhood-mainnet/0004_Vaults.py",
    "rh_production_vaults",
)
FINISH = _load(
    "migrations/robinhood-mainnet/0007_FinishSetup.py",
    "rh_production_finish_setup",
)
REGISTRIES = _load(
    "migrations/robinhood-mainnet/0001_Registries.py",
    "rh_production_registries",
)
BASE_VAULTS = _load(
    "migrations/base-mainnet/1008_VaultBook.py",
    "base_production_vaults",
)


def test_base_and_robinhood_bind_stability_and_ripe_gov_ids():
    assert VAULTS.STABILITY_POOL_VAULT_ID == BASE_VAULTS.STABILITY_POOL_VAULT_ID == 1
    assert VAULTS.RIPE_GOV_VAULT_ID == BASE_VAULTS.RIPE_GOV_VAULT_ID == 2
    assert VAULTS.VAULTS[:2] == ("StabilityPool", "RipeGov")


class _Vault:
    def __init__(self, address, paused=False):
        self.address = address
        self.paused = paused

    def totalClaimableBalances(self, _asset):
        return 0

    def totalGovPoints(self):
        return 0

    def isPaused(self):
        return self.paused


class _VaultBook:
    def __init__(self, stability, ripe_gov):
        self.addresses = {1: stability.address, 2: ripe_gov.address}
        self.ids = {stability.address: 1, ripe_gov.address: 2}

    def getRegId(self, vault):
        return self.ids.get(vault.address, 0)

    def getAddr(self, vault_id):
        return self.addresses.get(vault_id, "0x" + "0" * 40)


class _MissionControl:
    def __init__(self, stability_id=1, gov_id=2, marked=True):
        self.stability_id = stability_id
        self.gov_id = gov_id
        self.marked = marked

    def preferredStabVaultId(self):
        return self.stability_id

    def coreRipeGovVaultId(self):
        return self.gov_id

    def isStabVaultId(self, vault_id):
        return self.marked and vault_id == self.stability_id


def _verify_vaults(stability=None, ripe_gov=None, mission_control=None):
    stability = stability or _Vault("0x" + "1" * 40)
    ripe_gov = ripe_gov or _Vault("0x" + "2" * 40)
    VAULTS._verify_vault_bindings(
        _VaultBook(stability, ripe_gov),
        mission_control or _MissionControl(),
        stability,
        ripe_gov,
        "0x" + "3" * 40,
    )


def test_post_deploy_vault_binding_accepts_exact_types_and_pointers():
    _verify_vaults()


@pytest.mark.parametrize(
    "candidate_stability,candidate_control",
    [
        (_Vault("0x" + "1" * 40, paused=True), None),
        (None, _MissionControl(stability_id=0)),
        (None, _MissionControl(gov_id=0)),
        (None, _MissionControl(marked=False)),
    ],
)
def test_post_deploy_vault_binding_rejects_paused_or_wrong_pointers(
    candidate_stability,
    candidate_control,
):
    with pytest.raises(AssertionError):
        _verify_vaults(
            stability=candidate_stability,
            mission_control=candidate_control,
        )


def test_post_deploy_vault_binding_rejects_wrong_interface():
    class WrongVault:
        address = "0x" + "1" * 40

        def isPaused(self):
            return False

    with pytest.raises(AttributeError):
        _verify_vaults(stability=WrongVault())


class _ActionTimelock:
    def __init__(self, name, minimum):
        self.name = name
        self.minimum = minimum
        self.value = 0

    def actionTimeLock(self):
        return self.value

    def minActionTimeLock(self):
        return self.minimum

    def setActionTimeLockAfterSetup(self, selected):
        assert self.value == 0
        self.value = selected
        return True


class _RegistryTimelock:
    def __init__(self, name, minimum):
        self.name = name
        self.minimum = minimum
        self.value = 0

    def registryChangeTimeLock(self):
        return self.value

    def minRegistryTimeLock(self):
        return self.minimum

    def setRegistryTimeLockAfterSetup(self, selected):
        assert self.value == 0
        self.value = selected
        return True


class _Hq(_RegistryTimelock):
    def finishRipeHqSetup(self, governance):
        self.governance = governance
        return True


class _FinishMigration:
    def __init__(self):
        self.fetched = []
        self.calls = []
        self.contracts = {
            name: _ActionTimelock(name, index + 11)
            for index, name in enumerate(FINISH.ACTION_TIMELOCK_COMPONENTS)
        }
        self.contracts.update(
            {
                name: _RegistryTimelock(name, index + 101)
                for index, name in enumerate(FINISH.REGISTRY_TIMELOCK_COMPONENTS)
                if name != "RipeHq"
            }
        )
        self.contracts["RipeHq"] = _Hq("RipeHq", 104)

    def get_contract(self, name):
        self.fetched.append(name)
        return self.contracts[name]

    def execute(self, transaction, *args):
        self.calls.append((transaction.__self__.name, transaction.__name__, args))
        return transaction(*args)


def test_finish_setup_records_all_twelve_readbacks_before_safe_handoff():
    migration = _FinishMigration()
    FINISH.migrate(migration)

    expected = set(FINISH.ACTION_TIMELOCK_COMPONENTS) | set(
        FINISH.REGISTRY_TIMELOCK_COMPONENTS
    )
    finalized = {
        name
        for name, method, _args in migration.calls
        if method in {
            "setActionTimeLockAfterSetup",
            "setRegistryTimeLockAfterSetup",
        }
    }
    assert finalized == expected
    assert len(finalized) == 12
    assert "BlueChipYieldPrices" not in migration.fetched
    assert migration.calls[-1][1] == "finishRipeHqSetup"
    for name in FINISH.ACTION_TIMELOCK_COMPONENTS:
        component = migration.contracts[name]
        assert component.value == component.minimum != 0
    for name in FINISH.REGISTRY_TIMELOCK_COMPONENTS:
        component = migration.contracts[name]
        assert component.value == component.minimum != 0


def test_ledger_live_profile_requires_real_rpc():
    class MissingRpc:
        def rpc(self):
            return None

    with pytest.raises(AssertionError, match="real RPC"):
        REGISTRIES._node_read_word(MissingRpc(), "0x" + "1" * 40, "x()")


@pytest.mark.parametrize(
    "source,action_block",
    [(0, 1), (0x65, 1), (0x64, 0)],
)
def test_ledger_live_profile_rejects_wrong_source_or_zero_health(
    monkeypatch,
    source,
    action_block,
):
    answers = iter((source, action_block))
    monkeypatch.setattr(REGISTRIES, "_node_read_word", lambda *_args: next(answers))
    with pytest.raises(AssertionError):
        REGISTRIES._validate_ledger_profile(object(), "0x" + "1" * 40)


def test_ledger_live_profile_accepts_exact_source_and_nonzero_health(monkeypatch):
    answers = iter((0x64, 99))
    monkeypatch.setattr(REGISTRIES, "_node_read_word", lambda *_args: next(answers))
    assert REGISTRIES._validate_ledger_profile(
        object(),
        "0x" + "1" * 40,
    ) == (0x64, 99)
