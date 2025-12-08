from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS


def migrate(migration: Migration):
    hq = migration.get_contract("RipeHq")
    defaults = migration.deploy("DefaultsBase")
    mission_control = migration.deploy("MissionControl", hq, defaults)
