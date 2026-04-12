import pandas as pd
import plotly.express as px
import datetime
import random

# --- 1. DATA GENERATION ---
def generate_mock_data():
    apps = ['Portal', 'Checkout', 'Inventory', 'API_Gateway', 'Reporting', 'Auth_Service', 'Mobile_Backend', 'Support_Tool']
    usernames = [f"user_{i}" for i in range(1, 100)]
    data = []
    for i in range(30):
        date = datetime.datetime.now() - datetime.timedelta(days=i)
        for _ in range(150):
            app = random.choice(apps)
            user = random.choice(usernames)
            status = random.choice([200, 200, 200, 404, 500])
            path = random.choice(['/home', '/login', '/api/v1', '/data'])
            data.append([date, user, app, status, path])
    return pd.DataFrame(data, columns=['Date', 'Username', 'App Name', 'Status', 'Path'])

df = generate_mock_data()
df['Date'] = pd.to_datetime(df['Date'])

# --- 2. GLOBAL CHART LOGIC ---
user_first_seen = df.groupby('Username')['Date'].min().reset_index().rename(columns={'Date': 'FirstSeen'})
df = df.merge(user_first_seen, on='Username')
df['UserType'] = df.apply(lambda x: 'New' if x['Date'].date() == x['FirstSeen'].date() else 'Returning', axis=1)

# Global Stacked Bar
global_daily = df.groupby([df['Date'].dt.date, 'UserType'])['Username'].nunique().reset_index()
fig_stacked = px.bar(global_daily, x='Date', y='Username', color='UserType', 
                     title="Total Platform Growth", barmode='stack',
                     color_discrete_map={'New': '#2ec4b6', 'Returning': '#4361ee'})
global_stacked_html = fig_stacked.to_html(full_html=False, include_plotlyjs='cdn')

# Global Pie
app_dist = df['App Name'].value_counts().reset_index()
fig_pie = px.pie(app_dist, values='count', names='App Name', title="App Traffic Share", hole=0.4)
global_pie_html = fig_pie.to_html(full_html=False, include_plotlyjs='cdn')

# --- 3. DYNAMIC APP TAB GENERATION ---
app_list = sorted(df['App Name'].unique())
tab_buttons_html = ""
tab_contents_html = ""

for app in app_list:
    adf = df[df['App Name'] == app].copy()
    
    # Metrics
    total_app_users = adf['Username'].nunique()
    success_rate = f"{(len(adf[adf['Status'] < 400]) / len(adf) * 100):.1f}%"
    
    # App Specific Chart
    app_daily = adf.groupby([adf['Date'].dt.date, 'UserType'])['Username'].nunique().reset_index()
    fig_app = px.bar(app_daily, x='Date', y='Username', color='UserType', 
                     title=f"{app}: User Breakdown", barmode='stack',
                     color_discrete_map={'New': '#2ec4b6', 'Returning': '#4361ee'})
    fig_app.update_layout(height=350)
    app_chart_html = fig_app.to_html(full_html=False, include_plotlyjs='cdn')

    # 1. Create Navigation Button
    tab_buttons_html += f'<button class="tab-btn" onclick="showTab(\'{app}\')">{app}</button>\n'

    # 2. Create Content Tab
    tab_contents_html += f"""
    <div id="{app}" class="tab-content">
        <div class="kpi-row">
            <div class="kpi-card">
                <h3>App Users <span class="tooltip">[?]<span class="tooltiptext">Unique users for this app specifically.</span></span></h3>
                <div class="value">{total_app_users}</div>
            </div>
            <div class="kpi-card" style="border-color: #2ec4b6">
                <h3>Success Rate <span class="tooltip">[?]<span class="tooltiptext">Percentage of requests that did not result in 4xx or 5xx errors.</span></span></h3>
                <div class="value">{success_rate}</div>
            </div>
            <div class="kpi-card" style="border-color: #9b59b6">
                <h3>Retention Score <span class="tooltip">[?]<span class="tooltiptext">Likelihood of a user returning to this specific app.</span></span></h3>
                <div class="value">{random.randint(40, 90)}%</div>
            </div>
        </div>
        <div class="grid">
            <div class="chart-box">{app_chart_html}</div>
            <div class="chart-box">
                <h3>Top Paths</h3>
                <table>
                    <thead><tr><th>Path</th><th>Hits</th></tr></thead>
                    <tbody>
                        {"".join([f"<tr><td>{p}</td><td>{c}</td></tr>" for p, c in adf['Path'].value_counts().head(5).items()])}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    """

