import csv
import json
import os
import re
from collections import defaultdict
from datetime import datetime

# Points structure: F1 style (1st to 10th)
F1_POINTS = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]

MONTHS_NAMES = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


def parse_csv(file_path):
    records = []
    reviewer_pattern = re.compile(r"([^,;]+?)\s+to\s+review", re.IGNORECASE)

    with open(file_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            closed_date_str = row.get("Closed Date", "").strip()
            if not closed_date_str:
                continue

            try:
                closed_date = datetime.strptime(
                    closed_date_str, "%d/%m/%Y %H:%M:%S"
                )
            except ValueError:
                continue

            if closed_date.year != 2026:
                continue

            try:
                story_points = float(row.get("Story Points Numeric", 0) or 0)
            except ValueError:
                story_points = 0.0

            tags = row.get("Tags", "")
            matches = reviewer_pattern.findall(tags)

            for raw_name in matches:
                reviewer_name = raw_name.strip().title()
                if reviewer_name:
                    records.append(
                        {
                            "id": row.get("ID"),
                            "reviewer": reviewer_name,
                            "closed_date": closed_date,
                            "story_points": story_points,
                        }
                    )
    return records


def calculate_monthly_ranks(records):
    monthly_data = defaultdict(lambda: defaultdict(list))

    for rec in records:
        m = rec["closed_date"].month
        monthly_data[m][rec["reviewer"]].append(rec)

    monthly_rankings = {}

    for month in range(1, 13):
        reviewers_in_month = monthly_data[month]
        if not reviewers_in_month:
            monthly_rankings[month] = []
            continue

        stats = []
        for rev, rev_records in reviewers_in_month.items():
            count = len(rev_records)
            sp_total = sum(r["story_points"] for r in rev_records)
            weighted_score = count * sp_total
            first_review_time = min(r["closed_date"] for r in rev_records)

            stats.append(
                {
                    "reviewer": rev,
                    "count": count,
                    "story_points": sp_total,
                    "weighted": weighted_score,
                    "first_time": first_review_time,
                }
            )

        def process_mode_rankings(mode_key):
            sorted_stats = sorted(
                stats, key=lambda x: (-x[mode_key], x["first_time"])
            )

            results = []
            i = 0
            n = len(sorted_stats)

            while i < n:
                j = i
                while (
                    j < n
                    and sorted_stats[j][mode_key] == sorted_stats[i][mode_key]
                    and sorted_stats[j]["first_time"]
                    == sorted_stats[i]["first_time"]
                ):
                    j += 1

                group_size = j - i
                start_rank = i + 1

                pts_sum = sum(
                    F1_POINTS[pos] if pos < 10 else 0
                    for pos in range(i, j)
                )
                shared_points = pts_sum / group_size if group_size > 0 else 0

                for item in sorted_stats[i:j]:
                    results.append(
                        {
                            "reviewer": item["reviewer"],
                            "rank": start_rank,
                            "points": shared_points,
                            "score": item[mode_key],
                            "count": item["count"],
                            "story_points": item["story_points"],
                        }
                    )
                i = j
            return {r["reviewer"]: r for r in results}

        weighted_res = process_mode_rankings("weighted")
        unweighted_res = process_mode_rankings("count")

        all_reviewers = set(weighted_res.keys())
        month_combined = []

        for rev in all_reviewers:
            month_combined.append(
                {
                    "reviewer": rev,
                    "count": weighted_res[rev]["count"],
                    "story_points": weighted_res[rev]["story_points"],
                    "weighted": weighted_res[rev],
                    "unweighted": unweighted_res[rev],
                }
            )

        monthly_rankings[month] = month_combined

    return monthly_rankings


def generate_html_report(monthly_rankings, template_path="template.html"):
    all_reviewers = set()
    for m in range(1, 13):
        for entry in monthly_rankings[m]:
            all_reviewers.add(entry["reviewer"])

    data_payload = {
        "months": MONTHS_NAMES,
        "monthlyData": monthly_rankings,
        "reviewers": sorted(list(all_reviewers)),
    }

    tab_buttons = []
    tab_contents = []

    for idx, name in enumerate(MONTHS_NAMES):
        m_num = idx + 1
        tab_buttons.append(
            f'<button class="tab-btn" onclick="switchTab(\'month-{m_num}\', event)">{name}</button>'
        )
        tab_contents.append(
            f'<div id="month-{m_num}" class="tab-content"><h2>{name} Standings</h2><div id="month-table-{m_num}"></div></div>'
        )

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    rendered = template.replace("<!--MONTH_TABS-->", "\n    ".join(tab_buttons))
    rendered = rendered.replace("<!--MONTH_CONTENTS-->", "\n    ".join(tab_contents))
    rendered = rendered.replace("<!--DATA_PAYLOAD-->", json.dumps(data_payload))

    return rendered


def run():
    input_file = "input.csv"
    template_file = "template.html"

    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    if not os.path.exists(template_file):
        print(f"Error: {template_file} not found.")
        return

    records = parse_csv(input_file)
    monthly_rankings = calculate_monthly_ranks(records)
    html_out = generate_html_report(monthly_rankings, template_file)

    now_str = datetime.now().strftime("%Y_%m_%d")
    output_file = f"leaderboard_{now_str}.html"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_out)

    print(f"Successfully generated report: {output_file}")


if __name__ == "__main__":
    run()
