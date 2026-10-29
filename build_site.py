import csv
import json
from pathlib import Path
from datetime import datetime, timezone
from fx_reference import load_fx


def read_csv(path):
    path = Path(path)
    if not path.exists():
        return []
    with path.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


# Keep the 2026-10-28 legacy experiment untouched and visibly separate.
# Display the forward-only, conservative model only after its first complete run.
real_state_path = Path('state/realistic_portfolios.json')
real_report = Path('reports/realistic_latest.csv')
real_history = Path('reports/realistic_history.csv')
real_orders = Path('reports/realistic_orders.csv')
realistic = real_state_path.exists() and real_report.exists() and real_history.exists()
if realistic:
    state = json.loads(real_state_path.read_text(encoding='utf-8'))
    rows = read_csv(real_report)
    history = read_csv(real_history)
    if state.get('version') != 2 or len(rows) != 18 or any(r.get('strategy') is None for r in rows):
        raise RuntimeError('Incomplete realistic simulation: refusing to mix histories')
    data = {
        'model': 'realistic_v2',
        'updated': state['updated'],
        'launched_at': state['created'],
        'rows': rows,
        'history': history,
        'orders': read_csv(real_orders)[-100:],
        'assumptions': state.get('market_assumptions', {}),
    }
else:
    state_path = Path('state/portfolios.json')
    state = json.loads(state_path.read_text(encoding='utf-8')) if state_path.exists() else {}
    data = {
        'model': 'legacy_v1',
        'updated': state.get('updated', datetime.now(timezone.utc).isoformat()),
        'launched_at': '2026-10-28T06:36:00Z',
        'rows': read_csv('reports/latest.csv'),
        'history': read_csv('reports/history.csv'),
        'orders': [],
        'assumptions': {},
    }
# FX is a display-only quotation; it never enters the trading calculations.
data['fx'] = load_fx()
catalog_path = Path('research/market_catalog.json')
catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
required = {'id', 'title', 'family', 'status', 'risk', 'strategies', 'data',
            'execution', 'constraint', 'source', 'examples', 'description'}
allowed_status = {'active', 'connect', 'research', 'high_risk'}
markets = catalog.get('markets', [])
ids = [market.get('id') for market in markets]
if (catalog.get('schema_version') != 1 or len(markets) < 8
        or len(set(ids)) != len(ids) or any(not required.issubset(market) for market in markets)
        or any(market['status'] not in allowed_status for market in markets)
        or any(not market['strategies'] for market in markets)
        or any(not market['source'].startswith('https://') for market in markets)
        or {m['id'] for m in markets if m['status'] == 'active'} != {'crypto'}):
    raise RuntimeError('Unvalidated market catalog, refusing to publish unverified activity')
# Research ideas never participate in simulated balances or performance calculations.
data['market_catalog'] = catalog
# Multi-asset experiment is fully independent: separate capital, orders and history.
multi_state_path = Path("state/multi_asset_micro_portfolios.json")
multi_report_path = Path("reports/multi_asset_micro_latest.csv")
multi_history_path = Path("reports/multi_asset_micro_history.csv")
multi_orders_path = Path("reports/multi_asset_micro_orders.csv")
multi_sources_path = Path("reports/multi_asset_micro_sources.json")
multi = {"ready": False, "rows": [], "history": [], "orders": [],
         "sources": {}, "started_at": None, "updated_at": None,
         "initial_per_strategy_usd": 20}
if multi_state_path.exists() and multi_report_path.exists() and multi_history_path.exists():
    multi_state = json.loads(multi_state_path.read_text(encoding="utf-8"))
    multi_rows = read_csv(multi_report_path)
    keys = [r.get("strategy") for r in multi_rows]
    if (multi_state.get("schema") != 2 or len(multi_rows) != 18
            or len(set(keys)) != 18
            or multi_state.get("initial_per_strategy_usd") != 20):
        raise RuntimeError("Multi-asset state invalid: refuse to publish misleading totals")
    multi = {"ready": True, "rows": multi_rows,
             "history": read_csv(multi_history_path)[-720:],
             "orders": read_csv(multi_orders_path)[-100:],
             "sources": json.loads(multi_sources_path.read_text(encoding="utf-8"))
                 if multi_sources_path.exists() else {},
             "started_at": multi_state["created"], "updated_at": multi_state["updated"],
             "initial_per_strategy_usd": 20,
             "warnings": multi_state.get("feed_notes", {})}
