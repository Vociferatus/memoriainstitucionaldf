"use client";

import { useEffect, useMemo, useState } from "react";
import Image from "next/image";
import Link from "next/link";

type Mode = "blind_primary" | "independent_second";
type Judgment = "PRESENT" | "AMBIGUOUS";
type Confidence = "certain" | "probable" | "uncertain";
type TaskType =
  | "document_structure"
  | "published_item_boundary"
  | "editorial_context"
  | "entity_mention"
  | "administrative_action"
  | "reference"
  | "temporal_assertion";

type SourceBlock = {
  id: string;
  page: number;
  order: number;
  bbox: number[];
  text: string;
};

type CalibrationPage = {
  number: number;
  width: number;
  height: number;
  image: string;
  blocks: SourceBlock[];
};

type CalibrationData = {
  schema_version: string;
  protocol: { name: string; version: string; guide_uri: string };
  source: {
    document_key: string;
    document_filename: string;
    document_sha256: string;
    page_count: number;
    baseline_commit: string;
  };
  scope: { pages: number[]; selection_method: string };
  pages: CalibrationPage[];
};

type Evidence = {
  document_sha256: string;
  page: number;
  block_id: string;
  start: number | null;
  end: number | null;
  bbox: number[];
  quote: string;
};

type AnnotationRecord = {
  id: string;
  annotation_type: "observation";
  task_type: TaskType;
  judgment: Judgment;
  target: null;
  evidence: Evidence[];
  payload: {
    observed_type: string | null;
    label: string | null;
    role: string | null;
    value_original: string | null;
    value_normalized: string | null;
    start_block_id: string | null;
    end_block_id: string | null;
    date_type: "publication" | "signature" | "validity" | "effect" | null;
    date_value: string | null;
    fragment_ids: string[];
    decision: null;
    attributes: Record<string, never>;
  };
  confidence: Confidence;
  rationale: string | null;
  error_categories: [];
  notes: string | null;
};

const taskLabels: Record<TaskType, string> = {
  document_structure: "Estrutura do documento",
  published_item_boundary: "Limite de matéria",
  editorial_context: "Contexto editorial",
  entity_mention: "Menção de entidade",
  administrative_action: "Ação administrativa",
  reference: "Referência",
  temporal_assertion: "Afirmação temporal",
};

const observedSuggestions: Record<TaskType, string[]> = {
  document_structure: [
    "section_heading",
    "running_header",
    "footer",
    "column",
    "table",
    "image",
    "noise",
    "reading_order_failure",
  ],
  published_item_boundary: ["published_item"],
  editorial_context: ["editorial_context"],
  entity_mention: [
    "person",
    "organization",
    "legal_organization",
    "position",
    "process",
    "norm",
  ],
  administrative_action: ["administrative_action"],
  reference: [
    "cnpj",
    "process",
    "norm",
    "legal_provision",
    "monetary_value",
    "instrument",
  ],
  temporal_assertion: ["publication", "signature", "validity", "effect"],
};

const draftKey = "dodf112-calibration-blind-draft-v1";

function nullable(value: string) {
  return value.trim() || null;
}

function safeReviewer(value: string) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "") || "reviewer";
}

