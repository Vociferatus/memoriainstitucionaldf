"use client";

import { useEffect, useMemo, useState } from "react";

type Risk = "critical" | "high" | "medium";
type Judgment = "CONFIRMED" | "REJECTED" | "AMBIGUOUS" | "MISSING";
type Evidence = { block_id:string; page:number; bbox:number[]; start:number|null; end:number|null; text:string };
type Candidate = { id:string; target:{layer:"evidence"|"semantic"|"identity";record_id:string}; category:string; sample_kind:string; risk:Risk; priority:number; question:string; proposal:string; label:string; reasons:string[]; evidence:Evidence[] };
type Queue = { schema_version:string; generated_at:string; source:{title:string;publication_date:string;pages:number;sha256:string}; policy:{name:string;version:string;human_role:string}; counts:Record<string,number>; queue:Candidate[] };
type Decision = { judgment:Judgment; decided_at:string; note:string|null };

const riskLabel:Record<Risk,string>={critical:"Crítico",high:"Alto",medium:"Médio"};
const categoryLabel:Record<string,string>={identity_resolution:"Conflito material",identity_candidate:"Identidade candidata",entity_mention:"Entidade",administrative_action:"Ação administrativa",published_item_boundary:"Limite de matéria",reference:"Referência",negative_recall:"Busca de omissão"};
const draftKey="dodf112-assisted-review-v1";

function Highlight({evidence}:{evidence:Evidence}) {
  const valid=evidence.start!==null&&evidence.end!==null&&evidence.end>evidence.start;
  return <p>{valid?<>{evidence.text.slice(0,evidence.start!)}<mark>{evidence.text.slice(evidence.start!,evidence.end!)}</mark>{evidence.text.slice(evidence.end!)}</>:evidence.text}</p>;
}

