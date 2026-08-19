import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

async function render(path = "/") {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);
  return worker.fetch(
    new Request(`http://localhost${path}`, { headers: { accept: "text/html" } }),
    { ASSETS: { fetch: async () => new Response("Not found", { status: 404 }) } },
    { waitUntil() {}, passThroughOnException() {} },
  );
}

test("renders the DODF evidence explorer", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  const html = await response.text();
  assert.match(html, /Explorador DODF 112/);
  assert.match(html, /Memória Institucional/);
  assert.match(html, /Organizando o Diário Oficial/);
  assert.doesNotMatch(html, /codex-preview|SkeletonPreview/);
});

test("ships a coherent pilot dataset", async () => {
  const payload = JSON.parse(
    await readFile(new URL("../public/dodf112.json", import.meta.url), "utf8"),
  );
  assert.equal(payload.items.length, 457);
  assert.equal(payload.document.pages, 85);
  assert.equal(payload.document.counts.unclassified_items, 0);
  assert.equal(payload.processes.length, 1096);
  assert.ok(payload.blocks["p0001-b0043"]);
});

test("renders the blind human annotation route", async () => {
  const response = await render("/anotar");
  assert.equal(response.status, 200);
  const html = await response.text();
  assert.match(html, /Anote o que a página permite observar/);
  assert.match(html, /MODO CEGO ATIVO/);
  assert.match(html, /As classificações automáticas estão ocultas/);
});

test("ships only source locators for frozen calibration pages", async () => {
  const raw = await readFile(
    new URL("../public/dodf112-calibration.json", import.meta.url),
    "utf8",
  );
  const payload = JSON.parse(raw);
  assert.deepEqual(payload.scope.pages, [37, 51]);
  assert.deepEqual(payload.pages.map((page) => page.blocks.length), [7, 15]);
  assert.doesNotMatch(
    raw,
    /"(?:entities|actions|references|item_type|markdown_role|removed_as_noise)"/,
  );
  assert.equal(payload.source.document_sha256.length, 64);
});

test("renders the risk-based assisted review route", async () => {
  const response = await render("/revisar");
  assert.equal(response.status, 200);
  const html = await response.text();
  assert.match(html, /Revisão assistida/);
  assert.match(html, /Calculando prioridades de revisão/);
});

test("ships a bounded and stratified assisted review queue", async () => {
  const payload = JSON.parse(
    await readFile(new URL("../public/dodf112-review-queue.json", import.meta.url), "utf8"),
  );
  assert.equal(payload.queue.length, 69);
  assert.equal(payload.counts.critical, 1);
  assert.equal(payload.counts.high, 36);
  assert.equal(payload.counts.medium, 32);
  assert.ok(payload.queue.some((row) => row.sample_kind === "negative"));
  assert.ok(payload.queue.every((row) => row.evidence.length > 0));
  assert.ok(payload.queue.every((row) => row.reasons.length > 0));
});
