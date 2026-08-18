"""Estrutura PDFs textuais do DODF e gera Markdown auditavel.

O JSON estrutural e o artefato principal: preserva paginas, blocos, coordenadas
e ordem de leitura. O Markdown e uma visualizacao derivada para leitura humana.
PDFs compostos apenas por imagens precisam passar por OCR antes deste passo.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
import sys
from collections import Counter
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover - depende do ambiente
    fitz = None


SCRIPT_VERSION = "0.2.0"
SPACE_RE = re.compile(r"[ \t]+")
PAGE_NUMBER_RE = re.compile(r"^(?:pagina\s+)?\d+$", re.IGNORECASE)
RUNNING_HEADER_RE = re.compile(
    r"^P(?:A|Á)GINA\s+\d+\s+Di(?:a|á)rio Oficial do Distrito Federal\b",
    re.IGNORECASE,
)
SECTION_RE = re.compile(r"^SE(?:C|Ç)(?:A|Ã)O\s+[IVXLCDM]+$", re.IGNORECASE)


@dataclass(frozen=True)
class TextLine:
    order: int
    bbox: list[float]
    text_original: str
    text_normalized: str
    font_size: float
    bold: bool


@dataclass(frozen=True)
class TextBlock:
    id: str
    page: int
    order: int
    source_order: int
    column: int | None
    bbox: list[float]
    text_original: str
    text_normalized: str
    font_size: float
    bold: bool
    markdown_role: str
    removed_as_noise: bool
    noise_reason: str | None
    lines: list[TextLine]

    @property
    def x0(self) -> float:
        return self.bbox[0]

    @property
    def y0(self) -> float:
        return self.bbox[1]

    @property
    def x1(self) -> float:
        return self.bbox[2]

    @property
    def y1(self) -> float:
        return self.bbox[3]

    @property
    def width(self) -> float:
        return self.x1 - self.x0


def normalize_line(text: str) -> str:
    return SPACE_RE.sub(" ", text.replace("\u00a0", " ")).strip()


def join_lines(lines: list[str]) -> str:
    """Une linhas, mantendo hifens que pertencem a palavras compostas."""
    result = ""
    for raw_line in lines:
        line = normalize_line(raw_line)
        if not line:
            continue
        if result.endswith("-") and line[:1].islower():
            result = result[:-1] + line
        else:
            result += (" " if result else "") + line
    return result


def rounded_bbox(bbox: list[float] | tuple[float, float, float, float]) -> list[float]:
    return [round(float(value), 2) for value in bbox]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def create_manifest(input_path: Path) -> dict[str, Any]:
    stat = input_path.stat()
    return {
        "schema_version": "1.0",
        "created_at": utc_now(),
        "tool": {"name": Path(__file__).name, "version": SCRIPT_VERSION},
        "document": {
            "path": str(input_path),
            "filename": input_path.name,
            "size_bytes": stat.st_size,
            "modified_at": datetime.fromtimestamp(
                stat.st_mtime, timezone.utc
            ).replace(microsecond=0).isoformat(),
            "sha256": sha256_file(input_path),
            "media_type": "application/pdf",
        },
    }


def extract_blocks(document: "fitz.Document") -> tuple[list[dict[str, Any]], list[list[TextBlock]]]:
    page_metadata: list[dict[str, Any]] = []
    pages: list[list[TextBlock]] = []
    for page_number, page in enumerate(document, start=1):
        page_blocks: list[TextBlock] = []
        page_metadata.append(
            {
                "number": page_number,
                "width": round(float(page.rect.width), 2),
                "height": round(float(page.rect.height), 2),
                "rotation": page.rotation,
            }
        )
        data = page.get_text("dict", flags=fitz.TEXTFLAGS_TEXT)
        for source_order, raw_block in enumerate(data.get("blocks", []), start=1):
            if raw_block.get("type") != 0:
                continue

            block_lines: list[TextLine] = []
            spans = []
            for line_order, raw_line in enumerate(raw_block.get("lines", []), start=1):
                line_spans = [
                    span
                    for span in raw_line.get("spans", [])
                    if normalize_line(span.get("text", ""))
                ]
                if not line_spans:
                    continue
                spans.extend(line_spans)
                line_text = "".join(span.get("text", "") for span in raw_line.get("spans", []))
                line_sizes = [float(span.get("size", 0)) for span in line_spans]
                line_fonts = " ".join(str(span.get("font", "")) for span in line_spans)
                block_lines.append(
                    TextLine(
                        order=line_order,
                        bbox=rounded_bbox(raw_line["bbox"]),
                        text_original=line_text,
                        text_normalized=normalize_line(line_text),
                        font_size=statistics.median(line_sizes),
                        bold="bold" in line_fonts.lower(),
                    )
                )

            text_original = join_lines([line.text_original for line in block_lines])
            if not spans or not text_original:
                continue

            sizes = [float(span.get("size", 0)) for span in spans]
            fonts = " ".join(str(span.get("font", "")) for span in spans)
            block_id = f"p{page_number:04d}-b{source_order:04d}"
            page_blocks.append(
                TextBlock(
                    id=block_id,
                    page=page_number,
                    order=0,
                    source_order=source_order,
                    column=None,
                    bbox=rounded_bbox(raw_block["bbox"]),
                    text_original=text_original,
                    text_normalized=normalize_line(text_original),
                    font_size=statistics.median(sizes),
                    bold="bold" in fonts.lower(),
                    markdown_role="paragraph",
                    removed_as_noise=False,
                    noise_reason=None,
                    lines=block_lines,
                )
            )
        pages.append(page_blocks)
    return page_metadata, pages


def repeated_marginal_text(
    pages: list[list[TextBlock]], page_metadata: list[dict[str, Any]]
) -> set[str]:
    """Detecta textos repetidos nos 12% superiores/inferiores das paginas."""
    occurrences: Counter[str] = Counter()
    for blocks, metadata in zip(pages, page_metadata):
        height = float(metadata["height"])
        seen = {
            block.text_normalized.casefold()
            for block in blocks
            if block.y1 < height * 0.12 or block.y0 > height * 0.88
        }
        occurrences.update(seen)
    threshold = max(2, round(len(pages) * 0.30))
    return {text for text, count in occurrences.items() if count >= threshold}


def order_columns(blocks: list[TextBlock], split: float) -> list[TextBlock]:
    left = [block for block in blocks if (block.x0 + block.x1) / 2 < split]
    right = [block for block in blocks if block not in left]
    return sorted(left, key=lambda block: (block.y0, block.x0)) + sorted(
        right, key=lambda block: (block.y0, block.x0)
    )


def reading_order(blocks: list[TextBlock], page_width: float) -> list[TextBlock]:
    """Ordena blocos largos e blocos de coluna sem misturar as colunas."""
    full_width = [block for block in blocks if block.width >= page_width * 0.62]
    columns = [block for block in blocks if block.width < page_width * 0.62]
    if not columns:
        return sorted(full_width, key=lambda block: (block.y0, block.x0))

    split = page_width / 2
    ordered: list[TextBlock] = []
    remaining = list(columns)
    for wide in sorted(full_width, key=lambda block: block.y0):
        above = [block for block in remaining if block.y1 <= wide.y0]
        ordered.extend(order_columns(above, split))
        remaining = [block for block in remaining if block not in above]
        ordered.append(wide)
    ordered.extend(order_columns(remaining, split))
    return ordered


def markdown_role(block: TextBlock, body_size: float) -> str:
    text = block.text_normalized
    if SECTION_RE.fullmatch(text):
        return "h1"
    if block.font_size >= body_size * 1.45:
        return "h2"
    if block.bold and block.font_size >= body_size * 1.08 and len(text) <= 180:
        return "h3"
    return "paragraph"


def noise_reason(block: TextBlock, repeated: set[str]) -> str | None:
    text = block.text_normalized
    if text.casefold() in repeated:
        return "repeated_margin"
    if PAGE_NUMBER_RE.fullmatch(text):
        return "page_number"
    if RUNNING_HEADER_RE.match(text):
        return "running_header"
    return None


def enrich_blocks(
    pages: list[list[TextBlock]], page_metadata: list[dict[str, Any]]
) -> tuple[list[list[TextBlock]], float]:
    repeated = repeated_marginal_text(pages, page_metadata)
    body_sizes = [
        block.font_size
        for blocks in pages
        for block in blocks
        if len(block.text_normalized) >= 40
    ]
    body_size = statistics.median(body_sizes) if body_sizes else 10.0

    enriched_pages: list[list[TextBlock]] = []
    for blocks, metadata in zip(pages, page_metadata):
        page_width = float(metadata["width"])
        ordered = reading_order(blocks, page_width)
        enriched_blocks: list[TextBlock] = []
        split = page_width / 2
        for order, block in enumerate(ordered, start=1):
            reason = noise_reason(block, repeated)
            column = 0 if block.width >= page_width * 0.62 else int((block.x0 + block.x1) / 2 >= split) + 1
            enriched_blocks.append(
                replace(
                    block,
                    order=order,
                    column=column,
                    markdown_role=markdown_role(block, body_size),
                    removed_as_noise=reason is not None,
                    noise_reason=reason,
                )
            )
        enriched_pages.append(enriched_blocks)
    return enriched_pages, body_size


def structured_document(input_path: Path) -> dict[str, Any]:
    if fitz is None:
        raise RuntimeError(
            "PyMuPDF nao esta instalado. Execute: pip install -r requirements.txt"
        )

    with fitz.open(input_path) as document:
        if document.needs_pass:
            raise ValueError("O PDF e protegido por senha.")
        page_metadata, raw_pages = extract_blocks(document)
        pdf_metadata = dict(document.metadata or {})

    if not any(raw_pages):
        raise ValueError("O PDF nao contem texto extraivel; aplique OCR primeiro.")

    pages, body_size = enrich_blocks(raw_pages, page_metadata)
    manifest = create_manifest(input_path)
    manifest["document"]["page_count"] = len(page_metadata)

    return {
        "schema_version": "1.0",
        "created_at": utc_now(),
        "tool": {"name": Path(__file__).name, "version": SCRIPT_VERSION},
        "source": manifest["document"],
        "pdf_metadata": pdf_metadata,
        "processing": {
            "body_font_size": round(float(body_size), 3),
            "noise_filters": ["repeated_margin", "page_number", "running_header"],
            "reading_order": "wide-blocks-interleaved-with-two-column-order",
        },
        "pages": [
            {
                **metadata,
                "blocks": [
                    {
                        **asdict(block),
                        "lines": [asdict(line) for line in block.lines],
                    }
                    for block in blocks
                ],
            }
            for metadata, blocks in zip(page_metadata, pages)
        ],
    }


def markdown_for_block(block: dict[str, Any]) -> str:
    text = block["text_normalized"].strip()
    role = block["markdown_role"]
    if role == "h1":
        return f"# {text}"
    if role == "h2":
        return f"## {text}"
    if role == "h3":
        return f"### {text}"
    return text


def markdown_from_structure(structure: dict[str, Any], page_markers: bool = False) -> str:
    output: list[str] = []
    for page in structure["pages"]:
        if page_markers:
            output.append(f"<!-- pagina {page['number']} -->")
        for block in page["blocks"]:
            if block["removed_as_noise"]:
                continue
            item = markdown_for_block(block)
            if item:
                output.append(item)
    return "\n\n".join(output).rstrip() + "\n"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def default_output_paths(input_path: Path, markdown_path: Path | None) -> dict[str, Path]:
    stem = input_path.stem
    if markdown_path is None:
        markdown_path = Path("data/markdown") / f"{stem}.md"
    return {
        "manifest": Path("data/manifests") / f"{stem}.manifest.json",
        "structured": Path("data/structured") / f"{stem}.structured.json",
        "markdown": markdown_path,
    }


def convert_pdf(
    input_path: Path,
    markdown_path: Path | None = None,
    page_markers: bool = False,
    manifest_path: Path | None = None,
    structured_path: Path | None = None,
) -> dict[str, Path | int]:
    paths = default_output_paths(input_path, markdown_path)
    if manifest_path is not None:
        paths["manifest"] = manifest_path
    if structured_path is not None:
        paths["structured"] = structured_path

    structure = structured_document(input_path)
    manifest = {
        "schema_version": "1.0",
        "created_at": utc_now(),
        "tool": structure["tool"],
        "document": structure["source"],
        "derived_outputs": {
            "structured_json": str(paths["structured"]),
            "markdown": str(paths["markdown"]),
        },
    }

    write_json(paths["manifest"], manifest)
    write_json(paths["structured"], structure)
    write_text(paths["markdown"], markdown_from_structure(structure, page_markers))

    return {
        "pages": len(structure["pages"]),
        "manifest": paths["manifest"],
        "structured": paths["structured"],
        "markdown": paths["markdown"],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Estrutura um PDF textual do DODF e gera Markdown."
    )
    parser.add_argument("input", type=Path, help="arquivo PDF de entrada")
    parser.add_argument(
        "output",
        type=Path,
        nargs="?",
        help="arquivo Markdown (padrao: data/markdown/<nome>.md)",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        help="caminho do manifesto JSON (padrao: data/manifests/<nome>.manifest.json)",
    )
    parser.add_argument(
        "--structured",
        type=Path,
        help="caminho do JSON estrutural (padrao: data/structured/<nome>.structured.json)",
    )
    parser.add_argument(
        "--page-markers",
        action="store_true",
        help="inclui comentarios HTML indicando o inicio de cada pagina no Markdown",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    input_path = args.input.resolve()
    output_path = args.output.resolve() if args.output else None
    if not input_path.is_file():
        print(f"Erro: arquivo nao encontrado: {input_path}", file=sys.stderr)
        return 2
    try:
        result = convert_pdf(
            input_path=input_path,
            markdown_path=output_path,
            page_markers=args.page_markers,
            manifest_path=args.manifest,
            structured_path=args.structured,
        )
    except (RuntimeError, ValueError, OSError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1
    print(f"Convertidas {result['pages']} paginas")
    print(f"Manifesto: {result['manifest']}")
    print(f"JSON estrutural: {result['structured']}")
    print(f"Markdown: {result['markdown']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