export default function AssistedReviewPage(){
  const [data,setData]=useState<Queue|null>(null);
  const [reviewer,setReviewer]=useState("");
  const [decisions,setDecisions]=useState<Record<string,Decision>>({});
  const [selected,setSelected]=useState("");
  const [risk,setRisk]=useState<"all"|Risk>("all");
  const [show,setShow]=useState<"pending"|"all">("pending");
  const [note,setNote]=useState("");
  const [message,setMessage]=useState("");
  const [hydrated,setHydrated]=useState(false);

  useEffect(()=>{
    fetch("/dodf112-review-queue.json").then(response=>response.json()).then((payload:Queue)=>{setData(payload);setSelected(payload.queue[0]?.id||"");});
    const timer=window.setTimeout(()=>{try{const stored=localStorage.getItem(draftKey);if(stored){const draft=JSON.parse(stored);setReviewer(draft.reviewer||"");setDecisions(draft.decisions||{});}}catch{localStorage.removeItem(draftKey);}finally{setHydrated(true);}},0);
    return()=>window.clearTimeout(timer);
  },[]);
  useEffect(()=>{if(hydrated)localStorage.setItem(draftKey,JSON.stringify({reviewer,decisions}));},[reviewer,decisions,hydrated]);

  const rows=useMemo(()=>data?.queue.filter(row=>(risk==="all"||row.risk===risk)&&(show==="all"||!decisions[row.id]))||[],[data,decisions,risk,show]);
  const current=rows.find(row=>row.id===selected)||rows[0]||data?.queue.find(row=>row.id===selected)||null;
  const completed=Object.keys(decisions).length;

  function decide(judgment:Judgment){
    if(!current)return;
    setDecisions(value=>({...value,[current.id]:{judgment,decided_at:new Date().toISOString(),note:note.trim()||null}}));
    setNote("");setMessage("Decisão registrada localmente.");
    const index=rows.findIndex(row=>row.id===current.id);const next=rows[index+1]||rows[0];if(next)setSelected(next.id);
  }
  function exportDecisions(){
    if(!data||!reviewer.trim()){setMessage("Informe o revisor antes de exportar.");return;}
    if(!completed){setMessage("Registre ao menos uma decisão.");return;}
    const payload={schema_version:"assisted-review-decisions/1.0",created_at:new Date().toISOString(),reviewer:reviewer.trim(),queue:{schema_version:data.schema_version,generated_at:data.generated_at,policy:data.policy},source:data.source,coverage:{reviewed:completed,total:data.queue.length},decisions:Object.entries(decisions).map(([candidate_id,decision])=>({candidate:data.queue.find(row=>row.id===candidate_id),...decision}))};
    const blob=new Blob([`${JSON.stringify(payload,null,2)}\n`],{type:"application/json"});const url=URL.createObjectURL(blob);const anchor=document.createElement("a");anchor.href=url;anchor.download=`dodf112-revisao-${Date.now()}.json`;anchor.click();URL.revokeObjectURL(url);setMessage("Decisões exportadas.");
  }

  if(!data)return <main className="review-loading"><div className="brand-mark">DF</div><p>Calculando prioridades de revisão…</p></main>;
  const negative=current?.category==="negative_recall";
  return <main className="review-page">
    <header className="review-topbar"><div className="annotation-brand"><span className="brand-mark">DF</span><span><strong>Revisão assistida</strong><small>DODF 112 · decisões, não transcrição</small></span></div><div className="review-progress"><span>{completed} de {data.queue.length}</span><i><b style={{width:`${completed/data.queue.length*100}%`}}/></i></div><button onClick={exportDecisions}>Exportar decisões</button></header>
    <section className="review-summary"><div><p className="eyebrow">VALIDAÇÃO BASEADA EM RISCO</p><h1>Revise somente o que merece atenção.</h1><p>O sistema propõe, mostra a evidência e explica o risco. Você confirma, rejeita ou preserva a ambiguidade.</p></div><dl><div><dt>Críticos</dt><dd>{data.counts.critical}</dd></div><div><dt>Alto risco</dt><dd>{data.counts.high}</dd></div><div><dt>Amostra</dt><dd>{data.counts.medium}</dd></div></dl></section>
    <section className="review-controls"><label>Revisor<input value={reviewer} onChange={event=>setReviewer(event.target.value)} placeholder="seu identificador"/></label><label>Risco<select value={risk} onChange={event=>setRisk(event.target.value as typeof risk)}><option value="all">Todos</option><option value="critical">Crítico</option><option value="high">Alto</option><option value="medium">Médio</option></select></label><label>Exibir<select value={show} onChange={event=>setShow(event.target.value as typeof show)}><option value="pending">Pendentes</option><option value="all">Todos</option></select></label><p>{rows.length} casos na fila atual</p></section>
    <section className="review-workspace"><nav className="review-queue">{rows.map(row=><button key={row.id} className={current?.id===row.id?"selected":""} onClick={()=>{setSelected(row.id);setNote(decisions[row.id]?.note||"");}}><span><i className={`risk-${row.risk}`}>{riskLabel[row.risk]}</i>{categoryLabel[row.category]||row.category}</span><b>{row.label}</b><small>{row.question}</small>{decisions[row.id]&&<em>{decisions[row.id].judgment}</em>}</button>)}{!rows.length&&<p>Todos os casos deste filtro foram decididos.</p>}</nav>
      <article className="review-card">{current&&<><div className="review-kicker"><span className={`risk-${current.risk}`}>{riskLabel[current.risk]}</span><b>prioridade {current.priority}</b><small>{current.sample_kind}</small></div><h2>{current.question}</h2><section className="proposal"><span>PROPOSTA DO SISTEMA</span><strong>{current.proposal}</strong><p>{current.label}</p></section><div className="risk-reasons"><span>POR QUE ESTÁ NA FILA</span>{current.reasons.map(reason=><p key={reason}>• {reason.replaceAll("_"," ")}</p>)}</div><label className="review-note">Correção ou justificativa, se necessária<textarea rows={3} value={note} onChange={event=>setNote(event.target.value)}/></label>{message&&<p className="review-message">{message}</p>}<div className="decision-buttons"><button className="confirm" onClick={()=>decide("CONFIRMED")}>{negative?"Nenhuma omissão":"Correto"}</button><button className="reject" onClick={()=>decide(negative?"MISSING":"REJECTED")}>{negative?"Há omissão":"Incorreto"}</button><button onClick={()=>decide("AMBIGUOUS")}>Ambíguo</button></div></>}</article>
      <aside className="review-evidence">{current&&<><div className="evidence-heading"><span>EVIDÊNCIA PRIMÁRIA</span><a href={`/dodf112.pdf#page=${current.evidence[0]?.page||1}`} target="_blank" rel="noreferrer">Abrir PDF · p. {current.evidence[0]?.page}</a></div><iframe title={`Página ${current.evidence[0]?.page} do DODF`} src={`/dodf112.pdf#page=${current.evidence[0]?.page||1}&view=FitH`}/><div className="evidence-stack">{current.evidence.map((item,index)=><section key={`${item.block_id}-${index}`}><span>p. {item.page} · {item.block_id}</span><Highlight evidence={item}/><small>bbox {item.bbox.join(" · ")}</small></section>)}</div></>}</aside>
    </section>
  </main>;
}
