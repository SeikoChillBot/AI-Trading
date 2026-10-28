"""Public, sampled large stablecoin transfer observations (not wallet identities).

No private API key, no assumed buy/sell, no trading actions. The explorer API
only returns a capped sample, not an exhaustive feed. Partial failure is explicit.
"""
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports/large_transfer_observations.json"
STATE = ROOT / "state/large_transfer_cursor.json"
HOST = "https://eth.blockscout.com/api/v2"
CONTRACTS = {
    "USDC": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    "USDT": "0xdac17f958d2ee523a2206206994597c13d831ec7",
}
MIN_UNITS = Decimal("1000000")
MAX_RECORDS = 50


def read(path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return fallback


def transfer(raw, token, now):
    """Validate contract, quantity, timing, source identity and transaction hash."""
    if not isinstance(raw, dict):
        raise ValueError("Invalid transfer")
    meta = raw.get("token", {})
    if not isinstance(meta, dict) or str(meta.get("address_hash", "")).lower() != CONTRACTS[token]:
        raise ValueError("Unexpected contract")
    amount = raw.get("total", {})
    if not isinstance(amount, dict):
        raise ValueError("Transfer amount missing")
    decimals = int(amount["decimals"])
    if decimals != 6:
        raise ValueError("Unexpected stablecoin decimals")
    units = Decimal(str(amount["value"])) / (Decimal(10) ** decimals)
    if not units.is_finite() or units <= 0:
        raise ValueError("Invalid transfer size")
    dt = datetime.fromisoformat(raw["timestamp"].replace("Z", "+00:00"))
    if dt.tzinfo is None or not 0 <= (now - dt).total_seconds() <= 86400:
        raise ValueError("Transfer outside a bounded fresh period")
    tx = str(raw.get("transaction_hash") or raw.get("tx_hash") or "").lower()
    if len(tx) != 66 or not tx.startswith("0x") or any(x not in "0123456789abcdef" for x in tx[2:]):
        raise ValueError("Invalid transaction hash")
    sender = str((raw.get("from") or {}).get("hash", "")).lower()
    receiver = str((raw.get("to") or {}).get("hash", "")).lower()
    if len(sender) != 42 or len(receiver) != 42:
        raise ValueError("Invalid transfer endpoints")
    # Stablecoin notional is not executable USD value: depegs and token restrictions.
    marker = str(raw.get("log_index") or raw.get("index") or "")
    identity = hashlib.sha256("|".join([tx, marker, token, sender, receiver, str(units)]).encode()).hexdigest()
    return {
        "id": identity, "token": token, "quantity": str(units),
        "nominal_usd_approx": float(units),
        "timestamp": dt.isoformat(),
        "tx_hash": tx,
        "from_address": sender, "to_address": receiver,
        "classification": "PUBLIC_STABLECOIN_TRANSFER_NOT_VERIFIED_TRADE",
        "owner_identity": "unknown", "trade_inference": "unknown",
    }


def build(now, state, get=requests.get):
    seen = set(state.get("seen_ids", [])) if isinstance(state, dict) else set()
    first = not bool(state.get("initialized")) if isinstance(state, dict) else True
    output = {
        "schema": 1, "generated_at": now.isoformat(),
        "source": HOST, "chain": "ethereum",
        "state": "observing", "method": "sample_latest_public_token_transfers",
        "coverage": "NOT_EXHAUSTIVE_first_page_only_per_contract",
        "minimum_nominal_usd": int(MIN_UNITS),
        "sampled_records": {}, "validated_records": {}, "large_transfers_observed": 0,
        "large_transfers_new": [], "sample_highlights": [],
        "errors": {}, "buy_sell_inference": False, "real_trades": False,
        "warning": "Large stablecoin transfers may be exchange movements, mint/redemption, custody or bridges; not proof of a whale purchase.",
    }
    observed = set()
    examples = []
    for token, contract in CONTRACTS.items():
        try:
            response = get(HOST + "/tokens/" + contract + "/transfers",
                           timeout=12, headers={"User-Agent": "SeikoResearch/1.0"})
            response.raise_for_status()
            body = response.json()
            items = body.get("items")
            if not isinstance(items, list) or len(items) > MAX_RECORDS:
                raise ValueError("Unexpected token transfer page")
            output["sampled_records"][token] = len(items)
            output["validated_records"][token] = 0
            for raw in items:
                try:
                    item = transfer(raw, token, now)
                except (KeyError, TypeError, ValueError, InvalidOperation):
                    continue
                output["validated_records"][token] += 1
                observed.add(item["id"])
                if Decimal(item["quantity"]) >= MIN_UNITS:
                    examples.append(item)
            if items and output["validated_records"][token] == 0:
                raise ValueError("No transfers decoded; source response incompatible")
        except (ValueError, TypeError, KeyError, requests.RequestException) as error:
            output["errors"][token] = type(error).__name__ + ": " + str(error)[:130]
    # Do not call observations "new" on the initial polling run.
    output["large_transfers_observed"] = len(examples)
    output["sample_highlights"] = sorted(examples, key=lambda x: x["nominal_usd_approx"], reverse=True)[:4]
    if not first:
        output["large_transfers_new"] = [x for x in examples if x["id"] not in seen][:8]
    if len(output["errors"]) == len(CONTRACTS):
        output["state"] = "unavailable"
    elif output["errors"]:
        output["state"] = "partial"
    if output["state"] == "unavailable":
        return output, state
    new_state = {
        "schema": 1, "initialized": True, "seen_ids": list((observed | seen))[-400:],
        "updated_at": now.isoformat(),
    }
    return output, new_state


def main():
    now = datetime.now(timezone.utc)
    report, state = build(now, read(STATE, {}))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if report["state"] != "unavailable":
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    print("Public large-transfer sample", report["state"],
          "new sampled observations:", len(report["large_transfers_new"]))


if __name__ == "__main__":
    main()
