import importlib.util
import os
import re
from operator import itemgetter

from scripts.utils import log
from scripts.utils.migration import Migration
from scripts.utils.deploy_args import DeployArgs


class MigrationError(Exception):
    """
    Error representing an exception that occurs while executing a migration.
    Provides a `failure_timestamp` to identify the migration in which the
    failure occurred, which can be used to resume execution later on.
    """

    def __init__(
        self, failure_timestamp, message="An error occurred while executing migration"
    ):
        self.failure_timestamp = failure_timestamp
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message}. Timestamp of failed migration script: {self.failure_timestamp}"


class MigrationRunner:
    """
    Facilitates the execution of migration scripts.
    """

    def __init__(self, migrations_dir, history_dir, files):
        self.migrations_dir = migrations_dir
        self.history_dir = history_dir
        self.files = files
        self.gas = 0

    def run(self, deploy_args: DeployArgs, start_timestamp=None, end_timestamp=None, continue_running=True):
        """
        Run migrations starting at `start_timestamp`. If no start timestamp is provided,
        the history directory is checked for existing timestamps, and migrations will
        start after the latest recorded manifest timestamp.

        The `migrate` function of each migration is called with the manifest generated
        by the previous migration. Manifests returned by each migration are stored in
        the history directory. For shared deployments, they should be included in version
        control.

        To make it easy for other utilities to obtain the current manifest, a manifest
        named `current-manifest.json` will be also be saved in the history directory,
        duplicating the manifest of the latest migration.
        """
        for migrate, timestamp, prev_timestamp in self._migrations(start_timestamp, end_timestamp):
            log.h1(f"Running migration with timestamp {timestamp}...")
            try:
                migration = Migration(
                    deploy_args, self.files, timestamp, prev_timestamp, self.history_dir
                )
                migrate(migration)
                self.gas += migration.end()

                if not continue_running:
                    break
            except Exception as exception:
                raise MigrationError(timestamp) from exception
        return self.gas

    def _migrations(self, start_timestamp=None, end_timestamp=None):
        # Generator that returns a `(migration, timestamp, prev_timestamp)` tuple for
        # each migration script, starting ON OR AFTER `start_timestamp`.
        #
        # If no start timestamp is provided, the history directory is checked for existing
        # timestamps, and migrations will start after the latest recorded manifest timestamp.

        migrations = []
        if start_timestamp == None:
            start_timestamp = self._latest_manifest_timestamp()
            migrations = self._filtered_migration_filenames(
                start_timestamp, end_timestamp, inclusive=False
            )
        else:
            migrations = self._filtered_migration_filenames(
                start_timestamp, end_timestamp)

        for filename, timestamp, prev_timestamp in migrations:
            migration = importlib.util.spec_from_file_location('migration', filename)
            module = importlib.util.module_from_spec(migration)
            migration.loader.exec_module(module)
            yield module.migrate, timestamp, prev_timestamp

    def _filtered_migration_filenames(self, start_timestamp, end_timestamp, inclusive=True):
        # Get a list of migration scripts having timestamps greater than or equal
        # to the value of `start_timestamp`.
        #
        # If `inclusive` == False, only timestamps AFTER the start timestamp will be
        # included.
        #
        # Returns a list of `(filename, timestamp, prev_timestamp)` tuples.
        # `prev_timestamp` is included so that the manifest from the previous
        # migration can be retrieved and passed to the next migration.

        timestamped_migrations = []
        for file in os.listdir(self.migrations_dir):
            # timestamp of the filename is the initial string of numbers,
            # up to the first non-digit character
            match = re.fullmatch("(\d+).*\.py$", file)
            if match:
                timestamp = match.group(1)
                filename = os.path.join(self.migrations_dir, file)
                timestamped_migrations.append((filename, timestamp))

        # sort order of `os.listdir` is not guaranteed, so we sort on timestamp
        timestamped_migrations = sorted(
            timestamped_migrations, key=itemgetter(0))

        # include previous timestamp in migration tuples
        migrations = []
        prev_timestamp = None
        for filename, timestamp in timestamped_migrations:
            if end_timestamp != '0' and end_timestamp != None and timestamp > end_timestamp:
                break
            if start_timestamp == None or timestamp >= start_timestamp:
                migrations.append((filename, timestamp, prev_timestamp))
            prev_timestamp = timestamp

        return migrations

    def _latest_manifest_timestamp(self):
        # get the timestamp of the most recently executed migration
        # (returns None if no migrations have been run)

        latest_timestamp = None

        # create the history directory if it doesn't already exist
        os.makedirs(self.history_dir, exist_ok=True)

        # scan each file to get the latest timestamp
        for file in os.listdir(self.history_dir):
            match = re.fullmatch("(.*)\-manifest\.json$", file)
            if match:
                timestamp = match.group(1)
                if latest_timestamp == None or timestamp > latest_timestamp:
                    latest_timestamp = timestamp

        return latest_timestamp
