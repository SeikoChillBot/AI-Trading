"""Bounded, conflict-only recovery for research reports on current main.

This is deliberately not a git merge tool. When generated state collides with a
newer publisher, keep the failed run failed and request one fresh full research
cycle. Never force-push or choose a version of scientific/paper state blindly.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

REPOSITORY = "SeikoChillBot/AI-Trading"
WORKFLOW = "research.yml"
RUNS_URL = f"https://api.github.com/repos/{REPOSITORY}/actions/workflows/{WORKFLOW}/runs"
RETRY_WINDOW = timedelta(hours=2)


def _timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else None
    except ValueError:
        return None


def should_recover(rows: Any, current_id: int, now: datetime) -> bool:
    """Fail closed unless this is one failed original run with no newer work.

    The caller is only reached following a *publication conflict*, not an
    arbitrary test, Gemini, network, or trading-simulator failure.
    """
    if not isinstance(rows, list) or not rows or len(rows) >= 100:
        return False
    if not all(isinstance(row, dict) and _timestamp(row.get("created_at"))
               and (row.get("path") or "").endswith("/research.yml")
               for row in rows):
        return False
    current = next((r for r in rows if r.get("id") == current_id), None)
    if current is None or current.get("event") not in ("schedule", "push"):
        # workflow_dispatch retries never recursively dispatch themselves.
        return False
    current_at = _timestamp(current.get("created_at"))
    if current_at is None or not timedelta(0) <= now - current_at <= RETRY_WINDOW:
        return False
    for row in rows:
        if row.get("id") == current_id:
            continue
        created = _timestamp(row.get("created_at"))
        if created is None:
            return False
        # Another, newer attempt (even if it failed) owns recovery.
        if created >= current_at:
            return False
        # Existing manual / automatic dispatch in the recent window is
        # treated as a retry already in flight; never create a retry storm.
        if row.get("event") == "workflow_dispatch" and now - created <= RETRY_WINDOW:
            return False
    return True


def recover(*, get=requests.get, post=requests.post) -> str:
    if os.environ.get("GITHUB_REPOSITORY") != REPOSITORY:
        return "skipped: unexpected repository"
    if os.environ.get("GITHUB_EVENT_NAME") not in ("schedule", "push"):
        return "skipped: no recursive workflow_dispatch recovery"
    token = os.environ.get("GH_TOKEN")
    try:
        current_id = int(os.environ.get("GITHUB_RUN_ID", ""))
    except ValueError:
        return "skipped: missing run identity"
    if not token or current_id <= 0:
        return "skipped: token or run identity unavailable"
    headers = {
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "AIT-Safe-Publication-Recovery",
    }
    try:
        response = get(RUNS_URL, params={"per_page": 100},
                       headers=headers, timeout=15)
        response.raise_for_status()
        body = response.json()
        if not isinstance(body, dict) or not should_recover(
                body.get("workflow_runs"), current_id, datetime.now(timezone.utc)):
            return "skipped: newer run, prior retry, or insufficient evidence"
        dispatched = post(
            f"https://api.github.com/repos/{REPOSITORY}/actions/workflows/{WORKFLOW}/dispatches",
            json={"ref": "main"}, headers=headers, timeout=15,
        )
        dispatched.raise_for_status()
        if dispatched.status_code not in (200, 201, 202, 204):
            return "skipped: unexpected dispatch response"
        return "dispatched: one fresh research cycle from current main"
    except (requests.RequestException, ValueError, TypeError):
        return "skipped: GitHub API unavailable; no unsafe fallback"


if __name__ == "__main__":
    print("AIT publication recovery:", recover())
