"""Shared reference vectors and laboratory settings for worker and launcher."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
VECTORS=json.loads((ROOT/'docs/priceSources/uniswap-v3-twap-reference-vectors.json').read_text())
LAB={'minCurrentLiquidity':1,'minHarmonicLiquidity':1,'maxObservationAgeSeconds':3600,'quoteStaleTime':0,'localGraphGlobalQuoteAge':86400}
