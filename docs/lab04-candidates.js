/* Seiko Lab : new robot cockpit. Read-only, strictly observed paper data. */
(function(){
'use strict';
const view=document.getElementById('view-candidates');if(!view)return;
const forward=(typeof DATA==='object'&&DATA.strategy_forward)||{};
const charts=(typeof DATA==='object'&&DATA.strategy_forward_charts)||{};
const items=Array.isArray(forward.trials)?forward.trials.filter(t=>t&&typeof t.id==='string'):[];
const money=v=>Number.isFinite(v)?v.toLocaleString('fr-FR',{minimumFractionDigits:2,maximumFractionDigits:2})+' $':'En attente';
const fmt=(v,d=2)=>Number(v).toLocaleString('fr-FR',{maximumFractionDigits:d,minimumFractionDigits:d});
const percent=v=>Number.isFinite(v)?(v>0?'+':'')+fmt(v)+' %':'En attente';
const valid=v=>typeof v==='number'&&Number.isFinite(v);
const measured=t=>valid(t.net_pct)&&Number(t.observed_days)>0;
const net=t=>measured(t)?t.net_pct:null;
const capital=t=>measured(t)?20*(1+t.net_pct/100):null;
const observed=items.filter(measured),waiting=items.filter(t=>!measured(t));
const initial=observed.length*20;
const total=observed.reduce((sum,t)=>sum+capital(t),0);
const date=v=>{const n=Date.parse(v);return Number.isFinite(n)?new Intl.DateTimeFormat('fr-FR',{day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit',timeZone:'Europe/Paris'}).format(new Date(n)):'Date indisponible'};
const stamp=t=>Number.isFinite(t)?new Intl.DateTimeFormat('fr-FR',{day:'2-digit',month:'short',timeZone:'Europe/Paris'}).format(new Date(t*1000)):'—';
const clean=v=>String(v||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'');
const sources={bounded_evolution:'Évolution algorithmique',autonomous_crossover:'Croisement autonome',bounded_local_research_director:'Recherche locale de secours',autonomous_grid_search:'Recherche quantitative',gemini_structured_hypothesis:'Hypothèse Gemini'};
const logics={breakout:'Cassure',trend_following:'Suivi de tendance',mean_reversion:'Retour à la moyenne',ema_trend:'Tendance EMA',rsi_reversal:'Rebond RSI',volatility_gate:'Filtre de volatilité',dual_confirmation:'Double confirmation'};
const short=t=>(t.asset||'Marché').replace('USD','')+' · '+(logics[t.logic]||String(t.logic||'Stratégie').replaceAll('_',' '));
const stateLabel=t=>t.sufficient_evidence?'Examen humain possible':!measured(t)?'En attente de cours':'En observation';
const points=t=>{const raw=charts.series&&charts.series[t.id];if(!Array.isArray(raw))return [];
 const map=new Map();
 for(const r of raw){if(r&&valid(r.t)&&valid(r.equity_usd)&&valid(r.hold_equity_usd)&&r.t>0&&r.equity_usd>=0&&r.hold_equity_usd>=0)map.set(r.t,r);}
 return [...map.values()].sort((a,b)=>a.t-b.t);
};
const h=(tag,cls,txt)=>{const el=document.createElement(tag);if(cls)el.className=cls;if(txt!==undefined)el.textContent=String(txt);return el};
const put=(parent,...nodes)=>{parent.append(...nodes);return parent};
const card=(title,sub,cls='')=>{const box=h('section','cv-panel '+cls);put(box,h('h3','cv-section-title',title));if(sub)put(box,h('p','cv-muted',sub));return box};
const badge=(text,type='')=>h('span','cv-badge '+type,text);
const css=document.createElement('style');css.id='seiko-candidates-v2';css.textContent=[
'#view-candidates{--cv-green:#92e5ad;--cv-cyan:#80d3d8;--cv-red:#fa98a4;--cv-muted:#a6bcc1;color:#e8f4ef}',
'#view-candidates *{box-sizing:border-box}',
'#view-candidates .cv-head{padding:27px 25px;border:1px solid #3d6762;border-radius:22px;background:radial-gradient(circle at 95% 4%,rgba(75,183,157,.19),transparent 46%),linear-gradient(145deg,#1c393b,#122527 70%);margin-bottom:15px}',
'#view-candidates .cv-eyebrow{color:#9fe3be;letter-spacing:.13em;font-size:11px;font-weight:800}',
'#view-candidates .cv-head h2{font-size:clamp(24px,4vw,38px);letter-spacing:-.04em;margin:7px 0 9px;color:#f1fff6}',
'#view-candidates .cv-head p,#view-candidates .cv-muted{font-size:12px;line-height:1.7;color:var(--cv-muted);margin:7px 0}',
'#view-candidates .cv-badges{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}',
'#view-candidates .cv-badge{font-size:10px;padding:5px 10px;border:1px solid #55736c;background:#25433e;color:#d6f5e4;border-radius:30px}',
'#view-candidates .cv-badge.cv-wait{color:#f5d3a8;border-color:#84694b;background:#45382c}',
'#view-candidates .cv-badge.cv-good{color:#c4fbbb;border-color:#578759}',
'#view-candidates .cv-kpis{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin:15px 0}',
'#view-candidates .cv-kpi{background:#192f34;border:1px solid #38565b;border-radius:15px;padding:16px;min-width:0}',
'#view-candidates .cv-kpi small{display:block;font-size:10px;letter-spacing:.04em;color:#a8c6c2}',
'#view-candidates .cv-kpi strong{display:block;font-size:clamp(17px,2.7vw,26px);margin:8px 0 4px;overflow-wrap:anywhere;color:#f0fff4;font-variant-numeric:tabular-nums}',
'#view-candidates .cv-kpi span{display:block;font-size:10px;color:#a4bbb7;line-height:1.5}',
'#view-candidates .cv-two{display:grid;grid-template-columns:1.18fr 1fr;gap:14px;margin:14px 0}',
'#view-candidates .cv-panel{border:1px solid #35565a;background:#14282e;border-radius:17px;padding:19px;min-width:0;overflow:hidden}',
'#view-candidates .cv-section-title{margin:0 0 8px;color:#e7f9ed;font-size:18px;letter-spacing:-.02em}',
'#view-candidates .cv-chart{height:235px;min-height:160px;margin:15px 0 5px}',
'#view-candidates .cv-chart svg{width:100%;height:100%;display:block;overflow:visible}',
'#view-candidates .cv-chart.cv-no-curve{display:flex;align-items:center;justify-content:center;padding:20px;text-align:center;background:rgba(144,203,190,.04);border:1px dashed #456166;border-radius:12px}',
'#view-candidates .cv-legend{display:flex;gap:15px;flex-wrap:wrap;font-size:11px;color:#b9d3cd;margin:8px 0}',
'#view-candidates .cv-dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px;background:var(--cv-color)}',
'#view-candidates .cv-asset{display:grid;grid-template-columns:54px minmax(0,1fr) 85px;gap:10px;align-items:center;margin:16px 0;font-size:12px}',
'#view-candidates .cv-asset .cv-track{height:14px;position:relative;background:#274049;border-radius:7px;overflow:hidden}',
'#view-candidates .cv-asset .cv-track>span{display:block;height:100%;background:linear-gradient(90deg,#357b7c,#99f0b3);border-radius:7px}',
'#view-candidates .cv-asset strong{text-align:right;font-variant-numeric:tabular-nums}',
'#view-candidates .cv-asset small{display:block;color:#b2c7c4;font-size:10px;margin-top:3px}',
'#view-candidates .cv-snapshot{display:flex;gap:6px;height:16px;border-radius:8px;overflow:hidden;background:#263d44;margin:12px 0}',
'#view-candidates .cv-snapshot>span{height:100%;min-width:0}',
'#view-candidates .cv-snapshot-legend{display:flex;flex-wrap:wrap;gap:12px;color:#aac5be;font-size:10px}',
'#view-candidates .cv-ranking{max-height:300px;overflow:auto;padding-right:5px}',
'#view-candidates .cv-rank-row{display:grid;grid-template-columns:28px minmax(95px,1fr) minmax(110px,1.5fr) 76px;gap:8px;align-items:center;font-size:11px;padding:9px 0;border-bottom:1px solid #2b4749}',
'#view-candidates .cv-rank-track{position:relative;height:12px;background:#253c42;border-radius:6px}',
'#view-candidates .cv-zero{position:absolute;top:-3px;bottom:-3px;left:50%;border-left:1px dashed #d7e5e0;opacity:.65}',
'#view-candidates .cv-rank-bar{position:absolute;top:2px;bottom:2px;border-radius:3px;background:#87ddb4}',
'#view-candidates .cv-rank-bar.cv-negative{background:#ee8793}',
'#view-candidates .cv-rank-row strong{font-variant-numeric:tabular-nums;text-align:right}',
'#view-candidates .cv-filters{display:grid;grid-template-columns:minmax(150px,1.3fr) repeat(3,minmax(115px,1fr));gap:9px;margin:15px 0}',
'#view-candidates .cv-filters input,#view-candidates .cv-filters select,#view-candidates .cv-picker{width:100%;max-width:100%;min-width:0;padding:11px;border:1px solid #54706a;background:#20383c;color:#e8fff0;border-radius:9px;font:inherit;font-size:12px}',
'#view-candidates .cv-filters input:focus-visible,#view-candidates button:focus-visible,#view-candidates select:focus-visible{outline:2px solid #92e5ad;outline-offset:3px}',
'#view-candidates .cv-layout{display:grid;grid-template-columns:minmax(220px,.82fr) minmax(0,1.5fr);gap:15px}',
'#view-candidates .cv-directory{max-height:725px;overflow:auto;display:flex;flex-direction:column;gap:7px;padding-right:4px}',
'#view-candidates .cv-item{cursor:pointer;text-align:left;background:#1b3438;border:1px solid #355256;border-radius:12px;padding:12px;color:#e4f7ef;font:inherit;width:100%}',
'#view-candidates .cv-item[aria-pressed=true]{border-color:#a2eec1;background:#254640;box-shadow:inset 3px 0 #9cddb4}',
'#view-candidates .cv-item-top{display:flex;justify-content:space-between;align-items:center;gap:9px;margin-bottom:6px}',
'#view-candidates .cv-item strong{font-size:12px}',
'#view-candidates .cv-item small{color:#afc9c4;display:block;font-size:10px;line-height:1.6}',
'#view-candidates .cv-item .cv-item-pct{font-size:12px;font-weight:800;font-variant-numeric:tabular-nums}',
'#view-candidates .cv-pos{color:#9df1b8}#view-candidates .cv-neg{color:#ffadb3}#view-candidates .cv-neutral{color:#c8d7d4}',
'#view-candidates .cv-detail-title{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}',
'#view-candidates .cv-detail-title h3{margin:0;font-size:21px;color:#f0fff4}',
'#view-candidates .cv-detail-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:17px 0}',
'#view-candidates .cv-stat{padding:12px;background:#1d363c;border-radius:11px;border:1px solid #36565b;min-width:0}',
'#view-candidates .cv-stat small{display:block;color:#a4c0bb;font-size:10px}',
'#view-candidates .cv-stat strong{display:block;font-size:15px;margin-top:5px;overflow-wrap:anywhere;font-variant-numeric:tabular-nums}',
'#view-candidates .cv-compare-row{display:grid;grid-template-columns:92px minmax(0,1fr) 76px;gap:8px;align-items:center;margin:10px 0;font-size:11px}',
'#view-candidates .cv-compare-track{height:17px;background:#243e43;border-radius:9px;overflow:hidden}',
'#view-candidates .cv-compare-track span{display:block;height:100%;border-radius:9px}',
'#view-candidates .cv-meter{height:10px;border-radius:6px;background:#294348;overflow:hidden;margin:6px 0 12px}',
'#view-candidates .cv-meter span{display:block;height:100%;background:#f4a1a3;border-radius:6px}',
'#view-candidates .cv-subhead{font-size:13px;color:#d3eee4;margin:22px 0 6px}',
'#view-candidates .cv-empty{padding:26px 12px;text-align:center;color:#b5cbc6;font-size:12px;line-height:1.7}',
'#view-candidates .cv-foot{font-size:11px;color:#91b1ab;line-height:1.7;margin-top:12px}',
'@media(max-width:950px){#view-candidates .cv-two,#view-candidates .cv-layout{grid-template-columns:1fr}#view-candidates .cv-directory{max-height:350px}#view-candidates .cv-filters{grid-template-columns:repeat(2,minmax(0,1fr))}}',
'@media(max-width:580px){#view-candidates .cv-head{padding:20px 16px}#view-candidates .cv-kpis{grid-template-columns:repeat(2,minmax(0,1fr))}#view-candidates .cv-kpi{padding:12px}#view-candidates .cv-panel{padding:14px}#view-candidates .cv-filters{grid-template-columns:1fr 1fr}#view-candidates .cv-filters input{grid-column:1/-1}#view-candidates .cv-asset{grid-template-columns:43px minmax(0,1fr) 72px}#view-candidates .cv-rank-row{grid-template-columns:19px minmax(60px,1fr) minmax(72px,1fr) 64px}#view-candidates .cv-detail-grid{grid-template-columns:repeat(2,minmax(0,1fr))}#view-candidates .cv-chart{height:205px}}'
].join('\n');document.head.append(css);
view.replaceChildren();
const head=h('header','cv-head');
put(head,h('span','cv-eyebrow','SEIKO LAB · RECHERCHE PROSPECTIVE'),
h('h2','','Nouveaux robots · Tableau de bord'),
h('p','','36 robots historiques conservés à part. Ici, chaque nouvelle stratégie expérimente avec 20 $ fictifs ; aucun argent réel ni ordre de trading.'));
const headBadges=h('div','cv-badges');
put(headBadges,badge(items.length+' robots suivis'),badge(observed.length+' avec résultats'),badge(waiting.length+' en attente','cv-wait'),badge('Relevé : '+date(forward.generated_at)));
put(head,headBadges);view.append(head);
const kpiRow=h('div','cv-kpis');
const withPoints=items.filter(t=>points(t).length>0).length;
const metrics=[
['STRATÉGIES SUIVIES',String(items.length),'En parallèle des 36 robots originaux'],
['CAPITAL MESURÉ',observed.length?money(total):'En attente',observed.length+' robots mesurés · '+money(initial)+' de départ'],
['RÉSULTAT MESURÉ',observed.length?percent((total/initial-1)*100):'En attente','Calcul uniquement sur les robots observés'],
['TRANSACTIONS CLÔTURÉES',String(items.reduce((sum,t)=>sum+(valid(t.closed_trades)?t.closed_trades:0),0)),'Simulations, après clôture'],
['POINTS DE COURBE',withPoints+' / '+items.length,'Chaque robot a son propre historique'],
['DOSSIERS EXAMINABLES',String(items.filter(t=>t.sufficient_evidence).length),'Ne signifie pas investissement approuvé']
];
for(const [label,value,extra] of metrics){const el=h('div','cv-kpi');put(el,h('small','',label),h('strong','',value),h('span','',extra));kpiRow.append(el)}
view.append(kpiRow);
const top=h('div','cv-two'),growth=card('Évolution globale des candidats','Courbe de la même cohorte, avec de vrais relevés datés seulement.'),right=card('Répartition par marché','Rendement moyen observé par univers. Chaque marché reste comparé séparément.');
const growthChart=h('div','cv-chart');put(growth,growthChart);
const growthNote=h('p','cv-foot');put(growth,growthNote);
const assetHost=h('div','');put(right,assetHost);
const snapshot=h('div','cv-snapshot');put(right,h('h4','cv-subhead','Avancement des 36 robots'),snapshot);
const snapshotLegend=h('div','cv-snapshot-legend');put(right,snapshotLegend);
put(top,growth,right);view.append(top);
function lineChart(host,rows,title,empty){
 host.replaceChildren();host.className='cv-chart';
 if(rows.length<2){host.classList.add('cv-no-curve');host.append(h('p','cv-muted',empty));return false}
 host.classList.remove('cv-no-curve');
 const vals=rows.flatMap(p=>[p.v,p.h]),mn=Math.min(...vals,20),mx=Math.max(...vals,20);
 const slack=Math.max((mx-mn)*.14,.15),lo=mn-slack,hi=mx+slack, minT=rows[0].t,maxT=rows[rows.length-1].t;
 const W=660,H=220,left=62,right=640,up=15,bottom=174;
 const x=t=>left+(maxT===minT?.5:(t-minT)/(maxT-minT))*(right-left);
 const y=v=>bottom-(v-lo)/(hi-lo)*(bottom-up);
 const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');
 svg.setAttribute('viewBox','0 0 '+W+' '+H);svg.setAttribute('role','img');svg.setAttribute('aria-label',title);
 const el=(tag,attrs)=>{const node=document.createElementNS(ns,tag);for(const [k,v] of Object.entries(attrs||{}))node.setAttribute(k,String(v));svg.append(node);return node};
 for(let k=0;k<4;k++){const val=lo+(hi-lo)*k/3,Y=y(val);
   el('line',{x1:left,y1:Y,x2:right,y2:Y,stroke:'#456067','stroke-width':1,'stroke-dasharray':'4 5'});
   const text=el('text',{x:4,y:Y+3,fill:'#9bb8b2','font-size':10});text.textContent=fmt(val,1)+'$'}
 const baseline=20*(title.startsWith('Global')?rows[0].cohort||1:1);
 if(baseline>=lo&&baseline<=hi)el('line',{x1:left,y1:y(baseline),x2:right,y2:y(baseline),stroke:'#b5cfc2','stroke-width':1,'stroke-dasharray':'2 6'});
 for(const [key,color] of [['h','#90a6b6'],['v','#88e5ae']]){
   const poly=el('polyline',{points:rows.map(p=>x(p.t).toFixed(2)+','+y(p[key]).toFixed(2)).join(' '),fill:'none',stroke:color,'stroke-width':3,'stroke-linecap':'round','stroke-linejoin':'round'});
   const titleEl=document.createElementNS(ns,'title');titleEl.textContent=key==='h'?'Marché conservé':'Capital fictif des robots';poly.append(titleEl);
   for(const p of rows){const dot=el('circle',{cx:x(p.t),cy:y(p[key]),r:3.5,fill:color});
     const t=document.createElementNS(ns,'title');t.textContent=stamp(p.t)+' · '+money(p[key]);dot.append(t)}
 }
 for(const p of [rows[0],rows[rows.length-1]]){const label=el('text',{x:x(p.t),y:H-15,'text-anchor':'middle',fill:'#a8c3bb','font-size':11});label.textContent=stamp(p.t)}
 host.append(svg);
 const legend=h('div','cv-legend');for(const [label,c] of [['Robots','#88e5ae'],['Marché conservé (Hold)','#90a6b6']]){const span=h('span','',label);span.prepend(h('i','cv-dot'));span.firstChild.style.setProperty('--cv-color',c);legend.append(span)}host.append(legend);
 return true;
}
function globalHistory(){
 const cohorts=items.map(t=>({id:t.id,rows:points(t)})).filter(t=>t.rows.length>=2);
 if(!cohorts.length)return {rows:[],size:0};
 const allTime=new Map();
 for(const c of cohorts)for(const p of c.rows){let map=allTime.get(p.t);if(!map){map=new Map();allTime.set(p.t,map)}map.set(c.id,p)}
 const records=[];
 for(const [t,m] of allTime){if(m.size!==cohorts.length)continue;const rr=[...m.values()];records.push({t,v:rr.reduce((n,p)=>n+p.equity_usd,0),h:rr.reduce((n,p)=>n+p.hold_equity_usd,0),cohort:cohorts.length})}
 records.sort((a,b)=>a.t-b.t);return {rows:records,size:cohorts.length};
}
const gl=globalHistory();const drawn=lineChart(growthChart,gl.rows,'Global · nouveaux robots (cohorte stable)','Courbe temporelle bientôt disponible. Il faut au moins deux dates communes à une même cohorte de robots. Les comparaisons chiffrées ci-dessous sont déjà consultables.');
growthNote.textContent=drawn?'Courbe construite sur '+gl.size+' robot(s) suivis aux mêmes dates. Le périmètre diffère du total si certains robots n’ont pas encore deux points.':'Aucune courbe artificielle : les performances actuelles sont détaillées dans le classement et les graphiques par marché.';
const countByAsset={},measuredByAsset={};
for(const t of items){const a=t.asset||'Autre';countByAsset[a]=(countByAsset[a]||0)+1;if(measured(t))(measuredByAsset[a]||(measuredByAsset[a]=[])).push(t.net_pct)}
const assetEntries=Object.entries(countByAsset).sort((a,b)=>a[0].localeCompare(b[0]));
for(const [asset,count] of assetEntries){
 const vals=measuredByAsset[asset]||[],avg=vals.length?vals.reduce((a,b)=>a+b,0)/vals.length:null,track=h('div','cv-track'),fill=h('span','');
 fill.style.width=(count?100*vals.length/count:0)+'%';track.append(fill);
 const title=h('span','',asset.replace('USD','')),val=h('strong','',avg===null?'En attente':percent(avg));
 val.append(h('small','','Mesurés : '+vals.length+'/'+count));
 put(assetHost,put(h('div','cv-asset'),title,track,val));
}
const blocks=[{label:'Mesurés',n:observed.length,color:'#74d5a2'},{label:'Sans relevé',n:waiting.length,color:'#e3a972'}];
for(const b of blocks){const part=h('span','');part.style.width=(items.length?b.n/items.length*100:0)+'%';part.style.background=b.color;snapshot.append(part);
 const span=h('span','',b.label+' : '+b.n);const dot=h('i','cv-dot');dot.style.setProperty('--cv-color',b.color);span.prepend(dot);snapshotLegend.append(span)}
const rank=card('Classement visuel des 36 nouveaux robots','Performance nette simulée depuis le début de leur propre suivi. Ce classement ne prédit pas les résultats futurs.');
const rankHost=h('div','cv-ranking');put(rank,rankHost);view.append(rank);
const ordered=[...items].sort((a,b)=>(net(b)??-Infinity)-(net(a)??-Infinity));
const range=Math.max(1,...observed.map(t=>Math.abs(t.net_pct)));
ordered.forEach((t,i)=>{
 const v=net(t),row=h('div','cv-rank-row'),track=h('div','cv-rank-track'),zero=h('span','cv-zero');
 track.append(zero);
 if(v!==null){const bar=h('span','cv-rank-bar'+(v<0?' cv-negative':''));const w=Math.min(50,Math.abs(v)/range*49);
 bar.style.left=(v>=0?50:50-w)+'%';bar.style.width=Math.max(v===0?0:1,w)+'%';track.append(bar)}
 const label=h('span','',short(t));label.title=short(t)+' · '+(sources[t.source]||t.source||'Source inconnue');
 put(row,h('span','',String(i+1)),label,track,h('strong',v===null?'—':percent(v)));rankHost.append(row);
});
const explorer=card('Explorer les robots un par un','Recherche et filtres, puis clique sur un robot pour afficher ses résultats, son risque et sa courbe.');
const controls=h('div','cv-filters'),search=h('input',''),market=h('select',''),origin=h('select',''),sort=h('select','');
search.type='search';search.placeholder='Rechercher un robot…';search.setAttribute('aria-label','Rechercher un robot');
function options(select,entries){for(const [v,label] of entries){const o=h('option','',label);o.value=v;select.append(o)}return select}
options(market,[['all','Tous les marchés'],...assetEntries.map(([a])=>[a,a.replace('USD','')])]);
const origins=[...new Set(items.map(t=>t.source).filter(Boolean))].sort();
options(origin,[['all','Toutes les origines'],...origins.map(v=>[v,sources[v]||v])]);
options(sort,[['return','Rendement décroissant'],['drawdown','Risque (baisse)'],['days','Plus anciens suivis'],['name','Nom / marché'],['awaiting','En attente en premier']]);
for(const [el,aria] of [[market,'Filtrer les marchés'],[origin,'Filtrer les origines'],[sort,'Trier les robots']])el.setAttribute('aria-label',aria);
put(controls,search,market,origin,sort);put(explorer,controls);
const layout=h('div','cv-layout'),listing=h('div','cv-panel'),listTitle=h('h3','cv-section-title','Répertoire interactif'),count=h('p','cv-muted'),directory=h('div','cv-directory');
put(listing,listTitle,count,directory);
const detail=h('div','cv-panel');put(layout,listing,detail);explorer.append(layout);view.append(explorer);
const state={id:items[0]?.id||null};
function compareBar(name,value,color,maximum){
 const row=h('div','cv-compare-row'),bar=h('div','cv-compare-track'),inside=h('span','');
 inside.style.background=color;inside.style.width=Math.max(0,Math.min(100,100*value/(maximum||20)))+'%';bar.append(inside);
 return put(row,h('span','',name),bar,h('strong','',money(value)));
}
function stat(label,value){const box=h('div','cv-stat');return put(box,h('small','',label),h('strong','',value))}
function show(t){
 state.id=t.id;detail.replaceChildren();
 const top=h('div','cv-detail-title');
 put(top,h('h3','',short(t)),badge(stateLabel(t),measured(t)?'':'cv-wait'));detail.append(top);
 put(detail,h('p','cv-muted','Origine : '+(sources[t.source]||t.source||'Non précisée')+' · Identifiant : '+t.id));
 const stats=h('div','cv-detail-grid'),v=net(t);
 for(const entry of [
 ['Capital fictif',money(capital(t))],['Rendement net',percent(v)],
 ['Écart vs Hold',percent(valid(t.excess_vs_hold_points)?t.excess_vs_hold_points:null)+' pts'],
 ['Trades clôturés',valid(t.closed_trades)?String(t.closed_trades):'—'],
 ['Jours suivis',valid(t.observed_days)?String(t.observed_days):'—'],
 ['Baisse maximale',valid(t.max_drawdown_pct)?percent(t.max_drawdown_pct):'—']
 ])stats.append(stat(...entry));
 detail.append(stats);
 put(detail,h('h4','cv-subhead','Courbe individuelle · capital fictif / Hold'));
 const plot=h('div','cv-chart'),rows=points(t),s=rows.map(p=>({t:p.t,v:p.equity_usd,h:p.hold_equity_usd}));
 const ok=lineChart(plot,s,'Robot '+short(t),'Aucun historique individuel daté disponible pour le moment. La première observation apparaîtra ici automatiquement.');
 if(!ok&&rows.length===1){
  plot.className='cv-chart';
  const one=rows[0],max=Math.max(one.equity_usd,one.hold_equity_usd,20);
  put(plot,h('p','cv-muted','Premier relevé du '+stamp(one.t)+' · comparaison ponctuelle :'),
  compareBar('Robot',one.equity_usd,'#88e5ae',max),compareBar('Hold',one.hold_equity_usd,'#90a6b6',max));
 }
 detail.append(plot);
 put(detail,h('p','cv-foot',rows.length===0?'Aucun point enregistré.':rows.length===1?'1 point réel. Le graphique linéaire exige deux dates distinctes.':rows.length+' observations datées disponibles, sans points historiques inventés.'));
 if(rows.length>=2){const latest=rows[rows.length-1],previous=rows[rows.length-2];detail.append(h('p','cv-muted','Dernier relevé : '+stamp(latest.t)+' · variation depuis le point précédent : '+money(latest.equity_usd-previous.equity_usd)+'.'))}
 detail.append(h('h4','cv-subhead','Risque et niveau de preuve'));
 const dd=valid(t.max_drawdown_pct)?Math.max(0,t.max_drawdown_pct):0;
 const risk=h('div','cv-meter'),riskbar=h('span','');riskbar.style.width=Math.min(100,dd)+'%';risk.append(riskbar);detail.append(risk);
 put(detail,h('p','cv-muted','Baisse maximale observée : '+(valid(t.max_drawdown_pct)?percent(dd):'inconnue')+'. '+'Cette jauge décrit les pertes passées du test, pas un risque futur garanti.'));
 const evidence=t.sufficient_evidence?'Des données permettent un examen humain. La stratégie n’est ni automatiquement validée ni autorisée à traiter de l’argent réel.':measured(t)?'Phase d’observation : nombre de journées, opérations clôturées et robustesse encore insuffisants pour conclure.':'Aucun résultat prospectif disponible : attendre le premier cours quotidien clôturé.';
 put(detail,h('p','cv-foot',evidence));
 directory.querySelectorAll('button[data-robot]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.robot===state.id)));
}
function render(){
 const query=clean(search.value);
 let filtered=items.filter(t=>(market.value==='all'||t.asset===market.value)&&(origin.value==='all'||t.source===origin.value)&&(!query||clean(short(t)+' '+t.id+' '+(sources[t.source]||t.source||'')).includes(query)));
 switch(sort.value){
 case 'drawdown':filtered.sort((a,b)=>(b.max_drawdown_pct||0)-(a.max_drawdown_pct||0));break;
 case 'days':filtered.sort((a,b)=>(b.observed_days||0)-(a.observed_days||0));break;
 case 'name':filtered.sort((a,b)=>short(a).localeCompare(short(b)));break;
 case 'awaiting':filtered.sort((a,b)=>(measured(a)?1:0)-(measured(b)?1:0));break;
 default:filtered.sort((a,b)=>(net(b)??-Infinity)-(net(a)??-Infinity));}
 count.textContent=filtered.length+' / '+items.length+' robots affichés';
 directory.replaceChildren();
 for(const t of filtered){
  const b=h('button','cv-item');b.type='button';b.dataset.robot=t.id;b.setAttribute('aria-pressed',String(t.id===state.id));
  const title=h('div','cv-item-top'),v=net(t);
  put(title,h('strong','',short(t)),h('span','cv-item-pct '+(v===null?'cv-neutral':v<0?'cv-neg':v>0?'cv-pos':'cv-neutral'),percent(v)));
  put(b,title,h('small','',(sources[t.source]||t.source||'Source inconnue')+' · '+(t.observed_days||0)+' j · '+(t.closed_trades||0)+' trades'));
  b.addEventListener('click',()=>show(t));directory.append(b);
 }
 if(!filtered.length)directory.append(h('p','cv-empty','Aucun robot ne correspond à ces filtres.'));
}
for(const el of [search,market,origin,sort])el.addEventListener(el===search?'input':'change',render);
render();if(items.length)show(items[0]);else put(detail,h('p','cv-empty','Aucun robot prospectif publié pour le moment.'));
view.append(h('p','cv-foot','Source : rapports de recherche prospectifs, actualisés lors des publications automatiques. Les 36 robots d’origine restent visibles dans « Robots ». Les graphiques sont descriptifs, sans rendement garanti, et aucune opération réelle n’est effectuée.'));
})();
