/* Seiko Gemini Desk — render only source-qualified, read-only JSON. */
(function(){
'use strict';
const d=DATA.gemini_desk||{};
const get=id=>document.getElementById(id);
if(!get('gemini-desk-panel'))return;
const put=(id,v)=>{const element=get(id);if(element)element.textContent=String(v)};
const stamp=x=>{const time=Date.parse(x||'');return Number.isFinite(time)?
 new Intl.DateTimeFormat('fr-FR',{timeZone:'Europe/Paris',day:'2-digit',
 month:'short',hour:'2-digit',minute:'2-digit'}).format(new Date(time)):'Date indisponible'};
const card=(host,title,body,sub)=>{
 if(!host)return;
 const item=document.createElement('article');item.className='research-idea';
 const t=document.createElement('strong');t.textContent=title;
 const p=document.createElement('p');p.textContent=body;
 item.append(t,p);
 if(sub){const foot=document.createElement('small');foot.textContent=sub;item.append(foot)}
 host.append(item);return item;
};
const empty=(host,message)=>card(host,'Aucune donnée confirmée',message);
put('desk-ai-status',d.ready&&d.model_status==='model_reflection_completed'?'Analyse disponible':'Relevé en attente');
put('desk-last-report',d.ready?
 'Dernière interrogation du modèle : '+stamp(d.last_ai_call)+
 ' · Dernier journal : '+stamp(d.generated_at)+
 ' · Modèle : '+(d.model||'non renseigné') :
 'Le journal autonome n’a pas encore été publié.');
// Daily dated journal: explicitly distinguishes a genuine Gemini reply from
// deterministic research records. Historical days remain selectable.
const dailyDays=Array.isArray(d.daily_briefs)?d.daily_briefs:[];
const dailyDate=get('desk-daily-date'),dailyContent=get('desk-daily-content');
if(dailyDate&&dailyContent){
 dailyDate.replaceChildren();
 for(const day of dailyDays){
  if(!day||!/^\\d{4}-\\d{2}-\\d{2}$/.test(day.date||''))continue;
  const option=document.createElement('option');
  option.value=day.date;
  const date=new Date(day.date+'T12:00:00');
  option.textContent=Number.isFinite(date.getTime())?
   new Intl.DateTimeFormat('fr-FR',{day:'numeric',month:'long',year:'numeric'}).format(date):
   day.date;
  dailyDate.append(option);
 }
 const renderDaily=()=>{
  dailyContent.replaceChildren();
  const day=dailyDays.find(v=>v&&v.date===dailyDate.value);
  if(!day){
   put('desk-daily-status','Le premier bilan quotidien sera créé lors du prochain cycle de recherche.');
   empty(dailyContent,'Aucun bilan horodaté encore enregistré. Les notes ci-dessous restent accessibles.');
   return;
  }
  put('desk-daily-status',(day.period==='in_progress'?'Journée en cours':'Journée archivée')+
   ' · Relevé '+stamp(day.updated_at)+
   (day.gemini_authored_summary?' · Synthèse Gemini authentifiée':
   ' · Synthèse du laboratoire (aucune réponse Gemini vérifiée)'));
  if(day.gemini_authored_summary){
   card(dailyContent,'Compte rendu de Gemini',String(day.gemini_authored_summary),
        'Réponse du modèle enregistrée dans le journal');
  }
  const sections=[
   ['Recherches effectuées',day.research],
   ['Décisions et expérimentations',day.decisions],
   ['Conclusions du jour',day.conclusions]
  ];
  for(const [heading,items] of sections){
   if(!Array.isArray(items)||!items.length)continue;
   const text=items.filter(x=>typeof x==='string').map(x=>'• '+x).join('\\n');
   card(dailyContent,heading,text);
  }
  if(typeof day.next==='string')card(dailyContent,'Suite du programme',day.next,
    'Décisions limitées au trading fictif et aux sources observées');
 };
 dailyDate.addEventListener('change',renderDaily);
 renderDaily();
}
const stats=d.stats||{};
put('desk-bots',d.ready?Number(stats.tracked||0):'—');
put('desk-tests',d.ready?Number(stats.testing||0):'—');
const trials=Array.isArray(d.experiments)?d.experiments:[];
put('desk-experiments',d.ready?trials.length:'—');
const watch=get('desk-market-watch');
if(watch){
 watch.replaceChildren();
 const alerts=Array.isArray(d.market_watch)?d.market_watch:[];
 if(!alerts.length)empty(watch,'Aucune étude de marché récente fiable disponible.');
 for(const market of alerts){
  const move=Number(market.move_7d_pct);
  const vol=Number(market.annualized_volatility_30d_pct);
  card(watch,(market.asset||'Marché')+' · '+(market.label||'à examiner'),
   'Évolution constatée sur 7 jours : '+(Number.isFinite(move)?move.toFixed(2)+' %':'non disponible')+
   ' · volatilité 30 jours annualisée : '+(Number.isFinite(vol)?vol.toFixed(1)+' %':'non disponible'),
   'Source : Kraken, clôture '+(market.source_at||'inconnue')+
   ' · Ce n’est pas un signal d’achat confirmé.');
 }
}
const placements=get('desk-placements');
if(placements){
 placements.replaceChildren();
 if(!trials.length)empty(placements,'Aucun test indépendant déclenché sur les données disponibles.');
 for(const item of trials){
  const status={
   waiting_next_closed_day:'Inscrit, en attente des données futures',
   in_paper_position:'Placement simulé en observation',
   completed_unvalidated_paper_trial:'Expérience fictive terminée, sans valeur prédictive',
   terminated_missing_observation:'Test interrompu : données manquantes',
   terminated_invalid_price:'Test interrompu : cotation invalide'
  }[item.status]||'Test suspendu ou non vérifié';
  const actor=item.actor==='gemini_structured_decision'?
   'Décision Gemini exécutée automatiquement':
   item.actor==='quantitative_auto_fallback'?
   'Moteur statistique autonome (Gemini en attente)':'Source de décision non précisée';
  const pct=Number(item.estimated_net_pct);
  const amount=Number(item.equity_usd);
  card(placements,(item.asset||'Actif')+' · '+Number(item.horizon_days||0)+' jour(s)',
   status+' · '+(item.rationale||'Hypothèse de recherche'),
   'Démarré : '+stamp(item.created_at)+
    ' · '+actor+' · Capital fictif : '+(Number.isFinite(amount)?amount.toFixed(2)+' $':'en attente')+
    ' · variation fictive : '+(Number.isFinite(pct)?pct.toFixed(2)+' %':'non disponible'));
 }
}
const entries=Array.isArray(d.entries)?d.entries:[];
const notesHost=get('desk-notes');
const updates=get('desk-patchnotes');
const news=get('desk-news');
for(const host of [notesHost,updates,news])if(host)host.replaceChildren();
let notes=0,patches=0,headlines=0;
for(const item of entries){
 if(!item||!item.type)continue;
 if(item.type==='news'){
  headlines++;
  const entry=card(news,item.title||'Publication',item.details||'',
                   'Source publiée : '+stamp(item.at));
  if(entry&&typeof item.link==='string'){
   try{
    const url=new URL(item.link);
    const permitted=['www.federalreserve.gov','www.ecb.europa.eu','www.coindesk.com'];
    if(url.protocol==='https:'&&permitted.includes(url.hostname)){
     const link=document.createElement('a');link.href=url.href;
     link.rel='noopener noreferrer';link.target='_blank';
     link.textContent='Lire la publication originale';
     entry.append(link);
    }
   }catch(e){}
  }
 }else if(item.type==='patchnote'||item.type==='paper_test'){
  patches++;
  card(updates,item.title||'Évolution',item.details||'',
       'Enregistré : '+stamp(item.at));
 }else if(item.type==='ai_note'){
  notes++;
  card(notesHost,item.title||'Analyse IA',item.details||'',
       'Hypothèse / analyse non validée · '+stamp(item.at));
 }
}
if(!notes)empty(notesHost,'Gemini n’a pas encore publié de nouvelle note pour ce créneau.');
if(!patches)empty(updates,'Aucun changement ou nouvel essai fictif enregistré.');
if(!headlines)empty(news,'Aucune publication sourcée récente disponible. Le système n’invente pas d’actualité.');
})();
