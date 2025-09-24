# ===================================
# jira_api.py – Jira API Integration
# ===================================

import os
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timezone

# ====================
# AUTH & CONFIGURATION
# ====================

from dotenv import load_dotenv
load_dotenv(override=True)   # load variables once at import

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
EMAIL = os.getenv("JIRA_EMAIL")

if not JIRA_BASE_URL:
    raise ValueError("JIRA_BASE_URL not found in environment.")
if not EMAIL:
    raise ValueError("JIRA_EMAIL not found in environment.")

# === AUTH HELPER ===
def get_auth():
    """
    Load the latest Jira API token from the environment at runtime.
    Ensures token refreshes without restarting Jupyter.
    """
    token = os.getenv("JIRA_API_TOKEN")
    if not token:
        raise ValueError("JIRA_API_TOKEN not found in environment.")
    return HTTPBasicAuth(EMAIL, token)

# === RESILIENCE: New JQL search API (cursor pagination) ===
# Jira removed the old search endpoints. The supported path is:
#   POST /rest/api/3/search/jql
# It uses a nextPageToken cursor (NOT startAt) and returns isLast/nextPageToken.
# Ref: Atlassian REST v3 "Issue search" > "Search for issues using JQL enhanced search" docs.
# === RESILIENCE: New JQL search API (cursor pagination) ===
def _search_jql(jql: str, max_results: int, next_page_token: str | None, fields, expand=None):
    """
    Perform a Jira search using the enhanced JQL endpoint with cursor pagination.

    Parameters:
        jql (str): JQL string.
        max_results (int): Page size.
        next_page_token (str|None): Cursor from previous page (None for first page).
        fields (list[str] | str): Fields to return.
        expand (list[str] | str | None): Optional expansions (e.g., "changelog").

    Returns:
        dict: JSON response from Jira (contains issues, isLast, nextPageToken, ...).
    """
    url = f"{JIRA_BASE_URL}/rest/api/3/search/jql"
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    # Normalize fields to a list
    if isinstance(fields, str):
        fields_list = [f.strip() for f in fields.split(",") if f.strip()]
    else:
        fields_list = list(fields or [])

    # ✅ Normalize expand to a comma-separated string (API expects string)
    #    e.g. ["changelog", "names"] -> "changelog,names"
    expand_str = None
    if expand:
        if isinstance(expand, (list, tuple)):
            expand_str = ",".join([e.strip() for e in expand if e and str(e).strip()])
        else:
            expand_str = str(expand).strip()

    payload = {
        "jql": jql,
        "maxResults": max_results,
        "fields": fields_list
    }
    if expand_str:
        payload["expand"] = expand_str
    if next_page_token:
        payload["nextPageToken"] = next_page_token  # cursor pagination

    resp = requests.post(url, headers=headers, auth=get_auth(), json=payload)
    if not resp.ok:
        # Surface server message to pinpoint bad parameter/field quickly
        raise requests.HTTPError(f"{resp.status_code} for {resp.url}\n{resp.text}")
    return resp.json()

# ======================
# GENERIC ISSUE FETCHING
# ======================

def fetch_issues(jql, max_results=100, start_at=0):
    """
    Execute a JQL query against Jira and return results.

    Parameters:
        jql (str): The Jira Query Language string.
        max_results (int): Page size (default 100).
        start_at (int): (Ignored with enhanced search; kept for API compatibility.)

    Returns:
        dict: JSON response with a combined 'issues' list (single page shape for callers).

    Resilience:
        - Uses POST /rest/api/3/search/jql with cursor pagination (nextPageToken).
    """
    all_issues = []
    token = None
    while True:
        result = _search_jql(
            jql=jql,
            max_results=max_results,
            next_page_token=token,
            fields=["summary", "status", "created", "updated", "resolutiondate", "assignee", "customfield_10239", "parent"]
        )
        batch = result.get("issues", [])
        all_issues.extend(batch)

        # Cursor handling
        if result.get("isLast") or not result.get("nextPageToken"):
            break
        token = result.get("nextPageToken")

    # Preserve prior return shape for callers expecting a dict with 'issues'
    return {"issues": all_issues}

