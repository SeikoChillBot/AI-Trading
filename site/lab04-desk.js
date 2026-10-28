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
const stats=d.stats||{};
put('desk-bots',d.ready?Number(stats.tracked||0):'—');
put('desk-tests',d.ready?Number(stats.testing||0):'—');
const trials=Array.isArray(d.experiments)?d.experiments:[];
put('desk-experiments',d.ready?trials.length:'—');
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
  const pct=Number(item.estimated_net_pct);
  const amount=Number(item.equity_usd);
  card(placements,(item.asset||'Actif')+' · '+Number(item.horizon_days||0)+' jour(s)',
   status+' · '+(item.rationale||'Hypothèse de recherche'),
   'Démarré : '+stamp(item.created_at)+
    ' · Capital fictif : '+(Number.isFinite(amount)?amount.toFixed(2)+' $':'en attente')+
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
