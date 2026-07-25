import click

from config.network_profiles import (
    NETWORK_PROFILE_IDS,
    NetworkProfileError,
    Operation,
    OperationOutcome,
    get_profile,
    operation_decision,
    static_manifest_path,
    validate_manifest_assertions,
)


@click.command()
@click.option(
    "--profile",
    "--chain",
    "profile_id",
    required=True,
    type=click.Choice(NETWORK_PROFILE_IDS, case_sensitive=False),
    help=(
        "Required canonical network profile. `--chain` is a deprecated "
        "equivalent spelling. `local` is recognized but unsupported by this "
        "command; it is reserved for a future embedded-runtime path."
    ),
)
@click.option(
    "--environment",
    default=None,
    help=(
        "Optional profile history-namespace assertion, validated before the "
        "verification route outcome."
    ),
)
@click.option(
    "--manifest",
    default="current",
    show_default=True,
    help=(
        "Manifest-name assertion validated before route selection. This "
        "command does not submit verification."
    ),
)
def cli(profile_id, environment, manifest):
    """Select a verification route without submitting verification."""
    try:
        profile = get_profile(profile_id)
        validate_manifest_assertions(
            profile,
            manifest,
            operation=Operation.VERIFICATION,
            environment=environment,
        )
        decision = operation_decision(profile, Operation.VERIFICATION)

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
        selected_manifest = static_manifest_path(
            profile,
            manifest,
            operation=Operation.VERIFICATION,
            environment=environment,
        )
        click.echo(f"Manifest: {selected_manifest}")
        raise NetworkProfileError(
            "H02_OPERATION_INVALID",
            profile_id=profile.identity.profile_id,
            operation=Operation.VERIFICATION,
        )
    except NetworkProfileError as error:
        raise click.ClickException(str(error)) from None


if __name__ == "__main__":
    cli()
