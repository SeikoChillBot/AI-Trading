/* Lab 04: read-only autonomous research dashboard. */
(function(){
'use strict';
const report=DATA.research||{};
const get=id=>document.getElementById(id);
const stamp=value=>{const t=Date.parse(value);return Number.isFinite(t)?new Intl.DateTimeFormat('fr-FR',{timeZone:'Europe/Paris',day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'}).format(new Date(t)):'date inconnue'};
const put=(id,value)=>{const node=get(id);if(node)node.textContent=String(value)};
if(!get('research-panel')&&!get('research-title'))return;
if(!report.ready){
 put('research-status','La première analyse automatique est en attente de publication.');
 put('research-ai-state','En attente');
 return;
}
const labs=report.labs||{};
const n=Number(labs.crypto?.count||0)+Number(labs.multi?.count||0);
const eligible=Number(report.qualification?.ready_for_human_review||0);
const ideas=Array.isArray(report.hypotheses)?report.hypotheses:[];
put('research-bots',n||'—');
put('research-eligible',String(eligible));
put('research-ideas',String(ideas.length));
const modelState=report.ai_status?.state||'not_configured';
put('research-ai-state',modelState==='model_reflection_completed'?'Analyse IA disponible':'Analyse automatique');
put('research-status',eligible===0?
  'Les données sont encore trop récentes : aucune stratégie validée. Les variantes proposées ci-dessous sont des hypothèses non testées.':
  eligible+' stratégie(s) documentée(s) pour une revue statistique. Cela ne prouve pas leur rentabilité future.');
const timestamp=Date.parse(report.generated_at||'');
const date=Number.isFinite(timestamp)?
 new Intl.DateTimeFormat('fr-FR',{timeZone:'Europe/Paris',day:'2-digit',month:'long',hour:'2-digit',minute:'2-digit'}).format(new Date(timestamp)):
 'date indisponible';
const human=modelState==='model_reflection_completed'?'Modèle d’IA interrogé ; propositions non validées.':
 'Statistiques automatisées actives. Modèle d’IA générative non connecté.';
put('research-updated','Dernière recherche : '+date+' · '+human+' Aucun ordre réel. Modifications de paramètres uniquement après validation prospective.');
const intel=report.market_intelligence||{};
const feeling=intel.sentiment||{};
put('intel-sentiment',Number.isInteger(feeling.index)?feeling.index+'/100':'—');
function toBillions(value){return Number(value)>0?(Number(value)/1e9).toFixed(1)+' Md USD':'—';}
put('intel-ethereum',toBillions((intel.chain_tvl||{}).tvl_usd_by_chain?.Ethereum));
put('intel-stablecoins',toBillions(intel.stablecoins?.circulating_usd_estimate));
const whale=intel.whales||{};
put('intel-whales',whale.state==='not_configured'?
 'Baleines : aucun wallet vérifié configuré. Aucun achat supposé.':
 'Baleines : '+Number(whale.observed_transfer_events||0)+' transfert(s) brut(s) observé(s). Achats non confirmés.');
const host=get('research-idea-list');if(!host)return;
host.replaceChildren();
for(const idea of ideas){
 const card=document.createElement('article');card.className='research-idea';
 const title=document.createElement('strong');title.textContent=idea.title||'Hypothèse à examiner';
 const why=document.createElement('p');why.textContent=idea.why||'Données insuffisantes';
 const test=document.createElement('p');test.textContent='Test proposé : '+(idea.experiment||'À définir');
 const criterion=document.createElement('small');criterion.textContent='Condition : '+(idea.success_rule||'Non définie');
 card.append(title,why,test,criterion);host.append(card);
}
const historical=DATA.challenger_optimization||{};
const historicalList=get('challenger-evaluations');
if(historicalList){
 historicalList.replaceChildren();
 if(historical.ready&&Array.isArray(historical.instruments)){
  for(const item of historical.instruments){
   const card=document.createElement('article');card.className='research-idea';
   const title=document.createElement('strong');
   title.textContent=item.asset+' : '+item.folds+' fenêtres chronologiques';
   const pct=document.createElement('p');
   const relative=Number(item.oos_excess);
   pct.textContent='Écart historique moyen vs conserver : '+
      (relative>0?'+':'')+relative.toFixed(2)+' points de pourcentage';
   const details=document.createElement('small');
   details.textContent='Risque maximal observé : '+Number(item.worst_drawdown).toFixed(1)+
     ' % | SMA'+item.parameters.window+' | Seuil '+(item.parameters.buffer*100).toFixed(1)+' %';
   card.append(title,pct,details);historicalList.append(card);
  }
 }else{
  const note=document.createElement('p');note.className='micro-note';
  note.textContent='Validation historique non disponible.';
  historicalList.append(note);
 }
}
const aiReview=DATA.ai_review||{};
const aiHost=get('ai-experiment-list');
if(aiHost){
 aiHost.replaceChildren();
 const fromModel=['openai_responses','gemini_generate_content'].includes(aiReview.source)&&aiReview.state==='model_reflection_completed';
 const label=fromModel?'Modèle IA connecté : hypothèses à tester.':
  'Diagnostic de robustesse statistique. Modèle IA externe non activé.';
 const observations=Array.isArray(aiReview.historical?.assets)?aiReview.historical.assets:[];
 put('ai-review-summary',aiReview.ready?
  label+' Aucune stratégie automatiquement promue ; résultats historiques non garantis.':
  'Diagnostic de robustesse en attente de sa première publication.');
 for(const item of observations.slice(0,3)){
  const card=document.createElement('article');card.className='research-idea';
  const name=document.createElement('strong');name.textContent=item.asset+' · '+item.folds+' périodes historiques';
  const findings=document.createElement('p');
  findings.textContent='Rendement moyen '+Number(item.avg_net_return_pct).toFixed(2)+
   ' % ; contre Hold '+Number(item.avg_excess_vs_hold_points).toFixed(2)+
   ' points ; avec frais doublés '+Number(item.avg_net_return_double_cost_pct).toFixed(2)+' %.';
  const limits=document.createElement('small');
  const passed=Object.values(item.research_checks||{}).filter(Boolean).length;
  const total=Object.keys(item.research_checks||{}).length;
  limits.textContent=item.closed_trades+' transactions closes · drawdown '+Number(item.worst_drawdown_pct).toFixed(1)+
   ' % · '+passed+'/'+total+' contrôles de recherche. Non validé pour une mise réelle.';
  card.append(name,findings,limits);aiHost.append(card);
 }
 const proposals=Array.isArray(aiReview.experiments)?aiReview.experiments.slice(0,3):[];
 for(const idea of proposals){
  const card=document.createElement('article');card.className='research-idea';
  const title=document.createElement('strong');title.textContent=(idea.asset||'Recherche')+' · '+(idea.title||'Expérience proposée');
  const hypothesis=document.createElement('p');hypothesis.textContent=idea.hypothesis||'Hypothèse non vérifiée.';
  const method=document.createElement('p');method.textContent='À tester : '+(idea.experiment||'Étude à définir.');
  const stopping=document.createElement('small');stopping.textContent='Critère d’abandon : '+(idea.rejection_rule||'Non défini.');
  card.append(title,hypothesis,method,stopping);aiHost.append(card);
 }
}

const pulse=DATA.market_pulse||{};
const pulseBox=get('market-pulse-assets');
if(pulseBox){
 pulseBox.replaceChildren();
 put('pulse-status',pulse.ready?
   'Cours de clôture Kraken et contexte DeFi/sentiment : observations horodatées, pas des prévisions.':
   'Étude de marché indisponible : aucune donnée ni signal inventé.');
 const assets=pulse.assets||{};
 for(const asset of ['BTCUSD','ETHUSD','SOLUSD']){
  const info=assets[asset];if(!info)continue;
  const card=document.createElement('article');card.className='research-idea';
  const title=document.createElement('strong');title.textContent=asset+' · cours clôturé '+(info.last_closed_day_utc||'date inconnue');
  const stats=document.createElement('p');
  const fmt=n=>Number.isFinite(Number(n))?Number(n).toFixed(2)+' %':'—';
  stats.textContent='1 jour '+fmt(info.change_1d_pct)+' · 7 jours '+fmt(info.change_7d_pct)+
   ' · 30 jours '+fmt(info.change_30d_pct)+
   ' · volatilité annualisée estimée '+fmt(info.realized_volatility_30d_annualized_pct);
  card.append(title,stats);pulseBox.append(card);
 }
 const sample=pulse.large_transfers||{};
 const samples=sample.sampled_records||{};
 const sources=Object.values(samples).reduce((n,v)=>n+(Number(v)||0),0);
 put('pulse-whales',sample.state==='observing'||sample.state==='partial'?
  'Gros transferts publics : '+Number(sample.large_transfers_observed||0)+
  ' transfert(s) ≥ 1 M de dollars nominaux dans '+sources+
  ' observations USDC/USDT échantillonnées. Nouveaux depuis la première collecte : '+
  Number(sample.new_in_sample||0)+
  '. Un transfert n’est pas un achat prouvé.':
  'Observation des gros transferts indisponible ; aucune activité de baleine présumée.');
}
const incubator=DATA.forward_challengers||{};
const forwardBox=get('forward-incubator-list');
if(forwardBox){
 forwardBox.replaceChildren();
 const data=incubator.assets||{};
 const number=Object.keys(data).length;
 put('forward-incubator-status',incubator.ready?
   number+' challenger(s) distinct(s) du laboratoire principal. Départ prospectif : aucun historique rejoué.':
   'Suivi prospectif en préparation ; les 36 robots restent indépendants.');
 for(const asset of ['BTCUSD','ETHUSD','SOLUSD']){
  const info=data[asset];if(!info)continue;
  const card=document.createElement('article');card.className='research-idea';
  const name=document.createElement('strong');name.textContent=asset+' · challenger v'+(info.version||1);
  const performance=document.createElement('p');
  performance.textContent='Capital fictif : '+Number(info.equity_usd||20).toFixed(2)+
   ' USD · variation '+Number(info.net_return_pct||0).toFixed(2)+
   ' % · témoin Hold '+Number(info.hold_equity_usd||20).toFixed(2)+' USD.';
  const limits=document.createElement('small');
  const params=info.parameters||{};
  limits.textContent=Number(info.observations||0)+' séance(s) après inscription · '+
   Number(info.closed_trades||0)+' aller-retour(s) clôturés · SMA'+(params.window||'?')+
   ' · seuil '+(Number(params.buffer||0)*100).toFixed(2)+
   ' %. Statut : '+(info.ready_for_review?'revue statistique possible':'observation insuffisante')+'.';
  card.append(name,performance,limits);forwardBox.append(card);
 }
}

const evolution=DATA.robot_evolution||{};
const evolList=get('evolution-bot-list');
if(evolList){
 const entries=Array.isArray(evolution.robots)?evolution.robots:[];
 const statusLabels={
   baseline_held:'Témoin de conservation, inchangé',
   analyzing_for_opportunities:'En veille : données insuffisantes pour modifier',
   testing_proposal:'Variante en cours de test, pas encore validée',
   tuning_activated:'Réglage appliqué en simulation après validation',
 };
 const counts=evolution.counts||{};
 put('evolution-total',String(evolution.ready?entries.length:0));
 put('evolution-testing',String(counts.testing||0));
 put('evolution-activated',String(counts.activated||0));
 put('evolution-summary',evolution.ready?
  'Chaque robot conserve son historique. Gemini propose des réglages limités, mesurés puis éventuellement activés après validation hors échantillon.':
  'Journal individuel en attente du premier cycle de recherche. Aucun réglage automatique présumé.');
 const filter=get('evolution-filter');
 const renderEvol=()=>{
   const selected=filter?.value||'all';
   evolList.replaceChildren();
   let shown=0;
   for(const item of entries){
     if(selected!=='all'&&selected!==item.lab&&selected!==item.status)continue;
     shown++;
     const card=document.createElement('article');card.className='research-idea';
     const heading=document.createElement('strong');
     heading.textContent=String(item.strategy||'Robot').replaceAll('_',' ')+' · '+(item.lab==='crypto'?'Crypto':'Multi-actifs');
     const state=document.createElement('p');
     state.textContent=statusLabels[item.status]||'Étude en cours';
     const stats=document.createElement('p');
     const ret=Number(item.paper_return_pct);
     stats.textContent='Simulation actuelle : '+(Number.isFinite(ret)?ret.toFixed(2)+' %':'données en attente')+
       ' · '+Number(item.closed_roundtrips||0)+' allers-retours clôturés · '+
       Number(item.samples||0)+' observations.';
     const tuning=document.createElement('small');
     tuning.textContent='Sensibilité actuellement utilisée : x'+Number(item.current_entry_scale||1).toFixed(1)+
       (item.proposed_entry_scale?' · Variante envisagée : x'+Number(item.proposed_entry_scale).toFixed(1):'')+
       (item.last_change_at?' · Dernier réglage : '+stamp(item.last_change_at):'');
     card.append(heading,state,stats,tuning);
     if(item.gemini_decision){
       const why=document.createElement('p');
       why.textContent=(item.decision_source==='automatic_statistical_shadow'?
         'Moteur statistique : ':'Gemini : ')+item.gemini_decision;
       card.append(why);
     }
     if(Array.isArray(item.blocked_checks)&&item.blocked_checks.length){
       const blocked=document.createElement('small');
       const terms={
         minimum_elapsed_days:'durée d’observation trop courte',
         minimum_closed_roundtrips:'pas assez d’achats et ventes terminés',
         sufficient_distinct_future_candles:'pas assez de nouveaux cours observés',
         bounded_missing_market_observations:'trop de données manquantes',
         improves_net_after_costs:'gain après frais non démontré',
         double_fees_not_loss:'risque de perte lorsque les frais augmentent',
         bounded_maximum_drawdown:'risque de baisse trop important',
         missing_forward_shadow_data:'premiers résultats encore attendus',
         stale_shadow_evidence:'résultats trop anciens',
         shadow_provenance_or_candidate_mismatch:'comparaison non certifiée',
         incomplete_or_invalid_shadow_statistics:'données de comparaison incomplètes'
       };
       blocked.textContent='Encore à vérifier : '+item.blocked_checks.map(k=>terms[k]||'contrôle technique en attente').join(' · ');
       card.append(blocked);
     }
     evolList.append(card);
   }
   if(!shown){
     const empty=document.createElement('p');empty.className='micro-note';
     empty.textContent='Aucun robot dans ce filtre pour le moment.';
     evolList.append(empty);
   }
 };
 if(filter)filter.addEventListener('change',renderEvol);
 renderEvol();
 const events=get('evolution-event-list');
 if(events){
   events.replaceChildren();
   const items=Array.isArray(evolution.events)?evolution.events:[];
   if(!items.length){
     const p=document.createElement('p');p.className='micro-note';
     p.textContent='Aucune modification ni proposition individuelle enregistrée à cette date.';
     events.append(p);
   }
   for(const e of items.slice(0,40)){
     const article=document.createElement('article');article.className='research-idea';
     const title=document.createElement('strong');
     title.textContent=(e.robot||'Robot')+' · '+(e.action||'événement');
     const desc=document.createElement('p');
     desc.textContent=(e.at?stamp(e.at)+' · ':'')+(e.details||'')+
       (e.to_scale?' · nouveau profil candidat x'+Number(e.to_scale).toFixed(1):'');
     article.append(title,desc);events.append(article);
   }
 }
}

})();
