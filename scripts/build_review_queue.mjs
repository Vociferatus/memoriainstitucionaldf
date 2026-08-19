import { readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const explorer = JSON.parse(await readFile(resolve(root, "web/public/dodf112.json"), "utf8"));
const identity = JSON.parse(await readFile(resolve(root, ".artifacts/pilot-db/DODF 112 22-06-2026 INTEGRA.identity.json"), "utf8"));
const fragments = new Map(identity.fragments.map((row) => [row.id, row]));

function evidence(blockId, start = null, end = null) {
  const block = explorer.blocks[blockId];
  if (!block) return null;
  return { block_id: block.id, page: block.page, bbox: block.bbox, start, end, text: block.text };
}

function stableSample(rows, count) {
  return [...rows].sort((a, b) => a.id.localeCompare(b.id)).filter((_, index) => index % Math.max(1, Math.floor(rows.length / count)) === 0).slice(0, count);
}

const queue = [];
for (const row of identity.resolution_cases) {
  queue.push({
    id: `review-${row.id}`,
    target: { layer: "identity", record_id: row.id },
    category: "identity_resolution",
    sample_kind: "critical",
    risk: "critical",
    priority: 100,
    question: "A decisão deve permanecer sem resolução?",
    proposal: row.recommended_decision,
    label: row.reason,
    reasons: ["identificador material inválido", ...row.divergences],
    evidence: row.fragment_ids.map((id) => fragments.get(id)).filter(Boolean).map((fragment) => evidence(fragment.block_id, fragment.start, fragment.end)).filter(Boolean),
  });
}

for (const row of identity.candidate_groups.slice(0, 20)) {
  queue.push({
    id: `review-${row.id}`,
    target: { layer: "identity", record_id: row.id },
    category: "identity_candidate",
    sample_kind: "high_risk",
    risk: "high",
    priority: 85,
    question: "Estes fragmentos devem permanecer separados?",
    proposal: row.decision,
    label: row.candidate_key,
    reasons: ["coincidência nominal sem identificador intransferível", ...row.missing_evidence],
    evidence: row.fragment_ids.map((id) => fragments.get(id)).filter(Boolean).map((fragment) => evidence(fragment.block_id, fragment.start, fragment.end)).filter(Boolean),
  });
}

for (const row of stableSample(explorer.entities, 12)) {
  queue.push({
    id: `review-${row.id}`,
    target: { layer: "semantic", record_id: row.id },
    category: "entity_mention",
    sample_kind: "random",
    risk: "medium",
    priority: 55,
    question: "O trecho representa o tipo de entidade proposto?",
    proposal: row.entity_type,
    label: row.name,
    reasons: ["amostra aleatória de precisão por tipo"],
    evidence: row.occurrences.slice(0, 2).map((occurrence) => evidence(occurrence.block_id, occurrence.start, occurrence.end)).filter(Boolean),
  });
}

for (const row of stableSample(explorer.actions, 12)) {
  queue.push({
    id: `review-${row.id}`,
    target: { layer: "semantic", record_id: row.id },
    category: "administrative_action",
    sample_kind: "random",
    risk: "medium",
    priority: 55,
    question: "A ação e seu participante estão corretamente representados?",
    proposal: row.verb,
    label: row.participant || row.value_original,
    reasons: ["amostra aleatória de ações administrativas"],
    evidence: [evidence(row.block_id, row.start, row.end)].filter(Boolean),
  });
}

for (const row of stableSample(explorer.items.filter((item) => item.end_page > item.start_page), 8)) {
  queue.push({
    id: `review-${row.id}`,
    target: { layer: "semantic", record_id: row.id },
    category: "published_item_boundary",
    sample_kind: "high_risk",
    risk: "high",
    priority: 75,
    question: "Os limites desta matéria multipágina estão corretos?",
    proposal: `${row.start_page}–${row.end_page}`,
    label: row.title,
    reasons: ["matéria multipágina", `${row.block_ids.length} blocos`],
    evidence: [evidence(row.block_ids[0]), evidence(row.block_ids.at(-1))].filter(Boolean),
  });
}

for (const row of stableSample(explorer.references, 8)) {
  queue.push({
    id: `review-${row.id}`,
    target: { layer: "semantic", record_id: row.id },
    category: "reference",
    sample_kind: "random",
    risk: row.valid === false ? "high" : "medium",
    priority: row.valid === false ? 78 : 45,
    question: "A referência foi localizada e normalizada corretamente?",
    proposal: row.reference_type,
    label: row.value_original,
    reasons: [row.valid === false ? "validação formal falhou" : "amostra aleatória de referências"],
    evidence: [evidence(row.block_id, row.start, row.end)].filter(Boolean),
  });
}

const occupied = new Set([
  ...explorer.entities.flatMap((row) => row.occurrences.map((occurrence) => occurrence.block_id)),
  ...explorer.actions.map((row) => row.block_id),
  ...explorer.references.map((row) => row.block_id),
  ...explorer.processes.flatMap((row) => row.occurrences.map((occurrence) => occurrence.block_id)),
]);
const negativeBlocks = Object.values(explorer.blocks).filter((block) => block.text.length >= 80 && !occupied.has(block.id));
for (const block of stableSample(negativeBlocks.map((row) => ({ ...row, id: row.id })), 8)) {
  queue.push({
    id: `review-negative-${block.id}`,
    target: { layer: "evidence", record_id: block.id },
    category: "negative_recall",
    sample_kind: "negative",
    risk: "high",
    priority: 70,
    question: "Há pessoa, organização, ação ou referência relevante omitida neste bloco?",
    proposal: "nenhuma omissão detectada",
    label: `Bloco ${block.id}`,
    reasons: ["amostra negativa para estimar omissões"],
    evidence: [evidence(block.id)],
  });
}

queue.sort((a, b) => b.priority - a.priority || a.id.localeCompare(b.id));
const counts = queue.reduce((result, row) => {
  result[row.risk] = (result[row.risk] || 0) + 1;
  return result;
}, {});

await writeFile(resolve(root, "web/public/dodf112-review-queue.json"), `${JSON.stringify({
  schema_version: "assisted-review-queue/1.0",
  generated_at: identity.created_at,
  source: explorer.document,
  policy: { name: "risk_based_assisted_review", version: "1.0", human_role: "decision_not_transcription" },
  counts: { total: queue.length, ...counts },
  queue,
}, null, 2)}\n`);
console.log(`Fila assistida: ${queue.length} decisões (${JSON.stringify(counts)})`);
