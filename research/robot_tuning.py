"""Guarded, auditable robot tuning; no arbitrary AI code execution.

Only two bounded entry-signal sensitivity multipliers are supported. HOLD bots
are immutable benchmark controls. Config revisions never reset portfolio state.
"""
from __future__ import annotations
import json
from pathlib import Path

ACTIVE_PATH = Path("state/robot_tuning_active.json")
ALLOWED_SCALES = (0.8, 1.0, 1.2)
TUNABLE_CRYPTO = {
    "btc_momentum", "eth_momentum", "sol_momentum",
    "btc_reversion", "eth_reversion", "sol_reversion",
    "btc_breakout", "btc_rsi", "eth_ema_cross", "sol_bollinger",
    "btc_volatility", "btc_scalp_momentum", "eth_scalp_trailing",
    "sol_scalp_microtrend", "btc_scalp_conservative",
}
MULTI_ASSETS = ("aapl", "msft", "spy", "qqq", "bnd", "gld", "slv", "vnq", "eurusd")
TUNABLE_MULTI = {name+"_trend20" for name in MULTI_ASSETS}
CRYPTO_HOLD = {"btc_hold", "eth_hold", "sol_hold"}
MULTI_HOLD = {name+"_hold" for name in MULTI_ASSETS}
ALL_ROBOTS = TUNABLE_CRYPTO | TUNABLE_MULTI | CRYPTO_HOLD | MULTI_HOLD

def validate_active(value):
    if not isinstance(value, dict) or value.get("schema") != 1:
        return {}
    result = {}
    for name, raw in value.get("profiles", {}).items():
        if name not in TUNABLE_CRYPTO | TUNABLE_MULTI or not isinstance(raw, dict):
            continue
        scale = raw.get("entry_scale")
        if type(scale) in (int, float) and float(scale) in ALLOWED_SCALES:
            if raw.get("source") == "automatic_prospective_validation" and raw.get("approved_at"):
                result[name] = float(scale)
    return result

def active_scales(path=ACTIVE_PATH):
    try:
        return validate_active(json.loads(Path(path).read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return {}

def scale_for(name, profiles):
    return profiles.get(name, 1.0) if name in TUNABLE_CRYPTO | TUNABLE_MULTI else 1.0
