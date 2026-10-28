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
 const money=(v,dec=2)=>(Number(v)/(eur()?rate:1)).toLocaleString('fr-FR',{minimumFractionDigits:dec,maximumFractionDigits:dec})+(eur()?' €':' $');
 const tone=n=>n>0.00001?'positive':n<-.00001?'negative':'neutral';
 const put=(id,v)=>{const node=document.getElementById(id);if(node)node.textContent=v};
 const stamp=t=>{const d=Date.parse(t);return Number.isFinite(d)?new Intl.DateTimeFormat('fr-FR',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit',timeZone:'Europe/Paris'}).format(new Date(d)):'En attente'};
 const day=t=>{const d=Date.parse(t);return Number.isFinite(d)?'J+'+Math.max(0,Math.floor((Date.now()-d)/86400000)):'Non démarré'};
 function series(log,items,initial,startTime){
  const cache=new Map(items.map(r=>[r.strategy,initial(r)])),pts=[];
  const t=Date.parse(startTime);
  if(Number.isFinite(t))pts.push({t:t-1,v:items.reduce((n,r)=>n+initial(r),0)});
  let group='';
  const flush=()=>{if(group){const at=Date.parse(group);if(Number.isFinite(at))pts.push({t:at,v:[...cache.values()].reduce((a,b)=>a+b,0)})}};
  for(const row of log||[]){if(!cache.has(row.strategy))continue;
   if(row.recorded_at!==group){flush();group=row.recorded_at}
   const v=Number(row.capital_usd);if(Number.isFinite(v))cache.set(row.strategy,v);
  }flush();
  if(pts.length===0)pts.push({t:Date.now()-1,v:items.reduce((a,r)=>a+initial(r),0)});
  const end=items.reduce((n,r)=>n+Number(r.capital_usd),0);
  if(Math.abs(pts[pts.length-1].v-end)>.00001)pts.push({t:Date.now(),v:end});
  if(pts.length===1)pts.push({t:pts[0].t+1,v:end});
  return pts;
 }
 const history={crypto:series(D.history,cr,()=>20,D.launched_at),
  multi:mr.length?series(m.history,mr,r=>Number(r.initial_usd||1000),m.started_at):[]};
 window.SeikoV4={D,m,cr,mr,init,total,start,pct,money,tone,put,stamp,day,history,ready:mr.length===18};
})();
