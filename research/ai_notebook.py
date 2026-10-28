"""Verifiable Gemini work journal and financial research news feed.

Only existing recorded decisions are described as changes. All published
model commentary remains marked as unverified research, never gain claims.
"""
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCES={
    "ai":ROOT/"reports/ai_research_proposals.json",
    "status":ROOT/"reports/ai_research_status.json",
    "evolution":ROOT/"reports/robot_evolution.json",
    "experiments":ROOT/"reports/ai_placement_experiments.json",
    "news":ROOT/"reports/market_news.json",
    "pulse":ROOT/"reports/market_pulse.json",
}
STATE=ROOT/"state/ai_journal_state.json"
OUTPUT=ROOT/"reports/ai_journal.json"

def read(path):
    try:
        o=json.loads(path.read_text(encoding="utf-8"))
        return o if isinstance(o,dict) else {}
    except (OSError,ValueError):
        return {}

def build(now, data, old):
    history=list(old.get("entries",[])) if isinstance(old.get("entries"),list) else []
    seen={x.get("id") for x in history if isinstance(x,dict)}
    def record(kind,at,title,details,link=None):
        if not at or not isinstance(title,str) or not title.strip():
            return
        marker=hashlib.sha256((kind+"|"+str(at)+"|"+title).encode()).hexdigest()[:18]
        if marker in seen:return
        item={"id":marker,"type":kind,"at":at,
              "title":title[:130],"details":str(details)[:650],
              "link":link if isinstance(link,str) and link.startswith("https://") else None,
              "real_trade":False}
        history.append(item);seen.add(marker)
    ai=data.get("ai",{})
    status=data.get("status",{})
    if ai.get("source")=="gemini_generate_content" and ai.get("state")=="model_reflection_completed":
        at=status.get("model_last_called_at")
        record("ai_note",at,"Analyse Gemini — synthèse",
               str(ai.get("summary",""))[:650])
        for i,note in enumerate(ai.get("desk_notes",[])[:3]):
            if isinstance(note,dict) and note.get("text"):
                record("ai_note",at,f'Note {i+1} — {note.get("category","analyse")}',
                       note.get("text","")+" [Hypothèse IA non validée]")
    evol=data.get("evolution",{})
    for item in evol.get("events_this_cycle",[])[:15]:
        if not isinstance(item,dict):continue
        action=item.get("action")
        if action=="paper_tuning_activated":
            verb="Réglage fictif activé après validation"
        elif action=="paper_tuning_rolled_back":
            verb="Retour automatique au réglage précédent"
        elif action=="proposed_by_gemini":
            verb="Proposition Gemini : expérimentation ouverte"
        else:
            continue
        record("patchnote",item.get("at"),verb+" — "+str(item.get("robot")),
               str(item.get("details",""))+
               f' | Profil {item.get("from_scale")} → {item.get("to_scale")}')
    placement=data.get("experiments",{})
    for item in placement.get("events",[])[:10]:
        if not isinstance(item,dict) or not item.get("asset"):continue
        state=item.get("status","")
        if state not in ("paper_experiment_registered","completed_unvalidated_paper_trial"):
            continue
        record("paper_test",placement.get("generated_at"),
               str(item["asset"])+" — "+("nouveau test fictif" if state=="paper_experiment_registered" else "test fictif terminé"),
               "Capital expérimental 20 USD ; prix de clôture modélisés. "
               +("Résultat fictif "+str(item.get("estimated_net_pct"))+" % ; non prédictif."
                 if state=="completed_unvalidated_paper_trial"
                 else "En observation prospective, résultat non disponible."))
    news=data.get("news",{})
    for article in news.get("articles",[])[:10]:
        if isinstance(article,dict) and article.get("source") and article.get("title"):
            record("news",article.get("published_at"),
                   article.get("source")+" — "+article.get("title",""),
                   "Lien vers la publication d'origine. Actualité informative, pas une recommandation de placement.",
                   article.get("url"))
    history=sorted(history,key=lambda x:x.get("at",""),reverse=True)[:85]
    output={
        "schema":1,"generated_at":now.isoformat(),"title":"Gemini — journal du laboratoire",
        "model_status":status.get("state","not_configured"),
        "model": "gemini-3.5-flash-lite" if status.get("provider")=="gemini" else "not_configured",
        "last_ai_call":status.get("model_last_called_at"),
        "market_pulse_at":data.get("pulse",{}).get("generated_at"),
        "source_health":news.get("status","unavailable"),
        "entries":history[:35],
        "latest_notes":ai.get("desk_notes",[])[:3] if ai.get("source")=="gemini_generate_content" else [],
        "paper_experiments":placement.get("trials",[])[:12],
        "robot_statistics":evol.get("counts",{}),
        "limits":"News and AI suggestions are not confirmed profit opportunities; all trades are fictitious.",
        "real_trades":False,
    }
    return output,{"schema":1,"entries":history}

def main():
    now=datetime.now(timezone.utc)
    output,state=build(now,{k:read(v) for k,v in SOURCES.items()},read(STATE))
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    STATE.parent.mkdir(parents=True,exist_ok=True)
    STATE.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Gemini editor journal",len(output["entries"]),"entries")


if __name__=="__main__":
    main()
