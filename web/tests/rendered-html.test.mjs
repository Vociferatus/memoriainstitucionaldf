import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);
  return worker.fetch(
    new Request("http://localhost/", { headers: { accept: "text/html" } }),
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
