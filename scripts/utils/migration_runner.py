import importlib.util
import os
import re

from scripts.utils import log
from scripts.utils.migration import (Migration, MigrationHistoryError,
                                     history_has_deployment)
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

    def _require_start_point(self, deploy_args, start_timestamp):
        # A history that already has a current-manifest.json has been deployed.
        # Extending it is fine; redoing it by accident is not, and those are the
        # same command: `--start-timestamp` defaults to "0", which selects every
        # migration from the first one. Nothing here corrects for that -- the
        # numbered step manifests are pruned by policy, `end()` deletes the
        # transaction log on success, and current-manifest.json records no step
        # attribution, so nothing says which migration ran last.
        #
        # Two ways to proceed deliberately: name the first migration to run, or
        # pass --is-retry to resume a run that failed partway (which is also
        # what makes the per-step skip read the log at all).
        if not history_has_deployment(self.history_dir):
            return
        if not getattr(deploy_args, "ignore_logs", True):  # --is-retry
            return
        try:
            if int(str(start_timestamp).strip()) > 0:
                return
        except (TypeError, ValueError):
            pass
        raise MigrationHistoryError(
            "H06_DEPLOYED_HISTORY_NEEDS_START_TIMESTAMP: "
            f"{self.history_dir} already holds a deployed current-manifest.json. "
            "Running from the default start point would execute every migration "
            "from the first one against it. Pass --start-timestamp naming the "
            "first migration to run, or --is-retry to resume a failed run."
        )

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
        self._require_start_point(deploy_args, start_timestamp)

        for migrate, timestamp, prev_timestamp in self._migrations(start_timestamp, end_timestamp):
            log.h1(f"Running migration with timestamp {timestamp}...")
            try:
                migration = Migration(
                    deploy_args, self.files, timestamp, prev_timestamp, self.history_dir,
                    # _require_start_point has established a deliberate start.
                    allow_deployed_history=True,
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
            match = re.fullmatch(r"(\d+).*\.py$", file)
            if match:
                timestamp = match.group(1)
                filename = os.path.join(self.migrations_dir, file)
                timestamped_migrations.append((filename, timestamp))

        # sort order of `os.listdir` is not guaranteed, so we sort on timestamp
        # Convert timestamps to integers for proper numerical sorting
        timestamped_migrations = sorted(
            timestamped_migrations, key=lambda x: int(x[1]))

        # include previous timestamp in migration tuples
        migrations = []
        prev_timestamp = None
        for filename, timestamp in timestamped_migrations:
            # Convert timestamps to integers for proper numerical comparison
            timestamp_int = int(timestamp)
            end_timestamp_int = int(end_timestamp) if end_timestamp and end_timestamp != '0' else None
            start_timestamp_int = int(start_timestamp) if start_timestamp else None

            if end_timestamp_int is not None and timestamp_int > end_timestamp_int:
                break
            # `inclusive` was declared, documented and passed by the auto-resume
            # call above, but never read here -- both modes compared with `>=`.
            # That made resuming re-run the migration that produced the latest
            # manifest. On both mainnets the resume point is 2026080700, whose
            # migration deploys the CCIP token pools, so a resume would have
            # deployed a second set against a live chain.
            if start_timestamp_int is None or (
                timestamp_int >= start_timestamp_int
                if inclusive
                else timestamp_int > start_timestamp_int
            ):
                migrations.append((filename, timestamp, prev_timestamp))
            prev_timestamp = timestamp

        return migrations

    def _latest_manifest_timestamp(self):
        # get the timestamp of the most recently executed migration
        # (returns None if no migrations have been run)

        latest_timestamp = None

        # create the history directory if it doesn't already exist
        os.makedirs(self.history_dir, exist_ok=True)

        # Scan each file to get the latest timestamp. The pattern is anchored to
        # digits on purpose: `current-manifest.json` sits in the same directory
        # and a `(.*)` group matched it too, so this walked into
        # int("current") -- a ValueError -- as soon as a history held both a
        # numbered manifest and the current one. That is every history with
        # step manifests, which is to say every real deployment.
        for file in os.listdir(self.history_dir):
            match = re.fullmatch(r"(\d+)\-manifest\.json$", file)
            if match:
                timestamp = match.group(1)
                # Convert timestamps to integers for proper numerical comparison
                if latest_timestamp == None or int(timestamp) > int(latest_timestamp):
                    latest_timestamp = timestamp

        return latest_timestamp
