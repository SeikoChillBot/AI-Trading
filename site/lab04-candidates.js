/* Candidate dashboard: observed paper-only values, never synthetic history. */
(function(){
'use strict';
const view=document.getElementById('view-candidates');if(!view)return;
const forward=(typeof DATA!=='undefined'&&DATA.strategy_forward)||{};
const charts=(typeof DATA!=='undefined'&&DATA.strategy_forward_charts)||{};
const trials=Array.isArray(forward.trials)?forward.trials.filter(x=>x&&typeof x.id==='string'):[];
const select=document.getElementById('candidate-select');
const summary=document.getElementById('candidate-summary');
const chart=document.getElementById('candidate-chart');
const note=document.getElementById('candidate-chart-note');
const usd=v=>Number(v).toLocaleString('fr-FR',{minimumFractionDigits:2,maximumFractionDigits:2})+' $';
const pct=v=>(Number(v)>0?'+':'')+Number(v).toFixed(2)+' %';
const safe=v=>Number.isFinite(Number(v))?Number(v):0;
const style=document.createElement('style');style.textContent=`
#view-candidates .candidate-kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px;margin:18px 0}
#view-candidates .candidate-kpi,#view-candidates .candidate-card,#view-candidates .candidate-detail{background:rgba(125,145,175,.07);border:1px solid rgba(150,165,190,.19);border-radius:14px;padding:15px}
#view-candidates .candidate-kpi small,#view-candidates .candidate-card small{display:block;opacity:.75;font-size:.78rem}
#view-candidates .candidate-kpi strong{display:block;font-size:1.35rem;margin-top:5px}
#view-candidates .candidate-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin:18px 0}
#view-candidates .candidate-card{color:inherit;text-align:left;cursor:pointer;font:inherit;min-width:0}
#view-candidates .candidate-card[aria-pressed="true"]{border-color:#7fcba4;background:rgba(90,190,145,.12)}
#view-candidates .candidate-card strong{display:block;font-size:1.04rem;margin-bottom:8px}
#view-candidates .candidate-card .candidate-stats{display:flex;justify-content:space-between;gap:8px;margin:9px 0}
#view-candidates .candidate-pill{display:inline-block;font-size:.77rem;border:1px solid rgba(150,165,190,.3);border-radius:20px;padding:3px 9px}
#view-candidates .candidate-chart-wrap{margin:15px 0;overflow:hidden}
#view-candidates .candidate-chart-wrap svg{display:block;width:100%;height:auto;max-height:290px}
#view-candidates .candidate-legend{display:flex;gap:18px;flex-wrap:wrap;font-size:.84rem;opacity:.85}
#view-candidates .candidate-legend span:before{content:'● ';color:var(--dot)}
#view-candidates .candidate-explainer{font-size:.9rem;opacity:.85;line-height:1.6}
`;document.head.append(style);
const heading=document.createElement('div');heading.className='candidate-kpis';
const kpis=[['ROBOTS EN OBSERVATION',String(trials.length)],['CAPITAL FICTIF TOTAL',usd(trials.reduce((s,t)=>s+20*(1+safe(t.net_pct)/100),0))],['TRADES CLÔTURÉS',String(trials.reduce((s,t)=>s+safe(t.closed_trades),0))],['ROBOTS VALIDÉS',String(trials.filter(t=>t.sufficient_evidence).length)]];
kpis.forEach(([label,value])=>{const el=document.createElement('div');el.className='candidate-kpi';const s=document.createElement('small');s.textContent=label;const b=document.createElement('strong');b.textContent=value;el.append(s,b);heading.append(el)});
summary.before(heading);
const expl=document.createElement('p');expl.className='candidate-explainer';expl.textContent='Chaque robot commence avec 20 $ fictifs. Les résultats affichés sont ceux des tests prospectifs, pas des gains réels. « En observation » signifie que le robot n’a pas encore assez de preuves pour être retenu.';heading.after(expl);
const grid=document.createElement('div');grid.className='candidate-grid';summary.before(grid);
const detail=document.createElement('div');detail.className='candidate-detail';summary.append(detail);
const list=[];
function series(t){const s=charts.series&&charts.series[t.id];return Array.isArray(s)?s.filter(x=>x&&Number.isFinite(x.equity_usd)&&Number.isFinite(x.hold_equity_usd)):[]}
function plot(t){
 chart.replaceChildren();chart.className='candidate-chart-wrap';
 const rows=series(t),values=rows.flatMap(x=>[x.equity_usd,x.hold_equity_usd]);
 if(!rows.length){note.textContent='Aucun relevé graphique disponible pour ce robot. Les chiffres ci-dessus restent consultables.';return}
 const min=Math.min(...values),max=Math.max(...values),margin=Math.max((max-min)*.13,.2),lo=min-margin,hi=max+margin;
 const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox','0 0 680 260');svg.setAttribute('role','img');svg.setAttribute('aria-label','Capital fictif du robot en vert et conservation du marché en gris');
 for(let i=0;i<4;i++){const y=20+i*66;const l=document.createElementNS(ns,'line');for(const [k,v] of Object.entries({x1:45,x2:655,y1:y,y2:y,stroke:'currentColor','stroke-opacity':'.14'}))l.setAttribute(k,v);svg.append(l)}
 for(const [key,color] of [['hold_equity_usd','#94a3b8'],['equity_usd','#34c98a']]){
  const coords=rows.map((r,i)=>[45+(rows.length===1?305:i*610/(rows.length-1)),220-(r[key]-lo)/(hi-lo)*190]);
  if(rows.length>1){const line=document.createElementNS(ns,'polyline');line.setAttribute('points',coords.map(p=>p.join(',')).join(' '));line.setAttribute('fill','none');line.setAttribute('stroke',color);line.setAttribute('stroke-width','3');svg.append(line)}
  for(const [x,y] of coords){const circle=document.createElementNS(ns,'circle');circle.setAttribute('cx',x);circle.setAttribute('cy',y);circle.setAttribute('r',rows.length===1?6:3);circle.setAttribute('fill',color);svg.append(circle)}
 }
 chart.append(svg);
 const legend=document.createElement('div');legend.className='candidate-legend';for(const [name,color] of [['Robot','#34c98a'],['Marché conservé (Hold)','#94a3b8']]){const span=document.createElement('span');span.style.setProperty('--dot',color);span.textContent=name;legend.append(span)}chart.append(legend);
 note.textContent=rows.length===1?'Premier point réel enregistré. La courbe se dessinera dès le deuxième relevé distinct. Aucun historique inventé.':rows.length+' relevés réels enregistrés. Évolution du capital fictif en dollars.';
}
function show(index){
 const t=trials[index];if(!t)return;select.value=String(index);
 list.forEach((el,i)=>el.setAttribute('aria-pressed',String(i===index)));
 detail.replaceChildren();
 const title=document.createElement('h3');title.textContent=(t.asset||'Marché')+' · '+(t.logic||'Stratégie');
 const p=document.createElement('p');p.textContent='Capital : '+usd(20*(1+safe(t.net_pct)/100))+' | Rendement : '+pct(t.net_pct)+' | Trades clôturés : '+safe(t.closed_trades)+' | Baisse maximale : '+pct(t.max_drawdown_pct)+' | Jours observés : '+safe(t.observed_days);
 const status=document.createElement('p');status.textContent=t.sufficient_evidence?'Statut : données suffisantes pour évaluation':'Statut : en observation, pas encore validé';
 detail.append(title,p,status);plot(t);
}
trials.forEach((t,i)=>{
 const opt=document.createElement('option');opt.value=String(i);opt.textContent=(t.asset||'?')+' · '+(t.logic||'?')+' · robot '+(i+1);select.append(opt);
 const card=document.createElement('button');card.type='button';card.className='candidate-card';card.setAttribute('aria-pressed','false');
 const title=document.createElement('strong');title.textContent=(i+1)+'. '+(t.asset||'Marché')+' · '+(t.logic||'Stratégie');
 const row=document.createElement('div');row.className='candidate-stats';const capital=document.createElement('span');capital.textContent=usd(20*(1+safe(t.net_pct)/100));const perf=document.createElement('span');perf.textContent=pct(t.net_pct);row.append(capital,perf);
 const small=document.createElement('small');small.textContent=safe(t.closed_trades)+' trades · '+safe(t.observed_days)+' jours observés';
 const pill=document.createElement('span');pill.className='candidate-pill';pill.textContent=t.sufficient_evidence?'Évaluation possible':'En observation';
 card.append(title,row,small,pill);card.addEventListener('click',()=>show(i));grid.append(card);list.push(card);
});
select.addEventListener('change',()=>show(Number(select.value)||0));
if(trials.length)show(0);else note.textContent='Aucun nouveau robot publié pour le moment.';
})();