/* Lab 04: transparent comparative research, never a combined trade history. */
(function(){
'use strict';
const L=window.SeikoV4;if(!L)return;
const $=id=>document.getElementById(id);
const ce=(tag,className,text)=>{const node=document.createElement(tag);if(className)node.className=className;if(text!==undefined)node.textContent=text;return node};
function paint(){
 const host=$('cross-scorecard');if(!host)return;host.replaceChildren();
 for(const type of ['crypto','multi']){
  if(type==='multi'&&!L.ready)continue;
  const start=L.init[type],value=L.total[type],difference=value-start;
  const box=ce('article','cross-score');
  const head=ce('div','cross-score-top');
  head.append(ce('strong','',type==='crypto'?'Crypto / Kraken':'Multi-actifs / prix indicatifs'),
              ce('small','',L.day(L.start[type])));
  const amount=ce('strong','cross-score-money',L.money(value));
  const meta=ce('div','cross-score-meta');
  const gain=ce('em',L.tone(difference),L.pct(start?100*difference/start:0));
  meta.append(ce('span','','Départ '+L.money(start)),gain);
  box.append(head,amount,meta);host.append(box);
 }
 const risk=$('cross-risk-grid');risk.replaceChildren();
 const stats=[
  ['ORDRES CRYPTO',L.cr.reduce((n,r)=>n+Number(r.trades||0),0)],
  ['ORDRES MULTI-ACTIFS',L.mr.reduce((n,r)=>n+Number(r.trades||0),0)],
  ['FRAIS CRYPTO',L.money(L.cr.reduce((n,r)=>n+Number(r.fees_usd||0),0),3)],
  ['FRAIS MULTI-ACTIFS',L.money(L.mr.reduce((n,r)=>n+Number(r.fees_usd||0),0),3)],
  ['QUALITÉ DE L’ÉCHANTILLON','En observation'],
  ['MARCHÉS MESURÉS',L.ready?'9 références':'En attente']
 ];
 for(const [label,value] of stats){const card=ce('div','');card.append(ce('small','',label),ce('strong','',value));risk.append(card)}
 drawMultiChart();
}
function drawMultiChart(){
 const host=$('multi-analysis-chart');if(!host)return;host.replaceChildren();
 if(!L.ready){host.append(ce('p','micro-note','La courbe apparaîtra avec le premier relevé multi-actifs.'));return}
 const points=L.history.multi;if(points.length<2)return;
 const values=points.map(p=>p.v),low=Math.min(...values),high=Math.max(...values),margin=Math.max((high-low)*.25,5);
 const w=700,h=170;const coords=points.map((p,i)=>({x:5+i*690/(points.length-1),y:9+(h-18)*(1-(p.v-(low-margin))/(high-low+2*margin))}));
 const d=coords.map((v,i)=>(i?'L':'M')+v.x.toFixed(2)+' '+v.y.toFixed(2)).join(' ');
 const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
 svg.setAttribute('viewBox','0 0 '+w+' '+h);svg.setAttribute('preserveAspectRatio','none');
 svg.setAttribute('role','img');svg.setAttribute('aria-label','Historique multi-actifs depuis le lancement');
 svg.style.width='100%';svg.style.height='100%';
 const color=values.at(-1)>=values[0]?'#b9f477':'#ff8497';
 svg.innerHTML='<path d="'+d+'" fill="none" stroke="'+color+'" stroke-width="2.8" stroke-linejoin="round"/>';
 host.append(svg);
}
function marketCards(){
 if(!L.ready)return;
 const box=$('multi-market-groups');if(!box)return;box.replaceChildren();
 const groups=new Map();
 for(const r of L.mr){const list=groups.get(r.asset)||[];list.push(r);groups.set(r.asset,list)}
 for(const [asset,rows] of groups){
  const start=rows.reduce((n,r)=>n+Number(r.initial_usd||20),0);
  const total=rows.reduce((n,r)=>n+Number(r.capital_usd),0);
  const card=ce('article','multi-group'),button=ce('button','multi-group-link');
  button.type='button';button.setAttribute('aria-label','Voir les robots '+asset);
  const head=ce('div','multi-group-head');
  head.append(ce('h3','',asset+' · '+rows[0].label));
  const pct=ce('small',L.tone(total-start),L.pct((total/start-1)*100));
  head.append(pct);
  const sub=ce('p','multi-group-sub',rows[0].market.toUpperCase()+' · 2 robots');
  const foot=ce('div','multi-group-summary');
  foot.append(ce('strong','',L.money(total)),ce('small','',rows.some(r=>r.pricing_quality==='STALE')?'Cotations périmées':rows.some(r=>r.pricing_quality==='NO_DATA')?'Sans cours':'Valeur indicative'));
  button.append(head,sub,foot,ce('span','multi-group-open','Voir les deux stratégies →'));
  button.addEventListener('click',()=>L.openRobotMarket&&L.openRobotMarket(asset));
  card.append(button);box.append(card);
 }
}
function foldResearch(){
 const anchor=document.querySelector('.market-workflow');
 if(!anchor||document.querySelector('.market-research-fold'))return;
 const details=ce('details','market-research-fold');
 const summary=ce('summary','','Découvrir les 13 univers et 42 pistes de recherche');
 details.append(summary);anchor.parentNode.insertBefore(details,anchor);
 for(const node of [anchor,document.querySelector('.market-section-heading'),
   document.querySelector('.market-search-wrap'),document.querySelector('.market-filters'),
   $('market-grid'),document.querySelector('.market-disclaimer')])if(node)details.append(node);
}
function refresh(){paint();marketCards();L.put('market-active-count',L.ready?'2':'1')}
foldResearch();
L.refreshers.push(refresh);
document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>{if(b.dataset.view==='analysis'||b.dataset.view==='explore')refresh()}));
refresh();
})();