data["multi_asset"] = multi
research_file = Path("reports/autonomous_research.json")
research_status = Path("reports/ai_research_status.json")
data["research"] = {"ready": False}
if research_file.exists():
    item = json.loads(research_file.read_text(encoding="utf-8"))
    if item.get("schema") == 1 and item.get("kind") == "deterministic_statistical_research":
        data["research"] = {
            "ready": True, "generated_at": item.get("generated_at"),
            "qualification": item.get("qualification", {}),
            "labs": {k: {"count": v.get("count"), "eligible": v.get("eligible"),
                         "elapsed_days": v.get("elapsed_days")}
                     for k, v in item.get("labs", {}).items()},
            "hypotheses": item.get("hypotheses", [])[:6],
            "market_intelligence": item.get("market_intelligence", {}),
            "ai_status": json.loads(research_status.read_text()) if research_status.exists() else {},
            "auto_changes": False
        }
walk_path = Path("reports/challenger_walkforward.json")
data["challenger_optimization"] = {"ready": False}
if walk_path.exists():
    record = json.loads(walk_path.read_text(encoding="utf-8"))
    if record.get("schema") == 1 and record.get("model") == "kraken_daily_walkforward_v1":
        data["challenger_optimization"] = {
            "ready": True, "generated_at": record.get("generated_at"),
            "historical_only": True, "orders_real": False,
            "instruments": [
                {"asset": asset, "bars": info.get("bars", 0),
                 "folds": info.get("fold_count", 0),
                 "oos_return": info.get("average_oos_return_pct"),
                 "oos_excess": info.get("average_oos_excess_vs_hold_points"),
                 "stress_return": info.get("average_oos_return_double_cost_pct"),
                 "worst_drawdown": info.get("max_oos_drawdown_pct"),
                 "parameters": info.get("candidate_parameters", {}),
                 "status": info.get("status", "research_only")}
                for asset, info in record.get("instruments", {}).items()
            ],
            "errors": record.get("issues", {})
        }
# Machine-readable, non-executable research proposals only (never portfolio inputs).
ai_proposals_path = Path("reports/ai_research_proposals.json")
data["ai_review"] = {"ready": False}
if ai_proposals_path.exists():
    try:
        advisory = json.loads(ai_proposals_path.read_text(encoding="utf-8"))
        if (advisory.get("schema") == 1
                and not advisory.get("real_orders_enabled", True)
                and not advisory.get("live_strategy_changes_enabled", True)):
            data["ai_review"] = {
                "ready": True, "state": advisory.get("state", "not_configured"),
                "source": advisory.get("source", "deterministic_fallback"),
                "summary": str(advisory.get("summary", ""))[:1000],
                "experiments": advisory.get("experiments", [])[:3],
                # These are untested signal-threshold hypotheses, NOT changes
                # to portfolio size or instructions that AI can execute.
                "bot_adjustments": [
                    {"strategy":candidate.get("strategy"),
                     "entry_scale":candidate.get("entry_scale"),
                     "reason":str(candidate.get("reason", ""))[:240],
                     "evidence_state":"gemini_hypothesis_unverified"}
                    for candidate in advisory.get("bot_adjustments", [])[:3]
                    if isinstance(candidate, dict)
                    and candidate.get("strategy") in {
                        "btc_momentum","eth_momentum","sol_momentum",
                        "btc_reversion","eth_reversion","sol_reversion",
                        "btc_breakout","btc_rsi","eth_ema_cross",
                        "sol_bollinger","btc_volatility",
                        "btc_scalp_momentum","eth_scalp_trailing",
                        "sol_scalp_microtrend","btc_scalp_conservative",
                        "aapl_trend20","msft_trend20","spy_trend20",
                        "qqq_trend20","bnd_trend20","gld_trend20",
                        "slv_trend20","vnq_trend20","eurusd_trend20"
                    } and type(candidate.get("entry_scale")) in (int,float)
                    and candidate.get("entry_scale") in (0.8,1.2)
                    and advisory.get("source")=="gemini_generate_content"
                    and advisory.get("state")=="model_reflection_completed"
                ],
                "historical": {
                    "status": advisory.get("historical", {}).get("status"),
                    "assets": advisory.get("historical", {}).get("assets", [])[:3],
                },
                "validated": False,
            }
    except (ValueError, TypeError, KeyError):
        pass
