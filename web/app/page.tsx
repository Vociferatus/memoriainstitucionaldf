"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";

type Occurrence = { block_id:string; page:number; start:number; end:number; method:string; item_id:string|null; role?:string };
type Item = { id:string; section_id:string; title:string; item_type:string; number:string|null; act_date:string|null; start_page:number; end_page:number; breadcrumb:string[]; text:string; block_ids:string[]; actions:string[]; entities:string[]; references:string[]; processes:string[]; provision_count:number };
type Entity = { id:string; entity_type:string; name:string; occurrences:Occurrence[]; item_ids:string[] };
type Action = Occurrence & { id:string; verb:string; value_original:string; participant:string|null };
type Process = { id:string; value:string; occurrences:Occurrence[]; item_ids:string[] };
type Reference = Occurrence & { id:string; reference_type:string; value_original:string; value_normalized:string; valid:boolean|null };
type Block = { id:string; page:number; bbox:number[]; text:string };
type Data = { document:{title:string; publication_date:string; pages:number; sha256:string; counts:Record<string,number>}; items:Item[]; entities:Entity[]; actions:Action[]; processes:Process[]; references:Reference[]; blocks:Record<string,Block> };
type View = "items"|"entities"|"actions"|"processes"|"references";
type Row = Item|Entity|Action|Process|Reference;

const labels:Record<View,string> = { items:"Matérias", entities:"Pessoas e órgãos", actions:"Ações administrativas", processes:"Processos SEI", references:"Referências" };
const icons:Record<View,string> = { items:"▤", entities:"◎", actions:"↗", processes:"⌕", references:"§" };
const normalize = (value:string) => value.normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase();
const pretty = (value:string) => value.replaceAll("_"," ").replace(/\b\w/g, char => char.toUpperCase());

function Evidence({occurrence,data}:{occurrence:Occurrence;data:Data}) {
  const block=data.blocks[occurrence.block_id];
  if(!block) return <p className="empty">Bloco de evidência não localizado.</p>;
  const hasSpan=occurrence.end>occurrence.start;
  return <section className="evidence"><div className="section-title"><span>EVIDÊNCIA PRIMÁRIA</span><b>PÁGINA {block.page}</b></div><div className="paper-text">{hasSpan?<>{block.text.slice(0,occurrence.start)}<mark>{block.text.slice(occurrence.start,occurrence.end)}</mark>{block.text.slice(occurrence.end)}</>:block.text}</div><dl><div><dt>Bloco</dt><dd>{block.id}</dd></div><div><dt>Coordenadas</dt><dd>{block.bbox.map(n=>n.toFixed(1)).join(" · ")}</dd></div><div><dt>Método</dt><dd>{occurrence.method||"segmentação_semântica_v2"}</dd></div></dl></section>;
}

function RelatedItems({ids,data,onOpen}:{ids:string[];data:Data;onOpen:(id:string)=>void}) {
  const rows=ids.slice(0,8).map(id=>data.items.find(item=>item.id===id)).filter(Boolean) as Item[];
  if(!rows.length) return <p className="empty">Nenhuma matéria relacionada.</p>;
  return <div className="related">{rows.map(item=><button key={item.id} onClick={()=>onOpen(item.id)}><span>{pretty(item.item_type)}</span><b>{item.title}</b><small>p. {item.start_page}{item.end_page!==item.start_page?`–${item.end_page}`:""}</small></button>)}</div>;
}

function filteredRows(data:Data,view:View,index:Map<string,Item>,query:string,type:string):Row[] {
  const q=normalize(query); const matches=(hay:string,typeValue:string)=> (!q||normalize(hay).includes(q))&&(type==="all"||typeValue===type);
  if(view==="items") return data.items.filter(row=>matches([row.title,row.item_type,...row.breadcrumb,row.text].join(" "),row.item_type));
  if(view==="entities") return data.entities.filter(row=>matches(`${row.name} ${row.entity_type}`,row.entity_type));
  if(view==="actions") return data.actions.filter(row=>matches(`${row.verb} ${row.participant||""} ${row.value_original} ${index.get(row.item_id||"")?.title||""}`,row.verb));
  if(view==="processes") return data.processes.filter(row=>matches(row.value,"all"));
  return data.references.filter(row=>matches(`${row.value_original} ${row.reference_type} ${index.get(row.item_id||"")?.title||""}`,row.reference_type));
}

function typeOptions(data:Data,view:View):string[] {
  if(view==="items") return [...new Set(data.items.map(row=>row.item_type))].sort();
  if(view==="entities") return [...new Set(data.entities.map(row=>row.entity_type))].sort();
  if(view==="actions") return [...new Set(data.actions.map(row=>row.verb))].sort();
  if(view==="references") return [...new Set(data.references.map(row=>row.reference_type))].sort();
  return [];
}

