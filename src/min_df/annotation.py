"""Validação de lotes imutáveis de anotação humana."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from min_df.contracts import ContractValidationError, validate_human_annotation


def read_annotation(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ContractValidationError(f"Arquivo de anotação não encontrado: {path}") from None
    except json.JSONDecodeError as exc:
        raise ContractValidationError(f"JSON de anotação inválido em {path}: {exc}") from exc


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Valida um lote de anotação humana.")
    parser.add_argument("annotation", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        payload = read_annotation(args.annotation)
        validate_human_annotation(payload)
    except ContractValidationError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    print("Anotação válida")
    print(f"lote: {payload['annotation_batch_id']}")
    print(f"modo: {payload['annotator']['mode']}")
    print(f"páginas: {len(payload['scope']['pages'])}")
    print(f"registros: {len(payload['records'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
