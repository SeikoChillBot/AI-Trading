/* Verified system health & hourly paper laboratory; never mutate any account. */
(function(){
'use strict';
const get=id=>document.getElementById(id);
const put=(id,value)=>{const node=get(id);if(node)node.textContent=String(value)};
const tile=(host,title,description,details)=>{
 if(!host)return;
 const art=document.createElement('article');art.className='research-idea';
 const label=document.createElement('strong');label.textContent=title;
 const p=document.createElement('p');p.textContent=description;
 art.append(label,p);
 if(details){const small=document.createElement('small');small.textContent=details;art.append(small)}
 host.append(art);
};
const operations=DATA.operations||{};
const statuses={active:'Actif',testing:'En test',partial:'Partiel',
  degraded:'Dégradé',pending:'En attente',disabled:'Désactivé'};
const roadmap=get('operations-roadmap');
if(roadmap){
 roadmap.replaceChildren();
 put('operations-status',operations.ready?
  'Relevé automatique : '+(operations.generated_at||'date inconnue')+
  ' · '+(operations.status==='needs_attention'?'anomalies à examiner':'système en observation'):
  'Premier diagnostic opérationnel en attente. Ne pas supposer que tout fonctionne.');
 const rows=Array.isArray(operations.roadmap)?operations.roadmap:[];
 if(!rows.length)tile(roadmap,'Données en attente','Aucune capacité ne peut être confirmée.');
 for(const item of rows)
  tile(roadmap,(statuses[item.status]||'Inconnu')+' · '+(item.title||'Fonction'),
       item.detail||'État non précisé.');
 const problems=get('operations-alerts');
 if(problems){
  problems.replaceChildren();
  const alerts=Array.isArray(operations.alerts)?operations.alerts:[];
  if(!alerts.length)tile(problems,'Aucune alerte issue du dernier contrôle',
                         'Un workflow ou une source peut néanmoins échouer ultérieurement.');
  for(const alert of alerts)tile(problems,'Signalement',String(alert));
  const workflowList=operations.workflows?.workflows||operations.workflows||{};
  for(const [name,run] of Object.entries(workflowList)){
   if(!run||typeof run!=='object')continue;
   tile(problems,(run.state==='healthy'?'Dernier cycle réussi':'Dernier cycle à examiner')+
        ' · '+name,'Run #'+String(run.run_id||'inconnu'),
        'Résultat : '+(run.last_result||'indisponible'));
  }
 }
}
const hour=DATA.intraday_study||{};
const hourlyHost=get('hourly-study-list');
if(hourlyHost){
 hourlyHost.replaceChildren();
 put('hourly-study-status',hour.ready?
   'Étude Kraken 60 minutes : '+String(hour.generated_at||'date indisponible')+
   ' · résultats après frais sans garantie de performance.':
   'Recherche horaire indisponible ou en préparation ; aucune performance inventée.');
 for(const asset of ['BTCUSD','ETHUSD','SOLUSD']){
  const entry=(hour.assets||{})[asset];
  if(!entry)continue;
  const history=entry.historical_study||{};
  const forward=entry.paper_forward||{};
  const pct=v=>typeof v==='number'&&Number.isFinite(v)?v.toFixed(2)+' %':'—';
  tile(hourlyHost,asset+' · étude horaire',
    'Hors échantillon historique : '+pct(history.avg_net_return_pct)+
    ' net ; écart au Hold '+pct(history.avg_excess_vs_hold)+
    ' ; drawdown max '+pct(history.max_drawdown_pct),
    'Suivi futur séparé : '+Number(forward.observations||0)+
    ' bougie(s), '+(typeof forward.capital_usd==='number'?forward.capital_usd.toFixed(2):'—')+
    ' USD fictifs ; pas de rentabilité démontrée.');
 }
 if(!Object.keys(hour.assets||{}).length)
  tile(hourlyHost,'Études en attente','Kraken ne fournit pas encore des données horaires validées.');
}
})();
