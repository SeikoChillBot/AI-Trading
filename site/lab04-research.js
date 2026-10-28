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
})();
