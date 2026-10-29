/* Lab / 05 — source-grounded clarity & radar. No trading actions, no navigation changes. */
(function(){
'use strict';
const $=id=>document.getElementById(id);
const D=window.DATA||(typeof DATA==='object'?DATA:{});
const put=(id,value)=>{const el=$(id);if(el)el.textContent=String(value)};
const date=t=>{const n=typeof t==='number'?t:Date.parse(t||'');return Number.isFinite(n)?
 new Intl.DateTimeFormat('fr-FR',{timeZone:'Europe/Paris',day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'}).format(new Date(n)):'date inconnue'};
const format=(v,max=2)=>{const n=Number(v);return Number.isFinite(n)?
 n.toLocaleString('fr-FR',{minimumFractionDigits:0,maximumFractionDigits:max}):'—'};
const money=v=>window.SeikoV4?.money?.(v)??(format(v,2)+' $');
function freshness(){
 const a=Date.parse(D.updated||''),b=Date.parse(D.multi_asset?.updated_at||'');
 const now=Date.now(),validA=Number.isFinite(a),validB=Number.isFinite(b);
 const stale=!(validA&&validB)||now-a>30*60000||now-b>45*60000||a>now+60000||b>now+60000;
 put('lab-freshness-badge',stale?'À vérifier':'Récent');
 const badge=$('lab-freshness-badge');if(badge)badge.classList.toggle('is-stale',stale);
 put('lab-freshness-detail','Crypto : '+date(D.updated)+' · Multi-actifs : '+date(D.multi_asset?.updated_at)+
  (stale?' · Au moins un relevé est absent ou trop ancien.':' · Derniers relevés intégrés à cette page.')+
  ' Cette page est une publication statique, pas un flux boursier en direct.');
}
freshness();document.addEventListener('visibilitychange',()=>{if(!document.hidden)freshness()});setInterval(freshness,60000);
const refresh=$('lab-refresh');
if(refresh)refresh.addEventListener('click',()=>{
 const url=new URL(window.location.href);
 url.searchParams.set('r',String(Date.now()));
 window.location.assign(url.href);
});
const ai=D.research?.ai_status||{};
const state=ai.state;
const reason=ai.last_http_status?'HTTP '+ai.last_http_status:
 ai.error_type||'cause non enregistrée';
put('lab-gemini-diagnostic',state==='model_reflection_completed'?
 'Réponse Gemini vérifiée · dernier appel '+date(ai.model_last_called_at||ai.last_attempt_at)+'.':
 state==='model_reflection_failed'?
 'Gemini indisponible : '+reason+(ai.error_code?' · '+ai.error_code:'')+
 ' · '+(ai.used_cache?'dernier échec conservé':'tentative API effectuée')+
 ' · '+format(ai.attempts_in_slot,0)+' tentative(s) ce créneau. Les calculs statistiques continuent.':
 'Réponse Gemini non confirmée : '+(state||'statut absent')+' · calculs statistiques indépendants.');
// Show portfolio composition for both legacy crypto highlights and unified directory sheets.
const panel=$('robot-sheet'),name=$('sheet-name');
let selectedPeriod='all';
function drawIndividualChart(r,multi,history){
 const box=$('sheet-chart');if(!box)return;
 const launch=Date.parse(multi?D.multi_asset?.started_at:D.launched_at);
 const update=Date.parse(multi?D.multi_asset?.updated_at:D.updated);
 const original=(history||[]).filter(x=>x.strategy===r.strategy).map(x=>({
   t:Date.parse(x.recorded_at||''),v:Number(x.capital_usd)}))
   .filter(p=>Number.isFinite(p.t)&&Number.isFinite(p.v)&&p.v>=0)
   .sort((a,b)=>a.t-b.t);
 const points=[...original];
 if(Number.isFinite(launch)&&(!points.length||launch<points[0].t))
  points.unshift({t:launch,v:Number(r.initial_usd||20)});
 if(Number.isFinite(update)&&(!points.length||update>points[points.length-1].t))
  points.push({t:update,v:Number(r.capital_usd)});
 const maxT=points.length?points[points.length-1].t:Date.now();
 const delay=selectedPeriod==='1d'?86400000:selectedPeriod==='7d'?604800000:Infinity;
 const selected=points.filter(p=>p.t>=maxT-delay);
 const selectedRows=original.filter(p=>p.t>=maxT-delay);
 box.replaceChildren();
 document.querySelectorAll('[data-sheet-range]').forEach(button=>{
  const active=button.dataset.sheetRange===selectedPeriod;
  button.classList.toggle('is-active',active);
  button.setAttribute('aria-pressed',String(active));
 });
 if(selected.length<2){
  const p=document.createElement('p');p.className='micro-note';
  p.textContent='Pas encore assez de relevés dans cette période pour tracer une courbe fiable.';
  box.append(p);put('sheet-chart-stats','Données insuffisantes sur cette période.');return;
 }
 const low=Math.min(...selected.map(p=>p.v)),high=Math.max(...selected.map(p=>p.v));
 const pad=Math.max((high-low)*.18,Number(r.initial_usd||20)*.003);
 const min=low-pad,max=high+pad,w=520,h=175;
 const xy=selected.map(p=>({
  x:14+(p.t-selected[0].t)/Math.max(1,maxT-selected[0].t)*(w-28),
  y:10+(max-p.v)/(max-min)*(h-30)}));
 // The last sample is the actual last observation, not an invented projection.
 const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
 svg.setAttribute('viewBox','0 0 '+w+' '+h);
 svg.setAttribute('role','img');
 svg.setAttribute('aria-label','Capital estimé de '+r.strategy+' de '+date(selected[0].t)+' à '+date(selected[selected.length-1].t));
 svg.style.width='100%';svg.style.height='100%';
 const ns='http://www.w3.org/2000/svg';
 for(const y of [18,85,152]){
  const line=document.createElementNS(ns,'line');
  line.setAttribute('x1',14);line.setAttribute('x2',w-14);
  line.setAttribute('y1',y);line.setAttribute('y2',y);
  line.setAttribute('stroke','#35504e');line.setAttribute('stroke-width','1');
  svg.append(line);
 }
 const path=document.createElementNS(ns,'path');
 path.setAttribute('d',xy.map((p,i)=>(i?'L':'M')+p.x.toFixed(2)+' '+p.y.toFixed(2)).join(' '));
 path.setAttribute('fill','none');
 path.setAttribute('stroke',selected.at(-1).v>=selected[0].v?'#b9f477':'#ff8497');
 path.setAttribute('stroke-width','3');
 path.setAttribute('stroke-linecap','round');path.setAttribute('stroke-linejoin','round');
 svg.append(path);
 const dot=document.createElementNS(ns,'circle');
 dot.setAttribute('cx',xy.at(-1).x);dot.setAttribute('cy',xy.at(-1).y);
 dot.setAttribute('r','4');dot.setAttribute('fill',path.getAttribute('stroke'));
 svg.append(dot);box.append(svg);
 put('sheet-chart-stats','Minimum '+money(low)+' · maximum '+money(high)+
  ' · '+selectedRows.length+' relevé(s) horodaté(s) · '+date(selected[0].t)+' → '+
  date(selected.at(-1).t)+'.');
}
for(const button of document.querySelectorAll('[data-sheet-range]')){
 button.addEventListener('click',()=>{selectedPeriod=button.dataset.sheetRange;updateHoldings()});
}
function updateHoldings(){
 if(!panel||panel.hidden||!name)return;
 const L=window.SeikoV4;if(!L)return;
 const norm=t=>String(t||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'')
  .replace(/[^a-z0-9]+/g,'_').replace(/^_|_$/g,'');
 const key=name.dataset.strategy||norm(name.textContent);
 const category=String($('sheet-category')?.textContent||'').toLowerCase();
 const rows=category.includes('multi')?L.mr:L.cr;
 let r=rows.find(x=>x.strategy===key);
 if(!r&&category.includes('multi')){
  const asset=String($('sheet-asset')?.textContent||'').toLowerCase();
  const isHold=/conservation|hold/i.test(name.textContent||'');
  r=rows.find(x=>x.strategy===asset+(isHold?'_hold':'_trend20'));
 }
 if(!r){put('sheet-initial','20 $ fictifs');put('sheet-cash','—');put('sheet-units','—');put('sheet-position','Non identifié');return}
 put('sheet-initial',money(Number(r.initial_usd||20)));
 put('sheet-cash',Number.isFinite(Number(r.cash_usd))?money(r.cash_usd):'Donnée absente');
 const n=Number(r.units);
 put('sheet-units',Number.isFinite(n)?format(n,8)+' '+String(r.asset||'').replace(/USD$/,''):'Donnée absente');
 put('sheet-position',Number.isFinite(n)?n>0?'Actif détenu (simulation)':'Liquidités uniquement':'Non déterminée');
 const history=category.includes('multi')?L.m.history:L.D.history;
 drawIndividualChart(r,category.includes('multi'),history);
 const records=(history||[]).filter(x=>x.strategy===r.strategy&&Number.isFinite(Date.parse(x.recorded_at||'')));
 const first=records[0]?.recorded_at,last=records[records.length-1]?.recorded_at;
 put('sheet-chart-context',records.length?records.length+' relevés · '+date(first)+' → '+date(last)+
  ' · capital estimé après coûts, non prix d’achat garanti.':
  'Aucune série horodatée complète encore disponible pour ce robot.');
}
if(panel&&name){
 const watch=new MutationObserver(updateHoldings);
 watch.observe(panel,{attributes:true,attributeFilter:['hidden']});
 watch.observe(name,{childList:true,characterData:true,subtree:true});
 updateHoldings();
}
const radar=D.whale_radar||{},host=$('whale-radar-highlights'),wallets=$('whale-radar-addresses');
if(host&&wallets){
 host.replaceChildren();wallets.replaceChildren();
 const n=Number(radar.large_transfers_observed||0),count=Number(radar.sampled_wallets_count||0);
 put('whale-radar-count',radar.ready?format(n,0):'—');
 put('whale-radar-wallets',radar.ready?format(count,0):'—');
 put('whale-radar-new',radar.ready?format(radar.new_event_count||0,0):'—');
 const sampled=Object.values(radar.sampled_records||{}).reduce((a,v)=>a+Number(v||0),0);
 put('whale-radar-status',radar.ready?'Échantillon de '+format(sampled,0)+' transferts publics · '+date(radar.generated_at)+
  (radar.state==='partial'?' · collecte partielle':' · collecte disponible')+
  '. Les adresses listées sont des pseudonymes publics non attribués.':
  'Radar indisponible ('+(radar.state||'non publié')+'). Aucun mouvement déduit.');
 const tile=(target,title,desc,link,linkLabel)=>{
  const box=document.createElement('article');box.className='research-idea radar-card';
  const h=document.createElement('strong');h.textContent=title;
  const p=document.createElement('p');p.textContent=desc;box.append(h,p);
  if(link){const a=document.createElement('a');a.href=link;a.rel='noopener noreferrer';a.target='_blank';
   a.textContent=linkLabel;box.append(a)}target.append(box);
 };
 const txOk=h=>/^0x[0-9a-f]{64}$/.test(h||'');
 const addressOk=a=>/^0x[0-9a-f]{40}$/.test(a||'');
 for(const e of (radar.sample_highlights||[]).slice(0,6)){
  const hash=String(e.tx_hash||'').toLowerCase();
  tile(host,String(e.token||'Stablecoin')+' · '+format(e.nominal_usd_approx,0)+' unités nominales',
   date(e.timestamp)+' · Transfert ERC-20 constaté ; ni achat ni vente vérifié.',
   txOk(hash)?'https://eth.blockscout.com/tx/'+hash:null,'Voir la transaction publique');
 }
 if(!host.children.length)tile(host,'Aucun gros transfert confirmé dans l’échantillon',
  'Les données sont absentes ou aucun transfert ne franchit le seuil nominal de 1 million.');
 for(const flow of (radar.sampled_wallet_flows||[]).slice(0,10)){
  const address=String(flow.address||'').toLowerCase();
  if(!addressOk(address))continue;
  tile(wallets,address.slice(0,8)+'…'+address.slice(-6)+' · '+format(flow.sample_observations,0)+' transferts',
   'Entrées échantillonnées : '+format(flow.incoming_nominal_usd,0)+
   ' · sorties : '+format(flow.outgoing_nominal_usd,0)+
   ' · solde directionnel dans cet échantillon : '+format(flow.sample_net_nominal_usd,0)+
   '. Ni solde du wallet ni identité vérifiée.',
   'https://eth.blockscout.com/address/'+address,'Consulter l’adresse sur Blockscout');
 }
 if(!wallets.children.length)tile(wallets,'Aucune adresse exploitable','Identités non vérifiées. Aucun wallet attribué à une baleine.');
 const follow=radar.follow||{},followBox=$('whale-radar-follow-list');
 if(followBox){
  followBox.replaceChildren();
  const active=Array.isArray(follow.tracked_addresses)?follow.tracked_addresses:[];
  const events=Array.isArray(follow.new_transfers)?follow.new_transfers:[];
  const followReadable=(follow.state==='observing'||follow.state==='partial')?
   active.length+' adresse(s) suivie(s). Sans nouvelle grosse transaction, elles restent surveillées.':
   follow.state==='no_addresses_yet'?'Aucune nouvelle adresse repérée : le radar continue.':
   follow.state==='unavailable'?'Source indisponible : les adresses déjà enregistrées sont conservées.':
   'Premiers relevés en attente.';
  put('whale-radar-follow-status',followReadable);
  /* previous display intentionally superseded */
  for(const entry of active.slice(0,4)){
   const a=String(entry.address||'').toLowerCase();if(!addressOk(a))continue;
   tile(followBox,a.slice(0,8)+'…'+a.slice(-6),
     format(entry.sample_count,0)+' transferts USDC/USDT validés dans la page examinée · '+
     format(entry.new_count,0)+' nouveau(x) depuis la première observation de cette adresse.',
     'https://eth.blockscout.com/address/'+a,'Ouvrir l’historique public');
  }
  for(const e of events.slice(0,5)){
   const h=String(e.tx_hash||'').toLowerCase();if(!txOk(h))continue;
   tile(followBox,'Nouveau transfert observé · '+String(e.token||'ERC-20'),
    date(e.timestamp)+' · '+format(e.nominal_usd_approx,0)+
    ' unités nominales ; ni achat ni propriétaire vérifié.',
    'https://eth.blockscout.com/tx/'+h,'Voir la transaction');
  }
  if(!followBox.children.length)tile(followBox,'Suivi non confirmé','Les adresses seront affichées seulement après une collecte valide.');
 }
}
})();