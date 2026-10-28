/* Lab 04: transparent comparative research, never a combined trade history. */
(function(){
'use strict';
const L=window.SeikoV4;if(!L)return;
const $=id=>document.getElementById(id);
const ce=(tag,className,text)=>{const node=document.createElement(tag);if(className)node.className=className;if(text!==undefined)node.textContent=text;return node};
function paint(){
 const host=$('cross-scorecard');if(!host)return;host.replaceChildren();
 for(const type of ['crypto','multi']){
  if(type==='multi'&&!L.ready)continue;
  const start=L.init[type],value=L.total[type],difference=value-start;
  const box=ce('article','cross-score');
  const head=ce('div','cross-score-top');
  head.append(ce('strong','',type==='crypto'?'Crypto / Kraken':'Multi-actifs / prix indicatifs'),
              ce('small','',L.day(L.start[type])));
  const amount=ce('strong','cross-score-money',L.money(value));
  const meta=ce('div','cross-score-meta');
  const gain=ce('em',L.tone(difference),L.pct(start?100*difference/start:0));
  meta.append(ce('span','','Départ '+L.money(start)),gain);
  box.append(head,amount,meta);host.append(box);
 }
 const risk=$('cross-risk-grid');risk.replaceChildren();
 const stats=[
  ['ORDRES CRYPTO',L.cr.reduce((n,r)=>n+Number(r.trades||0),0)],
  ['ORDRES MULTI-ACTIFS',L.mr.reduce((n,r)=>n+Number(r.trades||0),0)],
  ['FRAIS CRYPTO',L.money(L.cr.reduce((n,r)=>n+Number(r.fees_usd||0),0),3)],
  ['FRAIS MULTI-ACTIFS',L.money(L.mr.reduce((n,r)=>n+Number(r.fees_usd||0),0),3)],
  ['QUALITÉ DE L’ÉCHANTILLON','En observation'],
  ['MARCHÉS MESURÉS',L.ready?'9 références':'En attente']
 ];
 for(const [label,value] of stats){const card=ce('div','');card.append(ce('small','',label),ce('strong','',value));risk.append(card)}
 drawMultiChart();
}
