import { readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const input = resolve(
  root,
  "data/structured/DODF 112 22-06-2026 INTEGRA.structured.json",
);
const output = resolve(root, "web/public/dodf112-calibration.json");
const calibrationPages = new Set([37, 51]);

const structured = JSON.parse(await readFile(input, "utf8"));
const pages = structured.pages
  .filter((page) => calibrationPages.has(page.number))
  .map((page) => ({
    number: page.number,
    width: page.width,
    height: page.height,
    image: `/calibration/dodf112-page-${page.number}.png`,
    blocks: page.blocks.map((block) => ({
      id: block.id,
      page: block.page,
      order: block.order,
      bbox: block.bbox,
      text: block.text_original,
    })),
  }));

if (pages.length !== calibrationPages.size) {
  throw new Error("As páginas congeladas 37 e 51 não foram localizadas.");
}

const payload = {
  schema_version: "calibration-source/1.0",
  protocol: {
    name: "dodf_human_annotation",
    version: "1.0",
    guide_uri: "repo:///docs/ANNOTATION_GUIDE_DODF.md",
  },
  source: {
    document_key: "dodf:2026-06-22:edicao-112:integra",
    document_filename: structured.source.filename,
    document_sha256: structured.source.sha256,
    page_count: structured.source.page_count,
    baseline_commit: "1a6f37b5a3eca2439a7663184f699e808d6646c6",
  },
  scope: {
    pages: [37, 51],
    selection_method: "calibration_pages_37_51_v1",
  },
  pages,
};

await writeFile(output, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
console.log(`Dataset cego gravado em ${output}`);