# ===========================
# WIP ISSUE FETCHING (Changelog Required)
# ===========================

def get_wip_issues(project_key, days=30):
    """
    Retrieve issues that are currently in progress or were in progress
    during the past N days. This includes changelog data for WIP tracking.

    Parameters:
        project_key (str): Jira project key (e.g. 'ITNET')
        days (int): Lookback window in days (default 30)

    Returns:
        list: List of issue dictionaries with changelogs

    Resilience:
        - Uses POST /rest/api/3/search/jql with expand=["changelog"] and cursor pagination.
    """
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=days)
    start_str = start_date.strftime('%Y-%m-%d')

    jql = (
        f'project = {project_key} AND '
        f'(status = "In Progress" OR status WAS "In Progress" AFTER "{start_str}") '
        f'AND issuetype != Epic ORDER BY created DESC'
    )

    issues = []
    token = None
    batch_size = 100
    while True:
        result = _search_jql(
            jql=jql,
            max_results=batch_size,
            next_page_token=token,
            fields=["summary", "status", "created", "resolutiondate"],  # minimal + safe
            expand=["changelog"]  # required for WIP ranges
        )
        batch = result.get("issues", [])
        issues.extend(batch)

        if result.get("isLast") or not result.get("nextPageToken"):
            break
        token = result.get("nextPageToken")

    return issues

# ================================
# STANDARD: LAST N MONTHS OF DONE
# ================================

def get_last_n_months_issues(project_key, months=6):
    """
    Retrieve completed Jira issues for the last N months from a given project.

    Parameters:
        project_key (str): The Jira project key (e.g. 'ITNET').
        months (int): Number of months to look back (default 6).

    Returns:
        list: List of issue dictionaries.

    Resilience:
        - Delegates to fetch_issues(), which uses enhanced JQL with cursor pagination.
    """
    now = datetime.now(timezone.utc)
    start_date = now.replace(day=1)
    # Adjust for cross-year range if needed
    month = (start_date.month - months + 12) % 12 or 12
    year = start_date.year if start_date.month > months else start_date.year - 1
    query_start = start_date.replace(month=month, year=year)
    start_str = query_start.strftime('%Y-%m-%d')

    jql = (
        f'project = {project_key} AND status = Done '
        f'AND issuetype != Epic '
        f'AND resolved >= "{start_str}" ORDER BY resolved DESC'
    )

    issues = []
    start_at = 0  # kept for compatibility; unused by enhanced search
    while True:
        result = fetch_issues(jql, start_at=start_at)
        batch = result.get("issues", [])
        issues.extend(batch)
        # fetch_issues now returns ALL pages in one shot; break immediately
        break
    return issues

# ===============================
# CYCLE TIME: WITH CHANGELOG DATA
# ===============================

def get_cycle_time_issues(project_key, months=6):
    """
    Retrieve completed issues with changelog for cycle time analysis
    (In Progress → Done duration).

    Parameters:
        project_key (str): The Jira project key (e.g. 'ITNET').
        months (int): Lookback window in months (default 6).

    Returns:
        list: List of issue dictionaries with changelog expanded.

    Resilience:
        - Uses POST /rest/api/3/search/jql with expand=["changelog"] and cursor pagination.
    """
    now = datetime.now(timezone.utc)
    start_date = now.replace(day=1)
    # Adjust for cross-year range if needed
    month = (start_date.month - months + 12) % 12 or 12
    year = start_date.year if start_date.month > months else start_date.year - 1
    query_start = start_date.replace(month=month, year=year)
    start_str = query_start.strftime('%Y-%m-%d')

    jql = (
        f'project = {project_key} AND status = Done '
        f'AND issuetype != Epic '
        f'AND resolved >= "{start_str}" ORDER BY resolved DESC'
    )

    issues = []
    token = None
    batch_size = 100
    while True:
        result = _search_jql(
            jql=jql,
            max_results=batch_size,
            next_page_token=token,
            fields=["summary", "status", "created", "resolutiondate", "assignee", "parent"],
            expand=["changelog"]
        )
        batch = result.get("issues", [])
        issues.extend(batch)

        if result.get("isLast") or not result.get("nextPageToken"):
            break
        token = result.get("nextPageToken")

    return issues