function RowCard({row,view,index,isSelected,onSelect}:{row:Row;view:View;index:Map<string,Item>;isSelected:boolean;onSelect:()=>void}) {
  let content;
  if(view==="items"){const item=row as Item;content=<><span>{pretty(item.item_type)} · SEÇÃO {item.section_id.slice(-1).toUpperCase()}</span><b>{item.title}</b><small>{item.breadcrumb.join(" › ")} · p. {item.start_page}{item.end_page!==item.start_page?`–${item.end_page}`:""}</small></>}
  else if(view==="entities"){const entity=row as Entity;content=<><span>{pretty(entity.entity_type)}</span><b>{entity.name}</b><small>{entity.occurrences.length} ocorrência(s) · {entity.item_ids.length} matéria(s)</small></>}
  else if(view==="actions"){const action=row as Action;content=<><span>{pretty(action.verb)} · PÁGINA {action.page}</span><b>{action.participant||action.value_original}</b><small>{index.get(action.item_id||"")?.title}</small></>}
  else if(view==="processes"){const process=row as Process;content=<><span>PROCESSO SEI</span><b>{process.value}</b><small>{process.occurrences.length} ocorrência(s) · {process.item_ids.length} matéria(s)</small></>}
  else {const reference=row as Reference;content=<><span>{pretty(reference.reference_type)} · PÁGINA {reference.page}</span><b>{reference.value_original}</b><small>{index.get(reference.item_id||"")?.title}</small></>}
  return <button className={isSelected?"selected":""} onClick={onSelect}>{content}</button>;
}

export default function Home() {
  const [data,setData]=useState<Data|null>(null); const [view,setView]=useState<View>("items"); const [query,setQuery]=useState(""); const [type,setType]=useState("all"); const [selected,setSelected]=useState("");
  useEffect(()=>{fetch("/dodf112.json").then(r=>r.json()).then((payload:Data)=>{setData(payload);setSelected(payload.items[0]?.id||"");});},[]);
  const index=useMemo(()=>{if(!data)return new Map<string,Item>();return new Map(data.items.map(item=>[item.id,item]));},[data]);
  const rows=useMemo(()=>data?filteredRows(data,view,index,query,type):[],[data,view,query,type,index]);
  const options=useMemo(()=>data?typeOptions(data,view):[],[data,view]);
  const current=rows.find(row=>row.id===selected)||rows[0];
  function changeView(next:View){setView(next);setType("all");setSelected("");}
  function openItem(id:string){setView("items");setType("all");setQuery("");setSelected(id);}
  if(!data)return <main className="loading"><div className="brand-mark">DF</div><p>Organizando o Diário Oficial…</p></main>;
  const counts:Record<View,number>={items:data.items.length,entities:data.entities.length,actions:data.actions.length,processes:data.processes.length,references:data.references.length};
  return <main><header className="topbar"><div className="brand-mark">DF</div><div><strong>Memória Institucional</strong><span>Explorador de evidências oficiais</span></div><Link className="annotation-entry" href="/revisar">Revisar resultados</Link><div className="edition-pill">DODF 112 · 22 JUN 2026</div></header>
    <section className="intro"><div><p className="eyebrow">FORMAÇÃO DOS DADOS</p><h1>Do Diário Oficial à informação navegável.</h1><p>Selecione qualquer registro para reconstruir o caminho entre documento, matéria, entidade e evidência.</p></div><div className="pipeline"><span>PDF</span><i>→</i><span>2.553 blocos</span><i>→</i><span>457 matérias</span><i>→</i><b>relações</b></div></section>
    <section className="metrics"><div><strong>85</strong><span>páginas</span></div><div><strong>457</strong><span>matérias</span></div><div><strong>202</strong><span>contextos</span></div><div><strong>114</strong><span>ações</span></div><div><strong>1.096</strong><span>processos únicos</span></div></section>
    <section className="workspace"><aside><p className="aside-label">EXPLORAR POR</p>{(Object.keys(labels) as View[]).map(key=><button className={view===key?"active":""} key={key} onClick={()=>changeView(key)}><i>{icons[key]}</i><span>{labels[key]}</span><b>{counts[key].toLocaleString("pt-BR")}</b></button>)}<div className="provenance"><span>ARQUIVO VERIFICADO</span><b>SHA-256</b><code>{data.document.sha256.slice(0,18)}…</code></div></aside>
      <div className="explorer"><div className="toolbar"><div><p className="eyebrow">{labels[view].toUpperCase()}</p><h2>{rows.length.toLocaleString("pt-BR")} resultados</h2></div><div className="controls"><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Busque nome, órgão, processo ou ato…" aria-label="Buscar" />{options.length>0&&<select value={type} onChange={e=>setType(e.target.value)} aria-label="Filtrar tipo"><option value="all">Todos os tipos</option>{options.map(value=><option key={value} value={value}>{pretty(value)}</option>)}</select>}</div></div>
        <div className="split"><div className="list" aria-label={`Lista de ${labels[view]}`}>{rows.slice(0,150).map(row=><RowCard key={row.id} row={row} view={view} index={index} isSelected={current?.id===row.id} onSelect={()=>setSelected(row.id)}/>)}{rows.length>150&&<p className="limit">Exibindo os primeiros 150 resultados. Refine a busca para localizar outros registros.</p>}</div>
          <article className="detail">{!current?<p className="empty">Nenhum resultado para os filtros selecionados.</p>:<>{view==="items"&&<ItemDetail item={current as Item} data={data} />}{view==="entities"&&<EntityDetail entity={current as Entity} data={data} openItem={openItem} />}{view==="actions"&&<OccurrenceDetail title={(current as Action).participant||pretty((current as Action).verb)} kicker={pretty((current as Action).verb)} occurrence={current as Action} itemIds={[(current as Action).item_id]} data={data} openItem={openItem} />}{view==="processes"&&<OccurrenceDetail title={(current as Process).value} kicker="Processo SEI" occurrence={(current as Process).occurrences[0]} itemIds={(current as Process).item_ids} data={data} openItem={openItem} />}{view==="references"&&<OccurrenceDetail title={(current as Reference).value_original} kicker={pretty((current as Reference).reference_type)} occurrence={current as Reference} itemIds={[(current as Reference).item_id]} data={data} openItem={openItem} />}</>}</article>
        </div></div></section></main>;
}

