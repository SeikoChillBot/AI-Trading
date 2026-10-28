"""Small, source-grounded RSS news desk (never an inferred trading signal).

Only article metadata is retained, never full scraped articles. Feed failures
are explicit, news titles are untrusted data and are never instructions.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse
from xml.etree import ElementTree as ET

import requests

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports/market_news.json"
FEEDS = {
    "Fed": ("https://www.federalreserve.gov/feeds/press_monetary.xml",
            "www.federalreserve.gov", "macro"),
    "BCE": ("https://www.ecb.europa.eu/rss/press.html",
            "www.ecb.europa.eu", "macro"),
    "CoinDesk": ("https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml",
                 "www.coindesk.com", "crypto"),
}
MAX_AGE_DAYS = 4
MAX_PER_SOURCE = 4


def clean_text(value, limit=180):
    return re.sub(r"\s+", " ", "".join(ch for ch in str(value or "") if ch.isprintable())).strip()[:limit]


def parse_date(text):
    try:
        result = parsedate_to_datetime(text)
    except (ValueError, TypeError, IndexError):
        result = datetime.fromisoformat(str(text).replace("Z", "+00:00"))
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result.astimezone(timezone.utc)


def parse_feed(xml, source, expected_host, category, now):
    if len(xml) > 700_000:
        raise ValueError("RSS feed oversized")
    root = ET.fromstring(xml)
    results = []
    # RSS 2 and Atom only; no arbitrary XML external entities or HTML.
    items = root.findall(".//item")
    if not items:
        items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
    for item in items[:30]:
        title = clean_text(item.findtext("title") or item.findtext("{http://www.w3.org/2005/Atom}title"))
        link = item.findtext("link")
        if not link:
            anchor = item.find("{http://www.w3.org/2005/Atom}link")
            link = anchor.get("href") if anchor is not None else ""
        date = (item.findtext("pubDate") or item.findtext("published") or
                item.findtext("{http://www.w3.org/2005/Atom}published") or
                item.findtext("{http://www.w3.org/2005/Atom}updated") or "")
        try:
            at = parse_date(date)
        except (ValueError, TypeError, OverflowError):
            continue
        host = urlparse(link)
        if (host.scheme != "https" or host.hostname not in (expected_host, expected_host.removeprefix("www."))
                or not title or not 0 <= (now-at).total_seconds() <= MAX_AGE_DAYS*86400):
            continue
        results.append({
            "id":hashlib.sha256((source+"|"+link).encode()).hexdigest()[:16],
            "source":source, "category":category, "title":title,
            "url":link, "published_at":at.isoformat(),
            "assessment":"unreviewed_source_headline_not_investment_advice",
        })
        if len(results) >= MAX_PER_SOURCE:
            break
    return results


def build(now, get=requests.get):
    report = {"schema":1,"generated_at":now.isoformat(),"source_type":"publisher_rss",
              "status":"available", "articles":[], "source_errors":{},
              "no_auto_trade":True,"editorial_warning":"Publisher titles are unverified signals. Research context only; not a confirmed profitable deal."}
    for source,(feed,hostname,category) in FEEDS.items():
        try:
            response = get(feed,timeout=12,headers={"User-Agent":"SeikoTradingResearch/1.0"})
            response.raise_for_status()
            report["articles"].extend(parse_feed(response.content,source,hostname,category,now))
        except (requests.RequestException,ET.ParseError,ValueError,TypeError) as error:
            report["source_errors"][source] = type(error).__name__ + ": " + str(error)[:100]
    report["articles"].sort(key=lambda x:x["published_at"],reverse=True)
    report["articles"]=report["articles"][:10]
    if len(report["source_errors"]) == len(FEEDS):
        report["status"]="unavailable"
    elif report["source_errors"]:
        report["status"]="partial"
    return report


def main():
    report=build(datetime.now(timezone.utc))
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Source-linked market headlines",len(report["articles"]),report["status"])


if __name__=="__main__":
    main()
