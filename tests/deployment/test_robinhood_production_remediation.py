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


class _RegistryContract:
    def __init__(self, address):
        self.address = address

    def startAddNewAddressToRegistry(self, contract, name):
        return contract, name

    def confirmNewAddressToRegistry(self, contract):
        return contract


class _RegistriesMigration:
    def __init__(self):
        self.hq = _RegistryContract("0x" + "1" * 40)
        self.defaults = _RegistryContract("0x" + "2" * 40)
        self.events = []
        self.deployments = []
        self.registry_calls = []
        self._next_address = 10
        self._confirmation = 4

    def get_contract(self, name):
        return self.hq if name == "RipeHq" else self.defaults

    def deploy(self, name, *args):
        contract = _RegistryContract(f"0x{self._next_address:040x}")
        self._next_address += 1
        self.events.append(("deploy", name))
        self.deployments.append((name, args, contract))
        return contract

    def execute(self, transaction, *args):
        self.events.append(("registry", transaction.__name__))
        self.registry_calls.append((transaction.__name__, args))
        if transaction.__name__ == "confirmNewAddressToRegistry":
            result = self._confirmation
            self._confirmation += 1
            return result
        return transaction(*args)


def test_0001_ledger_rejects_non_arbsys_policy_before_helper_or_registry(monkeypatch):
    migration = _RegistriesMigration()
    helper_calls = []
    monkeypatch.setattr(
        REGISTRIES,
        "LEDGER_ACTION_BLOCK_SOURCE",
        "0x0000000000000000000000000000000000000065",
    )
    monkeypatch.setattr(
        REGISTRIES,
        "validate_ledger_action_block_source",
        lambda *args, **kwargs: helper_calls.append((args, kwargs)),
    )

    with pytest.raises(
        AssertionError,
        match="production action-block source must be ArbSys",
    ):
        REGISTRIES.migrate(migration)

    assert helper_calls == []
    assert migration.registry_calls == []


def test_0001_ledger_validates_strictly_before_registry_mutation(monkeypatch):
    migration = _RegistriesMigration()
    helper_calls = []

    def validate(candidate_migration, ledger_address, expected_source, **kwargs):
        helper_calls.append(
            (candidate_migration, ledger_address, expected_source, kwargs)
        )
        migration.events.append(("validate", ledger_address))
        return 0x64, 99

    monkeypatch.setattr(
        REGISTRIES,
        "validate_ledger_action_block_source",
        validate,
    )

    assert REGISTRIES.migrate(migration) is None
    assert helper_calls == [
        (
            migration,
            migration.deployments[0][2].address,
            0x64,
            {"allow_local_preview": False},
        )
    ]
    assert migration.events[:3] == [
        ("deploy", "Ledger"),
        ("validate", migration.deployments[0][2].address),
        ("registry", "startAddNewAddressToRegistry"),
    ]
    assert [call[0] for call in migration.registry_calls] == [
        "startAddNewAddressToRegistry",
        "confirmNewAddressToRegistry",
        "startAddNewAddressToRegistry",
        "confirmNewAddressToRegistry",
    ]


def test_0001_ledger_validation_failure_leaves_registry_untouched(monkeypatch):
    migration = _RegistriesMigration()

    def fail_validation(*_args, **_kwargs):
        raise AssertionError("Ledger action-block source mismatch")

    monkeypatch.setattr(
        REGISTRIES,
        "validate_ledger_action_block_source",
        fail_validation,
    )

    with pytest.raises(
        AssertionError,
        match="Ledger action-block source mismatch",
    ):
        REGISTRIES.migrate(migration)

    assert migration.registry_calls == []
