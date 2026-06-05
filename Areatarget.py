import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# ==========================================
# 1. Configuration & Data Loading
# ==========================================
csv_filename = 'your_devops_file.csv' 
target_year = 2026  

targets = {
    'Area A': 200,
    'Area B': 300,
    'Area C': 100
}

df = pd.read_csv(csv_filename)
date_col = 'Closed Date'
area_col = 'Area'

df[date_col] = pd.to_datetime(df[date_col])
df = df[df[date_col].dt.year == target_year]

# Determine the last month we have actual data for
current_date = datetime.now()
last_actual_month = df[date_col].max().month

# ==========================================
# 2. Data Processing & Run-Rate Projections
# ==========================================
all_months = pd.period_range(start=f'{target_year}-01', end=f'{target_year}-12', freq='M')
df['Month'] = df[date_col].dt.to_period('M')

# Aggregate monthly historic numbers
monthly_counts = df.groupby([area_col, 'Month']).size().unstack(fill_value=0)
monthly_counts = monthly_counts.reindex(columns=all_months, fill_value=0)

# X-axis single letter labels
single_letters = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']
x_indexes = np.arange(12)

# ==========================================
# 3. Plotting the Visuals
# ==========================================
fig, axes = plt.subplots(len(targets), 1, figsize=(10, 3.5 * len(targets)), sharex=False, gridspec_kw={'hspace': 0.5})
if len(targets) == 1:
    axes = [axes]

for i, area in enumerate(targets.keys()):
    ax = axes[i]
    annual_target = targets[area]
    
    # Generate linear baseline target path
    target_line = np.linspace(0, annual_target, 13)[1:]
    
    # Separate historical counts from future projections
    area_months = monthly_counts.loc[area].values if area in monthly_counts.index else np.zeros(12)
    actual_cumulative = np.zeros(12)
    
    # 1. Populate Actuals up to current month cutoff
    running_total = 0
    for m in range(last_actual_month):
        running_total += area_months[m]
        actual_cumulative[m] = running_total
        
    # 2. Project Run-Rate out to the rest of the year
    monthly_run_rate = running_total / max(last_actual_month, 1)
    for m in range(last_actual_month, 12):
        running_total += monthly_run_rate
        actual_cumulative[m] = running_total
        
    # 3. Calculate Final Variances for Title
    final_projected = actual_cumulative[-1]
    variance = round(final_projected - annual_target)
    
    if variance >= 0:
        status_str = f"ahead by {variance}"
        title_color = '#1e4620'  # Deep green
    else:
        status_str = f"behind by {abs(variance)}"
        title_color = '#8b0000'  # Deep red

    # --- Draw the Chart Elements ---
    # Expected target trajectory line
    ax.plot(x_indexes, target_line, label='Expected Target Path', color='darkgray', linestyle='--')
    
    # Actuals path (Solid Line)
    ax.plot(x_indexes[:last_actual_month], actual_cumulative[:last_actual_month], 
            color='royalblue', linewidth=2.5, marker='o', label='Actual Closures')
    
    # Forecasted path (Faded Dotted Line starting from our transition point)
    ax.plot(x_indexes[last_actual_month-1:], actual_cumulative[last_actual_month-1:], 
            color='royalblue', linewidth=2.5, linestyle=':', alpha=0.5, 
            marker='o', markerfacecolor='white', label='Projected Trend')
    
    # Background Shading - Stronger color weight for concrete historic data
    ax.fill_between(x_indexes[:last_actual_month], actual_cumulative[:last_actual_month], target_line[:last_actual_month],
                    where=(actual_cumulative[:last_actual_month] >= target_line[:last_actual_month]), interpolate=True, color='green', alpha=0.12)
    ax.fill_between(x_indexes[:last_actual_month], actual_cumulative[:last_actual_month], target_line[:last_actual_month],
                    where=(actual_cumulative[:last_actual_month] < target_line[:last_actual_month]), interpolate=True, color='red', alpha=0.12)
    
    # Background Shading - Softer color weight for hypothetical projections
    ax.fill_between(x_indexes[last_actual_month-1:], actual_cumulative[last_actual_month-1:], target_line[last_actual_month-1:],
                    where=(actual_cumulative[last_actual_month-1:] >= target_line[last_actual_month-1:]), interpolate=True, color='green', alpha=0.04)
    ax.fill_between(x_indexes[last_actual_month-1:], actual_cumulative[last_actual_month-1:], target_line[last_actual_month-1:],
                    where=(actual_cumulative[last_actual_month-1:] < target_line[last_actual_month-1:]), interpolate=True, color='red', alpha=0.04)
    
    # Layout Adjustments
    ax.set_title(f"{area} — Projected to be {status_str} by year-end (Target: {annual_target})", fontsize=12, fontweight='bold', color=title_color)
    ax.set_ylabel('Closures')
    ax.set_xticks(x_indexes)
    ax.set_xticklabels(single_letters)
    ax.grid(True, linestyle=':', alpha=0.5)
    ax.legend(loc='upper left', fontsize=9)

axes[-1].set_xlabel('Month')
fig.savefig('projected_burnup_minimal_x.png', bbox_inches='tight')
print("Updated projected visual saved successfully as 'projected_burnup_minimal_x.png'.")
