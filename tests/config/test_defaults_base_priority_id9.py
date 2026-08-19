import boa

from config.BluePrint import PARAMS
from constants import EIGHTEEN_DECIMALS, ZERO_ADDRESS


def _desk_params(fork):
    return (
        PARAMS[fork]["PRICE_DESK_MIN_REG_TIMELOCK"],
        PARAMS[fork]["PRICE_DESK_MAX_REG_TIMELOCK"],
    )


def test_defaults_base_priority_omits_id9():
    defaults = boa.load("contracts/config/DefaultsBase.vy", name="defaults_base_id9")
    live = boa.load("contracts/config/DefaultsBaseLive.vy", name="defaults_base_live_id9")
    assert list(defaults.priorityPriceSourceIds()) == [1, 8, 2, 4, 5]
    assert list(live.priorityPriceSourceIds()) == [1, 8, 2, 4, 5]
    assert 9 not in defaults.priorityPriceSourceIds()
    assert 9 not in live.priorityPriceSourceIds()


def test_defaults_base_id9_does_not_win_ahead_of_id4(
    ripe_hq,
    governance,
    switchboard_alpha,
    mission_control,
    fork,
    charlie_token,
):
    min_tl, max_tl = _desk_params(fork)
    with boa.env.anchor():
        defaults = boa.load("contracts/config/DefaultsBase.vy", name="defaults_base_id9_walk")
        priority = defaults.priorityPriceSourceIds()
        assert list(priority) == [1, 8, 2, 4, 5]
        desk = boa.load(
            "contracts/registries/PriceDesk.vy",
            ripe_hq,
            ZERO_ADDRESS,
            "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
            min_tl,
            max_tl,
            name="id9_desk",
        )
        sources = []
        for i in range(8):
            src = boa.load(
                "contracts/mock/MockPriceSource.vy",
                ripe_hq,
                min_tl,
                max_tl,
                name=f"id9_src_{i+1}",
            )
            assert desk.startAddNewAddressToRegistry(src, f"s{i+1}", sender=governance.address)
            assert desk.confirmNewAddressToRegistry(src, sender=governance.address) == i + 1
            sources.append(src)

        assert desk.numAddrs() == 9
        assert desk.isValidRegId(8)
        assert not desk.isValidRegId(9)

        sources[3].setPrice(charlie_token, 99 * EIGHTEEN_DECIMALS)
        mission_control.setPriorityPriceSourceIds(
            list(priority),
            sender=switchboard_alpha.address,
        )
        assert desk.getPrice(charlie_token) == 99 * EIGHTEEN_DECIMALS

        ninth = boa.load(
            "contracts/mock/MockPriceSource.vy",
            ripe_hq,
            min_tl,
            max_tl,
            name="id9_src_9",
        )
        ninth.setPrice(charlie_token, 42 * EIGHTEEN_DECIMALS)
        assert desk.startAddNewAddressToRegistry(ninth, "s9", sender=governance.address)
        assert desk.confirmNewAddressToRegistry(ninth, sender=governance.address) == 9
        assert desk.isValidRegId(9)
        assert desk.getPrice(charlie_token) == 99 * EIGHTEEN_DECIMALS


def test_mission_control_sanitizes_duplicates_and_invalid_ids(
    mission_control,
    switchboard_alpha,
):
    with boa.env.anchor():
        mission_control.setPriorityPriceSourceIds(
            [1, 1, 2, 99, 2],
            sender=switchboard_alpha.address,
        )
        assert list(mission_control.getPriorityPriceSourceIds()) == [1, 2]
        with boa.reverts("invalid priority price source ids"):
            mission_control.setPriorityPriceSourceIds(
                [99, 98],
                sender=switchboard_alpha.address,
            )


def test_switchboard_write_then_id_disabled_after_propose(
    switchboard_alpha,
    mission_control,
    price_desk,
    governance,
):
    with boa.env.anchor():
        action_id = switchboard_alpha.setPriorityPriceSourceIds(
            [1, 6],
            sender=governance.address,
        )
        assert price_desk.startAddressDisableInRegistry(6, sender=governance.address)
        boa.env.time_travel(
            blocks=max(
                switchboard_alpha.actionTimeLock(),
                price_desk.registryChangeTimeLock(),
            )
            + 1
        )
        assert price_desk.confirmAddressDisableInRegistry(6, sender=governance.address)
        assert price_desk.getAddr(6) == boa.eval("empty(address)")
        assert switchboard_alpha.executePendingAction(action_id, sender=governance.address)
        assert list(mission_control.getPriorityPriceSourceIds()) == [1]

        only_disabled = switchboard_alpha.setPriorityPriceSourceIds(
            [6],
            sender=governance.address,
        )
        boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock() + 1)
        with boa.reverts("invalid priority price source ids"):
            switchboard_alpha.executePendingAction(only_disabled, sender=governance.address)


MOCK_HQ = """
# @version 0.4.3

desk: public(address)
switchboard: public(address)

@deploy
def __init__(_desk: address, _switchboard: address):
    self.desk = _desk
    self.switchboard = _switchboard

@view
@external
def getAddr(_id: uint256) -> address:
    if _id == 7:
        return self.desk
    if _id == 6:
        return self.switchboard
    return empty(address)
"""


def test_replacement_mission_control_uses_own_price_desk(
    ripe_hq,
    defaults,
    switchboard,
    switchboard_alpha,
    price_desk,
    governance,
    fork,
):
    min_tl, max_tl = _desk_params(fork)
    own_desk = boa.load(
        "contracts/registries/PriceDesk.vy",
        ripe_hq,
        ZERO_ADDRESS,
        "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        min_tl,
        max_tl,
        name="replacement_mc_own_desk",
    )
    src = boa.load(
        "contracts/mock/MockPriceSource.vy",
        ripe_hq,
        min_tl,
        max_tl,
        name="replacement_mc_own_src",
    )
    assert own_desk.startAddNewAddressToRegistry(src, "own-1", sender=governance.address)
    assert own_desk.confirmNewAddressToRegistry(src, sender=governance.address) == 1
    assert own_desk.isValidRegId(1)
    assert not own_desk.isValidRegId(2)
    assert price_desk.isValidRegId(2)

    mock_hq = boa.loads(MOCK_HQ, own_desk.address, switchboard.address)
    replacement = boa.load(
        "contracts/data/MissionControl.vy",
        mock_hq.address,
        defaults,
        name="replacement_mc_priority",
    )
    replacement.setPriorityPriceSourceIds(
        [1, 1, 2, 99],
        sender=switchboard_alpha.address,
    )
    assert list(replacement.getPriorityPriceSourceIds()) == [1]
    with boa.reverts("invalid priority price source ids"):
        replacement.setPriorityPriceSourceIds(
            [2, 99],
            sender=switchboard_alpha.address,
        )
