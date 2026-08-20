from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ZERO_ADDRESS = "0x" + "0" * 40
ETH = "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
MIGRATION = ROOT / "migrations/robinhood-mainnet/0003_PriceSources.py"


def _load_price_sources():
    spec = importlib.util.spec_from_file_location("price_sources_0003", MIGRATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PRICE_SOURCES = _load_price_sources()


class _AssetConfig:
    def __init__(self, is_nft=False):
        self.isNft = is_nft


class _MissionControl:
    def __init__(self, assets):
        # index 0 is unused, matching MissionControl.numAssets = 1 at init
        self._assets = {0: ZERO_ADDRESS}
        self._configs = {}
        for index, (asset, is_nft) in enumerate(assets, start=1):
            self._assets[index] = asset
            self._configs[asset.lower()] = _AssetConfig(is_nft)

    def numAssets(self):
        return len(self._assets)

    def assets(self, index):
        return self._assets[index]

    def assetConfig(self, asset):
        return self._configs[str(asset).lower()]


class _PriceDesk:
    def __init__(self):
        self.scales = {}
        self.synced = []

    def syncTokenScale(self, asset):
        self.synced.append(str(asset).lower())
        if str(asset).lower() not in self.scales:
            self.scales[str(asset).lower()] = 10**18
        return True

    def tokenScale(self, asset):
        return self.scales.get(str(asset).lower(), 0)


def _execute(fn, *args):
    return fn(*args)


def test_bootstrap_enumerates_mission_control_live_assets_and_sets_nonzero_scale():
    weth = "0x0000000000000000000000000000000000000001"
    ripe = "0x0000000000000000000000000000000000000002"
    sgreen = "0x0000000000000000000000000000000000000003"
    green = "0x0000000000000000000000000000000000000004"
    extra_a = "0x0000000000000000000000000000000000000005"
    extra_b = "0x0000000000000000000000000000000000000006"
    nft = "0x0000000000000000000000000000000000000007"

    mission_control = _MissionControl(
        [
            (ETH, False),
            (weth, False),
            (ripe, False),
            (sgreen, False),
            (green, False),
            (extra_a, False),
            (nft, True),
            (extra_b, False),
        ]
    )
    price_desk = _PriceDesk()

    PRICE_SOURCES.sync_existing_token_scales(
        _execute,
        price_desk,
        mission_control,
        ETH,
    )

    synced = set(price_desk.synced)
    assert ETH not in synced
    assert nft.lower() not in synced
    expected = {weth, ripe, sgreen, green, extra_a, extra_b}
    assert synced == expected
    for asset in expected:
        assert price_desk.tokenScale(asset) != 0
    assert price_desk.tokenScale(ETH) == 0
    assert price_desk.tokenScale(nft) == 0


def test_bootstrap_reads_live_mission_control_list_before_price_desk_promotion():
    source = MIGRATION.read_text()
    assert "sync_existing_token_scales(" in source
    assert "for index in range(1, num_assets)" in source
    assert "mission_control.assets(index)" in source or "mission_control.assets(" in source
    assert "numAssets()" in source
    assert source.index("sync_existing_token_scales(") < source.index(
        'hq.startAddNewAddressToRegistry, price_desk, "PriceDesk"'
    )
    assert "0x0Bd7D308f8E1639FAb988df18A8011f41EAcAD73" not in source
    assert "0x2A0a59d6B975828e781EcaC125dBA40d7ee5dDC0" not in source
