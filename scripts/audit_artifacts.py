"""Wrapper compatível para o auditor histórico."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from min_df.audit_artifacts import main

if __name__ == "__main__":
    raise SystemExit(main())
