/* Lab / 05 — source-grounded clarity & radar. No trading actions, no navigation changes. */
(function(){
'use strict';
const $=id=>document.getElementById(id);
const D=window.DATA||(typeof DATA==='object'?DATA:{});
const put=(id,value)=>{const el=$(id);if(el)el.textContent=String(value)};
const date=t=>{const n=Date.parse(t||'');return Number.isFinite(n)?
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
function updateHoldings(){
 if(!panel||panel.hidden||!name)return;
 const L=window.SeikoV4;if(!L)return;
 const norm=t=>String(t||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'')
  .replace(/[^a-z0-9]+/g,'_').replace(/^_|_$/g,'');
 const key=norm(name.textContent);
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
  put('whale-radar-follow-status',follow.state==='observing'||follow.state==='partial'?
    active.length+' adresse(s) observée(s) séparément sur une page de transferts récents · '+
    date(follow.generated_at)+
    (follow.error_count?' · '+follow.error_count+' erreur(s) de collecte':'')+
    '. Premier relevé = référence, jamais nouvelle alerte.':
    'Suivi d’adresses '+(follow.state||'non disponible')+
    ' ; aucune transaction ou identité supposée.');
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