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
// Make the distinction between what Gemini says and what the data support explicit.
const eth=Array.isArray(review.historical?.assets)?
 review.historical.assets.find(x=>x.asset==='ETHUSD'):null;
const ethReturn=Number(eth?.avg_net_return_pct),ethDrop=Number(eth?.worst_drawdown_pct);
put('ait-gemini-nuance',modelAnswered&&eth&&
 Number.isFinite(ethReturn)&&Number.isFinite(ethDrop)?
 'Contrôle des chiffres : les anciens essais sur ETH affichent une moyenne de '+
 (ethReturn>0?'+':'')+fmt(ethReturn,2)+' %, mais aussi une baisse maximale de '+
 fmt(ethDrop,2)+' %. Ce résultat historique n’est pas une performance garantie.' :
 'Les observations passées ne prouvent pas qu’une stratégie sera rentable demain.');
const ideaBox=$('ait-gemini-ideas');
if(ideaBox){
 ideaBox.replaceChildren();
 const candidateList=modelAnswered&&Array.isArray(review.bot_adjustments)?
 review.bot_adjustments:[];
 if(!candidateList.length){
  const p=document.createElement('p');
  p.textContent='Aucune proposition Gemini récente et vérifiée dans ce relevé.';
  ideaBox.append(p);
 }
 const readableName=name=>String(name||'Robot').toUpperCase().replaceAll('_',' ');
 for(const item of candidateList){
  const card=document.createElement('article');card.className='ait-activity-item';
  const heading=document.createElement('strong');
  heading.textContent=readableName(item.strategy)+' — idée encore non testée';
  const profile=document.createElement('p');
  profile.textContent=item.entry_scale===1.2?
   'Gemini suggère de rendre le signal d’entrée plus strict. Ce n’est ni une réduction garantie des pertes ni une diminution de la mise.':
   'Gemini suggère de rendre le signal d’entrée plus réactif. Il pourrait générer plus d’opérations et de frais.';
  const reason=document.createElement('small');
  reason.textContent='Motif avancé par Gemini, non confirmé : '+
    String(item.reason||'aucune justification fournie');
  card.append(heading,profile,reason);ideaBox.append(card);
 }
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
function explainRule(strategy,multi,robot){
 const interval=Number(robot?.timeframe_min);
 const period=multi?'la clôture de chaque journée de marché':
  'des périodes de prix terminées'+(Number.isFinite(interval)&&interval>0?
  ' de '+interval+' minute(s)':'');
 const rules={
  momentum:'Acheter si le prix dépasse sa moyenne des 20 dernières périodes d’environ 0,3 %. Vendre si le prix passe environ 0,3 % sous cette moyenne.',
  reversion:'Acheter si le prix descend d’au moins 1 % sous la moyenne des 20 dernières périodes. Vendre lorsqu’il remonte au moins 0,5 % au-dessus.',
  breakout:'Acheter quand le prix dépasse le plus haut des 20 périodes précédentes. Vendre lorsqu’il descend sous le plus bas des 10 précédentes.',
  rsi:'Acheter quand un indicateur de hausse et baisse, appelé RSI, descend sous 35 ; vendre lorsqu’il dépasse 60. Cet indicateur ne prévoit pas l’avenir.',
  ema_cross:'Comparer deux moyennes qui réagissent au prix : une rapide de 9 périodes et une plus lente de 21. Acheter si la rapide passe assez au-dessus, vendre quand elle passe en dessous.',
  bollinger:'Acheter si le prix tombe beaucoup plus bas que sa zone habituelle des 20 dernières périodes. Vendre lorsqu’il remonte au-dessus de la moyenne.',
  volatility:'Acheter si le prix dépasse ses récents sommets et que les variations ont été suffisamment fortes. Vendre lorsqu’il repasse sous la moyenne.',
  scalp_momentum:'Acheter après une montée de plus de 0,4 % sur trois périodes, si le prix dépasse également sa moyenne. Vendre s’il perd environ 0,4 % depuis son dernier sommet.',
  scalp_trailing:'Acheter après une montée de plus de 0,5 % sur trois périodes, si le prix dépasse sa moyenne. Vendre s’il perd environ 0,6 % depuis le dernier sommet.',
  scalp_microtrend:'Acheter si les trois dernières périodes montent et que le prix dépasse la moyenne de plus de 0,3 %. Vendre si la hausse s’inverse ou si le prix recule de 0,5 % depuis son sommet.',
  scalp_conservative:'Acheter seulement après une montée de plus de 0,8 % sur trois périodes et si le prix dépasse assez sa moyenne. Vendre s’il perd environ 0,8 % depuis son sommet.'
 };
 let body;
 if(strategy.endsWith('_hold')){
  body='Acheter une première fois dès que le marché et les prix le permettent, puis conserver cet actif pour servir de comparaison. Pas d’aller-retour à chaque petite variation.';
 }else if(multi){
  body='Observer les 20 derniers jours de prix terminés. Acheter si le dernier prix clôturé est au moins 0,5 % au-dessus de sa moyenne ; vendre s’il descend au moins 0,5 % en dessous. L’achat fictif attend une cotation éligible : certains marchés sont fermés le soir ou le week-end.';
 }else{
  const mode=strategy.replace(/^[a-z]+_/,'');
  body=rules[mode]||'Appliquer la règle algorithmique prévue pour ce robot : sa fiche suit les achats et les ventes réellement simulés.';
 }
 const entry=(Array.isArray(evolution.robots)?evolution.robots:[])
  .find(x=>x.strategy===strategy);
 const scale=Number(entry?.current_entry_scale);
 const adjustment=Number.isFinite(scale)&&scale!==1?
  ' Un ajustement approuvé du seuil est actif ; les pourcentages indiqués ci-dessus sont ceux du réglage de référence.':
  '';
 return 'Le robot observe '+period+'. '+body+adjustment+
  ' Si les conditions ne sont pas réunies, il attend sans inventer d’opération.';
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
 put('ait-sheet-rule',explainRule(strategy,multi,bot));
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