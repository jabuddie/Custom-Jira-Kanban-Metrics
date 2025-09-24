# ========================================
# utils.py - General Utility Functions
# ========================================

from datetime import datetime
import pandas as pd

# ----------------------------------------
# Date Utilities
# ----------------------------------------

def get_month_range(months_back: int = 6):
    """
    Returns the first day of the month N months ago and today’s date.
    Useful for constructing dynamic Jira JQL ranges.
    """
    today = datetime.now()
    start_month = (today.replace(day=1) - pd.DateOffset(months=months_back)).to_pydatetime()
    return start_month, today

def timestamp_to_period(series, freq="M"):
    """
    Converts a datetime Series to a pandas PeriodIndex (e.g., by month).
    """
    return pd.to_datetime(series).dt.to_period(freq)

# ----------------------------------------
# Formatting Utilities
# ----------------------------------------

def period_index_to_str(index: pd.PeriodIndex, fmt="%b"):
    """
    Converts a PeriodIndex (e.g., '2025-04') to readable strings (e.g., 'Apr').
    Used for cleaner chart X-axis labels.
    """
    return [p.strftime(fmt) for p in index.to_timestamp()]

def format_percent(value: float, decimals=1):
    """
    Converts a float to a formatted percent string (e.g., 0.426 → '42.6%').
    """
    return f"{value:.{decimals}f}%"

# ----------------------------------------
# Math and Clamping Utilities
# ----------------------------------------

def clamp(value, min_val, max_val):
    """
    Clamp a numeric value to a minimum and maximum bound.
    Useful for safe rendering in charts or heatmaps.
    """
    return max(min_val, min(value, max_val))

def safe_divide(numerator, denominator, fallback=0):
    """
    Divides two numbers safely, returning a fallback on division error.
    """
    try:
        return numerator / denominator
    except (ZeroDivisionError, TypeError):
        return fallback

# ----------------------------------------
# Outlier Reporting
# ----------------------------------------

def report_outliers(series, clamp_range, label="Value"):
    """
    Print values outside the defined clamp range for transparency.
    """
    outliers = series[(series < clamp_range[0]) | (series > clamp_range[1])]
    if not outliers.empty:
        print(f"\n⚠️ {label} outliers excluded from chart range ({clamp_range[0]}–{clamp_range[1]}):")
        print(outliers)

# ----------------------------------------
# Flexible Classification Utility
# ----------------------------------------

def classify_by_issueflag(flag, match_value="KTLO", match_label="KTLO", default_label="Non-KTLO"):
    """
    Classifies a custom field by matching a value (default = 'KTLO').
    Handles list, dict, string, or null values from Jira multi/single-select fields.

    Parameters:
        flag: Raw field value from Jira (list, dict, str, or None)
        match_value: What to match against (default: 'KTLO')
        match_label: Label to return on match
        default_label: Label to return if no match

    Returns:
        str: match_label or default_label
    """
    if isinstance(flag, list):
        return match_label if any(isinstance(f, dict) and f.get("value") == match_value for f in flag) else default_label
    elif isinstance(flag, dict):
        return match_label if flag.get("value") == match_value else default_label
    elif isinstance(flag, str):
        return match_label if flag == match_value else default_label
    else:
        return default_label
