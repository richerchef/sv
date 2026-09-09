import csv
import json
import os
import re
from collections import defaultdict
from datetime import datetime

# Points structure: F1 style (1st to 10th)
F1_POINTS = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]


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

            # Filter exclusively for 2026
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
    # month_num -> reviewer -> list of reviews
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

        # Prepare stats for both weighted (SP) and unweighted (Count) modes
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
                    "weighted": weighted_score,
                    "first_time": first_review_time,
                }
            )

        # Helper to compute tied ranks & F1 points
        def process_mode_rankings(mode_key):
            # Sort: primary key descending, tiebreaker (earliest timestamp) ascending
            sorted_stats = sorted(
                stats, key=lambda x: (-x[mode_key], x["first_time"])
            )

            results = []
            i = 0
            n = len(sorted_stats)

            while i < n:
                # Group ties based on identical primary score AND identical tiebreaker timestamp
                j = i
                while (
                    j < n
                    and sorted_stats[j][mode_key] == sorted_stats[i][mode_key]
                    and sorted_stats[j]["first_time"]
                    == sorted_stats[i]["first_time"]
                ):
                    j += 1

                group_size = j - i
                start_rank = i + 1  # 1-indexed rank

                # Sum available F1 points for positions occupied by this tied group
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
                    "weighted": weighted_res[rev],
                    "unweighted": unweighted_res[rev],
                }
            )

        monthly_rankings[month] = month_combined

    return monthly_rankings


