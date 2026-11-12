/* Seiko Lab / lecture rapide : présentation uniquement, aucune décision de trading. */
(function(){
'use strict';
const L=window.SeikoV4;
const D=(typeof DATA==='object'&&DATA)||{};
const home=document.getElementById('view-home');
if(!L||!home)return;
const make=(tag,cls,txt)=>{
  const node=document.createElement(tag);
  if(cls)node.className=cls;
  if(txt!==undefined)node.textContent=String(txt);
  return node;
};
const finite=v=>typeof v==='number'&&Number.isFinite(v);
const stamp=v=>{
  const n=Date.parse(v||'');
  return Number.isFinite(n)?
    new Intl.DateTimeFormat('fr-FR',{day:'numeric',month:'short',hour:'2-digit',minute:'2-digit',timeZone:'Europe/Paris'}).format(new Date(n)):
    'date indisponible';
};
const root=make('section','ait-focus-panel');
root.id='ait-focus-panel';
root.setAttribute('aria-label','Votre laboratoire en résumé');
const header=make('div','ait-focus-head');
const heading=make('div','');
heading.append(make('span','ait-focus-eyebrow','TABLEAU DE BORD · SIMULATION'),
  make('h2','ait-focus-title','L’essentiel, en 20 secondes'),
  make('p','ait-focus-intro','36 robots et des expériences de recherche. Chaque montant est fictif : aucun argent réel n’est investi.'));
const mode=make('button','ait-focus-mode','Afficher tous les détails');
mode.type='button';mode.setAttribute('aria-pressed','false');
header.append(heading,mode);
const freshness=make('p','ait-focus-freshness');
const grid=make('div','ait-focus-grid');
const takeaway=make('div','ait-focus-takeaway');
const links=make('div','ait-focus-links');
const nav=[
  ['Comparer les 36 robots','robots'],
  ['Suivre les nouvelles stratégies','candidates'],
  ['Lire le journal de Gemini','desk']
];
for(const [label,view] of nav){
  const button=make('button','ait-focus-link',label);
  button.type='button';button.addEventListener('click',()=>L.goto?.(view));
  links.append(button);
}
root.append(header,freshness,grid,takeaway,links);
const original=home.querySelector('.lab-freshness');
if(original)original.insertAdjacentElement('afterend',root);
else home.prepend(root);
const guide=make('div','ait-route-guide');
guide.setAttribute('aria-live','polite');
document.querySelector('.page-heading')?.insertAdjacentElement('afterend',guide);
const guides={
  home:'Accueil : une vue rapide de chaque groupe. Le graphique plus bas correspond uniquement au groupe sélectionné.',
  robots:'Robots : retrouve les 36 stratégies et ouvre une fiche pour voir son historique et sa courbe.',
  candidates:'Nouveaux : des stratégies expérimentales distinctes des 36 robots. Une idée en test n’est pas un succès.',
  analysis:'Analyse : compare les performances, les frais, les risques et la durée des observations.',
  desk:'Journal IA : sépare les réponses de Gemini, les calculs statistiques et les décisions réellement appliquées.',
  explore:'Marchés : découvre les actifs étudiés ; tous ne sont pas forcément simulés avec des cours exécutables.'
};
function updateGuide(){
  const name=(location.hash||'#home').replace('#','').toLowerCase();
  guide.textContent=guides[name]||guides.home;
  guide.hidden=name==='home';
}
let selected='crypto';
try{
  const saved=localStorage.getItem('seiko-lab04-wallet');
  if(saved==='multi'&&L.ready)selected='multi';
  else if(saved==='crypto')selected='crypto';
  else selected=L.ready?'multi':'crypto';
}catch(e){selected=L.ready?'multi':'crypto';}
let simple=true;
try{simple=localStorage.getItem('seiko-lab-v8-reading')!=='detail';}catch(e){}
function setMode(value){
  simple=value;
  document.body.classList.toggle('ait-reading-simple',simple);
  mode.textContent=simple?'Afficher tous les détails':'Revenir à l’essentiel';
  mode.setAttribute('aria-pressed',String(!simple));
  try{localStorage.setItem('seiko-lab-v8-reading',simple?'simple':'detail');}catch(e){}
}
mode.addEventListener('click',()=>setMode(!simple));
function sparkline(scope){
  const points=(L.history[scope]||[]).filter(p=>finite(p.v)&&finite(p.t));
  if(points.length<2)return make('span','ait-focus-nodata','Courbe en attente de relevés');
  const vals=points.map(p=>p.v),low=Math.min(...vals),high=Math.max(...vals);
  const denom=Math.max(0.001,high-low),width=260,height=62;
  const t0=points[0].t,t1=points[points.length-1].t;
  const line=points.map((p,i)=>{
    const x=8+(t1>t0?(p.t-t0)/(t1-t0):i/(points.length-1))*(width-16);
    const y=7+(1-(p.v-low)/denom)*(height-14);
    return (i?'L':'M')+x.toFixed(1)+' '+y.toFixed(1);
  }).join(' ');
  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
  svg.setAttribute('viewBox','0 0 260 62');
  svg.setAttribute('role','img');
  svg.setAttribute('aria-label','Évolution observée du groupe '+scope);
  svg.classList.add('ait-focus-spark');
  const path=document.createElementNS('http://www.w3.org/2000/svg','path');
  path.setAttribute('d',line);path.setAttribute('fill','none');
  path.setAttribute('stroke',vals.at(-1)>=vals[0]?'#9fe8bf':'#ff9da9');
  path.setAttribute('stroke-width','2.8');path.setAttribute('stroke-linecap','round');
  path.setAttribute('stroke-linejoin','round');
  svg.append(path);
  return svg;
}
function portfolio(label,scope,count){
  const button=make('button','ait-focus-wallet');
  button.type='button';
  const ready=scope==='crypto'?L.cr.length===18:L.ready;
  button.disabled=!ready;
  const start=L.init[scope],value=L.total[scope];
  const change=ready&&start>0?(value/start-1)*100:null;
  const up=finite(change)&&change>=0;
  button.classList.add(ready?(up?'ait-up':'ait-down'):'ait-pending');
  button.classList.toggle('is-selected',selected===scope);
  button.setAttribute('aria-pressed',String(selected===scope));
  button.append(make('small','',label+' · '+count+' robots'),
    make('strong','ait-focus-value',ready?L.money(value):'Données en attente'),
    make('span','ait-focus-delta',ready?L.pct(change)+' depuis le départ':'Aucune évolution fiable disponible'));
  if(ready)button.append(sparkline(scope));
  button.append(make('span','ait-focus-start',ready?'Départ : '+L.money(start)+' fictifs':'Les relevés manquent'));
  button.addEventListener('click',()=>{
    if(!ready)return;
    selected=scope;L.selectWallet?.(scope);render();
  });
  return button;
}
function research(){
  const forward=D.strategy_forward||{};
  const trials=Array.isArray(forward.trials)?forward.trials:[];
  const number=forward.ready&&finite(forward.tracked)?forward.tracked:forward.ready?trials.length:null;
  const qualified=trials.filter(t=>t?.sufficient_evidence===true).length;
  const box=make('article','ait-focus-research');
  box.append(make('small','','RECHERCHE · NOUVELLES STRATÉGIES'),
    make('strong','ait-focus-value',number===null?'En attente':number+' piste'+(number===1?'':'s')+' suivie'+(number===1?'':'s')),
    make('span','ait-focus-delta',number===null?'Aucun rapport exploitable publié':
      qualified+' piste'+(qualified===1?'':'s')+' avec preuves jugées suffisantes pour examen'),
    make('p','', 'Ces pistes ne sont pas les 36 robots existants. Aucune n’est autorisée ici à passer des ordres réels.'));
  return box;
}
function render(){
  grid.replaceChildren(portfolio('Cryptomonnaies','crypto',18),
    portfolio('Actions, fonds et devises','multi',18),research());
  const statuses=[Date.parse(D.updated||''),Date.parse(D.multi_asset?.updated_at||'')];
  const fresh=statuses.every(v=>Number.isFinite(v)&&v<=Date.now()+60000&&Date.now()-v<=60*60000);
  freshness.textContent=fresh?
    'Derniers relevés : crypto '+stamp(D.updated)+' · autres marchés '+stamp(D.multi_asset?.updated_at):
    'Attention, certains résultats peuvent être anciens. Crypto : '+stamp(D.updated)+
    ' · autres marchés : '+stamp(D.multi_asset?.updated_at)+'.';
  freshness.classList.toggle('ait-focus-warning',!fresh);
  const status=D.research?.ai_status||{};
  const evol=D.robot_evolution||{};
  const active=finite(evol.counts?.activated)?evol.counts.activated:null;
  const last=stamp(status.model_last_called_at);
  takeaway.replaceChildren(
    make('strong','','Que faut-il retenir ?'),
    make('p','',active===null?
      'Validation des modifications : données indisponibles. Ne pas confondre essai et stratégie prouvée.':
      active===0?
      'Aucun changement des robots n’est déclaré validé dans le dernier rapport disponible.':
      active+' changement(s) de robot déclarés validés dans le dernier rapport.'),
    make('p','',status.state==='model_reflection_completed'&&last!=='date indisponible'?
      'Dernier appel Gemini documenté : '+last+'. Ses idées doivent encore être testées.' :
      'Réponse Gemini non confirmée dans les données affichées. Les tests statistiques sont indépendants.')
  );
}
document.querySelectorAll('[data-currency]').forEach(b=>b.addEventListener('click',render));
document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',updateGuide));
window.addEventListener('hashchange',updateGuide);
L.refreshers?.push(render);
setMode(simple);updateGuide();render();
})();