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
 const rate=Number(D.fx?.usd_per_eur),ref=Date.parse((D.fx?.reference_date||'')+'T12:00:00Z');
 const fxOk=D.fx?.source==='ECB'&&rate>.5&&rate<3.5&&Math.abs(Date.now()-ref)<9.5*86400000;
 const eur=()=>{try{return fxOk&&localStorage.getItem('seiko-trading-display-currency')==='EUR'}catch(e){return false}};
 const money=(v,dec=2)=>(Number(v)/(eur()?rate:1)).toLocaleString('fr-FR',{minimumFractionDigits:dec,maximumFractionDigits:dec})+(eur()?' €':' D,m,cr,mr,init,total,start,pct,money,tone,put,ready:mr.length===18};
})();
);
 const tone=n=>n>0.00001?'positive':n<-.00001?'negative':'neutral';
 const put=(id,v)=>{const node=document.getElementById(id);if(node)node.textContent=v};
 window.SeikoV4={D,m,cr,mr,init,total,start,pct,ready:mr.length===18};
})();
