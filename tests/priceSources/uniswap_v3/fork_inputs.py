"""Shared reference vectors and laboratory settings for worker and launcher."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
VECTORS=json.loads((ROOT/'docs/priceSources/uniswap-v3-twap-reference-vectors.json').read_text())
LAB={'twapWindow':3600,'maxObservationAge':1800,'minLiquidityRatio':50_00,'localGraphGlobalStaleTime':86400}
# Updated only from a fresh, fully captured run of the current reference model.
FRESH_FIXTURE=Path(__file__).parent/'fixtures/fresh-58962463.json'
