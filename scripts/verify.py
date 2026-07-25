import re

import click

from config.network_profiles import (
    NETWORK_PROFILE_IDS,
    NetworkProfileError,
    Operation,
    OperationOutcome,
    PathState,
    get_profile,
    operation_decision,
)


def _profile_manifest_path(profile, manifest_name, environment):
    repository = profile.repository
    if (
        repository.history_dir is None
        or repository.history_state is PathState.ABSENT
    ):
        return None
    if environment is not None and environment != repository.history_dir.name:
        raise NetworkProfileError(
            "H02_HISTORY_ALIAS",
            profile_id=profile.identity.profile_id,
            operation=Operation.VERIFICATION,
        )
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", manifest_name):
        raise NetworkProfileError(
            "H02_REPOSITORY_UNAVAILABLE",
            profile_id=profile.identity.profile_id,
            operation=Operation.VERIFICATION,
        )
    return repository.history_dir / f"{manifest_name}-manifest.json"


@click.command()
@click.option(
    "--profile",
    "--chain",
    "profile_id",
    required=True,
    type=click.Choice(NETWORK_PROFILE_IDS, case_sensitive=False),
    help=(
        "Required canonical network profile. `--chain` is a deprecated "
        "equivalent spelling."
    ),
)
@click.option(
    "--environment",
    default=None,
    help=(
        "Optional compatibility assertion; it must match the profile-owned "
        "history namespace."
    ),
)
@click.option(
    "--manifest",
    default="current",
    show_default=True,
    help="Profile-owned manifest name.",
)
def cli(profile_id, environment, manifest):
    """Select a verification route without submitting verification."""
    try:
        profile = get_profile(profile_id)
        decision = operation_decision(profile, Operation.VERIFICATION)
        selected_manifest = _profile_manifest_path(
            profile, manifest, environment
        )
        if selected_manifest is not None:
            click.echo(f"Manifest: {selected_manifest}")

        if decision.outcome is OperationOutcome.BLOCKED_PENDING_POLICY:
            raise NetworkProfileError(
                "H02_VERIFIER_BLOCKED",
                profile_id=profile.identity.profile_id,
                operation=Operation.VERIFICATION,
            )
        if decision.outcome is OperationOutcome.UNSUPPORTED:
            raise NetworkProfileError(
                "H02_VERIFIER_UNSUPPORTED",
                profile_id=profile.identity.profile_id,
                operation=Operation.VERIFICATION,
            )
        raise NetworkProfileError(
            "H02_OPERATION_INVALID",
            profile_id=profile.identity.profile_id,
            operation=Operation.VERIFICATION,
        )
    except NetworkProfileError as error:
        raise click.ClickException(str(error)) from None


if __name__ == "__main__":
    cli()
