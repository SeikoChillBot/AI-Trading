/* AIT / 07: explain observed paper decisions, never create or execute orders. */
(function(){
'use strict';
const D=(typeof DATA==='object'&&DATA)||{};
const $=id=>document.getElementById(id);
const fmt=(v,max=2)=>{const n=Number(v);return Number.isFinite(n)?
 n.toLocaleString('fr-FR',{maximumFractionDigits:max}):'—';};
const stamp=t=>{const d=Date.parse(t||'');return Number.isFinite(d)?
 new Intl.DateTimeFormat('fr-FR',{timeZone:'Europe/Paris',day:'2-digit',
 month:'short',hour:'2-digit',minute:'2-digit'}).format(new Date(d)):'date indisponible';};
const put=(id,text)=>{const el=$(id);if(el)el.textContent=String(text);};
const review=D.ai_review||{},evolution=D.robot_evolution||{};
const status=D.research?.ai_status||{};
const modelAnswered=review.state==='model_reflection_completed'&&
 review.source==='gemini_generate_content'&&
 status.state==='model_reflection_completed';
const checks=evolution.counts||{};
const tests=Number(checks.testing||0),approved=Number(checks.activated||0);
const proposed=modelAnswered&&Array.isArray(review.experiments)?
 review.experiments.length:0;
put('ait-proof-state',tests+' variante(s) de stratégie en cours de comparaison, '+
 approved+' changement(s) validé(s). Les robots témoins restent inchangés.');
const proof=$('ait-gemini-proof');
if(proof){
 proof.replaceChildren();
 const tile=(name,value,explanation)=>{
  const card=document.createElement('div');card.className='ait-proof-cell';
  const small=document.createElement('small');small.textContent=name;
  const big=document.createElement('strong');big.textContent=value;
  const desc=document.createElement('p');desc.textContent=explanation;
  card.append(small,big,desc);proof.append(card);
 };
 tile('Propositions IA',modelAnswered?fmt(proposed,0)+' expérience(s)':'Non confirmées',
  modelAnswered?'Dernière réponse vérifiée : '+stamp(status.model_last_called_at)+
    '. Une proposition reste une hypothèse.':
    'Aucune réponse Gemini récente et authentifiée dans ce relevé.');
 tile('Tests en cours',evolution.ready?fmt(tests,0):'En attente',
  'Variantes comparées sur de nouvelles observations. Certaines viennent de calculs statistiques, pas de Gemini.');
 tile('Changements approuvés',evolution.ready?fmt(approved,0):'En attente',
  'Un changement n’est retenu qu’après des résultats futurs suffisants et des contrôles de risque.');
}
const sheet=$('robot-sheet'),title=$('sheet-name');
const actions=$('ait-sheet-activity-list');
const labels={BUY:'Achat fictif',SELL:'Vente fictive'};
function statusLabel(e){
 const status=String(e.status||'').toUpperCase();
 if(status==='FILLED_SIMULATED'||status==='SIMULATED_FILL')return 'opération simulée enregistrée';
 if(status.includes('REJECT')||status.includes('BLOCK'))return 'opération refusée : aucun achat/vente effectué';
 if(status.includes('SKIP')||status.includes('WAIT'))return 'condition non réunie : aucune opération';
 return 'statut : '+(e.status||'non précisé');
}
function reasonLabel(row){
 const reason=String(row.reason||'');
 if(/conservation|hold/i.test(reason))return 'Le robot suit la règle « conserver ».';
 if(/seuil|threshold/i.test(reason))return 'Le prix a franchi un seuil utilisé par sa stratégie.';
 if(/signal=buy/i.test(reason))return 'Les conditions d’achat de sa stratégie étaient réunies.';
 if(/signal=sell/i.test(reason))return 'Les conditions de vente de sa stratégie étaient réunies.';
 if(/non ex.cut|estimated|estim.e/i.test(reason))return 'Prix et coûts estimés : aucune transaction réelle.';
 return 'La règle automatique du robot a produit cette décision. Les détails techniques restent dans les données de simulation.';
}
function renderActivity(){
 if(!sheet||sheet.hidden||!title||!actions)return;
 const strategy=title.dataset.strategy;
 const multi=String($('sheet-category')?.textContent||'').toLowerCase().includes('multi');
 const data=multi?D.multi_asset:D;
 const rows=(Array.isArray(data?.orders)?data.orders:[])
  .filter(e=>e&&e.strategy===strategy)
  .sort((a,b)=>Date.parse(b.observed_at||'')-Date.parse(a.observed_at||''));
 const bot=(multi?D.multi_asset?.rows:D.rows||[])?.find(r=>r.strategy===strategy);
 actions.replaceChildren();
 const units=Number(bot?.units),cash=Number(bot?.cash_usd);
 const position=Number.isFinite(units)?(units>0?
    'Ce robot détient une quantité d’actif dans sa simulation.':
    'Ce robot ne détient aucun actif actuellement.'):'Quantité détenue non publiée.';
 const avail=Number.isFinite(cash)?' Argent non investi : '+fmt(cash,2)+' $ fictifs.':'';
 put('ait-sheet-activity-status',position+avail+
  ' Voici seulement les dernières décisions conservées dans la publication.');
 if(!rows.length){
  const note=document.createElement('p');
  note.className='micro-note';
  note.textContent=Number(bot?.trades||0)>0?
   'Ce robot a déjà effectué des opérations, mais aucune ne figure dans les derniers événements publiés. Son capital et ses quantités sont toujours affichés au-dessus.':
   'Aucune opération enregistrée pour ce robot. Il peut attendre un signal, des prix valides ou l’ouverture du marché.';
  actions.append(note);return;
 }
 for(const row of rows.slice(0,3)){
  const item=document.createElement('article');item.className='ait-activity-item';
  const name=document.createElement('strong');
  name.textContent=(labels[String(row.side||'').toUpperCase()]||'Décision enregistrée')+
    ' · '+stamp(row.observed_at);
  const state=document.createElement('p');
  state.textContent=statusLabel(row)+'. '+reasonLabel(row);
  const details=document.createElement('small');
  const amount=Number(row.gross_usd),fees=Number(row.fee_usd);
  details.textContent=(Number.isFinite(amount)&&amount>0?
     'Montant de l’opération : '+fmt(amount,2)+' $ fictifs. ':'')+
     (Number.isFinite(fees)&&fees>0?
     'Frais estimés : '+fmt(fees,3)+' $.':'');
  item.append(name,state,details);actions.append(item);
 }
}
if(sheet&&title&&actions){
 const watch=new MutationObserver(renderActivity);
 watch.observe(sheet,{attributes:true,attributeFilter:['hidden']});
 watch.observe(title,{attributes:true,attributeFilter:['data-strategy'],
                        childList:true,characterData:true,subtree:true});
 renderActivity();
}
})();