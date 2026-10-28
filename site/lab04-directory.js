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
