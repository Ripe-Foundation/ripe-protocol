"""Plain local graph helper. Call only AFTER selecting the Boa environment."""
from types import SimpleNamespace
from contextlib import contextmanager
import boa
from conf_utils import advance_timelock_blocks

ZERO = '0x' + '00' * 20
ETH = '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'
SOURCE = 'contracts/priceSources/UniswapV3TwapPrices.vy'


def identity():
    return boa.loads('# @version 0.4.3\n@external\n@view\ndef alive() -> bool:\n    return True\n')


def register(registry, contract, gov):
    assert registry.startAddNewAddressToRegistry(contract, 'local TWAP test', sender=gov)
    advance_timelock_blocks(registry.registryChangeTimeLock())
    return registry.confirmNewAddressToRegistry(contract, sender=gov)


def make_graph():
    timestamp = boa.env.timestamp
    gov = boa.env.generate_address('twap HQ governor')
    local = boa.env.generate_address('twap local governor')
    tokens = [identity() for _ in range(3)]
    hq = boa.load('contracts/registries/RipeHq.vy', *tokens, gov, 1, 100, 1, 100)
    ledger, actor = identity(), identity()
    mc = boa.load('contracts/data/MissionControl.vy', hq, ZERO)
    board = boa.load('contracts/registries/Switchboard.vy', hq, local, 1, 100)
    desk = boa.load('contracts/registries/PriceDesk.vy', hq, local, ETH, 1, 100)
    for index, contract in enumerate([ledger, mc, board, desk], start=4):
        assert register(hq, contract, gov) == index
    register(board, actor, gov)
    config = mc.genConfig()._asdict()
    config['priceStaleTime'] = 86400
    mc.setGeneralConfig(tuple(config.values()), sender=actor.address)
    assert hq.getAddr(7) == desk.address
    assert hq.getAddr(5) == mc.address
    assert mc.getPriceStaleTime() == 86400
    assert boa.env.timestamp == timestamp
    return SimpleNamespace(gov=gov, local=local, hq=hq, mc=mc, board=board, actor=actor, desk=desk)


def set_policy(g, age):
    config = g.mc.genConfig()._asdict()
    config['priceStaleTime'] = age
    g.mc.setGeneralConfig(tuple(config.values()), sender=g.actor.address)


def rotate_desk(g, desk=None):
    desk = desk or boa.load('contracts/registries/PriceDesk.vy', g.hq, g.local, ETH, 1, 100)
    assert g.hq.startAddressUpdateToRegistry(7, desk, sender=g.gov)
    advance_timelock_blocks(g.hq.registryChangeTimeLock())
    assert g.hq.confirmAddressUpdateToRegistry(7, sender=g.gov)
    g.desk = desk
    return desk


@contextmanager
def temporary_desk(g, desk=None):
    """Restore both the registry and Python pointer, including on assertions."""
    old=g.desk
    with boa.env.anchor():
        try:
            yield rotate_desk(g,desk)
        finally:
            g.desk=old


def source(g, factory, weth, anchor):
    return boa.load(SOURCE, g.hq, g.local, 2, 100, factory, weth, anchor)


def params(pool, window=1800, current=1, harmonic=1, age=3600, quote_age=0):
    return (getattr(pool, 'address', pool), window, current, harmonic, age, quote_age)


def admit(g, s, asset, p, register_source=True):
    assert s.addNewPriceFeed(asset, p, sender=g.gov)
    advance_timelock_blocks(s.actionTimeLock())
    assert s.confirmNewPriceFeed(asset, sender=g.gov)
    if register_source and g.desk.getRegId(s) == 0:
        register(g.desk, s, g.gov)
    return s.getPrice(asset)
