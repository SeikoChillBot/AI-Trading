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
function renderChart(){
 const host=$('portfolio-chart');if(!host)return;host.replaceChildren();
 const raw=L.history[selected]||[],end=raw[raw.length-1]?.t||Date.now();
 const windowMs=range==='1d'?86400000:range==='7d'?604800000:Infinity;
 let series=raw.filter(p=>p.t>=end-windowMs);if(series.length<2)series=raw.slice(-2);
 if(series.length<2)return;
 const values=series.map(p=>p.v),minimum=Math.min(...values),maximum=Math.max(...values);
 const margin=Math.max((maximum-minimum)*.22,(L.init[selected]||1)*.0002);
 const low=minimum-margin,high=maximum+margin,W=760,H=210;
 const xy=series.map((p,i)=>({x:14+i*(W-28)/(series.length-1),y:18+(H-36)*(1-(p.v-low)/(high-low))}));
 const line=xy.map((p,i)=>(i?'L':'M')+p.x.toFixed(2)+' '+p.y.toFixed(2)).join(' ');
 const last=xy[xy.length-1],up=values.at(-1)>=values[0];
 const color=up?'#b9f477':'#ff8497',grad='lab04-grad';
 const fill=line+' L'+last.x+' '+(H-10)+' L'+xy[0].x+' '+(H-10)+' Z';
 const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
 svg.setAttribute('viewBox','0 0 '+W+' '+H);svg.setAttribute('preserveAspectRatio','none');
 svg.style.width='100%';svg.style.height='100%';svg.setAttribute('role','img');
 svg.setAttribute('aria-label','Courbe '+labelFor(selected)+' : '+L.money(values[0])+' à '+L.money(values.at(-1)));
 svg.innerHTML='<defs><linearGradient id="'+grad+'" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="'+color+'" stop-opacity=".23"/><stop offset="100%" stop-color="'+color+'" stop-opacity="0"/></linearGradient></defs>'+
 '<path d="'+fill+'" fill="url(#'+grad+')"/>'+
 '<path d="'+line+'" fill="none" stroke="'+color+'" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'+
 '<circle cx="'+last.x+'" cy="'+last.y+'" r="5" fill="'+color+'" stroke="#172831" stroke-width="3"/>';
 host.append(svg);
}
const labelFor=v=>v==='crypto'?'crypto':'multi-actifs';
document.querySelectorAll('[data-lab]').forEach(b=>b.addEventListener('click',()=>L.selectWallet(b.dataset.lab)));
document.querySelectorAll('[data-range]').forEach(b=>b.addEventListener('click',()=>{range=b.dataset.range;draw()}));
document.querySelectorAll('[data-currency]').forEach(b=>b.addEventListener('click',()=>L.refresh()));
document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>L.refresh()));
window.addEventListener('hashchange',()=>L.refresh());
on.push(draw);
draw();
})();
