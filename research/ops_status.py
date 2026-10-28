"""Source-grounded operational health and live roadmap.

Reports are descriptive only. GitHub action failures are compared with newer
successful runs; past red e-mails are not misreported as current outages.
Never suppresses real CI failures or publishes credentials.
"""
from __future__ import annotations
import json
import os
from datetime import datetime,timezone
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"reports/system_health.json"
API="https://api.github.com/repos/SeikoChillBot/AI-Trading/actions/runs"

def read(path):
    try:
        value=json.loads((ROOT/path).read_text(encoding="utf-8"))
        return value if isinstance(value,dict) else {}
    except (OSError,ValueError):
        return {}

def age_hours(now,obj):
    try:
        timestamp=datetime.fromisoformat(obj["generated_at"])
        if timestamp.tzinfo is None: return None
        return (now-timestamp).total_seconds()/3600
    except (ValueError,TypeError,KeyError):
        return None

def workflows(get=requests.get, token=None):
    try:
        headers={"Accept":"application/vnd.github+json","User-Agent":"SeikoLabHealth/1.0"}
        if token:headers["Authorization"]="Bearer "+token
        response=get(API,params={"per_page":35},headers=headers,timeout=15)
        response.raise_for_status()
        runs=response.json()["workflow_runs"]
        if not isinstance(runs,list):raise ValueError("Invalid GitHub data")
        result={}
        for name in ("Paper trading","Seiko research — guarded automatic analysis"):
            finished=[x for x in runs if x.get("name")==name and
                      x.get("status")=="completed" and x.get("conclusion") in ("success","failure")]
            if not finished:
                result[name]={"state":"unknown","reason":"No completed run in recent GitHub history"}
                continue
            latest=max(finished,key=lambda x:x.get("created_at",""))
            result[name]={
                "state":"healthy" if latest["conclusion"]=="success" else "failure",
                "run_id":latest.get("id"),"last_created_at":latest.get("created_at"),
                "url":latest.get("html_url"),
                "last_result":latest["conclusion"],
            }
        return {"state":"available","workflows":result}
    except (KeyError,TypeError,ValueError,requests.RequestException) as error:
        return {"state":"unavailable","reason":type(error).__name__,"workflows":{}}

def build(now, reports, actions):
    evolution=reports.get("evolution",{})
    model=reports.get("model",{})
    intraday=reports.get("intraday",{})
    transfers=reports.get("transfers",{})
    experiment=reports.get("experiments",{})
    news=reports.get("news",{})
    errors=[]
    def check_fresh(label,obj,limit):
        age=age_hours(now,obj)
        if age is None or age < -1 or age > limit:
            errors.append(label+": rapport absent ou périmé")
            return False
        return True
    model_ok=check_fresh("Gemini",model,16) and model.get("state")=="model_reflection_completed"
    intraday_fresh=check_fresh("Marchés horaires",intraday,6)
    oos=len(intraday.get("assets",{})) if isinstance(intraday.get("assets"),dict) else 0
    hourly_ok=intraday_fresh and oos>=2
    robots= int(evolution.get("counts",{}).get("tracked") or 0)
    if robots!=36:errors.append("Registre de 36 robots incomplet")
    if not model_ok:errors.append("Dernière analyse Gemini non confirmée")
    if not hourly_ok:errors.append("Marché horaire insuffisant ou indisponible")
    if transfers.get("state")=="unavailable":errors.append("Transferts publics non accessibles")
    if news.get("status")=="unavailable":errors.append("Flux d'actualités indisponibles")
    for name,item in actions.get("workflows",{}).items():
        if item.get("state")=="failure":
            errors.append("Échec récent du workflow "+name+" (#"+str(item.get("run_id"))+")")
    roadmap=[
        {"id":"robots","title":"36 robots de simulation","status":"active" if robots==36 else "degraded",
         "detail":str(robots)+" robots identifiés ; 12 Hold servent de témoins."},
        {"id":"intelligence","title":"Analyses Gemini et recherche autonome",
         "status":"active" if model_ok else "degraded",
         "detail":"Jusqu'à 4 analyses IA par jour, tests statistiques entre deux appels."},
        {"id":"scenarios","title":"Expériences fictives en rotation","status":"active" if experiment.get("schema")==1 else "pending",
         "detail":str(experiment.get("active",0))+" expériences en cours, jusqu'à 12 simultanées, au maximum 4 nouvelles par cycle."},
        {"id":"hourly","title":"Marchés et backtests horaires","status":"active" if hourly_ok else "degraded",
         "detail":str(oos)+" actifs avec études Kraken 60 minutes et candidat prospectif distinct."},
        {"id":"whales","title":"Surveillance des baleines","status":"partial",
         "detail":"Échantillons de transferts USDC/USDT Ethereum ; identité et achats non vérifiés, couverture non exhaustive."},
        {"id":"changes","title":"Modifications automatiques par robot",
         "status":"testing" if evolution.get("counts",{}).get("testing",0)>0 else "pending",
         "detail":str(evolution.get("counts",{}).get("testing",0))+" profils en test indépendant ; "+
                  str(evolution.get("counts",{}).get("activated",0))+" adopté(s) après validation."},
        {"id":"news","title":"Journal IA, actualités et patchnotes",
         "status":"active" if news.get("status") in ("available","partial") else "degraded",
         "detail":"Sources Fed, BCE et CoinDesk, notes IA distinguées des faits."},
        {"id":"reliability","title":"Surveillance de la fiabilité",
         "status":"active" if actions.get("state")=="available" else "partial",
         "detail":"Dernière exécution terminée de chaque workflow GitHub ; les anciens e-mails ne sont pas de nouvelles pannes."},
        {"id":"real","title":"Trading avec argent réel","status":"disabled",
         "detail":"Aucun courtier relié, aucun ordre réel ; rentabilité reproductible non démontrée."},
    ]
    return {"schema":1,"generated_at":now.isoformat(),
            "status":"needs_attention" if errors else "observing",
            "alerts":errors[:12],"roadmap":roadmap,
            "workflows":actions,
            "gemini_last_state":model.get("state"),
            "paper_experiments_active":experiment.get("active",0),
            "robot_count":robots,"real_orders":False,
            "recommendation":"Les essais restent fictifs ; aucune rentabilité future n'est garantie."}

def main():
    now=datetime.now(timezone.utc)
    pairs={
      "evolution":read("reports/robot_evolution.json"),
      "model":read("reports/ai_research_status.json"),
      "intraday":read("reports/intraday_research.json"),
      "transfers":read("reports/large_transfer_observations.json"),
      "experiments":read("reports/ai_placement_experiments.json"),
      "news":read("reports/market_news.json"),
    }
    result=build(now,pairs,workflows(token=os.environ.get("GITHUB_TOKEN")))
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Operational research health:",result["status"],"warnings",len(result["alerts"]))

if __name__=="__main__":main()
