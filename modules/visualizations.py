# ========================================
# visualizations.py - Charting Functions
# ========================================

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from utils import safe_divide, report_outliers

# ==========================
# THROUGHPUT VISUALIZATIONS
# ==========================

# ----------------------------------------
# Bar Chart: Monthly Throughput
# ----------------------------------------

def plot_throughput_bar(df, project_key):
    throughput = df.groupby("Month")["resolved"].count()
    average_throughput = throughput.mean()

    plt.figure(figsize=(10, 6))
    ax = throughput.plot(kind="bar", color="skyblue")
    ax.set_xticklabels([period.strftime("%B") for period in throughput.index], rotation=45)
    plt.title(f"Monthly Throughput - {project_key.upper()}")
    plt.xlabel("Month")
    plt.ylabel("Number of Issues Resolved")
    plt.grid(True)

    for idx, value in enumerate(throughput):
        ax.annotate(str(value), xy=(idx, value), xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=9)

    plt.axhline(y=average_throughput, color='red', linestyle='--', linewidth=1.5,
                label=f"Avg: {average_throughput:.1f}")
    plt.legend()
    plt.tight_layout()
    plt.show()

# ----------------------------------------
# Combined Chart: KTLO Volume + % Trendline
# ----------------------------------------

def plot_combined_ktlo_chart(df, project_key, show_outliers=False, clamp_range=(0, 100)):
    """
    Stacked bar chart for KTLO vs Non-KTLO throughput with KTLO % line and average.
    Optional logging of outliers that are visually excluded by clamp_range.
    """
    throughput_by_category = df.groupby(["Month", "Category"]).size().unstack(fill_value=0)
    ktlo_counts = throughput_by_category.get("KTLO", pd.Series(0, index=throughput_by_category.index))
    non_ktlo_counts = throughput_by_category.get("Non-KTLO", pd.Series(0, index=throughput_by_category.index))
    totals = throughput_by_category.sum(axis=1)
    ktlo_pct = (ktlo_counts / totals * 100).round(1)
    average_ktlo_pct = ktlo_pct.mean()

    if show_outliers:
        report_outliers(ktlo_pct, clamp_range, label="KTLO %")

    ktlo_pct_clamped = ktlo_pct.clip(lower=clamp_range[0], upper=clamp_range[1])

    fig, ax1 = plt.subplots(figsize=(12, 6))
    throughput_by_category.plot(kind="bar", stacked=True, colormap="Set2", ax=ax1)
    ax1.set_ylabel("Number of Issues Resolved")
    ax1.set_xlabel("Month")
    ax1.set_title(f"Monthly Throughput by KTLO vs Non-KTLO with KTLO % Trend – {project_key}")
    ax1.set_xticklabels([p.strftime("%b") for p in ktlo_pct.index], rotation=45)
    ax1.grid(True)

    ax2 = ax1.twinx()
    ax2.plot(ktlo_pct.index.astype(str), ktlo_pct_clamped, color="purple", marker="o", linewidth=2, label="KTLO %")
    ax2.axhline(y=average_ktlo_pct, color="red", linestyle="--", linewidth=1.5, label=f"Avg KTLO %: {average_ktlo_pct:.1f}")
    ax2.set_ylabel("KTLO %")
    ax2.set_ylim(clamp_range[0], clamp_range[1] + 10)

    for idx, pct in enumerate(ktlo_pct_clamped):
        total_height = totals.iloc[idx]
        ax1.annotate(f"{pct}%", xy=(idx, total_height), xytext=(0, 3), textcoords="offset points",
                     ha='center', va='bottom', fontsize=9, color='purple')

    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc="upper right")

    plt.tight_layout()
    plt.show()


# ========================
# LEAD TIME VISUALIZATIONS
# ========================

# ----------------------------------------
# Line Chart: Lead Time Trend (Unfiltered)
# ----------------------------------------