# Read-only radar of SAMPLE transfers, never balances or verified trades.
data["whale_radar"] = {"ready": False, "state": "unknown"}
radar_file = Path("reports/large_transfer_observations.json")
if radar_file.exists():
    try:
        radar = json.loads(radar_file.read_text(encoding="utf-8"))
        if radar.get("schema") == 1 and radar.get("real_trades") is False:
            valid = []
            for row in radar.get("sampled_wallet_flows", [])[:10]:
                if not isinstance(row, dict):
                    continue
                address = row.get("address")
                if not isinstance(address, str) or len(address) != 42 or not address.startswith("0x"):
                    continue
                if not all(ch in "0123456789abcdef" for ch in address[2:]):
                    continue
                valid.append({key: row.get(key) for key in (
                    "address", "incoming_nominal_usd", "outgoing_nominal_usd",
                    "sample_net_nominal_usd", "sample_observations", "tokens",
                    "identity_verified", "trade_inference")})
            highlights = []
            for row in radar.get("sample_highlights", [])[:6]:
                if not isinstance(row, dict):
                    continue
                tx = row.get("tx_hash", "")
                if not isinstance(tx, str) or len(tx) != 66 or not tx.startswith("0x") or not all(ch in "0123456789abcdef" for ch in tx[2:]):
                    continue
                highlights.append({key:row.get(key) for key in (
                    "token", "quantity", "nominal_usd_approx", "timestamp", "tx_hash",
                    "classification", "owner_identity", "trade_inference")})
            data["whale_radar"] = {
                "ready": (radar.get("state") in ("observing", "partial")
                           and isinstance(radar.get("sampled_wallet_flows"), list)
                           and isinstance(radar.get("sampled_wallets_count"), int)),
                "generated_at":radar.get("generated_at"),
                "state":radar.get("state"),
                "source":radar.get("source"),
                "sampled_records":radar.get("sampled_records", {}),
                "validated_records":radar.get("validated_records", {}),
                "large_transfers_observed":radar.get("large_transfers_observed", 0),
                "new_event_count":radar.get("new_event_count", 0),
                "sampled_wallets_count":radar.get("sampled_wallets_count", 0),
                "sampled_wallet_flows":valid,
                "sample_highlights":highlights,
                "errors":radar.get("errors", {}),
                "not_exhaustive":True, "verified_wallet_identities":False,
                "verified_buy_sell":False,
            }
    except (OSError, ValueError, TypeError):
        pass

# Independently tracked addresses: baseline first; no ownership or trade inference.
follow_file = Path("reports/whale_follow.json")
if follow_file.exists():
    try:
        follow = json.loads(follow_file.read_text(encoding="utf-8"))
        if follow.get("schema") == 1 and follow.get("real_orders") is False:
            data["whale_radar"]["follow"] = {
                "state":follow.get("state"),
                "generated_at":follow.get("generated_at"),
                "coverage":follow.get("coverage"),
                "tracked_addresses":[{k:row.get(k) for k in (
                    "address","verified_identity","sample_count","new_count","baseline_at",
                    "last_polled_at","monitoring")}
                    for row in follow.get("tracked_addresses",[])[:4] if isinstance(row,dict)],
                "new_transfers":[{k:row.get(k) for k in (
                    "tx_hash","token","nominal_usd_approx","timestamp",
                    "classification","trade_inference")}
                    for row in follow.get("new_transfers",[])[:8] if isinstance(row,dict)],
                "error_count":len(follow.get("errors",{})),
                "can_infer_trade":False, "can_infer_owner":False,
            }
    except (OSError,ValueError,TypeError):
        pass

# Separate public Base/USDC transfer sample; not verified exchange activity.
data["base_radar"]={"ready":False}
base_file=Path("reports/base_usdc_observations.json")
if base_file.exists():
    try:
        item=json.loads(base_file.read_text(encoding="utf-8"))
        if item.get("schema")==1 and item.get("real_orders") is False and item.get("chain")=="base":
            data["base_radar"]={"ready":item.get("state")=="observing",
                "state":item.get("state"),"generated_at":item.get("generated_at"),
                "sampled_count":item.get("sampled_count",0),
                "large_count":item.get("large_count",0),
                "highlights":item.get("highlights",[])[:4],
                "source_method":item.get("source_method"),
                "coverage":item.get("coverage"),
                "sampled_blocks":item.get("sampled_blocks"),
                "not_exhaustive":True,"verified_trades":False}
    except (OSError,ValueError,TypeError):
        pass

