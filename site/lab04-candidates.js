/* Dedicated prospective paper robot charts, no trading actions. */
(function(){
'use strict';
const view=document.getElementById('view-candidates');
if(!view)return;
const forward=DATA.strategy_forward||{};
const charts=DATA.strategy_forward_charts||{};
const select=document.getElementById('candidate-select');
const summary=document.getElementById('candidate-summary');
const chart=document.getElementById('candidate-chart');
const note=document.getElementById('candidate-chart-note');
const trials=Array.isArray(forward.trials)?forward.trials.filter(x=>x&&typeof x.id==='string'):[];
trials.forEach((t,i)=>{
 const o=document.createElement('option');
 o.value=String(i);
 o.textContent=(t.asset||'?')+' / '+(t.logic||'?')+' / '+t.id;
 select.append(o);
});
function draw(){
 summary.replaceChildren();chart.replaceChildren();
 const t=trials[Number(select.value)||0];
 if(!t){note.textContent='Aucune stratégie prospective publiée.';return}
 const p=document.createElement('p');
 p.textContent='Capital fictif : '+(20*(1+Number(t.net_pct||0)/100)).toFixed(2)+
 ' USD | rendement net : '+Number(t.net_pct||0).toFixed(2)+
 ' % | trades clôturés : '+Number(t.closed_trades||0)+
 ' | drawdown : '+Number(t.max_drawdown_pct||0).toFixed(2)+
 ' % | journées : '+Number(t.observed_days||0)+
 ' | statut : '+String(t.status||'en attente');
 summary.append(p);
 const all=charts.series&&charts.series[t.id];
 const points=Array.isArray(all)?all.filter(x=>x&&Number.isFinite(x.equity_usd)&&Number.isFinite(x.hold_equity_usd)):[];
 if(points.length<2){note.textContent='Courbe en attente de deux observations futures distinctes. Aucun historique reconstruit artificiellement.';return}
 const ns='http://www.w3.org/2000/svg';
 const svg=document.createElementNS(ns,'svg');
 svg.setAttribute('viewBox','0 0 600 220');
 svg.setAttribute('role','img');
 svg.setAttribute('aria-label','Capital fictif et benchmark Hold');
 svg.style.width='100%';
 const vals=points.flatMap(x=>[x.equity_usd,x.hold_equity_usd]);
 let min=Math.min(...vals),max=Math.max(...vals);
 if(min===max){min-=0.5;max+=0.5}
 for(const pair of [['hold_equity_usd','#94a3b8'],['equity_usd','#22c55e']]){
  const line=document.createElementNS(ns,'polyline');
  line.setAttribute('fill','none');
  line.setAttribute('stroke',pair[1]);
  line.setAttribute('stroke-width','3');
  line.setAttribute('points',points.map((x,i)=>
    (30+i*540/(points.length-1)).toFixed(1)+','+
    (190-(x[pair[0]]-min)/(max-min)*160).toFixed(1)).join(' '));
  svg.append(line);
 }
 chart.append(svg);
 note.textContent='Vert : stratégie | Gris : Hold | Capital fictif en USD | Observations prospectives uniquement';
}
select.addEventListener('change',draw);
draw();
})();
