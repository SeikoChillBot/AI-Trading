/* Lab 04: unified paper strategy directory. */
(function(){
'use strict';
const L=window.SeikoV4;if(!L)return;
const $=id=>document.getElementById(id);
let scope='all',search='',sort='return',state='all',asset='all',opened=null;
const entries=[...L.cr.map(r=>({...r,kind:'crypto',initial:20,name:r.strategy.replaceAll('_',' ').toUpperCase(),marketName:'Crypto'})),...L.mr.map(r=>({...r,kind:'multi',initial:Number(r.initial_usd||1000),name:r.asset+' '+(r.strategy.endsWith('_hold')?'Conservation':'Tendance SMA20'),marketName:r.market}))];
const n=v=>Number(v)||0;
function card(r){
 const b=document.createElement('button');b.type='button';b.className='robot-row';
 const ico=document.createElement('span');ico.className='coin-icon is-market';
 ico.textContent=r.kind==='crypto'?({BTC:'₿',ETH:'Ξ',SOL:'◎'}[r.asset.slice(0,3)]||'◈'):r.asset.slice(0,2);
 const mid=document.createElement('span');mid.className='robot-row-middle';
 const title=document.createElement('span');title.className='robot-row-name';
 title.textContent=r.name;
 const detail=document.createElement('span');detail.className='robot-row-sub';
 detail.textContent=(r.kind==='crypto'?'CRYPTO':'MULTI-ACTIFS')+' · '+r.marketName+' · '+n(r.trades)+' ordre(s)';
 mid.append(title,detail);
 const right=document.createElement('span');right.className='robot-row-right';
 const cap=document.createElement('strong');cap.textContent=L.money(r.capital_usd);
 const pct=document.createElement('small');pct.className=L.tone(n(r.return_pct));pct.textContent=L.pct(n(r.return_pct));
 right.append(cap,pct);b.append(ico,mid,right);b.addEventListener('click',()=>detailSheet(r));return b;
}
function render(){
 let rows=entries.filter(r=>(scope==='all'||r.kind===scope)&&
 (state==='all'||state==='positive'&&n(r.return_pct)>0||state==='negative'&&n(r.return_pct)<0||state==='inactive'&&n(r.trades)===0)&&
 (scope!=='crypto'||asset==='all'||r.asset.startsWith(asset))&&
 (!search||[r.name,r.marketName,r.asset].join(' ').toLocaleLowerCase('fr').includes(search)));
 if(sort==='return')rows.sort((a,b)=>n(b.return_pct)-n(a.return_pct));
 else if(sort==='activity')rows.sort((a,b)=>n(b.trades)-n(a.trades)||n(b.return_pct)-n(a.return_pct));
 else rows.sort((a,b)=>a.name.localeCompare(b.name,'fr'));
 const host=$('robot-list');if(!host)return;host.replaceChildren();
 L.put('robots-count',rows.length+' / '+entries.length+' stratégies');
 if(!rows.length){const empty=document.createElement('div');empty.className='empty-list';empty.textContent='Aucune stratégie pour ces filtres.';host.append(empty)}
 rows.forEach(r=>host.append(card(r)));
 const coins=$('crypto-asset-filters');if(coins)coins.hidden=scope!=='crypto';
 document.querySelectorAll('[data-robot-lab]').forEach(b=>{let yes=b.dataset.robotLab===scope;b.classList.toggle('is-active',yes);b.setAttribute('aria-pressed',String(yes))});
}
function detailSheet(r){
 opened=r;
 const crypto=r.kind==='crypto';
 const set=(id,value)=>L.put(id,value);
 set('sheet-name',r.name);set('sheet-capital',L.money(r.capital_usd));
 set('sheet-return',L.pct(n(r.return_pct)));
 set('sheet-asset',r.asset);
 set('sheet-category',crypto?'Crypto':'Multi-actifs');
 set('sheet-trades',String(r.trades));
 set('sheet-fees',L.money(r.fees_usd,3));
 set('sheet-timeframe',crypto?r.timeframe_min+' min':'1 séance');
 $('sheet-return').className=L.tone(n(r.return_pct));
 $('sheet-coin').className='coin-icon is-market';
 set('sheet-coin',crypto?({BTC:'₿',ETH:'Ξ',SOL:'◎'}[r.asset.slice(0,3)]||'◈'):r.asset.slice(0,2));
 set('sheet-description',(r.strategy.endsWith('_hold')?'Conservation longue durée.':'Stratégie de tendance.')+(crypto?' Carnet Kraken simulé.':' Cotations publiques indicatives, coûts estimés ; dividendes non modélisés.'));
 const mates=crypto?L.cr:L.mr;
 const hold=mates.find(x=>x.asset===r.asset&&x.strategy.endsWith('_hold'));
 set('sheet-benchmark',hold?L.pct(n(r.return_pct)-n(hold.return_pct)):'—');
 set('sheet-benchmark-note','Écart indicatif avec conservation du même actif. Profils de risque différents.');
 const initial=r.initial,series=[initial];
 const source=(crypto?L.D.history:L.m.history)||[];
 source.forEach(item=>{if(item.strategy===r.strategy&&Number.isFinite(Number(item.capital_usd)))series.push(Number(item.capital_usd))});
 let peak=initial,worst=0;for(const v of series){peak=Math.max(peak,v);if(peak>0)worst=Math.max(worst,100*(peak-v)/peak)}
 set('sheet-drawdown',worst.toLocaleString('fr-FR',{maximumFractionDigits:2})+' %');
 const host=$('sheet-chart');host.replaceChildren();
 const w=420,h=150,lo=Math.min(...series),hi=Math.max(...series);
 const span=Math.max((hi-lo)*1.2,initial*.005),mid=(lo+hi)/2;
 const path=series.map((v,i)=>(i?'L':'M')+(8+i*(w-16)/Math.max(1,series.length-1)).toFixed(1)+' '+(h/2-(v-mid)/span*110).toFixed(1)).join(' ');
 const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
 svg.setAttribute('viewBox','0 0 '+w+' '+h);svg.style.width='100%';svg.style.height='100%';
 svg.innerHTML='<path d="'+path+'" fill="none" stroke="'+(n(r.return_pct)>=0?'#b9f477':'#ff8497')+'" stroke-width="2.6" stroke-linecap="round"/>';
 host.append(svg);
 $('robot-sheet').hidden=false;document.body.style.overflow='hidden';$('close-sheet').focus();
}
document.querySelectorAll('[data-robot-lab]').forEach(b=>b.addEventListener('click',()=>{
 scope=b.dataset.robotLab;asset='all';render();
}));
const input=$('robot-search'),sorting=$('robot-sort');
if(input)input.addEventListener('input',e=>{search=e.target.value.toLocaleLowerCase('fr').trim();render()});
if(sorting)sorting.addEventListener('change',e=>{sort=e.target.value;render()});
document.querySelectorAll('[data-filter]').forEach(b=>b.addEventListener('click',()=>{state=b.dataset.filter;render()}));
document.querySelectorAll('[data-coin]').forEach(b=>b.addEventListener('click',()=>{asset=b.dataset.coin;render()}));
document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>{if(b.dataset.view==='robots')render()}));
window.addEventListener('hashchange',()=>{if(location.hash==='#robots')render()});
L.openRobotMarket=name=>{scope='multi';search=name.toLocaleLowerCase('fr');if(input)input.value=name;render();L.goto('robots')};
L.refreshers.push(()=>{render();if(opened&&!$('robot-sheet').hidden){L.put('sheet-capital',L.money(opened.capital_usd));L.put('sheet-fees',L.money(opened.fees_usd,3))}});
render();
})();