# Report-only widgets for new market studies and forward-only challengers.
data["market_pulse"] = {"ready": False}
pulse_path = Path("reports/market_pulse.json")
if pulse_path.exists():
    try:
        pulse = json.loads(pulse_path.read_text(encoding="utf-8"))
        if pulse.get("schema") == 1 and pulse.get("real_orders") is False:
            data["market_pulse"] = {
                "ready": True, "generated_at": pulse.get("generated_at"),
                "assets": {k: {
                    attr: entry.get(attr) for attr in (
                        "change_1d_pct", "change_7d_pct", "change_30d_pct",
                        "realized_volatility_30d_annualized_pct", "last_closed_day_utc")}
                    for k, entry in pulse.get("assets", {}).items()
                    if k in ("BTCUSD", "ETHUSD", "SOLUSD") and isinstance(entry, dict)},
                "macro": pulse.get("macro", {}),
                "large_transfers": pulse.get("large_transfers", {}),
                "issues": pulse.get("issues", {}),
            }
    except (ValueError, KeyError, TypeError):
        pass
data["forward_challengers"] = {"ready": False}
incubator_path = Path("reports/challenger_incubator.json")
if incubator_path.exists():
    try:
        forward = json.loads(incubator_path.read_text(encoding="utf-8"))
        if (forward.get("schema") == 1 and not forward.get("real_orders", True)
                and not forward.get("automatic_promotion", True)):
            data["forward_challengers"] = {
                "ready": True, "generated_at": forward.get("generated_at"),
                "assets": {k: {
                    attr: entry.get(attr) for attr in (
                        "version", "created_at", "status", "parameters",
                        "observations", "net_return_pct", "equity_usd",
                        "hold_equity_usd", "closed_trades", "worst_drawdown_pct",
                        "ready_for_review")}
                    for k, entry in forward.get("assets", {}).items()
                    if k in ("BTCUSD", "ETHUSD", "SOLUSD") and isinstance(entry, dict)},
                "errors": forward.get("errors", {}),
                "historical_bots_unchanged": True,
            }
    except (ValueError, KeyError, TypeError):
        pass
# Per-robot audit and autonomous, validated tuning: never portfolio input.
evolution_path = Path("reports/robot_evolution.json")
evolution_history = Path("reports/robot_evolution_events.jsonl")
data["robot_evolution"] = {"ready": False}
if evolution_path.exists():
    try:
        evolution = json.loads(evolution_path.read_text(encoding="utf-8"))
        if (evolution.get("schema") == 1
                and evolution.get("model") == "per_robot_review_and_guarded_paper_evolution_v1"
                and evolution.get("real_orders") is False
                and evolution.get("llm_generated_code_executed") is False):
            bots = [
                {field: r.get(field) for field in (
                    "strategy", "lab", "asset", "role", "status",
                    "current_entry_scale", "proposed_entry_scale", "proposed_at",
                    "gemini_decision", "decision_source", "blocked_checks", "validation_progress", "paper_return_pct",
                    "drawdown_pct", "closed_roundtrips", "samples",
                    "ready_for_review", "last_change_at"
                )} for r in evolution.get("robots", [])
                if isinstance(r, dict) and isinstance(r.get("strategy"), str)
            ]
            history = []
            if evolution_history.exists():
                for line in evolution_history.read_text(encoding="utf-8").splitlines()[-120:]:
                    try:
                        event = json.loads(line)
                        if isinstance(event, dict) and event.get("robot"):
                            history.append({k:event.get(k) for k in (
                                "at","robot","action","from_scale","to_scale","details")})
                    except (ValueError, TypeError):
                        continue
            data["robot_evolution"] = {
                "ready":len(bots)==36, "generated_at":evolution.get("generated_at"),
                "counts":evolution.get("counts", {}), "robots":bots[:36],
                "events":history[-40:][::-1], "real_orders":False,
            }
    except (ValueError, KeyError, TypeError):
        pass
# Gemini notes and external headlines never enter portfolio calculations.
desk_path = Path("reports/ai_journal.json")
data["gemini_desk"] = {"ready": False}
if desk_path.exists():
    try:
        desk = json.loads(desk_path.read_text(encoding="utf-8"))
        if desk.get("schema") == 1 and desk.get("real_trades") is False:
            data["gemini_desk"] = {
                "ready": True, "generated_at": desk.get("generated_at"),
                "model": desk.get("model"), "model_status": desk.get("model_status"),
                "last_ai_call": desk.get("last_ai_call"),
                "source_health": desk.get("source_health"),
                "entries": [
                    {k: item.get(k) for k in ("type","at","title","details","link")}
                    for item in desk.get("entries", [])[:35] if isinstance(item, dict)
                ],
                "experiments": [
                    {k: trial.get(k) for k in
                     ("id","asset","trigger","actor","status","horizon_days","created_at",
                      "estimated_net_pct","equity_usd","rationale")}
                    for trial in desk.get("paper_experiments", [])[:12]
                    if isinstance(trial, dict) and trial.get("paper_only") is True
                ],
                "stats": desk.get("robot_statistics", {}),
                "market_watch": [
                    {k:item.get(k) for k in (
                        "asset","move_7d_pct","annualized_volatility_30d_pct",
                        "label","source","source_at","verified_opportunity","buy_signal")}
                    for item in desk.get("market_watch",[])[:3]
                    if isinstance(item,dict) and item.get("buy_signal") is False
                ],
                "real_trades": False,
            }
    except (ValueError, KeyError, TypeError):
        pass