export default function BlindAnnotationPage() {
  const [data, setData] = useState<CalibrationData | null>(null);
  const [loadError, setLoadError] = useState("");
  const [pageNumber, setPageNumber] = useState(37);
  const [selectedBlockId, setSelectedBlockId] = useState("");
  const [reviewer, setReviewer] = useState("");
  const [mode, setMode] = useState<Mode>("blind_primary");
  const [records, setRecords] = useState<AnnotationRecord[]>([]);
  const [hydrated, setHydrated] = useState(false);

  const [taskType, setTaskType] = useState<TaskType>("entity_mention");
  const [judgment, setJudgment] = useState<Judgment>("PRESENT");
  const [confidence, setConfidence] = useState<Confidence>("certain");
  const [observedType, setObservedType] = useState("");
  const [label, setLabel] = useState("");
  const [role, setRole] = useState("");
  const [valueOriginal, setValueOriginal] = useState("");
  const [valueNormalized, setValueNormalized] = useState("");
  const [dateType, setDateType] = useState<
    "publication" | "signature" | "validity" | "effect"
  >("publication");
  const [dateValue, setDateValue] = useState("");
  const [rationale, setRationale] = useState("");
  const [notes, setNotes] = useState("");
  const [quote, setQuote] = useState("");
  const [spanStart, setSpanStart] = useState("");
  const [spanEnd, setSpanEnd] = useState("");
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [message, setMessage] = useState("");

  useEffect(() => {
    fetch("/dodf112-calibration.json")
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
      })
      .then((payload: CalibrationData) => setData(payload))
      .catch(() =>
        setLoadError("Não foi possível abrir o pacote de calibração."),
      );

    const restoreDraft = window.setTimeout(() => {
      try {
        const stored = localStorage.getItem(draftKey);
        if (stored) {
          const draft = JSON.parse(stored) as {
            reviewer?: string;
            mode?: Mode;
            records?: AnnotationRecord[];
          };
          setReviewer(draft.reviewer ?? "");
          setMode(draft.mode ?? "blind_primary");
          setRecords(draft.records ?? []);
        }
      } catch {
        localStorage.removeItem(draftKey);
      } finally {
        setHydrated(true);
      }
    }, 0);

    return () => window.clearTimeout(restoreDraft);
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    localStorage.setItem(draftKey, JSON.stringify({ reviewer, mode, records }));
  }, [hydrated, mode, records, reviewer]);

  const currentPage = useMemo(
    () => data?.pages.find((page) => page.number === pageNumber) ?? null,
    [data, pageNumber],
  );
  const selectedBlock = useMemo(
    () =>
      data?.pages
        .flatMap((page) => page.blocks)
        .find((block) => block.id === selectedBlockId) ?? null,
    [data, selectedBlockId],
  );

  function chooseBlock(block: SourceBlock) {
    setSelectedBlockId(block.id);
    setQuote("");
    setSpanStart("");
    setSpanEnd("");
    setMessage("");
  }

  function useWholeBlock() {
    if (!selectedBlock) return;
    setQuote(selectedBlock.text);
    setSpanStart("0");
    setSpanEnd(String(selectedBlock.text.length));
  }

  function addEvidence() {
    if (!data || !selectedBlock) {
      setMessage("Selecione um bloco da página antes de adicionar evidência.");
      return;
    }
    if (!quote.trim()) {
      setMessage("Copie a citação mínima que sustenta a observação.");
      return;
    }

    const hasStart = spanStart.trim() !== "";
    const hasEnd = spanEnd.trim() !== "";
    if (hasStart !== hasEnd) {
      setMessage("Informe início e fim do span juntos, ou deixe ambos vazios.");
      return;
    }

    const start = hasStart ? Number(spanStart) : null;
    const end = hasEnd ? Number(spanEnd) : null;
    if (
      start !== null &&
      end !== null &&
      (!Number.isInteger(start) ||
        !Number.isInteger(end) ||
        start < 0 ||
        end <= start ||
        end > selectedBlock.text.length)
    ) {
      setMessage("O span precisa estar dentro do bloco e ter fim maior que início.");
      return;
    }
    if (
      start !== null &&
      end !== null &&
      selectedBlock.text.slice(start, end) !== quote.trim()
    ) {
      setMessage("A citação precisa coincidir exatamente com o span informado.");
      return;
    }

    setEvidence((current) => [
      ...current,
      {
        document_sha256: data.source.document_sha256,
        page: selectedBlock.page,
        block_id: selectedBlock.id,
        start,
        end,
        bbox: selectedBlock.bbox,
        quote: quote.trim(),
      },
    ]);
    setQuote("");
    setSpanStart("");
    setSpanEnd("");
    setMessage("Evidência adicionada ao registro em preparação.");
  }

  function addRecord() {
    if (!observedType.trim()) {
      setMessage("Defina o tipo observado antes de registrar.");
      return;
    }
    if (!evidence.length) {
      setMessage("Adicione ao menos uma evidência antes de registrar.");
      return;
    }
    if (judgment === "AMBIGUOUS" && !rationale.trim()) {
      setMessage("Uma observação ambígua exige justificativa.");
      return;
    }
    if (taskType === "temporal_assertion" && dateValue && !/^\d{4}-\d{2}-\d{2}$/.test(dateValue)) {
      setMessage("Use o formato AAAA-MM-DD para a data observada.");
      return;
    }

    const record: AnnotationRecord = {
      id: `annotation-${String(records.length + 1).padStart(4, "0")}-${Date.now().toString(36)}`,
      annotation_type: "observation",
      task_type: taskType,
      judgment,
      target: null,
      evidence,
      payload: {
        observed_type: nullable(observedType),
        label: nullable(label),
        role: nullable(role),
        value_original: nullable(valueOriginal),
        value_normalized: nullable(valueNormalized),
        start_block_id:
          taskType === "published_item_boundary"
            ? evidence.at(0)?.block_id ?? null
            : null,
        end_block_id:
          taskType === "published_item_boundary"
            ? evidence.at(-1)?.block_id ?? null
            : null,
        date_type: taskType === "temporal_assertion" ? dateType : null,
        date_value: taskType === "temporal_assertion" ? nullable(dateValue) : null,
        fragment_ids: [],
        decision: null,
        attributes: {},
      },
      confidence,
      rationale: nullable(rationale),
      error_categories: [],
      notes: nullable(notes),
    };

    setRecords((current) => [...current, record]);
    setEvidence([]);
    setObservedType("");
    setLabel("");
    setRole("");
    setValueOriginal("");
    setValueNormalized("");
    setDateValue("");
    setRationale("");
    setNotes("");
    setJudgment("PRESENT");
    setConfidence("certain");
    setMessage("Observação registrada no rascunho local.");
  }

  function exportBatch() {
    if (!data) return;
    if (!reviewer.trim()) {
      setMessage("Informe o identificador do revisor antes de exportar.");
      return;
    }
    if (!records.length) {
      setMessage("Registre ao menos uma observação antes de exportar.");
      return;
    }

    const createdAt = new Date().toISOString();
    const batchId = [
      "dodf112-calibration",
      mode,
      safeReviewer(reviewer),
      createdAt.replace(/[-:.TZ]/g, "").toLowerCase(),
    ].join("-");
    const payload = {
      schema_version: "1.0",
      annotation_batch_id: batchId,
      created_at: createdAt,
      protocol: data.protocol,
      annotator: { id: reviewer.trim(), kind: "human", mode },
      source: { ...data.source, automatic_artifacts: [] },
      scope: {
        pages: data.scope.pages,
        selection_method: data.scope.selection_method,
        pass_number: mode === "blind_primary" ? 1 : 2,
        parent_batch_ids: [],
      },
      records,
    };

    const blob = new Blob([`${JSON.stringify(payload, null, 2)}\n`], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${batchId}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
    setMessage("Lote exportado. Valide o JSON antes de considerá-lo fechado.");
  }

  function discardDraft() {
    if (!window.confirm("Descartar todas as observações deste dispositivo?")) return;
    setRecords([]);
    setEvidence([]);
    localStorage.removeItem(draftKey);
    setMessage("Rascunho local descartado.");
  }

  if (loadError) {
    return (
      <main className="annotation-loading">
        <div className="brand-mark">DF</div>
        <h1>Anotação cega</h1>
        <p>{loadError}</p>
        <Link href="/">Voltar ao explorador</Link>
      </main>
    );
  }

  return (
    <main className="annotation-page">
      <header className="annotation-topbar">
        <div className="annotation-brand">
          <span className="brand-mark">DF</span>
          <span>
            <strong>Memória Institucional</strong>
            <small>Protocolo de referência humana</small>
          </span>
        </div>
        <div className="blind-badge">
          <i aria-hidden="true" /> MODO CEGO ATIVO
        </div>
        <button className="primary-action" onClick={exportBatch}>
          Exportar lote JSON
        </button>
      </header>

      <section className="annotation-hero">
        <div>
          <p className="eyebrow">CALIBRAÇÃO · PORTÃO 1</p>
          <h1>Anote o que a página permite observar.</h1>
          <p>
            As classificações automáticas estão ocultas. O PDF é a fonte primária;
            os blocos servem somente para localizar evidências.
          </p>
        </div>
        <dl>
          <div>
            <dt>Escopo congelado</dt>
            <dd>páginas 37 e 51</dd>
          </div>
          <div>
            <dt>Contrato de saída</dt>
            <dd>human-annotation/1.0</dd>
          </div>
          <div>
            <dt>Registros no rascunho</dt>
            <dd>{records.length}</dd>
          </div>
        </dl>
      </section>

      <section className="protocol-strip" aria-label="Regras do protocolo">
        <span><b>01</b> Observe sem inferir identidade</span>
        <span><b>02</b> Cite a evidência mínima</span>
        <span><b>03</b> Preserve toda ambiguidade</span>
        <span><b>04</b> Exporte um lote imutável</span>
      </section>

      <section className="reviewer-panel">
        <label>
          Identificador do revisor
          <input
            value={reviewer}
            onChange={(event) => setReviewer(event.target.value)}
            placeholder="Ex.: revisor-paulo-01"
          />
        </label>
        <label>
          Aplicação independente
          <select
            value={mode}
            disabled={records.length > 0}
            onChange={(event) => setMode(event.target.value as Mode)}
          >
            <option value="blind_primary">Primeira aplicação cega</option>
            <option value="independent_second">Segunda aplicação independente</option>
          </select>
          {records.length > 0 && <small>Descarte o rascunho para trocar de aplicação.</small>}
        </label>
        <p>
          O rascunho é salvo somente neste dispositivo. Não abra o explorador
          automático durante esta aplicação.
        </p>
      </section>

      {!data || !currentPage ? (
        <section className="annotation-loading">
          <div className="brand-mark">DF</div>
          <p>Preparando páginas e referências de bloco…</p>
        </section>
      ) : (
        <section className="annotation-workspace">
          <div className="source-column">
            <div className="source-toolbar">
              <div>
                <p className="eyebrow">FONTE PRIMÁRIA</p>
                <h2>{data.source.document_filename}</h2>
              </div>
              <div className="page-tabs" aria-label="Páginas da calibração">
                {data.scope.pages.map((page) => (
                  <button
                    className={pageNumber === page ? "active" : ""}
                    key={page}
                    onClick={() => setPageNumber(page)}
                  >
                    Página {page}
                  </button>
                ))}
              </div>
            </div>

            <figure className="document-sheet">
              <Image
                src={currentPage.image}
                alt={`Página ${currentPage.number} do DODF 112`}
                width={currentPage.width * 2}
                height={currentPage.height * 2}
                priority
                unoptimized
              />
              <figcaption>
                Página {currentPage.number} · imagem integral preservada · SHA-256{" "}
                <code>{data.source.document_sha256.slice(0, 16)}…</code>
              </figcaption>
            </figure>

            <section className="block-locator">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">LOCALIZADOR DE EVIDÊNCIA</p>
                  <h2>{currentPage.blocks.length} blocos na página {pageNumber}</h2>
                </div>
                <p>Sem tipos, entidades ou ações automáticas.</p>
              </div>
              <div className="block-list">
                {currentPage.blocks.map((block) => (
                  <button
                    className={selectedBlockId === block.id ? "selected" : ""}
                    key={block.id}
                    onClick={() => chooseBlock(block)}
                  >
                    <span>{block.id}</span>
                    <p>{block.text}</p>
                    <small>
                      ordem {block.order} · bbox {block.bbox.map((n) => n.toFixed(1)).join(" · ")}
                    </small>
                  </button>
                ))}
              </div>
            </section>
          </div>

          <aside className="annotation-form">
            <div className="form-heading">
              <p className="eyebrow">NOVA OBSERVAÇÃO</p>
              <h2>Registre sem comparar.</h2>
              <span>{evidence.length} evidência(s) preparada(s)</span>
            </div>

            <fieldset>
              <legend>1. Tarefa e julgamento</legend>
              <label>
                Tarefa
                <select
                  value={taskType}
                  onChange={(event) => {
                    setTaskType(event.target.value as TaskType);
                    setObservedType("");
                  }}
                >
                  {(Object.keys(taskLabels) as TaskType[]).map((key) => (
                    <option key={key} value={key}>{taskLabels[key]}</option>
                  ))}
                </select>
              </label>
              <div className="two-fields">
                <label>
                  Julgamento
                  <select value={judgment} onChange={(event) => setJudgment(event.target.value as Judgment)}>
                    <option value="PRESENT">Presente</option>
                    <option value="AMBIGUOUS">Ambíguo</option>
                  </select>
                </label>
                <label>
                  Confiança
                  <select value={confidence} onChange={(event) => setConfidence(event.target.value as Confidence)}>
                    <option value="certain">Certa</option>
                    <option value="probable">Provável</option>
                    <option value="uncertain">Incerta</option>
                  </select>
                </label>
              </div>
              <label>
                Tipo observado
                <input
                  value={observedType}
                  onChange={(event) => setObservedType(event.target.value)}
                  placeholder="Selecione abaixo ou descreva"
                />
              </label>
              <div className="suggestion-chips">
                {observedSuggestions[taskType].map((suggestion) => (
                  <button key={suggestion} onClick={() => setObservedType(suggestion)}>
                    {suggestion}
                  </button>
                ))}
              </div>
            </fieldset>

            <fieldset>
              <legend>2. Evidência material</legend>
              {!selectedBlock ? (
                <p className="form-hint">Selecione um bloco no localizador ao lado.</p>
              ) : (
                <>
                  <div className="selected-block">
                    <b>{selectedBlock.id}</b>
                    <span>página {selectedBlock.page}</span>
                    <button onClick={useWholeBlock}>Usar bloco inteiro</button>
                  </div>
                  <label>
                    Citação mínima
                    <textarea
                      value={quote}
                      onChange={(event) => setQuote(event.target.value)}
                      rows={4}
                      placeholder="Copie apenas o trecho que sustenta a observação."
                    />
                  </label>
                  <div className="two-fields">
                    <label>
                      Início do span
                      <input inputMode="numeric" value={spanStart} onChange={(event) => setSpanStart(event.target.value)} placeholder="opcional" />
                    </label>
                    <label>
                      Fim do span
                      <input inputMode="numeric" value={spanEnd} onChange={(event) => setSpanEnd(event.target.value)} placeholder="opcional" />
                    </label>
                  </div>
                  <button className="secondary-action" onClick={addEvidence}>
                    Adicionar evidência
                  </button>
                </>
              )}

              {evidence.length > 0 && (
                <ol className="evidence-queue">
                  {evidence.map((item, index) => (
                    <li key={`${item.block_id}-${index}`}>
                      <span>p. {item.page} · {item.block_id}</span>
                      <p>{item.quote}</p>
                      <button onClick={() => setEvidence((current) => current.filter((_, position) => position !== index))}>
                        remover
                      </button>
                    </li>
                  ))}
                </ol>
              )}
            </fieldset>

            <fieldset>
              <legend>3. Conteúdo observado</legend>
              <label>
                Rótulo literal
                <input value={label} onChange={(event) => setLabel(event.target.value)} placeholder="nome, título ou denominação" />
              </label>
              <label>
                Papel no texto
                <input value={role} onChange={(event) => setRole(event.target.value)} placeholder="ex.: sujeito, cargo, unidade" />
              </label>
              <label>
                Valor original
                <input value={valueOriginal} onChange={(event) => setValueOriginal(event.target.value)} placeholder="como aparece no documento" />
              </label>
              <label>
                Valor normalizado
                <input value={valueNormalized} onChange={(event) => setValueNormalized(event.target.value)} placeholder="opcional; não completar externamente" />
              </label>
              {taskType === "temporal_assertion" && (
                <div className="two-fields">
                  <label>
                    Tipo de data
                    <select value={dateType} onChange={(event) => setDateType(event.target.value as typeof dateType)}>
                      <option value="publication">Publicação</option>
                      <option value="signature">Assinatura</option>
                      <option value="validity">Vigência</option>
                      <option value="effect">Efeito</option>
                    </select>
                  </label>
                  <label>
                    Data
                    <input type="date" value={dateValue} onChange={(event) => setDateValue(event.target.value)} />
                  </label>
                </div>
              )}
              <label>
                Justificativa {judgment === "AMBIGUOUS" && <b>obrigatória</b>}
                <textarea value={rationale} onChange={(event) => setRationale(event.target.value)} rows={3} />
              </label>
              <label>
                Notas
                <textarea value={notes} onChange={(event) => setNotes(event.target.value)} rows={3} />
              </label>
            </fieldset>

            {message && <p className="form-message" role="status">{message}</p>}
            <button className="record-action" onClick={addRecord}>
              Registrar observação no lote
            </button>
          </aside>
        </section>
      )}

      <section className="draft-section">
        <div className="section-heading">
          <div>
            <p className="eyebrow">LOTE EM PREPARAÇÃO</p>
            <h2>{records.length} observação(ões) independentes</h2>
          </div>
          {records.length > 0 && <button className="danger-link" onClick={discardDraft}>Descartar rascunho</button>}
        </div>
        {records.length === 0 ? (
          <p className="empty-draft">O lote ainda está vazio. Cada registro deverá preservar tarefa, julgamento, evidência e confiança.</p>
        ) : (
          <div className="record-grid">
            {records.map((record, index) => (
              <article key={record.id}>
                <div><span>#{String(index + 1).padStart(2, "0")}</span><b>{taskLabels[record.task_type]}</b></div>
                <h3>{record.payload.observed_type}</h3>
                <p>{record.evidence.map((item) => `p. ${item.page} · ${item.block_id}`).join(" / ")}</p>
                <small>{record.judgment} · {record.confidence}</small>
                <button onClick={() => setRecords((current) => current.filter((item) => item.id !== record.id))}>Remover</button>
              </article>
            ))}
          </div>
        )}
      </section>

      <footer className="annotation-footer">
        <p>Primeira calibração humana · DODF 112 · páginas 37 e 51</p>
        <p>O Codex estrutura e valida o lote, mas não atua como segundo revisor humano.</p>
      </footer>
    </main>
  );
}
