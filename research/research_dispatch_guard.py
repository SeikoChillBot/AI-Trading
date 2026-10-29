"""Bounded GitHub Actions research watchdog triggered from healthy paper runs.

GitHub cron is best-effort, not guaranteed. If recent research has not been
queued or run, send ONE workflow_dispatch using the existing GitHub Actions
token. Never infer an outage from historical failed runs; avoid double runs.
Failure to read GitHub API does not dispatch blindly and cannot stop paper trading.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional
import requests

OWNER_REPO = "SeikoChillBot/AI-Trading"
ROOT_API = "https://api.github.com/repos/" + OWNER_REPO + "/actions"
API = ROOT_API + "/workflows/research.yml"
RUNS_API = ROOT_API + "/runs"
RESEARCH_NAME = "Seiko research — guarded automatic analysis"
MAX_AGE_SECONDS = 165 * 60  # research normally every 120 minutes, with GitHub cron jitter
RECOVERY_WAIT_SECONDS = 8 * 60  # failed run; wait for source correction to land


def parse_utc(value: object) -> Optional[datetime]:
    if not isinstance(value, str):
        return None
    try:
        t = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return t.astimezone(timezone.utc) if t.tzinfo else None
    except ValueError:
        return None


def is_research(row: object) -> bool:
    if not isinstance(row, dict):
        return False
    name = row.get("name")
    path = row.get("path")
    return name == RESEARCH_NAME or (
        isinstance(path, str) and ".github/workflows/research.yml" in path
    )


def should_dispatch(now: datetime, rows: object) -> bool:
    """Require enough overall Actions history to rule out a recent research run."""
    if not isinstance(rows, list) or not rows:
        return False
    candidates = [row for row in rows if isinstance(row, dict)]
    # GitHub returns recent runs sorted newest-first but we inspect timestamps
    # rather than trusting order. For a full page of 100 runs, history must
    # reach BEYOND the freshness threshold to prove no recent research was lost
    # to pagination (notably when Pages builds are frequent).
    timestamps = [parse_utc(row.get("created_at")) for row in candidates]
    timestamps = [t for t in timestamps if t is not None]
    if not timestamps:
        return False
    oldest = min(timestamps)
    if len(candidates) >= 100 and (now - oldest).total_seconds() < MAX_AGE_SECONDS:
        return False
    research = [row for row in candidates if is_research(row)
                and row.get("event") in ("schedule", "workflow_dispatch")]
    recent=[]
    for row in research:
        created = parse_utc(row.get("created_at"))
        if created is not None and -60 <= (now-created).total_seconds() < MAX_AGE_SECONDS:
            recent.append((created,row))
    if recent:
        recent.sort(key=lambda p:p[0],reverse=True)
        latest_t,latest=recent[0]
        failures=[r for _,r in recent
                  if r.get("status")=="completed" and r.get("conclusion")=="failure"]
        # Exactly one recent failed run may be re-dispatched once after
        # a cooling-off period. A second failed run suppresses repeated
        # retries until the ordinary stale-cycle threshold. Do not retry
        # queued, running, successful or unknown-conclusion executions.
        if (len(failures)==1 and len(recent)==1
                and latest.get("status")=="completed"
                and latest.get("conclusion")=="failure"
                and (now-latest_t).total_seconds()>=RECOVERY_WAIT_SECONDS):
            return True
        return False
    return True


def check_and_dispatch(now: Optional[datetime] = None, token: Optional[str] = None,
                       get=requests.get, post=requests.post) -> str:
    now = now or datetime.now(timezone.utc)
    token = token if token is not None else os.environ.get("GH_TOKEN", "")
    if not token or os.environ.get("GITHUB_REPOSITORY") != OWNER_REPO:
        return "skipped: token missing or unexpected repository"
    headers = {
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "AIT-Research-Cron-Recovery",
    }
    try:
        reply = get(RUNS_API, headers=headers,
                    params={"per_page": 100}, timeout=15)
        reply.raise_for_status()
        data = reply.json()
        if not isinstance(data, dict) or not isinstance(data.get("workflow_runs"), list):
            return "skipped: invalid workflow history"
        rows = data["workflow_runs"]
        if not should_dispatch(now, rows):
            return "skipped: recent research run or insufficient Actions history"
        # Guard against accidental repeat dispatches based on the run created
        # during the same window; do not dispatch without confirmed API history.
        result = post(API + "/dispatches", headers=headers,
                      json={"ref": "main"}, timeout=12)
        result.raise_for_status()
        if result.status_code not in (200, 201, 202, 204):
            return "warning: unexpected GitHub dispatch response"
        return "dispatched: recovery research workflow_dispatch"
    except (requests.RequestException, ValueError, TypeError):
        return "skipped: GitHub API unavailable; leave cron and paper intact"


def main() -> None:
    # Avoid exposing tokens or JSON HTTP responses in CI logs.
    print("AIT research watchdog:", check_and_dispatch())


if __name__ == "__main__":
    main()