function ItemDetail({item,data}:{item:Item;data:Data}) { const first=data.blocks[item.block_ids[0]]; const occurrence:Occurrence={block_id:first.id,page:first.page,start:0,end:0,method:"semantic_segmentation_v2",item_id:item.id}; return <><p className="detail-kicker">{pretty(item.item_type)} · SEÇÃO {item.section_id.slice(-1).toUpperCase()}</p><h3>{item.title}</h3><p className="breadcrumb">{item.breadcrumb.join(" › ")}</p><div className="chips"><span>p. {item.start_page}{item.end_page!==item.start_page?`–${item.end_page}`:""}</span><span>{item.provision_count} dispositivos</span><span>{item.actions.length} ações</span><span>{item.processes.length} processos</span></div><section className="lineage"><div><b>01</b><span>Documento</span><small>PDF preservado</small></div><i>→</i><div><b>02</b><span>Bloco</span><small>{item.block_ids.length} blocos</small></div><i>→</i><div><b>03</b><span>Matéria</span><small>{pretty(item.item_type)}</small></div><i>→</i><div><b>04</b><span>Relações</span><small>{item.actions.length+item.entities.length+item.references.length+item.processes.length} vínculos</small></div></section><Evidence occurrence={occurrence} data={data}/>{item.processes.length>0&&<><div className="section-title"><span>PROCESSOS RELACIONADOS</span></div><div className="tags">{item.processes.slice(0,12).map(id=><span key={id}>{data.processes.find(row=>row.id===id)?.value}</span>)}</div></>}<details><summary>Ver texto integral da matéria</summary><p className="full-text">{item.text}</p></details></>; }
function EntityDetail({entity,data,openItem}:{entity:Entity;data:Data;openItem:(id:string)=>void}) { const occurrence=entity.occurrences[0]; return <><p className="detail-kicker">{pretty(entity.entity_type)}</p><h3>{entity.name}</h3><div className="chips"><span>{entity.occurrences.length} ocorrências</span><span>{entity.item_ids.length} matérias relacionadas</span></div><div className="section-title"><span>MATÉRIAS RELACIONADAS</span></div><RelatedItems ids={entity.item_ids} data={data} onOpen={openItem}/>{occurrence&&<Evidence occurrence={occurrence} data={data}/>}</>; }
function OccurrenceDetail({title,kicker,occurrence,itemIds,data,openItem}:{title:string;kicker:string;occurrence:Occurrence;itemIds:(string|null)[];data:Data;openItem:(id:string)=>void}) { const ids=itemIds.filter(Boolean) as string[]; return <><p className="detail-kicker">{kicker}</p><h3>{title}</h3><div className="section-title"><span>MATÉRIAS RELACIONADAS</span></div><RelatedItems ids={ids} data={data} onOpen={openItem}/><Evidence occurrence={occurrence} data={data}/></>; }