def plot_lead_time_trend(df, project_key):
    """
    Plots raw average lead time per month (includes outliers),
    with data point annotations and a red overall average line.
    """
    trend = df.groupby("Month")["lead_time_days"].mean()
    overall_avg = trend.mean()

    plt.figure(figsize=(10, 5))
    ax = trend.plot(marker="o", color="steelblue", label="Monthly Avg Lead Time")

    # === Add annotations ===
    for month, value in trend.items():
        ax.annotate(
            f"{value:.1f}",
            xy=(month, value),
            xytext=(0, 6),
            textcoords="offset points",
            ha="center",
            fontsize=9,
        )

    # === Draw average line ===
    plt.axhline(
        y=overall_avg,
        color='red',
        linestyle='--',
        linewidth=1.5,
        label=f"Overall Avg: {overall_avg:.1f} days"
    )

    plt.title(f"Average Lead Time by Month (Incl. Outliers) – {project_key.upper()}")
    plt.xlabel("Month")
    plt.ylabel("Lead Time (days)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

    # === Summary Table ===
    summary = trend.round(1).reset_index()
    summary.columns = ["Month", "Avg Lead Time (All Issues)"]
    summary["Month"] = summary["Month"].astype(str)
    print("\n📊 Monthly Lead Time Averages (Includes Outliers):")
    display(summary)


# ----------------------------------------
# Line Chart: Lead Time Trend (Excludes Outliers > Threshold)
# ----------------------------------------

def plot_lead_time_trend_exclude_extremes(df, project_key, threshold_days=750):
    filtered_df = df[df["lead_time_days"] <= threshold_days]
    all_df = df.copy()

    leadtime_by_month_filtered = filtered_df.groupby("Month")["lead_time_days"].mean()
    leadtime_by_month_all = all_df.groupby("Month")["lead_time_days"].mean()

    plt.figure(figsize=(10, 6))
    ax = leadtime_by_month_filtered.plot(marker="o", color="steelblue", label="Avg Lead Time (Filtered)")
    average_leadtime_filtered = leadtime_by_month_filtered.mean()
    plt.axhline(y=average_leadtime_filtered, color="red", linestyle="--", linewidth=1.5,
                label=f"Filtered Avg: {average_leadtime_filtered:.1f} days")

    for month, value in leadtime_by_month_filtered.items():
        ax.annotate(f"{value:.1f}", xy=(month, value), xytext=(0, 6), textcoords="offset points",
                    ha="center", fontsize=9)

    plt.title(f"Lead Time Trend (Excludes Issues > {threshold_days}d) - {project_key}")
    plt.xlabel("Month")
    plt.ylabel("Lead Time (days)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

    # Monthly summary (filtered)
    summary = leadtime_by_month_filtered.round(1).reset_index()
    summary.columns = ["Month", "Avg Lead Time (Filtered)"]
    summary["Month"] = summary["Month"].astype(str)
    print("\n📊 Monthly Averages (Excludes Outliers):")
    display(summary)

    # Outlier table
    excluded = df[df["lead_time_days"] > threshold_days]
    if not excluded.empty:
        print(f"\n⚠️ Excluded Issues (Lead Time > {threshold_days} days):")
        requested_cols = [
            "key", "summary", "parent_summary",
            "assignee", "created", "resolved", "lead_time_days"
        ]
        available_cols = [col for col in requested_cols if col in excluded.columns]
        display(excluded[available_cols].sort_values(by="lead_time_days", ascending=False))
    else:
        print(f"\n✅ No issues exceeded {threshold_days} days.")

# ----------------------------------------
# Histogram: Lead Time Distribution
# ----------------------------------------

def plot_lead_time_distribution(df, project_key):
    plt.figure(figsize=(10, 6))
    ax = sns.histplot(df["lead_time_days"], bins=20, kde=True, color="skyblue")
    mean = df["lead_time_days"].mean()
    p95 = df["lead_time_days"].quantile(0.95)
    max_val = df["lead_time_days"].max()

    plt.axvline(mean, color="green", linestyle="--", label=f"Mean: {mean:.1f}d")
    plt.axvline(p95, color="orange", linestyle="--", label=f"95th %ile: {p95:.1f}d")
    plt.axvline(max_val, color="red", linestyle="--", label=f"Max: {max_val:.1f}d")

    for patch in ax.patches:
        height = patch.get_height()
        if height > 0:
            ax.annotate(f"{int(height)}", xy=(patch.get_x() + patch.get_width() / 2, height),
                        xytext=(0, 4), textcoords="offset points",
                        ha='center', va='bottom', fontsize=9)

    plt.title(f"Lead Time Distribution - {project_key.upper()}")  # <-- fixed f-string
    plt.xlabel("Lead Time (days)")
    plt.ylabel("Number of Issues")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# ----------------------------------------
# Heatmap: Lead Time by Assignee
# ----------------------------------------

def plot_lead_time_heatmap_by_assignee(df, project_key):
    pivot = df.pivot_table(values="lead_time_days", index="assignee", aggfunc="mean").sort_values("lead_time_days", ascending=False)
    plt.figure(figsize=(8, len(pivot) * 0.5 + 1))
    sns.heatmap(pivot, annot=True, cmap="Blues", fmt=".1f")
    plt.title(f"Average Lead Time by Assignee – {project_key.upper()}")
    plt.xlabel("")
    plt.ylabel("Assignee")
    plt.tight_layout()
    plt.show()

    # Summary table below
    print(f"\n{project_key.upper()} - Lead Time by Assignee:")
    summary = pivot.reset_index().rename(columns={"lead_time_days": "Avg Lead Time (days)"})
    display(summary)




# ==========================
# CYCLE TIME VISUALIZATIONS
# ==========================

# ----------------------------------------
# Line Chart: Cycle Time Trend (Excludes Outliers > Threshold)
# ----------------------------------------

def plot_cycle_time_trend_exclude_extremes(df, project_key, threshold_days=750):
    filtered_df = df[df["cycle_time_days"] <= threshold_days]
    all_df = df.copy()

    cycle_by_month_filtered = filtered_df.groupby("Month")["cycle_time_days"].mean()
    cycle_by_month_all = all_df.groupby("Month")["cycle_time_days"].mean()

    plt.figure(figsize=(10, 6))
    ax = cycle_by_month_filtered.plot(marker="o", color="teal", label="Avg Cycle Time (Filtered)")
    avg_cycle_filtered = cycle_by_month_filtered.mean()
    plt.axhline(y=avg_cycle_filtered, color="red", linestyle="--", linewidth=1.5,
                label=f"Filtered Avg: {avg_cycle_filtered:.1f} days")

    for month, value in cycle_by_month_filtered.items():
        ax.annotate(f"{value:.1f}", xy=(month, value), xytext=(0, 6), textcoords="offset points",
                    ha="center", fontsize=9)

    plt.title(f"Cycle Time Trend (Excludes Issues > {threshold_days}d) - {project_key}")
    plt.xlabel("Month")
    plt.ylabel("Cycle Time (days)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

    # Monthly summary (filtered)
    summary = cycle_by_month_filtered.round(1).reset_index()
    summary.columns = ["Month", "Avg Cycle Time (Filtered)"]
    summary["Month"] = summary["Month"].astype(str)
    print("\n📊 Monthly Averages (Excludes Outliers):")
    display(summary)

    # Outlier table
    excluded = df[df["cycle_time_days"] > threshold_days]
    if not excluded.empty:
        print(f"\n⚠️ Excluded Issues (Cycle Time > {threshold_days} days):")
        requested_cols = [
            "key", "summary", "parent_summary",
            "assignee", "in_progress", "resolved", "cycle_time_days"
        ]
        available_cols = [col for col in requested_cols if col in excluded.columns]
        display(excluded[available_cols].sort_values(by="cycle_time_days", ascending=False))
    else:
        print(f"\n✅ No issues exceeded {threshold_days} days.")



# ----------------------------------------
# Line Chart: Cycle Time Trend (All Issues, Incl. Outliers)
# ----------------------------------------

def plot_cycle_time_trend(df, project_key):
    """
    Plots raw average cycle time per month (includes outliers),
    with point annotations and a red overall average line.
    """
    trend = df.groupby("Month")["cycle_time_days"].mean()
    overall_avg = trend.mean()

    plt.figure(figsize=(10, 5))
    ax = trend.plot(marker="o", color="teal", label="Monthly Avg Cycle Time")

    for month, value in trend.items():
        ax.annotate(
            f"{value:.1f}",
            xy=(month, value),
            xytext=(0, 6),
            textcoords="offset points",
            ha="center",
            fontsize=9,
        )

    plt.axhline(
        y=overall_avg,
        color='red',
        linestyle='--',
        linewidth=1.5,
        label=f"Overall Avg: {overall_avg:.1f} days"
    )

    plt.title(f"Average Cycle Time by Month (Incl. Outliers) – {project_key.upper()}")
    plt.xlabel("Month")
    plt.ylabel("Cycle Time (days)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

    summary = trend.round(1).reset_index()
    summary.columns = ["Month", "Avg Cycle Time (All Issues)"]
    summary["Month"] = summary["Month"].astype(str)
    print("\n📊 Monthly Cycle Time Averages (Includes Outliers):")
    display(summary)



# ----------------------------------------
# Histogram: Cycle Time Distribution
# ----------------------------------------

def plot_cycle_time_distribution(df, project_key):
    plt.figure(figsize=(10, 6))
    ax = sns.histplot(df["cycle_time_days"], bins=20, kde=True, color="lightseagreen")
    mean = df["cycle_time_days"].mean()
    p95 = df["cycle_time_days"].quantile(0.95)
    max_val = df["cycle_time_days"].max()

    plt.axvline(mean, color="green", linestyle="--", label=f"Mean: {mean:.1f}d")
    plt.axvline(p95, color="orange", linestyle="--", label=f"95th %ile: {p95:.1f}d")
    plt.axvline(max_val, color="red", linestyle="--", label=f"Max: {max_val:.1f}d")

    for patch in ax.patches:
        height = patch.get_height()
        if height > 0:
            ax.annotate(f"{int(height)}", xy=(patch.get_x() + patch.get_width() / 2, height),
                        xytext=(0, 4), textcoords="offset points",
                        ha='center', va='bottom', fontsize=9)

    plt.title(f"Cycle Time Distribution - {project_key.upper()}")  # <-- fixed f-string
    plt.xlabel("Cycle Time (days)")
    plt.ylabel("Number of Issues")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# ----------------------------------------
# Heatmap: Cycle Time by Assignee
# ----------------------------------------

def plot_cycle_time_heatmap_by_assignee(df, project_key):
    pivot = df.pivot_table(values="cycle_time_days", index="assignee", aggfunc="mean").sort_values("cycle_time_days", ascending=False)
    plt.figure(figsize=(8, len(pivot) * 0.5 + 1))
    sns.heatmap(pivot, annot=True, cmap="Greens", fmt=".1f")
    plt.title(f"Average Cycle Time by Assignee - {project_key.upper()}")
    plt.xlabel("")
    plt.ylabel("Assignee")
    plt.tight_layout()
    plt.show()

    print("\nCycle Time by Assignee:")
    summary = pivot.reset_index().rename(columns={"cycle_time_days": "Avg Cycle Time (days)"})
    display(summary)


# ==========================
# WIP VISUALIZATIONS
# ==========================

# ----------------------------------------
# Line Chart: Daily WIP Trend
# ----------------------------------------

def plot_daily_wip_time_series(wip_records, days_lookback, project_key):
    import pandas as pd
    import matplotlib.pyplot as plt
    from datetime import datetime, timedelta, timezone

    # Compute daily range
    end_date = datetime.now(timezone.utc).replace(hour=23, minute=59, second=59, microsecond=999999)
    start_date = end_date - timedelta(days=days_lookback)
    date_range = pd.date_range(start=start_date, end=end_date, freq='D', tz="UTC")

    # Count issues in progress on each day
    wip_counts = pd.Series(0, index=date_range)
    for record in wip_records:
        start = record["start"]
        end = record["end"]
        for day in date_range:
            if start <= day <= end:
                wip_counts[day] += 1

    # === Plot ===
    plt.figure(figsize=(12, 6))
    ax = wip_counts.plot()
    plt.title(f"Daily Work in Progress (WIP) – Last {days_lookback} Days - {project_key.upper()}")
    plt.xlabel("Date")
    plt.ylabel("Number of In Progress Items")
    plt.grid(True)

    for i in range(len(wip_counts)):
        ax.annotate(f"{wip_counts.iloc[i]}", (wip_counts.index[i], wip_counts.iloc[i]),
                    textcoords="offset points", xytext=(0, 6), ha='center', fontsize=8, color='darkgreen')

    plt.tight_layout()
    plt.show()

    # === Summary Lines ===
    latest_date = wip_counts.index[-1].strftime("%Y-%m-%d")
    print(f"\nWIP Count on {latest_date}: {wip_counts.iloc[-1]}")
    print(f"Max WIP: {wip_counts.max()}")
    print(f"Min WIP: {wip_counts.min()}")
    print(f"Avg WIP: {wip_counts.mean():.1f}")

# ----------------------------------------
# WIP Table: Daily Breakdown (Optional View)
# ----------------------------------------

def show_daily_wip_table(wip_records, days_lookback, project_key):
    import pandas as pd
    from datetime import datetime, timedelta, timezone

    end_date = datetime.now(timezone.utc).replace(hour=23, minute=59, second=59, microsecond=999999)
    start_date = end_date - timedelta(days=days_lookback)
    date_range = pd.date_range(start=start_date, end=end_date, freq='D', tz="UTC")

    wip_counts = pd.Series(0, index=date_range)
    for record in wip_records:
        start = record["start"]
        end = record["end"]
        for day in date_range:
            if start <= day <= end:
                wip_counts[day] += 1

    table = pd.DataFrame({
        "Date": wip_counts.index.strftime("%b %d"),
        "WIP Count": wip_counts.values
    })

    print(f"\n📅 Daily {project_key.upper()} WIP Table:")
    display(table)


def debug_daily_wip_table(wip_records, days_lookback):
    import pandas as pd
    from datetime import datetime, timedelta, timezone

    end_date = datetime.now(timezone.utc).replace(hour=23, minute=59, second=59, microsecond=999999)
    start_date = end_date - timedelta(days=days_lookback)
    date_range = pd.date_range(start=start_date, end=end_date, freq='D', tz="UTC")

    wip_counts = pd.Series(0, index=date_range)
    for record in wip_records:
        start = record["start"]
        end = record["end"]
        for day in date_range:
            if start <= day <= end:
                wip_counts[day] += 1

    df = pd.DataFrame({
        "Date": wip_counts.index.strftime("%b %d"),
        "WIP Count": wip_counts.values
    })

    print("📅 Daily WIP Table:")
    display(df)

# ----------------------------------------
# Bar Chart: Monthly Average WIP
# ----------------------------------------

def plot_monthly_average_wip(wip_records, months_lookback, project_key):
    import pandas as pd
    import matplotlib.pyplot as plt
    from datetime import datetime, timezone

    end_date = datetime.now(timezone.utc).replace(hour=23, minute=59, second=59, microsecond=999999)
    start_date = end_date - pd.DateOffset(months=months_lookback)
    date_range = pd.date_range(start=start_date, end=end_date, freq='D', tz="UTC")

    wip_counts = pd.Series(0, index=date_range)
    for record in wip_records:
        start = record["start"]
        end = record["end"]
        for day in date_range:
            if start <= day <= end:
                wip_counts[day] += 1

    df = pd.DataFrame({
        "date": wip_counts.index,
        "wip": wip_counts.values
    })

    df["date"] = df["date"].dt.tz_localize(None)
    df["month"] = df["date"].dt.to_period("M")
    monthly_avg = df.groupby("month")["wip"].mean().reset_index()
    monthly_avg["month_str"] = monthly_avg["month"].astype(str)

    plt.figure(figsize=(10, 6))
    ax = monthly_avg.set_index("month_str")["wip"].plot(kind="bar", color="seagreen")
    ax.set_title(f"Monthly Average WIP (Daily-based) – {project_key.upper()}")  # <-- include key
    ax.set_xlabel("Month")
    ax.set_ylabel("Average Daily WIP")
    ax.set_xticklabels(monthly_avg["month"].dt.strftime("%b %Y"), rotation=45)

    for idx, val in enumerate(monthly_avg["wip"]):
        ax.annotate(f"{val:.1f}", xy=(idx, val), xytext=(0, 3), textcoords="offset points",
                    ha='center', fontsize=9)

    plt.grid(True)
    plt.tight_layout()
    plt.show()

# ----------------------------------------
# Debug View: Monthly WIP Aggregation
# ----------------------------------------

def debug_monthly_wip_aggregation(wip_records, months_lookback):
    import pandas as pd

    all_days = []
    for record in wip_records:
        all_days.extend(pd.date_range(start=record["start"], end=record["end"], freq='D'))

    wip_df = pd.DataFrame({"date": all_days})
    wip_df["date"] = wip_df["date"].dt.tz_localize(None)
    wip_df["month"] = wip_df["date"].dt.to_period("M")

    max_month = wip_df["month"].max()
    min_month = max_month - months_lookback + 1
    wip_df = wip_df[wip_df["month"] >= min_month]

    daily_counts = wip_df.groupby("date").size().rename("WIP Count").reset_index()
    print("\n📅 Daily Presence Counts:")
    display(daily_counts)

    monthly_avg = wip_df.groupby("month").size().rename("WIP Days").reset_index()
    monthly_avg["Avg WIP"] = monthly_avg["WIP Days"] / monthly_avg["month"].apply(lambda m: m.days_in_month)

    print("\n📆 Monthly Aggregated WIP Averages:")
    display(monthly_avg)
