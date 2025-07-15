from scripts.utils.migration import Migration
from tests.constants import ZERO_ADDRESS


def migrate(migration: Migration):
    migration.deploy(
        'DefaultsBase',
        migration.get_address('Contributor'),
        migration.get_address('TrainingWheels'),
        ZERO_ADDRESS
    )
