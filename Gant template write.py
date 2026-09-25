from datetime import datetime, timedelta
import json
import pandas as pd

# Files
CSV_FILE = "devops_data.csv"
TEMPLATE_FILE = "template.html"
OUTPUT_FILE = "report.html"

# 1. Load CSV
df = pd.read_csv(CSV_FILE)

# Handle empty values / defaults
df["Assignee"] = df["Assignee"].fillna("Unassigned")
df["Status"] = df["Status"].fillna("in-progress").str.lower()

now = datetime.now()
now_str = now.strftime("%Y-%m-%d %H:%M:%S")
thirty_days_ago = now - timedelta(days=30)

formatted_data = []

# 2. Process rows for timeline
for _, row in df.iterrows():
    start_date = str(row["StartDate"]).strip()

    # If item is still in-progress or missing EndDate, extend to current time
    end_date = str(row["EndDate"]).strip() if pd.notna(row["EndDate"]) else None
    if not end_date or end_date.lower() in ["nan", "none", ""]:
        end_date = now_str

    formatted_data.append(
        {
            "id": str(row["ID"]),
            "title": str(row["Title"]),
            "assignee": str(row["Assignee"]),
            "status": str(row["Status"]),
            "start": start_date,
            "end": end_date,
        }
    )

# 3. Read template and inject variables
with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
    template_content = f.read()

rendered_html = (
    template_content.replace(
        "{{ raw_data_json }}", json.dumps(formatted_data, indent=2)
    )
    .replace("{{ generation_date }}", now.strftime("%B %d, %Y"))
    .replace("{{ today_str }}", now.strftime("%Y-%m-%d"))
    .replace("{{ thirty_days_ago_str }}", thirty_days_ago.strftime("%Y-%m-%d"))
)

# 4. Save output report
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(rendered_html)

print(
    f"Report successfully generated! Open '{OUTPUT_FILE}' in your web browser."
)
