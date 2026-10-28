(() => {
'use strict';
const $ = id => document.getElementById(id);
const START = 20;
const rawRows = Array.isArray(DATA.rows) ? DATA.rows : [];
const rows = rawRows.map(r => ({...r, capital_usd: Number(r.capital_usd), return_pct: Number(r.return_pct), trades: Number(r.trades), fees_usd: Number(r.fees_usd), timeframe_min: Number(r.timeframe_min) || 0}));
const byName = new Map(rows.map(r => [r.strategy, r]));
const history = Array.isArray(DATA.history) ? DATA.history : [];
// The trading model remains in USD. EUR is a display-only conversion.
const fxReference = DATA.fx && typeof DATA.fx === 'object' ? DATA.fx : null;
const usdPerEur = Number(fxReference?.usd_per_eur);
const fxDate = Date.parse(String(fxReference?.reference_date || '') + 'T12:00:00Z');
const fxAgeDays = (Date.now() - fxDate) / 86400000;
const fxAvailable = fxReference?.source === 'ECB' && Number.isFinite(usdPerEur) &&
  usdPerEur > .5 && usdPerEur < 3.5 && Number.isFinite(fxAgeDays) && fxAgeDays >= -1 && fxAgeDays <= 9.5;
let displayCurrency = 'USD';
try { if(fxAvailable && localStorage.getItem('seiko-trading-display-currency') === 'EUR') displayCurrency = 'EUR'; } catch (_) {}
const displayAmount = value => Number(value) / (displayCurrency === 'EUR' ? usdPerEur : 1);
const money = (n, digits=2) => displayAmount(n).toLocaleString('fr-FR',
  {minimumFractionDigits:digits,maximumFractionDigits:digits}) + (displayCurrency === 'EUR' ? ' €' : ' $');
const percentage = n => (n > 0 ? '+' : '') + Number(n).toLocaleString('fr-FR',{minimumFractionDigits:2,maximumFractionDigits:2}) + ' %';
const signedMoney = n => (n > 0 ? '+' : n === 0 ? '±' : '') + money(n);
const polarity = n => n > 0.000001 ? 'positive' : n < -0.000001 ? 'negative' : 'neutral';
const coinFor = asset => String(asset || '').replace(/(?:USDT|USD)$/,'').replace('/','').toUpperCase();
const nameFor = key => { const [asset,...parts] = key.split('_'); return asset.toUpperCase() + ' ' + parts.map(p => p === 'ema' ? 'EMA' : p === 'rsi' ? 'RSI' : p[0].toUpperCase()+p.slice(1)).join(' '); };
const descriptions = {
 hold:['Buy & Hold','Un achat initial, puis conservation de la cryptomonnaie, même lorsque son prix diminue.'],
 momentum:['Suivi de tendance','Recherche un mouvement durable au-dessus de la moyenne récente ; revend lorsque la tendance s’inverse.'],
 reversion:['Retour à la moyenne','Recherche un rebond après une baisse marquée par rapport à la moyenne récente des prix.'],
 breakout:['Cassure','Entre lorsque le prix dépasse ses précédents sommets ; sort sur rupture de support.'],
 rsi:['RSI','Utilise l’indice de force relative pour chercher des zones de survente et de reprise.'],
 ema_cross:['Croisement EMA','Compare une moyenne mobile exponentielle courte à une longue pour repérer les tendances.'],
 bollinger:['Bandes de Bollinger','Recherche un prix inhabituellement bas par rapport à ses bandes statistiques, puis un retour à la moyenne.'],
 volatility:['Cassure + volatilité','Recherche une cassure lorsque le marché présente une amplitude suffisamment importante.'],
 scalp_momentum:['Scalping · Momentum','Recherche une accélération de court terme et suit un seuil de sortie proche du sommet.'],
 scalp_trailing:['Scalping · Trailing','Suit un mouvement haussier rapide avec un seuil de sortie mobile.'],
 scalp_microtrend:['Scalping · Microtendance','Cherche plusieurs bougies haussières consécutives sur un horizon court.'],
 scalp_conservative:['Scalping · Sélectif','Tente de filtrer davantage les entrées sur les mouvements de très court terme.']
};
const info = r => descriptions[r.strategy.split('_').slice(1).join('_')] || ['Stratégie expérimentale','Robot en observation ; paramètres à consulter dans le code source.'];
const symbol = coin => coin === 'BTC' ? '₿' : coin === 'ETH' ? 'Ξ' : coin === 'SOL' ? '◎' : '◇';
const coinClass = coin => ['BTC','ETH','SOL'].includes(coin) ? 'coin-'+coin.toLowerCase() : 'coin-unknown';
const rawDate = DATA.updated;
function dateFR(value) { const date = new Date(value); return Number.isNaN(date.getTime()) ? 'Indisponible' : new Intl.DateTimeFormat('fr-FR',{timeZone:'Europe/Paris',day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit'}).format(date); }
function parseRecordedAt(s) { const m = String(s || '').match(/(\d{2})\/(\d{2})\/(\d{4})\s+à\s+(\d{2}):(\d{2})/); if(m) return Date.UTC(+m[3],+m[2]-1,+m[1],+m[4],+m[5]); const v = Date.parse(s); return Number.isFinite(v) ? v : NaN; }
const latest = rows.reduce((sum,r) => sum+r.capital_usd, 0);
const initial = rows.length*START;
const profit = latest-initial;
const totalTrades = rows.reduce((sum,r)=>sum+r.trades,0);

// The history contains updates at different candle timeframes. Reconstruct actual
// portfolio snapshots by their recording time, carrying forward unchanged robots.
function reconstruct() {
 const cap = new Map(rows.map(r=>[r.strategy,START]));
 const snapshots = [];
 let group = null, timestamp = 0;
 const flush = () => { if(group === null) return; snapshots.push({label:group,t:timestamp,capital:[...cap.values()].reduce((a,b)=>a+b,0),values:new Map(cap)}); };
 for(const item of history) {
   if(!byName.has(item.strategy)) continue;
   const stamp = String(item.recorded_at || item.candle_end_ms || '');
   if(group !== stamp) {flush();group=stamp;timestamp=parseRecordedAt(stamp);if(!Number.isFinite(timestamp))timestamp=Number(item.candle_end_ms)||0;}
   const value = Number(item.capital_usd);
   if(Number.isFinite(value)) cap.set(item.strategy,value);
 }
 flush();
 if(snapshots.length === 0) snapshots.push({label:'Initial',t:0,capital:initial,values:new Map(cap)});
 // Include a last point from the current live report to avoid a misleading old total.
 const last = snapshots[snapshots.length-1];
 if(Math.abs(last.capital-latest)>0.0001) snapshots.push({label:'Dernier relevé',t:Date.parse(rawDate)||Date.now(),capital:latest,values:new Map(rows.map(r=>[r.strategy,r.capital_usd]))});
 // The new experiment starts exactly at $20 per robot, before any fees.
 // The first filled orders may immediately reduce liquidation value.
 if(DATA.model==='realistic_v2'){
   const launch=Date.parse(DATA.launched_at);
   if(Number.isFinite(launch))snapshots.unshift({label:'Capital initial',t:launch-1,
      capital:initial,values:new Map(rows.map(r=>[r.strategy,START]))});
 }
 return snapshots;
}
const series = reconstruct();
let range='1d', view='home', filter='all', sort='return', search='', sheetRobot=null, previouslyFocused=null;
const setText=(id,value)=>{const el=$(id);if(el)el.textContent=value};
const setTone=(node,value)=>{node.classList.remove('positive','negative','neutral','is-positive','is-negative');node.classList.add(polarity(value));};
const refreshedAt = new Date(rawDate);
const age = Date.now()-refreshedAt.getTime();
const recent=Number.isFinite(age)&&age>=-60000&&age<45*60*1000;
setText('status-text',recent?'Simulation récente':'Actualisation à vérifier');
if(!recent)$('live-status').classList.add('is-stale');
setText('page-subtitle','Dernier relevé · '+dateFR(rawDate)+' · Heure de Paris');
setText('footer-update','Mise à jour '+dateFR(rawDate));
setText('portfolio-value',rows.length?money(latest):'—');
setText('portfolio-profit',rows.length?signedMoney(profit):'—');
setText('portfolio-percent',rows.length?percentage(profit/initial*100):'—');
setTone($('portfolio-profit'),profit);
setTone($('portfolio-percent'),profit);
$('portfolio-profit').classList.add(polarity(profit)==='negative'?'is-negative':'is-positive');
$('portfolio-percent').classList.add(polarity(profit)==='negative'?'is-negative':'is-positive');
setText('stat-bots',rows.length.toString().padStart(2,'0'));
setText('stat-trades',totalTrades.toLocaleString('fr-FR'));

function toView(next,updateHash=true) {
 const titles={home:['PAPER TRADING · LABORATOIRE','Vue d’ensemble','Les résultats de votre expérience, au même endroit.'],robots:['LES STRATÉGIES','Vos robots','18 approches, une seule expérience.'],analysis:['LES STATISTIQUES','Analyse','Comprendre la performance, sans raccourcis.']};
 if(!titles[next])next='home';view=next;
 for(const item of ['home','robots','analysis']){const el=$('view-'+item);el.hidden=item!==next;el.classList.toggle('is-visible',item===next);}
 document.querySelectorAll('[data-view]').forEach(el=>{const active=el.dataset.view===next;el.classList.toggle('is-active',active);if(active)el.setAttribute('aria-current','page');else el.removeAttribute('aria-current');});
 setText('page-eyebrow',titles[next][0]);
 $('page-title').innerHTML='';$('page-title').append(document.createTextNode(titles[next][1]));const dot=document.createElement('span');dot.className='title-period';dot.textContent='.';$('page-title').append(dot);
 setText('page-subtitle',next==='home'?'Dernier relevé · '+dateFR(rawDate)+' · Heure de Paris':titles[next][2]);
 if(updateHash){historyApi.replaceState(null,'','#'+next);}
 window.scrollTo({top:0,behavior:'instant'});
 if(next==='home')renderMainChart();
}
const historyApi=window.history;
document.querySelectorAll('[data-view]').forEach(button=>button.addEventListener('click',()=>toView(button.dataset.view)));
$('open-all-robots').addEventListener('click',()=>toView('robots'));
window.addEventListener('hashchange',()=>toView(window.location.hash.substring(1)||'home',false));

function lineChart(host,points,{compact=false,tone=profit}={}) {
 host.replaceChildren();
 if(points.length<2){const no=document.createElement('div');no.className='chart-empty';no.textContent='La courbe apparaîtra après plusieurs relevés.';host.append(no);return;}
 const w=720,h=compact?158:180,pad={left:compact?4:2,right:compact?4:2,top:compact?13:12,bottom:compact?5:12};
 const vals=points.map(p=>p.v).filter(Number.isFinite);
 const low=Math.min(...vals),high=Math.max(...vals),margin=Math.max((high-low)*.25,0.015);
 const bottom=low-margin,top=high+margin;
 const x=i=>pad.left+(w-pad.left-pad.right)*i/(points.length-1);
 const y=v=>pad.top+(h-pad.top-pad.bottom)*(1-(v-bottom)/(top-bottom));
 const coords=points.map((p,i)=>[x(i),y(p.v)]);
 const path=coords.map((v,i)=>(i===0?'M':'L')+v[0].toFixed(2)+' '+v[1].toFixed(2)).join(' ');
 const fill=path+' L'+x(points.length-1)+' '+h+' L'+x(0)+' '+h+' Z';
 const color=tone>=0?'#baf477':'#ff8998';const grad='grad-'+Math.random().toString(36).slice(2,9);
 const ns='http://www.w3.org/2000/svg';const svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox',`0 0 ${w} ${h}`);svg.setAttribute('preserveAspectRatio','none');svg.setAttribute('aria-hidden','true');svg.classList.add('chart-svg-press');
 svg.innerHTML=`<defs><linearGradient id="${grad}" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="${color}" stop-opacity=".24"/><stop offset="100%" stop-color="${color}" stop-opacity="0"/></linearGradient></defs><path d="${fill}" fill="url(#${grad})"/><path d="${path}" stroke="${color}" stroke-width="2.7" stroke-linecap="round" stroke-linejoin="round" fill="none" vector-effect="non-scaling-stroke"/><circle cx="${coords.at(-1)[0]}" cy="${coords.at(-1)[1]}" r="4" fill="${color}" stroke="#172822" stroke-width="2"/>`;
 host.append(svg);
 if(compact)return;
 const tooltip=document.createElement('div');tooltip.className='chart-tooltip';tooltip.hidden=true;host.append(tooltip);
 const indicator=document.createElementNS(ns,'g');indicator.innerHTML='<line class="chart-scrub" y1="0" y2="'+h+'"/><circle class="chart-point" r="5" fill="'+color+'"/>';indicator.style.display='none';svg.append(indicator);
 const hover=e=>{const r=svg.getBoundingClientRect();if(!r.width)return;const pos=Math.min(1,Math.max(0,(e.clientX-r.left)/r.width));const ix=Math.min(points.length-1,Math.round(pos*(points.length-1)));const p=points[ix];const c=coords[ix];indicator.style.display='';indicator.querySelector('line').setAttribute('x1',c[0]);indicator.querySelector('line').setAttribute('x2',c[0]);indicator.querySelector('circle').setAttribute('cx',c[0]);indicator.querySelector('circle').setAttribute('cy',c[1]);tooltip.hidden=false;tooltip.textContent=money(p.v)+' · '+(p.label||'Relevé');tooltip.style.left=Math.max(90,Math.min(r.width-90,c[0]/w*r.width))+'px';};
 svg.addEventListener('pointermove',hover);svg.addEventListener('pointerdown',hover);svg.addEventListener('pointerleave',()=>{indicator.style.display='none';tooltip.hidden=true;});
}
function filterRange(points) { if(range==='all'||points.length<2)return points;const last=points.at(-1).t;if(!last)return points;const limit=range==='1d'?86400000:604800000;const filtered=points.filter(p=>p.t>=last-limit);return filtered.length>=2?filtered:points.slice(-2); }
function renderMainChart(){const points=filterRange(series).map(p=>({v:p.capital,label:p.label,t:p.t}));lineChart($('portfolio-chart'),points,{tone:profit});setText('chart-period',range==='1d'?'24 dernières heures':range==='7d'?'7 derniers jours':'Depuis le lancement');setText('chart-last',rows.length?'Dernier : '+money(latest):'—');}
document.querySelectorAll('[data-range]').forEach(button=>button.addEventListener('click',()=>{range=button.dataset.range;document.querySelectorAll('[data-range]').forEach(b=>b.classList.toggle('is-active',b===button));renderMainChart();}));

const compare=[...rows].sort((a,b)=>b.return_pct-a.return_pct);
function highlightCard({label,robot}) {
 const button=document.createElement('button');button.type='button';button.className='highlight-card';
 const a=document.createElement('span');a.className='highlight-meta';a.textContent=label;
 const n=document.createElement('span');n.className='highlight-name';n.textContent=nameFor(robot.strategy);
 const asset=document.createElement('span');asset.className='highlight-asset';asset.textContent=coinFor(robot.asset)+' · '+info(robot)[0];
 const value=document.createElement('span');value.className='highlight-value '+polarity(robot.return_pct);value.textContent=percentage(robot.return_pct);
 button.append(a,n,asset,value);button.addEventListener('click',()=>openSheet(robot));return button;
}
const highlights=$('highlights');
if(rows.length){const active=[...rows].sort((a,b)=>b.trades-a.trades)[0];highlights.append(highlightCard({label:'01 · MEILLEUR RENDEMENT',robot:compare[0]}),highlightCard({label:'02 · PLUS FAIBLE',robot:compare.at(-1)}),highlightCard({label:'03 · PLUS ACTIF',robot:active}));}
else highlights.textContent='En attente du premier relevé.';

function robotRow(r){const button=document.createElement('button');button.className='robot-row';button.type='button';button.setAttribute('aria-label',nameFor(r.strategy)+', rendement '+percentage(r.return_pct));
 const coin=coinFor(r.asset);const icon=document.createElement('span');icon.className='coin-icon '+coinClass(coin);icon.textContent=symbol(coin);
 const middle=document.createElement('span');middle.className='robot-row-middle';const title=document.createElement('span');title.className='robot-row-name';title.textContent=nameFor(r.strategy);const sub=document.createElement('span');sub.className='robot-row-sub';sub.textContent=coin+' · '+info(r)[0]+' · '+r.timeframe_min+' min';middle.append(title,sub);
 const right=document.createElement('span');right.className='robot-row-right';const cap=document.createElement('strong');cap.textContent=money(r.capital_usd);const percent=document.createElement('small');percent.className=polarity(r.return_pct);percent.textContent=percentage(r.return_pct);right.append(cap,percent);
 button.append(icon,middle,right);button.addEventListener('click',()=>openSheet(r));return button;}
function renderRobots(){const term=search.trim().toLocaleLowerCase('fr');let list=rows.filter(r=>{const ok=filter==='all'||filter==='positive'&&r.return_pct>0||filter==='negative'&&r.return_pct<0||filter==='inactive'&&r.trades===0;return ok&&(!term||(nameFor(r.strategy)+' '+info(r)[0]+' '+coinFor(r.asset)).toLowerCase().includes(term));});
 list=list.filter(r=>assetFilter==='all'||coinFor(r.asset)===assetFilter);
 if(sort==='return')list.sort((a,b)=>b.return_pct-a.return_pct);else if(sort==='activity')list.sort((a,b)=>b.trades-a.trades||b.return_pct-a.return_pct);else list.sort((a,b)=>nameFor(a.strategy).localeCompare(nameFor(b.strategy),'fr'));
 const box=$('robot-list');box.replaceChildren();setText('robots-count',list.length+' / '+rows.length+' stratégies');if(!list.length){const empty=document.createElement('div');empty.className='empty-list';empty.textContent='Aucun robot pour ce filtre.';box.append(empty);}else list.forEach(r=>box.append(robotRow(r)));}
$('robot-search').addEventListener('input',e=>{search=e.target.value;renderRobots();});$('robot-sort').addEventListener('change',e=>{sort=e.target.value;renderRobots();});document.querySelectorAll('[data-filter]').forEach(b=>b.addEventListener('click',()=>{filter=b.dataset.filter;document.querySelectorAll('[data-filter]').forEach(x=>x.classList.toggle('is-active',x===b));renderRobots();}));

function renderAnalysis(){const wins=rows.filter(r=>r.return_pct>0).length,losses=rows.filter(r=>r.return_pct<0).length,idle=rows.filter(r=>r.trades===0).length,fees=rows.reduce((s,r)=>s+r.fees_usd,0);
 setText('analysis-winners',wins+' / '+rows.length);setText('analysis-losers',losses+' / '+rows.length);setText('analysis-idle',idle+' / '+rows.length);setText('analysis-fees',money(fees,3));
 const groups=['BTC','ETH','SOL'].map(asset=>({asset,values:rows.filter(r=>coinFor(r.asset)===asset)})).filter(g=>g.values.length).map(g=>({...g,gain:g.values.reduce((s,r)=>s+r.capital_usd-START,0)}));const max=Math.max(.05,...groups.map(g=>Math.abs(g.gain)));
 const box=$('asset-breakdown');box.replaceChildren();groups.forEach(g=>{const item=document.createElement('div');const head=document.createElement('div');head.className='asset-item-head';const title=document.createElement('strong');title.textContent=g.asset+' · '+g.values.length+' robots';const value=document.createElement('span');value.className=polarity(g.gain);value.textContent=signedMoney(g.gain);head.append(title,value);const track=document.createElement('div');track.className='asset-track';const bar=document.createElement('div');bar.className='asset-bar'+(g.gain<0?' is-negative':'');bar.style.width=(Math.abs(g.gain)/max*47)+'%';bar.style.left=g.gain<0?(50-Math.abs(g.gain)/max*47)+'%':'50%';track.append(bar);item.append(head,track);box.append(item);});}

function openSheet(r){sheetRobot=r;previouslyFocused=document.activeElement;const coin=coinFor(r.asset),v=r.capital_usd-START;
 $('sheet-coin').className='coin-icon '+coinClass(coin);$('sheet-coin').textContent=symbol(coin);setText('sheet-name',nameFor(r.strategy));setText('sheet-category',info(r)[0]);setText('sheet-capital',money(r.capital_usd));setText('sheet-return',percentage(r.return_pct));$('sheet-return').className=polarity(r.return_pct);setText('sheet-asset',coin);setText('sheet-timeframe',r.timeframe_min+' min');setText('sheet-trades',r.trades.toLocaleString('fr-FR'));setText('sheet-fees',money(r.fees_usd,3));setText('sheet-description',info(r)[1]);renderSheetExtras(r);
 const points=series.map(s=>({v:s.values.get(r.strategy)??START,t:s.t,label:s.label}));lineChart($('sheet-chart'),points,{compact:true,tone:v});$('robot-sheet').hidden=false;document.body.style.overflow='hidden';$('close-sheet').focus();}
function closeSheet(){$('robot-sheet').hidden=true;document.body.style.overflow='';sheetRobot=null;if(previouslyFocused&&previouslyFocused.focus)previouslyFocused.focus();}
$('close-sheet').addEventListener('click',closeSheet);$('sheet-backdrop').addEventListener('click',closeSheet);document.addEventListener('keydown',e=>{if(e.key==='Escape'&&sheetRobot)closeSheet();if(e.key==='Tab'&&sheetRobot){const targets=[$('close-sheet')];if(!targets.includes(document.activeElement)){$('close-sheet').focus();e.preventDefault();}}});
/* Seiko Trading Lab — provenance, research diagnostics, and accessible exports. */
const labEpoch=Date.parse(DATA.launched_at||'2026-10-28T06:36:00Z');
const msDay=86400000;
const labClock=()=>Math.max(0,Date.now()-labEpoch);
const labDate=ms=>new Intl.DateTimeFormat('fr-FR',{timeZone:'Europe/Paris',day:'numeric',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit'}).format(new Date(ms));
const labShortDate=ms=>new Intl.DateTimeFormat('fr-FR',{timeZone:'Europe/Paris',day:'numeric',month:'short',year:'numeric'}).format(new Date(ms));
const labDuration=ms=>{const d=Math.floor(ms/msDay),h=Math.floor(ms%msDay/3600000),m=Math.floor(ms%3600000/60000);return d?d+' j '+h+' h':h?h+' h '+m+' min':m+' min';};
function renderLabTimeline(){
 if(!Number.isFinite(labEpoch))return;
 const elapsed=labClock(),day=Math.floor(elapsed/msDay),progress=Math.min(100,Math.max(0,elapsed/(7*msDay)*100));
 setText('lab-start',labDate(labEpoch));setText('lab-duration',labDuration(elapsed));setText('lab-day','J+'+day);
 setText('lab-progress-label',day>=7?'J+7 atteint':Math.floor(progress)+' %');
 $('lab-progress-fill').style.width=progress.toFixed(2)+'%';$('lab-progress').setAttribute('aria-valuenow',Math.round(progress));
 setText('lab-review','Bilan '+labShortDate(labEpoch+7*msDay));
 setText('review-one',labShortDate(labEpoch+7*msDay));setText('review-two',labShortDate(labEpoch+14*msDay));
}
// These values are observed on recorded portfolio snapshots, not intra-candle extremes.
function observedDrawdown(values){let peak=-Infinity,worst=0;for(const n of values){if(!Number.isFinite(n)||n<=0)continue;peak=Math.max(peak,n);if(peak>0)worst=Math.max(worst,(peak-n)/peak*100);}return worst;}
function researchInsights(){
 const totals=[initial,...series.map(s=>s.capital),latest];
 const dd=observedDrawdown(totals);
 const n=history.length?new Set(history.map(x=>String(x.recorded_at))).size:0;
 setText('insight-samples',n.toLocaleString('fr-FR')+' relevés');
 setText('insight-drawdown',dd.toLocaleString('fr-FR',{maximumFractionDigits:2,minimumFractionDigits:2})+' %');
 setText('insight-activity',rows.filter(r=>r.trades>0).length+' / '+rows.length);
 const ranked=[...rows].sort((a,b)=>b.return_pct-a.return_pct);
 if(ranked.length){setText('insight-best',percentage(ranked[0].return_pct));setText('insight-best-name',nameFor(ranked[0].strategy));setText('insight-worst',percentage(ranked.at(-1).return_pct));setText('insight-worst-name',nameFor(ranked.at(-1).strategy));}
 const grid=$('benchmark-grid');grid.replaceChildren();
 ['BTC','ETH','SOL'].forEach(asset=>{
  const group=rows.filter(r=>coinFor(r.asset)===asset),hold=group.find(r=>r.strategy===asset.toLowerCase()+'_hold'),active=group.filter(r=>r!==hold);
  if(!hold||!active.length)return;
  const mean=active.reduce((sum,r)=>sum+r.return_pct,0)/active.length,diff=mean-hold.return_pct;
  const tile=document.createElement('article');tile.className='benchmark-item';
  const head=document.createElement('div');head.className='benchmark-head';const label=document.createElement('strong');label.textContent=symbol(asset)+' '+asset;const count=document.createElement('small');count.textContent=active.length+' stratégies comparées';head.append(label,count);
  const pair=document.createElement('div');pair.className='benchmark-pair';
  for(const [title,value] of [['Robot Hold',hold.return_pct],['Moyenne des autres robots',mean]]){const col=document.createElement('div'),sm=document.createElement('small'),strong=document.createElement('strong');sm.textContent=title;strong.textContent=percentage(value);strong.className=polarity(value);col.append(sm,strong);pair.append(col);}
  const foot=document.createElement('div');foot.className='benchmark-delta';foot.textContent=(diff>=0?'+':'')+diff.toLocaleString('fr-FR',{minimumFractionDigits:2,maximumFractionDigits:2})+' point(s) de rendement pour les stratégies actives';
  tile.append(head,pair,foot);grid.append(tile);
 });
}
function renderSheetExtras(r){
 const numbers=[START,...series.map(s=>s.values.get(r.strategy)).filter(Number.isFinite),r.capital_usd];
 const dd=observedDrawdown(numbers);
 setText('sheet-drawdown',dd.toLocaleString('fr-FR',{minimumFractionDigits:2,maximumFractionDigits:2})+' %');
 const asset=coinFor(r.asset),hold=rows.find(x=>x.strategy===asset.toLowerCase()+'_hold');
 if(r===hold){setText('sheet-benchmark','Référence');setText('sheet-benchmark-note','Ce robot sert de comparaison « acheter et conserver » pour '+asset+'.');}
 else if(hold){const diff=r.return_pct-hold.return_pct;setText('sheet-benchmark',(diff>0?'+':'')+diff.toLocaleString('fr-FR',{minimumFractionDigits:2,maximumFractionDigits:2})+' pt');setText('sheet-benchmark-note','Écart de rendement avec '+asset+' Hold, sans équivalence de risque.');}
 else{setText('sheet-benchmark','—');setText('sheet-benchmark-note','Pas de robot Hold de référence pour cet actif.');}
}

// Signals are measured in USD; convert only explicitly labelled price values.
function displaySignalReason(reason){
 const text=String(reason||'Motif non enregistré');
 return displayCurrency === 'EUR'
   ? text.replace(/\b(close|moy20)=([0-9]+(?:\.[0-9]+)?)/g,
       (_,name,value)=>name+'='+money(Number(value),4))
   : text;
}
// Human-readable paper execution log. Source: recorded quotes and decisions,
// never reconstructed or invented transactions.
let showAllEvents=false;
function renderTradeJournal(){
 const container=$('trade-journal-list'),toggle=$('trade-journal-toggle');
 if(!container)return;
 const events=Array.isArray(DATA.orders)?[...DATA.orders].reverse():[];
 container.replaceChildren();
 if(!events.length){
   const empty=document.createElement('p');empty.className='micro-note';
   empty.textContent='Aucune opération ou tentative enregistrée pour cette expérience.';
   container.append(empty);toggle.hidden=true;return;
 }
 const visible=showAllEvents?events:events.slice(0,8);
 toggle.hidden=events.length<=8;
 toggle.textContent=showAllEvents?'Réduire la liste':'Afficher les '+events.length+' événements';
 for(const e of visible){
   const card=document.createElement('article');card.className='trade-event';
   const head=document.createElement('div');head.className='trade-event-head';
   const label=document.createElement('strong');label.textContent=nameFor(e.strategy);
   const status=document.createElement('span');
   const filled=e.status==='FILLED_SIMULATED';
   status.className=filled?'trade-status is-filled':'trade-status is-rejected';
   const action=e.side==='BUY'?'Achat':'Vente';
   status.textContent=filled?action+' simulé':action+' refusé';
   head.append(label,status);
   const when=document.createElement('small');when.className='trade-when';
   when.textContent=dateFR(e.observed_at)+' · '+(e.asset||'').replace('USDT','/USD').replace(/([A-Z]{3})USD$/,'$1/USD');
   card.append(head,when);
   const details=document.createElement('div');details.className='trade-event-metrics';
   if(filled){
      const price=document.createElement('span');price.textContent='Prix estimé '+money(Number(e.executed_price),4);
      const qty=document.createElement('span');qty.textContent='Quantité '+String(e.quantity);
      const fees=document.createElement('span');fees.textContent='Frais '+money(Number(e.fee_usd),4);
      details.append(price,qty,fees);
   }else{
      const reason=document.createElement('span');reason.textContent='Motif du refus : '+String(e.status).replaceAll('_',' ').toLowerCase();details.append(reason);
   }
   card.append(details);
   const explain=document.createElement('details');explain.className='trade-explanation';
   const summary=document.createElement('summary');summary.textContent='Pourquoi cette décision ?';
   const body=document.createElement('p');body.textContent=displaySignalReason(e.reason);
   explain.append(summary,body);card.append(explain);
   container.append(card);
 }
}
const journalToggle=$('trade-journal-toggle');
if(journalToggle)journalToggle.addEventListener('click',()=>{showAllEvents=!showAllEvents;renderTradeJournal();});
if(DATA.model==='realistic_v2'){
 const note=document.querySelector('.notice p');
 if(note)note.textContent='Simulation conservatrice : carnet d’ordres Kraken, frais taker 0,80 %, glissement supplémentaire estimé 0,05 % par opération. Aucun ordre réel.';
 const method=document.querySelectorAll('.method-list > div p');
 if(method[1])method[1].textContent='Frais et exécution : ordres simulés sur le carnet Kraken, 0,80 % de frais taker et 0,05 % de glissement supplémentaire estimé.';
 if(method[2])method[2].textContent='Limites : les cotations sont observées puis simulées, et non garanties comme un ordre réellement exécuté. Les minimums de marché sont vérifiés.';
 // The display currency badge is managed centrally when toggling.
}

let assetFilter='all';
document.querySelectorAll('[data-coin]').forEach(button=>button.addEventListener('click',()=>{assetFilter=button.dataset.coin;document.querySelectorAll('[data-coin]').forEach(x=>x.classList.toggle('is-active',x===button));renderRobots();}));
function refreshCurrency(){
 setText('portfolio-value',rows.length ? money(latest) : '—');
 setText('portfolio-profit',rows.length ? signedMoney(profit) : '—');
 const tag=document.querySelector('.hero-small-tag');
 if(tag)tag.textContent=displayCurrency+' · '+(DATA.model==='realistic_v2' ? 'MODÈLE PRUDENT V2' : 'SIMULATION');
 const fxNote=$('fx-note');
 if(fxNote)fxNote.textContent=fxAvailable
  ? 'BCE · taux du '+new Intl.DateTimeFormat('fr-FR',{timeZone:'UTC',day:'2-digit',month:'2-digit',year:'numeric'}).format(new Date(fxDate))+
    ' · 1 € = '+usdPerEur.toLocaleString('fr-FR',{minimumFractionDigits:4,maximumFractionDigits:4})+
    ' $ · conversion indicative uniquement'
  : 'Taux BCE indisponible ou trop ancien : affichage en USD uniquement.';
 document.querySelectorAll('[data-currency]').forEach(button=>{
   const active=button.dataset.currency===displayCurrency;
   button.classList.toggle('is-active',active);
   button.setAttribute('aria-pressed',String(active));
   if(button.dataset.currency==='EUR'){
     button.disabled=!fxAvailable;
     button.title=fxAvailable?'Afficher les équivalents en euros':'Taux BCE indisponible';
   }
 });
 renderMainChart();renderRobots();renderAnalysis();renderTradeJournal();
 if(sheetRobot){
   setText('sheet-capital',money(sheetRobot.capital_usd));
   setText('sheet-fees',money(sheetRobot.fees_usd,3));
   lineChart($('sheet-chart'),series.map(p=>({
      v:p.values.get(sheetRobot.strategy)??START,t:p.t,label:p.label
   })),{compact:true,tone:sheetRobot.capital_usd-START});
 }
}
document.querySelectorAll('[data-currency]').forEach(button=>button.addEventListener('click',()=>{
 const next=button.dataset.currency;
 if(next==='EUR'&&!fxAvailable)return;
 if(next!=='USD'&&next!=='EUR')return;
 displayCurrency=next;
 try { localStorage.setItem('seiko-trading-display-currency',next); } catch (_) {}
 refreshCurrency();
}));
renderLabTimeline();researchInsights();
refreshCurrency();toView(window.location.hash.substring(1)||'home',false);
})();