# Dated Gemini/quantitative journal: only source-backed daily summaries.
brief_path = Path("reports/ai_daily_brief.json")
data["gemini_desk"]["daily_briefs"] = []
if brief_path.exists():
    try:
        brief = json.loads(brief_path.read_text(encoding="utf-8"))
        if (brief.get("schema") == 1 and brief.get("real_orders") is False
                and brief.get("model_authorship_must_be_verified") is True):
            days = brief.get("days", [])
            data["gemini_desk"]["daily_briefs"] = [
                {field: day.get(field) for field in (
                    "date", "updated_at", "period", "headline", "source",
                    "gemini_authored_summary", "gemini_status", "research",
                    "decisions", "conclusions", "next", "counts"
                )}
                for day in days[:14] if isinstance(day, dict)
                and day.get("real_orders") is False
            ]
    except (ValueError, TypeError, KeyError):
        pass
# Read-only intraday research and transparent operational capability roadmap.
intraday_path=Path("reports/intraday_research.json")
data["intraday_study"]={"ready":False}
if intraday_path.exists():
    try:
        hourly=json.loads(intraday_path.read_text(encoding="utf-8"))
        if hourly.get("schema")==1 and hourly.get("real_orders") is False:
            data["intraday_study"]={
                "ready":hourly.get("status") in ("available","partial"),
                "generated_at":hourly.get("generated_at"),
                "status":hourly.get("status"),
                "assets":{symbol:{
                    "last_closed_hour_utc":item.get("last_closed_hour_utc"),
                    "historical_study":{key:item.get("historical_study",{}).get(key)
                      for key in ("avg_net_return_pct","avg_excess_vs_hold",
                                  "max_drawdown_pct","proven_profitable")},
                    "paper_forward":{k:item.get("paper_forward",{}).get(k)
                      for k in ("observations","capital_usd","net_return_pct",
                                "closed_trades","max_drawdown_pct","status","created_at")}
                } for symbol,item in hourly.get("assets",{}).items()
                  if symbol in ("BTCUSD","ETHUSD","SOLUSD") and isinstance(item,dict)},
                "errors":hourly.get("errors",{}),
                "real_orders":False,
            }
    except (ValueError,TypeError,KeyError):
        pass
health_path=Path("reports/system_health.json")
data["operations"]={"ready":False}
if health_path.exists():
    try:
        health=json.loads(health_path.read_text(encoding="utf-8"))
        if health.get("schema")==1 and health.get("real_orders") is False:
            data["operations"]={
                "ready":True,"generated_at":health.get("generated_at"),
                "status":health.get("status"),"alerts":health.get("alerts",[])[:12],
                "roadmap":[{k:item.get(k) for k in ("id","title","status","detail")}
                    for item in health.get("roadmap",[])[:12] if isinstance(item,dict)],
                "workflows":health.get("workflows",{}).get("workflows",{}),
                "real_orders":False,
            }
    except (ValueError,TypeError,KeyError):
        pass
rows = data['rows']
history = data['history']
template = Path('site/index.html').read_text(encoding='utf-8')
optional = {
    '/*__CSS__*/': Path('site/theme.css').read_text(encoding='utf-8'),
    '/*__JS__*/': Path('site/app.js').read_text(encoding='utf-8'),
}
for marker, replacement in optional.items():
    if marker in template:
        template = template.replace(marker, replacement)
marker = '/*__DATA__*/{"updated":"En attente du premier relevé","rows":[],"history":[]}'
if template.count(marker) != 1:
    raise RuntimeError('Dashboard template marker missing or duplicated')
safe_json = json.dumps(data, ensure_ascii=False).replace('<', '\\u003c')
template = template.replace(marker, safe_json)
Path('site/dashboard.html').write_text(template, encoding='utf-8')
print('Generated site/dashboard.html with', len(rows), 'portfolios and', len(history), 'history points')
