/* Lab 04: unified paper strategy directory. */
(function(){
'use strict';
const L=window.SeikoV4;if(!L)return;
const $=id=>document.getElementById(id);
let scope='all',search='',sort='return',state='all',asset='all',opened=null;
const entries=[...L.cr.map(r=>({...r,kind:'crypto',initial:20,name:r.strategy.replaceAll('_',' ').toUpperCase(),marketName:'Crypto'})),...L.mr.map(r=>({...r,kind:'multi',initial:Number(r.initial_usd||1000),name:r.asset+' '+(r.strategy.endsWith('_hold')?'Conservation':'Tendance SMA20'),marketName:r.market}))];
const n=v=>Number(v)||0;
