/* Lab 04 — independent home dashboard, no trading operations. */
(function(){
'use strict';
const L=window.SeikoV4;if(!L)return;
const $=id=>document.getElementById(id);
let selected=L.ready?'multi':'crypto',range='1d';
try{const saved=localStorage.getItem('seiko-lab04-wallet');if(saved==='crypto'||saved==='multi'&&L.ready)selected=saved}catch(e){}
const on=[];L.refreshers=on;
L.refresh=()=>on.forEach(fn=>fn());
L.selectWallet=v=>{if(v==='crypto'||v==='multi'&&L.ready){selected=v;
 try{localStorage.setItem('seiko-lab04-wallet',v)}catch(e){}
 draw();}};
L.goto=slug=>{const b=document.querySelector('[data-view="'+slug+'"]');if(b)b.click()};
function summary(){
 const multiCount=L.mr.length;
 L.put('overview-bots',L.cr.length+multiCount);
 L.put('switch-all-count',L.cr.length+multiCount);
 L.put('overview-crypto-value',L.money(L.total.crypto));
 L.put('overview-crypto-return',L.pct((L.total.crypto/L.init.crypto-1)*100));
 L.put('overview-crypto-age',L.day(L.start.crypto));
 L.put('overview-multi-value',L.ready?L.money(L.total.multi):'En attente');
 L.put('overview-multi-return',L.ready?L.pct((L.total.multi/L.init.multi-1)*100):'Sans relevé');
 L.put('overview-multi-age',L.day(L.start.multi));
 L.put('stat-bots',String(L.cr.length+multiCount).padStart(2,'0'));
 L.put('stat-trades',[...L.cr,...L.mr].reduce((n,r)=>n+Number(r.trades||0),0).toLocaleString('fr-FR'));
 for(const scope of ['crypto','multi']){
  const e=$('overview-'+scope+'-return');if(e)e.className=L.tone((L.total[scope]/(L.init[scope]||1)-1)*100);
 }
 document.querySelectorAll('[data-lab]').forEach(b=>{
  const active=b.dataset.lab===selected;b.classList.toggle('is-selected',active);
  b.setAttribute('aria-pressed',String(active));b.disabled=b.dataset.lab==='multi'&&!L.ready;
 });
}
function draw(){
 summary();
 const label=selected==='crypto'?'CRYPTO · KRAKEN':'MULTI-ACTIFS · 9 INSTRUMENTS';
 L.put('hero-portfolio-kind',label);L.put('hero-capital-label','VALEUR ESTIMÉE · '+(selected==='crypto'?'CRYPTO':'MULTI-ACTIFS'));
 const amt=L.total[selected],base=L.init[selected],gain=amt-base;
 L.put('portfolio-value',L.money(amt));L.put('portfolio-profit',(gain>0?'+':'')+L.money(gain));
 L.put('portfolio-percent',L.pct(base?gain/base*100:0));
 for(const id of ['portfolio-profit','portfolio-percent']){
  const e=$(id);if(e)e.className=(id==='portfolio-profit'?'profit-amount ':'profit-percent ')+L.tone(gain);
 }
 L.put('hero-since','Depuis '+L.stamp(L.start[selected]));
 L.put('chart-clarification',selected==='crypto'?
  'Crypto : montant récupérable après vente estimée, incluant frais et carnet Kraken.':
  'Multi-actifs : prix publics indicatifs, frais d’exécution et de sortie estimés ; dividendes non intégrés.');
 const tag=document.querySelector('.hero-small-tag');if(tag)tag.textContent='FICTIF · '+(selected==='crypto'?'SPOT':'PRIX INDICATIFS');
 L.put('chart-period',range==='all'?'Depuis le lancement':range==='7d'?'7 derniers jours':'24 dernières heures');
 L.put('chart-last','Dernier : '+L.money(amt));
 renderChart();
}
