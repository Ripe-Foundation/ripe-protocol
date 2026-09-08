"""Shared public-state and unavailable-price assertions."""
import boa


def state(s,a):
    p=s.getPendingFeed(a)
    return (s.getFeedConfig(a),p,s.getBoundAssetDecimals(a),tuple(s.getPricedAssets()),s.numAssets(),s.indexOfAsset(a),s.hasPriceFeed(a),s.hasPendingPriceFeedUpdate(a),s.pendingActions(p.actionId),s.actionId())



def unavailable(lab):
    s,a,g=lab.s,lab.asset,lab.g
    assert s.getPriceAndHasFeed(a)==(0,True)
    assert s.hasPriceFeed(a)
    assert g.desk.getPrice(a)==0
    with boa.reverts('has price config, no price'):
        g.desk.getPrice(a,True)
