"""Shared reference vectors and laboratory settings for worker and launcher."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
VECTORS=json.loads((ROOT/'docs/priceSources/uniswap-v3-twap-reference-vectors.json').read_text())
LAB={'minLiquidityRatio':50_00,'minObservationCardinality':500,'maxObservationAge':3600,'localGraphGlobalStaleTime':86400}
