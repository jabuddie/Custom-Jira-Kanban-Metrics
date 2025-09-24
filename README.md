# Custom-Jira-Kanban-Metrics

A free and comprehensive Jupyter notebook-based analytics suite for extracting and visualizing the four essential Kanban metrics from Jira. This free alternative provides on-demand analytics that aren't available by default in Jira.

## The Four Essential Kanban Metrics

### 1. Lead Time
**Lead time measures the duration from when a task is added to the system until it's marked as complete.** This metric provides comprehensive understanding of how long it takes for a task to move through the entire workflow—from customer request to delivery.

### 2. Cycle Time  
**Cycle time tracks the time taken from commencing work on a task to its completion.** It shows the actual time spent actively working on a task, offering insights into operational efficiency within individual tasks or user stories.

### 3. Work-in-Progress (WIP)
**Work-in-progress (WIP) encapsulates the volume of tasks actively in play at any given moment within the workflow.** Monitoring WIP allows teams to visualize workload across different stages and identify bottlenecks.

### 4. Throughput
**Throughput measures the quantity of tasks completed within a specific timeframe**, typically evaluated weekly or monthly. This provides a macroscopic view of overall productivity and team performance.

## Features

- **Throughput Analysis**: Monthly volume tracking, KTLO percentage breakdown, stacked bar charts with trend lines
- **Lead Time Analysis**: Monthly lead time tracking, distribution analysis, assignee-based metrics, outlier filtering  
- **Cycle Time Analysis**: In Progress → Done time tracking with comprehensive charting
- **WIP Analysis**: Daily and monthly work-in-progress history with line and bar chart visualizations
- **Built-in Debug Features**: Uncomment sections in notebooks to view detailed issue data and troubleshoot

## Prerequisites

- **Jupyter Notebook**: Install using your preferred method (Anaconda, pip, etc.)
- **Jira API Token**: Generate an API token for your Jira instance
- **Python Dependencies**: All required packages are included in the notebooks

## Project Structure

```
📦 kanban-metrics/
│
├── 📁 notebooks/
│   ├── throughput_analysis.ipynb    → Monthly volume, KTLO %, stacked bars + trendlines
│   ├── leadtime_analysis.ipynb      → Lead time per month, distribution, by-assignee, outlier filters
│   ├── cycletime_analysis.ipynb     → In Progress → Done, mirrors lead time charts
│   └── wip_analysis.ipynb           → Daily and monthly WIP history (line + bar charts)
│
├── 📁 modules/
│   ├── jira_api.py                  → Secure API client, token-based auth, paginated fetching
│   ├── metrics_calculations.py      → All logic: throughput, lead/cycle time, WIP analysis
│   ├── visualizations.py            → Chart functions (bar, stacked, heatmap, line, histogram)
│   └── utils.py                     → Time helpers, clamping, outlier handling, formatting
│
├── .env                             → Stores your Jira API token securely
├── requirements.txt                 → Optional: pip dependencies
└── README.md                        → You're here!
```

## Setup Instructions

### 1. Clone/Download the Repository
Download or clone this repository to your local machine.

### 2. Configure Your Jira API Access
1. Generate a Jira API token from your Atlassian account settings
2. Create a `.env` file in the root directory with the following format:
   ```
   JIRA_BASE_URL=https://your-instance.atlassian.net
   JIRA_EMAIL=your-email@company.com
   JIRA_API_TOKEN=your-api-token-here
   ```

### 3. Install Dependencies (Optional)
If you prefer to install dependencies via pip rather than within notebooks:
```bash
pip install -r requirements.txt
```

### 4. Launch Jupyter Notebook
```bash
jupyter notebook
```

## Usage

1. **Start with any notebook** in the `notebooks/` folder based on your analysis needs
2. **Configure your project settings** in the first cell of each notebook (project key, date ranges, etc.)
3. **Run all cells** to generate your metrics and visualizations
4. **Customize as needed** by modifying parameters or chart configurations

## Important Notes

### Custom Field Dependencies
The **Throughput Analysis** includes KTLO% (Keep The Lights On) metrics that depend on a custom field (`customfield_10239`) used to tag issues as either:
- **KTLO**: Maintenance/operational work
- **Project**: New feature/project work

**To customize for your environment:**
- Replace `customfield_10239` with your custom field ID, or
- Remove KTLO-related calculations if not applicable

## Important Notes

### Custom Jira Fields
This suite uses a **custom field** to flag KTLO (Keep the Lights On) items:
- **Jira Custom Field**: `customfield_10239`
- **Value**: "KTLO"

If your Jira instance does **not** include a similar custom field, you'll need to:
- Modify the `determine_ktlo()` function in `utils.py`
- Remove KTLO-based metrics or adjust classification logic

### Workflow-Specific Logic
- **Cycle Time** is based on transitions into "In Progress" → "Done"
- **Lead Time** is based on issue statuses "Backlog" → "Done" dates  
- **WIP** is tracked by parsing changelogs for "In Progress" intervals

You may need to adjust these terms depending on your team's Jira workflows.

### Data Security
- All API credentials are stored securely in the `.env` file
- The `.gitignore` file prevents accidental credential commits
- API communication uses token-based authentication

## Customization

### Modifying Metrics
Edit functions in `modules/metrics_calculations.py` to adjust calculation logic.

### Changing Visualizations
Update chart configurations in `modules/visualizations.py` for different styling or chart types.

### Adding New Analysis
Create new notebooks following the existing pattern and leverage the modular functions.

### Custom Field Configuration
To modify KTLO tracking for your Jira instance:
1. Locate your custom field ID in Jira Administration
2. Update `customfield_10239` references in relevant modules
3. Adjust the `determine_ktlo()` function logic as needed

### Workflow Customization  
If your Jira uses different status names:
1. Update status references in `metrics_calculations.py`
2. Modify transition logic for cycle time calculations
3. Adjust WIP tracking status filters

## Troubleshooting

- **Authentication Issues**: Verify your API token and base URL in the `.env` file with testApiToken.ipynb
- **Custom Field Errors**: Update or remove references to `customfield_10239` based on your Jira configuration
- **Date Range Issues**: Ensure your date filters align with your project's timeline

## Contributing

Feel free to fork this repository and submit pull requests for improvements or additional metrics.

## License

This project is open source. Use and modify as needed for your organization's requirements.
