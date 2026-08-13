import boa

from constants import ZERO_ADDRESS


def test_is_underscore_addr_default_uses_current_mission_control(
    teller_utils,
    mission_control,
    switchboard_alpha,
    mock_undy_v2,
    alice,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )

    assert teller_utils.isUnderscoreAddr(alice) is True


def test_is_underscore_addr_default_and_explicit_forms_agree(
    teller_utils,
    mission_control,
    switchboard_alpha,
    mock_undy_v2,
    alice,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )

    default_result = teller_utils.isUnderscoreAddr(alice)
    explicit_result = teller_utils.isUnderscoreAddr(
        alice,
        mission_control.address,
    )

    assert default_result == explicit_result
    assert default_result is True


def test_is_underscore_addr_zero_registry_returns_false(
    teller_utils,
    mission_control,
    switchboard_alpha,
    alice,
):
    mission_control.setUnderscoreRegistry(
        ZERO_ADDRESS,
        sender=switchboard_alpha.address,
    )

    assert teller_utils.isUnderscoreAddr(alice) is False
    assert (
        teller_utils.isUnderscoreAddr(alice, mission_control.address)
        is False
    )


def test_is_underscore_addr_explicit_mission_control_tracks_registry(
    teller_utils,
    mission_control,
    switchboard_alpha,
    mock_undy_v2,
    alice,
):
    mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )
    assert (
        teller_utils.isUnderscoreAddr(alice, mission_control.address)
        is True
    )

    mission_control.setUnderscoreRegistry(
        ZERO_ADDRESS,
        sender=switchboard_alpha.address,
    )
    assert (
        teller_utils.isUnderscoreAddr(alice, mission_control.address)
        is False
    )


def test_is_underscore_addr_explicit_uses_supplied_mission_control(
    teller_utils,
    mission_control,
    ripe_hq_deploy,
    defaults,
    switchboard_alpha,
    mock_undy_v2,
    alice,
):
    alternate_mission_control = boa.load(
        "contracts/data/MissionControl.vy",
        ripe_hq_deploy,
        defaults,
        name="alternate_mission_control",
    )
    mission_control.setUnderscoreRegistry(
        ZERO_ADDRESS,
        sender=switchboard_alpha.address,
    )
    alternate_mission_control.setUnderscoreRegistry(
        mock_undy_v2.address,
        sender=switchboard_alpha.address,
    )

    assert mission_control.underscoreRegistry() == ZERO_ADDRESS
    assert (
        alternate_mission_control.underscoreRegistry()
        == mock_undy_v2.address
    )
    assert teller_utils.isUnderscoreAddr(alice) is False
    assert (
        teller_utils.isUnderscoreAddr(
            alice,
            alternate_mission_control.address,
        )
        is True
    )
