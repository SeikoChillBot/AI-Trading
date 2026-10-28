/* Seiko Lab / 04. Trading data are never modified here. */
(function(){
 'use strict';
 const D=DATA, m=D.multi_asset||{};
 const cr=Array.isArray(D.rows)?D.rows:[];
 const mr=m.ready&&Array.isArray(m.rows)&&m.rows.length===18?m.rows:[];
 const init={crypto:cr.length*20,multi:mr.reduce((a,r)=>a+Number(r.initial_usd||1000),0)};
 const total={crypto:cr.reduce((a,r)=>a+Number(r.capital_usd),0),multi:mr.reduce((a,r)=>a+Number(r.capital_usd),0)};
 const start={crypto:D.launched_at,multi:m.started_at};
 const pct=n=>(n>0?'+':'')+Number(n).toLocaleString('fr-FR',{minimumFractionDigits:2,maximumFractionDigits:2})+' %';
 window.SeikoV4={D,m,cr,mr,init,total,start,pct,ready:mr.length===18};
})();