def generate_html_report(monthly_rankings):
    months_names = [
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

    # Collect all unique reviewers across the entire year
    all_reviewers = set()
    for m in range(1, 13):
        for entry in monthly_rankings[m]:
            all_reviewers.add(entry["reviewer"])

    # Prepare JSON structure for dynamic rendering via UI script
    data_payload = {
        "months": months_names,
        "monthlyData": monthly_rankings,
        "reviewers": sorted(list(all_reviewers)),
    }

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>DevOps Reviewer Leaderboard 2026</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{
            --bbc-yellow: #ffd200;
            --bbc-black: #141414;
            --bbc-red: #b80000;
            --bbc-gray: #f6f6f6;
            --bbc-border: #e0e0e0;
        }}
        body {{
            font-family: ReithSans, Arial, Helvetica, sans-serif;
            background-color: var(--bbc-gray);
            color: #222;
            margin: 0;
            padding: 0;
        }}
        header {{
            background-color: var(--bbc-black);
            color: white;
            padding: 15px 30px;
            border-bottom: 4px solid var(--bbc-yellow);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        header h1 {{
            margin: 0;
            font-size: 26px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .badge {{
            background: var(--bbc-yellow);
            color: var(--bbc-black);
            padding: 4px 10px;
            font-weight: bold;
            font-size: 14px;
        }}
        .controls-bar {{
            background: white;
            padding: 12px 30px;
            border-bottom: 1px solid var(--bbc-border);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .toggle-container {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-weight: bold;
            font-size: 14px;
        }}
        .nav-tabs {{
            display: flex;
            background: var(--bbc-black);
            padding: 0 30px;
            overflow-x: auto;
        }}
        .tab-btn {{
            background: none;
            border: none;
            color: white;
            padding: 12px 18px;
            cursor: pointer;
            font-weight: bold;
            font-size: 14px;
            border-bottom: 3px solid transparent;
            white-space: nowrap;
        }}
        .tab-btn:hover {{
            background-color: #2a2a2a;
        }}
        .tab-btn.active {{
            border-bottom-color: var(--bbc-yellow);
            color: var(--bbc-yellow);
        }}
        .container {{
            max-width: 1200px;
            margin: 20px auto;
            background: white;
            padding: 25px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }}
        .tab-content {{
            display: none;
        }}
        .tab-content.active {{
            display: block;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th {{
            background-color: var(--bbc-black);
            color: white;
            text-align: left;
            padding: 10px;
            font-size: 14px;
        }}
        td {{
            padding: 12px 10px;
            border-bottom: 1px solid var(--bbc-border);
            font-size: 15px;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        tr:hover {{
            background-color: #f1f1f1;
        }}
        .pos-1 {{ font-weight: bold; color: #d4af37; }}
        .pos-2 {{ font-weight: bold; color: #aaa; }}
        .pos-3 {{ font-weight: bold; color: #cd7f32; }}
        .card-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 25px;
        }}
        .card {{
            background: var(--bbc-gray);
            border-left: 4px solid var(--bbc-black);
            padding: 15px;
        }}
        .card h4 {{
            margin: 0 0 8px 0;
            color: #555;
            text-transform: uppercase;
            font-size: 12px;
        }}
        .card .value {{
            font-size: 24px;
            font-weight: bold;
        }}
        .chart-box {{
            margin-top: 30px;
            height: 400px;
        }}
        /* Switch styling */
        .switch {{
            position: relative;
            display: inline-block;
            width: 46px;
            height: 24px;
        }}
        .switch input {{ opacity: 0; width: 0; height: 0; }}
        .slider {{
            position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0;
            background-color: #ccc; transition: .4s; border-radius: 24px;
        }}
        .slider:before {{
            position: absolute; content: ""; height: 18px; width: 18px; left: 3px; bottom: 3px;
            background-color: white; transition: .4s; border-radius: 50%;
        }}
        input:checked + .slider {{ background-color: var(--bbc-red); }}
        input:checked + .slider:before {{ transform: translateX(22px); }}
    </style>
</head>
<body>

<header>
    <h1>DevOps Reviewer Championship 2026</h1>
    <span class="badge">BBC SPORT STYLE</span>
</header>

<div class="controls-bar">
    <div class="toggle-container">
        <span>Raw Reviews Only</span>
        <label class="switch">
            <input type="checkbox" id="modeToggle" onchange="renderAll()">
            <span class="slider"></span>
        </label>
        <span>Weighted by Story Points</span>
    </div>
</div>

<div class="nav-tabs">
    <button class="tab-btn active" onclick="switchTab('championship')">Championship</button>
    <button class="tab-btn" onclick="switchTab('analytics')">Analytics & Potential</button>
    {''.join([f'<button class="tab-btn" onclick="switchTab(\'month-{i+1}\')">{m}</button>' for i, m in enumerate(months_names)])}
</div>

<div class="container">
    <div id="championship" class="tab-content active">
        <h2>Championship Leaderboard</h2>
        <div id="championship-table-container"></div>
    </div>

    <div id="analytics" class="tab-content">
        <h2>Season Analytics & Potential</h2>
        <div class="card-grid">
            <div class="card">
                <h4>Months Elapsed</h4>
                <div class="value" id="stat-elapsed">0 / 12</div>
            </div>
            <div class="card">
                <h4>Max Remaining Points</h4>
                <div class="value" id="stat-remaining-pts">0</div>
            </div>
            <div class="card">
                <h4>Current Leader</h4>
                <div class="value" id="stat-leader">-</div>
            </div>
        </div>
        <div class="chart-box">
            <canvas id="progressChart"></canvas>
        </div>
        <h3 style="margin-top:40px;">Max Potential Finish Matrix</h3>
        <div id="potential-table-container"></div>
    </div>

    {''.join([f'<div id="month-{i+1}" class="tab-content"><h2>{m} Standings</h2><div id="month-table-{i+1}"></div></div>' for i, m in enumerate(months_names)])}
</div>

<script>
const data = {json.dumps(data_payload)};
let progressChart = null;

function isWeighted() {{
    return document.getElementById('modeToggle').checked;
}}

function switchTab(tabId) {{
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
    
    document.getElementById(tabId).classList.add('active');
    event.currentTarget.classList.add('active');
}}

function renderAll() {{
    const mode = isWeighted() ? 'weighted' : 'unweighted';
    renderChampionship(mode);
    renderMonthly(mode);
    renderAnalytics(mode);
}}

function renderChampionship(mode) {{
    const totals = {{}};
    data.reviewers.forEach(r => totals[r] = 0);

    for (let m = 1; m <= 12; m++) {{
        const monthList = data.monthlyData[m] || [];
        monthList.forEach(item => {{
            totals[item.reviewer] += item[mode].points;
        }});
    }}

    const sorted = Object.keys(totals)
        .map(r => ({{ reviewer: r, points: totals[r] }}))
        .sort((a, b) => b.points - a.points);

    let html = `<table><thead><tr><th>Pos</th><th>Reviewer</th><th>Total Points</th></tr></thead><tbody>`;
    sorted.forEach((item, index) => {{
        const posClass = index === 0 ? 'pos-1' : index === 1 ? 'pos-2' : index === 2 ? 'pos-3' : '';
        html += `<tr>
            <td class="${{posClass}}">${{index + 1}}</td>
            <td><strong>${{item.reviewer}}</strong></td>
            <td>${{item.points.toFixed(1)}}</td>
        </tr>`;
    }});
    html += `</tbody></table>`;
    document.getElementById('championship-table-container').innerHTML = html;
}}

function renderMonthly(mode) {{
    for (let m = 1; m <= 12; m++) {{
        const monthList = data.monthlyData[m] || [];
        const sorted = [...monthList].sort((a, b) => a[mode].rank - b[mode].rank);

        let html = `<table><thead><tr><th>Pos</th><th>Reviewer</th><th>Score (${{mode === 'weighted' ? 'SP Weighted' : 'Reviews'}})</th><th>F1 Points</th></tr></thead><tbody>`;
        if (sorted.length === 0) {{
            html += `<tr><td colspan="4">No reviews recorded for this month.</td></tr>`;
        }} else {{
            sorted.forEach(item => {{
                html += `<tr>
                    <td>${{item[mode].rank}}</td>
                    <td>${{item.reviewer}}</td>
                    <td>${{item[mode].score.toFixed(1)}}</td>
                    <td>${{item[mode].points.toFixed(1)}}</td>
                </tr>`;
            }});
        }}
        html += `</tbody></table>`;
        document.getElementById(`month-table-${{m}}`).innerHTML = html;
    }}
}}

function renderAnalytics(mode) {{
    let elapsed = 0;
    for (let m = 1; m <= 12; m++) {{
        if ((data.monthlyData[m] || []).length > 0) elapsed = m;
    }}

    const remainingMonths = 12 - elapsed;
    const maxRemainingPts = remainingMonths * 25;

    document.getElementById('stat-elapsed').innerText = `${{elapsed}} / 12`;
    document.getElementById('stat-remaining-pts').innerText = maxRemainingPts;

    // Cumulative points tracking
    const cumPoints = {{}};
    data.reviewers.forEach(r => cumPoints[r] = Array(12).fill(0));

    data.reviewers.forEach(r => {{
        let run = 0;
        for (let m = 1; m <= 12; m++) {{
            const found = (data.monthlyData[m] || []).find(x => x.reviewer === r);
            if (found) run += found[mode].points;
            cumPoints[r][m - 1] = run;
        }}
    }});

    // Leader stat
    const currentStandings = data.reviewers.map(r => ({{
        reviewer: r,
        pts: cumPoints[r][11]
    }})).sort((a, b) => b.pts - a.pts);

    document.getElementById('stat-leader').innerText = currentStandings[0] ? `${{currentStandings[0].reviewer}} (${{currentStandings[0].pts.toFixed(1)}} pts)` : 'N/A';

    // Render Chart
    const datasets = data.reviewers.map((r, i) => {{
        const colors = ['#b80000', '#ffd200', '#005ace', '#008000', '#800080', '#ff69b4', '#a52a2a', '#808080'];
        return {{
            label: r,
            data: cumPoints[r],
            borderColor: colors[i % colors.length],
            fill: false,
            tension: 0.1
        }};
    }});

    if (progressChart) progressChart.destroy();
    const ctx = document.getElementById('progressChart').getContext('2d');
    progressChart = new Chart(ctx, {{
        type: 'line',
        data: {{
            labels: data.months,
            datasets: datasets
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{ title: {{ display: true, text: 'Championship Point Trajectory' }} }}
        }}
    }});

    // Highest potential calculation
    let potHtml = `<table><thead><tr><th>Reviewer</th><th>Current Points</th><th>Max Possible Points</th><th>Highest Potential Finish</th></tr></thead><tbody>`;
    
    currentStandings.forEach(item => {{
        const maxPossible = item.pts + maxRemainingPts;
        // Rank if this reviewer achieves maxPossible while everyone else keeps current pts
        const highestPos = currentStandings.filter(other => other.pts > maxPossible).length + 1;

        potHtml += `<tr>
            <td><strong>${{item.reviewer}}</strong></td>
            <td>${{item.pts.toFixed(1)}}</td>
            <td>${{maxPossible.toFixed(1)}}</td>
            <td><strong>Pos ${{highestPos}}</strong></td>
        </tr>`;
    }});
    potHtml += `</tbody></table>`;
    document.getElementById('potential-table-container').innerHTML = potHtml;
}}

window.onload = function() {{
    renderAll();
}};
</script>

</body>
</html>
"""
    return html_content


def run():
    input_file = "input.csv"
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    records = parse_csv(input_file)
    monthly_rankings = calculate_monthly_ranks(records)
    html_out = generate_html_report(monthly_rankings)

    now_str = datetime.now().strftime("%Y_%m_%d")
    output_file = f"leaderboard_{now_str}.html"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_out)

    print(f"Successfully generated report: {output_file}")


if __name__ == "__main__":
    run()
