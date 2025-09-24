# ==========================================
# metrics_calculations.py – Metric Functions
# ==========================================

from datetime import datetime
import pandas as pd

# ============================
# DATAFRAME TRANSFORMATION
# ============================

# ------------------------------------------
# Jira Issue JSON → Structured DataFrame
# ------------------------------------------

def parse_issues_to_dataframe(issues):
    """
    Convert raw Jira issue JSON into a structured pandas DataFrame.

    Parameters:
        issues (list): List of Jira issue dicts.

    Returns:
        pd.DataFrame: Parsed data with columns:
                      key, summary, created, resolved,
                      lead_time_days, assignee, customfield_10239, parent
    """
    records = []
    for issue in issues:
        fields = issue["fields"]
        resolution = fields.get("resolutiondate")
        created = fields.get("created")
        assignee = fields["assignee"]["displayName"] if fields.get("assignee") else None
        ktlo_flag = fields.get("customfield_10239")

        # --- Safely extract parent info ---
        parent_obj = fields.get("parent")
        parent_key = parent_obj.get("key") if parent_obj else None
        parent_summary = (
            parent_obj.get("fields", {}).get("summary") if parent_obj and "fields" in parent_obj else None
        )

        if resolution and created:
            created_dt = datetime.strptime(created[:19], "%Y-%m-%dT%H:%M:%S")
            resolved_dt = datetime.strptime(resolution[:19], "%Y-%m-%dT%H:%M:%S")
            lead_time = (resolved_dt - created_dt).days

            records.append({
                "key": issue["key"],
                "summary": fields["summary"],
                "created": created_dt,
                "resolved": resolved_dt,
                "lead_time_days": lead_time,
                "assignee": assignee,
                "customfield_10239": ktlo_flag,
                "parent": parent_key,
                "parent_summary": parent_summary
            })

    return pd.DataFrame(records)

# =======================
# THROUGHPUT METRICS
# =======================

# ------------------------------------------
# Monthly Throughput (Count of Issues Closed)
# ------------------------------------------

def calculate_throughput(df):
    """
    Group resolved issues by month and count them to determine throughput.

    Parameters:
        df (pd.DataFrame): Jira issues DataFrame with a 'resolved' column.

    Returns:
        pd.DataFrame: Resolved month and issue count per month.
    """
    if df.empty:
        return pd.DataFrame()
    df["resolved_month"] = df["resolved"].dt.to_period("M")
    return df.groupby("resolved_month").size().rename("throughput").reset_index()

# ------------------------------------------
# Average Monthly Throughput
# ------------------------------------------

def calculate_average_throughput(df):
    """
    Calculate the average throughput per month over the range of available data.

    Parameters:
        df (pd.DataFrame): Jira issues DataFrame.

    Returns:
        float: Average number of issues resolved per month.
    """
    if df.empty:
        return 0
    monthly = calculate_throughput(df)
    return monthly["throughput"].mean()

# ------------------------------------------
# Monthly KTLO Summary Table
# ------------------------------------------

def generate_ktlo_summary(df, category_col="Category", value_col="resolved"):
    """
    Generate a monthly summary table for a binary category field (e.g., KTLO vs Non-KTLO).

    Parameters:
        df (pd.DataFrame): Input Jira issues DataFrame.
        category_col (str): Name of the category column (default: "Category").
        value_col (str): Value field (not used directly yet, but allows extension).

    Returns:
        pd.DataFrame: Summary table with Total, breakdown by category, and category %.
    """
    throughput_by_category = df.groupby(["Month", category_col]).size().unstack(fill_value=0)
    totals = throughput_by_category.sum(axis=1)
    categories = throughput_by_category.columns.tolist()
    summary = throughput_by_category.copy()
    summary["Total"] = totals

    if len(categories) == 2:
        cat1, cat2 = categories
        summary[f"{cat1} %"] = (summary[cat1] / totals * 100).round(1)
        summary = summary.reset_index().rename(columns={cat1: f"{cat1}", cat2: f"{cat2}"})
        summary = summary[["Month", "Total", cat1, cat2, f"{cat1} %"]]
    else:
        summary = summary.reset_index()

    return summary



# =======================
# LEAD TIME METRICS
# =======================

# ------------------------------------------
# Group Lead Time by Assignee
# ------------------------------------------

def group_lead_time_by_assignee(df):
    """
    Compute average lead time by assignee.

    Parameters:
        df (pd.DataFrame): Jira issues DataFrame.

    Returns:
        pd.DataFrame: Assignee and average lead time.
    """
    if df.empty:
        return pd.DataFrame()
    return df.groupby("assignee")["lead_time_days"].mean().reset_index().sort_values(
        by="lead_time_days", ascending=False
    )

# ------------------------------------------
# Identify Outlier Issues by Z-Score
# ------------------------------------------

def identify_outliers(df, z_threshold=2.0):
    """
    Identify outlier issues based on z-score for lead time.

    Parameters:
        df (pd.DataFrame): Jira issues DataFrame.
        z_threshold (float): Z-score threshold for defining an outlier.

    Returns:
        pd.DataFrame: Subset of issues with lead times significantly above the mean.
    """
    if df.empty or "lead_time_days" not in df.columns:
        return pd.DataFrame()
    mean = df["lead_time_days"].mean()
    std = df["lead_time_days"].std()
    df["z_score"] = (df["lead_time_days"] - mean) / std
    return df[df["z_score"].abs() >= z_threshold].sort_values(by="z_score", ascending=False)