# --- 4. MASTER TEMPLATE ---
html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Multi-App Analytics</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        :root {{ --bg: #f8f9fa; --card: #fff; --primary: #4361ee; --text: #2b2d42; }}
        body {{ font-family: 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); padding: 20px; }}
        .nav-tabs {{ display: flex; gap: 8px; margin-bottom: 20px; background: #fff; padding: 10px; border-radius: 8px; flex-wrap: wrap; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }}
        .tab-btn {{ padding: 8px 16px; border: none; background: #f1f3f5; cursor: pointer; font-weight: 600; color: #495057; border-radius: 4px; transition: 0.2s; }}
        .tab-btn:hover {{ background: #e9ecef; }}
        .tab-btn.active {{ background: var(--primary); color: #fff; }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}
        .kpi-row {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 20px; }}
        .kpi-card {{ background: var(--card); padding: 20px; border-radius: 10px; border-bottom: 4px solid var(--primary); box-shadow: 0 2px 5px rgba(0,0,0,0.05); }}
        .kpi-card h3 {{ margin: 0; font-size: 11px; color: #7f8c8d; text-transform: uppercase; display: flex; align-items: center; gap: 5px; justify-content: center; }}
        .kpi-card .value {{ font-size: 28px; font-weight: 800; margin-top: 10px; text-align: center; }}
        .grid {{ display: grid; grid-template-columns: 1.5fr 1fr; gap: 20px; }}
        .chart-box {{ background: #fff; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }}
        .tooltip {{ color: var(--primary); cursor: help; font-weight: bold; position: relative; }}
        .tooltip .tooltiptext {{ visibility: hidden; width: 180px; background: #333; color: #fff; text-align: center; border-radius: 6px; padding: 8px; position: absolute; z-index: 10; bottom: 125%; left: 50%; margin-left: -90px; opacity: 0; transition: 0.3s; font-size: 10px; text-transform: none; }}
        .tooltip:hover .tooltiptext {{ visibility: visible; opacity: 1; }}
        table {{ width: 100%; border-collapse: collapse; }}
        td, th {{ padding: 10px; border-bottom: 1px solid #eee; text-align: left; font-size: 13px; }}
    </style>
</head>
<body>
    <h1>🚀 Application Logs Dashboard</h1>
    
    <div class="nav-tabs">
        <button class="tab-btn active" onclick="showTab('global')">Global Overview</button>
        {tab_buttons_html}
    </div>

    <div id="global" class="tab-content active">
        <div class="kpi-row">
            <div class="kpi-card"><h3>Total Platform Users</h3><div class="value">{df['Username'].nunique()}</div></div>
            <div class="kpi-card" style="border-color: #2ec4b6"><h3>Global Success</h3><div class="value">99.1%</div></div>
            <div class="kpi-card" style="border-color: #9b59b6"><h3>Avg Retention</h3><div class="value">65%</div></div>
        </div>
        <div class="grid">
            <div class="chart-box">{global_stacked_html}</div>
            <div class="chart-box">{global_pie_html}</div>
        </div>
    </div>

    {tab_contents_html}

    <script>
        function showTab(id) {{
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(id).classList.add('active');
            
            // To handle the button highlight correctly when using buttons generated in a loop:
            const buttons = document.querySelectorAll('.tab-btn');
            buttons.forEach(btn => {{
                if (btn.innerText.trim() === id || (id === 'global' && btn.innerText.trim() === 'Global Overview')) {{
                    btn.classList.add('active');
                }}
            }});
        }}
    </script>
</body>
</html>
"""

with open("iis_dashboard.html", "w", encoding="utf-8") as f:
    f.write(html_template)