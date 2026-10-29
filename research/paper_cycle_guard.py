"""Avoid double-running scheduled and ChillBot-triggered paper cycles.

Return True for a new cycle when the last committed portfolio update is at
least four minutes old. Invalid or missing state never blocks recovery.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

MIN_GAP_SECONDS = 240

def due(path="state/portfolios.json", now=None, min_gap=MIN_GAP_SECONDS):
    now = now or datetime.now(timezone.utc)
    try:
        value=json.loads(Path(path).read_text(encoding="utf-8"))
        raw=value.get("updated")
        if not isinstance(raw,str):
            return True
        last=datetime.fromisoformat(raw.replace("Z","+00:00"))
        if last.tzinfo is None:
            return True
        age=(now-last).total_seconds()
        return age >= min_gap or age < -60
    except (OSError,ValueError,TypeError,OverflowError):
        return True

def main():
    import os
    ready=due()
    print("Paper cycle "+("due" if ready else "skipped: recent successful snapshot"))
    with open(os.environ["GITHUB_OUTPUT"],"a",encoding="utf-8") as out:
        out.write("run="+("true" if ready else "false")+"\n")

if __name__=="__main__":
    main()
