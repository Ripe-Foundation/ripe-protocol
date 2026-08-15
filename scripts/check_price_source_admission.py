#!/usr/bin/env python3
"""Validate the canonical Robinhood PriceDesk admission manifest."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.price_source_admission import DEFAULT_MANIFEST, load_manifest


def main() -> int:
    load_manifest()
    print(f"PriceDesk admission manifest OK: {DEFAULT_MANIFEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
