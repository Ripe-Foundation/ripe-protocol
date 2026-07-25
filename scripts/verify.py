import click

from config.network_profiles import (
    NETWORK_PROFILE_IDS,
    NetworkProfileError,
    Operation,
    OperationOutcome,
    get_profile,
    operation_decision,
    static_manifest_path,
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
        "equivalent spelling. Availability is operation-specific; `local` "
        "is reserved for an embedded local runtime."
    ),
)
@click.option(
    "--environment",
    default=None,
    help=(
        "Reserved history-namespace assertion, checked only for a supported "
        "verification route."
    ),
)
@click.option(
    "--manifest",
    default="current",
    show_default=True,
    help=(
        "Reserved manifest-name assertion. This command does not submit "
        "verification."
    ),
)
def cli(profile_id, environment, manifest):
    """Select a verification route without submitting verification."""
    try:
        profile = get_profile(profile_id)
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
