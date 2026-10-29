/* AIT — lecture simple, présentée avant les diagnostics. Données vérifiées seulement. */
(function(){
'use strict';
const D=(typeof DATA!=='undefined' && DATA && typeof DATA==='object')?DATA:{};
const el=id=>document.getElementById(id);
const fmt=(v)=>Number.isFinite(Number(v))?Math.round(Number(v)).toLocaleString('fr-FR'):'—';
const stamp=v=>{const t=Date.parse(v||'');return Number.isFinite(t)?
 new Intl.DateTimeFormat('fr-FR',{timeZone:'Europe/Paris',day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'}).format(new Date(t)):'date inconnue'};
const div=(tag,cls,txt)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(txt!==undefined)e.textContent=txt;return e};
const put=(id,v)=>{if(el(id))el(id).textContent=String(v)};
const research=D.research||{},status=research.ai_status||{},evolution=D.robot_evolution||{};
const counts=evolution.counts||{},radar=D.whale_radar||{},follow=radar.follow||{};
const modelFresh=Number.isFinite(Date.parse(status.model_last_called_at||'')) &&
 Date.now()-Date.parse(status.model_last_called_at)<18*3600000;
let modelTitle,modelText;
if(status.state==='model_reflection_completed'&&modelFresh){
 modelTitle='Gemini a répondu';
 modelText='Dernier avis vérifié : '+stamp(status.model_last_called_at)+'. Ce sont des idées, pas des gains garantis.';
}else if(status.state==='model_reflection_completed'){
 modelTitle='Dernier avis à actualiser';
 modelText='Dernière réponse Gemini : '+stamp(status.model_last_called_at)+'. Les calculs automatiques continuent.';
}else{
 modelTitle='Gemini à vérifier';
 modelText='Les calculs du laboratoire continuent, même si Gemini ne répond pas.';
}
const tracked=Array.isArray(follow.tracked_addresses)?follow.tracked_addresses:[];
const good=tracked.filter(x=>x?.monitoring!=='temporarily_unavailable');
const sampleCount=Object.values(radar.validated_records||{}).reduce((a,b)=>a+(Number(b)||0),0);
let whaleTitle='Observation en cours',whaleText='Un transfert observé ne prouve pas que quelqu’un a acheté.';
if(good.length){
 whaleTitle=good.length+' adresse(s) suivie(s)';
 whaleText='Dans un échantillon de '+fmt(sampleCount)+' transferts vérifiés. Les propriétaires restent inconnus.';
}else if(tracked.length){
 whaleTitle='Suivi temporairement ralenti';
 whaleText=tracked.length+' adresse(s) conservée(s), mais certaines lectures sont indisponibles.';
}else if(radar.ready){
 whaleTitle='Pas de grosse opération repérée';
 whaleText='Dans le dernier petit échantillon seulement : aucune conclusion sur le marché entier.';
}else{
 whaleTitle='Collecte à vérifier';
 whaleText='Les données sont absentes ou partielles ; aucune activité ne sera inventée.';
}
let botTitle=evolution.ready===false?'Résultats en attente':fmt(counts.testing||0)+' idées à l’essai';
let botText=fmt(counts.activated||0)+' changement(s) validé(s) sur '+fmt(counts.tracked||36)+
 ' robots. Les 12 robots de référence ne changent jamais.';

const parent=el('research-title')?.closest('.research-panel');
if(parent && !el('ait-beginner-snapshot')){
 const section=div('section','ait-beginner-snapshot');
 section.id='ait-beginner-snapshot';
 section.setAttribute('aria-label','Résumé du laboratoire');
 section.append(div('h3','', 'L’essentiel, sans jargon'));
 const grid=div('div','ait-summary-grid');
 for(const [name,value,desc] of [
    ['L’intelligence artificielle',modelTitle,modelText],
    ['Évolution des robots',botTitle,botText],
    ['Gros mouvements',whaleTitle,whaleText]]){
   const card=div('article','ait-summary-card');
   card.append(div('small','',name),div('strong','',value),div('p','',desc));
   grid.append(card);
 }
 const pulse=D.market_pulse||{};
 const marketLine=div('p','ait-simple-caption');
 const moves=['BTCUSD','ETHUSD','SOLUSD'].map(asset=>{
  const info=pulse.assets?.[asset];
  if(!info||!Number.isFinite(Number(info.change_7d_pct)))return null;
  const n=Number(info.change_7d_pct);
  return asset.slice(0,3)+' '+(n>0?'+':'')+n.toFixed(1)+' %';
 }).filter(Boolean);
 marketLine.textContent=moves.length?'Évolution des cryptos sur 7 jours : '+moves.join(' · ')+
  '. Ce sont des observations passées, pas des prévisions.':
  'Dernières évolutions des cryptos : données en cours de vérification.';
 section.append(grid,marketLine,div('p','ait-simple-caption',
  'Tous les montants sont fictifs et les résultats ne prouvent pas une rentabilité future.'));
 const metrics=parent.querySelector('.research-panel-metrics');
 if(metrics)parent.insertBefore(section,metrics);else parent.append(section);
}
const topSummary=el('ait-simple-overview');
if(topSummary)topSummary.hidden=true; // avoid duplicate summary from other source variants
put('ait-simple-gemini',modelTitle);
put('ait-simple-gemini-note',modelText);
put('ait-simple-robots',botTitle);
put('ait-simple-robots-note',botText);
put('ait-simple-whales',whaleTitle);
put('ait-simple-whales-note',whaleText);
const mainInfo=el('ait-friendly-status');
if(mainInfo)mainInfo.textContent='36 robots, deux expériences fictives. Les résultats sont mis à jour régulièrement, mais ne correspondent à aucun compte bancaire.';
})();
