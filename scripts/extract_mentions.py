"""Wrapper compatível para o extrator histórico."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from min_df.extract_mentions import main

if __name__ == "__main__":
    raise SystemExit(main())
