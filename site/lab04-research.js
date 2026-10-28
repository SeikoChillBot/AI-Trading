/* Lab 04: read-only autonomous research dashboard. */
(function(){
'use strict';
const report=DATA.research||{};
const get=id=>document.getElementById(id);
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
put('research-updated','Dernière recherche : '+date+' · '+human+' Aucun ordre réel, aucune modification des robots.');
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

})();