# =======================
# CYCLE TIME METRICS
# =======================

# ------------------------------------------
# Parse Jira Issues for Cycle Time Analysis
# ------------------------------------------

def parse_cycle_time_issues(issues):
    """
    Extracts cycle time data from issues with changelog.
    Cycle time = In Progress → Done

    Parameters:
        issues (list): Jira issues with changelog included.

    Returns:
        pd.DataFrame: DataFrame with cycle time and key metadata.
    """
    records = []

    for issue in issues:
        fields = issue.get("fields", {})
        changelog = issue.get("changelog", {}).get("histories", [])

        key = issue.get("key")
        summary = fields.get("summary")
        assignee = fields["assignee"]["displayName"] if fields.get("assignee") else None
        resolved_str = fields.get("resolutiondate")

        # Parent context (optional)
        parent_obj = fields.get("parent")
        parent_key = parent_obj.get("key") if parent_obj else None
        parent_summary = (
            parent_obj.get("fields", {}).get("summary") if parent_obj and "fields" in parent_obj else None
        )

        # Parse resolution time
        resolved_dt = pd.to_datetime(resolved_str, utc=True) if resolved_str else None

        # Walk changelog to find first "In Progress"
        in_progress_dt = None
        for entry in changelog:
            for item in entry.get("items", []):
                if item.get("field") == "status":
                    to_status = item.get("toString")
                    if to_status == "In Progress" and in_progress_dt is None:
                        in_progress_dt = pd.to_datetime(entry.get("created"), utc=True)

        if in_progress_dt and resolved_dt:
            cycle_time_days = (resolved_dt - in_progress_dt).days

            records.append({
                "key": key,
                "summary": summary,
                "assignee": assignee,
                "in_progress": in_progress_dt,
                "resolved": resolved_dt,
                "cycle_time_days": cycle_time_days,
                "parent": parent_key,
                "parent_summary": parent_summary
            })

    return pd.DataFrame(records)


# ======================
# WIP METRICS
# ======================

# ------------------------------------------
# Build WIP Ranges from Changelog
# ------------------------------------------

def parse_wip_ranges(issues, end_date):
    """

    Parse changelogs to extract In Progress intervals as full WIP records (with metadata).

    Parameters:
        issues (list): List of Jira issues with changelog
        end_date (datetime): End of the WIP observation window (should match plotting range)

    Returns:
        Returns a list of dicts 

    """
    import pandas as pd

    wip_records = []
    seen_keys = set()
    missing_details = []

    for issue in issues:
        issue_key = issue.get("key")
        fields = issue.get("fields", {})
        changelog = issue.get("changelog", {}).get("histories", [])
        current_status = fields.get("status", {}).get("name")
        created_date = pd.to_datetime(fields.get("created"), utc=True)

        summary = fields.get("summary")
        assignee = fields.get("assignee", {}).get("displayName") if fields.get("assignee") else None

        in_progress_start = None
        in_progress_end = None

        for entry in sorted(changelog, key=lambda x: x["created"]):
            for item in entry.get("items", []):
                if item.get("field") == "status":
                    from_status = item.get("fromString")
                    to_status = item.get("toString")
                    timestamp = pd.to_datetime(entry.get("created"), utc=True)

                    if to_status == "In Progress" and in_progress_start is None:
                        in_progress_start = timestamp
                    elif from_status == "In Progress" and in_progress_start:
                        in_progress_end = timestamp
                        wip_records.append({
                            "key": issue_key,
                            "summary": summary,
                            "assignee": assignee,
                            "start": in_progress_start,
                            "end": in_progress_end
                        })
                        in_progress_start = None

        # Still in progress
        if in_progress_start and not in_progress_end and current_status == "In Progress":
            wip_records.append({
                "key": issue_key,
                "summary": summary,
                "assignee": assignee,
                "start": in_progress_start,
                "end": end_date
            })
            seen_keys.add(issue_key)

        # Fallback logic
        if current_status == "In Progress" and issue_key not in seen_keys:
            inferred_start = max(created_date, end_date - pd.Timedelta(days=30))
            wip_records.append({
                "key": issue_key,
                "summary": summary,
                "assignee": assignee,
                "start": inferred_start,
                "end": end_date
            })
            seen_keys.add(issue_key)
            missing_details.append((issue_key, summary))

    return wip_records, missing_details



def get_issues_in_progress_in_month(wip_records, target_month_str):
    """
    Returns issues that had active WIP time during the specified month.

    Parameters:
        wip_records (list of dict): List of WIP issues with 'start', 'end', 'key', etc.
        target_month_str (str): Target month in YYYY-MM format (e.g., "2025-01")

    Returns:
        pd.DataFrame: Table of matching issues with key metadata
    """
    import pandas as pd
    from datetime import timezone

    target_period = pd.Period(target_month_str, freq="M")
    start_of_month = target_period.start_time.replace(tzinfo=timezone.utc)
    end_of_month = target_period.end_time.replace(tzinfo=timezone.utc)

    matched = []
    for record in wip_records:
        if record["start"] <= end_of_month and record["end"] >= start_of_month:
            matched.append({
                "key": record.get("key"),
                "summary": record.get("summary"),
                "assignee": record.get("assignee"),
                "in_progress_start": record["start"],
                "in_progress_end": record["end"],
                "days_in_progress": (record["end"] - record["start"]).days
            })

    df = pd.DataFrame(matched)
    df.sort_values("in_progress_start", inplace=True)
    return df

