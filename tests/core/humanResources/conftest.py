import boa
import pytest

from conf_utils import filter_logs
from constants import EIGHTEEN_DECIMALS
from contracts.modules import Contributor


@pytest.fixture(scope="module")
def valid_contributor_terms():
    """Valid contributor terms shared by the Contributor test modules."""
    return {
        "owner": "0x" + "11" * 20,
        "manager": "0x" + "22" * 20,
        "compensation": 500_000 * EIGHTEEN_DECIMALS,
        "startDelay": 7 * 24 * 3600,
        "vestingLength": 2 * 365 * 24 * 3600,
        "cliffLength": 90 * 24 * 3600,
        "unlockLength": 365 * 24 * 3600,
        "depositLockDuration": 100,
    }


@pytest.fixture(scope="module")
def setupHrConfig(mission_control, switchboard_delta, contributor_template):
    """Set MissionControl's HR configuration for Contributor tests."""

    def setup_hr_config(
        _contribTemplate=None,
        _maxCompensation=1_000_000 * EIGHTEEN_DECIMALS,
        _minCliffLength=30 * 24 * 3600,
        _maxStartDelay=90 * 24 * 3600,
        _minVestingLength=365 * 24 * 3600,
        _maxVestingLength=4 * 365 * 24 * 3600,
    ):
        template_addr = (
            _contribTemplate if _contribTemplate else contributor_template.address
        )
        hr_config = (
            template_addr,
            _maxCompensation,
            _minCliffLength,
            _maxStartDelay,
            _minVestingLength,
            _maxVestingLength,
        )
        mission_control.setHrConfig(hr_config, sender=switchboard_delta.address)
        return hr_config

    yield setup_hr_config


@pytest.fixture(scope="module")
def setupLedgerBalance(ledger, switchboard_delta):
    """Set the Ledger's RIPE allocation for HR."""

    def setup_ledger_balance(_amount=1_000_000 * EIGHTEEN_DECIMALS):
        ledger.setRipeAvailForHr(_amount, sender=switchboard_delta.address)
        return _amount

    yield setup_ledger_balance


@pytest.fixture(scope="module")
def setupRipeGovVaultConfig(
    mission_control,
    setGeneralConfig,
    setAssetConfig,
    switchboard_alpha,
    ripe_token,
):
    """Configure the RIPE asset in the RipeGov vault."""

    def setup_ripe_gov_vault_config(
        _assetWeight=100_00,
        _minLockDuration=100,
        _maxLockDuration=1000,
        _maxLockBoost=200_00,
        _exitFee=10_00,
        _canExit=True,
    ):
        setGeneralConfig()
        lock_terms = (
            _minLockDuration,
            _maxLockDuration,
            _maxLockBoost,
            _canExit,
            _exitFee,
        )
        mission_control.setRipeGovVaultConfig(
            ripe_token,
            _assetWeight,
            False,
            lock_terms,
            sender=switchboard_alpha.address,
        )
        setAssetConfig(ripe_token, _vaultIds=[2])

    yield setup_ripe_gov_vault_config


@pytest.fixture(autouse=True)
def _live_ripe_gov_terms_for_contributor_creation(setupRipeGovVaultConfig):
    """Contributor creation requires live RipeGov terms: 0 < duration <= max."""
    setupRipeGovVaultConfig()


@pytest.fixture(scope="module")
def deployedContributor(
    human_resources,
    setupHrConfig,
    setupLedgerBalance,
    valid_contributor_terms,
    governance,
):
    """Deploy a Contributor through HumanResources."""

    def deployed_contributor(_terms=None):
        terms = _terms if _terms else valid_contributor_terms
        setupHrConfig()
        setupLedgerBalance(terms["compensation"])
        action_id = human_resources.initiateNewContributor(
            terms["owner"],
            terms["manager"],
            terms["compensation"],
            terms["startDelay"],
            terms["vestingLength"],
            terms["cliffLength"],
            terms["unlockLength"],
            terms["depositLockDuration"],
            sender=governance.address,
        )
        boa.env.time_travel(blocks=human_resources.actionTimeLock())
        human_resources.confirmNewContributor(action_id, sender=governance.address)
        events = filter_logs(human_resources, "NewContributorConfirmed")
        return events[0].contributorAddr

    yield deployed_contributor


@pytest.fixture
def contributor_contract(deployedContributor):
    """Return a fresh deployed Contributor contract."""
    return Contributor.at(deployedContributor())


@pytest.fixture
def owner_address(valid_contributor_terms):
    return valid_contributor_terms["owner"]


@pytest.fixture
def manager_address(valid_contributor_terms):
    return valid_contributor_terms["manager"]
