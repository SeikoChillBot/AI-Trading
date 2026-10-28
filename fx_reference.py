"""Display-only USD/EUR conversion, using ECB daily reference rates.

No FX value is used to execute, size, or score simulated trading orders.
The latest validated official reference rate is cached in the repository.
"""
import json
import math
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen
from xml.etree import ElementTree

URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
CACHE = Path("reports/fx_reference.json")
MAX_REFERENCE_AGE_DAYS = 9
REFRESH_HOURS = 3


def validate(reference, now=None):
    if not isinstance(reference, dict):
        return False
    if reference.get("source") != "ECB":
        return False
    try:
        day = date.fromisoformat(reference["reference_date"])
        rate = float(reference["usd_per_eur"])
        today = (now or datetime.now(timezone.utc)).date()
        return math.isfinite(rate) and 0.5 < rate < 3.5 and 0 <= (today - day).days <= MAX_REFERENCE_AGE_DAYS
    except (KeyError, TypeError, ValueError, OverflowError):
        return False


def from_xml(body):
    root = ElementTree.fromstring(body)
    reference_date = None
    rate = None
    for element in root.iter():
        if "time" in element.attrib:
            reference_date = element.attrib["time"]
        if element.attrib.get("currency") == "USD":
            rate = float(element.attrib["rate"])
    result = {
        "source": "ECB",
        "url": URL,
        "reference_date": reference_date,
        "usd_per_eur": rate,
    }
    if not validate(result):
        raise ValueError("ECB response contains no valid recent USD reference rate")
    return result


def load_fx(cache_path=CACHE):
    cached = None
    if cache_path.exists():
        try:
            obj = json.loads(cache_path.read_text(encoding="utf-8"))
            if validate(obj):
                cached = obj
        except (OSError, ValueError):
            pass
    if cached is not None:
        try:
            fetched_at = datetime.fromisoformat(str(cached.get("retrieved_at", "")).replace("Z", "+00:00"))
            age = datetime.now(timezone.utc) - fetched_at
            if timedelta(0) <= age < timedelta(hours=REFRESH_HOURS):
                return cached
        except ValueError:
            pass
    try:
        req = Request(URL, headers={"User-Agent": "SeikoTradingLab/1.0 USD-EUR Display"})
        with urlopen(req, timeout=8) as response:
            payload = response.read(64000)
        fresh = from_xml(payload)
        fresh["retrieved_at"] = datetime.now(timezone.utc).isoformat()
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(fresh, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return fresh
    except (OSError, ValueError, TimeoutError, ElementTree.ParseError) as exc:
        print("ECB FX reference unavailable, using verified cache if available:", exc)
        return cached
