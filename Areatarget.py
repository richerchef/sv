import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# ==========================================
# 1. Configuration & Data Loading
# ==========================================
csv_filename = 'your_devops_file.csv' 
target_year = 2026  

# Define individual area targets
area_targets = {
    'Area A': 200,
    'Area B': 300,
    'Area C': 100
}

df = pd.read_csv(csv_filename)
closed_date_col = 'Closed Date'
created_date_col = 'Date Created'  # Update if column is named differently
area_col = 'Area'

# Parse both columns using your exact timestamp structure
date_format = '%d/%m/%Y %H:%M:%S'
df[created_date_col] = pd.to_datetime(df[created_date_col], format=date_format, errors='coerce')
df[closed_date_col] = pd.to_datetime(df[closed_date_col], format=date_format, errors='coerce')

# Filter for items originating in the target year
df = df[df[created_date_col].dt.year == target_year]

# Safely establish the current calendar month cutoff threshold
if not df.empty and pd.notnull(df[created_date_col].max()):
    last_actual_month = df[created_date_col].max().month
else:
    last_actual_month = datetime.now().month
last_actual_month = max(1, min(12, last_actual_month))

# ==========================================
# 2. Data Transformation & Backlog Counting
# ==========================================
all_months = pd.period_range(start=f'{target_year}-01', end=f'{target_year}-12', freq='M')
df['Month Closed'] = df[closed_date_col].dt.to_period('M')

# Track cumulative historical closed items by area
closed_monthly = df.groupby([area_col, 'Month Closed']).size().unstack(fill_value=0).reindex(columns=all_months, fill_value=0)
closed_monthly.loc['Grand Total'] = closed_monthly.sum()

# CORE FILTER: If an item has no closed date, it is classified as 'Still Open'
open_backlog_counts = df[df[closed_date_col].isna()].groupby(area_col).size()
open_backlog_counts['Grand Total'] = open_backlog_counts.sum()

# Compile master targets registry
targets_registry = area_targets.copy()
targets_registry['Grand Total'] = sum(area_targets.values())

# Layout controls
plot_order = ['Grand Total'] + list(area_targets.keys())
single_letters = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']
x_indexes = np.arange(12)

# ==========================================
# 3. Generating the Dashboards
# ==========================================
fig, axes = plt.subplots(len(plot_order), 1, figsize=(11, 4 * len(plot_order)), sharex=False, gridspec_kw={'hspace': 0.55})
if len(plot_order) == 1:
    axes = [axes]

for i, area in enumerate(plot_order):
    ax = axes[i]
    annual_target = targets_registry[area]
    target_line = np.linspace(0, annual_target, 13)[1:]
    
    # Extract historical values and set up run-rate loops
    hist_closed_vals = closed_monthly.loc[area].values
    closed_cum = np.zeros(12)
    running_closed = 0
    
    # 1. Populate Actual Closures to date
    for m in range(last_actual_month):
        running_closed += hist_closed_vals[m]
        closed_cum[m] = running_closed
        
    # 2. Project Run Rate for remaining months
    run_rate = running_closed / max(last_actual_month, 1)
    for m in range(last_actual_month, 12):
        running_closed += run_rate
        closed_cum[m] = running_closed
        
    # 3. Create "What-If" Vector by stacking open items onto our current progress
    current_open_pool = open_backlog_counts.get(area, 0)
    what_if_cum = closed_cum.copy()
    # Apply the open ticket volume as an immediate boost starting from the cutoff onwards
    what_if_cum[last_actual_month-1:] += current_open_pool
    
    # Calculate target percentages
    current_closed_snapshot = closed_cum[last_actual_month-1]
    pct_now = round((current_closed_snapshot / annual_target) * 100) if annual_target > 0 else 0
    pct_projected = round((closed_cum[-1] / annual_target) * 100) if annual_target > 0 else 0
    
    # Title aesthetics based on variance
    variance = round(closed_cum[-1] - annual_target)
    status_str = f"ahead by {variance}" if variance >= 0 else f"behind by {abs(variance)}"
    title_color = '#1e4620' if variance >= 0 else '#8b0000'
    
    # --- Plotting Visual Lines ---
    # Linear Target Line
    ax.plot(x_indexes, target_line, label='Expected Target Path', color='darkgray', linestyle='--')
    
    # Solid Actual Closures Track
    ax.plot(x_indexes[:last_actual_month], closed_cum[:last_actual_month], 
            color='royalblue', linewidth=2.5, marker='o', 
            label=f'Actual Closures ({pct_now}% of target achieved)')
    
    # Dotted Baseline Projection Track
    ax.plot(x_indexes[last_actual_month-1:], closed_cum[last_actual_month-1:], 
            color='royalblue', linewidth=2.5, linestyle=':', alpha=0.5, 
            marker='o', markerfacecolor='white', 
            label=f'Projected Baseline Trend ({pct_projected}% of target)')
    
    # Faint Dotted Amber "What-If Open Backlog is Cleared" Track
    ax.plot(x_indexes[last_actual_month-1:], what_if_cum[last_actual_month-1:], 
            color='#d97706', linewidth=2, linestyle='--', alpha=0.6, 
            marker='s', markerfacecolor='white', 
            label=f'What-If: Resolve Current Open Items (+{current_open_pool} items)')
    
    # Historical Progress Shading
    ax.fill_between(x_indexes[:last_actual_month], closed_cum[:last_actual_month], target_line[:last_actual_month],
                    where=(closed_cum[:last_actual_month] >= target_line[:last_actual_month]), interpolate=True, color='green', alpha=0.1)
    ax.fill_between(x_indexes[:last_actual_month], closed_cum[:last_actual_month], target_line[:last_actual_month],
                    where=(closed_cum[:last_actual_month] < target_line[:last_actual_month]), interpolate=True, color='red', alpha=0.1)
    
    # Finalize Subplot Details
    ax.set_title(f"{area} — Projected to be {status_str} by year-end (Target: {annual_target})", fontsize=12, fontweight='bold', color=title_color)
    ax.set_ylabel('Total Items')
    ax.set_xticks(x_indexes)
    ax.set_xticklabels(single_letters)
    ax.grid(True, linestyle=':', alpha=0.5)
    ax.legend(loc='upper left', fontsize=9)

axes[-1].set_xlabel('Month')
fig.savefig('burnup_with_open_potential.png', bbox_inches='tight')
print("Traditional Burnup chart with 'What-If' Backlog modeling created and saved successfully.")


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
