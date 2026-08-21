import boa

from config.BluePrint import PARAMS
from conf_utils import filter_logs
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
    alice,
):
    with boa.env.anchor():
        raw_ids = [1, 1, 2, 99, 2]
        mission_control.setPriorityPriceSourceIds(
            raw_ids,
            sender=switchboard_alpha.address,
        )
        assert list(mission_control.getPriorityPriceSourceIds()) == raw_ids

        mission_control.setPriorityPriceSourceIds(
            [],
            sender=switchboard_alpha.address,
        )
        assert list(mission_control.getPriorityPriceSourceIds()) == []

        with boa.reverts("no perms"):
            mission_control.setPriorityPriceSourceIds(
                [1],
                sender=alice,
            )


def test_switchboard_writes_valid_priority_list(
    switchboard_alpha,
    mission_control,
    governance,
):
    with boa.env.anchor():
        valid_ids = [1, 8, 2, 4, 5]
        action_id = switchboard_alpha.setPriorityPriceSourceIds(
            valid_ids,
            sender=governance.address,
        )
        pending = filter_logs(switchboard_alpha, "PendingPriorityPriceSourceIdsChange")
        assert pending[0].numPriorityPriceSourceIds == 5
        boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock() + 1)
        assert switchboard_alpha.executePendingAction(action_id, sender=governance.address)
        assert list(mission_control.getPriorityPriceSourceIds()) == valid_ids
        modified = filter_logs(switchboard_alpha, "PriorityPriceSourceIdsModified")
        assert modified[0].numIds == 5


def test_switchboard_write_then_id_disabled_after_propose(
    switchboard_alpha,
    mission_control,
    price_desk,
    governance,
):
    with boa.env.anchor():
        mixed_action = switchboard_alpha.setPriorityPriceSourceIds(
            [1, 6],
            sender=governance.address,
        )
        only_disabled = switchboard_alpha.setPriorityPriceSourceIds(
            [6],
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

        assert switchboard_alpha.executePendingAction(
            mixed_action,
            sender=governance.address,
        )
        assert list(mission_control.getPriorityPriceSourceIds()) == [1]
        modified = filter_logs(switchboard_alpha, "PriorityPriceSourceIdsModified")
        assert len(modified) == 1
        assert modified[0].numIds == 1

        after_mixed = list(mission_control.getPriorityPriceSourceIds())
        with boa.reverts("invalid priority price source ids"):
            switchboard_alpha.executePendingAction(
                only_disabled,
                sender=governance.address,
            )
        assert switchboard_alpha.hasPendingAction(only_disabled)
        assert list(mission_control.getPriorityPriceSourceIds()) == after_mixed


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
    mission_control,
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
    assert replacement.getRipeHq() == mock_hq.address
    assert price_desk.isValidRegId(1)
    default_ids = list(mission_control.getPriorityPriceSourceIds())

    with boa.env.anchor():
        write_action = switchboard_alpha.setPriorityPriceSourceIds(
            [1, 1, 2, 99],
            replacement.address,
            sender=governance.address,
        )
        pending = filter_logs(switchboard_alpha, "PendingPriorityPriceSourceIdsChange")
        assert pending[0].numPriorityPriceSourceIds == 4

        revalidate_action = switchboard_alpha.setPriorityPriceSourceIds(
            [1],
            replacement.address,
            sender=governance.address,
        )

        boa.env.time_travel(blocks=switchboard_alpha.actionTimeLock() + 1)
        assert switchboard_alpha.executePendingAction(
            write_action,
            sender=governance.address,
        )
        assert list(replacement.getPriorityPriceSourceIds()) == [1]
        modified = filter_logs(switchboard_alpha, "PriorityPriceSourceIdsModified")
        assert modified[0].numIds == 1
        assert list(mission_control.getPriorityPriceSourceIds()) == default_ids

        assert own_desk.startAddressDisableInRegistry(1, sender=governance.address)
        if own_desk.registryChangeTimeLock() != 0:
            boa.env.time_travel(blocks=own_desk.registryChangeTimeLock() + 1)
        assert own_desk.confirmAddressDisableInRegistry(1, sender=governance.address)
        assert own_desk.getAddr(1) == boa.eval("empty(address)")
        assert price_desk.getAddr(1) != boa.eval("empty(address)")

        before_fail = list(replacement.getPriorityPriceSourceIds())
        with boa.reverts("invalid priority price source ids"):
            switchboard_alpha.executePendingAction(
                revalidate_action,
                sender=governance.address,
            )
        assert switchboard_alpha.hasPendingAction(revalidate_action)
        assert list(replacement.getPriorityPriceSourceIds()) == before_fail
