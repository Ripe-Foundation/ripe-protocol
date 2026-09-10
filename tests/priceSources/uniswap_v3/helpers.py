"""Shared public-state and unavailable-price assertions."""
import boa


def state(s,a):
    p=s.pendingUpdates(a)
    return (s.feedConfig(a),p,tuple(s.getPricedAssets()),s.numAssets(),s.indexOfAsset(a),s.hasPriceFeed(a),s.hasPendingPriceFeedUpdate(a),s.pendingActions(p.actionId),s.actionId())


def unavailable(lab):
    """Active feed returning (0, True): the desk reports 0 and strict reads fail closed."""
    s,a,g=lab.s,lab.asset,lab.g
    assert s.getPriceAndHasFeed(a)==(0,True)
    assert s.hasPriceFeed(a)
    assert g.desk.getPrice(a)==0
    with boa.reverts('has price config, no price'):
        g.desk.getPrice(a,True)


def isolated(lab):
    """Active feed whose read reverts: the desk isolates it as a failed source."""
    s,a,g=lab.s,lab.asset,lab.g
    with boa.reverts():
        s.getPriceAndHasFeed(a)
    assert s.hasPriceFeed(a)
    assert g.desk.getPrice(a)==0
    with boa.reverts('has price config, no price'):
        g.desk.getPrice(a,True)


def settings(config):
    """The governed settings of a config, in addNewPriceFeed argument order."""
    return (config.pool,config.twapWindow,config.maxObservationAge)
